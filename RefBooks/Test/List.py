# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import QVariant, SIGNAL, Qt

from library.InDocTable      import CInDocTableModel, CInDocTableCol, CRBInDocTableCol
from library.ItemEditorDialogWithIdentification import CItemEditorDialogWithIdentification
from library.interchange     import getLineEditValue, getRBComboBoxValue, getSpinBoxValue, getTextEditValue, setLineEditValue, setRBComboBoxValue, setSpinBoxValue, setTextEditValue
from library.ItemsListDialog import CItemsListDialog, CItemEditorBaseDialog
from library.TableModel      import CNumCol, CTextCol, CRefBookCol
from library.Utils           import forceRef, forceInt

from RefBooks.Tables         import rbCode, rbName, rbRegionalCode, rbFederalCode
from Orgs.EquipmentComboBox  import CEquipmentComboBox

from Ui_TestListDialog       import Ui_TestListDialog
from Ui_RBTestEditor         import Ui_RBTestEditorDialog
from Ui_TestListFilterDialog import Ui_ItemFilterDialog


class CRBTestList(Ui_TestListDialog, CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',          [rbCode], 32),
            CTextCol(u'Наименование', [rbName], 40),
            CTextCol(u'Региональный код', [rbRegionalCode], 32),
            CTextCol(u'Федеральный код', [rbFederalCode], 32),
            CRefBookCol(u'Группа', ['testGroup_id'], 'rbTestGroup', 15),
            CNumCol(u'Позиция', ['position'], 15),
            CTextCol(u'Примечание', ['note'], 40),
            ], 'rbTest', ['rbTest.' + rbCode, 'rbTest.' + rbName], filterClass=CRBTestListFilterDialog)
        self.setWindowTitleEx(u'Показатели исследований')
        self.tblItems.addPopupDelRow()


    def getItemEditor(self):
        return CRBTestEditor(self)


    def setSort(self, col):
        name = self.model.cols()[col].fields()[0]
        if name == 'testGroup_id':
            self.order = 'rbTestGroup.name'
        elif name == 'note':
            self.order = 'rbTest.note'
        elif name == 'name':
            self.order = 'rbTest.name'
        elif name == 'code':
            self.order = 'rbTest.code'
        else:
            self.order = name
        header = self.tblItems.horizontalHeader()
        header.setSortIndicatorShown(True)
        self.isAscending = not self.isAscending
        header.setSortIndicator(col, Qt.AscendingOrder if self.isAscending else Qt.DescendingOrder)
        if self.isAscending:
            self.order = self.order + u' ASC'
        else:
            self.order = self.order + u' DESC'
        self.renewListAndSetTo(self.currentItemId())


    def select(self, props):
        db = QtGui.qApp.db
        tableTest = self.model.table()
        tableEquipmentTest = db.table('rbEquipment_Test')
        tableTestGroup = db.table('rbTestGroup')
        table = tableTest.leftJoin(tableEquipmentTest, tableEquipmentTest['test_id'].eq(tableTest['id']))
        table = table.leftJoin(tableTestGroup, tableTest['testGroup_id'].eq(tableTestGroup['id']))

        cond = []
        groupId = props.get('groupId', None)
        nameContains = props.get('nameContains', None)
        edtFederalCode = props.get('federalCode', None)
        testCode = props.get('testCode', None)
        equipmentId = props.get('equipmentId', None)

        if groupId:
            cond.append(tableTest['testGroup_id'].eq(groupId))
        if nameContains:
            orCond = db.joinOr([
                tableTest['name'].contain(unicode(nameContains)),
                tableEquipmentTest['hardwareTestName'].contain(unicode(nameContains)),
            ])
            cond.append(orCond)

        if edtFederalCode:
            cond.append(tableTest['federalCode'].contain(unicode(edtFederalCode)))

        if testCode:
            orCond = db.joinOr([
                tableTest['code'].contain(unicode(testCode)),
                tableEquipmentTest['hardwareTestCode'].contain(unicode(testCode)),
            ])
            cond.append(orCond)
        if equipmentId:
            cond.append(tableEquipmentTest['equipment_id'].eq(equipmentId))

        result = []
        query = db.query(db.selectStmt(table, 'DISTINCT rbTest.id', cond, self.order))
        while query.next():
            result.append(forceInt(query.value(0)))
        return result


