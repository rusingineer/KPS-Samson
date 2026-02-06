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

from library.interchange         import getDateEditValue, setDateEditValue
from library.ItemsListDialog     import CItemsListDialog
from library.ItemEditorDialogWithIdentification import CItemEditorDialogWithIdentification

from library.TableModel          import CTextCol, CDateCol
from library.Utils               import forceString, forceStringEx, toVariant, trim
from RefBooks.Tables             import rbCode, rbName

from .Ui_RBTNMPhaseEditor import Ui_RBTNMPhaseEditor
from ..Utils import CMKBOtoMKBXColumn


class CRBTNMPhaseList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',          [rbCode], 20),
            CTextCol(u'Наименование', [rbName], 40),
            CTextCol(u'Диагноз',      ['MKB'], 20),
            CMKBOtoMKBXColumn(u'Диагноз МКБ-10', ['MKB', 'begDate'], 20),
            CDateCol(u'Дата начала', ['begDate'], 20),
            CDateCol(u'Дата окончания', ['endDate'], 20),
            ], 'rbTNMphase', [rbCode, rbName, 'MKB'])
        self.setWindowTitleEx(u'Стадия заболевания по онкологии')

    def getItemEditor(self):
        return CRBTNMPhaseEditor(self)

#
# ##########################################################################
#

class CRBTNMPhaseEditor(Ui_RBTNMPhaseEditor, CItemEditorDialogWithIdentification):
    doCheckName = False

    def __init__(self, parent):
        CItemEditorDialogWithIdentification.__init__(self, parent, 'rbTNMphase')
        self.setWindowTitleEx(u'Стадии заболевания по онкологии')
        self.setupDirtyCather()


    def setRecord(self, record):
        CItemEditorDialogWithIdentification.setRecord(self, record)
        self.cmbMKB.setText(forceString(record.value('MKB')))
        setDateEditValue(self.edtBegDate, record, 'begDate')
        setDateEditValue(self.edtEndDate, record, 'endDate')
        self.modelIdentification.loadItems(self.itemId())


    def getRecord(self):
        record = CItemEditorDialogWithIdentification.getRecord(self)
        record.setValue('MKB', toVariant(forceStringEx(self.cmbMKB.text())))
        getDateEditValue(self.edtBegDate, record, 'begDate')
        getDateEditValue(self.edtEndDate, record, 'endDate')
        return record


    def checkDataEntered(self):
        result = CItemEditorDialogWithIdentification.checkDataEntered(self)
        result = result and (trim(forceStringEx(self.cmbMKB.text())) or self.checkInputMessage(u'диагноз', True, self.cmbMKB))
        return result
