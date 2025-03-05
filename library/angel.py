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

import sys
from xml.etree import ElementTree as xml

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, SLOT, QPointF, QRectF, QVariant

from library.Utils import trim

from library.Ui_angel import Ui_AngelDialog
from library.Ui_TextItemEditorDialog import Ui_TextItemEditorDialog


class CTextItemEditorDialog(QtGui.QDialog, Ui_TextItemEditorDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

    def setText(self, text):
        self.edtText.setText(text)
        self.edtText.selectAll()

    def text(self):
        return self.edtText.text()

    def setRotation(self, val):
        self.edtRotation.setValue(val)

    def rotation(self):
        return self.edtRotation.value()

    def setTextSize(self, val):
        self.edtTextSize.setValue(val)

    def textSize(self):
        return self.edtTextSize.value()

    def exec_(self):
        if QtGui.QDialog.exec_(self):
            if trim(self.text()):
                return QtGui.QDialog.Accepted
        return QtGui.QDialog.Rejected


class CCommonControl:
    def sizeToUp(self, mode=1):
        sizeUp = 1
        self.reSize(sizeUp)

    def sizeToDown(self, mode=1):
        sizeUp = -1
        self.reSize(sizeUp)

    def reSize(self, sizeUp):
        if sizeUp > 0:
            self.xSize += 2
            self.ySize += 2
        else:
            if self.xSize >= 8 and self.ySize >= 8:
                self.xSize -= 2
                self.ySize -= 2
        if self.xSize >= 8 and self.ySize >= 8:
            self.setRect(self.rect().x() - sizeUp,
                         self.rect().y() - sizeUp,
                         self.xSize,
                         self.ySize)
            self.resetHandles()

    def paintHandles(self, selected):
        if selected:
            self.resetHandles()
            self.tlHandle.setVisible(True)
            self.trHandle.setVisible(True)
            self.blHandle.setVisible(True)
            self.brHandle.setVisible(True)
            self.setCursor(QtGui.QCursor(Qt.SizeAllCursor))
        else:
            self.tlHandle.setVisible(False)
            self.trHandle.setVisible(False)
            self.blHandle.setVisible(False)
            self.brHandle.setVisible(False)
            self.setCursor(QtGui.QCursor(Qt.ArrowCursor))


    def resetHandles(self):
        rect = self.rect()
        self.tlHandle.resetHandle(rect.topLeft())
        self.trHandle.resetHandle(rect.topRight())
        self.blHandle.resetHandle(rect.bottomLeft())
        self.brHandle.resetHandle(rect.bottomRight())

    def resetSizes(self):
        self.xSize = self.rect().width()
        self.ySize = self.rect().height()

    def checkPos(self):
        rect = self.rect()
        if rect.height() < 0 and rect.width() < 0:
            self.setRect(rect.x() + +rect.width(),
                         rect.y() + rect.height(),
                         abs(rect.width()),
                         abs(rect.height()))
        else:
            if rect.width() < 0:
                self.setRect(rect.x() + rect.width(),
                             rect.y(),
                             abs(rect.width()),
                             abs(rect.height()))
            if rect.height() < 0:
                self.setRect(rect.x(),
                             rect.y() + rect.height(),
                             abs(rect.width()),
                             abs(rect.height()))
        self.resetHandles()


class CGraphicsPixmapItem(QtGui.QGraphicsPixmapItem):
    itemName = 'QGraphicsPixmapItem'


class CGraphicsHandleItem(QtGui.QGraphicsRectItem):
    itemName = 'CGraphicsHandleItem'
    HandleSize = 4

    def __init__(self, name, point, cursorShape, parent=None):
        self.parent = parent  # wtf? скрывать Qt-шный parent - это плохая затея
        #        HandleSize = 4
        rect = QRectF(point.x() - CGraphicsHandleItem.HandleSize,
                      point.y() - CGraphicsHandleItem.HandleSize,
                      CGraphicsHandleItem.HandleSize * 2,
                      CGraphicsHandleItem.HandleSize * 2)
        QtGui.QGraphicsRectItem.__init__(self, rect, parent)
        black = QtGui.QColor(0, 0, 0)
        white = QtGui.QColor(255, 255, 255)
        pen = QtGui.QPen(white)
        brush = QtGui.QBrush(black)
        self.setPen(pen)
        self.setBrush(brush)
        self.setCursor(QtGui.QCursor(cursorShape))

        self.setFlags(QtGui.QGraphicsItem.ItemIsMovable)

        self.handleName = name

        self.dRect = None

    def resetHandle(self, point):
        rect = QRectF(point.x() - CGraphicsHandleItem.HandleSize,
                      point.y() - CGraphicsHandleItem.HandleSize,
                      CGraphicsHandleItem.HandleSize * 2,
                      CGraphicsHandleItem.HandleSize * 2)
        self.setRect(rect)

    def itemChange(self, change, value):
        return QtGui.QGraphicsRectItem.itemChange(self, change, value)

    def mouseMoveEvent(self, mouseEvent):
        startPos = mouseEvent.buttonDownScenePos(Qt.LeftButton)
        currentPos = mouseEvent.scenePos()
        dPos = currentPos - startPos
        if not self.dRect:
            self.dRect = self.parent.rect()
        rect = self.dRect

        if self.handleName == 'br':
            self.brMoving(rect, QPointF(dPos.x(), dPos.y()))

        elif self.handleName == 'tl':
            self.tlMoving(rect, QPointF(dPos.x(), dPos.y()))

        elif self.handleName == 'bl':
            self.blMoving(rect, QPointF(dPos.x(), dPos.y()))

        elif self.handleName == 'tr':
            self.trMoving(rect, QPointF(dPos.x(), dPos.y()))

        self.parent.resetHandles()
        self.parent.resetSizes()
        QtGui.QGraphicsItem.mouseMoveEvent(self, mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        if mouseEvent.button() == Qt.LeftButton:
            self.dRect = None
            self.parent.checkPos()
        QtGui.QGraphicsItem.mouseReleaseEvent(self, mouseEvent)

    def brMoving(self, rect, dPos):
        self.parent.setRect(rect.x() - dPos.x(),
                            rect.y() - dPos.y(),
                            rect.width() + dPos.x(),
                            rect.height() + dPos.y())

    def tlMoving(self, rect, dPos):
        self.parent.setRect(rect.x(),
                            rect.y(),
                            rect.width() - dPos.x(),
                            rect.height() - dPos.y())

    def blMoving(self, rect, dPos):
        self.parent.setRect(rect.x(),
                            rect.y() - dPos.y(),
                            rect.width() - dPos.x(),
                            rect.height() + dPos.y())

    def trMoving(self, rect, dPos):
        self.parent.setRect(rect.x() - dPos.x(),
                            rect.y(),
                            rect.width() + dPos.x(),
                            rect.height() - dPos.y())


class CGraphicsTextItem(QtGui.QGraphicsTextItem, CCommonControl):
    itemName = 'CGraphicsTextItem'

    def __init__(self, point, text, colour, markSize=5, parent=None):
        QtGui.QGraphicsTextItem.__init__(self, text, parent)
        self.setFlags(QtGui.QGraphicsItem.ItemIsMovable | QtGui.QGraphicsItem.ItemIsSelectable)
        x = point.x()
        y = point.y()
        self.setPos(x, y)
        self.setTextSize(markSize)
        self._rotation = 0
        self.setDefaultTextColor(colour)
        rect = self.rect()
        self.tlHandle = CGraphicsHandleItem('tl', rect.topLeft(), Qt.SizeAllCursor, self)
        self.trHandle = CGraphicsHandleItem('tr', rect.topRight(), Qt.SizeAllCursor, self)
        self.blHandle = CGraphicsHandleItem('bl', rect.bottomLeft(), Qt.SizeAllCursor, self)
        self.brHandle = CGraphicsHandleItem('br', rect.bottomRight(), Qt.SizeAllCursor, self)

    def setDefaultTextColor(self, colour):
        self.colour = QtGui.QColor(colour)
        self.colour.setAlpha(255)
        QtGui.QGraphicsTextItem.setDefaultTextColor(self, self.colour)

    def textColour(self):
        return self.colour

    def rotate(self, val):
        self._rotation = val
        QtGui.QGraphicsTextItem.rotate(self, val)

    def rotation(self):
        return self._rotation

    def setTextSize(self, size):
        font = QtGui.QFont()
        font.setPixelSize(size * 10)
        self.setFont(font)

    def itemChange(self, change, value):
        if change == QtGui.QGraphicsItem.ItemSelectedChange:
            selected = value.toBool()
            self.paintHandles(selected)
        return QtGui.QGraphicsTextItem.itemChange(self, change, value)

    def rect(self):
        return self.boundingRect()

    def setRect(self, x, y, width, height):
        rect = QRectF(x, y, width, height)
        self.update(rect)


    @classmethod
    def loadSettings(cls, itemSettings, markSize):
        pos, text, colour, size, rotation = itemSettings
        item = cls(pos, text, colour, size)
        item.rotate(rotation)
        item.setZValue(1)
        return item


class CGraphicsEllipseItem(QtGui.QGraphicsEllipseItem, CCommonControl):
    itemName = 'CGraphicsEllipseItem'

    def __init__(self, point, colour, markSize, sizeX=10, sizeY=10, parent=None):
        self.xSize = sizeX * markSize
        self.ySize = sizeY * markSize

        self.myRect = QRectF(point.x() - self.xSize / 2,
                             point.y() - self.ySize / 2,
                             self.xSize,
                             self.ySize)
        QtGui.QGraphicsEllipseItem.__init__(self, self.myRect, parent)

        self.setRect(self.myRect)
        self.tlHandle = CGraphicsHandleItem('tl', self.myRect.topLeft(), Qt.SizeAllCursor, self)
        self.trHandle = CGraphicsHandleItem('tr', self.myRect.topRight(), Qt.SizeAllCursor, self)
        self.blHandle = CGraphicsHandleItem('bl', self.myRect.bottomLeft(), Qt.SizeAllCursor, self)
        self.brHandle = CGraphicsHandleItem('br', self.myRect.bottomRight(), Qt.SizeAllCursor, self)
        self.brushColour = colour
        self.brushColour.setAlpha(100)
        self.setPen(QtGui.QPen(colour))
        self.setFlags(QtGui.QGraphicsItem.ItemIsMovable | QtGui.QGraphicsItem.ItemIsSelectable)
        self.setBrush(self.brushColour)

    def itemChange(self, change, value):
        if change == QtGui.QGraphicsItem.ItemSelectedChange:
            selected = value.toBool()
            self.paintHandles(selected)
        return QtGui.QGraphicsEllipseItem.itemChange(self, change, value)

    def paint(self, painter, option, widget):
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawEllipse(self.rect())
        if option.state & QtGui.QStyle.State_Selected:
            black = QtGui.QColor(0, 0, 0)
            pen = QtGui.QPen(black)
            painter.setPen(pen)
            painter.drawRect(self.rect())

            white = QtGui.QColor(255, 255, 255)
            pen = QtGui.QPen(white)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.rect())

            hopt = QtGui.QStyleOptionGraphicsItem()
            self.tlHandle.paint(painter, hopt, widget)
            self.trHandle.paint(painter, hopt, widget)
            self.blHandle.paint(painter, hopt, widget)
            self.brHandle.paint(painter, hopt, widget)

    @classmethod
    def loadSettings(cls, itemSettings, markSize):
        point, rect, pen = itemSettings
        item = cls(point, pen, markSize)
        item.setRect(rect)
        item.setBrush(pen)
        item.resetSizes()
        item.setZValue(1)
        return item


class CGraphicsRectItem(QtGui.QGraphicsRectItem, CCommonControl):
    itemName = 'CGraphicsRectItem'

    def __init__(self, point, colour, markSize, sizeX=10, sizeY=10, parent=None):
        self.xSize = sizeX * markSize
        self.ySize = sizeY * markSize
        self.myRect = QRectF(point.x() - self.xSize / 2,
                             point.y() - self.ySize / 2,
                             self.xSize,
                             self.ySize)
        QtGui.QGraphicsRectItem.__init__(self, self.myRect, parent)

        self.setRect(self.myRect)
        self.tlHandle = CGraphicsHandleItem('tl', self.myRect.topLeft(), Qt.SizeAllCursor, self)
        self.trHandle = CGraphicsHandleItem('tr', self.myRect.topRight(), Qt.SizeAllCursor, self)
        self.blHandle = CGraphicsHandleItem('bl', self.myRect.bottomLeft(), Qt.SizeAllCursor, self)
        self.brHandle = CGraphicsHandleItem('br', self.myRect.bottomRight(), Qt.SizeAllCursor, self)
        self.brushColour = colour
        self.brushColour.setAlpha(100)
        self.setPen(QtGui.QPen(colour))
        self.setFlags(QtGui.QGraphicsItem.ItemIsMovable | QtGui.QGraphicsItem.ItemIsSelectable)
        self.setBrush(self.brushColour)

    def itemChange(self, change, value):
        if change == QtGui.QGraphicsItem.ItemSelectedChange:
            selected = value.toBool()
            self.paintHandles(selected)
        return QtGui.QGraphicsRectItem.itemChange(self, change, value)

    def paint(self, painter, option, widget):
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRect(self.rect())
        if option.state & QtGui.QStyle.State_Selected:
            white = QtGui.QColor(255, 255, 255)
            pen = QtGui.QPen(white)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.rect())

            hopt = QtGui.QStyleOptionGraphicsItem()
            self.tlHandle.paint(painter, hopt, widget)
            self.trHandle.paint(painter, hopt, widget)
            self.blHandle.paint(painter, hopt, widget)
            self.brHandle.paint(painter, hopt, widget)

    @classmethod
    def loadSettings(cls, itemSettings, markSize):
        point, rect, pen = itemSettings
        item = cls(point, pen, markSize)
        item.setRect(rect)
        item.setBrush(pen)
        item.resetSizes()
        item.setZValue(1)
        return item


