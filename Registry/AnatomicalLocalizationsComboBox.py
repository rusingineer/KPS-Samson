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
from PyQt4.QtCore import Qt, QEvent, SIGNAL, pyqtSignature, QModelIndex
from library.SortFilterProxyTreeModel import CSortFilterProxyTreeModel

from library.crbcombobox  import CRBModelDataCache, CRBComboBox
from library.InDocTable   import CInDocTableCol
from library.TreeComboBox import CTreeComboBox, CTreeComboBoxGetIdSetIdMixin
from library.TreeModel    import CDBTreeModel
from library.Utils import forceRef, forceStringEx, toVariant, forceInt

from Events.Ui_AnatomicalLocalizationsComboBoxPopup import Ui_AnatomicalLocalizationsComboBoxPopup


class CAnatomicalLocalizationsModel(CDBTreeModel):
    def __init__(self, parent, filter=None):
        CDBTreeModel.__init__(self, parent, 'rbAnatomicalLocalizations', 'id', 'group_id', 'name', order='code', filter=filter)
        self.setRootItemVisible(False)
        self.setLeavesVisible(True)
        self.searchFilter = None


class CAnatomicalLocalizationsComboBox(CTreeComboBoxGetIdSetIdMixin, CTreeComboBox):
    def __init__(self, parent, filter=None):
        CTreeComboBox.__init__(self, parent)
        self.SizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
        self._model = CAnatomicalLocalizationsModel(self, filter=filter)
        self.filter = filter
        self.setModel(self._model)
        self.searchParent = None
        self.readOnly = False
        self._popup = None
        self.values = []


    def setReadOnly(self, value=False):
        self.readOnly = value
        self._model.setReadOnly(self.readOnly)


    def isReadOnly(self):
        return self.readOnly


    def focusInEvent(self, event):
        QtGui.QComboBox.focusInEvent(self, event)


    def showPopup(self):
        if not self.isReadOnly():
            if not self._popup:
                self._popup = CAnatomicalLocalizationsComboBoxPopup(self, self.filter)
                self._popup.selectIdList = self.values
                for itemId in self._popup.selectIdList:
                    if itemId == 'None':
                        itemId = None 
                    index = self._popup.tableModel.sourceModel().findItemId(forceInt(itemId))
                    if index:
                        self._popup.tableSelectionModel.select(index, self._popup.tableSelectionModel.Select)
                        parentIndex = self._popup.tableModel.parent(index)
                        while parentIndex != QModelIndex():
                            self._popup.tblAnatomicalLocalizations.expand(parentIndex)
                            parentIndex = self._popup.tableModel.parent(parentIndex)
                self.connect(self._popup, SIGNAL('selectionChanged()'), self.setValues)
                self.connect(self._popup, SIGNAL('editingFinished()'), self.emitEditingFinished)
            pos = self.rect().bottomLeft()
            pos2 = self.rect().topLeft()
            pos = self.mapToGlobal(pos)
            pos2 = self.mapToGlobal(pos2)
            size = self._popup.sizeHint()
            width = max(size.width(), self.width())
            size.setWidth(width)
            screen = QtGui.QApplication.desktop().availableGeometry(pos)
            pos.setX(max(min(pos.x(), screen.right() - size.width()), screen.left()))
            pos.setY(max(min(pos.y(), screen.bottom() - size.height()), screen.top()))
            self._popup.move(pos)
            self._popup.resize(size)
            self._popup.show()


    def emitEditingFinished(self):
        self.emit(SIGNAL('editingFinished()'))


    def setValues(self):
        self.values = self._popup.values()


    def value(self):
        return ','.join([str(item) for item in self.values])


    def keyPressEvent(self, event):
        if self._model.isReadOnly():
            event.accept()
        else:
            if event.key() == Qt.Key_Space:
                self.showPopup()
            else:
                key = event.key()
                if key == Qt.Key_Escape:
                    event.ignore()
                elif key in (Qt.Key_Return, Qt.Key_Enter):
                    event.ignore()
                if key in (Qt.Key_Delete, Qt.Key_Clear):
                    self.values = []
                    event.accept()
                    self.emit(SIGNAL('editingFinished()'))
                elif key == Qt.Key_Space:
                    QtGui.QComboBox.keyPressEvent(self, event)
                else:
                    QtGui.QComboBox.keyPressEvent(self, event)


class CAnatomicalLocalizationsInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width):
        CInDocTableCol.__init__(self, title, fieldName, width)


    def toString(self, val, record):
        cache = CRBModelDataCache.getData('rbAnatomicalLocalizations', True)
        text = cache.getStringById(forceRef(val), CRBComboBox.showName)
        return toVariant(text)


    def toStatusTip(self, val, record):
        cache = CRBModelDataCache.getData('rbAnatomicalLocalizations', True)
        text = cache.getStringById(forceRef(val), CRBComboBox.showCodeAndName)
        return toVariant(text)


    def createEditor(self, parent):
        editor = CAnatomicalLocalizationsComboBox(parent)
        editor.model().getRootItem()._name = u'не задано'
        return editor


    def setEditorData(self, editor, value, record):
        editor.setValue(forceRef(value))


    def getEditorData(self, editor):
        return toVariant(editor.value())


class CAnatomicalLocalizationsComboBoxPopup(QtGui.QFrame, Ui_AnatomicalLocalizationsComboBoxPopup):
    __pyqtSignals__ = ('ContractFindCodeSelected(int)',
                      )
    def __init__(self, parent = None, filter={}):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.filter = filter
        self.tableModel = CFilterModel(self, CAnatomicalLocalizationsModel(self, filter=filter))
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblAnatomicalLocalizations.setModel(self.tableModel)
        self.tblAnatomicalLocalizations.setSelectionModel(self.tableSelectionModel)
        self.selectIdList = []


    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent is not None:
            opt = QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos()):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)


    def closeEvent(self, event):
        QtGui.QFrame.closeEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.tblAnatomicalLocalizations:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
        return QtGui.QFrame.eventFilter(self, watched, event)
    

    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.selectIdList = []
            for selectIndex in self.tblAnatomicalLocalizations.selectedIndexes():
                if selectIndex.isValid():
                    itemId = self.tableModel.itemId(selectIndex)
                    if itemId:
                        self.selectIdList.append(itemId)
            self.emit(SIGNAL('selectionChanged()'))
            self.emit(SIGNAL('editingFinished()'))
            self.close()
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.emit(SIGNAL('editingFinished()'))
            self.close()

    def values(self):
        return self.selectIdList
    
    
    @pyqtSignature('QString')
    def on_edtFindWord_textChanged(self, text):
        words = forceStringEx(text)
        if words:
            self.tableModel.filterName = words
        else:
            self.tableModel.filterName = ''

        self.tableModel.invalidateFilter()


class CFilterModel(CSortFilterProxyTreeModel):
    def __init__(self, parent, sourceModel):
        CSortFilterProxyTreeModel.__init__(self, parent, sourceModel)
        self.filterName = ''


    def data(self, index, role=Qt.DisplayRole):
        if self.filterName:
            self.parent().tblAnatomicalLocalizations.expand(index)
        return CSortFilterProxyTreeModel.data(self, index, role)

    def acceptItem(self, item):
        result = True
        if self.filterName:
            result = result and (item.name().upper().find(self.filterName.upper()) != -1)
        return result


    def hasFilters(self):
        return bool(self.filterName)