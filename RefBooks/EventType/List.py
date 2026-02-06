# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

# Просмотр списка типов событий и редактор типа событий

from PyQt4 import QtGui
from PyQt4.QtGui import QFont
from PyQt4.QtCore import Qt, QAbstractTableModel, QByteArray, QEvent, QMimeData, QModelIndex, QVariant, pyqtSignature, \
    SIGNAL, QDate

from Orgs.OrgComboBox import CPolyclinicComboBox
from Orgs.OrgStructureCol import COrgStructureInDocTableCol
from Orgs.Orgs import selectOrganisation
from Events.Action import CActionTypeCache
from Orgs.PersonComboBoxEx import CPersonFindInDocTableCol
from library.AgeSelector              import composeAgeSelector, parseAgeSelector
from library.AmountToWords            import amountToWords
from library.ICDMulti import CMultiICDInDocTableCol
from library.MultivalueComboBox import CRBMultivalueComboBox
from library.crbcombobox              import CRBModelDataCache, CRBPopupView, CRBComboBox
from library.IdentificationModel      import CIdentificationModel, checkIdentification
from library.InDocTable               import CInDocTableModel, CBoolInDocTableCol, CEnumInDocTableCol, CInDocTableCol, CIntInDocTableCol, CRBInDocTableCol
from library.interchange              import getCheckBoxValue, getComboBoxValue, getLineEditValue, getRBComboBoxValue, getSpinBoxValue, \
    getTextEditValue, setCheckBoxValue, setComboBoxValue, setLineEditValue, setRBComboBoxValue, setSpinBoxValue, \
    setTextEditValue, setRBMultivalueComboBoxValue, getRBMultivalueComboBoxValue

from library.ItemsListDialog          import CItemsListDialog, CItemEditorBaseDialog
from library.TableModel               import CBoolCol, CEnumCol, CNumCol, CRefBookCol, CTextCol
from library.Utils import forceInt, forceRef, forceString, forceStringEx, toVariant, trim, forceBool, addDotsEx, forceDate, ActionTypeServiceMixin

from Events.Action                    import CActionTypeCache
from Events.ActionTypeComboBox        import CActionTypeTableCol
from Events.ActionTypeComboBoxEx      import CActionTypeFindInDocTableCol
from Events.EditDispatcher            import getEventFormList
from Events.Utils                     import getActionTypeIdListByClass

from RefBooks.Service.SelectService   import selectService
from RefBooks.Service.ServiceModifier import createModifier, parseModifier, testRegExpServiceModifier, testServiceFilter
from RefBooks.Tables                  import rbCode, rbId, rbName, rbService

from .Ui_EventTypeListDialog          import Ui_EventTypeListDialog
from .Ui_EventTypeEditor              import Ui_ItemEditorDialog
from .Ui_EventFilterDialog            import Ui_EventFilterDialog


SexList = ('', u'М', u'Ж')


class CEventTypeList(Ui_EventTypeListDialog, CItemsListDialog):
    mimeTypeEventTypeActionsIdList     = 'application/x-s11/eventtypeactionsidlist'
    mimeTypeEventTypeDiagnosticsIdList = 'application/x-s11/eventtypediagnosticsidlist'

    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(   u'Код',              [rbCode], 10),
            CTextCol(   u'Наименование',     [rbName], 40),
            CTextCol(   u'Код ЕГИСЗ',        ['usishCode'],    10),
            CTextCol(   u'Региональный код', ['regionalCode'], 10),
            CRefBookCol(u'Назначение',       ['purpose_id'], 'rbEventTypePurpose', 10),
            CRefBookCol(u'Профиль',          ['eventProfile_id'], 'rbEventProfile', 10),
            CRefBookCol(u'Вид помощи',       ['medicalAidKind_id'], 'rbMedicalAidKind', 10),
            CRefBookCol(u'Тип помощи',       ['medicalAidType_id'], 'rbMedicalAidType', 10),
            CEnumCol(   u'Пол',              ['sex'], SexList, 10),
            CTextCol(   u'Возраст',          ['age'], 10),
            CNumCol(    u'Период',           ['period'], 10),
            CEnumCol(   u'Раз в',            ['singleInPeriod'], ('', u'неделю', u'месяц', u'квартал', u'полугодие', u'год', u'раз в два года', u'раз в три года'), 10),
            CBoolCol(   u'Продолжительное',  ['isLong'], 10),
            CNumCol(    u'Мин.длительность', ['minDuration'], 10),
            CNumCol(    u'Макс.длительность',['maxDuration'], 10),
            CRefBookCol(u'Сервис ОМС',       ['service_id'], 'rbService', 10),
            CBoolCol(   u'Активный',         ['isActive'],    10),
            ], 'EventType', [rbCode, rbName, rbId], filterClass=CEventFilterDialog)
        self.setWindowTitleEx(u'Типы событий')
        self.mimeData = QMimeData()
        self.setupMenu()
        self.props = {'isActive': False}
        self.order = 'code, name, id'


    @pyqtSignature('bool')
    def on_chkFilterActive_toggled(self, value):
        self.props['isActive'] = value
        self.tblItems.model().setIdList(self.select(self.props))


    def select(self, props=None):
        db = QtGui.qApp.db
        tableEventType = db.table('EventType')
        cond = [tableEventType['deleted'].eq(0)]
        isActive = self.props.get('isActive', False)
        if not isActive:
            cond.append(tableEventType['isActive'].eq(1))
        code = props.get('Код', '')
        if code:
            cond.append(tableEventType['code'].eq(code))
        name = props.get('Наименование', '')
        if name:
            dotedName = addDotsEx(name)
            cond.append(tableEventType['name'].like(dotedName))
        usish = props.get('Код ЕГИСЗ',  '')
        if usish:
            cond.append(tableEventType['usishCode'].eq(usish))
        regionalCode = props.get('Региональный код', '')
        if regionalCode:
            cond.append(tableEventType['regionalCode'].eq(regionalCode))
        age = props.get('Возраст', '')
        if age:
            cond.append(tableEventType['age'].eq(age))
        period = props.get('Период', '')
        if period:
            cond.append(tableEventType['period'].eq(period))
        minDuration = props.get('Мин.длительность', '')
        if minDuration:
            cond.append(tableEventType['minDuration'].eq(minDuration))
        maxDuration = props.get('Макс.длительность', '')
        if maxDuration:
            cond.append(tableEventType['maxDuration'].eq(maxDuration))
        purpose = props.get('Назначение', 0)
        if purpose:
            cond.append(tableEventType['purpose_id'].eq(purpose))
        profile = props.get('Профиль', 0)
        if profile:
            cond.append(tableEventType['eventProfile_id'].eq(profile))
        medicalAidKind = props.get('Вид помощи', 0)
        if medicalAidKind:
            cond.append(tableEventType['medicalAidKind_id'].eq(medicalAidKind))
        medicalAidType = props.get('Тип помощи', 0)
        if medicalAidType:
            cond.append(tableEventType['medicalAidType_id'].eq(medicalAidType))
        sex = props.get('Пол', 0)
        if sex:
            cond.append(tableEventType['sex'].eq(sex))
        singleInPeriod = props.get('Раз в', 0)
        if singleInPeriod:
            cond.append(tableEventType['singleInPeriod'].eq(singleInPeriod))
        isLong = props.get('Продолжительное', False)
        if isLong:
            cond.append(tableEventType['isLong'].eq(isLong))
        return db.getDistinctIdList(tableEventType, 'id', cond, self.order)


    def setupMenu(self):
        self.addObject('actRemoveItem',    QtGui.QAction(u'Удалить', self))
        self.addObject('actDuplicateItem', QtGui.QAction(u'Дублировать', self))
        self.addObject('actCopyPreCreateProperties',
                       QtGui.QAction(u'Копировать определения планировщика в буфер обмена', self))
        self.addObject('actPastPreCreateProperties',
                       QtGui.QAction(u'Вставить определения планировщика из буфера обмена', self))

        self.tblItems.addPopupAction(self.actDuplicateItem)
        self.tblItems.addPopupSeparator()
        self.tblItems.addPopupAction(self.actRemoveItem)
        self.tblItems.addPopupSeparator()
        self.tblItems.addPopupAction(self.actCopyPreCreateProperties)
        self.tblItems.addPopupAction(self.actPastPreCreateProperties)

        self.connect(self.tblItems.popupMenu(), SIGNAL('aboutToShow()'), self.on_mnuItems_aboutToShow)

        self.connect(self.actRemoveItem,
                     SIGNAL('triggered()'),
                     self.on_actRemoveItem_triggered)

        self.connect(self.actDuplicateItem,
                     SIGNAL('triggered()'),
                     self.on_actDuplicateItem_triggered)

        self.connect(self.actCopyPreCreateProperties,
                     SIGNAL('triggered()'),
                     self.on_actCopyPreCreateProperties_triggered)

        self.connect(self.actPastPreCreateProperties,
                     SIGNAL('triggered()'),
                     self.on_actPastPreCreateProperties_triggered)


    def getItemEditor(self):
        return CEventTypeEditor(self)


    def exec_(self):
        QtGui.qApp.clipboard().mimeData().removeFormat(CEventTypeList.mimeTypeEventTypeActionsIdList)
        QtGui.qApp.clipboard().mimeData().removeFormat(CEventTypeList.mimeTypeEventTypeDiagnosticsIdList)
        return CItemsListDialog.exec_(self)

