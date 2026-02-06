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

from library.TableModel       import CTableModel, CTextCol
from library.database         import CTableRecordCache

from Ui_DocumentLocationListDialog import Ui_DocumentLocationListDialog


class CDocumentLocationListDialog(QtGui.QDialog, Ui_DocumentLocationListDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.tableModel = CDocumentLocationTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblDocumentLocationList.setModel(self.tableModel)
        self.tblDocumentLocationList.setSelectionModel(self.tableSelectionModel)
        self.tblDocumentLocationList.installEventFilter(self)
        self._parent = parent
        self.documentLocationIdList = []
        self.tblDocumentLocationList.model().setIdList(self.setDocumentLocationList())


    def setDocumentLocationList(self):
        db = QtGui.qApp.db
        table = db.table('rbDocumentTypeLocation')
        cond = []
        return db.getDistinctIdList(table, table['id'].name(),
                              where=cond,
                              order=u'rbDocumentTypeLocation.code ASC, rbDocumentTypeLocation.name ASC')


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.getDocumentLocationList()
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()


    def getDocumentLocationList(self):
        documentLocationIdList = self.tblDocumentLocationList.selectedItemIdList()
        self.documentLocationIdList = documentLocationIdList
        self.close()


    def values(self):
        return self.documentLocationIdList


    def setValue(self, documentLocationIdList):
        self.documentLocationIdList = documentLocationIdList


class CDocumentLocationTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self._specialValues = []
        self.addColumn(CTextCol(u'Код',          ['code'], 5))
        self.addColumn(CTextCol(u'Наименование', ['name'], 40))
        self._fieldNames = ['rbDocumentTypeLocation.id', 'rbDocumentTypeLocation.code', 'rbDocumentTypeLocation.name']
        self.setTable('rbDocumentTypeLocation')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        table = db.table('rbDocumentTypeLocation')
        loadFields = []
        loadFields.append(u'DISTINCT '+ u', '.join(self._fieldNames))
        self._table = table
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, fakeValues=self._specialValues)
