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

from Orgs.Utils                            import COrgStructureInfo, COrgInfo
from Orgs.PersonInfo                       import CPersonInfo
from RefBooks.Finance.Info                 import CFinanceInfo
from RefBooks.MedicalAidKind.Info          import CMedicalAidKindInfo
from RefBooks.FinanceSource.Info           import CFinanceSourceInfo
from RefBooks.Unit.Info                    import CUnitInfo
from Registry.Utils                        import CClientInfo
from Stock.NomenclatureComboBox            import getFeaturesAndValues
from Stock.Utils                           import getMotionRecordsByRequisition
from library.PrintInfo                     import (
                                                   CInfo,
                                                   CInfoList,
                                                   CDateInfo,
                                                   CDateTimeInfo,
                                                   CRBInfo,
                                                   CRBInfoWithIdentification,
                                                  )
from library.Utils                         import (
                                                   forceDate,
                                                   forceDateTime,
                                                   forceDouble,
                                                   forceInt,
                                                   forceRef,
                                                   forceString,
                                                   forceStringEx,
                                                  )
from library.RLS.RLSInfo                   import CRLSInfo
from library.ESKLP.SmnnInfo                import CSmnnInfo


class CStockMotionItemReasonInfo(CRBInfo):
    tableName = 'rbStockMotionItemReason'


class CStockMotionItemInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id


    def setRecord(self, record):
        self._idx          = forceInt(record.value('idx'))
        self._nomenclature =  self.getInstance(CNomenclatureInfo, forceRef(record.value('nomenclature_id')))
        self._batch        = forceString(record.value('batch'))
        self._shelfTime    = CDateInfo(forceDate(record.value('shelfTime')))
        self._finance      = self.getInstance(CFinanceInfo, forceRef(record.value('finance_id')))
        self._qnt          = forceDouble(record.value('qnt'))
        self._price        = forceDouble(record.value('price'))
        self._sum          = forceDouble(record.value('sum'))
        self._oldQnt       = forceDouble(record.value('oldQnt'))
        self._oldPrice     = forceDouble(record.value('oldPrice'))
        self._oldSum       = forceDouble(record.value('oldSum'))
        self._isOut        = forceInt(record.value('isOut'))
        self._isOutString  = (u'затрата', u'получение')[self._isOut] if self._isOut in (0, 1) else u''
        self._note         = forceString(record.value('note'))
        self._unit         = self.getInstance(CUnitInfo, forceRef(record.value('unit_id')))
        self._reason       = self.getInstance(CStockMotionItemReasonInfo, forceRef(record.value('reason_id')))
        self._medicalAidKind = self.getInstance(CMedicalAidKindInfo, forceRef(record.value('medicalAidKind_id')))
        self._disposalMethod = self.getInstance(CDisposalMethodInfo, forceRef(record.value('disposalMethod_id')))
        return self


    def loadFromRecord(self, record):
        self.setRecord(record)
        self.setOkLoaded()
        return self


    def setOkLoaded(self):
        CInfo.setOkLoaded(self)
        return self


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('StockMotion_Item', '*', self.id) if self.id else None
        if record:
            self.setRecord(record)
            return True
        else:
            self._idx            = None
            self._nomenclature   = self.getInstance(CNomenclatureInfo, None)
            self._batch          = u''
            self._shelfTime      = CDateInfo()
            self._finance        = self.getInstance(CFinanceInfo, None)
            self._qnt            = 0
            self._price          = 0
            self._sum            = 0
            self._oldQnt         = 0
            self._oldPrice       = 0
            self._oldSum         = 0
            self._isOut          = None
            self._isOutString    = u''
            self._note           = u''
            self._unit           = self.getInstance(CUnitInfo, None)
            self._reason         = self.getInstance(CStockMotionItemReasonInfo, None)
            self._medicalAidKind = self.getInstance(CMedicalAidKindInfo, None)
            self._disposalMethod = self.getInstance(CDisposalMethodInfo, None)
            return False

    idx = property(lambda self: self.load()._idx)
    nomenclature = property(lambda self: self.load()._nomenclature)
    batch = property(lambda self: self.load()._batch)
    isOut = property(lambda self: self.load()._isOutString)
    shelfTime = property(lambda self: self.load()._shelfTime)
    finance = property(lambda self: self.load()._finance)
    qnt = property(lambda self: self.load()._qnt)
    price = property(lambda self: self.load()._price)
    sum = property(lambda self: self.load()._sum)
    oldQnt = property(lambda self: self.load()._oldQnt)
    oldPrice = property(lambda self: self.load()._oldPrice)
    oldSum = property(lambda self: self.load()._oldSum)
    note = property(lambda self: self.load()._note)
    unit = property(lambda self: self.load()._unit)
    reason = property(lambda self: self.load()._reason)
    medicalAidKind = property(lambda self: self.load()._medicalAidKind)
    disposalMethod = property(lambda self: self.load()._disposalMethod)


class CStockMotionCommissionInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def setRecord(self, record):
        if record:
            self._idx = forceInt(record.value('idx'))
            self._post = forceInt(record.value('post'))
            self._person = self.getInstance(CPersonInfo, forceRef(record.value('person_id')))
        else:
            self._idx = 0
            self._post = 0
            self._person = self.getInstance(CPersonInfo, None)

    def _load(self):
        record = QtGui.qApp.db.getRecord('StockMotion_CommissionComposition', '*', self.id)
        self.setRecord(record)
        return True

    @property
    def postName(self):
        return (u'Утверждающий', u'Председатель', u'Член комиссии')[self.post]

    idx = property(lambda self: self.load()._idx)
    post = property(lambda self: self.load()._post)
    person = property(lambda self: self.load()._person)


class CStockMotionItemInfoList(CInfoList):
    def __init__(self, context, parentId):
        CInfoList.__init__(self, context)
        self._idList = []
        self.masterId = parentId


    def _load(self):
        cond = 'master_id = %d AND deleted = 0' % self.masterId
        self._idList = QtGui.qApp.db.getIdList('StockMotion_Item', 'id', cond)
        self._items = [ self.getInstance(CStockMotionItemInfo, id) for id in self._idList ]
        return True


class CStockMotionCommissionInfoList(CInfoList):
    def __init__(self, context, masterId):
        CInfoList.__init__(self, context)
        self._idList = []
        self.masterId = masterId


    def _load(self):
        cond = 'master_id = %d' % self.masterId
        self._idList = QtGui.qApp.db.getIdList('StockMotion_CommissionComposition', 'id', cond, 'idx')
        self._items = [ self.getInstance(CStockMotionCommissionInfo, id) for id in self._idList ]
        return True


class CStockMotionInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id          = id
        self._type       = 0
        self._number     = ''
        self._date       = CDateTimeInfo()
        self._reason     = ''
        self._reasonDate = CDateInfo()
        self._items      = []
        self._commission = []


    def setRecord(self, record):
        if record:
            self.id          = forceInt(record.value('id'))
            from Stock.StockMotion import stockMotionType
            self._type       = stockMotionType[forceInt(record.value('type'))][0]
            self._number     = forceString(record.value('number'))
            self._date       = CDateTimeInfo(forceDateTime(record.value('date')))
            self._invoiceNumber = forceString(record.value('invoiceNumber'))
            self._invoiceDate = CDateInfo(forceDateTime(record.value('invoiceDate')))
            self._reason     = forceString(record.value('reason'))
            self._reasonDate = CDateInfo(forceDate(record.value('reasonDate')))
            self._receiver   = self.getInstance(COrgStructureInfo, forceInt(record.value('receiver_id')))
            self._supplier   = self.getInstance(COrgStructureInfo, forceInt(record.value('supplier_id')))
            self._note       = forceString(record.value('note'))
            self._client     = self.getInstance(CClientInfo, forceInt(record.value('client_id')))
            self._supplierPerson   = self.getInstance(CPersonInfo, forceInt(record.value('supplierPerson_id')))
            self._receiverPerson   = self.getInstance(CPersonInfo, forceInt(record.value('receiverPerson_id')))
            self._supplierOrgPerson = forceString(record.value('supplierOrgPerson'))
            self._supplierOrg   = self.getInstance(COrgInfo, forceInt(record.value('supplierOrg_id')))
            self._items      = self.getInstance(CStockMotionItemInfoList, self.id)
            self._commission = self.getInstance(CStockMotionCommissionInfoList, self.id)
            self.setOkLoaded()


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('StockMotion', '*', self.id) if self.id else None
        if record:
            self.setRecord(record)
            return True
        else:
            self._type       = None
            self._number     = ''
            self._date       = CDateTimeInfo()
            self._invoiceNumber = ''
            self._invoiceDate = CDateInfo()
            self._reason     = ''
            self._reasonDate = CDateInfo()
            self._receiver   = self.getInstance(COrgStructureInfo, None)
            self._supplier   = self.getInstance(COrgStructureInfo, None)
            self._note       = ''
            self._client     = self.getInstance(CClientInfo, None)
            self._supplierPerson    = self.getInstance(CPersonInfo, None)
            self._receiverPerson    = self.getInstance(CPersonInfo, None)
            self._supplierOrgPerson = ''
            self._supplierOrg   = self.getInstance(COrgInfo, None)
            self._items         = self.getInstance(CStockMotionItemInfoList, None)
            self._commission    = self.getInstance(CStockMotionCommissionInfoList, None)
            return False


    def getNomenclatureItem(self, nomecnlatureId):
        for item in self._items:
            if item._nomenclature.id == nomecnlatureId:
                return item
        return None


 #  def __str__(self):
 #     return self.load()._name

    type = property(lambda self: self.load()._type)
    number = property(lambda self: self.load()._number)
    date = property(lambda self: self.load()._date)
    invoiceNumber = property(lambda self: self.load()._invoiceNumber)
    invoiceDate = property(lambda self: self.load()._invoiceDate)
    reason = property(lambda self: self.load()._reason)
    reasonDate = property(lambda self: self.load()._reasonDate)
    receiver = property(lambda self: self.load()._receiver)
    supplier = property(lambda self: self.load()._supplier)
    note = property(lambda self: self.load()._note)
    client = property(lambda self: self.load()._client)
    supplierPerson = property(lambda self: self.load()._supplierPerson)
    receiverPerson = property(lambda self: self.load()._receiverPerson)
    supplierOrgPerson = property(lambda self: self.load()._supplierOrgPerson)
    supplierOrg = property(lambda self: self.load()._supplierOrg)
    items = property(lambda self: self.load()._items)


