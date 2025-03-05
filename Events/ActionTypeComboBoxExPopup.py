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
from PyQt4.QtCore import Qt, QEvent, pyqtSignature, SIGNAL

from Events.ActionTypeComboBox import CActionTypeModel
from Events.Utils              import getActionTypeIdListByFlatCode
from library.Utils             import forceStringEx

from Events.Ui_ActionTypeComboBoxExPopup import Ui_ActionTypeComboBoxExPopup


class CActionTypeComboBoxExPopup(QtGui.QFrame, Ui_ActionTypeComboBoxExPopup):
    __pyqtSignals__ = ('actionTypeIdChanged(int)'
                      )
    def __init__(self, parent = None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.tableModel = CActionTypeModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblActionTypeFind.setModel(self.tableModel)
        self.tblActionTypeFind.setSelectionModel(self.tableSelectionModel)
        self.cmbServiceType.insertSpecialValue('-', None)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setShortcut(Qt.Key_Return)
        self.tblActionTypeFind.installEventFilter(self)
        self.actionTypeIdList = []
        self._parent = parent
        self.actionTypeId = None
        self.serviceType = 0
        self.isPlanOperatingDay = False
        self.flatCode = None
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.tblActionTypeFind.expand(self.tableModel.index(0, 0))
        self.classesPopupVisible = False
        self.showInForm = True


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
        if watched == self.tblActionTypeFind:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblActionTypeFind.currentIndex()
                self.tblActionTypeFind.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBox_reset()


    def on_buttonBox_reset(self):
        #self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.edtCode.setText(u'')
        self.edtName.setText(u'')
        self.edtNomenclatureCode.setText(u'')
        self.cmbServiceType.setCurrentIndex(self.serviceType)
        self.chkPreferable.setChecked(False)
        self.chkPreferableOrgStructure.setChecked(False)
        self.chkShowInForm.setChecked(True)
        self.cmbSex.setCurrentIndex(0)
        self.spbAgeFor.setValue(0)
        self.spbAgeTo.setValue(150)


    def on_buttonBox_apply(self, id = None):
        crIdList = self.getActionTypeFindIdList()
        self.setActionTypeFindIdList(crIdList, id)
        if not id:
            self.tblActionTypeFind.expand(self.tableModel.index(0, 0))


    def initModel(self, id=None):
        self.on_buttonBox_apply(id)


    def setClassesPopup(self, classes):
        self.classesPopup = classes
        #self.tableModel.setClasses(self.classesPopup)


    def setClassesPopupVisible(self, value):
        self.classesPopupVisible = value
        self.tableModel.setClassesVisible(self.classesPopupVisible)


    def setOrgStructure(self, value):
        self.cmbOrgStructure.setValue(value)


    def setPreferableOrgStructure(self, value):
        self.chkPreferableOrgStructure.setChecked(value)


    def setPlanOperatingDay(self, value):
        self.isPlanOperatingDay = value
        self.cmbServiceType.setEnabled(not self.isPlanOperatingDay)


    def setFlatCode(self, flatCode):
        self.flatCode = flatCode


    def setServiceType(self, value):
        if value is not None:
            self.serviceType = value + 1
        self.cmbServiceType.setCurrentIndex(self.serviceType)


    def setActionTypeFindIdList(self, idList, posToId):
        if idList:
            self.tableModel.setEnabledActionTypeIdList(idList)
            self.tabWidget.setCurrentIndex(0)
            self.tabWidget.setTabEnabled(0, True)
            self.tblActionTypeFind.setFocus(Qt.OtherFocusReason)
            index = self.tableModel.findItemId(posToId)
            if index:
                parentIndex = self.tableModel.parent(index)
                self.tblActionTypeFind.expand(parentIndex)
                self.tblActionTypeFind.setCurrentIndex(index)
        else:
            self.tabWidget.setCurrentIndex(1)
            self.tabWidget.setTabEnabled(0, False)


    def getActionTypeFindIdList(self):
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        tableRbService = db.table('rbService')
        queryTable = tableActionType
        cond = [tableActionType['deleted'].eq(0)]
        if self.actionTypeIdList:
            cond.append(tableActionType['id'].inlist(self.actionTypeIdList))
        if self.flatCode:
            actionTypeIdList = getActionTypeIdListByFlatCode(self.flatCode)
            if actionTypeIdList:
                cond.append(tableActionType['id'].inlist(actionTypeIdList))
        if self.classesPopup:
            cond.append(tableActionType['class'].inlist(self.classesPopup))
        code = forceStringEx(self.edtCode.text())
        if code:
#            cond.append('''ActionType.code LIKE '%s' '''%(u'%'+ code + u'%'))
            cond.append(tableActionType['code'].contain(code))
        name = forceStringEx(self.edtName.text())
        if name:
#            cond.append('''ActionType.name LIKE '%s' '''%(u'%'+ name + u'%'))
            cond.append(tableActionType['name'].contain(name))
        nomenclatureCode = forceStringEx(self.edtNomenclatureCode.text())
        if nomenclatureCode:
            queryTable = queryTable.innerJoin(tableRbService, tableRbService['id'].eq(tableActionType['nomenclativeService_id']))
            cond.append(tableRbService['code'].contain(nomenclatureCode))
        serviceType = self.cmbServiceType.value()
        if serviceType is not None:
            cond.append(tableActionType['serviceType'].eq(serviceType))
        isPreferable = self.chkPreferable.isChecked()
        if isPreferable:
            cond.append(tableActionType['isPreferable'].eq(isPreferable))
        orgStructureId = self.cmbOrgStructure.value()
        if orgStructureId:
            orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
            tableActionTypeOS = db.table('OrgStructure_ActionType')
            queryTable = queryTable.innerJoin(tableActionTypeOS, tableActionTypeOS['actionType_id'].eq(tableActionType['id']))
            isPreferableOS = self.chkPreferableOrgStructure.isChecked()
            if isPreferableOS:
                cond.append(tableActionTypeOS['isPreferable'].eq(isPreferableOS))
            cond.append(tableActionTypeOS['master_id'].inlist(orgStructureIdList))
        sex = self.cmbSex.currentIndex()
        if sex:
            cond.append(tableActionType['sex'].eq(sex))
        ageFor = self.spbAgeFor.value()
        ageTo = self.spbAgeTo.value()
        if ageFor and ageTo and ageFor <= ageTo:
            cond.append(tableActionType['age'].ge(ageFor))
            cond.append(tableActionType['age'].le(ageTo))
        if self.chkShowInForm.isChecked():
            self.showInForm = True
            cond.append(tableActionType['showInForm'].eq(1))
            cond.append("""CASE
			WHEN  ActionType.group_id IS NOT NULL
				THEN (SELECT at2.showInForm FROM ActionType at2 WHERE at2.id = ActionType.group_id ) = 1
			ELSE 1
		END """)
        else:
            self.showInForm = False

        idList = db.getDistinctIdList(queryTable, tableActionType['id'].name(),
                              where=cond,
                              order=u'ActionType.name ASC')
        if idList:
            idList = db.getTheseAndParents('ActionType', 'group_id', idList)
        return idList


    def setActionTypeIdList(self, actionTypeIdList):
        self.actionTypeIdList = actionTypeIdList


    def setActionTypeId(self, actionTypeId):
        self.actionTypeId = actionTypeId
        self.on_buttonBox_apply(self.actionTypeId)


    def selectActionTypeId(self, actionTypeId):
        self.actionTypeId = actionTypeId
        if actionTypeId is None:
            actionTypeId = 0
        self.emit(SIGNAL('actionTypeIdChanged(int)'), actionTypeId)
        self.close()


    def getCurrentActionTypeId(self):
        curIndex = self.tblActionTypeFind.currentIndex()
        return self.tableModel.itemId(curIndex)


    @pyqtSignature('QModelIndex')
    def on_tblActionTypeFind_doubleClicked(self, index):
        if index.isValid():
            if (Qt.ItemIsEnabled & self.tableModel.flags(index)):
                actionTypeId = self.getCurrentActionTypeId()
                self.selectActionTypeId(actionTypeId)

