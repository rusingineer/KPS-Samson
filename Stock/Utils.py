# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, SIGNAL, QVariant, pyqtSignal
from PyQt4.QtGui import QComboBox

from Reports.ReportBase import CReportBase, createTable

from library.InDocTable import CFloatInDocTableCol, CLocItemDelegate
from library.Utils      import (forceRef, forceString, forceInt, forceDouble, forceDate,
                                forceBool, formatName, formatSex, formatDate, forceStringEx)
from Users.Rights       import urAccessStockAgreeRequirements
from Reports.ReportView import CReportViewDialog

contractTypeDict = {
    1: u'купля продажа',
    2: u'комиссия',
    3: u'агентский договор',
    4: u'передача на безвозмездной основе',
    5: u'возврат контрактному производителю',
    6: u'государственное лекарственное обеспечение',
    7: u'договор консигнации',
    8: u'собственные средства',
}

reasonDestructionTypeDict = {
    0: u'не задано',
    1: u'недоброкачественный ЛП',
    2: u'контрафактный ЛП',
    3: u'фальсифицированный ЛП',
    4: u'ЛП, утративший потребительские свойства',
    5: u'ЛП с истекшим сроком годности',
    6: u'ЛП, отозванный производителем/держателем регистрационного удостоверения',
    7: u'ЛП, исключенный из Государственного реестра лекарственных средств'
}

destructionTypeDict = {
    0: u'не задано',
    1: u'по решению владельца',
    2: u'по решению Росздравнадзора',
    3: u'по решению суда',
}


def getNomenclatureAnalogies(nomenclatureId):
    db = QtGui.qApp.db
    tableNomenclature = db.table('rbNomenclature')
    tableNomenclature2 = db.table('rbNomenclature').alias('RBN2')
    table = tableNomenclature.leftJoin(tableNomenclature2,
                                       tableNomenclature2['analog_id'].eq(tableNomenclature['analog_id']))
    return db.getIdList(table,
                        tableNomenclature['id'],
                        db.joinAnd([
                                    tableNomenclature2['id'].eq(nomenclatureId),
                                    tableNomenclature['analog_id'].isNotNull(),
                                   ]
                                  )
                       )


def getRatio(nomenclatureId, oldUnitId, newUnitId):
    db = QtGui.qApp.db
    stockUnitId = forceRef(db.translate('rbNomenclature', 'id', nomenclatureId, 'defaultStockUnit_id'))
    if oldUnitId is None:
        oldUnitId = stockUnitId
    if newUnitId is None:
        newUnitId = stockUnitId
    if oldUnitId == newUnitId:
        return 1
    ratio = getNomenclatureUnitRatio(nomenclatureId, oldUnitId, newUnitId)
    return ratio


def getInventoryLastDate(orgStructureId):
    from Stock.StockModel   import CStockMotionType
    if not orgStructureId:
        return None
    db = QtGui.qApp.db
    tableMotion = db.table('StockMotion')
    tableMotionItem = db.table('StockMotion_Item')
    cols = [tableMotion['date']]
    cond = [tableMotion['type'].eq(CStockMotionType.inventory),
            tableMotion['supplier_id'].eq(orgStructureId),
            tableMotion['receiver_id'].eq(orgStructureId),
            tableMotion['deleted'].eq(0),
            tableMotionItem['deleted'].eq(0)
            ]
    queryTable = tableMotion.innerJoin(tableMotionItem, tableMotionItem['master_id'].eq(tableMotion['id']))
    record = db.getRecordEx(queryTable, cols, cond, order = u'StockMotion.date DESC')
    return forceDate(record.value('date')) if record else None


def setAgreementRequirementsStock(supplierId):
    isEnabled = False
    isRightAgreeRequirementsStock = QtGui.qApp.userHasRight(urAccessStockAgreeRequirements)
    accordingRequirementsStockType = forceInt(QtGui.qApp.preferences.appPrefs.get('accordingRequirementsStockType', QVariant()))
    if forceBool(accordingRequirementsStockType):
        if accordingRequirementsStockType == 1:
            if supplierId:
                db = QtGui.qApp.db
                table = db.table('OrgStructure')
                record = db.getRecordEx(table, table['id'], [table['id'].eq(supplierId), table['mainStocks'].eq(1), table['deleted'].eq(0)])
                isEnabled = bool(isRightAgreeRequirementsStock and (record and forceRef(record.value('id')) == supplierId))
        elif accordingRequirementsStockType == 2:
            isEnabled = isRightAgreeRequirementsStock and True
    return isEnabled


def getStockMotionNumberCounterId(motionType):
    db = QtGui.qApp.db
    orgStructureId = QtGui.qApp.currentOrgStructureId()
    tableRbStockMotionNumber = db.table('rbStockMotionNumber')
    cond = [tableRbStockMotionNumber['motionType'].eq(motionType),
                tableRbStockMotionNumber['orgStructure_id'].eq(orgStructureId)]
    record = db.getRecordEx(tableRbStockMotionNumber, 'counter_id', cond)
    counterId = forceInt(record.value('counter_id')) if record else None
    if counterId is None:
        condNull = [tableRbStockMotionNumber['motionType'].eq(motionType),
                tableRbStockMotionNumber['orgStructure_id'].isNull()]
        record = db.getRecordEx(tableRbStockMotionNumber, 'counter_id', condNull)
        counterId = forceInt(record.value('counter_id')) if record else None
    return counterId


def getStockMotionItemQuantityColumn(title=u'Кол-во', fieldName='qnt', width=12):
    return CFloatInDocTableCol(title, fieldName, width, low=1, high=65535, precision=QtGui.qApp.numberDecimalPlacesQnt())


def getBatchRecords(nomenclatureId, financeId=None, shelfTime=None, batch=None, filter=[], medicalAidKind=None, setShelfTimeCond=True, isStockUtilization=False, filterFor=None, isStrictMedicalAidKindId=False):
    db = QtGui.qApp.db
    havCond = [u'qnt>0'] if isStockUtilization else []
    if medicalAidKind is not None:
        if medicalAidKind == 0:
            havCond = [u'qnt>0', u'medicalAidKind_id is NULL', u'shelfTime >= CURDATE()']
        else:
            havCond = [u'qnt>0', u'medicalAidKind_id=%s OR medicalAidKind_id is NULL'%medicalAidKind, u'shelfTime >= CURDATE()']
    if not setShelfTimeCond and havCond and medicalAidKind is not None:
        havCond.pop()
        havCond.pop()
    stmt = getExistsNomenclatureStmt(   nomenclatureId,
                                        financeId=financeId,
                                        medicalAidKindId = medicalAidKind,
                                        batch=batch,
                                        shelfTime=shelfTime,
                                        filter = filter,
                                        otherHaving = havCond,
                                        filterFor=filterFor,
                                        isStrictMedicalAidKindId=isStrictMedicalAidKindId)
    res = []
    query = db.query(stmt)
    while query.next():
        res.append(query.record())
    return res


def getBatchSGTINRecords(nomenclatureId, financeId=None, shelfTime=None, batch=None, filter=[], medicalAidKind=None, setShelfTimeCond=True, isStockUtilization=False, filterFor=None, isStrictMedicalAidKindId=False):
    db = QtGui.qApp.db
    havCond = [u'qnt>0'] if isStockUtilization else []
    if medicalAidKind is not None:
        if medicalAidKind == 0:
            havCond = [u'qnt>0', u'medicalAidKind_id is NULL', u'shelfTime >= CURDATE()']
        else:
            havCond = [u'qnt>0', u'medicalAidKind_id=%s OR medicalAidKind_id is NULL'%medicalAidKind, u'shelfTime >= CURDATE()']
    if not setShelfTimeCond and havCond and medicalAidKind is not None:
        havCond.pop()
        havCond.pop()
    stmt = getExistsNomenclatureToSGTINStmt(nomenclatureId,
                                            financeId=financeId,
                                            medicalAidKindId = medicalAidKind,
                                            batch=batch,
                                            shelfTime=shelfTime,
                                            filter = filter,
                                            otherHaving = havCond,
                                            filterFor=filterFor,
                                            isStrictMedicalAidKindId=isStrictMedicalAidKindId)
    res = []
    query = db.query(stmt)
    while query.next():
        res.append(query.record())
    return res


def getBatchShelfTimeFinance(nomenclatureId, financeId=None, shelfTime=None, batch=None, filter=[], medicalAidKind=None, setShelfTimeCond=True, isStockUtilization=False, condHaving=[], isStockRequsition=False, orgStructureId=None, orderBy=None):
    recordBatch = None
    recordShelfTime = None
    recordFinance = None
    recordMedicalAidKind = None
    recordPrice = 0
    db = QtGui.qApp.db
    havCond = [u'qnt>0'] if isStockUtilization else []
    if medicalAidKind is not None:
        if medicalAidKind == 0:
            havCond = [u'qnt>0', u'medicalAidKind_id is NULL', u'shelfTime >= CURDATE()']
        else:
            havCond = [u'qnt>0', u'medicalAidKind_id=%s OR medicalAidKind_id is NULL'%medicalAidKind, u'shelfTime >= CURDATE()']
    if not setShelfTimeCond and havCond and medicalAidKind is not None:
        havCond.pop()
        havCond.pop()
    if condHaving:
        havCond.append(condHaving)
    stmt = getExistsNomenclatureStmt(   nomenclatureId,
                                        financeId=financeId,
                                        medicalAidKindId = medicalAidKind,
                                        batch=batch,
                                        orgStructureId=orgStructureId,
                                        shelfTime=shelfTime,
                                        filter = filter,
                                        orderBy = orderBy,
                                        otherHaving = havCond,
                                        isStockRequsition = isStockRequsition)
    query = db.query(stmt)
    if query.next():
        record = query.record()
        recordBatch = forceString(record.value('batch'))
        recordShelfTime = forceDate(record.value('shelfTime'))
        recordFinance = forceRef(record.value('finance_id'))
        recordMedicalAidKind = forceRef(record.value('medicalAidKind_id'))
        recordPrice = forceDouble(record.value('price'))
        return recordBatch, recordShelfTime, recordFinance, recordMedicalAidKind, recordPrice
    return recordBatch, recordShelfTime, recordFinance, recordMedicalAidKind, recordPrice


def getBatchShelfTimeFinanceQnt(nomenclatureId, financeId=None, shelfTime=None, batch=None, filter=[], medicalAidKind=None, setShelfTimeCond=True, isStockUtilization=False, condHaving=[], isStockRequsition=False, orgStructureId=None, orderBy=None, unitId=None, precision=-1):
    recordBatch = None
    recordShelfTime = None
    recordFinance = None
    recordMedicalAidKind = None
    recordPrice = 0
    recordQnt = 0
    db = QtGui.qApp.db
    havCond = [u'qnt>0'] if isStockUtilization else []
    if medicalAidKind is not None:
        if medicalAidKind == 0:
            havCond = [u'qnt>0', u'medicalAidKind_id is NULL', u'(shelfTime >= CURDATE() OR shelfTime is NULL)']
        else:
            havCond = [u'qnt>0', u'medicalAidKind_id=%s OR medicalAidKind_id is NULL'%medicalAidKind, u'(shelfTime >= CURDATE() OR shelfTime is NULL)']
    if not setShelfTimeCond and havCond and medicalAidKind is not None:
        havCond.pop()
        havCond.pop()
    if condHaving:
        havCond.append(condHaving)
    stmt = getExistsNomenclatureStmt(   nomenclatureId,
                                        financeId=financeId,
                                        medicalAidKindId = medicalAidKind,
                                        batch=batch,
                                        orgStructureId=orgStructureId,
                                        shelfTime=shelfTime,
                                        filter = filter,
                                        orderBy = orderBy,
                                        otherHaving = havCond,
                                        isStockRequsition = isStockRequsition)
    query = db.query(stmt)
    if query.next():
        record = query.record()
        recordNomenclatureId = forceRef(record.value('nomenclature_id'))
        recordBatch = forceString(record.value('batch'))
        recordShelfTime = forceDate(record.value('shelfTime'))
        recordFinance = forceRef(record.value('finance_id'))
        recordMedicalAidKind = forceRef(record.value('medicalAidKind_id'))
        recordPrice = forceDouble(record.value('price'))
        recordQnt = forceDouble(record.value('qnt'))
        if unitId is not None:
            if precision >= 0:
                recordQnt = round(applyNomenclatureUnitRatio(recordQnt, recordNomenclatureId, unitId), precision)
            else:
                recordQnt = applyNomenclatureUnitRatio(recordQnt, recordNomenclatureId, unitId)
        return recordBatch, recordShelfTime, recordFinance, recordMedicalAidKind, recordPrice, recordQnt
    return recordBatch, recordShelfTime, recordFinance, recordMedicalAidKind, recordPrice, recordQnt


def getRemainingHistory(nomenclatureId, **kwargs):
    orgStructureId = kwargs.get('orgStructureId')
    batch = kwargs.get('batch')
    financeId = kwargs.get('financeId')
    showDeleted = kwargs.get('showDeleted')
    onlyDeleted = kwargs.get('onlyDeleted')

    db = QtGui.qApp.db

    tableStockTrans = db.table('StockTrans')
    tableStockMotion = db.table('StockMotion')
    tableStockMotionItem = db.table('StockMotion_Item')

    stockTransCond = [
        db.joinOr([tableStockTrans['debNomenclature_id'].eq(nomenclatureId),
                   tableStockTrans['creNomenclature_id'].eq(nomenclatureId)])
    ]
    deletedCond = []
    isNegativeQnt = False

    if batch:
        stockTransCond.append(tableStockTrans['batch'].eq(batch))

    if financeId: #0012562:0044803
        if QtGui.qApp.controlSMFinance() == 1:
            stockTransCond.extend(
                [db.joinOr([tableStockTrans['debFinance_id'].eq(financeId), tableStockTrans['debFinance_id'].isNull()]),
                 db.joinOr([tableStockTrans['creFinance_id'].eq(financeId), tableStockTrans['creFinance_id'].isNull()])]
            )
        elif QtGui.qApp.controlSMFinance() == 2:
            stockTransCond.extend(
                [tableStockTrans['debFinance_id'].eq(financeId),
                 tableStockTrans['creFinance_id'].eq(financeId)]
            )

    if orgStructureId:
        isNegativeQnt = True
        stockTransCond.append(
            db.joinOr([tableStockTrans['debOrgStructure_id'].eq(orgStructureId),
                       tableStockTrans['creOrgStructure_id'].eq(orgStructureId)])
        )

    if onlyDeleted:
        deletedCond.append(tableStockMotion['deleted'].eq(1))
        deletedCond.append(tableStockMotionItem['deleted'].eq(1))

    if not showDeleted and not onlyDeleted:
        deletedCond.append(tableStockMotion['deleted'].eq(0))
        deletedCond.append(tableStockMotionItem['deleted'].eq(0))

    stmt = """
    SELECT
        StockMotion.id AS stockMotionId,
        StockMotion.number AS stockMotionNumber,
        StockMotion.date AS stockMotionDate,
        StockMotion.deleted AS stockMotionDeleted,
        StockMotion.type AS stockMotionType,
        StockMotion.supplier_id AS stockMotionSupplierId,
        StockMotion.supplierOrg_id AS stockMotionSupplierOrgId,
        StockMotion.receiver_id AS stockMotionReceiverId,
        StockMotion.client_id AS stockMotionClientId,
        StockMotion.modifyDatetime,
        StockMotion.modifyPerson_id AS modifyPersonId,
        StockMotion_Item.id AS stockMotionItemId,
        %(negQnt)s StockMotion_Item.qnt AS qnt,
        StockMotion_Item.deleted AS stockMotionItemDeleted,
        StockMotion_Item.finance_id AS stockMotionItemFinanceId,
        StockMotion_Item.batch AS stockMotionItemBatch,
        StockMotion_Item.shelfTime AS stockMotionItemShelfTime,
        rbNomenclature.code AS NomenclatureCode,
        rbNomenclature.name AS NomenclatureName,
        rbLfForm.code AS lfFormCode,
        rbLfForm.name AS lfFormName,
        rbUnit.code AS unitCode,
        rbUnit.name AS unitName
    FROM StockMotion
    INNER JOIN StockMotion_Item ON StockMotion_Item.master_id = StockMotion.id
    INNER JOIN rbNomenclature ON rbNomenclature.id = StockMotion_Item.nomenclature_id
    LEFT JOIN rbLfForm ON rbLfForm.id = rbNomenclature.lfForm_id
    LEFT JOIN rbUnit ON rbUnit.id = rbNomenclature.unit_id

    WHERE StockMotion_Item.id IN (
        SELECT StockTrans.stockMotionItem_id
        FROM StockTrans
        WHERE  %(stockTransCond)s
    )
    AND %(deletedCond)s
    ORDER BY StockMotion.id
    """% {'stockTransCond': db.joinAnd(stockTransCond),
          'deletedCond': db.joinAnd(deletedCond),
          'negQnt': '-' if isNegativeQnt else ''}

    query = db.query(stmt)
    result = []
    while query.next():
        result.append(query.record())
    return result


