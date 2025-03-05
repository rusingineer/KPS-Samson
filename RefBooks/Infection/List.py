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

from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL

from library.AgeSelector     import composeAgeSelector, parseAgeSelector, parseAgeSelectorInt
from library.IdentificationModel import CIdentificationModel, checkIdentification
from library.InDocTable      import CInDocTableCol, CRBInDocTableCol, CInDocTableModel, CRBSearchInDocTableCol
from library.interchange     import getCheckBoxValue, getLineEditValue, setCheckBoxValue, setLineEditValue
from library.ItemsListDialog import CItemEditorBaseDialog, CItemsListDialog

from library.TableModel      import CTableModel, CRefBookCol, CTextCol, CBoolCol
from library.Utils           import forceRef, forceString, forceStringEx, toVariant

from RefBooks.Tables         import rbCode, rbName

from .Ui_RBInfectionItemList import Ui_RBInfectionItemList
from .Ui_RBInfectionEditor   import Ui_RBInfectionEditor


class CRBInfectionList(CItemsListDialog, Ui_RBInfectionItemList):
    setupUi       = Ui_RBInfectionItemList.setupUi
    retranslateUi = Ui_RBInfectionItemList.retranslateUi
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',              [rbCode], 20),
            CTextCol(u'Наименование',     [rbName], 40),
            CBoolCol(u'В наличии',        ['available'], 15),
            CTextCol(u'Региональный код', ['regionalCode'], 20),
            CTextCol(u'Минимальный срок', ['minimumTerm'], 20),
            ], 'rbInfection', [rbCode, rbName])
        self.tblItems.addPopupDelRow()
        self.tblItems.model().rowsRemoved.connect(self.renewListAndSetTo)
        self.setWindowTitleEx(u'Инфекции')


    def getItemEditor(self):
        return CRBInfectionEditor(self)


    def setup(self, *args, **kw):
        CItemsListDialog.setup(self, *args, **kw)
        self.addModels('InfectionVaccines',
                       CTableModel(self,
                                   [
                                    CRefBookCol(u'Вакцина',['vaccine_id'],'rbVaccine', 20, 2)
                                   ],
                                   u'rbInfection_rbVaccine')
                      )
        self.addModels('InfectionMinimumTerms',
                       CTableModel(self,
                                   [
                                    CRefBookCol(u'Инфекция', ['infection_id'], 'rbInfection', 20, 2),
                                    CTextCol(u'Минимальный срок',['minimumTerm'], 20)
                                   ],
                                   u'rbInfection_MinimumTerm')
                      )

        self.setModels(self.tblInfectionVaccines,
                       self.modelInfectionVaccines,
                       self.selectionModelInfectionVaccines)

        self.setModels(self.tblInfectionMinimumTerms,
                       self.modelInfectionMinimumTerms,
                       self.selectionModelInfectionMinimumTerms)

        self.connect(self.selectionModel,
                     SIGNAL('currentChanged(QModelIndex, QModelIndex)'),
                     self.on_selectionModel_currentChanged)


    def getIdByRow(self, row):
        if 0 <= row < self.model.rowCount():
            return self.model.idList()[row]
        return None


    def on_selectionModel_currentChanged(self, current, previous):
        infectionId = self.getIdByRow(current.row())
        if infectionId:
            db = QtGui.qApp.db

            tableInfectionVaccine = db.table('rbInfection_rbVaccine')
            idList = db.getIdList(tableInfectionVaccine, 'id',
                                  tableInfectionVaccine['infection_id'].eq(infectionId), 'idx')
            self.modelInfectionVaccines.setIdList(idList)

            tableInfectionMinimumTerm = db.table('rbInfection_MinimumTerm')
            idList = db.getIdList(tableInfectionMinimumTerm, 'id',
                                  tableInfectionMinimumTerm['master_id'].eq(infectionId))
            self.modelInfectionMinimumTerms.setIdList(idList)

#
# ##########################################################################
#


