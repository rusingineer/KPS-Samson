# -*- coding: utf-8 -*-
from PyQt4 import QtGui
from EconomicAnalisysSetupDialog import getCond
from library.Utils import forceString

actionJoins = u"""
FROM Action
LEFT JOIN Event on Event.id = Action.event_id
LEFT JOIN Organisation currentOrg on currentOrg.id = Event.org_id
LEFT JOIN EventType ON EventType.id = Event.eventType_id
LEFT JOIN rbMedicalAidType ON EventType.medicalAidType_id = rbMedicalAidType.id
LEFT JOIN rbEventProfile ep on ep.id = EventType.eventProfile_id
LEFT JOIN ActionType ON ActionType.id = Action.actionType_id
LEFT JOIN rbService ON rbService.id = ActionType.nomenclativeService_id
LEFT JOIN Contract ON Contract.id = Event.contract_id
LEFT JOIN rbFinance on rbFinance.id = coalesce(Action.finance_id, Contract.finance_id)
LEFT JOIN Contract_Tariff ct ON ct.id = COALESCE(
                                        (SELECT ct1.id FROM Contract_Tariff ct1 WHERE ct1.master_id = Contract.id
                                            and ct1.service_id = rbService.id and ct1.deleted = 0
                                            and (ct1.endDate is not null and DATE(Action.endDate) between ct1.begDate and ct1.endDate
                                            or DATE(Action.endDate) >= ct1.begDate and ct1.endDate is null) and ct1.tariffType in (2,5) LIMIT 1),
                                        (SELECT ct2.id FROM Contract_Tariff ct2 WHERE ct2.master_id = Contract.priceListExternal_id
                                            and ct2.service_id = rbService.id and ct2.deleted = 0
                                            and (ct2.endDate is not null and DATE(Action.endDate) between ct2.begDate and ct2.endDate
                                            or DATE(Action.endDate) >= ct2.begDate and ct2.endDate is null) and ct2.tariffType in (2,5) LIMIT 1))
LEFT JOIN Diagnosis d on d.id = (SELECT diagnosis_id
  FROM Diagnostic
  INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = diagnosisType_id
  WHERE Diagnostic.event_id = Event.id
  AND Diagnostic.deleted = 0
  AND rbDiagnosisType.code IN ('1', '2', '4')
  ORDER BY rbDiagnosisType.code
  LIMIT 1
  )
LEFT JOIN Person ON Person.id = Action.person_id
LEFT JOIN rbSpeciality PersonSpeciality ON PersonSpeciality.id = Person.speciality_id
LEFT JOIN Client on Client.id = Event.client_id
LEFT JOIN ClientPolicy on ClientPolicy.id = COALESCE((SELECT MAX(cp2.id) 
                                                      FROM ClientPolicy cp2
                                                      WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
    (select MAX(cp.begDate) from ClientPolicy cp
            WHERE cp.client_id = Client.id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.execDate)))),
   (SELECT MAX(cp2.id)
            FROM ClientPolicy cp2
            WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
            (select MAX(cp.begDate)
              from ClientPolicy cp
              WHERE cp.client_id = Client.id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate BETWEEN Event.execDate AND ADDDATE(DATE(Event.execDate), 30)
              )),
  (SELECT MAX(cp2.id)
          FROM ClientPolicy cp2
          WHERE cp2.client_id = Event.relative_id AND cp2.deleted = 0 AND cp2.begDate =
          (select MAX(cp.begDate)
          from ClientPolicy cp
          WHERE cp.client_id = Event.relative_id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.execDate))
             )))
LEFT JOIN Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
LEFT JOIN rbMedicalAidType mt ON mt.id = case when rbMedicalAidType.regionalCode in ('271', '272') and Event.execDate >= '2020-05-01' then (select mat.id from rbMedicalAidType mat where mat.regionalCode = IF(rbMedicalAidType.regionalCode = '271', '21', '22') limit 1) else rbMedicalAidType.id end
"""

visitJoins = u"""
FROM Visit
LEFT JOIN Event on Event.id = Visit.event_id
LEFT JOIN EventType  ON EventType.id = Event.eventType_id
LEFT JOIN rbService ON rbService.id = Visit.service_id
LEFT JOIN rbMedicalAidType ON EventType.medicalAidType_id = rbMedicalAidType.id
LEFT JOIN rbEventProfile ep on ep.id = EventType.eventProfile_id
LEFT JOIN Contract ON Contract.id = Event.contract_id
LEFT JOIN rbFinance on rbFinance.id = coalesce(Visit.finance_id, Contract.finance_id)
LEFT JOIN Contract_Tariff ct ON ct.id = (COALESCE(
                                           (SELECT ct1.id FROM Contract_Tariff ct1 WHERE ct1.master_id = Contract.id
                                                and ct1.tariffType = 0 and ct1.service_id = rbService.id and ct1.deleted = 0
                                                and (ct1.endDate is not null and DATE(Visit.date) between ct1.begDate and ct1.endDate
                                                or DATE(Visit.date) >= ct1.begDate and ct1.endDate IS NULL) LIMIT 1),
                                           (SELECT ct2.id FROM Contract_Tariff ct2 WHERE ct2.master_id = Contract.priceListExternal_id
                                                and ct2.tariffType = 0 and ct2.service_id = rbService.id and ct2.deleted = 0
                                                and (ct2.endDate is not null and DATE(Visit.date) between ct2.begDate and ct2.endDate
                                                or DATE(Visit.date) >= ct2.begDate and ct2.endDate IS NULL) LIMIT 1))
)
LEFT JOIN Person ON Person.id = Visit.person_id
LEFT JOIN Client on Client.id = Event.client_id
LEFT JOIN ClientPolicy on ClientPolicy.id = COALESCE((SELECT MAX(cp2.id) 
                                                      FROM ClientPolicy cp2
                                                      WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
    (select MAX(cp.begDate) from ClientPolicy cp
            WHERE cp.client_id = Client.id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate <= Event.setDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.setDate)))),
   (SELECT MAX(cp2.id)
            FROM ClientPolicy cp2
            WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
            (select MAX(cp.begDate)
              from ClientPolicy cp
              WHERE cp.client_id = Client.id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate BETWEEN Event.setDate AND ADDDATE(DATE(Event.execDate), 30)
              )),
  (SELECT MAX(cp2.id)
          FROM ClientPolicy cp2
          WHERE cp2.client_id = Event.relative_id AND cp2.deleted = 0 AND cp2.begDate =
          (select MAX(cp.begDate)
          from ClientPolicy cp
          WHERE cp.client_id = Event.relative_id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate <= Event.setDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.setDate))
             )))
LEFT JOIN Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
LEFT JOIN rbMedicalAidType mt ON mt.id = case when rbMedicalAidType.regionalCode in ('271', '272') and Event.execDate >= '2020-05-01' then (select mat.id from rbMedicalAidType mat where mat.regionalCode = IF(rbMedicalAidType.regionalCode = '271', '21', '22') limit 1) else rbMedicalAidType.id end
LEFT JOIN Diagnosis d on d.id = (SELECT diagnosis_id
  FROM Diagnostic
  INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = diagnosisType_id
  WHERE Diagnostic.event_id = Event.id
  AND Diagnostic.deleted = 0
  AND rbDiagnosisType.code IN ('1', '2', '4')
  ORDER BY rbDiagnosisType.code
  LIMIT 1
  )
"""

