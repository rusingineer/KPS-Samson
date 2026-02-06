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

from PyQt4.QtCore import Qt, QModelIndex

from library.crbcombobox import CRBComboBox
from library.InDocTable  import CInDocTableModel, CIntInDocTableCol, CRBInDocTableCol
from library.Utils       import forceInt


class CWorkHurtsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientWork_Hurt', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Вредность', 'hurtType_id', 30, 'rbHurtType', showFields = CRBComboBox.showNameAndCode, addNone=False))
        self.addCol(CIntInDocTableCol(u'Стаж',   'stage', 4, low=0, high=99))
        # self.__factors = []
        # self.__factorsModel = None
        self.readOnly = False

# WTF? базовый класс сам поддерживает readOnpy
    def setReadOnly(self, value):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
           return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    # def setFactorsModel(self,  model):
        # self.__factorsModel = model


    # def factors(self, row):
    #     if row >= len(self.__factors):
    #         self.__factors.extend([None]*(row-len(self.__factors)+1))
    #     if self.__factors[row] is None:
    #         self.__factors[row] = []
    #     return self.__factors[row]


    def insertRecord(self, row, record):
        CInDocTableModel.insertRecord(self, row, record)
        self.__factors.insert(row, [])


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        return CInDocTableModel.removeRows(self, row, count, parentIndex)


    def loadItems(self, masterId):
        CInDocTableModel.loadItems(self, masterId)
        # self.__factors = []
        # if self.__factorsModel:
        #     self.__factorsModel.blockSignals(True)
        #     try:
        #         for row, item in enumerate(self.items()):
        #             itemId = forceInt(item.value('id'))
        #             self.__factorsModel.setItems(self.factors(row))
        #             self.__factorsModel.loadItems(itemId)
        #             self.__factors[row] = self.__factorsModel.items()
        #     finally:
        #         self.__factorsModel.blockSignals(False)
        #     self.__factorsModel.reset()
        #     self.__factorsModel.setItems(self.factors(0))


    def saveItems(self, masterId):
        CInDocTableModel.saveItems(self, masterId)
        # saveItems = self.__factorsModel.items()
        # if self.__factorsModel:
        #     try:
        #         for row, item in enumerate(self.items()):
        #             itemId = forceInt(item.value('id'))
        #             self.__factorsModel.setItems(self.factors(row))
        #             self.__factorsModel.saveItems(itemId)
        #         self.__factorsModel.setItems(saveItems)
        #     finally:
        #         self.__factorsModel.blockSignals(False)


class CWorkHurtFactorsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientWork_Hurt_Factor', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Фактор', 'factorType_id', 34, 'rbHurtFactorType', showFields = CRBComboBox.showNameAndCode, addNone=False))
        self.readOnly = False


    def setReadOnly(self, value):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
           return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)
