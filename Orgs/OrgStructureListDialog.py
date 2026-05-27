# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2019 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4                    import QtGui
from PyQt4.QtCore             import Qt, pyqtSignature

from library.database         import CTableRecordCache
from library.DialogBase       import CDialogBase
from library.TableModel       import CTableModel, CTextCol
from library.PreferencesMixin import CDialogPreferencesMixin

from Ui_OrgStructureListDialog import Ui_OrgStructureListDialog


class COrgStructureListDialog(CDialogBase, Ui_OrgStructureListDialog, CDialogPreferencesMixin):
    def __init__(self, parent, filter=None):
        CDialogBase.__init__(self, parent)
        self.tableModel = COrgStructureTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitle(u'Выберите Подразделения')
        self.tblOrgStructureList.setModel(self.tableModel)
        self.tblOrgStructureList.setSelectionModel(self.tableSelectionModel)
        self.tblOrgStructureList.installEventFilter(self)
        self._parent = parent
        self.orgStructureIdList = []
        self.filter = filter
        self.isOk = False
        self.tblOrgStructureList.model().setIdList(self.getOrgStructureIdList())
        self.loadDialogPreferences()


    def getOrgStructureIdList(self):
        db = QtGui.qApp.db
        tableOrgStructure = db.table('OrgStructure')
        cond = [tableOrgStructure['deleted'].eq(0)]
        if self.filter:
            cond.append(self.filter)
        return db.getDistinctIdList(tableOrgStructure, tableOrgStructure['id'].name(),
                              where=cond,
                              order=u'OrgStructure.code ASC, OrgStructure.name ASC')


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.isOk = True
            self.getOrgStructureList()
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.isOk = False
            self.close()


    def getOrgStructureList(self):
        self.orgStructureIdList = self.tblOrgStructureList.selectedItemIdList()


    def values(self):
        return self.orgStructureIdList


    def setValues(self, orgStructureIdList):
        self.orgStructureIdList = orgStructureIdList


    def saveData(self):
        return True


class COrgStructureTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self._specialValues = []
        self.addColumn(CTextCol(u'Код', ['code'], 5))
        self.addColumn(CTextCol(u'Наименование', ['name'], 40))
        self._fieldNames = ['OrgStructure.id', 'OrgStructure.code', 'OrgStructure.name']
        self.setTable('OrgStructure')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        loadFields = []
        loadFields.append(u'DISTINCT '+ u', '.join(self._fieldNames))
        self._table = db.table('OrgStructure')
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, fakeValues=self._specialValues)

