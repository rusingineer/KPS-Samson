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

from library.interchange import (setLineEditValue, setComboBoxValue,
                                 setDoubleBoxValue, setSpinBoxValue,
                                 getLineEditValue, getComboBoxValue,
                                 getDoubleBoxValue, getSpinBoxValue,
                                 setDateEditValue, getDateEditValue)
from library.TableModel import CTextCol, CEnumCol, CDoubleCol, CNumCol, CDateCol
from library.ItemsListDialog import CItemEditorBaseDialog, CItemsListDialogEx

from ItemsListDialogEx import CItemEditorDialogEx

from Tables import rbCode, rbName, rbMesKSG
from Ui_MesKSG import Ui_Dialog


class CMesKSGList(CItemsListDialogEx):
    ksgType = (u'Неизвестный', u'Тер.', u'Комб.', u'Хир.', u'Проч')

    def __init__(self, parent):
        CItemsListDialogEx.__init__(self, parent, [
            CTextCol(   u'Код',                  [rbCode], 10),
            CTextCol(   u'Наименование',         [rbName], 30),
            CEnumCol(   u'Тип КСГ',     ['type'],  self.ksgType, 30),
            CDoubleCol(   u'Весовой коэффициент затратоемкости',         ['vk'], 30),
            CNumCol(   u'Код клинико-профильной группы',         ['prof'], 30),
            CDoubleCol(   u'Управленческий коэффициент',         ['managementFactor'], 30),
            CDateCol(u'Начало действия', ['begDate'], 30),
            CDateCol(u'Окончание действия', ['endDate'], 30),
            ], rbMesKSG, [rbCode, rbName], uniqueCode=True)
        self.setWindowTitleEx(u'Группы КСГ')

    def getItemEditor(self):
        return CMesKSGEditor(self)
#
# ##########################################################################
#

class CMesKSGEditor(CItemEditorDialogEx, Ui_Dialog):
    def __init__(self,  parent):
        CItemEditorDialogEx.__init__(self, parent, rbMesKSG)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'КСГ')
        self.cmbType.addItems(CMesKSGList.ksgType)
        self.edtBegDate.canBeEmpty()
        self.edtEndDate.canBeEmpty()
        self.setupDirtyCather()


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(   self.edtCode,         record, 'code')
        setLineEditValue(   self.edtName,         record, 'name')
        setComboBoxValue(   self.cmbType,       record, 'type')
        setDoubleBoxValue(   self.edtVk,       record, 'vk')
        setSpinBoxValue(   self.edtProf,      record, 'prof')
        setDoubleBoxValue(self.edtManagementFactor, record, 'managementFactor')
        setDateEditValue(self.edtBegDate, record, 'begDate')
        setDateEditValue(self.edtEndDate, record, 'endDate')


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(   self.edtCode,         record, 'code')
        getLineEditValue(   self.edtName,         record, 'name')
        getComboBoxValue(   self.cmbType,       record, 'type')
        getDoubleBoxValue(   self.edtVk,       record, 'vk')
        getSpinBoxValue(   self.edtProf,      record, 'prof')
        getDoubleBoxValue(self.edtManagementFactor, record, 'managementFactor')
        getDateEditValue(self.edtBegDate, record, 'begDate')
        getDateEditValue(self.edtEndDate, record, 'endDate')
        return record
