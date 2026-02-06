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
from PyQt4.QtCore import QDate, QDateTime

from library.ICDUtils           import MKBwithoutSubclassification
from library.Utils              import agreeNumberAndWord, firstMonthDay, forceString, formatList, formatSex, lastMonthDay
from Events.ActionStatus        import CActionStatus
from Orgs.Utils                 import getOrganisationShortName, getOrgStructureFullName, getPersonInfo, getMedicalAidProfileIdName
from Reports                    import OKVEDList
from Reports.ReportBase         import CReportBase, createTable
from Reports.Utils              import dateRangeAsStr
from Reports.ReportSetupDialog  import CReportSetupDialog
from Reports.MesDispansListDialog import getMesDispansNameList


monthsInYear = 12


class CReport(CReportBase):
    def __init__(self, parent=None):
        CReportBase.__init__(self, parent)
        self.payPeriodVisible = False
        self.workTypeVisible = False
        self.ownershipVisible = False


    def setPayPeriodVisible(self, value):
        self.payPeriodVisible = value


    def setWorkTypeVisible(self, value):
        self.workTypeVisible = value


    def setOwnershipVisible(self, value):
        self.ownershipVisible = value


    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setPayPeriodVisible(self.payPeriodVisible)
        result.setWorkTypeVisible(self.workTypeVisible)
        result.setOwnershipVisible(self.ownershipVisible)
        result.setTitle(self.title())
        return result


    def dumpParams(self, cursor, params, align=CReportBase.AlignLeft):
        description = self.getDescription(params)
        columns = [ ('100%', [], align) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getDescription(self, params):
        db = QtGui.qApp.db

        ismancheckedage = params.get('addManAgeCondition', None)
        iswomencheckedage = params.get('addWomanAgeCondition', None)

        manAgeBegType = [u'г', u'д', u'н', u'м', u'г'][params.get('manAgeBegType', 0)]
        manAgeEndType = [u'г', u'д', u'н', u'м', u'г'][params.get('manAgeEndType', 0)]
        manAgeBegValue = params.get('manAgeBegValue', 0)
        manAgeEndValue = params.get('manAgeEndValue', 0)

        womanAgeBegType = [u'г', u'д', u'н', u'м', u'г'][params.get('womanAgeBegType', 0)]
        womanAgeEndType = [u'г', u'д', u'н', u'м', u'г'][params.get('womanAgeEndType', 0)]
        womanAgeBegValue = params.get('womanAgeBegValue', 0)
        womanAgeEndValue = params.get('womanAgeEndValue', 0)

        actionDateType = params.get('actionDateType', None)
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        begTime = params.get('begTime', None)
        endTime = params.get('endTime', None)
        begDateTime = None
        endDateTime = None
        if begTime and endTime:
            begDateTime = QDateTime(begDate, begTime)
            endDateTime = QDateTime(endDate, endTime)
        byPeriod= params.get('byPeriod', None)

        useInputDate = bool(params.get('useInputDate', False))
        begInputDate = params.get('begInputDate', QDate())
        endInputDate = params.get('endInputDate', QDate())
        begDateBeforeRecord = params.get('begDateBeforeRecord', QDate())
        endDateBeforeRecord = params.get('endDateBeforeRecord', QDate())
        isPeriodOnService = params.get('isPeriodOnService', False)

        doctype = params.get('doctype', None)
        tempInvalidReason = params.get('tempInvalidReason', None)
        tempInvalidReasonIdList  = params.get('tempInvalidReasonIdList', None)
        tempInvalidReasonListText = params.get('tempInvalidReasonListText', None)
        durationFrom = params.get('durationFrom', 0)
        durationTo = params.get('durationTo', 0)
        insuranceOfficeMark = params.get('insuranceOfficeMark', 0)
        sex = params.get('sex', 0)
        typePay = params.get('typePay', None)
        actStatus = params.get('ActionStatus', None)
        ageFrom = params.get('ageFrom', None)
        ageTo = params.get('ageTo', None)
        socStatusClassId = params.get('socStatusClassId', None)
        socStatusTypeId = params.get('socStatusTypeId', None)
        contingentTypeId = params.get('contingentTypeId', None)
        osnScheta = params.get('osnScheta', None)
        without0price = params.get('without0price', None)
        areaIdEnabled = params.get('areaIdEnabled', False)
        areaId = params.get('areaId', None)
        isFilterAddressOrgStructure = params.get('isFilterAddressOrgStructure', False)
        addressOrgStructureType = params.get('addressOrgStructureType', 0)
        addressOrgStructure = params.get('addressOrgStructure', None)
        areaAddressType = params.get('areaAddressType', None)
        clientAddressType = params.get('clientAddressType', None)
        locality = params.get('locality', 0)
        onlyClosed = params.get('onlyClosed', None)
        MKBFilter = params.get('MKBFilter', 0)
        MKBFrom = params.get('MKBFrom', '')
        MKBTo = params.get('MKBTo', '')
        phaseId   = params.get('phaseId', None)
        MKBExFilter = params.get('MKBExFilter', 0)
        MKBExFrom = params.get('MKBExFrom', '')
        MKBExTo = params.get('MKBExTo', '')
        phaseIdEx   = params.get('phaseIdEx', None)
        stageId = params.get('stageId', None)

        eventPurposeId = params.get('eventPurposeId', None)
        eventTypeId = params.get('eventTypeId', None)
        eventType = params.get('eventType', None)
        eventTypeList = params.get('eventTypeList', None)
        eventResultId = params.get('eventResultId', None)
        mesDispansIdList = params.get('mesDispansIdList', None)
        visitTypeId = params.get('visitTypeId', None)
        orgStructureId = params.get('orgStructureId', None)
        setOrgStructureId = params.get('setOrgStructureId', None)
        sceneId = params.get('sceneId', None)
        isPersonPost = params.get('isPersonPost', 0)
        specialityId = params.get('specialityId', None)
        personId = params.get('personId', None)
        personIdList = params.get('personIdList', None)
        userProfileId = params.get('userProfileId', None)
        beforeRecordUserId = params.get('beforeRecordUserId', None)
        onlyPermanentAttach =  params.get('onlyPermanentAttach', False)
        onlyPayedEvents = params.get('onlyPayedEvents', None)

        characterClass = params.get('characterClass', 0)
        onlyFirstTime = params.get('onlyFirstTime', None)
        registeredInPeriod = params.get('registeredInPeriod', None)
        notNullTraumaType = params.get('notNullTraumaType', None)
        accountAccomp = params.get('accountAccomp', None)

        busyness = params.get('busyness', 0)
        currentWorkOrganisation = params.get('currentWorkOrganisation', False)
        workOrgId = params.get('workOrgId', None)
        OrgId = params.get('OrgId', None)
        rbMedicalAidProfileId = params.get('rbMedicalAidProfileId', None)
        typeFinanceId = params.get('financeId', None)
        tariff = params.get('tariff', None)
        visitPayStatus = params.get('visitPayStatus', None)
        groupingRows = params.get('groupingRows', None)
        rowGrouping = params.get('rowGrouping', None)

        insurerId = params.get('insurerId', None)
        contractId = params.get('contractId', None)
        contractIdList = params.get('contractIdList', None)
        accountIdList = params.get('accountIdList', None)

        actionTypeClass = params.get('actionTypeClass', None)
        actionTypeId = params.get('actionTypeId', None)
        actionTypeCode = params.get('queueType', None)
        actionStatus = params.get('actionStatus', None)

        permanentAttach = params.get('permanentAttach', None)

        deathPlace = params.get('deathPlace', '')
        deathCause = params.get('deathCause', '')
        deathFoundBy = params.get('deathFoundBy', '')
        deathFoundation = params.get('deathFoundation', '')

        vidPom = params.get('vidPom', None)
        naselenie = params.get('naselenie', None)
        scheta = params.get('scheta', None)
        payer = params.get('payer', None)
        dateType = params.get('dataType', None)
        onlyNotExposed = params.get('onlyNotExposed', False)
        isPrimary = params.get('isPrimary', 0)
        age1 = params.get('age1',  None)
        age2 = params.get('age2',  None)
        profileBedId = params.get('profileBed', None)
        equipmentId = params.get('equipmentId', None)
        cashPayments = params.get('cashPayments', False)
        filterClientId = params.get('filterClientId', None)

        rows = []
        if filterClientId:
            rows.append(u'Код пациента: {0}'.format(filterClientId))
        if actionDateType is not None and (begDate or endDate):
            rows.append(u'Тип дат: %s'%{0:u'Выполнения',
                                       1:u'Назначения',
                                       2:u'Начала',
                                       3:u'Планирования'}[actionDateType])
        if dateType == 1:
            rows.append(u'по дате окончания лечения')
            if onlyNotExposed:
                rows.append(u'только невыставленные счета')
        if dateType == 2:
            rows.append(u'по дате выставления счет-фактуры')
            accountType = params.get("accountType", 0)
            if accountType:
                rows.append(u'типы реестров: %s' %  [u"не задано", u"Только Основные", u"Основные + Дополнительные", u"Только Повторные"][accountType])
        if dateType == 3 and params.get('accountId'):
            rows.append(u'по номеру счета: ' + forceString(db.translate('Account', 'id', params.get('accountId'), "concat_ws(' ', number, DATE_FORMAT(exposeDate,'%d:%m:%Y'))")))
        if isPeriodOnService:
            rows.append(u'учитывать период по услуге')
        if dateType != 3 and (begDate or endDate):
            if begDateTime and endDateTime:
                rows.append(dateRangeAsStr(u'за период', begDateTime, endDateTime))
            else:
                rows.append(dateRangeAsStr(u'за период', begDate, endDate))
        if begDateBeforeRecord or endDateBeforeRecord:
            rows.append(dateRangeAsStr(u'период предварительной записи', begDateBeforeRecord, endDateBeforeRecord))
        if useInputDate and (begInputDate or endInputDate):
            rows.append(dateRangeAsStr(u'дата ввода в период', begInputDate, endInputDate))
        if byPeriod is not None:
            if byPeriod:
                rows.append(u'отчёт по периоду случая')
            else:
                rows.append(u'отчёт по окончанию случая')
        if eventPurposeId:
            rows.append(u'Цель обращения: ' + forceString(db.translate('rbEventTypePurpose', 'id', eventPurposeId, 'name')))
        if eventTypeId:
            rows.append(u'Тип обращения: ' + getEventTypeName(eventTypeId))
        if eventType:
            rows.append(u'тип события: ' + getEventTypeNames(eventType))
        if eventTypeList:
            tableET = db.table('EventType')
            records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(eventTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            rows.append(u'Тип обращения:  %s'%(u','.join(name for name in nameList if name)))
        if eventResultId:
            rows.append(u'Результат обращения: ' + forceString(db.translate('rbResult', 'id', eventResultId, 'name')))
        if mesDispansIdList:
            nameList = getMesDispansNameList(mesDispansIdList)
            if nameList:
                rows.append(u'Стандарт:  %s'%(u','.join(name for name in nameList if name)))
        if isPrimary:
           rows.append(u'Первичность: ' + [u'Не учитывать', u'Первичные', u'Повторные'][isPrimary])
        if visitTypeId:
            rows.append(u'Тип визита: ' + forceString(db.translate('rbVisitType', 'id', visitTypeId, 'name')))
        if sceneId:
            rows.append(u'Место: ' + forceString(db.translate('rbScene', 'id', sceneId, 'name')))
        if setOrgStructureId:
            rows.append(u'назначевшее подразделение: ' + getOrgStructureFullName(setOrgStructureId))
        if orgStructureId:
            rows.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        if isPersonPost:
            rows.append(u'тип персонала: %s'%([u'Не задано', u'Врачи', u'Средний медицинский персонал'][isPersonPost]))
        if specialityId:
            rows.append(u'специальность: ' + forceString(db.translate('rbSpeciality', 'id', specialityId, 'name')))
        if personId:
            personInfo = getPersonInfo(personId)
            rows.append(u'врач: ' + personInfo['shortName']+', '+personInfo['specialityName'])
        if personIdList:
            if personIdList:
                db = QtGui.qApp.db
                table = db.table('vrbPersonWithSpecialityAndOrgStr')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(personIdList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                rows.append(u'Врач:  %s'%(u'; '.join(name for name in nameList if name)))
            else:
                rows.append(u'Врач:  не задано')
        if userProfileId:
            rows.append(u'профиль прав пользователя: ' + forceString(db.translate('rbUserProfile', 'id', userProfileId, 'name')))
        if beforeRecordUserId:
            personInfo = getPersonInfo(beforeRecordUserId)
            rows.append(u'пользователь: ' + personInfo['shortName']+', '+personInfo['specialityName'])
        if doctype is not None:
            rows.append(u'тип документа: ' + forceString(db.translate('rbTempInvalidDocument', 'id', doctype, 'name')))
        if tempInvalidReason is not None:
            rows.append(u'причина нетрудоспособности: ' + forceString(db.translate('rbTempInvalidReason', 'id', tempInvalidReason, 'name')))
        if tempInvalidReasonIdList is not None:
            rows.append(u'причина нетрудоспособности: ' + tempInvalidReasonListText)
        if durationTo:
            rows.append(u'длительность нетрудоспособности: c %d по %d дней' % (durationFrom, durationTo))
        if insuranceOfficeMark in (1, 2):
            rows.append([u'без отметки страхового стола', u'с отметкой страхового стола'][insuranceOfficeMark-1])
        if sex:
            rows.append(u'пол: ' + formatSex(sex))
        if typePay is not None:
            if typePay == 0:
                rows.append(u'Тип оплаты: Наличная оплата')
            if typePay == 1:
                rows.append(u'Тип оплаты: Электронная оплата')
            if typePay == 2:
                rows.append(u'Не учитывать факт оплаты')
        if actStatus is not None:
            if actStatus==0:
               rows.append(u'Статус: Начато')
            if actStatus==1:
               rows.append(u'Статус: Ожидание')
            if actStatus==2:
               rows.append(u'Статус: Закончено')
            if actStatus==3:
               rows.append(u'Статус: Отменено')
            if actStatus==4:
               rows.append(u'Статус: Без результата')
            if actStatus==5:
               rows.append(u'Статус: Назначено')
            if actStatus==6:
               rows.append(u'Статус: Отказ')
        if ageFrom is not None and ageTo is not None and ageFrom <= ageTo:
            rows.append(u'возраст: c %d по %d %s' % (ageFrom, ageTo, agreeNumberAndWord(ageTo, (u'год', u'года', u'лет'))))
        if contingentTypeId:
            rows.append(u'Тип контингента: ' + forceString(db.translate('rbContingentType', 'id', contingentTypeId, 'name')))
        if socStatusTypeId:
            rows.append(u'Тип соц.статуса: ' + forceString(db.translate('vrbSocStatusType', 'id', socStatusTypeId, 'name')))
        if socStatusClassId:
            rows.append(u'Класс соц.статуса: ' + forceString(db.translate('rbSocStatusClass', 'id', socStatusClassId, 'name')))
        if areaIdEnabled:
            rows.append(u'проживает на территории: ' + (getOrgStructureFullName(areaId) if areaId else u'ЛПУ'))
        if isFilterAddressOrgStructure:
            rows.append(u'по участку ' + (u'регистрации', u'проживания', u'регистрации или проживания', u'прикрепления', u'регистрации или прикрепления',  u'проживания или прикрепления',  u'регистрации, проживания или прикрепления')[addressOrgStructureType] + u': ' + (getOrgStructureFullName(addressOrgStructure) if addressOrgStructure else u'ЛПУ'))
        if areaAddressType is not None:
            rows.append(u'адрес ' + (u'проживания', u'регистрации')[areaAddressType])
        if locality:
            rows.append(u'%s жители' % ((u'городские', u'сельские')[locality-1]))
        if clientAddressType is not None:
            rows.append(u'адрес ' + [u'регистрации', u'проживания'][clientAddressType])
        if insurerId:
            rows.append(u'СМО: ' + forceString(db.translate('Organisation', 'id', insurerId, 'shortName')))
        if onlyClosed:
            rows.append(u'только закрытые')
        if MKBFilter == 1:
            rows.append(u'код МКБ с "%s" по "%s"' % (MKBFrom, MKBTo))
            if phaseId:
                rows.append(u'фаза заболевания: ' + forceString(db.translate('rbDiseasePhases', 'id', phaseId, 'name')))
        elif MKBFilter == 2:
            rows.append(u'код МКБ пуст')
        if MKBExFilter == 1:
            rows.append(u'доп.код МКБ с "%s" по "%s"' % (MKBExFrom, MKBExTo))
            if phaseIdEx:
                rows.append(u'фаза заболевания: ' + forceString(db.translate('rbDiseasePhases', 'id', phaseIdEx, 'name')))
        elif MKBExFilter == 2:
            rows.append(u'доп.код МКБ пуст')
        if characterClass:
            rows.append(u'характер заболевания:' + [u'Любой', u'Острый', u'Хронический', u'Острый или хронический', u'Фактор', u'исправь меня'][characterClass if 0<=characterClass<5 else -1])
        if stageId:
            rows.append(u'стадия заболевания:' + forceString(db.translate('rbDiseaseStage', 'id', stageId, 'name')))
        if onlyFirstTime:
            rows.append(u'зарегистрированные в период впервые')
        if registeredInPeriod:
            rows.append(u'зарегистрированные в период')
        if notNullTraumaType:
            rows.append(u'тип травмы указан')
        if accountAccomp:
            rows.append(u'учитывать сопутствующие')

        if onlyPermanentAttach:
            rows.append(u'имеющие постоянное прикрепление')
            
        if contractId:
            rows.append(u'по договору № ' + forceString(db.translate('Contract', 'id', contractId, "concat_ws(' | ', (select rbFinance.name from rbFinance where rbFinance.id = Contract.finance_id), Contract.resolution, Contract.number)")))


        if contractIdList:
            if len(contractIdList) == 1:
               rows.append(u'по договору № ' + getContractName(contractIdList[0]))
            else:
               rows.append(u'по договорам №№ ' + formatList([getContractName(contractId) for contractId in contractIdList]))

        if accountIdList:
            if len(accountIdList) == 1:
               rows.append(u'по счёту № ' + getAccountName(accountIdList[0]))
            else:
               rows.append(u'по счетам №№ ' + formatList([getAccountName(accountId) for accountId in accountIdList]))

        if onlyPayedEvents:
            rows.append(u'только оплаченные обращения')
            if self.payPeriodVisible:
                begPayDate = params.get('begPayDate', None)
                endPayDate = params.get('endPayDate', None)
                row = ''
                if begPayDate:
                    row  = row + u' с ' + forceString(begPayDate)
                if endPayDate:
                    row  = row + u' по ' + forceString(endPayDate)
                if row:
                    rows.append(u'в период'+row)
        if self.workTypeVisible:
            workType = params.get('workType', 0)
            if 0<workType<len(OKVEDList.rows):
                descr = OKVEDList.rows[workType]
                name = descr[0]
                code = descr[2]
            else:
                name = u'Любой'
                code = ''
            row = u'Вид деятельности: ' + name
            if code:
                row = row + u', код по ОКВЭД: ' + code
            rows.append(row)
        if self.ownershipVisible:
            ownership = params.get('ownership', 0)
            row = u'Собственность: ' + [u'Любая', u'Бюджетная', u'Частная', u'Cмешанная'][min(ownership, 3)]
            rows.append(row)
        if busyness == 1:
            rows.append(u'занятость указана')
        elif busyness == 2:
            rows.append(u'занятость не указана')
        if currentWorkOrganisation:
            rows.append(u'учитывать только текущее место работы')
        if workOrgId:
            rows.append(u'занятость: '+getOrganisationShortName(workOrgId))
        if OrgId:
            rows.append(u'направление в: '+getOrganisationShortName(OrgId))
        if rbMedicalAidProfileId:
            rows.append(u'профиль помощи: '+getMedicalAidProfileIdName(rbMedicalAidProfileId))
        if actionTypeClass is not None:
            actionTypeClassName={0:u'статус', 1:u'диагностика', 2:u'лечение', 3:u'прочие мероприятия'}.get(actionTypeClass, u'')
            rows.append(u'класс мероприятий: '+actionTypeClassName)
        if actionTypeId:
            actionTypeName=forceString(db.translate('ActionType', 'id', actionTypeId, 'name'))
            rows.append(u'мероприятие: '+actionTypeName)
        if actionTypeCode == 0:
            rows.append(u'мероприятие: Прием')
        elif actionTypeCode == 1:
            rows.append(u'мероприятие: Вызовы')
        if actionStatus is not None:
            rows.append(u'статус выполнения действия: '+ CActionStatus.text(actionStatus))
        if permanentAttach and permanentAttach>0:
            lpu=forceString(db.translate('Organisation', 'id', permanentAttach, 'shortName'))
            rows.append(u'прикрепление: '+lpu)
        if deathPlace:
            rows.append(u'смерть последовала: '+deathPlace)
        if deathCause:
            rows.append(u'смерть произошла: '+deathCause)
        if deathFoundBy:
            rows.append(u'причина смерти установлена: '+deathFoundBy)
        if deathFoundation:
            rows.append(u'основание установления причины смерти: '+deathFoundation)
        if typeFinanceId is not None:
            rows.append(u'тип финансирования: '+ forceString(db.translate('rbFinance', 'id', typeFinanceId, 'name')))
        if tariff is not None:
            rows.append(u'тарификация: '+ [u'не учитывать', u'тарифицированные', u'не тарифицированные'][tariff])
        if visitPayStatus is not None:
            rows.append(u'флаг финансирования: '+ [u'не задано', u'не выставлено', u'выставлено', u'отказано', u'оплачено'][visitPayStatus])
        if groupingRows is not None:
            rows.append(u'группировка: '+ [u'по специальности', u'по должности', u'по профилю оплаты', u'по страховым'][groupingRows])
        if rowGrouping is not None:
            rows.append(u'группировка: '+ [u'по датам', u'по месяцам', u'по врачам', u'по подразделениям', u'по специальности', u'по должности'][rowGrouping])
        if equipmentId is not None:
            rows.append(u'Оборудование: ' + forceString(db.translate('rbEquipment', 'id', equipmentId, 'name')))
        if vidPom!=None:
            vidPomName = forceString(QtGui.qApp.db.translate('rbMedicalAidType', 'id', params['vidPom'],'name'))
            rows.append(u'вид помощи: '+vidPomName)
        if naselenie!=None:
           if naselenie==1:
               rows.append(u'население: краевое')
           if naselenie==2:
               rows.append(u'население: инокраевое')
        if scheta!=None:
            if scheta == 1: 
                rows.append(u'по представленным к оплате счетам')
            if scheta == 2: 
                rows.append(u'по счетам подлежащих к оплате')
            if scheta == 3:
                rows.append(u'по счетам возвращенным из СМО')
        if osnScheta:
            rows.append(u'только по основным счетам')            
        if without0price:
            rows.append(u'не учитывая услуги с нулевой ценой')
        if payer!=None:
           rows.append(u'плательщик: ' + forceString(db.translate('Organisation', 'id', payer, 'shortName')))
        if age1!=None and age2:
            if not (age1 == 0 and age2==150):
                rows.append(u'Возраст: с %s до %s' %(age1, age2))
        if profileBedId:
            rows.append(u'профиль койки: %s'%(forceString(db.translate('rbHospitalBedProfile', 'id', profileBedId, "concat(code, ' | ', name)"))))

        if ismancheckedage != None:
            rows.append(u'Мужчины ' + forceString(manAgeBegValue) + manAgeBegType + '-' + forceString(manAgeEndValue) + manAgeEndType)

        if iswomencheckedage != None:
            rows.append(u'Женщины ' + forceString(womanAgeBegValue) + womanAgeBegType + '-' + forceString(womanAgeEndValue) + womanAgeEndType)
        if cashPayments:
            rows.append(u'Оплата по кассовому аппарату')
        rows.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))

        return rows


    def dumpParamsEventTypeList(self, cursor, params):
        description = []
        #db = QtGui.qApp.db
        eventTypeIdList = params.get('eventTypeIdList', None)
        if eventTypeIdList:
            description.append(u'тип обращения:')
            for eventTypeId in eventTypeIdList:
                description.append(getEventTypeName(eventTypeId))
            columns = [ ('100%', [], CReportBase.AlignLeft) ]
            table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
            for i, row in enumerate(description):
                table.setText(i, 0, row)
            cursor.movePosition(QtGui.QTextCursor.End)


    def dumpParamsAdress(self, cursor, params):
        description = []
        db = QtGui.qApp.db
        typeAdress = [u'регистрации', u'проживания']
        filterAddress = params.get('isFilterAddress', False)
        if filterAddress:
            filterAddressType = params.get('filterAddressType', 0)
            filterAddressCity = params.get('filterAddressCity', None)
            filterAddressStreet = params.get('filterAddressStreet', None)
            filterAddressHouse = params.get('filterAddressHouse', u'')
            filterAddressCorpus = params.get('filterAddressCorpus', u'')
            filterAddressFlat = params.get('filterAddressFlat', u'')

            description.append(u'Адрес ' + forceString(typeAdress[filterAddressType]) + u':')
            description.append((u'город ' + forceString(db.translate(u'kladr.KLADR', u'CODE', filterAddressCity, u'NAME')) if filterAddressCity else u'') + (u' улица ' + forceString(db.translate(u'kladr.STREET', u'CODE', filterAddressStreet, u'NAME')) if filterAddressStreet else u'') + (u' дом ' + forceString(filterAddressHouse) if filterAddressHouse else u'') + (u' корпус ' + forceString(filterAddressCorpus) if filterAddressCorpus else u'') + (u' квартира ' + forceString(filterAddressFlat) if filterAddressFlat else u''))

            columns = [ ('100%', [], CReportBase.AlignLeft) ]
            table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
            for i, row in enumerate(description):
                table.setText(i, 0, row)
            cursor.movePosition(QtGui.QTextCursor.End)


    def dumpParamsAttach(self, cursor, params):
        description = []
        db = QtGui.qApp.db
        chkFilterAttachType = params.get('chkFilterAttachType', False)
        if chkFilterAttachType:
            attachCategory, attachTypeId, attachBegDate, attachEndDate = params.get('attachType', (0, None, QDate(), QDate()))
            description.append(u'прикрепление ' + [u'-', u'Постоянное', u'Временное', u'Выбыл'][attachCategory])
            if attachBegDate or attachEndDate:
                description.append(dateRangeAsStr(u'прикрепление за период', attachBegDate, attachEndDate))
            if attachTypeId:
               description.append(u'Тип прикрепления: ' + forceString(db.translate('rbAttachType', 'id', attachTypeId, 'name')))
        dead = params.get('dead', False)
        if dead:
            begDeathDate = params.get('begDeathDate', QDate()) if params.get('chkFilterDeathBegDate', False) else None
            endDeathDate = params.get('endDeathDate', QDate()) if params.get('chkFilterDeathEndDate', False) else None
            description.append(dateRangeAsStr(u'умершие', begDeathDate, endDeathDate))
        chkFilterAttach = params.get('chkFilterAttach', False)
        if chkFilterAttach:
            attachTo = params.get('attachTo', None)
            if attachTo:
                description.append(u'прикрепление к ЛПУ: ' + forceString(db.translate('Organisation', 'id', attachTo, 'shortName')))
        attachToNonBase = params.get('attachToNonBase', False)
        if attachToNonBase:
            description.append(u'любое ЛПУ кроме базового')
        excludeLeaved = params.get('excludeLeaved', False)
        if excludeLeaved:
            description.append(u'скрыть выбывших')
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)


