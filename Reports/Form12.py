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
from PyQt4.QtCore import QDate, QTime, QDateTime

from Orgs.Utils import getOrgStructureFullName
from Reports.Form11 import CForm11SetupDialog
from Reports.Utils import dateRangeAsStr, splitTitle
from library.MapCodeWithExSubClass import createMapCodeToRowIdx, normalizeMKB
from library.Utils import forceBool, forceInt, forceString, forceRef

from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable


class CForm12(CReport):

    # отступ | наименование | № строки | диагнозы титул | диагнозы диапазон
    CompRows = [
        (0, u'Всего', u'1.0', u'Z00-Z99', u'Z00-Z99'),
        (1, u'из них:\nобращения в медицинские организации для медицинского осмотра и обследования', u'1.1', u'Z00-Z13', u'Z00-Z13'),
        (2, u'из них:\nобращения в связи с получением медицинских документов', u'1.1.1', u'Z02.7', u'Z02.7'),
        (1, u'потенциальная опасность для здоровья, связанная с инфекционными болезнями', u'1.2', u'Z20-Z29', u'Z20-Z29'),
        (2, u'из них:\nносительство возбудителя инфекционной болезни', u'1.2.1', u'Z22', u'Z22'),
        (1, u'обращения в медицинские организации в связи с обстоятельствами, относящимися к репродуктивной функции', u'1.3', u'Z30-Z39', u'Z30-Z39'),
        (1, u'обращения в медицинские организации в связи с необходимостью проведения специфических процедур и получения медицинской помощи', u'1.4', u'Z40-Z54', u'Z40-Z54'),
        (2, u'из них:\nпомощь, включающая использование реабилитационных процедур', u'1.4.1', u'Z50', u'Z50'),
        (2, u'паллиативная помощь', u'1.4.2', u'Z51.5', u'Z51.5'),
        (1, u'потенциальная опасность для здоровья, связанная с социально-экономическими и психосоциальными обстоятельствами', u'1.5', u'Z55-Z65', u'Z55-Z65'),
        (1, u'обращения в медицинские организации в связи с другими обстоятельствами', u'1.6', u'Z70-Z76', u'Z70-Z76'),
        (2, u'из них:\nроблемы, связанные с образом жизни:', u'1.6.1', u'Z72', u'Z72'),
        (1, u'потенциальная опасность для здоровья, связанная с личным или семейным анамнезом и определенными обстоятельствами, влияющими на здоровье', u'1.7', u'Z80-Z99', u'Z80-Z99'),
        (2, u'из них:\nзаболевания в семейном анамнезе', u'1.7.1', u'Z80-Z84', u'Z80-Z84'),
        (2, u'наличие илеостомы, колостомы', u'1.7.2', u'Z93.2, Z93.3', u'Z93.2; Z93.3')
    ]

    def __init__(self, parent):
        CReport.__init__(self, parent)

    def getSetupDialog(self, parent):
        result = CForm11SetupDialog(parent)
        result.setTypeDNVisible()
        result.setAddressTypeVisible(False)
        return result

    def dumpParams(self, cursor, params):
        description = []
        endDate = params.get('endDate', QDate())
        begDate = params.get('begDate', QDate())
        if not endDate:
            endDate = QDate.currentDate()
        if endDate:
            endTime = params.get('endTime', QTime(9, 0, 0, 0))
            begTime = params.get('begTime', None)
            endDateTime = QDateTime(endDate, endTime)
            if not begDate:
                description.append(u'Текущий день: ' + forceString(QDateTime(endDate, endTime)))
            else:
                begTime = begTime if begTime else endTime
                begDateTime = QDateTime(begDate, begTime)
                if begDateTime.date() or endDateTime.date():
                    description.append(dateRangeAsStr(u'за период', begDateTime, endDateTime))

        orgStructureId = params.get('orgStructureId', None)
        typeDN = params.get('typeDN', -1)

        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')

        if typeDN >= 0:
            description.append(u'диспансерное наблюдение по: ' + (u'контингентам в карте' if typeDN else u'событиям'))

        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [('100%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

    def selectData(self, params):
        db = QtGui.qApp.db
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        begDateTime = None
        endDateTime = None
        ageFrom = params.get('ageFrom', 0)
        ageTo = params.get('ageTo', 0)
        typeDN = params.get('typeDN', -1)

        if not endDate:
            endDate = QDate.currentDate()
        if endDate:
            endTime = params.get('endTime', QTime(9, 0, 0, 0))
            begTime = params.get('begTime', QTime(0, 0, 0, 0))
            endDateTime = QDateTime(endDate, endTime)
            if not begDate:
                begTime = begTime if begTime else endTime
                begDateTime = QDateTime(endDate.addDays(-1), begTime)
            else:
                begTime = begTime if begTime else endTime
                begDateTime = QDateTime(begDate, begTime)

        ageCond = ''
        orgStructureIdList = params.get('orgStructureIdList', None)
        if orgStructureIdList:
            condOrgstruct = 'AND ' + db.table('Person').alias('p')['orgStructure_id'].inlist(orgStructureIdList)
        else:
            condOrgstruct = ''
        if ageFrom <= ageTo:
            if ageFrom == 55:
                ageCond = """AND (age(c.birthDate, {endDate}) between {ageMaleFrom} and {ageTo} AND c.sex = 1 
                OR age(c.birthDate, {endDate}) between {ageFrom} and {ageTo} AND c.sex = 2)""".format(
                    endDate=db.formatDate(endDateTime), ageFrom=ageFrom, ageTo=ageTo, ageMaleFrom=ageFrom+5)
            else:
                ageCond = 'AND age(c.birthDate, {endDate}) between {ageFrom} and {ageTo}'.format(
                    endDate=db.formatDate(endDateTime), ageFrom=ageFrom, ageTo=ageTo)

        if typeDN:
            stmt = u"""SELECT c.id as client_id,
      IF(cck.exSubclassMKB IS NOT NULL, CONCAT(cck.MKB, cck.exSubclassMKB), cck.MKB) AS MKB,
      c.sex,
      age(c.birthDate, IF(cck.begDate BETWEEN {begDate} AND {endDate}, cck.begDate, {endDate})) AS age,
      IF(DATE_ADD(c.birthDate, INTERVAL 29 DAY) >= cck.begDate, 1, 0) AS dayAge,
      IF(cck.begDate BETWEEN {begDate} AND {endDate} AND c.begDate BETWEEN {begDate} AND {endDate}, 1, 0) isFirstInLife,
      IF(ck.code = 'Д-наблюдение', 1, 0)  AS DN,
      IF(ck.code = 'Д-наблюдение' AND IFNULL(cck.endDate, {endDate} + INTERVAL 1 day) >= {endDate}, 1, 0)  AS DNforEndDate
    FROM Client c
    LEFT JOIN ClientContingentKind cck ON cck.client_id = c.id
    LEFT JOIN rbContingentKind ck ON cck.contingentKind_id = ck.id
    WHERE c.deleted = 0
    AND cck.deleted = 0
    AND ck.code IN ('Д-наблюдение', 'ПДЛР')
    AND (cck.endDate BETWEEN {begDate} AND {endDate} OR cck.endDate IS NULL)
    -- пока закомментировал это условие
   /* AND IFNULL(cck.contingentKindRemoval_id, 0) <> 3
    AND NOT EXISTS (SELECT NULL FROM ClientContingentKind cck
              left JOIN rbContingentKind ck ON cck.contingentKind_id = ck.id
              WHERE cck.client_id = c.id AND ck.code = 'А' AND cck.deleted = 0
              AND cck.endDate is null)*/
    {ageCond}
    AND length(cck.MKB) >= 3 
    AND cck.MKB not like 'Z%'
    """.format(begDate=db.formatDate(begDateTime), endDate=db.formatDate(endDateTime), ageCond=ageCond)
        else:
            stmt = u"""
        SELECT t.* 
          FROM (SELECT c.id as client_id, e.setDate,
            IF(d.exSubclassMKB IS NOT NULL, CONCAT(d.MKB, d.exSubclassMKB), d.MKB) AS MKB,
            c.sex,
            age(c.birthDate, e.setDate) AS age,
            IF(c.begDate BETWEEN {begDate} AND {endDate}, 1, 0) isFirstInLife,
            EXISTS (SELECT NULL FROM ClientContingentKind cck
              left JOIN rbContingentKind ck ON cck.contingentKind_id = ck.id
              WHERE cck.client_id = c.id AND ck.code = 'Д-наблюдение' AND cck.deleted = 0
              AND cck.begDate BETWEEN {begDate} AND {endDate}
             ) AS DN,
            EXISTS (SELECT NULL FROM ClientContingentKind cck
              left JOIN rbContingentKind ck ON cck.contingentKind_id = ck.id
              WHERE cck.client_id = c.id AND ck.code = 'Д-наблюдение' AND cck.deleted = 0
              AND cck.begDate <= {endDate} AND IFNULL(cck.endDate, {endDate} + INTERVAL 1 day) >= {endDate}
             ) AS DNforEndDate
          FROM Event e
          LEFT JOIN Person p ON p.id = e.execPerson_id
          left JOIN Client c on c.id = e.client_id
          left JOIN EventType et ON e.eventType_id = et.id
          left JOIN rbEventTypePurpose etp ON et.purpose_id = etp.id
          LEFT JOIN Diagnosis d on d.id = (SELECT diagnosis_id
          FROM Diagnostic
          INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = diagnosisType_id
          WHERE Diagnostic.event_id = e.id
          AND Diagnostic.deleted = 0
          AND rbDiagnosisType.code in ('1', '2', '7')
          ORDER BY rbDiagnosisType.code
          LIMIT 1
          )
          WHERE e.deleted = 0
          AND c.deleted = 0
          AND d.deleted = 0
          AND et.code NOT IN ('hospDir','egpuDisp','plng', 'anonim')
          AND et.context NOT LIKE '%relatedAction%' AND et.context NOT LIKE '%inspection%'
          AND et.form NOT IN ('000', '027', '106', '110')
          AND etp.code <> 0 
          AND e.setDate BETWEEN {begDate} AND {endDate}
          AND mod_id is NULL
          {condOrgstruct}) t
        GROUP BY t.client_id, t.MKB
        ORDER BY t.setDate desc
            """.format(begDate=db.formatDate(begDateTime), endDate=db.formatDate(endDateTime),
                       condOrgstruct=condOrgstruct)

        return db.query(stmt)

    def selectDataZDiagnosis(self, params):
        db = QtGui.qApp.db
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        begDateTime = None
        endDateTime = None
        ageFrom = params.get('ageFrom', 0)
        ageTo = params.get('ageTo', 0)
        if not endDate:
            endDate = QDate.currentDate()
        if endDate:
            endTime = params.get('endTime', QTime(9, 0, 0, 0))
            begTime = params.get('begTime', QTime(0, 0, 0, 0))
            endDateTime = QDateTime(endDate, endTime)
            if not begDate:
                begTime = begTime if begTime else endTime
                begDateTime = QDateTime(endDate.addDays(-1), begTime)
            else:
                begTime = begTime if begTime else endTime
                begDateTime = QDateTime(begDate, begTime)

        orgStructureIdList = params.get('orgStructureIdList', None)
        ageCond = ''
        if orgStructureIdList:
            condOrgstruct = 'AND ' + db.table('Person').alias('p')['orgStructure_id'].inlist(orgStructureIdList)
        else:
            condOrgstruct = ''
        if ageFrom <= ageTo:
            if ageFrom == 55:
                ageCond = """AND (age(Client.birthDate, {endDate}) between {ageMaleFrom} and {ageTo} AND Client.sex = 1 
                OR age(Client.birthDate, {endDate}) between {ageFrom} and {ageTo} AND Client.sex = 2)""".format(
                    endDate=db.formatDate(endDateTime), ageFrom=ageFrom, ageTo=ageTo, ageMaleFrom=ageFrom + 5)
            else:
                ageCond = 'AND age(Client.birthDate, {endDate}) between {ageFrom} and {ageTo}'.format(
                    endDate=db.formatDate(endDateTime), ageFrom=ageFrom, ageTo=ageTo)
        stmt = u"""
    SELECT
       Event.id,
       Diagnosis.MKB AS MKB,
       count(*) AS sickCount,
       IF(Event.isPrimary = 2, 1, 0) AS isNotPrimary
    FROM Event
      LEFT JOIN Diagnostic ON Event.id = Diagnostic.event_id
      LEFT JOIN Diagnosis ON Diagnostic.diagnosis_id = Diagnosis.id
      LEFT JOIN Client ON Client.id = Diagnosis.client_id
      LEFT JOIN rbDiagnosisType ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
      LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnostic.character_id
      LEFT JOIN rbDispanser ON rbDispanser.id = Diagnostic.dispanser_id
      LEFT JOIN EventType ON EventType.id = Event.eventType_id
      LEFT JOIN rbMedicalAidType ON EventType.medicalAidType_id = rbMedicalAidType.id
      LEFT JOIN Person ON Person.id = Event.execPerson_id
    WHERE Diagnostic.diagnosisType_id IN (SELECT RBDT.id FROM rbDiagnosisType RBDT WHERE RBDT.code in ('1', '2', '9'))
      AND Diagnostic.deleted = 0
      AND Client.deleted = 0 
      AND Diagnosis.deleted = 0 
      AND Event.deleted = 0
      AND rbMedicalAidType.code NOT IN ('1', '2', '3', '7')
      AND Event.execDate BETWEEN {begDate} AND {endDate}
      AND Diagnosis.MKB LIKE 'Z%'
      {ageCond}
      {condOrgstruct}
    GROUP BY MKB, isNotPrimary
            """.format(begDate=db.formatDate(begDateTime), endDate=db.formatDate(endDateTime), ageCond=ageCond,
                       condOrgstruct=condOrgstruct)
        return db.query(stmt)


class CForm12_1000_1100(CForm12):

    # отступ | наименование | № строки | диагнозы титул | диагнозы диапазон
    MainRows = [
        (0, u'Зарегистрировано заболеваний - всего', u'1.0', u'A00-T98', u'A00-T98'),
        (1, u'в том числе:\nнекоторые инфекционные и паразитарные болезни', u'2.0', u'A00-B99', u'A00-B99'),
        (2, u'из них:\nкишечные инфекции', u'2.1', u'A00-A09', u'A00-A09'),
        (2, u'менингококковая инфекция', u'2.2', u'A39', u'A39'),
        (2, u'вирусный гепатит', u'2.3', u'B15-B19', u'B15-B19'),
        (1, u'новообразования', u'3.0', u'C00-D48', u'C00-D48'),
        (2, u'из них:\nзлокачественные новообразования', u'3.1', u'C00-C96', u'C00-C96'),
        (3, u'из них:\nзлокачественные новообразования лимфоидной, кроветворной и родственных им тканей', u'3.1.1', u'C81-C96', u'C81-C96'),
        (2, u'доброкачественные новобразования', u'3.2', u'D10-D36', u'D10-D36'),
        (1, u'болезни крови, кроветворных органов и отдельные нарушения, вовлекающие иммунный механизм', u'4.0', u'D50-D89', u'D50-D89'),
        (2, u'из них:\nанемии', u'4.1', u'D50-D64', u'D50-D64'),
        (3, u'из них:\n апластические анемии', u'4.1.1', u'D60-D61', u'D60-D61'),
        (2, u'нарушения свертываемости крови, пурпура и другие геморрагические состояния', u'4.2', u'D65-D69', u'D65-D69'),
        (3, u'из них: гемофилия', u'4.2.1', u'D66-D68', u'D66-D68'),
        (2, u'отдельные нарушения, вовлекающие иммунный механизм', u'4.3', u'D80-D89', u'D80-D89'),
        (1, u'болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'5.0', u'E00-E89', u'E00-E89'),
        (2, u'из них:\nболезни щитовидной железы', u'5.1', u'E00-E07', u'E00-E07'),
        (3, u'из них:\nсиндром врожденной йодной недостаточности', u'5.1.1', u'E00', u'E00'),
        (3, u'эндемический зоб, связанный с йодной недостаточностью', u'5.1.2', u'E01.0-2', u'E01.0-2'),
        (3, u'субклинический гипотиреоз вследствие йодной недостаточности и другие формы гипотиреоза', u'5.1.3', u'E02, E03', u'E02; E03'),
        (3, u'другие формы нетоксического зоба', u'5.1.4', u'E04', u'E04'),
        (3, u'тиреотоксикоз (гипертиреоз)', u'5.1.5', u'E05', u'E05'),
        (3, u'тиреоидит', u'5.1.6', u'E06', u'E06'),
        (2, u'сахарный диабет', u'5.2', u'E10-E14', u'E10-E14'),
        (3, u'из него:\nс поражением глаз', u'5.2.1', u'E10.3, E11.3, E12.3, E13.3, E14.3', u'E10.3; E11.3; E12.3; E13.3; E14.3'),
        (3, u'с поражением почек', u'5.2.2', u'E10.2, E11.2, E12.2, E13.2, E14.2', u'E10.2; E11.2; E12.2; E13.2; E14.2'),
        (3, u'из него (из стр. 5.2): сахарный диабет I типа', u'5.2.3', u'E10', u'E10'),
        (3, u'сахарный диабет II типа', u'5.2.4', u'E11', u'E11'),
        (2, u'гиперфункция гипофиза', u'5.3', u'E22', u'E22'),
        (2, u'гипопитуитаризм', u'5.4', u'E23.0', u'E23.0'),
        (2, u'несахарный диабет', u'5.5', u'E23.2', u'E23.2'),
        (2, u'адреногенитальные расстройства', u'5.6', u'E25', u'E25'),
        (2, u'дисфункция яичников', u'5.7', u'E28', u'E28'),
        (2, u'дисфункция яичек', u'5.8', u'E29', u'E29'),
        (2, u'рахит', u'5.9', u'E55.0', u'E55.0'),
        (2, u'ожирение', u'5.10', u'E66', u'E66'),
        (2, u'фенилкетонурия', u'5.11', u'E70.0', u'E70.0'),
        (2, u'нарушения обмена галактозы (галактоземия)', u'5.12', u'E74.2', u'E74.2'),
        (2, u'болезнь Гоше', u'5.13', u'E75.2', u'E75.2'),
        (2, u'нарушения обмена гликозамигликанов (мукополисахаридоз)', u'5.14', u'E76', u'E76'),
        (2, u'муковисцидоз', u'5.15', u'E84', u'E84'),
        (1, u'психические расстройства и расстройства поведения', u'6.0', u'F01, F03-F99', u'F01; F03-F99'),
        (2, u'из них:\nпсихические расстройства и расстройства поведения, связанные с употреблением психоактивных веществ', u'6.1', u'F10-F19', u'F10-F19'),
        (2, u'детский аутизм, атипичный аутизм, синдром Ретта, дезинтегративное расстройство детского возраста', u'6.2', u'F84.0-3', u'F84.0-3'),
        (1, u'болезни нервной системы', u'7.0', u'G00-G98', u'G00-G98'),
        (2, u'из них:\nвоспалительные болезни центральной нервной системы', u'7.1', u'G00-G09', u'G00-G09'),
        (3, u'из них:\n бактериальный менингит', u'7.1.1', u'G00', u'G00'),
        (3, u'энцефалит, миелит и энцефаломиелит', u'7.1.2', u'G04', u'G04'),
        (2, u'системные атрофии, поражающие преимущественно нервную систему', u'7.2', u'G10-G12', u'G10-G12'),
        (2, u'экстрапирамидные и другие двигательные нарушения', u'7.3', u'G20, G21, G23-G25', u'G20; G21; G23-G25'),
        (3, u'из них:\nдругие экстрапирамидные и двигательные нарушения', u'7.3.2', u'G25', u'G25'),
        (2, u'другие дегенеративные болезни нервной системы', u'7.4', u'G30-G31', u'G30-G31'),
        (2, u'демиелинизирующие болезни центральной нервной системы', u'7.5', u'G35-G37', u'G35-G37'),
        (3, u'из них:\nрассеянный склероз', u'7.5.1', u'G35', u'G35'),
        (2, u'эпизодические и пароксизмальные расстройства', u'7.6', u'G40-G47', u'G40-G47'),
        (3, u'из них:\nэпилепсия, эпилептический статус', u'7.6.1', u'G40-G41', u'G40-G41'),
        (3, u'преходящие транзиторные церебральные ишемические приступы (атаки) и родственные синдромы', u'7.6.2', u'G45', u'G45'),
        (2, u'поражения отдельных нервов, нервных корешков и сплетений, полиневропатии и другие поражения периферической нервной  системы', u'7.7', u'G50-G64', u'G50-G64'),
        (3, u'из них:\nсиндром Гийена-Барре', u'7.7.1', u'G61.0', u'G61.0'),
        (2, u'болезни нервно-мышечного синапса и мышц', u'7.8', u'G70-G73', u'G70-G73'),
        (3, u'из них:\nмиастения ', u'7.8.1', u'G70.0, 2', u'G70.0, 2'),
        (3, u'мышечная дистрофия Дюшенна', u'7.8.2', u'G71.0', u'G71.0'),
        (2, u'церебральный паралич и другие паралитические синдромы', u'7.9', u'G80-G83', u'G80-G83'),
        (3, u'из них:\nцеребральный паралич', u'7.9.1', u'G80', u'G80'),
        (2, u'расстройства вегетативной(автономной) нервной системы', u'7.10', u'G90', u'G90'),
        (2, u'сосудистые миелопатии', u'7.11', u'G95.1', u'G95.1'),
        (1, u'болезни глаза и его придаточного аппарата', u'8.0', u'H00-H59', u'H00-H59'),
        (2, u'из них:\nконъюнктивит', u'8.1', u'H10', u'H10'),
        (2, u'кератит', u'8.2', u'H16', u'H16'),
        (3, u'из него:\nязва роговицы', u'8.2.1', u'H16.0', u'H16.0'),
        (2, u'катаракта', u'8.3', u'H25-H26', u'H25-H26'),
        (2, u'хориоретинальное воспаление', u'8.4', u'H30', u'H30'),
        (2, u'отслойка сетчатки с разрывом сетчатки', u'8.5', u'H33.0', u'H33.0'),
        (2, u'преретинопатия', u'8.6', u'H35.1', u'H35.1'),
        (2, u'дегенерация макулы и заднего полюса', u'8.7', u'H35.3', u'H35.3'),
        (2, u'глаукома', u'8.8', u'H40', u'H40'),
        (2, u'дегенеративная миопия', u'8.9', u'H44.2', u'H44.2'),
        (2, u'болезни зрительного нерва и зрительных путей', u'8.10', u'H46-H48', u'H46-H48'),
        (3, u'атрофия зрительного нерва', u'8.10.1', u'H47.2', u'H47.2'),
        (2, u'болезни мышц глаза, нарушения содружественного движения глаз, аккомодации и рефракции', u'8.11', u'H49-H52', u'H49-H52'),
        (3, u'из них:\nмиопия', u'8.11.1', u'H52.1', u'H52.1'),
        (3, u'астигматизм', u'8.11.2', u'H52.2', u'H52.2'),
        (2, u'слепота и пониженное зрение', u'8.12', u'H54', u'H54'),
        (3, u'из них:\nслепота обоих глаз', u'8.12.1', u'H54.0', u'H54.0'),
        (1, u'болезни уха и сосцевидного отростка', u'9.0', u'H60-H95', u'H60-H95'),
        (2, u'из них:\nболезни наружного уха', u'9.1', u'H60-H61', u'H60-H61'),
        (2, u'болезни среднего уха и сосцевидного отростка', u'9.2', u'H65-H66, H68-H74', u'H65-H66; H68-H74'),
        (3, u'из них:\n острый средний отит', u'9.2.1', u'H65.0, H65.1, H66.0', u'H65.0; H65.1; H66.0'),
        (3, u'хронический средний отит', u'9.2.2', u'H65.2-4, H66.1-3', u'H65.2-4; H66.1-3'),
        (3, u'болезни слуховой (евстахиевой) трубы', u'9.2.3', u'H68-H69', u'H68-H69'),
        (3, u'перфорация барабанной перепонки', u'9.2.4', u'H72', u'H72'),
        (3, u'другие болезни среднего уха и сосцевидного отростка', u'9.2.5', u'H74', u'H74'),
        (2, u'болезни внутреннего уха', u'9.3', u'H80-H81, H83', u'H80-H81; H83'),
        (3, u'из них:\nотосклероз', u'9.3.1', u'H80', u'H80'),
        (3, u'болезнь Меньера', u'9.3.2', u'H81.0', u'H81.0'),
        (2, u'кондуктивная и нейросенсорная потеря слуха', u'9.4', u'H90', u'H90'),
        (3, u'из них:\nкондуктивная потеря слуха двусторонняя', u'9.4.1', u'H90.0', u'H90.0'),
        (3, u'нейросенсорная потеря слуха двусторонняя', u'9.4.2', u'H90.3', u'H90.3'),
        (1, u'болезни системы кровообращения', u'10.0', u'I00-I99', u'I00-I99'),
        (2, u'из них:\nострая ревматическая лихорадка', u'10.1', u'I00-I02', u'I00-I02'),
        (2, u'хронические ревматические болезни сердца', u'10.2', u'I05-I09', u'I05-I09'),
        (3, u'из них:\nревматические поражения клапанов', u'10.2.1', u'I05-I08', u'I05-I08'),
        (2, u'болезни, характеризующиеся повышенным кровяным давлением', u'10.3', u'I10-I13', u'I10-I13'),
        (3, u'из них:\nэссенциальная гипертензия', u'10.3.1', u'I10', u'I10'),
        (3, u'гипертензивная болезнь сердца(гипертоническая болезнь с преимущественным поражением сердца)', u'10.3.2', u'I11', u'I11'),
        (3, u'гипертензивная (гипертоническая) болезнь с преимущественным  поражением  почек', u'10.3.3', u'I12', u'I12'),
        (3, u'гипертензивная (гипертоническая) болезнь с преимущественным  поражением сердца и  почек', u'10.3.4', u'I13', u'I13'),
        (2, u'ишемические болезни сердца', u'10.4', u'I20- I25', u'I20-I25'),
        (2, u'другие болезни сердца', u'10.5', u'I30-I51', u'I30-I51'),
        (3, u'из них:\nострый перикардит', u'10.5.1', u'I30', u'I30'),
        (3, u'из них острый и подострый эндокардит', u'10.5.2', u'I33', u'I33'),
        (3, u'острый миокардит', u'10.5.3', u'I40', u'I40'),
        (3, u'кардиомиопатия', u'10.5.4', u'I42', u'I42'),
        (2, u'цереброваскулярные болезни', u'10.6', u'I60-I69', u'I60-I69'),
        (3, u'из них:\nсубарахноидальное кровоизлияние', u'10.6.1', u'I60', u'I60'),
        (3, u'внутримозговое и другое внутричерепное кровоизлияние', u'10.6.2', u'I61, I62', u'I61; I62'),
        (3, u'инфаркт мозга', u'10.6.3', u'I63', u'I63'),
        (3, u'инсульт, не уточненный, как кровоизлияние  или инфаркт', u'10.6.4', u'I64', u'I64'),
        (3, u'закупорка и стеноз прецеребральных, церебральных артерий, не приводящие к инфаркту мозга', u'10.6.5', u'I65-I66', u'I65-I66'),
        (3, u'другие цереброваскулярные болезни', u'10.6.6', u'I67', u'I67'),
        (3, u'последствия цереброваскулярные болезни', u'10.6.7', u'I69', u'I69'),
        (2, u'болезни вен, лимфатических сосудов и лимфатических узлов', u'10.8', u'I80-I83, I85-I89', u'I80-I83; I85-I89'),
        (3, u'из них:\nфлебит и тромбофлебит', u'10.8.1', u'I80', u'I80'),
        (3, u'тромбоз портальной вены', u'10.8.2', u'I81', u'I81'),
        (3, u'варикозное расширение вен нижних конечностей', u'10.8.3', u'I83', u'I83'),
        (1, u'болезни органов дыхания', u'11.0', u'J00-J98', u'J00-J98'),
        (2, u'из них:\nострые респираторные инфекции верхних дыхательных путей', u'11.1', u'J00-J06', u'J00-J06'),
        (3, u'из них:\nострый ларингит и трахеит', u'11.1.1', u'J04', u'J04'),
        (3, u'острый обструктивный ларингит (круп) и эпиглоттит', u'11.1.2', u'J05', u'J05'),
        (2, u'грипп', u'11.2', u'J09-J11', u'J09-J11'),
        (2, u'пневмонии', u'11.3', u'J20-J22', u'J20-J22'),
        (2, u'Из них бронхопневмония, вызванная S.Pneumoniae', u'11.3.1', u'J13', u'J13'),
        (2, u'острые респираторные инфекции нижних дыхательных путей', u'11.4', u'J12-J16, J18', u'J12-J16; J18'),
        (2, u'аллергический ринит (поллиноз)', u'11.5', u'J30.1', u'J30.1'),
        (2, u'хронические болезни миндалин и аденоидов, перитонзиллярный абсцесс', u'11.6', u'J35-J36', u'J35-J36'),
        (2, u'бронхит хронический и неуточненный, эмфизема', u'11.7', u'J40-J43', u'J40-J43'),
        (2, u'другая хроническая обструктивная легочная болезнь ', u'11.8', u'J44', u'J44'),
        (2, u'бронхоэктатическая болезнь', u'11.9', u'J47', u'J47'),
        (2, u'астма, астматический статус', u'11.10', u'J45-J46', u'J45-J46'),
        (2, u'другие интерстициальные легочные болезни, гнойные  и некротические болезни, состояния нижних дыхательных путей, другие болезни плевры', u'11.11', u'J84-J90, J92-J94', u'J84-J90; J92-J94'),
        (1, u'болезни органов пищеварения', u'12.0', u'K00-K92', u'K00-K92'),
        (2, u'из них:\nязва желудка и двенадцатиперстной перстной кишки', u'12.1', u'K25-K26', u'K25-K26'),
        (2, u'гастрит и дуоденит', u'12.2', u'K29', u'K29'),
        (2, u'грыжи', u'12.3', u'K40-K46', u'K40-K46'),
        (2, u'неинфекционный энтерит и колит', u'12.4', u'K50-K52', u'K50-K52'),
        (2, u'другие болезни кишечника', u'12.5', u'K55-K63', u'K55-K63'),
        (3, u'из них:\n паралитический илеус и непроходимость кишечника без грыжи', u'12.5.1', u'K56', u'K56'),
        (2, u'геморрой', u'12.6', u'K64', u'K64'),
        (2, u'болезни печени', u'12.7', u'K70-K76', u'K70-K76'),
        (3, u'из них:\nфиброз и цирроз печени', u'12.7.1', u'K74', u'K74'),
        (2, u'болезни желчного пузыря, желчевыводящих путей', u'12.8', u'K80-K83', u'K80-K83'),
        (2, u'болезни поджелудочной железы', u'12.9', u'K85-K86', u'K85-K86'),
        (3, u'из них:\nострый панкреатит', u'12.9.1', u'K85', u'K85'),
        (1, u'болезни кожи и подкожной клетчатки', u'13.0', u'L00-L98', u'L00-L98'),
        (2, u'из них:\nатопический дерматит', u'13.1', u'L20', u'L20'),
        (2, u'контактный дерматит', u'13.2', u'L23-L25', u'L23-L25'),
        (2, u'другие дерматиты (экзема)', u'13.3', u'L30', u'L30'),
        (2, u'псориаз', u'13.4', u'L40', u'L40'),
        (3, u'из него:\nпсориаз артропатический', u'13.4.1', u'L40.5', u'L40.5'),
        (3, u'дискоидная красная волчанка', u'13.5', u'L93.0', u'L93.0'),
        (3, u'локализованная склеродермия', u'13.6', u'L94.0', u'L94.0'),
        (1, u'болезни костно-мышечной системы и соединительной ткани', u'14.0', u'M00-M99', u'M00-M99'),
        (2, u'из них:\nартропатии', u'14.1', u'M00-M25', u'M00-M25'),
        (3, u'из них:\nпневмококковый артрит и полиартрит', u'14.1.1', u'M00.1', u'M00.1'),
        (3, u'реактивные артропатии', u'14.1.2', u'M02', u'M02'),
        (3, u'ревматоидный артрит (серопозитивный и серонегативный)', u'14.1.3', u'M05-M06', u'M05-M06'),
        (3, u'юношеский (ювенальный) артрит', u'14.1.4', u'M08', u'M08'),
        (3, u'артрозы', u'14.1.5', u'M15-M19', u'M15-M19'),
        (2, u'системные поражения соединительной ткани', u'14.2', u'M30-M35', u'M30-M35'),
        (3, u'из них:\nсистемная красная волчанка', u'14.2.1', u'M32', u'M32'),
        (2, u'деформирующие дорсопатии', u'14.3', u'M40-M43', u'M40-M43'),
        (2, u'cпондилопатии', u'14.4', u'M45-M48', u'M45-M48'),
        (3, u'из них:\nанкилозирующий спондилит', u'14.4.1', u'M45', u'M45'),
        (2, u'поражение синовинальных оболочек и сухожилий', u'14.5', u'M65-M67', u'M65-M67'),
        (2, u'остеопатии и хондропатии', u'14.6', u'M80-M94', u'M80-M94'),
        (3, u'из них:\nостеопорозы', u'14.6.1', u'M80-M81', u'M80-M81'),
        (1, u'болезни мочеполовой системы', u'15.0', u'N00-N99', u'N00-N99'),
        (2, u'из них:\nгломерулярные, тубулоинтерстициальные болезни почек, другие болезни почки и мочеточника', u'15.1', u'N00-N07, N09-N15, N25-N28', u'N00-N07; N09-N15; N25-N28'),
        (2, u'почечная недостаточность', u'15.2', u'N17-N19', u'N17-N19'),
        (2, u'мочекаменная болезнь', u'15.3', u'N20-N21, N23', u'N20-N21; N23'),
        (2, u'другие болезни мочевой системы', u'15.4', u'N30-N32, N34-N36, N39', u'N30-N32; N34-N36; N39'),
        (2, u'болезни предстательной железы', u'15.5', u'N40-N42', u'N40-N42'),
        (2, u'доброкачественная дисплазия молочной   железы', u'15.7', u'N60', u'N60'),
        (2, u'воспалительные болезни женских тазовых органов', u'15.8', u'N70-N73, N75-N76', u'N70-N73; N75-N76'),
        (3, u'из них"\nсальпингит и оофорит', u'15.8.1', u'N70', u'N70'),
        (2, u'эндометриоз', u'15.9', u'N80', u'N80'),
        (2, u'эрозия и эктропион шейки матки', u'15.10', u'N86', u'N86'),
        (2, u'расстройства менструаций', u'15.11', u'N91-N94', u'N91-N94'),
        (1, u'беременность, роды и послеродовой период', u'16.0', u'O00-O99', u'O00-O99'),
        (1, u'отдельные состояния, возникающие в перинатальном периоде', u'17.0', u'P05-P96', u'P05-P96'),
        (1, u'врожденные аномалии (пороки развития), деформации и хромосомные нарушения', u'18.0', u'Q00-Q99', u'Q00-Q99'),
        (2, u'из них:\nврожденные аномалии нервной системы', u'18.1', u'Q00-Q07', u'Q00-Q07'),
        (2, u'врожденные аномалии глаза', u'18.2', u'Q10-Q15', u'Q10-Q15'),
        (2, u'врожденные аномалии системы кровообращения', u'18.3', u'Q20-Q28', u'Q20-Q28'),
        (22, u'врожденные аномалии женских половых органов', u'18.4', u'Q50-Q52', u'Q50-Q52'),
        (2, u'неопределенность пола и псевдогермафродитизм', u'18.5', u'Q56', u'Q56'),
        (2, u'врожденные деформации бедра', u'18.6', u'Q65', u'Q65'),
        (2, u'врожденный ихтиоз', u'18.7', u'Q80', u'Q80'),
        (2, u'нейрофиброматоз', u'18.8', u'Q85.0', u'Q85.0'),
        (2, u'синдром Дауна', u'18.9', u'Q90', u'Q90'),
        (1, u'симптомы, признаки и отклонения от нормы, выявленные при клинических и лабораторных исследованиях, не классифицированные в других рубриках', u'19.0', u'R00-R99', u'R00-R99'),
        (1, u'травмы, отравления и некоторые другие последствия воздействия внешних причин', u'20.0', u'S00-T98', u'S00-T98'),
        (2, u'из них:\nоткрытые укушенные раны (только с кодом внешней причины W54)', u'20.1', u'S01, S11, S21, S31, S41, S51, S61, S71, S81, S91', u'S01; S11; S21; S31; S41; S51; S61; S71; S81; S91'),
    ]

    def __init__(self, parent):
        CForm12.__init__(self, parent)
        self.setTitle(u'Форма N 12 1. Дети (0 - 14 лет включительно)')

    def build(self, params):
        mapMainRows = createMapCodeToRowIdx([row[4] for row in self.MainRows])
        mapCompRows = createMapCodeToRowIdx([row[4] for row in self.CompRows])
        rowSize = 9
        rowCompSize = 2
        reportMainData = [[0] * rowSize for row in xrange(len(self.MainRows))]
        reportCompData = [[0] * rowCompSize for row in xrange(len(self.CompRows))]
        clientIdList = set()
        registeredAll = 0
        registeredFirst = 0
        consistsByEnd = [0, 0, 0]
        params['ageFrom'] = 0
        params['ageTo'] = 14
        query = self.selectData(params)
        while query.next():
            record = query.record()
            clientAge = forceInt(record.value('age'))
            clientId = forceRef(record.value('client_id'))
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            DN = forceBool(record.value('DN'))
            isFirstInLife = forceBool(record.value('isFirstInLife'))
            DNforEndDate = forceBool(record.value('DNforEndDate'))

            if clientId and clientId not in clientIdList:
                clientIdList.add(clientId)
                registeredAll += 1

            cols = [0]
            if clientAge >= 0 and clientAge < 5:
                cols.append(1)
            elif clientAge >= 5 and clientAge < 10:
                cols.append(2)
            if DN:
                consistsByEnd[0] += 1
                if clientAge >= 0 and clientAge < 5:
                    consistsByEnd[1] += 1
                elif clientAge >= 5 and clientAge < 10:
                    consistsByEnd[2] += 1
                cols.append(3)
            if isFirstInLife:
                registeredFirst += 1
                cols.append(4)
                if DN:
                    cols.append(5)
            if DN and not DNforEndDate:
                cols.append(7)
            if DNforEndDate:
                cols.append(8)

            rows = []
            for postfix in postfixs:
                rows.extend(mapMainRows.get((MKB, postfix), []))
                while len(MKB[:-1]) > 4:
                    MKB = MKB[:-1]
                    rows.extend(mapMainRows.get((MKB, postfix), []))

            for row in rows:
                reportLine = reportMainData[row]
                for col in cols:
                    reportLine[col] += 1

        query = self.selectDataZDiagnosis(params)
        while query.next():
            record = query.record()
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            sickCount = forceInt(record.value('sickCount'))
            isNotPrimary = forceBool(record.value('isNotPrimary'))
            for row in mapCompRows.get((MKB, ''), []):
                reportLine = reportCompData[row]
                reportLine[0] += sickCount
                if isNotPrimary:
                    reportLine[1] += sickCount

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'1. Дети (0 - 14 лет включительно)')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        splitTitle(cursor, u'(1000)', u'Код по ОКЕИ: единица - 642; человек - 792')

        tableColumns = [('25%', [u'Наименование классов и отдельных болезней', u'', u'', u'1'], CReportBase.AlignLeft),
            ('5%', [u'№ строки', u'', u'', u'2'], CReportBase.AlignLeft),
            ('16%', [u'Код по МКБ-10 пересмотра', u'', u'', u'3'], CReportBase.AlignLeft),
            ('6%', [u'Зарегистрировано заболеваний', u'всего', u'', u'4'], CReportBase.AlignRight),
            ('6%', [u'', u'из них(из гр. 4):', u'в возрасте 0 - 4 года', u'5'], CReportBase.AlignRight),
            ('6%', [u'', u'', u'в возрасте 5 - 9 лет', u'6'], CReportBase.AlignRight),
            ('6%', [u'', u'из них(из гр. 4):', u'взято под диспансерное наблюдение', u'8'], CReportBase.AlignRight),
            ('6%', [u'', u'', u'с впервые в жизни установленным диагнозом', u'9'], CReportBase.AlignRight),
            ('6%', [u'', u'из заболеваний с впервые в жизни установленным диагнозом (из гр. 9):', u'взято под диспансерное наблюдение', u'10'], CReportBase.AlignRight),
            ('6%', [u'', u'', u'выявлено при профосмотре', u'11'], CReportBase.AlignRight),
            ('6%', [u'Снято с диспансерного наблюдения', u'', u'', u'14'], CReportBase.AlignRight),
            ('6%', [u'Состоит под диспансерным наблюдением на конец отчетного года', u'', u'', u'15'], CReportBase.AlignRight)]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1)  # Наименование
        table.mergeCells(0, 1, 3, 1)  # № стр.
        table.mergeCells(0, 2, 3, 1)  # Код МКБ
        table.mergeCells(0, 3, 1, 7)  # Всего
        table.mergeCells(1, 3, 2, 1)  # Всего
        table.mergeCells(1, 4, 1, 2)
        table.mergeCells(1, 6, 1, 2)
        table.mergeCells(1, 7, 1, 2)
        table.mergeCells(1, 8, 1, 2)
        table.mergeCells(0, 9, 3, 1)
        table.mergeCells(0, 10, 3, 1)
        table.mergeCells(0, 11, 3, 1)

        t = QtGui.QTextBlockFormat()
        for row, rowDescr in enumerate(self.MainRows):
            reportLine = reportMainData[row]
            i = table.addRow()
            t.setLeftMargin(rowDescr[0] * 10)
            table.setText(i, 0, rowDescr[1], blockFormat=t)
            table.setText(i, 1, rowDescr[2])
            table.setText(i, 2, rowDescr[3])
            for col in xrange(rowSize):
                table.setText(i, 3 + col, reportLine[col])

        # 1001
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, '(1001)', u'Код по ОКЕИ: человек - 792')
        cursor.insertText(u"""Число физических лиц зарегистрированных пациентов - всего {0},
из  них  с  диагнозом, установленным впервые в жизни {1},
состоит под диспансерным  наблюдением  на  конец  отчетного года (из гр. 15, стр.  1.0) {2}.""".format(registeredAll, registeredFirst, consistsByEnd[0]))

        # 1002
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, '(1002)', u'Код по ОКЕИ: человек - 792')
        cursor.insertText(u"""Состоит под диспансерным наблюдением на конец отчетного года (из стр. 1.0
гр. 15) детей в возрасте: 0 - 4 года {0}, 5 - 9 лет {1}.""".format(consistsByEnd[1], consistsByEnd[2]))

        # 1003 для психиатрии не заполняем
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, '(1003)', u'Код по ОКЕИ: человек - 792')
        cursor.insertText(u"""Из числа пациентов, состоящих на конец отчетного года под диспансерным
наблюдением (гр. 15): состоит под диспансерным наблюдением лиц с
хроническим вирусным гепатитом (B18) и циррозом печени (K74.6)
одновременно 1 _____ чел.;  с  хроническим   вирусным   гепатитом  (B18)  и
гепатоцеллюлярным раком (C22.0) одновременно 2 _____ чел""")

        # 1100
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock()
        cursor.insertText(u'Дети (до 14 лет включительно).')
        cursor.insertBlock()
        cursor.insertText(u'Факторы, влияющие на состояние здоровья населения')
        cursor.insertBlock()
        cursor.insertText(u'и обращения в медицинские организации')
        cursor.insertBlock()
        cursor.insertText(u'(с профилактической и иными целями)')
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        splitTitle(cursor, '(1100)', u'Код по ОКЕИ: единица - 642')

        tableColumns = [('30%', [u'Наименование', u'', u'1'], CReportBase.AlignLeft),
            ('10%', [u'№ строки', u'', u'2'], CReportBase.AlignLeft),
            ('15%', [u'Код МКБ-10', u'', u'3'], CReportBase.AlignLeft),
            ('15%', [u'Обращения', u'всего', u'4'], CReportBase.AlignRight),
            ('15%', [u'', u'из них: повторные', u'5'], CReportBase.AlignRight), ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 2)

        t = QtGui.QTextBlockFormat()
        for row, rowDescr in enumerate(self.CompRows):
            reportLine = reportCompData[row]
            i = table.addRow()
            t.setLeftMargin(rowDescr[0] * 10)
            table.setText(i, 0, rowDescr[1], blockFormat=t)
            table.setText(i, 1, rowDescr[2])
            table.setText(i, 2, rowDescr[3])
            table.setText(i, 3, reportLine[0])
            table.setText(i, 4, reportLine[1])

        return doc


