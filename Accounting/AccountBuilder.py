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

u"""Утилиты формирования счёта"""
import json

from collections                     import namedtuple

from PyQt4                           import QtGui
from PyQt4.QtCore                    import QDate, QVariant

from library.AgeSelector             import checkAgeSelector
from library.Calendar import wpFiveDays, wpSixDays, wpSevenDays, countWorkDays
from library.Identification import getIdentification
from library.database                import CTableRecordCache
from library.Utils                   import ( smartDict,
                                              calcAgeInYears,
                                              calcAgeTuple,
                                              firstMonthDay,
                                              firstYearDay,
                                              forceBool,
                                              forceDate,
                                              forceDateTime,
                                              forceDouble,
                                              forceInt,
                                              forceRef,
                                              forceString,
                                              lastMonthDay,
                                              lastYearDay,
                                              toVariant,
                                            )

from Accounting.Tariff               import CTariff
from Accounting.Utils import (CCoefficientTypeDescr,
                              getNextAccountNumber,
                              getRefuseTypeId,
                              setActionPayStatus,
                              setEventPayStatus,
                              setEventVisitsPayStatus,
                              setVisitPayStatus,
                              setEventCsgPayStatus,
                              unpackExposeDiscipline,
                              updateDocsPayStatus,
                              roundMath,
                              getWeekProfile,
                              isInterruptedCase,
                              hasCancerHemaBloodProfile,
                              isGerontologicalKPK,
                              hasSevereMKB,
                              hasServiceInEvent
                              )

from Events.ActionServiceType        import CActionServiceType
from Events.ActionStatus             import CActionStatus
from Events.MapActionTypeToServiceIdList import CMapActionTypeIdToServiceIdList
from Events.Utils                    import ( CPayStatus,
                                              CFinanceType,
                                              getEventDuration,
                                              getEventServiceId,
                                              getEventAidTypeRegionalCode,
                                              getEventDiagnosis
                                            )

__all__ = [ 'CAccountDetails',
            'CAccountPool',
            'CAccountBuilder',
            'getEventVisitsCircumstances',
            'getEventActionsCircumstances',
            'filterUniqueCircumstances',
            'getVisitsFromEventWithSameSevrice',
            'getMesAmount',
            'evalPriceForKrasnodarA13',
            'evalPriceForMurmansk2015Hospital',
          ]


class CAccountDetails:
    def __init__(self, contractDescr, orgId, orgStructureId, settleDate, reexpose, payerId=None):
        self.contractDescr = contractDescr
        self.orgId = orgId
        self.orgStructureId = orgStructureId
        self.settleDate = settleDate
        self.reexpose = reexpose
        self.payerId = payerId
        self.id, self.record = self.createAccountRecord()
        self.totalAmount = 0
        self.totalUet = 0
        self.totalSum = 0


    def createAccountRecord(self):
        db = QtGui.qApp.db
        table = db.table('Account')
        record = table.newRecord()
        record.setValue('contract_id', toVariant(self.contractDescr.id))
        record.setValue('orgStructure_id', toVariant(self.orgStructureId))
        record.setValue('format_id', toVariant(self.contractDescr.formatId))
        record.setValue('payer_id', toVariant(self.payerId))
        record.setValue('settleDate', toVariant(self.settleDate))
        if QtGui.qApp.defaultKLADR()[:2] == u'23' and self.contractDescr.financeType == CFinanceType.CMI:
            date = lastMonthDay(self.settleDate)
        else:
            date = QDate().currentDate()
        record.setValue('date', toVariant(date))
        accountId = db.insertRecord(table,  record)
        record.setValue('id',              accountId)
        return accountId, record


    def update(self, settleDate, number, note=None, payerId=None, accountTypeId=None, groupAccountType=None):
        record = self.record
        record.setValue('settleDate', settleDate)
        record.setValue('number',     number)
        record.setValue('amount',     self.totalAmount)
        record.setValue('uet',        self.totalUet)
        record.setValue('sum',        self.totalSum)
        record.setValue('note',        toVariant(note))
        if payerId:
            record.setValue('payer_id', toVariant(payerId))
        if accountTypeId:
            record.setValue('type_id', toVariant(accountTypeId))
        if groupAccountType:
            record.setValue('group_id', toVariant(groupAccountType))
        QtGui.qApp.db.updateRecord('Account', record)


class CAccountPool:
    # порядок полей важен для упрощения сортировки
    CKey = namedtuple('CKey',
                         (
                           'date',
                           'payerId',
                           'insurer',
                           'sourceOrg',
                           'accountTypeId',
                           'groupAccountType',
                           'batch',
                           'client',
                           'event',
                           'oncology',
                           'bookkeeperId'
                         )
                     )


    def __init__(self, contractDescr, orgId, orgStructureId, settleDate, reexposeInSeparateAccount, mapOrgStructToBookkeeper):
        self.contractDescr = contractDescr
        self.orgId = orgId
        self.orgStructureId = orgStructureId
        self.settleDate = settleDate
        self.reexposeInSeparateAccount = reexposeInSeparateAccount
        self.mapOrgStructToBookkeeper = mapOrgStructToBookkeeper
        self.mapKeyExToDetails = {}
        self.mapEventIdToExternalIdAndSeqNumber = {}
        self.mapInsurerIdToKey = {}
        self.mapInsurerIdToPayerId = {}
        self.mapEventIdToDispanser = {}
        self.mapEventIdHasObr = {}
        if QtGui.qApp.defaultKLADR()[:2] == '23':
            self.mapGroupAccountTypeToAccountType = {
                (1, 0): '2', (1, 1): '4', (1, 2): '5',
                (2, 0): 'i', (2, 1): 'k', (2, 2): 'l',
                (3, 0): '2', (3, 1): '4', (3, 2): '5',
                (4, 0): 'm', (4, 1): 'o', (4, 2): 'p',
                (5, 0): 'a', (5, 1): 'c', (5, 2): 'd',  # старые типы реестров по дисп
                (6, 0): 'e', (6, 1): 'g', (6, 2): 'h',  # медосмотры несовершеннолетних
                (7, 0): '2', (7, 1): '4', (7, 2): '5',
                (8, 0): '2', (8, 1): '4', (8, 2): '5',
                (9, 0): 'q', (9, 1): 's', (9, 2): 't',
                (10, 0): 'q', (10, 1): 's', (10, 2): 't',
                (11, 0): 'a1', (11, 1): 'c1', (11, 2): 'd1',  # первый этап дисп
                (12, 0): 'a2', (12, 1): 'c2', (12, 2): 'd2',  # второй этап дисп
                (13, 0): 'a3', (13, 1): 'c3', (13, 2): 'd3',  # профосмотры взрослых
                (14, 0): 'o', (14, 1): 'o', (14, 2): 'p',  # ДН
                (15, 0): 'o', (15, 1): 'o', (15, 2): 'p',  # разовые посещения по подушевому
                (16, 0): 'ak', (16, 1): 'ck', (16, 2): 'dk',  # по компьютерной томографии
                (17, 0): 'am', (17, 1): 'cm', (17, 2): 'dm',  # по магнитно-резонансной томографии
                (18, 0): 'au', (18, 1): 'cu', (18, 2): 'du',  # по ультразвуковому исследованию ССС
                (19, 0): 'ae', (19, 1): 'ce', (19, 2): 'de',  # по эндоскопическим диаг. исследованиям
                (20, 0): 'ag', (20, 1): 'cg', (20, 2): 'dg',  # по мол.-ген. иссл. с целью выявления онк. заб.
                (21, 0): 'ah', (21, 1): 'ch', (21, 2): 'dh',  # по гист. исследованиям с целью выявления онк. заб.
                (22, 0): 'ao', (22, 1): 'co', (22, 2): 'do',  # по экстракорпоральному оплодотворению
                (23, 0): 'av', (23, 1): 'cv', (23, 2): 'dv',  # по коронавирусу
                (24, 0): '4', (24, 1): '4', (24, 2): '5',  # ДН по полному подушевому
                (25, 0): '4', (25, 1): '4', (25, 2): '5',  # разовые посещения по полному подушевому
                (26, 0): 'a4', (26, 1): 'c4', (26, 2): 'd4',  # по углуб. дисп. взр.нас. I этап
                (27, 0): 'a5', (27, 1): 'c5', (27, 2): 'd5',  # по углуб. дисп. взр.нас. II этап
                (28, 0): 'e', (28, 1): 'g', (28, 2): 'h',  # Диспансеризация детей-сирот
                (29, 0): 'e', (29, 1): 'g', (29, 2): 'h',  # диспансеризация детей остав-ся без попечения родит
                (30, 0): 'ap', (30, 1): 'cp', (30, 2): 'dp',  # по патологоанатомическим вскрытиям
                (31, 0): 'a6', (31, 1): 'c6', (31, 2): 'd6',  # дисп. для оценки репрод. здоровья I этап
                (32, 0): 'a7', (32, 1): 'c7', (32, 2): 'd7',  # дисп. для оценки репрод. здоровья II этап
                (33, 0): 'ad', (33, 1): 'cd', (33, 2): 'dd'  # по диспансерному наблюдению на рабочих местах
            }
        elif QtGui.qApp.defaultKLADR()[:2] == '01':
            self.mapGroupAccountTypeToAccountType = {
                (1, 0): 'HM', (1, 1): 'HM', (1, 2): 'HM',
                (2, 0): 'HC', (2, 1): 'HC', (2, 2): 'HC',
                (3, 0): 'AM', (3, 1): 'AM', (3, 2): 'AM',
                (4, 0): 'AC', (4, 1): 'AC', (4, 2): 'AC'
            }
        else:
            self.mapGroupAccountTypeToAccountType = {}
        self.mapAccountType = {}
        self.baseAccountNumber = None
        self.mapPayerIdToInfisCode = {}
        self.mapClientPolicyForDate = {}
        self.mapAccountTypeIdByRegionalCode = {}

        (
          self.exposeBySourceOrg,
          self.exposeByOncology,
          self.exposeByBatch,
          self.exposeByEvent,
          self.exposeByMonth,
          self.exposeByClient,
          self.exposeByInsurer
        )                     = unpackExposeDiscipline(self.contractDescr.exposeDiscipline)

        if self.contractDescr.financeType == CFinanceType.cash and self.exposeByEvent:
            self.getTransformedEventId = self._getExternalIdAndSeqNumber
            self.getAccountNumber      = self._getAccountNumberWithoutBaseNumber
        else:
            self.getTransformedEventId = self._getEventIdAsIs
            self.getAccountNumber      = self._getTrivialAccountNumber

        if self.exposeByMonth:
            self.getSettleDate = self._getLastMonthDayAsSettleDate
        else:
            self.getSettleDate = self._getTrivialSettleDate
        self._mapOrgIdToShortName = {}
            
    def getAccountTypeId(self, groupAccountType, orgStructureId, payerId, execDate, reexpose):
        db = QtGui.qApp.db
        accountTypeId = self.mapAccountType.get((groupAccountType, orgStructureId, payerId, execDate, reexpose))
        if accountTypeId is None:
            if reexpose:
                isAdditional = 2
            else:
                tableAccount = db.table('Account')
                cond = [tableAccount['deleted'].eq(0),
                        tableAccount['payer_id'].eq(payerId),
                        tableAccount['group_id'].eq(groupAccountType),
                        tableAccount['contract_id'].eq(self.contractDescr.id),
                        tableAccount['settleDate'].dateBetween(firstMonthDay(execDate), lastMonthDay(execDate)),
                        ]
                if orgStructureId:
                    cond.append(tableAccount['orgStructure_id'].eq(orgStructureId))
                else:
                    cond.append(tableAccount['orgStructure_id'].isNull())
                cnt = db.getDistinctCount(tableAccount,
                                          tableAccount['id'].name(),
                                          cond
                                          )
                isAdditional = 1 if cnt > 0 else 0
            accountTypeCode = self.mapGroupAccountTypeToAccountType.get((groupAccountType, isAdditional))
            accountTypeId = self.mapAccountTypeIdByRegionalCode.get(accountTypeCode, None)
            if not accountTypeId:
                accountTypeId = forceRef(QtGui.qApp.db.translate('rbAccountType', 'regionalCode', accountTypeCode, 'id'))
                self.mapAccountTypeIdByRegionalCode[accountTypeCode] = accountTypeId
            self.mapAccountType[(groupAccountType, orgStructureId, payerId, execDate, reexpose)] = accountTypeId
        return accountTypeId
        
        
    def getPayerInfisCode(self, payerId):
        if payerId:
            payerInfisCode = self.mapPayerIdToInfisCode.get(payerId)
            if payerInfisCode is None:
                payerInfisCode = forceString(QtGui.qApp.db.translate('Organisation', 'id', payerId, 'infisCode'))
                if not payerInfisCode:
                    payerInfisCode = '{%d}' % payerId
                self.mapPayerIdToInfisCode[payerId] = payerInfisCode
        else:
            payerInfisCode = u'без полиса'
        return payerInfisCode


    def getBaseAccountNumber(self):
        if self.baseAccountNumber is None or self.contractDescr.counterId:
            self.baseAccountNumber = getNextAccountNumber(self.contractDescr.number, self.contractDescr.counterId)
        return self.baseAccountNumber


    def createAccount(self, reexpose, payerId=None, bookkeeperId=None):
        return CAccountDetails(self.contractDescr, self.orgId, bookkeeperId if bookkeeperId else self.orgStructureId, self.settleDate, reexpose, payerId)


    def _getAccount(self, key, reexpose):
        reexpose = bool(self.reexposeInSeparateAccount and reexpose)
        result = self.mapKeyExToDetails.get((key, reexpose), None)
        if result is None:
            result = self.createAccount(reexpose, key.payerId, key.bookkeeperId)
            self.mapKeyExToDetails[(key, reexpose)] = result
        return result


    def _getEventIdAsIs(self, eventId):
        return eventId


    # это для случая if self.contractDescr.financeType == CFinanceType.cash and self.exposeByEvent:
    def _getExternalIdAndSeqNumber(self, eventId):
        if not eventId:
            return None

        # кеширование приводит к тому, что мы не видим новые счета,
        # таким образом происходит группировка услуг одного события в один счёт
        result = self.mapEventIdToExternalIdAndSeqNumber.get(eventId, None)
        if result is None:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            result = forceString(db.translate(tableEvent, tableEvent['id'], eventId, tableEvent['externalId']))
            if not result:
                result = '{%d}' % eventId

            tableAccount     = db.table('Account')
            tableAccountItem = db.table('Account_Item')
            cnt = db.getDistinctCount(tableAccountItem.innerJoin(tableAccount,
                                                                 tableAccount['id'].eq(tableAccountItem['master_id'])
                                                                ),
                                      tableAccount['id'].name(),
                                      [ tableAccountItem['deleted'].eq(0),
                                        tableAccountItem['event_id'].eq(eventId),
                                        tableAccount['deleted'].eq(0),
                                        tableAccount['contract_id'].eq(self.contractDescr.id),
#                                        tableAccount['settleDate'].eq(self.settleDate),
                                      ]
                                     )
            result += '/%d' % (cnt + 1)
            self.mapEventIdToExternalIdAndSeqNumber[eventId] = result
        return result

        
    def getPayer(self, clientId, date, eventId=None):
        from Registry.Utils import getClientCompulsoryPolicy, getClientVoluntaryPolicy

        def getPayerId(insurerId):
            result = self.mapInsurerIdToPayerId.get(insurerId, None)
            if result is None:
                if insurerId:
                    tmpInsurerId = insurerId
                    db = QtGui.qApp.db
                    table = db.table('Organisation')
                    if self.exposeByInsurer == 1:
                        if forceString(db.translate(table, 'id', tmpInsurerId, 'area'))[:2] == QtGui.qApp.defaultKLADR()[:2]:
                            while True:
                                headId = forceRef(db.translate(table, 'id', tmpInsurerId, 'head_id'))
                                if headId:
                                    tmpInsurerId = headId
                                else:
                                    break
                        else:
                            tmpInsurerId = self.contractDescr.payerId
                    result = tmpInsurerId
                self.mapInsurerIdToPayerId[insurerId] = result
            return result

        if clientId:
            if self.contractDescr.financeType == CFinanceType.VMI:
                record = getClientVoluntaryPolicy(clientId)
            else:
                if QtGui.qApp.defaultKLADR()[:2] == u'23':
                    record = self.mapClientPolicyForDate.get((clientId, date, eventId), None)
                    if record is None:
                        record = getClientCompulsoryPolicy(clientId, date, eventId)
                        self.mapClientPolicyForDate[(clientId, date, eventId)] = record
                else:
                    record = getClientCompulsoryPolicy(clientId)
            if record:
                insurerId = forceRef(record.value('insurer_id'))
                insurerArea = forceString(record.value('area'))
                return getPayerId(insurerId), insurerArea
        return None, None


    def getOncologySign(self, eventId):
        db = QtGui.qApp.db
        tableDiagnostic    = db.table('Diagnostic')
        tableDiagnosis     = db.table('Diagnosis')
        tableDiagnosisType = db.table('rbDiagnosisType')
        tableDiseasePhases = db.table('rbDiseasePhases')
        table = tableDiagnostic
        table = table.innerJoin(tableDiagnosis,
                                tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id'])
                                )
        table = table.innerJoin(tableDiagnosisType,
                                tableDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id'])
                                )
        table = table.leftJoin( tableDiseasePhases,
                                tableDiseasePhases['id'].eq(tableDiagnostic['phase_id'])
                              )

        cnt = db.getCount(table,
                          '1',
                          db.joinAnd([tableDiagnostic['event_id'].eq(eventId),
                                      tableDiagnostic['deleted'].eq(0),
                                      db.joinOr([ db.joinAnd([ db.joinOr([ tableDiagnosis['MKB'].like('C%'),
                                                                           tableDiagnosis['MKB'].like('D0%'),
                                                                           tableDiagnosis['MKB'].between('D45', 'D47.9'),
                                                                         ]
                                                                        ),
                                                               tableDiagnosisType['code'].inlist([ '1',  # заключительный
                                                                                                   '2',  # основной
#                                                                                                   '9',  # сопутствующий
                                                                                                 ]
                                                                                                ),
                                                             ]
                                                            ),
                                                  db.joinAnd([ db.joinOr([ tableDiagnosis['MKB'].like('C%'),
                                                                           tableDiagnosis['MKB'].like('D0%'),
                                                                         ]
                                                                        ),
                                                               tableDiagnosisType['code'].inlist([ '1',  # заключительный
                                                                                                   '2',  # основной
                                                                                                   '9',  # сопутствующий
                                                                                                   '7',  # Основной предварительный диагноз
                                                                                                   '11', # Сопутствующий предварительный диагноз
                                                                                                   '10', # предв.соп. (?!)
                                                                                                 ]
                                                                                                ),
                                                               tableDiseasePhases['code'].eq('10'),

                                                             ]
                                                            ),
                                                  tableDiagnosis['MKB'].eq('Z03.1'),
                                                ]
                                               )
                                     ]
                                    )
                         )

        if cnt:
            result = u'ОНКО'
        else:
            result = ''
        return result


    def getShortNameOfSourceOrg(self, eventId):
        db = QtGui.qApp.db
        sourceOrgId = forceRef(db.translate('Event', 'id', eventId, 'relegateOrg_id'))
        if sourceOrgId:
            return self._getShortNameOfHeadOrg(sourceOrgId)
        else:
            return ''


    def _getShortNameOfHeadOrg(self, orgId):
        db = QtGui.qApp.db

        if orgId in self._mapOrgIdToShortName:
            return self._mapOrgIdToShortName[orgId]

        headOrgId = orgId
        path = [orgId]
        while True:
            tmpOrgId = forceRef(db.translate('Organisation', 'id', headOrgId, 'head_id'))
            if tmpOrgId:
                headOrgId = tmpOrgId
                if headOrgId in path: # loop detected
                    headOrgId = orgId
                    break
                else:
                    path.append(headOrgId)
            else:
                break

        shortName = forceString(db.translate('Organisation', 'id', headOrgId, 'shortName'))
        self._mapOrgIdToShortName[orgId] = shortName
        return shortName


    def _getTrivialSettleDate(self, key):
        return self.settleDate


    def _getLastMonthDayAsSettleDate(self, key):
        return min(self.settleDate, lastMonthDay(QDate(key.date)))


    def isDispanserEvent(self, eventId):
        isDispanser = self.mapEventIdToDispanser.get(eventId)
        if isDispanser is None:
            db = QtGui.qApp.db
            isDispanser = db.getCount(
                u"""Action a 
                left join ActionType at on at.id = a.actionType_id 
                left join rbService s on s.id = at.nomenclativeService_id
                left join Event e on e.id = a.event_id
                left join EventType et on et.id = e.eventType_id
                left join rbMedicalAidType mat on mat.id = et.medicalAidType_id
                left join soc_dispanserServices sds on sds.code = s.infis and sds.begDate <= a.endDate and (sds.endDate >= a.endDate or sds.endDate is null)""",
                u'a.id',
                u"a.event_id = {0} and a.deleted = 0 and mat.regionalCode = '271' and sds.id is not null".format(eventId))
            self.mapEventIdToDispanser[eventId] = isDispanser
        return isDispanser


    def isEventHasObr(self, eventId):
        hasObr = self.mapEventIdHasObr.get(eventId)
        if hasObr is None:
            db = QtGui.qApp.db
            hasObr = db.getCount(
                u"""Action a 
                left join ActionType at on at.id = a.actionType_id 
                left join rbService s on s.id = at.nomenclativeService_id
                left join soc_obr so on s.infis in (so.kusl, so.kusl2) and so.begDate <= a.endDate and (so.endDate >= a.endDate or so.endDate is null)""",
                u'a.id',
                u"a.event_id = {0} and a.deleted = 0 and so.kusl is not null".format(eventId))
            self.mapEventIdHasObr[eventId] = hasObr
        return hasObr


    def getKey(self, clientId, date, eventId, groupAccountType, batch, reexpose, personOrgStructId):
        # policyDate = date
        execDate = date
        # if QtGui.qApp.defaultKLADR()[:2] == u'23':
        #      if eventId:
        #         record = QtGui.qApp.db.getRecord('Event', 'setDate, execDate', eventId)
        #         policyDate = forceDate(record.value('setDate'))
        #         execDate = forceDate(record.value('execDate'))
                
        (payerId, insurerArea) = self.getPayer(clientId, None if groupAccountType == 30 else execDate, eventId) if self.exposeByInsurer else (self.contractDescr.payerId, '00')

        if QtGui.qApp.defaultKLADR()[:2] == u'23':

            # а с 01.05.2020 полное подушевое финансирование
            if groupAccountType == 4 and self.settleDate >= QDate(2020, 5, 1):
                # Диспансерные приемы по краевым формируем в отдельные реестры
                if insurerArea is not None and insurerArea[:2] == QtGui.qApp.defaultKLADR()[:2] and self.isDispanserEvent(eventId):
                    groupAccountType = 24
                # разовые посещения формируем в отдельные реестры, если включена настройка
                elif QtGui.qApp.checkGlobalPreference(u'23:accSingleVisitsCapita', u'да') and not self.isEventHasObr(eventId):
                    groupAccountType = 25
                else:
                    groupAccountType = 3

            # инокраевых из прикрепления отправляем в ОМС c 01.09.2017
            if groupAccountType == 4 and execDate >= QDate(2017, 9, 1) and insurerArea is not None and insurerArea[:2] != QtGui.qApp.defaultKLADR()[:2]:
                groupAccountType = 3

            # Диспансерные приемы по краевым формируем в отдельные реестры
            if groupAccountType == 4 and self.isDispanserEvent(eventId):
                groupAccountType = 14
            # разовые посещения формируем в отдельные реестры, если включена настройка
            elif QtGui.qApp.checkGlobalPreference(u'23:accSingleVisitsCapita', u'да') and groupAccountType == 4 and not self.isEventHasObr(eventId):
                groupAccountType = 15

        accountTypeId = self.getAccountTypeId(groupAccountType, self.orgStructureId, payerId, execDate, reexpose) if self.contractDescr.exposeByAccountType else None
        
        bookkeeperId = self.mapOrgStructToBookkeeper.get(personOrgStructId) if personOrgStructId else None

        accountTypeId = self.getAccountTypeId(groupAccountType, bookkeeperId if bookkeeperId else self.orgStructureId, payerId, execDate, reexpose) if self.contractDescr.exposeByAccountType else None
        
        key = CAccountPool.CKey(
                date = firstMonthDay(date).toPyDate() if self.exposeByMonth else None,
                payerId = payerId,
                insurer = self.getPayerInfisCode(payerId) if self.exposeByInsurer else None,
                accountTypeId = accountTypeId,
                groupAccountType = groupAccountType,
                sourceOrg = self.getShortNameOfSourceOrg(eventId)  if self.exposeBySourceOrg else None,
                batch = batch if self.exposeByBatch else None,
                client = clientId if self.exposeByClient else None,
                event = self.getTransformedEventId(eventId) if self.exposeByEvent else None,
                oncology  = self.getOncologySign(eventId)          if self.exposeByOncology  else None,
                bookkeeperId = bookkeeperId
              )
        return key


    def getAccount(self, clientId, date, eventId, groupAccountType, batch, reexpose=False, personOrgStructId=None):
        return self._getAccount(self.getKey(clientId, date, eventId, groupAccountType, batch, reexpose, personOrgStructId), reexpose)


    def addAccountIfEmpty(self, reexpose=False):
        if not self.mapKeyExToDetails:
            self.getAccount(None, self.settleDate, None, '', False)
            if reexpose and self.reexposeInSeparateAccount:
                self.getAccount(None, self.settleDate, None, '', True)


    def getDetailsList(self):
        return [ details for key, details in sorted(self.mapKeyExToDetails.iteritems()) ]


    def getAccountIdList(self):
        return [details.id for details in self.getDetailsList()]


    def updateDetails(self):
        for (key, reexpose), details in sorted(self.mapKeyExToDetails.iteritems()):
            number, note = self.getAccountNumber(key, reexpose)
            details.update(self.getSettleDate(key), number, note, key.payerId, key.accountTypeId, key.groupAccountType)


    def _getTrivialAccountNumber(self, key, reexpose):
        return self.formatNumber(self.getBaseAccountNumber(), key, reexpose)


    def _getAccountNumberWithoutBaseNumber(self, key, reexpose):
        if any(key):
            return self.formatNumber('', key, reexpose)
        else:
            return self._getTrivialAccountNumber(key, reexpose)


    def formatNumber(self, baseAccountNumber, key, reexpose):
        if self.contractDescr.counterId:
            return baseAccountNumber, None

        parts = []
        if baseAccountNumber:
            parts.append(baseAccountNumber)
        if self.exposeByInsurer and key.insurer:
            parts.append(unicode(key.insurer))
        elif self.exposeByInsurer and QtGui.qApp.defaultKLADR().startswith('23'):
            parts.append(u'9007')
        if self.exposeBySourceOrg and key.sourceOrg:
            parts.append(key.sourceOrg)
        if self.exposeByBatch and key.batch:
            parts.append(unicode(key.batch))
        if self.exposeByClient and key.client:
            parts.append(unicode(key.client))
        if self.exposeByEvent and key.event:
            parts.append(unicode(key.event))
        if self.exposeByOncology and key.oncology:
            parts.append(key.oncology)
        if reexpose:
            parts.append(u'П')
        return '/'.join(parts), None