class CRBTestEditor(Ui_RBTestEditorDialog, CItemEditorDialogWithIdentification):
    def __init__(self,  parent):
        CItemEditorDialogWithIdentification.__init__(self, parent, 'rbTest')

        self.addModels('TestEquipments', CTestEquipmentModel(self))
        self.addModels('TestAnalog',     CTestAnalogModel(self))

        # self.setupUi(self)
        self.setWindowTitleEx(u'Показатель исследования')

        self.setModels(self.tblEquipments, self.modelTestEquipments, self.selectionModelTestEquipments)
        self.setModels(self.tblTestAnalog, self.modelTestAnalog, self.selectionModelTestAnalog)

        self.tblEquipments.addPopupSelectAllRow()
        self.tblEquipments.addPopupClearSelectionRow()
        self.tblEquipments.addPopupDelRow()

        self.cmbTestGroup.setTable('rbTestGroup', addNone=True)

        self.actSyncTestAnalogList = QtGui.QAction(u'Синхронизировать аналоги тестов по текущему', self)
        self.tblTestAnalog.createPopupMenu(actions=[self.actSyncTestAnalogList])
        self.connect(self.actSyncTestAnalogList, SIGNAL('triggered()'), self.syncTestAnalogListByCurrent)
        self.connect(self.tblTestAnalog.popupMenu(), SIGNAL('aboutToShow()'), self.on_aboutToShow)
        self.setupDirtyCather()


    def on_aboutToShow(self):
        self.actSyncTestAnalogList.setEnabled(bool(len(self.modelTestAnalog.items())))


    def syncTestAnalogListByCurrent(self):
        db = QtGui.qApp.db
        testIdList = [forceRef(item.value('analogTest_id')) for item in self.modelTestAnalog.items()]
        currentTestId = self.itemId()
        table = db.table('rbTest_AnalogTest')
        for testId in testIdList:
            localAnalogTestIdList = list(set(testIdList) - set([testId])) + [currentTestId]
            for analogTestId in localAnalogTestIdList:
                cond = [table['master_id'].eq(testId),
                        table['analogTest_id'].eq(analogTestId)]
                record = db.getRecordEx(table, '*', cond)
                if not record:
                    record = table.newRecord()
                    record.setValue('master_id', QVariant(testId))
                    record.setValue('analogTest_id', QVariant(analogTestId))
                    db.insertRecord(table, record)


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(self.edtCode, record, rbCode)
        setLineEditValue(self.edtName, record, rbName)
        setLineEditValue(self.edtRegionalCode, record, rbRegionalCode)
        setLineEditValue(self.edtFederalCode, record, rbFederalCode)
        setRBComboBoxValue(self.cmbTestGroup, record, 'testGroup_id')
        setSpinBoxValue(self.edtPosition, record, 'position')
        setTextEditValue(self.txtNote, record, 'note')

        itemId = self.itemId()
        self.modelTestEquipments.loadItems(itemId)
        self.modelTestAnalog.loadItems(itemId)
        self.modelIdentification.loadItems(itemId)


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(self.edtCode, record, rbCode)
        getLineEditValue(self.edtName, record, rbName)
        getLineEditValue(self.edtRegionalCode, record, rbRegionalCode)
        getLineEditValue(self.edtFederalCode, record, rbFederalCode)
        getRBComboBoxValue(self.cmbTestGroup, record, 'testGroup_id')
        getSpinBoxValue(self.edtPosition, record, 'position')
        getTextEditValue(self.txtNote, record, 'note')
        return record

    def saveInternals(self, id):
        self.modelTestEquipments.saveItems(id)
        self.modelTestAnalog.saveItems(id)
        self.modelIdentification.saveItems(id)


# ##############################################


class CRBEquipmentCol(CRBInDocTableCol):
    def createEditor(self, parent):
        editor = CEquipmentComboBox(parent)
        editor.setTable(self.tableName, addNone=self.addNone, filter=self.filter)
        editor.setShowFields(self.showFields)
        editor.setPreferredWidth(self.preferredWidth)
        return editor


class CTestEquipmentModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbEquipment_Test', 'id', 'test_id', parent)
        self.addCol(CRBEquipmentCol(u'Оборудование',  'equipment_id',   15, 'rbEquipment')).setSortable(True)
        self.addCol(CInDocTableCol(u'Код теста', 'hardwareTestCode', 15)).setSortable(True)
        self.addCol(CInDocTableCol(u'Наименование теста', 'hardwareTestName', 15)).setSortable(True)
        self.addCol(CInDocTableCol(u'Код образца', 'hardwareSpecimenCode', 15)).setSortable(True)
        self.addCol(CInDocTableCol(u'Наименование образца', 'hardwareSpecimenName', 15)).setSortable(True)


# ####

class CRBTestAnalogCol(CRBInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, parentEditor, **params):
        CRBInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)
        self._parentEditor = parentEditor

    def createEditor(self, parent):
        self.filter = u'`id` != %d' % self._parentEditor.itemId()
        return CRBInDocTableCol.createEditor(self, parent)


class CTestAnalogModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbTest_AnalogTest', 'id', 'master_id', parent)
        self.addCol(CRBTestAnalogCol(u'Тест аналог',  'analogTest_id',   15, 'rbTest', parent, showFields=2)).setSortable(True)


class CRBTestListFilterDialog(QtGui.QDialog, Ui_ItemFilterDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbGroup.setTable('rbTestGroup')
        self.setWindowTitle(u'Фильтр показателей исследований')


    def setProps(self, props):
        self.cmbGroup.setValue(props.get('groupId', 0))
        self.edtNameContains.setText(props.get('nameContains', ''))
        self.edtCode.setText(props.get('testCode', ''))
        self.edtFederalCode.setText(props.get('federalCode', ''))
        self.cmbEquipment.setValue(props.get('equipmentId', 0))


    def props(self):
        result = {}
        result['groupId'] = self.cmbGroup.value()
        result['nameContains'] = self.edtNameContains.text()
        result['testCode'] = self.edtCode.text()
        result['federalCode'] = self.edtFederalCode.text()
        result['equipmentId'] = self.cmbEquipment.value()
        return result
