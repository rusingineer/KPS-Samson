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
from collections import namedtuple

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, QBuffer, QByteArray, QDate, QDateTime, QIODevice, QTime

from library.Identification import getIdentification, getIdentificationInfo, getIdentificationInfoList
from library.Utils import forceDate, forceDateTime, forceString, formatTime


__all__ = ( 'CInfoContext',
            'CInfo',
            'CTemplatableInfoMixin',
            'CIdentificationInfoMixin',
            'CDictInfoMixin',
            'CInfoList',
            'CInfoProxyList',
            'CDateInfo',
            'CDateTimeInfo',
            'CTimeInfo',
            'CRBInfo',
            'CRBInfoWithIdentification',
            'CImageInfo',
          )

_identification = namedtuple('identification', ('code', 'name', 'urn', 'version', 'value', 'note', 'checkDate', 'value_spr', 'name_spr', 'record'))


class CInfoContext(object):
    u'Отображение (класс объекта, параметры объекта) -> Экземпляр класса'
    def __init__(self):
        self._mapClassesToInstances = {}


    def getInstance(self, infoClass, *args, **kwargs):
        mapArgsToInstance = self._mapClassesToInstances.setdefault(infoClass, {})
        key = (tuple([(y if y and not isinstance(y, list) else ()) for y in args]), tuple([(x[0] if (x and len(x) > 1 and (isinstance(x[1], dict) or isinstance(x[1], list))) else x) for x in kwargs.iteritems()]))
        if key in mapArgsToInstance:
            return mapArgsToInstance[key]
        else:
            result = infoClass(self, *args, **kwargs)
            mapArgsToInstance[key] = result
            return result


    def removeInstance(self, infoClass, instance):
        mapArgsToInstance = self._mapClassesToInstances.setdefault(infoClass, {})
        for key in mapArgsToInstance:
            if id(mapArgsToInstance[key]) == id(instance):
                del mapArgsToInstance[key]
                return True
        return False


class CInfo(object):
    u'Базовый класс для представления объектов при передаче в шаблоны печати'
    def __init__(self, context):
        self._loaded = False
        self._ok = False
        self.context = context


    def load(self):
        if not self._loaded:
            self._ok = self._load()
            self._loaded = True
        return self


    def _load(self):
        raise NotImplementedError('abstract method call')


    def setOkLoaded(self, ok=True):
        self._ok = ok
        self._loaded = True


    def getInstance(self, infoClass, *args, **kwargs):
        return self.context.getInstance(infoClass, *args, **kwargs)


    def __nonzero__(self):
        self.load()
        return self._ok


    def __cmp__(self, x):
        ss = unicode(self)
        sx = unicode(x)
        if ss>sx:
            return 1
        elif ss<sx:
            return -1
        else:
            return 0


    def __add__(self, x):
        return unicode(self) + unicode(x)


    def __radd__(self,x):
        return unicode(x) + unicode(self)


    def getProperties(self):
        result = []
        # class properties
        class_ = type(self)
        for name, value in class_.__dict__.iteritems():
            if name.startswith('_') and isinstance(value, property):
                propvalue = self.__getattribute__(name)
                type_ = type(propvalue)
                result.append((name, str(type_), value.__doc__))
        return result


    def drop(self):
        self.context.removeInstance(self.__class__, self)
        for key in self.__dict__.keys():
            if hasattr(self.__dict__[key], 'drop'):
                self.__dict__[key].drop()


class CTemplatableInfoMixin:
    u'Примесевый класс для представления возможности печати СInfo через собственный шаблон'

    def getPrintTemplateContext(self):
        # "абстрактный" метод для получения контекста печати
        return None


    def getPrintTemplateList(self, printContext=None):
        # список CPrintTemplateMiniDescr(имяШаблона, idШаблона, group) подходящих для печати этого объекта
        from PrintTemplates import getPrintTemplates
        return getPrintTemplates(printContext if printContext else self.getPrintTemplateContext())


    def getData(self):
        # "абстрактный" метод для получения данных для шаблона печати
        return { }


    def formatByTemplateId(self, templateId):
        # формирование html по id шаблона
        from PrintTemplates import getTemplate, compileAndExecTemplate, htmlTemplate
        templateName, template, templateType, printBlank = getTemplate(templateId)

        if templateType != htmlTemplate:
            template = u'<HTML><BODY>Поддержка шаблонов печати в формате'\
                u' отличном от html не реализована</BODY></HTML>'

        data = self.getData()
        templateResult = compileAndExecTemplate(templateName, template, data)
        return templateResult.content


    def formatByTemplate(self, name, printContext=None):
        # формирование html по имени шаблона
        for template in self.getPrintTemplateList(printContext):
            if template.name == name:
                return self.formatByTemplateId(template.id)
        return u'Шаблон "%s" не найден в контексте печати "%s"' % (name, printContext if printContext else self.getPrintTemplateContext())


