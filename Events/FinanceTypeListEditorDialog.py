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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature

from library.TableModel import CTableModel, CTextCol
from library.database   import CTableRecordCache

from Events.Ui_FinanceTypeListEditor import Ui_FinanceTypeListEditor


class CFinanceTypeTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self._specialValues = []
        self.addColumn(CTextCol(u'Код',              ['code'], 5))
        self.addColumn(CTextCol(u'Наименование',     ['name'], 40))
        self._fieldNames = ['rbFinance.id', 'rbFinance.code', 'rbFinance.name']
        self.setTable('rbFinance')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        table = db.table('rbFinance')
        loadFields = []
        loadFields.append(u'DISTINCT '+ u', '.join(self._fieldNames))
        self._table = table
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, fakeValues=self._specialValues)


class CFinanceTypeListEditorDialog(QtGui.QDialog, Ui_FinanceTypeListEditor):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.tableModel = CFinanceTypeTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblFinanceTypeList.setModel(self.tableModel)
        self.tblFinanceTypeList.setSelectionModel(self.tableSelectionModel)
        self.tblFinanceTypeList.installEventFilter(self)
        self._parent = parent
        self.financeTypeIdList =  []
        self.tblFinanceTypeList.model().setIdList(self.setFinanceTypeList())


    def setFinanceTypeList(self):
        db = QtGui.qApp.db
        table = db.table('rbFinance')
        cond = []
        return db.getDistinctIdList(table, table['id'].name(),
                              where=cond,
                              order=u'rbFinance.code ASC, rbFinance.name ASC')


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.getFinanceTypeList()
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()


    def getFinanceTypeList(self):
        financeTypeIdList = self.tblFinanceTypeList.selectedItemIdList()
        self.financeTypeIdList = financeTypeIdList
        self.close()


    def values(self):
        return self.financeTypeIdList


    def setValue(self, financeTypeIdList):
        self.financeTypeIdList = financeTypeIdList

