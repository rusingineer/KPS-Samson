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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, QVariant, QDateTime

from Events.EventInfo import CEventInfo
from Events.Utils import sendTempInvalidDocuments
from library.DialogBase import CConstructHelperMixin
from library.PrintInfo import CInfoContext
from library.database   import CTableRecordCache
from library.InDocTable import CInDocTableModel, CBoolInDocTableCol, CRBInDocTableCol, CDateInDocTableCol, CEnumInDocTableCol, CInDocTableCol
from library.Utils      import forceRef, forceString, toVariant
from library.PreferencesMixin import CPreferencesMixin
from RefBooks.TempInvalidState    import CTempInvalidState
from Registry.Utils     import getRightEditTempInvalid, getClientMiniInfo
from Events.TempInvalidEditDialog import CTempInvalidCreateDialog, CTempInvalidEditDialog, titleList, getTempInvalidIdOpen
from Events.TempInvalidInfo import CTempInvalidInfo

from Events.Ui_TempInvalid import Ui_grpTempInvalid


class CTempInvalid(QtGui.QGroupBox, CConstructHelperMixin, CPreferencesMixin, Ui_grpTempInvalid):
    def __init__(self, parent=None):
        QtGui.QGroupBox.__init__(self, parent)
        self.eventEditor = None
        self.addObject('modelTempInvalidPrivate', CTempInvalidPrivateModel(self))
        self.addObject('modelTempInvalidPatronage', CTempInvalidPatronageModel(self))
        self.setupUi(self)
        self.tblTempInvalidPrivate.setModel(self.modelTempInvalidPrivate)
        self.tblTempInvalidPrivate.setAlternatingRowColors(False)
        self.tblTempInvalidPatronage.setModel(self.modelTempInvalidPatronage)
        self.tblTempInvalidPatronage.setAlternatingRowColors(False)
        self.tblTempInvalidPrivate.enableColsHide()
        self.tblTempInvalidPrivate.enableColsMove()
        self.tblTempInvalidPatronage.enableColsHide()
        self.tblTempInvalidPatronage.enableColsMove()
        self.addPopupEditTempInvalidPrivate()
        self.addPopupEditTempInvalidPatronage()
        self.addPopupShowClosedTempInvalidPrivate()
        self.addPopupShowClosedTempInvalidPatronage()
        self.connect(self.tblTempInvalidPrivate._popupMenu, SIGNAL('aboutToShow()'), self.on_popupMenuTempInvalidPrivate_aboutToShow)
        self.connect(self.tblTempInvalidPatronage._popupMenu, SIGNAL('aboutToShow()'), self.on_popupMenuTempInvalidPatronage_aboutToShow)


    def loadPreferences(self, prefs):
        policy = forceString(prefs.get('tempinvalid_showpolicy', 'onlyOpened'))
        policyPatronage = forceString(prefs.get('tempinvalid_showpolicypatronage', 'onlyOpened'))
        if policy == 'showAll':
            self.actShowAllTempInvalidPrivate.setChecked(True)
        elif policy == 'showClosed':
            self.actShowClosedTempInvalidPrivate.setChecked(True)
        if policyPatronage == 'showAll':
            self.actShowAllTempInvalidPatronage.setChecked(True)
        elif policyPatronage == 'showClosed':
            self.actShowClosedTempInvalidPatronage.setChecked(True)
        self.modelTempInvalidPrivate.setShowPolicy(policy)
        self.modelTempInvalidPatronage.setShowPolicy(policyPatronage)


    def savePreferences(self):
        return {'tempinvalid_showpolicy': self.modelTempInvalidPrivate._showPolicy,
                'tempinvalid_showpolicypatronage': self.modelTempInvalidPatronage._showPolicy
                }


    def on_popupMenuTempInvalidPrivate_aboutToShow(self):
        table = self.tblTempInvalidPrivate
        model = self.modelTempInvalidPrivate
        self.actEditTempInvalidPrivate.setEnabled(bool(self.popupMenuTempInvalidId(table, model)))


    def on_popupMenuTempInvalidPatronage_aboutToShow(self):
        table = self.tblTempInvalidPatronage
        model = self.modelTempInvalidPatronage
        self.actEditTempInvalidPatronage.setEnabled(bool(self.popupMenuTempInvalidId(table, model)))


    def popupMenuTempInvalidId(self, table, model):
        table.on_popupMenu_aboutToShow()
        row = table.currentIndex().row()
        # rowCount = model.realRowCount() if hasattr(model, 'realRowCount') else model.rowCount()
        record = model._items[row] if 0 <= row < len(model._items) else None
        return forceRef(record.value('id')) if record else None


    def addPopupEditTempInvalidPrivate(self):
        if self.tblTempInvalidPrivate._popupMenu is None:
            self.tblTempInvalidPrivate.createPopupMenu()
        self.actEditTempInvalidPrivate = QtGui.QAction(u'Редактировать (F4)', self)
        self.actEditTempInvalidPrivate.setObjectName('actEditTempInvalidPrivate')
        self.tblTempInvalidPrivate._popupMenu.addAction(self.actEditTempInvalidPrivate)
        self.connect(self.actEditTempInvalidPrivate, SIGNAL('triggered()'), self.on_actEditTempInvalidPrivate_triggered)
        self.addObject('qshcEditTempInvalidPrivate', QtGui.QShortcut('F4', self.tblTempInvalidPrivate, self.on_actEditTempInvalidPrivate_triggered))
        self.qshcEditTempInvalidPrivate.setContext(Qt.WidgetShortcut)


    def addPopupEditTempInvalidPatronage(self):
        if self.tblTempInvalidPatronage._popupMenu is None:
            self.tblTempInvalidPatronage.createPopupMenu()
        self.actEditTempInvalidPatronage = QtGui.QAction(u'Редактировать (F4)', self)
        self.actEditTempInvalidPatronage.setObjectName('actEditTempInvalidPatronage')
        self.tblTempInvalidPatronage._popupMenu.addAction(self.actEditTempInvalidPatronage)
        self.connect(self.actEditTempInvalidPatronage, SIGNAL('triggered()'), self.on_actEditTempInvalidPatronage_triggered)
        self.addObject('qshcEditTempInvalidPatronage', QtGui.QShortcut('F4', self.tblTempInvalidPatronage, self.on_actEditTempInvalidPatronage_triggered))
        self.qshcEditTempInvalidPatronage.setContext(Qt.WidgetShortcut)


    def addPopupShowClosedTempInvalidPrivate(self):
        if self.tblTempInvalidPrivate._popupMenu is None:
            self.tblTempInvalidPrivate.createPopupMenu()
        self.actShowClosedTempInvalidPrivate = QtGui.QAction(u'Отображать по событию', self)
        self.actShowClosedTempInvalidPrivate.setObjectName('actShowClosedTempInvalidPrivate')
        self.actShowClosedTempInvalidPrivate.setCheckable(True)
        self.actShowAllTempInvalidPrivate = QtGui.QAction(u'Отображать ретроспективно', self)
        self.actShowAllTempInvalidPrivate.setObjectName('actShowAllTempInvalidPrivate')
        self.actShowAllTempInvalidPrivate.setCheckable(True)
        self.tblTempInvalidPrivate._popupMenu.addAction(self.actShowClosedTempInvalidPrivate)
        self.tblTempInvalidPrivate._popupMenu.addAction(self.actShowAllTempInvalidPrivate)
        self.connect(self.actShowClosedTempInvalidPrivate, SIGNAL('triggered()'),
                     self.on_actShowClosedTempInvalidPrivate_triggered)
        self.connect(self.actShowAllTempInvalidPrivate, SIGNAL('triggered()'),
                     self.on_actShowAllTempInvalidPrivate_triggered)


    def addPopupShowClosedTempInvalidPatronage(self):
        if self.tblTempInvalidPatronage._popupMenu is None:
            self.tblTempInvalidPatronage.createPopupMenu()
        self.actShowClosedTempInvalidPatronage = QtGui.QAction(u'Отображать по событию', self)
        self.actShowClosedTempInvalidPatronage.setObjectName('actShowClosedTempInvalidPatronage')
        self.actShowClosedTempInvalidPatronage.setCheckable(True)
        self.actShowAllTempInvalidPatronage = QtGui.QAction(u'Отображать ретроспективно', self)
        self.actShowAllTempInvalidPatronage.setObjectName('actShowAlldTempInvalidPatronage')
        self.actShowAllTempInvalidPatronage.setCheckable(True)
        self.tblTempInvalidPatronage._popupMenu.addAction(self.actShowClosedTempInvalidPatronage)
        self.tblTempInvalidPatronage._popupMenu.addAction(self.actShowAllTempInvalidPatronage)
        self.connect(self.actShowClosedTempInvalidPatronage, SIGNAL('triggered()'),
                     self.on_actShowClosedTempInvalidPatronage_triggered)
        self.connect(self.actShowAllTempInvalidPatronage, SIGNAL('triggered()'),
                     self.on_actShowAllTempInvalidPatronage_triggered)


    @pyqtSignature('')
    def on_actEditTempInvalidPrivate_triggered(self):
        currentItem = self.tblTempInvalidPrivate.currentItem()
        tempInvalidId = forceRef(currentItem.value('id')) if currentItem else None
        self.openTempInvalid(tempInvalidId)


    @pyqtSignature('')
    def on_actEditTempInvalidPatronage_triggered(self):
        currentItem = self.tblTempInvalidPatronage.currentItem()
        tempInvalidId = forceRef(currentItem.value('id')) if currentItem else None
        self.openTempInvalid(tempInvalidId)


    @pyqtSignature('')
    def on_actShowClosedTempInvalidPrivate_triggered(self):
        policy = 'onlyOpened'
        if self.actShowClosedTempInvalidPrivate.isChecked():
            self.actShowAllTempInvalidPrivate.setChecked(False)
            policy = 'showClosed'
        self.modelTempInvalidPrivate.setShowPolicy(policy)


    @pyqtSignature('')
    def on_actShowAllTempInvalidPrivate_triggered(self):
        policy = 'onlyOpened'
        if self.actShowAllTempInvalidPrivate.isChecked():
            self.actShowClosedTempInvalidPrivate.setChecked(False)
            policy = 'showAll'
        self.modelTempInvalidPrivate.setShowPolicy(policy)


    @pyqtSignature('')
    def on_actShowClosedTempInvalidPatronage_triggered(self):
        policy = 'onlyOpened'
        if self.actShowClosedTempInvalidPatronage.isChecked():
            self.actShowAllTempInvalidPatronage.setChecked(False)
            policy = 'showClosed'
        self.modelTempInvalidPatronage.setShowPolicy(policy)


    @pyqtSignature('')
    def on_actShowAllTempInvalidPatronage_triggered(self):
        policy = 'onlyOpened'
        if self.actShowAllTempInvalidPatronage.isChecked():
            self.actShowClosedTempInvalidPatronage.setChecked(False)
            policy = 'showAll'
        self.modelTempInvalidPatronage.setShowPolicy(policy)


    def protectFromEdit(self, isProtected):
        widgets = [self.tblTempInvalidPrivate.model(),
                   self.tblTempInvalidPatronage.model()
                  ]
        for widget in widgets:
            widget.setReadOnly(isProtected)


    def destroy(self):
        self.tblTempInvalidPrivate.setModel(None)
        del self.modelTempInvalidPrivate
        self.tblTempInvalidPatronage.setModel(None)
        del self.modelTempInvalidPatronage


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor
        self.modelTempInvalidPrivate.setEventEditor(eventEditor)
        self.modelTempInvalidPatronage.setEventEditor(eventEditor)


    def setType(self, type_, docCode=None):
        self.type_ = type_
        self.docCode = docCode
        self.modelTempInvalidPrivate.setType(self.type_, self.docCode)
        self.modelTempInvalidPatronage.setType(self.type_, self.docCode)


    def pickupTempInvalid(self):
        self.modelTempInvalidPrivate.loadItems(self.eventEditor.clientId)
        self.modelTempInvalidPatronage.loadItems(self.eventEditor.clientId)



    @pyqtSignature('QModelIndex')
    def on_tblTempInvalidPrivate_doubleClicked(self, index):
        self.editTempInvalid(self.tblTempInvalidPrivate, 0)


    @pyqtSignature('QModelIndex')
    def on_tblTempInvalidPatronage_doubleClicked(self, index):
        self.editTempInvalid(self.tblTempInvalidPatronage, 1, True)


    def openTempInvalid(self, tempInvalidId):
        if tempInvalidId and getRightEditTempInvalid(tempInvalidId):
            db = QtGui.qApp.db
            clientId = self.eventEditor.clientId
            clientCache = CTableRecordCache(db, db.forceTable('Client'), u'*', capacity=None)
            dialog = CTempInvalidEditDialog(self, clientCache)
            clientInfo = getClientMiniInfo(clientId)
            dialog.setWindowTitle(titleList[self.type_] + u': ' + clientInfo)
            dialog.setType(self.type_, self.docCode)
            dialog.load(tempInvalidId)
            try:
                if dialog.exec_():
                    # tempInvalidNewId = dialog.itemId()
                    self.modelTempInvalidPrivate.loadItems(clientId)
                    self.modelTempInvalidPatronage.loadItems(clientId)
                sendTempInvalidDocuments(dialog.transfer_tempId_list)
            finally:
                dialog.deleteLater()


    def editTempInvalid(self, table, type = 0, patronage = False):
        currentItem = table.currentItem()
        tempInvalidId = forceRef(currentItem.value('id')) if currentItem else None
        self.getEditorTempInvalid(tempInvalidId, type, patronage)


    def getEditorTempInvalid(self, tempInvalidId, type = 0, patronage = False):
        if tempInvalidId:
            self.openTempInvalid(tempInvalidId)
        else:
            openTempInvalidId = getTempInvalidIdOpen(self.eventEditor.clientId, self.type_, self.docCode)
            if openTempInvalidId:
                self.getEditorTempInvalid(openTempInvalidId, type)
            else:
                self.createTempInvalid(type, patronage)


    def newTempInvalid(self):
        tempInvalidId = getTempInvalidIdOpen(self.eventEditor.clientId, self.type_, self.docCode)
        self.getEditorTempInvalid(tempInvalidId)


    def createTempInvalid(self, type = 0, patronage = False):
        clientId = self.eventEditor.clientId
        eventId = self.eventEditor._id
        context = CInfoContext()
        eventInfo = context.getInstance(CEventInfo, eventId)
        eventMedicalAidType = u'стационар' in eventInfo.eventType.medicalAidType.name.lower()
        if clientId:
            MKBList = self.eventEditor.getFinalDiagnosisMKB() if hasattr(self.eventEditor, 'getFinalDiagnosisMKB') else u''
            MKB = MKBList[0] if len(MKBList) > 1 else MKBList
            db = QtGui.qApp.db
            clientCache = CTableRecordCache(db, db.forceTable('Client'), u'*', capacity=None)
            dialog = CTempInvalidCreateDialog(self, clientId, clientCache, eventId = eventId)
            dialog.setType(self.type_, self.docCode)
            clientInfo = getClientMiniInfo(clientId)
            dialog.setWindowTitle(titleList[self.type_] + u': ' + clientInfo)
            eventSetDateTime = self.eventEditor.eventSetDateTime
            if not QtGui.qApp.userSpecialityId:
                execDate = (
                    eventSetDateTime.date() if isinstance(eventSetDateTime, QDateTime) else eventSetDateTime) if (
                            eventSetDateTime and eventSetDateTime.isValid()) else None
                execPersonId = self.eventEditor.getExecPersonId()
            else:
                execDate = None
                execPersonId = None
            if eventMedicalAidType:
                begDateStationary = QDateTime() if patronage and eventInfo.eventType.form == '003' else eventSetDateTime.date()
                endDateStationary = QDateTime() if patronage and eventInfo.eventType.form == '003' else self.eventEditor.eventDate
                dialog.createTempInvalidDocument(MKB, type=type, execDate=execDate, execPersonId=execPersonId, begDateStationary=begDateStationary, endDateStationary = endDateStationary)
            else:
                dialog.createTempInvalidDocument(MKB, type=type, execDate=execDate, execPersonId=execPersonId)
            if patronage:
                data = {'clientId': clientId, 
                        'tempInvalidRegime_code': (2, u'стационарный') if eventInfo.eventType.form == '003' else (1, u'амбулаторный')}
                if eventInfo.eventType.form == '003':
                    data['begDate'] = self.eventEditor.edtBegDate.date()
                    data['endDate'] = self.eventEditor.edtEndDate.date()
                dialog.newPatronageRecord(data)
            try:
                if dialog.exec_():
                   self.modelTempInvalidPrivate.loadItems(clientId)
                   self.modelTempInvalidPatronage.loadItems(clientId)
                sendTempInvalidDocuments(dialog.transfer_tempId_list)
            finally:
                dialog.deleteLater()


    def getTempInvalidInfo(self, context):
        result = context.getInstance(CTempInvalidInfo, None)
        if result._ok:
            return result
