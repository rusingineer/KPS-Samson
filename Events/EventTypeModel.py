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
from PyQt4.QtCore import Qt
from library.database   import CTableRecordCache
from library.TableModel import CTableModel, CBoolCol, CEnumCol, CNumCol, CRefBookCol, CTextCol

class CEventTypeTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self._specialValues = []
        self.addColumn(CTextCol(u'Код', ['code'], 5))
        self.addColumn(CTextCol(   u'Наименование',     ['name'], 40))
        self.addColumn(CTextCol(   u'Код ЕГИСЗ',        ['usishCode'], 40))
        self.addColumn(CTextCol(   u'Региональный код', ['regionalCode'], 10))
        self.addColumn(CRefBookCol(u'Назначение',       ['purpose_id'], 'rbEventTypePurpose', 10))
        self.addColumn(CRefBookCol(u'Профиль',          ['eventProfile_id'], 'rbEventProfile', 10))
        self.addColumn(CRefBookCol(u'Вид помощи',       ['medicalAidKind_id'], 'rbMedicalAidKind', 10))
        self.addColumn(CRefBookCol(u'Тип помощи',       ['medicalAidType_id'], 'rbMedicalAidType', 10))
        self.addColumn(CEnumCol(   u'Пол',              ['sex'], ['', u'М', u'Ж'], 10))
        self.addColumn(CTextCol(   u'Возраст',          ['age'], 10))
        self.addColumn(CNumCol(    u'Период',           ['period'], 10))
        self.addColumn(CEnumCol(   u'Раз в',            ['singleInPeriod'], ('', u'неделю', u'месяц', u'квартал', u'полугодие', u'год', u'раз в два года', u'раз в три года'), 10))
        self.addColumn(CBoolCol(   u'Продолжительное',  ['isLong'], 10))
        self.addColumn(CNumCol(    u'Мин.длительность', ['minDuration'], 10))
        self.addColumn(CNumCol(    u'Макс.длительность',['maxDuration'], 10))
        self.addColumn(CRefBookCol(u'Сервис ОМС',       ['service_id'], 'rbService', 10))
        self._fieldNames = ['EventType.id', 'EventType.code', 'EventType.name', 'EventType.usishCode',
        'EventType.regionalCode', 'EventType.purpose_id', 'EventType.eventProfile_id',
        'EventType.medicalAidKind_id', 'EventType.medicalAidType_id', 'EventType.sex',
        'EventType.age', 'EventType.period', 'EventType.singleInPeriod',
        'EventType.isLong', 'EventType.minDuration', 'EventType.maxDuration',
        'EventType.service_id'
        ]
        self.setTable('EventType')

    
    def sort(self, col, sortOrder=Qt.AscendingOrder):
        if self._idList:
            db = QtGui.qApp.db
            table = db.table('EventType')
            cond = [table['id'].inlist(self._idList)]
            colClass = self.cols()[col]
            colName = colClass.fields()[0]
            if col in [4,5,6,7]:
                tableSort = db.table(colClass.tableName).alias('fieldSort')
                table = table.leftJoin(tableSort, tableSort['id'].eq(table[colName]))
                colName = 'fieldSort.name'
            order = '{} {}'.format(colName, u'DESC' if sortOrder else u'ASC')
            self._idList = db.getIdList(table, table['id'].name() , where = cond, order=order)
            self.reset()
    

    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        tableEventType = db.table('EventType')
        loadFields = []
        loadFields.append(u'DISTINCT '+ u', '.join(self._fieldNames))
        self._table = tableEventType
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, fakeValues=self._specialValues)



class CEventTypePurposeTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Код',              ['code'], 5))
        self.addColumn(CTextCol(u'Наименование',     ['name'], 45))
        self.addColumn(CTextCol(u'Федеральный код',  ['federalCode'], 10))
        self.addColumn(CTextCol(u'Код ЕГИСЗ',        ['usishCode'],   10))
        self.addColumn(CTextCol(u'Региональный код', ['regionalCode'], 10))
        self.addColumn(CEnumCol(u'Цель',             ['purpose'], (u'Не задано', u'Лечение', u'Профилактика', u'Диагностика',
                                                                   u'Социальная', u'Реабилитация', u'Диспансерное наблюдение', u'СМП'), 20))
        self.setTable('rbEventTypePurpose')


    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

