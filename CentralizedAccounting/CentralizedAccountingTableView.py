# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
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

#from library.Utils import
from library.TableView import CTableView

__all__ = ( 'CCentralizedAccountingTableView',
          )


class CCentralizedAccountingTableView(CTableView):
    def __init__(self, parent):
        CTableView.__init__(self, parent)
        self.eventEditor = None
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter):
            event.ignore()
        elif event.modifiers() == Qt.ControlModifier and key == Qt.Key_A:
            if self.eventEditor:
                self.eventEditor.loadActions(None)
            QtGui.QTableView.keyPressEvent(self, event)
        elif key in (Qt.Key_Tab, Qt.Key_Backtab) and event.modifiers() & Qt.ControlModifier:
            event.ignore()
        elif event.matches(QtGui.QKeySequence.Copy):
            event.accept()
            self.copy()
        else:
            QtGui.QTableView.keyPressEvent(self, event)

