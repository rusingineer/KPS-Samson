# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from functools import wraps
import datetime
import json
import locale
import os
import re
import sys
import traceback
import types

import requests
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QDateTime, QString, QTime, QVariant, QByteArray, QObject, QEvent


# WTF?
# преобразуем строку в int с учетом пустой строки
lenient_int = lambda string: int(string) if string.strip() else 0

# WTF?
# преобразуем вх. данные в строку (для сортировки)
def conv_data(data):
    if isinstance(data, int):
        return str(data)
    elif isinstance(data, types.NoneType):
        return ''
    elif isinstance(data, unicode):
        return data.strip().lower()
    elif isinstance(data, QString):
        return "%s" % data
    else:
        return data


class smartDict:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return self.__dict__.__iter__()

    def __contain__(self, key):
        return key in self.__dict__

    def clear(self):
        self.__dict__.clear()

    def copy(self):
        return smartDict(**self.__dict__)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def setdefault(self, key, default=None):
        return self.__dict__.setdefault(key, default)

    def update(self, d, **i):
        return self.__dict__.update(d, **i)

    def items(self):
        return self.__dict__.items()

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def iteritems(self):
        return self.__dict__.iteritems()

    def iterkeys(self):
        return self.__dict__.iterkeys()

    def itervalues(self):
        return self.__dict__.itervalues()

    def has_key(self, key):
        return self.__dict__.has_key()


def anyToUnicode(s, encodingHint=None): # это для обработки ошибок.
    # в python2 сообщения об ошибках, особенно когда источником сообщения об ошибке
    # выступает OS (tcp/ip, serial etc.) могут быть в разных кодировках.
    # я не имею ни возможности ни желания проверить все варианты, поэтому делаю так
    if isinstance(s, unicode):
        return s
    if os.name == 'nt':
        encodingList = ( encodingHint,
                         locale.getpreferredencoding(), # по уставу
                         'utf8', # as fallback
                         'cp1251',
                         'cp866',
                       )
    else:
        encodingList = ( encodingHint,
                         locale.getpreferredencoding(), # по уставу
                         'utf8', # as fallback
                         'cp1251', # для крипто-...
                       )

    for encoding in encodingList:
        try:
            if encoding:
                return s.decode(encoding)
        except:
            pass
    return unicode(repr(s))


def exceptionToUnicode(e):
    # Общая "помойка" для журналирования исключительных ситуаций.
    # поскольку exception-ы иногда могут иметь дополнительную информацию
    # предпочтительно использовать более специфический код.

    if isinstance(e, AssertionError):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_traceback:
            fileName, lineNnum, funcName, text = traceback.extract_tb(exc_traceback)[-1]
            return u'Assertion failed %s@%s:%d %s' % (funcName, fileName, lineNnum, anyToUnicode(e.message or text))
        else:
            return u'Assertion failed %s' % ( anyToUnicode(e.message) )

    try:
        result = unicode(e)
        if result:
            return result
    except:
        pass

    try:
        result = anyToUnicode(str(e))
        if result:
            return result
    except:
        pass
    
    try:
        result = unicode(e.message) #если в ошибке Shutil.error есть кириллица (существующий путь в сохранении, например), 
        if result:                  #функция не может декодировать её. Декодируем напрямую сообщение ошибки.
            return result
    except:
        pass

    return repr(e)

#############################################################################

def getPref(dict, key, default):
    return dict.get(unicode(key).lower(), default)

def getPrefDate(dict, key, default):
    return forceDate(dict.get(unicode(key).lower(), default))

def getPrefTime(dict, key, default):
    return forceTime(dict.get(unicode(key).lower(), default))

def getPrefRef(dict, key, default):
    return forceRef(dict.get(unicode(key).lower(), default))

def getPrefBool(dict, key, default):
    return forceBool(dict.get(unicode(key).lower(), default))

def getPrefInt(dict, key, default):
    return forceInt(dict.get(unicode(key).lower(), default))

def getPrefString(dict, key, default):
    return forceString(dict.get(unicode(key).lower(), default))


def setPref(dict, key, value):
    dict[unicode(key).lower()] = value


def trim(s):
    return u' '.join(unicode(s).split())


def nameCase(s):
    r = u''
    if s:
        up = True
        for c in s:
            if c.isalpha():
                if up:
                    r += c.upper()
                    up = False
                else:
                    r += c.lower()
            else:
                up = True
                r += c
    return r

def isNameValid(name, isLastName = False):
    symbolsPattern = ur'''[^а-яА-ЯёЁ\- .A-Z',()]+.*'''
    termsPattern = ur'(^([^а-яА-ЯёЁ\w])|([^а-яА-ЯёЁ\w\.])$)|([.,\'\-][^а-яА-ЯёЁ\w\s])|([^а-яА-ЯёЁ\w\s][.,\'\-])|([.,\'\-]{2,})|(^[A-Z])'
    if isLastName:
        termsPattern = termsPattern.replace(ur'|([^а-яА-ЯёЁ\w\.])$)|', ur'|([^а-яА-ЯёЁ\w])$)|')
    if not re.search(symbolsPattern, forceStringEx(name)) and not re.search(termsPattern, forceStringEx(name)):
        counter = 0
        for symbol in name:
            if symbol == '(':
                counter += 1
            elif symbol == ')':
                counter -= 1
            if counter < 0:
                return False
        if counter == 0:
            return True
        else:
            return False
    else:
        return False


