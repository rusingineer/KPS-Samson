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
from PyQt4 import QtGui
from PyQt4.QtCore import QDate

from Accounting.Tariff import CTariff

from library.AgeSelector import parseAgeSelector, checkAgeSelector
from library.Identification import getIdentification
from library.PrintInfo import CInfo, CRBInfo, CDateInfo, CRBInfoWithIdentification
from library.Utils import (
    forceString,
    forceDouble,
    forceInt,
    forceDate,
    calcAgeTuple,
    forceRef,
    forceBool
)


class CServiceGroupInfo(CRBInfo):
    tableName = 'rbServiceGroup'

    def _initByRecord(self, record):
        self._regionalCode = forceString(record.value('regionalCode'))


    def _initByNull(self):
        self._regionalCode = None

    regionalCode  = property(lambda self: self.load()._regionalCode)


class CServiceInfo(CRBInfoWithIdentification):
    tableName = 'rbService'

    def _initByRecord(self, record):
        self._groupId = forceRef(record.value('group_id'))
        self._eisLegacy = forceBool(record.value('eisLegacy'))
        self._license = forceBool(record.value('license'))
        self._infis = forceString(record.value('infis'))
        self._begDate = CDateInfo(record.value('begDate'))
        self._endDate = CDateInfo(record.value('endDate'))
        self._adultUetDoctor = forceDouble(record.value('adultUetDoctor'))
        self._adultUetAverageMedWorker = forceDouble(record.value('adultUetAverageMedWorker'))
        self._childUetDoctor = forceDouble(record.value('childUetDoctor'))
        self._childUetAverageMedWorker = forceDouble(record.value('childUetAverageMedWorker'))


    def _initByNull(self):
        self._groupId = None
        self._eisLegacy = False
        self._eisLegacy = False
        self._license = False
        self._infis = ''
        self._begDate = CDateInfo()
        self._endDate = CDateInfo()
        self._adultUetDoctor = 0
        self._adultUetAverageMedWorker = 0
        self._childUetDoctor = 0
        self._childUetAverageMedWorker = 0


    def prepareTariff(self, contractId, clientId = None):
        self.tariff = self.getInstance(CTariffInfo, self.id)
        self.tariff.setContractId(contractId)
        if clientId:
            self.tariff.setClientId(clientId)

    group       = property(lambda self: self.getInstance(CServiceGroupInfo, self.load()._groupId))
    eisLegacy   = property(lambda self: self.load()._eisLegacy)
    license     = property(lambda self: self.load()._license)
    infis       = property(lambda self: self.load()._infis)
    begDate     = property(lambda self: self.load()._begDate)
    endDate     = property(lambda self: self.load()._endDate)
    adultUetDoctor = property(lambda self: self.load()._adultUetDoctor)
    adultUetAverageMedWorker = property(lambda self: self.load()._adultUetAverageMedWorker)
    childUetDoctor = property(lambda self: self.load()._childUetDoctor)
    childUetAverageMedWorker = property(lambda self: self.load()._childUetAverageMedWorker)
    serviceIdent = property(lambda self: self.identify(u'urn:oid:131o'))