#    @pyqtSignature('')
    def on_mnuItems_aboutToShow(self):
        itemPresent = self.tblItems.currentIndex().row()>=0
        mimeData = QtGui.qApp.clipboard().mimeData()
        fullMimeData = bool(mimeData.hasFormat(CEventTypeList.mimeTypeEventTypeActionsIdList))
        fullMimeData = fullMimeData or bool(mimeData.hasFormat(CEventTypeList.mimeTypeEventTypeDiagnosticsIdList))
        self.actDuplicateItem.setEnabled(itemPresent)
        self.actRemoveItem.setEnabled(itemPresent)
        self.actCopyPreCreateProperties.setEnabled(itemPresent)
        self.actPastPreCreateProperties.setEnabled(itemPresent and fullMimeData)


#    @pyqtSignature('')
    def on_actDuplicateItem_triggered(self):
        eventTypeId = self.tblItems.currentItemId()
        db = QtGui.qApp.db
        table = db.table('EventType')
        db.transaction()
        try:
            record = db.getRecord(table, '*', eventTypeId)
            record.setNull('id')
            record.setValue('code', toVariant(forceString(record.value('code'))+u'-копия'))
            record.setValue('name', toVariant(forceString(record.value('name'))+u'-копия'))
            newId = db.insertRecord(table, record)
            db.copyDepended(db.table('EventTypeForm'), 'eventType_id', eventTypeId, newId)
            db.copyDepended(db.table('EventType_Action'), 'eventType_id', eventTypeId, newId)
            db.copyDepended(db.table('EventType_Diagnostic'), 'eventType_id', eventTypeId, newId)
            db.copyDepended(db.table('EventType_Identification'), 'master_id', eventTypeId, newId)
            db.commit()
        except:
            db.rollback()
            raise
        self.renewListAndSetTo(newId)


#    @pyqtSignature('')
    def on_actRemoveItem_triggered(self):
        eventTypeId = self.tblItems.currentItemId()
        db = QtGui.qApp.db
        table = db.table('EventType')
        db.transaction()
        try:
            db.deleteRecord(table, table['id'].eq(eventTypeId))
            self.tblItems.removeCurrentRow()
            db.commit()

            from Events.Utils import CEventTypeDescription
            CEventTypeDescription.purge()
        except:
            db.rollback()
            QtGui.qApp.logCurrentException()
            raise


#    @pyqtSignature('')
    def on_actCopyPreCreateProperties_triggered(self):
        try:
            eventTypeId = self.tblItems.currentItemId()
            if eventTypeId:
                actionsCount = self.copyPreCreateProperties(eventTypeId,
                                                           'EventType_Action',
                                                           CEventTypeList.mimeTypeEventTypeActionsIdList)
                diagnosticsCount = self.copyPreCreateProperties(eventTypeId,
                                                               'EventType_Diagnostic',
                                                               CEventTypeList.mimeTypeEventTypeDiagnosticsIdList)
                txtActionsCount     = amountToWords(actionsCount, ((u'действие', u'действия',   u'действий',   'n'), None))
                txtDiagnosticsCount = amountToWords(diagnosticsCount, ((u'осмотр', u'осмотра',   u'осмотров',   'm'), None))
                message = u'Скопировано: %s, %s'% (txtActionsCount, txtDiagnosticsCount)
                self.statusBar.showMessage(message,  5000)
        except:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Не удалось скопировать определения планировщика в буфер обмена')


    def copyPreCreateProperties(self, eventTypeId, tableName, mimeTypeName):
        db = QtGui.qApp.db
        eventTypeActionsIdList = db.getIdList(tableName, 'id', 'eventType_id=%d'%eventTypeId)
        if bool(eventTypeActionsIdList):
            strList = ','.join([str(id) for id in eventTypeActionsIdList])
            self.mimeData.setData(mimeTypeName, QByteArray(strList))
            QtGui.qApp.clipboard().setMimeData(self.mimeData)
            return len(eventTypeActionsIdList)
        QtGui.qApp.clipboard().mimeData().removeFormat(mimeTypeName)
        return 0


#    @pyqtSignature('')
    def on_actPastPreCreateProperties_triggered(self):
        dlg = CCheckPreCreatePropertiesTypes(self)
        if not dlg.exec_():
            return
        QtGui.qApp.setWaitCursor()
        selectedIdList = self.tblItems.selectedItemIdList()
        if bool(selectedIdList):
            db = QtGui.qApp.db
            mimeData = QtGui.qApp.clipboard().mimeData()
            actionsRecordList     = []
            diagnosticsRecordList = []
            if bool(dlg.actionClasses()) and bool(mimeData.hasFormat(CEventTypeList.mimeTypeEventTypeActionsIdList)):
                strIdList = unicode(mimeData.data(CEventTypeList.mimeTypeEventTypeActionsIdList)).split(',')
                actionsIdList = [int(id) for id in strIdList]
                table = db.table('EventType_Action')
                tableActionType = db.table('ActionType')
                cond = [table['id'].inlist(actionsIdList),
                        'EXISTS (SELECT ActionType.`id` FROM ActionType WHERE %s AND EventType_Action.`actionType_id`=ActionType.`id`)'%tableActionType['class'].inlist(dlg.actionClasses())]
                actionsRecordList = db.getRecordList(table, '*', cond)
            if dlg.diagnostics() and bool(mimeData.hasFormat(CEventTypeList.mimeTypeEventTypeDiagnosticsIdList)):
                strIdList = unicode(mimeData.data(CEventTypeList.mimeTypeEventTypeDiagnosticsIdList)).split(',')
                diagnosticsIdList = [int(id) for id in strIdList]
                table = db.table('EventType_Diagnostic')
                diagnosticsRecordList = db.getRecordList(table, '*', table['id'].inlist(diagnosticsIdList))
            for selectedId in selectedIdList:
                actualActionsRecordList = self.checkSameRecords(selectedId, actionsRecordList, 'EventType_Action')
                actualDiagnosticsRecordList = self.checkSameRecords(selectedId, diagnosticsRecordList, 'EventType_Diagnostic')
                for record in actualActionsRecordList:
                    db.insertRecord('EventType_Action', record)
                for record in actualDiagnosticsRecordList:
                    db.insertRecord('EventType_Diagnostic', record)
                actionsCount = len(actualActionsRecordList)
                diagnosticsCount = len(actualDiagnosticsRecordList)
                txtActionsCount     = amountToWords(actionsCount, ((u'действие', u'действия',   u'действий',   'n'), None))
                txtDiagnosticsCount = amountToWords(diagnosticsCount, ((u'осмотр', u'осмотра',   u'осмотров',   'm'), None))
                message = u'Добавлено: %s, %s'% (txtActionsCount, txtDiagnosticsCount)
                self.statusBar.showMessage(message,  5000)
        QtGui.qApp.restoreOverrideCursor()


    def checkSameRecords(self, id, pastedRecordList, tableName):
        db = QtGui.qApp.db
        table = db.table(tableName)
        existsRecordList = db.getRecordList(table, '*', table['eventType_id'].eq(id))
        actualPastedRecordList = []
        for pastedRecord in pastedRecordList:
            pastedRecord.setNull('id')
            pastedRecord.setNull('eventType_id')
            pastedFieldsCount = pastedRecord.count()
            difRecords = True
            for existsRecord in existsRecordList:
                allIsSame = True
                existsRecord.setNull('id')
                existsRecord.setNull('eventType_id')
                existsFieldsCount = existsRecord.count()
                if existsFieldsCount == pastedFieldsCount:
                    for i in range(pastedFieldsCount):
                        if unicode(existsRecord.fieldName(i)) not in (u'id', u'eventType_id'):
                            if existsRecord.value(i) != pastedRecord.value(i):
                                allIsSame = False
                                break
                if allIsSame:
                    difRecords = False
                    break
            if difRecords:
                pastedRecord.setValue('eventType_id', QVariant(id))
                actualPastedRecordList.append(pastedRecord)
        return actualPastedRecordList

#
# ##########################################################################
#

class CCheckPreCreatePropertiesTypes(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.vLayout                = QtGui.QVBoxLayout(self)
        self.__chkDiagnostics       = QtGui.QCheckBox(u'Осмотры', self)
        self.__chkDiagnostics.setChecked(True)
        self.__chkStatusActions     = QtGui.QCheckBox(u'Статус', self)
        self.__chkStatusActions.setChecked(True)
        self.__chkDiagnosticActions = QtGui.QCheckBox(u'Диагностика', self)
        self.__chkDiagnosticActions.setChecked(True)
        self.__chkCureActions       = QtGui.QCheckBox(u'Лечение', self)
        self.__chkCureActions.setChecked(True)
        self.__chkMiscActions       = QtGui.QCheckBox(u'Прочие мероприятия', self)
        self.__chkMiscActions.setChecked(True)
        self.buttonBox              = QtGui.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)

        self.vLayout.addWidget(self.__chkDiagnostics)
        self.vLayout.addWidget(self.__chkStatusActions)
        self.vLayout.addWidget(self.__chkDiagnosticActions)
        self.vLayout.addWidget(self.__chkCureActions)
        self.vLayout.addWidget(self.__chkMiscActions)
        self.vLayout.addWidget(self.buttonBox)
        self.connect(self.buttonBox, SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, SIGNAL('rejected()'), self.reject)

    def diagnostics(self):
        return self.__chkDiagnostics.isChecked()

    def actionClasses(self):
        classes = []
        if self.__chkStatusActions.isChecked():
            classes.append(0)
        if self.__chkDiagnosticActions.isChecked():
            classes.append(1)
        if self.__chkCureActions.isChecked():
            classes.append(2)
        if self.__chkMiscActions.isChecked():
            classes.append(3)
        return classes


#
# ##########################################################################
#

