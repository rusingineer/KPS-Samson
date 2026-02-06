# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
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

from library.database         import CTableRecordCache
from library.TableModel       import CTableModel, CTextCol
from library.Utils            import forceString

from Reports.Ui_SpecialityListDialog import Ui_SpecialityListDialog


class CContingentTypeListDialog(QtGui.QDialog, Ui_SpecialityListDialog):
    def __init__(self, parent, filter=None):
        QtGui.QDialog.__init__(self, parent)
        self.tableModel = CContingentTypeListModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblSpecialityList.setModel(self.tableModel)
        self.tblSpecialityList.setSelectionModel(self.tableSelectionModel)
        self.tblSpecialityList.installEventFilter(self)
        self.contingentTypeidList =  []
        self.filter = filter
        self.tblSpecialityList.model().setIdList(self.setSpecialityList())


    def setSpecialityList(self):
        db = QtGui.qApp.db
        table = db.table('rbContingentType')
        cond = []
        if self.filter:
            cond.append(self.filter)
        return db.getDistinctIdList(table, table['id'].name(),
                            where=cond,
                            order=u'rbContingentType.code ASC, rbContingentType.name ASC')


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.getSpecialityList()
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()


    def getSpecialityList(self):
        contingentTypeidList = self.tblSpecialityList.selectedItemIdList()
        self.contingentTypeidList = contingentTypeidList
        self.close()


    def values(self):
        return self.contingentTypeidList


    def setValue(self, contingentTypeidList):
        self.contingentTypeidList = contingentTypeidList


class CContingentTypeListModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self._specialValues = []
        self.addColumn(CTextCol(u'Код',          ['code'], 5))
        self.addColumn(CTextCol(u'Наименование', ['name'], 40))
        self._fieldNames = ['rbContingentType.id', 'rbContingentType.code', 'rbContingentType.name']
        self.setTable('rbContingentType')


    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        table = db.table('rbContingentType')
        loadFields = []
        loadFields.append(u'DISTINCT '+ u', '.join(self._fieldNames))
        self._table = table
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, fakeValues=self._specialValues)


def formatContingentTypeList(contingentTypeIdList):
    if not contingentTypeIdList:
        return u''
    db = QtGui.qApp.db
    table = db.table('rbContingentType')
    records = db.getRecordList(table, [table['name']], [table['id'].inlist(contingentTypeIdList)])
    return u', '.join(forceString(record.value('name')) for record in records if forceString(record.value('name')))
