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

import json
from inspect import isfunction

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, SIGNAL, QEventLoop, QMimeData, QVariant

from library.Utils import CColsMovingFeature, forceInt, forceString, getPref, setPref, toVariant, forceBool

from library.TableModel import CTableModel, CQueryModel
from library.MemTableModel import CMemTableModel
from library.PreferencesMixin import CPreferencesMixin

from library.ClientRecordProperties import CRecordProperties

from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CReportViewDialog


class CTableView(QtGui.QTableView, CPreferencesMixin, CColsMovingFeature):

    __pyqtSignals__ = ('popupMenuAboutToShow()',
                      )

    def __init__(self, parent):
        QtGui.QTableView.__init__(self, parent)
        self._popupMenu = None
        self._actDeleteRow = None
        self._actCopyCell = None
        self._actRecordProperties = None
        self.__reportHeader = u'List of records'
        self.__reportDescription = u''

        h = self.fontMetrics().height()
        self.verticalHeader().setDefaultSectionSize(3*h/2)
        self.verticalHeader().hide()
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.setTabKeyNavigation(False)
        self._order = None
        self._orderColumn = None
        self._isDesc = True


    def order(self):
        return self._order


    def setOrder(self, column):
        if column is not None:
            self._isDesc = not self._isDesc if self._orderColumn == column else False
            self._order = self.getOrder(column) + (' DESC' if self._isDesc else ' ASC')
            self._orderColumn = column
            self.horizontalHeader().setSortIndicator(column, Qt.DescendingOrder if self._isDesc else Qt.AscendingOrder)
        else:
            self._order = None
            self._orderColumn = None
            self._isDesc = True


    def getOrder(self, column):
        return self.model().getOrder(self.model().cols()[column].fields()[0], column)


    def createPopupMenu(self, actions=[]):
        self._popupMenu = QtGui.QMenu(self)
        self._popupMenu.setObjectName('popupMenu')
        self.connect(self._popupMenu, SIGNAL('aboutToShow()'), self.on_popupMenu_aboutToShow)
        if actions:
            self.addPopupActions(actions)
        return self._popupMenu


    def setPopupMenu(self, menu):
        self._popupMenu = menu


    def popupMenu(self):
        if not self._popupMenu:
            self.createPopupMenu()
        return self._popupMenu


    def addPopupSeparator(self):
        self.popupMenu().addSeparator()


    def addPopupAction(self, action):
        self.popupMenu().addAction(action)


    def addPopupActions(self, actions):
        menu = self.popupMenu()
        for action in actions:
            if isinstance(action, QtGui.QAction):
                menu.addAction(action)
            elif action == '-':
                menu.addSeparator()


    def addPopupDelRow(self):
        self._actDeleteRow = QtGui.QAction(u'Удалить запись', self)
        self._actDeleteRow.setObjectName('actDeleteRow')
        self.connect(self._actDeleteRow, SIGNAL('triggered()'), self.removeCurrentRow)
        self.addPopupAction(self._actDeleteRow)
#        self.setPopupMenu(self._popupMenu)


    def addPopupCopyCell(self):
        self._actCopyCell = QtGui.QAction(u'Копировать', self)
        self._actCopyCell.setObjectName('actCopyCell')
        self.connect(self._actCopyCell, SIGNAL('triggered()'), self.copyCurrentCell)
        self.addPopupAction(self._actCopyCell)


    def addPopupRecordProperies(self):
        self._actRecordProperties = QtGui.QAction(u'Свойства записи', self)
        self._actRecordProperties.setObjectName('actRecordProperties')
        self.connect(self._actRecordProperties, SIGNAL('triggered()'), self.showRecordProperties)
        self.addPopupAction(self._actRecordProperties)


    def setReportHeader(self, reportHeader):
        self.__reportHeader = reportHeader


    def reportHeader(self):
        return self.__reportHeader


    def setReportDescription(self, reportDescription):
        self.__reportDescription = reportDescription


    def reportDescription(self):
        return self.__reportDescription


    def on_popupMenu_aboutToShow(self):
        currentIndex = self.currentIndex()
        curentIndexIsValid = currentIndex.isValid()
        if self._actDeleteRow:
            self._actDeleteRow.setEnabled(curentIndexIsValid and self.canRemoveRow(currentIndex.row()))
        if self._actCopyCell:
            self._actCopyCell.setEnabled(curentIndexIsValid)
        if self._actRecordProperties:
            self._actRecordProperties.setEnabled(curentIndexIsValid)
        self.emit(SIGNAL('popupMenuAboutToShow()'))


    def setIdList(self, idList, itemId=None, realItemCount=None):
        if not itemId:
            itemId = self.currentItemId()
        curColumn = self.currentIndex().column()
        if not idList:
            selectionModel = self.selectionModel()
            if selectionModel:
                selectionModel.clear()
        self.model().setIdList(idList, realItemCount)
        if idList:
            self.setCurrentItemId(itemId, curColumn)


    def setCurrentRow(self, row, col=0):
        rowCount = self.model().rowCount()
        if col < 0:
            col = 0
        if row >= rowCount:
            row = rowCount-1
        if row >= 0:
            self.setCurrentIndex(self.model().index(row, col))
        elif rowCount>0:
            self.setCurrentIndex(self.model().index(0, col))
