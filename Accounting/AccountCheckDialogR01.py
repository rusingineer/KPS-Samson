# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, SIGNAL, pyqtSlot, pyqtSignature, QObject

from Accounting.Utils import clearPayStatus, updateAccount
from Events.EditDispatcher import getEventFormClass
from library.DialogBase import CDialogBase
from library.InDocTable import CRecordListModel, CTextInDocTableCol, CInDocTableCol, CDateInDocTableCol
from library.Utils import forceString, forceRef, forceBool, formatNum1
from Registry.ClientEditDialog import CClientEditDialog
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CReportViewDialog
from Users.Rights import (urAdmin,
                          urAccessAccountInfo,
                          urAccessAccounting,
                          urAccessAccountingBudget,
                          urAccessAccountingCMI,
                          urAccessAccountingVMI,
                          urAccessAccountingCash,
                          urAccessAccountingTargeted,
                          )

from Ui_AccountCheckDialogR01 import Ui_AccountCheckDialog

accountantRightList = (urAdmin,
                       urAccessAccountInfo,
                       urAccessAccounting,
                       urAccessAccountingBudget,
                       urAccessAccountingCMI,
                       urAccessAccountingVMI,
                       urAccessAccountingCash,
                       urAccessAccountingTargeted
                       )


class CFLCModel(CRecordListModel):

    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.headerSortingCol = {}
        self.addCol(CTextInDocTableCol(u'Код ошибки', 'OSHIB', 6)).setReadOnly()
        self.addCol(CTextInDocTableCol(u'Имя поля', 'IM_POL', 12)).setReadOnly()
        self.addCol(CTextInDocTableCol(u'Баз. элемент', 'BAS_EL', 6)).setReadOnly()
        # self.addCol(CInDocTableCol(u'№ записи', 'N_ZAP', 6)).setReadOnly()
        # self.addCol(CInDocTableCol(u'Номер сводного счета', 'NSVOD', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Код пациента', 'clientId', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'ФИО', 'clientName', 6)).setReadOnly()
        self.addCol(CDateInDocTableCol(u'Дата рождения', 'birthDate', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Код случая', 'IDCASE', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Тип события', 'eventTypeName', 6)).setReadOnly()
        self.addCol(CDateInDocTableCol(u'Дата начала', 'setDate', 6)).setReadOnly()
        self.addCol(CDateInDocTableCol(u'Дата окончания', 'execDate', 6)).setReadOnly()
        self.addCol(CTextInDocTableCol(u'Ответственный', 'personName', 6)).setReadOnly()
        self.addCol(CTextInDocTableCol(u'Результат', 'result', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Номер записи', 'IDSERV', 6)).setReadOnly()
        self.addCol(CTextInDocTableCol(u'Комментарий', 'COMMENT', 6)).setReadOnly()
        self.addHiddenCol('isDone')


    def loadData(self, cond=None):
        db = QtGui.qApp.db
        tableFLC = db.table('soc_flc')
        # tableF012 = db.table('ro_F012')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableEventType = db.table('EventType')
        tablePerson = db.table('vrbPersonWithSpecialityAndOrgStr')
        tableResult = db.table('rbResult')
        table = tableFLC.leftJoin(tableEvent, tableEvent['id'].eq(tableFLC['IDCASE']))
        # table = table.leftJoin(tableF012, tableF012['code'].eq(tableFLC['OSHIB']))
        table = table.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        table = table.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        table = table.leftJoin(tablePerson, tablePerson['id'].eq(tableEvent['execPerson_id']))
        table = table.leftJoin(tableResult, tableResult['id'].eq(tableEvent['result_id']))
        cols = [tableFLC['id'],
                tableFLC['OSHIB'],
                # "CONCAT_WS(' | ', ro_F012.code, ro_F012.name) as error",
                tableFLC['IM_POL'],
                tableFLC['BAS_EL'],
                # tableFLC['N_ZAP'],
                # tableFLC['NSVOD'],
                tableClient['id'].alias('clientId'),
                tableFLC['IDCASE'],
                tableFLC['IDSERV'],
                tableFLC['COMMENT'],
                tableEventType['name'].alias('eventTypeName'),
                'formatClientName(Event.client_id) as clientName',
                tableClient['birthDate'],
                tableEvent['setDate'],
                tableEvent['execDate'],
                tablePerson['name'].alias('personName'),
                "CONCAT_WS(' | ', rbResult.code, rbResult.name) as result",
                tableFLC['isDone']
                ]
        self.setItems(QtGui.qApp.db.getRecordList(table, cols=cols, where=cond))
        for key in self.headerSortingCol:
            order = self.headerSortingCol.get(key, Qt.DescendingOrder)
            self.sort(key, order)


    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.BackgroundRole:
                record = self._items[row]
                if forceBool(record.value('isDone')):
                    return QtGui.QColor(Qt.green)
        return CRecordListModel.data(self, index, role)


    def sort(self, column, order=Qt.AscendingOrder):
        col = self._cols[column]
        self._items.sort(key=lambda item: col.toSortString(item.value(col.fieldName()), item), reverse=(order==Qt.DescendingOrder))
        self.emitRowsChanged(0, len(self._items) - 1)


class CAccountCheckDialogR01(CDialogBase, Ui_AccountCheckDialog):

    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.addObject('mnuFLC', QtGui.QMenu(self))
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actOpenEvent',  QtGui.QAction(u'Открыть первичный документ', self))
        self.addObject('actMarkIsDone', QtGui.QAction(u'Пометить ошибку отработанной', self))
        self.addObject('actMarkEventIsDone', QtGui.QAction(u'Пометить все ошибки по случаю отработанными', self))
        self.addObject('actDeleteEventFromAccount', QtGui.QAction(u'Удалить событие из реестра', self))
        self.mnuFLC.addAction(self.actEditClient)
        self.mnuFLC.addAction(self.actOpenEvent)
        self.mnuFLC.addAction(self.actMarkIsDone)
        self.mnuFLC.addAction(self.actMarkEventIsDone)
        self.mnuFLC.addAction(self.actDeleteEventFromAccount)
        self.setupUi(self)
        self.cmbEventType.setTable('EventType', True, 'deleted = 0')
        self.cmbEventType.setValue(None)
        self.chkSelectAllCheckTypes.setCheckState(Qt.Checked)
        self.addModels('FLC', CFLCModel(self))
        self.tblFLC.setModel(self.modelFLC)
        self.tblFLC.setSelectionModel(self.selectionModelFLC)
        self.tblFLC.enableColsHide()
        self.tblFLC.enableColsMove()
        QObject.connect(self.tblFLC.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setFLCSort)
        header = self.tblFLC.horizontalHeader()
        header.setSortIndicatorShown(True)
        self.tblFLC.show()
        self.selectionModelFLC.currentRowChanged.connect(self.FLCSelectionChanged)
        self.tblFLC.setPopupMenu(self.mnuFLC)
        self.chkSelectAllCheckTypes.stateChanged.connect(self.setAllCheckTypes)
        self.listCheckTypes.itemChanged.connect(self.listItemChanged)
        self.changeCheckTypes()
        self.on_btnApply_clicked()

    def setFLCSort(self, col):
        order = self.tblFLC.model().headerSortingCol.get(col, Qt.DescendingOrder)
        order = Qt.AscendingOrder if Qt.DescendingOrder == order else Qt.DescendingOrder
        self.tblFLC.model().headerSortingCol = {col: order}
        self.tblFLC.model().sort(col, order)

    def changeCheckTypes(self):
        self.listCheckTypes.clear()
        stmt = 'SELECT COMMENT, COUNT(id) AS cnt FROM soc_flc GROUP BY COMMENT ORDER BY cnt desc;'
        query = QtGui.qApp.db.query(stmt)
        while query.next():
            record = query.record()
            comment = forceString(record.value('COMMENT')) + u' (' + forceString(record.value('cnt')) + u')'
            item = QtGui.QListWidgetItem(comment)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.checkCode = forceString(record.value('COMMENT'))
            self.listCheckTypes.addItem(item)


    def listItemChanged(self, item):
        self.chkSelectAllCheckTypes.stateChanged.disconnect(self.setAllCheckTypes)

        allChecked = True
        allUnchecked = True
        for index in range(0, self.listCheckTypes.count()):
            itemState = self.listCheckTypes.item(index).checkState()
            if itemState == Qt.Unchecked:
                allChecked = False
            else:
                allUnchecked = False
        if allChecked:
            self.chkSelectAllCheckTypes.setCheckState(Qt.Checked)
        elif allUnchecked:
            self.chkSelectAllCheckTypes.setCheckState(Qt.Unchecked)
        else:
            self.chkSelectAllCheckTypes.setCheckState(Qt.PartiallyChecked)

        self.chkSelectAllCheckTypes.stateChanged.connect(self.setAllCheckTypes)

    def setAllCheckTypes(self, state):
        if state == Qt.PartiallyChecked:
            self.chkSelectAllCheckTypes.setCheckState(Qt.Checked)
            return
        self.listCheckTypes.itemChanged.disconnect(self.listItemChanged)
        for index in range(0, self.listCheckTypes.count()):
            item = self.listCheckTypes.item(index)
            item.setCheckState(state)
        self.listCheckTypes.itemChanged.connect(self.listItemChanged)


    @pyqtSlot()
    def on_btnApply_clicked(self):
        db = QtGui.qApp.db
        table = db.table('soc_flc')
        allChecked = True
        allUnchecked = True
        checkedList = []
        cond = []
        for index in range(0, self.listCheckTypes.count()):
            item = self.listCheckTypes.item(index)
            itemState = item.checkState()
            if itemState == Qt.Unchecked:
                allChecked = False
            else:
                checkedList.append(item.checkCode)
                allUnchecked = False
        if not all([allChecked, allUnchecked]):
            cond.append(table['COMMENT'].inlist(checkedList))
        elif allChecked:
            pass
        else:
            cond.append(False)
        if self.chkNotIsDone.isChecked():
            cond.append(table['isDone'].eq(False))
        eventTypeId = self.cmbEventType.value()
        if eventTypeId:
            tableEvent = db.table('Event')
            cond.append(tableEvent['eventType_id'].eq(eventTypeId))
        self.modelFLC.loadData(cond)
    
    
    @pyqtSlot()
    def on_btnPrintByOrgStructure_clicked(self):
        db = QtGui.qApp.db
        table = db.table('soc_flc')
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tablePerson = db.table('Person')
        tableOrgStructure = db.table('OrgStructure')
        table = table.leftJoin(tableEvent, tableEvent['id'].eq(table['IDCASE']))
        table = table.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        table = table.leftJoin(tablePerson, tablePerson['id'].eq(tableEvent['execPerson_id']))
        table = table.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))
        cols = [table['IDCASE'],
                tableEventType['name'].alias('eventType'),
                tableOrgStructure['name'].alias('orgStructure'),
                tablePerson['lastName'],
                table['COMMENT']
                ]
        cond = []
        orgStructureIdList = []
        if self.cmbOrgStructure.value():
            orgStructureIndex = self.cmbOrgStructure._model.index(
                self.cmbOrgStructure.currentIndex(), 0,
                self.cmbOrgStructure.rootModelIndex())
            treeItem = orgStructureIndex.internalPointer() if orgStructureIndex.isValid() else None
            orgStructureIdList = treeItem.getItemIdList() if treeItem else []
            cond.append(tableOrgStructure['id'].inlist(orgStructureIdList))
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Сводка по ошибкам в разрезе отделений')
        cursor.insertBlock()
        cursor.insertBlock()

        tableColumns = [
            ('7%',  [u'Номер карточки'], CReportBase.AlignLeft),
            ('29%', [u'Тип события'], CReportBase.AlignLeft),
            ('17%', [u'Отделение'], CReportBase.AlignLeft),
            ('7%', [u'Врач'], CReportBase.AlignLeft),
            ('40%', [u'Ошибка'], CReportBase.AlignLeft),
            ]

        tableDoc = createTable(cursor, tableColumns)
        recordList = db.getRecordList(table, cols, cond)
        for record in recordList:
            idcase = forceString(record.value('idcase'))
            eventType = forceString(record.value('eventType'))
            orgStructure = forceString(record.value('orgStructure'))
            lastName = forceString(record.value('lastName'))
            comment = forceString(record.value('COMMENT'))
            
            row = tableDoc.addRow()
            
            tableDoc.setText(row, 0, idcase)
            tableDoc.setText(row, 1, eventType)
            tableDoc.setText(row, 2, orgStructure)
            tableDoc.setText(row, 3, lastName)
            tableDoc.setText(row, 4, comment)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportBody)
        reportView = CReportViewDialog(self)
        reportView.setWindowTitle(u'Сводка в разрере отделений')
        reportView.setOrientation(QtGui.QPrinter.Landscape)
        reportView.setText(doc)
        reportView.exec_()


    def FLCSelectionChanged(self, current, previous):
        row = self.tblFLC.currentIndex().row()
        record = self.modelFLC.getRecordByRow(row)
        eventId = forceRef(record.value('IDCASE'))
        if eventId:
            db = QtGui.qApp.db
            table = db.table('soc_flc')
            recordList = db.getRecordList('soc_flc', 'COMMENT', table['IDCASE'].eq(eventId))
            self.textErrorDescription.setPlainText("\n".join(forceString(record.value('COMMENT')) for record in recordList))

    @pyqtSlot()
    def on_mnuFLC_aboutToShow(self):
        # isAccountant = QtGui.qApp.userHasAnyRight(accountantRightList)
        currentRow = self.tblFLC.currentIndex().row()
        # itemPresent = currentRow >= 0 and isAccountant
        self.actEditClient.setEnabled(currentRow >= 0)
        self.actOpenEvent.setEnabled(currentRow >= 0)


    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        row = self.tblFLC.currentIndex().row()
        record = self.modelFLC.getRecordByRow(row)
        clientId = forceRef(record.value('clientId'))
        if clientId:
            dialog = CClientEditDialog(self)
            try:
                dialog.load(clientId)
                dialog.exec_()
            finally:
                dialog.deleteLater()


    @pyqtSignature('')
    def on_actMarkIsDone_triggered(self):
        row = self.tblFLC.currentIndex().row()
        record = self.modelFLC.getRecordByRow(row)
        _id = forceRef(record.value('id'))
        db = QtGui.qApp.db
        db.query('update soc_flc set isDone = 1 where id = %s' % _id)
        record.setValue('isDone', 1)


    @pyqtSignature('')
    def on_actMarkEventIsDone_triggered(self):
        row = self.tblFLC.currentIndex().row()
        record = self.modelFLC.getRecordByRow(row)
        eventId = forceRef(record.value('IDCASE'))
        db = QtGui.qApp.db
        db.query('update soc_flc set isDone = 1 where IDCASE = %s' % eventId)
        for item in self.modelFLC._items:
            if item.value('IDCASE') == eventId:
                item.setValue('isDone', 1)


    @pyqtSignature('')
    def on_actDeleteEventFromAccount_triggered(self):
        selectedEventIdList = []
        for row in self.tblFLC.selectedRowList():
            record = self.modelFLC.getRecordByRow(row)
            eventId = forceRef(record.value('IDCASE'))
            selectedEventIdList.append(eventId)
        db = QtGui.qApp.db
        table = db.table('Account_Item')
        tableFLC = db.table('soc_flc')
        cond = [table['event_id'].inlist(selectedEventIdList), table['date'].isNull()]
        cols = [table['master_id'], table['id']]
        records = db.getRecordList(table, cols=cols, where=cond)
        accountMap = {}
        cnt = len(records)
        for record in records:
            accountId = forceRef(record.value('master_id'))
            accountItemId = forceRef(record.value('id'))
            accountMap.setdefault(accountId, []).append(accountItemId)

        message = u'Вы действительно хотите удалить %s реестра? ' % formatNum1(cnt, (u'запись', u'записи', u'записей'))
        if QtGui.QMessageBox.question(self,
                                      u'Внимание!',
                                      message,
                                      QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                      QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:

            QtGui.qApp.setWaitCursor()
            try:
                db.transaction()
                try:
                    for accountId in accountMap.keys():
                        itemIdList = accountMap[accountId]
                        clearPayStatus(accountId, itemIdList)
                        db.deleteRecordSimple(table, table['id'].inlist(itemIdList))
                        updateAccount(accountId)
                    cond = tableFLC['IDCASE'].inlist(selectedEventIdList)
                    db.query('update soc_flc set isDone = 1 where %s' % cond)
                    db.commit()
                    for item in self.modelFLC._items:
                        if item.value('IDCASE') in selectedEventIdList:
                            item.setValue('isDone', 1)
                except:
                    db.rollback()
                    QtGui.qApp.logCurrentException()
                    raise
            finally:
                QtGui.qApp.restoreOverrideCursor()


    @pyqtSlot()
    def on_actOpenEvent_triggered(self):
        row = self.tblFLC.currentIndex().row()
        record = self.modelFLC.getRecordByRow(row)
        eventId = forceRef(record.value('IDCASE'))
        if eventId:
            formClass = getEventFormClass(eventId)
            dialog = formClass(self)
            try:
                dialog.load(eventId)
                dialog.exec_()
            finally:
                dialog.deleteLater()
