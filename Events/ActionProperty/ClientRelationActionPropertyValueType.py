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

from PyQt4 import QtGui
from PyQt4.QtCore import QVariant

from ActionPropertyValueType  import CActionPropertyValueType
from Registry.Utils           import CClientRelationComboBoxPatronEx, CClientRelationInfo
from library.Utils            import forceRef, forceString, formatShortName


class CClientRelationActionPropertyValueType(CActionPropertyValueType):
    name        = u'Связи пациента'
    variantType = QVariant.Int

    def __init__(self, domain = None):
        CActionPropertyValueType.__init__(self, domain)
        self.action = None
        self.clientId = None


    class CPropEditor(CClientRelationComboBoxPatronEx):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            CClientRelationComboBoxPatronEx.__init__(self, parent)
            self.clientId = clientId
            self.setClientId(self.clientId)

        def setValue(self, value):
            v = forceRef(value)
            CClientRelationComboBoxPatronEx.setValue(self, v)

        def getClientId(self, value):
            v = forceRef(value)
            return CClientRelationComboBoxPatronEx.getClientId(self, v)

        def getRelativeId(self, value):
            v = forceRef(value)
            return CClientRelationComboBoxPatronEx.getRelativeId(self, v)


    def getEditorClass(self):
        return self.CPropEditor


    @classmethod
    def getTableName(cls):
        return cls.tableNamePrefix+'Client_Relation'


    @staticmethod
    def convertDBValueToPyValue(value):
        return forceRef(value)


    convertQVariantToPyValue = convertDBValueToPyValue


    def shownUp(self, action, clientId):
        self.action = action
        self.clientId = clientId


    def toText(self, v):
        name = ''
        value = forceRef(v)
        if value and self.clientId:
            db = QtGui.qApp.db
            tableCR = db.table('ClientRelation')
            tableRT = db.table('rbRelationType')
            tableC  = db.table('Client')
            record = db.getRecordEx(tableCR, [tableCR['id']], [tableCR['id'].eq(value), tableCR['deleted'].eq(0), tableCR['client_id'].eq(self.clientId)])
            colName = 'relative_id' if (record and forceRef(record.value('id'))) else 'client_id'
            queryTable = tableCR
            queryTable = queryTable.leftJoin(tableRT, tableRT['id'].eq(tableCR['relativeType_id']))
            queryTable = queryTable.leftJoin(tableC, tableC['id'].eq(tableCR[colName]))
            cols = ['CONCAT_WS(\' | \', rbRelationType.code, CONCAT_WS(\'->\', rbRelationType.leftName, rbRelationType.rightName)) AS relationType',
                      tableC['lastName'].alias(), tableC['firstName'].name(),
                      tableC['patrName'].name(), tableC['birthDate'].name()
                      ]
            cond = [tableCR['id'].eq(value),
                    tableCR['deleted'].eq(0)
                    ]
            relationRecord = db.getRecordEx(queryTable, cols, cond)
            if relationRecord:
                name = u', '.join([formatShortName(relationRecord.value('lastName'),
                                   relationRecord.value('firstName'),
                                   relationRecord.value('patrName')),
                                   forceString(relationRecord.value('birthDate')),
                                   forceString(relationRecord.value('relationType'))])
        return name


    def toInfo(self, context, v):
        isDirect = False
        if v and self.clientId:
            db = QtGui.qApp.db
            tableCR = db.table('ClientRelation')
            record = db.getRecordEx(tableCR, [tableCR['id']], [tableCR['id'].eq(v), tableCR['deleted'].eq(0), tableCR['client_id'].eq(self.clientId)])
            isDirect = True if (record and forceRef(record.value('id'))) else False
        return context.getInstance(CClientRelationInfo, forceRef(v), isDirect=isDirect)

