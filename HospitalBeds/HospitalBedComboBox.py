# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QVariant

from library.TreeComboBox import CTreeComboBox, CTreeComboBoxGetIdSetIdMixin
from library.TreeModel   import CTreeItemWithId, CTreeModel
from library.AgeSelector import convertAgeSelectorToAgeRange, parseAgeSelector
from library.Utils       import forceBool, forceDate, forceInt, forceRef, forceString, toVariant


class CHospitalBedTreeItem(CTreeItemWithId):
    def __init__(self, parent, id, code, name, isBusy, isPermanent):
        CTreeItemWithId.__init__(self, parent, name, id)
        self._code = code
        self._isBusy = isBusy
        self._isPermanent = isPermanent
        self._items = []


    def flags(self):
        return Qt.NoItemFlags if self._isBusy == 2 else (Qt.ItemIsEnabled | Qt.ItemIsSelectable)


    def data(self, column):
        if column == 0:
            s = self._name
            return toVariant(s)
        else:
            return QVariant()


    def sortItems(self):
        pass


    def sortKey(self):
        return (2, not self._isPermanent, self._isBusy, self._code, self._name, self._id)


class CHospitalBedOrgStructureTreeItem(CTreeItemWithId):
    def __init__(self, parent, name):
        CTreeItemWithId.__init__(self, parent, name, None)
        self._items = []

    def flags(self):
        return Qt.ItemIsEnabled

    def sortItems(self):
        self._items.sort(key=lambda item: item.sortKey())
        for item in self._items:
            item.sortItems()

    def sortKey(self):
        return (1, self._name)


