# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2026 SAMSON Group. All rights reserved.
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

from library.Utils      import forceBool, forceInt, forceRef, forceString, forceStringEx, smartDict

from Orgs.Utils         import CNet, getOrgStructureDescendants, getOrgStructureNetId, getOrgStructures
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Registry.Utils     import formatAddressInt
from Orgs.OrgStructComboBoxes import COrgStructureModel


def selectData(endDate, ageFrom, ageTo, areaId, addressType, isServiceArea):
    stmt="""
SELECT
   COUNT(Client.id) as cnt,
   %(orgStructField)s AS repOrgStructure_id,
   age(Client.birthDate, %(attachCheckDate)s) AS clientAge,
   Client.sex AS clientSex,
   IF(ClientAttach.id IS NULL,0,1) AS attached  %(serviceAreaField)s
FROM Client
%(joins)s
LEFT JOIN ClientAttach  ON ClientAttach.client_id = Client.id
                        AND ClientAttach.id = (SELECT MAX(CAT.id) FROM ClientAttach AS CAT
                                               LEFT JOIN rbAttachType ON rbAttachType.id=CAT.attachType_id
                                               WHERE CAT.deleted=0
                                               AND   CAT.client_id=Client.id
                                               AND   rbAttachType.temporary=0
                                               AND   CAT.begDate<=%(attachCheckDate)s
                                               AND   (CAT.endDate IS NULL or CAT.endDate>=%(attachCheckDate)s)
                                              )
                        AND %(attachToArea)s
LEFT JOIN rbAttachType ON rbAttachType.id=ClientAttach.attachType_id
%(serviceAreaJoin)s
WHERE %(mainCond)s
GROUP BY repOrgStructure_id, clientAge, clientSex, attached %(groupBy)s
    """
    db = QtGui.qApp.db
    tableClient  = db.table('Client')
    tableOrgStructureAddress = db.table('OrgStructure_Address')
    tableClientAttach = db.table('ClientAttach')
    tableAttachType = db.table('rbAttachType')
    cond = []
    cond.append(tableClient['deleted'].eq(0))
    cond.append( db.joinOr([ tableAttachType['outcome'].eq(0),
                             tableAttachType['outcome'].isNull()]))
#    cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))

#    if eventTypeIdList:
#        cond.append(tableEvent['eventType_id'].inlist(eventTypeIdList))
    if ageFrom <= ageTo:
        # для проверки логики:
        # если взять ageFrom == ageTo == 0 то
        # должны получиться дети родившиеся за последний год,
        # а годовалые уже не подходят
        cond.append(tableClient['birthDate'].gt(endDate.addYears(-ageTo-1)))
        cond.append(tableClient['birthDate'].le(endDate.addYears(-ageFrom)))
