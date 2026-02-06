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

from library.Utils import forceRef


class CMapActionTypeIdToServiceIdList:
    def __init__(self):
        self.mapActionTypeIdToServiceIdList = {}

    def mappingActionTypeList(self, actionTypeList, financeId):
        # для массовой загрузки в событиях
        db = QtGui.qApp.db
        table = db.table('ActionType_Service')
        notFoundList = []
        for actionType in set(actionTypeList):
            key = (actionType, financeId)
            if self.mapActionTypeIdToServiceIdList.get(key, None) is None:
                notFoundList.append(actionType)
        if notFoundList:
            records = db.getRecordList(table, cols='master_id, service_id',
                                       where=[table['master_id'].inlist(notFoundList),
                                              table['finance_id'].eq(financeId),
                                              table['service_id'].isNotNull()])
            for record in records:
                key = (forceRef(record.value('master_id')), financeId)
                item = self.mapActionTypeIdToServiceIdList.setdefault(key, set())
                if type(item) == list:
                    item = set(item)
                item.add(forceRef(record.value('service_id')))
                self.mapActionTypeIdToServiceIdList[key] = item

        notFoundList = []
        for actionType in set(actionTypeList):
            key = (actionType, financeId)
            if self.mapActionTypeIdToServiceIdList.get(key, None) is None:
                notFoundList.append(actionType)

        if notFoundList:
            records = db.getRecordList(table, cols='master_id, service_id',
                                       where=[table['master_id'].inlist(notFoundList),
                                              table['finance_id'].isNull(),
                                              table['service_id'].isNotNull()])
            for record in records:
                key = (forceRef(record.value('master_id')), financeId)
                item = self.mapActionTypeIdToServiceIdList.setdefault(key, set())
                if type(item) == list:
                    item = set(item)
                item.add(forceRef(record.value('service_id')))
                self.mapActionTypeIdToServiceIdList[key] = item

        for actionType in actionTypeList:
            key = (actionType, financeId)
            if self.mapActionTypeIdToServiceIdList.get(key, None) is None:
                self.mapActionTypeIdToServiceIdList[key] = []


    def getActionTypeServiceIdList(self, actionTypeId, financeId):
        key = (actionTypeId, financeId)
        result = self.mapActionTypeIdToServiceIdList.get(key, False)
        if result == False:
            db = QtGui.qApp.db
            table = db.table('ActionType_Service')
            result = db.getDistinctIdList(table,
                                          idCol='service_id',
                                          where=[table['master_id'].eq(actionTypeId),
                                                 table['finance_id'].eq(financeId),
                                                 table['service_id'].isNotNull()])
            if not result:
                result = db.getDistinctIdList(table,
                                          idCol='service_id',
                                          where=[table['master_id'].eq(actionTypeId),
                                                 table['finance_id'].isNull(),
                                                 table['service_id'].isNotNull()])
            self.mapActionTypeIdToServiceIdList[key] = result
        return list(result) if type(result) == set else result


    def reset(self):
        self.mapActionTypeIdToServiceIdList = {}
