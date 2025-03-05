# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import re

from PyQt4 import QtGui
from PyQt4.QtCore import QDate

from library.AgeSelector    import parseAgeSelector, checkAgeSelector
from library.DbEntityCache import CDbEntityCache
from library.Identification import getIdentification, CIdentificationException
from library.PrintInfo import CInfo, CRBInfo, CInfoList, CDateInfo, CDictInfoMixin, CIdentificationInfoMixin
from library.Utils         import forceBool, forceInt, forceRef, forceDate, forceString, forceStringEx, formatNameInt, formatSex, formatShortNameInt, nameCase, toVariant, trim

from KLADR.KLADRModel      import getKladrTreeModel

__all__ = [ 'CNet',
            'CNetInfo',
            'COKFSInfo',
            'COKPFInfo',
            'COrgInfo',
            'COrgStructure',
            'COrgStructureInfo',
            'CSexAgeConstraint',
            'advisePolicyType',
            'findOrgStructuresByAddress',
            'findOrgStructuresByHouseAndFlat',
            'fixOKVED',
            'getAccountInfo',
            'getActionTypeOrgStructureIdList',
            'getBankFilials',
            'getOKVEDName',
            'getOrganisationCluster',
            'getOrganisationDescendants',
            'getOrganisationInfo',
            'getOrganisationParent',
            'getOrganisationShortName',
            'getOrgStructureActionTypeIdSet',
            'getOrgStructureAddressIdList',
            'getOrgStructureDescendants',
            'getOrgStructureListDescendants', 
            'getOrgStructureFullName',
            'getOrgStructureName',
            'getOrgStructureNetId',
            'getOrgStructurePersonIdList',
            'getOrgStructures',
            'getPersonChiefs',
            'getPersonOrgStructureChiefs',
            'getPersonInfo',
            'getPersonShortName',
            'getPostName',
            'getShortBankName',
            'getSolitaryOrgStructureId',
            'getSpecialityName',
            'parseOKVEDList',
          ]


def getOrganisationShortName(id):
    result = QtGui.qApp.db.translate('Organisation', 'id', id, 'shortName')
    if result:
        return forceString(result)
    else:
        return ''


def getMedicalAidProfileIdName(id):
    result = QtGui.qApp.db.translate('rbMedicalAidProfile', 'id', id, 'name')
    if result:
        return forceString(result)
    else:
        return ''

 
def getOrganisationInfisAndShortName(id):
    result = QtGui.qApp.db.translate('Organisation', 'id', id, "concat_ws(' | ', infisCode, shortName)")
    if result:
        return forceString(result)
    else:
        return ''


def getOrganisationInfo(id):
    if id:
        db = QtGui.qApp.db
        table  = db.table('Organisation')
        record = db.getRecord(table, '*', id)
        if record:
            return dict(id        = id,
                        fullName  = forceString(record.value('fullName')),
                        shortName = forceString(record.value('shortName')),
                        title     = forceString(record.value('title')),
                        INN       = forceString(record.value('INN')),
                        KPP       = forceString(record.value('KPP')),
                        OGRN      = forceString(record.value('OGRN')),
                        OKVED     = forceString(record.value('OKVED')),
                        infisCode = forceString(record.value('infisCode')),
                        miacCode  = forceString(record.value('miacCode'))
                       )
    return {}


def parseOKVEDList(str):
    return [ trim(s) for s in str.replace(',', ';').replace('|', ';').split(';') if s != '' ]


def fixOKVED(code):
    db = QtGui.qApp.db
    table  = db.table('rbOKVED')
    fixedCode = forceString(db.translate(table, 'code', code, 'code'))
    if fixedCode:
        return True, fixedCode
    partialCode = code
    while partialCode:
        fixedCode = forceString(db.translate(table, 'OKVED', partialCode, 'code'))
        if fixedCode:
            return True, fixedCode
        partialCode = partialCode[:-1]
    return False, code


def getOKVEDName(code):
    if code:
        db = QtGui.qApp.db
        table  = db.table('rbOKVED')
        records= db.getRecordList(table, 'name', table['code'].eq(code))
        if records:
            return forceString(records[0].value(0))
        else:
            return u'{%s}' % code
    else:
        return u''


def advisePolicyType(insurerId, serial):
    # подобрать тип полиса по с.к. и серии
    db = QtGui.qApp.db
    table = db.table('Organisation_PolicySerial')
    record = db.getRecordEx(table, 'policyType_id',
                            [table['organisation_id'].eq(insurerId), table['serial'].eq(serial)]
                           )
    if record:
        return forceRef(record.value(0))
    else:
        return None


def getShortBankName(bankId):
    if bankId:
        db = QtGui.qApp.db
        bankRecord = db.getRecord('Bank', 'BIK, name', bankId)
        if bankRecord:
            return forceString(bankRecord.value('BIK'))+ ' '+forceString(bankRecord.value('name'))
        else:
            return '{%d}' % bankId
    return ''


def getBankFilials(BIK):
    # Список филиалов банка, имеющего данный БИК
    db = QtGui.qApp.db
    table  = db.table('Bank')
    records = db.getRecordList(table, 'branchName', table['BIK'].eq(BIK))
    if records:
        return [record.value(0) for record in records]
    else:
        return []


def getAccountInfo(id):
    if id:
        db = QtGui.qApp.db
        table  = db.table('Organisation_Account')
        record = db.getRecord(table, ('name','notes','bank_id'), id)
        if record:
            bankId = forceRef(record.value('bank_id'))
            return dict(id      = id,
                        name    = forceString(record.value('name')),
                        notes   = forceString(record.value('notes')),
                        bank_id = bankId,
                        shortBankName = getShortBankName(bankId)
                       )
    return {}


