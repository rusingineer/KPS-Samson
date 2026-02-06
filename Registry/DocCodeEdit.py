# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012 SAMSON Group. All rights reserved.
## Copyright (C) 2015 Oskin A.
## Copyright (C) 2016 Oskin A. and Arkhipov S.
## Copyright (C) 2021 Arkhipov S.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtCore, QtGui

from library.Completer import CompletingComboBox
from library.Utils import forceString


class CDocCodeEdit(CompletingComboBox):
    _COMPLITELY_LOADED = 1

    def __init__(self, parent=None):
        super(CDocCodeEdit, self).__init__(parent=parent)
        self._tableName = 'rbFmsUnit'
        self._loadedVals = None
        self.lineEdit().selectAll()
        self.lineEdit().setFocus()

    # def onCompleterHighlighted(self, text):
    #     self.emit(QtCore.SIGNAL('textEdited(QString)'), text)

    def setTable(self):
        if self._loadedVals == CDocCodeEdit._COMPLITELY_LOADED:
            return
        code = self.lineEdit().text()
        if len(code) and code[0] == self._loadedVals:
            return

        self.filter.beginResetModel()
        self.clear()
        result = ['']
        try:
            table = QtGui.qApp.db.table(self._tableName)
            cond = [
                table['code'].ne(''),
                # table['name'].ne(''),
            ]
            if code:
                cond.append(table['code'].like('%s%%' % code[0]))
            query = QtGui.qApp.db.query(
                QtGui.qApp.db.selectStmt(table, u'CONCAT_WS(\'| \',`code`, `name`)', where=cond, order='code'))
            while query.next():
                result.append(forceString(query.value(0)))
            self._loadedVals = CDocCodeEdit._COMPLITELY_LOADED if not code else code[0]
        except:
            QtGui.qApp.logCurrentException()
        finally:
            self.addItems(result)
            self.filter.endResetModel()
            self.setEditText(code)
            self.filter.setFilterFixedString(code)

    def setText(self, text):
        self.lineEdit().setText(text)

    def showPopup(self):
        self.setTable()
        self.completer.complete()
