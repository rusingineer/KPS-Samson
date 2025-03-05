# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, SIGNAL, QDateTime

from library.ClientRecordProperties import CRecordProperties
from Registry.Utils                  import preFillingActionRecordMSI
from library.Utils            import copyFields, forceBool, forceRef, toVariant
from library.InDocTable       import CInDocTableView, CRecordListModel
from Events.Action            import CAction, CActionTypeCache
from F088.F088AddActions29Dialog import CF088AddActions30Dialog


class CF088AddActions29InDocTableView(CInDocTableView):
    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.__actAddRows = False


    def on_popupMenu_aboutToShow(self):
        model = self.model()
        rowCount = model.realRowCount() if hasattr(model, 'realRowCount') else model.rowCount()
        row = self.currentIndex().row()
        column = self.currentIndex().column()
        if self.__actAddRows:
           self.__actAddRows.setEnabled(True)
        if self._CInDocTableView__actUpRow:
            self._CInDocTableView__actUpRow.setEnabled(0<row<rowCount)
        if self._CInDocTableView__actDownRow:
            self._CInDocTableView__actDownRow.setEnabled(0<=row<rowCount-1)
        if self._CInDocTableView__actDuplicateCurrentRow:
            self._CInDocTableView__actDuplicateCurrentRow.setEnabled(0<=row<rowCount)
        if self._CInDocTableView__actAddFromReportRow:
            self._CInDocTableView__actAddFromReportRow.setEnabled(rowCount <= 0)
        if self._CInDocTableView__actDeleteRows:
            rows = self.getSelectedRows()
            canDeleteRow = bool(0<=row<rowCount)
            if canDeleteRow and self._CInDocTableView__delRowsChecker:
                canDeleteRow = self._CInDocTableView__delRowsChecker(rows)
            if len(rows) == 1 and rows[0] == row:
                self._CInDocTableView__actDeleteRows.setText(u'Удалить текущую строку')
            elif len(rows) == 1:
                self._CInDocTableView__actDeleteRows.setText(u'Удалить выделенную строку')
            else:
                self._CInDocTableView__actDeleteRows.setText(u'Удалить выделенные строки')
            if canDeleteRow and self._CInDocTableView__delRowsIsExposed:
                canDeleteRow = canDeleteRow and self._CInDocTableView__delRowsIsExposed(rows)
            self._CInDocTableView__actDeleteRows.setEnabled(canDeleteRow)
            if self._CInDocTableView__actDuplicateSelectRows:
                self._CInDocTableView__actDuplicateSelectRows.setEnabled(canDeleteRow)
        if self._CInDocTableView__actSelectAllRow:
            self._CInDocTableView__actSelectAllRow.setEnabled(0<=row<rowCount)
        if self._CInDocTableView__actSelectRowsByData:
            items = self.model().items()
            record, action = items[row] if items else (None, None)
            value = record.value(column) if record and row < len(items) else None
            self._CInDocTableView__actSelectRowsByData.setEnabled(forceBool(0<=row<rowCount and (value and value.isValid())))
        if self._CInDocTableView__actClearSelectionRow:
            self._CInDocTableView__actClearSelectionRow.setEnabled(0<=row<rowCount)
        if self._CInDocTableView__actCheckedAllRow:
            self._CInDocTableView__actCheckedAllRow.setEnabled(0<=row<rowCount)
        if self._CInDocTableView__actClearCheckedAllRow:
            self._CInDocTableView__actClearCheckedAllRow.setEnabled(0<=row<rowCount)
        if self._CInDocTableView__actRecordProperties:
            self._CInDocTableView__actRecordProperties.setEnabled(0<=row<rowCount)
        for act, checker in self._CInDocTableView__actionsWithCheckers:
            act.setEnabled(checker())
        self.emit(SIGNAL('popupMenuAboutToShow()'))


    def addPopupAddRow(self):
        if self._popupMenu is None:
            self.createPopupMenu()
        self.__actAddRows = QtGui.QAction(u'Добавление услуг', self)
        self.__actAddRows.setObjectName('actAddRows')
        self._popupMenu.addAction(self.__actAddRows)
        self.connect(self.__actAddRows, SIGNAL('triggered()'), self.on_addRows)


    def on_addRows(self):
        dialog = CF088AddActions30Dialog(self)
        try:
            dialog.setClientInfo(self.model().clientId, self.model().clientSex, self.model().clientAge)
            prevMKB = self.model().MKB
            MKBList = self.model().MKBList
            dialog.setMKBList(MKBList)
            dialog.setEventTypeId(self.model().eventTypeId)
            dialog.loadData()
            if dialog.exec_():
                addActions30IdList = dialog.values()
                basicAdditionalList = dialog.getBasicAdditional()
                currentRow = self.currentIndex().row() if self.currentIndex().isValid() else -1
                db = QtGui.qApp.db
                tableAction = db.table('Action')
                for actionTypeId in addActions30IdList:
                    actionType = CActionTypeCache.getById(actionTypeId)
                    defaultStatus = actionType.defaultStatus
                    defaultOrgId = actionType.defaultOrgId
                    defaultExecPersonId = actionType.defaultExecPersonId
                    newRecord = tableAction.newRecord()
                    newRecord.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                    newRecord.setValue('createPerson_id',toVariant(QtGui.qApp.userId))
                    newRecord.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
                    newRecord.setValue('modifyPerson_id',toVariant(QtGui.qApp.userId))
                    newRecord.setValue('actionType_id',  toVariant(actionTypeId))
                    newRecord.setValue('status',         toVariant(defaultStatus))
                    newRecord.setValue('begDate',        toVariant(QDateTime.currentDateTime()))
                    newRecord.setValue('directionDate',  toVariant(QDateTime.currentDateTime()))
                    newRecord.setValue('org_id',         toVariant(defaultOrgId if defaultOrgId else QtGui.qApp.currentOrgId()))
                    newRecord.setValue('setPerson_id',   toVariant(QtGui.qApp.userId))
                    newRecord.setValue('person_id',      toVariant(defaultExecPersonId))
                    newRecord.setValue('id',             toVariant(None))
                    newRecord.setValue('additional',     toVariant(basicAdditionalList.get(actionTypeId, 0)))
                    newRecord = preFillingActionRecordMSI(newRecord, actionTypeId)
                    if prevMKB:
                        newRecord.setValue('MKB', toVariant(prevMKB))
                    newAction = CAction(actionType=actionType, record=newRecord)
                    if newAction:
                        self.model().addRecord(newAction.getRecord(), newAction)
                if currentRow >= 0:
                    self.setCurrentRow(currentRow)
                elif len(self.model().items()) > 0:
                    self.setCurrentRow(0)
                self.model().reset()
        finally:
            dialog.deleteLater()


    def on_deleteRows(self):
        rows = self.getSelectedRows()
        for row in reversed(rows):
            self.model().removeRow(row)


    def on_selectRowsByData(self):
        items = self.model().items()
        currentRow = self.currentIndex().row()
        if currentRow < len(items):
            currentColumn = self.currentIndex().column()
            selectIndexes = self.selectedIndexes()
            selectRowList = []
            for selectIndex in selectIndexes:
                selectRow = selectIndex.row()
                if selectRow not in selectRowList:
                    selectRowList.append(selectRow)
            currentRecord, currentAction = items[currentRow]
            data = currentRecord.value(currentColumn)
            if data.isValid():
                for row, (item, action) in enumerate(items):
                    if (item.value(currentColumn) == data) and (row not in selectRowList):
                        self.selectRow(row)


    def on_duplicateCurrentRow(self):
        currentRow = self.currentIndex().row()
        items = self.model().items()
        if currentRow < len(items):
            newRecord = self.model().getEmptyRecord()
            currentRecord, currentAction = items[currentRow]
            copyFields(newRecord, currentRecord)
            newRecord.setValue(self.model()._idFieldName, toVariant(None))
            newAction = CAction(record=newRecord)
            for id in currentAction._propertiesById:
                property = newAction.getPropertyById(id)
                if property.type().valueType.isCopyable:
                    property.copy(currentAction._propertiesById[id])
            self.model().insertRecord(currentRow+1, newRecord, newAction if forceRef(newRecord.value('actionType_id')) else None)
            self.model().reset()


    def on_duplicateSelectRows(self):
        currentRow = self.currentIndex().row()
        items = self.model().items()
        if currentRow < len(items):
            selectIndexes = self.selectedIndexes()
            selectRowList = []
            for selectIndex in selectIndexes:
                selectRow = selectIndex.row()
                if selectRow not in selectRowList:
                    selectRowList.append(selectRow)
            selectRowList.sort()
            for row in selectRowList:
                newRecord = self.model().getEmptyRecord()
                currentRecord, currentAction = items[row]
                copyFields(newRecord, currentRecord)
                newRecord.setValue(self.model()._idFieldName, toVariant(None))
                newAction = CAction(record=newRecord)
                for id in currentAction._propertiesById:
                    property = newAction.getPropertyById(id)
                    if property.type().valueType.isCopyable:
                        property.copy(currentAction._propertiesById[id])
                items.append((newRecord, newAction if forceRef(newRecord.value('actionType_id')) else None))
            self.model().reset()


    def on_checkedAllRow(self):
        items = self.model().items()
        for row, (record, action) in items.items():
            record.setValue('include', toVariant(2))
            if action:
                recordAction = action.getRecord()
                recordAction.setValue('include', toVariant(2))
            items[row] = (record, action)


    def on_clearCheckedAllRow(self):
        items = self.model().items()
        for row, (record, action) in items.items():
            record.setValue('include', toVariant(0))
            items[row] = (record, action)


    def showRecordProperties(self):
        currentRow = self.currentIndex().row()
        items = self.model().items()
        if currentRow < len(items):
            (record, action) = items[currentRow]
            itemId = forceRef(record.value('id'))
        else:
            return
        table = self.model().table
        CRecordProperties(self, table, itemId).exec_()


    def on_sortByColumn(self, logicalIndex):
        currentIndex = self.currentIndex()
        currentItem = self.currentItem()
        model = self.model()
        if isinstance(model, CRecordListModel):
            header=self.horizontalHeader()
            if model.cols()[logicalIndex].sortable():
                if self._CInDocTableView__sortColumn == logicalIndex:
                    self._CInDocTableView__sortAscending = not self.__sortAscending
                else:
                    self._CInDocTableView__sortColumn = logicalIndex
                    self._CInDocTableView__sortAscending = True
                header.setSortIndicatorShown(True)
                header.setSortIndicator(self._CInDocTableView__sortColumn, Qt.AscendingOrder if self._CInDocTableView__sortAscending else Qt.DescendingOrder)
                model.sortData(logicalIndex, self._CInDocTableView__sortAscending)
            elif self._CInDocTableView__sortColumn is not None:
                header.setSortIndicator(self._CInDocTableView__sortColumn, Qt.AscendingOrder if self._CInDocTableView__sortAscending else Qt.DescendingOrder)
            else:
                header.setSortIndicatorShown(False)
            if currentItem:
                newRow = model.items().index(currentItem)
                self.setCurrentIndex(model.index(newRow, currentIndex.column()))
            else:
                self.setCurrentIndex(model.index(0, 0))
        else:
            header=self.horizontalHeader()
            if self._CInDocTableView__sortColumn == logicalIndex:
                self._CInDocTableView__sortAscending = not self._CInDocTableView__sortAscending
            else:
                self._CInDocTableView__sortColumn = logicalIndex
                self._CInDocTableView__sortAscending = True
            sortOrder = Qt.AscendingOrder if self._CInDocTableView__sortAscending else Qt.DescendingOrder
            header.setSortIndicatorShown(True)
            header.setSortIndicator(self._CInDocTableView__sortColumn, sortOrder)
            model.sort(logicalIndex, sortOrder)

