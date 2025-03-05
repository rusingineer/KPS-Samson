# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2019 SAMSON Group. All rights reserved.
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
from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils import splitTitle
from Reports.Utils import dateRangeAsStr
from library.MapCodeWithExSubClass import createMapCodeToRowIdx, normalizeMKB
from library.Utils import forceString, forceInt, forceBool

# отступ | наименование | диагнозы титул | диагнозы | № строки
MainRows = [
    (0, u'Психические расстройства - всего', u'F00 - F09, F20 - F99', u'F00-F05; F06.0-F06.2; F06.30-F06.33; F06.81; F06.910-F06.918; F09; F20; F21; F25; F30.24; F31.24; F31.54; F32.34; F33.34; F23; F24; F22; F28; F29; F80.31; F84.0-F84.4; F99.1; F30.23-F30.28; F31.23-F31.28; F31.53-F31.58; F32.33-F32.38; F33.33-F33.38; F39; F06.34-F06.39; F06.4-F06.7; F06.82; F06.920-F06.989; F06.99; F07; F30.0; F30.1; F30.8; F30.9; F31.0; F31.1; F31.30; F31.31; F31.3; F31.4; F31.6-F31.9; F32.0-F32.2; F32.8; F32.9; F33.0-F33.2; F33.4-F38.8; F40-F48; F50-F59; F80-F83; F84.5; F90-F98; F99.2-F99.9; F60-F69; F70-F79', u'1'),
    (0, u'Психозы и (или) состояния слабоумия', u'F00 - F05, F06 (часть), F09, F20 - F25, F28, F29, F84.0-4, F30 - F39 (часть)', u'F00-F05; F06.0-F06.2; F06.30-F06.33; F06.81; F06.910-F06.918; F09; F20; F21; F25; F30.24; F31.24; F31.54; F32.34; F33.34; F23; F24; F22; F28; F29; F80.31; F84.0-F84.4; F99.1; F30.23-F30.28; F31.23-F31.28; F31.53-F31.58; F32.33-F32.38; F33.33-F33.38; F39', u'2'),
    (1, u'из них: шизофрения, шизотипические расстройства, шизоаффективные психозы, аффективные психозы с неконгруентным аффекту бредом', u'F20, F21, F25, F3x.x4', u'F20; F21; F25; F30.24; F31.24; F31.54; F32.34; F33.34', u'3'),
    (1, u'детский аутизм, атипичный аутизм', u'F84.0-1', u'F84.0; F84.1', u'4'),
    (0, u'Психические расстройства непсихотического характера', u'F06 (часть), F07, F30 - F39 (часть), F40 - F69, F80 - F83, F84.5, F90 - F98', u'F06.34-F06.39; F06.4-F06.7; F06.82; F06.920-F06.989; F06.99; F07; F30.0; F30.1; F30.8; F30.9; F31.0; F31.1; F31.30; F31.31; F31.3; F31.4; F31.6-F31.9; F32.0-F32.2; F32.8; F32.9; F33.0-F33.2; F33.4-F38.8; F40-F48; F50-F59; F80-F83; F84.5; F90-F98; F99.2-F99.9; F60-F69', u'5'),
    (1, u'из них синдром Аспергера', u'F84.5', u'F84.5', u'6'),
    (0, u'Умственная отсталость', u'F70 - F79', u'F70-F79', u'7')
    ]

# отступ | наименование | диагнозы титул | диагнозы | № строки
MainRows2180 = [
    (0, u'Психические расстройства - всего', u'F00 - F09, F20 - F99', u'F00 - F09; F20 - F99', u'1'),
    (1, u'из них: шизофрения, шизотипические расстройства, шизоаффективные психозы, аффективные психозы с неконгруентным аффекту бредом', u'F20, F21, F25, F3x.x4', u'F20; F21; F25; F3x.x4', u'2'),
    (0, u'хронические неорганические психозы, детские психозы', u'F22, F28, F29, F84.0-4', u'F22; F28; F29; F84.0-F84.4', u'3'),
    (1, u'из них: детский аутизм, атипичный аутизм', u'F84.0-1', u'F84.0-F84.4', u'4'),
    (0, u'психические расстройства вследствие эпилепсии', u'F04.2, F0x.x2, F0x.xx2', u'F04.2; F0x.x2; F0x.xx2', u'5'),
    (0, u'умственная отсталость', u'F70 - F79', u'F70 - F79', u'6'),
    (0, u'Кроме того, пациенты, имеющие инвалидность по общесоматическим заболеваниям', u'', u'', u'7')
]

