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

from library.Utils      import firstYearDay, forceInt, forceString, lastYearDay

from Orgs.Utils         import getOrgStructureFullName, getOrgStructurePersonIdList
from RefBooks.ContingentType.List import CContingentTypeTranslator
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import dateRangeAsStr, getAgeClass
from Reports.MesDispansListDialog import getMesDispansNameList

from Reports.ReportForm131_1000_SetupDialog import CReportForm131_1000_SetupDialog


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    contingentTypeId = params.get('contingentTypeId', None)
    isAttache = params.get('isAttache', False)
    orgStructureId = params.get('orgStructureId', None)
    orgId          = params.get('orgId', None)
    if not endDate or not contingentTypeId:
        return None
    begYearDate = firstYearDay(begDate)
    endYearDate = lastYearDay(endDate)
    db = QtGui.qApp.db
    mesDispansIdList = params.get('mesDispansIdList', [])
    if mesDispansIdList:
        mesDispans = u''' AND Event.MES_id IN (%s)'''%(u','.join(forceString(mesId) for mesId in mesDispansIdList if mesId))
    else:
        mesDispans = u''
    if contingentTypeId:
        condAttach = []
        if isAttache:
            tableClientAttach = db.table('ClientAttach')
            tableAttachType = db.table('rbAttachType')
            cond = [tableClientAttach['deleted'].eq(0),
                    tableAttachType['temporary'].eq(0),
                    db.joinOr([tableClientAttach['begDate'].isNull(), tableClientAttach['begDate'].lt(endDate.addDays(1))]),
                    db.joinOr([tableClientAttach['endDate'].isNull(), tableClientAttach['endDate'].ge(begDate)])
                    ]
            if orgId:
                cond.append(tableClientAttach['LPU_id'].eq(orgId))
            condAttach = u'''
            EXISTS(SELECT MAX(ClientAttach.id)
            FROM ClientAttach INNER JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
            WHERE ClientAttach.client_id = clientCT.id
    AND %s)'''%(db.joinAnd(cond))
        condOrgStructure = u''
        if orgStructureId:
            personIdList = getOrgStructurePersonIdList(orgStructureId)
            if personIdList:
                condOrgStructure = u''' AND Event.execPerson_id IN (%s)'''%(u','.join(str(personId) for personId in personIdList if personId))
        stmt = u'''
    SELECT clientSex,
           clientAge,
           SUM(executedI) AS executedCntI,
           SUM(executedII) AS executedCntII
    FROM (SELECT IF((Event.execDate IS NOT NULL AND DATE(Event.execDate) BETWEEN DATE(%(begDate)s) AND DATE(%(endDate)s)
                 AND Event.prevEvent_id IS NULL), 1, 0) AS executedI,
                 IF((Event.execDate IS NOT NULL AND DATE(Event.execDate) BETWEEN  DATE(%(begDate)s) AND DATE(%(endDate)s)
                 AND Event.prevEvent_id IS NOT NULL), 1, 0) AS executedII,
                 clientCT.sex AS clientSex,
                 age(clientCT.birthDate, %(endYearDate)s) AS clientAge
          FROM Event
          INNER JOIN mes.MES ON mes.MES.id=Event.MES_id
          INNER JOIN mes.mrbMESGroup ON mes.mrbMESGroup.id=mes.MES.group_id
          INNER JOIN Client AS clientCT ON clientCT.id=Event.client_id
          WHERE (Event.deleted=0)
            AND DATE(DATE(Event.setDate)) BETWEEN DATE(%(begPrevYearDate)s) AND DATE(%(endYearDate)s)
            %(mesDispans)s
            AND (mes.mrbMESGroup.code='ДиспанС')
            AND (mes.MES.endDate IS NULL OR mes.MES.endDate >= DATE(%(begPrevYearDate)s))
            %(condAttach)s
            %(condOrgStructure)s
          ) AS T
    GROUP BY clientSex, clientAge''' % dict(begDate = db.formatDate(begDate),
                                            endDate = db.formatDate(endDate),
                                            begYearDate = db.formatDate(begYearDate),
                                            endYearDate = db.formatDate(endYearDate),
                                            begPrevYearDate = db.formatDate(begYearDate.addYears(-1)),
                                            condAttach = (u'AND ' + condAttach) if condAttach else u'',
                                            condOrgStructure = condOrgStructure,
                                            mesDispans = mesDispans
                                           )
    return db.query(stmt)


