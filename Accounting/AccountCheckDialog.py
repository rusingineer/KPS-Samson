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
from PyQt4.QtCore import QDate, Qt, SIGNAL, pyqtSlot, pyqtSignature, QTimer
from PyQt4.QtGui import QSortFilterProxyModel

from Accounting.Utils import updateAccount, clearPayStatus
from Events.EditDispatcher import getEventFormClass
from Exchange.ExportR23Native import getFLCQuery
from library.DialogBase import CDialogBase
from library.InDocTable import CRecordListModel, CInDocTableCol
from library.MemTableModel import CMemTableModel
from library.SortFilterProxyTableModel import CSortFilterProxyTableModel
from library.TableModel import CBoolCol, CTextCol, CDateCol
from library.Utils import forceString, forceRef, agreeNumberAndWord, forceInt, forceBool
from Orgs.Utils import getOrgStructureDescendants
from Registry.ClientEditDialog import CClientEditDialog
from Reports.ReportAccountCheck import CReportAccountCheck
from Surveillance.SurveillanceDialog import CSurveillanceDialog, isSurveillanceActive
from Users.Rights import (urAdmin,
                          urAccessAccountInfo,
                          urAccessAccounting,
                          urAccessAccountingBudget,
                          urAccessAccountingCMI,
                          urAccessAccountingVMI,
                          urAccessAccountingCash,
                          urAccessAccountingTargeted,
                          )

from Ui_AccountCheckDialog import Ui_AccountCheckDialog

accountantRightList = (urAdmin,
                       urAccessAccountInfo,
                       urAccessAccounting,
                       urAccessAccountingBudget,
                       urAccessAccountingCMI,
                       urAccessAccountingVMI,
                       urAccessAccountingCash,
                       urAccessAccountingTargeted
                       )


class CAccountCheckModel(CMemTableModel):
    def __init__(self, parent):
        checkCol = CBoolCol(u'Проверить', ['doCheck'], 15)
        checkCol.checkable = True
        CMemTableModel.__init__(self, parent, [
            checkCol,
            CTextCol(u'Номер', ['number'], 20),
            CDateCol(u'Дата', ['date'], 20)
        ], ['id'])


class CAccountItemsCheckModel(CMemTableModel):

    class CErrorsCol(CTextCol):
        def format(self, values):
            errorCodes = forceString(values[0]).split()
            errorDescriptions = [CAccountCheckDialog.CheckTypes[(code, 0)][0] if (code, 0) in CAccountCheckDialog.CheckTypes else CAccountCheckDialog.CheckTypes[(code, 1)][0] for code in errorCodes]
            return "; ".join(errorDescriptions) if len(errorDescriptions) > 0 else u'нет'

    def __init__(self, parent):
        CMemTableModel.__init__(self, parent, [
            CTextCol(u'№ п.счета', ['event_id'], 12),
            CTextCol(u'Код пациента', ['client_id'], 12),
            CTextCol(u'Ф.И.О.', ['clientName'], 30),
            CDateCol(u'Дата рож.', ['birthDate'], 11),
            CTextCol(u'МКБ', ['mkb'], 7),
            CTextCol(u'Тип обращения', ['eventType_title'], 50),
            CDateCol(u'Дата нач.', ['setDate'], 11),
            CDateCol(u'Дата окон.', ['execDate'], 11),
            CTextCol(u'Результат осмотра', ['diagRes'], 5),
            CTextCol(u'Результат обращения', ['eventRes'], 5),
            self.CErrorsCol(u'Ошибки', ['errorList'], 80),
            CTextCol(u'ОГРН', ['ogrn'], 15),
            CTextCol(u'Плательщик', ['payer_title'], 80),
            CTextCol(u'Ответственный', ['personName'], 30)
        ], ['event_id', 'client_id'])
        self.client_id = self.makeIndex('client_id')
        self.event_id = self.makeIndex('event_id')


