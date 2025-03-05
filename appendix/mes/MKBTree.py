#!/usr/bin/env python
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
from PyQt4 import QtGui
from PyQt4.QtCore import QString

from library.ICDCodeEdit import CICDCodeEdit
from library.ICDInDocTableCol import CICDExInDocTableCol
from library.Utils import forceString, forceRef, toVariant
from library.database import CDatabaseException

u"""Столбик и выпадающая таблица с деревом для выбора кода МКБ.
Сведения о кодах МКБ берутся из таблицы s11.MKB
Если такой таблицы нет, используется обычный CICDInDocTableCol"""

MKB_TABLE_NAME = 's11.MKB'
MKB_SUBCLASS_TABLE_NAME = 's11.rbMKBSubclass'
MKB_SUBCLASS_ITEM_TABLE_NAME = 's11.rbMKBSubclass_Item'


def checkMKBTable():
    u"""Проверяет, существуют ли таблицы с кодами МКБ"""
    try:
        db = QtGui.qApp.db
        tableMKB = db.table(MKB_TABLE_NAME)
        tableSubclass = db.table(MKB_SUBCLASS_TABLE_NAME)
        tableSubclassItem = db.table(MKB_SUBCLASS_ITEM_TABLE_NAME)
        return True
    except CDatabaseException:
        return False


def getMKBName(MKB):
    u"""Предполагая, что таблицы с кодами МКБ существуют, получаем имя диагноза по коду"""
    result = '{%s}' % MKB
    mainCode = MKB[:5]
    if mainCode:
        subclass = MKB[5:]
        db = QtGui.qApp.db
        table = db.table(MKB_TABLE_NAME)
        record = db.getRecordEx(table, 'DiagName, MKBSubclass_id', table['DiagID'].eq(mainCode))
        if record:
            result = forceString(record.value(0))
            if subclass:
                subclassId = forceRef(record.value(1))
                tableSubclass = db.table(MKB_SUBCLASS_ITEM_TABLE_NAME)
                cond = [tableSubclass['master_id'].eq(subclassId), tableSubclass['code'].eq(subclass)]
                recordSubclass = db.getRecordEx(tableSubclass, 'name', cond)
                if recordSubclass:
                    result = result + ' / ' + forceString(recordSubclass.value(0))
                else:
                    result = result + ' {%s}'%subclass
    else:
        result = '{%s}' % MKB
    return result


class CMKBInDocTableCol(CICDExInDocTableCol):
    def __init__(self, name, table, len, hasname=True):
        CICDExInDocTableCol.__init__(self, name, table, len)
        self.hasname = hasname and checkMKBTable()

    def toString(self, val, record):
        if val.toString():
            return toVariant(val.toString() + QString(" - %s"%getMKBName(val.toString()) if self.hasname else ""))
        else:
            return ''


    def createEditor(self, parent):
#        if checkMKBTable():
#            return CICDCodeEditEx(parent)
#        else:
        return CICDCodeEdit(parent)


    def toStatusTip(self, val, record):
        code = forceString(val)
        if self.cache.has_key(code):
            descr = self.cache[code]
        else:
            descr = getMKBName(code) if (code and checkMKBTable()) else ''
            self.cache[code] = descr
        return toVariant((code+': '+descr) if code else '')