class CReportForm131_o_1000_2016(CReport):

    ages = (u'18-36 лет', u'39-60 лет', u'Старше 60 лет')

    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.parent = parent
        self.setTitle(u'Сведения о проведении диспансеризации определенных групп взрослого населения (2016)')


    def getSetupDialog(self, parent):
        result = CReportForm131_1000_SetupDialog(parent)
        result.setMesDispansListVisible(True)
        result.setTitle(self.title())
        return result


    def dumpParams(self, cursor, params):
        db = QtGui.qApp.db
        description = []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if begDate or endDate:
           description.append(dateRangeAsStr(u'за период', begDate, endDate))
        contingentTypeId = params.get('contingentTypeId', None)
        orgStructureId   = params.get('orgStructureId', None)
        isAttache        = params.get('isAttache', False)
        orgId            = params.get('orgId', None)
        mesDispansIdList = params.get('mesDispansIdList', None)
        if mesDispansIdList:
            nameList = getMesDispansNameList(mesDispansIdList)
            if nameList:
                description.append(u'Стандарт:  %s'%(u','.join(name for name in nameList if name)))
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        if contingentTypeId:
            description.append(u'тип контингента: ' + forceString(db.translate('rbContingentType', 'id', contingentTypeId, 'name')))
        if isAttache:
            description.append(u'прикрепление к ЛПУ: ' + forceString(db.translate('Organisation', 'id', orgId, 'shortName')))
        description.append(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.insertText(u'(1000)')
        cursor.insertBlock()
        tableColumns = [
            ( '7%',   [u'Возрастная группа', u'', u'', u'1'], CReportBase.AlignLeft),
            ( '3%',   [u'№ строки', u'', u'', u'2'], CReportBase.AlignRight),
            ( '7.5%', [u'Все население', u'Численность населения на 01.01 текущего года', u'', u'3'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'Подлежит диспансе-ризации по плану текущего года', u'', u'4'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'Прошли диспансеризацию (чел.)', u'I этап', u'5'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'', u'II этап', u'6'], CReportBase.AlignRight),
            ( '7.5%', [u'Мужчины', u'Численность населения на 01.01 текущего года', u'', u'7'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'Подлежит диспансе-ризации по плану текущего года', u'', u'8'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'Прошли диспансеризацию (чел.)', u'I этап', u'9'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'', u'II этап', u'10'], CReportBase.AlignRight),
            ( '7.5%', [u'Женщины', u'Численность населения на 01.01 текущего года', u'', u'11'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'Подлежит диспансе-ризации по плану текущего года', u'', u'12'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'Прошли диспансеризацию (чел.)', u'I этап', u'13'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'', u'II этап', u'14'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 3, 1)
        table.mergeCells(1, 2, 2, 1)
        table.mergeCells(1, 3, 2, 1)
        table.mergeCells(0, 2, 1, 4)
        table.mergeCells(1, 4, 1, 2)
        table.mergeCells(0, 6, 1, 4)
        table.mergeCells(1, 6, 2, 1)
        table.mergeCells(1, 7, 2, 1)
        table.mergeCells(1, 8, 1, 2)
        table.mergeCells(0, 10, 1, 4)
        table.mergeCells(1, 10, 2, 1)
        table.mergeCells(1, 11, 2, 1)
        table.mergeCells(1, 12, 1, 2)
        query = selectData(params)
        if query is None:
            return doc
        endDate   = params['endDate']
        isAttache = params.get('isAttache', False)
        orgId     = params.get('orgId', None)
        reportData = [ [0]*12 for age in self.ages]
        self.getDataByEvents(reportData, query)
        self.getDataByContingent(reportData, params)
        commonAgeStats = self.getCommonAgeStats(endDate, isAttache, orgId)
        self.addCommonAgeData(reportData, commonAgeStats)
        result = [0]*12
        cnt = 1
        for reportRow, age in enumerate(self.ages):
            i = table.addRow()
            table.setText(i, 0, age)
            table.setText(i, 1, cnt)
            cnt += 1
            reportLine = reportData[reportRow]
            for idx, value in enumerate(reportLine):
                column = 2+idx
                table.setText(i, column, value)
                result[idx] += value
        i = table.addRow()
        table.mergeCells(i, 0, 1, 2)
        table.setText(i, 1, u'Всего')
        for idx, value in enumerate(result):
            column = 2+idx
            table.setText(i, column, value)
        return doc


    def getDataByEvents(self, reportData, query):
        while query.next():
            record = query.record()
            clientSex   = forceInt(record.value('clientSex'))
            clientAge   = forceInt(record.value('clientAge'))
            executedCntI = forceInt(record.value('executedCntI'))
            executedCntII = forceInt(record.value('executedCntII'))
            if executedCntI or executedCntII:
                reportRow = getAgeClass(clientAge)
                if reportRow is not None:
                    reportLine = reportData[reportRow]
                    column = 5 if clientSex == 1 else 9
                    reportLine[column+1] += executedCntI
                    reportLine[column+2] += executedCntII
                    reportLine[2] += executedCntI
                    reportLine[3] += executedCntII
        return reportData


    def addCommonAgeData(self, reportData, commonAgeStats):
        for (clientAge, sex), val in commonAgeStats.iteritems():
            reportRow = getAgeClass(clientAge)
            if reportRow is not None:
                reportLine = reportData[reportRow]
                if sex == 1:
                    reportLine[4] += val
                elif sex == 2:
                    reportLine[8] += val
                reportLine[0] += val


    def getCommonAgeStats(self, endDate, isAttache, orgId):
        db = QtGui.qApp.db
        date = lastYearDay(endDate)
        strDate = db.formatDate(date)
        tableClient = db.table('Client')
        if isAttache:
            tableClientAddress = db.table('ClientAddress')
            tableAddress = db.table('Address')
            tableClientAttach = db.table('ClientAttach')
            tableAttachType = db.table('rbAttachType')
            tableAddressHouse = db.table('AddressHouse')
            clientAddressJoinCond = [tableClientAddress['client_id'].eq(tableClient['id']),
                                     'ClientAddress.id=(SELECT MAX(CA.id) FROM ClientAddress AS CA WHERE CA.client_id=ClientAddress.client_id AND CA.deleted = 0)']
            queryTable = tableClient
            queryTable = queryTable.innerJoin(tableClientAddress, clientAddressJoinCond)
            queryTable = queryTable.innerJoin(tableAddress, tableAddress['id'].eq(tableClientAddress['address_id']))
            queryTable = queryTable.innerJoin(tableAddressHouse, tableAddressHouse['id'].eq(tableAddress['house_id']))
            cond = ['SUBSTR(AddressHouse.`KLADRCode`, 1, 2)=\'%s\''%QtGui.qApp.defaultKLADR()[0:2],
                    tableClient['deleted'].eq(0),
                    tableClientAttach['deleted'].eq(0)
                    ]
            if orgId:
                cond.append(tableClientAttach['LPU_id'].eq(orgId))
            begDateAttach = db.formatDate(QDate(endDate.year(), 1, 1))
            cond.append('ClientAttach.`id` = getClientAttachIdForDate(Client.id, 0, %s)'%(begDateAttach))
            queryTable = queryTable.innerJoin(tableClientAttach, tableClientAttach['client_id'].eq(tableClient['id']))
            queryTable = queryTable.innerJoin(tableAttachType, tableAttachType['id'].eq(tableClientAttach['attachType_id']))
        else:
            cond = [tableClient['deleted'].eq(0)]
            queryTable = tableClient
        fields = 'age(birthDate, %s) AS clientAge, sex AS clientSex , COUNT(Client.`id`) AS cnt' % strDate
#        cond.append('''(age(birthDate, %s) >= 18 AND age(birthDate, %s) < 36) OR (age(birthDate, %s) >= 39 AND age(birthDate, %s) < 60) OR age(birthDate, %s) > 60'''%(strDate, strDate, strDate, strDate, strDate))
        stmt = db.selectStmtGroupBy(queryTable, fields, cond, 'clientSex, clientAge')
        query = db.query(stmt)
        result = {}
        while query.next():
            record = query.record()
            clientAge = forceInt(record.value('clientAge'))
            clientSex = forceInt(record.value('clientSex'))
            cnt= forceInt(record.value('cnt'))
            key = clientAge, clientSex
            result[key] = result.get(key, 0) + cnt
        return result


    def getDataByContingent(self, reportData, params):
        contingentTypeId = params.get('contingentTypeId', None)
        isAttache = params.get('isAttache', False)
        if not contingentTypeId:
            return {}
        endDate = params.get('endDate', QDate())
        orgId   = params.get('orgId', None)
        date = lastYearDay(endDate)
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableClientSocStatus = db.table('ClientSocStatus')
        queryTable = tableClient.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
        cols = 'age(Client.birthDate, %s) AS clientAge, Client.sex AS clientSex , COUNT(Client.`id`) AS cnt' % db.formatDate(date)
        cond = self.appendClientToContingentTypeCond(contingentTypeId)
        cond.append(tableClient['deleted'].eq(0))
        if isAttache:
            cond.append('SUBSTR(AddressHouse.`KLADRCode`, 1, 2)=\'%s\''%QtGui.qApp.defaultKLADR()[0:2])
            tableClientAddress = db.table('ClientAddress')
            tableAddress = db.table('Address')
            tableClientAttach = db.table('ClientAttach')
            tableAttachType = db.table('rbAttachType')
            tableAddressHouse = db.table('AddressHouse')
            clientAddressJoinCond = [tableClientAddress['client_id'].eq(tableClient['id']),
                                     'ClientAddress.id=(SELECT MAX(CA.id) FROM ClientAddress AS CA WHERE CA.client_id=ClientAddress.client_id AND CA.deleted = 0)'
                                     ]
            queryTable = queryTable.innerJoin(tableClientAddress, clientAddressJoinCond)
            queryTable = queryTable.innerJoin(tableAddress, tableAddress['id'].eq(tableClientAddress['address_id']))
            queryTable = queryTable.innerJoin(tableAddressHouse, tableAddressHouse['id'].eq(tableAddress['house_id']))
            queryTable = queryTable.innerJoin(tableClientAttach, tableClientAttach['client_id'].eq(tableClient['id']))
            queryTable = queryTable.innerJoin(tableAttachType, tableAttachType['id'].eq(tableClientAttach['attachType_id']))
            cond.append(tableClientAttach['deleted'].eq(0))
            if orgId:
                cond.append(tableClientAttach['LPU_id'].eq(orgId))
            begDateAttach = db.formatDate(QDate(endDate.year(), 1, 1))
            cond.append('ClientAttach.`id` = getClientAttachIdForDate(Client.id, 0, %s)'%(begDateAttach))
            cond.append(tableClientSocStatus['deleted'].eq(0))
            cond.append('ClientSocStatus.begDate BETWEEN %s  and %s'%(begDateAttach, db.formatDate(date)))
        stmt = db.selectStmtGroupBy(queryTable, cols, cond, 'clientSex, clientAge')
        query = db.query(stmt)
        while query.next():
            record = query.record()
            clientAge = forceInt(record.value('clientAge'))
            clientSex = forceInt(record.value('clientSex'))
            cnt= forceInt(record.value('cnt'))
            reportRow = getAgeClass(clientAge)
            if reportRow is not None:
                reportLine = reportData[reportRow]
                if clientSex == 1:
                    reportLine[5] += cnt
                elif clientSex == 2:
                    reportLine[9] += cnt
                reportLine[1] += cnt


    def appendClientToContingentTypeCond(self, contingentTypeId):
        if not contingentTypeId:
            return []
        db = QtGui.qApp.db
        contingentOperation = forceInt(db.translate(CContingentTypeTranslator.CTTName, 'id',
                                                    contingentTypeId, 'contingentOperation'))
        contingentTypeCond = []
        if CContingentTypeTranslator.isSexAgeSocStatusEnabled(contingentOperation):
            tmp = []
            contingentTypeCond.append('Client.deleted = 0')
            sexAgeCond    = CContingentTypeTranslator.getSexAgeCond(contingentTypeId)
            socStatusCond = CContingentTypeTranslator.getSocStatusCond(contingentTypeId)
            if CContingentTypeTranslator.isSexAgeSocStatusOperationType_OR(contingentOperation):
                if sexAgeCond is not None:
                    tmp.extend(sexAgeCond)
                if socStatusCond is not None:
                    tmp.extend(socStatusCond)
                contingentTypeCond.append(db.joinOr(tmp))
            else:
                if sexAgeCond is not None:
                    tmp.append(db.joinOr(sexAgeCond))
                if socStatusCond is not None:
                    tmp.append(db.joinOr(socStatusCond))
                contingentTypeCond.append(db.joinAnd(tmp))
        return contingentTypeCond

