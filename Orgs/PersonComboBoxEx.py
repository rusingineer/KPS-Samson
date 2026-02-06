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
from PyQt4.QtCore import QDate, QVariant, SIGNAL

from library.InDocTable import CInDocTableCol
from library.Utils import forceInt, forceString, toVariant, forceBool, forceRef

from PersonComboBox import CPersonComboBox
from PersonComboBoxExPopup import CPersonComboBoxExPopup
from library.database import CTableRecordCache


class CPersonComboBoxEx(CPersonComboBox):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                      )

    def __init__(self, parent=None, specialityPresent=False):
        CPersonComboBox.__init__(self, parent, specialityPresent)
        self._popup = None
        self.personId = None
        self.date = QDate.currentDate()
        self.orgStructureId = None
        self.orgStructureIdList = []
        self.personIdList = []
        self.organisationId = None
        self.activityCode = None
        self.postCode = None
        self.userId = None
        self.specialityCode = None
        self.specialityId = None
        self._specialValueCount = 0
        self.onlyDoctorsIfUnknowPost = False
        self.defaultOrgStructureId = False
        appPrefs = QtGui.qApp.preferences.appPrefs
        onlyDoctors = forceBool(appPrefs.get('onlyDoctorsInPopup', False))
        self.isOnlyDoctors = onlyDoctors


    def getActualEmptyRecord(self):
        self._createPopup()
        return self._popup.getActualEmptyRecord()


    def addNotSetValue(self):
        record = self.getActualEmptyRecord()
        record.setValue('code', QVariant(u'----'))
        record.setValue('name', QVariant(u'Значение не задано'))
        self.setSpecialValues(((-1, record), ))


    def setSpecialValues(self, specialValues):
        self._createPopup()
        self._popup.setSpecialValues(specialValues)
        sv = []
        for id, record in specialValues:
            sv.append((id, forceString(record.value('code')), forceString(record.value('name'))))
        CPersonComboBox.setSpecialValues(self, sv)
        self._specialValueCount = len(sv)


    def _createPopup(self):
        if not self._popup:
            self._popup = CPersonComboBoxExPopup(self)
            self.connect(self._popup, SIGNAL('personIdSelected(int)'), self.setValue)
            self.connect(self._popup, SIGNAL('orgStructureIdChanged(int, bool)'), self.setOrgStructureId)
            self.connect(self._popup, SIGNAL('specialityIdChanged(int)'), self.setSpecialityId)
            self.connect(self._popup, SIGNAL('deallocatedPersonChecked(bool)'), self.setDeallocatedPerson)
            if self.defaultOrgStructureId is not False:
                self._popup.cmbOrgStructure.setValue(self.defaultOrgStructureId)
            self._popup.setOnlyDoctorsIfUnknowPost(self.onlyDoctorsIfUnknowPost)
            self._popup.setOnlyDoctors(self.isOnlyDoctors)
            self._popup.setPersonIdList(self.personIdList, id)
            self._popup.setOrgStructureList(self.orgStructureIdList)
            # self._popup.initModel(self.value())


    def showPopup(self):
        if not self.isReadOnly():
            self._createPopup()
            self._popup.setFilter(self._customFilter)
            pos = self.rect().bottomLeft()
            pos = self.mapToGlobal(pos)
            size = self._popup.sizeHint()
            screen = QtGui.QApplication.desktop().availableGeometry(pos)
            size.setWidth(screen.width())
            pos.setX(max(min(pos.x(), screen.right()-size.width()), screen.left()))
            pos.setY(max(min(pos.y(), screen.bottom()-size.height()), screen.top()))
            self._popup.move(pos)
            self._popup.resize(size)
            #if self.personIdList:
            self._popup.setPersonEventIdList(self.personIdList, id)
            self._popup.setOrgStructureList(self.orgStructureIdList)
            if self.organisationId:
                self._popup.cmbOrganisation.setValue(self.organisationId)
            if self.orgStructureId:
                if forceBool(QtGui.qApp.preferences.appPrefs.get('personFilterInCmb', True)) and not self.propertyOrgStructure:
                    currOrgStructureId = QtGui.qApp.currentOrgStructureId()
                    if currOrgStructureId:
                        self._popup.cmbOrgStructure.model().setRootItemVisible(False)
                        db = QtGui.qApp.db
                        tableOS = db.table('OrgStructure')
                        orgStructureIdList = db.getDescendants(tableOS, 'parent_id', currOrgStructureId)
                        self._popup.cmbOrgStructure.setFilter(tableOS['id'].inlist(orgStructureIdList) if orgStructureIdList else '')
                self._popup.setPropertyOrgStructure(self.propertyOrgStructure)
                self._popup.cmbOrgStructure.setValue(self.orgStructureId)
            elif hasattr(self, 'propertyOrgStructure') and self.propertyOrgStructure:
                self._popup.setPropertyOrgStructure(self.propertyOrgStructure)
                self._popup.cmbOrgStructure.setValue(self.orgStructureId)
            elif self.orgStructureIdList:
                db = QtGui.qApp.db
                tableOS = db.table('OrgStructure')
                self._popup.cmbOrgStructure.setFilter(tableOS['id'].inlist(self.orgStructureIdList))
            else:
                self._popup.cmbOrgStructure.setFilter('')
                self._popup.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
            if self.postCode:
                self._popup.cmbPost.setCode(self.postCode)
            if self.activityCode:
                self._popup.cmbActivity.setCode(self.activityCode)
            if self.specialityId:
                self._popup.cmbSpeciality.setValue(self.specialityId)
            elif self.specialityCode:
                self._popup.cmbSpeciality.setCode(self.specialityCode)
            self._popup.setRetireDate(self._retireDate)
            self._popup.setDate(self.date)
            self._popup.setPersonId(self.value())
            if self.userId:
                self._popup.setUserId(self.userId)
            self._popup.show()


    def setOrganisationId(self, orgId):
        self.organisationId = orgId
        CPersonComboBox.setOrgId(self, orgId)


    def setOrgStructureId(self, orgStructureId, propertyOrgStructure=False):
        self.orgStructureId = orgStructureId
        self.propertyOrgStructure = propertyOrgStructure  # WFT
        CPersonComboBox.setOrgStructureId(self, orgStructureId, propertyOrgStructure)


    def setDeallocatedPerson(self, deallocatedPerson):
        self.deallocatedPerson = deallocatedPerson
        CPersonComboBox.setDeallocatedPerson(self, deallocatedPerson)


    def setDefaultOrgStructureId(self, orgStructureId):
        self.defaultOrgStructureId = orgStructureId


    def setActivityCode(self, code):
        self.activityCode = code


    def setOnlyDoctors(self, value):
        self.isOnlyDoctors = value


    def setPostCode(self, code):
        self.postCode = code


    def setUserId(self, userId):
        self.userId = userId


    def setOnlyDoctorsIfUnknowPost(self, value):
        self.onlyDoctorsIfUnknowPost = value


    def setSpecialityCode(self, code):
        self.specialityCode = code


    def setSpecialityId(self, id):
        self.specialityId = id


    def setDate(self, date):
        self.date = date

    def setOrgStructureList(self, orgStructureIdList):
        self.orgStructureIdList = orgStructureIdList

    def setPersonIdList(self, personIdList):
        self.personIdList = personIdList

