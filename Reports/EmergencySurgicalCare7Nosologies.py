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

from library.MapCode          import createMapCodeToRowIdx
from library.Utils            import forceBool, forceRef, forceString, forceStringEx

from Orgs.Utils               import getOrgStructureFullName
from Events.ActionServiceType import CActionServiceType
from Events.Utils             import getActionTypeIdListByFlatCode

from Reports.Report           import CReport, normalizeMKB
from Reports.ReportBase       import CReportBase, createTable
from Reports.ReportView       import CPageFormat
from Reports.Utils            import ( getStringPropertyLastEventValue,
#                                       isActionToServiceTypeForEvent,
                                       dateRangeAsStr,
                                       getOrgStructureProperty,
                                     )
from Reports.StationaryF014   import CStationaryF14SetupDialog


MainRows = [
            ( u'Острая непроходимость кишечника',       u'K56-K56.7',               u'1', u'2', u'Всего', u'из них позднее 24-х часов'),
            ( u'Острый аппендицит',                     u'K35-K35.8',               u'3', u'4', u'Всего', u'из них позднее 24-х часов'),
            ( u'Язва желудка и 12 п/к с кровотечением', u'K25.0,K25.4,K26.0,K26.4', u'5', u'6', u'Всего', u'из них позднее 24-х часов'),
            ( u'Язва желудка и 12 п/к с прободением',   u'K25.1,K25.5,K26.1,K26.5', u'7', u'8', u'Всего', u'из них позднее 24-х часов'),
            ( u'Язва желудка и 12 п/к с кровотечением и прободением', u'K25.2,K25.6,K26.2,K26.6', u'9', u'10',  u'Всего', u'из них позднее 24-х часов'),
            ( u'Желудочно кишечное кровотечение',                     u'K92.2',                   u'11', u'12', u'Всего', u'из них позднее 24-х часов'),
            ( u'Ущемленная грыжа(с непроходимостью)',                 u'K40.0,K41.0,K41.3,K42.0,K43.0,K44.0,K45.0,K46.0', u'13', u'14', u'Всего', u'из них позднее 24-х часов'),
            ( u'Острый холецистит',                                   u'K80.0,K81.0', u'15', u'16', u'Всего', u'из них позднее 24-х часов'),
            ( u'Острый панкреатит',                                   u'K85,K85.1',   u'17', u'18', u'Всего', u'из них позднее 24-х часов'),
            ( u'Внематочная беременность',                            u'O00-O00.9',   u'19', u'20', u'Всего', u'из них позднее 24-х часов'),
            ]


