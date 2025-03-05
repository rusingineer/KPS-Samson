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

from PyQt4 import QtGui, QtCore

from library.blmodel.Model import CModel, CDocumentModel
from library.blmodel.ModelAttribute import (
    CIntAttribute, CStringAttribute, CDateTimeAttribute, CDateAttribute, CRefAttribute, CDoubleAttribute
)
from library.blmodel.ModelRelationship import CRelationship

from Stock.Utils import getStockMotionNumberCounterId


class CStockMotionType:
    invoice = 0
    inventory = 1
    finTransfer = 2
    production = 3
    clientInvoice = 4
    clientRefund = 5
    clientReservation = 6
    utilization = 7
    internalConsumption = 8
    supplierRefund = 9
    incomingInvoice = 10
    residualQuantityWriteDown = 11


class CStockMotion(CDocumentModel):
    tableName = 'StockMotion'

    type = CIntAttribute()
    number = CStringAttribute(length=32)
    date = CDateTimeAttribute()
    reason = CStringAttribute(length=128)
    reasonDate = CDateAttribute()
    supplier_id = CRefAttribute()
    receiver_id = CRefAttribute()
    note = CStringAttribute()
    supplierPerson_id = CRefAttribute()
    receiverPerson_id = CRefAttribute()
    client_id = CRefAttribute()
    supplierOrgPerson = CStringAttribute(length=255)
    supplierOrg_id = CRefAttribute()

    def generateStockMotionNumber(self):
        if self.id:
            # In this case document number must be already generated or entered by user
            return

        if self.number:
            # Document number already exists
            return

        counterId = getStockMotionNumberCounterId(self.stockDocumentType)
        if not counterId:
            return

        self.number = QtGui.qApp.getDocumentNumber(None, counterId, date=QtCore.QDate.currentDate())


class CStockMotionItemReason(CDocumentModel):
    tableName = 'rbStockMotionItemReason'

    code = CStringAttribute(length=64)
    name = CStringAttribute(length=128)
    stockMotionType = CIntAttribute()



class CRBNomenclature(CDocumentModel):
    tableName = 'rbNomenclature'

    type_id = CRefAttribute()
    code = CStringAttribute(length=64)
    regionalCode = CStringAttribute(length=64)
    name =CStringAttribute(length=255)
    internationalNonproprietaryName = CStringAttribute(length=128)
    analog_id = CRefAttribute()
    producer = CStringAttribute(length=128)
    ATC = CStringAttribute(length=16)
    packSize = CIntAttribute()
    dosageValue = CStringAttribute(length=25)
    unit_id = CRefAttribute()
    lfForm_id = CRefAttribute()
    inDate = CDateAttribute()
    exDate = CDateAttribute()
    trnCode = CStringAttribute(length=10)
    mnnCode = CStringAttribute(length=10)
    completeness = CStringAttribute(length=100)
    defaultClientUnit_id = CRefAttribute()
    defaultStockUnit_id = CRefAttribute()
    originName = CStringAttribute(length=48)
    mnnLatin = CStringAttribute(length=128)


class CStockMotionItem(CModel):
    tableName = 'StockMotion_Item'

    master_id = CRefAttribute()
    idx = CIntAttribute()
    nomenclature_id = CRefAttribute()
    batch = CStringAttribute(length=64)
    shelfTime = CDateAttribute()
    finance_id = CRefAttribute()
    medicalAidKind_id = CRefAttribute()
    qnt = CDoubleAttribute()
    price = CDoubleAttribute()
    sum = CDoubleAttribute()
    oldQnt = CDoubleAttribute()
    oldSum = CDoubleAttribute()
    oldFinance_id = CRefAttribute()
    isOut = CDoubleAttribute()
    note = CStringAttribute()
    unit_id = CRefAttribute()
    reason_id = CRefAttribute()

    stockMotion = CRelationship(CStockMotion, 'master_id')
    reason = CRelationship(CStockMotionItemReason, 'reason_id')
    nomenclature = CRelationship(CRBNomenclature, 'nomenclature_id')

    def setBatch(self, batch):
        batch = CStockMotionItem.batch.attributeType.fromQVariantValue(batch)
        if self.batch == batch:
            return False
        self.batch = batch
        return True

    def setShelfTime(self, shelfTime):
        shelfTime = CStockMotionItem.shelfTime.attributeType.fromQVariantValue(shelfTime)
        if self.shelfTime == shelfTime:
            return False
        self.shelfTime = shelfTime
        return True

    def setFinanceId(self, finance_id):
        finance_id = CStockMotionItem.finance_id.attributeType.fromQVariantValue(finance_id)
        if self.finance_id == finance_id:
            return False
        self.finance_id = finance_id
        return True


    def setMedicalAidKindId(self, medicalAidKind_id):
        medicalAidKind_id = CStockMotionItem.medicalAidKind_id.attributeType.fromQVariantValue(medicalAidKind_id)
        if self.medicalAidKind_id == medicalAidKind_id:
            return False
        self.medicalAidKind_id = medicalAidKind_id
        return True


    def setSum(self, sum):
        sum = CStockMotionItem.sum.attributeType.fromQVariantValue(sum)
        if self.sum == sum:
            return False
        self.sum = sum
        return True


    def setQnt(self, qnt):
        qnt = CStockMotionItem.qnt.attributeType.fromQVariantValue(qnt)
        if self.qnt == qnt:
            return False
        self.qnt = qnt
        return True


    def setPrice(self, price):
        price = CStockMotionItem.price.attributeType.fromQVariantValue(price)
        if self.price == price:
            return False
        self.price = price
        return True