def showRemainingHistoryReport(records, parent=None):
    from Stock.StockMotion import stockMotionType
    db = QtGui.qApp.db

    doc = QtGui.QTextDocument()
    cursor = QtGui.QTextCursor(doc)
    cursor.setCharFormat(CReportBase.ReportTitle)
    cursor.insertText(u'История по остаткам')
    cursor.insertBlock()

    tableColumns = [
        ('4%', [u'№ п/п'], CReportBase.AlignRight),
        ('7%', [u'Тип документа'], CReportBase.AlignLeft),
        ('7%', [u'Номер документа'], CReportBase.AlignLeft),
        ('6%', [u'Дата'], CReportBase.AlignLeft),
        ('7%', [u'Получатель'], CReportBase.AlignLeft),
        ('7%', [u'Поставщик'], CReportBase.AlignLeft),
        ('7%', [u'Тип финансирования'], CReportBase.AlignLeft),
        ('7%', [u'Товар'], CReportBase.AlignLeft),
        ('7%', [u'Количество'], CReportBase.AlignRight),
        ('7%', [u'Срок годности'], CReportBase.AlignLeft),
        ('7%', [u'Серия'], CReportBase.AlignLeft),
        ('7%', [u'Форма выпуска'], CReportBase.AlignLeft),
        ('6%', [u'Ед. изм.'], CReportBase.AlignLeft),
        ('7%', [u'Дата редактирования документа'], CReportBase.AlignLeft),
        ('7%', [u'Пользователь, отредактировавший документ'], CReportBase.AlignLeft),
    ]

    table = createTable(cursor, tableColumns)

    prevStockMotionId = None
    stockMotionRows = 0
    strikeOutCharFormat = QtGui.QTextCharFormat()
    strikeOutCharFormat.setFontStrikeOut(True)
    for record in records:
        i = table.addRow()
        table.setText(i, 0, i)
        stockMotionId = forceRef(record.value('stockMotionId'))
        stockMotionDeleted = forceBool(record.value('stockMotionDeleted'))
        stockMotionItemDeleted = forceBool(record.value('stockMotionItemDeleted'))
        charFormat = strikeOutCharFormat if (stockMotionDeleted or stockMotionItemDeleted) else None
        if stockMotionId != prevStockMotionId:
            if stockMotionRows:
                table.mergeCells(i - stockMotionRows, 1, stockMotionRows, 1)
                table.mergeCells(i - stockMotionRows, 2, stockMotionRows, 1)
            stockMotionNumber = forceString(record.value('stockMotionNumber'))
            stockMotionDate = forceString(record.value('stockMotionDate'))
            stockTypeInt = forceInt(record.value('stockMotionType'))
            stockType = stockMotionType[stockTypeInt][0]
            stockMotionSupplierId = forceInt(record.value('stockMotionSupplierId'))
            stockMotionSupplierOrgId = forceInt(record.value('stockMotionSupplierOrgId'))
            stockMotionReceiverId = forceInt(record.value('stockMotionReceiverId'))
            stockMotionClientId = forceInt(record.value('stockMotionClientId'))
            stockMotionItemFinanceId = forceInt(record.value('stockMotionItemFinanceId'))
            if stockTypeInt == 10:  # накладная от поставщика
                stockMotionSupplier = forceString(db.translate('Organisation', 'id', stockMotionSupplierOrgId, 'shortName'))
            else:
                stockMotionSupplier = forceString(db.translate('OrgStructure', 'id', stockMotionSupplierId, 'name'))
            if stockTypeInt == 4:  # списание
                client = db.getRecord('Client', '*', stockMotionClientId)
                firstName = forceString(client.value('firstName'))
                lastName = forceString(client.value('lastName'))
                patrName = forceString(client.value('patrName'))
                birthDate = forceDate(client.value('birthDate'))
                sex = forceInt(client.value('sex'))
                items = (formatName(lastName, firstName, patrName), formatDate(birthDate), formatSex(sex))
                stockMotionReceiver = ', '.join(i for i in items if i)
            else:
                stockMotionReceiver = forceString(db.translate('OrgStructure', 'id', stockMotionReceiverId, 'name'))
            table.setText(i, 1, stockType, charFormat=charFormat)
            table.setText(i, 2, stockMotionNumber, charFormat=charFormat)
            table.setText(i, 3, stockMotionDate, charFormat=charFormat)
            table.setText(i, 4, stockMotionReceiver, charFormat=charFormat)
            table.setText(i, 5, stockMotionSupplier, charFormat=charFormat)
            finance = forceString(db.translate('rbFinance', 'id', stockMotionItemFinanceId, 'name'))
            table.setText(i, 6, finance, charFormat=charFormat)

        qnt = forceInt(record.value('qnt'))
        stockMotionItemBatch = forceString(record.value('stockMotionItemBatch'))
        stockMotionItemShelfTime = forceString(record.value('stockMotionItemShelfTime'))
        if stockMotionReceiverId == QtGui.qApp.currentOrgStructureId():
            qnt = abs(qnt)
        nomenclatureCode = forceString(record.value('nomenclatureCode'))
        nomenclatureName = forceString(record.value('nomenclatureName'))
        lfFormCode = forceString(record.value('lfFormCode'))
        lfFormName = forceString(record.value('lfFormName'))
        unitCode = forceString(record.value('unitCode'))
        unitName = forceString(record.value('unitName'))
        modifyDatetime = forceString(record.value('modifyDatetime'))
        modifyPersonId = forceInt(record.value('modifyPersonId'))

        table.setText(i, 7, ' | '.join([nomenclatureCode, nomenclatureName]), charFormat=charFormat)
        table.setText(i, 8, qnt, charFormat=charFormat)
        table.setText(i, 9, stockMotionItemShelfTime, charFormat=charFormat)
        table.setText(i, 10, stockMotionItemBatch, charFormat=charFormat)
        if lfFormCode or lfFormName:
            table.setText(i, 11, ' | '.join([v for v in [lfFormCode, lfFormName] if v]), charFormat=charFormat)
        if unitCode or unitName:
            table.setText(i, 12, ' | '.join([v for v in [unitCode, unitName] if v]), charFormat=charFormat)
        table.setText(i, 13, modifyDatetime, charFormat=charFormat)
        table.setText(i, 14, forceString(db.translate('vrbPersonWithSpeciality', 'id', modifyPersonId, 'name')), charFormat=charFormat)

    viewDialog = CReportViewDialog(parent)
    viewDialog.setWindowTitle(u'История по остаткам')
    viewDialog.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
    viewDialog.setText(doc)
    viewDialog.setOrientation(QtGui.QPrinter.Portrait)
    viewDialog.exec_()


def showRequisitionMotionsHistoryReport(records, parent=None):
    doc = QtGui.QTextDocument()
    cursor = QtGui.QTextCursor(doc)

    cursor.setCharFormat(CReportBase.ReportTitle)
    cursor.insertText(u'Накладные по требованию')
    cursor.insertBlock()

    tableColumns = [
        ('10%', [u'№ п/п'], CReportBase.AlignRight),
        ('50%', [u'Накладная'], CReportBase.AlignLeft),
        ('40%', [u'Дата'], CReportBase.AlignLeft),
    ]

    table = createTable(cursor, tableColumns)

    for record in records:
        i = table.addRow()
        table.setText(i, 0, i)
        stockMotionNumber = forceString(record.value('number'))
        stockMotionDate = forceString(record.value('date'))
        table.setText(i, 1, stockMotionNumber)
        table.setText(i, 2, stockMotionDate)

    viewDialog = CReportViewDialog(parent)

    viewDialog.setWindowTitle(u'Накладные по требованию')
    viewDialog.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
    viewDialog.setText(doc)
    viewDialog.setOrientation(QtGui.QPrinter.Portrait)
    viewDialog.exec_()


def getMotionRecordsByRequisition(requisitionId):
    db = QtGui.qApp.db
    tableSRM = db.table('StockRequisition_Motions')
    tableSM = db.table('StockMotion')
    table = tableSRM.leftJoin(tableSM, tableSM['id'].eq(tableSRM['motion_id']))
    records =   db.getRecordList(table,
                   'StockMotion.*',
                   [tableSRM['master_id'].eq(requisitionId)
                   ],
                   'master_id')
    return records



def getExistsNomenclatureIdList(orgStructureId=None, financeId=None, medicalAidKindId=None, otherHaving = [], nomenclatureIdList = [], isFinanceComboBoxFilter = False):
    db = QtGui.qApp.db
    result = []
    stmt = getExistsNomenclatureStmt(financeId=financeId,
                                     orgStructureId=orgStructureId,
                                     medicalAidKindId=medicalAidKindId,
                                     otherHaving = otherHaving,
                                     nomenclatureIdList = nomenclatureIdList,
                                     isFinanceComboBoxFilter = isFinanceComboBoxFilter)
    query = db.query(stmt)
    while query.next():
        nomenclatureId = forceRef(query.record().value('nomenclature_id'))
        if nomenclatureId and nomenclatureId not in result:
            result.append(nomenclatureId)
    return result


# ##################################################################################

def getNomenclatureSimpleUnitRatio(nomenclatureId, sourceUnitId, targetUnitId):
    db = QtGui.qApp.db
    tableNUR = db.table('rbNomenclature_UnitRatio')
    cond = [tableNUR['sourceUnit_id'].eq(sourceUnitId),
            tableNUR['targetUnit_id'].eq(targetUnitId),
            tableNUR['deleted'].eq(0),
            tableNUR['master_id'].eq(nomenclatureId)]
    record = db.getRecordEx(tableNUR, 'ratio', cond)
    return forceInt(record.value('ratio')) if record else None


def getNomenclatureUnitRatio(nomenclatureId, sourceUnitId, targetUnitId):
    if sourceUnitId == targetUnitId:
        return 1

    db = QtGui.qApp.db

    tableNUR = db.table('rbNomenclature_UnitRatio')

    cond = [tableNUR['sourceUnit_id'].eq(sourceUnitId),
            tableNUR['targetUnit_id'].eq(targetUnitId),
            tableNUR['deleted'].eq(0),
            tableNUR['master_id'].eq(nomenclatureId)]

    record = db.getRecordEx(tableNUR, 'ratio', cond)
    ratio = forceDouble(record.value('ratio')) if record else None
    if ratio is not None:
        return ratio

    cond = [tableNUR['sourceUnit_id'].eq(targetUnitId),
            tableNUR['targetUnit_id'].eq(sourceUnitId),
            tableNUR['master_id'].eq(nomenclatureId),
            tableNUR['deleted'].eq(0)]

    record = db.getRecordEx(tableNUR, 'ratio', cond)
    ratio = forceDouble(record.value('ratio')) if record else None
    if ratio is not None and ratio!=0:
        return 1.0/ratio

    return None


def applyNomenclatureUnitRatio(qnt, nomenclatureId, unitId, revert=False):
    db = QtGui.qApp.db

    stockUnitId = forceRef(db.translate('rbNomenclature', 'id', nomenclatureId, 'defaultStockUnit_id'))

    if revert:
        ratio = getNomenclatureUnitRatio(nomenclatureId, unitId, stockUnitId)
    else:
        ratio = getNomenclatureUnitRatio(nomenclatureId, stockUnitId, unitId)

    if ratio in (1, None):
        return qnt

    return qnt * ratio


