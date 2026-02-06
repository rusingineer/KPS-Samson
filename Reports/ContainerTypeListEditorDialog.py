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
from PyQt4.QtCore import pyqtSignature, Qt

from library.TableModel import CTableModel, CTextCol
from library.database   import CTableRecordCache

from Ui_ContainerTypeListEditor import Ui_ContainerTypeListEditor


class CContainerTypeListEditorDialog(QtGui.QDialog, Ui_ContainerTypeListEditor):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.tableModel = CContainerTypeTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblContainerTypeList.setModel(self.tableModel)
        self.tblContainerTypeList.setSelectionModel(self.tableSelectionModel)
        self.tblContainerTypeList.installEventFilter(self)
        self._parent = parent
        self.containerTypeIdList =  []
        self.tblContainerTypeList.model().setIdList(self.setContainerTypeList())


    def setContainerTypeList(self):
        db = QtGui.qApp.db
        table = db.table('rbContainerType')
        cond = []
        return db.getDistinctIdList(table, table['id'].name(),
                              where=cond,
                              order=u'rbContainerType.code ASC, rbContainerType.name ASC')


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.getContainerTypeList()
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()


    def getContainerTypeList(self):
        containerTypeIdList = self.tblContainerTypeList.selectedItemIdList()
        self.containerTypeIdList = containerTypeIdList
        self.close()


    def values(self):
        return self.containerTypeIdList


    def setValue(self, containerTypeIdList):
        self.containerTypeIdList = containerTypeIdList


class CContainerTypeTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self._specialValues = []
        self.addColumn(CTextCol(u'Код',          ['code'], 5))
        self.addColumn(CTextCol(u'Наименование', ['name'], 40))
        self._fieldNames = ['rbContainerType.id', 'rbContainerType.code', 'rbContainerType.name']
        self.setTable('rbContainerType')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        table = db.table('rbContainerType')
        loadFields = []
        loadFields.append(u'DISTINCT '+ u', '.join(self._fieldNames))
        self._table = table
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, fakeValues=self._specialValues)
