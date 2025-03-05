# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
import json

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt, SIGNAL, QVariant

from library.Utils import CColsMovingFeature, forceInt, getPref, setPref, forceString, forceBool, forceRef
#from library.DialogBase import CDialogBase
from library.PreferencesMixin import CPreferencesMixin

from Events.NomenclatureExpense.NomenclatureExpenseDayDialog import CNomenclatureExpenseDayDialog
from Events.NomenclatureExpense.NomenclatureExpenseItemDelegate import CLocItemDelegate
from Events.NomenclatureExpense.Utils import NOTE_INDEX, SMNN_INDEX, SMNN_GRLSLF_INDEX, GROUPING_INDEX, NOMENCLATURE_INDEX

#from Events.NomenclatureExpense.Ui_ExtendAppointmentNomenclatureDialog import Ui_ExtendAppointmentNomenclatureDialog


class CNomenclatureExpenseView(QtGui.QTableView, CPreferencesMixin, CColsMovingFeature):
    __pyqtSignals__ = ('popupMenuAboutToShow()',
                       )

    def __init__(self, parent):
        QtGui.QTableView.__init__(self, parent)
        self.verticalHeader().hide()
        self.setItemDelegate(CLocItemDelegate(self))
        self._popupMenu = None
        self._actEditDayNomenclatureExpense = None
