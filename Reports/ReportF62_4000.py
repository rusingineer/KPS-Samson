# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import *

from library.Utils      import *
from Events.Utils       import getWorkEventTypeFilter
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import dateRangeAsStr
from Orgs.Utils         import *


MainRows = [
    ( u'ВСЕГО',                               u'',      u'01'),
    ( u'Центральный ФО',                      u'30',    u'02'),
    ( u'Белгородская область',                u'14',    u'03'),
    ( u'Брянская область',                    u'15',    u'04'),
    ( u'Владимирская область',                u'17',    u'05'),
    ( u'Воронежская область',                 u'20',    u'06'),
    ( u'Ивановская область',                  u'24',    u'07'),
    ( u'Калужская область',                   u'29',    u'08'),
    ( u'Костромская область',                 u'34',    u'09'),
    ( u'Курская область',                     u'38',    u'10'),
    ( u'Липецкая область',                    u'42',    u'11'),
    ( u'Московская область',                  u'46',    u'12'),
    ( u'Орловская область',                   u'54',    u'13'),
    ( u'Рязанская область',                   u'61',    u'14'),
    ( u'Смоленская область',                  u'66',    u'15'),
    ( u'Тамбовская область',                  u'68',    u'16'),
    ( u'Тверская область',                    u'28',    u'17'),
    ( u'Тульская область',                    u'70',    u'18'),
    ( u'Ярославская область',                 u'78',    u'19'),
    ( u'г. Москва',                           u'45',    u'20'),
    ( u'Северо-Западный ФО',                  u'31',    u'21'),
    ( u'Республика Карелия',                  u'86',    u'22'),
    ( u'Республика Коми',                     u'87',    u'23'),
    ( u'Архангельская область',               u'11',    u'24'),
    ( u'Ненецкий авт. округ',                 u'11100', u'25'),
    ( u'Вологодская область',                 u'19',    u'26'),
    ( u'Калининградская область',             u'27',    u'27'),
    ( u'Ленинградская область',               u'41',    u'28'),
    ( u'Мурманская область',                  u'47',    u'29'),
    ( u'Новгородская область',                u'49',    u'30'),
    ( u'Псковская область',                   u'58',    u'31'),
    ( u'г. Санкт-Петербург',                  u'40',    u'32'),
    ( u'Южный ФО',                            u'32',    u'33'),
    ( u'Республика Адыгея',                   u'79',    u'34'),
    ( u'Республика Калмыкия',                 u'89',    u'35'),
    ( u'Краснодарский край',                  u'03',    u'36'),
    ( u'Астраханская область',                u'12',    u'37'),
    ( u'Волгоградская область',               u'18',    u'38'),
    ( u'Ростовская область',                  u'60',    u'39'),
    ( u'Северо-Кавказский ФО',                u'33',    u'40'),
    ( u'Республика Дагестан',                 u'82',    u'41'),
    ( u'Республика Ингушетия',                u'26',    u'42'),
    ( u'Кабардино-Балкарская Республика',     u'83',    u'43'),
    ( u'Карачаево-Черкесская Республика',     u'91',    u'44'),
    ( u'Республика Северная Осетия –Алания',  u'90',    u'45'),
    ( u'Чеченская Республика',                u'96',    u'46'),
    ( u'Ставропольский край',                 u'07',    u'47'),
    ( u'Приволжский ФО',                      u'34',    u'48'),
    ( u'Республика Башкортостан',             u'80',    u'49'),
    ( u'Республика Марий Эл',                 u'88',    u'50'),
    ( u'Республика Мордовия',                 u'89',    u'51'),
    ( u'Республика Татарстан',                u'92',    u'52'),
    ( u'Удмуртская Республика',               u'94',    u'53'),
    ( u'Чувашская Республика',                u'97',    u'54'),
    ( u'Пермский край',                       u'57',    u'55'),
    ( u'Кировская область',                   u'33',    u'56'),
    ( u'Нижегородская область',               u'22',    u'57'),
    ( u'Оренбургская область',                u'53',    u'58'),
    ( u'Пензенская область',                  u'56',    u'59'),
    ( u'Самарская область',                   u'36',    u'60'),
    ( u'Саратовская область',                 u'63',    u'61'),
    ( u'Ульяновская область',                 u'73',    u'62'),
    ( u'Уральский ФО',                        u'34',    u'63'),
    ( u'Курганская область',                  u'37',    u'64'),
    ( u'Свердловская область',                u'65',    u'65'),
    ( u'Тюменская область',                   u'71',    u'66'),
    ( u'Ханты-Мансийский авт. округ – Югра',  u'71100', u'67'),
    ( u'Ямало-Ненецкий авт. округ',           u'71140', u'68'),
    ( u'Челябинская область',                 u'75',    u'69'),
    ( u'Сибирский ФО',                        u'35',    u'70'),
    ( u'Республика Алтай',                    u'84',    u'71'),
    ( u'Республика Бурятия',                  u'81',    u'72'),
    ( u'Республика Тыва',                     u'93',    u'73'),
    ( u'Республика Хакасия',                  u'95',    u'74'),
    ( u'Алтайский край',                      u'01',    u'75'),
    ( u'Забайкальский край',                  u'76',    u'76'),
    ( u'Красноярский край',                   u'04',    u'77'),
    ( u'Иркутская область',                   u'25',    u'78'),
    ( u'Кемеровская область',                 u'32',    u'79'),
    ( u'Новосибирская область',               u'50',    u'80'),
    ( u'Омская область',                      u'52',    u'81'),
    ( u'Томская область',                     u'69',    u'82'),
    ( u'Дальневосточный ФО',                  u'36',    u'83'),
    ( u'Республика Саха (Якутия)',            u'98',    u'84'),
    ( u'Камчатский край',                     u'30',    u'85'),
    ( u'Приморский край',                     u'05',    u'86'),
    ( u'Хабаровский край',                    u'08',    u'87'),
    ( u'Амурская область',                    u'10',    u'88'),
    ( u'Магаданская область',                 u'44',    u'89'),
    ( u'Сахалинская область',                 u'64',    u'90'),
    ( u'Еврейская авт. область',              u'99',    u'91'),
    ( u'Чукотский авт. округ',                u'77',    u'92'),
    ( u'Крымский ФО',                         u'8880',  u'93'),
    ( u'Республика Крым',                     u'35',    u'94'),
    ( u'г. Севастополь',                      u'67',    u'95'),
    ( u'г. Байконур',                         u'8880',  u'96'),
    ( u'Граждане СНГ',                        u'9990',  u'97'),
    ( u'Лица без гражданства',                u'9999',  u'98'),
]