class CAccountCheckDialog(CDialogBase, Ui_AccountCheckDialog):
    CheckTypes = {
        ('181', 0):
            (u'181 - поле "ОГРН плательщика" не заполнено',
             u"Payer.OGRN is null or char_length(Payer.OGRN) <> 13"),
        ('201', 0):
            (u'201 - не заполнено поле "Фамилия"',
             u"IFNULL(Client.lastName, '') = ''"),
        ('202', 0):
            (u'202 - не заполнено поле "Имя"',
             u"IFNULL(Client.firstName, '') = ''"),
        ('204', 0):
            (u'204 - не заполнено поле "Пол"',
             u"Client.sex is null"),
        ('205', 0):
            (u'205 - некорректно заполнено поле "Пол"',
             u"Client.sex not in (1, 2)"),
        ('206', 0):
            (u'206 - не заполнено поле "Дата рождения"',
             u"DATE(Client.birthDate) is null"),
        ('210', 0):
            (u'210 - услуга "Обращение" добавлена некорректно',
             u"CheckObr210(Event.id)"),
        ('219', 0):
            (u'219 - поле "Исход лечения" не заполнено',
             u"IFNULL(DiagnosticResult.regionalCode, '') = ''"),
        ('220', 0):
            (u'220 - поле "Исход лечения" не соответствует справочнику или условию оказания МП',
             u"IFNULL(DiagnosticResult.regionalCode, '') <> '' and s11.code is null"),
        ('221', 0):
            (u'221 - поле "Исход обращения" не заполнено',
             "IFNULL(EventResult.regionalCode, '') = ''"),
        ('222', 0):
            (u'222 - поле "Исход обращения" не соответствует справочнику или условию оказания',
             u"IFNULL(EventResult.regionalCode, '') <> '' and s12.code is null"),
        ('225', 1):
            (u'225 - поле "Код отделения" не заполнено',
            u"""exists(select ai.id
            from Account_Item ai
            left join Event e on e.id = ai.event_id
            left join Action a on a.id = ai.action_id
            left join Visit v on v.id = ai.visit_id
            left join Person p on p.id = COALESCE(v.person_id, a.person_id, e.execPerson_id)
            left join OrgStructure o on o.id = p.orgStructure_id
            where ai.deleted = 0 and ai.event_id = Event.id and ai.master_id in ({master_id})
            and (trim(o.infisCode) = '' or o.infisCode is null))
            """
             ),
        ('225', 2):
            (u'225 - поле "Код отделения" не заполнено',
            u"""exists(select ct.id from Event e
            left join Action a on a.event_id = e.id
            left join ActionType at on at.id = a.actionType_id
            left join rbService s on s.id = at.nomenclativeService_id
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id) and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(a.endDate) between ct.begDate and ct.endDate
                or DATE(a.endDate) >= ct.begDate and ct.endDate is null) and ct.tariffType in (2,5)
            left join Person p on p.id = COALESCE(a.person_id, e.execPerson_id)
            left join OrgStructure o on o.id = p.orgStructure_id
            where e.id = Event.id and a.deleted = 0 and s.id is not null
                and ct.price is not null and (trim(o.infisCode) = '' or o.infisCode is null)
            union all
            select ct.id from Event e
            left join Visit v on v.event_id = e.id
            left join rbService s on s.id = v.service_id
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id) and ct.tariffType = 0
                and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(v.date) between ct.begDate and ct.endDate
                or DATE(v.date) >= ct.begDate and ct.endDate is null)
            left join Person p on p.id = COALESCE(v.person_id, e.execPerson_id)
            left join OrgStructure o on o.id = p.orgStructure_id
            where e.id = Event.id and v.deleted = 0 and s.id is not null
                and ct.price is not null and (trim(o.infisCode) = '' or o.infisCode is null)
            union all
            select ct.id from Event e
            left join mes.MES on MES.id = e.MES_id
            left join rbService s on s.infis = MES.code
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id)
                and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(e.execDate) between ct.begDate and ct.endDate
                or DATE(e.execDate) >= ct.begDate and ct.endDate is null)
                and ct.tariffType = 13
            left join Person p on p.id = e.execPerson_id
            left join OrgStructure o on o.id = p.orgStructure_id
            where e.id = Event.id and e.MES_id is not null and substr(MES.code, 1, 1) = 'G' and ct.price is not null
            and (trim(o.infisCode) = '' or o.infisCode is null))
            """
             ),
        ('227', 0):
            (u'227 - поле "Условия оказания медицинской помощи" не заполнено',
             u"IFNULL(rbMedicalAidType.regionalCode, '') = ''"),
        ('229', 0):
            (u'229 - поле "Профиль койки" не заполнено',
            u"""exists (select HospitalAction.id
                    from Action AS HospitalAction
                    left join ActionPropertyType on ActionPropertyType.name = 'койка'
                        and ActionPropertyType.actionType_id = HospitalAction.actionType_id
                        and ActionPropertyType.deleted = 0
                    left join ActionProperty on ActionProperty.type_id = ActionPropertyType.id
                        and ActionProperty.action_id = HospitalAction.id
                        and ActionProperty.deleted = 0
                    left join ActionProperty_HospitalBed on ActionProperty_HospitalBed.id = ActionProperty.id
                    left join OrgStructure_HospitalBed on OrgStructure_HospitalBed.id=ActionProperty_HospitalBed.value
                    left join rbHospitalBedProfile on rbHospitalBedProfile.id = OrgStructure_HospitalBed.profile_id
                    where HospitalAction.id = (
                        SELECT MAX(A.id)
                        FROM Action A
                        WHERE A.event_id = Event.id AND
                                  A.deleted = 0 AND
                                  A.actionType_id IN (
                                        SELECT AT.id
                                        FROM ActionType AT
                                        WHERE AT.flatCode ='moving'
                                            AND AT.deleted = 0
                                  )
                    ) and HospitalAction.id is not null and IFNULL(rbHospitalBedProfile.regionalCode, '') = '')
            """
             ),
        ('232', 0):
            (u'232 - поле "Диагноз основного заболевания" не заполнено',
             u"IFNULL(Diagnosis.MKB, '') = ''"),
        ('241', 1):
            (u'241 - нет услуги, у которой "Дата окончания" совпадала бы с "Датой окончания лечения"',
            u"""not exists(select ai.id from Account_Item ai
            left join Event e on e.id = ai.event_id
            left join Action a on a.id = ai.action_id
            left join Visit v on v.id = ai.visit_id
            LEFT JOIN rbService s ON s.id = ai.service_id
            where ai.deleted = 0 and ai.event_id = Event.id and ai.master_id in ({master_id})
            and (TO_DAYS(a.endDate) = TO_DAYS(e.execDate)
                or TO_DAYS(v.date) = TO_DAYS(e.execDate)
                or (e.MES_id is not null and substr(s.infis, 1, 1) = 'G')))
            """
             ),
        ('241', 2):
            (u'241 - нет услуги, у которой "Дата окончания" совпадала бы с "Датой окончания лечения"',
            u"""not exists(select ct.id from Event e
            left join Action a on a.event_id = e.id
            left join ActionType at on at.id = a.actionType_id
            left join rbService s on s.id = at.nomenclativeService_id
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id) and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(a.endDate) between ct.begDate and ct.endDate
                or DATE(a.endDate) >= ct.begDate and ct.endDate is null) and ct.tariffType in (2,5)
            where e.id = Event.id and a.deleted = 0 and s.id is not null
                and ct.price is not null and TO_DAYS(a.endDate) = TO_DAYS(e.execDate)
            union all
            select ct.id from Event e
            left join Visit v on v.event_id = e.id
            left join rbService s on s.id = v.service_id
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id) and ct.tariffType = 0
                and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(v.date) between ct.begDate and ct.endDate
                or DATE(v.date) >= ct.begDate and ct.endDate is null)
            where e.id = Event.id and v.deleted = 0 and s.id is not null
                and ct.price is not null and TO_DAYS(v.date) = TO_DAYS(e.execDate)
            union all
            select ct.id from Event e
            left join mes.MES on MES.id = e.MES_id
            left join rbService s on s.infis = MES.code
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id)
                and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(e.execDate) between ct.begDate and ct.endDate
                or DATE(e.execDate) >= ct.begDate and ct.endDate is null)
                and ct.tariffType = 13 AND (ct.eventType_id = e.eventType_id or ct.eventType_id is null)
            where e.id = Event.id and e.MES_id is not null and substr(MES.code, 1, 1) = 'G' and ct.price is not null)
            """
             ),
        ('242', 1):
            (u'242 - нет услуги, у которой "Дата начала" совпадала бы с "Датой начала лечения"',
            u"""not exists(select ai.id from Account_Item ai
            left join Event e on e.id = ai.event_id
            left join Action a on a.id = ai.action_id
            left join Visit v on v.id = ai.visit_id
            LEFT JOIN rbService s ON s.id = ai.service_id
            where ai.deleted = 0 and ai.event_id = Event.id and ai.master_id in ({master_id})
            and (IF (s.infis IN ( 
                                  'B04.012.001.010', 'B04.012.001.011', 'B04.012.001.012', 'B04.008.007', 
                                  'B04.015.001', 'B04.008.008', 'B04.023.006', 'B04.037.003', 'B04.023.005', 
                                  'B04.040.001', 'B04.037.004', 'B04.023.003', 'B04.015.002', 'B04.023.004',
                                  'B04.004.003', 'B04.025.003', 'B04.015.006', 'B05.069.008', 'B04.057.003',
                                  'B04.025.004', 'B04.025.001', 'B04.058.001.001', 'B04.058.001.01',
                                  'B04.058.001', 'B04.058.010', 'B04.070.007', 'B04.023.004.010', 'B04.023.005.010', 
                                  'B04.058.001.010'
                                ) OR substr(s.infis, 1, 1) = 'V', TO_DAYS(a.begDate), TO_DAYS(a.endDate)) = TO_DAYS(e.setDate)
                or TO_DAYS(v.date) = TO_DAYS(e.setDate)
                or (e.MES_id is not null and substr(s.infis, 1, 1) = 'G')))
            """
             ),
        ('242', 2):
            (u'242 - нет услуги, у которой "Дата начала" совпадала бы с "Датой начала лечения"',
            u"""not exists(select ct.id from Event e
            left join Action a on a.event_id = e.id
            left join ActionType at on at.id = a.actionType_id
            left join rbService s on s.id = at.nomenclativeService_id
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id) and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(a.endDate) between ct.begDate and ct.endDate
                or DATE(a.endDate) >= ct.begDate and ct.endDate is null) and ct.tariffType in (2,5)
            where e.id = Event.id and a.deleted = 0 and s.id is not null
                and ct.price is not null 
                and IF (s.infis IN ( 
                                     'B04.012.001.010', 'B04.012.001.011', 'B04.012.001.012', 'B04.008.007', 
                                     'B04.015.001', 'B04.008.008', 'B04.023.006', 'B04.037.003', 'B04.023.005', 
                                     'B04.040.001', 'B04.037.004', 'B04.023.003', 'B04.015.002', 'B04.023.004',
                                     'B04.004.003', 'B04.025.003', 'B04.015.006', 'B05.069.008', 'B04.057.003',
                                     'B04.025.004', 'B04.025.001', 'B04.058.001.001', 'B04.058.001.01',
                                     'B04.058.001', 'B04.058.010', 'B04.070.007', 'B04.023.004.010', 'B04.023.005.010', 
                                     'B04.058.001.010'
                                   ) OR substr(s.infis, 1, 1) = 'V', TO_DAYS(a.begDate), TO_DAYS(a.endDate)) = TO_DAYS(e.setDate)
            union all
            select ct.id from Event e
            left join Visit v on v.event_id = e.id
            left join rbService s on s.id = v.service_id
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id) and ct.tariffType = 0
                and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(v.date) between ct.begDate and ct.endDate
                or DATE(v.date) >= ct.begDate and ct.endDate is null)
            where e.id = Event.id and v.deleted = 0 and s.id is not null
               and ct.price is not null and TO_DAYS(v.date) = TO_DAYS(e.setDate)
            union all
            select ct.id from Event e
            left join mes.MES on MES.id = e.MES_id
            left join rbService s on s.infis = MES.code
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id)
                and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(e.execDate) between ct.begDate and ct.endDate
                or DATE(e.execDate) >= ct.begDate and ct.endDate is null)
                and ct.tariffType = 13 AND (ct.eventType_id = e.eventType_id or ct.eventType_id is null)
            where e.id = Event.id and e.MES_id is not null and substr(MES.code, 1, 1) = 'G' and ct.price is not null)
            """
             ),
        ('243', 1):
            (u'243 - поле "Количество услуг" заполнено не корректно',
            u"""exists(select ai.id from Account_Item ai
            left join Event e on e.id = ai.event_id
            left join rbService s on s.id = ai.service_id
            left join Contract_Tariff ct on ct.id = ai.tariff_id
            where ai.deleted = 0 and ai.event_id = Event.id and ai.master_id in ({master_id})
            and (ai.amount < 1 or ai.amount > 999 or (isPos(s.infis, rbMedicalAidType.regionalCode, ct.price) = 1 and ai.amount > 1)))
            """
             ),
        ('243', 2):
            (u'243 - поле "Количество услуг" заполнено не корректно',
            u"""exists(select ct.id from Event e
            left join Action a on a.event_id = e.id
            left join ActionType at on at.id = a.actionType_id
            left join rbService s on s.id = at.nomenclativeService_id
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id) and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(a.endDate) between ct.begDate and ct.endDate
                or DATE(a.endDate) >= ct.begDate and ct.endDate is null) and ct.tariffType in (2,5)
            where e.id = Event.id and a.deleted = 0 and s.id is not null and ct.price is not null
            AND EXISTS(SELECT NULL FROM ActionType_Service ats WHERE ats.master_id = a.actionType_id AND ats.service_id is not null 
                and (ats.finance_id = c.finance_id or ats.finance_id is null)
            )
            and (a.amount < 1 or a.amount > 999 or (isPos(s.infis, rbMedicalAidType.regionalCode, ct.price) = 1 and a.amount > 1)))
            """
             ),
        ('247', 0):
            (u'247 - поле "Серия документа ОМС" не заполнено',
             u"rbPolicyKind.regionalCode = '1' and IFNULL(ClientPolicy.serial, '') = ''"),
        ('248', 0):
            (u'248 - поле "Номер документа ОМС" не заполнено',
             u"ClientPolicy.id is not null and IFNULL(ClientPolicy.number, '') = ''"),
        ('263', 0):
            (u'263 - поле "Код направившей медицинской организации (заказчика) в системе ОМС" не заполнено',
            u"""(rbMedicalAidType.regionalCode in ('11', '12', '301', '302', '401', '402', '41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522')
                    or rbMedicalAidType.regionalCode in ('211', '233', '244') and rbEventProfile.regionalCode in ('8009', '8015', '8019', '8021')
                    or eti.id is not null)
               and rbFinance.code = '2' and Event.`order` = 1 and ifnull(RelegateOrg.smoCode, '') = ''"""
             ),
        ('264', 0):
            (u'264 -  поле "Номер направления" не заполнено или содержит недопустимый символ',
            u"""(rbMedicalAidType.regionalCode in ('11', '12', '301', '302', '401', '402', '41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522')
                    or rbMedicalAidType.regionalCode in ('211', '233', '244') and rbEventProfile.regionalCode in ('8009', '8015', '8019', '8021')
                    or eti.id is not null)
               and rbFinance.code = '2' and Event.`order` = 1 and length(ifnull(Event.srcNumber, '')) = 0"""
             ),
        ('265', 0):
            (u'265 -  поле "Дата направления" не заполнено',
            u"""(rbMedicalAidType.regionalCode in ('11', '12', '301', '302', '401', '402', '41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522')
                    or rbMedicalAidType.regionalCode in ('211', '233', '244') and rbEventProfile.regionalCode in ('8009', '8015', '8019', '8021')
                    or eti.id is not null)
               and rbFinance.code = '2' and Event.`order` = 1 and Event.srcDate is null"""
             ),
        ('290', 1):
            (u'290 - сумма к оплате по случаю заболевания равна 0',
             u"""(select sum(sm.sum) from Account_Item sm where sm.master_id in ({master_id})
                 and sm.event_id = Event.id and sm.deleted = 0) = 0 
                 and not (Event.execDate >= '2017-01-01' and rbMedicalAidType.regionalCode in ('271', '272') 
                             and Contract.payer_id not in (select Account.payer_id from Account where Account.id in ({master_id})))
             """
             ),
        ('305', 0):
            (u'305 - услуга с указанным диагнозом или профилем койки не подлежит оплате в системе ОМС',
             u"s20.code is null and s20group.code is null"),
        ('307', 0):
            (u"307 - посещение по заболеванию сформировано как разовое посещение",
            u"""exists(select a1.id
                from Event e1
                left join Action a1 on a1.event_id = e1.id and a1.deleted = 0
                left join ActionType at1 on at1.id = a1.actionType_id
                left join rbService s1 on s1.id = at1.nomenclativeService_id
                LEFT join Organisation o1 ON e1.org_id = o1.id
                left join Contract c1 on c1.id = IFNULL(a1.contract_id, e1.contract_id) and c1.deleted = 0
                left join Contract_Tariff ct1 ON ct1.master_id = IFNULL(c1.priceList_id, c1.id)
                    and ct1.service_id = s1.id and ct1.deleted = 0
                    and (ct1.endDate is not null and DATE(a1.endDate) between ct1.begDate and ct1.endDate
                    or DATE(a1.endDate) >= ct1.begDate and ct1.endDate is null)
                    and ct1.tariffType in (2,5)
                left join Event e2 on e2.client_id = e1.client_id and e2.deleted = 0
                left join EventType et2 on et2.id = e2.eventType_id
                left join Diagnosis d2 on d2.id = getEventDiagnosis(e2.id)
                left join rbMedicalAidType mt2 ON et2.medicalAidType_id = mt2.id
                left join Action a2 on a2.event_id = e2.id and a2.deleted = 0
                left join ActionType at2 on at2.id = a2.actionType_id
                left join rbService s2 on s2.id = at2.nomenclativeService_id
                LEFT join Organisation o2 ON e2.org_id = o2.id
                left join Contract c2 on c2.id = IFNULL(a2.contract_id, e2.contract_id) and c2.deleted = 0
                left JOIN rbFinance f2 ON f2.id = c2.finance_id
                left join Contract_Tariff ct2 ON ct2.master_id = IFNULL(c2.priceList_id, c2.id)
                    and ct2.service_id = s2.id and ct2.deleted = 0
                    and (ct2.endDate is not null and DATE(a2.endDate) between ct2.begDate and ct2.endDate
                    or DATE(a2.endDate) >= ct2.begDate and ct2.endDate is null)
                    and ct2.tariffType in (2,5)
                left JOIN soc_OBRPOS so1 ON so1.posCode = s1.infis AND so1.begDate <= a1.endDate AND so1.endDate >= a1.endDate
                left JOIN soc_OBRPOS so2 ON so2.posCode = s2.infis AND so2.begDate <= a2.endDate AND so2.endDate >= a2.endDate
                where e1.id = Event.id and e2.id <> Event.id and e1.client_id = e2.client_id and e1.deleted = 0
                    AND f2.code = '2'
                    and rbMedicalAidType.regionalCode IN ('21', '22', '31', '32', '60', '201', '202', '271', '272')
                    and mt2.regionalCode = rbMedicalAidType.regionalCode
                    and d2.mkb = Diagnosis.mkb 
                    AND so1.obrCode = so2.obrCode
                    AND ct1.id IS NOT NULL AND ct2.id is NOT NULL
                    and month(e2.execDate) = month(e1.execDate) and year(e2.execDate) = year(e1.execDate)
                    AND o1.infisCode = o2.infisCode)
            """
             ),
        ('322', 0):
            (u'322 - в счете отсутствует услуга "Обращение"',
             u"rbMedicalAidType.regionalCode IN ('21', '22', '31', '32', '60', '201', '202', '271', '272') and CheckObr(Event.id)"),
        # ('328', 0):
        #     (u'328 - повторная госпитализация пациента в срок менее 30 дней по одному и тому же диагнозу',
        #     u"""rbMedicalAidType.regionalCode in ('11', '12', '301', '302') and exists(select e2.id from Event e2
        #     LEFT JOIN EventType et2 on et2.id = e2.eventType_id
        #     left join Person p2 on p2.id = e2.execPerson_id
        #     left join Diagnosis d2 on d2.id = getEventDiagnosis(e2.id)
        #     LEFT JOIN rbMedicalAidType mt2 ON et2.medicalAidType_id = mt2.id
        #     where e2.deleted = 0 and mt2.regionalCode = rbMedicalAidType.regionalCode
        #     and e2.client_id = Event.client_id and e2.id <> Event.id
        #     and d2.mkb = Diagnosis.mkb and abs(datediff(e2.execDate, Event.setDate)) < 30)
        #     """
        #      ),
        ('346', 1):
            (u'346 - дублирование счета по услуге стационар и поликлиника в один день по одному пациенту',
            u""" rbMedicalAidType.regionalCode in ('01', '02', '111', '112', '21', '22', '211', '222', '201', '202',
                '241', '232', '233', '252', '242', '262', '261', '32', '31', '60', '80', '271', '272')
                and
                exists(select ai2.id
                from Account_Item ai
                left join Event e1 on e1.id = ai.event_id
                left join rbService s on s.id = ai.service_id
                left join Event e2 on e2.deleted = 0 and e2.client_id = e1.client_id and e2.id <> e1.id 
                    and e1.execDate between date_add(e2.setDate, INTERVAL 1 DAY) and date_add(e2.execDate, INTERVAL -1 DAY) 
                left join Account_Item ai2 on ai2.event_id = e2.id and ai2.deleted = 0
                left join EventType et2 on et2.id = e2.eventType_id
                left join rbMedicalAidType mt2 ON et2.medicalAidType_id = mt2.id
                where ai.master_id in ({master_id})
                    and ai.event_id = Event.id
                    and ai.deleted = 0
                    and s.infis REGEXP 'B0[124]'
                    and mt2.regionalCode in ('11', '12', '41', '42', '51', '52', '71', '72', '90', '301', '302', '411', '422', '511', '522')
                    and ai2.id IS NOT null)
            """
             ),
        ('346', 2):
            (u'346 - дублирование счета по услуге стационар и поликлиника в один день по одному пациенту',
            u""" rbMedicalAidType.regionalCode in ('01', '02', '111', '112', '21', '22', '211', '222', '201', '202',
                '241', '232', '233', '252', '242', '262', '261', '32', '31', '60', '80', '271', '272')
                and exists(select a.id
                from Action a
                left join Event e1 on e1.id = a.event_id
                LEFT JOIN Contract c1 ON c1.id=e1.contract_id
                LEFT JOIN rbFinance f1 ON f1.id=c1.finance_id
                left join ActionType at on at.id = a.actionType_id
                left join rbService s on s.id = at.nomenclativeService_id
                left join Event e2 on e2.client_id = e1.client_id and e2.id <> e1.id 
                    and e1.execDate between date_add(e2.setDate, INTERVAL 1 DAY)
                    and date_add(e2.execDate, INTERVAL -1 DAY) and e2.deleted = 0
                left join EventType et2 on et2.id = e2.eventType_id
                left join rbMedicalAidType mt2 ON et2.medicalAidType_id = mt2.id
                LEFT JOIN Contract c2 ON c2.id=e2.contract_id
                LEFT JOIN rbFinance f2 ON f2.id=c2.finance_id
                where a.event_id = Event.id and a.deleted = 0
                and s.infis REGEXP 'B0[124]'
                and mt2.regionalCode in ('11', '12', '41', '42', '51', '52', '71', '72', '90', '301', '302', '411', '422', '511', '522')
                and e2.MES_id is not null
                AND f1.id=f2.id and f2.code = '2')
            """
             ),
        ('347', 1):
            (u'347 - указанный КСГ не соответствует страховому случаю и справочнику SPR69, SPR70',
            u"""rbMedicalAidType.regionalCode in ('11', '12', '41', '42', '43', '51', '52', '71', '72', '90', '301', '302', '411', '422', '511', '522') 
                and exists(select Event.MES_id
                from Account_Item ai
                left join Event e on e.id = ai.event_id
                left join rbService s on s.id = ai.service_id
                left join Diagnostic on Diagnostic.id = getEventDiagnostic(ai.event_id)
                left join Diagnosis on Diagnosis.id = Diagnostic.diagnosis_id and Diagnosis.deleted = 0
                left join soc_spr69 s69 on s69.ksgkusl = s.infis and ((s69.mkb = Diagnosis.MKB or s69.mkb is null or (s69.mkb = 'C.' and substr(Diagnosis.MKB, 1, 1) = 'C') or (s69.mkb = 'C00-C80' and Diagnosis.MKB between 'C00' and 'C80.9')) and (s69.kusl is null 
                    or s69.kusl in (select s2.infis from Account_Item ai2
                                        left join rbService s2 on s2.id = ai2.service_id
                                        where ai2.event_id = ai.event_id and ai2.master_id = ai.master_id and ai2.deleted = 0)))
                    and s69.datn <= DATE(e.execDate) and (s69.dato is null or s69.dato >= DATE(e.execDate))
                left join soc_spr70 s70 on s70.ksgmkb = s69.ksgkusl and s70.datn <= DATE(e.execDate) and (s70.dato is null or s70.dato >= DATE(e.execDate))
                left join soc_spr69 s69_2 on s69_2.ksgkusl = s70.ksgkusl and s69_2.kusl in (SELECT s2.infis from Account_Item ai2
                            left join rbService s2 on s2.id = ai2.service_id
                            where ai2.event_id = ai.event_id and ai2.master_id = ai.master_id)
                    and s69_2.datn <= DATE(e.execDate) and (s69_2.dato is null or s69_2.dato >= DATE(e.execDate))
                where ai.event_id = Event.id and ai.deleted = 0 and substr(s.infis, 1, 1) = 'G' and (s69.ksgkusl is null or s69_2.ksgkusl is not null))
            """
             ),
        ('347', 2):
            (u'347 - указанный КСГ не соответствует страховому случаю и справочнику SPR69, SPR70',
            u"""rbMedicalAidType.regionalCode in ('11', '12', '41', '42', '43', '51', '52', '71', '72', '90', '301', '302', '411', '422', '511', '522') 
                and exists(select e.MES_id
                from Event e
                LEFT JOIN mes.MES m ON m.id = e.MES_id
                left join Diagnostic on Diagnostic.id = getEventDiagnostic(e.id)
                left join Diagnosis on Diagnosis.id = Diagnostic.diagnosis_id and Diagnosis.deleted = 0
                left join soc_spr69 s69 on s69.ksgkusl = m.code and ((s69.mkb = Diagnosis.MKB or s69.mkb is null or (s69.mkb = 'C.' and substr(Diagnosis.MKB, 1, 1) = 'C') or (s69.mkb = 'C00-C80' and Diagnosis.MKB between 'C00' and 'C80.9'))
                    and (s69.kusl is null
                    or s69.kusl in (select s.infis from Action a
                                        left join ActionType at on at.id = a.actionType_id
                                        left join rbService s on s.id = at.nomenclativeService_id
                                        where a.event_id = e.id and a.deleted = 0)))
                     and s69.datn <= DATE(e.execDate) and (s69.dato is null or s69.dato >= DATE(e.execDate))
                left join soc_spr70 s70 on s70.ksgmkb = s69.ksgkusl and s70.datn <= DATE(e.execDate) 
                    and (s70.dato is null or s70.dato >= DATE(e.execDate))
                left join soc_spr69 s69_2 on s69_2.ksgkusl = s70.ksgkusl and s69_2.kusl in (select s2.infis from Action a2
                                        left join ActionType at2 on at2.id = a2.actionType_id
                                        left join rbService s2 on s2.id = at2.nomenclativeService_id
                                        where a2.event_id = e.id and a2.deleted = 0)
                    and s69_2.datn <= DATE(e.execDate) and (s69_2.dato is null or s69_2.dato >= DATE(e.execDate))
                where e.id = Event.id and substr(m.code, 1, 1) = 'G' and (s69.ksgkusl is null or s69_2.ksgkusl is not null))
            """
             ),
        ('349', 1):
            (u'349 - дублирование посещения в один день к врачу одной специальности, внутри реестра',
            u"""exists(select STRAIGHT_JOIN ai2.id
                from Account_Item ai
                left join rbService s on s.id = ai.service_id
                left JOIN Event e1 ON e1.id = ai.event_id
                left join Event e2 on e2.client_id = e1.client_id
                left join EventType et2 on et2.id = e2.eventType_id
                left join rbMedicalAidType mt2 ON et2.medicalAidType_id = mt2.id
                left join Account_Item ai2 on ai2.master_id = ai.master_id and ai.serviceDate = ai2.serviceDate AND ai2.event_id = e2.id
                left join rbService s2 on s2.id = ai2.service_id
                where ai.master_id in ({master_id}) and ai.event_id = Event.id
                    and ai.deleted = 0 and ai2.deleted = 0
                    and e2.id <> e1.id
                    and isPos(s.infis, rbMedicalAidType.regionalCode, ai.price) = 1
                    and substr(s.infis, 1, 7) = substr(s2.infis, 1, 7)
                    and isPos(s2.infis, mt2.regionalCode, ai2.price) = 1)
            """
             ),
        ('350', 1):
            (u'350 - дублирование посещения в один день к врачу одной специальности, в различных реестрах.',
            u"""exists(select STRAIGHT_JOIN ai2.id
                from Account_Item ai
                left join rbService s on s.id = ai.service_id
                left JOIN vVisitServices vs ON vs.id = s.id
                left JOIN Event e1 ON e1.id = ai.event_id
                left join Event e2 on e2.client_id = e1.client_id
                left join Account_Item ai2 on ai.serviceDate = ai2.serviceDate AND e2.id = ai2.event_id
                left join rbService s2 on s2.id = ai2.service_id
                LEFT join vVisitServices vs2 ON vs2.id = s2.id
                where ai.master_id in ({master_id}) and ai.event_id = Event.id and ai.deleted = 0
                    and vs.infis IS NOT NULL
                    and ai2.master_id <> ai.master_id and e2.id <> e1.id and ai2.deleted = 0
                    and substr(s.infis, 5, 3) = substr(s2.infis, 5, 3)
                    and vs2.infis IS NOT NULL
                )
            """
             ), #34216
        ('355', 0):
            (u'355 - дублирование посещения в один день к врачу одной специальности, в персональном счете',
            u"""exists(select COUNT(DISTINCT a2.id), substr(s2.infis, 1, 7), date(a2.endDate)
            from Event e2
            left join EventType et2 on et2.id = e2.eventType_id
            left join Action a2 on a2.event_id = e2.id and a2.deleted = 0
            left join ActionType at2 on at2.id = a2.actionType_id
            left join rbMedicalAidType mt2 ON et2.medicalAidType_id = mt2.id
            left join rbService s2 on s2.id = at2.nomenclativeService_id
            left join Contract c2 on c2.id = IFNULL(a2.contract_id, e2.contract_id)
                and c2.deleted = 0  -- and c2.finance_id = a2.finance_id
            left join Contract_Tariff ct2 ON ct2.master_id = IFNULL(c2.priceList_id, c2.id)
                and ct2.service_id = s2.id and ct2.deleted = 0
                    and (ct2.endDate is not null and DATE(a2.endDate) between ct2.begDate and ct2.endDate
                    or DATE(a2.endDate) >= ct2.begDate and ct2.endDate is null)
                    and ct2.tariffType in (2,5)
            where e2.id = Event.id and isPos(s2.infis, mt2.regionalCode, ct2.price) = 1
            AND substr(s2.name,1,31) <> 'Обращение по поводу заболевания'
            -- исключить из проверки проведение КТ и МРТ по списку услуг
            AND s2.infis not in ('B01.039.011', 'B01.039.012', 'B01.039.013', 'B01.039.014')
            group by substr(s2.infis, 1, 7), date(a2.endDate)
            having count(DISTINCT a2.id) > 1)
            """
             ),
        ('374', 0):
            (u'374 - Для событий с онкодиагнозом отсутствует "Контрольный лист"',
             """(Diagnosis.MKB LIKE 'C%'
                  OR Diagnosis.MKB LIKE 'D0%'
                  OR LEFT(Diagnosis.MKB, 3) IN ('D45', 'D46', 'D47'))
                AND NOT EXISTS(SELECT
                                  NULL
                                  FROM Action A1
                                  WHERE A1.event_id = Event.id
                                  AND DATE(A1.endDate) = DATE(Event.execDate)
                                  AND A1.deleted = 0
                                  AND A1.actionType_id IN (SELECT AT1.id
                                    FROM ActionType AT1
                                    WHERE AT1.flatCode = 'ControlListOnko'
                                    AND AT1.deleted = 0))                
             """),
        # ('359', 0):
        #     (u'359 - предоставьте обоснование для сверхкороткого случая госпитализации',
        #     u"""exists(select m.code
        #     from mes.MES m
        #     where m.id = Event.MES_id and substr(m.code, 1, 1) = 'G'
        #     and WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, rbMedicalAidType.regionalCode) < 3)
        #     """
        #      ),
        ('835', 1):
            (u'835 - для медицинской услуги не указана специальность врача',
            u"""exists(select ai.id from Account_Item ai
                left join rbService s on s.id = ai.service_id
                left join Visit v on v.id  = ai.visit_id
                left join Action a on a.id = ai.action_id
                left join Event e on e.id = ai.event_id
                left join Person p on p.id = coalesce(a.person_id, v.person_id, e.execPerson_id)
                left join rbSpeciality sp on p.speciality_id = sp.id
                where ai.event_id = Event.id and ai.master_id in ({master_id}) and ai.deleted = 0
                    and a.org_id is null and (sp.regionalCode = '' or sp.regionalCode is null))
            """
             ),
        ('835', 2):
            (u'835 - для медицинской услуги не указана специальность врача',
            u"""exists(select ct.id from Event e
            left join Action a on a.event_id = e.id
            left join ActionType at on at.id = a.actionType_id
            LEFT JOIN ActionType_Service ats ON ats.master_id = a.actionType_id
            left join rbService s on s.id = ats.service_id
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id) and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(a.endDate) between ct.begDate and ct.endDate
                or DATE(a.endDate) >= ct.begDate and ct.endDate is null) and ct.tariffType in (2,5)
            left join Person p on p.id = coalesce(a.person_id, e.execPerson_id)
            left join rbSpeciality sp on p.speciality_id = sp.id
            where e.id = Event.id and a.deleted = 0 and s.id is not null
                and ct.price is not null and a.org_id is null and (sp.regionalCode = '' or sp.regionalCode is null)
            union all
            select ct.id from Event e
            left join Visit v on v.event_id = e.id
            left join rbService s on s.id = v.service_id
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id) and ct.tariffType = 0
                and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(v.date) between ct.begDate and ct.endDate
                or DATE(v.date) >= ct.begDate and ct.endDate is null)
            left join Person p on p.id = v.person_id
            left join rbSpeciality sp on p.speciality_id = sp.id
            where e.id = Event.id and v.deleted = 0 and s.id is not null
               and ct.price is not null and (sp.regionalCode = '' or sp.regionalCode is null)
            union all
            select ct.id from Event e
            left join mes.MES on MES.id = e.MES_id
            left join rbService s on s.infis = MES.code
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id)
                and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(e.execDate) between ct.begDate and ct.endDate
                or DATE(e.execDate) >= ct.begDate and ct.endDate is null)
                and ct.tariffType = 13
            left join Person p on p.id = e.execPerson_id
            left join rbSpeciality sp on p.speciality_id = sp.id
            where e.id = Event.id and e.MES_id is not null AND LEFT(MES.code, 1) IN ('V', 'G') and (sp.regionalCode = '' or sp.regionalCode is null))
            """
             ),
        ('846', 0):
            (u'846 - поле "Вид обращения" заполнено некорректно',
            u"""(rbMedicalAidType.regionalCode in ('241', '242', '111', '112') and Event.`order` <> 6) or
            (rbMedicalAidType.regionalCode in ('01', '02', '21', '22', '211', '222', '201', '202', '232',
                '233', '252',  '262', '261', '32', '31', '60', '80', '271', '272',
                '41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522') and Event.`order` = 2)
            """
             ),
        ('850', 1):
            (u'850 - специальность врача не соответствует возрасту (или полу) пациента',
             u"""exists(select ai.id from Account_Item ai
                left join rbService s on s.id = ai.service_id
                left join Visit v on v.id  = ai.visit_id
                left join Action a on a.id = ai.action_id
                left join Event e on e.id = ai.event_id
                left join Person p on p.id = coalesce(a.person_id, v.person_id, e.execPerson_id)
                left join rbSpeciality sp on p.speciality_id = sp.id
                where ai.event_id = Event.id and ai.master_id in ({master_id}) and ai.deleted = 0
                    and isSexAndAgeSuitable(Client.sex, Client.birthDate, sp.sex, sp.age, e.setDate) = 0)
            """),
        ('854', 0):
            (u'854 - поле "Тип документа, подтверждающего факт страхования по ОМС" не заполнено',
             u"ClientPolicy.id is not null and IFNULL(rbPolicyKind.regionalCode, '') = ''"),
        ('866', 1):
            (u'866 - поле "Профиль оказанной МП" не заполнено',
            u"""exists(select ai.id from Account_Item ai
                left join rbService s on s.id = ai.service_id
                left join Visit v on v.id  = ai.visit_id
                left join Action a on a.id = ai.action_id
                left join Event e on e.id = ai.event_id
                left join Person p on p.id = coalesce(a.person_id, v.person_id, e.execPerson_id)
                left join rbSpeciality spec on p.speciality_id = spec.id
                left join rbMedicalAidProfile ssp on ssp.id = spec.medicalAidProfile_id
                where ai.event_id = Event.id and ai.master_id in ({master_id}) and ai.deleted = 0
                    and (ai.sum > 0 or isPos(s.infis, rbMedicalAidType.regionalCode, ai.price) = 1)
                    and ifnull(ssp.regionalCode, '') = '')
            """
             ),
        ('867', 1):
            (u'867 - поле "Профиль оказанной МП" не соответствует справочнику',
            """exists(select ai.id from Account_Item ai
                left join rbService s on s.id = ai.service_id
                left join Visit v on v.id  = ai.visit_id
                left join Action a on a.id = ai.action_id
                left join Event e on e.id = ai.event_id
                left join Person p on p.id = coalesce(a.person_id, v.person_id, e.execPerson_id)
                left join rbService_Profile sp on
                    sp.id = (select max(id) from rbService_Profile rs where rs.master_id = s.id
                    and rs.speciality_id = p.speciality_id)
                left join rbMedicalAidProfile ssp on ssp.id = coalesce(sp.medicalAidProfile_id, s.medicalAidProfile_id)
                left join soc_spr60 s60 on s60.code = ssp.regionalCode and s60.datn <= e.execDate
                    and (s60.dato >= e.execDate or s60.dato is null)
                where ai.event_id = Event.id and ai.master_id in ({master_id}) and ai.deleted = 0
                    and (ai.sum > 0 or isPos(s.infis, rbMedicalAidType.regionalCode, ai.price) = 1)
                    and ifnull(ssp.regionalCode, '') <> '' and s60.code is null)
            """
             ),
        ('903', 0):
            (u'903 - поле "исход обращения" содержит недопустимое значение для диспансеризации, СМП или для исхода лечения',
            u"""scs12.code_ishl is not null and (scs12.code_ishl = 'не ОМС' or INSTR(scs12.code_ishl, DiagnosticResult.regionalCode) = 0)
            """
             ),
        ('911', 1):
            (u'911 - несоответствие профиля оказанной МП и специальности медицинского сотрудника',
            u"""exists(select ai.id from Account_Item ai
                left join rbService s on s.id = ai.service_id
                left join Visit v on v.id  = ai.visit_id
                left join Action a on a.id = ai.action_id and a.org_id is null
                left join Event e on e.id = ai.event_id
                left join Person p on p.id = coalesce(a.person_id, v.person_id, e.execPerson_id)
                left join rbSpeciality spec on p.speciality_id = spec.id
                left join rbMedicalAidProfile ssp on ssp.id = spec.medicalAidProfile_id
                left join soc_checkSpecProf csp on csp.specCode = spec.regionalCode and csp.profilCode = ssp.regionalCode
                where ai.event_id = Event.id and ai.master_id in ({master_id}) and ai.deleted = 0
                and csp.specCode is null)
            """
             ),
        ('911', 2):
            (u'911 - несоответствие профиля оказанной МП и специальности медицинского сотрудника',
            u"""exists(select ct.id from Event e
            left join Action a on a.event_id = e.id
            left join ActionType at on at.id = a.actionType_id
            LEFT JOIN ActionType_Service ats ON ats.master_id = a.actionType_id
            left join rbService s on s.id = ats.service_id
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id) and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(a.endDate) between ct.begDate and ct.endDate
                or DATE(a.endDate) >= ct.begDate and ct.endDate is null) and ct.tariffType in (2,5)
            left join Person p on p.id = coalesce(a.person_id, e.execPerson_id)
            left join rbSpeciality spec on p.speciality_id = spec.id
            left join rbMedicalAidProfile ssp on ssp.id = spec.medicalAidProfile_id
            left join soc_checkSpecProf csp on csp.specCode = spec.regionalCode and csp.profilCode = ssp.regionalCode
            where e.id = Event.id and a.deleted = 0 and a.org_id is null and s.id is not null
                and ct.price is not null and csp.specCode is null
            union all
            select ct.id from Event e
            left join Visit v on v.event_id = e.id
            left join rbService s on s.id = v.service_id
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id) and ct.tariffType = 0
                and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(v.date) between ct.begDate and ct.endDate
                or DATE(v.date) >= ct.begDate and ct.endDate is null)
            left join Person p on p.id = v.person_id
            left join rbSpeciality spec on p.speciality_id = spec.id
            left join rbMedicalAidProfile ssp on ssp.id = spec.medicalAidProfile_id
            left join soc_checkSpecProf csp on csp.specCode = spec.regionalCode and csp.profilCode = ssp.regionalCode
            where e.id = Event.id and v.deleted = 0 and s.id is not null
               and ct.price is not null and csp.specCode is null
            union all
            select ct.id from Event e
            left join mes.MES on MES.id = e.MES_id
            left join rbService s on s.infis = MES.code
            LEFT JOIN Contract c ON c.id = e.contract_id
            left join Contract_Tariff ct on ct.master_id in (c.id, c.priceListExternal_id)
                and ct.service_id = s.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(e.execDate) between ct.begDate and ct.endDate
                or DATE(e.execDate) >= ct.begDate and ct.endDate is null)
                and ct.tariffType = 13
            left join Person p on p.id = e.execPerson_id
            left join rbSpeciality spec on p.speciality_id = spec.id
            left join rbMedicalAidProfile ssp on ssp.id = spec.medicalAidProfile_id
            left join soc_checkSpecProf csp on csp.specCode = spec.regionalCode and csp.profilCode = ssp.regionalCode
            where e.id = Event.id and e.MES_id is not null AND LEFT(MES.code, 1) IN ('V', 'G') and csp.specCode is null)
            """
             ),
        ('930', 0):
            (u'930 - диагноз не соответствует возрасту пациента',
            """((Diagnosis.MKB = 'Z00.1' and age(Client.birthDate, Event.setDate) >= 4)
            or (Diagnosis.MKB = 'Z00.2' and (age(Client.birthDate, Event.setDate) < 4
            or age(Client.birthDate, Event.setDate) >= 12))
            or (Diagnosis.MKB = 'Z00.3' and (age(Client.birthDate, Event.setDate) < 12
            or age(Client.birthDate, Event.setDate) > 18)))
            """
             ),
        ('1000', 0):
            (u'1000 - КОВИД-19. В персональном счете не заполнен файл E или заполнен не корректно для случаев лечения COVID-19',
             """Diagnosis.MKB in ('U07.1', 'U07.2') 
              AND IFNULL(eti.value, '') <> 'av'
              AND
              (EXISTS(SELECT NULL FROM mes.MES m
                        WHERE Event.MES_id = m.id AND m.code like 'G%%' and IF(Event.execDate < '2026-01-01', substr(m.code, 4, 8) not in ('st36.013', 'st36.014', 'st36.015'), substr(m.code, 4, 8) not in ('st36.050', 'st36.051', 'st36.052', 'st36.053', 'st36.054')))
               AND NOT EXISTS(SELECT NULL
                      FROM Action A1
                      WHERE A1.event_id = Event.id
                      AND A1.deleted = 0
                      AND A1.actionType_id IN (SELECT
                          AT1.id
                        FROM ActionType AT1
                        WHERE AT1.flatCode = 'List_covid'
                        AND AT1.deleted = 0))
              
              OR 
              NOT EXISTS(SELECT NULL FROM mes.MES m
                        WHERE Event.MES_id = m.id AND (m.code like 'G%%' or IF(Event.execDate < '2026-01-01', substr(m.code, 4, 8) in ('st36.013', 'st36.014', 'st36.015'), substr(m.code, 4, 8) in ('st36.050', 'st36.051', 'st36.052', 'st36.053', 'st36.054'))))
               AND NOT EXISTS (SELECT NULL FROM Action a
                                LEFT JOIN ActionType at on at.id = a.actionType_id
                                LEFT JOIN rbService s on s.id = at.nomenclativeService_id
                                WHERE a.event_id = Event.id and a.deleted = 0 and s.infis like 'B%%'
                                AND EXISTS (SELECT NULL
                                              FROM Action A1
                                              WHERE A1.event_id = Event.id
                                              AND A1.deleted = 0
                                              AND DATE(A1.endDate) = DATE(a.endDate)
                                              AND A1.actionType_id IN (SELECT
                                                  AT1.id
                                                FROM ActionType AT1
                                                WHERE AT1.flatCode = 'List_covid'
                                                AND AT1.deleted = 0)))
              )
             """
             ),
        ('1002', 0):
            (u'1002 - ПРОФ. Значение поля DATE_PO не заполнено или заполнено не корректно',
             u"""CASE WHEN Event.execDate >= '2023-01-10' AND rbMedicalAidType.regionalCode in ('211', '232', '252', '262', '261') THEN
                            NOT EXISTS (SELECT css.begDate FROM ClientSocStatus css
                                    left JOIN rbSocStatusType sst on sst.id = css.socStatusType_id
                                    left JOIN rbSocStatusClass ssc ON ssc.id = css.socStatusClass_id
                                    WHERE css.client_id = Client.id AND css.deleted = 0 AND ssc.code = 'profilac'
                                          AND css.begDate > Event.execDate  ORDER BY css.begDate DESC LIMIT 1)
                     WHEN Event.execDate >= '2023-01-10' AND EXISTS(SELECT NULL FROM Action a
                                                        LEFT JOIN ActionType at on at.id = a.actionType_id 
                                                        LEFT JOIN rbService rs1 ON rs1.id = at.nomenclativeService_id
                                                        INNER JOIN soc_spr97 s97 ON s97.kusl = rs1.infis AND s97.datn <= a.endDate AND (s97.dato is NULL OR s97.dato >= a.endDate)
                                                        WHERE a.event_id = Event.id AND a.deleted = 0) THEN
                    NOT EXISTS (SELECT pp.begDate
                     FROM ProphylaxisPlanning pp
                     LEFT JOIN rbProphylaxisPlanningType ppt ON pp.prophylaxisPlanningType_id = ppt.id
                     WHERE pp.client_id = Event.client_id AND ppt.code = 'ДН' AND pp.MKB like CONCAT(LEFT(Diagnosis.MKB, 3), '%%')
                      AND pp.begDate > Event.execDate
                       AND (YEAR(pp.begDate) = YEAR(Event.execDate) AND MONTH(pp.begDate) > MONTH(Event.execDate) OR YEAR(pp.begDate) > YEAR(Event.execDate))
                       AND pp.parent_id IS NOT NULL AND pp.deleted = 0 order BY pp.begDate limit 1) END
             """
             ),
        ('clientPolicy', 0):
            (u'Нет полисных данных',
             u"ClientPolicy.id is null"),
        ('BADPOLICY', 0):
            (u'Есть несколько полисов ОМС с незакрытой датой окончания действия',
             u"CountNullEndDateClientPolicy(Event.client_id) > 1"),
        ('DOC_TABN', 1):
            (u'Не заполнен табельный номер сотрудника',
            u"""exists(select ai.id from Account_Item ai
                    left join rbService s on s.id = ai.service_id
                    left join Contract_Tariff ct on ai.tariff_id = ct.id
                    left join Visit v on v.id  = ai.visit_id
                    left join Action a on a.id = ai.action_id
                    left join Event e on e.id = ai.event_id
                    left join Person p on p.id = coalesce(a.person_id, v.person_id, e.execPerson_id)
                    where ai.event_id = Event.id and ai.master_id in ({master_id}) and ai.deleted = 0
                        and (ai.sum > 0 or isPos(s.infis, rbMedicalAidType.regionalCode, ai.price) = 1)
                        and ifnull(p.code, '') = '')
                    """
             ),
        ('policyInsurer', 0):
            (u'Не указан код страховой организации',
             u"ClientPolicy.id is not null and Insurer.infisCode is null"),
        ('policyTypeCode', 0):
            (u'Не указан вид полиса',
             u"ClientPolicy.id is not null and ClientPolicy.PolicyType_id is null"),
        ('DATNDATO', 1):
            (u'Прием врача должен оказываться в один день',
            u"""exists(select ai.id from Account_Item ai
                    left join rbService s on s.id = ai.service_id
                    left JOIN vVisitServices vs ON vs.id = s.id
                    left join Contract_Tariff ct on ai.tariff_id = ct.id
                    left join Action a on a.id = ai.action_id
                    where ai.event_id = Event.id and ai.master_id in ({master_id}) and ai.deleted = 0
                        and vs.infis IS NOT NULL
                        and TO_DAYS(a.begDate) <> TO_DAYS(a.endDate)
                        and vs.infis NOT IN (
                            'B04.012.001.010', 'B04.012.001.011', 'B04.012.001.012', 'B04.008.007', 
                            'B04.015.001', 'B04.008.008', 'B04.023.006', 'B04.037.003', 'B04.023.005', 
                            'B04.040.001', 'B04.037.004', 'B04.023.003', 'B04.015.002', 'B04.023.004',
                            'B04.004.003', 'B04.025.003', 'B04.015.006', 'B05.069.008', 'B04.057.003',
                            'B04.025.004', 'B04.025.001', 'B04.058.001.001', 'B04.058.001.01',
                            'B04.058.001', 'B04.058.010', 'B04.070.007', 'B04.023.004.010', 'B04.023.005.010', 
                            'B04.058.001.010',
                            'B04.037.003.010', 'B04.037.004.010', 'B04.040.001.010', 'B04.001.003.010', 'B04.004.003.010',
                            'B04.008.007.010', 'B04.008.008.010', 'B04.015.001.010', 'B04.015.002.010', 'B04.015.006.010',
                            'B04.058.001.010', 'B04.058.001.011', 'B04.070.007.010', 'B04.023.003.010', 'B04.023.004.010',
                            'B04.023.005.010', 'B04.025.004.010', 'B04.070.009.010', 'B04.070.009'
                        )
                )
                    """
             ),
        ('StomPosDouble', 0):
            (u'В персональном счете по стоматологии оказано более одного посещения в один день',
             u"""rbMedicalAidType.regionalCode in ('31', '32') and exists(select COUNT(a2.id), date(a2.endDate)
             from Event e2
             left join EventType et2 on et2.id = e2.eventType_id
             left join Action a2 on a2.event_id = e2.id and a2.deleted = 0
             left join ActionType at2 on at2.id = a2.actionType_id
             left join rbMedicalAidType mt2 ON et2.medicalAidType_id = mt2.id
             left join rbService s2 on s2.id = at2.nomenclativeService_id
             left join Contract c2 on c2.id = IFNULL(a2.contract_id, e2.contract_id)
                 and c2.deleted = 0 -- and c2.finance_id = a2.finance_id
             left join Contract_Tariff ct2 ON ct2.master_id = IFNULL(c2.priceList_id, c2.id)
                 and ct2.service_id = s2.id and ct2.deleted = 0
                     and (ct2.endDate is not null and DATE(a2.endDate) between ct2.begDate and ct2.endDate
                     or DATE(a2.endDate) >= ct2.begDate and ct2.endDate is null)
                     and ct2.tariffType in (2,5)
             where e2.id = Event.id and isPos(s2.infis, mt2.regionalCode, ct2.price) = 1
             AND substr(s2.name,1,31) <> 'Обращение по поводу заболевания'
             group by e2.id, date(a2.endDate)
             having count(a2.id) > 1)
             """
             )
    }

    def __init__(self, parent, selectedRecords, fromExportFLC=False, oms_code=None, selectedAccountIds=None):
        CDialogBase.__init__(self, parent)
        self.fromExportFLC = fromExportFLC
        self.addObject('mnuAccountItems', QtGui.QMenu(self))
        self.addObject('mnuFLC', QtGui.QMenu(self))
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actEditClientFLC', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actOpenEvent',  QtGui.QAction(u'Открыть первичный документ', self))
        self.addObject('actDeleteEventFromAccount', QtGui.QAction(u'Удалить первичный документ из реестра', self))
        self.addObject('actSurveillancePlanningClients', QtGui.QAction(u'Контрольная карта диспансерного наблюдения', self))
        self.mnuAccountItems.addAction(self.actEditClient)
        self.mnuAccountItems.addAction(self.actOpenEvent)
        self.mnuAccountItems.addAction(self.actDeleteEventFromAccount)
        self.mnuAccountItems.addAction(self.actSurveillancePlanningClients)
        self.mnuFLC.addAction(self.actEditClientFLC)

        self.setupUi(self)
        self.setWindowFlags(Qt.Window)

        if fromExportFLC:
            self.tabWidget.removeTab(0)
            self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
            self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            self.addModels('FLC', CFLCModel(self, oms_code, selectedAccountIds))
            self.tblAccountItemsFLC.setModel(self.modelFLC)
            self.tblAccountItemsFLC.setPopupMenu(self.mnuFLC)
            self.withErrorSN = []

        if not fromExportFLC:
            self.tabWidget.removeTab(1)
            self.dePeriodFrom.setDate(QDate().currentDate())
            self.dePeriodTo.setDate(QDate().currentDate())
            self.cmbEventType.setTable('EventType', True, 'deleted = 0')

            self.chkSelectAllCheckTypes.setCheckState(Qt.Checked)

            self.addModels('AccountCheck', CAccountCheckModel(self))
            self.tblAccounts.setModel(self.modelAccountCheck)
            self.tblAccounts.show()

            self.addModels('AccountItemsCheck', CAccountItemsCheckModel(self))
            self.proxyModel = CSortFilterProxyTableModel(self, self.modelAccountItemsCheck)
            self.tblAccountItems.setSelectionModel(self.selectionModelAccountItemsCheck)
            self.tblAccountItems.setSortingEnabled(True)
            self.tblAccountItems.setModel(self.proxyModel)
            self.tblAccountItems.show()
            self.orgStructureId = None
            self.cmbEventType.setValue(None)
            self.cmbFinance.setTable('rbFinance', addNone=True)
            self.cmbFinance.setValue(None)
            self.cmbContract.setTable('Contract', "concat_ws(' | ', (select rbFinance.name from rbFinance where rbFinance.id = Contract.finance_id), Contract.resolution, Contract.number)")
            self.cmbContract.setAddNone(True, u'не задано')
            self.cmbContract.setOrder('finance_id, resolution, number')
            self.cmbContract.setFilter(u'Contract.deleted = 0')
            self.cmbContract.setValue(None)

            # self.selectionModelAccountItemsCheck.currentRowChanged.connect(self.accountItemSelectionChanged)  # после добавления self.proxyModel не работает
            self.tblAccountItems.selectionModel().currentRowChanged.connect(self.accountItemSelectionChanged)  # после добавления self.proxyModel вроде работает

            self.tblAccountItems.setPopupMenu(self.mnuAccountItems)

            if selectedRecords:
                for record in selectedRecords:
                    self.modelAccountCheck.appendRecord(record, doCheck=True)
                self.changeCheckTypes(1)
            else:
                self.twAccounts.removeTab(0)
                self.changeCheckTypes(2)

            self.chkSelectAllCheckTypes.stateChanged.connect(self.setAllCheckTypes)
            self.listCheckTypes.itemChanged.connect(self.listItemChanged)
            self.twAccounts.connect(self.twAccounts, SIGNAL("currentChanged(int)"), self.tabChanged)
            self.selectedCodes = []


    def showEvent(self, event):
        if self.fromExportFLC:
            QTimer.singleShot(0, self.beginCheckFLC)


    def changeCheckTypes(self, index):
        self.listCheckTypes.clear()
        for code, checkData in sorted(self.CheckTypes.items()):
            if code[1] in (0, index):
                item = QtGui.QListWidgetItem(checkData[0])
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                item.checkCode = code
                self.listCheckTypes.addItem(item)

    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        self.orgStructureId = self.cmbOrgStructure.value()

    @pyqtSignature('int')
    def on_cmbFinance_currentIndexChanged(self, index):

        if self.cmbFinance.value():
            self.cmbContract.setFilter(u'Contract.finance_id = {0} AND Contract.deleted = 0'.format(self.cmbFinance.value()))
            self.cmbContract.setValue(None)
        else:
            self.cmbContract.setFilter(u'Contract.deleted = 0')
            self.cmbContract.setValue(None)

    @pyqtSignature('int')
    def on_cmbContract_currentIndexChanged(self, index):
        db = QtGui.qApp.db
        EventTypeTable = db.table('EventType')
        if self.cmbContract.value():
            eventTypeIdList = self.getContractSpecificationEventType()
            cond = []
            cond.append(u"deleted = 0")
            cond.append(EventTypeTable['id'].inlist(eventTypeIdList))
            self.cmbEventType.setTable('EventType', True, db.joinAnd(cond))
            self.cmbEventType.setValue(None)
        else:
            self.cmbEventType.setTable('EventType', True, "deleted = 0")
            self.cmbEventType.setValue(None)

    def getContractSpecificationEventType(self):
        contract_id = self.cmbContract.value()
        temp = u"SELECT eventType_id FROM Contract_Specification WHERE master_id = '{0}'".format(contract_id)
        query = QtGui.qApp.db.query(temp)
        results = []
        while query.next():
            record = query.record()
            results.append(forceInt(record.value('eventType_id')))
        return results

    def setEventTypeVisible(self, value):
        self.lblEventType.setVisible(value)
        self.cmbEventType.setVisible(value)

    @pyqtSlot(int)
    def tabChanged(self, argTabIndex):
        self.changeCheckTypes(argTabIndex+1)

    def listItemChanged(self, item):
        self.chkSelectAllCheckTypes.stateChanged.disconnect(self.setAllCheckTypes)

        allChecked = True
        allUnchecked = True
        for index in range(0, self.listCheckTypes.count()):
            itemState = self.listCheckTypes.item(index).checkState()
            if itemState == Qt.Unchecked:
                allChecked = False
            else:
                allUnchecked = False
        if allChecked:
            self.chkSelectAllCheckTypes.setCheckState(Qt.Checked)
        elif allUnchecked:
            self.chkSelectAllCheckTypes.setCheckState(Qt.Unchecked)
        else:
            self.chkSelectAllCheckTypes.setCheckState(Qt.PartiallyChecked)

        self.chkSelectAllCheckTypes.stateChanged.connect(self.setAllCheckTypes)

    def setAllCheckTypes(self, state):
        if state == Qt.PartiallyChecked:
            self.chkSelectAllCheckTypes.setCheckState(Qt.Checked)
            return
        self.listCheckTypes.itemChanged.disconnect(self.listItemChanged)
        for index in range(0, self.listCheckTypes.count()):
            item = self.listCheckTypes.item(index)
            item.setCheckState(state)
        self.listCheckTypes.itemChanged.connect(self.listItemChanged)

    def getCheckQuery(self, condition, accountIds=None):
        db = QtGui.qApp.db

        def checkCase(errorCode):
            errorCondition = CAccountCheckDialog.CheckTypes[errorCode][1]
            return u"case when ({0}) then '{1} ' end".format(errorCondition, errorCode[0])

        if self.twAccounts.currentWidget() == self.tabAccount:
            table = QtGui.qApp.db.table('Account_Item')
            cond = db.joinAnd([table['master_id'].inlist(accountIds), table['deleted'].eq(0)])
            eventIdList = db.getDistinctIdList(table, idCol='Account_Item.event_id', where=cond)
            if eventIdList:
                templateCond = db.table('Event')['id'].inlist(eventIdList)
            else:
                templateCond = u"Event.id = 0"
        else:
            templateCond = u"""Event.deleted = 0
            and {0}
            /*только не выставленные/перевыставленные*/
            and Event.expose = 1
            and not exists(select ai.id from Account_Item ai where ai.event_id = Event.id and ai.deleted = 0
            and (ai.refuseType_id is null or ai.refuseType_id is not null and ai.reexposeItem_id is not null) limit 1)
                """.format(condition)

        if self.selectedCodes:
            accountIdsCond = ', '.join([str(_id) for _id in accountIds]) if accountIds else '-1'
            checkCases = u", concat_ws(' ', {0}) as errorList".format(','.join([checkCase(code) for code in self.selectedCodes]).format(master_id=accountIdsCond))
        else:
            checkCases = u', NULL as errorList'
            
        template = u"""
select Event.id as event_id,
Client.id as client_id,
concat_ws(' ', Client.lastName, Client.firstName, Client.patrName) as clientName,
Client.birthDate,
DATE(Event.setDate)  as setDate,
DATE(Event.execDate)  as execDate,
concat(Person.lastName, ' ', substr(Person.firstName, 1, 1), '. '
      , substr(Person.patrName, 1, 1), '. (', Person.code, ')') as personName,
EventType.name as eventType_title,
Diagnosis.mkb,
concat_ws(' ', Payer.infisCode, Payer.shortName) as payer_title,
DiagnosticResult.regionalCode as diagRes,
EventResult.regionalCode as eventRes,
Payer.ogrn
{0}
from Event
LEFT JOIN Organisation RelegateOrg on RelegateOrg.id = Event.relegateOrg_id
/*данные пациента */
left join Client on Client.id = Event.client_id
LEFT JOIN ClientPolicy on ClientPolicy.id = COALESCE((SELECT MAX(cp2.id) 
                                                      FROM ClientPolicy cp2
                                                      WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
    (select MAX(cp.begDate) from ClientPolicy cp
            WHERE cp.client_id = Client.id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate <= Event.setDate AND (cp.endDate is NULL OR cp.endDate >= Event.setDate))),
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
              AND cp.begDate <= Event.setDate AND (cp.endDate is NULL OR cp.endDate >= Event.setDate)
             )))
left join rbPolicyKind on rbPolicyKind.id = ClientPolicy.policyKind_id
left join Organisation as Insurer on Insurer.id = ClientPolicy.insurer_id
/*данные события*/
left join Person on Person.id = Event.execPerson_id
left join EventType on EventType.id = Event.eventType_id
left JOIN EventType_Identification eti on eti.master_id = EventType.id AND eti.value IN ('ak', 'am', 'au', 'ae', 'ag', 'ah', 'ao', 'av')
left join rbResult as EventResult on EventResult.id = Event.result_id
LEFT JOIN Diagnostic ON Diagnostic.event_id = Event.id
    AND Diagnostic.id = (SELECT MAX(d.id)
      FROM Diagnostic d
      WHERE d.event_id = Event.id
      AND d.diagnosisType_id IN (SELECT id
        FROM rbDiagnosisType
        WHERE code IN ('1', '2'))
      AND d.deleted = 0)
      left join rbDiseaseCharacter on rbDiseaseCharacter.id = Diagnostic.character_id
      left join rbDispanser on rbDispanser.id = Diagnostic.dispanser_id
left join Diagnosis on Diagnosis.id = Diagnostic.diagnosis_id and Diagnosis.deleted = 0
left join rbDiagnosticResult as DiagnosticResult on DiagnosticResult.id = Diagnostic.result_id
left join rbMedicalAidType on rbMedicalAidType.id = EventType.medicalAidType_id
left join rbEventProfile on rbEventProfile.id = EventType.eventProfile_id
left join soc_spr11 s11 on s11.code = DiagnosticResult.regionalCode and (s11.code_gr = '1'
    and rbMedicalAidType.regionalCode in ('11', '12', '301', '302', '401', '402')
            or s11.code_gr = '2' and rbMedicalAidType.regionalCode in ('41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522')
            or s11.code_gr = '3' and rbMedicalAidType.regionalCode in ('01', '02', '111', '112', '21', '22', '211',
                '222', '201', '202', '241', '232', '233', '244', '252', '242', '262', '261', '32', '31', '60', '80', '271', '272')
            or s11.code_gr = '5' and rbMedicalAidType.regionalCode in ('801', '802'))
            and s11.datn <= Event.execDate and (s11.dato >= Event.execDate or s11.dato is null)
left join soc_spr12 s12 on s12.code = EventResult.regionalCode and (s12.code_gr = '1'
    and rbMedicalAidType.regionalCode in ('11', '12', '301', '302', '401', '402')
            or s12.code_gr = '2' and rbMedicalAidType.regionalCode in ('41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522')
            or s12.code_gr = '3' and rbMedicalAidType.regionalCode in ('01', '02', '111', '112', '21', '22', '211',
                '222', '201', '202', '241', '232', '233', '244', '252', '242', '262', '261', '32', '31', '60', '80', '271', '272')
            or s12.code_gr = '5' and rbMedicalAidType.regionalCode in ('801', '802'))
            and s12.datn <= Event.execDate and (s12.dato >= Event.execDate or s12.dato is null)
left join soc_checkSpr12 scs12 on scs12.code = EventResult.regionalCode and Event.execDate between scs12.begDate and scs12.endDate
/*Плательщик*/
left join Contract on Contract.id = Event.contract_id
left JOIN rbFinance ON rbFinance.id = Contract.finance_id
LEFT JOIN Organisation AS headInsurer ON headInsurer.id = Insurer.head_id AND substr(Insurer.area, 1, 2) = '23'
LEFT JOIN Organisation as Payer on Payer.id = COALESCE(headInsurer.id, Contract.payer_id)
left join soc_spr20 s20 on s20.code = Diagnosis.MKB and s20.datn <= Event.execDate
    and (s20.dato >= Event.execDate or s20.dato is null)
left join soc_spr20 s20group on s20group.code = substr(Diagnosis.MKB, 1, 3)
    and s20group.datn <= Event.execDate and (s20group.dato >= Event.execDate or s20group.dato is null)
where EventType.code <> 'hospDir' and rbFinance.code = '2' and Contract.deleted = 0 and {1}""".format(checkCases, templateCond, QtGui.qApp.provinceKLADR()[:2])
        return template

    def getCheckResults(self, condition):
        sql = self.getCheckQuery(condition)
        query = QtGui.qApp.db.query(sql)
        results = []
        while query.next():
            results.append(query.record())

        return results


    def beginCheckFLC(self):
        self.setCursor(Qt.WaitCursor)
        QtGui.qApp.processEvents()
        self.lblResultCountFLC.setText(u'Идет проверка...')
        QtGui.qApp.processEvents()
        self.modelFLC.loadItems()
        self.setCursor(Qt.ArrowCursor)

        rows = self.modelFLC.rowCount()
        if rows:
            text = u'{0:d} {1}'.format(rows, agreeNumberAndWord(rows, (u'ошибка найдена', u'ошибки найдено', u'ошибок найдено')))
            self.lblResultCountFLC.setText(text if rows > 0 else u'Ошибок не найдено')
        else:
            QtGui.QMessageBox.information(self, u'Внимание!',
                                          u'Ошибок по структуре ФЛК не обнаружено',
                                          QtGui.QMessageBox.Ok,
                                          QtGui.QMessageBox.Ok)
            self.withErrorSN = []
            self.close()


    def beginCheck(self):
        sql = ''
        self.lblResultCount.setText(u'Проверка...')
        self.setCursor(Qt.WaitCursor)
        QtGui.qApp.processEvents()
        self.selectedCodes = []
        for index in range(0, self.listCheckTypes.count()):
            item = self.listCheckTypes.item(index)
            if item.checkState() == Qt.Checked:
                self.selectedCodes.append(item.checkCode)

        if self.twAccounts.currentWidget() == self.tabAccount:
            accountIds = []
            for record in self.modelAccountCheck.recordList():
                if forceBool(record.value('doCheck')):
                    accountIds.append(forceRef(record.value('id')))
            table = QtGui.qApp.db.table('Account_Item').alias('ai')
            sql = self.getCheckQuery(table['master_id'].inlist(accountIds), accountIds)
        elif self.twAccounts.currentWidget() == self.tabPeriod:
            dateFrom = self.dePeriodFrom.date().toString('yyyy-MM-dd')
            dateTo = self.dePeriodTo.date().toString('yyyy-MM-dd 23:59:59')
            eventTypeId = self.cmbEventType.value()
            orgStrId = self.cmbOrgStructure.value()
            financeType = self.cmbFinance.value()
            contractId = self.cmbContract.value()
            doctor = self.cmbFilterEventPerson.value()
            cond = []
            db = QtGui.qApp.db
            Person = db.table("Person")
            cond.append(u"(Event.execDate between '{0}' and '{1}')".format(dateFrom, dateTo))
            if orgStrId:
                cond.append(Person['orgStructure_id'].inlist(getOrgStructureDescendants(orgStrId)))
            if eventTypeId:
                cond.append(u"Event.eventType_id = '{0}'".format(eventTypeId))
            if financeType:
                cond.append(u"rbFinance.id = '{0}'".format(financeType))
            if contractId:
                cond.append(u"Event.contract_id = '{0}'".format(contractId))
            if doctor:
                cond.append(u"Event.execPerson_id = '{0}'".format(doctor))

            sql = self.getCheckQuery(db.joinAnd(cond))
        self.modelAccountItemsCheck.loadFromSql(sql, lambda record: record.value('errorList') != '')
        self.setCursor(Qt.ArrowCursor)
        rows = self.tblAccountItems.model().rowCount()
        text = u'{0:d} {1}'.format(rows,
                                   agreeNumberAndWord(rows, (u'ошибка найдена', u'ошибки найдено', u'ошибок найдено')))
        self.lblResultCount.setText(text if rows > 0 else u'Ошибок не найдено')
        if rows > 0:
            buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
            default = QtGui.QMessageBox.Yes
            message = u'Распечатать полученные данные?'
            result = QtGui.QMessageBox().question(self,
                                                  u'Внимание!',
                                                  message,
                                                  buttons,
                                                  default) == QtGui.QMessageBox.Yes
            if not result:
                return
            self.buildCheckReport()


    def buildCheckReport(self):
        CReportAccountCheck(self).exec_()


    @pyqtSlot()
    def on_btnBeginCheck_clicked(self):
        self.beginCheck()


    @pyqtSlot()
    def on_btnBeginCheckFLC_clicked(self):
        self.beginCheckFLC()


    @pyqtSlot()
    def on_btnNext_clicked(self):
        items = self.modelFLC.items()
        self.withErrorSN = []
        if items:
            for item in items:
                self.withErrorSN.append(forceRef(item.value('SN')))
            if QtGui.QMessageBox.warning(self, u'Внимание!',
                                          u'Персональные счета с ошибками структуры не будут выгружены на ФЛК!\nПродолжить?',
                                          QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                          QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                self.close()


    @pyqtSlot()
    def on_btnPrint_clicked(self):
        self.tblAccountItemsFLC.setReportHeader(u'Ошибки ФЛК')
        self.tblAccountItemsFLC.printContent()


    def accountItemSelectionChanged(self, current, previous):
        record = self.tblAccountItems.model().getRecordByRow(current.row())
        errorCodes = forceString(record.value('errorList')).split()
        errorDescriptions = [CAccountCheckDialog.CheckTypes[(code, 0)][0] if (code, 0) in CAccountCheckDialog.CheckTypes else CAccountCheckDialog.CheckTypes[(code, 1)][0] for code in errorCodes]
        self.textErrorDescription.setPlainText("\n".join(errorDescriptions))

    @pyqtSlot()
    def on_mnuAccountItems_aboutToShow(self):
        isAccountant = QtGui.qApp.userHasAnyRight(accountantRightList)
        currentRows = self.tblAccountItems.selectedRowList()
        itemPresent = currentRows != [] and isAccountant
        self.actEditClient.setEnabled(currentRows != [])
        self.actOpenEvent.setEnabled(currentRows != [])
        self.actSurveillancePlanningClients.setEnabled(currentRows != [])
        self.actDeleteEventFromAccount.setEnabled(itemPresent and self.twAccounts.currentWidget() == self.tabAccount)
        if len(currentRows) == 1:
            self.actEditClient.setVisible(True)
            self.actOpenEvent.setVisible(True)
            self.actSurveillancePlanningClients.setVisible(True)
            self.actDeleteEventFromAccount.setText(u'Удалить первичный документ из реестра')
            self.actDeleteEventFromAccount.setVisible(True)
        elif len(currentRows) > 1:
            self.actEditClient.setVisible(False)
            self.actOpenEvent.setVisible(False)
            self.actSurveillancePlanningClients.setVisible(False)
            self.actDeleteEventFromAccount.setText(u'Удалить выбранные первичные документы из реестра')
            self.actDeleteEventFromAccount.setVisible(True)


    @pyqtSlot()
    def on_mnuFLC_aboutToShow(self):
        currentRow = self.tblAccountItemsFLC.currentIndex().row()
        self.actEditClientFLC.setEnabled(currentRow >= 0)


    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        row = self.tblAccountItems.currentIndex().row()
        record = self.tblAccountItems.model().getRecordByRow(row)
        clientId = forceRef(record.value('client_id'))
        if clientId:
            dialog = CClientEditDialog(self)
            try:
                dialog.load(clientId)
                if dialog.exec_():
                    invalidatedRecords = self.modelAccountItemsCheck.client_id.select(clientId)
                    self.recheckRecords(invalidatedRecords)
            finally:
                dialog.deleteLater()


    @pyqtSignature('')
    def on_actEditClientFLC_triggered(self):
        row = self.tblAccountItemsFLC.currentIndex().row()
        clientId = forceInt(self.modelFLC.value(row, 'clientId'))
        eventId = forceInt(self.modelFLC.value(row, 'SN'))
        if clientId:
            dialog = CClientEditDialog(self)
            try:
                dialog.load(clientId)
                if dialog.exec_():
                    self.modelFLC.validateRecord(row, eventId)
            finally:
                dialog.deleteLater()


    def recheckRecords(self, records):
        for record in records:
            eventId = forceRef(record.value('event_id'))
            newRecord = self.getCheckResults(u'Event.id = {0:d}'.format(eventId))
            self.modelAccountItemsCheck.assignRecord(record, newRecord[0])

    @pyqtSlot()
    def on_actOpenEvent_triggered(self):
        row = self.tblAccountItems.currentIndex().row()
        record = self.tblAccountItems.model().getRecordByRow(row)
        eventId = forceRef(record.value('event_id'))
        if eventId:
            formClass = getEventFormClass(eventId)
            dialog = formClass(self)
            try:
                dialog.load(eventId)
                if dialog.exec_():
                    if QtGui.qApp.checkGlobalPreference(u'23:obr', u'да'):
                        QtGui.qApp.db.query(u'CALL InsertObr({0:d});'.format(dialog.itemId()))
                    invalidatedRecords = self.modelAccountItemsCheck.event_id.select(eventId)
                    self.recheckRecords(invalidatedRecords)
            finally:
                dialog.deleteLater()

    @pyqtSlot()
    def on_actDeleteEventFromAccount_triggered(self):
        db = QtGui.qApp.db
        tableAccountItem = db.table('Account_Item')
        rows = self.tblAccountItems.selectedRowList()
        rows.sort()
        records = []
        eventIds = []
        accountIds = []
        for index, row in enumerate(rows):
            records.append(self.tblAccountItems.model().getRecordByRow(row))
            eventIds.append(forceRef(records[index].value('event_id')))
            accountIds.extend(db.getDistinctIdList(tableAccountItem, tableAccountItem['master_id'].name(),
                                                   tableAccountItem['event_id'].eq(eventIds[index])))
        eventIds.reverse()
        accountIds.reverse()
        if eventIds and accountIds:
            message = u'Вы действительно хотите удалить первичный документ из реестра?'
            if QtGui.QMessageBox().question(self, u'Внимание!', message, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                            QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                QtGui.qApp.setWaitCursor()
                try:
                    db.transaction()
                    try:
                        for index, row in enumerate(reversed(rows)):
                            itemList = db.getDistinctIdList(tableAccountItem, tableAccountItem['id'].name(),
                                                            [tableAccountItem['master_id'].eq(accountIds[index]),
                                                            tableAccountItem['event_id'].eq(eventIds[index])])
                            clearPayStatus(accountIds[index], itemList)
                            db.deleteRecordSimple(tableAccountItem, tableAccountItem['id'].inlist(itemList))
                            updateAccount(accountIds[index])
                            self.tblAccountItems.model().removeRow(row)
                        db.commit()
                    except:
                        db.rollback()
                        QtGui.qApp.logCurrentException()
                        raise
                finally:
                    QtGui.qApp.restoreOverrideCursor()

    @pyqtSignature('')
    def on_actSurveillancePlanningClients_triggered(self):
        row = self.tblAccountItems.currentIndex().row()
        record = self.tblAccountItems.model().getRecordByRow(row)
        clientId = forceRef(record.value('client_id'))
        eventId = forceRef(record.value('event_id'))
        if isSurveillanceActive(clientId, {'event_id': eventId}, {'begDate': QDate.currentDate(), 'event_id': eventId}):
            surPlanningShow = CSurveillanceDialog(self, isFake=True)
            surPlanningShow.surveillancePlanningShow(clientId, eventId=eventId)
        else:
            QtGui.QMessageBox().information(self, u'Информация', u'Пациент не состоит на диспансерном наблюдении по диагнозам в событии!', QtGui.QMessageBox.Close)


class CFLCModel(CRecordListModel):
    def __init__(self, parent, oms_code, selectedAccountIds):
        CRecordListModel.__init__(self, parent)
        self.oms_code = oms_code
        self.selectedAccountIds = selectedAccountIds
        self.addCol(CInDocTableCol(u'Ошибки', 'CHECK_LIST', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'NS', 'NS', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'VS', 'VS', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'DATS', 'DATS', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'SN', 'SN', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'DATPS', 'DATPS', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'CODE_MO', 'CODE_MO', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'PL_OGRN', 'PL_OGRN', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'FIO', 'FIO', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'IMA', 'IMA', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'OTCH', 'OTCH', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'POL', 'POL', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'DATR', 'DATR', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'SNILS', 'SNILS', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'OKATO_OMS', 'OKATO_OMS', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'SPV', 'SPV', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'SPS', 'SPS', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'SPN', 'SPN', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'ENP', 'ENP', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'Q_G', 'Q_G', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'FAMP', 'FAMP', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'IMP', 'IMP', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'OTP', 'OTP', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'POLP', 'POLP', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'DATRP', 'DATRP', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'C_DOC', 'C_DOC', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'S_DOC', 'S_DOC', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'N_DOC', 'N_DOC', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'DATN', 'DATN', 100).setReadOnly())
        self.addCol(CInDocTableCol(u'DATO', 'DATO', 100).setReadOnly())

        self._enableAppendLine = False
        self._extColsPresent = False


    def getCheckFLCQueryStmt(self, eventId=None):
        db = QtGui.qApp.db
        table = db.table('Account_Item')
        cond = [table['deleted'].eq(0),
                table['master_id'].inlist(self.selectedAccountIds)]
        if eventId:
            cond.append(table['event_id'].eq(eventId))

        flcQueryStmt = getFLCQuery().format(where=db.joinAnd(cond), oms_code=self.oms_code)

        stmt = u"""SELECT CONCAT_WS(', ',
                  IF(NS        REGEXP '^[[:digit:]]{1,5}$' = 1 OR IFNULL(NS, '') = '',                                               NULL, 'Некорректное поле NS'),
                  IF(VS        REGEXP '^.{1,2}$' = 1 OR IFNULL(VS, '') = '',                                                         NULL, 'Некорректное поле VS'),
                  IF(DATS      REGEXP '^[[:digit:]]{4}-[[:digit:]]{2}-[[:digit:]]{2}$' = 1 OR DATS IS NULL,                          NULL, 'Некорректное поле DATS'),
                  IF(SN        REGEXP '^[[:digit:]]{1,12}$' = 1 OR SN IS NULL,                                                       NULL, 'Некорректное поле SN'),
                  IF(DATPS     REGEXP '^[[:digit:]]{4}-[[:digit:]]{2}-[[:digit:]]{2}$' = 1 OR DATPS IS NULL,                         NULL, 'Некорректное поле DATPS'),
                  IF(CODE_MO   REGEXP '^.{1,5}$' = 1,                                                                                NULL, 'Некорректное поле CODE_MO'),
                  IF(PL_OGRN   REGEXP '^.{1,15}$' = 1 OR IFNULL(PL_OGRN, '') = '',                                                   NULL, 'Некорректное поле PL_OGRN'),
                  IF(CHAR_LENGTH(FIO) BETWEEN 1 AND 40,                                                                              NULL, 'Некорректное поле FIO'),
                  IF(CHAR_LENGTH(IMA) BETWEEN 1 AND 40,                                                                              NULL, 'Некорректное поле IMA'),
                  IF(CHAR_LENGTH(OTCH) <= 40,                                                                                        NULL, 'Некорректное поле OTCH'),
                  IF(CHAR_LENGTH(POL) = 1,                                                                                           NULL, 'Некорректное поле POL'),
                  IF(DATR      REGEXP '^[[:digit:]]{4}-[[:digit:]]{2}-[[:digit:]]{2}$' = 1,                                          NULL, 'Некорректное поле DATR'),
                  IF(SNILS     REGEXP '^[[:digit:]]{3}-[[:digit:]]{3}-[[:digit:]]{3} [[:digit:]]{2}$' = 1 OR IFNULL(SNILS, '') = '', NULL, 'Некорректное поле SNILS'),
                  IF(OKATO_OMS REGEXP '^.{1,5}$' = 1 OR IFNULL(OKATO_OMS, '') = '',                                                  NULL, 'Некорректное поле OKATO_OMS'),
                  IF(SPV       REGEXP '^[[:digit:]]{1}$' = 1 OR IFNULL(SPV, '') = '',                                                NULL, 'Некорректное поле SPV'),
                  IF(SPS       REGEXP '^.{1,10}$' = 1 OR IFNULL(SPS, '') = '',                                                       NULL, 'Некорректное поле SPS'),
                  IF(SPN       REGEXP '^.{1,20}$' = 1 OR IFNULL(SPN, '') = '',                                                       NULL, 'Некорректное поле SPN'),
                  IF(ENP       REGEXP '^[[:digit:]]{16}$' = 1 OR IFNULL(ENP, '') = '',                                               NULL, 'Некорректное поле ENP'),
                  IF(Q_G       REGEXP '^.{1,10}$' = 1 OR Q_G = '',                                                                   NULL, 'Некорректное поле Q_G'),
                  IF(CHAR_LENGTH(FAMP) <= 40,                                                                                        NULL, 'Некорректное поле FAMP'),
                  IF(CHAR_LENGTH(IMP) <= 40,                                                                                         NULL, 'Некорректное поле IMP'),
                  IF(CHAR_LENGTH(OTP) <= 40,                                                                                         NULL, 'Некорректное поле OTP'),
                  IF(CHAR_LENGTH(POL) <= 1,                                                                                          NULL, 'Некорректное поле POLP'),
                  IF(DATRP     REGEXP '^[[:digit:]]{4}-[[:digit:]]{2}-[[:digit:]]{2}$' = 1 OR IFNULL(DATRP, '') = '',                NULL, 'Некорректное поле DATRP'),
                  IF(C_DOC     REGEXP '^[[:digit:]]{1,2}$' = 1 OR IFNULL(C_DOC, '') = '',                                            NULL, 'Некорректное поле NS'),
                  IF(S_DOC     REGEXP '^.{1,10}$' = 1 OR IFNULL(S_DOC, '') = '',                                                     NULL, 'Некорректное поле S_DOC'),
                  IF(N_DOC     REGEXP '^.{1,15}$' = 1 OR IFNULL(N_DOC, '') = '',                                                     NULL, 'Некорректное поле N_DOC'),
                  IF(DATN      REGEXP '^[[:digit:]]{4}-[[:digit:]]{2}-[[:digit:]]{2}$' = 1,                                          NULL, 'Некорректное поле DATN'),
                  IF(DATO      REGEXP '^[[:digit:]]{4}-[[:digit:]]{2}-[[:digit:]]{2}$' = 1 OR IFNULL(DATO, '') = '',                 NULL, 'Некорректное поле DATN')
                  )  AS CHECK_LIST,
                  t.*
                FROM (%s) AS t
                HAVING CHECK_LIST <> ''""" % flcQueryStmt
        return stmt


    def loadItems(self):
        u"""Запрос для проверки ФЛК"""
        db = QtGui.qApp.db
        stmt = self.getCheckFLCQueryStmt()
        query = db.query(stmt)
        items = []
        while query.next():
            record = query.record()
            items.append(record)
        self.setItems(items)
        self.reset()


    def validateRecord(self, row, eventId):
        u"""Запрос для проверки ФЛК"""
        db = QtGui.qApp.db
        stmt = self.getCheckFLCQueryStmt(eventId)
        query = db.query(stmt)
        if query.next():
            record = query.record()
            self._items[row] = record
            self.emitRowChanged(row)
        else:
            self.removeRow(row)
