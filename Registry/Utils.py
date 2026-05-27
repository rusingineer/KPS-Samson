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
from collections import namedtuple

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QVariant, SIGNAL, QDateTime

from datetime import timedelta, datetime

from Exchange import AttachService
from RefBooks.DeathPlaceType.Info import CDeathPlaceTypeInfo
from RefBooks.DocumentType.Descr import getDocumentTypeDescr
from RefBooks.NomenclatureActiveSubstance.Info import CNomenclatureActiveSubstanceInfo
from KLADR.KLADRModel      import getExactCityName
from Orgs.PersonInfo       import CSpecialityInfo
from library.Counter import CCounterController
from library.Identification import getIdentificationByCode, getIdentificationInfoById
from library.database      import decorateString
from library.DialogBase    import CDialogBase
from library.DbComboBox    import CDbModel
from library.DbEntityCache import CDbEntityCache
from library.PrintInfo import CInfoContext, CInfo, CInfoList, CDateInfo, CDateTimeInfo, CRBInfo, CTimeInfo, \
    CDictInfoMixin, CRBInfoWithIdentification, CIdentificationInfoMixin
from library.Utils import calcAge, calcAgeTuple, forceBool, forceDate, forceDateTime, forceDouble, forceInt, forceRef, \
    forceString, forceStringEx, forceTime, formatAgeTuple, formatDate, formatName, formatNameInt, formatSex, \
    formatShortName, formatShortNameInt, formatSNILS, smartDict, toVariant, trim, formatDateTime
from library.ROComboBox    import CROComboBox
from Events.ActionStatus   import CActionStatus
import platform
from Events.MKBInfo        import CMKBInfo
from KLADR.KLADRModel      import getCityName, getStreetName, getKladrTreeModel, getOKATO, getDistrictName, getMainRegionName
from Orgs.PersonInfo       import CPersonInfo
from Orgs.Utils            import CNet, COrgInfo, COrgStructureInfo, CSexAgeConstraint, getOrganisationShortName, getOrgStructureDescendants, getOrgStructureNetId, getPersonOrgStructureChiefs
from RefBooks.QuotaType.List    import getQuotaTypeClassNameList
from RefBooks.BloodType.Info    import CBloodTypeInfo
from RefBooks.DocumentType.Info import CDocumentTypeInfo
from RefBooks.RiskFactor.Info   import CRBRiskFactorInfo
from Users.Rights import (urRegWriteInsurOfficeMark,
                          urRegEditTempInvalidWithInsurance,
                          urRegEditTempInvalidNoInsurance,
                          urEditOtherpeopleAction,
                          urEditClosedEvent,
                          urEditAfterInvoicingEvent,
                          urEditSubservientPeopleAction, urDeleteEventWithTissue, urDeleteEventWithJobTicket,
                          )


expertiseClass = [(u'Нетрудоспособность', u'inspection_disability%'),
                  (u'Обслуживание',       u'inspection_case%'),
                  ]


_identification = namedtuple('identification', ('code', 'name', 'urn', 'version', 'value', 'note', 'checkDate', 'value_spr', 'name_spr', 'record'))

def replaceMask(val, repFrom, repTo):
    return unicode('REPLACE(' + val + ',' + repFrom + ',' + repTo + ')')


def getClientSexAge(clientId, date=None):
    clientSex = None
    clientAge = None
    if clientId:
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        record = db.getRecordEx(tableClient, [tableClient['sex'], tableClient['birthDate']], [tableClient['id'].eq(clientId), tableClient['deleted'].eq(0)])
        if record:
            clientSex = forceInt(record.value('sex'))
            clientAge = calcAgeTuple(forceDate(record.value('birthDate')), date if date else QDate.currentDate())
    return clientSex, clientAge


# wtf? это точно имеет отношение к списку пациентов и не может быть перенесено в другое место?
def deleteTempInvalid(widget, tempInvalidId, onlyPrepare=False):
    db = QtGui.qApp.db
    table = db.table('TempInvalid')
    tablePeriod = db.table('TempInvalid_Period')
    tableResult = db.table('rbTempInvalidResult')
    tableDocument = db.table('TempInvalidDocument')
    tableDocumentExport = db.table('TempInvalidDocument_Export')
    if not tempInvalidId:
        return False
    tempInvalidDocumentIdList = getTempInvalidDocumentIdList(tempInvalidId)
    if tempInvalidDocumentIdList:
        cond = [tableDocumentExport['master_id'].inlist(tempInvalidDocumentIdList),
                tableDocumentExport['success'].eq(1)
                ]
        record = db.getRecordEx(tableDocumentExport, [tableDocumentExport['id']], cond)
        documentExportId = forceRef(record.value('id')) if record else None
        if documentExportId:
            QtGui.QMessageBox.warning(widget,
                    u'Внимание',
                    u' Нельзя удалять эпизод,\n так как относящийся к нему документ экспортирован во внешние системы!',
                    QtGui.QMessageBox.Ok,
                    QtGui.QMessageBox.Ok)
            return False
#            record = db.getRecord(table, 'id, deleted', tempInvalidId)
#            if record:
#                record.setValue('deleted',  QVariant(True))
#                db.updateRecord(table, record)
#            insuranceOfficeMark = forceInt(db.translate(table, 'id', tempInvalidId, 'insuranceOfficeMark'))
    record = db.getRecordEx(table, [table['insuranceOfficeMark'], table['prev_id'], table['client_id'], table['begDate'], table['endDate']], [table['id'].eq(tempInvalidId), table['deleted'].eq(0)])
    insuranceOfficeMark = 0
    prevId = None
    clientId = None
    begDate = None
    endDate = None
    if record:
        insuranceOfficeMark = forceInt(record.value('insuranceOfficeMark'))
        prevId = forceRef(record.value('prev_id'))
        clientId = forceRef(record.value('client_id'))
        begDate = forceDate(record.value('begDate'))
        endDate = forceDate(record.value('endDate'))
    recordPrev = db.getRecordEx(table, [table['id'], table['begDate'], table['endDate']], [table['prev_id'].eq(tempInvalidId), table['deleted'].eq(0)])
    prevTempInvalidId = None
    begDateLast = None
    endDateLast = None
    if recordPrev:
        prevTempInvalidId = forceRef(recordPrev.value('id'))
        begDateLast = forceDate(recordPrev.value('begDate'))
        endDateLast = forceDate(recordPrev.value('endDate'))
    stateResult = 0
    if prevId:
        queryTable = tablePeriod.innerJoin(table, tablePeriod['master_id'].eq(table['id']))
        queryTable = queryTable.innerJoin(tableResult, tableResult['id'].eq(tablePeriod['result_id']))
        recordClosed = db.getRecordEx(queryTable, [tableResult['state']], [table['id'].eq(prevId), table['deleted'].eq(0)], 'TempInvalid_Period.endDate DESC')
        if recordClosed:
            stateResult = forceInt(recordClosed.value('state'))
    if (not prevTempInvalidId) and (not insuranceOfficeMark or (insuranceOfficeMark and QtGui.qApp.userHasRight(urRegWriteInsurOfficeMark))):
        documentLastId, number, issueDate = getLastTempInvalidDocument(tempInvalidId)
        if not documentLastId:
            if prevId:
                db.updateRecords(table.name(), table['state'].eq(stateResult), [table['id'].eq(prevId), table['deleted'].eq(0)])
            if not onlyPrepare:
                db.markRecordsDeleted(table, table['id'].eq(tempInvalidId))
                if tempInvalidDocumentIdList:
                    db.markRecordsDeleted(tableDocument, tableDocument['id'].inlist(tempInvalidDocumentIdList))
                    documentLastRecords = db.getRecordList(tableDocument, '*', [tableDocument['last_id'].inlist(tempInvalidDocumentIdList), tableDocument['deleted'].eq(0)])
                    for documentLastRecord in documentLastRecords:
                        documentLastRecord.setValue('last_id', toVariant(None))
                        db.updateRecord(tableDocument, documentLastRecord)
                return True
        else:
            clientName = getClientName(clientId)
            documentId, numberLast, issueDateLast, clientIdLast = getTempInvalidDocumentInfo(documentLastId)
            QtGui.QMessageBox.warning(widget,
                                      u'Внимание',
                                      u' Нельзя удалять документ/эпизод (%s, %s, %s),\n так как в системе существует связанный с ним документ/эпизод (%s, %s, %s)!'%(number, forceString(issueDate), clientName, numberLast, forceString(issueDateLast), clientIdLast),
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)
    elif prevTempInvalidId:
        QtGui.QMessageBox.warning(widget,
                                  u'Внимание',
                                  u' Нельзя удалять эпизод (%s - %s),\n так как в системе существует связанный с ним эпизод (%s - %s)!'%(forceString(begDate), forceString(endDate), forceString(begDateLast), forceString(endDateLast)),
                                  QtGui.QMessageBox.Ok,
                                  QtGui.QMessageBox.Ok)
    return False


def getClientName(clientId):
    clientName = u''
    if clientId:
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        recordClient = db.getRecordEx(tableClient, [tableClient['lastName'], tableClient['firstName'], tableClient['patrName'], tableClient['id']], [tableClient['id'].eq(clientId), tableClient['deleted'].eq(0)])
        if recordClient:
            clientId = forceString(recordClient.value('id'))
            lastName = forceString(recordClient.value('lastName'))
            firstName = forceString(recordClient.value('firstName'))
            patrName = forceString(recordClient.value('patrName'))
            clientName = formatNameInt(lastName, firstName, patrName) + u', ' + clientId
    return clientName


def getTempInvalidDocumentIdList(tempInvalidId):
    if tempInvalidId:
        db = QtGui.qApp.db
        table = db.table('TempInvalidDocument')
        cond = [table['deleted'].eq(0),
                table['master_id'].eq(tempInvalidId)
                ]
        return db.getDistinctIdList(table, [table['id']], cond, [table['issueDate'].name(), table['idx'].name()])
    return None


def getLastTempInvalidDocument(tempInvalidId):
    documentLastId = None
    number = u''
    issueDate = u''
    if tempInvalidId:
        db = QtGui.qApp.db
        table = db.table('TempInvalidDocument')
        tableDocumentLast = db.table('TempInvalidDocument').alias('TempInvalidDocumentLast')
        cols = [table['last_id'],
                table['number'],
                table['issueDate']
                ]
        cond = [table['deleted'].eq(0),
                table['master_id'].eq(tempInvalidId),
                table['last_id'].isNotNull(),
                tableDocumentLast['deleted'].eq(0)
                ]
        queryTable = table.innerJoin(tableDocumentLast, tableDocumentLast['id'].eq(table['last_id']))
        record = db.getRecordEx(queryTable, cols, cond, [table['issueDate'].name(), table['idx'].name()])
        if record:
            documentLastId = forceRef(record.value('last_id'))
            number = forceString(record.value('number'))
            issueDate = forceDate(record.value('issueDate'))
    return documentLastId, number, issueDate


def getTempInvalidDocumentInfo(tempInvalidDocumentId, lastBool = False):
    documentLastId = None
    number = u''
    issueDate = u''
    clientId = None
    if tempInvalidDocumentId:
        db = QtGui.qApp.db
        table = db.table('TempInvalid')
        tableDocument = db.table('TempInvalidDocument')
        tableDocumentLast = db.table('TempInvalidDocument').alias('TempInvalidDocumentLast')
        cols = [tableDocument['last_id'],
                tableDocument['number'],
                tableDocument['issueDate'],
                table['client_id']
                ]
        cond = [tableDocument['deleted'].eq(0),
                table['deleted'].eq(0),
                tableDocument['id'].eq(tempInvalidDocumentId)
                ]
        queryTable = table.innerJoin(tableDocument, tableDocument['master_id'].eq(table['id']))
        if lastBool:
            queryTable = queryTable.innerJoin(tableDocumentLast, db.joinAnd([tableDocumentLast['id'].eq(tableDocument['last_id']), tableDocumentLast['deleted'].eq(0)]))
        else:
            queryTable = queryTable.leftJoin(tableDocumentLast, db.joinAnd([tableDocumentLast['id'].eq(tableDocument['last_id']), tableDocumentLast['deleted'].eq(0)]))
        record = db.getRecordEx(queryTable, cols, cond, [tableDocument['issueDate'].name(), tableDocument['idx'].name()])
        if record:
            documentLastId = forceRef(record.value('last_id'))
            number = forceString(record.value('number'))
            issueDate = forceDate(record.value('issueDate'))
            clientId = forceRef(record.value('client_id'))
    return documentLastId, number, issueDate, clientId


def getDocumentExportId(tempInvalidDocumentId):
    if not tempInvalidDocumentId:
        return None
    db = QtGui.qApp.db
    tableDocumentExport = db.table('TempInvalidDocument_Export')
    cond = [tableDocumentExport['master_id'].eq(tempInvalidDocumentId)]
    record = db.getRecordEx(tableDocumentExport, [tableDocumentExport['id']], cond)
    documentExportId = forceRef(record.value('id')) if record else None
    return documentExportId


def getDocumentExportSuccess(tempInvalidDocumentId):
    if not tempInvalidDocumentId:
        return None
    db = QtGui.qApp.db
    tableDocumentExport = db.table('TempInvalidDocument_Export')
    cond = [tableDocumentExport['master_id'].eq(tempInvalidDocumentId),
            tableDocumentExport['success'].eq(1)
            ]
    record = db.getRecordEx(tableDocumentExport, [tableDocumentExport['id']], cond)
    documentExportId = forceRef(record.value('id')) if record else None
    return documentExportId


def getTempInvalidDocumentPrevFssStatus(tempInvalidDocumentId):
    if not tempInvalidDocumentId:
        return None
    db = QtGui.qApp.db
    tableDocument = db.table('TempInvalidDocument')
    recordLast = db.getRecordEx(tableDocument, [tableDocument['prev_id']], [tableDocument['id'].eq(tempInvalidDocumentId), tableDocument['deleted'].eq(0)])
    prevTIDId = forceRef(recordLast.value('prev_id')) if recordLast else None
    if prevTIDId:
        cond = [tableDocument['id'].eq(prevTIDId),
                tableDocument['deleted'].eq(0),
                tableDocument['fssStatus'].eq(u'R')
                ]
        record = db.getRecordEx(tableDocument, [tableDocument['id']], cond)
        return forceRef(record.value('id')) if record else None
    return None


def deleteTempInvalidDocument(widget, tempInvalidClientId, tempInvalidId, tempInvalidDocumentId):
    db = QtGui.qApp.db
    table = db.table('TempInvalid')
    documentExportId = getDocumentExportSuccess(tempInvalidDocumentId)
    if not documentExportId:
        documentExportId = getTempInvalidDocumentPrevFssStatus(tempInvalidDocumentId)
    if documentExportId:
        QtGui.QMessageBox.warning(widget,
                                  u'Внимание',
                                  u' Нельзя удалять документ,\n так как он экспортирован во внешние системы!',
                                  QtGui.QMessageBox.Ok,
                                  QtGui.QMessageBox.Ok)
        return False
    if tempInvalidId:
        record = db.getRecordEx(table, [table['insuranceOfficeMark']], [table['id'].eq(tempInvalidId), table['deleted'].eq(0)])
    insuranceOfficeMark = 0
    if record:
        insuranceOfficeMark = forceInt(record.value('insuranceOfficeMark'))
    if not insuranceOfficeMark or (insuranceOfficeMark and QtGui.qApp.userHasRight(urRegWriteInsurOfficeMark)):
        documentLastId, number, issueDate, clientId = getTempInvalidDocumentInfo(tempInvalidDocumentId, lastBool = True)
        if not documentLastId:
            return True
        else:
            clientName = getClientName(tempInvalidClientId if tempInvalidClientId else clientId)
            documentId, numberLast, issueDateLast, clientIdLast = getTempInvalidDocumentInfo(documentLastId)
            clientNameLast = getClientName(clientIdLast)
            QtGui.QMessageBox.warning(widget,
                                      u'Внимание',
                                      u' Нельзя удалять документ (%s, %s, %s),\n так как в системе существует связанный с ним документ (%s, %s, %s)!'%(number, forceString(issueDate), clientName, numberLast, forceString(issueDateLast), clientNameLast),
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)
    return False


def selectLatestRecordStmt(tableName, clientId, filter=''):
    if type(tableName) == tuple:
        tableName1, tableName2 = tableName
    else:
        tableName1 = tableName
        tableName2 = tableName
    pos = tableName2.find('AS Tmp')
    if pos < 0:
        tableName2 = tableName2 + ' AS Tmp'

    if filter:
        filter = ' AND ('+filter+')'
    return u'SELECT * FROM %s AS Main WHERE Main.client_id = %s AND Main.id = (SELECT MAX(Tmp.id) FROM %s WHERE Tmp.client_id=%s AND Tmp.deleted=0 %s)' % (tableName1, clientId, tableName2, clientId, filter)


def selectLatestRecord(tableName, clientId, filter=''):
    db = QtGui.qApp.db
    stmt = selectLatestRecordStmt(tableName, clientId, filter)
    query = db.query(stmt)
    if query.next():
        return query.record()
    else:
        return None


def getClientAddress(clientId, addrType):
    return selectLatestRecord('ClientAddress', clientId,  'type=\'%d\'' % addrType)

def rblivingAreaName(livingId):
    db = QtGui.qApp.db
    stmt = '''SELECT name FROM rbLivingArea WHERE id= %s''' % (
        livingId)
    query = db.query(stmt)
    if query.next():
        return query.record().value(0)
    else:
        return None

def getClientDistrict(KLADRCode, KLADRStreetCode, number):
    return getDistrictName(KLADRCode, KLADRStreetCode, number)
# WFT?
#    if districtId is None:
#        return None
#    else:
#        return forceString(QtGui.qApp.db.translate('District', 'id', districtId, 'name'))


def getClientAddressEx(clientId):
    addr = getClientAddress(clientId, 1)
    if not addr:
        addr = getClientAddress(clientId, 0)
    return addr


def getAddress(addressId, freeInput=None, addressDate=None):
    result = smartDict()
    result.KLADRCode = ''
    result.KLADRStreetCode = ''
    result.number = ''
    result.index_ = ''
    result.corpus = ''
    result.flat = ''
    result.index = ''
    result.freeInput = forceString(freeInput) if freeInput else ''
    result.livingArea = ''
    result.addressDate = forceDate(addressDate) if addressDate else ''

    db = QtGui.qApp.db
    houseId = None
    if addressId:
        recAddress = db.getRecord('Address', 'house_id, flat', addressId)
        if recAddress:
            houseId = forceRef(recAddress.value('house_id'))
            result.flat = forceString(recAddress.value('flat'))
    if houseId:
        houseRecord = db.getRecord('AddressHouse LEFT JOIN kladr.STREET s ON s.CODE=AddressHouse.KLADRStreetCode ', 'AddressHouse.KLADRCode, AddressHouse.KLADRStreetCode, AddressHouse.number, AddressHouse.corpus, s.INDEX ', houseId)
        result.KLADRCode = forceString(houseRecord.value('KLADRCode'))
        result.KLADRStreetCode = forceString(houseRecord.value('KLADRStreetCode'))
        result.number = forceString(houseRecord.value('number'))
        result.index_ = forceString(houseRecord.value('INDEX'))
        result.corpus = forceString(houseRecord.value('corpus'))
        result.index = getHouseIndex(houseId, result.number+result.corpus)
    return result


def getInfisForKLADRCode(KLADRCode):
    if KLADRCode:
        return forceString(QtGui.qApp.db.translate('kladr.KLADR', 'CODE', KLADRCode, 'infis'))
    return ''


def getInfisForStreetKLADRCode(KLADRStreetCode):
    if KLADRStreetCode:
        return forceString(QtGui.qApp.db.translate('kladr.STREET', 'CODE', KLADRStreetCode, 'infis'))
    return ''


def getHouseIndex(houseId, number):
    if not houseId:
        return ''
    db = QtGui.qApp.db
    tableStreet = db.table('kladr.STREET')
    tableDoma = db.table('kladr.DOMA')
    tableHouse = db.table('AddressHouse')
    queryTable = tableStreet
    queryTable = queryTable.innerJoin(tableDoma, tableStreet['level5'].eq(tableDoma['level5']))
    queryTable = queryTable.innerJoin(tableHouse, tableHouse['KLADRStreetCode'].eq(tableStreet['CODE']))
    cond = [ tableStreet['actuality'].eq('00'),
             tableHouse['deleted'].eq(0),
             tableHouse['id'].eq(houseId),
             tableDoma['NAME'].contain(number)
           ]
    record = db.getRecordEx(queryTable, tableDoma['INDEX'], cond)
    if record:
        return forceString(record.value('INDEX'))
    return ''


def formatAddressInt(address, type=None):
    if address.KLADRCode:
        parts = []
        parts.append(getCityName(address.KLADRCode))
        if address.KLADRStreetCode:
            parts.append(getStreetName(address.KLADRStreetCode))
        if address.number:
            parts.append(u'д. '+address.number)
        if address.corpus:
            parts.append(u'к. '+address.corpus)
        if address.flat:
            parts.append(u'кв. '+address.flat)
        return ', '.join(parts)
    if address.freeInput and type in [None, 0]:     # в соответствии с задачей №8822 и №8950.
        return '[' + address.freeInput + ']'
    return ''


def formatAddress(addressId, freeInput = None):
    address = getAddress(addressId, freeInput)
    return formatAddressInt(address)


def findHouseId(address):
    # Необходимость обрезания number обусловлена тем, что если подать
    # слишком большую строку, то сравнение будет неудачно и на след. шаге будет
    # добавлена лишняя запись в AddressHouse.
    # Я не могу получать длины полей из БД. Сейчас (Qt 4.8.6) у меня метод
    # QSqlField.length() для MySQL VARCHAR(m) возвращает m*3.
    # Кто знает, что будет возвращаться в другой версии Qt или на другой платформе?
    truncate = lambda val, len: unicode(val)[:len] if val is not None else ''
    db = QtGui.qApp.db
    tableHouse = db.table('AddressHouse')
    filter = [tableHouse['KLADRCode'].eq(address['KLADRCode']),
              tableHouse['KLADRStreetCode'].eq(address['KLADRStreetCode']),
              tableHouse['number'].eq(truncate(address['number'], 8)),
              tableHouse['corpus'].eq(truncate(address['corpus'], 8)),
              tableHouse['deleted'].eq(0),
              ]
    houseIdList = db.getIdList(tableHouse, 'id', filter, 'id', 1)
    return houseIdList[0] if houseIdList else None


def getHouseId(address):
    houseId = findHouseId(address)
    if not houseId:
        db = QtGui.qApp.db
        tableHouse = db.table('AddressHouse')
        houseRecord = db.record('AddressHouse')
        houseRecord.setValue('KLADRCode',  toVariant(address['KLADRCode']))
        houseRecord.setValue('KLADRStreetCode',  toVariant(address['KLADRStreetCode']))
        houseRecord.setValue('number',  toVariant(address['number']))
        houseRecord.setValue('corpus',  toVariant(address['corpus']))
        houseId = db.insertRecord(tableHouse, houseRecord)
    return houseId


def findAddressIdEx(address):
    db = QtGui.qApp.db
    houseId = findHouseId(address)
    if houseId:
        tableAddress = db.table('Address')
        filter = [tableAddress['house_id'].eq(houseId),
                  tableAddress['flat'].eq(address.get('flat', None)),
                  tableAddress['deleted'].eq(0)]
        addressIdList = db.getIdList(tableAddress, 'id', filter)
        addressId = addressIdList[0] if addressIdList else None
        return houseId, addressId
    else:
        return None, None


def findAddressId(address):
    return findAddressIdEx(address)[1]


def getAddressId(address):
    houseId, addressId = findAddressIdEx(address)
    if not addressId:
        db = QtGui.qApp.db
        houseId = houseId if houseId else getHouseId(address)
        addressRecord = db.record('Address')
        addressRecord.setValue('house_id',  toVariant(houseId))
        addressRecord.setValue('flat',      toVariant(address.get('flat', None)))
        tableAddress = db.table('Address')
        addressId = db.insertRecord(tableAddress, addressRecord)
    return addressId


def getClientAddressKLADRCode(client_id, address_type):
    db = QtGui.qApp.db
    KLADRCode = ''
    tableCA = db.table('ClientAddress')
    tableA = db.table('Address')
    tableAH = db.table('AddressHouse')
    table = tableCA.leftJoin(tableA, tableA['id'].eq(tableCA['address_id']))
    table = table.leftJoin(tableAH, tableAH['id'].eq(tableA['house_id']))
    func = 'getClientRegAddressId({0})' if address_type == 0 else 'getClientLocAddressId({0})'
    cond = [tableCA['id'].eq(func.format(client_id))]
    record = db.getRecordEx(table, tableAH['KLADRCode'], where=cond)
    if record:
        KLADRCode = forceString(record.value('KLADRCode'))
    return KLADRCode


def getClientDocument(clientId):
    filter = '''Tmp.documentType_id IN (SELECT rbDocumentType.id FROM rbDocumentType LEFT JOIN rbDocumentTypeGroup ON rbDocumentTypeGroup.id=rbDocumentType.group_id WHERE rbDocumentTypeGroup.code = '1')'''
    return selectLatestRecord('ClientDocument', clientId, filter)


def formatDocument(documentTypeId, serial, number):
    db = QtGui.qApp.db
    result = u'%s %s %s' % (forceString(db.translate('rbDocumentType', 'id', documentTypeId, 'name')),
                            forceString(serial),
                            forceString(number)
                            )
    return result.strip()


def getClientPolicyEx(clientId, isCompulsory, date=None, eventId=None):
    db = QtGui.qApp.db
    if date:
        funcCall = 'getClientPolicyIdForDate(%d,%d,%s,%s)' % (clientId, 1 if isCompulsory else 0, db.formatDate(date), eventId if eventId else 'NULL')
    else:
        funcCall = 'getClientPolicyId(%d,%d)' % (clientId, 1 if isCompulsory else 0)

    stmt = 'SELECT ClientPolicy.*, Organisation.compulsoryServiceStop, Organisation.voluntaryServiceStop, Organisation.area, ' \
           " IF (ClientPolicy.policyKind_id = (SELECT id FROM rbPolicyKind WHERE rbPolicyKind.code = '3'), ClientPolicy.number, " \
           " (SELECT ci.identifier FROM ClientIdentification ci WHERE ci.client_id = ClientPolicy.client_id AND ci.deleted = 0 AND " \
           " ci.accountingSystem_id = (SELECT id FROM rbAccountingSystem rbas WHERE rbas.code = 'ENP') ) ) AS enp" \
           ' FROM ClientPolicy' \
           ' LEFT JOIN Organisation ON Organisation.id = ClientPolicy.insurer_id' \
           ' WHERE ClientPolicy.id = %s' % funcCall
    query = db.query(stmt)
    if query.next():
        return query.record()
    else:
        return None


def getClientCompulsoryPolicy(clientId, date=None, eventId=None):
    return getClientPolicyEx(clientId, True, date, eventId)


def getClientVoluntaryPolicy(clientId, date=None):
    return getClientPolicyEx(clientId, False, date)


getClientPolicy = getClientCompulsoryPolicy


def formatPolicy(insurerId, serial, number, begDate=None, endDate=None, name=None,  note=None, policyKindId=None):
    policyKindId = forceRef(policyKindId)
    result = (('[' + CPolicyKindCache.getCode(policyKindId) + ']') if policyKindId else '') + u': '
    result += forceString(serial) + ' ' + forceString(number)

    insurerId = forceRef(insurerId)
    nameParts = []
    if insurerId:
        nameParts.append(getOrganisationShortName(insurerId))
    name  = forceStringEx(name)
    if name:
        nameParts.append(name)
    note = forceStringEx(note)
    if note:
        nameParts.append('('+note+')')
    insurerName = ' '.join(nameParts)
    if insurerName:
        result = result + u' выдан ' + insurerName

    dateRange = ''
    if begDate and not begDate.isNull():
        dateRange = u'с ' + forceString(begDate)
    if endDate and not endDate.isNull():
        dateRange += u' по ' + forceString(endDate)
    if dateRange:
        result += u' действителен '+dateRange.strip()
    # вывод территории страхования
    area = forceString(QtGui.qApp.db.translate('Organisation', 'id', insurerId, 'area'))
    if area and hasattr(QtGui.qApp, 'provinceKLADR') and area != QtGui.qApp.provinceKLADR():
        areaName = forceString(QtGui.qApp.db.translate('kladr.infisAREA', 'KLADR', area, 'NAME'))
        if areaName:
            result += u' (' + areaName + u')'
    return result


def getClientWork(clientId):
    return selectLatestRecord('ClientWork', clientId)


def getCleintSocStatusType(clientId):
    return selectLatestRecord('ClientSocStatus', clientId)


# def getWorkRelationshipInfo(clientId):
#     db = QtGui.qApp.db
#     stmt = u'''SELECT *, rbSocStatusType.name as SSTName FROM Client
#                     LEFT JOIN ClientSocStatus ON ClientSocStatus.client_id = Client.id
#                     LEFT JOIN rbSocStatusType ON rbSocStatusType.id = ClientSocStatus.socStatusType_id
#                     LEFT JOIN ClientWork ON ClientWork.client_id = Client.id
#                     LEFT JOIN Organisation ON ClientWork.org_id = Organisation.id
#                 WHERE Client.id = \'%s\' ORDER BY ClientWork.modifyDatetime''' % (clientId)
#     query = db.query(stmt)
#     if query.next():
#         return query.record()
#     else:
#         return None


def getAttachRecord(clientId, temporary):
    clientAttach = selectLatestRecord(('ClientAttach', 'ClientAttach AS Tmp JOIN rbAttachType ON Tmp.attachType_id=rbAttachType.id'), clientId, 'rbAttachType.temporary %s \'0\'' % ('!=' if temporary else '='))
    if clientAttach:
        attachTypeId = forceRef(clientAttach.value('attachType_id'))
        attachType = QtGui.qApp.db.getRecord('rbAttachType', '*', attachTypeId)
        result = {
                  'attachTypeId'    : attachTypeId,
                  'LPU_id'          : forceRef(clientAttach.value('LPU_id')),
                  'orgStructure_id' : forceRef(clientAttach.value('orgStructure_id')),
                  'begDate'         : forceDate(clientAttach.value('begDate')),
                  'endDate'         : forceDate(clientAttach.value('endDate')),
                  'code'            : forceString(attachType.value('code')),
                  'name'            : forceString(attachType.value('name')),
                  'temporary'       : forceBool(attachType.value('temporary')),
                  'outcome'         : forceBool(attachType.value('outcome')),
                  'finance_id'      : forceRef(attachType.value('finance_id')),
                  'document_id'     : forceRef(clientAttach.value('document_id')),
                 }
        if result['outcome']:
            result['date'] = result['endDate']
        else:
            result['date'] = result['begDate']
        return result
    else:
        return None


def getClientAttachEx(clientId, isTemporary, date=None):
    db = QtGui.qApp.db
    if date and not QtGui.qApp.showingAttach(): # not QtGui.qApp.showingAttach() - считаю это не корректным
        funcCall = 'getClientAttachIdForDate(%d,%d,%s)' % (clientId, 1 if isTemporary else 0, db.formatDate(date))
    else:
        funcCall = 'getClientAttachId(%d,%d)' % (clientId, 1 if isTemporary else 0)

    stmt = 'SELECT ClientAttach.attachType_id, ClientAttach.id AS attachId,' \
           ' ClientAttach.LPU_id, ClientAttach.orgStructure_id,' \
           ' ClientAttach.begDate, ClientAttach.endDate,' \
           ' ClientAttach.document_id,' \
           ' rbAttachType.code, rbAttachType.name, rbAttachType.temporary,' \
           ' rbAttachType.outcome, rbAttachType.finance_id' \
           ' FROM ClientAttach' \
           ' LEFT JOIN rbAttachType ON rbAttachType.id=ClientAttach.attachType_id' \
           ' WHERE ClientAttach.id = %s' % funcCall
    query = db.query(stmt)
    if query.next():
        record = query.record()
        result = {
                  'attachTypeId'    : forceRef(record.value('attachType_id')),
                  'LPU_id'          : forceRef(record.value('LPU_id')),
                  'orgStructure_id' : forceRef(record.value('orgStructure_id')),
                  'begDate'         : forceDate(record.value('begDate')),
                  'endDate'         : forceDate(record.value('endDate')),
                  'code'            : forceString(record.value('code')),
                  'name'            : forceString(record.value('name')),
                  'temporary'       : forceBool(record.value('temporary')),
                  'outcome'         : forceBool(record.value('outcome')),
                  'finance_id'      : forceRef(record.value('finance_id')),
                  'document_id'     : forceRef(record.value('document_id')),
                  'attachId'        : forceRef(record.value('attachId')),
                 }
        result['date'] = result['endDate' if result['outcome'] else 'begDate']
        return result
    else:
        return None


def getClientAttaches(clientId, date=None):
    temporary = getClientAttachEx(clientId, True,  date)
    permanent = getClientAttachEx(clientId, False, date)
    result = []
    if temporary:
        result.append(temporary)
    if permanent:
        result.append(permanent)
    result.sort(key=lambda record: record['date'])
    return result


def getClientSocStatuses(clientId):
    db = QtGui.qApp.db
    table = db.table('ClientSocStatus')
    cond  = [table['client_id'].eq(clientId),
             table['deleted'].eq(0),
             db.joinOr([table['endDate'].isNull(), table['endDate'].ge(QDate.currentDate())])]
    return db.getIdList(table, idCol='socStatusType_id', where=cond, order='begDate')


def getClientSvoSocStatus(clientId):
    db = QtGui.qApp.db
    table = db.table('ClientSocStatus')
    cond  = [table['client_id'].eq(clientId),
             table['deleted'].eq(0),
             table['socStatusClass_id'].eq(forceInt(db.translate('rbSocStatusClass', 'code', 'svo', 'id'))),
             db.joinOr([table['endDate'].isNull(), table['endDate'].ge(QDate.currentDate())])]
    return db.getRecordEx(table, '*', where=cond, order='begDate')


def getClientSocStatusIds(clientId):
    db = QtGui.qApp.db
    table = db.table('ClientSocStatus')
    cond  = [table['client_id'].eq(clientId),
             table['deleted'].eq(0),
             db.joinOr([table['endDate'].isNull(), table['endDate'].ge(QDate.currentDate())])]
    return db.getIdList(table, idCol='id', where=cond, order='begDate')


def getClientPhones(clientId):
    db = QtGui.qApp.db
    table = db.table('ClientContact')
    cond  = []
    cond.append(table['client_id'].eq(clientId))
    cond.append(table['deleted'].eq(0))
    tableContactTypes = db.table('rbContactType')
    queryTable = table.leftJoin(tableContactTypes, tableContactTypes['id'].eq(table['contactType_id']))
    records = db.getRecordList(queryTable,
                               [tableContactTypes['name'], table['contact'], table['notes'], tableContactTypes['code']],
                               cond,
                               [u'ClientContact.id DESC', tableContactTypes['code'].name()])
    result = []
    for record in records:
        typeName = forceString(record.value(0))
        contact  = forceString(record.value(1))
        notes    = forceString(record.value(2))
        contactTypeCode = forceString(record.value(3))
        result.append((typeName, contact, notes, contactTypeCode))
    return result


def formatClientPhones(phones):
    return ', '.join([(phone[0]+': '+phone[1]+' ('+phone[2]+')') if phone[2] else (phone[0]+': '+phone[1]) for phone in phones])


def getClientPhonesEx(clientId):
    return formatClientPhones(getClientPhones(clientId))


def getClientPhone(clientId):
    """
    Возвращает последний внесённый номер телефона пациента в зависимости от принадлежности.
    :param clientId:
    :return Сначала мобильный, если нет, то домашний, либо ничего:
    """
    client_contact_list = getClientPhones(clientId)
    if any(map(lambda item: u'моб' in item[0], client_contact_list)):
        return filter(lambda item: u'моб' in item[0], getClientPhones(clientId))[0][1]
    elif any(map(lambda item: u'дом' in item[0], client_contact_list)):
        return filter(lambda item: u'дом' in item[0], getClientPhones(clientId))[0][1]
    else:
        return None


