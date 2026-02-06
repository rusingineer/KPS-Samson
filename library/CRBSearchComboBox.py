# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QEvent

from library.SortFilterProxyTableModel import CSortFilterProxyTableModel
from library.crbcombobox import CRBComboBox, CRBTestComboBox
from library.adjustPopup import adjustPopupToWidget


class CRBSearchPopupView(QtGui.QFrame):
    def __init__(self, parent, popupView):
        QtGui.QFrame.__init__(self, parent)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.setWindowFlags(Qt.Popup)
        self._cmb = parent
        self.filter = parent._filier
        self.table = popupView
        self.table.doubleClicked.connect(self.on_table_doubleClicked)
        self.lblCode = QtGui.QLabel()
        self.lblCode.setText(u'Код')
        self.edtCode = QtGui.QLineEdit()
        self.lblName = QtGui.QLabel()
        self.lblName.setText(u'Наименование')
        self.edtName = QtGui.QLineEdit()
        self.edtCode.textChanged.connect(self.on_edtCode_textChanged)
        self.edtName.textChanged.connect(self.on_edtName_textChanged)

        layout = QtGui.QVBoxLayout(self)
        layoutFilter = QtGui.QHBoxLayout()
        layoutFilter.addWidget(self.lblCode)
        layoutFilter.addWidget(self.edtCode)
        layoutFilter.addWidget(self.lblName)
        layoutFilter.addWidget(self.edtName)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.addLayout(layoutFilter)
        layout.addWidget(self.table)
        self.installEventFilter(self)


    def on_table_doubleClicked(self, index):
        self._cmb.setCurrentIndex(index.row())
        self._cmb.hidePopup()


    def on_edtCode_textChanged(self, code):
        db = QtGui.qApp.db
        table = db.table(self._cmb._tableName)
        _filter = [] if not self.filter else [self.filter]
        if code:
            _filter.append(table['code'].like('%' + unicode(code) + '%'))
        if self.edtName.text():
            _filter.append(table['name'].like('%' + unicode(self.edtName.text()) + '%'))
        _filter = db.joinAnd(_filter)
        self._cmb.setFilter(_filter)

        # if code:
        #     self._cmb.setLocalFilter('code', code, CSortFilterProxyTableModel.MatchContains, isCaseSensitive=False)
        # else:
        #     self._cmb.removeLocalFilter('code')


    def on_edtName_textChanged(self, name):
        db = QtGui.qApp.db
        table = db.table(self._cmb._tableName)
        _filter = [] if not self.filter else [self.filter]
        if name:
            _filter.append(table['name'].like('%' + unicode(name) + '%'))
        if self.edtCode.text():
            _filter.append(table['code'].like('%' + unicode(self.edtCode.text()) + '%'))
        _filter = db.joinAnd(_filter)
        self._cmb.setFilter(_filter)

        # if name:
        #     self._cmb.setLocalFilter('name', name, CSortFilterProxyTableModel.MatchContains, isCaseSensitive=False)
        # else:
        #     self._cmb.removeLocalFilter('name')


    def eventFilter(self, obj, event):
        if event.type() == QEvent.Show:
            self.cmbValue = self._cmb.getValue()
        if event.type() == QEvent.Close:
            if self.cmbValue:
                self._cmb.setFilter()
                self._cmb.setValue(self.cmbValue)
        if obj == self.table:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.table.currentIndex()
                self.on_table_doubleClicked(index)
                return True
        return QtGui.QFrame.eventFilter(self, obj, event)


