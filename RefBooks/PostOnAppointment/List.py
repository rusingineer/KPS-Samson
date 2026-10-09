# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, SIGNAL, pyqtSignature, QObject

from library.ItemsListDialog import CItemsListDialog, CItemEditorDialog
from library.interchange     import setLineEditValue, getLineEditValue
from library.TableModel import CTextCol
from library.DialogBase import CDialogBase
from library.Utils           import forceInt
from RefBooks.Tables         import rbCode

from .Ui_PostOnAppointmentEditor import Ui_PostOnAppointmentEditorDialog
from .Ui_PostOnAppointmentList import Ui_PostOnAppointmentList


class CPostOnAppointmentList(Ui_PostOnAppointmentList, CItemsListDialog, CDialogBase):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',          [rbCode], 10),
            CTextCol(u'Наименование', ['post_name'], 40),
            ], 'GetPositionList', [rbCode, 'post_name'])
        self.setWindowTitleEx(u'Контроль должностей при записи на прием')

    def postSetupUi(self):
        CItemsListDialog.postSetupUi(self)
        self.btnNew.setVisible(False)
        self.btnEdit.setVisible(False)

    def setup(self, *args, **kw):
        CItemsListDialog.setup(self, *args, **kw)
        self.setModels(self.tblItems_2, self.model, self.selectionModel)
        self.setModels(self.tblItems_3, self.model, self.selectionModel)
        self.setModels(self.tblItems_4, self.model, self.selectionModel)
        self.setModels(self.tblItems_5, self.model, self.selectionModel)
        shortcutEdt = QtGui.QShortcut(QtGui.QKeySequence('F4'), self)
        shortcutEdt.activated.connect(self.on_btnEdit_clicked)
        shortcutNew = QtGui.QShortcut(QtGui.QKeySequence('F9'), self)
        shortcutNew.activated.connect(self.on_btnNew_clicked)
        QObject.connect(
            self.tblItems_2.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)
        QObject.connect(
            self.tblItems_3.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)
        QObject.connect(
            self.tblItems_4.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)
        QObject.connect(
            self.tblItems_5.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)

    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self):
        self.renewListAndSetTo()

    def select(self, props={}):
        db = QtGui.qApp.db
        table = self.model.table()
        tab = self.tabWidget.currentIndex()
        cond = None
        if tab == 0:
            cond = table['code_last'].eq(12)
        elif tab == 1:
            cond = table['code_last'].eq(11)
        elif tab == 2:
            cond = table['code_last'].eq(13)
        elif tab == 3:
            cond = table['code_last'].eq(14)
        elif tab == 4:
            cond = table['code_last'].eq(15)
        result = []
        query = db.query(db.selectStmt(table, 'DISTINCT GetPositionList.id', cond, self.order))
        while query.next():
            result.append(forceInt(query.value(0)))
        return result

    def setSort(self, col):
        name = self.model.cols()[col].fields()[0]
        self.order = name
        tab = self.tabWidget.currentIndex()
        if tab == 0:
            header = self.tblItems.horizontalHeader()
        elif tab == 1:
            header = self.tblItems_2.horizontalHeader()
        elif tab == 2:
            header = self.tblItems_3.horizontalHeader()
        elif tab == 3:
            header = self.tblItems_4.horizontalHeader()
        else:
            header = self.tblItems_5.horizontalHeader()
        header.setSortIndicatorShown(True)
        self.isAscending = not self.isAscending
        header.setSortIndicator(col, Qt.AscendingOrder if self.isAscending else Qt.DescendingOrder)
        if self.isAscending:
            self.order = self.order + u' ASC'
        else:
            self.order = self.order + u' DESC'
        self.renewListAndSetTo(self.currentItemId())

    def renewListAndSetTo(self, itemId=None):
        idList = self.select(self.props)
        self.model.setIdList(idList)
        if idList:
            self.tblItems.selectRow(0)
        self.label.setText(u'всего: %d' % len(idList))
        self.label_2.setText(u'всего: %d' % len(idList))
        self.label_3.setText(u'Всего: %d' % len(idList))
        self.label_4.setText(u'Всего: %d' % len(idList))
        self.label_5.setText(u'Всего: %d' % len(idList))

    def getItemEditor(self):
        tab = self.tabWidget.currentIndex()
        return CPostOnAppointmentEditor(self, tab=tab)

    def on_tblItems_doubleClicked(self, index):
        pass


class CPostOnAppointmentEditor(Ui_PostOnAppointmentEditorDialog, CItemEditorDialog):
    def __init__(self,  parent, tab):
        CItemEditorDialog.__init__(self, parent, 'GetPositionList')
        self.setWindowTitleEx(u'Должность при записи на прием')
        self.setupDirtyCather()
        self.tab_inx = tab

    def setRecord(self, record):
        CItemEditorDialog.setRecord(self, record)
        setLineEditValue(self.edtCode, record, rbCode)
        setLineEditValue(self.edtName, record, 'post_name')

    def getRecord(self):
        record = CItemEditorDialog.getRecord(self)
        getLineEditValue(self.edtCode, record, rbCode)
        getLineEditValue(self.edtName, record, 'post_name')
        if self.tab_inx == 0:
            code_last = 12
        elif self.tab_inx == 1:
            code_last = 11
        elif self.tab_inx == 2:
            code_last = 13
        elif self.tab_inx == 3:
            code_last = 14
        elif self.tab_inx == 4:
            code_last = 15
        else:
            code_last = None
        record.setValue('code_last', code_last)
        return record
