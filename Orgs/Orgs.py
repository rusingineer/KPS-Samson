# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import re

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QVariant, pyqtSignature, SIGNAL, QDate

from library.IdentificationModel import CIdentificationModel, checkIdentification
from library.InDocTable import CInDocTableModel, CBoolInDocTableCol, CInDocTableCol, CRBInDocTableCol, CDateInDocTableCol, CTextInDocTableCol
from library.interchange import getCheckBoxValue, getComboBoxValue, getLineEditValue, getRBComboBoxValue, getTextEditValue, setCheckBoxValue, setComboBoxValue, setLineEditValue, setRBComboBoxValue, setTextEditValue
from library.MSCAPI import MSCApi
from library.ItemsListDialog import CItemEditorBaseDialog
from library.ItemsListDialog import CItemsListDialog
from library.TableModel import CTextCol, CDesignationCol
from library.Utils import addDotsEx, forceRef, forceString, forceStringEx, toVariant, forceDate, anyToUnicode, forceInt
from RefBooks.Service.RBServiceComboBox import CRBServiceInDocTableCol
from RefBooks.Tables import rbNet, rbOKFS, rbOKPF
from Banks import CBanksList
from Utils import fixOKVED, getShortBankName, parseOKVEDList
from Registry.Utils              import getAddress, getAddressId

from Ui_OrgEditor import Ui_OrgEditorDialog
from Ui_OrgFilterDialog   import Ui_OrgFilterDialog


def selectOrganisation(parent, orgId, showListFirst, filter=None, hospitalBedProfileId=None, isHeadOrgVisible=True, params={}, forSelect=False):
    if showListFirst:
        dialog = COrgsList(parent, forSelect=forSelect)
        try:
            dialog.filter = filter
            if orgId and orgId in dialog.model.idList():
                dialog.setItemId(orgId)
            if params:
                dialog.props = params
            if dialog.exec_():
                return dialog.currentItemId()
        finally:
            dialog.deleteLater()
    else:
        filterDialog = COrgFilterDialog(parent)
        if not isHeadOrgVisible:
            filterDialog.setHeadOrgVisible(isHeadOrgVisible)
        isActive = params.get('isActive', 2)
        isSupplier = params.get('isSupplier', 0)
        filterDialog.setProps({ 'hospitalBedProfileId':hospitalBedProfileId,
                                'isActive':isActive,
                                'isSupplier':isSupplier})
        try:
            if filterDialog.exec_():
                dialog = COrgsList(parent, True)
                dialog.filter = filter
                try:
                    dialog.props = filterDialog.props()
                    dialog.renewListAndSetTo(orgId)
                    if dialog.model.rowCount() == 1:
                        return dialog.currentItemId()
                    else:
                        if dialog.exec_():
                            return dialog.currentItemId()
                finally:
                    dialog.deleteLater()
        finally:
            filterDialog.deleteLater()
    return None


class COrgsList(CItemsListDialog):
    def __init__(self, parent, forSelect=False):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Краткое наименование',    ['shortName'], 30),
            CTextCol(u'ИНН',                     ['INN'],       12),
            CTextCol(u'ОГРН',                    ['OGRN'],      10),
            CTextCol(u'Код ТФОМС',               ['infisCode'], 10),
            CTextCol(u'Код ФФОМС',               ['smoCode'], 10),
            CTextCol(u'Код ОКАТО',               ['OKATO'], 10),
            CTextCol(u'Полное наименование',     ['fullName'],  30),
            CDesignationCol(u'Головная организация', ['head_id'], ('Organisation', 'shortName'), 20)
            ],
            'Organisation',
            ['shortName', 'INN', 'OGRN'],
            forSelect=forSelect,
            filterClass=COrgFilterDialog
            )
        self.setWindowTitleEx(u'Организации')
        self.filter = None
        self.tblItems.addPopupRecordProperies()


    @pyqtSignature('')
    def on_btnFilter_clicked(self):
        if self.filterClass:
            dialog = self.filterClass(self)
            try:
                dialog.setProps(self.props)
                if dialog.exec_():
                    self.props = dialog.props()
                    self.renewListAndSetTo(None)
            finally:
                dialog.deleteLater()


    def getItemEditor(self):
        return COrgEditor(self)


    def select(self, props):
        table = self.model.table()
        db = QtGui.qApp.db
        cond = []
        cond.append('deleted = 0')
        headOrgId = props.get('headOrgId', None)
        if headOrgId:
            cond.append(db.joinOr([table['id'].eq(headOrgId), table['head_id'].eq(headOrgId)]))
        iHeadVisible = props.get('iHeadVisible', False)
        if iHeadVisible:
            cond.append(table['head_id'].isNull())
        name = props.get('name', '')
        if name:
            nameFilter = []
            dotedName = addDotsEx(name)
            nameFilter.append(table['shortName'].like(dotedName))
            nameFilter.append(table['fullName'].like(dotedName))
            nameFilter.append(table['title'].like(dotedName))
            cond.append(QtGui.qApp.db.joinOr(nameFilter))
        inn = props.get('INN', '')
        if inn:
            cond.append(table['INN'].eq(inn))
        ogrn = props.get('OGRN', '')
        if ogrn:
            cond.append(table['OGRN'].eq(ogrn))
        okato = props.get('OKATO', '')
        if okato:
            cond.append(table['OKATO'].eq(okato))
        tfomsCode = props.get('tfomsCode', '')
        if tfomsCode:
            cond.append(table['infisCode'].eq(tfomsCode))
        okved = props.get('OKVED', '')
        if okved:
            cond.append(table['OKVED'].like(okved))
        isInsurer = props.get('isInsurer', 0)
        if isInsurer:
            cond.append(table['isInsurer'].eq(isInsurer-1))
        isActive = props.get('isActive', 0)
        if isActive:
            cond.append(table['isActive'].eq(isActive-1))
        isSupplier = props.get('isSupplier', 0)
        if isSupplier:
            cond.append(table['isSupplier'].eq(isSupplier-1))
        hospitalBedProfileId = props.get('hospitalBedProfileId')
        if hospitalBedProfileId:
            # это можно, и наверное, нужно переделать на LEFT JOIN
            # но на первый взгляд и так прокатит
            cond.append('EXISTS (SELECT 1 FROM Organisation_HospitalBedProfile WHERE master_id=Organisation.id and hospitalBedProfile_id=%d)' % hospitalBedProfileId)
        isMedical = props.get('isMedical', 0)
        if isMedical:
            cond.append(table['isMedical'].eq(isMedical))
        smoCode = props.get('smoCode','')
        if smoCode:
            cond.append(table['smoCode'].like(smoCode))
        if self.filter:
            cond.append(self.filter)
        return db.getIdList(table.name(), 'id', cond, self.order)


    def updateOrgsList(self, itemId):
        self.filter = None
        idList = self.select(self.props)
        self.model.setIdList(idList, itemId)
        if idList:
            self.tblItems.selectRow(0)
        self.setCurrentItemId(itemId)
        self.label.setText(u'всего: %d' % len(idList))
        self.btnSelect.setFocus(Qt.OtherFocusReason)
        self.props = {}


    @pyqtSignature('')
    def on_btnSelect_clicked(self):
        self.renewListAndSetTo(self.currentItemId())
        self.accept()


    @pyqtSignature('')
    def on_btnNew_clicked(self):
        dialog = self.getItemEditor()
        name = self.props.get('name', '')
        if name:
            words = forceStringEx(name).split(u'...')
            if len(words) == 1 and (u'...' not in words[0].lower()):
                name = words[0]
                dialog.edtFullName.setText(name)
                dialog.edtShortName.setText(name)
                dialog.edtTitle.setText(name)
        try:
            if dialog.exec_():
                itemId = dialog.itemId()
                self.updateOrgsList(itemId)
        finally:
            dialog.deleteLater()


    @pyqtSignature('')
    def on_btnEdit_clicked(self):
        itemId = self.currentItemId()
        if itemId:
            dialog = self.getItemEditor()
            try:
                dialog.load(itemId)
                if dialog.exec_():
                    self.updateOrgsList(itemId)
            finally:
                dialog.deleteLater()
        else:
            self.on_btnNew_clicked()

