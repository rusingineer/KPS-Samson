# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDate, forceDouble, formatSex, forceRef
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import getStmt, colEvent, colClient, colClientName, colClientSex, colClientBirthDate, \
    colRegAddress, colLocRegAddress, colWorkAddress, colOrgStructureInfis, colEventSetDate, colEventExecDate, \
    colServiceInfis, colServiceName, colServiceBegDate, colServiceEndDate, colMKBCode, colAmount, colSUM, colExposedSum


class CEconomicAnalisysE13(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Форма Э-13. Реестр счетов за пролеченных больных')

    def selectData(self, params):
        cols = [colEvent, colClient, colClientName, colClientSex, colClientBirthDate,
            # colRegAddress, colLocRegAddress, colWorkAddress,
            colOrgStructureInfis,
            colEventSetDate, colEventExecDate, colServiceInfis, colServiceName,
            colServiceBegDate, colServiceEndDate, colMKBCode, colAmount, colSUM, colExposedSum]
        colsStmt = u"""select colEvent as eventId,
        colClient as clientId,
        colClientName as person,
        colClientSex as pol,
        colClientBirthDate as datr,
       /* colRegAddress as reg_addr,
        colLocRegAddress as liv_addr,
        colWorkAddress as work_addr, */
        colOrgStructureInfis as org_code,
        colEventSetDate as setDate,
        colEventExecDate as execDate,
        colServiceInfis as uslcode,
        colServiceName as usl,
        colServiceBegDate as begdat,
        colServiceEndDate as enddat,
        colMKBCode as mkb,
        colAmount as amount,
        round(sum(colSUM), 2) as sum,
        round(sum(colExposedSUM), 2) as exposedSum
        """
        groupCols = u'colClient, colServiceInfis, colServiceBegDate, colServiceEndDate'
        orderCols = u'colClient, colServiceBegDate, colServiceEndDate, colServiceInfis'

        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params)

        db = QtGui.qApp.db
        return db.query(stmt)


    def selectClientData(self, clientIdSet):
        db = QtGui.qApp.db
        table = db.table('Client')
        cond = table['id'].inlist(clientIdSet)
        stmt = u'''SELECT Client.id,
                          getClientRegAddress(Client.id) as reg_addr,
                          getClientLocAddress(Client.id) as liv_addr,
                          getClientWork(Client.id) as work_addr
                   FROM Client
                   WHERE {0}'''.format(cond)
        return db.query(stmt)


    def build(self, description, params):
        needExposedSum = params.get('dataType', None) == 3

        reportData = {}
        clientData = {}
        clientIdSet = set()

        def processQuery(query):
            while query.next():
                record = query.record()
                id = forceInt(record.value('eventId'))
                clientId = forceRef(record.value('clientId'))
                clientIdSet.add(clientId)
                reportLine = reportData.setdefault(id, {
                    'clientId': clientId,
                    'person': forceString(record.value('person')),
                    'pol': forceInt(record.value('pol')),
                    'datr': forceDate(record.value('datr')),
                    # 'reg_addr': forceString(record.value('reg_addr')),
                    # 'liv_addr': forceString(record.value('liv_addr')),
                    # 'work_addr': forceString(record.value('work_addr')),
                    'setDate': forceDate(record.value('setDate')),
                    'execDate': forceDate(record.value('execDate')),
                    'org_code': forceString(record.value('org_code')),
                    'usl': []
                })
                reportLine['usl'].append({
                    'name': forceString(record.value('usl')),
                    'code': forceString(record.value('uslcode')),
                    'begdat': forceString(record.value('begdat')),
                    'enddat': forceString(record.value('enddat')),
                    'mkb': forceString(record.value('mkb')),
                    'amount': forceInt(record.value('amount')),
                    'sum': forceDouble(record.value('sum')),
                    'exposedSum': forceDouble(record.value('exposedSum')),

                })

        def processClientQuery(query):
            while query.next():
                record = query.record()
                clientId = forceRef(record.value('id'))
                clientData.setdefault(clientId, {
                    'clientId': clientId,
                    'reg_addr': forceString(record.value('reg_addr')),
                    'liv_addr': forceString(record.value('liv_addr')),
                    'work_addr': forceString(record.value('work_addr')),
                })

        query = self.selectData(params)
        processQuery(query)

        query = self.selectClientData(clientIdSet)
        processClientQuery(query)

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(description)
        cursor.insertBlock()

        tableColumns = [
            ('1%', [u'№ п/п'], CReportBase.AlignCenter),
            ('5%', [u'№ карты'], CReportBase.AlignCenter),
            ('15%', [u'ФИО пациента'], CReportBase.AlignCenter),
            ('3%', [u'Пол'], CReportBase.AlignCenter),
            ('8%', [u'Дата рождения'], CReportBase.AlignCenter),
            ('21%', [u'Адрес по регистрации'], CReportBase.AlignCenter),
            ('21%', [u'Адрес по проживанию'], CReportBase.AlignCenter),
            ('11%', [u'Место работы'], CReportBase.AlignCenter),
            ('5%', [u'Код отделения'], CReportBase.AlignCenter),
            ('5%', [u'Дата начала лечения'], CReportBase.AlignCenter),
            ('5%', [u'Дата окончания лечения'], CReportBase.AlignCenter)
            ]
        if needExposedSum:
            tableColumns.append(('5%',  [u''], CReportBase.AlignCenter))
        table = createTable(cursor, tableColumns)
        keys = reportData.keys()
        keys.sort()
        pp = 0
        for key in keys:
            pp += 1
            d = reportData[key]
            clientId = d['clientId']
            c = clientData[clientId]
            row = table.addRow()
            table.setText(row, 0, pp)
            table.setText(row, 1, clientId, CReportBase.TableHeader)
            table.setText(row, 2, d['person'], CReportBase.TableHeader)
            table.setText(row, 3, formatSex(d['pol']), CReportBase.TableHeader)
            table.setText(row, 4, d['datr'].toString('dd.MM.yyyy'), CReportBase.TableHeader)
            table.setText(row, 5, c['reg_addr'])
            table.setText(row, 6, c['liv_addr'])
            table.setText(row, 7, c['work_addr'])
            table.setText(row, 8, d['org_code'])
            table.setText(row, 9, d['setDate'].toString('dd.MM.yyyy'))
            table.setText(row, 10, d['execDate'].toString('dd.MM.yyyy'))
            row = table.addRow()
            table.setText(row, 5, u'Наименование услуги', CReportBase.TableHeader)
            table.setText(row, 6, u'Код услуги', CReportBase.TableHeader)
            table.setText(row, 7, u'Дата выполнения услуги (начало/окончание)', CReportBase.TableHeader)
            table.setText(row, 8, u'Код МКБ', CReportBase.TableHeader)
            table.setText(row, 9, u'Кол-во услуг', CReportBase.TableHeader)
            table.setText(row, 10, u'Сумма', CReportBase.TableHeader)
            if needExposedSum:
                table.setText(row, 11, u'Выставленная сумма', CReportBase.TableHeader)
            row = table.addRow()
            sum = 0
            exposedSum = 0
            amount = 0
            b = row-1
            a = 2
            for i, usl in enumerate(d['usl']):
                if i > 0:
                    row = table.addRow()
                table.setText(row, 5, "%s" % (usl['name']))
                table.setText(row, 6, "%s" % (usl['code']))
                table.setText(row, 7, "%s / %s" % (usl['begdat'], usl['enddat']))
                table.setText(row, 8, "%s" % (usl['mkb']))
                table.setText(row, 9, "%s" % (usl['amount']))
                table.setText(row, 10, usl['sum'])
                if needExposedSum:
                    table.setText(row, 11, usl['exposedSum'])
                sum += usl['sum']
                exposedSum += usl['exposedSum']
                amount += usl['amount']
                a+=1
            row = table.addRow()
            table.mergeCells(b, 1, a, 5 if needExposedSum else 4)
            table.setText(row, 8, u'Итого:', CReportBase.TableHeader)
            table.mergeCells(row, 5, 1, 4 if needExposedSum else 3)
            table.mergeCells(b, 0, a, 1)
            table.setText(row, 9, amount)
            table.setText(row, 10, sum)
            if needExposedSum:
                table.setText(row, 11, exposedSum)
        return doc


class CEconomicAnalisysE13Ex(CEconomicAnalisysE13):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysE13.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.cbPrice.setChecked(False)
        result.cbPrice.setEnabled(False)
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysE13.build(self, '\n'.join(self.getDescription(params)), params)