class CIdentificationInfoMixin:
    u'Примесевый класс для придания идентификаторов к СInfo'
    def __init__(self):
        self._mapUrnToIdentifier = {}
        self._mapUrnToIdentifierInfoList = {}
        self._mapUrnToIdentifierInfo = {}
        self._mapCodeToIdentifierInfo = {}

    def identify(self, urn):
        if self.id:
            if urn in self._mapUrnToIdentifier:
                return self._mapUrnToIdentifier[urn]
            else:
                result = getIdentification(self.tableName, self.id, urn, False)
                self._mapUrnToIdentifier[urn] = result
                return result
        else:
            return None

    def identifyInfoByUrn(self, urn):
        if self.id:
            if urn in self._mapUrnToIdentifierInfo:
                return self._mapUrnToIdentifierInfo[urn]
            else:
                code, name, urn, version, value, note, checkDate, value_spr, name_spr, record = getIdentificationInfo(self.tableName, self.id, urn)
                result = _identification(code, name, urn, version, value, note, CDateInfo(checkDate), value_spr, name_spr, record)
                self._mapUrnToIdentifierInfo[urn] = result
                return result
        else:
            return _identification(None, None, None, None, None, None, None, None, None, None)



    def identifyInfoByUrnList(self, urn):
        if self.id:
            if urn in self._mapUrnToIdentifierInfoList:
                return self._mapUrnToIdentifierInfoList[urn]
            else:
                # code, name, urn, version, value, note, checkDate = getIdentificationInfoList(self.tableName, self.id, urn)
                records = getIdentificationInfoList(self.tableName, self.id, urn)
                stmt_check_view = u"""select * from information_schema.views where table_name like '""" + \
                                  urn.replace(u'urn:oid:', u'v') + u"'"
                query_check_view = QtGui.qApp.db.query(stmt_check_view)
                view_exist = False
                list_record_from_view = None
                if query_check_view.next():
                    view_exist = True
                    list_record_from_view = QtGui.qApp.db.getRecordList(urn.replace(u'urn:oid:', u'v'))
                if records:
                    result = []
                    for record in records:
                        code = forceString(record.value('code'))
                        name = forceString(record.value('name'))
                        urn = forceString(record.value('urn'))
                        version = forceString(record.value('version'))
                        value = forceString(record.value('value'))
                        note = forceString(record.value('note'))
                        checkDate = forceDate(record.value('checkDate'))
                        value_spr = None
                        name_spr = None
                        record_spr = None
                        if view_exist and len(list_record_from_view):
                            for view_record in list_record_from_view:
                                if view_record.value('id') == record.value('value_spr'):
                                    value_spr = forceString(view_record.value('id'))
                                    name_spr = forceString(view_record.value('name'))
                                    record_spr = view_record
                                    break
                        result.append(_identification(code, name, urn, version, value, note, CDateInfo(checkDate), value_spr,name_spr,record_spr))
                    self._mapUrnToIdentifierInfoList[urn] = result
                    return result
                else:
                    return [_identification(None, None, None, None, None, None, None, None, None, None)]
        else:
            return _identification(None, None, None, None, None, None, None, None, None, None)

    def identifyInfoByCode(self, code):
        if self.id:
            if code in self._mapCodeToIdentifierInfo:
                return self._mapCodeToIdentifierInfo[code]
            else:
                code, name, urn, version, value, note, checkDate, value_spr, name_spr, record = getIdentificationInfo(self.tableName, self.id, code, byCode=True)
                result = _identification(code, name, urn, version, value, note, CDateInfo(checkDate), value_spr, name_spr, record)
                self._mapCodeToIdentifierInfo[code] = result
                return result
        else:
            return _identification(None, None, None, None, None, None, None, None, None, None)


