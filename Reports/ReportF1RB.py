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
from PyQt4.QtCore import *

from Reports.Report     import CReport, normalizeMKB
from Reports.ReportBase import CReportBase, createTable
from library.MapCode    import createMapCodeToRowIdx
from library.Utils      import *
from library.database   import addDateInRange
from Events.Utils           import getActionTypeIdListByFlatCode, getDeathDate
from Orgs.Utils         import getOrgStructureDescendants
from Reports.Utils      import getOrgStructureProperty
from Reports.StationaryF014 import CStationaryF014, CStationaryF14SetupDialog, MainRows
from StationaryF007     import getStringProperty

from Ui_ReportF1RBSetup import Ui_ReportF1RBSetupDialog


Rows1004 = [
              ( u'Всего', u'1.0', u'A00-T98'),
              ( u'в том числе:\nНекоторые инфекционные и паразитарные болезни', u'2.0', u'A00-B99'),
              ( u'Новообразования', u'3.0', u'C00-D48'),
              ( u'Болезни крови, кроветворных органов и отдельные нарушения, вовлекающие иммунный механизм', u'4.0', u'D50-D89'),
              ( u'из них:\nанемия', u'4.1', u'D50-D64'),
              ( u'нарушения свертываемости крови', u'4.2', u'D65-D68'),
              ( u'из них: диссеминированное внутрисосудистое свертывание (синдром дефибринации)', u'4.2.1', u'D65'),
              ( u'гемофилия', u'4.2.2', u'D66-D68'),
              ( u'отдельные нарушения, вовлекающие иммунный механизм', u'4.3', u'D80-D89'),
              ( u'Болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'5.0', u'E00-E90'),
              ( u'из них:\nтиреотоксикоз (гипертиреоз)', u'5.1', u'E05'),
              ( u'сахарный диабет', u'5.2', u'E10-E14'),
              ( u'в том числе:\nинсулинзависимый сахарный диабет', u'5.2.1', u'E10'),
              ( u'инсулиннезависимый сахарный диабет', u'5.2.2', u'E11'),
              ( u'ожирение', u'5.3', u'E66'),
              ( u'Психические расстройства и расстройства поведения', u'6.0', u'F01-F99'),
              ( u'Болезни нервной системы', u'7.0', u'G00-G98'),
              ( u'из них:\nэпилепсия, эпилептический статус', u'7.1', u'G40-G41'),
              ( u'болезни периферической нервной системы', u'7.2', u'G50-G72'),
              ( u'Болезни глаза и его придаточного аппарата', u'8.0', u'H00-H59'),
              ( u' из них:\nкатаракта', u'8.1', u'H25-H26'),
              ( u'глаукома', u'8.2', u'H40'),
              ( u'миопия', u'8.3', u'H52.1'),
              ( u'Болезни уха и сосцевидного отростка', u'9.0', u'H60-H95'),
              ( u'из них: хронический отит', u'9.1', u'H65.2-9, H66.1-3'),
              ( u'Болезни системы кровообращения', u'10.0', u'I00-I99'),
              ( u'из них:\nострая ревматичесская лихорадка', u'10.1', u'I00-I02'),
              ( u'хронические ревматические болезни сердца', u'10.2', u'I05-I09'),
              ( u'в том числе: ревматические пороки клапанов', u'10.2.1', u'I05-I08'),
              ( u'болезни, характеризующиеся повышенным кровяным давлением', u'10.3', u'I10-I13'),
              ( u'ишемическая болезнь сердца', u'10.4', u'I20-I25'),
              ( u'из общего числа больных ишемической болезнью больных:\nстенокардией', u'10.5', u'I20'),
              ( u'острым инфарктом миокарда', u'10.6', u'I21'),
              ( u'повторный инфаркт миокарда', u'10.7', u'I22'),
              ( u'некоторые текущие осложнения острого инфаркта миокарда', u'10.8', u'I23'),
              ( u'другие формы острой ишемической болезни сердца', u'10.9', u'I24'),
              ( u'цереброваскулярные болезни', u'10.10', u'I60-I69'),
              ( u'эндартериит, тромбангиит облитерирующий', u'10.11', u'I70.2,I73.1'),
              ( u'Болезни органов дыхания', u'11.0', u'J00-J98'),
              ( u' из них:\nпневмония', u'11.1', u'J12-J18'),
              ( u'аллергический ринит (поллиноз)', u'11.2', u'J30.1'),
              ( u'хронический фарингит, назофарингит, ринит, синусит', u'11.3', u'J31- J32'),
              ( u'хронические болезни миндалин и аденоидов, перитонзиллярный абсцесс', u'11.4', u'J35- J36'),
              ( u'бронхит хронический и неуточненный, эмфизема', u'11.5', u'J40-J43'),
              ( u'другая хроническая обструктивная легочная, бронхоэктатическая болезнь ', u'11.6', u'J44,J47'),
              ( u'астма; астматический статус', u'11.7', u'J45, J46'),
              ( u'интерстициальные, гнойные легочные болезни, другие болезни плевры', u'11.8', u'J84-J94'),
              ( u'Болезни органов пищеварения', u'12.0', u'K00-K92'),
              ( u' из них:\nязвенная болезнь желудка и 12-ти - перстной кишки', u'12.1', u'K25-K26'),
              ( u'гастрит и дуоденит', u'12.2', u'K29'),
              ( u'неинфекционный энтерит и колит', u'12.3', u'K50-K52'),
              ( u'болезни печени', u'12.4', u'K70-K76'),
              ( u'болезни желчного пузыря, желчевыводящих путей', u'12.5', u'K80-K83'),
              ( u'болезни поджелудочной железы', u'12.6', u'K85-K86'),
              ( u'Болезни кожи и подкожной клетчатки', u'13.0', u'L00-L99'),
              ( u'из них: атопический дерматит', u'13.1', u'L20'),
              ( u'контактный дерматит', u'13.2', u'L23-L25'),
              ( u'Болезни костно-мышечной системы и соединительной ткани', u'14.0', u'M00-M99'),
              ( u'из них:\nреактивные артропатии', u'14.1', u'M02'),
              ( u'серопозитивный и другие ревматоидные артриты', u'14.2', u'M05,M06'),
              ( u'артрозы', u'14.3', u'M15-M19'),
              ( u'системные поражения соединительной ткани', u'14.4', u'M30-M35'),
              ( u'анкилозирующий спондилит', u'14.5', u'M45'),
              ( u'остеопороз', u'14.6', u'M80-M81'),
              ( u'Болезни мочеполовой системы', u'15.0', u'N00-N99'),
              ( u' из них:\nгломерулярные, тубулоинтерстициальные болезни почек, другие болезни почки и мочеточника', u'15.1', u'N00-N15, N25-N28'),
              ( u'почечная недостаточность', u'15.2', u'N17-N19'),
              ( u'мочекаменная болезнь', u'15.3', u'N20-N21, N23'),
              ( u'болезни предстательной железы', u'15.4', u'N40-N42'),
              ( u'мужское бесплодие', u'15.5', u'N46'),
              ( u'доброкачественная дисплазия молочной железы', u'15.6', u'N60'),
              ( u'сальпингит и оофорит', u'15.7', u'N70'),
              ( u'эндометриоз', u'15.8', u'N80'),
              ( u'эрозия и эктропион шейки матки', u'15.9', u'N86'),
              ( u'расстройства менструаций ', u'15.10', u'N91-N94'),
              ( u'нарушения менопаузы и другие нарушения в околоменопаузном периоде', u'15.11', u'N95'),
              ( u'женское бесплодие', u'15.12', u'N97'),
              ( u'Беременность, роды и послеродовой период', u'16.0', u'O00-O99'),
              ( u'Врожденные аномалии, пороки развития, деформации и хромосомные нарушения', u'18.0', u'Q00-Q99'),
              ( u'из них:\nврожденные аномалии системы кровообращения', u'18.1', u'Q20-Q28'),
              ( u'Симптомы, признаки и оклонения от нормы, выявленные при клинических и лабораторных исследованиях, не классифицированные в других рубриках', u'19.0', u'R00-R99'),
              ( u'Травмы, отравления и некоторые другие последствия воздействия внешних причин', u'20.0', u'S00-T98'),
              ( u' Кроме того:\nфакторы, влияющие на состояние здоровья населения и обращения в учреждения здравоохранения', u'21.0', u'Z00-Z99'),
              ( u'из них:\nносители инфекционных заболеваний', u'21.1', u'Z22')
            ]


Rows4000 = [
              ( u'Выполнено выездов-всего', u'01'),
              ( u'в том числе: к гражданам Республики Беларусь, постоянно проживающим в Российской Федерации-всего', u'02'),
              ( u'из них: детям', u'03'),
              ( u'к гражданам Республики Беларусь, временно пребывающим и временно проживающим в Российской Федерации и работающим в организациях Российской Федерации по трудовым договорам', u'04'),
              ( u'к гражданам Республики Беларусь, временно пребывающим и временно проживающим в Российской Федерации', u'05'),
              ( u'из них: детям', u'06'),
              ( u'Число лиц, которым оказана медицинская помощь при выездах-всего', u'07'),
              ( u'в том числе: к гражданам Республики Беларусь, постоянно проживающим в Российской Федерации', u'08'),
              ( u'из них: детям', u'09'),
              ( u'гражданам Республики Беларусь, временно пребывающим и временно проживающим в Российской Федерации и работающим в организациях Российской Федерации по трудовым договорам', u'10'),
              ( u'гражданам Республики Беларусь, временно пребывающим и временно проживающим в Российской Федерации', u'11'),
              ( u'из них: детям', u'12'),
              ( u'Число лиц, которым оказана амбулаторная помощь-всего', u'13'),
              ( u'в том числе: к гражданам Республики Беларусь, постоянно проживающим в Российской Федерации', u'14'),
              ( u'из них: детям', u'15'),
              ( u'гражданам Республики Беларусь, временно пребывающим и временно проживающим в Российской Федерации и работающим в организациях Российской Федерации по трудовым договорам', u'16'),
              ( u'гражданам Республики Беларусь, временно пребывающим и временно проживающим в Российской Федерации', u'17'),
              ( u'из них: детям', u'18')
           ]


class CReportF1RBSetupDialog(QtGui.QDialog, Ui_ReportF1RBSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        return result


class CReportF1RB_AmbulatoryCare(CReport):
    def __init__(self, parent = None):
        CReport.__init__(self, parent)
        self.reportF1RBSetupDialog = None


    def getSetupDialog(self, parent):
        result = CReportF1RBSetupDialog(parent)
        self.reportF1RBSetupDialog = result
        return result


    def getSelectData1004(self, mapMainRows, reportMainData, params):
        orgStructureId   = params.get('orgStructureId', None)
        begDate          = params.get('begDate', QDate())
        endDate          = params.get('endDate', QDate())
        db = QtGui.qApp.db
        tableClient           = db.table('Client')
        tablePerson           = db.table('Person')
        tableDiagnosis        = db.table('Diagnosis')
        tableDiseaseCharacter = db.table('rbDiseaseCharacter')
        tableDiagnosisType    = db.table('rbDiagnosisType')
        tableDiagnostic       = db.table('Diagnostic')
        tableClientSocStatus  = db.table('ClientSocStatus')
        tableSSC              = db.table('rbSocStatusClass')
        tableSST              = db.table('rbSocStatusType')
        queryTable = tableDiagnosis.innerJoin(tableClient, tableDiagnosis['client_id'].eq(tableClient['id']))
        queryTable = queryTable.innerJoin(tableDiagnosisType, tableDiagnosis['diagnosisType_id'].eq(tableDiagnosisType['id']))
        queryTable = queryTable.innerJoin(tableDiseaseCharacter, tableDiagnosis['character_id'].eq(tableDiseaseCharacter['id']))
        queryTable = queryTable.innerJoin(tableClientSocStatus,
                                         db.joinAnd([tableClientSocStatus['client_id'].eq(tableClient['id']), tableClientSocStatus['deleted'].eq(0)]))
        queryTable = queryTable.innerJoin(tableSSC, tableClientSocStatus['socStatusClass_id'].eq(tableSSC['id']))
        queryTable = queryTable.innerJoin(tableSST, tableClientSocStatus['socStatusType_id'].eq(tableSST['id']))
        cond = [ tableClient['deleted'].eq(0),
                 tableDiagnosis['deleted'].eq(0),
                 tableClientSocStatus['deleted'].eq(0)
               ]
        cond.append(db.joinOr([tableDiagnosis['setDate'].isNull(), tableDiagnosis['setDate'].le(endDate)]))
        cond.append(db.joinOr([tableDiagnosis['endDate'].ge(begDate), tableDiseaseCharacter['code'].eq('3')]))
        diagnosticQuery = tableDiagnostic
        diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                           tableDiagnostic['deleted'].eq(0)
                         ]
        if begDate and begDate.isValid():
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                               tableClientSocStatus['endDate'].ge(begDate)
                                              ]),
                                   tableClientSocStatus['endDate'].isNull()
                                  ]))
        if endDate and endDate.isValid():
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                               tableClientSocStatus['begDate'].lt(endDate.addDays(1))
                                              ]),
                                   tableClientSocStatus['begDate'].isNull()
                                  ]))
        cond.append('''rbSocStatusClass.id IN (SELECT rbSSC.id FROM rbSocStatusClass AS rbSSC WHERE rbSSC.code LIKE '8')''')
        cond.append(tableSST['code'].like(u'м112'))
        addDateInRange(diagnosticCond, tableDiagnostic['setDate'], begDate, endDate)
        if orgStructureId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
        else:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
        cond.append(db.existsStmt(diagnosticQuery, diagnosticCond))
        stmt="""
    SELECT
       COUNT(DISTINCT Diagnosis.client_id) AS clientCount,
       Diagnosis.MKB,
       IF(age(Client.birthDate, %s) < 18, 1, 0) AS clientChild
    FROM %s
    WHERE Diagnosis.deleted=0 AND Diagnosis.mod_id IS NULL AND %s
    GROUP BY MKB, clientChild
        """ % (db.formatDate(endDate),
               db.getTableName(queryTable),
               db.joinAnd(cond))
        records = db.query(stmt)
        while records.next():
            record = records.record()
            clientCount = forceInt(record.value('clientCount'))
            MKBRec = normalizeMKB(forceString(record.value('MKB')))
            clientChild = forceBool(record.value('clientChild'))
            for row in mapMainRows.get(MKBRec, []):
                reportLine = reportMainData[row]
                reportLine[0] += clientCount
                if clientChild:
                    reportLine[1] += clientCount
        return reportMainData


    def getSelectData1001(self, params):
        reportMainDataEvent = [0]*9
        orgStructureId   = params.get('orgStructureId', None)
        begDate          = params.get('begDate', QDate())
        endDate          = params.get('endDate', QDate())
        db = QtGui.qApp.db
        tableEvent           = db.table('Event')
        tableClient          = db.table('Client')
        tablePerson          = db.table('Person')
        tableOrganisation    = db.table('Organisation')
        tableRBOKFS          = db.table('rbOKFS')
        tableClientSocStatus = db.table('ClientSocStatus')
        tableSSC             = db.table('rbSocStatusClass')
        tableSST             = db.table('rbSocStatusType')
        cond = [tableEvent['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableClientSocStatus['deleted'].eq(0)
                ]
        queryTable = tableEvent.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        queryTable = queryTable.leftJoin(tablePerson, db.joinAnd([tableEvent['execPerson_id'].eq(tablePerson['id']), tablePerson['deleted'].eq(0)]))
        queryTable = queryTable.leftJoin(tableOrganisation, db.joinAnd([tableOrganisation['id'].eq(tablePerson['org_id']), tableOrganisation['deleted'].eq(0)]))
        queryTable = queryTable.innerJoin(tableRBOKFS, tableOrganisation['OKFS_id'].eq(tableRBOKFS['id']))
        queryTable = queryTable.innerJoin(tableClientSocStatus,
                                         db.joinAnd([tableClientSocStatus['client_id'].eq(tableClient['id']), tableClientSocStatus['deleted'].eq(0)]))
        queryTable = queryTable.innerJoin(tableSSC, tableClientSocStatus['socStatusClass_id'].eq(tableSSC['id']))
        queryTable = queryTable.innerJoin(tableSST, tableClientSocStatus['socStatusType_id'].eq(tableSST['id']))
        if begDate and begDate.isValid():
            cond.append(tableEvent['execDate'].ge(begDate))
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                               tableClientSocStatus['endDate'].ge(begDate)
                                              ]),
                                   tableClientSocStatus['endDate'].isNull()
                                  ]))
        if endDate and endDate.isValid():
            cond.append(tableEvent['setDate'].lt(endDate.addDays(1)))
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                               tableClientSocStatus['begDate'].lt(endDate.addDays(1))
                                              ]),
                                   tableClientSocStatus['begDate'].isNull()
                                  ]))
        cond.append('''rbSocStatusClass.id IN (SELECT rbSSC.id FROM rbSocStatusClass AS rbSSC WHERE rbSSC.code LIKE '8')''')
        cond.append(tableSST['code'].like(u'м112'))
        if orgStructureId:
            cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
        stmt="""
    SELECT
       COUNT(DISTINCT Event.client_id) AS clientCount,
       IF(rbOKFS.code = 14, 1, 0) AS codeMunicipal,
       IF((ClientSocStatus.begDate IS NOT NULL AND ClientSocStatus.endDate IS NULL), 1, 0) AS typeOfStay,
       getClientWorkId(Client.id) AS clientWorkId,
       IF(age(Client.birthDate, %s) < 18, 1, 0) AS clientChild
    FROM %s
    WHERE %s
    GROUP BY codeMunicipal, typeOfStay, clientWorkId, clientChild
        """ % (db.formatDate(endDate),
               db.getTableName(queryTable),
               db.joinAnd(cond))
        records = db.query(stmt)
        while records.next():
            record = records.record()
            clientCount   = forceInt(record.value('clientCount'))
            codeMunicipal = forceBool(record.value('codeMunicipal'))
            typeOfStay    = forceBool(record.value('typeOfStay'))
            clientChild   = forceBool(record.value('clientChild'))
            clientWorkId  = forceRef(record.value('clientWorkId'))
            if typeOfStay:
                reportMainDataEvent[0] += clientCount
                if clientChild:
                    reportMainDataEvent[1] += clientCount
                if not codeMunicipal:
                    reportMainDataEvent[2] += clientCount
                    if clientChild:
                        reportMainDataEvent[3] += clientCount
                else:
                    reportMainDataEvent[4] += clientCount
                    if clientChild:
                        reportMainDataEvent[5] += clientCount
            elif clientWorkId:
                    reportMainDataEvent[6] += clientCount
                    if codeMunicipal:
                        reportMainDataEvent[8] += clientCount
                    else:
                        reportMainDataEvent[7] += clientCount
        return reportMainDataEvent


    def getSelectData1002_1003(self, params):
        reportMainDataVisitAmb = [0]*9
        reportMainDataVisitHome = [0]*9
        orgStructureId   = params.get('orgStructureId', None)
        begDate          = params.get('begDate', QDate())
        endDate          = params.get('endDate', QDate())
        db = QtGui.qApp.db
        tableVisit           = db.table('Visit')
        tableEvent           = db.table('Event')
        tableClient          = db.table('Client')
        tablePerson          = db.table('Person')
        tableOrganisation    = db.table('Organisation')
        tableRBOKFS          = db.table('rbOKFS')
        tableRBScene         = db.table('rbScene')
        tableClientSocStatus = db.table('ClientSocStatus')
        tableSSC             = db.table('rbSocStatusClass')
        tableSST             = db.table('rbSocStatusType')
        cond = [tableVisit['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableClientSocStatus['deleted'].eq(0)
                ]
        cond.append('DATE(Event.setDate) <= DATE(Visit.date)')
        queryTable = tableVisit.innerJoin(tableEvent, tableEvent['id'].eq(tableVisit['event_id']))
        queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        queryTable = queryTable.innerJoin(tableRBScene, tableVisit['scene_id'].eq(tableRBScene['id']))
        queryTable = queryTable.leftJoin(tablePerson, db.joinAnd([tableEvent['execPerson_id'].eq(tablePerson['id']), tablePerson['deleted'].eq(0)]))
        queryTable = queryTable.leftJoin(tableOrganisation, db.joinAnd([tableOrganisation['id'].eq(tablePerson['org_id']), tableOrganisation['deleted'].eq(0)]))
        queryTable = queryTable.innerJoin(tableRBOKFS, tableOrganisation['OKFS_id'].eq(tableRBOKFS['id']))
        queryTable = queryTable.innerJoin(tableClientSocStatus,
                                         db.joinAnd([tableClientSocStatus['client_id'].eq(tableClient['id']), tableClientSocStatus['deleted'].eq(0)]))
        queryTable = queryTable.innerJoin(tableSSC, tableClientSocStatus['socStatusClass_id'].eq(tableSSC['id']))
        queryTable = queryTable.innerJoin(tableSST, tableClientSocStatus['socStatusType_id'].eq(tableSST['id']))
        addDateInRange(cond, tableVisit['date'], begDate, endDate)
        if begDate and begDate.isValid():
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                               tableClientSocStatus['endDate'].ge(begDate)
                                              ]),
                                   tableClientSocStatus['endDate'].isNull()
                                  ]))
        if endDate and endDate.isValid():
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                               tableClientSocStatus['begDate'].lt(endDate.addDays(1))
                                              ]),
                                   tableClientSocStatus['begDate'].isNull()
                                  ]))
        cond.append('''rbSocStatusClass.id IN (SELECT rbSSC.id FROM rbSocStatusClass AS rbSSC WHERE rbSSC.code LIKE '8')''')
        cond.append(tableSST['code'].like(u'м112'))
        if orgStructureId:
            cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
        stmt="""
    SELECT
       COUNT(DISTINCT Visit.id) AS visitCount,
       IF(rbScene.code, 1, 0) AS sceneAmb,
       IF(rbOKFS.code = 14, 1, 0) AS codeMunicipal,
       IF((ClientSocStatus.begDate IS NOT NULL AND ClientSocStatus.endDate IS NULL), 1, 0) AS typeOfStay,
       getClientWorkId(Client.id) AS clientWorkId,
       IF(age(Client.birthDate, %s) < 18, 1, 0) AS clientChild
    FROM %s
    WHERE %s
    GROUP BY sceneAmb, codeMunicipal, typeOfStay, clientWorkId, clientChild
        """ % (db.formatDate(endDate),
               db.getTableName(queryTable),
               db.joinAnd(cond))
        records = db.query(stmt)
        while records.next():
            record = records.record()
            visitCount    = forceInt(record.value('visitCount'))
            sceneAmb      = forceBool(record.value('sceneAmb'))
            codeMunicipal = forceBool(record.value('codeMunicipal'))
            typeOfStay    = forceBool(record.value('typeOfStay'))
            clientChild   = forceBool(record.value('clientChild'))
            clientWorkId  = forceRef(record.value('clientWorkId'))
            if sceneAmb:
                if typeOfStay:
                    reportMainDataVisitAmb[0] += visitCount
                    if clientChild:
                        reportMainDataVisitAmb[1] += visitCount
                    if not codeMunicipal:
                        reportMainDataVisitAmb[2] += visitCount
                        if clientChild:
                            reportMainDataVisitAmb[3] += visitCount
                    else:
                        reportMainDataVisitAmb[4] += visitCount
                        if clientChild:
                            reportMainDataVisitAmb[5] += visitCount
                elif clientWorkId:
                        reportMainDataVisitAmb[6] += visitCount
                        if codeMunicipal:
                            reportMainDataVisitAmb[8] += visitCount
                        else:
                            reportMainDataVisitAmb[7] += visitCount
            else:
                if typeOfStay:
                    reportMainDataVisitHome[0] += visitCount
                    if clientChild:
                        reportMainDataVisitHome[1] += visitCount
                    if not codeMunicipal:
                        reportMainDataVisitHome[2] += visitCount
                        if clientChild:
                            reportMainDataVisitHome[3] += visitCount
                    else:
                        reportMainDataVisitHome[4] += visitCount
                        if clientChild:
                            reportMainDataVisitHome[5] += visitCount
                elif clientWorkId:
                        reportMainDataVisitHome[6] += visitCount
                        if codeMunicipal:
                            reportMainDataVisitHome[8] += visitCount
                        else:
                            reportMainDataVisitHome[7] += visitCount
        return reportMainDataVisitAmb, reportMainDataVisitHome


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
            params['begDate'] = begDate
            params['endDate'] = endDate
        if begDate and endDate:
            mapMainRows = createMapCodeToRowIdx( [row[2] for row in Rows1004] )
            rowSize = 2
            reportMainData = [ [0]*rowSize for row in xrange(len(Rows1004)) ]
            reportMainData = self.getSelectData1004(mapMainRows, reportMainData, params)
            reportMainDataEvent = self.getSelectData1001(params)
            reportMainDataVisitAmb, reportMainDataVisitHome = self.getSelectData1002_1003(params)
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.setBlockFormat(CReportBase.AlignCenter)
            cursor.insertText(u'1. АМБУЛАТОРНО-ПОЛИКЛИНИЧЕСКАЯ ПОМОЩЬ')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.insertBlock()
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.setBlockFormat(CReportBase.AlignCenter)
            cursor.insertText(u'1.1. Сведения об оказании медицинской помощи гражданам Республики Беларусь\n\
            в государственных и муниципальных амбулаторно-поликлинических учреждениях Российской Федерации\n')
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cursor.setBlockFormat(CReportBase.AlignRight)
            cursor.insertText(u'Коды по ОКЕИ: человек - 792, единица - 642, посещения в смену - 545')
            cursor.insertBlock()
            cursor.setBlockFormat(CReportBase.AlignLeft)
            cursor.setCharFormat(CReportBase.ReportSubTitle)
            cursor.insertText(u'1001 Число граждан, обратившихся в государственные и муниципальные амбулаторно-поликлинические учреждения Российской Федерации (АПУ):\n')
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertText(u'\tграждан республики Беларусь, постоянно проживающих в Российской Федерации: всего %d, в том числе детей %d;\n'%(reportMainDataEvent[0], reportMainDataEvent[1]))
            cursor.insertText(u'\t\tиз них: из государственные АПУ: всего %d, в том числе детей %d;\n'%(reportMainDataEvent[2], reportMainDataEvent[3]))
            cursor.insertText(u'\t\tиз муниципальные АПУ: всего %d, в том числе детей %d\n'%(reportMainDataEvent[4], reportMainDataEvent[5]))
            cursor.insertText(u'\tграждан республики Беларусь, временно пребывающих и временно проживающих в Российской Федерации \
и работающих в организациях Российской Федерации по трудовым договорам: всего %d, \
из них: из государственные АПУ %d, из муниципальные АПУ %d.\n'%(reportMainDataEvent[6], reportMainDataEvent[7], reportMainDataEvent[8]))
            cursor.insertBlock()
            cursor.setCharFormat(CReportBase.ReportSubTitle)
            cursor.insertText(u'1002 Число посещений врачей государственных и муниципальных АПУ, включая профилактические:\n')
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertText(u'\tгражданами республики Беларусь, постоянно проживающими в Российской Федерации: всего %d, в том числе детьми %d;\n'%(reportMainDataVisitAmb[0], reportMainDataVisitAmb[1]))
            cursor.insertText(u'\t\tиз них: в государственные АПУ: всего %d, в том числе детьми %d;\n'%(reportMainDataVisitAmb[2], reportMainDataVisitAmb[3]))
            cursor.insertText(u'\t\tв муниципальные АПУ: всего %i, в том числе детьми %i\n'%(reportMainDataVisitAmb[4], reportMainDataVisitAmb[5]))
            cursor.insertText(u'\tгражданами республики Беларусь, временно пребывающими и временно проживающими в Российской Федерации \
и работающими в организациях Российской Федерации по трудовым договорам: всего %d, \
из них: в государственных АПУ %d, в муниципальных АПУ %d.\n'%(reportMainDataVisitAmb[6], reportMainDataVisitAmb[7], reportMainDataVisitAmb[8]))
            cursor.insertBlock()
            cursor.setCharFormat(CReportBase.ReportSubTitle)
            cursor.insertText(u'1003 Число посещений врачами государственных и муниципальных АПУ на дому:\n')
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertText(u'\tграждан республики Беларусь, постоянно проживающих в Российской Федерации: всего %d, в том числе детей %d;\n'%(reportMainDataVisitHome[0], reportMainDataVisitHome[1]))
            cursor.insertText(u'\t\tиз них: в государственных АПУ: всего %d, в том числе детей %d;\n'%(reportMainDataVisitHome[2], reportMainDataVisitHome[3]))
            cursor.insertText(u'\t\tв муниципальных АПУ: всего %d, в том числе детей %d\n'%(reportMainDataVisitHome[4], reportMainDataVisitHome[5]))
            cursor.insertText(u'\tграждан республики Беларусь, временно пребывающих и временно проживающих в Российской Федерации \
и работающих в организациях Российской Федерации по трудовым договорам: всего %d, \
из них: в государственных АПУ %d, в муниципальных АПУ %d.\n'%(reportMainDataVisitHome[6], reportMainDataVisitHome[7], reportMainDataVisitHome[8]))
            blockFormat = QtGui.QTextBlockFormat()
            blockFormat.setPageBreakPolicy(QtGui.QTextFormat.PageBreak_AlwaysBefore)
            cursor.insertBlock(blockFormat)
            cursor.insertBlock()
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.setBlockFormat(CReportBase.AlignCenter)
            cursor.insertText(u'1.2 Сведения о заболеваниях, зарегистрированных у больных граждан Республики Беларусь в государственных и муниципальных амбулаторно-поликлинических учреждениях Российской Федерации\n')
            cursor.setBlockFormat(CReportBase.AlignLeft)
            cursor.setCharFormat(CReportBase.ReportSubTitle)
            cursor.insertText(u'1004')
            cursor.setCharFormat(CReportBase.ReportBody)
            cols = [('30%',[u'Наименование классов и отдельных болезней',        u'',                             u'1'], CReportBase.AlignLeft),
                    ('10%',[u'№ строки',                                         u'',                             u'2'], CReportBase.AlignLeft),
                    ('30%',[u'Код по МКБ-10',                                    u'',                             u'3'], CReportBase.AlignLeft),
                    ('15%',[u'Зарегистрировано больных с данным заболеванием',   u'Всего',                        u'4'], CReportBase.AlignLeft),
                    ('15%',[u'',                                                 u'В том числе детей (0-17 лет)', u'5'], CReportBase.AlignLeft)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 2, 1)
            table.mergeCells(0, 1, 2, 1)
            table.mergeCells(0, 2, 2, 1)
            table.mergeCells(0, 3, 1, 2)
            for row, rowDescr in enumerate(Rows1004):
                reportLine = reportMainData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])
        return doc


