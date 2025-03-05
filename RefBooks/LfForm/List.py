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


from library.TableModel      import CTextCol, CEnumCol
from library.ItemsListDialog import CItemsListDialog, CItemEditorDialog
from library.Utils           import forceStringEx, forceBool, toVariant

from RefBooks.Tables         import rbCode, rbName

from .Ui_RBLfFormEditor import Ui_RBLfFormEditor

# Какое скверное имя таблицы :(
# rbLfForm - это «Формы выпуска лекарственных препаратов»
# должно быть rbDosageForm

class CRBLfFormList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',          [rbCode], 20),
            CTextCol(u'Наименование', [rbName], 40),
            CTextCol(u'Дозировка', ['dosage'], 10),
            CEnumCol(u'Относится к ЕСКЛП', ['isESKLP'], [u'нет', u'да'], 4),
            ], 'rbLfForm', [rbCode, rbName])
        self.setWindowTitleEx(u'Формы выпуска лекарственных препаратов')


    def getItemEditor(self):
        return CRBLfFormEditor(self)


class CRBLfFormEditor(Ui_RBLfFormEditor, CItemEditorDialog):
    def __init__(self,  parent):
        CItemEditorDialog.__init__(self, parent, 'rbLfForm')
        self.setWindowTitleEx(u'Форма выпуска лекарственных препаратов')


    def setRecord(self, record):
        CItemEditorDialog.setRecord(self, record)
        self.edtDosage.setText(forceStringEx(record.value('dosage')))
        isESKLP = forceBool(record.value('isESKLP'))
        self.chkIsESKLP.setChecked(isESKLP)
        self.setReadOnly(isESKLP)
        self.edtCode.setReadOnly(isESKLP)
        self.edtName.setReadOnly(isESKLP)
        self.edtDosage.setReadOnly(isESKLP)
        self.chkIsESKLP.setEnabled(not isESKLP)


    def getRecord(self):
        record = CItemEditorDialog.getRecord(self)
        record.setValue('dosage', toVariant(self.edtDosage.text()))
        record.setValue('isESKLP', toVariant(self.chkIsESKLP.isChecked()))
        return record

