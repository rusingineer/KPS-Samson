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
from PyQt4.QtCore       import Qt, QAbstractTableModel, QDate, pyqtSignature, QVariant, SIGNAL, QModelIndex

from Registry.Utils import getClientName, getClientPhone
from library.DialogBase import CDialogBase
from library.Utils      import forceDate, forceRef, toVariant, formatDate
from library.DateItemDelegate import CDateItemDelegate


from Registry.Ui_RegistryProphylaxisPlanning import Ui_RegistryProphylaxisPlanningDialog


class CRegistryProphylaxisPlanning(CDialogBase, Ui_RegistryProphylaxisPlanningDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.addModels('VisitPeriods', CVisitPeriodsModel(self))
        self.setupUi(self)
        self.setModels(self.tblVisitPeriods,  self.modelVisitPeriods, self.selectionModelVisitPeriods)
        self.timeDelegate = CDateItemDelegate(self)
        self.tblVisitPeriods.setItemDelegateForColumn(0, self.timeDelegate)
        self.tblVisitPeriods.setItemDelegateForColumn(1, self.timeDelegate)
        self.tblVisitPeriods.addPopupDelRow()
        self.cmbSpeciality.setTable('rbSpeciality')
        self.cmbProphylaxisPlanningType.setTable('rbProphylaxisPlanningType')
        self.cmbScene.setTable('rbScene')
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        if QtGui.qApp.userSpecialityId:
            self.cmbPerson.setValue(QtGui.qApp.userId)
            self.cmbSpeciality.setValue(QtGui.qApp.userSpecialityId)
        self.clientId = None
        self.cmbProphylaxisPlanningType.setValue(0)
        self.cmbScene.setValue(0)

    def accept(self):
        if not self.cmbProphylaxisPlanningType.value():
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Не заполнено поле "Тип планирования профилактики"',
                                      QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            self.cmbProphylaxisPlanningType.setFocus()
            self.cmbProphylaxisPlanningType.showPopup()
        else:
            QtGui.QDialog.accept(self)
            return

    def registryProphylaxisPlanning(self):
        prophylaxisPlanningIdList = []
        if self.clientId:
            visitPeriods = self.getRegistryVisitPeriods()
            for begDate, endDate in visitPeriods:
                orgStructureId   = self.getRegistryOrgStructure()
                specialityId     = self.getRegistrySpeciality()
                personId         = self.getRegistryPerson()
                prophylaxisPlanningTypeId = self.getProphylaxisPlanningType()
                sceneId          = self.getRegistryScene()
                MKB               = self.getRegistryMKB()
                note               = self.getRegistryNote()
                db = QtGui.qApp.db
                table = db.table('ProphylaxisPlanning')
                cond = [table['deleted'].eq(0), table['client_id'].eq(self.clientId)]
                if personId:
                    cond.append(table['person_id'].eq(personId))
                else:
                    if specialityId:
                        cond.append(table['speciality_id'].eq(specialityId))
                    if orgStructureId:
                        cond.append(table['orgStructure_id'].eq(orgStructureId))
                if begDate:
                    cond.append(table['endDate'].ge(begDate))
                if endDate:
                    cond.append(table['begDate'].le(endDate))
                if prophylaxisPlanningTypeId:
                    cond.append(table['prophylaxisPlanningType_id'].eq(prophylaxisPlanningTypeId))
                if sceneId:
                    cond.append(table['scene_id'].eq(sceneId))
                if MKB:
                    cond.append(table['MKB'].eq(MKB))                 
                recordSA = db.getRecordEx(table, [table['id']], cond, order='id DESC')
                regisrtySAId = forceRef(recordSA.value('id')) if recordSA else None
                if not regisrtySAId:
                    record = table.newRecord()
                    record.setValue('client_id', toVariant(self.clientId))
                    record.setValue('begDate', toVariant(begDate))
                    record.setValue('endDate', toVariant(endDate))
                    record.setValue('orgStructure_id', toVariant(orgStructureId))
                    record.setValue('speciality_id', toVariant(specialityId))
                    record.setValue('person_id', toVariant(personId))                
                    record.setValue('prophylaxisPlanningType_id', toVariant(prophylaxisPlanningTypeId))
                    record.setValue('scene_id', toVariant(sceneId))
                    record.setValue('MKB', toVariant(MKB))                
                    record.setValue('note', toVariant(note))
                    record.setValue('contact', getClientPhone(self.clientId))
                    prophylaxisPlanningId = db.insertRecord(table, record)
                    if prophylaxisPlanningId and prophylaxisPlanningId not in prophylaxisPlanningIdList:
                        prophylaxisPlanningIdList.append(prophylaxisPlanningId)
                else:
                    QtGui.QMessageBox.warning(self,
                                              u'Внимание!',
                                              u'В Журнале планирования профилактического наблюдения запись на пациента %s в периоде с %s по %s уже существует, id = %s!'%(getClientName(self.clientId), begDate.toString('dd.MM.yyyy') if begDate else u'', endDate.toString('dd.MM.yyyy') if endDate else u'', regisrtySAId),
                                              QtGui.QMessageBox.Ok,
                                              QtGui.QMessageBox.Ok)
        return prophylaxisPlanningIdList                                 

    def getClientId(self):
        return self.clientId

    def getRegistryVisitPeriods(self):
        return self.modelVisitPeriods.getItems()         

    def getRegistryOrgStructure(self):
        return self.cmbOrgStructure.value()

    def getRegistrySpeciality(self):
        return self.cmbSpeciality.value()

    def getRegistryPerson(self):
        return self.cmbPerson.value()

    def getRegistryNote(self):
        return self.edtNote.toPlainText()

    def getProphylaxisPlanningType(self):
        return self.cmbProphylaxisPlanningType.value()

    def getRegistryScene(self):
        return self.cmbScene.value()

    def getRegistryMKB(self):
        return unicode(self.edtMKB.text())

    def setClientId(self, clientId):
        self.clientId = clientId
        self.edtMKB.setLUDEnabled(bool(self.clientId))
        self.edtMKB.setLUDChecked(True, self.clientId)

    def setRegistryVisitPeriods(self, begDate, endDate):
        self.modelVisitPeriods.setItems([[begDate, endDate]])    

    def setRegistryOrgStructure(self, orgStructureId):
        self.cmbOrgStructure.setValue(orgStructureId)

    def setRegistrySpeciality(self, specialityId):
        self.cmbSpeciality.setValue(specialityId)

    def setRegistryPerson(self, personId):
        self.cmbPerson.setValue(personId)

    def setRegistryNote(self, text):
        self.edtNote.setPlainText(text)

    def setProphylaxisPlanningType(self, value):
        self.cmbProphylaxisPlanningType.setValue(value)

    def setRegistryScene(self, value):
        self.cmbScene.setValue(value)

    def setRegistryMKB(self, value):
        self.edtMKB.setText(value)

    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)

    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        specialityId = self.cmbSpeciality.value()
        self.cmbPerson.setSpecialityId(specialityId)

                                 
