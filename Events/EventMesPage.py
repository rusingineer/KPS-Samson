# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QChar, QDate, QDateTime, QString, pyqtSignature, QModelIndex, SIGNAL, QVariant, pyqtSignal

from F090.F090EditDialog import CRBInfectionTableDialog
from library.AgeSelector import checkAgeSelector
from library.DialogBase import CConstructHelperMixin, CDialogBase
from library.DialogButtonBox import CApplyResetDialogButtonBox
from library.ICDCodeEdit import CICDCodeEditEx
from library.MemTableModel import CMemTableModel
from library.SortFilterProxyTableModel import CSortFilterProxyTableModel
from library.TableModel import CTableModel, CTextCol, CDoubleCol
from library.TableView import CTableView
from library.crbcombobox import CRBComboBox
from library.interchange import getRBComboBoxValue, setRBComboBoxValue
from library.ICDInDocTableCol import CICDExInDocTableCol
from library.CSG.CSGInDocTableCol import CCSGInDocTableCol
from library.CSG.CSGComboBox import defaultFilters
from library.InDocTable import CInDocTableModel, CIntInDocTableCol, CDateInDocTableCol, CCodeRefInDocTableCol, CSPR80SearchInDocTableCol
from library.ICDUtils import MKBwithoutSubclassification

from library.Utils import forceBool, forceInt, forceRef, forceString, forceDate, toVariant, forceDateTime, firstYearDay, \
    lastYearDay, calcAgeTuple

from Events.Utils import getEvenMesServiceMask, getEventMesSpecificationId, getEventMesCodeMask, getEventMesNameMask, \
    getEventProfileId, getEventCSGRequired, getEventMesRequired, getEventMesRequiredParams, getEventCSGCodeMask, \
    getEventSubCSGCodeMask, checkDiagnosis, getEventDiagnosis, getEventDuration, getEventAidTypeRegionalCode, \
    getEventTypeForm
from Reports.CheckMesDescription import showCheckMesDescription
from Reports.MesDescription import showMesDescription

from Accounting.Utils import getContractDescr, roundMath, getWeekProfile, isInterruptedCase

from Events.Ui_EventMesPage             import Ui_EventMesPageWidget
from Events.Ui_CheckMesParametersDialog import Ui_CheckMesParametersDialog