def splitDocSerial(serial):
    for c in '-=/_|':
        serial = serial.replace(c,' ')
    parts = trim(serial).partition(' ')
    return parts[0], parts[2]


def addDots(s):
    if s and not s.endswith('...'):
        return s + '...'
    else:
        return s


def addDotsBefore(s):
    if s and not s.startswith('...'):
        return '...' + s
    else:
        return s


def addDotsEx(s):
    if s:
        result = s
        if not s.startswith('...'): result = '...' + result
        if not s.endswith('...'):   result = result + '...'
        return result
    else:
        return s


def toVariant(v):
    if v is None:
        return QVariant()
    if isinstance(v, QVariant):
        return v
    if isinstance(v, datetime.date):
        return QVariant(QDate(v))
    if isinstance(v, datetime.datetime):
        return QVariant(QDateTime(v))
    if isinstance(v, datetime.time):
        return QVariant(QTime(v))
    return QVariant(v)


def variantEq(value1, value2):
    return (value1.isNull() and value2.isNull()) or (value1 == value2)


#############################################################################


def forceBool(val):
    if isinstance(val, QVariant):
        return val.toBool()
    return bool(val)


def forceDate(val):
    if isinstance(val, QVariant):
        return val.toDate()
    if isinstance(val, QDate):
        return val
    if isinstance(val, QDateTime):
        return val.date()
    if val is None:
        return QDate()
    return QDate(val)


def forceTime(val):
    if isinstance(val, QVariant):
        return val.toTime()
    if isinstance(val, QTime):
        return val
    if isinstance(val, QDateTime):
        return val.time()
    if val is None:
        return QTime()
    return QTime(val)


def forceDateTime(val):
    if isinstance(val, QVariant):
        return val.toDateTime()
    if isinstance(val, QDateTime):
        return val
    if isinstance(val, QDate):
        return QDateTime(val)
    if isinstance(val, QTime):
        return QDateTime(QDate(), val)
    if val is None:
        return QDateTime()
    return QDateTime(val)


def forceInt(val):
    if isinstance(val, QVariant):
        return val.toInt()[0]
    elif val is None:
        return 0
    return int(val)


def forceLong(val):
    if isinstance(val, QVariant):
        return val.toLongLong()[0]
    elif val is None:
        return 0L
    return long(val)


def forceRef(val):
    if isinstance(val, QVariant):
        if val.isNull():
            val = None
        else:
            val = val.toInt()[0]
            if val == 0:
                val = None
    return val


def forceString(val):
    if isinstance(val, QVariant):
        valType = val.type()
        if  valType == QVariant.Date:
            return formatDate(val.toDate())
        elif valType == QVariant.DateTime:
            return formatDateTime(val.toDateTime())
        elif valType == QVariant.Time:
            return formatTime(val.toTime())
        else:
            val = val.toString()
    if isinstance(val, QDate):
        return formatDate(val)
    if isinstance(val, QDateTime):
        return formatDateTime(val)
    if isinstance(val, QTime):
        return formatTime(val)
    if val is None:
        return u''
    return unicode(val)


def forceStringEx(val):
    return trim(forceString(val))


def forceDouble(val):
    if isinstance(val, QVariant):
        return val.toDouble()[0]
    else:
        return float(val)


def formatBool(val):
    if forceBool(val):
        return u'да'
    else:
        return u'нет'


def pyTime(time):
    if time:
        return time.toPyTime()
    else:
        return None


def pyDate(date):
    if date:
        return date.toPyDate()
    else:
        return None


def pyDateTime(date):
    if date:
        return date.toPyDateTime()
    else:
        return None


def toDateTimeWithoutSeconds(value):
    if isinstance(value, QDateTime):
        if value and value.isValid():
            time = value.time()
            newTime = QTime(time.hour(), time.minute())
            return QDateTime(value.date(), newTime)
    elif isinstance(value, QDate):
        if value:
            return QDateTime(value, QTime(0, 0))
    return QDateTime()


def getTimeNoSecond(time):
    if isinstance(time, QTime):
        return QTime(time.hour(), time.minute())
    return QTime()

#############################################################################


def formatDate(val):
    if isinstance(val, QVariant):
        val = val.toDate()
    return unicode(val.toString('dd.MM.yyyy'))


def formatTime(val):
    if isinstance(val, QVariant):
        val = val.toDate()
    return unicode(val.toString('H:mm'))


def formatDateTime(val):
    if isinstance(val, QVariant):
        val = val.toDateTime()
    return unicode(val.toString('dd.MM.yyyy H:mm'))


def formatNameInt(lastName, firstName, patrName):
    return trim(lastName+' '+firstName+' '+patrName)


def formatName(lastName, firstName, patrName):
    lastName  = nameCase(forceStringEx(lastName))
    firstName = nameCase(forceStringEx(firstName))
    patrName  = nameCase(forceStringEx(patrName))
    return formatNameInt(lastName, firstName, patrName)


def formatShortNameInt(lastName, firstName, patrName):
    return trim(lastName + ' ' +((firstName[:1]+'.') if firstName else '') + ((patrName[:1]+'.') if patrName else ''))


def formatShortName(lastName, firstName, patrName):
    lastName  = nameCase(forceStringEx(lastName))
    firstName = nameCase(forceStringEx(firstName))
    patrName  = nameCase(forceStringEx(patrName))
    return formatShortNameInt(lastName, firstName, patrName)


def formatNameByRecord(record):
    return formatName(record.value('lastName'),
                      record.value('firstName'),
                      record.value('patrName'))


