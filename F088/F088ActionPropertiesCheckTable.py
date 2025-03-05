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
from PyQt4.QtCore import Qt, QMimeData, QString, QVariant, pyqtSignature, SIGNAL, QSize

from library.Utils            import forceInt, forceRef, forceString, getPref, setPref, toVariant
from library.PreferencesMixin import CPreferencesMixin
from Events.PropertyHistoryDialog import CPropertyHistoryDialog
from Events.ActionPropertyChooser import CActionPropertyChooser
from Events.ActionPropertiesTable import (CActionPropertiesTableModel,
                                          CActionPropertiestableVerticalHeaderView,
                                          CActionPropertyEvaluationDelegate,
                                          CActionPropertyCommentDelegate,
                                          CActionPropertyDelegate,
                                          )
from Events.ActionProperty.BooleanActionPropertyValueType import CBooleanActionPropertyValueType
from Events.ActionProperty.TextActionPropertyValueType    import CTextActionPropertyValueType
from Events.ActionProperty.StringActionPropertyValueType  import CStringActionPropertyValueType
from Events.ActionProperty.IntegerActionPropertyValueType import CIntegerActionPropertyValueType
from Events.ActionProperty.DoubleStringActionPropertyValueType import CDoubleStringActionPropertyValueType
from Events.ActionProperty.DoubleActionPropertyValueType   import CDoubleActionPropertyValueType
from Events.ActionProperty.ConstructorActionPropertyValueType import CConstructorActionPropertyValueType


class CF088ActionPropertiesCheckTableModel(CActionPropertiesTableModel):
    column = [u'Включить', u'Назначено', u'Значение',  u'Ед.изм.',  u'Норма', u'Оценка', u'Комментарий']
    ciIsChecked  = 0
    ciIsAssigned = 1
    ciValue      = 2
    ciUnit       = 3
    ciNorm       = 4
    ciEvaluation = 5
    ciComment = 6

    def __init__(self, parent, visibilityFilter=0):
        CActionPropertiesTableModel.__init__(self, parent, visibilityFilter)
        self.includeRows = {}


    def columnCount(self, index = None):
        return 7


    def getCurrentActionId(self):
        return self.action.getId() if self.action else None


    def setIncludeRows(self, propertyIdList):
        for row, propertyId in enumerate(propertyIdList):
            findRow = self.getSelectedPropertyIdRow(propertyId)
            if findRow >= 0 and findRow < len(self.includeRows):
                self.includeRows[findRow] = Qt.Checked


    def getSelectedPropertyIdRow(self, findPropertyId):
        for row, propertyType in enumerate(self.propertyTypeList):
            property = self.action.getPropertyById(propertyType.id)
            if property:
                record = property.getRecord()
                if record:
                    if forceRef(record.value('id')) == findPropertyId:
                        return row
        return -1


    def getSelectedPropertyRows(self):
        propertyRows = {}
        for row, isChecked in self.includeRows.items():
            if bool(isChecked):
                property = self.getProperty(row)
                if property:
                    record = property.getRecord()
                    if record:
                        propertyId = forceRef(record.value('id'))
                        if propertyId:
                            propertyRows[propertyId] = row
        return propertyRows


    def getSelectedIdList(self):
        propertyIdList = []
        for row, isChecked in self.includeRows.items():
            if bool(isChecked):
                property = self.getProperty(row)
                if property:
                    record = property.getRecord()
                    if record:
                        propertyId = forceRef(record.value('id'))
                        if propertyId and propertyId not in propertyIdList:
                            propertyIdList.append(propertyId)
        return propertyIdList


    def getPropertyIdList(self):
        propertyIdList = []
        for row, propertyType in enumerate(self.propertyTypeList):
            property = self.action.getPropertyById(propertyType.id)
            if property:
                record = property.getRecord()
                if record:
                    propertyId = forceRef(record.value('id'))
                    if propertyId and propertyId not in propertyIdList:
                        propertyIdList.append(propertyId)
        return propertyIdList


    def flags(self, index):
        if index.column() == self.ciIsChecked:
            return Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled
        row = index.row()
        column = index.column()
        propertyType = self.propertyTypeList[row]
        if propertyType.isPacsImage():
            return Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled
        if self.readOnly or (self.action and self.action.isLocked()):
            if propertyType.isImage():
                return Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled
            else:
                return Qt.ItemIsEnabled|Qt.ItemIsSelectable
        else:
            if self.hasCommonPropertyChangingRight(row):
                if column == self.ciIsAssigned and propertyType.isAssignable:
                    return Qt.ItemIsSelectable|Qt.ItemIsUserCheckable|Qt.ItemIsEnabled
                elif column == self.ciValue:
                    if propertyType.isBoolean():
                        return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsUserCheckable
                    return Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled
                elif column == self.ciEvaluation:
                    propertyType = propertyType
                    if propertyType.defaultEvaluation in (0, 1):# 0-не определять, 1-автомат
                        return Qt.ItemIsSelectable|Qt.ItemIsEnabled
                    elif propertyType.defaultEvaluation in (2, 3):# 2-полуавтомат, 3-ручное
                        return Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled
                elif column == self.ciComment:
                    return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
            return Qt.ItemIsSelectable|Qt.ItemIsEnabled


    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        column = index.column()
        propertyType = self.propertyTypeList[row]
        property = self.action.getPropertyById(propertyType.id)
        if role == Qt.DisplayRole:
            if column == self.ciValue:
                if propertyType.isBoolean():
                    return QVariant()
                return toVariant(property.getText())
            elif column == self.ciUnit:
                return QVariant(self.unitData.getNameById(property.getUnitId()))
            elif column == self.ciNorm:
                return toVariant(property.getNorm())
            elif column == self.ciEvaluation:
                evaluation = property.getEvaluation()
                if evaluation is None:
                    s = self.getDefaultEvaluation(propertyType, property, index)
