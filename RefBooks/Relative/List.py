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

from library.interchange         import ( getCheckBoxValue,
                                          getComboBoxValue,
                                          getLineEditValue,
                                          setCheckBoxValue,
                                          setComboBoxValue,
                                          setLineEditValue,
                                        )
from library.IdentificationModel import CIdentificationModel, checkIdentification
from library.ItemsListDialog     import CItemsListDialog, CItemEditorBaseDialog
from library.TableModel          import CTextCol
from library.Utils               import forceStringEx


from RefBooks.Tables         import rbCode, rbRelationType

from .Ui_RBRelative  import Ui_ItemEditorDialog


class CRBRelativeList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',              [rbCode], 20),
            CTextCol(u'Региональный код', ['regionalCode'], 20),
            CTextCol(u'Субъект',          ['leftName'], 40),
            CTextCol(u'Объект',           ['rightName'], 40),
            ], rbRelationType, [rbCode, 'regionalCode', 'leftName', 'rightName', ])
        self.setWindowTitleEx(u'Типы связей пациента')

    def getItemEditor(self):
        return CRBRelativeEditor(self)

#
# ##########################################################################
#

class CRBRelativeEditor(Ui_ItemEditorDialog, CItemEditorBaseDialog):
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, rbRelationType)
        self.setupUi(self)
        self.setWindowTitleEx(u'Тип связи пациента')
        self.addModels('Identification',  CIdentificationModel(self, 'rbRelationType_Identification', 'rbRelationType'))
        self.setupDirtyCather()

        self.setModels(self.tblIdentification, self.modelIdentification, self.selectionModelIdentification)
        self.tblIdentification.addPopupDelRow()
        self.tblIdentification.setDelRowsChecker(self.modelIdentification.delRowsChecker)


    def checkDataEntered(self):
        result = True
        result = result and (forceStringEx(self.edtCode.text()) or self.checkInputMessage(u'код', False, self.edtCode))
        result = result and (forceStringEx(self.edtLeftName.text()) or self.checkInputMessage(u'субъекта отношения', False, self.edtLeftName))
        result = result and (forceStringEx(self.edtRightName.text()) or self.checkInputMessage(u'объекта отношения', False, self.edtRightName))
        result = result and checkIdentification(self, self.tblIdentification)
        return result


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(self.edtCode,         record, 'code')
        setLineEditValue(self.edtRegionalCode, record, 'regionalCode')
        setLineEditValue(self.edtRegionalReverseCode, record, 'regionalReverseCode')
        setLineEditValue(self.edtLeftName,     record, 'leftName')
        setLineEditValue(self.edtRightName,    record, 'rightName')
        setCheckBoxValue(self.chkDirectGeneticRelation,          record, 'isDirectGenetic')
        setCheckBoxValue(self.chkBackwardGeneticRelation,        record, 'isBackwardGenetic')
        setCheckBoxValue(self.chkDirectRepresentativeRelation,   record, 'isDirectRepresentative')
        setCheckBoxValue(self.chkBackwardRepresentativeRelation, record, 'isBackwardRepresentative')
        setCheckBoxValue(self.chkDirectEpidemicRelation,         record, 'isDirectEpidemic')
        setCheckBoxValue(self.chkBackwardEpidemicRelation,       record, 'isBackwardEpidemic')
        setCheckBoxValue(self.chkDirectDonationRelation,         record, 'isDirectDonation')
        setCheckBoxValue(self.chkBackwardDonationRelation,       record, 'isBackwardDonation')
        setComboBoxValue(self.cmbLeftSex, record, 'leftSex')
        setComboBoxValue(self.cmbRightSex, record, 'rightSex')
        self.modelIdentification.loadItems(self.itemId())


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(self.edtCode,         record, 'code')
        getLineEditValue(self.edtRegionalCode, record, 'regionalCode')
        getLineEditValue(self.edtRegionalReverseCode, record, 'regionalReverseCode')
        getLineEditValue(self.edtLeftName,     record, 'leftName')
        getLineEditValue(self.edtRightName,    record, 'rightName')
        getCheckBoxValue(self.chkDirectGeneticRelation,          record, 'isDirectGenetic')
        getCheckBoxValue(self.chkBackwardGeneticRelation,        record, 'isBackwardGenetic')
        getCheckBoxValue(self.chkDirectRepresentativeRelation,   record, 'isDirectRepresentative')
        getCheckBoxValue(self.chkBackwardRepresentativeRelation, record, 'isBackwardRepresentative')
        getCheckBoxValue(self.chkDirectEpidemicRelation,         record, 'isDirectEpidemic')
        getCheckBoxValue(self.chkBackwardEpidemicRelation,       record, 'isBackwardEpidemic')
        getCheckBoxValue(self.chkDirectDonationRelation,         record, 'isDirectDonation')
        getCheckBoxValue(self.chkBackwardDonationRelation,       record, 'isBackwardDonation')
        getComboBoxValue(self.cmbLeftSex, record, 'leftSex')
        getComboBoxValue(self.cmbRightSex, record, 'rightSex')
        return record


    def saveInternals(self, id):
        self.modelIdentification.saveItems(id)

