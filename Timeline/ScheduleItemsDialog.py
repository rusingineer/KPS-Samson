# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QAbstractTableModel, QDate, QDateTime, QTime, QVariant, pyqtSignature, SIGNAL

from Registry.ResourcesDock import isAppointmentEnabledForClient, isAppointmentEnabledForDate
from library.DialogBase               import CDialogBase
from library.RecordLock               import CRecordLockMixin
from library.TableModel               import CTableModel, CDesignationCol, CNameCol, CRefBookCol, CTextCol, CTimeCol
from library.TimeItemDelegate         import CTimeItemDelegate
from library.Utils import forceBool, forceRef, forceString, forceTime, toVariant, forceInt

from Registry.Utils                   import getClientBanner, getClientMiniInfo
from Timeline.Schedule import freeScheduleItemInt, getScheduleItemIdListForClient, getScheduleItemIdListForClient_OMS, \
    getExceptionSpecialty, getScheduleItemIdFinance, CScheduleItem
from Users.Rights import urAccessEditTimeLine

from Timeline.Ui_ScheduleItemsDialog  import Ui_ScheduleItemsDialog
from Timeline.Ui_RecordTransferDialog import Ui_RecordTransferDialog
from library.crbcombobox import CRBComboBox, CRBModelDataCache


class CScheduleItemsDialog(CDialogBase, CRecordLockMixin, Ui_ScheduleItemsDialog):

    class CComboBoxDelegate(QtGui.QItemDelegate):
        def __init__(self, parent, items=[]):
            QtGui.QItemDelegate.__init__(self, parent)
            self.items = items

        def createEditor(self, parent, option, index):
            editor = CRBComboBox(parent)
            editor.setTable('rbAppointmentPurpose')
            editor.setShowFields(CRBComboBox.showCodeAndName)
            return editor

        def setEditorData(self, editor, index):
            model = index.model()
            data = model.data(index, Qt.EditRole)
            editor.setShowFields(editor.showFields)
            editor.setValue(forceRef(data))

        def getEditorData(self, editor):
            return QVariant(editor.value())

        def setModelData(self, editor, model, index):
            model.setData(index, toVariant(editor.value()))


    def __init__(self, parent, schedule, siblingSchedules):
        CDialogBase.__init__(self, parent)
        CRecordLockMixin.__init__(self)
        self.addModels('ScheduleItems', CScheduleItemsModel(self))
        self.addModels('OrgStructureGaps', COrgStructureGapsModel(self))
        self.addModels('PersonGaps', CPersonGapsModel(self))
        self.addObject('actRecordTransfer', QtGui.QAction(u'Перенести запись', self))
        self.addObject('actRecordRelease',  QtGui.QAction(u'Удалить запись', self))

        self.setupUi(self)
        self.setModels(self.tblScheduleItems,  self.modelScheduleItems, self.selectionModelScheduleItems)
        self.timeDelegate = CTimeItemDelegate(self)
        self.purposeDelegate = CScheduleItemsDialog.CComboBoxDelegate(self)
        self.tblScheduleItems.setItemDelegateForColumn(0, self.timeDelegate)
        self.tblScheduleItems.setItemDelegateForColumn(2, self.purposeDelegate)
        self.tblScheduleItems.createPopupMenu([self.actRecordTransfer,
                                               self.actRecordRelease
                                              ]
                                             )
        self.connect(self.tblScheduleItems.popupMenu(), SIGNAL('aboutToShow()'), self.scheduleItemsPopupMenuAboutToShow)

        self.setModels(self.tblOrgStructureGaps, self.modelOrgStructureGaps, self.selectionModelOrgStructureGaps)
        self.setModels(self.tblPersonGaps, self.modelPersonGaps, self.selectionModelPersonGaps)
        self.schedule = schedule
        self.siblingSchedules = siblingSchedules
        self.modelScheduleItems.setItems(schedule.items)
        self.modelOrgStructureGaps.loadData(schedule.personId)
        self.modelPersonGaps.loadData(schedule.personId)


    def scheduleItemsPopupMenuAboutToShow(self):
        row = self.tblScheduleItems.currentIndex().row()
        clientId = self.modelScheduleItems.getClientId(row)
        rightEditTimeLine = QtGui.qApp.userHasRight(urAccessEditTimeLine)
        self.actRecordTransfer.setEnabled(bool(clientId) and rightEditTimeLine)
        self.actRecordRelease.setEnabled(bool(clientId) and rightEditTimeLine)


    @pyqtSignature('')
    def on_actRecordRelease_triggered(self):
        row = self.tblScheduleItems.currentIndex().row()
        if 0<=row<self.modelScheduleItems.rowCount():
            freeScheduleItemInt(self.modelScheduleItems.getScheduleItem(row).getRecord())
            self.modelScheduleItems.updateRow(row)


    @pyqtSignature('')
    def on_actRecordTransfer_triggered(self):
        row = self.tblScheduleItems.currentIndex().row()
        if 0<=row<self.modelScheduleItems.rowCount():
            dlg = CRecordTransferDialog(self)
            dlg.setup(self.schedule.appointmentType,
                      self.schedule.appointmentPurposeId,
                      self.schedule.personId,
                      self.schedule.date,
                      self.modelScheduleItems.getScheduleItem(row)
                     )
            if dlg.exec_():
                self.modelScheduleItems.updateRow(row)
                changedScheduleId = dlg.destScheduleId
                changedScheduleItemId = dlg.destScheduleItemId
                if self.schedule.id == changedScheduleId:
                    changedRow = self.modelScheduleItems.findRow(changedScheduleItemId)
                    if changedRow>=0:
                        self.modelScheduleItems.reloadRow(changedRow)
                else:
                    for schedule in self.siblingSchedules:
                        if schedule.id == changedScheduleId:
                            for item in schedule.items:
                                if item.id == changedScheduleItemId:
                                    item.reload()
                                    break
                            break



