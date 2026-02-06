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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate

from library.crbcombobox import CRBComboBox
from library.Utils import forceBool, forceRef

from Utils import getOrgStructureDescendants


class CPersonComboBox(CRBComboBox):
    def __init__(self, parent, specialityPresent=True):
        CRBComboBox.__init__(self, parent)
        self._tableName = 'vrbPersonWithSpecialityAndPost'
        self._addNone = True
        self._orgId = QtGui.qApp.currentOrgId()
        self._orgStructureId = None
        self._orgStructureIdList = None
        self._personIdList = []
        self._specialityId = None
        self._specialityPresent = specialityPresent
        self._postId = None
        self._begDate = None
        self._endDate = None
        self._retireDate = None
        self._deallocatedPerson = None
        self._customFilter = None
        self._propertyOrgStructure = False
        self.setOrderByName()
        if self._tableName:
            CRBComboBox.setTable(self, self._tableName, self._addNone, self.compileFilter(), self._order)
        self.setBegDate(QDate.currentDate())


    def currentPersonSpecialityId(self):
        personId = self.value()
        if personId:
            return forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
        return None


    def setTable(self, tableName, addNone=True, filter='', order=None):
        assert False


    def setAddNone(self, addNone=True):
        if self._addNone != addNone:
            self._addNone = addNone
            self.updateFilter()


    def setOrgId(self, orgId):
        if self._orgId != orgId:
            self._orgId = orgId
            self.updateFilter()


    def setOrgStructureId(self, orgStructureId, propertyOrgStructure=False):
        if forceBool(QtGui.qApp.preferences.appPrefs.get('personFilterInCmb', True)):
            self._propertyOrgStructure = propertyOrgStructure
            currOrgStructureId = QtGui.qApp.currentOrgStructureId()
            if currOrgStructureId:
                db = QtGui.qApp.db
                orgStructureIdList = db.getDescendants(db.table('OrgStructure'), 'parent_id', currOrgStructureId)
                if orgStructureIdList:
                    if orgStructureId and orgStructureId in orgStructureIdList:
                        self.updateFilterOrgStructure(orgStructureId)
                    else:
                        self.updateFilterOrgStructure(None)
                else:
                    self.updateFilterOrgStructure(orgStructureId)
            else:
                self.updateFilterOrgStructure(orgStructureId)

    def setOrgStructureList(self, orgStructureIdList):
        self._orgStructureIdList = orgStructureIdList
        self.updateFilter()

    def setPersonIdList(self, personIdList):
        self._personIdList = personIdList
        self.updateFilter()

    def updateFilterOrgStructure(self, orgStructureId):
        if self._orgStructureId != orgStructureId:
            self._orgStructureId = orgStructureId
            if orgStructureId:
                idList = getOrgStructureDescendants(orgStructureId)
            else:
                idList = None
            if self._orgStructureIdList != idList:
                self._orgStructureIdList = idList
                self.updateFilter()

    
    def keyPressEvent(self, event):  # В базах у сотрудника "Интернет" code пустой, поэтому вместо пустого поля, при нажатии Del или Backspace устанавливался Интернет
        if self.isReadOnly():
            event.accept()
        else:
            key = event.key()
            if key == Qt.Key_Delete:
                self.setCurrentIndex(0)
                event.accept()
            elif key == Qt.Key_Backspace:  # BS
                self._searchString = self._searchString[:-1]
                if self._searchString == '':
                    self.setCurrentIndex(0)
                else:
                    self.lookup()
                event.accept()
            else:
                CRBComboBox.keyPressEvent(self, event)
    

    def setDeallocatedPerson(self, deallocatedPerson):
        self._deallocatedPerson = deallocatedPerson
        if self._deallocatedPerson:
            self.setBegDate(QDate())
        else:
            self.setBegDate(QDate.currentDate())


    def setSpecialityId(self, specialityId):
        if self._specialityId != specialityId:
            self._specialityId = specialityId
            self.updateFilter()


    def setSpecialityPresent(self, specialityPresent):
        if self._specialityPresent != specialityPresent:
            self._specialityPresent = specialityPresent
            self.updateFilter()


    def _updateRetireDate(self):
        if self._endDate:
            retireDate = self._endDate  # self._endDate.addMonths(-1)
        elif self._begDate:
            retireDate = self._begDate
        else:
            retireDate = None
        if self._retireDate != retireDate:
            self._retireDate = retireDate
            self.updateFilter()


    def setBegDate(self, begDate):
        if self._begDate != begDate:
            self._begDate = QDate(begDate) if begDate else QDate()
            self._updateRetireDate()


    def setEndDate(self, endDate):
        if self._endDate != endDate:
            self._endDate = QDate(endDate) if endDate else QDate()
            self._updateRetireDate()


    def setFilter(self, filter, needCache=True):
        if self._customFilter != filter:
            self._customFilter = filter
            self.updateFilter(needCache=needCache)


    def compileFilter(self):
        if not QtGui.qApp.db:
            QtGui.qApp.openDatabase()
        db = QtGui.qApp.db
        table = db.table(self._tableName)
        cond = []
        if self._orgId:
            cond.append(table['org_id'].eq(self._orgId))
        if self._orgStructureIdList:
            cond.append(table['orgStructure_id'].inlist(self._orgStructureIdList))
        if self._personIdList:
            cond.append(table['id'].inlist(self._personIdList))
        if self._specialityId:
            if isinstance(self._specialityId, list):
                cond.append(table['speciality_id'].inlist(self._specialityId))
            else:
                cond.append(table['speciality_id'].eq(self._specialityId))
        elif self._specialityPresent:
            cond.append(table['speciality_id'].isNotNull())
        if self._postId:
            if isinstance(self._postId, list):
                cond.append(table['post_id'].inlist(self._postId))
            else:
                cond.append(table['post_id'].eq(self._postId))
        if self._retireDate:
            cond.append(db.joinOr([table['retireDate'].isNull(), table['retireDate'].ge(self._retireDate)]))
        if self._customFilter:
            cond.append(self._customFilter)
        return db.joinAnd(cond)


    def updateFilter(self, needCache=True):
        v = self.value()
        CRBComboBox.setTable(self, self._tableName, self._addNone, self.compileFilter(), self._order, needCache=needCache)
        self.setValue(v)


    def setOrderByCode(self):
        self._order = 'code, name'


    def setOrderByName(self):
        self._order = 'name, code'


    def tableName(self):
        return self._tableName