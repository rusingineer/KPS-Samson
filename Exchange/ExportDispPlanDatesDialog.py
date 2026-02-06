# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import QTimer, SIGNAL, Qt, pyqtSignature, QVariant, QModelIndex, QDate
from PyQt4.QtGui import QDialog, QAction

from library.DialogBase import CConstructHelperMixin
from library.InDocTable import CRecordListModel, CInDocTableCol, CDateInDocTableCol, CBoolInDocTableCol, CDateTimeInDocTableCol
from library.SortFilterProxyTableModel import CSortFilterProxyTableModel
from library.TableModel import CTableModel, CIntCol, CDesignationCol
from library.Calendar import wpFiveDays, wpSixDays, wpSevenDays, getNextWorkDay
from library.Utils import exceptionToUnicode, forceDateTime, forceString, getPref, setPref, toVariant, forceInt, forceRef, forceDate

import Exchange.AttachService as AttachService

from Ui_ExportDispPlanDatesDialog import Ui_ExportDispPlanDatesDialog


class CExportDispPlanDatesDialog(QDialog, CConstructHelperMixin, Ui_ExportDispPlanDatesDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.addModels('PlanDates', CPlanDatesModel(self))
        self.addModels('PlanDatesSort', CSortPlanDatesModel(self, self.modelPlanDates))
        self.addModels('PlanDateErrors', CPlanDateErrorsModel(self))
        self.addObject('actReplicate', QAction(u'Тиражировать', self))
        self.setupUi(self)
        self.setModels(self.tblPlanDates, self.modelPlanDatesSort, self.selectionModelPlanDatesSort)
        self.setModels(self.tblPlanDateErrors, self.modelPlanDateErrors, self.selectionModelPlanDateErrors)
        self.tblPlanDates.addPopupDelRow()
        self.tblPlanDates.addPopupAction(self.actReplicate)
        self.tblPlanDateErrors.setEnabled(False)
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
        self.loadPreferences()
        self.connect(self.tblPlanDates.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sortByColumn)
        self.__sortColumn = None
        self.__sortAscending = False
    
    def loadPreferences(self):
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, self.objectName(), {})
        date = getPref(preferences, 'ExportDispPlanDatesDialogDateFilter', None)
        if date and type(date) == QDate and date.isValid():
            self.edtDate.setDate(date)
        else:
            self.edtDate.setDate(QDate(QDate.currentDate().year(),1,1))

    def savePreferences(self):
        preferences = {}
        setPref(preferences,'ExportDispPlanDatesDialogDateFilter', self.edtDate.date())
        setPref(QtGui.qApp.preferences.windowPrefs, self.objectName(), preferences)

    def showEvent(self, event):
        QTimer.singleShot(0, self.updateList)
        
    def disableControls(self, disabled=True):
        if disabled:
            self.controlDisableLevel += 1
        else:
            self.controlDisableLevel -= 1
        if disabled or self.controlDisableLevel == 0:
            self.tblPlanDates.setDisabled(disabled)
            self.tblPlanDateErrors.setDisabled(disabled or not self.selectionModelPlanDates.hasSelection())
            self.btnExport.setDisabled(disabled)
            self.btnOK.setDisabled(disabled)
            self.btnCancel.setDisabled(disabled)
            self.btnApply.setDisabled(disabled or not self.modelPlanDates.hasChanges())

    def enableControls(self):
        self.disableControls(False)

    def controlsDisabled(self):
        return self.controlDisableLevel > 0

    def updateList(self):
        self.disableControls()
        try:
            QtGui.qApp.processEvents()
            self.modelPlanDates.loadItems()
            self.modelPlanDates.setCodeMo(self.getSelectedCodeMo())
            self.btnExport.setEnabled(self.modelPlanDates.realRowCount() > 0)
        except Exception as e:
            QtGui.QMessageBox.critical(self, u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)
        finally:
            self.enableControls()
    
    def export(self):
        self.disableControls()
        try:
            if self.modelPlanDates.hasChanges() and not self.applyChanges():
                return
            if not self.datesValidForExport():
                return
            self.btnExport.setText(u'Отправка...')
            QtGui.qApp.processEvents()
            result = AttachService.putEvPlanDates(self.getSelectedCodeMo())
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
            valid, message = self.modelPlanDates.validateItems()
            if valid:
                self.modelPlanDates.saveItems()
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
        if self.modelPlanDates.hasChanges():
            answer = QtGui.QMessageBox.warning(self,
                u'Список контактов', 
                u'Сохранить изменения?',
                QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel)
            if answer == QtGui.QMessageBox.Cancel:
                return
            elif answer == QtGui.QMessageBox.Yes and not self.applyChanges():
                return
        QtGui.QDialog.reject(self)
    
    def datesValidForExport(self):
        if self.modelPlanDates.hasChanges():
            QtGui.QMessageBox.warning(self, u'Проверка данных', u'Необходимо применить изменения перед отправкой!', QtGui.QMessageBox.Close)
            return False
        return True
    
    def getSelectedCodeMo(self):
        orgStructureId = self.cmbOrgStructure.value()
        if orgStructureId:
            db = QtGui.qApp.db
            codeMo = forceString(db.translate('OrgStructure', 'id', orgStructureId, 'bookkeeperCode'))
        else:
            codeMo = None
        return codeMo

    def sortByColumn(self, column):
        header = self.tblPlanDates.horizontalHeader()
        if column == self.__sortColumn:
            if self.__sortAscending:
                self.__sortAscending = False
            else:
                self.__sortAscending = True
        else:
            self.__sortColumn = column
            self.__sortAscending = True
        header.setSortIndicatorShown(True)
        header.setSortIndicator(column, Qt.AscendingOrder if self.__sortAscending else Qt.DescendingOrder)
        # self.modelPlanDates.sortData(column, self.__sortAscending)
        self.modelPlanDatesSort.sort(column, Qt.AscendingOrder if self.__sortAscending else Qt.DescendingOrder)

    @pyqtSignature('')
    def on_btnOK_clicked(self):
        if self.modelPlanDates.hasChanges() and not self.applyChanges():
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
    def on_modelPlanDates_dataChanged(self, topLeft, bottomRight):
        self.btnApply.setEnabled(not self.controlsDisabled())

    @pyqtSignature('QModelIndex, int, int')
    def on_modelPlanDates_rowsInserted(self, parent, first, last):
        self.btnApply.setEnabled(not self.controlsDisabled())

    @pyqtSignature('QModelIndex, int, int')
    def on_modelPlanDates_rowsRemoved(self, parent, first, last):
        self.btnApply.setEnabled(not self.controlsDisabled())

    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        self.modelPlanDates.setCodeMo(self.getSelectedCodeMo())
    
    @pyqtSignature('QDate')
    def on_edtDate_dateChanged(self, date):
        if date:
            self.modelPlanDatesSort.setFilter('evdt', forceDateTime(date), CSortFilterProxyTableModel.MatchGreaterEqual) 
        else:
            self.modelPlanDatesSort.removeFilter('evdt') 

    @pyqtSignature('')
    def on_actReplicate_triggered(self):
        model = self.tblPlanDates.model()
        sort_index = self.tblPlanDates.currentIndex()
        if not sort_index:
            return
        source_index = model.mapToSource(sort_index)
        source_model = model.sourceModel()

        row = source_index.row()
        record = source_model.items()[row]
        if record.isNull('evdt'):
            return
        begDate = forceDate(record.value('evdt')).addDays(1)
        dialog = CPlanDateReplicateDialog(self)
        if dialog.exec_():
            numDays = dialog.numDays
            weekProfile = dialog.weekProfile
            source_model.replicateRow(row, numDays, weekProfile)
            self.modelPlanDatesSort.invalidateFilter()


class CDictInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width, values, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.values = values

    def toString(self, val, record):
        if val.isNull():
            return ''
        else:
            return toVariant(self.values[forceInt(val)])

    def createEditor(self, parent):
        self.indexByKey = {}
        editor = QtGui.QComboBox(parent)
        for key, value in self.values.iteritems():
            index = editor.count()
            editor.addItem(value, QVariant(key))
            self.indexByKey[key] = index
        return editor

    def setEditorData(self, editor, value, record):
        if value.isNull():
            index = -1
        else:
            index = self.indexByKey[forceInt(value)]
        editor.setCurrentIndex(index)

    def getEditorData(self, editor):
        index = editor.currentIndex()
        if index == -1:
            return QVariant()
        else:
            return editor.itemData(index)


class CPlanDatesModel(CRecordListModel):
    kind = {
        1: u'Диспансеризация',
        2: u'Проф. осмотр'
    }
    meth = {
        1: u'по адресу МО',
        2: u'выезд мобильной бригады в отдаленный район',
        3: u'доставка граждан из отдаленного района в МО'
    }

    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CDateInDocTableCol(u'Дата', 'evdt', 20, inputMask='(999) 999-99-99'))
        self.addCol(CDictInDocTableCol(u'Вид мероприятия', 'kind', 20, CPlanDatesModel.kind))
        self.addCol(CDictInDocTableCol(u'Метод', 'meth', 20, CPlanDatesModel.meth))
        self.addCol(CInDocTableCol(u'Комментарий', 'comment', 20, maxLength=254))
        self.addCol(CInDocTableCol(u'Адрес', 'address', 20, maxLength=254))
        self.addCol(CBoolInDocTableCol(u'Изменен', 'changed', 20).setReadOnly())
        self.addCol(CBoolInDocTableCol(u'Отправлен успешно', 'exportSuccess', 20).setReadOnly())
        self.addCol(CDateTimeInDocTableCol(u'Дата экспорта', 'exportDate', 20).setReadOnly())
        self._enableAppendLine = True
        self._extColsPresent = False
        self._hasChanges = False
        db = QtGui.qApp.db
        self.table = db.table('disp_PlanDates')
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
        allRecords = db.getRecordList('disp_PlanDates', '*', order='evdt')
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
        if role == Qt.EditRole and self._cols[index.column()].fieldName() == 'evdt':
            value = toVariant(forceDateTime(forceDate(value)))
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
        table = db.table('disp_PlanDates')
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
        newRecord = QtGui.qApp.db.table('disp_PlanDates').newRecord()
        newRecord.setValue('code_mo', self.codeMo)
        return newRecord

    def validateItems(self):
        for record in self.items():
            evdt = record.value('evdt')
            if evdt.isNull():
                return (False, u'Дата мероприятия должна быть заполнена')
        return (True, None)

    def hasChanges(self):
        return self._hasChanges
    
    def setCodeMo(self, newCodeMo):
        self.codeMo = newCodeMo
        items = self.itemsByCodeMo.setdefault(self.codeMo, [])
        self.setItems(items)
        self.reset()
    
    def setDate(self, date):
        self.date = date
        items = self.itemsByCodeMo.setdefault(self.codeMo, [])
        self.setItems(items)
        self.reset()
    
    def replicateRow(self, row, numDays, weekProfile):
        sourceRecord = self.items()[row]
        newDate = getNextWorkDay(forceDate(sourceRecord.value('evdt')), weekProfile)
        newRecords = []
        self.beginInsertRows(QModelIndex(), row + 1, row + numDays)
        for i in xrange(0, numDays):
            newRecord = QtSql.QSqlRecord(sourceRecord)
            newRecord.setValue('id', None)
            newRecord.setValue('evdt', forceDateTime(newDate))
            self._items.insert(row + 1 + i, newRecord)
            newDate = getNextWorkDay(newDate, weekProfile)
        self.endInsertRows()