#    def setValue(self, personId):
#        self.personId = personId
#        rowIndex = self._model.searchId(self.personId)
#        self.setCurrentIndex(rowIndex)
#        self.updateText()
#        self.lineEdit().setCursorPosition(0)


#    def value(self):
#        rowIndex = self.currentIndex()
#        self.personId = self._model.getId(rowIndex)
#        return self.personId


    def setSpecialityIndependents(self):
        if not self._popup:
            self._popup = CPersonComboBoxExPopup(self)
            self.connect(self._popup, SIGNAL('personIdSelected(int)'), self.setValue)
        self._popup.setSpecialityIndependents()


    def setChkSpecialityDefaultStatus(self, value):
        if not self._popup:
            self._popup = CPersonComboBoxExPopup(self)
            self.connect(self._popup, SIGNAL('personIdSelected(int)'), self.setValue)
        self._popup.setChkSpecialityDefaultStatus(value)
    
    
    def filterInSearch(self, orgStructureIdList, specialityIdList):
        if not self._popup:
            self._popup = CPersonComboBoxExPopup(self)
            self.connect(self._popup, SIGNAL('personIdSelected(int)'), self.setValue)
        if specialityIdList:
            tableSpeciality = QtGui.qApp.db.table('rbSpeciality')
            self._popup.chkSpeciality.setChecked(True)
            self._popup.chkSpeciality.setEnabled(False)
            self._popup.cmbSpeciality.setEnabled(False)
        if orgStructureIdList:
            tableOrgStructure = QtGui.qApp.db.table('OrgStructure')
            self._popup.cmbOrgStructure.setFilter(tableOrgStructure['id'].inlist(orgStructureIdList))


