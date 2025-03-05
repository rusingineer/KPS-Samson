#!/usr/bin/env python
# -*- coding: utf-8 -*-

#############################################################################
##
## Copyright (C) 2006-2013 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2013-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

u"""
Экспорт МЭС в XML
"""
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QXmlStreamWriter, QVariant, Qt, QString

from Exchange.Utils import compressFileInRar
from RefBooks.Tables import rbCode, rbName
from Ui_ExportXML_Wizard_1 import Ui_ExportXML_Wizard_1
from Ui_ExportXML_Wizard_2 import Ui_ExportXML_Wizard_2
from library.DialogBase import CConstructHelperMixin
from library.TableModel import CTableModel, CTextCol
from library.Utils import forceString, forceBool, toVariant, forceDate, forceDouble, forceRef, anyToUnicode, addDotsEx
from library.crbcombobox import CRBModelDataCache, CRBComboBox

mesSimpleFields = ('code', 'name', 'descr', 'patientModel', 'minDuration',
    'maxDuration', 'avgDuration', 'tariff', 'KSGNorm', 'active', 'internal')

mesRefFields    =  ('group_id', )
mesRefTableNames=  ('mrbMESGroup', )
mesKeyFields = ('group_id',  'code',  'name')

mesVisitSimpleFields = ('serviceCode', 'additionalServiceCode', 'groupCode', 'averageQnt', 'sex', 'begAgeUnit', 'minimumAge', 'endAgeUnit', 'maximumAge', 'controlPeriod')
mesVisitRefFields = ('visitType_id', 'speciality_id')
mesVisitRefTableNames=  ('mrbVisitType', 'mrbSpeciality', )

mesServiceSimpleFields = ('groupCode', 'averageQnt', 'necessity', 'binding', 'sex', 'begAgeUnit', 'minimumAge', 'endAgeUnit', 'maximumAge', 'controlPeriod')
mesServiceRefFields = ('service_id', )
mesServiceRefTableNames=  ('mrbService', )

mesLimitationSimpleFields = ('sex', 'begAgeUnit', 'minimumAge', 'endAgeUnit', 'maximumAge', 'controlPeriod')
mesLimitationRefFields = tuple()
mesLimitationRefTableNames=  tuple()

mesMKBSimpleFields = ('mkb', )
mesMKBRefFields = tuple()
mesMKBRefTableNames=  tuple()

exportVersion = '0.01'

def ExportXML(widget):
    appPrefs = QtGui.qApp.preferences.appPrefs
    fileName = forceString(appPrefs.get('ExportMesXMLFileName', ''))
    compressRAR = forceBool(appPrefs.get('ExportMesXMLCompressRAR', False))
    dlg = CExportMesXML(fileName, compressRAR, widget)
    dlg.exec_()
    appPrefs['ExportMesXMLFileName'] = toVariant(dlg.fileName)
    appPrefs['ExportMesXMLCompressRAR'] = toVariant(dlg.compressRAR)


class CMesTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)

        self.addColumn(CTextCol(u'Код',                 [rbCode], 20))
        self.addColumn(CTextCol(u'Наименование',        [rbName], 40))
        self.addColumn(CTextCol(u'Описание',        ['descr'], 40))
        self.loadField('*')
        self.setTable('MES')