def getExistsNomenclatureAmount(nomenclatureId, financeId=None, batch=None, orgStructureId=None, unitId=None, medicalAidKindId=None, shelfTime=None, exact=False, filter=[], havCond=None, orderBy=None, otherHaving=None, price=None, isStockUtilization=False, isStockRequsition=False, precision=-1, isStrictMedicalAidKindId=False):
    db = QtGui.qApp.db
    qnt = 0
    stmt = getExistsNomenclatureStmt(   nomenclatureId,
                                        financeId=financeId,
                                        batch=batch,
                                        orgStructureId=orgStructureId,
                                        unitId=unitId,
                                        medicalAidKindId=medicalAidKindId,
                                        shelfTime=shelfTime,
                                        exact=exact,
                                        filter=filter,
                                        otherHaving=otherHaving,
                                        price=price,
                                        isStockUtilization=isStockUtilization,
                                        isStockRequsition=isStockRequsition)
    query = db.query(stmt)
    while query.next():
        record = query.record()
        recQnt = forceDouble(record.value('qnt'))
        if recQnt:
            #resQnt = recordList.get((recNomenclatureId,  recFinanceId, recMedicalAidKindId), 0)
            recNomenclatureId = forceRef(record.value('nomenclature_id'))
            recFinanceId = forceRef(record.value('finance_id'))
            recMedicalAidKindId = forceRef(record.value('medicalAidKind_id'))
            #resultList.append([(recNomenclatureId,  recFinanceId, recMedicalAidKindId), recQnt])
            #recordList[(recNomenclatureId,  recFinanceId, recMedicalAidKindId)] = resQnt + recQnt
            if isStockRequsition: #0013144 (isStockRequsition)
                if nomenclatureId == recNomenclatureId and ((((not financeId) and QtGui.qApp.controlSMFinance() != 2) or financeId == recFinanceId) and medicalAidKindId == recMedicalAidKindId) or ((not isStrictMedicalAidKindId) and financeId == recFinanceId):
                    qnt += recQnt
            elif financeId: #0012562:0044803
                if (nomenclatureId, financeId, medicalAidKindId) == (recNomenclatureId,  recFinanceId, recMedicalAidKindId):
                    qnt += recQnt
                elif nomenclatureId == recNomenclatureId:
                    if QtGui.qApp.controlSMFinance() == 2:
                        if financeId == recFinanceId and (medicalAidKindId == recMedicalAidKindId or not isStrictMedicalAidKindId):
                            qnt += recQnt
                    else:
                        if financeId == recFinanceId and (medicalAidKindId == recMedicalAidKindId or not isStrictMedicalAidKindId):
                            qnt += recQnt
                        elif medicalAidKindId == recMedicalAidKindId or not isStrictMedicalAidKindId:
                            qnt += recQnt
            elif exact:
                if (nomenclatureId, financeId, medicalAidKindId) == (recNomenclatureId,  recFinanceId, recMedicalAidKindId):
                    qnt += recQnt
                elif nomenclatureId == recNomenclatureId and medicalAidKindId == recMedicalAidKindId or not isStrictMedicalAidKindId:
                    qnt += recQnt

    if unitId is not None:
        if precision >= 0:
            qnt = round(applyNomenclatureUnitRatio(qnt, nomenclatureId, unitId), precision)
        else:
            qnt = applyNomenclatureUnitRatio(qnt, nomenclatureId, unitId)
    return qnt


def getExistsNomenclatureAmountEx(nomenclatureId, financeId=None, batch=None, orgStructureId=None, unitId=None, medicalAidKindId=None, shelfTime=None, exact=False, filter=[], havCond=None, orderBy=None, otherHaving=None, price=None, isStockUtilization=False, isStockRequsition=False, precision=-1, isStrictMedicalAidKindId=False):
    db = QtGui.qApp.db
    qnt = 0
    stmt = getExistsNomenclatureStmt(   nomenclatureId,
                                        financeId=financeId,
                                        batch=batch,
                                        orgStructureId=orgStructureId,
                                        unitId=unitId,
                                        medicalAidKindId=medicalAidKindId,
                                        shelfTime=shelfTime,
                                        exact=exact,
                                        filter=filter,
                                        otherHaving=otherHaving,
                                        price=price,
                                        isStockUtilization=isStockUtilization,
                                        isStockRequsition=isStockRequsition)
    shelfTime = forceDate(shelfTime)
    query = db.query(stmt)
    while query.next():
        record = query.record()
        recQnt = forceDouble(record.value('qnt'))
        if recQnt:
            recNomenclatureId = forceRef(record.value('nomenclature_id'))
            recFinanceId = forceRef(record.value('finance_id'))
            recMedicalAidKindId = forceRef(record.value('medicalAidKind_id'))
            recBatch = forceStringEx(record.value('batch'))
            recShelfTime = forceDate(record.value('shelfTime'))
            recPrice= forceDouble(record.value('price'))
            if isStockRequsition: #0013144 (isStockRequsition)
                if nomenclatureId == recNomenclatureId and ((((not financeId) and QtGui.qApp.controlSMFinance() != 2) or financeId == recFinanceId) and medicalAidKindId == recMedicalAidKindId) or ((not isStrictMedicalAidKindId) and financeId == recFinanceId):
                    qnt += recQnt
            elif exact:
                if (nomenclatureId, financeId, medicalAidKindId, batch, shelfTime, price) == (recNomenclatureId,  recFinanceId, recMedicalAidKindId, recBatch, recShelfTime, recPrice):
                    qnt += recQnt
    if unitId is not None:
        if precision >= 0:
            qnt = round(applyNomenclatureUnitRatio(qnt, nomenclatureId, unitId), precision)
        else:
            qnt = applyNomenclatureUnitRatio(qnt, nomenclatureId, unitId)
    return qnt


def getExistsNomenclatureAmountSum(nomenclatureId, financeId=None, batch=None, orgStructureId=None, unitId=None, medicalAidKindId=None, shelfTime=None, exact=False, filter=[], havCond=None, orderBy=None, otherHaving=None):
    db = QtGui.qApp.db
    sumQnt = 0
    stmt = getExistsNomenclatureStmt(   nomenclatureId,
                                                                financeId=financeId,
                                                                batch=batch,
                                                                orgStructureId=orgStructureId,
                                                                unitId=unitId,
                                                                medicalAidKindId=medicalAidKindId,
                                                                shelfTime=shelfTime,
                                                                exact=exact,
                                                                filter=filter,
                                                                otherHaving=otherHaving)
    query = db.query(stmt)
    while query.next():
        qnt = forceDouble(query.record().value('qnt'))
        if unitId is not None:
            sumQnt += round(applyNomenclatureUnitRatio(qnt, nomenclatureId, unitId), 2)
        else:
            sumQnt += forceDouble(query.record().value('qnt'))
    return sumQnt


def getExistsNomenclatureStmt(nomenclatureId=None, financeId=None, batch=None, orgStructureId=None, unitId=None, medicalAidKindId=None, shelfTime=None, exact=False, filter=[], havCond=None, orderBy=None, otherHaving=None, filterFor=None, isStrictMedicalAidKindId=False, price=None, isStockUtilization=False, nomenclatureIdList=[], isStockRequsition=False, isFinanceComboBoxFilter=False, inventoryFillFilter={}):
    db = QtGui.qApp.db
    tableStockTrans = db.table('StockTrans')
    tableSMI = db.table('StockMotion_Item')
    tableOrgStructureStock = db.table('OrgStructure_Stock')

    debCond = []
    creCond = []
    creCondFinanceTrans = []
    ossCond = []

    date = QDate.currentDate()
    orgStructureId = orgStructureId or QtGui.qApp.currentOrgStructureId()
#    inventoryLastDate = getInventoryLastDate(orgStructureId)
#    if inventoryLastDate:
#        debCond.append(tableStockTrans['date'].dateGe(inventoryLastDate))
#        creCond.append(tableStockTrans['date'].dateGe(inventoryLastDate))
#        creCondFinanceTrans.append(tableStockTrans['date'].dateGe(inventoryLastDate))
    if date:
        debCond.append(tableStockTrans['date'].dateLe(date))
        creCond.append(tableStockTrans['date'].dateLe(date))
        creCondFinanceTrans.append(tableStockTrans['date'].dateLe(date))
    if orgStructureId:
        debCond.append(tableStockTrans['debOrgStructure_id'].eq(orgStructureId))
        creCond.append(tableStockTrans['creOrgStructure_id'].eq(orgStructureId))
        creCondFinanceTrans.append(tableStockTrans['creOrgStructure_id'].eq(orgStructureId))
        ossCond.append(tableOrgStructureStock['master_id'].eq(orgStructureId))
    else:
        debCond.append(tableStockTrans['debOrgStructure_id'].isNotNull())
        creCond.append(tableStockTrans['creOrgStructure_id'].isNotNull())
        creCondFinanceTrans.append(tableStockTrans['creOrgStructure_id'].isNotNull())
    if nomenclatureId and isinstance(nomenclatureId, list):
        debCond.append(tableStockTrans['debNomenclature_id'].inlist(nomenclatureId))
        creCond.append(tableStockTrans['creNomenclature_id'].inlist(nomenclatureId))
        creCondFinanceTrans.append(tableStockTrans['creNomenclature_id'].inlist(nomenclatureId))
        ossCond.append(tableOrgStructureStock['nomenclature_id'].inlist(nomenclatureId))
    elif nomenclatureId:
        debCond.append(tableStockTrans['debNomenclature_id'].eq(nomenclatureId))
        creCond.append(tableStockTrans['creNomenclature_id'].eq(nomenclatureId))
        creCondFinanceTrans.append(tableStockTrans['creNomenclature_id'].eq(nomenclatureId))
        ossCond.append(tableOrgStructureStock['nomenclature_id'].eq(nomenclatureId))

    batchFields = 'StockTrans.batch AS batch, StockTrans.shelfTime AS shelfTime, StockTrans.price AS price, '
    sqlGroupByBatch = 'shelfTime, batch, price, '
    sqlGroupByBatchT = 'T.shelfTime, T.batch, T.price, '

    if price is not None:
        t = tableStockTrans['price'].eq(price)
        debCond.append(t)
        creCondFinanceTrans.append(t)
        creCond.append(t)
    if batch:
        t = tableStockTrans['batch'].eq(batch)
        debCond.append(t)
        creCondFinanceTrans.append(t)
        creCond.append(t)
    elif exact:
        t = tableStockTrans['batch'].eq('')
        debCond.append(t)
        creCondFinanceTrans.append(t)
        creCond.append(t)
    if filterFor != UTILIZATION or not isStockUtilization:
        if shelfTime:
            t = tableStockTrans['shelfTime'].ge(shelfTime)
            debCond.append(t)
            creCond.append(t)
            creCondFinanceTrans.append(t)
        elif exact:
            t = db.joinOr([tableStockTrans['shelfTime'].isNull(), tableStockTrans['shelfTime'].ge(date)])
            debCond.append(t)
            creCond.append(t)
            creCondFinanceTrans.append(t)
    if financeId: #0012562:0044803
        if isStockRequsition or isFinanceComboBoxFilter: #0013144 (isStockRequsition), #0013272 (isFinanceComboBoxFilter)
            debCond.append(tableStockTrans['debFinance_id'].eq(financeId))
            creCond.append(tableStockTrans['creFinance_id'].eq(financeId))
            creCondFinanceTrans.append(tableStockTrans['creFinance_id'].eq(financeId))
            ossCond.append(tableOrgStructureStock['finance_id'].eq(financeId))
        elif QtGui.qApp.controlSMFinance() == 1:
            debCond.append(db.joinOr([tableStockTrans['debFinance_id'].eq(financeId), tableStockTrans['debFinance_id'].isNull()]))
            creCond.append(db.joinOr([tableStockTrans['creFinance_id'].eq(financeId), tableStockTrans['creFinance_id'].isNull()]))
            creCondFinanceTrans.append(db.joinOr([tableStockTrans['creFinance_id'].eq(financeId), tableStockTrans['creFinance_id'].isNull()]))
            ossCond.append(db.joinOr([tableOrgStructureStock['finance_id'].eq(financeId), tableOrgStructureStock['finance_id'].isNull()]))
        elif QtGui.qApp.controlSMFinance() == 2:
            debCond.append(tableStockTrans['debFinance_id'].eq(financeId))
            creCond.append(tableStockTrans['creFinance_id'].eq(financeId))
            creCondFinanceTrans.append(tableStockTrans['creFinance_id'].eq(financeId))
            ossCond.append(tableOrgStructureStock['finance_id'].eq(financeId))
    elif exact and not isStockRequsition: #0014606
        debCond.append(tableStockTrans['debFinance_id'].isNull())
        creCond.append(tableStockTrans['creFinance_id'].isNull())
        creCondFinanceTrans.append(tableStockTrans['creFinance_id'].isNull())
        ossCond.append(tableOrgStructureStock['finance_id'].isNull())
    if medicalAidKindId and not isStrictMedicalAidKindId:
        debCond.append(db.joinOr([tableSMI['medicalAidKind_id'].eq(medicalAidKindId), tableSMI['medicalAidKind_id'].isNull()]))
        creCond.append(db.joinOr([tableSMI['medicalAidKind_id'].eq(medicalAidKindId), tableSMI['medicalAidKind_id'].isNull()]))
        creCondFinanceTrans.append(db.joinOr([tableSMI['oldMedicalAidKind_id'].eq(medicalAidKindId), tableSMI['oldMedicalAidKind_id'].isNull()]))
    elif medicalAidKindId and isStrictMedicalAidKindId:
        debCond.append(tableSMI['medicalAidKind_id'].eq(medicalAidKindId))
        creCond.append(tableSMI['medicalAidKind_id'].eq(medicalAidKindId))
        creCondFinanceTrans.append(tableSMI['oldMedicalAidKind_id'].eq(medicalAidKindId))
    elif exact:
        debCond.append(tableSMI['medicalAidKind_id'].isNull())
        creCond.append(tableSMI['medicalAidKind_id'].isNull())
        creCondFinanceTrans.append(tableSMI['oldMedicalAidKind_id'].isNull())
    if otherHaving:
        havCond = otherHaving
    elif isStockUtilization:
        havCond = ['`qnt` > 0.0001']
    else:
        havCond = ['`qnt` > 0.0001 and ((shelfTime>=curDate()) OR shelfTime is NULL)']

    if filter:
        debCond.append(filter)
        creCond.append(filter)

    if unitId:
        unitCol = '%s AS unitId' %unitId
        unitParams = '''
(SELECT
            rbNomenclature_UnitRatio.ratio
        FROM
            rbNomenclature_UnitRatio
        WHERE
            rbNomenclature_UnitRatio.sourceUnit_id = RBUSource.id
                AND rbNomenclature_UnitRatio.targetUnit_id =  %(unitId)s
                AND rbNomenclature_UnitRatio.master_id = rbNomenclature.id) AS `ratio`,
(SELECT
        rbUnit.name
    FROM
        rbNomenclature_UnitRatio
            LEFT JOIN
        rbUnit ON rbUnit.id = rbNomenclature_UnitRatio.targetUnit_id
    WHERE
        rbNomenclature_UnitRatio.sourceUnit_id = RBUSource.id
            AND rbNomenclature_UnitRatio.targetUnit_id = %(unitId)s
            AND rbNomenclature_UnitRatio.master_id = rbNomenclature.id) AS `unitName`
        '''%{
        'unitId':unitId,
        }
    else:
        unitCol = 'RBUSource.id AS `unitId`'
        unitParams = '1'

    if medicalAidKindId:
        sqlGroupByBatchT = sqlGroupByBatchT + u'medicalAidKind_id, '
    order = u'OrgStructure.code, rbNomenclature.code, rbNomenclature.name, %s rbFinance.code'%sqlGroupByBatchT

    joinCondTInvFill = u''
    joinCondTAddInvFill = u''
    if inventoryFillFilter:
        nomenclatureClassId = inventoryFillFilter.get('classId', None)
        nomenclatureKindId = inventoryFillFilter.get('kindId', None)
        nomenclatureTypeId = inventoryFillFilter.get('typeId', None)
        nomenclatureName   = inventoryFillFilter.get('name', None)
        if nomenclatureTypeId:
            joinCondTAddInvFill = u' AND rbNomenclature.type_id = %s '%(str(nomenclatureTypeId))
        if nomenclatureName:
            joinCondTAddInvFill += u' AND (rbNomenclature.name LIKE %s OR rbNomenclature.originName LIKE %s) '%(u'\'%%%s%%\''%(forceString(nomenclatureName)), u'\'%%%s%%\''%(forceString(nomenclatureName)))
        if nomenclatureKindId or nomenclatureClassId:
            if nomenclatureKindId:
                joinCondTInvFill = u' INNER JOIN rbNomenclatureType ON (rbNomenclatureType.id = rbNomenclature.type_id AND rbNomenclatureType.kind_id = %s) '%(str(nomenclatureKindId))
            if nomenclatureClassId and not nomenclatureKindId:
                joinCondTInvFill = u' INNER JOIN rbNomenclatureType ON rbNomenclatureType.id = rbNomenclature.type_id INNER JOIN rbNomenclatureKind ON (rbNomenclatureKind.id = rbNomenclatureType.kind_id AND rbNomenclatureKind.class_id = %s) '%(str(nomenclatureClassId))
            elif nomenclatureClassId and nomenclatureKindId:
                joinCondTInvFill += u' INNER JOIN rbNomenclatureKind ON (rbNomenclatureKind.id = rbNomenclatureType.kind_id AND rbNomenclatureKind.class_id = %s) '%(str(nomenclatureClassId))
    if nomenclatureIdList:
        joinCondT = u'INNER JOIN rbNomenclature ON (rbNomenclature.id = T.nomenclature_id AND rbNomenclature.id IN (%s)%s) '%(u','.join(str(nomenclatureId) for nomenclatureId in nomenclatureIdList if nomenclatureId), joinCondTAddInvFill)
    elif joinCondTAddInvFill:
        joinCondT = u'INNER JOIN rbNomenclature ON (rbNomenclature.id = T.nomenclature_id%s) '%(joinCondTAddInvFill)
    else:
        joinCondT = u'LEFT JOIN rbNomenclature ON (rbNomenclature.id = T.nomenclature_id) '
    if joinCondTInvFill:
        joinCondT += joinCondTInvFill

    stmt = u'''
SELECT T.orgStructure_id,
   T.nomenclature_id,
   T.batch,
   T.shelfTime,
   T.price,
   T.medicalAidKind_id,
   T.finance_id,
   sum(T.`qnt`) AS `qnt`,
   sum(T.`sum`) AS `sum`
FROM
(
SELECT debOrgStructure_id AS orgStructure_id,
       debNomenclature_id AS nomenclature_id,
       %(batchFields)s
       StockMotion_Item.medicalAidKind_id,
       debFinance_id      AS finance_id,
       sum(StockTrans.qnt) AS `qnt`,
       sum(StockTrans.`sum`) AS `sum`
FROM StockTrans
LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
WHERE %(debCond)s AND StockMotion.deleted = 0 AND (StockMotion_Item.deleted=0) AND (StockMotion.type != 2)
GROUP BY debOrgStructure_id, debNomenclature_id, %(groupByBatch)s debFinance_id, medicalAidKind_id

UNION ALL
SELECT creOrgStructure_id AS orgStructure_id,
       creNomenclature_id AS nomenclature_id,
       %(batchFields)s
       StockMotion_Item.medicalAidKind_id,
       creFinance_id      AS finance_id,
       -sum(StockTrans.qnt)          AS `qnt`,
       -sum(StockTrans.`sum`)        AS `sum`
FROM StockTrans
LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
WHERE %(creCond)s AND StockMotion.deleted = 0 AND (StockMotion_Item.deleted=0) AND (StockMotion.type != 2)
GROUP BY creOrgStructure_id, creNomenclature_id, %(groupByBatch)s creFinance_id, medicalAidKind_id

UNION ALL
    SELECT debOrgStructure_id AS orgStructure_id,
       debNomenclature_id AS nomenclature_id,
       %(batchFields)s
       StockMotion_Item.medicalAidKind_id,
       debFinance_id      AS finance_id,
       sum(StockTrans.qnt)           AS `qnt`,
       sum(StockTrans.`sum`)         AS `sum`
FROM StockTrans
LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
WHERE %(debCond)s AND StockMotion.deleted = 0 AND (StockMotion_Item.deleted=0) AND (StockMotion.type = 2)
GROUP BY debOrgStructure_id, debNomenclature_id, %(groupByBatch)s debFinance_id, medicalAidKind_id

UNION ALL
SELECT creOrgStructure_id AS orgStructure_id,
       creNomenclature_id AS nomenclature_id,
       %(batchFields)s
       StockMotion_Item.oldMedicalAidKind_id AS medicalAidKind_id,
       StockMotion_Item.oldFinance_id      AS finance_id,
       -sum(StockTrans.qnt)          AS `qnt`,
       -sum(StockTrans.`sum`)        AS `sum`
FROM StockTrans
LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
WHERE %(creCondFinanceTrans)s AND StockMotion.deleted = 0 AND (StockMotion_Item.deleted=0) AND (StockMotion.type = 2)
GROUP BY creOrgStructure_id, creNomenclature_id, %(groupByBatch)s creFinance_id, medicalAidKind_id

UNION ALL
SELECT master_id          AS orgStructure_id,
       nomenclature_id    AS nomenclature_id,
       ''                 AS batch,
       NULL               AS shelfTime,
       0                  AS price,
       NULL               AS medicalAidKind_id,
       finance_id         AS finance_id,
       0                  AS `qnt`,
       0                  AS `sum`
FROM OrgStructure_Stock
WHERE %(ossCond)s
GROUP BY master_id, nomenclature_id, finance_id, medicalAidKind_id
) AS T
LEFT JOIN OrgStructure ON OrgStructure.id = T.orgStructure_id
%(joinCondT)s
LEFT JOIN rbUnit AS RBUSource ON rbNomenclature.defaultStockUnit_id = RBUSource.id
LEFT JOIN rbFinance ON rbFinance.id = T.finance_id
LEFT JOIN OrgStructure_Stock ON OrgStructure_Stock.master_id = T.orgStructure_id
      AND OrgStructure_Stock.nomenclature_id = T.nomenclature_id
      AND OrgStructure_Stock.finance_id = T.finance_id
GROUP BY orgStructure_id, nomenclature_id, %(groupByBatchT)s finance_id, medicalAidKind_id
HAVING (%(havCond)s)
ORDER BY %(orderBy)s
''' % {
    'debCond' : db.joinAnd(debCond) if debCond else '1',
    'creCond' : db.joinAnd(creCond) if creCond else '1',
    'creCondFinanceTrans' : db.joinAnd(creCondFinanceTrans) if creCondFinanceTrans else '1',
    'ossCond' : db.joinAnd(ossCond) if ossCond else '1',
    'havCond' : db.joinAnd(havCond),
    'groupByBatch' : sqlGroupByBatch,
    'joinCondT'      : joinCondT,
    'groupByBatchT' : sqlGroupByBatchT,
    'batchFields'  : batchFields,
    'unitCol':unitCol,
    'unitParams':unitParams,
    'orderBy': orderBy if orderBy else order
    }
    return stmt


