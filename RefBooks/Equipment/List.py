# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4        import QtGui
from PyQt4.QtCore import Qt, QDate, QObject, QRegExp, QString, QVariant, pyqtSignature, SIGNAL

from library.DialogBase            import CDialogBase
from library.InDocTable            import CInDocTableModel, CBoolInDocTableCol, CDateInDocTableCol, CEnumInDocTableCol, CFloatInDocTableCol, CInDocTableCol, CRBInDocTableCol
from library.interchange           import (
                                              getCheckBoxValue,
                                              getComboBoxData,
                                              getComboBoxValue,
                                              getDateEditValue,
                                              getLineEditValue,
                                              getRBComboBoxValue,
                                              getSpinBoxValue,
                                              getTextEditValue,
                                              setCheckBoxValue,
                                              setComboBoxData,
                                              setComboBoxValue,
                                              setDateEditValue,
                                              setLineEditValue,
                                              setRBComboBoxValue,
                                              setSpinBoxValue,
                                              setTextEditValue,
                                          )
from library.ItemsListDialog       import CItemsListDialog, CItemEditorBaseDialog
from library.TableModel            import CTableModel, CDateCol, CEnumCol, CNumCol, CRefBookCol, CTextCol
from library.Utils                 import copyFields, forceDate, forceInt, forceRef, forceString, forceStringEx

from RefBooks.Tables              import rbCode, rbEquipment, rbEquipmentClass, rbEquipmentType, rbName
from .Protocol                    import CEquipmentProtocol

from .Ui_SpecimenTypeChoiceDialog import Ui_SpecimenTypeChoiceDialog
from .Ui_EquipmentsListDialog     import Ui_EquipmentsListDialog
from .Ui_RBEquipmentEditor        import Ui_RBEquipmentEditorDialog