class CMyXmlStreamWriter(QXmlStreamWriter):
    def __init__(self, parent, recordList, idList):
        QXmlStreamWriter.__init__(self)
        self._parent = parent
        self._recordList = recordList
        self._idList = idList
        self.db = QtGui.qApp.db
        self.setAutoFormatting(True)
        self.tableVisits = self.db.table('MES_visit')
        self.tableService = self.db.table('MES_service')
        self.tableLimitation = self.db.table('MES_limitedBySexAge')
        self.tableMKB = self.db.table('MES_mkb')
        self.refValueCache = {}
        self.visitRecordList = {}
        self.serviceRecordList = {}
        self.limitationRecordList = {}
        self.mkbRecordList = {}


    def writeRecord(self, record, elementName, simpleFields,  refFields,  closeElement = True):
        self.writeStartElement(elementName)

        # все нессылочные свойства действия экспортируем как атрибуты
        for fieldName in simpleFields:
            value = record.value(fieldName)
            fieldType = record.field(fieldName).type()

            if fieldType == QVariant.Date:
                strValue = forceDate(value).toString(QtCore.Qt.ISODate)
            elif fieldType == QVariant.Double:
                strValue = unicode(forceDouble(value))
            else:
                strValue = forceString(value)

            self.writeAttribute(fieldName, strValue)

        # ссылочные свойства экспортируем как элементы с атрибутами code и name
        for fieldName in refFields:
            elementName = fieldName[:-3]
            self.writeStartElement(elementName)
            value = forceRef(record.value(fieldName))
            if value:
                cache = self.refValueCache[fieldName]
                self.writeAttribute('code', cache.getStringById(value, CRBComboBox.showCode))
                self.writeAttribute('name', cache.getStringById(value, CRBComboBox.showName))
            self.writeEndElement()

        if closeElement:
            self.writeEndElement()


    def writeMes(self, record):
        # Выгружаем МЭСы
        self.writeRecord(record, 'MesElement', mesSimpleFields, mesRefFields,  False)
        mesId = forceRef(record.value('id'))

        # Выгружаем визиты
        for visit in self.visitRecordList.get(mesId, []):
            self.writeRecord(visit, 'MesVisit', mesVisitSimpleFields,  mesVisitRefFields)

        # Выгружаем услуги
        for service in self.serviceRecordList.get(mesId, []):
            self.writeRecord(service, 'MesService', mesServiceSimpleFields,  mesServiceRefFields)

        # Выгружаем половозрастные ограничения
        for limitationRecord in self.limitationRecordList.get(mesId, []):
            self.writeRecord(limitationRecord, 'MesLimitation', mesLimitationSimpleFields,  mesLimitationRefFields)

        # Выгружаем МКБ
        for mkbRecord in self.mkbRecordList.get(mesId, []):
            self.writeRecord(mkbRecord, 'MesMKB', mesMKBSimpleFields,  mesMKBRefFields)

        self.writeEndElement() # MesElement


    def prepareRecordList(self, table):
        result = {}
        cond = [table['master_id'].inlist(self._idList),
                        table['deleted'].eq(0)]

        records = self.db.getRecordList(table, where=cond)

        for x in records:
            id = forceRef(x.value('master_id'))
            result.setdefault(id, []).append(x)

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
            progressBar.setMaximum(2 + len(mesRefTableNames))
            progressBar.reset()
            progressBar.setText(u'Запрос в БД ...')
            progressBar.setValue(0)

            for field, tableName in zip(mesRefFields + mesVisitRefFields + mesServiceRefFields,
                                        mesRefTableNames + mesVisitRefTableNames + mesServiceRefTableNames):
                self.refValueCache[field] = CRBModelDataCache.getData(tableName, True)
                progressBar.step()
                QtGui.qApp.processEvents()

            self.visitRecordList = self.prepareRecordList(self.tableVisits)
            progressBar.step()
            QtGui.qApp.processEvents()
            self.serviceRecordList= self.prepareRecordList(self.tableService)
            progressBar.step()
            QtGui.qApp.processEvents()
            self.limitationRecordList= self.prepareRecordList(self.tableLimitation)
            progressBar.step()
            QtGui.qApp.processEvents()
            self.mkbRecordList= self.prepareRecordList(self.tableMKB)
            progressBar.step()
            QtGui.qApp.processEvents()

            progressBar.setMaximum(max(len(self._recordList), 1))
            progressBar.reset()
            progressBar.setFormat('%p%')
            progressBar.setValue(0)

            self.setDevice(device)
            self.writeStartDocument()
            self.writeDTD('<!DOCTYPE xMes>')
            self.writeStartElement('MesExport')
            self.writeAttribute('SAMSON',
                                '2.0 revision(%s, %s)' %(lastChangedRev, lastChangedDate))
            self.writeAttribute('version', exportVersion)

            for record in self._recordList:
                self.writeMes(record)
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
            QtGui.QMessageBox.critical (self._parent,
                u'Произошла ошибка ввода-вывода', msg, QtGui.QMessageBox.Close)
            return False
        except Exception, e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical (self._parent,
                u'Произошла ошибка', unicode(e), QtGui.QMessageBox.Close)
            return False

        return True


class CExportWizardPage1(QtGui.QWizardPage, Ui_ExportXML_Wizard_1, CConstructHelperMixin):
    def __init__(self, parent):
        QtGui.QWizardPage.__init__(self, parent)
        self._parent = parent
        self.table = QtGui.qApp.db.table('MES')
        self.order = ['code', 'name', 'id']
        self.filter = [self.table['deleted'].eq(0)]

        self.preSetupUi()
        self.setupUi(self)
        self.postSetupUi()
        self.setTitle(u'Параметры экспорта')
        self.setSubTitle(u'Выбор записей для экспорта')


    def preSetupUi(self):
        self.addModels('Table', CMesTableModel(self))
        self.modelTable.cellReadOnly = lambda index: True


    def postSetupUi(self):
        self.setModels(self.tblItems, self.modelTable, self.selectionModelTable)
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        idList = self.select()
        self.modelTable.setIdList(idList)
        self.selectionModelTable.clearSelection()
        self.tblItems.setFocus(Qt.OtherFocusReason)
        self._parent.selectedItemsIdList = []


    def isComplete(self):
        # проверим пустой ли у нас список выбранных элементов
        return self._parent.selectedItemsIdList != []


    def select(self):
        return QtGui.qApp.db.getIdList(self.table,
                            'id', self.filter,  self.order)


    def selectedItemList(self):
        rows = [self.modelTable.idList()[index.row()] for index in self.selectionModelTable.selectedRows()]
        rows.sort()
        return rows


    def selectedRecordList(self,  idList):
        recordList = [self.modelTable.getRecordById(id) for id in idList]
        return recordList


    @QtCore.pyqtSignature('QModelIndex')
    def on_tblItems_clicked(self, index):
        self._parent.selectedItemsIdList = self.selectedItemList()
        self.emit(QtCore.SIGNAL('completeChanged()'))


    @QtCore.pyqtSignature('')
    def on_btnFilter_clicked(self):
        self.filter = [self.table['deleted'].eq(0)]
        code = self.edtCodeFilter.text()
        if code:
            self.filter.append(self.table['code'].like(addDotsEx(unicode(code))))
        name = self.edtNameFilter.text()
        if name:
            self.filter.append(self.table['name'].like(addDotsEx(unicode(name))))
        self.modelTable.setIdList(self.select())
        self.modelTable.reset()


    @QtCore.pyqtSignature('')
    def on_btnSelectAll_clicked(self):
        selectedItemsIdList = self.modelTable.idList()
        self._parent.selectedItemsIdList = selectedItemsIdList
        for id in selectedItemsIdList:
            row = self.modelTable.findItemIdIndex(id)
            if row >= 0:
                index = self.tblItems.model().index(row, 0)
                if index and index.isValid():
                    self.tblItems.selectionModel().select(index,
                        QtGui.QItemSelectionModel.Select|QtGui.QItemSelectionModel.Rows)
        self.emit(QtCore.SIGNAL('completeChanged()'))


    @QtCore.pyqtSignature('')
    def on_btnClearSelection_clicked(self):
        self.selectionModelTable.clearSelection()
        self._parent.selectedItemsIdList = []
        self.emit(QtCore.SIGNAL('completeChanged()'))


