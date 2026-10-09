# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Страница настройки ввода обращений
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QVariant

from library.Utils import (
    forceBool,
    forceInt,
    toVariant,
)

from Ui_EventPage import Ui_eventPage

DefaultAverageDuration = 28
DefaultPlanningFreq = 6
DefaultPlanningBegDate = 0
DefaultPlanningDuration = 1


class CEventPage(Ui_eventPage, QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.lblCheckDispanserObservation.setVisible(False)
        self.chkCheckDispanserObservation.setVisible(False)

    def setProps(self, props):
        self.edtAverageDuration.setValue(forceInt(props.get('averageDuration', DefaultAverageDuration)))
        self.chkFillDiagnosticsEventsResults.setChecked(forceBool(props.get('fillDiagnosticsEventsResults', True)))
        self.cmbDiagnosisTypeAfterFinalForm043.setCurrentIndex(forceInt(props.get('diagnosisTypeAfterFinalForm043', 0)))
        self.chkEventTypeActive.setChecked(forceBool(props.get('isPreferencesEventTypeActive', False)))
        self.chkSurveillancePlanningDialog.setChecked(forceBool(props.get('isPrefSurveillancePlanningDialog', False)))
        self.chkCheckDispanserObservation.setChecked(forceBool(props.get('checkDispanserObservation', False)))
        planningCheck = forceBool(props.get('paramPlanningCheck', False))
        self.chkPlanningParam.setChecked(planningCheck)
        self.grbParam.setEnabled(planningCheck)
        self.edtPlanningFreq.setValue(forceInt(props.get('paramPlanningFreq', DefaultPlanningFreq)))
        self.cmbPlanningBegDate.setCurrentIndex(forceInt(props.get('paramPlanningBegDate', DefaultPlanningBegDate)))


    def getProps(self, props):
        props['averageDuration'] = toVariant(self.edtAverageDuration.value())
        props['fillDiagnosticsEventsResults'] = toVariant(self.chkFillDiagnosticsEventsResults.isChecked())
        props['diagnosisTypeAfterFinalForm043'] = toVariant(self.cmbDiagnosisTypeAfterFinalForm043.currentIndex())
        props['isPreferencesEventTypeActive'] = toVariant(self.chkEventTypeActive.isChecked())
        props['isPrefSurveillancePlanningDialog'] = toVariant(self.chkSurveillancePlanningDialog.isChecked())
        props['checkDispanserObservation'] = toVariant(self.chkCheckDispanserObservation.isChecked())
        props['paramPlanningCheck'] = toVariant(self.chkPlanningParam.isChecked())
        props['paramPlanningFreq'] = toVariant(self.edtPlanningFreq.value())
        props['paramPlanningBegDate'] = toVariant(self.cmbPlanningBegDate.currentIndex())


    @pyqtSignature('bool')
    def on_chkPlanningParam_toggled(self):
        if self.chkPlanningParam.isChecked():
            self.grbParam.setEnabled(True)
        else:
            self.grbParam.setEnabled(False)