class CReportF1RB_2000(CStationaryF014):
    def __init__(self, parent = None):
        CStationaryF014.__init__(self, parent)
        self.stationaryF14SetupDialog = None


    def getSetupDialog(self, parent):
        result = CStationaryF14SetupDialog(parent)
        self.stationaryF14SetupDialog = result
        self.stationaryF14SetupDialog.cmbTypeSurgery.setVisible(False)
        self.stationaryF14SetupDialog.lblTypeSurgery.setVisible(False)
        return result


    def dataLeavedMKB(self, eventOrder, mapMainRows, reportMainData, orgStructureId, begDateTime, endDateTime, financeId, age = None, children = False, isHospital = None, adult = False):
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableContract = db.table('Contract')
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnostic = db.table('Diagnostic')
        tableRBTraumaType = db.table('rbTraumaType')
        tableRBDiagnosisType = db.table('rbDiagnosisType')
        tableEventType = db.table('EventType')
        tableRBMedicalAidType = db.table('rbMedicalAidType')
        queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        queryTable = queryTable.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
        queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        queryTable = queryTable.innerJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
        queryTable = queryTable.innerJoin(tableDiagnosis, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
        queryTable = queryTable.innerJoin(tableRBDiagnosisType, tableDiagnostic['diagnosisType_id'].eq(tableRBDiagnosisType['id']))
        queryTable = queryTable.leftJoin(tableRBTraumaType, tableDiagnosis['traumaType_id'].eq(tableRBTraumaType['id']))
        leavedIdList = getActionTypeIdListByFlatCode(u'leaved%')
        cond = [ tableActionType['id'].inlist(leavedIdList),
                 tableAction['deleted'].eq(0),
                 tableEvent['deleted'].eq(0),
                 tableActionType['deleted'].eq(0),
                 tableClient['deleted'].eq(0),
                 tableDiagnosis['deleted'].eq(0),
                 tableDiagnostic['deleted'].eq(0),
                 tableAction['endDate'].isNotNull(),
                 tableEventType['deleted'].eq(0)
               ]
        if orgStructureId:
            orgStructureIndex = self.stationaryF14SetupDialog.cmbOrgStructure._model.index(self.stationaryF14SetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14SetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            if orgStructureIdList:
                cond.append('''%s'''%(getOrgStructureProperty(u'Отделение', orgStructureIdList)))
        cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
        joinOr1 = db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].ge(begDateTime)])
        joinOr2 = db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].lt(endDateTime)])
        cond.append(db.joinAnd([joinOr1, joinOr2]))
        cond.append(u'getClientCitizenship(Client.id, Action.begDate) = \'м112\'''')
        if financeId:
            cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(financeId), str(financeId)))
            queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
        cond.append(u'''rbDiagnosisType.code = '1' OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1' AND DC.event_id = Event.id LIMIT 1)))''')
        cond.append('NOT ' + getStringProperty(u'Исход госпитализации', u'(APS.value LIKE \'%%переведен в другой стационар%%\')'))
        cols = [tableEvent['id'].alias('eventId'),
                tableAction['id'].alias('actionId'),
                tableAction['endDate'],
                tableClient['id'].alias('clientId'),
                tableClient['birthDate'],
                tableDiagnosis['MKB']
                ]
        cols.append(u'''IF(Event.relegateOrg_id IS NOT NULL, (SELECT Organisation.id
        FROM Organisation WHERE Organisation.deleted = 0 AND Organisation.id = Event.relegateOrg_id
        AND Organisation.isMedical = 1), NULL) AS relegateOrgIsPoliklinik''')
        receivedIdList = getActionTypeIdListByFlatCode(u'received%')
        movingIdList = getActionTypeIdListByFlatCode(u'moving%')
        cols.append(u'''(SELECT APS_S.value
                        FROM Action AS A_S
                        INNER JOIN ActionType AS AT_S ON AT_S.id = A_S.actionType_id
                        INNER JOIN ActionPropertyType AS APT_S ON APT_S.actionType_id = AT_S.id
                        INNER JOIN ActionProperty AS AP_S ON AP_S.type_id = APT_S.id
                        INNER JOIN ActionProperty_String AS APS_S ON APS_S.id = AP_S.id
                        WHERE %sA_S.deleted=0
                        AND AP_S.deleted=0
                        AND APT_S.deleted=0
                        AND AP_S.action_id = A_S.id
                        AND A_S.event_id = Event.id
                        AND APT_S.name LIKE 'Кем доставлен') AS whatIsDeliver'''%((u'''A_S.actionType_id IN (%s) AND ''' % (','.join(str(receivedId) for receivedId in receivedIdList))) if receivedIdList else u''))
        cols.append(u'''(SELECT APS_S.value
                        FROM Action AS A_S
                        INNER JOIN ActionType AS AT_S ON AT_S.id = A_S.actionType_id
                        INNER JOIN ActionPropertyType AS APT_S ON APT_S.actionType_id = AT_S.id
                        INNER JOIN ActionProperty AS AP_S ON AP_S.type_id = APT_S.id
                        INNER JOIN ActionProperty_String AS APS_S ON APS_S.id = AP_S.id
                        WHERE %sA_S.deleted=0
                        AND AP_S.deleted=0
                        AND APT_S.deleted=0
                        AND AP_S.action_id = A_S.id
                        AND A_S.event_id = Event.id
                        AND APT_S.name LIKE 'Доставлен') AS deliverCall'''%((u'''A_S.actionType_id IN (%s) AND ''' % (','.join(str(receivedId) for receivedId in receivedIdList))) if receivedIdList else u''))
        cols.append(u'''(SELECT APS.value
                        FROM Action AS A
                        INNER JOIN ActionType AS AT ON AT.id = A.actionType_id
                        INNER JOIN ActionPropertyType AS APT ON APT.actionType_id = AT.id
                        INNER JOIN ActionProperty AS AP ON AP.type_id = APT.id
                        INNER JOIN ActionProperty_String AS APS ON APS.id = AP.id
                        WHERE %s A.event_id = Event.id AND A.deleted=0
                        AND AP.deleted=0
                        AND APT.deleted=0
                        AND AP.action_id = A.id
                        AND APT.name LIKE '%s') AS renunciationReceived'''%((u'''A.actionType_id IN (%s) AND ''' % (','.join(str(receivedId) for receivedId in receivedIdList))) if receivedIdList else u'',
                        u'Причина отказа от госпитализации'))
        cols.append(u'''(SELECT APS.value
                        FROM Action AS A
                        INNER JOIN ActionType AS AT ON AT.id = A.actionType_id
                        INNER JOIN ActionPropertyType AS APT ON APT.actionType_id = AT.id
                        INNER JOIN ActionProperty AS AP ON AP.type_id = APT.id
                        INNER JOIN ActionProperty_String AS APS ON APS.id = AP.id
                        WHERE %s A.event_id = Event.id AND A.deleted=0
                        AND AP.deleted=0
                        AND APT.deleted=0
                        AND AP.action_id = A.id
                        AND APT.name LIKE '%s') AS renunMeasuresReceived'''%((u'''A.actionType_id IN (%s) AND ''' % (','.join(str(receivedId) for receivedId in receivedIdList))) if receivedIdList else u'',
                        u'Принятые меры при отказе в госпитализации'))
        cols.append(u'''Event.order AS orderEvent''')
        if eventOrder == 2:
            cols.append(u'''IF(Event.order = 2, 1, 0) AS urgentReading''')
            cond.append(tableEvent['order'].eq(2))
        elif eventOrder == 1:
            cond.append((u''' EXISTS(SELECT APS_S.value
                        FROM Action AS A_S
                        INNER JOIN ActionType AS AT_S ON AT_S.id = A_S.actionType_id
                        INNER JOIN ActionPropertyType AS APT_S ON APT_S.actionType_id = AT_S.id
                        INNER JOIN ActionProperty AS AP_S ON AP_S.type_id = APT_S.id
                        INNER JOIN ActionProperty_String AS APS_S ON APS_S.id = AP_S.id
                        WHERE %sA_S.deleted=0
                        AND AP_S.deleted=0
                        AND APT_S.deleted=0
                        AND AP_S.action_id = A_S.id
                        AND A_S.event_id = Event.id
                        AND APT_S.name LIKE 'Доставлен по'
                        AND APS_S.value LIKE \'%%экстренным показаниям%%\')''' %((u'''A_S.actionType_id IN (%s) AND ''' % (','.join(str(receivedId) for receivedId in receivedIdList))) if receivedIdList else u'')))
            cols.append(u''' EXISTS(SELECT APS_S.value
                        FROM Action AS A_S
                        INNER JOIN ActionType AS AT_S ON AT_S.id = A_S.actionType_id
                        INNER JOIN ActionPropertyType AS APT_S ON APT_S.actionType_id = AT_S.id
                        INNER JOIN ActionProperty AS AP_S ON AP_S.type_id = APT_S.id
                        INNER JOIN ActionProperty_String AS APS_S ON APS_S.id = AP_S.id
                        WHERE %sA_S.deleted=0
                        AND AP_S.deleted=0
                        AND APT_S.deleted=0
                        AND AP_S.action_id = A_S.id
                        AND A_S.event_id = Event.id
                        AND APT_S.name LIKE 'Доставлен по'
                        AND APS_S.value LIKE \'%%экстренным показаниям%%\') AS urgentReadingAction''' %((u'''A_S.actionType_id IN (%s) AND ''' % (','.join(str(receivedId) for receivedId in receivedIdList))) if receivedIdList else u''))
        else:
            cols.append(u'''IF(Event.order = 2, 1, 0) AS urgentReading''')
            cols.append(u''' EXISTS(SELECT APS_S.value
                        FROM Action AS A_S
                        INNER JOIN ActionType AS AT_S ON AT_S.id = A_S.actionType_id
                        INNER JOIN ActionPropertyType AS APT_S ON APT_S.actionType_id = AT_S.id
                        INNER JOIN ActionProperty AS AP_S ON AP_S.type_id = APT_S.id
                        INNER JOIN ActionProperty_String AS APS_S ON APS_S.id = AP_S.id
                        WHERE %sA_S.deleted=0
                        AND AP_S.deleted=0
                        AND APT_S.deleted=0
                        AND AP_S.action_id = A_S.id
                        AND A_S.event_id = Event.id
                        AND APT_S.name LIKE 'Доставлен по'
                        AND APS_S.value LIKE \'%%экстренным показаниям%%\') AS urgentReadingAction''' %((u'''A_S.actionType_id IN (%s) AND ''' % (','.join(str(receivedId) for receivedId in receivedIdList))) if receivedIdList else u''))
        cols.append(u'''age(Client.birthDate, Action.begDate) AS clientAge''')
        cols.append(u'''(SELECT APS_S.value
                    FROM Action AS A_S
                    INNER JOIN ActionType AS AT_S ON AT_S.id = A_S.actionType_id
                    INNER JOIN ActionPropertyType AS APT_S ON APT_S.actionType_id = AT_S.id
                    INNER JOIN ActionProperty AS AP_S ON AP_S.type_id = APT_S.id
                    INNER JOIN ActionProperty_String AS APS_S ON APS_S.id = AP_S.id
                    WHERE A_S.id = Action.id AND A_S.deleted = 0
                    AND AP_S.deleted=0
                    AND APT_S.deleted=0
                    AND AP_S.action_id = A_S.id
                    AND A_S.event_id = Event.id
                    AND APT_S.name LIKE 'Причина отказа от пребывания'
                    AND APS_S.value) AS renunciationLeaved''')
        cols.append(u''' (SELECT A_S.begDate
                    FROM Action AS A_S
                    WHERE %sA_S.deleted=0
                    AND A_S.event_id = Event.id) AS begDateReceived''' %((u'''A_S.actionType_id IN (%s) AND ''' % (','.join(str(receivedId) for receivedId in receivedIdList))) if receivedIdList else u''))
        cols.append(u'''(%s) AS outDeath'''%(getStringProperty(u'Исход госпитализации%%', u'(APS.value LIKE \'умер%%\' OR APS.value LIKE \'смерть%%\')')))
        stmt = db.selectStmt(queryTable, cols, cond)
        query = db.query(stmt)
        days = 0
        cols = [tableAction['begDate'],
                tableEvent['id'].alias('eventId'),
                tableEvent['isPrimary'],
                tableEvent['setDate'],
                tableEvent['execDate'],
                tableAction['id'].alias('actionId'),
                tableAction['endDate'],
                tableClient['id'].alias('clientId'),
                tableDiagnosis['MKB']
                ]
        cols.append(u'''IF(rbTraumaType.code = 03 OR rbTraumaType.code = 08, 1, 0) AS traumaType''')
        renunciationList = [0]*4
        deathList = [0]*7
        deathMKB = [u'I60', u'I61', u'I62', u'I63', u'I64']
        eventIdList = []
        eventAndMovingIdList = []
        mapTraumaTypeRows = createMapCodeToRowIdx( [u'S00-T98'] )
        mapCerebroRows = createMapCodeToRowIdx( [u'I60, I61, I62, I63, I64, I65- I66, I67, I67.2'] )
        mapEmbRows = createMapCodeToRowIdx( [u'O00-O99'] )
        reportSubLine = [0]*27
        reportSubLine[8] = u'-'
        reportSubLine[9] = u'-'
        reportSubLine[12] = u'-'
        reportSubLine[15] = u'-'
        clientAge = None
        while query.next():
            record = query.record()
            eventId = forceRef(record.value('eventId'))
            if eventId and eventId not in eventIdList:
                eventIdList.append(eventId)
                clientId = forceRef(record.value('clientId'))
                relegateOrgIsPoliklinik = forceRef(record.value('relegateOrgIsPoliklinik'))
                whatIsDeliver = forceString(record.value('whatIsDeliver'))
                poliklinikCall = 1 if ((u'Поликлиника'.lower() in whatIsDeliver.lower()) or relegateOrgIsPoliklinik) else 0
                independentlyCall = 1 if u'Самостоятельно'.lower() in whatIsDeliver.lower() else 0
                orderEvent = forceInt(record.value('orderEvent'))
                clientAge = forceInt(record.value('clientAge'))
                birthDate = forceDate(record.value('birthDate'))
                begDateReceived = forceDate(record.value('begDateReceived'))
                deliverCall = forceString(record.value('deliverCall'))
                reportSubLine[18] += poliklinikCall
                if clientAge < 18:
                    reportSubLine[19] += poliklinikCall
                if orderEvent == 4:
                    reportSubLine[20] += 1
                    if clientAge < 18:
                        reportSubLine[21] += 1
                reportSubLine[22] += independentlyCall
                renunciationLeaved = forceString(record.value('renunciationLeaved'))
                renunciationReceived = forceString(record.value('renunciationReceived'))
                renunMeasuresReceived = forceString(record.value('renunMeasuresReceived'))
                if renunciationLeaved:
                    if u'отказ пациента' in renunciationLeaved.lower():
                        renunciationList[0] += 1
                    elif u'нет показаний' in renunciationLeaved.lower():
                        renunciationList[1] += 1
                    elif u'амбулаторно' in renunciationLeaved.lower():
                        renunciationList[2] += 1
                    elif u'стационар' in renunciationLeaved.lower():
                        renunciationList[3] += 1
                elif renunciationReceived:
                    if u'отказ пациента' in renunciationReceived.lower():
                        renunciationList[0] += 1
                    elif u'нет показаний' in renunciationReceived.lower():
                        renunciationList[1] += 1
                    elif u'амбулаторн' in renunciationReceived.lower():
                        renunciationList[2] += 1
                    elif u'стационар' in renunciationReceived.lower():
                        renunciationList[3] += 1
                if renunMeasuresReceived:
                    if u'амбулаторная помощь' in renunMeasuresReceived.lower() and u'амбулаторно' not in renunciationLeaved.lower() and u'амбулаторн' not in renunciationReceived.lower():
                        renunciationList[2] += 1
                    elif u'в другой стационар' in renunMeasuresReceived.lower() and u'стационар' not in renunciationLeaved.lower() and u'стационар' not in renunciationReceived.lower():
                        renunciationList[3] += 1
                outDeath = forceInt(record.value('outDeath'))
                if outDeath:
                    clientDeathDate = getDeathDate(clientId)
                    ageTuple = calcAgeTuple(birthDate, begDateReceived)
                    dayLev = 0
                    monthLev = 0
                    if ageTuple:
                        dayLev = ageTuple[0]
                        monthLev = ageTuple[2]
                    if clientDeathDate:
                        if begDateReceived == clientDeathDate:
                            if clientAge < 18:
                                deathList[0] += 1
                            elif clientAge >= 18 and clientAge <= 65:
                                deathList[1] += 1
                            if dayLev <= 1:
                                deathList[4] += 1
                            if dayLev <= 7:
                                deathList[3] += 1
                            if monthLev <= 12 and dayLev > 1:
                               deathList[5] += 1
                        else:
                            dayDeath = begDateReceived.daysTo(clientDeathDate)
                            if dayDeath >= 0 and dayDeath < 2:
                                if clientAge < 18:
                                    deathList[0] += 1
                                elif clientAge >= 18 and clientAge <= 65:
                                    deathList[1] += 1
                                if dayLev <= 1:
                                    deathList[4] += 1
                                if dayLev <= 7:
                                    deathList[3] += 1
                                if monthLev <= 12 and dayLev > 1:
                                   deathList[5] += 1
                cond = [tableAction['deleted'].eq(0),
                        tableAction['actionType_id'].inlist(movingIdList),
                        tableEvent['deleted'].eq(0),
                        tableEvent['id'].eq(eventId),
                        tableDiagnosis['deleted'].eq(0),
                        tableDiagnostic['deleted'].eq(0),
                        tableAction['endDate'].isNotNull()
                       ]
                cond.append(u'''rbDiagnosisType.code = '1' OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1' AND DC.event_id = Event.id LIMIT 1)))''')
                order = u'Action.begDate DESC'
                firstRecord = db.getRecordEx(queryTable, cols, cond, order)
                if firstRecord:
                    eventAndMovingId = forceRef(firstRecord.value('eventId'))
                    if eventAndMovingId not in eventAndMovingIdList:
                        eventAndMovingIdList.append(eventAndMovingId)
                        isHospitalRecord = None
                        MKBRec = normalizeMKB(forceString(firstRecord.value('MKB')))
                        if isHospital is not None:
                            isHospitalRecord = forceInt(record.value('isMedical'))
                        if MKBRec and isHospital == isHospitalRecord:
                            traumaType = forceInt(firstRecord.value('traumaType'))
                            if traumaType:
                                isPrimary = forceInt(firstRecord.value('isPrimary'))
                                setDate = forceDate(firstRecord.value('setDate'))
                                execDate = forceDate(firstRecord.value('execDate'))
                                for rowTraumaType in mapTraumaTypeRows.get(MKBRec, []):
                                    reportSubLine[0] += 1
                                    if isPrimary and setDate.daysTo(execDate) <= 30:
                                        reportSubLine[1] += 1
                                    if isPrimary and setDate.daysTo(execDate) <= 7:
                                        reportSubLine[2] += 1
                            if MKBRec in [u'I21', u'I22']:
                                if u'в первые 6часов' in deliverCall.lower() or u'в течении 7-24 часов' in deliverCall.lower():
                                    reportSubLine[7] += 1
                                reportSubLine[8] = u'-'
                                reportSubLine[9] = u'-'
                                if outDeath and begDateReceived == clientDeathDate:
                                    reportSubLine[10] += 1
                                    if clientAge <= 65:
                                        reportSubLine[11] += 1
                                reportSubLine[12] = u'-'
                            for rowCerebroType in mapCerebroRows.get(MKBRec, []):
                                reportSubLine[15] = u'-'
                                if u'в первые 6часов' in deliverCall.lower() or u'в течении 7-24 часов' in deliverCall.lower():
                                    reportSubLine[13] += 1
                                if u'в первые 6часов' in deliverCall.lower():
                                    reportSubLine[14] += 1
                            if outDeath:
                                if MKBRec in deathMKB:
                                   deathList[2] += 1
                                for pnewMKB in [u'J12', u'J18']:
                                    if pnewMKB in MKBRec:
                                        deathList[6] += 1
                                if MKBRec in [u'I21', u'I22']:
                                    reportSubLine[5] += 1
                                for rowEmbType in mapEmbRows.get(MKBRec, []):
                                    reportSubLine[16] += 1
                                    if not mapEmbRows.get(u'O30', []):
                                        reportSubLine[17] += 1
                            endDateRec = forceDate(record.value('endDate'))
                            divergenceDiagnosis = 0
                            countAutopsy = 0
                            countDeathChildren = 0
                            days = 0
                            recordReceived = self.dataReceivedMKB(eventId)
                            if recordReceived:
                                begDateRec = forceDate(recordReceived.value('begDate'))
                                if begDateRec and endDateRec:
                                    days += (begDateRec.daysTo(endDateRec)) if begDateRec != endDateRec else 1

                            if clientId and outDeath:
                                stmtDeath = u'''SELECT IF(rbResult.code > 0, 1, 0) AS divergenceDiagnosis, IF(Event.isPrimary = 1, 1, 0) AS autopsy, IF(age(Client.birthDate, Event.setDate) < 1, 1, 0) AS children
        FROM Event
        INNER JOIN EventType ON EventType.id = Event.eventType_id
        INNER JOIN rbEventTypePurpose ON rbEventTypePurpose.id = EventType.purpose_id
        INNER JOIN rbResult ON rbResult.id = Event.result_id
        INNER JOIN Client ON Client.id = Event.client_id
        WHERE Event.client_id = %d
        AND Event.deleted = 0 AND EventType.deleted = 0 AND Client.deleted = 0
        AND rbEventTypePurpose.code = 5 AND (EventType.code = 15 OR EventType.code = 23)'''%(clientId)
                                queryDeath = db.query(stmtDeath)
                                while queryDeath.next():
                                    recordDeath = queryDeath.record()
                                    divergenceDiagnosis += forceInt(recordDeath.value('divergenceDiagnosis'))
                                    countAutopsy += forceInt(recordDeath.value('autopsy'))
                                    countDeathChildren += forceInt(recordDeath.value('children'))
                            for row in mapMainRows.get(MKBRec, []):
                                reportLine = reportMainData[row]
                                reportLine[0] += 1
                                reportLine[2] += 1
                                reportLine[6] += days
                                reportLine[8] += days
                                reportLine[12] += outDeath
                                reportLine[14] += outDeath
                                if clientAge < 18:
                                    reportLine[1] += 1
                                    reportLine[3] += 1
                                    reportLine[7] += days
                                    reportLine[9] += days
                                    reportLine[13] += outDeath
                                    reportLine[15] += outDeath

        outHospitalRecords = self.getOutcomeOfHospitalization(eventOrder, orgStructureId, begDateTime, endDateTime, financeId, age, children, isHospital, adult)
        while outHospitalRecords.next():
            recordOH = outHospitalRecords.record()
            outHospital = forceString(recordOH.value('outHospital'))
            if outHospital:
                if u'переведен' in outHospital.lower():
                    svidORojd = forceBool(recordOH.value('svidORojd'))
                    reportSubLine[3] += 1
                    if clientAge < 1 and not svidORojd:
                        reportSubLine[4] += 1
                    if u'санаторий' in outHospital.lower():
                        reportSubLine[6] += 1
                    elif u'восстановит' in outHospital.lower():
                        reportSubLine[5] += 1
                    renunciationLeaved = forceString(recordOH.value('renunciationLeaved'))
                    renunciationReceived = forceString(recordOH.value('renunciationReceived'))
                    renunMeasuresReceived = forceString(recordOH.value('renunMeasuresReceived'))
                    if renunciationLeaved:
                        if u'отказ пациента' in renunciationLeaved.lower():
                            renunciationList[0] += 1
                        elif u'нет показаний' in renunciationLeaved.lower():
                            renunciationList[1] += 1
                        elif u'амбулаторно' in renunciationLeaved.lower():
                            renunciationList[2] += 1
                    elif renunciationReceived:
                        if u'отказ пациента' in renunciationReceived.lower():
                            renunciationList[0] += 1
                        elif u'нет показаний' in renunciationReceived.lower():
                            renunciationList[1] += 1
                        elif u'амбулаторн' in renunciationReceived.lower():
                            renunciationList[2] += 1
                    if renunMeasuresReceived:
                        if u'амбулаторная помощь' in renunMeasuresReceived.lower() and u'амбулаторно' not in renunciationLeaved.lower() and u'амбулаторн' not in renunciationReceived.lower():
                            renunciationList[2] += 1
                    if (renunciationLeaved and renunciationLeaved != u'') or (renunciationReceived and renunciationReceived != u'') or (renunMeasuresReceived and renunMeasuresReceived != u''):
                        renunciationList[3] += 1
        return reportMainData, renunciationList, deathList, reportSubLine


    def build(self, params):
        orgStructureId = params.get('orgStructureId', None)
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        orgStructureId = params.get('orgStructureId', None)
        eventOrder = params.get('eventOrder', 0)
        financeId = params.get('financeId', None)
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            mapMainRows = createMapCodeToRowIdx( [row[2] for row in MainRows] )
            rowSize = 18
            reportMainData = [ [0]*rowSize for row in xrange(len(MainRows)) ]
            reportMainData, renunciationList, deathList, reportSubLine = self.dataLeavedMKB(eventOrder, mapMainRows, reportMainData, orgStructureId, begDate, endDate, financeId)

            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.setBlockFormat(CReportBase.AlignCenter)
            cursor.insertText(u'2. СТАЦИОНАРНАЯ ПОМОЩЬ')
            cursor.insertBlock()
            cursor.insertText(u'2.1 Сведения об оказании медицинской помощи гражданам Республики Беларусь\n\
            в государственных и муниципальных учреждениях Российской Федерации\n')

            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cursor.setBlockFormat(CReportBase.AlignRight)
            cursor.insertText(u'Коды по ОКЕИ: человек - 792, единица - 642')
            cursor.insertBlock()
            cursor.setBlockFormat(CReportBase.AlignLeft)
            cursor.setCharFormat(CReportBase.ReportSubTitle)
            cursor.insertText(u'2001 Выписано больных:\n')
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertText(u'\tграждан республики Беларусь, постоянно проживающих в Российской Федерации: всего %i, в том числе детей %i;\n'%(reportMainData[0][0], reportMainData[0][1]))
            cursor.insertText(u'\t\tиз них: из государственных больничных учреждений: всего %i, в том числе детей %i;\n'%(reportMainData[0][2], reportMainData[0][3]))
            cursor.insertText(u'\t\tиз муниципальных больничных учреждений: всего %i, в том числе детей %i\n'%(reportMainData[0][4], reportMainData[0][5]))
            cursor.insertText(u'\tграждан республики Беларусь, временно пребывающих и временно проживающих в Российской Федерации \
и рабоающих в организациях Российской Федерации по трудовым договорам: всего 0, \
из них: из государственных больничных учреждений 0, из муниципальных больничных учреждений 0\n')
            cursor.insertBlock()

            cursor.setCharFormat(CReportBase.ReportSubTitle)
            cursor.insertText(u'2002 Проведено койко-дней:\n')
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertText(u'\tгражданами республики Беларусь, постоянно проживающими в Российской Федерации: всего %i, в том числе детьми %i;\n'%(reportMainData[0][6], reportMainData[0][7]))
            cursor.insertText(u'\t\tиз них: в государственных больничных учреждениях: всего %i, в том числе детьми %i;\n'%(reportMainData[0][8], reportMainData[0][9]))
            cursor.insertText(u'\t\tв муниципальных больничных учреждениях: всего %i, в том числе детьми %i\n'%(reportMainData[0][10], reportMainData[0][11]))
            cursor.insertText(u'\tгражданами республики Беларусь, временно пребывающими и временно проживающими в Российской Федерации \
и рабоающими в организациях Российской Федерации по трудовым договорам: всего 0, \
из них: в государственных больничных учреждениях 0, в муниципальных больничных учреждениях 0\n')
            cursor.insertBlock()

            cursor.setCharFormat(CReportBase.ReportSubTitle)
            cursor.insertText(u'2003 Умерло:\n')
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertText(u'\tграждан республики Беларусь, постоянно проживающих в Российской Федерации: всего %i, в том числе детей %i;\n'%(reportMainData[0][12], reportMainData[0][13]))
            cursor.insertText(u'\t\tиз них: в государственных больничных учреждениях: всего %i, в том числе детей %i;\n'%(reportMainData[0][14], reportMainData[0][15]))
            cursor.insertText(u'\t\tв муниципальных больничных учреждениях: всего %i, в том числе детей %i\n'%(reportMainData[0][16], reportMainData[0][17]))
            cursor.insertText(u'\tграждан республики Беларусь, временно пребывающих и временно проживающих в Российской Федерации \
и рабоающих в организациях Российской Федерации по трудовым договорам: всего 0, \
из них: в государственных больничных учреждениях 0, в муниципальных больничных учреждениях 0\n')

            blockFormat = QtGui.QTextBlockFormat()
            blockFormat.setPageBreakPolicy(QtGui.QTextFormat.PageBreak_AlwaysBefore)
            cursor.insertBlock(blockFormat)
            cursor.insertBlock()

            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.setBlockFormat(CReportBase.AlignCenter)
            cursor.insertText(u'2.2 Состав больных граждан Республики Беларусь в государственных и муниципальных\n\
            больничных учреждениях Российской Федерации, сроки и исходы лечения\n')
            cursor.setBlockFormat(CReportBase.AlignLeft)
            cursor.setCharFormat(CReportBase.ReportSubTitle)
            cursor.insertText(u'2004')
            cursor.setCharFormat(CReportBase.ReportBody)
            cols = [('10%',[u'Наименование болезни', u'', u'', u'', u'1'], CReportBase.AlignLeft),
                    ('4%', [u'№ строки', u'', u'', u'', u'2'], CReportBase.AlignLeft),
                    ('5%', [u'Код по МКБ 10', u'', u'', u'', u'3'], CReportBase.AlignLeft),

                    ('4.5%', [u'Выписано больных', u'Всего', u'', u'', u'4'], CReportBase.AlignLeft),
                    ('4.5%', [u'', u'В том числе детей', u'', u'', u'5'], CReportBase.AlignLeft),
                    ('4.5%', [u'', u'В том числе из больничных учреждений', u'Государственных', u'Всего', u'6'], CReportBase.AlignLeft),
                    ('4.5%', [u'', u'', u'', u'В т. ч. детей', u'7'], CReportBase.AlignLeft),
                    ('4.5%', [u'', u'', u'Муниципальных', u'Всего', u'8'], CReportBase.AlignLeft),
                    ('4.5%', [u'', u'', u'', u'В т. ч. детей', u'9'], CReportBase.AlignLeft),

                    ('4.5%', [u'Проведено всеми больными койко-дней', u'Всего', u'', u'', u'10'], CReportBase.AlignLeft),
                    ('4.5%', [u'', u'В том числе детей', u'', u'', u'11'], CReportBase.AlignLeft),
                    ('4.5%', [u'', u'В том числе в больничных учреждениях', u'Государственных', u'Всего', u'12'], CReportBase.AlignLeft),
                    ('4.5%', [u'', u'', u'', u'В т. ч. детей', u'13'], CReportBase.AlignLeft),
                    ('4.5%', [u'', u'', u'Муниципальных', u'Всего', u'14'], CReportBase.AlignLeft),
                    ('4.5%', [u'', u'', u'', u'В т. ч. детей', u'15'], CReportBase.AlignLeft),

                    ('4.5%', [u'Умерло', u'Всего', u'', u'', u'16'], CReportBase.AlignLeft),
                    ('4.5%', [u'', u'В том числе детей', u'', u'', u'17'], CReportBase.AlignLeft),
                    ('4.5%', [u'', u'В том числе в больничных учреждениях', u'Государственных', u'Всего', u'18'], CReportBase.AlignLeft),
                    ('4.5%', [u'', u'', u'', u'В т. ч. детей', u'19'], CReportBase.AlignLeft),
                    ('4.5%', [u'', u'', u'Муниципальных', u'Всего', u'20'], CReportBase.AlignLeft),
                    ('4.5%', [u'', u'', u'', u'В т. ч. детей', u'21'], CReportBase.AlignLeft)
                   ]

            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 4, 1)
            table.mergeCells(0, 1, 4, 1)
            table.mergeCells(0, 2, 4, 1)

            table.mergeCells(0, 3, 1, 6)
            table.mergeCells(1, 3, 3, 1)
            table.mergeCells(1, 4, 3, 1)
            table.mergeCells(1, 5, 1, 4)
            table.mergeCells(2, 5, 1, 2)
            table.mergeCells(2, 7, 1, 2)

            table.mergeCells(0, 9, 1, 6)
            table.mergeCells(1, 9, 3, 1)
            table.mergeCells(1, 10, 3, 1)
            table.mergeCells(1, 11, 1, 4)
            table.mergeCells(2, 11, 1, 2)
            table.mergeCells(2, 13, 1, 2)

            table.mergeCells(0, 15, 1, 6)
            table.mergeCells(1, 15, 3, 1)
            table.mergeCells(1, 16, 3, 1)
            table.mergeCells(1, 17, 1, 4)
            table.mergeCells(2, 17, 1, 2)
            table.mergeCells(2, 19, 1, 2)

            for row, rowDescr in enumerate(MainRows):
                reportLine = reportMainData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])
        return doc


