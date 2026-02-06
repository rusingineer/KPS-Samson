# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDouble
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog, getCond

#не стала вешать на общий эк анализ. Тк группировка очень специфична и не все столбцы сойдутся по цифрам
class CReportStomPersonSalary(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет для ЗП')
        self.groupByPersonSnils = 0

    def selectData(self, params):
        self.groupByPersonSnils = params.get('groupByPersonSnils', 0)

        stmt = u"""select
        colPersonFIO as person,
        colPersonSNILS as personSNILS,
        colPersonWithSpeciality as personWithSpeciality,
        colCreatePerson as createPerson,
        count(distinct colEvent) as cnt,
        count(distinct colClient) as fl,
        sum(colPos) as pos,
        round(sum(colUET), 2) as uet
        FROM (
            select Event.client_id as colClient, Event.id as colEvent, 
            concat(createPerson.lastName, ' ', createPerson.firstName, ' ', createPerson.patrName, ' (', createPerson.code, ')') as colCreatePerson, 
            Person.SNILS as colPersonSNILS, 
            concat(Person.lastName, ' ', Person.firstName, ' ', Person.patrName) as colPersonFIO, 
            concat(Person.lastName, ' ', Person.firstName, ' ', Person.patrName, ' (', Person.code, '), ', ifnull(rbSpeciality.OKSOName, '')) as colPersonWithSpeciality, 
            IF(rbService.id in (select vVisitServices.id from vVisitServices), 1, 0) AS colPos, 
            Action.amount * ct.uet as colUET
            
            FROM Action
            LEFT JOIN Event on Event.id = Action.event_id
            LEFT JOIN Organisation currentOrg on currentOrg.id = Event.org_id
            LEFT JOIN EventType ON EventType.id = Event.eventType_id
            LEFT JOIN rbMedicalAidType ON EventType.medicalAidType_id = rbMedicalAidType.id
            LEFT JOIN rbEventProfile ep on ep.id = EventType.eventProfile_id
            LEFT JOIN ActionType ON ActionType.id = Action.actionType_id
            LEFT JOIN rbService ON rbService.id = ActionType.nomenclativeService_id
            LEFT JOIN Contract ON Contract.id = Event.contract_id
            LEFT JOIN Organisation AS ContractPayer ON ContractPayer.id = Contract.payer_id
            LEFT JOIN rbFinance on rbFinance.id = coalesce(Action.finance_id, Contract.finance_id)
            LEFT JOIN Contract_Tariff ct ON ct.master_id in (Contract.id, Contract.priceListExternal_id)
                and ct.service_id = rbService.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(Action.endDate) between ct.begDate and ct.endDate
                or DATE(Action.endDate) >= ct.begDate and ct.endDate is null) and ct.tariffType in (2,5)
            LEFT JOIN Diagnosis d on d.id = (SELECT diagnosis_id
              FROM Diagnostic
              INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = diagnosisType_id
              WHERE Diagnostic.event_id = Event.id
              AND Diagnostic.deleted = 0
              AND rbDiagnosisType.code IN ('1', '2', '4')
              ORDER BY rbDiagnosisType.code
              LIMIT 1
              )
            LEFT JOIN Person ON Person.id = Action.person_id
            LEFT JOIN Person createPerson ON createPerson.id = Action.createPerson_id
            LEFT JOIN rbSpeciality PersonSpeciality ON PersonSpeciality.id = Person.speciality_id
            LEFT JOIN Client on Client.id = Event.client_id
            LEFT JOIN ClientPolicy on ClientPolicy.id = COALESCE((SELECT MAX(cp2.id) 
                                                                  FROM ClientPolicy cp2
                                                                  WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
                (select MAX(cp.begDate) from ClientPolicy cp
                        WHERE cp.client_id = Client.id
                          AND cp.policyType_id IN (1,2)
                          AND cp.deleted = 0
                          AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= Event.execDate))),
               (SELECT MAX(cp2.id)
                        FROM ClientPolicy cp2
                        WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
                        (select MAX(cp.begDate)
                          from ClientPolicy cp
                          WHERE cp.client_id = Client.id
                          AND cp.policyType_id IN (1,2)
                          AND cp.deleted = 0
                          AND cp.begDate BETWEEN Event.execDate AND ADDDATE(DATE(Event.execDate), 30)
                          )),
              (SELECT MAX(cp2.id)
                      FROM ClientPolicy cp2
                      WHERE cp2.client_id = Event.relative_id AND cp2.deleted = 0 AND cp2.begDate =
                      (select MAX(cp.begDate)
                      from ClientPolicy cp
                      WHERE cp.client_id = Event.relative_id
                          AND cp.policyType_id IN (1,2)
                          AND cp.deleted = 0
                          AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= Event.execDate)
                         )))
            LEFT JOIN Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
            LEFT JOIN Organisation AS headInsurer ON headInsurer.id = Insurer.head_id
            LEFT JOIN rbMedicalAidType mt ON mt.id = case when rbMedicalAidType.regionalCode in ('271', '272') and Event.execDate >= '2020-05-01' then (select mat.id from rbMedicalAidType mat where mat.regionalCode = IF(rbMedicalAidType.regionalCode = '271', '21', '22') limit 1) else rbMedicalAidType.id end
            
            LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id
            LEFT JOIN OrgStructure on OrgStructure.id = Person.orgStructure_id
            WHERE Action.deleted = 0
            and Event.deleted = 0
            and ActionType.nomenclativeService_id is not null
            and Event.expose = 1
            and {cond}       
            and ct.id is not null
            
            UNION ALL 
            
            select Event.client_id as colClient, Event.id as colEvent, 
            concat(createPerson.lastName, ' ', createPerson.firstName, ' ', createPerson.patrName, ' (', createPerson.code, ')') as colCreatePerson, 
            Person.SNILS as colPersonSNILS, concat(Person.lastName, ' ', Person.firstName, ' ', Person.patrName) as colPersonFIO, 
            concat(Person.lastName, ' ', Person.firstName, ' ', Person.patrName, ' (', Person.code, '), ', ifnull(rbSpeciality.OKSOName, '')) as colPersonWithSpeciality, 
            IF(rbService.id in (select vVisitServices.id from vVisitServices), 1, 0) AS colPos, 
            0 as colUET
            
            FROM Visit
            LEFT JOIN Event on Event.id = Visit.event_id
            LEFT JOIN EventType  ON EventType.id = Event.eventType_id
            LEFT JOIN rbService ON rbService.id = Visit.service_id
            LEFT JOIN rbMedicalAidType ON EventType.medicalAidType_id = rbMedicalAidType.id
            LEFT JOIN rbEventProfile ep on ep.id = EventType.eventProfile_id
            LEFT JOIN Contract ON Contract.id = Event.contract_id
            LEFT JOIN Organisation AS ContractPayer ON ContractPayer.id = Contract.payer_id
            LEFT JOIN rbFinance on rbFinance.id = coalesce(Visit.finance_id, Contract.finance_id)
            LEFT JOIN Contract_Tariff ct ON ct.master_id in (Contract.id, Contract.priceListExternal_id)
                and ct.tariffType = 0 and ct.service_id = rbService.id and ct.deleted = 0
                and (ct.endDate is not null and DATE(Visit.date) between ct.begDate and ct.endDate
                or DATE(Visit.date) >= ct.begDate and ct.endDate is null)
            LEFT JOIN Person createPerson ON createPerson.id = Visit.createPerson_id    
            LEFT JOIN Person ON Person.id = Visit.person_id
            LEFT JOIN Client on Client.id = Event.client_id
            LEFT JOIN ClientPolicy on ClientPolicy.id = COALESCE((SELECT MAX(cp2.id) 
                                                                  FROM ClientPolicy cp2
                                                                  WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
                (select MAX(cp.begDate) from ClientPolicy cp
                        WHERE cp.client_id = Client.id
                          AND cp.policyType_id IN (1,2)
                          AND cp.deleted = 0
                          AND cp.begDate <= Event.setDate AND (cp.endDate is NULL OR cp.endDate >= Event.setDate))),
               (SELECT MAX(cp2.id)
                        FROM ClientPolicy cp2
                        WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
                        (select MAX(cp.begDate)
                          from ClientPolicy cp
                          WHERE cp.client_id = Client.id
                          AND cp.policyType_id IN (1,2)
                          AND cp.deleted = 0
                          AND cp.begDate BETWEEN Event.setDate AND ADDDATE(DATE(Event.execDate), 30)
                          )),
              (SELECT MAX(cp2.id)
                      FROM ClientPolicy cp2
                      WHERE cp2.client_id = Event.relative_id AND cp2.deleted = 0 AND cp2.begDate =
                      (select MAX(cp.begDate)
                      from ClientPolicy cp
                      WHERE cp.client_id = Event.relative_id
                          AND cp.policyType_id IN (1,2)
                          AND cp.deleted = 0
                          AND cp.begDate <= Event.setDate AND (cp.endDate is NULL OR cp.endDate >= Event.setDate)
                         )))
            LEFT JOIN Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
            LEFT JOIN Organisation AS headInsurer ON headInsurer.id = Insurer.head_id
            LEFT JOIN rbMedicalAidType mt ON mt.id = case when rbMedicalAidType.regionalCode in ('271', '272') and Event.execDate >= '2020-05-01' then (select mat.id from rbMedicalAidType mat where mat.regionalCode = IF(rbMedicalAidType.regionalCode = '271', '21', '22') limit 1) else rbMedicalAidType.id end
            
            LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id
            LEFT JOIN OrgStructure on OrgStructure.id = Person.orgStructure_id
            WHERE Event.deleted = 0
            and Event.expose = 1
            and Visit.deleted = 0
            and Visit.service_id is not null
            and {cond}
            and ct.id is not null
        ) q
        GROUP BY {groupCols} 
        ORDER BY {orderCols}
        """

        groupCols = u'colPersonSNILS, ' if self.groupByPersonSnils else ''
        orderCols = u'colPersonSNILS, ' if self.groupByPersonSnils else ''

        groupCols += u'colPersonWithSpeciality, colCreatePerson'
        orderCols += u'colPersonWithSpeciality, colCreatePerson'

        return QtGui.qApp.db.query(stmt.format(cond=getCond(params), groupCols=groupCols, orderCols=orderCols))

    def build(self, description, params):
        needExposedSum = params.get('dataType', None) == 3

        reportRowSize = 5 if needExposedSum else 4
        reportData = {}

        def processQuery(query):
            while query.next():
                record = query.record()
                person = forceString(record.value('person')) if self.groupByPersonSnils else ''
                personSNILS = forceString(record.value('personSNILS')) if self.groupByPersonSnils else ''
                personWithSpeciality = forceString(record.value('personWithSpeciality'))
                createPerson = forceString(record.value('createPerson'))
                pos = forceInt(record.value('pos'))
                uet = forceDouble(record.value('uet'))


                key = ((person, personSNILS), personWithSpeciality, createPerson)

                reportLine = reportData.setdefault(key, [0] * reportRowSize)
                reportLine[0] += uet
                reportLine[1] += pos

        query = self.selectData(params)
        processQuery(query)

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        title = u'Отчет для ЗП'
        cursor.insertText(title)
        self.setTitle(title)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(description)
        cursor.insertBlock()

        tableColumns = [
            ('60%', [u'Врач / Автор'], CReportBase.AlignLeft),
            ('20%', [u'Кол-во УЕТ'], CReportBase.AlignRight),
            ('20%', [u'Кол-во посещений'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)
        totalByReport = [0] * reportRowSize
        totalByFinance = [0] * reportRowSize
        totalByPersonSNILS = [0] * reportRowSize
        colsShift = 1
        prevPersonWithSpeciality = None
        personWithSpeciality = None
        person = None
        prevPerson = None
        keys = reportData.keys()
        keys.sort()
        for key in keys:
            person = key[0]
            personWithSpeciality = key[1]
            createPerson = key[2]

            if prevPersonWithSpeciality != personWithSpeciality:
                if prevPersonWithSpeciality is not None:
                    row = table.addRow()
                    table.setText(row, 0, u'Итого по %s' % prevPersonWithSpeciality)
                    for col in xrange(reportRowSize - 2):
                        table.setText(row, col + colsShift, totalByFinance[col])
                        totalByReport[col] = totalByReport[col] + totalByFinance[col]
                    totalByFinance = [0] * reportRowSize

            if self.groupByPersonSnils:
                if prevPerson != person:
                    if prevPerson is not None:
                        row = table.addRow()
                        table.setText(row, 0, u'Итого по %s' % prevPerson[0], CReportBase.TableHeader)
                        for col in xrange(reportRowSize - 2):
                            table.setText(row, col + colsShift, totalByPersonSNILS[col])
                        totalByPersonSNILS = [0] * reportRowSize

            if self.groupByPersonSnils:
                if prevPerson != person:
                    row = table.addRow()
                    table.setText(row, 0, person[0], CReportBase.TableHeader)
                    table.mergeCells(row, 0, 1, reportRowSize )
                    prevPerson = person

            if prevPersonWithSpeciality != personWithSpeciality:
                row = table.addRow()
                table.setText(row, 0, personWithSpeciality, CReportBase.TableHeader)
                table.mergeCells(row, 0, 1, reportRowSize )
                prevPersonWithSpeciality = personWithSpeciality

            reportLine = reportData[key]
            if reportLine[0] or reportLine[1]:
                row = table.addRow()
                table.setText(row, 0, createPerson)


                for col in xrange(reportRowSize - 2):
                    table.setText(row, col + colsShift, reportLine[col])
                    totalByFinance[col] = totalByFinance[col] + reportLine[col]
                    if self.groupByPersonSnils:
                        totalByPersonSNILS[col] += reportLine[col]

        if personWithSpeciality is not None:
            row = table.addRow()
            table.setText(row, 0, u'Итого по %s' % personWithSpeciality)
            for col in xrange(reportRowSize - 2):
                table.setText(row, col + colsShift, totalByFinance[col])
                totalByReport[col] = totalByReport[col] + totalByFinance[col]

        if self.groupByPersonSnils:
            if person is not None:
                row = table.addRow()
                table.setText(row, 0, u'Итого по %s' % person[0], CReportBase.TableHeader)
                for col in xrange(reportRowSize - 2):
                    table.setText(row, col + colsShift, totalByPersonSNILS[col])


        row = table.addRow()
        table.setText(row, 0, u'Итого')
        for col in xrange(reportRowSize - 2):
            table.setText(row, col + colsShift, totalByReport[col])

        return doc


class CReportStomPersonSalaryEx(CReportStomPersonSalary):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CReportStomPersonSalary.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        self.hideWidgets(result)
        result.setGroupByPersonSnilsVisible(True)
        result.shrink()
        result.loadPrefs()
        return result

    def hideWidgets(self, result):
        result.grpdatetype.setEnabled(False)
        result.grpdatetype.setVisible(False)
        result.lblNoscheta.setVisible(False)
        result.cmbNoscheta.setVisible(False)
        result.lblAccountType.setVisible(False)
        result.cmbAccountType.setVisible(False)
        result.lblScheta.setVisible(False)
        result.cmbScheta.setVisible(False)
        result.lblPayer.setVisible(False)
        result.cmbPayer.setVisible(False)
        result.cbPrice.setVisible(False)
        result.cbCashPayments.setVisible(False)
        result.lblFinance.setVisible(False)
        result.cmbFinance.setVisible(False)
        result.lblContract.setVisible(False)
        result.cmbContract.setVisible(False)
        result.lblVidPom.setVisible(False)
        result.cmbVidPom.setVisible(False)
        result.lblRazrNas.setVisible(False)
        result.cmbRazrNas.setVisible(False)
        result.lbltypePay.setVisible(False)
        result.cmbtypePay.setVisible(False)
        result.lblPurpose.setVisible(False)
        result.cmbPurpose.setVisible(False)
        result.lblEventType.setVisible(False)
        result.cmbEventType.setVisible(False)

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CReportStomPersonSalary.build(self, '\n'.join(self.getDescription(params)), params)
