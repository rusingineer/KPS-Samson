# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, Qt, QDateTime

from library.Utils import forceDouble, forceInt, forceRef

from Accounting.Tariff import CTariff


class CContractTariffDescr:
    def __init__(self, contractId, tariffChecker, loadTariffs=True):
        self.visitTariffMap = {}
        self.actionTariffMap = {}
        self.dateTariffMap = {}
        self.financeId = None

        if contractId and loadTariffs:
            db = QtGui.qApp.db
            self.financeId = forceRef(db.translate('Contract', 'id', contractId, 'finance_id'))
            table = db.table('Contract_Tariff')
            priceListId = forceRef(db.translate('Contract', 'id', contractId, 'priceListExternal_id'))
            if priceListId is None:
                masterCond = table['master_id'].eq(contractId)
                order = 'id'
            else:
                masterCond = table['master_id'].inlist([contractId, priceListId])
                order = 'master_id, id' if priceListId < contractId else 'master_id DESC, id'
            currentDate = QDate().currentDate()
            cond = [masterCond,
                    table['deleted'].eq(0),
                    db.joinOr([table['begDate'].isNull(), table['begDate'].le(currentDate)]),
                    db.joinOr([table['endDate'].isNull(), table['endDate'].ge(currentDate)]),
                    ]
            eventTypeId = tariffChecker.getEventTypeId() if tariffChecker else None
            if eventTypeId:
                cond.append(db.joinOr([table['eventType_id'].eq(eventTypeId),
                                       table['eventType_id'].isNull()
                                       ]))
            records = db.getRecordList(table,
                                       'tariffType, service_id, tariffCategory_id, begDate, endDate, price, uet',
                                       cond,
                                       order)
            for record in records:
                if not tariffChecker or tariffChecker.recordAcceptable(record):
                    tariffType = forceInt(record.value('tariffType'))
                    serviceId = forceRef(record.value('service_id'))
                    tariffCategoryId = forceRef(record.value('tariffCategory_id'))
                    price = forceDouble(record.value('price'))
                    uet = forceDouble(record.value('uet'))
                    if tariffType == CTariff.ttVisit:
                        self._register(self.visitTariffMap, serviceId, tariffCategoryId, price, uet)
                    elif tariffType in (CTariff.ttActionAmount, CTariff.ttActionUET,  CTariff.ttHospitalBedService):
                        self._register(self.actionTariffMap, serviceId, tariffCategoryId, price, uet)

    def getDateTariffMap(self, contractId, tariffChecker, date, financeId):
        if contractId:
            db = QtGui.qApp.db
            self.financeId = financeId
            table = db.table('Contract_Tariff')
            priceListId = forceRef(db.translate('Contract', 'id', contractId, 'priceListExternal_id'))
            if priceListId is None:
                masterCond = table['master_id'].eq(contractId)
                order = 'id'
            else:
                masterCond = table['master_id'].inlist([contractId, priceListId])
                order = 'master_id, id' if priceListId < contractId else 'master_id DESC, id'
            if date is None:
                date = QDate().currentDate()
            cond = [masterCond, table['deleted'].eq(0),
                    db.joinOr([table['begDate'].isNull(), table['begDate'].le(date)]),
                    db.joinOr([table['endDate'].isNull(), table['endDate'].ge(date)]), ]
            eventTypeId = tariffChecker.getEventTypeId() if tariffChecker else None
            if eventTypeId:
                cond.append(db.joinOr([table['eventType_id'].eq(eventTypeId), table['eventType_id'].isNull()]))
            records = db.getRecordList(table, 'tariffType, service_id, tariffCategory_id, begDate, endDate, price, uet',
                                       cond, order)
            for record in records:
                tariffType = forceInt(record.value('tariffType'))
                serviceId = forceRef(record.value('service_id'))
                if tariffType in (CTariff.ttActionAmount, CTariff.ttActionUET,  CTariff.ttHospitalBedService):
                    tariff = CTariff(record, 2)
                    tariffList = self.dateTariffMap.get(serviceId, None)
                    if tariffList:
                        tariffList.append(tariff)
                    else:
                        self.dateTariffMap[serviceId] = [tariff]
        return self

    @staticmethod
    def _register(dataMap, serviceId, tariffCategoryId, price, uet):
        mapTariffCategoryToPriceAndUet = dataMap.setdefault(serviceId, {})
        priceAndUet = mapTariffCategoryToPriceAndUet.get(tariffCategoryId, None)
        if priceAndUet is None:
            mapTariffCategoryToPriceAndUet[tariffCategoryId] = price, uet
            if tariffCategoryId is None:
                mapTariffCategoryToPriceAndUet[0] = price, uet


