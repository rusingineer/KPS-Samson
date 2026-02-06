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
from PyQt4 import QtGui
from Reports.Report import CReport, CVoidSetupDialog
from Reports.ReportBase import CReportBase, createTable
from library.Utils import forceString


def getQuery(isExternal, isReexport):
    if isExternal:
        stmt = u"""
select Action.id,
concat(IF(length(trim(PersonOrgStructure.bookkeeperCode))=5, PersonOrgStructure.bookkeeperCode,
                        IF(length(trim(Parent1.bookkeeperCode))=5, Parent1.bookkeeperCode,
                          IF(length(trim(Parent2.bookkeeperCode))=5, Parent2.bookkeeperCode,
                            IF(length(trim(Parent3.bookkeeperCode))=5, Parent3.bookkeeperCode,
                              IF(length(trim(Parent4.bookkeeperCode))=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode)))))
    , '_', apv_number.value) AS m11_ornm,
IF(Action.begDate < CURDATE(), DATE_ADD(date(Action.begDate), INTERVAL '23:59' HOUR_MINUTE), Action.begDate) as m12_ordt,
case
  when apv_form.value LIKE 'планов%%' then 1
  when apv_form.value LIKE 'неотлож%%' then 2
  when apv_form.value LIKE 'экстрен%%' then 3
end as m13_ortp,
IF(length(trim(PersonOrgStructure.bookkeeperCode))=5, PersonOrgStructure.bookkeeperCode,
                        IF(length(trim(Parent1.bookkeeperCode))=5, Parent1.bookkeeperCode,
                          IF(length(trim(Parent2.bookkeeperCode))=5, Parent2.bookkeeperCode,
                            IF(length(trim(Parent3.bookkeeperCode))=5, Parent3.bookkeeperCode,
                              IF(length(trim(Parent4.bookkeeperCode))=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode))))) as m14_moscd,
HospitalOrg.infisCode as m15_modcd,
Diagnosis.MKB as m18_mkbcd,
BedProfile.code as m19_kpkcd,
substring(PersonOrgStructure.infisCode, 1, 3) as m20_sccd,
Person.code as m21_dcnm,
DATE_ADD(apv_date.value, INTERVAL '23:59' HOUR_MINUTE) as m22_dtph,
CASE apv_usok.value WHEN 'круглосуточный' THEN 1 WHEN 'дневной' THEN 2 ELSE 1 END AS m24_usok,
PolicyKind.regionalCode as a10_dct,
Policy.serial as a11_dcs,
Policy.number as a12_dcn,
Insurer.infisCode as a13_smcd,
Insurer.OKATO as a14_trcd,
Client.lastName as a15_pfio,
Client.firstName as a16_pnm,
Client.patrName as a17_pln,
case Client.sex when 1 then 'м' when 2 then 'ж' end as a18_ps,
Client.birthDate as a19_pbd,
getClientContacts(Client.id) as a20_pph,
Document.serial as a21_ps,
Document.number as a22_pn,
DocType.regionalCode as a23_dt,
formatSNILS(Client.SNILS) AS a24_sl,
IF(PolicyKind.regionalCode IN ('3', '4', '5'), Policy.number, NULL) AS a25_enp
from Action
inner join Event on Event.id = Action.event_id
left join Contract c ON c.id = Event.contract_id
left JOIN rbFinance f ON f.id = c.finance_id
LEFT JOIN EventType et ON et.id = Event.eventType_id
LEFT JOIN rbMedicalAidType mat ON mat.id = et.medicalAidType_id
inner join Client on Client.id = Event.client_id
inner join ActionType on ActionType.id = Action.actionType_id
left join ActionPropertyType as apt_number on apt_number.actionType_id = Action.actionType_id and apt_number.name = 'Номер направления' and apt_number.deleted = 0
left join ActionProperty     as ap_number  on ap_number.type_id = apt_number.id and ap_number.action_id = Action.id    AND ap_number.deleted = 0
left join ActionProperty_String as apv_number on apv_number.id = ap_number.id
left join ActionPropertyType as apt_date on apt_date.actionType_id = Action.actionType_id and apt_date.name = 'Плановая дата госпитализации' and apt_date.deleted = 0
left join ActionProperty     as ap_date  on ap_date.type_id = apt_date.id and ap_date.action_id = Action.id    AND ap_date.deleted = 0
left join ActionProperty_Date as apv_date on apv_date.id = ap_date.id
left join ActionPropertyType as apt_form on apt_form.actionType_id = Action.actionType_id and apt_form.name = 'Порядок направления' and apt_form.deleted = 0
left join ActionProperty     as ap_form  on ap_form.type_id = apt_form.id and ap_form.action_id = Action.id    AND ap_form.deleted = 0
left join ActionProperty_String as apv_form on apv_form.id = ap_form.id
left join ActionPropertyType as apt_org on apt_org.actionType_id = Action.actionType_id and apt_org.name = 'Куда направляется' and apt_org.deleted = 0
left join ActionProperty     as ap_org  on ap_org.type_id = apt_org.id and ap_org.action_id = Action.id    AND ap_org.deleted = 0
left join ActionProperty_Organisation as apv_org on apv_org.id = ap_org.id
left join Organisation as HospitalOrg on HospitalOrg.id = apv_org.value
left join ActionPropertyType as apt_profile on apt_profile.actionType_id = Action.actionType_id and apt_profile.name = 'Профиль койки' and apt_profile.deleted = 0
left join ActionProperty     as ap_profile  on ap_profile.type_id = apt_profile.id and ap_profile.action_id = Action.id    AND ap_profile.deleted = 0
left join ActionProperty_rbHospitalBedProfile as apv_profile on apv_profile.id = ap_profile.id
left join rbHospitalBedProfile as BedProfile on BedProfile.id = apv_profile.value
left join ActionPropertyType as apt_usok on apt_usok.actionType_id = Action.actionType_id and apt_usok.name = 'Тип стационара' and apt_usok.deleted = 0
left join ActionProperty     as ap_usok  on ap_usok.type_id = apt_usok.id and ap_usok.action_id = Action.id    AND ap_usok.deleted = 0
left join ActionProperty_String as apv_usok on apv_usok.id = ap_usok.id
left join Diagnosis on Diagnosis.id = getEventDiagnosis(Event.id)
left join Person on Person.id = Action.person_id
left join OrgStructure as PersonOrgStructure on PersonOrgStructure.id = Person.orgStructure_id
left join OrgStructure as Parent1 on Parent1.id = PersonOrgStructure.parent_id
left join OrgStructure as Parent2 on Parent2.id = Parent1.parent_id
left join OrgStructure as Parent3 on Parent3.id = Parent2.parent_id
left join OrgStructure as Parent4 on Parent4.id = Parent3.parent_id
left join OrgStructure as Parent5 on Parent5.id = Parent4.parent_id
left join ClientPolicy as Policy on Policy.id = getClientPolicyIdForDate(Client.id, 1, IFNULL(Event.execDate, Event.setDate), Event.id)
left join Organisation as Insurer on Insurer.id = Policy.insurer_id
left join rbPolicyKind as PolicyKind on PolicyKind.id = Policy.policyKind_id
left join ClientDocument as Document on Document.id = getClientDocumentId(Client.id)
left join rbDocumentType as DocType on DocType.id = Document.documentType_id
left join rbExternalSystem es on es.code = 'ТФОМС:План.госп.'
left join Action_Export ae ON ae.system_id = es.id AND Action.id = ae.master_id
where ActionType.flatCode = 'hospitalDirection'
and ActionType.deleted = 0
and Action.deleted = 0
and Event.deleted = 0
AND f.code in ('2', '4')
AND IF(Action.begDate < CURDATE(), DATE_ADD(date(Action.begDate), INTERVAL '23:59' HOUR_MINUTE), Action.begDate) >= (NOW() - interval 5 day)       
%s"""
    else:
        stmt = u"""
select Action.id,
concat(IF(length(trim(PersonOrgStructure.bookkeeperCode))=5, PersonOrgStructure.bookkeeperCode,
                        IF(length(trim(Parent1.bookkeeperCode))=5, Parent1.bookkeeperCode,
                          IF(length(trim(Parent2.bookkeeperCode))=5, Parent2.bookkeeperCode,
                            IF(length(trim(Parent3.bookkeeperCode))=5, Parent3.bookkeeperCode,
                              IF(length(trim(Parent4.bookkeeperCode))=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode)))))
    , '_', apv_number.value) AS m11_ornm,
IF(Action.begDate < CURDATE(), DATE_ADD(date(Action.begDate), INTERVAL '23:59' HOUR_MINUTE), Action.begDate) as m12_ordt,
case
  when apv_form.value LIKE 'планов%%' then 1
  when apv_form.value LIKE 'неотлож%%' then 2
  when apv_form.value LIKE 'экстрен%%' then 3
end as m13_ortp,
IF(length(trim(PersonOrgStructure.bookkeeperCode))=5, PersonOrgStructure.bookkeeperCode,
                        IF(length(trim(Parent1.bookkeeperCode))=5, Parent1.bookkeeperCode,
                          IF(length(trim(Parent2.bookkeeperCode))=5, Parent2.bookkeeperCode,
                            IF(length(trim(Parent3.bookkeeperCode))=5, Parent3.bookkeeperCode,
                              IF(length(trim(Parent4.bookkeeperCode))=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode))))) as m14_moscd,
IF(length(trim(os.bookkeeperCode))=5, os.bookkeeperCode,
                        IF(length(trim(destParent1.bookkeeperCode))=5, destParent1.bookkeeperCode,
                          IF(length(trim(destParent2.bookkeeperCode))=5, destParent2.bookkeeperCode,
                            IF(length(trim(destParent3.bookkeeperCode))=5, destParent3.bookkeeperCode,
                              IF(length(trim(destParent4.bookkeeperCode))=5, destParent4.bookkeeperCode, destParent5.bookkeeperCode))))) as m15_modcd,
Diagnosis.MKB as m18_mkbcd,
BedProfile.code as m19_kpkcd,
substring(PersonOrgStructure.infisCode, 1, 3) as m20_sccd,
Person.code as m21_dcnm,
DATE_ADD(apv_date.value, INTERVAL '23:59' HOUR_MINUTE) as m22_dtph,
CASE apv_usok.value WHEN 'круглосуточный' THEN 1 WHEN 'дневной' THEN 2 ELSE 1 END AS m24_usok,
PolicyKind.regionalCode as a10_dct,
Policy.serial as a11_dcs,
Policy.number as a12_dcn,
Insurer.infisCode as a13_smcd,
Insurer.OKATO as a14_trcd,
Client.lastName as a15_pfio,
Client.firstName as a16_pnm,
Client.patrName as a17_pln,
case Client.sex when 1 then 'м' when 2 then 'ж' end as a18_ps,
Client.birthDate as a19_pbd,
getClientContacts(Client.id) as a20_pph,
Document.serial as a21_ps,
Document.number as a22_pn,
DocType.regionalCode as a23_dt,
formatSNILS(Client.SNILS) AS a24_sl,
IF(PolicyKind.regionalCode IN ('3', '4', '5'), Policy.number, NULL) AS a25_enp
from Action
inner join Event on Event.id = Action.event_id
left join Contract c ON c.id = Event.contract_id
left JOIN rbFinance f ON f.id = c.finance_id
LEFT JOIN EventType et ON et.id = Event.eventType_id
LEFT JOIN rbMedicalAidType mat ON mat.id = et.medicalAidType_id
inner join Client on Client.id = Event.client_id
inner join ActionType on ActionType.id = Action.actionType_id
left join ActionPropertyType as apt_number on apt_number.actionType_id = Action.actionType_id and apt_number.name = 'Номер направления' and apt_number.deleted = 0
left join ActionProperty     as ap_number  on ap_number.type_id = apt_number.id and ap_number.action_id = Action.id    AND ap_number.deleted = 0
left join ActionProperty_String as apv_number on apv_number.id = ap_number.id
left join ActionPropertyType as apt_date on apt_date.actionType_id = Action.actionType_id and apt_date.name = 'Плановая дата госпитализации поликлиники' and apt_date.deleted = 0
left join ActionProperty     as ap_date  on ap_date.type_id = apt_date.id and ap_date.action_id = Action.id   AND ap_date.deleted = 0
left join ActionProperty_Date as apv_date on apv_date.id = ap_date.id
left join ActionPropertyType as apt_form on apt_form.actionType_id = Action.actionType_id and apt_form.name = 'Порядок направления' and apt_form.deleted = 0
left join ActionProperty     as ap_form  on ap_form.type_id = apt_form.id and ap_form.action_id = Action.id   AND ap_form.deleted = 0
left join ActionProperty_String as apv_form on apv_form.id = ap_form.id
left join ActionPropertyType as apt_org on apt_org.actionType_id = Action.actionType_id and apt_org.name = 'Подразделение' and apt_org.deleted = 0
left join ActionProperty     as ap_org  on ap_org.type_id = apt_org.id and ap_org.action_id = Action.id   AND ap_org.deleted = 0
left join ActionProperty_OrgStructure apos on apos.id = ap_org.id
left join OrgStructure  as os on os.id = apos.value
left join OrgStructure as destParent1 on destParent1.id = os.parent_id
left join OrgStructure as destParent2 on destParent2.id = destParent1.parent_id
left join OrgStructure as destParent3 on destParent3.id = destParent2.parent_id
left join OrgStructure as destParent4 on destParent4.id = destParent3.parent_id
left join OrgStructure as destParent5 on destParent5.id = destParent4.parent_id
left join ActionPropertyType as apt_profile on apt_profile.actionType_id = Action.actionType_id and apt_profile.name = 'Профиль койки' and apt_profile.deleted = 0
left join ActionProperty     as ap_profile  on ap_profile.type_id = apt_profile.id and ap_profile.action_id = Action.id   AND ap_profile.deleted = 0
left join ActionProperty_rbHospitalBedProfile as apv_profile on apv_profile.id = ap_profile.id
left join rbHospitalBedProfile as BedProfile on BedProfile.id = apv_profile.value
left join ActionPropertyType as apt_usok on apt_usok.actionType_id = Action.actionType_id and apt_usok.name = 'Тип стационара' and apt_usok.deleted = 0
left join ActionProperty     as ap_usok  on ap_usok.type_id = apt_usok.id and ap_usok.action_id = Action.id   AND ap_usok.deleted = 0
left join ActionProperty_String as apv_usok on apv_usok.id = ap_usok.id
left join Diagnosis on Diagnosis.id = getEventDiagnosis(Event.id)
left join Person on Person.id = Action.person_id
left join OrgStructure as PersonOrgStructure on PersonOrgStructure.id = Person.orgStructure_id
left join OrgStructure as Parent1 on Parent1.id = PersonOrgStructure.parent_id
left join OrgStructure as Parent2 on Parent2.id = Parent1.parent_id
left join OrgStructure as Parent3 on Parent3.id = Parent2.parent_id
left join OrgStructure as Parent4 on Parent4.id = Parent3.parent_id
left join OrgStructure as Parent5 on Parent5.id = Parent4.parent_id
left join ClientPolicy as Policy on Policy.id = getClientPolicyIdForDate(Client.id, 1, IFNULL(Event.execDate, Event.setDate), Event.id)
left join Organisation as Insurer on Insurer.id = Policy.insurer_id
left join rbPolicyKind as PolicyKind on PolicyKind.id = Policy.policyKind_id
left join ClientDocument as Document on Document.id = getClientDocumentId(Client.id)
left join rbDocumentType as DocType on DocType.id = Document.documentType_id
left join rbExternalSystem es on es.code = 'ТФОМС:План.госп.'
left join Action_Export ae ON ae.system_id = es.id AND Action.id = ae.master_id
where ActionType.flatCode = 'planning'
and Action.org_id is null
and ActionType.deleted = 0
and Action.deleted = 0
and Event.deleted = 0
AND f.code = '2'
AND IF(Action.begDate < CURDATE(), DATE_ADD(date(Action.begDate), INTERVAL '23:59' HOUR_MINUTE), Action.begDate) >= (NOW() - interval 5 day)
%s"""
    if isReexport:
        cond = u"and ae.success = 1 AND ae.dateTime >= IF(hour(now()) >= 20, curDate() + INTERVAL 20 HOUR, curDate() - INTERVAL 4 HOUR);"
    else:
        cond = u"AND IFNULL(ae.success, 0) = 0;"
    stmt = stmt % cond
    return QtGui.qApp.db.query(stmt)


