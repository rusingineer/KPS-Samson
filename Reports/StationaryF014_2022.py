# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4                      import QtGui
from PyQt4.QtCore               import QDate
from library.Utils              import forceInt, forceString
from library.MapCode            import createMapCodeToRowIdx
from Events.Utils               import getActionTypeIdListByFlatCode
from Reports.ReportBase         import CReportBase, createTable
from Reports.Report             import normalizeMKB
from Reports.StationaryF007     import getStringProperty
from Reports.StationaryF014     import CStationaryF014
from Reports.Utils              import getDataOrgStructure, getOrgStructureProperty


Rows4201 = [
    ( u'Трансплантации всего, в том числе:', u'1'),
    ( u'легкого', u'2'),
    ( u'сердца', u'3'),
    ( u'печени', u'4'),
    ( u'поджелудочной железы', u'5'),
    ( u'тонкой кишки', u'6'),
    ( u'почки', u'7'),
    ( u'костного мозга', u'8'),
    ( u'    в том числе: аутологичного', u'8.1'),
    ( u'    аллогенного', u'8.2'),
    ( u'прочих органов', u'9'),
    ( u'трансплантации 2-х и более органов', u'10')
]

Rows2910 = [
    ( u'сахарный диабет (из стр. 5.4)', u'1', u'E10-E11, E13-E14'),
    ( u'болезни, характеризующиеся повышенным кровяным давлением (из стр. 10.3)', u'2', u'I10, I11.9, I12.9, I13.9'),
    ( u'хроническая ишемическая болезнь сердца (стр. 10.4.5)', u'3', u'I25'),
    ( u'бронхит хронический и неуточненный, эмфизема (стр. 11.7)', u'4', u'J40-J43'),
    ( u'другая хроническая обструктивная легочная болезнь (стр. 11.8)', u'5', u'J44'),
    ( u'бронхоэктатическая болезнь (стр. 11.9)', u'6', u'J47'),
    ( u'астма, астматический статус (стр. 11.10)', u'7', u'J45, J46'),
]


