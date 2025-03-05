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
from PyQt4.QtCore import QVariant, SIGNAL

from Orgs.OrgStructComboBoxes import COrgStructureComboBox
from Orgs.Utils               import getOrgStructureFullName, COrgStructureInfo

from library.Utils            import forceRef
from Events.Utils            import getEventAidTypeCode

from ActionPropertyValueType       import CActionPropertyValueType



class COrgStructureActionPropertyValueType(CActionPropertyValueType):
    name        = 'OrgStructure'
    variantType = QVariant.Int
    badDomain   = u'Неверное описание области определения значения свойства действия типа OrgStructure:\n%(domain)s'
    badKey      = u'Недопустимый ключ "%(key)s" в описание области определения значения свойства действия типа OrgStructure:\n%(domain)s'
    badValue    = u'Недопустимое значение "%(val)s" ключа "%(key)s" в описание области определения значения свойства действия типа OrgStructure:\n%(domain)s'


    class CPropEditor(COrgStructureComboBox):
        __pyqtSignals__ = ('commit()',
                          )
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            # db = QtGui.qApp.db
            # finalCond = domain[:]
            # code = getEventAidTypeCode(eventTypeId)
            # if code == '7':
            #     tableOS = db.table('OrgStructure')
            #     tableHB = db.table('OrgStructure_HospitalBed').alias('OSHB')
            #     tableBS = db.table('rbHospitalBedShedule').alias('rbHBS')
            #     table = tableHB.innerJoin(tableBS, tableBS['id'].eq(tableHB['schedule_id']))
            #     cond = [tableHB['master_id'].eq(tableOS['id']),
            #                 tableBS['code'].ne('1')]
            #     finalCond.append(db.existsStmt(table, cond))
            self.action = action
            if self.action.getType().flatCode == 'moving':
                self.oldValueOtdPreb = self.action[u'Отделение пребывания']
            COrgStructureComboBox.__init__(self, parent, None, None, domain)

        def setValue(self, value):
            COrgStructureComboBox.setValue(self, forceRef(value))
            if self.action.getType().flatCode == 'moving':
                if self.oldValueOtdPreb != self.action[u'Отделение пребывания']:
                    try:
                        self.action[u'койка'] = None
                    except Exception:
                        pass
                self.oldValueOtdPreb = self.action[u'Отделение пребывания']


        def emitValueChanged(self):
            self.emit(SIGNAL('commit()'))


    def __init__(self, domain = None):
        CActionPropertyValueType.__init__(self, domain)
        self.domain = self.parseDomain(domain)


    def parseDomain(self, domain):
        db = QtGui.qApp.db
        orgStructureType = None
        orgStructureTypeList = [u'амбулатория',u'стационар',u'скорая помощь',u'мобильная станция',u'приемное отделение стационара']
        netCodes = []
        orgStructureCode = ''
        orgStructureCodes = []
        orgStructureIdList = []
        orgStructureId = None
        isBeds = 0
        isStock = 0
        isFilter = False
        val = ''
        for word in domain.split(','):
            if word:
                parts = word.split(':')
                if len(parts) == 1:
                    key = parts[0].strip()
                elif len(parts) == 2:
                    key, val = parts[0].strip(), parts[1].strip()
                else:
                    raise ValueError, self.badDomain % locals()
                keylower = key.lower()
                vallower = val.lower()
                if keylower == u'код':
                    orgStructureCodes.extend(vallower.split(';'))
                elif keylower == u'тип':
                    if vallower in orgStructureTypeList:
                        orgStructureType = orgStructureTypeList.index(vallower)
                    else:
                        raise ValueError, self.badValue % locals()
                elif keylower == u'сеть':
                    netCodes.append(val)
                elif keylower == u'имеет койки':
                    isBeds = 1
                elif keylower == u'имеет склад':
                    isStock = 1
                else:
                    raise ValueError, self.badKey % locals()
        db = QtGui.qApp.db
        table = db.table('OrgStructure')
        cond = []
        if isBeds:
            cond.append(table['hasHospitalBeds'].eq(isBeds))
            isFilter = True
        if isStock:
            cond.append(table['hasStocks'].eq(isStock))
            isFilter = True
        if orgStructureType is not None:
            cond.append(table['type'].eq(orgStructureType))
            isFilter = True
        if orgStructureCodes:
            isFilter = True
            orgStructureList = []
            parentIdList = db.getDistinctIdList(table, ['id'], [table['deleted'].eq(0), table['code'].inlist(orgStructureCodes)])
            for orgStructureId in parentIdList:
                orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
                if orgStructureIdList:
                    orgStructureList.extend(orgStructureIdList)
            if orgStructureList:
                cond.append(table['id'].inlist(orgStructureList))
        if netCodes:
            isFilter = True
            tableNet = db.table('rbNet')
            contNet  = [ tableNet['code'].inlist(netCodes), tableNet['name'].inlist(netCodes)]
            netIdList = db.getIdList(tableNet, 'id', db.joinOr(contNet))
            cond.append(table['net_id'].inlist(netIdList))
        cond.append(table['deleted'].eq(0))
        cond.append(table['organisation_id'].eq(QtGui.qApp.currentOrgId()))
        idList = db.getIdList(table, 'OrgStructure.id', cond)
        theseAndParentIdList = []
        if idList:
            theseAndParentIdList = db.getTheseAndParents('OrgStructure', 'parent_id', idList)
        cond = []
        if theseAndParentIdList or isFilter:
            cond.append(table['id'].inlist(theseAndParentIdList if theseAndParentIdList else []))
            cond.append(table['deleted'].eq(0))
            cond.append(table['organisation_id'].eq(QtGui.qApp.currentOrgId()))
            return cond
        return []


    @staticmethod
    def convertDBValueToPyValue(value):
        return forceRef(value)


    convertQVariantToPyValue = convertDBValueToPyValue


    def toText(self, v):
        return getOrgStructureFullName(forceRef(v))


    def toInfo(self, context, v):
        return context.getInstance(COrgStructureInfo, forceRef(v))