def getClientDocumentLocation(clientId):
    db = QtGui.qApp.db
    table = db.table('Client_DocumentTracking')
    cond  = []
    cond.append(table['client_id'].eq(clientId))
    cond.append(table['deleted'].eq(0))
    tableClientDocumentTrackingItem = db.table('Client_DocumentTrackingItem')
    tableRBDocumentTypeForTracking = db.table('rbDocumentTypeForTracking')
    tableRBDocumentTypeLocation = db.table('rbDocumentTypeLocation')
    queryTable = table.leftJoin(tableRBDocumentTypeForTracking, tableRBDocumentTypeForTracking['id'].eq(table['documentTypeForTracking_id']))
    queryTable = queryTable.leftJoin(tableClientDocumentTrackingItem, tableClientDocumentTrackingItem['master_id'].eq(table['id']))
    queryTable = queryTable.leftJoin(tableRBDocumentTypeLocation, tableRBDocumentTypeLocation['id'].eq(tableClientDocumentTrackingItem['documentLocation_id']))
    cond.append(tableRBDocumentTypeForTracking['showInClientInfo'].eq(1))
    record = db.getRecordEx(queryTable, [tableRBDocumentTypeForTracking['name'], tableRBDocumentTypeLocation['name'], tableRBDocumentTypeLocation['color'], tableClientDocumentTrackingItem['note'], table['documentNumber']], cond, 'concat_ws(\' \', Client_DocumentTrackingItem.documentLocationDate, Client_DocumentTrackingItem.documentLocationTime) DESC')
    result = []
    if record:
        documentNumber = forceString(record.value(4))
        documentTypeName = forceString(record.value(0))
        documentTypeName = u'{0} № {1}'.format(documentTypeName, documentNumber)
        documentLocationName  = forceString(record.value(1))
        color = forceString(record.value(2))
        note = forceString(record.value(3))
        result.extend((documentTypeName, documentLocationName, color, note))
    return result


def getActualClientQuoting(clientId):
    date = QDate.currentDate()
    return getClientQuoting(clientId, date)


def getClientQuoting(clientId, date):
    db = QtGui.qApp.db
    table = db.table('Client_Quoting')
    tableQuotaType = db.table('QuotaType')
    queryTable = table.innerJoin(tableQuotaType, tableQuotaType['id'].eq(table['quotaType_id']))
    cond = [table['master_id'].eq(clientId),
            table['deleted'].eq(0)]
    if date and date.isValid():
        cond.extend([table['dateRegistration'].dateLe(date),
                     db.joinOr([
                                table['dateEnd'].dateGe(date),
                                'DATE('+table['dateEnd'].name()+')='+'DATE(0000-00-00)'
                               ])
                     ])
    fields = [tableQuotaType['class'].name(),
              tableQuotaType['code'].name(),
              table['quotaTicket'].name(),
              table['status'].name()]
    recordList = db.getRecordList(queryTable, fields, cond)
    result = []
    for record in recordList:
        class_ = getQuotaTypeClassNameList()[forceInt(record.value('class'))]
        code   = forceString(record.value('code'))
        quotaTicket = forceString(record.value('quotaTicket'))
        status = [u'Отменено',
                  u'Ожидание',
                  u'Активный талон',
                  u'Талон для заполнения',
                  u'Заблокированный талон',
                  u'Отказано',
                  u'Необходимо согласовать дату обслуживания',
                  u'Дата обслуживания на согласовании',
                  u'Дата обслуживания согласована',
                  u'Пролечен',
                  u'Обслуживание отложено',
                  u'Отказ пациента',
                  u'Импортировано из ВТМП'][forceInt(record.value('status'))]
        result.append((class_, code, quotaTicket, status))
    return result


def getClientResearchIds(clientId):
    db = QtGui.qApp.db
    table = db.table('ClientResearch')
    cond  = [ table['client_id'].eq(clientId),
              table['deleted'].eq(0) ]
    return db.getIdList(table, idCol='id', where=cond, order='begDate')


def getClientActiveDispensaryIds(clientId):
    db = QtGui.qApp.db
    table = db.table('ClientActiveDispensary')
    cond  = [ table['client_id'].eq(clientId),
              table['deleted'].eq(0) ]
    return db.getIdList(table, idCol='id', where=cond, order='begDate')


def getClientDangerousIds(clientId):
    db = QtGui.qApp.db
    table = db.table('ClientDangerous')
    cond  = [ table['client_id'].eq(clientId),
              table['deleted'].eq(0) ]
    return db.getIdList(table, idCol='id', where=cond, order='date')


def getClientForcedTreatmentIds(clientId):
    db = QtGui.qApp.db
    table = db.table('ClientForcedTreatment')
    cond  = [ table['client_id'].eq(clientId),
              table['deleted'].eq(0) ]
    return db.getIdList(table, idCol='id', where=cond, order='begDate')


def getClientSuicideIds(clientId):
    db = QtGui.qApp.db
    table = db.table('ClientSuicide')
    cond  = [ table['client_id'].eq(clientId),
              table['deleted'].eq(0) ]
    return db.getIdList(table, idCol='id', where=cond, order='date')


def getClientContingentKindIds(clientId):
    db = QtGui.qApp.db
    table = db.table('ClientContingentKind')
    cond  = [ table['client_id'].eq(clientId),
              table['deleted'].eq(0) ]
    return db.getIdList(table, idCol='id', where=cond, order='begDate')


def formatClientQuoting(clientQuotingList):
    result = []
    for clientQuoting in clientQuotingList:
        values = {'class'       : clientQuoting[0],
                  'code'        : clientQuoting[1],
                  'quotaTicket' : clientQuoting[2],
                  'status'      : clientQuoting[3]}
        result.append(u'класс-%(class)s, код-%(code)s, талон-%(quotaTicket)s, состояние-%(status)s'% values)
    return u' | '.join(result)


def getrbClientWorkPost_name(code):
    db = QtGui.qApp.db

    query = db.query('SELECT name FROM rbClientWorkPost WHERE id = {0}'.format(code))
    if query.next():
        record = query.record()
        result = forceString(record.value('name'))
        return result
    else:
        return None


def formatWork(workRecord):
    orgId = forceRef(workRecord.value('org_id'))
    if orgId:
        orgShortName = getOrganisationShortName(orgId)
    else:
        orgShortName = forceString(workRecord.value('freeInput'))
    post = forceString(workRecord.value('post'))
    post_id = forceString(workRecord.value('post_id'))
    if post_id != 0:
        rbClientWorkPost_name = getrbClientWorkPost_name(post_id)
        if rbClientWorkPost_name != None:
            post = rbClientWorkPost_name

    OKVED = forceString(workRecord.value('OKVED'))
    result = []
    if orgShortName:
        result.append(orgShortName)
    if post:
        result.append(post)
    if OKVED:
        result.append(u'ОКВЭД: '+OKVED)
    return trim(', '.join(result))


def formatWorkPlace(workRecord):
    orgId = forceRef(workRecord.value('org_id'))
    if orgId:
        return getOrganisationShortName(orgId)
    else:
        return forceString(workRecord.value('freeInput'))


def workRecordIsNotEmpty(workRecord):
    return forceRef(workRecord.value('org_id')) or bool(forceString(workRecord.value('freeInput')))


def workRecordDescribesStudent(workRecord):
    post = forceString(workRecord.value('post')).lower()
    return post.startswith(u'учащ') or post.startswith(u'студ')


def clientIsWorking(clientId):
    workRecord = getClientWork(clientId)
    return workRecordIsNotEmpty(workRecord) if workRecord else False


def clientIsStudent(clientId):
    workRecord = getClientWork(clientId)
    return workRecordDescribesStudent(workRecord) if workRecord else False


def getSocStatusTypeClasses(id):
    db = QtGui.qApp.db
    table = db.table('rbSocStatusClassTypeAssoc')
    cond  = table['type_id'].eq(id)
    return db.getIdList(table, idCol='class_id', where=cond, order='class_id')


def formatClientIdentification(clientIdentification):
    return '. '.join(['%s: <B>%s</B>' % (key,  val[0]) for key,  val in clientIdentification.items()])


def getClientObservationStatus(clientId):
    if clientId:
        db = QtGui.qApp.db
        table = db.table('Client_StatusObservation')
        rbTable = db.table('rbStatusObservationClientType')
        record = db.getRecordEx(table.leftJoin(rbTable, table['statusObservationType_id'].eq(rbTable['id'])), [rbTable['code'], rbTable['name'], rbTable['color']], [table['deleted'].eq(0), table['master_id'].eq(clientId)], 'Client_StatusObservation.createDatetime DESC')
        if record:
            # code = forceString(record.value('code')) + '-' + forceString(record.value('name'))
            code = forceString(record.value('name'))
            color = forceString(record.value('color'))
            if code:
                return [code, color]
    return None

def getDispensarySpecialties(clientId):
    if clientId:
        date = QDate.currentDate()
        db = QtGui.qApp.db
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnostic = db.table('Diagnostic')
        tableDispNabMKB = db.table('soc_DispNabMKB')
        tableRBDispanser = db.table('rbDispanser')
        tablePerson = db.table('Person')
        tableRBSpeciality = db.table('rbSpeciality')
        cond = [tableDiagnosis['client_id'].eq(clientId),
                tableDiagnosis['deleted'].eq(0),
                tableDiagnostic['deleted'].eq(0),
                db.joinOr([db.joinAnd([tableDiagnostic['endDate'].isNotNull(), tableDiagnostic['endDate'].le(date)]),
                            db.joinAnd([tableDiagnostic['endDate'].isNull(), tableDiagnostic['setDate'].le(date)])]),
                tableRBDispanser['observed'].eq(1)
                ]
        queryTable = tableDiagnosis.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
        queryTable = queryTable.innerJoin(tableDispNabMKB, tableDispNabMKB['code'].eq(tableDiagnosis['MKB']))
        queryTable = queryTable.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
        queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnosis['dispanserPerson_id']))
        queryTable = queryTable.leftJoin(tableRBSpeciality, tableRBSpeciality['id'].eq(tablePerson['speciality_id']))
        cond.append(u'''NOT EXISTS(SELECT DC.id
                                FROM Diagnostic AS DC
                                INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                WHERE DC.diagnosis_id = Diagnosis.id AND DC.endDate <= {} AND DC.deleted = 0 AND rbDP.name LIKE '{}')
                        OR EXISTS(SELECT DC.id
                                FROM Diagnostic AS DC
                                INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                WHERE DC.diagnosis_id = Diagnosis.id AND DC.endDate <= {} AND DC.deleted = 0 AND rbDP.name LIKE '{}')''' .format(db.formatDate(date), 
                                                                                                                                                 u'%снят%', 
                                                                                                                                                 db.formatDate(date), 
                                                                                                                                                 u'%взят повторно%'))
        records = db.getRecordListGroupBy(queryTable, [u'rbSpeciality.name'], where=cond, group = u'rbSpeciality.name', order='Diagnostic.endDate DESC')
        specialties = []
        for record in records:
            specialty = forceString(record.value('name'))
            if specialty:
                specialties.append(specialty)
        return u', '.join(specialty for specialty in specialties)
    return None
        


def getVaccineInfectionIdList(vaccineId):
    db = QtGui.qApp.db
    table = db.table('rbInfection_rbVaccine')
    return db.getDistinctIdList(table, 'infection_id', where=table['vaccine_id'].eq(vaccineId))


def getClientVaccinationIdList(clientId):
    db = QtGui.qApp.db
    table = db.table('ClientVaccination')
    return db.getIdList(table, where=[table['client_id'].eq(clientId), table['deleted'].eq(0)])
    
    
def getClientVaccinationProbeIdList(clientId):
    db = QtGui.qApp.db
    table = db.table('ClientVaccinationProbe')
    return db.getIdList(table, where=[table['client_id'].eq(clientId), table['deleted'].eq(0)])


def getClientMedicalExemptionIdList(clientId):
    db = QtGui.qApp.db
    table = db.table('ClientMedicalExemption')
    return db.getIdList(table, where=[table['client_id'].eq(clientId), table['deleted'].eq(0)])


def getClientConsentsEx(clientId, date):
    result = {}
    maxList = {}
    clientConsentRecordList = getClientConsents(clientId, date)
    for clientConsentRecord in clientConsentRecordList:
        consentTypeCode = forceString(clientConsentRecord.value('consentTypeCode'))
        clientConsentDate = forceDate(clientConsentRecord.value('date'))
        currMax = maxList.get(consentTypeCode, QDate())
        if clientConsentDate > currMax:
            maxList[consentTypeCode] = clientConsentDate
            result[consentTypeCode] = clientConsentRecord
    return result.values()


def getClientConsents(clientId, dateConsent):
    if clientId:
        db = QtGui.qApp.db
        tableCC = db.table('ClientConsent')
        tableCCT = db.table('rbClientConsentType')
        queryTable = tableCC.leftJoin(tableCCT, tableCCT['id'].eq(tableCC['clientConsentType_id']))
        cond = [tableCC['client_id'].eq(clientId), tableCC['deleted'].eq(0), tableCCT['inClientInfoBrowser'].eq(1)]
        if dateConsent:
            cond.append(tableCC['date'].dateLe(dateConsent))
            cond.append(db.joinOr([tableCC['endDate'].dateGe(dateConsent), tableCC['endDate'].isNull()]))
        fields = [tableCCT['code'].alias('consentTypeCode'),
                  tableCCT['name'].alias('consentTypeName'),
                  tableCC['value'].name(),
                  tableCC['endDate'].name(),
                  tableCC['date'].name(),
                  tableCC['modifyPerson_id'],
                  tableCC['createPerson_id'],
                  tableCC['id'].alias('clientConsentId'),
                  tableCC['representerClient_id'].alias('representerClientId')]
        return db.getRecordList(queryTable, fields, cond)
    return []


def formatClientConsents(clientConsentRecordList):
    result = []
    currentDate = QDate.currentDate()
    for clientConsentRecord in clientConsentRecordList:
        code = forceString(clientConsentRecord.value('consentTypeCode'))
        # name = forceString(clientConsentRecord.value('consentTypeName'))
        value = forceInt(clientConsentRecord.value('value'))
        endDate = forceDate(clientConsentRecord.value('endDate'))
        dateConsent = forceString(clientConsentRecord.value('date'))
        value = u'Да' if value else u'Нет'
        if not endDate or (endDate and endDate >= currentDate):
            result.append(u'%s - <B><font color=green>%s</font></B>(%s)' % (code, value, dateConsent))
        else:
            result.append(u'%s - <B><font color=red>%s</font></B>(%s)' % (code, value, dateConsent))
    return ' | '.join(result)


def getClientContingentTypeId(clientId):
    # Пол, Возраст и соц.статус имеют приоритет перед событиями и МЭС
    result = None
    query = QtGui.qApp.db.query('SELECT getClientContingentTypeIdCK(%d)'%clientId)
    if query.next():
        result = forceRef(query.value(0))
    return result
    
    
def getClientContingentTypeIdList(clientId):
    # Пол, Возраст и соц.статус имеют приоритет перед событиями и МЭС
    db = QtGui.qApp.db
    tableRbContingentType = db.table('rbContingentType')
    result = db.getIdList(tableRbContingentType, where='isClientContingentTypeIdCK(%d, rbContingentType.id) > 0 AND priority > 0' % clientId, order='priority desc')
    return result


def getContingentHasEventTypeCond(contingentTypeId):
    return forceBool(QtGui.qApp.db.translate('rbContingentType_EventType', 'master_id', contingentTypeId, 'id'))


def formatClientContingentEventType(clientId, contingentTypeId):
    contingentHasEventTypeCond = getContingentHasEventTypeCond(contingentTypeId)
    if contingentHasEventTypeCond:
        query = QtGui.qApp.db.query('SELECT checkClientContingentTypeETM(%d, %d)' % (clientId, contingentTypeId))
        if query.next():
            eventTypeCondValue = forceInt(query.value(0))
        else:
            eventTypeCondValue = 0
    else:
        eventTypeCondValue = 0
    return eventTypeCondValue, contingentHasEventTypeCond


def getContingentHasActionTypeCond(contingentTypeId):
    return forceBool(QtGui.qApp.db.translate('rbContingentType_ActionType', 'master_id', contingentTypeId, 'id'))


def formatClientContingentActionType(clientId, contingentTypeId):
    contingentHasActionTypeCond = getContingentHasActionTypeCond(contingentTypeId)
    if contingentHasActionTypeCond:
        query = QtGui.qApp.db.query('SELECT checkClientContingentTypeEAT(%d, %d)' % (clientId, contingentTypeId))
        if query.next():
            actionTypeCondValue = forceInt(query.value(0))
        else:
            actionTypeCondValue = 0
    else:
        actionTypeCondValue = 0
    return actionTypeCondValue, contingentHasActionTypeCond


def formatClientContingentType(clientId, contingentTypeId):
    from RefBooks.ContingentType.List import CContingentTypeTranslator
    if not contingentTypeId:
        return u' ', u''
    db = QtGui.qApp.db
    eventTypeCondValue, contingentHasEventTypeCond = formatClientContingentEventType(clientId, contingentTypeId)
    actionTypeCondValue, contingentHasActionTypeCond = formatClientContingentActionType(clientId, contingentTypeId)
    eventOrActionOperation = forceInt(db.translate(CContingentTypeTranslator.CTTName,
                                                   'id',
                                                   contingentTypeId,
                                                   'eventOrActionOperation'))
    typeCondValue = 0
    contingentHasTypeCond = False
    eventOrActionOperationOR = (not CContingentTypeTranslator.isEventTypeActionTypeEnabled(eventOrActionOperation) or CContingentTypeTranslator.isEventTypeActionTypeOperationType_OR(eventOrActionOperation))
    if contingentHasEventTypeCond and contingentHasActionTypeCond:
        if eventOrActionOperationOR:
            if not eventTypeCondValue:
                typeCondValue = actionTypeCondValue
                contingentHasTypeCond = contingentHasActionTypeCond
            elif eventTypeCondValue >= actionTypeCondValue:
                typeCondValue = eventTypeCondValue
                contingentHasTypeCond = contingentHasEventTypeCond
            elif eventTypeCondValue < actionTypeCondValue:
                typeCondValue = actionTypeCondValue
                contingentHasTypeCond = contingentHasActionTypeCond
        else:
            if not actionTypeCondValue:
                typeCondValue = actionTypeCondValue
                contingentHasTypeCond = contingentHasActionTypeCond
            else:
                typeCondValue = eventTypeCondValue
                contingentHasTypeCond = contingentHasEventTypeCond
    elif contingentHasEventTypeCond:
        typeCondValue = eventTypeCondValue
        contingentHasTypeCond = contingentHasEventTypeCond
    elif contingentHasActionTypeCond:
        typeCondValue = actionTypeCondValue
        contingentHasTypeCond = contingentHasActionTypeCond
#    синий - попадает в контингент в котором нет требований для Событий
#    красный - попадает в контингент и не имеет требуемых Событий
#    желтый - попадает в контингент, имеет Открытое Событие
#    зеленый - попадает в контингент, имеет Закрытое Событие
    color = {0: u'#0000CD', 1: u'#FF0000', 2: u'#CC9900', 3: u'#00FF00'}.get(typeCondValue+contingentHasTypeCond, u'#000000')
    contingentTypeCode = forceString(QtGui.qApp.db.translate('rbContingentType', 'id', contingentTypeId, 'code'))
    return contingentTypeCode, color

def getClientResearch(clientId):
    result = {}
    stmt = """
    SELECT rk.code, cr.begDate, cr.endDate
    FROM ClientResearch cr
        LEFT JOIN rbClientResearchKind rk ON rk.id = cr.researchKind_id
    WHERE cr.deleted = 0 AND cr.client_id = %s
        AND rk.inClientInfoBrowser = 1
        AND cr.begDate = (
            SELECT max(begDate)
            FROM ClientResearch cr1
            WHERE cr1.client_id = cr.client_id
                AND cr1.researchKind_id = cr.researchKind_id
        )
    """ % clientId
    db = QtGui.qApp.db
    query = db.query(stmt)
    result = []
    while query.next():
        result.append(query.record())
    return result

def getClientAllergy(clientId): #tt1304
    db = QtGui.qApp.db
    table = db.table('ClientAllergy')
    cond  = [table['client_id'].eq(clientId),
              table['deleted'].eq(0) ]
    records = db.getRecordList(table, [table['nameSubstance'], table['power'], table['createDate'], table['notes']], cond)
    result = []
    dataPower = [u'0 - не известно', u'1 - малая', u'2 - средняя', u'3 - высокая', u'4 - строгая']
    for record in records:
        nameSubstance = forceString(record.value(0))
        power         = dataPower[forceInt(record.value(1))]
        createDate    = forceString(forceDate(record.value(2)))
        notes         = forceString(record.value(3))
        string        = (u'%s, %s' % (nameSubstance, power))
        string        += u', дата установления: %s' %createDate if createDate else ''
        string        += u', (%s)' %notes if notes else ''
        result.append(string)
    return u'; '.join(result)

def getClientIntoleranceMedicament(clientId): #tt1304
    db = QtGui.qApp.db
    tableIntoleranceMedicament = db.table('ClientIntoleranceMedicament')
    tableActiveSubstance = db.table('rbNomenclatureActiveSubstance')
    table = tableIntoleranceMedicament.leftJoin(tableActiveSubstance, tableActiveSubstance['id'].eq(tableIntoleranceMedicament['activeSubstance_id']))
    cond = [tableIntoleranceMedicament['client_id'].eq(clientId),
            tableIntoleranceMedicament['deleted'].eq(0)]
    records = db.getRecordList(table, [tableActiveSubstance['name'], tableIntoleranceMedicament['power'], tableIntoleranceMedicament['createDate'], tableIntoleranceMedicament['notes']], cond)
    result = []
    dataPower = [u'0 - не известно', u'1 - малая', u'2 - средняя', u'3 - высокая', u'4 - строгая']
    for record in records:
        nameSubstance = forceString(record.value(0))
        power         = dataPower[forceInt(record.value(1))]
        createDate    = forceString(forceDate(record.value(2)))
        notes         = forceString(record.value(3))
        string        = (u'%s, %s' % (nameSubstance, power))
        string        += u', дата установления: %s' % createDate if createDate else ''
        string        += u', (%s)' % notes if notes else ''
        result.append(string)
    return u'; '.join(result)

def formatClientResearch(recordList):
    strings = []
    for record in recordList:
        code = forceString(record.value('code'))
        begDate = forceDate(record.value('begDate'))
        endDate = forceDate(record.value('endDate'))
        string = (u'%s-%s' % (code, forceString(begDate)))
        if endDate.isValid():
            string += (u' годен до %s' % forceString(endDate))
        strings.append(string)
    return u'; '.join(strings)

def checkClientAttachService(personInfo):
    def formatISODateTime(isoString, format):
        return QDateTime.fromString(isoString, Qt.ISODate).toString(format)

        # Синхронизация данных о пациенте с фондом
    def update_soc_attach(clientId, attachment):
        # !!!!!!!!!!!!!!!!!!!!!!!!!ПРОВЕРКА ВЫСТАВЛЕНИЯ ГЛОБАЛЬНОЙ НАСТРОЙКИ
        if QtGui.qApp.checkGlobalPreference('23:SynchronizeAttachment', u'да'):
            try:
                db = QtGui.qApp.db
                table = db.table('soc_attachments')
                cond = u'soc_attachments.enp = {0} and soc_attachments.serviceMethod in (0,5)'.format(
                    attachment['person']['enp'])
                record = db.getRecordEx(table, '*', cond)
                if record:
                    record.setValue('client_id', toVariant(clientId))
                    record.setValue('attach_area', toVariant(
                        attachment['info'][0]['area'] if attachment['info'][0].get('area') else None))
                    record.setValue('serviceMethod', toVariant(0))
                else:
                    record = table.newRecord()
                    record.setValue('lastName', toVariant(attachment['person']['lastName']))
                    record.setValue('firstName', toVariant(attachment['person']['firstName']))
                    record.setValue('patrName', toVariant(attachment['person']['patrName']))
                    record.setValue('birthDate', toVariant(attachment['person']['birthDate']))
                    record.setValue('sex', toVariant(attachment['person']['sex']))
                    record.setValue('enp', toVariant(attachment['person']['enp']))
                    record.setValue('attach_mo', toVariant(attachment['mo']))
                    record.setValue('attach_area', toVariant(
                        attachment['info'][0]['area'] if attachment['info'][0].get('area') else None))
                    record.setValue('serviceMethod', toVariant(0))
                    record.setValue('client_id', toVariant(clientId))
                db.insertOrUpdate(table, record)
            except Exception as e:
                print 'error update_soc_attach'
    try:
        result = AttachService.searchClientAttach(personInfo, timeout=10)
        if result.get('attachlist') is None:
            QtGui.QMessageBox.information(None, u'Результат поиска', u'Пациент не найден', QtGui.QMessageBox.Ok,
                                          QtGui.QMessageBox.Ok)
        else:
            for attachment in result['attachlist']:
                db = QtGui.qApp.db
                stmt = """select shortName from Organisation
                            where Organisation.infisCode='%s' AND isMedical = 3 AND isInsurer = 0 AND isActive = 1 AND deleted = 0""" % attachment['mo']
                query = db.query(stmt)
                moName = ''
                while query.next():
                    moName = forceString(query.record().value('shortName'))
                    break
                codeMO = (u'Наименование ЛПУ: %s %s' % (attachment['mo'], moName)) if attachment.get('mo') else None
                person = attachment['person']
                name = ' '.join(s for s in [person['lastName'], person['firstName'], person['patrName']] if s)
                birthDate = u'Дата рождения: %s' % formatISODateTime(person['birthDate'], 'dd.MM.yyyy')
                sex = (u'пол: %s' % person['sex']) if person.get('sex') else None
                enp = (u'ЕНП: %s' % person['enp']) if person.get('enp') else None
                personText = u'Пациент: %s; \nСведения о прикреплении:' % ', \n'.join(
                    [s for s in [name, sex, birthDate, enp, codeMO] if s])

                if not codeMO or not attachment.get('info'):
                    attachText = u'- нет прикрепления'
                    attachesSnils = ''
                else:
                    if 'clientId' in personInfo:
                        update_soc_attach(personInfo['clientId'], attachment)
                    attachTextList = []
                    attachDate = (u'Дата прикрепления: %s' % formatISODateTime(attachment['info'][0]['date'],
                                                                               'dd.MM.yyyy')) if attachment['info'][
                        0].get('date') else None
                    attachArea = (u'Участок: %s' % attachment['info'][0]['area']) if attachment['info'][0].get(
                        'area') else None
                    attachType = {1: u'первичное', 2: u'по заявлению'}.get(attachment['info'][0]['type'])
                    attachType = (u'Тип прикрепления: %s' % attachType) if attachType else None
                    attachText = ', \n'.join(
                        [s for s in [attachType, attachArea, attachDate] if s]) or u'нет сведений'
                    for attachInfo in attachment['info']:
                        attachDocSnils = (u'СНИЛС мед. работника: %s' % attachInfo['docSnils']) if attachInfo.get(
                            'docSnils') else u'нет сведений'
                        attachTextList.append(u'%s' % attachDocSnils)
                    attachesSnils = '\n'.join(attachTextList)
                message = u'%s\n%s\n%s' % (personText, attachText, attachesSnils)

                msgbox = QtGui.QMessageBox()
                msgbox.setWindowFlags(msgbox.windowFlags() | Qt.WindowStaysOnTopHint)
                msgbox.setWindowTitle(u'Результат поиска')
                msgbox.setText(message)
                msgbox.addButton(QtGui.QMessageBox.Ok)
                msgbox.setDefaultButton(QtGui.QMessageBox.Ok)
                msgbox.exec_()
    except Exception, e:
        QtGui.QMessageBox.critical(None, u'Ошибка', unicode(e), QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)

def getAttachmentPersonInfo(clientId):
    db = QtGui.qApp.db
    table = db.table('Client')
    record = db.getRecord(table, '*', clientId)
    personInfo = {}
    personInfo['clientId'] = clientId
    personInfo['lastName'] = forceString(record.value('lastName'))
    personInfo['firstName'] = forceString(record.value('firstName'))
    personInfo['patrName'] = forceString(record.value('patrName'))
    personInfo['sex'] = formatSex(forceInt(record.value('sex')))
    personInfo['birthDate'] = forceString(forceDate(record.value('birthDate')).toString('yyyy-MM-dd'))
    snils = forceString(record.value('SNILS'))
    if snils:
        personInfo['snils'] = formatSNILS(snils)

    documentRecord = getClientDocument(clientId)
    if documentRecord:
        docTypeId = forceRef(documentRecord.value('documentType_id'))
        docNumber = forceString(documentRecord.value('number'))
        docSerial = forceString(documentRecord.value('serial'))
        if docTypeId and docNumber:
            documentTypeDescr = getDocumentTypeDescr(docTypeId)
            if documentTypeDescr.regionalCode:
                personInfo['docTypeId'] = forceInt(documentTypeDescr.regionalCode)
                personInfo['docSerial'] = docSerial
                personInfo['docNumber'] = docNumber

    policyRecord = getClientCompulsoryPolicy(clientId)
    if policyRecord:
        policyKind = forceRef(policyRecord.value('policyKind_id'))
        policyNumber = forceString(policyRecord.value('number'))
        policySerial = forceString(policyRecord.value('serial'))
        insurerId = forceRef(policyRecord.value('insurer_id'))
        if policyKind and policyNumber:
            policyTypeRegionalCode = forceString(db.translate('rbPolicyKind', 'id', policyKind, 'regionalCode'))
            if policyTypeRegionalCode:
                personInfo['policyType'] = forceInt(policyTypeRegionalCode)
                personInfo['policySerial'] = policySerial
                personInfo['policyNumber'] = policyNumber
                if policyTypeRegionalCode == '3':
                    personInfo['enp'] = policyNumber
            infisCode = forceString(db.translate('Organisation', 'id', insurerId, 'infisCode'))
            if infisCode:
                personInfo['smoCode'] = infisCode
            OKATO = forceString(db.translate('Organisation', 'id', insurerId, 'OKATO'))
            if OKATO:
                personInfo['terrCode'] = OKATO

    return personInfo


def getClientEpidCases(clientId):
    db = QtGui.qApp.db
    table = db.table('Client_EpidCase')
    tablePerson = db.table('Person')
    tableOrganisation = db.table('Organisation')
    table = table.innerJoin(tablePerson, tablePerson['id'].eq(table['regPerson_id']))
    table = table.innerJoin(tableOrganisation, tableOrganisation['id'].eq(table['org_id']))
    cond  = [table['master_id'].eq(clientId)]
    return db.getRecordList(table, where=cond, order='regDate')


def selectAppropriateEpidCase(clientInfo, takenTissueJournalId):
    actualEpidCase = None
    db = QtGui.qApp.db
    epidCaseRecords = getClientEpidCases(clientInfo.id)
    epidCases = []
    for epidCaseRecord in epidCaseRecords:
        mkbCode = forceString(epidCaseRecord.value('MKB'))
        epidNumber = forceString(epidCaseRecord.value('number'))
        regDate = forceString(epidCaseRecord.value('regDate'))
        endDate = forceString(epidCaseRecord.value('endDate'))
        regOrgId = forceRef(epidCaseRecord.value('Org_id'))
        epidCases.append({'mkbCode': mkbCode, 'epidNumber': epidNumber, 'regDate': regDate, 'endDate': endDate, 'regOrgId': regOrgId})

    appropriateEpidCases = []
    for epidCase in epidCases:
        if not epidCase['endDate']:
            appropriateEpidCases.append(epidCase)
        else:
            continue
    if not appropriateEpidCases:
        appropriateEpidCases = epidCases

    if appropriateEpidCases:
        takenDateTime = forceString(db.translate('TakenTissueJournal', 'id', takenTissueJournalId, 'datetimeTaken'))
        takenDateTime = datetime.strptime(takenDateTime, "%d.%m.%Y %H:%M")
        td = timedelta.max
        for ec in appropriateEpidCases:
            # Если нет даты регистрации эпид. номера(любого) мы не можем вычислить эпид. номер, подходящий для передачи, поэтому не передаем эпид. номер
            if not ec['regDate']:
                return None
            ecDatetime = datetime.strptime(ec['regDate'], "%d.%m.%Y")
            if ecDatetime > takenDateTime:
                continue
            currTd = takenDateTime - ecDatetime
            currTdSeconds = (currTd.microseconds + (currTd.seconds + currTd.days * 24 * 3600) * 10**6) / 10.0**6
            tdSeconds = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10.0**6
            if 0 < currTdSeconds < tdSeconds:
                actualEpidCase = ec
                td = currTd
    return actualEpidCase

# consents - Для отображения result.consents, тт 2625,
# для события в consents передается словарь с begDate и endDate, чтобы отображать согласие, которое попадает в
# даты события. По умолчанию, отображает те согласия, у которых нет даты окончания согласия и если она есть то
# должна быть больше чем сегодняшний день
def getClientInfo(clientId, hasRegAddress=True, hasLocAddress=True, date=None, dateAttaches=None, consents=None, eventId=None):
    db = QtGui.qApp.db
    table  = db.table('Client')
    record = db.getRecord(table, '*', clientId)
    result = smartDict()
    result.id          = forceRef(clientId)
    result.lastName    = forceString(record.value('lastName'))
    result.firstName   = forceString(record.value('firstName'))
    result.patrName    = forceString(record.value('patrName'))
    result.sexCode     = forceInt(record.value('sex'))
    result.birthDate   = forceDate(record.value('birthDate'))
    result.birthTime   = forceTime(record.value('birthTime'))
    result.birthWeight = forceRef(record.value('birthWeight'))
    result.birthNumber = forceInt(record.value('birthNumber'))
    result.deathDate   = forceDateTime(record.value('deathDate'))
    result.birthPlace  = forceString(record.value('birthPlace'))
    result.SNILS       = forceString(record.value('SNILS'))
    result.notes       = forceString(record.value('notes'))
    result.attaches    = getClientAttaches(clientId, dateAttaches)
    result.socStatuses = getClientSocStatuses(clientId)
    result.quoting     = getActualClientQuoting(clientId)
    result.identification = formatClientIdentification(getClientIdentifications(clientId))
    result.clientDocumentLocation = getClientDocumentLocation(clientId)
    result.clientObservationStatus = getClientObservationStatus(clientId)
    result.dispensarySpecialties = getDispensarySpecialties(clientId)
    result.clientConsents = getClientConsentsEx(clientId, date)
    temp_list_consents = []
    for item in result.clientConsents:
        if not (item.value('endDate').toDate()) and item.value('endDate').toString() == u'': # нет даты окончания согласия
            if not consents:
                temp_list_consents.append(item)
                continue
            else:
                if consents['endDate']: # дата окончания события
                    if (item.value('date').toDate() >= consents['begDate'] \
                    and item.value('date').toDate() <= consents['endDate']) or \
                        (item.value('date').toDate() <= consents['begDate'] and \
                         item.value('date').toDate() <= consents['endDate']):
                        temp_list_consents.append(item)
                        continue
                else:
                    if item.value('date').toDate() >= consents['begDate']: # как будто бы такого случая вообще не будет, но это не точно
                        temp_list_consents.append(item)
                        continue
        else: # есть дата окончания согласия
            if not consents:
                if item.value('endDate').toDate() >= QDate.currentDate():
                    temp_list_consents.append(item)
                    continue
            else:
                if consents['endDate']: # дата окончания события
                    if ((item.value('endDate').toDate() >= consents['begDate']      \
                    and item.value('endDate').toDate() <= consents['endDate'])      \
                    or (item.value('endDate').toDate() >= consents['begDate']          \
                     and item.value('date').toDate() <= consents['begDate'])     \
                    ) or \
                    ((item.value('date').toDate() >= consents['begDate'] \
                    and item.value('date').toDate() <= consents['endDate'])
                    or (item.value('date').toDate() >= consents['endDate'] \
                    and item.value('endDate').toDate() <= consents['endDate'])
                    ) or \
                    (item.value('date').toDate() <= consents['begDate'] \
                    and  item.value('endDate').toDate() >= consents['endDate']):
                        temp_list_consents.append(item)
                        continue
                else:
                    if not (item.value('endDate').toDate() < consents['begDate']):
                        temp_list_consents.append(item)
                        continue

    result.clientConsents = temp_list_consents if len(temp_list_consents)>0 else []
    result.clientContingentTypeId = getClientContingentTypeId(clientId)
    result.contacts = getClientPhones(clientId)
    result.clientContingentTypeIdList = getClientContingentTypeIdList(clientId)
    result.epidCase = None
    result.workRelationship = {}

    documentRecord = getClientDocument(clientId)
    result.documentRecord = documentRecord
    if documentRecord:
        result.document = formatDocument(documentRecord.value('documentType_id'),
                                         documentRecord.value('serial'),
                                         documentRecord.value('number'))
