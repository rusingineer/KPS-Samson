# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, QObject, QVariant, QDate

from library.crbcombobox import CRBComboBox
from library.DialogBase import CConstructHelperMixin
from library.TableModel import CQueryModel, CTextCol, CTextListCol, CBoolCol
from library.Utils import formatSNILS, forceRef, forceString, forceBool, trim, formatRecordsCount, exceptionToUnicode

from Exchange.PyServices import getPyServices, CDistantMonitoringService
from Orgs.Utils import getOrgStructureDescendants
from RefBooks.Person.List import CPersonEditor
from Users.Rights import urAdmin, urAccessRefPerson, urAccessRefPersonPersonal

from Ui_DistantMonitoringPersonPage import Ui_DistantMonitoringPersonPage


class CDistantMonitoringPersonPage(QtGui.QWidget, Ui_DistantMonitoringPersonPage, CConstructHelperMixin):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.addModels('PersonList', CPersonListModel(self))
        self.addObject('actRegisterPerson', QtGui.QAction(u'Зарегистрировать врача', self))
        self.addObject('actEditPerson', QtGui.QAction(u'Редактировать врача', self))
        self.addObject('actOpenBrowser', QtGui.QAction(u'Переход в СИС ДН', self))
        self.setupUi(self)
        self.tblPersonList.addPopupAction(self.actRegisterPerson)
        self.tblPersonList.addPopupAction(self.actEditPerson)
        self.tblPersonList.addPopupAction(self.actOpenBrowser)
        self.connect(self.tblPersonList, SIGNAL('popupMenuAboutToShow()'), self.popupMenuAboutToShow)
        self.setModels(self.tblPersonList, self.modelPersonList, self.selectionModelPersonList)
        self.filter = {}
        self.cmbPost.setTable('rbPost')
        self.cmbSpeciality.setTable('rbSpeciality')
        self.cmbActivity.setTable('rbActivity')
        self.cmbActivity.setSpecialValues([(-1, '-', u'все')])
        self.cmbActivity.setShowFields(CRBComboBox.showCodeAndName)
        stmt = "SELECT DISTINCT org_id, infisCode FROM Person LEFT JOIN Organisation ON Organisation.id=Person.org_id ORDER BY infisCode"
        query = QtGui.qApp.db.query(stmt)
        while query.next():
            record = query.record()
            orgId = forceRef(record.value('org_id'))
            infisCode = forceString(record.value('infisCode')) if orgId else u'не задано'
            self.cmbLPU.addItem(infisCode, orgId)
        self.cmbUserProfile.setTable('rbUserProfile')
        self.cmbUserProfile.setSpecialValues([(-1, '', u'все')])
        self.resetFilter()
        header = self.tblPersonList.horizontalHeader()
        if self.modelPersonList.orderColumn():
            header.setSortIndicatorShown(True)
            header.setSortIndicator(self.modelPersonList.orderColumn(), self.modelPersonList.sortIndicator())
        QObject.connect(header, SIGNAL('sectionClicked(int)'), self.setSort)
        self.pyServices = getPyServices(CDistantMonitoringService)
    
    @pyqtSignature('int')
    def setSort(self, colIndex):
        self.modelPersonList.toggleOrder(colIndex)
        self.updatePersonList()

    def updatePersonList(self):
        self.modelPersonList.update(self.filter)
        self.lblRecordCount.setText(formatRecordsCount(self.modelPersonList.rowCount()))

    def applyFilter(self):
        self.filter = {}
        if self.chkStrPodr.isChecked():
            orgStructureId = self.cmbStrPodr.value()
            orgStructureIdList = getOrgStructureDescendants(orgStructureId)
            self.filter['orgStructureIds'] = orgStructureIdList
        if self.chkPost.isChecked():
            self.filter['postId'] = self.cmbPost.getValue()
        if self.chkSpeciality.isChecked():
            self.filter['specialityId'] = self.cmbSpeciality.getValue()
        if self.chkActivity.isChecked():
            self.filter['activityId'] = self.cmbActivity.getValue()
        if self.chkLPU.isChecked():
            self.filter['orgId'] = forceRef(self.cmbLPU.itemData(self.cmbLPU.currentIndex()))
        if self.chkUserProfile.isChecked():
            self.filter['userProfileId'] = self.cmbUserProfile.getValue()
        if self.chkLastName.isChecked():
            self.filter['lastName'] = trim(self.edtLastName.text())
        if self.chkUserLogin.isChecked():
            self.filter['userLogin'] = trim(self.edtUserLogin.text())
        if self.chkSNILS.isChecked():
            self.filter['SNILS'] = forceString(self.edtSNILS.text()).replace(' ', '-').split('-')
        if self.chkIsRegistered.isChecked():
            self.filter['isRegistered'] = True
        self.updatePersonList()

    def resetFilter(self):
        self.chkStrPodr.setChecked(False)
        self.cmbStrPodr.setValue(None)
        self.chkPost.setChecked(False)
        self.cmbPost.setValue(None)
        self.chkSpeciality.setChecked(False)
        self.cmbSpeciality.setValue(None)
        self.chkActivity.setChecked(False)
        self.cmbActivity.setValue(None)
        self.chkLPU.setChecked(False)
        self.cmbLPU.setCurrentIndex(0)
        self.chkUserProfile.setChecked(False)
        self.cmbUserProfile.setValue(None)
        self.chkLastName.setChecked(False)
        self.edtLastName.setText('')
        self.chkUserLogin.setChecked(False)
        self.edtUserLogin.setText('')
        self.chkSNILS.setChecked(False)
        self.edtSNILS.setText('')
        self.chkIsRegistered.setChecked(False)
        self.applyFilter()

    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxFilter_clicked(self, button):
        buttonCode = self.buttonBoxFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.applyFilter()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetFilter()

    def popupMenuAboutToShow(self):
        record = self.modelPersonList.recordByIndex(self.tblPersonList.currentIndex())
        isRegistered = forceBool(record.value('isRegistered')) if record else None
        self.actRegisterPerson.setEnabled(bool(self.pyServices and record and not isRegistered))
        self.actEditPerson.setEnabled(bool(record and QtGui.qApp.userHasAnyRight([urAdmin, urAccessRefPerson, urAccessRefPersonPersonal])))
        self.actOpenBrowser.setEnabled(bool(self.pyServices and isRegistered))
    
    @pyqtSignature('')
    def on_actRegisterPerson_triggered(self):
        record = self.modelPersonList.recordByIndex(self.tblPersonList.currentIndex())
        try:
            response = self.pyServices.createPractitioner(forceRef(record.value('id')))
            QtGui.QMessageBox.information(self, u'Сервис дистанционного наблюдения', u'Врач успешно зарегистрирован', QtGui.QMessageBox.Ok)
            self.updatePersonList()
        except Exception as e:
            QtGui.QMessageBox.critical(self, u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)
    
    @pyqtSignature('')
    def on_actEditPerson_triggered(self):
        record = self.modelPersonList.recordByIndex(self.tblPersonList.currentIndex())
        personId = forceRef(record.value('id'))
        dialog = CPersonEditor(self)
        dialog.load(personId)
        if not dialog.exec_():
            return
        isRegistered = forceBool(record.value('isRegistered'))
        if isRegistered:
            mbResult = QtGui.QMessageBox.question(self, u'Сервис дистанционного наблюдения', u'Изменить данные врача на сервисе?', QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
            if mbResult != QtGui.QMessageBox.Yes:
                return
            try:
                response = self.pyServices.editPractitioner(personId)
                QtGui.QMessageBox.information(self, u'Сервис дистанционного наблюдения', u'Данные врача обновлены', QtGui.QMessageBox.Ok)
            except Exception as e:
                QtGui.QMessageBox.critical(self, u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)
        self.updatePersonList()
    
    @pyqtSignature('')
    def on_actOpenBrowser_triggered(self):
        record = self.modelPersonList.recordByIndex(self.tblPersonList.currentIndex())
        snils = forceString(record.value('SNILS'))
        self.pyServices.openWebApp(snils)


class CPersonListModel(CQueryModel):
    class CSNILSCol(CTextCol):
        def format(self, values):
            val = unicode(values[0].toString())
            return QVariant(formatSNILS(val))

    def __init__(self, parent):
        CQueryModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Код', ['code'], 6))
        self.addColumn(CPersonListModel.CSNILSCol(u'СНИЛС', ['SNILS'], 20))
        self.addColumn(CTextListCol(u'ФИО', ['lastName', 'firstName', 'patrName'], 20))
        self.addColumn(CTextCol(u'Федеральный код', ['federalCode'], 10))
        self.addColumn(CTextCol(u'ЛПУ', ['organisation_infisCode'], 5))
        self.addColumn(CTextCol(u'Подразделение', ['orgStructure_name'], 5))
        self.addColumn(CTextCol(u'Должность', ['post_name'], 20))
        self.addColumn(CTextCol(u'Специальность', ['speciality_name'], 10))
        self.addColumn(CTextCol(u'Профиль', ['userProfile_name'], 10))
        self.addColumn(CBoolCol(u'Регистрация на сервисе', ['isRegistered'], 10))
        self.setOrder('lastName')

    def update(self, filter):
        db = QtGui.qApp.db
        systemId = forceRef(db.translate('rbAccountingSystem', 'code', 'SYSDM', 'id'))
        if not systemId:
            raise Exception(u'Не найдена внешняя учетная система "SYSDM"')
        tablePerson = db.table('Person')
        tableOrganisation = db.table('Organisation')
        tableOrgStructure = db.table('OrgStructure')
        tablePost = db.table('rbPost')
        tableSpeciality = db.table('rbSpeciality')
        tablePersonActivity = db.table('Person_Activity')
        tableUserProfile = db.table('rbUserProfile')
        tableIdentification = db.table('Person_Identification')
        query = tablePerson.leftJoin(tableOrganisation, tableOrganisation['id'].eq(tablePerson['org_id']))
        query = query.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))
        query = query.leftJoin(tablePost, tablePost['id'].eq(tablePerson['post_id']))
        query = query.leftJoin(tableSpeciality, tableSpeciality['id'].eq(tablePerson['speciality_id']))
        query = query.leftJoin(tableUserProfile, tableUserProfile['id'].eq(tablePerson['userProfile_id']))
        identificationCond = [
            tableIdentification['master_id'].eq(tablePerson['id']),
            tableIdentification['system_id'].eq(systemId), tableIdentification['deleted'].eq(0)
        ]
        cols = [
            tablePerson['id'],
            tablePerson['code'],
            tablePerson['SNILS'],
            tablePerson['lastName'],
            tablePerson['firstName'],
            tablePerson['patrName'],
            tablePerson['federalCode'],
            tableOrganisation['infisCode'].alias('organisation_infisCode'),
            tableOrgStructure['name'].alias('orgStructure_name'),
            tablePost['name'].alias('post_name'),
            tableSpeciality['name'].alias('speciality_name'),
            tableUserProfile['name'].alias('userProfile_name'),
            db.existsStmt(tableIdentification, identificationCond) + ' AS isRegistered'
        ]
        cond = [
            tablePerson['deleted'].eq(0),
            db.joinOr([tablePerson['retireDate'].isNull(), tablePerson['retireDate'].ge(QDate.currentDate())]),
            tablePerson['speciality_id'].isNotNull()
        ]
        if 'orgStructureIds' in filter:
            cond.append(tablePerson['orgStructure_id'].inlist(filter['orgStructureIds']))
        if 'postId' in filter:
            cond.append(tablePerson['post_id'].eq(filter['postId']))
        if 'specialityId' in filter:
            cond.append(tablePerson['speciality_id'].eq(filter['specialityId']))
        if 'activityId' in filter:
            activityCond = [
                tablePersonActivity['master_id'].eq(tablePerson['id']),
                tablePersonActivity['deleted'].eq(0),
            ]
            if filter['activityId'] is None:
                cond.append(db.notExistsStmt(tablePersonActivity, activityCond))
            elif filter['activityId'] == -1:
                activityCond.append(tablePersonActivity['activity_id'].isNotNull())
                cond.append(db.existsStmt(tablePersonActivity, activityCond))
            else:
                activityCond.append(tablePersonActivity['activity_id'].eq(filter['activityId']))
                cond.append(db.existsStmt(tablePersonActivity, activityCond))
        if 'orgId' in filter:
            cond.append(tablePerson['org_id'].eq(filter['orgId']))
        if 'userProfileId' in filter:
            if filter['userProfileId'] == -1:
                cond.append(tablePerson['userProfile_id'].isNotNull())
            else:
                cond.append(tablePerson['userProfile_id'].eq(filter['userProfileId']))
        if 'lastName' in filter:
            if filter['lastName']:
                cond.append(tablePerson['lastName'].contain(filter['lastName']))
            else:
                cond.append(tablePerson['lastName'].eq(''))
        if 'userLogin' in filter:
            if filter['userLogin']:
                cond.append(tablePerson['login'].contain(filter['userLogin']))
            else:
                cond.append(tablePerson['login'].eq(''))
        if 'SNILS' in filter:
            snils = filter['SNILS']
            if snils[0]:
                cond.append(tablePerson['SNILS'].like(u'{}%%'.format(snils[0])))
            if snils[1]:
                cond.append(tablePerson['SNILS'].like(u'___{}%%'.format(snils[1])))
            if snils[2]:
                cond.append(tablePerson['SNILS'].like(u'______{}%%'.format(snils[2])))
            if snils[3]:
                cond.append(tablePerson['SNILS'].like(u'_________{}%%'.format(snils[3])))
            if not any(snils):
                cond.append(tablePerson['SNILS'].eq(''))
        if filter.get('isRegistered'):
            cond.append(db.existsStmt(tableIdentification, identificationCond))
        order = self.formatOrderBy({
            'code': tablePerson['code'],
            'SNILS': tablePerson['SNILS'],
            'lastName': [tablePerson['lastName'], tablePerson['firstName'], tablePerson['patrName']],
            'federalCode': tablePerson['federalCode'],
            'organisation_infisCode': tableOrganisation['infisCode'],
            'orgStructure_name': tableOrgStructure['name'],
            'post_name': tablePost['name'],
            'speciality_name': tableSpeciality['name'],
            'userProfile_name': tableUserProfile['name'],
            'isRegistered': db.existsStmt(tableIdentification, identificationCond)
        })
        records = db.getRecordList(query, cols=cols, where=cond, order=order)
        self.setRecords(records)
