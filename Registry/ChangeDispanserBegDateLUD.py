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

from library.interchange     import getDateEditValue, setDateEditValue
from library.ItemsListDialog import CItemEditorBaseDialog
from library.Utils           import forceDate, toVariant

from Ui_ChangeDispanserBegDateLUD import Ui_ChangeDispanserBegDateLUD


class CChangeDispanserBegDateLUD(CItemEditorBaseDialog, Ui_ChangeDispanserBegDateLUD):
    def __init__(self, parent):
        CItemEditorBaseDialog.__init__(self, parent, 'Diagnosis')
        self.setupUi(self)
        self.setWindowTitleEx(u'Изменить дату постановки на учет')
        self.setupDirtyCather()


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setDateEditValue(self.edtBegDate, record, 'dispanserBegDate')
        self.setIsDirty(False)


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getDateEditValue(self.edtBegDate, record, 'dispanserBegDate')
        return record


    def checkDataEntered(self):
        result = True
        begDate = forceDate(self.edtBegDate.date())
        result = result and (begDate or self.checkInputMessage(u'дату постановки на диспансерный учет', True, self.edtBegDate))
        return result
    
    
    def save(self):
        if self.getRecord() and self._id:
            return CItemEditorBaseDialog.save(self)
        return True
    
    
    def getDate(self):
        return toVariant(self.edtBegDate.date())