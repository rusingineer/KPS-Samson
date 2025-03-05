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
from PyQt4.QtCore import QDate, QDateTime, SIGNAL
from library.ClientRecordProperties import CRecordProperties

from library.IdentificationModel import CIdentificationModel
from library.Utils import forceInt, forceRef, forceString, toVariant
from library.interchange import getLineEditValue, setLineEditValue, setRBComboBoxValue, getRBComboBoxValue, setDateEditValue, getDateEditValue
from library.ItemsListDialog import CItemsListDialog, CItemEditorBaseDialog
from library.TableModel import CDateCol, CTextCol, CRefBookCol
from library.crbcombobox import CRBComboBox

from RefBooks.Tables import rbCode, rbName, rbBegDate, rbEndDate, rbContingentKindRemoval

from RefBooks.ContingentKindRemoval.Ui_RBContingentKindRemovalEditor import Ui_ItemEditorDialog


class CRBContingentKindRemovalList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код', [rbCode], 20),
            CTextCol(u'Наименование', [rbName], 40),
            CRefBookCol(u'Вид контингента', ['contingentKind_id'], 'rbContingentKind', 10, CRBComboBox.showCodeAndName),
            CDateCol(u'Дата начала', [rbBegDate], 20),
            CDateCol(u'Дата окончания', [rbEndDate], 20),
            ], rbContingentKindRemoval, [rbCode, rbName, rbBegDate, rbEndDate])
        self.setWindowTitleEx(u'Причины снятия контингента')
        self.actDelete = QtGui.QAction(u'Удалить запись', self)
        self.actProperties = QtGui.QAction(u'Свойства записи', self)
        self.tblItems.addPopupAction(self.actDelete)
        self.tblItems.addPopupAction(self.actProperties)
        
        self.connect(self.tblItems._popupMenu, SIGNAL('aboutToShow()'), self.on_popupMenu_aboutToShow)
        self.connect(self.actProperties, SIGNAL('triggered()'), self.showRecordProperties)
        self.connect(self.actDelete, SIGNAL('triggered()'), self.deleteSelected)

    def on_popupMenu_aboutToShow(self):
        db = QtGui.qApp.db
        selectedIdList = self.tblItems.selectedItemIdList()
        query = db.query('SELECT * from ClientContingentKind where exists(select * from ClientContingentKind where contingentKindRemoval_id in ({})) limit 1'.format(','.join(str(i) for i in selectedIdList)))
        if query.next():
            self.actDelete.setEnabled(False)
        else:
            self.actDelete.setEnabled(True)

    def getItemEditor(self):
        return CRBContingentKindRemovalEditor(self)

    def deleteSelected(self):
        db = QtGui.qApp.db
        selectedIdList = self.tblItems.selectedItemIdList()
        for id in selectedIdList:
            table = db.table(rbContingentKindRemoval)
            tableIdentification = db.table('rbContingentKindRemoval_Identification')
            db.deleteRecord(table, table['id'].eq(id))
            db.deleteRecord(tableIdentification, tableIdentification['master_id'].eq(id))
            self.renewListAndSetTo(None)
            
    def showRecordProperties(self):
        itemId = self.currentItemId()
        CContingentRecordProperties(self, 'rbContingentKindRemoval', itemId).exec_()


