#!/usr/bin/env python
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
from PyQt4.QtCore import Qt, pyqtSignature

from library.DialogBase import CDialogBase
from library.TableModel import CTableModel, CTextCol

from Events.Ui_ActionTypeDialog import Ui_ActionTypeDialog


class CActionTypeDialog(CDialogBase, Ui_ActionTypeDialog):

    def __init__(self, parent, cols, tableName, order, forSelect=False, filterClass=None, idList=[], skipable=True):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.skipable = skipable
        if not skipable:
            self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.filterClass = filterClass
        self.props = {}
        self.order = order
        self.model = CTableModel(self, cols, tableName)
        self.model.setIdList(idList)
        self.tblActionType.setModel(self.model)
        if idList:
            self.tblActionType.selectRow(0)


    def selectItem(self):
        return self.exec_()


    def setCurrentItemId(self, itemId):
        self.tblActionType.setCurrentItemId(itemId)


    def currentItemId(self):
        return self.tblActionType.currentItemId()


    @pyqtSignature('QModelIndex')
    def on_tblListWidget_doubleClicked(self, index):
        pass

    def closeEvent(self, event):
        if not self.skipable:
            # Игнорируем попытку закрытия
            event.ignore()
        else:
            super(CActionTypeDialog, self).closeEvent(event)

    def reject(self):
        if self.skipable:
            super(CActionTypeDialog, self).reject()


class CActionTypeDialogTableModel(CActionTypeDialog):
    def __init__(self, parent, idList, skipable=True):
        CActionTypeDialog.__init__(self, parent, [
            CTextCol(u'Код', ['code'],  20),
            CTextCol(u'Наименование действия', ['name'], 40),
            CTextCol(u'"Плоский" код', ['flatCode'], 10)
            ], 'ActionType', ['id'], False, None, idList, skipable)
