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

from library.Utils           import forceDate, forceInt, forceRef, forceString
from Events.ActionStatus     import CActionStatus
from Reports.Report          import CReport
from Reports.ReportBase      import CReportBase, createTable
from Reports.Utils           import updateLIKE, existsPropertyValue, dateRangeAsStr
from Reports.TempInvalidF035Dialog import CTempInvalidF035Dialog
from Orgs.Utils              import getOrgStructureFullName, getPersonInfo
from Events.Utils            import getActionTypeIdListByFlatCode


def selectData(params):
    def addEqCond(cond, table, fieldName, filter, name):
        if name in filter:
            cond.append(table[fieldName].eq(filter[name]))

    def addDateCond(cond, table, fieldName, filter, begDateName, endDateName):
        begDate = filter.get(begDateName, None)
        if begDate:
            cond.append(table[fieldName].ge(begDate))
        endDate = filter.get(endDateName, None)
        if endDate:
            cond.append(table[fieldName].lt(endDate.addDays(1)))

    def getPropertyValue(propertyName, aliasName, tableName):
        return u'''(SELECT APS.value
            FROM ActionProperty AS AP
            INNER JOIN ActionPropertyType AS APT ON AP.type_id = APT.id
            INNER JOIN %s AS APS ON APS.id = AP.id
            WHERE AP.action_id = Action.id AND APT.actionType_id = Action.actionType_id
            AND  Action.id IS NOT NULL AND APS.value != ''
            AND APT.deleted = 0 AND AP.deleted = 0 AND APT.name %s
            LIMIT 1) AS %s'''%(tableName, updateLIKE(propertyName), aliasName)

    def getPropertyValueRBTable(propertyName, aliasName, tableName, rbTableName):
        return u'''(SELECT rbTableName.name
            FROM ActionProperty AS AP
            INNER JOIN ActionPropertyType AS APT ON AP.type_id = APT.id
            INNER JOIN %s AS APS ON APS.id = AP.id
            INNER JOIN %s AS rbTableName ON rbTableName.id = APS.value
            WHERE AP.action_id = Action.id AND APT.actionType_id = Action.actionType_id
            AND  Action.id IS NOT NULL AND APS.value != ''
            AND APT.deleted = 0 AND AP.deleted = 0 AND APT.name %s
            LIMIT 1) AS %s'''%(tableName, rbTableName, updateLIKE(propertyName), aliasName)

    def getPropertyValueMSE(propertyName, aliasName, tableName):
        return u'''(SELECT APS.value
            FROM ActionProperty AS AP
            INNER JOIN ActionPropertyType AS APT ON AP.type_id = APT.id
            INNER JOIN %s AS APS ON APS.id = AP.id
            INNER JOIN Action AS A ON AP.action_id = A.id
            INNER JOIN ActionType AS AT ON AT.id = A.actionType_id
            WHERE AT.flatCode LIKE 'inspection_mse%%'
            AND A.prevAction_id = Action.id
            AND APT.actionType_id = A.actionType_id AND APS.value != ''
            AND  A.id IS NOT NULL AND A.deleted = 0 AND AT.deleted = 0
            AND APT.deleted = 0 AND AP.deleted = 0 AND APT.name %s
            LIMIT 1) AS %s'''%(tableName, updateLIKE(propertyName), aliasName)

    db = QtGui.qApp.db
    table = db.table('Action')
    tableEvent = db.table('Event')
    tableClient = db.table('Client')
    tablePerson = db.table('vrbPersonWithSpeciality')
    tableOrganisation = db.table('Organisation')

    queryTable = table.innerJoin(tableEvent, tableEvent['id'].eq(table['event_id']))
    queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(table['setPerson_id']))
    queryTable = queryTable.leftJoin(tableOrganisation, db.joinAnd([tableOrganisation['id'].eq(tablePerson['org_id']), tableOrganisation['deleted'].eq(0)]))