#    else:
#        result.document = None

    policyRecord = getClientCompulsoryPolicy(clientId, date, eventId)
    result.compulsoryPolicyRecord = policyRecord
    result.compulsoryPolicy = u''
    result.voluntaryPolicy = u''
    colorOMC = u'green'
    colorDMC = u'blue'
    currentDate = forceDate(date) if date else QDate.currentDate()
    if policyRecord:
        result.policy = formatPolicy(policyRecord.value('insurer_id'),
                                     policyRecord.value('serial'),
                                     policyRecord.value('number'),
                                     policyRecord.value('begDate'),
                                     policyRecord.value('endDate'),
                                     policyRecord.value('name'),
                                     policyRecord.value('note'),
                                     policyRecord.value('policyKind_id')
                                     )
        compulsoryPolicyServiceOMC = forceBool(policyRecord.value('compulsoryServiceStop'))
        colorOMC = u'green' if not compulsoryPolicyServiceOMC else u'red'
        endDateOMC = forceDate(policyRecord.value('endDate'))
        if endDateOMC and endDateOMC < currentDate:
            colorOMC = u'red'
        result.compulsoryPolicy = result.policy
    policyRecord = getClientVoluntaryPolicy(clientId, date)
    result.voluntaryPolicyRecord = policyRecord
    if policyRecord:
        result.voluntaryPolicy = formatPolicy(policyRecord.value('insurer_id'),
                                              policyRecord.value('serial'),
                                              policyRecord.value('number'),
                                              policyRecord.value('begDate'),
                                              policyRecord.value('endDate'),
                                              policyRecord.value('name'),
                                              policyRecord.value('note'),
                                              policyRecord.value('policyKind_id')
                                             )
        voluntaryPolicyServiceDMC = forceBool(policyRecord.value('voluntaryServiceStop'))
        colorDMC = u'blue' if not voluntaryPolicyServiceDMC else u'red'
        endDateDMC = forceDate(policyRecord.value('endDate'))
        if endDateDMC and endDateDMC < currentDate:
            colorDMC = u'red'

    if result.compulsoryPolicy or result.voluntaryPolicy:
        result.compulsoryvoluntaryPolicy = u'''<B><font color=%s>%s</font></B>%s<B><font color=%s>%s</font></B>'''%(colorOMC, result.compulsoryPolicy, (u', Полис ДМС ' if result.voluntaryPolicy else ''), colorDMC, result.voluntaryPolicy)

    if hasRegAddress:
        regAddressRecord = getClientAddress(clientId, 0)
        if regAddressRecord:
            result.regAddressInfo = getAddress(regAddressRecord.value('address_id'), regAddressRecord.value('freeInput'), regAddressRecord.value('addressDate'))
            result.regAddress     = formatAddressInt(result['regAddressInfo'], 0)
            # WTF district?
            # district = getClientDistrict(forceRef(regAddressRecord.value('district')))
#            if district:
#                result['regAddress'] += u' %s окр.' % district
#             district = getClientDistrict(result.regAddressInfo.KLADRCode, result.regAddressInfo.KLADRStreetCode, result.regAddressInfo.number)
#             if district:
#                 result['regAddress'] += u' %s район.' % district
#           убрал во избежание появления подобных записей в картотеке "Краснодарский край, Темрюкский р-н, Темрюк г, Чернышевского ул, д. 22 Темрюкский р-н Краснодарского края район."

    if hasLocAddress:
        locAddressRecord = getClientAddress(clientId, 1)
        if locAddressRecord:
            result.locAddressInfo = getAddress(locAddressRecord.value('address_id'), locAddressRecord.value('freeInput'))
            result.locAddress     = formatAddressInt(result.locAddressInfo, 0)
            # WTF district?
            # district = getClientDistrict(result.locAddressInfo.KLADRCode, result.locAddressInfo.KLADRStreetCode, result.locAddressInfo.number)
            # if district:
            #     result['locAddress'] += u' %s район.' % district
            #           убрал во избежание появления подобных записей в картотеке "Краснодарский край, Темрюкский р-н, Темрюк г, Чернышевского ул, д. 22 Темрюкский р-н Краснодарского края район."

    workRecord = getClientWork(clientId)
    if workRecord:
        result.work = formatWork(workRecord)

    researchRecords = getClientResearch(clientId)
    if researchRecords:
        result.research = formatClientResearch(researchRecords)

        result.workRelationship['workRecord'] = workRecord
    # workInfo = getWorkRelationshipInfo(clientId)
    socStatusRecord = getCleintSocStatusType(clientId)
    if socStatusRecord:
        result.workRelationship['socStatusRecord'] = socStatusRecord
    allergyRecord = getClientAllergy(clientId) #tt1304
    result.allergy = allergyRecord if allergyRecord else None

    intoleranceMedicamentRecord = getClientIntoleranceMedicament(clientId)
    result.intoleranceMedicament = intoleranceMedicamentRecord if intoleranceMedicamentRecord else None

    return result


def getClientInfoEx(clientId, date=None):
    # сделать в CClientInfo
    clientInfo = getClientInfo(clientId)
    clientInfo.fullName = formatNameInt(clientInfo.lastName, clientInfo.firstName, clientInfo.patrName)
    clientInfo.shortName = formatShortNameInt(clientInfo.lastName, clientInfo.firstName, clientInfo.patrName)

    birthDate = clientInfo.birthDate
    clientInfo.birthDateStr = formatDate(birthDate)
    clientInfo.age = calcAge(clientInfo.birthDate, date)
    clientInfo.sex = formatSex(clientInfo.sexCode)
    clientInfo.SNILS = formatSNILS(clientInfo.SNILS)

    clientInfo.setdefault('document', u'не указан')
    clientInfo.setdefault('compulsoryPolicy', u'не указан')
    clientInfo.setdefault('voluntaryPolicy', u'не указан')
    clientInfo.policy = clientInfo.compulsoryPolicy
    clientInfo.socStatus = formatSocStatuses(clientInfo.get('socStatuses', u'не указан'))
    clientInfo.setdefault('regAddress', u'не указан')
    clientInfo.setdefault('locAddress', u'не указан')
    clientInfo.setdefault('work', u'не указано')
    # clientInfo['id'] = clientId
    clientInfo.phones = formatClientPhones(clientInfo.contacts)
    clientInfo.attaches = formatAttaches(clientInfo.attaches, date)
    return clientInfo

def formatAttachGetPersonName(attachId):
    if attachId:
        personRec = QtGui.qApp.db.getRecordEx('Person_Order', 'master_id',
                                              'orgStructure_id = {0} AND type = 6 AND ((validToDate IS NULL OR LENGTH(validToDate) = 0) or validToDate > now()) '
                                              'AND deleted=0 '
                                              'AND (SELECT 1 FROM Person p INNER JOIN rbSpeciality s ON p.speciality_id = s.id  WHERE p.id = Person_Order.master_id AND p.deleted=0 AND isHigh=1)'.format(
                                                  attachId))
        if personRec and forceRef(personRec.value('master_id')):
            return u' <font color=black> Участковый врач:</font> %s' % forceString(
                QtGui.qApp.db.translate('Person', 'id', forceRef(personRec.value('master_id')), 'formatPersonName(id)'))
    return ''

def formatAttachAsHTML_SynchronizeAttachment(attach, clientId, atDate):
    td = forceDate(atDate) if atDate else QDate.currentDate()
    bold = False
    txt = attach['name']
    color = '#ffa500'
    organisationName = getOrganisationShortName(attach['LPU_id'])
    orgstructureIdList, uch, mocode,OrgNameAttach = getWebattach(clientId)
    orgStructureWebIdTrue = attach[
                                'orgStructure_id'] in orgstructureIdList  # any(attach['orgStructure_id'] == org_id for org_id in orgstructureIdList)
    orgStructureWebId = orgstructureIdList[0] if orgstructureIdList else None
    orgUch = organisationName + u' (' + forceString(
        QtGui.qApp.db.translate('OrgStructure', 'id', attach['orgStructure_id'], 'code')) + u')'
    orgUch += formatAttachGetPersonName(attach['orgStructure_id'])

    orgUchWeb = ''
    if orgStructureWebId:
        orgUchWeb = organisationName + u' (' + forceString(
            QtGui.qApp.db.translate('OrgStructure', 'id', orgStructureWebId, 'code')) + u')'
    if attach['outcome'] or attach['endDate'].isValid() and attach['endDate'] <= td:


        txt = '<font color=red>' + txt + ' ' + orgUch + forceString(attach['endDate']) +'</font>'
        # txt = txt + ' '
        if orgStructureWebId or orgStructureWebIdTrue:
            txt += u'''<BR><font color=black>Прикрепление в ТФОМС:</font> %s''' % (
                OrgNameAttach)
        elif attach['name'] != u'умер':
            if uch and mocode:
                txt += u'''код МО: %s участок: %s''' % (mocode, uch)
            # else:
            #     txt += u' (не прикреплен)'
    elif orgStructureWebIdTrue:
        txt = txt + ' ' + orgUch
        color = 'green'
    elif orgStructureWebId:
        if not attach['orgStructure_id']:
            txt = u'''<BR><font color=black>Прикрепление в ТФОМС:</font> %s''' % (OrgNameAttach)
        else:
            txt = txt + ' ' + orgUch
            txt += u'''<BR><font color=black>Прикрепление в ТФОМС:</font> %s''' % (OrgNameAttach)
    elif uch and mocode:
        if orgUch:
            txt = txt + ' ' + orgUch
        else:
            txt += u' Отсутствуют данные'
        txt += u'''<BR><font color=black>Прикрепление в ТФОМС:</font> код МО: %s участок: %s</font>''' % (mocode, uch)
    else:
        txt = txt + ' ' + orgUch + u'</font> <BR><font color=black>Прикрепление в ТФОМС:<font color=#ffa500> Информация отсутствует</font>'

    return u'Прикрепление в МИС: <font color="%s">%s%s%s</font>' % (
    color, '<B>' if bold else '', txt, '</B>' if bold else '')

def formatAttachAsHTML(attach, atDate):
    td = forceDate(atDate) if atDate else QDate.currentDate()
    bold = False
    txt = attach['name']
    orgStructureCode = u' (' + forceString(QtGui.qApp.db.translate('OrgStructure', 'id', attach['orgStructure_id'], 'code')) + u')'
    personName = formatAttachGetPersonName(attach['orgStructure_id'])

    if attach['outcome']:
        color = 'red'
        txt = txt + ' ' + forceString(attach['begDate'])
    elif attach['temporary']:
        color = 'blue'
        bold = True
        txt = txt + ' ' + getOrganisationShortName(attach['LPU_id']) + orgStructureCode + personName
        if attach['begDate'].isValid():
            txt = txt + u' с ' + forceString(attach['begDate'])
            color = 'blue' if attach['begDate'] <= td else 'red'
        if attach['endDate'].isValid():
            txt = txt + u' по ' + forceString(attach['endDate'])
            color = 'blue' if attach['endDate'] >= td else 'red'
    else:
        txt = txt + ' ' + getOrganisationShortName(attach['LPU_id']) + orgStructureCode + personName
        if attach['endDate'].isValid():
            color = 'red' if attach['endDate'] < td else 'green'
        else:
            color = 'green'
    return u'Прикрепление: <font color="%s">%s%s%s</font>' % (color,  '<B>' if bold else '',  txt,  '</B>' if bold else '')

def formatAttachesAsHTML(attaches, clientId, atDate):
    if QtGui.qApp.checkGlobalPreference('23:SynchronizeAttachment', u'да'):
        return ', '.join([formatAttachAsHTML_SynchronizeAttachment(x, clientId, atDate) for x in attaches])
    else:
        return ', '.join([formatAttachAsHTML(x, atDate) for x in attaches])

def getWebattach(clientId):
    db = QtGui.qApp.db
    stmt = u'''SELECT 
    Org.fullName AS OrgNameAttach,
      o.id  AS id,
      sa.attach_area AS uch,
      sa.attach_mo AS mocode
    FROM soc_attachments sa
     LEFT JOIN OrgStructure o ON o.infisinternalcode=sa.attach_area 
     LEFT JOIN Organisation Org ON Org.infisCode =  sa.attach_mo
    WHERE sa.client_id = "{0}"'''.format(clientId)
    idlist = []
    uch = mocode = OrgNameAttach = ''
    result = db.query(stmt)
    while result.next():
        record = result.record()
        idlist.append(forceRef(record.value('id')))
        uch = forceString(record.value('uch'))
        mocode = forceString(record.value('mocode'))
        OrgNameAttach = forceString(record.value('OrgNameAttach'))
    return idlist, uch, mocode,OrgNameAttach

def getWebattachAsHTML(clientId):
    txt = ''
    orgstructureIdList, uch, mocode,OrgNameAttach = getWebattach(clientId)
    orgStructureWebId = orgstructureIdList[0] if orgstructureIdList else None
    if orgStructureWebId:
        record = QtGui.qApp.db.getRecordEx('OrgStructure', 'organisation_id, code', 'id = %d' % orgStructureWebId)
        if record:
            orgWebId = forceRef(record.value('organisation_id'))
            orgStructureWebCode = forceString(record.value('code'))
            orgUchWeb = OrgNameAttach + u' (' + uch + u')'
            txt += u'''Прикрепление в МИС: <font color=#ffa500>Информация отсутствует</font>
                           <BR>Прикрепление в ТФОМС: <font color=#ffa500>%s</font>''' % (
                orgUchWeb)
    elif uch and mocode:
        txt += u'''<BR>Прикрепление в МИС:
                        <font color=black>Прикрепление в ТФОМС: </font><font color=#ffa500> код МО: %s участок: %s</font>''' % (
            mocode, uch)
    else:
        txt += u'''Прикрепление в МИС: '''
    return txt

def formatAttach(attach,  atDate):
    # td = forceDate(atDate) if atDate else QDate.currentDate()
    txt = attach['name']
    orgStructureCode = u' (' + forceString(QtGui.qApp.db.translate('OrgStructure', 'id', attach['orgStructure_id'], 'code')) + u')'
    if attach['outcome']:
        txt = txt + ' ' + forceString(attach['begDate'])
    elif attach['temporary']:
        txt = txt + ' ' + getOrganisationShortName(attach['LPU_id']) + orgStructureCode
        if attach['begDate'].isValid():
            txt = txt + u' с ' + forceString(attach['begDate'])
        if attach['endDate'].isValid():
            txt = txt + u' по ' + forceString(attach['endDate'])
    else:
        txt = txt + ' ' + getOrganisationShortName(attach['LPU_id']) + orgStructureCode
    return txt


def formatAttaches(attaches,  atDate):
    return ', '.join([formatAttach(x,  atDate) for x in attaches])


def getSocStatusClassList():
    socStatusClassList = {}
    records = QtGui.qApp.db.getRecordList('rbSocStatusClass', 'id', 'group_id IS NULL')
    for record in records:
        classId = forceRef(record.value('id'))
        if classId and (classId not in socStatusClassList.keys()):
            socStatusClassList[classId] = []
    return socStatusClassList


def formatSocStatus(socStatusTypeId, socStatusClassList):
    db = QtGui.qApp.db
    tableClassTypeAssoc = db.table('rbSocStatusClassTypeAssoc')
    tableSocStatusClass = db.table('rbSocStatusClass')
    table = tableClassTypeAssoc.innerJoin(tableSocStatusClass, tableClassTypeAssoc['class_id'].eq(tableSocStatusClass['id']))
    cond  = tableClassTypeAssoc['type_id'].eq(socStatusTypeId)
    socStatusClasses = db.getDistinctIdList(table, 'IF(rbSocStatusClass.group_id IS NOT NULL, rbSocStatusClass.group_id, rbSocStatusClass.id) AS class_id', where=cond, order='class_id')
    for id in socStatusClasses:
        record = db.getRecordEx('rbSocStatusClass', 'IF(code = 1 OR group_id IN (SELECT SSC.id FROM rbSocStatusClass AS SSC WHERE SSC.code = 1), 1, 0) AS privilegeClass, group_id', 'id = %d'%(id))
        if record:
            groupId = forceRef(record.value('group_id'))
            privilegeClass = forceBool(record.value('privilegeClass'))
            if groupId and groupId in socStatusClassList.keys():
                socStatusClass = socStatusClassList[groupId]
                socStatusClass.append(CSocStatusTypeCache.getCode(socStatusTypeId) if privilegeClass else CSocStatusTypeCache.getName(socStatusTypeId))
            elif id in socStatusClassList.keys():
                socStatusClass = socStatusClassList[id]
                socStatusClass.append(CSocStatusTypeCache.getCode(socStatusTypeId) if privilegeClass else CSocStatusTypeCache.getName(socStatusTypeId))
    return socStatusClassList


def formatSocStatuses(socStatuses, asHtml=False):
    db = QtGui.qApp.db
    tableSSC = db.table('rbSocStatusClass')
    tableSSCT = db.table('rbSocStatusClassTypeAssoc')
    table = tableSSC.innerJoin(tableSSCT, tableSSCT['class_id'].eq(tableSSC['id']))
    sstIdList = db.getDistinctIdList(table, [tableSSCT['type_id']], [tableSSC['code'].eq('8')])
    if socStatuses:
        if QtGui.qApp.showingInInfoBlockSocStatus() == 0:
            if asHtml:
                lines = [(('<B>' + CSocStatusTypeCache.getCode(socStatusTypeId) + u'</B>') if socStatusTypeId not in sstIdList
                                                            else CSocStatusTypeCache.getCode(socStatusTypeId)) for socStatusTypeId in socStatuses]
            else:
                lines = [CSocStatusTypeCache.getCode(socStatusTypeId) for socStatusTypeId in socStatuses]
        elif QtGui.qApp.showingInInfoBlockSocStatus() == 1:
            if asHtml:
                lines = [((u'<B>' + CSocStatusTypeCache.getName(socStatusTypeId) + u'</B>') if (socStatusTypeId in sstIdList and CSocStatusTypeCache.getCode(socStatusTypeId) != u'м643')
                                                            else CSocStatusTypeCache.getName(socStatusTypeId)) for socStatusTypeId in socStatuses]
            else:
                lines = [CSocStatusTypeCache.getName(socStatusTypeId) for socStatusTypeId in socStatuses]
        else:
            if asHtml:
                lines = [((('<B>' + CSocStatusTypeCache.getCode(socStatusTypeId) + u'</B>-') if socStatusTypeId not in sstIdList
                                                            else (CSocStatusTypeCache.getCode(socStatusTypeId) + '-'))
                                + ((u'<B>' + CSocStatusTypeCache.getName(socStatusTypeId) + u'</B>') if (socStatusTypeId in sstIdList and CSocStatusTypeCache.getCode(socStatusTypeId) != u'м643')
                                                            else CSocStatusTypeCache.getName(socStatusTypeId))) for socStatusTypeId in socStatuses]
            else:
                lines = [CSocStatusTypeCache.getCode(socStatusTypeId) + '-' + CSocStatusTypeCache.getName(socStatusTypeId) for socStatusTypeId in socStatuses]
        lines.sort()
        return ', '.join(lines)
    else:
        return u'не указан'


def getClientMiniInfo(clientId, atDate=None):
    db = QtGui.qApp.db
    record = db.getRecord('Client', ['lastName', 'firstName', 'patrName', 'birthDate', 'sex'], clientId)
    if record:
        name  = formatName(record.value('lastName'), record.value('firstName'), record.value('patrName'))
        birthDate = forceDate(record.value('birthDate'))
        birthDateStr = formatDate(birthDate)
        age       = calcAge(birthDate, atDate)
        sex       = formatSex(forceInt(record.value('sex')))
        return u'%s, %s (%s) %s' % (name, birthDateStr, age, sex)
    else:
        return ''


def getClientBanner(clientId, atDate=None):
    appPrefs = QtGui.qApp.preferences.appPrefs
    showingFIO = forceBool(appPrefs.get('showingFIO', True))
    showingConsents = forceBool(appPrefs.get('showingConsents', True))
    showingIdentification = forceBool(appPrefs.get('showingIdentification', True))
    showingQuoting = forceBool(appPrefs.get('showingQuoting', True))
    showingSocStatuses = forceBool(appPrefs.get('showingSocStatuses', True))
    showingDocument = forceBool(appPrefs.get('showingDocument', True))
    showingCompulsoryPolicy = forceBool(appPrefs.get('showingCompulsoryPolicy', True))
    showingHospitalBed = forceBool(appPrefs.get('showingHospitalBed', True))
    showingVoluntaryPolicy = forceBool(appPrefs.get('showingVoluntaryPolicy', True))
    showingRegAddress = forceBool(appPrefs.get('showingRegAddress', True))
    showingLocAddress = forceBool(appPrefs.get('showingLocAddress', True))
    showingWork = forceBool(appPrefs.get('showingWork', True))
    showingPhones = forceBool(appPrefs.get('showingPhones', True))
    showingNotes = forceBool(appPrefs.get('showingNotes', True))
    showingAllergy = forceBool(appPrefs.get('showingAllergy', True))
    showingBirthPlace = forceBool(appPrefs.get('showingBirthPlace', True))
    showingObservationStatus = forceBool(appPrefs.get('showingObservationStatus', True))
    showingObservationGroup = forceBool(appPrefs.get('showingObservationGroup', False))
    showingAttaches = forceBool(appPrefs.get('showingAttaches', True))
    showingClientContingent = forceInt(appPrefs.get('showingClientContingent', 1))
    showingClientRelations = forceBool(appPrefs.get('showingClientRelations', False))
    showingBlockFromNewLine = forceBool(appPrefs.get('showingBlockFromNewLine', True))
    showingEpidCase = forceInt(appPrefs.get('showingEpidCase', 2))
    showingDispanserySpecialities = forceBool(appPrefs.get('showingDispanserySpecialities', True))
    showingResearch = forceBool(appPrefs.get('showingResearch', True))
    showingIntoleranceMedicament = forceBool(appPrefs.get('showingIntoleranceMedicament', True))
    showingProf = forceBool(appPrefs.get('showingProf', True))

    db = QtGui.qApp.db
    table = db.table('Client')
    cols = []
    if showingFIO:
        cols.extend(['lastName', 'firstName', 'patrName'])
    cols.append('birthDate')
    cols.append('deathDate')
    cols.append('sex')
    cols.append('SNILS')
    cols.append('getClientInfoDocumentLocation(id) AS documentLocation')
    if showingHospitalBed:
        cols.append('getClientInfoHospitalization(id) as hospitalBed')
    if showingSocStatuses:
        cols.append('getClientInfoSocStatus(id, {showing}) as socStatuses'.format(showing=QtGui.qApp.showingInInfoBlockSocStatus()))
    if showingConsents:
        cols.append('getClientInfoConsents(id, NULL, {0}) as clientConsents'.format(db.formatDate(atDate) if atDate else 'CURDATE()')) # TODO: даты события
    if showingIdentification:
        cols.append('getClientInfoIdentifications(id) as identification')
    if showingQuoting:
        cols.append('getClientInfoQuoting(id, CURDATE()) as quoting')
    if showingClientContingent != 2:
        cols.append('getClientInfoContingent(id, {0}) as contingents'.format(showingClientContingent))
    if showingAttaches:
        cols.append('getClientInfoAttach(id, 0, {0}, {1}) as permanentAttach'.format(db.formatDate(atDate) if atDate else 'NULL', forceInt(QtGui.qApp.checkGlobalPreference('23:SynchronizeAttachment', u'да'))))
        cols.append('getClientInfoAttach(id, 1, {0}, {1}) as temporaryAttach'.format(db.formatDate(atDate) if atDate else 'NULL', forceInt(QtGui.qApp.checkGlobalPreference('23:SynchronizeAttachment', u'да'))))
    if showingDocument:
        cols.append('getClientInfoDocument(id) as document')
    if showingCompulsoryPolicy:
        if atDate:
            cols.append("getClientInfoPolicy(id, 1, {0}, {1}) AS compulsoryPolicy".format(db.formatDate(atDate), QtGui.qApp.provinceKLADR()))
        else:
            cols.append("getClientInfoPolicy(id, 1, NULL, {0}) AS compulsoryPolicy".format(QtGui.qApp.provinceKLADR()))
    if showingVoluntaryPolicy:
        if atDate:
            cols.append("getClientInfoPolicy(id, 0, {0}, {1}) AS voluntaryPolicy".format(db.formatDate(atDate), QtGui.qApp.provinceKLADR()))
        else:
            cols.append("getClientInfoPolicy(id, 0, NULL, {0}) AS voluntaryPolicy".format(QtGui.qApp.provinceKLADR()))
    if showingRegAddress:
        cols.append('getClientRegAddress(id) AS regAddress')
    if showingLocAddress:
        cols.append('getClientLocAddress(id) AS locAddress')
    if showingWork:
        cols.append('getClientInfoWork(id) as work')
    if showingPhones:
        cols.append('getClientContacts(id) AS phones')
    if showingBirthPlace:
        cols.append('birthPlace')
    if showingAllergy:
        cols.append('getClientInfoAllergy(id) as allergy')
    if showingClientRelations:
        cols.append('getClientInfoRelations(id) as relations')
    if showingObservationStatus:
        cols.append('getClientInfoObservationStatus(id) as observationStatus')
    if showingEpidCase != 2:
        cols.append('getClientInfoEpidCases(id, 0) as epidCase')
    if showingNotes:
        cols.append('notes')
    if showingObservationGroup:
        cols.append('getClientInfoObservationGroup(id) as observationGroup')
    if showingIntoleranceMedicament:
        cols.append('getClientInfoIntoleranceMedicament(id) as intoleranceMedicament')
    if showingResearch:
        cols.append('getClientInfoResearch(id) as research')
    if showingDispanserySpecialities:
        cols.append('getClientInfoDispanserySpecialities(id) as dispanserySpecialities')
    if showingProf:
        cols.append('getClientProfEventThisYear(id) as lastProf')

    record = db.getRecord(table, cols, clientId)

    bannerHTML = []
    lineEnd = u'<br/>' if showingBlockFromNewLine else u', '

    deathDate = forceDateTime(record.value('deathDate'))
    lineItems = []
    if deathDate:
        lineItems.append(u'<b><font color=red>УМЕР %s</font></b>' % formatDateTime(deathDate))
    lineItems.append(u'Код пациента: <b><font size=+1 color=blue>%s</font></b>' % clientId)
    documentLocation = forceString(record.value('documentLocation'))
    if documentLocation:
        lineItems.append(documentLocation)
    bannerHTML.append(' '.join(lineItems))

    lineItems = []
    if showingFIO:
        lastName = forceString(record.value('lastName'))
        firstName = forceString(record.value('firstName'))
        patrName = forceString(record.value('patrName'))
        name = formatName(lastName, firstName, patrName)
        lineItems.append('<b><font size=+1>' + name + '</font></b>,')
    birthDate = forceDate(record.value('birthDate'))
    age = calcAge(birthDate, deathDate if deathDate else atDate)
    lineItems.append(u'дата рождения: <b>%s</b> (%s)' % (formatDate(birthDate), age))
    lineItems.append(u'пол: <b>' + formatSex(forceInt(record.value('sex'))) + '</b>')
    bannerHTML.append(' '.join(lineItems))

    if showingClientContingent != 2:
        contingents = forceString(record.value('contingents'))
        if contingents:
            bannerHTML.append(u'Наблюдаемый контингент: ' + contingents)

    if showingObservationGroup:
        observationGroup = forceString(record.value('observationGroup'))
        if observationGroup:
            bannerHTML.append(u'Группа наблюдения: <b>' + observationGroup + '</b>')

    lineItems = []
    snils = formatSNILS(forceString(record.value('SNILS')))
    lineItems.append(u'СНИЛС: <b>' + (snils if snils else u'не указан') + '</b>')
    if showingDocument:
        document = forceString(record.value('document'))
        lineItems.append(u'Документ: <b>' + (document if document else u'не указан') + '</b>')
    bannerHTML.append(' '.join(lineItems))

    if showingConsents:
        clientConsents = forceString(record.value('clientConsents'))
        if clientConsents:
            bannerHTML.append(u'Согласия: <b>' + clientConsents + '</b>')

    if showingDispanserySpecialities:
        dispanserySpecialities = forceString(record.value('dispanserySpecialities'))
        if dispanserySpecialities:
            bannerHTML.append(u'Д-учет: <font color=#990000><b>' + dispanserySpecialities + '</b></font>')

    if showingSocStatuses:
        socStatuses = forceString(record.value('socStatuses'))
        bannerHTML.append(u'Статус: ' + (socStatuses if socStatuses else u'<b>не указан</b>'))

    if showingAttaches:
        permanentAttach = forceString(record.value('permanentAttach'))
        temporaryAttach = forceString(record.value('temporaryAttach'))
        attaches = []
        if permanentAttach:
            attaches.append(permanentAttach)
        if temporaryAttach:
            attaches.append(temporaryAttach)
        if attaches:
            if QtGui.qApp.checkGlobalPreference('23:SynchronizeAttachment', u'да'):
                attaches = u', '.join(attaches)
            else:
                attaches = u'Прикрепление: ' + u', '.join(attaches)
            bannerHTML.append(attaches)
        else:
            bannerHTML.append(u'Прикрепление: <b>отсутствует</b>')

    if showingCompulsoryPolicy:
        compulsoryPolicy = forceString(record.value('compulsoryPolicy'))
        bannerHTML.append(u'Полис ОМС: ' + (compulsoryPolicy if compulsoryPolicy else u'<b>не указан</b>'))

    if showingVoluntaryPolicy:
        voluntaryPolicy = forceString(record.value('voluntaryPolicy'))
        bannerHTML.append(u'Полис ДМС: ' + (voluntaryPolicy if voluntaryPolicy else u'<b>не указан</b>'))

    if showingRegAddress:
        regAddress = forceString(record.value('regAddress'))
        if not regAddress:
            regAddress = u'не указан'
        bannerHTML.append(u'Адрес регистрации: <b>' + regAddress + '</b>')

    if showingLocAddress:
        locAddress = forceString(record.value('locAddress'))
        if not locAddress:
            locAddress = u'не указан'
        bannerHTML.append(u'Адрес проживания: <b>' + locAddress + '</b>' )

    if showingWork:
        work = forceString(record.value('work'))
        if not work:
            work = u'не указано'
        bannerHTML.append(u'Место работы (учёбы): <b>' + work + '</b>')

    lineItems = []
    if showingHospitalBed:
        hospitalBed = forceString(record.value('hospitalBed'))
        if hospitalBed:
            lineItems.append(u'Госпитализация: ' + hospitalBed)
    if showingObservationStatus:
        observationStatus = forceString(record.value('observationStatus'))
        if observationStatus:
            lineItems.append(observationStatus)
    if showingQuoting:
        quoting = forceString(record.value('quoting'))
        if quoting:
            lineItems.append(u'<i>Квоты:</i> ' + quoting)
    bannerHTML.append(' '.join(lineItems))

    if showingIdentification:
        identification = forceString(record.value('identification'))
        if identification:
            bannerHTML.append(identification)

    if showingPhones:
        phones = forceString(record.value('phones'))
        if phones:
            bannerHTML.append(u'Контакты: <b>' + phones + '</b>')

    if showingBirthPlace:
        birthPlace = forceString(record.value('birthPlace'))
        if birthPlace:
            bannerHTML.append(u'Место рождения: <b>' + birthPlace + '</b>')

    if showingResearch:
        research = forceString(record.value('research'))
        if research:
            bannerHTML.append(u'Обследования: <b>' + research + '</b>')

    if showingNotes:
        notes = forceString(record.value('notes'))
        if notes:
            bannerHTML.append(u'Примечания: <b><font color=#990000>' + notes + '</font></b>')

    if showingAllergy:
        allergy = forceString(record.value('allergy'))
        if allergy:
            bannerHTML.append(u'Аллергии: <b>' + allergy + '</b>')

    if showingIntoleranceMedicament:
        intoleranceMedicament = forceString(record.value('intoleranceMedicament'))
        if intoleranceMedicament:
            bannerHTML.append(u'Медикаментозная непереносимость: <b>' + intoleranceMedicament + '</b>')

    if showingClientRelations:
        relations = forceString(record.value('relations'))
        if relations:
            bannerHTML.append(u'Связи: <b>' + relations + '</b>' )

    if showingEpidCase != 2:
        epidCase = forceString(record.value('epidCase'))
        if epidCase:
            bannerHTML.append(epidCase)

    if showingProf:
        prof = forceString(record.value('lastProf'))
        if prof:
            bannerHTML.append(u'Профилактические мероприятия: <b>' + prof +'</b>')

    return u'<html><body>' + lineEnd.join(bannerHTML).replace('<br/><br/>', '<br/>').replace('<br/>,', ',<br/>') + '</body></html>'


def getClientString(clientId, atDate=None):
    info = getClientInfo(clientId)
    return formatClientString(info, atDate)


def clientIdToText(clientId, needSNILS=False):
    text = ''
    if clientId:
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableDocument = db.table('ClientDocument')
        tableLocAddress = db.table('ClientAddress').alias('loc')
        tableRegAddress = db.table('ClientAddress').alias('reg')
        tableDocumentType = db.table('rbDocumentType')
        cols = [tableClient['id'],
                tableClient['lastName'],
                tableClient['firstName'],
                tableClient['patrName'],
                tableClient['birthDate'],
                tableClient['sex'],
                tableDocument['serial'],
                tableDocument['number'],
                tableDocument['date'],
                tableDocument['origin'],
                tableDocumentType['name']
                ]
        if needSNILS:
            cols.append(tableClient['SNILS'])
        cols.append(u"IF(reg.id IS NOT null, CONCAT(_utf8 'Адрес регистрации: ', formatClientAddress(reg.id)), _utf8 '') AS regAddress, IF(loc.id IS NOT null, CONCAT(_utf8 'Адрес проживания: ', formatClientAddress(loc.id)), _utf8 '') AS logAddress")
        queryTable = tableClient.leftJoin(tableRegAddress, 'reg.id = getClientRegAddressId(Client.id)')
        queryTable = queryTable.leftJoin(tableLocAddress, 'loc.id = getClientLocAddressId(Client.id)')
        queryTable = queryTable.leftJoin(tableDocument, 'ClientDocument.id = getClientDocumentId(Client.id)')
        queryTable = queryTable.leftJoin(tableDocumentType, tableDocument['documentType_id'].eq(tableDocumentType['id']))
        cond = [tableClient['id'].eq(clientId),
                tableClient['deleted'].eq(0)
                ]

        record = db.getRecordEx(queryTable, cols, cond)
        if record:
            clientId = forceString(record.value('id'))
            lastName = forceString(record.value('lastName'))
            firstName = forceString(record.value('firstName'))
            patrName = forceString(record.value('patrName'))
            SNILS = formatSNILS(forceString(record.value('SNILS')))
            birthDate = forceString(record.value('birthDate'))
            sex = formatSex(forceInt(record.value('sex')))
            regAddress = forceString(record.value('regAddress'))
            logAddress = forceString(record.value('logAddress'))
            docName = forceString(record.value('name'))
            serialDoc = forceString(record.value('serial'))
            numberDoc = forceString(record.value('number'))
            originDoc = forceString(record.value('origin'))
            dateDoc = forceString(record.value('date'))
            FIO = ' '.join([lastName, firstName, patrName])
            sexStr = ': '.join([u'пол', sex])
            docSerialNumb = ' '.join([u' серия', serialDoc])
            docSerialNumb += ' '.join([u' номер', numberDoc])
            infoDoc = ': '.join([docName, docSerialNumb])
            infoDocOrg = ': '.join([u' выдан', originDoc])
            infoDocDate = ' '.join([dateDoc])
            infoDoc += ' '.join([infoDocOrg, infoDocDate])
            text = ', '.join([field for field in (FIO, SNILS, clientId, birthDate, sexStr, infoDoc, regAddress, logAddress) if field])
    else:
        text = ''
    return text


def eventIdToText(eventId):
    text = ''
    if eventId:
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableDiagnosis = db.table('Diagnosis')
        cols = [tableEvent['id'],
                tableEvent['setDate'],
                tableEvent['execDate'],
                tableDiagnosis['MKB'],
                tableEventType['name']
                ]

        queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        queryTable = queryTable.leftJoin(tableDiagnosis, 'Diagnosis.id=getEventDiagnosis(Event.id)')
        cond = [tableEvent['id'].eq(eventId),
                tableEvent['deleted'].eq(0)
                ]

        record = db.getRecordEx(queryTable, cols, cond)
        if record:
            eventId = forceString(record.value('id'))
            setDate = forceString(record.value('setDate'))
            execDate = forceString(record.value('execDate'))
            mkb = forceString(record.value('MKB'))
            eventType = forceString(record.value('name'))

            event = ' '.join([u'Код:', eventId])
            setDate = ' '.join([u'c', setDate])
            execDate = ' '.join([u'по', execDate])
            text = ', '.join([field for field in (event, setDate, execDate, mkb, eventType) if field])
    else:
        text = ''
    return text

