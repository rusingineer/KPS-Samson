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
import json
import urlparse

import requests
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, QDate, QVariant, pyqtSignature, SIGNAL, QDateTime

from Registry.ClientEditDialog import CClientEditDialog
from Registry.ClientSearchDialog import CExternalClientSearchDialog
from Registry.Ui_AttachOnlineReasonReject import Ui_ReasonRejectDialog
from Registry.Ui_AttachOnlineService import Ui_AttachOnlineServiceDialog
from Reports.ReportView import CReportViewDialog
from Reports.ReportBase import createTable, CReportBase
from Users.Rights import urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry
from library.DialogBase import CDialogBase
from library.InDocTable import CRecordListModel, CInDocTableCol, CEnumInDocTableCol
from library.Utils import agreeNumberAndWord, forceString, forceInt, forceRef, forceDate, toVariant, forceBool, trim


class CAttachOnlineServiceDialog(CDialogBase, Ui_AttachOnlineServiceDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.edtFilterRequestBegDate.setDate(QDate())
        self.edtFilterRequestEndDate.setDate(QDate())
        self.edtFilterBirthDate.setDate(QDate())
        self.addModels('Statements',    CStatementsModel(self))
        self.setModels(self.tblStatements, self.modelStatements, self.selectionModelStatements)
        self.btnApplyFilters.clicked.connect(self.applyFilters)
        self.btnResetFilters.clicked.connect(self.resetFilters)
        self.btnApplyStatement.clicked.connect(self.applyStatement)
        self.btnCancelStatement.clicked.connect(self.cancelStatement)
        self.btnOpenData.clicked.connect(self.openData)
        self.btnDetachClient.clicked.connect(self.detachClient)
        self.btnNeedUpload.clicked.connect(self.uploadTasks)
        self.selectionModelStatements.currentRowChanged.connect(self.setInfoToFields)
        self.servicesURL = forceString(QtGui.qApp.getGlobalPreference('23:servicesURL'))
        self.tblStatements.enableColsHide()
        self.tblStatements.enableColsMove()
        self.connect(self.tblStatements.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sortByColumn)
        self.__sortColumn = None
        self.__sortAscending = False
        self.modelStatementsDataChanged()
        if self.servicesURL:
            self.servicesURL = self.servicesURL.replace('\\\\','//')
            self.servicesURL = urlparse.urljoin(self.servicesURL, 'api/AttachMO/fhir')
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.btnDetachClient.setVisible(False)

    def applyStatement(self):
        """Кнопка Выполнить заявку"""
        model = self.tblStatements.model()
        row = self.tblStatements.currentRow()
        if row > -1:
            db = QtGui.qApp.db
            taskId = forceRef(model.value(row, 'attachTaskId'))
            self.updateData(model, row, taskId)
            status = forceString(model.value(row, 'status'))
            orderType = forceInt(model.value(row, 'order_type'))
            relatedTaskId = forceRef(db.translate('soc_AttachMO_Task', 'relatedTask_id', taskId, 'id'))
            if status == u'in-progress':
                if orderType == 1 and relatedTaskId:
                    QtGui.QMessageBox().warning(self, u'Внимание!',
                                                    u'Невозможно выполнить заявление на прикрепление, так как гражданин отозвал свое заявление!')
                    ReasonComment = u"Невозможно выполнить заявление на прикрепление, так как гражданин отозвал свое заявление"
                    ReasonCode = 1
                    self.AttachMO_Reject(taskId, ReasonComment, ReasonCode)
                    self.updateData(model, row, taskId)
                    return
                if QtGui.QMessageBox().question(self, u'Внимание!', u'Выполнить заявление?',
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:

                    clientId = forceRef(model.value(row, 'client_id'))
                    if orderType == 1:
                        # Открываем форму выбора/создания пациента
                        if not clientId:
                            # нужно допилить сохранение данных паспорта/полиса из данных сервиса
                            dialog = CAttachOnlineClientSearchDialog(self, model.items()[row])
                            if dialog.exec_():
                                clientId = dialog.clientId
                                if not dialog.createdPatient:
                                    self.editClient(clientId)
                            else:
                                # Если нажато ОТМЕНА, то выход
                                return
                        # проверки
                        stmt = u"""SELECT ca.id as clientAttachId, ca.endDate as attachEndDate, os.id as orgStructId, os.infisInternalCode, p.lastName, p.firstName, p.patrName, p.SNILS, s.name
                          FROM Client c
                          left JOIN ClientAttach ca ON c.id = ca.client_id AND ca.id = getClientAttachId(c.id, 0)
                          left JOIN OrgStructure os ON os.id = ca.orgStructure_id
                          LEFT JOIN Person_Order po on po.orgStructure_id = os.id AND po.deleted = 0 and po.type = 6 AND po.documentType_id IS NOT NULL
                                          and validFromDate <= now() and ((po.validToDate IS NULL OR LENGTH(po.validToDate) = 0) or po.validToDate >= now())
                          left JOIN Person p ON p.id = po.master_id
                          left JOIN rbSpeciality s ON p.speciality_id = s.id
                          WHERE c.id = {0} and p.retireDate is null AND p.retired = 0 limit 1""".format(clientId)

                        query = db.query(stmt)
                        clientAttachId = None
                        orgStructId = None
                        attachEndDate = None
                        practitioner = dict()
                        while query.next():
                            record = query.record()
                            clientAttachId = forceRef(record.value('clientAttachId'))
                            orgStructId = forceRef(record.value('orgStructId'))
                            attachEndDate = forceDate(record.value('attachEndDate'))

                            practitioner = {'practitionerArea': forceString(record.value('infisInternalCode')),
                                            'practitionerSurname': forceString(record.value('lastName')),
                                            'practitionerName': forceString(record.value('firstName')),
                                            'practitionerPatronymic': forceString(record.value('patrName')),
                                            'practitionerSNILS': forceString(record.value('SNILS')),
                                            'practitionerSpecialityName': forceString(record.value('name'))}

                        if not clientAttachId:
                            QtGui.QMessageBox().warning(self, u'Информация',
                                                            u'У пациента отсутствуют данные о прикреплении!')
                            return
                        if not orgStructId:
                            QtGui.QMessageBox().warning(self, u'Информация',
                                                            u'У пациента должен быть выбран участок!')
                            return
                        if attachEndDate:
                            QtGui.QMessageBox().warning(self, u'Информация',
                                                            u'У пациента должено быть действующее прикрепление к участку!')
                            return
                        if not practitioner.get('practitionerArea', None):
                            QtGui.QMessageBox().warning(self, u'Информация',
                                                            u'У участка должен быть заполнен "Внутренний" код по ИнФИС!')
                            return
                        if not practitioner.get('practitionerSurname', None):
                            QtGui.QMessageBox().warning(self, u'Информация',
                                                            u'У выбранного участка должен быть выбран участоковый врач!')
                        if not practitioner.get('practitionerName', None):
                            QtGui.QMessageBox().warning(self, u'Информация',
                                                            u'У участкового врача должены быть заполнены фамилия и имя!')
                        if not practitioner.get('practitionerSNILS', None):
                            QtGui.QMessageBox().warning(self, u'Информация',
                                                            u'У участкового врача должен быть заполнен СНИЛС')
                            return
                        if not practitioner.get('practitionerSpecialityName', None):
                            QtGui.QMessageBox().warning(self, u'Информация',
                                                            u'У участкового врача должна быть специальность')
                            return

                        if QtGui.QMessageBox().question(self, u'Внимание!', u'Заявка выполнена успешно?',
                                                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                        QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                            # прописываем пациента в заявление
                            self.AttachMO_Complete(orderType, taskId, clientId, practitioner)
                            self.updateData(model, row, taskId)
                    elif orderType == 2:  # Открепление
                        # Открываем форму выбора/создания пациента
                        if not clientId:
                            dialog = CAttachOnlineClientSearchDialog(self, model.items()[row])
                            dialog.addIgnoreButton()
                            # Если нажат ПРОПУСТИТЬ, то не создаем пациента
                            if dialog.exec_():
                                clientId = dialog.clientId
                            else:
                                # Если нажато ОТМЕНА, то выход
                                return
                        if clientId:
                            self.editClient(clientId)
                            # проверки
                            stmt = u"""SELECT ca.id as clientAttachId, ca.endDate as attachEndDate
                              FROM ClientAttach ca
                              WHERE ca.id = getClientAttachId({0}, 0)
                              limit 1""".format(clientId)

                            query = db.query(stmt)
                            clientAttachId = None
                            attachEndDate = None
                            while query.next():
                                record = query.record()
                                clientAttachId = forceRef(record.value('clientAttachId'))
                                attachEndDate = forceDate(record.value('attachEndDate'))
                            if clientAttachId and not attachEndDate:
                                QtGui.QMessageBox().warning(self, u'Информация',
                                                                u'У пациента есть действующее прикрепление!')
                                return
                        if QtGui.QMessageBox().question(self, u'Внимание!', u'Заявка выполнена успешно?',
                                                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                        QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                            self.AttachMO_Complete(orderType, taskId, clientId)
                            self.updateData(model, row, taskId)
                    elif orderType == 3:  # Отмена заявки
                        relatedTaskId = forceRef(model.value(row, 'relatedTask_id'))
                        if not relatedTaskId:
                            QtGui.QMessageBox().warning(self, u'Внимание!',
                                                            u'Для заявления на отмену нет связанного основного заявления!')
                            return
                        relationOrderType = forceInt(model.value(row, 'relationOrderType'))
                        if relationOrderType == 2:
                            QtGui.QMessageBox().warning(self, u'Внимание!',
                                                            u'Заявление на отмену открепления выполнить нельзя, его можно только отклонить!')
                            return
                        relationTaskStatus = forceString(model.value(row, 'relationTaskStatus'))

                        if relatedTaskId and relationOrderType == 1 and relationTaskStatus != "rejected":
                            reasonComment = u"Невозможно выполнить заявление на прикрепление, так как гражданин отозвал свое заявление"
                            reasonCode = 1
                            self.AttachMO_Reject(relatedTaskId, reasonComment, reasonCode)
                            relatedRow = self.getRowById(relatedTaskId)
                            self.updateData(model, relatedRow, relatedTaskId)
                        elif relationTaskStatus != "rejected":
                            QtGui.QMessageBox().warning(self, u'Внимание!',
                                                            u'Для выполнении заявления на отмену необходимо отменить связанную основное заявление!')
                            return
                        self.AttachMO_Complete(orderType, taskId, clientId)
                        self.updateData(model, row, taskId)

    def getRowById(self, id):
        row = 0
        model = self.tblStatements.model()
        items = model.items()
        for item in items:
            if forceInt(item.value('attachTaskId')) == id:
                break
            else:
                row += 1
        return row

    def AttachMO_Complete(self, orderTypeId, taskId, clientId, practitioner=None):
        db = QtGui.qApp.db
        tableTask = db.table('soc_AttachMO_Task')
        tablePatient = db.table('soc_AttachMO_Person')
        if orderTypeId == 1:  # Прикрепление
            taskRecord = db.getRecordEx(tableTask, '*', tableTask['id'].eq(taskId))
            if taskRecord:
                # Привязываем пациента
                patientId = forceRef(taskRecord.value('patient_id'))
                patientRecord = db.getRecordEx(tablePatient, '*', tablePatient['id'].eq(patientId))
                patientRecord.setValue('client_id', toVariant(clientId))
                db.updateRecord(tablePatient, patientRecord)
                # Подготавливаем для выгрузки заявку
                taskRecord.setValue('status', toVariant("completed"))
                taskRecord.setValue('PractitionerArea', practitioner.get('practitionerArea', None))
                taskRecord.setValue('PractitionerSurname', practitioner.get('practitionerSurname', None))
                taskRecord.setValue('PractitionerName', practitioner.get('practitionerName', None))
                taskRecord.setValue('PractitionerPatronymic', practitioner.get('practitionerPatronymic', None))
                taskRecord.setValue('PractitionerSNILS', practitioner.get('practitionerSNILS', None))
                taskRecord.setValue('PractitionerSpecialityName', practitioner.get('practitionerSpecialityName', None))
                taskRecord.setValue('need_upload', toVariant(True))
                taskRecord.setValue('completedPersonID', toVariant(QtGui.qApp.userId))
                taskRecord.setValue('dateCompleted', toVariant(QDateTime.currentDateTime()))
                db.updateRecord(tableTask, taskRecord)
                self.sendRequest(taskId, '$UpdateTaskStatus')
        elif orderTypeId == 2:  # Открепление
            taskRecord = db.getRecordEx(tableTask, '*', tableTask['id'].eq(taskId))
            if taskRecord:
                # Привязываем пациента
                if clientId:
                    patientId = forceRef(taskRecord.value('patient_id'))
                    patientRecord = db.getRecordEx(tablePatient, '*', tablePatient['id'].eq(patientId))
                    patientRecord.setValue('client_id', toVariant(clientId))
                    db.updateRecord(tablePatient, patientRecord)
                # Подготавливаем для выгрузки заявку
                taskRecord.setValue('status', toVariant("completed"))
                taskRecord.setValue('need_upload', toVariant(True))
                taskRecord.setValue('completedPersonID', toVariant(QtGui.qApp.userId))
                taskRecord.setValue('dateCompleted', toVariant(QDateTime.currentDateTime()))
                db.updateRecord(tableTask, taskRecord)
                self.sendRequest(taskId, '$UpdateTaskStatus')
        elif orderTypeId == 3:  # Отмена заявки
            taskRecord = db.getRecordEx(tableTask, '*', tableTask['id'].eq(taskId))
            if taskRecord:
                # Подготавливаем для выгрузки заявку
                taskRecord.setValue('status', toVariant("completed"))
                taskRecord.setValue('need_upload', toVariant(True))
                taskRecord.setValue('completedPersonID', toVariant(QtGui.qApp.userId))
                taskRecord.setValue('dateCompleted', toVariant(QDateTime.currentDateTime()))
                db.updateRecord(tableTask, taskRecord)
                self.sendRequest(taskId, '$UpdateTaskStatus')

    def sendRequest(self, taskId, resource):
        if self.servicesURL:
            dictTask = {'attach_id': taskId}
            js = json.dumps(dictTask)
            message = None
            try:
                response = requests.post(self.servicesURL + '/' + resource, data=js)
                if response.status_code == 200:
                    try:
                        jsonData = response.json()
                        if jsonData.get('result', '') != "success":
                            message = u"Возвращен неверный формат ответа!"
                    except Exception, e:
                        message = u"Произошла ошибка при распарсевании JSON ответа. Неверный формат JSON! Текст ошибки: " + unicode(
                            e)
                elif response.status_code >= 400:
                    try:
                        jsonData = response.json()
                        message = jsonData.get('detail', '')
                    except Exception, e:
                        message = u"Произошла ошибка при распарсевании JSON ответа. Неверный формат JSON! Текст ошибки: " + unicode(
                            e)
            except Exception, e:
                QtGui.QMessageBox().critical(self, u'Ошибка', u'Произошла ошибка: ' + unicode(e),
                                             QtGui.QMessageBox.Close)
            if message:
                QtGui.QMessageBox().critical(self, u'Ошибка', message, QtGui.QMessageBox.Close)


    def AttachMO_Reject(self, taskId, ReasonComment, ReasonCode):
        db = QtGui.qApp.db
        tableTask = db.table('soc_AttachMO_Task')
        taskRecord = db.getRecordEx(tableTask, '*', tableTask['id'].eq(taskId))
        # Подготавливаем для выгрузки заявку
        taskRecord.setValue('status', toVariant("rejected"))
        taskRecord.setValue('reasonReject_id', toVariant(ReasonCode))
        taskRecord.setValue('statusComment', toVariant(ReasonComment))
        taskRecord.setValue('need_upload', toVariant(True))
        taskRecord.setValue('completedPersonID', toVariant(QtGui.qApp.userId))
        taskRecord.setValue('dateCompleted', toVariant(QDateTime.currentDateTime()))
        db.updateRecord(tableTask, taskRecord)
        self.sendRequest(taskId, '$UpdateTaskStatus')

    def updateData(self, model, row, taskId):
        model.updateData(taskId, row)
        model.emitRowChanged(row)
        self.setInfoToFields(row, row)


    def cancelStatement(self):
        """Кнопка Отменить заявку"""
        model = self.tblStatements.model()
        row = self.tblStatements.currentRow()
        if row > -1:
            taskId = forceRef(model.value(row, 'attachTaskId'))
            self.updateData(model, row, taskId)
            status = forceString(model.value(row, 'status'))
            if status == u'in-progress':
                orderType = forceInt(model.value(row, 'order_type'))
                if orderType == 3:
                    relatedTaskId = forceRef(model.value(row, 'relatedTask_id'))
                    if not relatedTaskId:
                        QtGui.QMessageBox().warning(self, u'Внимание!',
                                                        u'Для заявления на отмену нет связанного основного заявления!')
                        return
                    relationTaskStatus = forceString(model.value(row, 'relationTaskStatus'))
                    relationOrderType = forceInt(model.value(row, 'relationOrderType'))

                    if relationOrderType == 1 and relationTaskStatus != "completed":
                        QtGui.QMessageBox().warning(self, u'Внимание!',
                                                        u'Заявление на отмену заявления на прикрепление отклонить невозможно, его необходимо выполнить!')
                        return
                elif orderType == 2:
                    QtGui.QMessageBox().warning(self, u'Внимание!',
                                                    u'Заявление на открепление отклонить невозможно, его необходимо выполнить!')
                    return
                elif orderType == 1:
                    dialog = CAttachOnlineReasonRejectDialog(self)
                    dialog.exec_()
                    if dialog.execResult:
                        ReasonComment = dialog.edtComment.text()
                        ReasonCode = dialog.cmbReasonReject.value()
                        if ReasonComment and ReasonCode:
                            self.AttachMO_Reject(taskId, ReasonComment, ReasonCode)
                            self.updateData(model, row, taskId)
            else:
                QtGui.QMessageBox().warning(self, u'Внимание!', u'Для этого статуса данное действие невозможно!')

    def uploadTasks(self):
        """Кнопка выгрузить ожидающие"""
        self.sendRequest(0, '$UpdateTaskStatus')
        self.applyFilters()

    def openData(self):
        """Кнопка Просмотр/Изменение данных"""
        model = self.tblStatements.model()
        row = self.tblStatements.currentRow()
        clientId = forceInt(model.value(row, 'client_id'))
        taskId = forceRef(model.value(row, 'attachTaskId'))
        self.editClient(clientId)
        self.updateData(model, row, taskId)

    def editClient(self, clientId):
        if QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = CClientEditDialog(self)
            try:
                if clientId:
                    dialog.load(clientId)
                    dialog.exec_()
            finally:
                dialog.deleteLater()


    def detachClient(self):
        """Кнопка Отвязать пациента"""
        model = self.tblStatements.model()
        row = self.tblStatements.currentRow()
        taskStatus = forceString(model.value(row, 'status'))
        if taskStatus == 'in-progress':
            clientId = forceRef(model.value(row, 'client_id'))
            if clientId:
                if QtGui.QMessageBox().question(self, u'Внимание!', u'Очистить информацию о пациенте в заявлении?',
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                    patientId = forceRef(model.value(row, 'patient_id'))
                    db = QtGui.qApp.db
                    tablePatient = db.table('soc_AttachMO_Person')
                    patientRecord = db.getRecordEx(tablePatient, '*', tablePatient['id'].eq(patientId))
                    patientRecord.setValue('client_id', toVariant(None))
                    db.updateRecord(tablePatient, patientRecord)
                    taskId = forceRef(model.value(row, 'attachTaskId'))
                    self.updateData(model, row, taskId)
        else:
            QtGui.QMessageBox().warning(self, u'Информация', u'Для этого статуса данное действие невозможно!')


    def setInfoToFields(self, current, previous):
        model = self.tblStatements.model()
        row = self.tblStatements.currentRow()
        self.btnOpenData.setEnabled(forceBool(model.value(row, 'client_id')))
        self.btnDetachClient.setEnabled(forceBool(model.value(row, 'client_id')))
        self.edtClientFIO.setText(forceString(model.value(row, 'client_fullName')))
        
        taskMisId = forceString(model.value(row, 'attachTaskId'))
        taskServerId = forceString(model.value(row, 'task_guid'))
        taskNumber = forceString(model.value(row, 'order_number'))
        taskType = forceString(model.value(row, 'order_type'))
        attachReasonInfo = forceString(model.value(row, 'ReasonName'))
        taskStatus = forceString(model.value(row, 'statusString'))
        createDate = forceString(model.value(row, 'createDate'))
        orderCreateDate = forceString(model.value(row, 'orderCreateDate'))
        needUpload = forceInt(model.value(row, 'need_upload'))
        reasonReject = forceString(model.value(row, 'RejectName'))
        statusComment = forceString(model.value(row, 'statusComment'))
        practitionerArea = forceString(model.value(row, 'PractitionerArea'))
        PractitionerFullname = forceString(model.value(row, 'practitioner_fullName'))
        PractitionerSNILS = forceString(model.value(row, 'PractitionerSNILS'))
        PractitionerSpecialityName = forceString(model.value(row, 'PractitionerSpecialityName'))
        
        relatedTaskMisId = forceString(model.value(row, 'relatedTask_id'))
        relatedTaskServerId = forceString(model.value(row, 'task_guid_rel'))

        clientGuid = forceString(model.value(row, 'person_guid'))
        clientFullname = forceString(model.value(row, 'patient_fullName'))
        clientBirthdate = forceString(model.value(row, 'birthDate'))
        clientSex = u'мужской' if forceString(model.value(row, 'sex')) == 'male' else u'женский'
        clientPhone = forceString(model.value(row, 'phone'))
        clientBirthPlace = forceString(model.value(row, 'birthPlace'))
        clientCitizenship = forceString(model.value(row, 'citizenship'))
        clientDocumentTypeCode = forceString(model.value(row, 'docTypeName'))
        clientDocumentSerial = forceString(model.value(row, 'documentSerial'))
        clientDocumentNumber = forceString(model.value(row, 'documentNumber'))
        clientDocumentOriginCode = forceString(model.value(row, 'documentOriginCode'))
        clientDocumentOrigin = forceString(model.value(row, 'documentOrigin'))
        clientDocumentIssuedDate = forceString(model.value(row, 'documentIssuedDate'))
        clientPolicyType = forceString(model.value(row, 'policyName'))
        clientPolicySerial = forceString(model.value(row, 'policySerial'))
        clientPolicyNumber = forceString(model.value(row, 'policyNumber'))
        clientPolicyBegDate = forceString(model.value(row, 'policyBegDate'))
        clientPolicyEndDate = forceString(model.value(row, 'policyEndDate'))
        clientPolicyOKATO = forceString(model.value(row, 'policyOKATO'))
        clientPolicyOrgCode = forceString(model.value(row, 'policyOrgCode'))
        clientRegAddress = forceString(model.value(row, 'regAddress'))
        clientRegAddressPostCode = forceString(model.value(row, 'regAddressPostCode'))
        clientLocAddress = forceString(model.value(row, 'locAddress'))
        clientLocAddressPostCode = forceString(model.value(row, 'locAddressPostCode'))

        personFullname = forceString(model.value(row, 'person_fullName'))
        personBirthdate = forceString(model.value(row, 'birthDateP'))
        personSex = u'мужской' if forceString(model.value(row, 'sexP')) == 'male' else u'женский'
        relationshipDict = {'FTH': u'Отец', 'MTH': u'Мать', 'PRNFOST': u'Опекун', 'ADOPTP': u'Попечитель', }
        personRelationship = relationshipDict[forceString(model.value(row, 'relationshipP'))] if forceString(model.value(row, 'relationshipP')) else u''
        personSNILS = forceString(model.value(row, 'SNILSP'))
        personCitizenship = forceString(model.value(row, 'citizenshipP'))
        personDocumentTypeCode = forceString(model.value(row, 'docTypeNameP'))
        personDocumentSerial = forceString(model.value(row, 'documentSerialP'))
        personDocumentNumber = forceString(model.value(row, 'documentNumberP'))
        personDocumentOriginCode = forceString(model.value(row, 'documentOriginCodeP'))
        personDocumentOrigin = forceString(model.value(row, 'documentOriginP'))
        personDocumentIssuedDate = forceString(model.value(row, 'documentIssuedDateP'))
        if needUpload:
            statementInfo = u"""
            <br>
            <b><p style="color:#B22222";>!!! ЗАЯВЛЕНИЕ ЖДЕТ ВЫГРУЗКИ НА СЕРВЕР !!!</p></b>
            """
        else:
            statementInfo = u''
        statementInfo += u"""
        -----------------------------------------------------------------
        <b><p style="color:#556B2F";>Информация о заявлении</p></b>
        -----------------------------------------------------------------<br>
        <b>Идентификатор заявления МИС: </b> {0}<br>                                  
        <b>Идентификатор заявления присвоенный сервером: </b> {1}<br>
        <b>Номер заявления: </b> {2}<br>
        <b>Тип заявления: </b> {3}<br>
        <b>Информация о причине смены прикрепления: </b> {4}<br>
        <b>Статус заявления: </b> {5}<br>
        <b>Дата создания заявления: </b> {6}<br>
        <b>Дата получения заявления: </b> {7}<br>
        <b>Причины отказа в прикреплении к МО: </b> {8}<br>
        <b>Комментарий к статусу: </b> {9}<br>
        <b>Участок: </b> {10}<br>
        <b>Участковый врач: </b> {11}<br>
        <b>СНИЛС врача: </b> {12}<br>
        <b>Специальность врача: </b> {13}<br>
        """.format(taskMisId, taskServerId, taskNumber, taskType, attachReasonInfo, taskStatus, 
        orderCreateDate, createDate,
        reasonReject, statusComment, practitionerArea, PractitionerFullname, PractitionerSNILS, 
        PractitionerSpecialityName)
        if relatedTaskServerId:
            statementInfo += u"""
        -----------------------------------------------------------------
        <b><p style="color:#556B2F";>Информация о связанном заявлении</p></b>
        -----------------------------------------------------------------<br>
        <b>Идентификатор связанного заявления МИС: </b> {0}<br>
        <b>Идентификатор связанного заявления присвоенный сервером: </b> {1}<br>
        """.format(relatedTaskMisId, relatedTaskServerId)

        statementInfo += u"""
        -----------------------------------------------------------------
        <b><p style="color:#556B2F";>Информация о пациенте</p></b>
        -----------------------------------------------------------------<br>
        <b>Идентификатор пациента присвоенный сервером: </b> {0}<br>
        <b>ФИО пациента: </b> {1}<br>
        <b>Дата рождения пациента: </b> {2}<br>
        <b>Пол пациента: </b> {3}<br>
        <b>Телефон пациента: </b> {4}<br>
        <b>Место рождения пациента: </b> {5}<br>
        <b>Гражданство пациента: </b> {6}<br>
        <b>Документ удостоверяющий личность пациента: </b> {7}<br>
        <b>Серия: </b> {8}<br>
        <b>Номер: </b> {9}<br>
        <b>Код подразделения: </b> {10}<br>
        <b>Выдан: </b> {11}<br>
        <b>Дата выдачи: </b> {12}<br>
        <b>Полис ОМС пациента: </b> {13}<br>
        <b>Серия: </b> {14}<br>
        <b>Номер: </b> {15}<br>
        <b>Действует с: </b> {16}<br>
        <b>Действует по: </b> {17}<br>
        <b>Код региона ОКАТО: </b> {18}<br>
        <b>Код СМО: </b> {19}<br>
        <b>Адрес регистрации пациента: </b> {20}<br>
        <b>Почтовый индекс адреса регистрации: </b> {21}<br>
        <b>Адрес проживания пациента: </b> {22}<br>
        <b>Почтовый индекс адреса проживания: </b> {23}<br>
        """.format(
        clientGuid, clientFullname, clientBirthdate, clientSex, clientPhone, clientBirthPlace, clientCitizenship,
        clientDocumentTypeCode, clientDocumentSerial, clientDocumentNumber, clientDocumentOriginCode,
        clientDocumentOrigin, clientDocumentIssuedDate, clientPolicyType, clientPolicySerial, clientPolicyNumber,
        clientPolicyBegDate, clientPolicyEndDate, clientPolicyOKATO, clientPolicyOrgCode, clientRegAddress,
        clientRegAddressPostCode, clientLocAddress, clientLocAddressPostCode)
        if personFullname:
            statementInfo += u"""
        -----------------------------------------------------------------
        <b><p style="color:#556B2F";>Информация о представителе</p></b>
        -----------------------------------------------------------------<br>
        <b>ФИО представителя: </b> {0}<br>
        <b>Дата рождения представителя: </b> {1}<br>
        <b>Пол представителя: </b> {2}<br>
        <b>Отношение законного представителя к пациенту: </b> {3}<br>
        <b>СНИЛС представителя: </b> {4}<br>
        <b>Гражданство представителя: </b> {5}<br>
        <b>Документ удостоверяющий личность представителя: </b> {6}<br>
        <b>Серия: </b> {7}<br>
        <b>Номер: </b> {8}<br>
        <b>Код подразделения: </b> {9}<br>
        <b>Дата выдачи: </b> {10}<br>
        <b>Выдан: </b> {11}<br>
        """.format(personFullname, personBirthdate, personSex, personRelationship, personSNILS, personCitizenship,
                   personDocumentTypeCode, personDocumentSerial, personDocumentNumber, personDocumentOriginCode,
                   personDocumentOrigin, personDocumentIssuedDate)
        self.edtStatementInfo.setHtml(statementInfo)

    def contextMenuEvent(self, event):
        model = self.tblStatements.model()
        row = self.tblStatements.currentRow()
        self.menu = QtGui.QMenu(self)
        hasRelatedTask = forceInt(model.value(row, 'relatedTask_id'))
        if hasRelatedTask:
            openRelated = QtGui.QAction(u'Открыть связанное заявление', self)
            openRelated.triggered.connect(self.getTaskWithRelated)
            self.menu.addAction(openRelated)
            self.menu.popup(QtGui.QCursor.pos())

    def getTaskWithRelated(self):
        model = self.tblStatements.model()
        row = self.tblStatements.currentRow()
        taskId = forceInt(model.value(row, 'attachTaskId'))
        relatedTaskId = forceInt(model.value(row, 'relatedTask_id'))
        model.loadData(id=[taskId, relatedTaskId])

    def applyFilters(self):
        filters = dict.fromkeys(['statementType', 'statementStatus','requestBegDate', 'requestEndDate',
                                 'patientSurname', 'patientName', 'patientPatronymic', 'patientBirthDate'])
        requestBegDate = self.edtFilterRequestBegDate.date()
        requestEndDate = self.edtFilterRequestEndDate.date()
        statementType = forceInt(self.cmbFilterStatementType.currentIndex())
        statementStatus = forceInt(self.cmbFilterStatementStatus.currentIndex())
        patientSurname = forceString(self.leFilterSurname.text())
        patientName = forceString(self.leFilterName.text())
        patientPatronymic = forceString(self.leFilterPatronymic.text())
        patientBirthDate = self.edtFilterBirthDate.date()

        if requestBegDate:
            filters['requestBegDate'] = requestBegDate
        if requestEndDate:
            filters['requestEndDate'] = requestEndDate
        filters['statementType'] = statementType
        filters['statementStatus'] = statementStatus
        if patientSurname:
            filters['patientSurname'] = patientSurname + u'...'
        if patientName:
            filters['patientName'] = patientName + u'...'
        if patientPatronymic:
            filters['patientPatronymic'] = patientPatronymic + u'...'
        if patientBirthDate:
            filters['patientBirthDate'] = patientBirthDate

        self.loadData(filters)

    def resetFilters(self):
        self.edtFilterRequestBegDate.setDate(QDate())
        self.edtFilterRequestEndDate.setDate(QDate())
        self.cmbFilterStatementStatus.setCurrentIndex(0)
        self.cmbFilterStatementType.setCurrentIndex(0)
        self.leFilterSurname.setText('')
        self.leFilterName.setText('')
        self.leFilterPatronymic.setText('')
        self.edtFilterBirthDate.setDate(QDate())

        self.loadData()

    def loadData(self, filters=None):
        self.tblStatements.model().loadData(filters)
        self.tblStatements.setCurrentRow(0)
        self.modelStatementsDataChanged()

    def formatDateTime(self, value):
        if isinstance(value, QVariant):
            value = value.toDateTime()
            return unicode(value.toString('dd.MM.yyyy H:mm:ss'))
        if value is None:
            return ''
    

    def modelStatementsDataChanged(self):
        labelText = u'В списке %d %s' % (self.modelStatements.countItems, agreeNumberAndWord(self.modelStatements.countItems, (u'запись', u'записи', u'записей')))
        self.lblStatementsCount.setText(labelText)
    
    @pyqtSignature('')
    def on_btnPrintList_clicked(self):
        document = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(document)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Заявки прикрепления on-line')
        cursor.insertBlock()
        model = self.tblStatements.model()
        tableColumns = [('9%', [u'Тип заявления'], CReportBase.AlignLeft),
                        ('7%', [u'Статус заявления'], CReportBase.AlignLeft),
                        ('7%', [u'Идентификатор заявления'], CReportBase.AlignLeft),
                        ('7%', [u'Дата получения заявления'], CReportBase.AlignLeft),
                        ('13%', [u'ФИО пациента'], CReportBase.AlignLeft),
                        ('4%', [u'Дата рождения'], CReportBase.AlignLeft),
                        ('12%', [u'Адрес регистрации'], CReportBase.AlignLeft),
                        ('12%', [u'Адрес проживания'], CReportBase.AlignLeft),
                        ('7%', [u'Идентификатор связанного заявления'], CReportBase.AlignLeft),
                        ('7%', [u'Результат выгрузки'], CReportBase.AlignLeft),
                        ('4%', [u'Дата выгрузки'], CReportBase.AlignLeft),
                        ('7%', [u'ФИО отработавшего'], CReportBase.AlignLeft),
                        ('4%', [u'Дата выполнения'], CReportBase.AlignLeft),
                        ]
        table = createTable(cursor, tableColumns)
        for row in range(len(model._items)):
            tableRow = table.addRow()
            for column in range(len(model._cols)):
                col = model._cols[column]
                record = model._items[row]
                table.setText(tableRow, column, forceString(col.toString(record.value(col.fieldName()), record)))
        view = CReportViewDialog(self)
        view.setWindowTitle(u'Печать списка заявок прикрепления on-line')
        view.setText(document)
        view.exec_()
        
    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        model = self.tblStatements.model()
        row = self.tblStatements.currentRow()
        if row >= 0:
            document = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(document)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.setBlockFormat(CReportBase.AlignCenter)
            cursor.insertText(u'''Информация об электронном заявлении с выбором 
гражданином медицинской организации 
для оказания медицинской помощи в рамках 
программы государственных гарантий бесплатного оказания 
гражданам медицинской помощи''')
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.setBlockFormat(CReportBase.AlignLeft)
            statementInfo = u"""
            <b>Источник поступления заявления: </b> {0}<br>  
            <b>Идентификатор заявления МИС: </b> {1} <b>Номер заявления: </b> {2}<br>                                
            <b>Идентификатор заявления присвоенный сервером: </b> {3}<br>
            <b>Тип заявления: </b> {4} <b>Информация о причине смены прикрепления: </b> {5}<br>
            <b>Статус заявления: </b> {6}<br>
            <b>Дата создания заявления: </b> {7}<br>
            <b>Дата получения заявления: </b> {8}<br>
            <b>Причины отказа в прикреплении к МО: </b> {9}<br>
            <b>Комментарий к статусу: </b> {10}<br>
            <b>Участок: </b> {11}<br>
            <b>Участковый врач: </b> {12}<br>
            <b>СНИЛС врача: </b> {13}<br>
            <b>Специальность врача: </b> {14}<br>
            """.format(forceString(model.value(row, 'order_source')), forceString(model.value(row, 'attachTaskId')),
                       forceString(model.value(row, 'order_number')), forceString(model.value(row, 'task_guid')),
                       forceString(model.value(row, 'order_type')), forceString(model.value(row, 'ReasonName')),
                       forceString(model.value(row, 'StatusString')), forceString(model.value(row, 'orderCreateDate')),
                       forceString(model.value(row, 'createDate')), forceString(model.value(row, 'RejectName')),
                       forceString(model.value(row, 'statusComment')), forceString(model.value(row, 'PractitionerArea')),
                       forceString(model.value(row, 'practitioner_fullName')),forceString(model.value(row, 'PractitionerSNILS')),
                       forceString(model.value(row, 'PractitionerSpecialityName')))
            cursor.insertHtml(statementInfo)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'Сведения о заявителе')
            cursor.insertBlock()
            cursor.insertBlock()
            statementInfo = u"""
            <b>Идентификатор пациента присвоенный сервером: </b> {0}<br>
            <b>ФИО: </b> {1}<br>
            <b>Дата рождения пациента: </b> {2} <b>Пол пациента: </b> {3}<br>
            <b>Телефон пациента: </b> {4}<br>
            <b>Место рождения пациента: </b> {5}<br>
            <b>Гражданство пациента: </b> {6}<br>
            <b>Документ удостоверяющий личность пациента: </b> {7}<br>
            <b>Серия: </b> {8} <b>Номер: </b> {9} <b>Дата выдачи: </b> {10} <b>Код подразделения: </b> {11}<br>
            <b>Выдан: </b> {12}<br>
            <b>Полис ОМС пациента: </b> {13}<br>
            <b>Серия: </b> {14} <b>Номер: </b> {15} <b>Действует с: </b> {16} <b>Действует по: </b> {17}<br>
            <b>Код региона ОКАТО: </b> {18} <b>Код СМО: </b> {19}<br>
            <b>Адрес регистрации пациента: </b> {20} {21}<br>
            <b>Адрес проживания пациента: </b> {22} {23}<br>
            """.format(forceString(model.value(row, 'person_guid')), forceString(model.value(row, 'patient_fullName')),
                       forceString(model.value(row, 'birthDate')), u'мужской' if forceString(model.value(row, 'sex')) == 'male' else u'женский',
                       forceString(model.value(row, 'phone')), forceString(model.value(row, 'birthPlace')),
                       forceString(model.value(row, 'citizenship')), forceString(model.value(row, 'docTypeName')),
                       forceString(model.value(row, 'documentSerial')), forceString(model.value(row, 'documentNumber')),
                       forceString(model.value(row, 'documentIssuedDate')), forceString(model.value(row, 'documentOriginCode')),
                       forceString(model.value(row, 'documentOrigin')), forceString(model.value(row, 'policyName')),
                       forceString(model.value(row, 'policySerial')), forceString(model.value(row, 'policyNumber')),
                       forceString(model.value(row, 'policyBegDate')), forceString(model.value(row, 'policyEndDate')),
                       forceString(model.value(row, 'policyOKATO')), forceString(model.value(row, 'policyOrgCode')),
                       forceString(model.value(row, 'regAddressPostCode')), forceString(model.value(row, 'regAddress')),
                       forceString(model.value(row, 'locAddressPostCode')), forceString(model.value(row, 'locAddress')),)
            cursor.insertHtml(statementInfo)
            view = CReportViewDialog(self)
            view.setWindowTitle(u'Печать заявки прикрепления on-line')
            view.setText(document)
            view.exec_()


    def sortByColumn(self, column):
        header = self.tblStatements.horizontalHeader()
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
        self.modelStatements.sortData(column, self.__sortAscending)


class CAttachOnlineReasonRejectDialog(CDialogBase, Ui_ReasonRejectDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.btnApply.clicked.connect(self.applyClicked)
        self.btnCancel.clicked.connect(self.cancelClicked)
        self.cmbReasonReject.setTable('soc_AttachMO_ReasonReject')
        self.execResult = 0
        self.cmbReasonReject.setCurrentIndex(0)

    def applyClicked(self):
        if not self.edtComment.text():
            QtGui.QMessageBox().warning(self, u'Внимание!',
                                    u'Необходимо заполнить комментарий при отказе')
            return
        if not self.cmbReasonReject.value():
            QtGui.QMessageBox().warning(self, u'Внимание!',
                                    u'Необходимо указать причину отказа')
            return
        self.execResult = 1
        self.close()

    def cancelClicked(self):
        self.close()



class CStatementsModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CEnumInDocTableCol(u'Тип заявления', 'order_type', 20, [u'-', u'Прикрепление', u'Открепление', u'Отмена заявления'])).setReadOnly()
        self.addCol(CInDocTableCol(u'Статус заявления', 'statusString', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Идентификатор заявления', 'attachTaskId', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата получения заявления', 'orderCreateDate', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'ФИО пациента', 'patient_fullName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата рождения', 'birthDate', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Адрес регистрации', 'regAddress', 40)).setReadOnly()
        self.addCol(CInDocTableCol(u'Адрес проживания', 'locAddress', 40)).setReadOnly()
        self.addCol(CInDocTableCol(u'Идентификатор связанного заявления', 'relatedTask_id', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Результат выгрузки', 'uploadResult', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата выгрузки', 'uploadDate', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'ФИО отработавшего', 'completedPerson', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата выполнения', 'dateCompleted', 20)).setReadOnly()
        self.loadData()
        self.countItems = len(self._items)

    def updateData(self, _id, row):
        db = QtGui.qApp.db
        tableQuery, cols, cond = self.getTableQuery(filters=None, _id=_id)
        record = db.getRecordEx(tableQuery, cols, cond)
        self._items[row] = record

    def getTableQuery(self, filters=None, _id=None):
        db = QtGui.qApp.db
        tableAttachTask = db.table('soc_AttachMO_Task')
        tableAttachReason = db.table('soc_AttachMO_Reason')
        tableAttachReasonReject = db.table('soc_AttachMO_ReasonReject')
        tableAttachPersonC = db.table('soc_AttachMO_Person').alias('attachMO_Client')
        tableClient = db.table('Client')
        tableAttachPersonP = db.table('soc_AttachMO_Person').alias('attachMO_Person')
        tableAttachTaskRel = db.table('soc_AttachMO_Task').alias('soc_AttachMO_TaskRel')
        tableDocType = db.table('rbDocumentType')
        tableDocTypeP = db.table('rbDocumentType').alias('rbDocumentTypePerson')
        tablePolicyKind = db.table('rbPolicyKind')
        tablePerson = db.table('Person')

        tableQuery = tableAttachTask
        tableQuery = tableQuery.leftJoin(tableAttachReason, tableAttachReason['id'].eq(tableAttachTask['reason_id']))
        tableQuery = tableQuery.leftJoin(tableAttachReasonReject, tableAttachReasonReject['id'].eq(tableAttachTask['reasonReject_id']))
        tableQuery = tableQuery.leftJoin(tableAttachPersonC, tableAttachPersonC['id'].eq(tableAttachTask['patient_id']))
        tableQuery = tableQuery.leftJoin(tableClient, tableClient['id'].eq(tableAttachPersonC['client_id']))
        tableQuery = tableQuery.leftJoin(tableAttachPersonP, tableAttachPersonP['id'].eq(tableAttachTask['related_person_id']))
        tableQuery = tableQuery.leftJoin(tableAttachTaskRel, tableAttachTaskRel['id'].eq(tableAttachTask['relatedTask_id']))
        tableQuery = tableQuery.leftJoin(tableDocType, tableAttachPersonC['documentTypeCode'].eq(tableDocType['regionalCode']))
        tableQuery = tableQuery.leftJoin(tableDocTypeP, tableAttachPersonP['documentTypeCode'].eq(tableDocTypeP['regionalCode']))
        tableQuery = tableQuery.leftJoin(tablePolicyKind, tableAttachPersonC['policyType'].eq(tablePolicyKind['code']))
        tableQuery = tableQuery.leftJoin(tablePerson, tableAttachTask['completedPersonID'].eq(tablePerson['id']))


        cols = [
            tableAttachTask['id'].alias('attachTaskId'),
            tableAttachTask['createDatetime'].alias('createDate'),
            tableAttachTask['task_guid'],
            tableAttachTask['order_number'],
            tableAttachTask['order_source'],
            tableAttachTask['order_type'],
            tableAttachTask['status'],
            tableAttachTask['orderCreateDate'],
            tableAttachTask['reason_id'],
            tableAttachTask['relatedTask_id'],
            tableAttachTask['patient_id'],
            u"IF (soc_AttachMO_Task.error_upload IS NULL and soc_AttachMO_Task.uploadDate IS NOT NULL, 'Успешно', soc_AttachMO_Task.error_upload) as uploadResult",
            u"""CASE
            WHEN soc_AttachMO_Task.status = 'completed' THEN 'Выполнено'
            WHEN soc_AttachMO_Task.status = 'rejected' THEN 'Отклонено'
            WHEN soc_AttachMO_Task.status = 'in-progress' THEN 'В работе'
            ELSE '-'
            END AS statusString
            """,
            u"CONCAT_WS(' ', attachMO_Client.lastName, attachMO_Client.firstName, attachMO_Client.patrName) AS patient_fullName",
            u"CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) AS client_fullName",
            u"CONCAT_WS(' ', attachMO_Person.lastName, attachMO_Person.firstName, attachMO_Person.patrName) AS person_fullName",
            u"CONCAT_WS(' ', soc_AttachMO_Task.PractitionerSurname, soc_AttachMO_Task.PractitionerName, soc_AttachMO_Task.PractitionerPatronymic) AS practitioner_fullName",
            tableAttachTask['related_person_id'],
            tableAttachTask['uploadDate'],
            tableAttachTask['need_upload'],
            tableAttachTask['reasonReject_id'],
            tableAttachTask['statusComment'],
            tableAttachTask['error_upload'],
            tableAttachTask['PractitionerSNILS'],
            tableAttachTask['PractitionerSpecialityName'],
            tableAttachTask['PractitionerArea'],
            tableAttachTask['dateCompleted'],

            tableAttachReason['name'].alias('ReasonName'),
            tableAttachReasonReject['name'].alias('RejectName'),

            tableAttachTaskRel['task_guid'].alias('task_guid_rel'),
            tableAttachTaskRel['status'].alias('relationTaskStatus'),
            tableAttachTaskRel['order_type'].alias('relationOrderType'),

            tableAttachPersonC['person_guid'],
            tableAttachPersonC['person_type'],
            tableAttachPersonC['client_id'],
            tableAttachPersonC['lastName'],
            tableAttachPersonC['firstName'],
            tableAttachPersonC['patrName'],
            tableAttachPersonC['birthDate'],
            tableAttachPersonC['sex'],
            tableAttachPersonC['phone'],
            tableAttachPersonC['birthPlace'],
            tableAttachPersonC['citizenship'],
            tableAttachPersonC['documentTypeCode'],
            tableAttachPersonC['documentSerial'],
            tableAttachPersonC['documentNumber'],
            tableAttachPersonC['documentOriginCode'],
            tableAttachPersonC['documentOrigin'],
            tableAttachPersonC['documentIssuedDate'],
            tableAttachPersonC['policyType'],
            tableAttachPersonC['policySerial'],
            tableAttachPersonC['policyNumber'],
            tableAttachPersonC['policyBegDate'],
            tableAttachPersonC['policyEndDate'],
            tableAttachPersonC['policyOKATO'],
            tableAttachPersonC['policyOrgCode'],
            tableAttachPersonC['regAddress'],
            tableAttachPersonC['regAddressPostCode'],
            tableAttachPersonC['locAddress'],
            tableAttachPersonC['locAddressPostCode'],
            tableAttachPersonC['relationship'],
            tableAttachPersonC['SNILS'],

            tableDocType['name'].alias('docTypeName'),
            tableDocTypeP['name'].alias('docTypeNameP'),
            tablePolicyKind['name'].alias('policyName'),

            tableAttachPersonP['birthDate'].alias('birthDateP'),
            tableAttachPersonP['sex'].alias('sexP'),
            tableAttachPersonP['birthPlace'].alias('birthPlaceP'),
            tableAttachPersonP['relationship'].alias('relationshipP'),
            tableAttachPersonP['citizenship'].alias('citizenshipP'),
            tableAttachPersonP['documentTypeCode'].alias('documentTypeCodeP'),
            tableAttachPersonP['documentSerial'].alias('documentSerialP'),
            tableAttachPersonP['documentNumber'].alias('documentNumberP'),
            tableAttachPersonP['documentOriginCode'].alias('documentOriginCodeP'),
            tableAttachPersonP['documentOrigin'].alias('documentOriginP'),
            tableAttachPersonP['documentIssuedDate'].alias('documentIssuedDateP'),
            tableAttachPersonP['relationship'].alias('relationshipP'),
            tableAttachPersonP['SNILS'].alias('SNILSP'),

            u"CONCAT_WS(' ', Person.lastName, Person.firstName, Person.patrName) AS completedPerson",

        ]
        cond = []
        if _id:
            if isinstance(_id, list):
                cond.append(tableAttachTask['id'].inlist(_id))
            else:
                cond.append(tableAttachTask['id'].eq(_id))
        elif filters:
            if filters['requestBegDate'] and filters['requestEndDate']:
                cond.append(tableAttachTask['createDatetime'].ge(filters['requestBegDate']))
                cond.append(tableAttachTask['createDatetime'].lt(filters['requestEndDate'].addDays(1)))
            elif filters['requestBegDate']:
                cond.append(tableAttachTask['createDatetime'].ge(filters['requestBegDate']))
            elif filters['requestEndDate']:
                cond.append(tableAttachTask['createDatetime'].lt(filters['requestEndDate'].addDays(1)))
            if filters['statementType']:
                cond.append(tableAttachTask['order_type'].eq(filters['statementType']))
            if filters['statementStatus']:
                statusDict = {1: 'completed', 3: 'in-progress', 2: 'rejected'}
                cond.append(tableAttachTask['status'].eq(statusDict[filters['statementStatus']]))
            if filters['patientSurname']:
                cond.append(tableAttachPersonC['lastName'].like(filters['patientSurname']))
            if filters['patientName']:
                cond.append(tableAttachPersonC['firstName'].like(filters['patientName']))
            if filters['patientPatronymic']:
                cond.append(tableAttachPersonC['patrName'].like(filters['patientPatronymic']))
            if filters['patientBirthDate']:
                cond.append(tableAttachPersonC['birthDate'].eq(filters['patientBirthDate']))
        return tableQuery, cols, cond

    def loadData(self, filters=None, id=None):
        db = QtGui.qApp.db
        tableQuery, cols, cond = self.getTableQuery(filters, id)
        records = db.getRecordList(tableQuery, cols, cond)
        self.setItems(records)
        self.countItems = len(self._items)

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):

            if role == Qt.EditRole:
                col = self._cols[column]
                record = self._items[row]
                return record.value(col.fieldName())

            if role == Qt.DisplayRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toString(record.value(col.fieldName()), record)

            if role == Qt.StatusTipRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toStatusTip(record.value(col.fieldName()), record)

            if role == Qt.ToolTipRole and self.getColIndex('system_id') >= 0:
                db = QtGui.qApp.db
                record = db.getRecord('rbAccountingSystem', 'urn', forceString(self.items()[row].value('system_id')))
                if record:
                    result = forceString(record.value('urn'))
                else:
                    result = None
                return result

            if role == Qt.TextAlignmentRole:
                col = self._cols[column]
                return col.alignment()

            if role == Qt.CheckStateRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toCheckState(record.value(col.fieldName()), record)

            record = self._items[row]
            if role == Qt.BackgroundRole and forceString(record.value('status')) == 'completed':
                return QtCore.QVariant(QtGui.QColor('#9ACD32'))
            if role == Qt.BackgroundRole and forceString(record.value('status')) == 'rejected':
                return QtCore.QVariant(QtGui.QColor('#FF4500'))
            if role == Qt.BackgroundRole and forceString(record.value('status')) == 'in-progress':
                return QtCore.QVariant(QtGui.QColor('#FFFFFF'))
        else:
            if role == Qt.CheckStateRole:
                flags = self.flags(index)
                if (flags & Qt.ItemIsUserCheckable and flags & Qt.ItemIsEnabled):
                    col = self._cols[column]
                    return col.toCheckState(QVariant(False), None)

        return QVariant()


class CAttachOnlineClientSearchDialog(CExternalClientSearchDialog):
    def __init__(self, parent, serviceRecord):
        defaultFilter = {
            'lastName': forceString(serviceRecord.value('lastName')),
            'firstName': forceString(serviceRecord.value('firstName')),
            'patrName': forceString(serviceRecord.value('patrName')),
            'birthDate': forceDate(serviceRecord.value('birthDate'))
        }
        self.serviceRecord = serviceRecord
        CExternalClientSearchDialog.__init__(self, parent, defaultFilter=defaultFilter, addInfo=u'Данные web-сервиса')
        self.externalInfo['lastName'] = self.infoStringValue(serviceRecord.value('lastName'))
        self.externalInfo['firstName'] = self.infoStringValue(serviceRecord.value('firstName'))
        self.externalInfo['patrName'] = self.infoStringValue(serviceRecord.value('patrName'))
        gender = serviceRecord.value('sex')
        gender = None if gender.isNull() else forceString(gender)
        self.externalInfo['sex'] = {'male': u"М", 'female': u"Ж"}.get(gender)
        self.externalInfo['birthDate'] = self.infoDateValue(serviceRecord.value('birthDate'))
        self.addObject('btnCreate', QtGui.QPushButton(u'Создать', self))
        self.connect(self.btnCreate, SIGNAL('clicked()'), self.on_btnCreate_clicked)
        self.buttonBox.addButton(self.btnCreate, QtGui.QDialogButtonBox.ActionRole)
        self.updateInfoText()
        self.createdPatient = False

    def addIgnoreButton(self):
        self.addObject('btnIgnore', QtGui.QPushButton(u'Пропустить', self))
        self.connect(self.btnIgnore, SIGNAL('clicked()'), self.on_btnIgnore_clicked)
        self.buttonBox.addButton(self.btnIgnore, QtGui.QDialogButtonBox.ActionRole)

    @pyqtSignature('')
    def on_btnCreate_clicked(self):
        db = QtGui.qApp.db

        documentTypeCode = forceString(self.serviceRecord.value('documentTypeCode'))
        tableDocumentType = db.table('rbDocumentType')
        tableDocumentTypeGroup = db.table('rbDocumentTypeGroup')
        queryTable = tableDocumentType.leftJoin(tableDocumentTypeGroup, tableDocumentTypeGroup['id'].eq(tableDocumentType['group_id']))
        docTypeRecord = db.getRecordEx(queryTable,
                                       tableDocumentType['id'].name(),
                                       [tableDocumentType['regionalCode'].eq(documentTypeCode),
                                        tableDocumentTypeGroup['code'].eq('1')])
        docType = forceRef(docTypeRecord.value('id'))
        docSerial = forceString(self.serviceRecord.value('documentSerial'))
        for c in '-=/_|':
            docSerial = docSerial.replace(c, ' ')
        docSerial = trim(docSerial).split()
        serialLeft = docSerial[0] if len(docSerial) >= 1 else ''
        serialRight = docSerial[1] if len(docSerial) >= 2 else ''
        if len(docSerial) == 1:
            if documentTypeCode == '14':
                serialLeft = docSerial[0][:2]
                serialRight = docSerial[0][-2:]
        docNumber = forceString(self.serviceRecord.value('documentNumber'))
        dialogInfo = {'lastName': forceString(self.serviceRecord.value('lastName')),
                      'firstName': forceString(self.serviceRecord.value('firstName')),
                      'patrName': forceString(self.serviceRecord.value('patrName')),
                      'birthDate': forceDate(self.serviceRecord.value('birthDate')),
                      'sex': {'male': 1, 'female': 2}.get(forceString(self.serviceRecord.value('sex'))),
                      'birthPlace': forceString(self.serviceRecord.value('birthPlace'))
                      }
        if docType:
            dialogInfo['docType'] = docType
            dialogInfo['serialLeft'] = serialLeft
            dialogInfo['serialRight'] = serialRight
            dialogInfo['docNumber'] = docNumber
            dialogInfo['docIssueDate'] = forceDate(self.serviceRecord.value('documentIssuedDate'))
            dialogInfo['docOrigin'] = forceString(self.serviceRecord.value('documentOrigin'))
            dialogInfo['docOriginCode'] = forceString(self.serviceRecord.value('documentOriginCode'))
        policyKind = forceInt(self.serviceRecord.value('policyType'))
        if policyKind:
            dialogInfo['polisType'] = forceRef(db.translate('rbPolicyType', 'code', '1', 'id'))
            dialogInfo['polisKind'] = forceRef(db.translate('rbPolicyKind', 'regionalCode', policyKind, 'id'))
            dialogInfo['polisSerial'] = forceString(self.serviceRecord.value('policySerial'))
            dialogInfo['polisNumber'] = forceString(self.serviceRecord.value('policyNumber'))
            policyOrgCode = forceString(self.serviceRecord.value('policyOrgCode'))
            policyOKATO = forceString(self.serviceRecord.value('policyOKATO'))
            policyOrgid = findOrgBySMOCode(policyOrgCode)
            if not policyOrgid:
                policyOrgid = findOrgByOKATO(policyOKATO)

            dialogInfo['polisCompany'] = policyOrgid
            dialogInfo['polisBegDate'] = forceDate(self.serviceRecord.value('policyBegDate'))
            dialogInfo['polisEndDate'] = forceDate(self.serviceRecord.value('policyEndDate'))

            dialogInfo['contactType'] = '3'
            dialogInfo['contact'] = forceString(self.serviceRecord.value('phone'))
            dialogInfo['regAddress'] = forceString(self.serviceRecord.value('regAddress'))
            dialogInfo['locAddress'] = forceString(self.serviceRecord.value('locAddress'))

        dialog = CClientEditDialog(self)
        dialog.setClientDialogInfo(dialogInfo)
        try:
            if dialog.exec_():
                self.clientId = dialog.itemId()
                self.createdPatient = True
                QtGui.QDialog.accept(self)
        finally:
            dialog.deleteLater()

    @pyqtSignature('')
    def on_btnIgnore_clicked(self):
        self.clientId = None
        QtGui.QDialog.accept(self)


def findOrgBySMOCode(smoCode):
    u"""Возвращает id и область страховой."""
    result = None
    db = QtGui.qApp.db
    table = db.table('Organisation')
    record = db.getRecordEx(table, 'id', [table['deleted'].eq(0),
                                          table['smoCode'].eq(smoCode),
                                          table['isActive'].eq(1)], 'id')
    if record:
        result = forceRef(record.value(0))
    return result


def findOrgByOKATO(okato):
    u"""Возвращает id и область страховой."""
    result = None
    db = QtGui.qApp.db
    table = db.table('Organisation')
    record = db.getRecordEx(table, 'id, area',  [table['deleted'].eq(0),
                                                 table['OKATO'].eq(okato),
                                                 table['isActive'].eq(1)], 'id')
    if record:
        result = forceRef(record.value(0))
    return result
