# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, QObject, QVariant

from Events.CreateEvent import editEvent

from library.crbcombobox import CRBComboBox
from library.DialogBase import CConstructHelperMixin
from library.TableModel import CCol, CQueryModel, CTextCol, CTextListCol, CDateCol, CBoolCol
from library.TableView import CCenterIconDelegate
from library.Utils import formatSNILS, forceRef, forceString, forceBool, forceInt, trim, formatRecordsCount, exceptionToUnicode

from Exchange.PyServices import getPyServices, CDistantMonitoringService
from Registry.DistantMonitoringEventEditDialog import CDistantMonitoringEventEditDialog
from Users.Rights import urAdmin, urRegTabWriteEvents

from Ui_DistantMonitoringEventPage import Ui_DistantMonitoringEventPage


class CDistantMonitoringEventPage(QtGui.QWidget, Ui_DistantMonitoringEventPage, CConstructHelperMixin):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.addModels('EventList', CEventListModel(self))
        self.addModels('ActionList', CActionListModel(self))
        self.addObject('actCreateEvent', QtGui.QAction(u'Создать программу', self))
        self.addObject('actEditEvent', QtGui.QAction(u'Редактировать программу', self))
        self.addObject('actReplaceEquipment', QtGui.QAction(u'Замена оборудования', self))
        self.addObject('actEndProgram', QtGui.QAction(u'Закрытие программы и возврат оборудования', self))
        self.addObject('actOpenBrowserPatientPage', QtGui.QAction(u'Переход в СИС ДН карточка пациента', self))
        self.addObject('actOpenBrowserTasksPage', QtGui.QAction(u'Переход в СИС ДН планировщик', self))
        self.addObject('actOpenEvent', QtGui.QAction(u'Переход в служебное событие', self))
        self.addObject('actCreateSubscription', QtGui.QAction(u'Подписаться на уведомления', self))
        self.addObject('actDisableSubscription', QtGui.QAction(u'Отписаться от уведомлений', self))
        self.setupUi(self)
        self.tblEventList.addPopupAction(self.actCreateEvent)
        self.tblEventList.addPopupAction(self.actEditEvent)
        self.tblEventList.addPopupAction(self.actReplaceEquipment)
        self.tblEventList.addPopupAction(self.actEndProgram)
        self.tblEventList.addPopupAction(self.actOpenBrowserPatientPage)
        self.tblEventList.addPopupAction(self.actOpenBrowserTasksPage)
        self.tblEventList.addPopupAction(self.actOpenEvent)
        self.tblEventList.addPopupAction(self.actCreateSubscription)
        self.tblEventList.addPopupAction(self.actDisableSubscription)
        self.tblEventList.setItemDelegateForColumn(self.modelEventList.columnIndexByFieldName('notification_priority'), CCenterIconDelegate(self))
        self.connect(self.tblEventList, SIGNAL('popupMenuAboutToShow()'), self.popupMenuAboutToShow)
        self.setModels(self.tblEventList, self.modelEventList, self.selectionModelEventList)
        self.setModels(self.tblActionList, self.modelActionList, self.selectionModelActionList)
        self.filter = {}
        db = QtGui.qApp.db
        tableEquipmentClass = db.table('rbEquipmentClass')
        tableEquipmentType = db.table('rbEquipmentType')
        equipmentClassIds = db.getIdList(tableEquipmentClass, where=tableEquipmentClass['code'].inlist(['6', '12']))
        self.cmbEquipmentClass.setTable(tableEquipmentClass.name(), filter=tableEquipmentClass['id'].inlist(equipmentClassIds))
        self.cmbEquipmentClass.setShowFields(CRBComboBox.showCodeAndName)
        self.cmbEquipmentType.setTable(tableEquipmentType.name(), filter=tableEquipmentType['class_id'].inlist(equipmentClassIds))
        self.cmbEquipmentType.setShowFields(CRBComboBox.showCodeAndName)
        self.resetFilter()
        header = self.tblEventList.horizontalHeader()
        if self.modelEventList.orderColumn():
            header.setSortIndicatorShown(True)
            header.setSortIndicator(self.modelEventList.orderColumn(), self.modelEventList.sortIndicator())
        QObject.connect(header, SIGNAL('sectionClicked(int)'), self.setSort)
        self.pyServices = getPyServices(CDistantMonitoringService)
    
    @pyqtSignature('int')
    def setSort(self, colIndex):
        self.modelEventList.toggleOrder(colIndex)
        self.updateEventList()

    def updateEventList(self):
        self.modelEventList.update(self.filter)
        self.lblRecordCount.setText(formatRecordsCount(self.modelEventList.rowCount()))
        self.updateActionList()

    def updateActionList(self):
        eventRecord = self.tblEventList.currentItem()
        eventId = forceRef(eventRecord.value('id')) if eventRecord else None
        if eventId:
            self.modelActionList.update(eventId)
        else:
            self.modelActionList.clear()

    def applyFilter(self):
        self.filter = {}
        if self.chkLastName.isChecked():
            self.filter['lastName'] = trim(self.edtLastName.text())
        if self.chkFirstName.isChecked():
            self.filter['firstName'] = trim(self.edtFirstName.text())
        if self.chkPatrName.isChecked():
            self.filter['patrName'] = trim(self.edtPatrName.text())
        if self.chkBirthDate.isChecked():
            self.filter['birthDate'] = self.edtBirthDate.date()
            if self.chkBirthDateTo.isChecked():
                self.filter['birthDateTo'] = self.edtBirthDateTo.date()
        if self.chkSex.isChecked():
            self.filter['sex'] = self.cmbSex.currentIndex()
        if self.chkPerson.isChecked():
            self.filter['personId'] = self.cmbPerson.value()
        if self.chkEquipmentClass.isChecked():
            self.filter['equipmentClassId'] = self.cmbEquipmentClass.value()
        if self.chkEquipmentType.isChecked():
            self.filter['equipmentTypeId'] = self.cmbEquipmentType.value()
        if self.chkEquipmentStatus.isChecked():
            self.filter['equipmentStatus'] = unicode(self.cmbEquipmentStatus.currentText())
        if self.chkEventSetDate.isChecked():
            self.filter['eventSetDate'] = self.edtEventSetDate.date()
            if self.chkEventSetDateTo.isChecked():
                self.filter['eventSetDateTo'] = self.edtEventSetDateTo.date()
        if self.chkEventExecDate.isChecked():
            self.filter['eventExecDate'] = self.edtEventExecDate.date()
            if self.chkEventExecDateTo.isChecked():
                self.filter['eventExecDateTo'] = self.edtEventExecDateTo.date()
        if self.chkEventStatus.isChecked():
            self.filter['eventStatus'] = self.cmbEventStatus.currentIndex()
        if self.chkObservationGroup.isChecked():
            self.filter['observationGroup'] = unicode(self.cmbObservationGroup.currentText())
        if self.chkActiveNotifications.isChecked():
            self.filter['activeNotifications'] = self.cmbActiveNotifications.currentIndex()
        if self.chkSubscription.isChecked():
            self.filter['subscription'] = self.cmbSubscription.currentIndex()
        self.updateEventList()

    def resetFilter(self):
        self.chkLastName.setChecked(False)
        self.edtLastName.setText('')
        self.chkFirstName.setChecked(False)
        self.edtFirstName.setText('')
        self.chkPatrName.setChecked(False)
        self.edtPatrName.setText('')
        self.chkBirthDate.setChecked(False)
        self.chkBirthDateTo.setChecked(False)
        self.chkSex.setChecked(False)
        self.chkPerson.setChecked(False)
        self.chkEquipmentClass.setChecked(False)
        self.cmbEquipmentClass.setValue(None)
        self.chkEquipmentType.setChecked(False)
        self.cmbEquipmentType.setValue(None)
        self.chkEquipmentStatus.setChecked(False)
        self.chkEventSetDate.setChecked(False)
        self.chkEventSetDateTo.setChecked(False)
        self.chkEventExecDate.setChecked(False)
        self.chkEventExecDateTo.setChecked(False)
        self.chkEventStatus.setChecked(False)
        self.chkObservationGroup.setChecked(False)
        self.chkActiveNotifications.setChecked(False)
        self.chkSubscription.setChecked(False)
        self.applyFilter()

    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxFilter_clicked(self, button):
        buttonCode = self.buttonBoxFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.applyFilter()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetFilter()

    def popupMenuAboutToShow(self):
        record = self.tblEventList.currentItem()
        isActive = record.isNull('execDate') if record else None
        hasSubscription = forceInt(record.value('subscription_status')) == 1 if record else None
        self.actCreateEvent.setEnabled(True)
        self.actEditEvent.setEnabled(bool(record and isActive))
        self.actReplaceEquipment.setEnabled(bool(record and isActive))
        self.actEndProgram.setEnabled(bool(record and isActive))
        self.actOpenBrowserPatientPage.setEnabled(bool(record))
        self.actOpenBrowserTasksPage.setEnabled(bool(record))
        self.actOpenEvent.setEnabled(bool(record and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteEvents])))
        self.actCreateSubscription.setVisible(bool(record and not hasSubscription))
        self.actDisableSubscription.setVisible(False)
    
    @pyqtSignature('')
    def on_actCreateEvent_triggered(self):
        dialog = CDistantMonitoringEventEditDialog(self)
        if dialog.execCreateEvent():
            eventId = dialog.eventId
            QtGui.QMessageBox.information(self, u'Сервис дистанционного наблюдения', u'Программа ДН успешно создана', QtGui.QMessageBox.Ok)
            try:
                self.pyServices.createSubscription(eventId)
            except Exception as e:
                QtGui.QMessageBox.critical(self, u'Произошла ошибка при подписке на уведомления', exceptionToUnicode(e), QtGui.QMessageBox.Close)
            self.updateEventList()
    
    @pyqtSignature('')
    def on_actEditEvent_triggered(self):
        record = self.tblEventList.currentItem()
        eventId = forceRef(record.value('id'))
        dialog = CDistantMonitoringEventEditDialog(self)
        if dialog.execEditEvent(eventId):
            QtGui.QMessageBox.information(self, u'Сервис дистанционного наблюдения', u'Данные программы ДН изменены', QtGui.QMessageBox.Ok)
            self.updateEventList()
    
    @pyqtSignature('')
    def on_actReplaceEquipment_triggered(self):
        record = self.tblEventList.currentItem()
        eventId = forceRef(record.value('id'))
        dialog = CDistantMonitoringEventEditDialog(self)
        if dialog.execReplaceEquipment(eventId):
            QtGui.QMessageBox.information(self, u'Сервис дистанционного наблюдения', u'Оборудование успешно заменено', QtGui.QMessageBox.Ok)
            self.updateEventList()
    
    @pyqtSignature('')
    def on_actEndProgram_triggered(self):
        record = self.tblEventList.currentItem()
        eventId = forceRef(record.value('id'))
        dialog = CDistantMonitoringEventEditDialog(self)
        if dialog.execEndProgram(eventId):
            QtGui.QMessageBox.information(self, u'Сервис дистанционного наблюдения', u'Программа успешно закрыта', QtGui.QMessageBox.Ok)
            self.updateEventList()
    
    @pyqtSignature('')
    def on_actOpenBrowserPatientPage_triggered(self):
        record = self.tblEventList.currentItem()
        personSnils = forceString(record.value('person_SNILS'))
        clientSnils = forceString(record.value('client_SNILS'))
        self.pyServices.openWebApp(personSnils, clientSnils)
    
    @pyqtSignature('')
    def on_actOpenBrowserTasksPage_triggered(self):
        record = self.tblEventList.currentItem()
        personSnils = forceString(record.value('person_SNILS'))
        self.pyServices.openWebApp(personSnils)
    
    @pyqtSignature('')
    def on_actOpenEvent_triggered(self):
        record = self.tblEventList.currentItem()
        eventId = forceRef(record.value('id'))
        eventId = editEvent(self, eventId)
        self.updateEventList()
    
    @pyqtSignature('')
    def on_actCreateSubscription_triggered(self):
        record = self.tblEventList.currentItem()
        eventId = forceRef(record.value('id'))
        try:
            self.pyServices.createSubscription(eventId)
            QtGui.QMessageBox.information(self, u'Сервис дистанционного наблюдения', u'Подписка успешно создана', QtGui.QMessageBox.Ok)
            self.updateEventList()
        except Exception as e:
            QtGui.QMessageBox.critical(self, u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)
    
    @pyqtSignature('')
    def on_actDisableSubscription_triggered(self):
        record = self.tblEventList.currentItem()
        eventId = forceRef(record.value('id'))
        try:
            self.pyServices.disableSubscription(eventId)
            QtGui.QMessageBox.information(self, u'Сервис дистанционного наблюдения', u'Подписка успешно отключена', QtGui.QMessageBox.Ok)
            self.updateEventList()
        except Exception as e:
            QtGui.QMessageBox.critical(self, u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelEventList_currentRowChanged(self, current, previous):
        self.updateActionList()
    
    @pyqtSignature('bool')
    def on_chkBirthDate_toggled(self, checked):
        self.edtBirthDateTo.setEnabled(checked and self.chkBirthDateTo.isChecked())
    
    @pyqtSignature('bool')
    def on_chkEventSetDate_toggled(self, checked):
        self.edtEventSetDateTo.setEnabled(checked and self.chkEventSetDateTo.isChecked())
    
    @pyqtSignature('bool')
    def on_chkEventExecDate_toggled(self, checked):
        self.edtEventExecDateTo.setEnabled(checked and self.chkEventExecDateTo.isChecked())


class CEventListModel(CQueryModel):
    class CNotificationCol(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'c')
        
        def decoration(self, values):
            priority = forceInt(values[0])
            if priority == 1:
                return QVariant(QtGui.QIcon(':/new/prefix1/icons/bell_1.png'))
            elif priority == 2:
                return QVariant(QtGui.QIcon(':/new/prefix1/icons/bell_2.png'))
            elif priority == 3:
                return QVariant(QtGui.QIcon(':/new/prefix1/icons/bell_3.png'))
            else:
                return QVariant()

    def __init__(self, parent):
        CQueryModel.__init__(self, parent)
        self.addColumn(CEventListModel.CNotificationCol(u'Оповещение', ['notification_priority'], 20))
        self.addColumn(CTextListCol(u'ФИО пациента', ['client_lastName', 'client_firstName', 'client_patrName'], 20))
        self.addColumn(CDateCol(u'Дата рождения пациента', ['client_birthDate'], 20))
        self.addColumn(CTextCol(u'Телефон пациента', ['clientContact_contact'], 20))
        self.addColumn(CTextListCol(u'ФИО лечащего врача', ['person_lastName', 'person_firstName', 'person_patrName'], 20))
        self.addColumn(CDateCol(u'Дата начала ДН', ['setDate'], 20))
        self.addColumn(CDateCol(u'Дата окончания ДН', ['execDate'], 20))
        self.addColumn(CTextCol(u'Модель прибора ДН', ['equipment_name'], 20))
        self.addColumn(CTextCol(u'Группа наблюдения', ['observationGroup'], 20))
        self.addColumn(CBoolCol(u'Сервисная подписка на уведомления', ['subscription_status'], 20))
        self.addColumn(CTextCol(u'Комментарий', ['comment'], 20))
        self.setOrder('client_lastName')
        self.recordInfo = {}

    def update(self, filter):
        db = QtGui.qApp.db
        eventTypeId = forceRef(db.translate('EventType', 'code', 'SYSDM', 'id', nonDeleted=True))
        if not eventTypeId:
            raise Exception(u'Не найден тип события "SYSDM"')
        actionTypeMonitoringId = forceRef(db.translate('ActionType', 'flatCode', 'monitoring', 'id', nonDeleted=True))
        if not actionTypeMonitoringId:
            raise Exception(u'Не найден тип действия "monitoring"')
        tableEvent = db.table('Event')
        tableNotification = db.table('UserNotification')
        tableClient = db.table('Client')
        tableClientContact = db.table('ClientContact')
        tableAction = db.table('Action')
        tablePerson = db.table('Person')
        tableAPTEquipmentStatus = db.table('ActionPropertyType').alias('APTEquipmentStatus')
        tableAPEquipmentStatus = db.table('ActionProperty').alias('APEquipmentStatus')
        tableAPVEquipmentStatus = db.table('ActionProperty_String').alias('APVEquipmentStatus')
        tableAPTEquipment = db.table('ActionPropertyType').alias('APTEquipment')
        tableAPEquipment = db.table('ActionProperty').alias('APEquipment')
        tableAPVEquipment = db.table('ActionProperty_rbEquipment').alias('APVEquipment')
        tableEquipment = db.table('rbEquipment')
        tableEquipmentType = db.table('rbEquipmentType')
        tableAPTObservationGroup = db.table('ActionPropertyType').alias('APTObservationGroup')
        tableAPObservationGroup = db.table('ActionProperty').alias('APObservationGroup')
        tableAPVObservationGroup = db.table('ActionProperty_String').alias('APVObservationGroup')
        tableAPTComment = db.table('ActionPropertyType').alias('APTComment')
        tableAPComment = db.table('ActionProperty').alias('APComment')
        tableAPVComment = db.table('ActionProperty_String').alias('APVComment')
        tableSubscription = db.table('DistantMonitoringSubscription')
        query = tableEvent.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        query = query.leftJoin(tableNotification, 
            u'''UserNotification.id = (SELECT un.id
            FROM UserNotification as un
                INNER JOIN UserNotification_Event as une on une.userNotification_id = un.id
            WHERE une.event_id = Event.id
                AND un.status = 1
            ORDER BY un.priority desc
            LIMIT 1)'''
        )
        query = query.leftJoin(tableClientContact, 
            u'''ClientContact.id = (SELECT cc.id
            FROM ClientContact cc
                LEFT JOIN rbContactType as ct on ct.id = cc.contactType_id
            WHERE cc.client_id = Client.id
                AND cc.deleted = 0
                AND ct.name = 'мобильный телефон'
            ORDER BY cc.id desc
            LIMIT 1)'''
        )
        query = query.leftJoin(tableAction, 
            u'''Action.id = (SELECT a.id
            FROM Action a
            WHERE a.event_id = Event.id
                AND a.actionType_id = {actionTypeMonitoringId}
                AND a.deleted = 0
            ORDER BY a.id desc
            LIMIT 1)'''.format(actionTypeMonitoringId=actionTypeMonitoringId)
        )
        query = query.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
        if 'equipmentStatus' in filter:
            query = query.leftJoin(tableAPTEquipmentStatus, [
                tableAPTEquipmentStatus['actionType_id'].eq(tableAction['actionType_id']),
                tableAPTEquipmentStatus['deleted'].eq(0),
                tableAPTEquipmentStatus['name'].eq(u'Модель прибора дистанционного наблюдения')
            ])
            query = query.leftJoin(tableAPEquipmentStatus, [
                tableAPEquipmentStatus['action_id'].eq(tableAction['id']),
                tableAPEquipmentStatus['type_id'].eq(tableAPTEquipmentStatus['id']),
                tableAPEquipmentStatus['deleted'].eq(0)
            ])
            query = query.leftJoin(tableAPVEquipmentStatus, tableAPVEquipmentStatus['id'].eq(tableAPEquipmentStatus['id']))
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
        if 'equipmentClassId' in filter:
            query = query.leftJoin(tableEquipmentType, tableEquipmentType['id'].eq(tableEquipment['equipmentType_id']))
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
        query = query.leftJoin(tableSubscription, tableSubscription['event_id'].eq(tableEvent['id']))
        cols = [
            tableEvent['id'],
            tableNotification['priority'].alias('notification_priority'),
            tableClient['lastName'].alias('client_lastName'),
            tableClient['firstName'].alias('client_firstName'),
            tableClient['patrName'].alias('client_patrName'),
            tableClient['birthDate'].alias('client_birthDate'),
            tableClient['SNILS'].alias('client_SNILS'),
            tableClientContact['contact'].alias('clientContact_contact'),
            tablePerson['lastName'].alias('person_lastName'),
            tablePerson['firstName'].alias('person_firstName'),
            tablePerson['patrName'].alias('person_patrName'),
            tablePerson['SNILS'].alias('person_SNILS'),
            tableEvent['setDate'],
            tableEvent['execDate'],
            tableEquipment['name'].alias('equipment_name'),
            tableAPVObservationGroup['value'].alias('observationGroup'),
            tableAPVComment['value'].alias('comment'),
            tableSubscription['status'].alias('subscription_status')
        ]
        cond = [
            tableEvent['deleted'].eq(0),
            tableEvent['eventType_id'].eq(eventTypeId)
        ]
        if 'lastName' in filter:
            if filter['lastName']:
                cond.append(tableClient['lastName'].contain(filter['lastName']))
            else:
                cond.append(tableClient['lastName'].eq(''))
        if 'firstName' in filter:
            if filter['firstName']:
                cond.append(tableClient['firstName'].contain(filter['firstName']))
            else:
                cond.append(tableClient['firstName'].eq(''))
        if 'patrName' in filter:
            if filter['patrName']:
                cond.append(tableClient['patrName'].contain(filter['patrName']))
            else:
                cond.append(tableClient['patrName'].eq(''))
        if 'birthDate' in filter:
            if 'birthDateTo' in filter:
                cond.append(tableClient['birthDate'].ge(filter['birthDate']))
                cond.append(tableClient['birthDate'].le(filter['birthDateTo']))
            else:
                cond.append(tableClient['birthDate'].eq(filter['birthDate']))
        if 'sex' in filter:
            cond.append(tableClient['sex'].eq(filter['sex']))
        if 'personId' in filter:
            cond.append(tableAction['person_id'].eq(filter['personId']))
        if 'equipmentClassId' in filter:
            cond.append(tableEquipmentType['class_id'].eq(filter['equipmentClassId']))
        if 'equipmentTypeId' in filter:
            cond.append(tableEquipment['equipmentType_id'].eq(filter['equipmentTypeId']))
        if 'equipmentStatus' in filter:
            cond.append(tableAPVEquipmentStatus['value'].eq(filter['equipmentStatus']))
        if 'eventSetDate' in filter:
            if 'eventSetDateTo' in filter:
                cond.append(tableEvent['setDate'].ge(filter['eventSetDate']))
                cond.append(tableEvent['setDate'].le(filter['eventSetDateTo']))
            else:
                cond.append(tableEvent['setDate'].eq(filter['eventSetDate']))
        if 'eventExecDate' in filter:
            if 'eventExecDateTo' in filter:
                cond.append(tableEvent['execDate'].ge(filter['eventExecDate']))
                cond.append(tableEvent['execDate'].le(filter['eventExecDateTo']))
            else:
                cond.append(tableEvent['execDate'].eq(filter['eventExecDate']))
        if 'eventStatus' in filter:
            if filter['eventStatus'] == 0:
                cond.append(tableEvent['execDate'].isNull())
            elif filter['eventStatus'] == 1:
                cond.append(tableEvent['execDate'].isNotNull())
        if 'observationGroup' in filter:
            cond.append(tableAPVObservationGroup['value'].eq(filter['observationGroup']))
        if 'activeNotifications' in filter:
            if filter['activeNotifications'] == 0:
                cond.append(tableNotification['id'].isNull())
            elif filter['activeNotifications'] == 1:
                cond.append(tableNotification['id'].isNotNull())
        if 'subscription' in filter:
            if filter['subscription'] == 0:
                cond.append(tableSubscription['id'].isNull())
            elif filter['subscription'] == 1:
                cond.append(tableSubscription['id'].isNotNull())
        order = self.formatOrderBy({
            'notification_priority': tableNotification['priority'],
            'client_lastName': [tableClient['lastName'], tableClient['firstName'], tableClient['patrName']],
            'client_birthDate': tableClient['birthDate'],
            'clientContact_contact': tableClientContact['contact'],
            'person_lastName': [tablePerson['lastName'], tablePerson['firstName'], tablePerson['patrName']],
            'setDate': tableEvent['setDate'],
            'execDate': tableEvent['execDate'],
            'equipment_id': tableAPVEquipment['value'],
            'observationGroup': tableAPVObservationGroup['value'],
            'comment': tableAPVComment['value'],
        })
        records = db.getRecordList(query, cols=cols, where=cond, order=order)
        self.setRecords(records)
    
    def data(self, index, role):
        column = index.column()
        row = index.row()
        if role == Qt.DecorationRole and column == self.columnIndexByFieldName('notification_priority'):
            (col, values) = self.getRecordValues(column, row)
            return col.decoration(values)
        elif role == Qt.BackgroundRole:
            return self.getBackgroundColor(row)
        return CQueryModel.data(self, index, role)
    
    def getBackgroundColor(self, row):
        record = self._records[row]
        priority = forceInt(record.value('notification_priority'))
        if priority == 1:
            return QVariant(QtGui.QColor(224, 255, 224))
        elif priority == 2:
            return QVariant(QtGui.QColor(255, 255, 200))
        elif priority == 3:
            return QVariant(QtGui.QColor(255, 192, 192))
        else:
            return QVariant()


class CActionListModel(CQueryModel):
    def __init__(self, parent):
        CQueryModel.__init__(self, parent)
        self.addColumn(CDateCol(u'Дата', ['begDate'], 20))
        self.addColumn(CTextCol(u'Действие', ['equipmentStatus'], 20))
        self.addColumn(CTextCol(u'Модель прибора', ['equipment_name'], 20))
        self.addColumn(CTextCol(u'Комментарий', ['comment'], 20))

    def update(self, eventId):
        db = QtGui.qApp.db
        actionTypeMonitoringId = forceRef(db.translate('ActionType', 'flatCode', 'monitoring', 'id', nonDeleted=True))
        if not actionTypeMonitoringId:
            raise Exception(u'Не найден тип действия "monitoring"')
        tableAction = db.table('Action')
        tableAPTEquipment = db.table('ActionPropertyType').alias('APTEquipment')
        tableAPEquipment = db.table('ActionProperty').alias('APEquipment')
        tableAPVEquipment = db.table('ActionProperty_rbEquipment').alias('APVEquipment')
        tableAPTEquipmentStatus = db.table('ActionPropertyType').alias('APTEquipmentStatus')
        tableAPEquipmentStatus = db.table('ActionProperty').alias('APEquipmentStatus')
        tableAPVEquipmentStatus = db.table('ActionProperty_String').alias('APVEquipmentStatus')
        tableEquipment = db.table('rbEquipment')
        tableAPTComment = db.table('ActionPropertyType').alias('APTComment')
        tableAPComment = db.table('ActionProperty').alias('APComment')
        tableAPVComment = db.table('ActionProperty_String').alias('APVComment')
        query = tableAction.leftJoin(tableAPTEquipmentStatus, [
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
        cols = [
            tableAction['id'],
            tableAction['begDate'],
            tableAPVEquipmentStatus['value'].alias('equipmentStatus'),
            tableEquipment['name'].alias('equipment_name'),
            tableAPVComment['value'].alias('comment'),
        ]
        cond = [
            tableAction['event_id'].eq(eventId),
            tableAction['actionType_id'].eq(actionTypeMonitoringId),
            tableAction['deleted'].eq(0),
        ]
        records = db.getRecordList(query, cols=cols, where=cond, order='Action.begDate')
        self.setRecords(records)
    
    def clear(self):
        self.setRecords([])