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
from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from Ui_RBService import Ui_Dialog
from Ui_ServiceFilterDialog import Ui_ServiceFilterDialog
from appendix.mes.RefBooksLocal.ItemsListDialogEx import CItemEditorDialogEx
from appendix.mes.RefBooksLocal.Tables import rbServiceGroup, rbCode, rbName, rbService_Contents
from library.InDocTable import CInDocTableModel, CCodeNameInDocTableCol, CIntInDocTableCol, CFloatInDocTableCol
from library.ItemsListDialog import CItemsSplitListDialogEx, CItemEditorBaseDialog
from library.TableModel import CTextCol, CRefBookCol, CNumCol
from library.Utils import addDots, forceStringEx, forceRef, forceDouble
from library.crbcombobox import CRBComboBox
from library.interchange import setLineEditValue, setRBComboBoxValue, setDoubleBoxValue, getLineEditValue, \
    getDoubleBoxValue, getRBComboBoxValue


def isComplexService(code):
    return code[0] == u'В'


class CRBServiceList(CItemsSplitListDialogEx):
    def __init__(self, parent):
        CItemsSplitListDialogEx.__init__(self, parent,
            'mrbService',
            [
            CTextCol(   u'Код',           ['code'], 10),
            CTextCol(   u'Наименование',  ['name'], 30),
            CRefBookCol(   u'Группа услуг',     ['group_id'], rbServiceGroup, 30),
            CNumCol(   u'УЕТ врача',      ['doctorWTU'], 30),
            CNumCol(   u'УЕТ средний',    ['paramedicalWTU'], 30),
            ],
            [rbCode, rbName],
            rbService_Contents,
            [
            CRefBookCol(u'Код', ['service_id'], 'mrbService', 20, showFields=CRBComboBox.showCode),
            CRefBookCol(u'Наименование', ['service_id'], 'mrbService', 50, showFields=CRBComboBox.showName),
            CNumCol(   u'СЧЕ',         ['averageQnt'], 20),
            CNumCol(   u'ЧН',          ['necessity'], 20),
            ],
            'master_id', 'service_id',
            uniqueCode=True, filterClass=CServiceFilterDialog)
        self.setWindowTitle(u'Услуги')

    def getItemEditor(self):
        return CRBServiceEditor(self)

    def select(self, props):
        table = self.model.table()
        cond = [table['deleted'].eq(0)]

        code = props.get('code', '')
        if code:
            cond.append(table['code'].likeBinary(addDots(code)))

        name = props.get('name', '')
        if name:
            cond.append(table['name'].contain(name))

        group = props.get('group_id', None)
        if group:
            cond.append(table['group_id'].eq(group))

        doctorWTU = props.get('doctorWTU', '')
        if doctorWTU:
            cond.append(table['doctorWTU'].eq(doctorWTU))

        paramedicalWTU = props.get('paramedicalWTU', '')
        if paramedicalWTU:
            cond.append(table['paramedicalWTU'].eq(paramedicalWTU))


        return QtGui.qApp.db.getIdList(table.name(),
                           'id',
                           cond,
                           self.order)

class CServiceFilterDialog(QtGui.QDialog, Ui_ServiceFilterDialog):
    def __init__(self,  parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbServiceGroup.setTable('mrbServiceGroup')
        self.edtCode.setFocus(Qt.ShortcutFocusReason)


    def setProps(self,  props):
        self.edtCode.setText(props.get('code', ''))
        self.edtName.setText(props.get('name', ''))
        self.cmbServiceGroup.setValue(props.get('group_id', 0))
        self.edtDoctorWTU.setValue(props.get('doctorWTU', 0))
        self.edtParamedicalWTU.setValue(props.get('paramedicalWTU', 0))


    def props(self):
        result = {'code'   : forceStringEx(self.edtCode.text()),
                  'name'   : forceStringEx(self.edtName.text()),
                  'group_id'  : forceRef(self.cmbServiceGroup.value()),
                  'doctorWTU'   : forceDouble(self.edtDoctorWTU.value()),
                  'paramedicalWTU'   : forceDouble(self.edtParamedicalWTU.value()),
                 }
        return result

#
# ##########################################################################
#

class CServicesModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, rbService_Contents, 'id', 'master_id', parent)
        self.__parent = parent
        self.addCol(CCodeNameInDocTableCol(u'Услуга', 'service_id', 40, 'mrbService', preferredWidth = 100, filter='deleted=0'))
        self.addCol(CIntInDocTableCol(u'СЧЕ', 'averageQnt', 10, low=1, high=1000))
        self.addCol(CFloatInDocTableCol(u'ЧН', 'necessity', 10, precision=2))

#
# ##########################################################################
#

class CRBServiceEditor(CItemEditorDialogEx, Ui_Dialog):
    def __init__(self,  parent):
        CItemEditorDialogEx.__init__(self, parent, 'mrbService')
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Услуга')
        self.cmbType.setTable(rbServiceGroup)

        self.addModels('Services', CServicesModel(self))
        self.setModels(self.tblServices, self.modelServices, self.selectionModelServices)
        self.tblServices.addPopupDelRow()

        self.setupDirtyCather()


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(   self.edtCode,         record, 'code')
        setLineEditValue(   self.edtName,         record, 'name')
        setRBComboBoxValue(   self.cmbType,       record, 'group_id')
        setDoubleBoxValue(   self.edtDoctor,       record, 'doctorWTU')
        setDoubleBoxValue(   self.edtParamedical,  record, 'paramedicalWTU')
        if isComplexService(self.edtCode.text()):
            self.modelServices.loadItems(self.itemId())
            self.tblServices.show()
        else:
            self.tblServices.hide()

    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(   self.edtCode,         record, 'code')
        getLineEditValue(   self.edtName,         record, 'name')
        getRBComboBoxValue(   self.cmbType,       record, 'group_id')
        getDoubleBoxValue(   self.edtDoctor,       record, 'doctorWTU')
        getDoubleBoxValue(   self.edtParamedical,  record, 'paramedicalWTU')
        return record

    def saveInternals(self, id):
        self.modelServices.saveItems(id)
