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
from PyQt4.QtCore import Qt, pyqtSignature, QDate, QDateTime, QTime, SIGNAL

from Events.Utils  import getAvailableCharacterIdByMKB, specifyDiagnosis, getChiefId
from library.Utils import forceBool, forceInt, forceRef, forceString

from Ui_HospitalizationTransferDialog import Ui_HospitalizationTransferDialog
from HospitalBedComboBox import CHospitalBedModel

class CHospitalizationTransferDialog(QtGui.QDialog, Ui_HospitalizationTransferDialog):
    def __init__(self, parent, purposeId):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbDiseaseCharacter.setTable('rbDiseaseCharacter', order='code')
        self.eventPurposeId = purposeId
        self.cmbMKBResult.setTable('rbDiagnosticResult', True, 'eventPurpose_id=\'%d\'' % self.eventPurposeId)
        self.cmbMesSpecification.setTable('rbMesSpecification')
        self.cmbResultEvent.setTable('rbResult', True, 'eventPurpose_id=\'%d\'' % self.eventPurposeId)
        self.edtTime.setTime(QTime.currentTime())
        self.actionByNextEventCreation = False
        self.modifiableDiagnosisesMap = {}
        self.eventSetDateTime = QDateTime()
        self.eventDate = QDateTime()
        self.date = QDateTime()
        self.clientId = None
        self.execPersonId = None
        self.orgStructureId = None
        self.clientSex = 0
        self.clientAge = 0
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setVisible(False)
        self.diagnosisVisible = False
        self.minDate = None
        self.edtDiagnosis.edited = False
        self.edtDiagnosisEnd.edited = False
        self.edtDiagnosis.connect(self.edtDiagnosis._lineEdit, SIGNAL('editingFinished()'), self.on_edtDiagnosis_editingFinished)
        self.edtDiagnosisEnd.connect(self.edtDiagnosisEnd._lineEdit, SIGNAL('editingFinished()'), self.on_edtDiagnosisEnd_editingFinished)
        self.setHospitalBedVisible(False)
        # self.cmbOrgStructure.connect(self.cmbOrgStructure, SIGNAL('currentIndexChanged()'), self.on_cmbOrgStructureChanged)
        self.cmbOrgStructure.currentIndexChanged.connect(self.on_cmbOrgStructure_currentIndexChanged)

    def on_cmbOrgStructureChanged(self):
        if self.cmbOrgStructure.value() != '' and self.cmbOrgStructure.value() != None:
            self.cmbHospitalBed.filter['orgStructureId'] = self.cmbOrgStructure.value()
            self.cmbHospitalBed._model = CHospitalBedModel(self.cmbHospitalBed, self.cmbHospitalBed.filter)
            self.cmbHospitalBed.setModel(self.cmbHospitalBed._model)
            if not self.cmbHospitalBed._popup:
                self.cmbHospitalBed.showPopup()
            self.cmbHospitalBed._popup.tableModel = self.cmbHospitalBed._model
            self.cmbHospitalBed._popup.tblHospitalBedFind.setModel(self.cmbHospitalBed._popup.tableModel)
            self.cmbHospitalBed._popup.tblHospitalBedFind.expandAll()
            self.cmbHospitalBed._popup.close()
            self.setHospitalBedVisible(True)
            chief_id = getChiefId(self.cmbOrgStructure.value())
            if chief_id:
                self.setExecPerson(chief_id)
        else:
            self.setHospitalBedVisible(False)


    def dialogResultEnabled(self):
        visible = True
        visible = visible and forceBool(self.edtDate.date())
        visible = visible and forceBool(self.cmbOrgStructure.value())
        visible = visible and forceBool(self.cmbPerson.value())
        #if self.diagnosisVisible:
            #visible = visible and forceBool(self.edtDiagnosis.text())
        if self.actionByNextEventCreation:
            #visible = visible and forceBool(self.edtDiagnosisEnd.text())
            #visible = visible and forceBool(self.cmbDiseaseCharacter.value())
            visible = visible and forceBool(self.cmbMKBResult.value())
            visible = visible and forceBool(self.cmbMes.value())
            visible = visible and forceBool(self.cmbMesSpecification.value())
            visible = visible and forceBool(self.cmbResultEvent.value())
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setVisible(visible)

    
    def setHospitalBedVisible(self, isVisible):
        self.lblHospitalBed.setVisible(isVisible)
        self.cmbHospitalBed.setVisible(isVisible)
        

    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(self.orgStructureId, True)
        self.cmbExecPerson.setOrgStructureId(orgStructureId, True)
        self.dialogResultEnabled()
        self.on_cmbOrgStructureChanged()


    @pyqtSignature('int')
    def on_cmbPerson_currentIndexChanged(self, index):
        self.dialogResultEnabled()


    @pyqtSignature('int')
    def on_cmbExecPerson_currentIndexChanged(self, index):
        self.dialogResultEnabled()


    @pyqtSignature('int')
    def on_cmbDiseaseCharacter_currentIndexChanged(self, index):
        self.dialogResultEnabled()


    @pyqtSignature('int')
    def on_cmbMKBResult_currentIndexChanged(self, index):
        self.dialogResultEnabled()


    def getDiagFilter(self):
        personId = forceRef(self.cmbPerson.value())
        result = ''
        if personId:
            db = QtGui.qApp.db
            tablePerson = db.table('Person')
            tableRBSpeciality = db.table('rbSpeciality')
            record = db.getRecordEx(tablePerson.innerJoin(tableRBSpeciality,
                                    tableRBSpeciality['id'].eq(tablePerson['speciality_id'])),
                                    [tableRBSpeciality['mkbFilter']],
                                    [tablePerson['deleted'].eq(0), tablePerson['id'].eq(personId)]
                                    )
            result = forceString(record.value('mkbFilter')) if record else u''
        return result


    def setEditorDataTI(self):
        db = QtGui.qApp.db
        MKB  = unicode(self.edtDiagnosisEnd.text())
        codeIdList = getAvailableCharacterIdByMKB(MKB)
        table = db.table('rbDiseaseCharacter')
        self.cmbDiseaseCharacter.setTable(table.name(), not bool(codeIdList), filter=table['id'].inlist(codeIdList))


    def dateDiagnosis(self, eventSetDateTime, eventDate):
        self.eventSetDateTime = eventSetDateTime
        self.eventDate = eventDate
        self.date = min(d for d in (self.eventSetDateTime.date(), self.eventDate, QDate.currentDate()) if d)


    def getClientInfoForDiagnosis(self, clientId):
        self.clientId = clientId
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        cols = [tableClient['sex']]
        cols.append('age(Client.birthDate, %s) AS ageClient'%(db.formatDate(self.eventSetDateTime)))
        record = db.getRecordEx(tableClient,
                                cols,
                                [tableClient['deleted'].eq(0), tableClient['id'].eq(clientId)])
        self.clientSex = forceRef(record.value('sex')) if record else None
        self.clientAge = forceInt(record.value('ageClient')) if record else 0


    def specifyDiagnosis(self, MKB):
        diagFilter = self.getDiagFilter()
        acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, modifiableDiagnosisId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = specifyDiagnosis(self, MKB, diagFilter, self.clientId, self.clientSex, self.clientAge, self.date)
        self.modifiableDiagnosisesMap[specifiedMKB] = modifiableDiagnosisId
        return acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB


    def updateCharacterByMKB(self, MKB, specifiedCharacterId):
        characterIdList = getAvailableCharacterIdByMKB(MKB)
        if specifiedCharacterId in characterIdList:
            characterId = specifiedCharacterId
        else:
            characterId = forceRef(self.cmbDiseaseCharacter.value())
            if (characterId in characterIdList) or (characterId is None and not characterIdList):
                return
            if characterIdList:
                characterId = characterIdList[0]
            else:
                characterId = None
        self.cmbDiseaseCharacter.setValue(characterId)


    @pyqtSignature('int')
    def on_cmbMes_currentIndexChanged(self, index):
        self.dialogResultEnabled()


    @pyqtSignature('int')
    def on_cmbMesSpecification_currentIndexChanged(self, index):
        self.dialogResultEnabled()


    @pyqtSignature('int')
    def on_cmbResultEvent_currentIndexChanged(self, index):
        self.dialogResultEnabled()


    def on_edtDiagnosis_editingFinished(self):
        if self.edtDiagnosis.edited == True:
            newMKB = unicode(self.edtDiagnosis.text())
            if newMKB:
                acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = self.specifyDiagnosis(newMKB)
                self.setEditorDataTI()
                self.updateCharacterByMKB(specifiedMKB, specifiedCharacterId)
                if acceptable:
                    self.edtDiagnosis.setText(specifiedMKB)
            self.edtDiagnosis.edited = False


    @pyqtSignature('QString')
    def on_edtDiagnosis_textEdited(self, text):
        self.edtDiagnosis.edited = True
        self.cmbMes.setMKBEx(forceString(text))
        self.dialogResultEnabled()


    def on_edtDiagnosisEnd_editingFinished(self):
        if self.edtDiagnosisEnd.edited == True:
            newMKB = unicode(self.edtDiagnosisEnd.text())
            if newMKB:
                acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = self.specifyDiagnosis(newMKB)
                self.setEditorDataTI()
                self.updateCharacterByMKB(specifiedMKB, specifiedCharacterId)
                if acceptable:
                    self.edtDiagnosisEnd.setText(specifiedMKB)
            self.edtDiagnosisEnd.edited = False


    @pyqtSignature('QString')
    def on_edtDiagnosisEnd_textEdited(self, text):
        self.edtDiagnosisEnd.edited = True
        self.cmbMes.setMKB(forceString(text))
        self.dialogResultEnabled()


    def setActionDate(self, date):
        self.edtDate.setDate(date)


    def getActionDate(self):
        return self.edtDate.date()


    def setActionTime(self, time):
        self.edtTime.setTime(time)


    def getActionTime(self):
        return self.edtTime.time()


    def getPersonId(self):
        return self.cmbPerson.value()


    def setPersonId(self, personId):
        self.cmbPerson.setValue(personId)


    def execPerson(self):
        return self.cmbExecPerson.value()


    def setExecPerson(self, execPersonId):
        self.cmbExecPerson.setValue(execPersonId)


    def setOrgStructureId(self, orgStructureId, execPersonId, propertyOrgStructure = False):
        self.orgStructureId = orgStructureId
        self.execPersonId = execPersonId
        self.cmbOrgStructure.setValue(self.orgStructureId)


    def setMinimumDate(self, minimumDateTime):
        self.minDate = minimumDateTime
        dateTime = QDateTime(self.edtDate.date(), self.edtTime.time())
        if dateTime < minimumDateTime:
            self.edtDate.setDate(minimumDateTime.date())
            self.edtTime.setTime(minimumDateTime.time())


    def done(self, result):
        if result > 0 and self.minDate:
            dateTime = QDateTime(self.edtDate.date(), self.edtTime.time())
            if dateTime > QDateTime.currentDateTime():
                res = QtGui.QMessageBox.warning( self,
                                         u'Внимание!',
                                         u'Вы указали будущее время для данного Действия!',
                                         QtGui.QMessageBox.Ok|QtGui.QMessageBox.Ignore,
                                         QtGui.QMessageBox.Ok)
                if res == QtGui.QMessageBox.Ok:
                    self.edtDate.setFocus(Qt.ShortcutFocusReason)
                    return
            if dateTime < self.minDate:
                QtGui.QMessageBox.warning( self,
                                         u'Внимание!',
                                         u'Невозможно завершить движение раньше его начала!',
                                         QtGui.QMessageBox.Ok,
                                         QtGui.QMessageBox.Ok)
                self.edtDate.setFocus(Qt.ShortcutFocusReason)
                return
        QtGui.QDialog.done(self, result)

    def getOrgStructureId(self):
        return self.cmbOrgStructure.value()
    
    
    def getHospitalBedId(self):
        return self.cmbHospitalBed.value()


    def setHospitalBedId(self, value):
        self.cmbHospitalBed.setValue(value)


    def setDiagnosis(self, value):
        self.edtDiagnosis.setText(value)
        self.edtDiagnosis.setEnabled(forceBool(not value))


    def getDiagnosis(self):
        return self.edtDiagnosis.text()


    def setDiagnosisEnd(self, value):
        self.edtDiagnosisEnd.setText(value)
        self.edtDiagnosisEnd.setEnabled(forceBool(not value))


    def getDiagnosisEnd(self):
        return self.edtDiagnosisEnd.text()


    def setDiseaseCharacter(self, value):
        self.cmbDiseaseCharacter.setValue(value)


    def getDiseaseCharacter(self):
        return self.cmbDiseaseCharacter.value()


    def setMKBResult(self, value):
        self.cmbMKBResult.setValue(value)


    def getMKBResult(self):
        return self.cmbMKBResult.value()


    def setMes(self, value):
        self.cmbMes.setValue(value)


    def getMes(self):
        return self.cmbMes.value()


    def setMesSpecification(self, value):
        self.cmbMesSpecification.setValue(value)


    def getMesSpecification(self):
        return self.cmbMesSpecification.value()


    def setResultEvent(self, value):
        self.cmbResultEvent.setValue(value)


    def getResultEvent(self):
        return self.cmbResultEvent.value()


    def getDropFeed(self):
        return self.chkDropFeed.isChecked()

    def getDropPatron(self):
        return self.chkDropPatron.isChecked()


    def setDiagnosisVisible(self, visibleMKB, enableMKB, canEdit):
        self.diagnosisVisible = visibleMKB
        self._diagnosisVisible = visibleMKB
        self.lblDiagnosis.setVisible(visibleMKB)
        self.edtDiagnosis.setVisible(visibleMKB)
        self.edtDiagnosis.setEnabled(canEdit and enableMKB)


    def setFromEventVisible(self, value):
        self.actionByNextEventCreation = value
        self._diagnosisEndVisible = value
        self.lblDiagnosisEnd.setVisible(value)
        self.edtDiagnosisEnd.setVisible(value)

        self._diseaseCharacter = value
        self.lblDiseaseCharacter.setVisible(value)
        self.cmbDiseaseCharacter.setVisible(value)

        self._MKBResult = value
        self.lblMKBResult.setVisible(value)
        self.cmbMKBResult.setVisible(value)

        self._Mes = value
        self.lblMes.setVisible(value)
        self.cmbMes.setVisible(value)

        self._MesSpecification = value
        self.lblMesSpecification.setVisible(value)
        self.cmbMesSpecification.setVisible(value)

        self._ResultEvent = value
        self.lblResultEvent.setVisible(value)
        self.cmbResultEvent.setVisible(value)