#    expertiseId = params.get('expertiseId', None)
    actionTypeList = getActionTypeIdListByFlatCode(u'inspection_disability%')
    actionTypeList.extend(getActionTypeIdListByFlatCode(u'inspection_case%'))
    cond = [table['actionType_id'].inlist(actionTypeList),
            table['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            table['endDate'].isNotNull(),
            tableClient['deleted'].eq(0)
           ]
    expertiseTypeId = params.get('expertiseTypeId', None)
    if bool(expertiseTypeId is not None and expertiseTypeId[0]):
        cond.append(table['actionType_id'].inlist(expertiseTypeId[0]))
    addDateCond(cond, table, 'endDate', params, 'begExecDate', 'endExecDate')
    addEqCond(cond, table, 'setPerson_id', params, 'setPersonId')
    addEqCond(cond, table, 'person_id', params, 'expertId')
    actionMKBFrom = params.get('begMKB', None)
    actionMKBTo = params.get('endMKB', None)
    if actionMKBFrom or actionMKBTo:
        if actionMKBFrom and not actionMKBTo:
           actionMKBTo = u'U'
        elif not actionMKBFrom and actionMKBTo:
            actionMKBFrom = u'A'
        cond.append(table['MKB'].ge(actionMKBFrom))
        cond.append(table['MKB'].le(actionMKBTo))
    addEqCond(cond, table, 'status', params, 'actionStatus')
    if 'expertOrgStructureId' in params or 'expertSpecialityId' in params:
        if 'expertOrgStructureId' in params:
            expertOrgStructureId = params.get('expertOrgStructureId', None)
            if expertOrgStructureId:
                orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', expertOrgStructureId)
                if orgStructureIdList:
                    cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
        if 'expertSpecialityId' in params:
            expertSpecialityId = params.get('expertSpecialityId', None)
            if expertSpecialityId:
                cond.append(tablePerson['speciality_id'].eq(expertSpecialityId))
    expertiseCharacterId = params.get('expertiseCharacterId', None)
    if expertiseCharacterId:
        cond.append(existsPropertyValue(u'ActionProperty_rbMedicalBoardExpertiseCharacter', u'Характеристика экспертизы', unicode(expertiseCharacterId)))
    expertiseKindId = params.get('expertiseKindId', None)
    if expertiseKindId:
        cond.append(existsPropertyValue(u'ActionProperty_rbMedicalBoardExpertiseKind', u'Вид экспертизы', unicode(expertiseKindId)))
    expertiseObjectId = params.get('expertiseObjectId', None)
    if expertiseObjectId:
        cond.append(existsPropertyValue(u'ActionProperty_rbMedicalBoardExpertiseObject', u'Предмет экспертизы', unicode(expertiseObjectId)))
    expertiseArgumentId = params.get('expertiseArgumentId', None)
    if expertiseArgumentId:
        cond.append(existsPropertyValue(u'ActionProperty_rbMedicalBoardExpertiseArgument', u'Обоснование экспертизы', unicode(expertiseArgumentId)))

    cols = [table['id'].alias('actionId'),
            table['endDate'],
            tablePerson['name'].alias('personName'),
            tableOrganisation['shortName'].alias('orgName'),
            tableClient['id'].alias(u'clientId'),
            u'''CONCAT_WS(_utf8' ', Client.lastName, Client.firstName, Client.patrName, CAST(Client.id AS CHAR)) AS clientName''',
            tableClient['birthDate'],
            tableClient['sex'],
            table['MKB'],
            u'''(SELECT A.endDate FROM Action AS A WHERE A.prevAction_id = Action.id AND A.deleted = 0/* ORDER BY A.endDate DESC*/ LIMIT 1) AS prevEndDate''',
            u'''(SELECT tip.isExternal FROM TempInvalid ti LEFT JOIN TempInvalid_Period tip ON tip.master_id = ti.id WHERE ti.id = Event.tempInvalid_id LIMIT 1) AS tipIsExternal''',
            u'''(SELECT SUM(DATEDIFF(tip.endDate, tip.begDate) + 1) FROM TempInvalid ti LEFT JOIN TempInvalid_Period tip ON tip.master_id = ti.id WHERE ti.id = Event.tempInvalid_id) AS sumDays'''
            ]
    if params.get('isRegAddress', 0):
        cols.append(u'getClientRegAddress(Client.id) AS address')
    if params.get('isNumberPolicy', 0):
        cols.append(u'getClientPolicy(Client.id, 1) AS policy')
    cols.append(u'getClientWork(Client.id) as work')
    cols.append(getPropertyValue(u'Номер', u'expertNumberExpertise', u'ActionProperty_String'))
    cols.append(getPropertyValueRBTable(u'Характеристика экспертизы', u'expertiseCharacter', u'ActionProperty_rbMedicalBoardExpertiseCharacter', u'rbMedicalBoardExpertiseCharacter'))
    cols.append(getPropertyValueRBTable(u'Вид экспертизы', u'expertiseKind', u'ActionProperty_rbMedicalBoardExpertiseKind', u'rbMedicalBoardExpertiseKind'))
    cols.append(getPropertyValueRBTable(u'Предмет экспертизы', u'expertiseObject', u'ActionProperty_rbMedicalBoardExpertiseObject', u'rbMedicalBoardExpertiseObject'))
    cols.append(getPropertyValue(u'Номер ЛН', u'expertNumberMC', u'ActionProperty_String'))
    cols.append(getPropertyValue(u'Выявлено при экспертизе: отклонение от стандартов', u'expertDeviation', u'ActionProperty_String'))
    cols.append(getPropertyValue(u'Выявлено при экспертизе: дефекты, нарушения, ошибки и др.', u'expertError', u'ActionProperty_String'))
    cols.append(getPropertyValue(u'Выявлено при экспертизе: результат этапа', u'expertResult', u'ActionProperty_String'))
    cols.append(getPropertyValue(u'Решение', u'expertDecision', u'ActionProperty_String'))
    cols.append(getPropertyValueMSE(u'Результат', u'resultMSE', u'ActionProperty_String'))
    cols.append(getPropertyValueMSE(u'Решение МСЭ', u'decisionMSE', u'ActionProperty_String'))
    cols.append(getPropertyValueMSE(u'Дата освидетельствования МСЭ', u'dateMSE', u'ActionProperty_String'))
    cols.append(getPropertyValueMSE(u'Причина инвалидности', u'reasonMSE', u'ActionProperty_String'))
    cols.append(getPropertyValueMSE(u'Степень ограничения способности к трудовой деятельности', u'restrictionMSE', u'ActionProperty_String'))
    cols.append(getPropertyValueMSE(u'Инвалидность установлена на срок до', u'disabilityMSE', u'ActionProperty_String'))
    cols.append(getPropertyValueMSE(u'Дата очередного освидетельствования', u'dateLastMSE', u'ActionProperty_String'))
    cols.append(u"COALESCE ({0}, {1}) AS expert1".format(
        getPropertyValue(u'Эксперт 1', u'expert1', u'ActionProperty_Person').replace(u'AS expert1', u''),
        getPropertyValue(u'Эксперт 1', u'expert1', u'ActionProperty_String').replace(u'AS expert1', u'')))
    cols.append(u"COALESCE ({0}, {1}) AS expert2".format(
        getPropertyValue(u'Эксперт 2', u'expert2', u'ActionProperty_Person').replace(u'AS expert2', u''),
        getPropertyValue(u'Эксперт 2', u'expert2', u'ActionProperty_String').replace(u'AS expert2', u'')))
    cols.append(u"COALESCE ({0}, {1}) AS expert3".format(
        getPropertyValue(u'Эксперт 3', u'expert3', u'ActionProperty_Person').replace(u'AS expert3', u''),
        getPropertyValue(u'Эксперт 3', u'expert3', u'ActionProperty_String').replace(u'AS expert3', u'')))
    cols.append(u"COALESCE ({0}, {1}) AS expert4".format(
        getPropertyValue(u'Эксперт 4', u'expert4', u'ActionProperty_Person').replace(u'AS expert4', u''),
        getPropertyValue(u'Эксперт 4', u'expert4', u'ActionProperty_String').replace(u'AS expert4', u'')))
    cols.append(u'''(SELECT rbSocStatusType.name
FROM rbSocStatusType
INNER JOIN rbSocStatusClassTypeAssoc ON rbSocStatusClassTypeAssoc.type_id = rbSocStatusType.id
INNER JOIN rbSocStatusClass ON rbSocStatusClass.id = rbSocStatusClassTypeAssoc.class_id
INNER JOIN ClientSocStatus ON (ClientSocStatus.socStatusClass_id = rbSocStatusClass.id AND ClientSocStatus.socStatusType_id = rbSocStatusType.id)
WHERE rbSocStatusClass.code = 9 AND ClientSocStatus.client_id = Client.id AND ClientSocStatus.deleted = 0
ORDER BY ClientSocStatus.begDate DESC, ClientSocStatus.endDate DESC
LIMIT 1) AS socStatus''')

    return db.getRecordList(queryTable, cols, cond, u'Action.endDate, expertNumberExpertise')


def getPersonName(personId):
    db = QtGui.qApp.db
    query = db.query("select vp.name from vrbPerson vp where vp.id = {0}".format(personId))
    if query.next():
        return forceString(query.value(0))
    return str()


class CTempInvalidBookF035(CReport):
    name = u'Журнал учета клинико-экспертной работы лечебно-профилактического учреждения (Ф.035).'

    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(self.name)


    def getSetupDialog(self, parent):
        result = CTempInvalidF035Dialog(parent)
        result.setTitle(self.title())
        return result


    def getDescription(self, params):
        db = QtGui.qApp.db
        begDate = params.get('begExecDate', QDate())
        endDate = params.get('endExecDate', QDate())
        MKBFrom = params.get('begMKB', '')
        MKBTo = params.get('endMKB', '')
        expertOrgStructureId = params.get('expertOrgStructureId', None)
        expertSpecialityId = params.get('expertSpecialityId', None)
        setPersonId = params.get('setPersonId', None)
        expertId = params.get('expertId', None)
        actionStatus = params.get('actionStatus', None)
        expertiseType = params.get('expertiseTypeId', ([], u''))
        expertiseCharacterId = params.get('expertiseCharacterId', None)
        expertiseKindId = params.get('expertiseKindId', None)
        expertiseObjectId = params.get('expertiseObjectId', None)
        expertiseArgumentId = params.get('expertiseArgumentId', None)
        rows = []
        if begDate or endDate:
            rows.append(dateRangeAsStr(u'за период', begDate, endDate))
        if expertiseType[0] or expertiseType[1]:
            rows.append(u'тип экспертизы: ' + expertiseType[1])
        if expertiseCharacterId:
            rows.append(u'характер экспертизы: ' + forceString(db.translate('rbMedicalBoardExpertiseCharacter', 'id', expertiseCharacterId, 'name')))
        if expertiseKindId:
            rows.append(u'вид экспертизы: ' + forceString(db.translate('rbMedicalBoardExpertiseKind', 'id', expertiseKindId, 'name')))
        if expertiseObjectId:
            rows.append(u'предмет экспертизы: ' + forceString(db.translate('rbMedicalBoardExpertiseObject', 'id', expertiseObjectId, 'name')))
        if expertiseArgumentId:
            rows.append(u'обоснование экспертизы: ' + forceString(db.translate('rbMedicalBoardExpertiseArgument', 'id', expertiseArgumentId, 'name')))
        if expertOrgStructureId:
            rows.append(u'подразделение: ' + getOrgStructureFullName(expertOrgStructureId))
        if expertSpecialityId:
            rows.append(u'специальность: ' + forceString(db.translate('rbSpeciality', 'id', expertSpecialityId, 'name')))
        if setPersonId:
            personInfo = getPersonInfo(setPersonId)
            rows.append(u'назначивший врач: ' + personInfo['shortName']+', '+personInfo['specialityName'])
        if expertId:
            personInfo = getPersonInfo(expertId)
            rows.append(u'эксперт: ' + personInfo['shortName']+', '+personInfo['specialityName'])
        if MKBFrom or MKBTo:
            rows.append(u'код МКБ с "%s" по "%s"' % (MKBFrom, MKBTo))
        if actionStatus is not None:
            rows.append(u'статус выполнения действия: '+ CActionStatus.text(actionStatus))
        rows.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        return rows


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.name)
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        isRegAddress = params.get('isRegAddress', 0)
        isNumberPolicy = params.get('isNumberPolicy', 0)
        isClientId = params.get('isClientId', 0)
        cursor.insertBlock()
        tableColumns = [
            ('2%', [u'N п/п', u'', u'1' ], CReportBase.AlignLeft),
            ('4.9%', [u'Дата экспертизы', u'', u'2' ], CReportBase.AlignLeft),
            ('4.9%', [u'Наименование ЛПУ, фамилия врача, направившего пациента на экспертизу', u'', u'3' ], CReportBase.AlignLeft),
            ('4.9%', [u'Фамилия, имя, отчество пациента', u'', u'4' ], CReportBase.AlignLeft),
            ('4.9%', [u'Адрес (либо номер страхового полиса или медицинского документа) пациента', u'', u'5' ], CReportBase.AlignLeft),
            ('4.9%', [u'Дата рождения', u'', u'6' ], CReportBase.AlignLeft),
            ('2%', [u'Пол', u'', u'7' ], CReportBase.AlignRight),
            ('4.9%', [u'Социальный статус', u'профессия', u'8' ], CReportBase.AlignLeft),
            ('2%', [u'Причина обращения, Диагноз (основной, сопутствующий) в соответсвии с МКБ-10', u'', u'9' ], CReportBase.AlignLeft),
            ('4.9%', [u'Характеристика случая экспертизы', u'', u'10' ], CReportBase.AlignLeft),
            ('5%', [u'Вид и предмет экспертизы', u'(проставляется N Л/Н, количество дней нетрудоспосо-бности, длительность пребывания в ЛПУ и др. в зависимости от вида экспертизы)', u'11' ], CReportBase.AlignLeft),
            ('4.9%', [u'Выявлено при экспертизе', u'отклонение от стандартов', u'12'], CReportBase.AlignLeft),
            ('4.9%', [u'', u'дефекты, нарушения, ошибки и др.', u'13'], CReportBase.AlignLeft),
            ('4.9%', [u'', u'достижение результата этапа или исхода лечебно- профилактического мероприятия', u'14'], CReportBase.AlignLeft),
            ('4.9%', [u'Обоснование заключения. Заключение экспертов, рекомендации', u'', u'15'], CReportBase.AlignLeft),
            ('4.9%', [u'Дата направления в бюро МСЭ или другие (специализиро-ванные) учреждения', u'', u'16'], CReportBase.AlignRight),
            ('4.9%', [u'Заключение МСЭ или других (специализиро-ванных) учреждений', u'', u'17'], CReportBase.AlignLeft),
            ('4.9%', [u'Дата получения заключения МСЭ или других учреждений, срок его действия', u'', u'18'], CReportBase.AlignLeft),
            ('4.9%', [u'Дополнительная информация по заключению других (специализиро-ванных) учреждений. Примечания', u'', u'19'], CReportBase.AlignLeft),
            ('4.9%', [u'Основной состав экспертов', u'', u'20'], CReportBase.AlignLeft),
            ('4.9%', [u'Подписи экспертов', u'', u'21'], CReportBase.AlignLeft),
            ]

        table = createTable(cursor, tableColumns, duplicateHeaderOnNewPage=False)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 2, 1)
        table.mergeCells(0, 4, 2, 1)
        table.mergeCells(0, 5, 2, 1)
        table.mergeCells(0, 6, 2, 1)
        table.mergeCells(0, 8, 2, 1)
        table.mergeCells(0, 9, 2, 1)
        table.mergeCells(0, 11, 1, 3)
        table.mergeCells(0, 14, 2, 1)
        table.mergeCells(0, 15, 2, 1)
        table.mergeCells(0, 16, 2, 1)
        table.mergeCells(0, 17, 2, 1)
        table.mergeCells(0, 18, 2, 1)
        table.mergeCells(0, 19, 2, 1)
        table.mergeCells(0, 20, 2, 1)

        cnt = params.get('cntUser', 1)
        actionIdList = []
        records = selectData(params)
        for record in records:
            actionId = forceRef(record.value('actionId'))
            if actionId and actionId not in actionIdList:
                actionIdList.append(actionId)
                endDate = forceDate(record.value('endDate')).toString(u'dd.MM.yyyy')
                personName = forceString(record.value('personName'))
                orgName = forceString(record.value('orgName'))
                clientName = forceString(record.value('clientName'))
                birthDate = forceDate(record.value('birthDate')).toString(u'dd.MM.yyyy')
                sex = [u'', u'М', u'Ж'][forceInt(record.value('sex'))]
                MKB = forceString(record.value('MKB'))
                prevEndDate = forceDate(record.value('prevEndDate')).toString(u'dd.MM.yyyy')
                columnN5 = u''
                if isRegAddress:
                    columnN5 += u'Адрес: ' + forceString(record.value('address')) + (u'\n' if (isNumberPolicy or isClientId) else u'')
                if isNumberPolicy:
                    columnN5 += u'Полис: ' + forceString(record.value('policy')) + (u'\n' if isClientId else u'')
                if isClientId:
                    columnN5 += u'Номер карты: ' + forceString(record.value('clientId'))
                socStatus = forceString(record.value('socStatus'))
                work = forceString(record.value('work'))
                socStatusWork = socStatus + ', ' + work if socStatus else work
                externalLength = forceInt(record.value('sumDays'))

                duration = str(externalLength) + u' дн.' if externalLength else u'0 дн.'
                expertiseCharacter = forceString(record.value('expertiseCharacter'))
                expertiseKind = forceString(record.value('expertiseKind'))
                expertiseKindName = (u'Вид:' + expertiseKind) if expertiseKind else u''
                expertiseObject = forceString(record.value('expertiseObject'))
                expertiseObjectName = (u'Предмет:' + expertiseObject) if expertiseObject else u''
                expertNumberMC = forceString(record.value('expertNumberMC'))
                expertNumberMCName = (u'Номер ЛН:' + expertNumberMC) if expertNumberMC else u''
                expertDeviation = forceString(record.value('expertDeviation'))
                expertError = forceString(record.value('expertError'))
                expertResult = forceString(record.value('expertResult'))
                expertDecision = forceString(record.value('expertDecision'))
                resultMSE = forceString(record.value('resultMSE'))
                resultMSEName = (u'Результат: ' + resultMSE) if resultMSE else u''
                decisionMSE = forceString(record.value('decisionMSE'))
                decisionMSEName = (u'Решение МСЭ: ' + decisionMSE) if decisionMSE else u''
                dateMSE = forceString(record.value('dateMSE'))
                reasonMSE = forceString(record.value('reasonMSE'))
                reasonMSEName = (u'Причина инвалидности: ' + reasonMSE) if reasonMSE else u''
                restrictionMSE = forceString(record.value('restrictionMSE'))
                restrictionMSEName = (u'Степень ограничения способности к трудовой деятельности: ' + restrictionMSE) if restrictionMSE else u''
                disabilityMSE = forceString(record.value('disabilityMSE'))
                disabilityMSEName = (u'Инвалидность установлена на срок до: ' + disabilityMSE) if disabilityMSE else u''
                dateLastMSE = forceString(record.value('dateLastMSE'))
                dateLastMSEName = (u'Дата очередного освидетельствования: ' + dateLastMSE) if dateLastMSE else u''
                expert1 = forceString(record.value('expert1'))
                expert1 = getPersonName(expert1) if expert1.isdigit() else expert1
                expert1 = expert1 + u',' if expert1.replace(u' ', u'') != u"" else expert1
                expert2 = forceString(record.value('expert2'))
                expert2 = getPersonName(expert2) if expert2.isdigit() else expert2
                expert2 = expert2 + u',' if expert2.replace(u' ', u'') != u"" else expert2
                expert3 = forceString(record.value('expert3'))
                expert3 = getPersonName(expert3) if expert3.isdigit() else expert3
                expert3 = expert3 + u',' if expert3.replace(u' ', u'') != u"" else expert3
                expert4 = forceString(record.value('expert4'))
                expert4 = getPersonName(expert4) if expert4.isdigit() else expert4
                expert4 = expert4 + u',' if expert4.replace(u' ', u'') != u"" else expert4
                expert = u'\n'.join(name for name in [expert1, expert2, expert3, expert4] if name)
                expert = expert[:-1]

                i = table.addRow()
                table.setText(i, 0, cnt)
                table.setText(i, 1, endDate)
                table.setText(i, 2, orgName + u'\n' + personName)
                table.setText(i, 3, clientName)
                table.setText(i, 4, columnN5)
                table.setText(i, 5, birthDate)
                table.setText(i, 6, sex)
                table.setText(i, 7, socStatusWork)
                table.setText(i, 8, MKB)
                table.setText(i, 9, expertiseCharacter)
                table.setText(i, 10, u'\n'.join(name for name in [expertiseKindName, expertiseObjectName, expertNumberMCName, duration] if name))
                table.setText(i, 11, expertDeviation)
                table.setText(i, 12, expertError)
                table.setText(i, 13, expertResult)
                table.setText(i, 14, expertDecision)
                table.setText(i, 15, prevEndDate)
                table.setText(i, 16, u'\n'.join(name for name in [resultMSEName, decisionMSEName] if name))
                table.setText(i, 17, dateMSE)
                table.setText(i, 18, u'\n'.join(name for name in [reasonMSEName, restrictionMSEName, disabilityMSEName, dateLastMSEName] if name))
                table.setText(i, 19, expert)
                cnt += 1

        return doc