def getExistsNomenclatureToSGTINStmt(nomenclatureId=None, financeId=None, batch=None, orgStructureId=None, unitId=None, medicalAidKindId=None, shelfTime=None, exact=False, filter=[], havCond=None, orderBy=None, otherHaving=None, filterFor=None, isStrictMedicalAidKindId=False, price=None, isStockUtilization=False, nomenclatureIdList=[], isStockRequsition=False, isFinanceComboBoxFilter=False, inventoryFillFilter={}):
    db = QtGui.qApp.db
    tableStockTrans = db.table('StockTrans')
    tableSMI = db.table('StockMotion_Item')
    tableOrgStructureStock = db.table('OrgStructure_Stock')

    debCond = []
    creCond = []
    creCondFinanceTrans = []
    ossCond = []

    date = QDate.currentDate()
    orgStructureId = orgStructureId or QtGui.qApp.currentOrgStructureId()
#    inventoryLastDate = getInventoryLastDate(orgStructureId)
#    if inventoryLastDate:
#        debCond.append(tableStockTrans['date'].dateGe(inventoryLastDate))
#        creCond.append(tableStockTrans['date'].dateGe(inventoryLastDate))
#        creCondFinanceTrans.append(tableStockTrans['date'].dateGe(inventoryLastDate))
    if date:
        debCond.append(tableStockTrans['date'].dateLe(date))
        creCond.append(tableStockTrans['date'].dateLe(date))
        creCondFinanceTrans.append(tableStockTrans['date'].dateLe(date))
    if orgStructureId:
        debCond.append(tableStockTrans['debOrgStructure_id'].eq(orgStructureId))
        creCond.append(tableStockTrans['creOrgStructure_id'].eq(orgStructureId))
        creCondFinanceTrans.append(tableStockTrans['creOrgStructure_id'].eq(orgStructureId))
        ossCond.append(tableOrgStructureStock['master_id'].eq(orgStructureId))
    else:
        debCond.append(tableStockTrans['debOrgStructure_id'].isNotNull())
        creCond.append(tableStockTrans['creOrgStructure_id'].isNotNull())
        creCondFinanceTrans.append(tableStockTrans['creOrgStructure_id'].isNotNull())
    if nomenclatureId and isinstance(nomenclatureId, list):
        debCond.append(tableStockTrans['debNomenclature_id'].inlist(nomenclatureId))
        creCond.append(tableStockTrans['creNomenclature_id'].inlist(nomenclatureId))
        creCondFinanceTrans.append(tableStockTrans['creNomenclature_id'].inlist(nomenclatureId))
        ossCond.append(tableOrgStructureStock['nomenclature_id'].inlist(nomenclatureId))
    elif nomenclatureId:
        debCond.append(tableStockTrans['debNomenclature_id'].eq(nomenclatureId))
        creCond.append(tableStockTrans['creNomenclature_id'].eq(nomenclatureId))
        creCondFinanceTrans.append(tableStockTrans['creNomenclature_id'].eq(nomenclatureId))
        ossCond.append(tableOrgStructureStock['nomenclature_id'].eq(nomenclatureId))

    batchFields = 'StockTrans.batch AS batch, StockTrans.shelfTime AS shelfTime, StockTrans.price AS price, '
    sqlGroupByBatch = 'shelfTime, batch, price, '
    sqlGroupByBatchT = 'T.shelfTime, T.batch, T.price, '

    if price is not None:
        t = tableStockTrans['price'].eq(price)
        debCond.append(t)
        creCondFinanceTrans.append(t)
        creCond.append(t)
    if batch:
        t = tableStockTrans['batch'].eq(batch)
        debCond.append(t)
        creCondFinanceTrans.append(t)
        creCond.append(t)
    elif exact:
        t = tableStockTrans['batch'].eq('')
        debCond.append(t)
        creCondFinanceTrans.append(t)
        creCond.append(t)
    if filterFor != UTILIZATION or not isStockUtilization:
        if shelfTime:
            t = tableStockTrans['shelfTime'].ge(shelfTime)
            debCond.append(t)
            creCond.append(t)
            creCondFinanceTrans.append(t)
        elif exact:
            t = db.joinOr([tableStockTrans['shelfTime'].isNull(), tableStockTrans['shelfTime'].ge(date)])
            debCond.append(t)
            creCond.append(t)
            creCondFinanceTrans.append(t)
    if financeId: #0012562:0044803
        if isStockRequsition or isFinanceComboBoxFilter: #0013144 (isStockRequsition), #0013272 (isFinanceComboBoxFilter)
            debCond.append(tableStockTrans['debFinance_id'].eq(financeId))
            creCond.append(tableStockTrans['creFinance_id'].eq(financeId))
            creCondFinanceTrans.append(tableStockTrans['creFinance_id'].eq(financeId))
            ossCond.append(tableOrgStructureStock['finance_id'].eq(financeId))
        elif QtGui.qApp.controlSMFinance() == 1:
            debCond.append(db.joinOr([tableStockTrans['debFinance_id'].eq(financeId), tableStockTrans['debFinance_id'].isNull()]))
            creCond.append(db.joinOr([tableStockTrans['creFinance_id'].eq(financeId), tableStockTrans['creFinance_id'].isNull()]))
            creCondFinanceTrans.append(db.joinOr([tableStockTrans['creFinance_id'].eq(financeId), tableStockTrans['creFinance_id'].isNull()]))
            ossCond.append(db.joinOr([tableOrgStructureStock['finance_id'].eq(financeId), tableOrgStructureStock['finance_id'].isNull()]))
        elif QtGui.qApp.controlSMFinance() == 2:
            debCond.append(tableStockTrans['debFinance_id'].eq(financeId))
            creCond.append(tableStockTrans['creFinance_id'].eq(financeId))
            creCondFinanceTrans.append(tableStockTrans['creFinance_id'].eq(financeId))
            ossCond.append(tableOrgStructureStock['finance_id'].eq(financeId))
    elif exact and not isStockRequsition: #0014606
        debCond.append(tableStockTrans['debFinance_id'].isNull())
        creCond.append(tableStockTrans['creFinance_id'].isNull())
        creCondFinanceTrans.append(tableStockTrans['creFinance_id'].isNull())
        ossCond.append(tableOrgStructureStock['finance_id'].isNull())
    if medicalAidKindId and not isStrictMedicalAidKindId:
        debCond.append(db.joinOr([tableSMI['medicalAidKind_id'].eq(medicalAidKindId), tableSMI['medicalAidKind_id'].isNull()]))
        creCond.append(db.joinOr([tableSMI['medicalAidKind_id'].eq(medicalAidKindId), tableSMI['medicalAidKind_id'].isNull()]))
        creCondFinanceTrans.append(db.joinOr([tableSMI['oldMedicalAidKind_id'].eq(medicalAidKindId), tableSMI['oldMedicalAidKind_id'].isNull()]))
    elif medicalAidKindId and isStrictMedicalAidKindId:
        debCond.append(tableSMI['medicalAidKind_id'].eq(medicalAidKindId))
        creCond.append(tableSMI['medicalAidKind_id'].eq(medicalAidKindId))
        creCondFinanceTrans.append(tableSMI['oldMedicalAidKind_id'].eq(medicalAidKindId))
    elif exact:
        debCond.append(tableSMI['medicalAidKind_id'].isNull())
        creCond.append(tableSMI['medicalAidKind_id'].isNull())
        creCondFinanceTrans.append(tableSMI['oldMedicalAidKind_id'].isNull())
    if otherHaving:
        havCond = otherHaving
    elif isStockUtilization:
        havCond = ['`qnt` > 0.0001']
    else:
        havCond = ['`qnt` > 0.0001 and ((shelfTime>=curDate()) OR shelfTime is NULL)']

    if filter:
        debCond.append(filter)
        creCond.append(filter)

    if unitId:
        unitCol = '%s AS unitId' %unitId
        unitParams = '''
(SELECT
            rbNomenclature_UnitRatio.ratio
        FROM
            rbNomenclature_UnitRatio
        WHERE
            rbNomenclature_UnitRatio.sourceUnit_id = RBUSource.id
                AND rbNomenclature_UnitRatio.targetUnit_id =  %(unitId)s
                AND rbNomenclature_UnitRatio.master_id = rbNomenclature.id) AS `ratio`,
(SELECT
        rbUnit.name
    FROM
        rbNomenclature_UnitRatio
            LEFT JOIN
        rbUnit ON rbUnit.id = rbNomenclature_UnitRatio.targetUnit_id
    WHERE
        rbNomenclature_UnitRatio.sourceUnit_id = RBUSource.id
            AND rbNomenclature_UnitRatio.targetUnit_id = %(unitId)s
            AND rbNomenclature_UnitRatio.master_id = rbNomenclature.id) AS `unitName`
        '''%{
        'unitId':unitId,
        }
    else:
        unitCol = 'RBUSource.id AS `unitId`'
        unitParams = '1'

    if medicalAidKindId:
        sqlGroupByBatchT = sqlGroupByBatchT + u'medicalAidKind_id, '
    order = u'OrgStructure.code, rbNomenclature.code, rbNomenclature.name, %s rbFinance.code'%sqlGroupByBatchT

    joinCondTInvFill = u''
    joinCondTAddInvFill = u''
    if inventoryFillFilter:
        nomenclatureClassId = inventoryFillFilter.get('classId', None)
        nomenclatureKindId = inventoryFillFilter.get('kindId', None)
        nomenclatureTypeId = inventoryFillFilter.get('typeId', None)
        nomenclatureName   = inventoryFillFilter.get('name', None)
        if nomenclatureTypeId:
            joinCondTAddInvFill = u' AND rbNomenclature.type_id = %s '%(str(nomenclatureTypeId))
        if nomenclatureName:
            joinCondTAddInvFill += u' AND (rbNomenclature.name LIKE %s OR rbNomenclature.originName LIKE %s) '%(u'\'%%%s%%\''%(forceString(nomenclatureName)), u'\'%%%s%%\''%(forceString(nomenclatureName)))
        if nomenclatureKindId or nomenclatureClassId:
            if nomenclatureKindId:
                joinCondTInvFill = u' INNER JOIN rbNomenclatureType ON (rbNomenclatureType.id = rbNomenclature.type_id AND rbNomenclatureType.kind_id = %s) '%(str(nomenclatureKindId))
            if nomenclatureClassId and not nomenclatureKindId:
                joinCondTInvFill = u' INNER JOIN rbNomenclatureType ON rbNomenclatureType.id = rbNomenclature.type_id INNER JOIN rbNomenclatureKind ON (rbNomenclatureKind.id = rbNomenclatureType.kind_id AND rbNomenclatureKind.class_id = %s) '%(str(nomenclatureClassId))
            elif nomenclatureClassId and nomenclatureKindId:
                joinCondTInvFill += u' INNER JOIN rbNomenclatureKind ON (rbNomenclatureKind.id = rbNomenclatureType.kind_id AND rbNomenclatureKind.class_id = %s) '%(str(nomenclatureClassId))
    if nomenclatureIdList:
        joinCondT = u'INNER JOIN rbNomenclature ON (rbNomenclature.id = T.nomenclature_id AND rbNomenclature.id IN (%s)%s) '%(u','.join(str(nomenclatureId) for nomenclatureId in nomenclatureIdList if nomenclatureId), joinCondTAddInvFill)
    elif joinCondTAddInvFill:
        joinCondT = u'INNER JOIN rbNomenclature ON (rbNomenclature.id = T.nomenclature_id%s) '%(joinCondTAddInvFill)
    else:
        joinCondT = u'LEFT JOIN rbNomenclature ON (rbNomenclature.id = T.nomenclature_id) '
    if joinCondTInvFill:
        joinCondT += joinCondTInvFill

    stmt = u'''
SELECT T.orgStructure_id,
   T.nomenclature_id,
   T.batch,
   T.shelfTime,
   T.price,
   T.medicalAidKind_id,
   T.finance_id,
   T.sgtin,
   sum(T.`qnt`) AS `qnt`,
   sum(T.`sum`) AS `sum`
FROM
(
SELECT debOrgStructure_id AS orgStructure_id,
       debNomenclature_id AS nomenclature_id,
       %(batchFields)s
       StockMotion_Item.medicalAidKind_id,
       debFinance_id      AS finance_id,
       StockMotion_Item.sgtin,
       sum(StockTrans.qnt) AS `qnt`,
       sum(StockTrans.`sum`) AS `sum`
FROM StockTrans
LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
WHERE %(debCond)s AND StockMotion.deleted = 0 AND (StockMotion_Item.deleted=0) AND (StockMotion.type != 2)
GROUP BY debOrgStructure_id, debNomenclature_id, %(groupByBatch)s debFinance_id, medicalAidKind_id, sgtin

UNION ALL
SELECT creOrgStructure_id AS orgStructure_id,
       creNomenclature_id AS nomenclature_id,
       %(batchFields)s
       StockMotion_Item.medicalAidKind_id,
       creFinance_id      AS finance_id,
       StockMotion_Item.sgtin,
       -sum(StockTrans.qnt)          AS `qnt`,
       -sum(StockTrans.`sum`)        AS `sum`
FROM StockTrans
LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
WHERE %(creCond)s AND StockMotion.deleted = 0 AND (StockMotion_Item.deleted=0) AND (StockMotion.type != 2)
GROUP BY creOrgStructure_id, creNomenclature_id, %(groupByBatch)s creFinance_id, medicalAidKind_id, sgtin

UNION ALL
    SELECT debOrgStructure_id AS orgStructure_id,
       debNomenclature_id AS nomenclature_id,
       %(batchFields)s
       StockMotion_Item.medicalAidKind_id,
       debFinance_id      AS finance_id,
       StockMotion_Item.sgtin,
       sum(StockTrans.qnt)           AS `qnt`,
       sum(StockTrans.`sum`)         AS `sum`
FROM StockTrans
LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
WHERE %(debCond)s AND StockMotion.deleted = 0 AND (StockMotion_Item.deleted=0) AND (StockMotion.type = 2)
GROUP BY debOrgStructure_id, debNomenclature_id, %(groupByBatch)s debFinance_id, medicalAidKind_id, sgtin

UNION ALL
SELECT creOrgStructure_id AS orgStructure_id,
       creNomenclature_id AS nomenclature_id,
       %(batchFields)s
       StockMotion_Item.oldMedicalAidKind_id AS medicalAidKind_id,
       StockMotion_Item.oldFinance_id      AS finance_id,
       StockMotion_Item.sgtin,
       -sum(StockTrans.qnt)          AS `qnt`,
       -sum(StockTrans.`sum`)        AS `sum`
FROM StockTrans
LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
WHERE %(creCondFinanceTrans)s AND StockMotion.deleted = 0 AND (StockMotion_Item.deleted=0) AND (StockMotion.type = 2)
GROUP BY creOrgStructure_id, creNomenclature_id, %(groupByBatch)s creFinance_id, medicalAidKind_id, sgtin

UNION ALL
SELECT master_id          AS orgStructure_id,
       nomenclature_id    AS nomenclature_id,
       ''                 AS batch,
       NULL               AS shelfTime,
       0                  AS price,
       NULL               AS medicalAidKind_id,
       finance_id         AS finance_id,
       ''                 AS sgtin,
       0                  AS `qnt`,
       0                  AS `sum`
FROM OrgStructure_Stock
WHERE %(ossCond)s
GROUP BY master_id, nomenclature_id, finance_id, medicalAidKind_id, sgtin
) AS T
LEFT JOIN OrgStructure ON OrgStructure.id = T.orgStructure_id
%(joinCondT)s
LEFT JOIN rbUnit AS RBUSource ON rbNomenclature.defaultStockUnit_id = RBUSource.id
LEFT JOIN rbFinance ON rbFinance.id = T.finance_id
LEFT JOIN OrgStructure_Stock ON OrgStructure_Stock.master_id = T.orgStructure_id
      AND OrgStructure_Stock.nomenclature_id = T.nomenclature_id
      AND OrgStructure_Stock.finance_id = T.finance_id
GROUP BY orgStructure_id, nomenclature_id, %(groupByBatchT)s finance_id, medicalAidKind_id, sgtin
HAVING (%(havCond)s)
ORDER BY %(orderBy)s
''' % {
    'debCond' : db.joinAnd(debCond) if debCond else '1',
    'creCond' : db.joinAnd(creCond) if creCond else '1',
    'creCondFinanceTrans' : db.joinAnd(creCondFinanceTrans) if creCondFinanceTrans else '1',
    'ossCond' : db.joinAnd(ossCond) if ossCond else '1',
    'havCond' : db.joinAnd(havCond),
    'groupByBatch' : sqlGroupByBatch,
    'joinCondT'      : joinCondT,
    'groupByBatchT' : sqlGroupByBatchT,
    'batchFields'  : batchFields,
    'unitCol':unitCol,
    'unitParams':unitParams,
    'orderBy': orderBy if orderBy else order
    }
    return stmt