#
# ##########################################################################
#

class COrgFilterDialog(QtGui.QDialog, Ui_OrgFilterDialog):
    def __init__(self,  parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.edtName.setFocus(Qt.ShortcutFocusReason)
        self.cmbHospitalBedProfile.setTable('rbHospitalBedProfile', addNone=True)
        self.cmbActive.setCurrentIndex(2)
        self.setHeadOrgVisible(True)
#        self.cmbHospitalBedProfile.setValue(None)


    def setHeadOrgVisible(self, value):
        self.isHeadOrgVisible = value
        self.lblHead.setVisible(value)
        self.cmbHead.setVisible(value)
        self.btnSelectHeadOrganisation.setVisible(value)


    def setProps(self,  props):
        if self.isHeadOrgVisible:
            self.cmbHead.setValue(props.get('headOrgId', None))
        self.edtName.setText(props.get('name', ''))
        self.edtINN.setText(props.get('INN',   ''))
        self.edtOGRN.setText(props.get('OGRN', ''))
        self.edtOKATO.setText(props.get('OKATO', ''))
        self.edtTfomsCode.setText(props.get('tfomsCode', ''))
        self.edtOKVED.setText(props.get('OKVED', ''))
        self.cmbIsInsurer.setCurrentIndex(props.get('isInsurer', 0))
        self.cmbHospitalBedProfile.setValue(props.get('hospitalBedProfileId'))
        self.cmbIsMedical.setCurrentIndex(props.get('isMedical', 0))
        self.cmbActive.setCurrentIndex(props.get('isActive', 2))
        self.cmbSupplier.setCurrentIndex(props.get('isSupplier', 0))
        self.chkHeadVisible.setChecked(props.get('iHeadVisible', False))
        self.edtSMOCode.setText(props.get('smoCode', ''))


    def props(self):
        result = {}
        if self.isHeadOrgVisible:
            result['headOrgId'] = forceRef(self.cmbHead.value())
        result['name'] = forceStringEx(self.edtName.text())
        result['INN'] = forceStringEx(self.edtINN.text())
        result['OGRN'] = forceStringEx(self.edtOGRN.text())
        result['OKATO'] = forceStringEx(self.edtOKATO.text())
        result['tfomsCode'] = forceStringEx(self.edtTfomsCode.text())
        result['OKVED'] = forceStringEx(self.edtOKVED.text())
        result['isInsurer'] = self.cmbIsInsurer.currentIndex()
        result['hospitalBedProfileId'] = self.cmbHospitalBedProfile.value()
        result['isMedical'] = self.cmbIsMedical.currentIndex()
        result['isActive'] = self.cmbActive.currentIndex()
        result['isSupplier'] = self.cmbSupplier.currentIndex()
        result['iHeadVisible'] = self.chkHeadVisible.isChecked()
        result['smoCode'] = forceStringEx(self.edtSMOCode.text())
        return result


    @pyqtSignature('')
    def on_btnSelectHeadOrganisation_clicked(self):
        headOrgId = selectOrganisation(self, self.cmbHead.value(), showListFirst = False, isHeadOrgVisible = False)
        self.cmbHead.updateModel()
        if headOrgId:
            self.cmbHead.setValue(headOrgId)


#
# ##########################################################################
#

class COrgEditor(CItemEditorBaseDialog, Ui_OrgEditorDialog):
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'Organisation')
        self.props = parent.props
        self.addModels('OrganisationAccounts', COrganisationAccountsModel(self))
        self.addModels('PolicySerials', CPolicySerialsModel(self))
        self.addModels('HospitalBedProfiles', CHospitalBedProfilesModel(self))
        self.addModels('Specialitys', CSpecialitysModel(self))
        self.addModels('Services', CServicesModel(self))
        self.addModels('Identification', CIdentificationModel(self, 'Organisation_Identification', 'Organisation'))
        self.addModels('License', CLicenseModel(self))

        self.addObject('btnMDLPRequest', QtGui.QPushButton(u'Запросить в МДЛП', self))

        self.setupUi(self)
        self.tblOrganisationAccounts.addPopupDelRow()
        self.tabWidget.setTabEnabled(3, False)
        self.setWindowTitleEx(u'Организация')

        self.setModels(self.tblOrganisationAccounts, self.modelOrganisationAccounts, self.selectionModelOrganisationAccounts)
        self.setModels(self.tblPolicySerials,        self.modelPolicySerials,        self.selectionModelPolicySerials)
        self.setModels(self.tblHospitalBedProfiles,  self.modelHospitalBedProfiles,  self.selectionModelHospitalBedProfiles)
        self.setModels(self.tblSpecialitys,          self.modelSpecialitys,          self.selectionModelSpecialitys)
        self.setModels(self.tblServices,             self.modelServices,             self.selectionModelServices)
        self.setModels(self.tblIdentification,       self.modelIdentification,       self.selectionModelIdentification)
        self.setModels(self.tblLicense,              self.modelLicense,              self.selectionModelLicense)

        self.tblPolicySerials.addPopupDelRow()
        #self.tblHospitalBedProfiles.addPopupDelRow()
        #self.tblSpecialitys.addPopupDelRow()
        #self.tblServices.addPopupDelRow()
        self.tblIdentification.addPopupDelRow()
        #self.tblIdentification.setDelRowsChecker()
        self.tblLicense.addPopupDelRow()

        self.cmbNet.setTable(rbNet, True)
        self.cmbOKPF.setTable(rbOKPF, True)
        self.cmbOKFS.setTable(rbOKFS, True)
        self.cmbArea.setAreaSelectable(True)
        self.on_chkKLADR_toggled(False)
        self.setupDirtyCather()
        
        self.buttonBox.addButton(self.btnMDLPRequest, QtGui.QDialogButtonBox.ActionRole)
        self.btnMDLPRequest.setEnabled(True if QtGui.qApp.isMdlpEnabled() else False)
        if self.props.get('INN', None):
            self.edtINN.setText(self.props['INN'])
        if self.props.get('OGRN', None):
            self.edtOGRN.setText(self.props['OGRN'])

    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(self.edtFullName,          record, 'fullName')
        setLineEditValue(self.edtShortName,         record, 'shortName')
        setLineEditValue(self.edtTitle,             record, 'title')
        setLineEditValue(self.edtAddress,           record, 'Address')
        setRBComboBoxValue(self.cmbHead,            record, 'head_id')

        setLineEditValue(self.edtOGRN,              record, 'OGRN')
        setLineEditValue(self.edtINN,               record, 'INN')
        setLineEditValue(self.edtKPP,               record, 'KPP')
        setLineEditValue(self.edtFSS,               record, 'FSS')
        setLineEditValue(self.edtOKVEDName,             record, 'OKVED')
        setLineEditValue(self.edtOKATO,             record, 'OKATO')
        setRBComboBoxValue(self.cmbOKPF,            record, 'OKPF_id')
        setRBComboBoxValue(self.cmbOKFS,            record, 'OKFS_id')
        setLineEditValue(self.edtOKPO,              record, 'OKPO')

        setRBComboBoxValue(self.cmbChief,           record, 'chief_id')
        setLineEditValue(self.edtChief,             record, 'chiefFreeInput')
        setLineEditValue(self.edtAccountant,        record, 'accountant')
        setLineEditValue(self.edtPhone,             record, 'phone')
        setLineEditValue(self.edtEmail,             record, 'email')

        setLineEditValue(self.edtTfomsCode,         record, 'infisCode')
        setLineEditValue(self.edtTfomsExtCode,      record, 'tfomsExtCode')