class CAngelScene(QtGui.QGraphicsScene):
    def __init__(self, parent=None):
        QtGui.QGraphicsScene.__init__(self, parent)
        self.mode = 0
        self.selectionBox = None
        self.markSize = 1
        self.rmbIsPressed = False
        self.lmbIsPressed = False

        self.previousText = None
        self.previousTextSize = None
        self.previousTextPotation = None

        self.colour = QtGui.QColor(0x000000)

        self.isDataSaved = False

        self.marksData = None
        self.savingAbility = True

        self.help = CHelpWindow()

    def setMarkSize(self, markSize):
        self.markSize = markSize

    def setMode(self, mode):
        self.mode = mode

    def setDataSaved(self, bool):
        self.isDataSaved = bool

    def setColour(self, colour):
        if colour == 'Blue':
            self.colour = QtGui.QColor(0x0000FF)
        elif colour == 'Red':
            self.colour = QtGui.QColor(0xFF0000)
        elif colour == 'Green':
            self.colour = QtGui.QColor(0x00FF00)
        elif colour == 'Black':
            self.colour = QtGui.QColor(0x000000)
        elif colour == 'Yellow':
            self.colour = QtGui.QColor(0xFFFF00)

    def mouseDoubleClickEvent(self, mouseEvent):
        items = self.selectedItems()
        if len(items) == 1:
            item = items[0]
            if isinstance(item, CGraphicsTextItem):
                text = item.toPlainText()
                rotation = item.rotation()
                textSize = item.font().pixelSize() / 10
                dlgText = CTextItemEditorDialog(self)
                dlgText.setText(text)
                dlgText.setRotation(rotation)
                dlgText.setTextSize(textSize)
                if dlgText.exec_():
                    item.resetTransform()
                    item.setPlainText(dlgText.text())
                    item.rotate(dlgText.rotation())
                    item.setTextSize(dlgText.textSize())
                    item.resetHandles()
                    dlgText.deleteLater()
        QtGui.QGraphicsScene.mouseDoubleClickEvent(self, mouseEvent)

    def emitItemWasAdded(self):
        self.emit(SIGNAL('itemWasAdded()'))

    def mousePressEvent(self, mouseEvent):
        if mouseEvent.button() == Qt.RightButton:
            self.rmbIsPressed = True
        if mouseEvent.button() == Qt.LeftButton:
            self.lmbIsPressed = True
            if self.mode == 0:
                item = CGraphicsRectItem(mouseEvent.scenePos(), self.colour, self.markSize)
                self.preAddItem(item)
                self.emitItemWasAdded()

            elif self.mode == 1:
                item = CGraphicsEllipseItem(mouseEvent.scenePos(), self.colour, self.markSize)
                self.preAddItem(item)
                self.emitItemWasAdded()

            elif self.mode == 2:
                dlgText = CTextItemEditorDialog(self)
                dlgText.setTextSize(self.markSize)
                if self.previousTextSize:
                    dlgText.setTextSize(self.previousTextSize)
                if self.previousTextPotation:
                    dlgText.setRotation(self.previousTextPotation)
                if self.previousText:
                    dlgText.setText(self.previousText)
                if dlgText.exec_():
                    size = dlgText.textSize()
                    text = dlgText.text()
                    self.previousTextSize = size
                    self.previousText = text
                    item = CGraphicsTextItem(mouseEvent.scenePos(),
                                             text,
                                             self.colour, size)
                    rotation = dlgText.rotation()
                    self.previousTextPotation = rotation
                    item.rotate(rotation)
                    self.preAddItem(item)
                    self.emitItemWasAdded()
                dlgText.deleteLater()

            elif self.mode == 3 and not self.mouseGrabberItem():
                startPos = mouseEvent.buttonDownScenePos(Qt.LeftButton)
                stopPos = mouseEvent.scenePos()
                left = min(startPos.x(), stopPos.x())
                top = min(startPos.y(), stopPos.y())
                width = abs(startPos.x() - stopPos.x())
                height = abs(startPos.y() - stopPos.y())
                if not self.selectionBox:
                    palette = QtGui.qApp.palette()
                    highlightColor = palette.color(QtGui.QPalette.Active,
                                                   QtGui.QPalette.Highlight)
                    pen = QtGui.QPen(highlightColor)
                    pen.setStyle(Qt.DotLine)
                    brushColor = QtGui.QColor(highlightColor)
                    brushColor.setAlpha(100)
                    brush = QtGui.QBrush(brushColor)
                    self.selectionBox = self.addRect(left, top, width, height, pen, brush)
                    self.selectionBox.setZValue(2)
                else:
                    self.selectionBox.setRect(left, top, width, height)
                    # mouseEvent.accept()
        QtGui.QGraphicsScene.mousePressEvent(self, mouseEvent)

    def preAddItem(self, item):
        self.clearSelection()
        item.setZValue(1)
        self.addItem(item)

    def mouseReleaseEvent(self, mouseEvent):
        if self.mode == 3 and mouseEvent.button() == Qt.LeftButton:
            if self.selectionBox:
                startPos = mouseEvent.buttonDownScenePos(Qt.LeftButton)
                stopPos = mouseEvent.scenePos()
                left = min(startPos.x(), stopPos.x())
                top = min(startPos.y(), stopPos.y())
                width = abs(startPos.x() - stopPos.x())
                height = abs(startPos.y() - stopPos.y())
                self.removeItem(self.selectionBox)
                self.selectionBox = None
                pp = QtGui.QPainterPath()
                pp.addRect(left, top, width, height)
                self.setSelectionArea(pp)
            mouseEvent.accept()
        else:
            QtGui.QGraphicsScene.mouseReleaseEvent(self, mouseEvent)

        if mouseEvent.button() == Qt.LeftButton:
            self.lmbIsPressed = False
            for obj in self.items():
                if not isinstance(obj, QtGui.QGraphicsPixmapItem):
                    obj.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
        if mouseEvent.button() == Qt.RightButton:
            self.rmbIsPressed = False
        QtGui.QGraphicsScene.mouseReleaseEvent(self, mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        if self.mode == 3 and self.selectionBox and not self.mouseGrabberItem():
            startPos = mouseEvent.buttonDownScenePos(Qt.LeftButton)
            stopPos = mouseEvent.scenePos()
            left = min(startPos.x(), stopPos.x())
            top = min(startPos.y(), stopPos.y())
            width = abs(startPos.x() - stopPos.x())
            height = abs(startPos.y() - stopPos.y())
            self.selectionBox.setRect(left, top, width, height)
            mouseEvent.accept()
        else:
            QtGui.QGraphicsScene.mouseMoveEvent(self, mouseEvent)
            self.selectionBox = None
        QtGui.QGraphicsScene.mouseMoveEvent(self, mouseEvent)

    def keyPressEvent(self, keyEvent):
        if keyEvent.matches(QtGui.QKeySequence.Delete) and self.selectedItems():
            for x in self.selectedItems():
                self.removeItem(x)
        if keyEvent.text() == u'a':
            for x in self.items(): x.setSelected(True)
        elif keyEvent.text() == u'+':
            for obj in self.selectedItems():
                obj.sizeToUp()
        elif keyEvent.text() == u'-':
            for obj in self.selectedItems():
                obj.sizeToDown()
        elif keyEvent.text() == u's':
            self.saveItems()
        elif keyEvent.text() == u'h':
            self.helpOpen()
        elif keyEvent.text() == u'l':
            self.loadMarks(self.marksData)
        QtGui.QGraphicsScene.keyPressEvent(self, keyEvent)

    def helpOpen(self):
        self.help.exec_()

    def saveItems(self):
        if self.savingAbility:
            self.setDataSaved(True)
            root = xml.Element('root')
            for obj in self.items():  #
                if (not isinstance(obj, (CGraphicsHandleItem, QtGui.QGraphicsPixmapItem))) and (QtGui.QGraphicsRectItem != type(obj)):
                    object = xml.SubElement(root, 'object')
                    object.set('type', obj.itemName)
                    if isinstance(obj, (CGraphicsEllipseItem, CGraphicsRectItem)):
                        rect = xml.SubElement(object, 'rect')
                        x, y = str(obj.rect().x() + obj.pos().x()), str(obj.rect().y() + obj.pos().y())
                        width, height = str(obj.rect().width()), str(obj.rect().height())
                        t = ','.join([x, y, width, height])
                        rect.text = (t)
                        pen = xml.SubElement(object, 'pen')
                        pen.text = str(obj.pen().color().rgb())
                    elif isinstance(obj, CGraphicsTextItem):
                        pos = xml.SubElement(object, 'pos')
                        pos.text = '%d,%d' % (obj.pos().x(), obj.pos().y())
                        text = xml.SubElement(object, 'text')
                        text.text = unicode(obj.toPlainText())
                        colour = xml.SubElement(object, 'colour')
                        colour.text = str(obj.textColour().rgb())
                        size = xml.SubElement(object, 'size')
                        size.text = str(int(obj.font().pixelSize() / 10))
                        rotation = xml.SubElement(object, 'rotation')
                        rotation.text = str(obj.rotation())
                    elif isinstance(obj, QtGui.QGraphicsPixmapItem):
                        pixmap = xml.SubElement(object, 'pixmap')
                        pixmap.text = 'Nice pixmap'
            #            tree = xml.ElementTree(root)
            self.marksData = xml.tostring(root)
            self.emit(SIGNAL('marksDataSaved()'))

    def loadItems(self, marksData):
        result = getImageMapItemsSettings(marksData)

        _itemTypeMap = {'CGraphicsEllipseItem': CGraphicsEllipseItem,
                        'CGraphicsRectItem': CGraphicsRectItem,
                        'CGraphicsTextItem': CGraphicsTextItem}

        for itemTypeName, settingsList in result.items():
            itemType = _itemTypeMap.get(itemTypeName, None)
            if itemType:
                for itemSettings in settingsList:
                    item = itemType.loadSettings(itemSettings, self.markSize)
                    self.addItem(item)

    def loadMarks(self, marksData):
        if marksData == '':
            pass
        else:
            self.loadItems(marksData)


class CHelpWindow(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setWindowTitle(u'Помощь')
        self.setFixedSize(400, 260)

        self.text = QtGui.QTextEdit()
        self.text.setReadOnly(True)
        self.text.setDocumentTitle(u'Помощь')
        self.text.setText(u'Клавиша «+» --- Увеличить текущий элемент\n'
                          u'Клавиша «-» --- Уменьшить текущий элемент\n'
                          u'Клавиша «a» --- Выделить все элементы\n'
                          u'Клавиша «s» --- Сохраненить элементы в текущем сеансе\n'
                          u'Клавиша «l» --- Загрузить ранее сохраненные элементы в текущем сеансе\n'
                          u'Клавиша «h» --- Отобразить данное окно помощи\n'
                          u'Клавиша «Delete» --- Удалить выделенные элементы')

        self.closeButton = QtGui.QPushButton(u'Закрыть')
        self.myLayout = QtGui.QGridLayout(self)
        self.myLayout.addWidget(self.text, 1, 1, 1, 1)
        self.myLayout.addWidget(self.closeButton, 1, 2, 1, 1)

        self.setLayout(self.myLayout)

        self.connect(self.closeButton,
                     SIGNAL('clicked()'),
                     SLOT('close()'))


class CAngelDialog(QtGui.QDialog, Ui_AngelDialog):
    def __init__(self, dataText, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.dataText = dataText
        self.marksData, self.imgCode = dataSeparation(dataText)
        self.scene = CAngelScene(self)
        self.checkedItemInString = u'Квадрат'
        self.checkedColourInString = u'Черный'
        self.colour = QtGui.QColor(0x000000)
        self.setLabelText()
        self.markSize = 1
        self.isResizeByPixmap = False
        self.graphicsView.setScene(self.scene)
        self.pixmap = self.getPixmap()
        self.addImage()
        self.scene.loadMarks(self.marksData)
        self.colourButtonBox = QtGui.QButtonGroup(self)
        self.colourButtonBox.addButton(self.btnBlue)
        self.colourButtonBox.addButton(self.btnGreen)
        self.colourButtonBox.addButton(self.btnRed)
        self.colourButtonBox.addButton(self.btnYellow)
        self.colourButtonBox.addButton(self.btnBlack)
        self.actionButtonBox = QtGui.QButtonGroup(self)
        self.actionButtonBox.addButton(self.btnRect)
        self.actionButtonBox.addButton(self.btnEllipse)
        self.actionButtonBox.addButton(self.btnText)
        self.actionButtonBox.addButton(self.btnCross)
        self.connect(self.btnSave, SIGNAL('clicked()'), self.saveItems)
        self.connect(self.btnLoad, SIGNAL('clicked()'), self.loadItems)
        self.connect(self.btnHelp, SIGNAL('clicked()'), self.helpWindowOpen)
        self.connect(self.scene, SIGNAL('itemWasAdded()'), self.checkCrossButton)
        self.connect(self.scene, SIGNAL('marksDataSaved()'), self.setSavedMarksData)
        self.setWindowTitle(u'Редактор отметок')

    def exec_(self):
        self.resetViewToPixmap()
        return QtGui.QDialog.exec_(self)

    def accept(self):
        self.saveData()
        QtGui.QDialog.accept(self)

    def saveItems(self):
        self.scene.saveItems()

    def loadItems(self):
        self.scene.loadItems(self.scene.marksData)

    def setLabelText(self):
        text = u'\n'.join([self.checkedItemInString, self.checkedColourInString])
        self.lblItemInfo.setText(text)
        size = self.lblColour.frameSize()
        pixmap = QtGui.QPixmap(size.width(), size.height())
        pixmap.fill(self.colour)
        self.lblColour.setPixmap(pixmap)

    def checkCrossButton(self):
        self.btnCross.setChecked(True)

    def setMarkSize(self, markSize):
        if markSize:
            self.scene.setMarkSize(markSize)
        else:
            self.scene.setMarkSize(1)

    def saveData(self):
        self.scene.saveItems()
        self.setSavedMarksData()
        return True

    def setSavedMarksData(self):
        self.marksData = self.scene.marksData

    def getPixmap(self):
        try:
            db = QtGui.qApp.db
            where = 'code=\'%s\'' % self.imgCode
            record = db.getRecordEx('rbImageMap', 'image', where)
            ba = record.value('image').toByteArray()
            image = QtGui.QImage.fromData(ba)
            pixmap = QtGui.QPixmap.fromImage(image)
            self.scene.savingAbility = True
            return pixmap
        except:
            self.scene.savingAbility = False

    def helpWindowOpen(self):
        self.scene.helpOpen()

    def setBlackColour(self):
        self.scene.setColour('Black')
        colour = QtGui.QColor(0x000000)
        colour.setAlpha(100)
        self.setColourToItems(colour)

    def setYellowColour(self):
        self.scene.setColour('Yellow')
        colour = QtGui.QColor(0xFFFF00)
        colour.setAlpha(100)
        self.setColourToItems(colour)

    def setBlueColour(self):
        self.scene.setColour('Blue')
        colour = QtGui.QColor(0x0000FF)
        colour.setAlpha(100)
        self.setColourToItems(colour)

    def setGreenColour(self):
        self.scene.setColour('Green')
        colour = QtGui.QColor(0x00FF00)
        colour.setAlpha(100)
        self.setColourToItems(colour)

    def setRedColour(self):
        self.scene.setColour('Red')
        colour = QtGui.QColor(0xFF0000)
        colour.setAlpha(100)
        self.setColourToItems(colour)

    def setColourToItems(self, colour):
        self.colour = colour
        listItems = self.scene.selectedItems()
        if listItems:
            for obj in listItems:
                if isinstance(obj, (CGraphicsEllipseItem, CGraphicsRectItem)):
                    obj.setPen(QtGui.QColor(colour))
                    obj.setBrush(colour)
                if isinstance(obj, CGraphicsTextItem):
                    obj.setPlainText(obj.toPlainText())
                    obj.setDefaultTextColor(colour)

    def addImage(self):
        scene = self.graphicsView.scene()
        if self.pixmap:
            pixmapItem = CGraphicsPixmapItem(self.pixmap)
            pixmapItem.setZValue(0)
            pixmapItem.setPos(0, 0)
            scene.addItem(pixmapItem)

    def resetViewToPixmap(self):
        self.isResizeByPixmap = True
        if self.pixmap:
            pRect = self.pixmap.rect()
            pWidth = pRect.width()
            pHeight = pRect.height()

            wRect = self.geometry()
            wWidth = wRect.width()
            wHeight = wRect.height()

            vRect = self.graphicsView.geometry()
            vWidth = vRect.width()
            vHeight = vRect.height()

            width = pWidth + wWidth - vWidth + 3  # без '3' размер чуть меньше чем требуется
            height = pHeight + wHeight - vHeight + 3

            dRect = QtGui.qApp.desktop().availableGeometry()
            if width < dRect.width() and height < dRect.height():
                self.resize(width, height)
            else:
                self.showMaximized()
            self.graphicsView.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    @pyqtSignature('bool')
    def on_btnRect_toggled(self, checked):
        self.scene.setMode(0)
        self.checkedItemInString = u'Квадрат'
        self.setLabelText()

    @pyqtSignature('bool')
    def on_btnEllipse_toggled(self, checked):
        self.scene.setMode(1)
        self.checkedItemInString = u'Круг'
        self.setLabelText()

    @pyqtSignature('bool')
    def on_btnText_toggled(self, checked):
        self.scene.setMode(2)
        self.checkedItemInString = u'Текст'
        self.setLabelText()

    @pyqtSignature('bool')
    def on_btnCross_toggled(self, checked):
        self.scene.setMode(3)
        self.checkedItemInString = u''
        self.setLabelText()

    @pyqtSignature('bool')
    def on_btnBlue_toggled(self, checked):
        self.setBlueColour()
        self.checkedColourInString = u'Голубой'
        self.setLabelText()

    @pyqtSignature('bool')
    def on_btnGreen_toggled(self, checked):
        self.setGreenColour()
        self.checkedColourInString = u'Зеленый'
        self.setLabelText()

    @pyqtSignature('bool')
    def on_btnRed_toggled(self, checked):
        self.setRedColour()
        self.checkedColourInString = u'Красный'
        self.setLabelText()

    @pyqtSignature('bool')
    def on_btnBlack_toggled(self, checked):
        self.setBlackColour()
        self.checkedColourInString = u'Черный'
        self.setLabelText()

    @pyqtSignature('bool')
    def on_btnYellow_toggled(self, checked):
        self.setYellowColour()
        self.checkedColourInString = u'Желтый'
        self.setLabelText()

    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        self.scene.clearSelection()
        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        dialog = QtGui.QPrintDialog(printer, self)
        if dialog.exec_():
            painter = QtGui.QPainter(printer)
            self.scene.render(painter)
            painter.end()


# ######################################################################################


def translateColour(val):
    try:
        intVal = int(val, 0)
        return QtGui.QColor(intVal)
    except:
        return None


def dataSeparation(dataText):
    if isinstance(dataText, QVariant):
        tmp = dataText.toString().split('</code>')
    else:
        tmp = dataText.split('</code>')
    if len(tmp) > 1:
        marksData = unicode(tmp[1])
        tmp = unicode(tmp[0].split('<code>')[1])
        imgCode = tmp
    else:
        marksData = tmp[0]
        imgCode   = tmp[0]

    return marksData, imgCode


def getImageMapItemsSettings(marksData):
    result = {}  # key - item type; value - list of tuple contain args for each item of this type

    try:
        root = xml.XML(marksData)
        for i in root:
            type = i.get('type')
            if type in ('CGraphicsEllipseItem', 'CGraphicsRectItem'):
                work = True
                if i.find('rect') is not None:
                    rectList = i.find('rect').text.split(',')
                    if len(rectList) == 4:
                        point = QPointF(float(rectList[0]),
                                        float(rectList[1]))
                        rect = QRectF(float(rectList[0]),
                                      float(rectList[1]),
                                      float(rectList[2]),
                                      float(rectList[3]))
                    else:
                        work = False
                else:
                    work = False

                if i.find('pen') is not None:
                    val = translateColour(i.find('pen').text)
                    pen = QtGui.QColor(val) if val else None
                    if pen:
                        pen.setAlpha(100)
                    else:
                        work = False
                else:
                    work = False
                if work:
                    result.setdefault(type, []).append((point, rect, pen))

            if type == 'CGraphicsTextItem':
                work = True
                if i.find('pos') is not None:
                    pos = i.find('pos').text.split(',')
                    if len(pos) == 2:
                        pos = QPointF(int(pos[0]), int(pos[1]))
                    else:
                        work = False
                else:
                    work = False

                if i.find('text') is not None:
                    text = i.find('text').text
                else:
                    work = False

                if i.find('colour') is not None:
                    val = translateColour(i.find('colour').text)
                    colour = QtGui.QColor(val) if val else None
                    if not colour:
                        work = False
                else:
                    work = False

                if i.find('size') is not None:
                    size = int(i.find('size').text)
                else:
                    work = False

                if i.find('rotation') is not None:
                    rotation = int(i.find('rotation').text)
                else:
                    work = False

                if work:
                    result.setdefault(type, []).append((pos, text, colour, size, rotation))
    except:
        pass

    return result


def getMarksSettingsForImageMapActionPropertyType(dataText):
    return getImageMapItemsSettings(dataSeparation(dataText)[0])


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    angelDialog = CAngelDialog('')
    angelDialog.show()
    # angelDialog.resetViewToPixmap()
    app.exec_()
