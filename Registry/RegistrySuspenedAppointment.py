# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2015-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore       import QDate, pyqtSignature

from library.DialogBase import CDialogBase
from library.Utils      import forceDate, forceRef, toVariant


from Registry.Ui_RegistrySuspenedAppointment import Ui_RegistrySuspenedAppointmentDialog


class CRegistrySuspenedAppointment(CDialogBase, Ui_RegistrySuspenedAppointmentDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.cmbSpeciality.setTable('rbSpeciality')
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        if QtGui.qApp.userSpecialityId:
            self.cmbPerson.setValue(QtGui.qApp.userId)
            self.cmbSpeciality.setValue(QtGui.qApp.userSpecialityId)
        self.edtBegDate.setDate(QDate.currentDate())
        self.edtEndDate.setDate(QDate.currentDate().addDays(30))
        self.clientId = None


    def registrySuspenedAppointment(self):
        if self.clientId:
            begDate, endDate = self.getRegistryDate()
            orgStructureId   = self.getRegistryOrgStructure()
            specialityId     = self.getRegistrySpeciality()
            personId         = self.getRegistryPerson()
            note             = self.getRegistryNote()
            db = QtGui.qApp.db
            table = db.table('SuspendedAppointment')
            tableSchedule_Item = db.table('Schedule_Item')
            queryTable = table.innerJoin(tableSchedule_Item,
                                                     tableSchedule_Item['id'].eq(table['appointment_id']))
            cond = [table['deleted'].eq(0),
                    table['client_id'].eq(self.clientId), ' (date(Schedule_Item.time)>date(NOW()) OR processed = 0) '
                    ]
            if personId:
                cond.append(table['person_id'].eq(personId))
            else:
                if specialityId:
                    cond.append(table['speciality_id'].eq(specialityId))
                if orgStructureId:
                    cond.append(table['orgStructure_id'].eq(orgStructureId))
            if begDate:
                cond.append(table['endDate'].ge(begDate))
            if endDate:
                cond.append(table['begDate'].le(endDate))
            recordSA = db.getRecordEx(queryTable, [table['id']], cond, order='id DESC')
            regisrtySAId = forceRef(recordSA.value('id')) if recordSA else None
            if not regisrtySAId:
                record = table.newRecord()
                record.setValue('client_id', toVariant(self.clientId))
                record.setValue('begDate', toVariant(begDate))
                record.setValue('endDate', toVariant(endDate))
                record.setValue('orgStructure_id', toVariant(orgStructureId))
                record.setValue('speciality_id', toVariant(specialityId))
                record.setValue('person_id', toVariant(personId))
                record.setValue('note', toVariant(note))
                return db.insertRecord(table, record)
            else:
                QtGui.QMessageBox.warning( self,
                                     u'Внимание!',
                                     u'В Журнале отложенной записи запись на этого пациента уже существует, id = %s!'%(regisrtySAId),
                                     QtGui.QMessageBox.Ok,
                                     QtGui.QMessageBox.Ok)


    def getClientId(self):
        return self.clientId


    def getRegistryDate(self):
        return self.edtBegDate.date(), self.edtEndDate.date()


    def getRegistryOrgStructure(self):
        return self.cmbOrgStructure.value()


    def getRegistrySpeciality(self):
        return self.cmbSpeciality.value()


    def getRegistryPerson(self):
        return self.cmbPerson.value()


    def getRegistryNote(self):
        return self.edtNote.toPlainText()


    def setClientId(self, clientId):
        self.clientId = clientId


    def setRegistryDate(self, begDate, endDate):
        self.edtBegDate.setDate(begDate)
        self.edtEndDate.setDate(endDate)


    def setRegistryOrgStructure(self, orgStructureId):
        self.cmbOrgStructure.setValue(orgStructureId)


    def setRegistrySpeciality(self, specialityId):
        self.cmbSpeciality.setValue(specialityId)


    def setRegistryPerson(self, personId):
        self.cmbPerson.setValue(personId)


    def setRegistryNote(self, text):
        self.edtNote.setPlainText(text)


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)


    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        specialityId = self.cmbSpeciality.value()
        self.cmbPerson.setSpecialityId(specialityId)


def setRegistrySuspenedAppointment(content, clientId):
    if clientId:
        orgStructureId = content.getCurrentOrgSrtuctureId() if content else QtGui.qApp.currentOrgStructureId()
        specialityId   = QtGui.qApp.userSpecialityId
        personIdList   = content.getCurrentPersonIdList() if content else []
        personId       = content.getCurrentPersonId() if content else QtGui.qApp.userId
        begDate        = content.getCurrentDate() if content else QDate.currentDate()
        endDate        = begDate.addDays(30)
        if personId or personIdList:
            db = QtGui.qApp.db
            tableSchedule = db.table('Schedule')
            tablePerson   = db.table('Person')
            cols = [tableSchedule['date']]
            cond = [tableSchedule['deleted'].eq(0)]
            if personId:
                cond.append(tableSchedule['person_id'].eq(personId))
            elif personIdList:
                cond.append(tableSchedule['person_id'].inlist(personIdList))
            record = db.getRecordEx(tableSchedule, cols, cond, order='date DESC')
            if record:
                endDate = forceDate(record.value('date'))
            if personId:
                record = db.getRecordEx(tablePerson, [tablePerson['speciality_id'], tablePerson['orgStructure_id']], [tablePerson['id'].eq(personId), tablePerson['deleted'].eq(0)])
                if record:
                    specialityId = forceRef(record.value('speciality_id'))
                    orgStructureId = forceRef(record.value('orgStructure_id'))
            elif content:
                for personIdSP in personIdList:
                    if personIdSP:
                        specialityId = content.getPersonSpecialityId(personIdSP)
                        if specialityId:
                            break
        if begDate > endDate:
            endDate = begDate.addDays(30)
        if orgStructureId or specialityId or personId:
            dialog = CRegistrySuspenedAppointment(content)
            dialog.setClientId(clientId)
            dialog.setRegistryDate(begDate, endDate)
            dialog.setRegistryOrgStructure(orgStructureId)
            dialog.setRegistrySpeciality(specialityId)
            dialog.setRegistryPerson(personId)
            if dialog.exec_():
                if dialog.getClientId():
                    suspenedAppointmentId = dialog.registrySuspenedAppointment()
                    if suspenedAppointmentId:
                        QtGui.QMessageBox.warning( content,
                                             u'Внимание!',
                                             u'Произведена запись в Журнал отложенной записи!',
                                             QtGui.QMessageBox.Ok,
                                             QtGui.QMessageBox.Ok)
        else:
            QtGui.QMessageBox.critical( content,
                                 u'Внимание!',
                                 u'Не указаны подразделение и специальность или врач! Запись в Журнал отложенной записи не возможна!',
                                 QtGui.QMessageBox.Ok,
                                 QtGui.QMessageBox.Ok)

