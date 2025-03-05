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
from PyQt4.QtCore import SIGNAL, pyqtSignature


from library.DialogBase import CDialogBase
from library.Utils import forceBool
from Events.NomenclatureExpense.Ui_NomenclatureExpenseDayDialog import Ui_NomenclatureExpenseDayDialog
from Events.NomenclatureExpense.NomenclatureExpenseItemDelegate import CLocItemDelegate
from Events.NomenclatureExpense.NomenclatureExpenseDayModel import CNomenclatureExpenseDayModel
#, TIME_INDEX, DOSES_INDEX


class CNomenclatureExpenseDayDialog(CDialogBase, Ui_NomenclatureExpenseDayDialog):
    def __init__(self, parent, items, dosageUnitName='', ignoreTime=False):
        assert items
        date = items[0].date
        CDialogBase.__init__(self, parent)
        self._parent = parent
        self._items = items
        self.addModels('NomenclatureExpense', CNomenclatureExpenseDayModel(self, dosageUnitName=dosageUnitName, ignoreTime=ignoreTime))
        self.setupUi(self)
        self.setWindowTitle(u'Суточные назначения: %d.%d.%d' % (date.year(), date.month(), date.day()))
        self.tblNomenlcatureExpense.contextMenuEvent = self._tblContextMenuEvent
        self.setModels(self.tblNomenlcatureExpense, self.modelNomenclatureExpense, self.selectionModelNomenclatureExpense)
        self.tblNomenlcatureExpense.setItemDelegate(CLocItemDelegate(self.tblNomenlcatureExpense))
        h = self.tblNomenlcatureExpense.fontMetrics().height()
        self.tblNomenlcatureExpense.verticalHeader().setDefaultSectionSize(3 * h / 2)
        self.tblNomenlcatureExpense.verticalHeader().hide()
        self.tblNomenlcatureExpense.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self._popupMenu = QtGui.QMenu(self.tblNomenlcatureExpense)
        self._popupMenu.setObjectName('popupMenu')
        self.connect(self._popupMenu, SIGNAL('aboutToShow()'), self.on_popupMenu_aboutToShow)
        self._actDelete = QtGui.QAction(u'Удалить', self.tblNomenlcatureExpense)
        self._popupMenu.addAction(self._actDelete)
        self.connect(self._actDelete, SIGNAL('triggered()'), self.on_delete)
        self.chkApplyChangesCourseNextDays.setChecked(forceBool(QtGui.qApp.preferences.appPrefs.get('NomenclatureExpenseIsApplyChangesCourseNextDays', False)))


    @pyqtSignature('bool')
    def on_chkApplyChangesCourseNextDays_toggled(self, checked):
        self.modelNomenclatureExpense.setApplyChangesCourseNextDays(checked)


    def getApplyChangesCourseNextDays(self):
        return self.modelNomenclatureExpense.getApplyChangesCourseNextDays()


    def _tblContextMenuEvent(self, event):
        if self._popupMenu:
            self._popupMenu.exec_(event.globalPos())
            event.accept()
        else:
            event.ignore()


    def on_popupMenu_aboutToShow(self):
        enable = False
        index = self.tblNomenlcatureExpense.currentIndex()
        if index.isValid():
            row = index.row()
            items = self.modelNomenclatureExpense.items()
            if row >= 0 and row < len(items):
                item = items[row]
                if self.modelNomenclatureExpense._readOnly or item.action or not item.editable:
                    enable = False
                else:
                    enable = True
        self._actDelete.setEnabled(enable)
        self.tblNomenlcatureExpense.emit(SIGNAL('popupMenuAboutToShow()'))


    def on_delete(self):
        rows = [i.row() for i in self.tblNomenlcatureExpense.selectedIndexes()]
        for row in set(rows):
            if not self.modelNomenclatureExpense.removeRow(row):
                QtGui.QMessageBox.warning( self,
                                           u'Внимание!',
                                           u'Невозможно удалить выполненный прием!',
                                           QtGui.QMessageBox.Close)


    def protectWidgetFromEdit(self, isReadOnly):
        isEditable = not isReadOnly
        if hasattr(self, 'modelNomenclatureExpense'):
            self.modelNomenclatureExpense.setReadOnly(isReadOnly)
        if hasattr(self, 'chkApplyChangesCourseNextDays'):
            self.chkApplyChangesCourseNextDays.setEnabled(isEditable)
        if hasattr(self, 'buttonBox'):
            self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(isEditable)


    def load(self, readOnly=False):
        self.modelNomenclatureExpense.load([i.makeCopy() for i in self._items], readOnly=readOnly)


    def itemsToSave(self):
        result = []
        for i in self.modelNomenclatureExpense.items():
            item = i.item
            if item.__origin__:
                item.mergeIntoOrigin()
            result.append(item.getOrigin())
        return result


    def saveData(self):
        return self.modelNomenclatureExpense.items()


    def setDayStatistics(self, planItems, doneItems):
        self.lblDayStatistics.setText(u'Назначено: %i, Выполнено: %i, Осталось: %i'%( planItems,
                                                                                                                            doneItems,
                                                                                                                            planItems-doneItems))