class CForm12_1500_1900(CForm12):

    # отступ | наименование | № строки | диагнозы титул | диагнозы диапазон
    MainRows = [
        (0, u'Зарегистрировано заболеваний - всего', u'1.0', u'A00-T98', u'A00-T98'),
        (1, u'в том числе:\n некоторые инфекционные и паразитарные болезни', u'2.0', u'A00-B99', u'A00-B99'),
        (2, u'из них:\nкишечные инфекции', u'2.1', u'A00-A09', u'A00-A09'),
        (2, u'менингококковая инфекция', u'2.2', u'A39', u'A39'),
        (1, u'новообразования', u'3.0', u'C00-D48', u'C00-D48'),
        (2, u'из них:\nзлокачественные новообразования', u'3.1', u'C00-C96', u'C00-C96'),
        (3, u'из них:\nзлокачественные новообразования лимфоидной, кроветворной и родственных им тканей', u'3.1.1', u'C81-C96', u'C81-C96'),
        (1, u'болезни крови, кроветворных органов и отдельные нарушения, вовлекающие иммунный механизм', u'4.0', u'D50-D89', u'D50-D89'),
        (2, u'из них:\nанемии', u'4.1', u'D50-D64', u'D50-D64'),
        (1, u'болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'5.0', u'E00-E89', u'E00-E89'),
        (2, u'из них:\nболезни щитовидной железы', u'5.1', u'E00-E07', u'E00-E07'),
        (3, u'из них:\nсиндром врожденной йодной недостаточности', u'5.1.1', u'E00', u'E00'),
        (3, u'Врождённый гипотериоз ', u'5.1.2', u'E03.1', u'E03.1'),
        (2, u'сахарный диабет', u'5.2', u'E10-E14', u'E10-E14'),
        (2, u'гиперфункция гипофиза', u'5.3', u'E22', u'E22'),
        (2, u'адреногенитальные расстройства', u'5.6', u'E25', u'E25'),
        (2, u'рахит', u'5.9', u'E55.0', u'E55.0'),
        (2, u'фенилкетонурия', u'5.10', u'E70.0', u'E70.0'),
        (2, u'нарушения обмена галактозы (галактоземия)', u'5.11', u'E74.2', u'E74.2'),
        (2, u'муковисцидоз', u'5.14', u'E84', u'E84'),
        (1, u'психические расстройства и расстройства поведения', u'6.0', u'F01, F03-F99', u'F01; F03-F99'),
        (2, u'из них:\nумственная отсталость', u'6.1', u'F70-F79', u'F70-F79'),
        (2, u'специфические расстройства речи и языка', u'6.2', u'F80', u'F80'),
        (2, u'специфические расстройства развития моторной функции', u'6.3', u'F82', u'F82'),
        (2, u'общие расстройства психологического развития', u'6.4', u'F84', u'F84'),
        (3, u'из них:\nдетский аутизм, атипичный аутизм, синдром Ретта, дезинтегративное расстройство детского возраста', u'6.4.1', u'F84.0-3', u'F84.0-3'),
        (1, u'болезни нервной системы', u'7.0', u'G00-G98', u'G00-G98'),
        (3, u'из них:\nдетский церебральный паралич', u'7.9.1', u'G80', u'G80'),
        (1, u'болезни глаза и его придаточного аппарата', u'8.0', u'H00-H59', u'H00-H59'),
        (2, u'из них:\nпреретинопатия', u'8.6', u'H35.1', u'H35.1'),
        (1, u'болезни уха и сосцевидного отростка', u'9.0', u'H60-H95', u'H60-H95'),
        (2, u'из них:\nкондуктивная и нейросенсорная потеря слуха', u'9.4', u'H90', u'H90'),
        (1, u'болезни системы кровообращения', u'10.0', u'I00-I99', u'I00-I99'),
        (1, u'болезни органов дыхания', u'11.0', u'J00-J98', u'J00-J98'),
        (2, u'из них:\nострые респираторные инфекции верхних дыхательных путей', u'11.1', u'J00-J06', u'J00-J06'),
        (2, u'грипп', u'11.2', u'J09-J11', u'J09-J11'),
        (2, u'пневмонии', u'11.3', u'J12-J16, J18', u'J12-J16; J18'),
        (1, u'болезни органов пищеварения', u'12.0', u'K00-K92', u'K00-K92'),
        (1, u'болезни кожи и подкожной клетчатки', u'13.0', u'L00-L98', u'L00-L98'),
        (1, u'болезни костно-мышечной системы и соединительной ткани', u'14.0', u'M00-M99', u'M00-M99'),
        (1, u'болезни мочеполовой системы', u'15.0', u'N00-N99', u'N00-N99'),
        (1, u'отдельные состояния, возникающие в перинатальном периоде', u'17.0', u'P05-P96', u'P05-P96'),
        (2, u'из них:\nродовая травма', u'17.1', u'P10-P15', u'P10-P15'),
        (2, u'Внутричерепное нетравматическое кровоизлияние у плода и новорожденного', u'17.2', u'P52', u'P52'),
        (2, u'другие нарушения церебрального статуса у новорожденного', u'17.3', u'P91', u'P91'),
        (1, u'врожденные аномалии (пороки развития), деформации и хромосомные нарушения', u'18.0', u'Q00-Q99', u'Q00-Q99'),
        (2, u'из них:\nврожденные аномалии [пороки развития] нервной системы', u'18.1', u'Q00-Q07', u'Q00-Q07'),
        (2, u'расщелина губы и неба (заячья губа и волчья пасть)', u'18.2', u'Q35-Q37', u'Q35-Q37'),
        (2, u'хромосомные аномалии, не классифицированные в других рубриках', u'18.3', u'Q90-Q99', u'Q90-Q99'),
        (1, u'симптомы, признаки и отклонения от нормы, выявленные при клинических и лабораторных исследованиях, не классифицированные в других рубриках', u'19.0', u'R00-R99', u'R00-R99'),
        (1, u'травмы, отравления и некоторые другие последствия воздействия внешних причин', u'20.0', u'S00-T98', u'S00-T98'),
        (1, u'из них:\nоткрытые укушенные раны (только с кодом внешней причины W54)', u'20.01.20', u'S01, S11, S21, S31, S41, S51, S61, S71, S81, S91', u'S01; S11; S21; S31; S41; S51; S61; S71; S81; S91')
    ]

    # отступ | наименование | № строки | диагнозы титул | диагнозы диапазон
    CompRows = [
        (0, u'Всего', u'1.0', u'Z00-Z99', u'Z00-Z99'),
        (1, u'из них:\nОбращения в медицинские организации для медицинского осмотра и обследования', u'1.1', u'Z00-Z13', u'Z00-Z13'),
        (1, u'потенциальная опасность для здоровья, связанная с инфекционными болезнями', u'1.2', u'Z20-Z29', u'Z20-Z29'),
        (1, u'обращения в медицинские организации в связи с необходимостью проведения специфических процедур и получения медицинской помощи', u'1.4', u'Z40-Z54', u'Z40-Z54'),
        (2, u'из них:\nпомощь, включающая использование реабилитационных процедур', u'1.4.1', u'Z50', u'Z50'),
        (2, u'паллиативная помощь', u'1.4.2', u'Z51.5', u'Z51.5'),
        (1, u'потенциальная опасность для здоровья, связанная с социально-экономическими и психосоциальными обстоятельствами', u'1.5', u'Z55-Z65', u'Z55-Z65'),
        (1, u'потенциальная опасность для здоровья, связанная с личным или семейным анамнезом и определенными обстоятельствами, влияющими на здоровье', u'1.7', u'Z80-Z99', u'Z80-Z99'),
        (2, u'из них:\nзаболевания в семейном анамнезе', u'1.7.1', u'Z80-Z84', u'Z80-Z84'),
        (3, u'из них:\nглухота и потеря слуха', u'1.7.1.1', u'Z82.2', u'Z82.2')
    ]

    def __init__(self, parent):
        CForm12.__init__(self, parent)
        self.setTitle(u'Форма N 12 2. Дети первых трех лет жизни')

    def build(self, params):
        mapMainRows = createMapCodeToRowIdx([row[4] for row in self.MainRows])
        mapCompRows = createMapCodeToRowIdx([row[4] for row in self.CompRows])
        rowSize = 16
        rowCompSize = 5
        reportMainData = [[0] * rowSize for row in xrange(len(self.MainRows))]
        reportCompData = [[0] * rowCompSize for row in xrange(len(self.CompRows))]
        params['ageFrom'] = 0
        params['ageTo'] = 3

        clientIdList = set()
        registeredAll = 0
        registeredFirst = 0
        consistsByEnd = [0, 0, 0]

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'2. Дети первых трех лет жизни')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        splitTitle(cursor, u'(1500)', u'Код по ОКЕИ: единица - 642; человек - 792')
        cursor.insertBlock()

        tableColumns = [
            ('20%', [u'Наименование классов и отдельных болезней', u'', u'', u'', u'1'], CReportBase.AlignLeft),
            ('5%', [u'№ строки', u'', u'', u'', u'2'], CReportBase.AlignLeft),
            ('5%', [u'Код по МКБ-10 пересмотра', u'', u'', u'', u'3'], CReportBase.AlignLeft),
            ('5%', [u'Зарегистрировано заболеваний', u'Всего', u'', u'', u'4'], CReportBase.AlignRight),
            ('3%', [u'', u'из них (из гр. 4):', u'до 1 года', u'', u'5'], CReportBase.AlignRight),
            ('3%', [u'', u'', u'от 1 до 3 лет', u'', u'6'], CReportBase.AlignRight),
            ('3%', [u'', u'', u'до 1 мес.', u'', u'7'], CReportBase.AlignRight),
            ('5%', [u'', u'из них (из гр. 5 и 6):', u'взято под диспансерное наблюдение', u'до 1 года', u'8'], CReportBase.AlignRight),
            ('5%', [u'', u'', u'', u'от 1 до 3 лет', u'9'], CReportBase.AlignRight),
            ('5%', [u'', u'', u'с впервые в жизни установленным диагнозом', u'до 1 года', u'10'], CReportBase.AlignRight),
            ('5%', [u'', u'', u'', u'от 1 до 3 лет', u'11'], CReportBase.AlignRight),
            ('5%', [u'', u'из заболеваний с впервые в жизни установленным диагнозом (из гр. 10 и 11):', u'взято под диспансерное наблюдение', u'до 1 года', u'12'], CReportBase.AlignRight),
            ('5%', [u'', u'', u'', u'от 1 до 3 лет', u'13'], CReportBase.AlignRight),
            ('5%', [u'', u'', u'выявлено при профосмотре', u'до 1 года', u'14'], CReportBase.AlignRight),
            ('5%', [u'', u'', u'', u'от 1 до 3 лет', u'15'], CReportBase.AlignRight),
            ('5%', [u'Снято с диспансерного наблюдения', u'', u'', u'до 1 года', u'16'], CReportBase.AlignRight),
            ('5%', [u'', u'', u'', u'от 1 до 3 лет', u'17'], CReportBase.AlignRight),
            ('5%', [u'Состоит под диспансерным наблюдением на конец отчетного года', u'', u'', u'до 1 года', u'18'], CReportBase.AlignRight),
            ('5%', [u'', u'', u'', u'от 1 до 3 лет', u'19'], CReportBase.AlignRight)
        ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 4, 1)  # Наименование
        table.mergeCells(0, 1, 4, 1)  # № стр.
        table.mergeCells(0, 2, 4, 1)  # Код МКБ
        table.mergeCells(0, 3, 1, 12)
        table.mergeCells(1, 3, 3, 1)
        table.mergeCells(1, 4, 1, 3)
        table.mergeCells(2, 4, 2, 1)
        table.mergeCells(2, 5, 2, 1)
        table.mergeCells(2, 6, 2, 1)
        table.mergeCells(1, 7, 1, 4)
        table.mergeCells(2, 7, 1, 2)
        table.mergeCells(3, 7, 1, 1)
        table.mergeCells(3, 8, 1, 1)
        table.mergeCells(2, 9, 1, 2)
        table.mergeCells(3, 9, 1, 1)
        table.mergeCells(3, 10, 1, 1)
        table.mergeCells(1, 11, 1, 4)
        table.mergeCells(2, 11, 1, 2)
        table.mergeCells(3, 11, 1, 1)
        table.mergeCells(3, 12, 1, 1)
        table.mergeCells(2, 13, 1, 2)
        table.mergeCells(3, 13, 1, 1)
        table.mergeCells(3, 14, 1, 1)
        table.mergeCells(0, 15, 3, 2)
        table.mergeCells(3, 15, 1, 1)
        table.mergeCells(3, 16, 1, 1)
        table.mergeCells(0, 17, 3, 2)
        table.mergeCells(3, 17, 1, 1)
        table.mergeCells(3, 18, 1, 1)

        query = self.selectData(params)
        while query.next():
            record = query.record()
            clientAge = forceInt(record.value('age'))
            dayAge = forceBool(record.value('dayAge'))
            clientId = forceRef(record.value('client_id'))
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            DN = forceBool(record.value('DN'))
            isFirstInLife = forceBool(record.value('isFirstInLife'))
            DNforEndDate = forceBool(record.value('DNforEndDate'))

            if clientId and clientId not in clientIdList:
                clientIdList.add(clientId)
                registeredAll += 1

            cols = [0]
            if clientAge < 1:
                cols.append(1)
                if dayAge:  # до 1 мес.
                    cols.append(3)
                if DN:
                    cols.append(4)
                if isFirstInLife:
                    cols.append(6)
                    if DN:
                        cols.append(8)
            elif clientAge >= 1 and clientAge < 3:
                cols.append(2)
                if DN:
                    cols.append(5)
                if isFirstInLife:
                    cols.append(7)
                    if DN:
                        cols.append(9)
            if DN and not DNforEndDate:
                cols.append(12)
            if DNforEndDate:
                cols.append(13)

            rows = []
            for postfix in postfixs:
                rows.extend(mapMainRows.get((MKB, postfix), []))
                while len(MKB[:-1]) > 4:
                    MKB = MKB[:-1]
                    rows.extend(mapMainRows.get((MKB, postfix), []))

            for row in rows:
                reportLine = reportMainData[row]
                for col in cols:
                    reportLine[col] += 1

        allChildren = 0
        allChildren1 = 0
        childrenWithDiagnos = 0
        childrenWithDiagnos1 = 0
        childrenObserved = 0
        childrenObserved1 = 0

        reportLine = reportMainData[0]
        allChildren = reportLine[0]
        allChildren1 = reportLine[1]
        childrenWithDiagnos = reportLine[6] + reportLine[7]
        childrenWithDiagnos1 = reportLine[6]
        childrenObserved = reportLine[14] + reportLine[15]
        childrenObserved1 = reportLine[14]

        query = self.selectDataZDiagnosis(params)
        while query.next():
            record = query.record()
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            sickCount = forceInt(record.value('sickCount'))
            isNotPrimary = forceBool(record.value('isNotPrimary'))
            for row in mapCompRows.get((MKB, ''), []):
                reportLine = reportCompData[row]
                reportLine[0] += sickCount
                if isNotPrimary:
                    reportLine[1] += sickCount

        cursor.insertBlock()
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportTitle)


        t = QtGui.QTextBlockFormat()
        for row, rowDescr in enumerate(self.MainRows):
            reportLine = reportMainData[row]
            i = table.addRow()
            t.setLeftMargin(rowDescr[0] * 10)
            table.setText(i, 0, rowDescr[1], blockFormat=t)
            table.setText(i, 1, rowDescr[2])
            table.setText(i, 2, rowDescr[3])
            for col in xrange(rowSize):
                table.setText(i, 3 + col, reportLine[col])

        # 1600
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock()
        cursor.insertText(u'Дети первых трех лет жизни.')
        cursor.insertBlock()
        cursor.insertText(u'Факторы, влияющие на состояние здоровья населения')
        cursor.insertBlock()
        cursor.insertText(u'и обращения в медицинские организации (с профилактической и иными целями)')
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        splitTitle(cursor, '(1600)', u'Код по ОКЕИ: единица - 642')

        tableColumns = [('30%', [u'Наименование', u'', u'1'], CReportBase.AlignLeft),
                        ('10%', [u'№ строки', u'', u'2'], CReportBase.AlignLeft),
                        ('15%', [u'Код МКБ-10', u'', u'3'], CReportBase.AlignLeft),
                        ('15%', [u'Обращения', u'всего', u'4'], CReportBase.AlignRight),
                        ('15%', [u'', u'из них: повторные', u'5'], CReportBase.AlignRight), ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 2)

        t = QtGui.QTextBlockFormat()
        for row, rowDescr in enumerate(self.CompRows):
            reportLine = reportCompData[row]
            i = table.addRow()
            t.setLeftMargin(rowDescr[0] * 10)
            table.setText(i, 0, rowDescr[1], blockFormat=t)
            table.setText(i, 1, rowDescr[2])
            table.setText(i, 2, rowDescr[3])
            table.setText(i, 3, reportLine[0])
            table.setText(i, 4, reportLine[1])

        # 1601
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, '(1601)', u'Код по ОКЕИ: человек - 792')
        cursor.insertText(u"""Число  физических  лиц  зарегистрированных  пациентов в возрасте до 3 лет - всего {0},
из них в возрасте до 1 года {1}, из них (из стр. 1) с диагнозом, установленным впервые в жизни {2},
из них в возрасте до 1 года {3}, состоит  под диспансерным наблюдением на конец отчетного
года детей в возрасте до 3 лет (из гр. 18 и 19 стр. 1.0) {4}, из них в возрасте до 1 года {5}.""".format(allChildren, allChildren1, childrenWithDiagnos, childrenWithDiagnos1, childrenObserved, childrenObserved1))

        # 1650
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, '(1650)', u'Код по ОКЕИ: человек - 792')
        cursor.insertText(u"""Из  стр.  1.7.1.1  таблицы  1600:  обследовано  на выявление кондуктивной и
нейросенсорной потери слуха 1 ___________.""")

        # 1700
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, '(1700)', u'Код по ОКЕИ: человек - 792')
        cursor.insertText(u"""Число  новорожденных, поступивших под наблюдение данной организации - всего
1 _________.""")

        # 1800
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, '(1800)', u'Код по ОКЕИ: человек - 792')
        cursor.insertText(u"""Осмотрено новорожденных на 1 этапе           из них: выявлено с нарушениями
аудиологического скрининга 1 _________,      слуха 2 ___________,

из числа выявленных с нарушением слуха
на 1 этапе аудиологического скрининга        из них: выявлено с нарушениями
обследовано на 2 этапе аудиологического      слуха 4 ___________,
скрининга 3 _________,""")

        # 1900
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, '(1900)', u'Код по ОКЕИ: человек - 792')
        cursor.insertText(u"""Из  числа новорожденных поступивших под наблюдение (табл. 1700) обследовано
на:   фенилкетонурию  1  _________,  врожденный  гипотиреоз  2  __________,
адреногенитальный  синдром  3  _____________,  галактоземию 4 ____________,
муковисцидоз 5 ___________.""")

        return doc