def selectGetObserved(params):
    db = QtGui.qApp.db
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
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
    if orgStructureIdList:
        condOrgstruct = 'AND ' + db.table('Person').alias('p')['orgStructure_id'].inlist(orgStructureIdList)
    else:
        condOrgstruct = ''

    typeDN = params.get('typeDN', -1)
    typeContingent = params.get('typeContingent', u'Д-наблюдение')

    if typeDN:
        stmt = u"""SELECT 
  IF(cck.exSubclassMKB IS NOT NULL, CONCAT(cck.MKB, cck.exSubclassMKB), cck.MKB) AS MKB,
  age(c.birthDate, cck.begDate) AS age,
  IF(c.begDate BETWEEN {begDate} AND {endDate}, 1, 0) isFirstInLife
FROM Client c
LEFT JOIN ClientContingentKind cck ON cck.client_id = c.id
LEFT JOIN rbContingentKind ck ON cck.contingentKind_id = ck.id
WHERE c.deleted = 0
AND cck.deleted = 0
AND ck.code = '{typeContingent}'
AND cck.begDate BETWEEN {begDate} AND {endDate}
AND cck.MKB LIKE 'F%' AND cck.MKB NOT LIKE 'F1%';""".format(begDate=db.formatDate(begDateTime),
                                                            endDate=db.formatDate(endDateTime),
                                                            typeContingent=typeContingent
                                                            )
    else:
        stmt = u"""SELECT 
  IF(d.exSubclassMKB IS NOT NULL, CONCAT(d.MKB, d.exSubclassMKB), d.MKB) AS MKB,
  IF(rbDiseaseCharacter.code IN ('1', '2'), 1, 0) AS isFirstInLife,
  age(c.birthDate, D1.endDate) AS age
  FROM Diagnostic AS D1
  LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
  LEFT JOIN Diagnosis d ON d.id = D1.diagnosis_id
  LEFT JOIN rbDiagnosisType ON rbDiagnosisType.id = D1.diagnosisType_id
  LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = D1.character_id
  left JOIN Event e on e.id = D1.event_id
  left JOIN EventType et ON e.eventType_id = et.id
  LEFT JOIN rbMedicalAidType mat ON mat.id = et.medicalAidType_id
  left JOIN rbEventTypePurpose etp ON et.purpose_id = etp.id
  left JOIN Client c on c.id  = e.client_id
  LEFT JOIN Person p ON p.id = e.execPerson_id
  WHERE  D1.deleted = 0
    AND d.deleted = 0
    AND e.deleted = 0
    AND c.deleted = 0
    AND et.code NOT IN ('hospDir','egpuDisp','plng', 'anonim')
    AND et.context NOT LIKE '%relatedAction%' AND et.context NOT LIKE '%inspection%'
    AND et.form NOT IN ('000', '027', '106', '110')
    AND etp.code <> 0
    AND mat.code NOT IN ('1', '2', '3', '7')
    AND rbDispanser.code IN ('2', '6')
    AND D1.endDate BETWEEN {begDate} AND {endDate}
    AND d.MKB LIKE 'F%' AND d.MKB NOT LIKE 'F1%'
    AND mod_id is NULL
    AND rbDiagnosisType.code = '1'
    {condOrgstruct};
        """.format(begDate=db.formatDate(begDateTime),
                endDate=db.formatDate(endDateTime),
                condOrgstruct=condOrgstruct)

    return db.query(stmt)

def selectGetRemovingObserved(params):
    db = QtGui.qApp.db
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
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
    if orgStructureIdList:
        condOrgstruct = 'AND ' + db.table('Person').alias('p')['orgStructure_id'].inlist(orgStructureIdList)
    else:
        condOrgstruct = ''

    typeDN = params.get('typeDN', -1)
    typeContingent = params.get('typeContingent', u'Д-наблюдение')

    if typeDN:
        stmt = u"""SELECT 
  IF(cck.exSubclassMKB IS NOT NULL, CONCAT(cck.MKB, cck.exSubclassMKB), cck.MKB) AS MKB,
  IF(cck.contingentKindRemoval_id = 1, 1, 0) removedToRecover
FROM Client c
LEFT JOIN ClientContingentKind cck ON cck.client_id = c.id
LEFT JOIN rbContingentKind ck ON cck.contingentKind_id = ck.id
WHERE c.deleted = 0
AND cck.deleted = 0
AND ck.code = '{typeContingent}'
AND cck.endDate BETWEEN {begDate} AND {endDate}
AND cck.MKB LIKE 'F%' AND cck.MKB NOT LIKE 'F1%';""".format(begDate=db.formatDate(begDateTime),
                                                            endDate=db.formatDate(endDateTime),
                                                            typeContingent=typeContingent
                )
    else:
        stmt = u"""SELECT 
  IF(d.exSubclassMKB IS NOT NULL, CONCAT(d.MKB, d.exSubclassMKB), d.MKB) AS MKB,
  IF(rbDispanser.code = '4', 1, 0) AS removedToRecover
  FROM Diagnostic AS D1
  LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
  LEFT JOIN Diagnosis d ON d.id = D1.diagnosis_id
  LEFT JOIN rbDiagnosisType ON rbDiagnosisType.id = D1.diagnosisType_id
  left JOIN Event e on e.id = D1.event_id
  left JOIN EventType et ON e.eventType_id = et.id
  LEFT JOIN rbMedicalAidType mat ON mat.id = et.medicalAidType_id
  left JOIN rbEventTypePurpose etp ON et.purpose_id = etp.id
  left JOIN Client c on c.id  = e.client_id
  LEFT JOIN Person p ON p.id = e.execPerson_id
  WHERE  D1.deleted = 0
    AND d.deleted = 0
    AND e.deleted = 0
    AND c.deleted = 0
    AND et.code NOT IN ('hospDir','egpuDisp','plng', 'anonim')
    AND et.context NOT LIKE '%relatedAction%' AND et.context NOT LIKE '%inspection%'
    AND et.form NOT IN ('000', '027', '106', '110')
    AND etp.code <> 0
    AND mat.code NOT IN ('1', '2', '3', '7')
    AND rbDispanser.code IN ('3', '4', '5')
    AND D1.endDate between {begDate} AND {endDate}
    AND d.MKB LIKE 'F%' AND d.MKB NOT LIKE 'F1%'
    AND rbDiagnosisType.code = '1'
    {condOrgstruct};
        """.format(begDate=db.formatDate(begDateTime),
                endDate=db.formatDate(endDateTime),
                condOrgstruct=condOrgstruct)

    return db.query(stmt)

