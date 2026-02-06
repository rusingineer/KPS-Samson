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
from PyQt4 import QtCore
from PyQt4.QtCore import QDate

from library.Utils import forceString, forceInt, forceDate, forceDouble

from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable

from Orgs.Utils                 import getOrgStructureDescendants

from Reports.Ui_NomenclatureReportSetup import Ui_NomenclatureReportDialog


class CNomenclatureReportDialog(QtGui.QDialog, Ui_NomenclatureReportDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle(u'Параметры отчёта')
        self.cmbNomenclatureClass.setTable('rbNomenclatureClass', order='name')
        self.cmbNomenclatureKind.setTable('rbNomenclatureKind', order='name')
        self.cmbNomenclatureType.setTable('rbNomenclatureType', order='name')
        self.setDatePeriodVisible(False)
        self.setDatesVisible(True)
        self.setMonthVisible(False)
        self.setMonthOptionVisible(False)
        self.setDatesOptionVisible(False)
        self.setClientIdVisible(False)
        self.setOrgStructureVisible(True)
        self.setNomenclatureVisible(True)
        self.setNomenclatureTypeVisible(False)
        self.setSignaVisible(True)
        self.setSupplierVisible(False)
        self.setSupplierOrgVisible(False)
        self.setReceiverVisible(False)
        self.setReceiverPersonVisible(False)
        self.setFinanceVisible(False)
        self.setChkCountingTotalVisible(False)


    def setChkCountingTotalVisible(self, value):
        self.isChkCountingTotalVisible = value
        self.chkCountingTotal.setVisible(value)


    def setNomenclatureTypeVisible(self, value):
        self.isNomenclatureTypeVisible = value
        self.lblNomenclatureClass.setVisible(value)
        self.cmbNomenclatureClass.setVisible(value)
        self.lblNomenclatureKind.setVisible(value)
        self.cmbNomenclatureKind.setVisible(value)
        self.lblNomenclatureType.setVisible(value)
        self.cmbNomenclatureType.setVisible(value)


    def setDatePeriodVisible(self, value):
        self.datePeriodVisible = value
        self.lblDatePeriod.setVisible(value)
        self.cmbDatePeriod.setVisible(value)


    def setDatesVisible(self, value):
        self.datesVisible = value
        self.lblBegDate.setVisible(value)
        self.edtBegDate.setVisible(value)
        self.edtBegTime.setVisible(value)
        self.lblEndDate.setVisible(value)
        self.edtEndDate.setVisible(value)
        self.edtEndTime.setVisible(value)

    def setDatesOptionVisible(self, value):
        self.datesOptionVisible = value
        self.chkBegDate.setVisible(value)
        self.edtBegDateOption.setVisible(value)
        self.chkEndDate.setVisible(value)
        self.edtEndDateOption.setVisible(value)

    def setMonthVisible(self, value):
        self.monthVisible = value
        self.lblMonth.setVisible(value)
        self.edtMonth.setVisible(value)

    def setMonthOptionVisible(self, value):
        self.monthOptionVisible = value
        self.chkMonth.setVisible(value)
        self.edtMonthOption.setVisible(value)

    def setClientIdVisible(self, value):
        self.clientIdVisible = value
        self.lblClientId.setVisible(value)
        self.edtClientId.setVisible(value)

    def setOrgStructureVisible(self, value):
        self.orgStructureVisible = value
        self.lblOrgStructure.setVisible(value)
        self.cmbOrgStructure.setVisible(value)

    def setNomenclatureVisible(self, value):
        self.nomenclatureVisible = value
        self.lblNomenclature.setVisible(value)
        self.cmbNomenclature.setVisible(value)

    def setSignaVisible(self, value):
        self.signaVisible = value
        self.lblSigna.setVisible(value)
        self.edtSigna.setVisible(value)

    def setSupplierVisible(self, value):
        self.supplierVisible = value
        self.lblSupplier.setVisible(value)
        self.cmbSupplier.setVisible(value)

    def setSupplierOrgVisible(self, value):
        self.supplierOrgVisible = value
        self.lblSupplierOrg.setVisible(value)
        self.cmbSupplierOrg.setVisible(value)

    def setReceiverVisible(self, value):
        self.receiverVisible = value
        self.lblReceiver.setVisible(value)
        self.cmbReceiver.setVisible(value)

    def setReceiverPersonVisible(self, value):
        self.receiverPersonVisible = value
        self.lblReceiverPerson.setVisible(value)
        self.cmbReceiverPerson.setVisible(value)

    def setFinanceVisible(self, value):
        self.financeVisible = value
        self.lblFinance.setVisible(value)
        self.cmbFinance.setVisible(value)
        self.cmbFinance.setTable('rbFinance', True)

    def setOnlyExists(self, value):
        self.cmbNomenclature.setOnlyExists(value)

    def setParams(self, params):
        if self.monthVisible:
            self.edtMonth.setDate(params.get('month', QtCore.QDate.currentDate()))
        if self.datePeriodVisible:
            self.cmbDatePeriod.setCurrentIndex(params.get('datePeriod', 0))
        if self.datesVisible:
            self.edtBegDate.setDate(params.get('begDate', QtCore.QDate.currentDate()))
            self.edtBegTime.setTime(params.get('begTime', QtCore.QTime(0, 0)))
            self.edtEndDate.setDate(params.get('endDate', QtCore.QDate.currentDate()))
            self.edtEndTime.setTime(params.get('endTime', QtCore.QTime(23, 59)))
        if self.monthOptionVisible:
            self.edtMonthOption.setDate(params.get('monthOption', QtCore.QDate.currentDate()))
            self.chkMonth.setChecked(params.get('monthChecked', True))
        if self.datesOptionVisible:
            self.edtBegDateOption.setDate(params.get('begDateOption', QtCore.QDate.currentDate()))
            self.edtEndDateOption.setDate(params.get('endDateOption', QtCore.QDate.currentDate()))
            self.chkBegDate.setChecked(params.get('begDateChecked', False))
            self.chkEndDate.setChecked(params.get('endDateChecked', False))
        if self.clientIdVisible:
            self.edtClientId.setText(params.get('clientId', ''))
        if self.orgStructureVisible:
            self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        if self.nomenclatureVisible:
            self.cmbNomenclature.setValue(params.get('nomenclatureId', None))
        if self.isNomenclatureTypeVisible:
            self.cmbNomenclatureClass.setValue(params.get('nomenclatureClassId', None))
            self.cmbNomenclatureKind.setValue(params.get('nomenclatureKindId', None))
            self.cmbNomenclatureType.setValue(params.get('nomenclatureTypeId', None))
        if self.isChkCountingTotalVisible:
            self.chkCountingTotal.setChecked(params.get('chkCountingTotal', False))
        if self.signaVisible:
            self.edtSigna.setText(params.get('signa', u''))
        if self.supplierVisible:
            self.cmbSupplier.setValue(params.get('supplierId', None))
        if self.supplierOrgVisible:
            self.cmbSupplierOrg.setValue(params.get('supplierOrgId', None))
        if self.receiverVisible:
            self.cmbReceiver.setValue(params.get('receiverId', None))
        if self.receiverPersonVisible:
            self.cmbReceiverPerson.setValue(params.get('receiverPersonId', None))
        if self.financeVisible:
            self.cmbFinance.setValue(params.get('financeId', None))

    def params(self):
        result = {}
        if self.monthVisible:
            result['month'] = self.edtMonth.date()
        if self.datePeriodVisible:
            result['datePeriod'] = self.cmbDatePeriod.currentIndex()
        if self.datesVisible:
            result['begDate'] = self.edtBegDate.date()
            result['begTime'] = self.edtBegTime.time()
            result['endDate'] = self.edtEndDate.date()
            result['endTime'] = self.edtEndTime.time()
        if self.monthOptionVisible:
            result['monthOption'] = self.edtMonthOption.date()
            result['monthChecked'] = self.chkMonth.isChecked()
        if self.datesOptionVisible:
            result['begDateChecked'] = self.chkBegDate.isChecked()
            result['endDateChecked'] = self.chkEndDate.isChecked()
            result['begDateOption'] = self.edtBegDateOption.date()
            result['endDateOption'] = self.edtEndDateOption.date()
        if self.clientIdVisible:
            result['clientId'] = unicode(self.edtClientId.text())
        if self.orgStructureVisible:
            result['orgStructureId'] = self.cmbOrgStructure.value()
        if self.nomenclatureVisible:
            result['nomenclatureId'] = self.cmbNomenclature.value()
        if self.isNomenclatureTypeVisible:
            result['nomenclatureClassId'] = self.cmbNomenclatureClass.value()
            result['nomenclatureKindId'] = self.cmbNomenclatureKind.value()
            result['nomenclatureTypeId'] = self.cmbNomenclatureType.value()
        if self.isChkCountingTotalVisible:
            result['chkCountingTotal'] = self.chkCountingTotal.isChecked()
        if self.signaVisible:
            result['signa'] = unicode(self.edtSigna.text())
        if self.supplierVisible:
            result['supplierId'] = self.cmbSupplier.value()
        if self.supplierOrgVisible:
            result['supplierOrgId'] = self.cmbSupplierOrg.value()
        if self.receiverVisible:
            result['receiverId'] = self.cmbReceiver.value()
        if self.receiverPersonVisible:
            result['receiverPersonId'] = self.cmbReceiverPerson.value()
        if self.financeVisible:
            result['financeId'] = self.cmbFinance.value()
        return result


def selectData(params, customDate=None):
    if customDate:
        begDate = customDate
    else:
        begDate = params.get('begDate', QDate())
    signa = params.get('signa', None)
    nomenclatureId = params.get('nomenclatureId', None)
    orgStructureId = params.get('orgStructureId', None)

    orgStructureIdList = None
    if orgStructureId:
        orgStructureIdList = getOrgStructureDescendants(orgStructureId)

    db = QtGui.qApp.db
    tableActionExecutionPlanItem        = db.table('ActionExecutionPlan_Item')
    tableActionExecutionPlan    = db.table('ActionExecutionPlan')
    tableActionExecutionPlanItemNomenclature        = db.table('ActionExecutionPlan_Item_Nomenclature')
    tableRbNomenclature    = db.table('rbNomenclature')

    cond = [db.joinOr([db.joinAnd([tableActionExecutionPlanItem['date'].ge(begDate),
                    tableActionExecutionPlanItem['date'].lt(begDate.addDays(1))]),
                    db.joinAnd([tableActionExecutionPlanItem['executedDatetime'].isNull(),
                    tableActionExecutionPlanItem['date'].lt(begDate.addDays(1))])]),
                ]

    cols = [    tableRbNomenclature['name'].alias('nomenclatureName'),
                    tableRbNomenclature['producer'].alias('producer'),
                    u'''(SELECT CONCAT_WS(' ', Client.`lastName`, Client.`firstName`, Client.`patrName`)
                        FROM Client
                        LEFT JOIN Event ON Event.client_id = Client.id
                        LEFT JOIN Action ON Action.event_id = Event.id
                        LEFT JOIN ActionExecutionPlan_Item AS AEPI ON AEPI.action_id = Action.id
                        WHERE AEPI.master_id = ActionExecutionPlan_Item.master_id AND Client.id IS NOT NULL AND Action.deleted = 0
                        LIMIT 1) AS clientName''',
                    tableActionExecutionPlanItem['date'].alias('date'),
                    tableActionExecutionPlanItem['master_id'].alias('master_id'),
                    u'''    IF(COUNT(ActionExecutionPlan_Item.master_id) > 1
                    AND (GROUP_CONCAT(DATE_FORMAT(ActionExecutionPlan_Item.time, '%H:%i')) = '00:00'
                    OR GROUP_CONCAT(DATE_FORMAT(ActionExecutionPlan_Item.time, '%H:%i')) IS NULL),
                    NULL,
                    IF(COUNT(ActionExecutionPlan_Item.master_id) > 1,
                        CONCAT(IF(COUNT(DISTINCT ActionExecutionPlan_Item.time) < COUNT(ActionExecutionPlan_Item_Nomenclature.id),
                                    '00:00,',
                                    ''),
                        GROUP_CONCAT(DATE_FORMAT(ActionExecutionPlan_Item.time, '%H:%i') order by DATE_FORMAT(ActionExecutionPlan_Item.time, '%H:%i'))
                                ),
                        '00:00')) AS time''',
                    u'''GROUP_CONCAT(DISTINCT ActionExecutionPlan_Item_Nomenclature.dosage  ORDER BY ActionExecutionPlan_Item_Nomenclature.id) AS dosage''',
                    u'''COUNT(ActionExecutionPlan_Item_Nomenclature.id) AS aliquoticity''',
                    u'''SUM(ActionExecutionPlan_Item_Nomenclature.dosage) AS sumDosage''',
                    u'''(SELECT COUNT(AEPIC.master_id) FROM ActionExecutionPlan_Item AS AEPIC WHERE
                        AEPIC.master_id = ActionExecutionPlan_Item.master_id) / COUNT(ActionExecutionPlan_Item_Nomenclature.id) AS courseDays''',
                    u'''(SELECT min(date) FROM ActionExecutionPlan_Item AS AEP WHERE
                        AEP.master_id = ActionExecutionPlan_Item.master_id
                        AND AEP.date IS NOT NULL) AS firstCourseDay''',
                    u'''(SELECT MAX(date) FROM ActionExecutionPlan_Item AS AEP WHERE
                        AEP.master_id = ActionExecutionPlan_Item.master_id
                        AND AEP.executedDatetime IS NOT NULL) as lastDoneDate''',
                    u''' (SELECT
                        SUM(IF(date = DATE('%s'), 1, 0))
                    FROM
                        ActionExecutionPlan_Item AS AEP
                    WHERE
                        AEP.master_id = ActionExecutionPlan_Item.master_id
                        AND AEP.date = DATE('%s')) AS currentDateAvialable'''%(forceString(begDate.toString('yyyy-MM-dd')), forceString(begDate.toString('yyyy-MM-dd'))),
                    u'''IF(COUNT(ActionExecutionPlan_Item.executedDatetime IS NOT NULL) = ActionExecutionPlan_Item.id, 1, 0) AS isExecuted''',
                    u'''(SELECT
                            GROUP_CONCAT(ActionProperty_String.value)
                        FROM
                            Action
                                LEFT JOIN
                            ActionExecutionPlan_Item AS AEPI ON AEPI.action_id = Action.id
                                LEFT JOIN
                            ActionProperty ON ActionProperty.action_id = Action.id
                                LEFT JOIN
                            ActionType ON ActionType.id = Action.actionType_id
                                LEFT JOIN
                            ActionPropertyType ON ActionPropertyType.actionType_id = ActionType.id
                                INNER JOIN
                            ActionProperty_String ON ActionProperty.id = ActionProperty_String.id
                        WHERE
                            AEPI.master_id = ActionExecutionPlan_Item.master_id
                                AND Action.deleted = 0
                                AND ActionPropertyType.name LIKE '%применения%') AS signa''',
                        u'''(SELECT
                                DATE(Action.begDate)
                            FROM
                                Action
                                    LEFT JOIN
                                ActionExecutionPlan_Item AS AEPI ON AEPI.action_id = Action.id
                            WHERE
                                AEPI.master_id = ActionExecutionPlan_Item.master_id
                                    AND Action.deleted = 0
                                    AND Action.status = 3) AS canceledDate''',
                        u'''    (SELECT
            MAX(AAEP.begDate)
        FROM
            ActionExecutionPlan_Item AS AEP
                LEFT JOIN
            Action AS AAEP ON AAEP.id = AEP.action_id
        WHERE
            AEP.master_id = ActionExecutionPlan_Item.master_id
                AND AAEP.status IN (0 , 5)) AS lastOpenActionDate'''
                ]

    havingCond = u'''clientName IS NOT NULL AND (canceledDate is NULL OR canceledDate > DATE('%s'))'''%(forceString(begDate.toString('yyyy-MM-dd')))

    if signa:
        havingCond = havingCond + u''' AND signa LIKE '%%%s%%' '''%(signa)
    if nomenclatureId:
        cond.append(tableActionExecutionPlanItemNomenclature['nomenclature_id'].eq(nomenclatureId))
    if orgStructureIdList:
        havingCond = havingCond + u' AND orgStrId in (%s)'%', '.join(str(x) for x in orgStructureIdList)
        cols.append(u'''(SELECT
            OrgStructure.id
        FROM
            Client
                LEFT JOIN
            Event ON Event.client_id = Client.id
                LEFT JOIN
            Action ON Action.event_id = Event.id
                LEFT JOIN
            ActionExecutionPlan_Item AS AEPI ON AEPI.action_id = Action.id
                LEFT JOIN
            Action AS ACOR ON ACOR.event_id = Action.event_id
                LEFT JOIN
            ActionProperty ON ActionProperty.action_id = ACOR.id
                LEFT JOIN
            ActionType ON ActionType.id = ACOR.actionType_id
                INNER JOIN
            ActionProperty_OrgStructure ON ActionProperty.id = ActionProperty_OrgStructure.id
                INNER JOIN
            OrgStructure ON ActionProperty_OrgStructure.value = OrgStructure.id
        WHERE
            AEPI.master_id = ActionExecutionPlan_Item.master_id
                AND Action.deleted = 0
                AND OrgStructure.id IS NOT NULL
                AND ActionType.flatCode = 'moving'
        LIMIT 1) AS orgStrId''')


    groupBy = u'''ActionExecutionPlan_Item.date ,
                            rbNomenclature.id ,
                            ActionExecutionPlan_Item.master_id
                            HAVING %s
                            ORDER BY rbNomenclature.name,
                            (SELECT MIN(date) FROM ActionExecutionPlan_Item AS AEP
                            WHERE AEP.master_id = ActionExecutionPlan_Item.master_id
                            AND AEP.date IS NOT NULL),
                            ActionExecutionPlan_Item.master_id, ActionExecutionPlan_Item.date'''%havingCond



    queryTable = tableActionExecutionPlanItem
    queryTable = queryTable.leftJoin(tableActionExecutionPlan, tableActionExecutionPlan['id'].eq(tableActionExecutionPlanItem['master_id']))
    queryTable = queryTable.leftJoin(tableActionExecutionPlanItemNomenclature, tableActionExecutionPlanItemNomenclature['actionExecutionPlan_item_id'].eq(tableActionExecutionPlanItem['id']))
    queryTable = queryTable.leftJoin(tableRbNomenclature, tableRbNomenclature['id'].eq(tableActionExecutionPlanItemNomenclature['nomenclature_id']))

    stmt = db.selectStmtGroupBy(queryTable, cols, cond, groupBy)
    query = db.query(stmt)

    result = []
    prevDate = None
    prevNomenclature = None
    sumNomDosage = 0
    setCourseFirstDate = False
    courseKey = None
    while query.next():
        record = query.record()
        nomenclatureName = forceString(record.value('nomenclatureName'))
        producer = forceString(record.value('producer'))
        clientName = forceString(record.value('clientName'))
        date = forceDate(record.value('date'))
        time = forceString(record.value('time'))
        dosage = forceString(record.value('dosage'))
        signa = forceString(record.value('signa'))
        aliquoticity = forceInt(record.value('aliquoticity'))
        sumDosage = forceDouble(record.value('sumDosage'))
        courseDays = forceDouble(record.value('courseDays'))
        firstCourseDay = forceDate(record.value('firstCourseDay'))
        lastDoneDate = forceDate(record.value('lastDoneDate')) if forceDate(record.value('lastDoneDate')) <=begDate else None
        lastOpenActionDate = forceDate(record.value('lastOpenActionDate'))
        isExecuted = forceInt(record.value('isExecuted'))
        masterId = forceInt(record.value('master_id'))
        currentDateAvialable = forceInt(record.value('currentDateAvialable'))


        if ((courseKey and courseKey == masterId and isExecuted == 0)
            or (currentDateAvialable>=1 and courseKey != masterId and date<begDate)):
            if date == begDate:
                if (prevDate != date or prevNomenclature!= nomenclatureName) and prevDate is not None and sumNomDosage!=0:
                    if result[-1][0] == u'NOMENCLATURE_RESULT':
                        result.pop()
                    result.append(('NOMENCLATURE_RESULT',
                    {
                        'nomenclatureName': prevNomenclature if prevNomenclature else nomenclatureName,
                        'date': formatDate(prevDate) if prevDate else formatDate(date),
                        'sumDosage' : sumNomDosage,
                    }))
                    sumNomDosage = 0
                if date>=begDate:
                    sumNomDosage += sumDosage
                result.append(('ROW_RESULT',
                            {
                                'nomenclatureName': nomenclatureName,
                                'producer': producer,
                                'clientName': clientName,
                                'dosage' : dosage,
                                'signa' : signa,
                                'date': formatDate(date),
                                'firstCourseDay': formatDate(firstCourseDay),
                                'courseDays': courseDays,
                                'time': time,
                                'sumDosage' : sumDosage,
                                'aliquoticity': aliquoticity,
                                'lastDoneDate': lastDoneDate,
                                'lastOpenActionDate' : lastOpenActionDate,
                                'isExecuted': isExecuted
                            }))
            else:
                setCourseFirstDate = True
                courseKey = masterId
                continue
        else:
            if (prevDate != date or prevNomenclature!= nomenclatureName) and prevDate is not None and sumNomDosage!=0:
                result.append(('NOMENCLATURE_RESULT',
                {
                    'nomenclatureName': prevNomenclature if prevNomenclature else nomenclatureName,
                    'date': formatDate(prevDate) if prevDate else formatDate(date),
                    'sumDosage' : sumNomDosage,
                }))
                sumNomDosage = 0
            if date>=begDate:
                sumNomDosage += sumDosage
            #if date<=begDate and not currentDateAvialable:
            result.append(('ROW_RESULT',
                        {
                            'nomenclatureName': nomenclatureName,
                            'producer': producer,
                            'clientName': clientName,
                            'dosage' : dosage,
                            'signa' : signa,
                            'date': formatDate(date),
                            'firstCourseDay': formatDate(firstCourseDay) if date<begDate or (setCourseFirstDate and courseKey == masterId) else None,
                            'courseDays': courseDays,
                            'time': time,
                            'sumDosage' : sumDosage,
                            'aliquoticity': aliquoticity,
                            'lastDoneDate': lastDoneDate,
                            'lastOpenActionDate' : lastOpenActionDate,
                            'isExecuted': isExecuted
                        }))
            setCourseFirstDate = False

        courseKey = masterId
        prevDate = date
        prevNomenclature = nomenclatureName
    if sumNomDosage!=0:
        result.append(('NOMENCLATURE_RESULT',
                {
                    'nomenclatureName': prevNomenclature,
                    'date': formatDate(prevDate),
                    'sumDosage' : sumNomDosage,
                }))


    return result


def formatDate(date):
    return forceDate(date).toString('dd.MM.yyyy') if date else ''


class CPlannedClientInvoiceNomenclaturesReport(CReport):
    def __init__(self, parent = None):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет о выдаче ЛС на выбранный период')

    def getSetupDialog(self, parent):
        result = CNomenclatureReportDialog(parent)
        result.setOnlyExists(True)
        return result

    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        tableColumns = [
            ('5%', [u'№'], CReportBase.AlignLeft),
            ('20%', [u'Наименование ЛСиИМН'], CReportBase.AlignLeft),
            ('5%', [u'Производитель'], CReportBase.AlignLeft),
            ('20%', [u'Пациент'], CReportBase.AlignLeft),
            ('5%', [u'Кол-во'], CReportBase.AlignRight),
            ('10%', [u'Дата'], CReportBase.AlignRight),
            ('5%', [u'Время'], CReportBase.AlignRight),
            ('5%', [u'Кратность'], CReportBase.AlignRight),
            ('5%', [u'Кол-во на 1 прием'], CReportBase.AlignRight),
            ('5%', [u'Способ приема'], CReportBase.AlignRight),
            ('15%', [u'Комментарий'], CReportBase.AlignLeft)
        ]

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        table = createTable(cursor, tableColumns)
        data = []

        for i in range(endDate.toJulianDay()-begDate.toJulianDay()+1):
            data.append(('DATE_DATA',
            {
                'date': formatDate(begDate.addDays(i)),
            }))
            dateData = selectData(params, begDate.addDays(i))
            data.extend(dateData)

        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        rowNumber = 1

        for dataType, values in data:
            row = table.addRow()
            if dataType == 'DATE_DATA':
                table.mergeCells(row, 0, 1, len(tableColumns))
                table.setText(row, 0, u"Информация по назначениям на %s" % (values['date']),
                                    charFormat = boldChars, blockFormat = CReportBase.AlignCenter)
                currentReportDate = values['date']
            elif dataType == 'NOMENCLATURE_RESULT':
                table.mergeCells(row, 0, 1, len(tableColumns))
                table.setText(row, 0, u"%s \"%s\": %s" % (values['date'], values['nomenclatureName'], values['sumDosage']))
            else:
                table.setText(row, 0, rowNumber)
                table.setText(row, 1, values['nomenclatureName'])
                table.setText(row, 2, values['producer'])
                table.setText(row, 3, values['clientName'])
                if values['date']==currentReportDate:
                    table.setText(row, 4, values['sumDosage'])
                    table.setText(row, 5, values['date'])
                    table.setText(row, 6, values['time'])
                    table.setText(row, 7, values['aliquoticity'])
                    table.setText(row, 8, values['dosage'])
                    table.setText(row, 9, values['signa'])
                else:
                    table.setText(row, 4, u'')
                    table.setText(row, 5, u'')
                    table.setText(row, 6, u'')
                    table.setText(row, 7, u'')
                    table.setText(row, 8, u'')
                    table.setText(row, 9, u'')

                if values['lastDoneDate'] and values['lastOpenActionDate']:
                    table.setText(row, 10, u'Списание ЛСиИМН не выполнено с %s'%formatDate(values['lastOpenActionDate']))
                elif values['firstCourseDay']:
                    table.setText(row, 10, u'Списание ЛСиИМН не начато с %s'%values['firstCourseDay'])

                rowNumber += 1

        return doc
