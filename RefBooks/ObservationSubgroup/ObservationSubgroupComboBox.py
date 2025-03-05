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

from PyQt4                  import QtGui
from PyQt4.QtCore           import Qt, QVariant
from library.Utils          import forceInt, forceString, toVariant
from library.crbcombobox    import CRBModelDataCache
from library.InDocTable     import CInDocTableCol


class CObservationSubgroupComboBox(QtGui.QComboBox):
    def __init__(self, parent):
        QtGui.QComboBox.__init__(self, parent)
        self._displayText = ''
        self._select()
        # баг, на некоторых стилях не отображается чекбокс
        self.setStyleSheet('QComboBox { combobox-popup: 0 }')


    def _select(self):
        data = CRBModelDataCache.getData('rbObservationSubgroup', False)
        model = QtGui.QStandardItemModel(data.getCount(), 1)
        for i in xrange(data.getCount()):
            item = QtGui.QStandardItem(data.getCode(i) + ' | ' + data.getName(i))
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setData(Qt.Unchecked, Qt.CheckStateRole)
            item.setData(data.getId(i), Qt.UserRole)
            model.setItem(i, 0, item)
        self.setModel(model)
        model.itemChanged.connect(self.on_itemChanged)


    def on_itemChanged(self, item):
        self.updateDisplayText()
        self.repaint()


    def paintEvent(self, event):
        painter = QtGui.QStylePainter(self)
        painter.setPen(self.palette().color(QtGui.QPalette.Text))
        option = QtGui.QStyleOptionComboBox()
        self.initStyleOption(option)
        painter.drawComplexControl(QtGui.QStyle.CC_ComboBox, option)
        textRect = self.rect().adjusted(4, 1, -22, 0)
        painter.drawText(textRect, Qt.AlignVCenter, self._displayText)


    def resizeEvent(self, event):
        self.updateDisplayText()


    def updateDisplayText(self):
        textRect = self.rect().adjusted(4, 1, -22, 0)
        fontMetrics = QtGui.QFontMetrics(self.font())
        displayText = self.getDisplayText()

        if fontMetrics.size(Qt.TextSingleLine, displayText).width() > textRect.width():
            while displayText != '' and fontMetrics.size(Qt.TextSingleLine, displayText + '...').width() > textRect.width():
                displayText = displayText[:-1]
            displayText += '...'
        self._displayText = displayText


    def getCheckedIdList(self):
        idList = []
        model = self.model()
        for row in xrange(model.rowCount()):
            item = model.item(row)
            if item and item.checkState() == Qt.Checked:
                idList.append(forceInt(item.data(Qt.UserRole)))
        return ','.join(map(str, idList))


    def setCheckedIdList(self, idList):
        if not idList:
            return
        model = self.model()
        for itemId in map(forceInt, idList.split(',')):
            for row in xrange(model.rowCount()):
                item = model.item(row)
                if forceInt(item.data(Qt.UserRole)) == itemId:
                    item.setData(Qt.Checked, Qt.CheckStateRole)


    def getDisplayText(self):
        codes = []
        model = self.model()
        data = CRBModelDataCache.getData('rbObservationSubgroup', False)
        for row in xrange(model.rowCount()):
            item = model.item(row)
            if item and item.checkState() == Qt.Checked:
                code = forceString(data.getCode(row))
                codes.append(code)
        return ', '.join(codes)


    def value(self):
        return self.getCheckedIdList()


    def setValue(self, idList):
        self.setCheckedIdList(idList)


class CObservationSubgroupInDocTableCol(CInDocTableCol):
    def toString(self, val, record):
        cache = CRBModelDataCache.getData('rbObservationSubgroup', False)
        strVal = forceString(val)
        if strVal:
            idList = [forceInt(x.strip()) for x in strVal.split(',')]
            text = ', '.join(unicode(cache.getCodeById(itemId)) for itemId in idList)
            return toVariant(text)
        return QVariant()


    def createEditor(self, parent):
        editor = CObservationSubgroupComboBox(parent)
        return editor


    def setEditorData(self, editor, value, record):
        editor.setValue(forceString(value))


    def getEditorData(self, editor):
        return toVariant(editor.value())