def setRegistryProphylaxisPlanningList(content, clientIdList):
    try:
        orgStructureId = content.getCurrentOrgSrtuctureId() if content else QtGui.qApp.currentOrgStructureId()
        specialityId = QtGui.qApp.userSpecialityId
        personIdList = content.getCurrentPersonIdList() if content else []
        personId = content.getCurrentPersonId() if content else QtGui.qApp.userId
        begDate = content.getCurrentDate() if content else QDate.currentDate()
        withoutCurrentPerson = False
    except AttributeError:
        withoutCurrentPerson = True
        orgStructureId = None
        specialityId = None
        personIdList = []
        personId = None
        begDate = QDate.currentDate()
    endDate = begDate.addDays(30)
    if personId or personIdList:
        db = QtGui.qApp.db
        tableSchedule = db.table('Schedule')
        tablePerson   = db.table('Person')
        cols = [tableSchedule['date']]
        cond = [tableSchedule['deleted'].eq(0)]
        if personId:
            cond.append(tableSchedule['person_id'].eq(personId))
        elif personIdList:
            cond.append(tableSchedule['person_id'].inlist(personIdList))
        record = db.getRecordEx(tableSchedule, cols, cond, order='date DESC')
        if record:
            endDate = forceDate(record.value('date'))
        if personId:
            record = db.getRecordEx(tablePerson,
                                    [tablePerson['speciality_id'], tablePerson['orgStructure_id']],
                                    [tablePerson['id'].eq(personId), tablePerson['deleted'].eq(0)])
            if record:
                specialityId = forceRef(record.value('speciality_id'))
                orgStructureId = forceRef(record.value('orgStructure_id'))
        elif content:
            for personIdSP in personIdList:
                if personIdSP:
                    specialityId = content.getPersonSpecialityId(personIdSP)
                    if specialityId:
                        break
    if begDate > endDate:
        endDate = begDate.addDays(30)
    dialog = CRegistryProphylaxisPlanning(content)
    dialog.setRegistryVisitPeriods(begDate, endDate)
    dialog.setRegistryOrgStructure(orgStructureId)
    dialog.setRegistrySpeciality(specialityId)
    dialog.setRegistryPerson(personId)
    if clientIdList and len(clientIdList) == 1:
        dialog.setClientId(clientIdList[0])
    else:
        dialog.edtMKB.setLUDEnabled(False)
    if dialog.exec_():
        if (orgStructureId or specialityId or personId) or withoutCurrentPerson:
            prophylaxisPlanningIdList = []
            for clientId in clientIdList:
                if clientId:
                    dialog.setClientId(clientId)
                    if dialog.getClientId():
                        registryPPIdList = dialog.registryProphylaxisPlanning()
                        if registryPPIdList:
                            prophylaxisPlanningIdList.extend(registryPPIdList)
            if prophylaxisPlanningIdList:                    
                QtGui.QMessageBox.warning(content,
                                          u'Внимание!',
                                          u'Произведена запись в Журнал планирования профилактического наблюдения!',
                                          QtGui.QMessageBox.Ok,
                                          QtGui.QMessageBox.Ok)
        else:
            QtGui.QMessageBox.critical(content,
                                       u'Внимание!',
                                       u'Не указаны подразделение и специальность или врач! Запись в Журнал '
                                       u'планирования профилактического наблюдения не возможна!',
                                       QtGui.QMessageBox.Ok,
                                       QtGui.QMessageBox.Ok)