class CRBContingentKindRemovalEditor(CItemEditorBaseDialog, Ui_ItemEditorDialog):
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, rbContingentKindRemoval)
        self.setupUi(self)
        self.cmbContingent.setTable('rbContingentKind', True)
        self.cmbContingent.setCurrentIndex(0)
        self.setWindowTitleEx(u'Причины снятия контингента')
        self.modelIdentification = CRBContingentKindRemovalIdentificationModel(self)
        self.tblIdentification.setModel(self.modelIdentification)
        self.tblIdentification.addPopupDelRow()
        self.tblIdentification.setDelRowsChecker(self.modelIdentification.delRowsChecker)
        self._itemId = None
        self.edtBegDate.setDate(QDate())
        self.edtEndDate.setDate(QDate())
        self.setupDirtyCather()

    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        self._itemId = forceInt(record.value('id'))
        setLineEditValue(self.edtCode, record, rbCode)
        setLineEditValue(self.edtName, record, rbName)
        setRBComboBoxValue(self.cmbContingent, record, 'contingentKind_id')
        setDateEditValue(self.edtBegDate, record, rbBegDate)
        setDateEditValue(self.edtEndDate, record, rbEndDate)
        self.modelIdentification.loadItems(self._itemId)

    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        if not self._itemId:
            record.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
            record.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
        getLineEditValue(self.edtCode, record, rbCode)
        getLineEditValue(self.edtName, record, rbName)
        getRBComboBoxValue(self.cmbContingent, record, 'contingentKind_id')
        getDateEditValue(self.edtBegDate, record, rbBegDate)
        getDateEditValue(self.edtEndDate, record, rbEndDate)
        
        return record

    def checkData(self):
        if not self.edtCode.text():
            return self.checkValueMessage(u"Заполните 'Код'!", False, self.edtCode)
        if not self.edtName.text():
            return self.checkValueMessage(u"Заполните 'Наименование'!", False, self.edtName)
        if not self.edtBegDate.date().isValid() and self.edtBegDate.date() != QDate():
            return self.checkValueMessage(u"Некорректная дата начала!", False, self.edtBegDate)
        if not self.edtEndDate.date().isValid() and self.edtEndDate.date() != QDate():
            return self.checkValueMessage(u"Некорректная дата окончания!", False, self.edtEndDate)
        if self.edtEndDate.date().isValid() and self.edtBegDate.date().isValid() and self.edtBegDate.date() > self.edtEndDate.date():
            return self.checkValueMessage(u"Дата окончания не может быть меньше даты начала!", False, self.edtEndDate)
        return True
            
    
    def itemId(self):
        return self._itemId
    
    def accept(self):
        if not self.checkData():
            return
        record = self.getRecord()
        itemId = QtGui.qApp.db.insertOrUpdate('rbContingentKindRemoval', record)
        self.modelIdentification.saveItems(itemId)
        self._itemId = itemId
        CItemEditorBaseDialog.accept(self)


class CRBContingentKindRemovalIdentificationModel(CIdentificationModel):
    def __init__(self, parent):
        CIdentificationModel.__init__(self, parent, 'rbContingentKindRemoval_Identification', 'rbContingentKindRemoval')
        self._cols[2].canBeEmpty = True
        self.addHiddenCol('createDatetime')
        self.addHiddenCol('modifyDatetime')
        self.addHiddenCol('createPerson_id')
        self.addHiddenCol('modifyPerson_id')


    def saveItems(self, masterId):
        for record in self._items:
            if forceRef(record.value('master_id')) == masterId:
                record.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
                record.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
            if record.isNull('createPerson_id'):
                record.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
                record.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
            if record.isNull('createDatetime'):
                record.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                record.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
        CIdentificationModel.saveItems(self, masterId)


class CContingentRecordProperties(CRecordProperties):
    def loadInfo(self):
        if self.recordId is None:
            return u''
        db = QtGui.qApp.db
        fields = [
            'createPerson_id',
            'modifyPerson_id',
            'createDatetime',
            'modifyDatetime',
        ]
        record = db.getRecord(self.table, fields, self.recordId)
        createPersonId = forceRef(record.value('createPerson_id'))
        modifyPersonId = forceRef(record.value('modifyPerson_id'))
        createPerson = db.translate('vrbPersonWithSpeciality', 'id', createPersonId, 'name')
        modifyPerson = db.translate('vrbPersonWithSpeciality', 'id', modifyPersonId, 'name')
        return u'\n'.join([
            u'Идентификатор: ' + forceString(self.recordId),
            u'Создатель записи: ' + forceString(createPerson),
            u'Дата создания записи: ' + forceString(record.value('createDatetime')),
            u'Редактор записи: ' + forceString(modifyPerson),
            u'Дата редактирования записи: ' + forceString(record.value('modifyDatetime')),
        ])
