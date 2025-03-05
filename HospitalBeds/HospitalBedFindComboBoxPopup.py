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
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, QEvent

from library.Utils import forceInt, forceRef
from HospitalBeds.HospitalBedComboBox import CHospitalBedModel

from Ui_HospitalBedFindComboBoxPopup import Ui_HospitalBedFindComboBoxPopup


class CHospitalBedFindComboBoxPopup(QtGui.QFrame, Ui_HospitalBedFindComboBoxPopup):
    __pyqtSignals__ = ('HospitalBedFindCodeSelected(int)',
                      )
    def __init__(self, parent = None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.filter = {}
        self.filter['orgStructureId'] = parent.orgStructureId
        self.filter['sex'] = parent.sex
        self.filter['currentAge'] = parent.currentAge
        self.filter['domain'] = parent.domain
        self.filter['plannedEndDate'] = parent.plannedEndDate
        self.filter['begDateAction'] = parent.begDateAction
        self.filter['eventTypeId'] = parent.eventTypeId
        self.eventTypeId = parent.eventTypeId
        self.begDateAction = parent.begDateAction
        self.tableModel = CHospitalBedModel(self, self.filter)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblHospitalBedFind.setModel(self.tableModel)
        self.tblHospitalBedFind.setSelectionModel(self.tableSelectionModel)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setShortcut(Qt.Key_Return)
        self.tblHospitalBedFind.installEventFilter(self)
        self.cmbOrgStructureBed.setValue(parent.orgStructureId)
        self.cmbSexBed.setCurrentIndex(parent.sex)
        self.edtAgeForBed.setValue(0)
        self.edtAgeToBed.setValue(0)
        self.currentAge = parent.currentAge
        self.cmbHospitalBedProfile.setTable('rbHospitalBedProfile', addNone=True, filter = (u'''endDate IS NULL OR endDate >= %s'''%(QtGui.qApp.db.formatDate(self.begDateAction))) if self.begDateAction else u'')
        self.cmbTypeBed.setTable('rbHospitalBedType', addNone=True)
        self.cmbIsPermanentBed.setCurrentIndex(0)
        self.parent = parent #wtf? скрывать Qt-шный parent - это плохая затея
        self.tblHospitalBedFind.blockSignals(True) # Каждое открытие в expandAll() вызывает несколько сигналов
        self.tblHospitalBedFind.setUpdatesEnabled(False)
        self.tblHospitalBedFind.expandAll()
        self.tblHospitalBedFind.blockSignals(False)
        self.tblHospitalBedFind.setUpdatesEnabled(True)


    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent!=None:
            opt=QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(
                QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if (arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos())):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)


    def closeEvent(self, event):
        QtGui.QFrame.closeEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.tblHospitalBedFind:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblHospitalBedFind.currentIndex()
                self.tblHospitalBedFind.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)


    def getOrgStructureIdList(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBox_reset()


    def on_buttonBox_reset(self):
        self.filter = {}
        self.cmbOrgStructureBed.setValue(self.parent.orgStructureId)
        self.cmbSexBed.setCurrentIndex(self.parent.sex)
        self.edtAgeForBed.setValue(0)
        self.edtAgeToBed.setValue(0)
        self.cmbHospitalBedProfile.setValue(0)
        self.cmbTypeBed.setValue(0)
        self.cmbIsPermanentBed.setCurrentIndex(0)
        self.filter['orgStructureId'] = self.parent.orgStructureId
        self.filter['sex'] = self.parent.sex
        self.tblHospitalBedFind.setModel(None)
        self.tableModel = None
        self.parent.setModel(None)


    def on_buttonBox_apply(self, id = None):
        self.filter = {}
        self.filter['orgStructureId'] = forceRef(self.cmbOrgStructureBed.value())
        self.filter['sex'] = forceInt(self.cmbSexBed.currentIndex())
        self.filter['ageForBed'] = forceInt(self.edtAgeForBed.value())
        self.filter['ageToBed'] = forceInt(self.edtAgeToBed.value())
        self.filter['hospiatBedProfileId'] = forceRef(self.cmbHospitalBedProfile.value())
        self.filter['typeBed'] = forceRef(self.cmbTypeBed.value())
        self.filter['isPermanentBed'] = forceInt(self.cmbIsPermanentBed.currentIndex())
        self.filter['begDateAction'] = self.begDateAction
        self.filter['currentAge'] = self.currentAge
        self.filter['eventTypeId'] = self.eventTypeId
        self.tblHospitalBedFind.setModel(None)
        self.tableModel = CHospitalBedModel(self, self.filter)
        self.tblHospitalBedFind.setModel(self.tableModel)
        self.tabWidget.setCurrentIndex(0)
        self.tblHospitalBedFind.setFocus(Qt.OtherFocusReason)
        self.parent._model = self.tableModel
        self.parent.setModel(self.parent._model)
        self.tblHospitalBedFind.expandAll()


    def setHospitalBedFindCode(self, code):
        self.code = code


    @pyqtSignature('QModelIndex')
    def on_tblHospitalBedFind_doubleClicked(self, index):
        if index.isValid():
            if index.isValid() and (int(index.flags()) & Qt.ItemIsSelectable) != 0:
                self.parent.setCurrentIndex(index)
                self.code = forceInt(self.tableModel.itemId(index))
                self.emit(SIGNAL('HospitalBedFindCodeSelected(int)'), self.code)
                self.close()
