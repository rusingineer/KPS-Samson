# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, pyqtSignature, Qt, QVariant, SIGNAL, QDateTime, QModelIndex

from library.ClientRecordProperties import CRecordProperties
from library.crbcombobox import CRBComboBox
from library.database import CDatabaseException
from library.DialogBase import CDialogBase
from library.InDocTable import CInDocTableModel, CIntInDocTableCol, CRBInDocTableCol, CDateInDocTableCol, \
    CInDocTableCol, CLocItemDelegate, CEnumInDocTableCol
from library.SortFilterProxyTableModel import CSortFilterProxyTableModel
from library.Utils import toVariant, getOrgStructureIdList, forceRef, forceString, trim, copyFields, forceInt
from Users.Rights import urPlanningHospitalBedProfileGen

from OrgStructureCol import COrgStructureInDocTableCol

from Ui_PlanningHospitalBedProfile import Ui_PlanningHospitalBedProfileDialog


class COrgStructurePlanningHospitalBedProfile(CInDocTableModel):

    class CLocProfileInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.profileCache = {}
            self.showFieldName = params['showFieldName']

        def toString(self, val, record):
            profileId = forceRef(val)
            if profileId:
                profileRecord = self.profileCache.get(profileId)
                if not profileRecord:
                    profileRecord = QtGui.qApp.db.getRecord('rbHospitalBedProfile', self.showFieldName, profileId)
                    self.profileCache[profileId] = profileRecord
                value = forceString(profileRecord.value(self.showFieldName))
                return toVariant(value)
            return val

    class CLocBookkeeperCodeInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.orgStructureCache = {}

        def toString(self, val, record):
            orgStructureId = forceRef(val)
            if orgStructureId:
                bookkeeperCode = self.orgStructureCache.get(orgStructureId, '')
                if not bookkeeperCode:
                    tmpOrgStructureId = orgStructureId
                    # ищем омс код подразделения к которому прикреплен человек
                    while not trim(bookkeeperCode) and len(trim(bookkeeperCode)) != 5 and tmpOrgStructureId:
                        tmpOrgStructureId = forceRef(
                            QtGui.qApp.db.translate('OrgStructure', 'id', tmpOrgStructureId, 'parent_id'))
                        bookkeeperCode = forceString(
                            QtGui.qApp.db.translate('OrgStructure', 'id', tmpOrgStructureId, 'bookkeeperCode'))
                    self.orgStructureCache[orgStructureId] = trim(bookkeeperCode)
                return toVariant(trim(bookkeeperCode))
            return val

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'OrgStructure_PlanningHospitalBedProfile', 'id', 'master_id', parent)
        self.addExtCol(self.CLocBookkeeperCodeInDocTableCol(u'ОМС код', 'master_id', 20), QVariant.String).setReadOnly()
        self.addCol(CDateInDocTableCol(u'Дата создания', 'createDatetime',6,canBeEmpty=False))
        self.addCol(COrgStructureInDocTableCol(u'Подразделение', 'master_id', 20, addNone=False))
        self.addCol(
            CRBInDocTableCol(u'Профиль', 'profile_id', 20, 'rbHospitalBedProfile', showFields=CRBComboBox.showName))
        self.addExtCol(
            self.CLocProfileInDocTableCol(u'Региональный код профиля', 'profile_id', 20, showFieldName='regionalCode'),
            QVariant.String).setReadOnly()
        self.addExtCol(self.CLocProfileInDocTableCol(u'ЕГИСЗ код профиля', 'profile_id', 20, showFieldName='usishCode'),
                       QVariant.String).setReadOnly()
        self.addCol(CEnumInDocTableCol(u'Режим койки', 'regime', 20, [u'круглосуточные', u'дневные']))
        self.addCol(CDateInDocTableCol(u'Дата', 'date', 6, canBeEmpty=False))
        self.addCol(CIntInDocTableCol(u'Мужские', 'adultMan', 5, high=1000).setToolTip(u'Cвободных коек мужчины'))
        self.addCol(CIntInDocTableCol(u'Женские', 'adultWoman', 5, high=1000).setToolTip(u'Cвободных коек женщины'))
        self.addCol(CIntInDocTableCol(u'Детские', 'children', 5, high=1000).setToolTip(u'Cвободных коек дети'))

        self.dirtyRows = []
        self.deletedRowsId = []
        self.setEnableAppendLine(True)
        self.mapOrgStructureToHBP = {}

    def createEditor(self, index, parent):
        column = index.column()
        row = index.row()
        model = index.model()
        editor = self._cols[column].createEditor(parent)
        if type(editor).__name__ == 'CRBComboBox' and row < len(model.items()):
            db = QtGui.qApp.db
            tableHBP = db.table('rbHospitalBedProfile')
            profList = self.getProfileListForOrgStructure(self.items()[row].value('master_id'))
            editor.setFilter(tableHBP['id'].inlist(profList))
        return editor

    def getProfileListForOrgStructure(self, orgStructureId):
        profileList = self.mapOrgStructureToHBP.get(orgStructureId, None)
        if profileList is None:
            db = QtGui.qApp.db
            tableOSHB = db.table('OrgStructure_HospitalBed')
            tableHBP = db.table('rbHospitalBedProfile')
            table = tableOSHB.leftJoin(tableHBP, tableOSHB['profile_id'].eq(tableHBP['id']))
            cond = [tableHBP['id'].isNotNull(), tableOSHB['master_id'].eq(orgStructureId)]
            profileList = db.getDistinctIdList(table, idCol=['rbHospitalBedProfile.id'], where=cond)
            self.mapOrgStructureToHBP[orgStructureId] = profileList
        return profileList

    def load(self, params):
        cond = []
        db = QtGui.qApp.db
        table = db.table('OrgStructure_PlanningHospitalBedProfile')
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if begDate:
            cond.append(table['date'].ge(begDate))
        if endDate:
            cond.append(table['date'].le(endDate))
        cond.append(table['deleted'].eq(0))
        recordList = db.getRecordList(table, '*', where=cond, order='master_id, profile_id, date')
        self.setItems(recordList)

    def setData(self, index, value, role=Qt.EditRole):
        if CInDocTableModel.setData(self, index, value, role):
            record = self._items[index.row()]
            if record not in self.dirtyRows:
                self.dirtyRows.append(record)
            return True
        return False

    def getEmptyRecord(self):
        record = CInDocTableModel.getEmptyRecord(self)
        record.setValue('date', QDate().currentDate())
        record.setValue('adultMan', QVariant(0))
        record.setValue('adultWoman', QVariant(0))
        record.setValue('children', QVariant(0))
        return record

    def saveData(self):
        try:
            db = QtGui.qApp.db
            table = self._table
            idFieldName = self._idFieldName
            if self.dirtyRows:
                for record in self.dirtyRows:
                    if self._extColsPresent:
                        outRecord = self.removeExtCols(record)
                    else:
                        outRecord = record
                    idRecord = db.insertOrUpdate(table, outRecord)
                    record.setValue(idFieldName, toVariant(idRecord))
            if self.deletedRowsId:
                filterRecord = [table[idFieldName].inlist(self.deletedRowsId)]
                db.markRecordsDeleted(table, filterRecord)
        except CDatabaseException:
            return False
        return True

    def removeRow(self, row, parentIndex=QModelIndex(), *args, **kwargs):
        if 0 <= row < len(self._items):
            record = self._items[row]
            self.deletedRowsId.append(forceRef(record.value(self._idFieldName)))
            if record in self.dirtyRows:
                self.dirtyRows.remove(record)
            CInDocTableModel.removeRow(self, row)

    def getRecordByRow(self, row):
        record = None
        if 0 <= row < len(self._items):
            record = self._items[row]
        return record

    def addRecord(self, record):
        self.insertRecord(len(self._items), record)
        self.dirtyRows.append(record)


