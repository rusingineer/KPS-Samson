# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2019 SAMSON Group. All rights reserved.
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

from PyQt4 import QtGui

from library.Utils            import (
                                         forceInt,
                                         forceRef,
                                         toVariant,
                                     )

from Ui_ClientPlatePage import Ui_clientPlatePage


class CClientPlatePage(Ui_clientPlatePage, QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.cmbTFAccountingSystemId.setTable('rbAccountingSystem', True)
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            self.lblTFAccountingSystemId.setVisible(False)
            self.cmbTFAccountingSystemId.setVisible(False)



    def setProps(self, props):
        self.cmbShowingInInfoBlockSocStatus.setCurrentIndex(forceInt(props.get('showingInInfoBlockSocStatus', 0)))
        self.cmbShowingAttach.setCurrentIndex(forceInt(props.get('showingAttach',0)))
        self.cmbTFAccountingSystemId.setValue(forceRef(props.get('TFAccountingSystemId', None)))


    def getProps(self, props):
        props['showingInInfoBlockSocStatus'] = toVariant(self.cmbShowingInInfoBlockSocStatus.currentIndex())
        props['showingAttach'] = toVariant(self.cmbShowingAttach.currentIndex())
        props['TFAccountingSystemId'] = toVariant(self.cmbTFAccountingSystemId.value())

