# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
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

from library.database    import addDateInRange
from library.MapCode     import createMapCodeToRowIdx
from library.Utils import firstYearDay,  forceInt, forceString, lastYearDay, firstMonthDay, lastMonthDay

from Orgs.Utils          import getOrgStructureDescendants, getOrgStructures

from Reports.Report      import CReport, normalizeMKB
from Reports.ReportBase  import CReportBase, createTable
from DispObservationList import CDispObservationListSetupDialog, dumpParamsEx

MainRows = [
    (u'Всего', u'1.0', u'A00-T98'),
    (u'в том числе: некоторые инфекционные и паразитарные болезни', u'2.0', u'A00-B99'),
    (u'новообразования', u'3.0', u'C00-D48'),
    (u'болезни крови, кроветворных органов и отдельные нарушения, вовлекающие иммунный механизм', u'4.0', u'D50-D89'),
    (u'из них: анемии', u'4.1', u'D50-D64'),
    (u'нарушения свертываемости крови', u'4.2', u'D65-D68'),
    (u'в том числе диссеминированное внутрисосудистое свертывание (синдром дефибринации)', u'4.2.1', u'D65'),
    (u'гемофилия', u'4.2.2', u'D66-D67, D68.0'),
    (u'отдельные нарушения, вовлекающие иммунный механизм', u'4.3', u'D80-D89'),
    (u'болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'5.0', u'E00-E90'),
    (u'из них: тиреотоксикоз (гипертиреоз)', u'5.1', u'E05'),
    (u'сахарный диабет', u'5.2', u'E10-E14'),
    (u'в том числе: инсулинзависимый сахарный диабет', u'5.2.1', u'E10'),
    (u'инсулиннезависимый сахарный диабет', u'5.2.2', u'E11'),
    (u'ожирение', u'5.3', u'E66'),
    (u'муковисцидоз', u'5.4', u'E84.0'),
    (u'гипофизарный нанизм', u'5.5', u'E23.0'),
    (u'болезнь Гоше', u'5.6', u'E75.5'),
    (u'психические расстройства и расстройства поведения', u'6.0', u'F00-F99'),
    (u'болезни нервной системы', u'7.0', u'G00-G99'),
    (u'из них: эпилепсия, эпилептический статус', u'7.1', u'G40-G41'),
    (u'болезни периферической нервной системы', u'7.2', u'G50-G72'),
    (u'детский церебральный паралич', u'7.3', u'G80'),
    (u'рассеянный склероз', u'7.4', u'G35.0'),
    (u'болезни глаза и его придаточного аппарата', u'8.0', u'H00-H59'),
    (u'из них: катаракта', u'8.1', u'H25-H26'),
    (u'глаукома', u'8.2', u'H40'),
    (u'миопия', u'8.3', u'H52.1'),
    (u'болезни уха и сосцевидного отростка', u'9.0', u'H60-H95'),
    (u'из них хронический отит', u'9.1', u'H65.2-9, H66.1-9'),
    (u'болезни системы кровообращения', u'10.0', u'I00-I99'),
    (u'из них: острая ревматическая лихорадка', u'10.1', u'I00-I02'),
    (u'хронические ревматические болезни сердца', u'10.2', u'I05-I09'),
    (u'в том числе ревматические пороки клапанов', u'10.2.1', u'I05-I08'),
    (u'болезни, характеризующиеся повышенным кровяным давлением', u'10.3', u'I10-I13'),
    (u'ишемическая болезнь сердца', u'10.4', u'I20-I25'),
    (u'из общего числа больных ишемической болезнью больных: стенокардией', u'10.5', u'I20'),
    (u'острым инфарктом миокарда', u'10.6', u'I21'),
    (u'повторным инфарктом миокарда', u'10.7', u'I22'),
    (u'некоторыми текущими осложнениями острого инфаркта миокарда', u'10.8', u'I23'),
    (u'другими формами острой ишемической болезни сердца', u'10.9', u'I24'),
    (u'цереброваскулярные болезни', u'10.10', u'I60-I69'),
    (u'инсульт', u'10.10.1', u'I60-I64'),
    (u'эндартериит, тромбангиит облитерирующий', u'10.11', u'I70.2, I73.1'),
    (u'болезни органов дыхания', u'11.0', u'J00-J99'),
    (u'из них: пневмонии', u'11.1', u'J12-J18'),
    (u'аллергический ринит (поллиноз)', u'11.2', u'J30.1'),
    (u'хронический фарингит, назофарингит, синусит, ринит', u'11.3', u'J31-J32'),
    (u'хронические болезни миндалин и аденоидов, перитонзиллярный абсцесс', u'11.4', u'J35, J36'),
    (u'бронхит хронический и неуточненный, эмфизема', u'11.5', u'J40-J43'),
    (u'другая хроническая обструктивная легочная, бронхоэктатическая болезнь', u'11.6', u'J44, J47'),
    (u'астма, астматический статус', u'11.7', u'J45-J46'),
    (u'интерстициальные, гнойные легочные болезни, другие болезни плевры', u'11.8', u'J84-J94'),
    (u'болезни органов пищеварения', u'12.0', u'K00-K93'),
    (u'из них: язва желудка и 12-перстной кишки', u'12.1', u'K25-K26'),
    (u'гастрит и дуоденит', u'12.2', u'K29'),
    (u'функциональные расстройства желудка', u'12.3', u'K30-K31'),
    (u'неинфекционный энтерит и колит', u'12.4', u'K50-K52'),
    (u'болезни печени', u'12.5', u'K70-K76'),
    (u'болезни желчного пузыря, желчевыводящих путей', u'12.6', u'K80-K83'),
    (u'болезни поджелудочной железы', u'12.7', u'K85-K86'),
    (u'болезни кожи и подкожной клетчатки', u'13.0', u'L00-L99'),
    (u'из них: атопический дерматит', u'13.1', u'L20'),
    (u'контактный дерматит', u'13.2', u'L23-L25'),
    (u'болезни костно-мышечной системы и соединительной ткани', u'14.0', u'M00-M99'),
    (u'из них: реактивные артропатии', u'14.1', u'M02'),
    (u'ревматоидный артрит (серопозитивный и серонегативный, юношеский (ювенильный))', u'14.2', u'M05, M06, M08'),
    (u'юношеский (ювенильный) артрит', u'14.3', u'M08'),
    (u'артрозы', u'14.4', u'M15-M19'),
    (u'системные поражения соединительной ткани', u'14.5', u'M30-M35'),
    (u'анкилозирующий спондилит', u'14.6', u'M45'),
    (u'остеопороз', u'14.7', u'M80-M81'),
    (u'болезни мочеполовой системы', u'15.0', u'N00-N99'),
    (u'из них: гломерулярные, тубулоинтерстициальные болезни почек, другие болезни почки и мочеточника', u'15.1', u'N00-N16, N25-N28'),
    (u'почечная недостаточность', u'15.2', u'N17-N19'),
    (u'мочекаменная болезнь', u'15.3', u'N20-N23'),
    (u'болезни предстательной железы', u'15.4', u'N40-N42'),
    (u'мужское бесплодие', u'15.5', u'N46'),
    (u'доброкачественная дисплазия, гипертрофия молочной железы', u'15.6', u'N60, N62-N63'),
    (u'сальпингит и оофорит', u'15.7', u'N70'),
    (u'эндометриоз', u'15.8', u'N80'),
    (u'эрозия и эктропион шейки матки', u'15.9', u'N86'),
    (u'расстройства менструаций', u'15.10', u'N91-N94'),
    (u'нарушение менопаузы и другие нарушения в околоменопаузном периоде', u'15.11', u'N95'),
    (u'женское бесплодие', u'15.12', u'N97'),
    (u'беременность, роды и послеродовой период', u'16.0', u'O00-O99'),
    (u'врожденные аномалии (пороки развития), деформации и хромосомные нарушения', u'18.0', u'Q00-Q99'),
    (u'из них: врожденные аномалии системы кровообращения', u'18.1', u'Q20-Q28'),
    (u'симптомы, признаки и отклонения от нормы, выявленные при клинических и лабораторных исследованиях, не классифицированные в других рубриках', u'19.0', u'R00-R99'),
    (u'травмы, отравления и некоторые другие последствия воздействия внешних причин', u'20.0', u'S00-T98')
]


def selectData(date, workOrgId, sex, ageFrom, ageTo, areaIdEnabled, areaId, MKBFilter, MKBFrom, MKBTo, personId, filterAddressType, socStatusClassId, socStatusTypeId, orgStructureId, specialityId, attachOrgStructureId):
    stmt = u"""
SELECT
    COUNT(DISTINCT Diagnosis.id) AS count,
    Diagnosis.MKB,
    rbDiseaseCharacter.code AS diseaseCharacter,
    (%s) AS firstInPeriodCharacter,
    COUNT(ProphylaxisPlanning.id) as plannedVisit,
    COUNT(ProphylaxisPlanning.visit_id) as factVisit
FROM Diagnosis
LEFT JOIN rbDispanser ON rbDispanser.id = Diagnosis.dispanser_id
LEFT JOIN Diagnostic  ON Diagnostic.diagnosis_id = Diagnosis.id
LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnosis.character_id
LEFT JOIN Client ON Client.id = Diagnosis.client_id
LEFT JOIN ClientAddress AS ClientAddress0 ON ClientAddress0.client_id = Diagnosis.client_id
                        AND ClientAddress0.id = (SELECT MAX(id) FROM ClientAddress AS CA0 WHERE CA0.Type=%d
                                                 and CA0.client_id = Diagnosis.client_id AND CA0.deleted = 0)
left JOIN ClientAttach ca ON ca.id = (
              SELECT MAX(ClientAttach.id)
                    FROM ClientAttach
                    INNER JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
                    WHERE client_id = Client.id
                      AND ClientAttach.deleted = 0
                      AND NOT rbAttachType.TEMPORARY)
LEFT JOIN ProphylaxisPlanning ON Diagnosis.`MKB` = ProphylaxisPlanning.`MKB`
                                 AND Client.`id` = ProphylaxisPlanning.`client_id`
                                 AND ProphylaxisPlanning.deleted = 0 
                                 AND ProphylaxisPlanning.parent_id IS NOT NULL
                                 AND %s
LEFT JOIN rbProphylaxisPlanningType ON rbProphylaxisPlanningType.`id` = ProphylaxisPlanning.`prophylaxisPlanningType_id`
LEFT JOIN Address ON Address.id = ClientAddress0.address_id
LEFT JOIN vrbPersonWithSpeciality ON vrbPersonWithSpeciality.id = Diagnosis.dispanserPerson_id
%s
WHERE
    %s
GROUP BY
    Diagnosis.MKB, diseaseCharacter, firstInPeriodCharacter
"""
    db = QtGui.qApp.db
    tableDiagnosis       = db.table('Diagnosis')
    tableClient          = db.table('Client')
    tableClientDispanser = db.table('rbDispanser')
    tablePerson = db.table('vrbPersonWithSpeciality')
    tableClientAttach = db.table('ClientAttach').alias('ca')
    cond = []
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableDiagnosis['mod_id'].isNull())
    cond.append(tableClientDispanser['observed'].eq(1))
    cond.append(tableClient['deathDate'].isNull())
    cond.append(u'''NOT EXISTS(SELECT DC.id
                                      FROM Diagnostic AS DC
                                      INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                      INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                      WHERE DC.diagnosis_id = Diagnosis.id AND DC.endDate <= %s AND DC.deleted = 0 AND rbDP.name LIKE '%s')
                               OR EXISTS(SELECT DC.id
                                      FROM Diagnostic AS DC
                                      INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                      INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                      WHERE DC.diagnosis_id = Diagnosis.id AND DC.endDate <= %s AND DC.deleted = 0 AND rbDP.name LIKE '%s')''' % (db.formatDate(date), u'%снят%', db.formatDate(date), u'%взят повторно%'))

    if personId:
        cond.append(tableDiagnosis['dispanserPerson_id'].eq(personId))
    elif orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if specialityId:
        cond.append(tablePerson['speciality_id'].eq(specialityId))
    if attachOrgStructureId:
        orgStructureList = getOrgStructureDescendants(attachOrgStructureId)
        cond.append(tableClientAttach['orgStructure_id'].inlist(orgStructureList))

    if MKBFilter == 1:
        cond.append(tableDiagnosis['MKB'].ge(MKBFrom))
        cond.append(tableDiagnosis['MKB'].le(MKBTo))
    cond.append('''Diagnostic.endDate = (SELECT MAX(DC.endDate)
               FROM Diagnostic AS DC
               LEFT JOIN rbDispanser AS rbDSP ON rbDSP.id = DC.dispanser_id
               WHERE DC.deleted = 0 AND DC.diagnosis_id = Diagnosis.id AND rbDSP.observed=1 AND Diagnosis.client_id = Client.id
               AND DC.endDate < %s)''' % (db.formatDate(date.addDays(1))))
    joinWork = u''
    if workOrgId:
        tableClientWork = db.table('ClientWork')
        joinWork = u'''LEFT JOIN ClientWork ON ClientWork.client_id = Client.id
                                AND ClientWork.id = getClientWorkId(Client.id)'''
        cond.append(tableClientWork['org_id'].eq(workOrgId))
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        if ageFrom != 0:
            cond.append(' ADDDATE(Client.birthDate, INTERVAL %d YEAR)<= %s ' % (ageFrom,db.formatDate(date) ))
        if ageTo != 150:
            cond.append(' ADDDATE(Client.birthDate, INTERVAL %d YEAR)> %s ' % (ageTo + 1, db.formatDate(date)))
    if areaIdEnabled:
        if areaId:
            orgStructureIdList = getOrgStructureDescendants(areaId)
        else:
            orgStructureIdList = getOrgStructures(QtGui.qApp.currentOrgId())
        tableOrgStructureAddress = db.table('OrgStructure_Address')
        tableAddress = db.table('Address')
        subCond = [ tableOrgStructureAddress['master_id'].inlist(orgStructureIdList),
                    tableOrgStructureAddress['house_id'].eq(tableAddress['house_id']),
                  ]
        cond.append(db.existsStmt(tableOrgStructureAddress, subCond))

    if socStatusTypeId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusType_id=%d' % socStatusTypeId)
        cond.append('EXISTS('+subStmt+')')
    elif socStatusClassId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusClass_id=%d' % socStatusClassId)
        cond.append('EXISTS('+subStmt+')')


    date = date if date else QDate.currentDate()
    firstDay = firstYearDay(date)
    lastDay = lastYearDay(date)
    dateCond = []
    tableDiagnostic2 = db.table('Diagnostic').alias('d2')
    tableDispanser = db.table('rbDispanser')
    tableDC2 = db.table('rbDiseaseCharacter').alias('dc2')
    table2 = tableDiagnostic2.leftJoin(tableDC2, tableDC2['id'].eq(tableDiagnostic2['character_id']))
    table2 = table2.leftJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnostic2['dispanser_id']))

    addDateInRange(dateCond, tableDiagnostic2['endDate'], firstDay, lastDay)

    return db.query(stmt % (db.selectStmt(table2, tableDC2['code'],
                                          [tableDiagnostic2['diagnosis_id'].eq(tableDiagnosis['id']),
                                           tableDiagnostic2['deleted'].eq(0),
                                           tableDispanser['code'].inlist(['2', '6']),
                                           db.joinAnd(dateCond)], limit=1),
                            filterAddressType,
                            """(%s BETWEEN ProphylaxisPlanning.begDate AND ProphylaxisPlanning.endDate
                             OR %s BETWEEN ProphylaxisPlanning.begDate AND ProphylaxisPlanning.endDate)""" % (db.formatDate(firstMonthDay(date)), db.formatDate(lastMonthDay(date))),
                            joinWork,
                            db.joinAnd(cond)))


