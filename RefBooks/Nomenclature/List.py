# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import weakref

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QVariant, pyqtSignature, SIGNAL, QDate

from library.Counter import CCounterController
from library.Identification import findByIdentification
from library.abstract import abstract
from library.crbcombobox import CRBComboBox
from library.DialogBase import CDialogBase
from library.InDocTable import (CInDocTableModel, CRecordListModel, CInDocTableCol, CRBInDocTableCol,
                                CFloatInDocTableCol, CEnumInDocTableCol)
from library.interchange import (getDateEditValue, getLineEditValue, getRBComboBoxValue, getSpinBoxValue,
                                 setDateEditValue, setLineEditValue, setSpinBoxValue, setRBComboBoxValue,
                                 setComboBoxValue, getComboBoxValue)
from library.ItemsListDialog import CItemsListDialog, CItemEditorBaseDialog
from library.IdentificationModel import CIdentificationModel, checkIdentification
from library.TableModel import CRefBookCol, CTextCol, CEnumCol
from library.Utils import forceRef, forceString, forceStringEx, toVariant, forceBool, forceInt, forceDouble, forceDate

from RefBooks.Tables import rbCode, rbName
from RefBooks.NomenclatureActiveSubstance.ActiveSubstanceComboBox import CActiveSubstanceComboBox
from RefBooks.Nomenclature.NomenclatureFillMNNDialog import CNomenclatureFillMNNDialog
from Stock.NomenclatureComboBox import CNomenclatureInDocTableCol, getFeaturesAndValues
from .RBDiscrepancies import CRBDiscrepancies

from .Ui_RBNomenclatureEditor import Ui_ItemEditorDialog
from .Ui_RBNomenclatureFilter import Ui_ItemFilterDialog


class CRBNomenclatureList(CItemsListDialog):
    def __init__(self, parent, forSelect=False):
        CItemsListDialog.__init__(self, parent, [
            CRefBookCol(u'Тип', ['type_id'], 'rbNomenclatureType', 20),
            CTextCol(u'Код', [rbCode], 20),
            CTextCol(u'Региональный код', ['regionalCode'], 20),
            CTextCol(u'Наименование', [rbName], 40),
            CTextCol(u'Дозировка', ['dosageValue'], 10),
            CRefBookCol(u'Ед. дозировки', ['unit_id'], 'rbUnit', 20),
            CRefBookCol(u'Форма выпуска', ['lfForm_id'], 'rbLfForm', 40),
            CTextCol(u'Дата включения', ['inDate'], 40),
            CTextCol(u'Дата исключения', ['exDate'], 40),
            CTextCol(u'Комплектность', ['completeness'], 40),
            CEnumCol(u'Наркот./психотроп. вещество', ['isNarcotic'], [u'Нет', u'Да'], 55),
        ], 'rbNomenclature', [rbCode, rbName, 'dosageValue', 'inDate', 'exDate'], forSelect,
                                  filterClass=CRBNomenclatureListFilter
                                  )
        self.setWindowTitleEx(u'Номенклатура лекарственных средств и изделий медицинского назначения')
        if self.forSelect:
            self.parent = parent

    def preSetupUi(self):
        CItemsListDialog.preSetupUi(self)
        self.addObject('actDuplicate', QtGui.QAction(u'Дублировать', self))
        self.addObject('actDelete', QtGui.QAction(u'Удалить', self))

    def postSetupUi(self):
        CItemsListDialog.postSetupUi(self)
        self.tblItems.createPopupMenu([self.actDuplicate, '-', self.actDelete])
        self.connect(self.tblItems.popupMenu(), SIGNAL('aboutToShow()'), self.popupMenuAboutToShow)

    def getItemEditor(self):
        return CRBNomenclatureEditor(self)

    def generateFilterByProps(self, props):
        db = QtGui.qApp.db
        cond = CItemsListDialog.generateFilterByProps(self, props)
        table = self.model.table()
        code = props.get('code', None)
        name = props.get('name', None)
        regionalCode = props.get('regionalCode', None)
        internationalNonproprietaryName = props.get('internationalNonproprietaryName', None)
        ATC = props.get('ATC', None)
        producer = props.get('producer', None)
        classId = props.get('classId', None)
        kindId = props.get('kindId', None)
        typeId = props.get('typeId', None)

        if code:
            cond.append(table['code'].like(code))
        if name:
            orCond = db.joinOr([
                table['name'].contain(name),
                table['originName'].contain(name),
            ])
            cond.append(orCond)
        if regionalCode:
            cond.append(table['regionalCode'].like(regionalCode))
        if internationalNonproprietaryName:
            orCond = db.joinOr([
                table['internationalNonproprietaryName'].contain(internationalNonproprietaryName),
                table['mnnLatin'].contain(internationalNonproprietaryName),
            ])
            cond.append(orCond)
        if ATC:
            cond.append(table['ATC'].like(ATC))
        if producer:
            cond.append(table['producer'].like(producer))

        if typeId:
            cond.append(table['type_id'].eq(typeId))
        elif kindId:
            cond.append(table['type_id'].inlist(self.getTypeIdListByKind(kindId)))
        elif classId:
            cond.append(table['type_id'].inlist(self.getTypeIdListByClass(classId)))
        return cond

    def popupMenuAboutToShow(self):
        currentItemId = self.currentItemId()
        self.actDuplicate.setEnabled(bool(currentItemId))
        self.actDelete.setEnabled(bool(currentItemId))

    @pyqtSignature('')
    def on_actDuplicate_triggered(self):
        def duplicateCurrentInternal():
            currentItemId = self.currentItemId()
            if currentItemId:
                db = QtGui.qApp.db
                table = db.table('rbNomenclature')
                db.transaction()
                try:
                    record = db.getRecord(table, '*', currentItemId)
                    record.setValue('code', toVariant(forceString(record.value('code')) + '_1'))
                    record.setNull('id')
                    newItemId = db.insertRecord(table, record)
                    db.commit()
                except:
                    db.rollback()
                    QtGui.qApp.logCurrentException()
                    raise
                self.renewListAndSetTo(newItemId)

        QtGui.qApp.call(self, duplicateCurrentInternal)

    @pyqtSignature('')
    def on_actDelete_triggered(self):
        def deleteCurrentInternal():
            currentItemId = self.currentItemId()
            if currentItemId:
                row = self.tblItems.currentIndex().row()
                db = QtGui.qApp.db
                table = db.table('rbNomenclature')
                db.deleteRecord(table, table['id'].eq(currentItemId))
                self.renewListAndSetTo()
                self.tblItems.setCurrentRow(row)

        QtGui.qApp.call(self, deleteCurrentInternal)

    @staticmethod
    def getKindIdListByClass(classId):
        db = QtGui.qApp.db
        tableKind = db.table('rbNomenclatureKind')
        kindIdList = db.getIdList(tableKind, 'id', tableKind['class_id'].eq(classId))
        return kindIdList

    @staticmethod
    def getTypeIdListByKindList(kindIdList):
        db = QtGui.qApp.db
        tableType = db.table('rbNomenclatureType')
        typeIdList = db.getIdList(tableType, 'id', tableType['kind_id'].inlist(kindIdList))
        return typeIdList

    @staticmethod
    def getTypeIdListByKind(kindId):
        typeIdList = CRBNomenclatureList.getTypeIdListByKindList([kindId])
        return typeIdList

    @staticmethod
    def getTypeIdListByClass(classId):
        kindIdList = CRBNomenclatureList.getKindIdListByClass(classId)
        typeIdList = CRBNomenclatureList.getTypeIdListByKindList(kindIdList)
        return typeIdList


