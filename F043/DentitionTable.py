# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2015 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore  import Qt, QAbstractTableModel, QChar, QDateTime, QObject, QString, QVariant, SIGNAL

from library.StrComboBox import CStrComboBox
from library.TableView   import CTableView
from library.Utils       import forceDateTime, forceInt, forceRef, forceString, forceStringEx, formatNameInt, toVariant, trim

from Events.Action       import CAction
from Reports.ReportBase  import CReportBase, createTable
from Reports.ReportView  import CReportViewDialog

from F043.TeethMultiChangeEditor import CTeethMultiChangeEditor



class CClientDentitionHistoryTableView(CTableView):
    def __init__(self, parent):
        CTableView.__init__(self, parent)
        self.printRowShift = 1
        self.createCopyPasteActions()
        self.colorStatus = [Qt.white, Qt.lightGray, Qt.darkYellow, Qt.cyan, Qt.blue, Qt.green, Qt.darkGreen, Qt.magenta, Qt.yellow, Qt.red]


    def createCopyPasteActions(self):
        self._actPrintHistory = QtGui.QAction(u'Распечатать историю', self)
        self.addPopupAction(self._actPrintHistory)
        self.connect(self._actPrintHistory, SIGNAL('triggered()'), self.printHistory)

        self._actSelectedAll = QtGui.QAction(u'Выбрать все', self)
        self.addPopupAction(self._actSelectedAll)
        self.connect(self._actSelectedAll, SIGNAL('triggered()'), self.selectedAll)

        self._actDeselectedAll = QtGui.QAction(u'Отменить выбор', self)
        self.addPopupAction(self._actDeselectedAll)
        self.connect(self._actDeselectedAll, SIGNAL('triggered()'), self.deselectedAll)


    def getLastDentitionTeeth(self, items):
#        lastItemByDate = items[0]
        return self.getSimpleTeeth()


    def getLastParadentiumTeeth(self, items):
        return self.getSimpleTeeth()


    def getSimpleTeeth(self):
        return ['8', '7', '6', '5', '4', '3', '2', '1', '1', '2', '3', '4', '5', '6', '7', '8']


    def getParadentiumValues(self, action, teethRows, teethColumns=range(16)):
        teethValuesTop = []
        teethValuesLower = []
        for row in teethRows:
            if row <= 4:
                for column in teethColumns:
                    propertyName = CParodentiumModel.getPropertyName(row, column)
                    property     = action.getProperty(propertyName)
                    value        = property.getText()
                    teethValuesTop.append(value)
            elif row >= 5:
                for column in teethColumns:
                    propertyName = CParodentiumModel.getPropertyName(row, column)
                    property     = action.getProperty(propertyName)
                    value        = property.getText()
                    teethValuesLower.append(value)
        return teethValuesTop, teethValuesLower



    def getParadentiumTeethValues(self, action):
        teethKlinDefTop, teethKlinDefLower     = self.getParadentiumValues(action, [0, 9])
        teethRecessionTop, teethRecessionLower = self.getParadentiumValues(action, [1, 8])
        teethMobilityTop, teethMobilityLower   = self.getParadentiumValues(action, [2, 7])
        teethPocketTop, teethPocketLower       = self.getParadentiumValues(action, [3, 6])
        teethNumberTop, teethNumberLower       = self.getParadentiumValues(action, [4, 5])
        return teethNumberTop, teethNumberLower, teethKlinDefTop, teethKlinDefLower, teethRecessionTop, teethRecessionLower, teethMobilityTop, teethMobilityLower, teethPocketTop, teethPocketLower



    def getDentitionValues(self, action, teethRows, teethColumns=range(16)):
        teethValuesTop = []
        teethValuesLower = []
        for row in teethRows:
            if row <= 3:
                for column in teethColumns:
                    propertyName = CDentitionModel.getPropertyName(row, column)
                    property     = action.getProperty(propertyName)
                    value        = property.getText()
                    teethValuesTop.append(value)
            elif row >= 4:
                for column in teethColumns:
                    propertyName = CDentitionModel.getPropertyName(row, column)
                    property     = action.getProperty(propertyName)
                    value        = property.getText()
                    teethValuesLower.append(value)
        return teethValuesTop, teethValuesLower


    def getTeethValues(self, action):
#        teethNumber = self.getSimpleTeeth()
        teethStatusTop, teethStatusLower     = self.getDentitionValues(action, [0, 7])
        teethMobilityTop, teethMobilityLower = self.getDentitionValues(action, [1, 6])
        teethStateTop, teethStateLower       = self.getDentitionValues(action, [2, 5])
        teethNumberTop, teethNumberLower     = self.getDentitionValues(action, [3, 4])

        return teethNumberTop, teethNumberLower, teethStatusTop, teethStatusLower, teethStateTop, teethStateLower, teethMobilityTop, teethMobilityLower


    def getSubTitle(self):
        clientId = self.model().clientId()
        db = QtGui.qApp.db
        table  = db.table('Client')
        record = db.getRecord(table, '*', clientId)
        lastName  = forceString(record.value('lastName'))
        firstName = forceString(record.value('firstName'))
        patrName  = forceString(record.value('patrName'))
        fullName  = formatNameInt(lastName, firstName, patrName)
        birthDate = forceString(record.value('birthDate'))
        result = u'Пациент(код %d): %s, %s года рождения' % (clientId, fullName, birthDate)
        return result


    def getResult(self):
        rows = [u'Дата: %s'%forceString(QDateTime.currentDateTime())]
        eventEditor = self.model().eventEditor()
        personId = eventEditor.cmbPerson.value()
        if personId:
            personName = forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))
            rows.append(u'Ответственный: %s'%personName)
        return '\n'.join(rows)


    def printHistory(self):
        if self.model()._shownAction == CClientDentitionHistoryModel.dentitionIsShown:
            self.printDentitionHistory()
        elif self.model()._shownAction == CClientDentitionHistoryModel.paradentiumIsShown:
            self.printParadentiumHistory()


    def printParadentiumHistory(self):
        def isLastInBlock(valueIdx, valueRowIdx, valuesCount, valueRowsCount):
            return (valueIdx == (valuesCount-1)) and (valueRowIdx == (valueRowsCount-1))

        self.printRowShift = 1
        title = u'Параденталогическая история пациента'
        model = self.model()
        items = list(model.items())
        if not items:
            return
        items.reverse()