def selectObserved(params):
    db = QtGui.qApp.db
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
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
    if orgStructureIdList:
        condOrgstruct = 'AND ' + db.table('Person').alias('p')['orgStructure_id'].inlist(orgStructureIdList)
    else:
        condOrgstruct = ''

    typeDN = params.get('typeDN', -1)
    typeContingent = params.get('typeContingent', u'Д-наблюдение')
    typeContingent2 = u'ПДЛР' if typeContingent == u'Д-наблюдение' else u'Д-наблюдение'
    if typeDN:
        stmt = u"""SELECT 
  IF(cck.exSubclassMKB IS NOT NULL, CONCAT(cck.MKB, cck.exSubclassMKB), cck.MKB) AS MKB,
  age(c.birthDate, {endDate}) AS age,
  EXISTS (SELECT NULL FROM ClientContingentKind cck2
          left JOIN rbContingentKind ck2 ON cck2.contingentKind_id = ck2.id
          WHERE cck2.client_id = c.id AND ck2.code = '{typeContingent2}' AND cck2.deleted = 0
            AND cck2.endDate between {begDate} AND {endDate} 
            AND cck2.contingentKindRemoval_id in (1,5)
         ) AS transferFromPDLR, c.sex as sex
FROM Client c
LEFT JOIN ClientContingentKind cck ON cck.client_id = c.id
LEFT JOIN rbContingentKind ck ON cck.contingentKind_id = ck.id
WHERE c.deleted = 0
AND cck.deleted = 0
AND ck.code = '{typeContingent}'
AND IFNULL(cck.endDate, {endDate}) >= {endDate}
AND cck.MKB LIKE 'F%' AND cck.MKB NOT LIKE 'F1%';""".format(begDate=db.formatDate(begDateTime),
                                                            endDate=db.formatDate(endDateTime),
                                                            typeContingent=typeContingent,
                                                            typeContingent2=typeContingent2
                )
    else:
        stmt = u"""SELECT
   IF(Diagnosis.exSubclassMKB IS NOT NULL, CONCAT(Diagnosis.MKB,Diagnosis.exSubclassMKB), Diagnosis.MKB) AS MKB,
   age(Client.birthDate, {endDate}) AS age, Client.sex as sex,
   IF((SELECT MAX(rbDispanser.observed)
    FROM
    Diagnostic AS D1
    LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
    WHERE
      D1.diagnosis_id = Diagnosis.id
      AND D1.endDate = (
        SELECT MAX(D2.endDate)
        FROM Diagnostic AS D2
          left JOIN Event e on e.id = D2.event_id
          left JOIN EventType et ON e.eventType_id = et.id
          LEFT JOIN rbMedicalAidType mat ON mat.id = et.medicalAidType_id
          left JOIN rbEventTypePurpose etp ON et.purpose_id = etp.id
          LEFT JOIN Person p ON p.id = e.execPerson_id
        WHERE D2.diagnosis_id = Diagnosis.id
          AND et.code NOT IN ('hospDir','egpuDisp','plng', 'anonim')
          AND et.context NOT LIKE '%relatedAction%' AND et.context NOT LIKE '%inspection%'
          AND et.form NOT IN ('000', '027', '106', '110')
          AND etp.code <> 0
          AND mat.code NOT IN ('1', '2', '3', '7')
          AND e.deleted = 0
          AND D2.dispanser_id IS NOT NULL
          AND D2.endDate < {endDate}
          {condOrgstruct}))
          = 1, 1, 0) AS observed,
     EXISTS (SELECT NULL FROM ClientContingentKind cck
          left JOIN rbContingentKind ck ON cck.contingentKind_id = ck.id
          WHERE cck.client_id = Client.id AND ck.code = 'ПДЛР' AND cck.deleted = 0
          AND cck.endDate between {begDate} AND {endDate}
          AND cck.contingentKindRemoval_id = 5
         ) AS transferFromPDLR
FROM Diagnosis
LEFT JOIN Client ON Client.id = Diagnosis.client_id
LEFT JOIN rbDiagnosisType    ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
WHERE (Diagnosis.`deleted`=0) AND (Diagnosis.`mod_id` IS NULL) 
AND Diagnosis.MKB LIKE 'F%' AND Diagnosis.MKB NOT LIKE 'F1%'
AND rbDiagnosisType.code = '2'
HAVING observed = 1;""".format(begDate=db.formatDate(begDateTime),
                endDate=db.formatDate(endDateTime),
                condOrgstruct=condOrgstruct)

    return db.query(stmt)


