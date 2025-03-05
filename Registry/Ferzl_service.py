# -*- coding: utf-8 -*-
import base64
import urlparse
import uuid
from datetime import datetime
import json
import requests
from PyQt4.QtGui import QDialog

from Registry.Utils import getClientInfo, CSocStatusTypeCache
from library.MSCAPI import MSCApi
from library.Utils import forceString, forceInt, unformatSNILS

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt, QDateTime

getNrData_nbLoc = {
    u'1': u"в стационаре",
    u'2': u"дома",
    u'3': u"в другом месте",
    u'4': u"неизвестно"

}

getNrData_nbPerformer = {
    u'1': u"врач-акушер-гинеколог",
    u'2': u"фельдшер, акушерка",
    u'3': u"другое лицо"

}


getPersonData_attachStatus = {
    u"ДПП": u"Действующее подушевое",
    u"ДПУ": u"Действующее учетное",
    u"НСУ": u"Недействующее. Истечение срока действия учетного прикрепления",
    u"НДВ": u"Недействующее (достижение восемнадцатилетнего возраста)",
    u"НСМ": u"Недействующее (смена/закрытие МО)",
    u"НПП": u"Недействующее (прочие причины)",
    u"НАП": u"Недействующее (аннулированное)",
    u"ДВП": u"Действующее (временное подушевое) ",
    u"ДВУ": u"Действующее (временное учетное)",
    u"НВП": u"Недействующее (временное)"

}

getPersonData_pcyStatus = {
    u"ДНП": u"Действующий (на подтверждении)",
    u"ДПП": u"Действующий (подтверждённый)",
    u"НСД": u"Недействующий (истечение срока действия)",
    u"НСН": u"Недействующий (в связи со смертью)",
    u"НСП": u"Недействующий  (в связи со смертью на подтверждении)",
    u"НПГ": u"Недействующий (прекращение гражданства)",
    u"НАЖ": u"Недействующий (аннулирование вида на жительство)",
    u"НВР": u"Недействующий (аннулирование разрешения на временное проживание)",
    u"НУБ": u"Недействующий (утрата или лишение статуса беженца)",
    u"НВС": u"Недействующий (приостановлен в случае призыва на военную службу)",
    u"НПВ": u"Недействующий (приостановлен в случае поступления на военную службу или приравненную к ней службу)",
    u"ННП": u"Недействующий (не подтверждён)",
    u"НАП": u"Недействующий (аннулирован)"

}

getNrData_gender = {
    '0': u'Не задано',
    '1': u"Мужской",
    '2': u"Женский"
}

getNrData_birthOutcome = {
    '1': u"живорожденный",
    '2': u"мертворожденный"
}

getNrData_pregnancyRate_dict = {
    '1': u'Нет',
    '2': u'Да'
}


getNrData_docType_dict = {
    '33': u"Медицинское свидетельство о рождении",
    '14': u"Медицинское свидетельство о перинатальной смерти",
    '354': u"Документ, содержащий сведения медицинского свидетельства о перинатальной смерти в бумажной форме"
}

getPersonData_attachMethod = {
    u'1': u"по территориальному признаку",
    u'2': u"по личному заявлению",
    u'3': u"по электронному заявлению",
    u'4': u"по распоряжению органов здравоохранения"
}

getPersonData_areaType = {
    u'1': u"терапевтический",
    u'2': u"акушерско-гинекологический",
    u'3': u"стоматологический",
    u'4': u"СМП",
    u'5': u"ФАП (ФАП, ФП, врачебная амбулатория)"

}

getPersonData_pcyType = {
    u'Е': u'Временное свидетельство в форме электронного документа',
    u'П': u'Бумажный полис ОМС единого образца',
    u'Э': u'Электронный полис ОМС единого образца',
    u'К': u'Полис ОМС в составе универсальной электронной карты',
    u'Ц': u'Цифровой полис ОМС',
    u'Х': u'Состояние на учёте без полиса ОМС',
    u'М': u'Состояние на учёте МФЦ'

}

createUpdateNil_physique = {
    u'Нормостеническое': 1,
    u'Астеническое': 2,
    u'Гиперстеническое': 3
}

createUpdateNil_eyecolor = {
    u'Чёрный': 1,
    u'Тёмно-карий': 2,
    u'Светло-карий': 3,
    u'Жёлтый': 4,
    u'Буро-жёлто-зелёный': 5,
    u'Зелёный': 6,
    u'Серо-зелёный': 7,
    u'Светлый с буро-желтым венчиком': 8,
    u'Серый': 9,
    u'Серо-голубой': 10,
    u'Голубой': 11,
    u'Синий': 12
}

createUpdateNil_hgrow = {
    u'низкий': 1,
    u'средний': 2,
    u'высокий': 3,
    u'очень высокий': 4
}


