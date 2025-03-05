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
import json

from PyQt4 import QtGui
from PyQt4.QtCore import QVariant

from library.TableView import CTableView
from library.Utils import forceInt, getPref, setPref, forceString


class CStockBatchView(CTableView):
    def __init__(self, parent):
        CTableView.__init__(self, parent)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)


    def loadPreferences(self, preferences):
        model = self.model()
        horizontalHeader = self.horizontalHeader()
        headerCount = horizontalHeader.count()
        charWidth = self.fontMetrics().width('A0')/2
        for col in range(0, headerCount):
            title = model.headers[col]
            width = forceInt(getPref(preferences, unicode('width '+title.lower()), len(title)*charWidth))
            if width:
                self.setColumnWidth(col, width)
        self.horizontalHeader().setStretchLastSection(True)
        state = getPref(preferences, 'headerState', QVariant()).toByteArray()
        if state:
            header = self.horizontalHeader()
            try:
                state = json.loads(forceString(state))
            except:
                header.restoreState(state)
                return
            maxVIndex = 0
            for col in range(0, headerCount):
                title = model.headers[col]
                name = title.lower()
                curVIndex = header.visualIndex(col)
                if name in state:
                    vIndex = state[name][0]
                    isHidden = state[name][1]
                    if vIndex > maxVIndex:
                        maxVIndex = vIndex
                    if vIndex != curVIndex:
                        header.moveSection(curVIndex, vIndex)
                    if isHidden:
                        header.setSectionHidden(col, True)
                else:
                    header.moveSection(curVIndex, headerCount-1)


    def savePreferences(self):
        preferences = {}
        model = self.model()
        horizontalHeader = self.horizontalHeader()
        headerCount = horizontalHeader.count()
        for col in range(0, headerCount):
            width = self.columnWidth(col)
            title = model.headers[col]
            setPref(preferences, unicode('width '+title.lower()), QVariant(width))
        header = self.horizontalHeader()
        if header.isMovable() or self.headerColsHidingAvailable():
            params = {}
            needSave = False
            for col in range(0, headerCount):
                if col != header.visualIndex(col)  or header.isSectionHidden(col):
                    needSave = True
                    break
            if needSave:
                for col in range(0, headerCount):
                    title = model.headers[col]
                    name = title.lower()
                    params[name] = (header.visualIndex(col), header.isSectionHidden(col))
            setPref(preferences, 'headerState', QVariant(json.dumps(params)))
        return preferences