class CRBEquipmentList(Ui_EquipmentsListDialog, CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',          [rbCode], 20),
            CTextCol(u'Наименование', [rbName], 40),
            CRefBookCol(u'Тип оборудования', ['equipmentType_id'], rbEquipmentType, 10, 2),
            CRefBookCol(u'Подразделение', ['orgStructure_id'], 'OrgStructure', 10, 2),
            CTextCol(u'Инвентаризационный номер', ['inventoryNumber'], 10),
            CTextCol(u'Модель', ['model'], 10),
            CTextCol(u'Серийный номер', ['serialNumber'], 10),
            CDateCol(u'Дата выпуска', ['releaseDate'], 8),
            CDateCol(u'Дата ввода в эксплуатацию', ['startupDate'], 8),
            CWorkEnumCol(u'Статус', ['status'], [u'Не работает', u'работает'], 5),
            CNumCol(u'Срок службы(лет)', ['employmentTerm'], 7),
            CNumCol(u'Срок гарантии(месяцев)', ['warrantyTerm'], 7),
            CNumCol(u'Период ТО (целое число месяцев)', ['maintenancePeriod'], 12),
            CEnumCol(u'Период ТО(раз в)', ['maintenanceSingleInPeriod'], [u'Нет',
                                                                          u'Неделя',
                                                                          u'Месяц',
                                                                          u'Квартал',
                                                                          u'Полугодие',
                                                                          u'Год'], 12),
            CTextCol(u'Производитель', ['manufacturer'], 10),
            ], rbEquipment, [rbCode, rbName])
        self.cmbEquipmentType.setTable('rbEquipmentType')
        self.setWindowTitleEx(u'Список оборудования')
        self.tblItems.addPopupDelRow()


    def exec_(self):
        result = CItemsListDialog.exec_(self)
        self.saveCurrentItemJournal()
        return result


    def saveCurrentItemJournal(self):
        equipmentId = self.tblItems.currentItemId()
        if bool(equipmentId):
            self.modelMaintenanceJournal.saveItems(equipmentId)


    def setEditableJournal(self, val):
        self.modelMaintenanceJournal.setEditable(val)


    def setup(self, cols, tableName, order, forSelect=False, filterClass=None):
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.forSelect = forSelect
        self.filterClass = filterClass
        self.props = {}
        self.order = order

        self.modelMaintenanceJournal = CMaintenanceJournalModel(self)
        self.tblMaintenanceJournal.setModel(self.modelMaintenanceJournal)

        self.model = CEquipmentTableModel(self, cols, self.modelMaintenanceJournal)
        self.selectionModel = QtGui.QItemSelectionModel(self.model, self)
        self.model.idFieldName = self.idFieldName
        self.model.setTable(tableName)
        self.tblItems.setModel(self.model)
        self.tblItems.setSelectionModel(self.selectionModel)
        self.btnSelect.setEnabled(self.forSelect)
        self.btnSelect.setVisible(self.forSelect)
        self.btnSelect.setDefault(self.forSelect)
        self.btnFilter.setEnabled(self.forSelect and bool(self.filterClass))
        self.btnFilter.setEnabled(bool(self.filterClass))
        self.btnFilter.setVisible(bool(self.filterClass))
        self.btnEdit.setDefault(not self.forSelect)
        self.tblItems.setFocus(Qt.OtherFocusReason)

        self.btnNew.setShortcut(Qt.Key_F9)
        self.btnEdit.setShortcut(Qt.Key_F4)
        self.btnPrint.setShortcut(Qt.Key_F6)

        self.tblMaintenanceJournal.addPopupDelRow()
        self.tblMaintenanceJournal.addPopupSelectAllRow()
        self.tblMaintenanceJournal.addPopupClearSelectionRow()

        QObject.connect(
            self.tblItems.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)
        QObject.connect(
            self.selectionModel, SIGNAL('currentChanged(QModelIndex, QModelIndex)'), self.on_selectionModel_currentChanged)
        QObject.connect(
            self.modelMaintenanceJournal, SIGNAL('maintenanceDateChanged(int)'), self.model.maintenanceDateChanged)
        QObject.connect(
            self.modelMaintenanceJournal, SIGNAL('rowsRemoved(QModelIndex, int, int)'), self.maintenanceRemoved)


    def renewListAndSetTo(self, itemId=None):
        CItemsListDialog.renewListAndSetTo(self, itemId)
        if bool(itemId):
            self.reloadBackGround(itemId)


    def reloadBackGround(self, itemId):
        self.model.maintenanceDateChanged(itemId)


    def maintenanceRemoved(self, index, start, end):
        equipmentId = self.tblItems.currentItemId()
        self.modelMaintenanceJournal.setNeedSave(True)
        if equipmentId:
            self.reloadBackGround(equipmentId)


    def getItemEditor(self):
        return CRBEquipmentEditor(self)


    def getEquipmentIdList(self, props={}):
        db = QtGui.qApp.db
        tableEquipment = db.table('rbEquipment')
        cond = []
        if self.chkOrgStructure.isChecked():
            orgStructureId = self.cmbOrgStructure.value()
            if bool(orgStructureId):
                cond.append(tableEquipment['orgStructure_id'].eq(orgStructureId))
        if self.chkReleaseDate.isChecked():
            cond.append(tableEquipment['releaseDate'].dateLe(self.edtReleaseDateTo.date()))
            cond.append(tableEquipment['releaseDate'].dateGe(self.edtReleaseDateFrom.date()))
        if self.chkEquipmentType.isChecked():
            equipmentTypeId = self.cmbEquipmentType.value()
            if equipmentTypeId:
                cond.append(tableEquipment['equipmentType_id'].eq(equipmentTypeId))
        if self.chkModel.isChecked():
            model = forceStringEx(self.edtModel.text())
            if model:
                cond.append(tableEquipment['model'].contain(model))
        if self.chkInventoryNumber.isChecked():
            inventoryNumber = forceStringEx(self.edtInventoryNumber.text())
            if inventoryNumber:
                cond.append(tableEquipment['inventoryNumber'].contain(inventoryNumber))
        if self.chkStatus.isChecked():
            cond.append(tableEquipment['status'].eq(self.cmbStatus.currentIndex()))
        if self.chkMaintenance.isChecked():
            tableMaintenance = db.table('EquipmentMaintenanceJournal')
            condValue = self.cmbMaintenance.currentIndex()
            if condValue == 0: # не определено ТО
                cond.append(db.existsStmt(tableMaintenance,
                                          'NOT '+tableMaintenance['master_id'].eq(tableEquipment['id'])))
            elif condValue == 1:# ТО просрочено
                idList = self.model.getIdListByMaintenance()
                cond.append(tableEquipment['id'].inlist(idList))
            elif condValue == 2: # Осталось до окончания ТО
                idList = self.model.getIdListByMaintenance(self.edtMaintenanceTerm.value(),
                                                           self.cmbMaintenanceTermType.currentIndex())
                cond.append(tableEquipment['id'].inlist(idList))
        if self.chkWarranty.isChecked():
            condValue = self.cmbWarranty.currentIndex()
            if condValue == 0: # Гарантия не определена
                cond.append(db.joinOr([tableEquipment['warrantyTerm'].isNull(),
                                      tableEquipment['warrantyTerm'].eq(0)]))
            elif condValue == 1: # На гарантии
                condText = 'DATE(DATE_ADD(%s , INTERVAL %s MONTH)) >= DATE(%s)' %  (tableEquipment['releaseDate'].name(), tableEquipment['warrantyTerm'].name(), db.formatQVariant(QVariant.Date, QVariant(QDate.currentDate())))
                cond.append(condText)
            elif condValue == 2: # Гарантии нет (истекла или не было)
                condText = 'DATE(DATE_ADD(%s , INTERVAL %s MONTH)) < DATE(%s)' %  (tableEquipment['releaseDate'].name(), tableEquipment['warrantyTerm'].name(), db.formatQVariant(QVariant.Date, QVariant(QDate.currentDate())))
                cond.append(db.joinOr([condText,
                             tableEquipment['warrantyTerm'].isNull(),
                             tableEquipment['warrantyTerm'].eq(0)]))
            elif condValue == 3: # До истечения гарантии осталось
                termValue = self.edtWarrantyTerm.value()
                termType  = self.cmbWarrantyTermType.currentIndex()
                if termType == 0:
                    strTermType = 'DAY'
                elif termType == 1:
                    strTermType = 'MONTH'
                elif termType == 2:
                    strTermType = 'YEAR'
                condText = 'DATE(DATE_ADD(%s , INTERVAL %d %s)) = DATE(%s)' %  (tableEquipment['releaseDate'].name(), termValue, strTermType, db.formatQVariant(QVariant.Date, QVariant(QDate.currentDate())))
                cond.append(condText)
        if self.chkEmploymentTerm.isChecked():
            employmentTermValue = self.edtEmploymentTerm.value()
            cond.append(tableEquipment['employmentTerm'].eq(employmentTermValue))
        idList = db.getIdList(tableEquipment, 'id', cond, order=self.order)
        return idList


    def on_filterButtonBox_apply(self, id = None):
