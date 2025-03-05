# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

u'''
Сериализация/десериализация полей и моделей из редактора события/действия в json.
'''

import json
import os
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QTime, QVariant, QByteArray, QBuffer, QIODevice
from PyQt4.QtSql import QSqlField, QSqlRecord
from Events.Action import CAction, CActionTypeCache
from library.Utils import toVariant, forceInt


def storeUnsavedDataForActionDialog(self):
    u''' Сохраняет (сериализует) данные полей и свойств из редактора действия в локальный файл '''
    # assert isinstance(self, CActionEditDialog)
    actionTypeId = self.action.getType().id
    filename = 'ActionType_%d.json' % actionTypeId
    path = os.path.join(QtGui.qApp.preferencesDir, filename)
    with open(path, 'w') as f:
        json.dump(_serializeActionDialog(self), f)


def loadUnsavedDataForActionDialog(self):
    u''' Загружает (десериализует) данные полей и свойств из локального файла в редактор действия '''
    # assert isinstance(self, CActionEditDialog)
    actionTypeId = self.action.getType().id
    filename = 'ActionType_%d.json' % actionTypeId
    path = os.path.join(QtGui.qApp.preferencesDir, filename)
    if os.path.isfile(path):
        answer = QtGui.QMessageBox.question(
            None,
            u'Внимание',
            u'Есть несохраненные данные для этого типа действия. Загрузить?',
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
            QtGui.QMessageBox.Yes,
        )
        if answer == QtGui.QMessageBox.Yes:
            with open(path, 'r') as f:
                data = json.load(f)
                _deserializeActionDialog(self, data)
        os.remove(path)
        return True
    return False


def storeUnsavedDataForEventDialog(self):
    # assert isinstance(self, CEventEditDialog)
    if not self.eventTypeForm:
        return
    filename = 'EventType_%s.json' % self.eventTypeForm
    path = os.path.join(QtGui.qApp.preferencesDir, filename)
    pages = {}
    for pageName in ('tabStatus', 'tabDiagnostic', 'tabCure', 'tabMisc', 'tabActions'):
        if hasattr(self, pageName):
            page = getattr(self, pageName)
            if page.__class__.__name__ == 'CActionsPage':
                pages[pageName] = _serializeActionPage(page)
    diagnostics = {}
    for tbl in (
        'tblInspections',
        'tblPreliminaryDiagnostics',
        'tblFinalDiagnostics',
        'tblDiagnostics',
        'tblPersonnel',
    ):
        if hasattr(self, tbl):
            diagnostics[tbl] = _serializeTable(getattr(self, tbl))
    data = {
        'pages': pages,
        'diagnostics': diagnostics,
        'token': _serializeEventTokenPage(self),
    }
    if hasattr(self, 'tblVisits'):
        data['tblVisits'] = _serializeTable(self.tblVisits)
    if hasattr(self, 'tabFeed'):
        data['tabFeed'] = _serializeEventFeedPage(self.tabFeed)
    if hasattr(self, 'tabVoucher'):
        data['tabVoucher'] = _serializeEventVoucherPage(self.tabVoucher)
    if hasattr(self, 'tabMes'):
        data['tabMes'] = _serializeEventMesPage(self.tabMes)
    if hasattr(self, 'tabCash'):
        data['tabCash'] = _serializeEventCashPage(self.tabCash)
    if hasattr(self, 'tabNotes'):
        data['tabNotes'] = _serializeEventNotesPage(self.tabNotes)
    if hasattr(self, 'tblWorkHurts'):
        data['tblWorkHurts'] = _serializeTable(self.tblWorkHurts)
    if hasattr(self, 'tblWorkHurtFactors'):
        data['tblWorkHurtFactors'] = _serializeTable(self.tblWorkHurtFactors)
    if self.eventTypeForm == u'090':
        data['tblInspectionsResult'] = _serializeTable(self.tblInspectionsResult)
        data['tblInfectionDiseases'] = _serializeTable(self.tblInfectionDiseases)
        data['tblClientDiseases'] = _serializeTable(self.tblClientDiseases)
        data['tblVaccinations'] = _serializeTable(self.tblVaccinations)
        data['tblClientVaccinations'] = _serializeTable(self.tblClientVaccinations)
        data['tblStatusActions'] = _serializeTable(self.tblStatusActions)
        data['tblLabDiagnosticActions'] = _serializeTable(self.tblLabDiagnosticActions)
        data['tblToolDiagnosticActions'] = _serializeTable(self.tblToolDiagnosticActions)
        data['tblMembersMSIPerson'] = _serializeTable(self.tblMembersMSIPerson)
    with open(path, 'w') as f:
        json.dump(data, f)


def loadUnsavedDataForEventDialog(self):
    # assert isinstance(self, CEventEditDialog)
    if not self.eventTypeForm:
        return False
    filename = 'EventType_%s.json' % self.eventTypeForm
    path = os.path.join(QtGui.qApp.preferencesDir, filename)
    if os.path.isfile(path):
        answer = QtGui.QMessageBox.question(
            None,
            u'Внимание',
            u'Есть несохраненные данные для этого типа события. Загрузить?',
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
            QtGui.QMessageBox.Yes,
        )
        if answer == QtGui.QMessageBox.Yes:
            with open(path, 'r') as f:
                data = json.load(f)
                _deserializeEventTokenPage(self, data['token'])
                for page, pageData in data.get('pages', {}).iteritems():
                    _deserializeActionPage(getattr(self, page), pageData)
                for table, tableRows in data.get('diagnostics', {}).iteritems():
                    _deserializeTable(getattr(self, table), tableRows)
                if 'tblVisits' in data and hasattr(self, 'tblVisits'):
                    _deserializeTable(self.tblVisits, data['tblVisits'])
                if 'tabFeed' in data and hasattr(self, 'tabFeed'):
                    _deserializeEventFeedPage(self.tabFeed, data['tabFeed'])
                if 'tabVoucher' in data and hasattr(self, 'tabVoucher'):
                    _deserializeEventVoucherPage(self.tabVoucher, data['tabVoucher'])
                if 'tabMes' in data and hasattr(self, 'tabMes'):
                    _deserializeEventMesPage(self.tabMes, data['tabMes'])
                if 'tabCash' in data and hasattr(self, 'tabCash'):
                    _deserializeEventCashPage(self.tabCash, data['tabCash'])
                if 'tabNotes' in data and hasattr(self, 'tabNotes'):
                    _deserializeEventNotesPage(self.tabNotes, data['tabNotes'])
                if 'tblWorkHurts' in data and hasattr(self, 'tblWorkHurts'):
                    _deserializeTable(self.tblWorkHurts, data['tblWorkHurts'])
                if 'tblWorkHurtFactors' in data and hasattr(self, 'tblWorkHurtFactors'):
                    _deserializeTable(self.tblWorkHurtFactors, data['tblWorkHurtFactors'])
                if self.eventTypeForm == u'090':
                    _deserializeTable(self.tblInspectionsResult, data['tblInspectionsResult'])
                    _deserializeTable(self.tblInfectionDiseases, data['tblInfectionDiseases'])
                    _deserializeTable(self.tblClientDiseases, data['tblClientDiseases'])
                    _deserializeTable(self.tblVaccinations, data['tblVaccinations'])
                    _deserializeTable(self.tblClientVaccinations, data['tblClientVaccinations'])
                    _deserializeTable(self.tblStatusActions, data['tblStatusActions'])
                    _deserializeTable(self.tblLabDiagnosticActions, data['tblLabDiagnosticActions'])
                    _deserializeTable(self.tblToolDiagnosticActions, data['tblToolDiagnosticActions'])
                    _deserializeTable(self.tblMembersMSIPerson, data['tblMembersMSIPerson'])

        os.remove(path)
        return True
    return False


