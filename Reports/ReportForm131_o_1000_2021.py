# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, QDateTime, Qt

from library.Utils      import forceInt, forceString, lastYearDay
from library.TableModel import CTableModel, CTextCol

from Orgs.Utils         import getOrgStructureFullName, getOrgStructurePersonIdList
from RefBooks.ContingentType.List import CContingentTypeTranslator
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import dateRangeAsStr
from Reports.MesDispansListDialog import getMesDispansNameList

from Events.EventTypeListEditorDialog import CEventTypeListEditorDialog
from Reports.ReportForm131_1000_SetupDialog import CReportForm131_1000_SetupDialog


def appendClientToContingentTypeCond(contingentTypeId):
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


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    # isAttache = params.get('isAttache', False)
    isAttache = True
    orgStructureId = params.get('orgStructureId', None)
    orgId          = params.get('orgId', None)
    if not endDate:
        return None

    db = QtGui.qApp.db
    mesDispansIdList = params.get('mesDispansIdList', [])
    if mesDispansIdList:
        mesDispans = u''' AND Event.MES_id IN (%s)'''%(u','.join(forceString(mesId) for mesId in mesDispansIdList if mesId))
    else:
        mesDispans = u''

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
        WHERE ClientAttach.client_id = Event.client_id AND %s)''' % (db.joinAnd(cond))
    condOrgStructure = u''
    if orgStructureId:
        personIdList = getOrgStructurePersonIdList(orgStructureId)
        if personIdList:
            condOrgStructure = u''' AND Event.execPerson_id IN (%s)'''%(u','.join(str(personId) for personId in personIdList if personId))
    stmt = u'''
    SELECT  Client.id AS clientId,
            Client.sex AS clientSex,
           age(Client.birthDate, E.execDate) AS clientAge,
           SUM(executedPMO) AS executedCntPMO,
           SUM(executedDOGVN) AS executedCntDOGVN
    FROM (SELECT DISTINCT
                 Event.id,
                 IF(rbEventProfile.code IN (8011), 1, 0) AS executedPMO,
                 IF(rbEventProfile.code IN (8008, 8009, 8014, 8015) AND Event.prevEvent_id IS NULL, 1, 0) AS executedDOGVN
          FROM Event
          LEFT JOIN EventType ON Event.eventType_id = EventType.id
          LEFT JOIN rbEventProfile ON rbEventProfile.id = EventType.eventProfile_id
          WHERE Event.deleted = 0
            AND rbEventProfile.code IN (8008, 8009, 8011, 8014, 8015)
            AND (Event.execDate >= %(begDate)s AND Event.execDate < %(endDate)s)

            %(condAttach)s
            %(condOrgStructure)s
          ) AS T
        JOIN Event E ON T.id = E.id
        JOIN Client ON E.client_id = Client.id
        LEFT JOIN ClientSocStatus ON ClientSocStatus.client_id = Client.id
        LEFT JOIN rbSocStatusClass ON rbSocStatusClass.id = ClientSocStatus.socStatusClass_id
    GROUP BY E.id''' % dict(begDate = db.formatDate(begDate),
                                 endDate = db.formatDate(endDate.addDays(1)),
                                 condAttach = (u'AND ' + condAttach) if condAttach else u'',
                                 condOrgStructure = condOrgStructure,
                                 mesDispans = mesDispans)
    return db.query(stmt)



class CReportForm131_o_1000_2021(CReport):

    ages = (u'18-34', u'35-39', u'40-54', u'55-59', u'60-64', u'65-74', u'75 и старше')

    def getAgeGroup(self, clientAge):
        if 18 <= clientAge <= 34:
            return 0
        if 35 <= clientAge <= 39:
            return 1
        if 40 <= clientAge <= 54:
            return 2
        if 55 <= clientAge <= 59:
            return 3
        if 60 <= clientAge <= 64:
            return 4
        if 65 <= clientAge <= 74:
            return 5
        if clientAge >= 75:
            return 6


    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сведения о проведении диспансеризации определенных групп взрослого населения (2021)')


    def getSetupDialog(self, parent):
        result = CReportForm1000SetupDialog(parent)
        result.setTitle(self.title())
        return result


    def dumpParams(self, cursor, params):
        db = QtGui.qApp.db
        description = []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        contingentTypeIdList = params.get('contingentTypeIdList')
        if begDate or endDate:
           description.append(dateRangeAsStr(u'за период', begDate, endDate))
        orgStructureId   = params.get('orgStructureId', None)
        # isAttache        = params.get('isAttache', False)
        isAttache = True
        orgId            = params.get('orgId', None)
        mesDispansIdList = params.get('mesDispansIdList', None)
        if mesDispansIdList:
            nameList = getMesDispansNameList(mesDispansIdList)
            if nameList:
                description.append(u'Стандарт:  %s'%(u','.join(name for name in nameList if name)))
        if contingentTypeIdList:
            description.append(u'Наблюдаемый контингент: ' + CReportForm1000SetupDialog.formatContingentTypeList(contingentTypeIdList))
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
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
            ( '7%',   [u'Возраст', u'', u'', u'', u'1'], CReportBase.AlignLeft),
            ( '3%',   [u'№ строки', u'', u'', u'', u'2'], CReportBase.AlignRight),
            ( '7.5%', [u'Все взрослое население', u'', u'Численность прикрепленного взрослого населения на 01.01 текущего года', u'', u'3'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'', u'Из них по плану подлежат: ПМО и ДОГВН (чел.)', u'', u'4'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'', u'Из них прошли:', u'ПМО (чел.)', u'5'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'', u'', u'ДОГВН (чел.)', u'6'], CReportBase.AlignRight),
            ( '7.5%', [u'В том числе:', u'Мужчины', u'Численность прикрепленного взрослого населения на 01.01 текущего года ', u'', u'7'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'', u'Из них по плану подлежат: ПМО и ДОГВН (чел.)', u'', u'8'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'', u'Из них прошли:', u'ПМО (чел.)', u'9'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'', u'', u'ДОГВН (чел.)', u'10'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'Женщины', u'Численность прикрепленного взрослого населения на 01.01 текущего года', u'', u'11'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'', u'Из них по плану подлежат: ПМО и ДОГВН (чел.)', u'', u'12'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'', u'Из них прошли:', u'ПМО (чел.)', u'13'], CReportBase.AlignRight),
            ( '7.5%', [u'', u'', u'', u'ДОГВН (чел.)', u'14'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 4, 1)
        table.mergeCells(0, 1, 4, 1)
        table.mergeCells(0, 2, 1, 4)
        table.mergeCells(0, 6, 1, 8)

        table.mergeCells(1, 2,  3, 1)
        table.mergeCells(1, 3,  3, 1)
        table.mergeCells(1, 4,  2, 2)
        table.mergeCells(1, 6,  1, 4)
        table.mergeCells(1, 10, 1, 4)

        table.mergeCells(2, 6,  2, 1)
        table.mergeCells(2, 7,  2, 1)
        table.mergeCells(2, 8,  1, 2)
        table.mergeCells(2, 10, 2, 1)
        table.mergeCells(2, 11, 2, 1)
        table.mergeCells(2, 12, 1, 2)

        self.maleDispans1001 = 0
        self.femaleDispans1001 = 0
        self.maleProphylax1001 = 0
        self.femaleProphylax1001 = 0

        endDate   = params['endDate']
        # isAttache = params.get('isAttache', False)
        isAttache = True
        orgId     = params.get('orgId', None)
        reportData = [ [0]*12 for age in self.ages ]
        query = selectData(params)
        if query is None:
            return doc
        self.getDataByEvents(reportData, query)
        self.getDataByContingent(reportData, params)
        commonAgeStats = self.getCommonAgeStats(endDate, isAttache, orgId)
        self.addCommonAgeData(reportData, commonAgeStats)

        result = [0] * 12
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

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'\n(1001) Число лиц в трудоспособном возрасте прошло: диспансеризацию определенных групп взрослого населения всего ')
        cursor.insertText(str(self.maleDispans1001 + self.femaleDispans1001))
        cursor.insertText(u', в том числе: женщин ')
        cursor.insertText(str(self.femaleDispans1001))
        cursor.insertText(u', мужчин ')
        cursor.insertText(str(self.maleDispans1001))
        cursor.insertText(u'; профилактический медицинский осмотр всего ')
        cursor.insertText(str(self.maleProphylax1001 + self.femaleProphylax1001))
        cursor.insertText(u', в том числе: женщин ')
        cursor.insertText(str(self.femaleProphylax1001))
        cursor.insertText(u', мужчин ')
        cursor.insertText(str(self.maleProphylax1001))
        cursor.insertText(u'.')
        return doc


    def getDataByEvents(self, reportData, query):
        uniqueClientIdPMO = set()
        uniqueClientIdDOGVN = set()
        while query.next():
            record = query.record()
            clientId = forceInt(record.value('clientId'))
            clientSex   = forceInt(record.value('clientSex'))
            clientAge   = forceInt(record.value('clientAge'))
            executedCntPMO = forceInt(record.value('executedCntPMO'))
            executedCntDOGVN = forceInt(record.value('executedCntDOGVN'))
            if executedCntPMO and clientId not in uniqueClientIdPMO:
                executedCntPMO = 1
                uniqueClientIdPMO.add(clientId)
                reportRow = self.getAgeGroup(clientAge)
                if reportRow is not None:
                    reportLine = reportData[reportRow]
                    column = 5 if clientSex == 1 else 9
                    reportLine[column+1] += executedCntPMO

                    reportLine[2] += executedCntPMO

                if clientSex == 1 and 16 <= clientAge <= 60:
                    self.maleProphylax1001 += executedCntPMO
                elif clientSex == 2 and 16 <= clientAge <= 55:
                    self.femaleProphylax1001 += executedCntPMO

            if executedCntDOGVN and clientId not in uniqueClientIdDOGVN:
                executedCntDOGVN = 1
                uniqueClientIdDOGVN.add(clientId)
                reportRow = self.getAgeGroup(clientAge)
                if reportRow is not None:
                    reportLine = reportData[reportRow]
                    column = 5 if clientSex == 1 else 9

                    reportLine[column+2] += executedCntDOGVN

                    reportLine[3] += executedCntDOGVN

                if clientSex == 1 and 16 <= clientAge <= 60:
                    self.maleDispans1001 += executedCntDOGVN
                elif clientSex == 2 and 16 <= clientAge <= 55:
                    self.femaleDispans1001 += executedCntDOGVN
            # if executedCntPMO or executedCntDOGVN:
            #     reportRow = self.getAgeGroup(clientAge)
            #     if reportRow is not None:
            #         reportLine = reportData[reportRow]
            #         column = 5 if clientSex == 1 else 9
            #         reportLine[column+1] += executedCntPMO
            #         reportLine[column+2] += executedCntDOGVN
            #         reportLine[2] += executedCntPMO
            #         reportLine[3] += executedCntDOGVN

            # if clientSex == 1 and 16 <= clientAge <= 60:
            #         self.maleDispans1001 += executedCntDOGVN
            #         self.maleProphylax1001 += executedCntPMO

            # elif clientSex == 2 and 16 <= clientAge <= 55:
            #         self.femaleDispans1001 += executedCntDOGVN
            #         self.femaleProphylax1001 += executedCntPMO

        return reportData


    def getDataByContingent(self, reportData, params):
        # isAttache = params.get('isAttache', False)
        isAttache = True
        # contingentTypeIdList = params.get('contingentTypeIdList', [])
        # if not contingentTypeIdList:
        #     return
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        orgId   = params.get('orgId', None)
        date = lastYearDay(endDate)
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableClientSocStatus = db.table('ClientSocStatus')
        tableRbSocStatusClass = db.table('rbSocStatusClass')
        queryTable = tableClient.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
        queryTable = queryTable.leftJoin(tableRbSocStatusClass, tableRbSocStatusClass['id'].eq(tableClientSocStatus['socStatusClass_id']))
        cols = 'age(Client.birthDate, %s) AS clientAge, Client.sex AS clientSex , COUNT(Client.`id`) AS cnt' % db.formatDate(date)
        contingentTypeCond = []
        # for contingentTypeId in contingentTypeIdList:
        #     contingentTypeCond.append(db.joinAnd(appendClientToContingentTypeCond(contingentTypeId)))
        # cond = [ db.joinOr(contingentTypeCond) ]
        cond = [tableRbSocStatusClass['code'].eq('profilac'),
                db.joinOr([tableClientSocStatus['begDate'].isNull(), tableClientSocStatus['begDate'].lt(endDate.addDays(1))]),
                db.joinOr([tableClientSocStatus['endDate'].isNull(), tableClientSocStatus['endDate'].ge(begDate)]),
                ]
        cond.append(tableClient['deleted'].eq(0))
        cond.append(tableClientSocStatus['deleted'].eq(0))
        if isAttache:
            # cond.append('SUBSTR(AddressHouse.`KLADRCode`, 1, 2)=\'%s\''%QtGui.qApp.defaultKLADR()[0:2])
            tableClientAddress = db.table('ClientAddress')
            tableAddress = db.table('Address')
            tableClientAttach = db.table('ClientAttach')
            tableAttachType = db.table('rbAttachType')
            tableAddressHouse = db.table('AddressHouse')
            clientAddressJoinCond = [tableClientAddress['client_id'].eq(tableClient['id']),
                                     'ClientAddress.id=(SELECT MAX(CA.id) FROM ClientAddress AS CA WHERE CA.client_id=ClientAddress.client_id AND CA.deleted = 0)'
                                     ]
            queryTable = queryTable.leftJoin(tableClientAddress, clientAddressJoinCond)
            queryTable = queryTable.leftJoin(tableAddress, tableAddress['id'].eq(tableClientAddress['address_id']))
            queryTable = queryTable.leftJoin(tableAddressHouse, tableAddressHouse['id'].eq(tableAddress['house_id']))
            queryTable = queryTable.innerJoin(tableClientAttach, tableClientAttach['client_id'].eq(tableClient['id']))
            queryTable = queryTable.innerJoin(tableAttachType, tableAttachType['id'].eq(tableClientAttach['attachType_id']))
            cond.append(tableClientAttach['deleted'].eq(0))
            if orgId:
                cond.append(tableClientAttach['LPU_id'].eq(orgId))
            begDateAttach = db.formatDate(QDate(endDate.year(), 1, 1))
            cond.append('ClientAttach.`id` = getClientAttachIdForDate(Client.id, 0, %s)'%(begDateAttach))
        stmt = db.selectStmtGroupBy(queryTable, cols, cond, 'clientSex, clientAge')
        query = db.query(stmt)
        while query.next():
            record = query.record()
            clientAge = forceInt(record.value('clientAge'))
            clientSex = forceInt(record.value('clientSex'))
            cnt = forceInt(record.value('cnt'))
            reportRow = self.getAgeGroup(clientAge)
            if reportRow is not None:
                reportLine = reportData[reportRow]
                if clientSex == 1:
                    reportLine[5] += cnt
                elif clientSex == 2:
                    reportLine[9] += cnt
                reportLine[1] += cnt



    def addCommonAgeData(self, reportData, commonAgeStats):
        for (clientAge, sex), val in commonAgeStats.iteritems():
            reportRow = self.getAgeGroup(clientAge)
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
            queryTable = queryTable.leftJoin(tableClientAddress, clientAddressJoinCond)
            queryTable = queryTable.leftJoin(tableAddress, tableAddress['id'].eq(tableClientAddress['address_id']))
            queryTable = queryTable.leftJoin(tableAddressHouse, tableAddressHouse['id'].eq(tableAddress['house_id']))
            cond = [  # 'SUBSTR(AddressHouse.`KLADRCode`, 1, 2)=\'%s\''%QtGui.qApp.defaultKLADR()[0:2],
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



class CReportForm1000SetupDialog(CReportForm131_1000_SetupDialog):
    def __init__(self, parent=None):
        CReportForm131_1000_SetupDialog.__init__(self, parent)
        # self.setMesDispansListVisible(True)
        self.contingentTypeIdList = []
        self.btnContingentTypeList = QtGui.QPushButton(u'Тип контингента', self)
        self.btnContingentTypeList.clicked.connect(self.on_btnContingentTypeList_clicked)
        self.lblContingentTypeList = QtGui.QLabel(u'не задано', self)
        self.lblContingentTypeList.setWordWrap(True)
        self.gridLayout.addWidget(self.btnContingentTypeList, 3, 0)
        self.gridLayout.addWidget(self.lblContingentTypeList, 3, 1)
        self.btnContingentTypeList.setVisible(False)
        self.lblContingentTypeList.setVisible(False)
        self.cmbFilterContingentType.setVisible(False)
        self.lblFilterContingentType.setVisible(False)
        self.btnMesDispansList.setVisible(False)
        self.lblMesDispansList.setVisible(False)
        self.chkAttache.setVisible(False)
        self.chkAttache.setChecked(True)


    def on_btnContingentTypeList_clicked(self, checked=False):
        dialog = CEventTypeListEditorDialog(self)
        dialog.tableModel = CContingentTypeTableModel(dialog)
        dialog.tableSelectionModel = QtGui.QItemSelectionModel(dialog.tableModel, dialog)
        dialog.tableSelectionModel.setObjectName('tableSelectionModel')
        dialog.tblEventTypeList.setModel(dialog.tableModel)
        dialog.tblEventTypeList.setSelectionModel(dialog.tableSelectionModel)
        dialog.setWindowTitle(u'Типы контингента')
        if dialog.exec_():
            self.setContingentTypeList(dialog.eventTypeIdList)
        else:
            self.setContingentTypeList([])


    def setContingentTypeList(self, idList):
        self.contingentTypeIdList = idList
        self.lblContingentTypeList.setText(self.formatContingentTypeList(idList))
        # self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(bool(idList))
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True)


    @staticmethod
    def formatContingentTypeList(idList):
        if not idList:
            return u'не задано'
        db = QtGui.qApp.db
        table = db.table('rbContingentType')
        records = db.getRecordList(table, table['name'], table['id'].inlist(idList))
        return ', '.join(forceString(rec.value('name')) for rec in records)


    def params(self):
        result = CReportForm131_1000_SetupDialog.params(self)
        result['contingentTypeIdList'] = self.contingentTypeIdList
        return result


    def setParams(self, params):
        CReportForm131_1000_SetupDialog.setParams(self, params)
        self.setContingentTypeList(params.get('contingentTypeIdList', []))



class CContingentTypeTableModel(CTableModel):
    def __init__(self, parent=None):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Код',         ['code'], 30))
        self.addColumn(CTextCol(u'Наименование',['name'], 70))
        self.setTable('rbContingentType')
        self.setIdList(QtGui.qApp.db.getDistinctIdList('rbContingentType', 'id', order='code'))


    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
