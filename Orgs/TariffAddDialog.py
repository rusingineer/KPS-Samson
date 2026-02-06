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
from PyQt4.QtCore import QDate, Qt, pyqtSignature, QVariant
from PyQt4.QtGui import QFont
from PyQt4.QtSql import QSqlField
from library.InDocTable import CInDocTableModel, CInDocTableCol, CBoolInDocTableCol
from library.DialogBase import CDialogBase
from library.Utils import forceRef, forceString, forceDouble, toVariant, forceDate
from Accounting.Tariff import CTariff
from library.TableModel import CTableModel, CTextCol

from Ui_TariffAddDialog import Ui_TariffAddDialog


class FloatDelegate(QtGui.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QtGui.QLineEdit(parent)
        editor.setValidator(QtGui.QDoubleValidator(editor))
        return editor


class CTariffAddDialog(CDialogBase,  Ui_TariffAddDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, None)
        self.setupUi(self)
        self.setWindowTitle(u'Добавление тарифов для Краснодарского Края')
        self.model = CTariffModel('rbService', 'id', self)
        self.tblService.setModel(self.model)
        self.cmbAid.setTable('rbMedicalAidUnit', False)
        self.masterId = parent._id
        self.newRecords = []
        self.updatedRecords = {}
        
        self.edtDateChange.setDate(QDate.currentDate())
        
        self.tblTariff.verticalHeader().setDefaultSectionSize(3 * self.fontMetrics().height() / 2)
        self.tblTariff.verticalHeader().hide()
        self.tblTariff.setColumnCount(2)
        self.tblTariff.setHorizontalHeaderLabels([u"Тариф", u"Новый тариф"])
        self.tblTariff.setItemDelegateForColumn(1, FloatDelegate())
        self.tblTariff.selectionModel().currentRowChanged.connect(self.tariffSelectionChanged)
        self.chkOnlyUET.stateChanged.connect(self.updateTariffChangeList)
        self.edtDateChange.dateChanged.connect(self.updateTariffChangeList)
        self.updateTariffChangeList()
        
        self.tariffServicesModel = CTariffServicesModel(self)
        self.tblTariffServices.setModel(self.tariffServicesModel)

        self.parent = parent

        if self.parent.lastAddDialogDate:
            self.edtDate.setDate(self.parent.lastAddDialogDate)
        
    def serviceInfisById(self, serviceId):
        if serviceId.isNull():
            return ""
        else:
            serviceRecord = QtGui.qApp.db.getRecordEx(table = "rbService", cols = "infis", where = "id = %d" % serviceId.toInt()[0])
            return forceString(serviceRecord.value("infis"))
        
    def updateTariffChangeList(self):
        if self.masterId:
            date = self.edtDateChange.date()
            self.tblTariff.clearContents()
            sql = u"""select distinct price 
                from Contract_Tariff 
                where master_id = %(master_id)d 
                    and begDate <= '%(date)s' 
                    and (endDate is null or endDate >= '%(date)s') 
                    and price is not null %(onlyUET)s
                    and deleted = 0
                order by price"""
            if self.chkOnlyUET.isChecked():
                onlyUet = 'and uet > 0'
            else:
                onlyUet = ''
            sql = sql % {"date": date.toString('yyyy-MM-dd'), "master_id": self.masterId,  "onlyUET": onlyUet}
            query = QtGui.qApp.db.query(sql)
            rowCount = query.size()
            if rowCount == -1:
                self.tblTariff.setRowCount()
                return
            self.tblTariff.setRowCount(rowCount)
            row = 0
            while query.next():
                price = forceDouble(query.value(0))
                
                priceItem = QtGui.QTableWidgetItem("%.2f" % price)
                priceItem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.tblTariff.setItem(row, 0, priceItem)
                
                newPriceItem = QtGui.QTableWidgetItem("")
                self.tblTariff.setItem(row, 1, newPriceItem)
                row += 1
            
            
    def tariffSelectionChanged(self, current, previous):
        if current.isValid():
            price = self.tblTariff.item(current.row(), 0).text()
            price = forceDouble(price)
        else:
            price = None
        
        date = self.edtDateChange.date()
        if not date.isValid():
            self.tariffServicesModel.filter(price)
        else:
            self.tariffServicesModel.filter(price, date)
        
        
    def save(self):
        self.newRecords = []
        self.updatedRecords = {}
        self.parent.lastAddDialogDate = self.edtDate.date()
        for record in self.model._items:
            if(record.value("isActive").toBool()):
                service_id = record.value("id").toInt()[0]
                date = self.edtDate.date()
                price = self.edtTariff.text()
                price = price.replace(' ', '').replace(',', '.')
                unit_id = self.cmbAid.value()
                tariffType = self.cmbTariffType.currentIndex()
                
                table = QtGui.qApp.db.table('Contract_Tariff')
                serviceInfis = forceString(record.value("infis"))
                if serviceInfis[:1] == 'G' and len(serviceInfis) > 7:
                    tariffType = CTariff.ttKrasnodarA13
                    
                oldTariff = QtGui.qApp.db.getRecordEx(table, '*', [table['service_id'].eq(service_id), table['begDate'].eq(date), 
                    table['tariffType'].eq(tariffType),  table['master_id'].eq(self.masterId),  table['deleted'].eq(0)], 'id')
                # если есть тариф на услугу с той же датой, то обновляем его
                if oldTariff:
                    oldTariff.setValue('unit_id',  toVariant(unit_id))
                    oldTariff.setValue('price',  toVariant(price))
                    if tariffType == CTariff.ttKrasnodarA13:
                        oldTariff.setValue('frag1Sum',  toVariant(price))
                        oldTariff.setValue('frag2Sum',  toVariant(price))
                    QtGui.qApp.db.updateRecord(table, oldTariff)
                else: 
                    oldTariff = QtGui.qApp.db.getRecordEx(table, '*', [table['service_id'].eq(service_id), table['begDate'].lt(date), 
                    table['endDate'].isNull(), table['tariffType'].eq(tariffType),  table['master_id'].eq(self.masterId),  table['deleted'].eq(0)], 'id')
                    # если есть незакрытый тариф, проставляем endDate
                    if oldTariff:
                        oldTariff.setValue('endDate',  toVariant(date.addDays(-1)))
                        QtGui.qApp.db.updateRecord(table, oldTariff)
                        
                    # добавляем новый тариф
                    tariff = table.newRecord()
                    tariff.setValue('master_id',  toVariant(self.masterId))
                    tariff.setValue('tariffType',  toVariant(tariffType))
                    tariff.setValue('unit_id',  toVariant(unit_id))
                    tariff.setValue('service_id',  toVariant(service_id))
                    tariff.setValue('begDate',  toVariant(date))
                    tariff.setValue('price',  toVariant(price))
                    tariff.setValue('sex',  toVariant(0))
                    tariff.setValue('age',  toVariant(''))
                    tariff.setValue('amount',  toVariant(0))
                    tariff.setValue('MKB',  toVariant(''))
                    tariff.setValue('uet',  toVariant(record.value("adultUetDoctor")))
                    
                    # Заполняем поля второго и третьего тарифов, длительности для КСГ
                    if tariffType == CTariff.ttKrasnodarA13:
                        tariff.setValue('frag1Sum',  toVariant(price))
                        tariff.setValue('frag2Sum',  toVariant(price))
                        tableS71 = QtGui.qApp.db.table('soc_spr71')
                        tableS72 = QtGui.qApp.db.table('soc_spr72')
                        if QtGui.qApp.db.getRecordEx(tableS71, 'ksgkusl', tableS71['ksgkusl'].eq(serviceInfis), 'ksgkusl'):
                            tariff.setValue('frag1Start',  toVariant(1))
                        else:
                            tariff.setValue('frag1Start',  toVariant(3))
                        if QtGui.qApp.db.getRecordEx(tableS72, 'ksgkusl', tableS72['ksgkusl'].eq(serviceInfis), 'ksgkusl'):
                            tariff.setValue('frag2Start',  toVariant(46))
                        else:
                            tariff.setValue('frag2Start',  toVariant(31))
                        
                        # # Проставляем единицу учета
                        # rbMedicalAidUnit = QtGui.qApp.db.table('rbMedicalAidUnit')
                        # if serviceInfis[1] == '1':
                        #     regCode = '33'
                        # else:
                        #     regCode = '43'
                        # unitRecord = QtGui.qApp.db.getRecordEx(rbMedicalAidUnit, 'id', rbMedicalAidUnit['regionalCode'].eq(regCode), 'id')
                        # if unitRecord:
                        #     tariff.setValue('unit_id',  toVariant(unitRecord.value("id")))
                            
                    #QtGui.qApp.db.insertRecord(table, tariff)
                    if oldTariff:
                        self.updatedRecords[forceRef(oldTariff.value('id'))] = oldTariff
                    tariff.modified = True
                    self.newRecords.append(tariff)
        if not self.newRecords and not oldTariff:
            QtGui.QMessageBox.warning(self,
                                                u'Внимание!',
                                                u'Не выбрана ни одна услуга',
                                                QtGui.QMessageBox.Ok, 
                                                QtGui.QMessageBox.Ok)
            return False
        else:
            return True
        
    def applyFiler(self):
        self.edtFilter.setReadOnly(True)
        tariffAid = self.cmbAid.value()
        tariffType = self.cmbTariffType.currentIndex()
        if self.chkContract.isChecked():
            if tariffType==5 and tariffAid in (3, 53):
                self.model.loadItems(u"`infis` like \"%s\" and adultUetDoctor > 0 and id IN (SELECT ct.service_id FROM Contract_Tariff ct WHERE ct.master_id=\"%s\" AND ct.deleted=0)" % ((self.edtFilter.text() + "%" ), self.masterId))
            else:
                self.model.loadItems(u"`infis` like \"%s\" and id IN (SELECT ct.service_id FROM Contract_Tariff ct WHERE ct.master_id=\"%s\" AND ct.deleted=0)" % ((self.edtFilter.text() + "%" ), self.masterId))   
        else:
            if tariffType==5 and tariffAid in (3, 53):
                self.model.loadItems(u"`infis` like \"%s\" and adultUetDoctor > 0" % (self.edtFilter.text() + "%" ))
            else:
                self.model.loadItems(u"`infis` like \"%s\" " % (self.edtFilter.text() + "%" ))      
        self.edtFilter.setReadOnly(False)
        self.edtFilter.setFocus()
        
    def saveChange(self):
        db = QtGui.qApp.db
        insertCount = 0
        date = self.edtDateChange.date()
        tableContractTariff = db.table("Contract_Tariff")
        for row in xrange(0, self.tblTariff.rowCount()):
            newPrice = self.tblTariff.item(row, 1).text().replace(',', '.')
            if newPrice == '':
                continue
            try:
                newPrice = forceDouble(newPrice)
            except ValueError:
                continue
            insertCount += 1
            oldPrice = self.tblTariff.item(row, 0).text()
            oldPrice = forceDouble(oldPrice)
            
            cond = "master_id = %(master_id)d and round(price, 2) = %(price).2f and begDate <= '%(date)s' and (endDate is null or endDate >= '%(date)s')"
            cond = cond % {"master_id": self.masterId, "price": oldPrice, "date": date.toString('yyyy-MM-dd')}
            recordList = db.getRecordList(table = tableContractTariff, where = cond)
            for oldTariff in recordList:
                if oldTariff.value("begDate") == date:
                    oldTariff.setValue("price", toVariant(newPrice))
                    serviceInfis = self.serviceInfisById(oldTariff.value("service_id"))
                    if serviceInfis[:1] == 'G' and len(serviceInfis) > 7:
                        oldTariff.setValue('frag1Sum', toVariant(newPrice))
                        oldTariff.setValue('frag2Sum', toVariant(newPrice))
                    db.updateRecord(tableContractTariff, oldTariff)
                else:
                    oldTariff.setValue('endDate', toVariant(date.addDays(-1)))
                    db.updateRecord(tableContractTariff, oldTariff)
                    
                    newTariff = tableContractTariff.newRecord()
                    for field in tableContractTariff.fields:
                        fieldName = field.field.name()
                        if str(fieldName) not in ('id',  'endDate'):
                            newTariff.setValue(fieldName, oldTariff.value(fieldName))
                            
                    newTariff.setValue('master_id',  toVariant(self.masterId))
                    newTariff.setValue('begDate',    toVariant(date))
                    newTariff.setValue('price',      toVariant(newPrice))

                    serviceInfis = self.serviceInfisById(newTariff.value("service_id"))
                    if serviceInfis[:1] == 'G' and len(serviceInfis) > 7:
                        newTariff.setValue('frag1Sum', toVariant(newPrice))
                        newTariff.setValue('frag2Sum', toVariant(newPrice))

                    #db.insertRecord(tableContractTariff, newTariff)
                    if oldTariff:
                        self.updatedRecords[forceRef(oldTariff.value('id'))] = oldTariff
                    self.newRecords.append(newTariff)
        if insertCount == 0:
            QtGui.QMessageBox.warning(self,
                                                u'Внимание!',
                                                u'Не выбраны тарифы для изменения',
                                                QtGui.QMessageBox.Ok, 
                                                QtGui.QMessageBox.Ok)
            return False
        else:
            return True
        
    @pyqtSignature('')
    def on_edtFilter_returnPressed(self):
        self.applyFiler()
        return False
        
    @pyqtSignature('')
    def on_btnApplyfilter_clicked(self):
        self.applyFiler()
        
    @pyqtSignature('')
    def on_btnClear_clicked(self):
       for row,  record in enumerate(self.model._items):
           if(record.value("isActive").toBool()):
            record.setValue("isActive",  QVariant(Qt.Unchecked))
            self.model.emitCellChanged(row, record.indexOf("isActive"))

    @pyqtSignature('')
    def on_btnAll_clicked(self):
       for row,  record in enumerate(self.model._items):
           if not(record.value("isActive").toBool()):
            record.setValue("isActive",  QVariant(Qt.Checked))
            self.model.emitCellChanged(row, record.indexOf("isActive"))

            
    @pyqtSignature('')
    def on_btnAdd_clicked(self):
        if (self.save()):
            self.accept()
                
    @pyqtSignature('')
    def on_btnCancel_clicked(self):
        self.reject()
            
    @pyqtSignature('')
    def on_btnSaveChange_clicked(self):
        if (self.saveChange()):
            self.accept()
            
    @pyqtSignature('')
    def on_btnCancelChange_clicked(self):
        self.reject()
        
    @pyqtSignature('QDate')
    def on_edtDateChange_dateChanged(self, date):
        self.updateTariffChangeList()
            
    
class CTariffModel(CInDocTableModel):
    def __init__(self, tableName, idFieldName,parent):
        CInDocTableModel.__init__(self, tableName, idFieldName, None,  parent)
        self.addCol(CBoolInDocTableCol(u'Отметить', 'isActive', 15))
        colName = CInDocTableCol(u'Код', 'infis', 15)
        colName.setReadOnly()
        self.addCol(colName)
        colName = CInDocTableCol(u'Наименование', 'name', 25)
        colName.setReadOnly()
        self.addCol(colName)
        colName = CInDocTableCol(u'УЕТ', 'adultUetDoctor', 5)
        colName.setReadOnly()
        self.addCol(colName)
        self.loadItems()
        
    def loadItems(self,  filter = None):
        if filter!=None:
            filter+=' and '
        else:
            filter = ''
        filter+= "substr(`infis`, 1, 1) in ('A', 'B', 'G', 'K', 'S', 'V') "
        
        db = QtGui.qApp.db
        self.reset()    
        self._items = db.getRecordList(self._table, ['id', 'infis', 'name', 'adultUetDoctor', 'endDate'], filter, ['id'])
        for record in self._items:
            record.insert(0, QSqlField('isActive'))

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.FontRole:
            row = index.row()
            if 0 <= row < len(self._items):
                if forceDate(self.items()[row].value('endDate')) <= QDate.currentDate():
                    font = QFont()
                    font.setItalic(True)
                    font.setBold(True)
                    return font
                else:
                    return QVariant()

        if index.isValid() and role == Qt.ToolTipRole:
            row = index.row()
            if 0 <= row < len(self._items):
                if forceDate(self.items()[row].value('endDate')) <= QDate.currentDate():
                    return u"Данная услуга не является актуальной"
                else:
                    return u""

        return CInDocTableModel.data(self, index, role)
        
    
class CTariffServicesModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CTextCol(u'Код услуги',   ['infis'], 15),
            CTextCol(u'Наименование', ['name'], 20), 
            CTextCol(u'УЕТ', ['adultUetDoctor'], 5)
            ], 'rbService')
        self.filter()
        self.masterId = parent.masterId
        
    def filter(self, price=None, date=QDate.currentDate()):
        if price == None:
            self.setIdList([])
        else:
            db = QtGui.qApp.db
            idList = db.getDistinctIdList(table = "Contract_Tariff", idCol = "service_id", where = "master_id = %d and deleted = 0 and round(price, 2) = %.2f and (endDate >= %s or endDate is null)" % (self.masterId, price, db.formatDate(date)))
            self.setIdList(idList)