class CContractTariffCache:
    def __init__(self):
        self.mapContractIdToDecr = {}
        self.mapContractIdToDate = {}

    def getTariffDescr(self, contractId, tariffChecker):
        if contractId in self.mapContractIdToDecr:
            return self.mapContractIdToDecr[contractId]
        else:
            result = CContractTariffDescr(contractId, tariffChecker)
            self.mapContractIdToDecr[contractId] = result
            return result

    def getTariffDate(self, contractId, tariffChecker, date, financeId):
        dateString = date.date().toString(Qt.ISODate) if isinstance(date, QDateTime) else date.toString(Qt.ISODate)
        result = self.mapContractIdToDate.get((contractId, dateString))
        if not result:
            result = CContractTariffDescr(contractId, tariffChecker, loadTariffs=False).getDateTariffMap(contractId, tariffChecker, date, financeId)
            self.mapContractIdToDate[(contractId, dateString)] = result
        return result


    @staticmethod
    def getServiceIdList(tariffMap):
        return tariffMap.keys()

    @staticmethod
    def getPriceAndUet(tariffMap, serviceIdList, tariffCategoryId):
        resultPrice = 0.0
        resultUet = 0.0
        for serviceId in serviceIdList:
            mapTariffCategoryToPriceAndUet = tariffMap.get(serviceId, None)
            if mapTariffCategoryToPriceAndUet:
                priceAndUet = mapTariffCategoryToPriceAndUet.get(tariffCategoryId, None)
                if priceAndUet is None:
                    priceAndUet = mapTariffCategoryToPriceAndUet.get(None, None)
                if priceAndUet:
                    resultPrice += priceAndUet[0]
                    resultUet += priceAndUet[1]
        return resultPrice, resultUet

    @staticmethod
    def getPrice(tariffMap, serviceIdList, tariffCategoryId):
        return CContractTariffCache.getPriceAndUet(tariffMap, serviceIdList, tariffCategoryId)[0]

    @staticmethod
    def getUet(tariffMap, serviceIdList, tariffCategoryId):
        return CContractTariffCache.getPriceAndUet(tariffMap, serviceIdList, tariffCategoryId)[1]

    @staticmethod
    def getPriceAndUetToDate(tariffMap, serviceIdList, tariffCategoryId, date):
        resultPrice = 0.0
        resultUet = 0.0
        for serviceId in serviceIdList:
            mapTariffCategoryToPriceAndUet = tariffMap.get(serviceId, None)
            if mapTariffCategoryToPriceAndUet:
                for tariff in mapTariffCategoryToPriceAndUet:
                    if CContractTariffCache.isTariffApplicable(tariff, tariffCategoryId, date):
                        resultPrice, resultPrice, resultSum = tariff.evalAmountPriceSum(1, 1.0)
                        resultUet = tariff.uet if tariff.tariffType == CTariff.ttActionUET else 0
        return resultPrice, resultUet

    @staticmethod
    def getPriceToDate(tariffMap, serviceIdList, tariffCategoryId, date):
        return CContractTariffCache.getPriceAndUetToDate(tariffMap, serviceIdList, tariffCategoryId, date)[0]

    @staticmethod
    def getUetToDate(tariffMap, serviceIdList, tariffCategoryId, date):
        return CContractTariffCache.getPriceAndUetToDate(tariffMap, serviceIdList, tariffCategoryId, date)[1]

    @staticmethod
    def isTariffApplicable(tariff, tariffCategoryId, date):
        if tariff.tariffCategoryId and tariff.tariffCategoryId != tariffCategoryId:
            return False
        if not tariff.dateInRange(date):
            return False
        return True