class CHospitalBedRootTreeItem(CTreeItemWithId):
    def __init__(self, filter = {}):
        CTreeItemWithId.__init__(self, None, '-', None)
        self._classesVisible = False
        self.filter = filter
        self.domain = self.filter.get('domain', '')
        self.plannedEndDate = self.filter.get('plannedEndDate', QDate())
        self.begDateAction =  self.filter.get('begDateAction', QDate())
        self.orgStructureId = self.filter.get('orgStructureId', None)
        self.eventTypeId = self.filter.get('eventTypeId', None)
        self.currentAge = self.filter.get('currentAge', 0)


    def loadChildren(self):
        mapOrgStructureIdToTreeItem = {}
        result = []
        orgStructureIdList = []
        mapOrgStructureRecords = {}
        def getOrgStructureTreeItem(orgSructureId):
            if orgSructureId in mapOrgStructureIdToTreeItem:
                item = mapOrgStructureIdToTreeItem[orgSructureId]
            else:
                record = mapOrgStructureRecords.get(orgSructureId, None)
                name = forceString(record.value('name'))
                parentId = forceRef(record.value('parent_id'))
                if parentId:
                    parentItem = getOrgStructureTreeItem(forceString(parentId))
                    item = CHospitalBedOrgStructureTreeItem(parentItem, name)
                    parentItem._items.append(item)
                else:
                    parentItem = self
                    item = CHospitalBedOrgStructureTreeItem(parentItem, name)
                    result.append(item)
                mapOrgStructureIdToTreeItem[orgSructureId] = item
            return item
        db = QtGui.qApp.db
        if self.orgStructureId:
            orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', self.orgStructureId)

        tableHospitalBed = db.table('vHospitalBed')
        tableInvolution = db.table('OrgStructure_HospitalBed_Involution')
        tableOrgStructure = db.table('OrgStructure')
        tableHospitalBedShedule = db.table('rbHospitalBedShedule')

        recList = QtGui.qApp.db.getRecordList('OrgStructure', 'name, parent_id, id', tableOrgStructure['organisation_id'].eq(QtGui.qApp.currentOrgId()))
        for rec in recList:
            mapOrgStructureRecords[forceString(rec.value('id'))] = rec

        table = tableHospitalBed.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tableHospitalBed['master_id']) )
        table = table.leftJoin(tableHospitalBedShedule, tableHospitalBedShedule['id'].eq(tableHospitalBed['schedule_id']))
        joinCond = [
            tableInvolution['master_id'].eq(tableHospitalBed['id']),
        ]
        if self.begDateAction:
            joinCond.append('\'%s\' BETWEEN OrgStructure_HospitalBed_Involution.begDate AND OrgStructure_HospitalBed_Involution.endDate'%self.begDateAction.toString('yyyy-MM-dd'))
        table = table.leftJoin(tableInvolution, db.joinAnd(joinCond))
        
        if orgStructureIdList:
            cond = [tableOrgStructure['id'].inlist(orgStructureIdList)]
        else:
            cond = [tableOrgStructure['organisation_id'].eq(QtGui.qApp.currentOrgId())]
        # if self.eventTypeId:
        #     cond.append(u'''IF(EXISTS(SELECT EventType.id FROM EventType WHERE EventType.id = %s AND
        #                 EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id FROM rbMedicalAidType WHERE rbMedicalAidType.code IN ('7'))),
        #                 (vHospitalBed.schedule_id IS NULL OR rbHospitalBedShedule.code IN ('2', '3', '4', '5')), (vHospitalBed.schedule_id IS NULL OR rbHospitalBedShedule.code IN ('1')))''' % (forceString(self.eventTypeId)))
        sex = self.filter.get('sex', 0)
        if sex:
            cond.append(db.joinOr([tableHospitalBed['sex'].eq(sex), tableHospitalBed['sex'].eq(0)]))
        ageForBed = self.filter.get('ageForBed', 0)
        ageToBed = self.filter.get('ageToBed', 0)
        hospitalBedProfileId = self.filter.get('hospitalBedProfileId', None)
        if hospitalBedProfileId:
            cond.append(tableHospitalBed['profile_id'].eq(hospitalBedProfileId))
        typeBed = self.filter.get('typeBed', None)
        if typeBed:
            cond.append(tableHospitalBed['type_id'].eq(typeBed))
        isPermanentBed = self.filter.get('isPermanentBed', 0)
        if isPermanentBed:
            cond.append(tableHospitalBed['isPermanent'].eq(isPermanentBed-1))
        cond.append(tableOrgStructure['deleted'].eq(0))
        cols = [tableHospitalBed['id'],
                tableHospitalBed['code'],
                tableHospitalBed['name'],
                tableHospitalBed['begDate'],
                tableHospitalBed['endDate'],
                tableHospitalBed['master_id'],
                tableHospitalBed['isBusy'],
                tableInvolution['involutionType'],
                tableHospitalBed['sex'],
                tableHospitalBed['age'],
                tableHospitalBed['isPermanent']]
        query = db.query(db.selectStmt(table, cols, where=cond, order=tableHospitalBed['code'].name()))
        while query.next():
            record = query.record()
            age = forceString(record.value('age'))
            begAge, endAge = convertAgeSelectorToAgeRange(parseAgeSelector(age))
            begDate = forceDate(record.value('begDate'))
            endDate = forceDate(record.value('endDate'))
            involution = forceInt(record.value('involutionType'))
            if (ageForBed or ageToBed) and ageForBed <= ageToBed:
                if endAge >= ageForBed and begAge <= ageToBed:
                    pass
                elif not begAge and not endAge:
                    pass
                else:
                    continue
            if self.currentAge is not None:
                if (begAge or endAge) and self.currentAge >= begAge and self.currentAge <= endAge:
                    pass
                else:
                    continue
            if self.begDateAction:
                if begDate and begDate > self.begDateAction or endDate and endDate < self.begDateAction:
                    continue
            if involution > 0:
                continue
            id   = forceInt(record.value('id'))
            code = forceString(record.value('code'))
            name = forceString(record.value('name'))
            isBusy = forceInt(record.value('isBusy'))
            sex = forceInt(record.value('sex'))
            isPermanent = u'[ш] 'if forceBool(record.value('isPermanent')) else u'[]'
            orgSructureId = forceString(record.value('master_id'))
            orgSructureItem = getOrgStructureTreeItem(orgSructureId)
            if isBusy and self.plannedEndDate and self.domain == u'busy':
                isBusy = self.getBusiForPlanning(isBusy, id)
            strSexAge = isPermanent + code + u' | ' + name
            sexage = u'('
            if sex:
                sexage += [u'', u'М', u'Ж'][sex] + (u', ' if age else '')
            if age:
                sexage += age
            if sex or age:
               strSexAge = isPermanent + code + name + sexage + u')'
            name = strSexAge
            orgSructureItem._items.append(CHospitalBedTreeItem(orgSructureItem, id, code, name, isBusy, forceBool(record.value('isPermanent'))))
        result.sort(key=lambda item: item._name)
        for item in result:
            item.sortItems()
        return result


    def getBusiForPlanning(self, isBusy, hospitalBedId = None):
        if hospitalBedId:
            db = QtGui.qApp.db
            tableAPHB = db.table('ActionProperty_HospitalBed')
            tableAPT = db.table('ActionPropertyType')
            tableAP = db.table('ActionProperty')
            tableActionType = db.table('ActionType')
            tableAction = db.table('Action')
            tableOSHB = db.table('OrgStructure_HospitalBed')
            cols = [tableAction['id']]
            queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
            queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))

            cond = [ tableOSHB['id'].eq(hospitalBedId),
                     tableActionType['flatCode'].like(u'moving%'),
                     tableAction['deleted'].eq(0),
                     tableAP['deleted'].eq(0),
                     tableActionType['deleted'].eq(0),
                     tableAPT['typeName'].like('HospitalBed'),
                     tableAP['action_id'].eq(tableAction['id'])
                   ]
            cond.append(u'Action.plannedEndDate IS NOT NULL')
            cond.append(tableAction['plannedEndDate'].eq(self.plannedEndDate))
            records = db.getIdList(queryTable, cols, cond)
            if records != []:
                return False
        return isBusy


class CHospitalBedModel(CTreeModel):
    def __init__(self, parent=None, filter={}):
        CTreeModel.__init__(self, parent, CHospitalBedRootTreeItem(filter))

    def data(self, index, role):
        if index.isValid() and role in (Qt.DisplayRole, Qt.EditRole):
            item = index.internalPointer()
            if item:
                return item.data(index.column())
        if role == Qt.BackgroundColorRole:
            item = index.internalPointer()
            if item and hasattr(item, '_isBusy') and item._isBusy == 1:
                return toVariant(QtGui.QColor(255, 250, 205))
        return QVariant()


#    def headerData(self, section, orientation, role):
#        if role == Qt.DisplayRole:
#            return QVariant(u'-')
#        return QVariant()


class CHospitalBedComboBox(CTreeComboBoxGetIdSetIdMixin, CTreeComboBox):
    def __init__(self, parent):
        CTreeComboBox.__init__(self, parent)
        self.SizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
        self._model = CHospitalBedModel(self)
        self.setModel(self._model)
