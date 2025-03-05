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
#from PyQt4.QtCore import Qt

from library.adjustPopup import adjustPopupToWidget
from library.crbcombobox import CRBPopupView, CRBComboBox, CRBModel


class CF090RBPopupView(CRBPopupView):
    def __init__(self, parent):
        CRBPopupView.__init__(self, parent)


    def resizeEvent(self, resizeEvent):
        QtGui.QTableView.resizeEvent(self, resizeEvent)
        self.resizeColumnToContents(0)


class CF090RBComboBox(CRBComboBox):
    def __init__(self, parent):
        CRBComboBox.__init__(self, parent)
        self._searchString = ''
        self.showFields = CRBComboBox.showName
        self._tableName = ''
        self._addNone   = True
        self._needCache = True
        self._filier    = ''
        self._order     = ''
        self._specialValues = None
        self.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
        self.preferredWidth = None
        self.popupView = CF090RBPopupView(self)
        self.setModelColumn(self.showFields)
        self.setView(self.popupView)
        self.setModel(CRBModel(self))
        self.popupView.setFrameShape(QtGui.QFrame.NoFrame)
        self.readOnly = False
        self.installEventFilter(self)


    def showPopup(self):
        if not self.isReadOnly():
            totalItems = self._model.rowCount(None)
            if totalItems>0:
                self._searchString = ''
                view = self.popupView
                selectionModel = view.selectionModel()
                selectionModel.setCurrentIndex(self.proxyModel.index(self.currentIndex(), 1),
                                                     QtGui.QItemSelectionModel.ClearAndSelect)
                tblHeaderHeight = view.horizontalHeader().height()
                maxVisibleItems = self.maxVisibleItems()
                visibleItems = min(maxVisibleItems, totalItems)
                if visibleItems > 0:
                    view.setFixedHeight( view.rowHeight(0)*visibleItems + tblHeaderHeight )
                frame = view.parent()
                sizeHint = view.sizeHint()
                # устанавливаем рекомендуемую ширину по максимальной ширине кода + названия + 1
                #codes, names = self._model.codes(), self._model.names()
                maxWidthCode = max(view.fontMetrics().width(self._model.getCode(i) + ' ') for i in xrange(totalItems))
                preferredWidth = maxWidthCode
                preferredWidth += max(view.fontMetrics().width(self._model.getName(i)+' ') for i in xrange(totalItems))
                preferredWidth *= 1.1 # почему-то ширина не дотягивает
                view.horizontalHeader().setDefaultSectionSize(maxWidthCode+5)
                adjustPopupToWidget(self, frame, True, max(preferredWidth, self.preferredWidth, sizeHint.width()), view.height()+2)
                view.resizeColumnToContents(0)
                frame.show()
                view.setFocus()
                scrollBar = view.horizontalScrollBar()
                scrollBar.setValue(0)