class CStationaryF144201_2022(CStationaryF014):
    def __init__(self, parent=None):
        CStationaryF014.__init__(self, parent)
        self.stationaryF14SetupDialog = None


    def writeReportLine(self, table, row, records):
        reportLine = [0] * 7
        for record in records:
            countDeathSurgery = forceInt(record.value('countDeathSurgery'))
            clientAge = forceInt(record.value('clientAge'))
            countComplication = forceInt(record.value('countComplication'))
            countMorphologicalStudy = forceInt(record.value('countMorphologicalStudy'))
            reportLine[0] += 1
            if countComplication:
                reportLine[2] += 1
            if countDeathSurgery:
                reportLine[4] += 1
            if countMorphologicalStudy:
                reportLine[6] += 1
            if clientAge <= 17:
                reportLine[1] += 1
                if countComplication:
                    reportLine[3] += 1
                if countDeathSurgery:
                    reportLine[5] += 1
        table.setText(row, 2, reportLine[0])
        table.setText(row, 3, reportLine[1])
        table.setText(row, 4, reportLine[2])
        table.setText(row, 5, reportLine[3])
        table.setText(row, 6, reportLine[4])
        table.setText(row, 7, reportLine[5])
        table.setText(row, 8, reportLine[6])


    def build(self, params):
        orgStructureIndex = self.stationaryF14SetupDialog.cmbOrgStructure._model.index(self.stationaryF14SetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14SetupDialog.cmbOrgStructure.rootModelIndex())
        orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex) if orgStructureIndex.row() else []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'(4201)')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

        cols = [
            ('25%',[u'Наименование трансплантаций', u'1'], CReportBase.AlignLeft),
            ('5%', [u'№ строки', u'2'], CReportBase.AlignCenter),
            ('10%',[u'Проведено операций (трансплантаций) - всего', u'3'], CReportBase.AlignRight),
            ('10%',[u'из них: детям', u'4'], CReportBase.AlignRight),
            ('10%',[u'Число операций, при которых наблюдались осложнения (из гр. 3)', u'5'], CReportBase.AlignRight),
            ('10%',[u'из них: детям', u'6'], CReportBase.AlignRight),
            ('10%',[u'Умерло оперированных (из гр. 3)', u'7'], CReportBase.AlignRight),
            ('10%',[u'из них: детей (из гр. 7)', u'8'], CReportBase.AlignRight),
            ('10%',[u'Направлено материалов на морфологическое исследование (из гр. 3)', u'9'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, cols)

        recordsAll = self.getTransplantation(orgStructureIdList, begDate, endDate, u'трансплантация%')
        recordsBuds = self.getTransplantation(orgStructureIdList, begDate, endDate, u'трансплантация почки%')
        recordsPancreat = self.getTransplantation(orgStructureIdList, begDate, endDate, u'трансплантация поджелудочной железы%')
        recordsHearts = self.getTransplantation(orgStructureIdList, begDate, endDate, u'трансплантация сердца%')
        recordsBaking = self.getTransplantation(orgStructureIdList, begDate, endDate, u'трансплантация печени%')
        recordsMedulla = self.getTransplantation(orgStructureIdList, begDate, endDate, u'трансплантация костного мозга%')
        recordsLung = self.getTransplantation(orgStructureIdList, begDate, endDate, u'трансплантация легк%')
        recordsTK = self.getTransplantation(orgStructureIdList, begDate, endDate, u'трансплантация тонкой кишки%')
        recordsPR = self.getTransplantation(orgStructureIdList, begDate, endDate, u'трансплантация прочих органов%')
        recordsNesk = self.getTransplantation(orgStructureIdList, begDate, endDate, u'трансплантация двух и более органов%')

        for name, line in Rows4201:
            i = table.addRow()
            table.setText(i, 0, name)
            table.setText(i, 1, line)
        self.writeReportLine(table, 2, recordsAll)
        self.writeReportLine(table, 3, recordsLung)
        self.writeReportLine(table, 4, recordsHearts)
        self.writeReportLine(table, 5, recordsBaking)
        self.writeReportLine(table, 6, recordsPancreat)
        self.writeReportLine(table, 7, recordsTK)
        self.writeReportLine(table, 8, recordsBuds)
        self.writeReportLine(table, 9, recordsMedulla)
        self.writeReportLine(table,10, [])
        self.writeReportLine(table,11, [])
        self.writeReportLine(table,12, recordsPR)
        self.writeReportLine(table,13, recordsNesk)

        return doc


    def getTransplantation(self, orgStructureIdList, begDateTime, endDateTime, nameTrasplantate):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableClient = db.table('Client')
        tableRBService = db.table('rbService')
        tableEventType = db.table('EventType')
        tableRBMedicalAidType = db.table('rbMedicalAidType')
        table = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
        cond = [
            tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('received%')),
            tableEvent['deleted'].eq(0),
            tableAction['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableClient['deleted'].eq(0),
            tableEventType['deleted'].eq(0),
        ]
        socStatusClassId = self.params.get('socStatusClassId', None)
        socStatusTypeId  = self.params.get('socStatusTypeId', None)
        if socStatusClassId or socStatusTypeId:
            tableClientSocStatus = db.table('ClientSocStatus')
            if begDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                   tableClientSocStatus['endDate'].ge(begDateTime)
                                                  ]),
                                       tableClientSocStatus['endDate'].isNull()
                                      ]))
            if endDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                   tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                  ]),
                                       tableClientSocStatus['begDate'].isNull()
                                      ]))
            table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
            if socStatusClassId:
                cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
            if socStatusTypeId:
                cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
            cond.append(tableClientSocStatus['deleted'].eq(0))
        cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
        joinOr1 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNull()])
        joinOr2 = db.joinAnd([tableAction['begDate'].isNotNull(), tableAction['begDate'].ge(begDateTime), tableAction['begDate'].lt(endDateTime.addDays(1))])
        joinOr3 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNotNull(), tableAction['endDate'].ge(begDateTime)])
        joinOr4 = db.joinAnd([tableAction['begDate'].isNotNull(), tableAction['begDate'].lt(begDateTime.addDays(1)), db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(begDateTime)])])
        cond.append(db.joinOr([joinOr1, joinOr2, joinOr3, joinOr4]))
        if orgStructureIdList:
            cond.append(getDataOrgStructure(u'Направлен в отделение', orgStructureIdList))
        eventIdList = db.getDistinctIdList(table, 'Event.id', cond)
        if eventIdList:
            cols = [
                tableAction['id'].alias('actionId'),
                tableAction['event_id'],
            ]
            cols.append('age(Client.birthDate, Event.setDate) AS clientAge')
            cols.append('%s AS countDeathSurgery'%(getStringProperty(u'Исход операции', u'(APS.value LIKE \'умер%\' OR APS.value LIKE \'смерть%\')')))
            cols.append('%s AS countMorphologicalStudy'%(getStringProperty(u'Направление на морфологию', u'(APS.value = \'да\' OR APS.value = \'ДА\' OR APS.value = \'Да\')')))
            cols.append('%s AS countComplication'%(getStringProperty(u'Осложнение', u'(APS.value != \'\' OR APS.value != \' \')')))
            table = tableAction.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
            table = table.innerJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
            table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            cond = [
                tableAction['event_id'].inlist(eventIdList),
                tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableActionType['class'].eq(2),
                tableAction['endDate'].isNotNull()
            ]
            socStatusClassId = self.params.get('socStatusClassId', None)
            socStatusTypeId  = self.params.get('socStatusTypeId', None)
            if socStatusClassId or socStatusTypeId:
                tableClientSocStatus = db.table('ClientSocStatus')
                if begDateTime:
                    cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                       tableClientSocStatus['endDate'].ge(begDateTime)
                                                      ]),
                                           tableClientSocStatus['endDate'].isNull()
                                          ]))
                if endDateTime:
                    cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                       tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                      ]),
                                           tableClientSocStatus['begDate'].isNull()
                                          ]))
                table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
                if socStatusClassId:
                    cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
                if socStatusTypeId:
                    cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
                cond.append(tableClientSocStatus['deleted'].eq(0))
            cond.append(tableRBService['name'].like(nameTrasplantate))
            return db.getRecordList(table, cols, cond)
        return []