class CAccountBuilder(CMapActionTypeIdToServiceIdList):
    def __init__(self):
        CMapActionTypeIdToServiceIdList.__init__(self)
        self.mapMesIdToDescr = {}
        self.mapServiceIdToInfis = {}
        self.mapCsgCodeToDescr = {}
        self.mapEventIdToMKB = {}
        self.mapOrgIdToInfis = {}
        self.semifinishedMesRefuseTypeId = None
        self.reexposeEventIdDict = {}
        self.mapEventIdToDispCompleted = {}
        self.mapEventIdToProfCompleted = {}
        self.mapEventIdToTwoYearsDisp = {}
        self.mapEventIdToOncology = {}
        self.mapEventTypeIdToGroupAccountType = {}
        self.mapEventObr = {}
        self.mapEventHasReab = {}
        self.mapEventTypeIdToWeekProfileCode = {}
        self.mapBaseTariff = {}
        self.mapEventHasObr = {}
        self.mapOrgStructureIdToKODLPU = {}

        self.clientRecordCache = CTableRecordCache(QtGui.qApp.db, 'Client', ('sex', 'birthDate'))
        self.mapEventTypeToTFOMSAccIdent = {}
        if QtGui.qApp.defaultKLADR()[:2] == '23':
            self.mapSpr13ToGroupAccountType = {'11': 1, '12': 1, '301': 1, '302': 1,
            '401': 2, '402': 2,
            '241': 3, '242': 3, '201': 3, '202': 3, '21': 3, '22': 3, '31': 3, '32': 3, '60': 3, '111': 3, '112': 3, '01': 3, '02': 3, '281': 3, '282': 3,
            '271': 4, '272': 4,
            '261': 5, '211': 5, '233': 5, '244': 5,
            '262': 6, '252': 6, '232': 6,
            '43': 7, '41': 7, '42': 7, '51': 7, '52': 7, '71': 7, '72': 7, '90': 7, '411': 7, '422': 7, '511': 7, '522': 7,
            '801': 8, '802': 8
            }
        elif QtGui.qApp.defaultKLADR()[:2] == '01':
            self.mapSpr13ToGroupAccountType = {'1': 1, '6': 3}
        else:
            self.mapSpr13ToGroupAccountType = {}
        db = QtGui.qApp.db
        stmt = "select DISTINCT bookkeeperCode from OrgStructure where LENGTH(TRIM(bookkeeperCode)) = 5"
        query = db.query(stmt)
        self.omsCodes = []
        while query.next():
            record = query.record()
            self.omsCodes.append(forceString(record.value('bookkeeperCode')))

        self.ObrServiceIdList = db.getIdList('rbService', 'id', where=u"rbService.name like 'Обращен%'")
        self.complexVisitList = ['B04.026.001.001', 'B04.026.001.002', 'B04.026.001.005', 'B04.026.001.006',
                                 'B04.026.001.009', 'B04.026.001.010', 'B04.026.001.027', 'B04.026.001.028',
                                 'B04.026.001.054', 'B04.026.001.063', 'B04.026.001.064', 'B04.026.001.066',
                                 'B04.026.001.067', 'B04.026.001.068', 'B04.026.001.069', 'B04.026.001.070',
                                 'B04.026.001.071', 'B04.026.001.072', 'B04.026.001.073', 'B04.026.001.074',
                                 'B04.026.001.075', 'B04.026.001.076', 'B04.026.001.077', 'B04.026.001.078',
                                 'B04.026.001.079', 'B04.026.001.086', 'B04.026.001.087', 'B04.026.001.088',
                                 'B04.026.001.089', 'B04.026.001.090', 'B04.026.001.091', 'B04.026.002.013',
                                 'B04.026.002.014', 'B04.026.002.015', 'B04.026.002.016', 'B04.026.002.017',
                                 'B04.026.002.018', 'B04.026.002.019', 'B04.026.002.020', 'B04.026.002.020',
                                 'B04.026.002.021', 'B04.026.002.022', 'B04.047.001.001', 'B04.047.001.002',
                                 'B04.047.001.005', 'B04.047.001.006', 'B04.047.001.009', 'B04.047.001.010',
                                 'B04.047.001.019', 'B04.047.001.020', 'B04.047.001.027', 'B04.047.001.028',
                                 'B04.047.001.062', 'B04.047.001.063', 'B04.047.001.065', 'B04.047.001.066',
                                 'B04.047.001.067', 'B04.047.001.068', 'B04.047.001.069', 'B04.047.001.070',
                                 'B04.047.001.071', 'B04.047.001.072', 'B04.047.001.073', 'B04.047.001.074',
                                 'B04.047.001.075', 'B04.047.001.076', 'B04.047.001.077', 'B04.047.001.078',
                                 'B04.047.001.085', 'B04.047.001.086', 'B04.047.001.087', 'B04.047.001.088',
                                 'B04.047.001.089', 'B04.047.001.090', 'B04.047.002.013', 'B04.047.002.014',
                                 'B04.047.002.015', 'B04.047.002.016', 'B04.047.002.017', 'B04.047.002.018',
                                 'B04.047.002.019', 'B04.047.002.020', 'B04.047.002.021', 'B04.047.002.022',
                                 'A03.16.001',      'A03.18.001.012',  'A03.19.002',      'A04.12.005.003',
                                 'A06.09.007',      'A06.09.007.002',  'A12.09.001',      'A12.09.001.001',
                                 'B04.001.001.018', 'B04.018.001.030', 'B04.018.001.031', 'B04.023.001.041',
                                 'B04.028.001.003', 'B04.029.001.029', 'B04.053.001.016', 'B04.070.003',
                                 'B04.026.001.092', 'B04.047.001.091', 'B04.026.002.032',
                                 # детские профы
                                 'B04.031.001.001', 'B04.031.002.007', 'B04.031.002.008', 'B04.031.002.009',
                                 'B04.031.002.010', 'B04.031.002.011', 'B04.031.002.012', 'B04.031.002.013',
                                 'B04.031.002.014', 'B04.031.002.015', 'B04.031.002.016', 'B04.031.002.017',
                                 'B04.031.002.018', 'B04.031.002.019', 'B04.031.002.020', 'B04.031.002.021',
                                 'B04.031.002.022', 'B04.031.002.023', 'B04.031.002.024', 'B04.031.002.025',
                                 'B04.031.002.026', 'B04.031.002.027', 'B04.031.002.028', 'B04.031.002.029',
                                 'B04.031.002.030', 'B04.031.002.031', 'B04.031.002.032', 'B04.031.002.033',
                                 'B04.031.002.034', 'B04.031.002.035', 'B04.031.002.036', 'B04.031.002.037',
                                 'B04.031.002.038', 'B04.031.002.039', 'B04.031.002.040', 'B04.031.002.041',
                                 'B04.031.002.042', 'B04.031.002.043',
                                 'B04.001.001.022', 'B04.001.001.023', 'B04.001.001.024', 'B04.001.001.025',
                                 'B04.053.001.019', 'B04.057.001.030',
                                 'B04.047.009.011'
                                 ]

    def getGroupAccountType(self, eventTypeId):
        groupAccountType, matCode, rbEventProfileRegionalCode = self.mapEventTypeIdToGroupAccountType.get(eventTypeId, [None, None, None])
        if groupAccountType is None:
            db = QtGui.qApp.db
            record = db.getRecord('EventType left join rbMedicalAidType on EventType.medicalAidType_id = rbMedicalAidType.id \
            left join rbEventProfile ep on ep.id = EventType.eventProfile_id',
            'rbMedicalAidType.code, rbMedicalAidType.regionalCode, ep.regionalCode as eventProfile',
            eventTypeId)
            matCode = forceString(record.value('code' if QtGui.qApp.defaultKLADR()[:2] == '01' else 'regionalCode'))
            rbEventProfileRegionalCode = forceString(record.value('eventProfile'))
            groupAccountType = self.mapSpr13ToGroupAccountType.get(matCode)
            if QtGui.qApp.defaultKLADR()[:2] == '23':
                if groupAccountType == 5:
                    if rbEventProfileRegionalCode in ['8008', '8014', '8017']:
                        groupAccountType = 11
                    elif rbEventProfileRegionalCode in ['8009', '8015']:
                        groupAccountType = 12
                    elif rbEventProfileRegionalCode == '8011':
                        groupAccountType = 13
                    elif rbEventProfileRegionalCode == '8018':
                        groupAccountType = 26
                    elif rbEventProfileRegionalCode == '8019':
                        groupAccountType = 27
                    elif rbEventProfileRegionalCode == '8020':
                        groupAccountType = 31
                    elif rbEventProfileRegionalCode == '8021':
                        groupAccountType = 32
                elif groupAccountType in [1, 3, 4, 7]:
                    value = self.mapEventTypeToTFOMSAccIdent.get(eventTypeId, None)
                    if value is None:
                        value = getIdentification('EventType', eventTypeId, 'AccTFOMS', raiseIfNonFound=False)
                        self.mapEventTypeToTFOMSAccIdent[eventTypeId] = value if value is not None else ''
                    newGroupAccountType = {'ak': 16, 'am': 17, 'au': 18, 'ae': 19, 'ag': 20, 'ah': 21, 'ao': 22, 'av': 23, 'ap': 30, 'dnwork': 33, 'dneducate': 33}.get(value, None)
                    groupAccountType = newGroupAccountType if newGroupAccountType else groupAccountType
                elif groupAccountType == 6:
                    if matCode == '232':  # Диспансеризация детей-сирот
                        groupAccountType = 28
                    elif matCode == '252':  # диспансеризация детей остав-ся без попечения родит
                        groupAccountType = 29
            self.mapEventTypeIdToGroupAccountType[eventTypeId] = [groupAccountType, matCode, rbEventProfileRegionalCode]
        return groupAccountType, matCode, rbEventProfileRegionalCode
        
        
    def isDispCompleted(self, eventId):
        isCompleted = self.mapEventIdToDispCompleted.get(eventId)
        if isCompleted is None:
            db = QtGui.qApp.db
            isCompleted = not db.getCount("Action a left join ActionType at on at.id = a.actionType_id left join rbService s on s.id = at.nomenclativeService_id",
    'a.id', 
    "a.event_id = %d and a.deleted = 0 and s.infis in ('B04.026.001.062', 'B04.047.001.061', 'B04.047.001.092', 'B04.026.001.093')" % eventId)
            self.mapEventIdToDispCompleted[eventId] = isCompleted
        return isCompleted

    def getBaseTariff(self, eventEndDate, spr13Code):
        if spr13Code in ['11', '12', '301', '302', '401', '402']:
            group = 1
        elif spr13Code in ['41', '411', '42', '422', '43', '51', '511', '52', '522', '71', '72', '90']:
            group = 2
        else:
            group = 0
        if not self.mapBaseTariff:
            db = QtGui.qApp.db
            records = db.getRecordList('soc_spr89')
            for record in records:
                begDate = forceDate(record.value('DATN'))
                endDate = forceDate(record.value('DATO'))
                codeGR = forceInt(record.value('CODE_GR'))
                tariff = forceDouble(record.value('B_TARIFF'))
                key = (begDate, endDate, codeGR)
                self.mapBaseTariff[key] = tariff
        for (begDate, endDate, codeGR) in self.mapBaseTariff.keys():
            if codeGR == group and begDate <= eventEndDate and (eventEndDate <= endDate or endDate.isNull()):
                return self.mapBaseTariff[(begDate, endDate, codeGR)]
        return 0


    def isProfCompleted(self, eventId):
        isCompleted = self.mapEventIdToProfCompleted.get(eventId)
        if isCompleted is None:
            db = QtGui.qApp.db
            isCompleted = not db.getCount("Action a left join ActionType at on at.id = a.actionType_id left join rbService s on s.id = at.nomenclativeService_id",
    'a.id',
    "a.event_id = %d and a.deleted = 0 and s.infis in ('B04.047.002', 'B04.026.002')" % eventId)
            self.mapEventIdToProfCompleted[eventId] = isCompleted
        return isCompleted

    def isTwoYearsDisp(self, eventId):
        isTwoYears = self.mapEventIdToTwoYearsDisp.get(eventId)
        if isTwoYears is None:
            db = QtGui.qApp.db
            isTwoYears = db.getCount("Action a left join ActionType at on at.id = a.actionType_id left join rbService s on s.id = at.nomenclativeService_id",
    'a.id',
    "a.event_id = %d and a.deleted = 0 and s.infis in ('B04.047.001.092', 'B04.026.001.093')" % eventId)
            self.mapEventIdToTwoYearsDisp[eventId] = isTwoYears
        return isTwoYears


    def isOncology(self, eventId):
        result = self.mapEventIdToOncology.get(eventId)
        if result is None:
            db = QtGui.qApp.db
            tableDiagnostic = db.table('Diagnostic')
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnosisType = db.table('rbDiagnosisType')
            tableDiagnosticAssoc = db.table('Diagnostic').alias('ds')
            tableDiagnosisAssoc = db.table('Diagnosis').alias('dss')
            tableDiagnosisTypeAssoc = db.table('rbDiagnosisType').alias('dts')
            table = tableDiagnostic
            table = table.innerJoin(tableDiagnosis,
                                    tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id'])
                                    )
            table = table.innerJoin(tableDiagnosisType,
                                    tableDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id'])
                                    )
            table = table.leftJoin(tableDiagnosisTypeAssoc,
                                    tableDiagnosisTypeAssoc['code'].eq('9'))
            table = table.leftJoin(tableDiagnosticAssoc,
                                   db.joinAnd([tableDiagnosticAssoc['event_id'].eq(eventId),
                                               tableDiagnosticAssoc['diagnosisType_id'].eq(tableDiagnosisTypeAssoc['id']),
                                               tableDiagnosticAssoc['deleted'].eq(0)
                                              ])
                                   )
            table = table.leftJoin(tableDiagnosisAssoc, tableDiagnosisAssoc['id'].eq(tableDiagnosticAssoc['diagnosis_id']))
            onkoDiagnosisCondList = [tableDiagnosis['MKB'].like('C%'),
                                     tableDiagnosis['MKB'].between('D45', 'D47.9'),
                                     ]
            if QtGui.qApp.defaultKLADR()[:2] == '23':
                onkoDiagnosisCondList.extend([tableDiagnosis['MKB'].between('D00', 'D09.9'),
                                              db.joinAnd([tableDiagnosis['MKB'].eq('D70'),
                                                          db.joinOr([tableDiagnosisAssoc['MKB'].between('C00', 'C80.9'),
                                                                     tableDiagnosisAssoc['MKB'].eq('C97')
                                                                     ])
                                                          ])
                                              ])

            result = db.getCount(table,
                              '1',
                              db.joinAnd([tableDiagnostic['event_id'].eq(eventId),
                                          tableDiagnostic['deleted'].eq(0),
                                          tableDiagnosis['deleted'].eq(0),
                                          db.joinOr(onkoDiagnosisCondList),
                                          tableDiagnosisType['code'].inlist(
                                                                     ['1',  # заключительный
                                                                      '2'  # основной
                                                                      ]
                                                                     ),
                                         ])
                              )
            self.mapEventIdToOncology[eventId] = result
        return result
        
        
    # def calcAccountItemUnitId(self, serviceId, medicalAidTypeCode, price):
    #     unitId = self.mapServiceToUnitId.get((serviceId, medicalAidTypeCode, price), None)
    #     if not unitId:
    #         record = QtGui.qApp.db.getRecordEx('rbMedicalAidUnit', 'id', "regionalCode = getKSO(%d, '%s', %.2f)" % (serviceId, medicalAidTypeCode, price))
    #         if record:
    #             unitId = forceRef(record.value('id'))
    #             self.mapServiceToUnitId[(serviceId, medicalAidTypeCode, price)] = unitId
    #     return unitId


    def resetBuilder(self):
        self.mapMesIdToDescr.clear()
        self.mapCsgCodeToDescr.clear()
        self.mapEventIdToMKB.clear()
        # self.mapEventIdToPhaseId.clear()
        self.semifinishedMesRefuseTypeId = None
        self.clientRecordCache.invalidate()


    def exposeByEvents(self, progressDialog, contractDescr, accountFactory, eventIdList, checkMes, reexposableEventIdList):
        for eventId in eventIdList:
            if progressDialog:
                progressDialog.step()
                QtGui.qApp.processEvents()
            reexpose = eventId in reexposableEventIdList
            self.exposeEvent(contractDescr, accountFactory, eventId, reexpose)
            self.exposeEventAsCoupleVisit(contractDescr, accountFactory, eventId, reexpose)
            self.exposeEventByHospitalBedDay(contractDescr, accountFactory, eventId, reexpose)
            self.exposeVisitsByMes(contractDescr, accountFactory, eventId, checkMes, reexpose)
            self.exposeEventByMes(contractDescr,  accountFactory, eventId, reexpose)


    def exposeByVisitsByActionServices(self, progressDialog, contractDescr, accountFactory, mapServiceIdToVisitIdList, reexposableEventIdList):
        for serviceId, visitIdList in mapServiceIdToVisitIdList.items():
            for visitId in visitIdList:
                if progressDialog:
                    progressDialog.step()
                    QtGui.qApp.processEvents()
                self.exposeVisitByActionService(contractDescr, accountFactory, serviceId, visitId, reexposableEventIdList)


    def exposeByVisits(self, progressDialog, contractDescr, accountFactory, visitIdList, reexposableEventIdList):
        for visitId in visitIdList:
            if progressDialog:
                progressDialog.step()
                QtGui.qApp.processEvents()
            self.exposeVisit(contractDescr, accountFactory, visitId, reexposableEventIdList)


    def exposeByActions(self, progressDialog, contractDescr, accountFactory, actionIdList, reexposableEventIdList, date=None):
        for actionId in actionIdList:
            if progressDialog:
                progressDialog.step()
                QtGui.qApp.processEvents()
            self.exposeAction(contractDescr, accountFactory, actionId, date, reexposableEventIdList)


    def exposeByHospitalBedActionProperties(self, progressDialog, contractDescr, accountFactory, actionPropertyIdList, reexposableEventIdList):
        for actionPropertyId in actionPropertyIdList:
            if progressDialog:
                progressDialog.step()
                QtGui.qApp.processEvents()
            self.exposeHospitalBedActionProperty(contractDescr, accountFactory, actionPropertyId, reexposableEventIdList)


    def exposeVisitsByEventAndServicePairs(self, progressDialog, contractDescr, accountFactory, eventIdServiceIdPairList):
        for eventId, serviceId in eventIdServiceIdPairList:
            if progressDialog:
                progressDialog.step()
                QtGui.qApp.processEvents()
            self.exposeVisitsByEventAndServicePair(contractDescr, accountFactory, eventId, serviceId)


    def exposeByCsgs(self, progressDialog, contractDescr, accountFactory, csgIdList, reexposableEventIdList):
        for csgId in csgIdList:
            if progressDialog:
                progressDialog.step()
                QtGui.qApp.processEvents()
            if QtGui.qApp.defaultKLADR()[:2] == u'23':
                self.exposeCsg23(contractDescr, accountFactory, csgId, reexposableEventIdList)
            else:
                self.exposeCsg(contractDescr, accountFactory, csgId, reexposableEventIdList)


    def exposeEvent(self, contractDescr, accountFactory, eventId, reexpose):
        db = QtGui.qApp.db
        record = db.getRecord('''Event LEFT JOIN Person ON Person.id = Event.execPerson_id
                left join Account_Item ON Account_Item.event_id = Event.id and Account_Item.visit_id is null and Account_Item.action_id is null
                and Account_Item.refuseType_id is not null and Account_Item.reexposeItem_id is null and Account_Item.deleted = 0
                LEFT JOIN rbMesSpecification ON rbMesSpecification.id = Event.mesSpecification_id''',
                'Event.eventType_id, Event.setDate, Event.execDate, Event.MES_id, Event.cureMethod_id, Event.result_id, Event.client_id,  Person.tariffCategory_id, rbMesSpecification.level, Account_Item.id as oldAccId, Person.orgStructure_id',
            eventId)
        if record:
            eventTypeId  = forceRef(record.value('eventType_id'))
            cureMethodId = forceRef(record.value('cureMethod_id'))
            resultId     = forceRef(record.value('result_id'))
            mesLevel     = forceInt(record.value('level'))
            eventEndDate = forceDate(record.value('execDate'))
            tariffCategoryId = forceRef(record.value('tariffCategory_id'))
            tariffList = contractDescr.tariffByEventType.get(eventTypeId, None)
            serviceId = getEventServiceId(eventTypeId)
            personOrgStructId = forceRef(record.value('orgStructure_id'))

            if tariffList:
                for tariff in tariffList:
                    if ( self.isTariffApplicable(tariff, eventId, cureMethodId, resultId, mesLevel, tariffCategoryId, eventEndDate) and
                         ( tariff.serviceId is None or serviceId is None or tariff.serviceId == serviceId )
                       ):
                        eventBegDate = forceDate(record.value('setDate'))
                        mesId        = forceRef(record.value('MES_id'))
                        price = tariff.price
                        amount = 1.0
                        if tariff.enableCoefficients:
                            mesDescr = self.getMesDescr(mesId)
                            duration = getEventDuration(eventBegDate, eventEndDate, wpSevenDays, eventTypeId)
                            coefficient, usedCoefficients = self.getCoefficientAndReport(contractDescr, mesDescr, duration, eventEndDate, eventId)
                        else:
                            coefficient, usedCoefficients = 1.0, None
                        sum    = round(price*amount**coefficient, 2)
                        clientId = forceRef(record.value('client_id'))
                        oldAccId = forceRef(record.value('oldAccId'))
                        groupAccountType, medicalAidTypeCode, eventProfileRegionalCode = self.getGroupAccountType(eventTypeId)
                        # для группировки счетов по онкологии в стационарах в отдельные реестры
                        if groupAccountType in [1, 7] and eventEndDate >= QDate(2019, 3, 1):
                            if self.isOncology(eventId):
                                groupAccountType = 9 if groupAccountType == 1 else 10

                        account = accountFactory(clientId, eventEndDate, eventId, groupAccountType if QtGui.qApp.defaultKLADR()[:2] in ['23', '01'] else None, tariff.batch, reexpose, personOrgStructId)
                            
                        tableAccountItem = db.table('Account_Item')
                        accountItem = tableAccountItem.newRecord()
                        accountItem.setValue('master_id',        account.id)
                        accountItem.setValue('serviceDate',      eventEndDate)
                        accountItem.setValue('event_id',         eventId)
                        accountItem.setValue('price',            price)
                        accountItem.setValue('unit_id',          tariff.unitId)
                        accountItem.setValue('amount',           amount)
                        accountItem.setValue('sum',              sum)
                        accountItem.setValue('exposedSum',       sum)
                        accountItem.setValue('tariff_id',        tariff.id)
                        accountItem.setValue('service_id',       tariff.serviceId or serviceId)
                        accountItem.setValue('VAT',              tariff.vat)
                        accountItem.setValue('usedCoefficients', usedCoefficients)

                        newId = db.insertRecord(tableAccountItem, accountItem)

                        # если перевыставляем, добавляем ссылку в перевыставленный счет
                        if oldAccId:
                            oldAccountItem = db.getRecord(tableAccountItem, '*', oldAccId)
                            if oldAccountItem:
                                self.updateDocsPayStatus(oldAccountItem, contractDescr, CPayStatus.exposedBits)
                                oldAccountItem.setValue('reexposeItem_id', toVariant(newId))
                                db.updateRecord(tableAccountItem, oldAccountItem)

                        account.totalAmount += amount
                        account.totalSum    += sum
                        setEventPayStatus(eventId, contractDescr.payStatusMask, CPayStatus.exposedBits)
                        return


    def exposeEventAsCoupleVisit(self, contractDescr, accountFactory, eventId, reexpose):
        db = QtGui.qApp.db
        record = db.getRecord("Event LEFT JOIN Person ON Person.id = Event.execPerson_id \
        left join Account_Item ON Account_Item.event_id = Event.id and Account_Item.visit_id is null and Account_Item.action_id is null \
        and Account_Item.refuseType_id is not null and Account_Item.reexposeItem_id is null and Account_Item.deleted = 0 \
        LEFT JOIN rbMesSpecification ON rbMesSpecification.id = Event.mesSpecification_id",
        'Event.eventType_id, Event.setDate, Event.execDate, Event.MES_id, Event.client_id, Event.cureMethod_id, Event.result_id, Person.tariffCategory_id, rbMesSpecification.level, Account_Item.id as oldAccId, Person.orgStructure_id',
            eventId)
        if record:
            eventTypeId  = forceRef(record.value('eventType_id'))
            eventBegDate = forceDate(record.value('setDate'))
            eventEndDate = forceDate(record.value('execDate'))
            mesId        = forceRef(record.value('MES_id'))
            mesLevel     = forceInt(record.value('level'))
            cureMethodId = forceRef(record.value('cureMethod_id'))
            resultId     = forceRef(record.value('result_id'))
            tariffCategoryId = forceRef(record.value('tariffCategory_id'))
            tariffList = contractDescr.tariffByCoupleVisitEventType.get(eventTypeId, None)
            personOrgStructId = forceRef(record.value('orgStructure_id'))
            if tariffList:
                for tariff in tariffList:
                    if self.isTariffApplicable(tariff, eventId, cureMethodId, resultId, mesLevel, tariffCategoryId, eventEndDate):
                        serviceId = tariff.serviceId
                        if not serviceId:
                            continue
                        count = db.getCount('Visit', '1', 'event_id=%d AND service_id=%d AND deleted=0'%(eventId, serviceId))
                        if count == 0:
                            continue
                        if tariff.enableCoefficients:
                            mesDescr = self.getMesDescr(mesId)
                            duration = getEventDuration(eventBegDate, eventEndDate, wpSevenDays, eventTypeId)
                            coefficient, usedCoefficients = self.getCoefficientAndReport(contractDescr, mesDescr, duration, eventEndDate, eventId)
                        else:
                            coefficient, usedCoefficients = 1.0, None
                        amount = float(count)
                        amount, price, sum = tariff.evalAmountPriceSum(amount, coefficient)
                        clientId = forceRef(record.value('client_id'))
                        oldAccId = forceRef(record.value('oldAccId'))
                        groupAccountType, medicalAidTypeCode, eventProfileRegionalCode = self.getGroupAccountType(eventTypeId)
                        # для группировки счетов по онкологии в стационарах в отдельные реестры
                        if groupAccountType in [1, 7] and eventEndDate >= QDate(2019, 3, 1):
                            if self.isOncology(eventId):
                                groupAccountType = 9 if groupAccountType == 1 else 10

                        account = accountFactory(clientId, eventEndDate, eventId, groupAccountType if QtGui.qApp.defaultKLADR()[:2] == u'23' else None, tariff.batch, reexpose, personOrgStructId)

                        tableAccountItem = db.table('Account_Item')
                        accountItem = tableAccountItem.newRecord()
                        accountItem.setValue('master_id',        account.id)
                        accountItem.setValue('serviceDate',      eventEndDate)
                        accountItem.setValue('event_id',         eventId)
                        accountItem.setValue('price',            price)
                        accountItem.setValue('unit_id',          tariff.unitId)
                        accountItem.setValue('amount',           amount)
                        accountItem.setValue('sum',              sum)
                        accountItem.setValue('exposedSum',       sum)
                        accountItem.setValue('tariff_id',        tariff.id)
                        accountItem.setValue('service_id',       serviceId)
                        accountItem.setValue('VAT',              tariff.vat)
                        accountItem.setValue('usedCoefficients', usedCoefficients)
                        newId = db.insertRecord(tableAccountItem, accountItem)

                        # если перевыставляем, добавляем ссылку в перевыставленный счет
                        if oldAccId:
                            oldAccountItem = db.getRecord(tableAccountItem, '*', oldAccId)
                            if oldAccountItem:
                                self.updateDocsPayStatus(oldAccountItem, contractDescr, CPayStatus.exposedBits)
                                oldAccountItem.setValue('reexposeItem_id', toVariant(newId))
                                db.updateRecord(tableAccountItem, oldAccountItem)

                        account.totalAmount += amount
                        account.totalSum    += sum
                        setEventPayStatus(eventId, contractDescr.payStatusMask, CPayStatus.exposedBits)
                        return


    def exposeEventByHospitalBedDay(self, contractDescr, accountFactory, eventId, reexpose):
        db = QtGui.qApp.db
        record = db.getRecord("Event LEFT JOIN Person ON Person.id = Event.execPerson_id \
        left join Account_Item ON Account_Item.event_id = Event.id and Account_Item.visit_id is null and Account_Item.action_id is null \
        and Account_Item.refuseType_id is not null and Account_Item.reexposeItem_id is null and Account_Item.deleted = 0\
        LEFT JOIN rbMesSpecification ON rbMesSpecification.id = Event.mesSpecification_id",
            'Event.eventType_id, Event.setDate, Event.execDate, Event.MES_id, Event.cureMethod_id, Event.result_id, Event.client_id, Person.tariffCategory_id, rbMesSpecification.level, Account_Item.id as oldAccId, Person.orgStructure_id',
                              eventId)
        if record:
            eventTypeId  = forceRef(record.value('eventType_id'))
            eventBegDate = forceDate(record.value('setDate'))
            eventEndDate = forceDate(record.value('execDate'))
            mesId        = forceRef(record.value('MES_id'))
            mesLevel     = forceInt(record.value('level'))
            cureMethodId = forceRef(record.value('cureMethod_id'))
            resultId     = forceRef(record.value('result_id'))
            tariffCategoryId = forceRef(record.value('tariffCategory_id'))
            personOrgStructId = forceRef(record.value('orgStructure_id'))
            if eventBegDate and eventEndDate and eventBegDate<=eventEndDate:
                tariffList = contractDescr.tariffByHospitalBedDay.get(eventTypeId, None)
                if tariffList:
                    for tariff in tariffList:
                        if self.isTariffApplicable(tariff, eventId, cureMethodId, resultId, mesLevel, tariffCategoryId, eventEndDate):
                            if tariff.enableCoefficients:
                                mesDescr = self.getMesDescr(mesId)
                                duration = getEventDuration(eventBegDate, eventEndDate, wpSevenDays, eventTypeId)
                                coefficient, usedCoefficients = self.getCoefficientAndReport(contractDescr, mesDescr, duration, eventEndDate, eventId)
                                amount = 1.0
                            else:
                                coefficient, usedCoefficients = 1.0, None
                                count = eventBegDate.daysTo(eventEndDate)+1
                                amount = float(count)
                            amount, price, sum = tariff.evalAmountPriceSum(amount, coefficient)
                            clientId = forceRef(record.value('client_id'))
                            oldAccId = forceRef(record.value('oldAccId'))
                            groupAccountType, medicalAidTypeCode, eventProfileRegionalCode = self.getGroupAccountType(eventTypeId)
                            # для группировки счетов по онкологии в стационарах в отдельные реестры
                            if groupAccountType in [1, 7] and eventEndDate >= QDate(2019, 3, 1):
                                if self.isOncology(eventId):
                                    groupAccountType = 9 if groupAccountType == 1 else 10

                            account = accountFactory(clientId, eventEndDate, eventId, groupAccountType if QtGui.qApp.defaultKLADR()[:2] == u'23' else None, tariff.batch, reexpose, personOrgStructId)
                                
                            tableAccountItem = db.table('Account_Item')
                            accountItem = tableAccountItem.newRecord()
                            accountItem.setValue('master_id',        account.id)
                            accountItem.setValue('serviceDate',      eventEndDate)
                            accountItem.setValue('event_id',         eventId)
                            accountItem.setValue('price',            price)
                            accountItem.setValue('unit_id',          tariff.unitId)
                            accountItem.setValue('amount',           amount)
                            accountItem.setValue('sum',              sum)
                            accountItem.setValue('exposedSum',       sum)
                            accountItem.setValue('tariff_id',        tariff.id)
                            accountItem.setValue('service_id',       tariff.serviceId)
                            accountItem.setValue('VAT',              tariff.vat)
                            accountItem.setValue('usedCoefficients', usedCoefficients)
                            newId = db.insertRecord(tableAccountItem, accountItem)

                            # если перевыставляем, добавляем ссылку в перевыставленный счет
                            if oldAccId:
                                oldAccountItem = db.getRecord(tableAccountItem, '*', oldAccId)
                                if oldAccountItem:
                                    self.updateDocsPayStatus(oldAccountItem, contractDescr, CPayStatus.exposedBits)
                                    oldAccountItem.setValue('reexposeItem_id', toVariant(newId))
                                    db.updateRecord(tableAccountItem, oldAccountItem)

                            account.totalAmount += amount
                            account.totalSum    += sum
                            setEventPayStatus(eventId, contractDescr.payStatusMask, CPayStatus.exposedBits)
                            return


    def exposeVisitsByMes(self, contractDescr, accountFactory, eventId, checkMes, reexposableEventIdList):
        db = QtGui.qApp.db
        record = db.getRecord("Event LEFT JOIN Person ON Person.id = Event.execPerson_id \
            left join Account_Item ON Account_Item.event_id = Event.id and Account_Item.visit_id is null and Account_Item.action_id is null \
            and Account_Item.refuseType_id is not null and Account_Item.reexposeItem_id is null and Account_Item.deleted = 0\
            LEFT JOIN rbMesSpecification ON rbMesSpecification.id = Event.mesSpecification_id",
            """Event.eventType_id, Event.setDate, Event.execDate, Event.MES_id, Event.client_id, Event.cureMethod_id, Event.result_id, Person.tariffCategory_id, rbMesSpecification.level,
            Account_Item.id as oldAccId, Person.orgStructure_id""",
            eventId)
        eventTypeId  = forceRef(record.value('eventType_id'))
        eventBegDate = forceDate(record.value('setDate'))
        eventEndDate = forceDate(record.value('execDate'))
        mesId        = forceRef(record.value('MES_id'))
        mesLevel     = forceInt(record.value('level'))
        cureMethodId = forceRef(record.value('cureMethod_id'))
        resultId     = forceRef(record.value('result_id'))
        serviceId = self.getMesService(mesId)
        tariffCategoryId = forceRef(record.value('tariffCategory_id'))
        personOrgStructId = forceRef(record.value('orgStructure_id'))
        tariffList = contractDescr.tariffVisitsByMES.get((eventTypeId, serviceId), None)
        if tariffList and mesId:
            for tariff in tariffList:
                if self.isTariffApplicable(tariff, eventId, cureMethodId, resultId, mesLevel, tariffCategoryId, eventEndDate):
                    if tariff.enableCoefficients:
                        mesDescr = self.getMesDescr(mesId)
                        duration = getEventDuration(eventBegDate, eventEndDate, wpSevenDays, eventTypeId)
                        coefficient, usedCoefficients = self.getCoefficientAndReport(contractDescr, mesDescr, duration, eventEndDate, eventId)
                    else:
                        coefficient, usedCoefficients = 1.0, None