class CActionsControl(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'EventType_ActionControl', 'id', 'eventType_id', parent)
        self.addCol(CInDocTableCol( u'Шаблон',                    'template',  12))
        self.addCol(CIntInDocTableCol( u'Количество',        'amount',  12, low=0, high=99))
        self.addCol(CActionTypeFindInDocTableCol(u'Тип действия',   'actionType_id', 20, 'ActionType', None))

#
# ##########################################################################
#


class CEventTypeEditor(CItemEditorBaseDialog, Ui_ItemEditorDialog):
    orders = (
        u'Плановый',
        u'Экстренный',
        u'Самотёком',
        u'Принудительный',
        u'Внутренний перевод',
        u'Неотложная'
    )
    
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'EventType')

        self.addModels('Diagnostics',       CDiagnosticsModel(self))
        self.addModels('StatusActions',     CActionsModel(self, 0))
        self.addModels('DiagnosticActions', CActionsModel(self, 1))
        self.addModels('CureActions',       CActionsModel(self, 2))
        self.addModels('MiscActions',       CActionsModel(self, 3))
        self.addModels('ActionsControl',    CActionsControl(self))
        self.addModels('EventType',         CEventTypeModel(self))
        self.addModels('Identification',    CIdentificationModel(self, 'EventType_Identification', 'EventType'))
        self.addModels('OrgStruct',         COrgStructModel(self))
        self.addModels('Persons',           CPersonsModel(self))
        self.addModels('ActionType',        CActionTypeModel(self, None))
        self.addModels('ActionType_status', CActionTypeModel(self, 0))
        self.addModels('ActionType_diagnostic', CActionTypeModel(self, 1))
        self.addModels('ActionType_cure',   CActionTypeModel(self, 2))
        self.addModels('ActionType_other',  CActionTypeModel(self, 3))

        self.setupUi(self)

        self.setWindowTitleEx(u'Тип события')
        self.cmbPurpose.setTable('rbEventTypePurpose')
        self.cmbFinance.setTable('rbFinance')
        self.cmbEventProfile.setTable('rbEventProfile', True)
        self.cmbMedicalAidKind.setTable('rbMedicalAidKind', True)
        self.cmbMedicalAidType.setTable('rbMedicalAidType', True)
        filterPrevEventTypeId = u''
        if forceBool(QtGui.qApp.preferences.appPrefs.get('isPreferencesEventTypeActive', False)):
            filterPrevEventTypeId += u'EventType.isActive = 1 AND EventType.deleted = 0'
        self.cmbPrevEventTypeId.setTable('EventType', True, filter=filterPrevEventTypeId)
        self.cmbMesSpecification.setTable('rbMesSpecification', True)

        self.cmbForm.addItem(u'не задано', toVariant(''))
        for formCode, formDescr in getEventFormList():
            self.cmbForm.addItem(formDescr, toVariant(formCode))
        self.cmbScene.setTable('rbScene', True)
        self.cmbAvailableOrders.setItems(CEventTypeEditor.orders)

        self.setModels(self.tblDiagnostics, self.modelDiagnostics, self.selectionModelDiagnostics)
        self.setModels(self.tblStatusActions, self.modelStatusActions, self.selectionModelStatusActions)
        self.setModels(self.tblDiagnosticActions, self.modelDiagnosticActions, self.selectionModelDiagnosticActions)
        self.setModels(self.tblCureActions, self.modelCureActions, self.selectionModelCureActions)
        self.setModels(self.tblMiscActions, self.modelMiscActions, self.selectionModelMiscActions)
        self.setModels(self.tblActionsControl, self.modelActionsControl, self.selectionModelActionsControl)
        self.setModels(self.tblEventType, self.modelEventType, self.selectionModelEventType)
        self.setModels(self.tblIdentification, self.modelIdentification, self.selectionModelIdentification)
        self.setModels(self.tblOrgStruct, self.modelOrgStruct, self.selectionModelOrgStruct)
        self.setModels(self.tblPersons, self.modelPersons, self.selectionModelPersons)
        self.setModels(self.tblActionType_status, self.modelActionType_status, self.selectionModelActionType_status)
        self.setModels(self.tblActionType_diagnostic, self.modelActionType_diagnostic, self.selectionModelActionType_diagnostic)
        self.setModels(self.tblActionType_cure, self.modelActionType_cure, self.selectionModelActionType_cure)
        self.setModels(self.tblActionType_other, self.modelActionType_other, self.selectionModelActionType_other)

        for tbl in (self.tblDiagnostics, self.tblStatusActions, self.tblDiagnosticActions, self.tblCureActions,
                    self.tblMiscActions, self.tblEventType, self.tblActionType_status, self.tblActionType_diagnostic,
                    self.tblActionType_cure, self.tblActionType_other, self.tblOrgStruct, self.tblPersons):
            tbl.addMoveRow()
            tbl.addPopupDelRow()
        
        for mdl in (self.modelStatusActions, self.modelDiagnosticActions, self.modelCureActions, self.modelMiscActions,
                    self.modelOrgStruct, self.modelPersons,
                    self.modelActionType_status, self.modelActionType_diagnostic, self.modelActionType_cure, self.modelActionType_other):
            mdl.cols()[0].setSortable(True)
            
        self.tblIdentification.addPopupDelRow()
        self.tblIdentification.setDelRowsChecker(self.modelIdentification.delRowsChecker)
        self.cmbService.setTable(rbService, True)
        self.cmbCounter.setTable('rbCounter')
        self.cmbRelegateNum.setTable('rbCounter')
        self.cmbVoucherCounter.setTable('rbCounter')
        self.cmbService.setCurrentIndex(0)
        self.setupDirtyCather()
        self.setIsDirty(False)
        self.regExpTestStr = ''
        self.visitServiceFilterTestStr = ''
        self.oldFormValue = forceString(self.cmbForm.itemData(self.cmbForm.currentIndex()))
        self.edtVisitServiceFilter.setToolTip(u'Пример: \n2,4 \nгде 2-начало среза, 4-длина среза(не обязателен)')
        self.modelEventType.setFilter('EventType.deleted = 0')
        
        
    def setRecord(self, record):
        id = self.itemId()
        filterPrevEventTypeId = u'id != %d'%(id)
        if forceBool(QtGui.qApp.preferences.appPrefs.get('isPreferencesEventTypeActive', False)):
            filterPrevEventTypeId += u' AND EventType.isActive = 1 AND EventType.deleted = 0'
        self.cmbPrevEventTypeId.setFilter(filterPrevEventTypeId)
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(   self.edtCode,                              record, 'code')
        setLineEditValue(   self.edtRegionalCode,                      record, 'regionalCode')
        setLineEditValue(   self.edtUsishCode,                         record, 'usishCode')
        setLineEditValue(   self.edtName,                              record, 'name')
        setRBComboBoxValue( self.cmbPurpose,                           record, 'purpose_id')
        setRBComboBoxValue( self.cmbEventProfile,                      record, 'eventProfile_id')
        setRBComboBoxValue( self.cmbMedicalAidKind,                    record, 'medicalAidKind_id')
        setRBComboBoxValue( self.cmbMedicalAidType,                    record, 'medicalAidType_id')
        setRBComboBoxValue( self.cmbMesSpecification,                  record, 'mesSpecification_id')
        setComboBoxValue(   self.cmbSex,                               record, 'sex')
        (begUnit, begCount, endUnit, endCount) = parseAgeSelector(forceString(record.value('age')))
        self.cmbBegAgeUnit.setCurrentIndex(begUnit)
        self.edtBegAgeCount.setText(str(begCount))
        self.cmbEndAgeUnit.setCurrentIndex(endUnit)
        self.edtEndAgeCount.setText(str(endCount))
        setRBComboBoxValue( self.cmbCounter,                           record, 'counter_id')
        setRBComboBoxValue(self.cmbRelegateNum,                        record, 'relcounter_id')
        setRBComboBoxValue(self.cmbRelegateOrg,                        record, 'relOrg_id')
        setRBComboBoxValue( self.cmbVoucherCounter,                    record, 'voucherCounter_id')
        setCheckBoxValue(   self.chkRequiredCoordination,              record, 'isRequiredCoordination')
        setRBComboBoxValue( self.cmbFinance,                           record, 'finance_id')
        setCheckBoxValue(   self.chkCanHavePayableActions,             record, 'canHavePayableActions')
        setCheckBoxValue(   self.chkAddVisit,                          record, 'addVisit')
        setComboBoxValue(   self.cmbWeekProfile,                       record, 'weekProfileCode')
        setRBComboBoxValue( self.cmbScene,                             record, 'scene_id')
        setCheckBoxValue(   self.chkShowVisitTime,                     record, 'showVisitTime')
        setCheckBoxValue(   self.chkIsCheckedExecDateForVisit,         record, 'isCheckedExecDateForVisit')
        setComboBoxValue(   self.cmbTerritorialBelonging,              record, 'isTerritorialBelonging')
        setComboBoxValue(   self.cmbVisitFinance,                      record, 'visitFinance')
        setComboBoxValue(   self.cmbActionFinance,                     record, 'actionFinance')
        setComboBoxValue(   self.cmbActionContract,                    record, 'actionContract')
        setComboBoxValue(   self.cmbContractCondition,                 record, 'contractCondition')
        setComboBoxValue(   self.cmbPlannerCondition,                  record, 'plannerCondition')
        setComboBoxValue(   self.cmbOnlyNotExistsCondition,                  record, 'onlyNotExistsCondition')
        setComboBoxValue(   self.cmbOrgStructureCondition,             record, 'orgStructureCondition')
        setComboBoxValue(   self.cmbNomenclatureCondition,             record, 'nomenclatureCondition')
        setComboBoxValue(   self.cmbMESCondition,                      record, 'mesCondition')
        setSpinBoxValue(    self.edtPeriod,                            record, 'period')
        setComboBoxValue(   self.cmbSingleInPeriod,                    record, 'singleInPeriod')
        setCheckBoxValue(   self.chkFillNextEventDate,                 record, 'fillNextEventDate')
        setCheckBoxValue(self.chkIEMK,                                 record, 'exportIEMK')
        setComboBoxValue(   self.cmbDateInput,                         record, 'dateInput')
        setCheckBoxValue(   self.chkIsLong,                            record, 'isLong')
        setCheckBoxValue(   self.chkOrgStructurePriorityForAddActions, record, 'isOrgStructurePriority')
        setSpinBoxValue(    self.edtMinDuration,                       record, 'minDuration')
        setSpinBoxValue(    self.edtMaxDuration,                       record, 'maxDuration')
        setRBComboBoxValue( self.cmbService,                           record, 'service_id')
        self.cmbForm.setCurrentIndex(max(0, self.cmbForm.findData(record.value('form'))))
        setCheckBoxValue(   self.chkShowTime,                          record, 'showTime')
        setCheckBoxValue(   self.chkShowButtonAccount,                 record, 'showButtonAccount')
        setCheckBoxValue(self.chkShowButtonTemperatureList, record, 'showButtonTemperatureList')
        setCheckBoxValue(self.chkShowButtonNomenclatureExpense, record, 'showButtonNomenclatureExpense')
        setCheckBoxValue(self.chkShowButtonJobTickets, record, 'showButtonJobTickets')
        setLineEditValue(   self.edtContext,                           record, 'context')
        setCheckBoxValue(   self.chkExternalId,                        record, 'isExternal')
        setCheckBoxValue(   self.chkIsResolutionOfDirection,           record, 'isResolutionOfDirection')
        setCheckBoxValue(   self.chkMesRequired,                       record, 'mesRequired')
        setComboBoxValue(   self.cmbMesRequiredParams,                 record, 'mesRequiredParams')
        setCheckBoxValue(   self.chkCSGRequired,                       record, 'csgRequired')
        setCheckBoxValue(   self.chkIsTakenTissue,                     record, 'isTakenTissue')
        setLineEditValue(   self.edtMesCodeMask,                       record, 'mesCodeMask')
        setLineEditValue(   self.edtCSGCodeMask,                       record, 'csgCodeMask')
        setLineEditValue(   self.edtSubCSGCodeMask,                       record, 'subCsgCodeMask')
        setLineEditValue(   self.edtMesNameMask,                       record, 'mesNameMask')
        setTextEditValue(   self.edtMesServiceMask,                     record, 'mesServiceMask')
        setCheckBoxValue(   self.chkHasAssistant,                      record, 'hasAssistant')
        setCheckBoxValue(   self.chkHasCurator,                        record, 'hasCurator')
        setCheckBoxValue(   self.chkRelegationRequired,                      record, 'relegationRequired')
        setCheckBoxValue(   self.chkHasVisitAssistant,                 record, 'hasVisitAssistant')
        setComboBoxValue(   self.cmbEnableUnfinishedActions,           record, 'unfinishedAction')
        setComboBoxValue(   self.cmbEnableActionsBeyondEvent,          record, 'actionsBeyondEvent')
        setRBComboBoxValue( self.cmbPrevEventTypeId,                   record, 'prevEventtype_id')
        setLineEditValue(   self.edtServiceReason,                     record, 'serviceReason')
        setComboBoxValue(   self.cmbIsPrimary,                         record, 'isPrimary')
        setComboBoxValue(   self.cmbSetPerson,                         record, 'setPerson')
        setComboBoxValue(   self.cmbRequiredCondition,                 record, 'requiredCondition')
        setCheckBoxValue(   self.chkAutoFillingExpertise,              record, 'isAutoFillingExpertise')
        setRBMultivalueComboBoxValue(self.cmbAvailableOrders,          record, 'availableOrders')
        setComboBoxValue(   self.cmbOrder,                             record, 'order')
        setCheckBoxValue(   self.chkIncludeActionTypesWithoutService,  record, 'showActionTypesWithoutService')
        setCheckBoxValue(   self.chkKeepVisitParity,                   record, 'keepVisitParity')
        setCheckBoxValue(   self.chkRestrictVisitTypeAgeSex,           record, 'isRestrictVisitTypeAgeSex')
        setCheckBoxValue(self.chkIgnoreVisibleRights, record, 'ignoreVisibleRights')
        setCheckBoxValue(   self.chkActive,                            record, 'isActive')
        setCheckBoxValue(self.chkNextEventDateRequired,                record, 'nextEventDateRequired')

        self.cmbCounter.setEnabled(self.chkExternalId.isChecked())
        self.cmbVoucherCounter.setEnabled(forceString(self.cmbForm.itemData(self.cmbForm.currentIndex())) == u'072')

        setLineEditValue(   self.edtVisitServiceFilter, record, 'visitServiceFilter')
        action, text = parseModifier(record.value('visitServiceModifier'))
        if action == 0:
            self.rbVisitNoModifyService.setChecked(True)
        elif action == 1:
            self.rbVisitRemoveService.setChecked(True)
        elif action == 2:
            self.rbVisitReplaceService.setChecked(True)
            self.edtVisitNewServiceName.setText(text)
        elif action == 3:
            self.rbVisitModifyService.setChecked(True)
            self.edtVisitNewServicePrefix.setText(text)
        elif action == 4:
            self.rbVisitModifyByRegExp.setChecked(True)
            self.edtVisitRegExp.setPlainText(text)
        else:
            self.rbVisitNoModifyService.setChecked(True)
            self.edtVisitNewServiceName.setText(text)
            self.edtVisitNewServicePrefix.setText(text)

        setCheckBoxValue(   self.chkStatusShowOptionalInPlanner,     record, 'showStatusActionsInPlanner')
        setCheckBoxValue(   self.chkDiagnosticShowOptionalInPlanner, record, 'showDiagnosticActionsInPlanner')
        setCheckBoxValue(   self.chkCureShowOptionalInPlanner,       record, 'showCureActionsInPlanner')
        setCheckBoxValue(   self.chkMiscShowOptionalInPlanner,       record, 'showMiscActionsInPlanner')
        setCheckBoxValue(   self.chkStatusLimitInput,                record, 'limitStatusActionsInput')
        setCheckBoxValue(   self.chkDiagnosticLimitInput,            record, 'limitDiagnosticActionsInput')
        setCheckBoxValue(   self.chkCureLimitInput,                  record, 'limitCureActionsInput')
        setCheckBoxValue(   self.chkMiscLimitInput,                  record, 'limitMiscActionsInput')
        setCheckBoxValue(   self.chkLimitActionTypes,                record, 'limitActionTypes')
        setCheckBoxValue(   self.chkIncludeTooth,                    record, 'includeTooth')
        setCheckBoxValue(   self.chkActionsControl,                 record, 'actionsControlEnabled')
        self.on_chkIsTakenTissue_clicked(self.chkIsTakenTissue.isChecked())
        self.modelDiagnostics.loadItems(id)
        self.modelStatusActions.loadItems(id)
        self.modelDiagnosticActions.loadItems(id)
        self.modelCureActions.loadItems(id)
        self.modelMiscActions.loadItems(id)
        self.modelActionsControl.loadItems(id)
        self.modelEventType.loadItems(id)
        self.modelIdentification.loadItems(self.itemId())
        self.modelOrgStruct.loadItems(id)
        self.modelPersons.loadItems(id)
        self.modelActionType_status.loadItems(id)
        self.modelActionType_diagnostic.loadItems(id)
        self.modelActionType_cure.loadItems(id)
        self.modelActionType_other.loadItems(id)
        self.setIsDirty(False)


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(   self.edtCode,                              record, 'code')
        getLineEditValue(   self.edtRegionalCode,                      record, 'regionalCode')
        getLineEditValue(   self.edtUsishCode,                         record, 'usishCode')
        getLineEditValue(   self.edtName,                              record, 'name')
        getRBComboBoxValue( self.cmbPurpose,                           record, 'purpose_id')
        getRBComboBoxValue( self.cmbEventProfile,                      record, 'eventProfile_id')
        getRBComboBoxValue( self.cmbMedicalAidKind,                    record, 'medicalAidKind_id')
        getRBComboBoxValue( self.cmbMedicalAidType,                    record, 'medicalAidType_id')
        getRBComboBoxValue( self.cmbMesSpecification,                  record, 'mesSpecification_id')
        getComboBoxValue(   self.cmbSex,                               record, 'sex')
        record.setValue('age',        toVariant(composeAgeSelector(
                    self.cmbBegAgeUnit.currentIndex(),  forceStringEx(self.edtBegAgeCount.text()),
                    self.cmbEndAgeUnit.currentIndex(),  forceStringEx(self.edtEndAgeCount.text())
                        )))
        getRBComboBoxValue( self.cmbCounter,                           record, 'counter_id')
        getRBComboBoxValue(self.cmbRelegateNum,                        record, 'relcounter_id')
        getRBComboBoxValue(self.cmbRelegateOrg,                        record, 'relOrg_id')
        getRBComboBoxValue( self.cmbVoucherCounter,                    record, 'voucherCounter_id')
        getCheckBoxValue(   self.chkRequiredCoordination,              record, 'isRequiredCoordination')
        getRBComboBoxValue( self.cmbFinance,                           record, 'finance_id')
        getCheckBoxValue(   self.chkCanHavePayableActions,             record, 'canHavePayableActions')
        getComboBoxValue(   self.cmbWeekProfile,                       record, 'weekProfileCode')
        getCheckBoxValue(   self.chkAddVisit,                          record, 'addVisit')
        getRBComboBoxValue( self.cmbScene,                             record, 'scene_id')
        getCheckBoxValue(   self.chkShowVisitTime,                     record, 'showVisitTime')
        getCheckBoxValue(   self.chkIsCheckedExecDateForVisit,         record, 'isCheckedExecDateForVisit')
        getComboBoxValue(   self.cmbTerritorialBelonging,              record, 'isTerritorialBelonging')
        getComboBoxValue(   self.cmbVisitFinance,                      record, 'visitFinance')
        getComboBoxValue(   self.cmbActionFinance,                     record, 'actionFinance')
        getComboBoxValue(   self.cmbActionContract,                    record, 'actionContract')
        getComboBoxValue(   self.cmbContractCondition,                 record, 'contractCondition')
        getComboBoxValue(   self.cmbPlannerCondition,                  record, 'plannerCondition')
        getComboBoxValue(   self.cmbOnlyNotExistsCondition,                  record, 'onlyNotExistsCondition')
        getComboBoxValue(   self.cmbOrgStructureCondition,             record, 'orgStructureCondition')
        getComboBoxValue(   self.cmbNomenclatureCondition,             record, 'nomenclatureCondition')
        getComboBoxValue(   self.cmbMESCondition,                      record, 'mesCondition')
        getSpinBoxValue(    self.edtPeriod,                            record, 'period')
        getComboBoxValue(   self.cmbSingleInPeriod,                    record, 'singleInPeriod')
        getCheckBoxValue(   self.chkFillNextEventDate,                 record, 'fillNextEventDate')
        getCheckBoxValue(self.chkIEMK,                                 record, 'exportIEMK')
        getComboBoxValue(   self.cmbDateInput,                         record, 'dateInput')
        getCheckBoxValue(   self.chkIsLong,                            record, 'isLong')
        getCheckBoxValue(   self.chkOrgStructurePriorityForAddActions, record, 'isOrgStructurePriority')
        getSpinBoxValue(    self.edtMinDuration,                       record, 'minDuration')
        getSpinBoxValue(    self.edtMaxDuration,                       record, 'maxDuration')
        getRBComboBoxValue( self.cmbService,                           record, 'service_id')
        record.setValue('form', self.cmbForm.itemData(self.cmbForm.currentIndex()))
        getCheckBoxValue(   self.chkShowTime,                          record, 'showTime')
        getCheckBoxValue(   self.chkShowButtonAccount,                 record, 'showButtonAccount')
        getCheckBoxValue(self.chkShowButtonTemperatureList, record, 'showButtonTemperatureList')
        getCheckBoxValue(self.chkShowButtonNomenclatureExpense, record, 'showButtonNomenclatureExpense')
        getCheckBoxValue(self.chkShowButtonJobTickets, record, 'showButtonJobTickets')
        getLineEditValue(   self.edtContext,                           record, 'context')
        getCheckBoxValue(   self.chkExternalId,                        record, 'isExternal')
        getCheckBoxValue(   self.chkIsResolutionOfDirection,           record, 'isResolutionOfDirection')
        getCheckBoxValue(   self.chkMesRequired,                       record, 'mesRequired')
        getComboBoxValue(   self.cmbMesRequiredParams,                 record, 'mesRequiredParams')
        getCheckBoxValue(   self.chkCSGRequired,                       record, 'csgRequired')
        getCheckBoxValue(   self.chkIsTakenTissue,                     record, 'isTakenTissue')
        getLineEditValue(   self.edtMesCodeMask,                       record, 'mesCodeMask')
        getLineEditValue(   self.edtCSGCodeMask,                       record, 'csgCodeMask')
        getLineEditValue(   self.edtSubCSGCodeMask,                       record, 'subCsgCodeMask')
        getLineEditValue(   self.edtMesNameMask,                       record, 'mesNameMask')
        getTextEditValue(   self.edtMesServiceMask,                     record, 'mesServiceMask')
        getCheckBoxValue(   self.chkHasAssistant,                      record, 'hasAssistant')
        getCheckBoxValue(   self.chkHasCurator,                        record, 'hasCurator')
        getCheckBoxValue(   self.chkRelegationRequired,                      record, 'relegationRequired')
        getCheckBoxValue(   self.chkHasVisitAssistant,                 record, 'hasVisitAssistant')
        getComboBoxValue(   self.cmbEnableUnfinishedActions,           record, 'unfinishedAction')
        getComboBoxValue(   self.cmbEnableActionsBeyondEvent,          record, 'actionsBeyondEvent')
        getRBComboBoxValue( self.cmbPrevEventTypeId,                   record, 'prevEventtype_id')
        getLineEditValue(   self.edtServiceReason,                     record, 'serviceReason')
        getComboBoxValue(   self.cmbIsPrimary,                         record, 'isPrimary')
        getComboBoxValue(   self.cmbSetPerson,                         record, 'setPerson')
        getComboBoxValue(   self.cmbRequiredCondition,                 record, 'requiredCondition')
        getCheckBoxValue(   self.chkAutoFillingExpertise,              record, 'isAutoFillingExpertise')
        getComboBoxValue(   self.cmbOrder,                             record, 'order')
        getRBMultivalueComboBoxValue(self.cmbAvailableOrders,          record, 'availableOrders')
        getCheckBoxValue(   self.chkIncludeActionTypesWithoutService,  record, 'showActionTypesWithoutService')
        getCheckBoxValue(   self.chkKeepVisitParity,                   record, 'keepVisitParity')
        getCheckBoxValue(   self.chkRestrictVisitTypeAgeSex,           record, 'isRestrictVisitTypeAgeSex')
        getCheckBoxValue(self.chkIgnoreVisibleRights, record, 'ignoreVisibleRights')
        getCheckBoxValue(   self.chkActive,                            record, 'isActive')
        getCheckBoxValue(self.chkNextEventDateRequired,                record, 'nextEventDateRequired')

        action = 0
        text = u''
        if self.rbVisitNoModifyService.isChecked():
            action = 0
        if self.rbVisitRemoveService.isChecked():
            action = 1
        if self.rbVisitReplaceService.isChecked():
            action = 2
            text = forceStringEx(self.edtVisitNewServiceName.text())
        if self.rbVisitModifyService.isChecked():
            action = 3
            text = forceStringEx(self.edtVisitNewServicePrefix.text())
        if self.rbVisitModifyByRegExp.isChecked():
            action = 4
            text = forceString(self.edtVisitRegExp.toPlainText())
        record.setValue('visitServiceModifier', toVariant(createModifier(action, text)))
        getLineEditValue(   self.edtVisitServiceFilter, record, 'visitServiceFilter')

        getCheckBoxValue(   self.chkStatusShowOptionalInPlanner,     record, 'showStatusActionsInPlanner')
        getCheckBoxValue(   self.chkDiagnosticShowOptionalInPlanner, record, 'showDiagnosticActionsInPlanner')
        getCheckBoxValue(   self.chkCureShowOptionalInPlanner,       record, 'showCureActionsInPlanner')
        getCheckBoxValue(   self.chkMiscShowOptionalInPlanner,       record, 'showMiscActionsInPlanner')
        getCheckBoxValue(   self.chkStatusLimitInput,                record, 'limitStatusActionsInput')
        getCheckBoxValue(   self.chkDiagnosticLimitInput,            record, 'limitDiagnosticActionsInput')
        getCheckBoxValue(   self.chkCureLimitInput,                  record, 'limitCureActionsInput')
        getCheckBoxValue(   self.chkMiscLimitInput,                  record, 'limitMiscActionsInput')
        getCheckBoxValue(   self.chkLimitActionTypes,                record, 'limitActionTypes')
        getCheckBoxValue(   self.chkIncludeTooth,                    record, 'includeTooth')
        getCheckBoxValue(   self.chkActionsControl,              record, 'actionsControlEnabled')
        return record


    def saveInternals(self, id):
        self.modelDiagnostics.saveItems(id)
        self.modelStatusActions.saveItems(id)
        self.modelDiagnosticActions.saveItems(id)
        self.modelCureActions.saveItems(id)
        self.modelMiscActions.saveItems(id)
        self.modelActionsControl.saveItems(id)
        self.modelEventType.saveItems(id)
        self.modelIdentification.saveItems(id)
        self.modelOrgStruct.saveItems(id)
        self.modelPersons.saveItems(id)
        self.modelActionType_status.saveItems(id)
        self.modelActionType_diagnostic.saveItems(id)
        self.modelActionType_cure.saveItems(id)
        self.modelActionType_other.saveItems(id)


    def afterSave(self):
        from Events.Utils import CEventTypeDescription

        CEventTypeDescription.purge()
        CItemEditorBaseDialog.afterSave(self)


    def checkDataEntered(self):
        result = CItemEditorBaseDialog.checkDataEntered(self)
        result = result and (self.cmbPurpose.value() or self.checkInputMessage(u'назначение', False, self.cmbPurpose))
        result = result and self.checkVisitServiceFilter()
        result = result and self.modelStatusActions.checkValues(self.tblStatusActions)
        result = result and self.modelDiagnosticActions.checkValues(self.tblDiagnosticActions)
        result = result and self.modelCureActions.checkValues(self.tblCureActions)
        result = result and self.modelMiscActions.checkValues(self.tblMiscActions)
        result = result and self.modelActionType_status.checkValues(self.tblActionType_status)
        result = result and self.modelActionType_diagnostic.checkValues(self.tblActionType_diagnostic)
        result = result and self.modelActionType_cure.checkValues(self.tblActionType_cure)
        result = result and self.modelActionType_other.checkValues(self.tblActionType_other)
        result = result and self.modelEventType.checkValues()
        result = result and checkIdentification(self, self.tblIdentification)
        result = result and self.checkOrders()
        return result
    
    
    def checkOrders(self):
        if not self.cmbAvailableOrders.checkedValueList():
            return self.checkValueMessage(u'Должен быть выбран минимум один доступный порядок', False, self.cmbAvailableOrders, None, None)
        if self.cmbOrder.currentIndex() < 0:
            return self.checkValueMessage(u'Должен быть выбран порядок по умолчанию', False, self.cmbOrder, None, None)
        return True


    def checkVisitServiceFilter(self):
        val = trim(self.edtVisitServiceFilter.text())
        if val:
            parts = val.split(',')
            if len(parts) in (1, 2):
                try:
                    for idx, part in enumerate(parts):
                        if trim(part) or idx == 0:
                            int(part)
                    return True
                except ValueError:
                    pass
            return self.checkValueMessage(u'Не корректно указана \nфильтрация списка услуг визитов', False, self.edtVisitServiceFilter, None, None)
        return True


    @pyqtSignature('int')
    def on_cmbForm_currentIndexChanged(self, index):
        self.chkLimitActionTypes.setEnabled(forceString(self.cmbForm.itemData(index)) == u'001')
        formValue = forceString(self.cmbForm.itemData(index))
        if formValue and self.oldFormValue != formValue:
            if formValue == '003':
                # self.cmbMesRequiredParams.contractControlEnable(True)
                # self.cmbCSGRequiredParams.contractControlEnable(True)
                pass
            elif formValue == '090':
                self.modelDiagnostics._cols[1].setDefaultHidden(False)
                self.tblDiagnostics.horizontalHeader().setSectionHidden(1, False)
            else:
                self.modelDiagnostics._cols[1].setDefaultHidden(True)
                self.tblDiagnostics.horizontalHeader().setSectionHidden(1, True)
                # self.cmbMesRequiredParams.contractControlEnable(False)
                # self.cmbCSGRequiredParams.contractControlEnable(False)
            self.tblEventType.setEnabled(True)
            self.modelEventType.setFilter('''EventType.deleted = 0 and EventType.form LIKE '%s' ''' % formValue)
            self.modelEventType._cols[0].filter = self.modelEventType._filter
            self.modelEventType.clearItems()
        else:
            self.tblEventType.setEnabled(False)
            self.modelEventType.clearItems()
        self.oldFormValue = forceString(self.cmbForm.itemData(index))
        self.cmbVoucherCounter.setEnabled(forceString(self.cmbForm.itemData(self.cmbForm.currentIndex())) == u'072')
    
    
    @pyqtSignature('QString')
    def on_cmbAvailableOrders_editTextChanged(self, value):
        checkedList = self.cmbAvailableOrders.checkedValueList()
        checkedDict = self.cmbAvailableOrders.getCheckedDict()
        for key, value in checkedDict.items():
            self.cmbOrder.model().item(forceInt(key)).setEnabled(value)
        if forceString(self.cmbOrder.currentText()) not in checkedList:
            if checkedList:
                item = self.cmbOrder.model().item(self.cmbOrder.currentIndex())
                if item:
                    item.setEnabled(False)
                self.cmbOrder.setCurrentIndex(forceInt(self.cmbAvailableOrders.getIndex(checkedList[0])))
            else:
                self.cmbOrder.setCurrentIndex(-1)


    @pyqtSignature('QString')
    def on_edtVisitServiceFilter_textChanged(self, txt):
        self.btnVisitServiceFilterTest.setEnabled(bool(trim(txt)))


    @pyqtSignature('')
    def on_btnSelectService_clicked(self):
        serviceId = selectService(self, self.cmbService)
        if serviceId:
            self.cmbService.setValue(serviceId)


    @pyqtSignature('')
    def on_btnSelectRelegateOrg_clicked(self):
        orgId = selectOrganisation(self, self.cmbRelegateOrg.value(), False, filter=CPolyclinicComboBox.filter)
        self.cmbRelegateOrg.update()
        if orgId:
            self.cmbRelegateOrg.setValue(orgId)


    @pyqtSignature('bool')
    def on_chkIsTakenTissue_clicked(self, checked):
        self.modelStatusActions.cols()[2].setReadOnly(not checked)
        self.modelDiagnosticActions.cols()[2].setReadOnly(not checked)
        self.modelCureActions.cols()[2].setReadOnly(not checked)
        self.modelMiscActions.cols()[2].setReadOnly(not checked)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelStatusActions_currentRowChanged(self, current, previous):
        actionTypeIndex = self.tblStatusActions.currentIndex()
        if actionTypeIndex and actionTypeIndex.isValid():
            item = self.tblStatusActions.currentItem()
            if item:
                actionTypeId = forceRef(item.value(self.modelStatusActions.cols()[0].fieldName()))
                self.modelStatusActions.cols()[0].setCurrentActionType(actionTypeId)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelDiagnosticActions_currentRowChanged(self, current, previous):
        actionTypeIndex = self.tblDiagnosticActions.currentIndex()
        if actionTypeIndex and actionTypeIndex.isValid():
            item = self.tblDiagnosticActions.currentItem()
            if item:
                actionTypeId = forceRef(item.value(self.modelDiagnosticActions.cols()[0].fieldName()))
                self.modelDiagnosticActions.cols()[0].setCurrentActionType(actionTypeId)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelCureActions_currentRowChanged(self, current, previous):
        actionTypeIndex = self.tblCureActions.currentIndex()
        if actionTypeIndex and actionTypeIndex.isValid():
            item = self.tblCureActions.currentItem()
            if item:
                actionTypeId = forceRef(item.value(self.modelCureActions.cols()[0].fieldName()))
                self.modelCureActions.cols()[0].setCurrentActionType(actionTypeId)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelMiscActions_currentRowChanged(self, current, previous):
        actionTypeIndex = self.tblMiscActions.currentIndex()
        if actionTypeIndex and actionTypeIndex.isValid():
            item = self.tblMiscActions.currentItem()
            if item:
                actionTypeId = forceRef(item.value(self.modelMiscActions.cols()[0].fieldName()))
                self.modelMiscActions.cols()[0].setCurrentActionType(actionTypeId)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionType_status_currentRowChanged(self, current, previous):
        actionTypeIndex = self.tblActionType_status.currentIndex()
        if actionTypeIndex and actionTypeIndex.isValid():
            item = self.tblActionType_status.currentItem()
            if item:
                actionTypeId = forceRef(item.value(self.modelActionType_status.cols()[0].fieldName()))
                self.modelActionType_status.cols()[0].setCurrentActionType(actionTypeId)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionType_diagnostic_currentRowChanged(self, current, previous):
        actionTypeIndex = self.tblActionType_diagnostic.currentIndex()
        if actionTypeIndex and actionTypeIndex.isValid():
            item = self.tblActionType_diagnostic.currentItem()
            if item:
                actionTypeId = forceRef(item.value(self.modelActionType_diagnostic.cols()[0].fieldName()))
                self.modelActionType_diagnostic.cols()[0].setCurrentActionType(actionTypeId)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionType_cure_currentRowChanged(self, current, previous):
        actionTypeIndex = self.tblActionType_cure.currentIndex()
        if actionTypeIndex and actionTypeIndex.isValid():
            item = self.tblActionType_cure.currentItem()
            if item:
                actionTypeId = forceRef(item.value(self.modelActionType_cure.cols()[0].fieldName()))
                self.modelActionType_cure.cols()[0].setCurrentActionType(actionTypeId)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionType_other_currentRowChanged(self, current, previous):
        actionTypeIndex = self.tblActionType_other.currentIndex()
        if actionTypeIndex and actionTypeIndex.isValid():
            item = self.tblActionType_other.currentItem()
            if item:
                actionTypeId = forceRef(item.value(self.modelActionType_other.cols()[0].fieldName()))
                self.modelActionType_other.cols()[0].setCurrentActionType(actionTypeId)


    @pyqtSignature('int')
    def on_cmbFinance_currentIndexChanged(self, index):
        self.chkCanHavePayableActions.setEnabled(self.cmbFinance.code()!='4')


    @pyqtSignature('')
    def on_btnVisitRegExpTest_pressed(self):
        self.regExpTestStr = testRegExpServiceModifier(self, self.edtVisitRegExp.toPlainText(), self.regExpTestStr)


    @pyqtSignature('')
    def on_btnVisitServiceFilterTest_pressed(self):
        if self.checkVisitServiceFilter():
            self.visitServiceFilterTestStr = testServiceFilter(self, self.edtVisitServiceFilter.text(), self.visitServiceFilterTestStr)
