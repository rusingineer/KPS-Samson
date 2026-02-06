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
from PyQt4.QtCore import Qt, QDate, QEvent, QVariant, pyqtSignature, SIGNAL
from library.TableModel import CCol, CTableModel
from library.DialogBase import CDialogBase
from library.TableModel import CBoolCol, CTextCol
from library.Utils import forceInt, forceRef
from Events.Action import CActionTypeCache
from Ui_AddRelatedAction import Ui_AddRelatedAction


class CAddRelatedAction(CDialogBase, Ui_AddRelatedAction):
  
    def __init__(self, parent, idList):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.selectedActionTypeIdList = []
        self.addModels('ActionTypes', CActionsModel(self))
        self.setModels(self.tblActionTypes, self.modelActionTypes, self.selectionModelActionTypes)
        self.tblActionTypes.setIdList(idList)

    
    def isSelected(self, actionTypeId):
        return actionTypeId in self.selectedActionTypeIdList
    
    
    def setSelected(self, actionTypeId, value):
        present = self.isSelected(actionTypeId)
        if value:
            if not present:
                self.selectedActionTypeIdList.append(actionTypeId)
                return True
        else:
            if present:
                self.selectedActionTypeIdList.remove(actionTypeId)
                return True
        return False
    
    
    def getSelectedList(self):
        result = []
        for actionTypeId in self.selectedActionTypeIdList:
            result.append(actionTypeId)
        return result

class CActionsModel(CTableModel):
    def __init__(self, parent):
        cols = [CEnableCol(u'Включить', ['id'],   20,  parent),
                CTextCol(u'Код', ['code'], 20),
                CTextCol(u'Наименование', ['name'], 20)]
        self.initModel(parent, cols)


    def initModel(self, parent, cols):
        self.parentWidget = parent
        CTableModel.__init__(self, parent, cols, 'ActionType')


    def flags(self, index):
        result = CTableModel.flags(self, index)
        if index.column() == 0:
            result |= Qt.ItemIsUserCheckable
        return result


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        return CTableModel.data(self, index, role)


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole:
            row = index.row()
            id = self._idList[row]
            if not id:
                return False
            self.parentWidget.setSelected(self._idList[row], forceInt(value) == Qt.Checked)
            self.emitDataChanged()
            return True
        return False


class CEnableCol(CBoolCol):
    def __init__(self, title, fields, defaultWidth, selector):
        CBoolCol.__init__(self, title, fields, defaultWidth)
        self.selector = selector

    def checked(self, values):
        actionTypeId = forceRef(values[0])
        if self.selector.isSelected(actionTypeId):
            return CBoolCol.valChecked
        else:
            return CBoolCol.valUnchecked   
        