# WTF? что это? почему это здесь?
class CTariffInfo(CInfo):
    def __init__(self, context, serviceId):
        CInfo.__init__(self, context)
        self._serviceId = serviceId
        self._masterId = None
        self._price = None
        self._uet = 0
        self._maxAmount = 0
        self._contractDescr = None
        self._clientId = None
        self._clientBirthDate = None


    def setContractId(self, contractId):
        self._masterId = contractId

    def setClientId(self, clientId):
        self._clientId = clientId


    def _load(self, isVisit,  execDate):
        if self._masterId and self._serviceId:
            db = QtGui.qApp.db
            table = db.table('Contract_Tariff')
            cond = [table['deleted'].eq(0),
                    table['service_id'].eq(self._serviceId),
                    table['master_id'].eq(self._masterId), 
                    table['begDate'].le(execDate), 
                   "Contract_Tariff.endDate is null or Contract_Tariff.endDate >= '%s'" % execDate.toString("yyyy-MM-dd")
                   ]
            if isVisit:
                cond.append(table['tariffType'].eq(0))
                       
            recordList = db.getRecordList(table, '*', cond)
            tariffRecord = None
            for record in recordList:
                age = forceString(record.value('age'))
                ageSelector = None
                if age and self._clientId:
                    ageSelector = parseAgeSelector(age)
                    if not self._clientBirthDate:
                        self._clientBirthDate = forceDate(db.translate('Client', 'id', self._clientId, 'birthDate'))
                    clientAge = calcAgeTuple(self._clientBirthDate, QDate.currentDate())
                    if not clientAge:
                        clientAge = (0, 0, 0, 0)
                    if checkAgeSelector(ageSelector, clientAge):
                        tariffRecord = record
                        break
                else:
                    tariffRecord = record
                    break
            if tariffRecord:
                self._price            = forceDouble(tariffRecord.value('price'))
                self._uet = forceDouble(tariffRecord.value('uet'))
                frags = [(0.0, 0.0, self._price)]

                if forceDouble(tariffRecord.value('frag1Start')):
                    frags.append(( forceDouble(tariffRecord.value('frag1Start')),
                                   forceDouble(tariffRecord.value('frag1Sum')),
                                   forceDouble(tariffRecord.value('frag1Price')),
                                ))

                if forceDouble(tariffRecord.value('frag2Start')):
                    frags.append(( forceDouble(tariffRecord.value('frag2Start')),
                                   forceDouble(tariffRecord.value('frag2Sum')),
                                   forceDouble(tariffRecord.value('frag2Price'))/2,
                                ))
                frags.reverse()
                self._frags            = frags

                self._tariffType = forceInt(tariffRecord.value('tariffType'))
                self._maxAmount = forceDouble(tariffRecord.value('amount'))
                self._tariff = CTariff(tariffRecord, 2)
                return True
        return False



    def getPrice(self, amount, execDate, isVisit=False, eventInfo=None, actionInfo=None, isEvent_CSG=False, csgBegDate=None):
        from Accounting.Utils import getContractDescr
        from Accounting.Utils import unpackExposeDiscipline
        from Accounting.AccountBuilder import evalPriceForKrasnodarA13, evalPriceEventCSGForKrasnodar, evalPriceActionsForKrasnodar, evalPriceForMurmansk2015Hospital
        db = QtGui.qApp.db

        if self._load(isVisit,  execDate):
            if self._maxAmount and amount > self._maxAmount:
                amount = self._maxAmount
            if self._price:
                if self._tariffType == CTariff.ttEventByMESLen:
                    summa = 0
                    for fragStart, fragSum, fragPrice in self._frags:
                        if amount >= fragStart:
                            summa = fragSum + (amount - fragStart) * fragPrice
                            break
                    price = summa / amount if amount else self._price
                    return summa
                elif self._tariffType == CTariff.ttVisitsByMES:  # визиты по МЭС
                    return self._price
                elif self._tariffType == CTariff.ttKrasnodarA13 and eventInfo is not None and eventInfo._loaded:
                    if not self._contractDescr:
                        self._contractDescr = getContractDescr(self._masterId)
                    clientId = eventInfo._clientId
                    eventId = eventInfo.id
                    eventTypeId = eventInfo.getEventTypeId()
                    eventBegDate = eventInfo._setDate.date
                    eventEndDate = eventInfo._execDate.date
                    relativeId = eventInfo._relative._id
                    infis = forceString(db.translate('rbService', 'id', self._serviceId, 'infis'))

                    spr13Code =  forceString(db.translate('rbMedicalAidType', 'id', eventInfo.eventType.medicalAidType.id, 'regionalCode'))
                    if spr13Code in ['11', '12', '301', '302', '401', '402']:
                        group = 1
                    elif spr13Code in ['41', '411', '42', '422', '43', '51', '511', '52', '522', '71', '72', '90']:
                        group = 2
                    else:
                        group = 0
                    db = QtGui.qApp.db
                    records = db.getRecordList('soc_spr89')
                    mapBaseTariff = dict()
                    baseTariff = 0
                    for record in records:
                        begDate = forceDate(record.value('DATN'))
                        endDate = forceDate(record.value('DATO'))
                        codeGR = forceInt(record.value('CODE_GR'))
                        tariff = forceDouble(record.value('B_TARIFF'))
                        key = (begDate, endDate, codeGR)
                        mapBaseTariff[key] = tariff
                    for (begDate, endDate, codeGR) in mapBaseTariff.keys():
                        if codeGR == group and begDate <= eventEndDate and (eventEndDate <= endDate or endDate.isNull()):
                            baseTariff = mapBaseTariff[(begDate, endDate, codeGR)]
                            break

                    if isEvent_CSG:
                        price, coeff, usedCoeffDict = evalPriceEventCSGForKrasnodar(self._contractDescr, self._tariff, clientId, eventId, eventTypeId, csgBegDate if csgBegDate else eventBegDate, execDate, relativeId, infis, baseTariff)
                    else:
                        price, coeff, usedCoeffDict, interruptReason, interruptCoeff = evalPriceForKrasnodarA13(self._contractDescr, self._tariff, clientId, eventId, eventTypeId, eventBegDate, execDate, relativeId, infis, baseTariff)

                    sum = round(price, 2)
                    return sum
                elif self._tariffType == CTariff.ttMurmansk2015Hospital and eventInfo is not None and eventInfo._loaded:
                    if not self._contractDescr:
                        self._contractDescr = getContractDescr(self._masterId)
                    amount = 1.0
                    clientId = eventInfo._clientId
                    eventId = eventInfo.id
                    eventTypeId = eventInfo.getEventTypeId()
                    eventBegDate = eventInfo._setDate.date
                    eventEndDate = eventInfo._execDate.date
                    shortHospitalisation = eventBegDate.addDays(1) > eventEndDate
                    level = eventInfo.mesSpecification.level
                    mesId = eventInfo.mes.id
                    price  = evalPriceForMurmansk2015Hospital(self._contractDescr, self._tariff, eventId, eventTypeId, eventBegDate, eventEndDate, mesId, shortHospitalisation, level)
                    sum    = round(price, 2)
                    return sum
                elif self._tariffType in [CTariff.ttActionAmount, CTariff.ttActionUET] and eventInfo is not None and actionInfo is not None and eventInfo._loaded:
                    actionId = actionInfo.id
                    record = db.getRecord("vAction LEFT JOIN Person ON Person.id = vAction.person_id LEFT JOIN Event ON Event.id = vAction.event_id \
                            left join Client on Client.id = Event.client_id left join Account_Item ON Account_Item.event_id = Event.id and Account_Item.action_id = vAction.id \
                            and Account_Item.refuseType_id is not null and Account_Item.reexposeItem_id is null and Account_Item.deleted = 0 \
                            left join EventType on EventType.id = Event.eventType_id \
                            left join rbMedicalAidType on EventType.medicalAidType_id = rbMedicalAidType.id \
                            left join rbEventProfile ep on ep.id = EventType.eventProfile_id",
                          """Event.id as eventId, Event.setDate, Event.result_id, Event.eventType_id, Event.client_id, vAction.id, vAction.actionType_id, Event.eventType_id, 
                          vAction.event_id, vAction.exposeDate, vAction.amount, vAction.MKB, Person.tariffCategory_id, Event.execDate, 
                          Account_Item.id as oldAccId, Client.birthDate, vAction.org_id, rbMedicalAidType.regionalCode as matCode, ep.regionalCode as eventProfile
                          , vAction.endDate as actionEndDate""", actionId)
                    orgId = forceRef(record.value('org_id'))
                    exposeDate = forceDate(record.value('exposeDate'))
                    eventEndDate = forceDate(record.value('execDate'))
                    eventBegDate = forceDate(record.value('setDate'))
                    actionEndDate = forceDate(record.value('actionEndDate'))
                    eventTypeId = forceRef(record.value('eventType_id'))
                    eventId = forceRef(record.value('eventId'))
                    serviceRecord = db.getRecord('rbService', ['infis', u"name like 'Обращен%' AS isObr"], self._serviceId)
                    serviceInfis = forceString(serviceRecord.value('infis'))
                    serviceIsObr = forceInt(serviceRecord.value('isObr'))
                    medicalAidTypeCode = forceString(record.value('matCode'))
                    eventProfileRegionalCode = forceString(record.value('eventProfile'))
                    isInternalOrg = False
                    price = summa = self._price

                    if not self._contractDescr:
                        self._contractDescr = getContractDescr(self._masterId)
                        self.exposeBySourceOrg, self.exposeByOncology, self.exposeByBatch, self.exposeByEvent, self.exposeByMonth, self.exposeByClient, self.exposeByInsurer = unpackExposeDiscipline(self._contractDescr.exposeDiscipline)

                    def getPayer(clientId, date, eventId=None):
                        from Registry.Utils import getClientCompulsoryPolicy

                        def getPayerId(insurerId):
                            result = None
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
                                        tmpInsurerId = self._contractDescr.payerId
                                result = tmpInsurerId
                            return result

                        if clientId:
                            if QtGui.qApp.defaultKLADR()[:2] == u'23':
                                record = getClientCompulsoryPolicy(clientId, date, eventId)
                            else:
                                record = getClientCompulsoryPolicy(clientId)
                            if record:
                                insurerId = forceRef(record.value('insurer_id'))
                                insurerArea = forceString(record.value('area'))
                                return getPayerId(insurerId), insurerArea
                        return None, None

                    (payerId, insurerArea) = getPayer(eventInfo._clientId, execDate, eventId) if self.exposeByInsurer else (self._contractDescr.payerId, '00')
                    isTFOMS = payerId == self._contractDescr.payerId

                    if medicalAidTypeCode in ['271', '272'] and isTFOMS:
                        medicalAidTypeCode = '21' if medicalAidTypeCode == '271' else '22'

                    if orgId:
                        orgCode = forceString(db.translate('Organisation', 'id', orgId, 'infisCode'))
                        isInternalOrg = bool(db.getCount("OrgStructure", "bookkeeperCode", "TRIM(bookkeeperCode) = '{0}'".format(orgCode)))

                    serviceHasObr = serviceIsObr
                    if medicalAidTypeCode in ['21', '22'] and serviceInfis[:3] in ['B01', 'B02', 'B04', 'B05'] and not serviceIsObr:
                        stmt = u"""select a.id
                                from Event e
                                LEFT JOIN soc_obr u ON u.spec = '{codeSpec}'
                                left join rbService rs on rs.infis in (u.kusl, u.kusl2)
                                left join ActionType at on at.nomenclativeService_id = rs.id
                                left join Action a on a.event_id = e.id and a.actionType_id = at.id
                                where e.id = {aEvent_id} and e.deleted = 0 and a.deleted = 0
                                and rs.infis not in ('B02.001.005', 'B02.001.006', 'B02.031.010', 'B02.047.009', 'B02.047.010')""".format(
                            aEvent_id=eventId, codeSpec=serviceInfis[4:7])
                        query = QtGui.qApp.db.query(stmt)
                        serviceHasObr = query.size() > 0

                    eventHasReab = False
                    if medicalAidTypeCode == '21':
                        stmt = u"""select a.id
                                from Action a
                                left join ActionType at on at.id = a.actionType_id
                                left join rbService rs on rs.id = at.nomenclativeService_id
                                where a.id = {aEvent_id} and a.deleted = 0
                                and rs.infis in ('B05.015.002.010', 'B05.015.002.011', 'B05.015.002.012', 'B05.023.002.012',
                                   'B05.023.002.013', 'B05.023.002.14', 'B05.050.004.019', 'B05.050.004.020', 'B05.050.004.021',
                                   'B05.070.010', 'B05.070.011', 'B05.070.012')""".format(aEvent_id=eventId)
                        query = QtGui.qApp.db.query(stmt)
                        eventHasReab = query.size() > 0

                    isProfCompleted = False
                    if medicalAidTypeCode == '261' and eventProfileRegionalCode in ['8011']:
                        stmt = u"""select a.id
                                from Action a
                                left join ActionType at on at.id = a.actionType_id
                                left join rbService rs on rs.id = at.nomenclativeService_id
                                where a.id = {aEvent_id} and a.deleted = 0
                                and rs.infis in ('B04.047.002', 'B04.026.002')""".format(aEvent_id=eventId)
                        query = QtGui.qApp.db.query(stmt)
                        isProfCompleted = query.size() == 0

                    isDispCompleted = False
                    if medicalAidTypeCode == '211' and eventProfileRegionalCode in ['8008', '8014']:
                        stmt = u"""select a.id
                                from Action a
                                left join ActionType at on at.id = a.actionType_id
                                left join rbService rs on rs.id = at.nomenclativeService_id
                                where a.id = {aEvent_id} and a.deleted = 0
                                and rs.infis in ('B04.026.001.062', 'B04.047.001.061', 'B04.047.001.092', 'B04.026.001.093')""".format(aEvent_id=eventId)
                        query = QtGui.qApp.db.query(stmt)
                        isDispCompleted = query.size() == 0

                    eventTypeIdentification = None
                    if medicalAidTypeCode in ['211', '261', '233', '244', '232', '252', '262']:
                        eventTypeIdentification = getIdentification('EventType', eventTypeId, 'AccTFOMS', raiseIfNonFound=False)

                    price, summa = evalPriceActionsForKrasnodar(actionId, eventId, orgId, isInternalOrg, isTFOMS, medicalAidTypeCode,
                                                 eventProfileRegionalCode, eventTypeIdentification, eventBegDate,
                                                 eventEndDate, exposeDate, serviceInfis, amount, price, summa,
                                                 serviceIsObr, serviceHasObr, eventHasReab, isProfCompleted,
                                                 isDispCompleted, actionEndDate)
                    return summa
                else:
                    return self._price * amount
        return 0
