# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Регистрационная карта пациента
##
#############################################################################

from PyQt4 import QtGui

from library.Utils import forceBool, toVariant, forceInt

from Ui_ClientCardPage import Ui_clientCardPage


class CClientCardPage(Ui_clientCardPage, QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)

    def setProps(self, props):
        self.cmbCheckPolicyAffiliation.setCurrentIndex(forceInt(props.get('checkClientCardPolicyAffiliation', 0)))
        self.chkDeathDate.setChecked(forceBool(props.get('showingClientCardDeathDate', True)))
        self.chkBirthTime.setChecked(forceBool(props.get('showingClientCardBirthTime', True)))
        self.chkSNILS.setChecked(forceBool(props.get('showingClientCardSNILS', True)))
        self.chkCompulsoryPolisName.setChecked(forceBool(props.get('showingClientCardCompulsoryPolisName', True)))
        self.chkCompulsoryPolisNote.setChecked(forceBool(props.get('showingClientCardCompulsoryPolisNote', True)))
        self.chkDocOrigin.setChecked(forceBool(props.get('showingClientCardDocOrigin', True)))
        self.chkVoluntaryPolicy.setChecked(forceBool(props.get('showingClientCardVoluntaryPolicy', True)))
        self.chkVoluntaryPolisName.setChecked(forceBool(props.get('showingClientCardVoluntaryPolicyName', True)))
        self.chkVoluntaryPolisNote.setChecked(forceBool(props.get('showingClientCardVoluntaryPolicyNote', True)))
        self.chkTabAttach.setChecked(forceBool(props.get('showingClientCardTabAttach', True)))
        self.chkTabWork.setChecked(forceBool(props.get('showingClientCardTabWork', True)))
        self.chkTabQuoting.setChecked(forceBool(props.get('showingClientCardTabQuoting', True)))
        self.chkTabDeposit.setChecked(forceBool(props.get('showingClientCardTabDeposit', True)))
        self.chkTabSocStatus.setChecked(forceBool(props.get('showingClientCardTabSocStatus', True)))
        self.chkTabChangeJournal.setChecked(forceBool(props.get('showingClientCardTabChangeJournal', True)))
        self.chkTabFeature.setChecked(forceBool(props.get('showingClientCardTabFeature', True)))
        self.chkTabResearch.setChecked(forceBool(props.get('showingClientCardTabResearch', True)))
        self.chkTabDangerous.setChecked(forceBool(props.get('showingClientCardTabDangerous', True)))
        self.chkTabContingentKind.setChecked(forceBool(props.get('showingClientCardTabContingentKind', True)))
        self.chkTabIdentification.setChecked(forceBool(props.get('showingClientCardTabIdentification', True)))
        self.chkTabRelations.setChecked(forceBool(props.get('showingClientCardTabRelations', True)))
        self.chkTabContacts.setChecked(forceBool(props.get('showingClientCardTabContacts', True)))
        self.chkTabConsent.setChecked(forceBool(props.get('showingClientCardTabConsent', True)))
        self.chkTabMonitoring.setChecked(forceBool(props.get('showingClientCardTabMonitoring', True)))
        self.chkTabEpidCase.setChecked(forceBool(props.get('showingClientCardTabEpidCase', True)))

    def getProps(self, props):
        props['checkClientCardPolicyAffiliation'] = toVariant(self.cmbCheckPolicyAffiliation.currentIndex())
        props['showingClientCardDeathDate'] = toVariant(self.chkDeathDate.isChecked())
        props['showingClientCardBirthTime'] = toVariant(self.chkBirthTime.isChecked())
        props['showingClientCardSNILS'] = toVariant(self.chkSNILS.isChecked())
        props['showingClientCardCompulsoryPolisName'] = toVariant(self.chkCompulsoryPolisName.isChecked())
        props['showingClientCardCompulsoryPolisNote'] = toVariant(self.chkCompulsoryPolisNote.isChecked())
        props['showingClientCardDocOrigin'] = toVariant(self.chkDocOrigin.isChecked())
        props['showingClientCardVoluntaryPolicy'] = toVariant(self.chkVoluntaryPolicy.isChecked())
        props['showingClientCardVoluntaryPolicyName'] = toVariant(self.chkVoluntaryPolisName.isChecked())
        props['showingClientCardVoluntaryPolicyNote'] = toVariant(self.chkVoluntaryPolisNote.isChecked())
        props['showingClientCardTabAttach'] = toVariant(self.chkTabAttach.isChecked())
        props['showingClientCardTabWork'] = toVariant(self.chkTabWork.isChecked())
        props['showingClientCardTabQuoting'] = toVariant(self.chkTabQuoting.isChecked())
        props['showingClientCardTabDeposit'] = toVariant(self.chkTabDeposit.isChecked())
        props['showingClientCardTabSocStatus'] = toVariant(self.chkTabSocStatus.isChecked())
        props['showingClientCardTabChangeJournal'] = toVariant(self.chkTabChangeJournal.isChecked())
        props['showingClientCardTabFeature'] = toVariant(self.chkTabFeature.isChecked())
        props['showingClientCardTabResearch'] = toVariant(self.chkTabResearch.isChecked())
        props['showingClientCardTabDangerous'] = toVariant(self.chkTabDangerous.isChecked())
        props['showingClientCardTabContingentKind'] = toVariant(self.chkTabContingentKind.isChecked())
        props['showingClientCardTabIdentification'] = toVariant(self.chkTabIdentification.isChecked())
        props['showingClientCardTabRelations'] = toVariant(self.chkTabRelations.isChecked())
        props['showingClientCardTabContacts'] = toVariant(self.chkTabContacts.isChecked())
        props['showingClientCardTabConsent'] = toVariant(self.chkTabConsent.isChecked())
        props['showingClientCardTabMonitoring'] = toVariant(self.chkTabMonitoring.isChecked())
        props['showingClientCardTabEpidCase'] = toVariant(self.chkTabEpidCase.isChecked())