class CExportWizardPage2(QtGui.QWizardPage, Ui_ExportXML_Wizard_2):
    messageBoxTitle = u'Экспорт МЭС'

    def __init__(self, parent):
        self.done = False
        QtGui.QWizardPage.__init__(self, parent)
        self.setupUi(self)
        self._parent = parent
        self.setTitle(u'Параметры сохранения')
        self.setSubTitle(u'Выбор места для сохранения')
        self.progressBar.setFormat('%p%')
        self.progressBar.setValue(0)
        self.edtFileName.setText(self._parent.fileName)
        self.btnExport.setEnabled(self._parent.fileName != '')
        self.checkRAR.setChecked(self._parent.compressRAR)


    def initializePage(self):
        self.btnExport.setEnabled(self._parent.fileName != '')
        self.done = False


    def isComplete(self):
        return self.done


    def setExportMode(self, flag):
        self.btnExport.setEnabled(not flag)
        self.checkRAR.setEnabled(not flag)


    @QtCore.pyqtSignature('')
    def on_btnSelectFile_clicked(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self,
                u'Укажите файл с данными', self.edtFileName.text(),
                u'Файлы XML (*.xml)')

        if fileName:
            self.edtFileName.setText(fileName)
            self._parent.fileName = fileName
            self.btnExport.setEnabled(True)


    @QtCore.pyqtSignature('')
    def on_btnExport_clicked(self):
        fileName = self.edtFileName.text()
        self.setExportMode(True)

        if fileName.isEmpty():
            return

        messageBoxTitle = u'Ошибка!'

        if not self._parent.selectedItemsIdList:
            QtGui.QMessageBox.warning(self,
                                      messageBoxTitle,
                                      u'Не выбрано ни одного элемента для выгрузки')
            self._parent.back() # вернемся на пред. страницу. пусть выбирают
            return

        outFile = QtCore.QFile(fileName)
        if not outFile.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
            QtGui.QMessageBox.warning(self,
                                      messageBoxTitle,
                                      QString(u'Не могу открыть файл для записи %1:\n%2.').arg(fileName).arg(outFile.errorString()))
            self.setExportMode(False)
            return

        recordList = self._parent.page(0).selectedRecordList(self._parent.selectedItemsIdList)
        myXmlStreamWriter = CMyXmlStreamWriter(self, recordList, self._parent.selectedItemsIdList)

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
        self.setExportMode(False)
        self.btnExport.setEnabled(False)
        self.emit(QtCore.SIGNAL('completeChanged()'))


    @QtCore.pyqtSignature('')
    def on_checkRAR_clicked(self):
        self._parent.compressRAR = self.checkRAR.isChecked()


    @QtCore.pyqtSignature('QString')
    def on_edtFileName_textChanged(self):
        self._parent.fileName = self.edtFileName.text()
        self.btnExport.setEnabled(self._parent.fileName != '')
        self.emit(QtCore.SIGNAL('completeChanged()'))


class CExportMesXML(QtGui.QWizard):
    def __init__(self, fileName, compressRAR, parent=None):
        QtGui.QWizard.__init__(self, parent, Qt.Dialog)
        self.setWizardStyle(QtGui.QWizard.ModernStyle)
        self.setWindowTitle(u'Экспорт МЭС')
        self.selectedItemsIdList = []
        self.fileName= fileName
        self.compressRAR = compressRAR
        self.addPage(CExportWizardPage1(self))
        self.addPage(CExportWizardPage2(self))