def getPriceNomenclatureStmt(item, exact=False, filter=[], setShelfTimeCond=True, isStockUtilization=False, filterFor=None, isStrictMedicalAidKindId=False, isFinTransfer=False):
    supplierId = forceRef(item.value('supplier_id'))
    batch = forceString(item.value('batch'))
    shelfTime = forceDate(item.value('shelfTime'))
    nomenclatureId = forceRef(item.value('nomenclature_id'))
    unitId = forceRef(item.value('unit_id'))
    if isFinTransfer:
        financeId = forceRef(item.value('oldFinance_id'))
        medicalAidKindId = forceRef(item.value('oldMedicalAidKind_id'))
    else:
        financeId = forceRef(item.value('finance_id'))
        medicalAidKindId = forceRef(item.value('medicalAidKind_id'))
    havCond = [u'qnt>0'] if isStockUtilization else []
    if medicalAidKindId is not None:
        if medicalAidKindId == 0:
            havCond = [u'qnt>0', u'medicalAidKind_id is NULL', u'shelfTime >= CURDATE()']
        else:
            havCond = [u'qnt>0', u'medicalAidKind_id=%s OR medicalAidKind_id is NULL'%medicalAidKindId, u'shelfTime >= CURDATE()']
    if not setShelfTimeCond and havCond and medicalAidKindId is not None:
        havCond.pop()
        havCond.pop()
    stmt = getPriceExistsNomenclatureStmt(  nomenclatureId,
                                            financeId=financeId,
                                            batch=batch,
                                            orgStructureId=supplierId,
                                            unitId=unitId,
                                            medicalAidKindId = medicalAidKindId,
                                            shelfTime=shelfTime,
                                            exact=True,
                                            filter = filter,
                                            otherHaving = havCond,
                                            filterFor=filterFor,
                                            isStrictMedicalAidKindId=isStrictMedicalAidKindId)
    return stmt


def getPriceExistsNomenclatureStmt(nomenclatureId=None, financeId=None, batch=None, orgStructureId=None, unitId=None, medicalAidKindId=None, shelfTime=None, exact=False, filter=[], havCond=None, orderBy=None, otherHaving=None, filterFor=None, isStrictMedicalAidKindId=False, price=None):
    db = QtGui.qApp.db
    tableStockTrans = db.table('StockTrans')
    tableSMI = db.table('StockMotion_Item')
    tableOrgStructureStock = db.table('OrgStructure_Stock')

    debCond = []
    creCond = []
    creCondFinanceTrans = []
    ossCond = []

    date = QDate.currentDate()
    orgStructureId = orgStructureId or QtGui.qApp.currentOrgStructureId()