def formatSex(sex):
    sex = forceInt(sex)
    if sex == 1:
        return u'М'
    elif sex == 2:
        return u'Ж'
    else:
        return u''


def parseSex(sexAsStr):
    sexAsStr = sexAsStr.upper()
    if sexAsStr.startswith(u'М'):
        return 1
    elif sexAsStr.startswith(u'Ж'):
        return 2
    else:
        return 0


def formatAttachOrg(attachOrg):
    if attachOrg == 0:
        return u'Любое'
    elif attachOrg == 1:
        return u'Базовое'
    elif attachOrg ==2:
        return u'Любое кроме базового'
    else:
        return u''


def formatServiceArea(serviceArea):
    if serviceArea == 0:
        return u'Любая'
    elif serviceArea == 1:
        return u'Нас.пункт'
    elif serviceArea == 2:
        return u'Нас.пункт + область'
    elif serviceArea == 3:
        return u'Область'
    elif serviceArea == 4:
        return u'Область + Другие'
    elif serviceArea == 5:
        return u'Другие'
    else:
        return u''


def formatSNILS(SNILS):
    if SNILS:
        s = forceString(SNILS)+' '*14
        return s[0:3]+'-'+s[3:6]+'-'+s[6:9]+' '+s[9:11]
    else:
        return u''


def unformatSNILS(SNILS):
    return forceString(SNILS).replace('-', '').replace(' ', '')


def calcSNILSCheckCode(SNILS):
    result = 0
    for i in xrange(9):
        result += (9-i)*int(SNILS[i])
    result = result % 101
    if result == 100:
        result = 0
    return '%02.2d' % result


def checkSNILS(SNILS):
    raw = unformatSNILS(SNILS)
    if len(raw) == 11:
        return raw[:9] <= '001001998' or raw[-2:] == calcSNILSCheckCode(raw)
    return False


def fixSNILS(SNILS):
    raw = unformatSNILS(SNILS)
    return (raw+'0'*11)[:9] + calcSNILSCheckCode(raw)


def checkDocCode(code):
    pattern = '^(\d{3}[- ]{1}\d{3})?$'
    return re.match(pattern, code) is not None


def agreeNumberAndWord(num, words):
    u"""
        Согласовать число и слово:
        num - число, слово = (один, два, много)
        agreeNumberAndWord(12, (u'год', u'года', u'лет'))
    """
    if num<0: num = -num
    if (num/10)%10 != 1:
        if num%10 == 1:
            return words[0]
        elif 1 < num%10 < 5:
            return words[1]
    return words[-1]


def formatNum(num, words):
    return u'%d %s' % (num, agreeNumberAndWord(num,words))


def formatNum1(num, words):
    if num == 1:
        return agreeNumberAndWord(num,words)
    else:
        return u'%d %s' % (num, agreeNumberAndWord(num,words))


def formatYears(years):
    return '%d %s' % (years, agreeNumberAndWord(years, (u'год', u'года', u'лет')))


def formatMonths(months):
    return '%d %s' % (months, agreeNumberAndWord(months, (u'месяц', u'месяца', u'месяцев')))


def formatWeeks(weeks):
    return '%d %s' % (weeks, agreeNumberAndWord(weeks, (u'неделя', u'недели', u'недель')))


def formatDays(days):
    return '%d %s' % (days, agreeNumberAndWord(days, (u'день', u'дня', u'дней')))


def formatYearsMonths(years, months):
    if years == 0:
        return formatMonths(months)
    elif months == 0:
        return formatYears(years)
    else:
        return formatYears(years) + ' ' + formatMonths(months)


def formatMonthsWeeks(months, weeks):
    if  months == 0:
        return formatWeeks(weeks)
    elif weeks == 0:
        return formatMonths(months)
    else:
        return formatMonths(months) + ' ' + formatWeeks(weeks)


def formatRecordsCountInt(count):
    return '%d %s' % (count, agreeNumberAndWord(count, (u'запись', u'записи', u'записей')))


def formatRecordsCount(count):
    if count:
        return u'в списке '+formatRecordsCountInt(count)
    else:
        return u'список пуст'


def formatRecordsCount2(count, totalCount):
    if count and totalCount and count<totalCount:
        return formatRecordsCount(totalCount)+ u', показаны первые '+formatRecordsCountInt(count)
    else:
        return formatRecordsCount(count)


def formatList(list):
    if len(list)>2:
        return u' и '.join([', '.join(list[:-1]), list[-1]])
    else:
        return u' и '.join(list)


def splitText(text, widths):
    result = []
    if not text:
        return result

    width = widths[0]

    lines = text.splitlines()
    count = 0

    for line in lines:
        p = 0
        l = len(line)
        while p<l:
            while line[p:p+1].isspace():
                p += 1
            s = p + width
            if s>=l:
                breakpos = s
            else:
                breakpos = line.rfind(' ', p, s+1)
            if breakpos<0:
                breakpos = max([line.rfind(sep, p, s) for sep in '-,.;:!?)]}\\|/'])
                if breakpos>= 0:
                    breakpos+=1
            if breakpos<0:
                breakpos = s
            result.append(line[p:breakpos])
            p = breakpos
            count += 1
            width = widths[count if count<len(widths) else -1]
    return result


def foldText(text, widths):
    return '\n'.join(splitText(text, widths))


