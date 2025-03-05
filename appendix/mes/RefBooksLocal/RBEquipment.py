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

from Ui_RBEquipment import Ui_Dialog
from appendix.mes.RefBooksLocal.ItemsListDialogEx import CItemEditorDialogEx
from appendix.mes.RefBooksLocal.Tables import rbCode, rbName, rbEquipmentGroup, rbEquipment
from library.ItemsListDialog import CItemsListDialogEx, CItemEditorBaseDialog
from library.TableModel import CTextCol, CRefBookCol, CNumCol
from library.interchange import setLineEditValue, setRBComboBoxValue, setSpinBoxValue, getLineEditValue, \
    getRBComboBoxValue, getSpinBoxValue


class CRBEquipmentList(CItemsListDialogEx):
    def __init__(self, parent):
        CItemsListDialogEx.__init__(self, parent, [
            CTextCol(   u'Код',                  [rbCode], 10),
            CTextCol(   u'Наименование',         [rbName], 30),
            CRefBookCol(   u'Группа',     ['group_id'], rbEquipmentGroup, 30),
            CNumCol(   u'Дозировка',         ['dosage'], 30),
            CNumCol(   u'Тариф',         ['tariff'], 30),
            ], rbEquipment, [rbCode, rbName], uniqueCode=True)
        self.setWindowTitleEx(u'Типы оборудования')

    def getItemEditor(self):
        return CRBEquipmentEditor(self)
#
# ##########################################################################
#

class CRBEquipmentEditor(CItemEditorDialogEx, Ui_Dialog):
    def __init__(self,  parent):
        CItemEditorDialogEx.__init__(self, parent, rbEquipment)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Тип оборудования')
        self.cmbType.setTable(rbEquipmentGroup)
        self.setupDirtyCather()


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(   self.edtCode,         record, 'code')
        setLineEditValue(   self.edtName,         record, 'name')
        setRBComboBoxValue(   self.cmbType,       record, 'group_id')
        setSpinBoxValue(   self.spinBox,       record, 'dosage')
        setLineEditValue(   self.edtTariff,      record, 'tariff')

    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(   self.edtCode,         record, 'code')
        getLineEditValue(   self.edtName,         record, 'name')
        getRBComboBoxValue(   self.cmbType,       record, 'group_id')
        getSpinBoxValue(   self.spinBox,       record, 'dosage')
        getLineEditValue(   self.edtTariff,      record, 'tariff')
        return record