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
from PyQt4.QtCore import SIGNAL, QDate

from library.DateEdit import CDateEdit, CDateValidator
from library.Utils    import trim


class CF090DateEdit(CDateEdit):
    __pyqtSignals__ = ('dateChanged(const QDate &)',
                       'editingFinished()'
                       )

    def __init__(self, parent=None):
        CDateEdit.__init__(self, parent)
        self.endDateDefaultMax = self.validator.defaultMax
        self.endDateAction = None
        self.connect(self.lineEdit, SIGNAL('editingFinished()'), self.on_editingFinished)


    def setEndDateDefaultMax(self, endDateDefaultMax):
        self.endDateDefaultMax = endDateDefaultMax if (endDateDefaultMax and endDateDefaultMax.isValid()) else self.validator.defaultMax


    def setEndDateAction(self, endDateAction):
        self.endDateAction = endDateAction


    def on_editingFinished(self):
        dateAsText = self.lineEdit.text()
        state, pos = self.validator.validate(dateAsText, 0)
        if state == CDateValidator.Acceptable:
            date = self.date()
            self.setColor(date)
            self.emit(SIGNAL('dateChanged(const QDate &)'), date)
        else:
            date = self.endDateAction if (self.endDateAction and self.endDateAction.isValid()) else QDate()
            self.setDate(date)
            self.emit(SIGNAL('dateChanged(const QDate &)'), date)
        self.oldText = dateAsText


    def focusOutEvent(self, event):
        dateAsText = trim(self.lineEdit.text())
        QtGui.QComboBox.focusOutEvent(self, event)
        if dateAsText:
            state, pos = self.validator.validate(dateAsText, 0)
            if state == CDateValidator.Intermediate:
                date = self.endDateAction if (self.endDateAction and self.endDateAction.isValid()) else QDate()
                self.setDate(date)
                self.emit(SIGNAL('dateChanged(const QDate &)'), date)


    def setMinimumDate(self, min):
        if isinstance(min, QDate) and min.isValid():
            max = self.validator.max
            if max.isValid():
                if max < min:
                    max = min
            else:
                max = self.endDateDefaultMax if (self.endDateDefaultMax and self.endDateDefaultMax.isValid()) else self.validator.defaultMax
            self.setDateRange(min, max)
        elif isinstance(min, QDate) and not min.isValid():
            min = self.validator.defaultMin
            max = self.validator.max
            if not max.isValid():
                max = self.endDateDefaultMax if (self.endDateDefaultMax and self.endDateDefaultMax.isValid()) else self.validator.defaultMax
            self.setDateRange(min, max)


    def setMaximumDate(self, max):
        if isinstance(max, QDate) and max.isValid():
            min = self.validator.min
            if min.isValid():
                if min > max:
                    min = max
            else:
                min = self.validator.defaultMin
            self.setDateRange(min, max)
        elif isinstance(max, QDate) and not max.isValid():
            max = self.endDateDefaultMax if (self.endDateDefaultMax and self.endDateDefaultMax.isValid()) else self.validator.defaultMax
            min = self.validator.min
            if not min.isValid():
                min = self.validator.defaultMin
            self.setDateRange(min, max)


    def setDateRange(self, min, max):
        if isinstance(min, QDate) and isinstance(max, QDate):
            self.validator.min = min
            self.validator.max = max