#        lastParadentiumTeeth = self.getLastParadentiumTeeth(items)
#        teethAdditional = [('4.8%', [u''],  CReportBase.AlignLeft) for col in lastParadentiumTeeth[0:16]]
        teethAdditional = [('4.8%', [u''],  CReportBase.AlignLeft)]*16
        tableColumns = [('3%', [u'№'], CReportBase.AlignLeft),
                        ('10%', [u'Дата'], CReportBase.AlignLeft),
                        ('10%', [u'Тип свойства'], CReportBase.AlignLeft)
                        ] + teethAdditional

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(title)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(self.getSubTitle())
        cursor.insertBlock()
        table = createTable(cursor, tableColumns)

        lenItems = len(model._resultDentitionHistoryItems)

        iRow = 0

        teethTypePrint = self.getTeethTypePrint()
        teethNumber = self.getSimpleTeeth()

        for row, dentition in enumerate(items):
            dentRecord, dentAction, dentActionId, dentEventId, dentIsChecked, personName = dentition
            paradentium = record, action, actionId, eventId, isChecked, personName = model._resultDentitionHistoryItems[row]
            if record and action and isChecked:
                teethNumberTop, teethNumberLower, teethKlinDefTop, teethKlinDefLower, teethRecessionTop, teethRecessionLower, teethMobilityTop, teethMobilityLower, teethPocketTop, teethPocketLower = self.getParadentiumTeethValues(action)

                valueRowList = (
                                (teethKlinDefTop, u'Клиновидный дефект'),
                                (teethRecessionTop, u'Рецессия'),
                                (teethMobilityTop, u'Подвижность'),
                                (teethPocketTop, u'Глубина кармана')
                               )


                if teethTypePrint == CPrintTypeSelector.internationalPrint:
                    valueRowList += ((teethNumberTop, u'Верх'), (teethNumberLower, u'Низ'))
                    condSettings = ((4, 5), 0, 9)
                elif teethTypePrint == CPrintTypeSelector.simplePrint:
                    valueRowList += ((teethNumber, u'Номер'),)
                    condSettings = ((4, ), 0, 8)
                else:
                    continue

                valueRowList += (
                                 (teethPocketLower, u'Глубина кармана'),
                                 (teethMobilityLower, u'Подвижность'),
                                 (teethRecessionLower, u'Рецессия'),
                                 (teethKlinDefLower, u'Клиновидный дефект')
                                )

                values = [
                          (record, 'begDate', u'Осмотр', paradentium, valueRowList)
                         ]

                i = table.addRow()
                begMergeRow = i
                for valueIdx, (record, dateField, paradentiumTypeName, paradentiumItem, valueRows) in enumerate(values):
                    table.setText(i, 0, iRow+1)
                    if record:
                        date = forceDateTime(record.value(dateField))
                        dateText = (forceString(date)+'\n'+paradentiumTypeName) if date.isValid() else u''
                        table.setText(i, 1, dateText)
                    for valueRowIdx, (valueRow, rowName) in enumerate(valueRows):
                        self.addParadentiumRowValues(rowName, table, valueRow, i, len(values), valueRowIdx, condSettings)
                        if not isLastInBlock(valueIdx, valueRowIdx, len(values), len(valueRows)):
                            i = table.addRow()
                table.mergeCells(begMergeRow, 0, len(valueRowList), 1)
                table.mergeCells(begMergeRow, 1, len(valueRowList), 1)
                if iRow+1 != lenItems:
                    i = table.addRow()
                    table.mergeCells(i, 0, 1, len(tableColumns))
                iRow += 1

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(self.getResult())
        cursor.insertBlock()

        viewDialog = CReportViewDialog(self)
        viewDialog.setWindowTitle(title)
        viewDialog.setRepeatButtonVisible()
        viewDialog.setText(doc)
        viewDialog.buttonBox.removeButton(viewDialog.buttonBox.button(QtGui.QDialogButtonBox.Retry))
        viewDialog.setWindowState(Qt.WindowMaximized)
        viewDialog.exec_()


    def getTeethTypePrint(self):
         dlg = CPrintTypeSelector(self)
         dlg.exec_()
         return dlg.value()


    def printDentitionHistory(self):
        def isLastInBlock(valueIdx, valueRowIdx, valuesCount, valueRowsCount):
            return (valueIdx == (valuesCount-1)) and (valueRowIdx == (valueRowsCount-1))

        self.printRowShift = 1
        title = u'Стоматологическая история пациента'
        model = self.model()
        items = list(model.items())
        items.reverse()
        if not items:
            return
        lastDentitionTeeth = self.getLastDentitionTeeth(items)
#        teethAdditional = [('4.8%', [u''],  CReportBase.AlignLeft) for col in lastDentitionTeeth[0:16]]
        teethAdditional = [('4.8%', [u''],  CReportBase.AlignLeft)]*16
        tableColumns = [('3%', [u'№'], CReportBase.AlignLeft),
                        ('10%', [u'Дата'], CReportBase.AlignLeft),
                        ('10%', [u'Тип свойства'], CReportBase.AlignLeft)
                        ] + teethAdditional

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(title)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(self.getSubTitle())
        cursor.insertBlock()
        table = createTable(cursor, tableColumns)

        lenItems = len(items)

        teethTypePrint = self.getTeethTypePrint()
        teethNumber = self.getSimpleTeeth()

        for iRow, dentition in enumerate(items):
            record, action, actionId, eventId, isChecked, personName = dentition
            if isChecked:
                teethNumberTop, teethNumberLower, teethStatusTop, teethStatusLower, teethStateTop, teethStateLower, teethMobilityTop, teethMobilityLower = self.getTeethValues(action)

                valueRowList = (
                                (teethStatusTop, u'Статус'),
                                (teethMobilityTop, u'Подвижность'),
                                (teethStateTop, u'Состояние')
                               )

                if teethTypePrint == CPrintTypeSelector.internationalPrint:
                    valueRowList += ((teethNumberTop, u'Верх'), (teethNumberLower, u'Низ'))
                    condSettings = ((3, 4), 0, 7)
                elif teethTypePrint == CPrintTypeSelector.simplePrint:
                    valueRowList += ((teethNumber, u'Номер'),)
                    condSettings = ((3, ), 0, 6)
                else:
                    continue
                valueRowList += (
                                 (teethStateLower, u'Состояние'),
                                 (teethMobilityLower, u'Подвижность'),
                                 (teethStatusLower, u'Статус')
                                )

                values = [
                          (record, 'begDate', u'Осмотр', dentition, valueRowList)
                         ]
                i = table.addRow()
                begMergeRow = i
                for valueIdx, (record, dateField, dentitionTypeName, dentitionItem, valueRows) in enumerate(values):
                    i, lastDentitionTeeth = self.checkDentitionEquals(lastDentitionTeeth, dentitionItem, table, i)
                    table.setText(i, 0, iRow+1)
                    if record:
                        date = forceDateTime(record.value(dateField))
                        dateText = (forceString(date)+'\n'+dentitionTypeName) if date.isValid() else u''
                        table.setText(i, 1, dateText)
                    for valueRowIdx, (valueRow, rowName) in enumerate(valueRows):
                        self.addRowValues(rowName, table, valueRow, i, len(values), valueRowIdx, condSettings)
                        if not isLastInBlock(valueIdx, valueRowIdx, len(values), len(valueRows)):
                            i = table.addRow()
                table.mergeCells(begMergeRow, 0, len(valueRowList), 1)
                table.mergeCells(begMergeRow, 1, len(valueRowList), 1)
                if iRow+1 != lenItems:
                    i = table.addRow()
                    table.mergeCells(i, 0, 1, len(tableColumns))

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(self.getResult())
        cursor.insertBlock()

        viewDialog = CReportViewDialog(self)
        viewDialog.setWindowTitle(title)
        viewDialog.setRepeatButtonVisible()
        viewDialog.setText(doc)
        viewDialog.buttonBox.removeButton(viewDialog.buttonBox.button(QtGui.QDialogButtonBox.Retry))
        viewDialog.setWindowState(Qt.WindowMaximized)
        viewDialog.exec_()


    def addRowValues(self, rowName, table, rowValues, i, countRow, valueRowIdx, condSettings):
        teethNumberRows, minRow, maxRow = condSettings

        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        if valueRowIdx in teethNumberRows:
            table.setText(i, 2, rowName, charFormat=boldChars)
        else:
            table.setText(i, 2, rowName)
        for idxVal, val in enumerate(rowValues):
            val = val if val else u''
            if valueRowIdx in teethNumberRows:
                table.setText(i, idxVal+3, val, charFormat=boldChars)
            elif valueRowIdx == minRow or valueRowIdx == maxRow:
                table.setText(i, idxVal+3, val, brushColor=self.getToothColor(val))
            else:
                table.setText(i, idxVal+3, val)



    def addParadentiumRowValues(self, rowName, table, rowValues, i, countRow, valueRowIdx, condSettings):
        teethNumberRows, minRow, maxRow = condSettings

        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        if valueRowIdx in teethNumberRows:
            table.setText(i, 2, rowName, charFormat=boldChars)
        else:
            table.setText(i, 2, rowName)
        for idxVal, val in enumerate(rowValues):
            val = val if val else u''
            if valueRowIdx in teethNumberRows:
                table.setText(i, idxVal+3, val, charFormat=boldChars)
            else:
                table.setText(i, idxVal+3, val)


    def getToothColor(self, val):
#        color = QtGui.QColor(255, 255, 255)
        try:
            val = int(val)
            return QVariant(QtGui.QColor(self.colorStatus[val]))
        except:
            pass
        return QtGui.QColor(255, 255, 255)


    def checkDentitionEquals(self, mainDentitionTeeth, dentitionItem, table, i):
        if dentitionItem:
            dentitionTeeth = self.getSimpleTeeth()
            if len(set(mainDentitionTeeth) ^ set(dentitionTeeth)) != 0:
                boldChars = QtGui.QTextCharFormat()
                boldChars.setFontWeight(QtGui.QFont.Bold)
                for teethValueIdx, teethValue in enumerate(dentitionTeeth):
                    table.setText(i, teethValueIdx+3, teethValue, charFormat=boldChars)
                i = table.addRow()
                mainDentitionTeeth = dentitionTeeth
                self.printRowShift += 1
        return i, mainDentitionTeeth


    def popupMenuAboutToShow(self):