#                    price  = tariff.price
                    amount = float(getMesAmount(eventId, mesId))
                    amount, price, sum = tariff.evalAmountPriceSum(amount, coefficient)
#                    sum    = round(price*amount, 2)
                    clientId = forceRef(record.value('client_id'))
                    
                    oldAccId = forceRef(record.value('oldAccId'))
                    reexpose = self.reexposeEventIdDict.get(eventId, 0)
                    if not reexpose:
                        reexpose = forceBool(record.value('reexpose'))
                        self.reexposeEventIdDict[eventId] = reexpose
                    account = accountFactory(clientId, eventEndDate, eventId, tariff.batch, reexpose, personOrgStructId)
                        
                    tableAccountItem = db.table('Account_Item')
                    accountItem = tableAccountItem.newRecord()
                    accountItem.setValue('master_id',        account.id)
                    accountItem.setValue('serviceDate',      eventEndDate)
                    accountItem.setValue('event_id',         eventId)
                    accountItem.setValue('price',            tariff.price)
                    accountItem.setValue('unit_id',          tariff.unitId)
                    accountItem.setValue('amount',           amount)
                    accountItem.setValue('sum',              sum)
                    accountItem.setValue('exposedSum',       sum)
                    accountItem.setValue('tariff_id',        tariff.id)
                    accountItem.setValue('service_id',       serviceId)
                    accountItem.setValue('VAT',              tariff.vat)
                    accountItem.setValue('usedCoefficients', usedCoefficients)
                    if checkMes:
                        norm = self.getMesNorm(mesId)
                        if amount < norm:
                            self.rejectAccountItemBySemifinishedMes(accountItem, contractDescr.financeId)
                    newId = db.insertRecord(tableAccountItem, accountItem)
                    
                    # если перевыставляем, добавляем ссылку в перевыставленный счет
                    if reexpose and oldAccId:
                        oldAccountItem = db.getRecord(tableAccountItem, '*', oldAccId)
                        if oldAccountItem:
                            self.updateDocsPayStatus(oldAccountItem, contractDescr, CPayStatus.exposedBits)
                            oldAccountItem.setValue('reexposeItem_id', toVariant(newId))
                            db.updateRecord(tableAccountItem, oldAccountItem)
                        
                    account.totalAmount += amount
                    account.totalSum    += sum
                    setEventPayStatus(eventId, contractDescr.payStatusMask, CPayStatus.exposedBits)
                    setEventVisitsPayStatus(eventId, contractDescr.payStatusMask, CPayStatus.exposedBits)
                    return


    def exposeEventByMes(self, contractDescr, accountFactory, eventId, reexpose):
        db = QtGui.qApp.db
        record = db.getRecord("Event LEFT JOIN Person ON Person.id = Event.execPerson_id LEFT JOIN rbMesSpecification ON rbMesSpecification.id=Event.mesSpecification_id  left join \
        Account_Item ON Account_Item.event_id = Event.id and Account_Item.visit_id is null and Account_Item.action_id is null \
        and Account_Item.refuseType_id is not null and Account_Item.reexposeItem_id is null and Account_Item.deleted = 0",
            """Event.eventType_id, Event.cureMethod_id, Event.result_id, Event.client_id, Event.setDate, Event.execDate, Event.MES_id, Person.tariffCategory_id, rbMesSpecification.level, 
            Account_Item.id as oldAccId, Event.relative_id, Person.orgStructure_id""",
            eventId)
        eventTypeId  = forceRef(record.value('eventType_id'))
        cureMethodId = forceRef(record.value('cureMethod_id'))
        resultId     = forceRef(record.value('result_id'))
        mesLevel     = forceInt(record.value('level'))
        eventBegDate = forceDate(record.value('setDate'))
        eventEndDate = forceDate(record.value('execDate'))
        mesId = forceRef(record.value('MES_id'))
        relative_id = forceInt(record.value('relative_id'))
        serviceId = self.getMesService(mesId)
        coeff = None
        interruptReason = None
        interruptCoeff = None
        tariffCategoryId = forceRef(record.value('tariffCategory_id'))
        personOrgStructId = forceRef(record.value('orgStructure_id'))
        tariffList = contractDescr.tariffEventByMES.get((eventTypeId, serviceId), None)
        if tariffList is None and QtGui.qApp.defaultKLADR()[:2] == u'23':
            tariffList = contractDescr.tariffEventByMES.get((None, serviceId), None)
        if tariffList and mesId:
            for tariff in tariffList:
                if self.isTariffApplicable(tariff, eventId, cureMethodId, resultId, mesLevel, tariffCategoryId, eventEndDate):
                    clientId = forceRef(record.value('client_id'))
                    # price  = tariff.price
                    duration = getEventDuration(eventBegDate, eventEndDate, wpSevenDays, eventTypeId)
                    mesDescr = self.getMesDescr(mesId)
                    if tariff.enableCoefficients:
                        coefficient, usedCoefficients = self.getCoefficientAndReport(contractDescr, mesDescr, duration, eventEndDate, eventId, None)
                    else:
                        coefficient, usedCoefficients = 1.0, None
                    if tariff.tariffType == CTariff.ttEventByMESLen:
                        amount, price, sum = tariff.evalAmountPriceSum(duration, coefficient)
                    elif tariff.tariffType == CTariff.ttEventByMESLevel:
                        amount = float(duration)/mesDescr.avgDuration if mesDescr.avgDuration else 1
                        if mesLevel == 2: # выполнен полностью:
                            amount = 1
                        else: # fallback
                            amount = min(1, amount)
                        amount, price, sum = tariff.evalAmountPriceSum(amount, coefficient)
                    elif tariff.tariffType == CTariff.ttKrasnodarA13:
                        amount = 1.0
                        groupAccountType, medicalAidTypeCode, eventProfileRegionalCode = self.getGroupAccountType(eventTypeId)
                        baseTariff = self.getBaseTariff(eventEndDate, medicalAidTypeCode)
                        price, coeff, usedCoeffDict, interruptReason, interruptCoeff = evalPriceForKrasnodarA13(contractDescr, tariff, clientId, eventId, eventTypeId, eventBegDate, eventEndDate, relative_id, self.getServiceInfis(serviceId), baseTariff)
                        sum = price = round(price, 2)
                        if usedCoeffDict:
                            coeffList = []
                            for c in sorted(usedCoeffDict):
                                coeffList.append('{0}({1});'.format(c, usedCoeffDict[c]))
                                usedCoefficients = ''.join(coeffList)

                    elif tariff.tariffType == CTariff.ttMurmansk2015Hospital:
                        eventBegDateTime = forceDateTime(record.value('setDate'))
                        eventEndDateTime = forceDateTime(record.value('execDate'))
                        shortHospitalisation = eventBegDateTime.addDays(1) > eventEndDateTime
                        level = forceInt(record.value('level'))
                        amount = 1.0
                        price = evalPriceForMurmansk2015Hospital(contractDescr, tariff, eventId, eventTypeId, eventBegDate, eventEndDate,  mesId, shortHospitalisation, level, mesDescr = mesDescr)
                        sum = round(price*coefficient, 2)
                    else:
                        amount, price, sum = tariff.evalAmountPriceSum(1, coefficient)

                    oldAccId = forceRef(record.value('oldAccId'))
                    groupAccountType, medicalAidTypeCode, eventProfileRegionalCode = self.getGroupAccountType(eventTypeId)
                    # для группировки счетов по онкологии в стационарах в отдельные реестры
                    if QtGui.qApp.defaultKLADR()[:2] == '23' and groupAccountType in [1, 7] and eventEndDate >= QDate(
                            2019, 3, 1):
                        if self.isOncology(eventId):
                            groupAccountType = 9 if groupAccountType == 1 else 10
                    elif QtGui.qApp.defaultKLADR()[:2] == '01' and groupAccountType in [1, 3]:
                        if self.isOncology(eventId):
                            groupAccountType = 2 if groupAccountType == 1 else 4

                    account = accountFactory(clientId, eventEndDate, eventId, groupAccountType if QtGui.qApp.defaultKLADR()[:2] == u'23' else None, tariff.batch, reexpose, personOrgStructId)

                    unitId = tariff.unitId
                    # if QtGui.qApp.defaultKLADR()[:2] == u'23':
                    # # вычисление КСО
                    #     if not unitId:
                    #         unitId = self.calcAccountItemUnitId(serviceId, medicalAidTypeCode, price)
                    tableAccountItem = db.table('Account_Item')
                    accountItem = tableAccountItem.newRecord()
                    accountItem.setValue('master_id',  toVariant(account.id))
                    accountItem.setValue('serviceDate',toVariant(eventEndDate))
                    accountItem.setValue('event_id',   toVariant(eventId))
                    accountItem.setValue('price',      toVariant(price))
                    accountItem.setValue('unit_id',    toVariant(unitId))
                    accountItem.setValue('amount',     toVariant(amount))
                    accountItem.setValue('sum',        toVariant(sum))
                    accountItem.setValue('exposedSum', sum)
                    accountItem.setValue('tariff_id',  toVariant(tariff.id))
                    accountItem.setValue('service_id', toVariant(serviceId))
                    accountItem.setValue('VAT',  toVariant(tariff.vat))
                    accountItem.setValue('usedCoefficients', toVariant(usedCoefficients))
                    if usedCoefficients:
                        accountItem.setValue('usedCoefficientsValue', toVariant(coeff))
                    if interruptReason:
                        accountItem.setValue('interruptReason', toVariant(interruptReason))
                        accountItem.setValue('interruptCoeff', toVariant(interruptCoeff))
                    newId = db.insertRecord(tableAccountItem, accountItem)
                    
                    # если перевыставляем, добавляем ссылку в перевыставленный счет
                    if oldAccId:
                        oldAccountItem = db.getRecord(tableAccountItem, '*', oldAccId)
                        if oldAccountItem:
                            self.updateDocsPayStatus(oldAccountItem, contractDescr, CPayStatus.exposedBits)
                            oldAccountItem.setValue('reexposeItem_id', toVariant(newId))
                            db.updateRecord(tableAccountItem, oldAccountItem)
                        
                    account.totalAmount += amount
                    account.totalSum    += sum
                    setEventPayStatus(eventId, contractDescr.payStatusMask, CPayStatus.exposedBits)
                    return


    def exposeVisitByActionService(self, contractDescr, accountFactory, serviceId, visitId, reexposableEventIdList):
        db = QtGui.qApp.db
        record = db.getRecord("Visit LEFT JOIN Person ON Person.id = Visit.person_id LEFT JOIN Event ON Event.id=Visit.event_id \
        left join Account_Item ON Account_Item.event_id = Event.id and Account_Item.visit_id = Visit.id and Account_Item.action_id is null \
        and Account_Item.refuseType_id is not null and Account_Item.reexposeItem_id is null and Account_Item.deleted = 0\
        LEFT JOIN rbMesSpecification ON rbMesSpecification.id = Event.mesSpecification_id",
                              'Event.eventType_id, Event.setDate, Event.execDate, Event.MES_id, Event.client_id, Event.cureMethod_id, Event.result_id, Visit.id, Visit.event_id, Visit.date, Person.tariffCategory_id, rbMesSpecification.level, Person.orgStructure_id',
                             visitId)
        tariffList = contractDescr.tariffVisitByActionService.get(serviceId, None)
        if tariffList:
            eventId      = forceRef(record.value('event_id'))
            eventTypeId  = forceRef(record.value('eventType_id'))
            eventBegDate = forceDate(record.value('setDate'))
            eventEndDate = forceDate(record.value('execDate'))
            mesId        = forceRef(record.value('MES_id'))
            mesLevel     = forceInt(record.value('level'))
            cureMethodId = forceRef(record.value('cureMethod_id'))
            resultId     = forceRef(record.value('result_id'))
            visitDate    = forceDate(record.value('date'))
            tariffCategoryId = forceRef(record.value('tariffCategory_id'))
            for tariff in tariffList:
                if self.isTariffApplicable(tariff, eventId, cureMethodId, resultId, mesLevel, tariffCategoryId, visitDate):
                    if tariff.enableCoefficients:
                        mesDescr = self.getMesDescr(mesId)
                        duration = getEventDuration(eventBegDate, eventEndDate, wpSevenDays, eventTypeId)
                        coefficient, usedCoefficients = self.getCoefficientAndReport(contractDescr, mesDescr, duration, eventEndDate, eventId,  visitId=visitId)
                    else:
                        coefficient, usedCoefficients = 1.0, None
                    price  = tariff.price
                    amount = 1.0
                    sum    = round(price*amount*coefficient, 2)
                    clientId = forceRef(record.value('client_id'))
                    
                    oldAccId = forceRef(record.value('oldAccId'))
                    reexpose = eventId in reexposableEventIdList
                    groupAccountType, medicalAidTypeCode, eventProfileRegionalCode = self.getGroupAccountType(eventTypeId)
                    # для группировки счетов по онкологии в стационарах в отдельные реестры
                    if groupAccountType in [1, 7] and visitDate >= QDate(2019, 3, 1):
                        if self.isOncology(eventId):
                            groupAccountType = 9 if groupAccountType == 1 else 10
                    account = accountFactory(clientId, visitDate, eventId, groupAccountType if QtGui.qApp.defaultKLADR()[:2] == u'23' else None, tariff.batch, reexpose)
                        
                    tableAccountItem = db.table('Account_Item')
                    accountItem = tableAccountItem.newRecord()
                    accountItem.setValue('master_id',        account.id)
                    accountItem.setValue('serviceDate',      visitDate)
                    accountItem.setValue('event_id',         eventId)
                    accountItem.setValue('visit_id',         visitId)
                    accountItem.setValue('price',            price)
                    accountItem.setValue('unit_id',          tariff.unitId)
                    accountItem.setValue('amount',           amount)
                    accountItem.setValue('sum',              sum)
                    accountItem.setValue('exposedSum',       sum)
                    accountItem.setValue('tariff_id',        tariff.id)
                    accountItem.setValue('service_id',       serviceId)
                    accountItem.setValue('VAT',              tariff.vat)
                    accountItem.setValue('usedCoefficients', usedCoefficients)
                    newId = db.insertRecord(tableAccountItem, accountItem)
                    
                    # если перевыставляем, добавляем ссылку в перевыставленный счет
                    if oldAccId:
                        oldAccountItem = db.getRecord(tableAccountItem, '*', oldAccId)
                        if oldAccountItem:
                            self.updateDocsPayStatus(oldAccountItem, contractDescr, CPayStatus.exposedBits)
                            oldAccountItem.setValue('reexposeItem_id', toVariant(newId))
                            db.updateRecord(tableAccountItem, oldAccountItem)
                            
                    account.totalAmount += amount
                    account.totalSum    += sum
                    setVisitPayStatus(visitId, contractDescr.payStatusMask, CPayStatus.exposedBits)
                    return


    def exposeVisit(self, contractDescr, accountFactory, visitId, reexposableEventIdList):
        db = QtGui.qApp.db
        record = db.getRecord("Visit LEFT JOIN Person ON Person.id = Visit.person_id LEFT JOIN Event ON Event.id = Visit.event_id \
            left join Account_Item ON Account_Item.event_id = Event.id and Account_Item.visit_id = Visit.id and Account_Item.action_id is null \
            and Account_Item.refuseType_id is not null and Account_Item.reexposeItem_id is null and Account_Item.deleted = 0 \
            LEFT JOIN rbMesSpecification ON rbMesSpecification.id = Event.mesSpecification_id",
            """Event.eventType_id, Event.setDate, Event.execDate, Event.MES_id, Event.client_id, Event.cureMethod_id, Event.result_id, Visit.id, Visit.event_id, Visit.date, Visit.service_id, Person.tariffCategory_id, rbMesSpecification.level,
            Account_Item.id as oldAccId, Person.orgStructure_id""",
            visitId)
        serviceId = forceRef(record.value('service_id'))
        tariffList = contractDescr.tariffByVisitService.get(serviceId, None)
        if tariffList:
            eventId      = forceRef(record.value('event_id'))
            eventTypeId  = forceRef(record.value('eventType_id'))
            eventBegDate = forceDate(record.value('setDate'))
            eventEndDate = forceDate(record.value('execDate'))
            mesId        = forceRef(record.value('MES_id'))
            mesLevel     = forceInt(record.value('level'))
            cureMethodId = forceRef(record.value('cureMethod_id'))
            resultId     = forceRef(record.value('result_id'))
            visitDate    = forceDate(record.value('date'))
            tariffCategoryId = forceRef(record.value('tariffCategory_id'))
            personOrgStructId = forceRef(record.value('orgStructure_id'))

            for tariff in tariffList:
                if self.isTariffApplicable(tariff, eventId, cureMethodId, resultId, mesLevel, tariffCategoryId, visitDate):
                    if tariff.enableCoefficients:
                        mesDescr = self.getMesDescr(mesId)
                        duration = getEventDuration(eventBegDate, eventEndDate, wpSevenDays, eventTypeId)
                        coefficient, usedCoefficients = self.getCoefficientAndReport(contractDescr, mesDescr, duration, eventEndDate, eventId, visitId=visitId)
                    else:
                        coefficient, usedCoefficients = 1.0, None
                    price  = tariff.price
                    amount = 1.0
                    sum    = round(price*amount*coefficient, 2)
                    clientId = forceRef(record.value('client_id'))
                    oldAccId = forceRef(record.value('oldAccId'))
                    unitId = tariff.unitId
                    reexpose = eventId in reexposableEventIdList
                    groupAccountType, medicalAidTypeCode, eventProfileRegionalCode = self.getGroupAccountType(eventTypeId)
                    # для группировки счетов по онкологии в стационарах в отдельные реестры
                    if QtGui.qApp.defaultKLADR()[:2] == '23' and groupAccountType in [1, 7] and eventEndDate >= QDate(
                            2019, 3, 1):
                        if self.isOncology(eventId):
                            groupAccountType = 9 if groupAccountType == 1 else 10
                    elif QtGui.qApp.defaultKLADR()[:2] == '01' and groupAccountType in [1, 3]:
                        if self.isOncology(eventId):
                            groupAccountType = 2 if groupAccountType == 1 else 4

                    account = accountFactory(clientId, eventEndDate if QtGui.qApp.defaultKLADR()[:2] == u'23' else visitDate, eventId, groupAccountType, tariff.batch, reexpose, personOrgStructId)

                    if eventEndDate >= QDate(2020, 1, 1) and medicalAidTypeCode in ['211', '261', '233', '244', '232', '252', '262'] and self.getServiceInfis(serviceId) in self.complexVisitList:
                        eventWeekProfile = wpFiveDays
                        # В случае проведения мероприятий в рамках профилактических осмотров,
                        # включая диспансеризацию в выходные дни
                        if countWorkDays(eventEndDate, eventEndDate, eventWeekProfile) == 0:
                            price = round(round(price, 2) * 1.03, 2)
                            sum = price * amount

                        # В случае проведения мобильными медицинскими бригадами полного комплекса мероприятий
                        # в рамках профилактических осмотров, включая диспансеризацию
                        if QDate(2023, 1, 1) <= eventEndDate < QDate(2025, 2, 1):
                            value = self.mapEventTypeToTFOMSAccIdent.get(eventTypeId, None)
                            if value is None:
                                value = getIdentification('EventType', eventTypeId, 'AccTFOMS', raiseIfNonFound=False)
                                self.mapEventTypeToTFOMSAccIdent[eventTypeId] = value if value is not None else ''
                            if value in ['mob']:
                                price = round(round(price, 2) * 1.2, 2)
                                sum = price * amount

                    tableAccountItem = db.table('Account_Item')
                    accountItem = tableAccountItem.newRecord()
                    accountItem.setValue('master_id',        account.id)
                    accountItem.setValue('serviceDate',      visitDate)
                    accountItem.setValue('event_id',         eventId)
                    accountItem.setValue('visit_id',         visitId)
                    accountItem.setValue('price',            price)
                    accountItem.setValue('unit_id',          unitId)
                    accountItem.setValue('amount',           amount)
                    accountItem.setValue('sum',              sum)
                    accountItem.setValue('exposedSum',       sum)
                    accountItem.setValue('tariff_id',        tariff.id)
                    accountItem.setValue('service_id',       serviceId)
                    accountItem.setValue('VAT',              tariff.vat)
                    accountItem.setValue('usedCoefficients', usedCoefficients)
                    newId = db.insertRecord(tableAccountItem, accountItem)
                    
                    # если перевыставляем, добавляем ссылку в перевыставленный счет
                    if oldAccId:
                        oldAccountItem = db.getRecord(tableAccountItem, '*', oldAccId)
                        if oldAccountItem:
                            self.updateDocsPayStatus(oldAccountItem, contractDescr, CPayStatus.exposedBits)
                            oldAccountItem.setValue('reexposeItem_id', toVariant(newId))
                            db.updateRecord(tableAccountItem, oldAccountItem)
                        
                    account.totalAmount += amount
                    account.totalSum    += sum
                    setVisitPayStatus(visitId, contractDescr.payStatusMask, CPayStatus.exposedBits)

                    return


    def exposeAction(self, contractDescr, accountFactory, actionId, date, reexposableEventIdList):
        db = QtGui.qApp.db
        record = db.getRecord("""vAction 
            LEFT JOIN Person ON Person.id = vAction.person_id 
            LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id
            LEFT JOIN Event ON Event.id = vAction.event_id
            left join Client on Client.id = Event.client_id 
            left join Account_Item ON Account_Item.event_id = Event.id and Account_Item.action_id = vAction.id
                and Account_Item.refuseType_id is not null and Account_Item.reexposeItem_id is null and Account_Item.deleted = 0""",
            """Event.id as eventId, Event.setDate, Event.result_id, Event.eventType_id, Event.client_id, vAction.id, vAction.actionType_id, Event.eventType_id, 
            vAction.event_id, vAction.exposeDate, vAction.amount, vAction.MKB, Person.tariffCategory_id, Event.execDate, 
            Account_Item.id as oldAccId, Client.birthDate, vAction.org_id, rbSpeciality.regionalCode as specCode, vAction.begDate as actionBegDate, vAction.endDate as actionEndDate, vAction.status as actionStatus, Person.orgStructure_id""",
            actionId)
        if record:
            serviceIdList = self.getActionTypeServiceIdList(forceRef(record.value('actionType_id')), contractDescr.financeId)
            origAmount = forceDouble(record.value('amount'))
            lpuId = QtGui.qApp.currentOrgId()
            orgInfisCode = self.mapOrgIdToInfis.get(lpuId, None)
            if orgInfisCode is None:
                orgInfisCode = forceString(db.translate('Organisation', 'id', lpuId, 'infisCode'))
                self.mapOrgIdToInfis[lpuId] = orgInfisCode
            for serviceId in serviceIdList:
                tariffList = contractDescr.tariffByActionService.get(serviceId, None)
                if tariffList:
                    eventId      = forceRef(record.value('event_id'))
                    eventTypeId  = forceRef(record.value('eventType_id'))
                    eventBegDate = forceDate(record.value('setDate'))
                    eventEndDate = forceDate(record.value('execDate'))
                    orgId = forceRef(record.value('org_id'))
                    birthDate = forceDate(record.value('birthDate'))
                    clientId = forceRef(record.value('client_id'))
                    mesId        = forceRef(record.value('MES_id'))
                    mesLevel     = forceInt(record.value('level'))
                    cureMethodId = forceRef(record.value('cureMethod_id'))
                    resultId     = forceRef(record.value('result_id'))
                    exposeDate   = forceDate(record.value('exposeDate')) or date
                    MKB = forceString(record.value('MKB'))
                    tariffCategoryId = forceRef(record.value('tariffCategory_id'))
                    specialityCode = forceString(record.value('specCode'))
                    personOrgStructId = forceRef(record.value('orgStructure_id'))
                    actionStatus = forceInt(record.value('actionStatus'))

                    groupAccountType, medicalAidTypeCode, eventProfileRegionalCode = self.getGroupAccountType(eventTypeId)
                    # для группировки счетов по онкологии в стационарах в отдельные реестры
                    if QtGui.qApp.defaultKLADR()[:2] == '23' and groupAccountType in [1, 7] and eventEndDate >= QDate(2019, 3, 1):
                        if self.isOncology(eventId):
                            groupAccountType = 9 if groupAccountType == 1 else 10
                    elif QtGui.qApp.defaultKLADR()[:2] == '01' and groupAccountType in [1, 3]:
                        if self.isOncology(eventId):
                            groupAccountType = 2 if groupAccountType == 1 else 4

                    # # актуально ли?! Травма для поликлиники 11007
                    # if orgInfisCode == '11007' and specialityCode == '79' and medicalAidTypeCode in ['271', '272'] and eventEndDate >= QDate(2019, 6, 1):
                    #     eventMKB = self.mapEventIdToMKB.get(eventId, None)
                    #     if eventMKB is None:
                    #         eventMKB = getEventDiagnosis(eventId)
                    #         self.mapEventIdToMKB[eventId] = eventMKB
                    #     if eventMKB >=  'S00.00' and eventMKB <= 'T98.99':
                    #         medicalAidTypeCode = '21' if medicalAidTypeCode == '271' else '22'
                    #         groupAccountType = 3
                    
                    for tariff in tariffList:
                        if actionStatus == 6 and self.getServiceInfis(serviceId) in ('A08.20.017.002', 'A08.20.040', 'A01.20.003', 'A26.20.034.001', 'A26.20.009.002', 'A26.20.068'):
                            # если услуга по проф с отказом, но относится к услугам с особым случаем virgio, то не выставляем
                            return
                        elif actionStatus == 6:
                            exposeDate = forceDate(record.value('actionBegDate'))
                        if self.isTariffApplicable(tariff, eventId, cureMethodId, resultId, mesLevel, tariffCategoryId, exposeDate, MKB):
                            if tariff.enableCoefficients:
                                mesDescr = self.getMesDescr(mesId)
                                duration = getEventDuration(eventBegDate, eventEndDate, wpSevenDays, eventTypeId)
                                coefficient, usedCoefficients = self.getCoefficientAndReport(contractDescr, mesDescr, duration, eventEndDate, eventId, actionId=actionId)
                            else:
                                coefficient, usedCoefficients = 1.0, None
                            amount, price, sum = tariff.evalAmountPriceSum(origAmount, coefficient)
                            if actionStatus == 6:
                                # обнуляем количество и тариф у отказанных услуг
                                amount, price, sum = 0, 0, 0
                            uet = amount * tariff.uet if tariff.tariffType == CTariff.ttActionUET else 0
                            unitId = tariff.unitId
                            oldAccId = forceRef(record.value('oldAccId'))
                            reexpose = eventId in reexposableEventIdList
                            orgCode = None
                            account = accountFactory(clientId, eventEndDate if QtGui.qApp.defaultKLADR()[:2] == u'23' else exposeDate, eventId,  groupAccountType if QtGui.qApp.defaultKLADR()[:2] in ['23', '01'] else None, tariff.batch, reexpose, personOrgStructId)
                            if orgId:
                                orgCode = self.mapOrgIdToInfis.get(orgId, None)
                                if orgCode is None:
                                    orgCode = forceString(db.translate('Organisation', 'id', orgId, 'infisCode'))
                                    self.mapOrgIdToInfis[orgId] = orgCode

                            if QtGui.qApp.defaultKLADR()[:2] == u'23':
                                # с 2017-09-01 для инокраевых пациентов в пол-ках с прикрепленным населением меняем УОМП
                                if medicalAidTypeCode in ['271', '272'] and (account.settleDate >= QDate(2020, 5, 1) or eventEndDate >= QDate(2017, 9, 1) and account.payerId == contractDescr.payerId):
                                    medicalAidTypeCode = '21' if medicalAidTypeCode == '271' else '22'

                                # по маммографии с ии должен быть TARU - с ценой, SUMM - 0
                                if self.getServiceInfis(serviceId) == 'A06.30.002.017':
                                    sum = 0
                                #Скорая помощь vp in (801, 802) OKATO_OMS == '03000' KUSL like 'B01.044%' должен быть TARU - с ценой, SUMM - 0 с 01.01.2025
                                elif medicalAidTypeCode in ('801', '802') and self.getServiceInfis(serviceId).startswith('B01.044') and eventEndDate >= QDate(2025, 2, 1):
                                    from Registry.Utils import getClientCompulsoryPolicy
                                    record = getClientCompulsoryPolicy(clientId, eventEndDate, eventId)
                                    if record:
                                        if forceString(db.translate('Organisation', 'id', forceRef(record.value('insurer_id')), "OKATO")) == '03000':
                                            sum = 0
                                # тарификация услуг обращения/посещения для поликлиники
                                elif (eventEndDate >= QDate(2019, 3, 1) and medicalAidTypeCode in ['21', '22'] and self.getServiceInfis(serviceId)[:3] in ['B01', 'B02', 'B04', 'B05']\
                                        and serviceId not in self.ObrServiceIdList and self.serviceHasObr(eventId, self.getServiceInfis(serviceId)[4:7])
                                        and self.getServiceInfis(serviceId) not in ['B05.015.002.010', 'B05.015.002.011', 'B05.015.002.012', 'B05.023.002.012',
                                                                         'B05.023.002.013', 'B05.023.002.14', 'B05.050.004.019', 'B05.050.004.020', 'B05.050.004.021',
                                                                         'B05.070.010', 'B05.070.011', 'B05.070.012']):
                                    price, sum = 0, 0
                                # обнуление услуг по реабилитации
                                elif eventEndDate >= QDate(2022, 10, 1) and medicalAidTypeCode == '21' \
                                        and self.eventHasReab(eventId)\
                                        and self.getServiceInfis(serviceId) not in ['B05.015.002.010', 'B05.015.002.011', 'B05.015.002.012', 'B05.023.002.012',
                                                                         'B05.023.002.013', 'B05.023.002.14', 'B05.050.004.019', 'B05.050.004.020', 'B05.050.004.021',
                                                                         'B05.070.010', 'B05.070.011', 'B05.070.012']:
                                    price, sum = 0, 0
                                # обнуление стоимости у краевых застрахованных участковой службы
                                elif medicalAidTypeCode in ['271', '272'] and exposeDate >= QDate(2017, 1, 1) and account.payerId != contractDescr.payerId:
                                    price, sum = 0, 0
                                # для ранее оказанных и внешних услуг - цена равна 0
                                elif eventBegDate > exposeDate or orgId and medicalAidTypeCode not in ('222', '232', '211', '252', '233', '244', '261', '262') or orgId and orgCode not in self.omsCodes:
                                    price, sum = 0, 0
                                # профилактические мероприятия с февраля 2026 новые правила тарификации
                                # все простые услуги должны выставляться в поле Taru с ценой из договора, поле summ нулевые
                                # а комплексная услуга в поле Taru c нулевой ценой, поле summ сумма всех простых услуг (пересчитывается в процедуре beforeUpdateAccount).
                                elif (eventEndDate >= QDate(2026, 2, 1)
                                      and medicalAidTypeCode in ['211', '261', '233', '244', '232', '252', '262']
                                      and eventProfileRegionalCode not in ['8009', '8015', '8016', '103', '8019', '8021']
                                      and self.getServiceInfis(serviceId) not in ['B04.053.001.019', 'B04.057.001.030']):
                                    sum = 0
                                # обнуление простых услуг для детских профосмотров
                                elif medicalAidTypeCode in ['232', '252', '262'] and eventEndDate >= QDate(2019, 3, 1) and self.getServiceInfis(serviceId)[:7] not in ['B04.031', 'B04.026']:
                                    price, sum = 0, 0
                                # обнуление стоимости услуг для выполненного этапа профосмотров взрослого населения
                                elif medicalAidTypeCode == '261' and eventProfileRegionalCode in ['8011'] and eventEndDate >= QDate(2019, 5, 1):
                                    if self.isProfCompleted(eventId):
                                        if self.getServiceInfis(serviceId)[:7] not in ['B04.026', 'B04.047']:
                                            price, sum = 0, 0
                                # обнуление стоимости услуг для выполненного этапа взрослой дисп.
                                elif medicalAidTypeCode == '211' and eventProfileRegionalCode in ['8008', '8014']:
                                    if self.isDispCompleted(eventId):
                                        if self.getServiceInfis(serviceId)[:7] not in ['B04.026', 'B04.047']:
                                            price, sum = 0, 0
                                # обнуление стоимости простых услуг для второго этапа взрослой дисп.
                                elif medicalAidTypeCode in ['211'] and eventProfileRegionalCode in ['8009', '8015']:
                                    if self.getServiceInfis(serviceId)[:1] == 'A':
                                        price, sum = 0, 0

                                # обнуление стоимости у услуг терапевта по углубленной диспансеризации
                                elif medicalAidTypeCode == '233' and self.getServiceInfis(serviceId) in ['B04.047.002', 'B04.047.004', 'B04.026.002']:
                                    price, sum = 0, 0
                                elif medicalAidTypeCode == '244' and self.getServiceInfis(serviceId)[:1] == 'A' and eventProfileRegionalCode in ['8020']:
                                    # ТТ 3003 "Выставлять жидкостную цитологию с ценой"
                                    if self.getServiceInfis(serviceId) == "A08.20.017.002":
                                        stmt = """SELECT Action.id
                                        FROM Action
                                        LEFT JOIN ActionType ON ActionType.id = Action.actionType_id
                                        WHERE Action.event_id = {0} AND Action.id <> {1} AND Action.deleted = 0
                                            AND ActionType.deleted = 0 AND ActionType.nomenclativeService_id IS NOT NULL""".format(eventId, actionId)
                                        query = db.query(stmt)
                                        if query.size() > 0:
                                            price, sum = 0, 0
                                    else:
                                        price, sum = 0, 0

                                # В случае проведения мероприятий в рамках профилактических осмотров,
                                # включая диспансеризацию в выходные дни
                                if medicalAidTypeCode in ['211', '261', '233', '244', '232', '252', '262']:
                                    if eventEndDate >= QDate(2026, 2, 1) and price > 0:
                                        actionEndDate = forceDate(record.value('actionEndDate'))
                                        if countWorkDays(actionEndDate, actionEndDate, wpFiveDays) == 0:
                                            price = round(round(price, 2) * 1.03, 2)
                                            if sum > 0:
                                                sum = price
                                    elif QDate(2020, 1, 1) <= eventEndDate < QDate(2026, 2, 1) and sum > 0:
                                        if eventEndDate >= QDate(2025, 1, 1) and medicalAidTypeCode == '244':
                                            #  В репродуктивной применяется только к приёмам в выходной день
                                            actionEndDate = forceDate(record.value('actionEndDate'))
                                            if countWorkDays(actionEndDate, actionEndDate, wpFiveDays) == 0 and "B04" in self.getServiceInfis(serviceId):
                                                price = round(round(price, 2) * 1.03, 2)
                                                sum = price * amount
                                        else:
                                            if countWorkDays(eventEndDate, eventEndDate, wpFiveDays) == 0:
                                                price = round(round(price, 2) * 1.03, 2)
                                                sum = price * amount

                                    # В случае проведения мобильными медицинскими бригадами полного комплекса мероприятий
                                    # в рамках профилактических осмотров, включая диспансеризацию
                                    if QDate(2023, 1, 1) <= eventEndDate < QDate(2025, 2, 1):
                                        value = self.mapEventTypeToTFOMSAccIdent.get(eventTypeId, None)
                                        if value is None:
                                            value = getIdentification('EventType', eventTypeId, 'AccTFOMS', raiseIfNonFound=False)
                                            self.mapEventTypeToTFOMSAccIdent[eventTypeId] = value if value is not None else ''
                                        if value in ['mob']:
                                            price = round(round(price, 2) * 1.2, 2)
                                            sum = price * amount

                            tableAccountItem = db.table('Account_Item')                        
                            accountItem = tableAccountItem.newRecord()
                            accountItem.setValue('master_id',        account.id)
                            accountItem.setValue('serviceDate',      exposeDate)
                            accountItem.setValue('event_id',         eventId)
                            accountItem.setValue('action_id',        actionId)
                            accountItem.setValue('price',            price)
                            accountItem.setValue('unit_id',          unitId)
                            accountItem.setValue('amount',           amount)
                            accountItem.setValue('uet',              uet)
                            accountItem.setValue('sum',              sum)
                            accountItem.setValue('exposedSum',       sum)
                            accountItem.setValue('tariff_id',        tariff.id)
                            accountItem.setValue('service_id',       serviceId)
                            accountItem.setValue('VAT',              tariff.vat)
                            accountItem.setValue('usedCoefficients', usedCoefficients)
                            newId = db.insertRecord(tableAccountItem, accountItem)

                            # если перевыставляем, добавляем ссылку в перевыставленный счет
                            if oldAccId:
                                oldAccountItem = db.getRecord(tableAccountItem, '*', oldAccId)
                                if oldAccountItem:
                                    self.updateDocsPayStatus(oldAccountItem, contractDescr, CPayStatus.exposedBits)
                                    oldAccountItem.setValue('reexposeItem_id', toVariant(newId))
                                    db.updateRecord(tableAccountItem, oldAccountItem)

                            account.totalAmount += amount
                            account.totalUet    += uet
                            account.totalSum    += sum
                            setActionPayStatus(actionId, contractDescr.payStatusMask, CPayStatus.exposedBits)
                            break


    def exposeHospitalBedActionProperty(self, contractDescr, accountFactory, actionPropertyId, reexposableEventIdList):
        db = QtGui.qApp.db
        record = db.getRecord('''ActionProperty
                              INNER JOIN Action ON Action.id = ActionProperty.action_id
                              left join Account_Item ON Account_Item.event_id = Action.event_id and Account_Item.visit_id is null
                              and Account_Item.action_id = Action.id and Account_Item.refuseType_id is not null and Account_Item.reexposeItem_id is null and Account_Item.deleted = 0
                              LEFT JOIN Person ON Person.id = Action.person_id
                              LEFT JOIN ActionProperty_HospitalBed ON ActionProperty_HospitalBed.id = ActionProperty.id
                              LEFT JOIN OrgStructure_HospitalBed   ON OrgStructure_HospitalBed.id = ActionProperty_HospitalBed.value
                              LEFT JOIN rbHospitalBedProfile       ON rbHospitalBedProfile.id = OrgStructure_HospitalBed.profile_id
                              LEFT JOIN Event ON Event.id = Action.event_id
                              LEFT JOIN rbMesSpecification ON rbMesSpecification.id = Event.mesSpecification_id ''',
                              'Event.eventType_id, Event.setDate, Event.execDate, Event.MES_id, Event.client_id, Event.cureMethod_id, Event.result_id, ActionProperty.action_id, Action.event_id, Action.amount, Action.MKB, Person.tariffCategory_id, rbHospitalBedProfile.service_id, rbMesSpecification.level, Account_Item.id as oldAccId',
                              actionPropertyId)
        eventTypeId = forceRef(record.value('eventType_id'))
        cureMethodId = forceRef(record.value('cureMethod_id'))
        resultId    = forceRef(record.value('result_id'))
        mesLevel    = forceInt(record.value('level'))

        tariffList  = contractDescr.tariffByHospitalBedService.get(eventTypeId, None)
        if not tariffList:
            tariffList = contractDescr.tariffByHospitalBedService.get(None, None)
        if tariffList:
            eventId          = forceRef(record.value('event_id'))
            eventBegDate     = forceDate(record.value('setDate'))
            eventEndDate     = forceDate(record.value('execDate'))
            mesId            = forceRef(record.value('MES_id'))
            MKB = forceString(record.value('MKB'))
            tariffCategoryId = forceRef(record.value('tariffCategory_id'))
            actionId     = forceRef(record.value('action_id'))
            serviceId   = forceRef(record.value('service_id'))
            amount = forceDouble(record.value('amount'))
            reexpose = eventId in reexposableEventIdList
            for tariff in tariffList:
                if tariff.serviceId == serviceId and self.isTariffApplicable(tariff, eventId, cureMethodId, resultId, mesLevel, tariffCategoryId, eventEndDate, MKB):
                    if tariff.enableCoefficients:
                        mesDescr = self.getMesDescr(mesId)
                        duration = getEventDuration(eventBegDate, eventEndDate, wpSevenDays, eventTypeId)
                        coefficient, usedCoefficients = self.getCoefficientAndReport(contractDescr, mesDescr, duration, eventEndDate, eventId, actionId=actionId)
                    else:
                        coefficient, usedCoefficients = 1.0, None
                    amount, price, sum = tariff.evalAmountPriceSum(amount, coefficient)
                    uet = amount*tariff.uet if tariff.tariffType == CTariff.ttActionUET else 0
                    clientId = forceRef(record.value('client_id'))
                    
                    oldAccId = forceRef(record.value('oldAccId'))
                    groupAccountType, medicalAidTypeCode, eventProfileRegionalCode = self.getGroupAccountType(eventTypeId)
                    # для группировки счетов по онкологии в стационарах в отдельные реестры
                    if groupAccountType in [1, 7] and eventEndDate >= QDate(2019, 3, 1):
                        if self.isOncology(eventId):
                            groupAccountType = 9 if groupAccountType == 1 else 10

                    account = accountFactory(clientId, eventEndDate, eventId, groupAccountType if QtGui.qApp.defaultKLADR()[:2] == u'23' else None, tariff.batch, reexpose)
                        
                    tableAccountItem = db.table('Account_Item')
                    accountItem = tableAccountItem.newRecord()
                    accountItem.setValue('master_id',        account.id)
                    accountItem.setValue('serviceDate',      eventEndDate)
                    accountItem.setValue('event_id',         eventId)
                    accountItem.setValue('action_id',        actionId)
                    accountItem.setValue('price',            price)
                    accountItem.setValue('unit_id',          tariff.unitId)
                    accountItem.setValue('amount',           amount)
                    accountItem.setValue('uet',              uet)
                    accountItem.setValue('sum',              sum)
                    accountItem.setValue('exposedSum',       sum)
                    accountItem.setValue('tariff_id',        tariff.id)
                    accountItem.setValue('service_id',       serviceId)
                    accountItem.setValue('VAT',              tariff.vat)
                    accountItem.setValue('usedCoefficients', usedCoefficients)
                    newId = db.insertRecord(tableAccountItem, accountItem)
                    
                    # если перевыставляем, добавляем ссылку в перевыставленный счет
                    if oldAccId:
                        oldAccountItem = db.getRecord(tableAccountItem, '*', oldAccId)
                        if oldAccountItem:
                            self.updateDocsPayStatus(oldAccountItem, contractDescr, CPayStatus.exposedBits)
                            oldAccountItem.setValue('reexposeItem_id', toVariant(newId))
                            db.updateRecord(tableAccountItem, oldAccountItem)
                        
                    account.totalAmount += amount
                    account.totalUet    += uet
                    account.totalSum    += sum
                    setActionPayStatus(actionId, contractDescr.payStatusMask, CPayStatus.exposedBits)
                    return


    def exposeVisitsByEventAndServicePair(self, contractDescr, accountFactory, eventId, serviceId):
        db = QtGui.qApp.db
        record = db.getRecord('''Event
                             LEFT JOIN rbMesSpecification ON rbMesSpecification.id = Event.mesSpecification_id''',
                              'Event.eventType_id, Event.setDate, Event.execDate, Event.MES_id, Event.client_id, Event.cureMethod_id, Event.result_id, rbMesSpecification.level',
                             eventId)
        eventTypeId  = forceRef(record.value('eventType_id'))
        eventBegDate = forceDate(record.value('setDate'))
        eventEndDate = forceDate(record.value('execDate'))
        mesId        = forceRef(record.value('MES_id'))
        mesLevel     = forceInt(record.value('level'))
        clientId     = forceRef(record.value('client_id'))
        cureMethodId = forceRef(record.value('cureMethod_id'))
        resultId     = forceRef(record.value('result_id'))

        visits = db.getRecordList('''Visit
                                  INNER JOIN Person ON Person.id = Visit.person_id
                                  INNER JOIN Event ON Event.id = Visit.event_id''',
                                  'Visit.id, Visit.date, Person.tariffCategory_id',
                                  'Visit.deleted=0 AND Visit.event_id=%d AND Visit.service_id=%d AND (Visit.payStatus&%s)=0' % (eventId, serviceId, contractDescr.payStatusMask),
                                  'Visit.date'
                                 )
        if not visits:
            return
        tariffList = contractDescr.tariffCoupleVisits.get((eventTypeId, serviceId), []) + \
                     contractDescr.tariffCoupleVisits.get((eventTypeId, None), []) + \
                     contractDescr.tariffCoupleVisits.get((None, serviceId), []) + \
                     contractDescr.tariffCoupleVisits.get((None, None), [])
        tariffList.sort(key=lambda item:item.id)
        if tariffList:
            # firstVisitDate = forceDate(visits[0].value('date'))
            lastVisitDate  = forceDate(visits[-1].value('date'))
            tariffCategoryId = forceRef(visits[-1].value('tariffCategory_id'))  # ?!
            lastVisitId = forceRef(visits[-1].value('id'))  # ?!
            for tariff in tariffList:
                if self.isTariffApplicable(tariff, eventId, cureMethodId, resultId, mesLevel, tariffCategoryId, lastVisitDate):
                    if tariff.enableCoefficients:
                        mesDescr = self.getMesDescr(mesId)
                        duration = getEventDuration(eventBegDate, eventEndDate, wpSevenDays, eventTypeId)
                        coefficient, usedCoefficients = self.getCoefficientAndReport(contractDescr, mesDescr, duration, eventEndDate, eventId, visitId=lastVisitId)
                    else:
                        coefficient, usedCoefficients = 1.0, None

                    amount, price, sum = tariff.evalAmountPriceSum(len(visits), coefficient)
                    account = accountFactory(clientId, lastVisitDate, eventId, tariff.batch)
                    tableAccountItem = db.table('Account_Item')
                    accountItem = tableAccountItem.newRecord()
                    accountItem.setValue('master_id',        account.id)
                    accountItem.setValue('serviceDate',      lastVisitDate)
                    accountItem.setValue('event_id',         eventId)
                    accountItem.setValue('visit_id',         lastVisitId)
                    accountItem.setValue('price',            price)
                    accountItem.setValue('unit_id',          tariff.unitId)
                    accountItem.setValue('amount',           amount)
                    accountItem.setValue('sum',              sum)
                    accountItem.setValue('exposedSum',       sum)
                    accountItem.setValue('tariff_id',        tariff.id)
                    accountItem.setValue('service_id',       serviceId)
                    accountItem.setValue('VAT',              tariff.vat)
                    accountItem.setValue('usedCoefficients', usedCoefficients)
                    db.insertRecord(tableAccountItem, accountItem)
                    account.totalAmount += amount
                    account.totalSum    += sum
                    for visit in visits:
                        setVisitPayStatus(forceRef(visit.value('id')), contractDescr.payStatusMask, CPayStatus.exposedBits)
                    return


    def exposeCsg23(self, contractDescr, accountFactory, csgId, reexposableEventIdList):

        db = QtGui.qApp.db

        def getOperationCount(eventId, serviceId, eventEndDate):
            tableKSG = db.table('rbService')
            tableMKB = db.table('Diagnosis')
            tableS69 = db.table('soc_spr69')
            tableS82 = db.table('soc_spr82')
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            tableRBService = db.table('rbService').alias('s18')

            table = tableKSG.leftJoin(tableMKB, 'Diagnosis.id = getEventDiagnosis(%d)' % eventId)
            table = table.leftJoin(tableS69, u"""rbService.infis = soc_spr69.ksgkusl 
                    and (soc_spr69.mkb = Diagnosis.MKB or soc_spr69.mkb is null or (soc_spr69.mkb = 'C.' and substr(Diagnosis.MKB, 1, 1) = 'C') 
                    or (soc_spr69.mkb = 'I.' and substr(Diagnosis.MKB, 1, 1) = 'I')
                    or (soc_spr69.mkb = 'C00-C80' and Diagnosis.MKB between 'C00' and 'C80.9')) and soc_spr69.kusl is not null""")
            table = table.leftJoin(tableAction, 'Action.event_id = %d' % eventId)
            table = table.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            table = table.leftJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
            cond = [tableKSG['id'].eq(serviceId),
                    tableAction['deleted'].eq(0),
                    tableAction['status'].eq(2),
                    tableAction['event_id'].eq(eventId),
                    tableRBService['infis'].eq(tableS69['kusl']),
                    "s18.id is not null"
                    ]
            table = table.leftJoin(tableS82, tableS82['CODE'].eq(tableS69['ksgkusl']))
            cond.append(tableS82['DATN'].dateLe(eventEndDate))
            cond.append(db.joinOr([tableS82['DATO'].dateGe(eventEndDate), tableS82['DATO'].isNull()]))
            cond.append(tableS82['CODE'].isNotNull())
            result = db.getCount(table, where=cond)
            return result

        def getCombinedOperationLevel(eventId):
            result = 0
            stmt = u"""select s73.level 
                    from Event e
                    left join Action a on a.event_id = e.id
                    inner join ActionType at on at.id = a.ActionType_id
                    inner join rbService rs on rs.id = at.nomenclativeService_id
                    inner join soc_spr73 s73 on s73.ksgkusl = rs.infis and s73.datn <= e.execDate and (s73.dato >= e.execDate or s73.dato is null)
                    left join rbService rs2 on rs2.infis = s73.ksgkusl2
                    left join ActionType at2 on at2.nomenclativeService_id = rs2.id and at2.deleted = 0
                    left join Action a2 on a2.event_id = e.id and a2.ActionType_id = at2.id and a2.deleted = 0  AND a2.id <> a.id
                    where a.event_id = {aEvent_id} and e.deleted = 0 and a.deleted = 0  
                        and (s73.ksgkusl2 is not null and a2.id is not null)""".format(aEvent_id=eventId)
            query = db.query(stmt)
            if query.first():
                result = forceInt(query.value(0))
            return result

        def getOperationPairedOrgansLevel(eventId):
            result = 0
            stmt = u"""select s73.level
                    from Event e
                    left join Action a on a.event_id = e.id
                    inner join ActionType at on at.id = a.ActionType_id
                    inner join rbService rs on rs.id = at.nomenclativeService_id
                    inner join soc_spr73 s73 on s73.ksgkusl = rs.infis and s73.datn <= e.execDate and (s73.dato >= e.execDate or s73.dato is null) and s73.ksgkusl2 is null
                    left join Action a2 on a2.event_id = e.id and a2.ActionType_id = at.id and a2.deleted = 0 AND a2.id <> a.id
                    where e.id = {aEvent_id} and e.deleted = 0 and a.deleted = 0
                        and (a.amount + ifnull(a2.amount, 0)) > 1""".format(aEvent_id=eventId)
            query = db.query(stmt)
            if query.first():
                result = forceInt(query.value(0))
            return result

        def hasSupt(eventId):
            result = ''
            stmt = u"""SELECT ss.code
        FROM Action A
INNER JOIN ActionType AT ON A.actionType_id = AT.id
LEFT JOIN ActionProperty ap ON ap.action_id = A.id AND ap.deleted = 0
LEFT JOIN ActionPropertyType apt ON ap.type_id = apt.id AND apt.deleted = 0
LEFT JOIN ActionProperty_Integer api ON ap.id = api.id
LEFT JOIN soc_spr80 ss ON ss.id = api.value
WHERE A.event_id = {0} AND A.deleted = 0 AND AT.flatCode  = 'KRIT'
    AND apt.typeName = 'Доп. классиф. критерий'  AND ss.code like 'supt%'
AND NOT EXISTS(SELECT NULL FROM ActionProperty ap2
            LEFT JOIN ActionPropertyType apt2 ON ap2.type_id = apt2.id AND apt2.deleted = 0
            LEFT JOIN ActionProperty_Integer api2 ON ap2.id = api2.id
            LEFT JOIN soc_spr80 ss2 ON ss2.id = api2.value
            WHERE  A.id = ap2.action_id AND ap2.deleted = 0  AND apt2.typeName = 'Доп. классиф. критерий'  AND ss2.code NOT LIKE 'supt%'
            AND (ss2.drugName LIKE '%филграстим%' OR ss2.drugName LIKE '%деносумаб%' OR	ss2.drugName LIKE '%эмпэгфиграстим%'))""".format(eventId)
            query = db.query(stmt)
            if query.first():
                result = forceString(query.value(0))
            return result

        #  проведение тестирования на выявление респираторных вирусных заболеваний (гриппа, новой коронавирусной инфекции COVID-19) в период госпитализации
        def hasTestingCovid(eventId):
            stmt = u"""select ai.id
                    from Account_Item ai
                    left join rbService rs on rs.id = ai.service_id
                    where ai.event_id = {aEvent_id} and ai.deleted = 0
                        and rs.infis in ('A26.30.157.001', 'A26.08.013.003', 'A26.08.013.004', 'A26.08.027.002',
                                         'A26.08.046.002', 'A26.09.060.002', 'A26.09.044.002', 'A26.08.027.010',
                                         'A26.08.046.010', 'A26.09.044.010', 'A26.09.060.010')""".format(aEvent_id=eventId)
            query = db.query(stmt)
            result = query.size()
            return result

        def hasRehabilitation(eventId):
            stmt = u"""select Action.id 
    FROM Action
      LEFT JOIN ActionType at ON at.id = Action.actionType_id 
        AND at.deleted = 0
    where Action.deleted = 0 
      AND Action.event_id = {aEvent_id}
      AND at.flatCode = 'rehabilitation'
      AND Action.status = 2;""".format(aEvent_id=eventId)
            query = db.query(stmt)
            result = query.size()
            return result

        def hasKSLPDetiCancelation(eventId):
            stmt = u"""
            SELECT NULL 
            FROM Event 
            WHERE Event.id = {aEvent_id}
              AND Event.mesSpecification_id = (SELECT id FROM rbMesSpecification ms WHERE ms.code = 'kslp_deti' LIMIT 1);
            """.format(aEvent_id=eventId)
            query = db.query(stmt)
            result = query.size()
            return result

        db = QtGui.qApp.db
        record = db.getRecordEx('''Event_CSG
                                INNER JOIN Event ON Event.id = Event_CSG.master_id
                                INNER JOIN rbService ON rbService.code = Event_CSG.CSGCode
                                LEFT JOIN Action ON Action.eventCSG_id=Event_CSG.id AND Action.deleted=0
                                LEFT JOIN Person ON Person.id = IFNULL(Action.person_id, Event.execPerson_id)
                                LEFT JOIN rbMesSpecification ON rbMesSpecification.id = Event.mesSpecification_id
                                left join Account_Item ON Account_Item.event_id = Event.id and Account_Item.eventCSG_id = Event_CSG.id
                                    and Account_Item.refuseType_id is not null and Account_Item.reexposeItem_id is null and Account_Item.deleted = 0''',
                                '''Event.execDate, Event.cureMethod_id, Event.result_id, Event.eventType_id,
                                 Event.client_id, Event_CSG.CSGCode, Event_CSG.begDate, Event_CSG.endDate, Event_CSG.MKB, 
                                 Person.tariffCategory_id, rbMesSpecification.level, Event.relative_id,
                                 rbService.id AS service_id, Event.id AS event_id, Account_Item.id as oldAccId, Event_CSG.krit, Person.orgStructure_id''',
                                db.table('Event_CSG')['id'].eq(csgId),
                                'Action.id')
        serviceId = forceRef(record.value('service_id'))
        eventTypeId = forceRef(record.value('eventType_id'))
        relative_id = forceInt(record.value('relative_id'))
        oldAccId = forceRef(record.value('oldAccId'))
        tariffList = contractDescr.tariffEventByMES.get((None, serviceId), None)
        usedCoeffDict = {}
        coeff = 0
        interruptReason = None
        interruptCoeff = None
        if tariffList:
            eventId      = forceRef(record.value('event_id'))
            eventEndDate = forceDate(record.value('execDate'))
            reexpose = eventId in reexposableEventIdList
            csgCode      = forceString(record.value('CSGCode'))
            mkbCode      = forceString(record.value('MKB'))
            csgBegDate   = forceDate(record.value('begDate'))
            csgEndDate   = forceDate(record.value('endDate'))
            mesLevel     = forceInt(record.value('level'))
            cureMethodId = forceRef(record.value('cureMethod_id'))
            resultId     = forceRef(record.value('result_id'))
            tariffCategoryId = forceRef(record.value('tariffCategory_id'))
            csgKritId = forceRef(record.value('krit'))
            personOrgStructId = forceRef(record.value('orgStructure_id'))

            for tariff in tariffList:
                if self.isTariffApplicable(tariff, eventId, cureMethodId, resultId, mesLevel, tariffCategoryId, csgEndDate):
                    coefficient, usedCoefficients = 1.0, None
                    price = tariff.price
                    amount = 1.0
                    clientId = forceRef(record.value('client_id'))
                    groupAccountType, medicalAidTypeCode, eventProfileRegionalCode = self.getGroupAccountType(eventTypeId)
                    # для группировки счетов по онкологии в стационарах в отдельные реестры
                    if groupAccountType in [1, 7]:
                        if self.isOncology(eventId):
                            groupAccountType = 9 if groupAccountType == 1 else 10

                    clientRecord = db.getRecord('Client', ['sex', 'birthDate'], clientId) if clientId else None
                    age = 0
                    if clientRecord:
                        clientBirthDate = forceDate(clientRecord.value('birthDate'))
                        age = calcAgeInYears(clientBirthDate, csgBegDate)

                    if medicalAidTypeCode in ('11', '12', '301', '302') and csgCode[3:] in ['st36.013', 'st36.014', 'st36.015'] and QDate(2024, 11, 1) <= eventEndDate < QDate(2026, 1, 1):
                        minDuration = 0
                        amtCode = None
                        if csgKritId:
                            amtCode = forceString(db.translate('soc_spr80', 'id', csgKritId, 'code'))
                        else:
                            stmt = u"""SELECT ss.code
                            FROM Action A
                            INNER JOIN ActionType AT ON A.actionType_id = AT.id
                            LEFT JOIN ActionProperty ap ON ap.action_id = A.id AND ap.deleted = 0
                            LEFT JOIN ActionPropertyType apt ON ap.type_id = apt.id AND apt.deleted = 0
                            LEFT JOIN ActionProperty_Integer api ON ap.id = api.id
                            LEFT JOIN soc_spr80 ss ON ss.id = api.value
                            WHERE A.event_id = {0} AND A.deleted = 0 AND AT.flatCode  = 'KRIT' AND A.begDate >= {1} AND A.endDate <= {2}
                                AND apt.typeName = 'Доп. классиф. критерий'  AND ss.code like 'amt%'""".format(eventId, db.formatDate(csgBegDate), db.formatDate(csgEndDate))
                            query = db.query(stmt)
                            if query.first():
                                amtCode = forceString(query.value(0))
                        if amtCode in ['amt02', 'amt04','amt05','amt07','amt08','amt09','amt10','amt12','amt13','amt14','amt15']:
                            minDuration = 5
                        elif amtCode in ['amt01', 'amt03','amt06','amt11']:
                            minDuration = 10
                        eventWeekProfile = getWeekProfile(forceInt(db.getRecord('EventType', 'weekProfileCode', eventTypeId).value('weekProfileCode')))
                        duration = getEventDuration(csgBegDate, csgEndDate, eventWeekProfile, eventTypeId)
                        if duration < minDuration:
                            if duration >= 3:
                                price = roundMath(price * contractDescr.coefficients[0, 0][u'ПРЕРВДЛ4'][eventEndDate], 2)
                            else:
                                price = roundMath(price * contractDescr.coefficients[0, 0][u'ПРЕРВДЛ3'][eventEndDate], 2)

                    elif csgCode[3:] in ['st02.003', 'st02.004'] and eventEndDate >= QDate(2025, 6, 1):
                        minDuration = 1
                        eventWeekProfile = getWeekProfile(forceInt(db.getRecord('EventType', 'weekProfileCode', eventTypeId).value('weekProfileCode')))
                        duration = getEventDuration(csgBegDate, csgEndDate, eventWeekProfile, eventTypeId)

                        if medicalAidTypeCode in ['11', '12', '301', '302'] and QDate(2026, 2, 1) <= eventEndDate:
                            # Предоставление спального места и питания законному представителю
                            # (дети до 4 лет, дети старше 4 лет при наличии медицинских показаний)
                            if relative_id and age < 18:
                                childCoef = contractDescr.coefficients[0, 0][u'Дети'][eventEndDate]
                                childGemOnkoCoef = contractDescr.coefficients[0, 0][u'ДетиГемОнко'][eventEndDate]
                                # Предоставление спального места и питания законному представителю несовершеннолетних
                                # (детей до 4 лет, детей старше 4 лет при наличии медицинских показаний),
                                # получающих медицинскую помощь по профилю «Детская онкология» и (или) «Гематология»
                                if hasCancerHemaBloodProfile(eventId):
                                    coeff += childGemOnkoCoef
                                    usedCoeffDict['sl002'] = childGemOnkoCoef
                                elif not (hasKSLPDetiCancelation(eventId) > 0):
                                    coeff += childCoef
                                    usedCoeffDict['sl001'] = childCoef

                            # Сложность лечения пациента, связанная с возрастом (лица старше 75 лет)
                            # (в том числе, включая консультацию врача-гериатра)
                            # Кроме случаев госпитализации на геронтологические профильные койки
                            elif age >= 75 and not isGerontologicalKPK(eventId) and csgCode[3:7] != 'st37':
                                seniorCoef = contractDescr.coefficients[0, 0][u'Старше75'][eventEndDate]
                                if hasServiceInEvent(eventId, 'B01.007.001'):
                                    coeff += seniorCoef
                                    usedCoeffDict['sl003'] = seniorCoef

                            # Наличие у пациента тяжелой сопутствующей патологии, осложнений заболеваний, сопутствующих заболеваний, влияющих на сложность лечения пациента
                            if hasSevereMKB(eventId) > 0:
                                severeMKBCoef = contractDescr.coefficients[0, 0][u'ТяжСопМКБ'][eventEndDate]
                                coeff += severeMKBCoef
                                usedCoeffDict['sl005'] = severeMKBCoef

                            combinedOperationLevel = getCombinedOperationLevel(eventId)
                            operationPairedOrgansLevel = getOperationPairedOrgansLevel(eventId)
                            if combinedOperationLevel == 1 or operationPairedOrgansLevel == 1:
                                combinedCoeff = contractDescr.coefficients[0, 0][u'ПарноСочет1'][eventEndDate]
                                coeff += combinedCoeff
                                usedCoeffDict['sl006'] = combinedCoeff
                            elif combinedOperationLevel == 2 or operationPairedOrgansLevel == 2:
                                combinedCoeff = contractDescr.coefficients[0, 0][u'ПарноСочет2'][eventEndDate]
                                coeff += combinedCoeff
                                usedCoeffDict['sl007'] = combinedCoeff
                            elif combinedOperationLevel == 3 or operationPairedOrgansLevel == 3:
                                combinedCoeff = contractDescr.coefficients[0, 0][u'ПарноСочет3'][eventEndDate]
                                coeff += combinedCoeff
                                usedCoeffDict['sl008'] = combinedCoeff
                            elif combinedOperationLevel == 4 or operationPairedOrgansLevel == 4:
                                combinedCoeff = contractDescr.coefficients[0, 0][u'ПарноСочет4'][eventEndDate]
                                coeff += combinedCoeff
                                usedCoeffDict['sl009'] = combinedCoeff
                            elif combinedOperationLevel == 5 or operationPairedOrgansLevel == 5:
                                combinedCoeff = contractDescr.coefficients[0, 0][u'ПарноСочет5'][eventEndDate]
                                coeff += combinedCoeff
                                usedCoeffDict['sl010'] = combinedCoeff

                            # Проведение сопроводительной лекарственной терапии при злокачественных новообразованиях у взрослых
                            # в стационарных условиях в соответствии с клиническими рекомендациями*
                            if age >= 18 and medicalAidTypeCode in ['11'] and (
                                    'st19.084' <= csgCode[3:] <= 'st19.089'
                                    or 'st19.094' <= csgCode[3:] <= 'st19.102'
                                    or 'st19.163' <= csgCode[3:] <= 'st19.181'):
                                supt = hasSupt(eventId)
                                if supt in ['supt01', 'supt07', 'supt08']:
                                    onkoCoef = contractDescr.coefficients[0, 0][u'онкоКС1'][eventEndDate]
                                    coeff += onkoCoef
                                    usedCoeffDict['sl015'] = onkoCoef
                                elif supt in ['supt02', 'supt03', 'supt04', 'supt06']:
                                    onkoCoef = contractDescr.coefficients[0, 0][u'онкоКС2'][eventEndDate]
                                    coeff += onkoCoef
                                    usedCoeffDict['sl016'] = onkoCoef
                                elif supt in ['supt05', 'supt09', 'supt10', 'supt11', 'supt12']:
                                    onkoCoef = contractDescr.coefficients[0, 0][u'онкоКС3'][eventEndDate]
                                    coeff += onkoCoef
                                    usedCoeffDict['sl017'] = onkoCoef

                            # Проведение тестирования на выявление респираторных вирусных заболеваний
                            # (гриппа, новой коронавирусной инфекции COVID-19) в период госпитализации**
                            if csgCode[3:] not in ['st12.012', 'st12.015', 'st12.016', 'st12.017', 'st12.018', 'st12.019'] and hasTestingCovid(eventId) > 0:
                                testingCovidCoef = contractDescr.coefficients[0, 0][u'ТестВир'][eventEndDate]
                                coeff += testingCovidCoef
                                usedCoeffDict['sl014'] = testingCovidCoef

                            # проведение 1 этапа медицинской реабилитации
                            if hasRehabilitation(eventId) > 0:
                                rehabilitationCoef = contractDescr.coefficients[0, 0][u'реабилР'][eventEndDate]
                                coeff += rehabilitationCoef
                                usedCoeffDict['sl011'] = rehabilitationCoef

                        elif medicalAidTypeCode in ['41'] and eventEndDate >= QDate(2025, 6, 1):
                            # Проведение сопроводительной лекарственной терапии при злокачественных новообразованиях у взрослых в условиях дневного стационара в соответствии с клиническими рекомендациями*
                            if age >= 18 and (
                                    'ds19.058' <= csgCode[3:] <= 'ds19.062'
                                    or 'ds19.067' <= csgCode[3:] <= 'ds19.078'
                                    or 'ds19.135' <= csgCode[3:] <= 'ds19.156'):
                                supt = hasSupt(eventId)
                                if supt in ['supt01', 'supt07', 'supt08']:
                                    onkoCoef = contractDescr.coefficients[0, 0][u'онкоДС1'][eventEndDate]
                                    coeff += onkoCoef
                                    usedCoeffDict['sl018'] = onkoCoef
                                elif supt in ['supt02', 'supt03', 'supt04', 'supt06']:
                                    onkoCoef = contractDescr.coefficients[0, 0][u'онкоДС2'][eventEndDate]
                                    coeff += onkoCoef
                                    usedCoeffDict['sl019'] = onkoCoef
                                elif supt in ['supt05', 'supt09', 'supt10', 'supt11', 'supt12']:
                                    onkoCoef = contractDescr.coefficients[0, 0][u'онкоДС3'][eventEndDate]
                                    coeff += onkoCoef
                                    usedCoeffDict['sl020'] = onkoCoef

                        # применяем КСЛП
                        baseTariff = self.getBaseTariff(eventEndDate, medicalAidTypeCode)
                        price = price + roundMath(baseTariff * coeff, 2)

                        ishodOb = isInterruptedCase(eventId)
                        if ishodOb == '108':
                            interruptReason = '1'
                        elif ishodOb in ['102', '202']:
                            interruptReason = '4'
                        elif ishodOb in ['103', '203']:
                            interruptReason = '2'
                        elif ishodOb in ['105', '205', '206']:
                            interruptReason = '6'
                        elif ishodOb == '107':
                            interruptReason = '5'

                        if (minDuration > 1 and duration <= minDuration
                                or (QDate(2023, 2, 1) <= eventEndDate < QDate(2025, 1, 1)
                                    and minDuration == 1 and duration <= 3
                                    and ishodOb in ['103', '203', '105', '205', '107', '207', '108', '208', '110'])
                                or (QDate(2025, 1, 1) <= eventEndDate < QDate(2025, 6, 1)
                                    and minDuration == 1 and duration <= 3
                                    and ishodOb in ['102', '202', '103', '203', '105', '205', '107', '207', '108', '208', '110'])
                                or (eventEndDate >= QDate(2025, 6, 1)
                                    and minDuration == 1 and duration <= 3
                                    and ishodOb in ['102', '202', '103', '203', '104', '105', '205', '107', '207', '108', '208', '110'])):
                            if getOperationCount(eventId, tariff.serviceId, eventEndDate) > 0 or csgCode[3:] == 'st29.007':
                                interruptCoeff = contractDescr.coefficients[0, 0][u'ПРЕРВДЛ3ОПЕР'][eventEndDate]
                                price = roundMath(price * interruptCoeff, 2)
                            else:
                                interruptCoeff = contractDescr.coefficients[0, 0][u'ПРЕРВДЛ3'][eventEndDate]
                                price = roundMath(price * interruptCoeff, 2)
                            if duration <= 3 and interruptReason is None:
                                # длительность <= 3 дня и причина оплаты за прерванный случай ещё не была указана
                                interruptReason = '8'
                        # оплата прерванных случаев свыше 3-х дней
                        elif (duration > minDuration and ishodOb and minDuration > 1
                              or (QDate(2023, 2, 1) <= eventEndDate < QDate(2025, 1, 1)
                                  and minDuration == 1
                                  and ishodOb in ['103', '203', '105', '205', '107', '207', '108', '208', '110'])
                              or (QDate(2025, 1, 1) <= eventEndDate < QDate(2025, 6, 1)
                                  and minDuration == 1
                                  and ishodOb in ['102', '202', '103', '203', '105', '205', '107', '207', '108', '208', '110'])
                              or (eventEndDate >= QDate(2025, 6, 1)
                                  and minDuration == 1
                                  and ishodOb in ['102', '202', '103', '203', '104', '105', '205', '107', '207', '108', '208', '110'])):
                            if getOperationCount(eventId, tariff.serviceId, eventEndDate) > 0 or csgCode[3:] == 'st29.007':
                                interruptCoeff = contractDescr.coefficients[0, 0][u'ПРЕРВДЛ4ОПЕР'][eventEndDate]
                                price = roundMath(price * interruptCoeff, 2)
                            else:
                                interruptCoeff = contractDescr.coefficients[0, 0][u'ПРЕРВДЛ4'][eventEndDate]
                                price = roundMath(price * interruptCoeff, 2)

                    sum = round(price*amount*coefficient, 2)
                    if usedCoeffDict:
                        coeffList = []
                        for c in sorted(usedCoeffDict):
                            coeffList.append('{0}({1});'.format(c, usedCoeffDict[c]))
                            usedCoefficients = ''.join(coeffList)

                    account = accountFactory(clientId, eventEndDate, eventId, groupAccountType if QtGui.qApp.defaultKLADR()[:2] in ['23', '01'] else None, tariff.batch, reexpose, personOrgStructId)
                    tableAccountItem = db.table('Account_Item')
                    accountItem = tableAccountItem.newRecord()
                    accountItem.setValue('master_id',        account.id)
                    accountItem.setValue('serviceDate',      csgEndDate)
                    accountItem.setValue('event_id',         eventId)
                    accountItem.setValue('eventCSG_id',      csgId)
                    accountItem.setValue('price',            price)
                    accountItem.setValue('unit_id',          tariff.unitId)
                    accountItem.setValue('amount',           amount)
                    accountItem.setValue('sum',              sum)
                    accountItem.setValue('exposedSum',       sum)
                    accountItem.setValue('tariff_id',        tariff.id)
                    accountItem.setValue('service_id',       serviceId)
                    accountItem.setValue('VAT',              tariff.vat)
                    accountItem.setValue('usedCoefficients', toVariant(usedCoefficients))
                    if usedCoefficients:
                        accountItem.setValue('usedCoefficientsValue', toVariant(coeff))
                    if interruptReason:
                        accountItem.setValue('interruptReason', toVariant(interruptReason))
                        accountItem.setValue('interruptCoeff', toVariant(interruptCoeff))
                    newId = db.insertRecord(tableAccountItem, accountItem)

                    # если перевыставляем, добавляем ссылку в перевыставленный счет
                    if oldAccId:
                        oldAccountItem = db.getRecord(tableAccountItem, '*', oldAccId)
                        if oldAccountItem:
                            self.updateDocsPayStatus(oldAccountItem, contractDescr, CPayStatus.exposedBits)
                            oldAccountItem.setValue('reexposeItem_id', toVariant(newId))
                            db.updateRecord(tableAccountItem, oldAccountItem)

                    account.totalAmount += amount
                    account.totalSum    += sum
                    setEventCsgPayStatus(csgId, contractDescr.payStatusMask, CPayStatus.exposedBits)
                    return


    def exposeCsg(self, contractDescr, accountFactory, csgId, reexposableEventIdList):
        db = QtGui.qApp.db
        record = db.getRecordEx('Event_CSG'\
                                ' INNER JOIN Event ON Event.id = Event_CSG.master_id'\
                                ' LEFT JOIN EventType ON EventType.id = Event.eventType_id'\
                                ' LEFT JOIN rbMedicalAidType ON rbMedicalAidType.id = EventType.medicalAidType_id'\
                                ' LEFT JOIN Client ON Client.id = Event.client_id'\
                                ' INNER JOIN rbService ON rbService.code = Event_CSG.CSGCode'\
                                ' LEFT JOIN Action ON Action.eventCSG_id=Event_CSG.id AND Action.deleted=0' \
                                ' LEFT JOIN Person ON Person.id = IFNULL(Action.person_id, Event.execPerson_id)'\
                                ' LEFT JOIN rbMesSpecification ON rbMesSpecification.id = Event.mesSpecification_id'\
                                ' LEFT JOIN rbMesSpecification AS CSGSpecification ON CSGSpecification.id = Event_CSG.csgSpecification_id'\
                                ' LEFT JOIN rbResult on rbResult.id = Event.result_id',
                                'Event.cureMethod_id, Event.result_id, Event.eventType_id, Event.client_id, Event_CSG.CSGCode, Event_CSG.begDate, Event_CSG.endDate, '\
                                'Person.tariffCategory_id, Person.orgStructure_id, rbMesSpecification.level, rbService.id AS service_id, '\
                                'Event.id AS event_id, Event.relative_id, EventType.weekProfileCode, CSGSpecification.id as csgSpecificationId, CSGSpecification.level as csgLevel, '\
                                'Client.birthDate, rbMedicalAidType.federalCode as matFedCode, Event.setDate as eventSetDate, Event.execDate as eventExecDate, rbResult.federalCode as resultCode',
                                db.table('Event_CSG')['id'].eq(csgId),
                                'Action.id')
        serviceId = forceRef(record.value('service_id'))
        eventTypeId = forceRef(record.value('eventType_id'))
        tariffList = contractDescr.tariffByCSG.get((eventTypeId, serviceId), None)
        if not tariffList and (contractDescr.prog in ['R61TFOMSNATIVE', 'R01NATIVE']):
            tariffList = contractDescr.tariffByCSG.get((None, serviceId), None)
        if tariffList:
            eventId      = forceRef(record.value('event_id'))
            reexpose = eventId in reexposableEventIdList
            csgCode      = forceString(record.value('CSGCode'))
            csgBegDate   = forceDate(record.value('begDate'))
            csgEndDate   = forceDate(record.value('endDate'))
            mesLevel     = forceInt(record.value('level'))
            csgLevel     = forceInt(record.value('csgLevel'))
            cureMethodId = forceRef(record.value('cureMethod_id'))
            resultId     = forceRef(record.value('result_id'))
            tariffCategoryId = forceRef(record.value('tariffCategory_id'))
            clientId = forceRef(record.value('client_id'))
            relativeId = forceInt(record.value('relative_id'))
            birthDate = forceDate(record.value('birthDate'))
            weekProfileCode = forceInt(record.value('weekProfileCode'))
            matFedCode = forceString(record.value('matFedCode'))
            eventSetDate = forceDate(record.value('eventSetDate'))
            eventExecDate = forceDate(record.value('eventExecDate'))
            resultCode = forceString(record.value('resultCode'))
            for tariff in tariffList:
                if self.isTariffApplicable(tariff, eventId, cureMethodId, resultId, mesLevel, tariffCategoryId, csgEndDate):
                    amount = 1.0
                    price = tariff.price
                    sum = price
                    if True:  # У нас это поле скрыто tariff.enableCoefficients:
                        if contractDescr.prog in ['R61TFOMSNATIVE', 'R01NATIVE']:
                            orgStructureId = forceRef(record.value('orgStructure_id'))
                            csgLevel = csgLevel if forceRef(record.value('csgSpecificationId')) else None
                            omsCode = self.getKODLPU(orgStructureId)
                            price, coeff, usedCoeffDict = evalPriceForRostov(contractDescr, tariff, birthDate, eventSetDate, eventTypeId, eventId, csgBegDate, csgEndDate, csgCode, relativeId, weekProfileCode, matFedCode, csgLevel, resultCode, omsCode)
                            sum = price = round(price, 2)
                            price = tariff.frags[-3][2] if len(tariff.frags) == 3 and omsCode == '4010402' else tariff.price
                            if usedCoeffDict:
                                usedCoefficients = json.dumps(usedCoeffDict, ensure_ascii=False)
                            else:
                                usedCoefficients = None
                        else:
                            duration = getEventDuration(csgBegDate, csgEndDate, wpSevenDays, eventTypeId)
                            csgDescr = self.getCsgDescr(csgCode)
                            coefficient, usedCoefficients = self.getCoefficientAndReport(contractDescr, csgDescr, duration, csgEndDate, eventId, eventCsgId=csgId)
                            sum = round(price * amount * coefficient, 2)
                    else:
                        coefficient, usedCoefficients = 1.0, None

                    groupAccountType, medicalAidTypeCode, eventProfileRegionalCode = self.getGroupAccountType(eventTypeId)
                    if QtGui.qApp.defaultKLADR()[:2] == '01' and groupAccountType in [1, 3]:
                        if self.isOncology(eventId):
                            groupAccountType = 2 if groupAccountType == 1 else 4

                    account = accountFactory(clientId, eventExecDate, eventId, groupAccountType if QtGui.qApp.defaultKLADR()[:2] in ['23', '01'] else None, tariff.batch, reexpose)
                    tableAccountItem = db.table('Account_Item')
                    accountItem = tableAccountItem.newRecord()
                    accountItem.setValue('master_id',        account.id)
                    accountItem.setValue('serviceDate',      csgEndDate)
                    accountItem.setValue('event_id',         eventId)
                    accountItem.setValue('eventCSG_id',      csgId)
                    accountItem.setValue('price',            price)
                    accountItem.setValue('unit_id',          tariff.unitId)
                    accountItem.setValue('amount',           amount)
                    accountItem.setValue('sum',              sum)
                    accountItem.setValue('tariff_id',        tariff.id)
                    accountItem.setValue('service_id',       serviceId)
                    accountItem.setValue('VAT',              tariff.vat)
                    accountItem.setValue('usedCoefficients', usedCoefficients)
                    db.insertRecord(tableAccountItem, accountItem)
                    account.totalAmount += amount
                    account.totalSum    += sum
                    setEventCsgPayStatus(csgId, contractDescr.payStatusMask, CPayStatus.exposedBits)
                    return


    def getSemifinishedMesRefuseTypeId(self, financeId):
        return getRefuseTypeId(u'МЭС не выполнен полностью', True, financeId, True)


    def rejectAccountItemBySemifinishedMes(self, accountItem, financeId):
        if self.semifinishedMesRefuseTypeId is None:
            self.semifinishedMesRefuseTypeId = self.getSemifinishedMesRefuseTypeId(financeId)
        accountItem.setValue('date', QDate().currentDate())
        accountItem.setValue('refuseType_id', self.semifinishedMesRefuseTypeId)
        accountItem.setValue('number', QVariant(u'Проверка МЭС'))


    def isTariffApplicable(self, tariff, eventId, cureMethodId, resultId, mesLevel, tariffCategoryId, date, actualMKB=''):
        if tariff.tariffCategoryId and tariff.tariffCategoryId != tariffCategoryId:
            return False
        if not tariff.dateInRange(date):
            return False
        if tariff.cureMethodId and cureMethodId and tariff.cureMethodId != cureMethodId:
            return False
        if tariff.resultId and tariff.resultId != resultId:
            return False
        if tariff.mesStatus and ( (tariff.mesStatus == 2) != (mesLevel == 2) ):
            return False

        sex = tariff.sex
        ageSelector = tariff.ageSelector
        eventTypeId = tariff.eventTypeId
        if sex or ageSelector or eventTypeId:
            eventRecord = self.getEventRecord(eventId)
            if eventRecord:
                if eventTypeId and eventTypeId != forceRef(eventRecord.value('eventType_id')):
                    return False
                if not date:
                    date = forceDate(eventRecord.value('execDate'))
                if sex or ageSelector:
                    clientId = forceRef(eventRecord.value('client_id'))
                    clientRecord = self.getClientRecord(clientId) if clientId else None
                    if clientRecord:
                        clientSex = forceInt(clientRecord.value('sex'))
                        if sex and sex != clientSex:
                            return False
                        if ageSelector:
                            if tariff.controlPeriod == 1:
                                date = firstYearDay(date)
                            elif tariff.controlPeriod == 2:
                                date = lastYearDay(date)
                            else:
                                pass

                            clientBirthDate = forceDate(clientRecord.value('birthDate'))
                            clientAge = calcAgeTuple(clientBirthDate, date)
                            if not clientAge:
                                clientAge = (0, 0, 0, 0)
                            if not checkAgeSelector(ageSelector, clientAge):
                                return False
                    else:
                        return False
            else:
                return False
        if tariff.MKB:
            if actualMKB:
                MKB = actualMKB
            else:
                eventMKB = self.mapEventIdToMKB.get(eventId, None)
                if eventMKB is None:
                    eventMKB = getEventDiagnosis(eventId)
                    self.mapEventIdToMKB[eventId] = eventMKB
                MKB = eventMKB
            if not tariff.matchMKB(MKB or ''):
                return False