class Ferzl_service:
    def __init__(self):
        url_service = forceString(QtGui.qApp.getGlobalPreference('23:servicesURL'))
        self.url = (url_service + u'api/ferzl') if url_service[-1] == u'/' else (url_service + u'/api/ferzl')



    def getPersonDataFrom(self, params_dict = {}):

        params = {
                  "external_id": forceString(params_dict.get('external_id')),
                  "pcyType": forceString(params_dict.get('pcyType',None)),
                  "enp": forceString(params_dict.get('enp', None)),
                  "pcySer": forceString(params_dict.get('pcySer',None)),
                  "pcyNum": forceString(params_dict.get('pcyNum', None)),
                  "dudlSer": forceString(params_dict.get('dudlSer',None)),
                  "dudlNum": forceString(params_dict.get('dudlNum',None)),
                  "dudlType": forceString(params_dict.get("dudlType", None)),
                  "dudlDateB": forceString(params_dict.get("dudlDateB", None)),
                  "dt": forceString(params_dict.get('dt', None)),
                  "show": forceString(params_dict.get("show", None))
                  }
        isError = False
        buttonName = None
        url = forceString(self.url+'/oms/services/MpiPersonInfo') + forceString('?') + forceString(self.generateURLParams(params))
        resp = requests.get(url=url, params=params)
        result_dict = {
            'result': False,
            'elements': {}
        }
        if resp.status_code != 200:
            message = u'Ошибка сервисов. Код ошибки: ' + forceString(resp.status_code) + u' - ' + forceString(
                resp.reason)+ u'. MpiPersonInfo'
            msgbx = self.showMessageBox(message, isError=True)
            if msgbx == QtGui.QMessageBox.Cancel:
                return None
        if resp:
            jsonRequest = resp.json()
            message = u""
            oip, policy, attach, person = None, None, None, None
            firstName, surname, patronymic, birthDay, gender, deathDate, whenMerged = None, None, None, None, None, None, None
            if u'getPersonDataResponse' in jsonRequest['Envelope']['Body'].keys():
                main_tag = jsonRequest['Envelope']['Body']['getPersonDataResponse']
                if u'pd' in main_tag.keys():
                    person_data = main_tag['pd']
                    result_dict['result'] = True
                    oip = person_data.get('oip', None)
                    policy = person_data.get('policy', None)
                    attach = person_data.get('attach', None)
                    person = person_data.get('person', None)
                    if oip:
                        # message = message + u'ОИП: ' + forceString(oip) + u"\n"
                        result_dict['elements']['oip'] = oip
                    if person:
                        firstName = forceString(person['personItems'].get('firstName', None))
                        surname = forceString(person['personItems'].get('surname', None))
                        patronymic = forceString(person['personItems'].get('patronymic', None))
                        birthDay = forceString(person['personItems'].get('birthDay', None))
                        gender = forceInt(person['personItems'].get('gender', None))
                        deathDate = forceString(person['personItems'].get('deathDate', None))
                        whenMerged = forceString(person['personItems'].get('whenMerged', None))
                        if surname:
                            result_dict['elements']['surname'] = surname
                        if firstName:
                            result_dict['elements']['firstName'] = firstName
                        if patronymic:
                            result_dict['elements']['patronymic'] = patronymic
                        if birthDay:
                            birthDay = datetime.strptime(birthDay, '%Y-%m-%d')
                            birthDay = birthDay.date().strftime('%d.%m.%Y')
                            result_dict['elements']['birthDay'] = birthDay
                        if gender:
                            result_dict['elements']['gender'] = gender
                        if deathDate:
                            deathDate = datetime.strptime(deathDate, '%Y-%m-%d')
                            deathDate = deathDate.date().strftime('%d.%m.%Y')
                            result_dict['elements']['deathDate'] = deathDate
                        if whenMerged:
                            result_dict['elements']['whenMerged'] = whenMerged

                    if policy:
                        policy_insurfCode, policy_gender, policy_okato, policy_insurfName, policy_pcyStatus, policy_enp, \
                        policy_insurfOgrn, policy_pcyDateB, policy_pcyDateE, policy_pcyType, policy_pcySer, policy_pcyNum = None, None, None, None, None, None, None, None, None, None, None, None
                        policy_list = []
                        if isinstance(policy['policyItems'], dict):
                            policy_insurfCode = forceString(policy['policyItems'].get('insurfCode', None))
                            policy_gender = forceString(policy['policyItems'].get('gender', None))
                            policy_okato = forceString(policy['policyItems'].get('okato', None))
                            policy_insurfName = forceString(policy['policyItems'].get('insurfName', None))
                            policy_pcyStatus = forceString(policy['policyItems'].get('pcyStatus', None))
                            policy_enp = forceString(policy['policyItems'].get('enp', None))
                            policy_insurfOgrn = forceString(policy['policyItems'].get('insurfOgrn', None))
                            policy_pcyDateB =  forceString(policy['policyItems'].get('pcyDateB', None))
                            policy_pcyDateE = forceString(policy['policyItems'].get('pcyDateE', None))
                            policy_pcyType = forceString(policy['policyItems'].get('pcyType', None))
                            policy_pcySer = forceString(policy['policyItems'].get('pcySer', None))
                            policy_pcyNum = forceString(policy['policyItems'].get('pcyNum', None))
                            policy_dict = {}
                            if policy_pcySer:
                                policy_dict['policy_pcySer'] = policy_pcySer
                            if policy_pcyNum:
                                policy_dict['policy_pcyNum'] = policy_pcyNum
                            if policy_enp:
                                policy_dict['policy_enp'] = policy_enp
                            if policy_pcyDateB:
                                policy_pcyDateB = datetime.strptime(policy_pcyDateB, '%Y-%m-%d')
                                policy_pcyDateB = policy_pcyDateB.date().strftime('%d.%m.%Y')
                                policy_dict['policy_pcyDateB'] = policy_pcyDateB
                            if policy_pcyDateE:
                                policy_pcyDateE = datetime.strptime(policy_pcyDateE, '%Y-%m-%d')
                                policy_pcyDateE = policy_pcyDateE.date().strftime('%d.%m.%Y')
                                policy_dict['policy_pcyDateE'] = policy_pcyDateE
                            if policy_pcyType:
                                policy_dict['policy_pcyType'] = policy_pcyType
                            if policy_pcyStatus:
                                policy_dict['policy_pcyStatus'] = policy_pcyStatus
                            if policy_okato:
                                policy_dict['policy_okato'] = policy_okato
                            if policy_gender:
                                # message = message + u"Половая принадлежность: " + policy_gender + u'\n'
                                policy_dict['policy_gender'] = policy_gender
                            if policy_insurfName:
                                    # message = message +u"СМО: " + policy_insurfName+ u'\n'
                                policy_dict['policy_insurfName'] = policy_insurfName
                            if policy_insurfOgrn:
                                policy_dict['policy_insurfOgrn'] = policy_insurfOgrn
                            if policy_insurfCode:
                                policy_dict['policy_insurfCode'] = policy_insurfCode

                            policy_list.append(policy_dict)
                        elif isinstance(policy['policyItems'], list):
                            for policys_elem in policy['policyItems']:
                                policy_dict = {}
                                policy_insurfCode = forceString(policys_elem.get('insurfCode', None))
                                policy_gender = forceString(policys_elem.get('gender', None))
                                policy_okato = forceString(policys_elem.get('okato', None))
                                policy_insurfName = forceString(policys_elem.get('insurfName', None))
                                policy_pcyStatus = forceString(policys_elem.get('pcyStatus', None))
                                policy_enp = forceString(policys_elem.get('enp', None))
                                policy_insurfOgrn = forceString(policys_elem.get('insurfOgrn', None))
                                policy_pcyDateB = forceString(policys_elem.get('pcyDateB', None))
                                policy_pcyDateE = forceString(policys_elem.get('pcyDateE', None))
                                policy_pcyType = forceString(policys_elem.get('pcyType', None))
                                policy_pcySer = forceString(policys_elem.get('pcySer', None))
                                policy_pcyNum = forceString(policys_elem.get('pcyNum', None))
                                if policy_pcySer:
                                    policy_dict['policy_pcySer'] = policy_pcySer
                                if policy_pcyNum:
                                    policy_dict['policy_pcyNum'] = policy_pcyNum
                                if policy_enp:
                                    policy_dict['policy_enp'] = policy_enp
                                if policy_pcyDateB:
                                    policy_pcyDateB = datetime.strptime(policy_pcyDateB, '%Y-%m-%d')
                                    policy_pcyDateB = policy_pcyDateB.date().strftime('%d.%m.%Y')
                                    policy_dict['policy_pcyDateB'] = policy_pcyDateB
                                if policy_pcyDateE:
                                    policy_pcyDateE = datetime.strptime(policy_pcyDateE, '%Y-%m-%d')
                                    policy_pcyDateE = policy_pcyDateE.date().strftime('%d.%m.%Y')
                                    policy_dict['policy_pcyDateE'] = policy_pcyDateE
                                if policy_pcyType:
                                    policy_dict['policy_pcyType'] = policy_pcyType
                                if policy_pcyStatus:
                                    policy_dict['policy_pcyStatus'] = policy_pcyStatus
                                if policy_okato:
                                    policy_dict['policy_okato'] = policy_okato
                                if policy_gender:
                                    policy_dict['policy_gender'] = policy_gender
                                if policy_insurfName:
                                    policy_dict['policy_insurfName'] = policy_insurfName
                                if policy_insurfOgrn:
                                    policy_dict['policy_insurfOgrn'] = policy_insurfOgrn
                                if policy_insurfCode:
                                    policy_dict['policy_insurfCode'] = policy_insurfCode
                                policy_list.append(policy_dict)
                        result_dict['elements']['policy'] = policy_list

                    if attach:
                        attach_areaType, attach_attachMethod, attach_dateAttachB, attach_dateAttachE, attach_moCode, attach_moFId, attach_moOkato, attach_attachStatus, \
                        attach_depId = None, None, None, None, None, None, None, None, None
                        attach_list = []
                        if isinstance(attach['attachItems'], dict):
                            attach_dict = {}
                            attach_areaType = forceString(attach['attachItems'].get('areaType', None))
                            attach_attachMethod = forceString(attach['attachItems'].get('attachMethod', None))
                            attach_dateAttachB = forceString(attach['attachItems'].get('dateAttachB', None))
                            attach_dateAttachE = forceString(attach['attachItems'].get('dateAttachE', None))
                            attach_moCode = forceString(attach['attachItems'].get('moCode', None))
                            attach_moFId = forceString(attach['attachItems'].get('moFId', None))
                            attach_moOkato = forceString(attach['attachItems'].get('moOkato', None))
                            attach_attachStatus = forceString(attach['attachItems'].get('attachStatus', None))
                            attach_depId = forceString(attach['attachItems'].get('depId', None))
                            if attach_areaType:
                                attach_dict['attach_areaType'] = attach_areaType
                            if attach_attachMethod:
                                attach_dict['attach_attachMethod'] = attach_attachMethod
                            if attach_dateAttachB:
                                attach_dateAttachB = datetime.strptime(attach_dateAttachB, '%Y-%m-%d')
                                attach_dateAttachB = attach_dateAttachB.date().strftime('%d.%m.%Y')
                                attach_dict['attach_dateAttachB'] = attach_dateAttachB
                            if attach_dateAttachE:
                                attach_dateAttachE = datetime.strptime(attach_dateAttachE, '%Y-%m-%d')
                                attach_dateAttachE = attach_dateAttachE.date().strftime('%d.%m.%Y')
                                attach_dict['attach_dateAttachE'] = attach_dateAttachE
                            if attach_moCode:
                                attach_dict['attach_moCode'] = attach_moCode
                            if attach_moFId:
                                attach_dict['attach_moFId'] = attach_moFId
                            if attach_moOkato:
                                attach_dict['attach_moOkato'] = attach_moOkato
                            if attach_attachStatus:
                                attach_dict['attach_attachStatus'] = attach_attachStatus
                            if attach_depId:
                                attach_dict['attach_depId'] = attach_depId
                            attach_list.append(attach_dict)
                        elif isinstance(attach['attachItems'], list):
                            for attach_item in attach['attachItems']:
                                attach_dict = {}
                                attach_areaType = forceString(attach_item.get('areaType', None))
                                attach_attachMethod = forceString(attach_item.get('attachMethod', None))
                                attach_dateAttachB = forceString(attach_item.get('dateAttachB', None))
                                attach_dateAttachE = forceString(attach_item.get('dateAttachE', None))
                                attach_moCode = forceString(attach_item.get('moCode', None))
                                attach_moFId = forceString(attach_item.get('moFId', None))
                                attach_moOkato = forceString(attach_item.get('moOkato', None))
                                attach_attachStatus = forceString(attach_item.get('attachStatus', None))
                                attach_depId = forceString(attach_item.get('depId', None))
                                if attach_areaType:
                                    attach_dict['attach_areaType'] = attach_areaType
                                if attach_attachMethod:
                                    attach_dict['attach_attachMethod'] = attach_attachMethod
                                if attach_dateAttachB:
                                    attach_dateAttachB = datetime.strptime(attach_dateAttachB, '%Y-%m-%d')
                                    attach_dateAttachB = attach_dateAttachB.date().strftime('%d.%m.%Y')
                                    attach_dict['attach_dateAttachB'] = attach_dateAttachB
                                if attach_dateAttachE:
                                    attach_dateAttachE = datetime.strptime(attach_dateAttachE, '%Y-%m-%d')
                                    attach_dateAttachE = attach_dateAttachE.date().strftime('%d.%m.%Y')
                                    attach_dict['attach_dateAttachE'] = attach_dateAttachE
                                if attach_moCode:
                                    attach_dict['attach_moCode'] = attach_moCode
                                if attach_moFId:
                                    attach_dict['attach_moFId'] = attach_moFId
                                if attach_moOkato:
                                    attach_dict['attach_moOkato'] = attach_moOkato
                                if attach_attachStatus:
                                    attach_dict['attach_attachStatus'] = attach_attachStatus
                                if attach_depId:
                                    attach_dict['attach_depId'] = attach_depId
                                attach_list.append(attach_dict)
                        result_dict['elements']['attach'] = attach_list
                    buttonName = u"Обновить полисные данные"
                    if result_dict['elements'].get('surname', None):
                        message = message + u'Фамилия: ' + result_dict['elements'].get('surname') + u'\n'
                    if result_dict['elements'].get('firstName', None):
                        message = message + u'Имя: ' + result_dict['elements'].get('firstName') + u'\n'
                    if result_dict['elements'].get('patronymic', None):
                        message = message + u'Отчество: ' + result_dict['elements'].get('patronymic') + u'\n'
                    if result_dict['elements'].get('birthDay', None):
                        message = message + u'Дата рождения: ' + result_dict['elements'].get('birthDay') + u'\n'
                    if result_dict['elements'].get('deathDate', None):
                        message = message + u'Дата гашения персоны: ' + result_dict['elements'].get('deathDate') + u'\n'
                    if result_dict['elements'].get('whenMerged', None):
                        message = message + u'Дата и время объединения с дубликатом: ' + result_dict['elements'].get('whenMerged') + u'\n'
                    policy = result_dict['elements'].get('policy', None)
                    if policy:
                        if len(policy) > 0:
                            for item in policy:
                                if item.get('policy_pcySer', None):
                                    message = message + u"Серия полиса ОМС: " + item.get('policy_pcySer') + u'\n'
                                if item.get('policy_pcyNum', None):
                                    message = message +u"Номер полиса ОМС: " + item.get('policy_pcyNum')+ u'\n'
                                if item.get('policy_enp', None):
                                    message = message +u"ЕНП: " + item.get('policy_enp')+ u'\n'
                                if item.get('policy_pcyDateB', None):
                                    message = message +u"Дата начала действия полиса: " + item.get('policy_pcyDateB')+ u'\n'
                                if item.get('policy_pcyDateE', None):
                                    message = message + u"Дата окончания действия полиса: " + item.get('policy_pcyDateE') + u'\n'
                                if item.get('policy_pcyType', None):
                                    message = message + u"Тип полиса ОМС: " + getPersonData_pcyType.get(item.get('policy_pcyType')) + u'\n'
                                if item.get('policy_pcyStatus', None):
                                    message = message + u"Статус полиса ОМС: " + getPersonData_pcyStatus.get(item.get('policy_pcyStatus'), u'') + u'\n'
                                if item.get('policy_insurfCode', None):
                                    # mo_request = u"SELECT shortName FROM Organisation WHERE smoCode = '" + forceString(item.get('policy_insurfCode')) + "' AND deleted = 0 AND isActive = 1 LIMIT 1 "
                                    # mo_query = QtGui.qApp.db.query(mo_request)
                                    # if mo_query.next():
                                    #     shortName = mo_query.record().value('shortName')
                                    #     message = message + u"СМО: " + forceString(item.get('policy_insurfCode')) + u' - ' + forceString(shortName) +u'\n'
                                    message = message + u"СМО: " + forceString(item.get('policy_insurfCode')) + ((u" - " + item.get('policy_insurfName')) if item.get('policy_insurfName', None) else u"") + u"\n"
                                if item.get('policy_okato', None):
                                    message = message + u"ОКАТО: " + item.get('policy_okato') + u'\n'
                                if item.get('policy_insurfOgrn', None):
                                    message = message + u"ОГРН СМО: " + item.get('policy_insurfOgrn') + u'\n'
                    attach = result_dict['elements'].get('attach', None)
                    if attach:
                        if len(attach)> 0:
                            for item in attach:
                                if item.get('attach_areaType', None):
                                    message = message + u'Профиль прикрепления: ' + getPersonData_areaType.get(forceString(item.get('attach_areaType'))) + u'\n'
                                if item.get('attach_attachMethod', None):
                                    message = message + u'Способ прикрепления: ' + getPersonData_attachMethod.get(forceString(item.get('attach_attachMethod'))) + u'\n'
                                if item.get('attach_dateAttachB', None):
                                    message = message + u'Дата начала прикрепления: ' + item.get('attach_dateAttachB') + u'\n'
                                if item.get('attach_dateAttachE', None):
                                    message = message + u'Дата окончания прикрепления: ' + item.get('attach_dateAttachE') + u'\n'
                                if item.get('attach_moCode', None):
                                    mo_request = u"SELECT shortName FROM Organisation WHERE smoCode = '" + forceString(item.get('attach_moCode')) + "' AND deleted = 0 AND isActive = 1 LIMIT 1 "
                                    mo_query = QtGui.qApp.db.query(mo_request)
                                    if mo_query.next():
                                        shortName = mo_query.record().value('shortName')
                                        message = message + u"МО прикрепления: " + forceString(item.get('attach_moCode')) + u' - ' + forceString(shortName) + u'\n'
                                if item.get('attach_moFId', None):
                                    message = message + u'Идентификатор филиала МО: ' + item.get('attach_moFId') + u'\n'
                                if item.get('attach_moOkato', None):
                                    message = message + u'ОКАТО территории медицинской организации: ' + item.get('attach_moOkato') + u'\n'
                                if item.get('attach_attachStatus', None):
                                    message = message + u'Статус прикрепления: ' + getPersonData_attachStatus.get(item.get('attach_attachStatus'), u'') + u'\n'
                                # if item.get('attach_depId', None):
                                #     message = message + u'Код структурного подразделения МО: ' + item.get('attach_depId') + u'\n'
                if u'errors' in main_tag.keys():
                    isError = True
                    errors = main_tag['errors']
                    if isinstance(errors['errorItem'], dict):
                        error_message = forceString(errors['errorItem'].get('message', None))
                        error_code = forceString(errors['errorItem'].get('code', None))
                        error_tag = forceString(errors['errorItem'].get('tag', None))
                        error_value = forceString(errors['errorItem'].get('value', None))
                        message = message + u'Ошибка: ' + error_message + u"\n"
                        message = message + u'Код ошибки: ' + error_code + u"\n"
                        if error_tag:
                            message = message + u'tag ошибки: ' + error_tag + u"\n"
                        if error_value:
                            message = message + u'value ошибки: ' + error_value + u"\n"
                    elif isinstance(errors['errorItem'], list):
                        counter = 0
                        for elem in errors['errorItem']:
                            error_message = forceString(elem.get('message', None))
                            error_code = forceString(elem.get('code', None))
                            error_tag = forceString(elem.get('tag', None))
                            error_value = forceString(elem.get('value', None))
                            counter+=1
                            message = message + u'------------- Ошибка ' + forceString(counter) + u' ------------- '
                            message = message + u'Ошибка: ' + error_message + u"\n"
                            message = message + u'Код ошибки: ' + error_code + u"\n"
                            if error_tag:
                                message = message + u'tag ошибки: ' + error_tag + u"\n"
                            if error_value:
                                message = message + u'value ошибки: ' + error_value + u"\n"
            else:
                if u'Fault' in jsonRequest['Envelope']['Body'].keys():           
                    isError = True
                    fault = jsonRequest['Envelope']['Body']['Fault']
                    faultcode = fault.get('faultcode', None)
                    faultstring = fault.get('faultstring', None)
                    detail =  fault.get('detail', None)
                    if faultcode:
                        message = message + u'faultcode: ' + faultcode + u"\n"
                    if faultstring:
                        message = message + u'faultstring: ' + faultstring + u"\n"
                    if detail:
                        validationRequestBodyFault = detail.get('ValidationRequestBodyFault', None)
                        validationTypeError = detail.get('ValidationTypeError', None)
                        if validationRequestBodyFault:
                            errors = validationRequestBodyFault.get('errors', None)
                            if errors:
                                if isinstance(errors['errorItem'], dict):
                                    error_message = forceString(errors['errorItem'].get('message', None))
                                    error_code = forceString(errors['errorItem'].get('code', None))
                                    error_tag = forceString(errors['errorItem'].get('tag', None))
                                    error_value = forceString(errors['errorItem'].get('value', None))
                                    message = message + u'Ошибка: ' + error_message + u"\n"
                                    message = message + u'Код ошибки: ' + error_code + u"\n"
                                    if error_tag:
                                        message = message + u'tag ошибки: ' + error_tag + u"\n"
                                    if error_value:
                                        message = message + u'value ошибки: ' + error_value + u"\n"
                                elif isinstance(errors['errorItem'], list):
                                    counter = 0
                                    for elem in errors['errorItem']:
                                        error_message = forceString(elem.get('message', None))
                                        error_code = forceString(elem.get('code', None))
                                        error_tag = forceString(elem.get('tag', None))
                                        error_value = forceString(elem.get('value', None))
                                        counter += 1
                                        message = message + u'------------- Ошибка ' + forceString(counter) + u' ------------- '
                                        message = message + u'Ошибка: ' + error_message + u"\n"
                                        message = message + u'Код ошибки: ' + error_code + u"\n"
                                        if error_tag:
                                            message = message + u'tag ошибки: ' + error_tag + u"\n"
                                        if error_value:
                                            message = message + u'value ошибки: ' + error_value + u"\n"
                        if validationTypeError:
                            if isinstance(validationTypeError, list):
                                for elem in validationTypeError:
                                    message = message + u'ValidationTypeError: ' + forceString(elem) + u'\n'

            dialog = self.showMessageBox(message, buttonName=buttonName, isError=isError)
            if dialog == QtGui.QMessageBox.Ok:
                return result_dict
            else:
                return {'result': False, 'elements': None}



    def generateURLParams(self, params):
        return forceString("&").join(forceString("{}={}").format(k,forceString(v)) for k, v in params.items() if v)


    def findNRs(self, params_dict = {}):
        params = {
            "external_id": forceString(params_dict.get('external_id')),
            'pagination_pageNumber': forceString(params_dict.get('pageNumber', None)),
            'pagination_itemPerPage': forceString(params_dict.get('itemPerPage', None)),
            'NR_oip': forceString(params_dict.get('oip', None)),
            'NR_surnameEstim': forceString(params_dict.get('surnameEstim', None)),
            'NR_gender': forceString(params_dict.get('gender', None)),
            'NR_birthdaySince': forceString(params_dict.get('birthdaySince', None)),
            'NR_birthdayTill': forceString(params_dict.get('birthdayTill', None)),
            'NR_deathdaySince': forceString(params_dict.get('deathdaySince', None)),
            'NR_deathdayTill': forceString(params_dict.get('deathdayTill', None)),
            'MOInfo_moId': forceString(params_dict.get('moId', None)),
            'MOInfo_moCode': forceString(params_dict.get('moCode', None)),
            'NRDocs_docType_type': forceString(params_dict.get('NRDocs_docType_type', None)),
            'NRDocs_docType_spr': forceString(params_dict.get('NRDocs_docType_spr', None)),
            'NRDocs_idSemd': forceString(params_dict.get('idSemd', None)),
            'NRDocs_docNR_docSer': forceString(params_dict.get('docSer', None)),
            'NRDocs_docNR_docNum': forceString(params_dict.get('docNum', None)),
            'legalPerson_oip': forceString(params_dict.get('legalPerson_oip', None)),
            'legalPerson_enp': forceString(params_dict.get('legalPerson_enp', None)),
        }
        isError = False
        url = forceString(self.url+'/oms/services/MpiNr/findNR') + forceString('?') + forceString(self.generateURLParams(params))
        resp = requests.get(url=url, params=params)
        if resp.status_code != 200:
            message = u'Ошибка сервисов. Код ошибки: ' + forceString(resp.status_code) + u' - ' + forceString(
                resp.reason)+u'. findNR'
            msgbx = self.showMessageBox(message, isError=True)
            if msgbx == QtGui.QMessageBox.Cancel:
                return None
        if resp:

            jsonRequest = resp.json()
            message = u""
            if u'findNRsResponse' in jsonRequest['Envelope']['Body'].keys():
                main_tag = jsonRequest['Envelope']['Body']['findNRsResponse']
                if u'NR' in main_tag.keys():

                    nr = main_tag['NR']
                    list_nrs = []
                    if isinstance(nr, list):
                        for item in nr:
                            result_dict_nr = {
                                'gender': None,
                                'legalPerson': None,
                                'surnameEstim': None,
                                'deathday': None,
                                'birthday': None,
                                'oip': None
                            }
                            if u'gender' in item.keys():
                                result_dict_nr['gender'] = item['gender']
                            if u'legalPerson' in item.keys():
                                result_dict_nr['legalPerson'] = item['legalPerson']
                            if u'surnameEstim' in item.keys():
                                result_dict_nr['surnameEstim'] = item['surnameEstim']
                            if u'birthday' in item.keys():
                                birthday = datetime.strptime(item['birthday'], '%Y-%m-%d')
                                birthday = birthday.date().strftime('%d.%m.%Y')
                                result_dict_nr['birthday'] = birthday
                            if u'oip' in item.keys():
                                result_dict_nr['oip'] = item['oip']
                            if u'deathday' in item.keys():
                                deathday = datetime.strptime(item['deathday'], '%Y-%m-%d')
                                deathday = deathday.date().strftime('%d.%m.%Y')
                                result_dict_nr['deathday'] = deathday
                            list_nrs.append(result_dict_nr)
                    elif isinstance(nr, dict):
                        result_dict_nr = {
                            'gender': None,
                            'legalPerson': None,
                            'surnameEstim': None,
                            'deathday': None,
                            'birthday': None,
                            'oip': None
                        }
                        if u'gender' in nr.keys():
                            result_dict_nr['gender'] = nr['gender']
                        if u'legalPerson' in nr.keys():
                            result_dict_nr['legalPerson'] = nr['legalPerson']
                        if u'surnameEstim' in nr.keys():
                            result_dict_nr['surnameEstim'] = nr['surnameEstim']
                        if u'birthday' in nr.keys():
                            birthday = datetime.strptime(nr['birthday'], '%Y-%m-%d')
                            birthday = birthday.date().strftime('%d.%m.%Y')
                            result_dict_nr['birthday'] = birthday
                        if u'oip' in nr.keys():
                            result_dict_nr['oip'] = nr['oip']
                        if u'deathday' in nr.keys():
                            deathday = datetime.strptime(nr['deathday'], '%Y-%m-%d')
                            deathday = deathday.date().strftime('%d.%m.%Y')
                            result_dict_nr['deathday'] = deathday
                        list_nrs.append(result_dict_nr)

                    if len(list_nrs)>0:

                        return self.showListNrView(list_nrs, params.get('external_id', None))
                    else:
                        isError = True
                        dialog = self.showMessageBox(u'Ничего не найдено', isError=isError) # Возможно это не нужно, но черт его знает 
                        return None

                if u'errors' in main_tag.keys():
                    errors = main_tag['errors']
                    isError = True
                    if isinstance(errors['errorItem'], dict):
                        error_message = forceString(errors['errorItem'].get('message', None))
                        error_code = forceString(errors['errorItem'].get('code', None))
                        error_tag = forceString(errors['errorItem'].get('tag', None))
                        error_value = forceString(errors['errorItem'].get('value', None))
                        message = message + u'Ошибка: ' + error_message + u"\n"
                        message = message + u'Код ошибки: ' + error_code + u"\n"
                        if error_tag:
                            message = message + u'tag ошибки: ' + error_tag + u"\n"
                        if error_value:
                            message = message + u'value ошибки: ' + error_value + u"\n"
                    elif isinstance(errors['errorItem'], list):
                        counter = 0
                        for elem in errors['errorItem']:
                            error_message = forceString(elem.get('message', None))
                            error_code = forceString(elem.get('code', None))
                            error_tag = forceString(elem.get('tag', None))
                            error_value = forceString(elem.get('value', None))
                            counter += 1
                            message = message + u'------------- Ошибка ' + forceString(counter) + u' ------------- '
                            message = message + u'Ошибка: ' + error_message + u"\n"
                            message = message + u'Код ошибки: ' + error_code + u"\n"
                            if error_tag:
                                message = message + u'tag ошибки: ' + error_tag + u"\n"
                            if error_value:
                                message = message + u'value ошибки: ' + error_value + u"\n"


                    return self.showMessageBox(message, isError=isError)
            else:
                if u'Fault' in jsonRequest['Envelope']['Body'].keys():
                    isError = True
                    fault = jsonRequest['Envelope']['Body']['Fault']
                    faultcode = fault.get('faultcode', None)
                    faultstring = fault.get('faultstring', None)
                    detail = fault.get('detail', None)
                    if faultcode:
                        message = message + u'faultcode: ' + faultcode + u"\n"
                    if faultstring:
                        message = message + u'faultstring: ' + faultstring + u"\n"
                    if detail:
                        validationRequestBodyFault = detail.get('ValidationRequestBodyFault', None)
                        validationTypeError = detail.get('ValidationTypeError', None)
                        if validationRequestBodyFault:
                            errors = validationRequestBodyFault.get('errors', None)
                            if errors:
                                if isinstance(errors['errorItem'], dict):
                                    error_message = forceString(errors['errorItem'].get('message', None))
                                    error_code = forceString(errors['errorItem'].get('code', None))
                                    error_tag = forceString(errors['errorItem'].get('tag', None))
                                    error_value = forceString(errors['errorItem'].get('value', None))
                                    message = message + u'Ошибка: ' + error_message + u"\n"
                                    message = message + u'Код ошибки: ' + error_code + u"\n"
                                    if error_tag:
                                        message = message + u'tag ошибки: ' + error_tag + u"\n"
                                    if error_value:
                                        message = message + u'value ошибки: ' + error_value + u"\n"
                                elif isinstance(errors['errorItem'], list):
                                    counter = 0
                                    for elem in errors['errorItem']:
                                        error_message = forceString(elem.get('message', None))
                                        error_code = forceString(elem.get('code', None))
                                        error_tag = forceString(elem.get('tag', None))
                                        error_value = forceString(elem.get('value', None))
                                        counter += 1
                                        message = message + u'------------- Ошибка ' + forceString(
                                            counter) + u' ------------- '
                                        message = message + u'Ошибка: ' + error_message + u"\n"
                                        message = message + u'Код ошибки: ' + error_code + u"\n"
                                        if error_tag:
                                            message = message + u'tag ошибки: ' + error_tag + u"\n"
                                        if error_value:
                                            message = message + u'value ошибки: ' + error_value + u"\n"
                        if validationTypeError:
                            if isinstance(validationTypeError, list):
                                for elem in validationTypeError:
                                    message = message + u'ValidationTypeError: ' + forceString(elem) + u'\n'

                return self.showMessageBox(message, isError=isError)


    def showListNrView(self, list_nr, external_id=None):
        dialog = QDialog()
        dialog.setWindowTitle(u'Выбор новорожденного')
        # dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        # model = PyQt4.Qt.QStandardItemModel()

        # model.setHorizontalHeaderLabels([u'Фамилия', u'Пол', u'Дата рождения', u'ОИП', u'ЕНП/ОИП матери'])
        data = []
        for row_data in list_nr:
            gender = row_data.get('gender', None)
            if gender:
                if int(gender) == 1:
                    gender = u'М'
                if int(gender) == 2:
                    gender = u'Ж'
            oip = forceString(row_data.get('oip', None))
            surnameEstim = forceString(row_data.get('surnameEstim', None))
            birthday = forceString(row_data.get('birthday', None))
            deathday = forceString(row_data.get('deathday', None))
            legalPerson = row_data.get('legalPerson', None)
            legalPersonString = u''
            if legalPerson:
                legalPersonString = forceString(legalPerson.get('enp'))
            # items = [PyQt4.Qt.QStandardItem(surnameEstim), PyQt4.Qt.QStandardItem(gender), PyQt4.Qt.QStandardItem(birthday),
            #          PyQt4.Qt.QStandardItem(oip), PyQt4.Qt.QStandardItem(legalPersonString)]
            items = [surnameEstim, gender,birthday,deathday, oip,legalPersonString]
            # model.appendRow(items)
            data.append(items)
        table_view = QtGui.QTableView()
        model = CustomTableModel(data)
        table_view.setModel(model)
        table_view.setSelectionBehavior(QtGui.QTableView.SelectRows)

        table_view.setColumnWidth(0, 120)
        table_view.setColumnWidth(1, 30)
        table_view.setColumnWidth(2, 100)
        table_view.setColumnWidth(3, 140)
        table_view.setColumnWidth(4, 150)
        table_view.verticalHeader().hide()
        table_view.verticalHeader().setDefaultSectionSize(20)

        header = table_view.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(model.columnCount()-1):
            header.setResizeMode(i, QtGui.QHeaderView.Interactive)
        header.setResizeMode(4, QtGui.QHeaderView.Stretch)
        idx_row = None
        result = {}
        buttonBox_layout = QtGui.QGridLayout()
        buttonBox_layout.addWidget(QtGui.QLabel(u''), 0, 1, 1, 3)
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.rejected.connect(dialog.reject)
        buttonBox_layout.addWidget(buttonBox, 0, 4)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(table_view)
        layout.addLayout(buttonBox_layout)

        if table_view.model().rowCount() > 0:
            table_view.selectRow(0)
            idx_row = table_view.currentIndex()
        dialog.resize(650, 300)
        dialog.setLayout(layout)
        def on_tv_clicked(parent, table_view=table_view, idx_row=idx_row):
            # if isinstance(parent, PyQt4.QtCore.QModelIndex):
            if parent.isValid():
                table_view.setCurrentIndex(parent)
                table_view.selectionModel().select(parent, QtGui.QItemSelectionModel.Select | QtGui.QItemSelectionModel.Rows)
                idx_row = parent

        def on_btnOk_clicked(parent=None, table_view=table_view, dialog=dialog, result=result):
            idx_row = table_view.currentIndex()
            taken_row = table_view.model().takeRow(idx_row.row())
            oip = None
            oip_column_index = None
            for item in range(len(table_view.model()._headers)):
                if table_view.model()._headers[item] == u'ОИП':
                    # oip = taken_row[item]
                    oip_column_index = item
                    break
            if oip_column_index:
                oip = table_view.model().getHiddenData(idx_row.row(), oip_column_index)
            param = {
                "external_id": forceString(external_id),
                "oip": forceString(oip) if oip else None
            }

            result.update(self.getNrData(param))
            if result.get('result', None):

                dialog.accept()
                return result

        buttonBox.accepted.connect(on_btnOk_clicked)
        table_view.doubleClicked.connect(on_btnOk_clicked)
        table_view.clicked.connect(on_tv_clicked)
        if dialog.exec_():
            return result


    def showMessageBox(self, message, buttonName = None, isError=False, title=u'Данные персоны, полученные из ФЕРЗЛ'):
        msgbox = QtGui.QMessageBox()
        msgbox.setIcon(QtGui.QMessageBox.Information)
        msgbox.setWindowFlags(msgbox.windowFlags() | Qt.WindowStaysOnTopHint)
        msgbox.setWindowTitle(title)
        msgbox.setText(message)
        btn_cancel = msgbox.addButton(QtGui.QMessageBox.Cancel)
        if not isError:
            btn_ok = msgbox.addButton(QtGui.QMessageBox.Ok)
            if buttonName:
                btn_ok.setText(buttonName)
        else:
            btn_cancel.setText(u"ОК")
        return msgbox.exec_()


    def getNrData(self, params_dict = {}):
        params = {
            "external_id": forceString(params_dict.get('external_id')),
            "type": forceString(params_dict.get('type', None)),
            "spr": u'ЭМД' if params_dict.get('type', None) else None,
            "idSemd": forceString(params_dict.get('idSemd', None)),
            "docSer": forceString(params_dict.get('docSer', None)),
            "docNum": forceString(params_dict.get('docNum', None)),
            "oip": forceString(params_dict.get('oip', None))

        }
        isError = False
        buttonName = None
        result_dict = {
            'result': False,
            'elements': {}
        }
        url = forceString(self.url + '/oms/services/MpiNr/getNRData' + forceString('?')+ forceString(self.generateURLParams(params)))
        resp = requests.get(url=url, params=params)
        if resp.status_code != 200:
            message = u'Ошибка сервисов. Код ошибки: ' + forceString(resp.status_code) + u' - ' + forceString(
                resp.reason)+u'. getNRData'
            msgbx = self.showMessageBox(message, isError=True)
            if msgbx == QtGui.QMessageBox.Cancel:
                return None
        if resp:
            jsonRequest = resp.json()
            message = u""
            if u'getNRDataResponse' in jsonRequest['Envelope']['Body'].keys():
                main_tag = jsonRequest['Envelope']['Body']['getNRDataResponse']
                if u'NR' in main_tag.keys():
                    nr = main_tag['NR']
                    result_dict['result'] = True
                    moOkato, moCode, moId, oip, docs, surnameEstim, gender, nbHeight,  birthday, legalPerson, moIdBirth, \