class CReportEx(CReport):
    def __init__(self, parent=None, title=''):
        CReport.__init__(self, parent)
        self.table_columns = []
        self.setTitle(title)


    def getReportName(self):
        return self.title()


    def getSelectFunction(self, params = None):
        return None


    def addParagraph(self, cursor, text):
        cursor.insertText(text)
        cursor.insertBlock()


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        reportName = self.getReportName()
        if hasattr(self, 'getPeriodName'):
            reportName += u' за ' + self.getPeriodName(params) # WFT?
        self.addParagraph(cursor, reportName)
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        old_table_columns = [self.table_columns[i] for i in xrange(len(self.table_columns))]
        self.buildInt(params, cursor)
        self.table_columns = old_table_columns
        cursor.movePosition(QtGui.QTextCursor.End)
        return doc


    def buildInt(self, params, cursor):
        return []


    def addColumn(self, column, i=-1):
        if i==-1:
            self.table_columns = self.table_columns + [column, ]
        else:
            self.table_columns.insert(i, column)


    def removeColumn(self, i): # вызывается только внутри buildInt
        self.table_columns.remove(self.table_columns[i])


    def colCount(self):
        return len(self.table_columns)


    def createTable(self, cursor, border = 1, cellPadding=2, cellSpacing=0):
        headerRowCount = 0
        for columnDescr in self.table_columns:
                width, headers, align = columnDescr
                if type(headers) == list:
                    headerRowCount = max(headerRowCount,  len(headers))
        return createTable(cursor, self.table_columns, border=border, headerRowCount=headerRowCount, cellPadding=cellPadding, cellSpacing=cellSpacing)


    def addEmptyRows(self, table, num):
        for i in xrange(num):
           table.addRow()


    def fillTable(self, table, reportData):
        rows = len(reportData)
        if rows > 0:
            cols = min(table.colCount(), len(reportData[0]))
            for i in xrange(rows):
                rowNum = table.addRow()
                for j in xrange(cols):
                    table.setText(rowNum, j, unicode(reportData[i][j]))


    def setColumn(self, table, column, array, format_ = "%s"):
        for i in xrange(len(array)):
            row = i + table.headerRowCount()
            if row >= table.rowCount():
                table.addRow()
            table.setText(row, column, format_%array[i])


    def setNumbers(self, table, col=0):
        self.setColumn(table, col, xrange(1, table.dataRowCount() + 1), "%d")


    def addSummary(self, table, reportData, columns = [], format="%d"):
        def dict2Array(d):
            if type(d) == dict:
                array = [j for (i, j) in d.items()]
                d = []
                for elem in array:
                    (goodelem, subdict) = dict2Array(elem)
                    if subdict:
                        d = d + goodelem
                    else:
                        d = d + [goodelem, ]
                return (d, True)
            return (d, False)

        tableRow = table.addRow()
        table.setText(tableRow, 0, u'Итого:')
        (reportData, isdict) = dict2Array(reportData)
        rows = len(reportData)
        cols = len(reportData[0]) if rows else table.colCount()
        if len(columns) == 0:
            columns = xrange(1, cols)
        mincol = min(columns)
        table.mergeCells(tableRow, 0, 1, mincol)
        for i in columns:
            summa = sum([reportData[j][i] for j in xrange(rows)])
            table.setText(tableRow, i, format%summa)


    def getTableColumnByName(self, name):
        return -1


    def printColumn(self, columnName, tableRow, table, value):
        tableColumn = self.getTableColumnByName(columnName)
        if tableColumn >= 0:
            table.setText(tableRow, tableColumn, value)


    def printValues(self, tableRow, table, item):
        for columnName, value in item.items():
            self.printColumn(columnName, tableRow, table, value)


    #TODO: унифицировать с addSummary
    def calcResult(self, result, item):
         for columnName, value in item.items():
             result[columnName] += value


    def printValuesWithCalcResult(self, tableRow, table, item, result):
        for columnName, value in item.items():
            self.printColumn(columnName, tableRow, table, value)
            result[columnName] += value


