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

from PyQt4.QtCore import pyqtSignature

from library.AgeSelector     import composeAgeSelector, parseAgeSelector
from library.interchange import getComboBoxValue, getLineEditValue, getRBComboBoxValue, setComboBoxValue, \
    setLineEditValue, setRBComboBoxValue, setCheckBoxValue, getCheckBoxValue
from library.InDocTable      import CInDocTableModel, CRBInDocTableCol

from library.ItemEditorDialogWithIdentification import CItemEditorDialogWithIdentification
from library.ItemsListDialog import CItemsListDialog
from library.TableModel      import CEnumCol, CRefBookCol, CTextCol

from library.Utils           import forceString, forceStringEx, toVariant

from RefBooks.Service.SelectService import selectService
from RefBooks.Tables         import rbCode, rbName, rbService, rbSpeciality

from Ui_RBSpecialityEditor import Ui_ItemEditorDialog


class CRBSpecialityList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(   u'Код',                  [rbCode], 10),
            CTextCol(   u'Наименование',         [rbName], 30),
            CTextCol(   u'Код ОКСО',             ['OKSOCode'], 10),
            CTextCol(   u'Наименование ОКСО',    ['OKSOName'], 30),
            CTextCol(   u'Федеральный код',      ['federalCode'], 10),
            CTextCol(   u'Код ЕГИСЗ',            ['usishCode'],   10),
            CTextCol(   u'Региональный код',     ['regionalCode'], 10),
            CRefBookCol(u'Профиль МП',           ['medicalAidProfile_id'], 'rbMedicalAidProfile', 30),
            CRefBookCol(u'Услуга',               ['ambAppointmentService_id'], 'rbService', 30),
            CEnumCol(   u'Пол',                  ['sex'], ['', u'М', u'Ж'], 10),
            CTextCol(   u'Возраст',              ['age'], 10),
            CTextCol(   u'Фильтр по МКБ',        ['mkbFilter'], 20),
            ], rbSpeciality, [rbCode, rbName])
        self.setWindowTitleEx(u'Специальности врачей')

    def getItemEditor(self):
        return CRBSpecialityEditor(self)
#
# ##########################################################################
#

