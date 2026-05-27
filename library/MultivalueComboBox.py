# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, SIGNAL, QAbstractTableModel, QString, QVariant, QObject
from PyQt4.QtGui import QSortFilterProxyModel

from library.Utils import forceBool, forceInt, forceString, forceStringEx, trim

from library.adjustPopup import adjustPopupToWidget
from library.crbcombobox import CRBModelDataCache


class CMultivalueComboBoxView(QtGui.QTableView):
    def __init__(self, parent=None):
        QtGui.QTableView.__init__(self, parent)
        self.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        h = self.fontMetrics().height()
        self.verticalHeader().setDefaultSectionSize(3*h/2)
        self.verticalHeader().hide()
        header = self.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        self.setSelectionBehavior(QtGui.QTableView.SelectRows)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Right):
            self.setCurrentIndex(self.model().index(self.currentIndex().row(), 0))
        elif event.key() == Qt.Key_Up:
            new_row = self.currentIndex().row() - 1 if self.currentIndex().row() else 0
            self.setCurrentIndex(self.model().index(new_row, 0))
        elif event.key() == Qt.Key_Down:
            new_row = self.currentIndex().row() + 1 if self.currentIndex().row() < self.model().rowCount() else self.model().rowCount() - 1
            self.setCurrentIndex(self.model().index(new_row, 0))
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
            self.parent().keyPressEvent(event)
        else:
            QtGui.QTableView.keyPressEvent(self, event)


