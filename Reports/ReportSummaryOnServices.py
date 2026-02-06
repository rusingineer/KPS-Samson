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
from PyQt4.QtCore import pyqtSignature, QDate, QDateTime, QLocale

from library.Utils       import firstMonthDay, forceBool, forceDouble, forceRef, forceString, lastMonthDay

#from Events.ActionStatus import CActionStatus
from Orgs.Utils          import getOrgStructureFullName
from Reports.Report      import CReport
from Reports.ReportBase  import CReportBase, createTable


from Ui_ReportSummaryOnServicesDialog import Ui_ReportSummaryOnServicesDialog


class CReportSummaryOnServicesDialog(QtGui.QDialog, Ui_ReportSummaryOnServicesDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbActionTypeGroup.setClass(None)
        self.cmbActionTypeGroup.model().setLeavesVisible(False)
        self.cmbMedicalAidUnit.setTable('rbMedicalAidUnit', addNone=True)
        self.cmbFinance.setTable('rbFinance', addNone=True)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        chkClass = params.get('chkClass', False)
        self.chkClass.setChecked(chkClass)
        self.cmbClass.setCurrentIndex(params.get('class', 0))
        self.cmbActionTypeGroup.setValue(params.get('actionTypeGroupId', None))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbMedicalAidUnit.setValue(params.get('unitId', None))
        self.chkVAT.setChecked(params.get('isVAT', False))
        self.cmbFinance.setValue(params.get('financeId', None))
        self.chkConfirmation.setChecked(params.get('confirmation', False))
        date = QDate.currentDate()
        self.edtConfirmationBegDate.setDate(params.get('confirmationBegDate', firstMonthDay(date)))
        self.edtConfirmationEndDate.setDate(params.get('confirmationEndDate', lastMonthDay(date)))
        self.cmbConfirmationType.setCurrentIndex(params.get('confirmationType', 0))
        self.cmbConfirmationPeriodType.setCurrentIndex(params.get('confirmationPeriodType', 0))


    def params(self):
        params = {}
        params['begDate']               = self.edtBegDate.date()
        params['endDate']               = self.edtEndDate.date()
        params['chkClass']              = self.chkClass.isChecked()
        if params['chkClass']:
            params['class']             = self.cmbClass.currentIndex()
            params['actionTypeGroupId'] = self.cmbActionTypeGroup.value()
        params['orgStructureId']        = self.cmbOrgStructure.value()
        params['orgStructureIdList']    = self.getOrgStructureIdList()
        params['personId']              = self.cmbPerson.value()
        params['unitId']                = self.cmbMedicalAidUnit.value()
        params['isVAT']                 = self.chkVAT.isChecked()
        params['financeId']             = self.cmbFinance.value()
        params['financeText']           = self.cmbFinance.currentText()
        params['confirmation']          = self.chkConfirmation.isChecked()
        params['confirmationType']      = self.cmbConfirmationType.currentIndex()
        params['confirmationPeriodType']= self.cmbConfirmationPeriodType.currentIndex()
        params['confirmationBegDate']   = self.edtConfirmationBegDate.date()
        params['confirmationEndDate']   = self.edtConfirmationEndDate.date()
        return params


    def getOrgStructureIdList(self):
        treeIndex = self.cmbOrgStructure._model.index(self.cmbOrgStructure.currentIndex(), 0, self.cmbOrgStructure.rootModelIndex())
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    @pyqtSignature('bool')
    def on_chkClass_clicked(self, bValue):
        if bValue:
            class_ = self.cmbClass.currentIndex()
        else:
            class_ = None
        self.cmbActionTypeGroup.setClass(class_)


    @pyqtSignature('int')
    def on_cmbClass_currentIndexChanged(self, index):
        self.cmbActionTypeGroup.setClass(index)


def selectData(params):
    db = QtGui.qApp.db

    begDate           = params.get('begDate', None)
    endDate           = params.get('endDate', None)
    class_            = params.get('class', None)
    actionTypeGroupId = params.get('actionTypeGroupId', None)
    if actionTypeGroupId:
        actionTypeGroupIdList = db.getDescendants('ActionType', 'group_id', actionTypeGroupId)
    else:
        actionTypeGroupIdList = None
    unitId            = params.get('unitId', None)
    orgStructureId    = params.get('orgStructureId', None)
    personId          = params.get('personId', None)
    financeId         = params.get('financeId', None)
    confirmation               = params.get('confirmation', False)
    confirmationBegDate        = params.get('confirmationBegDate', None)
    confirmationEndDate        = params.get('confirmationEndDate', None)
    confirmationType           = params.get('confirmationType', 0)
    confirmationPeriodType     = params.get('confirmationPeriodType', 0)
    orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId) if orgStructureId else []

    tableAction            = db.table('Action')
    tableActionType        = db.table('ActionType')
    tableContract          = db.table('Contract')
    tablePriceList         = db.table('Contract').alias('ContractPriceList')
    tableAccountItem       = db.table('Account_Item')
    tableAccount           = db.table('Account')
    tableEvent             = db.table('Event')
    tableEventType         = db.table('EventType')
    tablePerson            = db.table('vrbPersonWithSpeciality')
    tableRBMedicalAidUnit  = db.table('rbMedicalAidUnit')
    tableOrgStructure      = db.table('OrgStructure')

    queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    queryTable = queryTable.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.innerJoin(tableContract, 'Contract.`id`=IF(Action.`contract_id`, Action.`contract_id`, Event.`contract_id`)')
    queryTable = queryTable.leftJoin(tablePriceList, tableContract['priceListExternal_id'].eq(tablePriceList['id']))
    queryTable = queryTable.innerJoin(tableAccountItem, tableAccountItem['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableAccount, tableAccount['id'].eq(tableAccountItem['master_id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
    queryTable = queryTable.leftJoin(tableRBMedicalAidUnit, tableRBMedicalAidUnit['id'].eq(tableAccountItem['unit_id']))
    queryTable = queryTable.leftJoin(tableOrgStructure, db.joinAnd([tableOrgStructure['id'].eq(tablePerson['orgStructure_id']),
                                                                    tableOrgStructure['deleted'].eq(0)]))
    cond = [tableAction['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableAccountItem['deleted'].eq(0),
            tableAccount['deleted'].eq(0),
            tableEventType['deleted'].eq(0)
            ]
    if financeId:
        cond.append(tableContract['finance_id'].eq(financeId))
    cond.append(tableAccount['date'].ge(begDate))
    cond.append(tableAccount['date'].lt(endDate.addDays(1)))
    if class_ is not None:
        cond.append(tableActionType['class'].eq(class_))
    if actionTypeGroupIdList:
        cond.append(tableActionType['group_id'].inlist(actionTypeGroupIdList))
    if orgStructureIdList:
        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
    if personId:
        cond.append(tablePerson['id'].eq(personId))
    cond.append('''Account_Item.visit_id IS NULL AND IF(Account_Item.action_id IS NOT NULL, Account_Item.action_id = Action.id, 1)''')

    cols = [tableOrgStructure['id'].alias('orgStructureId'),
            tableOrgStructure['name'].alias('orgStructureName'),
            tableRBMedicalAidUnit['id'].alias('unitId'),
            tableRBMedicalAidUnit['name'].alias('unitName'),
            tableAccountItem['amount'],
            tableAccountItem['price'],
            tableAccountItem['VAT'],
            tableAccountItem['sum'].alias('accountSum'),
            u'''EXISTS(SELECT rbFinance.id
                    FROM rbFinance
                    WHERE Contract.finance_id IS NOT NULL AND rbFinance.id = Contract.finance_id
                    AND rbFinance.code = 3) AS isDms''',
            u'''EXISTS(SELECT rbFinance.id
                    FROM rbFinance
                    WHERE Contract.finance_id IS NOT NULL AND rbFinance.id = Contract.finance_id
                    AND rbFinance.code = 4) AS isPaid''',
            u'''EXISTS(SELECT rbFinance.id
                    FROM rbFinance
                    WHERE Contract.finance_id IS NOT NULL AND rbFinance.id = Contract.finance_id
                    AND rbFinance.code = 5) AS isTargeted'''
           ]
    if unitId:
        cond.append(tableAccountItem['unit_id'].eq(unitId))
    if confirmation:
        cond.append(tableAccountItem['master_id'].eq(tableAccount['id']))
        if confirmationType == 0:
            cond.append(tableAccountItem['id'].isNull())
        elif confirmationType == 1:
            cond.append(tableAccountItem['date'].isNotNull())
            cond.append(tableAccountItem['number'].ne(''))
        elif confirmationType == 2:
            cond.append(tableAccountItem['date'].isNotNull())
            cond.append(tableAccountItem['number'].ne(''))
            cond.append(tableAccountItem['refuseType_id'].isNull())
        elif confirmationType == 3:
            cond.append(tableAccountItem['date'].isNotNull())
            cond.append(tableAccountItem['number'].ne(''))
            cond.append(tableAccountItem['refuseType_id'].isNotNull())
        if confirmationPeriodType:
            if confirmationBegDate:
                cond.append(tableAccountItem['date'].ge(confirmationBegDate))
            if confirmationEndDate:
                cond.append(tableAccountItem['date'].lt(confirmationEndDate.addDays(1)))
        else:
            if confirmationBegDate:
                cond.append(tableAccount['date'].ge(confirmationBegDate))
            if confirmationEndDate:
                cond.append(tableAccount['date'].lt(confirmationEndDate.addDays(1)))
    stmt = db.selectStmt(queryTable, cols, cond)
    query = db.query(stmt)
    return query


class CReportSummaryOnServices(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сводка по услугам')


    def getSetupDialog(self, parent):
        result = CReportSummaryOnServicesDialog(parent)
        result.setTitle(self.title())
        return result


    def build(self, params):
        query = selectData(params)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [
                        ('20%', [u'Ед.измерения'],         CReportBase.AlignLeft),
                        ('10%', [u'Кол-во платных услуг'], CReportBase.AlignRight),
                        ('10%', [u'Итого(сумма)'],         CReportBase.AlignRight),
                        ('10%', [u'Кол-во услуг по ДМС'],  CReportBase.AlignRight),
                        ('10%', [u'Итого(сумма)'],         CReportBase.AlignRight),
                        ('10%', [u'Кол-во целевых услуг'], CReportBase.AlignRight),
                        ('10%', [u'Итого(сумма)'],         CReportBase.AlignRight),
                        ('10%', [u'Всего кол-во'],         CReportBase.AlignRight),
                        ('10%', [u'Всего сумма'],          CReportBase.AlignRight)
                        ]
        table = createTable(cursor, tableColumns)
        reportSize = 8
        reportData = {}
        isVAT = params.get('isVAT', False)
        while query.next():
            record = query.record()
            orgStructureId   = forceRef(record.value('orgStructureId'))
            orgStructureName = forceString(record.value('orgStructureName'))
            unitId     = forceRef(record.value('unitId'))
            unitName   = forceString(record.value('unitName'))
            amount     = forceDouble(record.value('amount'))
            price      = forceDouble(record.value('price'))
            accountSum = forceDouble(record.value('accountSum'))
            VAT        = forceDouble(record.value('VAT'))
            isDms      = forceBool(record.value('isDms'))
            isPaid     = forceBool(record.value('isPaid'))
            isTargeted = forceBool(record.value('isTargeted'))
            reportUnitLine = reportData.setdefault((orgStructureId, orgStructureName), {})
            reportLine = reportUnitLine.setdefault((unitId, unitName), [0]*reportSize)
            if isVAT:
                accountSumIsVat = accountSum - (((price*VAT)/(100+VAT))*amount)
            else:
                accountSumIsVat = accountSum
            reportLine[6] += amount
            reportLine[7] += accountSumIsVat
            if isPaid:
                reportLine[0] += amount
                reportLine[1] += accountSumIsVat
            elif isDms:
                reportLine[2] += amount
                reportLine[3] += accountSumIsVat
            elif isTargeted:
                reportLine[4] += amount
                reportLine[5] += accountSumIsVat
        keysOrg = reportData.keys()
        keysOrg.sort(key=lambda x: x[1].lower())
        totalAll = [0]*reportSize
        totalUnits = {}
        idxFormat = [1, 3, 5, 7]
        locale = QLocale()
        for keyOrg in keysOrg:
            reportUnitLine = reportData.get(keyOrg, {})
            if reportUnitLine:
                i = table.addRow()
                table.setText(i, 0, keyOrg[1], CReportBase.TableTotal, CReportBase.AlignCenter)
                table.mergeCells(i, 0, 1, len(tableColumns))
                keysUnit = reportUnitLine.keys()
                keysUnit.sort(key=lambda x: x[1].lower())
                total = [0]*reportSize
                for keyUnit in keysUnit:
                    reportLine = reportUnitLine.get(keyUnit, [0]*reportSize)
                    unitLine = totalUnits.get(keyUnit, [0]*reportSize)
                    i = table.addRow()
                    table.setText(i, 0, keyUnit[1])
                    for col, values in enumerate(reportLine):
                        if col in idxFormat:
                            table.setText(i, col+1, locale.toString(float(values), 'f', 2))
                        else:
                            table.setText(i, col+1, values)
                        total[col] += values
                        totalAll[col] += values
                        unitLine[col] += values
                    totalUnits[keyUnit] = unitLine
                i = table.addRow()
                table.setText(i, 0, u'ИТОГО по отделению ' + (keyOrg[1] if keyOrg[1] else u'не задано'), CReportBase.TableTotal)
                for col, val in enumerate(total):
                    if col in idxFormat:
                        table.setText(i, col+1, locale.toString(float(val), 'f', 2), CReportBase.TableTotal)
                    else:
                        table.setText(i, col+1, val, CReportBase.TableTotal)
        if reportData:
            keysUnit = totalUnits.keys()
            keysUnit.sort(key=lambda x: x[1].lower())
            for keyUnit in keysUnit:
                i = table.addRow()
                table.setText(i, 0, u'ИТОГО ПО ЕДИНИЦЕ ИЗМЕРЕНИЯ ' + (keyUnit[1] if keyUnit[1] else u'не задано'), CReportBase.TableTotal)
                unitLine = totalUnits.get(keyUnit, [0]*reportSize)
                for col, val in enumerate(unitLine):
                    if col in idxFormat:
                        table.setText(i, col+1, locale.toString(float(val), 'f', 2), CReportBase.TableTotal)
                    else:
                        table.setText(i, col+1, val, CReportBase.TableTotal)
            i = table.addRow()
            table.setText(i, 0, u'ИТОГО ПО ВСЕМ ОТДЕЛЕНИЯМ ', CReportBase.TableTotal)
            for col, val in enumerate(totalAll):
                if col in idxFormat:
                    table.setText(i, col+1, locale.toString(float(val), 'f', 2), CReportBase.TableTotal)
                else:
                    table.setText(i, col+1, val, CReportBase.TableTotal)
        return doc


    def getDescription(self, params):
        begDate           = params.get('begDate', None)
        endDate           = params.get('endDate', None)
        class_            = params.get('class', None)
        actionTypeGroupId = params.get('actionTypeGroupId', None)
        unitId            = params.get('unitId', None)
        orgStructureId    = params.get('orgStructureId', None)
        personId          = params.get('personId', None)
        isVAT             = params.get('isVAT', False)
        confirmation      = params.get('confirmation', False)
        confirmationBegDate = params.get('confirmationBegDate', None)
        confirmationEndDate = params.get('confirmationEndDate', None)
        confirmationType    = params.get('confirmationType', 0)
        confirmationPeriodType = params.get('confirmationPeriodType', 0)
        rows = []
        if begDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endDate))
        if unitId:
            rows.append(u'Единица измерения: %s'%forceString(QtGui.qApp.db.translate('rbMedicalAidUnit', 'id', unitId, 'CONCAT(code, \' | \', name)')))
        if class_ is not None:
            rows.append(u'Класс типов действия: %s'%[u'статус', u'диагностика', u'лечение', u'прочие мероприятия'][class_])
        if actionTypeGroupId:
            rows.append(u'Группа типов действий: %s'%forceString(QtGui.qApp.db.translate('ActionType', 'id', actionTypeGroupId, 'CONCAT(code, \' | \', name)')))
        if orgStructureId:
            rows.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        if personId:
            rows.append(u'Исполнитель: %s' % forceRef(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name')))
        if unitId:
            rows.append(u'Единица измерения: %s'%forceString(QtGui.qApp.db.translate('rbMedicalAidUnit', 'id', unitId, 'CONCAT(code, \' | \', name)')))
        financeText = params.get('financeText', None)
        if financeText:
            rows.append(u'Тип финансирования: %s' % financeText)
        if confirmation:
            rows.append(u'Тип подтверждения: %s'%{0: u'не выставлено',
                                                  1: u'выставлено',
                                                  2: u'оплачено',
                                                  3: u'отказано'}.get(confirmationType, u'не выставлено'))
            rows.append(u'Период подтверждения: %s'%{0: u'по дате формирования счета',
                                                     1: u'по дате подтверждения оплаты'}.get(confirmationPeriodType, u'по дате формирования счета'))
            if confirmationBegDate:
                rows.append(u'Начало периода подтверждения: %s'%forceString(confirmationBegDate))
            if confirmationEndDate:
                rows.append(u'Окончание периода подтверждения: %s'%forceString(confirmationEndDate))
        if isVAT:
            rows.append(u'Без учёта НДС')
        rows.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        return rows

