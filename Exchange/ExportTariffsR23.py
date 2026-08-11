#!/usr/bin/env python
# -*- coding: utf-8 -*-

#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

u"""Экспорт тарифа для ЕИС Краснодара"""

import os.path
import shutil
import re
from zipfile import ZipFile, ZIP_DEFLATED

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDir, pyqtSignature, SIGNAL, QDate

from library.dbfpy.dbf import Dbf
from library.DialogBase import CConstructHelperMixin
from library.Utils import anyToUnicode, exceptionToUnicode, forceBool, forceDate, forceDouble, forceRef, forceString, forceStringEx, pyDate, toVariant


from Exchange.Export import CExportHelperMixin

from Exchange.Ui_ExportTariffR23_Wizard_1 import Ui_ExportTariff_Wizard_1
from Exchange.Ui_ExportTariffR23_Wizard_2 import Ui_ExportTariff_Wizard_2


def ExportTariffsR23(widget, tariffRecordList, begDate=None):
    appPrefs = QtGui.qApp.preferences.appPrefs
    fileName = forceString(appPrefs.get('ExportTariffsR23FileName', ''))
    exportAll = forceBool(appPrefs.get('ExportTariffsR23ExportAll', True))
    exportExternal = forceBool(appPrefs.get('ExportTariffsR23ExportExternal', False))
    exportExternalToZero = forceBool(appPrefs.get('ExportTariffsR23ExportExternalToZero', False))
    compressRAR = forceBool(appPrefs.get('ExportTariffsR23CompressRAR', False))
    dlg = CExportTariffR23(fileName, exportAll, exportExternal, exportExternalToZero, compressRAR, tariffRecordList, widget, begDate)
    dlg.exec_()
    appPrefs['ExportTariffsR23FileName'] = toVariant(dlg.fileName)
    appPrefs['ExportTariffsR23ExportAll'] = toVariant(dlg.exportAll)
    appPrefs['ExportTariffsR23ExportExternal'] = toVariant(dlg.exportExternal)
    appPrefs['ExportTariffsR23ExportExternalToZero'] = toVariant(dlg.exportExternalToZero)


class CExportTariffWizardPage1(QtGui.QWizardPage, Ui_ExportTariff_Wizard_1, CConstructHelperMixin):
    def __init__(self, parent):
        QtGui.QWizardPage.__init__(self, parent)
        self.parent = parent  # wtf? скрывать Qt-шный parent - это плохая затея
        self.preSetupUi()
        self.setupUi(self)
        self.postSetupUi()
        self.setTitle(u'Параметры экспорта')
        self.setSubTitle(u'Выбор записей для экспорта')
        self.edtFilterBegDateFrom.setDate(QDate(QDate().currentDate().year(), 1, 1))
        self.edtFilterBegDateTil.setDate(QDate(QDate().currentDate().year(), 12, 31))


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
        self.chkExportExternalTariff.setChecked(self.parent.exportExternal)
        self.chkExportExternalTariffToZero.setChecked(self.parent.exportExternalToZero)
        self.chkExportExternalTariffToZero.setEnabled(self.chkExportExternalTariff.isChecked())
        self.btnClearSelection.setEnabled(not self.parent.exportAll)
        self.chkExportAll.setChecked(self.parent.exportAll)
        if self.parent.exportAll:
            self.setSelectedItemsExportAll()
            self.parent.selectedItems = range(self.modelTable.rowCount())
            self.chkActive.setEnabled(False)
            self.edtFilterBegDateFrom.setEnabled(False)
            self.edtFilterBegDateTil.setEnabled(False)
        else:
            self.tblItems.clearSelection()
            self.parent.selectedItems = []


    def selectedItemList(self):
        if self.parent.exportAll:
            rows = [row for row in self.parent.selectedItems if not self.tblItems.isRowHidden(row)]
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
            self.setSelectedItemsExportAll()
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

    @pyqtSignature('')
    def on_chkExportExternalTariff_clicked(self):
        self.parent.exportExternal = self.chkExportExternalTariff.isChecked()
        self.chkExportExternalTariffToZero.setEnabled(self.chkExportExternalTariff.isChecked())
        if not self.chkExportExternalTariff.isChecked():
            self.chkExportExternalTariffToZero.setChecked(False)
            self.parent.exportExternalToZero = self.chkExportExternalTariffToZero.isChecked()
        if self.chkExportAll.isChecked():
            self.setSelectedItemsExportAll()
        else:
            self.tblItems.clearSelection()
            self.parent.selectedItems = []
            self.emit(SIGNAL('completeChanged()'))
            self.applyFilter()

    @pyqtSignature('')
    def on_chkExportExternalTariffToZero_clicked(self):
        self.parent.exportExternalToZero = self.chkExportExternalTariffToZero.isChecked()

    def setSelectedItemsExportAll(self):
        if self.chkExportAll.isChecked():
            self.parent.selectedItems = range(self.modelTable.rowCount())
            for row in self.parent.selectedItems:
                match = True
                if not self.chkExportExternalTariff.isChecked():
                    match = match and not self.modelTable.data(self.modelTable.index(row, 0),
                                                               Qt.CheckStateRole).toBool()
                self.tblItems.setRowHidden(row, not match)
    
    
    def applyFilter(self):
        self.selectionModelTable.clearSelection()
        self.parent.selectedItems = []
        if self.chkActive.isChecked():
            self.parent.begDate = self.edtFilterBegDateFrom.date()
        else:
            self.parent.begDate = None
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
                    dataStart = QDate.fromString(
                        self.modelTable.index(row, self.modelTable.getColIndex('begDate')).data().toString(),
                        "dd.MM.yyyy")  # 8
                    match = match and dataStart >= filter_begDateFrom and dataStart <= filter_begDateTil
                if match and not self.chkExportExternalTariff.isChecked():
                    match = match and not self.modelTable.data(self.modelTable.index(row, 0), Qt.CheckStateRole).toBool()
            self.tblItems.setRowHidden(row, not match)
            if first_matched_row == -1 and match:
                first_matched_row = row
        self.tblItems.setCurrentRow(first_matched_row)
        self.emit(SIGNAL('completeChanged()'))