class CBaseMultivalueComboBoxModel(QAbstractTableModel):
    class CMultivalueItem():
        def __init__(self, value, code, name, isChecked=0):
            self._value = value
            self._isChecked = isChecked
            self._code = code
            self._name = name

        def eq(self, value):
            return self._value == value

        def value(self):
            return self._value

        def setValue(self, value):
            self._value = value

        def code(self):
            return self._code

        def setCode(self, code):
            self._code = code

        def name(self):
            return self._name

        def setName(self, name):
            self._name = name

        def isChecked(self):
            return self._isChecked

        def setIsChecked(self, isChecked):
            self._isChecked = isChecked


    class CMultivalueColumn():
        def __init__(self, model):
            self._model = model
        def model(self):
            return self._model
        def isCheckable(self):
            return False


    class CMultivalueDataColumn(CMultivalueColumn):
        def data(self, item):
            return item.value()

        def isChecked(self, item):
            return None

        def setData(self, item, value):
            item.setValue(value)

        def flags(self, index=None):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    class CMultivalueDataColumnCode(CMultivalueColumn):
        def data(self, item):
            return item.code()

        def isChecked(self, item):
            return None

        def setData(self, item, value):
            item.setValue(value)

        def flags(self, index=None):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    class CMultivalueDataColumnName(CMultivalueColumn):
        def data(self, item):
            return item.name()

        def isChecked(self, item):
            return None

        def setData(self, item, value):
            item.setValue(value)

        def flags(self, index=None):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    class CMultivalueChekedColumn(CMultivalueColumn):
        def data(self, item):
            return None

        def isChecked(self, item):
            return item.isChecked()

        def setIsChecked(self, item, isChecked):
            item.setIsChecked(isChecked)

        def flags(self, index=None):
            if index.isValid():
                result = Qt.ItemIsEnabled | Qt.ItemIsSelectable
                # if forceStringEx(self.model().getDataColumnValue(index.row())):
                #     result |= Qt.ItemIsUserCheckable
                return result
            return Qt.NoItemFlags

        def isCheckable(self):
            return True


    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._checkedColumnIsHidden = False
        self._dataColumn = CBaseMultivalueComboBoxModel.CMultivalueDataColumn(self)
        self._dataColumnCode = CBaseMultivalueComboBoxModel.CMultivalueDataColumnCode(self)
        self._dataColumnName = CBaseMultivalueComboBoxModel.CMultivalueDataColumnName(self)
        self._checkedColumn = CBaseMultivalueComboBoxModel.CMultivalueChekedColumn(self)
        self._columns = [self._checkedColumn, self._dataColumnCode, self._dataColumnName]
        self._items = []
        self._readOnly = False

    def headerData(self, section, orientation, role):
        if len(self._columns) == 3:
            if orientation == Qt.Horizontal:
                if role == Qt.DisplayRole:
                    if section == 0:
                        return QVariant(u'   ')
                    if section == 1:
                        return QVariant(u'Код')
                    elif section == 2:
                        return QVariant(u'Наименование')
            return QVariant()
        else:
            pass

    def setReadOnly(self, value=False):
        self._readOnly = value


    def isReadOnly(self):
        return self._readOnly


    def clear(self):
        self._items = []
        self.reset()


    def getCheckedRows(self):
        return [row for row, item in enumerate(self._items) if item.isChecked()]


    def checkedValueList(self):
        return [item.value() for item in self._items if item.isChecked()]


    def findRowIndex(self, value):
        for rowIndex, item in enumerate(self._items):
            if item.eq(value):
                return rowIndex
        return -1


    def getCheckedColumnIndex(self):
        return self._columns.index(self._checkedColumn)


    def isColumnIndexCheckable(self, index):
        return self._getCol(index.column()).isCheckable()


    def setCheckedColumnIsHiden(self, value):
        self._checkedColumnIsHidden = value
        if hasattr(self, '_proxyModel'):
            #костыль для обновления видимых столбцов в прокси. Должны быть варианты лучше
            self._proxyModel.setSourceModel(self)
            self._proxyModel.enableFilter(forceInt(not value))

    def isCheckedColumnIsHiden(self):
        return self._checkedColumnIsHidden


    def addItem(self, value):
        self._items.append(CBaseMultivalueComboBoxModel.CMultivalueItem(value, '', '', False))
        self._columns = [self._checkedColumn, self._dataColumn]
        self.reset()

    def addList(self, value):
        import re
        self._items.append(CBaseMultivalueComboBoxModel.CMultivalueItem(re.sub(r"\s+", " ", value[0]), value[1], re.sub(r"\s+", " ", value[2]), value[3]))
        self._columns = [self._checkedColumn, self._dataColumnCode, self._dataColumnName]
        self.reset()


    def columnCount(self, index=None):
        return len(self._columns)-1 if self._checkedColumnIsHidden else len(self._columns)


    def itemCount(self):
        return self.rowCount()


    def rowCount(self, index=None):
        return len(self._items)


    def _getCol(self, column):
        return self._columns[1:][column] if self._checkedColumnIsHidden else self._columns[column]


    def getValue(self, row, column):
        return self._getCol(column).data(self._items[row])

    def getDataColumnValue(self, row):
        return self._dataColumn.data(self._items[row])

    def setValue(self, row, column, value):
        return self._getCol(column).setData(self._items[row], value)


    def isChecked(self, row, column):
        return self._getCol(column).isChecked(self._items[row])


    def isItemChecked(self, row):
        return self._checkedColumn.isChecked(self._items[row])


    def setCheckedRows(self, rows):
        for row, item in enumerate(self._items):
            self.setItemChecked(row, False)
        for row in rows:
            if row >= 0:
                self.setData(self.index(row, self.getCheckedColumnIndex()), QVariant(Qt.Checked), role=Qt.CheckStateRole)

    def setAllRowsChecked(self):
        for row, item in enumerate(self._items):
            self.setData(self.index(row, self.getCheckedColumnIndex()), QVariant(Qt.Checked), role=Qt.CheckStateRole)

    def clearItemChecked(self):
        rows = self.getCheckedRows()
        for row in rows:
            self.setItemChecked(row, False)


    def setItemChecked(self, row, value):
        self._checkedColumn.setIsChecked(self._items[row], value)


    def setIsChecked(self, row, column, value):
        self._checkedColumn.setIsChecked(self._items[row], value)


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            column = index.column()
            row    = index.row()
            return QVariant(self.getValue(row, column))

        elif role == Qt.EditRole:
            column = index.column()
            row    = index.row()
            return QVariant(self.getValue(row, column))

        elif role == Qt.CheckStateRole and not self._checkedColumnIsHidden:
            row    = index.row()
            if forceStringEx(self.getDataColumnValue(row)):
                column = index.column()
                if column == self.getCheckedColumnIndex():
                    return QVariant(self.isChecked(row, column))

        elif role == Qt.BackgroundRole:
            if self.isItemChecked(index.row()):
                color = QtGui.QTableView().palette().highlight().color().name()
                return QVariant(QtGui.QBrush(QtGui.QColor(color)))
                # return QVariant(QtGui.QColor(Qt.cyan))

        elif role == Qt.ForegroundRole and index.column() != 0:
            if self.isItemChecked(index.row()):
                color = QtGui.QTableView().palette().highlightedText().color().name()
                return QVariant(QtGui.QBrush(QtGui.QColor(color)))

        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        if role == Qt.CheckStateRole:
            row = index.row()
            column = index.column()
            self.setIsChecked(row, column, forceInt(value))
            self.emitDataCheckedChanged(row, forceBool(value))
            self.emitDataChanged()
            return True

        return False


    def emitDataChanged(self):
        index1 = self.index(0, 0)
        index2 = self.index(self.rowCount(), self.columnCount())
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)


    def emitDataCheckedChanged(self, row, added):
        data = QString(self.getDataColumnValue(row))
        self.emit(SIGNAL('dataCheckedChanged(QString, bool)'), data, added)


    def flags(self, index=None):
        if not index.isValid():
            return Qt.NoItemFlags
        if self._readOnly:
            return Qt.ItemIsEnabled
        return self._getCol(index.column()).flags(index)

class CMultivalueComboBoxModel(CBaseMultivalueComboBoxModel):
    def __init__(self, parent=None):
        CBaseMultivalueComboBoxModel.__init__(self, parent)
    

    def setCheckedColumnIsHiden(self, value):
        self._checkedColumnIsHidden = value
        if hasattr(self, '_proxyModel'):
            #костыль для обновления видимых столбцов в прокси. Должны быть варианты лучше
            self._proxyModel.setSourceModel(self)
            # self._proxyModel.enableFilter(forceInt(not value))
            self._proxyModel.setFilterString(1,"")
            self._proxyModel.setFilterString(2,"")
        
# ##############################################################

