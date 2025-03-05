# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QAbstractTableModel, QVariant, pyqtSignature, SIGNAL

from library.InDocTable  import CInDocTableModel, CRBInDocTableCol, CBoolInDocTableCol, CIntInDocTableCol, CFloatInDocTableCol
from library.Utils       import forceInt, forceBool, forceRef, forceString, forceDate, forceDouble, forceStringEx, toVariant
from library.DialogBase  import CDialogBase
from library.crbcombobox import CRBComboBox
from Stock.NomenclatureComboBox import CNomenclatureInDocTableCol
from Stock.ClientInvoiceEditDialog import CClientInvoiceEditDialog, CClientRefundInvoiceEditDialog
from Stock.Utils import getExistsNomenclatureAmount, getStockMotionItemQntEx, getNomenclatureUnitRatio, getNomenclatureSimpleUnitRatio

from Events.Ui_NomenclatureAddedActionsSelectDialog import Ui_NomenclatureAddedActionsSelectDialog


class CNomenclatureAddedActionsSelectDialog(CDialogBase, Ui_NomenclatureAddedActionsSelectDialog):
    def __init__(self, parent, actionExpenseItems):
        #CDialogBase.__init__(self, parent)
        super(self.__class__, self).__init__(parent)
        self.addModels('ActionsExpense', CActionsExpenseModel(self, actionExpenseItems))
        self.addModels('NomenclatureExpense', CNomenclatureExpenseModel(self))
        self.addObject('actAPNomenclatureExpense',  QtGui.QAction(u'Редактировать спмсание ЛСиИМН на пациента', self))
        self.setupUi(self)
        self.setupActionPopupMenu()
        self.setWindowTitleEx(u'Выберите ЛСиИМН для нормативного списания')
        self.setModels(self.tblActionsExpense, self.modelActionsExpense, self.selectionModelActionsExpense)
        self.setModels(self.tblNomenclatureExpense, self.modelNomenclatureExpense, self.selectionModelNomenclatureExpense)
        self.actionExpenseItems = actionExpenseItems
        self.firstEntry = True
        self._mapNomenclatureIdToUnitId = {}
        self.isControlExecWriteOffNE = True
        self.modelNomenclatureExpense.setEnableAppendLine(False)
        self.modelActionsExpense.loadItems()
        self.loadNomenclatureToAction()
        self.firstEntry = False
        if self.modelActionsExpense.rowCount() > 0:
            self.tblActionsExpense.setCurrentRow(0)


    def setupActionPopupMenu(self):
        self.mnuActionsExpense = self.tblActionsExpense.popupMenu()
        if self.mnuActionsExpense:
            self.tblActionsExpense.popupMenu().addSeparator()
            self.tblActionsExpense.addPopupAction(self.actAPNomenclatureExpense)
            self.tblActionsExpense.connect(self.mnuActionsExpense, SIGNAL('aboutToShow()'), self.on_mnuActionsExpense_aboutToShow)


    @pyqtSignature('')
    def on_actAPNomenclatureExpense_triggered(self):
        self.on_btnAPNomenclatureExpense_clicked()


    def getActionsExpenseEnabled(self):
        enabled = False
        currentIndex = self.tblActionsExpense.currentIndex()
        curentIndexIsValid = currentIndex.isValid()
        if curentIndexIsValid:
            model = self.tblActionsExpense.model()
            if 0 <= currentIndex.row() < len(model.items()):
                for item in self.modelNomenclatureExpense._items:
                    if forceBool(item.value('include')):
                        return True
        return enabled


    @pyqtSignature('')
    def on_mnuActionsExpense_aboutToShow(self):
        self.tblActionsExpense.on_popupMenu_aboutToShow()
        self.actAPNomenclatureExpense.setEnabled(self.getActionsExpenseEnabled())


    def loadNomenclatureToAction(self):
        for row, (record, action) in enumerate(self.modelActionsExpense._items):
            masterId = forceRef(record.value('actionType_id'))
            self.modelNomenclatureExpense.loadItems(masterId, row)
        self.on_selectionModelActionsExpense_currentRowChanged(self.modelActionsExpense.index(0, 0), self.modelActionsExpense.index(0, 0))


    def getNomenclatureToActions(self):
        return self.modelNomenclatureExpense.getNomenclatureToActions()


    def getActionExpenseItems(self):
        return self.modelActionsExpense._items


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionsExpense_currentRowChanged(self, current, previous):
        if previous.isValid() and not self.firstEntry:
            self.modelNomenclatureExpense.setNomenclatureToAction(self.modelActionsExpense.actionTypeId(previous.row()), previous.row())
        self.modelNomenclatureExpense.loadItems(self.modelActionsExpense.actionTypeId(self.tblActionsExpense.currentRow()), self.tblActionsExpense.currentRow())
        self.btnAPNomenclatureExpense.setEnabled(self.getActionsExpenseEnabled())


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.on_buttonBox_ok()
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            QtGui.QDialog.reject(self)
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBox_reset()


    def exec_(self):
        result = CDialogBase.exec_(self)
        if not self.isControlExecWriteOffNE:
            result = QtGui.QDialog.Rejected
        self.setResult(result)
        return result


    def getIncludeAvailable(self, aTNomenclatureItems, currentGroup):
        for item in aTNomenclatureItems:
            if currentGroup == forceInt(item.value('selectionGroup')) and forceBool(item.value('available')) and forceBool(item.value('include')):
                return True
        return False


    def getActionChanged(self, row, record, action):
        self.modelNomenclatureExpense.setNomenclatureToAction(self.modelActionsExpense.actionTypeId(self.tblActionsExpense.currentRow()), self.tblActionsExpense.currentRow())
        mapNomenclatureToAction = self.getNomenclatureToActions()
        if action and action.nomenclatureExpense and (not action.nomenclatureExpense._isApplyBatch or self.modelNomenclatureExpense.isUpdateInclude):
            aTNomenclatureList = []
            masterId = forceRef(record.value('actionType_id'))
            aTNomenclatureItems = mapNomenclatureToAction.get((masterId, row), [])
            for item in aTNomenclatureItems:
                include = forceBool(item.value('include'))
                if include and (not forceBool(item.value('selectionGroup')) or forceBool(item.value('available')) or self.getIncludeAvailable(aTNomenclatureItems, forceInt(item.value('selectionGroup')))):
                    aTNomenclatureList.append(item)
            action.nomenclatureExpense.updateNomenclatureToAction(aTNomenclatureList)
            action.nomenclatureExpense._isApplyBatch = True
