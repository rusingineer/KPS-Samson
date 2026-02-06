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
# Переименовать в ActionTypeGroupEditor?

from PyQt4 import QtGui
from PyQt4.QtCore import QVariant, pyqtSignature

from library.AgeSelector import composeAgeSelector, parseAgeSelector
from library.DialogBase  import CDialogBase
from library.interchange import setCheckBoxValue, setComboBoxValue, setLineEditValue, setRBComboBoxValue, setSpinBoxValue, setDateEditValue
from library.Utils       import forceRef, forceString, forceStringEx, toVariant, forceDate

from .Ui_GroupActionTypeEditor import Ui_GroupActionTypeEditorDialog


class CGroupActionTypeEditor(CDialogBase, Ui_GroupActionTypeEditorDialog):
    def __init__(self,  parent, actionTypeIdList=[], patternActionTypeId=None):
        self._actionTypeIdList = actionTypeIdList
        self._table = QtGui.qApp.db.table('ActionType')
        CDialogBase.__init__(self,  parent)
        self.setupUi(self)
        self.cmbAddVisitScene.setTable('rbScene')
        self.cmbAddVisitType.setTable('rbVisitType')
        self._load(patternActionTypeId)
        self.setWindowTitle(u'Групповой редактор')


    def _load(self, actionTypeId):
        record = QtGui.qApp.db.getRecord(self._table, '*', actionTypeId)

        setComboBoxValue(self.cmbSex, record, 'sex')
        (begUnit, begCount, endUnit, endCount) = parseAgeSelector(forceString(record.value('age')))
        self.cmbBegAgeUnit.setCurrentIndex(begUnit)
        self.edtBegAgeCount.setText(str(begCount))
        self.cmbEndAgeUnit.setCurrentIndex(endUnit)
        self.edtEndAgeCount.setText(str(endCount))
        setComboBoxValue(   self.cmbDefaultStatus,             record, 'defaultStatus')
        setComboBoxValue(   self.cmbDefaultDirectionDate,      record, 'defaultDirectionDate')
        setComboBoxValue(   self.cmbDefaultPlannedEndDate,     record, 'defaultPlannedEndDate')
        setComboBoxValue(   self.cmbDefaultBegDate,            record, 'defaultBegDate')
        setComboBoxValue(   self.cmbDefaultEndDate,            record, 'defaultEndDate')
        setComboBoxValue(   self.cmbDefaultSetPersonInEvent,   record, 'defaultSetPersonInEvent')
        setRBComboBoxValue( self.cmbDefaultExecPerson,         record, 'defaultExecPerson_id')
        setComboBoxValue(   self.cmbDefaultPersonInEvent,      record, 'defaultPersonInEvent')
        setComboBoxValue(   self.cmbDefaultPersonInEditor,     record, 'defaultPersonInEditor')
        setComboBoxValue(   self.cmbExecPersonRequired,        record, 'isExecPersonRequired')
        self.cmbDefaultOrg.setValue(forceRef(record.value('defaultOrg_id')))
        setComboBoxValue(   self.cmbDefaultMKB,                record, 'defaultMKB')
        setComboBoxValue(   self.cmbMKBRequired,               record, 'isMKBRequired')
        setComboBoxValue(   self.cmbIsMorphologyRequired,      record, 'isMorphologyRequired')
        setLineEditValue(   self.edtOffice,                    record, 'office')
        setCheckBoxValue(   self.chkShowInForm,                record, 'showInForm')
        setCheckBoxValue(   self.chkShowTime,                  record, 'showTime')
        setCheckBoxValue(   self.chkRequiredCoordination,      record, 'isRequiredCoordination')
        setCheckBoxValue(   self.chkHasAssistant,              record, 'hasAssistant')
        setCheckBoxValue(   self.chkEditStatus,                record, 'editStatus')
        setComboBoxValue(   self.cmbNeedAttachFile,            record, 'isNeedAttachFile')
        setCheckBoxValue(   self.chkEditBegDate,               record, 'editBegDate')
        setCheckBoxValue(   self.chkEditEndDate,               record, 'editEndDate')
        setCheckBoxValue(   self.chkEditExecPers,              record, 'editExecPers')
        setCheckBoxValue(   self.chkEditNote,                  record, 'editNote')
        setLineEditValue(   self.edtContext,                   record, 'context')
        setCheckBoxValue(   self.chkIsPreferable,              record, 'isPreferable')
        setCheckBoxValue(   self.chkShowBegDate,               record, 'showBegDate')
        setCheckBoxValue(   self.chkDuplication,               record, 'duplication')
        setCheckBoxValue(   self.chkIgnoreVisibleRights,       record, 'ignoreVisibleRights')
        setCheckBoxValue(self.chkEditSetPerson,                record, 'editSetPerson')
        setCheckBoxValue(self.chkEditOrg,                      record, 'editOrg')
        setCheckBoxValue(   self.chkEditOrgStructure,          record, 'editOrgStructure')
        setSpinBoxValue(    self.edtAmount,                    record, 'amount')
        setSpinBoxValue(    self.edtMaxOccursInEvent,          record, 'maxOccursInEvent')
        setRBComboBoxValue( self.cmbServiceType,               record, 'serviceType')
        setComboBoxValue(   self.cmbExposeDateSelector,        record, 'exposeDateSelector')
        setCheckBoxValue(   self.chkPropertyAssignedVisible,   record, 'propertyAssignedVisible')
        self.chkPropertyAssignedRequired.setVisible(self.chkPropertyAssignedVisible.isChecked())
        setCheckBoxValue(   self.chkPropertyAssignedRequired,  record, 'propertyAssignedRequired')
        setCheckBoxValue(   self.chkPropertyUnitVisible,       record, 'propertyUnitVisible')
        setCheckBoxValue(   self.chkPropertyNormVisible,       record, 'propertyNormVisible')
        setCheckBoxValue(   self.chkPropertyEvaluationVisible, record, 'propertyEvaluationVisible')
        setCheckBoxValue(   self.chkPropertyCommentVisible,    record, 'propertyCommentVisible')
        setDateEditValue(   self.edtBegDate,                   record, 'begDate')
        setDateEditValue(   self.endEndDate,                   record, 'endDate')
        setCheckBoxValue(   self.chkAddVisit,                  record, 'addVisit')
        setRBComboBoxValue( self.cmbAddVisitScene,             record, 'addVisitScene_id')
        setRBComboBoxValue( self.cmbAddVisitType,              record, 'addVisitType_id')
        self.on_chkAddVisitGroup_toggled(False)


    def saveData(self):
        if not self.confirm():
            return False
        fields = {'id':None}
        if self.chkSex.isChecked():
            fields['sex'] = self.cmbSex.currentIndex()
        if self.chkAge.isChecked():
            fields['age'] = composeAgeSelector(self.cmbBegAgeUnit.currentIndex(),  forceStringEx(self.edtBegAgeCount.text()),
                                               self.cmbEndAgeUnit.currentIndex(),  forceStringEx(self.edtEndAgeCount.text()))
        if self.chkChkShowTime.isChecked():
            fields['showTime'] = self.chkShowTime.isChecked()
        if self.chkChkRequiredCoordination.isChecked():
            fields['isRequiredCoordination'] = self.chkRequiredCoordination.isChecked()
        if self.chkChkShowInForm.isChecked():
            fields['showInForm'] = self.chkShowInForm.isChecked()
        if self.chkAssistant.isChecked():
            fields['hasAssistant'] = self.chkHasAssistant.isChecked()
        if self.chkChkEditStatus.isChecked():
            fields['editStatus'] = self.chkEditStatus.isChecked()
        if self.chkChkEditBegDate.isChecked():
            fields['editBegDate'] = self.chkEditBegDate.isChecked()
        if self.chkChkEditEndDate.isChecked():
            fields['editEndDate'] = self.chkEditEndDate.isChecked()
        if self.chkChkEditExecPers.isChecked():
            fields['editExecPers'] = self.chkEditExecPers.isChecked()
        if self.chkChkEditNote.isChecked():
            fields['editNote'] = self.chkEditNote.isChecked()
        if self.chkContext.isChecked():
            fields['context'] = forceStringEx(self.edtContext.text())
        if self.chkPreferable.isChecked():
            fields['isPreferable'] = self.chkIsPreferable.isChecked()
        if self.chkChkShowBegDate.isChecked():
            fields['showBegDate'] = self.chkShowBegDate.isChecked()
        if self.chkChkDuplication.isChecked():
            fields['duplication'] = self.chkDuplication.isChecked()
        if self.chkChkIgnoreVisibleRights.isChecked():
            fields['ignoreVisibleRights'] = self.chkIgnoreVisibleRights.isChecked()
        if self.chkChkEditSetPerson.isChecked():
            fields['editSetPerson'] = self.chkEditSetPerson.isChecked()
        if self.chkChkEditOrg.isChecked():
            fields['editOrg'] = self.chkEditOrg.isChecked()
        if self.chkChkEditOrgStructure.isChecked():
            fields['editOrgStructure'] = self.chkEditOrgStructure.isChecked()
        if self.chkMaxOccursInEvent.isChecked():
            fields['maxOccursInEvent'] = self.edtMaxOccursInEvent.value()
        if self.chkServiceType.isChecked():
            fields['serviceType'] = self.cmbServiceType.value()
        if self.chkExposeDateSelector.isChecked():
            fields['exposeDateSelector'] = self.cmbExposeDateSelector.currentIndex()
        if self.chkDefaultStatus.isChecked():
            fields['defaultStatus'] = self.cmbDefaultStatus.value()
        if self.chkDefaultPlannedEndDate.isChecked():
            fields['defaultPlannedEndDate'] = self.cmbDefaultPlannedEndDate.currentIndex()
        if self.chkDefaultBegDate.isChecked():
            fields['defaultBegDate'] = self.cmbDefaultBegDate.currentIndex()
        if self.chkDefaultEndDate.isChecked():
            fields['defaultEndDate'] = self.cmbDefaultEndDate.currentIndex()
        if self.chkDefaultDirectionDate.isChecked():
            fields['defaultDirectionDate'] = self.cmbDefaultDirectionDate.currentIndex()
        if self.chkDefaultSetPersonInEvent.isChecked():
            fields['defaultSetPersonInEvent'] = self.cmbDefaultSetPersonInEvent.currentIndex()
        if self.chkDefaultExecPerson.isChecked():
            fields['defaultExecPerson_id'] = self.cmbDefaultExecPerson.value()
        if self.chkDefaultPersonInEvent.isChecked():
            fields['defaultPersonInEvent'] = self.cmbDefaultPersonInEvent.currentIndex()
        if self.chkDefaultPersonInEditor.isChecked():
            fields['defaultPersonInEditor'] = self.cmbDefaultPersonInEditor.currentIndex()
        if self.chkExecPersonRequired.isChecked():
            fields['isExecPersonRequired'] = self.cmbExecPersonRequired.currentIndex()
        if self.chkDefaultMKB.isChecked():
            fields['defaultMKB'] = self.cmbDefaultMKB.currentIndex()
        if self.chkMKBRequired.isChecked():
            fields['isMKBRequired'] = self.cmbMKBRequired.currentIndex()
        if self.chkNeedAttachFile.isChecked():
            fields['isNeedAttachFile'] = self.cmbNeedAttachFile.currentIndex()
        if self.chkIsMorphologyRequired.isChecked():
            fields['isMorphologyRequired'] = self.cmbIsMorphologyRequired.currentIndex()
        if self.chkDefaultOrg.isChecked():
            fields['defaultOrg_id'] = self.cmbDefaultOrg.value()
        if self.chkAmount.isChecked():
            fields['amount'] = self.edtAmount.value()
        if self.chkOffice.isChecked():
            fields['office'] = forceStringEx(self.edtOffice.text())
        if self.chkActionTypeValidFrom.isChecked():
            fields['begDate'] = forceDate(self.edtBegDate.date())
            fields['endDate'] = forceDate(self.endEndDate.date())
        if self.chkAddVisitGroup.isChecked():
            fields['addVisit'] = self.chkAddVisit.isChecked()
            fields['addVisitScene_id'] = self.cmbAddVisitScene.value()
            fields['addVisitType_id'] = self.cmbAddVisitType.value()
        if self.grpPropertiesFields.isChecked():
            fields['propertyAssignedVisible'] = self.chkPropertyAssignedVisible.isChecked()
            fields['propertyAssignedRequired'] = self.chkPropertyAssignedRequired.isChecked()
            fields['propertyUnitVisible'] = self.chkPropertyUnitVisible.isChecked()
            fields['propertyNormVisible'] = self.chkPropertyNormVisible.isChecked()
            fields['propertyEvaluationVisible'] = self.chkPropertyEvaluationVisible.isChecked()
            fields['propertyCommentVisible'] = self.chkPropertyCommentVisible.isChecked()
        record = self._table.newRecord(fields.keys())
        for key, value in fields.items():
            record.setValue(key, toVariant(value))
        for actionTypeId in self._actionTypeIdList:
            record.setValue('id', QVariant(actionTypeId))
            QtGui.qApp.db.updateRecord(self._table, record)
        return True


    def confirm(self):
        return QtGui.QMessageBox().question(self,
                                            u'Внимание!',
                                            u'Вы уверены что хотите сохранить изменения?',
                                            QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                                            QtGui.QMessageBox.Cancel) == QtGui.QMessageBox.Ok


    @pyqtSignature('bool')
    def on_chkAddVisitGroup_toggled(self, value):
        self.cmbAddVisitScene.setEnabled(value and self.chkAddVisit.isChecked())
        self.lblAddVisitType.setEnabled(value and self.chkAddVisit.isChecked())
        self.cmbAddVisitType.setEnabled(value and self.chkAddVisit.isChecked())