class CRBSpecialityEditor(Ui_ItemEditorDialog, CItemEditorDialogWithIdentification):
    def __init__(self,  parent):
        CItemEditorDialogWithIdentification.__init__(self, parent, rbSpeciality)
        self.setWindowTitleEx(u'Специальность врача')
        for cmb in (self.cmbLocalService, self.cmbProvinceService, self.cmbOtherService, self.cmbAmbAppointmentService,
                    self.cmbAltLocalService, self.cmbAltProvinceService, self.cmbAltOtherService):
            cmb.setTable(rbService, True)
            cmb.setCurrentIndex(0)
        self.cmbMedicalAidProfile.setTable('rbMedicalAidProfile')
        self.cmbSex.setCurrentIndex(0)
        self.setupDirtyCather()


    def preSetupUi(self):
        CItemEditorDialogWithIdentification.preSetupUi(self)
        self.addModels('MedicalAidProfiles',
                         CMedicalAidProfileListModel(self)
                      )


    def postSetupUi(self):
        CItemEditorDialogWithIdentification.postSetupUi(self)
        self.setModels(self.tblMedicalAidProfiles,
                       self.modelMedicalAidProfiles,
                       self.selectionModelMedicalAidProfiles)
        self.tblIdentification.addPopupDelRow()


    def setRecord(self, record):
        CItemEditorDialogWithIdentification.setRecord(self, record)
        setLineEditValue(self.edtOKSOName, record, 'OKSOName')
        setLineEditValue(self.edtOKSOCode, record, 'OKSOCode')
        setLineEditValue(self.edtFederalCode, record, 'federalCode')
        setLineEditValue(self.edtUsishCode, record, 'usishCode')
        setLineEditValue(self.edtRegionalCode, record, 'regionalCode')
        setRBComboBoxValue(self.cmbMedicalAidProfile, record, 'medicalAidProfile_id')
        setRBComboBoxValue(self.cmbLocalService, record, 'service_id')
        setRBComboBoxValue(self.cmbProvinceService, record, 'provinceService_id')
        setRBComboBoxValue(self.cmbOtherService, record, 'otherService_id')
        setRBComboBoxValue(self.cmbAmbAppointmentService, record, 'ambAppointmentService_id')
        setRBComboBoxValue(self.cmbAltLocalService, record, 'altService_id')
        setRBComboBoxValue(self.cmbAltProvinceService, record, 'altProvinceService_id')
        setRBComboBoxValue(self.cmbAltOtherService, record, 'altOtherService_id')
        setComboBoxValue(self.cmbSex, record, 'sex')
        setCheckBoxValue(self.chkIsHigh, record, 'isHigh')
        (begUnit, begCount, endUnit, endCount) = parseAgeSelector(forceString(record.value('age')))
        self.cmbBegAgeUnit.setCurrentIndex(begUnit)
        self.edtBegAgeCount.setText(str(begCount))
        self.cmbEndAgeUnit.setCurrentIndex(endUnit)
        self.edtEndAgeCount.setText(str(endCount))
        setLineEditValue(   self.edtMKBFilter,  record, 'mkbFilter')
        self.modelMedicalAidProfiles.loadItems(self.itemId())


    def getRecord(self):
        record = CItemEditorDialogWithIdentification.getRecord(self)
        getLineEditValue(self.edtOKSOName, record, 'OKSOName')
        getLineEditValue(self.edtOKSOCode, record, 'OKSOCode')
        getLineEditValue(self.edtFederalCode, record, 'federalCode')
        getLineEditValue(self.edtUsishCode, record, 'usishCode')
        getLineEditValue(self.edtRegionalCode, record, 'regionalCode')
        getRBComboBoxValue(self.cmbMedicalAidProfile, record, 'medicalAidProfile_id')
        getRBComboBoxValue(self.cmbLocalService, record, 'service_id')
        getRBComboBoxValue(self.cmbProvinceService, record, 'provinceService_id')
        getRBComboBoxValue(self.cmbOtherService, record, 'otherService_id')
        getRBComboBoxValue(self.cmbAmbAppointmentService, record, 'ambAppointmentService_id')
        getRBComboBoxValue(self.cmbAltLocalService, record, 'altService_id')
        getRBComboBoxValue(self.cmbAltProvinceService, record, 'altProvinceService_id')
        getRBComboBoxValue(self.cmbAltOtherService, record, 'altOtherService_id')
        getComboBoxValue(self.cmbSex, record, 'sex')
        getCheckBoxValue(self.chkIsHigh, record, 'isHigh')
        record.setValue('age',        toVariant(composeAgeSelector(
                    self.cmbBegAgeUnit.currentIndex(),  forceStringEx(self.edtBegAgeCount.text()),
                    self.cmbEndAgeUnit.currentIndex(),  forceStringEx(self.edtEndAgeCount.text())
                        )))
        getLineEditValue(   self.edtMKBFilter,  record, 'mkbFilter')
        return record


    def saveInternals(self, id):
        CItemEditorDialogWithIdentification.saveInternals(self, id)
        self.modelMedicalAidProfiles.saveItems(id)


    def selectService(self, cmbService):
        serviceId = selectService(self, cmbService)
        if serviceId:
            cmbService.setValue(serviceId)


    @pyqtSignature('')
    def on_btnSelectLocalService_clicked(self):
        self.selectService(self.cmbLocalService)


    @pyqtSignature('')
    def on_btnSelectProvinceService_clicked(self):
        self.selectService(self.cmbProvinceService)


    @pyqtSignature('')
    def on_btnSelectOtherService_clicked(self):
        self.selectService(self.cmbOtherService)

    @pyqtSignature('')
    def on_btnSelectAmbAppointmentService_clicked(self):
        self.selectService(self.cmbAmbAppointmentService)

    @pyqtSignature('')
    def on_btnSelectAltLocalService_clicked(self):
        self.selectService(self.cmbAltLocalService)


    @pyqtSignature('')
    def on_btnSelectAltProvinceService_clicked(self):
        self.selectService(self.cmbAltProvinceService)


    @pyqtSignature('')
    def on_btnSelectAltOtherService_clicked(self):
        self.selectService(self.cmbAltOtherService)

#
# ######################################################################
#

class CMedicalAidProfileListModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbSpeciality_MedicalAidProfile', 'id', 'master_id', parent)

        self.addCol(CRBInDocTableCol(  u'Профиль',
                                       'medicalAidProfile_id',
                                       40,
                                       'rbMedicalAidProfile',
                                       addNone=False,
                                    )
                   )