class CVoidSetupDialog(object):
    u"""Полезный класс, если не нужно ничего запрашивать для отчета.
    Можно через него передавать параметры."""
    def __init__(self, parent):
        self._params = dict()

    def setParams(self, params): # сохраняет параметры с отличающимися именами
        for key in params.keys():
            self._params[key] = params[key]
            #self._params.setdefault(key, params[key])

    def updateParams(self, params): # меняет все параметры
        self._params = params

    def params(self):
        return self._params

    def exec_(self):
        return True



def normalizeMKB(mkb):
    mkb = MKBwithoutSubclassification(mkb)
    if len(mkb) == 3:
        mkb = mkb + '.0'
    return mkb


def getEventTypeName(eventTypeId):
    from Events.Utils import getEventName
    if eventTypeId:
        return getEventName(eventTypeId)
    else:
        return u'-'


def getEventTypeNames(eventTypeId):
    from Events.Utils import getEventName
    if eventTypeId:
        name = []
        for i in eventTypeId.split(','):
            name.append(getEventName(i.replace(' ', '')))
            name.append(', ')

        del name[-1]
        name = ''.join(name)

        return name
    else:
        return u'-'


def getContractName(contractId):
    if contractId:
        record = QtGui.qApp.db.getRecord('Contract', 'number, date', contractId)
        return forceString(record.value('number')) + u' от ' +forceString(record.value('date'))
    else:
        return '-'