def getOrganisationParent(orgId):
    # найти самый верхний элемент в иерархии организаций
    db = QtGui.qApp.db
    table = db.table('Organisation')

    while orgId:
        headId = forceRef(db.translate(table, 'id', orgId, 'head_id'))
        if headId:
            orgId = headId
    return orgId


def getOrganisationDescendants(orgId):
    # найти все организации явл. "потомками" данной
    return QtGui.qApp.db.getDescendants('Organisation', 'head_id', orgId)


def getOrganisationCluster(orgId):
    # найти все родственные организации
    return getOrganisationDescendants(getOrganisationParent(orgId))


def getPostName(postId):
    return forceString(QtGui.qApp.db.translate('rbPost', 'id', postId, 'name'))


def getSpecialityName(specialityId):
    return forceString(QtGui.qApp.db.translate('rbSpeciality', 'id', specialityId, 'name'))


def getTariffCategoryName(tariffCategoryId):
    return forceString(QtGui.qApp.db.translate('rbTariffCategory', 'id', tariffCategoryId, 'name'))


def getPersonInfo(personId):
    if personId:
        db = QtGui.qApp.db
        table  = db.table('Person')
        record = db.getRecord(table,
                              ['code',
                               'lastName',
                               'firstName',
                               'patrName',
                               'orgStructure_id',
                               'post_id',
                               'speciality_id',
                               'tariffCategory_id'
                              ],
                              personId)
        if record:
            code           = forceString(record.value('code'))
            lastName       = nameCase(forceString(record.value('lastName')))
            firstName      = nameCase(forceString(record.value('firstName')))
            patrName       = nameCase(forceString(record.value('patrName')))
            orgStructureId = forceRef(record.value('orgStructure_id'))
            postId         = forceRef(record.value('post_id'))
            specialityId   = forceRef(record.value('speciality_id'))
            tariffCategoryId = forceRef(record.value('tariffCategory_id'))
            return dict(id = personId,
                        code      = code,
                        lastName  = lastName,
                        firstName = firstName,
                        patrName  = patrName,
                        fullName  = formatNameInt(lastName, firstName, patrName),
                        shortName = formatShortNameInt(lastName, firstName, patrName),
                        postId    = postId,
                        postName  = getPostName(postId),
                        orgStructureId = orgStructureId,
                        orgStructureName = getOrgStructureName(orgStructureId),
                        specialityId   = specialityId,
                        specialityName = getSpecialityName(specialityId),
                        tariffCategoryId = tariffCategoryId,
                        tariffCategoryName = getTariffCategoryName(tariffCategoryId)
                        )
    return {}


def getPersonShortName(personId):
    if personId:
        db = QtGui.qApp.db
        table  = db.table('Person')
        record = db.getRecord(table, 'lastName,firstName,patrName', personId)
        if record:
            lastName     = nameCase(forceString(record.value('lastName')))
            firstName    = nameCase(forceString(record.value('firstName')))
            patrName     = nameCase(forceString(record.value('patrName')))
            return formatShortNameInt(lastName, firstName, patrName)
    return ''


def getPersonChiefs(personId):
    # Список начальников сотрудника
    result = []
    if personId:
        db = QtGui.qApp.db
        stmt = '''
        SELECT Chief.id
        FROM Person
        INNER JOIN rbPost ON rbPost.id = Person.post_id
        INNER JOIN Person AS Chief ON Chief.orgStructure_id = Person.orgStructure_id
        INNER JOIN rbPost AS rbChiefPost ON rbChiefPost.id = Chief.post_id
        WHERE Person.id = %d AND SUBSTR(rbChiefPost.code, 1, 1) in ('1', '2') AND SUBSTR(rbChiefPost.code, 1, 1) <  SUBSTR(rbPost.code, 1, 1)''' % personId
        query = db.query(stmt)
        while query.next():
            result.append( forceRef(query.record().value(0)) )
    return result


def getPersonOrgStructureChiefsToPost(personId):
    # Список начальников сотрудника подразделения по должности
    result = []
    if personId:
        db = QtGui.qApp.db
        table = db.table('Person')
        record = db.getRecordEx(table, [table['orgStructure_id']], [table['id'].eq(personId), table['deleted'].eq(0)])
        orgStructureId = forceRef(record.value('orgStructure_id')) if record else None
        if not orgStructureId:
            return result
        orgStructureIdList = db.getTheseAndParents('OrgStructure', 'parent_id', [orgStructureId])
        stmt = '''
        SELECT Chief.id
        FROM Person
        INNER JOIN rbPost ON rbPost.id = Person.post_id
        INNER JOIN Person AS Chief ON Chief.orgStructure_id IN (%s)
        INNER JOIN rbPost AS rbChiefPost ON rbChiefPost.id = Chief.post_id
        WHERE Person.id = %d AND SUBSTR(rbChiefPost.code, 1, 1) in ('1', '2') AND SUBSTR(rbChiefPost.code, 1, 1) <  SUBSTR(rbPost.code, 1, 1)'''%(u','.join(forceString(orgStructureId) for orgStructureId in orgStructureIdList if orgStructureId), personId)
        query = db.query(stmt)
        while query.next():
            result.append( forceRef(query.record().value(0)) )
    return result


def getPersonOrgStructureChiefs(personId):
    # Список начальников сотрудника подразделения OrgStructure.chief_id (Зав.отделением) #0012515:0045207.
    result = []
    if personId:
        db = QtGui.qApp.db
        table = db.table('Person')
        record = db.getRecordEx(table, [table['orgStructure_id']], [table['id'].eq(personId), table['deleted'].eq(0)])
        orgStructureId = forceRef(record.value('orgStructure_id')) if record else None
        if not orgStructureId:
            return result
        orgStructureIdList = db.getTheseAndParents('OrgStructure', 'parent_id', [orgStructureId])
        stmt = '''
        SELECT OrgStructure.chief_id
        FROM OrgStructure
        WHERE OrgStructure.id IN (%s) AND OrgStructure.chief_id != %d AND OrgStructure.deleted = 0'''%(u','.join(forceString(orgStructureId) for orgStructureId in orgStructureIdList if orgStructureId), personId)
        query = db.query(stmt)
        while query.next():
            result.append( forceRef(query.record().value(0)) )
    return result