#        if tariff.phaseId and eventId:
#            phaseId = self.mapEventIdToPhaseId.get(eventId, None)
#            if phaseId is None:
#                phaseId = getEventDiseasePhases(eventId)
#                self.mapEventIdToPhaseId[eventId] = phaseId
#            if not tariff.phaseIdEq(phaseId):
#                return False
        return True
   

    def reexpose(self, progressDialog, contractDescr, accountFactory, idList):
        db = QtGui.qApp.db
        qvNull = QVariant()
        tableAccountItem = db.table('Account_Item')
        mapTariffIdToBatch = {}
        for oldId in idList:
            progressDialog.step()
            oldAccountItem = db.getRecord(tableAccountItem, '*', oldId)
            self.updateDocsPayStatus(oldAccountItem, contractDescr, CPayStatus.exposedBits)
            qvDate    = oldAccountItem.value('serviceDate')
            qvEventId = oldAccountItem.value('event_id')
            clientId  = forceRef(db.translate('Event', 'id', qvEventId, 'client_id'))
            tariffId  = forceRef(oldAccountItem.value('tariff_id'))
            batch = mapTariffIdToBatch.get(tariffId)
            if batch is None:
                batch = forceString(db.translate('Contract_Tariff', 'id', tariffId, 'batch'))
                mapTariffIdToBatch[tariffId] = batch
            account = accountFactory(clientId,  forceDate(qvDate), forceRef(qvEventId),  batch,  1)
            newAccountItem = type(oldAccountItem)(oldAccountItem) # это я вывернулся чтобы не писать QtSql.QSqlRecord(oldAccountItem)
            newAccountItem.setValue('id',  qvNull) # или setNull достаточно?
            newAccountItem.setValue('master_id',       account.id)
            newAccountItem.setValue('date', qvNull)
            newAccountItem.setValue('number', qvNull)
            newAccountItem.setValue('refuseType_id', qvNull)
            newAccountItem.setValue('reexposeItem_id', qvNull)
            newId = db.insertRecord(tableAccountItem, newAccountItem)
            oldAccountItem.setValue('reexposeItem_id', newId)
            db.updateRecord(tableAccountItem, oldAccountItem)
            account.totalAmount += forceDouble(oldAccountItem.value('amount'))
            account.totalUet    += forceDouble(oldAccountItem.value('uet'))
            account.totalSum    += forceDouble(oldAccountItem.value('sum'))


    def updateDocsPayStatus(self,  accountItem, contractDescr, bits):
        updateDocsPayStatus(accountItem, contractDescr.payStatusMask, bits)


    def getEventRecord(self, eventId):
        # we need eventType_id, client_id, execDate
        return QtGui.qApp.db.getRecord('Event', ['eventType_id', 'client_id', 'execDate'], eventId)


    def getClientRecord(self, clientId):
        return self.clientRecordCache.get(clientId)


    def getMesDescr(self, mesId):
        descr = self.mapMesIdToDescr.get(mesId)
        if descr is None:
            db = QtGui.qApp.db
            descr = smartDict()
            record = db.getRecord('mes.MES',
                                  ('code',
                                   'minDuration',
                                   'maxDuration',
                                   'avgDuration',
                                   'ksg_id',
                                   'KSGNorm',
                                  ),
                                  mesId)
            if not record:
                record = db.dummyRecord()
            descr.code = forceString(record.value('code'))
            descr.serviceId = forceRef(db.translate('rbService', 'code', descr.code, 'id'))
            descr.minDuration = forceInt(record.value('minDuration'))
            descr.maxDuration = forceInt(record.value('maxDuration'))
            descr.avgDuration = forceDouble(record.value('avgDuration'))
            descr.ksgNorm     = forceInt(record.value('KSGNorm'))
            ksgId = forceRef(record.value('ksg_id'))
            record = db.getRecord('mes.MES_ksg',
                                  ('code',
                                   'type',
                                   'vk',
                                   'managementFactor',
                                  ),
                                  ksgId)
            if not record:
                record = db.dummyRecord()
            descr.ksgCode = forceString(record.value('code'))
            descr.ksgType = forceInt(record.value('type'))
            descr.ksgVk   = forceDouble(record.value('vk'))
            descr.ksgManagementFactor   = forceDouble(record.value('managementFactor'))
            self.mapMesIdToDescr[mesId] = descr
        return descr
        
        
    def getServiceInfis(self, serviceId):
        infis = self.mapServiceIdToInfis.get(serviceId)
        if infis is None:
            infis = forceString(QtGui.qApp.db.translate('rbService', 'id', serviceId, 'infis'))
            self.mapServiceIdToInfis[serviceId] = infis
        return infis

    def serviceHasObr(self, eventId, codeSpec):
        res = self.mapEventObr.get((eventId, codeSpec), None)
        if res is None:
            stmt = u"""select a.id
                        from Event e
                        LEFT JOIN soc_obr u ON u.spec = '{codeSpec}'
                        left join rbService rs on rs.infis in (u.kusl, u.kusl2)
                        left join ActionType at on at.nomenclativeService_id = rs.id
                        left join Action a on a.event_id = e.id and a.actionType_id = at.id
                        where e.id = {aEvent_id} and e.deleted = 0 and a.deleted = 0
                        and rs.infis not in ('B02.001.005', 'B02.001.006', 'B02.031.010', 'B02.047.009', 'B02.047.010')""".format(aEvent_id=eventId, codeSpec=codeSpec)
            query = QtGui.qApp.db.query(stmt)
            res = query.size() > 0
            self.mapEventObr[(eventId, codeSpec)] = res
        return res

    def eventHasReab(self, eventId):
        res = self.mapEventHasReab.get(eventId, None)
        if res is None:
            stmt = u"""select a.id
                        from Action a
                        left join ActionType at on at.id = a.actionType_id
                        left join rbService rs on rs.id = at.nomenclativeService_id
                        where a.id = {aEvent_id} and a.deleted = 0
                        and rs.infis in ('B05.015.002.010', 'B05.015.002.011', 'B05.015.002.012', 'B05.023.002.012',
                           'B05.023.002.013', 'B05.023.002.14', 'B05.050.004.019', 'B05.050.004.020', 'B05.050.004.021',
                           'B05.070.010', 'B05.070.011', 'B05.070.012')""".format(aEvent_id=eventId)
            query = QtGui.qApp.db.query(stmt)
            res = query.size() > 0
            self.mapEventHasReab[eventId] = res
        return res


    def getCsgDescr(self, csgCode):
        descr = self.mapCsgCodeToDescr.get(csgCode)
        if descr is None:
            db = QtGui.qApp.db
            descr = smartDict()
            table = db.table('mes.CSG')
            record = db.getRecordEx(table,
                                  ('minDuration',
                                   'maxDuration',
                                   'avgDuration',
                                  ),
                                  table['code'].eq(csgCode))
            if not record:
                record = db.dummyRecord()
            descr.code = csgCode
            descr.minDuration = forceInt(record.value('minDuration'))
            descr.maxDuration = forceInt(record.value('maxDuration'))
            descr.avgDuration = forceDouble(record.value('avgDuration'))
            self.mapCsgCodeToDescr[csgCode] = descr
        return descr


    def getMesCode(self, mesId):
        return self.getMesDescr(mesId).code


    def getMesService(self, mesId):
        return self.getMesDescr(mesId).serviceId


    def getMesNorm(self, mesId):
        return self.getMesDescr(mesId).ksgNorm


    def getMesAvgDuration(self, mesId):
        return self.getMesDescr(mesId).avgDuration


    def isEventLeavedWithDeath(self, eventId):
        db = QtGui.qApp.db
        table = db.table('vActionLeaved')

        record = db.getRecordEx(table,
                                'id',
                                [ table['event_id'].eq(eventId),
                                  table['deleted'].eq(0),
                                  db.joinOr( [ table['propOutcome'].like(u'%умер%'),
                                               table['propOutcome'].like(u'%смерть%')
                                             ]
                                           )
                                ]
                               )
        return bool(record)


    def getCoefficientAndReport(self,
                                contractDescr,
                                mesOrCsgDescr,
                                duration,
                                date,
                                eventId,
                                eventCsgId=None,
                                actionId=None,
                                visitId=None
                               ):
        mapGroupCodeToCoefficientTypes = {}
        accontingDetails = CCoefficientTypeDescr.getAccountingDetails(date, eventId, eventCsgId, actionId, visitId)
        matter = accontingDetails['matter']
        for coefficientType in contractDescr.coefficients.coefficientTypes[matter]:
            if coefficientType.applicable(accontingDetails):
                groupCodes = coefficientType.usageGroupCodes
                for groupCode in groupCodes:
                    mapGroupCodeToCoefficientTypes.setdefault(groupCode, []).append(coefficientType)

        report = {}
        overallVal = 1.0
        for groupCode, coefficientTypes in mapGroupCodeToCoefficientTypes.iteritems():
            group = contractDescr.coefficients[matter, groupCode]
            values = []
            groupReport = {}
            for coefficientType in coefficientTypes:
                value = group[coefficientType.code][date]
                value = coefficientType.algorithm(value, duration, mesOrCsgDescr.minDuration, mesOrCsgDescr.maxDuration, mesOrCsgDescr.avgDuration)
                values.append(value)
                groupReport[coefficientType.code] = value
            groupOp = group.groupOp
            if groupOp == 0: # сумма
                groupVal = sum(values)
            elif groupOp == 1: # произведение
                groupVal = reduce(lambda r,e: r*e, values, 1.0)
            elif groupOp == 2: # первый подходящий
                # groupVal = reduce(lambda r, e: r if r else e, [], 0.0)
                groupVal = values[0] if values else 0.0
            elif groupOp == 3: # max
                groupVal = max(values) if values else 0.0
            else:
                groupVal = 0.0
            groupVal = round( min(groupVal, group.maxLimit), group.precision)
            groupReport['__all__'] = groupVal
            report[groupCode] = groupReport
            overallVal *= groupVal

        return round(overallVal, contractDescr.valueTariffCoeffPrecision), json.dumps(report, ensure_ascii=False) if report else None


    def eventHasObr(self, eventId):
        result = self.mapEventHasObr.get(eventId, None)
        if result is None:
            db = QtGui.qApp.db
            stmt = u"""SELECT NULL FROM Action a
                       LEFT JOIN ActionType at on at.id = a.actionType_id and at.deleted = 0
                       LEFT JOIN rbService s ON at.nomenclativeService_id = s.id
                       WHERE a.event_id = %s AND a.deleted = 0 AND s.infis regexp '^29[0-9]{2}2[0-9]{6}'""" % eventId
            query = db.query(stmt)
            result = query.size()
            self.mapEventHasObr[eventId] = result
        return result


    def getKODLPU(self, orgStructureId):
        result = self.mapOrgStructureIdToKODLPU.get(orgStructureId, None)
        if result is None:
            db = QtGui.qApp.db
            table = db.table('OrgStructure')
            tmpId = orgStructureId
            bookkeeperCode = ''
            while tmpId:
                record = db.getRecordEx(table, [table['parent_id'], table['bookkeeperCode'], table['tfomsCode']],
                                        table['id'].eq(tmpId))
                bookkeeperCode = forceString(record.value('bookkeeperCode'))
                if not (bookkeeperCode and bookkeeperCode == forceString(record.value('tfomsCode'))):
                    tmpId = forceRef(record.value('parent_id'))
                    continue
                break
            self.mapOrgStructureIdToKODLPU[orgStructureId] = bookkeeperCode
            result = bookkeeperCode

        return result

