# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, pyqtSignature, SIGNAL, Qt

from library.database import CTableRecordCache
from library.DialogBase import CConstructHelperMixin
from library.ICDInDocTableCol import CICDExInDocTableCol
from library.InDocTable import CRecordListModel, CTextInDocTableCol, CDateInDocTableCol, CBoolInDocTableCol
from library.PrintTemplates import applyTemplate
from library.Utils import forceRef, forceInt, forceBool, firstMonthDay, toVariant

from Events.AmbulatoryCardDialog import CAmbulatoryCardDialog
from Events.CreateEvent import editEvent
from Events.TempInvalidEditDialog import CTempInvalidEditDialog
from Orgs.Utils import getOrgStructureDescendants, getOrgStructurePersonIdList, getOrgStructureName
from Registry.Utils import getClientContextData, getClientMiniInfo

from Ui_MyDoctorArea import Ui_MyDoctorArea


class CMyDoctorArea(QtGui.QWidget, CConstructHelperMixin, Ui_MyDoctorArea):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.addObject('actFindClient', QtGui.QAction(u'Найти в картотеке', self))
        self.addObject('actShowNotifications', QtGui.QAction(u'Показать уведомления', self))
        self.addObject('actLinkToDoctorPortal', QtGui.QAction(u'Перейти на портал врача', self))
        self.addObject('actOpenAmbulatoryCard', QtGui.QAction(u'Открыть амбулаторную карту', self))
        self.addObject('actEditTempInvalid', QtGui.QAction(u'Открыть эпизод ВУТ', self))
        self.addObject('actEditEvent', QtGui.QAction(u'Открыть событие', self))
        self.setupUi(self)
        self._currentClientId = None
        self._currentTempInvalidId = None
        self.myDoctorsAreaList = []
        self.isNarrowSpec = self.isNarrowSpecialist()
        self.narrowPersonsList = [QtGui.qApp.userId]
        self.clientsWithDn = []
        self.selectClientsWithDN()
        self.chkMyObserved.setChecked(True)
        self.setupMyDoctorsArea()
        self.updateButtonsState()

        # models
        self.modelEmergencyCalls = CSMPTableModel(self)
        self.selectionModelEmergencyCalls = QtGui.QItemSelectionModel(self.modelEmergencyCalls, self)
        # self.modelAmbulanceCalls = CSMPTableModel(self, callType=1)
        # self.selectionModelAmbulanceCalls = QtGui.QItemSelectionModel(self.modelAmbulanceCalls, self)

        self.modelOpenedTempInvalidDocuments = CTempInvalidDocumentTableModel(self, isOpened=True)
        self.selectionModelOpenedTempInvalidDocuments = QtGui.QItemSelectionModel(self.modelOpenedTempInvalidDocuments,
                                                                                  self)
        self.modelForCloseTempInvalidDocuments = CTempInvalidDocumentTableModel(self, isOpened=False)
        self.selectionModelForCloseTempInvalidDocuments = QtGui.QItemSelectionModel(
            self.modelForCloseTempInvalidDocuments, self)

        self.modelDeaths = CDeathsTableModel(self)
        self.selectionModelDeaths = QtGui.QItemSelectionModel(self.modelDeaths, self)
        self.modelLeavedStationary = CLeavedStationaryTableModel(self)
        self.selectionModelLeavedStationary = QtGui.QItemSelectionModel(self.modelLeavedStationary, self)

        self.modelDispansAbsent = CDispansAbsentTableModel(self)
        self.selectionModelDispansAbsent = QtGui.QItemSelectionModel(self.modelDispansAbsent, self)
        self.modelBadTest = CBadTestTableModel(self)
        self.selectionModelBadTest = QtGui.QItemSelectionModel(self.modelBadTest, self)

        # views
        self.tblEmergencyCalls.setModel(self.modelEmergencyCalls)
        self.tblEmergencyCalls.setSelectionModel(self.selectionModelEmergencyCalls)
        # self.tblAmbulanceCalls.setModel(self.modelAmbulanceCalls)
        # self.tblAmbulanceCalls.setSelectionModel(self.selectionModelAmbulanceCalls)

        self.tblOpenedTempInvalidDocuments.setModel(self.modelOpenedTempInvalidDocuments)
        self.tblOpenedTempInvalidDocuments.setSelectionModel(self.selectionModelOpenedTempInvalidDocuments)
        self.tblForCloseTempInvalidDocuments.setModel(self.modelForCloseTempInvalidDocuments)
        self.tblForCloseTempInvalidDocuments.setSelectionModel(self.selectionModelForCloseTempInvalidDocuments)

        self.tblDeaths.setModel(self.modelDeaths)
        self.tblDeaths.setSelectionModel(self.selectionModelDeaths)
        self.tblLeavedStationary.setModel(self.modelLeavedStationary)
        self.tblLeavedStationary.setSelectionModel(self.selectionModelLeavedStationary)

        self.tblDispansAbsent.setModel(self.modelDispansAbsent)
        self.tblDispansAbsent.setSelectionModel(self.selectionModelDispansAbsent)
        self.tblBadTest.setModel(self.modelBadTest)
        self.tblBadTest.setSelectionModel(self.selectionModelBadTest)

        for tableView in [self.tblEmergencyCalls,
                          self.tblOpenedTempInvalidDocuments,
                          self.tblForCloseTempInvalidDocuments,
                          self.tblDeaths,
                          self.tblLeavedStationary,
                          self.tblDispansAbsent,
                          self.tblBadTest]:
            self.connect(tableView, SIGNAL('clicked(QModelIndex)'), self.on_tableViewClicked)

        self.btnNotifications.clicked.connect(self.on_actShowNotifications_triggered)
        self.btnDoctorPortal.clicked.connect(self.on_actLinkToDoctorPortal_triggered)
        self.btnAmbulatoryCard.clicked.connect(self.on_actOpenAmbulatoryCard_triggered)

        # popup
        for tbl in [self.tblEmergencyCalls,  self.tblOpenedTempInvalidDocuments,
                    self.tblForCloseTempInvalidDocuments, self.tblDeaths, self.tblLeavedStationary,
                    self.tblDispansAbsent, self.tblBadTest]:
            tbl.createPopupMenu([self.actFindClient])
            if tbl in [self.tblOpenedTempInvalidDocuments, self.tblForCloseTempInvalidDocuments]:
                tbl.addPopupAction(self.actEditTempInvalid)

        self.tblBadTest.addPopupAction(self.actEditEvent)
        if QtGui.qApp.visibleMyDoctorArea:
            self.reloadData(self.edtDate.date())

        self.chkSMPColor.setStyleSheet(' QCheckBox::indicator { background-color: '+ CSMPTableModel.ambulanceColor +';}')
        self.chkNMPColor.setStyleSheet(' QCheckBox::indicator { background-color: '+ CSMPTableModel.emergencyColor +';}')
        self.chkSMPActiveColor.setStyleSheet(' QCheckBox::indicator { background-color: '+ CSMPTableModel.ambulanceActiveColor +';}')


    def changeUserId(self):
        self._currentClientId = None
        self._currentTempInvalidId = None
        self.myDoctorsAreaList = []
        self.isNarrowSpec = self.isNarrowSpecialist()
        self.narrowPersonsList = [QtGui.qApp.userId]
        self.clientsWithDn = []
        self.selectClientsWithDN()
        self.chkMyObserved.setChecked(True)
        self.setupMyDoctorsArea()
        self.updateButtonsState()
        if QtGui.qApp.visibleMyDoctorArea:
            self.reloadData(self.edtDate.date())


    def isNarrowSpecialist(self):
        db = QtGui.qApp.db
        currentPersonId = QtGui.qApp.userId
        table = db.table('Person_Order')
        cond = [table['master_id'].eq(forceInt(currentPersonId)),
                table['orgStructure_id'].isNotNull(),
                table['type'].eq(6),
                table['deleted'].eq(0),
                table['validFromDate'].isNotNull(),
                table['date'].isNotNull(),
                table['validToDate'].isNull()]
        isNarrowSpec = db.getIdList(table, idCol='master_id', where=cond)
        if not len(isNarrowSpec):
            self.cmbOrgStructure.setCurrentIndex(0)
            return True
        else:
            return False

    def setupMyDoctorsArea(self):
        db = QtGui.qApp.db
        table = db.table('Person_Order')
        cond = [table['master_id'].eq(forceInt(QtGui.qApp.userId)),
                table['orgStructure_id'].isNotNull(),
                table['type'].eq(6),
                table['deleted'].eq(0),
                table['validFromDate'].isNotNull(),
                table['date'].isNotNull(),
                table['validToDate'].isNull()]
        self.myDoctorsAreaList = db.getIdList(table, idCol='orgStructure_id', where=cond)
        areaNames = []
        for area in self.myDoctorsAreaList:
            areaNames.append(getOrgStructureName(area))
        self.lblMyAreas.setText(u'Мой участок:' + u', '.join(areaNames))

    def selectClientsWithDN(self):
        db = QtGui.qApp.db
        tableDiagnosis = db.table('Diagnosis')
        tableDispanser = db.table('rbDispanser')
        queryTable = tableDiagnosis.leftJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnosis['dispanser_id']))
        cond = [tableDispanser['code'].inlist([1, 2, 6]),
                tableDiagnosis['deleted'].eq(0),
                tableDiagnosis['dispanserPerson_id'].inlist(self.narrowPersonsList)]
        clientList = db.getDistinctIdList(queryTable, idCol=tableDiagnosis['client_id'], where=cond)
        if clientList:
            self.clientsWithDn = clientList



    def on_chkMyObserved_toggled(self, checked):
        self.narrowPersonsList = [QtGui.qApp.userId]
        self.selectClientsWithDN()


    def on_chkOrgStrObserved_toggled(self, checked):
        self.narrowPersonsList = []
        userOrgStructId = QtGui.qApp.userOrgStructureId
        personsList = getOrgStructurePersonIdList(userOrgStructId)
        if len(personsList):
            self.narrowPersonsList = personsList
        self.selectClientsWithDN()


    def on_chkSpecObserved_toggled(self, checked):
        self.narrowPersonsList = []
        db = QtGui.qApp.db
        tablePerson = db.table('Person')
        cond = [tablePerson['deleted'].eq(0),
                u'Person.speciality_id = (SELECT per.speciality_id FROM Person per WHERE per.id = {0})'.format(QtGui.qApp.userId)
                ]
        personIdList = db.getIdList(tablePerson, where=cond)
        if len(personIdList):
            self.narrowPersonsList = personIdList
        self.selectClientsWithDN()

    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        self.chkMyObserved.setDisabled(forceBool(self.cmbOrgStructure.value()))
        self.chkOrgStrObserved.setDisabled(forceBool(self.cmbOrgStructure.value()))
        self.chkSpecObserved.setDisabled(forceBool(self.cmbOrgStructure.value()))
        if self.cmbOrgStructure.currentIndex() == 0:
            if self.chkMyObserved.isChecked():
                self.on_chkMyObserved_toggled(True)
            if self.chkOrgStrObserved.isChecked():
                self.on_chkOrgStrObserved_toggled(True)
            if self.chkSpecObserved.isChecked():
                self.on_chkSpecObserved_toggled(True)


    @pyqtSignature('')
    def on_actFindClient_triggered(self):
        QtGui.qApp.mainWindow.registry.findClient(self.getCurrentClientId())
        QtGui.qApp.mainWindow.registry.tabBeforeRecord.setCurrentIndex(0)

    @pyqtSignature('')
    def on_actShowNotifications_triggered(self):
        QtGui.qApp.mainWindow.registry.findClient(self.getCurrentClientId())
        QtGui.qApp.mainWindow.registry.tabBeforeRecord.setCurrentIndex(2)

    @pyqtSignature('')
    def on_actLinkToDoctorPortal_triggered(self):
        clientId = self.getCurrentClientId()
        result = QtGui.qApp.db.getRecordEx('rbPrintTemplate', 'id',
                                           "`default` LIKE '%/EMK_V3/indexV2.php%' AND deleted = 0")
        if result:
            templateId = result.value('id').toString()
            if templateId:
                data = getClientContextData(clientId)
                QtGui.qApp.call(self, applyTemplate, (self, templateId, data))
            else:
                messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                                               u'Ошибка',
                                               u'Шаблон для перехода на портал врача не найден',
                                               QtGui.QMessageBox.Close)
                messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
                messageBox.exec_()
        else:
            messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Information, u'Ошибка',
                                           u'Шаблон для перехода на портал врача не найден', QtGui.QMessageBox.Close)
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            messageBox.exec_()

    @pyqtSignature('')
    def on_actOpenAmbulatoryCard_triggered(self):
        dialog = None
        try:
            dialog = CAmbulatoryCardDialog(self, clientId=self.getCurrentClientId())
            dialog.exec_()
        finally:
            if dialog:
                dialog.deleteLater()

    @pyqtSignature('')
    def on_actEditTempInvalid_triggered(self):
        db = QtGui.qApp.db
        clientCache = CTableRecordCache(db, db.forceTable('Client'), u'*', capacity=None)
        tempInvalidId = self.getCurrentTempInvalidId()
        clientId = self.getCurrentClientId()
        dialog = CTempInvalidEditDialog(self, clientCache)
        clientInfo = getClientMiniInfo(clientId)
        dialog.setWindowTitle(u'ВУТ: ' + clientInfo)
        dialog.load(tempInvalidId)
        try:
            dialog.exec_()
        finally:
            dialog.deleteLater()

    @pyqtSignature('')
    def on_actEditEvent_triggered(self):
        currentItem = self.tblBadTest.currentItem()
        if currentItem:
            eventId = forceRef(currentItem.value('eventId'))
            if eventId:
                editEvent(self, eventId, readOnly=True)

    def reloadData(self, date):
        try:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            orgStructureId = self.cmbOrgStructure.value()
            if orgStructureId:
                orgStructureList = getOrgStructureDescendants(orgStructureId)
                self.narrowPersonsList = []
            else:
                if self.isNarrowSpec:
                    orgStructureList = None
                else:
                    orgStructureList = self.myDoctorsAreaList
            self.modelEmergencyCalls.loadData(date, orgStructureList, self.isNarrowSpec, self.narrowPersonsList)
            self.lblEmergency.setText(u"Вызовы НМП и СМП: %d" % self.modelEmergencyCalls.realRowCount())
            # self.modelAmbulanceCalls.loadData(date, orgStructureList, self.isNarrowSpec, self.narrowPersonsList)
            # self.lblAmbulance.setText(u"Вызовы СМП: %d" % self.modelAmbulanceCalls.realRowCount())
            self.modelOpenedTempInvalidDocuments.loadData(date, orgStructureList, self.isNarrowSpec, self.narrowPersonsList, self.clientsWithDn)
            self.lblOpenedTempInvalidDocuments.setText(u"Открытые листы нетрудоспособности: %d" % self.modelOpenedTempInvalidDocuments.realRowCount())
            self.modelForCloseTempInvalidDocuments.loadData(date, orgStructureList, self.isNarrowSpec, self.narrowPersonsList, self.clientsWithDn)
            self.lblForCloseTempInvalidDocuments.setText(u"Листы нетрудоспособности ожидают закрытия: %d" % self.modelForCloseTempInvalidDocuments.realRowCount())
            self.modelDeaths.loadData(date, orgStructureList, self.isNarrowSpec, self.narrowPersonsList)
            self.lblDeaths.setText(u"Умершие: %d" % self.modelDeaths.realRowCount())
            self.modelLeavedStationary.loadData(date, orgStructureList, self.isNarrowSpec, self.narrowPersonsList)
            self.lblLeavedStationary.setText(u"Выписаны из стационара: %d" % self.modelLeavedStationary.realRowCount())
            self.modelDispansAbsent.loadData(date, orgStructureList, self.isNarrowSpec, self.narrowPersonsList)
            self.lblDispansAbsent.setText(u"Д-учет, не явившиеся: %d" % self.modelDispansAbsent.realRowCount())
            self.modelBadTest.loadData(date, orgStructureList, self.isNarrowSpec, self.narrowPersonsList)
            self.lblBadTest.setText(u"Анализы с превышением: %d" % self.modelBadTest.realRowCount())
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    def getCurrentClientId(self):
        return self._currentClientId

    def getCurrentTempInvalidId(self):
        return self._currentTempInvalidId

    def setCurrentClientId(self, clientId):
        self._currentClientId = clientId
        self.updateButtonsState()

    def setCurrentTempInvalidId(self, tempInvalidId):
        self._currentTempInvalidId = tempInvalidId

    def updateButtonsState(self):
        enable = bool(self.getCurrentClientId())
        self.btnNotifications.setEnabled(enable)
        self.btnDoctorPortal.setEnabled(enable)
        self.btnAmbulatoryCard.setEnabled(enable)

    @pyqtSignature('')
    def on_btnApply_clicked(self):
        self.reloadData(self.edtDate.date())

    def on_tableViewClicked(self, index):
        if index.isValid():
            for tbl in [self.tblEmergencyCalls,
                        self.tblOpenedTempInvalidDocuments,
                        self.tblForCloseTempInvalidDocuments,
                        self.tblDeaths,
                        self.tblLeavedStationary,
                        self.tblDispansAbsent,
                        self.tblBadTest]:
                if tbl.model() != index.model():
                    tbl.selectionModel().clearSelection()
            clientId = forceRef(index.model().value(index.row(), 'client_id'))
            self.setCurrentClientId(clientId)
            if index.model() in [self.modelOpenedTempInvalidDocuments, self.modelForCloseTempInvalidDocuments]:
                tempInvalidId = forceRef(index.model().value(index.row(), 'id'))
                self.setCurrentTempInvalidId(tempInvalidId)