#    inventoryLastDate = getInventoryLastDate(orgStructureId)
#    if inventoryLastDate:
#        debCond.append(tableStockTrans['date'].dateGe(inventoryLastDate))
#        creCond.append(tableStockTrans['date'].dateGe(inventoryLastDate))
#        creCondFinanceTrans.append(tableStockTrans['date'].dateGe(inventoryLastDate))
    if date:
        debCond.append(tableStockTrans['date'].dateLe(date))
        creCond.append(tableStockTrans['date'].dateLe(date))
        creCondFinanceTrans.append(tableStockTrans['date'].dateLe(date))
    if orgStructureId:
        debCond.append(tableStockTrans['debOrgStructure_id'].eq(orgStructureId))
        creCond.append(tableStockTrans['creOrgStructure_id'].eq(orgStructureId))
        creCondFinanceTrans.append(tableStockTrans['creOrgStructure_id'].eq(orgStructureId))
        ossCond.append(tableOrgStructureStock['master_id'].eq(orgStructureId))
    else:
        debCond.append(tableStockTrans['debOrgStructure_id'].isNotNull())
        creCond.append(tableStockTrans['creOrgStructure_id'].isNotNull())
        creCondFinanceTrans.append(tableStockTrans['creOrgStructure_id'].isNotNull())
    if nomenclatureId:
        debCond.append(tableStockTrans['debNomenclature_id'].eq(nomenclatureId))
        creCond.append(tableStockTrans['creNomenclature_id'].eq(nomenclatureId))
        creCondFinanceTrans.append(tableStockTrans['creNomenclature_id'].eq(nomenclatureId))
        ossCond.append(tableOrgStructureStock['nomenclature_id'].eq(nomenclatureId))

    batchFields = 'StockTrans.batch AS batch, StockTrans.shelfTime AS shelfTime, StockTrans.price AS price, '
    sqlGroupByBatch = 'shelfTime, batch, price, '
    sqlGroupByBatchT = 'T.shelfTime, T.batch, T.price, '

    if price is not None:
        t = tableStockTrans['price'].eq(price)
        debCond.append(t)
        creCondFinanceTrans.append(t)
        creCond.append(t)
    if batch:
        t = tableStockTrans['batch'].eq(batch)
        debCond.append(t)
        creCondFinanceTrans.append(t)
        creCond.append(t)
    elif exact:
        t = tableStockTrans['batch'].eq('')
        debCond.append(t)
        creCondFinanceTrans.append(t)
        creCond.append(t)
    if filterFor != UTILIZATION:
        if shelfTime:
            t = tableStockTrans['shelfTime'].ge(shelfTime)
            debCond.append(t)
            creCond.append(t)
            creCondFinanceTrans.append(t)
        elif exact:
            t = db.joinOr([tableStockTrans['shelfTime'].isNull(), tableStockTrans['shelfTime'].ge(date)])
            debCond.append(t)
            creCond.append(t)
            creCondFinanceTrans.append(t)
    if financeId: #0012562:0044803
        if QtGui.qApp.controlSMFinance() == 1:
            debCond.append(db.joinOr([tableStockTrans['debFinance_id'].eq(financeId), tableStockTrans['debFinance_id'].isNull()]))
            creCond.append(db.joinOr([tableStockTrans['creFinance_id'].eq(financeId), tableStockTrans['creFinance_id'].isNull()]))
            creCondFinanceTrans.append(db.joinOr([tableStockTrans['creFinance_id'].eq(financeId), tableStockTrans['creFinance_id'].isNull()]))
            ossCond.append(db.joinOr([tableOrgStructureStock['finance_id'].eq(financeId), tableOrgStructureStock['finance_id'].isNull()]))
        elif QtGui.qApp.controlSMFinance() == 2:
            debCond.append(tableStockTrans['debFinance_id'].eq(financeId))
            creCond.append(tableStockTrans['creFinance_id'].eq(financeId))
            creCondFinanceTrans.append(tableStockTrans['creFinance_id'].eq(financeId))
            ossCond.append(tableOrgStructureStock['finance_id'].eq(financeId))
    elif exact:
        debCond.append(tableStockTrans['debFinance_id'].isNull())
        creCond.append(tableStockTrans['creFinance_id'].isNull())
        creCondFinanceTrans.append(tableStockTrans['creFinance_id'].isNull())
        ossCond.append(tableOrgStructureStock['finance_id'].isNull())
    if medicalAidKindId and not isStrictMedicalAidKindId:
        debCond.append(db.joinOr([tableSMI['medicalAidKind_id'].eq(medicalAidKindId), tableSMI['medicalAidKind_id'].isNull()]))
        creCond.append(db.joinOr([tableSMI['medicalAidKind_id'].eq(medicalAidKindId), tableSMI['medicalAidKind_id'].isNull()]))
        creCondFinanceTrans.append(db.joinOr([tableSMI['oldMedicalAidKind_id'].eq(medicalAidKindId), tableSMI['oldMedicalAidKind_id'].isNull()]))
    elif medicalAidKindId and isStrictMedicalAidKindId:
        debCond.append(tableSMI['medicalAidKind_id'].eq(medicalAidKindId))
        creCond.append(tableSMI['medicalAidKind_id'].eq(medicalAidKindId))
        creCondFinanceTrans.append(tableSMI['oldMedicalAidKind_id'].eq(medicalAidKindId))
    elif exact:
        debCond.append(tableSMI['medicalAidKind_id'].isNull())
        creCond.append(tableSMI['medicalAidKind_id'].isNull())
        creCondFinanceTrans.append(tableSMI['oldMedicalAidKind_id'].isNull())
    if otherHaving:
        havCond = otherHaving
    else:
        havCond = ['`qnt` > 0.0001 and ((shelfTime>=curDate()) OR shelfTime is NULL)']

    if filter:
        debCond.append(filter)
        creCond.append(filter)

    if unitId:
        unitCol = '%s AS unitId' %unitId
        unitParams = '''
(SELECT
            rbNomenclature_UnitRatio.ratio
        FROM
            rbNomenclature_UnitRatio
        WHERE
            rbNomenclature_UnitRatio.sourceUnit_id = RBUSource.id
                AND rbNomenclature_UnitRatio.targetUnit_id =  %(unitId)s
                AND rbNomenclature_UnitRatio.master_id = rbNomenclature.id) AS `ratio`,
(SELECT
        rbUnit.name
    FROM
        rbNomenclature_UnitRatio
            LEFT JOIN
        rbUnit ON rbUnit.id = rbNomenclature_UnitRatio.targetUnit_id
    WHERE
        rbNomenclature_UnitRatio.sourceUnit_id = RBUSource.id
            AND rbNomenclature_UnitRatio.targetUnit_id = %(unitId)s
            AND rbNomenclature_UnitRatio.master_id = rbNomenclature.id) AS `unitName`
        '''%{
        'unitId':unitId,
        }
    else:
        unitCol = 'RBUSource.id AS `unitId`'
        unitParams = '1'

    if medicalAidKindId:
        sqlGroupByBatchT = sqlGroupByBatchT + u'medicalAidKind_id, '
    order = u'OrgStructure.code, rbNomenclature.code, rbNomenclature.name, %s rbFinance.code'%sqlGroupByBatchT

    stmt = u'''
SELECT T.orgStructure_id,
   T.nomenclature_id,
   T.batch,
   T.shelfTime,
   T.price,
   T.medicalAidKind_id,
   T.finance_id,
   sum(T.`qnt`) AS `qnt`,
   sum(T.`sum`) AS `sum`
FROM
(
SELECT debOrgStructure_id AS orgStructure_id,
       debNomenclature_id AS nomenclature_id,
       %(batchFields)s
       StockMotion_Item.medicalAidKind_id,
       debFinance_id      AS finance_id,
       sum(StockTrans.qnt)           AS `qnt`,
       sum(StockTrans.`sum`)         AS `sum`
FROM StockTrans
LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
WHERE %(debCond)s AND StockMotion.deleted = 0 AND (StockMotion_Item.deleted=0) AND (StockMotion.type != 2)
GROUP BY debOrgStructure_id, debNomenclature_id, %(groupByBatch)s debFinance_id, medicalAidKind_id

UNION ALL
SELECT creOrgStructure_id AS orgStructure_id,
       creNomenclature_id AS nomenclature_id,
       %(batchFields)s
       StockMotion_Item.medicalAidKind_id,
       creFinance_id      AS finance_id,
       -sum(StockTrans.qnt)          AS `qnt`,
       -sum(StockTrans.`sum`)        AS `sum`
FROM StockTrans
LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
WHERE %(creCond)s AND StockMotion.deleted = 0 AND (StockMotion_Item.deleted=0) AND (StockMotion.type != 2)
GROUP BY creOrgStructure_id, creNomenclature_id, %(groupByBatch)s creFinance_id, medicalAidKind_id

UNION ALL
    SELECT debOrgStructure_id AS orgStructure_id,
       debNomenclature_id AS nomenclature_id,
       %(batchFields)s
       StockMotion_Item.medicalAidKind_id,
       debFinance_id      AS finance_id,
       sum(StockTrans.qnt)           AS `qnt`,
       sum(StockTrans.`sum`)         AS `sum`
FROM StockTrans
LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
WHERE %(debCond)s AND StockMotion.deleted = 0 AND (StockMotion_Item.deleted=0) AND (StockMotion.type = 2)
GROUP BY debOrgStructure_id, debNomenclature_id, %(groupByBatch)s debFinance_id, medicalAidKind_id

UNION ALL
SELECT creOrgStructure_id AS orgStructure_id,
       creNomenclature_id AS nomenclature_id,
       %(batchFields)s
       StockMotion_Item.oldMedicalAidKind_id AS medicalAidKind_id,
       StockMotion_Item.oldFinance_id      AS finance_id,
       -sum(StockTrans.qnt)          AS `qnt`,
       -sum(StockTrans.`sum`)        AS `sum`
FROM StockTrans
LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
WHERE %(creCondFinanceTrans)s AND StockMotion.deleted = 0 AND (StockMotion_Item.deleted=0) AND (StockMotion.type = 2)
GROUP BY creOrgStructure_id, creNomenclature_id, %(groupByBatch)s creFinance_id, medicalAidKind_id

UNION ALL
SELECT master_id          AS orgStructure_id,
       nomenclature_id    AS nomenclature_id,
       ''                 AS batch,
       NULL               AS shelfTime,
       0                  AS price,
       NULL               AS medicalAidKind_id,
       finance_id         AS finance_id,
       0                  AS `qnt`,
       0                  AS `sum`
FROM OrgStructure_Stock
WHERE %(ossCond)s
GROUP BY price, master_id, nomenclature_id, finance_id, medicalAidKind_id
) AS T
LEFT JOIN OrgStructure ON OrgStructure.id = T.orgStructure_id
LEFT JOIN rbNomenclature ON rbNomenclature.id = T.nomenclature_id
LEFT JOIN rbUnit AS RBUSource ON rbNomenclature.defaultStockUnit_id = RBUSource.id
LEFT JOIN rbFinance ON rbFinance.id = T.finance_id
LEFT JOIN OrgStructure_Stock ON OrgStructure_Stock.master_id = T.orgStructure_id
      AND OrgStructure_Stock.nomenclature_id = T.nomenclature_id
      AND OrgStructure_Stock.finance_id = T.finance_id
GROUP BY orgStructure_id, nomenclature_id, %(groupByBatchT)s finance_id, medicalAidKind_id
HAVING (%(havCond)s)
ORDER BY %(orderBy)s
''' % {
    'debCond' : db.joinAnd(debCond) if debCond else '1',
    'creCond' : db.joinAnd(creCond) if creCond else '1',
    'creCondFinanceTrans' : db.joinAnd(creCondFinanceTrans) if creCondFinanceTrans else '1',
    'ossCond' : db.joinAnd(ossCond) if ossCond else '1',
    'havCond' : db.joinAnd(havCond),
    'groupByBatch' : sqlGroupByBatch,
    'groupByBatchT' : sqlGroupByBatchT,
    'batchFields'  : batchFields,
    'unitCol':unitCol,
    'unitParams':unitParams,
    'orderBy': orderBy if orderBy else order
    }
    return stmt


FILTER_FOR_BATCH = 0
FILTER_FOR_SHELF_TIME = 1
FILTER_FOR_FINANCE_ID = 2
FILTER_FOR_FINANCE_AND_SHELF_TIME = 3
FILTER_FOR_FINANCE_AND_BATCH = 4
FILTER_FOR_BATCH_AND_SHELF_TIME = 5
UTILIZATION = 6
FILTER_FOR_FINANCE_AND_SHELF_TIME_FOR_UTILIZATION = 7
FILTER_FOR_BATCH_AND_FINANCE_FOR_UTILIZATION = 8
INTERNAL_CONSUMPTION = 9
FILTER_FOR_BATCH_FOR_COMBOBOX = 10


def findFinanceBatchShelfTime(orgStructureId, nomenclatureId, qnt=None, stockMotionItem=None, filterFor=None, financeId=None, clientId=None,  first=True, medicalAidKind = None, oldUnitId=None):
    db = QtGui.qApp.db
    table = db.table('StockTrans')
    tableSMI = db.table('StockMotion_Item')
    tableOSS = db.table('OrgStructure_Stock')

    debCond = []
    creCond = []
    creCondTrans = []
    ossCond = []

