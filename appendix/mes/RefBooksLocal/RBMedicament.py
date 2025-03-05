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

from Ui_RBMedicament import Ui_Dialog
from appendix.mes.RefBooksLocal.ItemsListDialogEx import CItemEditorDialogEx
from appendix.mes.RefBooksLocal.Tables import rbCode, rbName, rbMedicamentDosageForm, rbMedicament
from library.ItemsListDialog import CItemsListDialogEx, CItemEditorBaseDialog
from library.TableModel import CTextCol, CRefBookCol, CNumCol
from library.interchange import setLineEditValue, setRBComboBoxValue, setSpinBoxValue, getLineEditValue, \
    getRBComboBoxValue, getSpinBoxValue


class CRBMedicamentList(CItemsListDialogEx):
    def __init__(self, parent):
        CItemsListDialogEx.__init__(self, parent, [
            CTextCol(   u'Код',                  [rbCode], 10),
            CTextCol(   u'Наименование',         [rbName], 30),
            CTextCol(   u'Торговое наименование',  ['tradeName'], 30),
            CTextCol(   u'Дозировка',  ['dosage'], 30),
            CTextCol(   u'Форма выпуска',  ['form'], 30),
            CRefBookCol(   u'Лекарственная форма', ['dosageForm_id'], rbMedicamentDosageForm, 30),
            CNumCol(   u'Кол.-во в упаковке',         ['packSize'], 10),
            CNumCol(   u'Стоимость упаковки',         ['packPrice'], 10),
            CNumCol(   u'Стоимость единицы',         ['unitPrice'], 10),
            ], rbMedicament, [rbCode, rbName], uniqueCode=True)
        self.setWindowTitleEx(u'Медикаменты')

    def getItemEditor(self):
        return CRBMedicamentEditor(self)
#
# ##########################################################################
#

class CRBMedicamentEditor(CItemEditorDialogEx, Ui_Dialog):
    def __init__(self,  parent):
        CItemEditorDialogEx.__init__(self, parent, rbMedicament)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Медикамент')
        self.cmbForm.setTable(rbMedicamentDosageForm)
        self.setupDirtyCather()


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(   self.edtCode,         record, 'code')
        setLineEditValue(   self.edtName,         record, 'name')
        setLineEditValue(   self.edtDosage,       record, 'dosage')
        setLineEditValue(   self.edtForm,         record, 'form')
        setLineEditValue(   self.edtTradeName,    record, 'tradeName')
        setRBComboBoxValue( self.cmbForm,       record, 'dosageForm_id')
        setSpinBoxValue(   self.spinBox,       record, 'packSize')
        setLineEditValue(   self.edtPackPrice,    record, 'packPrice')
        setLineEditValue(   self.edtUnitPrice,    record, 'unitPrice')

    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(   self.edtCode,         record, 'code')
        getLineEditValue(   self.edtName,         record, 'name')
        getLineEditValue(   self.edtTradeName,    record, 'tradeName')
        getLineEditValue(   self.edtDosage,       record, 'dosage')
        getLineEditValue(   self.edtForm,         record, 'form')
        getRBComboBoxValue( self.cmbForm,       record, 'dosageForm_id')
        getSpinBoxValue(   self.spinBox,       record, 'packSize')
        getLineEditValue(   self.edtPackPrice,    record, 'packPrice')
        getLineEditValue(   self.edtUnitPrice,    record, 'unitPrice')       
        return record