#    if areaId:
#        cond.append(tableOrgStructureAddress['master_id'].inlist(getOrgStructureDescendants(areaId)))
    if areaId:
        areaIdList = getOrgStructureDescendants(areaId)
    else:
        areaIdList = getOrgStructures(QtGui.qApp.currentOrgId())
    reg = (addressType+1) & 1
    loc = (addressType+1) & 2
    attach = (addressType+1) & 4
    condAddr = []
    joins = ''
    if reg:
        tableOrgStructureAddress = db.table('OrgStructure_Address').alias('OSAReg')
        condAddr.append(tableOrgStructureAddress['master_id'].inlist(areaIdList))
        joins += '''
LEFT JOIN ClientAddress AS CAReg ON CAReg.client_id = Client.id
                        AND CAReg.id = (SELECT MAX(CARegInt.id) FROM ClientAddress AS CARegInt WHERE CARegInt.type=0 AND CARegInt.client_id=Client.id)
LEFT JOIN Address       AS AReg ON AReg.id = CAReg.address_id
LEFT JOIN OrgStructure_Address AS OSAReg ON OSAReg.house_id = AReg.house_id AND %s
''' % (tableOrgStructureAddress['master_id'].inlist(areaIdList))
    if loc:
        tableOrgStructureAddress = db.table('OrgStructure_Address').alias('OSALoc')
        condAddr.append(tableOrgStructureAddress['master_id'].inlist(areaIdList))
        joins += '''
LEFT JOIN ClientAddress AS CALoc ON CALoc.client_id = Client.id
                        AND CALoc.id = (SELECT MAX(CALocInt.id) FROM ClientAddress AS CALocInt WHERE CALocInt.type=1 AND CALocInt.client_id=Client.id)
LEFT JOIN Address       AS ALoc ON ALoc.id = CALoc.address_id
LEFT JOIN OrgStructure_Address AS OSALoc ON OSALoc.house_id = ALoc.house_id AND %s
''' % (tableOrgStructureAddress['master_id'].inlist(areaIdList))
    if attach:
        condAddr.append(db.joinAnd([tableClientAttach['orgStructure_id'].inlist(areaIdList),
                                    tableClientAttach['deleted'].eq(0)
                                   ]))
    if condAddr:
        cond.append(db.joinOr(condAddr))
    serviceAddressHouse = u''
    if attach:
        if loc:
            if reg:
                orgStructField = 'IF(ClientAttach.orgStructure_id IS NOT NULL, ClientAttach.orgStructure_id, IF(OSALoc.master_id IS NOT NULL, OSALoc.master_id, OSAReg.master_id))'
                serviceAddressHouse = u'IF(OSALoc.master_id IS NOT NULL, ALoc.house_id, AReg.house_id)'
            else:
                orgStructField = 'IF(ClientAttach.orgStructure_id IS NOT NULL, ClientAttach.orgStructure_id, OSALoc.master_id)'
                serviceAddressHouse = u'ALoc.house_id'
        else:
            if reg:
                orgStructField = 'IF(ClientAttach.orgStructure_id IS NOT NULL, ClientAttach.orgStructure_id, OSAReg.master_id)'
                serviceAddressHouse = u'AReg.house_id'
            else:
                orgStructField = 'ClientAttach.orgStructure_id'
                serviceAddressHouse = ''' (SELECT ALoc.house_id
                                           FROM ClientAddress AS CALoc
                                                LEFT JOIN Address AS ALoc ON ALoc.id = CALoc.address_id
                                                LEFT JOIN OrgStructure_Address AS OSALoc ON OSALoc.house_id = ALoc.house_id
                                           WHERE CALoc.client_id = Client.id
                                                AND CALoc.id = (SELECT MAX(CALocInt.id) FROM ClientAddress AS CALocInt WHERE CALocInt.type=1 AND CALocInt.client_id=Client.id AND CALocInt.deleted = 0)
                                                AND CALoc.deleted = 0 AND ALoc.deleted = 0 AND OSALoc.master_id = ClientAttach.orgStructure_id
                                           LIMIT 1
                                          )''' % {'orgStructField' : orgStructField}
    else:
        if loc:
            if reg:
                orgStructField = 'IF(OSALoc.master_id IS NOT NULL, OSALoc.master_id, OSAReg.master_id)'
                serviceAddressHouse = u'IF(OSALoc.master_id IS NOT NULL, ALoc.house_id, AReg.house_id)'
            else:
                orgStructField = 'OSALoc.master_id'
                serviceAddressHouse = u'ALoc.house_id'
        else:
            if reg:
                orgStructField = 'OSAReg.master_id'
                serviceAddressHouse = u'AReg.house_id'
            else:
                orgStructField = 'NULL'
    serviceAreaField = u''
    serviceAreaJoin = u''
    grouping = u''
    if bool(isServiceArea and orgStructField and orgStructField != 'NULL' and serviceAddressHouse):
        serviceAreaJoin = u'''LEFT JOIN AddressHouse AS AH ON (AH.id IN (SELECT OSA.house_id
                                                                         FROM OrgStructure_Address AS OSA
                                                                         WHERE OSA.master_id = (%(orgStructField)s))
                                                               AND AH.id = (%(serviceAddressHouse)s)
                                                               AND AH.deleted = 0)'''% {'orgStructField' : orgStructField,
                                                                                        'serviceAddressHouse' : serviceAddressHouse}
        serviceAreaField = u', AH.id AS addressHouseId, AH.KLADRCode, AH.KLADRStreetCode, AH.number, AH.corpus'
        grouping += u', addressHouseId'
    #print stmt % {'orgStructField' : orgStructField,
    #                        'attachCheckDate': tableClient['birthDate'].formatValue(endDate),
    #                        'attachToArea'   : tableClientAttach['orgStructure_id'].inlist(areaIdList),
    #                        'serviceAreaField': serviceAreaField,
    #                        'joins'          : joins,
    #                        'serviceAreaJoin': serviceAreaJoin,
    #                        'mainCond'       : db.joinAnd(cond)}
    # cond.append(tableClient['endDate'].isNull())
    cond.append(u'((Client.endDate IS NOT NULL and ClientAttach.id IS NOT NULL) or Client.endDate IS NULL)')

    return db.query(stmt % {'orgStructField' : orgStructField,
                            'attachCheckDate': tableClient['birthDate'].formatValue(endDate),
                            'attachToArea'   : tableClientAttach['orgStructure_id'].inlist(areaIdList),
                            'serviceAreaField': serviceAreaField,
                            'joins'          : joins,
                            'serviceAreaJoin': serviceAreaJoin,
                            'mainCond'       : db.joinAnd(cond),
                            'groupBy'        : grouping
                                        })

