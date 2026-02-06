# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным
# программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4.QtCore import QVariant
from PyQt4 import QtGui

from library.PrintInfo import CRBInfoWithIdentification
from library.crbcombobox import CRBComboBox
from library.Utils import forceRef, forceString, forceDate

from ActionPropertyValueType import CActionPropertyValueType


class CMedicalAidProfileActionPropertyValueType(CActionPropertyValueType):
    name        = u'Профиль МП'
    variantType = QVariant.Int

    class CRBMedicalAidProfileInfo(CRBInfoWithIdentification):
        tableName = 'rbMedicalAidProfile'

    class CPropEditor(CRBComboBox):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            CRBComboBox.__init__(self, parent)
            self.setShowFields(CRBComboBox.showCodeAndName)
            self.setTable('rbMedicalAidProfile')
            self.setFilter(domain)
            filterList = [domain] if domain else []
            db = QtGui.qApp.db
            if action and action.actionType() and (
                    action.actionType().flatCode == u'consultationDirection' or action.actionType().flatCode == u'researchDirection'):
                if u'Куда направляется' in action._actionType._propertiesByName:
                    propertyValue = action[u'Куда направляется']
                    tableRBMAP = db.table('rbMedicalAidProfile')
                    tableOrganisation = db.table('Organisation')
                    tableOMAP = db.table('Organisation_MedicalAidProfile')
                    record = action.getRecord()
                    directionDate = forceDate(record.value('directionDate')) if record else None
                    cond = [tableOrganisation['deleted'].eq(0),
                            tableOMAP['medicalAidProfile_id'].isNotNull()
                            ]
                    if action.actionType().flatCode == u'researchDirection':
                        filterList.append(tableRBMAP['federalCode'].inlist([85, 86, 87, 88]))
                    else:
                        filterList.append(tableRBMAP['federalCode'].notInlist([85, 86, 87, 88]))
                    if propertyValue:
                        cond.append(tableOMAP['master_id'].eq(propertyValue))
                    if directionDate:
                        cond.append(
                            db.joinOr([tableOMAP['begDate'].isNull(), tableOMAP['begDate'].dateLe(directionDate)]))
                        cond.append(
                            db.joinOr([tableOMAP['endDate'].isNull(), tableOMAP['endDate'].dateGe(directionDate)]))
                    queryTable = tableOrganisation.innerJoin(tableOMAP,
                                                             tableOMAP['master_id'].eq(tableOrganisation['id']))
                    idList = db.getDistinctIdList(queryTable, [tableOMAP['medicalAidProfile_id']], cond)
                    filterList.append(tableRBMAP['id'].inlist(idList))
            self.setFilter(db.joinAnd(filterList))

        def setValue(self, value):
            CRBComboBox.setValue(self, forceRef(value))

    def __init__(self, domain=None):
        CActionPropertyValueType.__init__(self, domain)
        self.rawDomain = domain
        self.domain = self.parseDomain(domain)

    def parseDomain(self, domain):
        codeList = []
        for word in domain.split(','):
            if word:
                parts = word.split(':')
                if len(parts) == 1:
                    key, val = u'код', parts[0].strip()
                elif len(parts) == 2:
                    key, val = parts[0].strip(), parts[1].strip()
                else:
                    raise ValueError, self.badDomain % locals()
                keylower = key.lower()
                vallower = val.lower()
                if keylower == u'код':
                    codeList.extend(vallower.split(';'))
                else:
                    raise ValueError, self.badKey % locals()

        db = QtGui.qApp.db
        table = db.table('rbMedicalAidProfile')
        cond = []
        if codeList:
            cond.append(table['code'].inlist(codeList))
        return db.joinAnd(cond)

    @staticmethod
    def convertDBValueToPyValue(value):
        return forceRef(value)

    convertQVariantToPyValue = convertDBValueToPyValue

    def toText(self, v):
        return forceString(QtGui.qApp.db.translate('rbMedicalAidProfile', 'id', v, 'CONCAT(code,\' | \',name)'))

    def toInfo(self, context, v):
        return CMedicalAidProfileActionPropertyValueType.CRBMedicalAidProfileInfo(context, v)


    @classmethod
    def getTableName(cls):
        return cls.tableNamePrefix + 'Integer'
