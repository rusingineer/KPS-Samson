# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4                              import QtGui
from Events.Ui_TempInvalidListDialog    import Ui_TempInvalidList
from library.Utils                      import formatShortName
from library.DialogBase                 import CDialogBase
from Users.Rights                       import urEditClosedEvent


class CTempInvalidListDialog(CDialogBase, Ui_TempInvalidList):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)


    def setEventEditor(self, eventEditor):
        self.setWindowTitle(u'Трудоспособность %s' % formatShortName(eventEditor.clientLastName, eventEditor.clientFirstName, eventEditor.clientPatrName))
        isProtected = QtGui.qApp.userHasRight(urEditClosedEvent)

        self.grpTempInvalid.setEventEditor(eventEditor)
        self.grpTempInvalid.setType(0, '1')
        self.grpTempInvalid.pickupTempInvalid()
        self.grpTempInvalid.protectFromEdit(isProtected)

        self.grpAegrotat.setEventEditor(eventEditor)
        self.grpAegrotat.setType(0, '2')
        self.grpAegrotat.pickupTempInvalid()
        self.grpAegrotat.protectFromEdit(isProtected)

        self.grpDisability.setEventEditor(eventEditor)
        self.grpDisability.setType(1)
        self.grpDisability.pickupTempInvalid()
        self.grpDisability.protectFromEdit(isProtected)

        self.grpVitalRestriction.setEventEditor(eventEditor)
        self.grpVitalRestriction.setType(2)
        self.grpVitalRestriction.pickupTempInvalid()
        self.grpVitalRestriction.protectFromEdit(isProtected)