class CStockMotionInfoList(CInfoList):
    def __init__(self,  context, idList):
        CInfoList.__init__(self, context)
        self._idList = idList

    def _load(self):
        self._items = [ self.getInstance(CStockMotionInfo, id) for id in self._idList ]
        return True

# WTF?
class CStockRemainingsInfo(CInfo):
    def __init__(self, context, record):
        CInfo.__init__(self, context)
        self.record = record


    def setRecord(self, record):
        if record:
            self._orgStructure = self.getInstance(COrgStructureInfo, forceInt(record.value('orgStructure_id')))
            self._nomenclature = self.getInstance(CNomenclatureInfo, forceRef(record.value('nomenclature_id')))
            self._batch        = forceString(record.value('batch'))
            self._qnt          = forceDouble(record.value('qnt'))
            self._shelfTime    = CDateInfo(forceDate(record.value('shelfTime')))
            self._finance      = self.getInstance(CFinanceInfo, forceRef(record.value('finance_id')))
            self._unit         = self.getInstance(CUnitInfo, forceInt(record.value('unitId')))
            self._sum          = forceDouble(record.value('sum'))
            self.setOkLoaded()


    def _load(self):
        if self.record:
            self.setRecord(self.record)
            return True
        else:
            return False


    orgStructure = property(lambda self: self.load()._orgStructure)
    nomenclature = property(lambda self: self.load()._nomenclature)
    batch = property(lambda self: self.load()._batch)
    qnt = property(lambda self: self.load()._qnt)
    shelfTime = property(lambda self: self.load()._shelfTime)
    finance = property(lambda self: self.load()._finance)
    unit = property(lambda self: self.load()._unit)
    sum = property(lambda self: self.load()._sum)


class CStockRemainingsInfoList(CInfoList):
    def __init__(self,  context, records):
        CInfoList.__init__(self, context)
        self._class = CStockRemainingsInfo
        self._records = records

    def _load(self):
        self._items = [ self.getInstance(self._class, record) for record in self._records ]
        return True


# WFT?
class CStockRequisitionsItemInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id


    def setRecord(self, record):
        self._nomenclature = self.getInstance(CNomenclatureInfo, forceRef(record.value('nomenclature_id')))
        self._finance      = self.getInstance(CFinanceInfo, forceRef(record.value('finance_id')))
        self._qnt          = forceDouble(record.value('qnt'))
        self._satisfiedQnt = forceDouble(record.value('satisfiedQnt'))
        self._unit         = self.getInstance(CUnitInfo, forceRef(record.value('unit_id')))
        return self


    def setOkLoaded(self):
        CInfo.setOkLoaded(self)
        return self


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('StockRequisition_Item', '*', self.id) if self.id else None
        if record:
            self.setRecord(record)
            return True
        else:
            return False

    nomenclature = property(lambda self: self.load()._nomenclature)
    finance = property(lambda self: self.load()._finance)
    qnt = property(lambda self: self.load()._qnt)
    satisfiedQnt = property(lambda self: self.load()._satisfiedQnt)
    unit = property(lambda self: self.load()._unit)