#        if self.isChecked():
#            result._doctype = context.getInstance(CTempInvalidDocTypeInfo,  self.cmbTempInvalidDoctype.value())
#            result._reason  = context.getInstance(CTempInvalidReasonInfo,  self.cmbTempInvalidReason.value())
#            result._extraReason  = context.getInstance(CTempInvalidExtraReasonInfo, forceRef(self.cmbExtraReason.value()))
#            result._busyness = forceInt(self.cmbBusyness.currentIndex())
#            result._placeWork = forceString(self.edtPlaceWork.text())
#            result._serial  = forceStringEx(self.edtTempInvalidSerial.text())
#            result._number  = forceStringEx(self.edtTempInvalidNumber.text())
#            result._sex     = formatSex(self.cmbTempInvalidOtherSex.currentIndex())
#            result._age     = self.edtTempInvalidOtherAge.value()
#            result._receiver= context.getInstance(CClientInfo, self.cmbReceiver.value())
#            result._duration, result._externalDuration = self.modelTempInvalidPeriods.calcLengths()
#            result._begDate = CDateInfo(self.modelTempInvalidPeriods.begDate())
#            result._endDate = CDateInfo(self.modelTempInvalidPeriods.endDate())
#            result._issueDate = CDateInfo(forceDate(self.edtIssueDate.date()))
#            result._accountPregnancyTo12Weeks = forceInt(self.cmbAccountPregnancyTo12Weeks.currentIndex())
#            MKB, MKBEx = self.eventEditor.getFinalDiagnosisMKB()
#            result._MKB = context.getInstance(CMKBInfo, MKB)
#            result._MKBEx = context.getInstance(CMKBInfo, MKBEx)
#            closed = self.modelTempInvalidPeriods.getTempInvalidClosedStatus()
#            result._closed = closed
#            result._periods = self.modelTempInvalidPeriods.getPeriodsInfo(context)
#            if self.prevTempInvalidId:
#                result._prev = context.getInstance(CTempInvalidInfo, self.prevTempInvalidId)
#            else:
#                result._prev = None
#            result._ok = True
#        else:
#            result._ok = False
        result._loaded = True
        return result