def getQuery2(isReexport):
    stmt = u"""
select Action.id,
IF(INSTR(Event.srcNumber, concat(IF(RelegateOrg.OKATO <> '03000' OR LENGTH(RelegateOrg.infisCode) < 5, '88888', RelegateOrg.infisCode), '_'))=1, Event.srcNumber, concat(IF(RelegateOrg.OKATO <> '03000' OR LENGTH(RelegateOrg.infisCode) < 5, '88888', RelegateOrg.infisCode), '_', Event.srcNumber)) AS m11_ornm,
Event.srcDate as m12_ordt,
Event.order as m13_ortp,
IF(RelegateOrg.OKATO <> '03000' OR LENGTH(RelegateOrg.infisCode) < 5, '88888', RelegateOrg.infisCode) as m14_moscd,
IF(length(trim(MovingOrgStructure.bookkeeperCode))=5, MovingOrgStructure.bookkeeperCode,
                                IF(length(trim(Parent1.bookkeeperCode))=5, Parent1.bookkeeperCode,
                                  IF(length(trim(Parent2.bookkeeperCode))=5, Parent2.bookkeeperCode,
                                    IF(length(trim(Parent3.bookkeeperCode))=5, Parent3.bookkeeperCode,
                                      IF(length(trim(Parent4.bookkeeperCode))=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode))))) as m15_modcd,
Event.setDate as m16_dttmfh,
BedProfile.code as m18_kpkcd,
substring(MovingOrgStructure.infisCode, 1, 3) as m19_sccd,
IF(IFNULL(Event.externalId, '') <> '', Event.externalId, Event.id) as m20_crdnum,
Action.MKB as m21_mkbcd,
CASE
  WHEN mat.regionalCode IN ('11', '12', '301', '302', '401', '402') THEN 1
  ELSE 2 END AS m24_usok,
PolicyKind.regionalCode as a10_dct,
Policy.serial as a11_dcs,
Policy.number as a12_dcn,
Insurer.infisCode as a13_smcd,
Insurer.OKATO as a14_trcd,
Client.lastName as a15_pfio,
Client.firstName as a16_pnm,
Client.patrName as a17_pln,
case Client.sex when 1 then 'м' when 2 then 'ж' end as a18_ps,
Client.birthDate as a19_pbd,
getClientContacts(Client.id) as a20_pph,
Document.serial as a21_ps,
Document.number as a22_pn,
DocType.regionalCode as a23_dt,
formatSNILS(Client.SNILS) AS a24_sl,
IF(PolicyKind.regionalCode IN ('3', '4', '5'), Policy.number, NULL) AS a25_enp
from Action
inner join Action as Moving on Moving.id = getNextActionId(Action.event_id, Action.id, (select id from ActionType where flatCode = 'moving' and deleted = 0), Action.endDate)
inner join Event on Event.id = Action.event_id
left join Contract c ON c.id = Event.contract_id
left JOIN rbFinance f ON f.id = c.finance_id
LEFT JOIN EventType et ON et.id = Event.eventType_id
LEFT JOIN rbMedicalAidType mat ON mat.id = et.medicalAidType_id
inner join Client on Client.id = Event.client_id
inner join ActionType on ActionType.id = Action.actionType_id
left join ActionPropertyType as apt_orgstruct on apt_orgstruct.actionType_id = Moving.actionType_id and apt_orgstruct.name = 'Отделение пребывания' and apt_orgstruct.deleted = 0
left join ActionProperty as ap_orgstruct on ap_orgstruct.type_id = apt_orgstruct.id and ap_orgstruct.action_id = Moving.id   AND ap_orgstruct.deleted = 0
left join ActionProperty_OrgStructure as apv_orgstruct on apv_orgstruct.id = ap_orgstruct.id
left join OrgStructure as MovingOrgStructure on MovingOrgStructure.id = apv_orgstruct.value
left join OrgStructure as Parent1 on Parent1.id = MovingOrgStructure.parent_id
left join OrgStructure as Parent2 on Parent2.id = Parent1.parent_id
left join OrgStructure as Parent3 on Parent3.id = Parent2.parent_id
left join OrgStructure as Parent4 on Parent4.id = Parent3.parent_id
left join OrgStructure as Parent5 on Parent5.id = Parent4.parent_id
left join ActionPropertyType as apt_bed on apt_bed.actionType_id = Moving.actionType_id and apt_bed.name = 'койка' and apt_bed.deleted = 0
left join ActionProperty     as ap_bed  on ap_bed.type_id = apt_bed.id and ap_bed.action_id = Moving.id   AND ap_bed.deleted = 0
left join ActionProperty_HospitalBed as apv_bed on apv_bed.id = ap_bed.id
left join Organisation as RelegateOrg on RelegateOrg.id = Event.relegateOrg_id
left join OrgStructure_HospitalBed as HospitalBed on HospitalBed.id = apv_bed.value
left join rbHospitalBedProfile as BedProfile on BedProfile.id = HospitalBed.profile_id
left join ClientPolicy as Policy on Policy.id = getClientPolicyIdForDate(Client.id, 1, Event.setDate, Event.id)
left join Organisation as Insurer on Insurer.id = Policy.insurer_id
left join rbPolicyKind as PolicyKind on PolicyKind.id = Policy.policyKind_id
left join ClientDocument as Document on Document.id = getClientDocumentId(Client.id)
left join rbDocumentType as DocType on DocType.id = Document.documentType_id
left join rbExternalSystem es on es.code = 'ТФОМС:План.госп.'
left join Action_Export ae ON ae.system_id = es.id AND Action.id = ae.master_id
where ActionType.flatCode = 'received'
and mat.regionalCode in ('11', '12', '301', '302', '401', '402', '41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522')
and Event.order = 1
AND f.code = '2'
and ActionType.deleted = 0
and Action.deleted = 0
and Event.deleted = 0
and Action.begDate >= (NOW() - interval 5 day)
%s"""
    if isReexport:
        cond = u"and ae.success = 1 AND ae.dateTime >= IF(hour(now()) >= 20, curDate() + INTERVAL 20 HOUR, curDate() - INTERVAL 4 HOUR);"
    else:
        cond = u"AND IFNULL(ae.success, 0) = 0;"
    stmt = stmt % cond
    return QtGui.qApp.db.query(stmt)