class CStockRequisitionsItemInfoList(CInfoList):
    def __init__(self,  context, parentId):
        CInfoList.__init__(self, context)
        self._idList = []
        self._parentId = parentId


    def _load(self):
        self._idList = QtGui.qApp.db.getDistinctIdList('StockRequisition_Item', where='master_id=%i'%self._parentId)
        self._items = [ self.getInstance(CStockRequisitionsItemInfo, id) for id in self._idList ]
        return True

# WFT!!!
class CStockRequisitionsInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id
        self.motionsIdList = []
        motionRecords = getMotionRecordsByRequisition(id)
        for record in motionRecords:
            self.motionsIdList.append(forceInt(record.value('id')))
        self._items = []
        self._motions = []


    def setRecord(self, record):
        if record:
            self._number     = forceString(record.value('number'))
            self._date       = CDateTimeInfo(forceDateTime(record.value('date')))
            self._deadline   = CDateTimeInfo(forceDateTime(record.value('deadline')))
            self._receiver   = self.getInstance(COrgStructureInfo, forceInt(record.value('recipient_id')))
            self._recipientPerson   = self.getInstance(CPersonInfo, forceInt(record.value('recipientPerson_id')))
            self._supplier   = self.getInstance(COrgStructureInfo, forceInt(record.value('supplier_id')))
            self._note       = forceString(record.value('note'))
            self._items      = self.getInstance(CStockRequisitionsItemInfoList, self.id)
            self._motions    = self.getInstance(CStockMotionInfoList, self.motionsIdList)
            self._agreementDate   = CDateTimeInfo(forceDate(record.value('agreementDate')))
            self._agreementPerson = self.getInstance(CPersonInfo, forceInt(record.value('agreementPerson_id')))
            self._agreementStatus = forceInt(record.value('agreementStatus'))
            self._agreementNote   = forceString(record.value('agreementNote'))
            self.setOkLoaded()


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('StockRequisition', '*', self.id) if self.id else None
        if record:
            self.setRecord(record)
            return True
        else:
            self._number = u''
            self._date = CDateTimeInfo()
            self._deadline = CDateTimeInfo()
            self._receiver = self.getInstance(COrgStructureInfo, None)
            self._recipientPerson   = self.getInstance(CPersonInfo, None)
            self._supplier = self.getInstance(COrgStructureInfo, None)
            self._note     = u''
            self._items    = []
            self._motions  = []
            self._agreementDate   = CDateTimeInfo()
            self._agreementPerson = self.getInstance(CPersonInfo, None)
            self._agreementStatus = 0
            self._agreementNote   = ''
            return False


    number = property(lambda self: self.load()._number)
    date = property(lambda self: self.load()._date)
    deadline = property(lambda self: self.load()._deadline)
    receiver = property(lambda self: self.load()._receiver)
    recipientPerson = property(lambda self: self.load()._recipientPerson)
    supplier = property(lambda self: self.load()._supplier)
    note = property(lambda self: self.load()._note)
    items = property(lambda self: self.load()._items)
    motions = property(lambda self: self.load()._motions)
    agreementDate = property(lambda self: self.load()._agreementDate)
    agreementPerson = property(lambda self: self.load()._agreementPerson)
    agreementStatus = property(lambda self: self.load()._agreementStatus)
    agreementNote = property(lambda self: self.load()._agreementNote)


class CStockRequisitionsInfoList(CInfoList):
    def __init__(self, context, idList):
        CInfoList.__init__(self, context)
        self._idList = idList


    def _load(self):
        self._items = [ self.getInstance(CStockRequisitionsInfo, id) for id in self._idList ]
        return True


class CNomenclatureUsingTypeInfo(CRBInfoWithIdentification):
    tableName = 'rbNomenclatureUsingType'


class CNomenclatureTypeInfo(CRBInfo):
    tableName = 'rbNomenclatureType'


