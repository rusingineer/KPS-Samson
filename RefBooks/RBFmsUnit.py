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


from PyQt4.QtCore import *
from library.TableModel import *
from library.ItemsListDialog import CItemsListDialog, CItemEditorDialog

from Tables import *


class CRBFmsUnitList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',          [rbCode], 20),
            CTextCol(u'Наименование', [rbName], 40),
            ], rbFmsUnit, [rbCode, rbName])
        self.setWindowTitleEx(u'Место выдачи документа')

    def getItemEditor(self):
        return CRBFmsUnitEditor(self)


class CRBFmsUnitEditor(CItemEditorDialog):
    def __init__(self,  parent):
        CItemEditorDialog.__init__(self, parent, rbFmsUnit)
        self.setWindowTitleEx(u'Место выдачи документа')
