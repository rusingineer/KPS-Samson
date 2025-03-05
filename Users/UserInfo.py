# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui

from library.Utils import forceString, forceRef
from library.PrintInfo import CRBInfo
from Tables import tblUser, usrName, tblLogin


class CUserProfileInfo(CRBInfo):
    tableName = 'rbUserProfile'


class CUserInfo(object):
    def __init__(self, userId, loginId=None):
        db = QtGui.qApp.db
        record = db.getRecord(tblUser, [usrName, 'userProfile_id'], userId)
        self._userId = userId
        self._login  = forceString(db.translate(tblLogin, 'id', loginId, 'login'))
        self.loginId = loginId
        self._name   = forceString(record.value(usrName))
        self._rights = loadRights(forceRef(record.value('userProfile_id')))
        self._availableJobTypes = CUserAvailableJobTypes(self._userId)


    def availableJobTypeIdList(self):
        return self._availableJobTypes.availableJobTypeIdList()


    def isAvailableJobTypeId(self, jobTypeId):
        return self._availableJobTypes.isAvailableJobTypeId(jobTypeId)


    def isAvailableJobType(self, jobTypeCode):
        return self._availableJobTypes.isAvailableJobType(jobTypeCode)


    def login(self):
        return self._login


    def name(self):
        return self._name


    def hasRight(self, right):
        return right in self._rights


    def hasAnyRight(self, rights):
        for right in rights:
            if self.hasRight(right):
                return True
        return False


class CDemoUserInfo(CUserInfo):
    def __init__(self, userId):
        self._userId = userId
        self._login  = 'demo'
        self._name   = 'demo'
        self._rights = set([])
        self._availableJobTypeIdList = QtGui.qApp.db.getIdList('rbJobType')


    def availableJobTypeIdList(self):
        return self._availableJobTypeIdList


    def hasRight(self, right):
        return True


    def isAvailableJobTypeId(self, jobTypeId):
        return True


    def isAvailableJobType(self, jobTypeCode):
        return True


class CUserAvailableJobTypes(object):
    def __init__(self, userId):
        self._userId = userId

        self._mapJobTypeCodeToId     = {}
        self._availableJobTypeIdList = []

        self._init(userId)


    def clear(self):
        self._mapJobTypeCodeToId.clear()
        self._availableJobTypeIdList = []


    def _init(self, userId):
        assert self._userId == userId

        self.clear()

        db = QtGui.qApp.db
        tablePersonJobType  = db.table('Person_JobType')
        tableJobType        = db.table('rbJobType')

        jobTypeIdList = db.getIdList(tablePersonJobType,
                                     tablePersonJobType['jobType_id'].name(),
                                     tablePersonJobType['master_id'].eq(userId))
        result = set([])
        for jobTypeId in jobTypeIdList:
            result |= set(db.getDescendants(tableJobType,
                                            'group_id',
                                            jobTypeId))
        jobTypeIdList = list(result)

        fields = [tableJobType['code'].name(),
                  tableJobType['id'].name()]
        cond = tableJobType['id'].inlist(jobTypeIdList)

        recordList = db.getRecordList(tableJobType, fields, cond)
        for record in recordList:
            jobTypeId = forceRef(record.value('id'))
            jobTypeCode = forceString(record.value('code'))
            self._mapJobTypeCodeToId[jobTypeCode] = jobTypeId
            self._availableJobTypeIdList.append(jobTypeId)


    def jobTypeId(self, jobTypeCode):
        return self._mapJobTypeCodeToId.get(jobTypeCode, None)


    def isAvailableJobTypeId(self, jobTypeId):
        if self._availableJobTypeIdList:
            return jobTypeId in self._availableJobTypeIdList
        return True


    def isAvailableJobType(self, jobTypeCode):
        jobTypeId = self.jobTypeId(jobTypeCode)
        return self.isAvailableJobTypeId(jobTypeId)


    def availableJobTypeIdList(self):
        return self._availableJobTypeIdList


def loadRights(profileId):
    result = []
    if profileId:
        db = QtGui.qApp.db
        table = db.table('rbUserProfile_Right')
        tableUserRight = db.table('rbUserRight')
        stmt = db.selectStmt(table.leftJoin(tableUserRight,
                                            tableUserRight['id'].eq(table['userRight_id'])
                                           ),
                             [tableUserRight['code']],
                             table['master_id'].eq(profileId)
                            )
        query = db.query(stmt)
        while query.next():
            result.append(forceString(query.record().value('code')))
    return set(result)
