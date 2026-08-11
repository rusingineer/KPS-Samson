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
## Страница настройки выбора ЛПУ, подразделения, региона
##
#############################################################################

from PyQt4 import QtGui

from library.Utils            import (
                                         forceBool,
                                         toVariant,
                                     )

from Ui_ActionPage import Ui_actionPage


class CActionPage(Ui_actionPage, QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)


    def setProps(self, props):
        self.chkOrgStructurePriorityForAddActions.setChecked(forceBool(props.get('orgStructurePriorityForAddActions', False)))
        self.cmbActionTemplatePriorityLoad.setCurrentIndex(forceBool(props.get('actionTemplatePriorityLoad', 1)))
        self.chkEnableUserDictionary.setChecked(forceBool(props.get('enableUserDictionary', False)))
        self.chkAutoResizeColumns.setChecked(forceBool(props.get('autoResizeColumns', False)))


    def getProps(self, props):
        props['orgStructurePriorityForAddActions'] = toVariant(bool(self.chkOrgStructurePriorityForAddActions.isChecked()))
        props['actionTemplatePriorityLoad'] = toVariant(bool(self.cmbActionTemplatePriorityLoad.currentIndex()))
        props['enableUserDictionary'] = toVariant(bool(self.chkEnableUserDictionary.isChecked()))
        props['autoResizeColumns'] = toVariant(bool(self.chkAutoResizeColumns.isChecked()))