#            stockMotionItems = action.nomenclatureExpense.stockMotionItems()
#            for stockMotionItem in stockMotionItems:
#                action.nomenclatureExpense._applyBatchFinanceIdShelfTime(stockMotionItem)
        self.modelNomenclatureExpense.isUpdateInclude = False
        return action


    def on_buttonBox_ok(self):
        self.isControlExecWriteOffNE = True
        self.modelNomenclatureExpense.setNomenclatureToAction(self.modelActionsExpense.actionTypeId(self.tblActionsExpense.currentRow()), self.tblActionsExpense.currentRow())
        mapNomenclatureToAction = self.getNomenclatureToActions()
        for row, (record, action) in enumerate(self.modelActionsExpense._items):
            if action.nomenclatureExpense and (not action.nomenclatureExpense._isApplyBatch or self.modelNomenclatureExpense.isUpdateInclude):
                aTNomenclatureList = []
                masterId = forceRef(record.value('actionType_id'))
                aTNomenclatureItems = mapNomenclatureToAction.get((masterId, row), [])
                for item in aTNomenclatureItems:
                    include = forceBool(item.value('include'))
                    if include and (not forceBool(item.value('selectionGroup')) or forceBool(item.value('available')) or self.getIncludeAvailable(aTNomenclatureItems, forceInt(item.value('selectionGroup')))):
                        if self.modelNomenclatureExpense._extColsPresent:
                            item = self.modelNomenclatureExpense.removeExtCols(item)
                        aTNomenclatureList.append(item)
                if not action.nomenclatureExpensePreliminarySave:
                    action.nomenclatureExpense.updateNomenclatureToAction(aTNomenclatureList)
                    action.nomenclatureExpense._isApplyBatch = True