class CEventMesPage(QtGui.QWidget, CConstructHelperMixin, Ui_EventMesPageWidget):
    csgRowRemoved = pyqtSignal()
    csgRowAboutToBeRemoved = pyqtSignal(QtSql.QSqlRecord)
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.eventEditor = None

        self.addModels('CSGs', CCSGModel(self))
        self.addModels('CSGSubItems', CCSGSlaveModel(self))
        self.setupBtnCheckMes()

        self.setupUi(self)

        self.setFocusProxy(self.cmbMes)
        self.cmbMesSpecification.setTable('rbMesSpecification')
        self.cmbMesSpecification.setValue(1)
        self.setModels(self.tblCSGs, self.modelCSGs, self.selectionModelCSGs)
        self.setModels(self.tblCSGSubItems, self.modelCSGSubItems, self.selectionModelCSGSubItems)
        self.btnCheckMes.setMenu(self.mnuBtnCheckMes)
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            self.btnCheckMes.setVisible(False)
            self.btnShowMes.setVisible(False)
        self.eventId = None
        self.eventTypeId = None
        self.mesWidgets = [self.lblMes, self.cmbMes, self.lblMesSpecification, self.cmbMesSpecification, self.btnCheckMes, self.btnShowMes]
        self.csgWidgets = [self.grpCSG]
        self.tblCSGs.addPopupDelRow()
        # self.tblCSGs.addPopupDuplicateCurrentRow()
        self.tblCSGSubItems.addPopupDelRow()
        # self.tblCSGSubItems.addPopupDuplicateCurrentRow()
        self.tblCSGs.setDelRowsIsExposed(lambda rowsExp: not any(map(self.isExposed, rowsExp)))
        self.tblCSGSubItems.setDelRowsIsExposed(lambda rowsExp: not any(map(self.isExposed_sub, rowsExp)))
        # self.addObject('actCreateSomeCSGformepls', QtGui.QAction(u'Подобрать КСГ', self))
        # self.tblCSGs.addPopupAction(self.actCreateSomeCSGformepls)
        # self.connect(self.actCreateSomeCSGformepls, SIGNAL('triggered()'), self.on_actCreateSomeCSGformepls)
        # self.actCreateSomeCSGformepls.setEnabled(False)
        self.mesRequired = False
        self.mesRequiredParams = 0
        for w in self.mesWidgets:
            w.setEnabled(False)
        for w in self.csgWidgets:
            w.setEnabled(False)

        self.tblCSGs.verticalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)


    def isExposed(self, row):
        items = self.modelCSGs.items()
        if 0 <= row < len(items):
            item = items[row]
            return True if forceInt(item.value('payStatus')) != 0 else False
        return True

    def isExposed_sub(self, row):
        items = self.modelCSGSubItems.items()
        if 0 <= row < len(items):
            item = items[row]
            return True if forceInt(item.value('payStatus')) != 0 else False
        return True

    def protectFromEdit(self, isProtected):
        if self.mesRequired:
            editWidgets = [self.cmbMes, self.cmbMesSpecification]
            for widget in editWidgets:
                widget.setEnabled(not isProtected)


    def setupBtnCheckMes(self):
        self.addObject('mnuBtnCheckMes', QtGui.QMenu(self))
        self.addObject('actDecarationColor', QtGui.QAction(u'Оформление в цвете', self))
        self.addObject('actDecarationNoColor', QtGui.QAction(u'Оформление без цвета', self))
        self.mnuBtnCheckMes.addAction(self.actDecarationColor)
        self.mnuBtnCheckMes.addAction(self.actDecarationNoColor)


    def showCheckMes(self, decarationColor):
        mesId = self.cmbMes.value()
        if mesId:
            dialog = CCheckMesParametersDialog(self)
            #dialog.setParams(params)
            if not dialog.exec_():
                return
            params = dialog.params()
            showCheckMesDescription(self, mesId, decarationColor, params)


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor
        self.modelCSGs.csgCol.setEventEditor(eventEditor)
        self.modelCSGSubItems.csgCol.setEventEditor(eventEditor)
        # if hasattr(self.eventEditor,  'modelPreliminaryDiagnostics') and hasattr(self.eventEditor,  'tabMisc'):
        #     self.actCreateSomeCSGformepls.setEnabled(True)


    def setRecord(self, record):
        setRBComboBoxValue(self.cmbMes, record, 'MES_id')
        setRBComboBoxValue(self.cmbMesSpecification, record, 'mesSpecification_id')
        self.eventId = forceRef(record.value('id'))
        self.cmbMes.setExecDate(forceDate(record.value('execDate')))
        self.modelCSGs.loadItems(self.eventId)
        for record in self.modelCSGs.items()[::-1]:
            self.modelCSGSubItems.setMasterRecord(record)
        tabs = {}
        if hasattr(self.eventEditor, 'tabStatus'):
            tabs[0] = self.eventEditor.tabStatus
        if hasattr(self.eventEditor, 'tabDiagnostic'):
            tabs[1] = self.eventEditor.tabDiagnostic
        if hasattr(self.eventEditor, 'tabCure'):
            tabs[2] = self.eventEditor.tabCure
        if hasattr(self.eventEditor, 'tabMisc'):
            tabs[3] = self.eventEditor.tabMisc
        for row, tab in tabs.items():
            tab.cmbCSG.setItems()


    def setEventTypeId(self, eventTypeId):
        self.eventTypeId = eventTypeId
        self.cmbMes.setEventProfile(getEventProfileId(eventTypeId))
        self.cmbMes.setMESCodeTemplate(getEventMesCodeMask(eventTypeId))
        self.cmbMes.setMESNameTemplate(getEventMesNameMask(eventTypeId))
        self.cmbMes.setEventTypeId(eventTypeId)
        self.modelCSGs.setCsgCodeMask(getEventCSGCodeMask(eventTypeId))
        self.modelCSGSubItems.setSubCsgCodeMask(getEventSubCSGCodeMask(eventTypeId))
        self.cmbMesSpecification.setValue(getEventMesSpecificationId(eventTypeId))
        self.setMESServiceTemplate(eventTypeId)
        csgRequired = getEventCSGRequired(eventTypeId)
        self.mesRequired = getEventMesRequired(eventTypeId)
        self.mesRequiredParams = getEventMesRequiredParams(eventTypeId)
        if csgRequired:
            for w in self.csgWidgets:
                w.setEnabled(True)
        if self.mesRequired:
            for w in self.mesWidgets:
                w.setEnabled(True)
        
    def setContractId(self, contractId):
        self.cmbMes.setContractId(contractId)
        
    def setExecDate(self, execDate):
        self.cmbMes.setExecDate(execDate)


    def setClientId(self, clientId):
        pass


    def setMESServiceTemplate(self, eventTypeId):
        servicesCodeList = self.eventEditor.getServiceActionCode()
        # Для КК передаем все коды услуг
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            domainServicesCodeList = servicesCodeList
        else:  
            domainServicesCodeList = []
            domainRList = self.parseMesServiceMask(getEvenMesServiceMask(eventTypeId))  
            for domainR in domainRList:
                for servicesCode in servicesCodeList:
                    if domainR in servicesCode and servicesCode not in domainServicesCodeList:
                       domainServicesCodeList.append(servicesCode)
        self.cmbMes.setMESServiceTemplate(domainServicesCodeList)
        self.modelCSGs.setCsgServicesTemplate(domainServicesCodeList)


    def setAdditionalCriteria(self, criteriaList):
        self.criteriaList = criteriaList
        self.cmbMes.setAdditionalCriteria(self.criteriaList)


    def setFractions(self, fractions):
        self.fractions = fractions
        self.cmbMes.setFractions(self.fractions)
        self.modelCSGs.setCsgFilterFractions(self.fractions)


    def parseMesServiceMask(self, mesServiceTemplate):
        domainRList = u''
        if mesServiceTemplate:
            domainAll = QString(mesServiceTemplate)
            domainList = domainAll.split(';')
            if len(domainList) > 0:
                domainR = domainList[0]
                if len(domainR) > 0:
                    if u'*' in domainR:
                        index = domainR.indexOf(u'*', 0, Qt.CaseInsensitive)
                        if domainR[index - 1] != u',':
                            domainR.replace(QString('*'), QString(','))
                        else:
                            domainR.remove(QChar('*'), Qt.CaseInsensitive)
                    domainRList = domainR.split(',')
                    for i, domainR in enumerate(domainRList):
                        domainR.remove(QChar('\''), Qt.CaseInsensitive)
                        domainRList[i] = domainR
        return  domainRList


    def setEventBegDate(self, date):
        self.cmbMes.setEventBegDate(date)
        self.modelCSGs.setCsgFilterEventBegDate(date)


    def setClientInfo(self, baseDate, clientSex, clientBirthDate, clientAge, clientAgePrevYearEnd, clientAgeCurrYearEnd):
        self.cmbMes.setClientSex(clientSex)
        self.cmbMes.setClientAge(baseDate, clientBirthDate, clientAge, clientAgePrevYearEnd, clientAgeCurrYearEnd)
        self.modelCSGs.setCsgFilterClientBirthDate(clientBirthDate)
        self.modelCSGs.setCsgFilterClientSex(clientSex)


    def setSpeciality(self, specialityId):
        self.cmbMes.setSpeciality(specialityId)


    def getRecord(self, record):
        getRBComboBoxValue(self.cmbMes, record, 'MES_id')
        getRBComboBoxValue(self.cmbMesSpecification, record, 'mesSpecification_id')


    def save(self, eventId):
        self.modelCSGs.saveItems(eventId)
    
    def checkDataEntered(self):
        haveToCheck = False
        finalMKBList = list()
        for _ in self.eventEditor.modelFinalDiagnostics._items:
            diagType = forceString(QtGui.qApp.db.translate('rbDiagnosisType', 'id', forceString(_.value('diagnosisType_id')), 'code'))
            if diagType in ('1', '2'):
                finalMKBList.append(forceString(_.value('MKB')))
        csgContainsFinalDiag = False
        
        for record in self.modelCSGs.items():
            if forceString(record.value('CSGCode')):
                haveToCheck = True
                break
        haveToCheckPeriods = u'мэса нет' in unicode(self.cmbMes.currentText()).lower() or not bool(self.cmbMes.currentIndex())
        if haveToCheck:
            mainRecords = []
            eventBegDate = self.eventEditor.edtBegDate.date()
            eventEndDate = self.eventEditor.edtEndDate.date()
            for row, rec in enumerate(self.modelCSGs.items()):
                begDate = forceDate(rec.value('begDate'))
                endDate = forceDate(rec.value('endDate'))
                csg = forceString(rec.value('CSGCode'))

                if csg and begDate and begDate < eventBegDate:
                    self.eventEditor.checkValueMessage(
                        u'Дата начала КСГ ({}) ранее даты начала случая лечения.'
                        .format(csg),
                        False,
                        self.tblCSGs, row, 1
                    )
                    return False

                if csg and endDate and eventEndDate and endDate > eventEndDate:
                    self.eventEditor.checkValueMessage(
                        u'Дата окончания КСГ ({}) позже даты окончания случая лечения.'
                        .format(csg),
                        False,
                        self.tblCSGs, row, 2
                    )
                    return False

                if forceString(rec.value('MKB')) in finalMKBList and not csgContainsFinalDiag:
                    # заключительный диагноз вкладки стат. учет соответствует хотя бы одному диагнозу КСГ
                    csgContainsFinalDiag = True
                    

                if csg not in ('G26st36.009', 'G26st36.025', 'G26st36.026', 'G26st36.050', 'G26st36.051', 'G26st36.052', 'G26st36.053', 'G26st36.054'):
                    # тт 4478 - исключить ксг, которые подаются параллельно с основным
                    mainRecords.append((row, rec, begDate, endDate))
            if not csgContainsFinalDiag and eventEndDate:
                self.eventEditor.checkValueMessage(
                    u'Заключительный диагноз вкладки Стат. учет не соответствует ни одному диагнозу КСГ', False,
                    self.tblCSGs
                )
                return False

            mainRecords.sort(key=lambda x: x[2])
            prevEnd = None
            for row, rec, begDate, endDate in mainRecords:
                if haveToCheckPeriods and prevEnd is not None and begDate != prevEnd:
                    self.eventEditor.checkValueMessage(
                        u'Начало периода КСГ должно совпадать с концом предыдущего ({})'
                        .format(forceString(prevEnd)),
                        False,
                        self.tblCSGs, row, 1
                    )
                    return False
                prevEnd = endDate
        return True
        


    def setMKB(self, MKB):
        self.cmbMes.setMKB(MKB)
        self.modelCSGs.setCsgFilterMKB(MKB)
        self.modelCSGSubItems.setCsgFilterMKB(MKB)


    def setAssociatedMKB(self, MKB):
        self.cmbMes.setAssociatedMKB(MKB)


    def setComplicationMKB(self, MKB):
        self.cmbMes.setComplicationMKB(MKB)


    def setMKBEx(self, MKBEx):
        self.cmbMes.setMKBEx(MKBEx)

    def checkCsg(self):
        result = True
        isMesEmpty = forceString(self.cmbMes.code()) in ('', '0')
        is003Form = getEventTypeForm(self.eventEditor.eventTypeId) == u'003'
        financeCode = forceString(QtGui.qApp.db.translate('rbFinance', 'id', self.eventEditor.eventFinanceId, 'code'))
        isStac = getEventAidTypeRegionalCode(self.eventEditor.eventTypeId) in ('11', '12', '301', '302', '41', '42', '51', '52', '511', '522', '43')
        if isMesEmpty and financeCode == '2' and is003Form and isStac:
            result = len(self.modelCSGs.items()) > 0 or self.eventEditor.checkInputMessage(u'хотя бы один КСГ!', False, self.tblCSGs)
        result = result and self.modelCSGs.checkData()
        # result = result and self.checkActualMKB(self.modelCSGs, self.tblCSGs, 1)
        # result = result and self.checkActualMKB(self.modelCSGSubItems, self.tblCSGSubItems, 0)
        # result = result and self.checkDates(self.modelCSGs, self.tblCSGs, 1)
        # result = result and self.checkDates(self.modelCSGSubItems, self.tblCSGSubItems, 0)
        return result

    def checkActualMKB(self, model, tbl, addPos):
        for row, record in enumerate(model.items()):
            MKB = forceString(record.value('MKB'))
            if MKB:
                db = QtGui.qApp.db
                tableMKB = db.table('MKB')
                cond = [tableMKB['DiagID'].eq(MKBwithoutSubclassification(MKB))]
                cond.append(db.joinOr(
                    [tableMKB['endDate'].isNull(), tableMKB['endDate'].dateGe(forceDate(record.value('endDate')))]))
                recordMKB = db.getRecordEx(tableMKB, [tableMKB['DiagID']], cond)
                if not (recordMKB and forceString(recordMKB.value('DiagID')) == MKBwithoutSubclassification(MKB)):
                    self.eventEditor.checkValueMessage(u'Необходимо указать правильный МКБ ', False, tbl, row,
                                                       2 + addPos)
                    return False
        return True

    def checkDates(self, model, tbl, addPos):
        for row, record in enumerate(model.items()):
            begDate = forceDate(record.value('begDate'))
            endDate = forceDate(record.value('endDate'))
            if begDate > QDate.currentDate():
                self.eventEditor.checkValueMessage(u'Дата начала не может быть больше текущей ', False, tbl, row,
                                                   0 + addPos)
                return False
            if begDate > endDate:
                self.eventEditor.checkValueMessage(u'Дата начала не может быть больше даты окончания ', False, tbl, row,
                                                   0 + addPos)
                return False
            if endDate > QDate.currentDate():
                self.eventEditor.checkValueMessage(u'Дата окончания не может быть больше текущей ', False, tbl, row,
                                                   1 + addPos)
                return False
        return True

    def checkMesAndSpecification(self):
        if self.eventEditor.mesRequired and self.eventEditor.mesRequiredParams == 0:
            result = self.cmbMes.value() or self.eventEditor.checkInputMessage(u'МЭС', False, self.cmbMes)
            result = result and (self.cmbMesSpecification.value() or self.eventEditor.checkInputMessage(u'Особенности выполнения МЭС', False, self.cmbMesSpecification))
            return result
        return True


    def chechMesDuration(self):
        result = True
        mesId = self.cmbMes.value()
        if mesId:
            db = QtGui.qApp.db
            mesRecord = db.getRecord('mes.MES', '*', mesId)
            minDuration = forceInt(mesRecord.value('minDuration'))
            maxDuration = forceInt(mesRecord.value('maxDuration'))
            eventSetDateTime = self.eventEditor.eventSetDateTime
            eventDate = self.eventEditor.eventDate
            begDateEvent = eventSetDateTime if isinstance(eventSetDateTime, QDateTime) else (QDateTime(eventSetDateTime) if eventDate  else QDateTime())
            endDateEvent = eventDate if isinstance(eventDate, QDateTime) else (QDateTime(eventDate) if eventDate  else QDateTime())
            currentDateTime = QDateTime.currentDateTime()
            if not endDateEvent:
                endDateEvent = currentDateTime
            begDate = begDateEvent.date()
            endDate = endDateEvent.date()
            if endDate != begDate:
                avgDurationDay = begDate.daysTo(endDate) + 1
            else:
                avgDurationDay = 1
            result = (avgDurationDay >= minDuration or avgDurationDay >= maxDuration)
        return result


    def on_actCreateSomeCSGformepls(self):
        db = QtGui.qApp.db
        diags = self.eventEditor.modelFinalDiagnostics._items
        personTable = db.table('Person')
        mkbEx = None
        recordList = {}
        for (record, action) in self.eventEditor.tabMisc.modelAPActions._items:
            if action.getType().flatCode == 'moving':
                begDate = forceDateTime(record.value('begDate'))
                endDate = forceDateTime(record.value('endDate'))
                if endDate.isNull():
                    endDate = forceDateTime(record.value('plannedEndDate'))
                duration = begDate.daysTo(endDate)
                person_id = forceRef(record.value('person_id'))
                personIdList = db.getIdList(personTable, where=personTable['orgStructure_id'].signEx('=', '(select orgStructure_id from Person as P where id = %i)'%person_id)) if person_id else []
                mkb = forceString(record.value('MKB'))
                mkbEx = forceString(record.value('MKBEx'))
                if not mkbEx:
                    for diag in diags:
                        if forceInt(diag.value('diagnosisType_id')) == 1:
                            mkbEx = forceString(diag.value('MKBEx'))
                            break
                if not mkb:
                    for diag in diags:
                        if forceInt(diag.value('diagnosisType_id')) == 1:
                            mkb = forceString(diag.value('MKB'))
                            break
                if not mkb:
                    for diag in diags:
                        if forceRef(diag.value('person_id')) == person_id and forceInt(diag.value('diagnosisType_id')) == 2:
                            mkb = forceString(diag.value('MKB'))
                            break
                if not mkb:
                    for diag in diags:
                        if forceRef(diag.value('person_id')) in personIdList and forceInt(diag.value('diagnosisType_id')) == 2:
                            mkb = forceString(diag.value('MKB'))
                            break
                if begDate and endDate:
                    addNew = True
                    for existsCSGRecord in self.modelCSGs._items:
                        exbegDate = forceDateTime(existsCSGRecord.value('begDate'))
                        exendDate = forceDateTime(existsCSGRecord.value('endDate'))
                        exMKB = forceString(existsCSGRecord.value('MKB'))
                        if not exbegDate:
                            exbegDate = QDate.currentDate()
                        if not exendDate:
                            exendDate = QDate.currentDate()
                        if len(exMKB)>0 and len(mkb)>0 and exMKB[0] == mkb[0]: # надеюсь они отсортированы по датам
                            existsCSGRecord.setValue('endDate', QVariant(endDate))
                            self.eventEditor.tabMisc.cmbCSG.mapActionToCSG[record] = existsCSGRecord
                            tabs = []
                            if self.eventEditor and hasattr(self.eventEditor, 'tabCure'):
                                tabs.append(self.eventEditor.tabCure)
                            if self.eventEditor and hasattr(self.eventEditor, 'tabDiagnostic'):
                                tabs.append(self.eventEditor.tabDiagnostic)
                            for tab in tabs:
                                for (cureRecord, cureAction) in tab.modelAPActions._items:
                                    if cureAction._actionType.nomenclativeServiceId:
                                        cureEndDT = forceDateTime(cureRecord.value('endDate'))
                                        if cureEndDT >= begDate and cureEndDT <= endDate:
                                            tab.cmbCSG.mapActionToCSG[cureRecord] = existsCSGRecord
                            filter = {'duration': duration, 'MKBEx': mkbEx}
                            code, cost = self.modelCSGs.csgCol.getMostExpensiveCSG(existsCSGRecord, filter)
                            existsCSGRecord.setValue('CSGCode', QVariant(code))
                            addNew = False
                            break
                        if begDate < exendDate and endDate > exbegDate:
                            addNew = False
                            break
                    if addNew:
                        newCsg = self.modelCSGs.getEmptyRecord()
                        newCsg.setValue('begDate', toVariant(begDate))
                        newCsg.setValue('endDate', toVariant(endDate))
                        if mkb:
                            newCsg.setValue('MKB', toVariant(mkb))
                        self.eventEditor.tabMisc.cmbCSG.mapActionToCSG[record] = newCsg
                        tabs = []
                        if self.eventEditor and hasattr(self.eventEditor, 'tabCure'):
                            tabs.append(self.eventEditor.tabCure)
                        if self.eventEditor and hasattr(self.eventEditor, 'tabDiagnostic'):
                            tabs.append(self.eventEditor.tabDiagnostic)
                        for tab in tabs:
                            for (cureRecord, cureAction) in tab.modelAPActions._items:
                                if (cureAction.getType().serviceType in [0,3,4]) and cureAction._actionType.nomenclativeServiceId:
                                    cureEndDT = forceDateTime(cureRecord.value('endDate'))
                                    if cureEndDT >= begDate and cureEndDT <= endDate:
                                        tab.cmbCSG.mapActionToCSG[cureRecord] = newCsg
                        filter = {'duration': duration, 'MKBEx': mkbEx}
                        code, cost = self.modelCSGs.csgCol.getMostExpensiveCSG(newCsg, filter)
                        newCsg.setValue('CSGCode', QVariant(code))
                        self.modelCSGs.addRecord(newCsg)
                        orgStructure_id = action[u'Отделение пребывания']
                        recordList.setdefault(orgStructure_id, []).append((mkb,  record))