class CTempInvalidModel(CInDocTableModel):
    class CLocMKBColumn(CInDocTableCol):
        def __init__(self, title, fieldName, designationChain, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            tableName, fieldName = designationChain
            self.MKBCache = CTableRecordCache(QtGui.qApp.db, tableName, fieldName)

        def toString(self, val, record):
            diagnosisId = forceRef(val)
            if diagnosisId and self.MKBCache:
                MKBRecord = self.MKBCache.get(diagnosisId) if diagnosisId else None
                if MKBRecord:
                    return toVariant(forceString(MKBRecord.value('MKB')))
            return QVariant()

        def invalidateRecordsCache(self):
            self.MKBCache.invalidate()


    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'TempInvalid', 'id', 'client_id', parent)
        self.addCol(CBoolInDocTableCol(u'СтСт',                       'insuranceOfficeMark',                                                                 6)).setReadOnly(True)
        self.addCol(CRBInDocTableCol(  u'Тип',                        'doctype_id',                        15, 'rbTempInvalidDocument'                        )).setReadOnly(True)
        self.addCol(CRBInDocTableCol(  u'Причина нетрудоспособности', 'tempInvalidReason_id',              15, 'rbTempInvalidReason'                          )).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Дата начала ВУТ',            'caseBegDate',                                                                        10)).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Начало',                     'begDate',                                                                            10)).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Окончание',                  'endDate',                                                                            10)).setReadOnly(True)
        self.addCol(CRBInDocTableCol(  u'Врач',                       'person_id',                         15, 'vrbPersonWithSpeciality'                      )).setReadOnly(True)
        self.addCol(CTempInvalidModel.CLocMKBColumn(u'МКБ',           'diagnosis_id',                          ('Diagnosis', 'MKB'),                         6)).setReadOnly(True)
        self.addCol(CEnumInDocTableCol(u'Состояние',                  'state',                              4, CTempInvalidState.names                        )).setReadOnly(True)
        self.addCol(CInDocTableCol(u'Длительность',                   'duration',                                                                            5)).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'В стационаре "с"',           'begDateStationary',                                                                  12)).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'В стационаре "по"',          'endDateStationary',                                                                  12)).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Нарушение режима',             'break_id',                          15, 'rbTempInvalidBreak'                           )).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Дата нарушения режима',      'breakDate',                                                                          12)).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Результат',                    'result_id',                         15, 'rbTempInvalidResult'                          )).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Дата результата - Приступить к работе', 'resultDate',                                                              12)).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Дата результата - Иное',                'resultOtherwiseDate',                                                     12)).setReadOnly(True)
        self.addCol(CInDocTableCol(u'Номер путевки',                             'numberPermit',                                                            12)).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Дата начала путевки',                   'begDatePermit',                                                           12)).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Дата окончания путевки',                'endDatePermit',                                                           12)).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Инвалидность',                            'disability_id',          15, 'rbTempInvalidRegime'                          )).setReadOnly(True)
        self.eventEditor = None
        self.type_ = None
        self.docCode = None
        self.docId = None
        self.filterLoc = ''
        self.filterDoc = ''
        self.readOnly = False
        self.clientId = None
        self._showPolicy = 'onlyOpened'


    def setReadOnly(self, value):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.BackgroundRole:
            row = index.row()
            if len(self._items) > row:
                record = self._items[row]
                if forceRef(record.value('state')):
                    return QVariant(QtGui.QColor(232, 232, 232))
        return CInDocTableModel.data(self, index, role)


    def setType(self, type_, docCode=None):
        self.type_ = type_
        self.docCode = docCode
        self.docId = forceRef(QtGui.qApp.db.translate('rbTempInvalidDocument', 'code', self.docCode, 'id')) if self.docCode else None
        self.filterLoc = u'type=%d' % self.type_
        self.filterDoc = (self.filterLoc + u' AND code=\'%s\'' % self.docCode) if self.docCode else self.filterLoc


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setShowPolicy(self, showPolicy, reloadItems = True):
        self._showPolicy = showPolicy
        if reloadItems:
            self.loadItems(self.clientId)