def getQuery3(isReexport):
    stmt = u"""
select Leaved.id,
IF(INSTR(FirstEvent.srcNumber, concat(IF(RelegateOrg.OKATO <> '03000' OR LENGTH(RelegateOrg.infisCode) < 5, '88888', RelegateOrg.infisCode), '_'))=1, FirstEvent.srcNumber, concat(IF(RelegateOrg.OKATO <> '03000' OR LENGTH(RelegateOrg.infisCode) < 5, '88888', RelegateOrg.infisCode), '_', FirstEvent.srcNumber)) AS m11_ornm,
Event.srcDate as m12_ordt,
CASE FirstEvent.`order`
  WHEN 1 then 1
  WHEN 6 THEN 2
  else 3 end as m13_ortp,
IF(length(trim(LeavedOrgStructure.bookkeeperCode))=5, LeavedOrgStructure.bookkeeperCode,
                        IF(length(trim(Parent1.bookkeeperCode))=5, Parent1.bookkeeperCode,
                          IF(length(trim(Parent2.bookkeeperCode))=5, Parent2.bookkeeperCode,
                            IF(length(trim(Parent3.bookkeeperCode))=5, Parent3.bookkeeperCode,
                              IF(length(trim(Parent4.bookkeeperCode))=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode))))) as m14_modcd,
FirstEvent.setDate as m15_dttmfh,
Event.execDate as m16_dttmlv,
BedProfile.code as m18_kpkcd,
substring(LeavedOrgStructure.infisCode, 1, 3) as m19_sccd,
IF(IFNULL(Event.externalId, '') <> '', Event.externalId, Event.id) as m20_crdnum,
PolicyKind.regionalCode as a10_dct,
Policy.serial as a11_dcs,
Policy.number as a12_dcn,
Insurer.infisCode as a13_smcd,
Insurer.OKATO as a14_trcd,
Client.lastName as a15_pfio,
Client.firstName as a16_pnm,
Client.patrName as a17_pln,
case Client.sex when 1 then 'м' when 2 then 'ж' end as a18_ps,
Client.birthDate as a19_pbd,
getClientContacts(Client.id) as a20_pph,
Document.serial as a21_ps,
Document.number as a22_pn,
DocType.regionalCode as a23_dt,
formatSNILS(Client.SNILS) AS a24_sl,
IF(PolicyKind.regionalCode IN ('3', '4', '5'), Policy.number, NULL) AS a25_enp
from Action as Leaved
inner join Action as Moving on Moving.id = getPrevActionId(Leaved.event_id, Leaved.id, (select id from ActionType where flatCode = 'moving' and deleted = 0), Leaved.endDate)
inner join Action as Received on Received.id = getPrevActionId(Leaved.event_id, Leaved.id, (select id from ActionType where flatCode = 'received' and deleted = 0), Leaved.endDate)
inner join Event on Event.id = Leaved.event_id
LEFT JOIN Event FirstEvent on FirstEvent.id = Received.event_id
LEFT JOIN Organisation RelegateOrg on RelegateOrg.id = FirstEvent.relegateOrg_id
left join Contract c ON c.id = Event.contract_id
left JOIN rbFinance f ON f.id = c.finance_id
LEFT JOIN EventType et ON et.id = Event.eventType_id
LEFT JOIN rbMedicalAidType mat ON mat.id = et.medicalAidType_id
inner join Client on Client.id = Event.client_id
inner join ActionType on ActionType.id = Leaved.actionType_id
left join ActionPropertyType as apt_orgstruct on apt_orgstruct.actionType_id = Leaved.actionType_id and apt_orgstruct.name = 'Отделение' and apt_orgstruct.deleted = 0
left join ActionProperty as ap_orgstruct on ap_orgstruct.type_id = apt_orgstruct.id and ap_orgstruct.action_id = Leaved.id   AND ap_orgstruct.deleted = 0
left join ActionProperty_OrgStructure as apv_orgstruct on apv_orgstruct.id = ap_orgstruct.id
left join OrgStructure as LeavedOrgStructure on LeavedOrgStructure.id = apv_orgstruct.value
left join OrgStructure as Parent1 on Parent1.id = LeavedOrgStructure.parent_id
left join OrgStructure as Parent2 on Parent2.id = Parent1.parent_id
left join OrgStructure as Parent3 on Parent3.id = Parent2.parent_id
left join OrgStructure as Parent4 on Parent4.id = Parent3.parent_id
left join OrgStructure as Parent5 on Parent5.id = Parent4.parent_id
left join ActionPropertyType as apt_bedProfile on apt_bedProfile.actionType_id = Leaved.actionType_id and apt_bedProfile.name = 'Профиль' and apt_bedProfile.deleted = 0
left join ActionProperty as ap_bedProfile  on ap_bedProfile.type_id = apt_bedProfile.id and ap_bedProfile.action_id = Leaved.id   AND ap_bedProfile.deleted = 0
left join ActionProperty_rbHospitalBedProfile aphbp on aphbp.id = ap_bedProfile.id
left join rbHospitalBedProfile as BedProfile on BedProfile.id = aphbp.value
left join ClientPolicy as Policy on Policy.id = getClientPolicyIdForDate(Client.id, 1, Event.execDate, Event.id)
left join Organisation as Insurer on Insurer.id = Policy.insurer_id
left join rbPolicyKind as PolicyKind on PolicyKind.id = Policy.policyKind_id
left join ClientDocument as Document on Document.id = getClientDocumentId(Client.id)
left join rbDocumentType as DocType on DocType.id = Document.documentType_id
left join rbExternalSystem es on es.code = 'ТФОМС:План.госп.'
left join Action_Export ae ON ae.system_id = es.id AND Leaved.id = ae.master_id
where ActionType.flatCode = 'leaved'
and mat.regionalCode in ('11', '12', '301', '302', '401', '402', '41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522')
and ActionType.deleted = 0
and Leaved.deleted = 0
AND f.code = '2'
and Event.deleted = 0
and Leaved.endDate >= (NOW() - interval 5 day)
%s"""
    if isReexport:
        cond = u"and ae.success = 1 AND ae.dateTime >= IF(hour(now()) >= 20, curDate() + INTERVAL 20 HOUR, curDate() - INTERVAL 4 HOUR);"
    else:
        cond = u"AND IFNULL(ae.success, 0) = 0;"
    stmt = stmt % cond
    return QtGui.qApp.db.query(stmt)