#    def updateText(self):
#        self._createPopup()
#        self.setEditText(self._popup.getStringValue(self.personId))


#    def lookup(self):
#        i, self._searchString = self._specialValuesLookupWraper(self._model.searchCodeEx(self._searchString))
#        if i>=0 and i!=self.currentIndex():
#            self.setCurrentIndex(i)
#            rowIndex = self.currentIndex()
#            self.personId = self._model.getId(rowIndex)


#    def _specialValuesLookupWraper(self, (index, searchString)):
#        if self._addNone:
#            return (index+self._specialValueCount, searchString) if index == 0 else (index, searchString)
#        return (index, searchString)


class CPersonFindInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.tableName = tableName
        self.filter = params.get('filter', '')
        self.preferredWidth = params.get('preferredWidth', None)
        self.orgStructureId = QtGui.qApp.currentOrgStructureId()
        self.date = None
        self.orgStructureIdList = []
        self.personIdList = []


    def toString(self, val, record):
        if forceRef(val):
            if not hasattr(QtGui.qApp, '_recordsCache_vrbPersonWithSpecialityAndOrgStr'):
                QtGui.qApp._recordsCache_vrbPersonWithSpecialityAndOrgStr = CTableRecordCache(QtGui.qApp.db, 'vrbPersonWithSpecialityAndOrgStr')
            return QtGui.qApp._recordsCache_vrbPersonWithSpecialityAndOrgStr.get(val).value('name')
        else:
            return None


    def createEditor(self, parent):
        editor = CPersonComboBoxEx(parent)
        editor.setOrgStructureId(self.orgStructureId)
        editor.setOrgStructureList(self.orgStructureIdList)
        editor.setPersonIdList(self.personIdList)
        editor.setDate(self.date)
        editor.setBegDate(self.date)
        return editor


    def setDate(self, date):
        self.date = date


    def setEditorData(self, editor, value, record):
        editor.setValue(forceInt(value))


    def getEditorData(self, editor):
        return toVariant(editor.value())


class CPersonWithOrgListComboBoxEx(CPersonComboBoxEx):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                      )

    def __init__(self, parent=None, specialityPresent=True):
        CPersonComboBoxEx.__init__(self, parent, specialityPresent)


    def compileFilter(self):
        db = QtGui.qApp.db
        table = db.table(self._tableName)
        cond = []
        if self._orgStructureIdList:
            cond.append(table['orgStructure_id'].inlist(self._orgStructureIdList))
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
        if self._personIdList:
            cond.append(table['id'].inlist(self._personIdList))
        if self._customFilter:
            cond.append(self._customFilter)
        return db.joinAnd(cond)
