# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from library.interchange     import ( getLineEditValue, getRBComboBoxValue,
                                      setLineEditValue, setRBComboBoxValue,
                                    )
from library.ItemEditorDialogWithIdentification import CItemEditorDialogWithIdentification
from library.ItemsListDialog import CItemsListDialog
from library.TableModel      import CRefBookCol, CTextCol
from library.InDocTable      import CInDocTableCol

from RefBooks.Tables         import rbCode, rbName, rbSocStatusType

from .Ui_RBSocStatusTypeItemEditor import Ui_SocStatusTypeItemEditorDialog


class CRBSocStatusTypeList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',          [rbCode], 20),
            CTextCol(u'Наименование', [rbName], 40),
            CTextCol(u'Краткое наименование', ['shortName'], 40),
            CTextCol(u'Код для отчетов', ['regionalCode'], 20),
            CRefBookCol(u'Тип документа',['documentType_id'], 'rbDocumentType', 20)
            ], rbSocStatusType, [rbCode, rbName])
        self.setWindowTitleEx(u'Типы социального статуса')

    def getItemEditor(self):
        return CRBSocStatusTypeEditor(self)


class CRBSocStatusTypeEditor(Ui_SocStatusTypeItemEditorDialog, CItemEditorDialogWithIdentification):
    def __init__(self,  parent):
        CItemEditorDialogWithIdentification.__init__(self, parent, rbSocStatusType)
        self.setWindowTitleEx(u'Тип социального статуса')
        self.cmbDocumentType.setTable('rbDocumentType')
        self.setupDirtyCather()


    def setRecord(self, record):
        CItemEditorDialogWithIdentification.setRecord(self, record)
        setLineEditValue(self.edtShortName, record, 'shortName')
        setLineEditValue( self.edtRegionalCode, record, 'regionalCode')
        setRBComboBoxValue(self.cmbDocumentType, record, 'documentType_id')
        self.setIsDirty(False)


    def getRecord(self):
        record = CItemEditorDialogWithIdentification.getRecord(self)
        getLineEditValue( self.edtShortName, record, 'shortName')
        getLineEditValue( self.edtRegionalCode,  record, 'regionalCode')
        getRBComboBoxValue(self.cmbDocumentType, record, 'documentType_id')
        return record