def selectObservedInvalids(params):
    db = QtGui.qApp.db
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
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
    if orgStructureIdList:
        condOrgstruct = 'AND ' + db.table('Person').alias('p')['orgStructure_id'].inlist(orgStructureIdList)
    else:
        condOrgstruct = ''

    typeDN = params.get('typeDN', -1)

    if typeDN:
        stmt = u"""SELECT 
  IF(cck.exSubclassMKB IS NOT NULL, CONCAT(cck.MKB, cck.exSubclassMKB), cck.MKB) AS MKB,
  css.note AS invCategory,  age(c.birthDate, {endDate}) AS age,
  IF((SELECT COUNT(DISTINCT ClientSocStatus.id) FROM ClientSocStatus
  LEFT JOIN rbSocStatusType sstold ON sstold.id = ClientSocStatus.socStatusType_id
  WHERE ClientSocStatus.client_id=css.client_id AND ClientSocStatus.begDate BETWEEN {begDate} AND {endDate} AND code IN ('081', '082', '083', '084') AND note IN ('1с', '2с', '3с', '4с') )=1, 1, 0) AS isFirstDisability, c.sex as sex
FROM ClientSocStatus css
left JOIN rbSocStatusClass ssc ON ssc.id = css.socStatusClass_id
left JOIN rbSocStatusClass ssc2 ON ssc2.id = ssc.group_id
left JOIN rbSocStatusType sst ON sst.id = css.socStatusType_id
left JOIN Client c on c.id = css.client_id
LEFT JOIN ClientContingentKind cck ON cck.client_id = c.id
LEFT JOIN rbContingentKind ck ON cck.contingentKind_id = ck.id
WHERE css.deleted = 0 AND c.deleted = 0 AND sst.code in ('081', '082', '083', '084', '085')
AND css.note in ('1с', '2с', '3с', '4с', '1о', '2о', '3о', '4о', NULL, '')
AND ssc2.code = '1' AND ssc.code = '1'
AND c.deleted = 0
AND cck.deleted = 0 -- and c.id = 336341
AND ck.code in ('Д-наблюдение', 'ПДЛР')
AND IFNULL(cck.endDate, {endDate}) >= {endDate}
AND css.id = (SELECT MAX(id) FROM ClientSocStatus WHERE ClientSocStatus.client_id = c.id AND ClientSocStatus.note in ('1с', '2с', '3с', '4с') AND ClientSocStatus.deleted = 0 )
AND cck.MKB LIKE 'F%' AND cck.MKB NOT LIKE 'F1%';""".format(begDate=db.formatDate(begDateTime),
                                                            endDate=db.formatDate(endDateTime)
                )
    else:
        stmt = u"""SELECT
   IF(Diagnosis.exSubclassMKB IS NOT NULL, CONCAT(Diagnosis.MKB,Diagnosis.exSubclassMKB), Diagnosis.MKB) AS MKB,
   age(Client.birthDate, {endDate}) AS age, Client.sex as sex,
   IF((SELECT MAX(rbDispanser.observed)
    FROM
    Diagnostic AS D1
    LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
    WHERE
      D1.diagnosis_id = Diagnosis.id
      AND D1.endDate = (
        SELECT MAX(D2.endDate)
        FROM Diagnostic AS D2
          left JOIN Event e on e.id = D2.event_id
          left JOIN EventType et ON e.eventType_id = et.id
          LEFT JOIN rbMedicalAidType mat ON mat.id = et.medicalAidType_id
          left JOIN rbEventTypePurpose etp ON et.purpose_id = etp.id
          LEFT JOIN Person p ON p.id = e.execPerson_id
        WHERE D2.diagnosis_id = Diagnosis.id
          AND et.code NOT IN ('hospDir','egpuDisp','plng', 'anonim')
          AND et.context NOT LIKE '%relatedAction%' AND et.context NOT LIKE '%inspection%'
          AND et.form NOT IN ('000', '027', '106', '110')
          AND etp.code <> 0
          AND mat.code NOT IN ('1', '2', '3', '7')
          AND e.deleted = 0
          AND D2.dispanser_id IS NOT NULL
          AND D2.endDate < {endDate}
          {condOrgstruct}))
          = 1, 1, 0) AS observed,
     EXISTS (SELECT NULL FROM ClientContingentKind cck
          left JOIN rbContingentKind ck ON cck.contingentKind_id = ck.id
          WHERE cck.client_id = Client.id AND ck.code = 'ПДЛР' AND cck.deleted = 0
          AND cck.endDate between {begDate} AND {endDate}
          AND cck.contingentKindRemoval_id = 5
         ) AS transferFromPDLR
FROM Diagnosis
LEFT JOIN Client ON Client.id = Diagnosis.client_id
LEFT JOIN rbDiagnosisType    ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
WHERE (Diagnosis.`deleted`=0) AND (Diagnosis.`mod_id` IS NULL) 
AND Diagnosis.MKB LIKE 'F%' AND Diagnosis.MKB NOT LIKE 'F1%'
AND rbDiagnosisType.code = '2'
HAVING observed = 1;""".format(begDate=db.formatDate(begDateTime),
                endDate=db.formatDate(endDateTime),
                condOrgstruct=condOrgstruct)

    return db.query(stmt)


