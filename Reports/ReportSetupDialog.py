# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QDate, QDateTime, QTime

from Events.Utils import getWorkEventTypeFilter
from Orgs.Orgs import selectOrganisation
from library.Utils import forceString
from Events.Utils  import getWorkEventTypeFilter
from Events.EventTypeListEditorDialog import CEventTypeListEditorDialog
from Reports.SelectPersonListDialog   import CPersonListDialog
from Reports.MesDispansListDialog     import getMesDispansList, getMesDispansNameList

import OKVEDList

from Ui_ReportSetup import Ui_ReportSetupDialog
from library.Utils import forceString


class CReportSetupDialog(QtGui.QDialog, Ui_ReportSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.patientRequired = False
        self.datePeriodVisible = True
        self.timePeriodVisible = False
        self.setupUi(self)
        self.cmbSpeciality.setTable('rbSpeciality')
        self.cmbEventType.setTable('EventType', True)
        self.cmbStage.setTable('rbDiseaseStage', True)
        self.cmbFinance.setTable('rbFinance', True)
        self.cmbSocStatusType.setTable('rbSocStatusType', True)
        self.cmbEquipment.setTable('rbEquipment', True)
        self.cmbMedicalAidProfile.setTable('rbMedicalAidProfile', True)
        self.cmbMedicalAidType.setTable('rbMedicalAidType', True)
        self.cmbEquipment.setTable('rbEquipment', False)
        self.cmbSpeciality.setValue(0)
        self.setStageVisible(False)
        self.setDiagnosisType(False)
        self.setPayPeriodVisible(False)
        self.setWorkTypeVisible(False)
        self.edtBegPayDate.setDate(QDate())
        self.edtEndPayDate.setDate(QDate())
        self.setOwnershipVisible(False)
        self.setCurrentWorkOrganisationVisible(False)
        self.setWorkOrganisationVisible(False)
        self.setSexVisible(False)
        self.setAgeVisible(False)
        self.setActionTypeVisible(False)
        self.cmbActionType.setAllSelectable(True)
        self.setMKBFilterVisible(False)
        self.setInsurerVisible(False)
        self.setOrgStructureVisible(False)
        self.setSpecialityVisible(False)
        self.setPersonVisible(False)
        self.setPersonListVisible(False)
        self.setSetPersonVisible(False)
        self.setMedicalAidProfileVisible(False)
        self.setMedicalAidTypeVisible(False)
        self.setFinanceVisible(False)
        self.setSocStatusTypeVisible(False)
        self.setEventTypeVisible(True)
        self.setEventTypeListVisible(False)
        self.setOnlyPermanentAttachVisible(True)
        self.setEventStatusVisible(False)
        self.setDetailActionVisible(False)
        self.setNoteUETVisible(False)
        self.setEquipmentVisible(False)
        self.setActionStatusVisible(False)
        self.setTimePeriodVisible(False)
        self.setClientIdVisible(False)
        self.setMonthVisible(False)
        self.eventTypeList = []
        self.setDetailAssistantVisible(False)
        self.setChkOrderAddressVisible(False)
        self.setMesDispansListVisible(False)
        self.setGroupOrganisation(False)
        self.personIdList = []
        self.mesDispansIdList = []


    def setChkOrderAddressVisible(self, value):
        self.isOrderAddress = value
        self.chkOrderAddress.setVisible(value)


    def setDetailAssistantVisible(self, value):
        self.detailAssistantVisible = value
        self.chkDetailAssistant.setVisible(value)


    def setMonthVisible(self, value):
        self.monthVisible = value
        self.edtMonth.setVisible(value)
        self.lblMonth.setVisible(value)

    def setDatePeriodVisible(self, value):
        self.datePeriodVisible = value
        self.lblBegDate.setVisible(value)
        self.edtBegDate.setVisible(value)
        self.lblEndDate.setVisible(value)
        self.edtEndDate.setVisible(value)
        self.wgtDatePeriodSpacer.setVisible(value)

    def setTimePeriodVisible(self, value):
        self.timePeriodVisible = value
        self.edtBegTime.setVisible(value)
        self.edtEndTime.setVisible(value)

    def setClientIdVisible(self, value=True):
        self.lblClientId.setVisible(value)
        self.edtClientId.setVisible(value)
        self.clientIdVisible = value

    def setEquipmentVisible(self, value):
        self.equipmentVisible = value
        self.lblEquipment.setVisible(value)
        self.cmbEquipment.setVisible(value)


    def setNoteUETVisible(self, value=False):
        self.noteUETVisible = value
        self.cmbNoteUET.setVisible(value)
        self.lblNoteUET.setVisible(value)

    
    def setActionStatusVisible(self, value = True):
        self.ActionStatusVisible = value
        self.cmbActionStatus.setVisible(value)
        self.lblActionStatus.setVisible(value)


    def setDetailActionVisible(self, value=True):
        self.detailActionVisible = value
        self.cmbDetailAction.setVisible(value)
        self.lblDetailAction.setVisible(value)


    def setEventTypeVisible(self, value=True):
        self.eventTypeVisible = value
        self.cmbEventType.setVisible(value)
        self.lblEventType.setVisible(value)


    def setEventTypeListVisible(self, value=True):
        self.eventTypeListVisible = value
        self.btnEventTypeList.setVisible(value)
        self.lblEventTypeList.setVisible(value)


    def setMesDispansListVisible(self, value):
        self.mesDispansListVisible = value
        self.btnMesDispansList.setVisible(value)
        self.lblMesDispansList.setVisible(value)


    def setGroupOrganisation(self, value):
        self.chkGroupOrganisation.setVisible(value)


    def setEventStatusVisible(self, value = True):
        self.eventStatusVisible = value
        self.cmbEventStatus.setVisible(value)
        self.lblEventStatus.setVisible(value)


    def setOnlyPermanentAttachVisible(self, value):
        self.onlyPermanentAttachVisible = value
        self.chkOnlyPermanentAttach.setVisible(value)


    def setFinanceVisible(self, value):
        self.financeVisible = value
        self.lblFinance.setVisible(value)
        self.cmbFinance.setVisible(value)


    def setSocStatusTypeVisible(self, value):
        self.socStatusTypeVisible = value
        self.lblSocStatusType.setVisible(value)
        self.cmbSocStatusType.setVisible(value)


    def setPersonVisible(self, value):
        self.personVisible = value
        self.lblPerson.setVisible(value)
        self.cmbPerson.setVisible(value)
        self.chkDetailPerson.setVisible(value)


    def setPersonListVisible(self, value):
        self.personListVisible = value
        self.lblPersonList.setVisible(value)
        self.btnPersonList.setVisible(value)

    def setSetPersonVisible(self, value):
        self.isSetPersonVisible = value
        self.lblSetPerson.setVisible(value)
        self.cmbSetPerson.setVisible(value)


    def setMedicalAidProfileVisible(self, value):
        self.MedicalAidProfileVisible = value
        self.lblMedicalAidProfile.setVisible(value)
        self.cmbMedicalAidProfile.setVisible(value)
        
    def setMedicalAidTypeVisible(self, value):
        self.MedicalAidTypeVisible = value
        self.lblMedicalAidType.setVisible(value)
        self.cmbMedicalAidType.setVisible(value)


    def setSpecialityVisible(self, value):
        self.specialityVisible = value
        self.lblSpeciality.setVisible(value)
        self.cmbSpeciality.setVisible(value)


    def setOrgStructureVisible(self, value):
        self.orgStructureVisible = value
        self.lblOrgStructure.setVisible(value)
        self.cmbOrgStructure.setVisible(value)


    def setInsurerVisible(self, value):
        self.insurerVisible = value
        self.lblInsurer.setVisible(value)
        self.cmbInsurer.setVisible(value)


    def setStageVisible(self, value):
        self.stageVisible = value
        self.lblStage.setVisible(value)
        self.cmbStage.setVisible(value)


    def setPayPeriodVisible(self, value):
        self.payPeriodVisible = value
        for w in (self.lblBegPayDate, self.edtBegPayDate,
                  self.lblEndPayDate, self.edtEndPayDate,
                  self.chkOnlyPayedEvents
                 ):
            w.setVisible(value)


    def setWorkTypeVisible(self, value):
        if value and not self.cmbWorkType.count():
            for row in OKVEDList.rows:
                self.cmbWorkType.addItem(row[0])
        self.workTypeVisible = value
        self.lblWorkType.setVisible(value)
        self.cmbWorkType.setVisible(value)


    def setOwnershipVisible(self, value):
        self.ownershipVisible = value
        self.lblOwnership.setVisible(value)
        self.cmbOwnership.setVisible(value)


    def setCurrentWorkOrganisationVisible(self, value):
        self.currentWorkOrganisationVisible = value
        self.chkCurrentWorkOrganisation.setVisible(value)


    def setWorkOrganisationVisible(self, value):
        self.workOrganisationVisible = value
        self.lblWorkOrganisation.setVisible(value)
        self.cmbWorkOrganisation.setVisible(value)
        self.btnSelectWorkOrganisation.setVisible(value)


    def setSexVisible(self, value):
        self.lblSex.setVisible(value)
        self.cmbSex.setVisible(value)


    def setDiagnosisType(self, value):
        self.chkDiagnosisType.setVisible(value)


    def setAgeVisible(self, value):
        self.ageVisible = value
        self.lblAge.setVisible(value)
        self.edtAgeFrom.setVisible(value)
        self.lblAgeTo.setVisible(value)
        self.edtAgeTo.setVisible(value)
        self.lblAgeYears.setVisible(value)


    def setActionTypeVisible(self, value):
        self.actionTypeVisible = value
        for w in (self.lblActionTypeClass, self.cmbActionTypeClass,
                  self.lblActionType,      self.cmbActionType,
                  self.chkActionClass):
            w.setVisible(value)
        if value:
            self.on_cmbActionTypeClass_currentIndexChanged(self.cmbActionTypeClass.currentIndex())


    def setMKBFilterVisible(self, value):
        self.MKBFilterVisible = value
        for w in (self.lblMKBFilter, self.cmbMKBFilter,
                  self.edtMKBFrom,   self.edtMKBTo):
            w.setVisible(value)
        if value:
            self.on_cmbActionTypeClass_currentIndexChanged(self.cmbActionTypeClass.currentIndex())


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        if self.datePeriodVisible:
            self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
            self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        if self.timePeriodVisible:
            self.edtBegTime.setTime(params.get('endTime', QTime.currentTime()))
            self.edtEndTime.setTime(params.get('endTime', QTime.currentTime()))
        if self.eventTypeVisible:
            self.cmbEventType.setValue(params.get('eventTypeId', None))
        if self.detailActionVisible:
            self.cmbDetailAction.setCurrentIndex(params.get('isProfile', 0))
        if self.stageVisible:
            self.cmbStage.setValue(params.get('stageId', None))
        if self.onlyPermanentAttachVisible:
            self.chkOnlyPermanentAttach.setChecked(params.get('onlyPermanentAttach', False))
        self.chkDiagnosisType.setChecked(params.get('diagnosisType', False))
        self.chkOnlyPayedEvents.setChecked(params.get('onlyPayedEvents', False))
        self.edtBegPayDate.setDate(params.get('begPayDate', QDate.currentDate()))
        self.edtEndPayDate.setDate(params.get('endPayDate', QDate.currentDate()))
        self.cmbWorkType.setCurrentIndex(params.get('workType', 0))
        if self.ownershipVisible:
            self.cmbOwnership.setCurrentIndex(params.get('ownership', 0))
        if self.currentWorkOrganisationVisible:
            self.chkCurrentWorkOrganisation.setChecked(params.get('currentWorkOrganisation', False))
        self.cmbWorkOrganisation.setValue(params.get('workOrgId', None))
        self.cmbSex.setCurrentIndex(params.get('sex', 0))
        if self.ageVisible:
            self.edtAgeFrom.setValue(params.get('ageFrom', 0))
            self.edtAgeTo.setValue(params.get('ageTo', 150))
        if self.actionTypeVisible:
            self.chkActionClass.setChecked(params.get('chkActionTypeClass', False))
            if not self.chkActionClass.isChecked():
                classCode = params.get('actionTypeClass', 0)
                self.cmbActionTypeClass.setCurrentIndex(classCode)
                self.cmbActionType.setClassesPopup([classCode])
                self.cmbActionType.setClass(classCode)
                self.cmbActionType.setValue(params.get('actionTypeId', None))
        if self.MKBFilterVisible:
            MKBFilter = params.get('MKBFilter', 0)
            self.cmbMKBFilter.setCurrentIndex(MKBFilter if MKBFilter else 0)
            self.edtMKBFrom.setText(params.get('MKBFrom', 'A00'))
            self.edtMKBTo.setText(params.get('MKBTo',   'Z99.9'))
        if self.insurerVisible:
            self.cmbInsurer.setValue(params.get('insurerId', None))
        if self.orgStructureVisible:
            self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        if self.specialityVisible:
            self.cmbSpeciality.setValue(params.get('specialityId', None))
        if self.personVisible:
            self.chkDetailPerson.setChecked(params.get('detailPerson', False))
            self.cmbPerson.setValue(params.get('personId', None))
        if self.personListVisible:
            self.personIdList = params.get('personIdList', [])
            if self.personIdList:
                db = QtGui.qApp.db
                table = db.table('vrbPersonWithSpecialityAndOrgStr')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.personIdList)])
                self.lblPersonList.setText(u'; '.join(forceString(record.value('name')) for record in records if forceString(record.value('name'))))
            else:
                self.lblPersonList.setText(u'не задано')
        if self.financeVisible:
            self.cmbFinance.setValue(params.get('financeId', None))
        if self.socStatusTypeVisible:
            self.cmbSocStatusType.setValue(params.get('socStatusTypeId', None))
        if self.eventStatusVisible:
            self.cmbEventStatus.setCurrentIndex(params.get('eventStatus', 0))
        if self.noteUETVisible:
            self.cmbNoteUET.setCurrentIndex(params.get('noteUET', 0))
        if self.equipmentVisible:
            self.cmbEquipment.setValue(params.get('equipmentId', None))
        if self.MedicalAidProfileVisible:
            self.cmbMedicalAidProfile.setValue(params.get('', None))
        if self.MedicalAidTypeVisible:
            self.cmbMedicalAidType.setValue(params.get('rbMedicalAidTypeId', None))
        actstatus = params.get('ActionStatus', None)
        if actstatus is None:
            self.cmbActionStatus.setCurrentIndex(0)
        else:
            self.cmbActionStatus.setCurrentIndex(params['ActionStatus'] + 1)
        if self.clientIdVisible:
            self.edtClientId.setText(params.get('clientId', ''))
        if self.monthVisible:
            self.edtMonth.setDate(params.get('month', QDate.currentDate()))
        if self.detailAssistantVisible:
            self.chkDetailAssistant.setChecked(params.get('detailAssistant', False))
        if self.isOrderAddress:
            self.chkOrderAddress.setChecked(params.get('isOrderAddress', False))
        self.chkGroupOrganisation.setChecked(params.get('groupOrganisation', False))
        if self.eventTypeListVisible:
            self.eventTypeList =  params.get('eventTypeList', [])
            if self.eventTypeList:
                db = QtGui.qApp.db
                tableET = db.table('EventType')
                records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(self.eventTypeList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblEventTypeList.setText(u','.join(name for name in nameList if name))
            else:
                self.lblEventTypeList.setText(u'не задано')
        if self.mesDispansListVisible:
            self.mesDispansIdList = params.get('mesDispansIdList', [])
            nameList = getMesDispansNameList(self.mesDispansIdList)
            if nameList:
                self.lblMesDispansList.setText(u','.join(name for name in nameList if name))
            else:
                self.lblMesDispansList.setText(u'не задано')
        if self.isSetPersonVisible:
            self.cmbSetPerson.setValue(params.get('setPersonId', None))


    def params(self):
        result = {}
        if self.datePeriodVisible:
            result['begDate'] = self.edtBegDate.date()
            result['endDate'] = self.edtEndDate.date()
        if self.timePeriodVisible:
            result['begTime'] = self.edtBegTime.time()
            result['endTime'] = self.edtEndTime.time()
        if self.eventTypeVisible:
            result['eventTypeId'] = self.cmbEventType.value()
        if self.detailActionVisible:
            result['isProfile'] = self.cmbDetailAction.currentIndex()
        if self.stageVisible:
            result['stageId'] = self.cmbStage.value()
        if self.onlyPermanentAttachVisible:
            result['onlyPermanentAttach'] = self.chkOnlyPermanentAttach.isChecked()
        result['onlyPayedEvents'] = self.chkOnlyPayedEvents.isChecked()
        result['diagnosisType'] = self.chkDiagnosisType.isChecked()
        result['begPayDate'] = self.edtBegPayDate.date()
        result['endPayDate'] =self.edtEndPayDate.date()
        result['workType'] =self.cmbWorkType.currentIndex()
        if self.ownershipVisible:
            result['ownership'] = self.cmbOwnership.currentIndex()
        if self.currentWorkOrganisationVisible:
            result['currentWorkOrganisation'] = self.chkCurrentWorkOrganisation.isChecked()
        result['workOrgId'] = self.cmbWorkOrganisation.value()
        result['sex'] = self.cmbSex.currentIndex()
        if self.ageVisible:
            result['ageFrom'] = self.edtAgeFrom.value()
            result['ageTo'] = self.edtAgeTo.value()
        if self.actionTypeVisible:
            chkActionTypeClass = self.chkActionClass.isChecked()
            result['chkActionTypeClass'] = chkActionTypeClass
            if chkActionTypeClass:
                result['actionTypeClass'] = None
                result['actionTypeId'] = None
            else:
                result['actionTypeClass'] = self.cmbActionTypeClass.currentIndex()
                result['actionTypeId'] = self.cmbActionType.value()
        if self.MKBFilterVisible:
            result['MKBFilter'] = self.cmbMKBFilter.currentIndex()
            result['MKBFrom']   = unicode(self.edtMKBFrom.text())
            result['MKBTo']     = unicode(self.edtMKBTo.text())
        if self.personVisible:
            result['detailPerson'] = self.chkDetailPerson.isChecked()
            result['personId'] = self.cmbPerson.value()
        if self.personListVisible:
            result['personIdList'] = self.personIdList
        if self.specialityVisible:
            result['specialityId'] = self.cmbSpeciality.value()
        if self.orgStructureVisible:
            result['orgStructureId'] = self.cmbOrgStructure.value()
        if self.insurerVisible:
            result['insurerId'] = self.cmbInsurer.value()
        if self.financeVisible:
            result['financeId'] = self.cmbFinance.value()
            result['financeCode'] = self.cmbFinance.code()
        if self.socStatusTypeVisible:
            result['socStatusTypeId'] = self.cmbSocStatusType.value()
        if self.eventStatusVisible:
            result['eventStatus'] = self.cmbEventStatus.currentIndex()
        if self.noteUETVisible:
            result['noteUET'] = self.cmbNoteUET.currentIndex()
        if self.equipmentVisible:
            result['equipmentId'] = self.cmbEquipment.value()
        if self.MedicalAidProfileVisible:
            result['rbMedicalAidProfileId'] = self.cmbMedicalAidProfile.value()
        if self.MedicalAidTypeVisible:
            result['rbMedicalAidTypeId'] = self.cmbMedicalAidType.value()
        if self.ActionStatusVisible:
            result['ActionStatus'] = [None, 0, 1, 2, 3, 4, 5, 6][self.cmbActionStatus.currentIndex()]
        if self.clientIdVisible:
            result['clientId'] = unicode(self.edtClientId.text())
        if self.monthVisible:
            result['month'] = self.edtMonth.date()
        if self.eventTypeListVisible:
            result['eventTypeList'] = self.eventTypeList
        if self.mesDispansListVisible:
            result['mesDispansIdList'] = self.mesDispansIdList
        if self.detailAssistantVisible:
            result['detailAssistant'] = self.chkDetailAssistant.isChecked()
        if self.isOrderAddress:
            result['isOrderAddress'] = self.chkOrderAddress.isChecked()
        result['groupOrganisation'] = self.chkGroupOrganisation.isChecked()
        if self.isSetPersonVisible:
            result['setPersonId'] = self.cmbSetPerson.value()
        return result


    @pyqtSignature('')
    def on_btnPersonList_clicked(self):
        self.personIdList = []
        orgStructureId = self.cmbOrgStructure.value()
        self.lblPersonList.setText(u'не задано')
        dialog = CPersonListDialog(self, orgStructureId = orgStructureId if orgStructureId else None)
        if dialog.exec_():
            self.personIdList = dialog.values()
            if self.personIdList:
                db = QtGui.qApp.db
                table = db.table('vrbPersonWithSpecialityAndOrgStr')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.personIdList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblPersonList.setText(u', '.join(name for name in nameList if name))


    @pyqtSignature('')
    def on_btnSelectWorkOrganisation_clicked(self):
        orgId = selectOrganisation(self, self.cmbWorkOrganisation.value(), False)
        self.cmbWorkOrganisation.updateModel()
        if orgId:
            self.cmbWorkOrganisation.setValue(orgId)


    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        specialityId = self.cmbSpeciality.value()
        self.cmbPerson.setSpecialityId(specialityId)


    @pyqtSignature('int')
    def on_cmbActionTypeClass_currentIndexChanged(self, classCode):
        self.cmbActionType.setClassesPopup([classCode])
        self.cmbActionType.setClass(classCode)


    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        self.edtMKBFrom.setEnabled(index == 1)
        self.edtMKBTo.setEnabled(index == 1)


    @pyqtSignature('')
    def on_btnEventTypeList_clicked(self):
        self.eventTypeList = []
        self.lblEventTypeList.setText(u'не задано')
        filter = getWorkEventTypeFilter(isApplyActive=True)
        dialog = CEventTypeListEditorDialog(self, filter)
        if dialog.exec_():
            self.eventTypeList = dialog.values()
            if self.eventTypeList:
                db = QtGui.qApp.db
                tableET = db.table('EventType')
                records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(self.eventTypeList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblEventTypeList.setText(u','.join(name for name in nameList if name))


    @pyqtSignature('')
    def on_btnMesDispansList_clicked(self):
        db = QtGui.qApp.db
        tableMES = db.table('mes.MES')
        tableMESGroup = db.table('mes.mrbMESGroup')
        filter = [tableMESGroup['code'].eq(u'ДиспанС'),
                  db.joinOr([tableMES['endDate'].isNull(), tableMES['endDate'].ge(self.edtBegDate.date())])
                  ]
        self.mesDispansIdList, nameList = getMesDispansList(self, filter)
        if self.mesDispansIdList and nameList:
            self.lblMesDispansList.setText(u','.join(name for name in nameList if name))
        else:
            self.lblMesDispansList.setText(u'не задано')

