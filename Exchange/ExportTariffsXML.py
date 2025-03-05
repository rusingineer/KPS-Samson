#!/usr/bin/env python
# -*- coding: utf-8 -*-

#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2015 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

u"""
Экспорт тарифа в XML
"""
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QFile, QString, QVariant, QXmlStreamWriter, pyqtSignature, SIGNAL, QDate

from library.crbcombobox import CRBModelDataCache, CRBComboBox
from library.DialogBase import CConstructHelperMixin
from library.Utils import anyToUnicode, exceptionToUnicode, forceBool, forceDate, forceDouble, forceRef, forceString, toVariant

from Exchange.Utils import compressFileInRar

from Exchange.Ui_ExportTariff_Wizard_1 import Ui_ExportTariff_Wizard_1
from Exchange.Ui_ExportTariff_Wizard_2 import Ui_ExportTariff_Wizard_2


tariffSimpleFields = ('tariffType', 'batch', 'begDate', 'endDate', 'sex', 'age', 'MKB',
                      'amount', 'uet', 'price',
                      'frag1Start', 'frag1Sum', 'frag1Price',
                      'frag2Start', 'frag2Sum', 'frag2Price',
                      'limitationExceedMode',  'limitation',
                      'priceEx',
                      'federalLimitation', 'federalPrice',
                      'regionalLimitation', 'regionalPrice',
                     )

tariffRefFields    =  ('eventType_id', 'service_id', 'unit_id', 'tariffCategory_id',  'result_id')
tariffRefTableNames=  ('EventType',    'rbService',  'rbMedicalAidUnit', 'rbTariffCategory',  'rbResult')

tariffKeyFields    = ('eventType_id', 'tariffType', 'service_id', 'tariffCategory_id', 'MKB', 'sex', 'age', 'begDate')


exportVersion = '1.08'

def ExportTariffsXML(widget, tariffRecordList, expensesDict):
    appPrefs = QtGui.qApp.preferences.appPrefs
    fileName = forceString(appPrefs.get('ExportTariffsXMLFileName', ''))
    exportAll = forceBool(appPrefs.get('ExportTariffsXMLExportAll', True))
    compressRAR = forceBool(appPrefs.get('ExportTariffsXMLCompressRAR', False))
    dlg = CExportTariffXML(fileName, exportAll, compressRAR, tariffRecordList, expensesDict, widget)
    dlg.exec_()
    appPrefs['ExportTariffsXMLFileName'] = toVariant(dlg.fileName)
    appPrefs['ExportTariffsXMLExportAll'] = toVariant(dlg.exportAll)
    appPrefs['ExportTariffsXMLCompressRAR'] = toVariant(dlg.compressRAR)


