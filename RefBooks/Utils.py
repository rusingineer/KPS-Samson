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
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate

from library.InDocTable import CInDocTableView
from library.TableModel import CCol
from library.Utils import forceString, forceDate, toVariant


#WFT?
class CInDocTableViewTabMod(CInDocTableView):
    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)
        self.tabLeft = None
        self.tabRight = None


    def setTabLeftBorder(self, tab):
        self.tabLeft = tab


    def setTabRightBorder(self, tab):
        self.tabRight = tab


    def keyPressEvent(self, event):
        #self.tblItems.keyPressEventOrig(event)
        super(CInDocTableViewTabMod, self).keyPressEvent(event)
        if event.key() == Qt.Key_Tab:
            index = self.currentIndex()
            if self.tabLeft and index.column() < self.tabLeft:
                self.setCurrentIndex(self.model().index(index.row(), self.tabLeft))
            if self.tabRight and index.column() > self.tabRight:
                tab = self.tabLeft if self.tabLeft is not None else 0
                self.setCurrentIndex(self.model().index(index.row()+1, tab))


class CMKBOtoMKBXColumn(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        db = QtGui.qApp.db
        table = db.table('soc_M002')
        self.mapping = {}
        records = db.getRecordList(table)
        for record in records:
            mkbO = forceString(record.value('mkbO'))
            listMKBX = self.mapping.setdefault(mkbO, [])
            listMKBX.append(forceString(record.value('mkb10')))


    def format(self, values):
        mkbO = forceString(values[0])
        begDate = forceDate(values[1])
        if begDate < QDate(2025, 7, 1):
            return CCol.invalid
        listMKBX = self.mapping.get(mkbO)
        if listMKBX:
            return toVariant(';'.join(listMKBX))
        else:
            return CCol.invalid
