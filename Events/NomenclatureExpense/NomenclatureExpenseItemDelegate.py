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
from PyQt4.QtCore import QEvent, SIGNAL, Qt, QVariant

from library.Utils import forceInt, forceDate, forceRef, forceStringEx, toVariant
from Events.NomenclatureExpense.Utils import DIREACTION_DATE_INDEX, BEG_DATE_INDEX, NOMENCLATURE_INDEX#, SMNN_INDEX, SMNN_GRLSLF_INDEX
from Events.NomenclatureExpense.NomenclatureExpenseModel import CNomenclatureExpenseModel


class CLocItemDelegate(QtGui.QItemDelegate):
    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)
        self.row = 0
        self.column = 0
        self.editor = None


    def createEditor(self, parent, option, index):
        editor = index.model().createEditor(index, parent)
        column = index.column()
        model = index.model()
        if index.isValid():
            if column in [DIREACTION_DATE_INDEX, BEG_DATE_INDEX] and isinstance(model, CNomenclatureExpenseModel):
                groups = model._groups
                row = index.row()
                if row >= 0 and row < len(groups):
                    if column == BEG_DATE_INDEX:
                        editor.setMinimumDate(forceDate(groups[row].directionDate()))
                    if column == DIREACTION_DATE_INDEX:
                        editor.setMaximumDate(forceDate(groups[row].begDate()))
            elif column == NOMENCLATURE_INDEX and isinstance(model, CNomenclatureExpenseModel):
                groups = model._groups
                row = index.row()
                if row >= 0 and row < len(groups):
                    nomenclatureId = forceRef(model._cellsSettings.getGroupNomenclature(groups[row]))
                    if nomenclatureId:
                        nomenclatureRecord = model.getNomenclatureCaches(nomenclatureId)
                        if nomenclatureRecord:
                            editor.setFindNomenclatureName(forceStringEx(nomenclatureRecord.value('name')))
        if editor is None:
            return None
        self.connect(editor, SIGNAL('commit()'), self.emitCommitData)
        self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        self.editor = editor
        self.row = index.row()
        self.rowcount = index.model().rowCount()
        self.column   = index.column()
        return editor


    def setEditorData(self, editor, index):
        if editor is not None:
            model = index.model()
            model.setEditorData(index, editor)


    def setModelData(self, editor, model, index):
        if editor is not None:
            model.setData(index, toVariant(index.model().getEditorData(index, editor)))


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
                try:
                    self.parent().model()._canAddLastRow = False
                    self.parent().keyPressEvent(event)
                finally:
                    self.parent().model()._canAddLastRow = True
                return True
            elif event.key() == Qt.Key_Backtab:
                if editorCanEatBacktab():
                    self.editor.keyPressEvent(event)
                    return True
                if self.editor is not None:
                    self.parent().commitData(self.editor)
                self.parent().keyPressEvent(event)
                return True
            elif event.key() == Qt.Key_Return:
                return True
        return QtGui.QItemDelegate.eventFilter(self, object, event)
