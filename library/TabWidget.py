# -*- coding: utf-8 -*-

from PyQt4 import QtGui

class CTabWidget(QtGui.QTabWidget):
    __pyqtSignals__ = (
        'tabShown(QWidget*)',
        'tabHidden(QWidget*)',
    )

    def saveTabInfo(self):
        # запомнить названия и порядок оригинальных вкладок, чтобы можно было прятать и показывать
        self.originalTabs = []
        self.originalTitles = []
        for i in xrange(self.count()):
            self.originalTabs.append(self.widget(i))
            self.originalTitles.append(self.tabText(i))

    def isTabVisible(self, tab):
        return (self.indexOf(tab) > -1)
    
    def showTab(self, tab):
        # "показать" вкладку
        if not self.isTabVisible(tab):
            originalIndex = self.originalTabs.index(tab)
            title = self.originalTitles[originalIndex]
            prevTabs = self.originalTabs[:originalIndex]
            prevIndex = -1
            for prevTab in reversed(prevTabs):
                prevIndex = self.indexOf(prevTab)
                if prevIndex > -1:
                    break
            self.insertTab(prevIndex + 1, tab, title)
            self.tabShown.emit(tab)

    def hideTab(self, tab):
        # "спрятать" вкладку
        if self.isTabVisible(tab):
            self.removeTab(self.indexOf(tab))
            self.tabHidden.emit(tab)

    def setTabVisible(self, tab, visible):
        if visible:
            self.showTab(tab)
        else:
            self.hideTab(tab)

    def originalIndex(self, tab):
        try:
            return self.originalTabs.index(tab)
        except:
            return -1
    
    def setTabTextColor(self, index, color):
        self.tabBar().setTabTextColor(index, color)
