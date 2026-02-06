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

from library.database         import CTableRecordCache
from library.TableModel       import CTableModel, CTextCol

from Ui_HospitalBedProfileListDialog import Ui_HospitalBedProfileListDialog


class CHospitalBedProfileListDialog(QtGui.QDialog, Ui_HospitalBedProfileListDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.tableModel = CHospitalBedProfileTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblHospitalBedProfileList.setModel(self.tableModel)
        self.tblHospitalBedProfileList.setSelectionModel(self.tableSelectionModel)
        self.tblHospitalBedProfileList.installEventFilter(self)
        self._parent = parent
        self.hospitalBedProfileIdList = []
        self.tblHospitalBedProfileList.model().setIdList(self.setHospitalBedProfileList())


    def setHospitalBedProfileList(self):
        db = QtGui.qApp.db
        table = db.table('rbHospitalBedProfile')
        cond = []
        return db.getDistinctIdList(table, table['id'].name(),
                              where=cond,
                              order=u'rbHospitalBedProfile.code ASC, rbHospitalBedProfile.name ASC')


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.getHospitalBedProfileList()
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()


    def getHospitalBedProfileList(self):
        hospitalBedProfileIdList = self.tblHospitalBedProfileList.selectedItemIdList()
        self.hospitalBedProfileIdList = hospitalBedProfileIdList
        self.close()


    def values(self):
        return self.hospitalBedProfileIdList


    def setValue(self, hospitalBedProfileIdList):
        self.hospitalBedProfileIdList = hospitalBedProfileIdList


class CHospitalBedProfileTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self._specialValues = []
        self.addColumn(CTextCol(u'Код',          ['code'], 5))
        self.addColumn(CTextCol(u'Наименование', ['name'], 40))
        self._fieldNames = ['rbHospitalBedProfile.id', 'rbHospitalBedProfile.code', 'rbHospitalBedProfile.name']
        self.setTable('rbHospitalBedProfile')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        table = db.table('rbHospitalBedProfile')
        loadFields = []
        loadFields.append(u'DISTINCT '+ u', '.join(self._fieldNames))
        self._table = table
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, fakeValues=self._specialValues)