#    inventoryLastDate = getInventoryLastDate(orgStructureId)
#    if inventoryLastDate:
#        debCond.append(table['date'].dateGe(inventoryLastDate))
#        creCond.append(table['date'].dateGe(inventoryLastDate))
#        creCondTrans.append(table['date'].dateGe(inventoryLastDate))

    debCond.append(table['debOrgStructure_id'].eq(orgStructureId))
    creCond.append(table['creOrgStructure_id'].eq(orgStructureId))
    creCondTrans.append(table['creOrgStructure_id'].eq(orgStructureId))
    ossCond.append(tableOSS['master_id'].eq(orgStructureId))

    debCond.append(table['debNomenclature_id'].eq(nomenclatureId))
    creCond.append(table['creNomenclature_id'].eq(nomenclatureId))
    creCondTrans.append(table['creNomenclature_id'].eq(nomenclatureId))
    ossCond.append(tableOSS['nomenclature_id'].eq(nomenclatureId))

    batchFields = 'StockTrans.batch AS batch, StockTrans.shelfTime AS shelfTime, StockTrans.price AS price,'
    sqlGroupByBatch = 'StockTrans.batch, medicalAidKind_id, StockTrans.shelfTime, StockTrans.price, '
    sqlOrderByBatch = 'T.medicalAidKind_id, T.shelfTime, T.batch, T.price, '

    shelfTimeFilterIsSet = False

    havCond = []
    if qnt:
        havCond.append('(`qnt` >= %s)' % qnt)
    else:
        havCond.append('(`qnt` > 0)')

    if stockMotionItem and filterFor is not None:
        if filterFor == FILTER_FOR_BATCH:
            debCond.append(table['debFinance_id'].eq(stockMotionItem.finance_id))
            creCond.append(table['creFinance_id'].eq(stockMotionItem.finance_id))
            creCondTrans.append(table['creFinance_id'].eq(stockMotionItem.finance_id))

            debCond.append(db.joinOr([table['shelfTime'].dateLe(stockMotionItem.shelfTime), table['shelfTime'].isNull()]))
            creCond.append(db.joinOr([table['shelfTime'].dateLe(stockMotionItem.shelfTime), table['shelfTime'].isNull()]))
            creCondTrans.append(db.joinOr([table['shelfTime'].dateLe(stockMotionItem.shelfTime), table['shelfTime'].isNull()]))

            shelfTimeFilterIsSet = True

        elif filterFor == FILTER_FOR_FINANCE_ID:
            debCond.append(table['batch'].eq(stockMotionItem.batch))
            creCond.append(table['batch'].eq(stockMotionItem.batch))
            creCondTrans.append(table['batch'].eq(stockMotionItem.batch))

            debCond.append(db.joinOr([table['shelfTime'].dateLe(stockMotionItem.shelfTime), table['shelfTime'].isNull()]))
            creCond.append(db.joinOr([table['shelfTime'].dateLe(stockMotionItem.shelfTime), table['shelfTime'].isNull()]))
            creCondTrans.append(db.joinOr([table['shelfTime'].dateLe(stockMotionItem.shelfTime), table['shelfTime'].isNull()]))

            shelfTimeFilterIsSet = True

        elif filterFor == FILTER_FOR_SHELF_TIME:
            debCond.append(table['debFinance_id'].eq(stockMotionItem.finance_id))
            creCond.append(table['creFinance_id'].eq(stockMotionItem.finance_id))
            creCondTrans.append(table['creFinance_id'].eq(stockMotionItem.finance_id))

            debCond.append(table['batch'].eq(stockMotionItem.batch))
            creCond.append(table['batch'].eq(stockMotionItem.batch))
            creCondTrans.append(table['batch'].eq(stockMotionItem.batch))

        elif filterFor == FILTER_FOR_FINANCE_AND_SHELF_TIME:
            debCond.append(table['batch'].eq(stockMotionItem.batch))
            creCond.append(table['batch'].eq(stockMotionItem.batch))
            creCondTrans.append(table['batch'].eq(stockMotionItem.batch))

        elif filterFor == FILTER_FOR_FINANCE_AND_BATCH:
            debCond.append(db.joinOr([table['shelfTime'].dateLe(stockMotionItem.shelfTime), table['shelfTime'].isNull()]))
            creCond.append(db.joinOr([table['shelfTime'].dateLe(stockMotionItem.shelfTime), table['shelfTime'].isNull()]))
            creCondTrans.append(db.joinOr([table['shelfTime'].dateLe(stockMotionItem.shelfTime), table['shelfTime'].isNull()]))

        elif filterFor == FILTER_FOR_BATCH_AND_SHELF_TIME:
            debCond.append(table['debFinance_id'].eq(stockMotionItem.finance_id))
            creCond.append(table['creFinance_id'].eq(stockMotionItem.finance_id))
            creCondTrans.append(table['creFinance_id'].eq(stockMotionItem.finance_id))

            shelfTimeFilterIsSet = True

    if filterFor == FILTER_FOR_FINANCE_AND_SHELF_TIME_FOR_UTILIZATION:
        debCond.append(table['batch'].eq(stockMotionItem.batch))
        creCond.append(table['batch'].eq(stockMotionItem.batch))
        creCondTrans.append(table['batch'].eq(stockMotionItem.batch))
        shelfTimeFilterIsSet = True
    elif filterFor == FILTER_FOR_BATCH_AND_FINANCE_FOR_UTILIZATION:
        debCond.append(table['debFinance_id'].eq(stockMotionItem.finance_id))
        creCond.append(table['creFinance_id'].eq(stockMotionItem.finance_id))
        creCondTrans.append(table['creFinance_id'].eq(stockMotionItem.finance_id))
        shelfTimeFilterIsSet = True
    elif filterFor == UTILIZATION:
        shelfTimeFilterIsSet = True

    if financeId and QtGui.qApp.controlSMFinance() in (1, 2):
        debCond.append(table['debFinance_id'].eq(financeId))
        creCond.append(table['creFinance_id'].eq(financeId))
        creCondTrans.append(table['creFinance_id'].eq(financeId))

    if medicalAidKind:
        debCond.append(db.joinOr([tableSMI['medicalAidKind_id'].eq(medicalAidKind), tableSMI['medicalAidKind_id'].isNull()]))
        creCond.append(db.joinOr([tableSMI['medicalAidKind_id'].eq(medicalAidKind), tableSMI['medicalAidKind_id'].isNull()]))
        creCondTrans.append(db.joinOr([tableSMI['oldMedicalAidKind_id'].eq(medicalAidKind), tableSMI['medicalAidKind_id'].isNull()]))
    elif filterFor and filterFor != UTILIZATION and filterFor != INTERNAL_CONSUMPTION and filterFor != FILTER_FOR_BATCH_FOR_COMBOBOX:
        debCond.append(tableSMI['medicalAidKind_id'].isNull())
        creCond.append(tableSMI['medicalAidKind_id'].isNull())
        creCondTrans.append(tableSMI['medicalAidKind_id'].isNull())

    if not shelfTimeFilterIsSet:
        currentDate = QDate.currentDate()
        debCond.append(db.joinOr([table['shelfTime'].dateGe(currentDate), table['shelfTime'].isNull()]))
        creCond.append(db.joinOr([table['shelfTime'].dateGe(currentDate), table['shelfTime'].isNull()]))
        creCondTrans.append(db.joinOr([table['shelfTime'].dateGe(currentDate), table['shelfTime'].isNull()]))
    reservationClient = False
    if clientId:
        financeCond = u''
        if financeId and QtGui.qApp.controlSMFinance() in (1, 2):
            financeCond = u''' AND StockMotion_Item.finance_id = %(financeId)s'''%{u'financeId':financeId}
        medicalAidKindCond = u''
        if medicalAidKind:
            medicalAidKindCond = u''' AND StockMotion_Item.medicalAidKind_id = %(medicalAidKindId)s'''%{u'medicalAidKindId':medicalAidKind}

        reservationStmt = u'''SELECT
                StockMotion_Item.finance_id,
                StockMotion_Item.batch,
                StockMotion_Item.shelfTime,
                StockMotion_Item.price,
                StockMotion_Item.medicalAidKind_id,
                StockMotion_Item.unit_id,
                StockMotion_Item.qnt
            FROM
                StockMotion
                    LEFT JOIN
                StockMotion_Item ON StockMotion_Item.master_id = StockMotion.id
            WHERE
                StockMotion_Item.`nomenclature_id` = %(nomenclatureId)s
                    AND StockMotion.type = 6
                    AND StockMotion_Item.qnt > 0
                    AND StockMotion_Item.deleted = 0
                    AND StockMotion.deleted = 0
                    AND StockMotion.client_id = %(clientId)s
                    %(financeCond)s
                    %(medicalAidKindCond)s
                    ORDER BY StockMotion_Item.shelfTime, StockMotion_Item.qnt, StockMotion_Item.price LIMIT 1'''% {
        'nomenclatureId': nomenclatureId,
        'clientId': clientId,
        'financeCond': financeCond,
        'medicalAidKindCond': medicalAidKindCond,
            }
        reservationQuery = db.query(reservationStmt)
        while reservationQuery.next():
            resQnt = False
            reservationRecord = reservationQuery.record()
            if reservationRecord:
                financeId = forceRef(reservationRecord.value('finance_id'))
                batch = forceString(reservationRecord.value('batch'))
                shelfTime = forceDate(reservationRecord.value('shelfTime'))
                medicalAidKindId = forceRef(reservationRecord.value('medicalAidKind_id'))
                price = forceDouble(reservationRecord.value('price'))
                if qnt > 0 and oldUnitId:
                    unitId = forceRef(reservationRecord.value('unit_id'))
                    smiQnt = forceDouble(reservationRecord.value('qnt'))
                    if oldUnitId == unitId:
                        if smiQnt >= qnt:
                            resQnt = True
                    elif oldUnitId != unitId:
                        if unitId is not None:
                            ratio = getRatio(nomenclatureId, oldUnitId, unitId)
                            if ratio is not None:
                                smiQnt = smiQnt/ratio
                            if smiQnt >= qnt:
                                resQnt = True
                else:
                    resQnt = True
                if resQnt and (financeId or batch or shelfTime or price):
                    reservationClient = True
                    return financeId, batch, shelfTime, medicalAidKindId, price, reservationClient

    stmt = u'''
    SELECT T.orgStructure_id,
           T.nomenclature_id,
           T.batch,
           T.shelfTime,
           T.price,
           T.finance_id,
           T.medicalAidKind_id,
           round(sum(T.`qnt`),2) AS `qnt`,
           sum(T.`sum`) AS `sum`,
           OrgStructure_Stock.constrainedQnt AS constrainedQnt,
           OrgStructure_Stock.orderQnt AS orderQnt
    FROM
        (
        SELECT StockTrans.debOrgStructure_id AS orgStructure_id,
               StockTrans.debNomenclature_id AS nomenclature_id,
               %(batchFields)s
               StockMotion_Item.medicalAidKind_id,
               StockTrans.debFinance_id      AS finance_id,
               sum(StockTrans.qnt)           AS `qnt`,
               sum(StockTrans.`sum`)         AS `sum`
        FROM StockTrans
        LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
        LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
        WHERE %(debCond)s AND StockMotion.deleted = 0 AND StockMotion_Item.deleted=0 AND (StockMotion.type != 2)
        GROUP BY debOrgStructure_id, debNomenclature_id, %(groupByBatch)s debFinance_id

        UNION ALL
        SELECT StockTrans.creOrgStructure_id AS orgStructure_id,
               StockTrans.creNomenclature_id AS nomenclature_id,
               %(batchFields)s
               StockMotion_Item.medicalAidKind_id,
               StockTrans.creFinance_id      AS finance_id,
               -sum(StockTrans.qnt)          AS `qnt`,
               -sum(StockTrans.`sum`)        AS `sum`
        FROM StockTrans
        LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
        LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
        WHERE %(creCond)s AND StockMotion.deleted = 0 AND StockMotion_Item.deleted=0 AND (StockMotion.type != 2)
        GROUP BY creOrgStructure_id, creNomenclature_id, %(groupByBatch)s creFinance_id

        UNION ALL
        SELECT StockTrans.debOrgStructure_id AS orgStructure_id,
               StockTrans.debNomenclature_id AS nomenclature_id,
               %(batchFields)s
               StockMotion_Item.medicalAidKind_id,
               StockTrans.debFinance_id      AS finance_id,
               sum(StockTrans.qnt)           AS `qnt`,
               sum(StockTrans.`sum`)         AS `sum`
        FROM StockTrans
        LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
        LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
        WHERE %(debCond)s AND StockMotion.deleted = 0 AND StockMotion_Item.deleted=0 AND (StockMotion.type = 2)
        GROUP BY debOrgStructure_id, debNomenclature_id, %(groupByBatch)s debFinance_id

        UNION ALL
        SELECT StockTrans.creOrgStructure_id AS orgStructure_id,
               StockTrans.creNomenclature_id AS nomenclature_id,
               %(batchFields)s
               StockMotion_Item.medicalAidKind_id,
               StockTrans.creFinance_id      AS finance_id,
               - sum(StockTrans.qnt)          AS `qnt`,
               - sum(StockTrans.`sum`)        AS `sum`
        FROM StockTrans
        LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
        LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
        WHERE %(creCondTrans)s AND StockMotion.deleted = 0 AND StockMotion_Item.deleted=0 AND (StockMotion.type = 2)
        GROUP BY creOrgStructure_id, creNomenclature_id, %(groupByBatch)s creFinance_id

        UNION ALL
        SELECT master_id          AS orgStructure_id,
               nomenclature_id    AS nomenclature_id,
               ''                 AS batch,
               NULL               AS shelfTime,
               0                  AS price,
               NULL               AS medicalAidKind_id,
               finance_id         AS finance_id,
               0                  AS `qnt`,
               0                  AS `sum`
        FROM OrgStructure_Stock
        WHERE %(ossCond)s
        GROUP BY master_id, nomenclature_id, finance_id, medicalAidKind_id
        ) AS T
        LEFT JOIN OrgStructure ON OrgStructure.id = T.orgStructure_id
        LEFT JOIN rbNomenclature ON rbNomenclature.id = T.nomenclature_id
        LEFT JOIN rbFinance ON rbFinance.id = T.finance_id
        LEFT JOIN OrgStructure_Stock ON OrgStructure_Stock.master_id = T.orgStructure_id
              AND OrgStructure_Stock.nomenclature_id = T.nomenclature_id
              AND OrgStructure_Stock.finance_id = T.finance_id
    GROUP BY orgStructure_id, nomenclature_id, %(orderByBatch)s finance_id, medicalAidKind_id
    HAVING (%(havCond)s)
    ORDER BY T.shelfTime, T.batch, T.price, rbFinance.code, T.medicalAidKind_id
    %(limit)s
    ''' % {
        'debCond': db.joinAnd(debCond),
        'creCond': db.joinAnd(creCond),
        'creCondTrans': db.joinAnd(creCondTrans),
        'ossCond': db.joinAnd(ossCond),
        'havCond': db.joinAnd(havCond),
        'groupByBatch': sqlGroupByBatch,
        'orderByBatch': sqlOrderByBatch,
        'batchFields': batchFields,
        'limit': "LIMIT 1" if first else ''
    }
    query = db.query(stmt)

    if first:
        if query.next():
            record = query.record()
            financeId = forceRef(record.value('finance_id'))
            batch = forceString(record.value('batch'))
            shelfTime = forceDate(record.value('shelfTime'))
            medicalAidKindId = forceRef(record.value('medicalAidKind_id'))
            price = forceDouble(record.value('price'))
            return financeId, batch, shelfTime, medicalAidKindId, price, reservationClient
        return None, None, None, None, 0, reservationClient
    else:
        result = []
        while query.next():
            record = query.record()
            financeId = forceRef(record.value('finance_id'))
            batch = forceString(record.value('batch'))
            shelfTime = forceDate(record.value('shelfTime'))
            medicalAidKindId = forceRef(record.value('medicalAidKind_id'))
            price = forceDouble(record.value('price'))
            result.append((financeId, batch, shelfTime, medicalAidKindId, price, reservationClient))
        return result


# ########################################


class CSatisifiedFilter(object):
    str_values = [u'', u'Частично', u'Полностью', u'Нет', u'С превышением']
    ALL = 0
    PARTIAL = 1
    FULL = 2
    NOT = 3
    EXCEEDING = 4

    NEED_FILTER_INDEXES = (PARTIAL, FULL, NOT, EXCEEDING)

    @classmethod
    def getFilter(cls, index, nomenclatureId=None):
        if index not in cls.NEED_FILTER_INDEXES:
            return None

        db = QtGui.qApp.db
        table = db.table('StockRequisition')
        tableItems = db.table('StockRequisition_Item')

        subcond = [
            tableItems['master_id'].eq(table['id'])
        ]

        if nomenclatureId:
            subcond.append(tableItems['nomenclature_id'].eq(nomenclatureId))

        if index == cls.PARTIAL:
            return db.selectStmtGroupBy(tableItems, u'IF((SUM(StockRequisition_Item.`satisfiedQnt`) > 0 AND SUM(StockRequisition_Item.`qnt`) > SUM(StockRequisition_Item.`satisfiedQnt`)), StockRequisition_Item.master_id, NULL)', subcond, u'StockRequisition_Item.master_id')

        elif index == cls.FULL:
            return db.selectStmtGroupBy(tableItems, u'IF(SUM(StockRequisition_Item.`qnt`) = SUM(StockRequisition_Item.`satisfiedQnt`), StockRequisition_Item.master_id, NULL)', subcond, u'StockRequisition_Item.master_id')

        elif index == cls.NOT:
            return db.selectStmtGroupBy(tableItems, u'IF(SUM(StockRequisition_Item.`satisfiedQnt`) = 0, StockRequisition_Item.master_id, NULL)', subcond, u'StockRequisition_Item.master_id')

        elif index == cls.EXCEEDING:
            return db.selectStmtGroupBy(tableItems, u'IF(SUM(StockRequisition_Item.`qnt`) < SUM(StockRequisition_Item.`satisfiedQnt`), StockRequisition_Item.master_id, NULL)', subcond, u'StockRequisition_Item.master_id')

        else:
            return None

        return db.existsStmt(tableItems, subcond)


def tuneSatisfiedFilterCmb(cmb):
    cmb.addItems(CSatisifiedFilter.str_values)


def getStockMotionItemQnt(nomenclatureId, stockMotionId=None, batch=None, financeId=None, clientId=None, medicalAidKindId=None, price=None):
        db = QtGui.qApp.db
        table = db.table('StockMotion')
        tableItems = db.table('StockMotion_Item')
        cond = [tableItems['nomenclature_id'].eq(nomenclatureId),
                table['deleted'].eq(0),
                tableItems['deleted'].eq(0)]
        if stockMotionId:
            cond.append(table['id'].eq(stockMotionId))
        if price is not None:
            cond.append(tableItems['price'].eq(price))
        if batch:
            cond.append(tableItems['batch'].eq(batch))
        if financeId: #0012562:0044803
            if QtGui.qApp.controlSMFinance() == 1:
                cond.append(db.joinOr([tableItems['finance_id'].eq(financeId), tableItems['finance_id'].isNull()]))
            elif QtGui.qApp.controlSMFinance() == 2:
                cond.append(tableItems['finance_id'].eq(financeId))
        if medicalAidKindId:
            cond.append(db.joinOr([tableItems['medicalAidKind_id'].eq(medicalAidKindId), tableItems['medicalAidKind_id'].isNull()]))
        if clientId:
            cond.append(table['client_id'].eq(clientId))
            cond.append(table['type'].eq(6))
        col = u'SUM(StockMotion_Item.qnt) as smiQnt'
        queryTable = table
        queryTable = queryTable.leftJoin(tableItems, tableItems['master_id'].eq(table['id']))
        record = db.getRecordEx(queryTable, col, cond)
        if record:
            qnt = forceDouble(record.value('smiQnt'))
        else:
            qnt = 0
        return qnt


