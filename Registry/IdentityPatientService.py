# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
import urlparse

import requests
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QVariant, pyqtSignature, QEvent

from Orgs.Utils import getOrganisationShortName
from Registry.Ui_IdentityPatientService import Ui_IdentityPatientServiceDialog
from Registry.Utils import getClientPolicyEx
from library.DialogBase import CDialogBase
from library.InDocTable import CRecordListModel, CInDocTableCol
from library.Utils import forceString, forceInt, forceRef, forceDate, toVariant, forceDateTime


def formatDateTime(value):
    if isinstance(value, QVariant):
        value = value.toDateTime()
        return unicode(value.toString('dd.MM.yyyy H:mm:ss'))
    if value is None:
        return ''


class CIdentityPatientServiceDialog(CDialogBase, Ui_IdentityPatientServiceDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.edtFilterRequestBegDate.setDate(QDate())
        self.edtFilterRequestEndDate.setDate(QDate())
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.addModels('IdentityPatient',    CIdentityPatientModel(self))
        self.setModels(self.tblIdentityPatient, self.modelIdentityPatient, self.selectionModelIdentityPatient)
        self.btnRefreshData.clicked.connect(self.refreshData)
        self.btnGetDataFromService.clicked.connect(self.getDataFromService)
        self.btnGetDataFromServiceAll.clicked.connect(self.getDataFromServiceAll)
        self.selectionModelIdentityPatient.currentRowChanged.connect(self.setInfoToFields)
        self.tblIdentityPatient.setSortingEnabled(True)
        self.tblIdentityPatient.installEventFilter(self)
        self.loadData()
        self.servicesURL = forceString(QtGui.qApp.getGlobalPreference('23:servicesURL'))
        if self.servicesURL:
            self.servicesURL = self.servicesURL.replace('\\\\', '//')
            self.servicesURL = urlparse.urljoin(self.servicesURL, '/api/IdentityPatient/fhir/')
        self.position = None

    def refreshData(self):
        """Кнопка Обновить данные в БД"""
        model = self.tblIdentityPatient.model()
        row = self.tblIdentityPatient.currentRow()
        clientId = forceRef(model.value(row, 'clientId'))

        if clientId:
            db = QtGui.qApp.db
            tableOrg = db.table('Organisation')
            tablePolicyKind = db.table('rbPolicyKind')
            tableClientPolicy = db.table('ClientPolicy')
            oldPolicyLabel = ''
            oldBegDate = None
            currentPolicyRecord = getClientPolicyEx(clientId, True)
            oldInsurerId = None
            oldEndDate = None
            if currentPolicyRecord:
                oldSerial = forceString(currentPolicyRecord.value('serial'))
                oldNumber = forceString(currentPolicyRecord.value('number'))
                oldInsurerId = forceRef(currentPolicyRecord.value('insurer_id'))
                oldBegDate = forceDate(currentPolicyRecord.value('begDate'))
                oldEndDate = forceString(currentPolicyRecord.value('endDate'))
                oldPolicyKindId = forceRef(currentPolicyRecord.value('policyKind_id'))
                oldInsurerName = getOrganisationShortName(oldInsurerId) if oldInsurerId else ''
                oldPolicyKindName = forceString(db.translate(tablePolicyKind, 'id', oldPolicyKindId, 'name')) if oldPolicyKindId else ''
                oldPolicyLabel = u'Текущий полис:\nСМО: %s\nсерия: %s\nномер: %s\nвид: %s\nдействителен с %s%s\n' % \
                                 (oldInsurerName, oldSerial, oldNumber, oldPolicyKindName, forceString(oldBegDate), u' по %s' % oldEndDate if oldEndDate else '')
            newPolicyKindCode = forceString(model.value(row, 'respPolicyKindCode'))
            newPolicyKindName = newPolicyKindCode
            newPolicyKindId = None
            pkRecord = db.getRecordEx(tablePolicyKind, 'id, name',
                                      tablePolicyKind['regionalCode'].eq(newPolicyKindCode), 'id')
            if pkRecord:
                newPolicyKindId = forceRef(pkRecord.value('id'))
                newPolicyKindName = forceString(pkRecord.value('name'))
            newPolicySerial = forceString(model.value(row, 'respPolicySerial'))
            newPolicyNumber = forceString(model.value(row, 'respPolicyNumber'))
            newPolicyBegDate = forceDate(model.value(row, 'respPolicyBegDate'))
            newPolicyEndDate = forceDate(model.value(row, 'respPolicyEndDate'))
            newInsurerCode = forceString(model.value(row, 'respInsurerCode'))
            newInsuranceArea = forceString(model.value(row, 'respInsuranceArea'))

            record = db.getRecordEx(tableOrg, 'id, shortName',
                                    [tableOrg['deleted'].eq(0),
                                     tableOrg['isActive'].eq(1),
                                     tableOrg['OKATO'].eq(newInsuranceArea),
                                     tableOrg['smoCode'].eq(newInsurerCode)], 'id')
            if record:
                newInsurerId = forceRef(record.value(0))
                newInsurerName = forceString(record.value(1))
            else:
                record = db.getRecordEx(tableOrg, 'id, shortName',
                                        [tableOrg['deleted'].eq(0), tableOrg['isActive'].eq(1),tableOrg['OKATO'].eq(newInsuranceArea)], 'id')
                newInsurerId = forceRef(record.value(0))
                newInsurerName = forceString(record.value(1))

            messageBox = QtGui.QMessageBox()
            messageBox.setIcon(QtGui.QMessageBox.Information)
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            messageBox.setWindowTitle(u'Обновление полисных данных')
            messageBox.setText(u'%s'
                               u'Новый полис:\n'
                               u'СМО: %s\n'
                               u'серия: %s\n'
                               u'номер: %s\n'
                               u'вид: %s\n'
                               u'действителен с %s%s\n'
                               u'Обновить данные?\n' % (
                               oldPolicyLabel, newInsurerName, newPolicySerial, newPolicyNumber, newPolicyKindName,
                               forceString(newPolicyBegDate),
                               u' по %s' % forceString(newPolicyEndDate) if newPolicyEndDate else '')
                               )

            btnUpdate = QtGui.QPushButton()
            btnAdd = QtGui.QPushButton()
            btnUpdate.setText(u'Обновить данные')
            btnAdd.setText(u'Добавить новую запись')
            messageBox.addButton(QtGui.QMessageBox.Cancel)
            # если дата начала полиса отличаются, то показывать кнопку добавить
            if newPolicyBegDate != oldBegDate or not currentPolicyRecord:
                messageBox.addButton(btnAdd, QtGui.QMessageBox.ActionRole)
                messageBox.setDefaultButton(btnAdd)
            else:
                messageBox.addButton(btnUpdate, QtGui.QMessageBox.ActionRole)
                messageBox.setDefaultButton(btnUpdate)
            messageBox.exec_()
            if messageBox.clickedButton() == btnAdd:
                record = tableClientPolicy.newRecord()
                record.setValue('client_id', toVariant(clientId))
                record.setValue('insurer_id', toVariant(newInsurerId))
                record.setValue('policyType_id', db.translate('rbPolicyType', 'code', '1', 'id'))
                record.setValue('policyKind_id', toVariant(newPolicyKindId))
                if newPolicyBegDate:
                    record.setValue('begDate', toVariant(newPolicyBegDate))
                if newPolicyEndDate:
                    record.setValue('endDate', toVariant(newPolicyEndDate))
                record.setValue('checkDate', toVariant(forceDate(model.value(row, 'responseDatetime'))))
                record.setValue('serial', toVariant(newPolicySerial))
                record.setValue('number', toVariant(newPolicyNumber))
                record.setValue('note', toVariant(u'Получен из сервиса «ИДЕНТИФИКАЦИЯ ГРАЖДАН В СФЕРЕ ОМС» от {0}'.format(QDate().currentDate().toString('dd.MM.yyyy'))))
                db.insertRecord(tableClientPolicy, record)
                if currentPolicyRecord and not oldEndDate:
                    if newPolicyBegDate.addDays(-1) >= forceDate(currentPolicyRecord.value('begDate')):
                        currentPolicyRecord.setValue('endDate', toVariant(newPolicyBegDate.addDays(-1)))
                    else:
                        currentPolicyRecord.setValue('endDate', toVariant(currentPolicyRecord.value('begDate')))
                    currentPolicyRecord.setValue('note', toVariant(u'Обновлен из сервиса «ИДЕНТИФИКАЦИЯ ГРАЖДАН В СФЕРЕ ОМС» от {0}'.format(QDate().currentDate().toString('dd.MM.yyyy'))))
                    currentPolicyRecord.remove(currentPolicyRecord.indexOf('compulsoryServiceStop'))
                    currentPolicyRecord.remove(currentPolicyRecord.indexOf('voluntaryServiceStop'))
                    currentPolicyRecord.remove(currentPolicyRecord.indexOf('area'))
                    currentPolicyRecord.remove(currentPolicyRecord.indexOf('enp'))
                    db.updateRecord(tableClientPolicy, currentPolicyRecord)
            elif messageBox.clickedButton() == btnUpdate:
                if newInsurerId and newInsurerId != oldInsurerId:
                    currentPolicyRecord.setValue('insurer_id', toVariant(newInsurerId))
                currentPolicyRecord.setValue('serial', toVariant(newPolicySerial))
                currentPolicyRecord.setValue('number', toVariant(newPolicyNumber))
                currentPolicyRecord.setValue('policyKind_id', toVariant(newPolicyKindId))
                if newPolicyEndDate:
                    currentPolicyRecord.setValue('endDate', toVariant(newPolicyEndDate))
                else:
                    currentPolicyRecord.setValue('endDate', QVariant())
                currentPolicyRecord.setValue('checkDate', toVariant(forceDate(model.value(row, 'responseDatetime'))))
                currentPolicyRecord.setValue('note', toVariant(u'Получен из сервиса «ИДЕНТИФИКАЦИЯ ГРАЖДАН В СФЕРЕ ОМС» от {0}'.format(QDate().currentDate().toString('dd.MM.yyyy'))))
                currentPolicyRecord.remove(currentPolicyRecord.indexOf('compulsoryServiceStop'))
                currentPolicyRecord.remove(currentPolicyRecord.indexOf('voluntaryServiceStop'))
                currentPolicyRecord.remove(currentPolicyRecord.indexOf('area'))
                currentPolicyRecord.remove(currentPolicyRecord.indexOf('enp'))
                db.updateRecord(tableClientPolicy, currentPolicyRecord)

    def getDataFromService(self):
        """Кнопка Получить информацию из сервиса"""
        model = self.tblIdentityPatient.model()
        row = self.tblIdentityPatient.currentRow()
        if forceDate(model.value(row, 'responseDatetime')):
            QtGui.QMessageBox().information(self, u'Информация', u'На данный запрос ранее уже получен ответ!')
            return
        if self.servicesURL:
            identId = forceRef(model.value(row, 'id'))
            if identId:
                if QtGui.QMessageBox().question(self, u'Внимание!',
                                                u'Проверить информацию по запросу\n'
                                                u'в Web-сервере "Идентификации граждан в сфере ОМС"?',
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                    params = {'strah_ident_id': identId}
                    try:
                        response = requests.get(self.servicesURL + '$getIdentityPatient', params)
                        jsonData = response.json()
                        if jsonData.get('result', '') == "success":
                            db = QtGui.qApp.db
                            table = db.table('soc_IdentityPatient')
                            record = db.getRecord(table, [table['responseDatetime'],
                                                          table['errorDateResponse'],
                                                          table['errorMessageResponse']],
                                                  identId)
                            if record:
                                if forceDate(record.value('errorDateResponse')):
                                    if forceString(record.value('errorMessageResponse')) == '':
                                        message = u'Ошибка не указана!'
                                    else:
                                        message = forceString(record.value('errorMessageResponse'))
                                else:
                                    message = u'Получен успешный ответ!'
                                QtGui.QMessageBox().information(self, u'Информация', message)
                                model.updateData(identId, row)
                                model.emitRowChanged(row)
                                self.setInfoToFields(row, row)
                                self.tblIdentityPatient.setCurrentRow(row)
                        else:
                            self.tblIdentityPatient.setCurrentRow(row)
                            QtGui.QMessageBox().critical(self, u'Ошибка',
                                                         u"Возвращен неверный формат ответа!",
                                                         QtGui.QMessageBox.Close)
                    except Exception, e:
                        self.tblIdentityPatient.setCurrentRow(row)
                        QtGui.QMessageBox().critical(self, u'Ошибка',
                                                     u'Произошла ошибка: ' + unicode(e),
                                                     QtGui.QMessageBox.Close)

    def getDataFromServiceAll(self):
        """Кнопка Получить информацию из сервиса по всем запросам"""
        if self.servicesURL:
            if QtGui.QMessageBox().question(self, u'Внимание!',
                                            u'Проверить информацию по всем запросам\n'
                                            u'в Web-сервере "Идентификации граждан в сфере ОМС"?',
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                            QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                params = {'strah_ident_id': 0}
                try:
                    response = requests.get(self.servicesURL + '$getIdentityPatient', params)
                    jsonData = response.json()
                    if jsonData.get('result', '') == "success":
                        success = jsonData["count_success"]
                        errors = jsonData["count_error"]
                        message = u'Данные получены успешно!\nУспешно обновлены: %s, не обновлены: %s' % (success, errors)
                        QtGui.QMessageBox().information(self, u'Информация', message)
                        self.applyFilters()
                    else:
                        QtGui.QMessageBox().critical(self, u'Ошибка', u"Возвращен неверный формат ответа!",
                                                     QtGui.QMessageBox.Close)
                except Exception, e:
                    QtGui.QMessageBox().critical(self, u'Ошибка', u'Произошла ошибка: ' + unicode(e),
                                                 QtGui.QMessageBox.Close)

    def applyFilters(self):
        self.clearFields()
        filters = dict.fromkeys(['lastName', 'firstName', 'patrName', 'requestType',
                                 'requestBegDate', 'requestEndDate'])
        lastName = forceString(self.edtFilterLastName.text())
        firstName = forceString(self.edtFilterFirstName.text())
        patrName = forceString(self.edtFilterPatrName.text())
        requestBegDate = self.edtFilterRequestBegDate.date()
        requestEndDate = self.edtFilterRequestEndDate.date()
        responseType = forceInt(self.cmbResponseFilter.currentIndex())
        if lastName:
            filters['lastName'] = lastName
        if firstName:
            filters['firstName'] = firstName
        if patrName:
            filters['patrName'] = patrName
        if requestBegDate:
            filters['requestBegDate'] = requestBegDate
        if requestEndDate:
            filters['requestEndDate'] = requestEndDate
        filters['responseType'] = responseType

        self.loadData(filters)

    def resetFilters(self):
        self.clearFields()
        self.edtFilterLastName.clear()
        self.edtFilterFirstName.clear()
        self.edtFilterPatrName.clear()
        self.edtFilterRequestBegDate.setDate(QDate())
        self.edtFilterRequestEndDate.setDate(QDate())
        self.cmbResponseFilter.setCurrentIndex(0)
        self.loadData()

    def loadData(self, filters=None):
        self.tblIdentityPatient.model().loadData(filters)
        self.tblIdentityPatient.setCurrentRow(0)

    def setInfoToFields(self, current, previous):
        self.clearFields()
        model = self.tblIdentityPatient.model()
        row = self.tblIdentityPatient.currentRow()

        self.edtClientId.setText(forceString(model.value(row, 'clientId')))
        self.edtRequestDate.setText(formatDateTime(model.value(row, 'createDatetime')))
        self.edtLastName.setText(forceString(model.value(row, 'lastName')))
        self.edtFirstName.setText(forceString(model.value(row, 'firstName')))
        self.edtPatrName.setText(forceString(model.value(row, 'patrName')))
        self.edtBirthDate.setText(forceString(model.value(row, 'birthDate')))
        self.edtDocumentTypeCode.setText(forceString(model.value(row, 'documentTypeName')))
        self.edtSerial.setText(forceString(model.value(row, 'serial')))
        self.edtNumber.setText(forceString(model.value(row, 'number')))
        self.edtPolicyKindCode.setText(forceString(model.value(row, 'policyKindName')))
        self.edtPolicySerial.setText(forceString(model.value(row, 'policySerial')))
        self.edtPolicyNumber.setText(forceString(model.value(row, 'policyNumber')))
        self.edtCodeMO.setText(forceString(model.value(row, 'org_guid')))
        self.edtServerId.setText(forceString(model.value(row, 'requestMessageId')))
        if forceString(model.value(row, 'errorMessageResponse')):
            self.setVisibleResponse(True)
            self.edtErrorDate.setText(formatDateTime(model.value(row, 'errorDateResponse')))
            self.edtError.setText(forceString(model.value(row, 'errorMessageResponse')))
            self.btnRefreshData.setEnabled(False)
        else:
            self.setVisibleResponse(False)
            if forceDate(model.value(row, 'responseDatetime')):
                self.btnRefreshData.setEnabled(True)
            else:
                self.btnRefreshData.setEnabled(False)
            self.edtResponseInfoDate.setText(forceString(model.value(row, 'responseDatetime')))
            self.edtResponsePolicyType.setText(forceString(model.value(row, 'respPolicyKind')))
            self.edtResponsePolicySerial.setText(forceString(model.value(row, 'respPolicySerial')))
            self.edtResponsePolicyNumber.setText(forceString(model.value(row, 'respPolicyNumber')))
            self.edtResponseBegDate.setText(forceString(model.value(row, 'respPolicyBegDate')))
            self.edtResponseEndDate.setText(forceString(model.value(row, 'respPolicyEndDate')))
            self.edtResponseOKATO.setText(forceString(model.value(row, 'respInsuranceArea')))
            self.edtResponseCodeSMO.setText(forceString(model.value(row, 'respInsurerCode')))
            self.edtResponseCodeSMOInfo.setText(forceString(model.value(row, 'respInsurerName')))

    def setVisibleResponse(self, isError):
        notError = False if isError else True
        self.lblErrorDate.setVisible(isError)
        self.lblError.setVisible(isError)
        self.edtErrorDate.setVisible(isError)
        self.edtError.setVisible(isError)

        self.lblResponseInfoDate.setVisible(notError)
        self.lblResponsePolicyType.setVisible(notError)
        self.lblResponsePolicySerial.setVisible(notError)
        self.lblResponsePolicyNumber.setVisible(notError)
        self.lblResponseBegDate.setVisible(notError)
        self.lblResponseEndDate.setVisible(notError)
        self.lblResponseOKATO.setVisible(notError)
        self.lblResponseCodeSMO.setVisible(notError)
        self.edtResponseInfoDate.setVisible(notError)
        self.edtResponsePolicyType.setVisible(notError)
        self.edtResponsePolicySerial.setVisible(notError)
        self.edtResponsePolicyNumber.setVisible(notError)
        self.edtResponseBegDate.setVisible(notError)
        self.edtResponseEndDate.setVisible(notError)
        self.edtResponseOKATO.setVisible(notError)
        self.edtResponseCodeSMO.setVisible(notError)
        self.edtResponseCodeSMOInfo.setVisible(notError)

    def clearFields(self):
        self.edtClientId.clear()
        self.edtRequestDate.clear()
        self.edtLastName.clear()
        self.edtFirstName.clear()
        self.edtPatrName.clear()
        self.edtBirthDate.clear()
        self.edtDocumentTypeCode.clear()
        self.edtSerial.clear()
        self.edtNumber.clear()
        self.edtPolicyKindCode.clear()
        self.edtPolicySerial.clear()
        self.edtPolicyNumber.clear()
        self.edtCodeMO.clear()
        self.edtServerId.clear()
        self.edtErrorDate.clear()
        self.edtError.clear()
        self.edtResponseInfoDate.clear()
        self.edtResponsePolicyType.clear()
        self.edtResponsePolicySerial.clear()
        self.edtResponsePolicyNumber.clear()
        self.edtResponseBegDate.clear()
        self.edtResponseEndDate.clear()
        self.edtResponseOKATO.clear()
        self.edtResponseCodeSMO.clear()
        self.edtResponseCodeSMOInfo.clear()

    @pyqtSignature('QModelIndex')
    def on_tblIdentityPatient_doubleClicked(self, index):
        if index.isValid():
            self.getDataFromService()

    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxClient_clicked(self, button):
        buttonCode = self.buttonBoxClient.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.applyFilters()
            self.btnGetDataFromService.setFocus()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetFilters()
            self.btnGetDataFromService.setFocus()


    def eventFilter(self, watched, event):
        if watched == self.tblIdentityPatient:
            if event.type() == QEvent.ShortcutOverride and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                return True
        return CDialogBase.eventFilter(self, watched, event)

class CIdentityPatientModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Фамилия', 'lastName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Имя', 'firstName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Отчество', 'patrName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата рождения', 'birthDate', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата запроса', 'createDatetime', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата ответа', 'responseDatetime', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Результат ответа', 'hasErrorCodeResponse', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Ошибка', 'errorMessageResponse', 20)).setReadOnly()
        # self.addCol(CInDocTableCol(u'Данные обновлены', '', 20)).setReadOnly()
        self.headerSortingCol = {}

    def getTableQuery(self, filters=None, _id=None):
        db = QtGui.qApp.db
        tableIdentityPatient = db.table('soc_IdentityPatient')
        tableRbDocumentType = db.table('rbDocumentType')
        tableRbPolicyKind = db.table('rbPolicyKind')
        tableRbRespPolicyKind = db.table('rbPolicyKind').alias('respPolicy')
        tableQuery = tableIdentityPatient
        tableQuery = tableQuery.leftJoin(tableRbDocumentType, tableRbDocumentType['regionalCode'].eq(
            tableIdentityPatient['documentTypeCode']))
        tableQuery = tableQuery.leftJoin(tableRbPolicyKind,
                                         tableIdentityPatient['policyKindCode'].eq(tableRbPolicyKind['code']))
        tableQuery = tableQuery.leftJoin(tableRbRespPolicyKind,
                                         tableIdentityPatient['respPolicyKindCode'].eq(tableRbRespPolicyKind['code']))
        cols = [tableIdentityPatient['id'],
                tableIdentityPatient['client_id'].alias('clientId'),
                tableIdentityPatient['lastName'],
                tableIdentityPatient['firstName'],
                tableIdentityPatient['patrName'],
                tableIdentityPatient['birthDate'],
                tableIdentityPatient['createDatetime'],
                tableIdentityPatient['responseDatetime'],
                u"""IF (soc_IdentityPatient.errorDateResponse , 'Ошибка', (IF (soc_IdentityPatient.responseDatetime, 'Успешно', 'Не обработан'))) as hasErrorCodeResponse""",
                tableIdentityPatient['errorMessageResponse'],
                tableRbDocumentType['name'].alias('documentTypeName'),
                tableIdentityPatient['documentTypeCode'],
                tableIdentityPatient['serial'],
                tableIdentityPatient['number'],
                tableIdentityPatient['policyKindCode'],
                tableRbPolicyKind['name'].alias('policyKindName'),
                tableIdentityPatient['policySerial'],
                tableIdentityPatient['policyNumber'],
                tableIdentityPatient['errorDateResponse'],
                tableIdentityPatient['requestMessageId'],
                tableIdentityPatient['org_guid'],

                tableRbRespPolicyKind['name'].alias('respPolicyKind'),
                tableIdentityPatient['respPolicyKindCode'],
                tableIdentityPatient['respPolicySerial'],
                tableIdentityPatient['respPolicyNumber'],
                tableIdentityPatient['respInsurerCode'],
                tableIdentityPatient['respInsurerName'],
                tableIdentityPatient['respPolicyBegDate'],
                tableIdentityPatient['respPolicyEndDate'],
                tableIdentityPatient['respInsuranceArea']]
        cond = []
        if _id:
            cond.append(tableIdentityPatient['id'].eq(_id))
        elif filters:
            lastName = filters['lastName']
            firstName = filters['firstName']
            patrName = filters['patrName']
            requestBegDate = filters['requestBegDate']
            requestEndDate = filters['requestEndDate']
            responseType = filters['responseType']

            if lastName:
                cond.append("soc_IdentityPatient.lastName like '%s%%'" % lastName)
            if firstName:
                cond.append("soc_IdentityPatient.firstName like '%s%%'" % firstName)
            if patrName:
                cond.append("soc_IdentityPatient.patrName like '%s%%'" % patrName)

            if requestBegDate and requestEndDate:
                cond.append(tableIdentityPatient['createDatetime'].ge(requestBegDate))
                cond.append(tableIdentityPatient['createDatetime'].lt(requestEndDate.addDays(1)))
            elif requestBegDate:
                cond.append(tableIdentityPatient['createDatetime'].ge(requestBegDate))
            elif requestEndDate:
                cond.append(tableIdentityPatient['createDatetime'].lt(requestEndDate.addDays(1)))

            if responseType == 1:
                cond.append("""soc_IdentityPatient.responseDatetime IS NULL 
                                    and soc_IdentityPatient.errorDateResponse IS NULL""")
            if responseType == 2:
                cond.append("""soc_IdentityPatient.responseDatetime IS NOT NULL 
                                    and soc_IdentityPatient.errorDateResponse IS NULL""")
            if responseType == 3:
                cond.append("""soc_IdentityPatient.responseDatetime IS NULL 
                                    and soc_IdentityPatient.errorDateResponse IS NOT NULL""")
        return tableQuery, cols, cond

    def loadData(self, filters=None):
        db = QtGui.qApp.db
        tableQuery, cols, cond = self.getTableQuery(filters)
        records = db.getRecordList(tableQuery, cols, cond)
        self.setItems(records)
        for col, order in self.headerSortingCol.items():
            self.sort(col, order)

    def updateData(self, _id, row):
        db = QtGui.qApp.db
        tableQuery, cols, cond = self.getTableQuery(filters=None, _id=_id)
        record = db.getRecordEx(tableQuery, cols, cond)
        self._items[row] = record
        for col, order in self.headerSortingCol.items():
            self.sort(col, order)

    def sort(self, col, order=Qt.AscendingOrder):
        self.headerSortingCol = {col: order}
        reverse = order == Qt.DescendingOrder
        if col in [3, 4, 5]:
            self._items.sort(key=lambda x: forceDateTime(x.value(col+2)) if x else None, reverse=reverse)
        elif col == 6:
            self._items.sort(key=lambda x: forceString(x.value(col+2)) if x else None, reverse=reverse)
        else:
            self._items.sort(key=lambda x: forceString(x.value(col+2)).lower() if x else None, reverse=reverse)
        self.reset()
