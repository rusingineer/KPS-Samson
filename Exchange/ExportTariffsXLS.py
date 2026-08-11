#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from library.DialogBase import CConstructHelperMixin
from library.database import CTableRecordCache
from library.Utils import *

from Utils import *

from Ui_ExportTariff_Wizard_1 import Ui_ExportTariff_Wizard_1
from Ui_ExportTariff_Wizard_2 import Ui_ExportTariff_Wizard_2

from library import xlwt

class TariffField:
    def __init__(self, fieldName, caption, refTable = None, refTableField = None):
        self.fieldName = fieldName
        self.caption = caption
        self.refTable = refTable
        self.refTableField = refTableField

tariffFields = [
    TariffField(fieldName = 'service_id', caption = u"Код услуги", refTable = 'rbService', refTableField = 'infis'), 
    TariffField(fieldName = 'service_id', caption = u"Наименование услуги", refTable = 'rbService', refTableField = 'name'), 
    TariffField(fieldName = 'amount', caption = u"Кол-во"), 
    TariffField(fieldName = 'uet', caption = u"УЕТ"), 
    TariffField(fieldName = 'price', caption = u"Стоимость"),
    TariffField(fieldName = 'begDate', caption = u"Дата начала"),
    TariffField(fieldName = 'endDate', caption = u"Дата окончания")
]


def ExportTariffsXLS(widget, tariffRecordList):
    appPrefs = QtGui.qApp.preferences.appPrefs
    fileName = forceString(appPrefs.get('ExportTariffsXLSFileName', ''))
    exportAll = forceBool(appPrefs.get('ExportTariffsXLSExportAll', True))
    compressRAR = forceBool(appPrefs.get('ExportTariffsXLSCompressRAR', False))
    dlg = CExportTariffXLS(fileName, exportAll, compressRAR, tariffRecordList, widget)
    dlg.exec_()
    appPrefs['ExportTariffsXLSFileName'] = toVariant(dlg.fileName)
    appPrefs['ExportTariffsXLSExportAll'] = toVariant(dlg.exportAll)
    appPrefs['ExportTariffsXLSCompressRAR'] = toVariant(dlg.compressRAR)


