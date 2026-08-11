# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import QVariant
from Events.ActionStatus import CActionStatus
from Orgs.PersonComboBoxEx import CPersonFindInDocTableCol
from library.DialogBase import CDialogBase
from library.InDocTable import CRecordListModel, CInDocTableCol, CDateInDocTableCol
from library.RecordLock import CRecordLockMixin
from library.Utils import forceString, toVariant, forceRef, forceDate, getPref, setPref, forceDateTime

from Events.Ui_SyncCSGWidget import Ui_SyncCSGDialog

class CSyncCSGDialog(CDialogBase, CRecordLockMixin, Ui_SyncCSGDialog):
    def __init__(self, eventEditor, parent = None):
        CDialogBase.__init__(self, parent)
        CRecordLockMixin.__init__(self)
        self.setupUi(self)
        self.addModels('Actions', CActionsModel(self))
        self.setModels(self.tblActions, self.modelActions, self.selectionModelActions)
        self.tblActions.horizontalHeader().setStretchLastSection(True)
        self.tblActions.verticalHeader().hide()
        self._eventEditor = eventEditor
        self._parent = parent
        self.recordList = []
        self._parent.cmbCSG.setItems()
        self.syncCSG()
        self.modelActions.setItems(self.recordList)
        # self.tblActions.resizeColumnsToContents()
        self.modelActions.calculateMax()
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'SyncCSG_tblActions', {})
        self.loadPreferences(preferences)
    
    
    def syncCSG(self):
        haveToCheck = False
        for record in self._eventEditor.tabMes.modelCSGs.items():
            if forceString(record.value('CSGCode')):
                haveToCheck = True
                break
        if not haveToCheck:
            return
        for (record, action) in self._eventEditor.tabMisc.modelAPActions._items:
            newRecord = self.newActionRecord()
            if action.getType().flatCode == 'moving'and forceDate(record.value('endDate')) and forceRef(record.value('status')) == CActionStatus.finished:
                newRecord.setValue('begDate', record.value('begDate'))
                newRecord.setValue('endDate', record.value('endDate'))
                newRecord.setValue('person_id', record.value('person_id'))
                if not self._parent.cmbCSG.mapActionToCSG.get(record, None) or not self._parent.cmbCSG.mapActionToCSG[record]:
                    id = forceRef(record.value('eventCSG_id'))
                    if id:
                        db = QtGui.qApp.db 
                        table = db.table('Event_CSG')
                        CSGCode = forceString(db.translate(table, 'id', record.value('eventCSG_id'), 'CSGCode'))
                        newRecord.setValue('CSGCode', CSGCode)
                        if not self._parent.cmbCSG.mapActionToCSG.get(record, None):
                            csgRecord = self._parent.cmbCSG.mapIdToCSGRecord.get(id, None)
                            self._parent.cmbCSG.mapActionToCSG[record] = csgRecord
                    elif haveToCheck and (u'мэса нет' in unicode(self._eventEditor.tabMes.cmbMes.currentText()).lower() or not bool(self._eventEditor.tabMes.cmbMes.currentIndex())):
                        self.getCSG(record, newRecord)
                else:
                    newRecord.setValue('CSGCode', self._parent.cmbCSG.mapActionToCSG[record].value('CSGCode'))
                if action.hasProperty(u'койка'):
                    newRecord.setValue('bed_id', action[u'койка'])
                else:
                    newRecord.setValue('bed_id', None)
                    
                if action.hasProperty(u'Отделение пребывания'):
                    newRecord.setValue('orgStruct_id', action[u'Отделение пребывания'])
                else:
                    newRecord.setValue('orgStruct_id', None)
                self.recordList.append(newRecord)
    
    
    def getCSG(self, record, newRecord):
        for rec in self._eventEditor.tabMes.modelCSGs.items():
            if forceString(rec.value('CSGCode')) and forceDate(rec.value('begDate')) <= forceDate(record.value('begDate')) \
                and forceDate(rec.value('endDate')) >= forceDate(record.value('endDate')):
                    if forceString(rec.value('CSGCode')) not in ('G26st36.009', 'G26st36.025', 'G26st36.026', 'G26st36.050', 'G26st36.051', 'G26st36.052', 'G26st36.053', 'G26st36.054'):
                        self._parent.cmbCSG.mapActionToCSG[record] = rec
                        newRecord.setValue('CSGCode', forceString(rec.value('CSGCode')))
                        break
        return newRecord
    
    
    def newActionRecord(self):
        newRecord = QtSql.QSqlRecord()
        newRecord.append(QtSql.QSqlField('begDate', QVariant.Date))
        newRecord.append(QtSql.QSqlField('endDate', QVariant.Date))
        newRecord.append(QtSql.QSqlField('person_id', QVariant.Int))
        newRecord.append(QtSql.QSqlField('CSGCode', QVariant.String))
        newRecord.append(QtSql.QSqlField('bed_id', QVariant.Int))
        newRecord.append(QtSql.QSqlField('orgStruct_id', QVariant.Int))
        newRecord.append(QtSql.QSqlField('maxCSG', QVariant.String))
        return newRecord
    
    def closeEvent(self, event):
        preferences = self.tblActions.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'SyncCSG_tblActions', preferences)
        self.reject()
                   

    def exec_(self):
        self.loadDialogPreferences()
        if not self.recordList:
            return False
        result = QtGui.QDialog.exec_(self)
        return result


