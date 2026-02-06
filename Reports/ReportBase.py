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
from PyQt4.QtCore import *
from PyQt4.QtGui import QTextCharFormat

from library.Utils import *

from ReportView import CReportViewDialog

__all__ = ( 'CReportBase',
            'createTable',
            'autoMergeHeader'
          )

# обнаружено, что в некоторых случаях (напр., при запуске программы в kubuntu 8.04 и kubuntu 8.10)
# код
#   class CReportBase(object):
#       AlignLeft = QtGui.QTextBlockFormat()
#       AlignLeft.setAlignment(Qt.AlignLeft)
# приводит к дефектам изображения (неверно рисуется меню, для labels выделяется недостаточное пространство и пр.)
# вероятно, дело в кешировании оконной системой объектов соответствующих QtGui.QTextBlockFormat
# поэтому принято решение сделать их некешируемыми

# взято из http://stackoverflow.com/questions/5189699/how-can-i-make-a-class-property-in-python
class CClassPropertyDescriptor(object):
    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset


    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)
        return self.fget.__get__(obj, klass)()


    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)


    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self


def classproperty(func):
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return CClassPropertyDescriptor(func)


class CReportBase(object):
    @classproperty
    def AlignLeft(self):
        result = QtGui.QTextBlockFormat()
        result.setAlignment(Qt.AlignLeft)
        return result


    @classproperty
    def AlignCenter(self):
        result = QtGui.QTextBlockFormat()
        result.setAlignment(Qt.AlignCenter)
        return result


    @classproperty
    def AlignRight(self):
        result = QtGui.QTextBlockFormat()
        result.setAlignment(Qt.AlignRight)
        return result


    @classproperty
    def ReportTitle(self):
        result = QtGui.QTextCharFormat()
        result.setProperty(QtGui.QTextFormat.FontSizeIncrement, QVariant(2))
        result.setFontWeight(QtGui.QFont.Bold)
        return result


    @classproperty
    def ReportSubTitle(self):
        result = QtGui.QTextCharFormat()
        result.setProperty(QtGui.QTextFormat.FontSizeIncrement, QVariant(1))
        result.setFontWeight(QtGui.QFont.Bold)
        return result


    @classproperty
    def ReportBody(self):
        result = QtGui.QTextCharFormat()
        result.setProperty(QtGui.QTextFormat.FontSizeIncrement, QVariant(0))
        return result


    @classproperty
    def TableBody(self):
        result = QtGui.QTextCharFormat()
        return result


    @classproperty
    def TableHeader(self):
        result = QtGui.QTextCharFormat()
        result.setFontWeight(QtGui.QFont.Bold)
        return result


    @classproperty
    def TableTotal(self):
        result = QtGui.QTextCharFormat()
        result.setFontWeight(QtGui.QFont.Bold)
        return result


    def __init__(self, parent=None):
        self.__parent = parent
        self.__title  = ''
        self.__preferences = ''
        self.viewerGeometry = None
        self.orientation = QtGui.QPrinter.Portrait
        self.pageFormat = None
        self.lineWrapMode = None


    def setOrientation(self, orientation):
        self.orientation = orientation
    
    def setLineWrapMode(self, mode):
        self.lineWrapMode = mode


    def exec_(self):
        QtGui.qApp.call(self.__parent, self.reportLoop)


    def reportLoop(self):
        params = self.getDefaultParams()
        while True:
            setupDialog = self.getSetupDialog(self.__parent)
            setupDialog.setParams(params)
            if not setupDialog.exec_():
                break
            params = setupDialog.params()
            self.saveDefaultParams(params)
            try:
                reportResult = ''
                QtGui.qApp.setWaitCursor()
                reportResult = self.build(params)
            finally:
                QtGui.qApp.restoreOverrideCursor()
            viewDialog = CReportViewDialog(self.__parent)
            if self.viewerGeometry:
                viewDialog.restoreGeometry(self.viewerGeometry)
            viewDialog.setWindowTitle(self.title())
            viewDialog.setRepeatButtonVisible()
            viewDialog.setText(reportResult)
            viewDialog.setOrientation(self.orientation)
            if self.pageFormat:
                viewDialog.setPageFormat(self.pageFormat)
            if self.lineWrapMode is not None:
                viewDialog.txtReport.setLineWrapMode(self.lineWrapMode)
            done = not viewDialog.exec_()
            self.viewerGeometry = viewDialog.saveGeometry()
            if done:
                break
        # save params?


    def oneShot(self, params):
        try:
            QtGui.qApp.setWaitCursor()
            reportResult = self.build(params)
        finally:
            QtGui.qApp.restoreOverrideCursor()
        viewDialog = CReportViewDialog(self.__parent)
        if self.viewerGeometry:
            viewDialog.restoreGeometry(self.viewerGeometry)
        viewDialog.setWindowTitle(self.title())
        viewDialog.setText(reportResult)
        viewDialog.setOrientation(self.orientation)
        viewDialog.exec_()
        self.viewerGeometry = viewDialog.saveGeometry()


    def setTitle(self, title, preferences=''):
        self.__title = title
        if preferences:
            self.__preferences = preferences
        else:
            self.__preferences = title


    def title(self):
        return self.__title


    def patientRequired(self):
        return False


    def getDefaultParams(self):
        result = {}
        prefs = getPref(QtGui.qApp.preferences.reportPrefs, self.__preferences, {})
        today = QDate.currentDate()
        begYear = firstYearDay(today.addDays(-7))
        result['actionDateType'] = getPrefInt(prefs, 'actionDateType', 0)
        result['begDate']     = getPrefDate(prefs, 'begDate', begYear)
        result['begDateTalonSignal'] = getPrefDate(prefs, 'begDateTalonSignal', today.addDays(-1))
        result['endDate']     = getPrefDate(prefs, 'endDate', today.addDays(-1))
        result['begDateBeforeRecord']     = getPrefDate(prefs, 'begDateBeforeRecord', QDate(today.year(), today.month(), 1))
        result['endDateBeforeRecord']     = getPrefDate(prefs, 'endDateBeforeRecord', today.addDays(-1))
        result['Year']        = getPrefString(prefs, 'Year', '')
        result['begTime']     = getPrefTime(prefs, 'begTime', QTime(0, 0))
        result['endTime']     = getPrefTime(prefs, 'endTime', QTime(23, 59, 59))
        result['orgStructureId'] = getPrefRef(prefs, 'orgStructureId', None)
        result['setOrgStructureId'] = getPrefRef(prefs, 'setOrgStructureId', None)
        result['personId']  = getPrefRef(prefs, 'personId', None)
        result['userProfileId']  = getPrefRef(prefs, 'userProfileId', None)
        result['beforeRecordUserId']  = getPrefRef(prefs, 'beforeRecordUserId', None)
        result['orgInsurerId']  = getPrefRef(prefs, 'orgInsurerId', None)
        result['hospitalBedProfileId']   = getPrefRef(prefs, 'hospitalBedProfileId', None)
        result['emergencyOrder'] = getPrefInt(prefs, 'emergencyOrder', 0)
        # для нетрудоспособности:
        result['byPeriod']    = getPrefBool(prefs, 'byPeriod', None) # отбор по периоду
        result['doctype']     = getPrefRef(prefs, 'doctype', None)  # тип документа (листок, справка)
        result['tempInvalidReason']= getPrefRef(prefs, 'tempInvalidReason', None)  # причина временной нетрудоспособности
        result['durationFrom']= getPrefInt(prefs, 'durationFrom', 0)# фильтр по длительности
        result['durationTo']  = getPrefInt(prefs, 'durationTo', 0)  # фильтр по длительности
        result['sex']         = getPrefInt(prefs, 'sex', 0)
        result['ageFrom']     = getPrefInt(prefs, 'ageFrom', 0)
        result['ageTo']       = getPrefInt(prefs, 'ageTo', 150)
        result['socStatusClassId'] = getPrefRef(prefs, 'socStatusClassId', None)
        result['socStatusTypeId'] = getPrefRef(prefs, 'socStatusTypeId', None)
        result['onlyClosed']  = getPrefBool(prefs, 'onlyClosed', None) # только закрытые
        #
        result['MKBFilter']   = getPrefInt(prefs, 'MKBFilter', 0) # 0-нет фильтра, 1-интервал, 2-нет кода
        result['MKBFrom']     = getPrefString(prefs, 'MKBFrom', 'A00')
        result['MKBTo']       = getPrefString(prefs, 'MKBTo', 'Z99.9')
        result['MKBExFilter'] = getPrefInt(prefs, 'MKBExFilter', 0) # 0-нет фильтра, 1-интервал, 2-нет кода
        result['MKBExFrom']     = getPrefString(prefs, 'MKBExFrom', 'A00')
        result['MKBExTo']       = getPrefString(prefs, 'MKBExTo', 'Z99.9')

        result['eventTypeId'] = getPrefRef(prefs, 'eventTypeId', None)
        result['eventPurposeId'] = getPrefRef(prefs, 'eventPurposeId', None)
        result['eventResultId'] = getPrefRef(prefs, 'eventResultId', None)
        result['actionTypeClass'] = getPrefInt(prefs, 'actionTypeClass', 0)
        result['actionTypeId']    = getPrefRef(prefs, 'actionTypeId', None)
        result['queueType']    = getPrefRef(prefs, 'queueType', None)
        result['onlyPermanentAttach'] = getPrefBool(prefs, 'onlyPermanentAttach', False)
        result['onlyPayedEvents'] = getPrefBool(prefs, 'onlyPayedEvents', False)
        result['begPayDate']  = getPrefDate(prefs, 'begPayDate', begYear)
        result['endPayDate']  = getPrefDate(prefs, 'endPayDate', QDate())
        result['insurerId']  = getPrefRef(prefs, 'insurerId', None)
        result['contractPath']= getPrefString(prefs, 'contractPath', '')
        #
        result['financeId'] = getPrefRef(prefs, 'financeId', None)
        result['tariff'] = getPrefInt(prefs, 'tariff', 0)
        result['visitPayStatus'] = getPrefInt(prefs, 'visitPayStatus', 0)
        result['groupingRows'] = getPrefInt(prefs, 'groupingRows', 0)
        result['rowGrouping'] = getPrefInt(prefs, 'rowGrouping', 0)
        #
        result['areaId'] = getPrefRef(prefs, 'areaId', None)
        result['characterClass'] = getPrefInt(prefs, 'characterClass', 0)

        result['onlyFirstTime'] = getPrefBool(prefs, 'onlyFirstTime', None) # только первичные
        result['registeredInPeriod'] = getPrefBool(prefs, 'registeredInPeriod', None) # только зарегистрированные в период
        result['notNullTraumaType'] = getPrefBool(prefs, 'notNullTraumaType', None) # только с указанием типа травмы
        result['accountAccomp'] = getPrefBool(prefs, 'accountAccomp', None) # учитывать сопутствующие

        result['busyness'] = getPrefInt(prefs, 'business', 0) # учитывать занятость, 0-не учитывать, 1-только занятые, 2-только не занятые

        result['deathPlace']    = getPrefString(prefs, 'deathPlace', '')
        result['deathCause']    = getPrefString(prefs, 'deathCause', '')
        result['deathFoundBy']  = getPrefString(prefs, 'deathFoundBy', '')
        result['deathFoundation']= getPrefString(prefs, 'deathFoundation', '')

        result['chkClientId'] = getPrefBool(prefs, 'chkClientId', False)
        result['chkEventId'] = getPrefBool(prefs, 'chkEventId', False)
        result['chkExternalEventId'] = getPrefBool(prefs, 'chkExternalEventId', False)
        result['nomenclatureTypeId'] = getPrefRef(prefs, 'nomenclatureTypeId', None)
        result['nomenclatureFeatureNameIndex'] = getPrefInt(prefs, 'nomenclatureFeatureNameIndex', 0)
        result['nomenclatureFeatureValueIndex'] = getPrefInt(prefs, 'nomenclatureFeatureValueIndex', 0)

        result['isCompactInfo'] = getPrefBool(prefs, 'isCompactInfo', False)
        result['isEventInfo'] = getPrefBool(prefs, 'isEventInfo', False)
        result['noPrintCaption'] = getPrefBool(prefs, 'noPrintCaption', False)
        result['isGroupingOS'] = getPrefBool(prefs, 'isGroupingOS', False)
        result['isPermanentBed'] = getPrefBool(prefs, 'isPermanentBed', False)
        result['chkNoPrintFilterParameters'] = getPrefBool(prefs, 'chkNoPrintFilterParameters', False)
        result['noProfileBed'] = getPrefBool(prefs, 'noProfileBed', True)
        result['durationType'] = getPrefInt(prefs, 'durationType', 0)
        result['eventStatus'] = getPrefInt(prefs, 'eventStatus', 0)

        result['permanentBed'] = getPrefBool(prefs, 'permanentBed', False)  # учитывать внештатные койки
        result['eventExpose'] = getPrefBool(prefs, 'eventExpose', False)  # учитывать флаг события "выставлять"
        result['stacType'] = getPrefInt(prefs, 'stacType', 0)  # тип стационара
        result['bedsSchedule'] = getPrefInt(prefs, 'bedsSchedule', 0) # режим коек
        result['addressType'] = getPrefInt(prefs, 'addressType', 0) # тип адреса для определения сельского жителя
        result['forResult'] = getPrefInt(prefs, 'forResult', 0)  # для формы 11
        result['typeDN'] = getPrefInt(prefs, 'typeDN', 0)  # для формы 10
        result['onlyNotExposed'] = getPrefInt(prefs, 'onlyNotExposed', False)  # для формы 10
        result['isOnlyContingent'] = getPrefBool(prefs, 'isOnlyContingent', False)  # для формы 19
        result['cashPayments'] = getPrefBool(prefs, 'cashPayments', False)
        result['filterClientId'] = getPrefRef(prefs, 'filterClientId', None)

        geometry = getPref(prefs, 'viewerGeometry', None)
        if type(geometry) == QVariant and geometry.type() == QVariant.ByteArray and not geometry.isNull():
            self.viewerGeometry = geometry.toByteArray()
        return result


    def saveDefaultParams(self, params):
        prefs = {}
        for param, value in params.iteritems():
            setPref(prefs, param, value)
        if self.viewerGeometry:
            setPref(prefs, 'viewerGeometry', toVariant(self.viewerGeometry))
        setPref(QtGui.qApp.preferences.reportPrefs, self.__preferences, prefs)


    def build(self, params):
        return ''