mesJoins = u"""
FROM Event
LEFT JOIN mes.MES on MES.id = Event.MES_id
LEFT JOIN EventType ON EventType.id = Event.eventType_id
LEFT JOIN rbMedicalAidType ON EventType.medicalAidType_id = rbMedicalAidType.id
LEFT JOIN rbEventProfile ep on ep.id = EventType.eventProfile_id
LEFT JOIN Client on Client.id = Event.client_id
LEFT JOIN rbService ON rbService.infis = MES.code
LEFT JOIN Diagnosis d on d.id = (SELECT diagnosis_id
  FROM Diagnostic
  INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = diagnosisType_id
  WHERE Diagnostic.event_id = Event.id
  AND Diagnostic.deleted = 0
  AND rbDiagnosisType.code IN ('1', '2', '4')
  ORDER BY rbDiagnosisType.code
  LIMIT 1
  )
LEFT JOIN Contract ON Contract.id = Event.contract_id
LEFT JOIN rbFinance on rbFinance.id = Contract.finance_id
LEFT JOIN Contract_Tariff ct ON ct.id = COALESCE(
                                          (SELECT ct1.id FROM Contract_Tariff ct1 WHERE ct1.master_id = Contract.id
                                              and ct1.service_id = rbService.id and ct1.deleted = 0
                                              and (ct1.endDate is not null and DATE(Event.execDate) between ct1.begDate and ct1.endDate
                                              or DATE(Event.execDate) >= ct1.begDate and ct1.endDate is null) and ct1.tariffType = 13 LIMIT 1),
                                          (SELECT ct2.id FROM Contract_Tariff ct2 WHERE ct2.master_id = Contract.priceListExternal_id
                                              and ct2.service_id = rbService.id and ct2.deleted = 0
                                              and (ct2.endDate is not null and DATE(Event.execDate) between ct2.begDate and ct2.endDate
                                              or DATE(Event.execDate) >= ct2.begDate and ct2.endDate is null) and ct2.tariffType = 13 LIMIT 1))
LEFT JOIN Person ON Person.id = Event.execPerson_id
LEFT JOIN ClientPolicy on ClientPolicy.id = COALESCE((SELECT MAX(cp2.id) 
                                                      FROM ClientPolicy cp2
                                                      WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
    (select MAX(cp.begDate) from ClientPolicy cp
            WHERE cp.client_id = Client.id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate <= Event.setDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.setDate)))),
   (SELECT MAX(cp2.id)
            FROM ClientPolicy cp2
            WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
            (select MAX(cp.begDate)
              from ClientPolicy cp
              WHERE cp.client_id = Client.id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate BETWEEN Event.setDate AND ADDDATE(DATE(Event.execDate), 30)
              )),
  (SELECT MAX(cp2.id)
          FROM ClientPolicy cp2
          WHERE cp2.client_id = Event.relative_id AND cp2.deleted = 0 AND cp2.begDate =
          (select MAX(cp.begDate)
          from ClientPolicy cp
          WHERE cp.client_id = Event.relative_id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate <= Event.setDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.setDate))
             )))
LEFT JOIN Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
LEFT JOIN rbMedicalAidType mt ON mt.id = rbMedicalAidType.id
"""