class CEmergencySurgicalCare7Nosologies(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Экстренная хирургическая помощь по 7 нозологиям.')
        self.params = {}
        self.orientation = CPageFormat.Landscape


    def getSetupDialog(self, parent):
        result = CStationaryF14SetupDialog(parent)
        result.setTypeSurgeryVisible(False)
        result.setSelectActionTypeVisible(False)
        self.setupDialog = result
        return result


    def dumpParams(self, cursor, params):
        description = []
        self.params = params
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        eventOrder = params.get('eventOrder', 0)
        if begDate and endDate:
            description.append(dateRangeAsStr(u'за период', begDate, endDate))
        orgStructureId = params.get('orgStructureId', None)
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        if eventOrder == 2:
            description.append(u'учет экстренных пациентов '+ u'по атрибуту События "экстренно"')
        elif eventOrder == 1:
            description.append(u'учет экстренных пациентов '+ u'по свойству "Доставлен по экстренным показаниям"')
        financeId = params.get('financeId', None)
        description.append(u'тип финансирования: %s'%(forceString(QtGui.qApp.db.translate('rbFinance', 'id', financeId, 'name')) if financeId else u'не задано'))
        socStatusClassId = params.get('socStatusClassId', None)
        if socStatusClassId:
            description.append(u'класс соц.статуса: %s'%(forceString(QtGui.qApp.db.translate('rbSocStatusClass', 'id', socStatusClassId, 'name'))))
        socStatusTypeId  = params.get('socStatusTypeId', None)
        if socStatusTypeId:
            description.append(u'тип соц.статуса: %s'%(forceString(QtGui.qApp.db.translate('rbSocStatusType', 'id', socStatusTypeId, 'name'))))
        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getOrgStructureIdList(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    def selectData(self, eventOrder, mapMainRows, reportMainData, reportMainData24, rowSize, orgStructureId, begDateTime, endDateTime, financeId):
        eventIdList = []
        totalLine = [0]*rowSize
        totalLine24 = [0]*rowSize
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableContract = db.table('Contract')
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnostic = db.table('Diagnostic')
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
        receivedIdList = getActionTypeIdListByFlatCode(u'received%')
        leavedIdList = getActionTypeIdListByFlatCode(u'leaved%')
        cols = [tableEvent['id'].alias('eventId'),
                tableAction['id'].alias('actionId'),
                tableClient['id'].alias('clientId'),
                tableDiagnosis['MKB'],
                ]
        cols.append(u'''EXISTS(SELECT APS_S.value
                        FROM Action AS A_S
                        INNER JOIN ActionType AS AT_S ON AT_S.id = A_S.actionType_id
                        INNER JOIN ActionPropertyType AS APT_S ON APT_S.actionType_id = AT_S.id
                        INNER JOIN ActionProperty AS AP_S ON AP_S.type_id = APT_S.id
                        INNER JOIN ActionProperty_String AS APS_S ON APS_S.id = AP_S.id
                        WHERE A_S.actionType_id = Action.actionType_id
                        AND A_S.deleted=0
                        AND AP_S.deleted=0
                        AND APT_S.deleted=0
                        AND AP_S.action_id = A_S.id
                        AND A_S.event_id = getFirstEventId(Event.id)
                        AND TRIM(APS_S.value) != '%s'
                        AND APT_S.name = 'Доставлен'
                        ORDER BY APS_S.id DESC) AS isDeliverCall'''%(u'позднее 24-х часов'))
        cols.append(u'%s AS isDeath'%(getStringPropertyLastEventValue(leavedIdList, u'Исход госпитализации%%', u'(APS.value LIKE \'умер%%\' OR APS.value LIKE \'смерть%%\')')))
        cols.append(u'''(SELECT DS.MKB
                        FROM Event AS E
                        INNER JOIN EventType AS ET ON ET.id = E.eventType_id
                        INNER JOIN rbEventTypePurpose AS rbETP ON rbETP.id = ET.purpose_id
                        INNER JOIN Diagnostic AS DC ON DC.event_id = E.id
                        INNER JOIN Diagnosis AS DS ON DC.`diagnosis_id`=DS.`id`
                        INNER JOIN rbDiagnosisType AS rbDT ON DC.`diagnosisType_id`=rbDT.`id`
                        WHERE E.client_id = Client.id
                        AND E.deleted = 0 AND ET.deleted = 0
                        AND rbETP.code = 5 AND (ET.code = 15 OR ET.code = 23)
                        AND (rbDT.code = '4'
                        OR (rbDT.code = '8' AND Diagnostic.person_id = E.execPerson_id
                        AND (NOT EXISTS(SELECT DC2.id FROM Diagnostic AS DC2
                                        INNER JOIN rbDiagnosisType AS DT ON DT.id = DC2.diagnosisType_id WHERE DT.code = '4'
                                        AND DC2.event_id = E.id LIMIT 1))))
                        ORDER BY E.execDate DESC
                        LIMIT 1) AS constDeathMKB''')
        cols.append(u'''EXISTS(SELECT A.id
                      FROM Action AS A
                      INNER JOIN ActionType AS AT ON AT.id = A.actionType_id
                      INNER JOIN Event AS E ON E.id = A.event_id
                      WHERE E.client_id = Client.id AND A.deleted = 0
                      AND AT.serviceType = %d AND AT.deleted = 0
                      AND A.endDate IS NOT NULL AND A.begDate >= Action.begDate
                      AND A.endDate <= (SELECT A2.begDate
                                        FROM Action AS A2
                                        WHERE A2.event_id = getLastEventId(Event.id) AND A2.deleted=0
                                        AND A2.actionType_id IN (%s) AND A2.begDate IS NOT NULL)) AS isOperation'''%(CActionServiceType.operation, (','.join(forceString(leavedId) for leavedId in leavedIdList if leavedId))))
        cols.append(u'''EXISTS(SELECT A.id
                                FROM Action AS A
                                WHERE A.event_id = getLastEventId(Event.id) AND A.deleted=0
                                AND A.actionType_id IN (%s) AND A.begDate IS NOT NULL) AS isLeaved'''%(','.join(forceString(leavedId) for leavedId in leavedIdList if leavedId)))
        cond = [ tableActionType['id'].inlist(receivedIdList),
                 tableAction['deleted'].eq(0),
                 tableEvent['deleted'].eq(0),
                 tableActionType['deleted'].eq(0),
                 tableClient['deleted'].eq(0),
                 tableDiagnosis['deleted'].eq(0),
                 tableDiagnostic['deleted'].eq(0),
                 tableAction['endDate'].isNotNull(),
                 tableEventType['deleted'].eq(0),
               ]
        if orgStructureId:
            orgStructureIndex = self.setupDialog.cmbOrgStructure._model.index(self.setupDialog.cmbOrgStructure.currentIndex(), 0, self.setupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            if orgStructureIdList:
                cond.append('''%s'''%(getOrgStructureProperty(u'Направлен в отделение', orgStructureIdList)))
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
            cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(financeId), str(financeId)))
            queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
        cond.append(u'''(EXISTS(SELECT DS.MKB
                        FROM Event AS E
                        INNER JOIN EventType AS ET ON ET.id = E.eventType_id
                        INNER JOIN rbEventTypePurpose AS rbETP ON rbETP.id = ET.purpose_id
                        INNER JOIN Diagnostic AS DC ON DC.event_id = E.id
                        INNER JOIN Diagnosis AS DS ON DC.`diagnosis_id`=DS.`id`
                        INNER JOIN rbDiagnosisType AS rbDT ON DC.`diagnosisType_id`=rbDT.`id`
                        WHERE E.client_id = Client.id
                        AND E.deleted = 0 AND ET.deleted = 0
                        AND rbETP.code = 5 AND (ET.code = 15 OR ET.code = 23)
                        AND (rbDT.code = '4'
                        OR (rbDT.code = '8' AND Diagnostic.person_id = E.execPerson_id
                        AND (NOT EXISTS(SELECT DC2.id FROM Diagnostic AS DC2
                                        INNER JOIN rbDiagnosisType AS DT ON DT.id = DC2.diagnosisType_id WHERE DT.code = '4'
                                        AND DC2.event_id = E.id LIMIT 1))))
                        ORDER BY E.execDate DESC
                        LIMIT 1))
                        OR ((rbDiagnosisType.code = '1' OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
                        AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
                        AND DC.event_id = Event.id LIMIT 1)))) AND (Diagnosis.MKB LIKE 'K%' OR Diagnosis.MKB LIKE 'O%'))''')
        if eventOrder == 2:
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
                        AND A_S.event_id = getFirstEventId(Event.id)
                        AND APT_S.name = 'Доставлен по'
                        AND TRIM(APS_S.value) != ''
                        AND APS_S.value LIKE \'%%экстренным показаниям%%\')''' %((u'''A_S.actionType_id IN (%s) AND ''' % (','.join(str(receivedId) for receivedId in receivedIdList))) if receivedIdList else u'')))
        stmt = db.selectStmt(queryTable, cols, cond)
        query = db.query(stmt)
        while query.next():
            record = query.record()
            eventId = forceRef(record.value('eventId'))
            if eventId and eventId not in eventIdList:
                eventIdList.append(eventId)
                MKBRec = normalizeMKB(forceStringEx(record.value('constDeathMKB')))
                if not MKBRec:
                    MKBRec = normalizeMKB(forceStringEx(record.value('MKB')))
                isDeliverCall = forceBool(record.value('isDeliverCall'))
                isOperation = forceBool(record.value('isOperation'))
                isLeaved = forceBool(record.value('isLeaved'))
                isDeath = forceBool(record.value('isDeath'))
                for row in mapMainRows.get(MKBRec, []):
                    reportLine = reportMainData[row]
                    reportList = reportMainData24[row]
                    reportLine[0] += 1
                    totalLine[0] += 1
                    if isDeliverCall:
                        reportList[0] += 1
                        totalLine24[0] += 1
                    if isDeath:
                        reportLine[1] += 1
                        totalLine[1] += 1
                        if isDeliverCall:
                            reportList[1] += 1
                            totalLine24[1] += 1
                    if isLeaved:
                        if isOperation:
                            reportLine[4] += 1
                            totalLine[4] += 1
                            if isDeath:
                                reportLine[5] += 1
                                totalLine[5] += 1
                            if isDeliverCall:
                                reportList[4] += 1
                                totalLine24[4] += 1
                                if isDeath:
                                    reportList[5] += 1
                                    totalLine24[5] += 1
                        else:
                            reportLine[2] += 1
                            totalLine[2] += 1
                            if isDeath:
                                reportLine[3] += 1
                                totalLine[3] += 1
                            if isDeliverCall:
                                reportList[2] += 1
                                totalLine24[2] += 1
                                if isDeath:
                                    reportList[3] += 1
                                    totalLine24[3] += 1
        return reportMainData, reportMainData24, totalLine, totalLine24


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        orgStructureId = params.get('orgStructureId', None)
        eventOrder = params.get('eventOrder', 0)
        financeId = params.get('financeId', None)
        doc = QtGui.QTextDocument()
        if begDate and endDate:
            rowSize = 6
            mapMainRows = createMapCodeToRowIdx( [row[1] for row in MainRows] )
            reportMainData = [ [0]*rowSize for row in xrange(len(MainRows)) ]
            reportMainData24 = [ [0]*rowSize for row in xrange(len(MainRows)) ]
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'Экстренная хирургическая помощь по 7 нозологиям.')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()

            cols = [('15%', [u'Диагноз',                u'',               u'1'], CReportBase.AlignLeft),
                    ('10%', [u'Код МКБ',                u'',               u'2'], CReportBase.AlignLeft),
                    ('5%',  [u'№ строки',               u'',               u'3'], CReportBase.AlignLeft),
                    ('10%', [u'Сроки доставки в стац.', u'',               u'4'], CReportBase.AlignLeft),
                    ('10%', [u'Доставлено в стационар', u'Всего',          u'5'], CReportBase.AlignLeft),
                    ('10%', [u'',                       u'из них умерло',  u'6'], CReportBase.AlignLeft),
                    ('10%', [u'',                       u'не оперировано', u'7'], CReportBase.AlignLeft),
                    ('10%', [u'',                       u'из них умерло',  u'8'], CReportBase.AlignLeft),
                    ('10%', [u'',                       u'оперировано',    u'9'], CReportBase.AlignLeft),
                    ('10%', [u'',                       u'из них умерло',  u'10'], CReportBase.AlignLeft),
                   ]

            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 2, 1)
            table.mergeCells(0, 1, 2, 1)
            table.mergeCells(0, 2, 2, 1)
            table.mergeCells(0, 3, 2, 1)
            table.mergeCells(0, 4, 1, 6)
            reportMainData, reportMainData24, totalLine, totalLine24 = self.selectData(eventOrder, mapMainRows, reportMainData, reportMainData24, rowSize, orgStructureId, begDate, endDate, financeId)
            for row, rowDescr in enumerate(MainRows):
                reportLine = reportMainData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                table.setText(i, 3, rowDescr[4])
                for col in xrange(rowSize):
                    table.setText(i, 4+col, reportLine[col])
                reportList = reportMainData24[row]
                i = table.addRow()
                table.setText(i, 2, rowDescr[3])
                table.setText(i, 3, rowDescr[5])
                for col in xrange(rowSize):
                    table.setText(i, 4+col, reportList[col])
                table.mergeCells(i-1, 0, 2, 1)
                table.mergeCells(i-1, 1, 2, 1)
            if totalLine or totalLine24:
                i = table.addRow()
                table.setText(i, 0, u'Итого')
                table.setText(i, 2, u'21')
                table.setText(i, 3, u'Всего')
                for col in xrange(rowSize):
                    table.setText(i, 4+col, totalLine[col])
                i = table.addRow()
                table.setText(i, 2, u'22')
                table.setText(i, 3, u'из них позднее 24-х часов')
                for col in xrange(rowSize):
                    table.setText(i, 4+col, totalLine24[col])
                table.mergeCells(i-1, 0, 2, 1)
        return doc
