# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, Qt, QVariant

from Reports.ReportPreventiveMinors import CReportPreventiveMinorsSetupDialog
from library.MapCode import createMapCodeToRowIdx
from library.database import addDateInRange
from library.Utils import forceInt, forceString

from Orgs.Utils import getOrgStructureDescendants
from Reports.Report import CReport, normalizeMKB
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat


# Редакция формы https://normativ.kontur.ru/document?moduleId=1&documentId=500959#h2314

MKBRows = [
    (u'Некоторые инфекционные и паразитарные болезни, из них:', u'1', u'A00-B99'),
    (u'туберкулез', u'1.1', u'A15-A19'),
    (u'Болезнь, вызванная вирусом иммунодефицита человека [ВИЧ]', u'1.2', u'B20-B24'),
    (u'Новообразования', u'2', u'C00-D48'),
    (u'Болезни крови и кроветворных органов и отдельные нарушения, вовлекающие иммунный механизм, из них:', u'3',
     u'D50-D89'),
    (u'анемии, связанные с питанием', u'3.1', u'D50-D53'),
    (u'Болезни эндокринной системы, расстройства питания и нарушения обмена веществ, из них:', u'4', u'E00-E90'),
    (u'сахарный диабет', u'4.1', u'E10-E14'),
    (u'недостаточность питания', u'4.2', u'E40-E46'),
    (u'ожирение', u'4.3', u'E66'),
    (u'задержка полового развития', u'4.4', u'E30.0'),
    (u'преждевременное половое созревание', u'4.5', u'E30.1'),
    (u'Психические расстройства и расстройства поведения, из них:', u'5', u'F00-F99'),
    (u'умственная отсталость', u'5.1', u'F70-F79'),
    (u'Болезни нервной системы, из них:', u'6', u'G00-G98'),
    (u'церебральный паралич и другие паралитические синдромы', u'6.1', u'G80-G83'),
    (u'Болезни глаза и его придаточного аппарата', u'7', u'H00-H59'),
    (u'Болезни уха и сосцевидного отростка', u'8', u'H60-H95'),
    (u'Болезни системы кровообращения', u'9', u'I00-I99'),
    (u'Болезни органов дыхания, из них:', u'10', u'J00-J99'),
    (u'астма, астматический статус', u'10.1', u'J45-J46'),
    (u'Болезни органов пищеварения', u'11', u'K00-K93'),
    (u'Болезни кожи и подкожной клетчатки', u'12', u'L00-L99'),
    (u'Болезни костно-мышечной системы и соединительной ткани, из них:', u'13', u'M00-M99'),
    (u'кифоз, лордоз, сколиоз', u'13.1', u'M40-M41'),
    (u'Болезни мочеполовой системы, из них:', u'14', u'N00-N99'),
    (u'болезни мужских половых органов', u'14.1', u'N40-N51'),
    (u'нарушения ритма и характера менструаций', u'14.2', u'N91-N94.5'),
    (u'воспалительные болезни женских тазовых органов', u'14.3', u'N70-N77'),
    (u'невоспалительные болезни женских половых органов', u'14.5', u'N83-N83.9'),
    (u'болезни молочной железы', u'14.5', u'N60-N64'),
    (u'Отдельные состояния, возникающие в перинатальном периоде', u'15', u'P00-P96'),
    (u'Врожденные аномалии (пороки развития), деформации и хромосомные нарушения, из них:', u'16', u'Q00-Q99'),
    (u'нервной системы', u'16.1', u'Q00-Q07'),
    (u'системы кровообращения', u'16.2', u'Q20-Q28'),
    (u'костно-мышечной системы', u'16.3', u'Q65-Q79'),
    (u'женских половых органов', u'16.4', u'Q50-Q52'),
    (u'мужских половых органов', u'16.5', u'Q53-Q55'),
    (u'Травмы, отравления и некоторые другие последствия воздействия внешних причин', u'17', u'S00-T98'),
    (u'Прочие', u'18', u''),
    (u'ВСЕГО ЗАБОЛЕВАНИЙ', u'19', u'A00-T98'),
]


def prepareBaseQuery(params, previousPeriod):
    # выборка всех действий по диспансеризации за указанный период
    # возраст пациента считается на дату диспансеризации, при отсутствии - на конец периода
    begDate = params.get('begDateBeforeRecord' if previousPeriod else 'begDate', QDate())
    endDate = params.get('endDateBeforeRecord' if previousPeriod else 'endDate', QDate())
    sex = params.get('sex', 0)
    ageFrom = params.get('ageFrom', 0)
    ageTo = params.get('ageTo', 150)
    eventPurposeId = params.get('eventPurposeId', None)
    eventTypeList = params.get('eventTypeList', [])
    orgStructureId = params.get('orgStructureId', None)
    personId = params.get('personId', None)

    db = QtGui.qApp.db
    tableClient = db.table('Client')
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    tableRmt = db.table('rbMedicalAidType')
    # tableDiagnostic = db.table('Diagnostic')
    # tableHealth = db.table('rbHealthGroup')
    tableResult = db.table('rbResult')
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tablePerson = db.table('Person')

    table = tableEvent.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
    table = table.innerJoin(tableRmt, tableRmt['id'].eq(tableEventType['medicalAidType_id']))
    table = table.leftJoin(tablePerson, tablePerson['id'].eq(tableEvent['execPerson_id']))
    table = table.leftJoin(tableResult, tableEvent['result_id'].eq(tableResult['id']))
    # table = table.leftJoin(tableHealth, tableHealth['id'].eq(tableDiagnostic['healthGroup_id']))
    # table = table.leftJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
    table = table.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    table = table.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))

    cond = [
        tableEvent['deleted'].eq(0),
        tableEventType['deleted'].eq(0),
        tableRmt['regionalCode'].inlist(('232', '252')),
        tableClient['deleted'].eq(0),
        'age(%s,  %s) BETWEEN %d AND %d' % (
            tableClient['birthDate'].name(), tableEvent['execDate'].name(), ageFrom, ageTo),
        tableAction['deleted'].eq(0),
        tableActionType['context'].like('f030-ds/y-13%'),
    ]
    addDateInRange(cond, tableEvent['execDate'], begDate, endDate)
    if eventTypeList:
        cond.append(tableEvent['eventType_id'].inlist(eventTypeList))
    elif eventPurposeId:
        cond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    if personId:
        cond.append(tableEvent['execPerson_id'].eq(personId))
    elif orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if sex:
        cond.append(tableClient['sex'].eq(sex))

    cols = [
        "COUNT(DISTINCT %s) as clientCount" % tableClient['id'].name(),
        tableClient['sex'],
    ]

    return table, cols, cond


def selectDataMKB(params):
    table, cols, cond = prepareBaseQuery(params, 0)

    db = QtGui.qApp.db
    tableAction = db.table('Action')
    tableClient = db.table('Client')
    tableEvent = db.table('Event')
    tableAP = db.table('ActionProperty')
    tableAPT = db.table('ActionPropertyType')
    tableAPM = db.table('ActionProperty_MKB')

    table = table.innerJoin(tableAP, tableAP['action_id'].eq(tableAction['id']))
    table = table.leftJoin(tableAPM, tableAPM['id'].eq(tableAP['id']))
    table = table.innerJoin(tableAPT, tableAPT['id'].eq(tableAP['type_id']))

    cond.extend([
        tableAP['deleted'].eq(0),
        tableAPT['deleted'].eq(0),
        tableAPT['shortName'].inlist(('162mkb', '163mkb', '164mkb', '165mkb', '166mkb')),
    ])

    tableAPSub = db.table('ActionProperty').alias('apS')
    tableAPTSub = db.table('ActionPropertyType').alias('aptS')
    tableAPS = db.table('ActionProperty_String')
    tableAPI = db.table('ActionProperty_Integer')
    tableVspr527 = db.table(db.db.databaseName() + '.`v1.2.643.5.1.13.13.99.2.527`')

    tableString = tableAPSub.innerJoin(tableAPTSub, tableAPTSub['id'].eq(tableAPSub['type_id']))
    tableString = tableString.innerJoin(tableAPS, tableAPS['id'].eq(tableAPSub['id']))

    tableInt = tableAPSub.innerJoin(tableAPTSub, tableAPTSub['id'].eq(tableAPSub['type_id']))
    tableInt = tableInt.innerJoin(tableAPI, tableAPI['id'].eq(tableAPSub['id']))
    tableInt = tableInt.innerJoin(tableVspr527, tableVspr527['id'].eq(tableAPI['value']))

    condSub = [
        tableAPSub['action_id'].eq(tableAction['id']),
        tableAPSub['deleted'].eq(0),
        tableAPTSub['deleted'].eq(0)
    ]

    colFirstInPeriod = """(%s) as firstInPeriod""" % db.selectStmt(tableString, u'1',
                                                                   where=condSub + [tableAPS['value'].eq(u'да'),
                                                                                    "%s = concat(SUBSTR(%s, 1, 3), '1dig')" % (
                                                                                    tableAPTSub['shortName'],
                                                                                    tableAPT['shortName'].name())],
                                                                   limit=1)
    colGetObserved = """(%s) as getObserved""" % db.selectStmt(tableInt, u'1',
                                                               where=condSub + [tableVspr527['code'].eq(u'2'),
                                                                                "%s = concat(SUBSTR(%s, 1, 3), '2ds')" % (
                                                                                tableAPTSub['shortName'],
                                                                                tableAPT['shortName'].name())], limit=1)

    colIsObserved = """(%s) as isObserved""" % db.selectStmt(tableInt, u'1',
                                                             where=condSub + [tableVspr527['code'].eq(u'1'),
                                                                              "%s = concat(SUBSTR(%s, 1, 3), '2ds')" % (
                                                                              tableAPTSub['shortName'],
                                                                              tableAPT['shortName'].name())], limit=1)

    cols.extend([
        "age({birthDate}, {execDate}) AS clientAge".format(birthDate=tableClient['birthDate'].name(),
                                                           execDate=tableEvent['execDate'].name()),
        tableAPM['value'].alias('cmkb'),
        colFirstInPeriod,
        colGetObserved,
        colIsObserved,
    ])

    return db.query(db.selectStmtGroupBy(table, cols, where=cond,
                                              group='cmkb, sex, clientAge, isObserved, getObserved, firstInPeriod'))