#        idList = self.getEquipmentIdList()
        self.renewListAndSetTo(id)


    def on_filterButtonBox_reset(self):
        self.chkOrgStructure.setChecked(False)
        self.cmbOrgStructure.setEnabled(False)

        self.chkReleaseDate.setChecked(False)
        self.edtReleaseDateFrom.setEnabled(False)
        self.edtReleaseDateTo.setEnabled(False)

        self.chkEquipmentType.setChecked(False)
        self.cmbEquipmentType.setEnabled(False)

        self.chkModel.setChecked(False)
        self.edtModel.setEnabled(False)

        self.chkInventoryNumber.setChecked(False)
        self.edtInventoryNumber.setEnabled(False)

        self.chkStatus.setChecked(False)
        self.cmbStatus.setEnabled(False)


    def select(self, props):
        return self.getEquipmentIdList(props)


#    @pyqtSignature('QAbstractButton*')
    def on_filterButtonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.saveCurrentItemJournal()
            self.on_filterButtonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_filterButtonBox_reset()
            self.on_filterButtonBox_apply()
        elif unicode(button.text()) == u'Применить':
            self.saveCurrentItemJournal()
            self.on_filterButtonBox_apply()
        elif unicode(button.text()) == u'Сбросить':
            self.on_filterButtonBox_reset()
            self.on_filterButtonBox_apply()


#    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModel_currentChanged(self, currentIndex, previousIndex):
        if previousIndex.isValid():
            previousEquipmentId = self.tblItems.itemId(previousIndex)
            self.modelMaintenanceJournal.saveItems(previousEquipmentId)
        equipmentId = self.tblItems.currentItemId()
        if bool(equipmentId):
            self.modelMaintenanceJournal.loadItems(equipmentId)
        else:
            self.modelMaintenanceJournal.loadItems(0)



