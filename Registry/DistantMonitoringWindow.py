# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from library.DialogBase import CConstructHelperMixin

from Ui_DistantMonitoringWindow import Ui_DistantMonitoringWindow


class CDistantMonitoringWindow(QtGui.QWidget, Ui_DistantMonitoringWindow, CConstructHelperMixin):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