def _serializeActionDialog(self):
    result = {
        'edtDirectionDate': toISO(self.edtDirectionDate.date()),
        'edtDirectionTime': toISO(self.edtDirectionTime.time()),
        'chkIsUrgent': int(self.chkIsUrgent.isChecked()),
        'cmbSetPerson': self.cmbSetPerson.value(),
        'edtPlannedEndDate': toISO(self.edtPlannedEndDate.date()),
        'edtPlannedEndTime': toISO(self.edtPlannedEndTime.time()),
        'cmbOrg': self.cmbOrg.value(),
        'cmbMorphologyMKB': unicode(self.cmbMorphologyMKB.text()),
        'cmbMKB': unicode(self.cmbMKB.text()),
        'cmbStatus': self.cmbStatus.value(),
        'edtBegDate': toISO(self.edtBegDate.date()),
        'edtBegTime': toISO(self.edtBegTime.time()),
        'edtEndDate': toISO(self.edtEndDate.date()),
        'edtEndTime': toISO(self.edtEndTime.time()),
        'edtAmount': self.edtAmount.value(),
        'edtUet': self.edtUet.value(),
        'edtOffice': unicode(self.edtOffice.text()),
        'cmbPerson': self.cmbPerson.value(),
        'cmbAssistant': self.cmbAssistant.value(),
        'edtQuantity': self.edtQuantity.value(),
        'edtDuration': self.edtDuration.value(),
        'edtPeriodicity': self.edtPeriodicity.value(),
        'edtAliquoticity': self.edtAliquoticity.value(),
        'cmbOrgStructure': self.cmbOrgStructure.value(),
        'edtNote': unicode(self.edtNote.text()),
        'edtCoordDate': toISO(self.edtCoordDate.date()),
        'edtCoordTime': toISO(self.edtCoordTime.time()),
        'cmbActionSpecification': self.cmbActionSpecification.value(),
    }
    propsResult = {}
    for propId, prop in self.action.getPropertiesById().iteritems():
        value = prop.getValue()
        propsResult[propId] = _serializeVariant(toVariant(value))
    result['properties'] = propsResult
    return result


def _serializeActionPage(page):
    result = {
        'edtAPDirectionDate': toISO(page.edtAPDirectionDate.date()),
        'edtAPDirectionTime': toISO(page.edtAPDirectionTime.time()),
        'chkAPIsUrgent': int(page.chkAPIsUrgent.isChecked()),
        'cmbAPSetPerson': page.cmbAPSetPerson.value(),
        'edtAPPlannedEndDate': toISO(page.edtAPPlannedEndDate.date()),
        'edtAPPlannedEndTime': toISO(page.edtAPPlannedEndTime.time()),
        'cmbAPOrg': page.cmbAPOrg.value(),
        'cmbAPMorphologyMKB': unicode(page.cmbAPMorphologyMKB.text()),
        'cmbAPMKB': unicode(page.cmbAPMKB.text()),
        'cmbAPStatus': page.cmbAPStatus.value(),
        'edtAPBegDate': toISO(page.edtAPBegDate.date()),
        'edtAPBegTime': toISO(page.edtAPBegTime.time()),
        'edtAPEndDate': toISO(page.edtAPEndDate.date()),
        'edtAPEndTime': toISO(page.edtAPEndTime.time()),
        'edtAPAmount': page.edtAPAmount.value(),
        'edtAPUet': page.edtAPUet.value(),
        'edtAPOffice': unicode(page.edtAPOffice.text()),
        'cmbAPPerson': page.cmbAPPerson.value(),
        'cmbAPAssistant': page.cmbAPAssistant.value(),
        'edtAPQuantity': page.edtAPQuantity.value(),
        'edtAPDuration': page.edtAPDuration.value(),
        'edtAPPeriodicity': page.edtAPPeriodicity.value(),
        'edtAPAliquoticity': page.edtAPAliquoticity.value(),
        'cmbAPOrgStructure': page.cmbAPOrgStructure.value(),
        'edtAPNote': unicode(page.edtAPNote.text()),
        'edtAPCoordDate': toISO(page.edtAPCoordDate.date()),
        'edtAPCoordTime': toISO(page.edtAPCoordTime.time()),
        'cmbActionSpecification': page.cmbActionSpecification.value(),
    }
    actionsResult = []
    model = page.tblAPActions.model()
    for record, action in model.items():
        propsResult = {}
        for propId, prop in action.getPropertiesById().iteritems():
            value = prop.getValue()
            propsResult[propId] = _serializeVariant(toVariant(value))
        actionsResult.append({
            'record': _serializeRecord(record),
            'properties': propsResult,
        })
    result['actions'] = actionsResult
    return result


def _deserializeActionDialog(self, data):
    self.edtDirectionDate.setDate(fromISO(QDate, data['edtDirectionDate']))
    self.edtDirectionTime.setTime(fromISO(QTime, data['edtDirectionTime']))
    self.chkIsUrgent.setChecked(data['chkIsUrgent'])
    self.cmbSetPerson.setValue(data['cmbSetPerson'])
    self.edtPlannedEndDate.setDate(fromISO(QDate, data['edtPlannedEndDate']))
    self.edtPlannedEndTime.setTime(fromISO(QTime, data['edtPlannedEndTime']))
    self.cmbOrg.setValue(data['cmbOrg'])
    self.cmbMorphologyMKB.setText(data['cmbMorphologyMKB'])
    self.cmbMKB.setText(data['cmbMKB'])
    self.cmbStatus.setValue(data['cmbStatus'])
    self.edtBegDate.setDate(fromISO(QDate, data['edtBegDate']))
    self.edtBegTime.setTime(fromISO(QTime, data['edtBegTime']))
    self.edtEndDate.setDate(fromISO(QDate, data['edtEndDate']))
    self.edtEndTime.setTime(fromISO(QTime, data['edtEndTime']))
    self.edtAmount.setValue(data['edtAmount'])
    self.edtUet.setValue(data['edtUet'])
    self.edtOffice.setText(data['edtOffice'])
    self.cmbPerson.setValue(data['cmbPerson'])
    self.cmbAssistant.setValue(data['cmbAssistant'])
    self.edtQuantity.setValue(data['edtQuantity'])
    self.edtDuration.setValue(data['edtDuration'])
    self.edtPeriodicity.setValue(data['edtPeriodicity'])
    self.edtAliquoticity.setValue(data['edtAliquoticity'])
    self.cmbOrgStructure.setValue(data['cmbOrgStructure'])
    self.edtNote.setText(data['edtNote'])
    self.edtCoordDate.setDate(fromISO(QDate, data['edtCoordDate']))
    self.edtCoordTime.setTime(fromISO(QTime, data['edtCoordTime']))
    self.cmbActionSpecification.setValue(data['cmbActionSpecification'])
    for propId, value in data['properties'].iteritems():
        prop = self.action.getPropertyById(int(propId))
        prop.setValue(value)


