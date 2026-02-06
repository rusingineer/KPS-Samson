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
from PyQt4.QtCore import Qt, QAbstractListModel, QVariant

from Registry.NamesEditor import CNameCompleterModel

__all__ = [ 'CStaticCompleterModel',
            'CCompleter',
            'CNameCompleter',
          ]

#class CCompleterModel(QAbstractListModel):
#    def __init__(self, parent, tableName):
#        QAbstractListModel.__init__(self, parent)


class CStaticCompleterModel(QAbstractListModel):
    def __init__(self, parent, strings):
        QAbstractListModel.__init__(self, parent)
        self.__strings = [QVariant(s) for s in strings]


    def rowCount(self, parentIndex = None):
        return len(self.__strings)


    def data(self, index, role=Qt.DisplayRole):
        return self.__strings[index.row()]



class CCompleter(QtGui.QCompleter):
    def __init__(self, parent, model):
        QtGui.QCompleter.__init__(self, parent)
        self.setCompletionMode(QtGui.QCompleter.InlineCompletion)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setModelSorting(QtGui.QCompleter.CaseInsensitivelySortedModel)
        self.setModel(model)




class CNameCompleter(QtGui.QCompleter):
    def __init__(self, parent, model):
        self.setCompletionMode(QtGui.QCompleter.InlineCompletion)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setModelSorting(QtGui.QCompleter.CaseInsensitivelySortedModel)
        self.setModel(model)


class CFirstNameCompleter(CNameCompleter):
    model = None

    def __init__(self, parent):
        if not CFirstNameCompleter.model:
            CFirstNameCompleter.model = CNameCompleterModel(self, 'rdFirstName')
        CFirstNameCompleter.__init__(self, parent, CFirstNameCompleter.model)


class CompletingComboBox(QtGui.QComboBox):
    """An editable combo box that filters and autocompletes."""
    def __init__(self, parent=None):
        super(CompletingComboBox, self).__init__(parent)
        self.setEditable(True)
        self.filter = QtGui.QSortFilterProxyModel(self)
        self.filter.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.filter.setSourceModel(self.model())
        self.completer = QtGui.QCompleter(self.filter, self)
        self.completer.setCompletionMode(QtGui.QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(self.completer)
        self.lineEdit().textEdited[unicode].connect(self.filter.setFilterFixedString)
        self.currentIndexChanged.connect(self._index_changed)
        self.editTextChanged.connect(self._text_changed)
        self.setAutoCompletion(True)

    def _index_changed(self, index):
        self.lineEdit().selectAll()

    def _text_changed(self, index):
        self.lineEdit().text()
