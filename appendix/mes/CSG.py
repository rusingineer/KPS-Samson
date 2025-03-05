# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtCore, QtGui

from MKBTree import checkMKBTable, getMKBName, CMKBInDocTableCol
from Ui_CSGEditor import Ui_CSGEditor
from library.AgeSelector import composeAgeSelector, parseAgeSelector
from library.InDocTable import CInDocTableModel, CIntInDocTableCol, CEnumInDocTableCol, CInDocTableCol, \
    CFloatInDocTableCol
from library.ItemsListDialog import CItemEditorBaseDialog
from library.TableModel import CTableModel, CDoubleCol, CEnumCol, CRefBookCol, CTextCol, CIntCol
from library.Utils import forceString, toVariant, forceStringEx, forceRef
from library.crbcombobox import CRBComboBox
from library.interchange import getCheckBoxValue, getComboBoxValue, getLineEditValue, setCheckBoxValue, \
    setComboBoxValue, setLineEditValue, setRBComboBoxValue, getRBComboBoxValue

SexList = ['', u'М', u'Ж']

class CCSGTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CTextCol(   u'Код',               ['code'], 40),
            CTextCol(   u'Наименование',      ['name'], 60),
            CEnumCol(   u'Пол',               ['sex'], SexList, 10),
            CTextCol(   u'Возраст',           ['age'], 10),
            CTextCol(   u'Некое доп.условие', ['note'], 6),
            CRefBookCol(u'Профиль',           ['group_id'], 'mrbMESGroup', 20, showFields=CRBComboBox.showCodeAndName),
            CIntCol(    u'Политравма',        ['isPolyTrauma'], 10)
            ], 'CSG')


class CCSGMKBModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CTextCol(u'Диагноз',     ['mkb'], 10),
            CTextCol(u'Группировка', ['groupingMKB'], 10),
            CEnumCol(u'Сочетаемость',['blendingMKB'], [u'основной и дополнительный', u'основной', u'дополнительный'], 10)
            ], 'CSG_Diagnosis')
        QtCore.QObject.connect(self, QtCore.SIGNAL('dataChanged(const QModelIndex&, const QModelIndex&)'), self.updateDiagnosis)


    def cellReadOnly(self, index):
        return index.column() == 1


    def updateDiagnosis(self, lt=None, rb=None):
        if lt and lt.column() > 0:
            return
        if not checkMKBTable():
            return
        for i in xrange(self.rowCount()-1):
            code = forceString(self.data(self.index(i, 0)))
            name = getMKBName(code)


class CCSGServicesModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CTextCol(u'Номенклатурный код услуги',               ['serviceCode'], 40),
            CTextCol(u'Название услуги',      ['serviceName'], 60),
            CTextCol(u'Ещё какой-то код услуги',      ['localServiceCode'], 60),
            CDoubleCol(u'УЕТ для взрослого', ['auet'], 10),
            CDoubleCol(u'УЕТ для ребёнка', ['cuet'], 10),
            CDoubleCol(u'Частота использования для взрослого', ['afreq'], 10),
            CDoubleCol(u'Частота использования для взрослого', ['cfreq'], 10),
            CDoubleCol(u'УЕТ общей анастезии для взрослого', ['agauet'], 10),
            CDoubleCol(u'УЕТ общей анастезии для ребёнка', ['cgauet'], 10),
            CIntCol(u'Кратность', ['multiple'], 30)
            ], 'CSG_Service')


class CCSGMKBExModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'CSG_Diagnosis', 'id', 'master_id', parent)
        self.__parent = parent
        self.addCol(CMKBInDocTableCol(u'Диагноз', 'mkb', 10)).setSortable(True)
        self.addCol(CIntInDocTableCol(u'Группировка', 'groupingMKB', 10)).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Сочетаемость', 'blendingMKB', 10, [u'основной и дополнительный', u'основной', u'дополнительный'])).setSortable(True)
        QtCore.QObject.connect(self, QtCore.SIGNAL('dataChanged(const QModelIndex&, const QModelIndex&)'), self.updateDiagnosis)


    def cellReadOnly(self, index):
        return index.column() == 1


    def updateDiagnosis(self, lt=None, rb=None):
        if lt and lt.column() > 0:
            return
        if not checkMKBTable():
            return
        for i in xrange(self.rowCount()-1):
            code = forceString(self.data(self.index(i, 0)))
            name = getMKBName(code)


class CCSGServicesExModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'CSG_Service', 'id', 'master_id', parent)
        self.__parent = parent
        self.addCol(CInDocTableCol(u'Номенклатурный код услуги', 'serviceCode', 40)).setSortable(True)
        self.addCol(CInDocTableCol(u'Название услуги', 'serviceName', 40)).setSortable(True)
        self.addCol(CInDocTableCol(u'Ещё какой-то код услуги', 'localServiceCode', 40)).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'УЕТ для взрослого', 'auet', 10, precision=2)).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'УЕТ для ребёнка', 'cuet', 10, precision=2)).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'Частота использования для взрослого', 'afreq', 10, precision=2)).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'Частота использования для взрослого', 'cfreq', 10, precision=2)).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'УЕТ общей анастезии для взрослого', 'agauet', 10, precision=2)).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'УЕТ общей анастезии для ребёнка', 'cgauet', 10, precision=2)).setSortable(True)
        self.addCol(CInDocTableCol(u'Кратность', 'multiple', 30)).setSortable(True)


class CCSGEditor(CItemEditorBaseDialog, Ui_CSGEditor):
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'CSG')
        self.setupUi(self)

        self.addModels('CSGDiagnosisEx', CCSGMKBExModel(self))
        self.setModels(self.tblCSGDiagnosisEx, self.modelCSGDiagnosisEx, self.selectionModelCSGDiagnosisEx)
        self.tabCSGDiagnosisEx.setFocusProxy(self.tblCSGDiagnosisEx)
        self.tblCSGDiagnosisEx.addPopupDelRow()

        self.addModels('CSGServicesEx', CCSGServicesExModel(self))
        self.setModels(self.tblCSGServicesEx, self.modelCSGServicesEx, self.selectionModelCSGServicesEx)
        self.tabCSGServicesEx.setFocusProxy(self.tblCSGServicesEx)
        self.tblCSGServicesEx.addPopupDelRow()
        self.cmbMRBMESGroup.setTable('mrbMESGroup', addNone=True, filter='deleted=0')

        self.setWindowTitleEx(u'Редактор КСГ')
        self.setupDirtyCather()


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(self.edtCSGCode, record, 'code')
        setLineEditValue(self.edtCSGName, record, 'name')
        setComboBoxValue(self.cmbCSGSex,  record, 'sex')
        (begUnit, begCount, endUnit, endCount) = parseAgeSelector(forceString(record.value('age')))
        self.cmbBegAgeUnit.setCurrentIndex(begUnit)
        self.edtBegAgeCount.setText(str(begCount))
        self.cmbEndAgeUnit.setCurrentIndex(endUnit)
        self.edtEndAgeCount.setText(str(endCount))
        setCheckBoxValue(self.chkCSGActiviti, record, 'active')
        setCheckBoxValue(self.chkCSGInternal, record, 'internal')
        setCheckBoxValue(self.chkPolyTrauma, record, 'isPolyTrauma')
        setRBComboBoxValue(self.cmbMRBMESGroup, record, 'group_id')
        itemId = self.itemId()
        self.modelCSGDiagnosisEx.loadItems(itemId)
        self.modelCSGServicesEx.loadItems(itemId)


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(self.edtCSGCode, record, 'code')
        getLineEditValue(self.edtCSGName, record, 'name')
        getComboBoxValue(self.cmbCSGSex,  record, 'sex')
        record.setValue('age',        toVariant(composeAgeSelector(
                    self.cmbBegAgeUnit.currentIndex(),  forceStringEx(self.edtBegAgeCount.text()),
                    self.cmbEndAgeUnit.currentIndex(),  forceStringEx(self.edtEndAgeCount.text())
                        )))
        getCheckBoxValue(self.chkCSGActiviti, record, 'active')
        getCheckBoxValue(self.chkCSGInternal, record, 'internal')
        getCheckBoxValue(self.chkPolyTrauma, record, 'isPolyTrauma')
        getRBComboBoxValue(self.cmbMRBMESGroup, record, 'group_id')
        return record


    def saveInternals(self, id):
        self.modelCSGDiagnosisEx.saveItems(id)
        self.modelCSGServicesEx.saveItems(id)


    def checkDataEntered(self):
        result = True
        result = result and (self.edtCSGCode.text() or self.checkInputMessage(u'код', False, self.edtCSGCode))
        result = result and self.checkDubleCodeEntered()
        result = result and (self.edtCSGName.text() or self.checkInputMessage(u'наименование', False, self.edtCSGName))
        return result


    def checkDubleCodeEntered(self):
        query = QtGui.qApp.db.query('''
            SELECT id FROM CSG WHERE code = '%s' '''%self.edtCSGCode.text())
        if query.size() > 0:
            query.first()
            if forceRef(query.record().value('id')) != self.itemId():
                return False
        return True