class CBaseMultivalueComboBoxPopup(QtGui.QFrame):
    def __init__(self, parent=None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self._parent = parent
        self.vLayout = QtGui.QVBoxLayout(self)
        self._view   = CMultivalueComboBoxView(self)
        self._proxyModel = CBaseMultivalueComboBoxProxyModel()
        self._model  = CBaseMultivalueComboBoxModel(self)
        self._model._proxyModel = self.proxyModel()
        self.proxyModel().setSourceModel(self._model)
        
        self._view.setModel(self._proxyModel)
        self.vLayout.addWidget(self._view)
        self.edtFilter = QtGui.QLineEdit(self)
        self.vLayout.addWidget(self.edtFilter)
        QtCore.QObject.connect(self.edtFilter, QtCore.SIGNAL("textChanged(QString)"),
                               self.proxyModel().setFilterFixedString)
        self.vLayout.setContentsMargins(1, 1, 1, 1)
        
        self.setFrameShape(QtGui.QFrame.Box)
        self.setFrameShadow(QtGui.QFrame.Plain)
        self.setLineWidth(1)
        self.setMidLineWidth(0)
        self.setObjectName("comboPopup")
        self.setStyleSheet("""
            QFrame#comboPopup {
                border: 1px solid gray;
                border-radius: 3px;
            }
        """)
        self.setLayout(self.vLayout)

        self.connect(self._view, SIGNAL('clicked(QModelIndex)'), self.on_viewClicked)


    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
            self.on_viewClicked(self._view.currentIndex())
            self.close()
        else:
            QtGui.QFrame.keyPressEvent(self, event)


    def model(self):
        return self._model

    def proxyModel(self):
        return self._proxyModel

    def view(self):
        return self._view

    

    def on_viewClicked(self, proxyIndex, firstCall=True, clickCheckboxCol=False):
        if proxyIndex.isValid():
            if Qt.ShiftModifier == QtGui.QApplication.keyboardModifiers() and firstCall:
                selectedIndexes = self._view.selectionModel().selectedRows()
                for index in selectedIndexes:
                    self.on_viewClicked(index, False)
                self.proxyModel().setSourceModel(self._model)
            else:
                index = self.proxyModel().mapToSource(proxyIndex)
                row = index.row()
                if self._model.isColumnIndexCheckable(index) and self.getValueByRow(row) and firstCall:
                    if self._model.isColumnIndexCheckable(index):
                        self.on_viewClicked(self.proxyModel().index(proxyIndex.row(), 1), False, True)
                        self._model.emit(SIGNAL('dataCheckedChanged(QString, bool)'), u'', 0)
                        self.proxyModel().setSourceModel(self._model)
                        self._view.selectRow(proxyIndex.row())
                    else:
                        pass
                else:
                    if self.isCheckedColumnIsHiden():
                        self.setValue(self.getValueByRow(row))
                    else:
                        if self.getValueByRow(row):
                            value = QVariant(Qt.Unchecked) if self._model.isItemChecked(index.row()) and (firstCall or clickCheckboxCol) else QVariant(Qt.Checked)
                            self._model.setData(self._model.index(row, self._model.getCheckedColumnIndex()),
                                                                        value,
                                                                        role=Qt.CheckStateRole)
                            if firstCall:
                                self.proxyModel().setSourceModel(self._model)
                                self._view.selectRow(proxyIndex.row())
                        else:
                            rows = self.getCheckedRows()
                            value = QVariant(Qt.Unchecked)
                            checkedColumn = self._model.getCheckedColumnIndex()
                            for row in rows:
                                self._model.setData(self._model.index(row, checkedColumn), value, role=Qt.CheckStateRole)
            if self.isCheckedColumnIsHiden():
                self.close()


    def getCheckedRows(self):
        return self._model.getCheckedRows()


    def setCheckedRows(self, rows):
        self._model.setCheckedRows(rows)


    def getValueByRow(self, row):
        return forceStringEx(self._model.getDataColumnValue(row))


    def setValue(self, value):
        self.emit(SIGNAL('valueSetted(QString)'), QString(value))


    def setCheckedColumnIsHiden(self, value):
        self._model.setCheckedColumnIsHiden(value)


    def isCheckedColumnIsHiden(self):
        return self._model.isCheckedColumnIsHiden()


    def addItem(self, item):
        self._model.addItem(item)

    def addList(self, item):
        self._model.addList(item)


class CMultivalueComboBoxPopup(QtGui.QFrame):
    def __init__(self, parent=None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self._parent = parent
        self.vLayout = QtGui.QVBoxLayout(self)
        self._view   = CMultivalueComboBoxView(self)
        self._proxyModel = CMultivalueComboBoxProxyModel()
        self._model  = CMultivalueComboBoxModel(self)
        self._model._proxyModel = self.proxyModel()
        self.proxyModel().setSourceModel(self._model)
        # self.proxyModel().enableFilter(1)
        # self.proxyModel().enableFilter(2)

        # Горизонтальный
        self.hLayoutFilter = QtGui.QHBoxLayout()
        self.lblFilterCode = QtGui.QLabel(self)
        self.lblFilterName = QtGui.QLabel(self)
        self.lblFilterCode.setText(u'Код')
        self.lblFilterName.setText(u'Наименование')
        self.edtFilterName = QtGui.QLineEdit(self)
        self._view.setModel(self._proxyModel)
        self.vLayout.addWidget(self._view)
        self.edtFilter = QtGui.QLineEdit(self)
        self.hLayoutFilter.addWidget(self.lblFilterCode)
        self.hLayoutFilter.addWidget(self.edtFilter)
        self.hLayoutFilter.addWidget(self.lblFilterName)
        self.hLayoutFilter.addWidget(self.edtFilterName)
        self.hLayoutFilter.setContentsMargins(1, 1, 1, 1)
        self.vLayout.addLayout(self.hLayoutFilter)

        self.hLayoutButtons = QtGui.QHBoxLayout()
        self.btnClearAll = QtGui.QPushButton(self)
        self.btnClearAll.setText(u"Очистить выбор")
        # self.btnClearAll.setSize(100, 20)
        self.btnCheckFiltered = QtGui.QPushButton(self)
        self.btnCheckFiltered.setText(u"Выбрать всё")
        self.hLayoutButtons.addWidget(self.btnClearAll)
        self.hLayoutButtons.addWidget(self.btnCheckFiltered)
        self.hLayoutButtons.setContentsMargins(1, 1, 1, 1)
        self.vLayout.addLayout(self.hLayoutButtons)
        # self.vLayout.addWidget(self.edtFilter)
        # QtCore.QObject.connect(self.edtFilter, QtCore.SIGNAL("textChanged(QString)"),
        #                        self.proxyModel().setFilterFixedString)
        self.edtFilter.textChanged.connect(lambda text: self._proxyModel.setFilterString(1, text))
        self.edtFilterName.textChanged.connect(lambda text: self._proxyModel.setFilterString(2, text))
        self.vLayout.setContentsMargins(1, 1, 1, 1)
        self.setFrameShape(QtGui.QFrame.Box)
        self.setFrameShadow(QtGui.QFrame.Plain)
        self.setLineWidth(1)
        self.setMidLineWidth(0)
        self.setObjectName("comboPopup")
        self.setStyleSheet("""
            QFrame#comboPopup {
                border: 1px solid gray;
                border-radius: 3px;
            }
        """)
        self.setLayout(self.vLayout)

        self.connect(self._view, SIGNAL('clicked(QModelIndex)'), self.on_viewClicked)
        self.connect(self.btnClearAll, SIGNAL('clicked()'), self.on_btnClearAllClicked)
        self.connect(self.btnCheckFiltered, SIGNAL('clicked()'), self.on_btnCheckFilteredClicked)


    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
            # if event.key() != Qt.Key_Enter:
            #     self.on_viewClicked(self._view.currentIndex())
            # elif event.key() == Qt.Key_Enter:
            self.setCheckedRows(self.getCheckedRows())
            if not self.getCheckedRows():
                self._model.emit(SIGNAL('dataCheckedChanged(QString, bool)'), u'', 0)
            self.close()
        else:
            QtGui.QFrame.keyPressEvent(self, event)


    def model(self):
        return self._model

    def proxyModel(self):
        return self._proxyModel

    def view(self):
        return self._view

    def on_viewClicked(self, proxyIndex, firstCall=True, clickCheckboxCol=False):
        if proxyIndex.isValid():
            if Qt.ShiftModifier == QtGui.QApplication.keyboardModifiers() and firstCall:
                selectedIndexes = self._view.selectionModel().selectedRows()
                for index in selectedIndexes:
                    self.on_viewClicked(index, False)
                self.proxyModel().setSourceModel(self._model)
            else:
                index = self.proxyModel().mapToSource(proxyIndex)
                row = index.row()
                if self._model.isColumnIndexCheckable(index) and self.getValueByRow(row) and firstCall:
                    if self._model.isColumnIndexCheckable(index):
                        self.on_viewClicked(self.proxyModel().index(proxyIndex.row(), 1), False, True)
                        self._model.emit(SIGNAL('dataCheckedChanged(QString, bool)'), u'', 0)
                        self.proxyModel().setSourceModel(self._model)
                        self._view.selectRow(proxyIndex.row())
                    else:
                        pass
                else:
                    if self.isCheckedColumnIsHiden():
                        self.setValue(self.getValueByRow(row))
                    else:

                        if self.getValueByRow(row):
                            # value = QVariant(Qt.Unchecked) if self._proxyModel.isItemChecked(proxyIndex.row()) and firstCall else QVariant(Qt.Checked)
                            value = QVariant(Qt.Unchecked) if self._model.isItemChecked(index.row()) and (firstCall or clickCheckboxCol) else QVariant(Qt.Checked)
                            self._model.setData(self._model.index(row, self._model.getCheckedColumnIndex()),
                                                                        value,
                                                                        role=Qt.CheckStateRole)
                            # self._proxyModel.setData(self._proxyModel.index(proxyIndex.row(), 0),
                            #                     value,
                            #                     role=Qt.CheckStateRole)
                            if firstCall:
                                self.proxyModel().setSourceModel(self._model)
                                self._view.selectRow(proxyIndex.row())
                        else:
                            rows          = self.getCheckedRows()
                            value         = QVariant(Qt.Unchecked)
                            checkedColumn = self._model.getCheckedColumnIndex()
                            for row in rows:
                                self._model.setData(self._model.index(row, checkedColumn), value, role=Qt.CheckStateRole)


    def getCheckedRows(self):
        return self._model.getCheckedRows()


    def setCheckedRows(self, rows):
        self._model.setCheckedRows(rows)


    def getValueByRow(self, row):
        return forceStringEx(self._model.getDataColumnValue(row))


    def setValue(self, value):
        self.emit(SIGNAL('valueSetted(QString)'), QString(value))


    def setCheckedColumnIsHiden(self, value):
        self._model.setCheckedColumnIsHiden(value)


    def isCheckedColumnIsHiden(self):
        return self._model.isCheckedColumnIsHiden()


    def addItem(self, item):
        self._model.addItem(item)

    def addList(self, item):
        self._model.addList(item)

    def on_btnCheckFilteredClicked(self):
        for row in range(self.proxyModel().rowCount()):
            model_index = self.proxyModel().mapToSource(self.proxyModel().index(row, 0))
            model_row = model_index.row()
            self.model().setItemChecked(model_row, 2)
        # self.model().setAllRowsChecked()
        self.proxyModel().setSourceModel(self.model())
        self.model().emit(SIGNAL('dataCheckedChanged(QString, bool)'), u'', 0)

    def on_btnClearAllClicked(self):
        self.model().clearItemChecked()
        self.proxyModel().setSourceModel(self.model())
        self.model().emit(SIGNAL('dataCheckedChanged(QString, bool)'), u'', 0)
        # self.close()
    
# ################################################################


class CBaseMultivalue():
    def __init__(self, multivalue=True):
        self._popupView = CBaseMultivalueComboBoxPopup(self)
        self._model = self._popupView.model()
        self.setModel(self._model)
        self.preferredWidth = 100
        self.setMultivalueChecking(multivalue)
        self.connect(self._model, SIGNAL('dataCheckedChanged(QString, bool)'), self.on_dataCheckedChanged)
        self.connect(self._popupView, SIGNAL('valueSetted(QString)'), self.on_valueSetted)
        self.readOnly = False


    def setReadOnly(self, value=False):
        self.readOnly = value
        self._model.setReadOnly(self.readOnly)


    def isReadOnly(self):
        return self.readOnly


    def isCheckedColumnIsHiden(self):
        return self._popupView.isCheckedColumnIsHiden()


    def setValue(self, value):
        value = forceString(value)
        if self.isCheckedColumnIsHiden():
            if self.isEditable():
                rowIndex = self._model.findRowIndex(value)
                self.setCurrentIndex(rowIndex)
                self.setEditText(value)
            else:
                rowIndex = self._model.findRowIndex(value)
                self.setCurrentIndex(rowIndex)
        else:
            valueList = [trim(val) for val in value.split(u'‚')]   # изменяю разделитель строки с простой запятой на "нижняя одиночная кавычка" http://htmlbook.ru/samhtml/tekst/spetssimvoly
            for value in valueList:
                rowIndex = self._model.findRowIndex(value)
                if rowIndex >= 0:
                    modelIndex = self._model.index(rowIndex, self._model.getCheckedColumnIndex())
                    value      = QVariant(Qt.Checked)
                    self._model.setData(modelIndex, value, role=Qt.CheckStateRole)



    def setEditable(self, value, readOnly=False):
        QtGui.QComboBox.setEditable(self, value)
        if self.isEditable():
            self.lineEdit().setReadOnly(readOnly)


    # Волшебство?
    # По какой-то причине, в во время QComboBox.focusOutEvent и если значени идентично элементу из списка combobox-а,
    # срабатывает сигнал editTextChanged при этом как аргумент передается пустая строка.
    # Откуда такое происходит пока не ясно, ввиду этого поставлена данная заплатка.
    def focusOutEvent(self, event):
        currentText = trim(self.text())
        QtGui.QComboBox.focusOutEvent(self, event)
        if not trim(self.text()) and currentText:
            self.setValue(currentText)


    def on_valueSetted(self, value):
        self.setValue(trim(value))


    def on_dataCheckedChanged(self, data, added):
        if self._model.checkedValueList():
            if "|" in self._model.checkedValueList()[0]:
                newTextValue = u'‚ '.join("|".join([checkedVal.split('|')[1], checkedVal.split('|')[2]]) for checkedVal in self._model.checkedValueList() if checkedVal) # изменяю разделитель строки с простой запятой на "нижняя одиночная кавычка" http://htmlbook.ru/samhtml/tekst/spetssimvoly
                newToolTip   = u'\n'.join("|".join([checkedVal.split('|')[1], checkedVal.split('|')[2]]) for checkedVal in self._model.checkedValueList() if checkedVal)
                self.setEditText(newTextValue)
                self.setToolTip(newToolTip)
            else:
                newTextValue = u'‚ '.join(checkedVal for checkedVal in self._model.checkedValueList() if checkedVal)
                self.setEditText(newTextValue)
        else:
            newTextValue = u''
            self.setEditText(newTextValue)
            self.setToolTip(newTextValue)


#        data = trim(data)
#        if data:
#            currentTextValue = forceStringEx(self.currentText())
#            if added:
#                if data not in self.checkedValueList():
#                    newTextValue = u', '.join([data, currentTextValue]) if currentTextValue else data
#                else:
#                    newTextValue = currentTextValue
#            else:
#                newTextValue = u', '.join([trim(value) for value in currentTextValue.split(',') if trim(value) != data])
#            self.setEditText(newTextValue)


    def checkedValueList(self):
        return self._model.checkedValueList()
    
    
    def calculatePopupWidth(self, view):
        header = view.horizontalHeader()
        totalColWidth = header.length()
        vs = view.verticalScrollBar()
        scrollbarWidth = vs.isVisible() and vs.sizeHint().width() or 0
        frame = view.frameWidth() * 2                            
        return totalColWidth + scrollbarWidth + frame + 8


    def showPopup(self):
        if not self.isReadOnly():
            totalItems = self.itemCount()
            if totalItems:
                view = self._popupView.view()
                view.clearSelection()
                selectionModel = view.selectionModel()
                proxyModel = self._popupView.proxyModel()
                command = QtGui.QItemSelectionModel.Select|QtGui.QItemSelectionModel.Current|QtGui.QItemSelectionModel.Rows
                if self.isCheckedColumnIsHiden():
                    row = max(0, self.currentIndex())
                    selectionModel.setCurrentIndex(self._model.index(row, 0), command)
                else:
                    for row in self._model.getCheckedRows():
                        proxyIndex = proxyModel.mapFromSource(self._model.index(row, 0))
                        selectionModel.setCurrentIndex(proxyIndex, command)
                    if not selectionModel.hasSelection():
                        selectionModel.setCurrentIndex(proxyModel.index(0, 0), command)
                tblHeaderHeight = view.horizontalHeader().height()
                maxVisibleItems = self.maxVisibleItems()
                visibleItems = min(maxVisibleItems, totalItems)
                cols = view.model().columnCount()
                for col in range(cols):
                    view.resizeColumnToContents(col)
                popupWidth = self.calculatePopupWidth(view)
                if visibleItems > 0:
                    if self._popupView.proxyModel().rowCount() > 0:
                        view.setFixedHeight(view.rowHeight(0) * visibleItems + tblHeaderHeight + 5)
                adjustPopupToWidget(self, self._popupView, True, max(self.preferredWidth, popupWidth), view.height() + 2)
                self._popupView.show()
                view.setFocus()
                view.horizontalScrollBar().setValue(0)


    def itemCount(self):
        return self._model.itemCount()


    def addItems(self, items):
        for item in items:
            self.addItem(item)


    def addItem(self, item):
        self._popupView.view().horizontalHeader().hide()
        self._popupView.addItem(item)
        self.on_dataCheckedChanged(1, 1)


    def addList(self, item):
        for i in item:
            self._popupView.addList(i)
        self.on_dataCheckedChanged(1, 1)


    def setMultivalueChecking(self, value):
        self.setCheckedColumnIsHiden(not value)
        self.setEditable(value, value)


    def setCheckedColumnIsHiden(self, value):
        self._popupView.setCheckedColumnIsHiden(value)


    def clear(self):
        self._model.clear()
        QtGui.QComboBox.clear(self)


    def clearItemChecked(self):
        self._model.clearItemChecked()


class CMultivalueComboBox(CBaseMultivalue, QtGui.QComboBox):
    def __init__(self, parent=None):
        QtGui.QComboBox.__init__(self, parent)
        self._popupView = CMultivalueComboBoxPopup(self)
        self._model = self._popupView.model()
        self.setModel(self._model)
        self.preferredWidth = 100
        self.setMultivalueChecking(True)
        self.connect(self._model, SIGNAL('dataCheckedChanged(QString, bool)'), self.on_dataCheckedChanged)
        self.connect(self._popupView, SIGNAL('valueSetted(QString)'), self.on_valueSetted)
        self.readOnly = False


    def text(self):
        return unicode(self.currentText())
    
    def getCheckedRows(self):
        return self._popupView.getCheckedRows()
    
    def setCheckedRows(self, rows):
        self._popupView.setCheckedRows(rows)

    value = text


class CRBMultivalueComboBox(CMultivalueComboBox):
    def __init__(self, parent=None):
        CMultivalueComboBox.__init__(self, parent)
        self._tableName = ''
        self._addNone   = True
        self._needCache = True
        self._filter    = ''
        self._order     = ''
        self._specialValues = None
        self._data = None
        self._mapShown2Id = {}
        self._mapId2Shown = {}

        # Добавил возможность сортировка по столбцам
        QObject.connect(self._popupView._view.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)
        self.colSorting = {}

    def setSort(self, col):
        preOrder = self.colSorting.get(col, None)
        name = 'code'
        if col == 1:
            name = 'code'
        elif col == 2:
            name = 'name'
        self.colSorting[col] = 'DESC' if preOrder and preOrder == 'ASC' else 'ASC'
        self._order = ' '.join([name, self.colSorting[col]])
        header = self._popupView._view.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(col, Qt.AscendingOrder if self.colSorting[col] == 'ASC' else Qt.DescendingOrder)
        self._initRB()


    def clearValue(self):
        self.clearItemChecked()
        self.setEditText(u'')


    def _translateShownValue2Value(self, value):
        value = u'‚ '.join(checkedVal for checkedVal in self._model.checkedValueList() if checkedVal)
        if value:
            shownItems = [trim(item) for item in value.split(u'‚')] # изменяю разделитель строки с простой запятой на "нижняя одиночная кавычка" http://htmlbook.ru/samhtml/tekst/spetssimvoly
            if shownItems:
                value = [self._mapShown2Id[shownItem] for shownItem in shownItems]
                if value:
                    return u', '.join(value)
        return ''


    def _translateValue2ShownValue(self, value):
        if value:
            if not isinstance(value, list):
                idList = [trim(id.replace(' ', '')) for id in value.split(',')]
            else:
                idList = value
            if idList:
                value = [self._mapId2Shown[id] for id in idList]
                if value:
                    return u'‚ '.join(value) # потом в setValue сплитить не получается
        return u''


    def _initRB(self):
        import re
        self._data = CRBModelDataCache.getData(self._tableName,
                                               self._addNone,
                                               self._filter,
                                               self._order,
                                               self._specialValues,
                                               self._needCache)

        shownItems = []
        for itemIndex in xrange(self._data.getCount()):
            id = self._data.getId(itemIndex)
            shown = u' | '.join([unicode(self._data.getId(itemIndex)), unicode(self._data.getCode(itemIndex)), unicode(self._data.getName(itemIndex))])

            items = []

            code = unicode(self._data.getCode(itemIndex))
            name = unicode(self._data.getName(itemIndex))
            chBox = 2 if shown in self.checkedValueList() else 0

            items.append(shown)
            items.append(code)
            items.append(name)
            items.append(chBox)

            self._mapId2Shown[str(id)] = re.sub(r"\s+", " ", shown) #избавляемся от лишних пробелов...
            self._mapShown2Id[re.sub(r"\s+", " ", shown)] = unicode(id)

            shownItems.append(items)

        self.clear()
        self.addList(shownItems)

    def _setHorisontalTable(self):
        db = QtGui.qApp.db
        where = (' WHERE ' + self._filter) if self._filter else ''

        query = db.query("""
        SELECT 
        (SELECT LENGTH(code) FROM {0} {1} GROUP BY code ORDER BY LENGTH(code) DESC LIMIT 1) AS code,
        (SELECT LENGTH(name) FROM {2} {3} GROUP BY name ORDER BY LENGTH(name) DESC LIMIT 1) AS name;
        """.format(self._tableName, where, self._tableName, where))

        while query.next():
            prefWidthCode = query.record().value(0).toInt()[0]
            prefWidthName = query.record().value(1).toInt()[0]

        self._popupView.view().setColumnWidth(0, 30) # Изменяем ширину первого столбца
        self._popupView.view().setColumnWidth(1, 80 + (prefWidthCode * 2)) # Изменим ширину столбца code
        self._popupView.view().setColumnWidth(2, prefWidthName * 2) # Изменим ширину столбца name

        self._popupView.view().setMinimumWidth(int((20 + prefWidthName) * 2) * 2)

        self.preferredWidth = (prefWidthCode + prefWidthName) * 2 # Изменяем ширину второго столбца


    def setTable(self, tableName, addNone=False, filter='', order=None, specialValues=None, needCache=True):
        self._tableName = tableName
        self._addNone   = addNone
        self._filter    = filter
        self._order     = order
        self._needCache = needCache
        self._specialValues = specialValues
        self._setHorisontalTable()
        self._initRB()


    def setText(self, value):
        self.setValue(value)


    def setValue(self, value):
        CMultivalueComboBox.setValue(self, self._translateValue2ShownValue(value))


    def text(self):
        return self.value()


    def value(self):
        return self._translateShownValue2Value(CMultivalueComboBox.value(self))


class CBaseMultivalueComboBoxProxyModel(QSortFilterProxyModel):
    def __init__(self,parent=None):
        QtGui.QProxyModel.__init__(self, parent)
        self.filter_strings = {}

    def enableFilter(self, column):
        self.setFilterKeyColumn(column)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)

    def getCheckedColumnIndex(self):
        return self.sourceModel()._columns.index(self.sourceModel()._checkedColumn)

    def setIsChecked(self, row, column, value):
        self.sourceModel()._checkedColumn.setIsChecked(self.sourceModel()._items[row], value)

    def isItemChecked(self, row):
        return self.sourceModel()._checkedColumn.isChecked(self.sourceModel()._items[row])

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        if role == Qt.CheckStateRole:
            row = index.row()
            column = index.column()
            self.setIsChecked(row, column, forceInt(value))
            self.emitDataCheckedChanged(row, forceBool(value))
            self.emitDataChanged()
            return True

        return False

    def emitDataChanged(self):
        index1 = self.index(0, 0)
        index2 = self.index(self.rowCount(), self.columnCount())
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)


    def emitDataCheckedChanged(self, row, added):
        data = QString(self.getDataColumnValue(row))
        self.emit(SIGNAL('dataCheckedChanged(QString, bool)'), data, added)

    def getDataColumnValue(self, row):
        return self.sourceModel()._dataColumn.data(self.sourceModel()._items[row])

    # def setSourceModel(self, model):
    #     QSortFilterProxyModel.setSourceModel(self, model)