def disassembleSeconds(seconds):
    seconds = abs(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return (days, hours, minutes, seconds)


#############################################################################


def calcAgeInDays(birthDay, today):
    assert isinstance(birthDay, QDate)
    assert isinstance(today, QDate)
    return birthDay.daysTo(today)


def calcAgeInWeeks(birthDay, today):
    return calcAgeInDays(birthDay, today)/7


def calcAgeInMonths(birthDay, today):
    assert isinstance(birthDay, QDate)
    assert isinstance(today, QDate)

    bYear  = birthDay.year()
    bMonth = birthDay.month()
    bDay   = birthDay.day()

    tYear  = today.year()
    tMonth = today.month()
    tDay   = today.day()

    result = (tYear-bYear)*12+(tMonth-bMonth)
    if bDay > tDay:
        result -= 1
    return result


def calcAgeInYears(birthDay, today):
    assert isinstance(birthDay, QDate)
    assert isinstance(today, QDate)

    bYear  = birthDay.year()
    bMonth = birthDay.month()
    bDay   = birthDay.day()

    tYear  = today.year()
    tMonth = today.month()
    tDay   = today.day()

    result = tYear-bYear
    if bMonth>tMonth or (bMonth == tMonth and bDay > tDay):
        result -= 1
    return result


def calcAgeTuple(birthDay, today):
    if not today or today.isNull():
        today = QDate.currentDate()
    elif isinstance(today, QDateTime):
        today = today.date()
    d = calcAgeInDays(birthDay, today)
    if d>=0:
        return (d,
                d/7,
                calcAgeInMonths(birthDay, today),
                calcAgeInYears(birthDay, today)
               )
    else:
        return None


def formatAgeTuple(ageTuple, bd, td):
    if not ageTuple:
        return u'ещё не родился'
    (days, weeks, months, years) = ageTuple
    if years>=7:
        return formatYears(years)
    elif years>=1:
        return formatYearsMonths(years, months-12*years)
    elif months>=1:
        if not td:
            td = QDate.currentDate()
        return formatMonthsWeeks(months, bd.addMonths(months).daysTo(td)/7)
    else:
        return formatDays(days)


def calcAge(birthDay, today=None):
    bd = forceDate(birthDay)
    td = forceDate(today) if today else QDate.currentDate()
    ageTuple = calcAgeTuple(bd, td)
    return formatAgeTuple(ageTuple, bd, td)


def getRetirementAge(date):
    # получить нетрудоспособный возраст (М, Ж) на определенную дату
    if isinstance(date, QDateTime):
        date = date.date()
    if not date or not date.isValid():
        return (60, 55)
    year = date.year()
    if year <= 2020:
        return (60, 55)
    elif year == 2021:
        return (61, 56)
    elif year in (2022, 2023):
        return (62, 57)
    elif year in (2024, 2025):
        return (63, 58)
    elif year in (2026, 2027):
        return (64, 59)
    elif year >= 2028:
        return (65, 60)


def isRetirementAge(sex, age, date):
    ageM, ageF = getRetirementAge(date)
    return (sex == 1 and age >= ageM) or (sex == 2 and age >= ageF)


def firstWeekDay(date):
#    return date.addDays(-(date.dayOfWeek()-1))
    return date.addDays(1-date.dayOfWeek())


def lastWeekDay(date):
#    return firstWeekDay.addDays(6)
    return date.addDays(7-date.dayOfWeek())


def firstMonthDay(date):
    return QDate(date.year(), date.month(), 1)


def lastMonthDay(date):
    return firstMonthDay(date).addMonths(1).addDays(-1)


def firstQuarterDay(date):
    month = ((date.month()-1)/3)*3+1
    return QDate(date.year(), month, 1)


def lastQuarterDay(date):
    return firstQuarterDay(date).addMonths(3).addDays(-1)


def firstHalfYearDay(date):
    month = 1 if date.month() < 7 else 7
    return QDate(date.year(), month, 1)


def lastHalfYearDay(date):
    return firstHalfYearDay(date).addMonths(6).addDays(-1)


def firstYearDay(date):
    return QDate(date.year(), 1, 1)


def lastYearDay(date):
    return QDate(date.year(), 12, 31)

#############################################################################


def setBits(val, mask, bits):
    return ( val & ~mask ) | ( bits & mask )


def checkBits(val, mask, bits):
    return ( val & mask ) == ( bits & mask )


#############################################################################

def sorry(widget=None):
    widget = widget or QtGui.qApp.focusWidget() or QtGui.qApp.activeWindow() or QtGui.qApp.mainWindow
    QtGui.QMessageBox.information(widget,
                                u'не реализовано',
                                u'к сожалению не реализовано :(',
                                QtGui.QMessageBox.Ok,
                                QtGui.QMessageBox.Ok
                                )


def oops(widget=None):
    widget = widget or QtGui.qApp.focusWidget() or QtGui.qApp.activeWindow() or QtGui.qApp.mainWindow
    QtGui.QMessageBox.information(widget,
                                u'ой',
                                u'косяк, однако! :\'(',
                                QtGui.QMessageBox.Ok,
                                QtGui.QMessageBox.Ok
                                )

def getListChunks(lst, n):
    """
        Разбивает один длинный список на несколько равных частей длиной `n`.
        Например:
        ```
        idList = [1, 2, 3, 4, 5, 6]
        lst1 = list(getListChunks(idList, 1)))
        lst2 = list(getListChunks(idList, 2)))
        lst3 = list(getListChunks(idList, 3)))
        lst4 = list(getListChunks(idList, 4)))
        assert lst1 == [[1], [2], [3], [4], [5], [6]]
        assert lst2 == [[1, 2], [3, 4], [5, 6]]
        assert lst3 == [[1, 2, 3], [4, 5, 6]]
        assert lst4 == [[1, 2, 3, 4], [5, 6]]
        ```
    """
    assert n > 0, u"размер чанка не может быть нулевой"
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# WFT?
def get_date(d):
    d=forceDate(d)
    if d and 1800<=d.year()<=2200:
        return d.toPyDate()
    else:
        return None


# WFT?
def getInfisCodes(KLADRCode, KLADRStreetCode, house, corpus):
    db = QtGui.qApp.db
    area = ''
    region = ''
    npunkt = ''
    street = '*'
    streettype = ''
    npunkt=forceString(db.translate('kladr.KLADR', 'CODE', KLADRCode, 'NAME'))
    if KLADRCode.startswith('78'):
        OCATO=forceString(db.translate('kladr.STREET', 'CODE', KLADRStreetCode, 'OCATD'))
        if KLADRStreetCode and not OCATO:
            firstPart = house.split('/')[0]
            if re.match('^\d+$', firstPart):
                intHouse = int(firstPart)
            else:
                intHouse = None
            table = db.table('kladr.DOMA')
            cond = table['CODE'].like(KLADRStreetCode[:-2]+'%')
            list = db.getRecordList(table, 'CODE,NAME,KORP,OCATD', where=cond)
            for record in list:
                NAME=forceString(record.value('NAME'))
                KORP=forceString(record.value('KORP'))
                if checkHouse(NAME, KORP, house, intHouse, corpus):
                    OCATO = forceString(record.value('OCATD'))
                    break
        if OCATO:
            area = forceString(db.translate('kladr.OKATO', 'CODE', OCATO[:5], 'infis'))
        if KLADRCode!='7800000000000':
            region = forceString(db.translate(
                'kladr.KLADR', 'CODE', KLADRStreetCode[:-6]+'00', 'infis'))
            if region == u'СПб':
                region = area
        else:
            region = area
        street=forceString(db.translate('kladr.STREET', 'CODE', KLADRStreetCode, 'infis'))
        SOCR=forceString(db.translate('kladr.STREET', 'CODE', KLADRStreetCode, 'SOCR'))
        streettype=forceString(db.translate('kladr.SOCRBASE', 'SCNAME', SOCR, 'infisCODE'))
    elif KLADRCode.startswith('47'):
        KLADRArea   = KLADRCode[:2]+'0'*11
        KLADRRegion = KLADRCode[:5]+'0'*8
        area = forceString(db.translate('kladr.KLADR', 'CODE', KLADRArea, 'infis'))
        if KLADRArea != KLADRRegion:
            region = forceString(db.translate('kladr.KLADR', 'CODE', KLADRRegion, 'infis'))
        else:
            region = area
    else:
        KLADRArea   = KLADRCode[:2]+'0'*11
        area = forceString(db.translate('kladr.KLADR', 'CODE', KLADRArea, 'infis'))
        table = db.table('kladr.KLADR')
        region = area
        code = KLADRCode
        SOCR=forceString(db.translate('kladr.STREET', 'CODE', KLADRStreetCode, 'SOCR'))
        streettype=forceString(db.translate('kladr.SOCRBASE', 'SCNAME', SOCR, 'infisCODE'))
        while True:
            record = db.getRecordEx(table, 'parent, infis', table['CODE'].eq(code))
            if record:
                parent = forceString(record.value(0))
                infis  = forceString(record.value(1))
                if len(parent) <= 3 and infis:
                    region = infis
                    break
                else:
                    code = parent+'0'*(13-len(parent))
            else:
                break
    return area, region, npunkt, street, streettype


def checkHouse(rHouse, rCorpus, house, intHouse, corpus):
    for range in rHouse.split(','):
        if intHouse:
            simple = re.match('^(\d+)-(\d+)$', range)
            if simple:
                if int(simple.group(1)) <= intHouse <= int(simple.group(2)):
                    return True
                else:
                    continue
            if intHouse%2 == 0:
                even = re.match(u'^Ч\((\d+)-(\d+)\)$', range)
                if even:
                    if int(even.group(1)) <= intHouse <= int(even.group(2)):
                        return True
                    else:
                        continue
            else:
                odd = re.match(u'^Н\((\d+)-(\d+)\)$', range)
                if odd:
                    if int(odd.group(1)) <= intHouse <= int(odd.group(2)):
                        return True
                    else:
                        continue
            simple = re.match('^(\d+)', range)
            if simple:
                if int(simple.group(1)) == intHouse:
                    return True
                else:
                    continue
            if intHouse%2 == 0:
                even = re.match(u'^Ч\((\d+)\)', range)
                if even:
                    if int(even.group(1)) == intHouse:
                        return True
                    else:
                        continue
            else:
                odd = re.match(u'^Н\((\d+)\)', range)
                if odd:
                    if int(odd.group(1)) == intHouse:
                        return True
                    else:
                        continue
        if house == range:
            return True
    return False


def copyFields(newRecord, record):
    for i in xrange(newRecord.count()):
        newRecord.setValue(i, record.value(newRecord.fieldName(i)))


def quote(str, sep='\''):
    magicChars = { '\\' : '\\\\',
                   sep  : '\\'+sep,
#                   '\n' : '\\n',
#                   '\r' : '\\r',
#                   '\0' : '\x00'
                 }
    res = ''
    for c in str:
        res += magicChars.get(c, c)
    return sep + res + sep



#WTF?
def getDentitionActionTypeId():
    dentActionTypeId = None
    parodentActionTypeId = None
    db = QtGui.qApp.db
    tableActionType = db.table('ActionType')
    recordParodent = db.getRecordEx(tableActionType,
                                    [tableActionType['id']],
                                    [tableActionType['flatCode'].like(u'parodentInsp'),
                                    tableActionType['deleted'].eq(0)],
                                    tableActionType['flatCode'].name())
    if recordParodent:
        parodentActionTypeId = forceRef(recordParodent.value('id'))
    recordDentition = db.getRecordEx(tableActionType,
                                    [tableActionType['id']],
                                    [tableActionType['flatCode'].like(u'dentitionInspection'),
                                    tableActionType['deleted'].eq(0)],
                                    tableActionType['flatCode'].name())
    if recordDentition:
        dentActionTypeId = forceRef(recordDentition.value('id'))
    return dentActionTypeId, parodentActionTypeId


def getMKB():
    return '''(SELECT Diagnosis.MKB
FROM Diagnosis
LEFT JOIN Diagnostic ON Diagnostic.diagnosis_id=Diagnosis.id
LEFT JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id=rbDiagnosisType.id
WHERE Diagnostic.event_id = Event.id
    AND Diagnosis.deleted = 0
    AND Diagnostic.deleted = 0
    AND rbDiagnosisType.code IN ('1', '2')
ORDER BY rbDiagnosisType.code
LIMIT 1) AS MKB'''


def getBasic_MKB():
    return '''(SELECT Diagnosis.MKB
FROM Diagnosis INNER JOIN Diagnostic ON Diagnostic.diagnosis_id=Diagnosis.id
INNER JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id=rbDiagnosisType.id
WHERE Diagnostic.event_id = Event.id AND Diagnosis.deleted = 0 AND Diagnostic.deleted = 0
AND rbDiagnosisType.code = '7' LIMIT 1) AS Basic_MKB'''


def getMKBInfo():
    return '''(SELECT CONCAT_WS('  ', MKB.DiagID, MKB.DiagName, Diagnostic.freeInput)
FROM Diagnosis INNER JOIN Diagnostic ON Diagnostic.diagnosis_id=Diagnosis.id
INNER JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id = rbDiagnosisType.id
INNER JOIN MKB ON MKB.DiagID = Diagnosis.MKB
WHERE Diagnostic.event_id = Event.id AND Diagnosis.deleted = 0 AND Diagnostic.deleted = 0
AND (rbDiagnosisType.code = '1'
OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
AND DC.event_id = Event.id AND DC.deleted = 0
LIMIT 1)))) LIMIT 1) AS MKBInfo'''


def isMKB(MKBFrom, MKBTo):
    return '''EXISTS(SELECT Diagnosis.id
FROM Diagnosis
INNER JOIN Diagnostic ON Diagnostic.diagnosis_id=Diagnosis.id
INNER JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id=rbDiagnosisType.id
WHERE Diagnostic.event_id = Event.id AND Diagnosis.deleted = 0 AND Diagnostic.deleted = 0
AND Diagnosis.MKB >= '%s' AND Diagnosis.MKB <= '%s'
AND (rbDiagnosisType.code = '1'
OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
AND DC.event_id = Event.id AND DC.deleted = 0
LIMIT 1)))))'''%(MKBFrom, MKBTo)


def getDataOSHB():
    return '''(SELECT CONCAT_WS('  ', OSHB.code, OSHB.name, IF(OSHB.sex=1, \'%s\', IF(OSHB.sex=2, \'%s\', ' ')))
FROM ActionPropertyType AS APT
INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
INNER JOIN ActionProperty_HospitalBed AS APHB ON APHB.id=AP.id
INNER JOIN OrgStructure_HospitalBed AS OSHB ON OSHB.id=APHB.value
WHERE APT.actionType_id=Action.actionType_id AND AP.action_id=Action.id AND AP.deleted=0 AND APT.deleted=0
AND APT.typeName = 'HospitalBed') AS bedCodeName'''%(forceString(u''' /М'''), forceString(u''' /Ж'''))


def getAgeRangeCond(ageFor, ageTo):
    date = u'Event.setDate' if QtGui.qApp.defaultKLADR()[:2] == u'23' else u'Action.begDate'
    return '''(%s >= ADDDATE(Client.birthDate, INTERVAL %d YEAR))
           AND (%s < ADDDATE(Client.birthDate, INTERVAL %d YEAR))''' % (date, ageFor, date, ageTo+1)


def getHospDocumentLocation():
    return '''(SELECT rbDocumentTypeLocation.name FROM Client_DocumentTracking
        LEFT JOIN Client_DocumentTrackingItem ON Client_DocumentTrackingItem.master_id = Client_DocumentTracking.id
        LEFT JOIN rbDocumentTypeForTracking ON rbDocumentTypeForTracking.id = Client_DocumentTracking.documentTypeForTracking_id
        LEFT JOIN rbDocumentTypeLocation ON rbDocumentTypeLocation.id = Client_DocumentTrackingItem.documentLocation_id
        WHERE Client_DocumentTracking.client_id = Client.id
        AND rbDocumentTypeForTracking.showInClientInfo = 1
        AND Client_DocumentTracking.documentNumber = Event.externalId order by Client_DocumentTrackingItem.id desc limit 1) as hospDocumentLocation'''


def getHospDocumentLocationInfo():
    return '''(SELECT CONCAT_WS('  ', rbDocumentTypeLocation.name,  rbDocumentTypeLocation.color)
    FROM Client_DocumentTracking
        LEFT JOIN Client_DocumentTrackingItem ON Client_DocumentTrackingItem.master_id = Client_DocumentTracking.id
        LEFT JOIN rbDocumentTypeForTracking ON rbDocumentTypeForTracking.id = Client_DocumentTracking.documentTypeForTracking_id
        LEFT JOIN rbDocumentTypeLocation ON rbDocumentTypeLocation.id = Client_DocumentTrackingItem.documentLocation_id
    WHERE Client_DocumentTracking.client_id = Client.id
        AND rbDocumentTypeForTracking.showInClientInfo = 1
        AND Client_DocumentTracking.documentNumber = Event.externalId
    ORDER BY Client_DocumentTrackingItem.documentLocationDate desc, Client_DocumentTrackingItem.documentLocationTime desc
    LIMIT 1) AS documentLocationInfo'''


# ####################################################

def dict2json(t):
    return json.dumps(t)

def json2dict(j):
    return json.loads(j)

def formatRecordAsJson(table, id, fieldNameList=None):
    return dict2json(formatRecordAsDict(table, id, fieldNameList))

def formatRecordAsDict(table, id, fieldNameList=None):
    result = {}
    record = QtGui.qApp.db.getRecord(table, fieldNameList if fieldNameList else '*', id)
    for fieldIdx in xrange(record.count()):
        result[unicode(record.fieldName(fieldIdx))] = forceString(record.value(fieldIdx))
    return result


# ##################################################

def withWaitCursor(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        QtGui.qApp.setWaitCursor()
        try:
            return f(*args, **kwargs)
        finally:
            QtGui.qApp.restoreOverrideCursor()
    return wrapper


# ##################################################


class CColsMovingFeature:
    def enableColsHide(self):
        header = self.horizontalHeader()
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self.headerMenu)
        self.__headerColsHidingAvailable = True

    def headerColsHidingAvailable(self):
        try:
            return self.__headerColsHidingAvailable
        except AttributeError:
            return False

    def enableColsMove(self):
        self.horizontalHeader().setMovable(True)

    def headerMenu(self, pos):
        pos2 = QtGui.QCursor().pos()
        header = self.horizontalHeader()
        menu = QtGui.QMenu()
        checkedActions = []
        for i, col in enumerate(self.model().cols()):
            action = QtGui.QAction(forceString(col.title()), self)
            action.setCheckable(True)
            action.setData(i)
            action.setEnabled(col.switchOff())
            if not header.isSectionHidden(i):
                action.setChecked(True)
                checkedActions.append(action)
            menu.addAction(action)
        if len(checkedActions) == 1:
            checkedActions[0].setEnabled(False)
        selectedItem = menu.exec_(pos2)
        if selectedItem:
            section = forceInt(selectedItem.data())
            if header.isSectionHidden(section):
                header.showSection(section)
            else:
                header.hideSection(section)


def getExSubclassName(s, MKB):
    d = list(s)
    step = 5 - len(d)
    if step > 0:
        for i in range(0, step):
            d.append(u'')
    if not d or len(d) > 5:
        d = [u'', u'', u'', u'', u'']
    db = QtGui.qApp.db
    tableMKBExSC = db.table('rbMKBExSubclass')
    tableMKBExSCItem = db.table('rbMKBExSubclass_Item')
    tableMKB_ExSubclass = db.table('MKB_ExSubclass')
    tableMKB = db.table('MKB')
    queryTable = tableMKB.innerJoin(tableMKB_ExSubclass, tableMKB_ExSubclass['master_id'].eq(tableMKB['id']))
    queryTable = queryTable.innerJoin(tableMKBExSC, tableMKBExSC['id'].eq(tableMKB_ExSubclass['exSubclass_id']))
    queryTable = queryTable.innerJoin(tableMKBExSCItem, tableMKBExSCItem['master_id'].eq(tableMKBExSC['id']))
    result = u''
    for position, val in enumerate(d):
        record = None
        position += 6
        if len(MKB) > 3:
            MKBF = MKB[:5] if len(MKB) > 5 else MKB
            cond = [tableMKB['DiagID'].like(MKBF),
                    tableMKBExSC['position'].eq(position),
                    tableMKBExSCItem['code'].eq(val)]
            record = db.getRecordEx(queryTable, [tableMKBExSC['name']], cond)
        if not record:
            MKBF = MKB[:3]
            cond = [tableMKB['DiagID'].like(MKBF),
                    tableMKBExSC['position'].eq(position),
                    tableMKBExSCItem['code'].eq(val)]
            record = db.getRecordEx(queryTable, [tableMKBExSC['name']], cond)
        if record:
            result += forceStringEx(record.value('name'))
    return result

def getExSubclassItemLastName(s, MKB):
    d = list(s)
    step = 5 - len(d)
    if step > 0:
        for i in range(0, step):
            d.append(u'')
    if not d or len(d) > 5:
        d = [u'', u'', u'', u'', u'']
    db = QtGui.qApp.db
    tableMKBExSC = db.table('rbMKBExSubclass')
    tableMKBExSCItem = db.table('rbMKBExSubclass_Item')
    tableMKB_ExSubclass = db.table('MKB_ExSubclass')
    tableMKB = db.table('MKB')
    queryTable = tableMKB.innerJoin(tableMKB_ExSubclass, tableMKB_ExSubclass['master_id'].eq(tableMKB['id']))
    queryTable = queryTable.innerJoin(tableMKBExSC, tableMKBExSC['id'].eq(tableMKB_ExSubclass['exSubclass_id']))
    queryTable = queryTable.innerJoin(tableMKBExSCItem, tableMKBExSCItem['master_id'].eq(tableMKBExSC['id']))
    result = u''
    for position, val in enumerate(d):
        record = None
        position += 6
        if len(MKB) > 3:
            MKBF = MKB[:5] if len(MKB) > 5 else MKB
            cond = [tableMKB['DiagID'].like(MKBF),
                    tableMKBExSC['position'].eq(position),
                    tableMKBExSCItem['code'].eq(val)]
            record = db.getRecordEx(queryTable, [tableMKBExSCItem['name']], cond)
        if not record:
            MKBF = MKB[:3]
            cond = [tableMKB['DiagID'].like(MKBF),
                    tableMKBExSC['position'].eq(position),
                    tableMKBExSCItem['code'].eq(val)]
            record = db.getRecordEx(queryTable, [tableMKBExSCItem['name']], cond)
        if record:
            result = forceStringEx(record.value('name'))
    return result

def getOrgStructureIdList(treeIndex):
    if treeIndex:
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []
    else:
        return []


def savePatientDocuments(model, rootDirectory):
    items = model.selectedItems()
    interface = model.model().interface
    nameDoc = {u'Client': u'Пациент',
               u'Event': u'Обращение',
               u'Action': u'Мероприятие',
               u'ProphylaxisPlanning': u'Контрольная карта ДН', }
    for item in items:
        if not item.isLost:
            docName = nameDoc[forceString(item._record.value('objectTableName'))]
            docDir = os.path.join(rootDirectory, docName)
            if not os.path.exists(docDir):
                os.makedirs(docDir)
            docPath = unicode(os.path.join(docDir, item.newName))
            if not os.path.isfile(docPath):
                url = interface.getUrl(item)
                result = requests.get(url)
                with open(docPath, "wb") as code:
                    code.write(result.content)
    QtGui.QMessageBox.information(None,
                                  u'Внимание',
                                  u'Выбранные файлы успешно сохранены в каталог \n%s' % rootDirectory,
                                  QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)


def getPersonIdList(personId):
    tablePerson = QtGui.qApp.db.table('Person')
    SNILS = forceString(QtGui.qApp.db.translate('Person', 'id', personId, 'SNILS'))
    currentLastName = forceString(QtGui.qApp.db.translate('Person', 'id', personId, 'lastName'))
    return QtGui.qApp.db.getRecordList(tablePerson,
                                       cols=[tablePerson['id'], tablePerson['code'],
                                             tablePerson['lastName'],
                                             tablePerson['firstName'],
                                             tablePerson['patrName']],
                                       where=[#tablePerson['id'].ne(personId),
                                              tablePerson['SNILS'].eq(unformatSNILS(SNILS)),
                                              tablePerson['deleted'].eq(0),
                                              tablePerson['lastName'].eq(currentLastName)])


class CReadOnlyFilter(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)

    def eventFilter(self, obj, event):
        if isinstance(obj, QtGui.QLineEdit):
            t = event.type()
            if t in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease,
                     QEvent.MouseButtonDblClick, QEvent.MouseMove, QEvent.Wheel):
                return False

            if t in (QEvent.KeyPress, QEvent.KeyRelease):
                key = event.key()
                mods = event.modifiers()
                navigation_keys = {
                    Qt.Key_Left, Qt.Key_Right, Qt.Key_Home, Qt.Key_End,
                    Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown
                }
                if key in navigation_keys:
                    return False
                if (mods & Qt.ControlModifier) and (key in (Qt.Key_C, Qt.Key_A)):
                    return False
                return True
            return False

        if event.type() in (QEvent.KeyPress, 
                            QEvent.KeyRelease,
                            QEvent.MouseButtonPress, 
                            QEvent.MouseButtonRelease,
                            QEvent.MouseButtonDblClick, 
                            QEvent.MouseMove,
                            QEvent.Wheel, 
                            QEvent.ContextMenu,
                            QEvent.DragEnter, 
                            QEvent.Drop):
            return True
        return False


class ActionTypeServiceMixin:
    def __init__(self, *args, **kwargs):
        self.actionTypeActualCache = {}

    def checkActionTypeService(self, actionTypeId, code, serviceId):
        if actionTypeId in self.actionTypeActualCache:
            return self.actionTypeActualCache[actionTypeId]

        db = QtGui.qApp.db
        tableATS = db.table('ActionType_Service')
        tableService = db.table('rbService')
        table = tableATS.leftJoin(tableService, tableATS['service_id'].eq(tableService['id']))

        records = db.getRecordList(table,
                                   [tableService['endDate']],
                                   where=tableATS['master_id'].eq(actionTypeId))

        isActual = True

        if not records and code and serviceId:
            serviceRecord = db.getRecordEx(tableService, [tableService['code']], tableService['id'].eq(serviceId))
            if serviceRecord and forceString(serviceRecord.value('code')) == code:
                isActual = False
        else:
            for record in records:
                endDate = forceDate(record.value('endDate'))
                if endDate and endDate <= QDate.currentDate():
                    isActual = False
                    break

        self.actionTypeActualCache[actionTypeId] = isActual
        return isActual