class CTempInvalidPrivateModel(CTempInvalidModel):
    def loadItems(self, clientId):
        items = []
        self.clientId = clientId
        db = QtGui.qApp.db
        tableTempInvalid = db.table('TempInvalid')
        tableRBTempInvalidResult = db.table('rbTempInvalidResult')
        cond = [tableTempInvalid['deleted'].eq(0),
                tableTempInvalid['client_id'].eq(self.clientId),
                tableTempInvalid['type'].eq(self.type_)
                ]
        if self._showPolicy == 'showClosed':
            begDate = self.eventEditor.edtBegDate.date()
            endDate = self.eventEditor.edtEndDate.date()
            cond.append(tableTempInvalid['endDate'].ge(begDate))
            if endDate:
                cond.append(tableTempInvalid['begDate'].le(endDate))
        elif self._showPolicy == 'onlyOpened':
            cond.append(tableRBTempInvalidResult['state'].eq(0))
            cond.append(tableTempInvalid['state'].eq(0))
            cond.append(tableRBTempInvalidResult['able'].ne(1))
        if self.docCode:
            tableRBTempInvalidDocument = db.table('rbTempInvalidDocument')
            cond.append(tableRBTempInvalidDocument['code'].eq(self.docCode))
            table = tableTempInvalid.leftJoin(tableRBTempInvalidDocument, tableTempInvalid['doctype_id'].eq(tableRBTempInvalidDocument['id']))
        else:
            table = tableTempInvalid
        table = table.leftJoin(tableRBTempInvalidResult, tableRBTempInvalidResult['id'].eq(tableTempInvalid['result_id']))
        recordList = db.getRecordList(table, 'TempInvalid.*', cond, 'TempInvalid.begDate DESC')
        for record in recordList:
            items.append(record)
            tempInvalidId = forceRef(record.value('prev_id'))
            if tempInvalidId and self._showPolicy != 'showAll':
                while tempInvalidId:
                    recordChild = db.getRecordEx(tableTempInvalid, 'TempInvalid.*', [tableTempInvalid['id'].eq(tempInvalidId), tableTempInvalid['deleted'].eq(0)])
                    if recordChild:
                        tempInvalidId = forceRef(recordChild.value('prev_id'))
                        items.append(recordChild)
                    else:
                        tempInvalidId = None
        self.setItems(items)
        self.reset()


