# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, QTime, QDateTime, pyqtSignature, QVariant
from PyQt4.QtGui import QDialog

from library.Utils import forceRef, forceDate, firstMonthDay, lastMonthDay, forceString, forceBool, getPref, setPref
from library.crbcombobox import CRBComboBox
from Orgs.Utils import getOrgStructureDescendants
from Ui_EconomicAnalisysSetupDialogEx import Ui_EconomicAnalisysSetupDialogEx
from HospitalBeds.HospitalizationEventDialog import CFindClientInfoDialog
from library.Utils import forceStringEx


class CEconomicAnalisysSetupDialog(QDialog, Ui_EconomicAnalisysSetupDialogEx):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbFinance.setTable('rbFinance', addNone=True)
        # self.cmbContract.setTable('Contract', "concat_ws(' | ', (select rbFinance.name from rbFinance where rbFinance.id = Contract.finance_id), Contract.resolution, Contract.number)")
        # self.cmbContract.setAddNone(True, u'не задано')
        self.cmbContract.setMainDialog(self)
        self.cmbSpeciality.setTable('rbSpeciality', True)
        self.cmbProfileBed.setTable('rbHospitalBedProfile', True)
        self.cmbProfileBed.setShowFields(CRBComboBox.showCodeAndName)
        self.cmbPurpose.setTable('rbEventTypePurpose')
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbVidPom.setTable('rbMedicalAidType', True)
        self.cmbEventType.setTable('EventType', False, 'deleted = 0 AND isActive = 1', 'code ASC')
        self.cmbPerson.addNotSetValue()
        self.setVisibilityProfileBed(False)
        self.setDetailToVisible(False)
        self.setGroupByPersonSnilsVisible(False)
        self.setMedicalTypeTotalsVisible(False)
        self.setuslVisible(False)
        self.settypePayVisible(False)
        self.setzVisible(True)
        self.setVisibleWidget('cmbStepECO', False)
        self.setVisibleWidget('lblStepECO', False)
        self.setDetailVisible(False)
        self.setPrintAccNumberVisible(False)
        self.setHideNullVisible(False)
        self.setEventRelegateOrgVisible(False)
        self.launchedFromAccountingDialog(parent)
        self.loadPrefs()


    def loadPrefs(self):
        prefs = QtGui.qApp.preferences
        dlgGeometry = getPref(prefs.appPrefs, 'CEconomicAnalisysSetupDialog_geometry', QVariant()).toByteArray()
        if dlgGeometry:
            self.restoreGeometry(dlgGeometry)


    def savePrefs(self):
        prefs = QtGui.qApp.preferences
        setPref(prefs.appPrefs, 'CEconomicAnalisysSetupDialog_geometry', QVariant(self.saveGeometry()))


    def closeEvent(self, event):
        self.savePrefs()


    def hideAll(self):
        for i in range(self.layout().count()):
            w = self.layout().itemAt(i).widget()
            if w and w != self.scrollArea:
                w.setVisible(False)

    def setVisibleWidgets(self, *args):
        self.hideAll()
        for arg in args:
            if hasattr(self, arg):
                getattr(self, arg).setVisible(True)
        self.buttonBox.setVisible(True)
        self.shrink()

    def setVisibleWidget(self, widget, value):
        if hasattr(self, widget):
            getattr(self, widget).setVisible(value)

    def shrink(self):
        self.resize(self.minimumSize())

    def updateContractFilter(self):
        # db = QtGui.qApp.db
        # tableContract = db.table("Contract")
        # filter = []
        # filter.append(tableContract['deleted'].eq(0))
        # filter.append(tableContract['begDate'].dateLe(self.edtEndDate.date()))
        # filter.append(tableContract['endDate'].dateGe(self.edtBegDate.date()))
        financeId = self.cmbFinance.value()

        if self.cmbContract._popup:
            self.cmbContract._popup.cmbFinance.setValue(financeId)
            self.cmbContract._popup.edtEndDate.setDate(self.edtEndDate.date())
            self.cmbContract._popup.edtBegDate.setDate(self.edtBegDate.date())

        # if financeId:
        #     filter.append(tableContract['finance_id'].eq(financeId))
        #self.cmbContract.setFilter(db.joinAnd(filter))

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setVisibilityProfileBed(self, visibility):
        self.cmbProfileBed.setVisible(visibility)
        self.lblProfileBed.setVisible(visibility)

    def setFinanceVisible(self, visible=False):
        self.lblFinance.setVisible(visible)
        self.cmbFinance.setVisible(visible)

    def setOrgStructureVisible(self, value):
        self.lblOrgStructure.setVisible(value)
        self.cmbOrgStructure.setVisible(value)

    def setSpecialityVisible(self, value):
        self.lblSpeciality.setVisible(value)
        self.cmbSpeciality.setVisible(value)

    def setPersonVisible(self, value):
        self.lblPerson.setVisible(value)
        self.cmbPerson.setVisible(value)
        self.chkPersonBySnils.setVisible(value)

    def setVidPomVisible(self, value):
        self.lblVidPom.setVisible(value)
        self.cmbVidPom.setVisible(value)

    def setRazrNasVisible(self, value):
        self.lblRazrNas.setVisible(value)
        self.cmbRazrNas.setVisible(value)

    def setSchetaVisible(self, value):
        self.lblScheta.setVisible(value)
        self.cmbScheta.setVisible(value)

    def setPayerVisible(self, value):
        self.lblPayer.setVisible(value)
        self.cmbPayer.setVisible(value)

    def setEventTypeVisible(self, value):
        self.lblEventType.setVisible(value)
        self.cmbEventType.setVisible(value)

    def setSexVisible(self, value):
        self.ismancheckedage.setVisible(value)      #ymd
        self.iswomencheckedage.setVisible(value)  # ymd
    #    self.lblSex.setVisible(value)   #ymd
    #    self.cmbSex.setVisible(value)   #ymd

    def settypePayVisible(self, value):
        self.lbltypePay.setVisible(value)
        self.cmbtypePay.setVisible(value)

    def setCashPaymentsVisible(self, value):
        self.cbCashPayments.setVisible(value)

    def setDetailToVisible(self, value):
        self.lblDetailTo.setVisible(value)
        self.cmbDetailTo.setVisible(value)

    def setGroupByPersonSnilsVisible(self, value):
        self.chkGroupByPersonSnils.setVisible(value)

    def setMedicalTypeTotalsVisible(self, value):
        self.chkMedicalTypeTotals.setVisible(value)

    def setzVisible(self, value):
        self.grpdatetype.setFlat(value)

    def setAgeVisible(self, value):
        self.label.setVisible(value)  # ymd
        self.spnManAgeBeg.setVisible(value)  # ymd
        self.cmbMenBegAgeUnit.setVisible(value)  # ymd
        self.lblAge2.setVisible(value)  # ymd
        self.spnManAgeEnd.setVisible(value)  # ymd
        self.cmbMenEndAgeUnit.setVisible(value)  # ymd
        self.label_2.setVisible(value)  # ymd
        self.spnWomanAgeBeg.setVisible(value)  # ymd
        self.cmbWomenBegAgeUnit.setVisible(value)  # ymd
        self.lblAge2_2.setVisible(value)  # ymd
        self.spnWomanAgeEnd.setVisible(value)  # ymd
        self.cmbWomenEndAgeUnit.setVisible(value)  # ymd
        self.ageHolder.setVisible(value)  # ymd
        self.widget.setVisible(value)  # ymd
        #self.lblAge.setVisible(value)      #ymd
        #self.lblAge2.setVisible(value)     #ymd
        #self.spnAge1.setVisible(value)     #ymd
        #self.spnAge2.setVisible(value)     #ymd
        pass                                #ymd

    def setProfileBedVisible(self, value):
        self.lblProfileBed.setVisible(value)
        self.cmbProfileBed.setVisible(value)

    def setPriceVisible(self, value):
        self.cbPrice.setVisible(value)

    def setuslVisible(self, value):
        self.cbusl.setVisible(value)

    def setDetailVisible(self, value):
        self.chkDetail.setVisible(value)

    def setPrintAccNumberVisible(self, value):
        self.chkPrintAccNumber.setVisible(value)

    def setEndDateVisible(self, value):
        self.lblEndDate.setVisible(value)
        self.edtEndDate.setVisible(value)

    def setNoschetaVisible(self, value):
        self.lblNoscheta.setVisible(value)
        self.cmbNoscheta.setVisible(value)

    def setDateTypeVisible(self, value):
        self.grpdatetype.setVisible(value)

    def setHideNullVisible(self, value):
        self.chkHideNullStrOM.setVisible(value)

    def setVisibilityForDateType(self, datetype):
        if datetype == 1:
            self.setDateEnabled(True)
            self.setNoschetaEnabled(False)
            self.setSchetaEnabled(False)
            self.setAccountTypeEnabled(False)
        elif datetype == 2:
            self.setAccountTypeEnabled(True)
            self.setDateEnabled(True)
            self.setNoschetaEnabled(False)
            self.setSchetaEnabled(True)
        elif datetype == 3:
            self.setAccountTypeEnabled(True)
            self.setSchetaEnabled(True)
            if self.printOnlyByAccountIdList:
                self.grpdatetype.setEnabled(False)
                self.setDateEnabled(False)
                self.setNoschetaEnabled(False)
            else:
                self.setDateEnabled(True)
                self.setNoschetaEnabled(True)


    def setEventRelegateOrgVisible(self, value):
        self.lblEventRelegateOrg.setVisible(value)
        self.cmbEventRelegateOrg.setVisible(value)

    def setDateEnabled(self, enabled):
        self.lblBegDate.setEnabled(enabled)
        self.lblEndDate.setEnabled(enabled)
        self.edtBegDate.setEnabled(enabled)
        self.edtEndDate.setEnabled(enabled)
        self.edtBegTime.setEnabled(enabled)
        self.edtEndTime.setEnabled(enabled)

    def setAccountTypeEnabled(self, enabled):
        self.lblAccountType.setEnabled(enabled)
        self.cmbAccountType.setEnabled(enabled)

    def setNoschetaEnabled(self, enabled):
        self.lblNoscheta.setEnabled(enabled)
        self.cmbNoscheta.setEnabled(enabled)

    def setSchetaEnabled(self, enabled):
        self.lblScheta.setEnabled(enabled)
        self.cmbScheta.setEnabled(enabled)

    def setParams(self, params):
        date = QDate().currentDate().addDays(-3)
        self.cmbFinance.setValue(params.get('financeId', None))
        self.edtBegDate.setDate(params.get('begDate', firstMonthDay(date)))
        self.edtEndDate.setDate(params.get('endDate', lastMonthDay(date)))
        self.edtBegTime.setTime(params.get('begTime', QTime()))
        self.edtEndTime.setTime(params.get('endTime', QTime()))
        self.cmbContract.setValue(params.get('contractId', None))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbVidPom.setValue(params.get('vidPom', None))
        self.cmbRazrNas.setCurrentIndex(params.get('naselenie', 0))
        self.cmbStepECO.setCurrentIndex(params.get('stepECO', 0))
        self.cmbScheta.setCurrentIndex(params.get('scheta', 0))
        self.cmbPayer.setValue(params.get('payer', None))
        if params.get('eventTypeCheckedRows', None):
            self.cmbEventType.setCheckedRows(params.get('eventTypeCheckedRows', None))
        if params.get('eventPurposeId', None):
            self.cmbEventType._filter = 'deleted = 0 AND isActive = 1' + ' AND purpose_id = %s' % params.get('eventPurposeId', None)
        if params.get('eventTypeCheckedAscDesc', None):
            self.cmbEventType._order = params.get('eventTypeCheckedAscDesc', None)
        self.cmbPurpose.setValue(params.get('eventPurposeId', None))
        self.chkDetail.setChecked(params.get('paydetail', False))
        self.chkPrintAccNumber.setChecked(params.get('printAccNumber', False))
        # self.chbOsnScheta.setChecked(params.get('osnScheta', False))
        self.cmbProfileBed.setValue(params.get('profileBed', None))
        dataType = params.get('dataType', 1) if not self.printOnlyByAccountIdList else 3
        if dataType == 1:
            self.rbDatalech.setChecked(True)
            self.cbOnlyNotExposed.setChecked(params.get('onlyNotExposed', False))
        if dataType == 2:
            self.rbSchetf.setChecked(True)
        if dataType == 3:
            self.rbNomer.setChecked(True)
        self.setVisibilityForDateType(dataType)
        self.cmbNoscheta.setValue(params.get('accountId', None))
        self.cmbAccountType.setCurrentIndex(params.get('accountType', 0))
        #self.cmbSex.setCurrentIndex(params.get('sex', 0))  #ymd
        self.cmbMenBegAgeUnit.setCurrentIndex(4)  # ymd
        self.cmbMenEndAgeUnit.setCurrentIndex(4)  # ymd
        self.cmbWomenEndAgeUnit.setCurrentIndex(4)  # ymd
        self.cmbWomenBegAgeUnit.setCurrentIndex(4)  # ymd
        typePay = params.get('typePay', None)
        if typePay is None:
            self.cmbtypePay.setCurrentIndex(0)
        else:
            self.cmbtypePay.setCurrentIndex(params['typePay'] + 1)
        self.cmbDetailTo.setCurrentIndex(params.get('detailTo', 0))
        self.chkGroupByPersonSnils.setChecked(bool(params.get('groupByPersonSnils', 0)))
        self.chkMedicalTypeTotals.setChecked(bool(params.get('medicalTypeTotals', 0)))
        #self.spnAge1.setValue(params.get('age1', 0))       #ymd
        #self.spnAge2.setValue(params.get('age2', 150))     #ymd
        self.cbCashPayments.setChecked(params.get('cashPayments', False))
        self.edtFilterClientId.setText(forceString(params.get('filterClientId', '')))

        self.chkMKBFilter.setChecked(params.get('MKBFilter', 0))
        self.edtMKBFrom.setText(params.get('MKBFrom', 'A00.00'))
        self.edtMKBTo.setText(params.get('MKBTo', 'Z99.99'))

        self.chkHideNullStrOM.setChecked(params.get('hideNull', False))
        self.cmbEventRelegateOrg.setValue(params.get('eventRelegateOrgId', None))
        self.updateContractFilter()

    # def setOsnScheta(self, enabled):
    #     self.chbOsnScheta.setEnabled(enabled)
    #     if not enabled:
    #         self.chbOsnScheta.setChecked(False)

    def setListDetailTo(self, detailList):
        self.cmbDetailTo.clear()
        self.cmbDetailTo.setMaxCount(len(detailList))
        for detailName in detailList:
            self.cmbDetailTo.addItem(detailName)

    def launchedFromAccountingDialog(self, parentInstance):
        from Accounting.AccountingDialog import CAccountingDialog
        self.printOnlyByAccountIdList = False
        if isinstance(parentInstance, CAccountingDialog):
            self.printOnlyByAccountIdList = True


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['begTime'] = self.edtBegTime.time()
        result['endTime'] = self.edtEndTime.time()
        result['contractId'] = self.cmbContract.value()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['specialityId'] = self.cmbSpeciality.value()
        result['personId'] = self.cmbPerson.value()
        result['personIdList'] = []
        if self.cmbPerson.value():
            if self.chkPersonBySnils.isChecked():
                snils = forceString(QtGui.qApp.db.translate('Person', 'id', self.cmbPerson.value(), 'SNILS'))
                if snils:
                    tablePerson = QtGui.qApp.db.table('Person')
                    cond = [tablePerson['SNILS'].eq(snils), tablePerson['deleted'].eq(0)]
                    if self.cmbSpeciality.value():
                        cond.append(tablePerson['speciality_id'].eq(self.cmbSpeciality.value()))
                    if self.cmbOrgStructure.value():
                        cond.append(tablePerson['orgStructure_id'].inlist(
                            getOrgStructureDescendants(self.cmbOrgStructure.value())))
                    if self.edtBegDate.date() and self.rbDatalech.isChecked():
                        cond.append(QtGui.qApp.db.joinOr([
                            tablePerson['retireDate'].isNull(),
                            tablePerson['retireDate'].ge(self.edtBegDate.date())
                        ]))
                    result['personIdList'] = QtGui.qApp.db.getDistinctIdList(tablePerson, where=cond)
                if not result['personIdList']:
                    result['personIdList'] = [-1]
        result['financeId'] = self.cmbFinance.value()
        result['vidPom'] = self.cmbVidPom.value()
        if self.cmbRazrNas.isEnabled():
            result['naselenie'] = self.cmbRazrNas.currentIndex()
        
        result['scheta'] = self.cmbScheta.currentIndex()
        result['payer'] = self.cmbPayer.value()
        result['eventType'] = self.cmbEventType.value()
        result['eventTypeCheckedRows'] = self.cmbEventType.getCheckedRows()
        result['eventTypeCheckedAscDesc'] = self.cmbEventType._order
        result['eventTypeCheckedOldFilter'] = self.cmbEventType._filter.split(' ')[-1]
        result['eventPurposeId'] = self.cmbPurpose.value()
        result['accountId'] = self.cmbNoscheta.value()
        result['accountType'] = self.cmbAccountType.currentIndex()
        result['profileBed'] = forceRef(self.cmbProfileBed.value())
        if self.grpdatetype.isFlat():
            result['dataType'] = 1
            if self.rbDatalech.isChecked():
                result['dataType'] = 1
                result['onlyNotExposed'] = self.cbOnlyNotExposed.isChecked()
            if self.rbSchetf.isChecked():
                result['dataType'] = 2
            if self.rbNomer.isChecked():
                result['dataType'] = 3
        if self.cbPrice.isChecked():
            result['without0price'] = 1
        if self.cbusl.isChecked():
            result['without0usl'] = 1
        result['paydetail'] = self.chkDetail.isChecked()
        result['printAccNumber'] = self.chkPrintAccNumber.isChecked()
        # result['osnScheta'] = self.chbOsnScheta.isChecked()
        #result['sex'] = self.cmbSex.currentIndex()   #ymd
        result['typePay'] = [None, 0, 1, 2][self.cmbtypePay.currentIndex()]
        result['detailTo'] = self.cmbDetailTo.currentIndex()
        result['groupByPersonSnils'] = int(self.chkGroupByPersonSnils.isChecked())
        result['medicalTypeTotals'] = int(self.chkMedicalTypeTotals.isChecked())
        #result['age1'] = self.spnAge1.value()      #ymd
        #result['age2'] = self.spnAge2.value()      #ymd