# пишу и плачу :(
def getNetIdList(clientSex, clientAge):
    db = QtGui.qApp.db
    recordList = db.getRecordList('rbNet', '*')
    result = []
    for record in recordList:
        net = CSexAgeConstraint()
        net.initByRecord(record)
        if net.applicable(clientSex, clientAge):
            result.append(forceRef(record.value('id')))
    return result


def findOrgStructuresByHouseAndFlat(houseId, flat, orgId, orgStructureId=None, clientSex=None, clientAge=None):
    if houseId:
        db = QtGui.qApp.db
        flatNum = 0
        flatNumFilter = re.compile(r'^(\d+)')
        flatNumPart = flatNumFilter.search(flat)
        if flatNumPart:
            flatNumText = flatNumPart.group(1)
            if flatNumText:
                flatNum = int(flatNumText)

        tableOrgStructure = db.table('OrgStructure')
        tableOrgStructureAddress = db.table('OrgStructure_Address')
        tableOrgAddressHouse = db.table('AddressHouse').alias('OrgAddressHouse')
        tableSrcAddressHouse = db.table('AddressHouse').alias('SrcAddressHouse')
#        tableNet = db.table('rbNet')
        table = tableOrgStructureAddress.innerJoin(tableOrgStructure, tableOrgStructure['id'].eq(tableOrgStructureAddress['master_id']) )
        table = table.innerJoin(tableOrgAddressHouse, tableOrgAddressHouse['id'].eq(tableOrgStructureAddress['house_id']))
        table = table.innerJoin(tableSrcAddressHouse,
                                [
                                  tableSrcAddressHouse['KLADRCode'].eq(tableOrgAddressHouse['KLADRCode']),
                                  tableSrcAddressHouse['KLADRStreetCode'].eq(tableOrgAddressHouse['KLADRStreetCode']),
                                  tableSrcAddressHouse['number'].eq(tableOrgAddressHouse['number']),
                                  tableSrcAddressHouse['corpus'].eq(tableOrgAddressHouse['corpus']),
                                ]
                               )

        cond = [tableOrgStructure['organisation_id'].eq(orgId),
                tableOrgStructureAddress['house_id'].eq(houseId),
                tableOrgStructure['deleted'].eq(0)
               ]
        if flatNum:
            cond.extend([db.joinOr([tableOrgStructureAddress['firstFlat'].eq(0),
                           tableOrgStructureAddress['firstFlat'].le(flatNum),
                          ]),
                         db.joinOr([tableOrgStructureAddress['lastFlat'].eq(0),
                           tableOrgStructureAddress['lastFlat'].ge(flatNum),
                          ])])
        if clientSex or clientAge:
            # пишу и плачу :(
            # альтернатива - закешировать данные о подразделениях на уровне приложения
            # но я всё ещё не готов :(
            netIdList = getNetIdList(clientSex, clientAge)
            netIdListAsStr = ','.join((str(netId) for netId in netIdList))
            if netIdList:
                cond.append('getOrgStructureNetId(OrgStructure.id) in (%s)' % netIdListAsStr)
            else:
                return []
        if orgStructureId:
            cond.append(tableOrgStructure['id'].inlist(getOrgStructureDescendants(orgStructureId)))
        return db.getIdList(table, tableOrgStructureAddress['master_id'].name(), cond)
    return []


def findOrgStructuresByAddress(addressId, orgId, orgStructureId=None, clientAge=None):
    if addressId:
        db = QtGui.qApp.db
        tableAddress  = db.table('Address')
        record = db.getRecord(tableAddress, 'house_id, flat', addressId)
        houseId = record.value('house_id')
        flat = forceStringEx(record.value('flat'))
        return findOrgStructuresByHouseAndFlat(houseId, flat, orgId, orgStructureId, clientAge=clientAge)
    return []


def getOrgStructureName(orgStructureId):
    db = QtGui.qApp.db
    table = db.table('OrgStructure')
    return forceString(db.translate(table,'id',orgStructureId,'code'))


def getOrgStructureFullName(orgStructureId):
    db = QtGui.qApp.db
    table = db.table('OrgStructure')
    names = []
    ids   = set()

    while orgStructureId:
        record = db.getRecord(table, 'code, parent_id', orgStructureId)
        if record:
            names.append(forceString(record.value('code')))
            orgStructureId = forceRef(record.value('parent_id'))
        else:
            orgStructureId = None
        if orgStructureId in ids:
            orgStructureId = None
        else:
            ids.add(orgStructureId)
    return '/'.join(reversed(names))


def getOrgStructureNetId(orgStructureId):
    u'''получить id сети заданного подразделения'''
    if orgStructureId:
        db = QtGui.qApp.db
        stmt = 'SELECT getOrgStructureNetId(%d)'%orgStructureId
        query = db.query(stmt)
        if query.next():
            return forceRef(query.record().value(0))
    else:
        return None


def getOrgStructureIdentification(orgStructureId, urn):
    u'''получить идентификатор подразделения'''
    if orgStructureId:
        db = QtGui.qApp.db
        table = db.table('OrgStructure')
        tmpOrgStructureId = orgStructureId
        while tmpOrgStructureId:
            code = getIdentification('OrgStructure', tmpOrgStructureId, urn, False)
            if code:
                return code
            parentId = forceRef(db.translate(table, 'id', tmpOrgStructureId, 'parent_id'))
            if parentId:
                tmpOrgStructureId = parentId
            else:
                orgId = forceRef(db.translate(table, 'id', orgStructureId, 'organisation_id'))
                code = getIdentification('Organisation', orgId, urn, False)
                if code:
                    return code
                break
        raise CIdentificationException(u'Для OrgStructure.id=%s не задан код в системе %s' % (orgStructureId, urn))
    return None


