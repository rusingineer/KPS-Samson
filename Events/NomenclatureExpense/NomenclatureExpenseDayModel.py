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

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QDate

from library.Utils import forceTime, forceDouble, toVariant

from Events.ExecutionPlan.ExecutionPlanType import executionPlanType


class CItem(object):
    def __init__(self, item):
        self._item = item

    @property
    def item(self):
        return self._item

    @property
    def idx(self):
        return self._item.idx

    def setIdx(self, idx):
        self._item.idx = idx

    @property
    def time(self):
        return self._item.time

    @property
    def dosage(self):
        return self._item.nomenclature.dosage

    @property
    def action(self):
        return self._item.action

    def setIsDirty(self, dirty=True):
        self._item.setIsDirty(dirty)

    def setNomenclatureId(self, nomenclatureId):
        self._item.nomenclature.nomenclatureId = nomenclatureId

    def setTime(self, time):
        self._item.time = time

    def setDate(self, date):
        self._item.date = date

    def setDoses(self, dosage):
        self._item.nomenclature.dosage = dosage

    @property
    def editable(self):
        return not self._item.executedDatetime

    @classmethod
    def create(cls, ep):
        ept = executionPlanType(ep)
        return cls(ept.addNewDateTimeItem())


TIME_INDEX = 0
DOSES_INDEX = 1


class CNomenclatureExpenseDayModel(QtCore.QAbstractTableModel):
    def __init__(self, parent, dosageUnitName='', ignoreTime=False):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._items = []
        self._executionPlan = None
        self._canAddItems = False
        self._date = None
        self._zeroTime = QtCore.QTime(0, 0)
        self._dosageUnitName = dosageUnitName
        self._ignoreTime = ignoreTime
        self._templateItem = None
        self.isApplyChangesCourseNextDays = False
        self._readOnly = False


    def setReadOnly(self, value=False):
        self._readOnly = value


    def isReadOnly(self):
        return self._readOnly


    def setApplyChangesCourseNextDays(self, value):
        self.isApplyChangesCourseNextDays = value


    def getApplyChangesCourseNextDays(self):
        return self.isApplyChangesCourseNextDays


    def load(self, items, readOnly=False):
        if not self._readOnly:
            self._readOnly = readOnly
        self._templateItem = items[0]
        self._executionPlan = self._templateItem.executionPlan
        self._date = self._templateItem.date
        self._items = [CItem(i) for i in items]
        if self._items and self._date >= QDate.currentDate() and not self._readOnly:
            self._canAddItems = True
        self.reset()


    def removeRows(self, row, count, parentIndex = QtCore.QModelIndex()):
        if 0<=row and row+count<=len(self._items):
            for item in self._items[row:row+count]:
                if not item.editable or self._readOnly or item.action:
                    return False
            self.beginRemoveRows(parentIndex, row, row+count-1)
            del self._items[row:row+count]
            self.endRemoveRows()
            for item in self._items:
                item.setIsDirty(True)
            return True
        else:
            return False


    def rowCount(self, index=None):
        return len(self._items) + 1 if self._canAddItems else len(self._items)


    def columnCount(self, index=None):
        return 2


    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole or orientation == QtCore.Qt.Vertical:
            return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)
        return u'Время' if section == TIME_INDEX else u'Дозировка'


    def flags(self, index):
        row = index.row()
        result = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

        if self._readOnly:
            return result

        if row == len(self._items):
            if self._canAddItems:
                result |= QtCore.Qt.ItemIsEditable
        else:
            item = self._items[row]
            if item.editable and not self._readOnly:
                result |= QtCore.Qt.ItemIsEditable
        return result


    def data(self, index, role=QtCore.Qt.DisplayRole):
        row = index.row()
        if not (0 <= row < len(self._items)):
            return QtCore.QVariant()
        if role != QtCore.Qt.DisplayRole and role != QtCore.Qt.BackgroundColorRole:
            return QtCore.QVariant()

        if role == QtCore.Qt.BackgroundColorRole:
            if not self._items[row].editable:
                if self._items[row].item.executedDatetime.time()>=self._items[row].time and not self._ignoreTime:
                    return QtCore.QVariant(QtGui.QColor(QtCore.Qt.red))
                else:
                    return QtCore.QVariant(QtGui.QColor(QtCore.Qt.green))

        column = index.column()
        if column == TIME_INDEX:
            time = self._items[row].time
            if not time.isValid():
                return QtCore.QVariant(self._zeroTime)
            return toVariant(self._items[row].time)
        elif column == DOSES_INDEX:
            if self._dosageUnitName:
                value = '%s %s' % (str(self._items[row].dosage), self._dosageUnitName)
            else:
                value = str(self._items[row].dosage)
            return toVariant(value)
        return QtCore.QVariant()


    def createEditor(self, index, parent):
        column = index.column()
        if column == TIME_INDEX:
            return QtGui.QTimeEdit(parent)
        elif column == DOSES_INDEX:
            editor = QtGui.QDoubleSpinBox(parent)
            editor.setMaximum(100000)
            editor.setMinimum(0)
            editor.setDecimals(2)
            return editor
        return None


    def setEditorData(self, index, editor):
        row = index.row()
        item = self._items[row] if 0 <= row < len(self._items) else None
        column = index.column()
        if column == TIME_INDEX:
            editor.setTime(item.time if item else QtCore.QTime())
        elif column == DOSES_INDEX:
            editor.setValue(item.dosage if item else 0)


    def getEditorData(self, index, editor):
        column = index.column()
        if column == TIME_INDEX:
            return editor.time()
        elif column == DOSES_INDEX:
            return editor.value()
        else:
            return


    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role != QtCore.Qt.EditRole and role != QtCore.Qt.BackgroundColorRole:
            return False

        row = index.row()
        column = index.column()

        if row == len(self._items):
            if not getattr(self, '_canAddLastRow', True):
                return False
            self.beginInsertRows(QtCore.QModelIndex(), row, row)
            if self._items:
                dosage = self._items[-1].dosage
                idx = self._items[-1].idx + 1
            else:
                dosage = 0
                idx = 0

            item = CItem.create(self._executionPlan)
            item.setDate(self._date)
            item.setIdx(idx)
            item.setNomenclatureId(self._templateItem.nomenclature.nomenclatureId)
            self._items.append(item)
            if column == TIME_INDEX:
                item.setDoses(dosage)
            self.endInsertRows()

        item = self._items[row]
        if role == QtCore.Qt.BackgroundColorRole:
            if not item.editable:
                if item.executedDatetime.time()>=item.time and self._ignoreTime:
                    return QtCore.QVariant(QtGui.QColor(QtCore.Qt.red))
                else:
                    return QtCore.QVariant(QtGui.QColor(QtCore.Qt.green))
        if column == TIME_INDEX:
            item.setTime(forceTime(value))
        elif column == DOSES_INDEX:
            item.setDoses(forceDouble(value))
        else:
            return False

        self.emitAllChanged()

        return True


    def items(self):
        return self._items


    def emitAllChanged(self):
        index1 = self.index(0, 0)
        index2 = self.index(self.rowCount(), self.columnCount())
        self.emit(QtCore.SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)
