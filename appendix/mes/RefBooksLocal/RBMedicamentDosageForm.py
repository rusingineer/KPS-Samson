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
from PyQt4.QtCore import Qt

from Ui_RBMedicamentDosageForm import Ui_Dialog
from appendix.mes.RefBooksLocal.ItemsListDialogEx import CItemEditorDialogEx
from appendix.mes.RefBooksLocal.Tables import rbCode, rbName, rbMedicamentDosageForm
from library.ItemsListDialog import CItemsListDialogEx, CItemEditorBaseDialog
from library.TableModel import CTextCol
from library.interchange import setLineEditValue, getLineEditValue


class CRBMedicamentDosageFormList(CItemsListDialogEx):
    def __init__(self, parent):
        CItemsListDialogEx.__init__(self, parent, [
            CTextCol(   u'Код',                  [rbCode], 10),
            CTextCol(   u'Наименование',         [rbName], 30),
            ], rbMedicamentDosageForm, [rbCode, rbName], uniqueCode=True)
        self.setWindowTitleEx(u'Лекарственные формы')

    def getItemEditor(self):
        return CRBMedicamentDosageFormEditor(self)
#
# ##########################################################################
#

class CRBMedicamentDosageFormEditor(CItemEditorDialogEx, Ui_Dialog):
    def __init__(self,  parent):
        CItemEditorDialogEx.__init__(self, parent, rbMedicamentDosageForm)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Лекарственная форма')
        self.setupDirtyCather()


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(   self.edtCode,         record, 'code')
        setLineEditValue(   self.edtName,         record, 'name')


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(   self.edtCode,         record, 'code')
        getLineEditValue(   self.edtName,         record, 'name')

        return record