#        else:
#            self.setCurrentIndex(QtGui.QIndex())


    def currentRow(self):
        index = self.currentIndex()
        if index.isValid():
            return index.row()
        return None


    def setCurrentItemId(self, itemId, col=0):
        self.setCurrentRow(self.model().findItemIdIndex(itemId), col)


    def currentItemId(self):
        return self.itemId(self.currentIndex())


    def currentItem(self):
        if isinstance(self.model(), CQueryModel):
            index = self.currentIndex()
            record = self.model().recordByIndex(index)
        else:
            itemId = self.currentItemId()
            record = self.model().recordCache().get(itemId) if itemId else None
        return record


    def selectedRowList(self):
        return list(set([index.row() for index in self.selectedIndexes()]))


    def selectedItemIdList(self):
        itemIdList = self.model().idList()
        return [itemIdList[row] for row in self.selectedRowList()]


    def setSelectedRowList(self, rowList):
        model = self.model()
        selectionModel = self.selectionModel()
        for row in rowList:
            index = model.index(row, 0)
            selectionModel.select(index, QtGui.QItemSelectionModel.Select|QtGui.QItemSelectionModel.Rows)


    def setSelectedItemIdList(self, idList):
        self.setSelectedRowList((self.model().findItemIdIndex(itemId) for itemId in idList))


    def prepareCopy(self):
        cbfItemId = 'application/x-s11/itemid'
        currentItemId = self.currentItemId()
        strData=self.model().table().tableName+':'
        if currentItemId:
            strData += str(currentItemId)
        return {cbfItemId:strData}


    def copy(self):
        dataList = self.prepareCopy()
        mimeData = QMimeData()
        for format, data in dataList.iteritems():
            v = toVariant(data)
            mimeData.setData(format, v.toByteArray())
        QtGui.qApp.clipboard().setMimeData(mimeData)


    def itemId(self, index):
        if index.isValid():
            row = index.row()
            itemIdList = self.model().idList()
            if 0 <= row < len(itemIdList):
                return itemIdList[row]
        return None


    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter):
            event.ignore()
        elif key in (Qt.Key_Tab, Qt.Key_Backtab) and event.modifiers() & Qt.ControlModifier:
            event.ignore()
        elif event.matches(QtGui.QKeySequence.Copy):
            event.accept()
            self.copy()
        else:
            QtGui.QTableView.keyPressEvent(self, event)


    def contextMenuEvent(self, event): # event: QContextMenuEvent
        if self._popupMenu:
            self._popupMenu.exec_(event.globalPos())
            event.accept()
        else:
            event.ignore()


    def contentToHTML(self, showMask=None):
        model = self.model()
        cols = model.cols()
        if showMask is None:
            showMask = [None]*len(cols)
        _showMask = [ not self.isColumnHidden(iCol) if v is None else v
                      for iCol, v in enumerate(showMask)
                    ]
        QtGui.qApp.startProgressBar(model.rowCount())
        try:
#            report = CReportBase()
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            header = self.reportHeader()
            if Qt.mightBeRichText(header):
                cursor.insertHtml(header)
            else:
                cursor.insertText(header)
            cursor.insertBlock()
            cursor.setCharFormat(CReportBase.ReportBody)
            description = self.reportDescription()
            if Qt.mightBeRichText(description):
                cursor.insertHtml(description)
            else:
                cursor.insertText(description)
            cursor.insertBlock()

            colWidths = [ col._defaultWidth if _showMask[cols.index(col)] else 0 for col in cols ]
            colWidths.insert(0, 10)
            totalWidth = sum(colWidths)
            tableColumns = []
            for iCol, colWidth in enumerate(colWidths):
                widthInPercents = str(colWidths*3)
                if iCol == 0:
                    tableColumns.append((widthInPercents, [u'№'], CReportBase.AlignRight))
                else:
                    if not _showMask[iCol-1]:
                        continue
                    col = cols[iCol-1]
                    colAlingment = Qt.AlignHorizontal_Mask & forceInt(col.alignment())
                    format = QtGui.QTextBlockFormat()
                    format.setAlignment(Qt.AlignmentFlag(colAlingment))
                    tableColumns.append((widthInPercents, [forceString(col.title())], format))

            table = createTable(cursor, tableColumns)
            for iModelRow in xrange(model.rowCount()):
                QtGui.qApp.stepProgressBar()
                QtGui.qApp.processEvents(QEventLoop.ExcludeUserInputEvents)
                iTableRow = table.addRow()
                table.setText(iTableRow, 0, iModelRow+1)
                iTableCol = 1
                for iModelCol in xrange(len(cols)):
                    if not _showMask[iModelCol]:
                        continue
                    index = model.createIndex(iModelRow, iModelCol)
                    if type(model.data(index,Qt.DisplayRole)) != type(0):
                        if type(model.data(index,Qt.DisplayRole).toPyObject()) == type(None):
                            itemData = model.itemData(index)
                            if itemData:
                                key = itemData.keys()[0]
                                if forceBool(itemData[key]):
                                    text = u'x'
                                else:
                                    text = u''
                            else:
                                text = u''
                        else:
                            text = forceString(model.data(index,Qt.DisplayRole))
                    else:
                        text = forceString(model.data(index,Qt.DisplayRole))
                    table.setText(iTableRow, iTableCol, text)
                    iTableCol += 1
            return doc
        finally:
            QtGui.qApp.stopProgressBar()


    def printContent(self, showMask=None, orientation=None, pageFormat=None):
        html = self.contentToHTML(showMask)
        view = CReportViewDialog(self)
        if orientation:
            view.orientation = orientation
        if pageFormat:
            view.setPageFormat(pageFormat)
        view.setText(html)
        view.exec_()
        view.deleteLater()


    def canRemoveRow(self, row):
        return self.model().canRemoveRow(row)


    def confirmRemoveRow(self, row, multiple=False):
        return self.model().confirmRemoveRow(self, row, multiple)


    def removeCurrentRow(self):
        def removeCurrentRowInternal():
            index = self.currentIndex()
            if index.isValid() and self.confirmRemoveRow(self.currentIndex().row()):
                row = self.currentIndex().row()
                self.model().removeRow(row)
                self.setCurrentRow(row)
        QtGui.qApp.call(self, removeCurrentRowInternal)


    def removeSelectedRows(self):
        def removeSelectedRowsInternal():
            currentRow = self.currentIndex().row()
            newSelection = []
            deletedCount = 0
            rows = self.selectedRowList()
            rows.sort()
            for row in rows:
                actualRow = row-deletedCount
                self.setCurrentRow(actualRow)
                confirm = self.confirmRemoveRow(actualRow, len(rows)>1)
                if confirm is None:
                    newSelection.extend(x-deletedCount for x in rows if x>row)
                    break
                if confirm:
                    self.model().removeRow(actualRow)
                    deletedCount += 1
                    if currentRow>row:
                        currentRow-=1
                else:
                    newSelection.append(actualRow)
            if newSelection:
                self.setSelectedRowList(newSelection)
            else:
                self.setCurrentRow(currentRow)
        QtGui.qApp.call(self, removeSelectedRowsInternal)


    def copyCurrentCell(self):
        index = self.currentIndex()
        if index.isValid():
            carrier = QMimeData()
            dataAsText = self.model().data(index, Qt.DisplayRole)
            carrier.setText(dataAsText.toString() if dataAsText else '' )
            QtGui.qApp.clipboard().setMimeData(carrier)


    def showRecordProperties(self):
        table = self.model().table()
        itemId = self.currentItemId()
        CRecordProperties(self, table, itemId).exec_()


    def colKey(self, col):
        return unicode('width '+forceString(col.title()))


    def resizeTableHorizontalHeaderLoc(self):
        for column in range(self.horizontalHeader().count()):
            text = self.model().headerData(column, orientation=Qt.Horizontal, role=Qt.DisplayRole).toString()
            fm = QtGui.QFontMetrics(QtGui.QFont(text))
            width = fm.width(text)
            self.horizontalHeader().resizeSection(column, width)


    def loadPreferences(self, preferences):
        model = self.model()
        if isinstance(model, (CTableModel, CMemTableModel)):
            charWidth = self.fontMetrics().width('A0')/2
            cols = model.cols()
            i = 0
            for column, col in enumerate(cols):
                widthField = col.defaultWidth() * charWidth
                text = self.model().headerData(column, orientation=Qt.Horizontal, role=Qt.DisplayRole).toString()
                if text:
                    fm = QtGui.QFontMetrics(QtGui.QFont(text))
                    widthCol = fm.width(text)
                    if widthCol:
                        widthField = widthCol
                width = forceInt(getPref(preferences, self.colKey(col), widthField))
                if width:
                    self.setColumnWidth(i, width)
                i += 1
        else:
            if model:
                for i in xrange(model.columnCount()):
                    width = forceInt(getPref(preferences, 'col_'+str(i), None))
                    if width:
                        self.setColumnWidth(i, width)

        state = getPref(preferences, 'headerState', QVariant()).toByteArray()
        if state and hasattr(self.model(), 'cols'):
            header = self.horizontalHeader()
            try:
                state = json.loads(forceString(state))
            except:
                header.restoreState(state)
                return
            maxVIndex = 0
            try:
                colsLen = len(self.model().cols())
                for i, col in enumerate(self.model().cols()):
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
                        if self.headerColsHidingAvailable():
                            if hasattr(col, 'defaultHidden') and isfunction(col.defaultHidden):
                                header.setSectionHidden(i, col.defaultHidden())
                        header.moveSection(curVIndex, colsLen-1)
            except:
                return
        elif self.headerColsHidingAvailable() and hasattr(self.model(), 'cols'):
            try:
                cols = self.model().cols()
            except:
                return
            header = self.horizontalHeader()
            for i, col in enumerate(cols):
                if hasattr(col, 'defaultHidden') and isfunction(col.defaultHidden):
                    header.setSectionHidden(i, col.defaultHidden())


    def savePreferences(self):
        preferences = {}
        model = self.model()
        if isinstance(model, (CTableModel, CMemTableModel)):
            cols = model.cols()
            i = 0
            for col in cols:
                width = self.columnWidth(i)
                setPref(preferences, self.colKey(col), QVariant(width))
                i += 1
        else:
            if model:
                for i in xrange(model.columnCount()):
                    width = self.columnWidth(i)
                    setPref(preferences, 'col_'+str(i), QVariant(width))

        header = self.horizontalHeader()
        if self.model() and (header.isMovable() or self.headerColsHidingAvailable()):
            params = {}
            needSave = False
            for i, col in enumerate(self.model().cols()):
                if i != header.visualIndex(i) or header.isSectionHidden(i):
                    needSave = True
                    break
            if needSave:
                for i, col in enumerate(self.model().cols()):
                    name = forceString(col.title())
                    params[name] = (header.visualIndex(i), header.isSectionHidden(i))
            setPref(preferences, 'headerState', QVariant(json.dumps(params)))
        return preferences


class CExtendedSelectionTableView(CTableView):
    def __init__(self, parent):
        CTableView.__init__(self, parent)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)


class CCenterIconDelegate(QtGui.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        QtGui.QStyledItemDelegate.initStyleOption(self, option, index)
        option.decorationSize = option.rect.size()