class CForm12_2000_2100(CForm12):
    # отступ | наименование | № строки | диагнозы титул | диагнозы диапазон
    MainRows = [
        (0, u'Зарегистрировано заболеваний - всего', u'1.0', u'A00-T98', u'A00-T98'),
        (1, u'в том числе:\nнекоторые инфекционные и паразитарные болезни', u'2.0', u'A00-B99', u'A00-B99'),
        (2, u'из них:\nкишечные инфекции', u'2.1', u'A00-A09', u'A00-A09'),
        (2, u'менингококковая инфекция', u'2.2', u'A39', u'A39'),
        (2, u'вирусный гепатит', u'2.3', u'B15-B19', u'B15-B19'),
        (1, u'новообразования', u'3.0', u'C00-D48', u'C00-D48'),
        (2, u'из них:\nзлокачественные новообразования', u'3.1', u'C00-C96', u'C00-C96'),
        (3, u'из них:\nзлокачественные новообразования лимфоидной, кроветворной и родственных им тканей', u'3.1.1', u'C81-C96', u'C81-C96'),
        (2, u'доброкачественные новобразования', u'3.2', u'D10-D36', u'D10-D36'),
        (1, u'болезни крови, кроветворных органов и отдельные нарушения, вовлекающие иммунный механизм', u'4.0', u'D50-D89', u'D50-D89'),
        (2, u'из них:\nанемии', u'4.1', u'D50-D64', u'D50-D64'),
        (3, u'из них:\n апластические анемии', u'4.1.1', u'D60-D61', u'D60-D61'),
        (2, u'нарушения свертываемости крови, пурпура и другие геморрагические состояния', u'4.2', u'D65-D69', u'D65-D69'),
        (3, u'из них: гемофилия', u'4.2.1', u'D66-D68', u'D66-D68'),
        (2, u'отдельные нарушения, вовлекающие иммунный механизм', u'4.3', u'D80-D89', u'D80-D89'),
        (1, u'болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'5.0', u'E00-E89', u'E00-E89'),
        (2, u'из них:\nболезни щитовидной железы', u'5.1', u'E00-E07', u'E00-E07'),
        (3, u'из них:\nсиндром врожденной йодной недостаточности', u'5.1.1', u'E00', u'E00'),
        (3, u'эндемический зоб, связанный с йодной недостаточностью', u'5.1.2', u'E01.0-2', u'E01.0-2'),
        (3, u'субклинический гипотиреоз вследствие йодной недостаточности и другие формы гипотиреоза', u'5.1.3', u'E02, E03', u'E02; E03'),
        (3, u'другие формы нетоксического зоба', u'5.1.4', u'E04', u'E04'),
        (3, u'тиреотоксикоз (гипертиреоз)', u'5.1.5', u'E05', u'E05'),
        (3, u'тиреоидит', u'5.1.6', u'E06', u'E06'),
        (2, u'сахарный диабет', u'5.2', u'E10-E14', u'E10-E14'),
        (3, u'из него:\nс поражением глаз', u'5.2.1', u'E10.3, E11.3, E12.3, E13.3, E14.3', u'E10.3; E11.3; E12.3; E13.3; E14.3'),
        (3, u'с поражением почек', u'5.2.2', u'E10.2, E11.2, E12.2, E13.2, E14.2', u'E10.2; E11.2; E12.2; E13.2; E14.2'),
        (3, u'из него (из стр. 5.2): сахарный диабет I типа', u'5.2.3', u'E10', u'E10'),
        (3, u'сахарный диабет II типа', u'5.2.4', u'E11', u'E11'),
        (2, u'гиперфункция гипофиза', u'5.3', u'E22', u'E22'),
        (2, u'гипопитуитаризм', u'5.4', u'E23.0', u'E23.0'),
        (2, u'несахарный диабет', u'5.5', u'E23.2', u'E23.2'),
        (2, u'адреногенитальные расстройства', u'5.6', u'E25', u'E25'),
        (2, u'дисфункция яичников', u'5.7', u'E28', u'E28'),
        (2, u'дисфункция яичек', u'5.8', u'E29', u'E29'),
        (2, u'ожирение', u'5.10', u'E66', u'E66'),
        (2, u'фенилкетонурия', u'5.11', u'E70.0', u'E70.0'),
        (2, u'нарушения обмена галактозы (галактоземия)', u'5.12', u'E74.2', u'E74.2'),
        (2, u'болезнь Гоше', u'5.13', u'E75.2', u'E75.2'),
        (2, u'нарушения обмена гликозамигликанов (мукополисахаридоз)', u'5.14', u'E76', u'E76'),
        (2, u'муковисцидоз', u'5.15', u'E84', u'E84'),
        (1, u'психические расстройства и расстройства поведения', u'6.0', u'F01, F03-F99', u'F01; F03-F99'),
        (2, u'из них:\nпсихические расстройства и расстройства поведения, связанные с употреблением психоактивных веществ', u'6.1', u'F10-F19', u'F10-F19'),
        (2, u'детский аутизм, атипичный аутизм, синдром Ретта, дезинтегративное расстройство детского возраста', u'6.2', u'F84.0-3', u'F84.0-3'),
        (1, u'болезни нервной системы', u'7.0', u'G00-G98', u'G00-G98'),
        (2, u'из них:\nвоспалительные болезни центральной нервной системы', u'7.1', u'G00-G09', u'G00-G09'),
        (3, u'из них:\n бактериальный менингит', u'7.1.1', u'G00', u'G00'),
        (3, u'энцефалит, миелит и энцефаломиелит', u'7.1.2', u'G04', u'G04'),
        (2, u'системные атрофии, поражающие преимущественно нервную систему', u'7.2', u'G10-G12', u'G10-G12'),
        (2, u'экстрапирамидные и другие двигательные нарушения', u'7.3', u'G20, G21, G23-G25', u'G20; G21; G23-G25'),
        (3, u'из них:\nдругие экстрапирамидные и двигательные нарушения', u'7.3.2', u'G25', u'G25'),
        (2, u'другие дегенеративные болезни нервной системы', u'7.4', u'G30-G31', u'G30-G31'),
        (2, u'демиелинизирующие болезни центральной нервной системы', u'7.5', u'G35-G37', u'G35-G37'),
        (3, u'из них:\nрассеянный склероз', u'7.5.1', u'G35', u'G35'),
        (2, u'эпизодические и пароксизмальные расстройства', u'7.6', u'G40-G47', u'G40-G47'),
        (3, u'из них:\nэпилепсия, эпилептический статус', u'7.6.1', u'G40-G41', u'G40-G41'),
        (3, u'преходящие транзиторные церебральные ишемические приступы (атаки) и родственные синдромы', u'7.6.2', u'G45', u'G45'),
        (2, u'поражения отдельных нервов, нервных корешков и сплетений, полиневропатии и другие поражения периферической нервной  системы', u'7.7', u'G50-G64', u'G50-G64'),
        (3, u'из них:\nсиндром Гийена-Барре', u'7.7.1', u'G61.0', u'G61.0'),
        (2, u'болезни нервно-мышечного синапса и мышц', u'7.8', u'G70-G73', u'G70-G73'),
        (3, u'из них:\nмиастения ', u'7.8.1', u'G70.0, 2', u'G70.0, 2'),
        (3, u'мышечная дистрофия Дюшенна', u'7.8.2', u'G71.0', u'G71.0'),
        (2, u'церебральный паралич и другие паралитические синдромы', u'7.9', u'G80-G83', u'G80-G83'),
        (3, u'из них:\nцеребральный паралич', u'7.9.1', u'G80', u'G80'),
        (2, u'расстройства вегетативной(автономной) нервной системы', u'7.10', u'G90', u'G90'),
        (2, u'сосудистые миелопатии', u'7.11', u'G95.1', u'G95.1'),
        (1, u'болезни глаза и его придаточного аппарата', u'8.0', u'H00-H59', u'H00-H59'),
        (2, u'из них:\nконъюнктивит', u'8.1', u'H10', u'H10'),
        (2, u'кератит', u'8.2', u'H16', u'H16'),
        (3, u'из него:\nязва роговицы', u'8.2.1', u'H16.0', u'H16.0'),
        (2, u'катаракта', u'8.3', u'H25-H26', u'H25-H26'),
        (2, u'хориоретинальное воспаление', u'8.4', u'H30', u'H30'),
        (2, u'отслойка сетчатки с разрывом сетчатки', u'8.5', u'H33.0', u'H33.0'),
        (2, u'преретинопатия', u'8.6', u'H35.1', u'H35.1'),
        (2, u'дегенерация макулы и заднего полюса', u'8.7', u'H35.3', u'H35.3'),
        (2, u'глаукома', u'8.8', u'H40', u'H40'),
        (2, u'дегенеративная миопия', u'8.9', u'H44.2', u'H44.2'),
        (2, u'болезни зрительного нерва и зрительных путей', u'8.10', u'H46-H48', u'H46-H48'),
        (3, u'атрофия зрительного нерва', u'8.10.1', u'H47.2', u'H47.2'),
        (2, u'болезни мышц глаза, нарушения содружественного движения глаз, аккомодации и рефракции', u'8.11', u'H49-H52', u'H49-H52'),
        (3, u'из них:\nмиопия', u'8.11.1', u'H52.1', u'H52.1'),
        (3, u'астигматизм', u'8.11.2', u'H52.2', u'H52.2'),
        (2, u'слепота и пониженное зрение', u'8.12', u'H54', u'H54'),
        (3, u'из них:\nслепота обоих глаз', u'8.12.1', u'H54.0', u'H54.0'),
        (1, u'болезни уха и сосцевидного отростка', u'9.0', u'H60-H95', u'H60-H95'),
        (2, u'из них:\nболезни наружного уха', u'9.1', u'H60-H61', u'H60-H61'),
        (2, u'болезни среднего уха и сосцевидного отростка', u'9.2', u'H65-H66, H68-H74', u'H65-H66; H68-H74'),
        (3, u'из них:\n острый средний отит', u'9.2.1', u'H65.0, H65.1, H66.0', u'H65.0; H65.1; H66.0'),
        (3, u'хронический средний отит', u'9.2.2', u'H65.2-4, H66.1-3', u'H65.2-4; H66.1-3'),
        (3, u'болезни слуховой (евстахиевой) трубы', u'9.2.3', u'H68-H69', u'H68-H69'),
        (3, u'перфорация барабанной перепонки', u'9.2.4', u'H72', u'H72'),
        (3, u'другие болезни среднего уха и сосцевидного отростка', u'9.2.5', u'H74', u'H74'),
        (2, u'болезни внутреннего уха', u'9.3', u'H80-H81, H83', u'H80-H81; H83'),
        (3, u'из них:\nотосклероз', u'9.3.1', u'H80', u'H80'),
        (3, u'болезнь Меньера', u'9.3.2', u'H81.0', u'H81.0'),
        (2, u'кондуктивная и нейросенсорная потеря слуха', u'9.4', u'H90', u'H90'),
        (3, u'из них:\nкондуктивная потеря слуха двусторонняя', u'9.4.1', u'H90.0', u'H90.0'),
        (3, u'нейросенсорная потеря слуха двусторонняя', u'9.4.2', u'H90.3', u'H90.3'),
        (1, u'болезни системы кровообращения', u'10.0', u'I00-I99', u'I00-I99'),
        (2, u'из них:\nострая ревматическая лихорадка', u'10.1', u'I00-I02', u'I00-I02'),
        (2, u'хронические ревматические болезни сердца', u'10.2', u'I05-I09', u'I05-I09'),
        (3, u'из них:\nревматические поражения клапанов', u'10.2.1', u'I05-I08', u'I05-I08'),
        (2, u'болезни, характеризующиеся повышенным кровяным давлением', u'10.3', u'I10-I13', u'I10-I13'),
        (3, u'из них:\nэссенциальная гипертензия', u'10.3.1', u'I10', u'I10'),
        (3, u'гипертензивная болезнь сердца(гипертоническая болезнь с преимущественным поражением сердца)', u'10.3.2', u'I11', u'I11'),
        (3, u'гипертензивная (гипертоническая) болезнь с преимущественным  поражением  почек', u'10.3.3', u'I12', u'I12'),
        (3, u'гипертензивная (гипертоническая) болезнь с преимущественным  поражением сердца и  почек', u'10.3.4', u'I13', u'I13'),
        (2, u'ишемические болезни сердца', u'10.4', u'I20- I25', u'I20-I25'),
        (3, u'из них:\nстенокардия', u'10.4.1', u'I20', u'I20'),
        (4, u'из нее:\nнестабильная стенокардия', u'10.4.1.1', u'I20.0', u'I20.0'),
        (3, u'острый инфаркт миокарда', u'10.4.2', u'I21', u'I21'),
        (3, u'повторный инфаркт миокарда', u'10.4.3', u'I21', u'I22'),
        (3, u'другие формы острых ишемических болезней сердца', u'10.4.4', u'I24', u'I24'),
        (3, u'хроническая ишемическая болезнь сердца', u'10.4.5', u'I25', u'I25'),
        (4, u'из нее:\nпостинфарктный кардиосклероз', u'10.4.5.1', u'I25.8', u'I25.8'),
        (2, u'другие болезни сердца', u'10.5', u'I30-I51', u'I30-I51'),
        (3, u'из них:\nострый перикардит', u'10.5.1', u'I30', u'I30'),
        (3, u'из них острый и подострый эндокардит', u'10.5.2', u'I33', u'I33'),
        (3, u'острый миокардит', u'10.5.3', u'I40', u'I40'),
        (3, u'кардиомиопатия', u'10.5.4', u'I42', u'I42'),
        (2, u'цереброваскулярные болезни', u'10.6', u'I60-I69', u'I60-I69'),
        (3, u'из них:\nсубарахноидальное кровоизлияние', u'10.6.1', u'I60', u'I60'),
        (3, u'внутримозговое и другое внутричерепное кровоизлияние', u'10.6.2', u'I61, I62', u'I61; I62'),
        (3, u'инфаркт мозга', u'10.6.3', u'I63', u'I63'),
        (3, u'инсульт, не уточненный, как кровоизлияние  или инфаркт', u'10.6.4', u'I64', u'I64'),
        (3, u'закупорка и стеноз прецеребральных, церебральных артерий, не приводящие к инфаркту мозга', u'10.6.5', u'I65-I66', u'I65-I66'),
        (3, u'другие цереброваскулярные болезни', u'10.6.6', u'I67', u'I67'),
        (4, u'из них:\nцеребральный атеросклероз', u'10.6.6.1', u'I67.2', u'I67.2'),
        (3, u'последствия цереброваскулярные болезни', u'10.6.7', u'I69', u'I69'),
        (2, u'эндартериит, тромбангиит облитерирующий', u'10.7', u'I70.2, I73.1', u'I70.2; I73.1'),
        (2, u'болезни вен, лимфатических сосудов и лимфатических узлов', u'10.8', u'I80 - I83, I85 - I89', u'I80 - I83; I85 - I89'),
        (3, u'из них:\nфлебит и тромбофлебит', u'10.8.1', u'I80', u'I80'),
        (3, u'тромбоз портальной вены', u'10.8.2', u'I81', u'I81'),
        (3, u'варикозное расширение вен нижних конечностей', u'10.8.3', u'I83', u'I83'),
        (1, u'болезни органов дыхания', u'11.0', u'J00-J98', u'J00-J98'),
        (2, u'из них:\nострые респираторные инфекции верхних дыхательных путей', u'11.1', u'J00-J06', u'J00-J06'),
        (3, u'из них:\nострый ларингит и трахеит', u'11.1.1', u'J04', u'J04'),
        (3, u'острый обструктивный ларингит (круп) и эпиглоттит', u'11.1.2', u'J05', u'J05'),
        (2, u'грипп', u'11.2', u'J09-J11', u'J09-J11'),
        (2, u'пневмонии', u'11.3', u'J12 - J16, J18', u'J12 - J16; J18'),
        (3, u'Из них бронхопневмония, вызванная S.Pneumoniae', u'11.3.1', u'J13', u'J13'),
        (2, u'острые респираторные инфекции нижних дыхательных путей', u'11.4', u'J20-J22', u'J20-J22'),
        (2, u'аллергический ринит (поллиноз)', u'11.5', u'J30.1', u'J30.1'),
        (2, u'хронические болезни миндалин и аденоидов, перитонзиллярный абсцесс', u'11.6', u'J35-J36', u'J35-J36'),
        (2, u'бронхит хронический и неуточненный, эмфизема', u'11.7', u'J40-J43', u'J40-J43'),
        (2, u'другая хроническая обструктивная легочная болезнь ', u'11.8', u'J44', u'J44'),
        (2, u'бронхоэктатическая болезнь', u'11.9', u'J47', u'J47'),
        (2, u'астма, астматический статус', u'11.10', u'J45-J46', u'J45-J46'),
        (2, u'другие интерстициальные легочные болезни, гнойные  и некротические болезни, состояния нижних дыхательных путей, другие болезни плевры', u'11.11', u'J84-J90, J92-J94', u'J84-J90; J92-J94'),
        (1, u'болезни органов пищеварения', u'12.0', u'K00-K92', u'K00-K92'),
        (2, u'из них:\nязва желудка и двенадцатиперстной перстной кишки', u'12.1', u'K25-K26', u'K25-K26'),
        (2, u'гастрит и дуоденит', u'12.2', u'K29', u'K29'),
        (2, u'грыжи', u'12.3', u'K40-K46', u'K40-K46'),
        (2, u'неинфекционный энтерит и колит', u'12.4', u'K50-K52', u'K50-K52'),
        (2, u'другие болезни кишечника', u'12.5', u'K55-K63', u'K55-K63'),
        (3, u'из них:\n паралитический илеус и непроходимость кишечника без грыжи', u'12.5.1', u'K56', u'K56'),
        (2, u'геморрой', u'12.6', u'K64', u'K64'),
        (2, u'болезни печени', u'12.7', u'K70-K76', u'K70-K76'),
        (3, u'из них:\nфиброз и цирроз печени', u'12.7.1', u'K74', u'K74'),
        (2, u'болезни желчного пузыря, желчевыводящих путей', u'12.8', u'K80-K83', u'K80-K83'),
        (2, u'болезни поджелудочной железы', u'12.9', u'K85-K86', u'K85-K86'),
        (3, u'из них:\nострый панкреатит', u'12.9.1', u'K85', u'K85'),
        (1, u'болезни кожи и подкожной клетчатки', u'13.0', u'L00-L98', u'L00-L98'),
        (2, u'из них:\nатопический дерматит', u'13.1', u'L20', u'L20'),
        (2, u'контактный дерматит', u'13.2', u'L23-L25', u'L23-L25'),
        (2, u'другие дерматиты (экзема)', u'13.3', u'L30', u'L30'),
        (2, u'псориаз', u'13.4', u'L40', u'L40'),
        (3, u'из него:\nпсориаз артропатический', u'13.4.1', u'L40.5', u'L40.5'),
        (3, u'дискоидная красная волчанка', u'13.5', u'L93.0', u'L93.0'),
        (3, u'локализованная склеродермия', u'13.6', u'L94.0', u'L94.0'),
        (1, u'болезни костно-мышечной системы и соединительной ткани', u'14.0', u'M00-M99', u'M00-M99'),
        (2, u'из них:\nартропатии', u'14.1', u'M00-M25', u'M00-M25'),
        (3, u'из них:\nпневмококковый артрит и полиартрит', u'14.1.1', u'M00.1', u'M00.1'),
        (3, u'реактивные артропатии', u'14.1.2', u'M02', u'M02'),
        (3, u'ревматоидный артрит (серопозитивный и серонегативный)', u'14.1.3', u'M05-M06', u'M05-M06'),
        (3, u'юношеский (ювенальный) артрит', u'14.1.4', u'M08', u'M08'),
        (3, u'артрозы', u'14.1.5', u'M15-M19', u'M15-M19'),
        (2, u'системные поражения соединительной ткани', u'14.2', u'M30-M35', u'M30-M35'),
        (3, u'из них:\nсистемная красная волчанка', u'14.2.1', u'M32', u'M32'),
        (2, u'деформирующие дорсопатии', u'14.3', u'M40-M43', u'M40-M43'),
        (2, u'cпондилопатии', u'14.4', u'M45-M48', u'M45-M48'),
        (3, u'из них:\nанкилозирующий спондилит', u'14.4.1', u'M45', u'M45'),
        (2, u'поражение синовинальных оболочек и сухожилий', u'14.5', u'M65-M67', u'M65-M67'),
        (2, u'остеопатии и хондропатии', u'14.6', u'M80-M94', u'M80-M94'),
        (3, u'из них:\nостеопорозы', u'14.6.1', u'M80-M81', u'M80-M81'),
        (1, u'болезни мочеполовой системы', u'15.0', u'N00-N99', u'N00-N99'),
        (2, u'из них:\nгломерулярные, тубулоинтерстициальные болезни почек, другие болезни почки и мочеточника', u'15.1', u'N00-N07, N09-N15, N25-N28', u'N00-N07; N09-N15; N25-N28'),
        (2, u'почечная недостаточность', u'15.2', u'N17-N19', u'N17-N19'),
        (2, u'мочекаменная болезнь', u'15.3', u'N20-N21, N23', u'N20-N21; N23'),
        (2, u'другие болезни мочевой системы', u'15.4', u'N30-N32, N34-N36, N39', u'N30-N32; N34-N36; N39'),
        (2, u'болезни предстательной железы', u'15.5', u'N40-N42', u'N40-N42'),
        (2, u'доброкачественная дисплазия молочной   железы', u'15.7', u'N60', u'N60'),
        (2, u'воспалительные болезни женских тазовых органов', u'15.8', u'N70-N73, N75-N76', u'N70-N73; N75-N76'),
        (3, u'из них"\nсальпингит и оофорит', u'15.8.1', u'N70', u'N70'),
        (2, u'эндометриоз', u'15.9', u'N80', u'N80'),
        (2, u'эрозия и эктропион шейки матки', u'15.10', u'N86', u'N86'),
        (2, u'расстройства менструаций', u'15.11', u'N91-N94', u'N91-N94'),
        (1, u'беременность, роды и послеродовой период', u'16.0', u'O00-O99', u'O00-O99'),
        (1, u'отдельные состояния, возникающие в перинатальном периоде', u'17.0', u'P00-P04', u'P00-P04'),
        (1, u'врожденные аномалии (пороки развития), деформации и хромосомные нарушения', u'18.0', u'Q00-Q99', u'Q00-Q99'),
        (2, u'из них:\nврожденные аномалии нервной системы', u'18.1', u'Q00-Q07', u'Q00-Q07'),
        (2, u'врожденные аномалии глаза', u'18.2', u'Q10-Q15', u'Q10-Q15'),
        (2, u'врожденные аномалии системы кровообращения', u'18.3', u'Q20-Q28', u'Q20-Q28'),
        (22, u'врожденные аномалии женских половых органов', u'18.4', u'Q50-Q52', u'Q50-Q52'),
        (2, u'неопределенность пола и псевдогермафродитизм', u'18.5', u'Q56', u'Q56'),
        (2, u'врожденные деформации бедра', u'18.6', u'Q65', u'Q65'),
        (2, u'врожденный ихтиоз', u'18.7', u'Q80', u'Q80'),
        (2, u'нейрофиброматоз', u'18.8', u'Q85.0', u'Q85.0'),
        (2, u'синдром Дауна', u'18.9', u'Q90', u'Q90'),
        (1, u'симптомы, признаки и отклонения от нормы, выявленные при клинических и лабораторных исследованиях, не классифицированные в других рубриках', u'19.0', u'R00-R99', u'R00-R99'),
        (1, u'травмы, отравления и некоторые другие последствия воздействия внешних причин', u'20.0', u'S00-T98', u'S00-T98'),
        (2, u'из них:\nоткрытые укушенные раны (только с кодом внешней причины W54)', u'20.1', u'S01, S11, S21, S31, S41, S51, S61, S71, S81, S91', u'S01; S11; S21; S31; S41; S51; S61; S71; S81; S91'),
    ]

    def __init__(self, parent):
        CForm12.__init__(self, parent)
        self.setTitle(u'Форма N 12 3. Дети (15 - 17 лет включительно)')

    def build(self, params):
        mapMainRows = createMapCodeToRowIdx([row[4] for row in self.MainRows])
        mapCompRows = createMapCodeToRowIdx([row[4] for row in self.CompRows])
        rowSize = 11
        rowCompSize = 2
        reportMainData = [[0] * rowSize for row in xrange(len(self.MainRows))]
        reportCompData = [[0] * rowCompSize for row in xrange(len(self.CompRows))]
        clientIdList = set()
        registeredAll = 0
        registeredFirst = 0
        consistsByEnd = [0, 0, 0]
        params['ageFrom'] = 15
        params['ageTo'] = 17
        query = self.selectData(params)
        while query.next():
            record = query.record()
            sex = forceInt(record.value('sex'))
            clientId = forceRef(record.value('client_id'))
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            DN = forceBool(record.value('DN'))
            isFirstInLife = forceBool(record.value('isFirstInLife'))
            DNforEndDate = forceBool(record.value('DNforEndDate'))

            if clientId and clientId not in clientIdList:
                clientIdList.add(clientId)
                registeredAll += 1

            cols = [0]
            if sex == 1:
                cols.append(1)
            if DN:
                cols.append(2)
            if isFirstInLife:
                registeredFirst += 1
                cols.append(3)
                if DN:
                    cols.append(4)
                if sex == 1:
                    cols.append(7)
            if DN and not DNforEndDate:
                cols.append(8)
            if DNforEndDate:
                consistsByEnd[0] += 1
                cols.append(9)
                if sex == 1:
                    cols.append(10)

            rows = []
            for postfix in postfixs:
                rows.extend(mapMainRows.get((MKB, postfix), []))
                while len(MKB[:-1]) > 4:
                    MKB = MKB[:-1]
                    rows.extend(mapMainRows.get((MKB, postfix), []))

            for row in rows:
                reportLine = reportMainData[row]
                for col in cols:
                    reportLine[col] += 1

        query = self.selectDataZDiagnosis(params)
        while query.next():
            record = query.record()
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            sickCount = forceInt(record.value('sickCount'))
            isNotPrimary = forceBool(record.value('isNotPrimary'))
            for row in mapCompRows.get((MKB, ''), []):
                reportLine = reportCompData[row]
                reportLine[0] += sickCount
                if isNotPrimary:
                    reportLine[1] += sickCount

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'3. Дети (15 - 17 лет включительно)')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        splitTitle(cursor, u'(2000)', u'Код по ОКЕИ: единица - 642; человек - 792')

        tableColumns = [
            ('17%', [u'Наименование классов и отдельных болезней', u'', u'', u'1'], CReportBase.AlignLeft),
            ('5%', [u'№ строки', u'', u'', u'2'], CReportBase.AlignLeft),
            ('6.5%', [u'Код по МКБ-10 пересмотра', u'', u'', u'3'], CReportBase.AlignLeft),
            ('6.5%', [u'Зарегистрировано пациентов с данным заболеванием', u'Всего', u'', u'4'], CReportBase.AlignRight),
            ('6.5%', [u'', u'из них: юноши', u'', u'7'], CReportBase.AlignRight),
            ('6.5%', [u'', u'из них(из гр. 4):', u'взято под диспансерное наблюдение', u'8'], CReportBase.AlignRight),
            ('6.5%', [u'', u'', u'с впервые в жизни установленным диагнозом', u'9'], CReportBase.AlignRight),
            ('6.5%', [u'', u'из заболеваний с впервые в жизни установленным диагнозом (из гр. 9):', u'взято под диспансерное наблюдение', u'10'], CReportBase.AlignRight),
            ('6.5%', [u'', u'', u'выявлено при профосмотре', u'11'], CReportBase.AlignRight),
            ('6.5%', [u'', u'', u'выявлено при диспансеризации определенных групп взрослого населения', u'12'], CReportBase.AlignRight),
            ('6.5%', [u'', u'из заболеваний с впервые в жизни установленном диагнозом (из гр. 9) юноши', u'', u'13'], CReportBase.AlignRight),
            ('6.5%', [u'Снято с диспансерного наблюдения', u'', u'', u'14'], CReportBase.AlignRight),
            ('6.5%', [u'Состоит под диспан\n-серным наблюде\n-нием на конец отчетного года', u'', u'', u'15'], CReportBase.AlignRight),
            ('6.5%', [u'', u'из них (из гр. 15): юноши', u'', u'16'], CReportBase.AlignRight)
        ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1)  # Наименование
        table.mergeCells(0, 1, 3, 1)  # № стр.
        table.mergeCells(0, 2, 3, 1)  # Код МКБ
        table.mergeCells(0, 3, 1, 8)  # Всего
        table.mergeCells(1, 3, 2, 1)
        table.mergeCells(1, 4, 2, 1)
        table.mergeCells(1, 5, 1, 2)
        table.mergeCells(1, 7, 1, 3)
        table.mergeCells(1, 10, 2, 1)
        table.mergeCells(0, 11, 3, 1)
        table.mergeCells(0, 12, 3, 1)
        table.mergeCells(0, 13, 3, 1)

        t = QtGui.QTextBlockFormat()
        for row, rowDescr in enumerate(self.MainRows):
            reportLine = reportMainData[row]
            i = table.addRow()
            t.setLeftMargin(rowDescr[0] * 10)
            table.setText(i, 0, rowDescr[1], blockFormat=t)
            table.setText(i, 1, rowDescr[2])
            table.setText(i, 2, rowDescr[3])
            for col in xrange(rowSize):
                table.setText(i, 3 + col, reportLine[col])

        # 2001
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, '(2001)', u'Код по ОКЕИ: человек - 792')
        cursor.insertText(u"""Число физических лиц зарегистрированных пациентов - всего {0},
из  них  с  диагнозом, установленным впервые в жизни {1},
состоит под диспансерным  наблюдением  на  конец  отчетного года (из гр. 15, стр.  1.0) {2},
передано под наблюдение во взрослую поликлинику _________.""".format(registeredAll, registeredFirst, consistsByEnd[0]))

        # 2003 для психиатрии не заполняем
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, '(2003)', u'Код по ОКЕИ: человек - 792')
        cursor.insertText(u"""Из числа пациентов, состоящих на конец отчетного года под диспансерным
наблюдением (гр. 15): состоит под диспансерным наблюдением лиц с
хроническим вирусным гепатитом (B18) и циррозом печени (K74.6)
одновременно 1 _____ чел.;  с  хроническим   вирусным   гепатитом  (B18)  и
гепатоцеллюлярным раком (C22.0) одновременно 2 _____ чел.""")

        # 2100
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock()
        cursor.insertText(u'Дети (15 - 17 лет включительно)')
        cursor.insertBlock()
        cursor.insertText(u'Факторы, влияющие на состояние здоровья населения')
        cursor.insertBlock()
        cursor.insertText(u'и обращения в медицинские организации')
        cursor.insertBlock()
        cursor.insertText(u'(с профилактической и иными целями)')
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        splitTitle(cursor, '(2100)', u'Код по ОКЕИ: единица - 642')

        tableColumns = [
            ('30%', [u'Наименование', u'', u'1'], CReportBase.AlignLeft),
            ('10%', [u'№ строки', u'', u'2'], CReportBase.AlignLeft),
            ('15%', [u'Код МКБ-10', u'', u'3'], CReportBase.AlignLeft),
            ('15%', [u'Обращения', u'всего', u'4'], CReportBase.AlignRight),
            ('15%', [u'', u'из них: повторные', u'5'], CReportBase.AlignRight)
        ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 2)

        t = QtGui.QTextBlockFormat()
        for row, rowDescr in enumerate(self.CompRows):
            reportLine = reportCompData[row]
            i = table.addRow()
            t.setLeftMargin(rowDescr[0] * 10)
            table.setText(i, 0, rowDescr[1], blockFormat=t)
            table.setText(i, 1, rowDescr[2])
            table.setText(i, 2, rowDescr[3])
            table.setText(i, 3, reportLine[0])
            table.setText(i, 4, reportLine[1])

        return doc