def getQuery4(isReexport):
    stmt = u"""
select Action.id,
IF(length(trim(MovingOrgStructure.bookkeeperCode))=5, MovingOrgStructure.bookkeeperCode,
                        IF(length(trim(Parent1.bookkeeperCode))=5, Parent1.bookkeeperCode,
                          IF(length(trim(Parent2.bookkeeperCode))=5, Parent2.bookkeeperCode,
                            IF(length(trim(Parent3.bookkeeperCode))=5, Parent3.bookkeeperCode,
                              IF(length(trim(Parent4.bookkeeperCode))=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode))))) as m11_modcd,
Event.setDate as m12_dttmfh,
BedProfile.code as m14_kpkcd,
substring(MovingOrgStructure.infisCode, 1, 3) as m15_sccd,
IF(IFNULL(Event.externalId, '') <> '', Event.externalId, Event.id) as m16_crdnum,
Action.MKB as m17_mkbcd,
PolicyKind.regionalCode as a10_dct,
Policy.serial as a11_dcs,
Policy.number as a12_dcn,
Insurer.infisCode as a13_smcd,
Insurer.OKATO as a14_trcd,
Client.lastName as a15_pfio,
Client.firstName as a16_pnm,
Client.patrName as a17_pln,
case Client.sex when 1 then 'м' when 2 then 'ж' end as a18_ps,
Client.birthDate as a19_pbd,
getClientContacts(Client.id) as a20_pph,
Document.serial as a21_ps,
Document.number as a22_pn,
DocType.regionalCode as a23_dt,
formatSNILS(Client.SNILS) AS a24_sl,
IF(PolicyKind.regionalCode IN ('3', '4', '5'), Policy.number, NULL) AS a25_enp
from Action
inner join Action as Moving on Moving.id = getNextActionId(Action.event_id, Action.id, (select id from ActionType where flatCode = 'moving' and deleted = 0), Action.endDate)
inner join Event on Event.id = Action.event_id
LEFT JOIN EventType et ON et.id = Event.eventType_id
LEFT JOIN rbMedicalAidType mat ON mat.id = et.medicalAidType_id
left join Contract c ON c.id = Event.contract_id
left JOIN rbFinance f ON f.id = c.finance_id
inner join Client on Client.id = Event.client_id
inner join ActionType on ActionType.id = Action.actionType_id
left join ActionPropertyType as apt_orgstruct on apt_orgstruct.actionType_id = Moving.actionType_id and apt_orgstruct.name = 'Отделение пребывания' and apt_orgstruct.deleted = 0
left join ActionProperty as ap_orgstruct on ap_orgstruct.type_id = apt_orgstruct.id and ap_orgstruct.action_id = Moving.id AND ap_orgstruct.deleted = 0
left join ActionProperty_OrgStructure as apv_orgstruct on apv_orgstruct.id = ap_orgstruct.id
left join OrgStructure as MovingOrgStructure on MovingOrgStructure.id = apv_orgstruct.value
left join OrgStructure as Parent1 on Parent1.id = MovingOrgStructure.parent_id
left join OrgStructure as Parent2 on Parent2.id = Parent1.parent_id
left join OrgStructure as Parent3 on Parent3.id = Parent2.parent_id
left join OrgStructure as Parent4 on Parent4.id = Parent3.parent_id
left join OrgStructure as Parent5 on Parent5.id = Parent4.parent_id
left join ActionPropertyType as apt_bed on apt_bed.actionType_id = Moving.actionType_id and apt_bed.name = 'койка' and apt_bed.deleted = 0
left join ActionProperty as ap_bed  on ap_bed.type_id = apt_bed.id and ap_bed.action_id = Moving.id AND ap_bed.deleted = 0
left join ActionProperty_HospitalBed as apv_bed on apv_bed.id = ap_bed.id
left join OrgStructure_HospitalBed as HospitalBed on HospitalBed.id = apv_bed.value
left join rbHospitalBedProfile as BedProfile on BedProfile.id = HospitalBed.profile_id
left join ClientPolicy as Policy on Policy.id = getClientPolicyIdForDate(Client.id, 1, Event.setDate, Event.id)
left join Organisation as Insurer on Insurer.id = Policy.insurer_id
left join rbPolicyKind as PolicyKind on PolicyKind.id = Policy.policyKind_id
left join ClientDocument as Document on Document.id = getClientDocumentId(Client.id)
left join rbDocumentType as DocType on DocType.id = Document.documentType_id
left join rbExternalSystem es on es.code = 'ТФОМС:План.госп.'
left join Action_Export ae ON ae.system_id = es.id AND Action.id = ae.master_id
where ActionType.flatCode = 'received'
and mat.regionalCode in ('11', '12', '301', '302', '401', '402', '41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522')
and Event.order not in (1,6)
AND f.code = '2'
and ActionType.deleted = 0
and Action.deleted = 0
and Event.deleted = 0
and Action.begDate >= (NOW() - interval 5 day)
%s"""
    if isReexport:
        cond = u"and ae.success = 1 AND ae.dateTime >= IF(hour(now()) >= 20, curDate() + INTERVAL 20 HOUR, curDate() - INTERVAL 4 HOUR);"
    else:
        cond = u"AND IFNULL(ae.success, 0) = 0;"
    stmt = stmt % cond
    return QtGui.qApp.db.query(stmt)


