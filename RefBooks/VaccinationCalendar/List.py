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
from PyQt4.QtCore import Qt, QModelIndex, QVariant, pyqtSignature, SIGNAL

from library.AgeSelector     import parseAgeSelectorInt
from library.InDocTable      import CInDocTableCol, CRBInDocTableCol, CInDocTableModel, CEnumInDocTableCol
from library.interchange     import getDateEditValue, getLineEditValue, setDateEditValue, setLineEditValue
from library.ItemsListDialog import CItemEditorBaseDialog, CItemsListDialog
from library.TableModel      import CDateCol, CEnumCol, CRefBookCol, CTableModel, CTextCol
from library.Utils           import forceRef, forceStringEx

from RefBooks.Tables         import rbCode, rbName

from Ui_RBVaccinationCalendarItemList import Ui_RBVaccinationCalendarItemList
from Ui_RBVaccinationCalendarEditor   import Ui_RBVaccinationCalendarEditor


SexList = ['', u'М', u'Ж']


class CRBVaccinationCalendarList(Ui_RBVaccinationCalendarItemList, CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',           [rbCode], 20),
            CTextCol(u'Наименование',  [rbName], 40),
            CDateCol(u'Дата введения', ['date'], 20)
            ], 'rbVaccinationCalendar', [rbCode, rbName])
        self.tblItems.addPopupDelRow()
        self.tblItems.model().rowsRemoved.connect(self.renewListAndSetTo)
        self.setWindowTitleEx(u'Календари прививок')


    def getItemEditor(self):
        return CRBVaccinationCalendarEditor(self)


    def setup(self, *args, **kw):
        CItemsListDialog.setup(self, *args, **kw)
        self.addModels(
                       'VaccinationCalendarInfections',
                       CTableModel(self,
                                   [
                                    CRefBookCol(u'Инфекция', ['infection_id'], 'rbInfection', 20),
                                    CTextCol(   u'Тип прививки', ['vaccinationType'], 20),
                                    CEnumCol(   u'Пол',          ['sex'], SexList, 10),
                                    CTextCol(   u'Возраст',      ['age'], 20)
                                   ],
                                   u'rbVaccinationCalendar_Infection')
                      )

        self.setModels(self.tblVaccinationCalendarInfections,
                       self.modelVaccinationCalendarInfections,
                       self.selectionModelVaccinationCalendarInfections)

        self.connect(self.selectionModel,
                     SIGNAL('currentChanged(QModelIndex, QModelIndex)'),
                     self.on_selectionModel_currentChanged)


    def getIdByRow(self, row):
        if 0 <= row < self.model.rowCount():
            return self.model.idList()[row]
        return None


    def on_selectionModel_currentChanged(self, current, previous):
        itemId = self.getIdByRow(current.row())
        if itemId:
            db = QtGui.qApp.db

            tableVaccinationCalendarInfection = db.table('rbVaccinationCalendar_Infection')
            idList = db.getIdList(tableVaccinationCalendarInfection, 'id',
                                  tableVaccinationCalendarInfection['master_id'].eq(itemId), 'id')
            self.modelVaccinationCalendarInfections.setIdList(idList)


#
# ##########################################################################
#