def _deserializeActionPage(page, data):
    page.edtAPDirectionDate.setDate(fromISO(QDate, data['edtAPDirectionDate']))
    page.edtAPDirectionTime.setTime(fromISO(QTime, data['edtAPDirectionTime']))
    page.chkAPIsUrgent.setChecked(data['chkAPIsUrgent'])
    page.cmbAPSetPerson.setValue(data['cmbAPSetPerson'])
    page.edtAPPlannedEndDate.setDate(fromISO(QDate, data['edtAPPlannedEndDate']))
    page.edtAPPlannedEndTime.setTime(fromISO(QTime, data['edtAPPlannedEndTime']))
    page.cmbAPOrg.setValue(data['cmbAPOrg'])
    page.cmbAPMorphologyMKB.setText(data['cmbAPMorphologyMKB'])
    page.cmbAPMKB.setText(data['cmbAPMKB'])
    page.cmbAPStatus.setValue(data['cmbAPStatus'])
    page.edtAPBegDate.setDate(fromISO(QDate, data['edtAPBegDate']))
    page.edtAPBegTime.setTime(fromISO(QTime, data['edtAPBegTime']))
    page.edtAPEndDate.setDate(fromISO(QDate, data['edtAPEndDate']))
    page.edtAPEndTime.setTime(fromISO(QTime, data['edtAPEndTime']))
    page.edtAPAmount.setValue(data['edtAPAmount'])
    page.edtAPUet.setValue(data['edtAPUet'])
    page.edtAPOffice.setText(data['edtAPOffice'])
    page.cmbAPPerson.setValue(data['cmbAPPerson'])
    page.cmbAPAssistant.setValue(data['cmbAPAssistant'])
    page.edtAPQuantity.setValue(data['edtAPQuantity'])
    page.edtAPDuration.setValue(data['edtAPDuration'])
    page.edtAPPeriodicity.setValue(data['edtAPPeriodicity'])
    page.edtAPAliquoticity.setValue(data['edtAPAliquoticity'])
    page.cmbAPOrgStructure.setValue(data['cmbAPOrgStructure'])
    page.edtAPNote.setText(data['edtAPNote'])
    page.edtAPCoordDate.setDate(fromISO(QDate, data['edtAPCoordDate']))
    page.edtAPCoordTime.setTime(fromISO(QTime, data['edtAPCoordTime']))
    page.cmbActionSpecification.setValue(data['cmbActionSpecification'])

    model = page.tblAPActions.model()
    model.removeRows(0, model.rowCount())
    for item in data['actions']:
        record = _deserializeRecord(item['record'])
        actionTypeId = forceInt(record.value('actionType_id'))
        actionType = CActionTypeCache.getById(actionTypeId)
        action = CAction(actionType, record)
        for propId, value in item['properties'].iteritems():
            prop = action.getPropertyById(int(propId))
            prop.setValue(_deserializeVariant(value).toPyObject())
        model.addRow(actionTypeId, None, None, None, action)


def _serializeEventFeedPage(page):
    # assert isinstance(page, CEventFeedPage)

    # CFeedModel имеет необычное внутреннее устройство,
    # поэтому собираю данные из модели в матрицу через data.
    # Важно - использую role=Qt.EditRole, чтобы получать
    # id справочных столбцов, а не их отображаемый текст.

    clientFeed = []
    model = page.tblClientFeed.model()
    for row in xrange(model.rowCount()):
        tableRow = []
        for col in xrange(model.columnCount()):
            index = model.createIndex(row, col)
            role = Qt.CheckStateRole if col == model.columnCount()-1 else Qt.EditRole
            item = toVariant(model.data(index, role))
            tableRow.append(_serializeVariant(item))
        clientFeed.append(tableRow)

    patronFeed = []
    model = page.tblPatronFeed.model()
    for row in xrange(model.rowCount()):
        tableRow = []
        for col in xrange(model.columnCount()):
            index = model.createIndex(row, col)
            role = Qt.CheckStateRole if col == model.columnCount()-1 else Qt.EditRole
            item = toVariant(model.data(index, role))
            tableRow.append(_serializeVariant(item))
        patronFeed.append(tableRow)

    return {
        'clientFeed': clientFeed,
        'patronFeed': patronFeed,
    }


def _deserializeEventFeedPage(page, data):
    # assert isinstance(page, CEventFeedPage)

    # CFeedModel имеет необычное внутреннее устройство,
    # поэтому сериализованные данные хранятся в матрице.
    # Восстанавливаю данные через setData.

    model = page.tblClientFeed.model()
    for row, tableRow in enumerate(data['clientFeed']):
        for col, item in enumerate(tableRow):
            index = model.createIndex(row, col)
            role = Qt.CheckStateRole if col == len(tableRow)-1 else Qt.EditRole
            model.setData(index, _deserializeVariant(item), role)
    page.tblClientFeed.reset()

    model = page.tblPatronFeed.model()
    for row, tableRow in enumerate(data['patronFeed']):
        for col, item in enumerate(tableRow):
            index = model.createIndex(row, col)
            role = Qt.CheckStateRole if col == len(tableRow)-1 else Qt.EditRole
            model.setData(index, _deserializeVariant(item), role)
    page.tblPatronFeed.reset()


def _serializeEventVoucherPage(page):
    # assert isinstance(page, CEventVoucherPage)
    return {
        'voucherOrgId': page.cmbVoucherOrgs.value(),
        'voucherFinanceId': page.cmbVoucherFinance.value(),
        'serial': unicode(page.edtVoucherSerial.text()),
        'number': unicode(page.edtVoucherNumber.text()),
        'begDate': toISO(page.edtVoucherBegDate.date()),
        'endDate': toISO(page.edtVoucherEndDate.date()),
        'directionCity': str(page.cmbDirectionCity.code()),
        'directionRegion': page.cmbDirectionRegion.value(),
        'directionOrgId': page.cmbDirectionOrgs.value(),
        'directionPersonId': page.cmbDirectionPerson.value(),
        'directionNumber': unicode(page.edtDirectionNumber.text()),
        'directionDate': str(page.edtDirectionDate.date().toString(Qt.ISODate)),
        'directionMKB': str(page.edtDirectionMKB.text()),
    }


def _deserializeEventVoucherPage(page, data):
    # assert isinstance(page, CEventVoucherPage)
    page.cmbVoucherOrgs.setValue(data['voucherOrgId'])
    page.cmbVoucherFinance.setValue(data['voucherFinanceId'])
    page.edtVoucherSerial.setText(data['serial'])
    page.edtVoucherNumber.setText(data['number'])
    page.edtVoucherBegDate.setDate(fromISO(QDate, data['begDate']))
    page.edtVoucherEndDate.setDate(fromISO(QDate, data['endDate']))
    page.cmbDirectionCity.setCode(data['directionCity'])
    page.cmbDirectionRegion.setValue(data['directionRegion'])
    page.cmbDirectionOrgs.setValue(data['directionOrgId'])
    page.cmbDirectionPerson.setValue(data['directionPersonId'])
    page.edtDirectionNumber.setText(data['directionNumber'])
    page.edtDirectionDate.setDate(fromISO(QDate, data['directionDate']))
    page.edtDirectionMKB.setText(data['directionMKB'])


def _serializeEventMesPage(page):
    # assert isinstance(page, CEventMesPage)
    return {
        'cmbMes': page.cmbMes.value(),
        'cmbMesSpecification': page.cmbMesSpecification.value(),
        'tblCSGs': _serializeTable(page.tblCSGs),
        'tblCSGSubItems': _serializeTable(page.tblCSGSubItems),
    }