def getOrgStructures(orgId):
    u'''получить список id подразделений заданной организации'''
    db = QtGui.qApp.db
    table = db.table('OrgStructure')
    return db.getIdList(table, where=table['organisation_id'].eq(orgId))


def getOrgStructureDescendants(orgStructureId):
    u'''получить список id подразделений, вложенных в данное + само подразделение'''
    return QtGui.qApp.db.getDescendants('OrgStructure', 'parent_id', orgStructureId)


def getPersonOrgStructureId(personId):
    u'''получить подразделение сотрудника'''
    db = QtGui.qApp.db
    orgStructureId = None
    if personId:
        tablePerson = db.table('Person')
        recOrgStructure = db.getRecordEx(tablePerson, [tablePerson['orgStructure_id']], [tablePerson['deleted'].eq(0), tablePerson['id'].eq(personId)])
        orgStructureId = forceRef(recOrgStructure.value('orgStructure_id')) if recOrgStructure else None
    return orgStructureId


def getParentOrgStructureId(orgStructureId):
    u'''получить вышестоящее подразделение'''
    db = QtGui.qApp.db
    parentOrgStructureId = None
    if orgStructureId:
        tableOrgStructure = db.table('OrgStructure')
        recOrgStructure = db.getRecordEx(tableOrgStructure, [tableOrgStructure['parent_id']], [tableOrgStructure['deleted'].eq(0), tableOrgStructure['id'].eq(orgStructureId)])
        parentOrgStructureId = forceRef(recOrgStructure.value('parent_id')) if recOrgStructure else None
    return parentOrgStructureId


def getOrgStructureBookkeeperCode(orgStructureId):
    u"""Получает код для бухгалтерии по id отделения"""
    result = ''
    stmt = u"""select IF(length(trim(os.bookkeeperCode))=5, os.bookkeeperCode,
                IF(length(trim(destParent1.bookkeeperCode))=5, destParent1.bookkeeperCode,
                  IF(length(trim(destParent2.bookkeeperCode))=5, destParent2.bookkeeperCode,
                    IF(length(trim(destParent3.bookkeeperCode))=5, destParent3.bookkeeperCode,
                      IF(length(trim(destParent4.bookkeeperCode))=5, destParent4.bookkeeperCode, destParent5.bookkeeperCode)))))
                FROM OrgStructure as os
                left join OrgStructure as destParent1 on destParent1.id = os.parent_id
                left join OrgStructure as destParent2 on destParent2.id = destParent1.parent_id
                left join OrgStructure as destParent3 on destParent3.id = destParent2.parent_id
                left join OrgStructure as destParent4 on destParent4.id = destParent3.parent_id
                left join OrgStructure as destParent5 on destParent5.id = destParent4.parent_id
                where os.id = {0}""".format(orgStructureId)
    query = QtGui.qApp.db.query(stmt)
    if query.first():
        record = query.record()
        if record:
            result = forceString(record.value(0))
    return result


def getOrgStructureListDescendants(orgStructureIdList):
    u'''получить список id подразделений, вложенных в данные + сами подразделения'''
    orgStructureIdSet = set([])
    for orgStructureId in orgStructureIdList:
        orgStructureIdSet |= set(QtGui.qApp.db.getDescendants('OrgStructure', 'parent_id', orgStructureId))
    return list(orgStructureIdSet)


def getOrgStructurePersonIdList(orgStructureId):
    u'''получить список персонала с учётом вложенных подразделений'''
    db = QtGui.qApp.db
    table = db.table('Person')
    orgStructureIdList = getOrgStructureDescendants(orgStructureId)
    return db.getIdList(table, where=table['orgStructure_id'].inlist(orgStructureIdList))


def getOrgStructureAddressIdList(orgStructureId):
    u'''получить список id адресов, которые находятся на территории обслуживания подразделения'''
    if orgStructureId:
        orgStructureIdList = getOrgStructureDescendants(orgStructureId)
    else:
        orgStructureIdList = getOrgStructures(QtGui.qApp.currentOrgId())
    db = QtGui.qApp.db
    tableAddress = db.table('Address')
    tableOrgStructureAddress = db.table('OrgStructure_Address')
    table = tableAddress
    table = table.leftJoin(tableOrgStructureAddress, tableOrgStructureAddress['house_id'].eq(tableAddress['house_id']))
    cond = db.joinOr([
                        tableOrgStructureAddress['lastFlat'].eq(0),
                        db.joinAnd([
                                    tableOrgStructureAddress['firstFlat'].le(tableAddress['flat']),
                                    tableOrgStructureAddress['lastFlat'].ge(tableAddress['flat']),
                                  ])
                    ])
    cond = [tableOrgStructureAddress['master_id'].inlist(orgStructureIdList), cond]
    return db.getIdList(table, tableAddress['id'].name(), where=cond)


def getSolitaryOrgStructureId(orgStructureId):
    u'''получить id обособленного подразделения, в которое входит данное подразделение'''
    db = QtGui.qApp.db
    table = db.table('OrgStructure')
    skipableAddress = None
    while orgStructureId:
        record = db.getRecord(table, 'address, parent_id', orgStructureId)
        parentId = forceRef(record.value('parent_id'))
        address  = forceStringEx(record.value('address'))
        if skipableAddress is None:
            skipableAddress = address
        if parentId is None or address != skipableAddress:
            return orgStructureId
        orgStructureId = parentId
    return None