#
# ##########################################################################
#


class CRBNomenclatureListFilter(CDialogBase, Ui_ItemFilterDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Фильтр ЛСиИМН')
        self.cmbClass.setTable('rbNomenclatureClass', True)
        self.cmbKind.setTable('rbNomenclatureKind', True)
        self.cmbType.setTable('rbNomenclatureType', True)

    @pyqtSignature('int')
    def on_cmbClass_currentIndexChanged(self, index):
        self.setKindFilter()
        self.setTypeFilter()

    @pyqtSignature('int')
    def on_cmbKind_currentIndexChanged(self, index):
        self.setTypeFilter()

    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == self.buttonBox.Reset:
            self.setProps({})

    def setKindFilter(self):
        self.cmbKind.setFilter(self.formKindFilter(self.cmbClass.value()))

    def setTypeFilter(self):
        self.cmbType.setFilter(self.formTypeFilter(self.cmbClass.value(), self.cmbKind.value()))

    def setProps(self, props):
        self.edtCode.setText(props.get('code', ''))
        self.edtName.setText(props.get('name', ''))
        self.edtInternationalNonproprietaryName.setText(props.get('internationalNonproprietaryName', ''))
        self.edtRegionalCode.setText(props.get('regionalCode', ''))
        self.edtATC.setText(props.get('ATC', ''))
        self.edtProducer.setText(props.get('producer', ''))
        self.cmbClass.setValue(props.get('classId', None))
        self.cmbKind.setValue(props.get('kindId', None))
        self.cmbType.setValue(props.get('typeId', None))

    def props(self):
        code = forceStringEx(self.edtCode.text())
        name = forceStringEx(self.edtName.text())
        internationalNonproprietaryName = forceStringEx(self.edtInternationalNonproprietaryName.text())
        regionalCode = forceStringEx(self.edtRegionalCode.text())
        ATC = forceStringEx(self.edtATC.text())
        producer = forceStringEx(self.edtProducer.text())
        classId = self.cmbClass.value()
        kindId = self.cmbKind.value()
        typeId = self.cmbType.value()
        result = {}
        if code:
            result['code'] = code
        if name:
            result['name'] = name
        if internationalNonproprietaryName:
            result['internationalNonproprietaryName'] = internationalNonproprietaryName
        if regionalCode:
            result['regionalCode'] = regionalCode
        if ATC:
            result['ATC'] = ATC
        if producer:
            result['producer'] = producer
        if classId:
            result['classId'] = classId
        if kindId:
            result['kindId'] = kindId
        if typeId:
            result['typeId'] = typeId
        return result

    @staticmethod
    def formKindFilter(classId):
        if classId:
            table = QtGui.qApp.db.table('rbNomenclatureKind')
            return table['class_id'].eq(classId)
        return ''

    @staticmethod
    def formTypeFilter(classId, kindId):
        db = QtGui.qApp.db
        table = db.table('rbNomenclatureType')
        if kindId:
            return table['kind_id'].eq(kindId)
        else:
            if classId:
                kindIdList = CRBNomenclatureList.getKindIdListByClass(classId)
                return table['kind_id'].inlist(kindIdList)
        return ''


#
# ##########################################################################
#

class CRBNomenclatureEditor(CItemEditorBaseDialog, Ui_ItemEditorDialog):
    def __init__(self, parent):
        CItemEditorBaseDialog.__init__(self, parent, 'rbNomenclature')
        self.addModels('Composition', CCompositionModel(self))
        self.addModels('Features', CFeaturesModel(self))
        self.addModels('Ingredients', CIngredientsModel(self))
        self.addModels('Analogs', CAnalogsModel(self))
        self.addModels('UnitRatio', CUnitRatioModel(self))
        self.addModels('UsingTypes', CUsingTypesModel(self))
        self.addModels('Identification', CIdentificationModel(self, 'rbNomenclature_Identification', 'rbNomenclature'))
        self.addObject('actFillFeaturesBySiblings', QtGui.QAction(u'Добавить характеристики', self))
        self.setupUi(self)
        self.setWindowTitleEx(u'Лекарственное средство или изделие медицинского назначения')
        self.cmbClass.setTable('rbNomenclatureClass', True)
        self.cmbKind.setTable('rbNomenclatureKind', True)
        self.cmbType.setTable('rbNomenclatureType', True)
        self.cmbUnit.setTable('rbUnit', True)
        self.cmbDefaultClientUnit.setTable('rbUnit', True)
        self.cmbDefaultStockUnit.setTable('rbUnit', True)
        # self.cmbLfForm.setTable('rbLfForm', True)
        self.setModels(self.tblComposition, self.modelComposition, self.selectionModelComposition)
        self.setModels(self.tblFeatures, self.modelFeatures, self.selectionModelFeatures)
        self.tblComposition.addPopupDelRow()
        self.tblFeatures.addPopupAction(self.actFillFeaturesBySiblings)
        self.tblFeatures.addPopupSeparator()
        self.tblFeatures.addMoveRow()
        self.tblFeatures.addPopupDuplicateCurrentRow()
        self.tblFeatures.addPopupSelectAllRow()
        self.tblFeatures.addPopupClearSelectionRow()
        self.tblFeatures.addPopupSeparator()
        self.tblFeatures.addPopupDelRow()

        self.tblUnitRatio.addPopupDelRow()

        self.setModels(self.tblIngredients, self.modelIngredients, self.selectionModelIngredients)
        self.tblIngredients.addPopupSelectAllRow()
        self.tblIngredients.addPopupClearSelectionRow()
        self.tblIngredients.addPopupSeparator()
        self.tblIngredients.addPopupDelRow()

        self.modelAnalogs.setEnableAppendLine(True)
        self.setModels(self.tblAnalogs, self.modelAnalogs, self.selectionModelAnalogs)
        self.setModels(self.tblUnitRatio, self.modelUnitRatio, self.selectionModelUnitRatio)
        self.setModels(self.tblIdentification, self.modelIdentification, self.selectionModelIdentification)
        # self.tblAnalogs.setModel(self.modelAnalogs)
        self.tblAnalogs.addPopupSelectAllRow()
        self.tblAnalogs.addPopupClearSelectionRow()
        self.tblAnalogs.addPopupSeparator()
        self.tblAnalogs.addPopupDelRow()
        self.tblIdentification.addPopupDelRow()
        self.tblIdentification.setDelRowsChecker(self.modelIdentification.delRowsChecker)
        self.setModels(self.tblUsingTypes, self.modelUsingTypes, self.selectionModelUsingTypes)
        self.tblUsingTypes.addPopupDelRow()
        self.setupDirtyCather()
        self.connect(QtGui.qApp, SIGNAL('sgtinReceived(QString)'), self.onSgtinReceived)
        self.connect(QtGui.qApp, SIGNAL('gtinReceived(QString)'), self.onGtinReceived)
        self.eslkpUUID = None
        self.unitUrn = 'urn:esklp:unitName'
        self.urn = 'urn:gtin'
        self.dictDiscrepancies = {}
        self.orderedListDiscrepancies = []
        self.systemId = forceRef(QtGui.qApp.db.translate('rbAccountingSystem', 'urn', self.urn, 'id'))
        counterRBCode = QtGui.qApp.getGlobalPreference('nomenclatureCounterCode')
        self.counterCode = ''
        if counterRBCode:
            counterId = forceRef(QtGui.qApp.db.translate('rbCounter', 'code', counterRBCode, 'id'))
            if counterId:
                if QtGui.qApp.counterController():
                    QtGui.qApp.resetAllCounterValueIdReservation()
                else:
                    QtGui.qApp.delAllCounterValueIdReservation()
                QtGui.qApp.setCounterController(None)
                QtGui.qApp.setCounterController(CCounterController(self))
                self.counterCode = QtGui.qApp.getDocumentNumber(None, counterId)
        if not self.edtCode.text():
            self.edtCode.setText(self.counterCode)

    def checkDataEntered(self):
        if not checkIdentification(self, self.tblIdentification):
            return False

        stockDefaultId = self.cmbDefaultStockUnit.value()
        clientDefaultId = self.cmbDefaultClientUnit.value()

        if not self.edtCode.text():
            return self.checkInputMessage(u'значение поля "Код"', skipable=False, widget=self.edtCode)
        else:
            checkUniqueCodeId = forceRef(QtGui.qApp.db.translate('rbNomenclature', 'code', self.edtCode.text(), 'id'))
            if checkUniqueCodeId and checkUniqueCodeId != self.itemId():
                return self.checkValueMessage(u'Введённое значение "%s" поля "Код" не является уникальным.\n'
                                              u'Введите новое значение' % self.edtCode.text(), False, self.edtCode)

        if not (stockDefaultId or clientDefaultId):
            return self.checkInputMessage(u'расходную и упаковочную единицы по умолчанию', skipable=True,
                                          widget=self.cmbDefaultStockUnit)

        if not clientDefaultId:
            return self.checkInputMessage(u'расходную единицу по умолчанию', skipable=False,
                                          widget=self.cmbDefaultClientUnit)

        items = self.modelUnitRatio.items()

        if not stockDefaultId:
            return self.checkInputMessage(u'упаковочную единицу по умолчанию', skipable=False,
                                          widget=self.cmbDefaultStockUnit)

        allUnits = set()
        for item in items:
            targetUnitId = forceRef(item.value('targetUnit_id'))
            sourceUnitId = forceRef(item.value('sourceUnit_id'))
            if targetUnitId:
                allUnits.add(targetUnitId)
            if sourceUnitId:
                allUnits.add(sourceUnitId)
        if clientDefaultId not in allUnits:
            return self.checkInputMessage(u'расходную единицу по умолчанию в таблице отношений единиц учета',
                                          skipable=False, widget=self.tblUnitRatio)

        if stockDefaultId not in allUnits:
            return self.checkInputMessage(u'упаковочную единицу по умолчанию в таблице отношений единиц учета',
                                          skipable=False, widget=self.tblUnitRatio)
        if not self.checkComposition():
            return False
        return True

    def checkComposition(self):
        result = True
        items = self.modelComposition.items()
        isActive = False
        for row, item in enumerate(items):
            activeSubstanceId = forceRef(item.value('activeSubstance_id'))
            if forceInt(item.value('type')) == 0:
                isActive = True
            result = result and (activeSubstanceId or self.checkInputMessage(u'действующее вещество', False, self.tblComposition, row))
        if len(items) > 0:
            result = result and (isActive or self.checkInputMessage(u'хоть один тип "активное"', False, self.tblComposition, None))
        return result

    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        typeId = forceRef(record.value('type_id'))
        kindId = forceRef(QtGui.qApp.db.translate('rbNomenclatureType', 'id', typeId, 'kind_id'))
        classId = forceRef(QtGui.qApp.db.translate('rbNomenclatureKind', 'id', kindId, 'class_id'))
        unitId = forceRef(record.value('unit_id'))
        lfFormId = forceRef(record.value('lfForm_id'))
        self.cmbClass.setValue(classId)
        self.cmbKind.setValue(kindId)
        self.cmbType.setValue(typeId)
        self.cmbUnit.setValue(unitId)
        self.cmbLfForm.setValue(lfFormId)
        setRBComboBoxValue(self.cmbDefaultClientUnit, record, 'defaultClientUnit_id')
        setRBComboBoxValue(self.cmbDefaultStockUnit, record, 'defaultStockUnit_id')
        setLineEditValue(self.edtCode, record, 'code')
        if not self.edtCode.text():
            self.edtCode.setText(forceString(self.counterCode))
        setLineEditValue(self.edtRegionalCode, record, 'regionalCode')
        setLineEditValue(self.edtName, record, 'name')
        setLineEditValue(self.edtOriginName, record, 'originName')
        setLineEditValue(self.edtInternationalNonproprietaryName, record, 'internationalNonproprietaryName')
        setLineEditValue(self.edtATC, record, 'ATC')
        setLineEditValue(self.edtProducer, record, 'producer')
        setSpinBoxValue(self.spnPackSize, record, 'packSize')
        setLineEditValue(self.edtMnnCode, record, 'mnnCode')
        setLineEditValue(self.edtMnnLatin, record, 'mnnLatin')
        setLineEditValue(self.edtTrnCode, record, 'trnCode')
        setLineEditValue(self.edtDosageValue, record, 'dosageValue')
        setDateEditValue(self.edtInDate, record, 'inDate')
        setDateEditValue(self.edtExDate, record, 'exDate')
        setLineEditValue(self.edtCompleteness, record, 'completeness')
        setComboBoxValue(self.cmbVEN, record, 'VEN')
        setComboBoxValue(self.cmbNarcoticSubstance, record, 'isNarcotic')
        self.eslkpUUID = forceStringEx(record.value('esklpUUID'))
        if self.eslkpUUID:
            self.cmbESLKPName.setValue(self.eslkpUUID)
            self.cmbESLKPName.setEnabled(False)
            self.cmbESLKPName.lineEdit().setStyleSheet("color: rgb(0,0,0)")
        self.btnESLKPFill.setEnabled(True if self.eslkpUUID else False)
        self.modelComposition.loadItems(self.itemId())
        self.modelFeatures.loadItems(self.itemId())
        self.modelIngredients.loadItems(self.itemId())
        self.modelAnalogs.loadItems(self.itemId(), forceRef(record.value('analog_id')))
        self.modelUnitRatio.loadItems(self.itemId())
        self.modelUsingTypes.loadItems(self.itemId())
        self.modelIdentification.loadItems(self.itemId())
        self.applyUnitWidgets()

    def applyUnitWidgets(self):
        db = QtGui.qApp.db
        table = db.table('StockTrans')
        cond = db.joinOr([table['debNomenclature_id'].eq(self.itemId()), table['creNomenclature_id'].eq(self.itemId())])
        stockTransExists = QtGui.qApp.db.existsStmt(table, cond)
        query = db.query('SELECT %s' % stockTransExists)
        exists = query.first() and forceBool(query.record().value(0))
        self.cmbDefaultStockUnit.setEnabled(not exists)

    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        record.setValue('esklpUUID', toVariant(self.cmbESLKPName.value()))
        getRBComboBoxValue(self.cmbType, record, 'type_id')
        getRBComboBoxValue(self.cmbUnit, record, 'unit_id')
        getRBComboBoxValue(self.cmbDefaultClientUnit, record, 'defaultClientUnit_id')
        getRBComboBoxValue(self.cmbDefaultStockUnit, record, 'defaultStockUnit_id')
        getRBComboBoxValue(self.cmbLfForm, record, 'lfForm_id')
        getLineEditValue(self.edtCode, record, 'code')
        getLineEditValue(self.edtRegionalCode, record, 'regionalCode')
        getLineEditValue(self.edtName, record, 'name')
        getLineEditValue(self.edtOriginName, record, 'originName')
        getLineEditValue(self.edtInternationalNonproprietaryName, record, 'internationalNonproprietaryName')
        getLineEditValue(self.edtATC, record, 'ATC')
        getLineEditValue(self.edtProducer, record, 'producer')
        getSpinBoxValue(self.spnPackSize, record, 'packSize')
        getLineEditValue(self.edtMnnCode, record, 'mnnCode')
        getLineEditValue(self.edtMnnLatin, record, 'mnnLatin')
        getLineEditValue(self.edtTrnCode, record, 'trnCode')
        getLineEditValue(self.edtDosageValue, record, 'dosageValue')
        getDateEditValue(self.edtInDate, record, 'inDate')
        getDateEditValue(self.edtExDate, record, 'exDate')
        getLineEditValue(self.edtCompleteness, record, 'completeness')
        getComboBoxValue(self.cmbVEN, record, 'VEN')
        getComboBoxValue(self.cmbNarcoticSubstance, record, 'isNarcotic')
        record.setValue('analog_id', toVariant(self.modelAnalogs.correctAlanogId()))
        return record

    def saveInternals(self, id):
        self.modelComposition.saveItems(id)
        self.modelFeatures.saveItems(id)
        self.modelIngredients.saveItems(id)
        self.modelAnalogs.saveItems(id)
        self.modelUnitRatio.saveItems(id)
        self.modelUsingTypes.saveItems(id)
        self.modelIdentification.saveItems(id)
        QtGui.qApp.delAllCounterValueIdReservation()
        QtGui.qApp.setCounterController(None)

    def setKindFilter(self):
        self.cmbKind.setFilter(CRBNomenclatureListFilter.formKindFilter(self.cmbClass.value()))

    def setTypeFilter(self):
        self.cmbType.setFilter(CRBNomenclatureListFilter.formTypeFilter(self.cmbClass.value(), self.cmbKind.value()))

    def onSgtinReceived(self, sgtin):
        self.onGtinReceived(sgtin[:14])

    def onGtinReceived(self, gtin):
        if self.systemId:
            self.modelIdentification.addIdentification(self.systemId, gtin)
        else:
            QtGui.QMessageBox.critical(self,
                                       u'Внимание!',
                                       u'Добавление идентификации невозможно, так как не найдена учётная система с urn «%s»' % self.urn,
                                       QtGui.QMessageBox.Ok,
                                       QtGui.QMessageBox.Ok)

    @pyqtSignature('QString')
    def on_cmbESLKPName_editTextChanged(self, text):
        self.btnESLKPFill.setEnabled(True if self.cmbESLKPName.currentText() else False)

    @pyqtSignature('int')
    def on_cmbClass_currentIndexChanged(self, index):
        self.setKindFilter()
        self.setTypeFilter()
        self.modelAnalogs.setDefaultClassId(self.cmbClass.value())
        self.modelAnalogs.setDefaultKindId(self.cmbKind.value())
        self.modelAnalogs.setDefaultTypeId(self.cmbType.value())

    @pyqtSignature('int')
    def on_cmbKind_currentIndexChanged(self, index):
        self.setTypeFilter()
        self.modelAnalogs.setDefaultKindId(self.cmbKind.value())
        self.modelAnalogs.setDefaultTypeId(self.cmbType.value())

    @pyqtSignature('int')
    def on_cmbDefaultStockUnit_currentIndexChanged(self, index):
        self.updateUnitRatio(self.cmbDefaultStockUnit.value(), self.cmbDefaultClientUnit.value(), self.spnPackSize.value())

    @pyqtSignature('int')
    def on_cmbDefaultClientUnit_currentIndexChanged(self, index):
        self.updateUnitRatio(self.cmbDefaultStockUnit.value(), self.cmbDefaultClientUnit.value(), self.spnPackSize.value())

    @pyqtSignature('int')
    def on_cmbType_currentIndexChanged(self, index):
        typeId = self.cmbType.value()
        self.modelAnalogs.setDefaultTypeId(typeId)
        self.actFillFeaturesBySiblings.setEnabled(bool(typeId))

    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        if index == 1:
            if len(self.modelFeatures.items()) == 0:
                self.on_actFillFeaturesBySiblings_triggered()
            else:
                classId = self.cmbClass.value()
                kindId = self.cmbKind.value()
                typeId = self.cmbType.value()
                self.modelFeatures.updateLikelyFeatures(classId, kindId, typeId)

    @pyqtSignature('')
    def on_actFillFeaturesBySiblings_triggered(self):
        classId = self.cmbClass.value()
        kindId = self.cmbKind.value()
        typeId = self.cmbType.value()
        self.modelFeatures.fillBySiblings(classId, kindId, typeId)

    @pyqtSignature('')
    def on_btnFillMNN_clicked(self):
        items = self.modelComposition.items()
        if len(items) < 1:
            self.checkInputMessage(u'состав ЛСиИМН', False, self.tblComposition, None)
            return
        dialog = CNomenclatureFillMNNDialog(self, self.modelComposition.items())
        try:
            if dialog.exec_():
                MnnRussianStr, MnnRussian, MnnLatinStr, MnnLatin = dialog.getMNNValue()
                if MnnRussian:
                    self.edtInternationalNonproprietaryName.setText(MnnRussianStr)
                if MnnLatin:
                    self.edtMnnLatin.setText(MnnLatinStr)
            else:
                row = len(self.modelComposition.items())
                self.setFocusToWidget(self.tblComposition, row if row > 0 else None)
        finally:
            dialog.deleteLater()

    def showDiscrepanciesTable(self):
        dialog = CRBDiscrepancies(self, self.dictDiscrepancies, self.orderedListDiscrepancies)
        try:
            if dialog.exec_():
                if dialog.result() == QtGui.QDialog.Accepted:
                    outDict = dialog.outDict
                    if outDict:
                        self.changeDataFromPreparedOutDict(outDict)
        finally:
            dialog.deleteLater()

    def changeDataFromPreparedOutDict(self, outDict):
        listForDeleteKeys = []
        for key, value in outDict.items():
            if hasattr(self, str(key)) and value[2]:
                if str(key).startswith('cmb'):
                    item = self.findChild(QtGui.QComboBox, str(key))
                    if key == 'cmbNarcoticSubstance':
                        item.setCurrentIndex(value[1])
                    else:
                        item.setValue(value[1])
                elif str(key).startswith('edt'):
                    item = self.findChild(QtGui.QLineEdit, str(key))
                    if not item:
                        item = self.findChild(QtGui.QDateEdit, str(key))
                        item.setDate(QDate.fromString(value[1], 'yyyy-MM-dd'))
                    else:
                        item.setText(value[1])
                elif str(key).startswith('spn'):
                    item = self.findChild(QtGui.QSpinBox, str(key))
                    item.setValue(int(float(value[1])))
                listForDeleteKeys.append(key)
        for key in listForDeleteKeys:
            if key in self.dictDiscrepancies:
                del self.dictDiscrepancies[key]
        [self.orderedListDiscrepancies.remove(key) for key in listForDeleteKeys]

        self.updateUnitRatio(self.cmbDefaultStockUnit.value(), self.cmbDefaultClientUnit.value(), self.spnPackSize.value())

    @pyqtSignature('')
    def on_btnESLKPFill_clicked(self):
        rbNomenclatureUnitRatioId = None
        resultCheckDosage = True
        resultCheckDefaultUnit = True
        self.dictDiscrepancies = {}
        self.orderedListDiscrepancies = []

        self.eslkpUUID = self.cmbESLKPName.value()
        if self.eslkpUUID:
            db = QtGui.qApp.db
            tableESKLP_Klp = db.table('esklp.Klp')
            cols = [tableESKLP_Klp['mass_volume_num'],
                    tableESKLP_Klp['mass_volume_name'],
                    tableESKLP_Klp['trade_name'],
                    tableESKLP_Klp['lf_norm_name'],
                    tableESKLP_Klp['dosage_norm_name'],
                    tableESKLP_Klp['pack1_name'],
                    tableESKLP_Klp['pack1_num'],
                    tableESKLP_Klp['pack2_name'],
                    tableESKLP_Klp['pack2_num'],
                    tableESKLP_Klp['mnn_norm_name'],
                    tableESKLP_Klp['date_start'],
                    tableESKLP_Klp['date_end'],
                    tableESKLP_Klp['completeness'],
                    tableESKLP_Klp['is_narcotic'],
                    tableESKLP_Klp['smnn_id'],
                    tableESKLP_Klp['manufacturer_id'],
                    tableESKLP_Klp['code'],
                    ]
            cond = [tableESKLP_Klp['UUID'].eq(self.eslkpUUID)]
            record = db.getRecordEx(tableESKLP_Klp, cols, cond)
            if record:
                mass_volume_num = forceDouble(record.value('mass_volume_num'))
                mass_volume_name = forceStringEx(record.value('mass_volume_name'))
                trade_name = forceStringEx(record.value('trade_name'))
                lf_norm_name = forceStringEx(record.value('lf_norm_name'))
                dosage_norm_name = forceStringEx(record.value('dosage_norm_name'))
                pack1_name = forceStringEx(record.value('pack1_name'))
                pack1_num = forceDouble(record.value('pack1_num'))
                pack2_name = forceStringEx(record.value('pack2_name'))
                pack2_num = forceInt(record.value('pack2_num'))
                mnn_norm_name = forceStringEx(record.value('mnn_norm_name'))
                completeness = forceStringEx(record.value('completeness'))
                inDate = forceDate(record.value('date_start'))
                exDate = forceDate(record.value('date_end'))
                isNarcotic = forceInt(record.value('is_narcotic'))
                smnnId = forceRef(record.value('smnn_id'))
                manufacturerId = forceRef(record.value('manufacturer_id'))
                code = forceStringEx(record.value('code'))
                if mass_volume_name and mass_volume_num:
                    newNameTN = u'{0}, {1} {2}, {3} {4} {5}, {6} №{7}'.format(trade_name, lf_norm_name.lower(),
                                                                              dosage_norm_name, pack1_name.lower(),
                                                                              str(int(mass_volume_num) if int(mass_volume_num) else mass_volume_num),
                                                                              mass_volume_name, pack2_name.lower(),
                                                                              str(pack2_num))
                else:
                    newNameTN = u'{0}, {1} {2}, {3} №{4}'.format(trade_name, lf_norm_name.lower(), dosage_norm_name,
                                                                 pack2_name.lower(), str(int(pack1_num * pack2_num)))
                if not self.edtName.text():
                    self.edtName.setText(newNameTN)
                else:
                    if self.edtName.text() != newNameTN:
                        self.addDictDiscrepancies(self.edtName.objectName(),
                                                  [self.lblName.text(), self.edtName.text(), newNameTN, True])
                if not self.edtInternationalNonproprietaryName.text():
                    self.edtInternationalNonproprietaryName.setText(mnn_norm_name)
                else:
                    if self.edtInternationalNonproprietaryName.text() != mnn_norm_name:
                        self.addDictDiscrepancies(self.edtInternationalNonproprietaryName.objectName(),
                                                  [self.lblInternationalNonproprietaryName.text(),
                                                   self.edtInternationalNonproprietaryName.text(), mnn_norm_name, True])
                tableSmnn_Ath = db.table('esklp.Smnn_Ath')
                cols = [
                    tableSmnn_Ath['ath_code'],
                ]
                cond = [tableSmnn_Ath['master_id'].eq(smnnId)]
                recordAth = db.getRecordList(tableSmnn_Ath, cols, cond)
                newTextAth = u'; '.join([forceStringEx(item.value('ath_code')) for item in recordAth])
                if not self.edtATC.text():
                    self.edtATC.setText(newTextAth)
                else:
                    if self.edtATC.text() != newTextAth:
                        self.addDictDiscrepancies(self.edtATC.objectName(),
                                                  [self.lblATC.text(), self.edtATC.text(), newTextAth, True])
                tableManufacturer = db.table('esklp.Manufacturer')
                cols = [
                    tableManufacturer['name'],
                    tableManufacturer['country_name'],
                ]
                cond = [tableManufacturer['id'].eq(manufacturerId)]
                recordProducer = db.getRecordEx(tableManufacturer, cols, cond)
                newTextProducer = u', '.join([forceStringEx(recordProducer.value('name')),
                                              forceStringEx(recordProducer.value('country_name'))])
                if not self.edtProducer.text():
                    self.edtProducer.setText(newTextProducer)
                else:
                    if self.edtProducer.text() != newTextProducer:
                        self.addDictDiscrepancies(self.edtProducer.objectName(),
                                                  [self.lblProducer.text(), self.edtProducer.text(), newTextProducer, True])
                if self.itemId():
                    rbNomenclatureUnitRatioId = forceRef(QtGui.qApp.db.translate('rbNomenclature_UnitRatio', 'master_id', self.itemId(), 'id'))
                    actionPropertyRbNomenclatureId = forceStringEx(QtGui.qApp.db.translate('ActionProperty_rbNomenclature', 'value', self.itemId(), 'id'))
                    actionExecutionPlanItemNomenclatureId = forceRef(QtGui.qApp.db.translate('ActionExecutionPlan_Item_Nomenclature', 'nomenclature_id', self.itemId(), 'id'))
                    actionTypeGroupPlanItemNomenclatureId = forceRef(QtGui.qApp.db.translate('ActionTypeGroup_Plan_Item_Nomenclature', 'nomenclature_id', self.itemId(), 'id'))
                    stockMotionItemId = forceRef(QtGui.qApp.db.translate('StockMotion_Item', 'nomenclature_id', self.itemId(), 'id'))
                    stockPurchaseContractItemId = forceRef(QtGui.qApp.db.translate('StockPurchaseContract_Item', 'nomenclature_id', self.itemId(), 'id'))
                    stockRequisitionItemId = forceRef(QtGui.qApp.db.translate('StockRequisition_Item', 'nomenclature_id', self.itemId(), 'id'))
                    actionTypeNomenclatureId = forceRef(QtGui.qApp.db.translate('ActionType_Nomenclature', 'nomenclature_id', self.itemId(), 'id'))
                    resultCheckDosage = any([actionPropertyRbNomenclatureId, actionExecutionPlanItemNomenclatureId, actionTypeGroupPlanItemNomenclatureId])
                    resultCheckDefaultUnit = any([stockMotionItemId, stockPurchaseContractItemId, stockRequisitionItemId, actionTypeNomenclatureId])
                if mass_volume_num:
                    dosageValue = mass_volume_num
                    spnPackSize = pack2_num
                else:
                    dosageValue = 1
                    spnPackSize = pack1_num * pack2_num
                if not self.edtDosageValue.text():
                    self.edtDosageValue.setText(str(dosageValue))
                else:
                    if self.edtDosageValue.text() != str(dosageValue):
                        check = True if not resultCheckDosage else 'Disabled'
                        self.addDictDiscrepancies(self.edtDosageValue.objectName(),
                                                  [self.lbDosageValue.text(), self.edtDosageValue.text(), str(dosageValue), check])
                if mass_volume_name:
                    unitName = mass_volume_name
                    defaultClientUnit = pack1_name
                else:
                    unitName = lf_norm_name
                    defaultClientUnit = lf_norm_name
                unitId = findByIdentification('rbUnit', self.unitUrn, unitName, False)
                if unitId:
                    if self.itemId():
                        if self.cmbUnit.value() != unitId:
                            check = True if not resultCheckDosage else 'Disabled'
                            setRbUnitName = forceStringEx(db.getRecordEx('rbUnit', 'name', 'id=%s' % unitId).value('name'))
                            setUnitName = u'{0} [{1}]'.format(unitName, setRbUnitName)
                            self.addDictDiscrepancies(self.cmbUnit.objectName(),
                                                      [self.lbDosageUnit.text(), self.cmbUnit.currentText(), (unitId, setUnitName), check])
                    else:
                        if not self.cmbUnit.value():
                            self.cmbUnit.setValue(unitId)
                tableRbLfForm = db.table('rbLfForm')
                cols = [
                    tableRbLfForm['id'],
                    tableRbLfForm['name'],
                ]
                cond = [
                    tableRbLfForm['isESKLP'].eq(1),
                    tableRbLfForm['name'].eq(lf_norm_name),
                    tableRbLfForm['dosage'].eq(dosage_norm_name),
                ]
                recordRbLfForm = db.getRecordEx(tableRbLfForm, cols, cond)
                recordRbLfFormId = forceInt(recordRbLfForm.value('id'))
                recordRbLfFormName = forceStringEx(recordRbLfForm.value('name'))
                if not self.cmbLfForm.value():
                    self.cmbLfForm.setValue(recordRbLfFormId)
                else:
                    if self.cmbLfForm.value() != recordRbLfFormId:
                        self.addDictDiscrepancies(self.cmbLfForm.objectName(),
                                                  [self.lbLfForm.text(), self.cmbLfForm.currentName(), (recordRbLfFormId, recordRbLfFormName), True])
                if self.cmbNarcoticSubstance.currentIndex() != isNarcotic:
                    self.addDictDiscrepancies(self.cmbNarcoticSubstance.objectName(),
                                              [self.lblNarcoticSubstance.text(), self.cmbNarcoticSubstance.currentIndex(), isNarcotic, True])
                if self.edtInDate.date() != inDate and inDate.isValid():
                    self.edtInDate.setDate(inDate)
                if self.edtExDate.date() != exDate and exDate.isValid():
                    self.edtExDate.setDate(exDate)
                if not self.spnPackSize.value():
                    self.spnPackSize.setValue(spnPackSize)
                else:
                    if self.spnPackSize.value() != spnPackSize:
                        self.addDictDiscrepancies(self.spnPackSize.objectName(),
                                                  [self.lblPackSize.text(), self.spnPackSize.value(), spnPackSize, True])
                if not self.edtCompleteness.text():
                    self.edtCompleteness.setText(completeness)
                else:
                    if self.edtCompleteness.text() != completeness:
                        self.addDictDiscrepancies(self.edtCompleteness.objectName(),
                                                  [self.lblCompleteness.text(), self.edtCompleteness.text(), completeness, True])
                defaultStockUnitId = findByIdentification('rbUnit', self.unitUrn, pack2_name, False)
                if defaultStockUnitId:
                    if self.itemId():
                        if self.cmbDefaultStockUnit.value() != defaultStockUnitId:
                            check = True if not resultCheckDefaultUnit else 'Disabled'
                            setRbUnitStock = forceStringEx(db.getRecordEx('rbUnit', 'name', 'id=%s' % defaultStockUnitId).value('name'))
                            setTextStock = u'{0} [{1}]'.format(pack2_name, setRbUnitStock)
                            self.addDictDiscrepancies(self.cmbDefaultStockUnit.objectName(),
                                                      [self.lblDefaultStockUnit.text(), self.cmbDefaultStockUnit.currentText(), (defaultStockUnitId, setTextStock), check])
                    else:
                        if not self.cmbDefaultStockUnit.value():
                            self.cmbDefaultStockUnit.setValue(defaultStockUnitId)
                defaultClientUnitId = findByIdentification('rbUnit', self.unitUrn, defaultClientUnit, False)
                if defaultClientUnitId:
                    if self.itemId():
                        if self.cmbDefaultClientUnit.value() != defaultClientUnitId:
                            check = True if not resultCheckDefaultUnit else 'Disabled'
                            setRbUnitClient = forceStringEx(db.getRecordEx('rbUnit', 'name', 'id=%s' % defaultClientUnitId).value('name'))
                            setTextClient = u'{0} [{1}]'.format(defaultClientUnit, setRbUnitClient)
                            self.addDictDiscrepancies(self.cmbDefaultClientUnit.objectName(),
                                                      [self.lblDefaultClientUnit.text(), self.cmbDefaultClientUnit.currentText(), (defaultClientUnitId, setTextClient), check])
                    else:
                        if not self.cmbDefaultClientUnit.value():
                            self.cmbDefaultClientUnit.setValue(defaultClientUnitId)
                if not rbNomenclatureUnitRatioId:
                    self.updateUnitRatio(defaultStockUnitId, defaultClientUnitId, spnPackSize)
                itemsIdentification = [forceStringEx(item.value('value')) for item in self.modelIdentification.items()]
                tableMdlpPubProdInfo = db.table('esklp.MdlpPublicProductInformation')
                recordMdlpPubProdInfo = db.getRecordList(tableMdlpPubProdInfo,
                                                         tableMdlpPubProdInfo['gtin'],
                                                         tableMdlpPubProdInfo['code'].eq(code))
                for itemGTIN in recordMdlpPubProdInfo:
                    gtin = forceStringEx(itemGTIN.value('gtin'))
                    if gtin not in itemsIdentification:
                        self.modelIdentification.addIdentification(self.systemId, gtin)
                if self.itemId() and self.dictDiscrepancies:
                    self.showDiscrepanciesTable()

    def addDictDiscrepancies(self, key, value):
        if key not in self.dictDiscrepancies.keys():
            self.dictDiscrepancies[key] = value
            self.orderedListDiscrepancies.append(key)

    def updateUnitRatio(self, sourceUnitId, targetUnitId, ratio):
        self.modelUnitRatio.clearItems()
        db = QtGui.qApp.db
        tableRbNU = db.table('rbNomenclature_UnitRatio')
        newItem = tableRbNU.newRecord()
        newItem.setValue('sourceUnit_id', toVariant(sourceUnitId))
        newItem.setValue('targetUnit_id', toVariant(targetUnitId))
        newItem.setValue('ratio', toVariant(ratio))
        self.modelUnitRatio.items().append(newItem)


class CCompositionModel(CInDocTableModel):
    class CCompositionInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.caches = {}

        def toString(self, val, record):
            activeSubstanceId = forceRef(val)
            name = u''
            if activeSubstanceId:
                record = self.caches.get(activeSubstanceId, None)
                if not record:
                    db = QtGui.qApp.db
                    table = db.table('rbNomenclatureActiveSubstance')
                    record = db.getRecordEx(table, [table['name'], table['mnnLatin']], [table['id'].eq(activeSubstanceId)])
                if record:
                    name = forceStringEx(record.value('name'))
                    if not name:
                        name = forceStringEx(record.value('mnnLatin'))
                self.caches[activeSubstanceId] = record
            return toVariant(name)

        def createEditor(self, parent):
            editor = CActiveSubstanceComboBox(parent)
            return editor

        def setEditorData(self, editor, value, record):
            editor.setValue(forceRef(value))

        def getEditorData(self, editor):
            return toVariant(editor.value())

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbNomenclature_Composition', 'id', 'master_id', parent)
        self.addCol(
            CCompositionModel.CCompositionInDocTableCol(u'Действующее вещество', 'activeSubstance_id', 20)).setSortable(
            True)
        self.addCol(
            CEnumInDocTableCol(u'Тип', 'type', 4, [u'активное', u'активное вспомогательное', u'вспомогательное']))


class CBaseFeatureInDocTableCol(CInDocTableCol):
    # В базе данных хранится номер,
    # а на экране рисуется комбо-бокс с соотв. значениями
    def __init__(self, title, fieldName, width, model, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.model = weakref.ref(model)

    def toString(self, val, record):
        return val

    @abstract
    def getValues(self, record):
        pass

    def createEditor(self, parent):
        editor = QtGui.QComboBox(parent)
        editor.setEditable(True)
        return editor

    def setEditorData(self, editor, value, record):
        values = self.getValues(record)
        editor.addItems(values)
        #        for item in values:
        #            editor.addItem(item)
        index = editor.findText(forceString(value), Qt.MatchFixedString)
        if index >= 0:
            editor.setCurrentIndex(index)
        else:
            editor.insertItem(0, forceString(value))
            editor.setCurrentIndex(0)
        editor.setEditText(forceString(value))

    def getEditorData(self, editor):
        return toVariant(editor.currentText())


class CFeatureNameInDocTableCol(CBaseFeatureInDocTableCol):
    def getValues(self, record):
        return self.model().getFeatureNames()


class CFeatureValueInDocTableCol(CBaseFeatureInDocTableCol):
    def getValues(self, record):
        return self.model().getValuesForName(forceString(record.value('name')))


class CFeaturesModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbNomenclature_Feature', 'id', 'master_id', parent)
        self.addCol(CFeatureNameInDocTableCol(u'Наименование', 'name', 20, self)).setSortable(True)
        self.addCol(CFeatureValueInDocTableCol(u'Значение', 'value', 20, self)).setSortable(True)
        self.typeId = None
        self.kindId = None
        self.classId = None
        self.likelyFeatures = {}

    def updateLikelyFeatures(self, classId, kindId, typeId):
        if (self.typeId != typeId
                or self.kindId != kindId
                or self.classId != classId):
            self.likelyFeatures = getFeaturesAndValues(classId, kindId, typeId)
            self.typeId = typeId
            self.kindId = kindId
            self.classId = classId

    def fillBySiblings(self, classId, kindId, typeId):
        self.updateLikelyFeatures(classId, kindId, typeId)
        if self.likelyFeatures:
            actualFeatures = {}
            for item in self.items():
                name = forceString(item.value('name'))
                value = forceString(item.value('value'))
                if value:
                    actualFeatures.setdefault(name, set()).add(value)
            for name in actualFeatures:
                actualFeatures.setdefault(name, set())

            featureNames = actualFeatures.keys()
            featureNames.sort()

            items = []
            for name in featureNames:
                values = list(actualFeatures[name])
                values.sort()
                for value in values or ('',):
                    item = self.getEmptyRecord()
                    item.setValue('name', name)
                    item.setValue('value', value)
                    items.append(item)
            self.setItems(items)

    def getFeatureNames(self):
        result = self.likelyFeatures.keys()
        result.sort()
        return result

    def getValuesForName(self, name):
        return self.likelyFeatures.get(name) or []


class CIngredientsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbNomenclature_Ingredient', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Ингредиент', 'ingredient_id', 20, 'rbIngredient')).setSortable(True)


class CUnitRatioModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbNomenclature_UnitRatio', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Исходная Ед.учета', 'sourceUnit_id', 20, 'rbUnit')).setSortable(True)
        self.addCol(CRBInDocTableCol(u'Целевая Ед.учета', 'targetUnit_id', 20, 'rbUnit')).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'Коэффициент', 'ratio', 20, precision=1)).setSortable(True)
        self.addHiddenCol('auto_calculated')
        self.setFilter('auto_calculated = 0')
        self._autoCalculated = {}

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
                record.setValue('auto_calculated', toVariant(0))
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

            nodesIds = self._calculateNodes()
            idList.extend(nodesIds)

            filter = [table[masterIdFieldName].eq(masterId),
                      'NOT (' + table[idFieldName].inlist(idList) + ')']
            if self._filter:
                filter.append(self._filter)
            db.deleteRecord(table, filter)

    def _calculateNodes(self):
        return []

    def loadItems(self, masterId):
        CInDocTableModel.loadItems(self, masterId)
        # cols = []
        # for col in self._cols:
        #     if not col.external():
        #         cols.append(col.fieldName())
        # cols.append(self._idFieldName)
        # cols.append(self._masterIdFieldName)
        # if self._idxFieldName:
        #     cols.append(self._idxFieldName)
        # for col in self._hiddenCols:
        #     cols.append(col)
        # table = self._table
        # filter = [table[self._masterIdFieldName].eq(masterId),
        #           table['auto_calculated'].eq(1)]
        # if table.hasField('deleted'):
        #     filter.append(table['deleted'].eq(0))
        # if self._idxFieldName:
        #     order = [self._idxFieldName, self._idFieldName]
        # else:
        #     order = [self._idFieldName]
        # auto_calculated_items = db.getRecordList(table, cols, filter, order)
        #


class CAnalogsModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addExtCol(CNomenclatureInDocTableCol(u'ЛСиИМН', 'id', 50, showFields=CRBComboBox.showName),
                       QVariant.Int
                       )
        self.masterId = None  # в rbNomenclature
        self.analogId = None  # в rbNomenclature_analog

    def setDefaultClassId(self, classId):
        self._cols[0].setDefaultClassId(classId)

    def setDefaultKindId(self, kindId):
        self._cols[0].setDefaultClassId(kindId)

    def setDefaultTypeId(self, typeId):
        self._cols[0].setDefaultClassId(typeId)

    def getEmptyRecord(self):
        record = CRecordListModel.getEmptyRecord(self)
        record.append(QtSql.QSqlField('id', QVariant.Int))
        return record

    def getAnalogies(self, nomenclatureIdList, analogId):
        db = QtGui.qApp.db
        table = db.table('rbNomenclature')
        items = db.getRecordList(table,
                                 'id',
                                 [table['analog_id'].eq(analogId), table['id'].notInlist(nomenclatureIdList)],
                                 'name'
                                 )
        return items

    def loadItems(self, masterId, analogId):
        self.masterId = masterId
        self.analogId = analogId
        if analogId:
            items = self.getAnalogies([masterId], analogId)
            self.setItems(items)

    def getIdList(self):
        idlist = []
        for item in self.items():
            id = forceRef(item.value('id'))
            if id:
                idlist.append(id)
        if self.masterId:
            idlist.append(self.masterId)
        return idlist

    def newAnalogId(self):
        db = QtGui.qApp.db
        table = db.table('rbNomenclature_Analog')
        return db.insertRecord(table, table.newRecord())

    def correctAlanogId(self):
        idlist = self.getIdList()
        if idlist:
            idlist.sort()
            db = QtGui.qApp.db
            table = db.table('rbNomenclature')
            usedAnalogIdList = db.getIdList(table,
                                            idCol='DISTINCT analog_id',
                                            where=[table['id'].inlist(idlist), table['analog_id'].isNotNull()])
            if len(usedAnalogIdList) == 1:
                memberIdList = db.getIdList(table,
                                            'id',
                                            [table['analog_id'].eq(usedAnalogIdList[0]), table['id'].ne(self.masterId)],
                                            'id'
                                            )
                if memberIdList == idlist:
                    self.analogId = usedAnalogIdList[0]
                else:
                    self.analogId = self.newAnalogId()
            else:
                self.analogId = self.newAnalogId()
        else:
            self.analogId = None
        return self.analogId

    def saveItems(self, masterId):
        if self.analogId:
            self.masterId = masterId
            idlist = self.getIdList()
            db = QtGui.qApp.db
            table = db.table('rbNomenclature')
            db.updateRecords(table, table['analog_id'].eq(self.analogId), table['id'].inlist(idlist))

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            id = forceRef(value)
            if not id:  # не добавляем пустую строку
                return False
            idlist = self.getIdList()
            if id in idlist:  # не добавляем повторы
                return False
            result = CRecordListModel.setData(self, index, value, role)
            if not result:
                return False
            # добавляем аналоги только что указанного
            idlist.append(id)
            db = QtGui.qApp.db
            table = db.table('rbNomenclature')
            newAnalogId = db.translate(table, 'id', value, 'analog_id')
            if newAnalogId:
                row = index.row() + 1
                for record in self.getAnalogies(idlist, newAnalogId):
                    self.insertRecord(row, record)
                    row += 1
            return True
        else:
            return CRecordListModel.setData(self, index, value, role)


class CUsingTypesModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbNomenclature_UsingType', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Способ применения', 'usingType_id', 20, 'rbNomenclatureUsingType')).setSortable(
            True)
