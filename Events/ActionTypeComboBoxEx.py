# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL, Qt, QModelIndex, QVariant

from library.InDocTable import CInDocTableCol
from library.Utils import forceInt, toVariant, forceRef

from Events.ActionTypeComboBoxExPopup import CActionTypeComboBoxExPopup
from Events.ActionTypeComboBox import CActionTypeComboBox


class CActionTypeComboBoxEx(CActionTypeComboBox):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                      )

    def __init__(self, parent = None):
        CActionTypeComboBox.__init__(self, parent)
        self._popup=None
        self.actionTypeId = None
        self.classesPopup = range(4)
        self.classesPopupVisible = False
        self.serviceType = None
        self.isPlanOperatingDay = False
        self.flatCode = None
        self.orgStructureId = None #QtGui.qApp.currentOrgStructureId()
        self.preferableOrgStructure = 0
        self.actionTypeIdList = []


    def _createPopup(self):
        if not self._popup:
            self._popup = CActionTypeComboBoxExPopup(self)
            self.connect(self._popup,SIGNAL('actionTypeIdChanged(int)'), self.setValue)
        if self._popup:
            self._popup.setClassesPopup(self.classesPopup)
            self._popup.setClassesPopupVisible(self.classesPopupVisible)
            self._popup.setActionTypeIdList(self.actionTypeIdList)
            self._popup.setServiceType(self.serviceType)
            self._popup.setPlanOperatingDay(self.isPlanOperatingDay)
            self._popup.setOrgStructure(self.orgStructureId)
            self._popup.setPreferableOrgStructure(self.preferableOrgStructure)
            self._popup.setFlatCode(self.flatCode)
            self._popup.initModel(self.value())


    def showPopup(self):
        self._createPopup()
        pos = self.rect().bottomLeft()
        pos = self.mapToGlobal(pos)
        size = self._popup.sizeHint()
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        size.setWidth(screen.width())
        pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
        pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
        self._popup.move(pos)
        self._popup.resize(size)
        self._popup.show()


    def setClassesPopup(self, classes):
        self.classesPopup = classes


    def setClassesPopupVisible(self, value):
        self.classesPopupVisible = value


    def setActionTypeIdList(self, actionTypeIdList):
        self.actionTypeIdList = actionTypeIdList


    def setServiceType(self, serviceType):
        self.serviceType = serviceType


    def setOrgStructure(self, value):
        self.orgStructureId = value


    def setPreferableOrgStructure(self, value):
        self.preferableOrgStructure = value


    def setPlanOperatingDay(self, isPlanOperatingDay):
        self.isPlanOperatingDay = isPlanOperatingDay


    def setFlatCode(self, flatCode):
        self.flatCode = flatCode


    def setValue(self, id):
        self.actionTypeId = id
        index = self._model.findItemId(id)
        self.setCurrentModelIndex(index)


    def value(self):
        modelIndex = self.currentModelIndex()
        if modelIndex and modelIndex.isValid():
            return self._model.itemId(modelIndex)
        return None


    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.hidePopup()
            self.setCurrentModelIndex(QModelIndex())
            self._selectedModelIndex = None
            event.accept()
        else:
            QtGui.QComboBox.keyPressEvent(self, event)


class CActionTypeFindInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, actionTypeClass, serviceType = None, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.tableName  = tableName
        self.filter     = params.get('filter', '')
        self.preferredWidth = params.get('preferredWidth', None)
        self.actionTypeClass = [actionTypeClass] if actionTypeClass is not None else range(4)
        self.serviceType = serviceType
        self.isPlanOperatingDay = params.get('isPlanOperatingDay', False)
        self.orgStructureId =  params.get('orgStructureId', None)
        self.currentActionType = None
        self.preferableOrgStructure = params.get('isPreferableOrgStructure', False)
        self.caches = {}


    def toString(self, val, record):
        actionTypeId = forceRef(val)
        if actionTypeId:
            actionTypeName = self.caches.get(actionTypeId, None)
            if not actionTypeName:
                actionTypeName = QtGui.qApp.db.translate('ActionType','id', val, 'CONCAT_WS(\' | \', code, name)')
                self.caches[actionTypeId] = actionTypeName
            if actionTypeName:
                return toVariant(actionTypeName)
        return QVariant()


    def createEditor(self, parent):
        editor = CActionTypeComboBoxEx(parent)
        editor.setClassesPopup(self.actionTypeClass)
        editor.setServiceType(self.serviceType)
        editor.setOrgStructure(self.orgStructureId)
        editor.setPreferableOrgStructure(self.preferableOrgStructure)
        editor.setPlanOperatingDay(self.isPlanOperatingDay)
        editor.setValue(self.currentActionType)
        return editor


    def setEditorData(self, editor, value, record):
        editor.setValue(forceInt(value))


    def getEditorData(self, editor):
        return toVariant(editor.value())


    def setCurrentActionType(self, value):
        self.currentActionType = value