#                    s = ''
                else:
                    s = ('%+d'%evaluation) if evaluation else '0'
                return toVariant(s)
            elif column == self.ciComment:
                return QVariant(property.getComment())
            else:
                return QVariant()
        elif role == Qt.CheckStateRole:
            if column == self.ciIsChecked:
                return toVariant(Qt.Checked if self.includeRows.get(row, 0) else Qt.Unchecked)
            if column == self.ciValue:
                if propertyType.isBoolean():
                    return QVariant(Qt.Checked if property.getValue() else Qt.Unchecked)
            if column == self.ciIsAssigned:
                if propertyType.isAssignable:
                    return toVariant(Qt.Checked if property.isAssigned() else Qt.Unchecked)
        elif role == Qt.EditRole:
            if column == self.ciIsAssigned:
                return toVariant(property.getStatus())
            elif column == self.ciValue:
                return toVariant(property.getValue())
            elif column == self.ciUnit:
                return toVariant(property.getUnitId())
            elif column == self.ciNorm:
                return toVariant(property.getNorm())
            elif column == self.ciEvaluation:
                return toVariant(property.getEvaluation())
            elif column == self.ciComment:
                return toVariant(property.getComment())
            else:
                return QVariant()
        elif role == Qt.TextAlignmentRole:
            return QVariant(Qt.AlignLeft|Qt.AlignTop)
        elif role == Qt.DecorationRole:
            return QVariant()
        elif role == Qt.ForegroundRole:
            evaluation = property.getEvaluation()
            if evaluation:
                return QVariant(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
        elif role == Qt.FontRole:
            evaluation = property.getEvaluation()
            if evaluation and abs(evaluation) == 2:
                font = QtGui.QFont()
                font.setBold(True)
                return QVariant(font)
        elif role == Qt.ToolTipRole:
            if column == self.ciIsAssigned:
                if propertyType.isAssignable:
                    return toVariant(u'Назначено' if property.isAssigned() else u'Не назначено')
        elif role == Qt.StatusTipRole:
            if self.actionStatusTip:
                return toVariant(self.actionStatusTip)
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        propertyType = self.propertyTypeList[row]
        property = self.action.getPropertyById(propertyType.id)

        if role == Qt.EditRole:
            if column == self.ciValue:
                if not propertyType.isVector:
                    property.preApplyDependents(self.action)
                    property.setValue(propertyType.convertQVariantToPyValue(value))
                    self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                    self.getDefaultEvaluation(propertyType, property, index)
                    if property.isActionNameSpecifier():
                        self.action.updateSpecifiedName()
                        self.emit(SIGNAL('actionNameChanged()'))
                    property.applyDependents(self.action)
                    if propertyType.isJobTicketValueType():
                        self.action.setPlannedEndDateOnJobTicketChanged(property.getValue())
                    if propertyType.whatDepends:
                        self.updateDependedProperties(propertyType.whatDepends)
                    return True
            elif column == self.ciEvaluation:
                property.setEvaluation(None if value.isNull() else forceInt(value))
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                return True
        elif role == Qt.CheckStateRole:
            if column == self.ciIsChecked:
                self.includeRows[row] = Qt.Checked if forceInt(value) else Qt.Unchecked
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                return True
            elif column == self.ciComment:
                property.setComment(forceString(value))
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                return True
            if column == self.ciValue:
                if propertyType.isBoolean():
                    property.setValue(forceInt(value) == Qt.Checked)
                    self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                    self.getDefaultEvaluation(propertyType, property, index)
                    if propertyType.whatDepends:
                        self.updateDependedProperties(propertyType.whatDepends)
                    return True
            if column == self.ciIsAssigned:
                property.setAssigned(forceInt(value) == Qt.Checked)
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                return True
        return False


    def setAction2(self, action, clientId, clientSex=None, clientAge=None, eventTypeId=None, propertySelectedIdList=[]):
        self.includeRows = {}
        self.action = action
        self.clientId = clientId
        self.clientNormalParameters = self.getClientNormalParameters()
        self.eventTypeId = eventTypeId
        if self.action:
            propertyTypeList = [(id, prop.type()) for (id, prop) in action.getPropertiesById().items()]
            propertyTypeList.sort(key=lambda x: (x[1].idx, x[0]))
            self.propertyTypeList = [x[1] for x in propertyTypeList if x[1].applicable(clientSex, clientAge) and self.visible(x[1]) and x[1].typeName!='PacsImages']
            actionType = action.getType()
            propertyTypeList = actionType.getPropertiesTypeByTypeName('PacsImages')
            if propertyTypeList:
                self.propertyTypeList.extend(propertyTypeList)
        else:
            self.propertyTypeList = []
        propertyTypeListEx = []
        if self.action:
            for propertyType in self.propertyTypeList:
                valueType = propertyType.getValueType()
                if isinstance(valueType, (CTextActionPropertyValueType,
                                          CStringActionPropertyValueType,
                                          CIntegerActionPropertyValueType,
                                          CDoubleStringActionPropertyValueType,
                                          CDoubleActionPropertyValueType,
                                          CBooleanActionPropertyValueType,
                                          CConstructorActionPropertyValueType)):
                    property = self.action.getPropertyById(propertyType.id)
                    if property:
                        record = property.getRecord()
                        if record:
                            propertyId = forceRef(record.value('id'))
                            if propertyId:
                                if propertyId not in propertySelectedIdList and propertyId not in propertyTypeListEx:
                                    propertyTypeListEx.append(propertyType)
        self.propertyTypeList = propertyTypeListEx
        for propertyType in self.propertyTypeList:
            propertyType.shownUp(action, clientId)
        self.updateActionStatusTip()
        self.reset()


class CF088ActionPropertiesTableView(QtGui.QTableView, CPreferencesMixin):
    titleWidth = 20

    def __init__(self, parent):
        QtGui.QTableView.__init__(self, parent)
        self._verticalHeader = CActionPropertiestableVerticalHeaderView(Qt.Vertical, self)
        self.setVerticalHeader(self._verticalHeader)
        h = self.fontMetrics().height()
        self.verticalHeader().setDefaultSectionSize(3*h/2)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        #self.horizontalHeader().resizeSections(QtGui.QHeaderView.Custom)
        self.horizontalHeader().setStretchLastSection(True)
        self.valueDelegate = CActionPropertyDelegateF088(self.fontMetrics().height(), self)
        self.setItemDelegateForColumn(CF088ActionPropertiesCheckTableModel.ciValue, self.valueDelegate)
        self.evaluationDelegate = CActionPropertyEvaluationDelegate(self.fontMetrics().height(), self)
        self.setItemDelegateForColumn(CF088ActionPropertiesCheckTableModel.ciEvaluation, self.evaluationDelegate)
        self.commentDelegate = CActionPropertyCommentDelegate(self.fontMetrics().height(), self)
        self.setItemDelegateForColumn(CF088ActionPropertiesCheckTableModel.ciComment, self.commentDelegate)
        self.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        self._popupMenu = None
        self._actCopy = None
        self._actCopyCell = None
        #self.resizeColumnsToContents()
        #self.resizeRowsToContents()
        self.preferencesLocal = {}


#    def updatePropertiesTable(self, index, previous=None):
#        if previous:
#            self.savePreferencesLoc(previous.row())
#        row = index.row()
##        self.resizeColumnsToContents()
##        self.resizeRowsToContents()
##        self.horizontalHeader().setStretchLastSection(True)
#        self.loadPreferencesLoc(self.preferencesLocal, row)


    @pyqtSignature('int, int')                                   # см. примечание 1
    def rowCountChanged(self, oldCount, newCount):                      # см. примечание 1
        self.verticalHeader().setUpdatesEnabled(True)                   # см. примечание 1


    def getHeightFactor(self, row):
        propertyTypeList = self.model().propertyTypeList
        if 0 <= row < len(propertyTypeList):
            heightFactor = propertyTypeList[row].editorSizeFactor
            if heightFactor < 0:
                heightFactor = abs(heightFactor)
                return 1.0/heightFactor
            elif heightFactor > 0:
                return heightFactor
        return 1


    def sizeHintForRow(self, row):
        model = self.model()
        if model:
            index = model.index(row, CF088ActionPropertiesCheckTableModel.ciValue)
            heightFactor = self.getHeightFactor(row)
            return max(self.valueDelegate.sizeHint(None, index).height(),
                       self.evaluationDelegate.sizeHint(None, index).height()
                      )*heightFactor+1
        else:
            return -1


    # def sizeHintForColumn(self, column):
    #     if CF088ActionPropertiesCheckTableModel.ciIsAssigned == column:
    #         model = self.model()
    #         headerName = self.horizontalHeader().model().column[column]
    #         headerLen = len(headerName)-1
    #         headerSize = 20
    #         for i in range(headerLen):
    #             headerSize += self.fontMetrics().width(QString(headerName).at(i))
    #         colSizeList = [headerSize]
    #         if model:
    #             propertyTypeList = self.model().propertyTypeList
    #             for row, propertyType in enumerate(propertyTypeList):
    #                 colSizeList.append(self.columnWidth(column))
    #             return max(tuple(colSizeList))
    #         return -1
    #     else:
    #         return QtGui.QTableView.sizeHintForColumn(self, column)


    def createPopupMenu(self, actions=[]):
        self._popupMenu = QtGui.QMenu(self)
        self._popupMenu.setObjectName('popupMenu')
        for action in actions:
            if isinstance(action, QtGui.QAction):
                self._popupMenu.addAction(action)
            elif action == '-':
                self._popupMenu.addSeparator()
        self.connect(self._popupMenu, SIGNAL('aboutToShow()'), self.popupMenuAboutToShow)
        return self._popupMenu


    def popupMenu(self):
        if self._popupMenu is None:
            self.createPopupMenu()
        return self._popupMenu


    def addPopupSeparator(self):
        self.popupMenu().addSeparator()


    def addPopupAction(self, action):
        self.popupMenu().addAction(action)


    def focusInEvent(self, event):
        QtGui.QTableView.focusInEvent(self, event)
        self.updateStatusTip(self.currentIndex())


    def focusOutEvent(self, event):
        self.updateStatusTip(None)
        QtGui.QTableView.focusOutEvent(self, event)


    def updateStatusTip(self, index):
        tip = forceString(index.data(Qt.StatusTipRole)) if index else ''
        event = QtGui.QStatusTipEvent(tip)
        self.setStatusTip(tip)
        QtGui.qApp.sendEvent(self.parent(), event)


    def moveCursor(self, cursorAction, modifiers):
        if cursorAction in (QtGui.QAbstractItemView.MoveNext, QtGui.QAbstractItemView.MoveRight):
            return QtGui.QTableView.moveCursor(self, QtGui.QAbstractItemView.MoveDown, modifiers)
        elif cursorAction in (QtGui.QAbstractItemView.MovePrevious, QtGui.QAbstractItemView.MoveLeft):
            return QtGui.QTableView.moveCursor(self, QtGui.QAbstractItemView.MoveUp, modifiers)
        else:
            return QtGui.QTableView.moveCursor(self, QtGui.QAbstractItemView.CursorAction(cursorAction), modifiers)


    def contextMenuEvent(self, event):
        if self._popupMenu:
            self._popupMenu.exec_(event.globalPos())
            event.accept()
        else:
            event.ignore()


    def addPopupCopyCell(self):
        self._actCopyCell = QtGui.QAction(u'Копировать', self)
        self._actCopyCell.setObjectName('actCopyCell')
        self.connect(self._actCopyCell, SIGNAL('triggered()'), self.copyCurrentCell)
        self.addPopupAction(self._actCopyCell)


    def popupMenuAboutToShow(self):
        currentIndex = self.currentIndex()
        curentIndexIsValid = currentIndex.isValid()
        if self._actCopyCell:
            self._actCopyCell.setEnabled(curentIndexIsValid)


    def copyCurrentCell(self):
        index = self.currentIndex()
        if index.isValid():
            carrier = QMimeData()
            dataAsText = self.model().data(index, Qt.DisplayRole)
            carrier.setText(dataAsText.toString() if dataAsText else '' )
            QtGui.qApp.clipboard().setMimeData(carrier)


    def showHistory(self):
        index = self.currentIndex()
        model = self.model()
        row = index.row()
        if 0<=row<model.rowCount():
            actionProperty = model.getProperty(row)
            dlg = CPropertyHistoryDialog(model.clientId, [(actionProperty, True, True)], self)
            dlg.exec_()


    def showHistoryEx(self):
        index = self.currentIndex()
        model = self.model()
        row = index.row()
        if 0<=row<model.rowCount():
            dlgChooser = CActionPropertyChooser(self, self.model().propertyTypeList)
            if dlgChooser.exec_():
                propertyTypeList = dlgChooser.getSelectedPropertyTypeList()
                if propertyTypeList:
                    dlg = CPropertyHistoryDialog(model.clientId, [(model.action.getProperty(propertyType.name), showUnit, showNorm) for propertyType, showUnit, showNorm in propertyTypeList], self)
                    dlg.exec_()


    def colKey(self, col):
        return unicode('width '+forceString(col.title()))


    def loadPreferencesLoc(self, preferences, row):
        width = 0
        model = self.model()
        nullSizeDetected = False
        if model:
            for i in xrange(model.columnCount()):
                colWidth = forceInt(getPref(preferences, 'row_%d_col_%d' % (row, i), None))
                if colWidth and colWidth > width:
                    self.setColumnWidth(i, colWidth)
                else:
                    if not self.isColumnHidden(i):
                        nullSizeDetected = True

        if nullSizeDetected:
            self.resizeColumnsToContents()
            colCount = model.columnCount()
            for i in range(0, colCount):
                width += self.columnWidth(i)
            self.setColumnWidth(2, width)  # значение


    def savePreferencesLoc(self, row):
        model = self.model()
        if model:
            for i in xrange(model.columnCount()):
                width = self.columnWidth(i)
                setPref(self.preferencesLocal, 'row_%d_col_%d' % (row, i), QVariant(width))
        return self.preferencesLocal


    # def loadPreferences(self, preferences):
    #     width = 0
    #     model = self.model()
    #     self.resizeColumnsToContents()
    #     colCount = model.columnCount()
    #     for i in range(0, colCount):
    #         width += self.columnWidth(i)
    #     self.setColumnWidth(1, width*2)  # значение
    #     for i in range(colCount-1):
    #         if i != 1:
    #             self.setColumnWidth(i, width/2)


    # def savePreferences(self):
    #     preferences = {}
    #     model = self.model()
    #     if model:
    #         for i in xrange(model.columnCount()):
    #             if i == 0:
    #                 width = max(self.columnWidth(i), self.sizeHintForColumn(i))
    #                 self.setColumnWidth(i, width)
    #             else:
    #                 width = self.columnWidth(i)
    #             setPref(preferences, 'col_%d'%i, QVariant(width))
    #     return preferences


class CActionPropertyDelegateF088(CActionPropertyDelegate):
    def __init__(self, lineHeight, parent):
        CActionPropertyDelegate.__init__(self, lineHeight, parent)

    def sizeHint(self, option, index):
        model = index.model()
        row = index.row()
        propertyType = model.getPropertyType(row)
        property = model.action.getPropertyById(propertyType.id)
        preferredHeightUnit, preferredHeight = property.getPreferredHeight()
        result = QSize(10, self.lineHeight * preferredHeight if preferredHeightUnit == 1 else preferredHeight)
        return result
