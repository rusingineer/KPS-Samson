# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
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
from PyQt4.QtCore import Qt, SIGNAL, QEvent, QRectF, QPointF, QSize

from Events.ActionPropertiesTable import CActionPropertiestableVerticalHeaderView
from library.Utils                import forceString, toVariant


class CActionPropertyDelegate(QtGui.QItemDelegate):
    def __init__(self, parent, lineHeight):
        QtGui.QItemDelegate.__init__(self, parent)
        self.lineHeight = lineHeight


    def eventFilter(self, editor, event):
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and isinstance(editor, QtGui.QTextEdit):
                return False
        return QtGui.QItemDelegate.eventFilter(self, editor, event)


    def commit(self):
        editor = self.sender()
        self.emit(SIGNAL('commitData(QWidget *)'), editor)


    def commitAndCloseEditor(self):
        editor = self.sender()
        self.emit(SIGNAL('commitData(QWidget *)'), editor)
        self.emit(SIGNAL('closeEditor(QWidget *,QAbstractItemDelegate::EndEditHint)'), editor, QtGui.QAbstractItemDelegate.NoHint)


    def paint(self, painter, option, index):
        model = index.model()
        row = index.row()
        propertyType = model.getPropertyType(row)
        if propertyType.isImage():
            if option.state & QtGui.QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            image = model.getProperty(row).getImage()
            if image:
                painter.save()
                iconMaxSize = option.rect.size()
                style = QtGui.qApp.style()
                xOffset = style.pixelMetric(QtGui.QStyle.PM_FocusFrameHMargin)+style.pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
                yOffset = style.pixelMetric(QtGui.QStyle.PM_FocusFrameVMargin)+style.pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
                iconMaxSize -= QSize( xOffset*2,  yOffset*2 )
                if image.height() > iconMaxSize.height() or image.width() > iconMaxSize.width():
                    image = image.scaled(iconMaxSize.width(), iconMaxSize.height(), Qt.KeepAspectRatio)
                painter.translate(option.rect.x(), option.rect.y())
                painter.drawImage((option.rect.width()-image.width())//2,
                                  (option.rect.height()-image.height())//2,
                                  image)
                painter.restore()
                return
        if propertyType.isHtml():
            if option.state & QtGui.QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            painter.setBrush(QtGui.QColor(Qt.black))
            document = QtGui.QTextDocument()
            document.setHtml(index.data(Qt.DisplayRole).toString())
            context = QtGui.QAbstractTextDocumentLayout.PaintContext()
            context.palette = option.palette
            if option.state & QtGui.QStyle.State_Selected:
                context.palette.setColor(QtGui.QPalette.Text, Qt.white)
            else:
                context.palette.setColor(QtGui.QPalette.Text, Qt.black)
            painter.save()
            layout = document.documentLayout()
            painter.setClipRect(option.rect, Qt.IntersectClip)
            painter.translate(option.rect.x(), option.rect.y())
            layout.draw(painter, context)
            painter.restore()
        else:
            QtGui.QItemDelegate.paint(self, painter, option, index)


    def drawDisplay(self, painter, option, rect, text):
        if option.state & QtGui.QStyle.State_Enabled:
            if option.state & QtGui.QStyle.State_Active:
                cg = QtGui.QPalette.Normal
            else:
                cg = QtGui.QPalette.Inactive
        else:
            cg = QtGui.QPalette.Disabled
        if  option.state & QtGui.QStyle.State_Selected:
            painter.fillRect(rect, option.palette.brush(cg, QtGui.QPalette.Highlight))
            painter.setPen(option.palette.color(cg, QtGui.QPalette.HighlightedText))
        else:
            painter.setPen(option.palette.color(cg, QtGui.QPalette.Text))
        if text.isEmpty():
            return
        if (option.state & QtGui.QStyle.State_Editing):
            painter.save()
            painter.setPen(option.palette.color(cg, QtGui.QPalette.Text))
            painter.drawRect(rect.adjusted(0, 0, -1, -1))
            painter.restore()
        widget = None
        style = widget.style() if widget else QtGui.qApp.style()
        textMargin = style.pixelMetric(QtGui.QStyle.PM_FocusFrameHMargin, None, widget) + 1
        textRect = rect.adjusted(textMargin, 0, -textMargin, 0) # remove width padding
        textOption = QtGui.QTextOption()
        textOption.setWrapMode(textOption.WrapAtWordBoundaryOrAnywhere)
        textOption.setTextDirection(option.direction)
        textOption.setAlignment(QtGui.QStyle.visualAlignment(option.direction, option.displayAlignment))
        painter.save()
        try:
            painter.setFont(option.font)
            painter.drawText(QRectF(textRect), text, textOption)
            boundRect = painter.boundingRect(QRectF(textRect), text, textOption)
            if boundRect.height()>textRect.height():
                painter.setBrush(option.palette.color(cg, QtGui.QPalette.Button))
                x = rect.right()-1
                y = rect.bottom()-1
                h = w = painter.fontMetrics().averageCharWidth()
                painter.drawPolygon(QPointF(x-w*2, y-h),
                                    QPointF(x-w,   y),
                                    QPointF(x,     y-h)
                                   )
        finally:
            painter.restore()


    def createEditor(self, parent, option, index):
        model = index.model()
        row = index.row()
        propertyType = model.getPropertyType(row)
        editor = propertyType.createEditor(model.action, parent, model.clientId, model.eventTypeId)
        editor.setStatusTip(forceString(model.data(index, Qt.StatusTipRole)))
        if u'Счетчик' in forceString(propertyType.typeName):
            editor.setReadOnly(False)
        self.connect(editor, SIGNAL('commit()'), self.commit)
        self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        return editor


    def setEditorData(self, editor, index):
        model = index.model()
        value = model.data(index, Qt.EditRole)
        editor.setValue(value)


    def setModelData(self, editor, model, index):
        model = index.model()
        value = editor.value()
        model.setData(index, toVariant(value))
        row = index.row()
        propertyType = model.getPropertyType(row)
        if propertyType.isJobTicketValueType():
            if model.plannedEndDateByJobTicket():
                model.setPlannedEndDateByJobTicket(value)


    def sizeHint(self, option, index):
        model = index.model()
        row = index.row()
        propertyType = model.getPropertyType(row)
        property = model.action.getPropertyById(propertyType.id)
        preferredHeightUnit, preferredHeight = property.getPreferredHeight()
        result = QSize(10, self.lineHeight*preferredHeight if preferredHeightUnit == 1 else preferredHeight)
        return result


class CCheckActionPropertiesTableView(QtGui.QTableView):
    titleWidth = 20

    def __init__(self, parent):
        QtGui.QTableView.__init__(self, parent)
        self._verticalHeader = CActionPropertiestableVerticalHeaderView(Qt.Vertical, self)
        self.setVerticalHeader(self._verticalHeader)
        h = self.fontMetrics().height()
        self.verticalHeader().setDefaultSectionSize(3*h/2)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        w = self.fontMetrics().lineWidth()
        self.horizontalHeader().setDefaultSectionSize(3*w/2)
        self.valueDelegate = CActionPropertyDelegate(self, self.fontMetrics().height())
        self.setItemDelegateForColumn(1, self.valueDelegate)
        self.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        self._popupMenu = None
        self._actCopy = None
        self.preferencesLocal = {}
