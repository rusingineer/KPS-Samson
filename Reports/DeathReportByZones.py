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
from PyQt4.QtCore import QDate

from library.Utils      import forceBool, forceInt, forceRef, forceString
from Events.Utils       import getActionTypeIdListByFlatCode
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import getExistsStringPropertyCurrEvent

from Ui_DeathReportByZonesSetup import Ui_DeathReportByZonesSetupDialog


class CDeathReportByZones(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Сведения о летальности по зонам обслуживания')


    def getSetupDialog(self, parent):
        result = CDeathReportByZonesSetupDialog(parent)
        result.setTitle(self.title())
        return result

    def getData(self, params):
        def  getClientSubCond(addrType, addrIdList):
            subcond = [tableClientAddress['client_id'].eqEx('`Client`.`id`'),
                       tableClientAddress['id'].eqEx('(SELECT MAX(`id`) FROM `ClientAddress` AS `CA` WHERE `CA`.`client_id` = `Client`.`id` AND `CA`.`type`=%d)' % addrType)
                      ]
            subcond.append(tableClientAddress['address_id'].inlist(addrIdList))
            return subcond
        orgStructure = {}
        orgStructureTree = {}
        db = QtGui.qApp.db
        begDate   = params.get('begDate', None)
        endDate   = params.get('endDate', None)
        orgStructureIdList = params.get('orgStructureIdList', None)
        tableOS = db.table('OrgStructure')
        tableOSA = db.table('OrgStructure_Address')
        tablePerson = db.table('Person')
        tableClient = db.table('Client')
        tableClientAddress = db.table('ClientAddress')
        tableClientAttach = db.table('ClientAttach')
        tableAddress = db.table('Address')
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableMedicalAidType = db.table('rbMedicalAidType')
        tablePurpose = db.table('rbEventTypePurpose')
        tableAT = db.table('rbAttachType')

        smpCount = 0
        deadCount = 0
        deadEventCount = 0

        #список отделений
        tableParentOS = tableOS.alias('ParentOS')
        table = tableOS.leftJoin(tablePerson, db.joinAnd([tablePerson['orgStructure_id'].eq(tableOS['id']),
                                                          db.joinOr([tablePerson['retireDate'].isNull(),
                                                                     tablePerson['retireDate'].ge(endDate)])
            ]))
        table = table.leftJoin(tableParentOS, tableParentOS['id'].eq(tableOS['parent_id']))

        cols = [
            tableOS['id'],
            tableOS['name'],
            tableParentOS['name'].alias('parentName'),
            "GROUP_CONCAT(CONCAT_WS(' ', Person.lastName, Person.firstName) SEPARATOR '\n') as 'Doctor'"]

        cond = [tableOS['areaType'].eq(1)]

        if orgStructureIdList:
            cond.append(tableOS['id'].inlist(orgStructureIdList))

        stmt = db.selectStmtGroupBy(table, cols, cond, u'OrgStructure.id', u'OrgStructure.code, OrgStructure.name, Person.lastName, Person.firstName')
        query = db.query(stmt)
        while query.next():
            record = query.record()
            id = forceRef(record.value('id'))
            name = forceString(record.value('name'))
            parentName = forceString(record.value('parentName'))
            person = forceString(record.value('Doctor'))
            orgStructure[id] = [name, person, 0, 0, 0, 0]
            idList = orgStructureTree.setdefault(parentName, [])
            idList.append(id)

        #количество клиентов на участке

        tableCA0 = tableClientAddress.alias('CA0')
        tableCA1 = tableClientAddress.alias('CA1')
        tableCA2 = tableClientAddress.alias('CA2')
        tableAddress1 = tableAddress.alias('A1')
        tableAddress2 = tableAddress.alias('A2')
        tableCA = tableClientAttach.alias('CAt')

        cacols = ['MAX(`id`)']
        cacond = [tableCA0['client_id'].eq(tableClient['id'])]
        castmt0 = db.selectStmt(tableCA0, cacols, cacond +[tableCA0['type'].eq(0)])
        castmt1 = db.selectStmt(tableCA0, cacols, cacond +[tableCA0['type'].eq(1)])

        table = tableCA.leftJoin(tableAT, tableAT['id'].eq(tableCA['attachType_id']))
        cols = ['MAX(CAt.id)']
        cond = [
            tableCA['client_id'].eq(tableClient['id']),
            tableCA['deleted'].eq(0),
            tableAT['temporary'].eq(0)]
        CAtStmt = db.selectStmt(table, cols, cond)

        table = tableClient.leftJoin(tableCA1, tableCA1['id'].eqEx('(%s)'%castmt0))
        table = table.leftJoin(tableCA2, tableCA2['id'].eqEx('(%s)'%castmt1))
        table = table.leftJoin(tableAddress1, tableAddress1['id'].eq(tableCA1['address_id']))
        table = table.leftJoin(tableAddress2, tableAddress2['id'].eq(tableCA2['address_id']))
        table = table.leftJoin(tableClientAttach, tableClientAttach['id'].eqEx('(%s)'%CAtStmt))
        table = table.leftJoin(tableOSA, db.joinOr([
            db.joinAnd([tableOSA['house_id'].eq(tableAddress1['house_id']),
                db.joinOr([tableOSA['firstFlat'].eq(0), tableAddress1['flat'].ge(tableOSA['firstFlat'])]),
                db.joinOr([tableOSA['lastFlat'].eq(0), tableAddress1['flat'].le(tableOSA['lastFlat'])])
                ]),
            db.joinAnd([tableOSA['house_id'].eq(tableAddress2['house_id']),
                db.joinOr([tableOSA['firstFlat'].eq(0), tableAddress2['flat'].ge(tableOSA['firstFlat'])]),
                db.joinOr([tableOSA['lastFlat'].eq(0), tableAddress2['flat'].le(tableOSA['lastFlat'])])
                ])
            ]))
        table = table.leftJoin(tableOS, tableOS['id'].eqEx(db.if_(tableClientAttach['orgStructure_id'].isNotNull(),
            tableClientAttach['orgStructure_id'].name(),
            tableOSA['master_id'].name()  )))

        cols = ['COUNT(DISTINCT Client.id)',
                tableOS['id']
               ]

        cond = [tableOS['areaType'].eq(1), tableOS['deleted'].eq(0)]

        stmt = db.selectStmtGroupBy(table, cols, cond, tableOS['id'].name())
        query = db.query(stmt)
        while query.next():
            record = query.record()
            count = forceInt(query.record().value(0))
            id = forceInt(record.value(1))
            if id in orgStructure:
                orgStructure[id][2] = count

        #количество умерших клиентов на участке
        #cond0 = cond[:]
        condDeath = [
            tableClient['deathDate'].ge(begDate),
            tableClient['deathDate'].lt(endDate.addDays(1))]
        #cond0.insert(1, db.joinAnd(condDeath))
        stmt = db.selectStmtGroupBy(table, cols, condDeath, tableOS['id'].name())
        query = db.query(stmt)
        while query.next():
            record = query.record()
            count = forceInt(query.record().value(0))
            id = forceInt(record.value(1))
            if id in orgStructure:
                orgStructure[id][5] = count
            elif not orgStructureIdList:
                deadCount += count

        #количество событий СМП среди пациентов участка
        tableOSA1 = tableOSA.alias('OSA')

        table = tableEvent.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        table = table.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        table = table.leftJoin(tableMedicalAidType, tableMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))
        table = table.leftJoin(tableCA1, tableCA1['id'].eqEx('(%s)'%castmt0))
        table = table.leftJoin(tableCA2, tableCA2['id'].eqEx('(%s)'%castmt1))
        table = table.leftJoin(tableAddress1, tableAddress1['id'].eq(tableCA1['address_id']))
        table = table.leftJoin(tableAddress2, tableAddress2['id'].eq(tableCA2['address_id']))
        table = table.leftJoin(tableClientAttach, tableClientAttach['id'].eqEx('(%s)'%CAtStmt))
        table = table.leftJoin(tableOSA, tableOSA['id'].eqEx(
            '(%s)'%db.selectStmt( tableOSA1, 'MAX(id)',
                db.joinOr([tableOSA1['house_id'].eq(tableAddress1['house_id']),
                tableOSA1['house_id'].eq(tableAddress2['house_id'])])
            )
        ))
        table = table.leftJoin(tableOS, tableOS['id'].eqEx(db.if_(tableClientAttach['orgStructure_id'].isNotNull(),
            tableClientAttach['orgStructure_id'].name(),
            tableOSA['master_id'].name()) ))

        cols = ['count(DISTINCT Event.id)', tableOS['id']]
        condEvent = [db.joinOr([tableMedicalAidType['code'].eq('4'), tableMedicalAidType['code'].eq('5')]),
            tableEvent['execDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1))
            ]

        stmt = db.selectStmtGroupBy(table, cols, condEvent, tableOS['id'].name())
        query = db.query(stmt)
        while query.next():
            record = query.record()
            count = forceInt(query.record().value(0))
            id = forceInt(record.value(1))
            if id in orgStructure:
                orgStructure[id][3] = count
            elif not orgStructureIdList:
                smpCount += count

        #количество событий "Констатация смерти" среди пациентов участка
        table2 = table.leftJoin(tablePurpose, tableEventType['purpose_id'].eq(tablePurpose['id']))
        condEvent = [tablePurpose['code'].eq('5'),
            tableEvent['execDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1))]

        stmt = db.selectStmtGroupBy(table2, cols, condEvent, tableOS['id'].name())
        query = db.query(stmt)
        while query.next():
            record = query.record()
            count = forceInt(query.record().value(0))
            id = forceInt(record.value(1))
            if id in orgStructure:
                orgStructure[id][4] = count
            elif not orgStructureIdList:
                deadEventCount += count

        return orgStructureTree, orgStructure, smpCount, deadCount, deadEventCount


    def build(self, params):

        tableColumns = [
            ('18%', [u'Код участка'],       CReportBase.AlignRight),
            ('18%', [u'Фио врача'],  CReportBase.AlignRight),
            ('16%',[u'Количество прикрепленного населения'],     CReportBase.AlignLeft),
            ('16%',[u'Количество вызовов скорой помощи'],      CReportBase.AlignLeft),
            ('16%',[u'Констатировано смертей'], CReportBase.AlignLeft),
            ('16%',[u'Количество умерших'], CReportBase.AlignLeft)
            ]

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        table = createTable(cursor, tableColumns)
        dataTree, data, smpCount, deadCount, deadEventCount = self.getData(params)
        sumRow = [0, 0, 0, 0]
        for parentName in sorted(dataTree.keys()):
            localSum = [0, 0, 0, 0]
            i = table.addRow()
            table.setText(i, 0, parentName, CReportBase.ReportSubTitle, CReportBase.AlignLeft)
            table.mergeCells(i, 0, 1, 6)
            for id in dataTree[parentName]:
                i = table.addRow()
                for col, colText in enumerate(data[id]):
                    table.setText(i, col, colText)
                    if col >= 2:
                        sumRow[col-2] += colText
                        localSum[col-2] += colText
            i = table.addRow()
            table.mergeCells(i, 0, 1, 2)
            for col in xrange(4):
                table.setText(i, col+2, localSum[col])
        if smpCount or deadCount or deadEventCount:
            i = table.addRow()
            table.setText(i, 0, u'Прочее:')
            table.setText(i, 3, smpCount)
            table.setText(i, 4, deadEventCount)
            table.setText(i, 5, deadCount)
            sumRow[1] += smpCount
            sumRow[2] += deadEventCount
            sumRow[3] += deadCount
        i = table.addRow()
        table.setText(i, 0, u'Итого:', CReportBase.ReportSubTitle, CReportBase.AlignLeft)
        table.mergeCells(i, 0, 1, 2)
        for col in xrange(4):
            table.setText(i, col+2, sumRow[col], CReportBase.ReportSubTitle)
        return doc


class CDetailedDeathReportByZones(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Детализированная летальность по зонам')
        self.setLineWrapMode(QtGui.QTextEdit.NoWrap)


    def getSetupDialog(self, parent):
        result = CDeathReportByZonesSetupDialog(parent)
        result.setTitle(self.title())
        return result

    def getData(self, params, len_tableColumns):
        orgStructureLine = [0]*(len_tableColumns+1)
        orgStructureLine[0] = u'Базовое ЛПУ'
        orgStructure = {0:orgStructureLine}
        orgStructureTree = {u'':[(0, u'Базовое ЛПУ')]}
        db = QtGui.qApp.db
        begDate   = params.get('begDate', None)
        endDate   = params.get('endDate', None)
        orgStructureIdList = params.get('orgStructureIdList', None)
        tableOS = db.table('OrgStructure')
        tableOSA = db.table('OrgStructure_Address')
        tablePerson = db.table('Person')
        tableClient = db.table('Client')
        tableClientAddress = db.table('ClientAddress')
        tableClientAttach = db.table('ClientAttach')
        tableAddress = db.table('Address')
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableDiagnostic = db.table('Diagnostic')
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnosisType = db.table('rbDiagnosisType')
        tableAT = db.table('rbAttachType')

        #dispanser
        dispanserIdList = []
        tableDispanser = db.table('rbDispanser')
        recordDispanserList = db.getRecordList(tableDispanser)
        for recordDispanser in recordDispanserList:
            id = forceRef(recordDispanser.value('id'))
            observed = forceRef(recordDispanser.value('observed'))
            if observed:
                dispanserIdList.append(id)

        #список отделений
        tableParentOS = tableOS.alias('ParentOS')
        table = tableOS.leftJoin(tablePerson, tablePerson['orgStructure_id'].eq(tableOS['id']))
        table = table.leftJoin(tableParentOS, tableParentOS['id'].eq(tableOS['parent_id']))
        cols = [
            tableOS['id'],
            tableOS['name'],
            tableParentOS['name'].alias('parentName'),
            u'''GROUP_CONCAT(CONCAT_WS(' ', Person.lastName, Person.firstName) SEPARATOR '\n') AS 'Doctor' ''']

        cond = [tableOS['areaType'].eq(1),
                db.joinOr([tablePerson['retireDate'].isNull(),
                           tablePerson['retireDate'].ge(endDate)])]
        if orgStructureIdList:
            cond.append(tableOS['id'].inlist(orgStructureIdList))
        stmt = db.selectStmtGroupBy(table, cols, cond, [tableOS['id'].name(), u'CAST(OrgStructure.name AS SIGNED)', u"'Doctor'" , u'parentName'])
        query = db.query(stmt)
        while query.next():
            record = query.record()
            id = forceInt(record.value('id'))
            name = forceString(record.value('name'))
            parentName = forceString(record.value('parentName'))
            orgStructure[id] = [0]*(len_tableColumns+1)
            orgStructure[id][0] = name
            idList = orgStructureTree.setdefault(parentName, [])
            idList.append((id, name))

        #количество клиентов на участке
        tableCA0 = tableClientAddress.alias('CA0')
        tableCA1 = tableClientAddress.alias('CA1')
        tableCA2 = tableClientAddress.alias('CA2')
        tableAddress1 = tableAddress.alias('A1')
        tableAddress2 = tableAddress.alias('A2')
        tableCA = tableClientAttach.alias('CAt')

        cacols = [u'MAX(`id`)']
        cacond = [tableCA0['client_id'].eq(tableClient['id'])]
        castmt0 = db.selectStmt(tableCA0, cacols, cacond +[tableCA0['type'].eq(0)])
        castmt1 = db.selectStmt(tableCA0, cacols, cacond +[tableCA0['type'].eq(1)])

        table = tableCA.leftJoin(tableAT, tableAT['id'].eq(tableCA['attachType_id']))
        cols = [u'MAX(CAt.id)']
        cond = [
            tableCA['client_id'].eq(tableClient['id']),
            tableCA['deleted'].eq(0),
            tableAT['temporary'].eq(0)]
        CAtStmt = db.selectStmt(table, cols, cond)

        table = tableClient.leftJoin(tableCA1, tableCA1['id'].eqEx('(%s)'%castmt0))
        table = table.leftJoin(tableCA2, tableCA2['id'].eqEx('(%s)'%castmt1))
        table = table.leftJoin(tableAddress1, tableAddress1['id'].eq(tableCA1['address_id']))
        table = table.leftJoin(tableAddress2, tableAddress2['id'].eq(tableCA2['address_id']))
        table = table.leftJoin(tableClientAttach, tableClientAttach['id'].eqEx('(%s)'%CAtStmt))
        table = table.leftJoin(tableOSA, db.joinOr([
            db.joinAnd([tableOSA['house_id'].eq(tableAddress1['house_id']),
                db.joinOr([tableOSA['firstFlat'].eq(0), tableAddress1['flat'].ge(tableOSA['firstFlat'])]),
                db.joinOr([tableOSA['lastFlat'].eq(0), tableAddress1['flat'].le(tableOSA['lastFlat'])])
                ]),
            db.joinAnd([tableOSA['house_id'].eq(tableAddress2['house_id']),
                db.joinOr([tableOSA['firstFlat'].eq(0), tableAddress2['flat'].ge(tableOSA['firstFlat'])]),
                db.joinOr([tableOSA['lastFlat'].eq(0), tableAddress2['flat'].le(tableOSA['lastFlat'])])
                ])
            ]))
#        table = table.leftJoin(tableOS, tableOS['id'].eqEx(db.if_(tableClientAttach['orgStructure_id'].isNotNull(),
#            tableClientAttach['orgStructure_id'].name(),
#            tableOSA['master_id'].name()  )))
        table = table.leftJoin(tableOS, tableOS['id'].eq(tableClientAttach['orgStructure_id']))
        cols = [u'COUNT(DISTINCT Client.id)',
                tableOS['id'],
                tableOS['name'],
                tableClientAttach['LPU_id'],
                tableClientAttach['orgStructure_id'],
                '''(SELECT RAT.temporary
                    FROM rbAttachType AS RAT
                    WHERE RAT.id = ClientAttach.attachType_id
                    LIMIT 1) AS temporary''']

        cond = [db.joinOr([db.joinAnd([tableOS['areaType'].eq(1), tableOS['deleted'].eq(0)]), tableOS['deleted'].isNull()]),
                tableClientAttach['id'].isNotNull()]
        if orgStructureIdList:
            cond.append(tableOS['id'].inlist(orgStructureIdList))

        stmt = db.selectStmtGroupBy(table, cols, cond,
                                   [tableOS['id'].name(), u'CAST(OrgStructure.name AS SIGNED)', u'ClientAttach.LPU_id',
                                    u'ClientAttach.orgStructure_id', u'temporary'])
        query = db.query(stmt)
        while query.next():
            record = query.record()
            count = forceInt(query.record().value(0))
            id = forceInt(record.value(1))
            name = forceString(record.value('name'))
            LPUId = forceRef(record.value('LPU_id'))
            orgStructureIdAT = forceRef(record.value('orgStructure_id'))
            temporary = forceBool(record.value('temporary'))
            if id in orgStructure:
                orgStructure[id][1] += count
            if LPUId == QtGui.qApp.currentOrgId() and not orgStructureIdAT and temporary == 0:
                if id not in orgStructure.keys():
                    orgStructure[id] = [0]*(len_tableColumns+1)
                    orgStructure[id][0] = name
                orgStructure[id][len_tableColumns] = 1

        #количество умерших клиентов на участке
        #cond0 = cond[:]
        condDeath = [
            tableClient['deathDate'].ge(begDate),
            tableClient['deathDate'].lt(endDate.addDays(1)),
            tableEventType['form'].like(u'106'),
            tableEventType['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableDiagnosis['deleted'].eq(0),
            tableDiagnostic['deleted'].eq(0)
            ]
        #cond0.insert(1, db.joinAnd(condDeath))
        table = table.leftJoin(tableEvent, tableEvent['client_id'].eq(tableClient['id']))
        table = table.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        table = table.leftJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
        table = table.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
        table = table.leftJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id']))
        cols = [u'COUNT(DISTINCT Client.id)',
                tableOS['id'],
                tableOS['name']]
        cols.append(tableDiagnosis['MKB'])
        actionTypeIdList = getActionTypeIdListByFlatCode('deathCurcumstance')
        if actionTypeIdList:
            cols.append(getExistsStringPropertyCurrEvent(actionTypeIdList, u'Смерть последовала%%', u'дом%%') + u' AS isHome')
        else:
            cols.append(u'0 AS isHome')
        condDeath.append('''(rbDiagnosisType.code = '4'
OR (rbDiagnosisType.code = '8' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '4'
AND DC.event_id = Event.id))))''')
        stmt = db.selectStmtGroupBy(table, cols, condDeath, [tableOS['id'].name(), u'CAST(OrgStructure.name AS SIGNED)', tableDiagnosis['MKB'].name(), u'isHome'])
        query = db.query(stmt)
        while query.next():
            record = query.record()
            mkb = forceString(record.value('MKB'))
            isHome = forceBool(record.value('isHome'))
            count = forceInt(query.record().value(0))
            id = forceInt(record.value('id'))
            if id in orgStructure:
                if mkb >= u'A15' and mkb <= u'A19.9':
                    orgStructure[id][2] += count
                    if isHome:
                        orgStructure[id][3] += count
                elif mkb >= u'C00' and mkb <= u'C97.0':
                    orgStructure[id][7] += count
                    if isHome:
                        orgStructure[id][8] += count
                elif mkb >= u'E10.0' and mkb <= u'E14.9':
                    orgStructure[id][12] += count
                    if isHome:
                        orgStructure[id][13] += count
                elif mkb >= u'I60.0' and mkb <= u'I69.9':
                    orgStructure[id][19] += count
                    if isHome:
                        orgStructure[id][20] += count
                    if mkb >= u'I60.0' and mkb <= u'I64.9':
                        orgStructure[id][24] += count
                        if isHome:
                            orgStructure[id][25] += count
                elif mkb >= u'I10' and mkb <= u'I15.9':
                    orgStructure[id][30] += count
                    if isHome:
                        orgStructure[id][31] += count
                elif mkb >= u'I20' and mkb <= u'I25.9':
                    orgStructure[id][37] += count
                    if isHome:
                        orgStructure[id][38] += count
                    if mkb >= u'I21' and mkb <= u'I21.9':
                        orgStructure[id][45] += count
                        if isHome:
                            orgStructure[id][46] += count
                    if mkb >= u'I22' and mkb <= u'I22.9':
                        orgStructure[id][51] += count
                        if isHome:
                            orgStructure[id][52] += count
                elif mkb >= u'J00' and mkb <= u'J99.8':
                    orgStructure[id][57] += count
                    if isHome:
                        orgStructure[id][58] += count
                    if (mkb >= u'J12' and mkb <= u'J18.9') or mkb == u'J11.0':
                        orgStructure[id][62] += count
                        if isHome:
                            orgStructure[id][63] += count
                    if mkb >= u'J40' and mkb <= u'J47.9':
                        orgStructure[id][68] += count
                        if isHome:
                            orgStructure[id][69] += count
                elif mkb >= u'K00' and mkb <= u'K93.8':
                    orgStructure[id][76] += count
                    if isHome:
                        orgStructure[id][77] += count
                elif mkb >= u'A00' and mkb <= u'T98.9':
                    orgStructure[id][81] += count
                    if isHome:
                        orgStructure[id][82] += count

        #количество событий СМП среди пациентов участка
#        table = tableEvent.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
#        table = table.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
#        table = table.leftJoin(tableClientAddress, tableClientAddress['id'].eq('''(IF(getClientLocAddressId(Client.id), getClientLocAddressId(Client.id),  getClientRegAddressId(Client.id)))'''))
##        table = table.leftJoin(tableClientAddress, u'''ClientAddress.id = (IF(getClientLocAddressId(Client.id), getClientLocAddressId(Client.id),  getClientRegAddressId(Client.id)))''')
#        table = table.leftJoin(tableAddress, tableAddress['id'].eq(tableClientAddress['address_id']))
#        table = table.leftJoin(tableOSA, tableOSA['house_id'].eq(tableAddress['house_id']))
#        table = table.leftJoin(tableClientAttach, tableClientAttach['id'].eq('''getClientAttachIdForDate(Client.id, 0, DATE('%s'))'''%(db.formatDate(endDate))))
##        table = table.leftJoin(tableClientAttach, u'''ClientAttach.id = getClientAttachIdForDate(Client.id, 0, DATE('%s'))'''%(db.formatDate(endDate)))
#        table = table.leftJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
#        table = table.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
#        table = table.leftJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id']))
#        table = table.leftJoin(tableOS, db.joinOr([tableOSA['master_id'].eq(tableOS['id']),
#                                                   db.joinAnd([tableClientAttach['orgStructure_id'].eq(tableOS['id']),
#                                                               tableOS['areaType'].eq(1)])]))
#        table1 = table.leftJoin(tableMedicalAidType, tableMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))
#        table1 = table1.leftJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnosis['dispanser_id']))
#
##        tableDisp = tableDiagnosis.leftJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnosis['dispanser_id']))
##        condDisp = [tableDiagnosis['client_id'].eq(tableClient['id']),
##                    tableDispanser['observed'].inlist([1, 2, 6])]
##        dispanserStmt = db.existsStmt(tableDisp, condDisp)

#        cols = [u'count(DISTINCT Event.id)',
#                tableDiagnosis['MKB'],
#                tableDispanser['code'].alias('isDispanser'),
#                tableEvent['client_id'],
#                tableEvent['order'],
#                'IF(Event.isPrimary = 3, 1, 0) AS isActiv',
#                tableOS['id'].alias('orgStructureId'),
#                tableOS['name'],
#                u'''(SELECT ParentOS.name
#                FROM OrgStructure AS ParentOS
#                WHERE ParentOS.id = OrgStructure.parent_id AND ParentOS.deleted = 0) AS parentName''',
#                u'''(SELECT GROUP_CONCAT(CONCAT_WS(' ', Person.lastName, Person.firstName) SEPARATOR '\n')
#                FROM Person
#                WHERE Person.orgStructure_id = OrgStructure.id
#                AND ((Person.retireDate IS NULL) OR (DATE(Person.retireDate)>=DATE(%s)))) AS Doctor'''%(db.formatDate(begDate)),
#                u'''IF(rbMedicalAidType.code IN (4,5), 1, 0) AS emergCall''',
#                u'''IF(rbMedicalAidType.code IN (4,5), 0, 1) AS notEmergCall''',
#                u'''EXISTS(SELECT rbScene.id
#                FROM rbScene INNER JOIN Visit ON Visit.scene_id = rbScene.id
#                WHERE rbScene.appointmentType = 2
#                AND Visit.event_id = Event.id AND Visit.deleted = 0) AS isHome''',
#                u'''EXISTS(SELECT R.id
#                FROM rbResult AS R INNER JOIN rbEventTypePurpose AS ETP ON ETP.id = R.eventPurpose_id
#                WHERE R.id = Event.result_id AND ETP.code = '7' AND R.code = '07') AS isHospitalizir'''
#                ]
#        houseStmt = db.selectStmt(tableOSA, tableOSA['house_id'], [tableOSA['master_id'].eq(tableOS['id'])])
        cond1 = []
        if orgStructureIdList:
            cond1.append(tableOS['id'].inlist(orgStructureIdList))
        condEvent = [
                     tableEvent['execDate'].ge(begDate),
                     tableEvent['execDate'].lt(endDate.addDays(1))
                    ]
        cond1.insert(1, db.joinAnd(condEvent))
        cond1.append('''(rbDiagnosisType.code = '1'
OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
AND DC.event_id = Event.id))))''')
#        stmt = db.selectStmtGroupBy(table1, cols, cond1, ','.join([u'orgStructureId', u'CAST(OrgStructure.name AS SIGNED)',
#            tableDiagnosis['MKB'].name(), tableEvent['order'].name(), u'isDispanser', tableEvent['client_id'].name(), u'isActiv',
#            u'parentName', u'Doctor', u'emergCall', u'notEmergCall', u'isHome', u'isHospitalizir']))

        stmt = u'''
        SELECT COUNT(DISTINCT Event.id), Diagnosis.`MKB`, rbDispanser.`code` AS `isDispanser`,
Event.`client_id`, Event.`order`, IF(Event.isPrimary = 3, 1, 0) AS isActiv,
OrgStructure.`id` AS `orgStructureId`, OrgStructure.`name`,
(SELECT ParentOS.name
                FROM OrgStructure AS ParentOS
                WHERE ParentOS.id = OrgStructure.parent_id AND ParentOS.deleted = 0) AS parentName,
(SELECT GROUP_CONCAT(CONCAT_WS(' ', Person.lastName, Person.firstName) SEPARATOR '')
                FROM Person
                WHERE Person.orgStructure_id = OrgStructure.id
                AND ((Person.retireDate IS NULL) OR (DATE(Person.retireDate)>=DATE(%s)))) AS Doctor,
IF(rbMedicalAidType.code IN (4,5), 1, 0) AS emergCall,
IF(rbMedicalAidType.code IN (4,5), 0, 1) AS notEmergCall,
EXISTS(SELECT rbScene.id
                FROM rbScene INNER JOIN Visit ON Visit.scene_id = rbScene.id
                WHERE rbScene.appointmentType = 2
                AND Visit.event_id = Event.id AND Visit.deleted = 0) AS isHome,
EXISTS(SELECT R.id
                FROM rbResult AS R INNER JOIN rbEventTypePurpose AS ETP ON ETP.id = R.eventPurpose_id
                WHERE R.id = Event.result_id AND ETP.code = '7' AND R.code = '07') AS isHospitalizir
        FROM Event
LEFT JOIN Client ON Event.`client_id`=Client.`id`
LEFT JOIN EventType ON EventType.`id`=Event.`eventType_id`
LEFT JOIN ClientAddress ON ClientAddress.`id`= (IF(getClientLocAddressId(Client.id), getClientLocAddressId(Client.id),  getClientRegAddressId(Client.id)))
LEFT JOIN Address ON Address.`id`=ClientAddress.`address_id`
LEFT JOIN OrgStructure_Address ON OrgStructure_Address.`house_id`=Address.`house_id`
LEFT JOIN ClientAttach ON ClientAttach.`id`= getClientAttachIdForDate(Client.id, 0, DATE(%s))
LEFT JOIN Diagnostic ON Diagnostic.`event_id`=Event.`id`
LEFT JOIN Diagnosis ON Diagnosis.`id`=Diagnostic.`diagnosis_id`
LEFT JOIN rbDiagnosisType ON rbDiagnosisType.`id`=Diagnostic.`diagnosisType_id`
LEFT JOIN OrgStructure ON ((OrgStructure_Address.`master_id`=OrgStructure.`id`)
                           OR ((ClientAttach.`orgStructure_id`=OrgStructure.`id`) AND (OrgStructure.`areaType`=1)))
LEFT JOIN rbMedicalAidType ON rbMedicalAidType.`id`=EventType.`medicalAidType_id`
LEFT JOIN rbDispanser ON rbDispanser.`id`=Diagnosis.`dispanser_id`
        WHERE %s
        GROUP BY orgStructureId, CAST(OrgStructure.name AS SIGNED), Diagnosis.`MKB`, Event.`order`,
        isDispanser, Event.`client_id`, isActiv, parentName, Doctor, emergCall, notEmergCall, isHome, isHospitalizir
        '''%(db.formatDate(begDate), db.formatDate(endDate), db.joinAnd(cond1))
        clientToMKBDict = {}
        query = db.query(stmt)
        while query.next():
            record = query.record()
            count           = forceInt(query.record().value(0))
            mkb             = forceString(record.value('MKB'))
            clientId        = forceRef(record.value('client_id'))
            id              = forceInt(record.value('orgStructureId'))
            order           = forceInt(record.value('order'))
            isActiv         = forceBool(record.value('isActiv'))
            isDispanser     = forceString(record.value('isDispanser'))
            emergCall       = forceBool(record.value('emergCall'))
            notEmergCall    = forceBool(record.value('notEmergCall'))
            isHome          = forceBool(record.value('isHome'))
            isHospitalizir = forceBool(record.value('isHospitalizir'))
            orgStructureSum = orgStructure.get(id, None)
            if not orgStructureSum:
                parentName = forceString(record.value('parentName'))
                name = forceString(record.value('name'))
                orgStructureSum = [0]*(len_tableColumns+1)
                orgStructureSum[0] = name
                idList = orgStructureTree.setdefault(parentName, [])
                idList.append((id, name))
            if mkb >= u'A15' and mkb <= u'A19.9':
                if emergCall:
                    orgStructureSum[4] += count
                    if isDispanser in [u'1', u'2', u'6']:
                        orgStructureSum[5] += count
#                if order == 6:
#                    orgStructureSum[6] += count
            elif mkb >= u'C00' and mkb <= u'C97.0':
                if emergCall:
                    orgStructureSum[9] += count
                    if isDispanser in [u'1', u'2', u'6']:
                        orgStructureSum[10] += count
#                if order == 6:
#                    orgStructureSum[11] += count
            elif mkb >= u'E10.0' and mkb <= u'E14.9':
                if emergCall:
                    orgStructureSum[14] += count
                    if isDispanser in [u'1', u'2', u'6']:
                        orgStructureSum[15] += count
                if notEmergCall and isDispanser in [u'1', u'2', u'6'] and (isActiv or isHome):
                    orgStructureSum[18] += count
#                if order == 6:
#                    orgStructureSum[16] += count
                if isDispanser in [u'2', u'6']:
                    clientToMKBLine = clientToMKBDict.setdefault(clientId, [])
                    if mkb not in clientToMKBLine:
                        clientToMKBLine.append(mkb)
                        orgStructureSum[17] += count
            elif mkb >= u'I60.0' and mkb <= u'I69.9':
                if emergCall:
                    orgStructureSum[21] += count
                    if isDispanser in [u'1', u'2', u'6']:
                        orgStructureSum[22] += count
#                if order == 6:
#                    orgStructureSum[23] += count
                if mkb >= u'I60.0' and mkb <= u'I64.9':
                    if emergCall:
                        orgStructureSum[26] += count
                        if isDispanser in [u'1', u'2', u'6']:
                            orgStructureSum[27] += count
#                    if order == 6:
#                        orgStructureSum[28] += count
                        if order == 2 and isHospitalizir:
                            orgStructureSum[29] += count
            elif mkb >= u'I10' and mkb <= u'I15.9':
                if emergCall:
                    orgStructureSum[32] += count
                    if isDispanser in [u'1', u'2', u'6']:
                        orgStructureSum[33] += count
                if notEmergCall and isDispanser in [u'1', u'2', u'6'] and (isActiv or isHome):
                    orgStructureSum[36] += count
#                if order == 6:
#                    orgStructureSum[34] += count
                if isDispanser in [u'2', u'6']:
                    clientToMKBLine = clientToMKBDict.setdefault(clientId, [])
                    if mkb not in clientToMKBLine:
                        clientToMKBLine.append(mkb)
                        orgStructureSum[35] += count
            elif mkb >= u'I20' and mkb <= u'I25.9':
                if emergCall:
                    orgStructureSum[39] += count
                    if isDispanser in [u'1', u'2', u'6']:
                        orgStructureSum[40] += count
                    if order == 2 and isHospitalizir:
                        orgStructureSum[44] += count
                if notEmergCall and isDispanser in [u'1', u'2', u'6'] and (isActiv or isHome):
                    orgStructureSum[43] += count
#                if order == 6:
#                    orgStructureSum[41] += count
                if isDispanser in [u'2', u'6']:
                    clientToMKBLine = clientToMKBDict.setdefault(clientId, [])
                    if mkb not in clientToMKBLine:
                        clientToMKBLine.append(mkb)
                        orgStructureSum[42] += count
                if mkb >= u'I21' and mkb <= u'I21.9':
                    if emergCall:
                        orgStructureSum[47] += count
                        if isDispanser in [u'1', u'2', u'6']:
                            orgStructureSum[48] += count
#                    if order == 6:
#                        orgStructureSum[49] += count
                        if order == 2 and isHospitalizir:
                            orgStructureSum[50] += count
                if mkb >= u'I22' and mkb <= u'I22.9':
                    if emergCall:
                        orgStructureSum[53] += count
                        if isDispanser in [u'1', u'2', u'6']:
                            orgStructureSum[54] += count
#                    if order == 6:
#                        orgStructureSum[55] += count
                        if order == 2 and isHospitalizir:
                            orgStructureSum[56] += count
            elif mkb >= u'J00' and mkb <= u'J99.8':
                if emergCall:
                    orgStructureSum[59] += count
                    if isDispanser in [u'1', u'2', u'6']:
                        orgStructureSum[60] += count
#                if order == 6:
#                    orgStructureSum[61] += count
                if (mkb >= u'J12' and mkb <= u'J18.9') or mkb == u'J11.0':
                    if emergCall:
                        orgStructureSum[64] += count
                        if isDispanser in [u'1', u'2', u'6']:
                            orgStructureSum[65] += count
#                    if order == 6:
#                        orgStructureSum[66] += count
                    if order == 2:
                        orgStructureSum[67] += count
                if mkb >= u'J40' and mkb <= u'J47.9':
                    if emergCall:
                        orgStructureSum[70] += count
                        if isDispanser in [u'1', u'2', u'6']:
                            orgStructureSum[71] += count
                    if notEmergCall and isDispanser in [u'1', u'2', u'6'] and (isActiv or isHome):
                        orgStructureSum[74] += count
#                    if order == 6:
#                        orgStructureSum[72] += count
                    if isDispanser in [u'2', u'6']:
                        clientToMKBLine = clientToMKBDict.setdefault(clientId, [])
                        if mkb not in clientToMKBLine:
                            clientToMKBLine.append(mkb)
                            orgStructureSum[73] += count
                    if order == 2:
                        orgStructureSum[75] += count
            elif mkb >= u'K00' and mkb <= u'K93.8':
                if emergCall:
                    orgStructureSum[78] += count
                    if isDispanser in [u'1', u'2', u'6']:
                        orgStructureSum[79] += count
#                if order == 6:
#                    orgStructureSum[80] += count
            elif mkb >= u'A00' and mkb <= u'T98.9':
                if emergCall:
                    orgStructureSum[83] += count
                    if isDispanser in [u'1', u'2', u'6']:
                        orgStructureSum[84] += count
#                if order == 6:
#                    orgStructureSum[85] += count
            orgStructure[id] = orgStructureSum
        return orgStructureTree, orgStructure


    def build(self, params):
        tableColumns = [
            ('5%', [u'Терапевтический участок',                               u'',                                                        u'',                                                                                u'1'], CReportBase.AlignRight),
            ('1%', [u'Количество прикрепленного населения',                   u'',                                                        u'',                                                                                u'2'], CReportBase.AlignRight),
            ('1%',[u'Туберкулез (А15.0-А19.9)',                               u'Количество умерших за отчетный период  (за месяц), чел.', u'Всего',                                                                           u'3'], CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'в том числе на дому',                                                             u'4'], CReportBase.AlignRight),
            ('1%',[u'',                                                       u'Количество вызовов скорой помощи на участке',             u'Всего',                                                                           u'5'], CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'В том числе к лицам, состоящим под диспансерным наблюдением',                     u'6'], CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество вызовов неотложной медицинской помощи',                                u'7'], CReportBase.AlignRight),

            ('1%',[u'Онкологические заболевания (С00.0-С97.0)',               u'Количество умерших за отчетный период  (за месяц), чел.', u'Всего',                                                                           u'8'], CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'в том числе на дому',                                                             u'9'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'Количество вызовов скорой помощи на участке',             u'Всего',                                                                           u'10'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'В том числе к лицам, состоящим под диспансерным наблюдением',                     u'11'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество вызовов неотложной медицинской помощи',                                u'12'],CReportBase.AlignRight),

            ('1%',[u'Сахарный диабет (Е10.0-Е14.9)',                          u'Количество умерших за отчетный период  (за месяц), чел.', u'Всего',                                                                           u'13'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'в том числе на дому',                                                             u'14'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'Количество вызовов скорой помощи на участке',             u'Всего',                                                                           u'15'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'В том числе к лицам, состоящим под диспансерным наблюдением',                     u'16'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество вызовов неотложной медицинской помощи',                                u'17'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Число пациентов, взятых на диспансерное наблюдение',                              u'18'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество активных посещений пациентов, состоящих под диспансерным наблюдением', u'19'],CReportBase.AlignRight),

            ('1%',[u'Цереброваскулярные болезни (I60.0-I69.9)',               u'Количество умерших за отчетный период  (за месяц), чел.', u'Всего',                                                                           u'20'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'в том числе на дому',                                                             u'21'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'Количество вызовов скорой помощи на участке',             u'Всего',                                                                           u'22'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'В том числе к лицам, состоящим под диспансерным наблюдением',                     u'23'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество вызовов неотложной медицинской помощи',                                u'24'],CReportBase.AlignRight),

            ('1%',[u'из них: ОНМК (I60.0-I64)',                               u'Количество умерших за отчетный период  (за месяц), чел.', u'Всего',                                                                           u'25'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'в том числе на дому',                                                             u'26'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'Количество вызовов скорой помощи на участке',             u'Всего',                                                                           u'27'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'В том числе к лицам, состоящим под диспансерным наблюдением',                     u'28'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество вызовов неотложной медицинской помощи',                                u'29'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Число пациентов, госпитализированных по экстренным показаниям',                   u'30'],CReportBase.AlignRight),

            ('1%',[u'Гипертоническая болезнь (I10-I15.9)',                    u'Количество умерших за отчетный период  (за месяц), чел.', u'Всего',                                                                           u'31'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'в том числе на дому',                                                             u'32'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'Количество вызовов скорой помощи на участке',             u'Всего',                                                                           u'33'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'В том числе к лицам, состоящим под диспансерным наблюдением',                     u'34'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество вызовов неотложной медицинской помощи',                                u'35'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Число пациентов, взятых на диспансерное наблюдение',                              u'36'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество активных посещений пациентов, состоящих под диспансерным наблюдением', u'37'],CReportBase.AlignRight),

            ('1%',[u'Ишемическая болезнь сердца (I20.0-I25.9)',               u'Количество умерших за отчетный период  (за месяц), чел.', u'Всего',                                                                           u'38'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'в том числе на дому',                                                             u'39'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'Количество вызовов скорой помощи на участке',             u'Всего',                                                                           u'40'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'В том числе к лицам, состоящим под диспансерным наблюдением',                     u'41'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество вызовов неотложной медицинской помощи',                                u'42'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Число пациентов, взятых на диспансерное наблюдение',                              u'43'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество активных посещений пациентов, состоящих под диспансерным наблюдением', u'44'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Число пациентов, госпитализированных по экстренным показаниям',                   u'45'],CReportBase.AlignRight),

            ('1%',[u'из них: острый инфаркт миокарда (I21.0-I21.9)',          u'Количество умерших за отчетный период  (за месяц), чел.', u'Всего',                                                                           u'46'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'в том числе на дому',                                                             u'47'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'Количество вызовов скорой помощи на участке',             u'Всего',                                                                           u'48'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'В том числе к лицам, состоящим под диспансерным наблюдением',                     u'49'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество вызовов неотложной медицинской помощи',                                u'50'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Число пациентов, госпитализированных по экстренным показаниям',                   u'51'],CReportBase.AlignRight),

            ('1%',[u'повторный инфаркт миокарда (i22.0-I22.9)',               u'Количество умерших за отчетный период  (за месяц), чел.', u'Всего',                                                                           u'52'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'в том числе на дому',                                                             u'53'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'Количество вызовов скорой помощи на участке',             u'Всего',                                                                           u'54'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'В том числе к лицам, состоящим под диспансерным наблюдением',                     u'55'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество вызовов неотложной медицинской помощи',                                u'56'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Число пациентов, госпитализированных по экстренным показаниям',                   u'57'],CReportBase.AlignRight),

            ('1%',[u'Болезни органов дыхания (J00-J99.8)',                    u'Количество умерших за отчетный период  (за месяц), чел.', u'Всего',                                                                           u'58'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'в том числе на дому',                                                             u'59'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'Количество вызовов скорой помощи на участке',             u'Всего',                                                                           u'60'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'В том числе к лицам, состоящим под диспансерным наблюдением',                     u'61'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество вызовов неотложной медицинской помощи',                                u'62'],CReportBase.AlignRight),

            ('1%',[u'из них: пневмонии (J11.0, J12.0-J18.9)',                 u'Количество умерших за отчетный период  (за месяц), чел.', u'Всего',                                                                           u'63'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'в том числе на дому',                                                             u'64'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'Количество вызовов скорой помощи на участке',             u'Всего',                                                                           u'65'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'В том числе к лицам, состоящим под диспансерным наблюдением',                     u'66'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество вызовов неотложной медицинской помощи',                                u'67'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Число пациентов, госпитализированных по экстренным показаниям',                   u'68'],CReportBase.AlignRight),

            ('1%',[u'хронические болезни нижних дыхательных путей (J40-J47)', u'Количество умерших за отчетный период  (за месяц), чел.', u'Всего',                                                                           u'69'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'в том числе на дому',                                                             u'70'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'Количество вызовов скорой помощи на участке',             u'Всего',                                                                           u'71'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'В том числе к лицам, состоящим под диспансерным наблюдением',                     u'72'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество вызовов неотложной медицинской помощи',                                u'73'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Число пациентов, взятых на диспансерное наблюдение',                              u'74'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество активных посещений пациентов, состоящих под диспансерным наблюдением', u'75'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Число пациентов, госпитализированных по экстренным показаниям',                   u'76'],CReportBase.AlignRight),

            ('1%',[u'Болезни органов пищеварения (К00.0-К93.8)',              u'Количество умерших за отчетный период  (за месяц), чел.', u'Всего',                                                                           u'77'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'в том числе на дому',                                                             u'78'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'Количество вызовов скорой помощи на участке',             u'Всего',                                                                           u'79'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'В том числе к лицам, состоящим под диспансерным наблюдением',                     u'80'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество вызовов неотложной медицинской помощи',                                u'81'],CReportBase.AlignRight),

            ('1%',[u'Прочие (A00-T98 с за исключением выше представленных)',  u'Количество умерших за отчетный период  (за месяц), чел.', u'Всего',                                                                           u'82'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'в том числе на дому',                                                             u'83'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'Количество вызовов скорой помощи на участке',             u'Всего',                                                                           u'84'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'В том числе к лицам, состоящим под диспансерным наблюдением',                     u'85'],CReportBase.AlignRight),
            ('1%',[u'',                                                       u'',                                                        u'Количество вызовов неотложной медицинской помощи',                                u'86'],CReportBase.AlignRight),

            ('1%',[u'Число пациентов, находящихся на диспансерном наблюдении, из числа жителей участка, достигших стабильных целевых значений показателей', u'Артериальное давление', u'',                                    u'87'],CReportBase.AlignRight),
            ('1%',[u'',                                                                                                                                     u'Липидный спектр',       u'',                                    u'88'],CReportBase.AlignRight),
            ('1%',[u'',                                                                                                                                     u'Глюкоза крови',         u'',                                    u'89'],CReportBase.AlignRight),
            ('1%',[u'',                                                                                                                                     u'МНО',                   u'',                                    u'90'],CReportBase.AlignRight),
            ]

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        table = createTable(cursor, tableColumns)

        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 3, 1)

        # Туберкулез (А15.0-А19.9)
        table.mergeCells(0, 2, 1, 5)
        table.mergeCells(1, 2, 1, 2)
        table.mergeCells(1, 4, 1, 2)
        table.mergeCells(1, 6, 2, 1)

        # Онкологические заболевания (С00.0-С97.0)
        table.mergeCells(0, 7, 1, 5)
        table.mergeCells(1, 7, 1, 2)
        table.mergeCells(1, 9, 1, 2)
        table.mergeCells(1, 11, 2, 1)

        # Сахарный диабет (Е10.0-Е14.9)
        table.mergeCells(0, 12, 1, 7)
        table.mergeCells(1, 12, 1, 2)
        table.mergeCells(1, 14, 1, 2)
        table.mergeCells(1, 16, 2, 1)
        table.mergeCells(1, 17, 2, 1)
        table.mergeCells(1, 18, 2, 1)

        # Цереброваскулярные болезни (I60.0-I69.9)
        table.mergeCells(0, 19, 1, 5)
        table.mergeCells(1, 19, 1, 2)
        table.mergeCells(1, 21, 1, 2)
        table.mergeCells(1, 23, 2, 1)

        # из них: ОНМК (I60.0-I64)
        table.mergeCells(0, 24, 1, 6)
        table.mergeCells(1, 24, 1, 2)
        table.mergeCells(1, 26, 1, 2)
        table.mergeCells(1, 28, 2, 1)
        table.mergeCells(1, 29, 2, 1)

        # Гипертоническая болезнь (I10-I15.9)
        table.mergeCells(0, 30, 1, 7)
        table.mergeCells(1, 30, 1, 2)
        table.mergeCells(1, 32, 1, 2)
        table.mergeCells(1, 34, 2, 1)
        table.mergeCells(1, 35, 2, 1)
        table.mergeCells(1, 36, 2, 1)

        # Ишемическая болезнь сердца (I20.0-I25.9)
        table.mergeCells(0, 37, 1, 8)
        table.mergeCells(1, 37, 1, 2)
        table.mergeCells(1, 39, 1, 2)
        table.mergeCells(1, 41, 2, 1)
        table.mergeCells(1, 41, 2, 1)
        table.mergeCells(1, 41, 2, 1)
        table.mergeCells(1, 42, 2, 1)
        table.mergeCells(1, 43, 2, 1)
        table.mergeCells(1, 44, 2, 1)

        # из них: острый инфаркт миокарда (I21.0-I21.9)
        table.mergeCells(0, 45, 1, 6)
        table.mergeCells(1, 45, 1, 2)
        table.mergeCells(1, 47, 1, 2)
        table.mergeCells(1, 49, 2, 1)
        table.mergeCells(1, 50, 2, 1)

        # повторный инфаркт миокарда (i22.0-I22.9)
        table.mergeCells(0, 51, 1, 6)
        table.mergeCells(1, 51, 1, 2)
        table.mergeCells(1, 53, 1, 2)
        table.mergeCells(1, 55, 2, 1)
        table.mergeCells(1, 56, 2, 1)

        # Болезни органов дыхания (J00-J99.8)
        table.mergeCells(0, 57, 1, 5)
        table.mergeCells(1, 57, 1, 2)
        table.mergeCells(1, 59, 1, 2)
        table.mergeCells(1, 61, 2, 1)

        # из них: пневмонии (J11.0, J12.0-J18.9)
        table.mergeCells(0, 62, 1, 6)
        table.mergeCells(1, 62, 1, 2)
        table.mergeCells(1, 64, 1, 2)
        table.mergeCells(1, 66, 2, 1)
        table.mergeCells(1, 67, 2, 1)

        # хронические болезни нижних дыхательных путей (J40-J47)
        table.mergeCells(0, 68, 1, 8)
        table.mergeCells(1, 68, 1, 2)
        table.mergeCells(1, 70, 1, 2)
        table.mergeCells(1, 72, 2, 1)
        table.mergeCells(1, 73, 2, 1)
        table.mergeCells(1, 74, 2, 1)
        table.mergeCells(1, 75, 2, 1)

        # Болезни органов пищеварения (К00.0-К93.8)
        table.mergeCells(0, 76, 1, 5)
        table.mergeCells(1, 76, 1, 2)
        table.mergeCells(1, 78, 1, 2)
        table.mergeCells(1, 80, 2, 1)

        # Прочие (A00-T98 с за исключением выше представленных)
        table.mergeCells(0, 81, 1, 5)
        table.mergeCells(1, 81, 1, 2)
        table.mergeCells(1, 83, 1, 2)
        table.mergeCells(1, 85, 2, 1)

        # Число пациентов, находящихся на диспансерном наблюдении, из числа жителей участка, достигших стабильных целевых значений показателей
        table.mergeCells(0, 86, 1, 4)
        table.mergeCells(1, 86, 2, 1)
        table.mergeCells(1, 87, 2, 1)
        table.mergeCells(1, 88, 2, 1)
        table.mergeCells(1, 89, 2, 1)

        len_tableColumns = len(tableColumns) - 4
        dataTree, data = self.getData(params, len_tableColumns)
        sumRow = [0]*(len_tableColumns-1)
        baseLPUSUM = [0]*(len_tableColumns-1)
        for parentName in sorted(dataTree.keys()):
            localSum = [0]*(len_tableColumns-1)
            i = table.addRow()
            table.setText(i, 0, parentName, CReportBase.ReportSubTitle, CReportBase.AlignLeft)
            table.mergeCells(i, 0, 1, 6)
            OSList = dataTree[parentName]
            OSList.sort(key=lambda x: x[1].lower())
            for id, nameOS in OSList:
                i = table.addRow()
                dataOS = data.get(id, [0]*(len_tableColumns+1))
                for col, colText in enumerate(dataOS):
                    if col < len_tableColumns:
                        table.setText(i, col, colText)
                        if col >= 1:
                            sumRow[col-1] += colText
                            localSum[col-1] += colText
                            if dataOS[len_tableColumns]:
                                baseLPUSUM[col-1] += colText
            i = table.addRow()
            for col in xrange(len_tableColumns-1):
                if localSum[col]:
                    table.setText(i, col+1, localSum[col], CReportBase.ReportSubTitle)

        i = table.addRow()
        table.setText(i, 0, u'Базовое ЛПУ:', CReportBase.ReportSubTitle, CReportBase.AlignLeft)
        for col in xrange(len_tableColumns-1):
            table.setText(i, col+1, baseLPUSUM[col], CReportBase.ReportSubTitle)

        i = table.addRow()
        table.setText(i, 0, u'Итого:', CReportBase.ReportSubTitle, CReportBase.AlignLeft)
        for col in xrange(len_tableColumns-1):
            table.setText(i, col+1, sumRow[col], CReportBase.ReportSubTitle)
        return doc


class CDeathReportByZonesSetupDialog(QtGui.QDialog, Ui_DeathReportByZonesSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        #self.cmbOrgStructure.setFilter('OrgStructure.areaType = 1')

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
        result['orgStructureIdList'] = self.cmbOrgStructure.getItemIdList() if result['orgStructureId'] else None
        return result