def getAccountName(accountId):
    if accountId:
        record = QtGui.qApp.db.getRecord('Account', 'number, date', accountId)
        return forceString(record.value('number')) + u' от ' +forceString(record.value('date'))
    else:
        return '-'


def convertFilterToString(filter, filterFormat):
    # filter: словарь
    # filterFormat: список троек ( ключ-или-список-ключей, заголовок, функция преобразования )
    # выводит строки заголовок: filter[ключ]
    # для непустых filter[ключ]
    parts = []
    for keys, title, formatFunc in filterFormat:
        if isinstance(keys, basestring):
            values = [filter.get(keys, None)]
        else:
            values = [filter.get(key, None) for key in keys]
        if any(values):
            if formatFunc:
                outValue = formatFunc(*values)
            else:
                outValue = ' '.join([v for v in values if v])
            if outValue:
                parts.append(title +': '+outValue)
            else:
                parts.append(title)
    return '\n'.join(parts)


def selectMonthData(selectFunction, date, *args):
    u"""Возвращает массив результатов запросов - каждый на 1 день месяца"""
    db = QtGui.qApp.db
    daysInMonth = date.daysInMonth()
    date = firstMonthDay(date)
    result = [0] * daysInMonth
    for i in xrange(daysInMonth):
        result[i] = selectFunction(db, date.addDays(i), date.addDays(i), *args)
    return result

def selectYearData(selectFunction, date, *args):
    u"""Возвращает массив результатов запросов - каждый на 1 месяц года"""
    db = QtGui.qApp.db
    year = date.year()
    result = [0] * monthsInYear
    for i in xrange(monthsInYear):
        firstDay = QDate(year, i+1, 1)
        result[i] = selectFunction(db, firstDay, lastMonthDay(firstDay), *args)
    return result