class CRBEquipmentEditor(CItemEditorBaseDialog, Ui_RBEquipmentEditorDialog):
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, rbEquipment)
        self.addModels('Tests', CEquipmentTestModel(self))
        self.setupUi(self)
        self.setWindowTitleEx(u'Оборудование')

        self.setModels(self.tblTests, self.modelTests, self.selectionModelTests)

        self.tblTests.addPopupSelectAllRow()
        self.tblTests.addPopupClearSelectionRow()
        self.tblTests.addPopupSeparator()
        self.tblTests.addPopupDelRow()
        self.tblTests.addPopupSeparator()

        self._actSetSpecimenType = QtGui.QAction(u'Задать тип образца', self)
        self.connect(self._actSetSpecimenType, SIGNAL('triggered()'), self.on_setSpecimenType)
        self.tblTests.popupMenu().addAction(self._actSetSpecimenType)

        self._actCopyWithSpecimenTypeSetting = QtGui.QAction(u'Копировать и задать тип образца', self)
        self.connect(self._actCopyWithSpecimenTypeSetting, SIGNAL('triggered()'), self.on_copyWithSpecimenTypeSetting)
        self.tblTests.popupMenu().addAction(self._actCopyWithSpecimenTypeSetting)
        self.cmbEquipmentClass.setTable(rbEquipmentClass)
        self.cmbEquipmentType.setTable(rbEquipmentType)

        self.cmbProtocol.clear()
        for protocol in (
                          CEquipmentProtocol.manual,
                          CEquipmentProtocol.astm,
#                          CEquipmentProtocol.pacs,
#                          CEquipmentProtocol.fhir050,
                          CEquipmentProtocol.fhir102,
                          CEquipmentProtocol.samson,
                        ):
            self.cmbProtocol.addItem(CEquipmentProtocol.text(protocol), protocol)


    def getSpecimenTypeChoiceWidget(self):
        dlg = CSpecimenTypeChoice(self)
        item = self.tblTests.currentItem()
        if item:
            specimenTypeId = forceRef(item.value('specimenType_id'))
            specimenCode   = forceString(item.value('hardwareSpecimenCode'))
            specimenName   = forceString(item.value('hardwareSpecimenName'))
            dlg.setValues( *(specimenTypeId, specimenCode, specimenName) )
        return dlg


    def on_setSpecimenType(self):
        dlg = self.getSpecimenTypeChoiceWidget()
        if dlg.exec_():
            specimenTypeId = dlg.specimenTypeId()
            specimenCode   = dlg.specimenCode()
            specimenName   = dlg.specimenName()
            items = self.modelTests.items()
            for row in self.tblTests.getSelectedRows():
                items[row].setValue('specimenType_id', QVariant(specimenTypeId))
                items[row].setValue('hardwareSpecimenCode', QVariant(specimenCode))
                items[row].setValue('hardwareSpecimenName', QVariant(specimenName))


    def on_copyWithSpecimenTypeSetting(self):
        dlg = self.getSpecimenTypeChoiceWidget()
        if dlg.exec_():
            specimenTypeId = dlg.specimenTypeId()
            specimenCode   = dlg.specimenCode()
            specimenName   = dlg.specimenName()
            items = list(self.modelTests.items())
            rows = self.tblTests.getSelectedRows()
            for row in rows:
                newRecord = self.modelTests.getEmptyRecord()
                copyFields(newRecord, items[row])
                newRecord.setValue(self.modelTests._idFieldName, QVariant(None))
                newRecord.setValue('specimenType_id', QVariant(specimenTypeId))
                newRecord.setValue('hardwareSpecimenCode', QVariant(specimenCode))
                newRecord.setValue('hardwareSpecimenName', QVariant(specimenName))
                self.modelTests.insertRecord(len(self.modelTests.items()), newRecord)


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(  self.edtCode,                      record, rbCode)
        setLineEditValue(  self.edtName,                      record, rbName)
        equipmentTypeId = forceRef(record.value('equipmentType_id'))
        self.cmbEquipmentType.setValue(equipmentTypeId)
        equipmentClassId = forceRef(QtGui.qApp.db.translate('rbEquipmentType', 'id', equipmentTypeId, 'class_id')) if equipmentTypeId else None
        self.cmbEquipmentClass.setValue(equipmentClassId)
        setRBComboBoxValue(self.cmbOrgStructure,              record, 'orgStructure_id')
        #setSpinBoxValue(   self.edtTripod,                    record, 'tripod')
        setLineEditValue(  self.edtTripodIdentifiers,         record, 'tripod')
        setSpinBoxValue(   self.edtTripodCapacity,            record, 'tripodCapacity')
        setLineEditValue(  self.edtInventoryNumber,           record, 'inventoryNumber')
        setLineEditValue(  self.edtModel,                     record, 'model')
        setLineEditValue(  self.edtSerialNumber,              record, 'serialNumber')
        setDateEditValue(  self.edtReleaseDate,               record, 'releaseDate')
        setDateEditValue(  self.edtStartupDate,               record, 'startupDate')
        setComboBoxValue(  self.cmbStatus,                    record, 'status')
        setSpinBoxValue(   self.edtEmploymentTerm,            record, 'employmentTerm')
        setSpinBoxValue(   self.edtWarrantyTerm,              record, 'warrantyTerm')
        setSpinBoxValue(   self.edtMaintenancePeriod,         record, 'maintenancePeriod')
        setComboBoxValue(  self.cmbMaintenanceSingleInPeriod, record, 'maintenanceSingleInPeriod')
        setLineEditValue(  self.edtManufacturer,              record, 'manufacturer')
        setComboBoxValue(  self.cmbSamplePreparation,         record, 'samplePreparationMode')
        setCheckBoxValue(  self.chkEachTestDetached,          record, 'eachTestDetached')
        setComboBoxData(   self.cmbProtocol,                  record, 'protocol')
        setLineEditValue(  self.edtProtocolVersion,           record, 'protocolVersion')
        setTextEditValue(  self.edtAddress,                   record, 'address')
        setLineEditValue(  self.edtOwnName,                   record, 'ownName')
        setLineEditValue(  self.edtLabName,                   record, 'labName')
        setLineEditValue(  self.edtOwnCode,                   record, 'ownCode')
        setLineEditValue(  self.edtLabCode,                   record, 'labCode')
        setComboBoxValue(  self.cmbSpecimenIdentifierMode,    record, 'specimenIdentifierMode')
        setCheckBoxValue(  self.chkResultOnFact,              record, 'resultOnFact')
        setComboBoxValue(  self.cmbRoleInIntegration,         record, 'roleInIntegration')
        self.modelTests.loadItems(forceRef(record.value('id')))


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(  self.edtCode,                      record, rbCode)
        getLineEditValue(  self.edtName,                      record, rbName)
        getRBComboBoxValue(self.cmbEquipmentType,             record, 'equipmentType_id')
        getRBComboBoxValue(self.cmbOrgStructure,              record, 'orgStructure_id')
        #getSpinBoxValue(   self.edtTripod,                    record, 'tripod')
        getLineEditValue(  self.edtTripodIdentifiers,         record, 'tripod')
        getSpinBoxValue(   self.edtTripodCapacity,            record, 'tripodCapacity')
        getLineEditValue(  self.edtInventoryNumber,           record, 'inventoryNumber')
        getLineEditValue(  self.edtModel,                     record, 'model')
        getLineEditValue(  self.edtSerialNumber,              record, 'serialNumber')
        getDateEditValue(  self.edtReleaseDate,               record, 'releaseDate')
        getDateEditValue(  self.edtStartupDate,               record, 'startupDate')
        getComboBoxValue(  self.cmbStatus,                    record, 'status')
        getSpinBoxValue(   self.edtEmploymentTerm,            record, 'employmentTerm')
        getSpinBoxValue(   self.edtWarrantyTerm,              record, 'warrantyTerm')
        getSpinBoxValue(   self.edtMaintenancePeriod,         record, 'maintenancePeriod')
        getComboBoxValue(  self.cmbMaintenanceSingleInPeriod, record, 'maintenanceSingleInPeriod')
        getLineEditValue(  self.edtManufacturer,              record, 'manufacturer')
        getComboBoxValue(  self.cmbSamplePreparation,         record, 'samplePreparationMode')
        getCheckBoxValue(  self.chkEachTestDetached,          record, 'eachTestDetached')
        getComboBoxData(   self.cmbProtocol,                  record, 'protocol')
        getLineEditValue(  self.edtProtocolVersion,           record, 'protocolVersion')
        getTextEditValue(  self.edtAddress,                   record, 'address')
        getLineEditValue(  self.edtOwnName,                   record, 'ownName')
        getLineEditValue(  self.edtLabName,                   record, 'labName')
        getLineEditValue(  self.edtOwnCode,                   record, 'ownCode')
        getLineEditValue(  self.edtLabCode,                   record, 'labCode')
        getComboBoxValue(  self.cmbSpecimenIdentifierMode,    record, 'specimenIdentifierMode')
        getCheckBoxValue(  self.chkResultOnFact,              record, 'resultOnFact')
        getComboBoxValue(  self.cmbRoleInIntegration,         record, 'roleInIntegration')
        return record


    def saveInternals(self, id):
        self.modelTests.saveItems(id)


    def checkDataEntered(self):
        result = True
        result = result and self.checkModelTests()
        result = result and self.checkEquipmentInterface()
        result = result and self.checkEquipmentCode()
        result = result and self.checkEquipmentName()
        return result


    def checkModelTests(self):
        for row, item in enumerate(self.modelTests.items()):
            if not forceRef(item.value('test_id')):
                return self.checkValueMessage(u'Необходимо указать тест!',
                                              False, self.tblTests, row=row, column=0)
        return True


    def checkEquipmentCode(self):
        if self.edtCode.text().isEmpty():
            return self.checkValueMessage(u'Необходимо указать код оборудования!',
                                          False, self.edtCode)
        return True


    def checkEquipmentName(self):
        if self.edtName.text().isEmpty():
            return self.checkValueMessage(u'Необходимо указать наименование оборудования!',
                                          False, self.edtName)
        return True


    def checkEquipmentInterface(self):
        result = True
        result = result and self.checkEquipmentInterfaceAddress()
        return result


    def checkEquipmentInterfaceAddress(self):
        import json
        address = unicode(self.edtAddress.toPlainText())
        try:
            json.loads(address if address else '{}')
            return True
        except:
            return self.checkValueMessage(u'Адрес интерфейса оборудовния не корректен!\n\n%s' % address,
                                          False, self.edtAddress)


    @pyqtSignature('int')
    def on_cmbMaintenanceSingleInPeriod_currentIndexChanged(self, index):
        if bool(index) and bool(self.edtMaintenancePeriod.value()):
            self.edtMaintenancePeriod.setValue(0)


    @pyqtSignature('int')
    def on_edtMaintenancePeriod_valueChanged(self, value):
        if bool(value) and bool(self.cmbMaintenanceSingleInPeriod.currentIndex()):
            self.cmbMaintenanceSingleInPeriod.setCurrentIndex(0)


    @pyqtSignature('QString')
    def on_edtTripodIdentifiers_textChanged(self, value):
        if value == ';':
            self.edtTripodIdentifiers.setText('')
        elif value.indexOf(QRegExp(';;+')) != -1:
            value.replace(QRegExp(';;+'), ';')
            self.edtTripodIdentifiers.setText(value)
        else:
            self.edtTripod.setValue(0 if not value else len(value.split(';', QString.SkipEmptyParts)))


    @pyqtSignature('int')
    def on_cmbEquipmentClass_currentIndexChanged(self, index):
        typeId = self.cmbEquipmentType.value()
        if not typeId:
            filter = ''
            classId = self.cmbEquipmentClass.value()
            if classId:
                table = QtGui.qApp.db.table('rbEquipmentType')
                filter = table['class_id'].eq(classId)
            self.cmbEquipmentType.setFilter(filter)


    @pyqtSignature('int')
    def on_cmbEquipmentType_currentIndexChanged(self, index):
        typeId = self.cmbEquipmentType.value()
        classId = forceRef(QtGui.qApp.db.translate('rbEquipmentType', 'id', typeId, 'class_id')) if typeId else None
        self.cmbEquipmentClass.setValue(classId)
        self.cmbEquipmentClass.setEnabled(bool(not classId))


    @pyqtSignature('int')
    def on_cmbProtocol_currentIndexChanged(self, index):
        protocol = forceInt(self.cmbProtocol.itemData(index))
        hasAddress = protocol != CEquipmentProtocol.manual
        self.lblAddress.setEnabled(hasAddress)
        self.edtAddress.setEnabled(hasAddress)

