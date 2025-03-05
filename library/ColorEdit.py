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
from PyQt4.QtCore import Qt, SIGNAL, QAbstractTableModel, QVariant



__all__ = [ 'CColorComboBox',
          ]

class CColorComboBoxModel(QAbstractTableModel):
    colorNameList = [
                     '#FFFFFF',  # белый
                     '#C0C0C0',  # серебряный
                     '#964B00',  # коричневый
                     '#FAF0BE',  # blonde
                     '#FF0000',  # красный
                     '#FFA500',  # оранжевый
                     '#FFFF00',  # желтый
                     '#66FF00',  # ярко-зеленый
                     '#8DB600',  # зеленый
                     '#00BFFF',  # голубой
                     '#0000FF',  # синий
                     '#8B00FF',  # фиолетовый
                     '#000000',  # черный
                     '#2D8659',  # бардовый
                     '#DE9A9A',  # бледно-розовый
                     '#770000',  # темно-красный
                     '#FF0066',  # ярко-розовый
                     '#FFABFF',  # сиреневый
                     '#FF8C77',  # бледно-оранжевый
                     '#8FFFB0',  # салатовый
                     '#FF7E8F',  # ярко-розовый
                     ]
    # Если нужно добавить цвет, то записывать его в верхнем регистре, иначе в комбобоксе выбора цвета, вместо нужного будет записываться черный
    colorDict = {}


    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self._colorList = self._colors()


    def columnCount(self, index=None):
        return 1


    def rowCount(self, index=None):
        return len(self._colorList)


    def data(self, index, role=Qt.BackgroundRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.BackgroundRole:
            result = self._colorList[index.row()]
            return result
        return QVariant()


    def color(self, row):
        colorName = unicode(self.data(self.index(row, 0)).toString()).upper()
        return CColorComboBoxModel.colorDict.get(colorName, QtGui.QColor())


    def colorName(self, color):
        return unicode(color.name()).upper()


    def setColor(self, cmb, color):
        if type(color) == QtGui.QColor:
            color = unicode(color.name()).upper()
        if color in CColorComboBoxModel.colorNameList:
            cmb.setStyleSheet('QComboBox { background-color: %s; }'%color)
            return CColorComboBoxModel.colorNameList.index(color)
        else:
            cmb.setStyleSheet('')
            return -1


    @classmethod
    def _colors(cls):
        result = []
        for colorName in cls.colorNameList:
            color = QtGui.QColor(colorName)
            cls.colorDict[colorName] = color
            result.append(QVariant(color))
        return result


class CColorComboBox(QtGui.QComboBox):
    def __init__(self, parent=None):
        QtGui.QComboBox.__init__(self, parent)
        self._model = CColorComboBoxModel(self)
        self.setModel(self._model)
        self.connect(self, SIGNAL('currentIndexChanged(int)'), self.on_currentIndexChanged)


    def color(self):
        rowIndex = self.currentIndex()
        return self._model.color(rowIndex)


    def setColor(self, color):
        rowIndex = self._model.setColor(self, color)
        self.setCurrentIndex(rowIndex)


    def value(self):
        return self.color()


    def setValue(self, value):
        self.setColor(value)


    def colorName(self):
        color = self.color()
        return self._model.colorName(color)


    def on_currentIndexChanged(self, index):
        color = self._model.color(index)
        self.setColor(color)


if __name__ == u'__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    wgt = CColorComboBox()
    wgt.show()
    app.exec_()
