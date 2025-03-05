# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QDate, QEvent, QVariant, pyqtSignature, SIGNAL

from library.database import CTableRecordCache
from library.TableModel import CTableModel, CDateCol, CRefBookCol, CTextCol
from library.Utils import forceRef, forceString, forceStringEx, getPref, setPref


from Ui_PersonComboBoxExPopup import Ui_PersonComboBoxExPopup


class CPersonComboBoxExPopup(QtGui.QFrame, Ui_PersonComboBoxExPopup):
    __pyqtSignals__ = ('personIdSelected(int)',
                       'orgStructureIdChanged(int, bool)',
                       'specialityIdChanged(int)',
                       'deallocatedPersonChecked(bool)'
                      )

    def __init__(self, parent=None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.tableModel = CPersonTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblPerson.setModel(self.tableModel)
        self.tblPerson.setSelectionModel(self.tableSelectionModel)
        self.tblPerson.setSortingEnabled(True)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
#       к сожалению в данном случае setDefault обеспечивает рамочку вокруг кнопочки
#       но enter не работает...
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setShortcut(Qt.Key_Return)
        self.date = None
        self.personId = None
        self.retireDate = None
        self.userId = None
        self.onlyDoctorsIfUnknowPost = False
        self.tblPerson.installEventFilter(self)
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CPersonComboBoxExPopup', {})
        self.tblPerson.loadPreferences(preferences)
        self.cmbOrganisation.setValue(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbPost.setTable('rbPost')
        self.cmbSpeciality.setTable('rbSpeciality')
        self.cmbActivity.setTable('rbActivity')
        self.cmbTariffCategory.setTable('rbTariffCategory')
        self.prevColumn = None
        self.asc = True
        self.connect(self.tblPerson.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setPersonOrderByColumn)
        self.cmbPost.setValue(0)
        self.cmbSpeciality.setValue(0)
        self.cmbActivity.setValue(0)
        self.cmbTariffCategory.setValue(0)
        self.chkDeallocatedPerson.setChecked(False)
        self.chkSpeciality.setChecked(True)
        self.cmbSpeciality.setSpecialValues([(-1, '-', u'без специальности')])
        self._parent = parent
        self._customFilter = None

        # appPrefs = QtGui.qApp.preferences.appPrefs
        # onlyDoctors = forceBool(appPrefs.get('onlyDoctorsInPopup', False))
        # self.chkOnlyDoctors.setChecked(onlyDoctors)
        self.propertyOrgStructure = False  # WFT!
        self.chkSpecialityDefaultStatus = True
        # self.cmbSpeciality.setEnabled(False)


    def setRetireDate(self, retireDate):
        self.retireDate = retireDate


    def setOnlyDoctors(self, value):
        self.chkOnlyDoctors.setChecked(value)


    def getActualEmptyRecord(self):
        return self.tableModel.getActualEmptyRecord()


    def getStringValue(self, id):
        return self.tableModel.getStringValue(id)


    def addNotSetValue(self):
        self.tableModel.addNotSetValue()


    def setSpecialValues(self, specialValues):
        self.tableModel.setSpecialValues(specialValues)


    def setUserId(self, userId):
        self.userId = userId
        self.initModel(self.userId)


    def setFilter(self, filter):
        self._customFilter = filter


    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent is not None:
            opt = QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(
                QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos()):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)


    def closeEvent(self, event):
        preferences = self.tblPerson.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CPersonComboBoxExPopup', preferences)
        QtGui.QFrame.closeEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.tblPerson:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblPerson.currentIndex()
                self.tblPerson.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)


    def getOrgStructureIdList(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBox_reset()


    @pyqtSignature('int')
    def on_cmbOrganisation_currentIndexChanged(self, index):
        orgId = self.cmbOrganisation.value()
        self.cmbOrgStructure.setEnabled(bool(orgId))
        self.cmbOrgStructure.setOrgId(orgId)


    @pyqtSignature('bool')
    def on_chkSpeciality_clicked(self, checked):
        specialityId = self.cmbSpeciality.value()
        if checked:
            self.cmbSpeciality.setSpecialValues([(-1, '-', u'без специальности')])
        else:
            self.cmbSpeciality.setSpecialValues(None)
        self.cmbSpeciality.setValue(specialityId)
        # self.cmbSpeciality.setEnabled(checked)

    @pyqtSignature('QString')
    def on_edit_fio_textChanged(self, text):  # При вводе в текстовое поле сразу же формирует список по фамильно
        self.on_buttonBox_apply()

    def on_buttonBox_reset(self):
        self.cmbOrganisation.setValue(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbPost.setValue(0)
        self.chkDeallocatedPerson.setChecked(False)
        self.chkSpeciality.setChecked(self.chkSpecialityDefaultStatus)
        self.cmbSpeciality.setEnabled(False)
        self.cmbSpeciality.setValue(0)
        self.cmbActivity.setValue(0)
        self.cmbTariffCategory.setCurrentIndex(0)
        self.edit_fio.setText("")


    def setPropertyOrgStructure(self, value):
        self.propertyOrgStructure = value


    def setOnlyDoctorsIfUnknowPost(self, value):
        self.onlyDoctorsIfUnknowPost = value


    def on_buttonBox_apply(self, id=None):
        organisationId = forceRef(self.cmbOrganisation.value())
        orgStructureId = forceRef(self.cmbOrgStructure.value())
        postId = forceRef(self.cmbPost.value())
        specialityId = forceRef(self.cmbSpeciality.value()) if self.chkSpeciality.isChecked() else None
        activityId = forceRef(self.cmbActivity.value())
        tariffCategoryId = forceRef(self.cmbTariffCategory.value())
        deallocatedPerson = forceRef(self.chkDeallocatedPerson.isChecked())
        onlyDoctors = forceRef(self.chkOnlyDoctors.isChecked())
        name = forceString(self.edit_fio.text())
        
        crIdList = self.getPersonIdList(organisationId, orgStructureId, postId, specialityId, activityId, tariffCategoryId, deallocatedPerson, onlyDoctors, name=name)
        self.setPersonIdList(crIdList, id)

        if orgStructureId:
            self.emit(SIGNAL('orgStructureIdChanged(int, bool)'), orgStructureId, self.propertyOrgStructure)
        if specialityId:
            self.emit(SIGNAL('specialityIdChanged(int)'), specialityId)
        self.emit(SIGNAL('deallocatedPersonChecked(bool)'), deallocatedPerson)


    def initModel(self, id=None):
        self.on_buttonBox_apply(id)


    def setPersonIdList(self, idList, posToId):
        if idList:
            self.tblPerson.setIdList(idList, posToId)
            self.tabWidget.setCurrentIndex(0)
            self.tabWidget.setTabEnabled(0, True)
        else:
            self.tblPerson.setIdList(idList)
            self.tabWidget.setTabEnabled(0, True)


    def setSpecialityIndependents(self):
        self.chkSpeciality.setChecked(False)
        self.on_buttonBox_apply()


    def setChkSpecialityDefaultStatus(self, value):
        self.chkSpecialityDefaultStatus = value


    def getPersonIdList(self, organisationId, orgStructureId, postId, specialityId, activityId, tariffCategoryId, deallocatedPerson, onlyDoctors=True, orderByColumn=1, name =''):
        db = QtGui.qApp.db
        tableVRBPerson = db.table('vrbPersonWithSpecialityAndPost')
        tablePerson = db.table('Person')
        tablePerson_Activity = db.table('Person_Activity')
        tablePost = db.table('rbPost')
        tableSpeciality = db.table('rbSpeciality')
        tableOrg = db.table('OrgStructure')
        queryTable = tableVRBPerson

        cond = []
        if self.userId:
            cond.append(tableVRBPerson['id'].eq(self.userId))
        if organisationId:
            cond.append(tableVRBPerson['org_id'].eq(organisationId))
        if orgStructureId:
            orgStructureIndex = self.cmbOrgStructure._model.index(self.cmbOrgStructure.currentIndex(), 0, self.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            cond.append(tableVRBPerson['orgStructure_id'].inlist(orgStructureIdList))
        if postId:
            cond.append(tablePerson['post_id'].eq(postId))
        if name:
            cond.append(tableVRBPerson['name'].like(u'%'+name+u'%'))
        if onlyDoctors or (self.onlyDoctorsIfUnknowPost and not postId):
            cond.append('EXISTS (SELECT rbPost.`id` FROM rbPost WHERE Person.`post_id`=rbPost.`id` AND rbPost.`code` REGEXP \'^[1-3]+\')')
        if self.chkSpeciality.isChecked():
            if specialityId == -1:
                cond.append(tableVRBPerson['speciality_id'].isNull())
            elif specialityId is None:
                cond.append(tableVRBPerson['speciality_id'].isNotNull())
            else:
                cond.append(tableVRBPerson['speciality_id'].eq(specialityId))
        else:
#            if specialityId:
#                cond.append(tableVRBPerson['speciality_id'].eq(specialityId))
            pass
        if activityId:
            queryTable = queryTable.innerJoin(tablePerson_Activity, tableVRBPerson['id'].eq(tablePerson_Activity['master_id']))
            cond.append(tablePerson_Activity['activity_id'].eq(activityId))
            cond.append(tablePerson_Activity['deleted'].eq(0))
        if tariffCategoryId:
            cond.append(tablePerson['tariffCategory_id'].eq(tariffCategoryId))
        if not deallocatedPerson:
            if self.retireDate:
                cond.append(db.joinAnd([tablePerson['retired'].eq(0), db.joinOr([tablePerson['retireDate'].isNull(), tablePerson['retireDate'].ge(self.retireDate)])]))
            else:
                cond.append(db.joinAnd([tablePerson['retired'].eq(0), tablePerson['retireDate'].isNull()]))
        if postId or not deallocatedPerson or onlyDoctors or self.onlyDoctorsIfUnknowPost:
            cond.append(tablePerson['deleted'].eq(0))
        if self._customFilter:
            cond.append(self._customFilter)
        queryTable = queryTable.innerJoin(tablePerson, tableVRBPerson['id'].eq(tablePerson['id']))
        queryTable = queryTable.leftJoin(tablePost, tablePerson['post_id'].eq(tablePost['id']))
        queryTable = queryTable.leftJoin(tableSpeciality, tablePerson['speciality_id'].eq(tableSpeciality['id']))
        queryTable = queryTable.leftJoin(tableOrg, tablePerson['orgStructure_id'].eq(tableOrg['id']))
        order = u'vrbPersonWithSpecialityAndPost.name '
        asc = u'ASC'
        desc = u'DESC'
        orderName = u', vrbPersonWithSpecialityAndPost.name '
        if orderByColumn == 0:
            order = u'vrbPersonWithSpecialityAndPost.code '
        if orderByColumn == 1:
            order = u'vrbPersonWithSpecialityAndPost.name '
        if orderByColumn == 2:
            order = u'rbPost.name '
        if orderByColumn == 3:
            order = u'rbSpeciality.name '
        if orderByColumn == 4:
            order = u'OrgStructure.name '
        if orderByColumn == 5:
            order = u'vrbPersonWithSpecialityAndPost.retireDate '

        if self.prevColumn == orderByColumn and self.asc:
            self.asc = False
            order += desc + orderName + asc
        elif self.prevColumn == orderByColumn and not self.asc:
            self.asc = True
            order += asc + orderName + asc
        else:
            self.asc = True
            order += asc + orderName + asc

        idList = db.getDistinctIdList(queryTable, [tableVRBPerson['id'].name(), tableVRBPerson['name'].name()],
                              where=cond,
                              order=order,
                              limit=1000)
        fakeIdList = self.tableModel.getSpecialValuesKeys()
        if fakeIdList:
            return fakeIdList+idList
        return idList


    def setDate(self, date):
        self.tableModel.date = date


    def setPersonId(self, personId):
        self.personId = personId
        self.on_buttonBox_apply(self.personId)


    def selectPersonId(self, personId):
        self.personId = personId
        self.emit(SIGNAL('personIdSelected(int)'), personId)
        self.close()


    def getCurrentPersonId(self):
        return self.tblPerson.currentItemId()


    @pyqtSignature('QModelIndex')
    def on_tblPerson_doubleClicked(self, index):
        if index.isValid():
            if Qt.ItemIsEnabled & self.tableModel.flags(index):
                personId = self.getCurrentPersonId()
                self.selectPersonId(personId)


    def _setPersonOrderByColumn(self, column):
        organisationId = forceRef(self.cmbOrganisation.value())
        orgStructureId = forceRef(self.cmbOrgStructure.value())
        postId = forceRef(self.cmbPost.value())
        specialityId = forceRef(self.cmbSpeciality.value()) if self.chkSpeciality.isChecked() else None
        activityId = forceRef(self.cmbActivity.value())
        tariffCategoryId = forceRef(self.cmbTariffCategory.value())
        deallocatedPerson = forceRef(self.chkDeallocatedPerson.isChecked())
        onlyDoctors = forceRef(self.chkOnlyDoctors.isChecked())
        name = forceString(self.edit_fio.text())

        updateTable = self.getPersonIdList(organisationId, orgStructureId, postId, specialityId, activityId, tariffCategoryId, deallocatedPerson, onlyDoctors, column, name)
        self.setPersonIdList(updateTable, id)
        self.prevColumn = column


class CPersonTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self._specialValues = []
        self.addColumn(CTextCol(u'Код', ['code'], 5))
        self.addColumn(CTextCol(u'ФИО', ['name'], 15))
        self.addColumn(CRefBookCol(u'Должность', ['post_id'], 'rbPost', 15))
        self.addColumn(CRefBookCol(u'Специальность', ['speciality_id'], 'rbSpeciality', 10))
        self.addColumn(CRefBookCol(u'Подразделение', ['orgStructure_id'], 'OrgStructure', 10))
        self.addColumn(CDateCol(u'Дата запрещения', ['retireDate'], 10))
        self._fieldNames = ['vrbPerson.code', 'vrbPerson.name', 'Person.post_id', 'vrbPerson.speciality_id', 'vrbPerson.orgStructure_id', 'vrbPerson.retireDate']
        self.setTable('vrbPerson')
        self.date = QDate.currentDate()


    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
#        row = index.row()
#        record = self.getRecordByRow(row)
#        enabled = True
#        if enabled:
#            return Qt.ItemIsEnabled|Qt.ItemIsSelectable
#        else:
#            return Qt.ItemIsSelectable


    def getActualEmptyRecord(self):
        record = QtSql.QSqlRecord()
        record.append(QtSql.QSqlField('code', QVariant.String))
        record.append(QtSql.QSqlField('name', QVariant.String))
        record.append(QtSql.QSqlField('post_id', QVariant.Int))
        record.append(QtSql.QSqlField('speciality_id', QVariant.Int))
        record.append(QtSql.QSqlField('orgStructure_id', QVariant.Int))
        record.append(QtSql.QSqlField('retireDate', QVariant.Date))
        return record


    def getStringValue(self, id):
        row = self._idList.index(id) if id in self._idList else None
        if row is not None:
            name = forceStringEx(self.data(self.index(row, 1)))
            speciality = forceStringEx(self.data(self.index(row, 3)))
            return ', '.join((name, speciality))
        return forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))


    def setSpecialValues(self, specialValues):
        if self._specialValues != specialValues:
            self._specialValues = specialValues
            self.setTable(specialValues)  # WTF? таки specialValues или tableName?


    def getSpecialValuesKeys(self):
        return [key for key, item in self._specialValues]


    def setTable(self, tableName):  # WFT? tableName не используется?
        db = QtGui.qApp.db
        tableVRBPerson = db.table('vrbPerson')
        tablePerson = db.table('Person')
        loadFields = []
        loadFields.append(u'DISTINCT ' + u', '.join(self._fieldNames))
        table = tableVRBPerson.innerJoin(tablePerson, tablePerson['id'].eq(tableVRBPerson['id']))
        self._table = table
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, fakeValues=self._specialValues)