def getOrgStructureActionTypeIdSet(orgStructureId):
        idSet = set()
        db = QtGui.qApp.db
        tableOSAT = db.table('OrgStructure_ActionType')
        tableActionType = db.table('ActionType')
        table = tableOSAT.innerJoin(tableActionType, tableActionType['id'].eq(tableOSAT['actionType_id']))
        tableOrgStructure = db.table('OrgStructure')
        while orgStructureId:
            cond = [tableOSAT['master_id'].eq(orgStructureId),
                    tableOSAT['actionType_id'].isNotNull(),
                    tableActionType['deleted'].eq(0),
                    tableActionType['showInForm'].ne(0),
                   ]
            idList = db.getIdList(table,
                           tableOSAT['actionType_id'].name(),
                           cond
                           )
            idSet |= set(idList)
            record = db.getRecord(tableOrgStructure, ['parent_id', 'inheritActionTypes'], orgStructureId)
            orgStructureId = forceRef(record.value(0)) if forceBool(record.value(1)) else None
        return idSet


def getActionTypeOrgStructureIdList(actionTypeId, includeInheritance=False):
        db = QtGui.qApp.db
        table = db.table('OrgStructure_ActionType')
        tableOrgStructure = db.table('OrgStructure')

        resultIdList = db.getDistinctIdList(table.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(table['master_id'])),
                                            table['master_id'],
                                            [ table['actionType_id'].eq(actionTypeId),
                                              tableOrgStructure['deleted'].eq(0)
                                            ]
                                           )
        if includeInheritance:
            resultIdSet = set(resultIdList)
            idSet = set(resultIdSet)
            while idSet:
                idList = db.getIdList(tableOrgStructure,
                                      'id',
                                      [ tableOrgStructure['deleted'].eq(0),
                                        tableOrgStructure['master_id'].inlist(idSet),
                                        tableOrgStructure['inheritActionTypes'].eq(1),
                                      ]
                                     )
                idSet = set(idList)-resultIdSet
                resultIdList += list(idSet)
                resultIdSet |= idSet
        return resultIdList



def synchronizePlaceOfBusiness(result, supplierOrgId, inn=None, ogrn=None, kpp=None, chiefName=None):
    db = QtGui.qApp.db

    # Обновляем реквизиты организации сведениями из сервиса МДЛП
    tableOrg = db.table('Organisation')
    orgRecord = db.getRecord(tableOrg, '*', supplierOrgId)
    if not forceString(orgRecord.value('chiefFreeInput')):
        chiefName = u' '.join([result.lastName, result.firstName, result.middleName])
        orgRecord.setValue('chiefFreeInput', chiefName)
    if not forceString(orgRecord.value('KPP')):
        orgRecord.setValue('KPP', result.kpp)
    if not inn:
        orgRecord.setValue('INN', result.inn)
    if not ogrn:
        orgRecord.setValue('OGRN', result.ogrn)
    db.updateRecord(tableOrg, orgRecord)

    # Обновляем идентификатор МДЛП организации сведениями из сервиса МДЛП или не обновляем
    tableRbAS = db.table('rbAccountingSystem')
    mdlpId = QtGui.qApp.db.translate(tableRbAS, 'urn', 'urn:mdlp:anyId', 'id')
    if mdlpId:
        tableOI = db.table('Organisation_Identification')
        cond = [
            tableOI['master_id'].eq(supplierOrgId),
            tableOI['system_id'].eq(mdlpId),
        ]
        identificationRecords = QtGui.qApp.db.getRecordList(tableOI, '*', cond)
        if not identificationRecords:
            record = tableOI.newRecord()
            record.setValue('master_id', toVariant(supplierOrgId))
            record.setValue('system_id', toVariant(mdlpId))
            record.setValue('value', toVariant(result.sysId))
            record.setValue('checkDate', toVariant(QDate.currentDate()))
            db.insertRecord(tableOI, record)
        else:
            hasRec = False
            for record in identificationRecords:
                systemId = forceString(record.value('value'))
                deleted = forceInt(record.value('deleted'))
                if systemId == result.sysId:
                    hasRec = True
                    if deleted:
                        record.setValue('deleted', toVariant(0))
                    else:
                        break
                else:
                    record.setValue('deleted', toVariant(1))
                db.updateRecord(tableOI, record)
            if not hasRec:
                record = tableOI.newRecord()
                record.setValue('master_id', toVariant(supplierOrgId))
                record.setValue('system_id', toVariant(mdlpId))
                record.setValue('value', toVariant(result.sysId))
                record.setValue('checkDate', toVariant(QDate.currentDate()))
                db.insertRecord(tableOI, record)


class CSexAgeConstraint(object):
    def __init__(self):
        self.age = None
        self.sex = None


    def constrain(self):
        return bool(self.age or self.sex)


    def initBySimpleType(self, sex, age):
        self.sex = sex
        self.age = parseAgeSelector(age) if age else None


    def initByRecord(self, record):
        self.initBySimpleType(forceInt(record.value('sex')), forceStringEx(record.value('age')))


    def applicable(self, clientSex, clientAge):
        if self.sex and clientSex != self.sex:
            return False
        if self.age and not checkAgeSelector(self.age, clientAge):
            return False
        return True


class CNet(CSexAgeConstraint):
    def __init__(self, id):
        CSexAgeConstraint.__init__(self)
        db = QtGui.qApp.db
        table = db.table('rbNet')
        record = db.getRecord(table, '*', id)
        if record:
            self.initByRecord(record)
            self.code = forceString(record.value('code'))
            self.name = forceString(record.value('name'))
        else:
            self.code = None
            self.name = None


# ####################################################

class COKFSInfo(CRBInfo):
    tableName = 'rbOKFS'


    def _initByRecord(self, record):
        self._ownership = forceInt(record.value('ownership'))


    def _initByNull(self):
        self._ownership = None

    ownership = property(lambda self: self.load()._ownership)


class COKPFInfo(CRBInfo):
    tableName = 'rbOKPF'


