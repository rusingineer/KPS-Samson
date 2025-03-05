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
from library.PrintInfo               import (
                                             CInfo,
                                             CTemplatableInfoMixin,
                                             CInfoList,
                                             CInfoProxyList,
                                             CDateInfo,
                                             CDateTimeInfo,
                                             CRBInfo,
                                             CRBInfoWithIdentification,
                                             CTimeInfo,
                                            )
from library.Utils import (
    forceBool,
    forceDate,
    forceDateTime,
    forceDouble,
    forceInt,
    forceRef,
    forceString,
    forceStringEx,
    forceTime,
    formatSex,
    formatServiceArea,
    formatAttachOrg, calcAgeTuple, formatAgeTuple, getExSubclassItemLastName,
)
from Events.ActionInfo import CActionInfoList, CPropertyInfo
from RefBooks.AccountExportFormat.Info  import CAccountExportFormatInfo
from Events.TempInvalidInfo          import CTempInvalidInfoList, CTempInvalidPatronageInfoList
from Events.ContractTariffCache import CContractTariffCache
from RefBooks.Service.Info           import CServiceInfo
from Events.MKBInfo    import CMKBInfo
from Events.MesInfo    import CMesInfo
from Events.Utils      import recordAcceptable, getEventShowTime, getActionDispansPhase, CCSGInfo, getEventDuration
from Orgs.PersonInfo                 import CPersonInfo, CPersonInfoList
from Orgs.Utils        import COrgInfo, COrgStructureInfo
from Registry.Utils                  import (
                                             CClientInfo,
                                             CClientDocumentInfo,
                                             CQuotaTypeInfo,
                                             CRBPolicyTypeInfo,
                                             CAddressInfo,
                                            )
from Registry.ClientDocumentTracking import CDocumentLocationInfo
from RefBooks.EventTypePurpose.Info  import CEventTypePurposeInfo
from RefBooks.Finance.Info           import CFinanceInfo
from RefBooks.MedicalAidKind.Info    import CMedicalAidKindInfo
from RefBooks.MedicalAidType.Info    import CMedicalAidTypeInfo
from RefBooks.MedicalAidUnit.Info    import CMedicalAidUnitInfo
from RefBooks.Speciality.Info        import CSpecialityInfo
from RefBooks.Tumor.Info             import CTumorInfo
from RefBooks.VisitType.Info         import CVisitTypeInfo
from RefBooks.DeathPlaceType.Info    import CDeathPlaceTypeInfo
from RefBooks.DeathCauseType.Info    import CDeathCauseTypeInfo
from RefBooks.EmployeeTypeDeterminedDeathCause.Info import CEmployeeTypeDeterminedDeathCauseInfo
from RefBooks.GroundsForDeathCause.Info import CGroundsForDeathCauseInfo

from library.Calendar import wpFiveDays, wpSixDays, wpSevenDays


__all__ = ( 'CActionDispansPhaseInfo',
            'CBankInfo',
            'CCashOperationInfo',
            'CCharacterInfo',
            'CContractInfo',
            'CContractInfoList',
            'CCureMethodInfo',
            'CCureTypeInfo',
            'CDagnosisTypeInfo',
            'CDiagnosisInfo',
            'CDiagnosisInfoList',
            'CDiagnosticInfo',
            'CDiagnosticInfoList',
            'CDiagnosticInfoIdList',
            'CDiagnosticInfoProxyList',
            'CDiagnosticResultInfo',
            'CDispanserInfo',
            'CEmergencyAccidentInfo',
            'CEmergencyBrigadeInfo',
            'CEmergencyCauseCallInfo',
            'CEmergencyDeathInfo',
            'CEmergencyDiseasedInfo',
            'CEmergencyEbrietyInfo',
            'CEmergencyEventInfo',
            'CEmergencyEventInfoList',
            'CEmergencyMethodTransportInfo',
            'CEmergencyPlaceCallInfo',
            'CEmergencyPlaceReceptionCallInfo',
            'CEmergencyReasondDelaysInfo',
            'CEmergencyReceivedCallInfo',
            'CEmergencyResultInfo',
            'CEmergencyTransferTransportInfo',
            'CEmergencyTypeAssetInfo',
            'CEventInfo',
            'CEventInfoList',
            'CEventLocalContractInfo',
            'CEventPaymentInfo',
            'CEventPaymentInfoList',
            'CEventTypeInfo',
            'CHealthGroupInfo',
            'CHospitalInfo',
            'CLocEventInfoList',
            'CMesSpecificationInfo',
            'COrgAccountInfo',
            'CPatientModelInfo',
            'CPhasesInfo',
            'CResultInfo',
            'CSceneInfo',
            'CStageInfo',
            'CTraumaTypeInfo',
            'CToxicSubstancesInfo',
            'CVisitInfo',
            'CVisitInfoList',
            'CVisitInfoListEx',
            'CVisitInfoProxyList',
            'CVisitPersonallInfo',
            'CFeedInfo',
            'CFeedInfoList',
            'CMealTimeInfo',
            'CDietInfo',
            'CAnatomicalLocalizationsInfo',
          )

