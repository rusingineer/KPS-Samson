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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt,SIGNAL, QDate, QModelIndex

from library.Utils import forceString
from HospitalBedComboBox          import CHospitalBedModel
from HospitalBedFindComboBoxPopup import CHospitalBedFindComboBoxPopup


class CHospitalBedFindComboBox(QtGui.QComboBox):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                      )
    def __init__(self, parent = None, domain = None, plannedEndDate = None, orgStructureId = None, sex = 0, currentAge = None, bedId = None, eventTypeId = None, begDateAction = None):
        QtGui.QComboBox.__init__(self, parent)
        self.setModelColumn(0)
        self.filter = {}
        self.filter['orgStructureId'] = orgStructureId
        self.filter['eventTypeId'] = eventTypeId
        self.filter['sex'] = sex
        self.filter['currentAge'] = currentAge
        self.filter['domain'] = domain
        self.filter['plannedEndDate'] = plannedEndDate or QDate.currentDate()
        self._model = CHospitalBedModel(self, self.filter)
        self.setModel(self._model)
        self.preferredWidth = 0
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.SizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.setMinimumContentsLength(20)
        self._popup = None
        self.code = bedId
        self.date = QDate.currentDate()
        self.domain = domain
        self.plannedEndDate = plannedEndDate
        self.begDateAction = begDateAction
        self.orgStructureId = orgStructureId
        self.eventTypeId = eventTypeId
        self.sex = sex
        self.currentAge = currentAge


    def showPopup(self):
        if not self._popup:
            self._popup = CHospitalBedFindComboBoxPopup(self)
            self.connect(self._popup,SIGNAL('HospitalBedFindCodeSelected(int)'), self.setValue)
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
        self._popup.setHospitalBedFindCode(self.code)


    def setPreferredWidth(self, preferredWidth):
        self.preferredWidth = preferredWidth


    def setValue(self, id):
        self.code = id
        self.updateText()


    def value(self):
        return self.code


    def setCurrentIndex(self, index):
        if not index:
            index = QModelIndex()
        if index:
            QtGui.QComboBox.setCurrentIndex(self, index.row())


    def updateText(self):
        if self.code:
            self.setEditText(forceString(QtGui.qApp.db.translate('OrgStructure_HospitalBed', 'id', self.code, 'CONCAT(code,\' | \',name)')))
        else:
            self.setEditText('')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.showPopup()
        else:
            QtGui.QComboBox.keyPressEvent(self, event)


class CHospitalBedFindComboBoxEditor(QtGui.QComboBox):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                      )
    def __init__(self, parent):
        QtGui.QComboBox.__init__(self, parent)
        self.SizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
        self.setModelColumn(0)
        self.filter = {}
        self._model = CHospitalBedModel(self, self.filter)
        self.setModel(self._model)
        self.preferredWidth = 0
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self._popup = None
        self.code = None
        self.date = QDate.currentDate()
        self.domain = None
        self.plannedEndDate = None
        self.begDateAction = None
        self.orgStructureId = None
        self.sex = None
        self.currentAge = None
        self.eventTypeId = None


    def showPopup(self):
        if not self._popup:
            self._popup = CHospitalBedFindComboBoxPopup(self)
            self.connect(self._popup,SIGNAL('HospitalBedFindCodeSelected(int)'), self.setValue)
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
        self._popup.setHospitalBedFindCode(self.code)


    def setBedId(self, bedId):
        self.code = bedId


    def setDomain(self, domain):
        self.filter['domain'] = domain
        self.domain = domain


    def setPlannedEndDate(self, plannedEndDate):
        self.filter['plannedEndDate'] = plannedEndDate
        self.plannedEndDate = plannedEndDate


    def setBegDateAction(self, begDateAction):
        self.filter['begDateAction'] = begDateAction
        self.begDateAction = begDateAction


    def setOrgStructureId(self, orgStructureId):
        self.filter['orgStructureId'] = orgStructureId
        self.orgStructureId = orgStructureId


    def setSex(self, sex):
        self.filter['sex'] = sex
        self.sex = sex


    def setPreferredWidth(self, preferredWidth):
        self.preferredWidth = preferredWidth


    def setValue(self, id):
        self.code = id
        self.updateText()


    def value(self):
        return self.code


    def setCurrentIndex(self, index):
        if not index:
            index = QModelIndex()
        if index:
            QtGui.QComboBox.setCurrentIndex(self, index.row())


    def updateText(self):
        if self.code:
            self.setEditText(forceString(QtGui.qApp.db.translate('OrgStructure_HospitalBed', 'id', self.code, 'CONCAT(code,\' | \',name)')))
        else:
            self.setEditText('')