# =================================================================================

CCircumstance = namedtuple('CCircumstance',
                           (
                            'date',
                            'personId',
                            'specialityId',
                            'specialityCode',
                            'prvsTypeId',
                            'prvsGroup',
                            'important',
                            'additionalServiceCode',
                            'originatedFromAction',
                            'servMade',
                            'incompl',
                            'orgId',
                           )
                          )


def getEventVisitsCircumstances(availabilityCounters, eventId, mesId):
    # получить сведения о визитах, выполенных в рамках выполенния МЭС
    # для случая когда визит оформен как Visit
    # возвращает список кортежей
    #    date,
    #    personId,
    #    specialityId,
    #    specialityCode,
    #    prvsTypeId,
    #    prvsGroup,
    #    important,
    #    additionalServiceCode,
    #    originatedFromAction,
    #    servMade,
    #    orgId,
    result = []
    db = QtGui.qApp.db
    currentOrgId = QtGui.qApp.currentOrgId()
    stmt = u'''
        SELECT DATE(Visit.date)   AS date,
        Visit.person_id           AS person_id,
        Person.speciality_id      AS speciality_id,
        Person.org_id             AS org_id,
        rbSpeciality.regionalCode AS specialityCode,
        mmv.visitType_id          AS prvsTypeIdRequired,
        mVT.id                    AS prvsTypeIdPresent,
        mVT.code NOT LIKE '%%доп' AS important,
        mmv.groupCode             AS prvsGroup,
        mmv.averageQnt            AS averageQnt,
        mmv.additionalServiceCode AS additionalServiceCode,
        Visit.id       AS visit_id,
        (rbVisitType.code != mVT.code) AS visitTypeErr,
        DATE(Visit.date) < DATE(Event.setDate) AS outOfEvent
        FROM Visit
        INNER JOIN Event  ON Event.id = Visit.event_id
        INNER JOIN Client ON Client.id = Event.client_id
        LEFT JOIN Person ON Person.id  = Visit.person_id
        LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id
        LEFT JOIN rbVisitType  ON rbVisitType.id = Visit.visitType_id
        LEFT JOIN mes.mrbSpeciality AS mS   ON mS.regionalCode = rbSpeciality.regionalCode
        LEFT JOIN mes.MES_visit     AS mmv  ON mmv.speciality_id = mS.id AND mmv.deleted = 0
        LEFT JOIN mes.mrbVisitType  AS mVT  ON mVT.id = mmv.visitType_id
        WHERE Visit.deleted = 0
        AND Visit.event_id = %d
        AND mmv.master_id = %d
        AND isSexAndAgeSuitable(Client.sex,
                                Client.birthDate,
                                mmv.sex,
                                -- где ты, mmv.age :(
                                CONCAT( IF(mmv.begAgeUnit BETWEEN 1 AND 4,
                                           CONCAT( IF(mmv.minimumAge='','0',mmv.minimumAge),
                                                   SUBSTR('ДНМГ', mmv.begAgeUnit, 1)
                                                 ),
                                           ''
                                          ),
                                        '-',
                                        IF(mmv.endAgeUnit BETWEEN 1 AND 4,
                                           CONCAT( IF(mmv.maximumAge='','0',mmv.maximumAge),
                                                   SUBSTR('ДНМГ', mmv.endAgeUnit, 1)
                                                 ),
                                           ''
                                          )
                                      ),
                                CASE  mmv.controlPeriod
                                    WHEN 1 -- Конец текущего года
                                        THEN CONCAT( YEAR(Event.execDate),
                                                     '-12-31'
                                                   )
                                    WHEN 2 -- Конец предыдущего года
                                        THEN CONCAT( YEAR(Event.execDate)-1,
                                                     '-12-31'
                                                   )
                                    ELSE -- 0 and fallback
                                        Event.execDate
                                END
                               )
        ORDER BY visitTypeErr, (mVT.code LIKE '%%доп'), mmv.groupCode, Visit.date
    ''' % (eventId, mesId)
    query = db.query(stmt)
    countedVisits = set()
    incompl = 5 # услуга оказана в полном объеме
    while query.next():
        record = query.record()
        visitId = forceRef(record.value('visit_id'))
        if visitId not in countedVisits:
            date = forceDate(record.value('date'))
            personId = forceRef(record.value('person_id'))
            specialityId = forceRef(record.value('speciality_id'))
            orgId = forceRef(record.value('org_id'))
            specialityCode = forceInt(record.value('specialityCode'))
            prvsTypeId = forceInt(record.value('prvsTypeIdRequired'))
            prvsGroup = forceInt(record.value('prvsGroup')) or 1
            important  = forceBool(record.value('important'))
            additionalServiceCode = forceInt(record.value('additionalServiceCode'))
            averageQnt = forceDouble(record.value('averageQnt'))
            outOfEvent = forceBool(record.value('outOfEvent'))
            availabilityKey = (prvsGroup, additionalServiceCode)
            available = availabilityCounters.get(availabilityKey, averageQnt)
            if available > 0:
                availabilityCounters[availabilityKey] = available-1
                if outOfEvent:
                    servMade = 5
                elif orgId != currentOrgId:
                    servMade = 3
