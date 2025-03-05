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
from PyQt4.QtCore import SIGNAL

from Events.PropertyValueToTemplateComboBoxPopup import CPropertyValueToTemplateComboBoxPopup
from library.crbcombobox import CRBComboBox


__all__ = [ 'CPropertyValueToTemplateComboBox',
          ]

class CPropertyValueToTemplateComboBox(CRBComboBox):
    def __init__(self, parent, clientId):
        CRBComboBox.__init__(self, parent)
        self.setTable('ActionPropertyTemplate')
        self.setShowFields(CRBComboBox.showCodeAndName)
        self._popup = None
        self.templateId = None
        self.clientId = clientId
        self.items = {}
        self._eventEditor = None


    def showPopup(self):
        if not self._popup:
            self._popup = CPropertyValueToTemplateComboBoxPopup(self)
            self.connect(self._popup, SIGNAL('propertyValueToTemplateSelected(int)'), self.setValue)
        pos = self.rect().bottomLeft()
        pos2 = self.rect().topLeft()
        pos = self.mapToGlobal(pos)
        pos2 = self.mapToGlobal(pos2)
        size = self._popup.sizeHint()
        width= max(size.width(), self.width())
        size.setWidth(width)
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
        pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
        self._popup.move(pos)
        self._popup.resize(size)
        self._popup.show()
        self._popup.setEventEditor(self._eventEditor)
        self._popup.setClientId(self.clientId)
        self._popup.setValuePropertyToTemplateItems(self.items)
        self._popup.setValue(self.templateId)
        self._popup.updateIdList()


    def setEventEditor(self, eventEditor):
        self._eventEditor = eventEditor


    def hidePopup(self):
        if self._popup:
            self.items = self._popup.getValuePropertyToTemplateItems()
        QtGui.QComboBox.hidePopup(self)


    def getPropertyValue(self, templateId):
        valueProperty = None
        if templateId:
            valueProperty = self.items.get(templateId, None)
        return valueProperty


    def setValuePropertyToTemplateItems(self, items):
        self.items = items


    def getValuePropertyToTemplateItems(self):
        if self._popup:
            self.items = self._popup.getValuePropertyToTemplateItems()
        return self.items


    def setValue(self, itemId):
        row = self._model.searchId(itemId)
        if row == -1:
            self.setCurrentIndex(-1)
        else:
            sourceIndex = self._model.index(row, 0)
            proxyIndex = self.proxyModel.mapFromSource(sourceIndex)
            self.setCurrentIndex(proxyIndex.row())


    def getValue(self):
        return self.value()


    def value(self):
        row = self.currentIndex()
        rowIndex = self.proxyModel.index(row, 0)
        sourceIndex = self.proxyModel.mapToSource(rowIndex)
        return self._model.getId(sourceIndex.row())