class CMyXmlStreamWriter(QXmlStreamWriter):
    def __init__(self, parent, tariffRecordList, selectedItems, expensesDict):
        QXmlStreamWriter.__init__(self)
        self.parent = parent
        self.setAutoFormatting(True)
        self.tariffRecordList = tariffRecordList
        self.selectedItems = selectedItems
        self.expensesDict = expensesDict
        self.refValueCache = {}
        for field, tableName in zip(tariffRefFields, tariffRefTableNames):
            self.refValueCache[field] = CRBModelDataCache.getData(tableName, True)

        self.expenseCodeCache = {}


    def writeRecord(self, record, expenses):
        self.writeStartElement('TariffElement')
        # все нессылочные свойства действия экспортируем как атрибуты
        for fieldName in tariffSimpleFields:
            value = record.value(fieldName)
            fieldType = record.field(fieldName).type()
            if fieldType == QVariant.Date:
                strValue = forceDate(value).toString(Qt.ISODate)
            elif fieldType == QVariant.Double:
                strValue = unicode(forceDouble(value))
            else:
                strValue = forceString(value)
            self.writeAttribute(fieldName, strValue)
        # ссылочные свойства экспортируем как элементы с атрибутами code и name
        for fieldName in tariffRefFields:
            elementName = fieldName[:-3]
            self.writeStartElement(elementName)
            value = forceRef(record.value(fieldName))
            if value:
                cache = self.refValueCache[fieldName]
                self.writeAttribute('code', cache.getStringById(value, CRBComboBox.showCode))
                self.writeAttribute('name', cache.getStringById(value, CRBComboBox.showName))
            self.writeEndElement()
        #затраты
        for ex in expenses:
            self.writeStartElement('expense')
            self.writeAttribute('code', self.getExpenseCode(forceRef(ex.value('rbTable_id'))))
            self.writeAttribute('percent', forceString(ex.value('percent')))
            self.writeAttribute('sum',  forceString(ex.value('sum')))
            self.writeEndElement()

        self.writeEndElement() # TariffElement


    def getExpenseCode(self, id):
        result = self.expenseCodeCache.get(id,  -1)

        if result == -1:
            result = forceString(QtGui.qApp.db.translate('rbExpenseServiceItem', 'id',  id,  'code'))
            self.expenseCodeCache[id] = result

        return result

    def writeFile(self, device, progressBar):
        global lastChangedRev
        global lastChangedDate
        try:
            from buildInfo import lastChangedRev, lastChangedDate
        except:
            lastChangedRev  = 'unknown'
            lastChangedDate = 'unknown'

        try:
            progressBar.setMaximum(max(len(self.selectedItems), 1))
            progressBar.reset()
            progressBar.setValue(0)

            self.setDevice(device)
            self.writeStartDocument()
            self.writeDTD('<!DOCTYPE xTariff>')
            self.writeStartElement('TariffExport')
            self.writeAttribute('SAMSON',
                                '2.0 revision(%s, %s)' %(lastChangedRev, lastChangedDate))
            self.writeAttribute('version', exportVersion)

            for i in self.selectedItems:
                self.writeRecord(self.tariffRecordList[i], self.expensesDict[i])
                QtGui.qApp.processEvents()
                progressBar.step()

            self.writeEndDocument()

        except IOError, e:
            QtGui.qApp.logCurrentException()
            msg=''
            if hasattr(e, 'filename'):
                msg = u'%s:\n[Errno %s] %s' % (e.filename, e.errno, anyToUnicode(e.strerror))
            else:
                msg = u'[Errno %s] %s' % (e.errno, anyToUnicode(e.strerror))
            QtGui.QMessageBox.critical (self.parent,
                u'Произошла ошибка ввода-вывода', msg, QtGui.QMessageBox.Close)
            return False
        except Exception, e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical (self.parent,
                u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)
            return False

        return True

