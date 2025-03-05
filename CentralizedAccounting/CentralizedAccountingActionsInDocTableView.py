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

from PyQt4              import QtGui
from PyQt4.QtCore       import Qt, SIGNAL, QEvent, QVariant
from library.Utils      import forceInt
from library.DateEdit   import CDateEdit
from library.InDocTable import CInDocTableView
from Users.Rights       import urAccessEditCentralizedAccounting


class CCentralizedAccountingActionsItemDelegate(QtGui.QItemDelegate):
    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)
        self.row = 0
        self.lastrow = 0
        self.column = 0
        self.editor = None


    def createEditor(self, parent, option, index):
        editor = index.model().createEditor(index, parent)
        if editor is not None:
            self.connect(editor, SIGNAL('commit()'), self.emitCommitData)
            self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        self.editor   = editor
        self.row = index.row()
        self.rowcount = index.model().rowCount(None)
        self.column   = index.column()
        return editor


    def setEditorData(self, editor, index):
        if editor is not None:
            column = index.column()
            row    = index.row()
            model  = index.model()
            record = None
            for i, group in enumerate(model._groups):
                if row == i:
                    record = group.record
                    break
            if record:
                model.setEditorData(column, editor, model.data(index, Qt.EditRole), record)


    def setModelData(self, editor, model, index):
        if editor is not None:
            column = index.column()
            model.setData(index, index.model().getEditorData(column, editor))
            model.setModelActionsProxyGroupExpanded()


    def emitCommitData(self):
        self.emit(SIGNAL('commitData(QWidget *)'), self.sender())


    def commitAndCloseEditor(self):
        editor = self.sender()
        self.emit(SIGNAL('commitData(QWidget *)'), editor)
        self.emit(SIGNAL('closeEditor(QWidget *,QAbstractItemDelegate::EndEditHint)'), editor, QtGui.QAbstractItemDelegate.NoHint)


    def editorEvent(self, event, model, option, index):
        flags = model.flags(index)
        if not (flags & Qt.ItemIsEnabled and flags & Qt.ItemIsUserCheckable):
            return False

        value = index.data(Qt.CheckStateRole)
        if not value.isValid():
            return False

        if flags & Qt.ItemIsEnabled and flags & Qt.ItemIsEditable:
            return QtGui.QItemDelegate.editorEvent(self, event, model, option, index)

        state = QVariant(Qt.Unchecked if forceInt(value)==Qt.Checked else Qt.Checked)
        eventType = event.type()

        if eventType == QEvent.MouseButtonRelease:
            if self.parent().hasFocus():
                return model.setData(index, state, Qt.CheckStateRole)
            else:
                return False

        if eventType == QEvent.KeyPress:
            if event.key() in (Qt.Key_Space, Qt.Key_Select):
                return model.setData(index, state, Qt.CheckStateRole)
        return QtGui.QItemDelegate.editorEvent(self, event, model, option, index)


    def eventFilter(self, object, event):
        def editorIsEmpty():
            if isinstance(self.editor, QtGui.QLineEdit):
                return self.editor.text() == ''
            if  isinstance(self.editor, QtGui.QComboBox):
                return self.editor.currentIndex() == 0
            if  isinstance(self.editor, CDateEdit):
                return not self.editor.dateIsChanged()
            if  isinstance(self.editor, QtGui.QDateEdit):
                return not self.editor.date().isValid()
            return False

        def editorCanEatTab():
            if  isinstance(self.editor, QtGui.QDateEdit):
                return self.editor.currentSection() != QtGui.QDateTimeEdit.YearSection
            return False

        def editorCanEatBacktab():
            if isinstance(self.editor, QtGui.QDateEdit):
                return self.editor.currentSection() != QtGui.QDateTimeEdit.DaySection
            return False

        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                if editorCanEatTab():
                    self.editor.keyPressEvent(event)
                    return True
                if self.editor is not None:
                    self.parent().commitData(self.editor)
                self.parent().keyPressEvent(event)
                return True
            elif event.key() == Qt.Key_Backtab:
                if editorCanEatBacktab():
                    self.editor.keyPressEvent(event)
                    return True
                if self.editor is not None:
                    self.parent().commitData(self.editor)
                self.parent().keyPressEvent(event)
                return True
            elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
##                event.accept()
                return True
        return QtGui.QItemDelegate.eventFilter(self, object, event)


    def updateEditorGeometry(self, editor, option, index):
        if not isinstance(editor, QtGui.QColorDialog):
            QtGui.QItemDelegate.updateEditorGeometry(self, editor, option, index)
            index.model().afterUpdateEditorGeometry(editor, index)


class CCentralizedAccountingActionsInDocTableView(CInDocTableView):
    __pyqtSignals__ = ('popupMenuAboutToShow()',
                      )

    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)
        self.setItemDelegate(CCentralizedAccountingActionsItemDelegate(self))


    def isCentralizedAccountingActionsPopupMenuEnabled(self):
        if not QtGui.qApp.userHasRight(urAccessEditCentralizedAccounting):
            return False
        index = self.currentIndex()
        model = self.model()
        enabled = False
        row = index.row()
        if row >= 0 and row < len(model._groups) and row < len(model._groups._mapProxyRow2Group):
            group = model._mapProxyRow2Group[row]
            if group:
                proxyRow = group._mapProxyRow2ModelRow[row]
                action = group._mapRow2Item[proxyRow].action
                if not action:
                    return False
                if not action.executionPlanManager.hasItemsToDo():
                    return False
                if action.executionPlanManager.hasItemsToDo() and (forceInt(action._record.value('status')) != 2 and forceInt(action._record.value('status')) != 3):
                    enabled = True
                elif forceInt(action._record.value('status')) == 3 or not action.executionPlanManager.hasItemsToDo():
                    enabled = False
        return enabled


    def setCentralizedAccountingActionsPopupMenu(self, menu):
        if self._popupMenu:
            self.disconnect(self._popupMenu, SIGNAL('aboutToShow()'), self.on_centralizedAccountingActionsPopupMenu_aboutToShow)
        self._popupMenu = menu
        if menu:
            self.connect(menu, SIGNAL('aboutToShow()'), self.on_centralizedAccountingActionsPopupMenu_aboutToShow)


    def on_centralizedAccountingActionsPopupMenu_aboutToShow(self):
        self._popupMenu.setEnabled(self.isCentralizedAccountingActionsPopupMenuEnabled())
        self.emit(SIGNAL('popupMenuAboutToShow()'))