#ymd st
        if self.ismancheckedage.isChecked():                                                   #ymd
            result['addManAgeCondition'] = 1                                                   #ymd
        result['manAgeBegType'] = [0, 1, 2, 3, 4][self.cmbMenBegAgeUnit.currentIndex()]         #ymd
        result['manAgeEndType'] = [0, 1, 2, 3, 4][self.cmbMenEndAgeUnit.currentIndex()]         #ymd
        result['manAgeBegValue'] = self.spnManAgeBeg.value()                                    #ymd
        result['manAgeEndValue'] = self.spnManAgeEnd.value()                                    #ymd

        if self.iswomencheckedage.isChecked():                                                  #ymd
            result['addWomanAgeCondition'] = 1                                                  #ymd
        result['womanAgeBegType'] = [0, 1, 2, 3, 4][self.cmbWomenBegAgeUnit.currentIndex()]     #ymd
        result['womanAgeEndType'] = [0, 1, 2, 3, 4][self.cmbWomenEndAgeUnit.currentIndex()]     #ymd
        result['womanAgeBegValue'] = self.spnWomanAgeBeg.value()                                #ymd
        result['womanAgeEndValue'] = self.spnWomanAgeEnd.value()                                #ymd
#ymd end
        if self.cmbStepECO.isVisibleTo(self):
            result['stepECO'] = self.cmbStepECO.currentIndex()
        if self.edtFilterClientId.text():
            result['filterClientId'] = forceStringEx(self.edtFilterClientId.text())
        result['cashPayments'] = self.cbCashPayments.isChecked()

        result['MKBFilter'] = True if self.chkMKBFilter.isChecked() else False
        if result['MKBFilter']:
            result['MKBFrom'] = unicode(self.edtMKBFrom.text()) if unicode(self.edtMKBFrom.text()) != '.' else u'A00.00'
            result['MKBFrom'] = result['MKBFrom'] if result['MKBFrom'][-1] != '.' else result['MKBFrom'][:-1]
            result['MKBTo'] = unicode(self.edtMKBTo.text()) if unicode(self.edtMKBTo.text()) != '.' else u'Z99.99'
            result['MKBTo'] = result['MKBTo'] if result['MKBTo'][-1] != '.' else result['MKBTo'][:-1]

        result['hideNull'] = self.chkHideNullStrOM.isChecked()
        result['eventRelegateOrgId'] = self.cmbEventRelegateOrg.value()
        return result

    def onStateChanged(self, state):
        self.lblBegDateConfirmation.setEnabled(state)
        self.lblEndDateConfirmation.setEnabled(state)

    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.cmbPerson.setBegDate(date)
        self.cmbNoscheta.updateFilter(forceDate(self.edtBegDate.date()), forceDate(self.edtEndDate.date()))
        self.updateContractFilter()

    @pyqtSignature('bool')
    def on_rbDatalech_toggled(self, checked):
        if checked:
            self.setVisibilityForDateType(1)
            # self.cmbRazrNas.setEnabled(checked)
            # self.lblRazrNas.setEnabled(checked)

    @pyqtSignature('bool')
    def on_rbSchetf_toggled(self, checked):
        if checked:
            self.setVisibilityForDateType(2)
            # self.cmbRazrNas.setEnabled(not checked)
            # self.lblRazrNas.setEnabled(not checked)

    @pyqtSignature('bool')
    def on_rbNomer_toggled(self, checked):
        if checked:
            self.setVisibilityForDateType(3)
            # self.cmbRazrNas.setEnabled(not checked)
            # self.lblRazrNas.setEnabled(not checked)

    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.cmbPerson.setEndDate(date)
        self.cmbNoscheta.updateFilter(forceDate(self.edtBegDate.date()), forceDate(self.edtEndDate.date()))
        self.updateContractFilter()

    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)
        
        
    @pyqtSignature('int')
    def on_cmbFinance_currentIndexChanged(self, index):
        self.updateContractFilter()
        

    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        specialityId = self.cmbSpeciality.value()
        self.cmbPerson.setSpecialityId(specialityId)

    @pyqtSignature('int')
    def on_cmbPurpose_currentIndexChanged(self, index):
        _filter = ''
        _order = ''

        result = self.params()
        eventPurposeIdNew = result.get('eventPurposeId', None)
        eventPurposeIdOld = result.get('eventTypeCheckedOldFilter', None)
        eventTypeCheckedRows = result.get('eventTypeCheckedRows', None)
        eventTypeCheckedAscDesc = result.get('eventTypeCheckedAscDesc', None)

        if result.get('eventPurposeId', None):
            _filter = 'deleted = 0 AND isActive = 1' + ' AND purpose_id = %s' % result.get('eventPurposeId', None)
        if eventTypeCheckedAscDesc:
            _order = result.get('eventTypeCheckedAscDesc', None)

        self.cmbEventType.clear()
        self.cmbEventType.setTable('EventType', False, _filter, _order)

        if eventTypeCheckedRows:
            if eventPurposeIdNew:
                if (int(eventPurposeIdNew) == int(eventPurposeIdOld)):
                    self.cmbEventType.setCheckedRows(eventTypeCheckedRows)
            if eventPurposeIdNew is None:
                self.cmbEventType.setCheckedRows(eventTypeCheckedRows)


    @pyqtSignature('')
    def on_btnFindClientInfo_clicked(self):
        self.edtFilterClientId.setText('')
        HospitalizationEvent = CFindClientInfoDialog(self, [])
        if HospitalizationEvent:
            HospitalizationEvent.setIsHBDeath(True)
            HospitalizationEvent.setHospitalBedsHasRight(False)
            HospitalizationEvent.setWindowTitle(u'Поиск пациента')
            HospitalizationEvent.setupGetClientIdMenuNew()
            HospitalizationEvent.exec_()
            self.edtFilterClientId.setText(forceString(HospitalizationEvent.filterClientId))

    @pyqtSignature('int')
    def on_cmbPerson_currentIndexChanged(self, index):
        self.chkPersonBySnils.setEnabled(self.cmbPerson.value() is not None)
        if not self.chkPersonBySnils.isEnabled():
            self.chkPersonBySnils.setChecked(False)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        self.savePrefs()


