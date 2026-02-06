# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL

from library.AgeSelector     import parseAgeSelector, composeAgeSelector

from library.interchange     import ( setCheckBoxValue,
                                      getComboBoxValue,
                                      setComboBoxValue,
                                      getCheckBoxValue,
                                      setRBComboBoxValue,
                                      getRBComboBoxValue,
                                    )
from library.InDocTable      import CInDocTableModel
from library.ItemsListDialog import CItemsListDialog, CItemEditorDialog
from library.TableModel      import CTextCol
from library.Utils           import forceString, forceStringEx, toVariant

from RefBooks.Service.RBServiceComboBox import CRBServiceInDocTableCol
from RefBooks.Tables         import rbAppointmentPurpose, rbCode, rbName


from .Ui_RBAppointmentPurposeEditor import Ui_RBAppointmentPurposeEditorDialog

#

class CRBAppointmentPurposeList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',          [rbCode], 20),
            CTextCol(u'Наименование', [rbName], 40),
            ], rbAppointmentPurpose, [rbCode, rbName])
        self.setWindowTitleEx(u'Назначения приёма')
        self.actDuplicate = QtGui.QAction(u'Дублировать', self)
        self.actDuplicate.setObjectName('actDuplicate')
        self.connect(self.actDuplicate, SIGNAL('triggered()'), self.duplicateCurrentRow)
        self.tblItems.createPopupMenu([self.actDuplicate])


    def getItemEditor(self):
        return CRBAppointmentPurposeEditor(self)


#    def duplicateCurrentRow(self):
#        def duplicateCurrentInternal():
#            currentItemId = self.currentItemId()
#            if currentItemId:
#                db = QtGui.qApp.db
#                table = db.table('rbAppointmentPurpose')
#                db.transaction()
#                try:
#                    record = db.getRecord(table, '*', currentItemId)
#                    record.setValue('code', toVariant(forceString(record.value('code'))+'_1'))
#                    record.setValue('name', toVariant(forceString(record.value('name'))+'_1'))
#                    record.setNull('id')
#                    newItemId = db.insertRecord(table, record)
#                    db.commit()
#                except:
#                    db.rollback()
#                    QtGui.qApp.logCurrentException()
#                    raise
#                self.renewListAndSetTo(newItemId)
#        QtGui.qApp.call(self, duplicateCurrentInternal)


class CRBAppointmentPurposeEditor(Ui_RBAppointmentPurposeEditorDialog, CItemEditorDialog):
    def __init__(self,  parent):
        CItemEditorDialog.__init__(self, parent, rbAppointmentPurpose)
        self.setWindowTitleEx(u'Назначение приёма')
        self.cmbMedicalAidProfile.setTable('rbMedicalAidProfile', True)
        self.cmbMedicalAidProfile.setCurrentIndex(0)
        self.cmbFinance.setTable('rbFinance', addNone=True)
        self.setModels(self.tblServices, self.modelServices, self.selectionModelServices)
        self.tblServices.addPopupDelRow()
        self.setupDirtyCather()


    def preSetupUi(self):
        self.addModels('Services', CServicesModel(self))


    def setRecord(self, record):
        CItemEditorDialog.setRecord(self, record)
        setComboBoxValue(   self.cmbSex,            record, 'sex')
        (begUnit, begCount, endUnit, endCount) = parseAgeSelector(forceString(record.value('age')))
        self.cmbBegAgeUnit.setCurrentIndex(begUnit)
        self.edtBegAgeCount.setText(str(begCount))
        self.cmbEndAgeUnit.setCurrentIndex(endUnit)
        self.edtEndAgeCount.setText(str(endCount))
        setCheckBoxValue(self.chkEnablePrimaryRecord,       record, 'enablePrimaryRecord')
        setCheckBoxValue(self.chkEnableOwnRecord,           record, 'enableOwnRecord')
        setCheckBoxValue(self.chkEnableConsultancyRecord,   record, 'enableConsultancyRecord')
        setCheckBoxValue(self.chkEnableRecordViaInfomat,    record, 'enableRecordViaInfomat')
        setCheckBoxValue(self.chkEnableRecordViaCallCenter, record, 'enableRecordViaCallCenter')
        setCheckBoxValue(self.chkEnableRecordViaInternet,   record, 'enableRecordViaInternet')
        setComboBoxValue(self.cmbRequiredReferralType,      record, 'requiredReferralType')
        setCheckBoxValue(self.chkForExternalSchedule,       record, 'forExternalSchedule')
        setCheckBoxValue(self.chkRequireClientAttach,       record, 'requireClientAttach')
        setRBComboBoxValue(self.cmbMedicalAidProfile,       record, 'medicalAidProfile_id')
        setRBComboBoxValue(self.cmbFinance,                 record, 'finance_id')
        self.modelServices.loadItems(self.itemId())
        self.cmbFinance.setEnabled(False)


    def getRecord(self):
        record = CItemEditorDialog.getRecord(self)
        getComboBoxValue(   self.cmbSex,            record, 'sex')
        record.setValue('age',        toVariant(composeAgeSelector(
                    self.cmbBegAgeUnit.currentIndex(),  forceStringEx(self.edtBegAgeCount.text()),
                    self.cmbEndAgeUnit.currentIndex(),  forceStringEx(self.edtEndAgeCount.text())
                        )))
        getCheckBoxValue(self.chkEnablePrimaryRecord,       record, 'enablePrimaryRecord')
        getCheckBoxValue(self.chkEnableOwnRecord,           record, 'enableOwnRecord')
        getCheckBoxValue(self.chkEnableConsultancyRecord,   record, 'enableConsultancyRecord')
        getCheckBoxValue(self.chkEnableRecordViaInfomat,    record, 'enableRecordViaInfomat')
        getCheckBoxValue(self.chkEnableRecordViaCallCenter, record, 'enableRecordViaCallCenter')
        getCheckBoxValue(self.chkEnableRecordViaInternet,   record, 'enableRecordViaInternet')
        getComboBoxValue(self.cmbRequiredReferralType,      record, 'requiredReferralType')
        getCheckBoxValue(self.chkForExternalSchedule,       record, 'forExternalSchedule')
        getCheckBoxValue(self.chkRequireClientAttach,       record, 'requireClientAttach')
        getRBComboBoxValue(self.cmbMedicalAidProfile,       record, 'medicalAidProfile_id')
        getRBComboBoxValue(self.cmbFinance,                 record, 'finance_id')
        return record


    def saveInternals(self, id):
        self.modelServices.saveItems(id)


class CServicesModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbAppointmentPurpose_Service', 'id', 'master_id', parent)
        self.addCol(CRBServiceInDocTableCol(u'Услуга', 'service_id', 30, 'rbService'))