csgJoins = u"""
FROM Event_CSG
LEFT JOIN Event on Event.id = Event_CSG.master_id
LEFT JOIN Organisation currentOrg on currentOrg.id = Event.org_id
LEFT JOIN EventType ON EventType.id = Event.eventType_id
LEFT JOIN rbMedicalAidType ON EventType.medicalAidType_id = rbMedicalAidType.id
LEFT JOIN rbEventProfile ep on ep.id = EventType.eventProfile_id
LEFT JOIN rbService ON rbService.infis = Event_CSG.CSGCode
LEFT JOIN Contract ON Contract.id = Event.contract_id
LEFT JOIN rbFinance on rbFinance.id = Contract.finance_id
LEFT JOIN Contract_Tariff ct ON ct.id = COALESCE((SELECT ct1.id FROM Contract_Tariff ct1 WHERE ct1.master_id = Contract.id
    and ct1.service_id = rbService.id and ct1.deleted = 0
    and (ct1.endDate is not null and Event_CSG.endDate between ct1.begDate and ct1.endDate
    or Event_CSG.endDate >= ct1.begDate and ct1.endDate is null) and ct1.tariffType = 13 LIMIT 1),
      (SELECT ct2.id FROM Contract_Tariff ct2 WHERE ct2.master_id = Contract.priceListExternal_id
    and ct2.service_id = rbService.id and ct2.deleted = 0
    and (ct2.endDate is not null and Event_CSG.endDate between ct2.begDate and ct2.endDate
    or Event_CSG.endDate >= ct2.begDate and ct2.endDate is null) and ct2.tariffType = 13 LIMIT 1))
LEFT JOIN Diagnosis d on d.id = (SELECT diagnosis_id
  FROM Diagnostic
  INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = diagnosisType_id
  WHERE Diagnostic.event_id = Event.id
  AND Diagnostic.deleted = 0
  AND rbDiagnosisType.code IN ('1', '2', '4')
  ORDER BY rbDiagnosisType.code
  LIMIT 1
  )
LEFT JOIN Person ON Person.id = Event.execPerson_id
LEFT JOIN rbSpeciality PersonSpeciality ON PersonSpeciality.id = Person.speciality_id
LEFT JOIN Client on Client.id = Event.client_id
LEFT JOIN ClientPolicy on ClientPolicy.id = COALESCE((SELECT MAX(cp2.id) 
                                                      FROM ClientPolicy cp2
                                                      WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
    (select MAX(cp.begDate) from ClientPolicy cp
            WHERE cp.client_id = Client.id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.execDate)))),
   (SELECT MAX(cp2.id)
            FROM ClientPolicy cp2
            WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
            (select MAX(cp.begDate)
              from ClientPolicy cp
              WHERE cp.client_id = Client.id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate BETWEEN Event.execDate AND ADDDATE(DATE(Event.execDate), 30)
              )),
  (SELECT MAX(cp2.id)
          FROM ClientPolicy cp2
          WHERE cp2.client_id = Event.relative_id AND cp2.deleted = 0 AND cp2.begDate =
          (select MAX(cp.begDate)
          from ClientPolicy cp
          WHERE cp.client_id = Event.relative_id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.execDate))
             )))
LEFT JOIN Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
LEFT JOIN rbMedicalAidType mt ON mt.id = rbMedicalAidType.id
"""

accountJoins = u"""
FROM Account
left join rbAccountType on rbAccountType.id = Account.type_id
LEFT JOIN Contract ON Contract.id = Account.contract_id
LEFT JOIN Account_Item ON Account_Item.master_id = Account.id
LEFT JOIN Contract_Tariff ct ON ct.id = Account_Item.tariff_id
LEFT JOIN Event ON Event.id = Account_Item.event_id
LEFT JOIN Organisation currentOrg on currentOrg.id = Event.org_id
LEFT JOIN Client on Client.id = Event.client_id
LEFT JOIN EventType ON EventType.id = Event.eventType_id
LEFT JOIN rbMedicalAidType ON EventType.medicalAidType_id = rbMedicalAidType.id
LEFT JOIN rbEventProfile ep on ep.id = EventType.eventProfile_id
LEFT JOIN Action ON Action.id = Account_Item.action_id
LEFT JOIN Visit ON Visit.id = Account_Item.visit_id
LEFT JOIN Person ON Person.id = COALESCE(Visit.person_id, Action.person_id, Event.execPerson_id)
LEFT JOIN Person ActionPerson ON ActionPerson.id = Action.person_id
LEFT JOIN rbSpeciality PersonSpeciality ON PersonSpeciality.id = ActionPerson.speciality_id
LEFT JOIN rbFinance on rbFinance.id = COALESCE(Action.finance_id, Visit.finance_id, Contract.finance_id)
LEFT JOIN rbService ON rbService.id = Account_Item.service_id
LEFT JOIN Organisation AS Payer ON Payer.id = Account.payer_id
LEFT JOIN Diagnosis d on d.id = (SELECT diagnosis_id
  FROM Diagnostic
  INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = diagnosisType_id
  WHERE Diagnostic.event_id = Event.id
  AND Diagnostic.deleted = 0
  AND rbDiagnosisType.code IN ('1', '2', '4')
  ORDER BY rbDiagnosisType.code
  LIMIT 1
  )
LEFT JOIN rbMedicalAidType mt ON mt.id = case when rbMedicalAidType.regionalCode in ('271', '272') and Event.execDate >= '2020-05-01' then (select mat.id from rbMedicalAidType mat where mat.regionalCode = IF(rbMedicalAidType.regionalCode = '271', '21', '22') limit 1) else rbMedicalAidType.id end
LEFT JOIN Event_CSG ON Event_CSG.id = Account_Item.eventCSG_id
"""

actionOnlyMESJoins = u"""
LEFT JOIN mes.MES on MES.id = Event.MES_id
LEFT JOIN rbService mes_service ON mes_service.infis = MES.code
LEFT JOIN Contract_Tariff ct_mes ON ct_mes.master_id in (Contract.id, Contract.priceListExternal_id)
    and ct_mes.service_id = mes_service.id and ct_mes.deleted = 0
    and (ct_mes.endDate is not null and DATE(Event.execDate) between ct_mes.begDate and ct_mes.endDate
    or DATE(Event.execDate) >= ct_mes.begDate and ct_mes.endDate is null) and ct_mes.tariffType = 13
"""

actionCondition = u"""
WHERE Action.deleted = 0
and Event.deleted = 0
and ActionType.nomenclativeService_id is not null
and Event.expose = 1"""

visitCondition = u"""
WHERE Event.deleted = 0
and Event.expose = 1
and Visit.deleted = 0
and Visit.service_id is not null"""

mesCondition = u"""
WHERE Event.deleted = 0
and Event.expose = 1
AND Event.MES_id is not null"""

csgCondition = u"""
WHERE Event.deleted = 0
and Event.expose = 1
AND Event_CSG.CSGCode LIKE 'G%%'"""

