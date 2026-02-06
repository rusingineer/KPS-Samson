# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, QObject, QVariant

from library.crbcombobox import CRBComboBox
from library.DialogBase import CConstructHelperMixin
from library.TableModel import CQueryModel, CTextCol, CBoolCol, CEnumCol
from library.Utils import forceRef, forceInt, forceBool, forceString, formatRecordsCount, exceptionToUnicode

from Exchange.PyServices import getPyServices, CDistantMonitoringService
from Orgs.Utils import getOrgStructureDescendants

from Ui_DistantMonitoringEquipmentPage import Ui_DistantMonitoringEquipmentPage


class CDistantMonitoringEquipmentPage(QtGui.QWidget, Ui_DistantMonitoringEquipmentPage, CConstructHelperMixin):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.addModels('EquipmentList', CEquipmentListModel(self))
        self.addObject('actRegisterEquipment', QtGui.QAction(u'Зарегистрировать прибор', self))
        self.addObject('actDeactivateEquipment', QtGui.QAction(u'Открепить прибор от МО', self))
        self.setupUi(self)
        self.tblEquipmentList.addPopupAction(self.actRegisterEquipment)
        self.tblEquipmentList.addPopupAction(self.actDeactivateEquipment)
        self.connect(self.tblEquipmentList, SIGNAL('popupMenuAboutToShow()'), self.popupMenuAboutToShow)
        self.setModels(self.tblEquipmentList, self.modelEquipmentList, self.selectionModelEquipmentList)
        self.filter = {}
        db = QtGui.qApp.db
        tableEquipmentClass = db.table('rbEquipmentClass')
        tableEquipmentType = db.table('rbEquipmentType')
        equipmentClassIds = db.getIdList(tableEquipmentClass, where=tableEquipmentClass['code'].inlist(['6', '12']))
        self.cmbEquipmentClass.setTable(tableEquipmentClass.name(), filter=tableEquipmentClass['id'].inlist(equipmentClassIds))
        self.cmbEquipmentClass.setShowFields(CRBComboBox.showCodeAndName)
        self.cmbEquipmentType.setTable(tableEquipmentType.name(), filter=tableEquipmentType['class_id'].inlist(equipmentClassIds))
        self.cmbEquipmentType.setShowFields(CRBComboBox.showCodeAndName)
        self.cmbEquipmentStatus.addItem(u'Не работает', 0)
        self.cmbEquipmentStatus.addItem(u'Работает', 1)
        self.cmbRegistrationStatus.addItem(u'Не зарегистрировано', 0)
        self.cmbRegistrationStatus.addItem(u'Зарегистрировано', 1)
        self.resetFilter()
        header = self.tblEquipmentList.horizontalHeader()
        if self.modelEquipmentList.orderColumn():
            header.setSortIndicatorShown(True)
            header.setSortIndicator(self.modelEquipmentList.orderColumn(), self.modelEquipmentList.sortIndicator())
        QObject.connect(header, SIGNAL('sectionClicked(int)'), self.setSort)
        self.pyServices = getPyServices(CDistantMonitoringService)
    
    @pyqtSignature('int')
    def setSort(self, colIndex):
        self.modelEquipmentList.toggleOrder(colIndex)
        self.updateEquipmentList()

    def updateEquipmentList(self):
        self.modelEquipmentList.update(self.filter)
        self.lblRecordCount.setText(formatRecordsCount(self.modelEquipmentList.rowCount()))

    def applyFilter(self):
        self.filter = {}
        if self.chkEquipmentClass.isChecked():
            self.filter['equipmentClassId'] = self.cmbEquipmentClass.getValue()
        if self.chkEquipmentType.isChecked():
            self.filter['equipmentTypeId'] = self.cmbEquipmentType.getValue()
        if self.chkEquipmentStatus.isChecked():
            self.filter['equipmentStatus'] = forceInt(self.cmbEquipmentStatus.itemData(self.cmbEquipmentStatus.currentIndex()))
        if self.chkRegistrationStatus.isChecked():
            self.filter['registrationStatus'] = forceInt(self.cmbRegistrationStatus.itemData(self.cmbRegistrationStatus.currentIndex()))
        self.updateEquipmentList()

    def resetFilter(self):
        self.chkEquipmentClass.setChecked(False)
        self.cmbEquipmentClass.setValue(None)
        self.chkEquipmentType.setChecked(False)
        self.cmbEquipmentType.setValue(None)
        self.chkEquipmentStatus.setChecked(False)
        self.cmbEquipmentStatus.setCurrentIndex(1)
        self.chkRegistrationStatus.setChecked(False)
        self.cmbRegistrationStatus.setCurrentIndex(1)
        self.applyFilter()

    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxFilter_clicked(self, button):
        buttonCode = self.buttonBoxFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.applyFilter()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetFilter()

    def popupMenuAboutToShow(self):
        record = self.modelEquipmentList.recordByIndex(self.tblEquipmentList.currentIndex())
        isRegistered = forceBool(record.value('isRegistered')) if record else None
        self.actRegisterEquipment.setEnabled(bool(self.pyServices and record and not isRegistered))
        self.actDeactivateEquipment.setEnabled(bool(self.pyServices and record and isRegistered))
    
    @pyqtSignature('')
    def on_actRegisterEquipment_triggered(self):
        record = self.modelEquipmentList.recordByIndex(self.tblEquipmentList.currentIndex())
        try:
            response = self.pyServices.createDevice(forceRef(record.value('id')))
            QtGui.QMessageBox.information(self, u'Сервис дистанционного наблюдения', u'Прибор успешно зарегистрирован', QtGui.QMessageBox.Ok)
            self.updateEquipmentList()
        except Exception as e:
            QtGui.QMessageBox.critical(self, u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)
    
    @pyqtSignature('')
    def on_actDeactivateEquipment_triggered(self):
        if QtGui.QMessageBox.question(self, u'Внимание!', u'Действительно открепить прибор от МО?', QtGui.QMessageBox.Yes | QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
            return
        record = self.modelEquipmentList.recordByIndex(self.tblEquipmentList.currentIndex())
        try:
            response = self.pyServices.deactivateDevice(forceRef(record.value('id')))
            QtGui.QMessageBox.information(self, u'Сервис дистанционного наблюдения', u'Прибор успешно откреплен', QtGui.QMessageBox.Ok)
            self.updateEquipmentList()
        except Exception as e:
            QtGui.QMessageBox.critical(self, u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)


class CEquipmentListModel(CQueryModel):
    def __init__(self, parent):
        CQueryModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Код', ['code'], 6))
        self.addColumn(CTextCol(u'Наименование', ['name'], 20))
        self.addColumn(CTextCol(u'Класс оборудования', ['equipmentClass_name'], 20))
        self.addColumn(CTextCol(u'Тип оборудования', ['equipmentType_name'], 10))
        self.addColumn(CTextCol(u'Серийный номер', ['serialNumber'], 20))
        self.addColumn(CEnumCol(u'Статус', ['status'], [u'Не работает', u'Работает'], 10))
        self.addColumn(CBoolCol(u'Регистрация на сервисе', ['isRegistered'], 10))
        self.setOrder('name')

    def update(self, filter):
        db = QtGui.qApp.db
        systemId = forceRef(db.translate('rbAccountingSystem', 'code', 'SYSDM', 'id'))
        if not systemId:
            raise Exception(u'Не найдена внешняя учетная система "SYSDM"')
        tableEquipment = db.table('rbEquipment')
        tableEquipmentClass = db.table('rbEquipmentClass')
        tableEquipmentType = db.table('rbEquipmentType')
        tableIdentification = db.table('rbEquipment_Identification')
        query = tableEquipment.leftJoin(tableEquipmentType, tableEquipmentType['id'].eq(tableEquipment['equipmentType_id']))
        query = query.leftJoin(tableEquipmentClass, tableEquipmentClass['id'].eq(tableEquipmentType['class_id']))
        identificationCond = [
            tableIdentification['master_id'].eq(tableEquipment['id']),
            tableIdentification['system_id'].eq(systemId), tableIdentification['deleted'].eq(0)
        ]
        cols = [
            tableEquipment['id'],
            tableEquipment['code'],
            tableEquipment['name'],
            tableEquipmentClass['name'].alias('equipmentClass_name'),
            tableEquipmentType['name'].alias('equipmentType_name'),
            tableEquipment['serialNumber'],
            tableEquipment['status'],
            db.existsStmt(tableIdentification, identificationCond) + ' AS isRegistered'
        ]
        cond = []
        if 'equipmentClassId' in filter:
            cond.append(tableEquipmentType['class_id'].eq(filter['equipmentClassId']))
        if 'equipmentTypeId' in filter:
            cond.append(tableEquipment['equipmentType_id'].eq(filter['equipmentTypeId']))
        if 'equipmentStatus' in filter:
            cond.append(tableEquipment['status'].eq(filter['equipmentStatus']))
        if 'registrationStatus' in filter:
            if filter['registrationStatus'] == 0:
                cond.append(db.notExistsStmt(tableIdentification, identificationCond))
            else:
                cond.append(db.existsStmt(tableIdentification, identificationCond))
        order = self.formatOrderBy({
            'code': tableEquipment['code'],
            'name': tableEquipment['name'],
            'equipmentClass_name': tableEquipmentClass['name'],
            'equipmentType_name': tableEquipmentType['name'],
            'serialNumber': tableEquipment['serialNumber'],
            'status': tableEquipment['status'],
            'isRegistered': db.existsStmt(tableIdentification, identificationCond)
        })
        records = db.getRecordList(query, cols=cols, where=cond, order=order)
        self.setRecords(records)