RowsTemplate = [
                (u'Некоторые инфекционные и паразитарные болезни', u'1', u'A00 - B99'),
                (u'в том числе: туберкулез', u'1.1', u'A15 - A19'),
                (u'Новообразования', u'2', u'C00 - D48'),
	            (u'в том числе: злокачественные новообразования и новообразования in situ', u'2.1', u'C00 - D09'),
                (u'в том числе: пищевода', u'2.2', u'C15, D00.1'),
                (u'из них в 1 - 2 стадии', u'2.2.1', u'C15, D00.1'),
                (u'желудка', u'2.3', u'C16, D00.2'),
                (u'из них в 1 - 2 стадии', u'2.3.1', u'C16, D00.2'),
                (u'ободочной кишки', u'2.4', u'C18, D01.0'),
                (u'из них в 1 - 2 стадии', u'2.4.1', u'C18, D01.0'),
                (u'ректосигмоидного соединения, прямой кишки, заднего прохода (ануса) и анального канала', u'2.5', u'C19 - C21, D01.1 - D01.3'),
                (u'из них в 1 - 2 стадии', u'2.5.1', u'C19 - C21, D01.1 - D01.3'),
                (u'поджелудочной железы', u'2.6', u'C25'),
                (u'из них в 1 - 2 стадии', u'2.6.1', u'C25'),
                (u'трахеи, бронхов и легкого', u'2.7', u'C33, C34, D02.1 - D02.2'),
                (u'из них в 1 - 2 стадии', u'2.7.1', u'C33, C34, D02.1 - D02.2'),
                (u'молочной железы', u'2.8', u'C50, D05'),
                (u'из них в 1 - 2 стадии', u'2.8.1', u'C50, D05'),
                (u'шейки матки', u'2.9', u'C53, D06'),
                (u'из них в 1 - 2 стадии', u'2.9.1', u'C53, D06'),
                (u'тела матки', u'2.10', u'C54'),
                (u'из них в 1 - 2 стадии', u'2.10.1', u'C54'),
                (u'яичника', u'2.11', u'C56'),
                (u'из них в 1 - 2 стадии', u'2.11.1', u'C56'),
                (u'предстательной железы', u'2.12', u'C61, D07.5'),
                (u'из них в 1 - 2 стадии', u'2.12.1', u'C61, D07.5'),
                (u'почки, кроме почечной лоханки', u'2.13', u'C64'),
                (u'из них в 1 - 2 стадии', u'2.13.1', u'C64'),
                (u'Болезни крови, кроветворных органов и отдельные нарушения, вовлекающие иммунный механизм', u'3', u'D50 - D89'),
                (u'в том числе: анемии, связанные с питанием, гемолитические анемии,', u'3.1', u'D50 - D64'),
                (u'апластические и другие анемии', u'', u''), #??????????????????????
                (u'Болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'4', u'E00 - E90'),
                (u'в том числе: сахарный диабет', u'4.2', u'E10 - E14'),
                (u'ожирение', u'2', u'E66'),
                (u'нарушения обмена липопротеинов и другие липидемии', u'4.3', u'E78'),
                (u'Болезни нервной системы', u'5', u'G00 - G99'),
                (u'в том числе: преходящие церебральные ишемические приступы [атаки] и родственные синдромы', u'5.1', u'G45'),
                (u'Болезни глаза и его придаточного аппарата', u'6', u'H00 - H59'),
                (u'в том числе: старческая катаракта и другие катаракты', u'6.1', u'H25, H26'),
                (u'глаукома', u'6.2', u'H40'),
                (u'слепота и пониженное зрение', u'6.3', u'H54'),
                (u'Болезни системы кровообращения', u'7', u'I00 - I99'),
                (u'в том числе: болезни, характеризующиеся повышенным кровяным давлением', u'7.1', u'I10 - I15'),
                (u'ишемическая болезнь сердца', u'7.2', u'I20 - I25'),
                (u'в том числе: стенокардия (грудная жаба)', u'7.2.1', u'I20'),
                (u'в том числе нестабильная стенокардия', u'7.2.2', u'I20.0'),
                (u'хроническая ишемическая болезнь сердца', u'7.2.3', u'I25'),
                (u'в том числе: перенесенный в прошлом инфаркт миокарда', u'7.2.4', u'I25.2'),
                (u'другие болезни сердца', u'7.3', u'I30 - I52'),
                (u'цереброваскулярные болезни', u'7.4', u'I60 - I69'),
                (u'в том числе: закупорка и стеноз прецеребральных артерий, не приводящие к инфаркту мозга и закупорка и стеноз церебральных артерий, не приводящие к инфаркту мозга', u'7.4.1', u'I65, I66'),
                (u'другие цереброваскулярные болезни', u'7.4.2', u'I67'),
                (u'последствия субарахноидального кровоизлияния, последствия внутричерепного кровоизлияния, последствия другого нетравматического внутричерепного кровоизлияния, последствия инфаркта мозга, последствия инсульта, не уточненные как кровоизлияние или инфаркт мозга', u'7.4.3', u'I69.0 - I69.4'),
                (u'аневризма брюшной аорты', u'7.4.4', u'I71.3 - I71.4'),
                (u'Болезни органов дыхания', u'8', u'J00 - J98'),
                (u'в том числе: вирусная пневмония, пневмония, вызванная Streptococcus pneumonia, пневмония, вызванная Haemophilus influenza, бактериальная пневмония, пневмония, вызванная другими инфекционными возбудителями, пневмония при болезнях, классифицированных в других рубриках, пневмония без уточнения возбудителя', u'8.1', u'J12 - J18'),
                (u'бронхит, не уточненный как острый и хронический, простой и слизисто-гнойный хронический бронхит, хронический бронхит неуточненный, эмфизема', u'8.2', u'J40 - J43'),
                (u'другая хроническая обструктивная легочная болезнь, астма, астматический статус, бронхоэктатическая болезнь', u'8.3', u'J44 - J47'),
                (u'Болезни органов пищеварения', u'9', u'K00 - K93'),
                (u'в том числе: язва желудка, язва двенадцатиперстной кишки', u'9.1', u'K25, K26'),
                (u'гастрит и дуоденит', u'9.2', u'K29'),
                (u'неинфекционный энтерит и колит', u'9.3', u'K50 - K52'),
                (u'другие болезни кишечника', u'9.4', u'K55 - K63'),
                (u'Болезни мочеполовой системы', u'10', u'N00 - N99'),
                (u'в том числе: гиперплазия предстательной железы, воспалительные болезни предстательной железы, другие болезни предстательной железы', u'10.1', u'N40 - N42'),
                (u'доброкачественная дисплазия молочной железы', u'10.2', u'N60'),
                (u'воспалительные болезни женских тазовых органов', u'10.3', u'N70 - N77'),
                (u'Прочие заболевания', u'11', u'')
                ]

class CMealTimeInfo(CRBInfo):
    tableName = 'rbMealTime'

    def _initByRecord(self, record):
        self._begTime = CTimeInfo( forceTime(record.value('begTime')) )
        self._endTime = CTimeInfo( forceTime(record.value('endTime')) )

    def _initByNone(self):
        self._begTime = CTimeInfo()
        self._endTime = CTimeInfo()


    begtime = property(lambda self: self.load()._begTime)
    endTime = property(lambda self: self.load()._endTime)


class CDietInfo(CRBInfo):
    tableName = 'rbDiet'

    def _initByRecord(self, record):
        self._begDate = CDateInfo( forceDate(record.value('begDate')) )
        self._endDate = CDateInfo( forceDate(record.value('endDate')) )

    begDate = property(lambda self: self.load()._begDate)
    endDate = property(lambda self: self.load()._endDate)


class CFeedInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Event_Feed')
        record = db.getRecordEx(table, '*', [table['id'].eq(self.id), table['deleted'].eq(0)])
        if record:
            self.initByRecord(record)
            return True
        else:
            self.initByRecord(db.dummyRecord())
            return False


    def initByRecord(self, record):
        self._date = CDateInfo(forceDate(record.value('date')))
        self._eventInfo = self.getInstance(CEventInfo, forceRef(record.value('event_id')))
        self._mealTime = self.getInstance(CMealTimeInfo, forceRef(record.value('mealTime_id')))
        self._diet = self.getInstance(CDietInfo, forceRef(record.value('diet_id')))
        self._patron = self.getInstance(CClientInfo, forceRef(record.value('patron_id')))
        self._typeFeed = forceInt(record.value('typeFeed'))
        self._finance = self.getInstance(CFinanceInfo, forceRef(record.value('finance_id')))
        self._featuresToEat = forceString(record.value('featuresToEat'))
        self._refusalToEat = forceBool(record.value('refusalToEat'))

    date          = property(lambda self: self.load()._date)
    eventInfo     = property(lambda self: self.load()._eventInfo)
    mealTime      = property(lambda self: self.load()._mealTime)
    diet          = property(lambda self: self.load()._diet)
    patron        = property(lambda self: self.load()._patron)
    typeFeed      = property(lambda self: self.load()._typeFeed)
    finance       = property(lambda self: self.load()._finance)
    featuresToEat = property(lambda self: self.load()._featuresToEat)
    refusalToEat  = property(lambda self: self.load()._refusalToEat)


class CFeedInfoList(CInfoList):
    def __init__(self, context, eventId):
        CInfoList.__init__(self, context)
        self.eventId = eventId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Event_Feed')
        idList = db.getIdList(table, 'id', [table['event_id'].eq(self.eventId), table['deleted'].eq(0)], 'id')
        self._items = [ self.getInstance(CFeedInfo, id) for id in idList ]
        return True


# ###################################################################################################################



    def _initByRecord(self, record):
            self._purpose = forceInt(record.value('purpose'))


    def _initByNull(self):
            self._purpose = 0


    purpose = property(lambda self: self.load()._purpose)


class CEventProfile(CRBInfo):
    tableName = 'rbEventProfile'

    def _initByRecord(self, record):
        self._code = forceInt(record.value('code'))

    def _initByNull(self):
        self._code = 0

    code = property(lambda self: self.load()._code)


class CEventTypeInfo(CRBInfo):
    tableName = 'EventType'


    def _initByRecord(self, record):
        self._purpose = self.getInstance(CEventTypePurposeInfo, forceRef(record.value('purpose_id')))
        self._finance = self.getInstance(CFinanceInfo, forceRef(record.value('finance_id')))
        self._service = self.getInstance(CServiceInfo, forceRef(record.value('service_id')))
        self._printContext = forceString(record.value('context'))
        self._form = forceString(record.value('form'))
        self._regionalCode = forceString(record.value('regionalCode'))
        self._medicalAidType = self.getInstance(CMedicalAidTypeInfo, forceRef(record.value('medicalAidType_id')))
        self._medicalAidKind = self.getInstance(CMedicalAidKindInfo, forceRef(record.value('medicalAidKind_id')))
        self._eventProfile = self.getInstance(CEventProfile, forceString(record.value('eventProfile_id')))


    def _initByNull(self):
        self._purpose = self.getInstance(CEventTypePurposeInfo, None)
        self._finance = self.getInstance(CFinanceInfo, None)
        self._service = self.getInstance(CServiceInfo, None)
        self._printContext = ''
        self._regionalCode = ''
        self._form = ''
        self._medicalAidType = self.getInstance(CMedicalAidTypeInfo, None)
        self._medicalAidKind = self.getInstance(CMedicalAidKindInfo, None)
        self._eventProfile = self.getInstance(CEventProfile, None)

    purpose = property(lambda self: self.load()._purpose)
    finance = property(lambda self: self.load()._finance)
    service = property(lambda self: self.load()._service)
    form = property(lambda self: self.load()._form)
    medicalAidType = property(lambda self: self.load()._medicalAidType)
    medicalAidKind = property(lambda self: self.load()._medicalAidKind)
    printContext = property(lambda self: self.load()._printContext)
    regionalCode = property(lambda self: self.load()._regionalCode)
    eventProfile = property(lambda self: self.load()._eventProfile)


class CResultInfo(CRBInfo):
    tableName = 'rbResult'

    def _initByRecord(self, record):
        self._continued = forceBool(record.value('continued'))
        self._regionalCode = forceString(record.value('regionalCode'))
        self._federalCode = forceString(record.value('federalCode'))


    def _initByNull(self):
        self._continued = False
        self._regionalCode = self._federalCode = ''

    continued = property(lambda self: self.load()._continued)
    regionalCode = property(lambda self: self.load()._regionalCode)
    federalCode = property(lambda self: self.load()._federalCode)


class CDiagnosticResultInfo(CRBInfoWithIdentification):
    tableName = 'rbDiagnosticResult'

    def _initByRecord(self, record):
        self._regionalCode = forceString(record.value('regionalCode'))
        self._federalCode = forceString(record.value('federalCode'))


    def _initByNull(self):
        self._regionalCode = self._federalCode = ''

    regionalCode = property(lambda self: self.load()._regionalCode)
    federalCode = property(lambda self: self.load()._federalCode)


class CContractInfoList(CInfoList):
    def __init__(self, context, idList):
        CInfoList.__init__(self, context)
        self.idList = idList


    def _load(self):
        self._items = [ self.getInstance(CContractInfo, id) for id in self.idList ]
        return True


class CContractInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('Contract', '*', self.id)
        if record:
            self._number = forceString(record.value('number'))
            self._date = CDateInfo(forceDate(record.value('date')))
            self._begDate = CDateInfo(forceDate(record.value('begDate')))
            self._endDate = CDateInfo(forceDate(record.value('endDate')))
            self._recipient = self.getInstance(COrgInfo, forceRef(record.value('recipient_id')))
            self._recipientAccount = self.getInstance(COrgAccountInfo, forceRef(record.value('recipientAccount_id')))
            self._recipientKBK = forceString(record.value('recipientKBK'))
            self._payer = self.getInstance(COrgInfo, forceRef(record.value('payer_id')))
            self._payerAccount = self.getInstance(COrgAccountInfo, forceRef(record.value('payerAccount_id')))
            self._payerKBK = forceString(record.value('payerKBK'))
            self._finance = self.getInstance(CFinanceInfo, forceRef(record.value('finance_id')))
            self._note = forceString(record.value('note'))
            self._contingent = self.getInstance(CContingentInfoList, self.id)
            self._resolution = forceString(record.value('resolution'))
            self._format = self.getInstance(CAccountExportFormatInfo, forceRef(record.value('format_id')))
            self._attributes = self.getInstance(CAttributesInfoList, self.id)
            self._tariffs = self.getInstance(CTariffInfoList, self.id)
            return True
        else:
            self._number = ''
            self._date = CDateInfo()
            self._begDate = CDateInfo()
            self._endDate = CDateInfo()
            self._recipient = self.getInstance(COrgInfo, None)
            self._recipientAccount = self.getInstance(COrgAccountInfo, None)
            self._recipientKBK = ''
            self._payer = self.getInstance(COrgInfo, None)
            self._payerAccount = self.getInstance(COrgAccountInfo, None)
            self._payerKBK = ''
            self._finance = self.getInstance(CFinanceInfo, None)
            self._note = ''
            self._contingent = self.getInstance(CContingentInfoList, None)
            self._resolution  = ''
            self._format = self.getInstance(CAccountExportFormatInfo, None)
            self._attributes = self.getInstance(CAttributesInfoList, None)
            self._tariffs = self.getInstance(CTariffInfoList, None)
            return False


    def __str__(self):
        self.load()
        return self._number + ' ' + self._date

    number           = property(lambda self: self.load()._number)
    date             = property(lambda self: self.load()._date)
    begDate          = property(lambda self: self.load()._begDate)
    endDate          = property(lambda self: self.load()._endDate)
    recipient        = property(lambda self: self.load()._recipient)
    recipientAccount = property(lambda self: self.load()._recipientAccount)
    recipientKBK     = property(lambda self: self.load()._recipientKBK)
    payer            = property(lambda self: self.load()._payer)
    payerAccount     = property(lambda self: self.load()._payerAccount)
    payerKBK         = property(lambda self: self.load()._payerKBK)
    finance          = property(lambda self: self.load()._finance)
    note             = property(lambda self: self.load()._note)
    contingent   = property(lambda self: self.load()._contingent)
    resolution           = property(lambda self: self.load()._resolution)
    format = property(lambda self: self.load()._format)
    attributes = property(lambda self: self.load()._attributes)
    tariffs = property(lambda self: self.load()._tariffs)


class CTariffInfoList(CInfoList):
    def __init__(self, context, masterId):
        CInfoList.__init__(self, context)
        self.masterId = masterId


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Contract_Tariff')
        idList = db.getIdList(table, 'id', [table['master_id'].eq(self.masterId), table['deleted'].eq(0)], 'id')
        self._items = [ self.getInstance(CTariffInfo, id) for id in idList ]
        return True


class CTariffInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('Contract_Tariff', '*', self.id)
        if record:
            self._price = forceDouble(record.value('price'))
            self._service = self.getInstance(CServiceInfo, forceRef(record.value('service_id')))
            self._batch = forceString(record.value('batch'))
            self._vat = forceDouble(record.value('VAT'))
            self._age = forceString(record.value('age'))
            self._sex = forceString(record.value('sex'))
            self._unit = self.getInstance(CMedicalAidUnitInfo, forceRef(record.value('unit_id')))
            return True
        else:
            self._value = None
            self._service = self.getInstance(CServiceInfo, None)
            self._batch = None
            self._vat = None
            self._age = None
            self._sex = None
            self._unit = self.getInstance(CMedicalAidUnitInfo, None)
            return False

    price          = property(lambda self: self.load()._price)
    service       = property(lambda self: self.load()._service)
    batch          = property(lambda self: self.load()._batch)
    vat              = property(lambda self: self.load()._vat)
    age            = property(lambda self: self.load()._age)
    sex            = property(lambda self: self.load()._sex)
    unit            = property(lambda self: self.load()._unit)

class CContingentInfoList(CInfoList):
    def __init__(self, context, masterId):
        CInfoList.__init__(self, context)
        self.masterId = masterId


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Contract_Contingent')
        idList = db.getIdList(table, 'id', [table['master_id'].eq(self.masterId), table['deleted'].eq(0)], 'id')
        self._items = [ self.getInstance(CContingentInfo, id) for id in idList ]
        return True


class CContingentInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('Contract_Contingent', '*', self.id)
        if record:
            self._attachType = self.getInstance(CAttachTypeInfo, forceRef(record.value('attachType_id')))
            self._attachOrg = formatAttachOrg(forceInt(record.value('attachOrg')))
            self._org = self.getInstance(COrgInfo, forceRef(record.value('org_id')))
            self._socStatusType = self.getInstance(CSocStatusType, forceRef(record.value('attachType_id')))
            self._insurer = self.getInstance(COrgInfo, forceRef(record.value('insurer_id')))
            self._policyType = self.getInstance(CRBPolicyTypeInfo, forceRef(record.value('policyType_id')))
            self._serviceArea = formatServiceArea(forceInt(record.value('serviceArea')))
            self._sex = formatSex(forceInt(record.value('sex')))
            self._age = forceString(record.value('age'))
            return True
        else:
            self._attachType = self.getInstance(CAttachTypeInfo, None)
            self._attachOrg = 0
            self._org = self.getInstance(COrgInfo, None)
            self._socStatusType = self.getInstance(CSocStatusType, None)
            self._insurer = self.getInstance(COrgInfo, None)
            self._policyType = self.getInstance(CRBPolicyTypeInfo, None)
            self._serviceArea = 0
            self._sex = 0
            self._age = u''
            return False


    attachType           = property(lambda self: self.load()._attachType)
    attachOrg             = property(lambda self: self.load()._attachOrg)
    org          = property(lambda self: self.load()._org)
    socStatusType          = property(lambda self: self.load()._socStatusType)
    insurer        = property(lambda self: self.load()._insurer)
    policyType = property(lambda self: self.load()._policyType)
    serviceArea     = property(lambda self: self.load()._serviceArea)
    sex            = property(lambda self: self.load()._sex)
    age     = property(lambda self: self.load()._age)


class CAttributesInfoList(CInfoList):
    def __init__(self, context, masterId):
        CInfoList.__init__(self, context)
        self.masterId = masterId


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Contract_Attribute')
        idList = db.getIdList(table, 'id', [table['master_id'].eq(self.masterId), table['deleted'].eq(0)], 'id')
        self._items = [ self.getInstance(CAttributesInfo, id) for id in idList ]
        return True


class CAttributesInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('Contract_Attribute', '*', self.id)
        if record:
            self._attributeType = self.getInstance(CContractAttributeTypeInfo, forceRef(record.value('attributeType_id')))
            self._begDate = CDateInfo(forceDate(record.value('begDate')))
            self._value = forceString(record.value('value'))
            return True
        else:
            self._attributeType = self.getInstance(CContractAttributeTypeInfo, None)
            self._begDate = CDateInfo(None)
            self._value = u''
            return False


    attributeType           = property(lambda self: self.load()._attributeType)
    begDate             = property(lambda self: self.load()._begDate)
    value          = property(lambda self: self.load()._value)


class CContractAttributeTypeInfo(CRBInfo):
    tableName = 'rbContractAttributeType'


class CAttachTypeInfo(CRBInfo):
    tableName = 'rbAttachType'


class CSocStatusType(CRBInfoWithIdentification):
    tableName = 'rbSocStatusType'


class COrgAccountInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('Organisation_Account', '*', self.id)
        if record:
            self._org = self.getInstance(COrgInfo, forceRef(record.value('organisation_id')))
            self._bankName = forceString(record.value('bankName'))
            self._name = forceString(record.value('name'))
            self._notes = forceString(record.value('notes'))
            self._bank = self.getInstance(CBankInfo, forceRef(record.value('bank_id')))
            self._cash = forceBool(record.value('cash'))
            return True
        else:
            self._org = self.getInstance(COrgInfo, None)
            self._bankName = ''
            self._name = ''
            self._notes = ''
            self._bank = self.getInstance(CBankInfo, None)
            self._cash = False
            return False


    def __str__(self):
        self.load()
        return self._name

    organisation = property(lambda self: self.load()._org)
    org          = property(lambda self: self.load()._org)
    bankName     = property(lambda self: self.load()._bankName)
    name         = property(lambda self: self.load()._name)
    notes        = property(lambda self: self.load()._notes)
    bank         = property(lambda self: self.load()._bank)
    cash         = property(lambda self: self.load()._cash)


class CBankInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('Bank', '*', self.id)
        if record:
            self._BIK = forceString(record.value('BIK'))
            self._name = forceString(record.value('name'))
            self._branchName = forceString(record.value('branchName'))
            self._corrAccount = forceString(record.value('corrAccount'))
            self._subAccount = forceString(record.value('subAccount'))
            return True
        else:
            self._BIK = ''
            self._name = ''
            self._branchName = ''
            self._corrAccount = ''
            self._subAccount = ''
            return False


    def __str__(self):
        self.load()
        return self._name

    BIK        = property(lambda self: self.load()._BIK)
    name       = property(lambda self: self.load()._name)
    branchName = property(lambda self: self.load()._branchName)
    corrAccount= property(lambda self: self.load()._corrAccount)
    subAccount = property(lambda self: self.load()._subAccount)


class CRBInfoWithRegionalCode(CRBInfo):
    def _initByRecord(self, record):
        self._regionalCode = forceString(record.value('regionalCode'))


    def _initByNull(self):
        self._regionalCode = ''


class CMesSpecificationInfo(CRBInfoWithRegionalCode):
    tableName = 'rbMesSpecification'


    def _initByRecord(self, record):
        CRBInfoWithRegionalCode._initByRecord(self, record)
        self._level = forceInt(record.value('level'))


    def _initByNull(self):
        CRBInfoWithRegionalCode._initByNull(self)
        self._level = 0


    level = property(lambda self: self.load()._level)
    done  = property(lambda self: self.load()._level == 2)


class CPatientModelInfo(CRBInfo):
    tableName = 'rbPatientModel'


    def _initByRecord(self, record):
        self._MKB = self.getInstance(CMKBInfo, forceString(record.value('MKB')))
        self._quotaType = self.getInstance(CQuotaTypeInfo, forceRef(record.value('quotaType_id')))


    def _initByNull(self):
        self._MKB = self.getInstance(CMKBInfo, None)
        self._quotaType = self.getInstance(CQuotaTypeInfo, None)


    MKB       = property(lambda self: self.load()._MKB)
    quotaType = property(lambda self: self.load()._quotaType)


class CCureTypeInfo(CRBInfoWithRegionalCode):
    tableName = 'rbCureType'



class CCureMethodInfo(CRBInfoWithRegionalCode):
    tableName = 'rbCureMethod'


#WTF?
class CActionDispansPhaseInfo(CInfoList):
    def __init__(self, context, id, phase=0):
        CInfoList.__init__(self, context)
        self.id = id
        self.phase = phase
        self.row2Name = {}
        self.mapNumMesVisitCode2Row = {}


    def getCodeRowToPhase(self):
        if self.phase == 1:
            self.mapNumMesVisitCode2Row = {
                        u'1': [1],
                        u'3': [2],
                        u'2': [3],
                        u'4': [4],
                        u'5': [5],
                        u'6': [6],
                        u'86':[7],
                        u'15':[8],
                        u'18':[9],
                        u'14':[10],
                        u'19':[11],
                        u'8': [12],
                        u'9': [13],
                        u'11':[14],
                        u'10':[15],
                        u'12':[16],
                        u'87':[17],
                        u'13':[18],
                        u'7': [19],
                        u'17':[20]
                        }
            self.row2Name = {
                        1: u'Опрос(анкетирование), направленный на выявление хронических неинфекционных заболеваний, факторов риска их развития, потребления наркотических средств и психотропных веществ без назначения врача',
                        2: u'Антропометрия (измерение роста стоя, массы тела, окружности талии), расчет индекса массы тела',
                        3: u'Измерение артериального давления',
                        4: u'Определение уровня общего холестерина в крови',
                        5: u'Определение уровня глюкозы в крови экспресс-методом',
                        6: u'Определение относительного суммарного сердечно-сосудистого риска',
                        7: u'Определение абсолютного суммарного сердечно-сосудистого риска',
                        8: u'Электрокардиография (в покое)',
                        9: u'Осмотр фельдшером (акушеркой), включая взятие мазка (соскоба) с поверхности шейки матки (наружного маточного зева) и цервикального канала на цитологическое исследование',
                        10: u'Флюорография легких',
                        11: u'Маммография обеих молочных желез',
                        12: u'Клинический анализ крови',
                        13: u'Клинический анализ крови развернутый',
                        14: u'Анализ крови биохимический общетерапевтический',
                        15: u'Общий анализ мочи',
                        16: u'Исследование кала на скрытую кровь иммунохимическим методом',
                        17: u'Ультразвуковое исследование (УЗИ) на предмет исключения новообразований органов брюшной полости, малого таза и аневризмы брюшной аорты',
                        18: u'Ультразвуковое исследование (УЗИ) в целях исключения аневризмы брюшной аорты',
                        19: u'Измерение внутриглазного давления',
                        20: u'Прием (осмотр) врача-терапевта'
                        }
        elif self.phase == 2:
            self.mapNumMesVisitCode2Row = {u'55' : [1],
                                           u'44' : [2],
                                           u'56' : [3],
                                           u'50' : [4],
                                           u'45' : [5],
                                           u'46' : [5],
                                           u'58' : [6],
                                           u'53' : [7],
                                           u'90' : [8],
                                           u'48' : [9],
                                           u'54' : [10],
                                           u'91' : [11],
                                           u'92' : [12],
                                           u'47' : [13],
                                           u'52' : [14],
                                           u'59' : [15],
                                           u'17' : [16]
                                          }
            self.row2Name = {
                             1 : u'Дуплексное сканирование брахицефальных артерий',
                             2 : u'Осмотр (консультация) врачом-неврологом',
                             3 : u'Эзофагогастродуоденоскопия ',
                             4 : u'Осмотр (консультация) врачом-хирургом или врачом-урологом',
                             5 : u'Осмотр (консультация) врачом-хирургом или врачом-колопроктологом',
                             6 : u'Колоноскопия или ректороманоскопия',
                             7 : u'Определение липидного спектра крови',
                             8 : u'Спирометрия',
                             9 : u'Осмотр (консультация) врачом-акушером-гинекологом',
                             10: u'Определение концентрации гликированного гемоглобина в крови или тест на толерантность к глюкозе',
                             11: u'Осмотр (консультация) врачом-оториноларингологом',
                             12: u'Анализ крови на уровень содержания простатспецифического антигена',
                             13: u'Осмотр (консультация) врачом-офтальмологом',
                             14: u'Индивидуальное углубленное профилактическое консультирование',
                             15: u'Групповое профилактическое консультирование (школа пациента)',
                             16: u'Прием (осмотр) врача-терапевта'
                            }


    def getDefault(self):
        result = {}
        for key in self.row2Name.keys():
            result[key] = [u'-', u'-', u'-', u'-']
        return result


    def getName(self, num):
        return [self.row2Name.get(num, ''), num]


    def getReportData(self, query):
        self.getCodeRowToPhase()
        reportData = self.getDefault()
        uniqueSet = set()
        db = QtGui.qApp.db
        while query.next():
            record = query.record()
            eventId = forceRef(record.value('eventId'))
            actionId = forceRef(record.value('actionId'))
#            actionTypeName = forceString(record.value('actionTypeName'))
            actionMkb = forceString(record.value('actionMkb'))
#            clientId = forceRef(record.value('clientId'))
            serviceName = forceString(record.value('serviceName'))
            numMesVisitCode = forceString(record.value('numMesVisitCode'))
            actionExecNow = forceInt(record.value('actionExecNow'))
            actionExecPrev = forceInt(record.value('actionExecPrev'))
            actionExecRefusal = forceInt(record.value('actionExecRefusal'))
            propertyEvaluation = forceInt(record.value('propertyEvaluation'))
            endDate = forceDate(record.value('endDate'))
            directionDate = forceDate(record.value('directionDate'))
            if numMesVisitCode not in self.mapNumMesVisitCode2Row:
                continue
            key = (eventId, numMesVisitCode, serviceName)
            if key in uniqueSet:
                continue
            uniqueSet.add(key)
            numCode = self.mapNumMesVisitCode2Row.get(numMesVisitCode, [])
            numCodeKey = numCode[0] if numCode else None
            if numCodeKey not in self.row2Name.keys():
                continue
            data = reportData.get(numCodeKey, [u'-', u'-', u'-', u'-'])
            if eventId and actionId and not actionExecRefusal:
                if actionExecNow:
                    data[0] = u'%s' % db.formatDate(endDate)
                    data[3] = u'%s' % db.formatDate(directionDate)
                elif actionExecPrev:
                    data[2] = u'проведено ранее(%s)' % db.formatDate(endDate)
            elif eventId and actionExecRefusal:
                data[2] = u'отказ(%s)' % db.formatDate(directionDate)
            if actionMkb and actionMkb[0].isalpha() and actionMkb[0].upper() != 'Z':
                data[1] = u'+'
            elif propertyEvaluation:
                data[1] = u'+'
            else:
                data[1] = u'-'
            reportData[numCodeKey] = data
        return reportData


    def _load(self):
        reportData = self.getReportData(getActionDispansPhase(self.id, self.phase) if self.id else None)
        self._items = []
        if reportData:
            for numMesVisitCode, reportLine in reportData.items():
                name = self.getName(numMesVisitCode)
                item = [name[0], name[1]]
                for row, val in enumerate(reportLine):
                    item.append(val)
                self._items.append(item)
            return True
        else:
            self._items = []
            return False


    def _initByRecord(self, record=None):
        pass


    def _initByNull(self):
        pass


    def __str__(self):
        return u'Тут идёт какая-то фигня'

    dispansItems = property(lambda self: self.load()._items)


class CEventInfo(CInfo, CTemplatableInfoMixin):
    def __init__(self, context, id, isExecutionPlan=False):
        CInfo.__init__(self, context)
        self.id = id
        self._clientId = None
        self._localContract = None
        self._contractTariffCache = None
        self._tempInvalidListLoaded = False
        self._clientEvents = []
        self._isDirty = False
        self._actions = self.getInstance(CActionInfoList, None)
        self.isExecutionPlan = isExecutionPlan

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('Event', '*', self.id)
        if record:
            self._clientId = forceRef(record.value('client_id'))
            self._pregnancyWeek = forceInt(record.value('pregnancyWeek'))
            self._eventType = self.getInstance(CEventTypeInfo, forceRef(record.value('eventType_id')))
            self._identify = self.getInstance(CEventIdentificationInfo, forceRef(record.value('eventType_id')))
            self._externalId = forceString(record.value('externalId'))
            self._org = self.getInstance(COrgInfo, forceRef(record.value('org_id')))
            self._relegateOrg = self.getInstance(COrgInfo, forceRef(record.value('relegateOrg_id')))
            self._relegatePerson = self.getInstance(CPersonInfo, forceRef(record.value('relegatePerson_id')))
            self._client = self.getInstance(CClientInfo, forceRef(record.value('client_id')))
            self._contract = self.getInstance(CContractInfo, forceRef(record.value('contract_id')))
            self._prevEventDate = CDateInfo(forceDate(record.value('prevEventDate')))
            self._setDate = CDateTimeInfo(forceDateTime(record.value('setDate')))
            self._setTime = CTimeInfo(forceTime(record.value('setDate')))
            self._setPerson = self.getInstance(CPersonInfo, forceRef(record.value('setPerson_id')))
            self._execDate = CDateTimeInfo(forceDateTime(record.value('execDate')))
            self._execTime = CTimeInfo(forceTime(record.value('execDate')))
            self._execPerson = self.getInstance(CPersonInfo, forceRef(record.value('execPerson_id')))
            self._isPrimary = forceInt(record.value('isPrimary'))
            self._order = forceInt(record.value('order'))
            self._result = self.getInstance(CResultInfo, forceRef(record.value('result_id')))
            self._nextEventDate = CDateInfo(forceDate(record.value('nextEventDate')))
            self._payStatus = forceInt(record.value('payStatus'))
            self._typeAsset = self.getInstance(CEmergencyTypeAssetInfo, forceRef(record.value('typeAsset_id')))
            self._note = self._notes = forceString(record.value('note'))
            self._curator = self.getInstance(CPersonInfo, forceRef(record.value('curator_id')))
            self._assistant = self.getInstance(CPersonInfo, forceRef(record.value('assistant_id')))
            self._actions = self.getInstance(CActionInfoList, self.id, self.isExecutionPlan)
            self._diagnosises = self.getInstance(CDiagnosticInfoList, self.id)
            self._feeds = self.getInstance(CFeedInfoList, self.id)
            self._visits = self.getInstance(CVisitInfoList, self.id)
            self._dispansIPhase = self.getInstance(CActionDispansPhaseInfo, self.id, 1)
            self._dispansIIPhase = self.getInstance(CActionDispansPhaseInfo, self.id, 2)
            self._localContract = self.getInstance(CEventLocalContractInfo, self.id)
            self._mes = self.getInstance(CMesInfo, forceRef(record.value('MES_id')))
            self._mesSpecification = self.getInstance(CMesSpecificationInfo, forceRef(record.value('mesSpecification_id')))
            self._patientModel = self.getInstance(CPatientModelInfo, forceRef(record.value('patientModel_id')))
            self._cureType     = self.getInstance(CCureTypeInfo, forceRef(record.value('cureType_id')))
            self._cureMethod   = self.getInstance(CCureMethodInfo, forceRef(record.value('cureMethod_id')))
            self._prevEvent = self.getInstance(CEventInfo, forceRef(record.value('prevEvent_id')))
            self._tempInvalidList = self.getTempInvalidList()
            self._tempInvalidPatronageList = self.getTempInvalidList(patronage=True)
            self._relative = self.getInstance(CClientInfo, forceRef(record.value('relative_id')))
            self._clientEvents = self.getEventCount(self._clientId)
            self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._csgList = self.getInstance(CCSGInfoList, self.id)
            self._srcDate = CDateInfo(forceDate(record.value('srcDate')))
            self._srcNumber = forceString(record.value('srcNumber'))
            self._documentLocation = self.getInstance(CDocumentLocationInfo, forceInt(record.value('client_id')), forceString(record.value('externalId')))
            self._vouchers = self.getInstance(CVoucherInfoList, self.id)
            self._isClosed = forceBool(record.value('isClosed'))
            return True
        else:
            self._clientId = None
            self._clientEvents = []
            self._pregnancyWeek = 0
            self._eventType = self.getInstance(CEventTypeInfo, None)
            self._identify = self.getInstance(CEventIdentificationInfo, None)
            self._externalId = ''
            self._org = self.getInstance(COrgInfo, None)
            self._relegateOrg = self.getInstance(COrgInfo, None)
            self._relegatePerson = self.getInstance(CPersonInfo, None)
            self._client = self.getInstance(CClientInfo, None)
            self._contract = self.getInstance(CContractInfo, None)
            self._prevEventDate = CDateInfo()
            self._setDate = CDateTimeInfo()
            self._setTime = CTimeInfo()
            self._setPerson = self.getInstance(CPersonInfo, None)
            self._execDate = CDateTimeInfo()
            self._execTime = CTimeInfo()
            self._execPerson = self.getInstance(CPersonInfo, None)
            self._isPrimary = False
            self._order = 0
            self._result = self.getInstance(CResultInfo, None)
            self._nextEventDate = CDateInfo()
            self._payStatus = 0
            self._typeAsset = self.getInstance(CEmergencyTypeAssetInfo, None)
            self._note = self._notes = ''
            self._curator = self.getInstance(CPersonInfo, None)
            self._assistant = self.getInstance(CPersonInfo, None)
            self._actions = self.getInstance(CActionInfoList, None)
            self._diagnosises = self.getInstance(CDiagnosticInfoList, None)
            self._feeds = self.getInstance(CFeedInfoList, None)
            self._visits = self.getInstance(CVisitInfoList, None)
            self._localContract = self.getInstance(CEventLocalContractInfo, None)
            self._dispansIPhase = self.getInstance(CActionDispansPhaseInfo, None)
            self._dispansIIPhase = self.getInstance(CActionDispansPhaseInfo, None)
            self._mes = self.getInstance(CMesInfo, None)
            self._mesSpecification = self.getInstance(CMesSpecificationInfo, None)
            self._patientModel = self.getInstance(CPatientModelInfo, None)
            self._cureType     = self.getInstance(CCureTypeInfo, None)
            self._cureMethod   = self.getInstance(CCureMethodInfo, None)
            self._prevEvent = self.getInstance(CEventInfo, None)
            self._tempInvalidList = {}
            self._tempInvalidPatronageList = {}
            self._relative = self.getInstance(CClientInfo, None)
            self._createDatetime = CDateTimeInfo()
            self._modifyDatetime = CDateTimeInfo()
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._csgList = self.getInstance(CCSGInfoList, None)
            self._srcDate = CDateInfo()
            self._srcNumber = ''
            self._documentLocation = self.getInstance(CDocumentLocationInfo, None, None)
            self._vouchers = self.getInstance(CVoucherInfoList, None)
            self._isClosed = None
            return False


    # tariff checker interface
    def getEventTypeId(self):
        return self.eventType.id

    def getEventCount(self, clientId):
        idList=[]
        cond = []
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        queryTable = tableEvent.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        cond.append(tableEvent['client_id'].eq(clientId))
        cond.append(tableEvent['deleted'].eq(0))
        records = db.getRecordList(queryTable, ['Event.id as eventId'], cond)
        if records:
            for record in records:
                idList.append(forceInt(record.value('eventId')))
        clientEvents = CEventInfoList(self.context, idList)
        clientEvents._load()
        return clientEvents

    def recordAcceptable(self, record):
        client = self.client
        if client:
            return recordAcceptable(client.sexCode, client.ageTuple, record)
        else:
            return True


    def getTariffDescrEx(self, contractId):
        if not self._contractTariffCache:
            self._contractTariffCache = CContractTariffCache()
        return self._contractTariffCache.getTariffDescr(contractId, self)


    def getTariffDescr(self):
        return self.getTariffDescrEx(self.contract.id)


    def getPrintTemplateContext(self):
        return self.eventType.printContext


    def getData(self):
        return { 'event' : self,
                 'client': self.client,
                 'tempInvalid': None
               }


#    def __unicode__(self):
    def __str__(self):
        self.load()
        return unicode(self._eventType)


    def getTempInvalidList(self, begDate=None, endDate=None, clientId = None, types=None, currentTempInvalid = None, patronage=False):
        if self._tempInvalidListLoaded:
            return self._tempInvalidList
        if endDate is None:
            endDate = self._execDate
        if isinstance(endDate, CDateInfo):
            endDate = endDate.date
        if begDate is None:
            begDate = self._setDate
        if isinstance(begDate, CDateInfo):
            begDate = begDate.date
        if clientId is None:
            clientId = self._clientId
        if isinstance(begDate, CDateTimeInfo):
            begDate = begDate.date
        if isinstance(endDate, CDateTimeInfo):
            endDate = endDate.date
        if patronage:
            result = CTempInvalidPatronageInfoList._get(self.context, clientId, begDate, endDate, types)
        else:
            result = CTempInvalidInfoList._get(self.context, clientId, begDate, endDate, types)
        if currentTempInvalid:
            if currentTempInvalid.id:
                for (i, tempInvalid) in enumerate(result):
                    if tempInvalid.id == currentTempInvalid.id:
                        result._items[i] = currentTempInvalid
            else:
                result = result + [currentTempInvalid, ]
        self._invalidListLoaded = True
        self._tempInvalidList = result
        return result


    def getTempInvalidPatronageList(self, begDate=None, endDate=None, clientId=None, types=None, currentTempInvalid=None):
        return self.getTempInvalidList(begDate, endDate, clientId, types, currentTempInvalid, patronage=True)


    pregnancyWeek = property(lambda self: self.load()._pregnancyWeek)
    eventType   = property(lambda self: self.load()._eventType)
    identify   = property(lambda self: self.load()._identify)
    externalId  = property(lambda self: self.load()._externalId)
    org         = property(lambda self: self.load()._org)
    relegateOrg = property(lambda self: self.load()._relegateOrg)
    relegatePerson = property(lambda self: self.load()._relegatePerson)
    client      = property(lambda self: self.load()._client)
    contract    = property(lambda self: self.load()._contract)
    prevEventDate= property(lambda self: self.load()._prevEventDate)
    setDate     = property(lambda self: self.load()._setDate)
    setTime     = property(lambda self: self.load()._setTime)
    setPerson   = property(lambda self: self.load()._setPerson)
    execDate    = property(lambda self: self.load()._execDate)
    execTime    = property(lambda self: self.load()._execTime)
    execPerson  = property(lambda self: self.load()._execPerson)
    isPrimary   = property(lambda self: self.load()._isPrimary)
    order       = property(lambda self: self.load()._order)
    result      = property(lambda self: self.load()._result)
    nextEventDate= property(lambda self: self.load()._nextEventDate)
    payStatus   = property(lambda self: self.load()._payStatus)
    typeAsset   = property(lambda self: self.load()._typeAsset)
    note        = property(lambda self: self.load()._note)
    notes       = property(lambda self: self.load()._notes)
    curator     = property(lambda self: self.load()._curator)
    assistant   = property(lambda self: self.load()._assistant)
    finance     = property(lambda self: self.contract.finance)
    actions     = property(lambda self: self.load()._actions)
    diagnosises = property(lambda self: self.load()._diagnosises)
    feeds       = property(lambda self: self.load()._feeds)
    visits      = property(lambda self: self.load()._visits)
    localContract = property(lambda self: self.load()._localContract)
    eveDispansIIPhase = property(lambda self: self.load()._dispansIIPhase)
    eveDispansIPhase = property(lambda self: self.load()._dispansIPhase)
    mes         = property(lambda self: self.load()._mes)
    mesSpecification = property(lambda self: self.load()._mesSpecification)
    patientModel= property(lambda self: self.load()._patientModel)
    cureType    = property(lambda self: self.load()._cureType)
    cureMethod  = property(lambda self: self.load()._cureMethod)
    prevEvent = property(lambda self: self.load()._prevEvent)
    tempInvalidList = property(lambda self: self.load()._tempInvalidList)
    tempInvalidPatronageList = property(lambda self: self.load()._tempInvalidPatronageList)
    relative      = property(lambda self: self.load()._relative)
    clientEvents      = property(lambda self: self.load()._clientEvents)
    createDatetime      = property(lambda self: self.load()._createDatetime)
    modifyDatetime      = property(lambda self: self.load()._modifyDatetime)
    modifyPerson   = property(lambda self: self.load()._modifyPerson)
    createPerson   = property(lambda self: self.load()._createPerson)
    csgList = property(lambda self: self.load()._csgList)
    srcDate = property(lambda self: self.load()._srcDate)
    srcNumber = property(lambda self: self.load()._srcNumber)
    isDirty = property(lambda self: self._isDirty)
    documentLocation = property(lambda self: self.load()._documentLocation)
    vouchers      = property(lambda self: self.load()._vouchers)
    isClosed = property(lambda self: self.load()._isClosed)
    
    def getWorkDays(self):
        def getWeekProfile(index):
            return {0: wpFiveDays,
             1: wpSixDays,
             2: wpSevenDays}.get(index, wpSevenDays)
             
        eventWeekProfile = getWeekProfile(forceInt(QtGui.qApp.db.getRecord('EventType', 'weekProfileCode', self.eventType.id).value('weekProfileCode')))
        endDate = self.execDate.date if self.execDate.date else QDate()
        duration = getEventDuration(self.setDate.date, endDate, eventWeekProfile, self.eventType.id)
        return duration

    def setCustomFocus(self, tempAction=None, tempProperty=None):
        check = 0
        if tempAction:
            for actionTab in self.getActionsTabsList():
                model = actionTab.modelAPActions
                for row, (record, action) in enumerate(model.items()):
                    if action == tempAction:
                        check = 1
                        break
                if check == 1:
                    break
            self.setFocusToWidget(actionTab.tblAPActions, row, 0)
            if tempProperty and isinstance(tempProperty, CPropertyInfo):
                idx = tempProperty._property.type().idx
                self.setFocusToWidget(actionTab.tblAPProps, idx, 0)

    def getWorkDaysForDate(self, a, b):
        def getWeekProfile_user(index):
            return {0: wpFiveDays,
             1: wpSixDays,
             2: wpSevenDays}.get(index, wpSevenDays)
             
        eventWeekProfile = getWeekProfile_user(forceInt(QtGui.qApp.db.getRecord('EventType', 'weekProfileCode', self.eventType.id).value('weekProfileCode')))
        endDate = b.date if b.date else QDate()
        duration = getEventDuration(a.date, endDate, eventWeekProfile, self.eventType.id)
        return duration

class CEventInfoList(CInfoList):
    def __init__(self, context, accountIdList, isExecutionPlan=False):
        CInfoList.__init__(self, context)
        self.idList = accountIdList
        self.isExecutionPlan = isExecutionPlan
        
        
    def _load(self):
        self._items = [ self.getInstance(CEventInfo, id, self.isExecutionPlan) for id in self.idList ]
        return True


class CLocEventInfoList(CInfoProxyList):
    def __init__(self, context, idList):
        CInfoProxyList.__init__(self, context)
        self.idList = idList
        self._items = [ None ]*len(self.idList)


    def __getitem__(self, key):
        v = self._items[key]
        if v is None:
            v = self.getInstance(CEventInfo, self.idList[key])
            self._items[key] = v
        return v


class CCookedEventInfo(CEventInfo):
    def __init__(self, context, id, record):
        CEventInfo.__init__(self, context, id)
        self._record = record
        self.id = id
        self._ok = self._load()
        self._loaded = True


    def _load(self):
        record = self._record
        if record:
            self._clientId = forceRef(record.value('client_id'))
            self._pregnancyWeek = forceInt(record.value('pregnancyWeek'))
            self._eventType = self.getInstance(CEventTypeInfo, forceRef(record.value('eventType_id')))
            self._externalId = forceString(record.value('externalId'))
            self._org = self.getInstance(COrgInfo, forceRef(record.value('org_id')))
            self._relegateOrg = self.getInstance(COrgInfo, forceRef(record.value('relegateOrg_id')))
            self._relegatePerson = self.getInstance(CPersonInfo, forceRef(record.value('relegatePerson_id')))
            self._client = self.getInstance(CClientInfo, forceRef(record.value('client_id')))
            self._contract = self.getInstance(CContractInfo, forceRef(record.value('contract_id')))
            self._prevEventDate = CDateInfo(forceDate(record.value('prevEventDate')))
            self._setDate = CDateTimeInfo(forceDateTime(record.value('setDate')))
            self._setTime = CTimeInfo(forceTime(record.value('setDate')))
            self._setPerson = self.getInstance(CPersonInfo, forceRef(record.value('setPerson_id')))
            self._execDate = CDateTimeInfo(forceDateTime(record.value('execDate')))
            self._execTime = CTimeInfo(forceTime(record.value('execDate')))
            self._execPerson = self.getInstance(CPersonInfo, forceRef(record.value('execPerson_id')))
            self._isPrimary = forceInt(record.value('isPrimary'))
            self._order = forceInt(record.value('order'))
            self._result = self.getInstance(CResultInfo, forceRef(record.value('result_id')))
            self._nextEventDate = CDateInfo(forceDate(record.value('nextEventDate')))
            self._payStatus = forceInt(record.value('payStatus'))
            self._typeAsset = self.getInstance(CEmergencyTypeAssetInfo, forceRef(record.value('typeAsset_id')))
            self._note = self._notes = forceString(record.value('note'))
            self._curator = self.getInstance(CPersonInfo, forceRef(record.value('curator_id')))
            self._assistant = self.getInstance(CPersonInfo, forceRef(record.value('assistant_id')))
            self._actions = self.getInstance(CActionInfoList, self.id)
            self._diagnosises = self.getInstance(CDiagnosticInfoList, self.id)
            self._feeds = self.getInstance(CFeedInfoList, self.id)
            self._visits = self.getInstance(CVisitInfoList, self.id)
            self._dispansIPhase = self.getInstance(CActionDispansPhaseInfo, self.id, 1)
            self._dispansIIPhase = self.getInstance(CActionDispansPhaseInfo, self.id, 2)
            self._localContract = self.getInstance(CEventLocalContractInfo, self.id)
            self._mes = self.getInstance(CMesInfo, forceRef(record.value('MES_id')))
            self._mesSpecification = self.getInstance(CMesSpecificationInfo, forceRef(record.value('mesSpecification_id')))
            self._patientModel = self.getInstance(CPatientModelInfo, forceRef(record.value('patientModel_id')))
            self._cureType     = self.getInstance(CCureTypeInfo, forceRef(record.value('cureType_id')))
            self._cureMethod   = self.getInstance(CCureMethodInfo, forceRef(record.value('cureMethod_id')))
            self._prevEvent = self.getInstance(CEventInfo, forceRef(record.value('prevEvent_id')))
            self._tempInvalidList = self.getTempInvalidList()
            self._tempInvalidPatronageList = self.getTempInvalidList(patronage=True)
            self._relative = self.getInstance(CClientInfo, forceRef(record.value('relative_id')))
            self._clientEvents = self.getEventCount(self._clientId)
            self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._csgList = self.getInstance(CCSGInfoList, self.id)
            self._srcDate = CDateInfo(forceDate(record.value('srcDate')))
            self._srcNumber = forceString(record.value('srcNumber'))
            self._documentLocation = self.getInstance(CDocumentLocationInfo, forceInt(record.value('client_id')), forceString(record.value('externalId')))
            self._vouchers = self.getInstance(CVoucherInfoList, self.id)
            return True
        else:
            self._clientId = None
            self._clientEvents = []
            self._pregnancyWeek = 0
            self._eventType = self.getInstance(CEventTypeInfo, None)
            self._externalId = ''
            self._org = self.getInstance(COrgInfo, None)
            self._relegateOrg = self.getInstance(COrgInfo, None)
            self._relegatePerson = self.getInstance(CPersonInfo, None)
            self._client = self.getInstance(CClientInfo, None)
            self._contract = self.getInstance(CContractInfo, None)
            self._prevEventDate = CDateInfo()
            self._setDate = CDateInfo()
            self._setTime = CTimeInfo()
            self._setPerson = self.getInstance(CPersonInfo, None)
            self._execDate = CDateInfo()
            self._execTime = CTimeInfo()
            self._execPerson = self.getInstance(CPersonInfo, None)
            self._isPrimary = False
            self._order = 0
            self._result = self.getInstance(CResultInfo, None)
            self._nextEventDate = CDateInfo()
            self._payStatus = 0
            self._typeAsset = self.getInstance(CEmergencyTypeAssetInfo, None)
            self._note = self._notes = ''
            self._curator = self.getInstance(CPersonInfo, None)
            self._assistant = self.getInstance(CPersonInfo, None)
            self._actions = self.getInstance(CActionInfoList, None)
            self._diagnosises = self.getInstance(CDiagnosticInfoList, None)
            self._feeds = self.getInstance(CFeedInfoList, None)
            self._visits = self.getInstance(CVisitInfoList, None)
            self._localContract = self.getInstance(CEventLocalContractInfo, None)
            self._mes = self.getInstance(CMesInfo, None)
            self._mesSpecification = self.getInstance(CMesSpecificationInfo, None)
            self._patientModel = self.getInstance(CPatientModelInfo, None)
            self._cureType     = self.getInstance(CCureTypeInfo, None)
            self._cureMethod   = self.getInstance(CCureMethodInfo, None)
            self._prevEvent = self.getInstance(CEventInfo, None)
            self._tempInvalidList = {}
            self._tempInvalidPatronageList = {}
            self._relative = self.getInstance(CClientInfo, None)
            self._createDatetime = CDateTimeInfo()
            self._modifyDatetime = CDateTimeInfo()
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._csgList = self.getInstance(CCSGInfoList, None)
            self._srcDate = CDateInfo()
            self._srcNumber = ''
            self._documentLocation = self.getInstance(CDocumentLocationInfo, None, None)
            self._vouchers = self.getInstance(CVoucherInfoList, None)
            return False


class CEmergencyEventInfo(CEventInfo):
    def __init__(self, context, id):
        CEventInfo.__init__(self, context, id)

    def _load(self):
        db = QtGui.qApp.db
        result = True
        if CEventInfo._load(self):
            recordEmergency = db.getRecordEx('EmergencyCall', '*', 'event_id = %d' % self.id)
            recordDeath = db.getRecordEx('Event_Death', '*', 'master_id = %d' % self.id)
        else:
            recordEmergency = None
            recordDeath = None
        if recordEmergency:
            self._numberCardCall = forceString(recordEmergency.value('numberCardCall'))
            self._brigade = self.getInstance(CEmergencyBrigadeInfo, forceRef(recordEmergency.value('brigade_id')))
            self._causeCall = self.getInstance(CEmergencyCauseCallInfo, forceRef(recordEmergency.value('causeCall_id')))
            self._whoCallOnPhone = forceString(recordEmergency.value('whoCallOnPhone'))
            self._numberPhone = forceString(recordEmergency.value('numberPhone'))
            self._storey = forceString(recordEmergency.value('storey'))
            self._entrance = forceString(recordEmergency.value('entrance'))
            self._additional = forceString(recordEmergency.value('additional'))
            self._guidePerson_id = self.getInstance(CPersonInfo, forceString(recordEmergency.value('guidePerson_id')))
            self._numberEpidemic = forceString(recordEmergency.value('numberEpidemic'))
            self._numberOrder = forceString(recordEmergency.value('order'))
            self._orgStructure = self.getInstance(COrgStructureInfo, forceRef(recordEmergency.value('orgStructure_id')))
            if getEventShowTime(self._eventType.id):
                self._begDate = CDateTimeInfo(forceDateTime(recordEmergency.value('begDate')))
                self._passDate = CDateTimeInfo(forceDateTime(recordEmergency.value('passDate')))
                self._departureDate = CDateTimeInfo(forceDateTime(recordEmergency.value('departureDate')))
                self._arrivalDate = CDateTimeInfo(forceDateTime(recordEmergency.value('arrivalDate')))
                self._finishServiceDate = CDateTimeInfo(forceDateTime(recordEmergency.value('finishServiceDate')))
                self._endDate = CDateTimeInfo(forceDateTime(recordEmergency.value('endDate')))
            else:
                self._begDate = CDateInfo(forceDate(recordEmergency.value('begDate')))
                self._passDate = CDateInfo(forceDate(recordEmergency.value('passDate')))
                self._departureDate = CDateInfo(forceDate(recordEmergency.value('departureDate')))
                self._arrivalDate = CDateInfo(forceDate(recordEmergency.value('arrivalDate')))
                self._finishServiceDate = CDateInfo(forceDate(recordEmergency.value('finishServiceDate')))
                self._endDate = CDateInfo(forceDate(recordEmergency.value('endDate')))

            self._placeReceptionCall = self.getInstance(CEmergencyPlaceReceptionCallInfo, forceRef(recordEmergency.value('placeReceptionCall_id')))
            self._receivedCall = self.getInstance(CEmergencyReceivedCallInfo, forceRef(recordEmergency.value('receivedCall_id')))
            self._reasondDelays = self.getInstance(CEmergencyReasondDelaysInfo, forceRef(recordEmergency.value('reasondDelays_id')))
            self._resultCall = self.getInstance(CEmergencyResultInfo, forceRef(recordEmergency.value('resultCall_id')))
            self._accident = self.getInstance(CEmergencyAccidentInfo, forceRef(recordEmergency.value('accident_id')))
            self._death = self.getInstance(CEmergencyDeathInfo, forceRef(recordEmergency.value('death_id')))
            self._ebriety = self.getInstance(CEmergencyEbrietyInfo, forceRef(recordEmergency.value('ebriety_id')))
            self._diseased = self.getInstance(CEmergencyDiseasedInfo, forceRef(recordEmergency.value('diseased_id')))
            self._placeCall = self.getInstance(CEmergencyPlaceCallInfo, forceRef(recordEmergency.value('placeCall_id')))
            self._methodTransport = self.getInstance(CEmergencyMethodTransportInfo, forceRef(recordEmergency.value('methodTransport_id')))
            self._transfTransport = self.getInstance(CEmergencyTransferTransportInfo, forceRef(recordEmergency.value('transfTransport_id')))
            self._renunOfHospital = forceInt(recordEmergency.value('renunOfHospital'))
            self._faceRenunOfHospital = forceString(recordEmergency.value('faceRenunOfHospital'))
            self._disease = forceInt(recordEmergency.value('disease'))
            self._birth = forceInt(recordEmergency.value('birth'))
            self._pregnancyFailure = forceInt(recordEmergency.value('pregnancyFailure'))
            self._noteCall = forceString(recordEmergency.value('noteCall'))
            self._address = self.getInstance(CAddressInfo, forceRef(recordEmergency.value('address_id')))
        else:
            self._numberCardCall = ''
            self._brigade = self.getInstance(CEmergencyBrigadeInfo, None)
            self._causeCall = self.getInstance(CEmergencyCauseCallInfo, None)
            self._whoCallOnPhone = ''
            self._numberPhone = ''
            self._storey = ''
            self._entrance = ''
            self._additional = ''
            self._guidePerson_id = None
            self._numberEpidemic = ''
            self._numberOrder = ''
            self._begDate = CDateTimeInfo()
            self._passDate = CDateTimeInfo()
            self._departureDate = CDateTimeInfo()
            self._arrivalDate = CDateTimeInfo()
            self._finishServiceDate = CDateTimeInfo()
            self._endDate = CDateTimeInfo()
            self._placeReceptionCall = self.getInstance(CEmergencyPlaceReceptionCallInfo, None)
            self._receivedCall = self.getInstance(CEmergencyReceivedCallInfo, None)
            self._reasondDelays = self.getInstance(CEmergencyReasondDelaysInfo, None)
            self._resultCall = self.getInstance(CEmergencyResultInfo, None)
            self._accident = self.getInstance(CEmergencyAccidentInfo, None)
            self._death = self.getInstance(CEmergencyDeathInfo, None)
            self._ebriety = self.getInstance(CEmergencyEbrietyInfo, None)
            self._diseased = self.getInstance(CEmergencyDiseasedInfo, None)
            self._placeCall = self.getInstance(CEmergencyPlaceCallInfo, None)
            self._methodTransport = self.getInstance(CEmergencyMethodTransportInfo, None)
            self._transfTransport = self.getInstance(CEmergencyTransferTransportInfo, None)
            self._orgStructure = self.getInstance(COrgStructureInfo, None)
            self._renunOfHospital = 0
            self._faceRenunOfHospital = ''
            self._disease = 0
            self._birth = 0
            self._pregnancyFailure = 0
            self._noteCall = ''
            self._address = None
            result = False

        if recordDeath:
            self._deathPlaceType = self.getInstance(CDeathPlaceTypeInfo, forceRef(recordDeath.value('deathPlaceType_id')))
            self._deathCauseType = self.getInstance(CDeathCauseTypeInfo, forceRef(recordDeath.value('deathCauseType_id')))
            self._employeeTypeDeterminedDeathCause = self.getInstance(CEmployeeTypeDeterminedDeathCauseInfo, forceRef(recordDeath.value('employeeTypeDeterminedDeathCause_id')))
            self._groundsForDeathCause = self.getInstance(CGroundsForDeathCauseInfo, forceRef(recordDeath.value('groundsForDeathCause_id')))
            self._deathAddress = self.getInstance(CAddressInfo, forceRef(recordDeath.value('address_id')))
            self._deathAddressFreeInput = forceString(recordDeath.value('freeInput'))
        else:
            self._deathPlaceType = self.getInstance(CDeathPlaceTypeInfo, None)
            self._deathCauseType = self.getInstance(CDeathCauseTypeInfo, None)
            self._employeeTypeDeterminedDeathCause = self.getInstance(CEmployeeTypeDeterminedDeathCauseInfo, None)
            self._groundsForDeathCause = self.getInstance(CGroundsForDeathCauseInfo, None)
            self._deathAddress = None
            self._deathAddressFreeInput = ''
            result = False

        return result


    numberCardCall      = property(lambda self: self.load()._numberCardCall)
    brigade             = property(lambda self: self.load()._brigade)
    causeCall           = property(lambda self: self.load()._causeCall)
    whoCallOnPhone      = property(lambda self: self.load()._whoCallOnPhone)
    numberPhone         = property(lambda self: self.load()._numberPhone)
    storey              = property(lambda self: self.load()._storey)
    entrance            = property(lambda self: self.load()._entrance)
    additional          = property(lambda self: self.load()._additional)
    guidePerson_id      = property(lambda self: self.load()._guidePerson_id)
    numberEpidemic      = property(lambda self: self.load()._numberEpidemic)
    numberOrder         = property(lambda self: self.load()._numberOrder)
    begDate             = property(lambda self: self.load()._begDate)
    passDate            = property(lambda self: self.load()._passDate)
    departureDate       = property(lambda self: self.load()._departureDate)
    arrivalDate         = property(lambda self: self.load()._arrivalDate)
    finishServiceDate   = property(lambda self: self.load()._finishServiceDate)
    endDate             = property(lambda self: self.load()._endDate)
    placeReceptionCall  = property(lambda self: self.load()._placeReceptionCall)
    receivedCall        = property(lambda self: self.load()._receivedCall)
    reasondDelays       = property(lambda self: self.load()._reasondDelays)
    resultCall          = property(lambda self: self.load()._resultCall)
    accident            = property(lambda self: self.load()._accident)
    death               = property(lambda self: self.load()._death)
    ebriety             = property(lambda self: self.load()._ebriety)
    diseased            = property(lambda self: self.load()._diseased)
    placeCall           = property(lambda self: self.load()._placeCall)
    methodTransport     = property(lambda self: self.load()._methodTransport)
    transfTransport     = property(lambda self: self.load()._transfTransport)
    renunOfHospital     = property(lambda self: self.load()._renunOfHospital)
    faceRenunOfHospital = property(lambda self: self.load()._faceRenunOfHospital)
    disease             = property(lambda self: self.load()._disease)
    birth               = property(lambda self: self.load()._birth)
    pregnancyFailure    = property(lambda self: self.load()._pregnancyFailure)
    noteCall            = property(lambda self: self.load()._noteCall)
    orgStructure        = property(lambda self: self.load()._orgStructure)
    address             = property(lambda self: self.load()._address)
    deathPlaceType      = property(lambda self: self.load()._deathPlaceType)
    deathCauseType      = property(lambda self: self.load()._deathCauseType)
    groundsForDeathCause = property(lambda self: self.load()._groundsForDeathCause)
    deathAddress         = property(lambda self: self.load()._deathAddress)
    deathAddressFreeInput = property(lambda self: self.load()._deathAddressFreeInput)
    employeeTypeDeterminedDeathCause = property(lambda self: self.load()._employeeTypeDeterminedDeathCause)


class CEventIdentificationInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id
        self._byCode = {}
        #        self._byName = {}
        self._nameDict = {}

    def _load(self):
        db = QtGui.qApp.db
        self._code = ''
        self._name = ''
        self._value = ''
        tableCI = db.table('EventType_Identification')
        tableAS = db.table('rbAccountingSystem')
        stmt = db.selectStmt(tableCI.leftJoin(tableAS, tableAS['id'].eq(tableCI['system_id'])),
                             ['code', 'name', 'value', 'checkDate'],
                             db.joinAnd([tableCI['master_id'].eq(self.id),
                                         tableCI['deleted'].eq(0),
                                         ])
                             )
        query = db.query(stmt)
        while query.next():
            record = query.record()
            code = forceString(record.value('code'))
            name = forceString(record.value('name'))
            value = forceString(record.value('value'))
            self._byCode[code] = value
            #            self._byName[name] = identifier
            self._nameDict[code] = name
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._value = forceString(record.value('value'))
            self._checkDate = CDateInfo(record.value('checkDate'))
        return True

    def has_key(self, key):
        return key in self._byCode

    def get(self, key, default=None):
        return self._byCode.get(key, default)

    def iteritems(self):
        return self._byCode.iteritems()

    def iterkeys(self):
        return self._byCode.iterkeys()

    def itervalues(self):
        return self._byCode.itervalues()

    def items(self):
        return self._byCode.items()

    def keys(self):
        return self._byCode.keys()

    def values(self):
        return self._byCode.values()

    def __nonzero__(self):
        return bool(self._byCode)

    def __len__(self):
        return len(self._byCode)

    def __contains__(self, key):
        return key in self._byCode

    def __getitem__(self, key):
        return self._byCode.get(key, '')

    def __iter__(self):
        return self._byCode.iterkeys()

    def __str__(self):
        self.load()
        l = [u'%s (%s): %s' % (self._nameDict[code], code, value)
             for code, value in self._byCode.iteritems()
             ]
        l.sort()
        return ', '.join(l)

    byCode = property(lambda self: self.load()._byCode)
    #    byName = property(lambda self: self.load()._byName)
    nameDict = property(lambda self: self.load()._nameDict)
    code = property(lambda self: self.load()._code)
    name = property(lambda self: self.load()._name)
    value = property(lambda self: self.load()._value)
    checkDate = property(lambda self: self.load()._checkDate)

class CEmergencyEventInfoList(CInfoList):
    def __init__(self, context, eventIdList):
        CInfoList.__init__(self, context)
        self.idList = eventIdList


    def _load(self):
        self._items = [ self.getInstance(CEmergencyEventInfo, id) for id in self.idList ]
        return True


class CEventLocalContractInfo(CInfo):
    def __init__(self, context, eventId):
        CInfo.__init__(self, context)
        self._ageTuple  = None
        self._age       = ''
        self._ageTupleCustom  = None
        self._customerAge       = ''
        self.eventId = eventId
        self._payment = []

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Event_LocalContract')
        tableEvent = db.table('Event')
        queryTable = table.leftJoin(tableEvent, tableEvent['id'].eq(table['master_id']))
        record = db.getRecordEx(queryTable, '*', [table['master_id'].eq(self.eventId),
                                             table['deleted'].eq(0)
                                            ]) if self.eventId else None
        if record:
            self.initByRecord(record)
            return True
        else:
            self.initByRecord(db.dummyRecord())
            return False


    def initByRecord(self, record):
        self._coordDate = CDateInfo(forceDate(record.value('coordDate')))
        self._coordAgent = forceString(record.value('coordAgent'))
        self._coordInspector = forceString(record.value('coordInspector'))
        self._coordText = forceString(record.value('coordText'))
        self._date   = CDateInfo(forceDate(record.value('dateContract')))
        self._number = forceString(record.value('numberContract'))
        self._sumLimit = forceDouble(record.value('sumLimit'))
        self._org = self.getInstance(COrgInfo, forceRef(record.value('org_id')))
        self._lastName = forceString(record.value('lastName'))
        self._firstName = forceString(record.value('firstName'))
        self._patrName = forceString(record.value('patrName'))
        self._birthDate = CDateInfo(forceDate(record.value('birthDate')))
        self._ageTuple  = calcAgeTuple(self._birthDate.date, forceDate(record.value('setDate')))
        self._age       = formatAgeTuple(self._ageTuple, self._birthDate.date, forceDate(record.value('setDate')))
        self._document = CClientDocumentInfo(self.context)
        documentTypeId = forceRef(record.value('documentType_id'))
        self._document._documentType = forceString(QtGui.qApp.db.translate('rbDocumentType', 'id', documentTypeId, 'name'))
        self._document._documentTypeCode = forceString(QtGui.qApp.db.translate('rbDocumentType', 'id', documentTypeId, 'code'))
        self._document._documentTypeId = documentTypeId
        self._document._documentTypeFederalCode = forceString(QtGui.qApp.db.translate('rbDocumentType', 'id', documentTypeId, 'federalCode'))
        self._document._documentTypeRegionalCode = forceString(QtGui.qApp.db.translate('rbDocumentType', 'id', documentTypeId, 'regionalCode'))
        self._document._serial = forceStringEx(record.value('serialLeft'))+' '+forceStringEx(record.value('serialRight'))
        self._document._number = forceString(record.value('number'))
        self._document._origin = forceString(record.value('docOrigin'))
        self._document._date = CDateInfo(record.value('docDate'))
        if self._document._documentType:
            self._document._loaded = True
            self._document._ok = True
        self._address = forceString(record.value('regAddress'))
        self._email   = forceString(record.value('email'))

        self._customerOrg = self.getInstance(COrgInfo, forceRef(record.value('customerOrg_id')))
        self._customerLastName = forceString(record.value('customerLastName'))
        self._customerFirstName = forceString(record.value('customerFirstName'))
        self._customerPatrName = forceString(record.value('customerPatrName'))
        self._customerBirthDate = CDateInfo(forceDate(record.value('customerBirthDate')))
        self._ageTupleCustom  = calcAgeTuple(self._customerBirthDate.date, forceDate(record.value('setDate')))
        self._customerAge       = formatAgeTuple(self._ageTupleCustom, self._customerBirthDate.date, forceDate(record.value('setDate')))
        self._customerDocument = CClientDocumentInfo(self.context)
        customerDocumentTypeId = forceRef(record.value('customerDocumentType_id'))
        self._customerDocument._documentType = forceString(QtGui.qApp.db.translate('rbDocumentType', 'id', customerDocumentTypeId, 'name'))
        self._customerDocument._documentTypeId = customerDocumentTypeId
        self._customerDocument._documentTypeCode = forceString(QtGui.qApp.db.translate('rbDocumentType', 'id', documentTypeId, 'code'))
        self._customerDocument._documentTypeFederalCode = forceString(QtGui.qApp.db.translate('rbDocumentType', 'id', documentTypeId, 'federalCode'))
        self._customerDocument._documentTypeRegionalCode = forceString(QtGui.qApp.db.translate('rbDocumentType', 'id', documentTypeId, 'regionalCode'))
        self._customerDocument._serial = forceStringEx(record.value('customerSerialLeft'))+' '+forceStringEx(record.value('customerSerialRight'))
        self._customerDocument._number = forceString(record.value('customerNumber'))
        self._customerDocument._origin = forceString(record.value('customerDocOrigin'))
        self._customerDocument._date = CDateInfo(record.value('customerDocDate'))
        if self._customerDocument._documentType:
            self._customerDocument._loaded = True
            self._customerDocument._ok = True
        self._customerAddress = forceString(record.value('customerRegAddress'))
        self._customerEmail   = forceString(record.value('customerEmail'))
        self._customerEnabled = forceBool(record.value('customerEnabled'))
        self._payment =  self.getInstance(CEventPaymentInfoList, record.value('master_id'))

    coordDate   = property(lambda self: self.load()._coordDate)
    coordAgent  = property(lambda self: self.load()._coordAgent)
    coordInspector = property(lambda self: self.load()._coordInspector)
    coordText   = property(lambda self: self.load()._coordText)
    date        = property(lambda self: self.load()._date)
    number      = property(lambda self: self.load()._number)
    sumLimit    = property(lambda self: self.load()._sumLimit)
    lastName    = property(lambda self: self.load()._lastName)
    firstName   = property(lambda self: self.load()._firstName)
    patrName    = property(lambda self: self.load()._patrName)
    birthDate   = property(lambda self: self.load()._birthDate)
    age          = property(lambda self: self.load()._age)
    document    = property(lambda self: self.load()._document)
    address     = property(lambda self: self.load()._address)
    org         = property(lambda self: self.load()._org)
    email       = property(lambda self: self.load()._email)
    customerEnabled      = property(lambda self: self.load()._customerEnabled)
    customerLastName    = property(lambda self: self.load()._customerLastName)
    customerFirstName   = property(lambda self: self.load()._customerFirstName)
    customerPatrName    = property(lambda self: self.load()._customerPatrName)
    customerBirthDate   = property(lambda self: self.load()._customerBirthDate)
    customerAge          = property(lambda self: self.load()._customerAge)
    customerDocument    = property(lambda self: self.load()._customerDocument)
    customerAddress     = property(lambda self: self.load()._customerAddress)
    customerOrg         = property(lambda self: self.load()._customerOrg)
    customerEmail       = property(lambda self: self.load()._customerEmail)
    payment         = property(lambda self: self.load()._payment)

    def __str__(self):
        if self.load():
            parts = []
            if self._coordDate:
                parts.append(u'согласовано ' + self._coordDate)
            if self._coordText:
                parts.append(self._coordText)
            if self._number:
                parts.append(u'№ ' + self._number)
            if self._date:
                parts.append(u'от ' + forceString(self._date))
            if self._org:
                parts.append(unicode(self._org))
            else:
                parts.append(self._lastName)
                parts.append(self._firstName)
                parts.append(self._patrName)
            return ' '.join(parts)
        else:
            return ''


class CEventPaymentInfoList(CInfoList):
    def __init__(self, context, masterId):
        CInfoList.__init__(self, context)
        self.masterId = masterId

    def _load(self):
        idList = self.getEventPaymentIds()
        self._items = [ self.getInstance(CEventPaymentInfo, id) for id in idList ]

    def getEventPaymentIds(self):
        masterId = self.masterId
        db = QtGui.qApp.db
        table = db.table('Event_Payment')
        cond  = [table['master_id'].eq(masterId)]
        cond.append(table['deleted'].eq(0))
        return db.getIdList(table, idCol='id', where=cond)


class CEventPaymentInfo(CInfo):
    def __init__(self, context, paymentId):
        CInfo.__init__(self, context)
        self.paymentId = paymentId
        self._date = None
        self._cashOperation = None
        self._sum = None
        self._typePayment = None
        self._settlementAccount = None
        self._bank = None
        self._numberCreditCard = None
        self._cashBox = None


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Event_Payment')
        record = db.getRecord(table, '*', self.paymentId)
        if record:
            from Accounting.CashDialog import CCashOperationInfo
            cashOperationId = forceRef(record.value('cashOperation_id'))
            self._date = forceString(record.value('date'))
            self._cashOperation = self.getInstance(CCashOperationInfo, cashOperationId) if cashOperationId else None
            self._sum = forceDouble(record.value('sum'))
            self._typePayment = forceInt(record.value('typePayment'))
            self._settlementAccount = forceString(record.value('settlementAccount'))
            bankId = forceRef(record.value('bank_id'))
            self._bank = self.getInstance(COrgInfo, bankId) if bankId else None
            self._numberCreditCard = forceString(record.value('numberCreditCard'))
            self._cashBox = forceString(record.value('cashBox'))
            return True
        return False

    date = property(lambda self: self.load()._date)
    cashOperation = property(lambda self: self.load()._cashOperation)
    sum = property(lambda self: self.load()._sum)
    typePayment = property(lambda self: self.load()._typePayment)
    settlementAccount = property(lambda self: self.load()._settlementAccount)
    bank = property(lambda self: self.load()._bank)
    numberCreditCard = property(lambda self: self.load()._numberCreditCard)
    cashBox = property(lambda self: self.load()._cashBox)


class CDagnosisTypeInfo(CRBInfo):
    tableName = 'rbDiagnosisType'


class CCharacterInfo(CRBInfoWithIdentification):
    tableName = 'rbDiseaseCharacter'


class CPhasesInfo(CRBInfoWithIdentification):
    tableName = 'rbDiseasePhases'

    def _initByRecord(self, record):
        self._code = forceInt(record.value('code'))

    def _initByNull(self):
        self._code = 0

    code = property(lambda self: self.load()._code)


class CStageInfo(CRBInfo):
    tableName = 'rbDiseaseStage'

    def _initByRecord(self, record):
        self._code = forceInt(record.value('code'))

    def _initByNull(self):
        self._code = 0

    code = property(lambda self: self.load()._code)


class CDispanserInfo(CRBInfo):
    tableName = 'rbDispanser'

    def _initByRecord(self, record):
        self._observed = forceBool(record.value('observed'))
        self._code = forceInt(record.value('code'))
        self._dispanserBegDate = CDateInfo(forceDate(record.value('dispanserBegDate')))
        self._dispanserPerson = self.getInstance(CPersonInfo, forceRef(record.value('dispanserPerson_id')))


    def _initByNull(self):
        self._observed = False
        self._code = 0

    observed = property(lambda self: self.load()._observed)
    code = property(lambda self: self.load()._code)
    dispanserBegDate = property(lambda self: self.load()._dispanserBegDate)
    dispanserPerson = property(lambda self: self.load()._dispanserPerson)


class CHospitalInfo(CInfo):
    names = [u'не требуется', u'требуется', u'направлен', u'пролечен']

    def __init__(self, context, code):
        CInfo.__init__(self, context)
        self.code = code
        self.name = self.names[code] if 0<=code<len(self.names) else ('{%s}' % code)
        self._ok = True
        self._loaded = True

    def __str__(self):
        return self.name


class CTraumaTypeInfo(CRBInfoWithIdentification):
    tableName = 'rbTraumaType'


class CToxicSubstancesInfo(CRBInfo):
    tableName = 'rbToxicSubstances'

    def _initByRecord(self, record):
        self._MKB = forceStringEx(record.value('MKB'))


    def _initByNull(self):
        self._MKB = False

    MKB = property(lambda self: self.load()._MKB)


class CHealthGroupInfo(CRBInfoWithIdentification):
    tableName = 'rbHealthGroup'


class CNodusInfo(CRBInfoWithIdentification):
    tableName = 'rbNodus'


class CMetastasisInfo(CRBInfoWithIdentification):
    tableName = 'rbMetastasis'


class CTNMphaseInfo(CRBInfoWithIdentification):
    tableName = 'rbTNMphase'


class CDiagnosticInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        tableDiagnostic = db.table('Diagnostic')
        tableDiagnosis = db.table('Diagnosis')
        record = db.getRecord(tableDiagnostic.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id'])),
                              'Diagnostic.*, Diagnosis.MKB, Diagnosis.MKBEx, Diagnosis.morphologyMKB, Diagnosis.mod_id, Diagnosis.exSubclassMKB, Diagnosis.dispanserBegDate',
                              self.id)
        if record:
            self.initByRecord(record)
            return True
        else:
            self.initByRecord(db.dummyRecord())
            return False


    def initByRecord(self, record):
        self._type = self.getInstance(CDagnosisTypeInfo, forceRef(record.value('diagnosisType_id')))
        self._MKB = self.getInstance(CMKBInfo, forceString(record.value('MKB')))
        self._MKBEx = self.getInstance(CMKBInfo, forceString(record.value('MKBEx')))
        self._morphologyMKB = forceString(record.value('morphologyMKB'))
        self._character = self.getInstance(CCharacterInfo, forceRef(record.value('character_id')))
        self._stage = self.getInstance(CStageInfo, forceRef(record.value('stage_id')))
        self._phase = self.getInstance(CPhasesInfo, forceRef(record.value('phase_id')))
        self._dispanser = self.getInstance(CDispanserInfo, forceRef(record.value('dispanser_id')))
        self._sanatorium = self.getInstance(CHospitalInfo, forceInt(record.value('sanatorium')))
        self._hospital = self.getInstance(CHospitalInfo, forceInt(record.value('hospital')))
        self._traumaType = self.getInstance(CTraumaTypeInfo, forceRef(record.value('traumaType_id')))
        self._toxicSubstances = self.getInstance(CToxicSubstancesInfo, forceRef(record.value('toxicSubstances_id')))
        self._speciality = self.getInstance(CSpecialityInfo, forceRef(record.value('speciality_id')))
        self._person = self.getInstance(CPersonInfo, forceRef(record.value('person_id')))
        self._healthGroup = self.getInstance(CHealthGroupInfo, forceRef(record.value('healthGroup_id')))
        self._result = self.getInstance(CDiagnosticResultInfo, forceRef(record.value('result_id')))
        self._setDate = CDateInfo(forceDate(record.value('setDate')))
        self._endDate = CDateInfo(forceDate(record.value('endDate')))
        self._notes = forceString(record.value('notes'))
        self._mod = self.getInstance(CDiagnosisInfo, forceRef(record.value('mod_id')))
        self._diagnosis = self.getInstance(CDiagnosisInfo, forceRef(record.value('diagnosis_id')))
        self._freeInput = forceString(record.value('freeInput'))
        self._eventInfo = self.getInstance(CEventInfo, forceRef(record.value('event_id')))
        self._TNMS = forceString(record.value('TNMS'))
        self._exSubclassMKB = forceString(record.value('exSubclassMKB'))
        self._ExSubclassItemLastName = getExSubclassItemLastName(forceString(self._exSubclassMKB), forceString(self._MKB))
        self._cTumor = self.getInstance(CTumorInfo, forceRef(record.value('cTumor_id')))
        self._pTumor = self.getInstance(CTumorInfo, forceRef(record.value('pTumor_id')))
        self._cNodus = self.getInstance(CNodusInfo, forceRef(record.value('cNodus_id')))
        self._pNodus = self.getInstance(CNodusInfo, forceRef(record.value('pNodus_id')))
        self._cMetastasis = self.getInstance(CMetastasisInfo, forceRef(record.value('cMetastasis_id')))
        self._pMetastasis = self.getInstance(CMetastasisInfo, forceRef(record.value('pMetastasis_id')))
        self._cTNMphase = self.getInstance(CTNMphaseInfo, forceRef(record.value('cTNMphase_id')))
        self._pTNMphase = self.getInstance(CTNMphaseInfo, forceRef(record.value('pTNMphase_id')))
        self._dispanserBegDate = CDateInfo(forceDate(record.value('dispanserBegDate')))

    type          = property(lambda self: self.load()._type)
    MKB           = property(lambda self: self.load()._MKB)
    MKB_ExSubclass           = property(lambda self: self.load()._ExSubclassItemLastName)
    MKBEx         = property(lambda self: self.load()._MKBEx)
    morphologyMKB = property(lambda self: self.load()._morphologyMKB)
    character     = property(lambda self: self.load()._character)
    stage         = property(lambda self: self.load()._stage)
    phase         = property(lambda self: self.load()._phase)
    dispanser     = property(lambda self: self.load()._dispanser)
    sanatorium    = property(lambda self: self.load()._sanatorium)
    hospital      = property(lambda self: self.load()._hospital)
    traumaType    = property(lambda self: self.load()._traumaType)
    toxicSubstances = property(lambda self: self.load()._toxicSubstances)
    speciality    = property(lambda self: self.load()._speciality)
    person        = property(lambda self: self.load()._person)
    healthGroup   = property(lambda self: self.load()._healthGroup)
    result        = property(lambda self: self.load()._result)
    setDate       = property(lambda self: self.load()._setDate)
    endDate       = property(lambda self: self.load()._endDate)
    notes         = property(lambda self: self.load()._notes)
    mod           = property(lambda self: self.load()._mod)
    diagnosis     = property(lambda self: self.load()._diagnosis)
    freeInput         = property(lambda self: self.load()._freeInput)
    eventInfo     = property(lambda self: self.load()._eventInfo)
    TNMS     = property(lambda self: self.load()._TNMS)
    exSubclassMKB = property(lambda self: self.load()._exSubclassMKB)
    cTumor     = property(lambda self: self.load()._cTumor)
    pTumor     = property(lambda self: self.load()._pTumor)
    cNodus     = property(lambda self: self.load()._cNodus)
    pNodus     = property(lambda self: self.load()._pNodus)
    cMetastasis     = property(lambda self: self.load()._cMetastasis)
    pMetastasis     = property(lambda self: self.load()._pMetastasis)
    cTNMphase     = property(lambda self: self.load()._cTNMphase)
    pTNMphase     = property(lambda self: self.load()._pTNMphase)
    dispanserBegDate = property(lambda self: self.load()._dispanserBegDate)


class CDiagnosticInfoList(CInfoList):
    def __init__(self, context, eventId):
        CInfoList.__init__(self, context)
        self.eventId = eventId


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
        idList = db.getIdList(table, 'id', [table['event_id'].eq(self.eventId), table['deleted'].eq(0)], 'id')
        self._items = [ self.getInstance(CDiagnosticInfo, id) for id in idList ]
        return True


class CDiagnosticForTypeInfoList(CInfoList):
    def __init__(self, context, eventId, typeCode):
        CInfoList.__init__(self, context)
        self.eventId = eventId
        self.typeCode = typeCode


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
        tableRBDiagnosisType = db.table('rbDiagnosisType')
        queryTable = table.innerJoin(tableRBDiagnosisType, tableRBDiagnosisType['id'].eq(table['diagnosisType_id']))
        idList = db.getIdList(queryTable, table['id'], [table['event_id'].eq(self.eventId), table['deleted'].eq(0), tableRBDiagnosisType['code'].eq(self.typeCode)], 'id')
        self._items = [ self.getInstance(CDiagnosticInfo, id) for id in idList ]
        return True


class CDiagnosticInfoIdList(CInfoList):
    def __init__(self, context, idList):
        CInfoList.__init__(self, context)
        self.idList = idList


    def _load(self):
        self._items = [ self.getInstance(CDiagnosticInfo, id) for id in self.idList ]
        return True


class CDiagnosticInfoListEx(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self.clientId = clientId


    def _load(self):
        if self.clientId:
            db = QtGui.qApp.db
            table = db.table('Diagnostic')
            tableDiagnosis = db.table('Diagnosis')
            queryTable = table.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(table['diagnosis_id']))
            idList = db.getDistinctIdList(queryTable, table['id'], [tableDiagnosis['client_id'].eq(self.clientId), table['deleted'].eq(0), tableDiagnosis['deleted'].eq(0)], 'Diagnostic.id')
            self._items = [ self.getInstance(CDiagnosticInfo, id) for id in idList ]
            return True
        else:
            self._items = []
            return False


class CDiagnosisInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Diagnosis')
        record = db.getRecord(table, '*', self.id)
        if record:
            self.initByRecord(record)
            return True
        else:
            self.initByRecord(db.dummyRecord())
            return False


    def initByRecord(self, record):
        self._type = self.getInstance(CDagnosisTypeInfo, forceRef(record.value('diagnosisType_id')))
        self._MKB = self.getInstance(CMKBInfo, forceString(record.value('MKB')))
        self._MKBEx = self.getInstance(CMKBInfo, forceString(record.value('MKBEx')))
        self._morphologyMKB = forceString(record.value('morphologyMKB'))
        self._character = self.getInstance(CCharacterInfo, forceRef(record.value('character_id')))
        self._dispanser = self.getInstance(CDispanserInfo, forceRef(record.value('dispanser_id')))
        self._traumaType = self.getInstance(CTraumaTypeInfo, forceRef(record.value('traumaType_id')))
        self._person = self.getInstance(CPersonInfo, forceRef(record.value('person_id')))
        self._setDate = CDateInfo(forceDate(record.value('setDate')))
        self._endDate = CDateInfo(forceDate(record.value('endDate')))
        self._mod = self.getInstance(CDiagnosisInfo, forceRef(record.value('mod_id')))
        self._client = self.getInstance(CClientInfo, forceRef(record.value('client_id')))
        self._exSubclassMKB = forceString(record.value('exSubclassMKB'))
        self._dispanserBegDate = CDateInfo(forceDate(record.value('dispanserBegDate')))
        self._dispanserPerson = self.getInstance(CPersonInfo, forceRef(record.value('dispanserPerson_id')))

    type          = property(lambda self: self.load()._type)
    MKB           = property(lambda self: self.load()._MKB)
    MKBEx         = property(lambda self: self.load()._MKBEx)
    morphologyMKB = property(lambda self: self.load()._morphologyMKB)
    character     = property(lambda self: self.load()._character)
    dispanser     = property(lambda self: self.load()._dispanser)
    traumaType    = property(lambda self: self.load()._traumaType)
    person        = property(lambda self: self.load()._person)
#    healthGroup = property(lambda self: self.load()._healthGroup)
    setDate       = property(lambda self: self.load()._setDate)
    endDate       = property(lambda self: self.load()._endDate)
    mod           = property(lambda self: self.load()._mod)
    client        = property(lambda self: self.load()._client)
    exSubclassMKB = property(lambda self: self.load()._exSubclassMKB)
    dispanserBegDate = property(lambda self: self.load()._dispanserBegDate)
    dispanserPerson = property(lambda self: self.load()._dispanserPerson)


class CDiagnosisInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self.clientId = clientId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Diagnosis')
        idList = db.getIdList(table,
                              'id',
                              [table['client_id'].eq(self.clientId), table['deleted'].eq(0), table['mod_id'].isNull()],
                              'endDate')
        self._items = [ self.getInstance(CDiagnosisInfo, id) for id in idList ]
        return True


class CSceneInfo(CRBInfo):
    tableName = 'rbScene'


class CVisitInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Visit')
        record = db.getRecordEx(table, '*', [table['id'].eq(self.id), table['deleted'].eq(0)])
        if record:
            self.initByRecord(record)
            return True
        else:
            self.initByRecord(db.dummyRecord())
            return False


    def initByRecord(self, record):
        self._scene = self.getInstance(CSceneInfo, forceRef(record.value('scene_id')))
        self._date = CDateInfo(forceDate(record.value('date')))
        self._type = self.getInstance(CVisitTypeInfo, forceRef(record.value('visitType_id')))
        self._eventInfo = self.getInstance(CEventInfo, forceRef(record.value('event_id')))
        self._person = self.getInstance(CPersonInfo, forceRef(record.value('person_id')))
        self._assistant = self.getInstance(CPersonInfo, forceRef(record.value('assistant_id')))
        self._isPrimary = forceBool(record.value('isPrimary'))
        self._finance = self.getInstance(CFinanceInfo, forceRef(record.value('finance_id')))
        self._service = self.getInstance(CServiceInfo, forceRef(record.value('service_id')))
        self._payStatus = forceInt(record.value('payStatus'))

    scene       = property(lambda self: self.load()._scene)
    date        = property(lambda self: self.load()._date)
    type        = property(lambda self: self.load()._type)
    eventInfo   = property(lambda self: self.load()._eventInfo)
    person      = property(lambda self: self.load()._person)
    assistant   = property(lambda self: self.load()._assistant)
    isPrimary   = property(lambda self: self.load()._isPrimary)
    finance     = property(lambda self: self.load()._finance)
    service     = property(lambda self: self.load()._service)
    payStatus   = property(lambda self: self.load()._payStatus)


class CVisitInfoList(CInfoList):
    def __init__(self, context, eventId):
        CInfoList.__init__(self, context)
        self.eventId = eventId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Visit')
        idList = db.getIdList(table, 'id', [table['event_id'].eq(self.eventId), table['deleted'].eq(0)], 'id')
        self._items = [ self.getInstance(CVisitInfo, id) for id in idList ]
        return True


class CVisitInfoListEx(CInfoList):
    def __init__(self, context, visitIdList):
        CInfoList.__init__(self, context)
        self.idList = visitIdList


    def _load(self):
        self._items = [ self.getInstance(CVisitInfo, id) for id in self.idList ]
        return True


class CVoucherInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Event_Voucher')
        record = db.getRecordEx(table, '*', [table['id'].eq(self.id), table['deleted'].eq(0)])
        if record:
            self.initByRecord(record)
            return True
        else:
            self.initByRecord(db.dummyRecord())
            return False


    def initByRecord(self, record):
        self._finance = self.getInstance(CFinanceInfo, forceRef(record.value('finance_id')))
        self._org = self.getInstance(COrgInfo, forceRef(record.value('org_id')))
        self._begDate = CDateInfo(forceDate(record.value('begDate')))
        self._endDate = CDateInfo(forceDate(record.value('endDate')))
        self._serial = forceString(record.value('serial'))
        self._number = forceString(record.value('number'))

    finance       = property(lambda self: self.load()._finance)
    org        = property(lambda self: self.load()._org)
    begDate        = property(lambda self: self.load()._begDate)
    endDate   = property(lambda self: self.load()._endDate)
    serial      = property(lambda self: self.load()._serial)
    number   = property(lambda self: self.load()._number)


class CVoucherInfoList(CInfoList):
    def __init__(self, context, eventId):
        CInfoList.__init__(self, context)
        self.eventId = eventId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Event_Voucher')
        idList = db.getIdList(table, 'id', [table['event_id'].eq(self.eventId), table['deleted'].eq(0)], 'id')
        self._items = [ self.getInstance(CVoucherInfo, id) for id in idList ]
        return True


class CDiagnosticInfoProxyList(CInfoProxyList):
    def __init__(self, context, models):
        CInfoProxyList.__init__(self, context)
        self._rawItems = []
        for model in models:
            self._rawItems.extend(model.items())
        self._items = [ None ] * len(self._rawItems)


    def __getitem__(self, key):
        v = self._items[key]
        if v is None:
            record = self._rawItems[key]
            v = self.getInstance(CDiagnosticInfo, 'tmp_%d'%key)
            v.initByRecord(record)
            v.setOkLoaded()
            self._items[key] = v
        return v


class CVisitInfoProxyList(CInfoProxyList):
    def __init__(self, context, modelVisits):
        CInfoProxyList.__init__(self, context)
        self._items = [ None ] * len(modelVisits.items())
        self.model = modelVisits


    def _getItemEx(self, key):
        record = self.model.items()[key]
        v = self.getInstance(CVisitInfo, 'tmp_%d'%key)
        v.initByRecord(record)
        v.setOkLoaded()
        return v

    def __getitem__(self, key):
        if isinstance(key, slice):
            for i in range(key.start or 0, key.stop or len(self._items), key.step or 1):
                val = self._items[i]
                if val is None:
                    self._items[i] = self._getItemEx(i)
        v = self._items[key]
        if v is None:
            v = self._getItemEx(key)
            self._items[key] = v
        return v


class CVisitPersonallInfo(CInfo):
    def __init__(self, context, item = []):
        CInfo.__init__(self, context)
        self.item = item


    def _load(self):
        if self.item != []:
            self._scene = self.getInstance(CSceneInfo, self.item[0])
            self._date = CDateTimeInfo(self.item[1])
            self._type = self.getInstance(CVisitTypeInfo, self.item[2])
            self._person = self.getInstance(CPersonInfo, self.item[3])
            self._isPrimary = forceBool(self.item[4])
            self._finance = self.getInstance(CFinanceInfo, self.item[5])
            self._service = self.getInstance(CServiceInfo, self.item[6])
            self._payStatus = self.item[7]

    scene       = property(lambda self: self.load()._scene)
    date        = property(lambda self: self.load()._date)
    type        = property(lambda self: self.load()._type)
    person      = property(lambda self: self.load()._person)
    isPrimary   = property(lambda self: self.load()._isPrimary)
    finance     = property(lambda self: self.load()._finance)
    service     = property(lambda self: self.load()._service)
    payStatus   = property(lambda self: self.load()._payStatus)


class CEmergencyBrigadeInfo(CInfo):
    def __init__(self, context, brigadeId):
        CInfo.__init__(self, context)
        self.brigadeId = brigadeId
        self._code = ''
        self._name = ''
        self._regionalCode = ''
        self._persons = context.getInstance(CPersonInfoList, 'EmergencyBrigade_Personnel', None)


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('EmergencyBrigade', '*', self.brigadeId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._regionalCode = forceString(record.value('regionalCode'))
            self._persons = self.getInstance(CPersonInfoList, 'EmergencyBrigade_Personnel', self.brigadeId)
            return True
        else:
            return False


    def __str__(self):
        return self.load()._name

    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    regionalCode = property(lambda self: self.load()._regionalCode)
    persons  = property(lambda self: self.load()._persons)


class CEmergencyCauseCallInfo(CRBInfoWithRegionalCode):
    tableName = 'rbEmergencyCauseCall'


class CEmergencyTransferTransportInfo(CRBInfoWithRegionalCode):
    tableName = 'rbEmergencyTransferredTransportation'


class CEmergencyPlaceReceptionCallInfo(CRBInfoWithRegionalCode):
    tableName = 'rbEmergencyPlaceReceptionCall'


class CEmergencyReceivedCallInfo(CRBInfoWithRegionalCode):
    tableName = 'rbEmergencyReceivedCall'


class CEmergencyReasondDelaysInfo(CRBInfoWithRegionalCode):
    tableName = 'rbEmergencyReasondDelays'


class CEmergencyResultInfo(CRBInfoWithRegionalCode):
    tableName = 'rbEmergencyResult'


class CEmergencyAccidentInfo(CRBInfoWithRegionalCode):
    tableName = 'rbEmergencyAccident'


class CEmergencyDeathInfo(CRBInfoWithRegionalCode):
    tableName = 'rbEmergencyDeath'


class CEmergencyEbrietyInfo(CRBInfoWithRegionalCode):
    tableName = 'rbEmergencyEbriety'


class CEmergencyDiseasedInfo(CRBInfoWithRegionalCode):
    tableName = 'rbEmergencyDiseased'


class CEmergencyPlaceCallInfo(CRBInfoWithRegionalCode):
    tableName = 'rbEmergencyPlaceCall'


class CEmergencyMethodTransportInfo(CRBInfoWithRegionalCode):
    tableName = 'rbEmergencyMethodTransportation'


class CEmergencyTypeAssetInfo(CRBInfoWithRegionalCode):
    tableName = 'rbEmergencyTypeAsset'


class CCashOperationInfo(CRBInfo):
    tableName = 'rbCashOperation'



class CCentralizedAccountingEventInfo(CEventInfo):
    def __init__(self, context, id, isExecutionPlan=False, hBedOSId=None):
        CEventInfo.__init__(self, context, id, isExecutionPlan)
        self.id = id
        self.hBedOSId = hBedOSId
        self._clientId = None
        self._localContract = None
        self._contractTariffCache = None
        self._tempInvalidListLoaded = False
        self._clientEvents = []
        self._isDirty = False
        self.isExecutionPlan = isExecutionPlan

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('Event', '*', self.id)
        if record:
            self._clientId = forceRef(record.value('client_id'))
            self._pregnancyWeek = forceInt(record.value('pregnancyWeek'))
            self._eventType = self.getInstance(CEventTypeInfo, forceRef(record.value('eventType_id')))
            self._externalId = forceString(record.value('externalId'))
            self._org = self.getInstance(COrgInfo, forceRef(record.value('org_id')))
            self._relegateOrg = self.getInstance(COrgInfo, forceRef(record.value('relegateOrg_id')))
            self._relegatePerson = self.getInstance(CPersonInfo, forceRef(record.value('relegatePerson_id')))
            self._client = self.getInstance(CClientInfo, forceRef(record.value('client_id')))
            self._contract = self.getInstance(CContractInfo, forceRef(record.value('contract_id')))
            self._prevEventDate = CDateInfo(forceDate(record.value('prevEventDate')))
            self._setDate = CDateTimeInfo(forceDateTime(record.value('setDate')))
            self._setPerson = self.getInstance(CPersonInfo, forceRef(record.value('setPerson_id')))
            self._execDate = CDateTimeInfo(forceDateTime(record.value('execDate')))
            self._execPerson = self.getInstance(CPersonInfo, forceRef(record.value('execPerson_id')))
            self._isPrimary = forceInt(record.value('isPrimary'))
            self._order = forceInt(record.value('order'))
            self._result = self.getInstance(CResultInfo, forceRef(record.value('result_id')))
            self._nextEventDate = CDateInfo(forceDate(record.value('nextEventDate')))
            self._payStatus = forceInt(record.value('payStatus'))
            self._typeAsset = self.getInstance(CEmergencyTypeAssetInfo, forceRef(record.value('typeAsset_id')))
            self._note = self._notes = forceString(record.value('note'))
            self._curator = self.getInstance(CPersonInfo, forceRef(record.value('curator_id')))
            self._assistant = self.getInstance(CPersonInfo, forceRef(record.value('assistant_id')))
            self._actions = self.getInstance(CActionInfoList, self.id, self.isExecutionPlan)
            self._diagnosises = self.getInstance(CDiagnosticInfoList, self.id)
            self._diagnosises51 = self.getInstance(CDiagnosticForTypeInfoList, self.id, u'51')
            self._diagnosises52 = self.getInstance(CDiagnosticForTypeInfoList, self.id, u'52')
            self._diagnosises53 = self.getInstance(CDiagnosticForTypeInfoList, self.id, u'53')
            self._diagnosises54 = self.getInstance(CDiagnosticForTypeInfoList, self.id, u'54')
            self._feeds = self.getInstance(CFeedInfoList, self.id)
            self._visits = self.getInstance(CVisitInfoList, self.id)
            self._dispansIPhase = self.getInstance(CActionDispansPhaseInfo, self.id, 1)
            self._dispansIIPhase = self.getInstance(CActionDispansPhaseInfo, self.id, 2)
            self._localContract = self.getInstance(CEventLocalContractInfo, self.id)
            self._mes = self.getInstance(CMesInfo, forceRef(record.value('MES_id')))
            self._mesSpecification = self.getInstance(CMesSpecificationInfo, forceRef(record.value('mesSpecification_id')))
            self._patientModel = self.getInstance(CPatientModelInfo, forceRef(record.value('patientModel_id')))
            self._cureType     = self.getInstance(CCureTypeInfo, forceRef(record.value('cureType_id')))
            self._cureMethod   = self.getInstance(CCureMethodInfo, forceRef(record.value('cureMethod_id')))
            self._prevEvent = self.getInstance(CEventInfo, forceRef(record.value('prevEvent_id')))
            self._tempInvalidList = self.getTempInvalidList()
            self._tempInvalidPatronageList = self.getTempInvalidList(patronage=True)
            self._relative = self.getInstance(CClientInfo, forceRef(record.value('relative_id')))
            self._clientEvents = self.getEventCount(self._clientId)
            self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._csgList = self.getInstance(CCSGInfoList, self.id)
            self._srcDate = CDateInfo(forceDate(record.value('srcDate')))
            self._srcNumber = forceString(record.value('srcNumber'))
            self._documentLocation = self.getInstance(CDocumentLocationInfo, forceInt(record.value('client_id')), forceString(record.value('externalId')))
            self._vouchers = self.getInstance(CVoucherInfoList, self.id)
            self._hospitalBedOrgStructure = self.getInstance(COrgStructureInfo, self.hBedOSId)
            return True
        else:
            self._clientId = None
            self._clientEvents = []
            self._pregnancyWeek = 0
            self._eventType = self.getInstance(CEventTypeInfo, None)
            self._externalId = ''
            self._org = self.getInstance(COrgInfo, None)
            self._relegateOrg = self.getInstance(COrgInfo, None)
            self._relegatePerson = self.getInstance(CPersonInfo, None)
            self._client = self.getInstance(CClientInfo, None)
            self._contract = self.getInstance(CContractInfo, None)
            self._prevEventDate = CDateInfo()
            self._setDate = CDateTimeInfo()
            self._setPerson = self.getInstance(CPersonInfo, None)
            self._execDate = CDateTimeInfo()
            self._execPerson = self.getInstance(CPersonInfo, None)
            self._isPrimary = 0
            self._order = 0
            self._result = self.getInstance(CResultInfo, None)
            self._nextEventDate = CDateInfo()
            self._payStatus = 0
            self._typeAsset = self.getInstance(CEmergencyTypeAssetInfo, None)
            self._note = self._notes = ''
            self._curator = self.getInstance(CPersonInfo, None)
            self._assistant = self.getInstance(CPersonInfo, None)
            self._actions = self.getInstance(CActionInfoList, None)
            self._diagnosises = self.getInstance(CDiagnosticInfoList, None)
            self._diagnosises51 = self.getInstance(CDiagnosticForTypeInfoList, None, u'51')
            self._diagnosises52 = self.getInstance(CDiagnosticForTypeInfoList, None, u'52')
            self._diagnosises53 = self.getInstance(CDiagnosticForTypeInfoList, None, u'53')
            self._diagnosises54 = self.getInstance(CDiagnosticForTypeInfoList, None, u'54')
            self._feeds = self.getInstance(CFeedInfoList, None)
            self._visits = self.getInstance(CVisitInfoList, None)
            self._localContract = self.getInstance(CEventLocalContractInfo, None)
            self._mes = self.getInstance(CMesInfo, None)
            self._mesSpecification = self.getInstance(CMesSpecificationInfo, None)
            self._patientModel = self.getInstance(CPatientModelInfo, None)
            self._cureType     = self.getInstance(CCureTypeInfo, None)
            self._cureMethod   = self.getInstance(CCureMethodInfo, None)
            self._prevEvent = self.getInstance(CEventInfo, None)
            self._tempInvalidList = {}
            self._tempInvalidPatronageList = {}
            self._relative = self.getInstance(CClientInfo, None)
            self._createDatetime = CDateTimeInfo()
            self._modifyDatetime = CDateTimeInfo()
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._csgList = self.getInstance(CCSGInfoList, None)
            self._srcDate = CDateInfo()
            self._srcNumber = ''
            self._documentLocation = self.getInstance(CDocumentLocationInfo, None, None)
            self._vouchers = self.getInstance(CVoucherInfoList, None)
            self._hospitalBedOrgStructure = self.getInstance(COrgStructureInfo, None)
            return False


    pregnancyWeek = property(lambda self: self.load()._pregnancyWeek)
    eventType   = property(lambda self: self.load()._eventType)
    externalId  = property(lambda self: self.load()._externalId)
    org         = property(lambda self: self.load()._org)
    relegateOrg = property(lambda self: self.load()._relegateOrg)
    relegatePerson = property(lambda self: self.load()._relegatePerson)
    client      = property(lambda self: self.load()._client)
    contract    = property(lambda self: self.load()._contract)
    prevEventDate = property(lambda self: self.load()._prevEventDate)
    setDate     = property(lambda self: self.load()._setDate)
    setTime     = property(lambda self: self.load()._setTime)
    setPerson   = property(lambda self: self.load()._setPerson)
    execDate    = property(lambda self: self.load()._execDate)
    execTime    = property(lambda self: self.load()._execTime)
    execPerson  = property(lambda self: self.load()._execPerson)
    isPrimary   = property(lambda self: self.load()._isPrimary)
    order       = property(lambda self: self.load()._order)
    result      = property(lambda self: self.load()._result)
    nextEventDate = property(lambda self: self.load()._nextEventDate)
    payStatus   = property(lambda self: self.load()._payStatus)
    typeAsset   = property(lambda self: self.load()._typeAsset)
    note        = property(lambda self: self.load()._note)
    notes       = property(lambda self: self.load()._notes)
    curator     = property(lambda self: self.load()._curator)
    assistant   = property(lambda self: self.load()._assistant)
    finance     = property(lambda self: self.contract.finance)
    actions     = property(lambda self: self.load()._actions)
    diagnosises = property(lambda self: self.load()._diagnosises)
    diagnosises51 = property(lambda self: self.load()._diagnosises51)
    diagnosises52 = property(lambda self: self.load()._diagnosises52)
    diagnosises53 = property(lambda self: self.load()._diagnosises53)
    diagnosises54 = property(lambda self: self.load()._diagnosises54)
    feeds       = property(lambda self: self.load()._feeds)
    visits      = property(lambda self: self.load()._visits)
    localContract = property(lambda self: self.load()._localContract)
    mes         = property(lambda self: self.load()._mes)
    mesSpecification = property(lambda self: self.load()._mesSpecification)
    patientModel= property(lambda self: self.load()._patientModel)
    cureType    = property(lambda self: self.load()._cureType)
    cureMethod  = property(lambda self: self.load()._cureMethod)
    prevEvent   = property(lambda self: self.load()._prevEvent)
    tempInvalidList = property(lambda self: self.load()._tempInvalidList)
    tempInvalidPatronageList = property(lambda self: self.load()._tempInvalidPatronageList)
    relative      = property(lambda self: self.load()._relative)
    clientEvents      = property(lambda self: self.load()._clientEvents)
    createDatetime      = property(lambda self: self.load()._createDatetime)
    modifyDatetime      = property(lambda self: self.load()._modifyDatetime)
    modifyPerson   = property(lambda self: self.load()._modifyPerson)
    createPerson   = property(lambda self: self.load()._createPerson)
    csgList = property(lambda self: self.load()._csgList)
    srcDate = property(lambda self: self.load()._srcDate)
    srcNumber = property(lambda self: self.load()._srcNumber)
    isDirty = property(lambda self: self._isDirty)
    documentLocation = property(lambda self: self.load()._documentLocation)
    vouchers      = property(lambda self: self.load()._vouchers)
    hospitalBedOrgStructure = property(lambda self: self.load()._hospitalBedOrgStructure)


class CCentralizedAccountingEventInfoList(CInfoList):
    def __init__(self, context, accountIdList, isExecutionPlan=False, hBedOSIdDict={}, isSelected=False):
        CInfoList.__init__(self, context)
        self.idList = accountIdList
        self.isExecutionPlan = isExecutionPlan
        self.hBedOSIdDict = hBedOSIdDict
        self.isSelected = isSelected


    def _load(self):
        self._items = [ self.getInstance(CCentralizedAccountingEventInfo, id, self.isExecutionPlan, self.hBedOSIdDict.get(id, None)) for id in self.idList ]
        return True
       
    
class CCSGInfoList(CInfoList):
    def __init__(self, context, eventId):
        CInfoList.__init__(self, context)
        self.eventId = eventId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Event_CSG')
        idList = db.getIdList(table, 'id', table['master_id'].eq(self.eventId), 'id')
        self._items = [ self.getInstance(CCSGInfo, id) for id in idList ]
        return True


class CAnatomicalLocalizationsInfo(CRBInfo):
    tableName = 'rbAnatomicalLocalizations'

    def _initByRecord(self, record):
        self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
        self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
        self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
        self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
        groupId = forceRef(record.value('group_id'))
        self._group = self.getInstance(CAnatomicalLocalizationsInfo, groupId) if groupId else None
        self._latinName = forceString(record.value('latinName'))
        self._area = forceString(record.value('area'))
        self._laterality = forceInt(record.value('laterality'))
        self._synonyms = forceString(record.value('synonyms'))
        self._SNOMED_CT = forceString(record.value('SNOMED_CT'))


    def _initByNull(self):
        self._createDatetime = CDateTimeInfo()
        self._modifyDatetime = CDateTimeInfo()
        self._modifyPerson = self.getInstance(CPersonInfo, None)
        self._createPerson = self.getInstance(CPersonInfo, None)
        self._group = None
        self._latinName = u''
        self._area = u''
        self._laterality = u''
        self._synonyms = u''
        self._SNOMED_CT = u''

    createDatetime = property(lambda self: self.load()._createDatetime)
    modifyDatetime = property(lambda self: self.load()._modifyDatetime)
    modifyPerson   = property(lambda self: self.load()._modifyPerson)
    createPerson   = property(lambda self: self.load()._createPerson)
    group = property(lambda self: self.load()._group)
    latinName = property(lambda self: self.load()._latinName)
    area = property(lambda self: self.load()._area)
    laterality = property(lambda self: self.load()._laterality)
    synonyms = property(lambda self: self.load()._synonyms)
    SNOMED_CT = property(lambda self: self.load()._SNOMED_CT)

class CActionPropertyTemplateInfo(CRBInfo):
    tableName = 'ActionPropertyTemplate'