# #################################################

class CWorkEnumCol(CEnumCol):
    def getForegroundColor(self, values):
        value = forceInt(values[0])
        if not value:
            return QVariant(QtGui.QColor(255, 0, 0))
        return QVariant()


class CEquipmentTableModel(CTableModel):
    def __init__(self, parent, cols, journalModel=None):
        CTableModel.__init__(self, parent, cols)
        self.mapBackGroundToId = {}
        self.journalModel = journalModel


    def getIdListByMaintenance(self, value=None, valueType=None):
        def checkByValueAndValueType(data, value, valueType):
            backGround, endDate = data
            if (value is None) and (valueType is None):
                return backGround.isValid() # значит просрочено
            else:
                if not backGround.isValid(): # не просрочено, мы же ищем "которым осталось до просрочености"
                    currentDate = QDate.currentDate()
                    if valueType == 0: # дней
                        return currentDate.addDays(value) == endDate
                    elif valueType == 1: # месяцев
                        currentDays      = currentDate.daysInMonth()
                        endDays          = endDate.daysInMonth()
                        checkCurrentDate = QDate(currentDate.year(), currentDate.month(), currentDays)
                        checkEndDate     = QDate(endDate.year(), endDate.month(), endDays)
                        return checkCurrentDate.addMonths(value) == checkEndDate
                    elif valueType == 2: # лет
                        checkCurrentDate = QDate(currentDate.year(), 12, 31)
                        checkEndDate     = QDate(endDate.year(), 12, 31)
                        return checkCurrentDate.addYears(value) == checkEndDate
            return False

        recordList = QtGui.qApp.db.getRecordList('rbEquipment')
        if recordList:
            localMapBackGroundToId = {}
            for record in recordList:
                backGround, endDate = self.getBackGroundByMaintenancePeriod(record)
                localMapBackGroundToId[forceRef(record.value('id'))] = (backGround, endDate)
            return [id for id in localMapBackGroundToId.keys() if checkByValueAndValueType(localMapBackGroundToId[id],
                                                                                               value, valueType)]
        return []


    def getLastEquipmentMaintenanceDateFromModel(self, startupDate):
        date = startupDate
        for item in self.journalModel.items():
            modelDate = forceDate(item.value('date'))
            if modelDate > date:
                date = modelDate
        return date


    def getLastEquipmentMaintenanceDate(self, equipmentId, startupDate):
        db = QtGui.qApp.db
        tableJournal = db.table('EquipmentMaintenanceJournal')
        cond = [tableJournal['master_id'].eq(equipmentId)]
        record = db.getRecordEx(tableJournal, 'MAX('+tableJournal['date'].name()+') AS maxDate', cond)
        if record:
            date = forceDate(record.value('maxDate'))
            if date:
                return date
        return startupDate


    def maintenanceDateChanged(self, equipmentId):
        if bool(equipmentId):
            self.mapBackGroundToId[equipmentId] = (None, QDate())
            record = self._recordsCache.get(equipmentId)
            valid = self.isValidMaintenancePeriod(record)
            if not valid:
                self.mapBackGroundToId[equipmentId] = (QVariant(), QDate())
            else:
                startupDate = forceDate(record.value('startupDate'))
                date = self.getLastEquipmentMaintenanceDateFromModel(startupDate)
                backGround, endDate = self.makeBackGround(date, record)
                self.mapBackGroundToId[equipmentId] = (backGround, endDate)

            self.emitDataChanged()


    def getBackGround(self, id):
        return self.mapBackGroundToId.get(id, (None, QDate()))


    def getBackGroundByMaintenancePeriod(self, record):
        equipmentId = forceRef(record.value('id'))
        backGround, endDate = self.getBackGround(equipmentId)
        if not backGround:
            valid = self.isValidMaintenancePeriod(record)
            if not valid:
                return (QVariant(), endDate)
            startupDate = forceDate(record.value('startupDate'))
            date = self.getLastEquipmentMaintenanceDate(equipmentId, startupDate)
            backGround, endDate = self.makeBackGround(date, record)
            self.mapBackGroundToId[equipmentId] = (backGround, endDate)
        return backGround, endDate


    def makeBackGround(self, date, record):
        backGround = QVariant()
        maintenancePeriod = forceInt(record.value('maintenancePeriod'))
        maintenanceSingleInPeriod = forceInt(record.value('maintenanceSingleInPeriod'))
        currentDate = QDate.currentDate()
        if maintenancePeriod and date:
            endDate = date.addMonths(maintenancePeriod)
            if endDate < currentDate:
                backGround = QVariant(QtGui.QColor(125, 125, 125))
        elif maintenanceSingleInPeriod and date:
            checker = self.getCheckerMaintenanceSingleInPeriod(maintenanceSingleInPeriod)
            valid, endDate = checker(date, currentDate)
            if not valid:
                backGround = QVariant(QtGui.QColor(125, 125, 125))
        return backGround, endDate


    def isValidMaintenancePeriod(self, record):
        maintenancePeriod = forceInt(record.value('maintenancePeriod'))
        maintenanceSingleInPeriod = forceInt(record.value('maintenanceSingleInPeriod'))
        bothEmpty = not (bool(maintenancePeriod) or bool(maintenanceSingleInPeriod))
        bothFull  = bool(maintenancePeriod) and bool(maintenanceSingleInPeriod)
        valid =  not (bothEmpty or bothFull)
        return valid


    def getCheckerMaintenanceSingleInPeriod(self, value):
        def checkWeek(date, currentDate):
            iWeekDay = currentDate.dayOfWeek()
            mondey   = currentDate.addDays(Qt.Monday-iWeekDay)
            sunday   = currentDate.addDays(Qt.Sunday-iWeekDay)
            return (date >= mondey and date <= sunday), sunday

        def checkMonth(date, currentDate):
            monthDays = currentDate.daysInMonth()
            iDay      = currentDate.day()
            firstDay  = currentDate.addDays(1-iDay)
            lastDay   = currentDate.addDays(monthDays-iDay)
            return (date >= firstDay and date <= lastDay), lastDay

        def checkQuarter(date, currentDate): #WTF?
            iMonth     = currentDate.month()
            iQuarter   = ((iMonth-1)/3)+1
            iInQuarter = iMonth-((iQuarter-1)*3)
            firstMonth = currentDate.addMonths(1-iInQuarter)
            lastMonth  = currentDate.addMonths(3-iInQuarter)
            firstDate  = QDate(firstMonth.year(), firstMonth.month(), 1)
            lastDate   = QDate(lastMonth.year(), lastMonth.month(), lastMonth.daysInMonth())
            return (date >= firstDate and date <= lastDate), lastDate

        def checkHalfYear(date, currentDate):
            iMonth     = currentDate.month()
            iHalf      = ((iMonth-1)/6)+1
            iInHalf    = iMonth-((iHalf-1)*6)
            firstMonth = currentDate.addMonths(1-iInHalf)
            lastMonth  = currentDate.addMonths(6-iInHalf)
            firstDate  = QDate(firstMonth.year(), firstMonth.month(), 1)
            lastDate   = QDate(lastMonth.year(), lastMonth.month(), lastMonth.daysInMonth())
            return (date >= firstDate and date <= lastDate), lastDate

        def checkYear(date, currentDate):
            firstDate = QDate(currentDate.year(), 1, 1)
            lastDate  = QDate(currentDate.year(), 12, 31)
            return (date >= firstDate and date <= lastDate), lastDate

        def default(date, currentDate):
            return True, QDate()

        funcs = {1:checkWeek,
                 2:checkMonth,
                 3:checkQuarter,
                 4:checkHalfYear,
                 5:checkYear}

        return funcs.get(value, default)


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.BackgroundRole:
            column = index.column()
            row    = index.row()
            (col, values) = self.getRecordValues(column, row)
            backGround, endDate = self.getBackGroundByMaintenancePeriod(values[1])
            return backGround
        else:
            return CTableModel.data(self, index, role)
        return QVariant()