# Какое скверное имя таблицы :(
# rbLfForm - это «Формы выпуска лекарственных препаратов»
# должно быть rbDosageForm
class CLFFormInfo(CRBInfo):
    tableName = 'rbLfForm'

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord(self.tableName, '*', self.id) if self.id else None
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._dosage = forceStringEx(record.value('dosage'))
            self._isESKLP = forceInt(record.value('isESKLP'))
            self._initByRecord(record)
            return True
        else:
            self._code = ''
            self._name = ''
            self._dosage = ''
            self._isESKLP = 0
            self._initByNull()
            return False


    code = property(lambda self: self.load()._code)
    name = property(lambda self: self.load()._name)
    dosage  = property(lambda self: self.load()._dosage)
    isESKLP = property(lambda self: self.load()._isESKLP)


class CNomenclatureInfo(CRBInfoWithIdentification):
    tableName = 'rbNomenclature'

    def _initByRecord(self, record):
        id = forceRef(record.value('id'))
        self._RegionalCode                     = forceString(record.value('regionalCode'))
        self._type                             = self.getInstance(CNomenclatureTypeInfo, forceRef(record.value('type_id')))
        self._internationalNonproprietaryName  = forceString(record.value('internationalNonproprietaryName'))
        self._russianTradeName                 = forceString(record.value('russianTradeName'))
        self._latinTradeName                   = forceString(record.value('latinTradeName'))
        self._producer                         = forceString(record.value('producer'))
        self._ATC                              = forceString(record.value('ATC'))
        self._packSize                         = forceInt(record.value('packSize'))
        self._mnnCode                          = forceString(record.value('mnnCode'))
        self._mnnLatin                         = forceString(record.value('mnnLatin'))
        self._originName                       = forceString(record.value('originName'))
        self._trnCode                          = forceString(record.value('trnCode'))
        self._dosageValue                      = forceString(record.value('dosageValue'))
        self._dosageUnit                       = self.getInstance(CUnitInfo,  forceRef(record.value('unit_id')))
        self._lfForm                           = self.getInstance(CLFFormInfo, forceRef(record.value('lfForm_id')))
        self._inDate                           = CDateInfo(forceDate(record.value('inDate')))
        self._exDate                           = CDateInfo(forceDate(record.value('exDate')))
        self._completeness                     = forceString(record.value('completeness'))
        self._features                         = getFeaturesAndValues(nomenclatureId=record.value('id'))
        self._analogues                        = [] # эта строчка вешает экспорт счетов по ковиду self.getAnalogues(nomenclatureId=id, analogId=forceInt(record.value('analog_id')))
        self._note                             = forceString(record.value('note'))
        self._composition                      = self.getInstance(CNomenclatureCompositionInfoList, id)


    def _initByNull(self):
        self._RegionalCode                     = ''
        self._type                             = self.getInstance(CNomenclatureTypeInfo, None)
        self._internationalNonproprietaryName  = ''
        self._russianTradeName                 = ''
        self._latinTradeName                   = ''
        self._producer                         = ''
        self._ATC                              = ''
        self._mnnCode                          = ''
        self._mnnLatin                         = ''
        self._originName                       = ''
        self._trnCode                          = ''
        self._packSize                         = 0
        self._dosageValue                      = ''
        self._dosageUnit                       = self.getInstance(CUnitInfo,  None)
        self._lfForm                           = self.getInstance(CLFFormInfo, None)
        self._inDate                           = CDateInfo()
        self._exDate                           = CDateInfo()
        self._completeness                     = ''
        self._features                         = dict()
        self._analogues                        = []
        self._note                             = ''
        self._composition                      = self.getInstance(CNomenclatureCompositionInfoList, None)


    def getAnalogues(self, nomenclatureId = 0, analogId = 0):
        db = QtGui.qApp.db
        cond = []
        tableNomenclature = db.table('rbNomenclature')

        if nomenclatureId:
            cond.append(tableNomenclature['id'].ne(nomenclatureId))
        if analogId:
            cond.append(tableNomenclature['analog_id'].eq(analogId))

        stmt = db.selectDistinctStmt(tableNomenclature, [tableNomenclature['id']], cond, 'id')
        query = db.query(stmt)
        result = []
        while query.next():
            record = query.record()
            id = forceRef(record.value('id'))
            result.append(self.getInstance(CNomenclatureInfo, id))
        return result


    code                            = property(lambda self: self.load()._code)
    name                            = property(lambda self: self.load()._name)
    RegionalCode                    = property(lambda self: self.load()._RegionalCode)
    type                            = property(lambda self: self.load()._type)
    internationalNonproprietaryName = property(lambda self: self.load()._internationalNonproprietaryName)
    russianTradeName                = property(lambda self: self.load()._russianTradeName)
    latinTradeName                  = property(lambda self: self.load()._latinTradeName)
    producer                        = property(lambda self: self.load()._producer)
    ATC                             = property(lambda self: self.load()._ATC)
    packSize                        = property(lambda self: self.load()._packSize)
    mnnCode                         = property(lambda self: self.load()._mnnCode)
    mnnLatin                        = property(lambda self: self.load()._mnnLatin)
    originName                      = property(lambda self: self.load()._originName)
    trnCode                         = property(lambda self: self.load()._trnCode)
    dosageValue                     = property(lambda self: self.load()._dosageValue)
    dosageUnit                      = property(lambda self: self.load()._dosageUnit)
    unit                            = property(lambda self: self.load()._dosageUnit)
    lfForm                          = property(lambda self: self.load()._lfForm)
    inDate                          = property(lambda self: self.load()._inDate)
    exDate                          = property(lambda self: self.load()._exDate)
    completeness                    = property(lambda self: self.load()._completeness)
    features                        = property(lambda self: self.load()._features)
    analogues                       = property(lambda self: self.load()._analogues)
    note                            = property(lambda self: self.load()._note)
    composition                     = property(lambda self: self.load()._composition)


class CStockPurchaseContractItemInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id


    def setRecord(self, record):
        self._idx            = forceInt(record.value('idx'))
        self._nomenclature   = self.getInstance(CNomenclatureInfo, forceRef(record.value('nomenclature_id')))
        self._RLSInfo        = self.getInstance(CRLSInfo, forceRef(record.value('nomenclature_id')))
        self._batch          = forceString(record.value('batch'))
        self._shelfTime      = CDateInfo(forceDate(record.value('shelfTime')))
        self._comparisonDate = CDateTimeInfo(forceDateTime(record.value('comparisonDate')))
        self._medicalAidKind = self.getInstance(CMedicalAidKindInfo, forceRef(record.value('medicalAidKind_id')))
        self._qnt            = forceDouble(record.value('qnt'))
        self._remainPurchaseQnt = forceDouble(record.value('remainPurchaseQnt'))
        self._unit           = self.getInstance(CUnitInfo, forceRef(record.value('unit_id')))
        self._sum            = forceDouble(record.value('sum'))
        self._smnnUUID       = forceStringEx(record.value('smnnUUID'))
        self._smnn           = self.getInstance(CSmnnInfo, self._smnnUUID)
        self._lfForm         = self.getInstance(CLFFormInfo, forceRef(record.value('lfForm_id')))
        self._note           = forceString(record.value('note'))
        return self


    def setOkLoaded(self):
        CInfo.setOkLoaded(self)
        return self


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('StockPurchaseContract_Item', '*', self.id) if self.id else None
        if record:
            self.setRecord(record)
            return True
        else:
            self._idx            = None
            self._nomenclature   = self.getInstance(CNomenclatureInfo, None)
            self._RLSInfo        = self.getInstance(CRLSInfo, None)
            self._batch          = u''
            self._shelfTime      = CDateInfo()
            self._comparisonDate = CDateTimeInfo()
            self._medicalAidKind = self.getInstance(CMedicalAidKindInfo, None)
            self._qnt            = 0
            self._remainPurchaseQnt = 0
            self._unit           = self.getInstance(CUnitInfo, None)
            self._sum            = 0
            self._smnnUUID       = None
            self._smnn           = self.getInstance(CSmnnInfo, None)
            self._lfForm         = self.getInstance(CLFFormInfo, None)
            self._note           = ''
            return False

    idx = property(lambda self: self.load()._idx)
    nomenclature = property(lambda self: self.load()._nomenclature)
    RLSInfo = property(lambda self: self.load()._RLSInfo)
    batch = property(lambda self: self.load()._batch)
    shelfTime = property(lambda self: self.load()._shelfTime)
    comparisonDate = property(lambda self: self.load()._comparisonDate)
    medicalAidKind = property(lambda self: self.load()._medicalAidKind)
    qnt = property(lambda self: self.load()._qnt)
    remainPurchaseQnt = property(lambda self: self.load()._remainPurchaseQnt)
    unit = property(lambda self: self.load()._unit)
    sum = property(lambda self: self.load()._sum)
    smnnUUID = property(lambda self: self.load()._smnnUUID)
    smnn = property(lambda self: self.load()._smnn)
    lfForm = property(lambda self: self.load()._lfForm)
    note = property(lambda self: self.load()._note)