class CNetInfo(CRBInfo):
    tableName = 'rbNet'


    def _initByRecord(self, record):
        self._sexCode = forceInt(record.value('sex'))
        self._age = forceString(record.value('age'))


    def _initByNull(self):
        self._sexCode = 0
        self._age = ''


    sexCode = property(lambda self: self.load()._sexCode)
    sex = property(lambda self: formatSex(self.load()._sexCode))
    age = property(lambda self: self.load()._age)


class COrgInfo(CInfo, CIdentificationInfoMixin):
    tableName = 'Organisation'

    def __init__(self, context, id):
        CInfo.__init__(self, context)
        CIdentificationInfoMixin.__init__(self)
        self.id = id
        self._fullName = ''
        self._shortName = ''
        self._title = ''
        self._net = None
        self._ffoms = ''
        self._tfomsCode = ''
        self._miacCode = ''
        self._usishCode = ''
        self._tfomsExtCode = ''
        self._OKVED = ''
        self._INN = ''
        self._KPP = ''
        self._OGRN = ''
        self._OKATO = ''
        self._OKPF = None
        self._OKFS = None
        self._OKPO = ''
        self._FSS = ''
        self._region = ''
        self._address = None
        self._addressFreeInput = ''
        self._chief = None
        self._chiefFreeInput = ''
        self._phone = ''
        self._mail = ''
        self._accountant = ''
        self._notes = ''
        self._area = ''
        self._areaCode = ''
        self._medicalType = None
        self._identification = self.getInstance(COrgIdentificationInfo, None)
        self._licenses = self.getInstance(COrgLicenseInfoList, None)


    def _load(self):
        from Registry.Utils import CAddressInfo
        from PersonInfo import CPersonInfo
        db = QtGui.qApp.db
        record = db.getRecord('Organisation', '*', self.id) if self.id else None
        if record:
            self._fullName = forceString(record.value('fullName'))
            self._shortName = forceString(record.value('shortName'))
            self._title = forceString(record.value('title'))
            self._net = self.getInstance(CNetInfo, record.value('net_id'))
            self._ffoms = forceString(record.value('smoCode'))
            self._tfomsCode = forceString(record.value('infisCode'))
            self._miacCode = forceString(record.value('miacCode'))
            self._usishCode = forceString(record.value('usishCode'))
            self._tfomsExtCode = forceString(record.value('tfomsExtCode'))
            self._OKVED = forceString(record.value('OKVED'))
            self._INN = forceString(record.value('INN'))
            self._KPP = forceString(record.value('KPP'))
            self._OGRN = forceString(record.value('OGRN'))
            self._OKATO = forceString(record.value('OKATO'))
            self._OKPF = self.getInstance(COKPFInfo, forceRef(record.value('OKPF_id')))
            self._OKFS = self.getInstance(COKFSInfo, forceRef(record.value('OKFS_id')))
            self._OKPO = forceString(record.value('OKPO'))
            self._FSS = forceString(record.value('FSS'))
            self._region = forceString(record.value('region'))
            self._address = self.getInstance(CAddressInfo, forceRef(record.value('address_id')))
            self._addressFreeInput = forceString(record.value('Address'))
            self._chief = self.getInstance(CPersonInfo, forceRef(record.value('chief_id')))
            self._chiefFreeInput = forceString(record.value('chiefFreeInput'))
            self._phone = forceString(record.value('phone'))
            self._mail = forceString(record.value('email'))
            self._accountant = forceString(record.value('accountant'))
            self._notes = forceString(record.value('notes'))
            self._area = self.getKLADRName(forceString(record.value('area')))
            self._areaCode = forceString(record.value('area'))
            self._medicalType = forceInt(record.value('isMedical'))
            self._identification = self.getInstance(COrgIdentificationInfo, self.id)
            self._licenses = self.getInstance(COrgLicenseInfoList, self.id)
            if forceRef(record.value('address_id')) is None:
                self._address = self._addressFreeInput
            return True
        else:
            self._OKPF = self.getInstance(COKPFInfo, None)
            self._OKFS = self.getInstance(COKFSInfo, None)
            self._address = self.getInstance(CAddressInfo, None)
            self._chief = self.getInstance(CPersonInfo, None)
            return False


    def getKLADRName(self, code):
        model = getKladrTreeModel()
        item = model.getRootItem().findCode(code)
        if item and item != model.getRootItem():
            return item._name
        return u''


    def formatChief(self):
        if self.chief.personId:
            return unicode(self.chief)
        return self.chiefFreeInput


#    def __unicode__(self):
    def __str__(self):
        return self.load()._shortName

    fullName    = property(lambda self: self.load()._fullName)
    shortName   = property(lambda self: self.load()._shortName)
    title       = property(lambda self: self.load()._title)
    net         = property(lambda self: self.load()._net)
    ffoms       = property(lambda self: self.load()._ffoms)
    tfomsCode   = property(lambda self: self.load()._tfomsCode)
    miacCode    = property(lambda self: self.load()._miacCode)
    usishCode   = property(lambda self: self.load()._usishCode)
    tfomsExtCode= property(lambda self: self.load()._tfomsExtCode)
    OKVED       = property(lambda self: self.load()._OKVED)
    INN         = property(lambda self: self.load()._INN)
    KPP         = property(lambda self: self.load()._KPP)
    OGRN        = property(lambda self: self.load()._OGRN)
    OKATO       = property(lambda self: self.load()._OKATO)
    OKPF        = property(lambda self: self.load()._OKPF)
    OKFS        = property(lambda self: self.load()._OKFS)
    OKPO        = property(lambda self: self.load()._OKPO)
    FSS         = property(lambda self: self.load()._FSS)
    region      = property(lambda self: self.load()._region)
    address     = property(lambda self: self.load()._address)
    addressFreeInput = property(lambda self: self.load()._addressFreeInput)
    chief       = property(lambda self: self.load()._chief)
    chiefFreeInput = property(lambda self: self.load()._chiefFreeInput)
    phone       = property(lambda self: self.load()._phone)
    mail       = property(lambda self: self.load()._mail)
    accountant  = property(lambda self: self.load()._accountant)
    notes       = property(lambda self: self.load()._notes)
    note        = property(lambda self: self.load()._notes)
    area        = property(lambda self: self.load()._area)
    areaCode        = property(lambda self: self.load()._areaCode)
    medicalType = property(lambda self: self.load()._medicalType)
    infisCode   = property(lambda self: self.load()._tfomsCode)
    identification = property(lambda self: self.load()._identification)
    licenses = property(lambda self: self.load()._licenses)