#                    elif available <= 0.9999:
#                        servMade = 6
                else:
                    servMade = 1
                result.append(CCircumstance(date,
                                            personId,
                                            specialityId,
                                            specialityCode,
                                            prvsTypeId,
                                            prvsGroup,
                                            important,
                                            additionalServiceCode,
                                            False, # originatedFromAction
                                            servMade,
                                            incompl,
                                            orgId))
                countedVisits.add(visitId)
    return result
    

def getEventActionsCircumstances(availabilityCounters, eventId, mesId, onlyVisitLike):
    # получить сведения о визитах, выполенных в рамках выполенния МЭС
    # для случая когда визит оформен как Action (осмотр)
    # возвращает список кортежей
    #    date,
    #    personId,
    #    specialityId,
    #    specialityCode,
    #    prvsTypeId,
    #    prvsGroup,
    #    important
    #    additionalServiceCode,
    #    originatedFromAction,
    #    servMade,
    #    orgId
    result = []
    db = QtGui.qApp.db
    currentOrgId = QtGui.qApp.currentOrgId()
    stmt = u'''
        SELECT
        Action.id                 AS action_id,
        Action.status             AS actionStatus,
        Action.org_id             AS org_id,
        DATE(COALESCE(Action.endDate, Action.directionDate, Event.execDate)) AS date,
        Person.id                 AS person_id,
        rbSpeciality.id           AS speciality_id,
        IFNULL(NULLIF(mS.regionalCode, ''), rbSpeciality.regionalCode) AS specialityCode,
        mmv.visitType_id          AS prvsTypeIdRequired,
        mVT.id                    AS prvsTypeIdPresent,
        mmv.groupCode             AS prvsGroup,
        mVT.code NOT LIKE '%%доп' AS important,
        mmv.averageQnt            AS averageQnt,
        mmv.additionalServiceCode AS additionalServiceCode,
        mmv.serviceCode           AS serviceCode,
        (IFNULL(rbSpeciality.regionalCode,'') != mS.regionalCode) AS specialityErr,
        IF(mmv.visitType_id=4, 0, 1) AS visitTypeErr,
        DATE(Action.endDate) < DATE(Event.setDate) AS outOfEvent
        FROM Action
        INNER JOIN Event ON Event.id = Action.event_id
        INNER JOIN Client ON Client.id = Event.client_id
        INNER JOIN ActionType ON ActionType.id = Action.actionType_id
        INNER JOIN rbService ON rbService.id = ActionType.nomenclativeService_id
        INNER JOIN mes.MES_visit    AS mmv  ON rbService.code LIKE CONCAT(mmv.serviceCode,'%%') AND mmv.deleted=0
        INNER JOIN mes.mrbVisitType AS mVT  ON mVT.id = mmv.visitType_id
        LEFT JOIN mes.mrbSpeciality AS mS   ON mS.id = mmv.speciality_id
        LEFT JOIN Person ON Person.id  = IFNULL(Action.person_id, Event.execPerson_id)
        LEFT JOIN rbSpeciality              ON IF(Action.person_id IS NULL,
                                                  rbSpeciality.regionalCode = mS.regionalCode,
                                                  rbSpeciality.id = Person.speciality_id
                                                 )
        WHERE Action.deleted = 0
        AND Action.event_id = %(eventId)d
        AND (%(serviceTypeCond)s)
        AND mmv.master_id = %(mesId)d
        AND isSexAndAgeSuitable(Client.sex,
                                Client.birthDate,
                                mmv.sex,
                                -- где ты, mmv.age :(
                                CONCAT( IF(mmv.begAgeUnit BETWEEN 1 AND 4,
                                           CONCAT( IF(mmv.minimumAge='','0',mmv.minimumAge),
                                                   SUBSTR('ДНМГ', mmv.begAgeUnit, 1)
                                                 ),
                                           ''
                                          ),
                                        '-',
                                        IF(mmv.endAgeUnit BETWEEN 1 AND 4,
                                           CONCAT( IF(mmv.maximumAge='','0',mmv.maximumAge),
                                                   SUBSTR('ДНМГ', mmv.endAgeUnit, 1)
                                                 ),
                                           ''
                                          )
                                      ),
                                CASE  mmv.controlPeriod
                                    WHEN 1 -- Конец текущего года
                                        THEN CONCAT( YEAR(Event.execDate),
                                                     '-12-31'
                                                   )
                                    WHEN 2 -- Конец предыдущего года
                                        THEN CONCAT( YEAR(Event.execDate)-1,
                                                     '-12-31'
                                                   )
                                    ELSE -- 0 and fallback
                                        Event.execDate
                                END
                               )
        ORDER BY specialityErr, visitTypeErr, (mVT.code LIKE '%%доп'), mmv.groupCode, Action.endDate
    ''' % {'eventId':eventId,
           'mesId':mesId,
           'serviceTypeCond': (u'ActionType.serviceType in (%d,%d)' % (CActionServiceType.initialInspection, CActionServiceType.reinspection)
                               if onlyVisitLike
                               else '1')
          }

    query = db.query(stmt)
    countedActions = set()
    while query.next():
        record = query.record()
        actionId = forceRef(record.value('action_id'))
        additionalServiceCode = forceInt(record.value('additionalServiceCode'))
        if (actionId, additionalServiceCode) not in countedActions:
            date = forceDate(record.value('date'))
            personId = forceRef(record.value('person_id'))
            specialityId = forceRef(record.value('speciality_id'))
            specialityCode = forceInt(record.value('specialityCode'))
            prvsTypeId = forceInt(record.value('prvsTypeIdRequired'))
            prvsGroup = forceInt(record.value('prvsGroup')) or 1
            important = forceBool(record.value('important'))
    #        serviceCode = forceString(record.value('serviceCode'))
            averageQnt = forceDouble(record.value('averageQnt'))
            outOfEvent = forceBool(record.value('outOfEvent'))
            actionStatus = forceInt(record.value('actionStatus')) # 0-Начато, 1-Ожидание, 2-Закончено, 3-Отменено, 4-Без результата, 5-Назначено, 6-Отказ
            orgId = forceRef(record.value('org_id')) or currentOrgId

            availabilityKey = (prvsGroup, additionalServiceCode)
            available = availabilityCounters.get(availabilityKey, averageQnt)
            incompl = 5 # услуга оказана в полном объеме

            if available > 0:
                availabilityCounters[availabilityKey] = available-1
                if actionStatus in (CActionStatus.finished, CActionStatus.withoutResult): # закончено, без результата
                    if outOfEvent:
                        servMade = 5
                        incompl = 4 # ранее проведённые услуги в пределах установленных сроков
                    elif orgId != currentOrgId:
                        servMade = 3
    #                elif available <= 0.9999:
    #                    servMade = 6
                    else:
                        servMade = 1
                elif actionStatus == CActionStatus.refused: # отказ пациента
                    servMade = 4
                    incompl = 1 # документированный отказ больного
                elif actionStatus == CActionStatus.canceled: # отменено
                    servMade = 4
                    incompl = 3 # прочие причины (умер, переведён в другое отделение и пр.)
                else:
                    if orgId != currentOrgId:
                        servMade = 3
                    else:
                        servMade = 4
                result.append(CCircumstance(date,
                                            personId,
                                            specialityId,
                                            specialityCode,
                                            prvsTypeId,
                                            prvsGroup,
                                            important,
                                            additionalServiceCode,
                                            actionId, # originatedFromAction
                                            servMade,
                                            incompl,
                                            orgId))
                countedActions.add((actionId, additionalServiceCode))
    return result
 


def getInappropriateCircumstances(availabilityCounters, eventId, mesId):
    # получить сведения о позициях (визитах), которые включены в МЭС но НЕ подходят по полу или возрасту
    # для случая когда визит оформен как Action (осмотр)
    # возвращает список кортежей
    #    date,
    #    personId,
    #    specialityId,
    #    specialityCode,
    #    prvsTypeId,
    #    prvsGroup,
    #    important
    #    additionalServiceCode,
    #    originatedFromAction,
    #    servMade,
    #    orgId
    result = []
    db = QtGui.qApp.db
    currentOrgId = QtGui.qApp.currentOrgId()

    stmt = u'''
        SELECT
            mmv.id                    AS mesVisit_id,
            Person.id                 AS person_id,
            IFNULL(rbSubstSpeciality.id, Person.speciality_id) AS speciality_id,
            Person.org_id             AS org_id,
            IFNULL(NULLIF(mS.regionalCode, ''), rbSpeciality.regionalCode) AS specialityCode,
            mmv.visitType_id          AS prvsTypeIdRequired,
            mVT.id                    AS prvsTypeIdPresent,
            mVT.code NOT LIKE '%%доп' AS important,
            mmv.groupCode             AS prvsGroup,
            mmv.averageQnt            AS averageQnt,
            mmv.additionalServiceCode AS additionalServiceCode,
            DATE(Event.execDate)      AS date
        FROM Event
        INNER JOIN Client ON Client.id = Event.client_id
        INNER JOIN Person ON Person.id = Event.execPerson_id
        LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id,

        mes.MES_visit AS mmv
        INNER JOIN mes.mrbVisitType AS mVT  ON mVT.id = mmv.visitType_id
        LEFT JOIN mes.mrbSpeciality AS mS   ON mS.id = mmv.speciality_id
        LEFT JOIN rbSpeciality      AS rbSubstSpeciality ON rbSubstSpeciality.regionalCode = mS.regionalCode
        WHERE Event.id = %(eventId)d
          AND mmv.master_id = %(mesId)d
          AND mmv.deleted = 0
          AND NOT isSexAndAgeSuitable(Client.sex,
                                      Client.birthDate,
                                      mmv.sex,
                                      -- где ты, mmv.age :(
                                      CONCAT( IF(mmv.begAgeUnit BETWEEN 1 AND 4,
                                                 CONCAT( IF(mmv.minimumAge='','0',mmv.minimumAge),
                                                         SUBSTR('ДНМГ', mmv.begAgeUnit, 1)
                                                       ),
                                                 ''
                                                ),
                                              '-',
                                              IF(mmv.endAgeUnit BETWEEN 1 AND 4,
                                                 CONCAT( IF(mmv.maximumAge='','0',mmv.maximumAge),
                                                         SUBSTR('ДНМГ', mmv.endAgeUnit, 1)
                                                       ),
                                                 ''
                                                )
                                            ),
                                      CASE  mmv.controlPeriod
                                          WHEN 1 -- Конец текущего года
                                              THEN CONCAT( YEAR(Event.execDate),
                                                           '-12-31'
                                                         )
                                          WHEN 2 -- Конец предыдущего года
                                              THEN CONCAT( YEAR(Event.execDate)-1,
                                                           '-12-31'
                                                         )
                                          ELSE -- 0 and fallback
                                              Event.execDate
                                      END
                                     )
        ORDER BY mmv.groupCode, mmv.id
    ''' % {'eventId':eventId,
           'mesId':mesId,
          }

    query = db.query(stmt)
    countedVisits = set()
