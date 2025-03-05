# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2024 SAMSON Group. All rights reserved.
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

from Ui_HospitalBedsPage import Ui_HospitalBedsPage


class CHospitalBedsPage(Ui_HospitalBedsPage, QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)

    def setProps(self, props):
        self.chkTabDeath.setChecked(forceBool(props.get('showingHospitalBedsTabDeath', True)))
        self.chkTabEmergency.setChecked(forceBool(props.get('showingHospitalBedsTabEmergency', True)))
        self.chkTabFund.setChecked(forceBool(props.get('showingHospitalBedsTabFund', True)))
        self.chkTabLeaved.setChecked(forceBool(props.get('showingHospitalBedsTabLeaved', True)))
        self.chkTabPresence.setChecked(forceBool(props.get('showingHospitalBedsTabPresence', True)))
        self.chkTabQueue.setChecked(forceBool(props.get('showingHospitalBedsTabQueue', True)))
        self.chkTabReadyToLeave.setChecked(forceBool(props.get('showingHospitalBedsTabReadyToLeave', True)))
        self.chkTabReanimation.setChecked(forceBool(props.get('showingHospitalBedsTabReanimation', False)))
        self.chkTabReceived.setChecked(forceBool(props.get('showingHospitalBedsTabReceived', True)))
        self.chkTabRenunciation.setChecked(forceBool(props.get('showingHospitalBedsTabRenunciation', True)))
        self.chkTabTransfer.setChecked(forceBool(props.get('showingHospitalBedsTabTransfer', True)))

    def getProps(self, props):
        props['showingHospitalBedsTabDeath'] = toVariant(self.chkTabDeath.isChecked())
        props['showingHospitalBedsTabEmergency'] = toVariant(self.chkTabEmergency.isChecked())
        props['showingHospitalBedsTabFund'] = toVariant(self.chkTabFund.isChecked())
        props['showingHospitalBedsTabLeaved'] = toVariant(self.chkTabLeaved.isChecked())
        props['showingHospitalBedsTabPresence'] = toVariant(self.chkTabPresence.isChecked())
        props['showingHospitalBedsTabQueue'] = toVariant(self.chkTabQueue.isChecked())
        props['showingHospitalBedsTabReadyToLeave'] = toVariant(self.chkTabReadyToLeave.isChecked())
        props['showingHospitalBedsTabReanimation'] = toVariant(self.chkTabReanimation.isChecked())
        props['showingHospitalBedsTabReceived'] = toVariant(self.chkTabReceived.isChecked())
        props['showingHospitalBedsTabRenunciation'] = toVariant(self.chkTabRenunciation.isChecked())
        props['showingHospitalBedsTabTransfer'] = toVariant(self.chkTabTransfer.isChecked())