class CActionsModel(CRecordListModel):

    class CBedColumn(CInDocTableCol):
        def __init__(self, title, field, defaultWidth):
            CInDocTableCol.__init__(self, title, field, defaultWidth)
            self.caches = {}

        def toString(self, value, record):
            bedId = forceRef(value)
            if bedId:
                bedName = self.caches.get(bedId, None)
                if bedName:
                    return toVariant(bedName)
                db = QtGui.qApp.db 
                table = db.table('OrgStructure_HospitalBed')
                bedName = forceString(db.translate(table, 'id', bedId, 'CONCAT(code, " | ", name)'))
                if bedName:
                    self.caches[bedId] = bedName
                    return toVariant(bedName)
            return QVariant()

    class CLocOrgStructurePresenceColumn(CInDocTableCol):
        def __init__(self, title, field, defaultWidth):
            CInDocTableCol.__init__(self, title, field, defaultWidth)
            self.caches = {}

        def toString(self, value, record):
            orgStructId = forceRef(value)
            if orgStructId:
                orgStructureName = self.caches.get(orgStructId, None)
                if orgStructureName:
                    return toVariant(orgStructureName)
                db = QtGui.qApp.db 
                table = db.table('OrgStructure')
                orgStructureName = forceString(db.translate(table, 'id', orgStructId, 'name'))
                if orgStructureName:
                    self.caches[orgStructId] = orgStructureName
                    return toVariant(orgStructureName)
            return QVariant()
        
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CDateInDocTableCol(u'Начато', 'begDate', 2)).setReadOnly()
        self.addCol(CDateInDocTableCol(u'Выполнено', 'endDate', 2)).setReadOnly()
        self.addCol(CActionsModel.CLocOrgStructurePresenceColumn(u'Отделение', 'orgStruct_id', 2)).setReadOnly()
        self.addCol(CActionsModel.CBedColumn(u'Койка', 'bed_id', 2)).setReadOnly()
        self.addCol(CPersonFindInDocTableCol(u'Врач', 'person_id', 2, 'vrbPersonWithSpecialityAndOrgStr', parent=parent)).setReadOnly()
        self.addCol(CInDocTableCol(u'КСГ', 'CSGCode', 2)).setReadOnly()
        self.addCol(CInDocTableCol(u'Основное для КСГ', 'maxCSG', 6)).setReadOnly()
    
    
    def calculateMax(self):
        maxEndDates = {}
        for record in self.items():
            code = forceString(record.value('CSGCode'))
            endDate = forceDateTime(record.value('endDate'))
            if not endDate:
                continue

            prev = maxEndDates.get(code)
            if prev is None or endDate > prev:
                maxEndDates[code] = endDate

        for record in self.items():
            code = forceString(record.value('CSGCode'))
            endDate = forceDateTime(record.value('endDate'))
            if code not in maxEndDates or not endDate:
                record.setValue('maxCSG', u'ДА')
                continue

            if endDate == maxEndDates[code] and forceString(record.value('CSGCode')):
                record.setValue('maxCSG', u'ДА')
            else:
                record.setValue('maxCSG', u'')