#        setLineEditValue(self.edtObsoleteInfisCode, record, 'obsoleteInfisCode')
        setLineEditValue(self.edtMiacCode,          record, 'miacCode')
        setLineEditValue(self.edtSmoCode,           record, 'smoCode')
        setLineEditValue(self.edtUsishCode,         record, 'usishCode')
        setComboBoxValue(self.cmbIsMedical,         record, 'isMedical')
        setRBComboBoxValue(self.cmbNet,             record, 'net_id')

        setCheckBoxValue(self.chkIsInsurer,         record, 'isInsurer')
        setCheckBoxValue(self.chkIsActive,       record, 'isActive')
        self.cmbArea.setCode(forceString(record.value('area')))
        setCheckBoxValue(self.chkCompulsoryServiceStop, record, 'compulsoryServiceStop')
        setCheckBoxValue(self.chkVoluntaryServiceStop,  record, 'voluntaryServiceStop')
        setCheckBoxValue(self.chkIsSupplier, record, 'isSupplier')
        setTextEditValue(self.edtNotes,             record, 'notes')

        addressId = forceRef(record.value('address_id'))
        if addressId:
            address = getAddress(addressId)
            self.cmbKLADRCity.setCode(address.KLADRCode)
            self.cmbKLADRStreet.setCity(address.KLADRCode)
            self.cmbKLADRStreet.setCode(address.KLADRStreetCode)
            self.edtKLADRHouse.setText(address.number)
            self.edtKLADRCorpus.setText(address.corpus)
            self.chkKLADR.setChecked(True)
        else:
            self.cmbKLADRCity.setCode(QtGui.qApp.defaultKLADR())
            self.cmbKLADRStreet.setCity(QtGui.qApp.defaultKLADR())
            self.cmbKLADRStreet.setCode('')
            self.chkKLADR.setChecked(False)

        self.modelOrganisationAccounts.loadItems(self.itemId())
        self.modelPolicySerials.loadItems(self.itemId())
        self.modelHospitalBedProfiles.loadItems(self.itemId())
        self.modelSpecialitys.loadItems(self.itemId())
        self.modelServices.loadItems(self.itemId())
        self.modelIdentification.loadItems(self.itemId())
        self.modelLicense.loadItems(self.itemId())
        self.on_chkHBHideInactiveProfiles_toggled(True)
        self.on_chkSpecHideInactiveProfiles_toggled(True)
        self.on_chkServiceHideInactiveProfiles_toggled(True)


    def getRecord(self):