#        for mkbList in recordList:
#            if len(mkbList) > 1:
#                coolestMkb = mkbList[0][0]
        self.eventEditor.tabMisc.cmbCSG.setItems()
        self.eventEditor.tabCure.cmbCSG.setItems()
        self.eventEditor.tabMisc.updateCmbCSG()
        self.eventEditor.tabCure.updateCmbCSG()

    @pyqtSignature('')
    def on_mnuBtnCheckMes_aboutToShow(self):
        self.actDecarationColor.setEnabled(True)
        self.actDecarationNoColor.setEnabled(True)


    @pyqtSignature('')
    def on_actDecarationColor_triggered(self):
        self.showCheckMes(0)


    @pyqtSignature('')
    def on_actDecarationNoColor_triggered(self):
        self.showCheckMes(1)


    @pyqtSignature('')
    def on_btnShowMes_pressed(self):
        mesId = self.cmbMes.value()
        if mesId:
            showMesDescription(self, mesId)


    @pyqtSignature('')
    def on_btnOpenSpr69_pressed(self):
        dialog = CSpr69TableDialog(self, 'soc_spr69')
        dialog.setWindowTitle(u'Просмотрщик SPR69')
        dialog.exec_()


    @pyqtSignature('int')
    def on_cmbMes_currentIndexChanged(self, index):
        mesCode = u''
        mesId = self.cmbMes.value()
        if mesId:
            self.btnCheckMes.setEnabled(forceBool(mesId))
            self.btnShowMes.setEnabled(forceBool(mesId))
            mesCode = u'МЭС события: ' + self.cmbMes.code()
        if self.eventEditor:
            self.eventEditor.setMesInfo(mesCode)


    @pyqtSignature('QModelIndex')
    def on_tblCSGs_doubleClicked(self, index):
        if index.column() == 6: # CSG
            self.modelCSGs.setCsgFilterMKB(forceString(
                self.modelCSGs.value(index.row(),'MKB')))
            self.modelCSGs.setCsgFilterAssociatedMKB(forceString(
                self.modelCSGs.value(index.row(),'associatedMKB')))
            self.modelCSGs.setCsgFilterComplicationMKB(forceString(
                self.modelCSGs.value(index.row(),'complicationMKB')))
            self.modelCSGs.setCsgFilterEventProfileId(forceRef(
                self.modelCSGs.value(index.row(),'eventProfile_id')))

            self.modelCSGs.setCsgFilterKrit(forceRef(
                self.modelCSGs.value(index.row(),'krit')))

            self.modelCSGs.setCsgFilterBegDate(forceDate(
                self.modelCSGs.value(index.row(),'begDate')))
            self.modelCSGs.setCsgFilterEndDate(forceDate(
                self.modelCSGs.value(index.row(),'endDate')))



    @pyqtSignature('QModelIndex')
    def on_tblCSGs_clicked(self, index):
        if index.column() == 6: # CSG
            self.modelCSGs.setCsgFilterMKB(forceString(
                self.modelCSGs.value(index.row(),'MKB')))
            self.modelCSGs.setCsgFilterAssociatedMKB(forceString(
                self.modelCSGs.value(index.row(),'associatedMKB')))
            self.modelCSGs.setCsgFilterComplicationMKB(forceString(
                self.modelCSGs.value(index.row(),'complicationMKB')))
            self.modelCSGs.setCsgFilterEventProfileId(forceRef(
                self.modelCSGs.value(index.row(),'eventProfile_id')))

            self.modelCSGs.setCsgFilterKrit(forceRef(
                self.modelCSGs.value(index.row(),'krit')))

            self.modelCSGs.setCsgFilterBegDate(forceDate(
                self.modelCSGs.value(index.row(),'begDate')))
            self.modelCSGs.setCsgFilterEndDate(forceDate(
                self.modelCSGs.value(index.row(),'endDate')))

        csgCode = forceString(self.modelCSGs.value(index.row(),'CSGCode'))
        if csgCode and self.eventEditor.tabNotes.chkIsClosed.isChecked():
            msgTxt = csgCode + u' | '
            msgTxt += forceString(self.modelCSGs.csgNameCol.toString(csgCode, None))
            calcSum = self.calcCSGSum(index, csgCode)
            msgTxt += u', расчётная итоговая стоимость: {0}'.format(calcSum)
            self.eventEditor.statusBar.showMessage(msgTxt)

    def calcCSGSum(self, index, csgCode):
        # расчёт стоимости ксг почти как в CAccountBuilder.exposeCsg23()
        db = QtGui.qApp.db

        def isTariffApplicable(tariff, eventId, cureMethodId, resultId, mesLevel, tariffCategoryId, date, actualMKB=''):
            if tariff.tariffCategoryId and tariff.tariffCategoryId != tariffCategoryId:
                return False
            if not tariff.dateInRange(date):
                return False
            if tariff.cureMethodId and cureMethodId and tariff.cureMethodId != cureMethodId:
                return False
            if tariff.resultId and tariff.resultId != resultId:
                return False
            if tariff.mesStatus and ((tariff.mesStatus == 2) != (mesLevel == 2)):
                return False

            sex = tariff.sex
            ageSelector = tariff.ageSelector
            eventTypeId = tariff.eventTypeId
            if sex or ageSelector or eventTypeId:
                if eventTypeId and eventTypeId != self.eventEditor.eventTypeId:
                    return False
                if not date:
                    date = self.eventEditor.eventDate
                if sex or ageSelector:
                    clientId = self.eventEditor.clientId
                    clientMesInfo = self.eventEditor.getClientMesInfo() if clientId else None
                    if clientRecord:
                        clientSex = clientMesInfo[5]
                        if sex and sex != clientSex:
                            return False
                        if ageSelector:
                            if tariff.controlPeriod == 1:
                                date = firstYearDay(date)
                            elif tariff.controlPeriod == 2:
                                date = lastYearDay(date)
                            else:
                                pass

                            clientBirthDate = clientMesInfo[1]
                            clientAge = calcAgeTuple(clientBirthDate, date)
                            if not clientAge:
                                clientAge = (0, 0, 0, 0)
                            if not checkAgeSelector(ageSelector, clientAge):
                                return False
                    else:
                        return False
            if tariff.MKB:
                if actualMKB:
                    MKB = actualMKB
                else:
                    eventMKB = getEventDiagnosis(eventId)
                    MKB = eventMKB
                if not tariff.matchMKB(MKB or ''):
                    return False
            return True

        def getOperationCount(eventId, serviceId, eventEndDate, mkb):
            tableKSG = db.table('rbService')
            # tableMKB = db.table('Diagnosis')
            tableS69 = db.table('soc_spr69')
            tableS82 = db.table('soc_spr82')
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            tableRBService = db.table('rbService').alias('s18')

            # table = tableKSG.leftJoin(tableMKB, 'Diagnosis.id = getEventDiagnosis(%d)' % eventId)
            table = tableKSG.leftJoin(tableS69, u"""rbService.infis = soc_spr69.ksgkusl 
                    and (soc_spr69.mkb = '%s' or soc_spr69.mkb is null or (soc_spr69.mkb = 'C.' and substr('%s', 1, 1) = 'C') 
                    or (soc_spr69.mkb = 'I.' and substr('%s', 1, 1) = 'I')
                    or (soc_spr69.mkb = 'C00-C80' and '%s' between 'C00' and 'C80.9')) and soc_spr69.kusl is not null""" % mkb)
            table = table.leftJoin(tableAction, 'Action.event_id = %d' % eventId)
            table = table.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            table = table.leftJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
            cond = [tableKSG['id'].eq(serviceId),
                    tableAction['deleted'].eq(0),
                    tableAction['status'].eq(2),
                    tableAction['event_id'].eq(eventId),
                    tableRBService['infis'].eq(tableS69['kusl']),
                    "s18.id is not null"
                    ]
            table = table.leftJoin(tableS82, tableS82['CODE'].eq(tableS69['ksgkusl']))
            cond.append(tableS82['DATN'].dateLe(eventEndDate))
            cond.append(db.joinOr([tableS82['DATO'].dateGe(eventEndDate), tableS82['DATO'].isNull()]))
            cond.append(tableS82['CODE'].isNotNull())
            result = db.getCount(table, where=cond)
            return result

        sum = 0
        serviceId    = forceRef(db.translate('rbService', 'infis', csgCode, 'id'))
        eventId      = self.eventId
        eventTypeId  = self.eventEditor.eventTypeId
        eventEndDate = self.eventEditor.eventDate
        mkbCode      = forceString(self.modelCSGs.value(index.row(), 'MKB'))
        mkbAssocCode = forceString(self.modelCSGs.value(index.row(), 'associatedMKB'))
        mkbComplCode = forceString(self.modelCSGs.value(index.row(), 'complicationMKB'))
        mesLevel     = forceInt(db.translate('rbMesSpecification', 'id', self.cmbMesSpecification.value(), 'level'))
        csgBegDate   = forceDate(self.modelCSGs.value(index.row(), 'begDate'))
        csgEndDate   = forceDate(self.modelCSGs.value(index.row(), 'endDate'))
        cureMethodId = forceRef(self.eventEditor.getCureMethodId())
        resultId     = self.eventEditor.cmbResult.value()
        contractId   = self.eventEditor.cmbContract.value()
        tariffCategoryId = self.eventEditor.getPersonTariffCategoryId(self.eventEditor.personId)
        contractDescr = getContractDescr(contractId)
        tariffList = contractDescr.tariffEventByMES.get((None, serviceId), None)
        if tariffList:
            for tariff in tariffList:
                if isTariffApplicable(tariff, eventId, cureMethodId, resultId, mesLevel, tariffCategoryId, csgEndDate, actualMKB=mkbCode):
                    coefficient, usedCoefficients = 1.0, None
                    price = tariff.price
                    amount = 1.0
                    medicalAidTypeId = forceRef(db.translate('EventType', 'id', eventTypeId, 'medicalAidType_id'))
                    medicalAidType = forceString(db.translate('rbMedicalAidType', 'id', medicalAidTypeId, 'regionalCode'))
                    csgKritId = forceRef(self.modelCSGs.value(index.row(), 'krit'))
                    if medicalAidType in ('11', '12', '301', '302') and csgCode[3:] in ['st36.013', 'st36.014', 'st36.015'] and eventEndDate >= QDate(2024, 11, 1):
                        minDuration = 0
                        amtCode = None
                        if csgKritId:
                            amtCode = forceString(db.translate('soc_spr80', 'id', csgKritId, 'code'))
                        if amtCode in ['amt02', 'amt04','amt05','amt07','amt08','amt09','amt10','amt12','amt13','amt14','amt15']:
                            minDuration = 5
                        elif amtCode in ['amt01', 'amt03','amt06','amt11']:
                            minDuration = 10
                        eventWeekProfile = getWeekProfile(forceInt(db.getRecord('EventType', 'weekProfileCode', eventTypeId).value('weekProfileCode')))
                        duration = getEventDuration(csgBegDate, csgEndDate, eventWeekProfile, eventTypeId)
                        if duration < minDuration:
                            if duration >= 3:
                                price = roundMath(price * contractDescr.coefficients[0, 0][u'ПРЕРВДЛ4'][eventEndDate], 2)
                            else:
                                price = roundMath(price * contractDescr.coefficients[0, 0][u'ПРЕРВДЛ3'][eventEndDate], 2)

                    elif csgCode[3:] in ['st02.003', 'st02.004'] and eventEndDate >= QDate(2025, 6, 1):
                        ishodOb = isInterruptedCase(eventId)
                        minDuration = 1
                        eventWeekProfile = getWeekProfile(forceInt(db.getRecord('EventType', 'weekProfileCode', eventTypeId).value('weekProfileCode')))
                        duration = getEventDuration(csgBegDate, csgEndDate, eventWeekProfile, eventTypeId)

                        if (minDuration > 1 and duration <= minDuration
                                or (QDate(2023, 2, 1) <= eventEndDate < QDate(2025, 1, 1)
                                    and minDuration == 1 and duration <= 3
                                    and ishodOb in ['103', '203', '105', '205', '107', '207', '108', '208', '110'])
                                or (QDate(2025, 1, 1) <= eventEndDate < QDate(2025, 6, 1)
                                    and minDuration == 1 and duration <= 3
                                    and ishodOb in ['102', '202', '103', '203', '105', '205', '107', '207', '108', '208', '110'])
                                or (eventEndDate >= QDate(2025, 6, 1)
                                    and minDuration == 1 and duration <= 3
                                    and ishodOb in ['102', '202', '103', '203', '104', '105', '205', '107', '207', '108', '208', '110'])):
                            if getOperationCount(eventId, tariff.serviceId, eventEndDate, mkbCode) > 0 or csgCode[3:] == 'st29.007':
                                price = roundMath(price * contractDescr.coefficients[0, 0][u'ПРЕРВДЛ3ОПЕР'][eventEndDate], 2)
                            else:
                                price = roundMath(price * contractDescr.coefficients[0, 0][u'ПРЕРВДЛ3'][eventEndDate], 2)
                        # оплата прерванных случаев свыше 3-х дней
                        elif (duration > minDuration and ishodOb and minDuration > 1
                              or (QDate(2023, 2, 1) <= eventEndDate < QDate(2025, 1, 1)
                                  and minDuration == 1
                                  and ishodOb in ['103', '203', '105', '205', '107', '207', '108', '208', '110'])
                              or (QDate(2025, 1, 1) <= eventEndDate < QDate(2025, 6, 1)
                                  and minDuration == 1
                                  and ishodOb in ['102', '202', '103', '203', '105', '205', '107', '207', '108', '208', '110'])
                              or (eventEndDate >= QDate(2025, 6, 1)
                                  and minDuration == 1
                                  and ishodOb in ['102', '202', '103', '203', '104', '105', '205', '107', '207', '108', '208', '110'])):
                            if getOperationCount(eventId, tariff.serviceId, eventEndDate, mkbCode) > 0 or csgCode[3:] == 'st29.007':
                                price = roundMath(price * contractDescr.coefficients[0, 0][u'ПРЕРВДЛ4ОПЕР'][eventEndDate], 2)
                            else:
                                price = roundMath(price * contractDescr.coefficients[0, 0][u'ПРЕРВДЛ4'][eventEndDate], 2)

                    sum = round(price*amount*coefficient, 2)
                    return sum

        return sum


    @pyqtSignature('QModelIndex, int, int')
    def on_modelCSGs_rowsRemoved(self, index1, start, end):
        self.csgRowRemoved.emit()

    @pyqtSignature('QModelIndex, int, int')
    def on_modelCSGs_rowsAboutToBeRemoved(self, index1, start, end):
        record = self.modelCSGs.items()[start]
        self.modelCSGSubItems.masterRowRemove(record)
        self.csgRowAboutToBeRemoved.emit(record)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelCSGs_dataChanged(self, index1, index2):
        row = index1.row()
        if row == len(self.modelCSGs.items())-1:
            self.modelCSGSubItems.setMasterRecord(self.modelCSGs.items()[row])
            self.tblCSGSubItems.setEnabled(False)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelCSGs_currentRowChanged(self, current, previous):
        row = current.row()
        if row < len(self.modelCSGs.items()):
            currentCSGRecord = self.modelCSGs.items()[current.row()]
            self.modelCSGSubItems.setMasterRecord(currentCSGRecord)
            self.tblCSGSubItems.setEnabled(False)
        else:
            self.modelCSGSubItems.setMasterRecord(None)
            self.tblCSGSubItems.setEnabled(False)


