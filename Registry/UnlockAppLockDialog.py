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
from PyQt4.QtCore import QAbstractItemModel, QModelIndex, QVariant, Qt
from PyQt4.QtGui import QIntValidator

from Registry.Ui_UnlockAppLockDialog import Ui_UnlockAppLockDialog
from library.DialogBase import CDialogBase
from library.Utils import forceString, forceBool, forceInt, forceStringEx


class CUnlockAppLockDialog(Ui_UnlockAppLockDialog, CDialogBase):
    def __init__(self, parent, tableName, flatCode=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.show()
        self.tableName = tableName
        self.flatCode = flatCode
        self.addModels('CodeList', CCodeListModel(self))
        self.setModels(self.lvCode, self.modelCodeList, self.selectionModelCodeList)
        self.btnUnlockAll.setVisible(False)
        self.btnUnlock.clicked.connect(self.btnUnlock_Clicked)
        self.btnUnlockAll.clicked.connect(self.btnUnlockAll_Clicked)
        self.btnCancel.clicked.connect(self.close)
        self.edtCode.setValidator(QIntValidator(self))
        self.recordsIdList = []
        self.selectLockedCard()
        self.selectionModelCodeList.currentChanged.connect(self.currentChanged)

    def currentChanged(self, current, previous):
        rowData = forceString(self.modelCodeList.data(current, Qt.DisplayRole))
        self.edtCode.setText(rowData)

    def selectLockedCard(self):
        currentPersonId = QtGui.qApp.userId
        db = QtGui.qApp.db
        tableAppLockDetail = db.table('AppLock_Detail')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableAppLock = db.table('AppLock')
        tableQuery = tableAppLock
        tableQuery = tableQuery.leftJoin(tableAppLockDetail, tableAppLockDetail['master_id'].eq(tableAppLock['id']))
        cols = [tableAppLockDetail['recordId']]
        cond = [tableAppLock['person_id'].eq(currentPersonId), tableAppLockDetail['tableName'].eq(self.tableName)]
        if self.tableName == 'Action':
            tableQuery = tableQuery.leftJoin(tableAction, tableAction['id'].eq(tableAppLockDetail['recordId']))
            tableQuery = tableQuery.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            cond.append(tableActionType['flatCode'].eq('inspection_mse'))
            if self.flatCode:
                cond.append(tableActionType['flatCode'].eq(self.flatCode))

        recordList = db.getRecordList(tableQuery, cols, cond)
        lockedRecords = u'Заблокированы вашим пользователем:'
        self.modelCodeList.setList(recordList)
        for record in recordList:
            lockedRecord = forceString(record.value('recordId'))
            self.recordsIdList.append(lockedRecord)
            self.edtCode.setText(lockedRecord)
        if not forceBool(recordList):
            lockedRecords = u'Заблокированных вашим пользователем записей нет'
            self.edtCode.clear()
        if self.recordsIdList:
            self.btnUnlockAll.setVisible(True)
        else:
            self.btnUnlockAll.setVisible(False)

        self.lblLockedCardList.setText(lockedRecords)

    def btnUnlock_Clicked(self):
        code = forceString(self.edtCode.text())
        db = QtGui.qApp.db
        tableAppLockDetail = db.table('AppLock_Detail')
        tableAppLock = db.table('AppLock')
        cols = [tableAppLockDetail['recordId'], tableAppLockDetail['master_id']]
        if self.tableName == 'ProphylaxisPlanning':
            listId = []
            stmt = """SELECT p.id FROM ProphylaxisPlanning p 
             WHERE 
              p.id IN (SELECT recordId FROM AppLock_Detail WHERE tableName = "ProphylaxisPlanning") 
              AND p.client_id = (SELECT client_id FROM ProphylaxisPlanning p WHERE p.id = {0} LIMIT 1)""".format(code)
            query = db.query(stmt)
            while query.next():
                record = query.record()
                listId.append(forceString(record.value('id')))
            cond = [tableAppLockDetail['recordId'].inlist(listId), tableAppLockDetail['tableName'].eq(self.tableName)]
        else:
            cond = [tableAppLockDetail['recordId'].eq(code), tableAppLockDetail['tableName'].eq(self.tableName)]
        recordList = db.getRecordList(tableAppLockDetail, cols, cond)
        if recordList:
            masterIdList = []
            for record in recordList:
                masterIdList.append(forceString(record.value('master_id')))
            db.deleteRecord(tableAppLock, [tableAppLock['id'].inlist(masterIdList)])
            unlock = True
        else:
            unlock = False
        if self.tableName == 'Client':
            if unlock:
                text = u'Регистрационная карта {0} разблокирована!'.format(code)
            else:
                text = u'Регистрационная карта {0} не заблокирована!'.format(code)
        elif self.tableName == 'Event':
            if unlock:
                text = u'Обращение {0} разблокировано!'.format(code)
            else:
                text = u'Обращение {0} не заблокировано!'.format(code)
        elif self.tableName == 'TempInvalid':
            if unlock:
                text = u'Эпизод ВУТ {0} разблокирован!'.format(code)
            else:
                text = u'Эпизод ВУТ {0} не заблокирован!'.format(code)
        elif self.tableName == 'Action':
            if unlock:
                text = u'{} {} разблокировано!'.format(u'Направление на МСЭ' if self.flatCode == u'inspection_mse' else u'Карта беременной и родильницы', code)
            else:
                text = u'{} {} не заблокировано!'.format(u'Направление на МСЭ' if self.flatCode == u'inspection_mse' else u'Карта беременной и родильницы', code)
        elif self.tableName == 'ProphylaxisPlanning':
            if unlock:
                text = u'ККНД {0} разблокировано!'.format(code)
            else:
                text = u'ККНД {0} не заблокировано!'.format(code)
        else:
            text = ''
        messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Information, u'Внимание!', text, QtGui.QMessageBox.Ok)
        messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
        messageBox.exec_()
        self.selectLockedCard()

    def btnUnlockAll_Clicked(self):
        db = QtGui.qApp.db
        tableAppLockDetail = db.table('AppLock_Detail')
        tableAppLock = db.table('AppLock')
        cols = [tableAppLockDetail['master_id']]
        cond = [tableAppLockDetail['recordId'].inlist(self.recordsIdList),
                tableAppLockDetail['tableName'].eq(self.tableName)]
        recordList = db.getRecordList(tableAppLockDetail, cols, cond)
        if recordList:
            masterIdList = []
            for record in recordList:
                masterIdList.append(forceInt(record.value('master_id')))
            db.deleteRecord(tableAppLock, [tableAppLock['id'].inlist(masterIdList)])
            unlock = True
        else:
            unlock = False

        if self.tableName == 'Client':
            if unlock:
                text = u'Все регистрационные карты разблокированы!'
                self.recordsIdList = []
            else:
                text = u'Регистрационные карты не заблокированы!'
        elif self.tableName == 'Event':
            if unlock:
                text = u'Все обращения разблокированы!'
                self.recordsIdList = []
            else:
                text = u'Обращения не заблокированы!'
        elif self.tableName == 'TempInvalid':
            if unlock:
                text = u'Все эпизоды ВУТ разблокированы!'
                self.recordsIdList = []
            else:
                text = u'Эпизоды ВУТ не заблокированы!'
        elif self.tableName == 'Action':
            if unlock:
                text = u'Все {} разблокированы!'.format(u'направления на МСЭ' if self.flatCode == u'inspection_mse' else u'карты беременной и родильницы')
                self.recordsIdList = []
            else:
                text = u'{} не заблокированы!'.format(u'Направления на МСЭ' if self.flatCode == u'inspection_mse' else u'Карты беременной и родильницы')
        elif self.tableName == 'ProphylaxisPlanning':
            if unlock:
                text = u'Все ККДН разблокированы!'
                self.recordsIdList = []
            else:
                text = u'Планирования ККДН не заблокированы!'
        else:
            text = ''
        if self.recordsIdList:
            self.btnUnlockAll.setVisible(True)
        else:
            self.btnUnlockAll.setVisible(False)
        messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Information, u'Внимание!', text, QtGui.QMessageBox.Ok)
        messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
        messageBox.exec_()
        self.selectLockedCard()


class CCodeListModel(QAbstractItemModel):
    def __init__(self, parent):
        QAbstractItemModel.__init__(self, parent)
        self.rows = []
        self.recordList = {}

    def index(self, row, col, parent, *args, **kwargs):
        return self.createIndex(row, col, None)

    def parent(self, child):
        return QModelIndex()

    def setList(self, recordList):
        self.rows = []
        self.recordList = {}
        if recordList:
            for recordId in recordList:
                recId = forceInt(recordId.value('recordId'))
                self.recordList[recId] = forceString(recordId.value('recordId'))
            self.rows = sorted(self.recordList.keys(), key=lambda k: self.recordList[k])
        self.reset()

    def columnCount(self, parent, *args, **kwargs):
        return 1

    def rowCount(self, parent, *args, **kwargs):
        return len(self.rows)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            if col == 0:
                key = self.rows[row]
                return QVariant(self.recordList[key])
        return QVariant()

    def getCodeIndex(self, index):
        row = index.row()
        key = self.rows[row]
        return self.recordList[key]