class CLocItemDelegateProxy(CLocItemDelegate):

    def __init__(self, parent):
        CLocItemDelegate.__init__(self, parent)
        self.rowcount = 0

    def createEditor(self, parent, option, index):
        editor = index.model().sourceModel().createEditor(index.model().mapToSource(index), parent)
        self.connect(editor, SIGNAL('commit()'), self.emitCommitData)
        self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)

        self.editor = editor
        self.row = index.row()
        self.rowcount = index.model().sourceModel().rowCount(None)
        self.column = index.column()
        return editor

    def setEditorData(self, editor, index):
        if editor is not None:
            column = index.column()
            row = index.row()

            model = index.model().sourceModel()
            sourceRow = index.model().mapToSource(index).row()
            if sourceRow < len(model.items()):
                record = model.items()[sourceRow]
            else:
                record = model.table.newRecord()
            model.setEditorData(column, editor, model.data(index.model().mapToSource(index), Qt.EditRole), record)

    def setModelData(self, editor, model, index):
        if editor is not None:
            column = index.column()
            model.setData(index, index.model().sourceModel().getEditorData(column, editor))

    def updateEditorGeometry(self, editor, option, index):
        QtGui.QItemDelegate.updateEditorGeometry(self, editor, option, index)
        index.model().sourceModel().afterUpdateEditorGeometry(editor, index)