class CSortPlanDatesModel(CSortFilterProxyTableModel): #нахардкодили тут codeMO, приходится выкручиваться
    def createEditor(self, index, parent):
        column = index.column()
        if hasattr(self.model()._cols[column], 'setIndex'):
            self.model()._cols[column].setIndex(index)
        return self.model()._cols[column].createEditor(parent)


    def filterAcceptsRow(self, sourceRow, sourceParent):
        if sourceRow >= len(self.sourceModel().items()):
            return True
        return super(CSortPlanDatesModel, self).filterAcceptsRow(sourceRow, sourceParent)

    def rowCount(self, parent=QModelIndex()):
        if parent is None:
            parent = QModelIndex()
        return super(CSortPlanDatesModel, self).rowCount(parent)


    def __getattr__(self, name):
        # добавил ф-ию, т.к. много ошибок валилось из-за того, что у этой модели нет методов source-модели
        return getattr(self.sourceModel(), name)



class CPlanDateErrorsModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CIntCol(u'Код ошибки', ['errorType_id'], 20),
            CDesignationCol(u'Текст ошибки', ['errorType_id'], ('disp_ErrorTypes', 'name'), 20)
            ], 'disp_PlanDateErrors')

    def update(self, planDate_id):
        if planDate_id is None:
            idList = []
        else:
            db = QtGui.qApp.db
            table = db.table('disp_PlanDateErrors')
            where = [table['planDate_id'].eq(planDate_id)]
            idList = db.getIdList(table, where=where)
        self.setIdList(idList)


class CPlanDateReplicateDialog(QtGui.QDialog):
    WeekProfiles = (wpFiveDays, wpSixDays, wpSevenDays)

    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.lblAmount = QtGui.QLabel(u"Количество", self)
        self.edtAmount = QtGui.QSpinBox(self)

        self.lblWeekProfile = QtGui.QLabel(u'Длительность рабочей недели', self)
        self.cmbWeekProfile = QtGui.QComboBox(self)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok, Qt.Horizontal, self)

        self.layout = QtGui.QGridLayout(self)

        self.layout.addWidget(self.lblAmount, 0, 0)
        self.layout.addWidget(self.edtAmount, 0, 1)
        self.layout.addWidget(self.lblWeekProfile, 1, 0)
        self.layout.addWidget(self.cmbWeekProfile, 1, 1)
        self.layout.addWidget(self.buttonBox, 2, 1)

        self.setLayout(self.layout)

        self.edtAmount.setMinimum(1)
        self.edtAmount.setValue(1)

        self.cmbWeekProfile.addItem(u'пятидневная рабочая неделя')
        self.cmbWeekProfile.addItem(u'шестидневная рабочая неделя')
        self.cmbWeekProfile.addItem(u'семидневная рабочая неделя')
        self.cmbWeekProfile.setCurrentIndex(0)

        self.setWindowTitle(u'Тиражирование плановой даты')

        self.connect(self.buttonBox, SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, SIGNAL('rejected()'), self.reject)

    def exec_(self):
        r = QtGui.QDialog.exec_(self)
        if r:
            self.numDays = self.edtAmount.value()
            self.weekProfile = self.WeekProfiles[self.cmbWeekProfile.currentIndex()]
        return r
