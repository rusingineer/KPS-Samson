# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, SIGNAL

from library.crbcombobox     import CRBComboBox
from library.HierarchicalItemsListDialog import CHierarchicalItemsListDialog
from library.InDocTable      import CRBInDocTableCol, CInDocTableModel
from library.interchange     import getCheckBoxValue, getLineEditValue, setCheckBoxValue, setLineEditValue

from library.ItemsListDialog import CItemEditorBaseDialog
from library.TableModel      import CTextCol
from library.Utils           import forceRef, toVariant


from .Ui_RBSocStatusClassItemEditor import Ui_SocStatusClassItemEditorDialog


class CRBSocStatusClassList(CHierarchicalItemsListDialog):
    def __init__(self, parent):
        CHierarchicalItemsListDialog.__init__(self, parent, [
            CTextCol(   u'Код',          ['code'], 20),
            CTextCol(   u'Наименование', ['name'],   40),
            ], 'rbSocStatusClass', ['code', 'name', 'id'])
        self.setWindowTitleEx(u'Классы социального статуса')


    def preSetupUi(self):
        CHierarchicalItemsListDialog.preSetupUi(self)
        self.modelTree.setLeavesVisible(True)
        self.modelTree.setOrder('code')
#        self.addObject('actDuplicate', QtGui.QAction(u'Дублировать', self))
        self.addObject('actDelete',    QtGui.QAction(u'Удалить', self))


    def postSetupUi(self):
        CHierarchicalItemsListDialog.postSetupUi(self)
#        self.tblItems.createPopupMenu([self.actDuplicate, '-', self.actDelete])
        self.tblItems.createPopupMenu([self.actDelete])
        self.connect(self.tblItems.popupMenu(), SIGNAL('aboutToShow()'), self.popupMenuAboutToShow)


    def getItemEditor(self):
        editor = CSocStatusClassItemEditor(self)
        editor.setGroupId(self.currentGroupId())
        return editor


    def popupMenuAboutToShow(self):
        currentItemId = self.currentItemId()
        self.actDelete.setEnabled(bool(currentItemId) and not self.itemIdIsUsed(currentItemId))


    def itemIdIsUsed(self, itemId):
        db = QtGui.qApp.db
        if db.translate('rbSocStatusClass', 'group_id', itemId, 'id'):
            return True
        if db.translate('rbSocStatusClassTypeAssoc', 'class_id', itemId, 'id'):
            return True
        return False


    @pyqtSignature('')
    def on_actDelete_triggered(self):
        def deleteCurrentInternal():
            currentItemId = self.currentItemId()
            if currentItemId:
                row = self.tblItems.currentIndex().row()
                db = QtGui.qApp.db
                table = db.table('rbSocStatusClass')
                db.deleteRecord(table, table['id'].eq(currentItemId))
                self.renewListAndSetTo()
                self.tblItems.setCurrentRow(row)
        QtGui.qApp.call(self, deleteCurrentInternal)

#
# ##########################################################################
#

class CSocStatusClassItemEditor(CItemEditorBaseDialog, Ui_SocStatusClassItemEditorDialog):
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'rbSocStatusClass')
        self.addModels('Types', CTypesModel(self))
        self.setupUi(self)
        self.setModels(self.tblTypes, self.modelTypes, self.selectionModelTypes)
        self.tblTypes.addPopupDelRow()
        self.setWindowTitleEx(u'Класс социального статуса')
        self.setupDirtyCather()
        self.groupId = None


    def setGroupId(self, id):
        self.groupId = id


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(self.edtCode, record, 'code')
        setLineEditValue(self.edtName, record, 'name')
        setCheckBoxValue(self.chkIsHolded, record, 'isHolded')
        self.groupId = forceRef(record.value('group_id'))
        self.modelTypes.loadItems(self.itemId())
        self.setIsDirty(False)


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue( self.edtCode, record, 'code')
        getLineEditValue( self.edtName, record, 'name')
        getCheckBoxValue(self.chkIsHolded, record, 'isHolded')
        record.setValue('group_id', toVariant(self.groupId))
        return record


    def saveInternals(self, id):
        self.modelTypes.saveItems(id)


    def checkDataEntered(self):
        result = CItemEditorBaseDialog.checkDataEntered(self)
#        result = result and (self.checkRecursion(self.cmbGroup.value()) or self.checkValueMessage(u'попытка создания циклической группировки', False, self.cmbGroup))
        return result


class CTypesModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbSocStatusClassTypeAssoc', 'id', 'class_id', parent)
        self.addCol(CRBInDocTableCol(   u'Наименование',  'type_id',20, 'rbSocStatusType', showFields = CRBComboBox.showNameAndCode))
#        self.setEnableAppendLine(True)