class CPlanningHospitalBedProfileProxy(CSortFilterProxyTableModel):
    def __init__(self, parent, sourceModel):
        CSortFilterProxyTableModel.__init__(self, parent, sourceModel)

    def __getattr__(self, name):
        return getattr(self.sourceModel(), name)


class CPlanningHospitalBedProfileDialog(CDialogBase, Ui_PlanningHospitalBedProfileDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.btnFill.setEnabled(QtGui.qApp.userHasRight(urPlanningHospitalBedProfileGen))
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.addModels('', COrgStructurePlanningHospitalBedProfile(parent))
        self.addModels('Proxy', CPlanningHospitalBedProfileProxy(self, self.model))
        self.model = self.modelProxy.sourceModel()
        self.setModels(self.tblItems, self.modelProxy, self.selectionModelProxy)
        self.tblItems.enableColsMove()
        self.addPopupDelRow()
        self.addPopupDuplicateSelectRows()
        self.addPopupRecordProperties()
        self.cmbHospitalBedProfile.setTable('rbHospitalBedProfile', addNone=True, order='code')
        self.cmbHospitalBedProfile.setShowFields(CRBComboBox.showCodeAndName)
        orgStructureId = QtGui.qApp.currentOrgStructureId()
        if orgStructureId:
            self.chkOrgStructure.setChecked(True)
            self.cmbOrgStructure.setValue(orgStructureId)
        currentDate = QDate().currentDate()
        self.edtBegDate.setDate(currentDate)
        self.edtEndDate.setDate(currentDate.addDays(9))
        params = {'begDate': QDate().currentDate().addMonths(-1)}
        self.model.load(params)
        self.tblItems.setItemDelegate(CLocItemDelegateProxy(self))
        self.onFilterUpdate()

    def addPopupDelRow(self):
        if self.tblItems._popupMenu is None:
            self.tblItems.createPopupMenu()
        self.tblItems.__actDeleteRows = QtGui.QAction(u'Удалить строку', self)
        self.tblItems.__actDeleteRows.setObjectName('actDeleteRows')
        self.tblItems._popupMenu.addAction(self.tblItems.__actDeleteRows)
        self.tblItems.connect(self.tblItems.__actDeleteRows, SIGNAL('triggered()'), self.on_deleteRows)

    def addPopupDuplicateSelectRows(self):
        if self.tblItems._popupMenu is None:
            self.tblItems.createPopupMenu()
        self.tblItems.__actDuplicateSelectRows = QtGui.QAction(u'Дублировать выделенные строки', self)
        self.tblItems.__actDuplicateSelectRows.setObjectName('actDuplicateSelectRows')
        self.tblItems._popupMenu.addAction(self.tblItems.__actDuplicateSelectRows)
        self.tblItems.connect(self.tblItems.__actDuplicateSelectRows, SIGNAL('triggered()'), self.on_duplicateSelectRows)

    def addPopupRecordProperties(self):
        if self.tblItems._popupMenu is None:
            self.tblItems.createPopupMenu()
        self.tblItems.__actRecordProperties = QtGui.QAction(u'Свойства записи', self)
        self.tblItems.__actRecordProperties.setObjectName('actRecordProperties')
        self.tblItems._popupMenu.addAction(self.tblItems.__actRecordProperties)
        self.tblItems.connect(self.tblItems.__actRecordProperties, SIGNAL('triggered()'), self.showRecordProperties)

    def on_deleteRows(self):
        selectIndexes = self.tblItems.selectedIndexes()
        for selectIndex in selectIndexes:
            sourceRow = self.tblItems.model().mapToSource(selectIndex).row()
            self.tblItems.model().sourceModel().removeRow(sourceRow)

    def on_duplicateSelectRows(self):
        currentRow = self.tblItems.currentIndex().row()
        items = self.tblItems.model().sourceModel().items()

        if currentRow < len(items):
            selectIndexes = self.tblItems.selectedIndexes()
            selectRowList = []
            for selectIndex in selectIndexes:
                selectRow = selectIndex.row()
                if selectRow not in selectRowList:
                    selectRowList.append(selectRow)
            selectRowList.sort()
            for row in selectRowList:
                newRecord = self.tblItems.model().sourceModel().getEmptyRecord()
                index = self.tblItems.model().index(row, 0)
                sourceRow = self.tblItems.model().mapToSource(index).row()
                copyFields(newRecord, items[sourceRow])
                newRecord.setValue(self.tblItems.model().sourceModel()._idFieldName, toVariant(None))
                items.append(newRecord)
            self.tblItems.model().sourceModel().reset()

    def showRecordProperties(self):
        sourceRow = self.tblItems.model().mapToSource(self.tblItems.currentIndex()).row()
        items = self.tblItems.model().sourceModel().items()
        if sourceRow < len(items):
            itemId = forceRef(items[sourceRow].value('id'))
        else:
            return
        table = self.tblItems.model().sourceModel().table
        CRecordProperties(self, table, itemId).exec_()

    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            if self.saveData():
                buttons = QtGui.QMessageBox.Ok
                messageBox = QtGui.QMessageBox()
                messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
                messageBox.setWindowTitle(u'Внимание!')
                messageBox.setText(u'Данные сохранены')
                messageBox.setStandardButtons(buttons)
                messageBox.setDefaultButton(QtGui.QMessageBox.Ok)
                return messageBox.exec_()

    def saveData(self):
        result = self.model.saveData()
        if not result:
            messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Critical,
                                           u'Внимание!',
                                           u'Ошибка при сохранении.',
                                           QtGui.QMessageBox.Ok)
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            messageBox.exec_()
        return result

    def onFilterUpdate(self):
        if self.chkDate.isChecked():
            self.modelProxy.setFilter('date', (QDateTime(self.edtBegDate.date()), QDateTime(self.edtEndDate.date())),
                                      CSortFilterProxyTableModel.MatchBetween)
        else:
            self.modelProxy.removeFilter('date')

        if self.chkDateCreate.isChecked():
            self.modelProxy.setFilter('createDatetime', (QDateTime(self.edtBegDateCreate.date()),QDateTime(self.edtEndDateCreate.date())),
                                      CSortFilterProxyTableModel.MatchBetween)
        else:
            self.modelProxy.removeFilter('createDatetime')

        if self.chkOrgStructure.isChecked():
            orgStructureIndex = self.cmbOrgStructure.model().index(self.cmbOrgStructure.currentIndex(), 0,
                                                                   self.cmbOrgStructure.rootModelIndex())
            getOrgStructureIdList(orgStructureIndex)
            self.modelProxy.setFilter('master_id', getOrgStructureIdList(orgStructureIndex),
                                      CSortFilterProxyTableModel.MatchInList)
        else:
            self.modelProxy.removeFilter('master_id')

        if self.chkProfileBed.isChecked():
            self.modelProxy.setFilter('profile_id', self.cmbHospitalBedProfile.value(),
                                      CSortFilterProxyTableModel.MatchExactly)
        else:
            self.modelProxy.removeFilter('profile_id')

    @pyqtSignature('')
    def on_btnFill_clicked(self):
        begDate = self.edtBegDate.date()
        endDate = self.edtEndDate.date()
        db = QtGui.qApp.db
        tableOS = db.table('OrgStructure')
        tableOSHB = db.table('OrgStructure_HospitalBed')
        tableHBP = db.table('rbHospitalBedProfile')
        tableHBS = db.table('rbHospitalBedShedule')

        table = tableOS.leftJoin(tableOSHB, tableOSHB['master_id'].eq(tableOS['id']))
        table = table.leftJoin(tableHBP, tableHBP['id'].eq(tableOSHB['profile_id']))
        table = table.leftJoin(tableHBS, tableHBS['id'].eq(tableOSHB['schedule_id']))
        cond = [
            tableOS['deleted'].eq(0),
            tableOS['hasHospitalBeds'].eq(1),
            tableOS['type'].eq(1),
            'NOT EXISTS(SELECT NULL FROM OrgStructure os WHERE os.parent_id = OrgStructure.id AND os.deleted = 0)',
            tableOSHB['id'].ne(0),
            tableOSHB['deleted'].eq(0),
            db.joinOr([tableOSHB['endDate'].isNull(), tableOSHB['endDate'].dateGe(endDate)]),
            tableHBP['id'].isNotNull()
        ]
        cols = "OrgStructure.id, rbHospitalBedProfile.id, IF(rbHospitalBedShedule.code = '1', 0, 1) as regime"
        group = "rbHospitalBedProfile.id, OrgStructure.id, IF(rbHospitalBedShedule.code = '1', 0, 1)"
        order = 'OrgStructure.name, rbHospitalBedProfile.name'
        recordList = db.getRecordListGroupBy(table, cols, cond, group, order)

        idList = []
        for record in self.model.items():
            orgId = forceRef(record.value('master_id'))
            profileId = forceRef(record.value('profile_id'))
            regime = forceInt(record.value('regime'))
            date = forceRef(record.value('date'))
            idList.append((orgId, profileId, regime, date))

        for record in recordList:
            orgStructureId = record.value(0)
            profileId = record.value(1)
            regime = record.value(2)
            tmpDate = begDate
            while tmpDate <= endDate:
                if (orgStructureId, profileId, regime, tmpDate) not in idList and forceRef(profileId):
                    newRecord = self.model.getEmptyRecord()
                    newRecord.setValue('date', QDateTime(tmpDate))
                    newRecord.setValue('master_id', orgStructureId)
                    newRecord.setValue('profile_id', profileId)
                    newRecord.setValue('regime', regime)
                    newRecord.setValue('adultMan', 0)
                    newRecord.setValue('adultWoman', 0)
                    newRecord.setValue('children', 0)
                    newRecord.setValue('createDatetime', QDateTime(QDate().currentDate()))
                    self.model.addRecord(newRecord)
                tmpDate = tmpDate.addDays(1)
        self.model.reset()

    @pyqtSignature('bool')
    def on_chkDate_toggled(self, checked):
        self.edtBegDate.setEnabled(checked)
        self.edtEndDate.setEnabled(checked)
        if not QtGui.qApp.userHasRight(urPlanningHospitalBedProfileGen):
            self.btnFill.setEnabled(False)
        else:
            self.btnFill.setEnabled(checked)
        self.onFilterUpdate()


    @pyqtSignature('bool')
    def on_chkDateCreate_toggled(self, checked):
        self.edtBegDateCreate.setEnabled(checked)
        self.edtEndDateCreate.setEnabled(checked)
        self.onFilterUpdate()

    @pyqtSignature('bool')
    def on_chkOrgStructure_toggled(self, checked):
        self.cmbOrgStructure.setEnabled(checked)
        if not checked:
            self.chkProfileBed.setChecked(checked)
            self.cmbHospitalBedProfile.setEnabled(checked)
        self.onFilterUpdate()

    @pyqtSignature('bool')
    def on_chkProfileBed_toggled(self, checked):
        self.cmbHospitalBedProfile.setEnabled(checked)
        self.onFilterUpdate()

    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.onFilterUpdate()

    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.onFilterUpdate()


    @pyqtSignature('QDate')
    def on_edtBegDateCreate_dateChanged(self, date):
        self.onFilterUpdate()


    @pyqtSignature('QDate')
    def on_edtEndDateCreate_dateChanged(self, date):
        self.onFilterUpdate()

    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureIdList = []
        curOrgStructureId = self.cmbOrgStructure.value()
        if curOrgStructureId:
            orgStructureIndex = self.cmbOrgStructure.model().index(index, 0, self.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = getOrgStructureIdList(orgStructureIndex)
        if orgStructureIdList:
            db = QtGui.qApp.db
            table = db.table('vHospitalBed')
            profileBedIdList = db.getDistinctIdList(table, [table['profile_id']],
                                                    [table['master_id'].inlist(orgStructureIdList)])
            selFilter = u'id IN (%s)' % (u', '.join(str(hpbId) for hpbId in profileBedIdList if hpbId))
        else:
            selFilter = ''
        self.cmbHospitalBedProfile.setTable('rbHospitalBedProfile', addNone=True, filter=selFilter, order='code')
        self.onFilterUpdate()

    @pyqtSignature('int')
    def on_cmbHospitalBedProfile_currentIndexChanged(self, index):
        self.onFilterUpdate()