class CCheckMesParametersDialog(QtGui.QDialog, Ui_CheckMesParametersDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)


    def setParams(self, params):
        self.chkMandatoryServiceMes.setChecked(params.get('chkMandatoryServiceMes', False))
        self.chkServiceMes.setChecked(params.get('chkServiceMes', False))
        self.chkServiceNoMes.setChecked(params.get('chkServiceNoMes', False))
        self.chkMedicamentsSection.setChecked(params.get('chkMedicamentsSection', False))


    def params(self):
        result = {}
        result['chkMandatoryServiceMes'] = self.chkMandatoryServiceMes.isChecked()
        result['chkServiceMes'] = (self.chkServiceMes.isChecked() if self.chkServiceMes.isEnabled() else False)
        result['chkServiceNoMes'] = self.chkServiceNoMes.isChecked()
        result['chkMedicamentsSection'] = self.chkMedicamentsSection.isChecked()
        return result


class CCSGModel(CInDocTableModel):
    mkb_col = 3
    
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Event_CSG', 'id', 'master_id', parent)
        self._parent = parent
        csgFilter = defaultFilters
        if QtGui.qApp.getGlobalPreference('csgServiceFilter') == u'нет':
            csgFilter['csgServices'] = False
        self.csgCol = CCSGInDocTableCol( u'КСГ','CSGCode', csgFilter,         7)
        self.csgNameCol = CCodeRefInDocTableCol(u'Наименование КСГ', 'CSGCode', 45, 'rbService', showFields=CRBComboBox.showName)
        self.setFilter(self._table['parentCSG_id'].isNull())
        self.addExtCol(CIntInDocTableCol(u'№', 'seqNum', 5, canBeEmpty=False), QVariant.Int).setToolTip(
            u'Порядковый номер').setReadOnly(True)
        self.addCol(CDateInDocTableCol(  u'С',         'begDate',    15, canBeEmpty=False)).setToolTip(u'Дата начала')
        self.addCol(CDateInDocTableCol(  u'По',        'endDate',    15, canBeEmpty=False)).setToolTip(u'Дата окончания')
        self.addCol(CICDExInDocTableCol( u'МКБ',       'MKB',        7)).setToolTip(u'Код диагноза')
        self.addCol(CICDExInDocTableCol( u'Соп. МКБ',  'associatedMKB',        7)).setToolTip(u'Код диагноза сопутствующего заболевания')
        self.addCol(CICDExInDocTableCol( u'МКБ осл.',  'complicationMKB',        7)).setToolTip(u'Код диагноза осложнения')
        self.addHiddenCol('eventProfile_id')
        self.addCol(self.csgCol).setToolTip(u'Код КСГ')
        self.addCol(self.csgNameCol).setToolTip(u'Наименование КСГ').setReadOnly(True)
        self.addHiddenCol('amount')
        self.addCol(CSPR80SearchInDocTableCol(u'Доп. критерий', 'krit', 15, 'soc_spr80', parentModel=self)).setToolTip(u'Доп. классиф. критерий')
        self.addCol(CSPR80SearchInDocTableCol(u'Комбинированная схема', 'combSchema', 15, 'soc_spr80', parentModel=self)).setToolTip(u'Комбинированная схема для схем химиотерапии')
        self.addHiddenCol('csgSpecification_id')
        # self.addCol(CRBInDocTableCol(   u'Особенность выполнения', 'csgSpecification_id', 15, 'rbMesSpecification'))
        self.addHiddenCol('payStatus')


    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole or role == Qt.StatusTipRole:
            column = index.column()
            row = index.row()
            if 0 <= row < len(self.items()):
                col = self.cols()[column]
                fieldName = col.fieldName()
                if fieldName == 'seqNum':
                    return QVariant(row + 1)
        return CInDocTableModel.data(self, index, role)
    
    
    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self.items()) and column == self.mkb_col:
            newMKB = forceString(value)
            if not newMKB:
                pass
            else:
                acceptable = checkDiagnosis(self._parent, newMKB, None, None, self._parent.eventEditor.clientSex, self._parent.eventEditor.clientAge, self._parent.eventEditor.edtBegDate.date())
                if not acceptable:
                    return False
            value = toVariant(newMKB)
            result = CInDocTableModel.setData(self, index, value, role)
            return result
        return CInDocTableModel.setData(self, index, value, role)


    def checkData(self):
        tbl = self._parent.tblCSGs
        for row, record in enumerate(self.items()):
            begDate = forceDate(record.value('begDate'))
            endDate = forceDate(record.value('endDate'))
            if not begDate:
                self._parent.eventEditor.checkValueMessage(u'Должна быть указана дата начала для КСГ', False, tbl, row, 1)
                return False
            if not endDate:
                self._parent.eventEditor.checkValueMessage(u'Должна быть указана дата окончания для КСГ', False, tbl, row, 2)
                return False
            if begDate > endDate:
                self._parent.eventEditor.checkValueMessage(u'Дата начала не может быть больше даты окончания ', False, tbl, row, 1)
                return False
            if not forceString(record.value('MKB')):
                self._parent.eventEditor.checkValueMessage(u'Должен быть указан код МКБ основного заболевания для КСГ ', False, tbl, row, 3)
                return False
            if not forceString(record.value('CSGCode')):
                self._parent.eventEditor.checkValueMessage(u'Необходимо указать КСГ ', False, tbl, row, 6)
                return False
            # if not (forceDate(record.value('begDate')) and forceDate(record.value('endDate')) and forceString(record.value('MKB')) and forceString(record.value('CSGCode'))):
            #     return False
        return True


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.setValue('amount',  QVariant(1))
        return result


    def setCsgFilterEventBegDate(self, date):
        self.csgCol.setEventBegDate(date)


    def setCsgFilterClientBirthDate(self, date):
        self.csgCol.setClientBirthDate(date)


    def setCsgFilterClientSex(self, sex):
        self.csgCol.setClientSex(sex)


    def setCsgFilterMKB(self, MKB):
        self.csgCol.setMKB(MKB)


    def setCsgFilterAssociatedMKB(self, associatedMKB):
        self.csgCol.setAssociatedMKB(associatedMKB)


    def setCsgFilterComplicationMKB(self, complicationMKB):
        self.csgCol.setComplicationMKB(complicationMKB)


    def setCsgFilterEventProfileId(self, eventProfileId):
        self.csgCol.setEventProfileId(eventProfileId)


    def setCsgCodeMask(self, mask):
        self.csgCol.setCsgCodeMask(mask)


    def setCsgServicesTemplate(self, MESServiceTemplate):
        self.csgCol.setCsgServiceTemplate(MESServiceTemplate)


    def setCsgFilterKrit(self, kritId):
        self.csgCol.setKrit(kritId)


    def setCsgFilterFractions(self, fractions):
        self.csgCol.setFractions(fractions)


    def setCsgFilterBegDate(self, csgBegDate):
        self.csgCol.setCsgBegDate(csgBegDate)


    def setCsgFilterEndDate(self, csgEndDate):
        self.csgCol.setCsgEndDate(csgEndDate)


    def saveDependence(self, idx, id):
        record = self._items[idx]
        self._parent.modelCSGSubItems.saveItemsForRecord(record)


    def insertRecord(self, row, record):
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.insert(row, record)
        self.endInsertRows()
        self._parent.modelCSGSubItems.setMasterRecord(record)


    def createEditor(self, index, parent):
        column = index.column()
        row = index.row()
        editor = self._cols[column].createEditor(parent)
        if type(editor).__name__ == 'CCSGComboBox':
            if row < len(self._items):
                record = self._items[row]
                editor.setCSGRecord(record)
            else:
                editor.setCSGRecord(None)
        return editor


class CCSGSlaveModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Event_CSG', 'id', 'parentCSG_id', parent)
        self._parent = parent
        csgFilter = defaultFilters
        if QtGui.qApp.getGlobalPreference('csgServiceFilter') == u'нет':
            csgFilter['csgServices'] = False
        self.csgCol = CCSGInDocTableCol( u'КСГ','CSGCode', csgFilter, 7)
        self.addCol(CDateInDocTableCol( u'С',   'begDate',    15, canBeEmpty=False)).setToolTip(u'Дата начала')
        self.addCol(CDateInDocTableCol( u'По',  'endDate',    15, canBeEmpty=False)).setToolTip(u'Дата окончания')
        self.addCol(CICDExInDocTableCol( u'МКБ','MKB',        7)).setToolTip(u'Код диагноза')
        self.addCol(self.csgCol).setToolTip(u'Код КСГ')
        self.addCol(CIntInDocTableCol( u'Количество', 'amount', 10)).setToolTip(u'Количество')
        self.addHiddenCol('master_id')
        self.addHiddenCol('payStatus')
        self.mapRecordToItems = {}
        self.currentMasterRecord = None

    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.setValue('amount',  QVariant(1))
        return result

    def setMasterRecord(self, record):
        if record == self.currentMasterRecord:
            pass
        if not record:
            self.currentMasterRecord = None
            self._items = []
            self.reset()
            return
        self.currentMasterRecord = record
        if record in self.mapRecordToItems:
            self._items = self.mapRecordToItems[record]
            self.reset()
        else:
            masterId = forceRef(record.value('id'))
            if masterId:
                self.loadItems(masterId)
            else:
                self.mapRecordToItems[record] = []
                self._items = self.mapRecordToItems[record]
                self.reset()

    def saveItemsForRecord(self, record):
        if record in self.mapRecordToItems:
            self._items = self.mapRecordToItems[record]
            masterId = forceRef(record.value('id'))
            eventId = forceRef(record.value('master_id'))
            for item in self._items:
                item.setValue('master_id',  toVariant(eventId))
            self.saveItems(masterId)


    def setSubCsgCodeMask(self, mask):
        self.csgCol.setCsgCodeMask(mask)


    def setCsgFilterMKB(self, MKB):
        self.csgCol.setMKB(MKB)


    def loadItems(self, masterId):
        db = QtGui.qApp.db
        cols = []
        for col in self._cols:
            if not col.external():
                cols.append(col.fieldName())
        cols.append(self._idFieldName)
        cols.append(self._masterIdFieldName)
        if self._idxFieldName:
            cols.append(self._idxFieldName)
        for col in self._hiddenCols:
            cols.append(col)
        table = self._table
        filter = [table[self._masterIdFieldName].eq(masterId)]
        if self._filter:
            filter.append(self._filter)
        if table.hasField('deleted'):
            filter.append(table['deleted'].eq(0))
        if self._idxFieldName:
            order = [self._idxFieldName, self._idFieldName]
        else:
            order = [self._idFieldName]
        self.mapRecordToItems[self.currentMasterRecord] = db.getRecordList(table, cols, filter, order)
        if self._extColsPresent:
            extSqlFields = []
            for col in self._cols:
                if col.external():
                    fieldName = col.fieldName()
                    if fieldName not in cols:
                        extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))
            if extSqlFields:
                for item in self.mapRecordToItems[self.currentMasterRecord]:
                    for field in extSqlFields:
                        item.append(field)
        self._items = self.mapRecordToItems[self.currentMasterRecord]
        self.reset()

    def masterRowRemove(self, record):
        if record in self.mapRecordToItems:
            del self.mapRecordToItems[record]

    def createEditor(self, index, parent):
        column = index.column()
        row = index.row()
        editor = self._cols[column].createEditor(parent)
        if type(editor).__name__ == 'CCSGComboBox':
            record = self._items[row]
            editor.setCSGRecord(record)
        return editor


