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
from library.ItemEditorDialogWithIdentification import CItemEditorDialogWithIdentification
from library.interchange     import getCheckBoxValue, getLineEditValue, getRBComboBoxValue, setCheckBoxValue, setLineEditValue, setRBComboBoxValue, setDateEditValue, getDateEditValue
from library.ItemsListDialog import CItemsListDialog
from library.TableModel      import CBoolCol, CRefBookCol, CTextCol, CDateCol

from RefBooks.Tables         import rbCode, rbEventTypePurpose, rbName, rbResult, rbBegDate, rbEndDate

from .Ui_RBResultEditor import Ui_ItemEditorDialog


class CRBResultList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CRefBookCol(u'Назначение',      ['eventPurpose_id'], rbEventTypePurpose, 30),
            CTextCol(   u'Код',             [rbCode],         10),
            CTextCol(   u'Наименование',    [rbName],         40),
            CTextCol(   u'Федеральный код', ['federalCode'],  10),
            CTextCol(   u'Код ЕГИСЗ',       ['usishCode'],    10),
            CTextCol(   u'Региональный код',['regionalCode'], 10),
            CBoolCol(   u'Не закончен',     ['continued'],    10),
            CDateCol(   u'Дата начала',     [rbBegDate],      20),
            CDateCol(   u'Дата окончания',  [rbEndDate],      20),
            ], rbResult, ['eventPurpose_id', rbCode, rbName, rbBegDate, rbEndDate])
        self.setWindowTitleEx(u'Результаты обращения')

    def getItemEditor(self):
        return CRBResultEditor(self)
#
# ##########################################################################
#

class CRBResultEditor(Ui_ItemEditorDialog, CItemEditorDialogWithIdentification):
    def __init__(self,  parent):
        CItemEditorDialogWithIdentification.__init__(self, parent, rbResult)
        self.setWindowTitleEx(u'Результат обращения')
        self.cmbEventPurpose.setTable(rbEventTypePurpose, False)


    def setRecord(self, record):
        CItemEditorDialogWithIdentification.setRecord(self, record)
        setRBComboBoxValue( self.cmbEventPurpose, record, 'eventPurpose_id')
        setLineEditValue(   self.edtFederalCode,  record, 'federalCode')
        setLineEditValue(   self.edtUsishCode,    record, 'usishCode')
        setLineEditValue(   self.edtRegionalCode, record, 'regionalCode')
        setCheckBoxValue(   self.chkContinued,    record, 'continued')
        setDateEditValue(   self.edtBegDate,      record, 'begDate')
        setDateEditValue(   self.edtEndDate,      record, 'endDate')


    def getRecord(self):
        record = CItemEditorDialogWithIdentification.getRecord(self)
        getRBComboBoxValue( self.cmbEventPurpose, record, 'eventPurpose_id')
        getLineEditValue(   self.edtFederalCode,  record, 'federalCode')
        getLineEditValue(   self.edtUsishCode,    record, 'usishCode')
        getLineEditValue(   self.edtRegionalCode, record, 'regionalCode')
        getCheckBoxValue(   self.chkContinued,    record, 'continued')
        getDateEditValue(   self.edtBegDate,      record, 'begDate')
        getDateEditValue(   self.edtEndDate,      record, 'endDate')
        return record