def getusl(params):
    cond2 = []
    usl=params.get('without0usl', None)
    if usl:
        cond2=("q.nam,")
        os=("rbService.name AS nam,")
        os1=(",q.nam ,q.fio")
    else:
        cond2=(" ")
        os=("")
        os1=(",q.event_id")
    return cond2,os,os1


def getCond(params):
    db = QtGui.qApp.db
    cond = []
    begDate = params.get('begDate', None)
    endDate = params.get('endDate', None)
    begTime = params.get('begTime', QTime())
    endTime = params.get('endTime', QTime())
    begDateTime = QDateTime(begDate, begTime)
    endDateTime = QDateTime(endDate, endTime)
    
    # способ формирования выборки
    dataType = params.get('dataType', 1)
    # по дате лечения
    if dataType == 1:
        if begDateTime:
            cond.append("Event.execDate >= {0}".format(db.formatDate(begDateTime)))
        if endDateTime:
            cond.append("Event.execDate <= {0}".format(db.formatDate(endDateTime)))
        if params.get('onlyNotExposed', False):
            cond.append("NOT EXISTS(SELECT NULL FROM Account_Item ai WHERE ai.event_id = Event.id AND ai.deleted = 0)")
        #cond.append("Account_Item.reexposeItem_id is null")
    
    # по договору
    contractId = params.get('contractId', None)
    if contractId:
        tableContract = db.table("Contract")
        cond.append(tableContract['id'].eq(contractId))

    # по плательщику
    payerId = params.get('payer', None)
    if payerId:
        if dataType == 1:
            cond.append(u"""CASE WHEN substr(Insurer.area, 1, 2) = '%(defaultRegion)s' AND Insurer.head_id is not null THEN headInsurer.id
WHEN substr(Insurer.area, 1, 2) = '%(defaultRegion)s' AND Insurer.head_id is null THEN Insurer.id
WHEN Insurer.id is not null and substr(Insurer.area, 1, 2) <> '%(defaultRegion)s' THEN ContractPayer.id
ELSE NULL END = {0:d}""".format(payerId))
        else:
            cond.append("Payer.id = {0:d}".format(payerId))

    # по направителю
    eventRelegateOrgId = params.get('eventRelegateOrgId', None)
    if eventRelegateOrgId:
        cond.append("Event.relegateOrg_id IN ({0})".format(eventRelegateOrgId))

    # по условия оказания МП
    vidPom = params.get('vidPom', None)
    if vidPom:
#        regionalCode = forceRef(db.translate('rbMedicalAidType', 'id', vidPom, 'regionalCode'))
        cond.append("mt.id = {0}".format(vidPom))

    # краевые/инокраевые
    naselenie = params.get('naselenie', None)
    if naselenie:
        region = QtGui.qApp.provinceKLADR()[:2]
        payer = 'Payer' if dataType in [2, 3] else 'Insurer'
        if naselenie == 1:
            if region == '23':
                cond.append("substr({payer}.area, 1, 2) = '23' and {payer}.infisCode <> '9007'".format(payer=payer))
            else:
                cond.append("substr({payer}.area, 1, 2) = '{region}'".format(payer=payer, region=region))
        elif naselenie == 2:
            if region == '23' and dataType in [2, 3]:
                cond.append("{payer}.infisCode = '9007'".format(payer=payer))
            else:
                cond.append("substr({payer}.area, 1, 2) <> '{region}'".format(payer=payer, region=region))

    # по типу состояния оплаты счетов
    scheta = params.get('scheta', 0)
    if scheta:
        # TODO: Переделать логику определения оплаченных счетов
        if scheta == 1:  # представленные к оплате
            cond.append("Account_Item.id is not null")
        if scheta == 2:  # подлежащие к оплате
            cond.append("Account_Item.id is not null and Account_Item.refuseType_id is null")
        if scheta == 3:  # отказаны
            cond.append("Account_Item.id is not null and Account_Item.refuseType_id is not null")

    # по счет фактуре
    if dataType == 2:
        if begDateTime:
            cond.append("Account.date >= {0}".format(db.formatDate(begDateTime)))
        if endDateTime:
            cond.append("Account.date < {0}".format(db.formatDate(endDateTime)))
        accountType = params.get('accountType', 0)
        if accountType == 1:
            cond.append(u"rbAccountType.name like 'основн%%'")
        elif accountType == 2:
            cond.append(u"rbAccountType.name like 'основн%%' or rbAccountType.name like 'дополн%%'")
        elif accountType == 3:
            cond.append(u"rbAccountType.name like 'повторн%%'")

    # по номеру счета
    if dataType == 3:
        if params.get('accountIdList', None) is not None:
            cond.append(db.table('Account')['id'].inlist(params['accountIdList']))
        else:
            accountId = params.get('accountId')
            if accountId:
                cond.append("Account.id = {0:d}".format(accountId))

    # по врачу или подразделению
    personId = params.get('personId', None)
    personIdList = params.get('personIdList', [])
    orgStructureId = params.get('orgStructureId', None)
    if personId and not personIdList:
        cond.append("Person.id = {0:d}".format(personId))
    elif personIdList:
        cond.append(db.table("Person")['id'].inlist(personIdList))
    else:
        if orgStructureId:
            OrgStructure = db.table("OrgStructure")
            cond.append(OrgStructure['id'].inlist(getOrgStructureDescendants(params['orgStructureId'])))

    # по специальности
    specialityId = params.get('specialityId', None)
    if specialityId:
        cond.append('rbSpeciality.id = {0:d}'.format(specialityId))

    # по назначению события
    eventPurposeId = params.get('eventPurposeId', None)
    if eventPurposeId:
        cond.append("EventType.purpose_id = {0:d}".format(eventPurposeId))

    # по типу события
    eventTypeId = params.get('eventType', None)
    if eventTypeId:
        cond.append("Event.eventType_id IN ({0})".format(eventTypeId))

    # не учитывать услуги с нулевой ценой
    if params.get('without0price', None):
        cond.append("ct.price > 0")

    # # по основным счетам
    # if params.get('osnScheta', None):
    #     cond.append('not exists(select reex.id from Account_Item reex where reex.reexposeItem_id =  Account_Item.id)')

    # пол
    #sex = params.get('sex', 0)                             #ymd
    #if sex > 0:                                            #ymd
    #    cond.append("Client.sex = {0:d}".format(sex))      #ymd

    # тип оплаты
    typePay = params.get('typePay', 0)
    if typePay is not None and typePay!=2:
        cond.append("Event_Payment.typePayment = {0:d}".format(typePay))
        
    # возраст
    #age1 = params.get('age1', None)                                                        #ymd
    #age2 = params.get('age2', None)                                                        #ymd
    #if age1 is not None and age2 is not None:                                              #ymd
    #    if age1 == 0 and age2 == 150:                                                      #ymd
    #        pass                                                                           #ymd
    #    elif age1 == age2:                                                                 #ymd
    #        cond.append('age(Client.birthDate, Event.setDate) = {0:d}'.format(age1))       #ymd
    #    else:                                                                              #ymd
    #        cond.append('Event.setDate >= ADDDATE(Client.birthDate, INTERVAL {0:d} YEAR) and Event.setDate <= ADDDATE(Client.birthDate, INTERVAL {1:d} YEAR )'.format(age1, age2+1)) # age2+1 сделано для работы фильтра при котором выбирая в диалог окне 17 мы получаем фильтр до 18 лет  #ymd

    # тип финансирования
    financeId = params.get('financeId', None)
    if financeId:
        cond.append('rbFinance.id = {0:d}'.format(financeId))

    # профиль койки
    profileBedId = params.get('profileBed', None)
    if profileBedId:
        cond.append('rbHospitalBedProfile.id = {0:d}'.format(profileBedId))