okrugNumberRows = [u'02', u'21', u'33', u'40', u'48', u'63', u'70', u'83', u'93']

noCodeRows = [u'9990', u'9999']

OkrugRows = {
# Центральный ФО u'30'
                u'14':u'30'+u'FO',
                u'15':u'30'+u'FO',
                u'17':u'30'+u'FO',
                u'20':u'30'+u'FO',
                u'24':u'30'+u'FO',
                u'29':u'30'+u'FO',
                u'34':u'30'+u'FO',
                u'38':u'30'+u'FO',
                u'42':u'30'+u'FO',
                u'46':u'30'+u'FO',
                u'54':u'30'+u'FO',
                u'61':u'30'+u'FO',
                u'66':u'30'+u'FO',
                u'68':u'30'+u'FO',
                u'28':u'30'+u'FO',
                u'70':u'30'+u'FO',
                u'78':u'30'+u'FO',
                u'45':u'30'+u'FO',

# Северо-Западный ФО u'31'
                u'86':u'31'+u'FO',
                u'87':u'31'+u'FO',
                u'11':u'31'+u'FO',
                u'11100':u'31'+u'FO',
                u'19':u'31'+u'FO',
                u'27':u'31'+u'FO',
                u'41':u'31'+u'FO',
                u'47':u'31'+u'FO',
                u'49':u'31'+u'FO',
                u'58':u'31'+u'FO',
                u'40':u'31'+u'FO',

# Южный ФО u'32'
                u'79':u'32'+u'FO',
                u'89':u'32'+u'FO', # Республика Калмыкия ?
                u'03':u'32'+u'FO',
                u'12':u'32'+u'FO',
                u'18':u'32'+u'FO',
                u'60':u'32'+u'FO',

# Северо-Кавказский ФО u'33'
                u'82':u'33'+u'FO',
                u'26':u'33'+u'FO',
                u'83':u'33'+u'FO',
                u'91':u'33'+u'FO',
                u'90':u'33'+u'FO',
                u'96':u'33'+u'FO',
                u'07':u'33'+u'FO',

# Приволжский ФО u'34'            ?????????????????
                u'80':u'34'+u'FO',
                u'88':u'34'+u'FO',
                u'89':u'34'+u'FO', # Республика Мордовия ?
                u'92':u'34'+u'FO',
                u'94':u'34'+u'FO',
                u'97':u'34'+u'FO',
                u'57':u'34'+u'FO',
                u'33':u'34'+u'FO',
                u'22':u'34'+u'FO',
                u'53':u'34'+u'FO',
                u'56':u'34'+u'FO',
                u'36':u'34'+u'FO',
                u'63':u'34'+u'FO',
                u'73':u'34'+u'FO',

# Уральский ФО u'34'               ???????????????
                u'37':u'34_63'+u'FO',
                u'65':u'34_63'+u'FO',
                u'71':u'34_63'+u'FO',
                u'71100':u'34_63'+u'FO',
                u'71140':u'34_63'+u'FO',
                u'75':u'34_63'+u'FO',

# Сибирский ФО u'35'
                u'84':u'35'+u'FO',
                u'81':u'35'+u'FO',
                u'93':u'35'+u'FO',
                u'95':u'35'+u'FO',
                u'01':u'35'+u'FO',
                u'76':u'35'+u'FO',
                u'04':u'35'+u'FO',
                u'25':u'35'+u'FO',
                u'32':u'35'+u'FO',
                u'50':u'35'+u'FO',
                u'52':u'35'+u'FO',
                u'69':u'35'+u'FO',

# Дальневосточный ФО u'36'
                u'98':u'36'+u'FO',
                u'30':u'36'+u'FO',
                u'05':u'36'+u'FO',
                u'08':u'36'+u'FO',
                u'10':u'36'+u'FO',
                u'44':u'36'+u'FO',
                u'64':u'36'+u'FO',
                u'99':u'36'+u'FO',
                u'77':u'36'+u'FO',

# Крымский ФО u'8880'
                u'35':u'8880'+u'FO',
                u'67':u'8880'+u'FO',
             }