birthOutcome, nbWeight, pregnancyRate, seqTotal, seqNum, seqTotalNum, moName, nbLoc, nbPerformer, deathday = None, None, \
None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
                    if u'moOkato' in nr.keys():
                        moOkato = forceString(nr.get('moOkato', None))
                    if moOkato:
                        result_dict['elements']['moOkato'] = moOkato
                    if u'moCode' in nr.keys():
                        moCode = forceString(nr.get('moCode', None))
                    if moCode:
                        result_dict['elements']['moCode'] = moCode
                    if u'moId' in nr.keys():
                        moId = forceString(nr.get('moId', None))
                    if moId:
                        result_dict['elements']['moId'] = moId
                    if u'oip' in nr.keys():
                        oip = forceString(nr.get('oip', None))
                    if oip:
                        result_dict['elements']['oip'] = oip
                    if u'docs' in nr.keys():
                        docs = nr.get('docs', None)
                        if docs:
                            docs_list = []
                            if isinstance(docs, dict):
                                for item in docs:
                                    doc_dict = {}
                                    docSer, docNum, semdID, type, spr = None, None, None, None, None
                                    if u'docSer' in docs[item].keys():
                                        docSer = forceString(docs[item].get('docSer', None))
                                    if docSer:
                                        doc_dict['docSer'] = docSer
                                    if u'docNum' in docs[item].keys():
                                        docNum = forceString(docs[item].get('docNum', None))
                                    if docNum:
                                        doc_dict['docNum'] = docNum
                                    if u'semdID' in docs[item].keys():
                                        semdID = forceString(docs[item].get('semdID', None))
                                    if semdID:
                                        doc_dict['semdID'] = semdID
                                    if u'docType' in docs[item].keys():
                                        type = forceString(docs[item]['docType'].get('type', None))
                                        spr = forceString(docs[item]['docType'].get('spr', None))
                                    if type:
                                        doc_dict['type'] = type
                                    if spr:
                                        doc_dict['spr'] = spr
                                    docs_list.append(doc_dict)
                            if isinstance(docs, list):
                                for item in docs:
                                    doc_dict = {}
                                    docSer, docNum, semdID, type, spr = None, None, None, None, None
                                    if u'docSer' in item.keys():
                                        docSer = forceString(item.get('docSer', None))
                                    if docSer:
                                        doc_dict['docSer'] = docSer
                                    if u'docNum' in docs[item].keys():
                                        docNum = forceString(item.get('docNum', None))
                                    if docNum:
                                        doc_dict['docNum'] = docNum
                                    if u'semdID' in item.keys():
                                        semdID = forceString(item.get('semdID', None))
                                    if semdID:
                                        doc_dict['semdID'] = semdID
                                    if u'docType' in docs[item].keys():
                                        type = forceString(item['docType'].get('type', None))
                                        spr = forceString(item['docType'].get('spr', None))
                                    if type:
                                        doc_dict['type'] = type
                                    if spr:
                                        doc_dict['spr'] = spr
                                    docs_list.append(doc_dict)
                            result_dict['elements']['docs'] = docs_list if len(doc_dict) > 0 else None
                    if u'surnameEstim' in nr.keys():
                        surnameEstim = forceString(nr.get('surnameEstim', None))
                    if surnameEstim:
                        result_dict['elements']['surnameEstim'] = surnameEstim
                    if u'gender' in nr.keys():
                        gender = forceInt(nr.get('gender', None))
                        result_dict['elements']['gender'] = gender
                    if u'birthday' in nr.keys():
                        birthday = nr.get('birthday', None)
                    if birthday:
                        birthday = datetime.strptime(birthday, '%Y-%m-%d')
                        birthday = forceString(birthday.date().strftime('%d.%m.%Y'))
                        result_dict['elements']['birthday'] = birthday
                    if u'deathday' in nr.keys():
                        deathday = nr.get('deathday', None)
                    if deathday:
                        deathday = datetime.strptime(deathday, '%Y-%m-%d')
                        deathday = forceString(deathday.date().strftime('%d.%m.%Y'))
                        result_dict['elements']['deathday'] = deathday
                    if u'birthOutcome' in nr.keys():
                        birthOutcome = forceString(nr.get('birthOutcome', None))
                    if birthOutcome:
                        result_dict['elements']['birthOutcome'] = birthOutcome
                    if u'nbWeight' in nr.keys():
                        nbWeight = forceString(nr.get('nbWeight', None))
                    if nbWeight:
                        result_dict['elements']['nbWeight'] = nbWeight
                    if u'nbHeight' in nr.keys():
                        nbHeight = forceString(nr.get('nbHeight', None))
                    if nbHeight:
                        result_dict['elements']['nbHeight'] = nbHeight
                    if u'pregnancyRate' in nr.keys():
                        pregnancyRate  = nr.get('pregnancyRate', None)
                    if pregnancyRate:
                        result_dict['elements']['pregnancyRate'] = pregnancyRate
                    if u'seqTotal' in nr.keys():
                        seqTotal  = forceString(nr.get('seqTotal', None))
                    if seqTotal:
                        result_dict['elements']['seqTotal'] = seqTotal
                    if u'seqNum' in nr.keys():
                        seqNum = forceString(nr.get('seqNum', None))
                    if seqNum:
                        result_dict['elements']['seqNum'] = seqNum
                    if u'seqTotalNum' in nr.keys():
                        seqTotalNum = forceString(nr.get('seqTotalNum', None))
                    if seqTotalNum:
                        result_dict['elements']['seqTotalNum'] = seqTotalNum
                    if u'moIdBirth' in nr.keys():
                        moIdBirth = forceString(nr.get('moIdBirth', None))
                    if moIdBirth:
                        result_dict['elements']['moIdBirth'] = moIdBirth
                    if u'moName' in nr.keys():
                        moName = forceString(nr.get('moName', None))
                    if moName:
                        result_dict['elements']['moName'] = moName
                    if u'nbLoc' in nr.keys():
                        nbLoc = nr.get('nbLoc', None)
                    if nbLoc:
                        result_dict['elements']['nbLoc'] = nbLoc
                    if u'nbPerformer' in nr.keys():
                        nbPerformer = nr.get('nbPerformer', None)
                    if nbPerformer:
                        result_dict['elements']['nbPerformer'] = nbPerformer
                    if u'legalPerson' in nr.keys():
                        legalPerson = nr.get('legalPerson', None)
                        legalPerson_oip, enp, surname, firstName, patronymic, birthDate, \
                        legalPerson_gender = None, None, None, None, None, None, None
                        if legalPerson:
                            legalPerson_dict = {}
                            legalPerson_oip = forceString(legalPerson.get('oip', None))
                            if legalPerson_oip:
                                legalPerson_dict['oip'] = legalPerson_oip
                            enp = forceString(legalPerson.get('enp', None))
                            if enp:
                                legalPerson_dict['enp'] = enp
                            surname = legalPerson.get('surname', None)
                            if surname:
                                legalPerson_dict['surname'] = surname
                            firstName = legalPerson.get('firstName', None)
                            if firstName:
                                legalPerson_dict['firstName'] = firstName
                            patronymic = legalPerson.get('patronymic', None)
                            if patronymic:
                                legalPerson_dict['patronymic'] = patronymic

                            birthDate = legalPerson.get('birthDate', None)
                            if birthDate:
                                birthDate = datetime.strptime(birthDate, '%Y-%m-%d')
                                birthDate = forceString(birthDate.date().strftime('%d.%m.%Y'))
                                legalPerson_dict['birthDate'] = birthDate
                            legalPerson_gender = forceInt(legalPerson.get('gender', None))
                            if legalPerson_gender:
                                legalPerson_dict['gender'] = legalPerson_gender
                            result_dict['elements']['legalPerson'] = legalPerson_dict
                    if result_dict['elements'].get('surnameEstim', None):
                        message = message + u"Фамилия НР: " + result_dict['elements'].get('surnameEstim') + u"\n"
                    if result_dict['elements'].get('gender', None):
                        message = message + u"Пол: " + getNrData_gender.get(str(result_dict['elements'].get('gender'))) + u"\n"
                    if result_dict['elements'].get('birthday', None):
                        message = message + u"Дата рождения: " + result_dict['elements'].get('birthday') + u"\n"
                    if result_dict['elements'].get('deathday', None):
                        message = message + u"Дата смерти: " + result_dict['elements'].get('deathday') + u"\n"
                    if result_dict['elements'].get('moOkato', None):
                        region_request = u"SELECT name FROM rbRegion where okato_5 = " + forceString(result_dict['elements'].get('moOkato'))
                        region_query = QtGui.qApp.db.query(region_request)
                        if region_query.next():
                            region_name = forceString(region_query.record().value('name'))
                            message = message + u"Регион рождения: " + region_name + u"\n"
                    if result_dict['elements'].get('moCode', None):
                        # moBirth_request = u"SELECT shortName FROM Organisation WHERE smoCode = '" + forceString(result_dict['elements'].get('moCode')) +"' AND deleted = 0 AND isActive = 1 LIMIT 1 "
                        # moBirth_query = QtGui.qApp.db.query(moBirth_request)
                        # if moBirth_query.next():
                        #     moShortName = forceString(moBirth_query.record().value('shortName'))
                        #     message = message + u"МО рождения: " + forceString(result_dict['elements'].get('moCode')) + u' - ' + moShortName +  u"\n"
                        message = message + u"МО рождения: " + forceString(result_dict['elements'].get('moCode')) + ((u" - " + forceString(result_dict['elements'].get('moName'))) if result_dict['elements'].get('moName', None) else u"") + u"\n"

                    if result_dict['elements'].get('docs', None):
                        for doc in result_dict['elements'].get('docs'):
                            if doc.get('type', None) or doc.get('spr', None):
                                message = message + u"Тип документа: " + getNrData_docType_dict.get(doc.get('type')) + u"\n"
                            if doc.get('docSer', None):
                                message = message + u"Серия документа: " + doc.get('docSer') + u"\n"
                            if doc.get('docNum', None):
                                message = message + u"Номер документа: " + doc.get('docNum') + u"\n\n"
                    if result_dict['elements'].get('birthOutcome', None):
                        message = message + u"Исход родов: " + getNrData_birthOutcome.get(str(result_dict['elements'].get('birthOutcome'))) + u"\n"
                    if result_dict['elements'].get('nbWeight', None):
                        message = message + u"Вес при рождении (в граммах): " + result_dict['elements'].get('nbWeight') + u"\n"
                    if result_dict['elements'].get('nbHeight', None):
                        message = message + u"Рост при рождении (в сантиметрах): " + result_dict['elements'].get('nbHeight') + u"\n"

                    if result_dict['elements'].get('pregnancyRate', None):
                        message = message + u"Многоплодные роды: " + forceString(getNrData_pregnancyRate_dict.get(result_dict['elements'].get('pregnancyRate'))) + u"\n"
                    if result_dict['elements'].get('seqTotal', None):
                        message = message + u"Число родившихся детей: " + result_dict['elements'].get('seqTotal') + u"\n"
                    if result_dict['elements'].get('seqNum', None):
                        message = message + u"Номер при рождении: " + result_dict['elements'].get('seqNum') + u"\n"
                    if result_dict['elements'].get('seqTotalNum', None):
                        message = message + u"Роды по счету: " + result_dict['elements'].get('seqTotalNum') + u"\n"
                    if result_dict['elements'].get('nbLoc', None) and result_dict['elements'].get('nbLoc', None) != u'4':
                        message = message + u"Место рождения: " + getNrData_nbLoc.get(result_dict['elements'].get('nbLoc')) + u"\n"
                    if result_dict['elements'].get('nbPerformer', None):
                        message = message + u"Лицо, принимавшее роды: " + getNrData_nbPerformer.get(result_dict['elements'].get('nbPerformer')) + u"\n"
                    if result_dict['elements'].get('legalPerson', None):
                        message = message + u"\n\nИнформация о неподтвержденном законном представителе (матери):" + u"\n"
                        if result_dict['elements']['legalPerson'].get('surname', None):
                            message = message + u"Фамилия: " + result_dict['elements']['legalPerson'].get('surname') + u"\n"
                        if result_dict['elements']['legalPerson'].get('firstName', None):
                            message = message + u"Имя: " + result_dict['elements']['legalPerson'].get('firstName') + u"\n"
                        if result_dict['elements']['legalPerson'].get('patronymic', None):
                            message = message + u"Отчество: " + result_dict['elements']['legalPerson'].get('patronymic') + u"\n"
                        if result_dict['elements']['legalPerson'].get('birthDate', None):
                            message = message + u"Дата рождения: " + result_dict['elements']['legalPerson'].get('birthDate') + u"\n"
                        if result_dict['elements']['legalPerson'].get('gender', None):
                            message = message + u"Пол: " + getNrData_gender.get(str(result_dict['elements']['legalPerson'].get('gender'))) + u"\n"
                        if result_dict['elements']['legalPerson'].get('enp', None):
                            message = message + u"ЕНП: " + result_dict['elements']['legalPerson'].get('enp') + u"\n"


                    buttonName = u"Обновить данные пациента"
                    dialog = self.showMessageBox(message, buttonName=buttonName, isError=isError)
                    if dialog == QtGui.QMessageBox.Ok:
                        return result_dict
                    else:
                        return {'result': False, 'elements':None}
                # Errors
                if u'errors' in main_tag.keys():
                    isError = True
                    errors = main_tag['errors']
                    if isinstance(errors['errorItem'], dict):
                        error_message = forceString(errors['errorItem'].get('message', None))
                        error_code = forceString(errors['errorItem'].get('code', None))
                        error_tag = forceString(errors['errorItem'].get('tag', None))
                        error_value = forceString(errors['errorItem'].get('value', None))
                        message = message + u'Ошибка: ' + error_message + u"\n"
                        message = message + u'Код ошибки: ' + error_code + u"\n"
                        if error_tag:
                            message = message + u'tag ошибки: ' + error_tag + u"\n"
                        if error_value:
                            message = message + u'value ошибки: ' + error_value + u"\n"
                    elif isinstance(errors['errorItem'], list):
                        counter = 0
                        for elem in errors['errorItem']:
                            error_message = forceString(elem.get('message', None))
                            error_code = forceString(elem.get('code', None))
                            error_tag = forceString(elem.get('tag', None))
                            error_value = forceString(elem.get('value', None))
                            counter += 1
                            message = message + u'------------- Ошибка ' + forceString(counter) + u' ------------- '
                            message = message + u'Ошибка: ' + error_message + u"\n"
                            message = message + u'Код ошибки: ' + error_code + u"\n"
                            if error_tag:
                                message = message + u'tag ошибки: ' + error_tag + u"\n"
                            if error_value:
                                message = message + u'value ошибки: ' + error_value + u"\n"
                    dialog = self.showMessageBox(message, isError=isError)
                    return result_dict
            else:
                if u'Fault' in jsonRequest['Envelope']['Body'].keys():
                    isError = True
                    fault = jsonRequest['Envelope']['Body']['Fault']
                    faultcode = fault.get('faultcode', None)
                    faultstring = fault.get('faultstring', None)
                    detail = fault.get('detail', None)
                    if faultcode:
                        message = message + u'faultcode: ' + faultcode + u"\n"
                    if faultstring:
                        message = message + u'faultstring: ' + faultstring + u"\n"
                    if detail:
                        validationRequestBodyFault = detail.get('ValidationRequestBodyFault', None)
                        validationTypeError = detail.get('ValidationTypeError', None)
                        if validationRequestBodyFault:
                            errors = validationRequestBodyFault.get('errors', None)
                            if errors:
                                if isinstance(errors['errorItem'], dict):
                                    error_message = forceString(errors['errorItem'].get('message', None))
                                    error_code = forceString(errors['errorItem'].get('code', None))
                                    error_tag = forceString(errors['errorItem'].get('tag', None))
                                    error_value = forceString(errors['errorItem'].get('value', None))
                                    message = message + u'Ошибка: ' + error_message + u"\n"
                                    message = message + u'Код ошибки: ' + error_code + u"\n"
                                    if error_tag:
                                        message = message + u'tag ошибки: ' + error_tag + u"\n"
                                    if error_value:
                                        message = message + u'value ошибки: ' + error_value + u"\n"
                                elif isinstance(errors['errorItem'], list):
                                    counter = 0
                                    for elem in errors['errorItem']:
                                        error_message = forceString(elem.get('message', None))
                                        error_code = forceString(elem.get('code', None))
                                        error_tag = forceString(elem.get('tag', None))
                                        error_value = forceString(elem.get('value', None))
                                        counter += 1
                                        message = message + u'------------- Ошибка ' + forceString(
                                            counter) + u' ------------- '
                                        message = message + u'Ошибка: ' + error_message + u"\n"
                                        message = message + u'Код ошибки: ' + error_code + u"\n"
                                        if error_tag:
                                            message = message + u'tag ошибки: ' + error_tag + u"\n"
                                        if error_value:
                                            message = message + u'value ошибки: ' + error_value + u"\n"
                        if validationTypeError:
                            if isinstance(validationTypeError, list):
                                for elem in validationTypeError:
                                    message = message + u'ValidationTypeError: ' + forceString(elem) + u'\n'

                dialog = self.showMessageBox(message, isError=isError)

                return result_dict


    def registerAttachMo(self, json_params=None):
        isError = False
        buttonName = None
        result_dict = {
            'result': False,
            'elements': {}
        }
        if isinstance(json_params, dict):
            resp = requests.post(self.url + '/oms/services/AttachMoBuild', json=json.loads(json.dumps(json_params)))
            if resp.status_code != 200:
                message = u'Ошибка сервисов. Код ошибки: ' + forceString(resp.status_code) + u' - ' + forceString(resp.reason) + u'. AttachMoBuild'
                msgbx = self.showMessageBox(message, isError=True, title=u'Прикрепление в ФЕРЗЛ', isSimpleButton=True)
                if msgbx == QtGui.QMessageBox.Cancel:
                    return None
            if resp:
                jsonRequest = resp.json()
                message = u""
                if u'attachMoResponse' in jsonRequest['Envelope']['Body'].keys():
                    main_tag = jsonRequest['Envelope']['Body']['attachMoResponse']
                    if u'currAttach' in main_tag.keys():
                        result_dict['result'] = True
                        return result_dict


                    if u'errors' in main_tag.keys():
                        isError = True
                        errors = main_tag['errors']
                        if isinstance(errors['errorItem'], dict):
                            error_message = forceString(errors['errorItem'].get('message', None))
                            error_code = forceString(errors['errorItem'].get('code', None))
                            error_tag = forceString(errors['errorItem'].get('tag', None))
                            error_value = forceString(errors['errorItem'].get('value', None))
                            message = message + u'Ошибка: ' + error_message + u"\n"
                            message = message + u'Код ошибки: ' + error_code + u"\n"
                            if error_tag:
                                message = message + u'tag ошибки: ' + error_tag + u"\n"
                            if error_value:
                                message = message + u'value ошибки: ' + error_value + u"\n"
                        elif isinstance(errors['errorItem'], list):
                            counter = 0
                            for elem in errors['errorItem']:
                                error_message = forceString(elem.get('message', None))
                                error_code = forceString(elem.get('code', None))
                                error_tag = forceString(elem.get('tag', None))
                                error_value = forceString(elem.get('value', None))
                                counter += 1
                                message = message + u'------------- Ошибка ' + forceString(counter) + u' ------------- '
                                message = message + u'Ошибка: ' + error_message + u"\n"
                                message = message + u'Код ошибки: ' + error_code + u"\n"
                                if error_tag:
                                    message = message + u'tag ошибки: ' + error_tag + u"\n"
                                if error_value:
                                    message = message + u'value ошибки: ' + error_value + u"\n"
                else:
                    if u'Fault' in jsonRequest['Envelope']['Body'].keys():
                        isError = True
                        fault = jsonRequest['Envelope']['Body']['Fault']
                        faultcode = fault.get('faultcode', None)
                        faultstring = fault.get('faultstring', None)
                        detail = fault.get('detail', None)
                        if faultcode:
                            message = message + u'faultcode: ' + faultcode + u"\n"
                        if faultstring:
                            message = message + u'faultstring: ' + faultstring + u"\n"
                        if detail:
                            validationRequestBodyFault = detail.get('ValidationRequestBodyFault', None)
                            validationTypeError = detail.get('ValidationTypeError', None)
                            if validationRequestBodyFault:
                                errors = validationRequestBodyFault.get('errors', None)
                                if errors:
                                    if isinstance(errors['errorItem'], dict):
                                        error_message = forceString(errors['errorItem'].get('message', None))
                                        error_code = forceString(errors['errorItem'].get('code', None))
                                        error_tag = forceString(errors['errorItem'].get('tag', None))
                                        error_value = forceString(errors['errorItem'].get('value', None))
                                        message = message + u'Ошибка: ' + error_message + u"\n"
                                        message = message + u'Код ошибки: ' + error_code + u"\n"
                                        if error_tag:
                                            message = message + u'tag ошибки: ' + error_tag + u"\n"
                                        if error_value:
                                            message = message + u'value ошибки: ' + error_value + u"\n"
                                    elif isinstance(errors['errorItem'], list):
                                        counter = 0
                                        for elem in errors['errorItem']:
                                            error_message = forceString(elem.get('message', None))
                                            error_code = forceString(elem.get('code', None))
                                            error_tag = forceString(elem.get('tag', None))
                                            error_value = forceString(elem.get('value', None))
                                            counter += 1
                                            message = message + u'------------- Ошибка ' + forceString(
                                                counter) + u' ------------- '
                                            message = message + u'Ошибка: ' + error_message + u"\n"
                                            message = message + u'Код ошибки: ' + error_code + u"\n"
                                            if error_tag:
                                                message = message + u'tag ошибки: ' + error_tag + u"\n"
                                            if error_value:
                                                message = message + u'value ошибки: ' + error_value + u"\n"
                            if validationTypeError:
                                if isinstance(validationTypeError, list):
                                    for elem in validationTypeError:
                                        message = message + u'ValidationTypeError: ' + forceString(elem) + u'\n'
                dialog = self.showMessageBox(message, buttonName=buttonName, isError=isError, title=u'Прикрепление в ФЕРЗЛ')
                if dialog == QtGui.QMessageBox.Ok:
                    return result_dict
                else:
                    return {'result': False, 'elements': None}
        else:
            return result_dict
            

    def createUpdateNil(self, clientId, eventSetDate, eventExecDate, action):
        result_dict = {'result': False, 'elements': {}}
        try:
            clientInfo = getClientInfo(clientId)
            dataJson = {}
            dataJson['data'] = {}
            prop = action.getPropertyByShortName(u'nLr')
            if prop and prop.getValue():
                dataJson['data']['nLr'] = prop.getValue()
            prop = action.getPropertyByShortName(u'smp')
            if prop and prop.getValue():
                dataJson['data']['smpCode'] = forceString(QtGui.qApp.db.translate('Organisation', 'id', prop.getValue(), 'smoCode'))
                prop = action.getPropertyByShortName(u'teamNum')
                if prop and prop.getValue():
                    dataJson['data']['teamNum'] = prop.getValue()
                prop = action.getPropertyByShortName(u'subst')
                if prop and prop.getValue():
                    dataJson['data']['subst'] = prop.getValue()
                prop = action.getPropertyByShortName(u'assignNum')
                if prop and prop.getValue():
                    dataJson['data']['assignNum'] = prop.getValue()
            dataJson['data']['whenAdmittedDate'] = str(eventSetDate.date().toString('yyyy-MM-dd'))
            dataJson['data']['whenAdmittedTime'] = str(eventSetDate.time().toString('hh:mm'))
            if eventExecDate:
                if isinstance(eventExecDate, QDateTime):
                    dataJson['data']['whenLeavedDate'] = str(eventExecDate.date().toString('yyyy-MM-dd'))
                else:
                    dataJson['data']['whenLeavedDate'] = str(eventExecDate.toString('yyyy-MM-dd'))
                if isinstance(eventExecDate, QDateTime):
                    dataJson['data']['whenLeavedTime'] = str(eventExecDate.time().toString('hh:mm'))
                else:
                    dataJson['data']['whenLeavedTime'] = '00:00'
            dataJson['data']['birthplace'] = clientInfo.birthPlace if clientInfo.birthPlace else u'Неизвестно'
            dataJson['data']['surnameEstim'] = clientInfo.lastName if clientInfo.lastName else u'Неизвестно'
            dataJson['data']['firstNameEstim'] = clientInfo.firstName if clientInfo.firstName else u'Неизвестно'
            dataJson['data']['patronymicEstim'] = clientInfo.patrName
            dataJson['data']['gender'] = clientInfo.sexCode
            if clientInfo.SNILS:
                dataJson['data']['gender'] = unformatSNILS(clientInfo.SNILS)
            for socStatusTypeId in clientInfo.socStatuses:
                if CSocStatusTypeCache.getCode(socStatusTypeId) == u'м643':
                    dataJson['data']['ctznOksm'] = 'RUS'
                    break
            else:
                dataJson['data']['noCitizenship'] = 1
            prop = action.getPropertyByShortName(u'estimAgeB')
            if prop and prop.getValue():
                dataJson['data']['estimAgeB'] = prop.getValue()
            prop = action.getPropertyByShortName(u'estimAgeE')
            if prop and prop.getValue():
                dataJson['data']['estimAgeE'] = prop.getValue()
            if not dataJson['data'].get('estimAgeB'):
                dataJson['data']['birthday'] = str(clientInfo.birthDate.toString('yyyy-MM-dd'))
            if clientInfo.deathDate:
                dataJson['data']['deathDate'] = str(clientInfo.deathDate.date().toString('yyyy-MM-dd'))
                dataJson['data']['deathTime'] = str(clientInfo.deathDate.time().toString('hh:mm'))
            prop = action.getPropertyByShortName(u'physique')
            if prop and prop.getValue():
                dataJson['data']['physique'] = createUpdateNil_physique.get(prop.getValue(), None)
            prop = action.getPropertyByShortName(u'eyecolor')
            if prop and prop.getValue():
                dataJson['data']['eyecolor'] = createUpdateNil_eyecolor.get(prop.getValue(), None)
            prop = action.getPropertyByShortName(u'hgrow')
            if prop and prop.getValue():
                dataJson['data']['hgrow'] = createUpdateNil_hgrow.get(prop.getValue(), None)
            prop = action.getPropertyByShortName(u'specFeat')
            if prop and prop.getValue():
                dataJson['data']['specFeat'] = prop.getValue()
            prop = action.getPropertyByShortName(u'persThings')
            if prop and prop.getValue():
                dataJson['data']['persThings'] = prop.getValue()
            prop = action.getPropertyByShortName(u'persDrug')
            if prop and prop.getValue():
                dataJson['data']['persDrug'] = prop.getValue()
            prop = action.getPropertyByShortName(u'persIdent')
            if prop and prop.getValue():
                dataJson['data']['persIdent'] = prop.getValue()

            servicesURL = forceString(QtGui.qApp.getGlobalPreference('23:servicesURL'))
            servicesURL = urlparse.urljoin(servicesURL, '/api/ferzl/oms/services')
            response = requests.post(servicesURL + '/NilData', json=json.loads(json.dumps(dataJson)))
            if response.status_code != 200:
                message = u'Ошибка сервисов. Код ошибки: ' + forceString(response.status_code) + u' - ' + forceString(response.reason) + u'. NilData'
                QtGui.QMessageBox.warning(None, u'НИЛ', message)
                return result_dict
            if response:
                api = MSCApi(QtGui.qApp.getCsp())
                certUser = QtGui.qApp.getUserCert(api)
                data = response.text.encode('utf-8').replace("<?xml version='1.0' encoding='utf8'?>\n", '')
                detachedSignatureBytesUser = certUser.createDetachedSignature(data)
                guid = str(uuid.uuid5(uuid.UUID(bytes='Client'.ljust(16, '\0')), repr(clientId)))
                dictForJson = {
                                'guid': guid,
                               'sign': base64.b64encode(detachedSignatureBytesUser),
                               'certificate': base64.b64encode(detachedSignatureBytesUser), 'data': data}
                response = requests.post(servicesURL + '/NilBuild', json=json.loads(json.dumps(dictForJson)))
                if response.status_code != 200:
                    message = u'Ошибка сервисов. Код ошибки: ' + forceString(response.status_code) + u' - ' + forceString(response.reason) + u'. NilBuild'
                    QtGui.QMessageBox.warning(None, u'НИЛ', message)
                    return result_dict
                jsonResponse = response.json()

                message = u""
                if 'createUpdateNilResponse' in jsonResponse['Envelope']['Body'].keys():
                    main_tag = jsonResponse['Envelope']['Body']['createUpdateNilResponse']
                    if 'nLr' in main_tag.keys():
                        result_dict['result'] = True
                        result_dict['elements']['nLr'] = main_tag['nLr']
                        result_dict['elements']['oip'] = main_tag['oip']
                        message = u"НИЛ успешно {0}!\nНомер регистрационного листа {1}".format(u'обновлен' if dataJson['data'].get('nLr') else u'создан', main_tag['nLr'])
                    if u'errors' in main_tag.keys():
                        errors = main_tag['errors']
                        if isinstance(errors['errorItem'], dict):
                            error_message = forceString(errors['errorItem'].get('message', None))
                            error_code = forceString(errors['errorItem'].get('code', None))
                            error_tag = forceString(errors['errorItem'].get('tag', None))
                            error_value = forceString(errors['errorItem'].get('value', None))
                            message = message + u'Ошибка: ' + error_message + u"\n"
                            message = message + u'Код ошибки: ' + error_code + u"\n"
                            if error_tag:
                                message = message + u'tag ошибки: ' + error_tag + u"\n"
                            if error_value:
                                message = message + u'value ошибки: ' + error_value + u"\n"
                        elif isinstance(errors['errorItem'], list):
                            counter = 0
                            for elem in errors['errorItem']:
                                error_message = forceString(elem.get('message', None))
                                error_code = forceString(elem.get('code', None))
                                error_tag = forceString(elem.get('tag', None))
                                error_value = forceString(elem.get('value', None))
                                counter += 1
                                message = message + u'------------- Ошибка ' + forceString(counter) + u' ------------- '
                                message = message + u'Ошибка: ' + error_message + u"\n"
                                message = message + u'Код ошибки: ' + error_code + u"\n"
                                if error_tag:
                                    message = message + u'tag ошибки: ' + error_tag + u"\n"
                                if error_value:
                                    message = message + u'value ошибки: ' + error_value + u"\n"
                else:
                    if u'Fault' in jsonResponse['Envelope']['Body'].keys():
                        fault = jsonResponse['Envelope']['Body']['Fault']
                        faultcode = fault.get('faultcode', None)
                        faultstring = fault.get('faultstring', None)
                        detail = fault.get('detail', None)
                        if faultcode:
                            message = message + u'faultcode: ' + faultcode + u"\n"
                        if faultstring:
                            message = message + u'faultstring: ' + faultstring + u"\n"
                        if detail:
                            validationRequestBodyFault = detail.get('ValidationRequestBodyFault', None)
                            validationTypeError = detail.get('ValidationTypeError', None)
                            if validationRequestBodyFault:
                                errors = validationRequestBodyFault.get('errors', None)
                                if errors:
                                    if isinstance(errors['errorItem'], dict):
                                        error_message = forceString(errors['errorItem'].get('message', None))
                                        error_code = forceString(errors['errorItem'].get('code', None))
                                        error_tag = forceString(errors['errorItem'].get('tag', None))
                                        error_value = forceString(errors['errorItem'].get('value', None))
                                        message = message + u'Ошибка: ' + error_message + u"\n"
                                        message = message + u'Код ошибки: ' + error_code + u"\n"
                                        if error_tag:
                                            message = message + u'tag ошибки: ' + error_tag + u"\n"
                                        if error_value:
                                            message = message + u'value ошибки: ' + error_value + u"\n"
                                    elif isinstance(errors['errorItem'], list):
                                        counter = 0
                                        for elem in errors['errorItem']:
                                            error_message = forceString(elem.get('message', None))
                                            error_code = forceString(elem.get('code', None))
                                            error_tag = forceString(elem.get('tag', None))
                                            error_value = forceString(elem.get('value', None))
                                            counter += 1
                                            message = message + u'------------- Ошибка ' + forceString(
                                                counter) + u' ------------- '
                                            message = message + u'Ошибка: ' + error_message + u"\n"
                                            message = message + u'Код ошибки: ' + error_code + u"\n"
                                            if error_tag:
                                                message = message + u'tag ошибки: ' + error_tag + u"\n"
                                            if error_value:
                                                message = message + u'value ошибки: ' + error_value + u"\n"
                            if validationTypeError:
                                if isinstance(validationTypeError, list):
                                    for elem in validationTypeError:
                                        message = message + u'ValidationTypeError: ' + forceString(elem) + u'\n'
                QtGui.QMessageBox.warning(None, u'НИЛ', message)
        except Exception, e:
            QtGui.QMessageBox().critical(None, u'Ошибка', u'Произошла ошибка: ' + unicode(e), QtGui.QMessageBox.Close)
        return result_dict


class CustomTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(CustomTableModel, self).__init__()
        self._data = data
        self._headers = [u'Фамилия НР', u'Пол', u'Дата рождения', u'Дата смерти', u'ОИП', u'ЕНП матери']
        self._visible_columns = [0,1,2,3,5]  # Изначально все столбцы видимы

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._visible_columns)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            column_index = self._visible_columns[index.column()]
            return self._data[index.row()][column_index]
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                column_index = self._visible_columns[section]
                return self._headers[column_index]
        return None

    def takeRow(self, row):
        if row < 0 or row >= len(self._data):
            return None
        row_data = self._data[row]
        return row_data

    def hideColumn(self, column):
        """Скрыть столбец по индексу."""
        if column in self._visible_columns:
            self._visible_columns.remove(column)
            self.layoutChanged.emit()  # Уведомляем представление о том, что данные изменились

    def showColumn(self, column):
        """Показать столбец по индексу."""
        if column not in self._visible_columns and 0 <= column < len(self._headers):
            self._visible_columns.append(column)
            self._visible_columns.sort()  # Сортируем индексы видимых столбцов
            self.layoutChanged.emit()  # Уведомляем представление о том, что данные изменились


    def getHiddenData(self, row, column):
        """Получить данные из скрытого столбца."""
        if column < 0 or column >= len(self._headers):
            return None  # Неверный индекс столбца
        if row < 0 or row >= len(self._data):
            return None  # Неверный индекс строки
        return self._data[row][column]  # Возвращаем данные из скрытого столбца