class CForm36(CReport):

    def __init__(self, parent):
        CReport.__init__(self, parent)


    def getSetupDialog(self, parent):
        result = CForm11SetupDialog(parent)
        result.setAddressTypeVisible(False)
        result.setTypeDNVisible(True)
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
                begTime = begTime if begTime else endTime
                description.append(u'Текущий день: ' + forceString(QDateTime(endDate, endTime)))
            else:
                begTime = begTime if begTime else endTime
                begDateTime = QDateTime(begDate, begTime)
                if begDateTime.date() or endDateTime.date():
                    description.append(dateRangeAsStr(u'за период', begDateTime, endDateTime))

        orgStructureId = params.get('orgStructureId', None)
        addressType = params.get('addressType', -1)

        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')

        if addressType >= 0:
            description.append(u'адрес: ' + (u'по проживанию' if addressType else u'по регистрации'))

        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [('100%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

class CForm36_2100_2190(CForm36):
    def __init__(self, parent):
        CForm36.__init__(self, parent)
        self.setTitle(u'Форма №36 2100-2190')


    def build(self, params):
        mapMainRows = createMapCodeToRowIdx([row[3] for row in MainRows])
        rowSize = 10
        reportMainData = [[0] * rowSize for row in xrange(len(MainRows))]
        query = selectGetObserved(params)
        while query.next():
            record = query.record()
            clientAge = forceInt(record.value('age'))
            clientSex = forceInt(record.value('sex'))
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            isFirstInLife = forceBool(record.value('isFirstInLife'))
            cols = [0]
            if isFirstInLife:
                cols.append(1)
                if clientAge >= 0 and clientAge < 15:
                    cols.append(2)
                elif clientAge >= 15 and clientAge < 18:
                    cols.append(3)

            rows = []
            for postfix in postfixs:
                rows.extend(mapMainRows.get((MKB, postfix), []))
                while len(MKB[:-1]) > 4:
                    MKB = MKB[:-1]
                    rows.extend(mapMainRows.get((MKB, postfix), []))
            rows = set(rows)
            for row in rows:
                reportLine = reportMainData[row]
                for col in cols:
                    reportLine[col] += 1
        query = selectGetRemovingObserved(params)
        while query.next():
            record = query.record()
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            removedToRecover = forceBool(record.value('removedToRecover'))
            cols = [4]
            if removedToRecover:
                cols.append(5)

            rows = []
            for postfix in postfixs:
                rows.extend(mapMainRows.get((MKB, postfix), []))
                while len(MKB[:-1]) > 4:
                    MKB = MKB[:-1]
                    rows.extend(mapMainRows.get((MKB, postfix), []))
            rows = set(rows)
            for row in rows:
                reportLine = reportMainData[row]
                for col in cols:
                    reportLine[col] += 1
        itog2100 = 0
        query = selectObserved(params)
        while query.next():
            record = query.record()
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            clientAge = forceInt(record.value('age'))
            clientSex = forceInt(record.value('sex'))
            transferFromPDLR = forceBool(record.value('transferFromPDLR'))
            cols = [6]
            if clientAge >= 0 and clientAge < 15:
                cols.append(7)
            elif clientAge >= 15 and clientAge < 18:
                cols.append(8)
            if transferFromPDLR:
                cols.append(9)

            rows = []
            for postfix in postfixs:
                rows.extend(mapMainRows.get((MKB, postfix), []))
                while len(MKB[:-1]) > 4:
                    MKB = MKB[:-1]
                    rows.extend(mapMainRows.get((MKB, postfix), []))
            rows = set(rows)
            for row in rows:
                reportLine = reportMainData[row]
                for col in cols:
                    reportLine[col] += 1
            if rows and 0 in rows:
                if clientSex == 1 and clientAge >= 18 and clientAge <= 65:
                    itog2100 += 1
                if clientSex == 2 and clientAge >= 18 and clientAge <= 60:
                    itog2100 += 1
        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Контингенты пациентов, находящихся под диспансерным наблюдением')
        splitTitle(cursor, u'(2100)', u'Код по ОКЕИ: человек - 792')

        tableColumns = [
            ('28%', [u'Наименование', u'', u'', u'1'], CReportBase.AlignLeft),
            ('5%', [u'Код по МКБ-10 (класс V, адаптированный для использования в РФ)', u'', u'', u'2'], CReportBase.AlignCenter),
            ('5%', [u'№ строки', u'', u'', u'3'], CReportBase.AlignCenter),
            ('6%', [u'Взято под наблюдение в отчетном году', u'', u'', u'4'], CReportBase.AlignRight),
            ('6%', [u'из них с впервые в жизни установленным диагнозом', u'всего', u'', u'5'], CReportBase.AlignRight),
            ('6%', [u'', u'из них детей:', u'до 14 лет включительно', u'6'], CReportBase.AlignRight),
            ('6%', [u'', u'', u'15-17 лет', u'7'], CReportBase.AlignRight),
            ('6%', [u'Снято с наблюдения в отчетном году', u'всего', u'', u'8'], CReportBase.AlignRight),
            ('6%', [u'', u'из них в связи с выздоровлением или стойким улучшением', u'', u'9'], CReportBase.AlignRight),
            ('6%', [u'Состоит под наблюдением пациентов на конец отчетного года', u'всего', u'', u'10'], CReportBase.AlignRight),
            ('6%', [u'', u'из них детей:', u'до 14 лет включительно', u'11'], CReportBase.AlignRight),
            ('7%', [u'', u'', u'15-17 лет', u'12'], CReportBase.AlignRight),
            ('7%', [u'Из числа пациентов, показанных в гр. 10, переведено в течение года из группы пациентов, получавших консультативно-лечебную помощь', u'', u'', u'13'], CReportBase.AlignRight)
        ]

        table = createTable(cursor, tableColumns)

        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 3, 1)
        table.mergeCells(0, 2, 3, 1)
        table.mergeCells(0, 3, 3, 1)
        table.mergeCells(0, 4, 1, 3)
        table.mergeCells(1, 4, 2, 1)
        table.mergeCells(1, 5, 1, 2)
        table.mergeCells(0, 7, 1, 2)
        table.mergeCells(1, 7, 2, 1)
        table.mergeCells(1, 8, 2, 1)
        table.mergeCells(0, 9, 1, 3)
        table.mergeCells(1, 9, 2, 1)
        table.mergeCells(1, 10, 1, 2)
        table.mergeCells(0, 12, 3, 1)

        t = QtGui.QTextBlockFormat()
        for row, rowDescr in enumerate(MainRows):
            reportLine = reportMainData[row]
            i = table.addRow()
            t.setLeftMargin(rowDescr[0] * 10)
            table.setText(i, 0, rowDescr[1], blockFormat=t)
            table.setText(i, 1, rowDescr[2])
            table.setText(i, 2, rowDescr[4])
            for col in xrange(rowSize):
                table.setText(i, 3 + col, reportLine[col])

        # 2101
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, u'Код по ОКЕИ: человек - 792', u'')
        cursor.insertText(u'(2101) Число   пациентов, больных психическими расстройствами,\nклассифицированными в других рубриках МКБ-10, выявленных в отчетном году\n1 ________.')

        # 2110
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Контингенты пациентов, получающих консультативно-лечебную помощь')
        splitTitle(cursor, u'(2110)', u'Код по ОКЕИ: человек - 792')
        tableColumns = [
            ('28%', [u'Наименование', u'', u'', u'1'], CReportBase.AlignLeft),
            ('5%', [u'Код по МКБ-10 (класс V, адаптированный для использования в РФ)', u'', u'', u'2'], CReportBase.AlignCenter),
            ('5%', [u'№ строки', u'', u'', u'3'], CReportBase.AlignCenter),
            ('6%', [u'Обратились впервые в течение года за консультативно-лечебной помощью', u'', u'', u'4'], CReportBase.AlignRight),
            ('6%', [u'из них с впервые в жизни установленным диагнозом', u'всего', u'', u'5'], CReportBase.AlignRight),
            ('6%', [u'', u'из них детей:', u'до 14 лет включительно', u'6'], CReportBase.AlignRight),
            ('6%', [u'', u'', u'15-17 лет', u'7'], CReportBase.AlignRight),
            ('6%', [u'Прекратили обращаться за консультативно-лечебной помощью', u'', u'', u'8'], CReportBase.AlignRight),
            ('6%', [u'из них в связи с выздоровлением или стойким улучшением', u'', u'', u'9'], CReportBase.AlignRight),
            ('6%', [u'Пациенты, которым продолжает оказываться консультативно-лечебная помощь', u'всего', u'', u'10'], CReportBase.AlignRight),
            ('6%', [u'', u'из них детей:', u'до 14 лет включительно', u'11'], CReportBase.AlignRight),
            ('7%', [u'', u'', u'15-17 лет', u'12'], CReportBase.AlignRight),
            ('7%', [u'Из числа пациентов, показанных в гр. 10, переведено в течение года из группы пациентов, находившихся под диспансерным наблюдением', u'', u'', u'13'], CReportBase.AlignRight)
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 3, 1)
        table.mergeCells(0, 2, 3, 1)
        table.mergeCells(0, 3, 3, 1)
        table.mergeCells(0, 4, 1, 3)
        table.mergeCells(1, 4, 2, 1)
        table.mergeCells(1, 5, 1, 2)
        table.mergeCells(0, 7, 3, 1)
        table.mergeCells(0, 8, 3, 1)
        table.mergeCells(0, 9, 1, 3)
        table.mergeCells(1, 9, 2, 1)
        table.mergeCells(1, 10, 1, 2)
        table.mergeCells(0, 12, 3, 1)

        reportMainData = [[0] * rowSize for row in xrange(len(MainRows))]
        params['typeContingent'] = u'ПДЛР'
        query = selectGetObserved(params)
        while query.next():
            record = query.record()
            clientAge = forceInt(record.value('age'))
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            isFirstInLife = forceBool(record.value('isFirstInLife'))
            cols = [0]
            if isFirstInLife:
                cols.append(1)
                if clientAge >= 0 and clientAge < 15:
                    cols.append(2)
                elif clientAge >= 15 and clientAge < 18:
                    cols.append(3)

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

        query = selectGetRemovingObserved(params)
        while query.next():
            record = query.record()
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            removedToRecover = forceBool(record.value('removedToRecover'))
            cols = [4]
            if removedToRecover:
                cols.append(5)

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
        itog2110 = 0
        query = selectObserved(params)
        while query.next():
            record = query.record()
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            clientAge = forceInt(record.value('age'))
            clientSex = forceInt(record.value('sex'))
            transferFromPDLR = forceBool(record.value('transferFromPDLR'))
            cols = [6]
            if clientAge >= 0 and clientAge < 15:
                cols.append(7)
            elif clientAge >= 15 and clientAge < 18:
                cols.append(8)
            if transferFromPDLR:
                cols.append(9)

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
            if rows and 0 in rows:
                if clientSex == 1 and clientAge >= 18 and clientAge <= 65:
                    itog2110 += 1
                if clientSex == 2 and clientAge >= 18 and clientAge <= 60:
                    itog2110 += 1

        t = QtGui.QTextBlockFormat()
        for row, rowDescr in enumerate(MainRows):
            reportLine = reportMainData[row]
            i = table.addRow()
            t.setLeftMargin(rowDescr[0] * 10)
            table.setText(i, 0, rowDescr[1], blockFormat=t)
            table.setText(i, 1, rowDescr[2])
            table.setText(i, 2, rowDescr[4])
            for col in xrange(rowSize):
                table.setText(i, 3 + col, reportLine[col])

        # 2120
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, u'(2120)', u'Код по ОКЕИ: человек - 792')
        tableColumns = [
            ('28%', [u'Из числа пациентов, находившихся под диспансерным наблюдением и получавших консультативно-лечебную помощь на конец года (стр. 1 гр. 10 т. 2100 и 2110):', u'получили курс лечения/реабилитации бригадным методом', u'', u'1'], CReportBase.AlignCenter),
            ('12%', [u'', u'лиц трудоспособного возраста', u'', u'2'], CReportBase.AlignCenter),
            ('12%', [u'', u'работающих', u'всего', u'3'], CReportBase.AlignCenter),
            ('12%', [u'', u'', u'из них в трудоспособном возрасте (из гр. 3)', u'4'], CReportBase.AlignCenter),
            ('12%', [u'', u'находится под опекой', u'', u'5'], CReportBase.AlignCenter),
            ('12%', [u'Из числа снятых с диспансерного наблюдения (стр. 1, гр. 8, т. 2100):', u'умерло', u'', u'6'], CReportBase.AlignCenter),
            ('12%', [u'', u'из них непосредственно от психических заболеваний (коды F00 - F09, F20 - F99)', u'', u'7'], CReportBase.AlignCenter)
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 1, 5)
        table.mergeCells(1, 0, 2, 1)
        table.mergeCells(1, 1, 2, 1)
        table.mergeCells(1, 2, 1, 2)
        table.mergeCells(1, 4, 2, 1)
        table.mergeCells(0, 5, 1, 2)
        table.mergeCells(1, 5, 2, 1)
        table.mergeCells(1, 6, 2, 1)
        i = table.addRow()
        rowSize = 7
        for col in xrange(rowSize):
            if col == 1:
                table.setText(i, col, itog2100 + itog2110)
            else:
                table.setText(i, col, 0)

        # 2150
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, u'(2150)', u'Коды по ОКЕИ: единица - 642, человек - 792')
        tableColumns = [
            ('28%', [u'Из числа пациентов, находившихся под диспансерным наблюдением и получавших консультативно-лечебную помощь (стр. 1 гр. 8, 10 т. 2100 и 2110) в течение года, совершили суицидальные попытки:', u'диспансерные пациенты', u'всего', u'1'], CReportBase.AlignCenter),
            ('12%', [u'', u'', u'из них завершенные', u'2'], CReportBase.AlignCenter),
            ('12%', [u'', u'пациенты, получавшие консультативно-лечебную помощь', u'всего', u'3'], CReportBase.AlignCenter),
            ('12%', [u'', u'', u'из них завершенные', u'4'], CReportBase.AlignCenter),
            ('12%', [u'Число случаев и дней нетрудоспособности у пациентов, больных психическими расстройствами, по закрытым листкам нетрудоспособности:', u'число случаев', u'', u'5'], CReportBase.AlignCenter),
            ('12%', [u'', u'число дней', u'', u'6'], CReportBase.AlignCenter),
            ('12%', [u'', u'из них у пациентов с заболеваниями, связанными с употреблением ПАВ', u'число случаев (из графы 5)', u'7'], CReportBase.AlignCenter),
            ('12%', [u'', u'', u'число дней (из графы 6)', u'8'], CReportBase.AlignCenter)
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 1, 4)
        table.mergeCells(1, 0, 1, 2)
        table.mergeCells(1, 2, 1, 2)
        table.mergeCells(0, 4, 1, 4)
        table.mergeCells(1, 4, 2, 1)
        table.mergeCells(1, 5, 2, 1)
        table.mergeCells(1, 6, 1, 2)
        i = table.addRow()
        rowSize = 8
        for col in xrange(rowSize):
            table.setText(i, col, 0)

        # 2160
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, u'(2160)', u'Код по ОКЕИ: человек - 792', '70%')
        tableColumns = [
            ('28%', [u'Число пациентов, содержавшихся в психоневрологических учреждениях социального обслуживания (кроме пациентов, показанных в табл. 2100 и 2110) на конец года:', u'всего', u'', u'1'], CReportBase.AlignCenter),
            ('10%', [u'', u'из них детей 0 - 17 лет включительно', u'', u'2'], CReportBase.AlignCenter),
            ('10%', [u'Число лиц, недобровольно освидетельствованных диспансером (диспансерным отделением, кабинетом)', u'всего', u'', u'3'], CReportBase.AlignCenter),
            ('10%', [u'', u'из них признано страдающими психическими расстройствами', u'', u'4'], CReportBase.AlignCenter),
            ('10%', [u'', u'из них на момент обследования нуждаются в стационарном лечении', u'', u'5'], CReportBase.AlignCenter)
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 1, 2)
        table.mergeCells(1, 0, 2, 1)
        table.mergeCells(1, 1, 2, 1)
        table.mergeCells(0, 2, 1, 3)
        table.mergeCells(1, 2, 2, 1)
        table.mergeCells(1, 3, 2, 1)
        table.mergeCells(1, 4, 2, 1)
        i = table.addRow()
        rowSize = 5
        for col in xrange(rowSize):
            table.setText(i, col, 0)

        # 2180
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Контингенты пациентов, имеющих группу инвалидности')
        splitTitle(cursor, u'(2180)', u'Код по ОКЕИ: человек - 792')
        tableColumns = [
            ('28%', [u'Наименование', u'', u'', u'1'], CReportBase.AlignCenter),
            ('10%', [u'Код по МКБ-10 (класс V, адаптированный для использования в РФ)', u'', u'', u'2'], CReportBase.AlignCenter),
            ('10%', [u'N строки', u'', u'', u'3'], CReportBase.AlignCenter),
            ('10%', [u'Число пациентов, впервые признанных инвалидами в отчетном году', u'всего', u'', u'4'], CReportBase.AlignCenter),
            ('10%', [u'', u'из них', u'инвалидами III группы', u'5'], CReportBase.AlignCenter),
            ('10%', [u'', u'', u'инвалидов (до 17 лет включительно)', u'6'], CReportBase.AlignCenter),
            ('10%', [u'Число пациентов, имевших группу инвалидности на конец отчетного года', u'всего', u'', u'7'], CReportBase.AlignCenter),
            ('10%', [u'', u'из них', u'имевших III группу', u'8'], CReportBase.AlignCenter),
            ('10%', [u'', u'', u'инвалидов (до 17 лет включительно)', u'9'], CReportBase.AlignCenter)
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 3, 1)
        table.mergeCells(0, 2, 3, 1)
        table.mergeCells(0, 3, 1, 3)
        table.mergeCells(1, 3, 2, 1)
        table.mergeCells(1, 4, 1, 2)
        table.mergeCells(0, 6, 1, 3)
        table.mergeCells(1, 6, 2, 1)
        table.mergeCells(1, 7, 1, 2)
        rowSize = 6
        reportMainData = [[0] * rowSize for row in xrange(len(MainRows2180))]
        mapMainRows2180 = createMapCodeToRowIdx([row[3] for row in MainRows2180])
        query = selectObservedInvalids(params)
        itog2190 = 0
        while query.next():
            record = query.record()
            MKB, postfixs = normalizeMKB(forceString(record.value('MKB')))
            isFirstDisability = forceBool(record.value('isFirstDisability'))
            invCategory = forceString(record.value('invCategory'))
            clientAge = forceInt(record.value('age'))
            clientSex = forceInt(record.value('sex'))

            if invCategory in (u'1с', u'2с', u'3с', u'4с'):
                cols = [3]
                if invCategory == u'3с':
                    cols.append(4)
                if clientAge <= 17:
                    cols.append(5)

                if isFirstDisability:
                    cols.append(0)
                    if invCategory == u'3с':
                        cols.append(1)
                    if clientAge <= 17:
                        cols.append(2)
            else:
                cols = [3]
                if invCategory == u'3о':
                    cols.append(4)
                if clientAge <= 17:
                    cols.append(5)

                if isFirstDisability:
                    cols.append(0)
                    if invCategory == u'3о':
                        cols.append(1)
                    if clientAge <= 17:
                        cols.append(2)

            rows = []
            for postfix in postfixs:
                rows.extend(mapMainRows2180.get((MKB, postfix), []))
                while len(MKB[:-1]) > 4:
                    MKB = MKB[:-1]
                    rows.extend(mapMainRows2180.get((MKB, postfix), []))



            if invCategory in (u'1с', u'2с', u'3с', u'4с'):
                for row in rows:
                    reportLine = reportMainData[row]
                    for col in cols:
                        reportLine[col] += 1
                if rows and 0 in rows:
                    if clientSex == 1 and clientAge >= 18 and clientAge <= 65:
                        itog2190 += 1
                    if clientSex == 2 and clientAge >= 18 and clientAge <= 60:
                        itog2190 += 1
            else:
                for col in cols:
                    reportLine = reportMainData[6]
                    reportLine[col] += 1
                if clientSex == 1 and clientAge >= 18 and clientAge <= 65:
                    itog2190 += 1
                if clientSex == 2 and clientAge >= 18 and clientAge <= 60:
                    itog2190 += 1

        t = QtGui.QTextBlockFormat()
        for row, rowDescr in enumerate(MainRows2180):
            reportLine = reportMainData[row]
            i = table.addRow()
            t.setLeftMargin(rowDescr[0] * 10)
            table.setText(i, 0, rowDescr[1], blockFormat=t)
            table.setText(i, 1, rowDescr[2])
            table.setText(i, 2, rowDescr[4])
            for col in xrange(rowSize):
                table.setText(i, 3 + col, reportLine[col])

        # 2181
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, u'Код по ОКЕИ: человек - 792', u'')
        cursor.insertText(u'(2181) Число пациентов с психическими расстройствами,\nклассифицированные в других рубриках МКБ-10, впервые признанных инвалидами\nв отчетном году 1 ______, имевших группу инвалидности на конец отчетного\nгода 2 _______.')

        # 2190
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        splitTitle(cursor, u'(2190)', u'Код по ОКЕИ: человек - 792', '60%')
        tableColumns = [
            ('28%', [u'Из общего числа инвалидов по психическому заболеванию (стр. 1 гр. 7 т. 2180):', u'лиц трудоспособного возраста', u'', u'1'], CReportBase.AlignCenter),
            ('10%', [u'', u'работают:', u'на общем производстве', u'2'], CReportBase.AlignCenter),
            ('10%', [u'', u'', u'в спеццехах', u'3'], CReportBase.AlignCenter),
            ('10%', [u'', u'', u'в ЛТМ (ЛПМ)', u'4'], CReportBase.AlignCenter)
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 1, 4)
        table.mergeCells(1, 0, 2, 1)
        table.mergeCells(1, 1, 1, 3)
        i = table.addRow()
        rowSize = 4
        for col in xrange(rowSize):
            if col == 0:
                table.setText(i, col, itog2190)
            else:
                table.setText(i, col, 0)

        return doc