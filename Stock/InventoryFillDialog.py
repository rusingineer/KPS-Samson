#!/usr/bin/env python
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

from library.DialogBase import CDialogBase
from library.Utils      import forceStringEx, forceRef

from Stock.Ui_InventoryFillDialog import Ui_InventoryFillDialog


class CInventoryFillDialog(CDialogBase, Ui_InventoryFillDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.cmbClass.setTable('rbNomenclatureClass', True)
        self.cmbKind.setTable('rbNomenclatureKind', True)
        self.cmbType.setTable('rbNomenclatureType', True)
        self.filter = {}


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.setFilter()
            self.done(1)
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetFilter()


    def resetFilter(self):
        self.cmbClass.setFilter('')
        self.cmbKind.setFilter('')
        self.cmbType.setFilter('')
        self.cmbClass.setValue(None)
        self.cmbKind.setValue(None)
        self.cmbType.setValue(None)
        self.edtName.setText('')
        self.setFilter()


    def setFilter(self):
        self.filter = {}
        self.filter['classId'] = self.cmbClass.value()
        self.filter['kindId'] = self.cmbKind.value()
        self.filter['typeId'] = self.cmbType.value()
        self.filter['name'] = forceStringEx(self.edtName.text())


    def getFilter(self):
        return self.filter


    def setProxyIndex(self, widget, itemId):
        row = widget._model.searchId(itemId)
        if row == -1:
            widget.setCurrentIndex(-1)
        else:
            sourceIndex = widget._model.index(row, 0)
            proxyIndex = widget.proxyModel.mapFromSource(sourceIndex)
            return proxyIndex.row()
        return None


    @pyqtSignature('int')
    def on_cmbType_currentIndexChanged(self, index):
        if index:
            self.cmbKind.blockSignals(True)
            self.cmbClass.blockSignals(True)
            typeId = self.cmbType.value()
            if typeId:
                db = QtGui.qApp.db
                table = db.table('rbNomenclatureType')
                record = db.getRecordEx(table, [table['kind_id']], [table['id'].eq(typeId)])
                kindId = forceRef(record.value('kind_id')) if record else None
                if kindId:
                    self.cmbKind.setValue(kindId)
                    proxyIndex = self.setProxyIndex(self.cmbKind, kindId)
                    self.on_cmbKind_currentIndexChanged(proxyIndex)
                self.cmbType.blockSignals(True)
                self.cmbType.setValue(typeId)
                self.cmbType.blockSignals(False)
            self.cmbKind.blockSignals(False)
            self.cmbClass.blockSignals(False)


    @pyqtSignature('int')
    def on_cmbClass_currentIndexChanged(self, index):
        classId = self.cmbClass.value()
        kindId = self.cmbKind.value()
        typeId = self.cmbType.value()
        if index:
            if classId:
                db = QtGui.qApp.db
                table = db.table('rbNomenclatureKind')
                tableType = db.table('rbNomenclatureType')
                kindIdList = db.getDistinctIdList(table, [table['id']], [table['class_id'].eq(classId)])
                self.cmbKind.setFilter(table['class_id'].eq(classId))
                self.cmbType.setFilter(tableType['kind_id'].inlist(kindIdList) if kindIdList else '')
            else:
                self.cmbKind.setFilter('')
                self.cmbType.setFilter('')
        elif not classId:
            self.cmbKind.setFilter('')
            self.cmbType.setFilter('')
        if kindId:
            self.cmbKind.blockSignals(True)
            self.cmbKind.setValue(kindId)
            self.cmbKind.blockSignals(False)
        if typeId:
            self.cmbType.blockSignals(True)
            self.cmbType.setValue(typeId)
            self.cmbType.blockSignals(False)


    @pyqtSignature('int')
    def on_cmbKind_currentIndexChanged(self, index):
        if index:
            typeId = self.cmbType.value()
            self.cmbType.blockSignals(True)
            kindId = self.cmbKind.value()
            if kindId:
                db = QtGui.qApp.db
                table = db.table('rbNomenclatureType')
                tableKind = db.table('rbNomenclatureKind')
                record = db.getRecordEx(tableKind, [tableKind['class_id']], [tableKind['id'].eq(kindId)])
                classId = forceRef(record.value('class_id')) if record else None
                if classId:
                    self.cmbClass.setValue(classId)
                self.cmbType.setFilter(table['kind_id'].eq(kindId))
            else:
                self.cmbType.setFilter('')
            self.cmbType.setValue(typeId)
            self.cmbType.blockSignals(False)
        else:
            typeId = self.cmbType.value()
            self.cmbType.blockSignals(True)
            classId = self.cmbClass.value()
            if classId:
                db = QtGui.qApp.db
                table = db.table('rbNomenclatureKind')
                tableType = db.table('rbNomenclatureType')
                kindIdList = db.getDistinctIdList(table, [table['id']], [table['class_id'].eq(classId)])
                self.cmbType.setFilter(tableType['kind_id'].inlist(kindIdList) if kindIdList else '')
            else:
                self.cmbType.setFilter('')
            self.cmbType.setValue(typeId)
            self.cmbType.blockSignals(False)