#        CTableView.popupMenuAboutToShow(self)
        dataPresent = self.model().rowCount() > 0
        self._actPrintHistory.setEnabled(dataPresent)
        self._actSelectedAll.setEnabled(dataPresent)
        self._actDeselectedAll.setEnabled(dataPresent)


    def selectedAll(self):
        model = self.model()
        for row, (record, action, actionId, eventId, isChecked, personName) in enumerate(model._dentitionHistoryItems):
            if model._shownAction == CClientDentitionHistoryModel.dentitionIsShown:
                model._dentitionHistoryItems[row] = (record, action, actionId, eventId, 1, personName)
            elif model._shownAction == CClientDentitionHistoryModel.paradentiumIsShown:
                record, action, actionId, eventId, isChecked, personName = model.getParadentiumItem(row)
                model._resultDentitionHistoryItems[row] = (record, action, actionId, eventId, 1, personName)
        model.reset()


    def deselectedAll(self):
        model = self.model()
        for row, (record, action, actionId, eventId, isChecked, personName) in enumerate(model._dentitionHistoryItems):
            if model._shownAction == CClientDentitionHistoryModel.dentitionIsShown:
                model._dentitionHistoryItems[row] = (record, action, actionId, eventId, 0, personName)
            elif model._shownAction == CClientDentitionHistoryModel.paradentiumIsShown:
                record, action, actionId, eventId, isChecked, personName = model.getParadentiumItem(row)
                model._resultDentitionHistoryItems[row] = (record, action, actionId, eventId, 0, personName)
        model.reset()


class CDentitionTableView(QtGui.QTableView):
    def __init__(self, parent=None):
        QtGui.QTableView.__init__(self, parent)

        h = self.fontMetrics().height()
        self.verticalHeader().setDefaultSectionSize(3*h/2)
        self.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)

        w = self.geometry().width()
        self.horizontalHeader().setDefaultSectionSize(w/2)
        self.horizontalHeader().hide()

        self.setShowGrid(True)
        self.setTabKeyNavigation(True)

        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)

        self.itemDelegate = CItemDelegate(self)
        self.setItemDelegate(self.itemDelegate)

        self._popupMenu = None
        self._actCopyInspectionWithoutStatus = None
        self._actCopyInspection = None
        self._actClearInspectionStatus = None
        self._actClearInspection = None
        self._actTeethMultiChange = None

        self._actClearParodent = None
        self._actCopyParodent = None


    def popupMenu(self):
        if not self._popupMenu:
            self._popupMenu = QtGui.QMenu(self)
            self.connect(self._popupMenu, SIGNAL('aboutToShow()'), self.popupMenuAboutToShow)
        return self._popupMenu


    def addInspectionActions(self):
        self._actCopyInspection = QtGui.QAction(u'Копировать', self)
        self.connect(self._actCopyInspection, SIGNAL('triggered()'), self._onCopyInspection)
        self.popupMenu().addAction(self._actCopyInspection)

        self._actCopyInspectionWithoutStatus = QtGui.QAction(u'Копировать без статуса', self)
        self.connect(self._actCopyInspectionWithoutStatus, SIGNAL('triggered()'), self._onCopyInspectionWithoutStatus)
        self.popupMenu().addAction(self._actCopyInspectionWithoutStatus)

        self._actClearInspection = QtGui.QAction(u'Очистить', self)
        self.connect(self._actClearInspection, SIGNAL('triggered()'), self._onClearInspection)
        self.popupMenu().addAction(self._actClearInspection)

        self._actClearInspectionStatus = QtGui.QAction(u'Очистить статус', self)
        self.connect(self._actClearInspectionStatus, SIGNAL('triggered()'), self._onClearInspectionStatus)
        self.popupMenu().addAction(self._actClearInspectionStatus)

        self.popupMenu().addSeparator()

        self._actTeethMultiChange = QtGui.QAction(u'Изменить значения', self)
        self.connect(self._actTeethMultiChange, SIGNAL('triggered()'), self._onTeethMultiChange)
        self.popupMenu().addAction(self._actTeethMultiChange)


    def _onCopyInspection(self):
        self.model().copyInspection()


    def _onCopyInspectionWithoutStatus(self):
        self.model().copyInspectionWithoutStatus()


    def _onClearInspection(self):
        self.model().clearInspection(cleaningNames=[u'Статус', u'Подвижность', u'Состояние', u'Объективно', u'Слизистая', u'Примечание', u'Санация'])


    def _onClearInspectionStatus(self):
        self.model().clearInspection(cleaningNames=[u'Статус'])


    def _onTeethMultiChange(self):
        model = self.model()
        editorTypeList = {}
        mapForResult = {}
        for property in self.model().getTeethMultiChahgeProperties(self.selectionModel().selectedIndexes()):
            propertyType = property.type()
            editorType = propertyType.valueType.getEditorClass()
            domain = propertyType.valueType.domain
            key = (editorType, domain)
            map = mapForResult.setdefault(key, [])
            map.append(property)
            if self.selectionModel().selectedIndexes()[0].row() in [0, 7]:
                domainR = domain
                domainList = QString(domainR).remove(QChar('"'), Qt.CaseInsensitive).split(u',')
                for domainRow, domainKey in enumerate(domainList):
                    index = QString(domain).indexOf(domainKey, 0, Qt.CaseInsensitive)
                    domain = QString(domain).replace(index, 1, unicode(domainKey) + u' - ' + self.itemDelegate.getAddition(unicode(domainKey)))
            if key not in editorTypeList.keys():
                args = (model.action(), domain, self, model.clientId, model.eventTypeId())
                editorTypeList[key] = args
        if editorTypeList:
            teethMultiChangeEditor = CTeethMultiChangeEditor(self, editorTypeList)
            if teethMultiChangeEditor.exec_():
                values = teethMultiChangeEditor.values()
                for key, propertyList in mapForResult.items():
                    value = values[key]()
                    for property in propertyList:
                        property.setValue(value)
                model.emitAllDataChanged()


    def addParodentActions(self):
        self._actCopyParodent = QtGui.QAction(u'Копировать', self)
        self.connect(self._actCopyParodent, SIGNAL('triggered()'), self._onCopyParodent)
        self.popupMenu().addAction(self._actCopyParodent)

        self._actClearParodent = QtGui.QAction(u'Очистить', self)
        self.connect(self._actClearParodent, SIGNAL('triggered()'), self._onClearParodent)
        self.popupMenu().addAction(self._actClearParodent)


    def _onCopyParodent(self):
        self.model().copyParodent()


    def _onClearParodent(self):
        self.model().clearParodent()


    def popupMenuAboutToShow(self):
        isCurrentItem = self.isCurrentItem()

        if self._actCopyInspection:
            self._actCopyInspection.setEnabled(not isCurrentItem)

        if self._actCopyInspectionWithoutStatus:
            self._actCopyInspectionWithoutStatus.setEnabled(not isCurrentItem)

        if self._actClearInspection:
            self._actClearInspection.setEnabled(isCurrentItem)

        if self._actClearInspectionStatus:
            self._actClearInspectionStatus.setEnabled(isCurrentItem)

        if self._actTeethMultiChange:
            self._actTeethMultiChange.setEnabled(isCurrentItem and self.currentIndex().isValid())

        if self._actCopyParodent:
            self._actCopyParodent.setEnabled(not isCurrentItem)

        if self._actClearParodent:
            self._actClearParodent.setEnabled(isCurrentItem)


    def contextMenuEvent(self, event):
        self._popupMenu.exec_(event.globalPos())
        event.accept()


    def isCurrentItem(self):
        model = self.model()
        return model.isCurrentItem(model.currentHistoryRow())


