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


from library.interchange     import getLineEditValue, setLineEditValue
from library.ItemsListDialog import CItemEditorBaseDialog, CItemsListDialog
from library.TableModel      import CTextCol

from RefBooks.Tables         import rbCode, rbName

from .Ui_RBMedicalExemptionReasonItemList import Ui_RBMedicalExemptionReasonItemList
from .Ui_RBMedicalExemptionReasonEditor   import Ui_RBMedicalExemptionReasonEditor


class CRBMedicalExemptionReasonList(Ui_RBMedicalExemptionReasonItemList, CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',          [rbCode], 20),
            CTextCol(u'Наименование', [rbName], 40),
            ], 'rbMedicalExemptionReason', [rbCode, rbName])

        self.tblItems.addPopupDelRow()
        self.setWindowTitleEx(u'Причины медотводов')


    def getItemEditor(self):
        return CRBMedicalExemptionReasonEditor(self)


#
# ##########################################################################
#

class CRBMedicalExemptionReasonEditor(CItemEditorBaseDialog, Ui_RBMedicalExemptionReasonEditor):
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'rbMedicalExemptionReason')
        self.setupUi(self)
        self.setWindowTitleEx(u'Причина медотвода')
        self.setupDirtyCather()


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(self.edtCode,                record, 'code' )
        setLineEditValue(self.edtName,                record, 'name' )


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(self.edtCode,                record, 'code' )
        getLineEditValue(self.edtName,                record, 'name' )
        return record