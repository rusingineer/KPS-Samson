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


class CSpecialityListDialog(QtGui.QDialog, Ui_SpecialityListDialog):
    def __init__(self, parent, filter=None):
        QtGui.QDialog.__init__(self, parent)
        self.tableModel = CSpecialityTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblSpecialityList.setModel(self.tableModel)
        self.tblSpecialityList.setSelectionModel(self.tableSelectionModel)
        self.tblSpecialityList.installEventFilter(self)
        self._parent = parent
        self.specialityIdList =  []
        self.filter = filter
        self.tblSpecialityList.model().setIdList(self.setSpecialityList())


    def setSpecialityList(self):
        db = QtGui.qApp.db
        table = db.table('rbSpeciality')
        cond = []
        if self.filter:
            cond.append(self.filter)
        return db.getDistinctIdList(table, table['id'].name(),
                              where=cond,
                              order=u'rbSpeciality.code ASC, rbSpeciality.name ASC')


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.getSpecialityList()
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()


    def getSpecialityList(self):
        specialityIdList = self.tblSpecialityList.selectedItemIdList()
        self.specialityIdList = specialityIdList
        self.close()


    def values(self):
        return self.specialityIdList


    def setValue(self, specialityIdList):
        self.specialityIdList = specialityIdList


class CSpecialityTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self._specialValues = []
        self.addColumn(CTextCol(u'Код',          ['code'], 5))
        self.addColumn(CTextCol(u'Наименование', ['name'], 40))
        self._fieldNames = ['rbSpeciality.id', 'rbSpeciality.code', 'rbSpeciality.name']
        self.setTable('rbSpeciality')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        table = db.table('rbSpeciality')
        loadFields = []
        loadFields.append(u'DISTINCT '+ u', '.join(self._fieldNames))
        self._table = table
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, fakeValues=self._specialValues)


def formatSpecialityIdList(specialityIdList):
    if not specialityIdList:
        return u''
    db = QtGui.qApp.db
    table = db.table('rbSpeciality')
    records = db.getRecordList(table, [table['name']], [table['id'].inlist(specialityIdList)])
    return u', '.join(forceString(record.value('name')) for record in records if forceString(record.value('name')))
