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
from PyQt4.QtCore import Qt, pyqtSignature

from Orgs.Utils import getOrgStructureDescendants
from library.database         import CTableRecordCache
from library.TableModel       import CTableModel, CTextCol

from Ui_SelectPersonListDialog import Ui_SelectPersonListDialog


class CPersonListDialog(QtGui.QDialog, Ui_SelectPersonListDialog):
    def __init__(self, parent, orgStructureId=None):
        QtGui.QDialog.__init__(self, parent)
        self.tableModel = CPersonTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblSelectPersonList.setModel(self.tableModel)
        self.tblSelectPersonList.setSelectionModel(self.tableSelectionModel)
        self.tblSelectPersonList.installEventFilter(self)
        self._parent = parent
        self.orgStructureId = orgStructureId
        self.personIdList = []
        self.tblSelectPersonList.model().setIdList(self.setPersonList())


    def setPersonList(self):
        db = QtGui.qApp.db
        table = db.table('vrbPersonWithSpecialityAndOrgStr')
        cond = []
        if self.orgStructureId:
            cond.append(table['orgStructure_id'].inlist(getOrgStructureDescendants(self.orgStructureId)))
        return db.getDistinctIdList(table, table['id'].name(),
                              where=cond,
                              order=u'vrbPersonWithSpecialityAndOrgStr.code ASC, vrbPersonWithSpecialityAndOrgStr.name ASC')


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.getPersonList()
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()


    def getPersonList(self):
        personIdList = self.tblSelectPersonList.selectedItemIdList()
        self.personIdList = personIdList
        self.close()


    def values(self):
        return self.personIdList


    def setValue(self, personIdList):
        self.personIdList = personIdList


class CPersonTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self._specialValues = []
        self.addColumn(CTextCol(u'Код',          ['code'], 5))
        self.addColumn(CTextCol(u'Сотрудник', ['name'], 40))
        self._fieldNames = ['vrbPersonWithSpecialityAndOrgStr.id', 'vrbPersonWithSpecialityAndOrgStr.code', 'vrbPersonWithSpecialityAndOrgStr.name']
        self.setTable('vrbPersonWithSpecialityAndOrgStr')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        table = db.table('vrbPersonWithSpecialityAndOrgStr')
        loadFields = []
        loadFields.append(u'DISTINCT '+ u', '.join(self._fieldNames))
        self._table = table
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, fakeValues=self._specialValues)