class CScheduleItemsModel(QAbstractTableModel):
    headerText = [u'Время', u'Пациент', u'Назначение приёма']

    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.items = []


    def columnCount(self, index = None):
        return 3


    def rowCount(self, index = None):
        return len(self.items)


    def flags(self, index):
        result = Qt.ItemIsSelectable|Qt.ItemIsEnabled
        column = index.column()
        row = index.row()
        item = self.items[row]
        if column == 0:
            if not item[1]:
                result |= Qt.ItemIsEditable
        if column == 2:
            result |= Qt.ItemIsEditable
        return result


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.headerText[section])
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        item = self.items[row]
        if role == Qt.DisplayRole:
            if column == 0:
                return QVariant(item[column])
            if column == 1:
                return QVariant(item[column])
            if column == 2:
                if forceRef(item[4]):
                    cache = CRBModelDataCache.getData('rbAppointmentPurpose', True)
                    text = cache.getStringById(forceRef(item[4]), CRBComboBox.showCodeAndName)
                    return QVariant(text)
                else:
                    return QVariant()
        if role == Qt.EditRole:
            if column == 0:
                return QVariant(item[column])
            if column == 2:
                return QVariant(item[4])
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            column = index.column()
            row = index.row()
            if column == 0:
                newValue = value.toTime()
                if self.setTime(row, newValue):
                    self.emitCellChanged(row, column)
                else:
                    return False
            if column == 2:
                if self.setPurpose(row, value):
                    self.emitCellChanged(row, column)
                else:
                    return False
            return True
        return False


    def emitCellChanged(self, row, column):
        index = self.index(row, column)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)


    def setItems(self, items):
        self.items = []
        for item in items:
            clientId = item.clientId
            self.items.append( [item.time.time(),
                                getClientMiniInfo(clientId) if clientId else None,
                                clientId,
                                item,
                                item.appointmentPurposeId,
                               ]
                             )
        self.reset()


    def getTime(self, row):
        return self.items[row][0] if 0<=row<len(self.items) else None


    def setTime(self, row, time):
        if time.isValid():
            self.items[row][0] = time
            scheduleItem = self.items[row][3]
            scheduleItem.time = QDateTime(scheduleItem.time.date(), time)
            if scheduleItem.id:
                scheduleItem.save()

    def setPurpose(self, row, purposeId):
        if purposeId:
            self.items[row][4] = purposeId
            scheduleItem = self.items[row][3]
            scheduleItem.appointmentPurposeId = purposeId
            if scheduleItem.id:
                scheduleItem.save()


    def getClientId(self, row):
        return self.items[row][2] if 0<=row<len(self.items) else None


    def getScheduleItem(self, row):
        return self.items[row][3] if 0<=row<len(self.items) else None


    def findRow(self, scheduleItemId):
        for row, item in enumerate(self.items):
            if item[3].id == scheduleItemId:
                return row
        return -1


    def updateRow(self, row):
        item = self.items[row][3]
        clientId = item.clientId
        self.items[row] = [ item.time.time(),
                            getClientMiniInfo(clientId) if clientId else None,
                            clientId,
                            item,
                            item.appointmentPurposeId
                          ]
        self.emitCellChanged(row, 1)


    def reloadRow(self, row):
        item = self.items[row][3]
        item.reload()
        self.updateRow(row)


    def saveData(self):
        for item in self.items:
            time, clientText, clientId, scheduleItem, appointmentPurposeId = item
            if not clientId:
                scheduleItem.time = QDateTime(scheduleItem.time.date(), time)
                scheduleItem.appointmentPurposeId = appointmentPurposeId
        self.reset()


