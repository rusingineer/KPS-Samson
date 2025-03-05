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
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, QDate, QObject

from library.ItemsListDialog import CItemsListDialog, CItemEditorDialog
from library.IdentificationModel import CIdentificationModel, checkIdentification
from library.ItemEditorDialogWithIdentification import CItemEditorDialogWithIdentification
from library.ICDInDocTableCol import CICDExInDocTableCol
from library.InDocTable       import CInDocTableModel, CRBInDocTableCol, CInDocTableCol
from library.TableModel       import CTextCol
from library.Utils            import forceStringEx, toVariant, forceRef
from Events.Utils             import checkDiagnosis
from RefBooks.Tables          import rbCode, rbHurtType, rbName

from Ui_RBHurtTypeEditor import Ui_RBHurtTypeEditor


class CRBHurtTypeList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',          [rbCode], 20),
            CTextCol(u'Наименование', [rbName], 40),
            ], rbHurtType, [rbCode, rbName])
        self.setWindowTitleEx(u'Типы вредности')


    def getItemEditor(self):
        return CRBHurtTypeEditor(self)


class CRBHurtTypeEditor(Ui_RBHurtTypeEditor, CItemEditorDialogWithIdentification):
    def __init__(self,  parent):
        CItemEditorDialogWithIdentification.__init__(self, parent, rbHurtType)
        self.setWindowTitleEx(u'Тип вредности')


    def preSetupUi(self):
        CItemEditorDialog.preSetupUi(self)
        self.addModels('Diagnosis', CDiagnosisModel(self))
        self.addModels('Infections', CInfectionsModel(self))
        self.addModels('Identification', CRBHurtTypeIdentificationModel(self, self._tableName + '_Identification', self._tableName))


    def postSetupUi(self):
        CItemEditorDialog.postSetupUi(self)
        self.setModels(self.tblDiagnosis, self.modelDiagnosis, self.selectionModelDiagnosis)
        self.setModels(self.tblInfections, self.modelInfections, self.selectionModelInfections)
        self.setModels(self.tblIdentification, self.modelIdentification, self.selectionModelIdentification)
        self.tblDiagnosis.addPopupDelRow()
        self.tblInfections.addPopupDelRow()
        self.tblIdentification.addPopupDelRow()


    def setRecord(self, record):
        CItemEditorDialog.setRecord(self, record)
        self.modelDiagnosis.loadItems(self.itemId())
        self.modelInfections.loadItems(self.itemId())
        self.modelIdentification.loadItems(self.itemId())


    def getRecord(self):
        record = CItemEditorDialog.getRecord(self)
        return record


    def saveInternals(self, id):
        self.modelDiagnosis.saveItems(id)
        self.modelInfections.saveItems(id)
        self.modelIdentification.saveItems(id)


    def checkDataEntered(self):
        result = CItemEditorDialog.checkDataEntered(self)
        result = result and self.checkMKBUnique(self.tblDiagnosis)
        result = result and self.checkInfection(self.tblInfections)
        result = result and self.checkInfectionUnique(self.tblInfections)
        result = result and checkIdentification(self, self.tblIdentification)
        return result


    def checkInfection(self, widget):
        model = widget.model()
        for row, item in enumerate(model.items()):
            infectionId = forceRef(item.value('infection_id'))
            if not infectionId:
                self.checkInputMessage(u'инфекцию', False, widget, row, 1)
                return False
        return True


    def checkValueMessage(self, message, skipable, widget, row=None, column=None, detailWdiget=None, setFocus=True):
        buttons = QtGui.QMessageBox.Ok
        if skipable:
            buttons = buttons | QtGui.QMessageBox.Ignore
        res = QtGui.QMessageBox.critical( self if self.isVisible() else None,
                                         u'Внимание!',
                                         message,
                                         buttons,
                                         QtGui.QMessageBox.Ok)
        if res == QtGui.QMessageBox.Ok:
            if setFocus:
                self.setFocusToWidget(widget, row, column)
                if isinstance(detailWdiget, QtGui.QWidget):
                    self.setFocusToWidget(detailWdiget, row, column)
            return False
        return True


    def checkMKBUnique(self, widget):
        MKBList = []
        model = widget.model()
        for row, item in enumerate(model.items()):
            MKB = forceStringEx(item.value('MKB'))
            if MKB:
                if MKB in MKBList:
                    self.checkValueMessage(u'Код %s уже присутствует в списке!'%(MKB), False, widget, row, 0)
                    return False
                MKBList.append(MKB)
        return True


    def checkInfectionUnique(self, widget):
        infectionList = []
        model = widget.model()
        for row, item in enumerate(model.items()):
            infectionId = forceRef(item.value('infection_id'))
            if infectionId:
                if infectionId in infectionList:
                    db = QtGui.qApp.db
                    table = db.table('rbInfection')
                    record = db.getRecordEx(table, [table['code'], table['name']], [table['id'].eq(infectionId)])
                    infectionCode = forceStringEx(record.value('code'))
                    infectionName = ((infectionCode + u'-') if infectionCode else u'') + forceStringEx(record.value('name'))
                    self.checkValueMessage(u'Запись (%s) уже присутствует в списке!'%(infectionName), False, widget, row, 0)
                    return False
                infectionList.append(infectionId)
        return True


    def checkMKBUniqueEditor(self, MKBNew, rowNew):
        if MKBNew:
            MKBList = []
            model = self.tblDiagnosis.model()
            for row, item in enumerate(model.items()):
                MKB = forceStringEx(item.value('MKB'))
                if MKB and MKB not in MKBList:
                    MKBList.append(MKB)
            if MKBNew in MKBList and MKBList.index(MKBNew) != rowNew:
                self.checkValueMessage(u'Код %s уже присутствует в списке!'%(MKBNew), False, self.tblDiagnosis, row, 0)
                return False
        return True


    def checkInfectionUniqueEditor(self, infectionIdNew, rowNew):
        if infectionIdNew:
            infectionList = []
            model = self.tblInfections.model()
            for row, item in enumerate(model.items()):
                infectionId = forceRef(item.value('infection_id'))
                if infectionId and infectionId not in infectionList:
                    infectionList.append(infectionId)
            if infectionIdNew in infectionList and infectionList.index(infectionIdNew) != rowNew:
                db = QtGui.qApp.db
                table = db.table('rbInfection')
                record = db.getRecordEx(table, [table['code'], table['name']], [table['id'].eq(infectionIdNew)])
                infectionCode = forceStringEx(record.value('code'))
                infectionName = ((infectionCode + u'-') if infectionCode else u'') + forceStringEx(record.value('name'))
                self.checkValueMessage(u'Запись (%s) уже присутствует в списке!'%(infectionName), False, self.tblInfections, row, 0)
                return False
        return True


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelDiagnosis_dataChanged(self, topLeft, bottomRight):
        self.setIsDirty()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelInfections_dataChanged(self, topLeft, bottomRight):
        self.setIsDirty()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelIdentification_dataChanged(self, topLeft, bottomRight):
        self.setIsDirty()


