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

from library.interchange     import getComboBoxValue, getRBComboBoxValue, setComboBoxValue, setRBComboBoxValue
from library.ItemEditorDialogWithIdentification import CItemEditorDialog
from library.ItemsListDialog import CItemsListDialog
from library.TableModel      import CRefBookCol, CEnumCol, CTextCol

from .Ui_RBStockMotionNumberEditor import Ui_StockMotionNumberEditorDialog


class CRBStockMotionNumberList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',            ['code'],   10),
            CTextCol(u'Наименование',   ['name'],   10),
            CEnumCol(u'Тип накладной',  ['motionType'],[u'Внутренняя накладная', u'Инвентаризация', u'Финансовая переброска',
            u'Производство', u'Списание на пациента', u'Возврат от пациента', u'Резервирование на пациента',
            u'Утилизация', u'Внутреннее потребление', u'Требование', u'Накладная от поставщика', u'Списание остаточных количеств'],    10),
            CRefBookCol(u'Подразделение',   ['orgStructure_id'], 'OrgStructure',10),
            CRefBookCol(u'Счетчик',    ['counter_id'], 'rbCounter',10),
            ], 'rbStockMotionNumber', ['code', 'name'])
        self.setWindowTitleEx(u'Счетчики номеров накладных')


    def getItemEditor(self):
        return CRBStockMotionNumberListEditor(self)


# ###################################################


class CRBStockMotionNumberListEditor(Ui_StockMotionNumberEditorDialog, CItemEditorDialog):
    def __init__(self,  parent):
        CItemEditorDialog.__init__(self, parent, 'rbStockMotionNumber')
        self.setWindowTitleEx(u'Счетчик номера накладной')
        self.cmbCounter.setTable('rbCounter')
        self.setupDirtyCather()


    def setRecord(self, record):
        CItemEditorDialog.setRecord(self, record)
        setComboBoxValue(self.cmbStockMotionType, record, 'motionType')
        setRBComboBoxValue(self.cmbOrgStructure,  record, 'orgStructure_id')
        setRBComboBoxValue(self.cmbCounter,       record, 'counter_id')


    def getRecord(self):
        record = CItemEditorDialog.getRecord(self)
        getComboBoxValue(self.cmbStockMotionType, record, 'motionType')
        getRBComboBoxValue(self.cmbOrgStructure,  record, 'orgStructure_id')
        getRBComboBoxValue(self.cmbCounter,       record, 'counter_id')
        return record