def _deserializeEventMesPage(page, data):
    # assert isinstance(page, CEventMesPage)
    page.cmbMes.setValue(data['cmbMes'])
    page.cmbMesSpecification.setValue(data['cmbMesSpecification'])
    _deserializeTable(page.tblCSGs, data['tblCSGs'])
    _deserializeTable(page.tblCSGSubItems, data['tblCSGSubItems'])


def _serializeEventNotesPage(page):
    # assert isinstance(page, (CEventNotesPage, CEventNotesPageProtocol))
    result = {
        'chkIsClosed': page.chkIsClosed.isChecked(),
        'edtEventNote': unicode(page.edtEventNote.toPlainText()),
    }
    if hasattr(page, 'cmbPatientModel'):
        result['cmbPatientModel'] = page.cmbPatientModel.value()
    if hasattr(page, 'cmbCureType'):
        result['cmbCureType'] = page.cmbCureType.value()
    if hasattr(page, 'cmbCureMethod'):
        result['cmbCureMethod'] = page.cmbCureMethod.value()
    if hasattr(page, 'edtExpertiseDate'):
        result['edtExpertiseDate'] = toISO(page.edtExpertiseDate.date())
    if hasattr(page, 'cmbExpertPerson'):
        result['cmbExpertPerson'] = page.cmbExpertPerson.value()
    if hasattr(page, 'cmbEventAssistant'):
        result['cmbEventAssistant'] = page.cmbEventAssistant.value()
    if hasattr(page, 'cmbEventCurator'):
        result['cmbEventCurator'] = page.cmbEventCurator.value()
    if hasattr(page, 'cmbClientRelationConsents'):
        result['cmbClientRelationConsents'] = page.cmbClientRelationConsents.value()
    if hasattr(page, 'cmbRelegateOrg'):
        result['cmbRelegateOrg'] = page.cmbRelegateOrg.value()
    if hasattr(page, 'edtEventSrcDate'):
        result['edtEventSrcDate'] = toISO(page.edtEventSrcDate.date())
    if hasattr(page, 'edtEventSrcNumber'):
        result['edtEventSrcNumber'] = unicode(page.edtEventSrcNumber.text())
    if hasattr(page, 'cmbRelegatePerson'):
        result['cmbRelegatePerson'] = page.cmbRelegatePerson.value()
    return result


def _deserializeEventNotesPage(page, data):
    # assert isinstance(page, (CEventNotesPage, CEventNotesPageProtocol))
    page.chkIsClosed.setChecked(data['chkIsClosed'])
    page.edtEventNote.setPlainText(data['edtEventNote'])
    if hasattr(page, 'cmbPatientModel'):
        page.cmbPatientModel.setValue(data['cmbPatientModel'])
    if hasattr(page, 'cmbCureType'):
        page.cmbCureType.setValue(data['cmbCureType'])
    if hasattr(page, 'cmbCureMethod'):
        page.cmbCureMethod.setValue(data['cmbCureMethod'])
    if hasattr(page, 'edtExpertiseDate'):
        page.edtExpertiseDate.setDate(fromISO(QDate, data['edtExpertiseDate']))
    if hasattr(page, 'cmbExpertPerson'):
        page.cmbExpertPerson.setValue(data['cmbExpertPerson'])
    if hasattr(page, 'cmbEventAssistant'):
        page.cmbEventAssistant.setValue(data['cmbEventAssistant'])
    if hasattr(page, 'cmbEventCurator'):
        page.cmbEventCurator.setValue(data['cmbEventCurator'])
    if hasattr(page, 'cmbClientRelationConsents'):
        page.cmbClientRelationConsents.setValue(data['cmbClientRelationConsents'])
    if hasattr(page, 'cmbRelegateOrg'):
        page.cmbRelegateOrg.setValue(data['cmbRelegateOrg'])
    if hasattr(page, 'edtEventSrcDate'):
        page.edtEventSrcDate.setDate(fromISO(QDate, data['edtEventSrcDate']))
    if hasattr(page, 'edtEventSrcNumber'):
        page.edtEventSrcNumber.setText(data['edtEventSrcNumber'])
    if hasattr(page, 'cmbRelegatePerson'):
        page.cmbRelegatePerson.setValue(data['cmbRelegatePerson'])


def _serializeEventCashPage(page):
    # assert isinstance(page, CEventCashPage)
    result = {
        'grpLocalContract': page.grpLocalContract.isChecked(),
        'edtCoordDate': toISO(page.edtCoordDate.date()),
        'edtCoordAgent': unicode(page.edtCoordAgent.text()),
        'edtCoordInspector': unicode(page.edtCoordInspector.text()),
        'edtContractDate': toISO(page.edtContractDate.date()),
        'edtContractNumber': unicode(page.edtContractNumber.text()),
        'edtSumLimit': unicode(page.edtSumLimit.text()),
        'edtLastName': unicode(page.edtLastName.text()),
        'edtFirstName': unicode(page.edtFirstName.text()),
        'edtPatrName': unicode(page.edtPatrName.text()),
        'edtBirthDate': toISO(page.edtBirthDate.date()),
        'cmbDocType': page.cmbDocType.value(),
        'edtDocSerialLeft': unicode(page.edtDocSerialLeft.text()),
        'edtDocSerialRight': unicode(page.edtDocSerialRight.text()),
        'edtDocNumber': unicode(page.edtDocNumber.text()),
        'edtDocOrigin': unicode(page.edtDocOrigin.text()),
        'edtDocDate': toISO(page.edtDocDate.date()),
        'edtRegAddress': unicode(page.edtRegAddress.text()),
        'cmbOrganisation': page.cmbOrganisation.value(),
        'edtEmail': unicode(page.edtEmail.text()),
        'edtCoordText': unicode(page.edtCoordText.toPlainText()),
        'grpCustomer': page.grpCustomer.isChecked(),
        'edtCustomerLastName': unicode(page.edtCustomerLastName.text()),
        'edtCustomerFirstName': unicode(page.edtCustomerFirstName.text()),
        'edtCustomerPatrName': unicode(page.edtCustomerPatrName.text()),
        'edtCustomerBirthDate': toISO(page.edtCustomerBirthDate.date()),
        'cmbCustomerDocType': page.cmbCustomerDocType.value(),
        'edtCustomerDocSerialLeft': unicode(page.edtCustomerDocSerialLeft.text()),
        'edtCustomerDocSerialRight': unicode(page.edtCustomerDocSerialRight.text()),
        'edtCustomerDocNumber': unicode(page.edtCustomerDocNumber.text()),
        'edtCustomerDocOrigin': unicode(page.edtCustomerDocOrigin.text()),
        'edtCustomerDocDate': toISO(page.edtCustomerDocDate.date()),
        'edtCustomerRegAddress': unicode(page.edtCustomerRegAddress.text()),
        'cmbCustomerOrganisation': page.cmbCustomerOrganisation.value(),
        'edtCustomerEmail': unicode(page.edtCustomerEmail.text()),
        'tblPayments': _serializeTable(page.tblPayments),
    }
    return result