class CReportF1RB_DentalTreatment(CReport):
    def __init__(self, parent = None):
        CReport.__init__(self, parent)
        self.reportF1RBSetupDialog = None


    def getSetupDialog(self, parent):
        result = CReportF1RBSetupDialog(parent)
        self.reportF1RBSetupDialog = result
        return result


    def getSelectData(self, params):
        reportMainData = [0]*9
        orgStructureId   = params.get('orgStructureId', None)
        begDate          = params.get('begDate', QDate())
        endDate          = params.get('endDate', QDate())
        db = QtGui.qApp.db
        tableVisit            = db.table('Visit')
        tableEvent            = db.table('Event')
        tableEventType        = db.table('EventType')
        tableClient           = db.table('Client')
        tablePerson           = db.table('Person')
        tableOrganisation     = db.table('Organisation')
        tableRBOKFS           = db.table('rbOKFS')
        tableRBMedicalAidType = db.table('rbMedicalAidType')
        tableClientSocStatus  = db.table('ClientSocStatus')
        tableSSC              = db.table('rbSocStatusClass')
        tableSST              = db.table('rbSocStatusType')
        cond = [tableVisit['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                tableEventType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableClientSocStatus['deleted'].eq(0)
                ]
        cond.append('DATE(Event.setDate) <= DATE(Visit.date)')
        cond.append(db.joinOr([tableEventType['form'].like('043'), tableRBMedicalAidType['code'].like('9')]))
        queryTable = tableVisit.innerJoin(tableEvent, tableEvent['id'].eq(tableVisit['event_id']))
        queryTable = queryTable.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        queryTable = queryTable.leftJoin(tableRBMedicalAidType, tableRBMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))
        queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        queryTable = queryTable.leftJoin(tablePerson, db.joinAnd([tableEvent['execPerson_id'].eq(tablePerson['id']), tablePerson['deleted'].eq(0)]))
        queryTable = queryTable.leftJoin(tableOrganisation, db.joinAnd([tableOrganisation['id'].eq(tablePerson['org_id']), tableOrganisation['deleted'].eq(0)]))
        queryTable = queryTable.innerJoin(tableRBOKFS, tableOrganisation['OKFS_id'].eq(tableRBOKFS['id']))
        queryTable = queryTable.innerJoin(tableClientSocStatus,
                                         db.joinAnd([tableClientSocStatus['client_id'].eq(tableClient['id']), tableClientSocStatus['deleted'].eq(0)]))
        queryTable = queryTable.innerJoin(tableSSC, tableClientSocStatus['socStatusClass_id'].eq(tableSSC['id']))
        queryTable = queryTable.innerJoin(tableSST, tableClientSocStatus['socStatusType_id'].eq(tableSST['id']))
        addDateInRange(cond, tableVisit['date'], begDate, endDate)
        if begDate and begDate.isValid():
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                               tableClientSocStatus['endDate'].ge(begDate)
                                              ]),
                                   tableClientSocStatus['endDate'].isNull()
                                  ]))
        if endDate and endDate.isValid():
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                               tableClientSocStatus['begDate'].lt(endDate.addDays(1))
                                              ]),
                                   tableClientSocStatus['begDate'].isNull()
                                  ]))
        cond.append('''rbSocStatusClass.id IN (SELECT rbSSC.id FROM rbSocStatusClass AS rbSSC WHERE rbSSC.code LIKE '8')''')
        cond.append(tableSST['code'].like(u'м112'))
        if orgStructureId:
            cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
        stmt="""
    SELECT
       COUNT(DISTINCT Visit.id) AS visitCount,
       IF(rbOKFS.code = 14, 1, 0) AS codeMunicipal,
       IF((ClientSocStatus.begDate IS NOT NULL AND ClientSocStatus.endDate IS NULL), 1, 0) AS typeOfStay,
       getClientWorkId(Client.id) AS clientWorkId,
       IF(age(Client.birthDate, %s) < 18, 1, 0) AS clientChild
    FROM %s
    WHERE %s
    GROUP BY codeMunicipal, typeOfStay, clientWorkId, clientChild
        """ % (db.formatDate(endDate),
               db.getTableName(queryTable),
               db.joinAnd(cond))
        records = db.query(stmt)
        while records.next():
            record = records.record()
            visitCount    = forceInt(record.value('visitCount'))
            codeMunicipal = forceBool(record.value('codeMunicipal'))
            typeOfStay    = forceBool(record.value('typeOfStay'))
            clientChild   = forceBool(record.value('clientChild'))
            clientWorkId  = forceRef(record.value('clientWorkId'))
            if typeOfStay:
                reportMainData[0] += visitCount
                if clientChild:
                    reportMainData[1] += visitCount
                if not codeMunicipal:
                    reportMainData[2] += visitCount
                    if clientChild:
                        reportMainData[3] += visitCount
                else:
                    reportMainData[4] += visitCount
                    if clientChild:
                        reportMainData[5] += visitCount
            elif clientWorkId:
                    reportMainData[6] += visitCount
                    if codeMunicipal:
                        reportMainData[8] += visitCount
                    else:
                        reportMainData[7] += visitCount
        return reportMainData


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
            params['begDate'] = begDate
            params['endDate'] = endDate
        if begDate and endDate:
            reportMainData = self.getSelectData(params)
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.setBlockFormat(CReportBase.AlignCenter)
            cursor.insertText(u'3. СТОМАТОЛОГИЧЕСКАЯ ПОМОЩЬ')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.insertBlock()
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cursor.setBlockFormat(CReportBase.AlignLeft)
            cursor.setCharFormat(CReportBase.ReportSubTitle)
            cursor.insertText(u'3000. Число посещений стоматологов и зубных врачей:\n')
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertText(u'\tгражданами республики Беларусь, постоянно проживающих в Российской Федерации: всего %d, в том числе детей %d;\n'%(reportMainData[0], reportMainData[1]))
            cursor.insertText(u'\t\tиз них: из государственных учреждений здравоохранения: всего %d, в том числе детей %d;\n'%(reportMainData[2], reportMainData[3]))
            cursor.insertText(u'\t\tиз муниципальных учреждений здравоохранения: всего %d, в том числе детей %d\n'%(reportMainData[4], reportMainData[5]))
            cursor.insertText(u'\tгражданами республики Беларусь, временно пребывающих и временно проживающих в Российской Федерации \
и рабоатющих в организациях Российской Федерации по трудовым договорам: всего %d, \
из них: из государственных учреждений здравоохранения %d, из муниципальных учреждений здравоохранения %d.\n'%(reportMainData[6], reportMainData[7], reportMainData[8]))
            cursor.insertBlock()
            blockFormat = QtGui.QTextBlockFormat()
            blockFormat.setPageBreakPolicy(QtGui.QTextFormat.PageBreak_AlwaysBefore)
            cursor.insertBlock(blockFormat)
        return doc