def selectData(params):
    begDate        = params.get('begDate', QDate())
    endDate        = params.get('endDate', QDate())
    isSelectRegion = params.get('isSelectRegion', 0)
    stmt="""
SELECT
    COUNT(Visit.id) AS countVisit,
    SUM(AIE.payedSum) AS payedSumEvent,
    SUM(AIV.payedSum) AS payedSumVisit,
    Client.id AS clientId,
    Event.id AS eventId,
    Event.setDate,
    Event.execDate,
    IF(rbEventTypePurpose.code = '1', 1, 0) AS isIllness,
    IF(rbEventTypePurpose.code = '6', 1, 0) AS isRehabilitation,
    IF(Event.order IN (6), 1, 0) AS isUrgency,
    IF(rbMedicalAidType.code IN ('6'), 1, 0) AS isAmbAidType,
    IF(rbMedicalAidType.code IN ('7'), 1, 0) AS isDSAidType,
    IF(rbMedicalAidType.code IN ('1', '2', '3'), 1, 0) AS isStatAidType,
    IF(rbMedicalAidType.code IN ('8'), 1, 0) AS isSanKurAidType,
    IF((rbMedicalAidType.code NOT IN ('1', '2', '3', '6', '7', '8')
    AND rbEventTypePurpose.code !='6'), 1, 0) AS isOtherAidType,
    IF(FV.code = '1', 1, 0) AS isVisitBudget,
    IF(FV.code = '2', 1, 0) AS isVisitOMS,
    IF(FE.code = '1', 1, 0) AS isEventBudget,
    IF(FE.code = '1', (SELECT kladr.KLADR.OCATD
    FROM ClientAddress
         INNER JOIN Address ON (Address.id = ClientAddress.address_id AND Address.deleted = 0)
         INNER JOIN AddressHouse ON (AddressHouse.id = Address.house_id AND AddressHouse.deleted = 0)
         INNER JOIN kladr.KLADR ON kladr.KLADR.CODE = AddressHouse.KLADRCode
    WHERE ClientAddress.client_id = Event.client_id
          AND ClientAddress.id = (SELECT MAX(CA.id)
                                  FROM ClientAddress AS CA
                                  WHERE CA.client_id = Event.client_id
                                        AND CA.deleted = 0 AND CA.type = %(isSelectRegion)s)), '') AS kladrOCATDBudget,
    IF(FE.code = '2', 1, 0) AS isEventOMS,
    IF(FE.code = '2', (SELECT kladr.KLADR.OCATD
        FROM ClientPolicy
        INNER JOIN Organisation ON Organisation.id = ClientPolicy.insurer_id
        INNER JOIN kladr.KLADR ON kladr.KLADR.CODE = Organisation.area
        WHERE ClientPolicy.client_id = Event.client_id
              AND ClientPolicy.id = getClientPolicyIdForDate(Event.client_id, 1, Event.execDate, Event.id)), '') AS kladrOCATDOMS,
    IF(EXISTS(SELECT QuotaType.class
        FROM Action
        INNER JOIN ActionType ON ActionType.id = Action.actionType_id
        INNER JOIN QuotaType ON QuotaType.id = ActionType.quotaType_id
        WHERE Action.event_id = Event.id AND Action.deleted = 0 AND ActionType.deleted = 0
        AND QuotaType.deleted = 0 AND QuotaType.class = 0), 1,
        IF(EXISTS(SELECT QuotaType.class
            FROM Action
            INNER JOIN ActionType ON ActionType.id = Action.actionType_id
            INNER JOIN QuotaType ON QuotaType.id = ActionType.quotaType_id
            INNER JOIN ActionType_QuotaType ON ActionType_QuotaType.quotaType_id = QuotaType.id
            WHERE ActionType_QuotaType.master_id = ActionType.id AND QuotaType.deleted = 0
            AND QuotaType.class = 0 AND Action.event_id = Event.id), 1, 0)
       ) AS isQuotaTypeWTMP,
    EXISTS(SELECT Client_Quoting.id
           FROM Client_Quoting
           WHERE Client_Quoting.master_id = Client.id
           AND Client_Quoting.deleted = 0
           AND Client_Quoting.status IN (7, 8, 9)
           AND (Client_Quoting.dateRegistration IS NULL
           OR (DATE(Client_Quoting.dateRegistration) >= DATE(%(begDate)s)
           AND DATE(Client_Quoting.dateRegistration) <= DATE(%(endDate)s)))
          ) AS isQuotaClientTypeWTMP,
    EXISTS(SELECT ClientSocStatus.id
        FROM ClientSocStatus
        LEFT JOIN rbSocStatusClass AS SSC ON SSC.id = ClientSocStatus.socStatusClass_id
        LEFT JOIN rbSocStatusType AS SST ON SST.id = ClientSocStatus.socStatusType_id
        WHERE ClientSocStatus.client_id = Event.client_id
            AND ClientSocStatus.deleted = 0
            AND ClientSocStatus.id = (SELECT MAX(CS.id)
                                      FROM ClientSocStatus AS CS
                                      WHERE CS.client_id = Event.client_id
                                            AND CS.deleted = 0
                                            AND ((CS.begDate IS NULL AND CS.endDate IS NULL)
                                            OR ((CS.endDate IS NULL OR DATE(CS.endDate) >= DATE(%(begDate)s))
                                            AND (CS.begDate IS NULL OR DATE(CS.begDate) <= DATE(%(endDate)s)))))
            AND ((SSC.code = 8 AND SST.code IN (%(codeList)s))
                OR (ClientSocStatus.document_id IS NOT NULL
                    AND (ClientSocStatus.socStatusType_id IS NULL
                        OR (SSC.code = 8 AND TRIM(SST.code) = ''))))) AS isCitizensSNG,
    EXISTS(SELECT ClientSocStatus.id
        FROM ClientSocStatus
        LEFT JOIN rbSocStatusClass AS SSC ON SSC.id = ClientSocStatus.socStatusClass_id
        LEFT JOIN rbSocStatusType AS SST ON SST.id = ClientSocStatus.socStatusType_id
        WHERE ClientSocStatus.client_id = Event.client_id
            AND ClientSocStatus.deleted = 0
            AND ClientSocStatus.id = (SELECT MAX(CS.id)
                                      FROM ClientSocStatus AS CS
                                      WHERE CS.client_id = Event.client_id
                                            AND CS.deleted = 0
                                            AND ((CS.begDate IS NULL AND CS.endDate IS NULL)
                                            OR ((CS.endDate IS NULL OR DATE(CS.endDate) >= DATE(%(begDate)s))
                                            AND (CS.begDate IS NULL OR DATE(CS.begDate) <= DATE(%(endDate)s)))))
            AND (ClientSocStatus.document_id IS NULL
                 AND (ClientSocStatus.socStatusType_id IS NULL
                        OR (SSC.code = 8 AND TRIM(SST.code) = '')))) AS isNotCitizens

FROM  Event
      INNER JOIN Contract  ON (Contract.id = Event.contract_id AND Contract.deleted = 0)
      LEFT JOIN  Visit     ON (Event.id = Visit.event_id AND Visit.deleted = 0
                            AND Visit.finance_id IN (SELECT rbFinance.id FROM rbFinance WHERE rbFinance.code IN ('1', '2'))
                            AND DATE(Event.setDate) <= DATE(Visit.date)
                            AND (%(condJoinVisits)s))
      INNER JOIN EventType ON EventType.id = Event.eventType_id
      LEFT JOIN rbEventTypePurpose ON rbEventTypePurpose.id = EventType.purpose_id
      INNER JOIN Client    ON Client.id = Event.client_id
      LEFT JOIN rbMedicalAidType ON rbMedicalAidType.id = EventType.medicalAidType_id
      LEFT JOIN rbFinance AS FV  ON FV.id = Visit.finance_id
      LEFT JOIN rbFinance AS FE  ON FE.id = Contract.finance_id
      LEFT JOIN Account_Item AS AIE ON (Event.id = AIE.event_id AND AIE.deleted = 0 AND AIE.reexposeItem_id IS NULL AND AIE.date IS NOT NULL)
      LEFT JOIN Account_Item AS AIV ON (Visit.id = AIV.visit_id AND AIV.deleted = 0 AND AIV.reexposeItem_id IS NULL AND AIV.date IS NOT NULL)

WHERE Event.deleted = 0
AND EventType.deleted = 0
AND Client.deleted = 0
AND (FE.code IN ('1', '2') OR FV.code IN ('1', '2'))
AND %(cond)s
AND (NOT EXISTS(SELECT ClientAddress.id
    FROM ClientAddress
    WHERE ClientAddress.client_id = Event.client_id AND ClientAddress.deleted = 0)
OR
    EXISTS(SELECT ClientAddress.id
    FROM ClientAddress
    WHERE ClientAddress.client_id = Event.client_id
          AND ClientAddress.deleted = 0
          AND ClientAddress.id = (SELECT MAX(CA.id)
                                  FROM ClientAddress AS CA
                                  WHERE CA.client_id = Event.client_id
                                        AND CA.deleted = 0
                                        AND CA.type = %(isSelectRegion)s)))

GROUP BY clientId, eventId, Event.setDate, Event.execDate,
isIllness, isRehabilitation,
isUrgency, isAmbAidType, isDSAidType, isStatAidType, isSanKurAidType, isOtherAidType,
isQuotaTypeWTMP, isQuotaClientTypeWTMP, isVisitBudget, isVisitOMS, isEventBudget,
isEventOMS, kladrOCATDBudget, kladrOCATDOMS, isCitizensSNG, isNotCitizens
    """
    db = QtGui.qApp.db
    tableVisit  = db.table('Visit')
    tableEvent  = db.table('Event')
    cond = []
    joinVisits = []
    if begDate and not begDate.isNull():
        joinVisits.append(tableVisit['date'].ge(begDate))
    if endDate and not endDate.isNull():
        joinVisits.append(tableVisit['date'].lt(endDate.addDays(1)))
    if begDate and not begDate.isNull():
        cond.append(tableEvent['execDate'].ge(begDate))
    if endDate and not endDate.isNull():
        cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))
    return db.query(stmt % dict(cond            = db.joinAnd(cond),
                                condJoinVisits  = db.joinAnd(joinVisits),
                                begDate         = db.formatDate(begDate),
                                endDate         = db.formatDate(endDate),
                                isSelectRegion  = isSelectRegion,
                                codeList        = (u','.join(u''' '%s' '''''%(code) for code in (u'м031', u'м051', u'м398', u'м417', u'м643', u'м762', u'м795', u'м860', u'м804')))
                                ))