class CStationaryF014_2910_2022(CStationaryF014):
    def __init__(self, parent=None):
        CStationaryF014.__init__(self, parent)
        self.stationaryF14SetupDialog = None


    def getSetupDialog(self, parent):
        dialog = CStationaryF014.getSetupDialog(self, parent)
        dialog.setSpecialDeliverClientVisible(False)
        dialog.setTypeSurgeryVisible(False)
        # dialog.setSocStatusVisible(False)
        dialog.setSelectActionTypeVisible(False)
        return dialog


    def build(self, params):
        params['selectActionType'] = 3  # по выписке
        orgStructureIndex = self.stationaryF14SetupDialog.cmbOrgStructure._model.index(self.stationaryF14SetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14SetupDialog.cmbOrgStructure.rootModelIndex())
        orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex) if orgStructureIndex.row() else []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'(2910)')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

        mapMainRows = createMapCodeToRowIdx([row[2] for row in Rows2910])
        rowSize = 16
        reportMainData = [ [0]*rowSize for row in xrange(len(Rows2910)) ]
        reportMainDataDied = [ [0]*rowSize for row in xrange(len(Rows2910)) ]
        query = self.selectData(orgStructureIdList, begDate, endDate, financeId)

        while query.next():
            record = query.record()
            MKB = normalizeMKB(forceString(record.value('MKB')))
            age = forceInt(record.value('clientAge'))
            isDied = forceInt(record.value('isDied'))
            for row in mapMainRows.get(MKB, []):
                reportLine = (reportMainDataDied if isDied else reportMainData)[row]
                col = -1
                if 0 <= age <= 14: col = 0
                elif 15 <= age <= 19: col = 1
                elif 20 <= age <= 24: col = 2
                elif 25 <= age <= 29: col = 3
                elif 30 <= age <= 34: col = 4
                elif 35 <= age <= 39: col = 5
                elif 40 <= age <= 44: col = 6
                elif 45 <= age <= 49: col = 7
                elif 50 <= age <= 54: col = 8
                elif 55 <= age <= 59: col = 9
                elif 60 <= age <= 64: col = 10
                elif 65 <= age <= 69: col = 11
                elif 70 <= age <= 74: col = 12
                elif 75 <= age <= 79: col = 13
                elif 80 <= age <= 84: col = 14
                elif age >= 85: col = 15
                if col >= 0:
                    reportLine[col] += 1

        table = createTable(cursor, [
            ('10%',[u'Наименование болезни', u'', u'1'], CReportBase.AlignLeft),
            ('5%', [u'№ стр.', u'', u'2'], CReportBase.AlignCenter),
            ('5%', [u'Код по МКБ-10', u'', u'3'], CReportBase.AlignLeft),
            ('5%', [u'Выписано пациентов (из таб. 2000 гр.4 и гр.22) в возрасте', u'0-14 лет', u'4'], CReportBase.AlignRight),
            ('5%', [u'', u'15-19 лет', u'5'], CReportBase.AlignRight),
            ('5%', [u'', u'20-24 года', u'6'], CReportBase.AlignRight),
            ('5%', [u'', u'25-29 лет', u'7'], CReportBase.AlignRight),
            ('5%', [u'', u'30-34 года', u'8'], CReportBase.AlignRight),
            ('5%', [u'', u'35-39 лет', u'9'], CReportBase.AlignRight),
            ('5%', [u'', u'40-44 года', u'10'], CReportBase.AlignRight),
            ('5%', [u'', u'45-49 лет', u'11'], CReportBase.AlignRight),
            ('5%', [u'', u'50-54 года', u'12'], CReportBase.AlignRight),
            ('5%', [u'', u'55-59 лет', u'13'], CReportBase.AlignRight),
            ('5%', [u'', u'60-64 года', u'14'], CReportBase.AlignRight),
            ('5%', [u'', u'65-69 лет', u'15'], CReportBase.AlignRight),
            ('5%', [u'', u'70-74 года', u'16'], CReportBase.AlignRight),
            ('5%', [u'', u'75-79 лет', u'17'], CReportBase.AlignRight),
            ('5%', [u'', u'80-84 года', u'18'], CReportBase.AlignRight),
            ('5%', [u'', u'85 лет и старше', u'19'], CReportBase.AlignRight),
        ])
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 16)
        for row, rowDescr in enumerate(Rows2910):
            reportLine = reportMainData[row]
            row = table.addRow()
            table.setText(row, 0, rowDescr[0])
            table.setText(row, 1, rowDescr[1])
            table.setText(row, 2, rowDescr[2])
            for col in xrange(rowSize):
                table.setText(row, 3+col, reportLine[col])

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

        table = createTable(cursor, [
            ('10%',[u'Наименование болезни', u'', u'1'], CReportBase.AlignLeft),
            ('5%', [u'№ стр.', u'', u'2'], CReportBase.AlignCenter),
            ('5%', [u'Код по МКБ-10', u'', u'3'], CReportBase.AlignLeft),
            ('5%', [u'Умерло пациентов (из таб. 2000 гр.8 и гр.28) в возрасте', u'0-14 лет', u'20'], CReportBase.AlignRight),
            ('5%', [u'', u'15-19 лет', u'21'], CReportBase.AlignRight),
            ('5%', [u'', u'20-24 года', u'22'], CReportBase.AlignRight),
            ('5%', [u'', u'25-29 лет', u'23'], CReportBase.AlignRight),
            ('5%', [u'', u'30-34 года', u'24'], CReportBase.AlignRight),
            ('5%', [u'', u'35-39 лет', u'25'], CReportBase.AlignRight),
            ('5%', [u'', u'40-44 года', u'26'], CReportBase.AlignRight),
            ('5%', [u'', u'45-49 лет', u'27'], CReportBase.AlignRight),
            ('5%', [u'', u'50-54 года', u'28'], CReportBase.AlignRight),
            ('5%', [u'', u'55-59 лет', u'29'], CReportBase.AlignRight),
            ('5%', [u'', u'60-64 года', u'30'], CReportBase.AlignRight),
            ('5%', [u'', u'65-69 лет', u'31'], CReportBase.AlignRight),
            ('5%', [u'', u'70-74 года', u'32'], CReportBase.AlignRight),
            ('5%', [u'', u'75-79 лет', u'33'], CReportBase.AlignRight),
            ('5%', [u'', u'80-84 года', u'34'], CReportBase.AlignRight),
            ('5%', [u'', u'85 лет и старше', u'35'], CReportBase.AlignRight),
        ])
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 16)
        for row, rowDescr in enumerate(Rows2910):
            reportLine = reportMainDataDied[row]
            row = table.addRow()
            table.setText(row, 0, rowDescr[0])
            table.setText(row, 1, rowDescr[1])
            table.setText(row, 2, rowDescr[2])
            for col in xrange(rowSize):
                table.setText(row, 3+col, reportLine[col])

        return doc


    def selectData(self, orgStructureIdList, begDateTime, endDateTime, financeId):
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

        cond = [
            tableActionType['id'].inlist(getActionTypeIdListByFlatCode(u'leaved%')),
            tableAction['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableClient['deleted'].eq(0),
            tableDiagnosis['deleted'].eq(0),
            tableDiagnostic['deleted'].eq(0),
            tableAction['endDate'].isNotNull(),
            tableEventType['deleted'].eq(0),
        ]
        if orgStructureIdList:
            cond.append(getOrgStructureProperty(u'Отделение', orgStructureIdList))

        socStatusClassId = self.params.get('socStatusClassId', None)
        socStatusTypeId  = self.params.get('socStatusTypeId', None)
        if socStatusClassId or socStatusTypeId:
            tableClientSocStatus = db.table('ClientSocStatus')
            if begDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                   tableClientSocStatus['endDate'].ge(begDateTime)
                                                  ]),
                                       tableClientSocStatus['endDate'].isNull()
                                      ]))
            if endDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                   tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                  ]),
                                       tableClientSocStatus['begDate'].isNull()
                                      ]))
            queryTable = queryTable.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
            if socStatusClassId:
                cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
            if socStatusTypeId:
                cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
            cond.append(tableClientSocStatus['deleted'].eq(0))

        cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
        joinOr1 = db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].ge(begDateTime)])
        joinOr2 = db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].lt(endDateTime.addDays(1))])
        cond.append(db.joinAnd([joinOr1, joinOr2]))

        if financeId:
            cond.append('((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'%(str(financeId), str(financeId)))
            queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))

        cond.append(u"rbDiagnosisType.code = '1' OR"
                    u" (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id"
                    u" AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC"
                    u" INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id"
                    u" WHERE DT.code = '1' AND DC.event_id = Event.id LIMIT 1)))")
        cond.append('NOT ' + getStringProperty(u'Исход госпитализации', u'(APS.value LIKE \'%переведен в другой стационар%\')'))

        cols = [
            tableEvent['id'].alias('eventId'),
            tableAction['id'].alias('actionId'),
            tableAction['endDate'],
            tableClient['id'].alias('clientId'),
            tableClient['birthDate'],
            tableDiagnosis['MKB'],
            tableClient['birthGestationalAge'],
            u'age(Client.birthDate, Action.begDate) AS clientAge',

            u'(%s) AS isDied'%(getStringProperty(u'Исход госпитализации%',
                u'(APS.value LIKE \'умер%\' OR APS.value LIKE \'смерть%\')')),
        ]
        stmt = db.selectStmt(queryTable, cols, cond)
        return db.query(stmt)
