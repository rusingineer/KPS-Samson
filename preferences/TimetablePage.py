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
## Страница настройки - панель График
##
#############################################################################

from PyQt4 import QtGui

from library.Utils            import (
                                         forceBool,
                                         forceInt,
                                         toVariant,
                                     )

from Ui_TimetablePage             import Ui_timetablePage

from Orgs.CheckedTreeWidgetOrgStructure import CCheckedTreeWidgetOrgStructure


class CTimetablePage(Ui_timetablePage, QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.treeOrgStructure = CCheckedTreeWidgetOrgStructure(self)
        self.setupUi(self)
        self.gridLayout_4.addWidget(self.treeOrgStructure)

    def setProps(self, props):
        self.cmbDoubleClickQueuePerson.setCurrentIndex(forceInt(props.get('doubleClickQueuePerson', 0)))
        self.chkAmbulanceUserCheckable.setChecked(forceBool(props.get('ambulanceUserCheckable', False)))
        self.chkSyncCheckableAndInvitiation.setChecked(forceBool(props.get('syncCheckableAndInvitiation', False)))
        self.cmbCombineTimetable.setCurrentIndex(forceInt(props.get('combineTimetable', 0)))
        self.treeOrgStructure.setupTree(props.get('TimetableOrgStructureCheckedNames'))
        self.cmbSwitchingToUserSchedule.setCurrentIndex(forceInt(props.get('switchingToUserSchedule')))
        self.chkShowComplaint.setChecked(forceBool(props.get('showComplaintColumn', False)))

    def getProps(self, props):
        props['TimetableOrgStructureCheckedNames'] = toVariant(self.treeOrgStructure.makeReportsToHideInsertValues())
        props['doubleClickQueuePerson'] = toVariant(self.cmbDoubleClickQueuePerson.currentIndex())
        props['ambulanceUserCheckable'] = toVariant(int(self.chkAmbulanceUserCheckable.isChecked()))
        props['syncCheckableAndInvitiation'] = toVariant(int(self.chkSyncCheckableAndInvitiation.isChecked()))
        props['combineTimetable']       = toVariant(self.cmbCombineTimetable.currentIndex())
        props['switchingToUserSchedule'] = toVariant(self.cmbSwitchingToUserSchedule.currentIndex())
        props['showComplaintColumn'] = toVariant(int(self.chkShowComplaint.isChecked()))