#def getClientHospitalBeds(clientId = None):
#    result = [u'', 0]
#    if clientId:
#        currentDate = QDate.currentDate()
#        db = QtGui.qApp.db
#        tableAPHB = db.table('ActionProperty_HospitalBed')
#        tableAPT = db.table('ActionPropertyType')
#        tableAP = db.table('ActionProperty')
#        tableActionType = db.table('ActionType')
#        tableAction = db.table('Action')
#        tableEvent = db.table('Event')
#        tableOSHB = db.table('OrgStructure_HospitalBed')
#        tableOS = db.table('OrgStructure')
#        tableHBP = db.table('rbHospitalBedProfile')
#        cols = [tableAction['id'],
#                tableEvent['id'].alias('eventId'),
#                tableEvent['client_id'],
#                tableActionType['flatCode'],
#                tableAction['begDate'],
#                tableAction['endDate'],
#                tableOS['name'].alias('nameOS'),
#                tableOSHB['code'].alias('codeBed'),
#                tableOSHB['name'].alias('nameBed'),
#                tableHBP['code'].alias('codeBedProfile'),
#                tableHBP['name'].alias('nameBedProfile'),
#                ]
#        queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
#        queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
#        queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
#        queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
#        queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
#        queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))
#        queryTable = queryTable.innerJoin(tableHBP, tableHBP['id'].eq(tableOSHB['profile_id']))
#        queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
#        cond = [ tableEvent['deleted'].eq(0),
#                 tableAction['deleted'].eq(0),
#                 tableAP['deleted'].eq(0),
#                 tableActionType['deleted'].eq(0),
#                 tableOS['deleted'].eq(0),
#                 tableEvent['client_id'].eq(clientId),
#                 tableEvent['setDate'].le(currentDate),
#                 tableAction['begDate'].le(currentDate),
#                 tableAPT['typeName'].like('HospitalBed'),
#                 tableAP['action_id'].eq(tableAction['id'])
#               ]
#        cond.append(db.joinOr([tableEvent['execDate'].isNull(), tableEvent['execDate'].ge(currentDate)]))
#        cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(currentDate)]))
#        cond.append(db.joinOr([tableActionType['flatCode'].like('moving'), tableActionType['flatCode'].like('planning')]))
#        records =  db.getRecordList(queryTable, cols, cond)
#        for record in records:
#            nameOS = forceString(record.value('nameOS'))
#            codeBed = forceString(record.value('codeBed'))
#            nameBed = forceString(record.value('nameBed'))
#            flatCode = forceString(record.value('flatCode'))
#            codeBedProfile = forceString(record.value('codeBedProfile'))
#            nameBedProfile = forceString(record.value('nameBedProfile'))
#            resultStr = u'подразделение: ' + nameOS + u', ' + codeBed + u'-' + nameBed + u'(' + codeBedProfile + u'-' + nameBedProfile + u')'
#            if u'moving' in flatCode.lower():
#               resultFlatCode = 1
#            elif u'planning' in flatCode.lower():
#               resultFlatCode = 0
#            result = [resultStr, resultFlatCode]
#        return result


def getClientHospitalOrgStructureAndBedRecords(clientId):
    result = [None, None]
    if clientId:
        db = QtGui.qApp.db
        #tableAPHB = db.table('ActionProperty_HospitalBed')
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableOSHB = db.table('OrgStructure_HospitalBed')
        tableOS = db.table('OrgStructure')
        tableHBP = db.table('rbHospitalBedProfile')
        #tableAPOS = db.table('ActionProperty_OrgStructure')
        currentDateTime = QDateTime.currentDateTime()
        cols = [tableAction['id'],
                tableEvent['id'].alias('eventId'),
                tableEvent['client_id'],
                tableActionType['flatCode'],
                tableAction['begDate'],
                tableAction['endDate']
                ]
        condBeds = [tableAP['deleted'].eq(0),
                    tableActionType['deleted'].eq(0),
                    tableAPT['deleted'].eq(0),
                    tableAPT['typeName'].like('HospitalBed')
                   ]
        condBeds.append('A.deleted = 0')
        condBeds.append('A.id = Action.id')
        condBeds.append('ActionProperty.action_id=A.id')
        condOS = [tableAP['deleted'].eq(0),
                  tableActionType['deleted'].eq(0),
                  tableAPT['deleted'].eq(0)
                 ]
        condOS.append('A.id = Action.id')
        condOS.append('A.deleted = 0')
        condOS.append('ActionProperty.action_id=A.id')
        condOS.append('ActionProperty.type_id=ActionPropertyType.id')
        condOS.append('''(ActionProperty.id IN (SELECT DISTINCT APHB.id FROM ActionProperty_HospitalBed AS APHB) AND NOT(SELECT DISTINCT APHB.value FROM ActionProperty_HospitalBed AS APHB WHERE APHB.id = ActionProperty.id LIMIT 1)) OR (ActionProperty.id NOT IN (SELECT DISTINCT APHB.id FROM ActionProperty_HospitalBed AS APHB))''')
        condOS.append(db.joinOr([tableAPT['name'].like(u'Отделение пребывания'), tableAPT['typeName'].like('HospitalBed')]))
        cols.append('''(SELECT ActionProperty_HospitalBed.value
        FROM ActionType
        INNER JOIN Action AS A ON ActionType.id=A.actionType_id
        INNER JOIN ActionPropertyType ON ActionPropertyType.actionType_id=ActionType.id
        INNER JOIN ActionProperty ON ActionProperty.type_id=ActionPropertyType.id
        INNER JOIN ActionProperty_HospitalBed ON ActionProperty_HospitalBed.id=ActionProperty.id
        WHERE %s
        LIMIT 0,1) AS bedId''' % (db.joinAnd(condBeds)))
        cols.append('''(SELECT ActionProperty_OrgStructure.value
        FROM ActionType
        INNER JOIN Action AS A ON ActionType.id=A.actionType_id
        INNER JOIN ActionPropertyType ON ActionPropertyType.actionType_id=ActionType.id
        INNER JOIN ActionProperty ON ActionProperty.type_id=ActionPropertyType.id
        INNER JOIN ActionProperty_OrgStructure ON ActionProperty_OrgStructure.id=ActionProperty.id
        WHERE %s
        LIMIT 0,1) AS orgStructureId ''' % (db.joinAnd(condOS)))
        cols.append('''(SELECT name
        FROM OrgStructure
        WHERE OrgStructure.id = orgStructureId
        LIMIT 0,1) AS orgStructureName ''')

        queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
        queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
        cond = [ tableEvent['deleted'].eq(0),
             tableAction['deleted'].eq(0),
             tableAP['deleted'].eq(0),
             tableActionType['deleted'].eq(0),
             tableAPT['deleted'].eq(0),
             tableEvent['client_id'].eq(clientId),
             tableEvent['setDate'].le(currentDateTime),
             tableAction['begDate'].le(currentDateTime),
             tableAP['action_id'].eq(tableAction['id'])
            ]
        cond.append(db.joinOr([tableEvent['execDate'].isNull(), tableEvent['execDate'].ge(currentDateTime)]))
        cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(currentDateTime)]))
        cond.append(db.joinOr([tableActionType['flatCode'].like('moving'), tableActionType['flatCode'].like('planning')]))
        recordsMoving = db.getRecordListGroupBy(queryTable, cols, cond, u'Action.id')
        for record in recordsMoving:
            result = [record, None]
            bedId = forceRef(record.value('bedId'))
            queryTableBed = tableOSHB.innerJoin(tableHBP, tableHBP['id'].eq(tableOSHB['profile_id']))
            queryTableBed = queryTableBed.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
            colsBed = [tableOS['name'].alias('nameOS'),
                       tableOS['code'].alias('codeOS'),
                       tableOSHB['code'].alias('codeBed'),
                       tableOSHB['name'].alias('nameBed'),
                       tableHBP['code'].alias('codeBedProfile'),
                       tableHBP['name'].alias('nameBedProfile')
                       ]
            recordsBed = db.getRecordListGroupBy(queryTableBed, colsBed, [tableOSHB['id'].eq(bedId)], u'OrgStructure_HospitalBed.id')
            for recordBed in recordsBed:
                result = [record, recordBed]
    return result


def getClientHospitalOrgStructureAndBeds(clientId):
    result = [u'', 0]
    resultStr = ''
    flatCode = ''
    resultFlatCode = -1
    [recordMoving, recordBed] = getClientHospitalOrgStructureAndBedRecords(clientId)
    if recordMoving:
        # bedId = forceRef(recordMoving.value('bedId'))
        orgStructureName = forceString(recordMoving.value('orgStructureName'))
        flatCode = forceString(recordMoving.value('flatCode'))
        resultStr = (u' отделение: %s;' % orgStructureName) if orgStructureName else u''
    if recordBed:
        # nameOS = forceString(recordBed.value('nameOS'))
        # codeOS = forceString(recordBed.value('codeOS'))
        codeBed = forceString(recordBed.value('codeBed'))
        # nameBed = forceString(recordBed.value('nameBed'))
        codeBedProfile = forceString(recordBed.value('codeBedProfile'))
        nameBedProfile = forceString(recordBed.value('nameBedProfile'))
        resultStr += u' койка: %s (%s-%s)' % (codeBed, codeBedProfile, nameBedProfile)
    if u'moving' in flatCode.lower():
        resultFlatCode = 1
    elif u'planning' in flatCode.lower():
        resultFlatCode = 0
    result = [resultStr, resultFlatCode]
    return result


def formatClientString(info, atDate=None):
    id        = info.id
    name      = formatName(info.lastName, info.firstName, info.patrName)
    birthDate = formatDate(info.birthDate)
    birthPlace= info.birthPlace
    age       = calcAge(info.birthDate, atDate)
    sex       = formatSex(info.sexCode)
    SNILS     = formatSNILS(info.SNILS) if info.SNILS else u'не указан'
    attaches  = info.get('attaches', u'отсутствует')
    socStatuses = info.get('socStatuses', u'не указан')

    document  = info.get('document', u'не указан')
    compulsoryPolicy = info.get('compulsoryPolicy', u'не указан')
    voluntaryPolicy  = info.get('voluntaryPolicy', u'')
    regAddress = info.get('regAddress', u'не указан')
    locAddress = info.get('locAddress', u'не указан')
    work       = info.get('work', u'не указано')
    notes      = info.get('notes', u'')
    identification = info.get('identification',  u'')
    phones     = getClientPhonesEx(id)
    hospitalBed, busy = getClientHospitalOrgStructureAndBeds(id)
    if hospitalBed:
        bed = u'Госпитализация: %s %s' % (busy, hospitalBed)
    else:
        bed = ''

    bannerHTML = u'''код: %s
				 %s, дата рождения: %s (%s) пол: %s 
				 СНИЛС: %s Документ: %s 
				 Статус: %s
				 %s
				 Прикрепление: %s , 
				 Полис ОМС %s %s 
				 %s 
				 Адрес регистрации: %s 
				 Адрес проживания: %s 
				 Место работы (учёбы): %s
				 %s ''' % (id,
				 name, birthDate, age, sex,
				 SNILS, document,
				 formatSocStatuses(socStatuses),
				 formatAttachesAsHTML(attaches, id, atDate),
				 compulsoryPolicy, (u', Полис ДМС ' if voluntaryPolicy else u''), voluntaryPolicy,
				 regAddress,
				 locAddress,
				 work,
				 bed,
				 ((u' %s' % identification) if identification else u''))

    if phones:
        bannerHTML += u'Контакты: %s' % phones
    if birthPlace:
        bannerHTML += u'Место рождения: <B>%s</B>' % birthPlace
    if notes:
        bannerHTML += u'Примечания: %s' % notes

    try:
        TFAccountingSystemId = QtGui.qApp.TFAccountingSystemId()
        if TFAccountingSystemId:
            tableClientIdentification = QtGui.qApp.db.table('ClientIdentification')
            identDate = QtGui.qApp.db.getRecordEx(
                tableClientIdentification,
                'max(checkDate)',
                'client_id= %d and accountingSystem_id = %d' % (id, TFAccountingSystemId))
            if identDate:
                checkDate = forceDate(identDate.value(0))
                if checkDate:
                    bannerHTML += u'Дата подтверждения ТФОМС: %s' % forceString(checkDate)
    except:
        QtGui.qApp.logCurrentException()

    clientBanner = u'%s' % bannerHTML
    return clientBanner


def getClientContextData(clientId):
    from Events.TempInvalidInfo import CTempInvalidInfoList
    clientInfo = getClientInfo2(clientId)
    getTempInvalidList = lambda begDate=None, endDate=None, types=None: CTempInvalidInfoList._get(clientInfo.context, clientId, begDate, endDate, types)
    data = {'client': clientInfo,
            'getTempInvalidList': getTempInvalidList,
            'tempInvalids': getTempInvalidList()}
    return data

# проверка правильности ввода "номера единого полиса" (см. приложение к задаче №0004219)
def unitedPolicyIsVaid(number):
    return (len(number) == 16
            and number.isdigit()
            and str(-sum(int(d) for d in number[-3::-2]+str(int(number[-2::-2])*2)) % 10) == number[-1])

######################################################
# mixin для проверки применимости врача/подразделения
# к данному пациенту
######################################################

class CCheckNetMixin:
    def __init__(self):
        self.reset()
        self.connect(QtGui.qApp, SIGNAL('dbConnectionChanged(bool)'), self.onConnectionChanged)

    def reset(self):
        self.mapSpecialityIdToSpecialityConstraint = {}
        self.mapPersonIdToSpecialityId = {}
        self.mapPersonIdToOrgId = {}
        self.mapPersonIdToOrgStructureId = {}
        self.mapOrgStructureIdToNetId = {}
        self.mapNetIdToNet = {}

    def onConnectionChanged(self, state):
        if not state:
            self.reset()

    def _getPersonIds(self, personId):
        db = QtGui.qApp.db
        record = db.getRecord('Person', 'speciality_id, org_id, orgStructure_id', personId)
        if record:
            specialityId = forceRef(record.value(0))
            orgId = forceRef(record.value(1))
            orgStructureId = forceRef(record.value(2))
        else:
            specialityId = None
            orgId = None
            orgStructureId = None
        self.mapPersonIdToSpecialityId[personId] = specialityId
        self.mapPersonIdToOrgId[personId] = orgId
        self.mapPersonIdToOrgStructureId[personId] = orgStructureId

    def getPersonSpecialityId(self, personId):
        if personId not in self.mapPersonIdToOrgStructureId:
            self._getPersonIds(personId)
        return self.mapPersonIdToSpecialityId[personId]

    def getSpecialityConstraint(self, specialityId):
        if specialityId in self.mapSpecialityIdToSpecialityConstraint:
            return self.mapSpecialityIdToSpecialityConstraint[specialityId]
        else:
            specialityConstraint = CSpecialityConstraint(specialityId)
            self.mapSpecialityIdToSpecialityConstraint[specialityId] = specialityConstraint
            return specialityConstraint

    def getPersonOrgId(self, personId):
        if personId not in self.mapPersonIdToOrgId:
            self._getPersonIds(personId)
        return self.mapPersonIdToOrgId[personId]

    def getPersonOrgStructureId(self, personId):
        if personId not in self.mapPersonIdToOrgStructureId:
            self._getPersonIds(personId)
        return self.mapPersonIdToOrgStructureId[personId]

    def getOrgStructureNetId(self, orgStructureId):
        if orgStructureId in self.mapOrgStructureIdToNetId:
            return self.mapOrgStructureIdToNetId[orgStructureId]
        else:
            netId = getOrgStructureNetId(orgStructureId)
            self.mapOrgStructureIdToNetId[orgStructureId] = netId
            return netId

    def getNet(self, netId):
        if netId in self.mapNetIdToNet:
            return self.mapNetIdToNet[netId]
        else:
            net = CNet(netId)
            self.mapNetIdToNet[netId] = net
            return net

    def getOrgStructureNet(self, orgStructureId):
        return self.getNet(self.getOrgStructureNetId(orgStructureId))

    def getPersonSpecialityConstraint(self, personId):
        return self.getSpecialityConstraint(self.getPersonSpecialityId(personId))

    def getPersonNet(self, personId):
        return self.getNet(self.getOrgStructureNetId(self.getPersonOrgStructureId(personId)))

    def getClientSexAndAge(self, clientId):
        db = QtGui.qApp.db
        table  = db.table('Client')
        record = db.getRecord(table, 'sex, birthDate', clientId)
        if record:
            clientSex = forceInt(record.value('sex'))
            clientBirthDate = forceDate(record.value('birthDate'))
            clientAge       = calcAgeTuple(clientBirthDate, QDate.currentDate())
            return clientSex, clientAge
        else:
            return None, None

#    def checkNetApplicable(self, net, clientId):
#        if net.sex or net.age:
#            clientSex, clientAge = self.getClientSexAndAge(clientId)
#            return not clientSex or net.applicable(clientSex, clientAge)
#        return True