def _deserializeEventCashPage(page, data):
    # assert isinstance(page, CEventCashPage)
    page.grpLocalContract.setChecked(data['grpLocalContract'])
    page.edtCoordDate.setDate(fromISO(QDate, data['edtCoordDate']))
    page.edtCoordAgent.setText(data['edtCoordAgent'])
    page.edtCoordInspector.setText(data['edtCoordInspector'])
    page.edtContractDate.setDate(fromISO(QDate, data['edtContractDate']))
    page.edtContractNumber.setText(data['edtContractNumber'])
    page.edtSumLimit.setText(data['edtSumLimit'])
    page.edtLastName.setText(data['edtLastName'])
    page.edtFirstName.setText(data['edtFirstName'])
    page.edtPatrName.setText(data['edtPatrName'])
    page.edtBirthDate.setDate(fromISO(QDate, data['edtBirthDate']))
    page.cmbDocType.setValue(data['cmbDocType'])
    page.edtDocSerialLeft.setText(data['edtDocSerialLeft'])
    page.edtDocSerialRight.setText(data['edtDocSerialRight'])
    page.edtDocNumber.setText(data['edtDocNumber'])
    page.edtDocOrigin.setText(data['edtDocOrigin'])
    page.edtDocDate.setDate(fromISO(QDate, data['edtDocDate']))
    page.edtRegAddress.setText(data['edtRegAddress'])
    page.cmbOrganisation.setValue(data['cmbOrganisation'])
    page.edtEmail.setText(data['edtEmail'])
    page.edtCoordText.setPlainText(data['edtCoordText'])
    page.grpCustomer.setChecked(data['grpCustomer'])
    page.edtCustomerLastName.setText(data['edtCustomerLastName'])
    page.edtCustomerFirstName.setText(data['edtCustomerFirstName'])
    page.edtCustomerPatrName.setText(data['edtCustomerPatrName'])
    page.edtCustomerBirthDate.setDate(fromISO(QDate, data['edtCustomerBirthDate']))
    page.cmbCustomerDocType.setValue(data['cmbCustomerDocType'])
    page.edtCustomerDocSerialLeft.setText(data['edtCustomerDocSerialLeft'])
    page.edtCustomerDocSerialRight.setText(data['edtCustomerDocSerialRight'])
    page.edtCustomerDocNumber.setText(data['edtCustomerDocNumber'])
    page.edtCustomerDocOrigin.setText(data['edtCustomerDocOrigin'])
    page.edtCustomerDocDate.setDate(fromISO(QDate, data['edtCustomerDocDate']))
    page.edtCustomerRegAddress.setText(data['edtCustomerRegAddress'])
    page.cmbCustomerOrganisation.setValue(data['cmbCustomerOrganisation'])
    page.edtCustomerEmail.setText(data['edtCustomerEmail'])
    _deserializeTable(page.tblPayments, data['tblPayments'])


