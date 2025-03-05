# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
from library.interchange     import getLineEditValue, setLineEditValue
from library.ItemEditorDialogWithIdentification import CItemEditorDialogWithIdentification
from library.ItemsListDialog import CItemsListDialog
from library.TableModel      import CTextCol

from RefBooks.Tables import rbCode, rbDiagnosisType, rbName
from .Ui_RBDiagnosisTypeEditor import Ui_ItemEditorDialog

class CRBDiagnosisTypeList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',          [rbCode], 20),
            CTextCol(u'Наименование', [rbName], 30),
            CTextCol(u'В диагнозе заменять на', ['replaceInDiagnosis'], 20),
            ], rbDiagnosisType, [rbCode, rbName])
        self.setWindowTitleEx(u'Типы диагнозов')

    def getItemEditor(self):
        return CRBDiagnosisTypeEditor(self)

#
# ##########################################################################
#

class CRBDiagnosisTypeEditor(Ui_ItemEditorDialog, CItemEditorDialogWithIdentification):
    def __init__(self,  parent):
        CItemEditorDialogWithIdentification.__init__(self, parent, rbDiagnosisType)
        self.setWindowTitleEx(u'Тип диагноза')
        self.setupDirtyCather()


    def setRecord(self, record):
        CItemEditorDialogWithIdentification.setRecord(self, record)
        setLineEditValue(   self.edtCode,          record, 'code')
        setLineEditValue(   self.edtName,          record, 'name')
        setLineEditValue(   self.edtReplaceCode,   record, 'replaceInDiagnosis')


    def getRecord(self):
        record = CItemEditorDialogWithIdentification.getRecord(self)
        getLineEditValue(   self.edtCode,          record, 'code')
        getLineEditValue(   self.edtName,          record, 'name')
        getLineEditValue(   self.edtReplaceCode,   record, 'replaceInDiagnosis')
        return record