class CRBVaccinationCalendarEditor(CItemEditorBaseDialog, Ui_RBVaccinationCalendarEditor):
    def __init__(self, parent):
        CItemEditorBaseDialog.__init__(self, parent, 'rbVaccinationCalendar')
        self.setupUi(self)
        self.addModels('VaccinationCalendarInfections', CVaccinationCalendarInfectionsModel(self))
        self.setModels(self.tblVaccinationCalendarInfections,
                       self.modelVaccinationCalendarInfections,
                       self.selectionModelVaccinationCalendarInfections)

        self.cmbFilterInfection.setTable('rbInfection')

        self.tblVaccinationCalendarInfections.addPopupDelRow()

        self.setWindowTitleEx(u'Календарь прививок')


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(self.edtCode,                record, 'code' )
        setLineEditValue(self.edtName,                record, 'name' )
        setDateEditValue(self.edtDate,                record, 'date' )
        self.modelVaccinationCalendarInfections.loadItems(self.itemId())


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(self.edtCode,                record, 'code' )
        getLineEditValue(self.edtName,                record, 'name' )
        getDateEditValue(self.edtDate,                record, 'date' )
        return record


    def saveInternals(self, id):
        self.modelVaccinationCalendarInfections.saveItems(id)

    def checkDataEntered(self):
        result = CItemEditorBaseDialog.checkDataEntered(self)
        result = result and self.checkInfectionsModelAgeEntered()
        return result

    def checkInfectionsModelAgeEntered(self):
        for row, item in enumerate(self.modelVaccinationCalendarInfections.items()):
            age = forceStringEx(item.value('age'))
            if age:
                try:
                    parseAgeSelectorInt(age)
                except ValueError:
                    return self.checkInputMessage(u'корректный возраст', False, self.tblVaccinationCalendarInfections, row, 2)
        return True


    @pyqtSignature('int')
    def on_cmbFilterInfection_currentIndexChanged(self, index):
        self.modelVaccinationCalendarInfections.setInfection(self.cmbFilterInfection.value())


# ############################################################


class CVaccinationCalendarInfectionsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbVaccinationCalendar_Infection', 'id', 'master_id',   parent)
        self.addCol(CRBInDocTableCol(  u'Инфекция',     'infection_id',    20,   'rbInfection'))
        self.addCol(CInDocTableCol(    u'Тип прививки', 'vaccinationType', 20,                  maxLength=7))
        self.addCol(CEnumInDocTableCol(u'Пол',          'sex',             5,                   SexList))
        self.addCol(CInDocTableCol(    u'Возраст',      'age',             20,                  maxLength=9))
        self._infectionId = None
        self._tmpItems = []
        self._mapFakeRow2RealRow = {}

    def loadItems(self, masterId):
        CInDocTableModel.loadItems(self, masterId)
        self._tmpItems = list(self._items)
        self._applyOne2OneRowCache()



    def _applyOne2OneRowCache(self):
        for row in xrange(len(self.items())):
            self._mapFakeRow2RealRow[row] = row


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0<=row and row+count<=len(self._items):
            result = CInDocTableModel.removeRows(self, row, count, parentIndex)
            if result:
                for locRow in range(row, row+count):
                    realRow = self._mapFakeRow2RealRow[locRow]
                    del self._tmpItems[realRow]
        return False


    def setData(self, index, value, role=Qt.EditRole):
        addingNewRercord = False
        if role == Qt.EditRole:
#            column = index.column()
            row = index.row()
            if row == len(self._items) and not value.isNull():
                addingNewRercord = True
        if role == Qt.CheckStateRole:
#            column = index.column()
            row = index.row()
            state = value.toInt()[0]
            if row == len(self._items) and state != Qt.Unchecked:
                addingNewRercord = True
        result = CInDocTableModel.setData(self, index, value, role)
        if addingNewRercord:
            self._tmpItems.append(self._items[-1])
            self._mapFakeRow2RealRow[len(self.items())-1] = len(self._tmpItems)-1
        return result


    def getEmptyRecord(self):
        record = CInDocTableModel.getEmptyRecord(self)
        if self._infectionId:
            record.setValue('infection_id', QVariant(self._infectionId))
        return record


    def insertRecord(self, row, record):
        self._tmpItems.append(record)
        CInDocTableModel.insertRecord(self, row, record)


    def saveItems(self, masterId):
        self._items = list(self._tmpItems)
        CInDocTableModel.saveItems(self, masterId)


    def setInfection(self, infectionId):
        self._infectionId = infectionId
        if infectionId:
            self.cols()[self.getColIndex('infection_id')].setReadOnly(True)
            locItems = list(self._tmpItems)
            self._items = []
            fakeRow = 0
            for realRow, item in enumerate(locItems):
                if infectionId == forceRef(item.value('infection_id')):
                    self._items.append(item)
                    self._mapFakeRow2RealRow[fakeRow] = realRow
                    fakeRow += 1
        else:
            self._items = list(self._tmpItems)
            self.cols()[self.getColIndex('infection_id')].setReadOnly(False)
            self._applyOne2OneRowCache()
        self.reset()