class CRBSearchComboBox(CRBComboBox):
    u"""Combobox для таблицы справочника с возможностью поиска"""
    def __init__(self, parent=None):
        CRBComboBox.__init__(self, parent)
        self.popupView = CRBSearchPopupView(self, self.popupView)


    def setCodeFilter(self, code):
        if code:
            self.setLocalFilter('code', code, CSortFilterProxyTableModel.MatchContains, isCaseSensitive=False)
        else:
            self.removeLocalFilter('code')


    def showPopup(self):
        if not self.isReadOnly():
            self._searchString = ''
            view = self.popupView.table
            frame = self.popupView
            #для комбобоксов с предустановленными фильтрами
            frame.filter = '' if not self._filier else self._filier
            sizeHint = view.sizeHint()
            selectionModel = view.selectionModel()
            selectionModel.setCurrentIndex(self._model.index(self.currentIndex(), 1),
                                           QtGui.QItemSelectionModel.ClearAndSelect)
            view.scrollTo(view.model().index(self.currentIndex(), 1))
            adjustPopupToWidget(self, frame, True, max(sizeHint.width(), self.preferredWidth), sizeHint.height())
            frame.show()
            view.setFocus()


    def hidePopup(self):
        self.popupView.hide()


class CRBTestSearchPopupView(CRBSearchPopupView):
    # для поиска по справочнику rbTest
    def __init__(self, parent, popupView):
        QtGui.QFrame.__init__(self, parent)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.setWindowFlags(Qt.Popup)
        self._cmb = parent
        self.filter = parent._filier
        self.table = popupView
        self.table.doubleClicked.connect(self.on_table_doubleClicked)
        self.lblCode = QtGui.QLabel()
        self.lblCode.setText(u'Код')
        self.edtCode = QtGui.QLineEdit()
        self.lblName = QtGui.QLabel()
        self.lblName.setText(u'Наименование')
        self.edtName = QtGui.QLineEdit()
        self.lblFedCode = QtGui.QLabel()
        self.lblFedCode.setText(u'Федеральный код')
        self.edtFedCode = QtGui.QLineEdit()
        self.edtCode.textChanged.connect(self.on_edtCode_textChanged)
        self.edtName.textChanged.connect(self.on_edtName_textChanged)
        self.edtFedCode.textChanged.connect(self.on_edtFedCode_textChanged)

        layout = QtGui.QVBoxLayout(self)
        layoutFilter = QtGui.QHBoxLayout()
        layoutFilter.addWidget(self.lblCode)
        layoutFilter.addWidget(self.edtCode)
        layoutFilter.addWidget(self.lblName)
        layoutFilter.addWidget(self.edtName)
        layoutFilter.addWidget(self.lblFedCode)
        layoutFilter.addWidget(self.edtFedCode)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.addLayout(layoutFilter)
        layout.addWidget(self.table)
        self.installEventFilter(self)

    def on_edtFedCode_textChanged(self, name):
        db = QtGui.qApp.db
        table = db.table(self._cmb._tableName)
        _filter = []
        if name:
            _filter.append(table['federalCode'].like('%' + unicode(name) + '%'))
        if self.filter and _filter:
            _filter = db.joinAnd([self.filter, db.joinAnd(_filter)])
        else:
            _filter = db.joinAnd(_filter)
        self._cmb.setFilter(_filter)


class CRBTestSearchComboBox(CRBTestComboBox):
    u"""Combobox для таблицы rbTest с возможностью поиска по коду, наименованию и федеральному коду"""
    def __init__(self, parent=None):
        CRBTestComboBox.__init__(self, parent)
        # self.popupView = CRBSearchPopupView(self, self.popupView)
        self.popupView = CRBTestSearchPopupView(self, self.popupView)


    def setCodeFilter(self, code):
        if code:
            self.setLocalFilter('code', code, CSortFilterProxyTableModel.MatchContains, isCaseSensitive=False)
        else:
            self.removeLocalFilter('code')


    def showPopup(self):
        if not self.isReadOnly():
            self._searchString = ''
            view = self.popupView.table
            frame = self.popupView
            frame.filter = ''
            sizeHint = view.sizeHint()
            selectionModel = view.selectionModel()
            selectionModel.setCurrentIndex(self._model.index(self.currentIndex(), 1),
                                           QtGui.QItemSelectionModel.ClearAndSelect)
            view.scrollTo(view.model().index(self.currentIndex(), 1))
            adjustPopupToWidget(self, frame, True, max(sizeHint.width(), self.preferredWidth), sizeHint.height())
            frame.show()
            view.setFocus()


    def hidePopup(self):
        self.popupView.hide()
