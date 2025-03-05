# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2016-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4.QtCore import pyqtSignature

from library.IdentificationModel import CIdentificationModel, checkIdentification
from library.ItemsListDialog     import CItemEditorDialog
from library.Ui_ItemEditorDialogWithIdentification import Ui_ItemEditorDialogWithIdentification


# Согласен, это безобразное название.
# в тот день, когда все справочники получат _Identification
# нужно будет удалить CItemEditorDialog а этот класс переименовать в CItemEditorDialog

class CItemEditorDialogWithIdentification(Ui_ItemEditorDialogWithIdentification, CItemEditorDialog):
    def __init__(self, parent, tableName):
        CItemEditorDialog.__init__(self, parent, tableName)
#        self.setupUi(self)

    def preSetupUi(self):
        CItemEditorDialog.preSetupUi(self)
        self.addModels('Identification',
                         CIdentificationModel(self,
                                              self._tableName + '_Identification',
                                              self._tableName
                                             )
                        )
        pass


    def postSetupUi(self):
        CItemEditorDialog.postSetupUi(self)
        self.setModels(self.tblIdentification, self.modelIdentification, self.selectionModelIdentification)
        self.tblIdentification.addPopupDelRow()
        self.tblIdentification.setDelRowsChecker(self.modelIdentification.delRowsChecker)


    def setRecord(self, record):
        CItemEditorDialog.setRecord(self, record)
        self.modelIdentification.loadItems(self.itemId())


    def getRecord(self):
        record = CItemEditorDialog.getRecord(self)
        return record


    def saveInternals(self, id):
        self.modelIdentification.saveItems(id)


    def checkDataEntered(self):
        result = CItemEditorDialog.checkDataEntered(self)
        result = result and checkIdentification(self, self.tblIdentification)
        return result


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelIdentification_dataChanged(self, topLeft, bottomRight):
        self.setIsDirty()
        self.modelIdentification.on_dataChanged(topLeft, bottomRight)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelIdentification_currentChanged(self, current, previous):
        self.modelIdentification.set_row_system_id(current, previous)