class CExportTariffWizardPage1(QtGui.QWizardPage, Ui_ExportTariff_Wizard_1, CConstructHelperMixin):
    def __init__(self, parent):
        QtGui.QWizardPage.__init__(self, parent)
        self.parent = parent
        self.preSetupUi()
        self.setupUi(self)
        self.postSetupUi()
        self.setTitle(u'Параметры экспорта')
        self.setSubTitle(u'Выбор записей для экспорта')
        self.edtFilterBegDateFrom.setDate(QDate(QDate.currentDate().year(),1,1))
        self.edtFilterBegDateTil.setDate(QDate(QDate.currentDate().year(),12,31))


    def preSetupUi(self):
        from Orgs.Contracts import CTariffModel
        self.addModels('Table', CTariffModel(self))
        self.modelTable.cellReadOnly = lambda index: True
        self.modelTable.setEnableAppendLine(False)


    def postSetupUi(self):
        self.setModels(self.tblItems, self.modelTable, self.selectionModelTable)
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.modelTable.setItems(self.parent.tariffRecordList)
        self.selectionModelTable.clearSelection()
        self.tblItems.setFocus(Qt.OtherFocusReason)
        self.tblItems.setEnabled(not self.parent.exportAll)
        self.btnSelectAll.setEnabled(not self.parent.exportAll)
        self.btnClearSelection.setEnabled(not self.parent.exportAll)
        self.chkExportAll.setChecked(self.parent.exportAll)
        if self.parent.exportAll:
            self.parent.selectedItems = range(self.modelTable.rowCount())
            self.chkActive.setEnabled(False)
            self.edtFilterBegDateFrom.setEnabled(False)
            self.edtFilterBegDateTil.setEnabled(False)
        else:
            self.tblItems.clearSelection()
            self.parent.selectedItems = []


    def selectedItemList(self):
        if self.parent.exportAll:
            rows = self.parent.selectedItems
        else:
            rows = [index.row() for index in self.selectionModelTable.selectedRows() if not self.tblItems.isRowHidden(index.row())]
        rows.sort()
        return rows


    @pyqtSignature('')
    def on_btnSelectAll_clicked(self):
        self.tblItems.clearSelection()
        self.parent.selectedItems = []
        self.tblItems.selectAll()
        self.parent.selectedItems = self.selectedItemList()
        self.emit(SIGNAL('completeChanged()'))


    @pyqtSignature('')
    def on_btnClearSelection_clicked(self):
        self.selectionModelTable.clearSelection()
        self.parent.selectedItems = []
        self.emit(SIGNAL('completeChanged()'))

    
    @pyqtSignature('QDate')
    def on_edtFilterBegDateFrom_dateChanged(self, date):
        if date.isValid() and not self.chkExportAll.isChecked():
            self.applyFilter()
        self.emit(SIGNAL('completeChanged()'))
    
    
    @pyqtSignature('QDate')
    def on_edtFilterBegDateTil_dateChanged(self, date):
        if date.isValid() and not self.chkExportAll.isChecked():
            self.applyFilter()
        self.emit(SIGNAL('completeChanged()'))
    

    @pyqtSignature('')
    def on_chkExportAll_clicked(self):
        self.parent.exportAll = self.chkExportAll.isChecked()
        self.tblItems.setEnabled(not self.parent.exportAll)
        self.btnSelectAll.setEnabled(not self.parent.exportAll)
        self.btnClearSelection.setEnabled(not self.parent.exportAll)
        if self.chkExportAll.isChecked():
            self.parent.selectedItems = range(self.modelTable.rowCount())
            self.chkActive.setEnabled(False)
            self.edtFilterBegDateFrom.setEnabled(False)
            self.edtFilterBegDateTil.setEnabled(False)
        else:
            self.applyFilter()
            self.parent.selectedItems = self.selectedItemList()
            self.chkActive.setEnabled(True)
            self.edtFilterBegDateFrom.setEnabled(True)
            self.edtFilterBegDateTil.setEnabled(True)
        self.emit(SIGNAL('completeChanged()'))
    
    
    @pyqtSignature('')
    def on_chkActive_clicked(self):
        self.tblItems.clearSelection()
        self.parent.selectedItems = []
        self.emit(SIGNAL('completeChanged()'))
        self.applyFilter()    
    
    
    def applyFilter(self):
        self.selectionModelTable.clearSelection()
        self.parent.selectedItems = []
        filteredList = self.parent.tariffRecordList
        filter_begDateFrom = self.edtFilterBegDateFrom.date()
        filter_begDateTil = self.edtFilterBegDateTil.date()
        filter_begDate_valid = filter_begDateFrom.isValid() and filter_begDateTil.isValid() and not self.chkExportAll.isChecked()
        first_matched_row = -1
        for row in xrange(len(filteredList)):
            match = True
            if filter_begDate_valid:
                if self.chkActive.isChecked():
                    dataStart = QDate.fromString(self.modelTable.index(row, 8).data().toString(), "dd.MM.yyyy")
                    dataEnd = QDate.fromString(self.modelTable.index(row, 9).data().toString(), "dd.MM.yyyy")
                    match = match and ((dataEnd >= filter_begDateFrom and dataEnd <= filter_begDateTil) or not dataEnd) and dataStart <= filter_begDateTil
                else:
                    dataStart = QDate.fromString(self.modelTable.index(row, 8).data().toString(), "dd.MM.yyyy")
                    match = match and dataStart >= filter_begDateFrom and dataStart <= filter_begDateTil
            self.tblItems.setRowHidden(row, not match)
            if first_matched_row == -1 and match:
                first_matched_row = row
        self.tblItems.setCurrentRow(first_matched_row)
        self.emit(SIGNAL('completeChanged()'))


