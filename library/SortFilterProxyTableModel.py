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


from PyQt4 import QtGui
from PyQt4.QtCore import QString, QModelIndex

from library.Utils import forceString, forceRef

u'''
Пример использования:

model.setTable('Event')
sortModel.setFilter('srcNumber', 'abc', MatchContains, isCaseSensitive=True)
sortModel.setFilter('execDate',  QDate.currentDate(), MatchGreaterEqual)
'''


class CSortFilterProxyTableModel(QtGui.QSortFilterProxyModel):
    MatchExactly = 0
    MatchContains = 1
    MatchStartsWith = 2  # только для строковых значений
    MatchEndsWith = 3    # только для строковых значений
    MatchGreater = 4
    MatchLess = 5
    MatchGreaterEqual = 6
    MatchLessEqual = 7
    MatchBetween = 8
    MatchInList = 9

    def __init__(self, parent, sourceModel):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        self.__filters = {}
        self.setSourceModel(sourceModel)

    def model(self):
        return self.sourceModel()

    def __invalidateFilter(self):
        self.invalidate()

    def setFilter(self, recordFieldName, value, matchMethod=MatchExactly, isCaseSensitive=False):
        self.__filters[recordFieldName] = (value, matchMethod, isCaseSensitive)
        self.__invalidateFilter()

    def removeFilter(self, recordFieldName):
        if recordFieldName in self.__filters:
            del self.__filters[recordFieldName]
            self.__invalidateFilter()

    def clearFilters(self):
        self.__filters = {}
        self.__invalidateFilter()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        if not self.__filters:
            return True

        def isMatch(value1, value2, isCaseSensitive, cmp=lambda a,b: True):
            if type(value1) == QString and not isCaseSensitive:
                return cmp(forceString(value1).upper(), forceString(value2).upper())
            return cmp(value1, value2)

        sourceModel = self.sourceModel()
        record = sourceModel.getRecordByRow(sourceRow)
        result = True
        for recordFieldName, (value, matchMethod, isCaseSensitive) in self.__filters.items():
            if not result or not record:
                break

            recordValue = record.value(recordFieldName).toPyObject()
            if matchMethod == self.MatchExactly:
                result = result and isMatch(recordValue, value, isCaseSensitive, lambda a,b: a == b)
            elif matchMethod == self.MatchStartsWith:
                result = result and isMatch(recordValue, value, isCaseSensitive, lambda a,b: a.startswith(b))
            elif matchMethod == self.MatchEndsWith:
                result = result and isMatch(recordValue, value, isCaseSensitive, lambda a,b: a.endswith(b))
            elif matchMethod == self.MatchContains:
                result = result and isMatch(recordValue, value, isCaseSensitive, lambda a,b: b in a)
            elif matchMethod == self.MatchGreater:
                result = result and isMatch(recordValue, value, isCaseSensitive, lambda a,b: a > b)
            elif matchMethod == self.MatchLess:
                result = result and isMatch(recordValue, value, isCaseSensitive, lambda a,b: a < b)
            elif matchMethod == self.MatchGreaterEqual:
                result = result and isMatch(recordValue, value, isCaseSensitive, lambda a,b: a >= b)
            elif matchMethod == self.MatchLessEqual:
                result = result and isMatch(recordValue, value, isCaseSensitive, lambda a,b: a <= b)
            elif matchMethod == self.MatchBetween:
                result = result and isMatch(recordValue, value, isCaseSensitive, lambda a,(b,c): b <= a <= c)
            elif matchMethod == self.MatchInList:
                result = result and isMatch(recordValue, value, isCaseSensitive, lambda a,b: a in b)

        return result


    def getRecordByRow(self, row):
        index = self.index(row, 0)
        if index.isValid():
            sourceRow = self.mapToSource(index).row()
            return self.sourceModel().getRecordByRow(sourceRow)
        return None


    def __getItemId(self, row):
        index = self.index(row, 0)
        sourceRow = self.mapToSource(index).row()
        return forceRef(self.sourceModel().getRecordByRow(sourceRow).value('id'))


    def removeRow(self, row, parentIndex=QModelIndex(), *args, **kwargs):
        index = self.index(row, 0)
        return self.sourceModel().removeRow(self.mapToSource(index).row())