class CStockPurchaseContractItemInfoList(CInfoList):
    def __init__(self,  context, parentId):
        CInfoList.__init__(self, context)
        self._idList = []
        self._parentId = parentId


    def _load(self):
        self._idList = QtGui.qApp.db.getDistinctIdList('StockPurchaseContract_Item', where='master_id=%i'%self._parentId)
        self._items = [ self.getInstance(CStockPurchaseContractItemInfo, id) for id in self._idList ]
        return True


class CStockPCAdditionallyAgreementInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id


    def setRecord(self, record):
        self._idx    = forceInt(record.value('idx'))
        self._number = forceString(record.value('number'))
        self._date   = CDateTimeInfo(forceDateTime(record.value('date')))
        self._note   = forceString(record.value('note'))
        return self


    def setOkLoaded(self):
        CInfo.setOkLoaded(self)
        return self


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('StockPurchaseContract_AdditionallyAgreement', '*', self.id) if self.id else None
        if record:
            self.setRecord(record)
            return True
        else:
            self._idx            = None
            self._number      = ''
            self._date        = CDateTimeInfo()
            self._note        = ''
            return False

    idx = property(lambda self: self.load()._idx)
    number = property(lambda self: self.load()._number)
    date = property(lambda self: self.load()._date)
    note = property(lambda self: self.load()._note)


class CStockPCAdditionallyAgreementInfoList(CInfoList):
    def __init__(self,  context, parentId):
        CInfoList.__init__(self, context)
        self._idList = []
        self._parentId = parentId


    def _load(self):
        self._idList = QtGui.qApp.db.getDistinctIdList('StockPurchaseContract_AdditionallyAgreement', where='master_id=%i'%self._parentId)
        self._items = [ self.getInstance(CStockPCAdditionallyAgreementInfo, id) for id in self._idList ]
        return True


class CStockPurchaseContractInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id           = id
        self._number      = ''
        self._date        = CDateTimeInfo()
        self._name        = ''
        self._title       = ''
        self._supplierOrg =  None
        self._begDate     = CDateInfo()
        self._endDate     = CDateInfo()
        self._finance     =  None
        self._financeSource = self.getInstance(CFinanceSourceInfo, None)
        self._isState     = 0
        self._confirmationOrder = 0
        self._items       = []
        self._additionallyAgreement = []
        self._type       = 0
        self._reason     = ''
        self._reasonDate = CDateInfo()
        self._type       = None
        self._receiver   = self.getInstance(COrgStructureInfo, None)
        self._supplier   = self.getInstance(COrgStructureInfo, None)
        self._note       = ''
        self._supplierPerson   = self.getInstance(CPersonInfo, None)
        self._receiverPerson   = self.getInstance(CPersonInfo, None)
        self._supplierOrgPerson = ''


    def setRecord(self, record):
        if record:
            self.id           = forceRef(record.value('id'))
            self._number      = forceString(record.value('number'))
            self._date        = CDateTimeInfo(forceDateTime(record.value('date')))
            self._name        = forceString(record.value('name'))
            self._title       = forceString(record.value('title'))
            self._supplierOrg =  self.getInstance(COrgInfo, forceInt(record.value('supplierOrg_id')))
            self._begDate     = CDateInfo(forceDate(record.value('begDate')))
            self._endDate     = CDateInfo(forceDate(record.value('endDate')))
            self._finance     = self.getInstance(CFinanceInfo, forceRef(record.value('finance_id')))
            self._financeSource = self.getInstance(CFinanceSourceInfo, forceRef(record.value('financeSource_id')))
            self._isState     = forceInt(record.value('isState'))
            self._confirmationOrder = forceInt(record.value('confirmationOrder'))
            self._type       = forceInt(record.value('type'))
            self._reason     = forceString(record.value('reason'))
            self._reasonDate = CDateInfo(forceDate(record.value('reasonDate')))
            self._receiver   = self.getInstance(COrgStructureInfo, forceInt(record.value('receiver_id')))
            self._supplier   = self.getInstance(COrgStructureInfo, forceInt(record.value('supplier_id')))
            self._note       = forceString(record.value('note'))
            self._supplierPerson   = self.getInstance(CPersonInfo, forceInt(record.value('supplierPerson_id')))
            self._receiverPerson   = self.getInstance(CPersonInfo, forceInt(record.value('receiverPerson_id')))
            self._supplierOrgPerson = forceString(record.value('supplierOrgPerson'))
            self._items      = self.getInstance(CStockPurchaseContractItemInfoList, self.id)
            self._additionallyAgreement = self.getInstance(CStockPCAdditionallyAgreementInfoList, self.id)
            self.setOkLoaded()


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('StockPurchaseContract', '*', self.id) if self.id else None
        if record:
            self.setRecord(record)
            return True
        else:
            return False


    def getNomenclatureItem(self, nomecnlatureId):
        for item in self._items:
            if item._nomenclature.id == nomecnlatureId:
                return item
        return None

    number = property(lambda self: self.load()._number)
    date = property(lambda self: self.load()._date)
    name = property(lambda self: self.load()._name)
    title = property(lambda self: self.load()._title)
    supplierOrg = property(lambda self: self.load()._supplierOrg)
    begDate = property(lambda self: self.load()._begDate)
    endDate = property(lambda self: self.load()._endDate)
    finance = property(lambda self: self.load()._finance)
    financeSource = property(lambda self: self.load()._financeSource)
    isState = property(lambda self: self.load()._isState)
    confirmationOrder = property(lambda self: self.load()._confirmationOrder)
    type = property(lambda self: self.load()._type)
    reason = property(lambda self: self.load()._reason)
    reasonDate = property(lambda self: self.load()._reasonDate)
    receiver = property(lambda self: self.load()._receiver)
    supplier = property(lambda self: self.load()._supplier)
    note = property(lambda self: self.load()._note)
    supplierPerson = property(lambda self: self.load()._supplierPerson)
    receiverPerson = property(lambda self: self.load()._receiverPerson)
    supplierOrgPerson = property(lambda self: self.load()._supplierOrgPerson)
    items = property(lambda self: self.load()._items)
    additionallyAgreement = property(lambda self: self.load()._additionallyAgreement)