# #########################################################

class CMaintenanceJournalModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'EquipmentMaintenanceJournal', 'id', 'master_id', parent)
        self.addCol(CInDocTableCol(u'ФИО мастера', 'fullName', 30)).setSortable(True)
        self.addCol(CDateInDocTableCol(u'Дата ТО', 'date', 15, canBeEmpty=True)).setSortable(True)
        self.addCol(CDateInDocTableCol(u'Планируемая дата ТО', 'plannedDate', 15, canBeEmpty=True)).setSortable(True)
        self.addCol(CInDocTableCol(u'Примечание', 'note', 30)).setSortable(True)
        self.currentMasterId = None
        self.needSave = False
        self.isEditable = False


    def setEditable(self, val):
        self.isEditable = val


    def cellReadOnly(self, index):
        return not self.isEditable


    def setData(self, index, value, role=Qt.EditRole):
        result = CInDocTableModel.setData(self, index, value, role)
        if result:
            self.needSave = True
            if index.column() == 1 and bool(self.currentMasterId):
                self.emit(SIGNAL('maintenanceDateChanged(int)'), self.currentMasterId)
        return result


    def setNeedSave(self, val):
        self.needSave = val


    def loadItems(self, masterId):
        self.currentMasterId = masterId
        CInDocTableModel.loadItems(self, masterId)


    def saveItems(self, masterId):
        if self.needSave:
            CInDocTableModel.saveItems(self, masterId)
            self.needSave = False


class CEquipmentTestModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbEquipment_Test', 'id', 'equipment_id', parent)
        self.addCol(CRBInDocTableCol(u'Тест', u'test_id', 10, u'rbTest', showFields=2)).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Тип', 'type',    20,  [u'временно не используется', u'принимается и не передается', u'и принимается и передается'])).setSortable(True)
        self.addCol(CInDocTableCol(u'Код теста', 'hardwareTestCode', 15)).setSortable(True)
        self.addCol(CInDocTableCol(u'Наименование теста', 'hardwareTestName', 15)).setSortable(True)
        self.addCol(CInDocTableCol(u'Примечание',         'note', 20)).setSortable(True)
        self.addCol(CInDocTableCol(u'Тип результата',   'resultType', 20)).setSortable(True)
        self.addCol(CInDocTableCol(u'Код образца', 'hardwareSpecimenCode', 15)).setSortable(True)
        self.addCol(CInDocTableCol(u'Наименование образца', 'hardwareSpecimenName', 15)).setSortable(True)
        self.addCol(CRBInDocTableCol(u'Тип образца', u'specimenType_id', 15, 'rbSpecimenType', showFields=2)).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'Коэффициент', 'coefficient', 15))
        self.addCol(CBoolInDocTableCol(u'По умолчанию', 'isDefault', 15))


# #############################################################


class CSpecimenTypeChoice(CDialogBase, Ui_SpecimenTypeChoiceDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle(u'Тип образца')
        self.cmbSpecimenType.setTable('rbSpecimenType', addNone=True)


    def setSpecimenTypeId(self, specimenTypeId):
        self.cmbSpecimenType.setValue(specimenTypeId)


    def setSpecimenCode(self, specimenCode):
        self.edtSpecimenCode.setText(specimenCode)


    def setSpecimenName(self, specimenName):
        self.edtSpecimenName.setText(specimenName)


    def specimenTypeId(self):
        return self.cmbSpecimenType.value()


    def specimenCode(self):
        return unicode(self.edtSpecimenCode.text())


    def specimenName(self):
        return unicode(self.edtSpecimenName.text())


    def setValues(self, specimenTypeId, specimenCode, specimenName):
        self.setSpecimenTypeId(specimenTypeId)
        self.setSpecimenCode(specimenCode)
        self.setSpecimenName(specimenName)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    dialog = CSpecimenTypeChoice()
    dialog.exec_()
    app.exec_()