#
# ##########################################################################
#

class CEventFilterDialog(QtGui.QDialog, Ui_EventFilterDialog):
    def __init__(self,  parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.edtName.setFocus(Qt.ShortcutFocusReason)
        self.cmbPurpose.setTable('rbEventTypePurpose', addNone=True)
        self.cmbProfile.setTable('rbEventProfile', addNone=True)
        self.cmbMedicalAidKind.setTable('rbMedicalAidKind', addNone=True)
        self.cmbMedicalAidType.setTable('rbMedicalAidType', addNone=True)
        self.cmbSex.addItems(SexList)
        self.cmbSingleInPeriod.addItems(('', u'неделю', u'месяц', u'квартал', u'полугодие', u'год', u'раз в два года', u'раз в три года'))


    def setProps(self,  props):
        self.edtCode.setText(props.get('Код', ''))
        self.edtName.setText(props.get('Наименование', ''))
        self.edtEGISZ.setText(props.get('Код ЕГИСЗ',  ''))
        self.edtRegionalCode.setText(props.get('Региональный код', ''))
        self.edtAge.setText(props.get('Возраст', ''))
        self.edtPeriod.setText(props.get('Период', ''))
        self.edtMinDuration.setText(props.get('Мин.длительность', ''))
        self.edtMaxDuration.setText(props.get('Макс.длительность', ''))
        self.cmbPurpose.setValue(props.get('Назначение', 0))
        self.cmbProfile.setValue(props.get('Профиль', 0))
        self.cmbMedicalAidKind.setValue(props.get('Вид помощи', 0))
        self.cmbMedicalAidType.setValue(props.get('Тип помощи', 0))
        self.cmbSex.setCurrentIndex(props.get('Пол', 0))
        self.cmbSingleInPeriod.setCurrentIndex(props.get('Раз в', 0))


    def props(self):
        result = {}
        result['Код'] = forceStringEx(self.edtCode.text())
        result['Наименование'] = forceStringEx(self.edtName.text())
        result['Код ЕГИСЗ'] = forceStringEx(self.edtEGISZ.text())
        result['Региональный код'] = forceStringEx(self.edtRegionalCode.text())
        result['Возраст'] = forceStringEx(self.edtAge.text())
        result['Период'] = forceStringEx(self.edtPeriod.text())
        result['Мин.длительность'] = forceStringEx(self.edtMinDuration.text())
        result['Макс.длительность'] = forceStringEx(self.edtMaxDuration.text())
        result['Назначение'] = self.cmbPurpose.getValue()
        result['Профиль'] = self.cmbProfile.getValue()
        result['Вид помощи'] = self.cmbMedicalAidKind.getValue()
        result['Тип помощи'] = self.cmbMedicalAidType.getValue()
        result['Пол'] = self.cmbSex.currentIndex()
        result['Раз в'] = self.cmbSingleInPeriod.currentIndex()
        return result


# ###############################################################################################

class CHurtEditorModel(QAbstractTableModel):

    def __init__(self, parent, fieldType):
        QAbstractTableModel.__init__(self, parent)
        assert fieldType in (0, 1)
        self._tableName = None
        self._fieldType = fieldType
        self._items = []
        self._existsList = []
        self._row2Item = {}
        self._data = None

    def setExistsList(self, existsList):
        self._existsList = existsList
        data = self.getData(self._tableName)
        row = 0
        for item in data.buff:
            if unicode(item[self._fieldType]) not in self._existsList:
                id, code, name      = item
                self._row2Item[row] = item
                self._items.append((QVariant(code), QVariant(name)))
                row += 1
        self.reset()


    def getData(self, tableName):
        if self._data is None:
            self._data = CRBModelDataCache.reset(tableName)
            self._data = CRBModelDataCache.getData(tableName, addNone=False)
            self._data.load()
        return self._data


    def setTable(self, tableName):
        self._tableName = tableName


    def rowCount(self, index=None):
        return len(self._items)

    def columnCount(self, index=None):
        return 2

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section == 0:
                    return QVariant(u'Код')
                elif section == 1:
                    return QVariant(u'Наименование')
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.DisplayRole:
            return self._items[index.row()][index.column()]
        return QVariant()

    def getValue(self, row):
        return self._row2Item[row][self._fieldType]


class CHurtColEditor(QtGui.QWidget):
    __pyqtSignals__ = ('editingFinished()',
                       'commit()',
                      )
    typeSign  = {0:'%d', 1:'%s'}
    def __init__(self, parent, fieldType):
        QtGui.QWidget.__init__(self, parent)
        self._fieldType = fieldType
        self.edtItems = QtGui.QLineEdit(self)
        self.tblItems = CRBPopupView(self)
        self.layout = QtGui.QGridLayout(self)
        self.layout.setMargin(0)
        self.layout.setSpacing(0)

        self.layout.addWidget(self.edtItems, 0, 0)
        self.layout.addWidget(self.tblItems, 1, 0)


        self.modelItems = CHurtEditorModel(self, fieldType)
        self.tblItems.setModel(self.modelItems)

        self.connect(self.tblItems, SIGNAL('doubleClicked(QModelIndex)'), self.tblItemsDoubleClicked)

        self.edtItems.installEventFilter(self)
        self.tblItems.installEventFilter(self)


    def eventFilter(self, widget, event):
        et = event.type()
        if et == QEvent.FocusOut:
            fw = QtGui.qApp.focusWidget()
            if not (fw and self.isAncestorOf(fw)):
                self.emit(SIGNAL('editingFinished()'))
        elif et == QEvent.Hide and widget == self.edtItems:
            self.emit(SIGNAL('commit()'))
        return QtGui.QWidget.eventFilter(self, widget, event)


    def tblItemsDoubleClicked(self, index):
        if index.isValid():
            value = self.modelItems.getValue(index.row())
            currentText = trim(self.text())
            if currentText and currentText[-1] != ';':
                currentText += ';%s'
            else:
                currentText += '%s'
            text = (currentText%CHurtColEditor.typeSign[self._fieldType])%value
            self.edtItems.setText(text)


    def text(self):
        return self.edtItems.text()


    def setText(self, value):
        self.edtItems.setText(value)
        existsList = self.parseValue(value)
        self.modelItems.setExistsList(existsList)


    def setTable(self, tableName):
        self.modelItems.setTable(tableName)


    def parseValue(self, value):
        result = []
        for item in value.split(';'):
            result.append(trim(item))
        return result


class CHurtCol(CInDocTableCol):
    idField   = 0
    codeField = 1
    def __init__(self, name, fieldName, tableName, fieldType=codeField):
        CInDocTableCol.__init__(self, name, fieldName, 12)
        self._fieldType = fieldType
        self._tableName = tableName


    def createEditor(self, parent):
        editor = CHurtColEditor(parent, self._fieldType)
        editor.setTable(self._tableName)
        return editor


class CEventTypeModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'EventType_Event', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Событие', 'eventType_id',  30, 'EventType', filter='EventType.deleted = 0')).setSortable(True)


    def loadItems(self, masterId):
        if masterId:
            db = QtGui.qApp.db
            tableET = db.table('EventType')
            tableETE = db.table('EventType_Event')
            queryTable = tableET.innerJoin(tableETE, tableETE['master_id'].eq(tableET['id']))
            cols = [tableETE['eventType_id'],
                    tableETE['id'],
                    tableETE['master_id']
                    ]
            cond = [tableETE['master_id'].eq(masterId),
                    tableET['deleted'].eq(0)
                    ]
            if self._filter:
                cond.append(self._filter)
            self._items = db.getRecordList(queryTable, cols, cond, 'EventType_Event.id')
        self.reset()


    def saveItems(self, masterId):
        if self._items is not None:
            db = QtGui.qApp.db
            table = self._table
            masterId = toVariant(masterId)
            masterIdFieldName = self._masterIdFieldName
            idFieldName = self._idFieldName
            idList = []
            for idx, record in enumerate(self._items):
                record.setValue(masterIdFieldName, masterId)
                if self._idxFieldName:
                    record.setValue(self._idxFieldName, toVariant(idx))
                if self._extColsPresent:
                    outRecord = self.removeExtCols(record)
                else:
                    outRecord = record
                id = db.insertOrUpdate(table, outRecord)
                record.setValue(idFieldName, toVariant(id))
                idList.append(id)
                self.saveDependence(idx, id)

            filter = [table[masterIdFieldName].eq(masterId),
                      'NOT ('+table[idFieldName].inlist(idList)+')']
            db.deleteRecord(table, filter)

    def checkValues(self):
        for item in self._items:
            id = forceInt(item.value('eventType_id'))
            if not id:
                QtGui.QMessageBox.critical (None, u'Внимание!', u'Одно из указанных значений типов событий некорректно', QtGui.QMessageBox.Ok)
                return False
        return True


class CDiagnosticsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'EventType_Diagnostic', 'id', 'eventType_id', parent)
        self.addCol(CRBInDocTableCol(   u'Специальность',  'speciality_id', 20, 'rbSpeciality'))
        self.addCol(CRBInDocTableCol(   u'Должность',      'post_id', 10, 'rbPost', defaultHidden=True))
        self.addCol(CBoolInDocTableCol( u'Возможен ВОП',   'mayEngageGP', 3))
        self.addCol(CEnumInDocTableCol( u'Пол',            'sex',  5, ('', u'М', u'Ж')))
        self.addCol(CInDocTableCol(     u'Возраст',        'age',  12))
        self.addCol(CEnumInDocTableCol( u'Период контроля','controlPeriod', 5, (u'', u'начало События', u'начало года', u'конец года')))
        self.addCol(CInDocTableCol(     u'Код МКБ по умолчанию',  'defaultMKB', 5))
        self.addCol(CRBInDocTableCol(   u'ДН по умолчанию','defaultDispanser_id', 10, 'rbDispanser')).setToolTip(u'Диспансерное наблюдение')
        self.addCol(CRBInDocTableCol(   u'ГЗ по умолчанию','defaultHealthGroup_id', 10, 'rbHealthGroup')).setToolTip(u'Группа здоровья')
        self.addCol(CRBInDocTableCol(   u'Услуга визита',  'service_id', 20, 'rbService', showFields=CRBComboBox.showCodeAndName))
        self.addCol(CRBInDocTableCol(   u'Тип визита',     'visitType_id', 20, 'rbVisitType'))
        self.addCol(CIntInDocTableCol(  u'Действителен',   'actuality',      5))
        self.addCol(CIntInDocTableCol(  u'Группа выбора',  'selectionGroup', 15, low=-100, high=100))
        self.addCol(CHurtCol(u'Типы вредности', 'hurtType', 'rbHurtType'))
        self.addCol(CHurtCol(u'Факторы вредности', 'hurtFactorType', 'rbHurtFactorType'))

    def afterUpdateEditorGeometry(self, editor, index):
        if index.column() in (self.getColIndex('hurtType'), self.getColIndex('hurtFactorType')):
            editor.resize(editor.width(), 12*editor.height())