class CItemDelegate(QtGui.QItemDelegate):
    class CLocComboBox(CStrComboBox):
        pass


    cacheStatus2Additional = {'0' : u'профилактика',
                              '1' : u'осмотр',
                              '2' : u'требуется санация',
                              '3' : u'санация',
                              '4' : u'лечение без пломбировки',
                              '5' : u'пломбировка',
                              '6' : u'осложнение',
                              '7' : u'длительное осложнение',
                              '8' : u'операция',
                              '9' : u'удаление' }


    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)


    def commit(self):
        editor = self.sender()
        self.emit(SIGNAL('commitData(QWidget *)'), editor)


    def commitAndCloseEditor(self):
        editor = self.sender()
        self.emit(SIGNAL('commitData(QWidget *)'), editor)
        self.emit(SIGNAL('closeEditor(QWidget *,QAbstractItemDelegate::EndEditHint)'), editor, QtGui.QAbstractItemDelegate.NoHint)


    def createEditor(self, parent, option, index):
        model = index.model()
        row = index.row()
        column = index.column()
        propertyType = model.getPropertyType(row, column)
        editor = propertyType.createEditor(model.action(), parent, model.clientId, model.eventTypeId())
        if isinstance(model,  CDentitionModel) and row in model.statusRows and isinstance(editor, QtGui.QComboBox):
            newEditor = CItemDelegate.CLocComboBox(parent)
            newItems = []
            for itemRow in xrange(editor.count()):
                itemText = unicode(editor.itemText(itemRow))
                newItems.append(u' - '.join([itemText, self.getAddition(itemText)]))
            newEditor.addItems(newItems)
            editor = newEditor

        self.connect(editor, SIGNAL('commit()'), self.commit)
        self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        return editor


    def setEditorData(self, editor, index):
        model = index.model()
        value = model.data(index, Qt.EditRole)
        row = index.row()
        if isinstance(model,  CDentitionModel) and row in model.statusRows and isinstance(editor, QtGui.QComboBox):
            itemText = forceString(value)
            value = QVariant(u' - '.join([itemText, self.getAddition(itemText)]))
        editor.setValue(value)
        editor.showPopup()


    def setModelData(self, editor, model, index):
        model = index.model()
        row = index.row()
        if isinstance(model,  CDentitionModel) and row in model.statusRows and isinstance(editor, QtGui.QComboBox):
            value = trim(editor.value().split('-')[0])
        else:
            value = editor.value()
        model.setData(index, toVariant(value))


    def getAddition(self, value):
        return CItemDelegate.cacheStatus2Additional.get(value, u'')


class CDentitionModel(QAbstractTableModel):
    statusRows = (0, 7)
    adultDefaultTeethValues = {
               3: ['18', '17', '16', '15', '14', '13', '12', '11', '21', '22', '23', '24', '25', '26', '27', '28'],
               4: ['48', '47', '46', '45', '44', '43', '42', '41', '31', '32', '33', '34', '35', '36', '37', '38']
                              }

    childDefaultTeethValues = {
##               3: ['58', '57', '56', '55', '54', '53', '52', '51', '61', '62', '63', '64', '65', '66', '67', '68'],
##               4: ['88', '87', '86', '85', '84', '83', '82', '81', '71', '72', '73', '74', '75', '76', '77', '78']
               3: ['',   '',   '',   '55', '54', '53', '52', '51', '61', '62', '63', '64', '65',   '',   '',   ''],
               4: ['',   '',   '',   '85', '84', '83', '82', '81', '71', '72', '73', '74', '75',   '',   '',   '']
                              }



    colorStatus = [Qt.white, Qt.lightGray, Qt.darkYellow, Qt.cyan, Qt.blue, Qt.green, Qt.darkGreen, Qt.magenta, Qt.yellow, Qt.red]

    teethRowTypes = {0 : u'Статус',
                     7 : u'Статус',
                     1 : u'Подвижность',
                     6 : u'Подвижность',
                     2 : u'Состояние',
                     5 : u'Состояние',
                     3 : u'Верх',
                     4 : u'Низ'
                     }

    wayJaw = {0 : u'Левая',
              1 : u'Правая'
              }

    jawHalfTypes =  {0 : u'Верхний',
                     1 : u'Верхний',
                     2 : u'Верхний',
                     3 : u'Верхний',
                     4 : u'Нижний',
                     5 : u'Нижний',
                     6 : u'Нижний',
                     7 : u'Нижний',
                     }

    def __init__(self, parent, clientDentitionHistoryModel):
        QAbstractTableModel.__init__(self, parent)
        self._actionRecord              = None
        self._action                    = None
        self._isExistsDentitionAction   = False
        self._isCurrentDentitionAction  = False
        self.clientId = None
        self._history = clientDentitionHistoryModel
        self._eventEditor = parent
        self.readOnly = False
        self.asAdult = False


    def setReadOnly(self, value):
        self.readOnly = value


    def eventTypeId(self):
        return self._eventEditor.eventTypeId


    def teethIsSet(self):
        if self.asAdult:
            defaultTeethValues = self.adultDefaultTeethValues
        else:
            defaultTeethValues = self.childDefaultTeethValues
        for row in defaultTeethValues.keys():
            for column in range(self.columnCount()):
                value = forceStringEx(self.data(self.index(row, column)))
                if not value:
                    defaultValue = self._defaultValue(self.asAdult, row, column)
                    self.setData(self.index(row, column), defaultValue)
        return True


    def getPenultimateItemAction(self):
        if len(self._history.items()) > 1:
            return self._history.items()[1][1] if self._history.items()[1] else None
        return None


    def copyInspection(self, skippingNames=[], action=None):
        if action is None:
            record, action, actionId, eventId, isChecked, currentPersonName = self._history.getItemByRow(self.currentHistoryRow())
        currentRecord, currentAction, currentActionId, currentEventId, currentIsChecked, currentPersonName = self._history.getItemByRow(self._history.currentDentitionItemRow())
        actionType = action.getType()
        for propertyTypeId, propertyType in actionType.getPropertiesById().items():
            isSkipable = any(propertyType.name.startswith(x) for x in skippingNames)
            if not isSkipable:
                property = action.getPropertyById(propertyTypeId)
                currentProperty = currentAction.getPropertyById(propertyTypeId)
                currentProperty.copy(property)


    def copyInspectionWithoutStatus(self, action=None):
        self.copyInspection(skippingNames=[u'Статус'], action=action)


    def clearInspection(self, cleaningNames=[u'Статус', u'Подвижность', u'Состояние']):
        currentRecord, currentAction, currentActionId, currentEventId, currentIsChecked, currentPersonName = self._history.getItemByRow(self._history.currentDentitionItemRow())
        actionType = currentAction.getType()
        for propertyTypeId, propertyType in actionType.getPropertiesById().items():
            isCleanable = True
            if cleaningNames:
                isCleanable = any(propertyType.name.startswith(x) for x in cleaningNames)
            if isCleanable:
                property = currentAction.getPropertyById(propertyTypeId)
                property.setValue(None)
        self.emitAllDataChanged()


    def clearInspectionStatus(self):
        self.clearInspection(cleaningNames=[u'Статус'])


    def isCurrentItem(self, row):
        return self._history.isCurrentDentitionAction(row)


    def currentHistoryRow(self):
        return self._history._currentRow


    def setIsExistsDentitionAction(self, isExistsDentitionAction):
        self._isExistsDentitionAction = isExistsDentitionAction


    def columnCount(self, index=None):
        return 16


    def rowCount(self, index=None):
        return len(CDentitionModel.teethRowTypes.keys())


    def getPropertyType(self, row, column):
        return self._getProperty(row, column).type()


    def setClientId(self, clientId):
        self.clientId = clientId


    def getClientId(self):
        return self.clientId


    def getTeethMultiChahgeProperties(self, indexList):
        return [self._getProperty(index.row(), index.column()) for index in indexList if index.row() not in (3, 4)]


    def _getProperty(self, row, column):
        # магия в том что у каждого ActionPropertyType зубной формулы
        # имя состоит (через точку) из типа свойства по отношению к формуле,
        # части челюсти и номера справа налево(1...16)
        # например «Подвижность.Верхний.1»
        # обращение к значениям свойст происходит через их названия.
        # по row определяется тип и часть челюсти, а номер column+1
        try:
            propertyName = self.getPropertyName(row, column)
            return self._action.getProperty(propertyName)
        except:
            return None


    @classmethod
    def getPropertyName(cls, row, column):
        propertyTeethRowType = cls.teethRowTypes[row]
        propertyJawHalfType  = cls.jawHalfTypes[row]
        propertyToothIdx     = unicode(column+1)
        propertyName = u'.'.join([propertyTeethRowType, propertyJawHalfType, propertyToothIdx])
        return propertyName


    def action(self):
        return self._action


    def actionRecord(self):
        return self._actionRecord


    def loadAction(self, actionRecord, action, isCurrentDentitionAction=False):
        self._isCurrentDentitionAction = isCurrentDentitionAction
        self._actionRecord = actionRecord
        self._action = action
        self.reset()


    def setIsCurrentDentitionAction(self, isCurrentDentitionAction=False):
        self._isCurrentDentitionAction = isCurrentDentitionAction


    def isCurrentDentitionAction(self):
        return self._isCurrentDentitionAction


    def setNullValues(self):
        self.loadAction(None, None, None)


    def flags(self, index):
