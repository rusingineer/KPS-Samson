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
##
## Диалог редактирования расписания
##
#############################################################################


from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, pyqtSignature, QDateTime, QVariant

from library.DateEdit import CDateEdit
from library.DialogBase import CDialogBase
from library.InDocTable import CDateInDocTableCol, CRBInDocTableCol, CRecordListModel, CTextInDocTableCol
from library.SortFilterProxyTableModel import CSortFilterProxyTableModel
from library.Utils import forceInt, forceRef, forceString, forceDate, toVariant

from OrgStructComboBoxes import COrgStructureModel
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CReportViewDialog
from Ui_PersonSubstitution import Ui_PersonSubstitution
from PersonComboBoxEx import CPersonComboBoxEx
from Users.Rights import (urAdmin, urCanChangePersonSubstitution)
from library.crbcombobox import CRBComboBox


class CPersonSubstitutionDialog(CDialogBase, Ui_PersonSubstitution):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.addModels('OrgStructure', COrgStructureModel(self, QtGui.qApp.currentOrgId()))
        self.addModels('Personnel',    CPersonnelModel(self))
        self.addModels('PersonnelSort', CSortFilterProxyTableModel(self, self.modelPersonnel))
        self.modelPersonnel = self.modelPersonnelSort.model()
        self.addModels('Periods', CSubstitutionPeriodsModel(self))
        self.addModels('PeriodsSort', CSubstitutionPeriodsSortFilterProxyTableModel(self, self.modelPeriods))
        self.modelPeriods = self.modelPeriodsSort.model()
        
        self.addObject('actAddPeriod', QtGui.QAction(u'Добавить период', self))

        self.addObject('actEditPeriod', QtGui.QAction(u'Изменить период', self))
        self.addObject('actDeletePeriod', QtGui.QAction(u'Удалить период', self))

        self.setupUi(self)
        self.splitter_2.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(1, 1)
        self.btnPrint.setShortcut('F6')
        self.cmbPost.setTable('rbPost')
        self.cmbSpeciality.setTable('rbSpeciality')
        self.edtBegDate.setDate(QDate(QDate.currentDate().year(), 1, 1))
        self.edtEndDate.setDate(QDate(QDate.currentDate().year(), 12, 31))

        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self.setModels(self.treeOrgStructure, self.modelOrgStructure, self.selectionModelOrgStructure)

        self.setModels(self.tblPersonnel, self.modelPersonnelSort, self.selectionModelPersonnelSort)
        self.tblPersonnel.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblPersonnel.createPopupMenu([self.actAddPeriod])
        self.tblPersonnel.setSelectionMode(self.tblPersonnel.SingleSelection)
        
        self.setModels(self.tblSubstitutionPeriods, self.modelPeriodsSort, self.selectionModelPeriodsSort)
        self.tblSubstitutionPeriods.createPopupMenu([self.actEditPeriod, self.actDeletePeriod])
        
        orgStructureIndex = self.modelOrgStructure.findItemId(QtGui.qApp.currentOrgStructureId())
        if orgStructureIndex and orgStructureIndex.isValid():
            self.treeOrgStructure.setCurrentIndex(orgStructureIndex)
            self.treeOrgStructure.setExpanded(orgStructureIndex, True)
        if not (QtGui.qApp.userHasRight(urAdmin) or QtGui.qApp.userHasRight(urCanChangePersonSubstitution)):
            self.actAddPeriod.setEnabled(False)
            self.actDeletePeriod.setEnabled(False)
            self.actEditPeriod.setEnabled(False)


    def exec_(self):
        result = CDialogBase.exec_(self)
        return result

    
    def getBegDate(self):
        return forceDate(self.edtBegDate.date())

    def getOrgStructureId(self):
        if self.activityListIsShown:
            return None
        else:
            treeIndex = self.treeOrgStructure.currentIndex()
            treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
            return treeItem.id() if treeItem else None


    def getOrgStructureIdList(self):
        treeIndex = self.treeOrgStructure.currentIndex()
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    def getCurrentPersonId(self):
        return self.tblPersonnel.currentItemId()


    def getSelectedPersonIdList(self):
        return self.tblPersonnel.selectedItemIdList()


    def invalidatePersonTable(self):
        self.modelPersonnel.invalidateRecordsCache()
        self.modelPersonnel.emitDataChanged()

    
    def updatePersonListForOrgStructure(self, posToId=None):
        date = self.getBegDate()
        orgStructureIdList = self.getOrgStructureIdList()
        self.modelPersonnel.loadData(orgStructureIdList)
        self.modelPeriods.loadData(self.modelPersonnel.getIdList())
        self.modelPeriodsSort.sort(0)
        

    def printPeriodsTable(self):
        items = []
        for row in range(self.modelPeriods.rowCount()):
            index = self.modelPeriods.index(row, 0)
            proxy_index = self.modelPeriodsSort.mapFromSource(index)
            if proxy_index.isValid():
                items.append(self.modelPeriods.getRecordByRow(row))
        if not items:
            return

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Периоды замещения')
        cursor.insertBlock()

        cursor.setCharFormat(CReportBase.ReportBody)
        treeIndex = self.treeOrgStructure.currentIndex()
        orgStructure  = treeIndex.internalPointer().name() if treeIndex.isValid() else None
        if orgStructure:
            cursor.insertText(u'Подразделение: ' + orgStructure +'\n')
        else:
            cursor.insertText(u'Подразделение: ЛПУ\n')
        cursor.insertText(u'На даты с {} по {}\n'.format(forceString(self.edtBegDate.date()), forceString(self.edtEndDate.date())))
        if self.chkOnlyActive.isChecked():
            cursor.insertText(u'Только активные на дату: {}'.format(forceString(QDate.currentDate())))
        cursor.insertBlock()

        tableColumns = [
            ('15%',  [ u'Код, ФИО отсутствующего'], CReportBase.AlignLeft),        # 0
            ('14%', [ u'Подразделение'], CReportBase.AlignLeft),  # 1
            ('9%',  [ u'Начало периода'], CReportBase.AlignLeft),      # 2
            ('9%',  [ u'Окончание периода'], CReportBase.AlignLeft),         # 3
            ('15%',  [ u'Код, ФИО замещающего'], CReportBase.AlignLeft),        # 4
            ('14%',  [ u'Подразделение'], CReportBase.AlignLeft),      # 5
            ('9%', [ u'Дата'], CReportBase.AlignLeft),      # 6
            ('15%',  [ u'Изменивший пользователь'], CReportBase.AlignLeft),         # 7
                       ]
        table = createTable(cursor, tableColumns)

        for item in items:
            i = table.addRow()
            table.setText(i, 0, forceString(item.value('codeAbsent')))
            table.setText(i, 1, forceString(item.value('orgStructureNameAbsent')))
            table.setText(i, 2, forceString(item.value('begDate')))
            table.setText(i, 3, forceString(item.value('endDate')))
            table.setText(i, 4, forceString(item.value('codeSubs')))
            table.setText(i, 5, forceString(item.value('orgStructureNameSubs')))
            table.setText(i, 6, forceString(item.value('modifyDatetime')))
            table.setText(i, 7, forceString(item.value('codeModify')))

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

        view = CReportViewDialog(self)
        view.setWindowTitle(u'Периоды замещения')
        view.setText(doc)
        view.exec_()

    
    def toggleDateFilter(self):
        if self.chkOnlyActive.isChecked():
            if self.edtBegDate.date() == QDate() == self.edtEndDate.date():
                self.modelPeriodsSort.setFilter('begDate', forceDate(QDate.currentDate()), CSortFilterProxyTableModel.MatchLessEqual)
                self.modelPeriodsSort.setFilter('endDate', forceDate(QDate.currentDate()), CSortFilterProxyTableModel.MatchGreaterEqual)
            elif self.edtBegDate.date() == QDate() and QDate.currentDate() <= self.edtEndDate.date():
                self.modelPeriodsSort.setFilter('begDate', forceDate(QDate.currentDate()), CSortFilterProxyTableModel.MatchLessEqual)
                self.modelPeriodsSort.setFilter('endDate', (forceDate(QDate.currentDate()), forceDate(self.edtEndDate.date())), CSortFilterProxyTableModel.MatchBetween)
            elif self.edtEndDate.date() == QDate() and QDate.currentDate() >= self.edtBegDate.date():
                self.modelPeriodsSort.setFilter('begDate', (forceDate(self.edtBegDate.date()),forceDate(QDate.currentDate())), CSortFilterProxyTableModel.MatchBetween)
                self.modelPeriodsSort.setFilter('endDate', forceDate(QDate.currentDate()), CSortFilterProxyTableModel.MatchGreaterEqual)
            elif QDate.currentDate() <= self.edtEndDate.date() and QDate.currentDate() >= self.edtBegDate.date():
                self.modelPeriodsSort.setFilter('begDate', (forceDate(self.edtBegDate.date()), forceDate(QDate.currentDate())), CSortFilterProxyTableModel.MatchBetween)
                self.modelPeriodsSort.setFilter('endDate', (forceDate(QDate.currentDate()), forceDate(self.edtEndDate.date())), CSortFilterProxyTableModel.MatchBetween)
            else:
                self.modelPeriodsSort.setFilter('begDate', None, CSortFilterProxyTableModel.MatchExactly)
                self.modelPeriodsSort.setFilter('endDate', None, CSortFilterProxyTableModel.MatchExactly)
        else:
            if self.edtBegDate.date() == QDate() == self.edtEndDate.date():
                self.modelPeriodsSort.removeFilter('begDate')
                self.modelPeriodsSort.removeFilter('endDate')  
            elif self.edtEndDate.date() == QDate():
                self.modelPeriodsSort.setFilter('begDate', forceDate(self.edtBegDate.date()), CSortFilterProxyTableModel.MatchGreaterEqual) 
                self.modelPeriodsSort.setFilter('endDate', forceDate(self.edtBegDate.date()), CSortFilterProxyTableModel.MatchGreaterEqual)
            elif self.edtBegDate.date() == QDate():
                self.modelPeriodsSort.setFilter('begDate', forceDate(self.edtEndDate.date()), CSortFilterProxyTableModel.MatchLessEqual) 
                self.modelPeriodsSort.setFilter('endDate', forceDate(self.edtEndDate.date()), CSortFilterProxyTableModel.MatchLessEqual)
            else:
                self.modelPeriodsSort.setFilter('begDate', (forceDate(self.edtBegDate.date()), forceDate(self.edtEndDate.date())), CSortFilterProxyTableModel.MatchBetween) 
                self.modelPeriodsSort.setFilter('endDate', (forceDate(self.edtBegDate.date()), forceDate(self.edtEndDate.date())), CSortFilterProxyTableModel.MatchBetween)
                


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelOrgStructure_currentChanged(self, current, previous):
        self.updatePersonListForOrgStructure()
    
    
    @pyqtSignature('bool')
    def on_chkSpeciality_toggled(self, checked):
        if not checked:
            self.modelPersonnelSort.removeFilter('Speciality_id')
        else:
            self.modelPersonnelSort.setFilter('Speciality_id', forceInt(self.cmbSpeciality.getValue()), CSortFilterProxyTableModel.MatchExactly)
        self.modelPeriodsSort.setFilter('absencesPerson_id', self.modelPersonnel.getIdList(), CSortFilterProxyTableModel.MatchInList)
            
    
    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        self.modelPersonnelSort.setFilter('Speciality_id', forceInt(self.cmbSpeciality.getValue()), CSortFilterProxyTableModel.MatchExactly)
        self.modelPeriodsSort.setFilter('absencesPerson_id', self.modelPersonnel.getIdList(), CSortFilterProxyTableModel.MatchInList)
        
    @pyqtSignature('bool')
    def on_chkPost_toggled(self, checked):
        if not checked:
            self.modelPersonnelSort.removeFilter('Post_id')
        else:
            self.modelPersonnelSort.setFilter('Post_id', forceInt(self.cmbPost.getValue()), CSortFilterProxyTableModel.MatchExactly)
        self.modelPeriodsSort.setFilter('absencesPerson_id', self.modelPersonnel.getIdList(), CSortFilterProxyTableModel.MatchInList)
           
            
    @pyqtSignature('int')
    def on_cmbPost_currentIndexChanged(self, index):
        self.modelPersonnelSort.setFilter('Post_id', forceInt(self.cmbPost.getValue()), CSortFilterProxyTableModel.MatchExactly)
        self.modelPeriodsSort.setFilter('absencesPerson_id', self.modelPersonnel.getIdList(), CSortFilterProxyTableModel.MatchInList)
    
    
    @pyqtSignature('bool')
    def on_chkFIO_toggled(self, checked):
        if not checked:
            self.modelPersonnelSort.removeFilter('FIO')
        else:
            self.modelPersonnelSort.setFilter('FIO', forceString(self.edtFIO.text()), CSortFilterProxyTableModel.MatchContains)
        self.modelPeriodsSort.setFilter('absencesPerson_id', self.modelPersonnel.getIdList(), CSortFilterProxyTableModel.MatchInList)
            
            
    @pyqtSignature('QString')
    def on_edtFIO_textChanged(self, text):
        self.modelPersonnelSort.setFilter('FIO', forceString(self.edtFIO.text()), CSortFilterProxyTableModel.MatchContains)
        self.modelPeriodsSort.setFilter('absencesPerson_id', self.modelPersonnel.getIdList(), CSortFilterProxyTableModel.MatchInList)
    
    
    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.toggleDateFilter()
    
    
    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.toggleDateFilter()
    
    
    @pyqtSignature('bool')
    def on_chkOnlyActive_toggled(self, checked):
        self.toggleDateFilter()


    @pyqtSignature('')
    def on_actAddPeriod_triggered(self):
        dialog = CPeriodDialog(True)
        data = {
            'begDate': QDate.currentDate(),
            'endDate': QDate.currentDate(),
            'person_id': None,
            'record': None,
            'absencePerson': forceInt(self.modelPersonnelSort.getRecordByRow(self.tblPersonnel.selectedIndexes()[0].row()).value('id')),
        }
        dialog.loadData(data)
        if dialog.exec_() == QtGui.QDialog.Accepted:
            self.modelPeriods.loadData(self.modelPersonnel.getIdList())
    
    
    @pyqtSignature('')
    def on_actEditPeriod_triggered(self):
        res = QtGui.QMessageBox.warning(self, u'Внимание!',
                    u'При удалении/изменении периода замещения сотрудника проверьте наличие причины отсутствия в Учете рабочего времени на эти дни!')
        dialog = CPeriodDialog(False)
        record = self.modelPeriodsSort.getRecordByRow(self.tblSubstitutionPeriods.selectedIndexes()[0].row())
        
        data = {
            'begDate': forceDate(record.value('begDate')),
            'endDate': forceDate(record.value('endDate')),
            'person_id': forceInt(record.value('substitutionPerson_id')),
            'record': record,
            'absencePerson': forceInt(record.value('absencesPerson_id')),
        }
        dialog.loadData(data)
        if dialog.exec_() == QtGui.QDialog.Accepted:
            self.modelPeriods.loadData(self.modelPersonnel.getIdList())
            
    
    
    @pyqtSignature('')
    def on_actDeletePeriod_triggered(self):
        res = QtGui.QMessageBox.warning(self, u'Внимание!',
                    u'При удалении/изменении периода замещения сотрудника проверьте наличие причины отсутствия в Учете рабочего времени на эти дни!')
        db = QtGui.qApp.db
        table = db.table(u'soc_PersonSubstitution')
        record = self.modelPeriodsSort.getRecordByRow(self.tblSubstitutionPeriods.selectedIndexes()[0].row())
        db.markRecordsDeleted(table, where="id = {}".format(forceString(record.value('id'))))
        self.modelPeriods.loadData(self.modelPersonnel.getIdList())


    def on_btnFilterReset_clicked(self):  
        self.edtFIO.setText('')
        self.cmbPost.setCurrentIndex(-1)
        self.cmbSpeciality.setCurrentIndex(-1)
        self.edtBegDate.setDate(QDate(QDate.currentDate().year(), 1, 1))
        self.edtEndDate.setDate(QDate(QDate.currentDate().year(), 12, 31))
        
        self.chkFIO.setChecked(False)
        self.chkPost.setChecked(False)
        self.chkSpeciality.setChecked(False)
        self.chkOnlyActive.setChecked(True)
       
        
    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        self.printPeriodsTable()


class CPersonnelModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.items = []
        self.parentWidget = parent
        self.addCol(CTextInDocTableCol(u'Код', 'code', 6).setReadOnly())
        self.addCol(CTextInDocTableCol(u'Фамилия', 'lastName', 20).setReadOnly())
        self.addCol(CTextInDocTableCol(u'Имя', 'firstName', 20).setReadOnly())
        self.addCol(CTextInDocTableCol(u'Отчество', 'patrName', 20).setReadOnly())
        self.addCol(CTextInDocTableCol(u'Подразделение', 'orgStructureName', 5).setReadOnly())
        self.addCol(CRBInDocTableCol(u'Должность', 'post_id', 10, 'rbPost').setReadOnly())
        self.addCol(CRBInDocTableCol(u'Специальность', 'speciality_id', 10, 'rbSpeciality').setReadOnly())
        self.addHiddenCol(CTextInDocTableCol(u'ФИО', 'FIO', 6).setReadOnly())
    
    
    def loadData(self, orgStructureIdList):
        if orgStructureIdList:
            db = QtGui.qApp.db
            table = db.table('Person')
            tableOS = db.table('OrgStructure')
            queryTable = table
            queryTable = queryTable.leftJoin(tableOS, db.joinAnd([tableOS['id'].eq(table['orgStructure_id']), tableOS['deleted'].eq(0)]))
            cond = [ table['deleted'].eq(0),
                     table['retired'].eq(0),
                     table['speciality_id'].isNotNull(),
                     table['post_id'].isNotNull(),
                     table['orgStructure_id'].inlist(orgStructureIdList),
                   ]
            curOrder = self.parentWidget.tblPersonnel.order()
            if not curOrder:
                curOrder='lastName, firstName, patrName'
            else:
                if u'rbPost.name' in curOrder:
                    tableRBPost = db.table('rbPost')
                    queryTable = queryTable.leftJoin(tableRBPost, tableRBPost['id'].eq(table['post_id']))
                if u'rbSpeciality.name' in curOrder:
                    tableRBSpeciality = db.table('rbSpeciality')
                    queryTable = queryTable.leftJoin(tableRBSpeciality, tableRBSpeciality['id'].eq(table['speciality_id']))
            items = db.getRecordList(queryTable, 
                                    [table['id'],
                                    table['code'],
                                    table['lastName'],
                                    table['firstName'],
                                    table['patrName'],
                                    table['orgStructure_id'],
                                    table['post_id'],
                                    table['speciality_id'],
                                    'concat_ws(\' \', Person.lastName, Person.firstName, Person.patrName) as FIO',
                                    tableOS['name'].alias('orgStructureName')
                                    ], 
                                    where=cond, 
                                    order=curOrder)
            self.setItems(items)
        else:
            self.clearItems()
    
    
    def getIdList(self):
        idlist = []
        for row in xrange(self.rowCount()):
            record = self.getRecordByRow(row)
            id = forceRef(record.value('id'))
            proxyIndex = self.index(row, 0)
            data = self.parentWidget.modelPersonnelSort.mapFromSource(proxyIndex).isValid()
            if id and id not in idlist and data:
                idlist.append(id)
        return idlist


class CSubstitutionPeriodsModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.items = []
        self.parentWidget = parent
        self.addCol(CTextInDocTableCol(u'Код, ФИО отсутствующего', 'codeAbsent', 6).setReadOnly())
        self.addCol(CTextInDocTableCol(u'Подразделение', 'orgStructureNameAbsent', 5).setReadOnly())
        self.addCol(CDateInDocTableCol(u'Начало периода', 'begDate', 6).setReadOnly())
        self.addCol(CDateInDocTableCol(u'Окончание периода', 'endDate', 6).setReadOnly())
        self.addCol(CTextInDocTableCol(u'Код, ФИО замещающего', 'codeSubs', 6).setReadOnly())
        self.addCol(CTextInDocTableCol(u'Подразделение', 'orgStructureNameSubs', 5).setReadOnly())
        self.addCol(CDateInDocTableCol(u'Дата', 'modifyDatetime', 6).setReadOnly())
        self.addCol(CTextInDocTableCol(u'Изменивший пользователь', 'codeModify', 5).setReadOnly())
        self.addHiddenCol(CTextInDocTableCol(u'ИД отсутствуещего', 'absencesPerson_id', 6).setReadOnly())
    
    
    def loadData(self, personIdList):
        if personIdList:
            db = QtGui.qApp.db
            table = db.table('soc_PersonSubstitution')
            tableAbsentPerson = db.table('Person').alias('absentPerson')
            tableSubstitutePerson = db.table('Person').alias('substPerson')
            tableAbsentOS = db.table('OrgStructure').alias('absentOrg')
            tableSubstituteOS = db.table('OrgStructure').alias('substOrg')
            tableModifyPerson = db.table('Person').alias('modifyPerson')
            tableAbsentPost = db.table('rbPost').alias('absentPost')
            tableAbsentPI = db.table('rbPost_Identification').alias('absentPI')
            tableAbsentAS = db.table('rbAccountingSystem').alias('absentAS')
            tableSubstitutePost = db.table('rbPost').alias('substPost')
            tableSubstitutePI = db.table('rbPost_Identification').alias('substPI')
            tableSubstituteAS = db.table('rbAccountingSystem').alias('substAS')
            queryTable = table
            queryTable = queryTable.leftJoin(tableAbsentPerson, tableAbsentPerson['id'].eq(table['absencesPerson_id']))
            queryTable = queryTable.leftJoin(tableAbsentOS, tableAbsentOS['id'].eq(tableAbsentPerson['orgStructure_id']))
            queryTable = queryTable.leftJoin(tableSubstitutePerson, tableSubstitutePerson['id'].eq(table['substitutionPerson_id']))
            queryTable = queryTable.leftJoin(tableSubstituteOS, tableSubstituteOS['id'].eq(tableSubstitutePerson['orgStructure_id']))
            queryTable = queryTable.leftJoin(tableModifyPerson, tableModifyPerson['id'].eq(table['modifyPerson_id']))
            queryTable = queryTable.leftJoin(tableAbsentPost, tableAbsentPost['id'].eq(tableAbsentPerson['post_id']))
            queryTable = queryTable.leftJoin(tableAbsentPI, tableAbsentPI['master_id'].eq(tableAbsentPost['id']))
            queryTable = queryTable.leftJoin(tableAbsentAS, tableAbsentAS['id'].eq(tableAbsentPI['system_id']))
            queryTable = queryTable.leftJoin(tableSubstitutePost, tableSubstitutePost['id'].eq(tableSubstitutePerson['post_id']))
            queryTable = queryTable.leftJoin(tableSubstitutePI, tableSubstitutePI['master_id'].eq(tableSubstitutePost['id']))
            queryTable = queryTable.leftJoin(tableSubstituteAS, tableSubstituteAS['id'].eq(tableSubstitutePI['system_id']))
            cond = [ table['deleted'].eq(0),
                    table['absencesPerson_id'].inlist(personIdList),
                    db.joinOr([tableAbsentAS['urn'].eq('urn:oid:1.2.643.5.1.13.13.11.1002'), tableAbsentPI['system_id'].isNull()]),
                    db.joinOr([tableSubstituteAS['urn'].eq('urn:oid:1.2.643.5.1.13.13.11.1002'), tableSubstitutePI['system_id'].isNull()]),
                   ]

            items = db.getDistinctRecordList(queryTable, 
                                    [
                                     'concat_ws(\' \', absentPerson.code, "|", absentPerson.lastName, absentPerson.firstName, absentPerson.patrName) as codeAbsent',
                                     tableAbsentOS['name'].alias('orgStructureNameAbsent'),
                                     'CAST(soc_PersonSubstitution.begDate as DATE) as begDate',
                                     'CAST(soc_PersonSubstitution.endDate as DATE) as endDate',
                                     'concat_ws(\' \', substPerson.code, "|", substPerson.lastName, substPerson.firstName, substPerson.patrName) as codeSubs',
                                     tableSubstituteOS['name'].alias('orgStructureNameSubs'),
                                     table['modifyDatetime'],
                                     'concat_ws(\' \', modifyPerson.code, modifyPerson.lastName, modifyPerson.firstName, modifyPerson.patrName) as codeModify',
                                     table['absencesPerson_id'],
                                     table['substitutionPerson_id'],
                                     tableAbsentPI['value'].alias('absentPost'),
                                     tableSubstitutePI['value'].alias('substPost'),
                                     tableAbsentPI['system_id'].alias('absentSys'),
                                     tableSubstitutePI['system_id'].alias('substSys'),
                                     table['id'],
                                    ], 
                                    where=cond)
            self.setItems(items)
        else:
            self.clearItems()
    
    
    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        item = self._items[row]
        if role == Qt.BackgroundColorRole:
            absentPost = forceString(item.value('absentPost'))
            substPost = forceString(item.value('substPost'))
            absentSys = forceString(item.value('absentSys'))
            substSys = forceString(item.value('substSys'))
            if absentSys and substSys and absentPost==substPost and (absentPost in ('59', '110', '49')):
                return toVariant(QtGui.QColor(Qt.green))
        elif role == Qt.ToolTipRole:
            absentPost = forceString(item.value('absentPost'))
            substPost = forceString(item.value('substPost'))
            absentSys = forceString(item.value('absentSys'))
            substSys = forceString(item.value('substSys'))
            if absentSys and substSys and absentPost==substPost and (absentPost in ('59', '110', '49')):
                return toVariant(u'''Для сотрудников с должностями: врач-педиатр участковый, врач-терапевт участковый, врач общей практики (семейный врач), 
на время их отсутствия в сервис записи будет выгружено расписание замещающего их сотрудника, имеющего аналогичную должность''')
        elif role != Qt.DisplayRole:
            return QVariant()
        return item.value(index.column())