class CExportTariffWizardPage2(QtGui.QWizardPage, Ui_ExportTariff_Wizard_2, CExportHelperMixin):
    def __init__(self, parent):
        self.done = False
        QtGui.QWizardPage.__init__(self, parent)
        CExportHelperMixin.__init__(self)
        self.setupUi(self)
        self.parent = parent  # wtf? скрывать Qt-шный parent - это плохая затея
        self.setTitle(u'Параметры сохранения')
        self.setSubTitle(u'Выбор места для сохранения')
        self.progressBar.setFormat('%p%')
        self.progressBar.setValue(0)
        self.edtFileName.setText(self.parent.fileName)
        self.btnExport.setEnabled(self.parent.fileName != '')
        self.checkRAR.setChecked(self.parent.compressRAR)
        self.lpuCode = ''


    def initializePage(self):
        self.btnExport.setEnabled(self.parent.fileName != '')
        self.done = False


    def isComplete(self):
        return self.done

       
    def create22Dbf(self):
        dbfName = self.parent.getFullDbfFileName()
        dbf = Dbf(dbfName, new=True, encoding='cp866')
        dbf.addField(
            ('CODE_MO', 'C', 5),
            ('KUSL', 'C', 15),
            ('DATN', 'D'),
            ('DATO', 'D'),
            ('TARIF', 'N', 10, 2)
            )
        return dbf


    def writeDBF(self, outFile, tariffRecordList, selectedItems):
        try:
            self.progressBar.setMaximum(max(len(selectedItems), 1))
            self.progressBar.reset()
            self.progressBar.setValue(0)

            for i in selectedItems:
                if not forceBool(tariffRecordList[i].value('deleted')):
                    record = tariffRecordList[i]
                    if self.wizard().page(0).chkExportExternalTariffToZero.isChecked() and forceBool(
                            record.value('isExternal')):
                        record.setValue('price', toVariant(0.00))
                    self.writeRecord(outFile, record)
                    QtGui.qApp.processEvents()
                    self.progressBar.step()

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
    

    def writeRecord(self, outFile, record):
        price = forceDouble(record.value('price'))
        row = outFile.newRecord()
        begDate = forceDate(record.value('begDate'))
        endDate = forceDate(record.value('endDate'))
        
        row['CODE_MO'] = self.lpuCode
        row['KUSL'] = self.getServiceInfis(forceRef(record.value('service_id')))
        row['DATN'] = pyDate(self.parent.begDate if begDate < self.parent.begDate else begDate)
        if endDate:
            row['DATO'] = pyDate(endDate)
        row['TARIF'] = price
        row.store()


    @pyqtSignature('')
    def on_btnSelectFile_clicked(self):
        dir = QtGui.QFileDialog.getExistingDirectory(self,
                u'Выберите директорий для сохранения файла выгрузки',
                 forceStringEx(self.edtFileName.text()),
                 QtGui.QFileDialog.ShowDirsOnly)
        if forceString(dir):
            self.edtFileName.setText(QDir.toNativeSeparators(dir))


    @pyqtSignature('')
    def on_btnExport_clicked(self):
        dstDir = self.edtFileName.text()
        if dstDir.isEmpty():
            return

        if not self.parent.selectedItems:
            QtGui.QMessageBox.warning(self,
                                      u'Экспорт тарифов договора',
                                      u'Не выбрано ни одного элемента для выгрузки')
            self.parent.back() # вернемся на пред. страницу. пусть выбирают
            return

        if self.edtOms.text():
            if re.match("\d{5}", self.edtOms.text()) and \
                    QtGui.qApp.db.translate('Organisation', 'infisCode', self.edtOms.text(), 'id'):
                self.lpuCode = forceString(self.edtOms.text())
            else:
                QtGui.QMessageBox.warning(self,
                                          u'Экспорт тарифов договора',
                                          u'Код ЛПУ в системе ОМС заполнен не корректно')
                return
        else:
            self.lpuCode = forceString(QtGui.qApp.db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'infisCode'))
        
        outFile22 = self.create22Dbf()

        if (self.writeDBF(outFile22, self.parent.tariffRecordList, self.parent.selectedItems)):
            self.progressBar.setText(u'Готово')
        else:
            self.progressBar.setText(u'Прервано')
        outFile22.close()

        fileName = self.parent.getFullDbfFileName()          

        dstDir = forceStringEx(dstDir)

        if not os.path.exists(dstDir):
            os.makedirs(dstDir)
                
        if self.checkRAR.isChecked():           
            self.progressBar.setText(u'Сжатие')
            zipFilePath = os.path.join(forceStringEx(self.parent.getTmpDir()), self.lpuCode + '.zip')
            zf = ZipFile(zipFilePath, 'w', allowZip64=True)
            
            filePath = os.path.join(forceStringEx(self.parent.getTmpDir()), os.path.basename(u'SPR22.DBF'))
            zf.write(filePath, u'SPR22.DBF', ZIP_DEFLATED)
            zf.close()
            success, result = QtGui.qApp.call(self, shutil.move, (zipFilePath, dstDir))
            self.progressBar.setText(u'Сжато в "%s"' %  os.path.join(dstDir, os.path.basename(zipFilePath)))
        else:
            
            dstDbf = os.path.join(dstDir, os.path.basename(fileName))
            success, result = QtGui.qApp.call(self, shutil.move, (fileName, dstDbf))

        self.done = success
        self.emit(SIGNAL('completeChanged()'))


    @pyqtSignature('')
    def on_checkRAR_clicked(self):
        self.parent.compressRAR = self.checkRAR.isChecked()


    @pyqtSignature('QString')
    def on_edtFileName_textChanged(self):
        self.parent.fileName = self.edtFileName.text()
        self.btnExport.setEnabled(self.parent.fileName != '')
        self.emit(SIGNAL('completeChanged()'))