class CGapsModel(QAbstractTableModel):
    headerText = [u'Начало', u'Конец']

    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.items = []


    def columnCount(self, index = None):
        return 2


    def rowCount(self, index = None):
        return len(self.items)


    def flags(self, index):
        return Qt.ItemIsSelectable|Qt.ItemIsEnabled


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.headerText[section])
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            item = self.items[row]
            return QVariant(item[column])
        return QVariant()

    @staticmethod
    def addGap(gapList, record):
        begTime = forceTime(record.value('begTime'))
        endTime = forceTime(record.value('endTime'))
        if begTime < endTime:
            gapList.append((begTime, endTime))
        elif begTime > endTime:
            gapList.append((begTime, QTime(23, 59, 59, 999)))
            gapList.append((QTime(0, 0), endTime))



class CPersonGapsModel(CGapsModel):
    def loadData(self, personId):
        db = QtGui.qApp.db
        orgStructureId = forceRef(db.translate('Person', 'id', personId, 'orgStructure_id'))
        items = []
        while orgStructureId:
            recordsPersonGap = db.getRecordList('OrgStructure_Gap', 'begTime, endTime',  'master_id=%d AND person_id=%d' %(orgStructureId, personId))
            for record in recordsPersonGap:
                self.addGap(items, record)
            orgStructureId = forceRef(db.translate('OrgStructure', 'id', orgStructureId, 'parent_id'))
        items.sort()
        self.items = items
        self.reset()



class COrgStructureGapsModel(CGapsModel):
    def loadData(self, personId):
        db = QtGui.qApp.db
        specialityId = forceRef(db.translate('Person', 'id', personId, 'speciality_id'))
        orgStructureId = forceRef(db.translate('Person', 'id', personId, 'orgStructure_id'))
        items = []
        while orgStructureId:
            recordsOrgStructureGap = db.getRecordList('OrgStructure_Gap', 'begTime, endTime',  'master_id=%d AND %s AND person_id IS NULL' %(orgStructureId, '(speciality_id=%d OR speciality_id IS NULL)'%(specialityId) if specialityId else '(speciality_id IS NULL)'))
            for record in recordsOrgStructureGap:
                self.addGap(items, record)
            inheritGaps = forceBool(db.translate('OrgStructure', 'id', orgStructureId, 'inheritGaps'))
            if not inheritGaps:
                break
            orgStructureId = forceRef(db.translate('OrgStructure', 'id', orgStructureId, 'parent_id'))
        items.sort()
        self.items = items
        self.reset()