class CStockPurchaseContractInfoList(CInfoList):
    def __init__(self,  context, idList):
        CInfoList.__init__(self, context)
        self._class = CStockPurchaseContractInfo
        self._idList = idList

    def _load(self):
        self._items = [ self.getInstance(self._class, id) for id in self._idList ]
        return True


class CNomenclatureActiveSubstanceInfo(CRBInfoWithIdentification):
    tableName = 'rbNomenclatureActiveSubstance'

    def setRecord(self, record):
        if record:
            self._code     = forceString(record.value('code'))
            self._name     = forceString(record.value('name'))
            self._mnnLatin = forceString(record.value('mnnLatin'))
            self._unit     = self.getInstance(CUnitInfo, forceRef(record.value('unit_id')))
            self.setOkLoaded()


    def _load(self):
        db = QtGui.qApp.db
        cols = '`code`, `name`, `mnnLatin`, `unit_id`'
        record = db.getRecord('rbNomenclatureActiveSubstance', cols, self.id) if self.id else None
        if record:
            self.setRecord(record)
            return True
        else:
            self._code      = u''
            self._name      = u''
            self._mnnLatin  = u''
            self._unit      = self.getInstance(CUnitInfo, None)
            return False

    # code и name наследованы от CRBInfo
    mnnLatin = property(lambda self: self.load()._mnnLatin)
    unit     = property(lambda self: self.load()._unit)


class CNomenclatureCompositionInfoList(CInfoList):
    def __init__(self, context, masterId):
        CInfoList.__init__(self, context)
        self._masterId = masterId


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('rbNomenclature_Composition')
        idList = db.getIdList(table, where=table['master_id'].eq(self._masterId))
        self._items = [ self.getInstance(CNomenclatureCompositionInfo, id) for id in idList ]
        return True


class CNomenclatureCompositionInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id


    def _load(self):
        record = QtGui.qApp.db.getRecord('rbNomenclature_Composition', '*', self.id)
        if record:
            self._idx = forceInt(record.value('idx'))
            self._type = forceInt(record.value('type'))
            self._activeSubstance = self.getInstance(CNomenclatureActiveSubstanceInfo,
                                        forceRef(record.value('activeSubstance_id')))
            return True
        else:
            self._idx = None
            self._type = None
            self._activeSubstance = self.getInstance(CNomenclatureActiveSubstanceInfo, None)
            return False

    idx = property(lambda self: self.load()._idx)
    type = property(lambda self: self.load()._type)
    activeSubstance = property(lambda self: self.load()._activeSubstance)


class CDisposalMethodInfo(CRBInfo):
    tableName = 'rbDisposalMethod'