hospitalBedProfileJoin = u"""
LEFT JOIN Action AS HospitalAction ON
            HospitalAction.id = (
                SELECT MAX(A.id)
                FROM Action A
                WHERE A.event_id = Event.id AND
                          A.deleted = 0 AND
                          A.actionType_id IN ({0})
            )
left join ActionPropertyType on ActionPropertyType.name = 'койка'
    and ActionPropertyType.actionType_id = HospitalAction.actionType_id and ActionPropertyType.deleted = 0
left join ActionProperty on ActionProperty.type_id = ActionPropertyType.id
    and ActionProperty.action_id = HospitalAction.id and ActionProperty.deleted = 0
left join ActionProperty_HospitalBed on ActionProperty_HospitalBed.id = ActionProperty.id
left join OrgStructure_HospitalBed on OrgStructure_HospitalBed.id = ActionProperty_HospitalBed.value
left join rbHospitalBedProfile on rbHospitalBedProfile.id = OrgStructure_HospitalBed.profile_id"""

accountCondition = u"WHERE Account.deleted = 0 AND Account_Item.deleted = 0"

colActionVisitPos = u"""IF(rbService.id in (select vVisitServices.id from vVisitServices), 1, 0) AS colPos"""
colActionVisitObr = u"IF(rbService.name like 'Обращен%%', 1, 0) as colObr"
colMesObr = u"0 as colObr"
colMesPos = u"0 as colPos"
colMesSMP = u" 0 as colSMP"
colActionVisitSMP = u"IF(substr(rbService.infis, 1, 7) = 'B01.044', 1, 0) as colSMP"
colActionKD = u"IF(substr(rbService.infis, 1, 1) = 'V', WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode), 0) as colKD"
colVisitKD = u"0 as colKD"
colMesKD = u"""if(mt.regionalCode in ('11', '12', '301', '302', '401', '402'),
    WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode), 0) as colKD"""
colCsgKD = u"""if(mt.regionalCode in ('11', '12', '301', '302', '401', '402') and IF(Event.execDate < '2026-01-01', substr(rbService.infis, 4, 8) not in ('st36.013', 'st36.014', 'st36.015'), substr(rbService.infis, 4, 8) not in ('st36.050', 'st36.051', 'st36.052', 'st36.053', 'st36.054')),
    WorkDays(Event_CSG.begDate, Event_CSG.endDate, EventType.weekProfileCode, mt.regionalCode), 0) as colKD"""
colAccountKD = u"IF(substr(rbService.infis, 1, 1) in ('V', 'G') AND mt.regionalCode in ('11', '12', '301', '302', '401', '402'), WorkDays(IF(Account_Item.eventCSG_id is not null, Event_CSG.begDate, Event.setDate), IF(Account_Item.eventCSG_id is not null, Event_CSG.endDate, Event.execDate), EventType.weekProfileCode, mt.regionalCode), 0) as colKD"
colAccountKDPD = u"IF(substr(rbService.infis, 1, 1) in ('V', 'G') AND mt.regionalCode in ('11', '12', '301', '302', '401', '402','41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522'), WorkDays(IF(Account_Item.eventCSG_id is not null, Event_CSG.begDate, Event.setDate), IF(Account_Item.eventCSG_id is not null, Event_CSG.endDate, Event.execDate), EventType.weekProfileCode, mt.regionalCode), 0) as colKD"
colActionVisitPD = u"0 as colPD"
colMesPD = u"""if(mt.regionalCode in ('41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522'),
    WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode), 0) as colPD"""
colCsgPD = u"""if(mt.regionalCode in ('41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522'),
    WorkDays(Event_CSG.begDate, Event_CSG.endDate, EventType.weekProfileCode, mt.regionalCode), 0) as colPD"""
colAccountPD = u"""IF(substr(rbService.infis, 1, 1) = 'G' AND mt.regionalCode in ('41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522'),
WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode), 0) as colPD"""
colMesKDPD = u"""if(mt.regionalCode in ('11', '12', '301', '302', '401', '402','41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522'),
    WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode), 0) as colKD"""
colCsgKDPD = u"""if(mt.regionalCode in ('11', '12', '301', '302', '401', '402','41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522'),
    WorkDays(Event_CSG.begDate, Event_CSG.endDate, EventType.weekProfileCode, mt.regionalCode), 0) as colKD"""