def fakeAgeTuple(age):
    return (age*365,
            age*365/7,
            age*12,
            age
           )


class CPopulationStructure(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Состав населения по участкам')


    def getSetupDialog(self, parent):
        result = CPopulationStructureSetupDialog(parent)
        result.setTitle(self.title())
        return result


    def build(self, params):
        endDate = params.get('endDate', QDate())
        ageFrom = params.get('ageFrom', 0)
        ageTo = params.get('ageTo', 150)
        orgStructureId = params.get('orgStructureId', None)
        addressType = params.get('addressOrgStructureType', 0)
        isServiceArea = params.get('isServiceArea', False)
        rowSize = 4
        query = selectData(endDate, ageFrom, ageTo, orgStructureId, addressType, isServiceArea)
        reportData = {}
        mapAreaIdToNetId = {}
        mapNetIdToNet = {}
        while query.next():
            record    = query.record()
            areaId    = forceInt(record.value('repOrgStructure_id'))
            if areaId in mapAreaIdToNetId:
                netId = mapAreaIdToNetId[areaId]
            else:
                netId = getOrgStructureNetId(areaId)
                mapAreaIdToNetId[areaId] = netId
            if netId in mapNetIdToNet:
                net = mapNetIdToNet[netId]
            else:
                net = CNet(netId)
                mapNetIdToNet[netId] = net

            age = forceInt(record.value('clientAge'))
            sex = forceInt(record.value('clientSex'))
            if net.applicable(sex, fakeAgeTuple(age)):
                cnt       = forceInt(record.value('cnt'))
                attached  = forceBool(record.value('attached'))

                if isServiceArea:
                    addressHouseId = forceRef(record.value('addressHouseId'))
                    address = smartDict()
                    address.KLADRCode = forceStringEx(record.value('KLADRCode'))
                    address.KLADRStreetCode = forceStringEx(record.value('KLADRStreetCode'))
                    address.number = forceString(record.value('number'))
                    address.corpus = forceString(record.value('corpus'))
                    address.flat = ''
                    address.freeInput = ''
                    addressHouse = formatAddressInt(address)
                    reportLine = reportData.get(areaId, {})
                    reportRow = reportLine.get((addressHouseId, addressHouse), [0]*rowSize)
                    reportRow[0] += cnt
                    if sex == 1:
                        reportRow[1] += cnt
                    else:
                        reportRow[2] += cnt
                    if attached:
                        reportRow[3] += cnt
                    reportLine[(addressHouseId, addressHouse)] = reportRow
                    reportData[areaId] = reportLine
                else:
                    reportRow = reportData.get(areaId, None)
                    if not reportRow:
                        reportRow = [0]*rowSize
                        reportData[areaId] = reportRow
                    reportRow[0] += cnt
                    if sex == 1:
                        reportRow[1] += cnt
                    else:
                        reportRow[2] += cnt
                    if attached:
                        reportRow[3] += cnt

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('30%', [u'Подразделение'], CReportBase.AlignLeft),
            ('10%', [u'всего'], CReportBase.AlignRight),
            ('10%', [u'М'], CReportBase.AlignRight),
            ('10%', [u'Ж'], CReportBase.AlignRight),
            ('10%', [u'Прикр.'], CReportBase.AlignRight),
            ]

        table = createTable(cursor, tableColumns)
        self.genOrgStructureReport(table, reportData, rowSize, orgStructureId, isServiceArea)
        return doc


    def genOrgStructureReport(self, table, reportData, rowSize, orgStructureId, isServiceArea = False):
        model = COrgStructureModel(None, QtGui.qApp.currentOrgId())
        index = model.findItemId(orgStructureId)
        if index:
            item = index.internalPointer()
        else:
            item = model.getRootItem()
        self.genOrgStructureReportForItem(table, reportData, item, rowSize, isServiceArea)


    def dataPresent(self, reportData, item):
        row = reportData.get(item.id(), None)
        if item.areaType() or (row and any(row)):
            return True
        for subitem in item.items():
            if self.dataPresent(reportData, subitem):
                return True
        return False


    def genOrgStructureReportForItem(self, table, reportData, item, rowSize, isServiceArea = False):
        if self.dataPresent(reportData, item):
            i = table.addRow()
            if isServiceArea:
                if item.childCount() == 0:
                    reportRowTotal = [0]*rowSize
                    reportLine = reportData.get(item.id(), {})
                    table.setText(i, 0, item.name())
                    keysList = reportLine.keys()
                    keysList.sort(key=lambda item: item[1])
                    for addressHouseId, addressHouse in keysList:
                        reportRow = reportLine.get((addressHouseId, addressHouse), [0]*rowSize)
                        i = table.addRow()
                        table.setText(i, 0, addressHouse)
                        for j in xrange(rowSize):
                            table.setText(i, j+1, reportRow[j])
                            reportRowTotal[j] += reportRow[j]
                    return reportRowTotal
                else:
                    table.mergeCells(i,0, 1, rowSize+1)
                    table.setText(i, 0, item.name(), CReportBase.TableHeader)
                    total = [0]*rowSize
                    reportLine = reportData.get(item.id(), {})
                    keysList = reportLine.keys()
                    keysList.sort(key=lambda item: item[1])
                    for addressHouseId, addressHouse in keysList:
                        reportRow = reportLine.get((addressHouseId, addressHouse), [0]*rowSize)
                        i = table.addRow()
                        table.setText(i, 0, addressHouse, CReportBase.TableHeader)
                        for j in xrange(rowSize):
                            table.setText(i, j+1, reportRow[j])
                            total[j] += reportRow[j]
                    for subitem in item.items():
                        reportRow = self.genOrgStructureReportForItem(table, reportData, subitem, rowSize, isServiceArea)
                        if reportRow:
                            for j in xrange(rowSize):
                                total[j] += reportRow[j]
                    i = table.addRow()
                    table.setText(i, 0, u'всего по '+item.name(), CReportBase.TableTotal)
                    for j in xrange(rowSize):
                        table.setText(i, j+1, total[j], CReportBase.TableTotal)
                    return total
            else:
                if item.childCount() == 0:
                    row = reportData.get(item.id(), None)
                    table.setText(i, 0, item.name())
                    if row:
                        for j in xrange(rowSize):
                            table.setText(i, j+1, row[j])
                    return row
                else:
                    table.mergeCells(i,0, 1, rowSize+1)
                    table.setText(i, 0, item.name(), CReportBase.TableHeader)
                    total = [0]*rowSize
                    row = reportData.get(item.id(), None)
                    if row:
                        i = table.addRow()
                        table.setText(i, 0, '-', CReportBase.TableHeader)
                        for j in xrange(rowSize):
                            table.setText(i, j+1, row[j])
                            total[j] += row[j]
                    for subitem in item.items():
                        row = self.genOrgStructureReportForItem(table, reportData, subitem, rowSize, isServiceArea)
                        if row:
                            for j in xrange(rowSize):
                                total[j] += row[j]
                    i = table.addRow()
                    table.setText(i, 0, u'всего по '+item.name(), CReportBase.TableTotal)
                    for j in xrange(rowSize):
                        table.setText(i, j+1, total[j], CReportBase.TableTotal)
                    return total
        else:
            return None



from Ui_PopulationStructureSetup import Ui_PopulationStructureSetupDialog


class CPopulationStructureSetupDialog(QtGui.QDialog, Ui_PopulationStructureSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.patientRequired = False
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 150))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbAddressOrgStructureType.setCurrentIndex(params.get('addressOrgStructureType', 0))
        self.chkServiceAreaDetail.setChecked(params.get('isServiceArea', False))


    def params(self):
        result = {}
        result['endDate'] = self.edtEndDate.date()
        result['ageFrom'] = self.edtAgeFrom.value()
        result['ageTo'] = self.edtAgeTo.value()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['isFilterAddressOrgStructure'] = True
        result['addressOrgStructureType'] = self.cmbAddressOrgStructureType.currentIndex()
        result['addressOrgStructure'] = self.cmbOrgStructure.value()
        result['isServiceArea'] = self.chkServiceAreaDetail.isChecked()
        return result