#        row = index.row()
#        column = index.column()
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if not self._isCurrentDentitionAction:
            return Qt.ItemIsSelectable|Qt.ItemIsEnabled
        return Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Vertical:
                return QVariant(CDentitionModel.teethRowTypes.get(section, None))
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if not self._isExistsDentitionAction:
            return QVariant()
        if not self._action:
            return QVariant()
        row    = index.row()
        column = index.column()
        if role == Qt.DisplayRole:
            property = self._getProperty(row, column)
            if property:
                return toVariant(property.getText())
        elif role == Qt.ToolTipRole:
            if row in (2, 5):
                property = self._getProperty(row, column)
                if property:
                    return toVariant(property.getText())
        elif role == Qt.BackgroundRole:
            if row in (0, 7):
                property = self._getProperty(row, column)
                propertyValue = property.getValue() if property else None
                if propertyValue and propertyValue.isdigit():
                    return QVariant(QtGui.QColor(CDentitionModel.colorStatus[forceInt(propertyValue)]))
        elif role == Qt.EditRole:
            property = self._getProperty(row, column)
            if property:
                return toVariant(property.getValue())
        return QVariant()


    def _ensureTooth(self, row, column):
        # вспомогательная функция, устанавливает код зуба если до этого его небыло
        if row<=3:
            rows = (0, 1, 2)
            toothRow = 3
        else:
            rows = (5, 6, 7)
            toothRow = 4

        toothProperty = self._getProperty(toothRow, column)
        if toothProperty and not toothProperty.getValue():
            propertyValuePresent = False
            for row in rows:
                property = self._getProperty(row, column)
                if property and property.getValue():
                    propertyValuePresent = True
                    break
            if propertyValuePresent:
                toothCode = self.adultDefaultTeethValues[toothRow][column]
                toothProperty.setValue(toothCode)


    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        row = index.row()
        column = index.column()
        if role == Qt.EditRole:
            property = self._getProperty(row, column)
            propertyType = property.type() if property else None
            property.setValue(propertyType.convertQVariantToPyValue(value))
            if row <= 2:
                self._ensureTooth(row, column)
                begIndex = self.index(0, column)
                endIndex = self.index(3, column)
                self.emitDataChanged(begIndex, endIndex)
            elif row >= 5:
                self._ensureTooth(row, column)
                begIndex = self.index(4, column)
                endIndex = self.index(7, column)
                self.emitDataChanged(begIndex, endIndex)
            else:
                self.emitDataChanged(index, index)
            return True
        return False


    def emitAllDataChanged(self):
        begIndex = self.index(0, 0)
        endIndex = self.index(self.rowCount()-1, self.columnCount()-1)
        self.emitDataChanged(begIndex, endIndex)


    def emitDataChanged(self, begIndex, endIndex):
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), begIndex, endIndex)


    def setAdultDefaults(self, asAdult):
        self.asAdult = asAdult


    def setDefaults(self, asAdult):
        self.asAdult = asAdult
        rows = (3, 4)
        for column in xrange(16):
            for row in rows:
                defaultValue = self._defaultValue(self.asAdult, row, column)
                self.setData(self.index(row, column), defaultValue)


    def _defaultValue(self, asAdult, row, column):
        if asAdult:
            return self.adultDefaultTeethValues[row][column]
        else:
            return self.childDefaultTeethValues[row][column]


class CParodentiumTableView(CDentitionTableView):
    def __init__(self, parent=None):
        CDentitionTableView.__init__(self, parent)
        #self.createPopupMenu()

        h = self.fontMetrics().height()
        self.verticalHeader().setDefaultSectionSize(3*h/2)
        self.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)

        w = self.geometry().width()
        self.horizontalHeader().setDefaultSectionSize(w/2)
        self.horizontalHeader().hide()

        self.setShowGrid(True)
        self.setTabKeyNavigation(True)

        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)

        self.itemDelegate = CParodentiumItemDelegate(self)
        self.setItemDelegate(self.itemDelegate)


class CParodentiumItemDelegate(CItemDelegate):
    def __init__(self, parent):
        CItemDelegate.__init__(self, parent)


    def commit(self):
        editor = self.sender()
        self.emit(SIGNAL('commitData(QWidget *)'), editor)


    def commitAndCloseEditor(self):
        editor = self.sender()
        self.emit(SIGNAL('commitData(QWidget *)'), editor)
        self.emit(SIGNAL('closeEditor(QWidget *,QAbstractItemDelegate::EndEditHint)'), editor, QtGui.QAbstractItemDelegate.NoHint)


    def createEditor(self, parent, option, index):
        model = index.model()
        row = index.row()
        column = index.column()
        propertyType = model.getPropertyType(row, column)
        editor = propertyType.createEditor(model.action(), parent, model.clientId, model.eventTypeId())
        self.connect(editor, SIGNAL('commit()'), self.commit)
        self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        return editor


class CParodentiumModel(QAbstractTableModel):
    adultDefaultTeethValues = {
               4: ['18', '17', '16', '15', '14', '13', '12', '11', '21', '22', '23', '24', '25', '26', '27', '28'],
               5: ['48', '47', '46', '45', '44', '43', '42', '41', '31', '32', '33', '34', '35', '36', '37', '38']
                              }

    childDefaultTeethValues = {
               4: ['',   '',   '',   '55', '54', '53', '52', '51', '61', '62', '63', '64', '65',   '',   '',   ''],
               5: ['',   '',   '',   '85', '84', '83', '82', '81', '71', '72', '73', '74', '75',   '',   '',   '']
                              }

    colorStatus = [Qt.white, Qt.lightGray, Qt.darkYellow, Qt.cyan, Qt.blue, Qt.green, Qt.darkGreen, Qt.magenta, Qt.yellow, Qt.red]
    teethRowTypesHeader = { 0 : u'Клиновидный дефект',
                            1 : u'Рецессия',
                            2 : u'Подвижность',
                            3 : u'Глубина кармана',
                            4 : u'Верх',
                            5 : u'Низ',
                            6 : u'Глубина кармана',
                            7 : u'Подвижность',
                            8 : u'Рецессия',
                            9 : u'Клиновидный дефект',
                          }

    teethRowTypes = {0 : u'Клиновидный',
                     1 : u'Рецессия',
                     2 : u'Подвижность',
                     3 : u'Глубина',
                     4 : u'Верх',
                     5 : u'Низ',
                     6 : u'Глубина',
                     7 : u'Подвижность',
                     8 : u'Рецессия',
                     9 : u'Клиновидный',
                     }

    jawHalfTypes =  {0 : u'Верхний',
                     1 : u'Верхний',
                     2 : u'Верхний',
                     3 : u'Верхний',
                     4 : u'Верхний',
                     5 : u'Нижний',
                     6 : u'Нижний',
                     7 : u'Нижний',
                     8 : u'Нижний',
                     9 : u'Нижний',
                     }

    def __init__(self, parent, clientDentitionHistoryModel):
        QAbstractTableModel.__init__(self, parent)
        self._actionRecord              = None
        self._action                    = None
        self._isExistsDentitionAction   = False
        self._isCurrentParadentiumAction  = False
        self.clientId = None
        self._history = clientDentitionHistoryModel
        self._eventEditor = parent
        self.readOnly = False
        self.asAdult = False


    def setReadOnly(self, value):
        self.readOnly = value


    def eventTypeId(self):
        return self._eventEditor.eventTypeId


    def teethIsSet(self):
        allIsEmpty = True
        if self.asAdult:
            defaultTeethValues = self.adultDefaultTeethValues
        else:
            defaultTeethValues = self.childDefaultTeethValues
        for row in defaultTeethValues.keys():
            for column in range(self.columnCount()):
                value = forceStringEx(self.data(self.index(row, column)))
                if value:
                    allIsEmpty = False
                    break
        return not allIsEmpty

    def isCurrentItem(self, row):
        return self._history.isCurrentDentitionAction(row)


    def currentHistoryRow(self):
        return self._history._currentRow


    def copyParodent(self, action=None):
        if action is None:
            record, action, actionId, eventId, isChecked, personName = self._history.getParadentiumItem(self.currentHistoryRow())
        currentRecord, currentAction, currentActionId, currentEventId, currentIsChecked, currentPersonName = self._history.getParadentiumItem(self._history.currentDentitionItemRow())
        actionType = action.getType()
        for propertyTypeId, propertyType in actionType.getPropertiesById().items():
            property = action.getPropertyById(propertyTypeId)
            currentProperty = currentAction.getPropertyById(propertyTypeId)
            currentProperty.copy(property)


    def clearParodent(self):
        currentRecord, currentAction, currentActionId, currentEventId, currentIsChecked, personName = self._history.getParadentiumItem(self._history.currentDentitionItemRow())
        actionType = currentAction.getType()
        for propertyTypeId, propertyType in actionType.getPropertiesById().items():
            ok = True
            for name in [u'Клиновидный', u'Рецессия', u'Подвижность', u'Глубина']:
                ok = True if name in propertyType.name else False
                if ok:
                    break
            if ok:
                property = currentAction.getPropertyById(propertyTypeId)
                property.setValue(None)
        self.emitAllDataChanged()


    def getPenultimateItemAction(self):
        if len(self._history.items()) > 1:
            penultimateInspectionItem = self._history.items()[1] if self._history.items()[1] else None
            if penultimateInspectionItem:
                action = self._history.items()[1][1]
                if action:
                    record = action.getRecord()
                    visitId  = forceRef(record.value('visit_id'))
                    personId = forceRef(record.value('person_id'))
                    date     = forceDateTime(record.value('begDate'))
                    row = self._history.getParadentiumHistoryRow(penultimateInspectionItem[3], visitId, personId, date)
                    penultimateItem = self._history.getParadentiumItem(row)
                    return penultimateItem[1] if penultimateItem else None
        return None


    def setIsExistsDentitionAction(self, isExistsDentitionAction):
        self._isExistsDentitionAction = isExistsDentitionAction


    def columnCount(self, index=None):
        return 16


    def rowCount(self, index=None):
        return len(CParodentiumModel.teethRowTypes.keys())


    def getPropertyType(self, row, column):
        return self._getProperty(row, column).type()


    def setClientId(self, clientId):
        self.clientId = clientId


    def getClientId(self):
        return self.clientId


    def _getProperty(self, row, column):
        # магия в том что у каждого ActionPropertyType зубной формулы
        # имя состоит (через точку) из типа свойства по отношению к формуле,
        # части челюсти и номера с права на лево(1...16)
        # например `Подвижность.Верхний.1`
        # обращение к значениям свойст происходит через их названия.
        # по row определяется тип и часть челюсти, а номер column+1
        propertyName = self.getPropertyName(row, column)
        return self._action.getProperty(propertyName)


    @classmethod
    def getPropertyName(cls, row, column):
        propertyTeethRowType = cls.teethRowTypes[row]
        propertyJawHalfType  = cls.jawHalfTypes[row]
        propertyToothIdx     = unicode(column+1)
        propertyName = u'.'.join([propertyTeethRowType, propertyJawHalfType, propertyToothIdx])
        return propertyName


    def action(self):
        return self._action


    def actionRecord(self):
        return self._actionRecord


    def loadAction(self, actionRecord, action, isCurrentParadentiumAction):
        self._actionRecord = actionRecord
        self._action = action
        self._isCurrentParadentiumAction = isCurrentParadentiumAction
        self.reset()


    def setIsCurrentParadentiumAction(self, isCurrentParadentiumAction=False):
        self._isCurrentParadentiumAction = isCurrentParadentiumAction


    def setNullValues(self):
        self.loadAction(None, None, None)


    def flags(self, index):