class CDictInfoMixin:
    u'Примесевый класс для придания поведения словаря к CInfo'
    def __init__(self, dictAttrName='_infoDict'):
        self.__dictAttrName = dictAttrName
        setattr(self, dictAttrName, {})

    def has_key(self, key):
        return getattr(self, self.__dictAttrName).has_key(key)

    def get(self, key, default=None):
        return getattr(self, self.__dictAttrName).get(key, default)

    def iteritems(self):
        return getattr(self, self.__dictAttrName).iteritems()

    def iterkeys(self):
        return getattr(self, self.__dictAttrName).iterkeys()

    def itervalues(self):
        return getattr(self, self.__dictAttrName).itervalues()

    def items(self):
        return getattr(self, self.__dictAttrName).items()

    def keys(self):
        return getattr(self, self.__dictAttrName).keys()

    def values(self):
        return getattr(self, self.__dictAttrName).values()

    def __nonzero__(self):
        return bool(getattr(self, self.__dictAttrName))

    def __len__(self):
        return len(getattr(self, self.__dictAttrName))

    def __contains__(self, key):
        return key in getattr(self, self.__dictAttrName)

    def __getitem__(self, key):
        return getattr(self, self.__dictAttrName).get(key, '')

    def __iter__(self):
        return getattr(self, self.__dictAttrName).iterkeys()


class CInfoList(CInfo):
    u'Базовый класс для представления списков (массивов) объектов при передаче в шаблоны печати'
    def __init__(self, context):
        CInfo.__init__(self, context)
        self._items = []


    def __len__(self):
        self.load()
        return len(self._items)


    def __getitem__(self, key):
        self.load()
        return self._items[key]


    def __iter__(self):
        self.load()
        return iter(self._items)


    def __str__(self):
        self.load()
        return u', '.join([unicode(x) for x in self._items])


    def __nonzero__(self):
        self.load()
        return bool(self._items)


    def filter(self, **kw):
        self.load()

        result = CInfoList(self.context)
        result._loaded = True
        result._ok = True

        for item in self._items:
            if all([item.__getattribute__(key) == value for key, value in kw.iteritems()]):
                result._items.append(item)
        return result


    def __add__(self, right):
        if isinstance(right, CInfoList):
            right.load()
            rightItems = right.items
        elif isinstance(right, list):
            rightItems = right
        else:
            raise TypeError(u'can only concatenate CInfoList or list (not "%s") to CInfoList' % type(right).__name__)
        self.load()

        result = CInfoList(self.context)
        result._loaded = True
        result._ok = True

        result._items = self._items + rightItems
        return result

    def pop(self, index = -1):
        return self._items.pop(index)

    def drop(self):
        self.context.removeInstance(self.__class__, self)
        for item in self._items:
            if hasattr(item, 'drop'):
                item.drop()


class CInfoProxyList(CInfo):
    def __init__(self, context):
        CInfo.__init__(self, context)
#        self._loaded = True
#        self._ok = True
        self._items = []


    def __len__(self):
        return len(self._items)


    def __getitem__(self, key): # чисто-виртуальный
        return None


    def __iter__(self):
        for i in xrange(len(self._items)): # цикл по self._items исп. нельзя т.к. у нас хитрый __getitem__
            yield self.__getitem__(i)


    def __str__(self):
        return u', '.join([unicode(x) for x in self.__iter__()])


    def __nonzero__(self):
        return bool(self._items)


class CDateInfo(object):
    def __init__(self, date=None):
        if date is None:
            self.date = QDate()
        else:
            self.date = forceDate(date)


#    def __unicode__(self):
    def __str__(self):
        return forceString(self.date)


    def toString(self, fmt):
        return unicode(self.date.toString(fmt))


    def __nonzero__(self):
        return bool(self.date)


    def __add__(self, x):
        return forceString(self.date) + unicode(x)


    def __radd__(self,x):
        return unicode(x)+forceString(self.date)


    def __cmp__(self, x):
        ltime = None
        if type(x) == CDateInfo:
            ltime = x.date
        if ltime:
            if ltime > self.date:
                return -1
            elif ltime < self.date:
                return 1
        return 0


    def addYears(self, years):
        if self.date is None:
            return None
        return CDateInfo(self.date.addYears(years))

    year     = property(lambda self: self.date.year()  if self.date else None)
    month    = property(lambda self: self.date.month() if self.date else None)
    day      = property(lambda self: self.date.day()   if self.date else None)


class CTimeInfo(object):
    def __init__(self, time=None):
        self.time = QtCore.QTime() if time is None else time


    def toString(self, fmt=None):
        return unicode(self.time.toString(fmt)) if fmt else formatTime(self.time)