class CExportTariffWizardPage2(QtGui.QWizardPage, Ui_ExportTariff_Wizard_2):
    def __init__(self, parent):
        self.done = False
        QtGui.QWizardPage.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent
        self.setTitle(u'Параметры сохранения')
        self.setSubTitle(u'Выбор места для сохранения')
        self.progressBar.setFormat('%p%')
        self.progressBar.setValue(0)
        self.edtFileName.setText(self.parent.fileName)
        self.btnExport.setEnabled(self.parent.fileName != '')
        self.checkRAR.setChecked(self.parent.compressRAR)


    def initializePage(self):
        self.btnExport.setEnabled(self.parent.fileName != '')
        self.done = False


    def isComplete(self):
        return self.done


    @pyqtSignature('')
    def on_btnSelectFile_clicked(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, u'Укажите файл с данными', self.edtFileName.text(), u'Файлы XML (*.xml)')
        if fileName:
            self.edtFileName.setText(fileName)
            self.parent.fileName = fileName
            self.btnExport.setEnabled(True)


    @pyqtSignature('')
    def on_btnExport_clicked(self):
        fileName = self.edtFileName.text()
        if fileName.isEmpty():
            return

        if not self.parent.selectedItems:
            QtGui.QMessageBox.warning(self,
                                      u'Экспорт тарифов договора',
                                      u'Не выбрано ни одного элемента для выгрузки')
            self.parent.back() # вернемся на пред. страницу. пусть выбирают
            return

        outFile = QFile(fileName)
        if not outFile.open(QFile.WriteOnly | QFile.Text):
            QtGui.QMessageBox.warning(self,
                                      u'Экспорт тарифов договора',
                                      QString(u'Не могу открыть файл для записи %1:\n%2.').arg(fileName).arg(outFile.errorString()))
            return

        myXmlStreamWriter = CMyXmlStreamWriter(self, self.parent.tariffRecordList, self.parent.selectedItems, self.parent.expensesDict)
        if (myXmlStreamWriter.writeFile(outFile, self.progressBar)):
            self.progressBar.setText(u'Готово')
        else:
            self.progressBar.setText(u'Прервано')
        outFile.close()

        if self.checkRAR.isChecked():
            self.progressBar.setText(u'Сжатие')
            compressFileInRar(fileName, fileName+'.rar')
            self.progressBar.setText(u'Сжато в "%s"' % (fileName+'.rar'))

        self.done = True
        self.btnExport.setEnabled(False)
        self.emit(SIGNAL('completeChanged()'))


    @pyqtSignature('')
    def on_checkRAR_clicked(self):
        self.parent.compressRAR = self.checkRAR.isChecked()


    @pyqtSignature('QString')
    def on_edtFileName_textChanged(self):
        self.parent.fileName = self.edtFileName.text()
        self.btnExport.setEnabled(self.parent.fileName != '')
        self.emit(SIGNAL('completeChanged()'))


class CExportTariffXML(QtGui.QWizard):
    def __init__(self, fileName, exportAll, compressRAR, tariffRecordList, expensesDict, parent=None):
        QtGui.QWizard.__init__(self, parent, Qt.Dialog)
        self.setWizardStyle(QtGui.QWizard.ModernStyle)
        self.setWindowTitle(u'Экспорт тарифов договора')
        self.selectedItems = []
        self.fileName= fileName
        self.exportAll = exportAll
        self.compressRAR = compressRAR
        self.tariffRecordList = tariffRecordList
        self.expensesDict =  expensesDict
        self.addPage(CExportTariffWizardPage1(self))
        self.addPage(CExportTariffWizardPage2(self))
        self.currentIdChanged.connect(self.saveSelected)
    
    
    def saveSelected(self):
        self.selectedItems = self.page(0).selectedItemList()
    
    
    def exec_(self):
        QtGui.QWizard.exec_(self)
