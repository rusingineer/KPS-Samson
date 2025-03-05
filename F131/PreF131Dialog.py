# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Планировщик формы 131: ДД и т.п.
##
#############################################################################

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, pyqtSignature, QVariant

from library.DialogBase import CDialogBase
from library.InDocTable import CBoolInDocTableCol, CInDocTableModel, CIntInDocTableCol, CRBInDocTableCol
from library.Utils import calcAgeTuple, forceBool, forceDate, forceInt, forceRef, forceString, formatName, formatSex, trim
from library.SortFilterProxyInDocTableModel import CSortFilterProxyInDocTableModel
from Events.Utils import recordAcceptable, getEventPlannedInspections


from Ui_PreF131 import Ui_PreF131Dialog
from library.crbcombobox import CRBComboBox


class CPreF131Dialog(CDialogBase, Ui_PreF131Dialog):
    def __init__(self, parent, personSpecialityId=None):
        CDialogBase.__init__(self,  parent)
        self.__modelDiagnostics = CDiagnosticsModel(self)
        self.__modelDiagnostics.setObjectName('__modelDiagnostics')
        self.__modelActions     = CActionsModel(self)
        self.__modelActions.setObjectName('__modelActions')
        self.__modelSortActions = CSortFilterProxyInDocTableModel(self, self.__modelActions)
        self.__modelSortActions.setObjectName('__modelSortActions')
        self.__modelActions = self.__modelSortActions.sourceModel()
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Планирование осмотра Ф.131')
        self.__clientName      = None
        self.__clientSex       = None
        self.__clientBirthDate = None
        self.__clientAge       = None
        self.tissueTypeId      = None
        self.setEventDate      = None
        self._clientWorkHurtCodeList       = []
        self._clientWorkHurtFactorCodeList = []
        self.personSpecialityId = personSpecialityId
        self.warnAboutUnmatchedSpeciality = False
        self.tblDiagnostics.setModel(self.__modelDiagnostics)
        self.tblDiagnostics.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tblDiagnostics.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblActions.setModel(self.__modelSortActions)
        self.tblActions.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tblActions.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)


    def destroy(self):
        self.tblDiagnostics.setModel(None)
        self.tblActions.setModel(None)
        del self.__modelDiagnostics
        del self.__modelActions


    def setBegDateEvent(self, date):
        self.setEventDate = date


    def prepare(self, clientId, eventTypeId, eventDate, tissueTypeId=None, typeQueue = -1, docNum=None, relegateInfo=[],
                plannedEndDate = None, mapJournalInfoTransfer = [], voucherParams = {}, presentActionTypes = []):
        self.tissueTypeId = tissueTypeId
        self.setClientInfo(clientId, eventDate)
        self.setEventTypeId(eventTypeId, presentActionTypes)


    def setClientInfo(self, clientId, eventDate):
        db = QtGui.qApp.db
        table  = db.table('Client')
        record = db.getRecord(table, 'lastName, firstName, patrName, sex, birthDate', clientId)
        if record:
            lastName  = record.value('lastName')
            firstName = record.value('firstName')
            partName  = record.value('patrName')
            self.__clientName      = formatName(lastName, firstName, partName)
            self.__clientSex       = forceInt(record.value('sex'))
            self.__clientBirthDate = forceDate(record.value('birthDate'))
            self.__clientAge       = calcAgeTuple(self.__clientBirthDate, eventDate)
            if not self.__clientAge:
                self.__clientAge = (0, 0, 0, 0)

            self.setClientWorkHurtCodeList(clientId)

    def setClientWorkHurtCodeList(self, clientId):
        db = QtGui.qApp.db

        tableCW       = db.table('ClientWork')
        tableCWH      = db.table('ClientWork_Hurt')
        tableHurtType = db.table('rbHurtType')

        queryTable = tableCW.leftJoin(tableCWH, tableCWH['master_id'].eq(tableCW['id']))
        queryTable = queryTable.leftJoin(tableHurtType, tableHurtType['id'].eq(tableCWH['hurtType_id']))
        cond = tableCW['client_id'].eq(clientId)
        fieldList = [tableHurtType['code'].name(), tableCWH['id'].name()]
        recordList = db.getRecordList(queryTable, fieldList, cond)

        hurtIdList = []
        for record in recordList:
            self._clientWorkHurtCodeList.append(forceString(record.value('code')))
            hurtIdList.append(forceRef(record.value('id')))

        if hurtIdList:
            self.setClientWorkHurtFactorCodeList(clientId, hurtIdList=hurtIdList)


    def setClientWorkHurtFactorCodeList(self, clientId, hurtIdList=[]):
        db = QtGui.qApp.db

        tableCW             = db.table('ClientWork')
        tableCWH            = db.table('ClientWork_Hurt')
        tableCWHF           = db.table('ClientWork_Hurt_Factor')
        tableHurtFactorType = db.table('rbHurtFactorType')

        if hurtIdList:
            queryTable = tableCWHF.leftJoin(tableHurtFactorType, tableHurtFactorType['id'].eq(tableCWHF['factorType_id']))
            cond = tableCWHF['master_id'].inlist(hurtIdList)
        else:
            queryTable = tableCW.leftJoin(tableCWH, tableCWH['master_id'].eq(tableCW['id']))
            queryTable = tableCWHF.leftJoin(tableCWHF, tableCWHF['master_id'].eq(tableCWH['id']))
            queryTable = tableCWHF.leftJoin(tableHurtFactorType, tableHurtFactorType['id'].eq(tableCWHF['factorType_id']))
            cond = tableCW['client_id'].eq(clientId)

        recordList = db.getRecordList(queryTable, tableHurtFactorType['code'].name(), cond)

        for record in recordList:
            self._clientWorkHurtFactorCodeList.append(forceString(record.value('code')))


    def setEventTypeId(self, eventTypeId, presentActionTypes = []):
        eventTypeRecord = QtGui.qApp.db.getRecord('EventType', ['name'], eventTypeId)
        eventTypeName  = forceString(eventTypeRecord.value('name'))
        title = u'Планирование: %s, Пациент: %s, Пол: %s, ДР.: %s '% (eventTypeName, self.__clientName, formatSex(self.__clientSex), forceString(self.__clientBirthDate))
        QtGui.QDialog.setWindowTitle(self, title)
        self.prepareDiagnostics(eventTypeId)
        self.prepareActions(eventTypeId, presentActionTypes)


    def prepareDiagnostics(self, eventTypeId):
        includedGroups = []
        records = getEventPlannedInspections(eventTypeId)
        model = self.__modelDiagnostics
        self.warnAboutUnmatchedSpeciality = None
        gpSpecialityId = QtGui.qApp.getGPSpecialityId()
        for record in records:
            if self.recordAcceptable(record):
                target = model.getEmptyRecord()
                target.append(QtSql.QSqlField('defaultHealthGroup_id', QVariant.Int))
                target.append(QtSql.QSqlField('defaultDispanser_id', QVariant.Int))
                target.append(QtSql.QSqlField('defaultMKB', QVariant.String))
                target.append(QtSql.QSqlField('mayEngageGP', QVariant.Bool))
                target.setValue('speciality_id',  record.value('speciality_id'))
                target.setValue('visitType_id',   record.value('visitType_id'))
                target.setValue('actuality',      record.value('actuality'))
                target.setValue('selectionGroup', record.value('selectionGroup'))
                target.setValue('defaultDispanser_id', record.value('defaultDispanser_id'))
                target.setValue('defaultHealthGroup_id',  record.value('defaultHealthGroup_id'))
                target.setValue('defaultMKB',     record.value('defaultMKB'))
                target.setValue('mayEngageGP',    record.value('mayEngageGP'))

                selectionGroup = forceInt(record.value('selectionGroup'))
                specialityId   = forceRef(record.value('speciality_id'))
                mayEngageGP    = forceBool(record.value('mayEngageGP'))
                specialityIsMatched = (specialityId == self.personSpecialityId
                                       or mayEngageGP and gpSpecialityId == self.personSpecialityId)
                if selectionGroup <= 0:
                    target.setValue('include',  QVariant(0))
                elif selectionGroup == 1:
                    target.setValue('include',  QVariant(1))
                elif selectionGroup in includedGroups:
                    target.setValue('include',  QVariant(0))
                else:
                    if specialityIsMatched:
                        target.setValue('include',  QVariant(1))
                        includedGroups.append(selectionGroup)
                self.warnAboutUnmatchedSpeciality = (self.warnAboutUnmatchedSpeciality is None
                                                     or self.warnAboutUnmatchedSpeciality) and not specialityIsMatched
                model.items().append(target)
        model.reset()


    def prepareActions(self, eventTypeId, presentActionTypes = []):
        includedGroups = []

        db = QtGui.qApp.db

        table = db.table('EventType_Action')
        tableActionType = db.table('ActionType')
        join = table.leftJoin(tableActionType, tableActionType['id'].eq(table['actionType_id']))
        cond = [table['eventType_id'].eq(eventTypeId), tableActionType['deleted'].eq(0)]
        if presentActionTypes:
            cond.append('''(IF(selectionGroup=1 and ActionType.id in ({}), False, True))'''.format(', '.join(presentActionTypes)))
        records = db.getRecordList(join, 'EventType_Action.*', cond, 'ActionType.class, idx, id')

        for record in records:
            if self.recordAcceptable(record):
                tissueTypeId = forceRef(record.value('tissueType_id'))
                if tissueTypeId and self.tissueTypeId:
                    if self.tissueTypeId != tissueTypeId:
                        continue
                actionTypeId = forceRef(record.value('actionType_id'))
                selectionGroup = forceInt(record.value('selectionGroup'))
                if selectionGroup == -99:
                    continue
                target = self.__modelActions.getEmptyRecord()
                target.setValue('actionType_id',  QVariant(actionTypeId))
                target.setValue('actuality',      record.value('actuality'))
                target.setValue('selectionGroup', record.value('selectionGroup'))

                if selectionGroup <= 0:
                    target.setValue('include',  QVariant(0))
                elif selectionGroup == 1:
                    target.setValue('include',  QVariant(1))
                elif selectionGroup in includedGroups:
                    target.setValue('include',  QVariant(0))
                else:
                    target.setValue('include',  QVariant(1))
                    includedGroups.append(selectionGroup)
                target.setValue('expose', record.value('expose'))
                self.__modelActions.items().append(target)
        self.__modelActions.reset()


    def recordAcceptable(self, record):
        return recordAcceptable(self.__clientSex, self.__clientAge, record, self.setEventDate, self.__clientBirthDate) and self.recordAcceptableByClientHurt(record)


    def recordAcceptableByClientHurt(self, record):
        resultWH = True
        resultWHF = True

        listForChecking = self._getHurtListForChecking(record, 'hurtType')
        if listForChecking:
            resultWH = False
            if self._clientWorkHurtCodeList:
                resultWH = bool(set(self._clientWorkHurtCodeList) & set(listForChecking))

        listForChecking = self._getHurtListForChecking(record, 'hurtFactorType')
        if listForChecking:
            resultWHF = False
            if self._clientWorkHurtFactorCodeList:
                resultWHF = bool(set(self._clientWorkHurtFactorCodeList) & set(listForChecking))

        return resultWH or resultWHF


    def _getHurtListForChecking(self, record, fieldName):
        value = forceString(record.value(fieldName))
        result = [trim(val) for val in value.split(';') if val]
        return result


    def diagnosticsTableIsNotEmpty(self):
        return bool(self.__modelDiagnostics.items())


    def actionsTableIsNotEmpty(self):
        return bool(self.__modelActions.items())


    def diagnostics(self):
        return self.__modelDiagnostics.items()


    def actions(self):
        return self.__modelActions.items()


    def selectionPlanner(self, model, newSelect=0):
        for i, item in enumerate(model.items()):
            selectionGroup = forceInt(item.value('selectionGroup'))
            if selectionGroup == 0:
                item.setValue('include', QVariant(newSelect))
        model.reset()


    @pyqtSignature('')
    def on_btnSelectVisits_clicked(self):
        self.selectionPlanner(self.__modelDiagnostics, 1)


    @pyqtSignature('')
    def on_btnDeselectVisits_clicked(self):
        self.selectionPlanner(self.__modelDiagnostics, 0)


    @pyqtSignature('')
    def on_btnSelectActions_clicked(self):
        self.selectionPlanner(self.__modelActions, 1)


    @pyqtSignature('')
    def on_btnDeselectActions_clicked(self):
        self.selectionPlanner(self.__modelActions, 0)


    @pyqtSignature('QString')
    def on_edtNameFilter_textChanged(self, text):
        self.__modelSortActions.setNameFilter(unicode(text))