colActionVisitCSG = u"0 colCSG"
colMesCSG = u"IF(substr(rbService.infis, 1, 1) = 'G', 1, 0) as colCSG"
colActionUET = u"Action.amount * ct.uet as colUET"
colVisitMesUET = u"0 as colUET"
colAccountUET = u"Account_Item.uet as colUET"
colActionAmount = u"Action.amount as colAmount"
colVisitMesAmount = u"1 as colAmount"
colAccountAmount = u"Account_Item.amount as colAmount"
colActionSUM = u"""round(CASE
WHEN rbFinance.code <> '2' then ct.price
WHEN DATE(Event.setDate) > Action.endDate THEN 0
WHEN Action.org_id IS NOT NULL THEN 0
WHEN Event.execDate >= '2019-03-01' AND SUBSTR(rbService.infis, 1, 3) IN ('B01', 'B02', 'B04', 'B05') and mt.regionalCode in ('21', '22') and rbService.name NOT LIKE '%%обращение%%' 
    AND EXISTS(select a.id
                        from Event e
                        LEFT JOIN soc_obr u ON 1=1
                        left join rbService rs on rs.infis in (u.kusl, u.kusl2)
                        left join ActionType at on at.nomenclativeService_id = rs.id
                        left join Action a on a.event_id = e.id and a.actionType_id = at.id
                        where e.id = Event.id and u.spec = SUBSTR(rbService.infis, 5, 3) and e.deleted = 0 and a.deleted = 0
                        AND rs.infis not in ('B02.001.005', 'B02.001.006', 'B02.031.010', 'B02.047.009', 'B02.047.010')) THEN 0
WHEN mt.regionalCode IN ('232', '252', '262') AND Event.execDate >= '2019-03-01' AND SUBSTR(rbService.infis, 1, 7) NOT IN ('B04.031', 'B04.026') THEN 0
WHEN mt.regionalCode = '261' AND ep.regionalCode = '8011' AND Event.execDate >= '2019-06-01' AND SUBSTR(rbService.infis, 1, 7) NOT IN ('B04.047', 'B04.026') AND
  NOT EXISTS (SELECT
      a.id
    FROM Action a
      LEFT JOIN ActionType at
        ON at.id = a.actionType_id
      LEFT JOIN rbService s
        ON s.id = at.nomenclativeService_id
    WHERE a.event_id = Event.id
    AND a.deleted = 0
    AND s.infis IN ('B04.026.002', 'B04.047.002')) THEN 0
WHEN mt.regionalCode = '211' AND
  ep.regionalCode IN ('8008', '8014') AND
  SUBSTR(rbService.infis, 1, 7) NOT IN ('B04.026', 'B04.047') AND
  NOT EXISTS (SELECT
      a.id
    FROM Action a
      LEFT JOIN ActionType at
        ON at.id = a.actionType_id
      LEFT JOIN rbService s
        ON s.id = at.nomenclativeService_id
    WHERE a.event_id = Event.id
    AND a.deleted = 0
    AND s.infis IN ('B04.026.001.062', 'B04.047.001.061')) THEN 0 
WHEN Event.execDate >= '2019-05-01' and mt.regionalCode = '211' AND ep.regionalCode IN ('8009', '8015') 
    AND SUBSTR(rbService.infis, 1, 1) = 'A' THEN 0
WHEN mt.regionalCode IN ('271', '272') AND
  Action.endDate >= '2017-01-01' AND
  substr(Insurer.area, 1, 2) = '%(defaultRegion)s' THEN 0
WHEN mt.regionalCode = '233' AND rbService.infis IN ('B04.047.002', 'B04.047.004', 'B04.026.002')  THEN 0
WHEN mt.regionalCode = '244' AND ep.regionalCode IN ('8020') AND SUBSTR(rbService.infis, 1, 1) = 'A' THEN 0
WHEN Event.execDate >= '2020-01-01' and mt.regionalCode in ('211', '233', '244', '261', '232', '252', '262') 
         AND rbService.infis in ('B04.026.001.001', 'B04.026.001.002', 'B04.026.001.005', 'B04.026.001.006',
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
                                 'B04.053.001.019', 'B04.057.001.030')
     THEN CASE WHEN (SELECT MAX(dow) FROM CalendarException WHERE deleted = 0 AND year(Event.execDate) between begYear AND endYear AND month(Event.execDate) = month and day(Event.execDate) = day) > 5 OR WEEKDAY(Event.execDate) >= 5 THEN round(ct.price * 1.03, 2) ELSE ct.price END      
ELSE ct.price END * Action.amount, 2) AS colSUM"""
colVisitSUM = u"round(ct.price, 2) as colSUM"
colMesSUM = u"""CalcCSGTarif(Event.id, Event.execDate, rbService.infis, d.mkb,
    WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode), ct.frag1Start,
    ct.frag2Start, age(Client.birthDate, Event.setDate), mt.regionalCode, ct.master_id, ct.price) as colSUM"""
colCsgSUM = u"""IF (substr(rbService.infis, 4) = 'st02.003' AND Event.execDate >= '2025-06-01', CalcCSGTarif(Event.id, Event.execDate, rbService.infis, d.mkb,
    WorkDays(Event_CSG.begDate, Event_CSG.endDate, EventType.weekProfileCode, mt.regionalCode), ct.frag1Start,
    ct.frag2Start, age(Client.birthDate, Event.setDate), mt.regionalCode, ct.master_id, ct.price), round(ct.price, 2)) as colSUM"""
