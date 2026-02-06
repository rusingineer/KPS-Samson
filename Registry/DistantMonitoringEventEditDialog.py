# -*- coding: utf-8 -*-

import re

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, QDate

from library.DialogBase import CDialogBase
from library.Utils import forceRef, forceInt, forceString, forceDate, exceptionToUnicode

from Exchange.PyServices import getPyServices, CDistantMonitoringService
from Registry.ClientEditDialog import CClientEditDialog
from Users.Rights import urAdmin, urRegTabWriteRegistry

from Ui_DistantMonitoringEventEditDialog import Ui_DistantMonitoringEventEditDialog


class EditMode:
    CreateEvent = 1
    EditEvent = 2
    ReplaceEquipment = 3
    EndProgram = 4


class CDistantMonitoringEventEditDialog(CDialogBase, Ui_DistantMonitoringEventEditDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        db = QtGui.qApp.db
        self.systemId = forceRef(db.translate('rbAccountingSystem', 'code', 'SYSDM', 'id'))
        if not self.systemId:
            raise Exception(u'Не найдена внешняя учетная система "SYSDM"')
        self.cmbClient.setNoneText(u'не задано')
        tablePerson = db.table(self.cmbPerson.tableName())
        tablePersonIdentification = db.table('Person_Identification')
        personFilter = db.existsStmt(tablePersonIdentification, [
            tablePersonIdentification['master_id'].eq(tablePerson['id']),
            tablePersonIdentification['system_id'].eq(self.systemId),
            tablePersonIdentification['deleted'].eq(0),
        ])
        self.cmbPerson.setFilter(personFilter, needCache=False)
        self.cmbEquipment.setTable('rbEquipment', needCache=False)
        self.cmbEquipment.setValue(None)
        self.cmbObservationGroup.addItem(u'не задано')
        self.cmbObservationGroup.addItem(u'1. СД1И')
        self.cmbObservationGroup.addItem(u'2. СД2И')
        self.cmbObservationGroup.addItem(u'3. СД2Т')
        self.cmbObservationGroup.setCurrentIndex(-1)
        self.pyServices = getPyServices(CDistantMonitoringService)
        self.observationGroupActual = False
    
    @pyqtSignature('int')
    def on_cmbEquipment_currentIndexChanged(self, index):
        equipmentId = self.cmbEquipment.value()
        self.observationGroupActual = False
        self.lblProgramTypeText.setText('')
        if equipmentId:
            db = QtGui.qApp.db
            tableEquipment = db.table('rbEquipment')
            tableEquipmentType = db.table('rbEquipmentType')
            tableEquipmentClass = db.table('rbEquipmentClass')
            query = tableEquipment.leftJoin(tableEquipmentType, tableEquipmentType['id'].eq(tableEquipment['equipmentType_id']))
            query = query.leftJoin(tableEquipmentClass, tableEquipmentClass['id'].eq(tableEquipmentType['class_id']))
            record = db.getRecordEx(query, where=tableEquipment['id'].eq(equipmentId), cols=tableEquipmentClass['code'])
            if record:
                classCode = forceString(record.value('code'))
                if classCode == '12':
                    self.observationGroupActual = True
                    self.lblProgramTypeText.setText(u'Программа по СД')
                elif classCode == '6':
                    self.lblProgramTypeText.setText(u'Программа по АГ')
        if self.observationGroupActual:
            self.cmbObservationGroup.setEnabled(self.enableObservationGroup())
            if self.cmbObservationGroup.currentIndex() == -1:
                self.cmbObservationGroup.setCurrentIndex(0)
        else:
            self.cmbObservationGroup.setEnabled(False)
            self.cmbObservationGroup.setCurrentIndex(-1)
    
    def execCreateEvent(self):
        self.setEditMode(EditMode.CreateEvent)
        self.setEventId(None)
        self.lblEquipmentStatusText.setText(u'Выдача')
        return self.exec_()
    
    def execEditEvent(self, eventId):
        self.setEditMode(EditMode.EditEvent)
        self.setEventId(eventId)
        return self.exec_()
    
    def execReplaceEquipment(self, eventId):
        self.setEditMode(EditMode.ReplaceEquipment)
        self.setEventId(eventId)
        self.lblEquipmentStatusText.setText(u'Замена')
        self.edtComment.setPlainText('')
        return self.exec_()
    
    def execEndProgram(self, eventId):
        self.setEditMode(EditMode.EndProgram)
        self.setEventId(eventId)
        self.lblEquipmentStatusText.setText(u'Возврат')
        self.edtComment.setPlainText('')
        return self.exec_()
    
    def enableObservationGroup(self):
        return (self.editMode in (EditMode.CreateEvent, EditMode.EditEvent))
    
    def setEditMode(self, editMode):
        self.editMode = editMode
        self.cmbClient.setEnabled(editMode == EditMode.CreateEvent)
        self.cmbPerson.setEnabled(editMode in (EditMode.CreateEvent, EditMode.EditEvent))
        self.edtSetDate.setEnabled(editMode == EditMode.CreateEvent)
        self.cmbEquipment.setEnabled(editMode in (EditMode.CreateEvent, EditMode.ReplaceEquipment))
        self.cmbObservationGroup.setEnabled(self.enableObservationGroup())
        self.edtComment.setEnabled(editMode in (EditMode.CreateEvent, EditMode.ReplaceEquipment, EditMode.EndProgram))

    def accept(self):
        try:
            if not self.validate():
                return
            if self.editMode == EditMode.CreateEvent:
                self.createEvent()
            elif self.editMode == EditMode.EditEvent:
                self.editEvent()
            elif self.editMode == EditMode.ReplaceEquipment:
                self.replaceEquipment()
            elif self.editMode == EditMode.EndProgram:
                self.endProgram()
        except Exception as e:
            QtGui.QMessageBox.critical(self, u'Произошла ошибка', u'Программа по ДН не создана. Закройте текущую и создайте новую.\n'+e.message, QtGui.QMessageBox.Close)
            QtGui.qApp.logCurrentException()

    def validate(self):
        if not self.validateEventFields():
            return False
        if self.editMode == EditMode.CreateEvent and not self.validateClientFields():
            return False
        if self.editMode == EditMode.ReplaceEquipment and not self.validateEquipmentChanged():
            return False
        return True
    
    def validateEventFields(self):
        missingFields = []
        if self.editMode == EditMode.CreateEvent and not self.cmbClient.value():
            missingFields.append(u'- Пациент')
        if self.editMode in (EditMode.CreateEvent, EditMode.EditEvent) and not self.cmbPerson.value():
            missingFields.append(u'- Лечащий врач')
        if self.editMode in (EditMode.CreateEvent, EditMode.ReplaceEquipment) and not self.cmbEquipment.value():
            missingFields.append(u'- Модель прибора ДН')
        if self.enableObservationGroup() and self.observationGroupActual and self.cmbObservationGroup.currentIndex() < 1:
            missingFields.append(u'- Группа наблюдения')
        if self.editMode == EditMode.ReplaceEquipment and not unicode(self.edtComment.toPlainText()):
            missingFields.append(u'- Комментарий')
        if missingFields:
            QtGui.QMessageBox.critical(self, u'Программа ДН', u'Не заполнены обязательные поля:\n' + u'\n'.join(missingFields))
            return False
        return True
    
    def validateClientFields(self):
        db = QtGui.qApp.db
        missingFields = []
        clientId = self.cmbClient.value()
        clientRecord = db.getRecord('Client', ['lastName', 'firstName', 'birthDate', 'SNILS', 'sex'], clientId)
        if not forceString(clientRecord.value('lastName')):
            missingFields.append(u'- Фамилия')
        if not forceString(clientRecord.value('firstName')):
            missingFields.append(u'- Имя')
        if not forceDate(clientRecord.value('birthDate')).isValid():
            missingFields.append(u'- Дата рождения')
        if not forceString(clientRecord.value('SNILS')):
            missingFields.append(u'- СНИЛС')
        if forceInt(clientRecord.value('sex')) < 1:
            missingFields.append(u'- Пол')
        documentRecord = db.getRecordEx('ClientDocument', cols=['serial', 'number', 'date', 'origin'], where=[
            'ClientDocument.client_id = ' + str(clientId),
            'ClientDocument.deleted = 0',
            'ClientDocument.documentType_id = (select id from rbDocumentType where regionalCode = 14)'
        ], order='ClientDocument.id desc')
        if not documentRecord or not forceString(documentRecord.value('serial')):
            missingFields.append(u'- Паспорт: серия')
        if not documentRecord or not forceString(documentRecord.value('number')):
            missingFields.append(u'- Паспорт: номер')
        if not documentRecord or not forceDate(documentRecord.value('date')).isValid():
            missingFields.append(u'- Паспорт: дата выдачи')
        if not documentRecord or not forceString(documentRecord.value('origin')):
            missingFields.append(u'- Паспорт: кем выдан')
        policyTable = db.table('ClientPolicy')
        policyTable = policyTable.leftJoin(db.table('rbPolicyKind'), 'rbPolicyKind.id = ClientPolicy.policyKind_id')
        policyTable = policyTable.leftJoin(db.table('Organisation').alias('Insurer'), 'Insurer.id = ClientPolicy.insurer_id')
        policyTable = policyTable.leftJoin(db.table('Organisation_Identification').alias('Insurer_Identification'), [
            'Insurer_Identification.master_id = Insurer.id',
            "Insurer_Identification.system_id = (select id from rbAccountingSystem where rbAccountingSystem.urn = 'urn:oid:1.2.643.5.1.13.2.1.1.635')",
            'Insurer_Identification.deleted = 0'
        ])
        policyRecord = db.getRecordEx(policyTable, cols=[
            'ClientPolicy.number',
            'Insurer_Identification.`value` as insurerCode',
            'Insurer.fullName as insurerName'
        ], where=[
            'ClientPolicy.id = getClientPolicyId(' + str(clientId) + ', 1)'
        ])
        if not policyRecord or not forceString(policyRecord.value('number')):
            missingFields.append(u'- Полис: номер')
        if not policyRecord or not forceString(policyRecord.value('insurerCode')):
            missingFields.append(u'- Полис: код СМО')
        if not policyRecord or not forceString(policyRecord.value('insurerName')):
            missingFields.append(u'- Полис: наименование СМО')
        contactTable = db.table('ClientContact')
        contactTable = contactTable.leftJoin(db.table('rbContactType'), 'rbContactType.id = ClientContact.contactType_id')
        contactRecords = db.getRecordList(contactTable, cols=['ClientContact.contact'], where=[
            'ClientContact.client_id = ' + str(clientId),
            'ClientContact.deleted = 0',
            u"rbContactType.name like '%телефон%'"
        ])
        hasValidPhone = False
        hasInvalidPhone = False
        for contactRecord in contactRecords:
            if len(re.findall(r'[\d]', forceString(contactRecord.value('contact')))) >= 11:
                hasValidPhone = True
            else:
                hasInvalidPhone = True
        if not hasValidPhone:
            if hasInvalidPhone:
                missingFields.append(u'- Неправильный формат номера телефона (должно быть минимум 11 цифр)')
            else:
                missingFields.append(u'- Номер телефона')
        if missingFields:
            errorMessage = u'В карте пациента не заполнены обязательные поля:\n' + u'\n'.join(missingFields)
            if QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry]):
                errorMessage += u'\nБудет выполнен переход в регистрационную карту пациента.'
                QtGui.QMessageBox.critical(self, u'Программа ДН', errorMessage)
                dialog = CClientEditDialog(self)
                try:
                    dialog.load(clientId)
                    dialog.exec_()
                finally:
                    dialog.deleteLater()
            else:
                QtGui.QMessageBox.critical(self, u'Программа ДН', errorMessage)
            return False
        return True

    def validateEquipmentChanged(self):
        if self.cmbEquipment.value() == self.oldEquipmentId:
            QtGui.QMessageBox.critical(self, u'Программа ДН', u'При замене оборудования должно быть выбрано другое оборудование!')
            return False
        return True
    
    def createEvent(self):
        params = {}
        params['client_id'] = self.cmbClient.value()
        params['person_id'] = self.cmbPerson.value()
        params['equipment_id'] = self.cmbEquipment.value()
        params['set_date'] = unicode(self.edtSetDate.date().toString(Qt.ISODate))
        if self.cmbObservationGroup.isEnabled():
            params['observation_group'] = self.cmbObservationGroup.currentIndex()
        params['comment'] = unicode(self.edtComment.toPlainText())
        self.eventId = self.pyServices.createServiceRequest(params)
        CDialogBase.accept(self)
    
    def editEvent(self):
        params = {}
        params['event_id'] = self.eventId
        params['person_id'] = self.cmbPerson.value()
        if self.cmbObservationGroup.isEnabled():
            params['observation_group'] = self.cmbObservationGroup.currentIndex()
        self.pyServices.editServiceRequest(params)
        CDialogBase.accept(self)
    
    def replaceEquipment(self):
        params = {}
        params['event_id'] = self.eventId
        params['equipment_id'] = self.cmbEquipment.value()
        params['comment'] = unicode(self.edtComment.toPlainText())
        self.pyServices.createProcedure(params)
        CDialogBase.accept(self)
    
    def endProgram(self):
        params = {}
        params['event_id'] = self.eventId
        params['comment'] = unicode(self.edtComment.toPlainText())
        self.pyServices.createDeviceUseStatement(params)
        CDialogBase.accept(self)
    
    def setEventId(self, eventId):
        self.eventId = eventId
        if eventId is None:
            self.lblEquipmentStatusText.setText('')
            self.cmbClient.setValue(None)
            self.cmbPerson.setValue(None)
            self.updateEquipmentFilter(None, None)
            self.cmbEquipment.setValue(None)
            self.edtSetDate.setDate(QDate.currentDate())
            self.cmbObservationGroup.setCurrentIndex(-1)
            self.edtComment.setPlainText('')
            return
        db = QtGui.qApp.db
        eventTypeId = forceRef(db.translate('EventType', 'code', 'SYSDM', 'id', nonDeleted=True))
        if not eventTypeId:
            raise Exception(u'Не найден тип события "SYSDM"')
        actionTypeMonitoringId = forceRef(db.translate('ActionType', 'flatCode', 'monitoring', 'id', nonDeleted=True))
        if not actionTypeMonitoringId:
            raise Exception(u'Не найден тип действия "monitoring"')
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableAPTEquipment = db.table('ActionPropertyType').alias('APTEquipment')
        tableAPEquipment = db.table('ActionProperty').alias('APEquipment')
        tableAPVEquipment = db.table('ActionProperty_rbEquipment').alias('APVEquipment')
        tableEquipment = db.table('rbEquipment')
        tableEquipmentType = db.table('rbEquipmentType')
        tableEquipmentClass = db.table('rbEquipmentClass')
        tableAPTObservationGroup = db.table('ActionPropertyType').alias('APTObservationGroup')
        tableAPObservationGroup = db.table('ActionProperty').alias('APObservationGroup')
        tableAPVObservationGroup = db.table('ActionProperty_String').alias('APVObservationGroup')
        tableAPTComment = db.table('ActionPropertyType').alias('APTComment')
        tableAPComment = db.table('ActionProperty').alias('APComment')
        tableAPVComment = db.table('ActionProperty_String').alias('APVComment')
        tableAPTEquipmentStatus = db.table('ActionPropertyType').alias('APTEquipmentStatus')
        tableAPEquipmentStatus = db.table('ActionProperty').alias('APEquipmentStatus')
        tableAPVEquipmentStatus = db.table('ActionProperty_String').alias('APVEquipmentStatus')
        query = tableEvent.leftJoin(tableAction, 
            u'''Action.id = (SELECT a.id
            FROM Action a
            WHERE a.event_id = Event.id
                AND a.actionType_id = {actionTypeMonitoringId}
                AND a.deleted = 0
            ORDER BY a.id desc
            LIMIT 1)'''.format(actionTypeMonitoringId=actionTypeMonitoringId)
        )
        query = query.leftJoin(tableAPTEquipment, [
            tableAPTEquipment['actionType_id'].eq(tableAction['actionType_id']),
            tableAPTEquipment['deleted'].eq(0),
            tableAPTEquipment['name'].eq(u'Модель прибора дистанционного наблюдения')
        ])
        query = query.leftJoin(tableAPEquipment, [
            tableAPEquipment['action_id'].eq(tableAction['id']),
            tableAPEquipment['type_id'].eq(tableAPTEquipment['id']),
            tableAPEquipment['deleted'].eq(0)
        ])
        query = query.leftJoin(tableAPVEquipment, tableAPVEquipment['id'].eq(tableAPEquipment['id']))
        query = query.leftJoin(tableEquipment, tableEquipment['id'].eq(tableAPVEquipment['value']))
        query = query.leftJoin(tableEquipmentType, tableEquipmentType['id'].eq(tableEquipment['equipmentType_id']))
        query = query.leftJoin(tableEquipmentClass, tableEquipmentClass['id'].eq(tableEquipmentType['class_id']))
        query = query.leftJoin(tableAPTObservationGroup, [
            tableAPTObservationGroup['actionType_id'].eq(tableAction['actionType_id']),
            tableAPTObservationGroup['deleted'].eq(0),
            tableAPTObservationGroup['name'].eq(u'Группа наблюдения')
        ])
        query = query.leftJoin(tableAPObservationGroup, [
            tableAPObservationGroup['action_id'].eq(tableAction['id']),
            tableAPObservationGroup['type_id'].eq(tableAPTObservationGroup['id']),
            tableAPObservationGroup['deleted'].eq(0)
        ])
        query = query.leftJoin(tableAPVObservationGroup, tableAPVObservationGroup['id'].eq(tableAPObservationGroup['id']))
        query = query.leftJoin(tableAPTComment, [
            tableAPTComment['actionType_id'].eq(tableAction['actionType_id']),
            tableAPTComment['deleted'].eq(0),
            tableAPTComment['name'].eq(u'Комментарий')
        ])
        query = query.leftJoin(tableAPComment, [
            tableAPComment['action_id'].eq(tableAction['id']),
            tableAPComment['type_id'].eq(tableAPTComment['id']),
            tableAPComment['deleted'].eq(0)
        ])
        query = query.leftJoin(tableAPVComment, tableAPVComment['id'].eq(tableAPComment['id']))
        query = query.leftJoin(tableAPTEquipmentStatus, [
            tableAPTEquipmentStatus['actionType_id'].eq(tableAction['actionType_id']),
            tableAPTEquipmentStatus['deleted'].eq(0),
            tableAPTEquipmentStatus['name'].eq(u'Действия с оборудованием')
        ])
        query = query.leftJoin(tableAPEquipmentStatus, [
            tableAPEquipmentStatus['action_id'].eq(tableAction['id']),
            tableAPEquipmentStatus['type_id'].eq(tableAPTEquipmentStatus['id']),
            tableAPEquipmentStatus['deleted'].eq(0)
        ])
        query = query.leftJoin(tableAPVEquipmentStatus, tableAPVEquipmentStatus['id'].eq(tableAPEquipmentStatus['id']))
        cols = [
            tableEvent['client_id'],
            tableAction['person_id'],
            tableEvent['setDate'],
            tableEquipment['id'].alias('equipment_id'),
            tableEquipmentClass['code'].alias('equipmentClass_code'),
            tableAPVObservationGroup['value'].alias('observationGroup'),
            tableAPVEquipmentStatus['value'].alias('equipmentStatus'),
        ]
        cond = [
            tableEvent['id'].eq(eventId)
        ]
        record = db.getRecordEx(query, cols, where=cond)
        equipmentStatus = forceString(record.value('equipmentStatus'))
        self.lblEquipmentStatusText.setText(equipmentStatus)
        clientId = forceRef(record.value('client_id'))
        self.cmbClient.setValue(clientId)
        personId = forceRef(record.value('person_id'))
        self.cmbPerson.setValue(personId)
        setDate = forceDate(record.value('setDate'))
        self.edtSetDate.setDate(setDate)
        equipmentId = forceRef(record.value('equipment_id'))
        self.oldEquipmentId = equipmentId
        equipmentClassCode = forceString(record.value('equipmentClass_code'))
        self.updateEquipmentFilter(equipmentId, equipmentClassCode)
        self.cmbEquipment.setValue(equipmentId)
        observationGroup = forceString(record.value('observationGroup'))
        self.cmbObservationGroup.setCurrentIndex(self.cmbObservationGroup.findText(observationGroup))
        comment = forceString(record.value('comment'))
        self.edtComment.setPlainText(comment)


    def updateEquipmentFilter(self, equipmentId, equipmentClassCode):
        classFilter = ''
        equipmentFilter = u"""
            exists (
                select rbEquipment_Identification.`value`
                from rbEquipment_Identification
                where rbEquipment_Identification.master_id = rbEquipment.id
                    and rbEquipment_Identification.system_id = {systemId}
            )
            and not exists (
                select Event.id
                from Event
                    inner join Action on Action.id = (
                        select a.id
                        from Action a
                        where a.event_id = Event.id
                            and a.actionType_id = (select ActionType.id from ActionType where ActionType.deleted = 0 and ActionType.flatCode = 'monitoring')
                            and a.deleted = 0
                        order by a.id desc
                        limit 1
                    )
                    inner join ActionPropertyType as APTEquipment on APTEquipment.actionType_id = Action.actionType_id
                        and APTEquipment.name = 'Модель прибора дистанционного наблюдения'
                        and APTEquipment.deleted = 0
                    inner join ActionProperty as APEquipment on APEquipment.action_id = Action.id
                        and APEquipment.type_id = APTEquipment.id
                        and APEquipment.deleted = 0
                    inner join ActionProperty_rbEquipment as APVEquipment on APVEquipment.id = APEquipment.id
                    inner join ActionPropertyType as APTEquipmentStatus on APTEquipmentStatus.actionType_id = Action.actionType_id
                        and APTEquipmentStatus.name = 'Действия с оборудованием'
                        and APTEquipmentStatus.deleted = 0
                    inner join ActionProperty as APEquipmentStatus on APEquipmentStatus.action_id = Action.id
                        and APEquipmentStatus.type_id = APTEquipmentStatus.id
                        and APEquipmentStatus.deleted = 0
                    inner join ActionProperty_String as APVEquipmentStatus on APVEquipmentStatus.id = APEquipmentStatus.id
                where Event.deleted = 0
                    and Event.eventType_id = (select EventType.id from EventType where EventType.deleted = 0 and EventType.code = 'SYSDM')
                    and APVEquipment.`value` = rbEquipment.id
                    and APVEquipmentStatus.`value` in ('Выдача', 'Замена')
            )
        """.format(systemId=self.systemId)
        if equipmentClassCode:
            equipmentFilter += u"""
                and rbEquipment.equipmentType_id in (
                    select t.id
                    from rbEquipmentType as t
                        inner join rbEquipmentClass as c on c.id = t.class_id
                    where c.code = '{equipmentClassCode}')
            """.format(equipmentClassCode=equipmentClassCode)
        if equipmentId:
            equipmentFilter = u"rbEquipment.id = {equipmentId} or ({equipmentFilter})".format(equipmentId=equipmentId, equipmentFilter=equipmentFilter)
        self.cmbEquipment.setFilter(equipmentFilter)