#    countedActions = set()
    while query.next():
        record = query.record()
        mesVisitId = forceRef(record.value('mesVisit_id'))
        if mesVisitId not in countedVisits:
            date = forceDate(record.value('date'))
            personId = forceRef(record.value('person_id'))
            specialityId = forceRef(record.value('speciality_id'))
            specialityCode = forceInt(record.value('specialityCode'))
            prvsTypeId = forceInt(record.value('prvsTypeIdRequired'))
            prvsGroup = forceInt(record.value('prvsGroup')) or 1
            important = forceBool(record.value('important'))
            additionalServiceCode = forceInt(record.value('additionalServiceCode'))
            averageQnt = forceDouble(record.value('averageQnt'))
            orgId = forceRef(record.value('org_id')) or currentOrgId

            availabilityKey = (prvsGroup, additionalServiceCode)
            available = availabilityCounters.get(availabilityKey, averageQnt)
            incompl = 5 # услуга оказана в полном объеме

            if available > 0:
                servMade = 6 # как прошено
                incompl  = 3 # прочие причины (умер, переведён в другое отделение и пр.)
                availabilityCounters[availabilityKey] = available-1
                result.append(CCircumstance(date, personId, specialityId, specialityCode, prvsTypeId, prvsGroup, important, additionalServiceCode, True, servMade, incompl, orgId))
                countedVisits.add(mesVisitId)
    return result


def filterUniqueCircumstances(circumstances, distinctByGroup=False):
    circumstances.sort(key=lambda circumstance: (circumstance.date,
                                                 circumstance.personId,
                                                 circumstance.prvsTypeId,
                                                 circumstance.prvsGroup,
                                                 circumstance.additionalServiceCode,
                                                 circumstance.servMade,
                                                 circumstance.originatedFromAction,
                                                 -circumstance.incompl # сначала - бОльшие значения
                                                ))
    result = []
    producedKeys = []
    for circumstance in circumstances:
        if distinctByGroup:
            key = circumstance.date, circumstance.personId, circumstance.prvsTypeId, circumstance.prvsGroup, circumstance.additionalServiceCode
        else:
            key = circumstance.date, circumstance.personId, circumstance.additionalServiceCode
        if key not in producedKeys:
            producedKeys.append(key)
            result.append(circumstance)
    return result


def getVisitsFromEventWithSameSevrice(eventId, serviceId):
    # получить сведения о визитах, выполенных в рамках одного события и тарифицированных как "визиты по профилю"
    # возвращает список кортежей
    #    date,
    #    personId,
    #    specialityId,
    #    specialityCode,
    #    prvsTypeId,
    #    prvsGroup,
    #    important,
    #    additionalServiceCode,
    #    originatedFromAction,
    #    servMade,
    #    orgId,
    result = []
    db = QtGui.qApp.db
    currentOrgId = QtGui.qApp.currentOrgId()
    stmt = u'''
        SELECT DATE(Visit.date)   AS date,
        Visit.person_id           AS person_id,
        Person.speciality_id      AS speciality_id,
        Person.org_id             AS org_id,
        rbSpeciality.regionalCode AS specialityCode,
        DATE(Visit.date) < DATE(Event.setDate) AS outOfEvent
        FROM Visit
        INNER JOIN Event  ON Event.id = Visit.event_id
        LEFT JOIN Person ON Person.id  = Visit.person_id
        LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id
        LEFT JOIN rbVisitType  ON rbVisitType.id = Visit.visitType_id
        WHERE Visit.deleted = 0
        AND Visit.event_id = %d
        AND Visit.service_id = %d
        ORDER BY Visit.date
    ''' % (eventId, serviceId)
    query = db.query(stmt)
    while query.next():
        record = query.record()
        date = forceDate(record.value('date'))
        personId = forceRef(record.value('person_id'))
        specialityId = forceRef(record.value('speciality_id'))
        orgId = forceRef(record.value('org_id'))
        specialityCode = forceInt(record.value('specialityCode'))
        outOfEvent = forceBool(record.value('outOfEvent'))
        if outOfEvent:
            servMade = 5
        elif orgId != currentOrgId:
            servMade = 3
        else:
            servMade = 1
        result.append(CCircumstance(date,
                                    personId,
                                    specialityId,
                                    specialityCode,
                                    0,        # prvsTypeId
                                    0,        # prvsGroup
                                    True,     # important
                                    0,        # additionalServiceCode
                                    False,    # originatedFromAction
                                    servMade, # 1 servMade
                                    5,        # incompl
                                    orgId
                                   )
                     )
    return result


def getMesAmount(eventId, mesId):
    availabilityCounters = {}
    circumstances  = getEventVisitsCircumstances(availabilityCounters, eventId, mesId)
    circumstances += getEventActionsCircumstances(availabilityCounters, eventId, mesId, True)
    circumstances = filterUniqueCircumstances(circumstances)

    result = 0
    for circumstance in circumstances:
        if circumstance.important and circumstance.servMade == 1:
            result += 1
    return result