colAccountSum = u"round(Account_Item.sum, 2) as colSUM"
colExposedSum = u"0 as colExposedSUM"
colAccountExposedSum = u"round(Account_Item.exposedSum, 2) as colExposedSUM"
clientId = u"Event.client_id as colClient"
eventId = u"Event.id as colEvent"
orgStructureName = u"OrgStructure.name as colOrgStructure"
orgStructureId = u"OrgStructure.id as colOrgStructureId"
orgStructureIsFAP = u"OrgStructure.isFAP as colIsFAP"
orgStructureInfis = u"OrgStructure.infisCode as colOrgStructureInfis"
orgStructureInfisName = u"CONCAT(OrgStructure.infisCode, ' - ', OrgStructure.name) as colOrgStructureInfisName"
parentOrgStructureInfisName = u"CONCAT(parentOrgStructure.infisCode, ' - ', parentOrgStructure.name) as colParentOrgStructureInfisName"
serviceInfis = u"rbService.infis as colServiceInfis"
serviceName = u"rbService.name as colServiceName"
serviceInfisName = u"concat_ws(' ', rbService.code, rbService.name) as colServiceInfisName"
payerTitle = u"""CASE WHEN substr(Insurer.area, 1, 2) = '%(defaultRegion)s' AND Insurer.head_id is not null THEN concat_ws(' ', headInsurer.infisCode, headInsurer.shortName)
WHEN substr(Insurer.area, 1, 2) = '%(defaultRegion)s' AND Insurer.head_id is null THEN concat_ws(' ', Insurer.infisCode, Insurer.shortName)
WHEN Insurer.id is not null and substr(Insurer.area, 1, 2) <> '%(defaultRegion)s' THEN concat_ws(' ', ContractPayer.infisCode, ContractPayer.shortName)
ELSE '0000 Плательщик не определен (нет полиса)' END as colPayerTitle"""
payerInfis = u"""CASE WHEN substr(Insurer.area, 1, 2) = '%(defaultRegion)s' AND Insurer.head_id is not null THEN headInsurer.infisCode
WHEN substr(Insurer.area, 1, 2) = '%(defaultRegion)s' AND Insurer.head_id is null THEN Insurer.infisCode
WHEN Insurer.id is not null and substr(Insurer.area, 1, 2) <> '%(defaultRegion)s' THEN ContractPayer.infisCode
ELSE '0000' END as colPayerInfis"""
payerTitleAccount = u"concat_ws(' ', Payer.infisCode, Payer.shortName) as colPayerTitle"
payerInfisAccount = u"Payer.infisCode as colPayerInfis"
financeTitle = u"rbFinance.name as colFinance"
financeCode = u"rbFinance.code as colFinanceCode"
parentOrgStructure = u"parentOrgStructure.name as colParentOrgStructure"
person = u"concat(Person.lastName, ' ', Person.firstName, ' ', Person.patrName, ' (', Person.code, ')') as colPerson"
personSNILS = u'Person.SNILS as colPersonSNILS'
personFIO = u"concat(Person.lastName, ' ', Person.firstName, ' ', Person.patrName) as colPersonFIO"
MKBCode = u"m.diagID as colMKBCode"
MKBName = u"m.DiagName as colMKBName"
eventSetDate = u"Event.setDate as colEventSetDate"
eventExecDate = u"Event.execDate as colEventExecDate"
clientName = u"concat_ws(' ', Client.lastName, Client.firstName, Client.patrName) as colClientName"
age = u"age(Client.birthDate, Event.setDate) as colAge"
clientSex = u"Client.sex as colClientSex"
clientBirthDate = u"Client.birthDate as colClientBirthDate"
regAddress = u"getClientRegAddress(Client.id) as colRegAddress"
locAddress = u"getClientLocAddress(Client.id) as colLocRegAddress"
workAddress = u"getClientWork(Client.id) as colWorkAddress"
medicalType = u"mt.name as colMedicalType"
medicalTypeCode = u"mt.regionalCode as colMedicalTypeCode"
eventProfileCode = u"ep.regionalCode as colEventProfileCode"
eventType = u"EventType.name as colEventType"
eventTypeId = u"EventType.id as colEventTypeId"
specialityOKSOName = u"rbSpeciality.OKSOName as colSpecialityOKSOName"
personWithSpeciality = u"concat(Person.lastName, ' ', Person.firstName, ' ', Person.patrName, ' (', Person.code, '), ', ifnull(rbSpeciality.OKSOName, '')) as colPersonWithSpeciality"
contractName = u"concat_ws(' ', Contract.resolution, Contract.number) as colContract"
kpk = u"CONCAT(rbHospitalBedProfile.regionalCode, ' - ', rbHospitalBedProfile.name) as colKPK"
insurerCodeName = u"concat_ws(' ', Insurer.infisCode, Insurer.shortName) as colInsurerCodeName"
isWorking = u"(getClientWorkId(Client.id) is not null) as colIsWorking"
serviceActionBegDate = u"date(Action.begDate) as colServiceBegDate"
serviceVisitBegDate = u"date(Visit.date) as colServiceBegDate"
serviceMESBegDate = u"date(Event.setDate) as colServiceBegDate"
serviceCsgBegDate = u"Event_CSG.begDate as colServiceBegDate"
serviceAccountBegDate = u"IF(Visit.id is not null, date(Visit.date), IF(Action.id is not null, date(Action.begDate), date(Event.setDate))) as colServiceBegDate"
serviceActionEndDate = u"date(Action.endDate) as colServiceEndDate"
serviceVisitEndDate = u"date(Visit.date) as colServiceEndDate"
serviceMESEndDate = u"date(Event.execDate) as colServiceEndDate"
serviceCsgEndDate = u"Event_CSG.endDate as colServiceEndDate"
serviceAccountEndDate = u"IF(Visit.id is not null, date(Visit.date), IF(Action.id is not null, date(Action.endDate), date(Event.execDate))) as colServiceEndDate"
posType = u"""case 
        when substr(rbService.infis, 1, 3) in ('B01', 'B02') and rbService.name like '%%прием%%' and rbService.name not like '%%патронаж%%' and rbService.name not like '%%на дому%%' then 1
        when rbService.infis in ('B04.001.001', 'B04.008.001', 'B04.014.002', 'B04.015.003', 'B04.023.001', 'B04.026.001',
                                 'B04.027.001', 'B04.028.001', 'B04.029.001', 'B04.029.005', 'B04.040.002', 'B04.046.001',
                                 'B04.047.001', 'B04.047.003', 'B04.047.005', 'B04.050.001', 'B04.053.001', 'B04.057.001',
                                 'B04.058.005', 'B04.064.003', 'B04.065.001', 'B04.065.003', 'B04.065.005', 'B04.001.006',
                                 'B04.008.005', 'B04.009.001', 'B04.010.001', 'B04.014.007', 'B04.015.005', 'B04.023.016',
                                 'B04.026.004', 'B04.028.004', 'B04.029.006', 'B04.031.001', 'B04.031.003', 'B04.050.008',
                                 'B04.053.003', 'B04.058.002') and mt.regionalCode in ('21', '22', '31', '32') then 2
        when substr(rbService.infis, 1,3) = 'B04' and rbService.name like '%%прием%%' and rbService.name not like '%%диспансерн%%' then 3
        when (rbService.name like '%%на дому%%' or rbService.name like '%%патронаж%%') and substr(rbService.infis, 1, 3) in ('B01', 'B02') then 4
        end as colPosType"""
isAdult = u"age(Client.birthDate, Event.setDate) >= 18 as colIsAdult"
stepECO = u"""(select aps.value
        from Action ECO_Step
        left join ActionPropertyType apt on apt.actionType_id = ECO_Step.actionType_id and apt.deleted = 0
        left join ActionProperty ap on ap.type_id = apt.id and ap.action_id = ECO_Step.id and ap.deleted = 0
        left join ActionProperty_String aps on aps.id = ap.id
        where ECO_Step.id = (
                        SELECT MAX(A.id)
                        FROM Action A
                        WHERE A.event_id = Event.id AND
                                  A.deleted = 0 AND
                                  A.actionType_id IN (
                                        SELECT AT.id
                                        FROM ActionType AT
                                        WHERE AT.flatCode ='ECO_Step'
                                            AND AT.deleted = 0
                                  )
                    )
            and apt.name = 'Этап ЭКО') AS colStepECO"""