class CHospital(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setOrientation(QtGui.QPrinter.Landscape)
        self.setTitle(u'Выгрузка сервиса госпитализации')

    def getSetupDialog(self, parent):
        return CVoidSetupDialog(self)

    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(self.title())
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertHtml(u'''<table><tr><td>202 - Номер направления заполнен некоректно; (столбец "номер направления" не заполнен);<br>
206 - Неверно задан МО, направившей на госпитализацию; (столбец "код МО, направившей на госпитализацию" не заполнен);<br>
218 - Код МКБ заполнен неверно; (столбец "код МКБ приемного отделения" не заполнен);<br>
219 - Код профиля койки заполнен неверно; (столбец "код профиля койки" не заполнен);<br>
220 - Код отделения заполнен неверно; (столбец "код отделения" не заполнен);<br>
222 - Неверно указана дата госпитализации; (дата направления может быть меньше текущей на 3 дня, а вот дата плановой госпитализации может быть только сегодняшней и будущей);<br>
223 - Неверно указан номер карты стационарного больного; (столбец "номер карты стационарного больного" не заполнен);<br>
229 - Номер направления не найден в базе направлений (видимо из-за незаполненого поля "номер направления").</td></tr></table>''')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        firstTitle = u'Метод "sendPlanOrdersClinic" - передача сведений о выписанных направлениях на госпитализацию в ЦОД'
        cursor.insertBlock()
        cursor.insertText(firstTitle)
        cursor.insertBlock()

        tableColumns = [
            ('3%', [u'номер направления'], CReportBase.AlignLeft),
            ('4%', [u'дата направления'], CReportBase.AlignLeft),
            ('3%', [u'форма оказания медицинской помощи'], CReportBase.AlignCenter),
            ('5%', [u'код МО, направившей на госпитализацию'], CReportBase.AlignLeft),
            ('3%', [u'код МО, куда направлен пациент'], CReportBase.AlignLeft),
            ('3%', [u'код диагноза МКБ'], CReportBase.AlignLeft),
            ('3%', [u'код профиля койки'], CReportBase.AlignCenter),
            ('2%', [u'код отделения'], CReportBase.AlignCenter),
            ('4%', [u'код медицинского работника'], CReportBase.AlignLeft),
            ('5%', [u'плановая дата госпитализации'], CReportBase.AlignLeft),
            ('4%', [u'условия оказания медицинской помощи'], CReportBase.AlignCenter),
            ('5%', [u'тип документа, подтверждающего факт страхования по обязательному медицинскому страхованию'], CReportBase.AlignCenter),
            ('3%', [u'серия полиса'], CReportBase.AlignLeft),
            ('6%', [u'номер полиса'], CReportBase.AlignLeft),
            ('2%', [u'код СМО'], CReportBase.AlignCenter),
            ('4%', [u'код территории страхования'], CReportBase.AlignLeft),
            ('4%', [u'фамилия пациента'], CReportBase.AlignLeft),
            ('4%', [u'имя пациента'], CReportBase.AlignLeft),
            ('5%', [u'отчество пациента'], CReportBase.AlignLeft),
            ('2%', [u'пол'], CReportBase.AlignCenter),
            ('4%', [u'дата рождения'], CReportBase.AlignLeft),
            ('5%', [u'контактная информация'], CReportBase.AlignLeft),
            ('4%', [u'серия документа удостоверяющего личность'], CReportBase.AlignLeft),
            ('4%', [u'номер документа удостоверяющего личность'], CReportBase.AlignLeft),
            ('3%', [u'тип документа удостоверяющего личность'], CReportBase.AlignCenter),
            ('3%', [u'СНИЛС гражданина'], CReportBase.AlignLeft),
            ('3%', [u'ЕНП гражданина'], CReportBase.AlignLeft)
        ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 1, 1)

        rowNumber = 0
        for query in [getQuery(True, False), getQuery(True, True), getQuery(False, False), getQuery(False, True)]:
            while query.next():
                record = query.record()
                row = table.addRow()
                rowNumber += 1
    
                table.setText(row, 0, forceString(record.value('m11_ornm')))
                table.setText(row, 1, forceString(record.value('m12_ordt')))
                table.setText(row, 2, forceString(record.value('m13_ortp')))
                table.setText(row, 3, forceString(record.value('m14_moscd')))
                table.setText(row, 4, forceString(record.value('m15_modcd')))
                table.setText(row, 5, forceString(record.value('m18_mkbcd')))
                table.setText(row, 6, forceString(record.value('m19_kpkcd')))
                table.setText(row, 7, forceString(record.value('m20_sccd')))
                table.setText(row, 8, forceString(record.value('m21_dcnm')))
                table.setText(row, 9, forceString(record.value('m22_dtph')))
                table.setText(row, 10, forceString(record.value('m24_usok')))
                table.setText(row, 11, forceString(record.value('a10_dct')))
                table.setText(row, 12, forceString(record.value('a11_dcs')))
                table.setText(row, 13, forceString(record.value('a12_dcn')))
                table.setText(row, 14, forceString(record.value('a13_smcd')))
                table.setText(row, 15, forceString(record.value('a14_trcd')))
                table.setText(row, 16, forceString(record.value('a15_pfio')))
                table.setText(row, 17, forceString(record.value('a16_pnm')))
                table.setText(row, 18, forceString(record.value('a17_pln')))
                table.setText(row, 19, forceString(record.value('a18_ps')))
                table.setText(row, 20, forceString(record.value('a19_pbd')))
                table.setText(row, 21, forceString(record.value('a20_pph')))
                table.setText(row, 22, forceString(record.value('a21_ps')))
                table.setText(row, 23, forceString(record.value('a22_pn')))
                table.setText(row, 24, forceString(record.value('a23_dt')))
                table.setText(row, 25, forceString(record.value('a24_sl')))
                table.setText(row, 26, forceString(record.value('a25_enp')))
            
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        firstTitle = u'Метод "sendFactOrdersHospital" - передача сведений о плановых госпитализациях в ЦОД'
        cursor.insertBlock()
        #рисуем вторую табличку
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(firstTitle)
        cursor.insertBlock()
        cursor.insertBlock()
        tableColumns = [
            ('3%', [u'номер направления'], CReportBase.AlignLeft),
            ('4%', [u'дата направления'], CReportBase.AlignLeft),
            ('3%', [u'форма оказания медицинской помощи'], CReportBase.AlignCenter),
            ('3%', [u'код МО, направившей на госпитализацию'], CReportBase.AlignLeft),
            ('3%', [u'код МО, куда направлен пациент'], CReportBase.AlignLeft),
            ('4%', [u'дата и время фактической госпитализации'], CReportBase.AlignLeft),
            ('3%', [u'код профиля койки'], CReportBase.AlignCenter),
            ('2%', [u'код отделения'], CReportBase.AlignCenter),
            ('4%', [u'номер карты стационарного больного'], CReportBase.AlignCenter),
            ('5%', [u'код МКБ приемного отделения'], CReportBase.AlignLeft),
            ('4%', [u'условия оказания медицинской помощи'], CReportBase.AlignCenter),
            ('5%', [u'тип документа, подтверждающего факт страхования по обязательному медицинскому страхованию'], CReportBase.AlignCenter),
            ('3%', [u'серия полиса'], CReportBase.AlignLeft),
            ('6%', [u'номер полиса'], CReportBase.AlignLeft),
            ('2%', [u'код СМО'], CReportBase.AlignCenter),
            ('4%', [u'код территории страхования'], CReportBase.AlignLeft),
            ('4%', [u'фамилия пациента'], CReportBase.AlignLeft),
            ('4%', [u'имя пациента'], CReportBase.AlignLeft),
            ('5%', [u'отчество пациента'], CReportBase.AlignLeft),
            ('2%', [u'пол'], CReportBase.AlignCenter),
            ('4%', [u'дата рождения'], CReportBase.AlignLeft),
            ('5%', [u'контактная информация'], CReportBase.AlignLeft),
            ('4%', [u'серия документа удостоверяющего личность'], CReportBase.AlignLeft),
            ('4%', [u'номер документа удостоверяющего личность'], CReportBase.AlignLeft),
            ('4%', [u'тип документа удостоверяющего личность'], CReportBase.AlignCenter),
            ('3%', [u'СНИЛС гражданина'], CReportBase.AlignLeft),
            ('3%', [u'ЕНП гражданина'], CReportBase.AlignLeft)
            ]
            
            
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 1, 1)

        rowNumber = 0
        for query in [getQuery2(False), getQuery2(True)]:
            while query.next():
                record = query.record()
                row = table.addRow()
                rowNumber += 1
    
                table.setText(row, 0, forceString(record.value('m11_ornm')))
                table.setText(row, 1, forceString(record.value('m12_ordt')))
                table.setText(row, 2, forceString(record.value('m13_ortp')))
                table.setText(row, 3, forceString(record.value('m14_moscd')))
                table.setText(row, 4, forceString(record.value('m15_modcd')))
                table.setText(row, 5, forceString(record.value('m16_dttmfh')))
                table.setText(row, 6, forceString(record.value('m18_kpkcd')))
                table.setText(row, 7, forceString(record.value('m19_sccd')))
                table.setText(row, 8, forceString(record.value('m20_crdnum')))
                table.setText(row, 9, forceString(record.value('m21_mkbcd')))
                table.setText(row, 10, forceString(record.value('m24_usok')))
                table.setText(row, 11, forceString(record.value('a10_dct')))
                table.setText(row, 12, forceString(record.value('a11_dcs')))
                table.setText(row, 13, forceString(record.value('a12_dcn')))
                table.setText(row, 14, forceString(record.value('a13_smcd')))
                table.setText(row, 15, forceString(record.value('a14_trcd')))
                table.setText(row, 16, forceString(record.value('a15_pfio')))
                table.setText(row, 17, forceString(record.value('a16_pnm')))
                table.setText(row, 18, forceString(record.value('a17_pln')))
                table.setText(row, 19, forceString(record.value('a18_ps')))
                table.setText(row, 20, forceString(record.value('a19_pbd')))
                table.setText(row, 21, forceString(record.value('a20_pph')))
                table.setText(row, 22, forceString(record.value('a21_ps')))
                table.setText(row, 23, forceString(record.value('a22_pn')))
                table.setText(row, 24, forceString(record.value('a23_dt')))
                table.setText(row, 25, forceString(record.value('a24_sl')))
                table.setText(row, 26, forceString(record.value('a25_enp')))
            
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        firstTitle = u'Метод "sendOrdersLeave" - передача сведений о выбывших пациентах в ЦОД'
        cursor.insertBlock()

        #рисуем вторую табличку
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(firstTitle)
        cursor.insertBlock()
        cursor.insertBlock()
        tableColumns = [
            ('5%', [u'номер направления'], CReportBase.AlignLeft),
            ('4%', [u'дата направления'], CReportBase.AlignLeft),
            ('3%', [u'форма оказания медицинской помощи'], CReportBase.AlignCenter),
            ('3%', [u'код МО'], CReportBase.AlignLeft),
            ('4%', [u'дата госпитализации'], CReportBase.AlignLeft),
            ('4%', [u'дата выбытия'], CReportBase.AlignLeft),
            ('3%', [u'код профиля койки'], CReportBase.AlignCenter),
            ('2%', [u'код отделения'], CReportBase.AlignCenter),
            ('4%', [u'номер карты стационарного больного'], CReportBase.AlignCenter),
            ('7%', [u'тип документа, подтверждающего факт страхования по обязательному медицинскому страхованию'], CReportBase.AlignCenter),
            ('3%', [u'серия полиса'], CReportBase.AlignLeft),
            ('6%', [u'номер полиса'], CReportBase.AlignLeft),
            ('2%', [u'код СМО'], CReportBase.AlignCenter),
            ('4%', [u'код территории страхования'], CReportBase.AlignLeft),
            ('4%', [u'фамилия пациента'], CReportBase.AlignLeft),
            ('4%', [u'имя пациента'], CReportBase.AlignLeft),
            ('5%', [u'отчество пациента'], CReportBase.AlignLeft),
            ('2%', [u'пол'], CReportBase.AlignCenter),
            ('4%', [u'дата рождения'], CReportBase.AlignLeft),
            ('7%', [u'контактная информация'], CReportBase.AlignLeft),
            ('4%', [u'серия документа удостоверяющего личность'], CReportBase.AlignLeft),
            ('4%', [u'номер документа удостоверяющего личность'], CReportBase.AlignLeft),
            ('4%', [u'тип документа удостоверяющего личность'], CReportBase.AlignCenter),
            ('4%', [u'СНИЛС гражданина'], CReportBase.AlignLeft),
            ('4%', [u'ЕНП гражданина'], CReportBase.AlignLeft)
            ]
            
            
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 1, 1)

        rowNumber = 0
        for query in [getQuery3(False), getQuery3(True)]:
            while query.next():
                record = query.record()
                row = table.addRow()
                rowNumber += 1
    
                table.setText(row, 0, forceString(record.value('m11_ornm')))
                table.setText(row, 1, forceString(record.value('m12_ordt')))
                table.setText(row, 2, forceString(record.value('m13_ortp')))
                table.setText(row, 3, forceString(record.value('m14_modcd')))
                table.setText(row, 4, forceString(record.value('m15_dttmfh')))
                table.setText(row, 5, forceString(record.value('m16_dttmlv')))
                table.setText(row, 6, forceString(record.value('m18_kpkcd')))
                table.setText(row, 7, forceString(record.value('m19_sccd')))
                table.setText(row, 8, forceString(record.value('m20_crdnum')))
                table.setText(row, 9, forceString(record.value('a10_dct')))
                table.setText(row, 10, forceString(record.value('a11_dcs')))
                table.setText(row, 11, forceString(record.value('a12_dcn')))
                table.setText(row, 12, forceString(record.value('a13_smcd')))
                table.setText(row, 13, forceString(record.value('a14_trcd')))
                table.setText(row, 14, forceString(record.value('a15_pfio')))
                table.setText(row, 15, forceString(record.value('a16_pnm')))
                table.setText(row, 16, forceString(record.value('a17_pln')))
                table.setText(row, 17, forceString(record.value('a18_ps')))
                table.setText(row, 18, forceString(record.value('a19_pbd')))
                table.setText(row, 19, forceString(record.value('a20_pph')))
                table.setText(row, 20, forceString(record.value('a21_ps')))
                table.setText(row, 21, forceString(record.value('a22_pn')))
                table.setText(row, 22, forceString(record.value('a23_dt')))
                table.setText(row, 23, forceString(record.value('a24_sl')))
                table.setText(row, 24, forceString(record.value('a25_enp')))
            
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        firstTitle = u'Метод "sendOrdersHospitalUrgently" - передача сведений об экстренных госпитализациях в ЦОД'
        cursor.insertBlock()

        #рисуем вторую табличку
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(firstTitle)
        cursor.insertBlock()
        cursor.insertBlock()
        tableColumns = [
            ('3%', [u'код МО'], CReportBase.AlignLeft),
            ('4%', [u'дата и время фактической госпитализации'], CReportBase.AlignLeft),
            ('3%', [u'код профиля койки'], CReportBase.AlignCenter),
            ('2%', [u'код отделения'], CReportBase.AlignCenter),
            ('4%', [u'номер карты стационарного больного'], CReportBase.AlignCenter),
            ('5%', [u'код МКБ приемного отделения'], CReportBase.AlignCenter),
            ('5%', [u'тип документа, подтверждающего факт страхования по обязательному медицинскому страхованию'], CReportBase.AlignCenter),
            ('3%', [u'серия полиса'], CReportBase.AlignLeft),
            ('6%', [u'номер полиса'], CReportBase.AlignLeft),
            ('2%', [u'код СМО'], CReportBase.AlignCenter),
            ('4%', [u'код территории страхования'], CReportBase.AlignLeft),
            ('4%', [u'фамилия пациента'], CReportBase.AlignLeft),
            ('4%', [u'имя пациента'], CReportBase.AlignLeft),
            ('5%', [u'отчество пациента'], CReportBase.AlignLeft),
            ('2%', [u'пол'], CReportBase.AlignCenter),
            ('4%', [u'дата рождения'], CReportBase.AlignLeft),
            ('5%', [u'контактная информация'], CReportBase.AlignLeft),
            ('4%', [u'серия документа удостоверяющего личность'], CReportBase.AlignLeft),
            ('4%', [u'номер документа удостоверяющего личность'], CReportBase.AlignLeft),
            ('4%', [u'тип документа удостоверяющего личность'], CReportBase.AlignCenter),
            ('3%', [u'СНИЛС гражданина'], CReportBase.AlignLeft),
            ('3%', [u'ЕНП гражданина'], CReportBase.AlignLeft)
            ]
            
            
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 1, 1)

        rowNumber = 0
        for query in [getQuery4(False), getQuery4(True)]:
            while query.next():
                record = query.record()
                row = table.addRow()
                rowNumber += 1
    
                table.setText(row, 0, forceString(record.value('m11_modcd')))
                table.setText(row, 1, forceString(record.value('m12_dttmfh')))
                table.setText(row, 2, forceString(record.value('m14_kpkcd')))
                table.setText(row, 3, forceString(record.value('m15_sccd')))
                table.setText(row, 4, forceString(record.value('m16_crdnum')))
                table.setText(row, 5, forceString(record.value('m17_mkbcd')))
                table.setText(row, 6, forceString(record.value('a10_dct')))
                table.setText(row, 7, forceString(record.value('a11_dcs')))
                table.setText(row, 8, forceString(record.value('a12_dcn')))
                table.setText(row, 9, forceString(record.value('a13_smcd')))
                table.setText(row, 10, forceString(record.value('a14_trcd')))
                table.setText(row, 11, forceString(record.value('a15_pfio')))
                table.setText(row, 12, forceString(record.value('a16_pnm')))
                table.setText(row, 13, forceString(record.value('a17_pln')))
                table.setText(row, 14, forceString(record.value('a18_ps')))
                table.setText(row, 15, forceString(record.value('a19_pbd')))
                table.setText(row, 16, forceString(record.value('a20_pph')))
                table.setText(row, 17, forceString(record.value('a21_ps')))
                table.setText(row, 18, forceString(record.value('a22_pn')))
                table.setText(row, 19, forceString(record.value('a23_dt')))
                table.setText(row, 20, forceString(record.value('a24_sl')))
                table.setText(row, 21, forceString(record.value('a25_enp')))
        return doc
