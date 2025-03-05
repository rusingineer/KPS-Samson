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

from library.ItemsListDialog    import CItemsListDialog, CItemEditorDialog
from library.TableModel         import CTextCol


class CRBObservationSubgroupList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код', ['code'], 20),
            CTextCol(u'Наименование', ['name'], 40),
            ], 'rbObservationSubgroup', ['code', 'name'])
        self.setWindowTitleEx(u'Подгруппы наблюдения')


    def getItemEditor(self):
        editor = CItemEditorDialog(self, 'rbObservationSubgroup')
        editor.setWindowTitleEx(u'Подгруппы наблюдения')
        return editor
