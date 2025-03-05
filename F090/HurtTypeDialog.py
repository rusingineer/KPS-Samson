#!/usr/bin/env python
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


from PyQt4.QtCore import Qt, SIGNAL, QVariant

from library.DialogBase  import CDialogBase
from library.TableModel  import CTableModel, CBoolCol, CRefBookCol, forceInt
from library.crbcombobox import CRBComboBox
from library.Utils       import forceRef

from F090.Ui_HurtTypeDialog import Ui_HurtTypeDialog


class CHurtTypeDialog(CDialogBase, Ui_HurtTypeDialog):
    def __init__(self, parent, idList=[]):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.idList = idList
        self.model = CHurtTypeDialogTableModel(self)
        self.model.setIdList(self.idList)
        self.tblHurtType.setModel(self.model)
        if idList:
            self.tblHurtType.selectRow(0)


    def selectItem(self):
        return self.exec_()


    def setCurrentItemId(self, itemId):
        self.tblHurtType.setCurrentItemId(itemId)


    def currentItemId(self):
        return self.tblHurtType.currentItemId()


    def getCheckedId(self):
        return self.model.enableIdList[0] if len(self.model.enableIdList) > 0 else None


class CHurtTypeDialogTableModel(CTableModel):
    class CEnableCol(CBoolCol):
        def __init__(self, title, fields, defaultWidth, selector):
            CBoolCol.__init__(self, title, fields, defaultWidth)
            self.selector = selector

    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.enableIdList = []
        self.includeItems = {}
        self.addColumn(self.CEnableCol(u'Выбрать', ['id'], 5, self))
        self.addColumn(CRefBookCol(u'Выполняемые работы', ['id'], 'rbHurtType', 20, showFields=CRBComboBox.showCodeAndName))
        self.setTable('rbHurtType')


    def flags(self, index):
        result = CTableModel.flags(self, index)
        if index.column() == 0:
            result |= Qt.ItemIsUserCheckable
        else:
            result = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return result


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.CheckStateRole:
            column = index.column()
            if column == 0:
                row    = index.row()
                (col, values) = self.getRecordValues(column, row)
                id = forceRef(values[0])
                if id in self.enableIdList:
                    return QVariant(Qt.Checked)
                else:
                    return QVariant(Qt.Unchecked)
        return CTableModel.data(self, index, role)


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        id = self._idList[row]
        if role == Qt.CheckStateRole and column == 0:
            id = self._idList[row]
            self.enableIdList = []
            if forceInt(value) == Qt.Checked and id and not self.isSelected(id):
                self.enableIdList.append(id)
            self.emitColumnChanged(column)
            #self.reset()
            return True
        return False


    def isSelected(self, id):
        return id in self.enableIdList


    def setSelected(self, id, value):
        self.enableIdList = []
        if value and id:
            self.enableIdList.append(id)


    def emitCellChanged(self, row, column):
        index = self.index(row, column)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)


    def emitColumnChanged(self, column):
        index1 = self.index(0, column)
        index2 = self.index(self.rowCount(), column)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)