def _serializeEventTokenPage(self):
    # assert isinstance(self, CEventEditDialog)
    result = {
        'edtBegDate': toISO(self.edtBegDate.date()),
        'edtBegTime': toISO(self.edtBegTime.time()),
        'edtEndDate': toISO(self.edtEndDate.date()),
        'edtEndTime': toISO(self.edtEndTime.time()),
    }
    if hasattr(self, 'cmbPerson'):
        result['cmbPerson'] = self.cmbPerson.value()
    if hasattr(self, 'cmbContract'):
        result['cmbContract'] = self.cmbContract.value()
    if hasattr(self, 'chkPrimary'):
        result['chkPrimary'] = self.chkPrimary.isChecked()
    if hasattr(self, 'cmbOrder'):
        result['cmbOrder'] = self.cmbOrder.currentIndex()
    if hasattr(self, 'cmbResult'):
        result['cmbResult'] = self.cmbResult.value()
    if hasattr(self, 'edtNextDate'):
        result['edtNextDate'] = toISO(self.edtNextDate.date())
    if hasattr(self, 'edtNextTime'):
        result['edtNextTime'] = toISO(self.edtNextTime.time())
    if hasattr(self, 'cmbPrimary'):
        result['cmbPrimary'] = self.cmbPrimary.currentIndex()
    if hasattr(self, 'edtPregnancyWeek'):
        result['edtPregnancyWeek'] = self.edtPregnancyWeek.value()
    if hasattr(self, 'cmbClientRelationConsents'):
        result['cmbClientRelationConsents'] = self.cmbClientRelationConsents.value()
    if hasattr(self, 'edtEventExternalIdValue'):
        result['edtEventExternalIdValue'] = unicode(self.edtEventExternalIdValue.text())
    if self.eventTypeForm == u'001':
        result['cmbSetPerson'] = self.cmbSetPerson.value()
        result['chkConstraintActionTypes'] = self.chkConstraintActionTypes.isChecked()
        result['cmbMKB'] = unicode(self.cmbMKB.text())
        result['chkDiagnosisType'] = self.chkDiagnosisType.isChecked()
        result['cmbMKBEx'] = unicode(self.cmbMKBEx.text())
        result['cmbMorphology'] = unicode(self.cmbMorphology.text())
        result['cmbCharacter'] = self.cmbCharacter.value()
        result['cmbTraumaType'] = self.cmbTraumaType.value()
        result['cmbToxicSubstances'] = self.cmbToxicSubstances.value()
        result['cmbTNMS'] = self.cmbTNMS.getValue()[0]
        result['cmbExecPerson'] = self.cmbExecPerson.value()
        result['cmbDiagnosticResult'] = self.cmbDiagnosticResult.value()
        result['edtFreeInput'] = unicode(self.edtFreeInput.text())
        result['cmbTissueType'] = self.cmbTissueType.value()
        result['edtTissueDate'] = toISO(self.edtTissueDate.date())
        result['edtTissueTime'] = toISO(self.edtTissueTime.time())
        result['cmbTissueExecPerson'] = self.cmbTissueExecPerson.value()
        result['edtTissueAmount'] = self.edtTissueAmount.value()
        result['cmbTissueUnit'] = self.cmbTissueUnit.value()
        result['edtTissueExternalId'] = unicode(self.edtTissueExternalId.text())
        result['edtTissueNumber'] = unicode(self.edtTissueNumber.text())
        result['edtTissueNote'] = unicode(self.edtTissueNote.text())
    elif self.eventTypeForm == u'027':
        result['cmbRelegateOrg'] = self.cmbRelegateOrg.value()
        result['cmbPatientModel'] = self.cmbPatientModel.value()
        result['cmbCureType'] = self.cmbCureType.value()
        result['cmbCureMethod'] = self.cmbCureMethod.value()
        result['cmbEventCurator'] = self.cmbEventCurator.value()
        result['cmbPersonMedicineHead'] = self.cmbPersonMedicineHead.value()
        result['cmbPersonManager'] = self.cmbPersonManager.value()
        result['cmbPersonExpert'] = self.cmbPersonExpert.value()
        result['cmbEventAssistant'] = self.cmbEventAssistant.value()
    elif self.eventTypeForm == u'043':
        result['cmbDentitionBite'] = self.cmbDentitionBite.value()
        result['cmbDentitionApparat'] = self.cmbDentitionApparat.value()
        result['cmbDentitionProtezes'] = self.cmbDentitionProtezes.value()
        result['cmbDentitionOrtodontCure'] = self.cmbDentitionOrtodontCure.value()
        result['cmbDentitionSanitation'] = self.cmbDentitionSanitation.value()
        result['cmbDentitionNoTeeth'] = self.cmbDentitionNoTeeth.value()
        result['edtDentitionObjectively'] = self.edtDentitionObjectively.value()
        result['edtDentitionMucosa'] = self.edtDentitionMucosa.value()
        result['edtDentitionNote'] = unicode(self.edtDentitionNote.toPlainText())
        # переключаемся на последнюю запись в истории
        index = self.modelClientDentitionHistory.index(self.modelClientDentitionHistory.rowCount()-1, 0)
        self.tblClientDentitionHistory.setCurrentIndex(index)
        item = self.modelClientDentitionHistory.getItem(index)
        action = item[1] # type: CActionInfo
        toothProperties = {}
        for name, prop in action.getPropertiesByName().iteritems():
            if prop.type().typeName == u'Зуб':
                toothProperties[name] = prop.getTextScalar()
        result['toothProperties'] = toothProperties
    elif self.eventTypeForm == u'090':
        result['edtDirectionDate'] = toISO(self.edtDirectionDate.date())
        result['edtDirectionTime'] = toISO(self.edtDirectionTime.time())
        result['chkIsUrgent'] = self.chkIsUrgent.isChecked()
        result['cmbSetPerson'] = self.cmbSetPerson.value()
        result['edtPlannedEndDate'] = toISO(self.edtPlannedEndDate.date())
        result['cmbOrg'] = self.cmbOrg.value()
        result['cmbStatus'] = self.cmbStatus.currentIndex()
        result['edtAmount'] = self.edtAmount.value()
        result['edtOffice'] = unicode(self.edtOffice.text())
        result['cmbAssistant'] = self.cmbAssistant.value()
        result['edtNote'] = unicode(self.edtNote.text())
        result['cmbHurtType'] = self.cmbHurtType.value()
        result['edtElectronicMedicalBookNumber'] = unicode(self.edtElectronicMedicalBookNumber.text())
        result['edtCommentResult'] = unicode(self.edtCommentResult.toPlainText())
        result['cmbInfoResult'] = self.cmbInfoResult.value()
        result['edtVisitDateNextResult'] = toISO(self.edtVisitDateNextResult.date())
    elif self.eventTypeForm == u'106':
        result['cmbDeathPlaceType'] = self.cmbDeathPlaceType.value()
        result['cmbDeathCauseType'] = self.cmbDeathCauseType.value()
        result['cmbGroundsForDeathCause'] = self.cmbGroundsForDeathCause.value()
        result['chkAutopsy'] = self.chkAutopsy.isChecked()
        result['cmbAutopsyType'] = self.cmbAutopsyType.value()
        result['cmbOrg'] = self.cmbOrg.value()
        result['edtNumber'] = unicode(self.edtNumber.text())
        result['cmbEmployeeTypeDeterminedDeathCause'] = self.cmbEmployeeTypeDeterminedDeathCause.value()
        result['cmbPerson2'] = self.cmbPerson2.value()
        result['chkKLADR'] = self.chkKLADR.isChecked()
        result['edtFreeInput'] = unicode(self.edtFreeInput.text())
        result['cmbCity'] = str(self.cmbCity.code())
        result['cmbStreet'] = str(self.cmbStreet.code())
        result['edtHouse'] = self.edtHouse.text()
        result['edtCorpus'] = self.edtCorpus.text()
        result['edtFlat'] = self.edtFlat.text()
        result['edtNote'] = unicode(self.edtNote.toPlainText())
    elif self.eventTypeForm == u'110':
        result['edtNumberCardCall'] = unicode(self.edtNumberCardCall.text())
        result['cmbNumberBrigade'] = self.cmbNumberBrigade.value()
        result['cmbCauseCall'] = self.cmbCauseCall.value()
        result['edtWhoCallOnPhone'] = unicode(self.edtWhoCallOnPhone.text())
        result['edtNumberPhone'] = unicode(self.edtNumberPhone.text())
        result['edtStorey'] = unicode(self.edtStorey.text())
        result['edtEntrance'] = unicode(self.edtEntrance.text())
        result['cmbOrgStructure'] = self.cmbOrgStructure.value()
        result['edtAdditional'] = unicode(self.edtAdditional.toPlainText())
        result['edtPassDate'] = toISO(self.edtPassDate.date())
        result['edtPassTime'] = toISO(self.edtPassTime.time())
        result['edtDepartureDate'] = toISO(self.edtDepartureDate.date())
        result['edtDepartureTime'] = toISO(self.edtDepartureTime.time())
        result['edtArrivalDate'] = toISO(self.edtArrivalDate.date())
        result['edtArrivalTime'] = toISO(self.edtArrivalTime.time())
        result['edtFinishServiceDate'] = toISO(self.edtFinishServiceDate.date())
        result['edtFinishServiceTime'] = toISO(self.edtFinishServiceTime.time())
        result['cmbDispatcher'] = self.cmbDispatcher.value()
        result['cmbGuidePerson'] = self.cmbGuidePerson.value()
        result['cmbOrderEvent'] = self.cmbOrderEvent.currentIndex()
        result['edtNumberEpidemic'] = unicode(self.edtNumberEpidemic.text())
        result['edtOrderNumber'] = unicode(self.edtOrderNumber.text())
        result['cmbTypeAsset'] = self.cmbTypeAsset.value()
        result['cmbPlaceReceptionCall'] = self.cmbPlaceReceptionCall.value()
        result['cmbReceivedCall'] = self.cmbReceivedCall.value()
        result['cmbReasondDelays'] = self.cmbReasondDelays.value()
        result['cmbResultCircumstanceCall'] = self.cmbResultCircumstanceCall.value()
        result['chkDisease'] = self.chkDisease.isChecked()
        result['chkBirth'] = self.chkBirth.isChecked()
        result['chkPregnancy'] = self.chkPregnancy.isChecked()
        result['chkPregnancyFailure'] = self.chkPregnancyFailure.isChecked()
        result['cmbAccident'] = self.cmbAccident.value()
        result['cmbDeath'] = self.cmbDeath.value()
        result['cmbEbriety'] = self.cmbEbriety.value()
        result['cmbDiseased'] = self.cmbDiseased.value()
        result['cmbPlaceCall'] = self.cmbPlaceCall.value()
        result['cmbMethodTransportation'] = self.cmbMethodTransportation.value()
        result['cmbTransferredTransportation'] = self.cmbTransferredTransportation.value()
        result['cmbOrgId'] = self.cmbOrgId.value()
        result['cmbLocCity'] = str(self.cmbLocCity.code())
        result['cmbLocStreet'] = str(self.cmbLocStreet.code())
        result['edtLocHouse'] = unicode(self.edtLocHouse.text())
        result['edtLocCorpus'] = unicode(self.edtLocCorpus.text())
        result['edtLocFlat'] = unicode(self.edtLocFlat.text())
        result['grpRenunOfHospital'] = self.grpRenunOfHospital.isChecked()
        result['edtFaceRenunOfHospital'] = unicode(self.edtFaceRenunOfHospital.text())
    if self.eventTypeForm == u'131':
        result['cmbWorkOrganisation'] = self.cmbWorkOrganisation.value()
        result['edtWorkPost'] = unicode(self.edtWorkPost.text())
        result['cmbWorkOKVED'] = self.cmbWorkOKVED.value()
        result['edtWorkStage'] = self.edtWorkStage.value()
        result['edtPrevDate'] = toISO(self.edtPrevDate.date())
    return result