#        row = index.row()
#        column = index.column()
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if not (self._isCurrentParadentiumAction and self._action):
            return Qt.ItemIsSelectable|Qt.ItemIsEnabled
        return Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Vertical:
                return QVariant(CParodentiumModel.teethRowTypesHeader.get(section, None))
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if not self._isExistsDentitionAction:
            return QVariant()
        if not self._action:
            return QVariant()
        row    = index.row()
        column = index.column()
        if role == Qt.DisplayRole:
            property = self._getProperty(row, column)
            return toVariant(property.getText())
        elif role == Qt.EditRole:
            property = self._getProperty(row, column)
            return toVariant(property.getValue())
        return QVariant()


    def _ensureTooth(self, row, column):
        # вспомогательная функция, устанавливает код зуба если до этого его небыло
        if row<=3:
            rows = (0, 1, 2, 3)
            toothRow = 4
        else:
            rows = (6, 7, 8, 9)
            toothRow = 5

        toothProperty = self._getProperty(toothRow, column)
        if toothProperty and not toothProperty.getValue():
            propertyValuePresent = False
            for row in rows:
                property = self._getProperty(row, column)
                if property and property.getValue():
                    propertyValuePresent = True
                    break
            if propertyValuePresent:
                toothCode = self.adultDefaultTeethValues[toothRow][column]
                toothProperty.setValue(toothCode)


    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        if not self._action:
            return False
        row = index.row()
        column = index.column()
        if role == Qt.EditRole:
            property = self._getProperty(row, column)
            propertyType = property.type()
            property.setValue(propertyType.convertQVariantToPyValue(value))
            if row <= 3:
                self._ensureTooth(row, column)
                begIndex = self.index(0, column)
                endIndex = self.index(4, column)
                self.emitDataChanged(begIndex, endIndex)
            if row >= 6:
                self._ensureTooth(row, column)
                begIndex = self.index(5, column)
                endIndex = self.index(9, column)
                self.emitDataChanged(begIndex, endIndex)
            else:
                self.emitDataChanged(index, index)
            return True
        return False


    def emitAllDataChanged(self):
        begIndex = self.index(0, 0)
        endIndex = self.index(self.rowCount()-1, self.columnCount()-1)
        self.emitDataChanged(begIndex, endIndex)


    def emitDataChanged(self, begIndex, endIndex):
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), begIndex, endIndex)


    def setAdultDefaults(self, asAdult):
        self.asAdult = asAdult


    def setDefaults(self, asAdult):
        self.asAdult = asAdult
        rows = (4, 5)
        for column in xrange(16):
            for row in rows:
                defaultValue = self._defaultValue(self.asAdult, row, column)
                self.setData(self.index(row, column), defaultValue)


    def _defaultValue(self, asAdult, row, column):
        if asAdult:
            return self.adultDefaultTeethValues[row][column]
        else:
            return self.childDefaultTeethValues[row][column]
# ######################################################################################################