class CActionsModel(CInDocTableModel, ActionTypeServiceMixin):
    def __init__(self, parent, actionTypeClass):
        CInDocTableModel.__init__(self, 'EventType_Action', 'id', 'eventType_id', parent)
        ActionTypeServiceMixin.__init__(self)
        self._parent = parent
        self.addCol(CActionTypeFindInDocTableCol(u'Наименование',   'actionType_id',20, 'ActionType', actionTypeClass))
        self.addCol(CRBInDocTableCol(   u'Специальность',  'speciality_id', 20, 'rbSpeciality'))
        self.addCol(CRBInDocTableCol(   u'Тип ткани',      'tissueType_id', 20, 'rbTissueType')).setReadOnly(True)
        self.addCol(CEnumInDocTableCol( u'Пол',            'sex',  5, ['', u'М', u'Ж']))
        self.addCol(CInDocTableCol(     u'Возраст',        'age',  12))
        self.addCol(CEnumInDocTableCol( u'Период контроля','controlPeriod', 5, (u'', u'начало События', u'начало года', u'конец года')))
        self.addCol(CIntInDocTableCol(  u'Действителен',   'actuality',      10))
        self.addCol(CIntInDocTableCol(  u'Группа выбора',  'selectionGroup', 15, low=-100, high=100))
        self.addCol(CBoolInDocTableCol( u'Выставлять',  'expose', 5))
        self.addCol(CEnumInDocTableCol( u'Платно',         'payable',  5, [u'по событию', u'по выбору', u'обязательно']))
        self.addCol(CHurtCol(u'Типы вредности', 'hurtType', 'rbHurtType'))
        self.addCol(CHurtCol(u'Факторы вредности', 'hurtFactorType', 'rbHurtFactorType'))
        self.actionTypeClass = actionTypeClass
        self.actionTypeIdList = getActionTypeIdListByClass(actionTypeClass)
        db = QtGui.qApp.db
        table = db.table('EventType_Action')
        self.setFilter(table['actionType_id'].inlist(self.actionTypeIdList))


    def afterUpdateEditorGeometry(self, editor, index):
        if index.column() in (self.getColIndex('hurtType'), self.getColIndex('hurtFactorType')):
            editor.resize(editor.width(), 12*editor.height())

    
    def checkValues(self, widget):
        for num, item in enumerate(self._items):
            id = forceRef(item.value('actionType_id'))
            if not id:
                return self._parent.checkInputMessage(u'тип действия', False, widget, num, self.getColIndex('actionType_id'))
        return True
    

    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.setValue('expose', toVariant(True))
        return result


    def getActionTypeCluster(self, actionTypeId, actionTypeClass):
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        result = db.getLeafes(tableActionType,
                              'group_id',
                              actionTypeId,
                              db.joinAnd([tableActionType['deleted'].eq(0),
                                          tableActionType['class'].eq(actionTypeClass)
                                         ]
                                        )
                             )
        return sorted(result) if result else [actionTypeId]


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            noWriteList = True
            column = index.column()
            row = index.row()
            if row == len(self._items):
                if value.isNull():
                    return False
                if column == self.getColIndex('actionType_id'):
                    outWriteList, noWriteList = self.writeActionTypeIdList(forceRef(value), row, column)
                    if outWriteList:
                        return True
                self._items.append(self.getEmptyRecord())
                count = len(self._items)
                rootIndex = QModelIndex()
                self.beginInsertRows(rootIndex, count, count)
                self.insertRows(count, 1, rootIndex)
                self.endInsertRows()
            record = self._items[row]
            col = self._cols[column]
            record.setValue(col.fieldName(), value)
            self.emitCellChanged(row, column)
            if noWriteList and column == self.getColIndex('actionType_id'):
                outWriteList, noWriteList = self.writeActionTypeIdList(forceRef(value), row, column, True)
                if outWriteList:
                    return True
            return True
        return CInDocTableModel.setData(self, index, value, role)


    def writeActionTypeIdList(self, actionTypeId, row, column, these=False):
        if actionTypeId:
            actionTypeIdList = self.getActionTypeCluster(actionTypeId, self.actionTypeClass)
            if these:
                actionTypeIdList = list(set(actionTypeIdList)-set([actionTypeId]))
            if len(actionTypeIdList) > 1:
                if QtGui.QMessageBox.warning(None,
                   u'Внимание!',
                   u'Добавить группу действий?',
                   QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                   QtGui.QMessageBox.Cancel) == QtGui.QMessageBox.Ok:
                    for atId in actionTypeIdList:
                        self._items.append(self.getEmptyRecord())
                        count = len(self._items)
                        rootIndex = QModelIndex()
                        self.beginInsertRows(rootIndex, count, count)
                        self.insertRows(count, 1, rootIndex)
                        self.endInsertRows()
                        record = self._items[count-1]
                        col = self._cols[column]
                        record.setValue(col.fieldName(), toVariant(atId))
                        self.emitCellChanged(count-1, column)
                    return True, False
                else:
                    return False, False
            else:
                return False, False
        return False, False


    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.ToolTipRole:
                actionType_id = forceInt(self.items()[row].value('actionType_id'))
                if actionType_id != 0:
                    actionTypeCache = CActionTypeCache.getById(actionType_id)
                    showInForm = actionTypeCache.showInForm
                    code = actionTypeCache.code
                    numService = actionTypeCache.nomenclativeServiceId
                    if showInForm == 0:
                        return u"Не разрешается выбор данного типа действия в формах ввода событий"
                    elif not self.checkActionTypeService(actionType_id, code, numService):
                        return u"Услуга в типе действия не является актуальной"
                    else:
                        return u""

            if role == Qt.FontRole:
                actionType_id = forceInt(self.items()[row].value('actionType_id'))
                if actionType_id != 0:
                    actionTypeCache = CActionTypeCache.getById(actionType_id)
                    showInForm = actionTypeCache.showInForm
                    code = actionTypeCache.code
                    numService = actionTypeCache.nomenclativeServiceId
                    font = QFont()
                    if showInForm == 0:
                        font.setItalic(True)
                        font.setBold(True)
                        return font
                    elif not self.checkActionTypeService(actionType_id, code, numService):
                        font.setItalic(True)
                        font.setBold(True)
                        return font
                    else:
                        return font

        return CInDocTableModel.data(self, index, role)