def _deserializeEventTokenPage(self, data):
    # assert isinstance(self, CEventEditDialog)
    self.edtBegDate.setDate(fromISO(QDate, data['edtBegDate']))
    self.edtBegTime.setTime(fromISO(QTime, data['edtBegTime']))
    self.edtEndDate.setDate(fromISO(QDate, data['edtEndDate']))
    self.edtEndTime.setTime(fromISO(QTime, data['edtEndTime']))
    if hasattr(self, 'cmbPerson'):
        self.cmbPerson.setValue(data['cmbPerson'])
    if hasattr(self, 'cmbContract'):
        self.cmbContract.setValue(data['cmbContract'])
    if hasattr(self, 'chkPrimary'):
        self.chkPrimary.setChecked(data['chkPrimary'])
    if hasattr(self, 'cmbOrder'):
        self.cmbOrder.setCurrentIndex(data['cmbOrder'])
    if hasattr(self, 'cmbResult'):
        self.cmbResult.setValue(data['cmbResult'])
    if hasattr(self, 'edtNextDate'):
        self.edtNextDate.setDate(fromISO(QDate, data['edtNextDate']))
    if hasattr(self, 'edtNextTime'):
        self.edtNextTime.setTime(fromISO(QTime, data['edtNextTime']))
    if hasattr(self, 'cmbPrimary'):
        self.cmbPrimary.setCurrentIndex(data['cmbPrimary'])
    if hasattr(self, 'edtPregnancyWeek'):
        self.edtPregnancyWeek.setValue(data['edtPregnancyWeek'])
    if hasattr(self, 'cmbClientRelationConsents'):
        self.cmbClientRelationConsents.setValue(data['cmbClientRelationConsents'])
    if hasattr(self, 'edtEventExternalIdValue'):
        self.edtEventExternalIdValue.setText(data['edtEventExternalIdValue'])
    if self.eventTypeForm == u'001':
        self.cmbSetPerson.setValue(data['cmbSetPerson'])
        self.chkConstraintActionTypes.setChecked(data['chkConstraintActionTypes'])
        self.cmbMKB.setText(data['cmbMKB'])
        self.chkDiagnosisType.setChecked(data['chkDiagnosisType'])
        self.cmbMKBEx.setText(data['cmbMKBEx'])
        self.cmbMorphology.setText(data['cmbMorphology'])
        self.cmbCharacter.setValue(data['cmbCharacter'])
        self.cmbTraumaType.setValue(data['cmbTraumaType'])
        self.cmbToxicSubstances.setValue(data['cmbToxicSubstances'])
        self.cmbTNMS.setValue(data['cmbTNMS'])
        self.cmbExecPerson.setValue(data['cmbExecPerson'])
        bs = self.cmbDiagnosticResult.blockSignals(True)
        self.cmbDiagnosticResult.setValue(data['cmbDiagnosticResult'])
        self.cmbDiagnosticResult.blockSignals(bs)
        self.edtFreeInput.setText(data['edtFreeInput'])
        self.cmbTissueType.setValue(data['cmbTissueType'])
        self.edtTissueDate.setDate(fromISO(QDate, data['edtTissueDate']))
        self.edtTissueTime.setTime(fromISO(QTime, data['edtTissueTime']))
        self.cmbTissueExecPerson.setValue(data['cmbTissueExecPerson'])
        self.edtTissueAmount.setValue(data['edtTissueAmount'])
        self.cmbTissueUnit.setValue(data['cmbTissueUnit'])
        self.edtTissueExternalId.setText(data['edtTissueExternalId'])
        self.edtTissueNumber.setText(data['edtTissueNumber'])
        self.edtTissueNote.setText(data['edtTissueNote'])
    elif self.eventTypeForm == u'027':
        self.cmbRelegateOrg.setValue(data['cmbRelegateOrg'])
        self.cmbPatientModel.setValue(data['cmbPatientModel'])
        self.cmbCureType.setValue(data['cmbCureType'])
        self.cmbCureMethod.setValue(data['cmbCureMethod'])
        self.cmbEventCurator.setValue(data['cmbEventCurator'])
        self.cmbPersonMedicineHead.setValue(data['cmbPersonMedicineHead'])
        self.cmbPersonManager.setValue(data['cmbPersonManager'])
        self.cmbPersonExpert.setValue(data['cmbPersonExpert'])
        self.cmbEventAssistant.setValue(data['cmbEventAssistant'])
    elif self.eventTypeForm == u'043':
        self.cmbDentitionBite.setValue(data['cmbDentitionBite'])
        self.cmbDentitionApparat.setValue(data['cmbDentitionApparat'])
        self.cmbDentitionProtezes.setValue(data['cmbDentitionProtezes'])
        self.cmbDentitionOrtodontCure.setValue(data['cmbDentitionOrtodontCure'])
        self.cmbDentitionSanitation.setValue(data['cmbDentitionSanitation'])
        self.cmbDentitionNoTeeth.setValue(data['cmbDentitionNoTeeth'])
        self.edtDentitionObjectively.setValue(data['edtDentitionObjectively'])
        self.edtDentitionMucosa.setValue(data['edtDentitionMucosa'])
        self.edtDentitionNote.setPlainText(data['edtDentitionNote'])
        # переключаемся на последнюю запись в истории
        index = self.modelClientDentitionHistory.index(self.modelClientDentitionHistory.rowCount()-1, 0)
        self.tblClientDentitionHistory.setCurrentIndex(index)
        item = self.modelClientDentitionHistory.getItem(index)
        action = item[1] # type: CActionInfo
        for name, value in data['toothProperties'].iteritems():
            action.getProperty(name).setValue(value)
    elif self.eventTypeForm == u'090':
        self.edtDirectionDate.setDate(fromISO(QDate, data['edtDirectionDate']))
        self.edtDirectionTime.setTime(fromISO(QTime, data['edtDirectionTime']))
        self.chkIsUrgent.setChecked(data['chkIsUrgent'])
        self.cmbSetPerson.setValue(data['cmbSetPerson'])
        self.edtPlannedEndDate.setDate(fromISO(QDate, data['edtPlannedEndDate']))
        self.cmbOrg.setValue(data['cmbOrg'])
        self.cmbStatus.setCurrentIndex(data['cmbStatus'])
        self.edtAmount.setValue(data['edtAmount'])
        self.edtOffice.setText(data['edtOffice'])
        self.cmbAssistant.setValue(data['cmbAssistant'])
        self.edtNote.setText(data['edtNote'])
        self.cmbHurtType.setValue(data['cmbHurtType'])
        self.edtElectronicMedicalBookNumber.setText(data['edtElectronicMedicalBookNumber'])
        self.edtCommentResult.setPlainText(data['edtCommentResult'])
        self.cmbInfoResult.setValue(data['cmbInfoResult'])
        self.edtVisitDateNextResult.setDate(fromISO(QDate, data['edtVisitDateNextResult']))
    elif self.eventTypeForm == u'106':
        self.cmbDeathPlaceType.setValue(data['cmbDeathPlaceType'])
        self.cmbDeathCauseType.setValue(data['cmbDeathCauseType'])
        self.cmbGroundsForDeathCause.setValue(data['cmbGroundsForDeathCause'])
        self.chkAutopsy.setChecked(data['chkAutopsy'])
        self.cmbAutopsyType.setValue(data['cmbAutopsyType'])
        self.cmbOrg.setValue(data['cmbOrg'])
        self.edtNumber.setText(data['edtNumber'])
        self.cmbEmployeeTypeDeterminedDeathCause.setValue(data['cmbEmployeeTypeDeterminedDeathCause'])
        self.cmbPerson2.setValue(data['cmbPerson2'])
        self.chkKLADR.setChecked(data['chkKLADR'])
        self.edtFreeInput.text(data['edtFreeInput'])
        self.cmbCity.setCode(data['cmbCity'])
        self.cmbStreet.setCode(data['cmbStreet'])
        self.edtHouse.setText(data['edtHouse'])
        self.edtCorpus.setText(data['edtCorpus'])
        self.edtFlat.setText(data['edtFlat'])
        self.edtNote.setPlainText(data['edtNote'])
    elif self.eventTypeForm == u'110':
        self.edtNumberCardCall.setText(data['edtNumberCardCall'])
        self.cmbNumberBrigade.setValue(data['cmbNumberBrigade'])
        self.cmbCauseCall.setValue(data['cmbCauseCall'])
        self.edtWhoCallOnPhone.setText(data['edtWhoCallOnPhone'])
        self.edtNumberPhone.setText(data['edtNumberPhone'])
        self.edtStorey.setText(data['edtStorey'])
        self.edtEntrance.setText(data['edtEntrance'])
        self.cmbOrgStructure.setValue(data['cmbOrgStructure'])
        self.edtAdditional.setPlainText(data['edtAdditional'])
        self.edtPassDate.setDate(fromISO(QDate, data['edtPassDate']))
        self.edtPassTime.setTime(fromISO(QTime, data['edtPassTime']))
        self.edtDepartureDate.setDate(fromISO(QDate, data['edtDepartureDate']))
        self.edtDepartureTime.setTime(fromISO(QTime, data['edtDepartureTime']))
        self.edtArrivalDate.setDate(fromISO(QDate, data['edtArrivalDate']))
        self.edtArrivalTime.setTime(fromISO(QTime, data['edtArrivalTime']))
        self.edtFinishServiceDate.setDate(fromISO(QDate, data['edtFinishServiceDate']))
        self.edtFinishServiceTime.setTime(fromISO(QTime, data['edtFinishServiceTime']))
        self.cmbDispatcher.setValue(data['cmbDispatcher'])
        self.cmbGuidePerson.setValue(data['cmbGuidePerson'])
        self.cmbOrderEvent.setCurrentIndex(data['cmbOrderEvent'])
        self.edtNumberEpidemic.setText(data['edtNumberEpidemic'])
        self.edtOrderNumber.setText(data['edtOrderNumber'])
        self.cmbTypeAsset.setValue(data['cmbTypeAsset'])
        self.cmbPlaceReceptionCall.setValue(data['cmbPlaceReceptionCall'])
        self.cmbReceivedCall.setValue(data['cmbReceivedCall'])
        self.cmbReasondDelays.setValue(data['cmbReasondDelays'])
        self.cmbResultCircumstanceCall.setValue(data['cmbResultCircumstanceCall'])
        self.chkDisease.setChecked(data['chkDisease'])
        self.chkBirth.setChecked(data['chkBirth'])
        self.chkPregnancy.setChecked(data['chkPregnancy'])
        self.chkPregnancyFailure.setChecked(data['chkPregnancyFailure'])
        self.cmbAccident.setValue(data['cmbAccident'])
        self.cmbDeath.setValue(data['cmbDeath'])
        self.cmbEbriety.setValue(data['cmbEbriety'])
        self.cmbDiseased.setValue(data['cmbDiseased'])
        self.cmbPlaceCall.setValue(data['cmbPlaceCall'])
        self.cmbMethodTransportation.setValue(data['cmbMethodTransportation'])
        self.cmbTransferredTransportation.setValue(data['cmbTransferredTransportation'])
        self.cmbOrgId.setValue(data['cmbOrgId'])
        self.cmbLocCity.setCode(data['cmbLocCity'])
        self.cmbLocStreet.setCode(data['cmbLocStreet'])
        self.edtLocHouse.setText(data['edtLocHouse'])
        self.edtLocCorpus.setText(data['edtLocCorpus'])
        self.edtLocFlat.setText(data['edtLocFlat'])
        self.grpRenunOfHospital.setChecked(data['grpRenunOfHospital'])
        self.edtFaceRenunOfHospital.setText(data['edtFaceRenunOfHospital'])
    if self.eventTypeForm == u'131':
        self.cmbWorkOrganisation.setValue(data['cmbWorkOrganisation'])
        self.edtWorkPost.setText(data['edtWorkPost'])
        self.cmbWorkOKVED.setValue(data['cmbWorkOKVED'])
        self.edtWorkStage.setValue(data['edtWorkStage'])
        self.edtPrevDate.setDate(fromISO(QDate, data['edtPrevDate']))