citizenship = 'rbSocStatusType.name as colCitizenship'
eventOrder = 'Event.order as colEventOrder'
colCitizenship = [citizenship] * 5
colEventOrder = [eventOrder] * 5
colUslSpec = ['substr(rbService.infis, 5, 3) as colUslSpec', 'substr(rbService.infis, 5, 3)  as colUslSpec', 'NULL  as colUslSpec', 'NULL  as colUslSpec', 'substr(rbService.infis, 5, 3)  as colUslSpec']
colPos = [colActionVisitPos, colActionVisitPos, colMesPos, colMesPos, colActionVisitPos]
colObr = [colActionVisitObr, colActionVisitObr, colMesObr, colMesPos, colActionVisitObr]
colSMP = [colActionVisitSMP, colActionVisitSMP, colMesSMP, colMesSMP, colActionVisitSMP]
colKD = [colActionKD, colVisitKD, colMesKD, colCsgKD, colAccountKD]
colPD = [colActionVisitPD, colActionVisitPD, colMesPD, colCsgPD, colAccountPD]
colKDPD = [colActionKD, colVisitKD, colMesKDPD, colCsgKDPD, colAccountKDPD]
colCSG = [colActionVisitCSG, colActionVisitCSG, colMesCSG, colMesCSG, colMesCSG]
colUET = [colActionUET, colVisitMesUET, colVisitMesUET, colVisitMesUET, colAccountUET]
colAmount = [colActionAmount, colVisitMesAmount, colVisitMesAmount, colVisitMesAmount, colAccountAmount]
colSUM = [colActionSUM, colVisitSUM, colMesSUM, colCsgSUM, colAccountSum]
colExposedSum = [colExposedSum, colExposedSum, colExposedSum, colExposedSum, colAccountExposedSum]
colClient = [clientId] * 5
colClientSex = [clientSex] * 5
colAge = [age] * 5
colPosType = [posType] * 5
colIsAdult = [isAdult] * 5
colClientBirthDate = [clientBirthDate] * 5
colRegAddress = [regAddress] * 5
colLocRegAddress = [locAddress] * 5
colWorkAddress = [workAddress] * 5
colEvent = [eventId] * 5
colOrgStructure = [orgStructureName] * 5
colOrgStructureId = [orgStructureId] * 5
colOrgStructureInfis = [orgStructureInfis] * 5
colOrgStructureInfisName = [orgStructureInfisName] * 5
colIsFAP = [orgStructureIsFAP] * 5
colParentOrgStructureInfisName = [parentOrgStructureInfisName] * 5
colKPK = [kpk] * 5
colServiceInfis = [serviceInfis] * 5
colServiceName = [serviceName] * 5
colServiceInfisName = [serviceInfisName] * 5
colServiceBegDate = [serviceActionBegDate, serviceVisitBegDate, serviceMESBegDate, serviceCsgBegDate, serviceAccountBegDate]
colServiceEndDate = [serviceActionEndDate, serviceVisitEndDate, serviceMESEndDate, serviceCsgEndDate, serviceAccountEndDate]
colPayerTitle = [payerTitle, payerTitle, payerTitle, payerTitle, payerTitleAccount]
colPayerInfis = [payerInfis, payerInfis, payerInfis, payerInfis, payerInfisAccount]
colFinance = [financeTitle] * 5
colFinanceCode = [financeCode] * 5
colParentOrgStructure = [parentOrgStructure] * 5
colPerson = [person] * 5
colPersonSNILS = [personSNILS] * 5
colPersonFIO = [personFIO] * 5
colPersonWithSpeciality = [personWithSpeciality] * 5
colMKBCode = [MKBCode] * 5
colMKBName = [MKBName] * 5
colEventSetDate = [eventSetDate] * 5
colEventExecDate = [eventExecDate] * 5
colClientName = [clientName] * 5
colMedicalType = [medicalType] * 5
colMedicalTypeCode = [medicalTypeCode] * 5
colEventProfileCode = [eventProfileCode] * 5
colEventType = [eventType] * 5
colEventTypeId = [eventTypeId] * 5
colSpecialityOKSOName = [specialityOKSOName] * 5
colContract = [contractName] * 5
colInsurerCodeName = [insurerCodeName] * 5
colIsWorking = [isWorking] * 5
colStepECO = [stepECO] * 5

def getColsStmt(cols):
    stmtCols = ['', '', '', '', '']
    for col in cols:
        for idx, item in enumerate(stmtCols):
            if stmtCols[idx]:
                stmtCols[idx] += u', ' + col[idx]
            else:
                stmtCols[idx] = col[idx]
    return stmtCols
    