#        obsoleteInfisCode = forceString(self.edtObsoleteInfisCode.text())
#        obsoleteInfisCode = trim(obsoleteInfisCode.replace(',', ' ')).replace(' ', ',')

        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(self.edtFullName,          record, 'fullName')
        getLineEditValue(self.edtShortName,         record, 'shortName')
        getLineEditValue(self.edtTitle,             record, 'title')
        getLineEditValue(self.edtAddress,           record, 'Address')
        getRBComboBoxValue(self.cmbHead,            record, 'head_id')

        getLineEditValue(self.edtOGRN,              record, 'OGRN')
        getLineEditValue(self.edtINN,               record, 'INN')
        getLineEditValue(self.edtKPP,               record, 'KPP')
        getLineEditValue(self.edtFSS,               record, 'FSS')
        getLineEditValue(self.edtOKVEDName,             record, 'OKVED')
        getLineEditValue(self.edtOKATO,             record, 'OKATO')
        getRBComboBoxValue(self.cmbOKPF,            record, 'OKPF_id')
        getRBComboBoxValue(self.cmbOKFS,            record, 'OKFS_id')
        getLineEditValue(self.edtOKPO,              record, 'OKPO')

        getRBComboBoxValue(self.cmbChief,           record, 'chief_id')
        getLineEditValue(self.edtChief,             record, 'chiefFreeInput')
        getLineEditValue(self.edtAccountant,        record, 'accountant')
        getLineEditValue(self.edtPhone,             record, 'phone')
        getLineEditValue(self.edtEmail,             record, 'email')

        getLineEditValue(self.edtTfomsCode,         record, 'infisCode')
        getLineEditValue(self.edtTfomsExtCode,      record, 'tfomsExtCode')
#        record.setValue('obsoleteInfisCode',        toVariant(obsoleteInfisCode))
        getLineEditValue(self.edtMiacCode,          record, 'miacCode')

        getLineEditValue(self.edtSmoCode,           record, 'smoCode')
        getLineEditValue(self.edtUsishCode,         record, 'usishCode')

        getComboBoxValue(self.cmbIsMedical,         record, 'isMedical')
        getRBComboBoxValue(self.cmbNet,             record, 'net_id')

        getCheckBoxValue(self.chkIsInsurer,         record, 'isInsurer')
        getCheckBoxValue(self.chkIsActive,          record, 'isActive')
        area = self.cmbArea.code() if self.chkIsInsurer.isChecked() else ''
        record.setValue('area', toVariant(area))

        getCheckBoxValue(self.chkCompulsoryServiceStop, record, 'compulsoryServiceStop')
        getCheckBoxValue(self.chkVoluntaryServiceStop,  record, 'voluntaryServiceStop')
        getCheckBoxValue(self.chkIsSupplier, record, 'isSupplier')
        getTextEditValue(self.edtNotes, record, 'notes')

        if self.chkKLADR.isChecked():
            address = {
                'KLADRCode': self.cmbKLADRCity.code(),
                'KLADRStreetCode': self.cmbKLADRStreet.code() if self.cmbKLADRStreet.code() else '',
                'number': forceStringEx(self.edtKLADRHouse.text()),
                'corpus': forceStringEx(self.edtKLADRCorpus.text()),
            }
            addressId = getAddressId(address)
            record.setValue(record.indexOf('address_id'), toVariant(addressId))
        else:
            record.setValue(record.indexOf('address_id'), toVariant(None))

        return record


    def saveInternals(self, id):
        self.modelOrganisationAccounts.saveItems(id)
        self.modelPolicySerials.saveItems(id)
        self.modelHospitalBedProfiles.saveItems(id)
        self.modelSpecialitys.saveItems(id)
        self.modelServices.saveItems(id)
        self.modelIdentification.saveItems(id)
        self.modelLicense.saveItems(id)


    def checkDataEntered(self):
        result = True
        message = u'Необходимо указать '

        for record in self.modelLicense._items:
            begDate = forceDate(record.value('begDate'))
            endDate = forceDate(record.value('endDate'))
            if endDate and begDate > endDate:
                self.checkValueMessage(u'Дата начала действия лицензии не может быть позже даты окончания действия лицензии', False, self)
                return False
            if begDate > QDate.currentDate():
                if not self.checkValueMessage(u'Дата начала действия лицензии еще не наступила', True, self.tblLicense):
                    return False

        if self.chkIsInsurer.isChecked() and self.chkIsActive.isChecked() and not self.cmbArea.code():
            self.checkValueMessageIgnoreAll(message + u'Регион', False, self.edtOGRN)
            return False
        result = result and self.checkDataProfiles(self.modelHospitalBedProfiles, self.tblHospitalBedProfiles, u'hospitalBedProfile_id', message + u'Профиль койки', message + u'дату начала действия профиля')
        result = result and self.checkDataProfiles(self.modelSpecialitys, self.tblSpecialitys, u'speciality_id', message + u'Специальность', message + u'дату начала действия специальности')
        result = result and self.checkDataProfiles(self.modelServices, self.tblServices, u'service_id', message + u'Услугу', message + u'дату начала действия услуги')
        if not result:
            return False
        if not forceStringEx(self.edtFullName.text()):
            res = self.checkValueMessageIgnoreAll(message + u'полное наименование', False, self.edtFullName)
            if res == 0:
                return False
            elif res == 2:
                return True
        if not forceStringEx(self.edtShortName.text()):
            res = self.checkValueMessageIgnoreAll(message + u'краткое наименование', False, self.edtShortName)
            if res == 0:
                return False
            elif res == 2:
                return True
        if not forceStringEx(self.edtOGRN.text()):
            res = self.checkValueMessageIgnoreAll(message + u'ОГРН', True, self.edtOGRN)
            if res == 0:
                return False
            elif res == 2:
                return True
        headOrgId = self.cmbHead.value()
        if not headOrgId:
            INN = forceStringEx(self.edtINN.text())
            if not INN:
                res = self.checkValueMessageIgnoreAll(message + u'ИНН', True, self.edtINN)
                if res == 0:
                    return False
                elif res == 2:
                    return True
            if INN and not self.checkINN(INN):
                res = self.checkValueMessageIgnoreAll(message + u'правильный ИНН', True, self.edtINN)
                if res == 0:
                    return False
                elif res == 2:
                    return True
            if not forceStringEx(self.edtKPP.text()):
                res = self.checkValueMessageIgnoreAll(message + u'КПП', True, self.edtKPP)
                if res == 0:
                    return False
                elif res == 2:
                    return True
            if not self.cmbOKPF.value():
                res = self.checkValueMessageIgnoreAll(message + u'ОКПФ', True, self.cmbOKPF)
                if res == 0:
                    return False
                elif res == 2:
                    return True
            if not self.cmbOKFS.value():
                res = self.checkValueMessageIgnoreAll(message + u'ОКФС', True, self.cmbOKFS)
                if res == 0:
                    return False
                elif res == 2:
                    return True