#                    stockMotionItems = action.nomenclatureExpense.stockMotionItems()
#                    for stockMotionItem in stockMotionItems:
#                        action.nomenclatureExpense._applyBatchFinanceIdShelfTime(stockMotionItem)
            self.modelNomenclatureExpense.isUpdateInclude = False
        
        isControlExecWriteOffNomenclatureExpense = QtGui.qApp.controlExecutionWriteOffNomenclatureExpense()
        if isControlExecWriteOffNomenclatureExpense:
            mapNomenclatureToAction = self.getNomenclatureToActions()
            db = QtGui.qApp.db
            message = u''
            nomenclatureLine = []
            resQntDict = {}
            aTNomenclatureList = []
            tableNomenclature = db.table('rbNomenclature')
            for row, (record, action) in enumerate(self.modelActionsExpense._items):
                if action.nomenclatureExpense:
                    supplierId = forceRef(action.getRecord().value('orgStructure_id'))
                    if supplierId:
                        action.nomenclatureExpense.setSupplierId(supplierId)
                    masterId = forceRef(record.value('actionType_id'))
                    aTNomenclatureItems = mapNomenclatureToAction.get((masterId, row), [])
                    for item in aTNomenclatureItems:
                        include = forceBool(item.value('include'))
                        if include and (not forceBool(item.value('selectionGroup')) or forceBool(item.value('available')) or self.getIncludeAvailable(aTNomenclatureItems, forceInt(item.value('selectionGroup')))):
                            aTNomenclatureList.append(item)
                    nomenclatureIdDict = {}
                    for aTNomenclature in aTNomenclatureList:
                        nomenclatureIdAT = forceRef(aTNomenclature.value('nomenclature_id'))
                        nomenclatureIdDict[nomenclatureIdAT] = forceDouble(aTNomenclature.value('amount'))
                    stockMotionItems = action.nomenclatureExpense.stockMotionItems()
                    for stockMotionItem in stockMotionItems:
                        price = forceDouble(stockMotionItem.value('price'))
                        oldPrice = price
                        nomenclatureId = forceRef(stockMotionItem.value('nomenclature_id'))
                        if nomenclatureId and nomenclatureId not in nomenclatureLine:
                            qnt = forceDouble(stockMotionItem.value('qnt'))
                            resQnt, planQnt, simpleRatio = resQntDict.get(nomenclatureId, (None, None, 2))
                            unitId = forceRef(stockMotionItem.value('unit_id'))
                            stockUnitId = self.getDefaultStockUnitId(nomenclatureId)
                            ratio = self.getRatio(nomenclatureId, stockUnitId, unitId)
                            if ratio is not None:
                                price = price*ratio
                                qnt = qnt / ratio
                            qnt = round(qnt, QtGui.qApp.numberDecimalPlacesQnt())
                            if planQnt is None:
                                dosage = nomenclatureIdDict.get(nomenclatureId, 0)
                                planQnt = action.nomenclatureExpense.getNomenclatureDosageToQntValue(nomenclatureId, dosage)
                                if ratio is not None:
                                    planQnt = planQnt / ratio
                                planQnt = round(planQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            financeId = forceRef(stockMotionItem.value('finance_id'))
                            batch = forceString(stockMotionItem.value('batch'))
                            shelfTime = forceDate(stockMotionItem.value('shelfTime'))
                            shelfTime = shelfTime.toPyDate() if bool(shelfTime) else None
                            medicalAidKindId = forceRef(stockMotionItem.value('medicalAidKind_id'))
                            otherHaving=[u'(shelfTime>=curDate()) OR shelfTime is NULL']
                            existsQnt = getExistsNomenclatureAmount(nomenclatureId, financeId, batch, orgStructureId=supplierId, unitId=stockUnitId, medicalAidKindId = medicalAidKindId, shelfTime=shelfTime, otherHaving=otherHaving, exact=True, price=price, isStockUtilization=False, precision=QtGui.qApp.numberDecimalPlacesQnt())
                            masterId = forceRef(stockMotionItem.value('master_id'))
                            prevQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=masterId, batch=batch, financeId=financeId, medicalAidKindId=medicalAidKindId, price=None, oldPrice=oldPrice, oldUnitId=stockUnitId), QtGui.qApp.numberDecimalPlacesQnt()) if masterId else 0
                            reservationQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=None, batch=batch, financeId=financeId, clientId=action.nomenclatureExpense._clientId, medicalAidKindId=medicalAidKindId, price=None, oldPrice=price, oldUnitId=stockUnitId), QtGui.qApp.numberDecimalPlacesQnt())
                            if existsQnt < 0:
                                existsQnt = 0
                            if prevQnt < 0:
                                prevQnt = 0
                            if reservationQnt < 0:
                                reservationQnt = 0
                            if resQnt is None:
                                resQnt = (existsQnt + reservationQnt + prevQnt) - qnt
                            else:
                                resQnt += (existsQnt + reservationQnt + prevQnt) - qnt
                            resQnt = round(resQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            planQnt = planQnt - qnt
                            planQnt = round(planQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            resQntDict[nomenclatureId] = (resQnt, planQnt, len(forceStringEx(self.getSimpleRatio(nomenclatureId, stockUnitId, unitId))))
                    for nomenclatureIdKey, (resQntValue, planQntValue, simpleQntRatio) in resQntDict.items():
                        if resQntValue < 0 or resQntValue is None or (round(planQntValue, simpleQntRatio) != 0 and planQntValue is not None):
                            nomenclatureLine.append(nomenclatureIdKey)
                    if nomenclatureLine:
                        records = db.getRecordList(tableNomenclature, [tableNomenclature['name']], [tableNomenclature['id'].inlist(nomenclatureLine)], order = tableNomenclature['name'].name())
                        nomenclatureName = u','.join(forceString(recordNomenclature.value('name')) for recordNomenclature in records)
                        message += u'''Действие типа %s.\nОтсутствуют ЛСиИМН: %s!\n'''%(action._actionType.name, nomenclatureName)
                    if message:
                        if isControlExecWriteOffNomenclatureExpense == 1:
                            button = QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel
                            message2 = u'Списываемого ЛСиИМН %s недостаточно на остатке подразделения. Выполнить списание?'%(nomenclatureName)
                        else:
                            button = QtGui.QMessageBox.Cancel
                            message2 = u'Списываемого ЛСиИМН %s недостаточно на остатке подразделения. Выполнение назначения невозможно!\n'%(nomenclatureName)
                        res = QtGui.QMessageBox.warning(None,
                                                  u'Внимание!',
                                                  message2,
                                                  button,
                                                  QtGui.QMessageBox.Cancel)
                        if res == QtGui.QMessageBox.Cancel:
                            self.isControlExecWriteOffNE = False
                            action.getRecord().setValue('status', toVariant(action.getType().defaultStatus))
        if self.isControlExecWriteOffNE:
            QtGui.QDialog.accept(self)
        else:
            QtGui.QDialog.reject(self)


    def _getNomenclatureDefaultUnits(self, nomenclatureId):
        if not nomenclatureId:
            return {}
        result = self._mapNomenclatureIdToUnitId.get(nomenclatureId)
        if result is None:
            record = QtGui.qApp.db.getRecord('rbNomenclature',
                                             ('defaultStockUnit_id', 'defaultClientUnit_id'),
                                             nomenclatureId
                                            )
            if record:
                defaultStockUnitId = forceRef(record.value('defaultStockUnit_id'))
                defaultClientUnitId = forceRef(record.value('defaultClientUnit_id'))
            else:
                defaultStockUnitId = defaultClientUnitId = None
            result = {
                       'defaultStockUnitId' : defaultStockUnitId,
                       'defaultClientUnitId': defaultClientUnitId
                     }
            self._mapNomenclatureIdToUnitId[nomenclatureId] = result
        return result


    def getDefaultStockUnitId(self, nomenclatureId):
        return self._getNomenclatureDefaultUnits(nomenclatureId).get('defaultStockUnitId')


    def getRatio(self, nomenclatureId, oldUnitId, newUnitId):
        if oldUnitId is None:
            oldUnitId = self.getDefaultStockUnitId(nomenclatureId)
        if newUnitId is None:
            newUnitId = self.getDefaultStockUnitId(nomenclatureId)
        if oldUnitId == newUnitId:
            return 1
        ratio = getNomenclatureUnitRatio(nomenclatureId, oldUnitId, newUnitId)
        return ratio


    def getSimpleRatio(self, nomenclatureId, oldUnitId, newUnitId):
        if oldUnitId is None:
            oldUnitId = self.getDefaultStockUnitId(nomenclatureId)
        if newUnitId is None:
            newUnitId = self.getDefaultStockUnitId(nomenclatureId)
        if oldUnitId == newUnitId:
            return 1
        ratio = getNomenclatureSimpleUnitRatio(nomenclatureId, oldUnitId, newUnitId)
        return ratio


    def on_buttonBox_reset(self):
        for item in self.modelNomenclatureExpense._items:
            if forceBool(item.value('available')):
                item.setValue('include', QVariant(False))
        self.modelNomenclatureExpense.reset()


    @pyqtSignature('')
    def on_btnAPNomenclatureExpense_clicked(self):
        model = self.tblActionsExpense.model()
        items = model.items()
        row = self.tblActionsExpense.currentIndex().row()
        if 0 <= row < len(items):
            record, action = items[row]
            self._openNomenclatureEditor(action, record, row)
#            if not self._openNomenclatureEditor(action, record, row):
#                if action.nomenclatureExpense:
#                    action.nomenclatureExpense.cancelEx()


    def _openNomenclatureEditor(self, action, record, row, requireItems=False):
        if not action:
            return False
        if not action.getType().isNomenclatureExpense:
            return True
        if not action.nomenclatureExpense:
            return True
        action = self.getActionChanged(self.tblActionsExpense.currentIndex().row(), record, action)
        if action and action.nomenclatureExpense.stockMotionRecord():
            supplierId = forceRef(action.getRecord().value('orgStructure_id'))
            if supplierId:
                action.nomenclatureExpense.setSupplierId(supplierId)
#            if requireItems and not action.nomenclatureExpense.stockMotionItems():
#                nomenclatureIdDict = {}
#                nomenclatureId = action.findNomenclaturePropertyValue()
#                if not nomenclatureId:
#                    return True
#                nomenclatureIdDict[nomenclatureId] = (action.getRecord(), action.findDosagePropertyValue())
#                action.nomenclatureExpense.updateNomenclatureIdListToAction(nomenclatureIdDict)
            if not action.nomenclatureExpense.stockMotionItems():
                return True
            isControlExecWriteOffNomenclatureExpense = QtGui.qApp.controlExecutionWriteOffNomenclatureExpense()
            if isControlExecWriteOffNomenclatureExpense:
                mapNomenclatureToAction = self.getNomenclatureToActions()
                db = QtGui.qApp.db
                message = u''
                nomenclatureLine = []
                resQntDict = {}
                nomenclatureIdDict = {}
                tableNomenclature = db.table('rbNomenclature')
                if action.nomenclatureExpense:
                    aTNomenclatureList = []
                    masterId = forceRef(record.value('actionType_id'))
                    aTNomenclatureItems = mapNomenclatureToAction.get((masterId, row), [])
                    for item in aTNomenclatureItems:
                        include = forceBool(item.value('include'))
                        if include and (not forceBool(item.value('selectionGroup')) or forceBool(item.value('available')) or self.getIncludeAvailable(aTNomenclatureItems, forceInt(item.value('selectionGroup')))):
                            aTNomenclatureList.append(item)
                    nomenclatureIdDict = {}
                    for aTNomenclature in aTNomenclatureList:
                        nomenclatureIdAT = forceRef(aTNomenclature.value('nomenclature_id'))
                        nomenclatureIdDict[nomenclatureIdAT] = forceDouble(aTNomenclature.value('amount'))
                    stockMotionItems = action.nomenclatureExpense.stockMotionItems()
                    for stockMotionItem in stockMotionItems:
                        price = forceDouble(stockMotionItem.value('price'))
                        oldPrice = price
                        nomenclatureId = forceRef(stockMotionItem.value('nomenclature_id'))
                        if nomenclatureId and nomenclatureId not in nomenclatureLine:
                            qnt = forceDouble(stockMotionItem.value('qnt'))
                            resQnt, planQnt, simpleRatio = resQntDict.get(nomenclatureId, (None, None, 2))
                            unitId = forceRef(stockMotionItem.value('unit_id'))
                            stockUnitId = self.getDefaultStockUnitId(nomenclatureId)
                            ratio = self.getRatio(nomenclatureId, stockUnitId, unitId)
                            if ratio is not None:
                                price = price*ratio
                                qnt = qnt / ratio
                            qnt = round(qnt, QtGui.qApp.numberDecimalPlacesQnt())
                            if planQnt is None:
                                dosage = nomenclatureIdDict.get(nomenclatureId, 0)
                                planQnt = action.nomenclatureExpense.getNomenclatureDosageToQntValue(nomenclatureId, dosage)
                                if ratio is not None:
                                    planQnt = planQnt / ratio
                                planQnt = round(planQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            financeId = forceRef(stockMotionItem.value('finance_id'))
                            batch = forceString(stockMotionItem.value('batch'))
                            shelfTime = forceDate(stockMotionItem.value('shelfTime'))
                            shelfTime = shelfTime.toPyDate() if bool(shelfTime) else None
                            medicalAidKindId = forceRef(stockMotionItem.value('medicalAidKind_id'))
                            otherHaving=[u'(shelfTime>=curDate()) OR shelfTime is NULL']
                            existsQnt = getExistsNomenclatureAmount(nomenclatureId, financeId, batch, orgStructureId=supplierId, unitId=stockUnitId, medicalAidKindId = medicalAidKindId, shelfTime=shelfTime, otherHaving=otherHaving, exact=True, price=price, isStockUtilization=False, precision=QtGui.qApp.numberDecimalPlacesQnt())
                            masterId = forceRef(stockMotionItem.value('master_id'))
                            prevQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=masterId, batch=batch, financeId=financeId, medicalAidKindId=medicalAidKindId, price=None, oldPrice=oldPrice, oldUnitId=stockUnitId), QtGui.qApp.numberDecimalPlacesQnt()) if masterId else 0
                            reservationQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=None, batch=batch, financeId=financeId, clientId=action.nomenclatureExpense._clientId, medicalAidKindId=medicalAidKindId, price=None, oldPrice=price, oldUnitId=stockUnitId), QtGui.qApp.numberDecimalPlacesQnt())
                            if existsQnt < 0:
                                existsQnt = 0
                            if prevQnt < 0:
                                prevQnt = 0
                            if reservationQnt < 0:
                                reservationQnt = 0
                            if resQnt is None:
                                resQnt = (existsQnt + reservationQnt + prevQnt) - qnt
                            else:
                                resQnt += (existsQnt + reservationQnt + prevQnt) - qnt
                            resQnt = round(resQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            planQnt = planQnt - qnt
                            planQnt = round(planQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            resQntDict[nomenclatureId] = (resQnt, planQnt, len(forceStringEx(self.getSimpleRatio(nomenclatureId, stockUnitId, unitId))))
                    for nomenclatureIdKey, (resQntValue, planQntValue, simpleQntRatio) in resQntDict.items():
                        if resQntValue < 0 or resQntValue is None or (round(planQntValue, simpleQntRatio) != 0 and planQntValue is not None):
                            nomenclatureLine.append(nomenclatureIdKey)
                    if nomenclatureLine:
                        records = db.getRecordList(tableNomenclature, [tableNomenclature['name']], [tableNomenclature['id'].inlist(nomenclatureLine)], order = tableNomenclature['name'].name())
                        nomenclatureName = u','.join(forceString(recordNomenclature.value('name')) for recordNomenclature in records)
                        message += u'''Действие типа %s.\nОтсутствуют ЛСиИМН: %s!\n'''%(action._actionType.name, nomenclatureName)
                    if message:
                        if isControlExecWriteOffNomenclatureExpense == 1:
                            button = QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel
                            message2 = u'Списываемого ЛСиИМН %s недостаточно на остатке подразделения. Выполнить списание?'%(nomenclatureName)
                        else:
                            button = QtGui.QMessageBox.Cancel
                            message2 = u'Списываемого ЛСиИМН %s недостаточно на остатке подразделения. Выполнение назначения невозможно!\n'%(nomenclatureName)
                        res = QtGui.QMessageBox.warning(None,
                                                  u'Внимание!',
                                                  message2,
                                                  button,
                                                  QtGui.QMessageBox.Cancel)
                        if res == QtGui.QMessageBox.Cancel:
                            return False
                        
            if QtGui.qApp.keyboardModifiers() & Qt.ShiftModifier:
                dlg = CClientRefundInvoiceEditDialog(self)
                dlg.setData(action.nomenclatureExpense)
            else:
                dlg = CClientInvoiceEditDialog(self, fromAction=True)
                medicalAidKindId = action.getMedicalAidKindId()
                financeId = action.getFinanceId()
                clientId = action.nomenclatureExpense._clientId
                dlg.setFinanceId(financeId)
                if medicalAidKindId:
                    dlg.setMedicalAidKindId(medicalAidKindId)
                dlg.setData(action.nomenclatureExpense)
                dlg.setClientId(clientId)
            try:
                dlg.exec_()
                dlg.getRecord()
                result = dlg.closeByOkButton
                action.setNomenclatureExpensePreliminarySave(result)
            finally:
                dlg.deleteLater()
            return result
        else:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Не удалось инициализировать записи ЛСиИМН \nсвязанные с данным действием!',
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)


class CNomenclatureExpenseModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ActionType_Nomenclature', 'id', 'master_id', parent)
        self.addExtCol(CBoolInDocTableCol( u'Включить', 'include', 10), QVariant.Bool)
        self.addCol(CNomenclatureInDocTableCol(u'ЛСиИМН',  'nomenclature_id', 15, showFields = CRBComboBox.showName).setReadOnly())
        self.addCol(CFloatInDocTableCol(u'Количество',     'amount', 10, precision=QtGui.qApp.numberDecimalPlacesQnt()))
        self.addCol(CBoolInDocTableCol( u'Доступно для выбора', 'available', 3).setReadOnly())
        self.addCol(CIntInDocTableCol(  u'Группа выбора',  'selectionGroup', 15, low=-100, high=100).setReadOnly())
        #self.addHiddenCol('amount')
        self.addHiddenCol('writeoffTime')
        self.mapNomenclatureToAction = {}
        self.isUpdateInclude = False


    def flags(self, index):
        if index.column() == self.getColIndex('include') and forceBool(self.value(index.row(), 'available')):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        if index.column() == self.getColIndex('amount'):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('include', QVariant.Bool))
        return result


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                if column == self.getColIndex('amount'):
                    col = self._cols[column]
                    record = self._items[row]
                    return record.value(col.fieldName())
            if role == Qt.DisplayRole:
                col = self._cols[column]
                record = self._items[row]
                if column == record.indexOf('available'):
                    return col.toString(record.value(col.fieldName()), record)
                else:
                    return col.toString(record.value(col.fieldName()), record)
            if role == Qt.CheckStateRole:
                col = self._cols[column]
                record = self._items[row]
                if column == record.indexOf('available'):
                    return col.toCheckState(record.value(col.fieldName()), record)
                else:
                    return col.toCheckState(record.value(col.fieldName()), record)
            return CInDocTableModel.data(self, index, role)
        return QVariant()


    def updateAvailableIncludes(self, row, column, selectionGroup):
        for i, item in enumerate(self._items):
            if i != row and selectionGroup == forceInt(item.value('selectionGroup')) and forceBool(item.value('available')):
                item.setValue('include', QVariant(False))
                self.emitCellChanged(i, column)


    def updateNotAvailableIncludes(self, row, column, include, selectionGroup):
        for i, item in enumerate(self._items):
            if i != row and forceBool(item.value('selectionGroup')) and selectionGroup == forceInt(item.value('selectionGroup')) and not forceBool(item.value('available')):
                item.setValue('include', QVariant(include))
                self.emitCellChanged(i, column)


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        if role == Qt.CheckStateRole:
            if row >= 0 and row < len(self.items()):
                if column == self.getColIndex('include'):
                    include = forceBool(value)
                    self.setValue(row, 'include', QVariant(include))
                    if include:
                        self.updateAvailableIncludes(row, column, forceInt(self.items()[row].value('selectionGroup')))
                    self.updateNotAvailableIncludes(row, column, include, forceInt(self.items()[row].value('selectionGroup')))
                    self.emitCellChanged(row, column)
                    self.isUpdateInclude = True
                    return True
        if role == Qt.EditRole:
            if row >= 0 and row < len(self.items()):
                if column == self.getColIndex('amount'):
                    self.setValue(row, 'amount', QVariant(value))
                    self.emitCellChanged(row, column)
                    return True
        return False


    def getNomenclatureToActions(self):
        return self.mapNomenclatureToAction


    def setNomenclatureToAction(self, masterId, row):
        self.mapNomenclatureToAction[(masterId, row)] = self._items


    def loadItems(self, masterId, row):
        self._items = self.mapNomenclatureToAction.get((masterId, row), [])
        if not self._items:
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
            order = [table['selectionGroup'].name(), table['available'].name()]
            records = db.getRecordList(table, cols, filter, order)
            records.sort(key=lambda item: forceInt(item.value('selectionGroup')))
            self._items = records
            if self._extColsPresent:
                extSqlFields = []
                for col in self._cols:
                    if col.external():
                        fieldName = col.fieldName()
                        if fieldName not in cols:
                            extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))
                if extSqlFields:
                    for item in self._items:
                        for field in extSqlFields:
                            item.append(field)
                for record in records:
                    if not forceBool(record.value('selectionGroup')):
                        available = forceBool(record.value('available'))
                        record.setValue('include', QVariant(not available))
                self._items = records
                self.mapNomenclatureToAction[(masterId, row)] = self._items
        self.reset()