def evalPriceForKrasnodarA13(contractDescr,
                             tariff,
                             clientId,
                             eventId,
                             eventTypeId,
                             eventBegDate,
                             eventEndDate,
                             relative_id,
                             serviceInfis,
                             baseTariff=0):
    db = QtGui.qApp.db
    usedCoeffDict = {}

    # поиск выполненных операций, влияющих на выбор ксг
    def getOperationCount(eventId, serviceId, eventEndDate):
        tableKSG = db.table('rbService')
        tableMKB = db.table('Diagnosis')
        tableS69 = db.table('soc_spr69')
        tableS82 = db.table('soc_spr82')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableRBService = db.table('rbService').alias('s18')
        
        table = tableKSG.leftJoin(tableMKB,  'Diagnosis.id = getEventDiagnosis(%d)' % eventId)
        table = table.leftJoin(tableS69,  u"""rbService.infis = soc_spr69.ksgkusl 
                and (soc_spr69.mkb = Diagnosis.MKB or soc_spr69.mkb is null or (soc_spr69.mkb = 'C.' and substr(Diagnosis.MKB, 1, 1) = 'C') 
                or (soc_spr69.mkb = 'I.' and substr(Diagnosis.MKB, 1, 1) = 'I')
                or (soc_spr69.mkb = 'C00-C80' and Diagnosis.MKB between 'C00' and 'C80.9')) and soc_spr69.kusl is not null""")
        table = table.leftJoin(tableAction,  'Action.event_id = %d' % eventId)
        table = table.leftJoin(tableActionType,   tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.leftJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
        cond = [tableKSG['id'].eq(serviceId),
                tableAction['deleted'].eq(0),
                tableAction['status'].eq(2),
                tableAction['event_id'].eq(eventId),
                tableRBService['infis'].eq(tableS69['kusl']),
                "s18.id is not null"
                ]
        table = table.leftJoin(tableS82, tableS82['CODE'].eq(tableS69['ksgkusl']))
        cond.append(tableS82['DATN'].dateLe(eventEndDate))
        cond.append(db.joinOr([tableS82['DATO'].dateGe(eventEndDate), tableS82['DATO'].isNull()]))
        cond.append(tableS82['CODE'].isNotNull())
        result = db.getCount(table, where=cond)
        return result

    def getCombinedOperationLevel(eventId):
        result = 0
        stmt = u"""select s73.level 
                from Event e
                left join Action a on a.event_id = e.id
                inner join ActionType at on at.id = a.ActionType_id
                inner join rbService rs on rs.id = at.nomenclativeService_id
                inner join soc_spr73 s73 on s73.ksgkusl = rs.infis and s73.datn <= e.execDate and (s73.dato >= e.execDate or s73.dato is null)
                left join rbService rs2 on rs2.infis = s73.ksgkusl2
                left join ActionType at2 on at2.nomenclativeService_id = rs2.id and at2.deleted = 0
                left join Action a2 on a2.event_id = e.id and a2.ActionType_id = at2.id and a2.deleted = 0  AND a2.id <> a.id
                where a.event_id = {aEvent_id} and e.deleted = 0 and a.deleted = 0  
                    and (s73.ksgkusl2 is not null and a2.id is not null)""".format(aEvent_id=eventId)
        query = db.query(stmt)
        if query.first():
            result = forceInt(query.value(0))
        return result

    def getOperationPairedOrgansLevel(eventId):
        result = 0
        stmt = u"""select s73.level
                from Event e
                left join Action a on a.event_id = e.id
                inner join ActionType at on at.id = a.ActionType_id
                inner join rbService rs on rs.id = at.nomenclativeService_id
                inner join soc_spr73 s73 on s73.ksgkusl = rs.infis and s73.datn <= e.execDate and (s73.dato >= e.execDate or s73.dato is null) and s73.ksgkusl2 is null
                left join Action a2 on a2.event_id = e.id and a2.ActionType_id = at.id and a2.deleted = 0 AND a2.id <> a.id
                where e.id = {aEvent_id} and e.deleted = 0 and a.deleted = 0
                    and (a.amount + ifnull(a2.amount, 0)) > 1""".format(aEvent_id=eventId)
        query = db.query(stmt)
        if query.first():
            result = forceInt(query.value(0))
        return result

    def hasSupt(eventId):
        result = ''
        stmt = u"""SELECT ss.code
FROM Action A
INNER JOIN ActionType AT ON A.actionType_id = AT.id
LEFT JOIN ActionProperty ap ON ap.action_id = A.id AND ap.deleted = 0
LEFT JOIN ActionPropertyType apt ON ap.type_id = apt.id AND apt.deleted = 0
LEFT JOIN ActionProperty_Integer api ON ap.id = api.id
LEFT JOIN soc_spr80 ss ON ss.id = api.value
WHERE A.event_id = {0} AND A.deleted = 0 AND AT.flatCode  = 'KRIT'
    AND apt.typeName = 'Доп. классиф. критерий'  AND ss.code like 'supt%'
AND NOT EXISTS(SELECT NULL FROM ActionProperty ap2
            LEFT JOIN ActionPropertyType apt2 ON ap2.type_id = apt2.id AND apt2.deleted = 0
            LEFT JOIN ActionProperty_Integer api2 ON ap2.id = api2.id
            LEFT JOIN soc_spr80 ss2 ON ss2.id = api2.value
            WHERE  A.id = ap2.action_id AND ap2.deleted = 0  AND apt2.typeName = 'Доп. классиф. критерий'  AND ss2.code NOT LIKE 'supt%'
            AND (ss2.drugName LIKE '%филграстим%' OR ss2.drugName LIKE '%деносумаб%' OR	ss2.drugName LIKE '%эмпэгфиграстим%'))""".format(eventId)
        query = db.query(stmt)
        if query.first():
            result = forceString(query.value(0))
        return result

    #  проведение тестирования на выявление респираторных вирусных заболеваний (гриппа, новой коронавирусной инфекции COVID-19) в период госпитализации
    def hasTestingCovid(eventId):
        stmt = u"""select ai.id
                from Account_Item ai
                left join rbService rs on rs.id = ai.service_id
                where ai.event_id = {aEvent_id} and ai.deleted = 0
                    and rs.infis in ('A26.30.157.001', 'A26.08.013.003', 'A26.08.013.004', 'A26.08.027.002',
                                     'A26.08.046.002', 'A26.09.060.002', 'A26.09.044.002', 'A26.08.027.010',
                                     'A26.08.046.010', 'A26.09.044.010', 'A26.09.060.010')""".format(aEvent_id=eventId)
        query = db.query(stmt)
        result = query.size()
        return result

    def hasRehabilitation(eventId):
        stmt = u"""select Action.id 
FROM Action
  LEFT JOIN ActionType at ON at.id = Action.actionType_id 
    AND at.deleted = 0
where Action.deleted = 0 
  AND Action.event_id = {aEvent_id}
  AND at.flatCode = 'rehabilitation'
  AND Action.status = 2;""".format(aEvent_id=eventId)
        query = db.query(stmt)
        result = query.size()
        return result

    def hasKSLPDetiCancelation(eventId):
        stmt = u"""
        SELECT NULL 
        FROM Event 
        WHERE Event.id = {aEvent_id}
          AND Event.mesSpecification_id = (SELECT id FROM rbMesSpecification ms WHERE ms.code = 'kslp_deti' LIMIT 1);
        """.format(aEvent_id=eventId)
        query = db.query(stmt)
        result = query.size()
        return result

    price = tariff.price
    
    minDuration = tariff.frags[-2][0] if len(tariff.frags) >= 3 else 3
    eventWeekProfile = getWeekProfile(forceInt(db.getRecord('EventType', 'weekProfileCode', eventTypeId).value('weekProfileCode')))
    duration = getEventDuration(eventBegDate, eventEndDate, eventWeekProfile, eventTypeId)
    VP = getEventAidTypeRegionalCode(eventTypeId)
    
    coeff = 0
    clientRecord = db.getRecord('Client', ['sex', 'birthDate'], clientId) if clientId else None
    age = 0
    if clientRecord:
        clientBirthDate = forceDate(clientRecord.value('birthDate'))
        age = calcAgeInYears(clientBirthDate, eventBegDate)

    # Для круглосуточных стационаров(в т.ч. реабилитационных)
    if VP in ['11', '12', '301', '302']:
        # Предоставление спального места и питания законному представителю
        # (дети до 4 лет, дети старше 4 лет при наличии медицинских показаний)
        if relative_id and age < 18:
            childCoef = contractDescr.coefficients[0, 0][u'Дети'][eventEndDate]
            childGemOnkoCoef = contractDescr.coefficients[0, 0][u'ДетиГемОнко'][eventEndDate]
            # Предоставление спального места и питания законному представителю несовершеннолетних
            # (детей до 4 лет, детей старше 4 лет при наличии медицинских показаний),
            # получающих медицинскую помощь по профилю «Детская онкология» и (или) «Гематология»
            if hasCancerHemaBloodProfile(eventId):
                coeff += childGemOnkoCoef
                if eventEndDate < QDate(2026, 2, 1):
                    usedCoeffDict['2'] = childGemOnkoCoef
                else:
                    usedCoeffDict['sl002'] = childGemOnkoCoef
            elif eventEndDate < QDate(2025, 1, 1) or not (hasKSLPDetiCancelation(eventId) > 0 and eventEndDate >= QDate(2025, 1, 1)):
                coeff += childCoef
                if eventEndDate < QDate(2026, 2, 1):
                    usedCoeffDict['1'] = childCoef
                else:
                    usedCoeffDict['sl001'] = childCoef
        # Сложность лечения пациента, связанная с возрастом (лица старше 75 лет)
        # (в том числе, включая консультацию врача-гериатра)
        # Кроме случаев госпитализации на геронтологические профильные койки
        elif age >= 75 and not isGerontologicalKPK(eventId) and serviceInfis[3:7] != 'st37':
            seniorCoef = contractDescr.coefficients[0, 0][u'Старше75'][eventEndDate]
            if hasServiceInEvent(eventId, 'B01.007.001'):
                coeff += seniorCoef
                if eventEndDate < QDate(2026, 2, 1):
                    usedCoeffDict['3'] = seniorCoef
                else:
                    usedCoeffDict['sl003'] = seniorCoef

        # Наличие у пациента тяжелой сопутствующей патологии, осложнений заболеваний, сопутствующих заболеваний, влияющих на сложность лечения пациента
        if hasSevereMKB(eventId) > 0:
            severeMKBCoef = contractDescr.coefficients[0, 0][u'ТяжСопМКБ'][eventEndDate]
            coeff += severeMKBCoef
            if eventEndDate < QDate(2026, 2, 1):
                usedCoeffDict['5'] = severeMKBCoef
            else:
                usedCoeffDict['sl005'] = severeMKBCoef

        combinedOperationLevel = getCombinedOperationLevel(eventId)
        operationPairedOrgansLevel = getOperationPairedOrgansLevel(eventId)
        if combinedOperationLevel == 1 or operationPairedOrgansLevel == 1:
            combinedCoeff = contractDescr.coefficients[0, 0][u'ПарноСочет1'][eventEndDate]
            coeff += combinedCoeff
            if eventEndDate < QDate(2026, 2, 1):
                usedCoeffDict['6' if eventEndDate >= QDate(2024, 6, 4) else '9'] = combinedCoeff
            else:
                usedCoeffDict['sl006'] = combinedCoeff
        elif combinedOperationLevel == 2 or operationPairedOrgansLevel == 2:
            combinedCoeff = contractDescr.coefficients[0, 0][u'ПарноСочет2'][eventEndDate]
            coeff += combinedCoeff
            if eventEndDate < QDate(2026, 2, 1):
                usedCoeffDict['7' if eventEndDate >= QDate(2024, 6, 4) else '10'] = combinedCoeff
            else:
                usedCoeffDict['sl007'] = combinedCoeff
        elif combinedOperationLevel == 3 or operationPairedOrgansLevel == 3:
            combinedCoeff = contractDescr.coefficients[0, 0][u'ПарноСочет3'][eventEndDate]
            coeff += combinedCoeff
            if eventEndDate < QDate(2026, 2, 1):
                usedCoeffDict['8' if eventEndDate >= QDate(2024, 6, 4) else '11'] = combinedCoeff
            else:
                usedCoeffDict['sl008'] = combinedCoeff
        elif combinedOperationLevel == 4 or operationPairedOrgansLevel == 4:
            combinedCoeff = contractDescr.coefficients[0, 0][u'ПарноСочет4'][eventEndDate]
            coeff += combinedCoeff
            if eventEndDate < QDate(2026, 2, 1):
                usedCoeffDict['9' if eventEndDate >= QDate(2024, 6, 4) else '12'] = combinedCoeff
            else:
                usedCoeffDict['sl009'] = combinedCoeff
        elif combinedOperationLevel == 5 or operationPairedOrgansLevel == 5:
            combinedCoeff = contractDescr.coefficients[0, 0][u'ПарноСочет5'][eventEndDate]
            coeff += combinedCoeff
            if eventEndDate < QDate(2026, 2, 1):
                usedCoeffDict['10' if eventEndDate >= QDate(2024, 6, 4) else '13'] = combinedCoeff
            else:
                usedCoeffDict['sl010'] = combinedCoeff

        # Проведение сопроводительной лекарственной терапии при злокачественных новообразованиях у взрослых
        # в стационарных условиях в соответствии с клиническими рекомендациями*
        if eventEndDate >= QDate(2023, 2, 1) and eventEndDate < QDate(2024, 1, 1) and age >= 18 and VP in ['11'] and (
                'st19.084' <= serviceInfis[3:] <= 'st19.089'
                or 'st19.094' <= serviceInfis[3:] <= 'st19.102'
                or 'st19.125' <= serviceInfis[3:] <= 'st19.143') and hasSupt(eventId):
            onkoCoef = contractDescr.coefficients[0, 0][u'онкоКС'][eventEndDate]
            coeff += onkoCoef
            usedCoeffDict['12'] = onkoCoef
        elif eventEndDate >= QDate(2024, 2, 1) and eventEndDate < QDate(2024, 6, 4) and age >= 18 and VP in ['11'] and (
                'st19.084' <= serviceInfis[3:] <= 'st19.089'
                or 'st19.094' <= serviceInfis[3:] <= 'st19.102'
                or 'st19.144' <= serviceInfis[3:] <= 'st19.162') and hasSupt(eventId):
            onkoCoef = contractDescr.coefficients[0, 0][u'онкоКС'][eventEndDate]
            coeff += onkoCoef
            usedCoeffDict['7'] = onkoCoef
        elif QDate(2024, 6, 4) <= eventEndDate < QDate(2025, 1, 1) and age >= 18 and VP in ['11'] and (
                'st19.084' <= serviceInfis[3:] <= 'st19.089'
                or 'st19.094' <= serviceInfis[3:] <= 'st19.102'
                or 'st19.144' <= serviceInfis[3:] <= 'st19.162'):
            supt = hasSupt(eventId)
            if supt in ['supt01', 'supt07', 'supt08']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоКС1'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['15'] = onkoCoef
            elif supt in ['supt02', 'supt03', 'supt04', 'supt06']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоКС2'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['16'] = onkoCoef
            elif supt in ['supt05', 'supt09', 'supt10', 'supt11', 'supt12']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоКС3'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['17'] = onkoCoef
        elif QDate(2025, 1, 1) <= eventEndDate and age >= 18 and VP in ['11'] and (
                'st19.084' <= serviceInfis[3:] <= 'st19.089'
                or 'st19.094' <= serviceInfis[3:] <= 'st19.102'
                or 'st19.163' <= serviceInfis[3:] <= 'st19.181'):
            supt = hasSupt(eventId)
            if supt in ['supt01', 'supt07', 'supt08']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоКС1'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['15'] = onkoCoef
            elif supt in ['supt02', 'supt03', 'supt04', 'supt06']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоКС2'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['16'] = onkoCoef
            elif supt in ['supt05', 'supt09', 'supt10', 'supt11', 'supt12']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоКС3'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['17'] = onkoCoef
        elif QDate(2026, 2, 1) <= eventEndDate and age >= 18 and VP in ['11'] and (
                'st19.084' <= serviceInfis[3:] <= 'st19.089'
                or 'st19.094' <= serviceInfis[3:] <= 'st19.102'
                or 'st19.163' <= serviceInfis[3:] <= 'st19.181'):
            supt = hasSupt(eventId)
            if supt in ['supt01', 'supt07', 'supt08']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоКС1'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['sl015'] = onkoCoef
            elif supt in ['supt02', 'supt03', 'supt04', 'supt06']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоКС2'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['sl016'] = onkoCoef
            elif supt in ['supt05', 'supt09', 'supt10', 'supt11', 'supt12']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоКС3'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['sl017'] = onkoCoef

        # Проведение тестирования на выявление респираторных вирусных заболеваний
        # (гриппа, новой коронавирусной инфекции COVID-19) в период госпитализации**
        if eventEndDate >= QDate(2023, 2, 1) and serviceInfis[3:] not in ['st12.012', 'st12.015', 'st12.016',
                                                                          'st12.017', 'st12.018', 'st12.019'] and hasTestingCovid(eventId) > 0:
            testingCovidCoef = contractDescr.coefficients[0, 0][u'ТестВир'][eventEndDate]
            coeff += testingCovidCoef
            if eventEndDate < QDate(2026, 2, 1):
                usedCoeffDict['14'] = testingCovidCoef
            else:
                usedCoeffDict['sl014'] = testingCovidCoef

        # проведение 1 этапа медицинской реабилитации
        if eventEndDate >= QDate(2025, 1, 1) and hasRehabilitation(eventId) > 0:
            rehabilitationCoef = contractDescr.coefficients[0, 0][u'реабилР'][eventEndDate]
            coeff += rehabilitationCoef
            if eventEndDate < QDate(2026, 2, 1):
                usedCoeffDict['11'] = rehabilitationCoef
            else:
                usedCoeffDict['sl011'] = rehabilitationCoef

    elif VP in ['41']:
        # Проведение сопроводительной лекарственной терапии при злокачественных новообразованиях у взрослых в условиях дневного стационара в соответствии с клиническими рекомендациями*
        if eventEndDate >= QDate(2023, 2, 1) and eventEndDate < QDate(2024, 1, 1) and age >= 18 and (
                'ds19.058' <= serviceInfis[3:] <= 'ds19.062'
                or 'ds19.067' <= serviceInfis[3:] <= 'ds19.078'
                or 'ds19.078' <= serviceInfis[3:] <= 'ds19.115') and hasSupt(eventId):
            onkoCoef = contractDescr.coefficients[0, 0][u'онкоДС'][eventEndDate]
            coeff += onkoCoef
            usedCoeffDict['13'] = onkoCoef
        elif eventEndDate >= QDate(2024, 2, 1) and eventEndDate < QDate(2024, 6, 4) and age >= 18 and (
                'ds19.058' <= serviceInfis[3:] <= 'ds19.062'
                or 'ds19.067' <= serviceInfis[3:] <= 'ds19.078'
                or 'ds19.116' <= serviceInfis[3:] <= 'ds19.134') and hasSupt(eventId):
            onkoCoef = contractDescr.coefficients[0, 0][u'онкоДС'][eventEndDate]
            coeff += onkoCoef
            usedCoeffDict['8'] = onkoCoef
        elif QDate(2024, 6, 4) <= eventEndDate < QDate(2025, 1, 1) and age >= 18 and (
                'ds19.058' <= serviceInfis[3:] <= 'ds19.062'
                or 'ds19.067' <= serviceInfis[3:] <= 'ds19.078'
                or 'ds19.116' <= serviceInfis[3:] <= 'ds19.134'):
            supt = hasSupt(eventId)
            if supt in ['supt01', 'supt07', 'supt08']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоДС1'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['18'] = onkoCoef
            elif supt in ['supt02', 'supt03', 'supt04', 'supt06']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоДС2'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['19'] = onkoCoef
            elif supt in ['supt05', 'supt09', 'supt10', 'supt11', 'supt12']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоДС3'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['20'] = onkoCoef
        elif QDate(2025, 1, 1) <= eventEndDate and age >= 18 and (
                'ds19.058' <= serviceInfis[3:] <= 'ds19.062'
                or 'ds19.067' <= serviceInfis[3:] <= 'ds19.078'
                or 'ds19.135' <= serviceInfis[3:] <= 'ds19.156'):
            supt = hasSupt(eventId)
            if supt in ['supt01', 'supt07', 'supt08']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоДС1'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['18'] = onkoCoef
            elif supt in ['supt02', 'supt03', 'supt04', 'supt06']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоДС2'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['19'] = onkoCoef
            elif supt in ['supt05', 'supt09', 'supt10', 'supt11', 'supt12']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоДС3'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['20'] = onkoCoef
        elif QDate(2026, 2, 1) <= eventEndDate and age >= 18 and (
                'ds19.058' <= serviceInfis[3:] <= 'ds19.062'
                or 'ds19.067' <= serviceInfis[3:] <= 'ds19.078'
                or 'ds19.135' <= serviceInfis[3:] <= 'ds19.156'):
            supt = hasSupt(eventId)
            if supt in ['supt01', 'supt07', 'supt08']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоДС1'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['sl018'] = onkoCoef
            elif supt in ['supt02', 'supt03', 'supt04', 'supt06']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоДС2'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['sl019'] = onkoCoef
            elif supt in ['supt05', 'supt09', 'supt10', 'supt11', 'supt12']:
                onkoCoef = contractDescr.coefficients[0, 0][u'онкоДС3'][eventEndDate]
                coeff += onkoCoef
                usedCoeffDict['sl020'] = onkoCoef

    # применяем КСЛП
    price = price + roundMath(baseTariff * coeff, 2)

    ishodOb = isInterruptedCase(eventId)
    interruptReason = None
    interruptCoeff = None
    if ishodOb == '108':
        interruptReason = '1'
    elif ishodOb in ['102', '202']:
        interruptReason = '4'
    elif ishodOb in ['103', '203']:
        interruptReason = '2'
    elif ishodOb in ['105', '205', '206']:
        interruptReason = '6'
    elif ishodOb == '107':
        interruptReason = '5'
    # для сверхкоротких случаев лечения (применяется для стационаров всех типов)
    if (minDuration > 1 and duration <= minDuration
            or (QDate(2023, 2, 1) <= eventEndDate < QDate(2025, 1, 1)
                and minDuration == 1 and duration <= 3
                and ishodOb in ['103', '203', '105', '205', '107', '207', '108', '208', '110'])
            or (QDate(2025, 1, 1) <= eventEndDate < QDate(2025, 6, 1)
                and minDuration == 1 and duration <= 3
                and ishodOb in ['102', '202','103', '203', '105', '205', '107', '207', '108', '208', '110'])
            or (eventEndDate >= QDate(2025, 6, 1)
                and minDuration == 1 and duration <= 3
                and ishodOb in ['102', '202', '103', '203', '104', '105', '205', '107', '207', '108', '208', '110'])):
        if getOperationCount(eventId, tariff.serviceId, eventEndDate) > 0 or serviceInfis[3:] == 'st29.007':
            interruptCoeff = contractDescr.coefficients[0, 0][u'ПРЕРВДЛ3ОПЕР'][eventEndDate]
            price = roundMath(price * interruptCoeff, 2)
        else:
            interruptCoeff = contractDescr.coefficients[0, 0][u'ПРЕРВДЛ3'][eventEndDate]
            price = roundMath(price * interruptCoeff, 2)
        if duration <= 3 and interruptReason is None:
            # длительность <= 3 дня и причина оплаты за прерванный случай ещё не была указана
            interruptReason = '8'
    # оплата прерванных случаев свыше 3-х дней
    elif (duration > minDuration and ishodOb and minDuration > 1
          or (QDate(2023, 2, 1) <= eventEndDate < QDate(2025, 1, 1)
              and minDuration == 1
              and ishodOb in ['103', '203', '105', '205', '107', '207', '108', '208', '110'])
          or (QDate(2025, 1, 1) <= eventEndDate < QDate(2025, 6, 1)
              and minDuration == 1
              and ishodOb in ['102', '202','103', '203', '105', '205', '107', '207', '108', '208', '110'])
          or (eventEndDate >= QDate(2025, 6, 1)
              and minDuration == 1
              and ishodOb in ['102', '202', '103', '203', '104', '105', '205', '107', '207', '108', '208', '110'])):
        if getOperationCount(eventId, tariff.serviceId, eventEndDate) > 0 or serviceInfis[3:] == 'st29.007':
            interruptCoeff = contractDescr.coefficients[0, 0][u'ПРЕРВДЛ4ОПЕР'][eventEndDate]
            price = roundMath(price * interruptCoeff, 2)
        else:
            interruptCoeff = contractDescr.coefficients[0, 0][u'ПРЕРВДЛ4'][eventEndDate]
            price = roundMath(price * interruptCoeff, 2)

    return price, coeff, usedCoeffDict, interruptReason, interruptCoeff
    

def evalPriceForMurmansk2015Hospital(contractDescr,
                                     tariff,
                                     eventId,
                                     eventTypeId,
                                     eventBegDate,
                                     eventEndDate,
                                     mesId,
                                     shortHospitalisation,
                                     level,  # 0:прерван,1:частично,2:полностью
                                     mesDescr = None
                                    ):
                                        
    
    def getMesDescr(mesId):
        db = QtGui.qApp.db
        descr = smartDict()
        record = db.getRecord('mes.MES',
                              ('code',
                               'minDuration',
                               'maxDuration',
                               'avgDuration',
                               'ksg_id',
                               'KSGNorm',
                              ),
                              mesId)
        if not record:
            record = db.dummyRecord()
        descr.code = forceString(record.value('code'))
        descr.serviceId = forceRef(db.translate('rbService', 'code', descr.code, 'id'))
        descr.minDuration = forceInt(record.value('minDuration'))
        descr.maxDuration = forceInt(record.value('maxDuration'))
        descr.avgDuration = forceDouble(record.value('avgDuration'))
        descr.ksgNorm     = forceInt(record.value('KSGNorm'))
        ksgId = forceRef(record.value('ksg_id'))
        record = db.getRecord('mes.MES_ksg',
                              ('code',
                               'type',
                               'vk',
                               'managementFactor',
                              ),
                              ksgId)
        if not record:
            record = db.dummyRecord()
        descr.ksgCode = forceString(record.value('code'))
        descr.ksgType = forceInt(record.value('type'))
        descr.ksgVk   = forceDouble(record.value('vk'))
        descr.ksgManagementFactor   = forceDouble(record.value('managementFactor'))
        return descr
    
    def isEventLeavedWithDeath(eventId):
        db = QtGui.qApp.db
        table = db.table('vActionLeaved')

        record = db.getRecordEx(table,
                                'id',
                                [ table['event_id'].eq(eventId),
                                  table['deleted'].eq(0),
                                  db.joinOr( [ table['propOutcome'].like(u'%умер%'),
                                               table['propOutcome'].like(u'%смерть%')
                                             ]
                                           )
                                ]
                               )
        return bool(record)

    # 0006322: Мурманск. Новые правила тарификации Стационаров на 2015 г.
    #- Стоимость одного случая лечения (применяется по-умолчанию для всех случаев)
    #  рассчитывается по формуле:
    #
    #  SКСГсл = БС × Кзатр × Купр × КурСтац
    #
    #  где БС - базовая ставка (Цена тарифа в договоре),
    #      Кзатр - весовой коэффициент (поле vk в MES_ksg),
    #      Купр - управленческий коэффициент (поле managementFactor в MES_ksg),
    #      КурСтац - коэффициент Стационара (поле regionalTariffRegulationFactor в Contract)

    duration = getEventDuration(eventBegDate, eventEndDate, wpSevenDays, eventTypeId)
    
    if not mesDescr:
        mesDescr = getMesDescr(mesId)
    
    price = tariff.price * mesDescr.ksgVk * mesDescr.ksgManagementFactor * contractDescr.regionalTariffRegulationFactor

    #- Если длительность события < minDuration МЭС (кроме
    #  событий со свойством действия Исход госпитализации - умер
    #  и МЭС, имеющих КСГ с типом 3 Хир.)
    #
    #- Если длительность события < avgDuration МЭС
    #
    #- Если длительность события меньше суток и свойство действия Исход госпитализации - умер
    #  Тогда расчет по формуле:
    #
    #  SКСГсл = БС × Кзатр × Купр × КурСтац × (Длф / Длср)
    #  где Длф - фактическая длительность события, Длср - avgDuration МЭС

    isDeath = isEventLeavedWithDeath(eventId)
    if (    duration < mesDescr.minDuration and not ( isDeath or mesDescr.ksgType == 3 )
         or (level == 0 and duration < mesDescr.avgDuration)
         or shortHospitalisation and isDeath
       ):
        price *= max(1, duration)/mesDescr.avgDuration if mesDescr.avgDuration>0 else 0.0
    #
    #- Если длительность события > avgDuration МЭС в 2 раза.
    #  Тогда расчет по формуле:
    #
    #  SКСГсл = БС × Кзатр × Купр × КурСтац × (1 + (Длф – Длср) / Длср × 0,35)
    #
    elif ( duration > mesDescr.avgDuration * 2
         ):
        if mesDescr.avgDuration>0:
            price *= (1.0 + (duration-mesDescr.avgDuration)/mesDescr.avgDuration * 0.35)
        else:
            price = 0.0

    #Также необходимо сделать поле в Договоре "Поправочный коэффициент".
    #Итоговая стоимость случая лечения будет рассчитываться так:
    #
    #  SКСГсл = SКСГсл × Кпопр. Если Кпопр=0, тогда Итоговая стоимость случая лечения = SКСГсл.

    return price


def evalPriceForRostov(contractDescr, tariff, birthDate, eventSetDate, eventTypeId, eventId, csgBegDate, csgEndDate, csgCode, relativeId, weekProfileCode, matFedCode, csgLevel, resultCode, omsCode):

    def hasCrit(eventId, critCode):
        stmt = u"""SELECT AT.code
                        FROM Action A
                        INNER JOIN ActionType AT ON A.actionType_id = AT.id
                        WHERE A.event_id = {0} AND A.deleted = 0
                            AND AT.flatCode  = 'CRIT'
                            AND AT.code like '{1}%'""".format(eventId, critCode)
        query = db.query(stmt)
        result = query.size()
        return result

    def hasSevereMKB(eventId):
        stmt = u"""select dc.id
                from Diagnostic dc
                left join Event e on e.id = dc.event_id
                Left join Diagnosis ds on ds.id = dc.diagnosis_id
                left join soc_severeMKB s on ds.MKB like concat(s.mkb, '%')
                where dc.event_id = {eventId}
                    AND dc.diagnosisType_id IN (SELECT id FROM rbDiagnosisType WHERE code in ('3', '9'))
                    AND dc.deleted = 0
                    AND s.begDate <= e.execDate
                    AND (s.endDate is null OR s.endDate >= e.execDate)
                """.format(eventId=eventId)
        query = db.query(stmt)
        result = query.size()
        return result

    def getCombinedOperationLevel(eventId, begDate, endDate):
        result = 0
        stmt = u"""select co.level 
                from Event e
                left join Action a on a.event_id = e.id and DATE(a.endDate) between {begDate} and {endDate}
                inner join ActionType at on at.id = a.ActionType_id
                inner join rbService rs on rs.id = at.nomenclativeService_id
                inner join soc_combinedOperations co on co.code = rs.infis and co.begDate <= e.execDate
                                        and (co.endDate >= e.execDate or co.endDate is null)
                left join rbService rs2 on rs2.infis = co.code2
                left join ActionType at2 on at2.nomenclativeService_id = rs2.id and at2.deleted = 0
                left join Action a2 on a2.event_id = e.id and a2.ActionType_id = at2.id and a2.deleted = 0  AND a2.id <> a.id 
                                        and DATE(a2.endDate) between {begDate} and {endDate}
                where a.event_id = {eventId} and e.deleted = 0 and a.deleted = 0  
                    and (co.code2 is not null and a2.id is not null)""".format(eventId=eventId, begDate=db.formatDate(begDate), endDate=db.formatDate(endDate))
        query = db.query(stmt)
        if query.first():
            result = forceInt(query.value(0))
        return result

    def getOperationPairedOrgansLevel(eventId, begDate, endDate):
        result = 0
        stmt = u"""select co.level
                from Event e
                left join Action a on a.event_id = e.id and DATE(a.endDate) between {begDate} and {endDate}
                inner join ActionType at on at.id = a.ActionType_id
                inner join rbService rs on rs.id = at.nomenclativeService_id
                inner join soc_combinedOperations co on co.code = rs.infis and co.begDate <= e.execDate
                        and (co.endDate >= e.execDate or co.endDate is null) and co.code2 is null
                left join Action a2 on a2.event_id = e.id and a2.ActionType_id = at.id and a2.deleted = 0  AND a2.id <> a.id
                                 and DATE(a.endDate) between {begDate} and {endDate}
                where e.id = {eventId} and e.deleted = 0 and a.deleted = 0
                    and (a.amount + ifnull(a2.amount, 0)) > 1""".format(eventId=eventId, begDate=db.formatDate(begDate), endDate=db.formatDate(endDate))
        query = db.query(stmt)
        if query.first():
            result = forceInt(query.value(0))
        return result

    # поиск выполненных операций, влияющих на выбор ксг
    def getOperationCount(csgCode, csgEndDate):
        table = db.table('soc_surgeryCSG')
        cond = [table['code'].eq(csgCode),
                table['begDate'].le(csgEndDate),
                db.joinOr([table['endDate'].ge(csgEndDate),
                           table['endDate'].isNull()])
                ]
        record = db.getRecordEx(table, 'code', cond)
        return True if record else False

    # наличие услуги в событии
    def hasServiceInEvent(eventId, serviceCode):
        db = QtGui.qApp.db
        stmt = u"""select a.id
        from Action a
        left join ActionType at on at.id = a.actionType_id
        left join rbService s on s.id = at.nomenclativeService_id
        where a.event_id = %s and a.deleted = 0 and s.infis = '%s'
        """ % (eventId, serviceCode)
        query = db.query(stmt)
        result = query.size()
        return result

    # является ли профиль койки геронтологический?
    def isGerontologicalKPK(eventId):
        db = QtGui.qApp.db
        stmt = """select HospitalAction.id 
                    from Action AS HospitalAction
                    left join ActionPropertyType on ActionPropertyType.typeName = 'HospitalBed' and ActionPropertyType.actionType_id = HospitalAction.actionType_id and ActionPropertyType.deleted = 0
                    left join ActionProperty on ActionProperty.type_id = ActionPropertyType.id and ActionProperty.action_id = HospitalAction.id and ActionProperty.deleted = 0
                    left join ActionProperty_HospitalBed on ActionProperty_HospitalBed.id = ActionProperty.id
                    left join OrgStructure_HospitalBed on OrgStructure_HospitalBed.id = ActionProperty_HospitalBed.value
                    left join rbHospitalBedProfile on rbHospitalBedProfile.id = OrgStructure_HospitalBed.profile_id
                    where HospitalAction.id = (
                        SELECT MAX(A.id)
                        FROM Action A
                        WHERE A.event_id = %s AND
                                  A.deleted = 0 AND
                                  A.actionType_id IN (
                                        SELECT AT.id
                                        FROM ActionType AT
                                        WHERE AT.flatCode ='moving'
                                            AND AT.deleted = 0
                                  )
                    ) and rbHospitalBedProfile.regionalCode = '70'
        """ % eventId
        query = db.query(stmt)
        return query.size()


    def roundMath(val, digits):
        d = 10 ** digits
        return round(val * d) / d

    db = QtGui.qApp.db
    usedCoeffDict = {}
    price = tariff.frags[-3][2] if len(tariff.frags) == 3 and omsCode == '4010402' else tariff.price
    eventWeekProfile = {0: wpFiveDays, 1: wpSixDays, 2: wpSevenDays}.get(weekProfileCode, wpSevenDays)
    age = calcAgeInYears(birthDate, eventSetDate)
    duration = getEventDuration(csgBegDate, csgEndDate, eventWeekProfile, eventTypeId)
    coeff = 0
    hasOperations = getOperationCount(csgCode, csgEndDate)

    if matFedCode in ['1', '3']:
        if age < 5:
            # предоставление спального места и питания законному представителю несовершеннолетних
            # if relativeId:
                # Предоставление спального места и питания законному представителю несовершеннолетних (детей до 4 лет,
                # детей старше 4 лет при наличии медицинских показаний), получающих медицинскую помощь
                # по профилю «Детская онкология» и (или) «Гематология»
                if csgCode[:4] in ['st05', 'st08']:
                    childGemOnkoCoef = contractDescr.coefficients[0, 0][u'ДетиГемОнко'][csgEndDate]
                    coeff += childGemOnkoCoef
                    usedCoeffDict[u'ДетиГемОнко'] = {u'номер': '2', u'значение': childGemOnkoCoef}
                # предоставление спального места и питания законному представителю несовершеннолетних
                # (дети до 4 лет, дети старше 4 лет при наличии медицинских показаний)
                else:
                    childCoef = contractDescr.coefficients[0, 0][u'Дети'][csgEndDate]
                    coeff += childCoef
                    usedCoeffDict[u'Дети'] = {u'номер': '1', u'значение': childCoef}
        elif age >= 75 and csgCode[:4] != 'st37' and hasServiceInEvent(eventId, 'B01.007.001') and not isGerontologicalKPK(eventId):
            # оказание медицинской помощи пациенту в возрасте старше 75 лет в случае проведения консультации врача-гериатра
            # и за исключением случаев госпитализации на геронтологические профильные койки
            seniorCoef = contractDescr.coefficients[0, 0][u'Старше75'][csgEndDate]
            coeff += seniorCoef
            usedCoeffDict[u'Старше75'] = {u'номер': '3', u'значение': seniorCoef}

        # наличие у пациента тяжелой сопутствующей патологии, требующей оказания медицинской помощи в период госпитализации
        if hasSevereMKB(eventId) > 0:
            severeMKBCoef = contractDescr.coefficients[0, 0][u'ТяжСопМКБ'][csgEndDate]
            coeff += severeMKBCoef
            usedCoeffDict[u'ТяжСопМКБ'] = {u'номер': '5', u'значение': severeMKBCoef}

        # проведение сочетанных хирургических вмешательств или проведение однотипных операций на парных органах
        if hasOperations:
            combinedOperationLevel = getCombinedOperationLevel(eventId, csgBegDate, csgEndDate)
            operationPairedOrgansLevel = getOperationPairedOrgansLevel(eventId, csgBegDate, csgEndDate)
            if combinedOperationLevel == 1 or operationPairedOrgansLevel == 1:
                combinedCoef = contractDescr.coefficients[0, 0][u'ПарноСочет1'][csgEndDate]
                coeff += combinedCoef
                usedCoeffDict[u'ПарноСочет1'] = {u'номер': '6', u'значение': combinedCoef}
            elif combinedOperationLevel == 2 or operationPairedOrgansLevel == 2:
                combinedCoef = contractDescr.coefficients[0, 0][u'ПарноСочет2'][csgEndDate]
                coeff += combinedCoef
                usedCoeffDict[u'ПарноСочет2'] = {u'номер': '7', u'значение': combinedCoef}
            elif combinedOperationLevel == 3 or operationPairedOrgansLevel == 3:
                combinedCoef = contractDescr.coefficients[0, 0][u'ПарноСочет3'][csgEndDate]
                coeff += combinedCoef
                usedCoeffDict[u'ПарноСочет3'] = {u'номер': '8', u'значение': combinedCoef}
            elif combinedOperationLevel == 4 or operationPairedOrgansLevel == 4:
                combinedCoef = contractDescr.coefficients[0, 0][u'ПарноСочет4'][csgEndDate]
                coeff += combinedCoef
                usedCoeffDict[u'ПарноСочет4'] = {u'номер': '9', u'значение': combinedCoef}
            elif combinedOperationLevel == 5 or operationPairedOrgansLevel == 5:
                combinedCoef = contractDescr.coefficients[0, 0][u'ПарноСочет5'][csgEndDate]
                coeff += combinedCoef
                usedCoeffDict[u'ПарноСочет5'] = {u'номер': '10', u'значение': combinedCoef}
        if usedCoeffDict:
            usedCoeffDict[u'all'] = {u'значение': coeff}
        baseTariff = forceDouble(contractDescr.attributes['BS'][csgEndDate])
        coeffDiff = forceDouble(contractDescr.attributes['KD'][csgEndDate])
        price = price + roundMath(baseTariff * coeffDiff * coeff, 2)

        # проведение сопроводительной лекарственной терапии при злокачественных новообразованиях у взрослых
        # в стационарных условиях в соответствии с клиническими рекомендациями
        if ('st19.084' <= csgCode <= 'st19.089'
                or 'st19.094' <= csgCode <= 'st19.102'
                or 'st19.125' <= csgCode <= 'st19.143') and hasCrit(eventId, 'supt'):
            onkoCoef = contractDescr.coefficients[0, 0][u'онкоКС'][csgEndDate]
            coeff += onkoCoef
            usedCoeffDict[u'онкоКС'] = {u'номер': '12', u'значение': onkoCoef}
            # стоимость КСЛП «проведение сопроводительной лекарственной терапии при злокачественных новообразованиях
            # у взрослых в соответствии с клиническими рекомендациями» в стационарных условиях и в условиях
            # дневного стационара определяется без учета коэффициента дифференциации субъекта Российской Федерации.
            price = price + roundMath(baseTariff * onkoCoef, 2)
    elif matFedCode == '7':
        if ('ds19.058' <= csgCode <= 'ds19.062'
                or 'ds19.067' <= csgCode <= 'ds19.078'
                or 'ds19.097' <= csgCode <= 'ds19.115') and hasCrit(eventId, 'supt'):
            onkoCoef = contractDescr.coefficients[0, 0][u'онкоДС'][csgEndDate]
            coeff += onkoCoef
            usedCoeffDict[u'онкоДС'] = {u'номер': '13', u'значение': onkoCoef}
            # стоимость КСЛП «проведение сопроводительной лекарственной терапии при злокачественных новообразованиях
            # у взрослых в соответствии с клиническими рекомендациями» в стационарных условиях и в условиях
            # дневного стационара определяется без учета коэффициента дифференциации субъекта Российской Федерации.
            baseTariff = forceDouble(contractDescr.attributes['BS_ds'][csgEndDate])
            price = price + roundMath(baseTariff * onkoCoef, 2)

    # для сверхкоротких случаев лечения (применяется для стационаров всех типов)
    minDuration = tariff.frags[-2][0] if len(tariff.frags) >= 2 else 3
    if minDuration > 1 and duration <= minDuration:
        if 'st19.125' <= csgCode <= 'st19.141':
            interruptedCoeff = contractDescr.coefficients[0, 0][u'ПРЕРВДЛ3ОНКО'][csgEndDate]
            price = roundMath(price * interruptedCoeff, 2)
            usedCoeffDict[u'ПРЕРВДЛ3ОНКО'] = {u'значение': interruptedCoeff}
        elif hasOperations:
            interruptedCoeff = contractDescr.coefficients[0, 0][u'ПРЕРВДЛ3ОПЕР'][csgEndDate]
            price = roundMath(price * interruptedCoeff, 2)
            usedCoeffDict[u'ПРЕРВДЛ3ОПЕР'] = {u'значение': interruptedCoeff}
        else:
            interruptedCoeff = contractDescr.coefficients[0, 0][u'ПРЕРВДЛ3'][csgEndDate]
            price = roundMath(price * interruptedCoeff, 2)
            usedCoeffDict[u'ПРЕРВДЛ3'] = {u'значение': interruptedCoeff}
    # оплата прерванных случаев свыше 3-х дней
    elif (duration > minDuration > 1 or minDuration == 1) and (csgLevel is not None and csgLevel != 2 or csgLevel is None
                                                               and resultCode in ['102', '103', '105', '106', '107', '108', '110', '202', '203', '205', '206', '207', '208']):
        if hasOperations:
            interruptedCoeff = contractDescr.coefficients[0, 0][u'ПРЕРВДЛ4ОПЕР'][csgEndDate]
            price = roundMath(price * interruptedCoeff, 2)
            usedCoeffDict[u'ПРЕРВДЛ4ОПЕР'] = {u'значение': interruptedCoeff}
        elif 'st19.125' <= csgCode <= 'st19.141':
            interruptedCoeff = contractDescr.coefficients[0, 0][u'ПРЕРВДЛ3ОНКО'][csgEndDate]
            price = roundMath(price * interruptedCoeff, 2)
            usedCoeffDict[u'ПРЕРВДЛ3ОНКО'] = {u'значение': interruptedCoeff}
        else:
            interruptedCoeff = contractDescr.coefficients[0, 0][u'ПРЕРВДЛ4'][csgEndDate]
            price = roundMath(price * interruptedCoeff, 2)
            usedCoeffDict[u'ПРЕРВДЛ4'] = {u'значение': interruptedCoeff}

    return price, coeff, usedCoeffDict



def evalPriceEventCSGForKrasnodar(contractDescr,
                                  tariff,
                                  clientId,
                                  eventId,
                                  eventTypeId,
                                  csgBegDate,
                                  csgEndDate,
                                  relative_id,
                                  serviceInfis,
                                  baseTariff=0):
    """Расчет стоимости второго КСГ (по Event_CSG, как правило речь об антимикробной терапии)"""
    db = QtGui.qApp.db
    usedCoeffDict = {}
    coeff = 0
    price = tariff.price
    VP = getEventAidTypeRegionalCode(eventTypeId)

    if VP in ('11', '12', '301', '302') and serviceInfis[3:] in ['st36.013', 'st36.014', 'st36.015'] and QDate(2024, 11, 1) <= csgEndDate < QDate(2026, 1, 1):
        minDuration = 0
        stmt = u"""SELECT ss.code
        FROM Action A
        INNER JOIN ActionType AT ON A.actionType_id = AT.id
        LEFT JOIN ActionProperty ap ON ap.action_id = A.id AND ap.deleted = 0
        LEFT JOIN ActionPropertyType apt ON ap.type_id = apt.id AND apt.deleted = 0
        LEFT JOIN ActionProperty_Integer api ON ap.id = api.id
        LEFT JOIN soc_spr80 ss ON ss.id = api.value
        WHERE A.event_id = {0} AND A.deleted = 0 AND AT.flatCode  = 'KRIT'
            AND apt.typeName = 'Доп. классиф. критерий'  AND ss.code like 'amt%'""".format(eventId)
        query = db.query(stmt)
        if query.first():
            amtCode = forceString(query.value(0))
            if amtCode in ['amt02', 'amt04','amt05','amt07','amt08','amt09','amt10','amt12','amt13','amt14','amt15']:
                minDuration = 4
            elif amtCode in ['amt01', 'amt03','amt06','amt11']:
                minDuration = 9
        eventWeekProfile = getWeekProfile(forceInt(db.getRecord('EventType', 'weekProfileCode', eventTypeId).value('weekProfileCode')))
        duration = getEventDuration(csgBegDate, csgEndDate, eventWeekProfile, eventTypeId)
        if duration < minDuration:
            if duration >= 3:
                price = roundMath(price * contractDescr.coefficients[0, 0][u'ПРЕРВДЛ4'][csgEndDate], 2)
            else:
                price = roundMath(price * contractDescr.coefficients[0, 0][u'ПРЕРВДЛ3'][csgEndDate], 2)

    return price, coeff, usedCoeffDict


def evalPriceActionsForKrasnodar(actionId, eventId, orgId, isInternalOrg, isTFOMS,
                                 medicalAidTypeCode, eventProfileRegionalCode, eventTypeIdentification, eventBegDate, eventEndDate,
                                 exposeDate, serviceInfis, amount, price, summa,
                                 serviceIsObr, serviceHasObr, eventHasReab, isProfCompleted, isDispCompleted, actionEndDate):

    # по маммографии с ИИ должен быть TARU - с ценой, SUMM - 0
    if serviceInfis == 'A06.30.002.017':
        summa = 0
    # тарификация услуг обращения/посещения для поликлиники
    elif (medicalAidTypeCode in ['21', '22']
          and serviceInfis[:3] in ['B01', 'B02', 'B04', 'B05']
          and not serviceIsObr
          and serviceHasObr
          and serviceInfis not in ['B05.015.002.010', 'B05.015.002.011',
                                   'B05.015.002.012', 'B05.023.002.012',
                                   'B05.023.002.013', 'B05.023.002.14', 'B05.050.004.019',
                                   'B05.050.004.020', 'B05.050.004.021', 'B05.070.010',
                                   'B05.070.011', 'B05.070.012']
    ):
        price, summa = 0, 0
    # обнуление услуг по реабилитации
    elif (medicalAidTypeCode == '21' and eventHasReab
          and serviceInfis not in ['B05.015.002.010', 'B05.015.002.011',
                                   'B05.015.002.012', 'B05.023.002.012',
                                   'B05.023.002.013', 'B05.023.002.14', 'B05.050.004.019',
                                   'B05.050.004.020', 'B05.050.004.021', 'B05.070.010',
                                   'B05.070.011', 'B05.070.012']):
        price, summa = 0, 0
    # для ранее оказанных и внешних услуг - цена равна 0
    elif eventBegDate > exposeDate or orgId and medicalAidTypeCode != '211' or orgId and isInternalOrg:
        price, summa = 0, 0
    # обнуление простых услуг для детских профосмотров
    elif medicalAidTypeCode in ['232', '252', '262'] and serviceInfis[:7] not in ['B04.031', 'B04.026']:
        price, summa = 0, 0
    # обнуление стоимости услуг для выполненного этапа профосмотров взрослого населения
    elif medicalAidTypeCode == '261' and eventProfileRegionalCode in ['8011'] and isProfCompleted:
        if serviceInfis[:7] not in ['B04.026', 'B04.047']:
            price, summa = 0, 0
    # обнуление стоимости услуг для выполненного этапа взрослой диспансеризации
    elif medicalAidTypeCode == '211' and eventProfileRegionalCode in ['8008', '8014'] and isDispCompleted:
        if serviceInfis[:7] not in ['B04.026', 'B04.047']:
            price, summa = 0, 0
    # обнуление стоимости простых услуг для второго этапа взрослой диспансеризации
    elif medicalAidTypeCode in ['211'] and eventProfileRegionalCode in ['8009', '8015']:
        if serviceInfis[:1] == 'A':
            price, summa = 0, 0
    # обнуление стоимости у краевых застрахованных участковой службы
    elif medicalAidTypeCode in ['271', '272'] and not isTFOMS:
        price, summa = 0, 0
    # обнуление стоимости у услуг терапевта по углубленной диспансеризации
    elif medicalAidTypeCode == '233' and serviceInfis in ['B04.047.002', 'B04.047.004', 'B04.026.002']:
        price, summa = 0, 0
    elif medicalAidTypeCode == '244' and serviceInfis[:1] == 'A' and eventProfileRegionalCode in ['8020']:
        # ТТ 3003 "Выставлять жидкостную цитологию с ценой"
        if serviceInfis == "A08.20.017.002":
            stmt = """SELECT Action.id
                      FROM Action
                      LEFT JOIN ActionType ON ActionType.id = Action.actionType_id
                      WHERE Action.event_id = {0} AND Action.id <> {1} AND Action.deleted = 0
                          AND ActionType.deleted = 0 AND ActionType.nomenclativeService_id IS NOT NULL""".format(
                eventId, actionId)
            query = QtGui.qApp.db.query(stmt)
            if query.size() > 0:
                price, summa = 0, 0
        else:
            price, summa = 0, 0

    if medicalAidTypeCode in ['211', '261', '233', '244', '232', '252', '262'] and summa > 0:
        eventWeekProfile = wpFiveDays
        # В случае проведения мероприятий в рамках профилактических осмотров,
        # включая диспансеризацию в выходные дни
        if eventEndDate >= QDate(2025, 1, 1) and medicalAidTypeCode == '244':
            #  В репродуктивной применяется только к приёмам в выходной день
            if countWorkDays(actionEndDate, actionEndDate, eventWeekProfile) == 0 and "B04" in serviceInfis:
                price = round(round(price, 2) * 1.03, 2)
                summa = price
        else:
            if countWorkDays(eventEndDate, eventEndDate, eventWeekProfile) == 0:
                price = round(round(price, 2) * 1.03, 2)
                summa = price

        # В случае проведения мобильными медицинскими бригадами полного комплекса мероприятий
        # в рамках профилактических осмотров, включая диспансеризацию
        if QDate(2023, 1, 1) <= eventEndDate < QDate(2025, 2, 1) and eventTypeIdentification in ['mob']:
            price = round(round(price, 2) * 1.2, 2)
            summa = price

    return price * amount, summa * amount