def getStockMotionItemQntEx(nomenclatureId, stockMotionId=None, batch=None, financeId=None, clientId=None, medicalAidKindId=None, price=None, oldPrice=None, oldUnitId=None, financeField='finance_id', medicalAidKindField='medicalAidKind_id'):
        db = QtGui.qApp.db
        table = db.table('StockMotion')
        tableItems = db.table('StockMotion_Item')
        cond = [tableItems['nomenclature_id'].eq(nomenclatureId),
                table['deleted'].eq(0),
                tableItems['deleted'].eq(0)]
        if stockMotionId:
            cond.append(table['id'].eq(stockMotionId))
        if price is not None:
            cond.append(tableItems['price'].eq(price))
        if batch:
            cond.append(tableItems['batch'].eq(batch))
        if financeId: #0012562:0044803
            if QtGui.qApp.controlSMFinance() == 1:
                cond.append(db.joinOr([tableItems[financeField].eq(financeId), tableItems[financeField].isNull()]))
            elif QtGui.qApp.controlSMFinance() == 2:
                cond.append(tableItems[financeField].eq(financeId))
        if medicalAidKindId:
            cond.append(db.joinOr([tableItems[medicalAidKindField].eq(medicalAidKindId), tableItems[medicalAidKindField].isNull()]))
        if clientId:
            cond.append(table['client_id'].eq(clientId))
            cond.append(table['type'].eq(6))
        col = u'SUM(StockMotion_Item.qnt) as smiQnt, StockMotion_Item.unit_id, StockMotion_Item.price'
        queryTable = table
        queryTable = queryTable.leftJoin(tableItems, tableItems['master_id'].eq(table['id']))
        records = db.getRecordListGroupBy(queryTable, col, cond, group=u'StockMotion_Item.nomenclature_id, StockMotion_Item.unit_id, StockMotion_Item.price')
        qnt = 0
        for record in records:
            unitId = forceRef(record.value('unit_id'))
            price = forceDouble(record.value('price'))
            smiQnt = forceDouble(record.value('smiQnt'))
            if oldUnitId == unitId and price == oldPrice:
                qnt += smiQnt
            elif oldUnitId != unitId:
                if unitId is not None:
                    ratio = getRatio(nomenclatureId, oldUnitId, unitId)
                    if ratio is not None:
                        price = price*ratio
                    if  price == oldPrice:
                        if ratio is not None:
                            smiQnt = smiQnt/ratio
                        qnt += smiQnt
        return qnt


class CStockCache(object):
    def __init__(self):
        self._mapIdsToStock = {}


    def getStock(self, orgStructureId, nomenclatureId, financeId, batch=None, medicalAidKindId=None, shelfTime=None):
        if batch is not None:
            key = orgStructureId, nomenclatureId, financeId, batch, medicalAidKindId, shelfTime
        else:
            key = orgStructureId, nomenclatureId, financeId, medicalAidKindId, shelfTime
        result = self._mapIdsToStock.get(key, None)
        if result is None:
            result = self.readStock(orgStructureId, nomenclatureId, financeId, batch, medicalAidKindId, shelfTime)
            self._mapIdsToStock[key] = result
        return result


    def readStock(self, orgStructureId, nomenclatureId, financeId, batch=None, medicalAidKindId=None, shelfTime=None):
        qnt = 0.0
        sum = 0.0
        if orgStructureId and nomenclatureId:
            try:
                db = QtGui.qApp.db
                financeId = financeId if financeId is not None else 'NULL'
                if batch is not None:
                    db.query('CALL getStockForBatch(%s, %s, %s, %s, %s, NULL, %s, @resQnt, @resSum)' % (orgStructureId, nomenclatureId, financeId, medicalAidKindId if medicalAidKindId else u'NULL', db.formatDate(shelfTime) if shelfTime else u'NULL', batch if batch else u'\'\''))
                else:
                    db.query('CALL getStock(%s, %s, %s, NULL, @resQnt, @resSum)' % (orgStructureId, nomenclatureId, financeId))
                query = db.query('SELECT @resQnt, @resSum')
                if query.next():
                    record = query.record()
                    qnt = forceDouble(record.value(0))
                    sum = forceDouble(record.value(1))
            except:
                QtGui.qApp.logCurrentException()
        return qnt, sum


    def getPrice(self, orgStructureId, nomenclatureId, financeId, batch=None, medicalAidKindId=None, shelfTime=None):
        qnt, sum = self.getStock(orgStructureId, nomenclatureId, financeId, batch, medicalAidKindId, shelfTime)
        if qnt:
            return sum/qnt
        else:
            return 0.0

def calcNomenclatureSum(stockMotionItem):
    db = QtGui.qApp.db
    tableStockMotionItem = db.table('StockMotion_Item')
    tableStockMotion = db.table('StockMotion')
    cond = [tableStockMotion['type'].inlist((0, 1, 2)), tableStockMotion['deleted'].eq(0), tableStockMotionItem['deleted'].eq(0)]

    if stockMotionItem.batch:
        cond.append(tableStockMotionItem['batch'].eq(stockMotionItem.batch))
    if stockMotionItem.shelfTime:
        cond.append(tableStockMotionItem['shelfTime'].eq(stockMotionItem.shelfTime))
    if stockMotionItem.nomenclature_id:
        cond.append(tableStockMotionItem['nomenclature_id'].eq(stockMotionItem.nomenclature_id))

    queryTable = tableStockMotion
    queryTable = queryTable.leftJoin(tableStockMotionItem, tableStockMotionItem['master_id'].eq(tableStockMotion['id']))

    record = db.getRecordEx(queryTable, 'StockMotion_Item.sum / StockMotion_Item.qnt AS stockPrice', cond)
    if record:
        stockPrice = forceDouble(record.value('stockPrice'))
    else:
        stockPrice = 0

    stockUnitId = stockMotionItem.nomenclature.defaultStockUnit_id
    if stockMotionItem.unit_id == stockUnitId:
        ratio = 1
    else:
        ratio = getNomenclatureUnitRatio(stockMotionItem.nomenclature_id, stockMotionItem.unit_id, stockUnitId)
    if ratio is None:
        ratio = 0
    return stockMotionItem.qnt * ratio * stockPrice


def calcNomenclatureSumFromRecord(stockMotionItem):
    db = QtGui.qApp.db
    tableStockMotionItem = db.table('StockMotion_Item')
    tableStockMotion = db.table('StockMotion')
    cond = [tableStockMotion['type'].inlist((0, 1, 2)), tableStockMotion['deleted'].eq(0), tableStockMotionItem['deleted'].eq(0)]
    price = forceDouble(stockMotionItem.value('price'))
    if price:
        unitId = forceRef(stockMotionItem.value('unit_id'))
        nomenclatureId = forceRef(stockMotionItem.value('nomenclature_id'))
        ratio = getRatio(nomenclatureId, None, unitId)
        if ratio is not None:
            price = price*ratio
    if price:
        cond.append(tableStockMotionItem['price'].eq(price))
    if forceString(stockMotionItem.value('batch')):
        cond.append(tableStockMotionItem['batch'].eq(forceString(stockMotionItem.value('batch'))))
    else:
        cond.append(tableStockMotionItem['batch'].eq(u''))
    if forceDate(stockMotionItem.value('shelfTime')):
        cond.append(tableStockMotionItem['shelfTime'].eq(forceDate(stockMotionItem.value('shelfTime'))))
    else:
        cond.append(tableStockMotionItem['shelfTime'].isNull())
    if forceInt(stockMotionItem.value('nomenclature_id')):
        cond.append(tableStockMotionItem['nomenclature_id'].eq(forceInt(stockMotionItem.value('nomenclature_id'))))
    if forceInt(stockMotionItem.value('finance_id')):
        cond.append(tableStockMotionItem['finance_id'].eq(forceInt(stockMotionItem.value('finance_id'))))
    else:
        cond.append(tableStockMotionItem['finance_id'].isNull())
    if forceInt(stockMotionItem.value('medicalAidKind_id')):
        cond.append(tableStockMotionItem['medicalAidKind_id'].eq(forceInt(stockMotionItem.value('medicalAidKind_id'))))
    else:
        cond.append(tableStockMotionItem['medicalAidKind_id'].isNull())

    queryTable = tableStockMotion
    queryTable = queryTable.leftJoin(tableStockMotionItem, tableStockMotionItem['master_id'].eq(tableStockMotion['id']))

#    record = db.getRecordEx(queryTable, 'StockMotion_Item.sum / StockMotion_Item.qnt AS stockPrice', cond)
    record = db.getRecordEx(queryTable, 'StockMotion_Item.price AS stockPrice', cond)
    if record:
        stockPrice = forceDouble(record.value('stockPrice'))
    else:
        stockPrice = 0

    stockUnitId = forceInt(db.translate('rbNomenclature', 'id', forceInt(stockMotionItem.value('nomenclature_id')), 'defaultStockUnit_id'))
    if forceInt(stockMotionItem.value('unit_id')) == stockUnitId:
        ratio = 1
    else:
        ratio = getNomenclatureUnitRatio(forceInt(stockMotionItem.value('nomenclature_id')), forceInt(stockMotionItem.value('unit_id')), stockUnitId)
    return forceDouble(stockMotionItem.value('qnt')) * ratio * stockPrice


def checkNomenclatureExists(self, keys, item, supplierId=None):
    db = QtGui.qApp.db
    nomenclatureId, financeId, batch, supplierId, stockUnitId, medicalAidKindId, shelfTimePyDate, price = keys
    shelfTime = forceDate(shelfTimePyDate)
    supplierId = supplierId or self.cmbSupplier.value()
    qnt = item[0]
    shelfTimeString = item[1]
    medicalAidKindName = item[2]
    rows = item[3]
    row = rows[0] if len(rows) > 0 else -1
    existsQnt = getExistsNomenclatureAmountEx(nomenclatureId, financeId, batch, supplierId, stockUnitId, medicalAidKindId, shelfTime, exact=True, price=price)
    prevQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=self._id, batch=batch, financeId=financeId, medicalAidKindId=medicalAidKindId, price=None, oldPrice=price, oldUnitId=stockUnitId), QtGui.qApp.numberDecimalPlacesQnt()) if self._id else 0
    if (round(existsQnt, QtGui.qApp.numberDecimalPlacesQnt()) + prevQnt) - round(qnt, QtGui.qApp.numberDecimalPlacesQnt()) < 0:
        nomenclatureName = self.modelItems.getNomenclatureNameById(nomenclatureId)
        if existsQnt > 0:
            message = u'На складе {0} {7} {1} партии "{3}" годный до "{4}" типа финансирования "{5}" вида мед помощи "{6}", а списание на {2}'.format(   existsQnt,
                                                                                                                                                nomenclatureName,
                                                                                                                                                qnt,
                                                                                                                                                batch if batch else u'не указано',
                                                                                                                                                shelfTimeString if shelfTime else u'не указано',
                                                                                                                                                forceString(db.translate('rbFinance', 'id', financeId, 'name')) if financeId else u'не указано',
                                                                                                                                                medicalAidKindName if medicalAidKindName else u'не указано',
                                                                                                                                                forceString(db.translate('rbUnit', 'id', stockUnitId, 'name')))
        else:
            message = u'На складе отсутствует "{1}" партии "{3}" годный до "{4}" типа финансирования "{5}" вида мед помощи "{6}"'.format(   existsQnt,
                                                                                                                                    nomenclatureName,
                                                                                                                                    qnt,
                                                                                                                                    batch if batch else u'не указано',
                                                                                                                                    shelfTimeString if shelfTime else u'не указано',
                                                                                                                                    forceString(db.translate('rbFinance', 'id', financeId, 'name')) if financeId else u'не указано',
                                                                                                                                    medicalAidKindName if medicalAidKindName else u'не указано')
        return self.checkValueMessage(message, False, self.tblItems, row, self.modelItems.qntColumnIndex)
    return True


class CBatchItemDelegate(CLocItemDelegate):
    def createEditor(self, parent, option, index):
        column = index.column()
        row = index.row()
        editor = index.model().createBatchEditor(row, parent)
        self.connect(editor, SIGNAL('commit()'), self.emitCommitData)
        self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        self.editor   = editor
        self.row      = row
        self.rowcount = index.model().rowCount(None)
        self.column   = column
        return editor


    def setEditorData(self, editor, index):
        if editor is not None:
            row    = index.row()
            model  = index.model()
            if row < len(model.items()):
                record = model.items()[row]
            else:
                record = model.getEmptyRecord()
            model.setBatchEditorData(row, editor, model.data(index, Qt.EditRole), record)


    def setModelData(self, editor, model, index):
        if editor is not None:
            model.setData(index, index.model().getBatchEditorData(index.row(), editor))


class CPriceItemDelegate(CLocItemDelegate):
    def createEditor(self, parent, option, index):
        column = index.column()
        row = index.row()
        editor = index.model().createPriceEditor(row, column, parent)
        self.connect(editor, SIGNAL('commit()'), self.emitCommitData)
        self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        self.editor   = editor
        self.row      = row
        self.rowcount = index.model().rowCount(None)
        self.column   = column
        return editor


    def setEditorData(self, editor, index):
        if editor is not None:
            row    = index.row()
            model  = index.model()
            if row < len(model.items()):
                record = model.items()[row]
            else:
                record = model.getEmptyRecord()
            model.setPriceEditorData(row, editor, model.data(index, Qt.EditRole), record)
            editor.lineEdit().selectAll()


    def setModelData(self, editor, model, index):
        if editor is not None:
            model.setData(index, index.model().getPriceEditorData(index.row(), editor))


class CSummaryInfoModelMixin:
    def getSummaryInfo(self):
        totalQnt = 0.0
        totalSum = 0.0
        totalVat = 0.0
        cnt = len(self._items)
        for item in self._items:
            totalQnt += forceDouble(item.value('qnt'))
            totalSum += forceDouble(item.value('sum'))
            totalVat += forceDouble(item.value('vat'))
        return u'Количество позиций: %d, Количество: %.2f, Сумма: %.2f, Сумма НДС: %.2f' % (cnt, totalQnt, totalSum, totalVat)


class CPlaceOfBusinessComboBox(QComboBox):
    popupShow = pyqtSignal()

    def __init__(self, parent):
        QtGui.QComboBox.__init__(self, parent)
        self.readOnly = False

    def setReadOnly(self, value=False):
        self.readOnly = value

    def isReadOnly(self):
        return self.readOnly

    def showPopup(self):
        if not self.isReadOnly():
            self.popupShow.emit()
            super(CPlaceOfBusinessComboBox, self).showPopup()


class CContractTypeComboBox(QComboBox):
    def setItems(self):
        self.insertItem(0, u'не задано')
        for k, v in contractTypeDict.items():
            self.insertItem(k, u'%s | %s' % (k, v))


class CDestructionTypeComboBox(QComboBox):
    def setItems(self):
        for k, v in destructionTypeDict.items():
            self.insertItem(k, u'%s | %s' % (k, v))


class CReasonDestructionTypeComboBox(QComboBox):
    def setItems(self):
        for k, v in reasonDestructionTypeDict.items():
            self.insertItem(k, u'%s | %s' % (k, v))