class CExportTariffR23(QtGui.QWizard):
    def __init__(self, fileName, exportAll, exportExternal, exportExternalToZero, compressRAR, tariffRecordList, parent=None, begDate=None):
        QtGui.QWizard.__init__(self, parent, Qt.Dialog)
        self.setWizardStyle(QtGui.QWizard.ModernStyle)
        self.setWindowTitle(u'Экспорт тарифов договора для ЕИС Краснодара')
        self.selectedItems = []
        self.fileName= fileName
        self.exportAll = exportAll
        self.exportExternal = exportExternal
        self.exportExternalToZero = exportExternalToZero
        self.compressRAR = compressRAR
        self.begDate = begDate
        self.tariffRecordList = tariffRecordList
        self.addPage(CExportTariffWizardPage1(self))
        self.addPage(CExportTariffWizardPage2(self))
        self.tmpDir = ''
        self.currentIdChanged.connect(self.saveSelected)
    
    
    def saveSelected(self):
        self.selectedItems = self.page(0).selectedItemList()
    

    def getTmpDir(self):
        if not self.tmpDir:
            self.tmpDir = QtGui.qApp.getTmpDir('TariffR23')
        return self.tmpDir


    def getFullDbfFileName(self):
        return os.path.join(self.getTmpDir(), u'SPR22.DBF')


    def cleanup(self):
        if self.tmpDir:
            QtGui.qApp.removeTmpDir(self.tmpDir)
            self.tmpDir = ''


    def exec_(self):
        QtGui.QWizard.exec_(self)
        self.cleanup()