class CVisitPeriodsModel(QAbstractTableModel):
    headerText = [u'Дата начала периода', u'Дата окончания периода']

    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.items = []

    def columnCount(self, index=None):
        return 2

    def rowCount(self, index=None):
        return len(self.items) + 1

    def realRowCount(self):
        return len(self.items)        

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.headerText[section])
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self.items):
            item = self.items[row]
            val = item[column]
            if val:
                if role == Qt.DisplayRole:
                    if not val.isNull():
                       return QVariant(formatDate(val))
                if role == Qt.EditRole:
                    if not val.isNull():
                       return QVariant(formatDate(val))
        return QVariant()

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            column = index.column()
            row = index.row()
            if row == len(self.items):
                if value.isNull():
                    return False
                self.items.append([None, None])
                count = len(self.items)
                rootIndex = QModelIndex()
                self.beginInsertRows(rootIndex, count, count)
                self.insertRows(count, 1, rootIndex)
                self.endInsertRows() 
            if 0 <= row < len(self.items):
                if value.isNull():
                    return False
                date = value.toDate()
                if date.isValid():
                    self.items[row][column] = date
                    self.emitCellChanged(row, column)
                else:
                    return False
            return True
        return False

    def getDate(self, row, column):
        if 0 <= row < len(self.items):
            return self.items[row][column] 
        return None

    def setItems(self, items):
        self.items = items
        self.reset()

    def getItems(self):
        return self.items

    def confirmRemoveRow(self, view, row, multiple=False):
        return True

    def canRemoveRow(self, row):
        return True

    def removeRow(self, row, parent=QModelIndex()):
        if self.items and 0 <= row < len(self.items):
            QtGui.qApp.setWaitCursor()
            try:
                self.beginRemoveRows(parent, row, row)
                del self.items[row]
                self.endRemoveRows()
                self.emitItemsCountChanged()
                return True
            finally:
                QtGui.qApp.restoreOverrideCursor()
        return False        

    def emitCellChanged(self, row, column):
        index = self.index(row, column)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)

    def emitItemsCountChanged(self):
        self.emit(SIGNAL('itemsCountChanged(int)'), len(self.items) if self.items else 0)
