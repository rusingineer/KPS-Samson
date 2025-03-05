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

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtSignature

from library.TableView import CTableView
from library.Utils import toVariant, forceString


class CMesListTableView(CTableView):
    def __init__(self, parent):
        CTableView.__init__(self, parent)
        self._actDublicateRow = None


    def addPopupDublicateRow(self):
        self._actDublicateRow = QtGui.QAction(u'Дублировать строку', self)
        self._actDublicateRow.setObjectName('actDublicateRow')
        self.connect(self._actDublicateRow, QtCore.SIGNAL('triggered()'), self.on_actDublicateRow_triggered)
        self.addPopupAction(self._actDublicateRow)


    def popupMenuAboutToShow(self):
        currentIndex = self.currentIndex()
        curentIndexIsValid = currentIndex.isValid()
        if self._actDublicateRow:
            self._actDublicateRow.setEnabled(curentIndexIsValid)
        CTableView(self).popupMenuAboutToShow()


    @pyqtSignature('')
    def on_actDublicateRow_triggered(self):
        def duplicateContent(tableName, currentId, newId):
            db = QtGui.qApp.db
            table = db.table(tableName)
            records = db.getRecordList(table, '*', table['master_id'].eq(currentId))
            for record in records:
                record.setValue('master_id', toVariant(newId))
                record.setNull('id')
                db.insertRecord(table, record)

        def duplicateCurrentInternal():
            currentIndex = self.currentIndex()
            currentItemId = self.itemId(currentIndex)
            if currentItemId:
                db = QtGui.qApp.db
                table = db.table('mes.MES')
                db.transaction()
                try:
                    record = db.getRecord(table, '*', currentItemId)
                    record.setValue('code', toVariant(forceString(record.value('code'))+u'_1'))
                    record.setNull('id')
                    newItemId = db.insertRecord(table, record)
                    for tableName in ['mes.MES_mkb', 'mes.MES_service', 'mes.MES_visit', 'mes.MES_equipment',
                                      'mes.MES_medicament', 'mes.MES_bloodPreparation', 'mes.MES_nutrient',
                                      'mes.MES_limitedBySexAge']:
                        duplicateContent(tableName, currentItemId, newItemId)
                    db.commit()
                except:
                    db.rollback()
                    QtGui.qApp.logCurrentException()
                    raise
                QtGui.qApp.mainWindow.updateMain()
        QtGui.qApp.call(self, duplicateCurrentInternal)