class CActionsExpenseModel(QAbstractTableModel):
    def __init__(self, parent, actionExpenseItems):
        QAbstractTableModel.__init__(self, parent)
        self.actionExpenseItems = actionExpenseItems
        self._cols = []
        self._items = []
        self.addCol(CRBInDocTableCol(u'Мероприятия', 'actionType_id', 14, 'ActionType', showFields=2).setReadOnly())
        self.table = QtGui.qApp.db.table('Action')


    def addCol(self, col):
        self._cols.append(col)
        return col


    def items(self):
        return self._items


    def columnCount(self, index=None):
        return len(self._cols)


    def rowCount(self, index=None):
        return len(self._items)


    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self._cols[section].title()
            if role == Qt.ToolTipRole:
                return self._cols[section].toolTip()
            if role == Qt.WhatsThisRole:
                return self._cols[section].whatsThis()
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                col = self._cols[column]
                record = self._items[row][0]
                return record.value(col.fieldName())
            if role == Qt.DisplayRole:
                col = self._cols[column]
                record = self._items[row][0]
                return col.toString(record.value(col.fieldName()), record)
            if role == Qt.StatusTipRole:
                col = self._cols[column]
                record = self._items[row][0]
                return col.toStatusTip(record.value(col.fieldName()), record)
            if role == Qt.TextAlignmentRole:
                col = self._cols[column]
                return col.alignment()
            if role == Qt.CheckStateRole:
                col = self._cols[column]
                record = self._items[row][0]
                return col.toCheckState(record.value(col.fieldName()), record)
            if role == Qt.ForegroundRole:
                col = self._cols[column]
                record = self._items[row][0]
                return col.getForegroundColor(record.value(col.fieldName()), record)
        return QVariant()


    def loadItems(self, masterId=None):
        self._items = self.actionExpenseItems
        self.reset()


    def isLocked(self, row):
        if 0 <= row < len(self._items):
            action = self._items[row][1]
            if action:
                return action.isLocked()
        return False


    def isLockedOrExposed(self, row):
        if 0 <= row < len(self._items):
            recod, action = self._items[row]
            return forceInt(recod.value('payStatus'))!=0 or (action and action.isLocked())
        return False


    def isExposed(self, row):
        if 0 <= row < len(self._items):
            record, action = self._items[row]
            if action:
                return action.isExposed()
        return False


    def actionTypeId(self, row):
        if 0 <= row < len(self._items):
            return forceInt(self._items[row][0].value('actionType_id'))
        else:
            return None