# ##############################################################################


class CRecordTransferDialog(CDialogBase, Ui_RecordTransferDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.addModels('Personnel', CPersonnelModel(self))
        self.addModels('FreeScheduleItems', CFreeScheduleItemsModel(self))

        self.setupUi(self)
        self.setModels(self.tblPersonnel, self.modelPersonnel, self.selectionModelPersonnel)
        self.setModels(self.tblScheduleItems, self.modelFreeScheduleItems, self.selectionModelFreeScheduleItems)

        currentDate = QDate.currentDate()
        self.calendar.setMinimumDate(currentDate)
        self.calendar.setMaximumDate(currentDate.addMonths(6))

        self.cmbSpeciality.setTable('rbSpeciality')
        self.cmbAppointmentPurpose.setTable('rbAppointmentPurpose')

        self.enableOk(False)
        self.destScheduleId = None
        self.destScheduleItemId = None


    def saveData(self):
        return self.doRecordTransfer()


    def setup(self, appointmentType, appointmentPurposeId, personId, date, scheduleItem):
        self.setWindowTitle(u'Перенос записи с %s %s' % (forceString(date), forceString(scheduleItem.time.time())))
        clientId = scheduleItem.clientId
        self.txtClientInfoBrowser.setHtml(getClientBanner(clientId) if clientId else '')
        calendarBlockSignals   = self.calendar.blockSignals(True)
        specialityBlockSignals = self.cmbSpeciality.blockSignals(True)
        appointmentPurposeBlockSignals = self.cmbAppointmentPurpose.blockSignals(True)
        selectionModelPersonnelBlockSignals = self.selectionModelPersonnel.blockSignals(True)
        try:
            self.appointmentType = appointmentType
            self.appointmentPurposeId = appointmentPurposeId
            self.specialityId = self.getPersonSpeciality(personId)
            self.cmbSpeciality.setValue(self.specialityId)
            self.cmbAppointmentPurpose.setValue(appointmentPurposeId)
            self.personId = personId
            self.calendar.setSelectedDate(date)
            self.tblPersonnel.setCurrentItemId(personId)
            self.scheduleItem = scheduleItem
            self.updateTables()
        finally:
            self.calendar.blockSignals(calendarBlockSignals)
            self.cmbSpeciality.blockSignals(specialityBlockSignals)
            self.cmbAppointmentPurpose.blockSignals(appointmentPurposeBlockSignals)
            self.selectionModelPersonnel.blockSignals(selectionModelPersonnelBlockSignals)


    def getPersonSpeciality(self, personId):
        db = QtGui.qApp.db
        specialityId = forceRef(db.translate('Person', 'id', personId, 'speciality_id'))
        return specialityId


    def updateTables(self):
        self.updatePersonnelTable()
        self.updateScheduleItemsTable()


    def updatePersonnelTable(self):
        date = self.calendar.selectedDate()
        specialityId = self.cmbSpeciality.value()
        appointmentPurposeId = self.cmbAppointmentPurpose.value()

        db = QtGui.qApp.db
        tablePerson = db.table('Person')
        tableSchedule = db.table('Schedule')
        tableScheduleItem = db.table('Schedule_Item')

        table = tablePerson.innerJoin(tableSchedule, tableSchedule['person_id'].eq(tablePerson['id']))
        table = table.innerJoin(tableScheduleItem, tableScheduleItem['master_id'].eq(tableSchedule['id']))

        cond = [ tablePerson['deleted'].eq(0),
                 db.joinOr([tablePerson['retireDate'].isNull(), tablePerson['retireDate'].ge(QDate.currentDate().addMonths(6))]),
                 tablePerson['speciality_id'].eq(specialityId) if specialityId else tablePerson['speciality_id'].isNotNull(),
                 tableSchedule['deleted'].eq(0),
                 tableSchedule['date'].eq(date),
                 tableSchedule['appointmentType'].eq(self.appointmentType),
                 tableSchedule['appointmentPurpose_id'].eq(appointmentPurposeId) if appointmentPurposeId else '1',
                 tableSchedule['reasonOfAbsence_id'].isNull(),
                 tableScheduleItem['deleted'].eq(0),
                 tableScheduleItem['client_id'].isNull(),
               ]

        personIdList = db.getDistinctIdList(table, idCol=tablePerson['id'], where=cond, order='lastName, firstName, patrName')
        self.tblPersonnel.setIdList(personIdList)


    def updateScheduleItemsTable(self):
        self.enableOk(False)
        date = self.calendar.selectedDate()
        appointmentPurposeId = self.cmbAppointmentPurpose.value()
        personId = self.tblPersonnel.currentItemId()

        db = QtGui.qApp.db
        table = db.table('vScheduleItem')
        cond = [ table['date'].eq(date),
                 table['person_id'].eq(personId),
                 table['appointmentType'].eq(self.appointmentType),
                 table['reasonOfAbsence_id'].isNull(),
                 table['client_id'].isNull()
               ]
        if appointmentPurposeId:
            cond.append(table['appointmentPurpose_id'].eq(appointmentPurposeId))

        tableSchedule = db.table('Schedule')
        tableScheduleItem = db.table('Schedule_Item')

        table = tableScheduleItem.innerJoin(tableSchedule, tableScheduleItem['master_id'].eq(tableSchedule['id']))
        cond = [ tableSchedule['deleted'].eq(0),
                 tableSchedule['person_id'].eq(personId),
                 tableSchedule['date'].eq(date),
                 tableSchedule['appointmentType'].eq(self.appointmentType),
                 tableSchedule['appointmentPurpose_id'].eq(appointmentPurposeId) if appointmentPurposeId else '1',
                 tableSchedule['reasonOfAbsence_id'].isNull(),
                 tableScheduleItem['deleted'].eq(0),
                 tableScheduleItem['client_id'].isNull(),
               ]

        idList = db.getIdList(table, idCol=tableScheduleItem['id'], where=cond, order='idx, time')
        self.tblScheduleItems.setIdList(idList)
        self.tblScheduleItems.setCurrentRow(0)


    def enableOk(self, value):
        button = self.buttonBox.button(QtGui.QDialogButtonBox.Ok)
        button.setEnabled(value)

    def queueingEnabled(self, scheduleItemId, date, personId, specialityId, clientId, scheduleItem):
        appointmentPurposeId = forceRef(scheduleItem.record.value('appointmentPurpose_id'))

        if not isAppointmentEnabledForClient(appointmentPurposeId, personId, date, clientId):
            QtGui.QMessageBox.warning(self, u'Внимание!', u'Назначение приёма препятствует записи пациента')
            return False

        if scheduleItem and not QtGui.qApp.isReStagingInQueue() and not isAppointmentEnabledForDate(scheduleItem):
            QtGui.QMessageBox.warning(self, u'Внимание!',
                                      u'Запись за горизонт 14 дней разрешена только для повторной записи самому к себе')
            return False

        scheduleItemIdList = getScheduleItemIdListForClient(clientId, specialityId, date, '1')
        if scheduleItemIdList:
            scheduleItemIdList.remove(self.scheduleItem.id)
        if scheduleItemIdList:
            scheduleItemIdList_OMS = getScheduleItemIdListForClient_OMS(scheduleItemIdList)
            exceptionSpecialty = getExceptionSpecialty(specialityId)
            checkFinance = None
            if scheduleItemId and appointmentPurposeId:
                recordFinance = getScheduleItemIdFinance(scheduleItem)
                if recordFinance:
                    checkFinance = forceString(recordFinance.value('code'))
                else:
                    checkFinance = None
            if QtGui.qApp.isReStagingInQueue() or (checkFinance and checkFinance != '2') or not scheduleItemIdList_OMS or exceptionSpecialty == 1:
                messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, u'Внимание!',
                                               u'Этот пациент уже записан к врачу этой специальности\nВы подтверждаете повторную запись?')
            else:
                messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, u'Внимание!',
                                               u'Этот пациент уже записан к врачу этой специальности')
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            if QtGui.qApp.isReStagingInQueue() or (
                    checkFinance and checkFinance != '2') or not scheduleItemIdList_OMS or exceptionSpecialty == 1:
                messageBox.addButton(u'Ок', QtGui.QMessageBox.YesRole)
            messageBox.addButton(u'Отмена', QtGui.QMessageBox.NoRole)
            confirmation = messageBox.exec_()
            if (confirmation == 1 or not (QtGui.qApp.isReStagingInQueue() or (checkFinance and checkFinance != '2') or not scheduleItemIdList_OMS or exceptionSpecialty == 1)) :
                return False
        return True


    def doRecordTransfer(self):
        db = QtGui.qApp.db
        result = False
        destScheduleItemId = self.tblScheduleItems.currentItemId()
        parent = self.parent()
        lockId = parent.lock('Schedule_Item', destScheduleItemId)
        if lockId:
            try:
                destRecord = db.getRecord('Schedule_Item', '*', destScheduleItemId)
                scheduleItem = CScheduleItem(destRecord)
                result = ( bool(destRecord)
                           and not forceBool(destRecord.value('deleted'))
                           and not forceRef(destRecord.value('client_id'))
                           and self.queueingEnabled(destScheduleItemId, self.calendar.selectedDate(), self.personId, self.specialityId, self.scheduleItem.clientId, scheduleItem)
                         )
                if not result:
                    return result
                for fieldName in ('client_id',
                                  'recordDatetime',
                                  'recordPerson_id',
                                  'recordClass',
                                  'complaint',
                                  'note',
                                  'checked'):
                    destRecord.setValue(fieldName, self.scheduleItem.value(fieldName))
                db.updateRecord('Schedule_Item', destRecord)
                freeScheduleItemInt(self.scheduleItem.getRecord())
                self.destScheduleId = forceRef(destRecord.value('master_id'))
                self.destScheduleItemId = destScheduleItemId
            finally:
                parent.releaseLock(lockId)
        return result


    @pyqtSignature('')
    def on_calendar_selectionChanged(self):
        self.updateTables()


    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        self.updateTables()


    @pyqtSignature('int')
    def on_cmbAppointmentPurpose_currentIndexChanged(self, index):
        self.updateTables()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelPersonnel_currentChanged(self, current, previous):
        self.updateScheduleItemsTable()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelFreeScheduleItems_currentChanged(self, current, previous):
        self.enableOk(current.isValid())


    @pyqtSignature('QModelIndex')
    def on_tblScheduleItems_doubleClicked(self, current):
        self.accept()
        if not self.result():
            self.updateScheduleItemsTable()



class CPersonnelModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent,  [
            CTextCol(u'Код',      ['code'], 6),
            CTextCol(u'Фамилия',  ['lastName'], 20),
            CNameCol(u'Имя',      ['firstName'], 20),
            CNameCol(u'Отчество', ['patrName'], 20),
            CDesignationCol(u'Подразделение', ['orgStructure_id'], ('OrgStructure', 'name'), 5),
            CRefBookCol(u'Должность',      ['post_id'], 'rbPost', 10),
            CRefBookCol(u'Специальность',  ['speciality_id'], 'rbSpeciality', 10),
            ], 'Person' )



class CFreeScheduleItemsModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent,  [
            CTimeCol(u'Время',    ['time'], 6),
            CRefBookCol(u'Назначение приёма',  ['appointmentPurpose_id'], 'rbAppointmentPurpose', 10),
            ], 'vScheduleItem')