class CDispObservationSurvey(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Диспансерное наблюдение: сводка', u'Диспансерное наблюдение')


    def getSetupDialog(self, parent):
        result = CDispObservationListSetupDialog(parent)
        result.setTitle(self.title())
        result.setChkPrintOnlyFilledRowsVisible(True)
        return result


    def build(self, params):
        mapMainRows = createMapCodeToRowIdx([row[2] for row in MainRows])

        date = params.get('date', QDate())
        workOrgId = params.get('workOrgId', None)
        sex = params.get('sex', 0)
        ageFrom = params.get('ageFrom', 0)
        ageTo = params.get('ageTo', 150)
        areaIdEnabled = params.get('areaIdEnabled', False)
        areaId = params.get('areaId', None)
        MKBFilter = params.get('MKBFilter', 0)
        MKBFrom = params.get('MKBFrom', 'A00')
        MKBTo = params.get('MKBTo', 'Z99.9')
        personId = params.get('personId', None)
        filterAddressType = params.get('filterAddressType', 0)
        isPrintOnlyFilledRows = params.get('isPrintOnlyFilledRows', False)

        socStatusClassId = params.get('socStatusClassId', None)
        socStatusTypeId = params.get('socStatusTypeId', None)
        orgStructureId = params.get('orgStructureId', None)
        specialityId = params.get('specialityId', None)
        attachOrgStructureId = params.get('attachOrgStructureId', None)

        rowSize = 7
        reportMainData = [[0]*rowSize for row in xrange(len(MainRows))]
        query = selectData(date, workOrgId, sex, ageFrom, ageTo, areaIdEnabled, areaId, MKBFilter, MKBFrom, MKBTo, personId, filterAddressType, socStatusClassId, socStatusTypeId, orgStructureId, specialityId, attachOrgStructureId)

        while query.next():
            record    = query.record()
            count     = forceInt(record.value('count'))
            MKB       = normalizeMKB(forceString(record.value('MKB')))
            diseaseCharacter = forceString(record.value('diseaseCharacter'))
            firstInPeriodCharacter = forceString(record.value('firstInPeriodCharacter'))
            plannedVisit = forceInt(record.value('plannedVisit'))
            factVisit = forceInt(record.value('factVisit'))

            for row in mapMainRows.get(MKB, []):
                reportLine = reportMainData[row]
                reportLine[0] += count
                if diseaseCharacter != '1':
                    if firstInPeriodCharacter:
                        reportLine[1] += count
                        if firstInPeriodCharacter == '2':
                            reportLine[2] += count
                        else:
                            reportLine[3] += count
                reportLine[4] += plannedVisit
                reportLine[5] += factVisit
                reportLine[6] += plannedVisit - factVisit

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        dumpParamsEx(cursor, params)
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('40%', [u'Нозологическая группа', u''], CReportBase.AlignLeft),
            ('2%', [u'№ строки',              u''], CReportBase.AlignLeft),
            ('7%', [u'код МКБ',               u''], CReportBase.AlignLeft),
            ('7%', [u'Состоит',               u''], CReportBase.AlignRight),
            ('7%', [u'В т.ч. в тек.году',     u'взято'], CReportBase.AlignRight),
            ('7%', [u'', u'впервые установленные'], CReportBase.AlignRight),
            ('7%', [u'', u'ранее известные'], CReportBase.AlignRight),
            ('7%', [u'Запланировано диспансерных приемов', u''], CReportBase.AlignRight),
            ('7%', [u'явились на Д-прием', u''], CReportBase.AlignRight),
            ('7%', [u'не явились на Д-прием', u''], CReportBase.AlignRight),
            ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)  # Наименование
        table.mergeCells(0, 1, 2, 1)  # № стр.
        table.mergeCells(0, 2, 2, 1)  # Код МКБ
        table.mergeCells(0, 3, 2, 1)  # Состоит
        table.mergeCells(0, 4, 1, 3)  # Всего
        table.mergeCells(0, 5, 1, 2)  # в т.ч. впервые
        table.mergeCells(0, 6, 1, 2)  # в т.ч. ранее известны.
        table.mergeCells(0, 7, 2, 1)  # Запланировано
        table.mergeCells(0, 8, 2, 1)  # явились
        table.mergeCells(0, 9, 2, 1)  # не явились

        for row, rowDescr in enumerate(MainRows):
            reportLine = reportMainData[row]
            if not isPrintOnlyFilledRows or reportLine[0]:
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                table.setText(i, 3, reportLine[0])
                table.setText(i, 4, reportLine[1])
                table.setText(i, 5, reportLine[2])
                table.setText(i, 6, reportLine[3])
                table.setText(i, 7, reportLine[4])
                table.setText(i, 8, reportLine[5])
                table.setText(i, 9, reportLine[6])

        cursor.movePosition(QtGui.QTextCursor.End)
        return doc