class CPeriodDialog(QtGui.QDialog):
    def __init__(self, fromService=False, parent=None):
        super(CPeriodDialog, self).__init__(parent)
        self.record = None
        self.absencePerson = None
        
        self.begDate = CDateEdit(self)
        self.endDate = CDateEdit(self)

        self.cmbPerson = CPersonComboBoxEx(self)
        
        lblBegDate = QtGui.QLabel(u'Дата начала периода', self)
        lblEndDate = QtGui.QLabel(u'Дата окончания периода', self)
        lblPerson = QtGui.QLabel(u'Замещающий сотрудник', self)
        
        self.applyButton = QtGui.QPushButton(u'Принять', self)
        self.rejectButton = QtGui.QPushButton(u'Отмена', self)
        
        layout = QtGui.QGridLayout(self)
        layout.addWidget(lblBegDate, 0, 0)
        layout.addWidget(self.begDate, 0, 1)
        layout.addWidget(lblEndDate, 1, 0)
        layout.addWidget(self.endDate, 1, 1)
        layout.addWidget(lblPerson, 2, 0)
        layout.addWidget(self.cmbPerson, 2, 1)
        
        if fromService:
            self.cmbReasonOfAbsence = CRBComboBox(self)
            self.cmbReasonOfAbsence.setTable('rbReasonOfAbsence')
            self.cmbReasonOfAbsence.setEnabled(False)
            self.lblReasonOfAbsence = QtGui.QLabel(u'Причина отсутствия', self)
            self.lblReasonOfAbsence.setEnabled(False)
            self.chkAddReasonOfAbsence = QtGui.QCheckBox(u'Проставить причину отсутствия в учете рабочего времени', self)
            layout.addWidget(self.chkAddReasonOfAbsence, 3, 0, 1, 0)
            layout.addWidget(self.lblReasonOfAbsence, 4, 0)
            layout.addWidget(self.cmbReasonOfAbsence, 4, 1)
            layout.addWidget(self.applyButton, 5, 0)
            layout.addWidget(self.rejectButton, 5, 1)
            self.chkAddReasonOfAbsence.stateChanged.connect(self.toggleCmbReasonOfAbsence)
        else:
            self.chkAddReasonOfAbsence = None
            layout.addWidget(self.applyButton, 3, 0)
            layout.addWidget(self.rejectButton, 3, 1)

        self.applyButton.clicked.connect(self.save)
        self.rejectButton.clicked.connect(self.cancel)

        self.setWindowTitle(u'Редактирование периода')
        self.resize(600, 100)
    
    
    def toggleCmbReasonOfAbsence(self, state):
        self.cmbReasonOfAbsence.setEnabled(state)
        self.lblReasonOfAbsence.setEnabled(state)
    
    def loadData(self, data):
        self.begDate.setDate(data['begDate'])
        self.endDate.setDate(data['endDate'])
        self.cmbPerson.setValue(data['person_id'])
        self.record = data['record']
        self.absencePerson = data['absencePerson']
    
    
    def checkDates(self):
        if not self.begDate.date().isValid():
            QtGui.QMessageBox.warning(self, u'Ошибка при сохранении',
                        u'Дата начала некорректна')
            return False
        if not self.endDate.date().isValid():
            QtGui.QMessageBox.warning(self, u'Ошибка при сохранении',
                        u'Дата окончания некорректна')
            return False
        if self.begDate.date() > self.endDate.date():
            QtGui.QMessageBox.warning(self, u'Ошибка при сохранении',
                        u'Дата начала не может быть больше даты окончания периода')
            return False
        db = QtGui.qApp.db
        table = db.table(u'soc_PersonSubstitution')
        cond = """absencesPerson_id = {2} AND
            deleted = 0 AND
            (id <> {3} AND
            (({0} <= begDate and {1} >= begDate) 
            or ({0} >= begDate and {0} <= endDate)))""".format(db.formatDate(self.begDate.date()), 
                                                               db.formatDate(self.endDate.date()), 
                                                               self.absencePerson,
                                                               forceString(self.record.value('id')) if self.record else '0')
        record = db.getRecordEx(table, cols="*", where=cond)
        if record:
            QtGui.QMessageBox.warning(self, u'Ошибка при сохранении',
                        u'Новый период пересекается с существующим периодом с {} по {}'.format(forceString(record.value('begDate')), forceString(record.value('endDate'))))
            return False
        return True
    
    def checkPerson(self):
        if not self.cmbPerson.value():
            QtGui.QMessageBox.warning(self, u'Ошибка при сохранении',
                        u'Укажите замещающего сотрудника!')
            return False
        else:
            return True
        
    def checkReason(self):
        if self.chkAddReasonOfAbsence and self.chkAddReasonOfAbsence.isChecked():
            if not self.cmbReasonOfAbsence.getValue():
                QtGui.QMessageBox.warning(self, u'Ошибка при сохранении',
                        u'Укажите причину отсутствия!')
                return False
            return True
        else:
            return True
        
    def save(self):
        if self.checkDates() and self.checkPerson() and self.checkReason():
            db = QtGui.qApp.db
            table = db.table(u'soc_PersonSubstitution')
            if not self.record:
                self.record = table.newRecord()
                self.record.setValue('createDatetime', QDate.currentDate())
                self.record.setValue('createPerson_id',  QtGui.qApp.userId)
            else:
                rec = table.newRecord()
                rec.setValue('id', self.record.value('id'))
                self.record = rec
            self.record.setValue('modifyDatetime', QDate.currentDate())
            self.record.setValue('modifyPerson_id', QtGui.qApp.userId)
            self.record.setValue('absencesPerson_id', forceString(self.absencePerson))
            self.record.setValue('begDate', forceDate(self.begDate.date()))
            self.record.setValue('endDate', forceDate(self.endDate.date()))
            self.record.setValue('substitutionPerson_Id', forceString(self.cmbPerson.getValue()))
            db.insertOrUpdate(table, self.record)
            if self.chkAddReasonOfAbsence and self.chkAddReasonOfAbsence.isChecked():
                startDate = self.begDate.date()
                while startDate <= self.endDate.date():
                    query = db.query('SELECT id FROM Schedule WHERE date = {} and person_id = {} and deleted=0'.format(db.formatDate(startDate), forceString(self.absencePerson)))
                    if query.next():
                        id = forceString(query.value(0))
                        newQuery = db.query('UPDATE Schedule SET reasonOfAbsence_id = {} WHERE id = {} and deleted=0'.format(self.cmbReasonOfAbsence.getValue(), id))
                    else:
                        newQuery = db.query('''
                        INSERT INTO Schedule (createDatetime, createPerson_id, modifyDatetime, modifyPerson_id, person_id, appointmentType, date, begTime, endTime, reasonOfAbsence_id)
                        VALUES ({}, {}, {}, {}, {}, {}, {}, "{}", "{}", {})
                                            '''.format(
                                                db.formatDate(QDateTime.currentDateTime()),
                                                QtGui.qApp.userId,
                                                db.formatDate(QDateTime.currentDateTime()),
                                                QtGui.qApp.userId,
                                                forceString(self.absencePerson),
                                                '0',
                                                db.formatDate(startDate),
                                                '00:00:00',
                                                '00:00:00',
                                                self.cmbReasonOfAbsence.getValue(),
                                            ))
                    startDate = startDate.addDays(1) 
            self.accept()
    
    def cancel(self):
        self.reject()


class CSubstitutionPeriodsSortFilterProxyTableModel(CSortFilterProxyTableModel):
    def naturalSortKey(self, s):
        import re
        if not isinstance(s, unicode):
            s = str(s)
        return [int(text) if text.isdigit() else text.lower() for text in re.split('(\d+)', s)]
    
    def sort(self, column, order=Qt.AscendingOrder):
        import re
        model = self.model()
        col = model._cols[column]
        if column in (0, 4):
            model._items.sort(key=lambda item: self.naturalSortKey(re.sub(r'^[^.*?\|]+', '', col.toSortString(item.value(col.fieldName()), item))), reverse=(order==Qt.DescendingOrder))
        else:
            model._items.sort(key=lambda item: self.naturalSortKey(col.toSortString(item.value(col.fieldName()), item)), reverse=(order==Qt.DescendingOrder))
        self.invalidate()
        model.emitRowsChanged(0, len(model._items) - 1)
    