def selectDataAllChildren(params, previousPeriod=0):
    table, cols, cond = prepareBaseQuery(params, previousPeriod)

    begDate = params.get('begDateBeforeRecord' if previousPeriod else 'begDate', QDate())
    endDate = params.get('endDateBeforeRecord' if previousPeriod else 'endDate', QDate())

    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableResult = db.table('rbResult')
    tableClient = db.table('Client')
    tableClientSocStatus = db.table('ClientSocStatus')
    tableSocStatusClass = db.table('rbSocStatusClass')
    tableSocStatusType = db.table('rbSocStatusType')
    tableClientAttach = db.table('ClientAttach')
    tableClientAttach2 = db.table('ClientAttach').alias('CA2')
    tableAttachType = db.table('rbAttachType')

    # пациенты, подлежащие диспансеризации, но не прошедшие ее
    tableHasNotDisp = tableClient.innerJoin(tableClientSocStatus,
                                           tableClientSocStatus['client_id'].eq(tableClient['id']))
    tableHasNotDisp = tableHasNotDisp.innerJoin(tableSocStatusClass, tableSocStatusClass['id'].eq(
        tableClientSocStatus['socStatusClass_id']))
    tableHasNotDisp = tableHasNotDisp.innerJoin(tableSocStatusType, tableSocStatusType['id'].eq(
        tableClientSocStatus['socStatusType_id']))
    condHasNotDisp = [
        tableClientSocStatus['deleted'].eq(0),
        tableClientSocStatus['client_id'].eq(tableClient['id']),
        # tableSocStatusType['code'].eq('disp_d'),
        db.joinOr([tableSocStatusType['name'].like(u'%сирота%'),
                   tableSocStatusType['name'].like(u'%трудных жизненных ситуациях%'),
                   tableSocStatusType['name'].like(u'%без попечения%')]),
        db.joinOr([tableClientSocStatus['begDate'].isNull(), tableClientSocStatus['begDate'].le(endDate)]),
        db.joinOr([tableClientSocStatus['endDate'].isNull(), tableClientSocStatus['endDate'].gt(begDate)]),
        tableClient['birthDate'].le(endDate),
        "%s not in (%s)" % (tableClient['id'].name(), db.selectStmt(table, [tableClient['id'].name()], cond)),
    ]

    #проверка прикрепления для пациенты, подлежащие диспансеризации, но не прошедшие ее. копипаста
    tableAttach = tableClientAttach.leftJoin(tableAttachType, tableAttachType['id'].eq(tableClientAttach['attachType_id']))
    condAttach = [
        db.joinOr([tableClientAttach['endDate'].isNull(), tableClientAttach['endDate'].gt(begDate)]),
        db.joinOr([tableClientAttach['begDate'].isNull(), tableClientAttach['begDate'].le(endDate)]),
        u'''%s = (%s)''' % (tableClientAttach['id'].name(), db.selectStmt(
            tableClientAttach2.leftJoin(tableAttachType, tableAttachType['id'].eq(tableClientAttach2['attachType_id'])),
            "MAX(%s)" % tableClientAttach2['id'].name(),
            where=[
                tableClientAttach2['deleted'].eq(0),
                tableClientAttach2['client_id'].eq(tableClient['id']),
                tableAttachType['temporary'].eq(0)
            ])),
        tableClient['deathDate'].isNull(),
    ]
    condHasNotDisp.append(db.existsStmt(tableAttach, condAttach))

    colsHasNotDisp = []
    colsHasNotDisp.extend(cols)
    # end пациенты, подлежащие диспансеризации, но не прошедшие ее

    #формирование столбцов запроса
    tableAction= db.table('Action')
    tableAPSub = db.table('ActionProperty').alias('apS')
    tableAPTSub = db.table('ActionPropertyType').alias('aptS')
    tableAPS = db.table('ActionProperty_String')
    tableAPI = db.table('ActionProperty_Integer')
    tableVspr766 = db.table(db.db.databaseName() + '.`v1.2.643.5.1.13.13.99.2.766`')
    tableVspr982 = db.table(db.db.databaseName() + '.`v1.2.643.5.1.13.13.99.2.982`')
    tableAPD = db.table('ActionProperty_Date')

    tableString = tableAPSub.innerJoin(tableAPTSub, tableAPTSub['id'].eq(tableAPSub['type_id']))
    tableString = tableString.innerJoin(tableAPS, tableAPS['id'].eq(tableAPSub['id']))

    tableDate = tableAPSub.innerJoin(tableAPTSub, tableAPTSub['id'].eq(tableAPSub['type_id']))
    tableDate = tableDate.innerJoin(tableAPD, tableAPD['id'].eq(tableAPSub['id']))

    tableInt = tableAPSub.innerJoin(tableAPTSub, tableAPTSub['id'].eq(tableAPSub['type_id']))
    tableInt = tableInt.innerJoin(tableAPI, tableAPI['id'].eq(tableAPSub['id']))

    tableV982 = tableInt.innerJoin(tableVspr982, tableVspr982['id'].eq(tableAPI['value']))
    tableV766 = tableInt.innerJoin(tableVspr766, tableVspr766['id'].eq(tableAPI['value']))

    condSub = [
        tableAPSub['action_id'].eq(tableAction['id']),
        tableAPSub['deleted'].eq(0),
        tableAPTSub['deleted'].eq(0)
    ]

    #возраст пациента
    cols.append("age({birthDate}, {execDate}) AS clientAge".format(birthDate=tableClient['birthDate'].name(),
                                                                   execDate=tableEvent['execDate'].name()), )
    colsHasNotDisp.append("age({birthDate}, {endDate}) AS clientAge".format(birthDate=tableClient['birthDate'].name(),
                                                                            endDate=db.formatDate(endDate)), )

    #прошли проф мероприятия
    cols.append("1 as hasProf")
    colsHasNotDisp.append("0 as hasProf")

    if not previousPeriod:
        typeMO = {
            '3': tableAPS['value'].like(u'%муниципальных%'),
            '4': tableAPS['value'].like(u'%субъекта Российской Федерации%'),
            '5': tableAPS['value'].like(u'%федеральных%'),
            '6': tableAPS['value'].like(u'%частных%'),
            '7': tableAPS['value'].like(u'%санаторно%'),
        }
        condAmb = db.joinOr([tableAPS['value'].like(u'%амбулаторных%'), tableAPS['value'].like(u'%дневного%')])
        condStac = tableAPS['value'].like(u'%стационарных%')
        condYes = tableAPS['value'].like(u'%да%')

        #таблица 10 Результаты дополнительных консультаций, исследований, лечения и медицинской реабилитации детей по результатам проведения настоящей диспансеризации
        #таблица 10.1 Нуждались в дополнительных консультациях и исследованиях в амбулаторных условиях и в условиях дневного стационара.
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1623dk', '1623di', '1633dk', '1633di', '1643dk', '1643di', '1653dk', '1653di', '1663dk', '1663di'))
        for k, v in typeMO.items():
            alias = 't10_01_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condAmb, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 10.2 Прошли дополнительные консультации и исследования в амбулаторных условиях и в условиях дневного стационара
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1624dk', '1624di', '1634dk', '1634di', '1644dk', '1644di', '1654dk', '1654di', '1664dk', '1664di'))
        for k, v in typeMO.items():
            alias = 't10_02_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condAmb, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 10.3 Нуждались в дополнительных консультациях и исследованиях в стационарных условиях.
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1623dk', '1623di', '1633dk', '1633di', '1643dk', '1643di', '1653dk', '1653di', '1663dk', '1663di'))
        for k, v in typeMO.items():
            alias = 't10_03_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condStac, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 10.4 Прошли дополнительные консультации и исследования в стационарных условиях.
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1624dk', '1624di', '1634dk', '1634di', '1644dk', '1644di', '1654dk', '1654di', '1664dk', '1664di'))
        for k, v in typeMO.items():
            alias = 't10_04_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condStac, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 10.5 Рекомендовано лечение в амбулаторных условиях и в условиях дневного стационара.
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1625lnaz', '1635lnaz', '1645lnaz', '1655lnaz', '1665lnaz'))
        for k, v in typeMO.items():
            alias = 't10_05_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condAmb, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 10.6 Рекомендовано лечение в стационарных условиях.
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1625lnaz', '1635lnaz', '1645lnaz', '1655lnaz', '1665lnaz'))
        for k, v in typeMO.items():
            alias = 't10_06_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condStac, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 10.7 Рекомендована медицинская реабилитация в амбулаторных условиях и в условиях дневного стационара.
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1626mr', '1636mr', '1646mr', '1656mr', '1666mr'))
        for k, v in typeMO.items():
            alias = 't10_07_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condAmb, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 10.8 Рекомендованы медицинская реабилитация и (или) санаторно-курортное лечение в стационарных условиях.
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1626mr', '1636mr', '1646mr', '1656mr', '1666mr', '1626sl', '1636sl', '1646sl', '1656sl', '1666sl'))
        for k, v in typeMO.items():
            alias = 't10_08_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condStac, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 11. Результаты лечения, медицинской реабилитации и (или) санаторно-курортного лечения детей до проведения настоящей диспансеризации:
        #таблица 11.1 Рекомендовано лечение в амбулаторных условиях и в условиях дневного стационара.
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1522lnaz', '1532lnaz', '1542lnaz', '1552lnaz', '1562lnaz'))
        for k, v in typeMO.items():
            alias = 't11_01_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condAmb, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 11.2 Проведено лечение в амбулаторных условиях и в условиях дневного стационара <2>.
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1522lvip', '1532lvip', '1542lvip', '1552lvip', '1562lvip'))
        for k, v in typeMO.items():
            alias = 't11_02_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condAmb, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 11.3 Причины невыполнения рекомендаций по лечению в амбулаторных условиях и в условиях дневного стационара:
        #нет данных

        #таблица 11.4.Рекомендовано лечение в стационарных условиях.
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1522lnaz', '1532lnaz', '1542lnaz', '1552lnaz', '1562lnaz'))
        for k, v in typeMO.items():
            alias = 't11_04_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condStac, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 11.5 Проведено лечение в стационарных условиях <3>.
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1522lvip', '1532lvip', '1542lvip', '1552lvip', '1562lvip'))
        for k, v in typeMO.items():
            alias = 't11_05_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condStac, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 11.6.Причины невыполнения рекомендаций по лечению в стационарных условиях:
        #нет данных

        #таблица 11.7.Рекомендована медицинская реабилитация в амбулаторных условиях и в условиях дневного стационара.
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1524sannaz', '1534sannaz', '1544sannaz', '1554sannaz', '1564sannaz'))
        for k, v in typeMO.items():
            alias = 't11_07_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condAmb, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 11.8 Проведена медицинская реабилитация в амбулаторных условиях и в условиях дневного стационара <4>.
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1524sanvip', '1534sanvip', '1544sanvip', '1554sanvip', '1564sanvip'))
        for k, v in typeMO.items():
            alias = 't11_08_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condAmb, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 11.9.Причины невыполнения рекомендаций по медицинской реабилитации в амбулаторных условиях и в условиях дневного стационара:
        #нет данных

        #таблица 11.10.Рекомендованы медицинская реабилитация и (или) санаторно-курортное лечение в стационарных условиях.
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1524sannaz', '1534sannaz', '1544sannaz', '1554sannaz', '1564sannaz'))
        for k, v in typeMO.items():
            alias = 't11_10_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condStac, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 11.11 Проведена медицинская реабилитация и (или) санаторно-курортное лечение в стационарных условиях <5>.
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1524sanvip', '1534sanvip', '1544sanvip', '1554sanvip', '1564sanvip'))
        for k, v in typeMO.items():
            alias = 't11_11_%s' % k
            cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condAmb, v, condShortNames], limit=1), alias))
            colsHasNotDisp.append('0 as %s' % alias)

        #таблица 11.12.Причины невыполнения рекомендаций по медицинской реабилитации и (или) санаторно-курортному лечению в стационарных условиях:
        #нет данных

        #12.Оказание высокотехнологичной медицинской помощи:
        #12.1.рекомендована (по итогам настоящей диспансеризации): ____ чел., в том числе ____ мальчикам;
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1627vmp', '1637vmp', '1647vmp', '1657vmp', '1667vmp'))
        alias = 't12_01_2'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condYes, condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        #12.2.оказана (по итогам диспансеризации и т.п. в предыдущем году) ____ чел., в том числе ____ мальчикам.
        #цифра, теоретически, не верная, тк вмп может быть оказана, но в текущем году диспансеризация не пройдена
        condShortNames = tableAPTSub['shortName'].inlist(
            ('1526vmp', '1536vmp', '1546vmp', '1556vmp', '1566vmp'))
        alias = 't12_02_2'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [tableAPS['value'].like(u'%оказана%'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        #13.Число детей-инвалидов из числа детей, прошедших диспансеризацию в отчетном периоде.
        #13_2 с рождения
        condShortNames = tableAPTSub['shortName'].inlist(('167inv',))
        alias = 't13_01_2'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [tableAPS['value'].like(u'%с рождения%'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        # 13_3 приобретенная
        alias = 't13_01_3'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [tableAPS['value'].like(u'%приобретенная%'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        # 13_3 всего инвалидов
        alias = 't13_01_8'
        condTmp = db.joinOr([tableAPS['value'].like(u'%с рождения%'), tableAPS['value'].like(u'%приобретенная%'), condYes])
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [condTmp, condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        #13.6 установлена впервые в отчетном периоде
        condShortNames = tableAPTSub['shortName'].inlist(('167du',))
        alias = 't13_01_6'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableDate, '1', condSub + [tableAPD['value'].between(begDate, endDate), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        #14.Выполнение индивидуальных программ реабилитации (ИПР) детей-инвалидов в отчетном периоде.
        condShortNames = tableAPTSub['shortName'].inlist(('1673inv',))

        # 14_3 полностью
        alias = 't14_01_3'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [tableAPS['value'].like(u'%полностью%'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        # 14_5 частично
        alias = 't14_01_5'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [tableAPS['value'].like(u'%частично%'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        # 14_7 начато
        alias = 't14_01_7'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [tableAPS['value'].like(u'%начато%'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        # 14_9 не выполнена
        alias = 't14_01_9'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [tableAPS['value'].like(u'%не выполнена%'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        #15.Охват профилактическими прививками в отчетном периоде.
        condShortNames = tableAPTSub['shortName'].inlist(('169vac',))

        # 15_2 привит по возрасту
        alias = 't15_01_2'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [tableAPS['value'].like(u'%привит по возрасту%'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        # 15_3 не привит по медицинским показаниям: полностью
        alias = 't15_01_3'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [tableAPS['value'].like(u'%не привит по медицинским показаниям: полностью%'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        # 15_4 не привит по медицинским показаниям: частично
        alias = 't15_01_4'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [tableAPS['value'].like(u'%не привит по медицинским показаниям: частично%'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        # 15_5 не привит по другим причинам: полностью
        alias = 't15_01_5'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [tableAPS['value'].like(u'%не привит по другим причинам: полностью%'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        # 15_6 не привит по другим причинам: частично
        alias = 't15_01_6'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableString, '1', condSub + [tableAPS['value'].like(u'%не привит по другим причинам: частично%'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        # 16.Распределение детей по уровню физического развития.
        condShortNames = tableAPTSub['shortName'].inlist(('04fiz',))
        # 16_3 Нормальное физическое развитие (человек) (из графы 2)
        alias = 't16_01_3'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableV982, '1', condSub + [tableVspr982['code'].eq(u'1'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        condShortNames = tableAPTSub['shortName'].inlist(('04fizm',))
        # 16_4 дефицит массы тела
        alias = 't16_01_4'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableV982, '1', condSub + [tableVspr982['code'].eq(u'3'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        # 16_5 избыток массы тела
        alias = 't16_01_5'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableV982, '1', condSub + [tableVspr982['code'].eq(u'4'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        condShortNames = tableAPTSub['shortName'].inlist(('04fizr',))
        # 16_6 низкий рост
        alias = 't16_01_6'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableV982, '1', condSub + [tableVspr982['code'].eq(u'5'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        # 16_7 высокий рост
        alias = 't16_01_7'
        cols.append('SUM((%s)) as %s' % (db.selectStmt(tableV982, '1', condSub + [tableVspr982['code'].eq(u'6'), condShortNames], limit=1), alias))
        colsHasNotDisp.append('0 as %s' % alias)

        # #17.Распределение детей по группам состояния здоровья по рез-м дисп прошлых лет..
        # если брать с типа действия, то не учтутся пациенты, прошедшие дисп в прошлом году и не прошедшие в этом
        # condShortNames = tableAPTSub['shortName'].inlist(('157gz',))
        # # 17_3 1
        # alias = 't17_01_3'
        # cols.append('SUM((%s)) as %s' % (
        # db.selectStmt(tableV766, '1', condSub + [tableVspr766['code'].eq(u'1'), condShortNames], limit=1), alias))
        # colsHasNotDisp.append('0 as %s' % alias)
        # # 17_4 2
        # alias = 't17_01_4'
        # cols.append('SUM((%s)) as %s' % (
        # db.selectStmt(tableV766, '1', condSub + [tableVspr766['code'].eq(u'2'), condShortNames], limit=1), alias))
        # colsHasNotDisp.append('0 as %s' % alias)
        # # 17_5 3
        # alias = 't17_01_5'
        # cols.append('SUM((%s)) as %s' % (
        # db.selectStmt(tableV766, '1', condSub + [tableVspr766['code'].eq(u'5'), condShortNames], limit=1), alias))
        # colsHasNotDisp.append('0 as %s' % alias)
        # # 17_6 4
        # alias = 't17_01_6'
        # cols.append('SUM((%s)) as %s' % (
        #     db.selectStmt(tableV766, '1', condSub + [tableVspr766['code'].eq(u'6'), condShortNames], limit=1), alias))
        # colsHasNotDisp.append('0 as %s' % alias)
        # # 17_7 5
        # alias = 't17_01_7'
        # cols.append('SUM((%s)) as %s' % (
        #     db.selectStmt(tableV766, '1', condSub + [tableVspr766['code'].eq(u'7'), condShortNames], limit=1), alias))
        # colsHasNotDisp.append('0 as %s' % alias)

        #группы здоровья текущего периода
        for column, resultCode in enumerate((('347', '321'), ('348', '322'), ('349', '323'), ('350', '324'), ('351', '325')), 8):
            alias = 't17_01_%s' % column
            cols.append('SUM((%s)) as %s' % (tableResult['regionalCode'].inlist(resultCode), alias))
            colsHasNotDisp.append('0 as %s' % alias)
    if previousPeriod:
        #группы здоровья предыдущего периода
        for column, resultCode in enumerate((('347', '321'), ('348', '322'), ('349', '323'), ('350', '324'), ('351', '325')), 3):
            alias = 't17_01_%s' % column
            cols.append('SUM((%s)) as %s' % (tableResult['regionalCode'].inlist(resultCode), alias))
            colsHasNotDisp.append('0 as %s' % alias)

    group = u'sex, clientAge'
    if not previousPeriod:
        stmt = u'''%s UNION ALL %s''' % (db.selectStmtGroupBy(table, cols, cond, group=group),
                                         db.selectStmtGroupBy(tableHasNotDisp, colsHasNotDisp, condHasNotDisp, group=group))
    else:
        stmt = db.selectStmtGroupBy(table, cols, cond, group=group)
    return QtGui.qApp.db.query(stmt)


class CReport030dco13(CReport):
    ageRangesMKB = [(0, 4), (5, 9), (10, 14), (15, 17), (0, 14), (0, 17)]

    table01_02Prefix = ['t01_01', 't02_01']

    table10_11Prefix = ['t10_01', 't10_02', 't10_03', 't10_04', 't10_05', 't10_06', 't10_07', 't10_08', 't11_01', 't11_02',
                        't11_04', 't11_05', 't11_07', 't11_08', 't11_10', 't11_11']

    # 12 - ВМП
    table12Prefix = ['t12_01', 't12_02']

    # 13 - инвалиды, 14 - ИПР, 15 - проф прививки, 16 - физ разв, 17 - группы здоровья
    table13_15Prefix = ['t13_01', 't14_01', 't15_01']

    # 16 - физ разв, 17 - группы здоровья
    table16_17Prefix = ['t16_01', 't17_01']

    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Форма N 030-Д/с/о-13')
        self.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape, leftMargin=5,
                                      topMargin=5, rightMargin=5, bottomMargin=5)

    def dumpParamsMultiSelect(self, cursor, params):
        description = []
        eventTypeList = params.get('eventTypeList', None)
        if eventTypeList:
            db = QtGui.qApp.db
            tableET = db.table('EventType')
            records = db.getRecordList(tableET, [tableET['name']],
                                       [tableET['deleted'].eq(0), tableET['id'].inlist(eventTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            description.append(u'тип события:  %s' % (u','.join(name for name in nameList if name)))
        else:
            description.append(u'тип события:  не задано')
        columns = [('100%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)

    def getDescription(self, params):
        rows = CReport.getDescription(self, params)
        return rows

    def getSetupDialog(self, parent):
        result = CReportPreventiveMinorsSetupDialog(parent)
        result.setTitle(self.title())
        return result


    @staticmethod
    def calculateQueryMKB(query):
        rowMKBForCheck = MKBRows[-1]
        rowMKBForDefault = MKBRows[-2]

        mapMKBForCheck = createMapCodeToRowIdx([rowMKBForCheck[2]])
        mapMKBRows = createMapCodeToRowIdx([row[2] for row in MKBRows])
        rowSize = 8
        reportData = [[[0] * rowSize for _ in xrange(len(MKBRows))] for _ in CReport030dco13.ageRangesMKB]
        while query.next():
            record = query.record()
            mkb = normalizeMKB(forceString(record.value('cmkb')))
            # диагнозы, которые не требуется учитывать в данном разделе
            if not mapMKBForCheck.get(mkb, None):
                continue
            mkbCount = forceInt(record.value('clientCount'))
            sex = forceInt(record.value('sex'))
            age = forceInt(record.value('clientAge'))
            firstInPeriod = forceInt(record.value('firstInPeriod'))
            getObserved = forceInt(record.value('getObserved'))
            isObserved = forceInt(record.value('isObserved'))

            for idx, ages in enumerate(CReport030dco13.ageRangesMKB):
                if not ages[0] <= age <= ages[1]:
                    continue
                reportDataTable = reportData[idx]
                for row in mapMKBRows.get(mkb, [rowMKBForDefault]):
                    reportDataTable[row][0] += mkbCount
                    if firstInPeriod:
                        reportDataTable[row][2] += mkbCount
                    if isObserved:
                        reportDataTable[row][4] += mkbCount
                    if getObserved:
                        reportDataTable[row][6] += mkbCount
                    if sex == 1:
                        reportDataTable[row][1] += mkbCount
                        if firstInPeriod:
                            reportDataTable[row][3] += mkbCount
                        if isObserved:
                            reportDataTable[row][5] += mkbCount
                        if getObserved:
                            reportDataTable[row][7] += mkbCount

        return reportData

    def calculateQueryChildren(self, query, previousPeriod):
        # разделы 1, 2
        rows1_2 = [(u' всего в возрасте от 0 до 17 лет включительно: %d (человек), из них', u'.1.', 0, 17),
                   (u' в возрасте от 0 до 4 лет включительно %d (человек)', u'.1.1.', 0, 4),
                   (u' в возрасте от 5 до 9 лет включительно %d (человек),', u'.1.2.', 5, 9),
                   (u' в возрасте от 10 до 14 лет включительно %d (человек),', u'.1.3.', 10, 14),
                   (u' в возрасте от 15 до 17 лет включительно %d (человек),', u'.1.4.', 15, 17),
                   ]

        # разделы 10-15, кроме 12
        rowsAge = [(u'Всего детей в возрасте до 17 лет включительно, из них:', u'1.', 0, 17, None),
                (u'от 0 до 14 лет включительно', u'1.1', 0, 14, None),
                (u'от 0 до 4 лет включительно', u'1.1.1', 0, 4, None),
                (u'от 5 до 9 лет включительно', u'1.1.2', 5, 9, None),
                (u'от 10 до 14 лет включительно', u'1.1.3', 10, 14, None),
                (u'от 15 до 17 лет включительно', u'1.1.4', 15, 17, None),
                ]
        # разделы 12, 16, 17
        rowsAgeSex = [(u'Всего детей в возрасте до 17 лет включительно, из них:', u'1.', 0, 17, None),
                (u'от 0 до 14 лет включительно', u'1.1', 0, 14, None),
                (u'из них мальчиков', u'1.1.1', 0, 14, 1),
                (u'от 0 до 4 лет включительно', u'1.1.2', 0, 4, None),
                (u'из них мальчиков', u'1.1.2.1', 0, 4, 1),
                (u'от 5 до 9 лет включительно', u'1.1.3', 5, 9, None),
                (u'из них мальчиков', u'1.1.3.1', 5, 9, 1),
                (u'от 10 до 14 лет включительно', u'1.1.4', 10, 14, None),
                (u'из них мальчиков', u'1.1.4.1', 10, 14, 1),
                (u'от 15 до 17 лет включительно', u'1.2', 15, 17, None),
                (u'из них мальчиков', u'1.2.1', 15, 17, 1),
                ]

        for tablePref in CReport030dco13.table01_02Prefix:
            if not self.reportData.get(tablePref, None):
                self.reportData[tablePref] = [[unicode(1) + row[1]] + [row[0]] + [0] for row in rows1_2]
        maxColumnCount = 15
        for tablePref in CReport030dco13.table10_11Prefix:
            if not self.reportData.get(tablePref, None):
                self.reportData[tablePref] = [[row[1]] + [row[0]] + [0] * maxColumnCount for row in rowsAge]

        for tablePref in CReport030dco13.table12Prefix:
            if not self.reportData.get(tablePref, None):
                self.reportData[tablePref] = [[row[1]] + [row[0]] + [0] * maxColumnCount for row in rowsAgeSex]

        for tablePref in CReport030dco13.table13_15Prefix:
            if not self.reportData.get(tablePref, None):
                self.reportData[tablePref] = [[row[1]] + [row[0]] + [0] * maxColumnCount for row in rowsAge]

        for tablePref in CReport030dco13.table16_17Prefix:
            if not self.reportData.get(tablePref, None):
                self.reportData[tablePref] = [[row[1]] + [row[0]] + [0] * maxColumnCount for row in rowsAgeSex]

        prefixes = CReport030dco13.table10_11Prefix + CReport030dco13.table12Prefix + \
                   CReport030dco13.table13_15Prefix + CReport030dco13.table16_17Prefix \
            if not previousPeriod else CReport030dco13.table16_17Prefix

        while query.next():
            record = query.record()
            clientCount = forceInt(record.value('clientCount'))
            clientSex = forceInt(record.value('sex'))
            clientAge = forceInt(record.value('clientAge'))
            hasProf = forceInt(record.value('hasProf'))
            # isAttached = forceInt(record.value('isAttached'))

            # разделы 1, 2
            if not previousPeriod:
                for tablePref in CReport030dco13.table01_02Prefix:
                    # раздел2 - прошли проф мероприятия
                    if tablePref == 't02_01' and not hasProf:
                        continue
                    # Раздел 1 Собирается только по прикрепленному населению
                    # if idxTable == 0 and not isAttached:
                    #     continue
                    reportLine = self.reportData.get(tablePref, None)
                    for idxRow, row in enumerate(rows1_2):
                        if row[2] <= clientAge <= row[3]:
                            reportLine[idxRow][2] += clientCount

            if hasProf:
                for tablePref in CReport030dco13.table16_17Prefix:
                    # всего прошли дисп с разбивкой по полу для таблиц 16, 17
                    reportLine = self.reportData.get(tablePref, None)
                    for idxRow, row in enumerate(rowsAgeSex):
                        if row[4] is not None and row[4] != clientSex:
                            continue
                        if row[2] <= clientAge <= row[3]:
                            reportLine[idxRow][2] += clientCount

            # раздел 3 - отсутствуют данные
            # разделы 4 - 9 формируются в calculateQueryMKB

            # разделы с 10 до конца
            for i in range(record.count()):
                recField = record.field(i)
                recValue = forceInt(recField.value())
                if not recValue:
                    continue
                fieldName = forceString(recField.name())
                tablePref = fieldName[:6]
                if tablePref in prefixes:
                    reportLine = self.reportData.get(tablePref, None)
                    if reportLine is None:
                        continue
                    column = forceInt(fieldName[7:])
                    rows = rowsAgeSex if tablePref in CReport030dco13.table16_17Prefix else rowsAge
                    for idx, row in enumerate(rows):
                        if row[4] is not None and row[4] != clientSex:
                            continue
                        if row[2] <= clientAge <= row[3]:
                            reportLine[idx][column] += recValue
                            if tablePref in CReport030dco13.table10_11Prefix:
                                # всего
                                reportLine[idx][2] += recValue


    def build(self, params):
        query = selectDataMKB(params)
        MKBData = CReport030dco13.calculateQueryMKB(query)

        self.reportData = {}

        query = selectDataAllChildren(params, 0)
        self.calculateQueryChildren(query, 0)

        query = selectDataAllChildren(params, 1)
        self.calculateQueryChildren(query, 1)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        self.produceReportHeader(cursor, params)
        self.produceSection1(cursor)
        self.produceSection2(cursor)
        self.produceSection3(cursor)
        self.produceSection4_9(cursor, MKBData)
        self.produceSection10(cursor)
        self.produceSection11(cursor)
        self.produceSection12(cursor)
        self.produceSection13(cursor)
        self.produceSection14(cursor)
        self.produceSection15(cursor)
        self.produceSection16(cursor)
        self.produceSection17(cursor)
        self.produceReportFooter(cursor)

        return doc

    def produceReportHeader(self, cursor, params):
        from Registry.Utils import formatAddress

        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock(CReportBase.AlignCenter)
        cursor.insertText(u'СВЕДЕНИЯ О ДИСПАНСЕРИЗАЦИИ ПРЕБЫВАЮЩИХ В СТАЦИОНАРНЫХ УЧРЕЖДЕНИЯХ ДЕТЕЙ-СИРОТ И ДЕТЕЙ, НАХОДЯЩИХСЯ В ТРУДНОЙ ЖИЗНЕННОЙ СИТУАЦИИ\n '
                          u'за период %s-%s' % (params.get('begDate', QDate()).toString('dd.MM.yyyy'),
                                                params.get('endDate', QDate()).toString('dd.MM.yyyy')))
        cursor.insertBlock()
        cursor.insertBlock()

        bfAlignLeftTop = QtGui.QTextBlockFormat()
        bfAlignLeftTop.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        table = createTable(cursor, [('70%', [], CReportBase.AlignLeft), ('10%', [], CReportBase.AlignLeft),
                                     ('20%', [], CReportBase.AlignCenter)], headerRowCount=4, border=0, cellPadding=2,
                            cellSpacing=0)

        table.mergeCells(0, 0, 4, 1)
        cursorAt = table.cursorAt(0, 0)
        tmpTable = createTable(cursorAt, [('70%', [], CReportBase.AlignCenter), ('30%', [], CReportBase.AlignCenter)],
                               headerRowCount=2, border=1, cellPadding=2, cellSpacing=0)
        tmpTable.setText(0, 0, u'Представляют')
        tmpTable.setText(0, 1, u'Сроки представления')
        tmpTable.setText(1, 0,
                         u'\n\nМедицинские организации, проводившие диспансеризацию несовершеннолетних:\n\n- в орган исполнительной власти субъекта Российской Федерации в сфере здравоохранения\n\n\n Орган исполнительной власти субъекта Российской Федерации в сфере здравоохранения:\n\n - в Минздрав России\n\n',
                         blockFormat=bfAlignLeftTop)
        tmpTable.setText(1, 1, u'\n\n\nЕжегодно\n\nдо 20 января\n\n\nЕжегодно\n\nдо 15 февраля\n')
        cursorAt.insertBlock()
        cursorAt = table.cursorAt(0, 2)
        tmpTable = createTable(cursorAt, [('100%', [], CReportBase.AlignCenter)],
                               headerRowCount=1, border=2, cellPadding=2, cellSpacing=0)
        tmpTable.setText(0, 0, u'\nФорма N 030/о-Д/с\n', CReportBase.TableHeader)

        cursorAt = table.cursorAt(0, 2)
        tmpTable = createTable(cursorAt, [('100%', [], CReportBase.AlignCenter)],
                               headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)
        tmpTable.setText(0, 0, u'\nУтверждена приказом\nМинздрава России\nот "14" апреля 2025 г. № 212н\n')

        cursorAt = table.cursorAt(0, 2)
        tmpTable = createTable(cursorAt, [('100%', [], CReportBase.AlignCenter)],
                               headerRowCount=1, border=2, cellPadding=2, cellSpacing=0)
        tmpTable.setText(0, 0, u'Ежегодная')

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertBlock()

        table = createTable(cursor, [('100%', [], CReportBase.AlignLeft)], headerRowCount=2, border=2, cellPadding=2,
                            cellSpacing=0)

        orgRec = QtGui.qApp.db.getRecordEx('Organisation', 'fullName, Address, address_id', 'id=%d' % QtGui.qApp.currentOrgId())
        if orgRec:
            table.setHtml(0, 0,
                          u'Наименование отчитывающейся организации <u><b>%s</b></u>' % forceString(orgRec.value('fullName')))
            address_id = forceInt(orgRec.value('address_id'))
            table.setHtml(1, 0,
                          u'Почтовый адрес <u><b>%s</b></u>' % formatAddress(address_id) if address_id else forceString(
                              orgRec.value('Address')))

        cursor.movePosition(QtGui.QTextCursor.End)

        pageBreakBlockFormat = QtGui.QTextBlockFormat()
        pageBreakBlockFormat.setPageBreakPolicy(QtGui.QTextFormat.PageBreak_AlwaysBefore)
        cursor.insertBlock(pageBreakBlockFormat)
        cursor.insertBlock(QtGui.QTextBlockFormat())

    def produceSection1(self, cursor):
        tableData = self.reportData.get('t01_01')
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(
            u'1. Число несовершеннолетних (далее - дети), подлежащих диспансеризации в отчетном периоде:')
        cursor.insertBlock()

        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        self.produceSection1_2(cursor, tableData)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

    def produceSection2(self, cursor):
        tableData = self.reportData.get('t02_01')
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(
            u'2. Число детей прошедших диспансеризацию в отчетном периоде (от п. 1.):')
        cursor.insertBlock()

        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        self.produceSection1_2(cursor, tableData)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

    def produceSection1_2(self, cursor, sectionData):
        for idx in range(len(sectionData)):
            cursor.insertText(sectionData[idx][0] + sectionData[idx][1] % sectionData[idx][2])
            cursor.insertBlock()

    def produceSection3(self, cursor):
        sectionData1 = self.reportData.get('t01_01')
        sectionData2 = self.reportData.get('t02_01')
        # информация в БД отсутствует
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'3. Причины невыполнения плана диспансеризации в отчетном периоде:')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        # cursor.insertText(u'3.1 всего не прошли ____ (человек), ______ (удельный вес от п. 1.1.), из них:')
        cursor.insertText(u'3.1 всего не прошли ____%d (человек), ______%.2f (удельный вес от п. 1.1.), из них:' % (
        sectionData1[0][2] - sectionData2[1][2],
        sectionData1[0][2] - sectionData2[1][2] / sectionData1[0][2] * 100 if sectionData1[0][2] else 0))
        cursor.insertBlock()
        cursor.insertText(u'3.1.1 не явились ______ (человек), ________ (удельный вес от п. 3.1.);')
        cursor.insertBlock()
        cursor.insertText(u'3.1.2 отказались от медицинского вмешательства ____________ (человек), ___________ (удельный вес от п. 3.1.);')
        cursor.insertBlock()
        cursor.insertText(u'3.1.3 смена места жительства _______ (человек), ________ (удельный вес от п. 3.1.);')
        cursor.insertBlock()
        cursor.insertText(u'3.1.4 не в полном объеме ______ (человек), _____________ (удельный вес от п. 3.1.);')
        cursor.insertBlock()
        cursor.insertText(u'3.1.5 проблемы организации медицинской помощи _____________ (человек), ___________ (удельный вес от п. 3.1.);')
        cursor.insertBlock()
        cursor.insertText(u'3.1.6 прочие (указать причину, сколько человек):')
        cursor.insertBlock()
        cursor.insertText(u'3.1.6.1 ________ (причина) _______ (человек), _________ (удельный вес от п. 3.1.),')
        cursor.insertBlock()
        cursor.insertText(u'3.1.6.2 ________ (причина) _______ (человек), _________ (удельный вес от п. 3.1.) и т.д.')
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

    def produceSection4_9(self, cursor, sectionData):
        counter = 4
        for idxTable, age in enumerate(CReport030dco13.ageRangesMKB):
            cursor.setCharFormat(CReportBase.ReportSubTitle)
            cursor.insertText(
                u'%d. Структура выявленных заболеваний (состояний) у детей в возрасте от %d до %d лет включительно' % (
                counter, age[0], age[1]))
            cursor.insertBlock()
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            tableColumns = [
                ('5%', [u'N п/п', u'', u'1'], CReportBase.AlignLeft),
                (
                '32%', [u'Наименование заболеваний (по классам и отдельным нозологиям)', u'', u'2'], CReportBase.AlignLeft),
                ('7%', [u'Код по МКБ', u'', u'3'], CReportBase.AlignCenter),
                ('7%', [u'Всего зарегистрировано заболеваний', u'', u'4'], CReportBase.AlignCenter),
                ('7%', [u'из них у мальчиков (из графы 4)', u'', u'5'], CReportBase.AlignCenter),
                ('7%', [u'Выявлено впервые (из графы 4)', u'', u'6'], CReportBase.AlignCenter),
                ('7%', [u'из них у мальчиков (из графы 6)', u'', u'7'], CReportBase.AlignCenter),
                ('7%', [u'Состоит под диспансерным наблюдением на конец отчетного периода', u'Всего', u'8'],
                 CReportBase.AlignCenter),
                ('7%', [u'', u'из них мальчиков (из графы 8)', u'9'], CReportBase.AlignCenter),
                ('7%', [u'', u'Взято по результатам данной диспансеризации (из графы 8)', u'10'], CReportBase.AlignCenter),
                ('7%', [u'', u'из них мальчиков (из графы 10)', u'11'], CReportBase.AlignCenter),
            ]
            table = createTable(cursor, tableColumns)
            table.mergeCells(0, 7, 1, 4)
            for idx in range(7):
                table.mergeCells(0, idx, 2, 1)

            offset = 3
            for idxRow, row in enumerate(sectionData[idxTable]):
                i = table.addRow()
                table.setText(i, 0, MKBRows[idxRow][1])
                table.setText(i, 1, MKBRows[idxRow][0])
                table.setText(i, 2, MKBRows[idxRow][2])
                for idx in xrange(offset, len(tableColumns)):
                    table.setText(i, idx, row[idx - offset] if row[idx - offset] else '')

            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()

            counter += 1

    def produceSection10(self, cursor):
        sectionTitle = [
            (u'10.',
             u'Результаты дополнительных консультаций, исследований, лечения и медицинской реабилитации детей по результатам проведения настоящей диспансеризации:', None, None),
            (u'10.1.',
             u'Нуждались в дополнительных консультациях и исследованиях в амбулаторных условиях и в условиях дневного стационара', 0, self.produceSections10and11),
            (u'10.2.',
             u'Прошли дополнительные консультации и исследования в амбулаторных условиях и в условиях дневного стационара', 0, self.produceSection10and11Percent),
            (u'10.3.',
             u'Нуждались в дополнительных консультациях и исследованиях в стационарных условиях', 0, self.produceSections10and11),
            (u'10.4.',
             u'Прошли дополнительные консультации и исследования в стационарных условиях', 0, self.produceSection10and11Percent),
            (u'10.5.',
             u'Рекомендовано лечение в амбулаторных условиях и в условиях дневного стационара', 0, self.produceSections10and11),
            (u'10.6.',
             u'Рекомендовано лечение в стационарных условиях', 1, self.produceSections10and11),
            (u'10.7.',
             u'Рекомендована медицинская реабилитация в амбулаторных условиях и в условиях дневного стационара', 0, self.produceSections10and11),
            (u'10.8.',
             u'Рекомендованы медицинская реабилитация и (или) санаторно-курортное лечение в стационарных условиях', 1, self.produceSections10and11),
        ]

        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'%s %s' % (sectionTitle[0][0], sectionTitle[0][1]))
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        for idx in range(1, len(sectionTitle)):
            cursor.insertText(u'%s %s (человек)' % (sectionTitle[idx][0], sectionTitle[idx][1]))
            cursor.insertBlock()
            if callable(sectionTitle[idx][3]):
                sectionTitle[idx][3](cursor, 't10_%02.d' % idx, sectionTitle[idx])


    def produceSections10and11(self, cursor, tablePref, sectionTitle):
        tableData = self.reportData.get(tablePref)
        tableColumns = [
            ('8%', [u'N п/п', u'', u''], CReportBase.AlignLeft),
            ('32%', [u'Возраст детей', u'', u'1'], CReportBase.AlignLeft),
            ('12%', [u'%s' % sectionTitle[1], u'Всего', u'2'], CReportBase.AlignCenter),
            ('12%', [u'', u'в муниципальных медицинских организациях', u'3'], CReportBase.AlignCenter),
            ('12%', [u'', u'в государственных (субъекта Российской Федерации) медицинских организациях', u'4'], CReportBase.AlignCenter),
            ('12%', [u'', u'в государственных (федеральных) медицинских организациях', u'5'], CReportBase.AlignCenter),
            ('12%', [u'', u'в частных медицинских организациях', u'6'], CReportBase.AlignCenter),
        ]
        if sectionTitle[2]:
            tableColumns.append(('12%', [u'', u'в санаторно-курортных организациях', u'7'], CReportBase.AlignCenter),)
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 1, len(tableColumns)-2)

        for idxRow, row in enumerate(tableData):
            i = table.addRow()
            for idxColumn, column in enumerate(tableData[idxRow]):
                if idxColumn >= len(tableColumns):
                    break
                table.setText(i, idxColumn, tableData[idxRow][idxColumn])

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

    def produceSection10and11Percent(self, cursor, tablePref, sectionTitle):
        tableData = self.reportData.get(tablePref)

        tableNumber = forceInt(tablePref[1:3])
        tableNumberPrev = forceInt(tablePref[-1:]) - 1
        tablePrefPrevious = tablePref[:-1] + unicode(tableNumberPrev)
        tableDataPrevious = self.reportData.get(tablePrefPrevious)

        tableColumns = [
            ('8%', [u'N п/п', u'', u'', u''], CReportBase.AlignLeft),
            ('32%', [u'Возраст детей', u'', u'', u'1'], CReportBase.AlignLeft),
            ('6%', [u'%s' % sectionTitle[1], u'Всего', u'абс.', u'2'], CReportBase.AlignCenter),
            ('6%', [u'', u'', u'%% (из гр. 2 п. %d.%d)'% (tableNumber, tableNumberPrev), u'3'], CReportBase.AlignCenter),
            ('6%', [u'', u'в муниципальных медицинских организациях', u'абс.', u'4'], CReportBase.AlignCenter),
            ('6%', [u'', u'', u'%% (из гр. 3 п. %d.%d)'% (tableNumber, tableNumberPrev), u'5'], CReportBase.AlignCenter),
            ('6%', [u'', u'в государственных (субъекта Российской Федерации) медицинских организациях', u'абс.', u'6'], CReportBase.AlignCenter),
            ('6%', [u'', u'', u'%% (из гр. 4 п. %d.%d)'% (tableNumber, tableNumberPrev), u'7'], CReportBase.AlignCenter),
            ('6%', [u'', u'в государственных (федеральных) медицинских организациях', u'абс.', u'8'], CReportBase.AlignCenter),
            ('6%', [u'', u'', u'%% (из гр. 5 п. %d.%d)'% (tableNumber, tableNumberPrev), u'9'], CReportBase.AlignCenter),
            ('6%', [u'', u'в частных медицинских организациях', u'абс.', u'10'], CReportBase.AlignCenter),
            ('6%', [u'', u'', u'%% (из гр. 6 п. %d.%d)'% (tableNumber, tableNumberPrev), u'11'], CReportBase.AlignCenter),
        ]
        if sectionTitle[2]:
            tableColumns.append(('6%', [u'', u'в санаторно-курортных организациях', u'12'], CReportBase.AlignCenter),)
            tableColumns.append(('6%', [u'', u'', u'%% (из гр. 6 п. %d.%d)'% (tableNumber, tableNumberPrev), u'13'], CReportBase.AlignCenter),)
            
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 4, 1)
        table.mergeCells(0, 1, 3, 1)
        table.mergeCells(0, 2, 1, len(tableColumns)-2)
        table.mergeCells(1, 2, 1, 2)
        table.mergeCells(1, 4, 1, 2)
        table.mergeCells(1, 6, 1, 2)
        table.mergeCells(1, 8, 1, 2)
        table.mergeCells(1, 10, 1, 2)

        for idxRow, row in enumerate(tableData):
            i = table.addRow()
            table.setText(i, 0, tableData[idxRow][0])
            table.setText(i, 1, tableData[idxRow][1])
            table.setText(i, 2, tableData[idxRow][2])
            table.setText(i, 3, tableData[idxRow][2] * 100 / tableDataPrevious[idxRow][2] if tableDataPrevious[idxRow][2] else 0)
            table.setText(i, 4, tableData[idxRow][3])
            table.setText(i, 5, tableData[idxRow][3] * 100 / tableDataPrevious[idxRow][3] if tableDataPrevious[idxRow][3] else 0)
            table.setText(i, 6, tableData[idxRow][4])
            table.setText(i, 7, tableData[idxRow][4] * 100 / tableDataPrevious[idxRow][4] if tableDataPrevious[idxRow][4] else 0)
            table.setText(i, 8, tableData[idxRow][5])
            table.setText(i, 9, tableData[idxRow][5] * 100 / tableDataPrevious[idxRow][5] if tableDataPrevious[idxRow][5] else 0)
            table.setText(i, 10, tableData[idxRow][6])
            table.setText(i, 11, tableData[idxRow][6] * 100 / tableDataPrevious[idxRow][6] if tableDataPrevious[idxRow][6] else 0)
            if sectionTitle[2]:
                table.setText(i, 12, tableData[idxRow][7])
                table.setText(i, 13, tableData[idxRow][7] * 100 / tableDataPrevious[idxRow][7] if tableDataPrevious[idxRow][7] else 0)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

    def produceSection11(self, cursor):
        sectionTitle = [
            (u'11.',
             u'Результаты лечения, медицинской реабилитации и (или) санаторно-курортного лечения детей до проведения настоящей диспансеризации:', None, None),
            (u'11.1.',
             u'Рекомендовано лечение в амбулаторных условиях и в условиях дневного стационара', 0, self.produceSections10and11),
            (u'11.2.',
             u'Проведено лечение в амбулаторных условиях и в условиях дневного стационара', 0, self.produceSections10and11),
            (u'11.3.',
             u'Причины невыполнения рекомендаций по лечению в амбулаторных условиях и в условиях дневного стационара', 0, self.produceSection11NonCompliance),
            (u'11.4.',
             u'Рекомендовано лечение в стационарных условиях', 0, self.produceSections10and11),
            (u'11.5.',
             u'Проведено лечение в стационарных условиях', 1, self.produceSection10and11Percent),
            (u'11.6.',
             u'Причины невыполнения рекомендаций по лечению в стационарных условиях:', 0, self.produceSection11NonCompliance),
            (u'11.7.',
             u'Рекомендована медицинская реабилитация в амбулаторных условиях и в условиях дневного стационара', 0, self.produceSections10and11),
            (u'11.8.',
             u'Проведена медицинская реабилитация в амбулаторных условиях и в условиях дневного стационара', 0, self.produceSection10and11Percent),
            (u'11.9.',
             u'Причины невыполнения рекомендаций по медицинской реабилитации в амбулаторных условиях и в условиях дневного стационара:', 0, self.produceSection11NonCompliance),
            (u'11.10.',
             u'Рекомендованы медицинская реабилитация и (или) санаторно-курортное лечение в стационарных условиях', 0,
             self.produceSections10and11),
            (u'11.11.',
             u'Проведена медицинская реабилитация и (или) санаторно-курортное лечение в стационарных условиях', 1,
             self.produceSections10and11),
            (u'11.12.',
             u'Причины невыполнения рекомендаций по медицинской реабилитации и (или) санаторно-курортному лечению в стационарных условиях',
             0, self.produceSection11NonCompliance),
        ]

        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'%s %s' % (sectionTitle[0][0], sectionTitle[0][1]))
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        for idx in range(1, len(sectionTitle)):
            cursor.insertText(u'%s %s (человек)' % (sectionTitle[idx][0], sectionTitle[idx][1]))
            cursor.insertBlock()
            if callable(sectionTitle[idx][3]):
                sectionTitle[idx][3](cursor, 't11_%02.d' % idx, sectionTitle[idx])

    def produceSection11NonCompliance(self, cursor, tablePref, sectionTitle):
        tableNumber = forceInt(tablePref[-1:])
        tableDataRecomend = self.reportData.get(tablePref[:-1] + unicode(tableNumber-2))
        tableDataCompliance = self.reportData.get(tablePref[:-1] + unicode(tableNumber-1))

        cursor.insertText(u'%s        не прошли всего _________%d (человек), из них:' % (
        sectionTitle[0] + '1.', tableDataRecomend[0][2] - tableDataCompliance[0][2]))
        cursor.insertBlock()
        cursor.insertText(u'%s     не явились ______ (человек);'% (sectionTitle[0]+'1.1.'))
        cursor.insertBlock()
        cursor.insertText(u'%s     отказались от медицинского вмешательства ____________ (человек);'% (sectionTitle[0]+'1.2.'))
        cursor.insertBlock()
        cursor.insertText(u'%s     смена места жительства _______ (человек);'% (sectionTitle[0]+'1.3.'))
        cursor.insertBlock()
        cursor.insertText(u'%s     не в полном объеме ______ (человек);'% (sectionTitle[0]+'1.4.'))
        cursor.insertBlock()
        cursor.insertText(u'%s     проблемы организации медицинской помощи _____________ (человек);'% (sectionTitle[0]+'1.5.'))
        cursor.insertBlock()
        cursor.insertText(u'%s     прочие (указать причину, сколько человек):'% (sectionTitle[0]+'1.6.'))
        cursor.insertBlock()
        cursor.insertText(u'%s  ________ (причина) _______ (человек);'% (sectionTitle[0]+'1.6.1.'))
        cursor.insertBlock()
        cursor.insertText(u'%s  ________ (причина) _______ (человек) и т.д.'% (sectionTitle[0]+'1.6.2.'))
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()


    def produceSection12(self, cursor):
        tableData12_1 = self.reportData.get('t12_01')
        tableData12_2 = self.reportData.get('t12_02')

        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'12.   Оказание высокотехнологичной медицинской помощи:')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        cursor.insertText(
            u'12.1  рекомендована (по итогам настоящей диспансеризации): ____%d чел., в том числе ____%d мальчикам;' % (
            tableData12_1[1][2] + tableData12_1[9][2], tableData12_1[2][2] + tableData12_1[10][2]))
        cursor.insertBlock()
        cursor.insertText(
            u'12.2  оказана (по итогам диспансеризации и т.п. в предыдущем году) ____%d чел., в том числе ____%d мальчикам.' % (
            tableData12_2[1][2] + tableData12_2[9][2], tableData12_2[2][2] + tableData12_2[10][2]))
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

    def produceSection13(self, cursor):
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'13.   Число детей-инвалидов из числа детей, прошедших диспансеризацию в отчетном периоде.')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

        tableData = self.reportData.get('t13_01')
        tableData1 = self.reportData.get('t02_01')

        tableColumns = [
            ('8%', [u'N п/п', u'', u'', u'', u''], CReportBase.AlignLeft),
            ('32%', [u'Возраст детей', u'', u'', u'', u'1'], CReportBase.AlignLeft),
            ('8%', [u'Инвалидность', u'установлена до проведения настоящего профилактического медицинского осмотра', u'с рождения', u'всего (человек)', u'2'], CReportBase.AlignCenter),
            ('8%', [u'', u'', u'', u'процент от общего числа прошедших профилактические медицинские осмотры', u'3'], CReportBase.AlignCenter),
            ('8%', [u'', u'', u'приобретенная', u'всего (человек)', u'4'], CReportBase.AlignCenter),
            ('8%', [u'', u'', u'', u'процент от общего числа прошедших профилактические медицинские осмотры', u'5'], CReportBase.AlignCenter),
            ('8%', [u'', u'установлена впервые в отчетном периоде',
                    u'', u'всего (человек)', u'6'], CReportBase.AlignCenter),
            ('8%', [u'', u'', u'', u'процент от общего числа прошедших профилактические медицинские осмотры', u'7'],
             CReportBase.AlignCenter),
            ('8%', [u'', u'всего детей-инвалидов (человек)', u'', u'', u'8'],
             CReportBase.AlignCenter),
            ('8%', [u'', u'процент детей-инвалидов от общего числа прошедших профилактические медицинские осмотры', u'', u'', u'9'],
             CReportBase.AlignCenter),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 5, 1)
        table.mergeCells(0, 1, 4, 1)
        table.mergeCells(0, 2, 1, len(tableColumns) - 2)
        table.mergeCells(1, 2, 1, 4)
        table.mergeCells(1, 6, 1, 2)
        table.mergeCells(2, 2, 1, 2)
        table.mergeCells(2, 4, 1, 2)
        table.mergeCells(1, 8, 2, 1)
        table.mergeCells(1, 9, 2, 1)

        for idxRow, row in enumerate(tableData):
            i = table.addRow()
            table.setText(i, 0, tableData[idxRow][0])
            table.setText(i, 1, tableData[idxRow][1])
            table.setText(i, 2, tableData[idxRow][2])
            table.setText(i, 3, tableData[idxRow][2] * 100 / tableData1[0][2] if tableData1[0][2] else 0)
            table.setText(i, 4, tableData[idxRow][3])
            table.setText(i, 5, tableData[idxRow][3] * 100 / tableData1[0][2] if tableData1[0][2] else 0)
            table.setText(i, 6, tableData[idxRow][4])
            table.setText(i, 7, tableData[idxRow][4] * 100 / tableData1[0][2] if tableData1[0][2] else 0)
            totalCount = tableData[idxRow][2] + tableData[idxRow][3]
            table.setText(i, 8, totalCount)
            table.setText(i, 9, totalCount * 100 / tableData1[0][2] if tableData1[0][2] else 0)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

    def produceSection14(self, cursor):
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'14.   Выполнение индивидуальных программ реабилитации (ИПР) детей-инвалидов в отчетном периоде.')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

        tableData = self.reportData.get('t14_01')

        tableColumns = [
            ('8%', [u'N п/п', u'', u''], CReportBase.AlignLeft),
            ('32%', [u'Возраст детей', u'', u'1'], CReportBase.AlignLeft),
            ('7%', [u'Назначено ИПР', u'всего (человек)', u'2'], CReportBase.AlignCenter),
            ('7%', [u'ИПР выполнена полностью', u'всего (человек)', u'3'], CReportBase.AlignCenter),
            ('7%', [u'', u'процент от назначенного (%)', u'4'], CReportBase.AlignCenter),
            ('7%', [u'ИПР выполнена частично', u'всего (человек)', u'5'], CReportBase.AlignCenter),
            ('7%', [u'', u'процент от назначенного (%)', u'6'], CReportBase.AlignCenter),
            ('7%', [u'ИПР начата', u'всего (человек)', u'7'], CReportBase.AlignCenter),
            ('7%', [u'', u'процент от назначенного (%)', u'8'], CReportBase.AlignCenter),
            ('7%', [u'ИПР не выполнена', u'всего (человек)', u'9'], CReportBase.AlignCenter),
            ('7%', [u'', u'процент от назначенного (%)', u'10'], CReportBase.AlignCenter),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 3, 1, 2)
        table.mergeCells(0, 5, 1, 2)
        table.mergeCells(0, 7, 1, 2)
        table.mergeCells(0, 9, 1, 2)

        for idxRow, row in enumerate(tableData):
            i = table.addRow()
            table.setText(i, 0, tableData[idxRow][0])
            table.setText(i, 1, tableData[idxRow][1])
            table.setText(i, 2, tableData[idxRow][2])
            table.setText(i, 3, tableData[idxRow][3])
            table.setText(i, 4, tableData[idxRow][2] * 100 / tableData[idxRow][2] if tableData[idxRow][2] else 0)
            table.setText(i, 5, tableData[idxRow][5])
            table.setText(i, 6, tableData[idxRow][5] * 100 / tableData[idxRow][2] if tableData[idxRow][2] else 0)
            table.setText(i, 7, tableData[idxRow][7])
            table.setText(i, 8, tableData[idxRow][7] * 100 / tableData[idxRow][2] if tableData[idxRow][2] else 0)
            table.setText(i, 9, tableData[idxRow][9])
            table.setText(i, 10, tableData[idxRow][9] * 100 / tableData[idxRow][2] if tableData[idxRow][2] else 0)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

    def produceSection15(self, cursor):
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'15.   Охват профилактическими прививками в отчетном периоде.')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

        tableData = self.reportData.get('t15_01')

        tableColumns = [
            ('8%', [u'N п/п', u'', u''], CReportBase.AlignLeft),
            ('32%', [u'Возраст детей', u'', u'1'], CReportBase.AlignLeft),
            ('12%', [u'Привито в соответствии с национальным календарем профилактических прививок <6> (человек)', u'', u'2'], CReportBase.AlignCenter),
            ('12%', [u'Не привиты по медицинским показаниям', u'полностью (человек)', u'3'], CReportBase.AlignCenter),
            ('12%', [u'', u'частично (человек)', u'4'], CReportBase.AlignCenter),
            ('12%', [u'Не привиты по другим причинам', u'полностью (человек)', u'5'], CReportBase.AlignCenter),
            ('12%', [u'', u'частично (человек)', u'6'], CReportBase.AlignCenter),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 2)
        table.mergeCells(0, 5, 1, 2)

        for idxRow, row in enumerate(tableData):
            i = table.addRow()
            for idxColumn, column in enumerate(tableData[idxRow]):
                if idxColumn >= len(tableColumns):
                    break
                table.setText(i, idxColumn, tableData[idxRow][idxColumn])

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

    def produceSection16(self, cursor):
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'16.   Распределение детей по уровню физического развития.')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

        tableData = self.reportData.get('t16_01')

        tableColumns = [
            ('8%', [u'N п/п', u'', u''], CReportBase.AlignLeft),
            ('32%', [u'Возраст детей', u'', u'1'], CReportBase.AlignLeft),
            ('10%', [u'Число прошедших диспансеризацию в отчетном периоде (человек)', u'', u'2'], CReportBase.AlignCenter),
            ('10%', [u'Нормальное физическое развитие (человек) (из графы 2)', u'', u'3'], CReportBase.AlignCenter),
            ('10%', [u'Отклонения физического развития (человек) (из графы 2)', u'дефицит массы тела', u'4'], CReportBase.AlignCenter),
            ('10%', [u'', u'избыток массы тела', u'5'], CReportBase.AlignCenter),
            ('10%', [u'', u'низкий рост', u'6'], CReportBase.AlignCenter),
            ('10%', [u'', u'высокий рост', u'7'], CReportBase.AlignCenter),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 2, 1)
        table.mergeCells(0, 4, 1, 4)

        for idxRow, row in enumerate(tableData):
            i = table.addRow()
            for idxColumn, column in enumerate(tableData[idxRow]):
                if idxColumn >= len(tableColumns):
                    break
                table.setText(i, idxColumn, tableData[idxRow][idxColumn])

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()


    def produceSection17(self, cursor):
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'17.   Распределение детей по группам состояния здоровья.')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

        tableData = self.reportData.get('t17_01')

        tableColumns = [
            ('8%', [u'N п/п', u'', u'', u''], CReportBase.AlignLeft),
            ('32%', [u'Возраст детей', u'', u'', u'1'], CReportBase.AlignLeft),
            ('6%', [u'Число прошедших диспансеризацию в отчетном периоде (человек)', u'', u'2'], CReportBase.AlignCenter),
            ('6%', [u'Группы состояния здоровья',
                    u'По результатам профилактических медицинских осмотров и диспансеризации в предыдущем отчетном периоде',
                    u'I', u'3'], CReportBase.AlignCenter),
            ('6%', [u'', u'', u'II', u'4'], CReportBase.AlignCenter),
            ('6%', [u'', u'', u'III', u'5'], CReportBase.AlignCenter),
            ('6%', [u'', u'', u'IV', u'6'], CReportBase.AlignCenter),
            ('6%', [u'', u'', u'V', u'7'], CReportBase.AlignCenter),
            ('6%', [u'', u'По результатам диспансеризации в данном отчетном периоде', u'I', u'8'],
             CReportBase.AlignCenter),
            ('6%', [u'', u'', u'II', u'9'], CReportBase.AlignCenter),
            ('6%', [u'', u'', u'III', u'10'], CReportBase.AlignCenter),
            ('6%', [u'', u'', u'IV', u'11'], CReportBase.AlignCenter),
            ('6%', [u'', u'', u'V', u'12'], CReportBase.AlignCenter),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 4, 1)
        table.mergeCells(0, 1, 3, 1)
        table.mergeCells(0, 2, 3, 1)
        table.mergeCells(0, 3, 1, len(tableColumns)-3)
        table.mergeCells(1, 3, 1, 5)
        table.mergeCells(1, 8, 1, 5)

        for idxRow, row in enumerate(tableData):
            i = table.addRow()
            for idxColumn, column in enumerate(tableData[idxRow]):
                if idxColumn >= len(tableColumns):
                    break
                table.setText(i, idxColumn, tableData[idxRow][idxColumn])

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

    def produceReportFooter(self, cursor):
        cursor.insertHtml(u'<br><br>Руководитель медицинской организации (исполнительный орган субъекта Российской Федерации в сфере охраны здоровья)')
        cursor.insertHtml(u"<br><br>"+u'_'*35+u'&nbsp;'*4+u'_'*35+u'&nbsp;'*4+u'_'*55+u'&nbsp;'*4)
        cursor.insertHtml(u'<br>'+u'&nbsp;'*15+u'(должность)'+u'&nbsp;'*55+u'(подпись)'+u'&nbsp;'*55+u'(фамилия, имя, отчество (при наличии)<br>')
        cursor.insertHtml(
            u'<br><br>Должностное лицо, ответственное за составление отчетной формы N 030/о-Д/с')
        cursor.insertHtml(
            u"<br><br>" + u'_' * 35 + u'&nbsp;' * 4 + u'_' * 35 + u'&nbsp;' * 4 + u'_' * 55 + u'&nbsp;' * 4)
        cursor.insertHtml(
            u'<br>'+u'&nbsp;' * 15 + u'(должность)' + u'&nbsp;' * 55 + u'(подпись)' + u'&nbsp;' * 55 + u'(фамилия, имя, отчество (при наличии)<br>')
        cursor.insertHtml(u'<br><br>"__" __________ 20__ год')
        cursor.insertHtml(u'<br><br>М.П. (при наличии) (дата составления отчетной формы)')
