# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import re
import csv
from datetime import datetime, timedelta
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QDate
from Reports.ReportView import CReportViewDialog
from Reports.ReportBase import CReportBase, createTable
from Exchange.Utils import tbl
from library.Utils import forceString, toVariant, forceInt, forceDate
from Events.Action import CActionTypeCache, CAction, initActionProperties
from Events.Utils import getEventFinanceId, getActionTypeIdListByFlatCode

from Ui_ImportCSVClient import Ui_ImportCSVClient


class ImportCSVClient(QtGui.QDialog, Ui_ImportCSVClient):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent
        self.setWindowTitle(u"Импорт данных из санаторной программы")

        self.progressBar.setValue(0)
        self.btnStart.setEnabled(False)

        self.db = QtGui.qApp.db
        self.file = None
        self.progress = 0
        self.maxstr = 0
        self.status = True

        self.error = {}
        self.allList = {}
        self.newClient = []  # Новых
        self.oldClient = []  # Измененых
        self.noImport = []   # Не заполненых

        self.tableClient = tbl('Client')
        self.tableClientAddress = tbl('ClientAddress')
        self.tableClientDocument = tbl('ClientDocument')
        self.tableDocumentType = tbl('rbDocumentType')
        self.tableClientDocumentTracking = tbl('Client_DocumentTracking')
        self.tableClientStatusObservation = tbl('Client_StatusObservation')
        self.tableDocumentTypeForTracking = tbl('rbDocumentTypeForTracking')
        self.tableClientSocStatus = tbl('ClientSocStatus')
        self.tableSocStatusType = tbl('rbSocStatusType')
        self.tableSocStatusClass = tbl('rbSocStatusClass')

        self.tableStatusObservationClientType = tbl('rbStatusObservationClientType')
        self.tableOrgStructurePlacement = tbl('OrgStructure_Placement')

        self.tableEvent = tbl('Event')
        self.tableEventVoucher = tbl('Event_Voucher')

        self.tableAction = tbl('Action')

        self.tableName = {
            "colLastName": u"Не указана Фамилия (A)",
            "colFirstName": u"Не указано Имя (B)",
            "colStatusHouse": u"Статус проживания не указан либо не равен 'Проживает' (D)",
            "colEventId": u"Не указан уникальный код идентификации счета гостя (E)",
            "colClientId": u"Не указан уникальный код идентификации гостя (F)",
            "colDateCheckIn": u"Не указан период проживания (G)",
            "colDateCheckOut": u"Не указан период проживания (H)",
            "colRoomNumber": u"Не указан номер комнаты (J)",
            "colTypeDul": u"Не указан Тип ДУЛ (K)",
            "colSeriaNumberDul": u"Не указана серия, номер ДУЛ (L)",
            "colBirthDate": u"Не указана дата рождения (M)",
            "colDateDul": u"Не указана дата выдачи ДУЛ (P)",
            "colStreet": u"Не указана улица регистрации (Q)",
            "colCity": u"Не указан город регистрации (R)",
            "colCountrySubjectRF": u"Не указана cтрана или субъект РФ (S)",
            "colHouse": u"Не указан дом, квартира (T)"
        }


    @pyqtSignature('')
    def on_btnImportCSV_clicked(self):
        self.file = QtGui.QFileDialog.getOpenFileName(
            self, u'Укажите файл с данными', u'', u'Файл CSV (*.csv)')

        if forceString(self.file):
            self.btnStart.setEnabled(True)
            self.fileName.setText(forceString(self.file))

            self.maxstr = sum(1 for line in open(u"{0}".format(forceString(self.file)), 'rb'))

            self.numberAllClients.setText(forceString(self.maxstr))
        else:
            self.btnStart.setEnabled(False)
            self.fileName.setText(u'-')
            self.numberAllClients.setText(u'0')

        self.numberAddClients.setText(u'0')
        self.numberUpDateClients.setText(u'0')
        self.numberNoAddClients.setText(u'0')
        self.progressBar.setValue(0)


    @pyqtSignature('')
    def on_btnStart_clicked(self):
        self.numberAddClients.setText(str(0))
        self.numberUpDateClients.setText(str(0))
        self.numberNoAddClients.setText(str(0))

        self.btnStart.setEnabled(False)
        self.btnImportCSV.setEnabled(False)
        self.allList = {}
        self.newClient = []  # Новых
        self.oldClient = []  # Уже имеется записей
        self.noImport = []  # Не заполненых

        x = 0

        if forceString(self.file):
            csvreader = csv.reader(open(forceString(self.file), 'rb'), delimiter=';', quotechar=' ')
            for row in csvreader:
                x += 1
                # ! - Обязательные поля
                # !A	- Фамилия
                colLastName = row[0].decode('cp1251')
                # !B	- Имя
                colFirstName = row[1].decode('cp1251')
                # C	- Отчество
                colPatrName = row[2].decode('cp1251')
                #  !D	- Статус проживания (ПРОЖИВАЕТ, ВЫЕХАЛ)
                colStatusHouse = row[3].decode('cp1251')
                # !E	- уникальный код идентификации счета гостя, уникален на комнату
                colEventId = row[4].decode('cp1251')
                # !F	- уникальный код идентификации гостя
                colClientId = row[5].decode('cp1251')
                # 6,7 !G,H - период проживания (заезд/выезд)
                colDateCheckIn = row[6].decode('cp1251')
                # 6,7 !G,H - период проживания (заезд/выезд)
                colDateCheckOut = row[7].decode('cp1251')
                # I	- тариф путевки
                colPackagePrice = row[8].decode('cp1251')
                # !J	- Номер комнаты (формат 310, 310.1)
                colRoomNumber = row[9].decode('cp1251')
                # !K	- Тип ДУЛ* (Иностранный паспорт, Паспорт гражданина РФ, Свидетельство о рождении)
                colTypeDul = row[10].decode('cp1251')
                # !L	- Серия, номер ДУЛ (формат 8 008 620 186, 305 996 777 (без левого ноля),
                # VII-МЮ 897362 (наличие правых пробелов), N13298344 (наличие правых пробелов))
                colSeriaNumberDul = row[11].decode('cp1251')
                # !M	- Дата рождения
                colBirthDate = row[12].decode('cp1251')
                # !N	- Код подразделения ДУЛ
                colCodeStructureDul = row[13].decode('cp1251')
                # !O	- Кем выдан ДУЛ
                colWhomByDul = row[14].decode('cp1251')
                # !P	- Дата выдачи ДУЛ
                colDateDul = row[15].decode('cp1251')
                # !Q	- Улица (без типа) регистрации
                colStreet = row[16].decode('cp1251')
                # !R	- Город регистрации
                colCity = row[17].decode('cp1251')
                # !S	- Страна или субъект РФ
                colCountrySubjectRF = row[18].decode('cp1251')
                # !T	- Дом, квартира (формат  дом 62 корп 7 кв 428, дом 49 кв 121, дом 95)
                colHouse = row[19].decode('cp1251')
                # U	- Место рождения
                colCityBirth = row[20].decode('cp1251')
                # V	- Страна
                colCountry = row[21].decode('cp1251')

                if (colFirstName or colPatrName or colStatusHouse or colEventId or colClientId or colDateCheckIn or
                        colDateCheckOut or colPackagePrice or colRoomNumber or colTypeDul or colSeriaNumberDul or
                        colBirthDate or colCodeStructureDul or colWhomByDul or colDateDul or colStreet or colCity or
                        colCountrySubjectRF or colHouse or colCityBirth or colCountry):

                    self.allList[colClientId] = [colLastName.lower().title(), colFirstName.lower().title(),
                                                 colPatrName.lower().title(), colStatusHouse, colEventId,
                                                 colDateCheckIn, colDateCheckOut, colPackagePrice, colRoomNumber,
                                                 colTypeDul, colSeriaNumberDul, colBirthDate, colCodeStructureDul,
                                                 colWhomByDul, colDateDul, colStreet, colCity, colCountrySubjectRF,
                                                 colHouse, colCityBirth, colCountry]

                    if ((colLastName and colFirstName and colStatusHouse and colEventId and
                        colClientId and colDateCheckIn and colDateCheckOut and colRoomNumber and
                        colTypeDul and colSeriaNumberDul and colBirthDate and
                        colDateDul and colStreet and colCity and colCountrySubjectRF and colHouse) and
                            colStatusHouse.upper() == u"ПРОЖИВАЕТ"):

                        clientRecord = self.db.getRecordEx(
                            self.tableClient,
                            'id, lastName, firstName, patrName',
                            u"""lastName = '{0}' AND firstName = '{1}' AND patrName = '{2}' AND birthDate = '{3}'
                            """.format(colLastName.lower().title(),
                                       colFirstName.lower().title(),
                                       colPatrName.lower().title(),
                                       forceString(self.getDate(colBirthDate))
                                       )
                        )

                        clientId = None
                        lastName = None
                        firstName = None
                        patrName = None

                        if clientRecord:
                            clientId = forceInt(clientRecord.value('id'))
                            lastName = forceString(clientRecord.value('lastName'))
                            firstName = forceString(clientRecord.value('firstName'))
                            patrName = forceString(clientRecord.value('patrName'))

                        if not clientId:
                            # Добавляем нового
                            self.db.transaction()

                            # Client
                            sRecordClient = self.tableClient.newRecord()
                            sRecordClient.setValue('lastName', colLastName.lower().title())
                            sRecordClient.setValue('firstName', colFirstName.lower().title())
                            if colPatrName:
                                sRecordClient.setValue('patrName', colPatrName.lower().title())
                            sRecordClient.setValue('sex', self.getSexClient(colFirstName, colPatrName))
                            sRecordClient.setValue('birthDate', toVariant(self.getDate(colBirthDate)))
                            if colCityBirth:
                                sRecordClient.setValue('birthPlace', self.getColCityBirth(colCityBirth))
                            clientId = self.db.insertRecord(self.tableClient, sRecordClient)

                            # Client_DocumentTracking
                            sRecordClientDocumentTracking = self.tableClientDocumentTracking.newRecord()
                            sRecordClientDocumentTracking.setValue('client_id', forceInt(clientId))
                            documentTypeForTracking_id = self.db.getRecordEx(
                                self.tableDocumentTypeForTracking,
                                ['id'],
                                u"name LIKE '%Уникальный код идентификации гостя%'")
                            sRecordClientDocumentTracking.setValue('documentTypeForTracking_id',
                                                                   forceInt(documentTypeForTracking_id.value('id')))
                            sRecordClientDocumentTracking.setValue('documentNumber', forceInt(colClientId))
                            sRecordClientDocumentTracking.setValue('documentDate', toVariant(QDate.currentDate()))
                            self.db.insertRecord(self.tableClientDocumentTracking, sRecordClientDocumentTracking)

                            # ClientAddress
                            sRecordClientAddress = self.tableClientAddress.newRecord()
                            sRecordClientAddress.setValue('client_id', forceInt(clientId))
                            house = re.findall(r'(\D+)(\d+)', colHouse)
                            house = [pair[0].replace(u" ", u"") + u" " + pair[1].replace(u" ", u"") for pair in house]
                            house = u" ".join(house)
                            sRecordClientAddress.setValue('freeInput', u"г.{0}, ул.{1}, {2}".format(
                                colCity.lower().title(), colStreet.lower().title(), house))
                            self.db.insertRecord(self.tableClientAddress, sRecordClientAddress)

                            # ClientDocument
                            documentTypeId = self.db.getRecordEx(
                                self.tableDocumentType,
                                ['id'],
                                u"title LIKE '%{0}%'".format(
                                    colTypeDul.replace(u'РФ', u'Российской Федерации')))
                            if not documentTypeId and u"Иност" in colTypeDul:
                                documentTypeId = self.db.getRecordEx(
                                    self.tableDocumentType,
                                    ['id'],
                                    u"code = '24'")
                            if documentTypeId:
                                sRecordClientDocument = self.tableClientDocument.newRecord()
                                sRecordClientDocument.setValue('documentType_id', forceInt(documentTypeId.value('id')))
                                if colCodeStructureDul:
                                    sRecordClientDocument.setValue('originCode', colCodeStructureDul)
                                sRecordClientDocument.setValue('origin', colWhomByDul if colWhomByDul else u"")
                                sRecordClientDocument.setValue('date', forceDate(toVariant(self.getDate(colDateDul))))
                                sRecordClientDocument.setValue('client_id', forceInt(clientId))
                                serial, number = self.hetSeriaNumber(colSeriaNumberDul)
                                sRecordClientDocument.setValue('serial',  serial)
                                sRecordClientDocument.setValue('number', number)
                                self.db.insertRecord(self.tableClientDocument, sRecordClientDocument)

                                # ClientSocStatus
                                sRecordClientSocStatus = self.tableClientSocStatus.newRecord()
                                sRecordClientSocStatus.setValue('client_id', clientId)
                                sscId = self.db.getRecordEx(
                                    self.tableSocStatusClass,
                                    ['id'],
                                    u"name LIKE '%гражданство%'")
                                if sscId:
                                    sRecordClientSocStatus.setValue('socStatusClass_id', forceInt(sscId.value(0)))
                                sstId = self.db.getRecordEx(
                                    self.tableSocStatusType,
                                    ['id'],
                                    u"name LIKE '%{0}%'".format(colCountry))
                                if sstId:
                                    sRecordClientSocStatus.setValue('socStatusType_id', forceInt(sstId.value(0)))
                                self.db.insertRecord(self.tableClientSocStatus, sRecordClientSocStatus)

                                # Client_StatusObservation
                                sRecordClientStatusObservation = self.tableClientStatusObservation.newRecord()
                                sRecordClientStatusObservation.setValue('master_id', clientId)
                                sotId = self.db.getRecordEx(
                                    self.tableStatusObservationClientType,
                                    ['id'],
                                    u"name = '{0}'".format(colPackagePrice))
                                if sotId:
                                    sRecordClientStatusObservation.setValue('statusObservationType_id',
                                                                            forceInt(sotId.value('id')))
                                else:
                                    sRecordStatusObservationClientType = self.tableStatusObservationClientType.newRecord()
                                    sRecordStatusObservationClientType.setValue('code', u"ОЗД")
                                    sRecordStatusObservationClientType.setValue('name', forceString(colPackagePrice))
                                    sRecordStatusObservationClientType.setValue('color', u'#66FF00')
                                    sRecordStatusObservationClientType.setValue('removeStatus', 1)
                                    soctId = self.db.insertRecord(self.tableStatusObservationClientType,
                                                                  sRecordStatusObservationClientType)
                                    sRecordClientStatusObservation.setValue('statusObservationType_id', forceInt(soctId))
                                self.db.insertRecord(self.tableClientStatusObservation, sRecordClientStatusObservation)

                                self.newClient.append(colClientId)
                                self.db.commit()
                            else:
                                self.noImport.append(colClientId)
                                self.error[colClientId] = [
                                    u"Не найдена подходящая запись для '{0}' поле (K) Тип ДУЛ".format(colTypeDul)]
                                self.db.rollback()
                        else:
                            documentTypeRecord = self.db.getRecordEx(
                                self.tableDocumentTypeForTracking,
                                ['id'],
                                u"name LIKE '%Уникальный код идентификации гостя%'")
                            if documentTypeRecord:
                                documentTypeId = forceInt(documentTypeRecord.value('id'))

                                documentTrackingRecord = self.db.getRecordEx(self.tableClientDocumentTracking, '*',
                                                         """client_id = {0} AND documentTypeForTracking_id = {1}""".format(clientId, documentTypeId))
                                if documentTrackingRecord:
                                    if forceInt(colClientId) != forceInt(documentTrackingRecord.value('documentNumber')):
                                        documentTrackingRecord.setValue('documentNumber', forceInt(colClientId))
                                        self.db.updateRecord(self.tableClientDocumentTracking, documentTrackingRecord)

                            self.allList[colClientId] = [
                                lastName, firstName, patrName, colStatusHouse, colEventId, colDateCheckIn,
                                colDateCheckOut, colPackagePrice, colRoomNumber, colTypeDul, colSeriaNumberDul,
                                colBirthDate, colCodeStructureDul, colWhomByDul, colDateDul, colStreet, colCity,
                                colCountrySubjectRF, colHouse, colCityBirth, colCountry
                            ]

                            self.oldClient.append(colClientId)

                        eventId = self.db.getRecordEx(
                            self.tableEvent,
                            ['id'],
                            "client_id = '{0}' and externalId = '{1}'".format(clientId, colEventId))
                        if not eventId:
                            self.db.transaction()

                            try:
                                # Event
                                sRecordEvent = self.tableEvent.newRecord()

                                g = forceDate(self.getDate(colDateCheckIn))
                                h = forceDate(self.getDate(colDateCheckOut))

                                eventTypeId = 55  # Санаторно-курортное лечение

                                if g.daysTo(h) <= 14:
                                    eventTypeId = 62  # Амбулаторное лечение

                                elif g.daysTo(h) > 14:
                                    sotId = self.db.getRecordEx(
                                        self.tableStatusObservationClientType,
                                        ['id', 'name', 'code'],
                                        u"name = '{0}'".format(colPackagePrice))

                                    if sotId:
                                        code = forceString(sotId.value('code'))
                                        if code == u"САНКУР":
                                            eventTypeId = 55  # Санаторно-курортное лечение
                                        elif code == u"ОЗД":
                                            eventTypeId = 61  # Оздоровление
                                        else:
                                            str1 = u"Для тарифа {0} не удалось определить тип проживания гостя.".format(colPackagePrice)
                                            str2 = u'\n"Проверьте код тарифа в справочнике "Персонификация - Статус наблюдения пациента"'
                                            str3 = u"\nОжидаются значения САНКУР/ОЗД"
                                            self.error[colClientId] = [str1 + str2 + str3]

                                    else:
                                        sRecordStatusObservationClientType = self.tableStatusObservationClientType.newRecord()
                                        sRecordStatusObservationClientType.setValue('code', u"ОЗД")
                                        sRecordStatusObservationClientType.setValue('name', forceString(colPackagePrice))
                                        sRecordStatusObservationClientType.setValue('color', u'#66FF00')
                                        sRecordStatusObservationClientType.setValue('removeStatus', 1)
                                        self.db.insertRecord(self.tableStatusObservationClientType,
                                                                      sRecordStatusObservationClientType)

                                        eventTypeId = 61  # Оздоровление

                                sRecordEvent.setValue('eventType_id', eventTypeId)
                                orgId = QtGui.qApp.getCurrentOrgId()
                                sRecordEvent.setValue('org_id', orgId)
                                contractId = self.getContractId(orgId)
                                if contractId:
                                    sRecordEvent.setValue('contract_id', contractId)
                                sRecordEvent.setValue('setDate', toVariant(self.getDate(colDateCheckIn)))
                                sRecordEvent.setValue('isPrimary', 1)
                                sRecordEvent.setValue('client_id', clientId)
                                sRecordEvent.setValue('externalId', forceString(colEventId))
                                sRecordEvent.setValue('order', 1)
                                eId = self.db.insertRecord(self.tableEvent, sRecordEvent)

                                # Event_Voucher
                                sRecordEventVoucher = self.tableEventVoucher.newRecord()
                                sRecordEventVoucher.setValue('event_id', eId)
                                sRecordEventVoucher.setValue('begDate', toVariant(self.getDate(colDateCheckIn)))
                                sRecordEventVoucher.setValue('endDate', toVariant(self.getDate(colDateCheckOut)))
                                self.db.insertRecord(self.tableEventVoucher, sRecordEventVoucher)

                                # Поступление
                                sRecordAction = self.tableAction.newRecord()
                                actionTypeIdList = getActionTypeIdListByFlatCode(u'received%')
                                if actionTypeIdList:
                                    actionTypeId = actionTypeIdList[0]
                                else:
                                    actionTypeId = None
                                sRecordAction.setValue('actionType_id', actionTypeId)
                                sRecordAction.setValue('directionDate', toVariant(self.getDate(colDateCheckIn)))
                                sRecordAction.setValue('status', 2)
                                sRecordAction.setValue('begDate', toVariant(self.getDate(colDateCheckIn)))
                                sRecordAction.setValue('endDate', toVariant(self.getDate(colDateCheckIn)))
                                sRecordAction.setValue('event_id', eId)
                                actionType = CActionTypeCache.getById(actionTypeId)
                                newAction = CAction(actionType=actionType, record=sRecordAction)
                                initActionProperties(newAction)
                                newAction[u'Направлен в отделение'] = 3
                                newAction.save(idx=-1)

                                # Движение
                                sRecordAction = self.tableAction.newRecord()
                                actionTypeIdList = getActionTypeIdListByFlatCode(u'moving%')
                                if actionTypeIdList:
                                    actionTypeId = actionTypeIdList[0]
                                else:
                                    actionTypeId = None
                                sRecordAction.setValue('actionType_id', actionTypeId)
                                sRecordAction.setValue('directionDate', toVariant(self.getDateTime(colDateCheckIn, 1)))
                                sRecordAction.setValue('status', 0)
                                sRecordAction.setValue('begDate', toVariant(self.getDateTime(colDateCheckIn, 1)))
                                sRecordAction.setValue('event_id', eId)
                                actionType = CActionTypeCache.getById(actionTypeId)
                                newAction = CAction(actionType=actionType, record=sRecordAction)
                                initActionProperties(newAction)
                                newAction[u'Отделение пребывания'] = 3
                                ospId = self.db.getRecordEx(
                                    self.tableOrgStructurePlacement,
                                    ['id'],
                                    u"master_id = 3 and name = '{0}'".format(int(float(colRoomNumber))))
                                newAction[u'Помещение'] = forceInt(ospId.value('id'))
                                newAction.save(idx=-1)
                                self.db.commit()
                            except:
                                self.error[colClientId] = [
                                    u"Ошибка заполнения таблиц Event или Action"]
                                self.db.rollback()

                    else:
                        notData = []

                        if not colLastName:
                            notData.append(self.tableName['colLastName'])
                        if not colFirstName:
                            notData.append(self.tableName['colFirstName'])
                        if colStatusHouse:
                            notData.append(self.tableName['colStatusHouse'])
                        if not colEventId:
                            notData.append(self.tableName['colEventId'])
                        if not colClientId:
                            notData.append(self.tableName['colClientId'])
                        if not colDateCheckIn:
                            notData.append(self.tableName['colDateCheckIn'])
                        if not colDateCheckOut:
                            notData.append(self.tableName['colDateCheckOut'])
                        if not colRoomNumber:
                            notData.append(self.tableName['colRoomNumber'])
                        if not colTypeDul:
                            notData.append(self.tableName['colTypeDul'])
                        if not colSeriaNumberDul:
                            notData.append(self.tableName['colSeriaNumberDul'])
                        if not colBirthDate:
                            notData.append(self.tableName['colBirthDate'])
                        if not colDateDul:
                            notData.append(self.tableName['colDateDul'])
                        if not colStreet:
                            notData.append(self.tableName['colStreet'])
                        if not colCity:
                            notData.append(self.tableName['colCity'])
                        if not colCountrySubjectRF:
                            notData.append(self.tableName['colCountrySubjectRF'])
                        if not colHouse:
                            notData.append(self.tableName['colHouse'])

                            self.error[colClientId] = notData

                            self.noImport.append(colClientId)
                        else:
                            pass

                    self.progressBar.setValue(int((float(100) / float(self.maxstr)) * float(x)))

                    self.numberAddClients.setText(str(len(self.newClient)))
                    self.numberUpDateClients.setText(str(len(self.oldClient)))
                    self.numberNoAddClients.setText(str(len(self.noImport)))

            self.btnStart.setEnabled(True)
            self.btnImportCSV.setEnabled(True)

        view = CReportViewDialog(self)
        view.setText(self.build(self.allList, self.newClient, self.oldClient, self.noImport, self.error))
        view.exec_()


    def getSexClient(self, firstName, patrName):
        firstName = firstName.lower().title()
        patrName = patrName.lower().title()

        firstNameSex = forceInt(self.db.translate('rdFirstName', 'name', firstName, 'sex')) if firstName else 0
        patrNameSex = forceInt(self.db.translate('rdPatrName', 'name', patrName, 'sex')) if patrName else 0

        if firstNameSex and patrNameSex:
            if firstNameSex == patrNameSex:
                detectedSex = firstNameSex
            else:
                detectedSex = 0
        else:
            detectedSex = max(firstNameSex, patrNameSex)

        return detectedSex


    def hetSeriaNumber(self, seriaNumber):
        seria = None
        number = None
        seriaNumber = seriaNumber.replace(' ', '')

        if seriaNumber.isdigit():  # Если seriaNumber содержит только цифры
            if len(seriaNumber) == 10:
                seria = seriaNumber[:4]
                number = seriaNumber[-6:]
            elif len(seriaNumber) == 9:
                seria = "0" + str(seriaNumber[:3])
                number = seriaNumber[-6:]
        else:
            number = seriaNumber[-6:]
            seria = seriaNumber[:-6]

        if seria.isdigit():
            seria = seria[:2] + " " + seria[2:]

        return seria, number


    def getDate(self, colDateDul):
        colDateDul = str(colDateDul).split(' ')
        if '.' in colDateDul[0]:
            qtDate = QDate.fromString(colDateDul[0], 'dd.MM.yyyy')
        if '/' in colDateDul[0]:
            qtDate = QDate.fromString(colDateDul[0], 'dd/MM/yyyy')
        return toVariant(qtDate.toString('yyyy-MM-dd'))


    def getColCityBirth(self, colCityBirth):
        colCityBirth = colCityBirth.lower().title()
        if colCityBirth[-1] == u' ':
            colCityBirth = colCityBirth[:-1]
        elif colCityBirth[-1] == u',':
            colCityBirth = colCityBirth[:-1]

        return colCityBirth


    def getDateTime(self, dateString, plusTime=None):
        timeDate = datetime.strptime(dateString, '%d.%m.%Y')
        newDateTime = timeDate + timedelta(minutes=plusTime)
        formattedDateTime = newDateTime.strftime('%Y-%m-%d %H:%M:%S')
        return toVariant(formattedDateTime)


    def getContractId(self, orgId=None):
        db = QtGui.qApp.db
        tableContract = db.table('Contract')
        tableFinance = db.table('rbFinance')
        filter = [tableContract['deleted'].eq(0)]
        id = u''

        financeId = u''
        eventTypeId = 55
        strictEventType = False

        if orgId:
            filter.append(tableContract['recipient_id'].eq(orgId))
        if financeId:
            filter.append(tableContract['finance_id'].eq(financeId))
        if eventTypeId:
            tableContractSpecification = db.table('Contract_Specification')
            condInContract = db.joinAnd([tableContractSpecification['master_id'].eq(tableContract['id']),
                                         tableContractSpecification['deleted'].eq(0)])
            if strictEventType:
                filterEventType = [condInContract, tableContractSpecification['eventType_id'].eq(eventTypeId)]
                condEventType = db.existsStmt(tableContractSpecification, filterEventType)
            else:
                filterEventType = [condInContract, tableContractSpecification['eventType_id'].isNotNull()]
                condEventType = 'NOT ' + db.existsStmt(tableContractSpecification, filterEventType)
            filter.append(condEventType)
            financeId = getEventFinanceId(eventTypeId)
            if financeId:
                filter.append(tableContract['finance_id'].eq(financeId))

        stmt = db.selectStmt(tableContract.leftJoin(tableFinance, tableFinance['id'].eq(tableContract['finance_id'])),
                             [tableContract['id']],
                             filter,
                             [tableContract['number'].name(), tableFinance['code'].name() + ' DESC',
                              tableContract['date'].name(), tableContract['resolution'].name()]
                             )

        query = db.query(stmt)
        while query.next():
            record = query.record()
            id = record.value('id').toInt()[0]

        return id


    def build(self, allList, newClient, oldClient, noImport, error):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Отчет по импорту')
        cursor.insertBlock()
        cursor.insertBlock()

        tableColumns = [
            ('3%', [u'№'], CReportBase.AlignLeft),
            ('10%', [u'Идентификатор гостя'], CReportBase.AlignLeft),
            ('15%', [u'Фамилия'], CReportBase.AlignLeft),
            ('15%', [u'Имя'], CReportBase.AlignLeft),
            ('15%', [u'Отчество'], CReportBase.AlignLeft),
            ('42%', [u'Причина'], CReportBase.AlignLeft)
        ]

        table = createTable(cursor, tableColumns)

        if newClient:
            iRow = 0
            row = table.addRow()
            table.setText(row, 1, forceString(u'Новые записи'))

            for i in newClient:
                row = table.addRow()
                iRow = iRow + 1
                table.setText(row, 0, forceString(iRow))
                table.setText(row, 1, forceString(i))
                table.setText(row, 2, forceString(allList[i][0]))
                table.setText(row, 3, forceString(allList[i][1]))
                table.setText(row, 4, forceString(allList[i][2]))
                if i in error:
                    table.setText(row, 5, forceString("\n".join(error[i])))

            row = table.addRow()
            for i in range(5):
                table.setText(row, i, forceString(u'   '))

        if oldClient:
            iRow = 0
            row = table.addRow()
            table.setText(row, 1, forceString(u'Уже имеется записей'))

            for i in oldClient:
                row = table.addRow()
                iRow = iRow + 1
                table.setText(row, 0, forceString(iRow))
                table.setText(row, 1, forceString(i))
                table.setText(row, 2, forceString(allList[i][0]))
                table.setText(row, 3, forceString(allList[i][1]))
                table.setText(row, 4, forceString(allList[i][2]))

            row = table.addRow()
            for i in range(5):
                table.setText(row, i, forceString(u'   '))

        if noImport:
            iRow = 0
            row = table.addRow()
            table.setText(row, 1, forceString(u'Не добавленные записи'))

            for i in noImport:
                row = table.addRow()
                iRow = iRow + 1
                table.setText(row, 0, forceString(iRow))
                table.setText(row, 1, forceString(i))
                table.setText(row, 2, forceString(allList[i][0]))
                table.setText(row, 3, forceString(allList[i][1]))
                table.setText(row, 4, forceString(allList[i][2]))
                if i in error:
                    table.setText(row, 5, forceString("\n".join(error[i])))

            row = table.addRow()
            for i in range(5):
                table.setText(row, i, forceString(u'   '))

        return doc