#ymd st
    manCond = (
        'Client.sex = 1 and Event.setDate >= ADDDATE(Client.birthDate, INTERVAL {0:d} {1:s}) and Event.setDate <= ADDDATE(Client.birthDate, INTERVAL {2:d} {3:s} )'). \
        format(params.get('manAgeBegValue', 0),
               ['YEAR', 'DAY', 'WEEK', 'MONTH', 'YEAR'][params.get('manAgeBegType', 0)],
               params.get('manAgeEndValue', 0),
               ['YEAR', 'DAY', 'WEEK', 'MONTH', 'YEAR'][params.get('manAgeEndType', 0)])
    wumanCond = (
        'Client.sex = 2 and Event.setDate >= ADDDATE(Client.birthDate, INTERVAL {0:d} {1:s}) and Event.setDate <= ADDDATE(Client.birthDate, INTERVAL {2:d} {3:s} )'). \
        format(params.get('womanAgeBegValue', 0),
               ['YEAR', 'DAY', 'WEEK', 'MONTH', 'YEAR'][params.get('womanAgeBegType', 0)],
               params.get('womanAgeEndValue', 0),
               ['YEAR', 'DAY', 'WEEK', 'MONTH', 'YEAR'][params.get('womanAgeEndType', 0)])

    # пациент
    filterClientId = params.get('filterClientId', None)
    if filterClientId:
        cond.append('Client.id = {0}'.format(filterClientId))

    # МКБ
    filterMKB = params.get('MKBFilter', False)
    if filterMKB:
        MKBFrom = params.get('MKBFrom', 'A00.00')
        MKBTo = params.get('MKBTo', 'Z99.99')
        if MKBFrom < MKBTo:
            cond.append("d.MKB >= '{0}' AND d.MKB <= '{1}'".format(MKBFrom, MKBTo))
        elif MKBFrom == MKBTo:
            cond.append("d.MKB = '{0}'".format(MKBFrom))
        else:
            cond.append("d.MKB >= '{0}' AND d.MKB <= '{1}'".format(MKBTo, MKBFrom))

    ageCond = ''

    if params.get('addManAgeCondition', None) is not None and params.get('addWomanAgeCondition', None) is not None:
        ageCond = '((' + manCond + ') or (' + wumanCond + '))'
    elif params.get('addManAgeCondition', None) is not None:
        ageCond = manCond
    elif params.get('addWomanAgeCondition', None) is not None:
        ageCond = wumanCond
    else:
        ageCond = ''
#ymd end
    if len(ageCond) > 0:            #ymd
        cond.append(ageCond)        #ymd
    # Кассовый аппарат
    # (((Action.`payStatus` & 768) = 768))

    return db.joinAnd(cond)