def _serializeTable(table):
    # assert isinstance(table.model(), CRecordListModel)
    rows = []
    for record in table.model().items():
        rows.append(_serializeRecord(record))
    return rows


def _deserializeTable(table, rows):
    # assert isinstance(table.model(), CRecordListModel)
    records = [_deserializeRecord(row) for row in rows]
    if records:
        table.model().setItems(records)


def _serializeVariant(v):
    # assert isinstance(v, QVariant)
    if v.isNull():
        return None
    if v.type() in (QVariant.Date, QVariant.Time, QVariant.DateTime):
        dt = v.toDateTime()
        if dt.isNull():
            return None
        return toISO(dt)
    if v.type() == QVariant.String:
        return unicode(v.toString())
    if v.type() in (QVariant.Int, QVariant.Double, QVariant.Bool):
        return v.toPyObject()
    if v.type() == QVariant.Image:
        image = v.toPyObject()
        ba = QByteArray()
        buffer = QBuffer(ba)
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, 'PNG')
        # во втором питоне bytes == str, поэтому делаем костыль
        return 'qimage:' + str(buffer.data().toBase64().data())
    assert False, 'cannot serialize variant type "%s"' % v.typeName()


def _deserializeVariant(data):
    # во втором питоне bytes == str, поэтому делаем костыль
    if isinstance(data, basestring):
        if data.startswith('qimage:'):
            ba = QByteArray.fromBase64(data[7:])
            image = QtGui.QImage.fromData(ba, 'PNG')
            return toVariant(image)
    return toVariant(data)


def _serializeRecord(record):
    result = {}
    for i in xrange(record.count()):
        fieldName = unicode(record.fieldName(i))
        value = _serializeVariant(record.value(fieldName))
        result[fieldName] = value
    return result


def _deserializeRecord(data):
    record = QSqlRecord()
    for fieldName, value in data.iteritems():
        var = _deserializeVariant(value)
        record.append(QSqlField(fieldName, var.type()))
        record.setValue(fieldName, var)
    return record


def toISO(dateValue):
    # На типы QDate и встроенные datetime ругается json.dumps, что они не сериализуются.
    # Переводим в строку в формате ISO.
    # assert isinstance(dateValue, (QDate, QTime))
    return str(dateValue.toString(Qt.ISODate))


def fromISO(type_, dateValueISO):
    # Переводим строку в формате ISO в указанный тип (type_ должен быть QDate или QTime)
    # assert type_ in (QDate, QTime)
    return type_.fromString(dateValueISO, Qt.ISODate)