class CClientDentitionHistoryModel(QAbstractTableModel):
    dentitionIsShown = 0
    paradentiumIsShown = 1
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self._clientId = None
        self._currentDentitionItemRow = None
        self._currentDentitionItemsRow = []
        self._dentitionHistoryItems = []
        self._resultDentitionHistoryItems = []
        self._actionForPaste = None
        self._currentRow = -1
        self._shownAction = CClientDentitionHistoryModel.dentitionIsShown


    def setShownHistoryType(self, type):
        self._shownAction = type
        self.reset()


    def setCurrentHistoryRow(self, row):
        self._currentRow = row

    def eventEditor(self):
        return QObject.parent(self)


    def setActionForPaste(self, action):
        self._actionForPaste = action


    def setCurrentInspectionForPaste(self, index):
        record, action, actionId, eventId = self.getItem(index)
        self.setActionForPaste(action)


    def setCurrentResultForPaste(self, index):
        record, action, actionId, eventId = self.getResultItem(index)
        self.setActionForPaste(action)


    def getActionForPaste(self):
        return self._actionForPaste


    def currentDentitionItemRow(self):
        return self._currentDentitionItemRow


    def getCurrentDentitionItemsRow(self):
        return self._currentDentitionItemsRow


    def clientId(self):
        return self._clientId


    def loadClientDentitionHistory(self, clientId, setDate):
        self._dentitionHistoryItems = []
        self._resultDentitionHistoryItems = []
        self._clientId = clientId
        db = QtGui.qApp.db
        tableEvent            = db.table('Event')
        tableAction           = db.table('Action')
        tableActionType       = db.table('ActionType')
        tablePerson           = db.table('vrbPersonWithSpeciality')

        cond = [tableEvent['client_id'].eq(clientId),
                tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['flatCode'].eq(u'dentitionInspection')
                ]
        if setDate:
            cond.append(tableAction['begDate'].yearEq(setDate))

        queryTable = tableEvent.innerJoin(tableAction,
                                          tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableActionType,
                                          tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
        order  = tableAction['begDate'].name() + ' DESC' + ', ' + tableAction['event_id'].name() + ' DESC'
        fields = 'Event.id AS eventId, Action.*, vrbPersonWithSpeciality.name AS personName'
        recordList = db.getRecordList(queryTable, fields, cond, order)
        for record in recordList:
            id = forceRef(record.value('id'))
            eventId = forceRef(record.value('eventId'))
            personId = forceRef(record.value('person_id'))
            date = forceDateTime(record.value('begDate'))
            personName = forceString(record.value('personName'))
            action = CAction(record=record)
            isChecked = 0
            self._resultDentitionHistoryItems.append(self._getResultDentitionHistoryItem(eventId, isChecked, clientId, date, personId))
            self._dentitionHistoryItems.append((record, action, id, eventId, isChecked, personName))
        if len(self._dentitionHistoryItems) > 0:
            self._dentitionHistoryItems.sort(key=lambda x: forceDateTime(x[0].value('begDate') if x and x[0] else None))
            self._dentitionHistoryItems.reverse()
        if len(self._resultDentitionHistoryItems) > 0:
            self._resultDentitionHistoryItems.sort(key=lambda x: forceDateTime(x[0].value('begDate') if x and x[0] else None))
            self._resultDentitionHistoryItems.reverse()
        self.reset()


    def _getResultDentitionHistoryItem(self, eventId, isChecked, clientId, date, personId):
        db = QtGui.qApp.db
        tableEvent            = db.table('Event')
        tableAction           = db.table('Action')
        tableActionType       = db.table('ActionType')
        tablePerson           = db.table('vrbPersonWithSpeciality')
        cond = [tableEvent['client_id'].eq(clientId),
                tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['flatCode'].eq(u'parodentInsp'),
                tableEvent['id'].eq(eventId),
                tableAction['begDate'].eq(date),
                tableAction['person_id'].eq(personId)
                ]
        queryTable = tableEvent.innerJoin(tableAction,
                                          tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableActionType,
                                          tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
        record = db.getRecordEx(queryTable, 'Action.*, vrbPersonWithSpeciality.name AS personName', cond)
        if record:
            return record, CAction(record=record), forceRef(record.value('id')), eventId, isChecked, forceString(record.value('personName'))
        return None, None, None, None, None, None


    def addNewDentitionForVisitItem(self, newItemRecord, newItemAction, actionId, eventId, isChecked, personName):
        newItem = (newItemRecord, newItemAction, actionId, eventId, isChecked, personName)
        self._dentitionHistoryItems.insert(0, newItem)
        self._currentDentitionItemRow = 0
        self.reset()


    def addNewDentitionItem(self, newItemRecord, newItemAction):
        newItem = (newItemRecord, newItemAction, None, None, 0, None)
        self._dentitionHistoryItems.insert(0, newItem)
        self._currentDentitionItemRow = 0
        self.reset()


    def addNewParodentiumForVisitItem(self, newItemRecord, newItemAction, actionId, eventId, isChecked, personName):
        newItem = (newItemRecord, newItemAction, actionId, eventId, isChecked, personName)
        self._resultDentitionHistoryItems.insert(0, newItem)
        self._currentDentitionItemRow = 0
        self.reset()


    def addNewParodentiumItem(self, newItemRecord, newItemAction):
        newItem = (newItemRecord, newItemAction, None, None, 0, None)
        self._resultDentitionHistoryItems.insert(0, newItem)
        self._currentDentitionItemRow = 0
        self.reset()


    def getParadentiumItem(self, row):
        if row is not None and 0 <= row < len(self._resultDentitionHistoryItems):
            return self._resultDentitionHistoryItems[row]
        else:
            return (None, None, None, None, None, None)


    def updateParadentiumItem(self, row):
        if row is not None and 0 <= row < len(self._dentitionHistoryItems):
            record, action, actionId, eventId, isChecked, personName = self.getParadentiumItem(row)
            dentRecord, dentAction, dentActionId, dentEventId, isCheckedDent, personNameDent = self._dentitionHistoryItems[row]
            if dentAction:
                dentActionRecord = dentAction.getRecord()
                date = forceDateTime(dentActionRecord.value('begDate'))
                personId = forceDateTime(dentActionRecord.value('person_id'))
                record.setValue('directionDate', QVariant(date))
                record.setValue('begDate', QVariant(date))
                record.setValue('endDate', QVariant(date))
                record.setValue('person_id', QVariant(personId))
                recordAction = action.getRecord()
                recordAction.setValue('directionDate', QVariant(date))
                recordAction.setValue('begDate', QVariant(date))
                recordAction.setValue('endDate', QVariant(date))
                recordAction.setValue('person_id', QVariant(personId))
                self._resultDentitionHistoryItems[row] = record, action, actionId, eventId, isChecked, personNameDent
                self.emitDataRowChanged(row)


    def updateParadentiumHistoryItem(self, currentActionRecord, currentAction, currentBegDate, currentPersonId, currentEventId):
        if currentAction:
            db = QtGui.qApp.db
            tablePerson = db.table('vrbPersonWithSpeciality')
            actionRecord = currentAction.getRecord()
            currentActionId = forceRef(actionRecord.value('id'))
            currentVisitId = forceRef(actionRecord.value('visit_id'))
            newPersonId = forceRef(actionRecord.value('person_id'))
            newPersonName = forceString(db.translate(tablePerson, 'id', newPersonId, 'name'))
            for row, (record, action, id, eventId, isChecked, personName) in enumerate(self._resultDentitionHistoryItems):
                if id == currentActionId and currentEventId == eventId:
                    recordHist =  action.getRecord()
                    histVisitId = forceRef(recordHist.value('visit_id'))
                    histBegDate  = forceDateTime(recordHist.value('begDate'))
                    histPersonId = forceRef(recordHist.value('person_id'))
                    if histVisitId == currentVisitId and histPersonId == newPersonId and histBegDate == currentBegDate:
                        self._currentDentitionItemRow = row
                        self._resultDentitionHistoryItems[row] = (currentActionRecord, currentAction, currentActionId, currentEventId, isChecked, newPersonName)
                        self.emitDataRowChanged(row)
                        return row
        return None


    def updateDentitionHistoryItems(self, currentActionRecord, currentAction, currentBegDate, currentPersonId, currentEventId):
        if currentAction:
            db = QtGui.qApp.db
            tablePerson = db.table('vrbPersonWithSpeciality')
            actionRecord = currentAction.getRecord()
            currentActionId = forceRef(actionRecord.value('id'))
            currentVisitId = forceRef(actionRecord.value('visit_id'))
            newPersonId = forceRef(actionRecord.value('person_id'))
            newPersonName = forceString(db.translate(tablePerson, 'id', newPersonId, 'name'))
            for row, (record, action, id, eventId, isChecked, personName) in enumerate(self._dentitionHistoryItems):
                if id == currentActionId and currentEventId == eventId:
                    recordHist =  action.getRecord()
                    histVisitId = forceRef(recordHist.value('visit_id'))
                    histBegDate  = forceDateTime(recordHist.value('begDate'))
                    histPersonId = forceRef(recordHist.value('person_id'))
                    if histVisitId == currentVisitId and histPersonId == newPersonId and histBegDate == currentBegDate:
                        self._currentDentitionItemRow = row
                        self._dentitionHistoryItems[row] = (currentActionRecord, currentAction, currentActionId, currentEventId, isChecked, newPersonName)
                        self.emitDataRowChanged(row)
                        return row
        return None


    def getDentitionHistoryRow(self, eventId, visitId, personId, date):
        for row, (record, action, id, histEventId, isChecked, personName) in enumerate(self._dentitionHistoryItems):
            if action:
                actionRecord = action.getRecord()
                histVisitId  = forceRef(actionRecord.value('visit_id'))
                histPersonId = forceRef(actionRecord.value('person_id'))
                histBegDate  = forceDateTime(actionRecord.value('begDate'))
                if eventId == histEventId and visitId == histVisitId and personId == histPersonId and date == histBegDate:
                    return row
        return None


    def getParadentiumHistoryRow(self, eventId, visitId, personId, date):
        for row, (record, action, id, histEventId, isChecked, personName) in enumerate(self._resultDentitionHistoryItems):
            if action:
                actionRecord = action.getRecord()
                histVisitId  = forceRef(actionRecord.value('visit_id'))
                histPersonId = forceRef(actionRecord.value('person_id'))
                histBegDate  = forceDateTime(actionRecord.value('begDate'))
                if eventId == histEventId and visitId == histVisitId and personId == histPersonId and date == histBegDate:
                    return row
        return None


    def setCurrentDentitionItem(self, currentActionRecord, currentAction):
        if not currentActionRecord and not currentAction:
            return self._currentDentitionItemRow
        currentActionId = forceRef(currentActionRecord.value('id'))
        currentEventId  = forceRef(currentActionRecord.value('event_id'))
        for row, (record, action, id, currentEventId, isChecked, personName) in enumerate(self._dentitionHistoryItems):
            if id == currentActionId:
                self._currentDentitionItemRow = row
                self._dentitionHistoryItems[row] = (currentActionRecord, currentAction, currentActionId, currentEventId, isChecked, personName)
                self.emitDataRowChanged(row)
                break
        return self._currentDentitionItemRow


    def setCurrentParadentiumItem(self, currentActionRecord, currentAction):
        if not currentActionRecord and not currentAction:
            return self._currentDentitionItemRow
        currentActionId = forceRef(currentActionRecord.value('id'))
        currentEventId  = forceRef(currentActionRecord.value('event_id'))
        for row, (record, action, id, currentEventId, isChecked, personName) in enumerate(self._resultDentitionHistoryItems):
            if id == currentActionId:
                self._currentDentitionItemRow = row
                self._resultDentitionHistoryItems[row] = (currentActionRecord, currentAction, currentActionId, currentEventId, isChecked, personName)
                self.emitDataRowChanged(row)
                break
        return self._currentDentitionItemRow


    def setCurrentDentitionItems(self, currentActionRecord, currentAction, eventId):
        self._currentDentitionItemsRow = []
        if not currentActionRecord and not currentAction:
            return self._currentDentitionItemsRow
        # currentActionId = forceRef(currentActionRecord.value('id'))
        currentEventId  = forceRef(currentActionRecord.value('event_id'))
        for row, (record, action, id, currentEventId, isChecked, personName) in enumerate(self._dentitionHistoryItems):
            if eventId == currentEventId:
                self._currentDentitionItemsRow.append(row)
        return self._currentDentitionItemsRow


    def emitDataRowChanged(self, row):
        begIndex = self.index(row, 0)
        endIndex = self.index(row, self.columnCount()-1)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), begIndex, endIndex)


    def rowCount(self, index=None):
        return len(self._dentitionHistoryItems)


    def columnCount(self, index=None):
        return 3


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0:
                    return QVariant(u'Печать')
                elif section == 1:
                    return QVariant(u'Дата')
                elif section == 2:
                    return QVariant(u'Исполнитель')
        return QVariant()


    def getItem(self, index):
        row = index.row()
        return self.getItemByRow(row)


    def getItemParodentium(self, index):
        row = index.row()
        return self._resultDentitionHistoryItems[row]


    def getResultItem(self, index):
        row = index.row()
        return self.getResultItemByRow(row)


    def getItemByRow(self, row):
        if row is not None and 0 <= row < len(self._dentitionHistoryItems):
            return self._dentitionHistoryItems[row]
        return (None, None, None, None, None, None)


    def getResultItemByRow(self, row):
        if row is not None and 0 <= row < len(self._resultDentitionHistoryItems):
            return self._resultDentitionHistoryItems[row]
        else:
            return None


    def setResultItem(self, row, record, action, actionId, eventId, isChecked, personName):
        if row is not None and 0 <= row < len(self._resultDentitionHistoryItems):
            self._resultDentitionHistoryItems[row] = (record, action, actionId, eventId, isChecked, personName)
        elif row is not None and row >= len(self._resultDentitionHistoryItems):
            self._resultDentitionHistoryItems.append((record, action, actionId, eventId, isChecked, personName))


    def items(self):
        return self._dentitionHistoryItems


    def flags(self, index):
        column = index.column()
        if column == 0:
            return Qt.ItemIsSelectable|Qt.ItemIsUserCheckable|Qt.ItemIsEnabled
        else:
            return Qt.ItemIsSelectable|Qt.ItemIsEnabled


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if self._shownAction == CClientDentitionHistoryModel.dentitionIsShown:
            return self.__getDentitionData(index, role)
        elif self._shownAction == CClientDentitionHistoryModel.paradentiumIsShown:
            return self.__getParadentiumData(index, role)
        return QVariant()


    def __getDentitionData(self, index, role):
        row    = index.row()
        column = index.column()
        if row is not None and 0 <= row < len(self._dentitionHistoryItems):
            record, action, id, eventId, isChecked, personName = self._dentitionHistoryItems[row]
        else:
#            record, action, id, eventId, isChecked, personName = (None, None, None, None, None, None)
            record, isChecked, personName = (None, None, None)
        if role == Qt.DisplayRole:
            if column == 1:
                val = forceDateTime(record.value('endDate'))
                return QVariant(val.toString(Qt.LocaleDate))
            elif column == 2:
                return QVariant(personName)
            else:
                return QVariant()
        elif role == Qt.CheckStateRole:
            if column == 0:
                return toVariant(Qt.Unchecked if isChecked == 0 else Qt.Checked)
        elif role == Qt.ForegroundRole:
            if self.isCurrentDentitionAction(row):
                return QVariant(QtGui.QColor(255, 0, 0))
        elif role == Qt.FontRole:
            if self.isCurrentDentitionEvent(row):
                result = QtGui.QFont()
                result.setBold(True)
                return QVariant(result)
        else:
            return QVariant()
        return QVariant()


    def __getParadentiumData(self, index, role):
        row    = index.row()
        column = index.column()
        record, action, id, eventId, isChecked, personName = self.getParadentiumItem(row)
        if record:
            if role == Qt.DisplayRole:
                if column == 1:
                    val = forceDateTime(record.value('endDate'))
                    return QVariant(val.toString(Qt.LocaleDate))
                elif column == 2:
                    return QVariant(personName)
                else:
                    return QVariant()
            elif role == Qt.CheckStateRole:
                if column == 0:
                    return toVariant(Qt.Unchecked if isChecked == 0 else Qt.Checked)
            elif role == Qt.ForegroundRole:
                if self.isCurrentDentitionAction(row):
                    return QVariant(QtGui.QColor(255, 0, 0))
            elif role == Qt.FontRole:
                if self.isCurrentDentitionEvent(row):
                    result = QtGui.QFont()
                    result.setBold(True)
                    return QVariant(result)
            else:
                return QVariant()
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        if self._shownAction == CClientDentitionHistoryModel.dentitionIsShown:
            return self.__setDentitionData(index, value, role)
        elif self._shownAction == CClientDentitionHistoryModel.paradentiumIsShown:
            return self.__setParadentiumData(index, value, role)
        return False


    def __setDentitionData(self, index, value, role):
        column = index.column()
        row = index.row()
        if role == Qt.CheckStateRole:
            if column == 0:
                if row is not None and 0 <= row < len(self._dentitionHistoryItems):
                    record, action, id, eventId, isChecked, personName = self._dentitionHistoryItems[row]
                else:
                    record, action, id, eventId, isChecked, personName = (None, None, None, None, None, None)
                if forceInt(value) == 2:
                    isChecked = 1
                elif forceInt(value) == 0:
                    isChecked = 0
                self._dentitionHistoryItems[row] = (record, action, id, eventId, isChecked, personName)
                return True
        return False


    def __setParadentiumData(self, index, value, role):
        column = index.column()
        row = index.row()
        if role == Qt.CheckStateRole:
            if column == 0:
                record, action, id, eventId, isChecked, personName = self.getParadentiumItem(row)
                if forceInt(value) == 2:
                    isChecked = 1
                elif forceInt(value) == 0:
                    isChecked = 0
                self.setResultItem(row, record, action, id, eventId, isChecked, personName)
                return True
        return False


    def isCurrentDentitionAction(self, row):
        return row == self._currentDentitionItemRow


    def isCurrentDentitionEvent(self, row):
        return row in self._currentDentitionItemsRow

# #####################################################################

# WFT? QInputDialog не?

class CPrintTypeSelector(QtGui.QDialog):
    simplePrint = 0
    internationalPrint = 1
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.cmbPrintType = QtGui.QComboBox(self)
        self.cmbPrintType.addItem(u'Упрощенная нумерация')
        self.cmbPrintType.addItem(u'Международная нумерация')
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.layout = QtGui.QVBoxLayout(self)

        self.layout.addWidget(self.cmbPrintType)
        self.layout.addWidget(self.buttonBox)

        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)
        self.connect(self.buttonBox, SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, SIGNAL('rejected()'), self.reject)

        self.setLayout(self.layout)


    def value(self):
        return self.cmbPrintType.currentIndex()


    def isSimplePrint(self):
        return self.value() == CPrintTypeSelector.simplePrint


    def isInternationalPrint(self):
        return self.value() == CPrintTypeSelector.internationalPrint