class CReportF62_4000(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Форма 62 (4000)', u'Форма 62 (4000)')


    def getSetupDialog(self, parent):
        result = CReportF62SetupDialog(parent)
        return result


    def getDescription(self, params):
        begDate        = params.get('begDate', QDate())
        endDate        = params.get('endDate', QDate())
        isSelectRegion = params.get('isSelectRegion', 0)
        rows = []
        if begDate or endDate:
            rows.append(dateRangeAsStr(u'за период', begDate, endDate))
        if isSelectRegion is not None:
            rows.append(u'адрес ' + (u'регистрации', u'проживания', u'страховая медицинская организация')[isSelectRegion])
        rows.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        return rows


    def build(self, params):
        def createDictToRowIdx(mainRow):
            dictToRowIdx = {}
            for row, codeList in enumerate(mainRow):
                if codeList[2] in okrugNumberRows:
                    if codeList[2] == u'63':
                        dictToRowIdx[u'34_63'+u'FO'] = row
                    else:
                        dictToRowIdx[codeList[1]+u'FO'] = row
                else:
                    dictToRowIdx[codeList[1]] = row
            return dictToRowIdx
        db = QtGui.qApp.db
        reportRowSize = 50
        query = selectData(params)
        eventIdList = []
        clientIdList = []
        mapMainRows = createDictToRowIdx( [mainRow for mainRow in MainRows] )
        reportData = [ [0]*reportRowSize for row in xrange(len(MainRows)) ]
        while query.next():
            record                = query.record()
            clientId              = forceRef(record.value('clientId'))
            eventId               = forceRef(record.value('eventId'))
            setDate               = forceDate(record.value('setDate'))
            execDate              = forceDate(record.value('execDate'))
            countVisit            = forceInt(record.value('countVisit'))
            payedSumEvent         = forceDouble(record.value('payedSumEvent'))
            isQuotaTypeWTMP       = forceBool(record.value('isQuotaTypeWTMP'))
            isQuotaClientTypeWTMP = forceBool(record.value('isQuotaClientTypeWTMP'))
            isIllness             = forceBool(record.value('isIllness'))
            isRehabilitation      = forceBool(record.value('isRehabilitation'))
            isUrgency             = forceBool(record.value('isUrgency'))
            isAmbAidType          = forceBool(record.value('isAmbAidType'))
            isDSAidType           = forceBool(record.value('isDSAidType'))
            isStatAidType         = forceBool(record.value('isStatAidType'))
            isSanKurAidType       = forceBool(record.value('isSanKurAidType'))
            isOtherAidType        = forceBool(record.value('isOtherAidType'))
            isVisitBudget         = forceBool(record.value('isVisitBudget'))
            isVisitOMS            = forceBool(record.value('isVisitOMS'))
            isEventBudget         = forceBool(record.value('isEventBudget'))
            isEventOMS            = forceBool(record.value('isEventOMS'))
            kladrOCATDBudget      = forceString(record.value('kladrOCATDBudget'))
            kladrOCATDOMS         = forceString(record.value('kladrOCATDOMS'))
            isPolliativAidType    = True #forceBool(record.value('isPolliativAidType'))
            isCitizensSNG         = forceBool(record.value('isCitizensSNG'))
            isNotCitizens         = forceBool(record.value('isNotCitizens'))
            def setReportLine(reportData, findRow, setAll = False, Okrug = False):
                reportLine = reportData[findRow]
                if isAmbAidType:
                    if isVisitBudget:
                        reportLine[0] += countVisit
                    if isVisitOMS:
                        reportLine[1] += countVisit
                    if isIllness and eventId and (eventId not in eventIdList or Okrug):
                        if isEventBudget:
                            reportLine[2] += 1
                        if isEventOMS:
                            reportLine[3] += 1
                        if isEventBudget:
                            reportLine[4] += payedSumEvent
                            reportLine[47] += payedSumEvent
                            reportLine[48] += payedSumEvent
                        if isEventOMS:
                            reportLine[5] += payedSumEvent
                            reportLine[47] += payedSumEvent
                            reportLine[49] += payedSumEvent
                    if isUrgency:
                        if isVisitBudget:
                            reportLine[6] += countVisit
                        if isVisitOMS:
                            reportLine[7] += countVisit
                        if isEventBudget:
                            reportLine[8] += payedSumEvent
                        if isEventOMS:
                            reportLine[9] += payedSumEvent
                if isDSAidType:
                    if isEventBudget:
                        reportLine[10] += countVisit
                    if isEventOMS:
                        reportLine[11] += countVisit
                    if clientId and (clientId not in clientIdList or Okrug):
                        if isEventBudget:
                            reportLine[12] += 1
                        if isEventOMS:
                            reportLine[13] += 1
                    if isEventBudget:
                        reportLine[14] += payedSumEvent
                        reportLine[47] += payedSumEvent
                        reportLine[48] += payedSumEvent
                    if isEventOMS:
                        reportLine[15] += payedSumEvent
                        reportLine[47] += payedSumEvent
                        reportLine[49] += payedSumEvent
                if isStatAidType:
                    if eventId and (eventId not in eventIdList or Okrug):
                        if isEventBudget:
                            reportLine[16] += 1
                        if isEventOMS:
                            reportLine[17] += 1
                        if isEventBudget:
                            reportLine[18] += setDate.daysTo(execDate)
                        if isEventOMS:
                            reportLine[19] += setDate.daysTo(execDate)
                        if isEventBudget:
                            reportLine[20] += payedSumEvent
                            reportLine[47] += payedSumEvent
                            reportLine[48] += payedSumEvent
                        if isEventOMS:
                            reportLine[21] += payedSumEvent
                            reportLine[47] += payedSumEvent
                            reportLine[49] += payedSumEvent
                        if isQuotaClientTypeWTMP:
                            if isEventBudget:
                                reportLine[22] += 1
                            if isEventOMS:
                                reportLine[23] += 1
                        if isQuotaTypeWTMP:    # if isQuotaClientTypeWTMP and isQuotaTypeWTMP:
                            if isEventBudget:
                                reportLine[24] += 1
                            if isEventOMS:
                                reportLine[25] += 1
                        if isQuotaTypeWTMP:
                            if isEventBudget:
                                reportLine[26] += setDate.daysTo(execDate)
                                reportLine[28] += payedSumEvent
                            if isEventOMS:
                                reportLine[27] += setDate.daysTo(execDate)
                                reportLine[29] += payedSumEvent
                if isRehabilitation:
                    if eventId and (eventId not in eventIdList or Okrug):
                        if isEventBudget:
                            reportLine[30] += 1
                        if isEventOMS:
                            reportLine[31] += 1
                        if isEventBudget:
                            reportLine[32] += setDate.daysTo(execDate)
                        if isEventOMS:
                            reportLine[33] += setDate.daysTo(execDate)
                        if isEventBudget:
                            reportLine[34] += payedSumEvent
                        if isEventOMS:
                            reportLine[35] += payedSumEvent
                if isPolliativAidType: # ???????????????
                    #if eventId and (eventId not in eventIdList or Okrug):
                        #if isEventBudget:
                    reportLine[36] = u'-'   # += 1
                    #if isEventOMS:
                    reportLine[37] = u'-'   # += 1
                    #if isEventBudget:
                    reportLine[38] = u'-'   # += setDate.daysTo(execDate)
                    #if isEventOMS:
                    reportLine[39] = u'-'   # += setDate.daysTo(execDate)
                    #if isEventBudget:
                    reportLine[40] = u'-'   # += payedSumEvent
                    reportLine[47] += 0     # += payedSumEvent
                    reportLine[48] += 0     # += payedSumEvent
                    #if isEventOMS:
                    reportLine[41] = u'-'   # += payedSumEvent
                    reportLine[47] += 0     # += payedSumEvent
                    reportLine[49] += 0     # += payedSumEvent
                if isSanKurAidType:
                    if eventId and (eventId not in eventIdList or Okrug):
                        if isEventBudget:
                            reportLine[42] += 1
                        if isEventBudget:
                            reportLine[43] += setDate.daysTo(execDate)
                        if isEventBudget:
                            reportLine[44] += payedSumEvent
                            reportLine[47] += payedSumEvent
                            reportLine[48] += payedSumEvent
                if isOtherAidType:
                    if eventId and (eventId not in eventIdList or Okrug):
                        if isEventBudget:
                            reportLine[45] += payedSumEvent
                            reportLine[47] += payedSumEvent
                            reportLine[48] += payedSumEvent
                        if isEventOMS:
                            reportLine[46] += payedSumEvent
                            reportLine[47] += payedSumEvent
                            reportLine[49] += payedSumEvent
                if eventId and eventId not in eventIdList and not setAll:
                    eventIdList.append(eventId)
                if clientId and clientId not in clientIdList and not setAll:
                    clientIdList.append(clientId)
                reportData[findRow] = reportLine
            firstRow = mapMainRows.get(u'', -1)
            if firstRow > -1:
                setReportLine(reportData, firstRow, True)
            for kladrOCATD in [kladrOCATDBudget, kladrOCATDOMS]:
                if kladrOCATD:
                    for code, row in mapMainRows.items():
                        if code not in noCodeRows and code and QString(kladrOCATD).startsWith(code, Qt.CaseInsensitive):
                            setReportLine(reportData, row)
                            codeOkrug = OkrugRows.get(code, None)
                            if codeOkrug:
                                rowOkrug = mapMainRows.get(codeOkrug, None)
                                if rowOkrug:
                                    setReportLine(reportData, rowOkrug, False, True)
            if isCitizensSNG or isNotCitizens:
                if isCitizensSNG:
                    row = mapMainRows.get(u'9990', -1)
                    if row > -1:
                        setReportLine(reportData, row, True, True)
                if isNotCitizens:
                    row = mapMainRows.get(u'9999', -1)
                    if row > -1:
                        setReportLine(reportData, row, True, True)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [
            ('11.6%',[u'Субъекты Российской Федерации',              u'',                                                        u'',                                                  u'',                                                                      u'',       u'1'],  CReportBase.AlignLeft),
            ('1.7%', [u'Коды ОКАТО и ОКЭР',                          u'',                                                        u'',                                                  u'',                                                                      u'',       u'2'],  CReportBase.AlignLeft),
            ('1.7%', [u'№ стр.',                                     u'',                                                        u'',                                                  u'',                                                                      u'',       u'3'],  CReportBase.AlignLeft),
            ('1.7%', [u'Объемы оказания и финансирования:',          u'медицинской помощи, оказанной амбулаторно',               u'всего',                                             u'посещений, ед',                                                         u'бюджет', u'4'],  CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'5'],  CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'обращений в связи с заболеваниями, ед',                                 u'бюджет', u'6'],  CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'7'],  CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'руб',                                                                   u'бюджет', u'8'],  CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'9'],  CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'из них в неотложной форме',                         u'посещений, ед',                                                         u'бюджет', u'10'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'11'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'руб',                                                                   u'бюджет', u'12'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'13'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'медицинской помощи в условиях дневного стационара',       u'',                                                  u'пациенто-дней, ед',                                                     u'бюджет', u'14'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'15'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'пациентов, чел.',                                                       u'бюджет', u'16'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'17'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'руб',                                                                   u'бюджет', u'18'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'19'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'медицинской помощи, оказанной стационарно',               u'всего',                                             u'случаев госпитализации, ед',                                            u'бюджет', u'20'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'21'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'койко-дней, ед',                                                        u'бюджет', u'22'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'23'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'руб',                                                                   u'бюджет', u'24'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'25'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'из них высокотехнологичной медицинской помощи',     u'утверждено пациентов, чел.',                                            u'бюджет', u'26'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'27'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'исполнено пациентов, чел.',                                             u'бюджет', u'28'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'29'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'койко-дней, ед',                                                        u'бюджет', u'30'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'31'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'руб',                                                                   u'бюджет', u'32'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'33'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'из них медицинской реабилитации',                   u'случаев  госпитализации, ед',                                           u'бюджет', u'34'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'35'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'койко-дней, ед',                                                        u'бюджет', u'36'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'37'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'руб',                                                                   u'бюджет', u'38'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'39'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'паллиативной медицинской помощи в стационарных условиях', u'',                                                  u'случаев  госпитализации, ед',                                           u'бюджет', u'40'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'41'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'койко-дней, ед',                                                        u'бюджет', u'42'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'43'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'руб',                                                                   u'бюджет', u'44'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'45'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'санаторно-курортного лечения',                            u'',                                                  u'случаев  госпитализации, ед',                                           u'бюджет', u'46'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'койко-дней, ед',                                                        u'бюджет', u'47'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'руб',                                                                   u'бюджет', u'48'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'прочих видов медицинских и иных услуг, руб',              u'',                                                  u'',                                                                      u'бюджет', u'49'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'',                                                        u'',                                                  u'',                                                                      u'ОМС',    u'50'], CReportBase.AlignLeft),
            ('1.7%', [u'Всего (гр. 8+9+18+19+24+25+44+45+48+49+50)', u'',                                                        u'',                                                  u'',                                                                      u'',       u'51'], CReportBase.AlignLeft),
            ('1.7%', [u'в том числе:',                               u'бюджет (гр.8+18+24+44+48+49)',                            u'',                                                  u'',                                                                      u'',       u'52'], CReportBase.AlignLeft),
            ('1.7%', [u'',                                           u'ОМС (гр.9+19+25+45+50)',                                  u'',                                                  u'',                                                                      u'',       u'53'], CReportBase.AlignLeft),
            ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0,  5, 1)
        table.mergeCells(0, 1,  5, 1)
        table.mergeCells(0, 2,  5, 1)
        table.mergeCells(0, 3,  1, 47)
        table.mergeCells(1, 3,  1, 10)
        table.mergeCells(2, 3,  1, 6)
        table.mergeCells(3, 3,  1, 2)
        table.mergeCells(3, 5,  1, 2)
        table.mergeCells(3, 7,  1, 2)
        table.mergeCells(2, 9,  1, 4)
        table.mergeCells(3, 9,  1, 2)
        table.mergeCells(3, 11,  1, 2)
        table.mergeCells(1, 13,  2, 6)
        table.mergeCells(3, 13,  1, 2)
        table.mergeCells(3, 15,  1, 2)
        table.mergeCells(3, 17,  1, 2)
        table.mergeCells(1, 19,  1, 20)
        table.mergeCells(2, 19,  1, 6)
        table.mergeCells(3, 19,  1, 2)
        table.mergeCells(3, 21,  1, 2)
        table.mergeCells(3, 23,  1, 2)
        table.mergeCells(2, 25,  1, 8)
        table.mergeCells(3, 25,  1, 2)
        table.mergeCells(3, 27,  1, 2)
        table.mergeCells(3, 29,  1, 2)
        table.mergeCells(3, 31,  1, 2)
        table.mergeCells(2, 33,  1, 6)
        table.mergeCells(3, 33,  1, 2)
        table.mergeCells(3, 35,  1, 2)
        table.mergeCells(3, 37,  1, 2)
        table.mergeCells(1, 39,  2, 6)
        table.mergeCells(2, 39,  2, 2)
        table.mergeCells(3, 39,  1, 2)
        table.mergeCells(3, 41,  1, 2)
        table.mergeCells(3, 43,  1, 2)
        table.mergeCells(2, 41,  1, 2)
        table.mergeCells(2, 43,  1, 2)
        table.mergeCells(1, 45,  2, 3)
        table.mergeCells(1, 35, 1, 2)
        table.mergeCells(1, 37, 1, 2)
        table.mergeCells(1, 39, 1, 2)
        table.mergeCells(1, 41, 1, 2)
        table.mergeCells(1, 43, 1, 2)
        table.mergeCells(1, 45, 1, 3)
        table.mergeCells(1, 48, 3, 2)
        table.mergeCells(0, 50, 5, 1)
        table.mergeCells(0, 51, 1, 2)
        table.mergeCells(1, 51, 4, 1)
        table.mergeCells(1, 52, 4, 1)
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        for row, keyVal in enumerate(MainRows):
            reportLine = reportData[row]
            i = table.addRow()
            okrugFormat = (boldChars if keyVal[2] in okrugNumberRows else None)
            table.setText(i, 0, keyVal[0], charFormat = okrugFormat)
            table.setText(i, 1, keyVal[1], charFormat = okrugFormat)
            table.setText(i, 2, keyVal[2], charFormat = okrugFormat)
            for col, val in enumerate(reportLine):
                table.setText(i, col+3, val, charFormat = okrugFormat)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        return doc


from Ui_ReportF62Setup import Ui_ReportF62SetupDialog

class CReportF62SetupDialog(QtGui.QDialog, Ui_ReportF62SetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.selectVisible = True


    def setSelectRegionVisible(self, flag = True):
        self.selectVisible = flag
        self.lblSelectRegion.setVisible(flag)
        self.cmbSelectRegion.setVisible(flag)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbSelectRegion.setCurrentIndex(params.get('isSelectRegion', 0))


    def params(self):
        params = {}
        params['begDate'] = self.edtBegDate.date()
        params['endDate'] = self.edtEndDate.date()
        params['isSelectRegion'] = self.cmbSelectRegion.currentIndex()
        return params


