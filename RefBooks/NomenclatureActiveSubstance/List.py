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


from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QRegExp

from library.ItemsListDialog import CItemsListDialog , CItemEditorBaseDialog
from library.TableModel      import CTextCol
from library.interchange     import setLineEditValue, getLineEditValue, setRBComboBoxValue, getRBComboBoxValue
from library.Utils           import forceStringEx
from library.IdentificationModel import CIdentificationModel, checkIdentification
from library.InDocTable      import CInDocTableModel, CRBInDocTableCol
from library.crbcombobox     import CRBComboBox

from .Ui_RBNomenclatureActiveSubstanceEditor import Ui_RBNomenclatureActiveSubstanceEditor


class CRBNomenclatureActiveSubstanceList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',          ['code'], 20),
            CTextCol(u'Наименование на русском', ['name'], 40),
            CTextCol(u'Наименование на латыни', ['mnnLatin'], 40),
            ], 'rbNomenclatureActiveSubstance', ['code', 'name', 'mnnLatin'])
        self.setWindowTitleEx(u'Действующие вещества')

    def getItemEditor(self):
        return CRBNomenclatureActiveSubstanceEditor(self)


class CRBNomenclatureActiveSubstanceEditor(CItemEditorBaseDialog, Ui_RBNomenclatureActiveSubstanceEditor):
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'rbNomenclatureActiveSubstance')
        self.addModels('ActiveSubstanceGroups', CActiveSubstanceGroupsModel(self))
        self.addModels('Identification', CIdentificationModel(self, 'rbNomenclatureActiveSubstance_Identification', 'rbNomenclatureActiveSubstance'))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Действующие вещества')
#        self.addModels('ActiveSubstanceGroups', CActiveSubstanceGroupsModel(self))
        self.setModels(self.tblActiveSubstanceGroups, self.modelActiveSubstanceGroups, self.selectionModelActiveSubstanceGroups)
        self.setModels(self.tblIdentification, self.modelIdentification, self.selectionModelIdentification)
        self.cmbUnit.setTable('rbUnit', True)
        self.tblActiveSubstanceGroups.addPopupDelRow()
        self.tblIdentification.addPopupDelRow()
        self.tblIdentification.setDelRowsChecker(self.modelIdentification.delRowsChecker)
        self.initLineEditor()
        self.setupDirtyCather()


    def initLineEditor(self):
        rR = QRegExp(u"[-?!,.А-Яа-яёЁ\\d\\s]+")
        self.edtNameRussian.setValidator(QtGui.QRegExpValidator(rR, self))
        rL = QRegExp(u"[-?!,.A-Za-z\\d\\s]+")
        self.edtNameLatin.setValidator(QtGui.QRegExpValidator(rL, self))


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(self.edtCode, record, 'code')
        setLineEditValue(self.edtNameRussian, record, 'name')
        setLineEditValue(self.edtNameLatin, record, 'mnnLatin')
        setLineEditValue(self.edtATC,       record, 'ATC')
        setRBComboBoxValue(self.cmbUnit,    record, 'unit_id')
        self.modelActiveSubstanceGroups.loadItems(self.itemId())
        self.modelIdentification.loadItems(self.itemId())


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(self.edtCode, record, 'code')
        getLineEditValue(self.edtNameRussian, record, 'name')
        getLineEditValue(self.edtNameLatin, record, 'mnnLatin')
        getLineEditValue(self.edtATC,       record, 'ATC')
        getRBComboBoxValue(self.cmbUnit,    record, 'unit_id')
        return record


    def saveInternals(self, id):
        self.modelActiveSubstanceGroups.saveItems(id)
        self.modelIdentification.saveItems(id)


    def checkDataEntered(self):
        result = True
        if not checkIdentification(self, self.tblIdentification):
            return False
#        result = result and (forceStringEx(self.edtCode.text()) or self.checkInputMessage(u'код', False, self.edtCode))
        result = result and ((forceStringEx(self.edtNameRussian.text()) or forceStringEx(self.edtNameLatin.text())) or self.checkInputMessage(u'наименование', False, self.edtNameRussian))
        return result


class CActiveSubstanceGroupsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbNomenclatureActiveSubstance_Groups', 'id', 'substance_id', parent)
        self.addCol(CRBInDocTableCol(u'Группа',  'groups_id', 20, 'rbNomenclatureActiveSubstanceGroups', showFields=CRBComboBox.showCodeAndName))