class CXLSWriter:
    def __init__(self, parent, tariffRecordList, selectedItems):
        self.parent = parent
        self.tariffRecordList = tariffRecordList
        self.selectedItems = selectedItems
        self.workbook = xlwt.Workbook()
        self.sheet = self.workbook.add_sheet(u'Тарифы')
        self.refCaches = {}
        boldStyle = xlwt.easyxf('font: bold on')
        for column, field in enumerate(tariffFields):
            self.sheet.write(0, column, field.caption, boldStyle)
            if field.refTable and not field.refTable in self.refCaches:
                self.refCaches[field.refTable] = CTableRecordCache(QtGui.qApp.db, field.refTable)
        self.sheet.set_horz_split_pos(1)
        self.sheet.set_panes_frozen(True)
        self.currentRow = 1
        

    def writeRecord(self, record):
        for column, field in enumerate(tariffFields):
            value = record.value(field.fieldName)
            if field.refTable:
                cache = self.refCaches[field.refTable]
                refRecord = cache.get(value)
                value = refRecord.value(field.refTableField)

            fieldType = record.field(field.fieldName).type()
            if fieldType == QVariant.Double:
                strValue = unicode(forceDouble(value))
            else:
                strValue = forceString(value)
            self.sheet.write(self.currentRow, column, strValue)
        self.currentRow += 1


    def writeFile(self, fileName, progressBar):
        try:
            progressBar.setMaximum(max(len(self.selectedItems), 1))
            progressBar.reset()
            progressBar.setValue(0)

            for i in self.selectedItems:
                self.writeRecord(self.tariffRecordList[i])
                QtGui.qApp.processEvents()
                progressBar.step()
            self.workbook.save(fileName)
            

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
                u'Произошла ошибка', unicode(e), QtGui.QMessageBox.Close)
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


    @QtCore.pyqtSignature('')
    def on_btnSelectAll_clicked(self):
        self.tblItems.clearSelection()
        self.parent.selectedItems = []
        self.tblItems.selectAll()
        self.parent.selectedItems = self.selectedItemList()
        self.emit(QtCore.SIGNAL('completeChanged()'))
    

    @QtCore.pyqtSignature('')
    def on_btnClearSelection_clicked(self):
        self.selectionModelTable.clearSelection()
        self.parent.selectedItems = []
        self.emit(QtCore.SIGNAL('completeChanged()'))
    
    
    @QtCore.pyqtSignature('QDate')
    def on_edtFilterBegDateFrom_dateChanged(self, date):
        if date.isValid() and not self.chkExportAll.isChecked():
            self.applyFilter()
        self.emit(QtCore.SIGNAL('completeChanged()'))
    
    
    @QtCore.pyqtSignature('QDate')
    def on_edtFilterBegDateTil_dateChanged(self, date):
        if date.isValid() and not self.chkExportAll.isChecked():
            self.applyFilter()
        self.emit(QtCore.SIGNAL('completeChanged()'))


    @QtCore.pyqtSignature('')
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
        self.emit(QtCore.SIGNAL('completeChanged()'))
    
    
    @QtCore.pyqtSignature('')
    def on_chkActive_clicked(self):
        self.tblItems.clearSelection()
        self.parent.selectedItems = []
        self.emit(QtCore.SIGNAL('completeChanged()'))
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
                    dataStart = QDate.fromString(self.modelTable.index(row, self.modelTable.getColIndex('begDate')).data().toString(), "dd.MM.yyyy")
                    dataEnd = QDate.fromString(self.modelTable.index(row, self.modelTable.getColIndex('endDate')).data().toString(), "dd.MM.yyyy")
                    match = match and ((dataEnd >= filter_begDateFrom and dataEnd <= filter_begDateTil) or not dataEnd) and dataStart <= filter_begDateTil
                else:
                    dataStart = QDate.fromString(self.modelTable.index(row, self.modelTable.getColIndex('begDate')).data().toString(), "dd.MM.yyyy")
                    match = match and dataStart >= filter_begDateFrom and dataStart <= filter_begDateTil
            self.tblItems.setRowHidden(row, not match)
            if first_matched_row == -1 and match:
                first_matched_row = row
        self.tblItems.setCurrentRow(first_matched_row)
        self.emit(QtCore.SIGNAL('completeChanged()'))


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


    @QtCore.pyqtSignature('')
    def on_btnSelectFile_clicked(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, u'Укажите файл с данными', self.edtFileName.text(), u'Файлы XLS (*.xls)')
        if fileName:
            self.edtFileName.setText(fileName)
            self.parent.fileName = fileName
            self.btnExport.setEnabled(True)


    @QtCore.pyqtSignature('')
    def on_btnExport_clicked(self):
        fileName = unicode(self.edtFileName.text())
        if fileName == '':
            return

        if not self.parent.selectedItems:
            QtGui.QMessageBox.warning(self,
                                      u'Экспорт тарифов договора',
                                      u'Не выбрано ни одного элемента для выгрузки')
            self.parent.back() # вернемся на пред. страницу. пусть выбирают
            return

        xlsWriter = CXLSWriter(self, self.parent.tariffRecordList, self.parent.selectedItems)
        if (xlsWriter.writeFile(fileName, self.progressBar)):
            self.progressBar.setText(u'Готово')
        else:
            self.progressBar.setText(u'Прервано')

        if self.checkRAR.isChecked():
            self.progressBar.setText(u'Сжатие')
            compressFileInRar(fileName, fileName+'.rar')
            self.progressBar.setText(u'Сжато в "%s"' % (fileName+'.rar'))

        self.done = True
        self.btnExport.setEnabled(False)
        self.emit(QtCore.SIGNAL('completeChanged()'))


    @QtCore.pyqtSignature('')
    def on_checkRAR_clicked(self):
        self.parent.compressRAR = self.checkRAR.isChecked()


    @QtCore.pyqtSignature('QString')
    def on_edtFileName_textChanged(self):
        self.parent.fileName = self.edtFileName.text()
        self.btnExport.setEnabled(self.parent.fileName != '')
        self.emit(QtCore.SIGNAL('completeChanged()'))


class CExportTariffXLS(QtGui.QWizard):
    def __init__(self, fileName, exportAll, compressRAR, tariffRecordList, parent=None):
        QtGui.QWizard.__init__(self, parent, Qt.Dialog)
        self.setWizardStyle(QtGui.QWizard.ModernStyle)
        self.setWindowTitle(u'Экспорт тарифов договора')
        self.selectedItems = []
        self.fileName= fileName
        self.exportAll = exportAll
        self.compressRAR = compressRAR
        self.tariffRecordList = tariffRecordList
        self.addPage(CExportTariffWizardPage1(self))
        self.addPage(CExportTariffWizardPage2(self))
        self.currentIdChanged.connect(self.saveSelected)
    
    
    def saveSelected(self):
        self.selectedItems = self.page(0).selectedItemList()
    
    
    def exec_(self):
        QtGui.QWizard.exec_(self)