class CReportTableBase(object):
    def __init__(self, table, aligns):
        self.table = table
        self.aligns = aligns

    def mergeCells(self, row, column, numRows, numCols):
        self.table.mergeCells(row, column, numRows, numCols)

    def rowCount(self):
        return self.table.rows()

    def headerRowCount(self):
        return self.table.format().headerRowCount()

    def dataRowCount(self):
        return self.rowCount() - self.headerRowCount()

    def colCount(self):
        return self.table.columns()

    def addRow(self):
        row = self.rowCount()
        self.table.insertRows(row, 1)
        return row

    def appendRows(self, count):
        self.table.appendRows(count)

    def delRow(self, index, row):
        self.table.removeRows(index, row)
        return self.rowCount()

    def delCol(self, index, col):
        self.table.removeColumns(index, col)
        return self.colCount()

    def cellAt(self, row, column):
        return self.table.cellAt(row, column)

    def cursorAt(self, row, column):
        return self.cellAt(row, column).lastCursorPosition()

    def setText(self, row, column, text, charFormat=None, blockFormat=None, brushColor=None, fontBold=None, size=None):
        cursor = self.cellAt(row, column).firstCursorPosition()
        cursor.movePosition(QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        if brushColor:
            tableFormat = QtGui.QTextCharFormat()
            tableFormat.setBackground(QtGui.QBrush(brushColor))
            cursor.setBlockCharFormat(tableFormat)
        if fontBold or size:
            tableFormat = QtGui.QTextCharFormat()
            font = QtGui.QFont()
            if fontBold:
                font.setBold(True)
            if size:
                font.setPointSize(size)
            tableFormat.setFont(font)
            cursor.setBlockCharFormat(tableFormat)
        if blockFormat:
            cursor.setBlockFormat(blockFormat)
        else:
            cursor.setBlockFormat(self.aligns[column])
        if charFormat:
            cursor.setCharFormat(charFormat)
        cursor.insertText(unicode(text))

    def setHtml(self, row, column, html):
        cursor = self.cursorAt(row, column)
#        cursor.setBlockFormat(self.aligns[column])
#        if charFormat:
#            cursor.setCharFormat(charFormat)
        cursor.insertHtml(html)

    def getCellText(self, row, column):
        cursor = self.cellAt(row, column).firstCursorPosition()
        cursor.movePosition(QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.KeepAnchor)
        return unicode(cursor.selectedText())

    def removeEmptyRows(self, startRow=0, startCol=1, endRow=None, endCol=None):
        u''' просматривает ячейки в таблице, начиная со строки startRow и столбца startCol, и удаляет, если в них нет данных '''
        rowsToDelete = []
        if endRow is None:
            endRow = self.rowCount()
        if endCol is None:
            endCol = self.colCount()
        if startRow >= endRow or startCol >= endCol:
            return
        for i in xrange(startRow + self.headerRowCount(), endRow):
            rowIsZero = True
            for j in xrange(startCol, endCol - startCol):
                text = self.getCellText(i, j)
                if text and text != u'0' and text != u'0.0' and not text.isspace():
                    rowIsZero = False
                    break
            if rowIsZero:
                rowsToDelete.append(i)
        for i in sorted(rowsToDelete, reverse=True):
            self.delRow(i)


def autoMergeHeader(table, tableColumns):
    #ищет ячейки с пустым текстом и объединяет их
    headers = [col[1] for col in tableColumns]
    colheights = [len(col) for col in headers]
    colheightsMin, colheightsMax = [min(colheights), max(colheights)]
    mergeCells = {}
    for colIdx, cols in enumerate(headers):
        for rowIdx, row in enumerate(cols):
            nextColIdx = colIdx+1
            if (nextColIdx < len(headers)):
                nextcols = [col[rowIdx] if rowIdx < len(col) else None for col in headers[nextColIdx:]] # все следующие колонки этой строки

                curIdx = 0
                while(len(nextcols) > curIdx and nextcols[curIdx] == u''):
                    curIdx += 1

                if curIdx > 0:
                    colMerge = curIdx + 1
                    merge = mergeCells.setdefault((rowIdx, colIdx), [1, 1])
                    merge[1] = colMerge

        if len(cols) < colheightsMax:
            rowMerge = (colheightsMax - len(cols)) + 1
            rowIdx = max([i if col != u'' else -1 for i, col in enumerate(cols)]) # последний индекс строки, этой колонки, с текстом
            merge = mergeCells.setdefault((rowIdx, colIdx), [1, 1])
            merge[0] = rowMerge

    for cell,val in mergeCells.iteritems():
        table.mergeCells(cell[0], cell[1], val[0], val[1])

def createTable(testCursor, columnDescrs, headerRowCount=1, border=1, cellPadding=2, cellSpacing=0, duplicateHeaderOnNewPage=True, leftMargin=None, charFormat=True, size=None):
    def widthToTextLenght(width):
        widthSpec = QtGui.QTextLength.VariableLength
        widthVal  = 0
        try:
            if isinstance(width, basestring):
                if len(width)>0:
                    if width[-1:] == '%':
                        widthVal  = float(width[:-1])
                        widthSpec = QtGui.QTextLength.PercentageLength
                    elif width[-1:] == '?':
                        widthVal  = float(width[:-1])
                    elif width[-1:] == '=':
                        widthVal  = float(width[:-1])
                        widthSpec = QtGui.QTextLength.FixedLength
                    else:
                        widthVal  = float(width)
                        widthSpec = QtGui.QTextLength.FixedLength
            else:
                widthVal  = float(width)
                widthSpec = QtGui.QTextLength.FixedLength
        except:
            pass
        return QtGui.QTextLength(widthSpec, widthVal)


    columnWidthConstraints = []
    for columnDescr in columnDescrs:
        assert isinstance(columnDescr, (list, tuple)) and len(columnDescr) == 3
        width, headers, align = columnDescr
        columnWidthConstraints.append(widthToTextLenght(width))
        if isinstance(headers, (list, tuple)):
            headerRowCount = max(headerRowCount,  len(headers))

    tableFormat = QtGui.QTextTableFormat()
    tableFormat.setBorder(border)
    tableFormat.setCellPadding(cellPadding)
    tableFormat.setCellSpacing(cellSpacing)
    tableFormat.setColumnWidthConstraints(columnWidthConstraints)
    tableFormat.setHeaderRowCount(headerRowCount if duplicateHeaderOnNewPage else 0)
    if leftMargin:
        tableFormat.setLeftMargin(leftMargin)
#    tableFormat.setBackground(QtGui.QBrush(Qt.red))
    table = testCursor.insertTable(max(1, headerRowCount), max(1, len(columnDescrs)), tableFormat)

    column = 0
    aligns = []
    for columnDescr in columnDescrs:
        width, headers, align = columnDescr
        if not isinstance(headers, (list, tuple)):
            headers = [ headers ]
        row = 0
        for header in headers:
            if header != '' and type(header) is not list:
                cellCursor = table.cellAt(row, column).firstCursorPosition()
                cellCursor.setBlockFormat(CReportBase.AlignCenter)
                if size:
                    font = QtGui.QFont()
                    font.setPointSize(size)
                    font.setBold(charFormat)
                    elSigner = QTextCharFormat()
                    elSigner.setFont(font)
                    cellCursor.insertText(header, elSigner)
                else:
                    cellCursor.setCharFormat(CReportBase.TableHeader)
                    cellCursor.insertText(header)
            elif type(header) is list:
                cellCursor = table.cellAt(row, column).firstCursorPosition()
                cellCursor.setBlockFormat(CReportBase.AlignCenter)
                font = QtGui.QFont()
                font.setBold(header[1])
                if size:
                    font.setPointSize(size)
                elSigner = QTextCharFormat()
                elSigner.setFont(font)
                cellCursor.insertText(header[0], elSigner)
            row += 1
        aligns.append(align)
        column += 1

    return CReportTableBase(table, aligns)