class CForm12_3000_3100(CForm12):
    # отступ | наименование | № строки | диагнозы титул | диагнозы диапазон
    MainRows = [
        (0, u'Зарегистрировано заболеваний - всего', u'1.0', u'A00-T98', u'A00-T98'),
        (1, u'в том числе:\nнекоторые инфекционные и паразитарные болезни', u'2.0', u'A00-B99', u'A00-B99'),
        (2, u'из них:\nкишечные инфекции', u'2.1', u'A00-A09', u'A00-A09'),
        (2, u'менингококковая инфекция', u'2.2', u'A39', u'A39'),
        (2, u'вирусный гепатит', u'2.3', u'B15-B19', u'B15-B19'),
        (1, u'новообразования', u'3.0', u'C00-D48', u'C00-D48'),
        (2, u'из них:\nзлокачественные новообразования', u'3.1', u'C00-C96', u'C00-C96'),
        (3, u'из них:\nзлокачественные новообразования лимфоидной, кроветворной и родственных им тканей', u'3.1.1', u'C81-C96', u'C81-C96'),
        (2, u'доброкачественные новобразования', u'3.2', u'D10-D36', u'D10-D36'),
        (3, u'из них:\nлейомиома матки', u'3.2.1', u'D25', u'D25'),
        (1, u'болезни крови, кроветворных органов и отдельные нарушения, вовлекающие иммунный механизм', u'4.0', u'D50-D89', u'D50-D89'),
        (2, u'из них:\nанемии', u'4.1', u'D50-D64', u'D50-D64'),
        (3, u'из них:\n апластические анемии', u'4.1.1', u'D60-D61', u'D60-D61'),
        (2, u'нарушения свертываемости крови, пурпура и другие геморрагические состояния', u'4.2', u'D65-D69', u'D65-D69'),
        (3, u'из них: гемофилия', u'4.2.1', u'D66-D68', u'D66-D68'),
        (2, u'отдельные нарушения, вовлекающие иммунный механизм', u'4.3', u'D80-D89', u'D80-D89'),
        (1, u'болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'5.0', u'E00-E89', u'E00-E89'),
        (2, u'из них:\nболезни щитовидной железы', u'5.1', u'E00-E07', u'E00-E07'),
        (3, u'из них:\nсиндром врожденной йодной недостаточности', u'5.1.1', u'E00', u'E00'),
        (3, u'эндемический зоб, связанный с йодной недостаточностью', u'5.1.2', u'E01.0-2', u'E01.0-2'),
        (3, u'субклинический гипотиреоз вследствие йодной недостаточности и другие формы гипотиреоза', u'5.1.3', u'E02, E03', u'E02; E03'),
        (3, u'другие формы нетоксического зоба', u'5.1.4', u'E04', u'E04'),
        (3, u'тиреотоксикоз (гипертиреоз)', u'5.1.5', u'E05', u'E05'),
        (3, u'тиреоидит', u'5.1.6', u'E06', u'E06'),
        (2, u'сахарный диабет', u'5.2', u'E10-E14', u'E10-E14'),
        (3, u'из него:\nс поражением глаз', u'5.2.1', u'E10.3, E11.3, E12.3, E13.3, E14.3', u'E10.3; E11.3; E12.3; E13.3; E14.3'),
        (3, u'с поражением почек', u'5.2.2', u'E10.2, E11.2, E12.2, E13.2, E14.2', u'E10.2; E11.2; E12.2; E13.2; E14.2'),
        (3, u'из него (из стр. 5.2): сахарный диабет I типа', u'5.2.3', u'E10', u'E10'),
        (3, u'сахарный диабет II типа', u'5.2.4', u'E11', u'E11'),
        (2, u'гиперфункция гипофиза', u'5.3', u'E22', u'E22'),
        (2, u'гипопитуитаризм', u'5.4', u'E23.0', u'E23.0'),
        (2, u'несахарный диабет', u'5.5', u'E23.2', u'E23.2'),
        (2, u'адреногенитальные расстройства', u'5.6', u'E25', u'E25'),
        (2, u'дисфункция яичников', u'5.7', u'E28', u'E28'),
        (2, u'дисфункция яичек', u'5.8', u'E29', u'E29'),
        (2, u'ожирение', u'5.10', u'E66', u'E66'),
        (2, u'фенилкетонурия', u'5.11', u'E70.0', u'E70.0'),
        (2, u'нарушения обмена галактозы (галактоземия)', u'5.12', u'E74.2', u'E74.2'),
        (2, u'болезнь Гоше', u'5.13', u'E75.2', u'E75.2'),
        (2, u'нарушения обмена гликозамигликанов (мукополисахаридоз)', u'5.14', u'E76', u'E76'),
        (2, u'муковисцидоз', u'5.15', u'E84', u'E84'),
        (1, u'психические расстройства и расстройства поведения', u'6.0', u'F01, F03-F99', u'F01; F03-F99'),
        (2, u'из них:\nпсихические расстройства и расстройства поведения, связанные с употреблением психоактивных веществ', u'6.1', u'F10-F19', u'F10-F19'),
        (1, u'болезни нервной системы', u'7.0', u'G00-G98', u'G00-G98'),
        (2, u'из них:\nвоспалительные болезни центральной нервной системы', u'7.1', u'G00-G09', u'G00-G09'),
        (3, u'из них:\n бактериальный менингит', u'7.1.1', u'G00', u'G00'),
        (3, u'энцефалит, миелит и энцефаломиелит', u'7.1.2', u'G04', u'G04'),
        (2, u'системные атрофии, поражающие преимущественно нервную систему', u'7.2', u'G10-G12', u'G10-G12'),
        (2, u'экстрапирамидные и другие двигательные нарушения', u'7.3', u'G20, G21, G23-G25', u'G20; G21; G23-G25'),
        (3, u'из них:\nдругие экстрапирамидные и двигательные нарушения', u'7.3.2', u'G25', u'G25'),
        (2, u'другие дегенеративные болезни нервной системы', u'7.4', u'G30-G31', u'G30-G31'),
        (3, u'из них болезнь Альцгеймера', u'7.4.1', u'G30', u'G30'),
        (2, u'демиелинизирующие болезни центральной нервной системы', u'7.5', u'G35-G37', u'G35-G37'),
        (3, u'из них:\nрассеянный склероз', u'7.5.1', u'G35', u'G35'),
        (2, u'эпизодические и пароксизмальные расстройства', u'7.6', u'G40-G47', u'G40-G47'),
        (3, u'из них:\nэпилепсия, эпилептический статус', u'7.6.1', u'G40-G41', u'G40-G41'),
        (3, u'преходящие транзиторные церебральные ишемические приступы (атаки) и родственные синдромы', u'7.6.2', u'G45', u'G45'),
        (2, u'поражения отдельных нервов, нервных корешков и сплетений, полиневропатии и другие поражения периферической нервной  системы', u'7.7', u'G50-G64', u'G50-G64'),
        (3, u'из них:\nсиндром Гийена-Барре', u'7.7.1', u'G61.0', u'G61.0'),
        (2, u'болезни нервно-мышечного синапса и мышц', u'7.8', u'G70-G73', u'G70-G73'),
        (3, u'из них:\nмиастения ', u'7.8.1', u'G70.0, 2', u'G70.0, 2'),
        (3, u'мышечная дистрофия Дюшенна', u'7.8.2', u'G71.0', u'G71.0'),
        (2, u'церебральный паралич и другие паралитические синдромы', u'7.9', u'G80-G83', u'G80-G83'),
        (3, u'из них:\nцеребральный паралич', u'7.9.1', u'G80', u'G80'),
        (2, u'расстройства вегетативной(автономной) нервной системы', u'7.10', u'G90', u'G90'),
        (2, u'сосудистые миелопатии', u'7.11', u'G95.1', u'G95.1'),
        (1, u'болезни глаза и его придаточного аппарата', u'8.0', u'H00-H59', u'H00-H59'),
        (2, u'из них:\nконъюнктивит', u'8.1', u'H10', u'H10'),
        (2, u'кератит', u'8.2', u'H16', u'H16'),
        (3, u'из него:\nязва роговицы', u'8.2.1', u'H16.0', u'H16.0'),
        (2, u'катаракта', u'8.3', u'H25-H26', u'H25-H26'),
        (2, u'хориоретинальное воспаление', u'8.4', u'H30', u'H30'),
        (2, u'отслойка сетчатки с разрывом сетчатки', u'8.5', u'H33.0', u'H33.0'),
        (2, u'преретинопатия', u'8.6', u'H35.1', u'H35.1'),
        (2, u'дегенерация макулы и заднего полюса', u'8.7', u'H35.3', u'H35.3'),
        (2, u'глаукома', u'8.8', u'H40', u'H40'),
        (2, u'дегенеративная миопия', u'8.9', u'H44.2', u'H44.2'),
        (2, u'болезни зрительного нерва и зрительных путей', u'8.10', u'H46-H48', u'H46-H48'),
        (3, u'атрофия зрительного нерва', u'8.10.1', u'H47.2', u'H47.2'),
        (2, u'болезни мышц глаза, нарушения содружественного движения глаз, аккомодации и рефракции', u'8.11', u'H49-H52', u'H49-H52'),
        (3, u'из них:\nмиопия', u'8.11.1', u'H52.1', u'H52.1'),
        (3, u'астигматизм', u'8.11.2', u'H52.2', u'H52.2'),
        (2, u'слепота и пониженное зрение', u'8.12', u'H54', u'H54'),
        (3, u'из них:\nслепота обоих глаз', u'8.12.1', u'H54.0', u'H54.0'),
        (1, u'болезни уха и сосцевидного отростка', u'9.0', u'H60-H95', u'H60-H95'),
        (2, u'из них:\nболезни наружного уха', u'9.1', u'H60-H61', u'H60-H61'),
        (2, u'болезни среднего уха и сосцевидного отростка', u'9.2', u'H65-H66, H68-H74', u'H65-H66; H68-H74'),
        (3, u'из них:\n острый средний отит', u'9.2.1', u'H65.0, H65.1, H66.0', u'H65.0; H65.1; H66.0'),
        (3, u'хронический средний отит', u'9.2.2', u'H65.2-4, H66.1-3', u'H65.2-4; H66.1-3'),
        (3, u'болезни слуховой (евстахиевой) трубы', u'9.2.3', u'H68-H69', u'H68-H69'),
        (3, u'перфорация барабанной перепонки', u'9.2.4', u'H72', u'H72'),
        (3, u'другие болезни среднего уха и сосцевидного отростка', u'9.2.5', u'H74', u'H74'),
        (2, u'болезни внутреннего уха', u'9.3', u'H80-H81, H83', u'H80-H81; H83'),
        (3, u'из них:\nотосклероз', u'9.3.1', u'H80', u'H80'),
        (3, u'болезнь Меньера', u'9.3.2', u'H81.0', u'H81.0'),
        (2, u'кондуктивная и нейросенсорная потеря слуха', u'9.4', u'H90', u'H90'),
        (3, u'из них:\nкондуктивная потеря слуха двусторонняя', u'9.4.1', u'H90.0', u'H90.0'),
        (3, u'нейросенсорная потеря слуха двусторонняя', u'9.4.2', u'H90.3', u'H90.3'),
        (1, u'болезни системы кровообращения', u'10.0', u'I00-I99', u'I00-I99'),
        (2, u'из них:\nострая ревматическая лихорадка', u'10.1', u'I00-I02', u'I00-I02'),
        (2, u'хронические ревматические болезни сердца', u'10.2', u'I05-I09', u'I05-I09'),
        (3, u'из них:\nревматические поражения клапанов', u'10.2.1', u'I05-I08', u'I05-I08'),
        (2, u'болезни, характеризующиеся повышенным кровяным давлением', u'10.3', u'I10-I13', u'I10-I13'),
        (3, u'из них:\nэссенциальная гипертензия', u'10.3.1', u'I10', u'I10'),
        (3, u'гипертензивная болезнь сердца(гипертоническая болезнь с преимущественным поражением сердца)', u'10.3.2', u'I11', u'I11'),
        (3, u'гипертензивная (гипертоническая) болезнь с преимущественным  поражением  почек', u'10.3.3', u'I12', u'I12'),
        (3, u'гипертензивная (гипертоническая) болезнь с преимущественным  поражением сердца и  почек', u'10.3.4', u'I13', u'I13'),
        (2, u'ишемические болезни сердца', u'10.4', u'I20- I25', u'I20-I25'),
        (3, u'из них:\nстенокардия', u'10.4.1', u'I20', u'I20'),
        (4, u'из нее:\nнестабильная стенокардия', u'10.4.1.1', u'I20.0', u'I20.0'),
        (3, u'острый инфаркт миокарда', u'10.4.2', u'I21', u'I21'),
        (3, u'повторный инфаркт миокарда', u'10.4.3', u'I21', u'I22'),
        (3, u'другие формы острых ишемических болезней сердца', u'10.4.4', u'I24', u'I24'),
        (3, u'хроническая ишемическая болезнь сердца', u'10.4.5', u'I25', u'I25'),
        (4, u'из нее:\nпостинфарктный кардиосклероз', u'10.4.5.1', u'I25.8', u'I25.8'),
        (2, u'другие болезни сердца', u'10.5', u'I30-I51', u'I30-I51'),
        (3, u'из них:\nострый перикардит', u'10.5.1', u'I30', u'I30'),
        (3, u'из них острый и подострый эндокардит', u'10.5.2', u'I33', u'I33'),
        (3, u'острый миокардит', u'10.5.3', u'I40', u'I40'),
        (3, u'кардиомиопатия', u'10.5.4', u'I42', u'I42'),
        (2, u'цереброваскулярные болезни', u'10.6', u'I60-I69', u'I60-I69'),
        (3, u'из них:\nсубарахноидальное кровоизлияние', u'10.6.1', u'I60', u'I60'),
        (3, u'внутримозговое и другое внутричерепное кровоизлияние', u'10.6.2', u'I61, I62', u'I61; I62'),
        (3, u'инфаркт мозга', u'10.6.3', u'I63', u'I63'),
        (3, u'инсульт, не уточненный, как кровоизлияние  или инфаркт', u'10.6.4', u'I64', u'I64'),
        (3, u'закупорка и стеноз прецеребральных, церебральных артерий, не приводящие к инфаркту мозга', u'10.6.5', u'I65-I66', u'I65-I66'),
        (3, u'другие цереброваскулярные болезни', u'10.6.6', u'I67', u'I67'),
        (3, u'последствия цереброваскулярные болезни', u'10.6.7', u'I69', u'I69'),
        (2, u'эндартериит, тромбангиит облитерирующий', u'10.7', u'I70.2, I73.1', u'I70.2; I73.1'),
        (2, u'болезни вен, лимфатических сосудов и лимфатических узлов', u'10.8', u'I80 - I83, I85 - I89', u'I80 - I83; I85 - I89'),
        (3, u'из них:\nфлебит и тромбофлебит', u'10.8.1', u'I80', u'I80'),
        (3, u'тромбоз портальной вены', u'10.8.2', u'I81', u'I81'),
        (3, u'варикозное расширение вен нижних конечностей', u'10.8.3', u'I83', u'I83'),
        (1, u'болезни органов дыхания', u'11.0', u'J00-J98', u'J00-J98'),
        (2, u'из них:\nострые респираторные инфекции верхних дыхательных путей', u'11.1', u'J00-J06', u'J00-J06'),
        (3, u'из них:\nострый ларингит и трахеит', u'11.1.1', u'J04', u'J04'),
        (3, u'острый обструктивный ларингит (круп) и эпиглоттит', u'11.1.2', u'J05', u'J05'),
        (2, u'грипп', u'11.2', u'J09-J11', u'J09-J11'),
        (2, u'пневмонии', u'11.3', u'J12 - J16, J18', u'J12 - J16; J18'),
        (3, u'Из них бронхопневмония, вызванная S.Pneumoniae', u'11.3.1', u'J13', u'J13'),
        (2, u'острые респираторные инфекции нижних дыхательных путей', u'11.4', u'J20-J22', u'J20-J22'),
        (2, u'аллергический ринит (поллиноз)', u'11.5', u'J30.1', u'J30.1'),
        (2, u'хронические болезни миндалин и аденоидов, перитонзиллярный абсцесс', u'11.6', u'J35-J36', u'J35-J36'),
        (2, u'бронхит хронический и неуточненный, эмфизема', u'11.7', u'J40-J43', u'J40-J43'),
        (2, u'другая хроническая обструктивная легочная болезнь ', u'11.8', u'J44', u'J44'),
        (2, u'бронхоэктатическая болезнь', u'11.9', u'J47', u'J47'),
        (2, u'астма, астматический статус', u'11.10', u'J45-J46', u'J45-J46'),
        (2, u'другие интерстициальные легочные болезни, гнойные  и некротические болезни, состояния нижних дыхательных путей, другие болезни плевры', u'11.11', u'J84-J90, J92-J94', u'J84-J90; J92-J94'),
        (1, u'болезни органов пищеварения', u'12.0', u'K00-K92', u'K00-K92'),
        (2, u'из них:\nязва желудка и двенадцатиперстной перстной кишки', u'12.1', u'K25-K26', u'K25-K26'),
        (2, u'гастрит и дуоденит', u'12.2', u'K29', u'K29'),
        (2, u'грыжи', u'12.3', u'K40-K46', u'K40-K46'),
        (2, u'неинфекционный энтерит и колит', u'12.4', u'K50-K52', u'K50-K52'),
        (2, u'другие болезни кишечника', u'12.5', u'K55-K63', u'K55-K63'),
        (3, u'из них:\n паралитический илеус и непроходимость кишечника без грыжи', u'12.5.1', u'K56', u'K56'),
        (2, u'геморрой', u'12.6', u'K64', u'K64'),
        (2, u'болезни печени', u'12.7', u'K70-K76', u'K70-K76'),
        (3, u'из них:\nфиброз и цирроз печени', u'12.7.1', u'K74', u'K74'),
        (2, u'болезни желчного пузыря, желчевыводящих путей', u'12.8', u'K80-K83', u'K80-K83'),
        (2, u'болезни поджелудочной железы', u'12.9', u'K85-K86', u'K85-K86'),
        (3, u'из них:\nострый панкреатит', u'12.9.1', u'K85', u'K85'),
        (1, u'болезни кожи и подкожной клетчатки', u'13.0', u'L00-L98', u'L00-L98'),
        (2, u'из них:\nатопический дерматит', u'13.1', u'L20', u'L20'),
        (2, u'контактный дерматит', u'13.2', u'L23-L25', u'L23-L25'),
        (2, u'другие дерматиты (экзема)', u'13.3', u'L30', u'L30'),
        (2, u'псориаз', u'13.4', u'L40', u'L40'),
        (3, u'из него:\nпсориаз артропатический', u'13.4.1', u'L40.5', u'L40.5'),
        (3, u'дискоидная красная волчанка', u'13.5', u'L93.0', u'L93.0'),
        (3, u'локализованная склеродермия', u'13.6', u'L94.0', u'L94.0'),
        (1, u'болезни костно-мышечной системы и соединительной ткани', u'14.0', u'M00-M99', u'M00-M99'),
        (2, u'из них:\nартропатии', u'14.1', u'M00-M25', u'M00-M25'),
        (3, u'из них:\nпневмококковый артрит и полиартрит', u'14.1.1', u'M00.1', u'M00.1'),
        (3, u'реактивные артропатии', u'14.1.2', u'M02', u'M02'),
        (3, u'ревматоидный артрит (серопозитивный и серонегативный)', u'14.1.3', u'M05-M06', u'M05-M06'),
        (3, u'артрозы', u'14.1.5', u'M15-M19', u'M15-M19'),
        (2, u'системные поражения соединительной ткани', u'14.2', u'M30-M35', u'M30-M35'),
        (3, u'из них:\nсистемная красная волчанка', u'14.2.1', u'M32', u'M32'),
        (2, u'деформирующие дорсопатии', u'14.3', u'M40-M43', u'M40-M43'),
        (2, u'cпондилопатии', u'14.4', u'M45-M48', u'M45-M48'),
        (3, u'из них:\nанкилозирующий спондилит', u'14.4.1', u'M45', u'M45'),
        (2, u'поражение синовинальных оболочек и сухожилий', u'14.5', u'M65-M67', u'M65-M67'),
        (2, u'остеопатии и хондропатии', u'14.6', u'M80-M94', u'M80-M94'),
        (3, u'из них:\nостеопорозы', u'14.6.1', u'M80-M81', u'M80-M81'),
        (1, u'болезни мочеполовой системы', u'15.0', u'N00-N99', u'N00-N99'),
        (2, u'из них:\nгломерулярные, тубулоинтерстициальные болезни почек, другие болезни почки и мочеточника', u'15.1', u'N00-N07, N09-N15, N25-N28', u'N00-N07; N09-N15; N25-N28'),
        (2, u'почечная недостаточность', u'15.2', u'N17-N19', u'N17-N19'),
        (2, u'мочекаменная болезнь', u'15.3', u'N20-N21, N23', u'N20-N21; N23'),
        (2, u'другие болезни мочевой системы', u'15.4', u'N30-N32, N34-N36, N39', u'N30-N32; N34-N36; N39'),
        (2, u'болезни предстательной железы', u'15.5', u'N40-N42', u'N40-N42'),
        (2, u'доброкачественная дисплазия молочной   железы', u'15.7', u'N60', u'N60'),
        (2, u'воспалительные болезни женских тазовых органов', u'15.8', u'N70-N73, N75-N76', u'N70-N73; N75-N76'),
        (3, u'из них"\nсальпингит и оофорит', u'15.8.1', u'N70', u'N70'),
        (2, u'эндометриоз', u'15.9', u'N80', u'N80'),
        (2, u'эрозия и эктропион шейки матки', u'15.10', u'N86', u'N86'),
        (2, u'расстройства менструаций', u'15.11', u'N91-N94', u'N91-N94'),
        (2, u'женское бесплодие', u'15.12', u'N97', u'N97'),
        (1, u'беременность, роды и послеродовой период', u'16.0', u'O00-O99', u'O00-O99'),
        (1, u'отдельные состояния, возникающие в перинатальном периоде', u'17.0', u'P00-P04', u'P00-P04'),
        (1, u'врожденные аномалии (пороки развития), деформации и хромосомные нарушения', u'18.0', u'Q00-Q99', u'Q00-Q99'),
        (2, u'из них:\nврожденные аномалии нервной системы', u'18.1', u'Q00-Q07', u'Q00-Q07'),
        (2, u'врожденные аномалии глаза', u'18.2', u'Q10-Q15', u'Q10-Q15'),
        (2, u'врожденные аномалии системы кровообращения', u'18.3', u'Q20-Q28', u'Q20-Q28'),
        (22, u'врожденные аномалии женских половых органов', u'18.4', u'Q50-Q52', u'Q50-Q52'),
        (2, u'неопределенность пола и псевдогермафродитизм', u'18.5', u'Q56', u'Q56'),
        (2, u'врожденные деформации бедра', u'18.6', u'Q65', u'Q65'),
        (2, u'врожденный ихтиоз', u'18.7', u'Q80', u'Q80'),
        (2, u'нейрофиброматоз', u'18.8', u'Q85.0', u'Q85.0'),
        (2, u'синдром Дауна', u'18.9', u'Q90', u'Q90'),
        (1, u'симптомы, признаки и отклонения от нормы, выявленные при клинических и лабораторных исследованиях, не классифицированные в других рубриках', u'19.0', u'R00-R99', u'R00-R99'),
        (1, u'травмы, отравления и некоторые другие последствия воздействия внешних причин', u'20.0', u'S00-T98', u'S00-T98'),
        (2, u'из них:\nоткрытые укушенные раны (только с кодом внешней причины W54)', u'20.1', u'S01, S11, S21, S31, S41, S51, S61, S71, S81, S91', u'S01; S11; S21; S31; S41; S51; S61; S71; S81; S91'),
    ]

    def __init__(self, parent):
        CForm12.__init__(self, parent)
        self.setTitle(u'Форма N 12 4. Взрослые 18 лет и более')

    def build(self, params):
        mapMainRows = createMapCodeToRowIdx([row[4] for row in self.MainRows])
        mapCompRows = createMapCodeToRowIdx([row[4] for row in self.CompRows])
        rowSize = 8
        rowCompSize = 2
        reportMainData = [[0] * rowSize for row in xrange(len(self.MainRows))]
        reportCompData = [[0] * rowCompSize for row in xrange(len(self.CompRows))]
        clientIdList = set()
        registeredAll = 0
        registeredFirst = 0
        consistsByEnd = [0, 0, 0]
        params['ageFrom'] = 18
        params['ageTo'] = 150
        query = self.selectData(params)
        while query.next():
            record = query.record()
            sex = forceInt(record.value('sex'))
            clientId = forceRef(record.value('client_id'))
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            DN = forceBool(record.value('DN'))
            isFirstInLife = forceBool(record.value('isFirstInLife'))
            DNforEndDate = forceBool(record.value('DNforEndDate'))

            if clientId and clientId not in clientIdList:
                clientIdList.add(clientId)
                registeredAll += 1

            cols = [0]
            if DN:
                cols.append(1)
            if isFirstInLife:
                registeredFirst += 1
                cols.append(2)
                if DN:
                    cols.append(3)
            if DN and not DNforEndDate:
                cols.append(6)
            if DNforEndDate:
                consistsByEnd[0] += 1
                cols.append(7)

            rows = []
            for postfix in postfixs:
                rows.extend(mapMainRows.get((MKB, postfix), []))
                while len(MKB[:-1]) > 4:
                    MKB = MKB[:-1]
                    rows.extend(mapMainRows.get((MKB, postfix), []))

            for row in rows:
                reportLine = reportMainData[row]
                for col in cols:
                    reportLine[col] += 1

        query = self.selectDataZDiagnosis(params)
        while query.next():
            record = query.record()
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            sickCount = forceInt(record.value('sickCount'))
            isNotPrimary = forceBool(record.value('isNotPrimary'))
            for row in mapCompRows.get((MKB, ''), []):
                reportLine = reportCompData[row]
                reportLine[0] += sickCount
                if isNotPrimary:
                    reportLine[1] += sickCount

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'4. Взрослые 18 лет и более')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        splitTitle(cursor, u'(3000)', u'Код по ОКЕИ: единица - 642; человек - 792')

        tableColumns = [
            ('15%', [u'Наименование классов и отдельных болезней', u'', u'', u'1'], CReportBase.AlignLeft),
            ('5%', [u'№ строки', u'', u'', u'2'], CReportBase.AlignLeft),
            ('10%', [u'Код по МКБ-10 пересмотра', u'', u'', u'3'], CReportBase.AlignLeft),
            ('10%', [u'Зарегистрировано заболеваний', u'Всего', u'', u'4'], CReportBase.AlignRight),
            ('10%', [u'', u'из них(из гр. 4):', u'взято под диспансерное наблюдение', u'8'], CReportBase.AlignRight),
            ('10%', [u'', u'', u'с впервые в жизни установленным диагнозом', u'9'], CReportBase.AlignRight),
            ('10%', [u'', u'из заболеваний с впервые в жизни установленным диагнозом (из гр. 9):', u'взято под диспансерное наблюдение', u'10'], CReportBase.AlignRight),
            ('10%', [u'', u'', u'выявлено при профосмотре', u'11'], CReportBase.AlignRight),
            ('10%', [u'', u'', u'выявлено при диспансеризации определенных групп взрослого населения', u'12'], CReportBase.AlignRight),
            ('10%', [u'Снято с диспансерного наблюдения', u'', u'', u'14'], CReportBase.AlignRight),
            ('10%', [u'Состоит под диспансерным наблюдением на конец отчетного года', u'', u'', u'15'], CReportBase.AlignRight)
        ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1)  # Наименование
        table.mergeCells(0, 1, 3, 1)  # № стр.
        table.mergeCells(0, 2, 3, 1)  # Код МКБ
        table.mergeCells(0, 3, 1, 6)  # Всего
        table.mergeCells(1, 3, 2, 1)
        table.mergeCells(1, 4, 1, 2)
        table.mergeCells(1, 6, 1, 3)
        table.mergeCells(0, 9, 3, 1)
        table.mergeCells(0, 10, 3, 1)

        t = QtGui.QTextBlockFormat()
        for row, rowDescr in enumerate(self.MainRows):
            reportLine = reportMainData[row]
            i = table.addRow()
            t.setLeftMargin(rowDescr[0] * 10)
            table.setText(i, 0, rowDescr[1], blockFormat=t)
            table.setText(i, 1, rowDescr[2])
            table.setText(i, 2, rowDescr[3])
            for col in xrange(rowSize):
                table.setText(i, 3 + col, reportLine[col])

        # 3002
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, '(3002)', u'Код по ОКЕИ: человек - 792')
        cursor.insertText(u"""Число физических лиц зарегистрированных пациентов - всего {0},
из  них  с  диагнозом, установленным впервые в жизни {1},
состоит под диспансерным  наблюдением  на  конец  отчетного года (из гр. 15, стр.  1.0) {2}""".format(registeredAll, registeredFirst, consistsByEnd[0]))

        # 3003 для психиатрии не заполняем
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, '(2003)', u'Код по ОКЕИ: человек - 792')
        cursor.insertText(u"""Из числа пациентов, состоящих на конец отчетного года под диспансерным
наблюдением (гр. 15): состоит под диспансерным наблюдением лиц с
хроническим вирусным гепатитом (B18) и циррозом печени (K74.6)
одновременно 1 _____ чел.;  с  хроническим   вирусным   гепатитом  (B18)  и
гепатоцеллюлярным раком (C22.0) одновременно 2 _____ чел.""")

        # 3100
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock()
        cursor.insertText(u'Взрослые 18 лет и более')
        cursor.insertBlock()
        cursor.insertText(u'Факторы, влияющие на состояние здоровья населения')
        cursor.insertBlock()
        cursor.insertText(u'и обращения в медицинские организации')
        cursor.insertBlock()
        cursor.insertText(u'(с профилактической и иными целями)')
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        splitTitle(cursor, '(3100)', u'Код по ОКЕИ: единица - 642')

        tableColumns = [('30%', [u'Наименование', u'', u'1'], CReportBase.AlignLeft),
            ('10%', [u'№ строки', u'', u'2'], CReportBase.AlignLeft),
            ('15%', [u'Код МКБ-10', u'', u'3'], CReportBase.AlignLeft),
            ('15%', [u'Обращения', u'всего', u'4'], CReportBase.AlignRight),
            ('15%', [u'', u'из них: повторные', u'5'], CReportBase.AlignRight), ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 2)

        t = QtGui.QTextBlockFormat()
        for row, rowDescr in enumerate(self.CompRows):
            reportLine = reportCompData[row]
            i = table.addRow()
            t.setLeftMargin(rowDescr[0] * 10)
            table.setText(i, 0, rowDescr[1], blockFormat=t)
            table.setText(i, 1, rowDescr[2])
            table.setText(i, 2, rowDescr[3])
            table.setText(i, 3, reportLine[0])
            table.setText(i, 4, reportLine[1])

        return doc


