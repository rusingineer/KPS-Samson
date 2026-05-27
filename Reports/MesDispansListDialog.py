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

from library.database   import CTableRecordCache
from library.TableModel import CTableModel, CTextCol
from library.Utils      import forceString

from Reports.Ui_MesDispansListEditor import Ui_MesDispansListEditor


class CMesDispansTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self._specialValues = []
        self.addColumn(CTextCol(u'Код',          ['code'], 5))
        self.addColumn(CTextCol(u'Наименование', ['name'], 40))
        self._fieldNames = ['mes.MES.id', 'mes.MES.code', 'mes.MES.name']
        self.setTable('mes.MES')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        loadFields = []
        db = QtGui.qApp.db
        self._table = db.forceTable(tableName)
        loadFields.append(u'DISTINCT '+ u', '.join(self._fieldNames))
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, fakeValues=self._specialValues)


class CMesDispansListDialog(QtGui.QDialog, Ui_MesDispansListEditor):
    def __init__(self, parent, filter=None):
        QtGui.QDialog.__init__(self, parent)
        self.tableModel = CMesDispansTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblMesDispansList.setModel(self.tableModel)
        self.tblMesDispansList.setSelectionModel(self.tableSelectionModel)
        self.tblMesDispansList.installEventFilter(self)
        self._parent = parent
        self.mesDispansIdList =  []
        self.filter = filter
        self.tblMesDispansList.model().setIdList(self.setMesDispansList())


    def setMesDispansList(self):
        db = QtGui.qApp.db
        tableMES = db.table('mes.MES')
        tableMESGroup = db.table('mes.mrbMESGroup')
        queryTable = tableMES.innerJoin(tableMESGroup, tableMESGroup['id'].eq(tableMES['group_id']))
        cond = [tableMES['deleted'].eq(0)]
        for filter in self.filter:
            cond.append(filter)
        return db.getDistinctIdList(queryTable, tableMES['id'].name(), where=cond, order=u'mes.MES.code ASC, mes.MES.name ASC')


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.getMesDispansIdList()
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()


    def getMesDispansIdList(self):
        mesDispansIdList = self.tblMesDispansList.selectedItemIdList()
        self.mesDispansIdList = mesDispansIdList
        self.close()


    def values(self):
        return self.mesDispansIdList


    def setValue(self, mesDispansIdList):
        self.mesDispansIdList = mesDispansIdList


def getMesDispansNameList(mesDispansIdList):
    nameList = []
    if mesDispansIdList:
        db = QtGui.qApp.db
        tableMES = db.table('mes.MES')
        records = db.getRecordList(tableMES, [tableMES['code'], tableMES['name']], [tableMES['deleted'].eq(0), tableMES['id'].inlist(mesDispansIdList)])
        for record in records:
            nameList.append(forceString(record.value('code')) + u' - ' + forceString(record.value('name')))
    return nameList


def getMesDispansList(obj, filter):
    mesDispansIdList = []
    nameList = []
    dialog = CMesDispansListDialog(obj, filter)
    if dialog.exec_():
        mesDispansIdList = dialog.values()
        nameList = getMesDispansNameList(mesDispansIdList)
    return mesDispansIdList, nameList