class CReportF1RB_AmbulanceCall(CReport):
    def __init__(self, parent = None):
        CReport.__init__(self, parent)
        self.reportF1RBSetupDialog = None


    def getSetupDialog(self, parent):
        result = CReportF1RBSetupDialog(parent)
        self.reportF1RBSetupDialog = result
        return result


    def getSelectData(self, reportMainData, params):
        def setReportLine(reportLineData, keyRow, record, eventCount):
            isHospital        = forceBool(record.value('isHospital'))
            isAccident        = forceBool(record.value('isAccident'))
            isDisease         = forceBool(record.value('isDisease'))
            isBirthFailure    = forceBool(record.value('isBirthFailure'))
            isPrimaryTransfer = forceBool(record.value('isPrimaryTransfer'))
            reportLineData[keyRow][0] += eventCount
            if isAccident:
                reportLineData[keyRow][1] += eventCount
            if isDisease:
                reportLineData[keyRow][2] += eventCount
            if isBirthFailure:
                reportLineData[keyRow][3] += eventCount
            if isPrimaryTransfer and isBirthFailure:
                reportLineData[keyRow][4] += eventCount
            if isHospital:
                reportLineData[keyRow][5] += eventCount
            return reportLineData
        orgStructureId   = params.get('orgStructureId', None)
        begDate          = params.get('begDate', QDate())
        endDate          = params.get('endDate', QDate())
        db = QtGui.qApp.db
        tableEvent             = db.table('Event')
        tableEventType         = db.table('EventType')
        tableClient            = db.table('Client')
        tablePerson            = db.table('Person')
        tableOrganisation      = db.table('Organisation')
        #tableRBEventTypePurpose = db.table('rbEventTypePurpose')
        tableClientSocStatus   = db.table('ClientSocStatus')
        tableEmergencyCall     = db.table('EmergencyCall')
        tableRBEmergencyResult = db.table('rbEmergencyResult')
        tableSSC               = db.table('rbSocStatusClass')
        tableSST               = db.table('rbSocStatusType')
        cond = [tableEvent['deleted'].eq(0),
                tableEventType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableClientSocStatus['deleted'].eq(0),
                tableEmergencyCall['deleted'].eq(0)
                ]
        queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        queryTable = queryTable.innerJoin(tableEmergencyCall, tableEmergencyCall['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        #queryTable = queryTable.innerJoin(tableRBResult, tableEvent['result_id'].eq(tableRBResult['id']))
        #IF(rbResult.code IN (SELECT ), 1, 0) AS isMedCare
        queryTable = queryTable.leftJoin(tablePerson, db.joinAnd([tableEvent['execPerson_id'].eq(tablePerson['id']), tablePerson['deleted'].eq(0)]))
        queryTable = queryTable.leftJoin(tableOrganisation, db.joinAnd([tableOrganisation['id'].eq(tablePerson['org_id']), tableOrganisation['deleted'].eq(0)]))
        queryTable = queryTable.innerJoin(tableClientSocStatus,
                                         db.joinAnd([tableClientSocStatus['client_id'].eq(tableClient['id']), tableClientSocStatus['deleted'].eq(0)]))
        queryTable = queryTable.leftJoin(tableRBEmergencyResult, tableRBEmergencyResult['id'].eq(tableEmergencyCall['resultCall_id']))
        queryTable = queryTable.innerJoin(tableSSC, tableClientSocStatus['socStatusClass_id'].eq(tableSSC['id']))
        queryTable = queryTable.innerJoin(tableSST, tableClientSocStatus['socStatusType_id'].eq(tableSST['id']))
#        cond = [tableRBEventTypePurpose['purpose'].eq(7),
#                tableEvent['deleted'].eq(0),
#                tableEventType['deleted'].eq(0),
#                tableClient['deleted'].eq(0),
#                tableClientSocStatus['deleted'].eq(0)
#                ]
#        queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
#        queryTable = queryTable.leftJoin(tableRBEventTypePurpose, tableRBEventTypePurpose['id'].eq(tableEventType['purpose_id']))
#        queryTable = queryTable.innerJoin(tableEmergencyCall, tableEmergencyCall['id'].eq(tableEventType['purpose_id']))
#        queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
#        queryTable = queryTable.leftJoin(tablePerson, db.joinAnd([tableEvent['execPerson_id'].eq(tablePerson['id']), tablePerson['deleted'].eq(0)]))
#        queryTable = queryTable.leftJoin(tableOrganisation, db.joinAnd([tableOrganisation['id'].eq(tablePerson['org_id']), tableOrganisation['deleted'].eq(0)]))
#        queryTable = queryTable.innerJoin(tableClientSocStatus,
#                                         db.joinAnd([tableClientSocStatus['client_id'].eq(tableClient['id']), tableClientSocStatus['deleted'].eq(0)]))
        if begDate and begDate.isValid():
            cond.append(tableEvent['execDate'].ge(begDate))
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                               tableClientSocStatus['endDate'].ge(begDate)
                                              ]),
                                   tableClientSocStatus['endDate'].isNull()
                                  ]))
        if endDate and endDate.isValid():
            cond.append(tableEvent['setDate'].lt(endDate.addDays(1)))
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                               tableClientSocStatus['begDate'].lt(endDate.addDays(1))
                                              ]),
                                   tableClientSocStatus['begDate'].isNull()
                                  ]))
        cond.append('''rbSocStatusClass.id IN (SELECT rbSSC.id FROM rbSocStatusClass AS rbSSC WHERE rbSSC.code LIKE '8')''')
        cond.append(tableSST['code'].like(u'м112'))
        if orgStructureId:
            cond.append(tableEmergencyCall['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
        stmt="""
    SELECT
       COUNT(DISTINCT Event.id) AS eventCount,
       IF((ClientSocStatus.begDate IS NOT NULL AND ClientSocStatus.endDate IS NULL), 1, 0) AS typeOfStay,
       getClientWorkId(Client.id) AS clientWorkId,
       IF(age(Client.birthDate, %s) < 18, 1, 0) AS clientChild,
       IF(rbEmergencyResult.code = 4, 1, 0) AS isHospital,
       IF(EmergencyCall.accident_id IS NOT NULL, 1, 0) AS isAccident,
       IF(EmergencyCall.disease = 1, 1, 0) AS isDisease,
       IF(EmergencyCall.birth = 1 OR EmergencyCall.pregnancyFailure = 1, 1, 0) AS isBirthFailure,
       IF(Event.isPrimary IN (1,2,3), 1, 0) AS isPrimaryHelp,
       IF(Event.isPrimary = 4, 1, 0) AS isPrimaryTransfer,
       IF(Event.isPrimary = 5, 1, 0) AS isPrimaryAmb
    FROM %s
    WHERE %s
    GROUP BY typeOfStay, clientWorkId, clientChild, isHospital, isAccident, isDisease,
    isBirthFailure, isPrimaryHelp, isPrimaryTransfer, isPrimaryAmb
        """ % (db.formatDate(endDate),
               db.getTableName(queryTable),
               db.joinAnd(cond))
        records = db.query(stmt)
        while records.next():
            record = records.record()
            eventCount    = forceInt(record.value('eventCount'))
            typeOfStay    = forceBool(record.value('typeOfStay'))
            clientChild   = forceBool(record.value('clientChild'))
            clientWorkId  = forceRef(record.value('clientWorkId'))
            isPrimaryHelp = forceBool(record.value('isPrimaryHelp'))
            isPrimaryAmb  = forceBool(record.value('isPrimaryAmb'))
            reportMainData = setReportLine(reportMainData, u'01', record, eventCount)
            if typeOfStay:
                reportMainData = setReportLine(reportMainData, u'02', record, eventCount)
                if clientChild:
                    reportMainData = setReportLine(reportMainData, u'03', record, eventCount)
            else:
                if clientWorkId:
                    reportMainData = setReportLine(reportMainData, u'04', record, eventCount)
                else:
                    reportMainData = setReportLine(reportMainData, u'05', record, eventCount)
                if clientChild:
                    reportMainData = setReportLine(reportMainData, u'06', record, eventCount)
            if isPrimaryHelp:
                reportMainData = setReportLine(reportMainData, u'07', record, eventCount)
                if typeOfStay:
                    reportMainData = setReportLine(reportMainData, u'08', record, eventCount)
                    if clientChild:
                        reportMainData = setReportLine(reportMainData, u'09', record, eventCount)
                else:
                    if clientWorkId:
                        reportMainData = setReportLine(reportMainData, u'10', record, eventCount)
                    else:
                        reportMainData = setReportLine(reportMainData, u'11', record, eventCount)
                    if clientChild:
                        reportMainData = setReportLine(reportMainData, u'12', record, eventCount)
            if isPrimaryAmb:
                reportMainData = setReportLine(reportMainData, u'13', record, eventCount)
                if typeOfStay:
                    reportMainData = setReportLine(reportMainData, u'14', record, eventCount)
                    if clientChild:
                        reportMainData = setReportLine(reportMainData, u'15', record, eventCount)
                else:
                    if clientWorkId:
                        reportMainData = setReportLine(reportMainData, u'16', record, eventCount)
                    else:
                        reportMainData = setReportLine(reportMainData, u'17', record, eventCount)
                    if clientChild:
                        reportMainData = setReportLine(reportMainData, u'18', record, eventCount)


        return reportMainData


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
            params['begDate'] = begDate
            params['endDate'] = endDate
        if begDate and endDate:
            rowSize = 6
            reportMainData = {}
            for name, row in Rows4000:
                reportMainData[row] = [0]*rowSize
            reportMainData = self.getSelectData(reportMainData, params)
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.setBlockFormat(CReportBase.AlignCenter)
            cursor.insertText(u'4. СКОРАЯ МЕДИЦИНСКАЯ ПОМОЩЬ')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cursor.setBlockFormat(CReportBase.AlignRight)
            cursor.insertText(u'Коды по ОКЕИ: человек - 792, единица - 642')
            cursor.insertBlock()
            cursor.setBlockFormat(CReportBase.AlignLeft)
            blockFormat = QtGui.QTextBlockFormat()
            blockFormat.setPageBreakPolicy(QtGui.QTextFormat.PageBreak_AlwaysBefore)
            cursor.insertBlock(blockFormat)
            cursor.insertBlock()
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.setBlockFormat(CReportBase.AlignLeft)
            cursor.setCharFormat(CReportBase.ReportSubTitle)
            cursor.insertText(u'4000')
            cursor.setCharFormat(CReportBase.ReportBody)
            cols = [('30%',[u'Показатели',   u'',                                       u'',                                   u'1'], CReportBase.AlignLeft),
                    ('10%',[u'№ строки',     u'',                                       u'',                                   u'2'], CReportBase.AlignLeft),
                    ('10%',[u'Всего',        u'',                                       u'',                                   u'3'], CReportBase.AlignLeft),
                    ('10%',[u'В том числе:', u'оказание скорой помощи по поводу',       u'несчастных случаев',                 u'4'], CReportBase.AlignLeft),
                    ('10%',[u'',             u'',                                       u'внезапных заболеваний и состояний',  u'5'], CReportBase.AlignLeft),
                    ('10%',[u'',             u'',                                       u'родов и потологии беременности',     u'6'], CReportBase.AlignLeft),
                    ('10%',[u'',             u'перевозка больных, рожениц и родильниц', u'',                                   u'7'], CReportBase.AlignLeft),
                    ('10%',[u'',             u'число госпитализированных(из гр.3)',     u'',                                   u'8'], CReportBase.AlignLeft)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 3, 1)
            table.mergeCells(0, 1, 3, 1)
            table.mergeCells(0, 2, 3, 1)
            table.mergeCells(0, 3, 1, 5)
            table.mergeCells(1, 3, 1, 3)
            table.mergeCells(1, 6, 2, 1)
            table.mergeCells(1, 7, 2, 1)
            for row, rowDescr in enumerate(Rows4000):
                reportLine = reportMainData.get(rowDescr[1], [0]*rowSize)
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                for col in xrange(rowSize):
                    table.setText(i, 2+col, reportLine[col])
        return doc