class CActionTypeModel(CInDocTableModel):
    def __init__(self, parent, actionTypeClass):
        CInDocTableModel.__init__(self, 'EventType_RequireAction', 'id', 'eventType_id', parent)
        self.addCol(CActionTypeFindInDocTableCol(u'Наименование', 'actionType_id', 30,'ActionType',  actionTypeClass=actionTypeClass)).setSortable(True)
        self.addCol(CRBMultiInDocTableCol(u'Специальность', 'speciality_id', 30, 'rbSpeciality'))
        self.addCol(CMultiICDInDocTableCol(u'МКБ', 'mkb', 30))
        self.addCol(CIntInDocTableCol(u'Группа выбора', 'selectionGroup', 15))

        self.classesVisible = True
        self.actionTypeClass = actionTypeClass
        self.actionTypeIdList = self.getActionTypeIdList(actionTypeClass)
        db = QtGui.qApp.db
        table = db.table('EventType_RequireAction')
        self.setFilter(table['actionType_id'].inlist(self.actionTypeIdList))

    def getActionTypeIdList(self, actionTypeClass):
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        return db.getIdList(tableActionType, 'id',
                     [tableActionType['deleted'].eq(0), tableActionType['class'].eq(actionTypeClass)])

    def checkValues(self, widget):
        for num, item in enumerate(self._items):
            id = forceRef(item.value('actionType_id'))
            if not id:
                return self._parent.checkInputMessage(u'тип действия', False, widget, num, self.getColIndex('actionType_id'))
        return True


class COrgStructModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'EventType_OrgStruct', 'id', 'eventType_id', parent)
        self.addCol(COrgStructureInDocTableCol(u'Подразделение', 'orgstruct_id', 20))


class CPersonsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'EventType_Persons', 'id', 'eventType_id', parent)
        self.addCol(CPersonFindInDocTableCol(u'Врач', 'person_id', 20, 'vrbPersonWithSpeciality', parent=parent))

class CRBMultiInDocTableCol(CRBInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, **params):
        CRBInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)

    def toString(self, val, record):
        if not val:
            return toVariant('')

        db = QtGui.qApp.db
        table = db.table(self.tableName)
        id_list = [id_str.strip() for id_str in forceString(val).split(',') if id_str.strip()]

        if not id_list:
            return toVariant('')

        names = []
        for id in id_list:
            if id.isdigit():
                record = db.getRecordEx(table, 'name', [table['id'].eq(int(id))])
                if record:
                    names.append(forceString(record.value('name')))

        return toVariant(', '.join(names) if names else u'Неизвестно')

    def createEditor(self, parent):
        editor = CRBMultivalueComboBox(parent)
        editor.setTable(self.tableName, addNone=False, filter=self.filter)
        return editor

    def setEditorData(self, editor, value, record):
        editor.setValue(forceString(value))

    def getEditorData(self, editor):
        return toVariant(editor.value())