def getJoinStmt(cols, params):
    joinStmt = [actionJoins, visitJoins, mesJoins, csgJoins, accountJoins]
    for idx, item in enumerate(joinStmt):
        if colInsurerCodeName in cols and idx == 4:
            joinStmt[idx] += u"""
LEFT JOIN ClientPolicy on ClientPolicy.id = COALESCE((SELECT MAX(cp2.id) 
                                                      FROM ClientPolicy cp2
                                                      WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
    (select MAX(cp.begDate) from ClientPolicy cp
            WHERE cp.client_id = Client.id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate <= Event.setDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.setDate)))),
   (SELECT MAX(cp2.id)
            FROM ClientPolicy cp2
            WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
            (select MAX(cp.begDate)
              from ClientPolicy cp
              WHERE cp.client_id = Client.id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate BETWEEN Event.setDate AND ADDDATE(DATE(Event.execDate), 30)
              )),
  (SELECT MAX(cp2.id)
          FROM ClientPolicy cp2
          WHERE cp2.client_id = Event.relative_id AND cp2.deleted = 0 AND cp2.begDate =
          (select MAX(cp.begDate)
          from ClientPolicy cp
          WHERE cp.client_id = Event.relative_id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate <= Event.setDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.setDate))
             )))
LEFT JOIN Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
"""
        if colOrgStructure in cols or colOrgStructureInfis in cols or colOrgStructureInfisName in cols or colIsFAP in cols or params.get('orgStructureId', None):
           joinStmt[idx] += u"""
LEFT JOIN OrgStructure on OrgStructure.id = Person.orgStructure_id"""
        if colParentOrgStructure in cols or colParentOrgStructureInfisName in cols:
            joinStmt[idx] += u"""
LEFT JOIN OrgStructure as parentOrgStructure on parentOrgStructure.id = OrgStructure.parent_id"""
        if colPayerTitle in cols or colPayerInfis in cols or params.get('payer', None):
            if idx < 4:
                joinStmt[idx] += u"""
LEFT JOIN Organisation AS headInsurer ON headInsurer.id = Insurer.head_id
LEFT JOIN Organisation AS ContractPayer ON ContractPayer.id = Contract.payer_id"""
        if params.get('specialityId', None) or colSpecialityOKSOName in cols or colPersonWithSpeciality in cols:
            joinStmt[idx] += u"""
LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id"""
        if colMKBCode in cols:
            joinStmt[idx] += u"""
LEFT JOIN MKB m on m.diagID = d.MKB"""
        if colCitizenship in cols:
            joinStmt[idx] += u"""
            LEFT JOIN ClientSocStatus ON ClientSocStatus.client_id = Client.id and ClientSocStatus.deleted = 0
            LEFT JOIN rbSocStatusClass ON rbSocStatusClass.id = ClientSocStatus.socStatusClass_id
            LEFT JOIN rbSocStatusType ON rbSocStatusType.id = ClientSocStatus.socStatusType_id
            """
        if params.get('profileBed', None) or colKPK in cols:
            stmt = u"""SELECT GROUP_CONCAT(AT.id) as idList
                                FROM ActionType AT
                                WHERE AT.flatCode ='moving'
                                    AND AT.deleted = 0"""
            query = QtGui.qApp.db.query(stmt)
            if query.first():
                record = query.record()
                idList = forceString(record.value('idList'))
                if not idList:
                    idList = 'null'
            joinStmt[idx] += hospitalBedProfileJoin.format(idList)
            
    return joinStmt
   
def getStmt(colsStmt, cols, groupCols, orderCols, params, queryList=['action', 'visit', 'mes', 'csg'], additionCond=u" and ct.id is not null", having='', isOnlyMES=False):
    
    actionCols, visitCols, mesCols, csgCols, accountCols = getColsStmt(cols)
    actionJoins, visitJoins, mesJoins, csgJoins, accountJoins = getJoinStmt(cols, params)
    cond = getCond(params)
    if colCitizenship in cols:
        cond += " AND rbSocStatusClass.code = '8' AND rbSocStatusType.socCode is not null"

    if params['dataType'] == 1:
        queryList = queryList
    else:
        queryList = ['account']
            
    if additionCond:
        cond += additionCond
    
    if groupCols:
        groupCols = "GROUP BY " + groupCols
    if orderCols:
        orderCols = "ORDER BY " + orderCols
    if having:
        having = u'HAVING ' + having
        
    var = dict()
    var["colsStmt"] = colsStmt
        
    stmt = u"""
%(colsStmt)s
from (
"""
        
    if 'action' in queryList:
        stmt += u"""
select %(actionCols)s
%(actionJoins)s
%(actionCondition)s
and %(cond)s
%(having)s"""
        var["actionCols"] = actionCols
        var["actionJoins"] = actionJoins
        if isOnlyMES:
            var["actionJoins"] = actionJoins + actionOnlyMESJoins
            if params['cashPayments']:
                var["actionCondition"] = actionCondition + " and Event.MES_id is not null and ct_mes.id is not null and Action.`payStatus` = 768"
            else:
                var["actionCondition"] = actionCondition + " and Event.MES_id is not null and ct_mes.id is not null"
        else:
            var["actionJoins"] = actionJoins
            if params['cashPayments']:
                var["actionCondition"] = actionCondition + " and Action.`payStatus` = 768"
            else:
                var["actionCondition"] = actionCondition

    if 'visit' in queryList:
        if 'action' in queryList:
            stmt += u" union all"
            
        stmt += u"""
select %(visitCols)s
%(visitJoins)s
%(visitCondition)s
and %(cond)s
%(having)s"""
        var["visitCols"] = visitCols
        var["visitJoins"] = visitJoins
        if params['cashPayments']:
            var["visitCondition"] = visitCondition + " and Visit.`payStatus` = 768"
        else:
            var["visitCondition"] = visitCondition

    if 'mes' in queryList:
        if 'action' in queryList or 'visit' in queryList:
            stmt += u" union all"
        stmt += u"""
select %(mesCols)s
%(mesJoins)s
%(mesCondition)s
and %(cond)s
%(having)s"""
        var["mesCols"] = mesCols
        var["mesJoins"] = mesJoins
        if params['cashPayments']:
            var["mesCondition"] = mesCondition + " and Event.`payStatus` = 768"
        else:
            var["mesCondition"] = mesCondition

    if 'csg' in queryList:
        if 'action' in queryList or 'visit' in queryList or 'mes' in queryList:
            stmt += u" union all"
        stmt += u"""
select %(csgCols)s
%(csgJoins)s
%(csgCondition)s
and %(cond)s
%(having)s"""
        var["csgCols"] = csgCols
        var["csgJoins"] = csgJoins
        if params['cashPayments']:
            var["csgCondition"] = csgCondition + " and Event.`payStatus` = 768"
        else:
            var["csgCondition"] = csgCondition

    if 'account' in queryList:
        stmt += u"""
select %(accountCols)s
%(accountJoins)s
%(accountCondition)s
and %(cond)s
%(having)s
"""
        var["accountCols"] = accountCols
        var["accountJoins"] = accountJoins
        if params['cashPayments']:
            var["accountCondition"] = accountCondition + " and Account_Item.refuseType_id is not NULL"
        else:
            var["accountCondition"] = accountCondition
            
    stmt += u""") q
%(group)s
%(order)s
"""
    var["cond"] = cond
    var["group"] = groupCols
    var["order"] = orderCols
    var["having"] = having
    
    stmt = stmt % var
    if 'defaultRegion' in stmt:
        stmt = stmt % {'defaultRegion': QtGui.qApp.provinceKLADR()[:2]}
        
    return stmt