class CTempInvalidPatronageModel(CTempInvalidModel):
    def loadItems(self, clientId):
        items = []
        self.clientId = clientId
        db = QtGui.qApp.db
        tableTempInvalid = db.table('TempInvalid')
        tableRBTempInvalidResult = db.table('rbTempInvalidResult')
        tableTempInvalidDocument = db.table('TempInvalidDocument')
        tableTempInvalidDocumentCare = db.table('TempInvalidDocument_Care')
        cond = [tableTempInvalid['deleted'].eq(0),
                tableTempInvalid['client_id'].ne(self.clientId),
                tableTempInvalid['type'].eq(self.type_),
                tableTempInvalidDocumentCare['client_id'].eq(self.clientId)
                ]
        if self._showPolicy == 'showClosed':
            begDate = self.eventEditor.edtBegDate.date()
            endDate = self.eventEditor.edtEndDate.date()
            cond.append(tableTempInvalid['endDate'].ge(begDate))
            if endDate:
                cond.append(tableTempInvalid['begDate'].le(endDate))
        elif self._showPolicy == 'onlyOpened':
            cond.append(tableRBTempInvalidResult['state'].eq(0))
            cond.append(tableTempInvalid['state'].eq(0))
            cond.append(tableRBTempInvalidResult['able'].ne(1))
        if self.docCode:
            tableRBTempInvalidDocument = db.table('rbTempInvalidDocument')
            cond.append(tableRBTempInvalidDocument['code'].eq(self.docCode))
            table = tableTempInvalid.leftJoin(tableRBTempInvalidDocument, tableTempInvalid['doctype_id'].eq(tableRBTempInvalidDocument['id']))
        else:
            table = tableTempInvalid
        table = table.leftJoin(tableRBTempInvalidResult, tableRBTempInvalidResult['id'].eq(tableTempInvalid['result_id']))
        table = table.leftJoin(tableTempInvalidDocument, db.joinAnd([tableTempInvalidDocument['master_id'].eq(tableTempInvalid['id']), tableTempInvalidDocument['deleted'].eq(0)]))
        table = table.innerJoin(tableTempInvalidDocumentCare, tableTempInvalidDocumentCare['master_id'].eq(tableTempInvalidDocument['id']))
        recordList = db.getRecordList(table, 'TempInvalid.*', cond, 'TempInvalid.begDate DESC')
        for record in recordList:
            items.append(record)
            tempInvalidId = forceRef(record.value('prev_id'))
            if tempInvalidId and self._showPolicy != 'showAll':
                while tempInvalidId:
                    recordChild = db.getRecordEx(tableTempInvalid, 'TempInvalid.*', [tableTempInvalid['id'].eq(tempInvalidId), tableTempInvalid['deleted'].eq(0)])
                    if recordChild:
                        tempInvalidId = forceRef(recordChild.value('prev_id'))
                        items.append(recordChild)
                    else:
                        tempInvalidId = None
        self.setItems(items)
        self.reset()