#        result = result and (forceStringEx(self.edtTitle.text()) or  self.checkValueMessageIgnoreAll(message + u'наименование для печати', False, self.edtTitle))
        if not forceStringEx(self.edtOKVEDName.text()):
            res =  self.checkValueMessageIgnoreAll(message + u'ОКВЭД', True, self.edtOKVEDName)
            if res == 0:
                return False
            elif res == 2:
                return True
        result = result and self.checkOKVED()
        if result:
            for row, record in enumerate(self.modelOrganisationAccounts.items()):
                if not self.checkAccountDataEntered(row, record):
                    return False

        result = result and self.checkDup()
        result = result and checkIdentification(self, self.tblIdentification)
        return result


    def checkINN(self, INN):
        def checksum(n, s):
            result = sum( d*int(c) for (d,c) in zip(n,s) ) % 11
            if result == 10:
                result = 0
            return result

        n121 = (7, 2, 4, 10, 3,  5, 9, 4, 6, 8)
        n122 = (3, 7, 2,  4, 10, 3, 5, 9, 4, 6, 8)
        n10  = (2, 4, 10, 3, 5, 9, 4, 6, 8)

        if len(INN) == 10:
            return str(checksum(n10, INN[0:9])) == INN[9]
        elif len(INN) == 12:
            return str(checksum(n121, INN[0:11]))+str(checksum(n122, INN[0:11])) == INN[10:12]
        else:
            return False


    def checkOKVED(self):
        fixedCodes = []
        str = forceString(self.edtOKVEDName.text())
        list = parseOKVEDList(str)
        for code in list:
            success, fixedCode = fixOKVED(code)
            fixedCodes.append(fixedCode)
        self.edtOKVEDName.setText(u','.join(fixedCodes))
        return True


    def checkAccountDataEntered(self, row, record):
        result = True
        column = record.indexOf('name')
        name = forceString(record.value(column))
        if result and not re.match(r'^\d{20}$', name):
            result = self.checkValueMessage(u'Номер расчетного счета должен состоять из 20 цифр', True, self.tblOrganisationAccounts, row, column)

        column = record.indexOf('bank_id')
        bankId = forceRef(record.value(column))
        if result and not bankId:
            result = self.checkValueMessage(u'Необходимо указать банк', True, self.tblOrganisationAccounts, row, column)
        return result


    def checkDup(self):
        dupCheckList = ((self.findDupByTfomsCode,  u'по коду ТФОМС'),
                        (self.findDupByINN,  u'по ИНН'),
                        (self.findDupByOGRN, u'по ОГРН'),
                       )
        for method, title in dupCheckList:
            idlist = method()
            if idlist:
                res = QtGui.QMessageBox.question( self,
                                                 u'Внимание!',
                                                 u'Обнаружен "двойник" %s\nИгнорировать?' % title,
                                                 QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                                 QtGui.QMessageBox.No)
                if res == QtGui.QMessageBox.No:
                    return False
        return True


    def checkDataProfiles(self, model, table, profileField, message1, message2):
        for row, item in enumerate(model.items()):
            if not forceRef(item.value(profileField)):
                return self.checkValueMessage(message1, False, table, row, item.indexOf(profileField))
            if not forceDate(item.value('begDate')):
                return self.checkValueMessage(message2, False, table, row, item.indexOf('begDate'))
        return True


    def findDup(self, cond):
        db = QtGui.qApp.db
        table = db.table('Organisation')
        id = self.itemId()
        if id:
            cond.append(table['id'].ne(id))
        return db.getIdList(table, where=cond, order='id')


    def findDupByTfomsCode(self):
        tfomsCode  = forceStringEx(self.edtTfomsCode.text())
        if tfomsCode:
            db = QtGui.qApp.db
            table = db.table('Organisation')
            cond = [table['infisCode'].eq(tfomsCode)]
            return self.findDup(cond)
        else:
            return None


    def findDupByINN(self):
        INN  = forceStringEx(self.edtINN.text())
        if not self.cmbHead.value() and INN:
            db = QtGui.qApp.db
            table = db.table('Organisation')
            cond = [table['INN'].eq(INN)]
            return self.findDup(cond)
        else:
            return None


    def findDupByOGRN(self):
        OGRN  = forceStringEx(self.edtOGRN.text())
        if not self.cmbHead.value() and OGRN:
            db = QtGui.qApp.db
            table = db.table('Organisation')
            cond = [table['OGRN'].eq(OGRN)]
            return self.findDup(cond)
        else:
            return None


    def updateInfoByHead(self, orgId):
        if orgId or self.cmbHead.value():
            db = QtGui.qApp.db
            record = db.getRecord(db.table('Organisation'), '*', orgId)
            if not record:
                record = QtSql.QSqlRecord()
            setLineEditValue(self.edtINN,    record, 'INN')
            setLineEditValue(self.edtKPP,    record, 'KPP')
            setLineEditValue(self.edtOGRN,   record, 'OGRN')
            setLineEditValue(self.edtFSS,    record, 'FSS')
            setLineEditValue(self.edtOKATO,  record, 'OKATO')
            setLineEditValue(self.edtOKPO,   record, 'OKPO')
            setRBComboBoxValue(self.cmbOKPF, record, 'OKPF_id')
            setRBComboBoxValue(self.cmbOKFS, record, 'OKFS_id')
        headIsEmpty = not orgId
        self.edtINN.setEnabled(headIsEmpty)
        self.edtKPP.setEnabled(headIsEmpty)
        self.edtOGRN.setEnabled(headIsEmpty)
        self.edtFSS.setEnabled(headIsEmpty)
        self.edtOKATO.setEnabled(headIsEmpty)
        self.edtOKPO.setEnabled(headIsEmpty)
        self.cmbOKPF.setEnabled(headIsEmpty)
        self.cmbOKFS.setEnabled(headIsEmpty)


    @pyqtSignature('')
    def on_btnSelectHeadOrganisation_clicked(self):
        headOrgId = selectOrganisation(self, self.cmbHead.value(), False)
        self.cmbHead.updateModel()
        if headOrgId:
            self.cmbHead.setValue(headOrgId)