class COrgIdentificationInfo(CInfo, CDictInfoMixin):
    def __init__(self, context, orgId):
        CInfo.__init__(self, context)
        CDictInfoMixin.__init__(self, '_byCode')
        self._orgId = orgId
        self._nameDict = {}
        self._checkDateDict = {}
        self._byUrn = {}


    def _load(self):
        db = QtGui.qApp.db
        tableOI = db.table('Organisation_Identification')
        tableAS = db.table('rbAccountingSystem')
        queryTable = tableOI.leftJoin(tableAS, tableOI['system_id'].eq(tableAS['id']))
        cols = [ tableAS['code'],
                 tableAS['name'],
                 tableAS['urn'],
                 tableOI['value'],
                 tableOI['checkDate'],
                ]
        cond = [ tableOI['deleted'].eq(0),
                 tableOI['master_id'].eq(self._orgId),
               ]
        query = db.query(db.selectStmt(queryTable, cols, cond))
        while query.next():
            record = query.record()
            code = forceString(record.value('code'))
            self._byCode[code] = forceString(record.value('value'))
            self._nameDict[code] = forceString(record.value('name'))
            self._checkDateDict[code] = CDateInfo(record.value('checkDate'))
            self._byUrn[code] = forceString(record.value('urn'))
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
    checkDateDict = property(lambda self: self.load()._checkDateDict)


class COrgLicenseInfoList(CInfoList):
    def __init__(self, context, orgId):
        CInfoList.__init__(self, context)
        self._orgId = orgId


    def _load(self):
        if not self._orgId:
            return False
        idList = QtGui.qApp.db.getIdList('Organisation_License', 'id', 'master_id = %d' % self._orgId)
        self._items = [ self.getInstance(COrgLicenseInfo, id) for id in idList ]
        return True



class COrgLicenseInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id
        self._number = ''
        self._issuer = ''
        self._issueDate = CDateInfo()
        self._begDate = CDateInfo()
        self._endDate = CDateInfo()


    def _load(self):
        record = QtGui.qApp.db.getRecord('Organisation_License', '*', self.id)
        if record:
            self._number = forceString(record.value('number'))
            self._issuer = forceString(record.value('issuer'))
            self._issueDate = CDateInfo(forceDate(record.value('issueDate')))
            self._begDate = CDateInfo(forceDate(record.value('begDate')))
            self._endDate = CDateInfo(forceDate(record.value('endDate')))
            return True
        return False


    number      = property(lambda self: self.load()._number)
    issuer      = property(lambda self: self.load()._issuer)
    issueDate   = property(lambda self: self.load()._issueDate)
    begDate     = property(lambda self: self.load()._begDate)
    endDate     = property(lambda self: self.load()._endDate)


class COrgStructureInfo(CInfo, CIdentificationInfoMixin):
    tableName = 'OrgStructure'

    def __init__(self, context, id):
        CInfo.__init__(self, context)
        CIdentificationInfoMixin.__init__(self)
        self.id = id
        self._orgStructureId = self.id
        self._name = ''
        self._code = ''
        self._organisation = None
        self._parent = None
        self._net = None
        self._jobs = []
        self._chief = None
        self._headNurse = None
        self._address = None
        self._infisCode = None
        self._infisDepTypeCode = None
        self._infisInternalCode  = None
        self._actionTypes = None
        self._phone = None
        self._note = ''
        self._type = None
        self._bookkeeperCode = None
        self._identification = self.getInstance(COrgStructureIdentificationInfo, None)


    def _load(self):
        from PersonInfo import CPersonInfo

        db = QtGui.qApp.db
        record = db.getRecord('OrgStructure', '*', self.id) if self.id else None
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            parentId = forceRef(record.value('parent_id'))
            self._parent = self.getInstance(COrgStructureInfo, parentId) if parentId else None
            organisationId = forceRef(record.value('organisation_id'))
            self._organisation = self.getInstance(COrgInfo, organisationId) if organisationId else None
            netId = forceRef(record.value('net_id'))
            self._net = self.getInstance(CNetInfo, netId) if netId else None
            self._chief = self.getInstance(CPersonInfo, forceRef(record.value('chief_id')))
            self._headNurse = self.getInstance(CPersonInfo, forceRef(record.value('headNurse_id')))
            self._infisCode = forceString(record.value('infisCode'))
            self._infisInternalCode = forceString(record.value('infisInternalCode'))
            self._infisDepTypeCode = forceString(record.value('infisDepTypeCode'))
            self._note = forceString(record.value('note'))
            self._type = forceString(record.value('type'))
            self._bookkeeperCode = forceString(record.value('bookkeeperCode'))
            self._identification = self.getInstance(COrgStructureIdentificationInfo, self.id)
#            self._jobs =  self.getInstance(COrgStructureJobInfoList, self.id)
            self._jobs = None
            address = forceString(record.value('Address'))
            self._phone = forceString(record.value('phone'))
            if address:
                self._address = address
            return True
        else:
            return False


    def getNet(self):
        self.load()
        if self._net is None:
            if self._parent:
                self._net = self._parent.getNet()
            elif self._organisation:
                self._net = self._organisation.net
            else:
                self._net = self.getInstance(CNetInfo, None)
        return self._address

    def getFullName(self):
