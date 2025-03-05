# -*- coding: utf-8 -*-

import re

from PyQt4 import QtGui
from PyQt4.QtCore import QTimer, pyqtSignature, QModelIndex, Qt
from PyQt4.QtGui import QDialog

from library.DialogBase import CConstructHelperMixin
from library.InDocTable import CRecordListModel, CInDocTableCol, CBoolInDocTableCol, CDateTimeInDocTableCol
from library.TableModel import CTableModel,  CIntCol, CDesignationCol
from library.Utils import exceptionToUnicode, forceString, toVariant, forceRef

import Exchange.AttachService as AttachService

from Ui_ExportDispContactsDialog import Ui_ExportDispContactsDialog


class CExportDispContactsDialog(QDialog, CConstructHelperMixin, Ui_ExportDispContactsDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.addModels('Contacts', CContactsModel(self))
        self.addModels('ContactErrors', CContactErrorsModel(self))
        self.setupUi(self)
        self.setModels(self.tblContacts, self.modelContacts, self.selectionModelContacts)
        self.setModels(self.tblContactErrors, self.modelContactErrors, self.selectionModelContactErrors)
        self.tblContacts.addPopupDelRow()
        self.tblContactErrors.setEnabled(False)
        self.btnApply.setEnabled(False)
        self.controlDisableLevel = 0
        self.cmbOrgStructure.setTable('OrgStructure')
        self.cmbOrgStructure.setFilter(u"""
            length(OrgStructure.bookkeeperCode) = 5
            and exists (
                select *
                from OrgStructure as Child1
                    left join OrgStructure as Child2 on Child2.parent_id = Child1.id
                    left join OrgStructure as Child3 on Child3.parent_id = Child2.id
                    left join OrgStructure as Child4 on Child4.parent_id = Child3.id
                    left join OrgStructure as Child5 on Child5.parent_id = Child4.id
                where Child1.parent_id = OrgStructure.id
                    and (Child1.areaType in (1, 2)
                        or Child2.areaType in (1, 2)
                        or Child3.areaType in (1, 2)
                        or Child4.areaType in (1, 2)
                        or Child5.areaType in (1, 2)
                    )
            )
            """
            )
        self.cmbOrgStructure.setNameField(u"concat(bookkeeperCode, ' - ', name)")
        self.cmbOrgStructure.setOrder(u"bookkeeperCode, name")
        self.cmbOrgStructure.setAddNone(True, u'Не указано')
        self.cmbOrgStructure.setCurrentIndex(0)

    def showEvent(self, event):
        QTimer.singleShot(0, self.updateList)
        
    def disableControls(self, disabled=True):
        if disabled:
            self.controlDisableLevel += 1
        else:
            self.controlDisableLevel -= 1
        if disabled or self.controlDisableLevel == 0:
            self.tblContacts.setDisabled(disabled)
            self.tblContactErrors.setDisabled(disabled or not self.selectionModelContacts.hasSelection())
            self.btnExport.setDisabled(disabled)
            self.btnOK.setDisabled(disabled)
            self.btnCancel.setDisabled(disabled)
            self.btnApply.setDisabled(disabled or not self.modelContacts.hasChanges())

    def enableControls(self):
        self.disableControls(False)

    def controlsDisabled(self):
        return self.controlDisableLevel > 0

    def updateList(self):
        self.disableControls()
        try:
            QtGui.qApp.processEvents()
            self.modelContacts.loadItems()
            self.modelContacts.setCodeMo(self.getSelectedCodeMo())
            self.btnExport.setEnabled(self.modelContacts.realRowCount() > 0)
        except Exception as e:
            QtGui.QMessageBox.critical(self, u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)
        finally:
            self.enableControls()
    
    def export(self):
        self.disableControls()
        try:
            if self.modelContacts.hasChanges() and not self.applyChanges():
                return
            self.btnExport.setText(u'Отправка...')
            QtGui.qApp.processEvents()
            result = AttachService.putEvContacts(self.getSelectedCodeMo())
            successCount = result['successCount']
            errorCount = result['errorCount']
            totalCount = successCount + errorCount
            message = u'Отправлено %d записей' % totalCount
            if totalCount > 0:
                messageParts = []
                if successCount > 0:
                    messageParts.append(u'%d успешно' % successCount)
                if errorCount > 0:
                    messageParts.append(u'%d с ошибками' % errorCount)
                message += u', из них ' + u', '.join(messageParts)
            QtGui.QMessageBox.information(self, u'Экспорт завершен', message, QtGui.QMessageBox.Close)
        except Exception as e:
            QtGui.QMessageBox.critical(self, u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)
        finally:
            self.enableControls()
            self.btnExport.setText(u'Отправить')
            self.updateList()

    def applyChanges(self):
        self.disableControls()
        try:
            valid, message = self.modelContacts.validateItems()
            if valid:
                self.modelContacts.saveItems()
                self.btnApply.setEnabled(False)
                return True
            else:
                QtGui.QMessageBox.warning(self, u'Ошибка ввода', message, QtGui.QMessageBox.Close)
                return False
        except Exception as e:
            QtGui.QMessageBox.critical(self, u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)
            return False
        finally:
            self.enableControls()

    def reject(self):
        if self.modelContacts.hasChanges():
            answer = QtGui.QMessageBox.warning(self,
                u'Список контактов', 
                u'Сохранить изменения?',
                QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel)
            if answer == QtGui.QMessageBox.Cancel:
                return
            elif answer == QtGui.QMessageBox.Yes and not self.applyChanges():
                return
        QtGui.QDialog.reject(self)
    
    def getSelectedCodeMo(self):
        orgStructureId = self.cmbOrgStructure.value()
        if orgStructureId:
            db = QtGui.qApp.db
            codeMo = forceString(db.translate('OrgStructure', 'id', orgStructureId, 'bookkeeperCode'))
        else:
            codeMo = None
        return codeMo

    @pyqtSignature('')
    def on_btnOK_clicked(self):
        if self.modelContacts.hasChanges() and not self.applyChanges():
            return
        self.accept()

    @pyqtSignature('')
    def on_btnApply_clicked(self):
        self.applyChanges()

    @pyqtSignature('')
    def on_btnCancel_clicked(self):
        self.accept()

    @pyqtSignature('')
    def on_btnExport_clicked(self):
        self.export()

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelContacts_dataChanged(self, topLeft, bottomRight):
        self.btnApply.setEnabled(not self.controlsDisabled())

    @pyqtSignature('')
    def on_modelContacts_modelReset(self):
        self.btnApply.setEnabled(False)

    @pyqtSignature('QModelIndex, int, int')
    def on_modelContacts_rowsInserted(self, parent, first, last):
        self.btnApply.setEnabled(not self.controlsDisabled())

    @pyqtSignature('QModelIndex, int, int')
    def on_modelContacts_rowsRemoved(self, parent, first, last):
        self.btnApply.setEnabled(not self.controlsDisabled())

    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        self.modelContacts.setCodeMo(self.getSelectedCodeMo())


class CContactsModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Номер телефона', 'phone', 20, inputMask='(999) 999-99-99'))
        self.addCol(CInDocTableCol(u'Комментарий', 'comment', 20, maxLength=254))
        self.addCol(CBoolInDocTableCol(u'Изменен', 'changed', 20).setReadOnly())
        self.addCol(CBoolInDocTableCol(u'Отправлен успешно', 'exportSuccess', 20).setReadOnly())
        self.addCol(CDateTimeInDocTableCol(u'Дата экспорта', 'exportDate', 20).setReadOnly())
        self._enableAppendLine = True
        self._extColsPresent = False
        self._hasChanges = False
        db = QtGui.qApp.db
        self.table = db.table('disp_Contacts')
        self.codeMo = None
        self.itemsByCodeMo = {}

    def removeRows(self, row, count, parentIndex=QModelIndex()):
        deletedIdList = []
        if 0<=row and row+count<=self.realRowCount():
            records = self.items()[row:row+count]
            for record in records:
                id = forceRef(record.value('id'))
                if id is not None:
                    deletedIdList.append(id)
        removed = CRecordListModel.removeRows(self, row, count, parentIndex)
        if removed:
            self.deletedIds.update(deletedIdList)
            self._hasChanges = True
        return removed

    def loadItems(self):
        db = QtGui.qApp.db
        allRecords = db.getRecordList('disp_Contacts', '*', order='phone')
        self.itemsByCodeMo = {}
        for record in allRecords:
            codeMo = None if record.isNull('code_mo') else forceString(record.value('code_mo'))
            items = self.itemsByCodeMo.setdefault(codeMo, [])
            items.append(record)
        self.modifiedIds = set()
        self.deletedIds = set()
        items = self.itemsByCodeMo.setdefault(self.codeMo, [])
        self.setItems(items)
        self._hasChanges = False
        self.reset()

    def setData(self, index, value, role=Qt.EditRole):
        dataChanged = CRecordListModel.setData(self, index, value, role)
        if dataChanged:
            row = index.row()
            record = self.items()[row]
            id = forceRef(record.value('id'))
            if id is not None:
                self.modifiedIds.add(id)
            record.setValue('changed', toVariant(1))
            self._hasChanges = True
        return dataChanged
        
    def saveItems(self):
        db = QtGui.qApp.db
        table = db.table('disp_Contacts')
        for codeMo, records in self.itemsByCodeMo.iteritems():
            for record in records:
                id = forceRef(record.value('id'))
                if id is None:
                    db.insertRecord(table, record)
                elif id in self.modifiedIds:
                    db.updateRecord(table, record)
        if self.deletedIds:
            db.deleteRecord(table, where=table['id'].inlist(self.deletedIds))
        self.loadItems()

    def getEmptyRecord(self):
        newRecord = QtGui.qApp.db.table('disp_Contacts').newRecord()
        newRecord.setValue('code_mo', self.codeMo)
        return newRecord

    def validateItems(self):
        phones = set()
        for record in self.items():
            phone = forceString(record.value('phone'))
            digits = re.sub(r'[^\d]', '', phone)
            if len(digits) < 10:
                return (False, u'Неправильный номер телефона: ' + phone)
            elif phone in phones:
                return (False, u'Повторяющийся номер телефона: ' + phone)
            phones.add(phone)
        return (True, None)

    def hasChanges(self):
        return self._hasChanges
    
    def setCodeMo(self, newCodeMo):
        self.codeMo = newCodeMo
        items = self.itemsByCodeMo.setdefault(self.codeMo, [])
        self.setItems(items)
        self.reset()


class CContactErrorsModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CIntCol(u'Код ошибки', ['errorType_id'], 20),
            CDesignationCol(u'Текст ошибки', ['errorType_id'], ('disp_ErrorTypes', 'name'), 20)
            ], 'disp_ContactErrors')

    def update(self, contact_id):
        if contact_id is None:
            idList = []
        else:
            db = QtGui.qApp.db
            table = db.table('disp_ContactErrors')
            where = [table['contact_id'].eq(contact_id)]
            idList = db.getIdList(table, where=where)
        self.setIdList(idList)