class CForm12_4000_4100(CForm12):
    # отступ | наименование | № строки | диагнозы титул | диагнозы диапазон
    MainRows = [
        (0, u'Зарегистрировано заболеваний - всего', u'1.0', u'A00-T98', u'A00-T98'),
        (1, u'в том числе:\nнекоторые инфекционные и паразитарные болезни', u'2.0', u'A00-B99', u'A00-B99'),
        (2, u'из них:\nкишечные инфекции', u'2.1', u'A00-A09', u'A00-A09'),
        (2, u'менингококковая инфекция', u'2.2', u'A39', u'A39'),
        (2, u'вирусный гепатит', u'2.3', u'B15-B19', u'B15-B19'),
        (1, u'новообразования', u'3.0', u'C00-D48', u'C00-D48'),
        (2, u'из них:\nзлокачественные новообразования', u'3.1', u'C00-C96', u'C00-C96'),
        (3, u'из них:\nзлокачественные новообразования лимфоидной, кроветворной и родственных им тканей', u'3.1.1', u'C81-C96', u'C81-C96'),
        (2, u'доброкачественные новобразования', u'3.2', u'D10-D36', u'D10-D36'),
        (1, u'болезни крови, кроветворных органов и отдельные нарушения, вовлекающие иммунный механизм', u'4.0', u'D50-D89', u'D50-D89'),
        (2, u'из них:\nанемии', u'4.1', u'D50-D64', u'D50-D64'),
        (3, u'из них:\n апластические анемии', u'4.1.1', u'D60-D61', u'D60-D61'),
        (2, u'нарушения свертываемости крови, пурпура и другие геморрагические состояния', u'4.2', u'D65-D69', u'D65-D69'),
        (3, u'из них: гемофилия', u'4.2.1', u'D66-D68', u'D66-D68'),
        (2, u'отдельные нарушения, вовлекающие иммунный механизм', u'4.3', u'D80-D89', u'D80-D89'),
        (1, u'болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'5.0', u'E00-E89', u'E00-E89'),
        (2, u'из них:\nболезни щитовидной железы', u'5.1', u'E00-E07', u'E00-E07'),
        (3, u'из них:\nсиндром врожденной йодной недостаточности', u'5.1.1', u'E00', u'E00'),
        (3, u'эндемический зоб, связанный с йодной недостаточностью', u'5.1.2', u'E01.0-2', u'E01.0-2'),
        (3, u'субклинический гипотиреоз вследствие йодной недостаточности и другие формы гипотиреоза', u'5.1.3', u'E02, E03', u'E02; E03'),
        (3, u'другие формы нетоксического зоба', u'5.1.4', u'E04', u'E04'),
        (3, u'тиреотоксикоз (гипертиреоз)', u'5.1.5', u'E05', u'E05'),
        (3, u'тиреоидит', u'5.1.6', u'E06', u'E06'),
        (2, u'сахарный диабет', u'5.2', u'E10-E14', u'E10-E14'),
        (3, u'из него:\nс поражением глаз', u'5.2.1', u'E10.3, E11.3, E12.3, E13.3, E14.3', u'E10.3; E11.3; E12.3; E13.3; E14.3'),
        (3, u'с поражением почек', u'5.2.2', u'E10.2, E11.2, E12.2, E13.2, E14.2', u'E10.2; E11.2; E12.2; E13.2; E14.2'),
        (3, u'из него (из стр. 5.2): сахарный диабет I типа', u'5.2.3', u'E10', u'E10'),
        (3, u'сахарный диабет II типа', u'5.2.4', u'E11', u'E11'),
        (2, u'гиперфункция гипофиза', u'5.3', u'E22', u'E22'),
        (2, u'гипопитуитаризм', u'5.4', u'E23.0', u'E23.0'),
        (2, u'несахарный диабет', u'5.5', u'E23.2', u'E23.2'),
        (2, u'адреногенитальные расстройства', u'5.6', u'E25', u'E25'),
        (2, u'дисфункция яичников', u'5.7', u'E28', u'E28'),
        (2, u'дисфункция яичек', u'5.8', u'E29', u'E29'),
        (2, u'ожирение', u'5.10', u'E66', u'E66'),
        (2, u'фенилкетонурия', u'5.11', u'E70.0', u'E70.0'),
        (2, u'нарушения обмена галактозы (галактоземия)', u'5.12', u'E74.2', u'E74.2'),
        (2, u'болезнь Гоше', u'5.13', u'E75.2', u'E75.2'),
        (2, u'нарушения обмена гликозамигликанов (мукополисахаридоз)', u'5.14', u'E76', u'E76'),
        (2, u'муковисцидоз', u'5.15', u'E84', u'E84'),
        (1, u'психические расстройства и расстройства поведения', u'6.0', u'F01, F03-F99', u'F01; F03-F99'),
        (2, u'из них:\nпсихические расстройства и расстройства поведения, связанные с употреблением психоактивных веществ', u'6.1', u'F10-F19', u'F10-F19'),
        (1, u'болезни нервной системы', u'7.0', u'G00-G98', u'G00-G98'),
        (2, u'из них:\nвоспалительные болезни центральной нервной системы', u'7.1', u'G00-G09', u'G00-G09'),
        (3, u'из них:\n бактериальный менингит', u'7.1.1', u'G00', u'G00'),
        (3, u'энцефалит, миелит и энцефаломиелит', u'7.1.2', u'G04', u'G04'),
        (2, u'системные атрофии, поражающие преимущественно нервную систему', u'7.2', u'G10-G12', u'G10-G12'),
        (2, u'экстрапирамидные и другие двигательные нарушения', u'7.3', u'G20, G21, G23-G25', u'G20; G21; G23-G25'),
        (3, u'из них:\nдругие экстрапирамидные и двигательные нарушения', u'7.3.2', u'G25', u'G25'),
        (2, u'другие дегенеративные болезни нервной системы', u'7.4', u'G30-G31', u'G30-G31'),
        (3, u'из них болезнь Альцгеймера', u'7.4.1', u'G30', u'G30'),
        (2, u'демиелинизирующие болезни центральной нервной системы', u'7.5', u'G35-G37', u'G35-G37'),
        (3, u'из них:\nрассеянный склероз', u'7.5.1', u'G35', u'G35'),
        (2, u'эпизодические и пароксизмальные расстройства', u'7.6', u'G40-G47', u'G40-G47'),
        (3, u'из них:\nэпилепсия, эпилептический статус', u'7.6.1', u'G40-G41', u'G40-G41'),
        (3, u'преходящие транзиторные церебральные ишемические приступы (атаки) и родственные синдромы', u'7.6.2', u'G45', u'G45'),
        (2, u'поражения отдельных нервов, нервных корешков и сплетений, полиневропатии и другие поражения периферической нервной  системы', u'7.7', u'G50-G64', u'G50-G64'),
        (3, u'из них:\nсиндром Гийена-Барре', u'7.7.1', u'G61.0', u'G61.0'),
        (2, u'болезни нервно-мышечного синапса и мышц', u'7.8', u'G70-G73', u'G70-G73'),
        (3, u'из них:\nмиастения ', u'7.8.1', u'G70.0, 2', u'G70.0, 2'),
        (3, u'мышечная дистрофия Дюшенна', u'7.8.2', u'G71.0', u'G71.0'),
        (2, u'церебральный паралич и другие паралитические синдромы', u'7.9', u'G80-G83', u'G80-G83'),
        (3, u'из них:\nцеребральный паралич', u'7.9.1', u'G80', u'G80'),
        (2, u'расстройства вегетативной(автономной) нервной системы', u'7.10', u'G90', u'G90'),
        (2, u'сосудистые миелопатии', u'7.11', u'G95.1', u'G95.1'),
        (1, u'болезни глаза и его придаточного аппарата', u'8.0', u'H00-H59', u'H00-H59'),
        (2, u'из них:\nконъюнктивит', u'8.1', u'H10', u'H10'),
        (2, u'кератит', u'8.2', u'H16', u'H16'),
        (3, u'из него:\nязва роговицы', u'8.2.1', u'H16.0', u'H16.0'),
        (2, u'катаракта', u'8.3', u'H25-H26', u'H25-H26'),
        (2, u'хориоретинальное воспаление', u'8.4', u'H30', u'H30'),
        (2, u'отслойка сетчатки с разрывом сетчатки', u'8.5', u'H33.0', u'H33.0'),
        (2, u'преретинопатия', u'8.6', u'H35.1', u'H35.1'),
        (2, u'дегенерация макулы и заднего полюса', u'8.7', u'H35.3', u'H35.3'),
        (2, u'глаукома', u'8.8', u'H40', u'H40'),
        (2, u'дегенеративная миопия', u'8.9', u'H44.2', u'H44.2'),
        (2, u'болезни зрительного нерва и зрительных путей', u'8.10', u'H46-H48', u'H46-H48'),
        (3, u'атрофия зрительного нерва', u'8.10.1', u'H47.2', u'H47.2'),
        (2, u'болезни мышц глаза, нарушения содружественного движения глаз, аккомодации и рефракции', u'8.11', u'H49-H52', u'H49-H52'),
        (3, u'из них:\nмиопия', u'8.11.1', u'H52.1', u'H52.1'),
        (3, u'астигматизм', u'8.11.2', u'H52.2', u'H52.2'),
        (2, u'слепота и пониженное зрение', u'8.12', u'H54', u'H54'),
        (3, u'из них:\nслепота обоих глаз', u'8.12.1', u'H54.0', u'H54.0'),
        (1, u'болезни уха и сосцевидного отростка', u'9.0', u'H60-H95', u'H60-H95'),
        (2, u'из них:\nболезни наружного уха', u'9.1', u'H60-H61', u'H60-H61'),
        (2, u'болезни среднего уха и сосцевидного отростка', u'9.2', u'H65-H66, H68-H74', u'H65-H66; H68-H74'),
        (3, u'из них:\n острый средний отит', u'9.2.1', u'H65.0, H65.1, H66.0', u'H65.0; H65.1; H66.0'),
        (3, u'хронический средний отит', u'9.2.2', u'H65.2-4, H66.1-3', u'H65.2-4; H66.1-3'),
        (3, u'болезни слуховой (евстахиевой) трубы', u'9.2.3', u'H68-H69', u'H68-H69'),
        (3, u'перфорация барабанной перепонки', u'9.2.4', u'H72', u'H72'),
        (3, u'другие болезни среднего уха и сосцевидного отростка', u'9.2.5', u'H74', u'H74'),
        (2, u'болезни внутреннего уха', u'9.3', u'H80-H81, H83', u'H80-H81; H83'),
        (3, u'из них:\nотосклероз', u'9.3.1', u'H80', u'H80'),
        (3, u'болезнь Меньера', u'9.3.2', u'H81.0', u'H81.0'),
        (2, u'кондуктивная и нейросенсорная потеря слуха', u'9.4', u'H90', u'H90'),
        (3, u'из них:\nкондуктивная потеря слуха двусторонняя', u'9.4.1', u'H90.0', u'H90.0'),
        (3, u'нейросенсорная потеря слуха двусторонняя', u'9.4.2', u'H90.3', u'H90.3'),
        (1, u'болезни системы кровообращения', u'10.0', u'I00-I99', u'I00-I99'),
        (2, u'из них:\nострая ревматическая лихорадка', u'10.1', u'I00-I02', u'I00-I02'),
        (2, u'хронические ревматические болезни сердца', u'10.2', u'I05-I09', u'I05-I09'),
        (3, u'из них:\nревматические поражения клапанов', u'10.2.1', u'I05-I08', u'I05-I08'),
        (2, u'болезни, характеризующиеся повышенным кровяным давлением', u'10.3', u'I10-I13', u'I10-I13'),
        (3, u'из них:\nэссенциальная гипертензия', u'10.3.1', u'I10', u'I10'),
        (3, u'гипертензивная болезнь сердца(гипертоническая болезнь с преимущественным поражением сердца)', u'10.3.2', u'I11', u'I11'),
        (3, u'гипертензивная (гипертоническая) болезнь с преимущественным  поражением  почек', u'10.3.3', u'I12', u'I12'),
        (3, u'гипертензивная (гипертоническая) болезнь с преимущественным  поражением сердца и  почек', u'10.3.4', u'I13', u'I13'),
        (2, u'ишемические болезни сердца', u'10.4', u'I20- I25', u'I20-I25'),
        (3, u'из них:\nстенокардия', u'10.4.1', u'I20', u'I20'),
        (4, u'из нее:\nнестабильная стенокардия', u'10.4.1.1', u'I20.0', u'I20.0'),
        (3, u'острый инфаркт миокарда', u'10.4.2', u'I21', u'I21'),
        (3, u'повторный инфаркт миокарда', u'10.4.3', u'I21', u'I22'),
        (3, u'другие формы острых ишемических болезней сердца', u'10.4.4', u'I24', u'I24'),
        (3, u'хроническая ишемическая болезнь сердца', u'10.4.5', u'I25', u'I25'),
        (4, u'из нее:\nпостинфарктный кардиосклероз', u'10.4.5.1', u'I25.8', u'I25.8'),
        (2, u'другие болезни сердца', u'10.5', u'I30-I51', u'I30-I51'),
        (3, u'из них:\nострый перикардит', u'10.5.1', u'I30', u'I30'),
        (3, u'из них острый и подострый эндокардит', u'10.5.2', u'I33', u'I33'),
        (3, u'острый миокардит', u'10.5.3', u'I40', u'I40'),
        (3, u'кардиомиопатия', u'10.5.4', u'I42', u'I42'),
        (2, u'цереброваскулярные болезни', u'10.6', u'I60-I69', u'I60-I69'),
        (3, u'из них:\nсубарахноидальное кровоизлияние', u'10.6.1', u'I60', u'I60'),
        (3, u'внутримозговое и другое внутричерепное кровоизлияние', u'10.6.2', u'I61, I62', u'I61; I62'),
        (3, u'инфаркт мозга', u'10.6.3', u'I63', u'I63'),
        (3, u'инсульт, не уточненный, как кровоизлияние  или инфаркт', u'10.6.4', u'I64', u'I64'),
        (3, u'закупорка и стеноз прецеребральных, церебральных артерий, не приводящие к инфаркту мозга', u'10.6.5', u'I65-I66', u'I65-I66'),
        (3, u'другие цереброваскулярные болезни', u'10.6.6', u'I67', u'I67'),
        (3, u'последствия цереброваскулярные болезни', u'10.6.7', u'I69', u'I69'),
        (2, u'эндартериит, тромбангиит облитерирующий', u'10.7', u'I70.2, I73.1', u'I70.2; I73.1'),
        (2, u'болезни вен, лимфатических сосудов и лимфатических узлов', u'10.8', u'I80 - I83, I85 - I89', u'I80 - I83; I85 - I89'),
        (3, u'из них:\nфлебит и тромбофлебит', u'10.8.1', u'I80', u'I80'),
        (3, u'тромбоз портальной вены', u'10.8.2', u'I81', u'I81'),
        (3, u'варикозное расширение вен нижних конечностей', u'10.8.3', u'I83', u'I83'),
        (1, u'болезни органов дыхания', u'11.0', u'J00-J98', u'J00-J98'),
        (2, u'из них:\nострые респираторные инфекции верхних дыхательных путей', u'11.1', u'J00-J06', u'J00-J06'),
        (3, u'из них:\nострый ларингит и трахеит', u'11.1.1', u'J04', u'J04'),
        (3, u'острый обструктивный ларингит (круп) и эпиглоттит', u'11.1.2', u'J05', u'J05'),
        (2, u'грипп', u'11.2', u'J09-J11', u'J09-J11'),
        (2, u'пневмонии', u'11.3', u'J12 - J16, J18', u'J12 - J16; J18'),
        (3, u'Из них бронхопневмония, вызванная S.Pneumoniae', u'11.3.1', u'J13', u'J13'),
        (2, u'острые респираторные инфекции нижних дыхательных путей', u'11.4', u'J20-J22', u'J20-J22'),
        (2, u'аллергический ринит (поллиноз)', u'11.5', u'J30.1', u'J30.1'),
        (2, u'хронические болезни миндалин и аденоидов, перитонзиллярный абсцесс', u'11.6', u'J35-J36', u'J35-J36'),
        (2, u'бронхит хронический и неуточненный, эмфизема', u'11.7', u'J40-J43', u'J40-J43'),
        (2, u'другая хроническая обструктивная легочная болезнь ', u'11.8', u'J44', u'J44'),
        (2, u'бронхоэктатическая болезнь', u'11.9', u'J47', u'J47'),
        (2, u'астма, астматический статус', u'11.10', u'J45-J46', u'J45-J46'),
        (2, u'другие интерстициальные легочные болезни, гнойные  и некротические болезни, состояния нижних дыхательных путей, другие болезни плевры', u'11.11', u'J84-J90, J92-J94', u'J84-J90; J92-J94'),
        (1, u'болезни органов пищеварения', u'12.0', u'K00-K92', u'K00-K92'),
        (2, u'из них:\nязва желудка и двенадцатиперстной перстной кишки', u'12.1', u'K25-K26', u'K25-K26'),
        (2, u'гастрит и дуоденит', u'12.2', u'K29', u'K29'),
        (2, u'грыжи', u'12.3', u'K40-K46', u'K40-K46'),
        (2, u'неинфекционный энтерит и колит', u'12.4', u'K50-K52', u'K50-K52'),
        (2, u'другие болезни кишечника', u'12.5', u'K55-K63', u'K55-K63'),
        (3, u'из них:\n паралитический илеус и непроходимость кишечника без грыжи', u'12.5.1', u'K56', u'K56'),
        (2, u'геморрой', u'12.6', u'K64', u'K64'),
        (2, u'болезни печени', u'12.7', u'K70-K76', u'K70-K76'),
        (3, u'из них:\nфиброз и цирроз печени', u'12.7.1', u'K74', u'K74'),
        (2, u'болезни желчного пузыря, желчевыводящих путей', u'12.8', u'K80-K83', u'K80-K83'),
        (2, u'болезни поджелудочной железы', u'12.9', u'K85-K86', u'K85-K86'),
        (3, u'из них:\nострый панкреатит', u'12.9.1', u'K85', u'K85'),
        (1, u'болезни кожи и подкожной клетчатки', u'13.0', u'L00-L98', u'L00-L98'),
        (2, u'из них:\nатопический дерматит', u'13.1', u'L20', u'L20'),
        (2, u'контактный дерматит', u'13.2', u'L23-L25', u'L23-L25'),
        (2, u'другие дерматиты (экзема)', u'13.3', u'L30', u'L30'),
        (2, u'псориаз', u'13.4', u'L40', u'L40'),
        (3, u'из него:\nпсориаз артропатический', u'13.4.1', u'L40.5', u'L40.5'),
        (3, u'дискоидная красная волчанка', u'13.5', u'L93.0', u'L93.0'),
        (3, u'локализованная склеродермия', u'13.6', u'L94.0', u'L94.0'),
        (1, u'болезни костно-мышечной системы и соединительной ткани', u'14.0', u'M00-M99', u'M00-M99'),
        (2, u'из них:\nартропатии', u'14.1', u'M00-M25', u'M00-M25'),
        (3, u'из них:\nпневмококковый артрит и полиартрит', u'14.1.1', u'M00.1', u'M00.1'),
        (3, u'реактивные артропатии', u'14.1.2', u'M02', u'M02'),
        (3, u'ревматоидный артрит (серопозитивный и серонегативный)', u'14.1.3', u'M05-M06', u'M05-M06'),
        (3, u'артрозы', u'14.1.5', u'M15-M19', u'M15-M19'),
        (2, u'системные поражения соединительной ткани', u'14.2', u'M30-M35', u'M30-M35'),
        (3, u'из них:\nсистемная красная волчанка', u'14.2.1', u'M32', u'M32'),
        (2, u'деформирующие дорсопатии', u'14.3', u'M40-M43', u'M40-M43'),
        (2, u'cпондилопатии', u'14.4', u'M45-M48', u'M45-M48'),
        (3, u'из них:\nанкилозирующий спондилит', u'14.4.1', u'M45', u'M45'),
        (2, u'поражение синовинальных оболочек и сухожилий', u'14.5', u'M65-M67', u'M65-M67'),
        (2, u'остеопатии и хондропатии', u'14.6', u'M80-M94', u'M80-M94'),
        (3, u'из них:\nостеопорозы', u'14.6.1', u'M80-M81', u'M80-M81'),
        (1, u'болезни мочеполовой системы', u'15.0', u'N00-N99', u'N00-N99'),
        (2, u'из них:\nгломерулярные, тубулоинтерстициальные болезни почек, другие болезни почки и мочеточника', u'15.1', u'N00-N07, N09-N15, N25-N28', u'N00-N07; N09-N15; N25-N28'),
        (2, u'почечная недостаточность', u'15.2', u'N17-N19', u'N17-N19'),
        (2, u'мочекаменная болезнь', u'15.3', u'N20-N21, N23', u'N20-N21; N23'),
        (2, u'другие болезни мочевой системы', u'15.4', u'N30-N32, N34-N36, N39', u'N30-N32; N34-N36; N39'),
        (2, u'болезни предстательной железы', u'15.5', u'N40-N42', u'N40-N42'),
        (2, u'доброкачественная дисплазия молочной   железы', u'15.7', u'N60', u'N60'),
        (2, u'воспалительные болезни женских тазовых органов', u'15.8', u'N70-N73, N75-N76', u'N70-N73; N75-N76'),
        (3, u'из них"\nсальпингит и оофорит', u'15.8.1', u'N70', u'N70'),
        (2, u'эндометриоз', u'15.9', u'N80', u'N80'),
        (2, u'эрозия и эктропион шейки матки', u'15.10', u'N86', u'N86'),
        (2, u'расстройства менструаций', u'15.11', u'N91-N94', u'N91-N94'),
        (1, u'беременность, роды и послеродовой период', u'16.0', u'O00-O99', u'O00-O99'),
        (1, u'врожденные аномалии (пороки развития), деформации и хромосомные нарушения', u'18.0', u'Q00-Q99', u'Q00-Q99'),
        (2, u'из них:\nврожденные аномалии нервной системы', u'18.1', u'Q00-Q07', u'Q00-Q07'),
        (2, u'врожденные аномалии глаза', u'18.2', u'Q10-Q15', u'Q10-Q15'),
        (2, u'врожденные аномалии системы кровообращения', u'18.3', u'Q20-Q28', u'Q20-Q28'),
        (22, u'врожденные аномалии женских половых органов', u'18.4', u'Q50-Q52', u'Q50-Q52'),
        (2, u'неопределенность пола и псевдогермафродитизм', u'18.5', u'Q56', u'Q56'),
        (2, u'врожденные деформации бедра', u'18.6', u'Q65', u'Q65'),
        (2, u'врожденный ихтиоз', u'18.7', u'Q80', u'Q80'),
        (2, u'нейрофиброматоз', u'18.8', u'Q85.0', u'Q85.0'),
        (2, u'синдром Дауна', u'18.9', u'Q90', u'Q90'),
        (1, u'симптомы, признаки и отклонения от нормы, выявленные при клинических и лабораторных исследованиях, не классифицированные в других рубриках', u'19.0', u'R00-R99', u'R00-R99'),
        (1, u'травмы, отравления и некоторые другие последствия воздействия внешних причин', u'20.0', u'S00-T98', u'S00-T98'),
        (2, u'из них:\nоткрытые укушенные раны (только с кодом внешней причины W54)', u'20.1', u'S01, S11, S21, S31, S41, S51, S61, S71, S81, S91', u'S01; S11; S21; S31; S41; S51; S61; S71; S81; S91'),
    ]

    def __init__(self, parent):
        CForm12.__init__(self, parent)
        self.setTitle(u'Форма N 12 5. Взрослые старше трудоспособного возраста (с 55 лет у женщин и с 60 лет у мужчин)')

    def build(self, params):
        mapMainRows = createMapCodeToRowIdx([row[4] for row in self.MainRows])
        mapCompRows = createMapCodeToRowIdx([row[4] for row in self.CompRows])
        rowSize = 8
        rowCompSize = 2
        reportMainData = [[0] * rowSize for row in xrange(len(self.MainRows))]
        reportCompData = [[0] * rowCompSize for row in xrange(len(self.CompRows))]
        clientIdList = set()
        registeredAll = 0
        registeredFirst = 0
        consistsByEnd = [0, 0, 0]
        params['ageFrom'] = 55
        params['ageTo'] = 150
        query = self.selectData(params)
        while query.next():
            record = query.record()
            sex = forceInt(record.value('sex'))
            clientId = forceRef(record.value('client_id'))
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            DN = forceBool(record.value('DN'))
            isFirstInLife = forceBool(record.value('isFirstInLife'))
            DNforEndDate = forceBool(record.value('DNforEndDate'))

            if clientId and clientId not in clientIdList:
                clientIdList.add(clientId)
                registeredAll += 1

            cols = [0]
            if DN:
                cols.append(1)
            if isFirstInLife:
                registeredFirst += 1
                cols.append(2)
                if DN:
                    cols.append(3)
            if DN and not DNforEndDate:
                cols.append(6)
            if DNforEndDate:
                consistsByEnd[0] += 1
                cols.append(7)

            rows = []
            for postfix in postfixs:
                rows.extend(mapMainRows.get((MKB, postfix), []))
                while len(MKB[:-1]) > 4:
                    MKB = MKB[:-1]
                    rows.extend(mapMainRows.get((MKB, postfix), []))

            for row in rows:
                reportLine = reportMainData[row]
                for col in cols:
                    reportLine[col] += 1

        query = self.selectDataZDiagnosis(params)
        while query.next():
            record = query.record()
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            sickCount = forceInt(record.value('sickCount'))
            isNotPrimary = forceBool(record.value('isNotPrimary'))
            for row in mapCompRows.get((MKB, ''), []):
                reportLine = reportCompData[row]
                reportLine[0] += sickCount
                if isNotPrimary:
                    reportLine[1] += sickCount

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'5. Взрослые старше трудоспособного возраста (с 55 лет у женщин и с 60 лет у мужчин)')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        splitTitle(cursor, u'(4000)', u'Код по ОКЕИ: единица - 642; человек - 792')

        tableColumns = [
            ('15%', [u'Наименование классов и отдельных болезней', u'', u'', u'1'], CReportBase.AlignLeft),
            ('5%', [u'№ строки', u'', u'', u'2'], CReportBase.AlignLeft),
            ('10%', [u'Код по МКБ-10 пересмотра', u'', u'', u'3'], CReportBase.AlignLeft),
            ('10%', [u'Зарегистрировано пациентов с данным заболеванием', u'Всего', u'', u'4'], CReportBase.AlignRight),
            ('10%', [u'', u'из них(из гр. 4):', u'взято под диспансерное наблюдение', u'8'], CReportBase.AlignRight),
            ('10%', [u'', u'', u'с впервые в жизни установленным диагнозом', u'9'], CReportBase.AlignRight),
            ('10%', [u'', u'из заболеваний с впервые в жизни установленным диагнозом (из гр. 9):', u'взято под диспансерное наблюдение', u'10'], CReportBase.AlignRight),
            ('10%', [u'', u'', u'выявлено при профосмотре', u'11'], CReportBase.AlignRight),
            ('10%', [u'', u'', u'выявлено при диспансеризации определенных групп взрослого населения', u'12'], CReportBase.AlignRight),
            ('10%', [u'Снято с диспансерного наблюдения', u'', u'', u'14'], CReportBase.AlignRight),
            ('10%', [u'Состоит под диспансерным наблюдением на конец отчетного года', u'', u'', u'15'], CReportBase.AlignRight)
        ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1)  # Наименование
        table.mergeCells(0, 1, 3, 1)  # № стр.
        table.mergeCells(0, 2, 3, 1)  # Код МКБ
        table.mergeCells(0, 3, 1, 6)  # Всего
        table.mergeCells(1, 3, 2, 1)
        table.mergeCells(1, 4, 1, 2)
        table.mergeCells(1, 6, 1, 3)
        table.mergeCells(0, 9, 3, 1)
        table.mergeCells(0, 10, 3, 1)

        t = QtGui.QTextBlockFormat()
        for row, rowDescr in enumerate(self.MainRows):
            reportLine = reportMainData[row]
            i = table.addRow()
            t.setLeftMargin(rowDescr[0] * 10)
            table.setText(i, 0, rowDescr[1], blockFormat=t)
            table.setText(i, 1, rowDescr[2])
            table.setText(i, 2, rowDescr[3])
            for col in xrange(rowSize):
                table.setText(i, 3 + col, reportLine[col])

        # 4001
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, '(4001)', u'Код по ОКЕИ: человек - 792')
        cursor.insertText(u"""Число физических лиц зарегистрированных пациентов - всего {0},
из  них  с  диагнозом, установленным впервые в жизни {1},
состоит под диспансерным  наблюдением  на  конец  отчетного года (из гр. 15, стр.  1.0) {2}""".format(registeredAll, registeredFirst, consistsByEnd[0]))

        # 3003 для психиатрии не заполняем
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, '(4003)', u'Код по ОКЕИ: человек - 792')
        cursor.insertText(u"""Из числа пациентов, состоящих на конец отчетного года под диспансерным
наблюдением (гр. 15): состоит под диспансерным наблюдением лиц с
хроническим вирусным гепатитом (B18) и циррозом печени (K74.6)
одновременно 1 _____ чел.;  с  хроническим   вирусным   гепатитом  (B18)  и
гепатоцеллюлярным раком (C22.0) одновременно 2 _____ чел.""")

        # 4100
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock()
        cursor.insertText(u'Взрослые старше трудоспособного возраста')
        cursor.insertBlock()
        cursor.insertText(u'Факторы, влияющие на состояние здоровья населения')
        cursor.insertBlock()
        cursor.insertText(u'и обращения в медицинские организации')
        cursor.insertBlock()
        cursor.insertText(u'(с профилактической и иными целями)')
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        splitTitle(cursor, '(4100)', u'Код по ОКЕИ: единица - 642')

        tableColumns = [('30%', [u'Наименование', u'', u'1'], CReportBase.AlignLeft),
            ('10%', [u'№ строки', u'', u'2'], CReportBase.AlignLeft),
            ('15%', [u'Код МКБ-10', u'', u'3'], CReportBase.AlignLeft),
            ('15%', [u'Обращения', u'всего', u'4'], CReportBase.AlignRight),
            ('15%', [u'', u'из них: повторные', u'5'], CReportBase.AlignRight), ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 2)

        t = QtGui.QTextBlockFormat()
        for row, rowDescr in enumerate(self.CompRows):
            reportLine = reportCompData[row]
            i = table.addRow()
            t.setLeftMargin(rowDescr[0] * 10)
            table.setText(i, 0, rowDescr[1], blockFormat=t)
            table.setText(i, 1, rowDescr[2])
            table.setText(i, 2, rowDescr[3])
            table.setText(i, 3, reportLine[0])
            table.setText(i, 4, reportLine[1])

        return doc