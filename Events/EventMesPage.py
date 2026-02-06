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


from library.DialogBase import CConstructHelperMixin
from library.crbcombobox import CRBComboBox
from library.interchange import getRBComboBoxValue, setRBComboBoxValue
from library.ICDInDocTableCol import CICDExInDocTableCol
from library.CSG.CSGInDocTableCol import CCSGInDocTableCol
from library.CSG.CSGComboBox import defaultFilters
from library.InDocTable import CInDocTableModel, CIntInDocTableCol, CDateInDocTableCol, CCodeRefInDocTableCol, CSPR80SearchInDocTableCol
from library.ICDUtils import MKBwithoutSubclassification

from library.Utils import forceBool, forceInt, forceRef, forceString, forceDate, toVariant, forceDateTime

from Events.Utils import getEvenMesServiceMask, getEventMesSpecificationId, getEventMesCodeMask, getEventMesNameMask, \
    getEventProfileId, getEventCSGRequired, getEventMesRequired, getEventMesRequiredParams, getEventCSGCodeMask, \
    getEventSubCSGCodeMask, checkDiagnosis
from Reports.CheckMesDescription import showCheckMesDescription
from Reports.MesDescription import showMesDescription


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
        self.tblCSGs.addPopupDuplicateCurrentRow()
        self.tblCSGSubItems.addPopupDelRow()
        self.tblCSGSubItems.addPopupDuplicateCurrentRow()
        self.tblCSGs.setDelRowsIsExposed(lambda rowsExp: not any(map(self.isExposed, rowsExp)))
        self.tblCSGSubItems.setDelRowsIsExposed(lambda rowsExp: not any(map(self.isExposed_sub, rowsExp)))
        self.addObject('actCreateSomeCSGformepls', QtGui.QAction(u'Подобрать КСГ', self))
        self.tblCSGs.addPopupAction(self.actCreateSomeCSGformepls)
        self.connect(self.actCreateSomeCSGformepls, SIGNAL('triggered()'), self.on_actCreateSomeCSGformepls)
        self.actCreateSomeCSGformepls.setEnabled(False)
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
        if hasattr(self.eventEditor,  'modelPreliminaryDiagnostics') and hasattr(self.eventEditor,  'tabMisc'):
            self.actCreateSomeCSGformepls.setEnabled(True)


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
        for record in self.modelCSGs.items():
            if forceString(record.value('CSGCode')):
                haveToCheck = True
                break
        haveToCheckPeriods = u'мэса нет' in unicode(self.cmbMes.currentText()).lower()
        if haveToCheck:
            mainRecords = []
            for row, rec in enumerate(self.modelCSGs.items()):
                begDate = forceDate(rec.value('begDate'))
                endDate = forceDate(rec.value('endDate'))
                if not begDate:
                    self.eventEditor.checkValueMessage(
                        u'Должна быть указана дата начала для КСГ', False,
                        self.tblCSGs, row, 1
                    )
                    return False
                if not endDate:
                    self.eventEditor.checkValueMessage(
                        u'Должна быть указана дата окончания для КСГ', False,
                        self.tblCSGs, row, 2
                    )
                    return False
                if begDate > endDate:
                    self.eventEditor.checkValueMessage(u'Дата начала не может быть больше даты окончания ', False, self.tblCSGs, row,
                                                    1)
                    return False
                mainRecords.append((row, rec, begDate, endDate))

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
        result = len(self.modelCSGs.items()) > 0 or self.eventEditor.checkInputMessage(u'КСГ', False, self.tblCSGs)
        result = result and (self.modelCSGs.checkData() or self.eventEditor.checkInputMessage(u'Данные КСГ', False,
                                                                                              self.tblCSGs))
        result = result and self.checkActualMKB(self.modelCSGs, self.tblCSGs, 1)
        result = result and self.checkActualMKB(self.modelCSGSubItems, self.tblCSGSubItems, 0)
        result = result and self.checkDates(self.modelCSGs, self.tblCSGs, 1)
        result = result and self.checkDates(self.modelCSGSubItems, self.tblCSGSubItems, 0)
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
        if index.column() == 4: # CSG
            self.modelCSGs.setCsgFilterMKB(forceString(
                self.modelCSGs.value(index.row(),'MKB')))
            self.modelCSGs.setCsgFilterEventProfileId(forceRef(
                self.modelCSGs.value(index.row(),'eventProfile_id')))



    @pyqtSignature('QModelIndex')
    def on_tblCSGs_clicked(self, index):
        if index.column() == 4: # CSG
            self.modelCSGs.setCsgFilterMKB(forceString(
                self.modelCSGs.value(index.row(),'MKB')))
            self.modelCSGs.setCsgFilterEventProfileId(forceRef(
                self.modelCSGs.value(index.row(),'eventProfile_id')))


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
        self.addCol(CCodeRefInDocTableCol(   u'Наименование КСГ', 'CSGCode', 45, 'rbService', showFields=CRBComboBox.showName)).setToolTip(u'Наименование КСГ').setReadOnly(True)
        self.addHiddenCol('amount')
        self.addCol(CSPR80SearchInDocTableCol(u'Доп. критерий', 'krit', 15, 'soc_spr80', parentModel=self)).setToolTip(u'Доп. классиф. критерий')
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
        for record in self.items():
            if not (forceDate(record.value('begDate')) and forceDate(record.value('endDate')) and forceString(record.value('MKB')) and forceString(record.value('CSGCode'))):
                return False
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


    def setCsgFilterEventProfileId(self, eventProfileId):
        self.csgCol.setEventProfileId(eventProfileId)


    def setCsgCodeMask(self, mask):
        self.csgCol.setCsgCodeMask(mask)


    def setCsgServicesTemplate(self, MESServiceTemplate):
        self.csgCol.setCsgServiceTemplate(MESServiceTemplate)


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
