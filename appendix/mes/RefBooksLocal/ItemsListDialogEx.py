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
from PyQt4.QtCore import Qt

from library.ItemsListDialog import CItemEditorBaseDialog
from library.Utils import forceRef


class CItemEditorDialogEx(CItemEditorBaseDialog):
    u"""Диалог с контролем уникальности кода.
    Должен быть компонент edtCode"""
    def __init__(self, parent, tableName, uniqueCode = False):
        CItemEditorBaseDialog.__init__(self, parent, tableName)
        if 'uniqueCode' in dir(parent):
            self.uniqueCode = parent.uniqueCode
        else:
            self.uniqueCode = uniqueCode
            
    def showEvent(self, event):
        self.edtCode.setFocus(Qt.OtherFocusReason)
            
    def isNew(self):
        return not self.itemId()
        
    def checkDataEntered(self):
        u"""Проверка записи на корректность"""
        if not CItemEditorBaseDialog.checkDataEntered(self):
            return False
        code = self.edtCode.text()
        if self.uniqueCode:
            query = QtGui.qApp.db.query("""
                SELECT id
                from %s
                where code = '%s'
                and deleted = 0"""%(self.tableName(), code))
            if query.size() > 0: # такой код есть, проверяем на уникальность
                if self.isNew():
                    return self.checkValueMessage(u"Код не уникален!", True, self.edtCode)
                else:
                    query.first()
                    if forceRef(query.record().value("id")) != self.itemId():
                        return self.checkValueMessage(u"Код не уникален!", True, self.edtCode)
        return True