class CPreModel(CInDocTableModel):
    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole:
            # column = index.column()
            row = index.row()
            group = forceInt(self.items()[row].value('selectionGroup'))
            newState = 1 if forceInt(value) == Qt.Checked else 0
            if group > 0:
                newState = 1
            if group == 0:  # нулевая группа - всегда переключается
                return CInDocTableModel.setData(self, index, value, role)
            if group == 1:  # первая группа - никогда не переключается
                return False
            for itemIndex, item in enumerate(self.items()):
                itemGroup = forceInt(item.value('selectionGroup'))
                if itemGroup == group:
                    item.setValue('include',  QVariant(newState if itemIndex == row else 0))
                    self.emitCellChanged(itemIndex, 0)
            self.emitColumnChanged(0)
            return True
        return CInDocTableModel.setData(self, index, value, role)


class CDiagnosticsModel(CPreModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'EventType_Diagnostic', 'id', 'eventType_id', parent)
        self.addExtCol(CBoolInDocTableCol(u'Включить', 'include', 10), QVariant.Int)
        self.addCol(CRBInDocTableCol(u'Специальность', 'speciality_id', 20, 'rbSpeciality')).setReadOnly()
        self.addCol(CRBInDocTableCol(u'Тип визита', 'visitType_id', 20, 'rbVisitType')).setReadOnly()
        self.addCol(CIntInDocTableCol(u'Срок годности', 'actuality', 5)).setReadOnly()
        self.addCol(CIntInDocTableCol(u'Группа выбора', 'selectionGroup', 5)).setReadOnly()
        self.setEnableAppendLine(False)


class CActionsModel(CPreModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'EventType_Action', 'id', 'eventType_id', parent)
        self.addExtCol(CBoolInDocTableCol(u'Включить', 'include', 10), QVariant.Int)
        self.addCol(CRBInDocTableCol(u'Код', 'actionType_id', 20, 'ActionType', showFields=CRBComboBox.showCode)).setReadOnly()
        self.addCol(CRBInDocTableCol(u'Наименование', 'actionType_id', 20, 'ActionType', showFields=CRBComboBox.showName)).setReadOnly()
        self.addCol(CIntInDocTableCol(u'Срок годности', 'actuality', 5)).setReadOnly()
        self.addCol(CIntInDocTableCol(u'Группа выбора', 'selectionGroup', 5)).setReadOnly()
        self.addCol(CBoolInDocTableCol(u'Выставлять', 'expose', 10)).setReadOnly()
        self.setEnableAppendLine(False)