#            self.updateInfoByHead(orgId)


    @pyqtSignature('int')
    def on_cmbHead_currentIndexChanged(self, index):
        headOrgId = self.cmbHead.value()
        self.updateInfoByHead(headOrgId)


    @pyqtSignature('int')
    def on_cmbIsMedical_currentIndexChanged(self, index):
        self.cmbNet.setEnabled(bool(index))
        self.lblNet.setEnabled(bool(index))


    @pyqtSignature('bool')
    def on_chkIsInsurer_toggled(self, checked):
        self.tabWidget.setTabEnabled(3, checked)


    @pyqtSignature('int')
    def on_cmbChief_currentIndexChanged(self, index):
        self.edtChief.setEnabled(not self.cmbChief.value())


    def getActiveProfiles(self, table, model, checked):
        items = model.items()
        if checked:
            currentDate = QDate.currentDate()
            for row, item in enumerate(items):
                begDate = forceDate(item.value('begDate'))
                endDate = forceDate(item.value('endDate'))
                if not((not begDate or begDate <= currentDate) and (not endDate or endDate >= currentDate)):
                    table.hideRow(row)
        else:
            for row, item in enumerate(items):
                table.showRow(row)


    @pyqtSignature('bool')
    def on_chkKLADR_toggled(self, checked):
        self.edtAddress.setDisabled(checked)
        self.cmbKLADRCity.setEnabled(checked)
        self.cmbKLADRStreet.setEnabled(checked)
        self.edtKLADRHouse.setEnabled(checked)
        self.edtKLADRCorpus.setEnabled(checked)


    @pyqtSignature('int')
    def on_cmbKLADRCity_currentIndexChanged(self, val):
        self.cmbKLADRStreet.setCity(self.cmbKLADRCity.code())


    @pyqtSignature('bool')
    def on_chkHBHideInactiveProfiles_toggled(self, checked):
        self.getActiveProfiles(self.tblHospitalBedProfiles, self.modelHospitalBedProfiles, checked)


    @pyqtSignature('bool')
    def on_chkSpecHideInactiveProfiles_toggled(self, checked):
        self.getActiveProfiles(self.tblSpecialitys, self.modelSpecialitys, checked)


    @pyqtSignature('bool')
    def on_chkServiceHideInactiveProfiles_toggled(self, checked):
        self.getActiveProfiles(self.tblServices, self.modelServices, checked)


    @pyqtSignature('')
    def on_btnMDLPRequest_clicked(self):
        def appendIdentification(model, mdlpId, result, itemId, newRecord=True):
            if newRecord:
                db = QtGui.qApp.db
                tableOI = db.table('Organisation_Identification')
                cond = [
                    tableOI['master_id'].eq(itemId),
                    tableOI['system_id'].eq(mdlpId),
                ]
                recordsI = db.getRecordList(tableOI, '*', cond)
                hasRec = False
                if recordsI:
                    for record in recordsI:
                        systemId = forceString(record.value('value'))
                        deleted = forceInt(record.value('deleted'))
                        if systemId == result.sysId:
                            hasRec = True
                            if deleted:
                                record.setValue('deleted', toVariant(0))
                            else:
                                break
                        else:
                            record.setValue('deleted', toVariant(1))
                        db.updateRecord(tableOI, record)
                    if not hasRec:
                        model.addIdentification(mdlpId, result.sysId)
                    else:
                        model.loadItems(itemId)
                else:
                    model.addIdentification(mdlpId, result.sysId)
            else:
                item = model.items()[0]
                if forceString(item.value('system_id')) != result.sysId:
                    item.setValue('deleted', toVariant(1))
                    model.emitAllChanged()
                    model.addIdentification(mdlpId, result.sysId)

        cert = None
        api = None
        msg = u''
        try:
            api = MSCApi(QtGui.qApp.getCsp())
        except Exception as e:
            msg = e.message
        if api and not msg:
            try:
                cert = QtGui.qApp.getUserCert(api)
            except Exception as e:
                msg = e.message
        if msg:
            QtGui.QMessageBox.warning(None, u'Ошибка получения сертификата', anyToUnicode(msg),
                                      QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
        if cert:
            from Stock.Mdlp.connection import CMdlpConnection
            connection = CMdlpConnection()
            searchRequsitesList = []
            inn = forceString(self.edtINN.text()) or None
            ogrn = forceString(self.edtOGRN.text()) or None
            systemId = None
            response = None
            if ogrn and not re.search(r'\d{13}', ogrn):
                self.checkValueMessage(u'Необходимо указать корректное значение ОГРН', False, self.edtOGRN)
                return
            if not inn and not ogrn and not systemId:
                self.checkValueMessage(u'Необходимо заполнить ИНН и/или ОГРН', False, self.edtINN)
                return
            if inn:
                response = connection.getPartners(inn=inn)
                if not response:
                    searchRequsitesList.append(u'- <b>ИНН</b> %s' % inn)
            if not response:
                if ogrn:
                    response = connection.getPartners(ogrn=ogrn)
                    if not response:
                        searchRequsitesList.append(u'- <b>ОГРН</b> %s' % ogrn)
            if response:
                checkData = {}
                result = response[0]
                if not self.edtFullName.text():
                    self.edtFullName.setText(result.name)
                else:
                    if self.edtFullName.text() != result.name:
                        checkData[forceString(self.lblFullName.text())] = [result.name, self.edtFullName.objectName()]
                if not self.edtShortName.text():
                    self.edtShortName.setText(result.name)
                if not self.edtTitle.text():
                    self.edtTitle.setText(result.name)
                chiefName = u' '.join([result.lastName, result.firstName, result.middleName])
                chiefNameOrig = forceString(self.edtChief.text())
                if not self.edtChief.text():
                    self.edtChief.setText(chiefName)
                else:
                    if chiefNameOrig.lower().strip() != chiefName.lower().strip():
                        checkData[forceString(self.lblChief.text())] = [chiefName, self.edtChief.objectName()]
                if not ogrn:
                    self.edtOGRN.setText(result.ogrn)
                else:
                    if self.edtOGRN.text() != result.ogrn:
                        checkData[forceString(self.lblOGRN.text())] = [result.ogrn, self.edtOGRN.objectName()]
                if not inn:
                    self.edtINN.setText(result.inn)
                else:
                    if self.edtINN.text() != result.inn:
                        checkData[forceString(self.lblINN.text())] = [result.inn, self.edtINN.objectName()]
                if not self.edtKPP.text():
                    self.edtKPP.setText(result.kpp)
                else:
                    if self.edtKPP.text() != result.kpp:
                        checkData[forceString(self.lblKPP.text())] = [result.kpp, self.edtKPP.objectName()]
                self.chkIsSupplier.setChecked(True)
                self.chkIsActive.setChecked(True)
                mdlpId = QtGui.qApp.db.translate('rbAccountingSystem', 'urn', 'urn:mdlp:anyId', 'id')
                model = self.modelIdentification
                if model.items():
                    item = model.items()[0]
                    if forceString(item.value('value')) != result.sysId:
                        checkData[u'SysID'] = [result.sysId, None]
                else:
                    appendIdentification(model, mdlpId, result, self.itemId())

                if checkData:
                    diffString = u'<br>'.join([u'<span><b>%s</b></span>: %s' % (k, v[0]) for k, v in checkData.items()])
                    if QtGui.QMessageBox.question(None,
                                                  u'Внимание!',
                                                  u'Обнаружены расхождения с данными организации из МДЛП:<br><br>%s'
                                                  u'<br><br>Выполнить обновление данных в МИС?' % diffString,
                                                  QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                  QtGui.QMessageBox.Yes) == QtGui.QMessageBox.Yes:
                        for k, v in checkData.items():
                            if k == u'SysID':
                                appendIdentification(model, mdlpId, result, self.itemId(), False)
                            else:
                                textObj = self.findChild(QtGui.QLineEdit, str(v[1]))
                                textObj.setText(v[0])
                        QtGui.QMessageBox.information(None,
                                                      u'Внимание!',
                                                      u'Данные успешно обновлены!',
                                                      QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
            else:
                searchRequsitesString = u'<br>'.join(searchRequsitesList)
                QtGui.QMessageBox.warning(None,
                                          u'Внимание!',
                                          u'В сервисе МДЛП не найдено информации по указанным реквизитам:'
                                          u'<br><br>%s' % searchRequsitesString,
                                          QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)


class COrganisationAccountsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Organisation_Account', 'id', 'organisation_id', parent)
        self.addCol(CInDocTableCol(     u'Расчетный счет',  'name',    22, maxLength=20, inputMask='9'*20))
        self.addCol(CInDocTableCol(     u'Лицевой счет',  'personalAccount',    22, maxLength=20))
        self.addCol(CBankInDocTableCol( u'Банк',            'bank_id', 22))
        self.addCol(CInDocTableCol(     u'Наименование в банке',  'bankName', 22))
        self.addCol(CInDocTableCol(     u'Примечания',      'notes',   22))
        self.addCol(CBoolInDocTableCol( u'Нал',             'cash',    4))



class CBankInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width):
        CInDocTableCol.__init__(self, title, fieldName, width)


    def toString(self, value, record):
        bankId = forceRef(value)
        return QVariant(getShortBankName(bankId))


    def createEditor(self, parent):
        editor = CBankSelectButton(parent)
        return editor


    def setEditorData(self, editor, value, record):
        editor.setBankId(forceRef(value))


    def getEditorData(self, editor):
        return toVariant(editor.bankId)



class CBankSelectButton(QtGui.QPushButton):
    def __init__(self,  parent):
        QtGui.QPushButton.__init__(self, parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.bankId = None
        self.connect(self, SIGNAL('clicked()'), self.selectBank)


    def setBankId(self,  bankId):
        if bankId != self.bankId:
            self.bankId = bankId
            self.setText(getShortBankName(self.bankId))


    @pyqtSignature('')
    def selectBank(self):
        dlg = CBanksList(self, True)
        dlg.setCurrentItemId(self.bankId)
        if dlg.selectItem():
            self.setBankId(dlg.currentItemId())
        dlg.deleteLater()


class CPolicySerialsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Organisation_PolicySerial', 'id', 'organisation_id', parent)
        self.addCol(CRBInDocTableCol(u'Тип', 'policyType_id', 30, 'rbPolicyType'))
        self.addCol(CInDocTableCol(     u'Серия',  'serial',  16, maxLength=8))


class CHospitalBedProfilesModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Organisation_HospitalBedProfile', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Профиль', 'hospitalBedProfile_id', 30, 'rbHospitalBedProfile'))
        self.addCol(CDateInDocTableCol(u'Дата начала',    'begDate', 20, canBeEmpty=True))
        self.addCol(CDateInDocTableCol(u'Дата окончания', 'endDate', 20, canBeEmpty=True))
        self.addCol(CTextInDocTableCol(u'Примечание',     'note', 30))


    def cellReadOnly(self, index):
        if index.column() == self.getColIndex('hospitalBedProfile_id'):
            row = index.row()
            if 0 <= row < len(self._items):
                record = self._items[row]
                if record and forceRef(record.value('id')):
                    return True
        return False


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            if index.column() == self.getColIndex('hospitalBedProfile_id') and not forceRef(value):
                row = index.row()
                if row == len(self._items):
                    return False
                return self.removeRows(row, 1)
        return CInDocTableModel.setData(self, index, value, role)


class CSpecialitysModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Organisation_Speciality', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Специальность',    'speciality_id', 30, 'rbSpeciality'))
        self.addCol(CDateInDocTableCol(u'Дата начала',    'begDate', 20, canBeEmpty=True))
        self.addCol(CDateInDocTableCol(u'Дата окончания', 'endDate', 20, canBeEmpty=True))
        self.addCol(CTextInDocTableCol(u'Примечание',     'note', 30))


    def cellReadOnly(self, index):
        if index.column() == self.getColIndex('speciality_id'):
            row = index.row()
            if 0 <= row < len(self._items):
                record = self._items[row]
                if record and forceRef(record.value('id')):
                    return True
        return False


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            if index.column() == self.getColIndex('speciality_id') and not forceRef(value):
                row = index.row()
                if row == len(self._items):
                    return False
                return self.removeRows(row, 1)
        return CInDocTableModel.setData(self, index, value, role)


class CServicesModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Organisation_Service', 'id', 'master_id', parent)
        self.addCol(CRBServiceInDocTableCol(u'Услуга', 'service_id', 30, 'rbService'))
        self.addCol(CDateInDocTableCol(u'Дата начала',    'begDate', 20, canBeEmpty=True))
        self.addCol(CDateInDocTableCol(u'Дата окончания', 'endDate', 20, canBeEmpty=True))
        self.addCol(CTextInDocTableCol(u'Примечание',     'note', 30))


    def cellReadOnly(self, index):
        if index.column() == self.getColIndex('service_id'):
            row = index.row()
            if 0 <= row < len(self._items):
                record = self._items[row]
                if record and forceRef(record.value('id')):
                    return True
        return False


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            if index.column() == self.getColIndex('service_id') and not forceRef(value):
                row = index.row()
                if row == len(self._items):
                    return False
                return self.removeRows(row, 1)
        return CInDocTableModel.setData(self, index, value, role)


class CLicenseModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Organisation_License', 'id', 'master_id', parent)
        self.addCol(CInDocTableCol(u'Номер', 'number', 30))
        self.addCol(CInDocTableCol(u'Кем выдана', 'issuer', 30))
        self.addCol(CDateInDocTableCol(u'Дата выдачи', 'issueDate', 20))
        self.addCol(CDateInDocTableCol(u'Начало действия', 'begDate', 20, canBeEmpty=True))
        self.addCol(CDateInDocTableCol(u'Окончание действия', 'endDate', 20, canBeEmpty=True))