#    def checkOrgStructureNetApplicable(self, orgStructureId, clientId):
#        return self.checkNetApplicable(self.getOrgStructureNet(orgStructureId), clientId)

    def checkClientAttendance(self, personId, clientId):
        net = self.getPersonNet(personId)
        specialityConstraint = self.getPersonSpecialityConstraint(personId)
        if net.constrain() or specialityConstraint.constrain():
            clientSex, clientAge = self.getClientSexAndAge(clientId)
            return specialityConstraint.applicable(clientSex, clientAge) and net.applicable(clientSex, clientAge)
        return True

    def checkClientAttendanceEx(self, personId, clientSex, clientAge):
        net = self.getPersonNet(personId)
        specialityConstraint = self.getPersonSpecialityConstraint(personId)
        if net.constrain() or specialityConstraint.constrain():
            return specialityConstraint.applicable(clientSex, clientAge) and net.applicable(clientSex, clientAge)
        return True

    def confirmClientAttendance(self, widget, personId, clientId):
        message = u'Пациент не относится к лицам, обслуживаемым указанным врачом.\nВсё равно продолжить?'
        return QtGui.QMessageBox.critical(widget,
                                          u'Внимание!',
                                          message,
                                          QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                          QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes


    def checkClientAttach(self, personId, clientId, date, boolCreateOrder = False):
        def _isAttachActive(attach):
            if not attach:
                return False
            return not(attach['outcome']
                       or attach['endDate']         and (forceDate(date) if date else QDate.currentDate()) > attach['endDate']
                       or attach['orgStructure_id'] and self.getPersonOrgStructureId(personId) not in getOrgStructureDescendants(attach['orgStructure_id'])
                       or attach['LPU_id']          and self.getPersonOrgId(personId) != attach['LPU_id']
                       )

        if QtGui.qApp.isStrictAttachCheckOnEventCreation() != 2:
            isStrict = QtGui.qApp.isStrictAttachCheckOnEventCreation()
            temporary = getAttachRecord(clientId, True)
            if isStrict and not (_isAttachActive(temporary) or _isAttachActive(getAttachRecord(clientId, False))):
                QtGui.QMessageBox.critical(self,
                                           u'Внимание!',
                                           u'У этого пациента нет подходящего прикрепления',
                                           QtGui.QMessageBox.Ok,
                                           QtGui.QMessageBox.Ok)
                return False

            if temporary:
                attachTypeId = temporary.get('attachTypeId', None)
                code = temporary.get('code', u'')
                name = temporary.get('name', u'')
                if attachTypeId:
                    db = QtGui.qApp.db
                    tablePerson = db.table('Person')
                    # tableOrgStructure = db.table('OrgStructure')
                    tableOSDA = db.table('OrgStructure_DisabledAttendance')
                    table = tablePerson.innerJoin(tableOSDA, tableOSDA['master_id'].eq(tablePerson['orgStructure_id']))
                    record = db.getRecordEx(table,
                                            [tableOSDA['disabledType']],
                                            [tablePerson['deleted'].eq(0), tablePerson['id'].eq(personId), tableOSDA['attachType_id'].eq(attachTypeId)])
                    if record:
                        disabledType = forceInt(record.value('disabledType'))
                        if not isStrict and (disabledType == 0 or (disabledType == 1 and not boolCreateOrder)):
                            buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
                            message = u'Запрещено обслуживание врачом по прикреплению: %s.\nВсё равно продолжить?'%(code + u'-' + name)
                            buttonsFocus = QtGui.QMessageBox.No
                            buttonsResult = QtGui.QMessageBox.Yes
                        else:
                            buttons = QtGui.QMessageBox.Ok
                            message = u'Запрещено обслуживание врачом по прикреплению: %s.\n'%(code + u'-' + name)
                            buttonsFocus = QtGui.QMessageBox.Ok
                            buttonsResult = None
                        return QtGui.QMessageBox.critical(self,
                                                          u'Внимание!',
                                                          message,
                                                          buttons,
                                                          buttonsFocus) == buttonsResult
        return True


    def confirmClientPolicyConstraint(self, widget, clientId):
        if QtGui.qApp.isStrictPolicyCheckOnEventCreation() != 2:
            compulsoryServiceStop = 0
            voluntaryServiceStop = 0
            recordCompulsoryPolicy = getClientCompulsoryPolicy(clientId)
            if recordCompulsoryPolicy:
                compulsoryServiceStop = forceBool(recordCompulsoryPolicy.value('compulsoryServiceStop'))
            recordVoluntaryPolicy = getClientVoluntaryPolicy(clientId)
            if recordVoluntaryPolicy:
                voluntaryServiceStop = forceBool(recordVoluntaryPolicy.value('voluntaryServiceStop'))
            if compulsoryServiceStop or voluntaryServiceStop:
                if compulsoryServiceStop:
                    messageFinance = u'ОМС'
                elif voluntaryServiceStop:
                    messageFinance =  u'ДМС'
                message = u'По данной СМО приостановлено обслуживание %s полисов.\nЭто может привести к затруднениям оплаты обращения.\nВсё равно продолжить?'%(messageFinance)
                return QtGui.QMessageBox.critical(widget,
                                                  u'Внимание!',
                                                  message,
                                                  QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                                  QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes
        return True


class CSpecialityConstraint(CSexAgeConstraint):
    def __init__(self, id):
        CSexAgeConstraint.__init__(self)
        db = QtGui.qApp.db
        table = db.table('rbSpeciality')
        record = db.getRecord(table, 'sex, age', id)
        if record:
            self.initByRecord(record)
        else:
            self.code = None
            self.name = None

##################################################
# ClientInfo как объект: требуется для
# печати форм и т.п.
##################################################
class CClientInfo(CInfo):
    def __init__(self, context, id, date=None):
        from Events.EventInfo import CDiagnosticInfoListEx
        CInfo.__init__(self, context)
        self._id = id
        self._date = date
        self._lastName  = ''
        self._firstName = ''
        self._patrName  = ''

        self._sexCode   = -1
        self._sex       = ''
        self._birthDate = CDateInfo(None)
        self._birthTime = CTimeInfo(None)
        self._deathDate = CDateTimeInfo(None)
        self._deathPlaceType = ''
        self._birthPlace= ''
        self._ageTuple  = None
        self._age       = ''
        self._SNILS     = ''
        self._notes     = ''
        self._permanentAttach = self.getInstance(CClientAttachInfo, None, False)
        self._temporaryAttach = self.getInstance(CClientAttachInfo, None, True)
        self._socStatuses = self.getInstance(CClientSocStatusInfoList, None)
        self._document  = self.getInstance(CClientDocumentInfo, clientId=None)
        self._compulsoryPolicy = None
        self._voluntaryPolicy  = None
        self._regAddress = None
        self._locAddress = None
        self._work       = None
        self._contacts   = ''
        self._phones     = ''
        self._bloodType  = self.getInstance(CBloodTypeInfo, None)
        self._bloodDate  = CDateInfo(None)
        self._bloodNotes  = ''
        self._intolerances = self.getInstance(CClientIntoleranceMedicamentInfoList, None)
        self._allergies    = self.getInstance(CClientAllergyInfoList, None)
        self._identification = self.getInstance(CClientIdentificationInfo, None)
        self._relations    = self.getInstance(CClientRelationInfoList, None, date)
        self._quotas       = self.getInstance(CClientQuotaInfoList, None)
        self._consents     = self.getInstance(CClientConsentInfoList, None, date)
        self._vaccinations = self.getInstance(CClientVaccinationInfoList, None)
        self._vaccinationProbe = self.getInstance(CClientVaccinationProbeInfoList, None)
        self._diagnostics  = self.getInstance(CDiagnosticInfoListEx, None)
        self._medicalexemption = self.getInstance(CClientMedicalExemptionInfoList, None)
        self._birthHeight     = 0
        self._birthWeight     = 0
        self._birthNumber = 0
        self._birthGestationalAge  = 0
        self._statusObservation = self.getInstance(CClientStatusObservationInfo, None)
        self._createDatetime = CDateTimeInfo(None)
        self._createPerson = self.getInstance(CPersonInfo, None)
        self._modifyDatetime = CDateTimeInfo(None)
        self._modifyPerson = self.getInstance(CPersonInfo, None)
        self._begDate = CDateInfo(None)
        self._endDate = CDateInfo(None)
        self._platform = ''
        self._server = ''
        self._clientEvents = []
        self._documentLocation = ''
        self._dispensarySpecialties = ''

        self._createDatetime = CDateTimeInfo(None)
        self._createPerson = self.getInstance(CPersonInfo, None)
        self._modifyDatetime = CDateTimeInfo(None)
        self._modifyPerson = self.getInstance(CPersonInfo, None)
        self._epidCases = []
        self._riskFactors = []


    def _load(self):
        from Events.EventInfo import CDiagnosticInfoListEx
        db = QtGui.qApp.db
        table  = db.table('Client')
        if self._id:
            record = db.getRecord(table, '*', self._id)
        else:
            record = None
        if record:
            # self.id        = forceString(record.value('id'))
            self._lastName  = forceString(record.value('lastName'))
            self._firstName = forceString(record.value('firstName'))
            self._patrName  = forceString(record.value('patrName'))

            self._sexCode   = forceInt(record.value('sex'))
            self._sex       = formatSex(self._sexCode)
            self._birthDate = CDateInfo(record.value('birthDate'))
            self._birthTime = CTimeInfo(forceTime(record.value('birthTime')))
            self._deathDate = CDateTimeInfo(record.value('deathDate'))
            self._deathPlaceType = self.getInstance(CDeathPlaceTypeInfo, forceRef(record.value('deathPlaceType_id')))
            self._birthPlace= forceString(record.value('birthPlace'))
            self._ageTuple  = calcAgeTuple(self._birthDate.date, self._date)
            self._age       = formatAgeTuple(self._ageTuple, self._birthDate.date, self._date)
            self._SNILS     = formatSNILS(forceString(record.value('SNILS')))
            self._notes     = forceString(record.value('notes'))
            self._permanentAttach = self.getInstance(CClientAttachInfo, self._id, False)
            self._temporaryAttach = self.getInstance(CClientAttachInfo, self._id, True)
            self._socStatuses = self.getInstance(CClientSocStatusInfoList, self._id)
            self._document  = self.getInstance(CClientDocumentInfo, clientId=self._id)
            self._compulsoryPolicy = self.getInstance(CClientPolicyInfo, self._id, True)
            self._voluntaryPolicy  = self.getInstance(CClientPolicyInfo, self._id, False)
            self._regAddress = self.getInstance(CClientAddressInfo, self._id, 0)
            self._locAddress = self.getInstance(CClientAddressInfo, self._id, 1)
            self._work       = self.getInstance(CClientWorkInfo, self._id)
            self._contacts   = getClientPhones(self._id)
            self._phones     = formatClientPhones(self._contacts)
            self._bloodType  = self.getInstance(CBloodTypeInfo, forceRef(record.value('bloodType_id')))
            self._bloodDate  = CDateInfo(record.value('bloodDate'))
            self._bloodNotes  = forceString(record.value('bloodNotes'))
            self._intolerances = self.getInstance(CClientIntoleranceMedicamentInfoList, self._id)
            self._allergies    = self.getInstance(CClientAllergyInfoList, self._id)
            self._identification = self.getInstance(CClientIdentificationInfo, self._id)
            self._relations    = self.getInstance(CClientRelationInfoList, self._id, self._date)
            self._quotas       = self.getInstance(CClientQuotaInfoList, self._id)
            self._consents     = self.getInstance(CClientConsentInfoList, self._id, self._date)
            self._vaccinations = self.getInstance(CClientVaccinationInfoList, self._id)
            self._medicalexemption = self.getInstance(CClientMedicalExemptionInfoList, self._id)
            self._vaccinationProbe = self.getInstance(CClientVaccinationProbeInfoList, self._id)
            self._diagnostics  = self.getInstance(CDiagnosticInfoListEx, self._id)
            self._birthHeight     = forceInt(record.value('birthHeight'))
            self._birthWeight     = forceInt(record.value('birthWeight'))
            self._birthNumber = forceInt(record.value('birthNumber'))
            self._birthGestationalAge     = forceInt(record.value('birthGestationalAge'))

            self._statusObservation = self.getInstance(CClientStatusObservationInfo, self._id)
            self._createDatetime = CDateTimeInfo(record.value('createDatetime'))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._modifyDatetime = CDateTimeInfo(record.value('modifyDatetime'))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._epidCases = self.getInstance(CClientEpidCaseInfoList, self._id)
            self._riskFactors = self.getInstance(CClientRiskFactorInfoList, self._id)
            self._begDate = CDateInfo(record.value('begDate'))
            self._endDate = CDateInfo(record.value('endDate'))
            self._platform = platform.system()
            self._server = forceString(QtGui.qApp.preferences.dbServerName)
            self._researchList = self.getInstance(CClientResearchInfoList, self._id)
            self._activeDispensaryList = self.getInstance(CClientActiveDispensaryInfoList, self._id)
            self._dangerousList = self.getInstance(CClientDangerousInfoList, self._id)
            self._forcedTreatmentList = self.getInstance(CClientForcedTreatmentInfoList, self._id)
            self._suicideList = self.getInstance(CClientSuicideInfoList, self._id)
            self._contingentKindList = self.getInstance(CClientContingentKindInfoList, self._id)
            self._clientEvents = self.getEventCount(self._id)
            self._documentLocation = getClientDocumentLocation(self._id)
            self._dispensarySpecialties = getDispensarySpecialties(self._id)
            return True
        else:
            return False

    def getEventCount(self, clientId):
        idList=[]
        cond = []
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        queryTable = tableEvent.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        cond.append(tableEvent['client_id'].eq(clientId))
        cond.append(tableEvent['deleted'].eq(0))
        records = db.getRecordList(queryTable, ['Event.id as eventId'], cond)
        clientEvents = None
        if records:
            from Events.EventInfo import CEventInfo,CEventInfoList
            for record in records:
                idList.append(forceInt(record.value('eventId')))
            clientEvents = self.getInstance(CEventInfoList, idList)
            clientEvents._load()
        return clientEvents

    def getOrgStructureDescendants(self, orgStructureId):
        u'''получить список id подразделений, вложенных в данное + само подразделение'''
        return QtGui.qApp.db.getDescendants('OrgStructure', 'parent_id', orgStructureId)

    def __str__(self):
        self.load()
        return formatShortNameInt(self.lastName, self.firstName, self.patrName)

    def ageOnDate(self, date):
        if type(date) in [CDateInfo, CDateTimeInfo]:
            date = date.date
        ageTuple = calcAgeTuple(self.load()._birthDate.date, date)
        return formatAgeTuple(ageTuple, self.load()._birthDate.date, date)

    def CustomAgeOnDate(self, birthDate, date):
        if type(date) in [CDateInfo, CDateTimeInfo]:
            date = date.date
        if type(birthDate) in [CDateInfo, CDateTimeInfo]:
            birthDate = birthDate.date
        ageTuple = calcAgeTuple(birthDate, date)
        return formatAgeTuple(ageTuple, birthDate, date)

    id           = property(lambda self: self.load()._id)
    lastName     = property(lambda self: self.load()._lastName)
    firstName    = property(lambda self: self.load()._firstName)
    patrName     = property(lambda self: self.load()._patrName)
    fullName     = property(lambda self: formatNameInt(self.lastName, self.firstName,self.patrName))
    shortName    = property(lambda self: formatShortNameInt(self.lastName, self.firstName,self.patrName))
    sexCode      = property(lambda self: self.load()._sexCode)
    sex          = property(lambda self: self.load()._sex)
    birthDate    = property(lambda self: self.load()._birthDate)
    birthTime    = property(lambda self: self.load()._birthTime)
    deathDate    = property(lambda self: self.load()._deathDate)
    deathPlaceType    = property(lambda self: self.load()._deathPlaceType)
    birthPlace   = property(lambda self: self.load()._birthPlace)
    ageTuple     = property(lambda self: self.load()._ageTuple)
    age          = property(lambda self: self.load()._age)
    SNILS        = property(lambda self: self.load()._SNILS)
    notes        = property(lambda self: self.load()._notes)
    permanentAttach = property(lambda self: self.load()._permanentAttach)
    temporaryAttach = property(lambda self: self.load()._temporaryAttach)
    socStatuses     = property(lambda self: self.load()._socStatuses)
    document        = property(lambda self: self.load()._document)
    compulsoryPolicy= property(lambda self: self.load()._compulsoryPolicy)
    voluntaryPolicy = property(lambda self: self.load()._voluntaryPolicy)
    policy          = compulsoryPolicy
    policyDMS       = voluntaryPolicy
    regAddress      = property(lambda self: self.load()._regAddress)
    locAddress      = property(lambda self: self.load()._locAddress)
    work            = property(lambda self: self.load()._work)
    contacts        = property(lambda self: self.load()._contacts)
    phones          = property(lambda self: self.load()._phones)
    bloodType       = property(lambda self: self.load()._bloodType)
    bloodDate       = property(lambda self: self.load()._bloodDate)
    bloodNotes       = property(lambda self: self.load()._bloodNotes)
    intolerances    = property(lambda self: self.load()._intolerances)
    allergies       = property(lambda self: self.load()._allergies)
    identification  = property(lambda self: self.load()._identification)
    relations       = property(lambda self: self.load()._relations)
    quotas          = property(lambda self: self.load()._quotas)
    consents        = property(lambda self: self.load()._consents)
    vaccinations    = property(lambda self: self.load()._vaccinations)
    vaccinationProbe = property(lambda self: self.load()._vaccinationProbe)
    diagnostics    = property(lambda self: self.load()._diagnostics)
    medicalexemption    = property(lambda self: self.load()._medicalexemption)
    birthHeight    = property(lambda self: self.load()._birthHeight)
    birthWeight    = property(lambda self: self.load()._birthWeight)
    birthNumber = property(lambda self: self.load()._birthNumber)
    birthGestationalAge    = property(lambda self: self.load()._birthGestationalAge)
    statusObservation = property(lambda self: self.load()._statusObservation)
    createDatetime = property(lambda self: self.load()._createDatetime)
    createPerson = property(lambda self: self.load()._createPerson)
    modifyDatetime = property(lambda self: self.load()._modifyDatetime)
    modifyPerson = property(lambda self: self.load()._modifyPerson)
    epidCases         = property(lambda self: self.load()._epidCases)
    riskFactors       = property(lambda self: self.load()._riskFactors)
    begDate    = property(lambda self: self.load()._begDate)
    endDate    = property(lambda self: self.load()._endDate)
    platform    = property(lambda self: self.load()._platform)
    server    = property(lambda self: self.load()._server)
    clientEvents    = property(lambda self: self.load()._clientEvents)
    documentLocation    = property(lambda self: self.load()._documentLocation)
    researchList = property(lambda self: self.load()._researchList)
    activeDispensaryList = property(lambda self: self.load()._activeDispensaryList)
    dangerousList = property(lambda self: self.load()._dangerousList)
    forcedTreatmentList = property(lambda self: self.load()._forcedTreatmentList)
    suicideList = property(lambda self: self.load()._suicideList)
    contingentKindList = property(lambda self: self.load()._contingentKindList)
    dispensarySpecialties = property(lambda self: self.load()._dispensarySpecialties)


class CClientInfoListEx(CInfoList):
    def __init__(self, context, clientIdList):
        CInfoList.__init__(self, context)
        self.idList = clientIdList

    def _load(self):
        self._items = [self.getInstance(CClientInfo, id) for id in self.idList]
        return True


class CRBVaccineSchemaTransitionTypeInfo(CRBInfo):
    tableName = 'rbVaccine_SchemaTransitionType'


class CRBReactionInfo(CRBInfoWithIdentification):
    tableName = 'rbReaction'


class CRBVaccinationResultInfo(CRBInfo):
    tableName = 'rbVaccinationResult'


class CRBVaccinationProbeInfo(CRBInfoWithIdentification):
    tableName = 'rbVaccinationProbe'


class CRBMedicalExemptionTypeInfo(CRBInfo):
    tableName = 'rbMedicalExemptionType'

class CRBMedicalExemptionReasonInfo(CRBInfo):
    tableName = 'rbMedicalExemptionReason'


class CClientMedicalExemptionInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self.clientId = clientId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ClientMedicalExemption')
        idList = db.getIdList(table, 'id', [table['client_id'].eq(self.clientId), table['deleted'].eq(0)], 'id')
        self._items = [ self.getInstance(CClientMedicalExemptionInfo, id) for id in idList ]
        return True


class CClientMedicalExemptionInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('ClientMedicalExemption', '*', self.id)
        if record:
            self._date = CDateInfo(forceDate(record.value('date')))
            self._MKB = forceString(record.value('MKB'))
            self._person = self.getInstance(CPersonInfo, forceRef(record.value('person_id')))
            self._endDate = CDateInfo(forceDate(record.value('endDate')))
            self._medicalExemptionType = self.getInstance(CRBMedicalExemptionTypeInfo, forceRef(record.value('medicalExemptionType_id')))
            self._medicalExemptionReason = self.getInstance(CRBMedicalExemptionReasonInfo, forceRef(record.value('medicalExemptionReason_id')))
            self._infections = self.getInstance(CClientMedicalExemptionInfectionInfoList, forceRef(record.value('id')))
        else:
            self._date = CDateInfo()
            self._MKB = ''
            self._person = self.getInstance(CPersonInfo, None)
            self._endDate = CDateInfo()
            self._medicalExemptionType = self.getInstance(CRBMedicalExemptionTypeInfo, None)
            self._medicalExemptionReason = self.getInstance(CRBMedicalExemptionReasonInfo, None)
            self._infections = self.getInstance(CClientMedicalExemptionInfectionInfoList, None)

    date = property(lambda self: self.load()._date)
    MKB = property(lambda self: self.load()._MKB)
    person = property(lambda self: self.load()._person)
    endDate = property(lambda self: self.load()._endDate)
    medicalExemptionType = property(lambda self: self.load()._medicalExemptionType)
    medicalExemptionReason = property(lambda self: self.load()._medicalExemptionReason)
    infections = property(lambda self: self.load()._infections)


class CRBVaccineIdentificationInfo(object):
    def __init__(self, value, vaccinationType, note):
        self._value = value
        self._vaccinationType = vaccinationType
        self._note = note

    @property
    def value(self):
        return self._value

    @property
    def vaccinationType(self):
        return self._vaccinationType

    @property
    def note(self):
        return self._note

    def __str__(self):
        return self.value


class CRBVaccineInfo(CRBInfo,CIdentificationInfoMixin):
    tableName = 'rbVaccine'

    def __init__(self, context, id):
        CRBInfo.__init__(self, context, id)
        CIdentificationInfoMixin.__init__(self)
        self._mapUrnToIdentifier = {}

    def _initByRecord(self, record):
        self._regionalCode = forceString(record.value('regionalCode'))
        self._dose         = forceDouble(record.value('dose'))

    def _initByNull(self):
        self._regionalCode = u''
        self._dose         = 0.0

    def identify(self, urn):
        if self.id:
            if urn in self._mapUrnToIdentifier:
                return self._mapUrnToIdentifier[urn]
            else:
                condUrn = QtGui.qApp.db.table('rbAccountingSystem').alias('A')['urn'].eq(urn)
                query = QtGui.qApp.db.query('SELECT I.value, I.vaccinationType, I.note'
                                            ' FROM rbVaccine_Identification I'
                                            ' JOIN rbAccountingSystem A ON I.system_id = A.id'
                                            ' WHERE I.deleted = 0 AND I.master_id = %d AND %s'
                                            ' ORDER BY I.id DESC LIMIT 1' % (self.id, condUrn))
                if query.first():
                    value = forceString(query.value(0))
                    vaccinationType = forceString(query.value(1))
                    note = forceString(query.value(2))
                    result = CRBVaccineIdentificationInfo(value, vaccinationType, note)
                else:
                    result = CRBVaccineIdentificationInfo(u'', u'', u'')
                self._mapUrnToIdentifier[urn] = result
                return result
        else:
            return None

    def identifyByType(self, urn, vaccinationType):
        if self.id:
            if urn in self._mapUrnToIdentifier:
                return self._mapUrnToIdentifier[urn]
            else:
                condUrn = QtGui.qApp.db.table('rbAccountingSystem').alias('A')['urn'].eq(urn)
                query = QtGui.qApp.db.query('SELECT I.value, I.vaccinationType, I.note'
                                            ' FROM rbVaccine_Identification I'
                                            ' JOIN rbAccountingSystem A ON I.system_id = A.id'
                                            ' WHERE I.deleted = 0 AND I.master_id = %d AND %s and I.vaccinationType = "%s"'
                                            ' ORDER BY I.id DESC LIMIT 1' % (self.id, condUrn, vaccinationType))
                if query.first():
                    value = forceString(query.value(0))
                    vaccinationType = forceString(query.value(1))
                    note = forceString(query.value(2))
                    result = CRBVaccineIdentificationInfo(value, vaccinationType, note)
                else:
                    result = CRBVaccineIdentificationInfo(u'', u'', u'')
                self._mapUrnToIdentifier[urn] = result
                return result
        else:
            return None

    regionalCode = property(lambda self: self.load()._regionalCode)
    dose         = property(lambda self: self.load()._dose)


class CClientMedicalExemptionInfectionInfoList(CInfoList):
    def __init__(self, context, masterId):
        CInfoList.__init__(self, context)
        self.masterId = masterId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ClientMedicalExemption_Infection')
        idList = db.getIdList(table, 'id', table['master_id'].eq(self.masterId), 'id')
        self._items = [ self.getInstance(CClientMedicalExemptionInfectionInfo, id) for id in idList ]
        return True


class CClientMedicalExemptionInfectionInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('ClientMedicalExemption_Infection', '*', self.id)
        if record:
            self._infection = self.getInstance(CRBInfectionInfo, forceRef(record.value('infection_id')))
        else:
            self._infection = self.getInstance(CRBInfectionInfo, None)

    infection = property(lambda self: self.load()._infection)


class CClientVaccinationProbeInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self._id = id

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('ClientVaccinationProbe', '*', self._id)
        if record:
            self._probe = self.getInstance(CRBVaccinationProbeInfo, forceRef(record.value('probe_id')))
            code, name, urn, version, value, note, checkDate,value_spr, name_spr, record_ = getIdentificationInfoById('rbVaccinationProbe', forceRef(record.value('probeIdentificationIBP_id')))
            self._probeIdentificationIBP = _identification(code, name, urn, version, value, note, CDateInfo(checkDate),value_spr, name_spr, record)
            self._datetime = CDateTimeInfo(forceDate(record.value('datetime')))
            self._dose = forceDouble(record.value('dose'))
            self._seria = forceString(record.value('seria'))
            self._person = self.getInstance(CPersonInfo, forceRef(record.value('person_id')))
            self._reaction = self.getInstance(CRBReactionInfo, forceRef(record.value('reaction_id')))
            self._reactionDate = CDateInfo(forceDate(record.value('reactionDate')))
            self._result = self.getInstance(CRBVaccinationResultInfo, forceRef(record.value('result_id')))
            self._relegateOrg = self.getInstance(COrgInfo, forceRef(record.value('relegateOrg_id')))
            infectionIdList = set([])
            infections = forceString(db.translate('rbVaccinationProbe', 'id', forceRef(record.value('probe_id')), 'infections'))
            infectionList = set(infections.split(u','))
            infectionIdList |= infectionList
            infectionIdList = list(infectionIdList)
            self._infections = self.getInstance(CClientVaccinationProbeInfectionInfoList, infectionIdList)
        else:
            self._probe = self.getInstance(CRBVaccinationProbeInfo, None)
            self._probeIdentificationIBP = _identification(None, None, None, None, None, None, None, None, None, None)
            self._datetime = CDateTimeInfo()
            self._dose = 0.0
            self._seria = ''
            self._person = self.getInstance(CPersonInfo, None)
            self._reaction = self.getInstance(CRBReactionInfo, None)
            self._reactionDate = CDateInfo()
            self._result = self.getInstance(CRBVaccinationResultInfo, None)
            self._relegateOrg = self.getInstance(COrgInfo, None)
            self._infections = self.getInstance(CClientVaccinationProbeInfectionInfoList, [])

    id = property(lambda self: self.load()._id)
    probe = property(lambda self: self.load()._probe)
    probeIdentificationIBP = property(lambda self: self.load()._probeIdentificationIBP)
    datetime = property(lambda self: self.load()._datetime)
    dose = property(lambda self: self.load()._dose)
    seria = property(lambda self: self.load()._seria)
    person = property(lambda self: self.load()._person)
    reaction = property(lambda self: self.load()._reaction)
    reactionDate = property(lambda self: self.load()._reactionDate)
    result = property(lambda self: self.load()._result)
    relegateOrg = property(lambda self: self.load()._relegateOrg)
    infections = property(lambda self: self.load()._infections)


class CRBInfectionInfo(CRBInfoWithIdentification):
    tableName = 'rbInfection'

    def _initByRecord(self, record):
        self._regionalCode = forceString(record.value('regionalCode'))
        self._minimumTerm  = forceString(record.value('minimumTerm'))

    def _initByNull(self):
        self._regionalCode = u''
        self._minimumTerm  = u''

    regionalCode = property(lambda self: self.load()._regionalCode)
    minimumTerm  = property(lambda self: self.load()._minimumTerm)


class CRBInfectionInfoList(CInfoList):
    def __init__(self, context, vaccineId):
        CInfoList.__init__(self, context)
        self._vaccineId = vaccineId
        self._idList = []

    def _load(self):
        vaccineInfectionIdList = getVaccineInfectionIdList(self._vaccineId)
        self._items = [self.getInstance(CRBInfectionInfo, id) for id in vaccineInfectionIdList]
        return True

    def __str__(self):
        self.load()
        if self._items:
            return u', '.join([unicode(item) for item in self._items])
        return u''


class CClientVaccinationInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self._id = id

    def _load(self):
        table = QtGui.qApp.db.table('ClientVaccination')
        if self._id:
            record = QtGui.qApp.db.getRecord(table, '*', self._id)
            result = True
        else:
            record = table.newRecord()
            result = False

        self._vaccine          = self.getInstance(CRBVaccineInfo, forceRef(record.value('vaccine_id')))
        code, name, urn, version, value, note, checkDate,value_spr, name_spr, record_ = getIdentificationInfoById('rbVaccine', forceRef(record.value('vaccineIdentificationIBP_id')))
        self._vaccineIdentificationIBP = _identification(code, name, urn, version, value, note, CDateInfo(checkDate),value_spr, name_spr, record_)
        self._vaccinationType  = forceString(record.value('vaccinationType'))
        self._datetime         = CDateTimeInfo(forceDateTime(record.value('datetime')))
        self._dose             = forceDouble(record.value('dose'))
        self._seria            = forceString(record.value('seria'))
        self._person           = self.getInstance(CPersonInfo, forceRef(record.value('person_id')))
        self._reaction         = self.getInstance(CRBReactionInfo, forceRef(record.value('reaction_id')))
        self._reactionDate     = CDateInfo(forceDateTime(record.value('reactionDate')))
        self._transitionType   = self.getInstance(CRBVaccineSchemaTransitionTypeInfo,
                                                  forceRef(record.value('transitionType_id')))
        self._relegateOrg      = self.getInstance(COrgInfo, forceRef(record.value('relegateOrg_id')))
        self._infections = self.getInstance(CRBInfectionInfoList, forceRef(record.value('vaccine_id')))

        return result

    id               = property(lambda self: self.load()._id)
    vaccine          = property(lambda self: self.load()._vaccine)
    vaccineIdentificationIBP = property(lambda self: self.load()._vaccineIdentificationIBP)
    vaccinationType  = property(lambda self: self.load()._vaccinationType)
    datetime         = property(lambda self: self.load()._datetime)
    dose             = property(lambda self: self.load()._dose)
    seria            = property(lambda self: self.load()._seria)
    person           = property(lambda self: self.load()._person)
    reaction         = property(lambda self: self.load()._reaction)
    reactionDate     = property(lambda self: self.load()._reactionDate)
    transitionType   = property(lambda self: self.load()._transitionType)
    relegateOrg      = property(lambda self: self.load()._relegateOrg)
    infections       = property(lambda self: self.load()._infections)

    def __str__(self):
        self.load()
        return self._vaccine.__str__()


class CClientVaccinationInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self._clientId = clientId
        self._idList = []

    def _load(self):
        clientVaccinationIdList = getClientVaccinationIdList(self._clientId)
        self._items = [self.getInstance(CClientVaccinationInfo, id) for id in clientVaccinationIdList]
        return True


class CClientVaccinationProbeInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self._clientId = clientId
        self._idList = []

    def _load(self):
        clientVaccinationProbeIdList = getClientVaccinationProbeIdList(self._clientId)
        self._items = [self.getInstance(CClientVaccinationProbeInfo, id) for id in clientVaccinationProbeIdList]
        return True

    def __str__(self):
        self.load()
        if self._items:
            return u', '.join([unicode(item) for item in self._items])
        return u''


class CClientVaccinationProbeInfectionInfoList(CInfoList):
    def __init__(self, context, idList):
        CInfoList.__init__(self, context)
        self.idList = idList

    def _load(self):
        self._items = [self.getInstance(CClientVaccinationInfectionInfo, id) for id in self.idList]
        return True

    def __str__(self):
        self.load()
        if self._items:
            return u', '.join([unicode(item) for item in self._items])
        return u''


class CClientVaccinationInfectionInfoList(CInfoList):
    def __init__(self, context, vaccineId):
        CInfoList.__init__(self, context)
        self.vaccineId = vaccineId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('rbInfection_rbVaccine')
        idList = db.getIdList(table, 'id', table['vaccine_id'].eq(self.vaccineId), 'id')
        self._items = [self.getInstance(CClientVaccinationInfectionInfo, id) for id in idList]
        return True


class CClientVaccinationInfectionInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('rbInfection_rbVaccine', '*', self.id)
        if record:
            self._infection = self.getInstance(CRBInfectionInfo, forceRef(record.value('infection_id')))
        else:
            self._infection = self.getInstance(CRBInfectionInfo, None)

    infection = property(lambda self: self.load()._infection)

    def __str__(self):
        self.load()
        if self._infection:
            return self._infection.name
        return u''


class CClientConsentInfo(CInfo):
    def __init__(self, context, record):
        CInfo.__init__(self, context)
        self._record = record

    def _load(self):
        if self._record:
            self._id = forceRef(self._record.value('clientConsentId'))
            self._code = forceString(self._record.value('consentTypeCode'))
            self._name = forceString(self._record.value('consentTypeName'))
            self._value = forceInt(self._record.value('value'))
            self._strValue = u'Да' if forceInt(self._record.value('value')) else u'Нет'
            self._date = forceDate(self._record.value('date'))
            self._endDate = forceDate(self._record.value('endDate'))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(self._record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(self._record.value('createPerson_id')))
            self._representerClientId = forceRef(self._record.value('representerClientId'))

            representerRecord = QtGui.qApp.db.getRecord('Client',
                                                        'lastName, firstName, patrName',
                                                        self._representerClientId)
            if representerRecord:
                self._representer = formatShortNameInt(forceString(representerRecord.value('lastName')),
                                                       forceString(representerRecord.value('firstName')),
                                                       forceString(representerRecord.value('patrName'))
                                                       )
            else:
                 self._representer = u''
        else:
            self._id = None
            self._code = u''
            self._name = u''
            self._value = None
            self._strValue = u''
            self._date = CDateInfo(None)
            self._endDate = CDateInfo(None)
            self._representerClientId = None
            self._representer = u''
            self._modifyPerson = None
            self._createPerson = None

    def __str__(self):
        self.load()
        if self._id:
            return u': '.join([self._code, self._strValue])+forceString(self._date).join(['(', ')'])
        return u''

    id           = property(lambda self: self.load()._id)
    code = property(lambda self: self.load()._code)
    name = property(lambda self: self.load()._name)
    value = property(lambda self: self.load()._value)
    strValue = property(lambda self: self.load()._strValue)
    date = property(lambda self: self.load()._date)
    endDate = property(lambda self: self.load()._endDate)
    representerClientId = property(lambda self: self.load()._representerClientId)
    representer = property(lambda self: self.load()._representer)
    modifyPerson = property(lambda self: self.load()._modifyPerson)
    createPerson = property(lambda self: self.load()._createPerson)


class CClientConsentInfo(CInfo):
    def __init__(self, context, record):
        CInfo.__init__(self, context)
        self._record = record

    def _load(self):
        if self._record:
            self._id = forceRef(self._record.value('clientConsentId'))
            self._code = forceString(self._record.value('consentTypeCode'))
            self._name = forceString(self._record.value('consentTypeName'))
            self._value = forceInt(self._record.value('value'))
            self._strValue = u'Да' if forceInt(self._record.value('value')) else u'Нет'
            self._date = forceDate(self._record.value('date'))
            self._endDate = forceDate(self._record.value('endDate'))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(self._record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(self._record.value('createPerson_id')))
            self._representerClientId = forceRef(self._record.value('representerClientId'))

            representerRecord = QtGui.qApp.db.getRecord('Client',
                                                        'lastName, firstName, patrName',
                                                        self._representerClientId)
            if representerRecord:
                self._representer = formatShortNameInt(
                                                       forceString(representerRecord.value('lastName')),
                                                       forceString(representerRecord.value('firstName')),
                                                       forceString(representerRecord.value('patrName'))
                                                      )
            else:
                 self._representer = u''
        else:
            self._id = None
            self._code = u''
            self._name = u''
            self._value = None
            self._strValue = u''
            self._date = CDateInfo(None)
            self._endDate = CDateInfo(None)
            self._representerClientId = None
            self._representer = u''
            self._modifyPerson = None
            self._createPerson = None

    def __str__(self):
        self.load()
        if self._id:
            return u': '.join([self._code, self._strValue])+forceString(self._date).join(['(', ')'])
        return u''

    id           = property(lambda self: self.load()._id)
    code = property(lambda self: self.load()._code)
    name = property(lambda self: self.load()._name)
    value = property(lambda self: self.load()._value)
    strValue = property(lambda self: self.load()._strValue)
    date = property(lambda self: self.load()._date)
    endDate = property(lambda self: self.load()._endDate)
    representerClientId = property(lambda self: self.load()._representerClientId)
    representer = property(lambda self: self.load()._representer)
    modifyPerson = property(lambda self: self.load()._modifyPerson)
    createPerson = property(lambda self: self.load()._createPerson)


class CClientConsentInfoList(CInfoList):
    def __init__(self, context, clientId, date = None):
        CInfoList.__init__(self, context)
        self._clientId = clientId
        self._date = date
        self._idList = []

    def _load(self):
        clientConsentRecordList = getClientConsentsEx(self._clientId, self._date)
        self._items = [self.getInstance(CClientConsentInfo, record) for record in clientConsentRecordList]
        return True


class CClientStatusObservationInfo(CInfo):
    def __init__(self, context, clientId=None):
        CInfo.__init__(self, context)
        self._clientId = clientId
        self._color = u''
        self._name = u''
        self._code = u''

    def _load(self):
        if self._clientId:
            record = self.getClientStatusObservation(self._clientId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._color = forceString(record.value('color'))
            return True
        else:
            return False

    def getClientStatusObservation(self, clientId):
        db = QtGui.qApp.db
        cond=[]
        tableRbStatusObservationClientType = db.table('rbStatusObservationClientType')
        queryTable = db.table('Client_StatusObservation')
        queryTable = queryTable.leftJoin(tableRbStatusObservationClientType, queryTable['statusObservationType_id'].eq(tableRbStatusObservationClientType['id']))
        cond.append(queryTable['deleted'].eq(0))
        cond.append(queryTable['master_id'].eq(clientId))
        orderBy = u'Client_StatusObservation.createDatetime DESC'
        record = db.getRecordEx(queryTable, [tableRbStatusObservationClientType['code'], tableRbStatusObservationClientType['name'], tableRbStatusObservationClientType['color']], cond, orderBy)
        return record

    color = property(lambda self: self.load()._color)
    name = property(lambda self: self.load()._name)
    code = property(lambda self: self.load()._code)



class CClientDocumentInfo(CInfo):
    def __init__(self, context, clientId=None, documentId=None):
        CInfo.__init__(self, context)
        self._clientId = clientId
        self._documentId = documentId
        self._type = self.getInstance(CDocumentTypeInfo, None)
        self._documentTypeId = None
        self._documentType = u'-'
        self._documentTypeCode = u'-'
        self._documentTypeFederalCode = None
        self._documentTypeRegionalCode = u'-'
        self._serial = ''
        self._number = ''
        self._date = CDateInfo()
        self._origin = ''
        self._originCode = ''
        self._identification = self.getInstance(CDocumentIdentificationInfo, self._documentTypeId)


    def _load(self):
        if self._documentId:
            record = QtGui.qApp.db.getRecord('ClientDocument', '*', self._documentId)
        elif self._clientId:
            record = getClientDocument(self._clientId)
        else:
            record = None
        if record:
            documentTypeId = forceRef(record.value('documentType_id'))
            self._type = self.getInstance(CDocumentTypeInfo, documentTypeId)
            self._documentTypeId = documentTypeId
            self._documentType = forceString(QtGui.qApp.db.translate('rbDocumentType', 'id', documentTypeId, 'name'))
            self._documentTypeCode = forceString(QtGui.qApp.db.translate('rbDocumentType', 'id', documentTypeId, 'code'))
            self._documentTypeFederalCode = forceString(QtGui.qApp.db.translate('rbDocumentType', 'id', documentTypeId, 'federalCode'))
            self._documentTypeRegionalCode = forceString(QtGui.qApp.db.translate('rbDocumentType', 'id', documentTypeId, 'regionalCode'))
            self._serial = forceString(record.value('serial'))
            self._number = forceString(record.value('number'))
            self._date = CDateInfo(forceDate(record.value('date')))
            self._origin = forceString(record.value('origin'))
            self._originCode = forceString(record.value('originCode'))
            self._identification = self.getInstance(CDocumentIdentificationInfo, self._documentTypeId)
            return True
        else:
            return False


#    def __unicode__(self):
    def __str__(self):
        self.load()
        return (' '.join([self._type.name, self._serial, self._number])).strip()

    type             = property(lambda self: self.load()._type)
    documentTypeId = property(lambda self: self.load()._documentTypeId)
    documentType     = property(lambda self: self.load()._documentType)
    documentTypeName = property(lambda self: self.load()._documentType)
    documentTypeCode = property(lambda self: self.load()._documentTypeCode)
    documentTypeFederalCode = property(lambda self: self.load()._documentTypeFederalCode)
    documentTypeRegionalCode = property(lambda self: self.load()._documentTypeRegionalCode)
    serial           = property(lambda self: self.load()._serial)
    number           = property(lambda self: self.load()._number)
    date             = property(lambda self: self.load()._date)
    origin           = property(lambda self: self.load()._origin)
    originCode       = property(lambda self: self.load()._originCode)
    identification = property(lambda self: self.load()._identification)

#    documentType     = property(lambda self: self.load()._type.name) # удалить!
#    documentTypeName = property(lambda self: self.load()._type.name) # удалить!
#    documentTypeCode = property(lambda self: self.load()._type.code) # удалить!


class CClientSurveillanceInfo(CClientInfo):
    def __init__(self, context, id, date = None):
        CClientInfo.__init__(self, context, id, date)
        self._diagnostics = None

    def _load(self):
        from Events.EventInfo import CDiagnosticInfoListEx
        if CClientInfo._load(self):
            self._diagnostics = self.getInstance(CDiagnosticInfoListEx, self._id)
            return True
        else:
            self._diagnostics = self.getInstance(CDiagnosticInfoListEx, None)
            return False

    diagnostics = property(lambda self: self.load()._diagnostics)


class CClientSurveillanceInfoListEx(CInfoList):
    def __init__(self, context, clientIdList):
        CInfoList.__init__(self, context)
        self.idList = clientIdList


    def _load(self):
        self._items = [ self.getInstance(CClientSurveillanceInfo, id) for id in self.idList ]
        return True


class CRBPolicyTypeInfo(CRBInfo):
    tableName = 'rbPolicyType'


class CRBPolicyKindInfo(CRBInfo):
    tableName = 'rbPolicyKind'

    def _initByRecord(self, record):
        self._regionalCode = forceString(record.value('regionalCode'))

    def _initByNull(self):
        self._regionalCode = None

    regionalCode = property(lambda self: self.load()._regionalCode)


class CClientPolicyInfo(CInfo):
    def __init__(self, context, clientId, isCompulsory=True):
        CInfo.__init__(self, context)
        self.clientId = clientId
        self.isCompulsory = isCompulsory


    def _load(self):
        record = getClientPolicyEx(self.clientId, self.isCompulsory)
        if record:
            self._policyType = self.getInstance(CRBPolicyTypeInfo, forceRef(record.value('policyType_id')))
            self._policyKind = self.getInstance(CRBPolicyKindInfo, forceRef(record.value('policyKind_id')))
            self._insurer = self.getInstance(COrgInfo, forceRef(record.value('insurer_id')))
            self._serial  = forceString(record.value('serial'))
            self._number  = forceString(record.value('number'))
            self._name    = forceString(record.value('name'))
            self._note    = forceString(record.value('note'))
            self._begDate = CDateInfo(record.value('begDate'))
            self._endDate = CDateInfo(record.value('endDate'))
            return True
        else:
            self._policyType = self.getInstance(CRBPolicyTypeInfo, None)
            self._policyKind = self.getInstance(CRBPolicyKindInfo, None)
            self._insurer = self.getInstance(COrgInfo, None)
            self._serial  = ''
            self._number  = ''
            self._name    = ''
            self._note    = ''
            self._begDate = CDateInfo()
            self._endDate = CDateInfo()
            return False


#    def __unicode__(self):
    def __str__(self):
        self.load()
        return (' '.join([self._policyType.name, unicode(self._insurer), self._serial, self._number])).strip()

    policyType  = property(lambda self: self.load()._policyType)
    type        = property(lambda self: self.load()._policyType)
    kind        = property(lambda self: self.load()._policyKind)
    insurer     = property(lambda self: self.load()._insurer)
    serial      = property(lambda self: self.load()._serial)
    number      = property(lambda self: self.load()._number)
    name        = property(lambda self: self.load()._name)
    note        = property(lambda self: self.load()._note)
#    notes       = note
    begDate     = property(lambda self: self.load()._begDate)
    endDate     = property(lambda self: self.load()._endDate)

class COKATOInfo(CInfo):
    def __init__(self, context, code = None):
        CInfo.__init__(self, context)
        self._code = code
        self._name = None

    def _load(self):
        if self._code:
            db = QtGui.qApp.db
            stmt = 'SELECT `kladr`.`getOKATOName`(%s)' % (decorateString(self._code))
            query = db.query(stmt)
            if query.next():
                self._name = forceString(query.record().value(0))
                return True
        return False

    def __str__(self):
        return self.load()._code

    code = property(lambda self: self.load()._code)
    name = property(lambda self: self.load()._name)


class CAddressInfo(CInfo):
    def __init__(self, context, addressId):
        CInfo.__init__(self, context)
        self._addressId = addressId
        self._KLADRCode = ''
        self._KLADRStreetCode = ''
        self._city = ''
        self._exactCity = ''
        self._street = ''
        self._number = ''
        self._corpus = ''
        self._flat = ''
        self._index = ''
        self._text = ''
        self._OKATO = None
        self._district = None
        self._district23 = ''
        self._mainRegion = None


    def _load(self):
        parts = []
        address = getAddress(self._addressId)
        self._KLADRCode = address.KLADRCode
        self._KLADRStreetCode = address.KLADRStreetCode
        if self._KLADRCode:
            self._city = getCityName(self._KLADRCode)
            self._exactCity = getExactCityName(self._KLADRCode)
            parts.append(self._city)
        else:
            self._city = ''
        if self._KLADRStreetCode:
            self._street = getStreetName(self._KLADRStreetCode)
            parts.append(self._street)
        else:
            self._street = ''
        self._number = address.number
        self._corpus = address.corpus
        self._flat = address.flat
        self._index = address.index
        if self._number:
            parts.append(u'д.'+self._number)
        if self._corpus:
            parts.append(u'к.'+self._corpus)
        if self._flat:
            parts.append(u'кв.'+self._flat)
    #    if self._district23:
    #        parts.append(u'%s район' % self._district23)
        self._text = (', '.join(parts)).strip()
        return bool(self._text)


    def getOKATO(self):
        if self._OKATO is None:
            self.load()
            number = [self._number]
            if self._corpus:
                number.append(self._corpus)
            self._OKATO = self.getInstance(COKATOInfo, getOKATO(self._KLADRCode, self._KLADRStreetCode, u'к'.join(number)))
        return self._OKATO


    def getDistrict(self):
        if self._district is None:
            self.load()
            self._district = getDistrictName(self._KLADRCode, self._KLADRStreetCode, self._number)
        return self._district

    def getDistrict_23(self):
        db = QtGui.qApp.db
        if self._KLADRCode is None or len(self._KLADRCode) == 0:
            self._load() # если мы в шаблоне последовательно вызываем рег адрес и адрес проживания, то второй не грузится в поток, поэтому я его принудительно запускаю
        parent = self._KLADRCode[:5]
        if parent is not None:
            i = 13 - len(parent)
            newParent = parent
            for ii in xrange(i):
                newParent = newParent + '0'
            stmt = 'SELECT NAME FROM kladr.KLADR k  WHERE k.CODE= %s' % (newParent)
            try:
                query = db.query(stmt)
                if query.next():
                    return forceString(query.record().value(0))
            except:
                pass
        return ''

    def getKLADRAddress(self):
        db = QtGui.qApp.db
        addressId = self.load()._addressId
        address1 = getAddress(addressId)
        t = findHouseId(address1)
        stmt = 'SELECT CONCAT(s.SOCR," ",s.NAME),CONCAT(k.NAME," ",k.SOCR),r.NAME,a1.NAME FROM Address a   LEFT JOIN AddressHouse ah ON a.house_id = ah.id  LEFT JOIN kladr.STREET s ON s.CODE=ah.KLADRStreetCode LEFT JOIN kladr.KLADR k ON k.CODE=ah.KLADRCode  LEFT JOIN kladr.infisREGION r ON r.KLADR=CONCAT(k.parent,"00000000")  LEFT JOIN kladr.infisAREA a1 ON concat(r.kladrPrefix,"00000000000")=a1.KLADR or concat(k.parent,"00000000000")=a1.KLADR  WHERE ah.id= %s' % (
            t)
        try:
            query = db.query(stmt)
            if query.next():
                return (forceString(query.record().value(0)),forceString(query.record().value(1)),forceString(query.record().value(2)),forceString(query.record().value(3)))
        except:
            pass
        return ''

    def getMainRegion(self):
        if self._mainRegion is None:
            self.load()
            self._mainRegion = getMainRegionName(self._KLADRCode)
        return self._mainRegion


    @property
    def FIASStreetGUID(self):
        kladr = self.KLADRStreetCode[:15]
        if not kladr:
            kladr = self.KLADRCode[:11]
        if kladr:
            query = QtGui.qApp.db.query("SELECT fias.GetObjectGuidByKladr(%s)" % decorateString(kladr))
            if query.first():
                return forceString(query.value(0))
        return u''


    addressId        = property(lambda self: self.load()._addressId)
    KLADRCode       = property(lambda self: self.load()._KLADRCode)
    KLADRStreetCode = property(lambda self: self.load()._KLADRStreetCode)
    city            = property(lambda self: self.load()._city)
    exactCity       = property(lambda self: self.load()._exactCity)
    town            = city
    street          = property(lambda self: self.load()._street)
    number          = property(lambda self: self.load()._number)
    corpus          = property(lambda self: self.load()._corpus)
    flat            = property(lambda self: self.load()._flat)
    index           = property(lambda self: self.load()._index)
    OKATO           = property(getOKATO)
    district        = property(getDistrict_23)
    mainRegion         = property(getMainRegion)
    address        = property(getKLADRAddress)

#    def __unicode__(self):
    def __str__(self):
        self.load()
        return self._text



class CClientAddressInfo(CAddressInfo):
    def __init__(self, context, clientId, addrType):
        CAddressInfo.__init__(self, context, None)
        self._clientId = clientId
        self._addrType = addrType
        self._begDate = ''
        self._freeInput = ''
        self._index = ''
        self._resident = ''
        self._addressDate = QDate()

    def _load(self):
        record = getClientAddress(self._clientId, self._addrType)
        if record:
            self._addressId = forceRef(record.value('address_id'))
            self._begDate = CDateInfo(forceDate(record.value('createDatetime')))
            self._freeInput = forceString(record.value('freeInput'))
            self._resident = '' if record.value('resident').isNull() else forceInt(record.value('resident'))
            if self._addrType == 1 and self._resident != '':
                self._resident = u'Городской' if self._resident == 0 else u'Сельский'
            else:
                self._resident = ''
            self._livingArea = forceString(rblivingAreaName(forceString(record.value('livingArea'))))
            self._addressDate = CDateInfo(forceDate(record.value('addressDate')))
            # WTF district23?
            #self._district23 = getClientDistrict(forceRef(record.value('district')))
            result = getAddress(self._addressId, self._freeInput)
            self._index = result.index_
            self._district23 = getClientDistrict(result.KLADRCode, result.KLADRStreetCode, result.number)
            if self._addressId:
                return CAddressInfo._load(self)
            elif self._freeInput:
                return True
            else:
                return False
        else:
            self._addressId = None
            self._index = ''
            self._begDate = ''
            self._freeInput = ''
            self._livingArea = ''
            self._resident = ''
            self._addressDate = QDate()
            return False

    index_  = property(lambda self: self.load()._index)
    freeInput  = property(lambda self: self.load()._freeInput)
    livingArea  = property(lambda self: self.load()._livingArea)
    addressDate = property(lambda self: self.load()._addressDate)
    begDate  = property(lambda self: self.load()._begDate)
    resident  = property(lambda self: self.load()._resident)


#    def __unicode__(self):
    def __str__(self):
        self.load()
        if self._addressId and len(self._text):
            return CAddressInfo.__str__(self)
        else:
            return self.freeInput


class CClientWorkInfo(COrgInfo):
    def __init__(self, context, clientId):
        COrgInfo.__init__(self, context, None)
        self.clientId = clientId
        self._post = ''
        self._postId = self.getInstance(CRBClientWorkPost, None)
        self._OKVED = ''
        self._stage = ''
        self._hurts = []
        self._hurtFactors = []
        self._organisation = None
        self._shortName = ''


    def _load(self):
        workRecord = getClientWork(self.clientId)
        if workRecord:
#            self.orgId = forceRef(workRecord.value('org_id'))
            self.id = forceRef(workRecord.value('org_id'))
            if self.id:
                COrgInfo._load(self)
                self._organisation = self.getInstance(COrgInfo, forceRef(workRecord.value('org_id')))
            else:
                self._shortName = forceString(workRecord.value('freeInput'))
                self._organisation = None
            self._post = forceString(workRecord.value('post'))
            self._postId = self.getInstance(CRBClientWorkPost, forceRef(workRecord.value('post_id')))
            self._OKVED = forceString(workRecord.value('OKVED'))
            self._stage = forceString(workRecord.value('stage'))
            self._hurts = self.getInstance(CClientWorkHurtInfoList, forceRef(workRecord.value('id')))
            self._hurtFactors = self.getInstance(CClientWorkHurtFactorInfoList, forceRef(workRecord.value('id')))
            return True
        else:
            return False


#    def __unicode__(self):
    def __str__(self):
        self.load()
        parts = []
        if self._shortName:
            parts.append(self._shortName)
        if self._stage:
            parts.append(self._stage)
        if self._post:
            parts.append(self._post)
        if self._OKVED:
            parts.append(u'ОКВЭД: '+self._OKVED)
        return ', '.join(parts)

    shortName  = property(lambda self: self.load()._shortName)
    post       = property(lambda self: self.load()._post)
    postId     = property(lambda self: self.load()._postId)
    stage      = property(lambda self: self.load()._stage)
    OKVED      = property(lambda self: self.load()._OKVED)
    hurts      = property(lambda self: self.load()._hurts)
    organisation      = property(lambda self: self.load()._organisation)
    hurtFactors = property(lambda self: self.load()._hurtFactors)


class CRBClientWorkPost(CRBInfoWithIdentification):
    tableName = 'rbClientWorkPost'


class CClientWorkHurtInfoList(CInfoList):
    def __init__(self, context, workId):
        CInfoList.__init__(self, context)
        self.workId = workId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ClientWork_Hurt')
        idList = db.getIdList(table, 'id', table['master_id'].eq(self.workId), 'id')
        self._items = [ self.getInstance(CClientWorkHurtInfo, id) for id in idList ]
        return True


class CClientWorkHurtInfo(CInfo, CIdentificationInfoMixin):
    def __init__(self, context, clientWorkHurtId):
        CInfo.__init__(self, context)
        CIdentificationInfoMixin.__init__(self)
        self.clientWorkHurtId = clientWorkHurtId
        self.tableName = 'rbHurtType'


    def getHurtId(self):
        if not hasattr(self, 'id'):
            self.id = forceRef(QtGui.qApp.db.translate('ClientWork_Hurt', 'id', self.clientWorkHurtId, 'hurtType_id'))


    def identify(self, urn):
        self.getHurtId()
        return CIdentificationInfoMixin.identify(self, urn)


    def identifyInfoByUrn(self, urn):
        self.getHurtId()
        return CIdentificationInfoMixin.identifyInfoByUrn(self, urn)


    def identifyInfoByUrnList(self, urn):
        self.getHurtId()
        return CIdentificationInfoMixin.identifyInfoByUrnList(self, urn)


    def identifyInfoByCode(self, code):
        self.getHurtId()
        return CIdentificationInfoMixin.identifyInfoByCode(self, code)


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ClientWork_Hurt')
        tableHurtType = db.table('rbHurtType')

        record = db.getRecordEx(table.leftJoin(tableHurtType, tableHurtType['id'].eq(table['hurtType_id'])),
                                [table['id'], tableHurtType['code'], tableHurtType['name'], table['stage']],
                                table['id'].eq(self.clientWorkHurtId))
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._stage = forceInt(record.value('stage'))
            self._factors = self.getInstance(CClientWorkHurtFactorInfoList, forceRef(record.value('id')))
            return True
        else:
            self._code = ''
            self._name = ''
            self._stage = 0
            self._factors = []
            return False


    code  = property(lambda self: self.load()._code)
    name  = property(lambda self: self.load()._name)
    stage = property(lambda self: self.load()._stage)
    factors = property(lambda self: self.load()._factors)

#    def __unicode__(self):
    def __str__(self):
        return self.load()._name


class CClientWorkHurtFactorInfoList(CInfoList):
    def __init__(self, context, hurtId):
        CInfoList.__init__(self, context)
        self.hurtId = hurtId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ClientWork_Hurt_Factor')
        idList = db.getIdList(table, 'id', table['master_id'].eq(self.hurtId), 'id')
        self._items = [ self.getInstance(CClientWorkHurtFactorInfo, id) for id in idList ]


class CClientWorkHurtFactorInfo(CInfo, CIdentificationInfoMixin):
    def __init__(self, context, clientWorkHurtFactorId):
        CInfo.__init__(self, context)
        CIdentificationInfoMixin.__init__(self)
        self.clientWorkHurtFactorId = clientWorkHurtFactorId
        self._code = ''
        self._name = ''
        self.tableName = 'rbHurtFactorType'

    def getHurtFactorId(self):
        if not hasattr(self, 'id'):
            self.id = forceRef(QtGui.qApp.db.translate('ClientWork_Hurt_Factor', 'id', self.clientWorkHurtFactorId, 'factorType_id'))


    def identify(self, urn):
        self.getHurtFactorId()
        return CIdentificationInfoMixin.identify(self, urn)


    def identifyInfoByUrn(self, urn):
        self.getHurtFactorId()
        return CIdentificationInfoMixin.identifyInfoByUrn(self, urn)


    def identifyInfoByCode(self, code):
        self.getHurtFactorId()
        return CIdentificationInfoMixin.identifyInfoByCode(self, code)

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ClientWork_Hurt_Factor')
        tableHurtFactorType = db.table('rbHurtFactorType')
        record = db.getRecordEx(table.leftJoin(tableHurtFactorType, tableHurtFactorType['id'].eq(table['factorType_id'])),
                                [tableHurtFactorType['name'], tableHurtFactorType['code']],
                                table['id'].eq(self.clientWorkHurtFactorId))
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            return True
        return False

#    def __unicode__(self):
    def __str__(self):
        return self.load()._name

    code  = property(lambda self: self.load()._code)
    name  = property(lambda self: self.load()._name)


class CClientAttachInfo(CInfo):
    def __init__(self, context, clientId, temporary):
        CInfo.__init__(self, context)
        self.clientId = clientId
        self.temporary = temporary
        self._document = None


    def _load(self):
        attach = getAttachRecord(self.clientId, self.temporary)
        if attach:
            self._code = attach['code']
            self._name = attach['name']
            self._outcome = attach['outcome']
            self._org = self.getInstance(COrgInfo, attach['LPU_id'])
            self._orgStructure = self.getInstance(COrgStructureInfo, attach['orgStructure_id'])
            self._begDate = CDateInfo(attach['begDate'])
            self._endDate = CDateInfo(attach['endDate'])
            self._document = self.getInstance(CClientDocumentInfo, documentId=attach['document_id'])
            return True
        else:
            self._code = ''
            self._name = ''
            self._outcome = ''
            self._org = self.getInstance(COrgInfo, None)
            self._orgStructure = self.getInstance(COrgStructureInfo, None)
            self._begDate = CDateInfo()
            self._endDate = CDateInfo()
            self._document = None
            return False


    def __str__(self):
        self.load()
        if self._ok:
            result = self._name
            if self._outcome:
                result += ' '+ unicode(self._endDate)
            elif self.temporary:
                result += ' ' + self._org.shortName
                if self._begDate:
                    result += u' c ' + unicode(self._begDate)
                if self.endDate:
                    result += u' по ' + unicode(self._endDate)
            else:
                result += ' ' + self._org.shortName
        else:
            result = ''
        return result

    code    = property(lambda self: self.load()._code)
    name    = property(lambda self: self.load()._name)
    outcome = property(lambda self: self.load()._outcome)
    begDate = property(lambda self: self.load()._begDate)
    endDate = property(lambda self: self.load()._endDate)
    org    = property(lambda self: self.load()._org)
    orgStructure = property(lambda self: self.load()._orgStructure)
    document = property(lambda self: self.load()._document)


class CClientSocStatusInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self.clientId = clientId

    def _load(self):
        idList = getClientSocStatusIds(self.clientId)
        self._items = [ self.getInstance(CClientSocStatusInfo, id) for id in idList ]



class CClientSocStatusInfo(CInfo):
    def __init__(self, context, socStatusId):
        CInfo.__init__(self, context)
        self.socStatusId = socStatusId
        self._code = ''
        self._name = ''
        self._document = None
        self._begDate  = None
        self._endDate  = None
        self._socStatusType  = None
        self._note = ''
        self._classes  = []


    def _load(self):
        db = QtGui.qApp.db
        tableClientSocStatus = db.table('ClientSocStatus')
        tableSocStatusType = db.table('rbSocStatusType')
        record = QtGui.qApp.db.getRecord(tableClientSocStatus.leftJoin(tableSocStatusType,
                                                                       tableSocStatusType['id'].eq(tableClientSocStatus['socStatusType_id'])),
                                         'code, name, document_id, begDate, endDate, socStatusType_id, note, shortName',
                                         self.socStatusId)
#        record = QtGui.qApp.db.getRecord('ClientSocStatus LEFT JOIN rbSocStatusType ON rbSocStatusType.id = ClientSocStatus.socStatusType_id', 'code, name, document_id', self.socStatusId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._shortName = forceString(record.value('shortName'))
            self._document = self.getInstance(CClientDocumentInfo, documentId=forceRef(record.value('document_id')))
            self._begDate = CDateInfo(forceDate(record.value('begDate')))
            self._endDate = CDateInfo(forceDate(record.value('endDate')))
            self._note = forceString(record.value('note'))
            self._classes = self.getInstance(CSocStatusClassInfoList, forceRef(record.value('socStatusType_id')))
            self._socStatusType = self.getInstance(CSocStatusTypeInfo, forceRef(record.value('socStatusType_id')))
            return True
        return False

    code    = property(lambda self: self.load()._code)
    name    = property(lambda self: self.load()._name)
    shortName    = property(lambda self: self.load()._shortName)
    document= property(lambda self: self.load()._document)
    begDate = property(lambda self: self.load()._begDate)
    endDate = property(lambda self: self.load()._endDate)
    note    = property(lambda self: self.load()._note)
    classes = property(lambda self: self.load()._classes)
    socStatusType = property(lambda self: self.load()._socStatusType)

#    def __unicode__(self):
    def __str__(self):
        return self.load()._name


class CSocStatusClassInfoList(CInfoList):
    def __init__(self, context, socStatusTypeId):
        CInfoList.__init__(self, context)
        self.socStatusTypeId = socStatusTypeId


    def _load(self):
        idList = getSocStatusTypeClasses(self.socStatusTypeId)
        self._items = [ self.getInstance(CSocStatusClassInfo, id) for id in idList ]
        
    items = property(lambda self: self.load()._items)


class CSocStatusTypeInfo(CRBInfoWithIdentification):
    tableName = 'rbSocStatusType'

class CSocStatusClassInfo(CInfo):
    def __init__(self, context, socStatusClassId):
        CInfo.__init__(self, context)
        self.socStatusClassId = socStatusClassId
        self._code = ''
        self._name = ''
        self._group = None

    def _load(self):
        record = QtGui.qApp.db.getRecord('rbSocStatusClass', 'code, name, group_id', self.socStatusClassId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            groupId = forceRef(record.value('group_id'))
            self._group = self.getInstance(CSocStatusClassInfo, groupId) if groupId else None
            return True
        return False

    code    = property(lambda self: self.load()._code)
    name    = property(lambda self: self.load()._name)
    group   = property(lambda self: self.load()._group)

#    def __unicode__(self):
    def __str__(self):
        return self.load()._name


    def isPartOf(self, name):
        return self._isPartOf(name.lower(), set([]))


    def _isPartOf(self, name, seen):
        self.load()
        if self._name.lower() == name:
            return True
        if self.socStatusClassId in seen:
            return None
        elif self._group:
            seen.add(self.socStatusClassId)
            return self._group._isPartOf(name, seen)
        else:
            return False


class CClientIntoleranceMedicamentInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self.clientId = clientId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ClientIntoleranceMedicament')
        cond = [ table['client_id'].eq(self.clientId),
                 table['deleted'].eq(0),
               ]
        idList = db.getIdList(table, 'id', cond, 'id')
        self._items = [ self.getInstance(CClientIntoleranceMedicamentInfo, id) for id in idList ]
        return True

class CReactionTypeInfo(CRBInfoWithIdentification):
    tableName = 'rbReactionType'


class CReactionManifestationInfo(CRBInfoWithIdentification):
    tableName = 'rbReactionManifestation'

class CClientIntoleranceMedicamentInfo(CInfo):
    def __init__(self, context, itemId):
        CInfo.__init__(self, context)
        self.itemId = itemId

    def _load(self):
        db = QtGui.qApp.db
        tableIntolerance = db.table('ClientIntoleranceMedicament')
        cols = [ tableIntolerance['activeSubstance_id'],
                 tableIntolerance['power'],
                 tableIntolerance['nameMedicament'],
                 tableIntolerance['reactionType_id'],
                 tableIntolerance['reactionManifestation_id'],
                 tableIntolerance['createDate'],
                 tableIntolerance['notes']
               ]
        cond = [ tableIntolerance['deleted'].eq(0),
                 tableIntolerance['id'].eq(self.itemId),
               ]
        record = db.getRecordEx(tableIntolerance, cols, cond)
        if record:
            self._activeSubstance = self.getInstance(CNomenclatureActiveSubstanceInfo, forceRef(record.value('activeSubstance_id')))
            self._reactionType = self.getInstance(CReactionTypeInfo, forceRef(record.value('reactionType_id')))
            self._reactionManifestation = self.getInstance(CReactionManifestationInfo, forceRef(record.value('reactionManifestation_id')))
            self._power = forceInt(record.value('power'))
            self._date  = CDateInfo(record.value('createDate'))
            self._notes = forceString(record.value('notes'))
            self._name = self._activeSubstance.name if self._activeSubstance else ''
            return True
        else:
            self._activeSubstance = self.getInstance(CNomenclatureActiveSubstanceInfo, None)
            self._reactionType = self.getInstance(CReactionTypeInfo, None)
            self._reactionManifestation = self.getInstance(CReactionManifestationInfo, None)
            self._power = 0
            self._date  = CDateInfo(None)
            self._notes = ''
            self._name = ''
            return False

    activeSubstance  = property(lambda self: self.load()._activeSubstance)
    power = property(lambda self: self.load()._power)
    date  = property(lambda self: self.load()._date)
    notes = property(lambda self: self.load()._notes)
    name = property(lambda self: self.load()._name)
    reactionManifestation = property(lambda self: self.load()._reactionManifestation)
    reactionType = property(lambda self: self.load()._reactionType)

#    def __unicode__(self):
    def __str__(self):
        return self.load()._name


class CClientAllergyInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self.clientId = clientId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ClientAllergy')
        idList = db.getIdList(table, 'id', [table['client_id'].eq(self.clientId),  table['deleted'].eq(0)], 'id')
        self._items = [ self.getInstance(CClientAllergyInfo, id) for id in idList ]
        return True


class CClientAllergyInfo(CInfo):
    def __init__(self, context, itemId):
        CInfo.__init__(self, context)
        self.itemId = itemId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ClientAllergy')
        record = db.getRecord(table, ['nameSubstance', 'power', 'createDate', 'notes', 'reactionType_id', 'reactionManifestation_id'], self.itemId)
        if record:
            self._name  = forceString(record.value('nameSubstance'))
            self._reactionType = self.getInstance(CReactionTypeInfo, forceRef(record.value('reactionType_id')))
            self._reactionManifestation = self.getInstance(CReactionManifestationInfo, forceRef(record.value('reactionManifestation_id')))
            self._power = forceInt(record.value('power'))
            self._date  = CDateInfo(record.value('createDate'))
            self._notes = forceString(record.value('notes'))
            return True
        else:
            self._name  = ''
            self._reactionType = self.getInstance(CReactionTypeInfo, None)
            self._reactionManifestation = self.getInstance(CReactionManifestationInfo, None)
            self._power = 0
            self._date  = CDateInfo(None)
            self._notes = ''
            return False

    name   = property(lambda self: self.load()._name)
    power  = property(lambda self: self.load()._power)
    date   = property(lambda self: self.load()._date)
    notes  = property(lambda self: self.load()._notes)
    reactionManifestation = property(lambda self: self.load()._reactionManifestation)
    reactionType = property(lambda self: self.load()._reactionType)

#    def __unicode__(self):
    def __str__(self):
        return self.load()._name

class CDocumentIdentificationInfo(CInfo):
    def __init__(self, context, masterId):
        CInfo.__init__(self, context)
        self._masterId = masterId
        self._byCode = {}
#        self._byName = {}
        self._nameDict = {}

class CClientIdentificationInfo(CInfo, CDictInfoMixin):
    def __init__(self, context, clientId):
        CInfo.__init__(self, context)
        CDictInfoMixin.__init__(self, '_byCode')
        self._clientId = clientId
        self._nameDict = {}
        self._byUrn = {}


    def _load(self):
        db = QtGui.qApp.db
        tableCI = db.table('ClientIdentification')
        tableAS = db.table('rbAccountingSystem')
        stmt = db.selectStmt(tableCI.leftJoin(tableAS, tableAS['id'].eq(tableCI['accountingSystem_id'])),
                             ['code', 'name', 'identifier', 'checkDate', 'urn'],
                             db.joinAnd([tableCI['client_id'].eq(self._clientId),
                                         tableCI['deleted'].eq(0),
                                        ])
                            )
        query = db.query(stmt)
        while query.next():
            record = query.record()
            code = forceString(record.value('code'))
            name = forceString(record.value('name'))
            urn = forceString(record.value('urn'))
            identifier = forceString(record.value('identifier'))
            self._byUrn[code] = urn
            self._byCode[code] = identifier
            self._nameDict[code] = name
        return True


    def __str__(self):
        self.load()
        l = [ u'%s (%s): %s' % (self._nameDict[code], code, identifier)
              for code, identifier in self._byCode.iteritems()
            ]
        l.sort()
        return ', '.join(l)


    byCode = property(lambda self: self.load()._byCode)
    byUrn = property(lambda self: self.load()._byUrn)
    nameDict = property(lambda self: self.load()._nameDict)



class CClientRelationInfoList(CInfoList):
    def __init__(self, context, clientId, date):
        CInfoList.__init__(self, context)
        self.clientId = clientId
        self.date = date

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ClientRelation')
        directIdList = db.getIdList(table,
                              'id',
                              db.joinAnd([table['deleted'].eq(0),
                                          table['relativeType_id'].isNotNull(),
                                          table['client_id'].eq(self.clientId)
                                         ]),
                              'id')
        reversedIdList = db.getIdList(table,
                              'id',
                              db.joinAnd([table['deleted'].eq(0),
                                          table['relativeType_id'].isNotNull(),
                                          table['relative_id'].eq(self.clientId)
                                         ]),
                              'id')

        self._items = ([ self.getInstance(CClientRelationInfo, id, self.date, True) for id in directIdList ] +
                       [ self.getInstance(CClientRelationInfo, id, self.date, False) for id in reversedIdList ])
        return True


class CClientRelationInfo(CInfo):
    def __init__(self, context, itemId, date=None, isDirect=True):
        CInfo.__init__(self, context)
        self._itemId = itemId
        self._date = date
        self._isDirect = isDirect

    def _load(self):
        db = QtGui.qApp.db
        tableCR = db.table('ClientRelation')
        tableRT = db.table('rbRelationType')
        record = db.getRecord(tableCR.leftJoin(tableRT, tableRT['id'].eq(tableCR['relativeType_id'])),
                              ['client_id', 'relative_id',
                               'leftName', 'rightName',
                               'code', 'relativeType_id',
                               'isDirectGenetic', 'isBackwardGenetic',
                               'isDirectRepresentative', 'isBackwardRepresentative',
                               'isDirectEpidemic', 'isBackwardEpidemic',
                               'isDirectDonation', 'isBackwardDonation',
                               'regionalCode', 'regionalReverseCode'],
                              self._itemId)
        if record:
            leftName = forceString(record.value('leftName'))
            rightName = forceString(record.value('rightName'))
            code = forceString(record.value('code'))
            rbRelationTypeId = forceRef(record.value('relativeType_id'))

            isDirectGenetic = forceBool(record.value('isDirectGenetic'))
            isBackwardGenetic = forceBool(record.value('isBackwardGenetic'))
            isDirectRepresentative = forceBool(record.value('isDirectRepresentative'))
            isBackwardRepresentative = forceBool(record.value('isBackwardRepresentative'))
            isDirectEpidemic = forceBool(record.value('isDirectEpidemic'))
            isBackwardEpidemic = forceBool(record.value('isBackwardEpidemic'))
            isDirectDonation = forceBool(record.value('isDirectDonation'))
            isBackwardDonation = forceBool(record.value('isBackwardDonation'))

            if self._isDirect:
                clientId = forceRef(record.value('relative_id'))
                role, otherRole = leftName, rightName
                regionalCode = forceString(record.value('regionalCode'))
            else:
                clientId = forceRef(record.value('client_id'))
                role, otherRole = rightName, leftName
                regionalCode = forceString(record.value('regionalReverseCode'))
                isDirectGenetic, isBackwardGenetic = isBackwardGenetic, isDirectGenetic
                isDirectRepresentative, isBackwardRepresentative = isBackwardRepresentative, isDirectRepresentative
                isDirectEpidemic, isBackwardEpidemic = isBackwardEpidemic, isDirectEpidemic
                isDirectDonation, isBackwardDonation = isBackwardDonation, isDirectDonation

            self._role = role
            self._otherRole = otherRole
            self._client = self.getInstance(CClientInfo, forceRef(record.value('client_id')), self._date)
            self._relative = self.getInstance(CClientInfo, forceRef(record.value('relative_id')), self._date)
            self._other = self.getInstance(CClientInfo, clientId, self._date)
            self._name = role + ' -> ' + otherRole
            self._code = code
            self._regionalCode = regionalCode
            self._isDirectGenetic = isDirectGenetic
            self._isBackwardGenetic = isBackwardGenetic
            self._isDirectRepresentative = isDirectRepresentative
            self._isBackwardRepresentative = isBackwardRepresentative
            self._isDirectEpidemic = isDirectEpidemic
            self._isBackwardEpidemic = isBackwardEpidemic
            self._isDirectDonation = isDirectDonation
            self._isBackwardDonation = isBackwardDonation
            self._identification = self.getInstance(CRelationTypeIdentificationInfo, rbRelationTypeId)
            return True
        else:
            self._role = ''
            self._otherRole = ''
            self._other = None
            self._client = None
            self._relative = None
            self._name = ''
            self._code = ''
            self._regionalCode = ''
            self._isDirectGenetic = False
            self._isBackwardGenetic = False
            self._isDirectRepresentative = False
            self._isBackwardRepresentative = False
            self._isDirectEpidemic = False
            self._isBackwardEpidemic = False
            self._isDirectDonation = False
            self._isBackwardDonation = False
            self._identification = self.getInstance(CRelationTypeIdentificationInfo, None)
            return False


    role = property(lambda self: self.load()._role)
    otherRole = property(lambda self: self.load()._otherRole)
    other = property(lambda self: self.load()._other)
    client = property(lambda self: self.load()._client)
    relative = property(lambda self: self.load()._relative)
    name = property(lambda self: self.load()._name)
    code = property(lambda self: self.load()._code)
    regionalCode = property(lambda self: self.load()._regionalCode)
    isDirectGenetic = property(lambda self: self.load()._isDirectGenetic)
    isBackwardGenetic = property(lambda self: self.load()._isBackwardGenetic)
    isDirectRepresentative = property(lambda self: self.load()._isDirectRepresentative)
    isBackwardRepresentative = property(lambda self: self.load()._isBackwardRepresentative)
    isDirectEpidemic = property(lambda self: self.load()._isDirectEpidemic)
    isBackwardEpidemic = property(lambda self: self.load()._isBackwardEpidemic)
    isDirectDonation = property(lambda self: self.load()._isDirectDonation)
    isBackwardDonation = property(lambda self: self.load()._isBackwardDonation)
    identification = property(lambda self: self.load()._identification)

    def __str__(self):
        return self.name + ' ' + self.other.fullName


class CRelationTypeIdentificationInfo(CInfo, CDictInfoMixin):
    def __init__(self, context, relationTypeId):
        CInfo.__init__(self, context)
        CDictInfoMixin.__init__(self, '_byCode')
        self._masterId = relationTypeId
        self._nameDict = {}
        self._checkDateDict = {}
        self._byUrn = {}
        self._byCode = {}

    def _load(self):
        db = QtGui.qApp.db
        tableId = db.table('rbRelationType_Identification')
        tableAS = db.table('rbAccountingSystem')
        stmt = db.selectStmt(tableId.innerJoin(tableAS, tableAS['id'].eq(tableId['system_id'])),
                             ['code', 'name', 'value', 'checkDate', 'urn'],
                             db.joinAnd([tableId['master_id'].eq(self._masterId),
                                         tableId['deleted'].eq(0),
                                         ])
                             )
        query = db.query(stmt)
        while query.next():
            record = query.record()
            code = forceString(record.value('code'))
            name = forceString(record.value('name'))
            urn = forceString(record.value('urn'))
            value = forceString(record.value('value'))
            checkDate = forceDate(record.value('checkDate'))
            self._byUrn[code] = urn
            self._byCode[code] = value
            self._nameDict[code] = name
            self._checkDateDict[code] = checkDate
        return True

    def __str__(self):
        self.load()
        l = [u'%s (%s): %s' % (self._nameDict[code], code, value)
             for code, value in self._byCode.iteritems()
             ]
        l.sort()
        return ', '.join(l)

    byCode = property(lambda self: self.load()._byCode)
    byUrn = property(lambda self: self.load()._byUrn)
    nameDict = property(lambda self: self.load()._nameDict)
    checkDateDict = property(lambda self: self.load()._checkDateDict)


class CClientQuotaInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self.clientId = clientId


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Client_Quoting')
        idList = db.getIdList(table,
                              'id',
                              db.joinAnd([table['deleted'].eq(0),
                                          table['master_id'].eq(self.clientId)
                                         ]),
                              'directionDate, id')
        self._items = ([ self.getInstance(CClientQuotaInfo, id) for id in idList ])
        return True


class CQuotaTypeInfo(CRBInfoWithIdentification):
    tableName = 'QuotaType'


    def _initByRecord(self, record):
        self._class = forceInt(record.value('class'))
        self._groupCode = forceString(record.value('group_code'))


    def _initByNull(self):
        self._class = 0
        self._group = ''


    class_ = property(lambda self: self.load()._class)
    group = property(lambda self: self.load()._group)


class CClientQuotaInfo(CInfo):
    def __init__(self, context, itemId):
        CInfo.__init__(self, context)
        self._itemId = itemId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Client_Quoting')
        record = db.getRecord(table, '*', self._itemId)
        if record:
            result = True
        else:
            record = table.newRecord()
            result = False

        self._identifier    = forceString(record.value('identifier'))
        self._ticket        = forceString(record.value('quotaTicket'))
        self._type          = self.getInstance(CQuotaTypeInfo, forceRef(record.value('quotaType_id')))
        self._stage         = forceInt(record.value('stage'))
        self._directionDate = CDateInfo(forceDate(record.value('directionDate')))
        self._freeInput     = forceString(record.value('freeInput'))
        self._org           = self.getInstance(COrgInfo, forceRef(record.value('org_id')))
        self._amount        = forceInt(record.value('amount'))
        self._MKB           = self.getInstance(CMKBInfo, forceString(record.value('MKB')))
        self._status        = forceInt(record.value('status'))
        self._request       = forceInt(record.value('request'))
        self._statement     = forceString(record.value('statment'))
        self._registrationDate = CDateInfo(forceDate(record.value('dateRegistration')))
        self._endDate       = CDateInfo(forceDate(record.value('dateEnd')))
        self._orgStructure  = self.getInstance(COrgStructureInfo, forceRef(record.value('orgStructure_id')))
        self._regionCode    = forceString(record.value('regionCode'))
        self._discussion    = self.getInstance(CQuotaDiscussionInfoList, self._itemId)
        return result

    identifier       = property(lambda self: self.load()._identifier)
    ticket           = property(lambda self: self.load()._ticket)
    type             = property(lambda self: self.load()._type)
    stage            = property(lambda self: self.load()._stage)
    directionDate    = property(lambda self: self.load()._directionDate)
    freeInput        = property(lambda self: self.load()._freeInput)
    org              = property(lambda self: self.load()._org)
    amount           = property(lambda self: self.load()._amount)
    MKB              = property(lambda self: self.load()._MKB)
    status           = property(lambda self: self.load()._status)
    request          = property(lambda self: self.load()._request)
    statement        = property(lambda self: self.load()._statement)
    registrationDate = property(lambda self: self.load()._registrationDate)
    endDate          = property(lambda self: self.load()._endDate)
    orgStructure     = property(lambda self: self.load()._orgStructure)
    regionCode       = property(lambda self: self.load()._regionCode)
    discussion       = property(lambda self: self.load().discussion)

    def __str__(self):
        return self.identifier + ' ' + self.ticket


class CQuotaDiscussionInfoList(CInfoList):
    def __init__(self, context, quotaId):
        CInfoList.__init__(self, context)
        self.quotaId = quotaId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Client_QuotingDiscussion')
        idList = db.getIdList(table, 'id', table['master_id'].eq(self.quotaId), 'id')
        self._items = ([ self.getInstance(CQuotaDiscussionInfo, id) for id in idList ])
        return True


class CQuotaAgreementTypeInfo(CRBInfo):
    tableName = 'rbAgreementType'


class CQuotaDiscussionInfo(CInfo):
    def __init__(self, context, itemId):
        CInfo.__init__(self, context)
        self._itemId = itemId

    def _load(self):

        db = QtGui.qApp.db
        table = db.table('Client_QuotingDiscussion')
        record = db.getRecord(table, '*', self._itemId)
        if record:
            result = True
        else:
            record = table.newRecord()
            result = False
        return result


        self._date = CDateInfo(forceDate(record.value('dateMessage')))
        self._agreementType   = self.getInstance(CQuotaAgreementTypeInfo, forceRef(record.value('agreementType_id')))
        self._person          = self.getInstance(CPersonInfo, forceRef(record.value('responsiblePerson_id')))
        self._cosignatory     = forceString(record.value('cosignatory'))
        self._cosignatoryPost = forceString(record.value('cosignatoryPost'))
        self._cosignatoryName = forceString(record.value('cosignatoryName'))
        self._remark          = forceString(record.value('remark'))


    date             = property(lambda self: self.load()._date)
    agreementType    = property(lambda self: self.load()._agreementType)
    person           = property(lambda self: self.load()._person)
    cosignatory      = property(lambda self: self.load()._cosignatory)
    cosignatoryPost  = property(lambda self: self.load()._cosignatoryPost)
    cosignatoryName  = property(lambda self: self.load()._cosignatoryName)
    remark           = property(lambda self: self.load()._remark)

    def __str__(self):
        return self.date + ' ' + self.remark + ' ' + self.person


class CClientEpidCaseInfo(CInfo):
    def __init__(self, context, clientEpidCaseId):
        CInfo.__init__(self, context)
        self._id = clientEpidCaseId
        self._MKB = ''
        self._number = ''
        self._regDate = CDateInfo(None)
        self._regPerson = self.getInstance(CPersonInfo, None)
        self._endDate = CDateInfo(None)
        self._note = ''

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('Client_EpidCase', '*', self._id)
        if record:
            self._MKB = forceString(record.value('MKB'))
            self._number = forceString(record.value('number'))
            self._regDate = forceDate(record.value('regDate'))
            self._regPerson = self.getInstance(CPersonInfo, forceRef(record.value('regPerson_id')))
            self._endDate = forceDate(record.value('endDate'))
            self._note = forceString(record.value('note'))
            return True
        return False

    id        = property(lambda self: self._id)
    MKB       = property(lambda self: self.load()._MKB)
    number    = property(lambda self: self.load()._number)
    regDate   = property(lambda self: self.load()._regDate)
    regPerson = property(lambda self: self.load()._regPerson)
    endDate   = property(lambda self: self.load()._endDate)
    note      = property(lambda self: self.load()._note)


class CClientEpidCaseInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self._clientId = clientId
        self._items = []

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Client_EpidCase')
        idList = db.getIdList(table, 'id', table['master_id'].eq(self._clientId))
        self._items = [self.getInstance(CClientEpidCaseInfo, id) for id in idList]
        return True


class CClientRiskFactorInfo(CRBRiskFactorInfo):
    def __init__(self, context, id):
        CRBRiskFactorInfo.__init__(self, context, id=0)
        self._clientRiskFactorId = id
        self._MKB = ''
        self._begDate = CDateInfo(None)
        self._endDate = CDateInfo(None)
        self._note = ''
        self._MKB = ''
        self._power = ''

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('ClientRiskFactor', '*', self._clientRiskFactorId)
        if record:
            self.id = forceRef(record.value('riskFactor_id'))
            self._MKB = forceString(record.value('MKB'))
            self._power = forceString(record.value('power'))
            self._note = forceString(record.value('note'))
            self._begDate = CDateInfo(forceDate(record.value('begDate')))
            self._endDate = CDateInfo(forceDate(record.value('endDate')))
            return CRBRiskFactorInfo._load(self)
        return False

    MKB = property(lambda self: self.load()._MKB)
    power = property(lambda self: self.load()._power)
    note = property(lambda self: self.load()._note)
    begDate = property(lambda self: self.load()._begDate)
    endDate = property(lambda self: self.load()._endDate)


class CClientRiskFactorInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self._clientId = clientId
        self._items = []

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ClientRiskFactor')
        idList = db.getIdList(table, 'id', [
            table['client_id'].eq(self._clientId),
            table['deleted'].eq(0),
        ])
        self._items = [self.getInstance(CClientRiskFactorInfo, id) for id in idList]
        return True


class CClientResearchInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self.clientId = clientId

    def _load(self):
        idList = getClientResearchIds(self.clientId)
        self._items = [ self.getInstance(CClientResearchInfo, id) for id in idList ]

class CClientResearchInfo(CInfo):
    def __init__(self, context, researchId):
        CInfo.__init__(self, context)
        self.researchId = researchId
        self._researchKind = None
        self._begDate = QDate()
        self._researchResult = ''
        self._endDate = QDate()
        self._note = ''
        self._createPerson = self.getInstance(CPersonInfo, None)

    def _load(self):
        record = QtGui.qApp.db.getRecord('ClientResearch', 'researchKind_id, begDate, researchResult, endDate, note, createPerson_id', self.researchId)
        if record:
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._researchKind = self.getInstance(CResearchKindInfo, forceRef(record.value('researchKind_id')))
            self._begDate = CDateInfo(forceDate(record.value('begDate')))
            self._researchResult = forceString(record.value('researchResult'))
            self._endDate = CDateInfo(forceDate(record.value('endDate')))
            self._note = forceString(record.value('note'))
            return True
        return False

    createPerson   = property(lambda self: self.load()._createPerson)
    researchKind   = property(lambda self: self.load()._researchKind)
    begDate        = property(lambda self: self.load()._begDate)
    researchResult = property(lambda self: self.load()._researchResult)
    endDate        = property(lambda self: self.load()._endDate)
    note           = property(lambda self: self.load()._note)

    def __str__(self):
        result = self.researchKind.code if self.researchKind else ''
        result += '-' + self.begDate
        if self.endDate.date.isValid():
            result += (' ' + self.endDate)
        return result

class CResearchKindInfo(CInfo):
    def __init__(self, context, researchKindId):
        CInfo.__init__(self, context)
        self.researchKindId = researchKindId
        self._code = ''
        self._name = ''
        self._inClientInfoBrowser = False

    def _load(self):
        record = QtGui.qApp.db.getRecord('rbClientResearchKind', 'code, name, inClientInfoBrowser', self.researchKindId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._inClientInfoBrowser = forceBool(record.value('inClientInfoBrowser'))
            return True
        return False

    code = property(lambda self: self.load()._code)
    name = property(lambda self: self.load()._name)
    inClientInfoBrowser = property(lambda self: self.load()._inClientInfoBrowser)

    def __str__(self):
        return self.load()._name


class CClientActiveDispensaryInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self.clientId = clientId

    def _load(self):
        idList = getClientActiveDispensaryIds(self.clientId)
        self._items = [ self.getInstance(CClientActiveDispensaryInfo, id) for id in idList ]

class CClientActiveDispensaryInfo(CInfo):
    begReasons = [
        u'',
        u'находился на принудительном лечении',
        u'отбывал наказание до псих. заболевания',
        u'инициативное взятие'
    ]
    endReasons = [
        u'',
        u'перемена места жительства',
        u'компенсация',
        u'смерть'
    ]
    behaviorTypes = [
        u'',
        u'убийство',
        u'половые извращения',
        u'поджоги',
        u'хищения',
        u'хулиганские действия',
        u'нанесение телесных повреждений',
        u'др. виды'
    ]

    def __init__(self, context, clientActiveDispensaryId):
        CInfo.__init__(self, context)
        self.clientActiveDispensaryId = clientActiveDispensaryId
        self._begDate = QDate()
        self._begReason = 0
        self._begReasonName = ''
        self._endDate = QDate
        self._endReason = 0
        self._endReasonName = ''
        self._behaviorType = 0
        self._behaviorTypeName = ''
        self._note = ''

    def _load(self):
        record = QtGui.qApp.db.getRecord('ClientActiveDispensary', 'begDate, begReason, endDate, endReason, behaviorType, note', self.clientActiveDispensaryId)
        if record:
            self._begDate = CDateInfo(forceDate(record.value('begDate')))
            self._begReason = forceInt(record.value('begReason'))
            if 0 <= self._begReason < len(CClientActiveDispensaryInfo.begReasons):
                self._begReasonName = CClientActiveDispensaryInfo.begReasons[self._begReason]
            self._endDate = CDateInfo(forceDate(record.value('endDate')))
            self._endReason = forceInt(record.value('endReason'))
            if 0 <= self._endReason < len(CClientActiveDispensaryInfo.endReasons):
                self._endReasonName = CClientActiveDispensaryInfo.endReasons[self._endReason]
            self._behaviorType = forceInt(record.value('behaviorType'))
            if 0 <= self._behaviorType < len(CClientActiveDispensaryInfo.behaviorTypes):
                self._behaviorTypeName = CClientActiveDispensaryInfo.behaviorTypes[self._behaviorType]
            self._note = forceString(record.value('note'))
            return True
        return False

    begDate           = property(lambda self: self.load()._begDate)
    begReason         = property(lambda self: self.load()._begReason)
    begReasonName         = property(lambda self: self.load()._begReasonName)
    endDate           = property(lambda self: self.load()._endDate)
    endReason         = property(lambda self: self.load()._endReason)
    endReasonName         = property(lambda self: self.load()._endReasonName)
    behaviorType      = property(lambda self: self.load()._behaviorType)
    behaviorTypeName      = property(lambda self: self.load()._behaviorTypeName)
    note              = property(lambda self: self.load()._note)

    def __str__(self):
        result = self._treatmentTypeName + ' - ' + self.begDate
        return result

class CClientDangerousInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self.clientId = clientId

    def _load(self):
        idList = getClientDangerousIds(self.clientId)
        self._items = [ self.getInstance(CClientDangerousInfo, id) for id in idList ]

class CClientDangerousInfo(CInfo):
    def __init__(self, context, clientDangerousId):
        CInfo.__init__(self, context)
        self.clientDangerousId = clientDangerousId
        self._date = QDate()
        self._description = ''
        self._judgement = ''
        self._note = ''

    def _load(self):
        record = QtGui.qApp.db.getRecord('ClientDangerous', 'date, description, judgement, note', self.clientDangerousId)
        if record:
            self._date = CDateInfo(forceDate(record.value('date')))
            self._description = forceString(record.value('description'))
            self._judgement = forceString(record.value('judgement'))
            self._note = forceString(record.value('note'))
            return True
        return False

    date        = property(lambda self: self.load()._date)
    description = property(lambda self: self.load()._description)
    judgement   = property(lambda self: self.load()._judgement)
    note        = property(lambda self: self.load()._note)

    def __str__(self):
        result = self.date + ' - ' + self.description
        return result


class CClientForcedTreatmentInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self.clientId = clientId

    def _load(self):
        idList = getClientForcedTreatmentIds(self.clientId)
        self._items = [ self.getInstance(CClientForcedTreatmentInfo, id) for id in idList ]

class CClientForcedTreatmentInfo(CInfo):
    treatmentTypes = [
        u'',
        u'амбулаторное',
        u'в психиатр. стационаре общего типа',
        u'в психиатр. стационаре спец. типа',
        u'в психиатр. стационаре спец. типа с интенсив. наблюдением'
    ]
    statuses = [
        u'',
        u'лечение завершено',
        u'лечение прервано'
    ]
    endReasons = [
        u'',
        u'выезд',
        u'смерть',
        u'по суду'
    ]

    def __init__(self, context, clientForcedTreatmentId):
        CInfo.__init__(self, context)
        self.clientForcedTreatmentId = clientForcedTreatmentId
        self._begDate = QDate()
        self._judgement = ''
        self._treatmentType = 0
        self._treatmentTypeName = ''
        self._dispDate = QDate()
        self._mcNextDate = QDate()
        self._mcLastDate = QDate()
        self._endDate = QDate()
        self._endReason = 0
        self._endReasonName = ''
        self._dispEndDate = QDate()
        self._continueDate = QDate()
        self._statBegDate = QDate()
        self._statEndDate = QDate()

    def _load(self):
        record = QtGui.qApp.db.getRecord('ClientForcedTreatment', 'judgement, treatmentType, begDate, endDate, status, note', self.clientForcedTreatmentId)
        if record:
            self._begDate = CDateInfo(forceDate(record.value('begDate')))
            self._judgement = forceString(record.value('judgement'))
            self._treatmentType = forceInt(record.value('treatmentType'))
            if 0 <= self._treatmentType < len(CClientForcedTreatmentInfo.treatmentTypes):
                self._treatmentTypeName = CClientForcedTreatmentInfo.treatmentTypes[self._treatmentType]
            self._dispDate = CDateInfo(forceDate(record.value('dispDate')))
            self._mcNextDate = CDateInfo(forceDate(record.value('mcNextDate')))
            self._mcLastDate = CDateInfo(forceDate(record.value('mcLastDate')))
            self._endDate = CDateInfo(forceDate(record.value('endDate')))
            self._endReason = forceInt(record.value('endReason'))
            if 0 <= self._endReason < len(CClientForcedTreatmentInfo.endReasons):
                self._endReasonName = CClientForcedTreatmentInfo.endReasons[self._endReason]
            self._dispEndDate = CDateInfo(forceDate(record.value('dispEndDate')))
            self._continueDate = CDateInfo(forceDate(record.value('continueDate')))
            self._statBegDate = CDateInfo(forceDate(record.value('statBegDate')))
            self._statEndDate = CDateInfo(forceDate(record.value('statEndDate')))
            return True
        return False

    judgement         = property(lambda self: self.load()._judgement)
    begDate           = property(lambda self: self.load()._begDate)
    treatmentType     = property(lambda self: self.load()._treatmentType)
    treatmentTypeName = property(lambda self: self.load()._treatmentTypeName)
    dispDate          = property(lambda self: self.load()._dispDate)
    mcNextDate        = property(lambda self: self.load()._mcNextDate)
    mcLastDate        = property(lambda self: self.load()._mcLastDate)
    endDate           = property(lambda self: self.load()._endDate)
    endReason         = property(lambda self: self.load()._endReason)
    endReasonName     = property(lambda self: self.load()._endReasonName)
    dispEndDate       = property(lambda self: self.load()._dispEndDate)
    continueDate      = property(lambda self: self.load()._continueDate)
    statBegDate       = property(lambda self: self.load()._statBegDate)
    statEndDate       = property(lambda self: self.load()._statEndDate)

    def __str__(self):
        result = self._treatmentTypeName + ' - ' + self.begDate
        return result


class CClientSuicideInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self.clientId = clientId

    def _load(self):
        idList = getClientSuicideIds(self.clientId)
        self._items = [ self.getInstance(CClientSuicideInfo, id) for id in idList ]

class CClientSuicideInfo(CInfo):
    statusTypes = [u'', u'суицидальный риск', u'суицид']

    def __init__(self, context, clientSuicideId):
        CInfo.__init__(self, context)
        self.clientSuicideId = clientSuicideId
        self._date = QDate()
        self._statusType = 0
        self._statusTypeName = ''
        self._statusCondition = ''
        self._description = ''
        self._note = ''

    def _load(self):
        record = QtGui.qApp.db.getRecord('ClientSuicide', 'date, statusType, statusCondition, description, note', self.clientSuicideId)
        if record:
            self._date = CDateInfo(forceDate(record.value('date')))
            self._statusType = forceInt(record.value('statusType'))
            if 0 <= self._statusType < len(CClientSuicideInfo.statusTypes):
                self._statusTypeName = CClientSuicideInfo.statusTypes[self._statusType]
            self._statusCondition = forceString(record.value('statusCondition'))
            self._description = forceString(record.value('description'))
            self._note = forceString(record.value('note'))
            return True
        return False

    date            = property(lambda self: self.load()._date)
    statusType      = property(lambda self: self.load()._statusType)
    statusTypeName  = property(lambda self: self.load()._statusTypeName)
    statusCondition = property(lambda self: self.load()._statusCondition)
    description     = property(lambda self: self.load()._description)
    note            = property(lambda self: self.load()._note)

    def __str__(self):
        result = self.date + ' - ' + self._statusTypeName + ' ' + self._statusCondition
        return result


class CClientContingentKindInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self.clientId = clientId

    def _load(self):
        idList = getClientContingentKindIds(self.clientId)
        self._items = [ self.getInstance(CClientContingentKindInfo, id) for id in idList ]

class CClientContingentKindInfo(CInfo):
    reasons = [
        u'',
        u'1 - стойкая ремиссия/выздоровление',
        u'2 - смена места жительства',
        u'3 - неявка более 12 мес',
        u'4 - лишение свободы более 12 мес',
        u'5 - смена контингента',
        u'6 - смерть',
        u'7 - по заявлению'
    ]

    def __init__(self, context, clientContingentKindId):
        CInfo.__init__(self, context)
        self.clientContingentKindId = clientContingentKindId
        self._contingentKind = None
        self._begDate = QDate()
        self._endDate = QDate()
        self._reason = 0
        self._reasonName = ''
        self._speciality = None
        self._org = None
        self._MKB = None
        self._note = ''

    def _load(self):
        record = QtGui.qApp.db.getRecord('ClientContingentKind', 'contingentKind_id, begDate, endDate, contingentKindRemoval_id, speciality_id, org_id, MKB, note', self.clientContingentKindId)
        if record:
            self._contingentKind = self.getInstance(CContingentKindInfo, forceRef(record.value('contingentKind_id')))
            self._begDate = CDateInfo(forceDate(record.value('begDate')))
            self._endDate = CDateInfo(forceDate(record.value('endDate')))
            self._reason = forceInt(record.value('contingentKindRemoval_id'))
            if 0 <= self._reason < len(CClientContingentKindInfo.reasons):
                self._reasonName = CClientContingentKindInfo.reasons[self._reason]
            self._speciality = self.getInstance(CSpecialityInfo, forceRef(record.value('speciality_id')))
            self._org = self.getInstance(COrgInfo, forceRef(record.value('org_id')))
            self._MKB = self.getInstance(CMKBInfo, forceString(record.value('MKB')))
            self._note = forceString(record.value('note'))
            return True
        return False

    contingentKind = property(lambda self: self.load()._contingentKind)
    begDate        = property(lambda self: self.load()._begDate)
    endDate        = property(lambda self: self.load()._endDate)
    reason         = property(lambda self: self.load()._reason)
    reasonName     = property(lambda self: self.load()._reasonName)
    speciality     = property(lambda self: self.load()._speciality)
    org            = property(lambda self: self.load()._org)
    MKB            = property(lambda self: self.load()._MKB)
    note           = property(lambda self: self.load()._note)

    def __str__(self):
        result = self.contingentKind.code if self.contingentKind else ''
        result += '-' + self.begDate
        if self.endDate:
            result += (' ' + self.endDate)
        return result

class CContingentKindInfo(CInfo):
    def __init__(self, context, contingentKindId):
        CInfo.__init__(self, context)
        self.contingentKindId = contingentKindId
        self._code = ''
        self._name = ''

    def _load(self):
        record = QtGui.qApp.db.getRecord('rbContingentKind', 'code, name', self.contingentKindId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            return True
        return False

    code = property(lambda self: self.load()._code)
    name = property(lambda self: self.load()._name)

    def __str__(self):
        return self.load()._name


def getClientInfo2(id, date=None):
    context = CInfoContext()
    return CClientInfo(context, id, date)


def fixClientDeath(clientId, deathDate, fixDeathDate, orgId):
    db = QtGui.qApp.db
    tableClient = db.table('Client')
    record = db.getRecord(tableClient, 'id, deathDate', clientId)
    if record:
        record.setValue('deathDate', toVariant(fixDeathDate))
        db.updateRecord(tableClient, record)


#### Какой-то бардак с ClientIdentifier: то systemId, то code, то name :(((

#### вот тут - accountingSystemId
def getClientIdentifier(accountingSystemId, clientId):
    record = selectLatestRecord('ClientIdentification', clientId, filter='accountingSystem_id=%d' % accountingSystemId)
    if record:
        return forceString(record.value('identifier'))
    return ''

#### вот тут - name
def getClientIdentifications(clientId):
    result = {}
    stmt = """
    SELECT r.name, ci.identifier, ci.checkDate
    FROM ClientIdentification ci
    LEFT JOIN rbAccountingSystem r ON r.id = ci.accountingSystem_id
    WHERE ci.deleted = 0 AND ci.client_id = %s
        AND r.showInClientInfo = 1
    """ % clientId
    db = QtGui.qApp.db
    query = db.query(stmt)
    while query.next():
        r = query.record()
        if r:
            result[forceString(r.value(0))] = (forceString(r.value(1)), forceDate(r.value(2)))
    return result


def getClientIdentificationBySystemId(accountingSystemId, clientId):
    db = QtGui.qApp.db
    tableClientIdentification = db.table('ClientIdentification')
    record = db.getRecordEx(tableClientIdentification,
                            'client_id, identifier',
                            [tableClientIdentification['deleted'].eq(0),
                             tableClientIdentification['accountingSystem_id'].eq(accountingSystemId),
                             tableClientIdentification['client_id'].eq(clientId),
                            ],
                            'id desc'
                           )
    return forceString(record.value('identifier')) if record else None


def findClientByIdentificationBySystemId(accountingSystemId, value):
    db = QtGui.qApp.db
    tableClientIdentification = db.table('ClientIdentification')
    record = db.getRecordEx(tableClientIdentification,
                            'client_id',
                            [tableClientIdentification['deleted'].eq(0),
                             tableClientIdentification['accountingSystem_id'].eq(accountingSystemId),
                             tableClientIdentification['identifier'].eq(value),
                            ],
                            'id desc'
                           )
    return forceRef(record.value('client_id')) if record else None


def setClientIdentificationBySystemId(clientId, accountingSystemId, value):
    if not clientId:
        return
    db = QtGui.qApp.db
    tableClientIdentification = db.table('ClientIdentification')
    record = db.getRecordEx(tableClientIdentification,
                            '*',
                            [tableClientIdentification['deleted'].eq(0),
                             tableClientIdentification['client_id'].eq(clientId),
                             tableClientIdentification['accountingSystem_id'].eq(accountingSystemId),
                            ],
                            'id desc'
                           )
    if record is None:
        record = tableClientIdentification.newRecord()
        record.setValue('client_id',           clientId)
        record.setValue('accountingSystem_id', accountingSystemId)

    record.setValue('identifier', value)
    record.setValue('checkDate', QDate.currentDate())
    db.insertOrUpdate(tableClientIdentification, record)

#### вот тут - code
def getClientIdentification(code, clientId):
    db = QtGui.qApp.db
    accountingSystemId = forceRef(db.translate('rbAccountingSystem', 'code', code, 'id'))
    if accountingSystemId is None:
        raise Exception(u'В справочнике rbAccountingSystem не найдена запись с кодом «%s»' % code)
    return getClientIdentificationBySystemId(accountingSystemId, clientId)


def findClientByIdentification(code, value):
    db = QtGui.qApp.db
    accountingSystemId = forceRef(db.translate('rbAccountingSystem', 'code', code, 'id'))
    if accountingSystemId is None:
        raise Exception(u'В справочнике rbAccountingSystem не найдена запись с кодом «%s»' % code)
    return findClientByIdentificationBySystemId(accountingSystemId, value)


def setClientIdentification(clientId, code, value):
    if not clientId:
        return
    db = QtGui.qApp.db
    accountingSystemId = forceRef(db.translate('rbAccountingSystem', 'code', code, 'id'))
    if accountingSystemId is None:
        raise Exception(u'В справочнике rbAccountingSystem не найдена запись с кодом «%s»' % code)
    setClientIdentificationBySystemId(clientId, accountingSystemId, value)



def findKLADRRegionRecordsInQuoting(code, quotingRecord):
    def getValueFromRecords(records):
        res = []
        for rec in records:
            res.append(forceString(rec.value('region_code')))
        return res
    def appendCode(list, code, codesList, recordsList):
        if code in codesList:
            x = codesList.index(code)
            list.append(recordsList[x])
    db = QtGui.qApp.db
    model = getKladrTreeModel()
    item = model.getRootItem().findCode(code)
    quotingId = forceInt(quotingRecord.value('id'))
    cond = 'Quoting_Region.`master_id`=%d AND Quoting_Region.`deleted`=0'%quotingId
    quotingRegionRecords = db.getRecordList('Quoting_Region', '*', cond)
    codesList = getValueFromRecords(quotingRegionRecords)
    resumeList = []
    appendCode(resumeList, code, codesList, quotingRegionRecords)
    item = item.parent()
    while item:
        code = item._code
        appendCode(resumeList, code, codesList, quotingRegionRecords)
        item = item.parent()
    return resumeList


def findDistrictRecordsInQuoting(codes, quotingRecord):
    def getValueFromRecords(records):
        res = []
        for rec in records:
            res.append((forceString(rec.value('region_code')), forceString(rec.value('district_code'))))
        return res
    def appendCode(list, codes, codesList, recordsList):
        if codes in codesList:
            x = codesList.index(codes)
            list.append(recordsList[x])
    db = QtGui.qApp.db
    quotingId = forceInt(quotingRecord.value('id'))
    cond = 'Quoting_District.`master_id`=%d AND Quoting_District.`deleted`=0'%quotingId
    quotingRegionRecords = db.getRecordList('Quoting_District', '*', cond)
    codesList = getValueFromRecords(quotingRegionRecords)
    resumeList = []
    appendCode(resumeList, codes, codesList, quotingRegionRecords)
    return resumeList

# ############################################################################

def uniqueIdentifierCheckingIsPassed(currentItemId, accountingSystemId, newIdentifier):
    db = QtGui.qApp.db
    table = db.table('ClientIdentification')
    cond = [table['accountingSystem_id'].eq(accountingSystemId),
            table['identifier'].eq(newIdentifier)]
    if currentItemId:
        cond.append(table['id'].ne(currentItemId))
    record = db.getRecordEx(table, 'id', cond)
    if record:
        QtGui.QMessageBox.warning(QtGui.qApp.mainWindow, u'Изменение идентификатора',
            u'В выбранной учётной системе требуется ввод уникального удентификатора.\n\'%s\' не уникален'%newIdentifier,
            QtGui.QMessageBox.Close)
        return False
    return True


# ######################################################################################

class CPolicyKindCache(CDbEntityCache):
    mapIdToCode = {}

    @classmethod
    def purge(cls):
        cls.mapIdToCode.clear()


    @classmethod
    def getCode(cls, id):
        result = cls.mapIdToCode.get(id, False)
        if result == False:
            cls.connect()
            result = forceString(QtGui.qApp.db.translate('rbPolicyKind', 'id', id, 'code'))
            cls.mapIdToCode[id] = result
        return result


class CAppointmentPurposeCache(CDbEntityCache):
    mapIdToItem = {}

    class CAppointmentPurpose(CSexAgeConstraint):
        def __init__(self, record):
            CSexAgeConstraint.__init__(self)
            CSexAgeConstraint.initByRecord(self, record)
            self.code = forceString(record.value('code'))
            self.name = forceString(record.value('name'))
            self.enablePrimaryRecord     = forceBool(record.value('enablePrimaryRecord'))
            self.enableOwnRecord         = forceBool(record.value('enableOwnRecord'))
            self.enableConsultancyRecord = forceBool(record.value('enableConsultancyRecord'))
            self.enableRecordViaInfomat  = forceBool(record.value('enableRecordViaInfomat'))
            self.enableRecordViaCallCenter=forceBool(record.value('enableRecordViaCallCenter'))
            self.enableRecordViaInternet = forceBool(record.value('enableRecordViaInternet'))
            self.requireReferral         = forceBool(record.value('requireReferral'))


    @classmethod
    def purge(cls):
        cls.mapIdToItem.clear()


    @classmethod
    def getItem(cls, id):
        result = cls.mapIdToItem.get(id, False) if id is not None else None
        if result == False:
            cls.connect()
            record = QtGui.qApp.db.getRecord('rbAppointmentPurpose', '*', id)
            result = CAppointmentPurposeCache.CAppointmentPurpose(record) if record is not None else None
            cls.mapIdToItem[id] = result
        return result


    @classmethod
    def getName(cls, id):
        item = cls.getItem(id)
        return item.name if item else ''



class CSocStatusTypeCache(CDbEntityCache):
    mapIdToCode = {}
    mapIdToName = {}


    @classmethod
    def purge(cls):
        cls.mapIdToCode.clear()
        cls.mapIdToName.clear()


    @classmethod
    def register(cls, id):
        cls.connect()
        record = QtGui.qApp.db.getRecord('rbSocStatusType', ['code', 'name'], id)
        if record:
            code = forceString(record.value(0))
            name = forceString(record.value(1))
        else:
            code = name = 'Соц.статус {%r}' % id
        cls.mapIdToCode[id] = code
        cls.mapIdToName[id] = name
        return code, name


    @classmethod
    def getCode(cls, id):
        result = cls.mapIdToCode.get(id, False)
        if result == False:
            result, name = cls.register(id)
        return result


    @classmethod
    def getName(cls, id):
        result = cls.mapIdToName.get(id, False)
        if result == False:
            code, result = cls.register(id)
        return result

# #####################################################

def canRemoveEventWithTissue():
    widget = QtGui.qApp.mainWindow
    hasRight = QtGui.qApp.userHasRight(urDeleteEventWithTissue)
    if hasRight:
        mbResult = QtGui.QMessageBox.question(widget,
                                            u'Внимание!',
                                            u'В событии присутствуют действия связанные с забором биометериалов.\nУдалить?',
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                            QtGui.QMessageBox.No)
        result = mbResult == QtGui.QMessageBox.Yes
    else:
        result = False
        QtGui.QMessageBox.warning(widget,
                                  u'Внимание!',
                                  u'В событии присутствуют действия связанные с забором биометериалов.\nУ вас нет прав на удаление',
                                  QtGui.QMessageBox.Ok)
    return result


def canRemoveEventWithJobTicket():
    widget = QtGui.qApp.mainWindow
    hasRight = QtGui.qApp.userHasRight(urDeleteEventWithJobTicket)
    if hasRight:
        mbResult = QtGui.QMessageBox.question(widget,
                                            u'Внимание!',
                                            u'В событии присутствуют действия связанные с номерком на Работу.\nУдалить?',
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                            QtGui.QMessageBox.No)
        result = mbResult == QtGui.QMessageBox.Yes
    else:
        result = False
        QtGui.QMessageBox.warning(widget,
                                  u'Внимание!',
                                  u'В событии присутствуют действия связанные с номерком на Работу.\nУ вас нет прав на удаление',
                                  QtGui.QMessageBox.Ok)
    return result

# ########################################################################################


class CClientRelationComboBoxForConsents(QtGui.QComboBox):
    def __init__(self, parent=None):
        QtGui.QComboBox.__init__(self, parent)
        self._clientId = None


    def setClientId(self, clientId):
        self._clientId = clientId
        db = QtGui.qApp.db
        tableCR = db.table('ClientRelation')
        tableRT = db.table('rbRelationType')
        tableC  = db.table('Client')

        clientRecord = db.getRecord(tableC, 'lastName, firstName, patrName, birthDate', clientId)
        if clientRecord:
            name = formatShortName(clientRecord.value('lastName'),
                                   clientRecord.value('firstName'),
                                   clientRecord.value('patrName'))
            itemText = u', '.join([name, forceString(clientRecord.value('birthDate'))])
            self.addItem(itemText, QVariant(clientId))
        else:
            self.addItem(u'Неправильные данные!', QVariant())

        queryTable = tableCR
        queryTable = queryTable.leftJoin(tableRT, tableRT['id'].eq(tableCR['relativeType_id']))
        queryTable = queryTable.leftJoin(tableC, tableC['id'].eq(tableCR['relative_id']))

        cond = [tableCR['client_id'].eq(clientId), tableCR['deleted'].eq(0)]
        fields = ['CONCAT_WS(\' | \', rbRelationType.`code`, CONCAT_WS(\'->\', rbRelationType.`leftName`, rbRelationType.`rightName`)) AS relationType',
                  tableC['lastName'].alias(), tableC['firstName'].name(),
                  tableC['patrName'].name(), tableC['birthDate'].name(),
                  tableC['id'].alias('relativeId')]
        records = db.getRecordList(queryTable, fields, cond)
        for record in records:
            name = formatShortName(record.value('lastName'),
                                   record.value('firstName'),
                                   record.value('patrName'))
            itemText = u', '.join([name,
                                  forceString(record.value('birthDate')),
                                  forceString(record.value('relationType'))])
            relativeId = forceRef(record.value('relativeId'))
            self.addItem(itemText, QVariant(relativeId))

        queryTable = tableCR
        queryTable = queryTable.leftJoin(tableRT, tableRT['id'].eq(tableCR['relativeType_id']))
        queryTable = queryTable.leftJoin(tableC, tableC['id'].eq(tableCR['client_id']))

        cond = [tableCR['relative_id'].eq(clientId), tableCR['deleted'].eq(0)]
        fields = ['CONCAT_WS(\' | \', rbRelationType.`code`, CONCAT_WS(\'->\', rbRelationType.`rightName`, rbRelationType.`leftName`)) AS relationType',
                  tableC['lastName'].alias(), tableC['firstName'].name(),
                  tableC['patrName'].name(), tableC['birthDate'].name(),
                  tableC['id'].alias('relativeId')]
        records = db.getRecordList(queryTable, fields, cond)
        for record in records:
            name = formatShortName(record.value('lastName'),
                                   record.value('firstName'),
                                   record.value('patrName'))
            itemText = u', '.join([name,
                                  forceString(record.value('birthDate')),
                                  forceString(record.value('relationType'))])
            relativeId = forceRef(record.value('relativeId'))
            self.addItem(itemText, QVariant(relativeId))


    def value(self):
        currIndex = self.currentIndex()
        representerClientId = forceRef(self.itemData(currIndex))
        if representerClientId:
            return representerClientId
        return self._clientId


    def setValue(self, clientId):
        index = self.findData(QVariant(clientId))
        self.setCurrentIndex(index)


class CClientRelationComboBoxPatron(CROComboBox):
    def __init__(self, parent=None):
        CROComboBox.__init__(self, parent)
        self._clientId = None


    def setClientId(self, clientId):
        self._clientId = clientId
        self.addItem(u'не задано', QVariant(None))
        db = QtGui.qApp.db
        tableCR = db.table('ClientRelation')
        self.addPatronItem(db, tableCR, 'relative_id', 'relativeId', [tableCR['client_id'].eq(clientId), tableCR['deleted'].eq(0)])
        self.addPatronItem(db, tableCR, 'client_id', 'clientId', [tableCR['relative_id'].eq(clientId), tableCR['deleted'].eq(0)])


    def addPatronItem(self, db, tableCR, colRelative, colFields, cond):
        tableRT = db.table('rbRelationType')
        tableC  = db.table('Client')
        queryTable = tableCR
        queryTable = queryTable.leftJoin(tableRT, tableRT['id'].eq(tableCR['relativeType_id']))
        queryTable = queryTable.leftJoin(tableC, tableC['id'].eq(tableCR[colRelative]))

        fields = ['CONCAT_WS(\' | \', rbRelationType.`code`, CONCAT_WS(\'->\', rbRelationType.`leftName`, rbRelationType.`rightName`)) AS relationType',
                  tableC['lastName'].alias(), tableC['firstName'].name(),
                  tableC['patrName'].name(), tableC['birthDate'].name(),
                  tableC['id'].alias(colFields)]
        cond.append(tableCR['deleted'].eq(0))
        clientRelationRecordList = db.getRecordList(queryTable, fields, cond)
        for relationRecord in clientRelationRecordList:
            name = formatShortName(relationRecord.value('lastName'),
                                   relationRecord.value('firstName'),
                                   relationRecord.value('patrName'))
            itemText = u', '.join([name,
                                  forceString(relationRecord.value('birthDate')),
                                  forceString(relationRecord.value('relationType'))])
            relativeId = forceRef(relationRecord.value(colFields))
            self.addItem(itemText, QVariant(relativeId))


    def value(self):
        currIndex = self.currentIndex()
        representerClientId = forceRef(self.itemData(currIndex))
        if representerClientId:
            return representerClientId
        return None


    def setValue(self, clientId):
        index = self.findData(QVariant(clientId))
        self.setCurrentIndex(index)


class CClientRelationComboBoxPatronEx(CROComboBox):
    def __init__(self, parent=None):
        CROComboBox.__init__(self, parent)
        self._clientId = None
        self.clientRelationDict = {}


    def setClientId(self, clientId):
        self.clientRelationDict = {}
        self._clientId = clientId
        self.addItem(u'не задано', QVariant(None))
        db = QtGui.qApp.db
        tableCR = db.table('ClientRelation')
        self.addPatronItem(db, tableCR, 'relative_id', 'relativeId', [tableCR['client_id'].eq(clientId), tableCR['deleted'].eq(0)])
        self.addPatronItem(db, tableCR, 'client_id', 'clientId', [tableCR['relative_id'].eq(clientId), tableCR['deleted'].eq(0)])


    def addPatronItem(self, db, tableCR, colRelative, colFields, cond):
        tableRT = db.table('rbRelationType')
        tableC  = db.table('Client')
        queryTable = tableCR
        queryTable = queryTable.leftJoin(tableRT, tableRT['id'].eq(tableCR['relativeType_id']))
        queryTable = queryTable.leftJoin(tableC, tableC['id'].eq(tableCR[colRelative]))

        fields = ['CONCAT_WS(\' | \', rbRelationType.code, CONCAT_WS(\'->\', rbRelationType.leftName, rbRelationType.rightName)) AS relationType',
                  tableC['lastName'].alias(), tableC['firstName'].name(),
                  tableC['patrName'].name(), tableC['birthDate'].name(),
                  tableCR['id'].alias(colFields),
                  tableCR['client_id'], tableCR['relative_id']]
        clientRelationRecordList = db.getRecordList(queryTable, fields, cond)
        for relationRecord in clientRelationRecordList:
            name = formatShortName(relationRecord.value('lastName'),
                                   relationRecord.value('firstName'),
                                   relationRecord.value('patrName'))
            itemText = u', '.join([name,
                                  forceString(relationRecord.value('birthDate')),
                                  forceString(relationRecord.value('relationType'))])
            relativeId = forceRef(relationRecord.value(colFields))
            if relativeId and relativeId not in self.clientRelationDict.keys():
                crClientId = forceRef(relationRecord.value('client_id'))
                crRelativeId = forceRef(relationRecord.value('relative_id'))
                if colRelative == u'relative_id':
                    self.clientRelationDict[relativeId] = (crClientId, crRelativeId)
                elif colRelative == u'client_id':
                    self.clientRelationDict[relativeId] = (crRelativeId, crClientId)
            self.addItem(itemText, QVariant(relativeId))


    def value(self):
        currIndex = self.currentIndex()
        representerClientId = forceRef(self.itemData(currIndex))
        if representerClientId:
            return representerClientId
        return None


    def setValue(self, clientId):
        index = self.findData(QVariant(clientId))
        self.setCurrentIndex(index)


    def getClientId(self, clientRelationId):
        if clientRelationId:
            clientRelationLine = self.clientRelationDict.get(clientRelationId, (None, None))
            return clientRelationLine[0]
        return None


    def getRelativeId(self, clientRelationId):
        if clientRelationId:
            clientRelationLine = self.clientRelationDict.get(clientRelationId, (None, None))
            return clientRelationLine[1]
        return None


def getHousesList(records):
    numberList = {}
    for record in records:
        name = forceString(record.value('NAME'))
        korp = forceString(record.value('KORP'))
        #code = forceString(record.value('CODE'))
        flatHouseList = forceString(record.value('flatHouseList'))
        korpList = []
        nameList = name.split(',')
        notNameCorp = True
        if len(nameList) == 1 and korp:
            nameList = name.split('-')
            if len(nameList) == 1:
                notNameCorp = False
                if korp:
                    korpList = korp.split(',')
                korpListOld = numberList.get(unicode(nameList[0]), [])
                for corp in korpList:
                    if corp and corp not in korpListOld:
                        korpListOld.append(corp)
                if not korpListOld:
                    korpListOld.append(u'')
                korpListOld.sort()
                numberList[unicode(nameList[0])] = korpListOld
        if notNameCorp:
            nameList = flatHouseList.split(',')
            for number in nameList:
                i = 0
                house = []
                korp = []
                target = house
                while i < len( number ):
                    # if number[i] >= u'А' and number[i] <= u'Я' and i > 0:
                    #     korp.append(number[i])
                    # el
                    if number[i] == u'к':
                        target=korp
                    elif number[i] == u'л' and number[i:i+5] == u'литер':
                        target = korp
                        i += 4
                    else:
                        target.append(number[i])
                    i += 1
                houseStr = u''.join(house)
                korpStr = u''.join(korp)
                korpListOld = numberList.get(houseStr, [])
                if korpStr not in korpListOld:
                    korpListOld.append(korpStr)
                korpListOld.sort()
                numberList[houseStr] = korpListOld
    return numberList


# ######################################################


class CDbSearchWidget(QtGui.QWidget):
    class CLineEdit(QtGui.QLineEdit):
        def __init__(self, parent = None):
            QtGui.QLineEdit.__init__(self, parent)

        def keyPressEvent(self, event):
            key = event.key()
            if key == Qt.Key_Down:
                self.emit(SIGNAL('downKeyPressed()'))
            elif key == Qt.Key_Up:
                self.emit(SIGNAL('upKeyPressed()'))
            elif key == Qt.Key_Enter or key == Qt.Key_Return:
                self.emit(SIGNAL('enterKeyPressed()'))
            else:
                QtGui.QLineEdit.keyPressEvent(self, event)


    class CListView(QtGui.QListView):
        def __init__(self, parent = None):
            QtGui.QListView.__init__(self, parent)

        def keyPressEvent(self, event):
            key = event.key()
            if key == Qt.Key_Enter or key == Qt.Key_Return:
                self.emit(SIGNAL('enterKeyPressed()'))
            else:
                QtGui.QListView.keyPressEvent(self, event)

    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.setMinimumHeight(200)
        self.lineEdit = CDbSearchWidget.CLineEdit()
        self.connect(self.lineEdit, SIGNAL('downKeyPressed()'), self.on_downKeyPress)
        self.connect(self.lineEdit, SIGNAL('upKeyPressed()'), self.on_upKeyPressed)
        self.connect(self.lineEdit, SIGNAL('enterKeyPressed()'), self.on_enterKeyPressed)
        self.connect(self.lineEdit, SIGNAL('textEdited(QString)'), self.on_textEdited)

        self.view = CDbSearchWidget.CListView(self)
        self.connect(self.view, SIGNAL('enterKeyPressed()'), self.on_enterKeyPressed)
        self.connect(self.view, SIGNAL('activated(QModelIndex)'), self.on_activated)

        lv = QtGui.QVBoxLayout(self)
        lv.setSpacing(0)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.addWidget(self.lineEdit)
        lv.addWidget(self.view)

        self.sourceModel = None
        self.proxy = QtGui.QSortFilterProxyModel()
        self.proxy.setFilterCaseSensitivity(0)
        self.setFocusProxy(self.lineEdit)


    def setModel(self, model):
        self.sourceModel = model
        self.proxy.setSourceModel(self.sourceModel)
        self.view.setModel(self.proxy)
        index = self.proxy.index(0, 0)
        self.view.setCurrentIndex(index)


    def setTable(self, tableName, addNone=True, filter=None):
        model = CDbModel(self)
        model.setAddNone(addNone)
        model.setFilter(filter)
        model.setTable(tableName)
        self.setModel(model)


    def on_textEdited(self, text):
        self.proxy.setFilterFixedString(text)
        index = self.proxy.index(0, 0)
        self.view.setCurrentIndex(index)
        if self.view.isHidden():
            self.view.show()


    def on_activated(self, index):
        self.lineEdit.setText(self.proxy.data(index).toString())
        self.close()


    def on_upKeyPressed(self):
        index = self.view.currentIndex()
        new_index = index.sibling(index.row()-1, 0)
        if new_index.isValid():
            self.view.setCurrentIndex(new_index)


    def on_downKeyPress(self):
        if self.view.isHidden():
            self.view.show()
            return
        index = self.view.currentIndex()
        new_index = index.sibling(index.row()+1, 0)
        if new_index.isValid():
            self.view.setCurrentIndex(new_index)


    def on_enterKeyPressed(self):
        index = self.view.currentIndex()
        self.lineEdit.setText(self.proxy.data(index).toString())
        self.close()


    def setValue(self, itemId):
        self.itemId = itemId
        val = self.sourceModel.getNameById(itemId).toString()
        self.lineEdit.setText(val)


    def value(self):
        itemId = self.sourceModel.getIdByName(QVariant(self.lineEdit.text()))
        return itemId


def getRightEditTempInvalid(tempInvalidId):
    app = QtGui.qApp
    db = QtGui.qApp.db
    tableTempInvalid = db.table('TempInvalid')
    if app.userHasRight(urRegEditTempInvalidWithInsurance) and app.userHasRight(urRegEditTempInvalidNoInsurance):
        return True
    elif app.userHasRight(urRegEditTempInvalidWithInsurance):
        currentOrgStructureId = QtGui.qApp.currentOrgStructureId()
        if currentOrgStructureId:
            table = db.table('OrgStructure')
            tablePerson = db.table('Person')
            record = db.getRecordEx(table, [table['net_id']], [table['id'].eq(currentOrgStructureId), table['deleted'].eq(0)])
            currentNetId = forceRef(record.value('net_id')) if record else None
            if tempInvalidId:
                cond = [tableTempInvalid['id'].eq(tempInvalidId),
                        tableTempInvalid['deleted'].eq(0),
                        table['deleted'].eq(0),
                        tablePerson['deleted'].eq(0),
                        ]
                queryTable = tablePerson.innerJoin(tableTempInvalid, tableTempInvalid['person_id'].eq(tablePerson['id']))
                queryTable = queryTable.innerJoin(table, table['id'].eq(tablePerson['orgStructure_id']))
                record = db.getRecordEx(queryTable, [table['net_id'], tableTempInvalid['insuranceOfficeMark']], cond)
                createNetId = forceRef(record.value('net_id')) if record else None
                if currentNetId == createNetId and forceBool(record.value('insuranceOfficeMark')):
                    return True
    elif app.userHasRight(urRegEditTempInvalidNoInsurance):
        if tempInvalidId:
            cond = [tableTempInvalid['id'].eq(tempInvalidId),
                    tableTempInvalid['deleted'].eq(0)
                    ]
            record = db.getRecordEx(tableTempInvalid, [tableTempInvalid['insuranceOfficeMark']], cond)
            if not forceBool(record.value('insuranceOfficeMark')):
                return True
    return False


def canChangePayStatusAdditional(widget, table, id):
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableCan = db.table(table)

    tableQuery = tableEvent.innerJoin(tableCan, tableCan['event_id'].eq(tableEvent['id']))
    record = db.getRecordEx(tableQuery, 'Event.isClosed, %s.payStatus AS canPayStatus, %s as typeId, EXISTS(SELECT id FROM Account_Item WHERE event_id = Event.id) as payStatus' % (table, "Action.actionType_id" if table.lower() in 'Action'.lower() else "NULL"), [tableCan['id'].eq(id),
                                                                                          tableEvent['deleted'].eq(0),
                                                                                          tableCan['deleted'].eq(0)])
    if record:
        payStatus = forceInt(record.value('payStatus'))
        isClosed = forceInt(record.value('isClosed'))
        payStatusCan = forceInt(record.value('canPayStatus'))
        typeId = forceRef(record.value('typeId'))
        if payStatus or (isClosed and payStatusCan):
            if QtGui.qApp.userHasRight(urEditAfterInvoicingEvent) or typeId and getIdentificationByCode('ActionType', typeId, 'changeAfterAccounts', raiseIfNonFound=False):
                message = u''
                if payStatus:
                    message = u'Данное событие выставлено в счёт\nи его данные изменять нежелательно!\nВы настаиваете на изменении?'
                elif payStatusCan:
                    message = u'%s из закрытого события были выставлены в счет\nи его данные изменять нежелательно!\nВы настаиваете на изменении?'%(u'Действия' if (table.lower() in 'Action'.lower()) else (u'Визиты' if (table.lower() in 'Visit'.lower()) else u''))
                if not QtGui.QMessageBox().critical(widget, u'Внимание!', message, QtGui.QMessageBox.Yes|QtGui.QMessageBox.No, QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                    return False
            else:
                message = u''
                if payStatus:
                    message = u'Данное событие выставлено в счёт, редактирование запрещено!'
                elif payStatusCan:
                    message = u'%s из закрытого события были выставлены в счет, редактирование запрещено!'%(u'Действия' if (table.lower() in 'Action'.lower()) else (u'Визиты' if (table.lower() in 'Visit'.lower()) else u''))
                QtGui.QMessageBox().critical(widget, u'Внимание!', message)
                return False
        if isClosed:
            if not QtGui.qApp.userHasRight(urEditClosedEvent):
                QtGui.QMessageBox().critical(widget, u'Внимание!', u'Событие закрыто!\nНет права на изменение закрытых событий!')
                return False
    return True


def canAddActionToExposedEvent(widget, eventId):
    db = QtGui.qApp.db
    table = db.table('Event')
    record = db.getRecordEx(table, 'isClosed, EXISTS(SELECT id FROM Account_Item WHERE event_id = Event.id) as payStatus',
                                   [table['id'].eq(eventId),
                                    table['deleted'].eq(0)])
    if record:
        payStatus = forceInt(record.value('payStatus'))
        isClosed = forceInt(record.value('isClosed'))
        if payStatus or isClosed:
            if QtGui.qApp.userHasRight(urEditAfterInvoicingEvent):
                if payStatus:
                    message = u'Данное событие выставлено в счёт\nи его данные изменять нежелательно!\nВы настаиваете на изменении?'
                    if not QtGui.QMessageBox().critical(widget, u'Внимание!', message, QtGui.QMessageBox.Yes|QtGui.QMessageBox.No, QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                        return False
            else:
                if payStatus:
                    message = u'Данное событие выставлено в счёт, редактирование запрещено!'
                    QtGui.QMessageBox().critical(widget, u'Внимание!', message)
                    return False
        if isClosed:
            if not QtGui.qApp.userHasRight(urEditClosedEvent):
                QtGui.QMessageBox().critical(widget, u'Внимание!', u'Событие закрыто!\nНет права на изменение закрытых событий!')
                return False
    return True


def canEditOtherpeopleAction(widget, id):
    if id:
        db = QtGui.qApp.db
        table = db.table('Action')
        cond = [table['deleted'].eq(0),
                table['id'].eq(id)]
        record = db.getRecordEx(table, u'*', cond)
        if record:
            personId = forceRef(record.value('person_id'))
            status = forceInt(record.value('status'))
            if status == CActionStatus.finished and personId and personId != QtGui.qApp.userId:
                if not (QtGui.qApp.userHasRight(urEditOtherpeopleAction) or (QtGui.qApp.userHasRight(urEditSubservientPeopleAction) and QtGui.qApp.userId in getPersonOrgStructureChiefs(personId))):
                    QtGui.QMessageBox.critical(widget, u'Внимание!', u'Нет права на редактирование чужих действий!')
                    return False
        return True


def removeExtCols(db, srcRecord):
    tableAction = db.table('Action')
    record = tableAction.newRecord()
    for i in xrange(record.count()):
        record.setValue(i, srcRecord.value(record.fieldName(i)))
    return record


def addActionTabPresence(obj, eventId, currentWidget, currentTable):
    from Events.Action import CActionTypeCache, CAction
    from Events.EditDispatcher import getEventFormClass
    from Events.Utils import checkTissueJournalStatusByActions, getEventCSGRequired, getEventShowTime, CFinanceType

    def getActionIdxLast(db, eventId, actionTypeClass):
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        recordAction = db.getRecordEx(
            tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id'])), 
            'MAX(Action.idx) AS idxLast', 
            [tableAction['event_id'].eq(eventId), tableAction['deleted'].eq(0), tableActionType['deleted'].eq(0), 
             tableActionType['class'].eq(actionTypeClass)])
        return forceInt(recordAction.value('idxLast')) if recordAction else -1

    def saveNewAction(db, eventId, actionTypeId, action, idxLastDict, eventFinanceId):
        actionType = CActionTypeCache.getById(actionTypeId)
        actionTypeClass = actionType.class_
        idxLast = idxLastDict.get(actionTypeClass, -1)
        if idxLast < 0:
            idxLast = getActionIdxLast(db, eventId, actionTypeClass) + 1
            idxLastDict[actionTypeClass] = idxLast
        else:
            idxLast += 1
            idxLastDict[actionTypeClass] = idxLast
        outRecord = removeExtCols(db, action.getRecord())
        if outRecord:
            cashFinanceId = CFinanceType.getId(CFinanceType.cash)
            actionFinanceId = forceRef(outRecord.value('finance_id'))
            if actionFinanceId is None:
                actionFinanceId = eventFinanceId
            outRecord.setValue('account', toVariant(actionFinanceId == cashFinanceId))
            action._record = outRecord
            id = action.save(eventId, idx=idxLast, checkModifyDate=False)
            if id:
                if id not in newActionIdList:
                    newActionIdList.append(id)
                action.getRecord().setValue('id', toVariant(id))
                checkTissueJournalStatusByActions([(action.getRecord(), action)])
        return idxLastDict
    newActionIdList = []
    currentRow = currentTable.currentRow()
    if eventId and currentWidget >= 0:
        actionTypes = []
        isCheckAddOutsideActions = False
        isCloseEventByAction = False
        formClass = getEventFormClass(eventId)
        dialog = formClass(obj)
        QtGui.qApp.setCounterController(CCounterController(obj))
        QtGui.qApp.setJTR(dialog)
        try:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            dialog.load(eventId)
            record = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
            dialog.setRecord(record)
            clientId = forceRef(record.value('client_id')) if record else None
            mesId = forceRef(record.value('MES_id')) if record else None
            mesSpecificationId = forceRef(record.value('mesSpecification_id')) if record else None
            dialog.tabMes.cmbMes.setValue(toVariant(mesId))
            dialog.tabMes.cmbMesSpecification.setValue(toVariant(mesSpecificationId))
            tabWidgetList = [dialog.tabToken,
                             dialog.tabStatus,
                             dialog.tabDiagnostic,
                             dialog.tabCure,
                             dialog.tabMisc
                            ]
            dialog.tabWidget.setCurrentWidget(tabWidgetList[currentWidget])
            actionTypes, actionTypeClasses, hasTblActions, widget = getNewActionTypes(dialog)
            updateTabList = []
            notAddedActions = []
            isEventCSGRequired = getEventCSGRequired(dialog.eventTypeId)
            actionsTabsList = dialog.getActionsTabsList()
            from Events.ActionCreateDialog import CActionCreateDialog
            showEditorForEveryAction = True
            
            for actionTypeId, action, csgRecord in actionTypes:
                res = True
                actionType = CActionTypeCache.getById(actionTypeId)
                if u'moving' in actionType.flatCode.lower():
                    for record in dialog.modelActionsSummary._items:
                        if action:
                            actionTypeItem = CActionTypeCache.getById(forceString(record.value('actionType_id')))
                            if actionTypeItem and (u'received' in actionTypeItem.flatCode.lower()):
                                if not forceDate(record.value('endDate')):
                                    res = actionType.checkReceivedMovingLeaved(u'Действие "Движение" не может появится при наличии не законченного действия "Поступление"')
                                    break
                                break
                    else:
                        res = actionType.checkReceivedMovingLeaved(u'Действие "Движение" не должно применяться пока нет действия "Поступление"')
                if not res:
                    actionTypes.remove((actionTypeId, action, csgRecord))
            
            relatedItems = {}
            for actionTypeId, action, csgRecord in actionTypes:
                relatedActionTypes = CActionTypeCache.getById(actionTypeId).getRelatedActionTypes()
                relatedItems[action] = []
                for actionType, isRequired in relatedActionTypes.items():
                    if isRequired:
                        itemRecord = db.table('Action').newRecord()
                        itemRecord.setValue('actionType_id', actionType)
                        item = CAction.getFilledAction(dialog, itemRecord, actionType)
                        relatedItems[action].append((actionType, item, None))
            for items in relatedItems.values():
                actionTypes.extend(items)
            if showEditorForEveryAction:
                model = None
                for actionTypeId, action, csgRecord in actionTypes:
                    createDialog = None
                    try:
                        createDialog = CActionCreateDialog(dialog)
                        createDialog.load(action.getRecord(), action, clientId)
                        if createDialog.exec_():
                            if len(actionTypeClasses) > 1:
                                if hasTblActions:
                                    model = dialog.tblActions.model()
                                    for actionTypeId, action, csgRecord in actionTypes:
                                        class_ = forceInt(QtGui.qApp.db.translate('ActionType', 'id', actionTypeId, 'class'))
                                        actionsTab = actionsTabsList[class_]
                                        if actionsTab not in updateTabList:
                                            updateTabList.append(actionsTab)
                                        index = model.index(model.rowCount()-1, 0)
                                        model.setData(index, toVariant(actionTypeId), presetAction=action)
                                        if isEventCSGRequired:
                                            actionsTab.cmbCSG.addActionToCSG(action.getRecord(), csgRecord)
                                    model.emitAllChanged()
                                else:
                                    for actionTypeId, action, csgRecord in actionTypes:
                                        class_ = forceInt(QtGui.qApp.db.translate('ActionType', 'id', actionTypeId, 'class'))
                                        actionsTab = actionsTabsList[class_]
                                        if actionsTab not in updateTabList:
                                            updateTabList.append(actionsTab)
                                        model = actionsTab.tblAPActions.model()
                                        model.addRow(actionTypeId, presetAction=action)
                                        if isEventCSGRequired:
                                            actionsTab.cmbCSG.addActionToCSG(action.getRecord(), csgRecord)
                            else:
                                for actionTypeId, action, csgRecord in actionTypes:
                                    class_ = forceInt(QtGui.qApp.db.translate('ActionType', 'id', actionTypeId, 'class'))
                                    actionsTab = actionsTabsList[class_]
                                    if actionsTab not in updateTabList:
                                        updateTabList.append(actionsTab)
                                    model = actionsTab.tblAPActions.model()
                                    index = model.index(model.rowCount()-1, 0)
                                    model.setData(index, toVariant(actionTypeId), presetAction=action)
                                    if isEventCSGRequired:
                                        actionsTab.cmbCSG.addActionToCSG(action.getRecord(), csgRecord)
                        else:
                            notAddedActions.append((actionTypeId, action, csgRecord))
                    finally:
                        createDialog.deleteLater()
                if model:
                    model.emitAllChanged()
            
            for item in notAddedActions:
                actionTypes.remove(item)
            for actionsTab in updateTabList:
                actionsTab.updateActionEditor()
                actionsTab.onActionCurrentChanged()
            if len(actionTypeClasses) == 1:
                dialog.tabWidget.setCurrentWidget(widget)
            isEventCSGRequired = getEventCSGRequired(dialog.eventTypeId)
            actionList = []
            for actionTypeId, action, csgRecord in actionTypes:
                if action:
                    isActionClose = bool(action.getType().closeEvent)
                    if isActionClose and not isCloseEventByAction:
                        isCloseEventByAction = isActionClose
                    actionList.append((action.getRecord(), action))
            if actionList:
                showTime = getEventShowTime(dialog.eventTypeId)
                if showTime:
                    begDateEvent = QDateTime(dialog.edtBegDate.date(), dialog.edtBegTime.time())
                    endDateEvent = QDateTime(dialog.edtEndDate.date(), dialog.edtEndTime.time())
                else:
                    begDateEvent = dialog.edtBegDate.date()
                    endDateEvent = dialog.edtEndDate.date()
                isCheckAddOutsideActions = dialog.checkAddOutsideActionsDataEntered(begDateEvent, endDateEvent, actionList)
            dialog.done(0)
        finally:
            QtGui.qApp.unsetJTR(dialog)
            QtGui.qApp.delAllCounterValueIdReservation()
            QtGui.qApp.setCounterController(None)
            dialog.deleteLater()
        if isCheckAddOutsideActions:
            isAddAction = False
            idxLastDict = {}
            if len(actionTypes) > 0:
                for actionTypeId, action, csgRecord in actionTypes:
                    if action:
                        if isEventCSGRequired and csgRecord:
                            action.getRecord().setValue('eventCSG_id', csgRecord.value('id'))
                        idxLastDict = saveNewAction(db, forceRef(action.getRecord().value('event_id')), actionTypeId,
                                                    action, idxLastDict, forceRef(record.value('finance_id')))
                        if action in relatedItems.keys() and action.getId():
                            for item in relatedItems[action]:
                                item[1].setMasterId(action.getId())
                                item[1].getRecord().setValue('master_id', action.getId())
                                item[1].getRecord().setValue('person_id', action.getRecord().value('person_id'))
                        isAddAction = True
            if isCloseEventByAction and isAddAction:
                recordEvent = db.getRecordEx(tableEvent, 'Event.*', [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
                if recordEvent:
                    eventExecDate = forceDate(recordEvent.value('execDate'))
                    if not eventExecDate:
                        CDialogBase(obj).checkValueMessage(u'Добавлено Мероприятие требующее закрытия Случая Обслуживания! Для этого откройте на редактирование Случай Обслуживания и внесите необходимые правки.', False, None)
                currentTable.setCurrentRow(currentRow)
            record.setValue('modifyDatetime', QVariant(QDateTime.currentDateTime()))
            record.setValue('modifyPerson_id', QVariant(QtGui.qApp.userId))
            record._dirty = True
            db.updateRecord("Event", record)
    return currentTable, currentRow, newActionIdList


def getNewActionTypes(dialog):
    from Events.ActionsSelector import selectActionTypes
    if dialog.isReadOnly():
        return [], [], False, None
    if hasattr(dialog, 'tabWidget'):
        widget = dialog.tabWidget.currentWidget()
        cond = []
        widgetClass = {}
        if hasattr(dialog, 'tabToken'):
            cond.append(dialog.tabToken)
            widgetClass[dialog.tabToken] = [0, 1, 2, 3]
        if hasattr(dialog, 'tabMes'):
            cond.append(dialog.tabMes)
            widgetClass[dialog.tabMes] = [0, 1, 2, 3]
        if hasattr(dialog, 'tabStatus'):
            cond.append(dialog.tabStatus)
            widgetClass[dialog.tabStatus] = [0]
        if hasattr(dialog, 'tabDiagnostic'):
            cond.append(dialog.tabDiagnostic)
            widgetClass[dialog.tabDiagnostic] = [1]
        if hasattr(dialog, 'tabCure'):
            cond.append(dialog.tabCure)
            widgetClass[dialog.tabCure] = [2]
        if hasattr(dialog, 'tabMisc'):
            cond.append(dialog.tabMisc)
            widgetClass[dialog.tabMisc] = [3]
        if widget not in cond:
            return [], [], False, None
    else:
        return [], [], False, None
    if hasattr(dialog, 'tblActions'):
        hasTblActions = True
    else:
        hasTblActions = False
    orgStructureId = QtGui.qApp.currentOrgStructureId()
    financeCode = forceStringEx(QtGui.qApp.db.translate('rbFinance', 'id', dialog.eventFinanceId, 'code'))
    if financeCode:
        financeCode = financeCode in ('3', '4')
    existsActionTypesList = []
    if hasattr(dialog, 'modelActionsSummary'):
        for item in dialog.modelActionsSummary.items():
            existsActionTypesList.append(forceRef(item.value('actionType_id')))
    actionTypeClasses = widgetClass.get(widget, [0, 1, 2, 3])
    actionTypes = selectActionTypes( dialog if len(actionTypeClasses) != 1 else widget,
                                     dialog,
                                     actionTypeClasses,
                                     orgStructureId,
                                     dialog.eventTypeId,
                                     dialog.contractId,
                                     dialog.getMesId(),
                                     financeCode,
                                     dialog._id,
                                     existsActionTypesList,
                                     visibleTblSelected=True,
                                     contractTariffCache=dialog.contractTariffCache,
                                     clientMesInfo=dialog.getClientMesInfo(),
                                     eventDate = dialog.edtBegDate.date() if dialog.edtBegDate.date() else dialog.edtEndDate.date(),
                                   )
    return actionTypes, actionTypeClasses, hasTblActions, widget


def getJobTicketsToEvent(obj, eventId):
    from Events.EditDispatcher import getEventFormClass
    from Events.Utils          import checkTissueJournalStatusByActions
    if eventId:
        formClass = getEventFormClass(eventId)
        dialog = formClass(obj)
        QtGui.qApp.setJTR(dialog)
        try:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            dialog.load(eventId)
            record = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
            dialog.setRecord(record)
            fullActionsModelsItemList = dialog.on_btnJobTickets_clicked()
            dialog.done(0)
            db.transaction()
            try:
                for record, action in fullActionsModelsItemList:
                    outRecord = removeExtCols(db, action.getRecord())
                    if outRecord:
                        action._record = outRecord
                        id = action.save(eventId)
                        action.getRecord().setValue('id', toVariant(id))
                        checkTissueJournalStatusByActions([(action.getRecord(), action)])
                db.commit()
            except:
                db.rollback()
                QtGui.qApp.logCurrentException()
                raise
        finally:
            QtGui.qApp.unsetJTR(dialog)
            dialog.deleteLater()


def preFillingActionRecordMSI(record, actionTypeId, amount=0, financeId=None, contractId=None, eventRecord=None, action=None):
    from Events.Action import CActionTypeCache, CActionType, getActionDuration
    from Events.Utils import getEventDuration
    from library.Calendar import wpFiveDays, wpSixDays, wpSevenDays

    def getEventDurationMSI(weekProfile, startDate, stopDate, eventTypeId):
        return getEventDuration(startDate, stopDate, weekProfile, eventTypeId)

    def getActionDefaultAmountMSI(eventRecord, actionType, record, action):
        eventId = forceRef(eventRecord.value('id')) if eventRecord else None
        eventTypeId = forceRef(eventRecord.value('eventType_id')) if eventRecord else None
        setDate = forceDate(eventRecord.value('setDate')) if eventRecord else QDate.currentDate()
        execDate = forceDate(eventRecord.value('execDate')) if eventRecord else QDate.currentDate()
        result = actionType.amount
        if actionType.amountEvaluation == CActionType.eventVisitCount:
            visitCount = 0
            if eventId:
                db = QtGui.qApp.db
                tableVisit = db.table('Visit')
                visitCount = db.getDistinctCount(tableVisit, tableVisit['id'].name(), where=[tableVisit['event_id'].eq(eventId), tableVisit['deleted'].eq(0)])
            result = result * (visitCount if visitCount else 1)
        elif actionType.amountEvaluation == CActionType.eventDurationWithFiveDayWorking:
            result = result * getEventDurationMSI(wpFiveDays, setDate, execDate, eventTypeId)
        elif actionType.amountEvaluation == CActionType.eventDurationWithSixDayWorking:
            result = result * getEventDurationMSI(wpSixDays, setDate, execDate, eventTypeId)
        elif actionType.amountEvaluation == CActionType.eventDurationWithSevenDayWorking:
            result = result * getEventDurationMSI(wpSevenDays, setDate, execDate, eventTypeId)
        elif actionType.amountEvaluation == CActionType.actionDurationWithFiveDayWorking:
            result = result * getActionDuration(eventTypeId, record, wpFiveDays)
        elif actionType.amountEvaluation == CActionType.actionDurationWithSixDayWorking:
            result = result * getActionDuration(eventTypeId, record, wpSixDays)
        elif actionType.amountEvaluation == CActionType.actionDurationWithSevenDayWorking:
            result = result * getActionDuration(eventTypeId, record, wpSevenDays)
        elif actionType.amountEvaluation == CActionType.actionFilledPropsCount:
            result = result * action.getFilledPropertiesCount() if action else 0
        elif actionType.amountEvaluation == CActionType.actionAssignedPropsCount:
            result = result * action.getAssignedPropertiesCount() if action else 0
        return result

    if actionTypeId:
        actionType = CActionTypeCache.getById(actionTypeId)
        defaultStatus = actionType.defaultStatus
        defaultDirectionDate = actionType.defaultDirectionDate
        defaultBegDate = actionType.defaultBegDate
        defaultEndDate = actionType.defaultEndDate
        defaultExecPersonId = actionType.defaultExecPersonId
        defaultPerson = actionType.defaultPersonInEvent
        defaultOrgId = actionType.defaultOrgId
        office = actionType.office
        record.setValue('actionType_id', toVariant(actionTypeId))
        if not (amount and actionType.amountEvaluation == CActionType.userInput):
            amount = getActionDefaultAmountMSI(eventRecord, actionType, record, action)
            record.setValue('amount', toVariant(amount))
    else:
        defaultStatus = CActionStatus.finished  # Закончено
        defaultDirectionDate = CActionType.dddUndefined
        defaultBegDate = 0
        defaultEndDate = CActionType.dedEventExecDate  # Дата события
        defaultExecPersonId = None
        defaultPerson = CActionType.dpEmpty
        defaultOrgId = None
        office = ''

    if defaultEndDate == CActionType.dedCurrentDate:
        endDate = QDateTime.currentDateTime()
    else:
        if defaultStatus in (CActionStatus.finished, CActionStatus.withoutResult):
            endDate = QDateTime.currentDateTime()
        else:
            endDate = QDateTime()
    begDate = QDateTime.currentDateTime()
    if defaultDirectionDate == CActionType.dddCurrentDate:
        directionDate = QDateTime.currentDateTime()
    elif defaultDirectionDate == CActionType.dddActionExecDate:
        if endDate:
            directionDate = begDate = endDate
        else:
            directionDate = begDate
    else:
        directionDate = begDate
    if defaultBegDate == CActionType.dbdCurrentDate:
        begDate = QDateTime.currentDateTime()

    if defaultEndDate == CActionType.dedActionBegDate or defaultEndDate == CActionType.dedSyncActionBegDate:
        endDate = max(begDate, directionDate)
    setPersonId = QtGui.qApp.userId if QtGui.qApp.userSpecialityId else None
    if defaultExecPersonId:
        personId = defaultExecPersonId
    else:
        if defaultPerson == CActionType.dpCurrentMedUser:
            if QtGui.qApp.userSpecialityId:
                personId = QtGui.qApp.userId
            else:
                personId = None
        elif defaultPerson == CActionType.dpCurrentUser:
            personId = QtGui.qApp.userId
        elif defaultPerson == CActionType.dpSetPerson:
            personId = setPersonId
        else:
            personId = None
    if defaultBegDate == CActionType.dbdActionEndDate:
        begDate = max(endDate, directionDate)
    record.setValue('directionDate', toVariant(directionDate))
    record.setValue('setPerson_id', toVariant(setPersonId))
    record.setValue('begDate', toVariant(max(begDate, directionDate)))
    record.setValue('endDate', toVariant(endDate))
    record.setValue('status', toVariant(defaultStatus))
    record.setValue('office', toVariant(office))
    record.setValue('person_id', toVariant(personId))
    if defaultOrgId:
        record.setValue('org_id', toVariant(defaultOrgId))
    return record


def saveSurveillanceRemoveDeath(deathDate, clientId, execPerson=None):
    if deathDate and clientId:
        execPersonId = execPerson if execPerson else QtGui.qApp.userId
        db = QtGui.qApp.db
        table = db.table('ProphylaxisPlanning')
        tableDispanser = db.table('rbDispanser')
        recordDispanser = db.getRecordEx(tableDispanser, [tableDispanser['id']], [tableDispanser['observed'].eq(0), tableDispanser['name'].like(u'%%смерт%%')])
        dispanserId = forceRef(recordDispanser.value('id') if recordDispanser else None)
        tableRR = db.table('rbSurveillanceRemoveReason')
        recordRR = db.getRecordEx(tableRR, [tableRR['id']], [tableRR['dispanser_id'].eq(dispanserId), tableRR['name'].like(u'%%смерт%%')])
        removeReasonId = forceRef(recordRR.value('id') if recordRR else None)
        if not removeReasonId:
            recordRR = db.getRecordEx(tableRR, [tableRR['id']], [tableRR['dispanser_id'].isNull(), tableRR['name'].like(u'%%смерт%%')])
            removeReasonId = forceRef(recordRR.value('id') if recordRR else None)
        saveRecords = []
        removeIdList = []
        recordPPs = db.getRecordList(table, '*', [table['client_id'].eq(clientId), table['removeReason_id'].isNull(), table['parent_id'].isNull(), table['deleted'].eq(0)])
        for recordPP in recordPPs:
            prophylaxisPlanningId = forceRef(recordPP.value('id'))
            recordPP.setValue('dispanser_id', toVariant(dispanserId))
            recordPP.setValue('removeDate', toVariant(deathDate))
            recordPP.setValue('removeReason_id', toVariant(removeReasonId))
            recordPeriods = db.getRecordList(table, '*', [table['client_id'].eq(clientId), table['parent_id'].eq(prophylaxisPlanningId), table['deleted'].eq(0)])
            for recordPeriod in recordPeriods:
                begDate = forceDate(recordPeriod.value('begDate'))
                if not begDate or begDate <= deathDate:
                    recordPeriod.setValue('dispanser_id', toVariant(dispanserId))
                    recordPeriod.setValue('removeDate', toVariant(deathDate))
                    recordPeriod.setValue('removeReason_id', toVariant(removeReasonId))
                    saveRecords.append(recordPeriod)
                else:
                    periodId = forceRef(recordPeriod.value('id'))
                    if periodId and periodId not in removeIdList:
                        removeIdList.append(periodId)
                saveRecords.append(recordPP)
        if removeIdList:
            db.deleteRecord(table, [table['id'].inlist(removeIdList)])
        for saveRecord in saveRecords:
            db.updateRecord('ProphylaxisPlanning', saveRecord)
        diagnosisList = updateDiagnosisRecords(clientId, dispanserId, deathDate, execPersonId)
        if diagnosisList:
            createDiagnosticRecords(diagnosisList, execPersonId, clientId=clientId, removeDispanserId=dispanserId, removeDate=deathDate)


def getProphylaxisPlanningType():
    db = QtGui.qApp.db
    table = db.table('rbProphylaxisPlanningType')
    record = db.getRecordEx(table, [table['id']], [table['code'].eq(u'ДН')])
    return forceRef(record.value('id')) if record else None


def updateDiagnosisRecords(clientId, dispanserId, removeDate, execPersonId=None):
    db = QtGui.qApp.db
    tableDiagnosis = db.table('Diagnosis')
    tableRBDispanser = db.table('rbDispanser')
    query = tableDiagnosis.leftJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnosis['dispanser_id']))
    cond = [
        tableDiagnosis['dispanser_id'].isNotNull(),
        tableDiagnosis['deleted'].eq(0),
        tableRBDispanser['name'].notlike(u'снят%'),
        tableDiagnosis['client_id'].eq(clientId),
    ]
    diagnosisList = db.getRecordList(query, '*', cond)
    if diagnosisList:
        for item in diagnosisList:
            updateCond = [
                tableDiagnosis['id'].eq(forceInt(item.value('id'))),
                tableDiagnosis['deleted'].eq(0),
                tableDiagnosis['MKB'].eq(forceString(item.value('MKB'))),
            ]
            updateCols = [
                tableDiagnosis['endDate'].eq(forceDate(removeDate)),
                tableDiagnosis['dispanser_id'].eq(dispanserId),
            ]
            if execPersonId:
                updateCols.append(tableDiagnosis['person_id'].eq(execPersonId))
            db.updateRecords(tableDiagnosis, updateCols, updateCond)
    return diagnosisList


def createDiagnosticRecords(diagnosisList, execPersonId=None, clientId=None, removeDispanserId=None, removeDate=None):
    db = QtGui.qApp.db
    eventId = createEvent(clientId, removeDate)
    if not execPersonId:
        execPersonId = QtGui.qApp.userId
    for item in diagnosisList:
        tableDiagnostic = db.table('Diagnostic')
        cond = [
            tableDiagnostic['diagnosis_id'].eq(forceInt(item.value('id'))),
        ]
        cols = [tableDiagnostic['TNMS'],
                tableDiagnostic['diagnosisType_id'],
                tableDiagnostic['character_id'],
                tableDiagnostic['stage_id'],
                tableDiagnostic['phase_id'],
                ]
        lastDiagnosticRecord = db.getRecordList(tableDiagnostic, cols, cond, 'id DESC')[0]

        newDiagnosticRecord = tableDiagnostic.newRecord()
        newDiagnosticRecord.setValue('event_id', toVariant(eventId))
        newDiagnosticRecord.setValue('diagnosis_id', toVariant(item.value('id')))
        newDiagnosticRecord.setValue('TNMS', toVariant(lastDiagnosticRecord.value('TNMS')))
        newDiagnosticRecord.setValue('diagnosisType_id', toVariant(lastDiagnosticRecord.value('diagnosisType_id')))
        newDiagnosticRecord.setValue('character_id', toVariant(lastDiagnosticRecord.value('character_id')))
        newDiagnosticRecord.setValue('stage_id', toVariant(lastDiagnosticRecord.value('stage_id')))
        newDiagnosticRecord.setValue('phase_id', toVariant(lastDiagnosticRecord.value('phase_id')))
        newDiagnosticRecord.setValue('dispanser_id', toVariant(removeDispanserId))
        newDiagnosticRecord.setValue('sanatorium', toVariant(0))
        newDiagnosticRecord.setValue('hospital', toVariant(0))
        newDiagnosticRecord.setValue('person_id', toVariant(execPersonId))
        specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', execPersonId, 'speciality_id'))
        newDiagnosticRecord.setValue('speciality_id', toVariant(specialityId))
        newDiagnosticRecord.setValue('setDate', toVariant(removeDate))
        newDiagnosticRecord.setValue('endDate', toVariant(removeDate))
        newDiagnosticRecord.setValue('notes', toVariant(''))

        db.insertRecord('Diagnostic', newDiagnosticRecord)


def createEvent(clientId, removeDate):
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    eventType_id = db.getIdList(tableEventType, [tableEventType['id']], [tableEventType['code'].eq('rmDisp')])[0]
    newEventRecord = tableEvent.newRecord()
    newEventRecord.setValue('execPerson_id', toVariant(QtGui.qApp.userId))
    newEventRecord.setValue('setPerson_id', toVariant(QtGui.qApp.userId))
    newEventRecord.setValue('eventType_id', toVariant(eventType_id))
    newEventRecord.setValue('client_id', toVariant(clientId))
    orgId = forceRef(QtGui.qApp.db.translate('Person', 'id', QtGui.qApp.userId, 'org_id'))
    newEventRecord.setValue('org_id', toVariant(orgId))
    newEventRecord.setValue('setDate', toVariant(removeDate))
    newEventRecord.setValue('execDate', toVariant(removeDate))
    newEventRecord.setValue('isClosed', toVariant(1))

    eventId = db.insertRecord('Event', newEventRecord)
    return eventId


# Логичнее перенести в utils, т.к. используется в нескольких местах
def createRelatedActionTMK(widget, clientId, directionPersonId, directionDateTime, scheduleItemId):
    """
    При записи на талон с typeRecord = 4 (ТМК MAX) создаёт связанное действие tmkDirectMax, после чего вызывает шаблон для создания направления TMK (startTMK)
    """
    # Локальные импорты во избежание цикличного импорта
    from Events.Action import CActionTypeCache
    from Events.Action import CAction
    from library.PrintTemplates import getFirstPrintTemplate
    from Events.EventInfo import CEventInfo
    from Events.ActionInfo import CCookedActionInfo
    from Events.ActionsModel import CActionRecordItem
    from library.PrintTemplates import applyTemplate

    db = QtGui.qApp.db
    tableAction = db.table('Action')
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    tableActionType = db.table('ActionType')
    eventId = None

    recordEventType = db.getRecordEx(tableEventType, [tableEventType['id']],
                                     [tableEventType['context'].like(u'relatedAction%'),
                                      tableEventType['deleted'].eq(0)], u'EventType.id')
    eventTypeId = forceRef(recordEventType.value('id')) if recordEventType else None
    if not eventTypeId:
        QtGui.QMessageBox().warning(widget, u'Внимание!', u'Отсутствует тип события с контекстом "relatedAction"',
                                    QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
        return False

    actionTypeRecord = db.getRecordEx(tableActionType, [tableActionType['id']],
                                     [tableActionType['flatCode'].eq(u'tmkDirectMax'),
                                      tableActionType['deleted'].eq(0)], u'ActionType.id')
    actionTypeId = forceRef(actionTypeRecord.value('id')) if actionTypeRecord else None

    if not actionTypeId:
        QtGui.QMessageBox().warning(widget, u'Внимание!', u'Отсутствует тип действия с кодом для отчёта "tmkDirectMax"',
                                    QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
        return False

    if actionTypeId:
        prevEventId = eventId
        recordEvent = tableEvent.newRecord()
        recordEvent.setValue('createDatetime', toVariant(QDateTime().currentDateTime()))
        recordEvent.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
        recordEvent.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
        recordEvent.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
        recordEvent.setValue('setDate', toVariant(QDateTime().currentDateTime()))
        recordEvent.setValue('eventType_id', toVariant(eventTypeId))
        recordEvent.setValue('client_id', toVariant(clientId))
        recordEvent.setValue('prevEvent_id', toVariant(prevEventId))
        eventId = db.insertRecord(tableEvent, recordEvent)

        if eventId:
            recordEvent.setValue('id', toVariant(eventId))

        QtGui.qApp.setCounterController(CCounterController(widget))
        QtGui.qApp.setJTR(widget)
        try:
            actionType = CActionTypeCache.getById(actionTypeId)
            defaultStatus = actionType.defaultStatus
            newRecord = tableAction.newRecord()

            newRecord.setValue('createDatetime', toVariant(QDateTime().currentDateTime()))
            newRecord.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
            newRecord.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
            newRecord.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
            newRecord.setValue('actionType_id', toVariant(actionTypeId))
            newRecord.setValue('status', toVariant(defaultStatus))
            newRecord.setValue('begDate', toVariant(QDateTime().currentDateTime()))
            newRecord.setValue('directionDate', toVariant(QDateTime().currentDateTime()))
            newRecord.setValue('plannedEndDate', toVariant(directionDateTime))
            newRecord.setValue('setPerson_id', toVariant(QtGui.qApp.userId))
            newRecord.setValue('person_id', toVariant(directionPersonId))
            newRecord.setValue('id', toVariant(None))
            newRecord.setValue('event_id', toVariant(eventId))

            newAction = CAction(record=newRecord)
            newAction.updatePresetValuesConditions({'clientId': clientId, 'eventTypeId': eventTypeId})
            newAction.initPresetValues()

            if not newAction:
                QtGui.QMessageBox().warning(widget, u'Внимание!',
                                            u'Ошибка при сохранении связанного действия',
                                            QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                return False

            newAction.save(idx=0, checkModifyDate=False)


            template = getFirstPrintTemplate('startTMK')

            if not template:
                QtGui.QMessageBox().warning(widget, u'Внимание!',
                                            u'Ошибка при создании напрвления ТМК',
                                            QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                return False

            context = CInfoContext()

            eventInfo = context.getInstance(CEventInfo, eventId)
            eventInfo.actions._idList.append(newAction.getId())
            eventInfo.actions._items.append(
                CCookedActionInfo(context, newAction.getRecord(), newAction))
            eventInfo.actions._loaded = True
            action = eventInfo.actions[0]
            currentActionIndex = 0

            eventActions = eventInfo.actions

            data = {'event': eventInfo,
                    'action': action,
                    'client': eventInfo.client,
                    'actions': eventActions,
                    'currentActionIndex': currentActionIndex,
                    'currentAction': CActionRecordItem(newRecord, newAction),
                    'scheduleItemId': scheduleItemId
                    }
            applyTemplate(widget, template.id, data)

            return True

        finally:
            QtGui.qApp.unsetJTR(widget)
            QtGui.qApp.delAllCounterValueIdReservation()
            QtGui.qApp.setCounterController(None)

    return False