class CRBInfectionEditor(CItemEditorBaseDialog, Ui_RBInfectionEditor):
    def __init__(self, parent):
        CItemEditorBaseDialog.__init__(self, parent, 'rbInfection')
        self.setupUi(self)
        self.addModels('InfectionVaccines', CInfectionVaccinesModel(self))
        self.addModels('InfectionMinimumTerms', CInfectionMinimumTermsModel(self))
        self.addModels('InfectionIdentification', CIdentificationModel(self, 'rbInfection_Identification', 'rbInfection'))
        self.setModels(self.tblInfectionVaccines,
                       self.modelInfectionVaccines,
                       self.selectionModelInfectionVaccines)
        self.setModels(self.tblInfectionMinimumTerms,
                       self.modelInfectionMinimumTerms,
                       self.selectionModelInfectionMinimumTerms)
        self.setModels(self.tblInfectionIdentification,
                       self.modelInfectionIdentification,
                       self.selectionModelInfectionIdentification)

        self.tblInfectionVaccines.addPopupDelRow()
        self.tblInfectionMinimumTerms.addPopupDelRow()
        self.tblInfectionIdentification.addPopupDelRow()
        self.setWindowTitleEx(u'Инфекция')
        self.edtMinimumTermCount.setValidator(QtGui.QIntValidator(0, 999, self))
        self.edtMinimumTermCount.setMaxLength(3)


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(self.edtCode,                record, 'code' )
        setLineEditValue(self.edtName,                record, 'name' )
        setLineEditValue(self.edtRegionalCode,        record, 'regionalCode' )
        setCheckBoxValue(self.chkAvailable,           record, 'available')

        minimumTermValues = parseAgeSelector(forceString(record.value('minimumTerm')))
        (begMinimumTermUnit, begMinimumTermCount, endMinimumTermUnit, endMinimumTermCount) = minimumTermValues
        self.cmbMinimumTermUnit.setCurrentIndex(begMinimumTermUnit)
        self.edtMinimumTermCount.setText(str(begMinimumTermCount))

        itemId = self.itemId()
        self.modelInfectionVaccines.loadItems(itemId)
        self.modelInfectionMinimumTerms.loadItems(itemId)
        self.modelInfectionMinimumTerms.setFilter('id !=%d' % itemId)
        self.modelInfectionIdentification.loadItems(itemId)


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(self.edtCode,                record, 'code' )
        getLineEditValue(self.edtName,                record, 'name' )
        getLineEditValue(self.edtRegionalCode,        record, 'regionalCode' )
        getCheckBoxValue(self.chkAvailable,           record, 'available')
        record.setValue('minimumTerm', toVariant(composeAgeSelector(
                    self.cmbMinimumTermUnit.currentIndex(),  forceStringEx(self.edtMinimumTermCount.text()),
                    0,  0
                        )))
        return record


    def saveInternals(self, id):
        self.modelInfectionVaccines.saveItems(id)
        self.modelInfectionMinimumTerms.saveItems(id)
        self.modelInfectionIdentification.saveItems(id)


    def checkDataEntered(self):
        result = CItemEditorBaseDialog.checkDataEntered(self)
        result = result and self.checkMinimumTermsModelDataEntered()
        result = result and checkIdentification(self, self.tblInfectionIdentification)
        return result

    def checkMinimumTermsModelDataEntered(self):
        for row, item in enumerate(self.modelInfectionMinimumTerms.items()):
            minimumTerm = forceStringEx(item.value('minimumTerm'))
            infectionId = forceRef(item.value('infection_id'))
            if minimumTerm:
                try:
                    (begUnit, begCount, endUnit, endCount) = parseAgeSelectorInt(minimumTerm)
                    if endUnit or endCount:
                        raise ValueError, u'Недопустимый синтаксис селектора возраста "%s"' % minimumTerm
                except ValueError:
                    return self.checkInputMessage(u'корректный минимальный срок', False, self.tblInfectionMinimumTerms, row, 1)
            if not infectionId:
                return self.checkInputMessage(u'инфекцию', False, self.tblInfectionMinimumTerms, row, 0)
        return True


# ###########################################

class CInfectionVaccinesModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbInfection_rbVaccine', 'id', 'infection_id', parent)
        self.addCol(CRBSearchInDocTableCol(u'Вакцина', 'vaccine_id', 20, 'rbVaccine', showFields=2))



class CInfectionMinimumTermsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbInfection_MinimumTerm', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Инфекция',       'infection_id', 20, 'rbInfection', showFields=2))
        self.addCol(CInDocTableCol(u'Минимальный срок', 'minimumTerm',  10,                maxLength=9))

    def setFilter(self, filter):
        self.cols()[self.getColIndex('infection_id')].filter = filter