#    def __unicode__(self):


    def __str__(self):
        return formatTime(self.time)


    def __nonzero__(self):
        return bool(self.time.isValid())


    def __add__(self, x):
        return self.toString() + str(x)


    def __radd__(self,x):
        return str(x)+self.toString()

    def __cmp__(self, x):
        ltime = None
        if type(x) == str:
            ltime = QTime().fromString(x, 'h:mm')
        elif type(x) == CTimeInfo:
            ltime = x.time
        if ltime:
            if ltime > self.time:
                return -1
            elif ltime < self.time:
                return 1
        return 0

    hour   = property(lambda self: self.time.hour())
    minute = property(lambda self: self.time.minute())
    second = property(lambda self: self.time.second())


class CDateTimeInfo(object):
    def __init__(self, date=None):
        if date is None:
            self.datetime = QDateTime()
        else:
            self.datetime = forceDateTime(date)


#    def __unicode__(self):
    def __str__(self):
        if self.datetime:
            date = self.datetime.date()
            time = self.datetime.time()
            return forceString(date)+' '+formatTime(time)
        else:
            return ''


    def __cmp__(self, x):
        ltime = None
        if type(x) == CDateTimeInfo:
            ltime = x.datetime
        if ltime:
            if ltime > self.datetime:
                return -1
            elif ltime < self.datetime:
                return 1
        return 0


    def __nonzero__(self):
        return bool(self.datetime)


    def toString(self, fmt):
        return unicode(self.datetime.toString(fmt))


    def __add__(self, x):
        return forceString(self.datetime) + unicode(x)


    def __radd__(self,x):
        return unicode(x)+forceString(self.datetime)


    def addYears(self, years):
        if self.datetime is None:
            return None
        return CDateTimeInfo(self.datetime.addYears(years))

    date   = property(lambda self: self.datetime.date())
    time   = property(lambda self: self.datetime.time())
    year   = property(lambda self: self.datetime.date().year()   if self.datetime else None)
    month  = property(lambda self: self.datetime.date().month()  if self.datetime else None)
    day    = property(lambda self: self.datetime.date().day()    if self.datetime else None)
    hour   = property(lambda self: self.datetime.time().hour()   if self.datetime else None)
    minute = property(lambda self: self.datetime.time().minute() if self.datetime else None)
    second = property(lambda self: self.datetime.time().second() if self.datetime else None)


class CRBInfo(CInfo):
    u'Базовый класс для справочников'
    tableName = '' # for pylint

    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id


    def _load(self):
        assert self.tableName, 'tableName must be defined in derivative'
        db = QtGui.qApp.db
        record = db.getRecord(self.tableName, '*', self.id) if self.id else None
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._initByRecord(record)
            return True
        else:
            self._code = ''
            self._name = ''
            self._initByNull()
            return False


    def _initByRecord(self, record):
        pass


    def _initByNull(self):
        pass


    def __str__(self):
        return self.load()._name

    code = property(lambda self: self.load()._code)
    name = property(lambda self: self.load()._name)


class CRBInfoWithIdentification(CRBInfo, CIdentificationInfoMixin):
    u'Базовый класс для справочников с идентификацией'
    def __init__(self, context, id):
        CRBInfo.__init__(self,  context, id)
        CIdentificationInfoMixin.__init__(self)


class CImageInfo(CInfo):
    htmlTemplate  = '<img src="data:image/png;base64,%s">'

    def __init__(self, context, image):
        CInfo.__init__(self, context)
        self.image  = image


    def _load(self):
        return bool(self.image)


    def _getHtmlTag(self):
            ba = QByteArray()
            buffer  = QBuffer(ba)
            buffer.open(QIODevice.WriteOnly)
            self.image.save(buffer, 'PNG')
            return self.htmlTemplate % buffer.data().toBase64().data()


    def __str__(self):
            return self._getHtmlTag() if self.image else ''


    def scaled(self, width=None, height=None, keepAspectRatio=False, smoothTransformation=True):
        if self.image:
            if width and height:
                image = self.image.scaled(width,
                                          height,
                                          Qt.KeepAspectRatio if keepAspectRatio else Qt.IgnoreAspectRatio,
                                          Qt.SmoothTransformation if smoothTransformation else Qt.FastTransformation)
            elif width:
                image = self.image.scaledToWidth(width, Qt.SmoothTransformation if smoothTransformation else Qt.FastTransformation)
            elif height:
                image = self.image.scaledToHeight(height, Qt.SmoothTransformation if smoothTransformation else Qt.FastTransformation)
            else:
                image = self.image
            return CImageInfo(self.context, image)
        else:
            return self


    width  = property(lambda self: self.image.width() if self.image else 0)
    height = property(lambda self: self.image.height() if self.image else 0)