#        self.load()
        return getOrgStructureFullName(self.id)


    def getAddress(self):
        self.load()
        if self._address is None:
            if self._parent:
                self._address = self._parent.getAddress()
            elif self._organisation:
                self._address = self._organisation.addressFreeInput
            else:
                self._address = ''
        return self._address


    def getActionTypes(self):
        if self._actionTypes is None:
            from Events.ActionInfo import CActionTypeInfoList
            self._actionTypes = CActionTypeInfoList()
            self._actionTypes.idList = list(getOrgStructureActionTypeIdSet(self.id))
        return self._actionTypes

    def __str__(self):
        return self.getFullName()

    orgStructureId    = property(lambda self: self.load()._orgStructureId)
    code              = property(lambda self: self.load()._code)
    name              = property(lambda self: self.load()._name)
    organisation      = property(lambda self: self.load()._organisation)
    parent            = property(lambda self: self.load()._parent)
    net               = property(getNet)
    jobs               = property(lambda self: self.load()._jobs)
    chief             = property(lambda self: self.load()._chief)
    headNurse         = property(lambda self: self.load()._headNurse)
    infisCode         = property(lambda self: self.load()._infisCode)
    infisInternalCode = property(lambda self: self.load()._infisInternalCode)
    infisDepTypeCode  = property(lambda self: self.load()._infisDepTypeCode)
    fullName          = property(getFullName)
    address           = property(getAddress)
    phone             = property(lambda self: self.load()._phone)
    actionTypes       = property(getActionTypes)
    note              = property(lambda self: self.load()._note)
    type              = property(lambda self: self.load()._type)
    bookkeeperCode              = property(lambda self: self.load()._bookkeeperCode)
    identification  = property(lambda self: self.load()._identification)


class COrgStructureInfoList(CInfoList):
    def __init__(self, context, orgStructureIdList):
        CInfoList.__init__(self, context)
        self.idList = orgStructureIdList


    def _load(self):
        self._items = [ self.getInstance(COrgStructureInfo, id) for id in self.idList ]
        return True


# #####################################################################
class COrgStructureIdentificationInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id
        self._byCode = {}
#        self._byName = {}
        self._nameDict = {}

    def _load(self):
        db = QtGui.qApp.db
        self._code = ''
        self._name = ''
        self._value = ''
        tableCI = db.table('OrgStructure_Identification')
        tableAS = db.table('rbAccountingSystem')
        stmt = db.selectStmt(tableCI.leftJoin(tableAS, tableAS['id'].eq(tableCI['system_id'])),
                             ['code', 'name', 'value'],
                             db.joinAnd([tableCI['master_id'].eq(self.id),
                                         tableCI['deleted'].eq(0),
                                        ])
                            )
        query = db.query(stmt)
        while query.next():
            record = query.record()
            code = forceString(record.value('code'))
            name = forceString(record.value('name'))
            value = forceString(record.value('value'))
            self._byCode[code] = value
#            self._byName[name] = identifier
            self._nameDict[code] = name
            self._code  = forceString(record.value('code'))
            self._name  = forceString(record.value('name'))
            self._value  = forceString(record.value('value'))
        return True


    def has_key(self, key):
        return key in self._byCode


    def get(self, key, default=None):
        return self._byCode.get(key, default)


    def iteritems(self):
        return self._byCode.iteritems()


    def iterkeys(self):
        return self._byCode.iterkeys()


    def itervalues(self):
        return self._byCode.itervalues()


    def items(self):
        return self._byCode.items()


    def keys(self):
        return self._byCode.keys()


    def values(self):
        return self._byCode.values()


    def __nonzero__(self):
        return bool(self._byCode)


    def __len__(self):
        return len(self._byCode)


    def __contains__(self, key):
        return key in self._byCode


    def __getitem__(self, key):
        return self._byCode.get(key, '')


    def __iter__(self):
        return self._byCode.iterkeys()


    def __str__(self):
        self.load()
        l = [ u'%s (%s): %s' % (self._nameDict[code], code, value)
              for code, value in self._byCode.iteritems()
            ]
        l.sort()
        return ', '.join(l)

    byCode = property(lambda self: self.load()._byCode)
#    byName = property(lambda self: self.load()._byName)
    nameDict = property(lambda self: self.load()._nameDict)
    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    value     = property(lambda self: self.load()._value)
    
# #####################################################################
# #####################################################################

class COrgStructure(CDbEntityCache):
    cache = {}

    ostAmb = 0
    ostHospital = 1
    ostFirstAid = 2
    ostFobileStation = 3
    ostEmergencyDepartment = 4

    def __init__(self, orgStructureId):
        self._orgStructureId = orgStructureId

        db = QtGui.qApp.db

        record = db.getRecord('OrgStructure', 'type', orgStructureId)
        if not record:
            from PyQt4.QtSql import QSqlRecord
            record = QSqlRecord()

        self.type = forceInt(record.value('type'))

    @classmethod
    def purge(cls):
        cls.cache.clear()


    @classmethod
    def get(cls, orgStructureId):
        result = cls.cache.get(orgStructureId, None)
        if result is None:
            cls.connect()
            result = COrgStructure(orgStructureId)
            cls.cache[orgStructureId] = result
        return result


class CActivityInfo(CRBInfo):
    tableName = 'rbActivity'


    def _initByRecord(self, record):
        self._regionalCode = forceString(record.value('regionalCode'))
        self._note         = forceString(record.value('note'))


    def _initByNull(self):
        self._regionalCode = self._note = ''


    regionalCode = property(lambda self: self.load()._regionalCode)
    note = property(lambda self: self.load()._note)