class CSMPTableModel(CRecordListModel):
    emergencyColor = '#2D8659'
    ambulanceColor =  '#8FFFB0'
    ambulanceActiveColor =  '#55AAFF'

    def __init__(self, parent, callType=0):
        CRecordListModel.__init__(self, parent)
        self.addCol(CTextInDocTableCol(u'ФИО', 'clientName', 100, readOnly=True))
        self.addCol(CTextInDocTableCol(u'Пол', 'sex', 4, readOnly=True))
        self.addCol(CDateInDocTableCol(u'Дата рождения', 'birthDate', 10, readOnly=True, highlightRedDate=False))
        self.addCol(CTextInDocTableCol(u'Причина вызова', 'callOccasion', 150, readOnly=True))
        self.addCol(CTextInDocTableCol(u'Диагноз', 'diseaseBasic', 150, readOnly=True))
        self.addCol(CTextInDocTableCol(u'Адрес вызова', 'address', 150, readOnly=True))
        self.addHiddenCol('client_id')
        self.addHiddenCol('Type')
        self.callType = callType

    def loadData(self, date=QDate().currentDate(), orgStructureIdList=None, isNarrowSpec=False, narrowPersonList=None):
        db = QtGui.qApp.db
        if isNarrowSpec and narrowPersonList:
            table = db.table('smp_callinfo')
            tableClient = db.table('Client')
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tableDiagnostic = db.table('Diagnostic')
            tableDispanser = db.table('rbDispanser')
            tableMedicalAidType = db.table('rbMedicalAidType')
            queryTable = table.leftJoin(tableClient, u"""Client.lastName = smp_callinfo.lastName 
                        AND Client.firstName = smp_callinfo.name
                        AND Client.patrName = smp_callinfo.patronymic
                        AND Client.birthDate BETWEEN smp_callinfo.`callDate` - INTERVAL smp_callinfo.ageYears + 1 year 
                            AND smp_callinfo.`callDate` - INTERVAL smp_callinfo.ageYears - 1 year
                        AND Client.deleted = 0""")
            queryTable = queryTable.leftJoin(tableEvent, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
            queryTable = queryTable.leftJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.leftJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            queryTable = queryTable.leftJoin(tableMedicalAidType, tableMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))

            cond = [table['Type'].inlist([0,1,2]),        #eq(self.callType),
                    table['callDate'].eq(date),
                    tableMedicalAidType['code'].notInlist([1, 7]),
                    tableDispanser['code'].inlist([1, 2, 6]),
                    tableEvent['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableEvent['execPerson_id'].inlist(narrowPersonList),
                    u"""NOT EXISTS(SELECT e.id FROM Event e 
                    LEFT JOIN Diagnostic dc ON dc.event_id = e.id
                    LEFT JOIN rbDispanser rbd ON rbd.id = dc.dispanser_id
                    WHERE rbd.code IN (3, 4, 5) AND dc.diagnosis_id = Diagnostic.diagnosis_id AND Event.execDate < e.setDate AND e.client_id = Client.id
                    )
                    """
                    ]

            cols = ["CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) as clientName",
                    u"IF(Client.sex = 1, 'м', 'ж') as sex",
                    u'smp_callinfo.callOccasion as callOccasion',
                    u'smp_callinfo.diseaseBasic AS diseaseBasic',
                    tableClient['birthDate'],
                    u"""CONCAT_WS(', ', IF(smp_callinfo.settlement = '', NULL, smp_callinfo.settlement),
                      IF(smp_callinfo.street = '', NULL, smp_callinfo.street),
                      IF(smp_callinfo.house is not null, CONCAT('д. ', smp_callinfo.house), NULL),
                      IF(smp_callinfo.houseFract = '', NULL, smp_callinfo.houseFract),
                      IF(smp_callinfo.building = '', NULL, smp_callinfo.building),
                      IF(smp_callinfo.flat = '', NULL, CONCAT('кв. ', smp_callinfo.flat))) AS address""",
                    tableClient['id'].alias('client_id'),
                    u'smp_callinfo.Type as Type']
        else:
            table = db.table('smp_callinfo')
            tableClient = db.table('Client')
            tableClientAttach = db.table('ClientAttach').alias('ca')
            queryTable = table.leftJoin(tableClient, u"""Client.lastName = smp_callinfo.lastName 
                        AND Client.firstName = smp_callinfo.name
                        AND Client.patrName = smp_callinfo.patronymic
                        AND Client.birthDate BETWEEN smp_callinfo.`callDate` - INTERVAL smp_callinfo.ageYears + 1 year 
                            AND smp_callinfo.`callDate` - INTERVAL smp_callinfo.ageYears - 1 year
                        AND Client.deleted = 0""")
            queryTable = queryTable.leftJoin(tableClientAttach, """ca.id = (
                          SELECT MAX(ClientAttach.id)
                                FROM ClientAttach
                                INNER JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
                                WHERE client_id = Client.id
                                  AND ClientAttach.deleted = 0
                                  AND NOT rbAttachType.TEMPORARY)""")
            cond = [table['Type'].inlist([0,1,2]),    #.eq(self.callType),
                    table['callDate'].eq(date),
                    tableClientAttach['orgStructure_id'].inlist(orgStructureIdList)]

            cols = ["CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) as clientName",
                    u'smp_callinfo.callOccasion as callOccasion',
                    u'smp_callinfo.diseaseBasic AS diseaseBasic',
                    u"IF(Client.sex = 1, 'м', 'ж') as sex",
                    tableClient['birthDate'],
                    u"""CONCAT_WS(', ', IF(smp_callinfo.settlement = '', NULL, smp_callinfo.settlement),
                      IF(smp_callinfo.street = '', NULL, smp_callinfo.street),
                      IF(smp_callinfo.house is not null, CONCAT('д. ', smp_callinfo.house), NULL),
                      IF(smp_callinfo.houseFract = '', NULL, smp_callinfo.houseFract),
                      IF(smp_callinfo.building = '', NULL, smp_callinfo.building),
                      IF(smp_callinfo.flat = '', NULL, CONCAT('кв. ', smp_callinfo.flat))) AS address""",
                    tableClient['id'].alias('client_id'),
                    u'smp_callinfo.Type as Type']
        items = db.getRecordListGroupBy(queryTable, cols, where=cond, group='smp_callinfo.id', order='clientName')
        self.setItems(items)

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if role == Qt.BackgroundColorRole:
            if self.value(row,'Type') == 0:
                return toVariant(QtGui.QColor(self.emergencyColor))
            if self.value(row,'Type') == 1:
                return toVariant(QtGui.QColor(self.ambulanceColor))
            if self.value(row,'Type') == 2:
                return toVariant(QtGui.QColor(self.ambulanceActiveColor))

        return CRecordListModel.data(self, index, role)

class CTempInvalidDocumentTableModel(CRecordListModel):

    def __init__(self, parent, isOpened=True):
        CRecordListModel.__init__(self, parent)
        self.isOpened = isOpened

        self.addCol(CTextInDocTableCol(u'ФИО', 'clientName', 80, readOnly=True))
        self.addCol(CTextInDocTableCol(u'Пол', 'sex', 4, readOnly=True))
        self.addCol(CDateInDocTableCol(u'Дата рождения', 'birthDate', 10, readOnly=True, highlightRedDate=False))
        if self.isOpened:
            self.addCol(CDateInDocTableCol(u'Дата выдачи ЛН', 'issueDate', 8, readOnly=True, highlightRedDate=False))
        else:
            self.addCol(CDateInDocTableCol(u'Дата окончания', 'endDate', 8, readOnly=True, highlightRedDate=False))
        self.addCol(CTextInDocTableCol(u'Диагноз', 'MKB', 4, readOnly=True))
        self.addCol(CBoolInDocTableCol(u'Электронный', 'electronic', 4, readOnly=True))
        self.addCol(CBoolInDocTableCol(u'Уход', 'invalidCare', 4, readOnly=True))
        self.addHiddenCol('client_id')

    def loadData(self, date=QDate().currentDate(), orgStructureIdList=None, isNarrowSpec=False, narrowPersonList=None, clientsWithDn=[]):
        db = QtGui.qApp.db
        if isNarrowSpec and narrowPersonList:
            table = db.table('TempInvalidDocument')
            tableTempInvalid = db.table('TempInvalid')
            tableTempInvalidDocumentCare = db.table('TempInvalidDocument_Care')
            tableClient = db.table('Client')
            tableDiagnosis = db.table('Diagnosis')
            tableMKB = db.table('MKB')
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tableDiagnostic = db.table('Diagnostic')
            tableDispanser = db.table('rbDispanser')
            tableMedicalAidType = db.table('rbMedicalAidType')
            tableDs = db.table('Diagnosis').alias('ds2')
            tableDiagnosisE = db.table('Diagnosis').alias('dgns')
            queryTable = table.leftJoin(tableTempInvalid, tableTempInvalid['id'].eq(table['master_id']))
            queryTable = queryTable.leftJoin(tableTempInvalidDocumentCare, tableTempInvalidDocumentCare['master_id'].eq(table['id']))
            queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableTempInvalid['client_id']))
            queryTable = queryTable.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableTempInvalid['diagnosis_id']))
            queryTable = queryTable.leftJoin(tableMKB, u'MKB.DiagID = IF(TempInvalidDocument_Care.id, TempInvalidDocument_Care.MKB, Diagnosis.MKB)')
            # queryTable = queryTable.leftJoin(tableEvent, db.joinOr([tableEvent['client_id'].eq(tableClient['id']), tableEvent['client_id'].eq(tableTempInvalidDocumentCare['client_id'])]))
            queryTable = queryTable.leftJoin(tableEvent, u'Event.client_id = IF(TempInvalidDocument_Care.id, TempInvalidDocument_Care.client_id, Client.id)')

            queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
            queryTable = queryTable.leftJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.leftJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            queryTable = queryTable.leftJoin(tableMedicalAidType, tableMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))

            cond = [table['isExternal'].eq(0),
                    table['annulmentReason_id'].isNull(),
                    table['deleted'].eq(0),
                    tableTempInvalid['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tableMedicalAidType['code'].notInlist([1, 7]),
                    tableDispanser['code'].inlist([1, 2, 6]),
                    tableEvent['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableDiagnostic['person_id'].inlist(narrowPersonList),
                    u"""EXISTS (SELECT dgns.id 
                    FROM Event evt
                      LEFT JOIN Diagnostic dgns ON dgns.event_id = evt.id 
                        AND evt.id = (SELECT MAX(evt2.id) FROM Event evt2
                                    LEFT JOIN Diagnostic dgnstc ON evt2.id = dgnstc.event_id
                                    WHERE dgnstc.diagnosis_id = Diagnostic.diagnosis_id)
                    LEFT JOIN rbDispanser rbdr ON rbdr.id = dgns.dispanser_id
                    LEFT JOIN Diagnosis digns ON dgns.diagnosis_id = digns.id
                    WHERE digns.client_id = IF(TempInvalidDocument_Care.id IS NOT NULL,TempInvalidDocument_Care.client_id, Client.id) 
                    AND rbdr.code IN (1, 2, 6) AND dgns.person_id = Diagnostic.person_id)""",

                    u"""NOT EXISTS(SELECT e.id FROM Event e
                    LEFT JOIN Diagnostic dc ON dc.event_id = e.id
                    LEFT JOIN rbDispanser rbd ON rbd.id = dc.dispanser_id
                    WHERE rbd.code IN (3, 4, 5) AND dc.diagnosis_id = Diagnosis.id AND Event.execDate < e.setDate 
                    AND e.client_id = IF(TempInvalidDocument_Care.id IS NOT NULL,TempInvalidDocument_Care.client_id, Client.id) 
                    )
                    """
                    ]
            if self.isOpened:
                cond.append(table['issueDate'].eq(date))
            else:
                cond.append(tableTempInvalid['state'].eq(0))
                cond.append(tableTempInvalid['endDate'].eq(date))

            cols = ["CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) as clientName",
                    u"IF(Client.sex = 1, 'м', 'ж') as sex",
                    u"IF(TempInvalidDocument_Care.id IS NOT NULL, 1, 0) as invalidCare",
                    u"IF(TempInvalidDocument_Care.id IS NOT NULL, "
                    u"CONCAT_WS(' - ', TempInvalidDocument_Care.MKB, MKB.DiagName), "
                    u"CONCAT_WS(' - ', Diagnosis.MKB, MKB.DiagName)) as MKB",
                    tableClient['birthDate'],
                    table['issueDate'],
                    tableTempInvalid['endDate'],
                    table['electronic'],
                    tableTempInvalid['client_id'],
                    tableTempInvalid['id']]
            items = db.getRecordListGroupBy(queryTable, cols, where=cond, group='TempInvalidDocument.id', order='clientName')
        else:
            table = db.table('TempInvalidDocument')
            tableTempInvalidDocumentCare = db.table('TempInvalidDocument_Care')
            tableTempInvalid = db.table('TempInvalid')
            tableClient = db.table('Client')
            tableClientAttach = db.table('ClientAttach').alias('ca')
            tableDiagnosis = db.table('Diagnosis')
            tableMKB = db.table('MKB')
            queryTable = table.leftJoin(tableTempInvalid, tableTempInvalid['id'].eq(table['master_id']))
            queryTable = queryTable.leftJoin(tableTempInvalidDocumentCare, tableTempInvalidDocumentCare['master_id'].eq(table['id']))
            queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableTempInvalid['client_id']))
            queryTable = queryTable.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableTempInvalid['diagnosis_id']))
            queryTable = queryTable.leftJoin(tableMKB, u'MKB.DiagID = IF(TempInvalidDocument_Care.id, TempInvalidDocument_Care.MKB, Diagnosis.MKB)')
            queryTable = queryTable.leftJoin(tableClientAttach, """ca.id = (
                                  SELECT MAX(ClientAttach.id)
                                        FROM ClientAttach
                                        INNER JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
                                        WHERE 
                                          client_id = IF(TempInvalidDocument_Care.id IS NOT NULL,TempInvalidDocument_Care.client_id, Client.id)
                                          AND ClientAttach.deleted = 0
                                          AND NOT rbAttachType.TEMPORARY)""")
            cond = [table['isExternal'].eq(0),
                    table['annulmentReason_id'].isNull(),
                    table['deleted'].eq(0),
                    tableTempInvalid['deleted'].eq(0),
                    tableClient['deleted'].eq(0)]
            if self.isOpened:
                cond.append(table['issueDate'].eq(date))
            else:
                cond.append(tableTempInvalid['state'].eq(0))
                cond.append(tableTempInvalid['endDate'].eq(date))

            cond.append(tableClientAttach['orgStructure_id'].inlist(orgStructureIdList))

            cols = ["CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) as clientName",
                    u"IF(Client.sex = 1, 'м', 'ж') as sex",
                    u"IF(TempInvalidDocument_Care.id IS NOT NULL, 1, 0) as invalidCare",
                    u"IF(TempInvalidDocument_Care.id IS NOT NULL, "
                    u"CONCAT_WS(' - ', TempInvalidDocument_Care.MKB, MKB.DiagName), "
                    u"CONCAT_WS(' - ', Diagnosis.MKB, MKB.DiagName)) as MKB",
                    tableClient['birthDate'],
                    table['issueDate'],
                    tableTempInvalid['endDate'],
                    table['electronic'],
                    tableTempInvalid['client_id'],
                    tableTempInvalid['id']]
            items = db.getRecordListGroupBy(queryTable, cols, where=cond, group='TempInvalidDocument.id', order='clientName')
        self.setItems(items)


class CDeathsTableModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CTextInDocTableCol(u'ФИО', 'clientName', 100, readOnly=True))
        self.addCol(CTextInDocTableCol(u'Пол', 'sex', 4, readOnly=True))
        self.addCol(CDateInDocTableCol(u'Дата рождения', 'birthDate', 10, readOnly=True, highlightRedDate=False))
        self.addCol(CDateInDocTableCol(u'Дата смерти', 'deathDate', 10, readOnly=True, highlightRedDate=False))
        self.addHiddenCol('client_id')

    def loadData(self, date=QDate().currentDate(), orgStructureIdList=None, isNarrowSpec=False, narrowPersonList=None):
        db = QtGui.qApp.db
        if isNarrowSpec and narrowPersonList:
            table = db.table('demogr_Certificate')
            tableClient = db.table('Client')
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tableDiagnostic = db.table('Diagnostic')
            tableDiagnosis = db.table('Diagnosis')
            tableDispanser = db.table('rbDispanser')
            tableMedicalAidType = db.table('rbMedicalAidType')
            tableDiagnosticE = db.table('Diagnostic').alias('dgn')
            queryTable = table.leftJoin(tableClient, tableClient['id'].eq(table['client_id']))
            queryTable = queryTable.leftJoin(tableEvent, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
            queryTable = queryTable.leftJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            queryTable = queryTable.leftJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            queryTable = queryTable.leftJoin(tableMedicalAidType, tableMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))

            cond = [table['deathDate'].ge(date.addDays(-3)),
                    table['deathDate'].lt(date.addDays(1)),
                    tableClient['deleted'].eq(0),
                    tableMedicalAidType['code'].notInlist([1, 7]),
                    tableDispanser['code'].inlist([1, 2, 6]),
                    tableEvent['execPerson_id'].inlist(narrowPersonList),
                    u"""
                    (Diagnosis.id in (SELECT dgns.id  
                    FROM Event evt
                    LEFT JOIN Diagnostic dgn ON dgn.event_id = evt.id 
                    AND evt.id = (SELECT MAX(evt2.id) FROM Event evt2
                                  LEFT JOIN Diagnostic dgnstc ON evt2.id = dgnstc.event_id
                                  WHERE dgnstc.diagnosis_id = dgn.diagnosis_id)
                    LEFT JOIN Diagnosis dgns ON dgn.diagnosis_id = dgns.id
                    LEFT JOIN rbDispanser rbdr ON rbdr.id = dgns.dispanser_id 
                    WHERE dgns.id = Diagnosis.id 
                                        AND rbdr.code IN (1, 2, 6) 
                                        AND dgn.person_id = Diagnostic.person_id))
                    """,
                    u"""NOT EXISTS(SELECT e.id FROM Event e 
                    LEFT JOIN Diagnostic dc ON dc.event_id = e.id
                    LEFT JOIN rbDispanser rbd ON rbd.id = dc.dispanser_id
                    WHERE rbd.code IN (3, 4, 5) AND dc.diagnosis_id = Diagnostic.diagnosis_id AND Event.execDate < e.setDate AND e.client_id = Client.id
                    )
                    """
                    ]
            cols = [
                "CONCAT_WS(' ', demogr_Certificate.surname, demogr_Certificate.name, demogr_Certificate.patronymic) as clientName",
                u"IF(demogr_Certificate.gender = 0, 'м', 'ж') as sex",
                table['birthDate'],
                table['deathDate'],
                table['client_id']]
            items = db.getDistinctRecordList(queryTable, cols, where=cond, order='demogr_Certificate.deathDate desc')
        else:
            table = db.table('demogr_Certificate')
            tableClient = db.table('Client')
            tableClientAttach = db.table('ClientAttach').alias('ca')
            queryTable = table.leftJoin(tableClient, tableClient['id'].eq(table['client_id']))
            queryTable = queryTable.leftJoin(tableClientAttach, """ca.id = (
                  SELECT MAX(ClientAttach.id)
                        FROM ClientAttach
                        INNER JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
                        WHERE client_id = Client.id
                          AND ClientAttach.deleted = 0
                          AND NOT rbAttachType.TEMPORARY)""")
            cond = [table['deathDate'].ge(date.addDays(-3)),
                    table['deathDate'].lt(date.addDays(1)),
                    tableClient['deleted'].eq(0),
                    tableClientAttach['orgStructure_id'].inlist(orgStructureIdList)]
            cols = [
                "CONCAT_WS(' ', demogr_Certificate.surname, demogr_Certificate.name, demogr_Certificate.patronymic) as clientName",
                u"IF(demogr_Certificate.gender = 0, 'м', 'ж') as sex",
                table['birthDate'],
                table['deathDate'],
                table['client_id']]
            items = db.getRecordList(queryTable, cols, where=cond, order='demogr_Certificate.deathDate desc')
        self.setItems(items)


class CLeavedStationaryTableModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CTextInDocTableCol(u'ФИО', 'clientName', 100, readOnly=True))
        self.addCol(CTextInDocTableCol(u'Пол', 'sex', 4, readOnly=True))
        self.addCol(CDateInDocTableCol(u'Дата рождения', 'birthDate', 10, readOnly=True, highlightRedDate=False))
        self.addCol(CDateInDocTableCol(u'Дата выписки', 'endDate', 10, readOnly=True, highlightRedDate=False))
        self.addCol(CTextInDocTableCol(u'Организация', 'organisation_name', 20, readOnly=True))
        self.addCol(CICDExInDocTableCol(u'Диагноз', 'mkb', 10, readOnly=True))
        self.addCol(CBoolInDocTableCol(u'Д учет', 'DN', 10, readOnly=True))
        self.addHiddenCol('client_id')

    def loadData(self, date=QDate().currentDate(), orgStructureIdList=None, isNarrowSpec=False, narrowPersonList=None):
        db = QtGui.qApp.db
        if isNarrowSpec and narrowPersonList:
            table = db.table('ExternalNotification')
            tableClient = db.table('Client')
            tableMKB = db.table('MKB')
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tableDiagnostic = db.table('Diagnostic')
            tableDiagnosis = db.table('Diagnosis')
            tableDispanser = db.table('rbDispanser')
            tableMedicalAidType = db.table('rbMedicalAidType')
            tableDiagnosisE = db.table('Diagnosis').alias('dgns')
            tableDiagnosticE = db.table('Diagnostic').alias('dgn')
            diagnosticQuery = tableDiagnosticE['person_id'].inlist(narrowPersonList)
            queryTable = table.leftJoin(tableClient, tableClient['id'].eq(table['client_id']))
            queryTable = queryTable.leftJoin(tableMKB, tableMKB['DiagID'].eq(table['mkb']))
            queryTable = queryTable.leftJoin(tableEvent, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
            queryTable = queryTable.leftJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            queryTable = queryTable.leftJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            queryTable = queryTable.leftJoin(tableMedicalAidType, tableMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))
            cond = [tableClient['deleted'].eq(0),
                    table['endDate'].ge(date.addDays(-9)),
                    table['endDate'].lt(date.addDays(1)),
                    table['category_display'].eq(u'стационарный'),
                    tableEvent['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableMedicalAidType['code'].notInlist([1, 7]),
                    tableDispanser['code'].inlist([1, 2, 6]),
                    tableDiagnostic['person_id'].inlist(narrowPersonList),
                    # tableEvent['execPerson_id'].inlist(narrowPersonList),
                    u"""NOT EXISTS(SELECT e.id FROM Event e 
                    LEFT JOIN Diagnostic dc ON dc.event_id = e.id
                    LEFT JOIN rbDispanser rbd ON rbd.id = dc.dispanser_id
                    WHERE rbd.code IN (3, 4, 5) AND dc.diagnosis_id = Diagnostic.diagnosis_id AND Event.execDate < e.setDate 
                    AND e.client_id = Client.id
                    )""",

                    u"""(ExternalNotification.mkb in (SELECT dgns.MKB  
                      FROM Event evt
                           LEFT JOIN Diagnostic dgn ON dgn.event_id = evt.id 
                           AND evt.id = (SELECT MAX(evt2.id) FROM Event evt2
                                        LEFT JOIN Diagnostic dgnstc ON evt2.id = dgnstc.event_id
                                        WHERE dgnstc.diagnosis_id = dgn.diagnosis_id)
                           LEFT JOIN Diagnosis dgns ON dgn.diagnosis_id = dgns.id
                           LEFT JOIN rbDispanser rbdr ON rbdr.id = dgns.dispanser_id 
                      WHERE dgns.id = Diagnosis.id 
                                        AND rbdr.code IN (1, 2, 6) 
                                        AND dgn.person_id = Diagnostic.person_id))
                    """
                    ]
        
            cols = ["CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) as clientName",
                    u"IF(Client.sex = 1, 'м', 'ж') as sex",
                    tableClient['birthDate'],
                    table['endDate'],
                    "CONCAT_WS(' - ', ExternalNotification.mkb, MKB.DiagName) as mkb",
                    table['client_id'],
                    table['orgStructure_id'],
                    table['organisation_name'],
                    """EXISTS(SELECT NULL FROM Diagnosis d
                    left JOIN rbDispanser d1 ON d1.id = d.dispanser_id
                    WHERE d.client_id = Client.`id` AND d.deleted = 0 AND d.MKB = MKB.`DiagID` AND d1.observed = 1) AS 'DN'"""]
            items = db.getRecordListGroupBy(queryTable, cols, where=cond, group='ExternalNotification.id', order='ExternalNotification.endDate desc')
        else:
            table = db.table('ExternalNotification')
            tableClient = db.table('Client')
            tableMKB = db.table('MKB')
            queryTable = table.leftJoin(tableClient, tableClient['id'].eq(table['client_id']))
            queryTable = queryTable.leftJoin(tableMKB, tableMKB['DiagID'].eq(table['mkb']))
            cond = [tableClient['deleted'].eq(0),
                    table['endDate'].ge(date.addDays(-9)),
                    table['endDate'].lt(date.addDays(1)),
                    table['category_display'].eq(u'стационарный'),
                    table['orgStructure_id'].inlist(orgStructureIdList)]

            cols = ["CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) as clientName",
                    u"IF(Client.sex = 1, 'м', 'ж') as sex",
                    tableClient['birthDate'],
                    table['endDate'],
                    "CONCAT_WS(' - ', ExternalNotification.mkb, MKB.DiagName) as mkb",
                    table['client_id'],
                    table['orgStructure_id'],
                    table['organisation_name'],
                    """EXISTS(SELECT NULL FROM Diagnosis d 
    left JOIN rbDispanser d1 ON d1.id = d.dispanser_id
    WHERE d.client_id = Client.`id` AND d.deleted = 0 AND d.MKB = MKB.`DiagID` AND d1.observed = 1) AS 'DN'"""]
            items = db.getRecordList(queryTable, cols, where=cond, order='ExternalNotification.endDate desc')
        self.setItems(items)


class CDispansAbsentTableModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CTextInDocTableCol(u'ФИО', 'clientName', 100, readOnly=True))
        self.addCol(CTextInDocTableCol(u'Пол', 'sex', 4, readOnly=True))
        self.addCol(CDateInDocTableCol(u'Дата рождения', 'birthDate', 10, readOnly=True, highlightRedDate=False))
        self.addCol(CTextInDocTableCol(u'Диагноз', 'mkb', 10, readOnly=True))
        self.addCol(CTextInDocTableCol(u'Плановый период явки', 'curPeriod', 10, readOnly=True))
        self.addCol(CTextInDocTableCol(u'Врач ДН', 'personName', 30, readOnly=True))
        self.addCol(CTextInDocTableCol(u'Специальность', 'specialityName', 15, readOnly=True))
        self.addHiddenCol('client_id')

    def loadData(self, date=QDate().currentDate(), orgStructureIdList=None, isNarrowSpec=False, narrowPersonList=None):
        db = QtGui.qApp.db
        if isNarrowSpec and narrowPersonList:
            tablePP = db.table('ProphylaxisPlanning')
            tablePPType = db.table('rbProphylaxisPlanningType')
            tableClient = db.table('Client')
            tableDiagnosis = db.table('Diagnosis')
            tableMKB = db.table('MKB')
            tableDispanser = db.table('rbDispanser')
            tablePerson = db.table('Person')
            tableSpeciality = db.table('rbSpeciality')

            queryTable = tableDiagnosis.leftJoin(tableClient, tableClient['id'].eq(tableDiagnosis['client_id']))
            queryTable = queryTable.leftJoin(tableMKB, tableMKB['DiagID'].eq(tableDiagnosis['MKB']))
            queryTable = queryTable.leftJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnosis['dispanser_id']))
            queryTable = queryTable.leftJoin(tablePP, [tableDiagnosis['MKB'].eq(tablePP['MKB']),
                                                       tableClient['id'].eq(tablePP['client_id'])])
            queryTable = queryTable.leftJoin(tablePPType, tablePPType['id'].eq(tablePP['prophylaxisPlanningType_id']))
            queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnosis['dispanserPerson_id']))
            queryTable = queryTable.leftJoin(tableSpeciality, tableSpeciality['id'].eq(tablePerson['speciality_id']))

            cond = [tableDispanser['code'].inlist([1, 2, 6]),
                    tablePP['deleted'].eq(0),
                    tableDiagnosis['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tablePPType['code'].eq(u'ДН'),
                    tablePP['visit_id'].isNull(),
                    tablePP['parent_id'].isNotNull(),
                    tableDiagnosis['dispanserPerson_id'].inlist(narrowPersonList),
                    db.joinAnd([tablePP['endDate'].le(date), tablePP['endDate'].ge(firstMonthDay(date).addMonths(-1))])
                    ]

            cols = ["CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) as clientName",
                    "CONCAT_WS(' ', Person.lastName, Person.firstName, Person.patrName) as personName",
                    tableSpeciality['name'].alias('specialityName'),
                    u"IF(Client.sex = 1, 'м', 'ж') as sex",
                    tableClient['birthDate'],
                    "CONCAT_WS(' - ', DATE_FORMAT(ProphylaxisPlanning.begDate, '%d.%m.%Y'), DATE_FORMAT(ProphylaxisPlanning.endDate, '%d.%m.%Y')) as curPeriod",
                    "CONCAT_WS(' - ', Diagnosis.MKB, MKB.DiagName) as MKB",
                    tablePP['client_id']]

            items = db.getRecordListGroupBy(queryTable, cols, where=cond, group='Diagnosis.id', order='clientName, MKB')
        else:
            tablePP = db.table('ProphylaxisPlanning')
            tablePPType = db.table('rbProphylaxisPlanningType')
            tableClient = db.table('Client')
            tableClientAttach = db.table('ClientAttach').alias('ca')
            tableDiagnosis = db.table('Diagnosis')
            tableMKB = db.table('MKB')
            tableDispanser = db.table('rbDispanser')
            tablePerson = db.table('Person')
            tableSpeciality = db.table('rbSpeciality')

            queryTable = tableDiagnosis.leftJoin(tableClient, tableClient['id'].eq(tableDiagnosis['client_id']))
            queryTable = queryTable.leftJoin(tableMKB, tableMKB['DiagID'].eq(tableDiagnosis['MKB']))
            queryTable = queryTable.leftJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnosis['dispanser_id']))
            queryTable = queryTable.leftJoin(tablePP, [tableDiagnosis['MKB'].eq(tablePP['MKB']),
                                                       tableClient['id'].eq(tablePP['client_id'])])
            queryTable = queryTable.leftJoin(tablePPType, tablePPType['id'].eq(tablePP['prophylaxisPlanningType_id']))
            queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnosis['dispanserPerson_id']))
            queryTable = queryTable.leftJoin(tableSpeciality, tableSpeciality['id'].eq(tablePerson['speciality_id']))
            queryTable = queryTable.leftJoin(tableClientAttach, """ca.id = (
                                      SELECT MAX(ClientAttach.id)
                                            FROM ClientAttach
                                            INNER JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
                                            WHERE client_id = Client.id
                                              AND ClientAttach.deleted = 0
                                              AND NOT rbAttachType.TEMPORARY)""")
            cond = [tableDispanser['code'].inlist([1, 2, 6]),
                    tablePP['deleted'].eq(0),
                    tableDiagnosis['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tablePPType['code'].eq(u'ДН'),
                    tablePP['visit_id'].isNull(),
                    tablePP['parent_id'].isNotNull(),
                    tableClientAttach['orgStructure_id'].inlist(orgStructureIdList),
                    db.joinAnd([tablePP['endDate'].le(date), tablePP['endDate'].ge(firstMonthDay(date).addMonths(-1))])
                    ]

            cols = ["CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) as clientName",
                    "CONCAT_WS(' ', Person.lastName, Person.firstName, Person.patrName) as personName",
                    tableSpeciality['name'].alias('specialityName'),
                    u"IF(Client.sex = 1, 'м', 'ж') as sex",
                    tableClient['birthDate'],
                    "CONCAT_WS(' - ', DATE_FORMAT(ProphylaxisPlanning.begDate, '%d.%m.%Y'), DATE_FORMAT(ProphylaxisPlanning.endDate, '%d.%m.%Y')) as curPeriod",
                    "CONCAT_WS(' - ', Diagnosis.MKB, MKB.DiagName) as MKB",
                    tablePP['client_id']]

            items = db.getRecordList(queryTable, cols, where=cond, order='clientName, MKB')
        self.setItems(items)


class CBadTestTableModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CTextInDocTableCol(u'ФИО', 'clientName', 100, readOnly=True))
        self.addCol(CTextInDocTableCol(u'Пол', 'sex', 4, readOnly=True))
        self.addCol(CDateInDocTableCol(u'Дата рождения', 'birthDate', 10, readOnly=True, highlightRedDate=False))
        self.addHiddenCol('client_id')

    def loadData(self, date=QDate().currentDate(), orgStructureIdList=None, isNarrowSpec=False, narrowPersonList=None):
        db = QtGui.qApp.db
        tableClientAttach = db.table('ClientAttach').alias('ca')
        tableEvent = db.table('Event').alias('e')
        orgStructures = ' AND ' + tableClientAttach['orgStructure_id'].inlist(orgStructureIdList)
        personList = ' AND ' + tableEvent['execPerson_id'].inlist(narrowPersonList)
        tableDiagnosisE = db.table('Diagnosis').alias('ds2')
        diagnosisQuery = tableDiagnosisE['dispanserPerson_id'].inlist(narrowPersonList)

        if isNarrowSpec and narrowPersonList:
            stmt = u"""SELECT DISTINCT clientName, sex, birthDate, client_id, eventId
              FROM (select CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) as clientName,
              IF(Client.sex = 1, 'м', 'ж') as sex,
              Client.birthDate,
              at.name AS typeName, apt.name AS propName,
              aps.value AS rawValue,
              CASE WHEN LENGTH(ap.norm) > 0 THEN ap.norm
              WHEN LENGTH(apt.norm) > 0 THEN apt.norm ELSE NULL END AS rawNorm,
              CAST(aps.value AS decimal(19,4)) AS value,
              CASE WHEN LENGTH(ap.norm) > 0
                THEN SUBSTRING_INDEX(ap.norm, '-', 1)
                WHEN LENGTH(apt.norm) > 0
                THEN SUBSTRING_INDEX(apt.norm, '-', 1)
                ELSE NULL END AS refMin,
              CASE WHEN LENGTH(ap.norm) > 0
                THEN SUBSTRING_INDEX(ap.norm, '-',-1)
                WHEN LENGTH(apt.norm) > 0
                THEN SUBSTRING_INDEX(apt.norm, '-', -1)
                ELSE NULL END AS refMax,
                Client.id as client_id,
                e.id AS eventId
            from Action a
              left JOIN Event e ON e.id = a.event_id
              left JOIN Client ON Client.id = e.client_id
            LEFT JOIN EventType ON EventType.id=e.eventType_id 
            LEFT JOIN Diagnostic ON Diagnostic.event_id=e.id 
            LEFT JOIN rbDispanser ON rbDispanser.id=Diagnostic.dispanser_id
            LEFT JOIN rbMedicalAidType ON rbMedicalAidType.id=EventType.medicalAidType_id 
              left JOIN ActionType at on at.id= a.actionType_id
              left JOIN ActionPropertyType apt on apt.actionType_id = at.id
              left JOIN ActionProperty ap on ap.action_id = a.id AND ap.type_id = apt.id
              left JOIN ActionProperty_String aps on aps.id = ap.id
              WHERE a.deleted = 0 AND e.deleted = 0 AND Client.deleted = 0 
               AND apt.deleted = 0
               AND ap.deleted = 0
                AND at.serviceType = 10 
                AND a.endDate >= {date} 
                AND a.endDate < {date2}
                AND ap.id IS NOT NULL 
                AND apt.test_id is not NULL
                AND (ap.norm != ''  or apt.norm != '')
                AND (e.`deleted`=0) 
                AND (rbMedicalAidType.`code` NOT IN ('1','7')) 

                        
                AND EXISTS (SELECT ds2.id 
                FROM Diagnosis ds2 
                LEFT JOIN rbDispanser rbds2 ON rbds2.id = ds2.dispanser_id
                WHERE ds2.client_id = Client.id AND rbds2.`code` IN ('1','2','6') AND {diagnosisQuery})
                AND (NOT EXISTS(SELECT Event.id FROM Event 
                          LEFT JOIN Diagnostic dc ON dc.event_id = Event.id
                          LEFT JOIN rbDispanser rbd ON rbd.id = dc.dispanser_id
                          WHERE rbd.code IN (3, 4, 5) AND dc.diagnosis_id = Diagnostic.diagnosis_id AND e.execDate < Event.setDate AND Event.client_id = Client.id
                    ))
              HAVING value NOT BETWEEN CAST(refMin AS decimal(19,4)) AND CAST(refMax AS decimal(19,4))
            ORDER BY clientName) t""".format(date=db.formatDate(date),
                                             date2=db.formatDate(date.addDays(1)),
                                             orgStructures=orgStructures,
                                             personList=personList,
                                             diagnosisQuery=diagnosisQuery)
        else:
            stmt = u"""SELECT DISTINCT clientName, sex, birthDate, client_id, eventId
      FROM (select CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) as clientName,
      IF(Client.sex = 1, 'м', 'ж') as sex,
      Client.birthDate,
      at.name AS typeName, apt.name AS propName,
      aps.value AS rawValue,
      CASE WHEN LENGTH(ap.norm) > 0 THEN ap.norm
      WHEN LENGTH(apt.norm) > 0 THEN apt.norm ELSE NULL END AS rawNorm,
      CAST(aps.value AS decimal(19,4)) AS value,
      CASE WHEN LENGTH(ap.norm) > 0
        THEN SUBSTRING_INDEX(ap.norm, '-', 1)
        WHEN LENGTH(apt.norm) > 0
        THEN SUBSTRING_INDEX(apt.norm, '-', 1)
        ELSE NULL END AS refMin,
      CASE WHEN LENGTH(ap.norm) > 0
        THEN SUBSTRING_INDEX(ap.norm, '-',-1)
        WHEN LENGTH(apt.norm) > 0
        THEN SUBSTRING_INDEX(apt.norm, '-', -1)
        ELSE NULL END AS refMax,
        Client.id as client_id,
        e.id AS eventId
    from Action a
      left JOIN Event e ON e.id = a.event_id
      left JOIN Client ON Client.id = e.client_id
      left join ClientAttach ca on ca.id = (
                          SELECT MAX(ClientAttach.id)
                                FROM ClientAttach
                                INNER JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
                                WHERE client_id = Client.id
                                  AND ClientAttach.deleted = 0
                                  AND NOT rbAttachType.TEMPORARY)
      left JOIN ActionType at on at.id= a.actionType_id
      left JOIN ActionPropertyType apt on apt.actionType_id = at.id
      left JOIN ActionProperty ap on ap.action_id = a.id AND ap.type_id = apt.id
      left JOIN ActionProperty_String aps on aps.id = ap.id
      WHERE a.deleted = 0 AND e.deleted = 0 AND Client.deleted = 0 
       AND apt.deleted = 0
       AND ap.deleted = 0
        AND at.serviceType = 10 
        AND a.endDate >= {date} 
        AND a.endDate < {date2}
        AND ap.id IS NOT NULL 
        AND apt.test_id is not NULL
        AND (ap.norm != ''  or apt.norm != '')
        {orgStructures}
      HAVING value NOT BETWEEN CAST(refMin AS decimal(19,4)) AND CAST(refMax AS decimal(19,4))
    ORDER BY clientName) t""".format(date=db.formatDate(date),
                                     date2=db.formatDate(date.addDays(1)),
                                     orgStructures=orgStructures)
        items = []
        query = db.query(stmt)
        while query.next():
            items.append(query.record())
        self.setItems(items)