class CMultivalueComboBoxProxyModel(CBaseMultivalueComboBoxProxyModel):
    def __init__(self,parent=None):
        CBaseMultivalueComboBoxProxyModel.__init__(self, parent)
        self.filter_strings = {}

    def enableFilter(self, column):
        pass

    def setFilterString(self, column, filter_string):
        self.filter_strings[column] = filter_string
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        source_model = self.sourceModel()
        for column, filter_string in self.filter_strings.items():
            if filter_string:
                value = source_model.data(source_model.index(source_row, column), Qt.DisplayRole)
                if forceString(filter_string).lower() not in forceString(value).lower():
                    return False

        return True


if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    cmb = CMultivalueComboBox()
#    cmb.setMultivalueChecking(False)
    cmb.addItems(
        [
            u'12sdklmsdl;dlsdkl;vdl;vsdlvsdmlvsdlfddfdfdf3',
            u'23412sdklmsdl;dlsdkl;vdl;vsdlvsdmlvdfsdfsdsdl',
            '',
            '345'
        ])
    cmb.show()
    app.exec_()


class CRecordMultivalueComboBox(CMultivalueComboBox):
    u"""Класс для работы с полями в таблице с множественным выбором из заранее определенного списка значений"""
    def __init__(self, parent=None):
        CMultivalueComboBox.__init__(self, parent)
        self._mapShown2Id = {}
        self._mapId2Shown = {}
        self._checkedDict = {}
        self._byDict = False
        pv = self._popupView
        for widget in (pv.lblFilterCode, pv.lblFilterName, pv.edtFilter, pv.edtFilterName):
            widget.setVisible(False)

    def enableFilter(self, enable):
        pv = self._popupView
        for widget in (pv.lblFilterCode, pv.lblFilterName, pv.edtFilter, pv.edtFilterName):
            widget.setVisible(enable)
        
    def clearValue(self):
        self.clearItemChecked()
        self.setEditText(u'')
    
    
    def setTable(self, tableName, cols):
        from collections import OrderedDict
        import re
        cols = list(cols)
        if len(cols) == 1:
            cols.insert(0, 'id')
        if len(cols) == 2:
            values = OrderedDict()
            db = QtGui.qApp.db
            table = db.table(tableName)
            records = db.getRecordList(table, cols, order=cols[0])
            for record in records:
                value = forceString(record.value(1))
                key = forceString(record.value(0))
                if '\n' in value:
                    value = value.replace('\n', '').replace('\r', '') #для нестандартных значений...
                    value = re.sub(r'\s+', ' ', value)
                values[key] = value
        self.setItems(values)

        
    
    def setItems(self, values):
        shownItems = []
        if isinstance(values, (list, tuple)):
            self._byDict = False
            for id, value in enumerate(values):
                items = [value, forceString(id+1), value, 0]
                self._mapId2Shown[forceString(id+1)] = value 
                self._mapShown2Id[value] = unicode(id+1)
                shownItems.append(items)
        elif isinstance(values, dict):
            self._byDict = True
            for id, value in values.items():
                items = [value, id, value, 0]
                self._mapId2Shown[id] = value 
                self._mapShown2Id[value] = id
                shownItems.append(items)
        self.clear()
        #self.addItems(values)
        self.addList(shownItems)
        self.setCheckedDict()
        self._setHorisontalTable()


    def _setHorisontalTable(self):
        prefWidthCode = max(len(k) for k in self._mapId2Shown.keys()) if self._mapId2Shown.keys() else 10
        prefWidthName = max(len(v) for v in self._mapId2Shown.values()) if self._mapId2Shown.values() else 10
        pv = self._popupView.view()
        pv.setColumnWidth(0, 30)
        pv.setColumnWidth(1, 80 + (prefWidthCode * 2))
        pv.setColumnWidth(2, prefWidthName * 2)
        pv.setMinimumWidth(int((20 + prefWidthName) * 2) * 2)
        self.preferredWidth = (prefWidthCode + prefWidthName) * 2 


    def _translateShownValue2Value(self, value):
        value = u'‚ '.join(checkedVal for checkedVal in self._model.checkedValueList() if checkedVal)
        if value:
            shownItems = [trim(item) for item in value.split(u'‚')] # изменяю разделитель строки с простой запятой на "нижняя одиночная кавычка" http://htmlbook.ru/samhtml/tekst/spetssimvoly
            if shownItems:
                value = [self._mapShown2Id[shownItem] for shownItem in shownItems]
                if value:
                    return u', '.join(value)
        return ''


    def _translateValue2ShownValue(self, value):
        if value:
            if not isinstance(value, list):
                idList = [trim(id.replace(' ', '')) for id in value.split(',')]
            else:
                idList = value
            if idList:
                value = [self._mapId2Shown[forceString(id)] for id in idList]
                self.setCheckedDict(value, True)
                if value:
                    return u'‚ '.join(value) # потом в setValue сплитить не получается
        return u''


    def setText(self, value):
        self.setValue(value)


    def setValue(self, value):
        CMultivalueComboBox.setValue(self, self._translateValue2ShownValue(value))


    def text(self):
        return self.value()


    def value(self):
        return self._translateShownValue2Value(CMultivalueComboBox.value(self))
    
    def getIndex(self, value):
        if value:
            if isinstance(value, list):
                value = value[0]
            if self._byDict:
                return forceString(self._mapShown2Id[value])
            else:
                return forceString(forceInt(self._mapShown2Id[value])-1)
        return -1
    
    def setCheckedDict(self, value=None, init=False):
        if value:
            checkedList = value
        else:
            checkedList = self.checkedValueList()
        rows = []
        for key, value in self._mapShown2Id.items():
            if key in checkedList:
                rows.append(self._model.findRowIndex(key))    
                checked = True
            else:
                checked = False
            if self._byDict:
                self._checkedDict[forceString(value)] = checked
            else:
                self._checkedDict[forceString(forceInt(value)-1)] = checked
        if init:
            self.setCheckedRows(rows)
    
    def getCheckedDict(self):
        return self._checkedDict
    
    def on_dataCheckedChanged(self, data, added):
        self.setCheckedDict()
        CMultivalueComboBox.on_dataCheckedChanged(self, data, added)