class CSpr69TableDialog(CDialogBase):
    def __init__(self, parent=None, tableName='', filter=''):
        CDialogBase.__init__(self, parent)
        self.setObjectName('СSpr69TableDialog')
        self.tableName = 'soc_spr69'
        self.filter = filter
        self.parent = parent

        self.createUI()

        self.edtFractions.setMinimum(0)
        self.edtFractions.setMaximum(200)
        self.edtFractions.setValue(0)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self.addModels('Spr69', CSpr69Model(self))
        self.proxyModel = CSortFilterProxyTableModel(self, self.modelSpr69)
        # скрыл, потому что вызывает предупреждение об ошибке назначения selectionModel
        # self.tbl69.setSelectionModel(self.selectionModelSpr69)
        self.tbl69.setSortingEnabled(True)
        self.tbl69.setModel(self.proxyModel)
        self.tbl69.show()


    def createUI(self):
        widgetAgeMKBChoice = QtGui.QWidget(self)
        layoutAgeMKBChoice = QtGui.QGridLayout(self)
        self.cmbMKBType = QtGui.QComboBox(self)
        self.cmbMKBType.clear()
        self.cmbMKBType.setMaxCount(3)
        self.cmbMKBType.addItem(u'заключительный')
        self.cmbMKBType.addItem(u'сопутствующий')
        self.cmbMKBType.addItem(u'осложнение')
        self.cmbMKBType.setMaximumWidth(170)
        self.cmbAge = QtGui.QComboBox(self)
        self.cmbAge.clear()
        self.cmbAge.setMaxCount(7)
        self.cmbAge.addItem(u'не учитывать')
        self.cmbAge.addItem(u'от 0 до 28 дней (или новорожденный)')
        self.cmbAge.addItem(u'от 29 дней до 90 дней')
        self.cmbAge.addItem(u'от 91 дня до 1 года')
        self.cmbAge.addItem(u'от 0 дней до 2 лет')
        self.cmbAge.addItem(u'от 0 дней до 18 лет')
        self.cmbAge.addItem(u'старше 18 лет')
        self.cmbAge.setMaximumWidth(170)
        layoutAgeMKBChoice.addWidget(QtGui.QLabel(u'Вид МКБ'), 0, 0)
        layoutAgeMKBChoice.addWidget(self.cmbMKBType, 0, 1)
        layoutAgeMKBChoice.addWidget(QtGui.QLabel(u'Возрастная категория'), 1, 0)
        layoutAgeMKBChoice.addWidget(self.cmbAge, 1, 1)
        self.edtFractions = QtGui.QSpinBox(self)
        self.edtFractions.setMaximumWidth(60)
        layoutAgeMKBChoice.addWidget(QtGui.QLabel(u'Кол-во фракций'), 2, 0)
        layoutAgeMKBChoice.addWidget(self.edtFractions, 2, 1)
        widgetAgeMKBChoice.setLayout(layoutAgeMKBChoice)

        widgetFilters = QtGui.QWidget(self)
        layoutFilters = QtGui.QGridLayout(self)
        self.edtMKBCode = CICDCodeEditEx(self)
        self.edtMKBCode.setMinimumWidth(70)
        self.edtMKBCode.setMaximumWidth(110)
        self.edtMKBName = QtGui.QLineEdit(self)
        self.edtMKBName.setMinimumWidth(160)
        layoutFilters.addWidget(QtGui.QLabel(u'МКБ:'), 0, 0)
        layoutFilters.addWidget(QtGui.QLabel(u'Код'), 0, 1)
        layoutFilters.addWidget(self.edtMKBCode, 0, 2)
        layoutFilters.addWidget(QtGui.QLabel(u'Наименование'), 0, 3)
        layoutFilters.addWidget(self.edtMKBName, 0, 4)

        self.edtKritCode = QtGui.QLineEdit(self)
        self.edtKritCode.setMinimumWidth(70)
        self.edtKritCode.setMaximumWidth(110)
        self.edtKritName = QtGui.QLineEdit(self)
        self.edtKritName.setMinimumWidth(160)
        layoutFilters.addWidget(QtGui.QLabel(u'Доп. критерий:'), 1, 0)
        layoutFilters.addWidget(QtGui.QLabel(u'Код'), 1, 1)
        layoutFilters.addWidget(self.edtKritCode, 1, 2)
        layoutFilters.addWidget(QtGui.QLabel(u'Наименование'), 1, 3)
        layoutFilters.addWidget(self.edtKritName, 1, 4)

        self.edtServiceCode = QtGui.QLineEdit(self)
        self.edtServiceCode.setMinimumWidth(70)
        self.edtServiceCode.setMaximumWidth(110)
        self.edtServiceName = QtGui.QLineEdit(self)
        self.edtServiceName.setMinimumWidth(160)
        spacer1 = QtGui.QSpacerItem(35, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        layoutFilters.addItem(spacer1, 0, 5)
        layoutFilters.addWidget(QtGui.QLabel(u'Услуга:'), 0, 6)
        layoutFilters.addWidget(QtGui.QLabel(u'Код'), 0, 7)
        layoutFilters.addWidget(self.edtServiceCode, 0, 8)
        layoutFilters.addWidget(QtGui.QLabel(u'Наименование'), 0, 9)
        layoutFilters.addWidget(self.edtServiceName, 0, 10)

        self.edtCSGCode = QtGui.QLineEdit(self)
        self.edtCSGCode.setMinimumWidth(70)
        self.edtCSGCode.setMaximumWidth(110)
        self.edtCSGName = QtGui.QLineEdit(self)
        self.edtCSGName.setMinimumWidth(160)
        spacer2 = QtGui.QSpacerItem(35, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        layoutFilters.addItem(spacer2, 1, 5)
        layoutFilters.addWidget(QtGui.QLabel(u'КСГ:'), 1, 6)
        layoutFilters.addWidget(QtGui.QLabel(u'Код'), 1, 7)
        layoutFilters.addWidget(self.edtCSGCode, 1, 8)
        layoutFilters.addWidget(QtGui.QLabel(u'Наименование'), 1, 9)
        layoutFilters.addWidget(self.edtCSGName, 1, 10)

        widgetFilters.setLayout(layoutFilters)

        self.btnBox = CApplyResetDialogButtonBox(self)
        self.btnBox.setStandardButtons(QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Reset)
        self.connect(self.btnBox, SIGNAL(u'clicked(QAbstractButton*)'), self.on_btnBox_clicked)
        self.tbl69 = CTableView(self)
        self.tbl69.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        layout = QtGui.QGridLayout(self)
        layout.addWidget(widgetAgeMKBChoice, 0, 0)
        layout.addWidget(widgetFilters, 0, 1)
        layout.addWidget(self.btnBox, 1, 0, 1, 2)
        layout.addWidget(self.tbl69, 2, 0, 1, 2)
        self.cmbMKBType.setCurrentIndex(0)
        self.cmbAge.setCurrentIndex(0)


    def getQuery(self):
        db = QtGui.qApp.db

        begDate = forceDate(self.parent.eventEditor.eventSetDateTime)
        endDate = forceDate(self.parent.eventEditor.getExecDateTime())
        if not endDate:
            endDate = begDate

        # начальные условия
        conds = u"s69.datn <= '{0}' AND (s69.dato IS NULL OR s69.dato >= '{0}') ".format(endDate.toString('yyyy-MM-dd'))
        vpId = forceRef(db.translate('EventType', 'id', self.parent.eventEditor.eventTypeId, 'medicalAidType_id'))
        vpCode = forceString(db.translate('rbMedicalAidType', 'id', vpId, 'regionalCode'))
        if vpCode in ('11', '12', '301', '302', '401', '402'):
            conds += u"AND s69.vpname = 'стационар' "
        elif vpCode in ('41', '411', '42', '422', '43', '51', '511', '52', '522', '71', '72', '90'):
            conds += u"AND s69.vpname = 'дневной стационар' "

        # столбец и джойн для отображения и фильтрации по МКБ
        mkbCol = u''
        mkbType = self.cmbMKBType.currentIndex()
        filterByMKB = mkbType + 1
        mkbCol = u"s69.mkb AS mkbCol, s69.mkb2 as mkb2Col, s69.mkb3 as mkb3Col"

        if self.edtMKBCode.text() or self.edtMKBName.text():
            # если фильтруем по МКБ, то в столбце МКБ вместо поля из SPR69
            # используем код и наименование из справочника МКБ
            if mkbType == 0:
                # основной диагноз
                mkbCol = u"CONCAT(m.DiagID, ' | ', m.DiagName) AS mkbCol, s69.mkb2 AS mkb2Col, s69.mkb3 AS mkb3Col"
            elif mkbType == 1:
                # сопутствующий диагноз
                mkbCol = u"s69.mkb AS mkbCol, CONCAT(m.DiagID, ' | ', m.DiagName) AS mkb2Col, s69.mkb3 AS mkb3Col"
            elif mkbType == 2:
                # осложнение
                mkbCol = u"s69.mkb AS mkbCol, s69.mkb2 AS mkb2Col, CONCAT(m.DiagID, ' | ', m.DiagName) AS mkb3Col"

        else:
            filterByMKB = 0

        # при фильтрации по МКБ - параметры джойна справочника МКБ
        if filterByMKB == 1:
            mkbJoin = u'LEFT JOIN MKB m on m.DiagID BETWEEN s69.mkbMin AND s69.mkbMax'
        elif filterByMKB == 2:
            mkbJoin = u'LEFT JOIN MKB m on m.DiagID BETWEEN s69.mkb2Min AND s69.mkb2Max'
        elif filterByMKB == 3:
            mkbJoin = u'LEFT JOIN MKB m on m.DiagID BETWEEN s69.mkb3Min AND s69.mkb3Max'
        else:
            mkbJoin = u''


        # параметры фильтрации
        # для кодов - "начинается с", для наименований - "содержит",
        # для возраста - подходящие коды + "не учитывается"
        if self.edtMKBCode.text():
            conds += u"AND m.DiagID LIKE '{0}%'".format(forceString(self.edtMKBCode.text()))
        if self.edtMKBName.text():
            conds += u"AND m.DiagName LIKE '%{0}%'".format(forceString(self.edtMKBName.text()))
        if self.edtServiceCode.text():
            conds += u"AND s1.infis LIKE '{0}%'".format(forceString(self.edtServiceCode.text()))
        if self.edtServiceName.text():
            conds += u"AND s1.name LIKE '%{0}%'".format(forceString(self.edtServiceName.text()))
        if self.edtCSGCode.text():
            conds += u"AND s2.infis LIKE '{0}%'".format(forceString(self.edtCSGCode.text()))
        if self.edtCSGName.text():
            conds += u"AND s2.name LIKE '%{0}%'".format(forceString(self.edtCSGName.text()))
        if self.edtKritCode.text():
            conds += u"AND s80.code LIKE '{0}%'".format(forceString(self.edtKritCode.text()))
        if self.edtKritName.text():
            conds += u"AND s80.name LIKE '%{0}%'".format(forceString(self.edtKritName.text()))
        if self.cmbAge.currentIndex():
            ageGroup = self.cmbAge.currentIndex()
            if ageGroup == 1:
                conds += u"AND (s69.age IN ('1', '4', '5') OR s69.age IS NULL)"
            elif ageGroup == 2:
                conds += u"AND (s69.age IN ('2', '4', '5') OR s69.age IS NULL)"
            elif ageGroup == 3:
                conds += u"AND (s69.age IN ('3', '4', '5') OR s69.age IS NULL)"
            elif ageGroup == 4:
                conds += u"AND (s69.age IN ('4', '5') OR s69.age IS NULL)"
            elif ageGroup == 5:
                conds += u"AND (s69.age = '5' OR s69.age IS NULL)"
            elif ageGroup == 6:
                conds += u"AND (s69.age = '6' OR s69.age IS NULL)"
        if self.edtFractions.value():
            conds += u"AND CAST('{0}' AS INT) BETWEEN cast(SUBSTRING_INDEX(REPLACE(s69.`fr`, 'fr', ''), '-', 1) AS INT) AND cast(SUBSTRING_INDEX(REPLACE(s69.`fr`, 'fr', ''), '-', -1) as INT)".format(forceString(self.edtFractions.value()))


        sql = u"""
            SELECT DISTINCT
              {0},
              s69.age,
              s69.ksgkoef,
              CONCAT(s1.infis, ' | ',  s1.name) AS kuslName,
              CONCAT(s2.infis, ' | ',  s2.name) AS csgName,
              CONCAT(s69.KRIT, ' | ',  s80.name) AS kritName,
              s69.`fr` as fractions,
              s69.dlit 
            FROM soc_spr69 s69
              LEFT JOIN rbService s1 ON s1.id = (SELECT max(id) FROM rbService WHERE rbService.infis = s69.kusl)
              LEFT JOIN rbService s2 ON s2.id = (SELECT max(id) FROM rbService WHERE rbService.infis = s69.ksgkusl)
              LEFT JOIN soc_spr80 s80 ON s80.id = (SELECT max(id) FROM soc_spr80 WHERE s69.KRIT = soc_spr80.code)
              {1}
            WHERE {2};
        """.format(mkbCol, mkbJoin, conds)

        return sql


    @pyqtSignature('QAbstractButton*')
    def on_btnBox_clicked(self, button):
        buttonCode = self.btnBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            # mkbType = self.cmbMKBType.currentIndex()
            # if mkbType == 0:
            #     self.modelSpr69.mkbCol.setTitle(u'МКБ основной')
            # elif mkbType == 1:
            #     self.modelSpr69.mkbCol.setTitle(u'МКБ сопутствующий')
            # elif mkbType == 2:
            #     self.modelSpr69.mkbCol.setTitle(u'МКБ осложнения')
            self.modelSpr69.loadFromSql(self.getQuery())

        else:
            self.cmbMKBType.setCurrentIndex(0)
            self.cmbAge.setCurrentIndex(0)
            self.edtMKBCode.setText('')
            self.edtMKBName.setText('')
            self.edtServiceCode.setText('')
            self.edtServiceName.setText('')
            self.edtCSGCode.setText('')
            self.edtCSGName.setText('')
            self.edtKritCode.setText('')
            self.edtKritName.setText('')
            self.modelSpr69.loadFromSql(self.getQuery())


class CSpr69Model(CMemTableModel):
    def __init__(self, parent):
        # self.mkbCol = CTextCol(u'МКБ', ['mkbCol'], 80)
        CMemTableModel.__init__(self, parent, [
            CTextCol(u'Заключительный диагноз', ['mkbCol'], 80),
            CTextCol(u'Сопутствующий диагноз', ['mkb2Col'], 80),
            CTextCol(u'Диагноз осложнения', ['mkb3Col'], 80),
            self.CAgeCol(u'Возраст', ['age'], 40),
            CTextCol(u'Услуга', ['kuslName'], 100),
            CTextCol(u'КСГ', ['csgName'], 150),
            CTextCol(u'Коэф. затратоёмкости', ['ksgkoef'], 90),
            self.CDlitCol(u'Длительность', ['dlit'], 40),
            CTextCol(u'Критерий', ['kritName'], 60),
            CTextCol(u'Фракции', ['fractions'], 30)
        ])

    class CAgeCol(CTextCol):
        def format(self, values):
            age = forceString(values[0])
            if age == '1':
                return u'от 0 до 28 дней (или новорожденный)'
            elif age == '2':
                return u'от 29 дней до 90 дней'
            elif age == '3':
                return u'от 91 дня до 1 года'
            elif age == '4':
                return u'от 0 дней до 2 лет'
            elif age == '5':
                return u'от 0 дней до 18 лет'
            elif age == '6':
                return u'старше 18 лет'
            else:
                return u'не учитывается'

    class CDlitCol(CTextCol):
        def format(self, values):
            dlit = forceString(values[0])
            if dlit == '1':
                return u'от 1 до 3 дней'
            elif dlit == '2':
                return u'от 4 до 10 дней'
            elif dlit == '3':
                return u'от 11 до 20 дней'
            elif dlit == '4':
                return u'от 21 до 30 дней'
            elif dlit == '5':
                return u'30 дней'
            else:
                return u'не учитывается'
