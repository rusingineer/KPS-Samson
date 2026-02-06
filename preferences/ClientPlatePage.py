# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Страница настройки - шильдик пациента
##
#############################################################################

from PyQt4              import QtGui
from PyQt4.QtCore       import pyqtSignature
from library.Utils      import forceInt, forceRef, forceBool, toVariant
from Users.Rights       import urAdmin, urAccessSetupDefault
from Ui_ClientPlatePage import Ui_clientPlatePage


class CClientPlatePage(Ui_clientPlatePage, QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.cmbTFAccountingSystemId.setTable('rbAccountingSystem', True)
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            self.lblTFAccountingSystemId.setVisible(False)
            self.cmbTFAccountingSystemId.setVisible(False)
            self.chkTFOMS.setVisible(False)
        if not QtGui.qApp.userHasAnyRight([urAdmin, urAccessSetupDefault]):
            self.cmbTFAccountingSystemId.setEnabled(False)


    def setProps(self, props):
        self.chkFIO.setChecked(forceBool(props.get('showingFIO', True)))
        self.chkConsents.setChecked(forceBool(props.get('showingConsents', True)))
        self.chkIdentification.setChecked(forceBool(props.get('showingIdentification', True)))
        self.chkQuoting.setChecked(forceBool(props.get('showingQuoting', True)))
        self.chkSocStatuses.setChecked(forceBool(props.get('showingSocStatuses', True)))
        self.chkDocument.setChecked(forceBool(props.get('showingDocument', True)))
        self.chkCompulsoryPolicy.setChecked(forceBool(props.get('showingCompulsoryPolicy', True)))
        self.chkHospitalBed.setChecked(forceBool(props.get('showingHospitalBed', True)))
        self.chkVoluntaryPolicy.setChecked(forceBool(props.get('showingVoluntaryPolicy', True)))
        self.chkRegAddress.setChecked(forceBool(props.get('showingRegAddress', True)))
        self.chkLocAddress.setChecked(forceBool(props.get('showingLocAddress', True)))
        self.chkWork.setChecked(forceBool(props.get('showingWork', True)))
        self.chkPhones.setChecked(forceBool(props.get('showingPhones', True)))
        self.chkNotes.setChecked(forceBool(props.get('showingNotes', True)))
        self.chkAllergy.setChecked(forceBool(props.get('showingAllergy', True)))
        self.chkBirthPlace.setChecked(forceBool(props.get('showingBirthPlace', True)))
        self.chkTFOMS.setChecked(forceBool(props.get('showingTFOMS', False)))
        self.chkObservationGroup.setChecked(forceBool(props.get('showingObservationGroup', False)))
        self.chkAttaches.setChecked(forceBool(props.get('showingAttaches', True)))
        self.cmbClientContingent.setCurrentIndex(forceInt(props.get('showingClientContingent', 1)))
        self.cmbShowingInInfoBlockSocStatus.setCurrentIndex(forceInt(props.get('showingInInfoBlockSocStatus', 0)))
        self.cmbTFAccountingSystemId.setValue(forceRef(props.get('TFAccountingSystemId', None)))
        self.chkRelations.setChecked(forceBool(props.get('showingClientRelations', False)))
        self.chkNewLine.setChecked(forceBool(props.get('showingBlockFromNewLine', True)))
        self.cmbEpidCase.setCurrentIndex(forceInt(props.get('showingEpidCase', 2)))
        self.chkDispanserySpecialities.setChecked(forceBool(props.get('showingDispanserySpecialities', True)))
        self.chkResearch.setChecked(forceBool(props.get('showingResearch', True)))
        self.chkIntoleranceMedicament.setChecked(forceBool(props.get('showingIntoleranceMedicament', True)))
        self.chkObservationStatus.setChecked(forceBool(props.get('showingObservationStatus', True)))
        self.chkProf.setChecked(forceBool(props.get('showingProf', True)))


    def getProps(self, props):
        props['showingFIO'] = toVariant(self.chkFIO.isChecked())
        props['showingConsents'] = toVariant(self.chkConsents.isChecked())
        props['showingIdentification'] = toVariant(self.chkIdentification.isChecked())
        props['showingQuoting'] = toVariant(self.chkQuoting.isChecked())
        props['showingSocStatuses'] = toVariant(self.chkSocStatuses.isChecked())
        props['showingDocument'] = toVariant(self.chkDocument.isChecked())
        props['showingCompulsoryPolicy'] = toVariant(self.chkCompulsoryPolicy.isChecked())
        props['showingHospitalBed'] = toVariant(self.chkHospitalBed.isChecked())
        props['showingVoluntaryPolicy'] = toVariant(self.chkVoluntaryPolicy.isChecked())
        props['showingRegAddress'] = toVariant(self.chkRegAddress.isChecked())
        props['showingLocAddress'] = toVariant(self.chkLocAddress.isChecked())
        props['showingWork'] = toVariant(self.chkWork.isChecked())
        props['showingPhones'] = toVariant(self.chkPhones.isChecked())
        props['showingNotes'] = toVariant(self.chkNotes.isChecked())
        props['showingAllergy'] = toVariant(self.chkAllergy.isChecked())
        props['showingBirthPlace'] = toVariant(self.chkBirthPlace.isChecked())
        props['showingObservationGroup'] = toVariant(self.chkObservationGroup.isChecked())
        props['showingTFOMS'] = toVariant(self.chkTFOMS.isChecked() and bool(self.cmbTFAccountingSystemId.value()))
        props['showingClientContingent'] = toVariant(self.cmbClientContingent.currentIndex())
        props['showingAttaches'] = toVariant(self.chkAttaches.isChecked())
        props['showingInInfoBlockSocStatus'] = toVariant(self.cmbShowingInInfoBlockSocStatus.currentIndex())
        props['TFAccountingSystemId'] = toVariant(self.cmbTFAccountingSystemId.value())
        props['showingClientRelations'] = toVariant(self.chkRelations.isChecked())
        props['showingBlockFromNewLine'] = toVariant(self.chkNewLine.isChecked())
        props['showingEpidCase'] = toVariant(self.cmbEpidCase.currentIndex())
        props['showingNotes'] = toVariant(self.chkNotes.isChecked())
        props['showingDispanserySpecialities'] = toVariant(self.chkDispanserySpecialities.isChecked())
        props['showingResearch'] = toVariant(self.chkResearch.isChecked())
        props['showingIntoleranceMedicament'] = toVariant(self.chkIntoleranceMedicament.isChecked())
        props['showingObservationStatus'] = toVariant(self.chkObservationStatus.isChecked())
        props['showingProf'] = toVariant(self.chkProf.isChecked())


    @pyqtSignature('int')
    def on_cmbTFAccountingSystemId_currentIndexChanged(self, index):
        self.chkTFOMS.setEnabled(index > 0)