class CDiagnosisModel(CInDocTableModel):
    def __init__(self, parent = None):
        CInDocTableModel.__init__(self, 'rbHurtType_MKB', 'id', 'master_id', parent)
        self.addCol(CICDExInDocTableCol(u'Диагноз', 'MKB', 20))


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            newMKB = forceStringEx(value)
            if newMKB:
                row = index.row()
                if not QObject.parent(self).checkMKBUniqueEditor(newMKB, row):
                    return False
                acceptable = checkDiagnosis(QObject.parent(self), newMKB, None, None, None, None, QDate.currentDate())
                if not acceptable:
                    return False
            value = toVariant(newMKB)
            result = CInDocTableModel.setData(self, index, value, role)
            return result
        return CInDocTableModel.setData(self, index, value, role)


class CInfectionsModel(CInDocTableModel):
    def __init__(self, parent = None):
        CInDocTableModel.__init__(self, 'rbHurtType_Infection', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Инфекция', 'infection_id', 20, 'rbInfection'))


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        return result


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            column = index.column()
            row = index.row()
            if column == 0:
                infectionId = forceRef(value)
                if infectionId:
                    if not QObject.parent(self).checkInfectionUniqueEditor(infectionId, row):
                        return False
                value = toVariant(infectionId)
                result = CInDocTableModel.setData(self, index, value, role)
                return result
        return CInDocTableModel.setData(self, index, value, role)


class CRBHurtTypeIdentificationModel(CIdentificationModel):
    def __init__(self, parent, tableName, key):
        CIdentificationModel.__init__(self, parent, tableName, key)
        self.addCol(CInDocTableCol(u'Примечание', 'note', 30))

