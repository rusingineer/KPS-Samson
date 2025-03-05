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
## Регистрационная карта пациента
##
#############################################################################

from PyQt4 import QtGui

from library.Utils import forceBool, toVariant

from Ui_InformerPage import Ui_InformerPage


class CInformerPage(Ui_InformerPage, QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)


    def setProps(self, props):
        self.chkInformerShowPersonSNILS.setChecked(forceBool(props.get('informerShowPersonSNILS', False)))
        self.chkInformerShowNoSNILS.setChecked(forceBool(props.get('informerShowNoSNILS', False)))
        self.chkInformerShowByUserArea.setChecked(forceBool(props.get('informerShowByUserArea', False)))
        self.chkInformerShowByUserNotArea.setChecked(forceBool(props.get('informerShowByUserNotArea', False)))
        self.chkDisableCheckDB.setChecked(forceBool(props.get('disableCheckDB', False)))


    def getProps(self, props):
        props['informerShowPersonSNILS'] = toVariant(self.chkInformerShowPersonSNILS.isChecked())
        props['informerShowNoSNILS'] = toVariant(self.chkInformerShowNoSNILS.isChecked())
        props['informerShowByUserArea'] = toVariant(self.chkInformerShowByUserArea.isChecked())
        props['informerShowByUserNotArea'] = toVariant(self.chkInformerShowByUserNotArea.isChecked())
        props['disableCheckDB'] = toVariant(self.chkDisableCheckDB.isChecked())