#        self._actExtendAppointmentNomenclature = None
        self._copiedDayData = {}
        self.hideSections = []
        self.groupedColumns = [(GROUPING_INDEX, NOMENCLATURE_INDEX)]
        header = self.horizontalHeader()
        header.sectionMoved.connect(self.onColumnMoved) 
    
    def onColumnMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        for col1, col2 in self.groupedColumns:
            header = self.horizontalHeader()
            if logicalIndex == col1:
                col2Index = header.visualIndex(col2)
                header.moveSection(col2Index, newVisualIndex + 1)
            elif logicalIndex == col2:
                col1Index = header.visualIndex(col1)
                header.moveSection(col1Index, newVisualIndex - 1)
                                           

    def keyPressEvent(self, keyEvent):
        key = keyEvent.key()
        if keyEvent.modifiers() == Qt.ControlModifier and key == Qt.Key_A:
            self.clearSelection()
            model = self.model()
            items = model.groups()
            for row, item in enumerate(items):
                self.selectRow(row)
            keyEvent.accept()
        elif key == Qt.Key_Delete or key == Qt.Key_Backspace:
            currentIndex = self.currentIndex()
            if currentIndex.isValid():
                currentRow = currentIndex.row()
                if 0 <= currentRow < len(self.model()._groups):
                    currentColumn = currentIndex.column()
                    if currentColumn in (SMNN_INDEX, SMNN_GRLSLF_INDEX):
                        isExistsDoneByIndex = self.model().existsDoneByIndex(currentIndex)
                        group = self.model()._groups[currentRow]
                        if group and not isExistsDoneByIndex:
                            newSmnnUUID = u''
                            oldSmnnUUID = self.model()._cellsSettings.getGroupSmnn(group)
                            if oldSmnnUUID != newSmnnUUID:
                                self.model()._cellsSettings.setGroupSmnn(group, newSmnnUUID)
                            newSmnnGrlsLfId = None
                            oldSmnnGrlsLfId = self.model()._cellsSettings.getGroupSmnnGrlsLf(group)
                            if oldSmnnGrlsLfId != newSmnnGrlsLfId:
                                self.model()._cellsSettings.setGroupSmnnGrlsLf(group, newSmnnGrlsLfId)
                            self.model().reset()
                            keyEvent.accept()
                    else:
                        QtGui.QTableView.keyPressEvent(self, keyEvent)
                else:
                    QtGui.QTableView.keyPressEvent(self, keyEvent)
            else:
                QtGui.QTableView.keyPressEvent(self, keyEvent)
        else:
            QtGui.QTableView.keyPressEvent(self, keyEvent)


    def setHideSections(self, hideSections=[]):
        oldHideSections = self.hideSections
        self.hideSections = hideSections
        header = self.horizontalHeader()
        for section in oldHideSections:
            if section not in self.hideSections:
                header.showSection(section)
        for section in self.hideSections:
            header.hideSection(section)


    def enableColsHide(self):
        header = self.horizontalHeader()
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self.headerMenu)
        self.__headerColsHidingAvailable = True

    
    def paintEvent(self, event):
        QtGui.QTableView.paintEvent(self, event)
        model = self.model()
        for row in range(model.rowCount()-1):
            index = model.index(row, GROUPING_INDEX)
            group = model._groups[row]
            painter = QtGui.QPainter(self.viewport())
            if group.groupingInfo and group.currentItem in group.groupingInfo and len(group.groupingInfo) > 1:
                rect = self.visualRect(index)
                painter.setPen(QtGui.QPen(QtGui.QColor(100, 100, 100), 3))
                Xcenter = rect.left() + rect.width() // 2
                Ycenter = rect.top() + rect.height() // 2
                painter.drawLine(Xcenter, Ycenter, Xcenter, rect.bottom())
                CornerRect = self.visualRect(model.index(row, GROUPING_INDEX))
                painter.drawLine(Xcenter, Ycenter, CornerRect.right(), Ycenter)
            elif group.groupingItem and not group.groupingInfo:   
                rect = self.visualRect(index)
                painter.setPen(QtGui.QPen(QtGui.QColor(100, 100, 100), 3))
                Xcenter = rect.left() + rect.width() // 2
                painter.drawLine(Xcenter, rect.top(), Xcenter, rect.bottom())
            painter.end()
    

    def headerColsHidingAvailable(self):
        try:
            return self.__headerColsHidingAvailable
        except AttributeError:
            return False


    def enableColsMove(self):
        self.horizontalHeader().setMovable(True)


    def headerMenu(self, pos):
        pos2 = QtGui.QCursor().pos()
        header = self.horizontalHeader()
        menu = QtGui.QMenu()
        checkedActions = []
        objectName = self.objectName()
        if objectName == u'tblNomenclatureExpense':
            firstCol = 0
            lastCol = 15
        elif objectName == u'tblNomenclatureExpenseDays':
            firstCol = 15
            lastCol = len(self.model().cols())
        for i, col in enumerate(self.model().cols()):
            if i >= firstCol and i < lastCol:
                action = QtGui.QAction(forceString(col.title()), self)
                action.setCheckable(True)
                action.setData(i)
                action.setEnabled(col.switchOff())
                if not header.isSectionHidden(i):
                    action.setChecked(True)
                    checkedActions.append(action)
                menu.addAction(action)
        if len(checkedActions) == 1:
            checkedActions[0].setEnabled(False)
        selectedItem = menu.exec_(pos2)
        if selectedItem:
            section = forceInt(selectedItem.data())
            if header.isSectionHidden(section) and section not in self.hideSections:
                header.showSection(section)
            else:
                header.hideSection(section)


    def contextMenuEvent(self, event): # event: QContextMenuEvent
        if self._popupMenu:
            self._popupMenu.exec_(event.globalPos())
            event.accept()
        else:
            event.ignore()


    def createPopupMenu(self):
        menu = QtGui.QMenu(self)
        menu.setObjectName('popupMenu')
        self.setPopupMenu(menu)
        return self._popupMenu


    def setPopupMenu(self, menu):
        if self._popupMenu:
            self.disconnect(self._popupMenu, SIGNAL('aboutToShow()'), self.on_popupMenu_aboutToShow)
        self._popupMenu = menu
        if menu:
            self.connect(menu, SIGNAL('aboutToShow()'), self.on_popupMenu_aboutToShow)


    def setNomenclatureExpensePopupMenu(self, menu):
        if self._popupMenu:
            self.disconnect(self._popupMenu, SIGNAL('aboutToShow()'), self.on_nomenclatureExpensePopupMenu_aboutToShow)
        self._popupMenu = menu
        if menu:
            self.connect(menu, SIGNAL('aboutToShow()'), self.on_nomenclatureExpensePopupMenu_aboutToShow)


    def on_popupMenu_aboutToShow(self):
        index = self.currentIndex()
        model = self.model()

        exists = model.existsByIndex(index)
        isDone = model.existsDoneByIndex(index)
        isAfterLastDone = not model.existsDoneAfterIndex(index)
        isAfterBegDate = model.isIndexAfterBegDate(index)

        editable = exists and not isDone
        canPaste = editable or (not exists and isAfterLastDone) and isAfterBegDate
        canceledRow = False
        items = model._groups[index.row()].items
        for i in range(len(items)):
            if forceInt(model._groups[index.row()].items[i].action._record.value('status')) == 3:
                canceledRow = True
                break
        editableDel = editable and not self.model().existsDoneActionItemExecToDateByIndex(index) and not self.model().existsDoneActionAfterIndex(index)
        self._actCopyDayNomenclatureExpense.setEnabled(False if canceledRow else exists and not self.model().isReadOnly())
        self._actDeleteDayNomenclatureExpense.setEnabled(False if canceledRow else editableDel and not self.model().isReadOnly())
        self._actEditDayNomenclatureExpense.setEnabled(True)
        self._actPasteDayNomenclatureExpense.setEnabled(False if canceledRow else canPaste and not self.model().isReadOnly())

        self.emit(SIGNAL('popupMenuAboutToShow()'))


    def isNomenclatureExpensePopupMenuEnabled(self):
        index = self.currentIndex()
        model = self.model()
        if self.model().isReadOnly():
            return False
        enabled = False
        if index.row() <= len(model._groups)-1:
            items = model._groups[index.row()].items
            for i in range(len(items)):
                if (forceInt(items[i].action._record.value('status')) != 2 and forceInt(items[i].action._record.value('status')) != 3 and not enabled):
                    enabled = True
                if forceInt(items[i].action._record.value('status')) == 3:
                    enabled = False
                    break
        return enabled


    def getSelectedDialogRows(self):
        selectedRows = []
        selectedIndexes = self.selectedIndexes()
        if selectedIndexes:
            model = self.model()
            for index in selectedIndexes:
                if index and index.isValid():
                    row = index.row()
                    if 0 <= row < len(model.groups()) and row not in selectedRows:
                        selectedRows.append(row)
        selectedRows.sort()
        return selectedRows


    def isNotBusiActions(self):
        rows = self.getSelectedDialogRows()
        for row in reversed(rows):
            if row <= len(self.model().groups()):
                headAciton = self.model().groups()[row].headItem.action
                if not forceRef(headAciton._record.value('id')):
                    return True
        return False


    def isBusiActions(self):
        rows = self.getSelectedDialogRows()
        for row in reversed(rows):
            if row <= len(self.model().groups()):
                headAciton = self.model().groups()[row].headItem.action
                if forceRef(headAciton._record.value('id')):
                    return True
        return False


    def on_nomenclatureExpensePopupMenu_aboutToShow(self):
        self._popupMenu.setEnabled(self.isNomenclatureExpensePopupMenuEnabled())
        index = self.currentIndex()
        if index and index.isValid():
            actions = self._popupMenu.actions()
            for action in actions:
                if action.text() == u'Показать все назначения подразделения':
                    action.setEnabled(index.column() == 0)
                elif action.text() == u'Удалить назначение':
                    action.setEnabled(not self.isBusiActions())
                elif action.text() == u'Отменить назначение':
                    action.setEnabled(not self.isNotBusiActions())
                elif action.text() == u'Добавить назначение в группу':
                    if index.row() <= len(self.model()._groups)-1:
                        group = self.model()._groups[index.row()]
                        enabled = group.groupingItem == group.currentItem or not group.groupingItem
                    else:
                        enabled = False
                    action.setEnabled(enabled)
        self.emit(SIGNAL('popupMenuAboutToShow()'))


    def addDeleteDays(self):
        if self._popupMenu is None:
            self.createPopupMenu()

        self._actDeleteDayNomenclatureExpense = QtGui.QAction(u'Удалить', self)
        self._popupMenu.addAction(self._actDeleteDayNomenclatureExpense)
        self.connect(self._actDeleteDayNomenclatureExpense, SIGNAL('triggered()'), self.on_deleteDays)


    def on_deleteDays(self):
        rowsColumns = {}
        for index in self.selectedIndexes():
            rowsColumns.setdefault(index.row(), []).append(index.column())

        model = self.model()
        for row, columns in rowsColumns.items():
            for column in columns:
                model.deleteItemsByIndex(model.index(row, column))
        model.emitAllDataChanged()


    def addEditDay(self):
        if self._popupMenu is None:
            self.createPopupMenu()

        self._actEditDayNomenclatureExpense = QtGui.QAction(u'Редактировать', self)
        self._popupMenu.addAction(self._actEditDayNomenclatureExpense)
        self.connect(self._actEditDayNomenclatureExpense, SIGNAL('triggered()'), self.on_editDayNomenclatureExpense)


    def addCopyDay(self):
        if self._popupMenu is None:
            self.createPopupMenu()

        self._actCopyDayNomenclatureExpense = QtGui.QAction(u'Копировать', self)
        self._popupMenu.addAction(self._actCopyDayNomenclatureExpense)
        self.connect(self._actCopyDayNomenclatureExpense, SIGNAL('triggered()'), self.on_copyDayNomenclatureExpense)


    def addPasteDay(self):
        if self._popupMenu is None:
            self.createPopupMenu()

        self._actPasteDayNomenclatureExpense = QtGui.QAction(u'Вставить', self)
        self._popupMenu.addAction(self._actPasteDayNomenclatureExpense)
        self.connect(self._actPasteDayNomenclatureExpense, SIGNAL('triggered()'), self.on_pasteDayNomenclatureExpense)


    def on_copyDayNomenclatureExpense(self):
        index = self.currentIndex()
        self._copiedDayData = {}
        if not index.isValid():
            return

        row = index.row()
        column = index.column()
        for subrow, subgroup in enumerate(self.model().groups()):
            if subgroup.groupingItem == self.model().groups()[row].groupingItem:
                if not (0 <= subrow < len(self.model()._groups)):
                    items = []

                if column in self.model().STATIC_HEADERS:
                    items = []

                date = QtCore.QDate(self.model()._date.year(), self.model()._date.month(), column - NOTE_INDEX)
                items = subgroup.getItemsByDate(date)
                self._copiedDayData[subrow] = items


    def on_pasteDayNomenclatureExpense(self):
        if not self._copiedDayData:
            return

        rowsColumns = {}
        for index in self.selectedIndexes():
            row = index.row()
            column = index.column()
            if row not in self._copiedDayData:
                continue
            for subrow, subgroup in enumerate(self.model().groups()):
                if subgroup.groupingItem == self.model().groups()[row].groupingItem:        
                    rowsColumns.setdefault(subrow, []).append(column)

        model = self.model()

        for row, items in self._copiedDayData.items():
            for column in rowsColumns[row]:
                if items:
                    model.setItemsForDayIndex(model.index(row, column), items)
        self.model().emitAllDataChanged()


    def on_editDayNomenclatureExpense(self):
        index = self.currentIndex()
        if not index.isValid():
            return
        row = index.row()
        items = self.model().getItemsByIndex(index)
        if not items:
            return
        canceled = self.model().isReadOnly()
        groupItems = self.model()._groups[row].items
        for item in range(len(groupItems)):
            if forceInt(groupItems[item].record.value('status')) == 3:
                canceled = True
                break
        canceled = canceled or self.model().existsDoneActionAfterIndex(index)
        dosageUnitName = self.model().getDosageUnitName(row)
        dialog = CNomenclatureExpenseDayDialog(self, items, dosageUnitName=dosageUnitName, ignoreTime = self.model()._ignoreTime)
        dialog.load(readOnly=canceled)
        planItems, doneItems = self.getDayStatistics(items)
        dialog.setDayStatistics(planItems, doneItems)
        dialog.setReadOnly(self.model().isReadOnly())
        dialog.protectWidgetFromEdit(self.model().isReadOnly())
        if dialog.exec_():
            items = dialog.itemsToSave()
            isApplyChangesCourseNextDays = dialog.getApplyChangesCourseNextDays()
            QtGui.qApp.preferences.appPrefs['NomenclatureExpenseIsApplyChangesCourseNextDays'] = forceBool(isApplyChangesCourseNextDays)
            isEditable = False
            for i in items:
                if not i.executedDatetime and not dialog.modelNomenclatureExpense._readOnly:
                    isEditable = True
                    break
            if isEditable:
                self.model().setItemsForDayIndex(index, items, isApplyChangesCourseNextDays=isApplyChangesCourseNextDays)
                self.model().reset()


    def getDayStatistics(self, items):
        planItems = 0
        if not items:
            return None
        planItems = len(items)

        not_done_items = []

        for item in items:
            executedDatetime = item.executedDatetime
            if executedDatetime is None:
                not_done_items.append(item)
            elif executedDatetime.isNull() or not executedDatetime.isValid():
                not_done_items.append(item)

        return planItems, planItems-len(not_done_items)


    def loadPreferences(self, preferences):
        model = self.model()
        self.horizontalHeader().setStretchLastSection(True)
        charWidth = self.fontMetrics().width('A0')/2
        cols = model.cols()
        i = 0
        for col in cols:
            width = forceInt(getPref(preferences, col.key, col.width*charWidth))
            if width:
                self.setColumnWidth(i, width)
            i += 1
        self.horizontalHeader().setStretchLastSection(True)
        state = getPref(preferences, 'headerState', QVariant()).toByteArray()
        if state:
            header = self.horizontalHeader()
            try:
                newState = json.loads(forceString(state))
                if not newState:
                    header.restoreState(state)
                    return
                state = newState
            except:
                header.restoreState(state)
                return
            maxVIndex = 0
            colsLen = len(model.cols()) if model else 0
            cols = model.cols() if model else []
            for i, col in enumerate(cols):
                name = forceString(col.title())
                curVIndex = header.visualIndex(i)
                if name in state:
                    vIndex = state[name][0]
                    isHidden = state[name][1]
                    if vIndex > maxVIndex:
                        maxVIndex = vIndex
                    if vIndex != curVIndex:
                        header.moveSection(curVIndex, vIndex)
                    if isHidden:
                        header.setSectionHidden(i, True)
                else:
                    header.moveSection(curVIndex, colsLen-1)


    def savePreferences(self):
        preferences = {}
        model = self.model()
        if not model:
            return
        cols = model.cols()
        i = 0
        for col in cols:
            width = self.columnWidth(i)
            setPref(preferences, col.key, QtCore.QVariant(width))
            i += 1
        header = self.horizontalHeader()
        if header.isMovable() or self.headerColsHidingAvailable():
            params = {}
            needSave = False
            for i, col in enumerate(self.model().cols()):
                if i != header.visualIndex(i)  or header.isSectionHidden(i):
                    needSave = True
                    break
            if needSave:
                for i, col in enumerate(self.model().cols()):
                    name = forceString(col.title())
                    params[name] = (header.visualIndex(i), header.isSectionHidden(i))
            setPref(preferences, 'headerState', QVariant(json.dumps(params)))
        return preferences


