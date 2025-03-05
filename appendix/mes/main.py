#!/usr/bin/env python
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


import codecs
import locale
import os
import sys
import traceback

from PyQt4 import QtGui, QtCore, QtSql
from PyQt4.QtCore import SIGNAL, Qt, QObject, pyqtSignature, QSettings, QByteArray, QDateTime, QDir

from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CReportViewDialog
from appendix.mes.CSG import CCSGTableModel, CCSGMKBModel, CCSGServicesModel, CCSGEditor
from appendix.mes.ExchangeLocal.ExportXML import ExportXML
from appendix.mes.ExchangeLocal.ImportXML import ImportXML
from appendix.mes.MesEdit import MesEditor
from appendix.mes.MesInfo import CMesInfo, CMesModel
from appendix.mes.RefBooksLocal.MesKSG import CMesKSGList
from appendix.mes.RefBooksLocal.RBBloodPreparation import CRBBloodPreparationList
from appendix.mes.RefBooksLocal.RBBloodPreparationType import CRBBloodPreparationTypeList
from appendix.mes.RefBooksLocal.RBEquipment import CRBEquipmentList
from appendix.mes.RefBooksLocal.RBEquipmentGroup import CRBEquipmentGroupList
from appendix.mes.RefBooksLocal.RBMedicament import CRBMedicamentList
from appendix.mes.RefBooksLocal.RBMedicamentDosageForm import CRBMedicamentDosageFormList
from appendix.mes.RefBooksLocal.RBMedicamentGroup import CRBMedicamentGroupList
from appendix.mes.RefBooksLocal.RBMesGroup import CRBMesGroupList
from appendix.mes.RefBooksLocal.RBNutrient import CRBNutrientList
from appendix.mes.RefBooksLocal.RBNutrientGroup import CRBNutrientGroupList
from appendix.mes.RefBooksLocal.RBService import CRBServiceList
from appendix.mes.RefBooksLocal.RBServiceGroup import CRBServiceGroupList
from appendix.mes.RefBooksLocal.RBSpeciality import CRBSpecialityList
from appendix.mes.RefBooksLocal.RBVisitType import CRBVisitTypeList
from appendix.mes.Ui_MesList import Ui_MainWindow
from library.Calendar import CCalendarInfo
from library.DialogBase import CConstructHelperMixin
from library.InDocTable import CRecordListModel, CInDocTableCol
from library.Preferences import CPreferences
from library.Utils import forceString, forceInt, forceBool, anyToUnicode
from library.database import CMySqlDatabase
from preferences.connection import CConnectionDialog

title = u'САМСОН'
subtitle = u'Редактор МЭС'
about = u'Комплекс Программных Средств \n' \
        u'"Система автоматизации медико-страхового обслуживания населения"\n' \
        u'КПС «%s»\n'   \
        u'Версия 2.5 (ревизия %s от %s)\n' \
        u'Утилита "Редактор МЭС"\n' \
        u'Copyright © 2014 ООО "САМСОН Групп"\n' \
        u'распространяется под лицензией GNU GPL v.3 или выше\n' \
        u'Основано на КПС «САМСОН-ВИСТА» версии 2.0\n' \
        u'телефон тех.поддержки (812) 418-39-70'




class CModelMKB(CRecordListModel):
    def __init__(self,  parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Код диагноза',    'diagnosis_code', 10).setReadOnly().setSortable(True))
        # self.addCol(CInDocTableCol(u'Диагноз', 'diagnosis', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Доп.код диагноза', 'additional_diagnosis_code', 6)).setReadOnly()
        # self.addCol(CInDocTableCol(u'Доп.диагноз', 'additional_diagnosis', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Код соп. диагноза', 'sop_diagnosis_code', 6)).setReadOnly()
        # self.addCol(CInDocTableCol(u'Соп.диагноз', 'sop_diagnosis', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Код осложнения диагноза',    'diagnosis_complication_code', 10).setReadOnly().setSortable(True))
        # self.addCol(CInDocTableCol(u'Диагноз осложнения', 'diagnosis_of_complications', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Группировка', 'grouping', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Сочетаемость', 'compatibility', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Доп.критерий', 'additional_criteria', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата начала', 'start_date', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата окончания', 'end_date', 6)).setReadOnly()


    def loadData(self, order=None, ord_by=None, stmt=None):
        db = QtGui.qApp.db
        items = []

        if order is None:
            pass
        else:
            if ord_by is True:
                stmt = stmt + u" ORDER BY {0}".format(int(order) + 1)
            else:
                stmt = stmt + u" ORDER BY {0} DESC".format(int(order) + 1)

        query = db.query(stmt)

        while query.next():
            items.append(query.record())
        self.setItems(items)




class CModelServices(CRecordListModel):
    def __init__(self,  parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Группа',   'ggroup', 10).setReadOnly().setSortable(True))
        self.addCol(CInDocTableCol(u'Код',      'code', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Название',     'name', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'УЕТ вр.',   'yet_vr', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'УЕТ перс.',   'yet_pers', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'СК',       'sk', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'ЧП',       'cp', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Группа',   'ggroup', 10).setReadOnly().setSortable(True))
        self.addCol(CInDocTableCol(u'Объединять',      'jjoin', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Пол',     'sex', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Единица С',   'unit_c', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Минимальный возраст',   'min_age', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Единица ПО',       'unit_po', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Максимальный возраст',       'max_age', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Период контроля',   'сontrol_period', 10).setReadOnly().setSortable(True))
        self.addCol(CInDocTableCol(u'Доп.критерий',      'additional_criteria', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'мин. фракций',     'min_fractions', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'макс. фракций',   'max_fractions', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата начала',   'start_date', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата окончания',       'end_date', 6)).setReadOnly()


    def loadData(self, order=None, ord_by=None, stmt=None):
        db = QtGui.qApp.db
        items = []

        if order is None:
            pass
        else:
            if ord_by is True:
                stmt = stmt + u" ORDER BY {0}".format(int(order) + 1)
            else:
                stmt = stmt + u" ORDER BY {0} DESC".format(int(order) + 1)

        query = db.query(stmt)

        while query.next():
            items.append(query.record())
        self.setItems(items)




class CModelVisits(CRecordListModel):
    def __init__(self,  parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Тип визита',               'type_visit', 10).setReadOnly().setSortable(True))
        self.addCol(CInDocTableCol(u'Специальность',            'specialization', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Код услуги',               'service_code', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Доп. код',                 'additional_code', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Альтернативный доп. код',  'alternative_additional_code', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Группировка',              'grouping', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'СК',                       'sc', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Пол',                      'sex', 10).setReadOnly().setSortable(True))
        self.addCol(CInDocTableCol(u'Единица С',                'unit_with', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Минимальный возраст',      'minimum_age', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Единица ПО',               'unit_by', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Максимальный возраст',     'maximum_age', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Период контроля',          'control_period', 10).setReadOnly().setSortable(True))


    def loadData(self, order=None, ord_by=None, stmt=None):
        db = QtGui.qApp.db
        items = []

        if order is None:
            pass
        else:
            if ord_by is True:
                stmt = stmt + u" ORDER BY {0}".format(int(order) + 1)
            else:
                stmt = stmt + u" ORDER BY {0} DESC".format(int(order) + 1)

        query = db.query(stmt)

        while query.next():
            items.append(query.record())
        self.setItems(items)




class CModelEquipment(CRecordListModel):
    def __init__(self,  parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Код',               'code', 10).setReadOnly().setSortable(True))
        self.addCol(CInDocTableCol(u'Оборудование',      'equipment', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'СЧЕ',               'sche', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'ЧН',                'chn', 6)).setReadOnly()


    def loadData(self, order=None, ord_by=None, stmt=None):
        db = QtGui.qApp.db
        items = []

        if order is None:
            pass
        else:
            if ord_by is True:
                stmt = stmt + u" ORDER BY {0}".format(int(order) + 1)
            else:
                stmt = stmt + u" ORDER BY {0} DESC".format(int(order) + 1)

        query = db.query(stmt)

        while query.next():
            items.append(query.record())
        self.setItems(items)



class CModelMedicament(CRecordListModel):
    def __init__(self,  parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Код',                  'ccode', 10).setReadOnly().setSortable(True))
        self.addCol(CInDocTableCol(u'МНН',                  'mhh', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Торговое название',    'trade_name', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Форма выпуска',        'release_form', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Кол-во в упак.',       'quantity_per_pack', 10).setReadOnly().setSortable(True))
        self.addCol(CInDocTableCol(u'Цена упак.',           'package_price', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Цена ед.',             'unit_price', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дозировка',            'dosage', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Лекарственная форма',  'dosage_form', 10).setReadOnly().setSortable(True))
        self.addCol(CInDocTableCol(u'СЧЕ',                  'sche', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'ЧН',                   'chn', 6)).setReadOnly()


    def loadData(self, order=None, ord_by=None, stmt=None):
        db = QtGui.qApp.db
        items = []

        if order is None:
            pass
        else:
            if ord_by is True:
                stmt = stmt + u" ORDER BY {0}".format(int(order) + 1)
            else:
                stmt = stmt + u" ORDER BY {0} DESC".format(int(order) + 1)

        query = db.query(stmt)

        while query.next():
            items.append(query.record())
        self.setItems(items)




class CModelBlood(CRecordListModel):
    def __init__(self,  parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Код',          'code', 10).setReadOnly().setSortable(True))
        self.addCol(CInDocTableCol(u'Наименование', 'name', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дозировка',    'dosage', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'СЧЕ',          'sche', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'ЧН',           'chn', 6)).setReadOnly()


    def loadData(self, order=None, ord_by=None, stmt=None):
        db = QtGui.qApp.db
        items = []

        if order is None:
            pass
        else:
            if ord_by is True:
                stmt = stmt + u" ORDER BY {0}".format(int(order) + 1)
            else:
                stmt = stmt + u" ORDER BY {0} DESC".format(int(order) + 1)

        query = db.query(stmt)

        while query.next():
            items.append(query.record())
        self.setItems(items)




class CModelNutrient(CRecordListModel):
    def __init__(self,  parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Код',          'ccode', 10).setReadOnly().setSortable(True))
        self.addCol(CInDocTableCol(u'Дозировка',    'dosage', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Тариф',        'rate', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'СЧЕ',          'sche', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'ЧН',           'chn', 6)).setReadOnly()


    def loadData(self, order=None, ord_by=None, stmt=None):
        db = QtGui.qApp.db
        items = []

        if order is None:
            pass
        else:
            if ord_by is True:
                stmt = stmt + u" ORDER BY {0}".format(int(order) + 1)
            else:
                stmt = stmt + u" ORDER BY {0} DESC".format(int(order) + 1)

        query = db.query(stmt)

        while query.next():
            items.append(query.record())
        self.setItems(items)




class CModelFeaturesLimitedBySexAge(CRecordListModel):
    def __init__(self,  parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Пол',                  'sex', 10).setReadOnly().setSortable(True))
        self.addCol(CInDocTableCol(u'Единица С',            'unit_with', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Минимальный возраст',  'minimum_age', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Единица ПО',           'unit_by', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Максимальный возраст', 'maximum_age', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Период контроля',      'control_period', 6)).setReadOnly()


    def loadData(self, order=None, ord_by=None, stmt=None):
        db = QtGui.qApp.db
        items = []

        if order is None:
            pass
        else:
            if ord_by is True:
                stmt = stmt + u" ORDER BY {0}".format(int(order) + 1)
            else:
                stmt = stmt + u" ORDER BY {0} DESC".format(int(order) + 1)

        query = db.query(stmt)

        while query.next():
            items.append(query.record())
        self.setItems(items)




class mainWin(QtGui.QMainWindow, Ui_MainWindow, CConstructHelperMixin):
    # Номера колонок в mesView
    colId = 0
    colActive = 1
    colGroupName = 2
    colKSGName = 3
    colCode = 4
    colName = 5
    colAvgDuration = 6
    colPatientModel =  7
    colTariff = 8
    colDescr = 9
    colMinDuration = 10
    colMaxDuration = 11
    colKSGNorm = 12
    colGroupId = 13
    colInternal = 14
    colPeriodicity = 15
    colKSGId = 16
    colEndDate = 17
    colPolyTrauma = 18

    # Скрытые колонки в mesView
    hiddenColumns = (colMinDuration, colMaxDuration,
                         colKSGNorm, colGroupId, colId, colKSGId)

    def __init__(self, app):
        QtGui.QMainWindow.__init__(self)
        self.application = app
        QtGui.qApp = app

        self.openDbSetup()
        self.tableModelCSGList = CCSGTableModel(self)
        self.tableSelectionModelCSGList = QtGui.QItemSelectionModel(self.tableModelCSGList, self)
        self.tableSelectionModelCSGList.setObjectName('tableSelectionModelCSGList')

        self.modelCSGDiagnosis = CCSGMKBModel(self)
        self.selectionModelCSGDiagnosis = QtGui.QItemSelectionModel(self.modelCSGDiagnosis, self)
        self.selectionModelCSGDiagnosis.setObjectName('selectionModelCSGDiagnosis')

        self.modelCSGService = CCSGServicesModel(self)
        self.selectionModelCSGService = QtGui.QItemSelectionModel(self.modelCSGService, self)
        self.selectionModelCSGService.setObjectName('selectionModelCSGService')

        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self.__sortColumnMKB = None
        self.__sortAscendingMKB = False
        self.connect(self.tableMKB.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sortByColumnMKB)

        self.__sortColumnServices = None
        self.__sortAscendingServices = False
        self.connect(self.tableServices.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sortByColumnServices)

        self.__sortColumnVisits = None
        self.__sortAscendingVisits = False
        self.connect(self.tableVisits.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sortByColumnVisits)

        self.__sortColumnEquipment = None
        self.__sortAscendingEquipment = False
        self.connect(self.tableEquipment.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sortByColumnEquipment)

        self.__sortColumnMedicament = None
        self.__sortAscendingMedicament = False
        self.connect(self.tableMedicament.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sortByColumnMedicament)

        self.__sortColumnBlood = None
        self.__sortAscendingBlood = False
        self.connect(self.tableBlood.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sortByColumnBlood)

        self.__sortColumnNutrient = None
        self.__sortAscendingNutrient = False
        self.connect(self.tableNutrient.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sortByColumnNutrient)

        self.__sortColumnLimitedBySexAge = None
        self.__sortAscendingLimitedBySexAge = False
        self.connect(self.tableLimitedBySexAge.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sortByColumnLimitedBySexAge)

        self.mes = CMesInfo()
        self.initModels()
        self.initView()
        self.initFilter()
        self.openDbPostSetup()
#        self.openDb()
        self.setTableParam()

        if self.application.db:
            self.cmbGroup.setTable('mrbMESGroup', filter='deleted=0')

        self.tblCSGList.setModel(self.tableModelCSGList)
        self.tblCSGList.setSelectionModel(self.tableSelectionModelCSGList)
        self.tblCSGList.installEventFilter(self)

        self.tblCSGDiagnosis.setModel(self.modelCSGDiagnosis)
        self.tblCSGDiagnosis.setSelectionModel(self.selectionModelCSGDiagnosis)

        self.tblCSGService.setModel(self.modelCSGService)
        self.tblCSGService.setSelectionModel(self.selectionModelCSGService)

        self.showMaximized()

        QObject.connect(self.action_connect, QtCore.SIGNAL('triggered()'), self.openDb)
        QObject.connect(self.action_disconnect, QtCore.SIGNAL('triggered()'), self.closeDb)
        QObject.connect(self.action_add, QtCore.SIGNAL('triggered()'), self.add)
        QObject.connect(self.action_edit, QtCore.SIGNAL('triggered()'), self.edit)
        QObject.connect(self.action_print, QtCore.SIGNAL('triggered()'), self.print_)
        QObject.connect(self.action_find, QtCore.SIGNAL('triggered()'), self.find)
        QObject.connect(self.action_connection, QtCore.SIGNAL('triggered()'), self.on_actConnection_triggered)
        QObject.connect(self.action_about, QtCore.SIGNAL('triggered()'), self.on_actAbout_triggered)
        QObject.connect(self.action_Qt, QtCore.SIGNAL('triggered()'), self.on_actAboutQt_triggered)

        for action in dir(self):
            if action[:9] == 'action_rb':
                QObject.connect(getattr(self, action), QtCore.SIGNAL('triggered()'), getattr(self, 'on_act' + action[7:] + '_triggered'))

        QObject.connect(self.btnAdd, QtCore.SIGNAL('clicked()'), self.add)
        QObject.connect(self.btnEdit, QtCore.SIGNAL('clicked()'), self.edit)
        QObject.connect(self.btnFind, QtCore.SIGNAL('clicked()'), self.find)
        QObject.connect(self.mesView, QtCore.SIGNAL('doubleClicked(QModelIndex)'), self.edit)
        QObject.connect(self.btnPrint, QtCore.SIGNAL('clicked()'), self.print_)
        QObject.connect(self.btnClear, QtCore.SIGNAL('clicked()'), self.clearFilter)
        QObject.connect(self.btnUpdate, QtCore.SIGNAL('clicked()'), self.updateFilter)

        self.tblCSGList.model().setIdList(self.setCSGList())
        self.tblCSGList.setCurrentRow(0)
        self.txtCSGBrowser.setHtml(self.getCSGBrowserInfo())
        self.lblCountCSG.setText(u'В списке %d записей'%self.tableModelCSGList.rowCount())
        self.tblCSGList.addPopupDublicateRow()
        self.tblCSGList.addPopupDelRow()


    def getCSGFilter(self):
        db = QtGui.qApp.db
        table = db.table('CSG')
        cond = []
        if self.checkCode.isChecked():
            cond.append(table['code'].like(forceString(self.edtCode.text()) + u'%'))
        if self.checkName.isChecked():
            cond.append(table['name'].like(forceString(self.edtName.text()) + u'%'))
        if self.checkMKB.isChecked():
            cond.append('''EXISTS(SELECT *
                                  FROM CSG_Diagnosis
                                  WHERE CSG_Diagnosis.master_id = CSG.id AND CSG_Diagnosis.mkb LIKE '%s%%')'''%forceString(self.edtMKB.text()))
        if self.rbActive.isChecked():
            cond.append(table['active'].eq(1))
        elif self.rbNotActive.isChecked():
            cond.append(table['active'].eq(0))
        if self.rbInternal.isChecked():
            cond.append(table['internal'].eq(1))
        elif self.rbExternal.isChecked():
            cond.append(table['internal'].eq(0))
        return cond


    def setCSGList(self):
        db = QtGui.qApp.db
        if not db:
            return []
        table = db.table('CSG')
        cond = self.getCSGFilter()
        return db.getDistinctIdList(table, table['id'].name(),
                              where=cond,
                              order=u'CSG.code ASC, CSG.name ASC')


    @pyqtSignature('QModelIndex')
    def on_tblCSGList_doubleClicked(self, index):
        self.edit()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_tableSelectionModelCSGList_currentChanged(self, current, previous):
        CSGId = self.tblCSGList.itemId(current)
        if CSGId:
            db = QtGui.qApp.db
            table = db.table('CSG_Diagnosis')
            idList = db.getIdList(table, 'id', [table['master_id'].eq(CSGId)],  ['id'])
            self.tblCSGDiagnosis.model().setIdList(idList)
            table = db.table('CSG_Service')
            idList = db.getIdList(table, 'id', [table['master_id'].eq(CSGId)],  ['id'])
            self.tblCSGService.model().setIdList(idList)
        self.txtCSGBrowser.setHtml(self.getCSGBrowserInfo())


    @pyqtSignature('int')
    def on_tabMESCSGWidget_currentChanged(self, index):
        enable = not index
        self.checkGroup.setEnabled(enable)
        self.cmbGroup.setEnabled(enable)


    def MKBQuery(self):
        stmt = u"""
        SELECT MES_mkb.mkb as diagnosis_code,
        /*s11.MKB.DiagName as diagnosis,*/
        MES_mkb.mkb2 as sop_diagnosis_code,
        /*MKB_mkb2.DiagName as sop_diagnosis,*/
        MES_mkb.mkb3 as diagnosis_complication_code,
        /*MKB_mkb3.DiagName as diagnosis_of_complications,*/
        MES_mkb.groupingMKB AS grouping,
        IF(MES_mkb.blendingMKB = 0, 'основной и дополнительный', IF(MES_mkb.blendingMKB = 1, 'основной', 'дополнительный')) AS compatibility,
        MES_mkb.krit as additional_criteria,
        DATE(MES_mkb.begDate) as start_date,
        DATE(MES_mkb.endDate) as end_date
        FROM MES_mkb
        /*LEFT JOIN s11.MKB on s11.MKB.DiagID = LEFT(MES_mkb.mkb, 5)
        LEFT JOIN s11.MKB AS MKB_mkbEx on MKB_mkbEx.DiagID = LEFT(MES_mkb.mkbEx, 5)
        LEFT JOIN s11.MKB AS MKB_mkb2 on MKB_mkb2.DiagID = LEFT(MES_mkb.mkb2, 5)
        LEFT JOIN s11.MKB AS MKB_mkb3 on MKB_mkb3.DiagID = LEFT(MES_mkb.mkb3, 5)*/
        WHERE MES_mkb.master_id = %s
        and MES_mkb.deleted = 0
        """%self.mes.id
        return stmt


    def ServicesQuery(self):
        stmt = u"""
        SELECT mrbServiceGroup.name as ggroup,
        mrbService.code as code,
        mrbService.name as name,
        mrbService.doctorWTU as yet_vr,
        mrbService.paramedicalWTU as yet_pers,
        MES_service.averageQnt as sk,
        MES_service.necessity as cp,
        MES_service.groupCode as ggroup,
        MES_service.binding as jjoin,
        IF(sex = 1, 'М', IF(sex = 2, 'Ж', 'не определено')) as sex,
        IF(begAgeUnit = 1, 'Д', IF(begAgeUnit = 2, 'Н', IF(begAgeUnit = 3, 'М', IF(begAgeUnit = 4, 'Г','не определено')))) as unit_c,
        minimumAge as min_age,
        IF(endAgeUnit = 1, 'Д', IF(endAgeUnit = 2, 'Н', IF(endAgeUnit = 3, 'М', IF(endAgeUnit = 4, 'Г','не определено')))) as unit_po,
        maximumAge as max_age,
        IF(controlPeriod = 1, 'Конец года случая', IF(controlPeriod = 2, 'Конец предыдущего случаю года', 'Дата случая')) as сontrol_period,
        MES_service.krit as additional_criteria,
        MES_service.minFr as min_fractions,
        MES_service.maxFr as max_fractions,
        DATE(MES_service.begDate) as start_date,
        DATE(MES_service.endDate) as end_date
        FROM MES_service
        LEFT JOIN mrbService ON mrbService.id = MES_service.service_id
        LEFT JOIN mrbServiceGroup ON mrbServiceGroup.id = mrbService.group_id
        WHERE master_id = %d
        and MES_service.deleted = 0
        """%self.mes.id
        return  stmt

    def VisitsQuery(self):
        stmt = u"""
        SELECT mrbVisitType.name as type_visit,
        mrbSpeciality.name as specialization,
        MES_visit.serviceCode as service_code,
        MES_visit.additionalServiceCode as additional_code,
        MES_visit.altAdditionalServiceCode as alternative_additional_code,
        MES_visit.groupCode as grouping,
        MES_visit.averageQnt as sc,
        IF(sex = 1, 'М', IF(sex = 2, 'Ж', 'не определено')) as sex,
        IF(begAgeUnit = 1, 'Д', IF(begAgeUnit = 2, 'Н', IF(begAgeUnit = 3, 'М', IF(begAgeUnit = 4, 'Г','не определено')))) as unit_with,
        minimumAge as minimum_age,
        IF(endAgeUnit = 1, 'Д', IF(endAgeUnit = 2, 'Н', IF(endAgeUnit = 3, 'М', IF(endAgeUnit = 4, 'Г','не определено')))) as unit_by,
        maximumAge as maximum_age,
        IF(controlPeriod = 1, 'Конец года случая', IF(controlPeriod = 2, 'Конец предыдущего случаю года', 'Дата случая')) as control_period
        FROM MES_visit
        LEFT JOIN mrbVisitType ON mrbVisitType.id = MES_visit.visitType_id
        LEFT JOIN mrbSpeciality ON mrbSpeciality.id = MES_visit.speciality_id
        WHERE master_id = %d
        and MES_visit.deleted = 0
        """%self.mes.id

        return stmt

    def EquipmentQuery(self):
        stmt = u"""
        SELECT mrbEquipment.code as code,
        mrbEquipment.name as Equipment,
        MES_equipment.averageQnt as sche,
        MES_equipment.necessity as CHN
        FROM MES_equipment
        LEFT JOIN mrbEquipment ON mrbEquipment.id = MES_equipment.equipment_id
        WHERE master_id = %d
        and MES_equipment.deleted = 0
        """%self.mes.id

        return stmt

    def MedicamentQuery(self):
        stmt = u"""
         SELECT MES_medicament.medicamentCode as ccode,
         mrbMedicament.name as mhh,
         mrbMedicament.tradeName as trade_name,
         mrbMedicament.form as release_form,
         mrbMedicament.packSize as quantity_per_pack,
         mrbMedicament.packPrice as package_price,
         mrbMedicament.unitPrice as unit_price,
         MES_medicament.dosage as dosage,
         mrbMedicamentDosageForm.name as dosage_form,
         MES_medicament.averageQnt as sche,
         MES_medicament.necessity as chn
         FROM MES_medicament
         LEFT JOIN mrbMedicament ON mrbMedicament.code = MES_medicament.medicamentCode
         LEFT JOIN mrbMedicamentDosageForm ON mrbMedicamentDosageForm.id = MES_medicament.dosageForm_id
         WHERE master_id = %d
         and MES_medicament.deleted = 0
         """ % self.mes.id
        return stmt

    def BloodQuery(self):
        stmt = u"""
        SELECT
        mrbBloodPreparation.code as ccode,
        mrbBloodPreparation.dosage as dosage,
        mrbBloodPreparation.tariff as rate,
        MES_bloodPreparation.averageQnt as sche,
        MES_bloodPreparation.necessity as chn
        FROM MES_bloodPreparation
        LEFT JOIN mrbBloodPreparation ON mrbBloodPreparation.id = MES_bloodPreparation.preparation_id
        WHERE master_id = %d
        and MES_bloodPreparation.deleted = 0
        """%self.mes.id
        return stmt

    def NutrientQuery(self):
        stmt = u"""
        SELECT mrbNutrient.code as code,
        mrbNutrient.name as name,
        mrbNutrient.dosage as dosage,
        mrbNutrient.tariff as rate,
        MES_nutrient.averageQnt as sche,
        MES_nutrient.necessity as chn
        FROM MES_nutrient
        LEFT JOIN mrbNutrient ON mrbNutrient.id = MES_nutrient.nutrient_id
        WHERE master_id = %d
        and MES_nutrient.deleted = 0
        """%self.mes.id
        return stmt

    def LimitedBySexAgeQuery(self):
        stmt = u"""
        SELECT IF(sex = 1, 'М', IF(sex = 2, 'Ж', 'не определено')) as sex,
        IF(begAgeUnit = 1, 'Д', IF(begAgeUnit = 2, 'Н', IF(begAgeUnit = 3, 'М', IF(begAgeUnit = 4, 'Г','не определено')))) as unit_with,
        minimumAge as minimum_age,
        IF(endAgeUnit = 1, 'Д', IF(endAgeUnit = 2, 'Н', IF(endAgeUnit = 3, 'М', IF(endAgeUnit = 4, 'Г','не определено')))) as unit_by,
        maximumAge as maximum_age,
        IF(controlPeriod = 1, 'Конец года случая', IF(controlPeriod = 2, 'Конец предыдущего случаю года', 'Дата случая')) as control_period
        FROM MES_limitedBySexAge
        WHERE master_id = %d AND deleted = 0
        """%self.mes.id
        return stmt


    def initModels(self):
        self.mesModel = CMesModel(self)

        self.modelFeaturesMKB = CModelMKB(self)
        self.modelFeaturesServices = CModelServices(self)
        self.modelFeaturesVisits = CModelVisits(self)
        self.modelFeaturesEquipment = CModelEquipment(self)
        self.modelFeaturesMedicament = CModelMedicament(self)
        self.modelFeaturesBlood = CModelBlood(self)
        self.modelFeaturesNutrient = CModelNutrient(self)
        self.modelFeaturesLimitedBySexAge = CModelFeaturesLimitedBySexAge(self)


    def initView(self):
        self.mesView.setModel(self.mesModel)
        self.mesView.addPopupDublicateRow()
        self.mesView.addPopupDelRow()
        QObject.connect(self.mesView.selectionModel(), QtCore.SIGNAL('currentRowChanged(QModelIndex, QModelIndex)'), self.update)


    def sortByColumnMKB(self, column):
        header = self.tableMKB.horizontalHeader()
        if column == self.__sortColumnMKB:
            if self.__sortAscendingMKB:
                self.__sortAscendingMKB = False
            else:
                self.__sortAscendingMKB = True
        else:
            self.__sortColumnMKB = column
            self.__sortAscendingMKB = True
        header.setSortIndicatorShown(True)
        header.setSortIndicator(column, Qt.AscendingOrder if self.__sortAscendingMKB else Qt.DescendingOrder)
        stmt = self.MKBQuery()
        self.modelFeaturesMKB.loadData(column, self.__sortAscendingMKB, stmt)


    def sortByColumnServices(self, column):
        header = self.tableServices.horizontalHeader()
        if column == self.__sortColumnServices:
            if self.__sortAscendingServices:
                self.__sortAscendingServices = False
            else:
                self.__sortAscendingServices = True
        else:
            self.__sortColumnServices = column
            self.__sortAscendingServices = True
        header.setSortIndicatorShown(True)
        header.setSortIndicator(column, Qt.AscendingOrder if self.__sortAscendingServices else Qt.DescendingOrder)
        stmt = self.ServicesQuery()
        self.modelFeaturesServices.loadData(column, self.__sortAscendingServices, stmt)


    def sortByColumnVisits(self, column):
        header = self.tableVisits.horizontalHeader()
        if column == self.__sortColumnVisits:
            if self.__sortAscendingVisits:
                self.__sortAscendingVisits = False
            else:
                self.__sortAscendingVisits = True
        else:
            self.__sortColumnVisits = column
            self.__sortAscendingVisits = True
        header.setSortIndicatorShown(True)
        header.setSortIndicator(column, Qt.AscendingOrder if self.__sortAscendingVisits else Qt.DescendingOrder)
        stmt = self.Visits()
        self.modelFeaturesVisits.loadData(column, self.__sortAscendingVisits, stmt)


    def sortByColumnEquipment(self, column):
        header = self.tableEquipment.horizontalHeader()
        if column == self.__sortColumnEquipment:
            if self.__sortAscendingEquipment:
                self.__sortAscendingEquipment = False
            else:
                self.__sortAscendingEquipment = True
        else:
            self.__sortColumnEquipment = column
            self.__sortAscendingEquipment = True
        header.setSortIndicatorShown(True)
        header.setSortIndicator(column, Qt.AscendingOrder if self.__sortAscendingEquipment else Qt.DescendingOrder)
        stmt = self.EquipmentQuery()
        self.modelFeaturesEquipment.loadData(column, self.__sortAscendingEquipment, stmt)


    def sortByColumnMedicament(self, column):
        header = self.tableMedicament.horizontalHeader()
        if column == self.__sortColumnMedicament:
            if self.__sortAscendingMedicament:
                self.__sortAscendingMedicament = False
            else:
                self.__sortAscendingMedicament = True
        else:
            self.__sortColumnMedicament = column
            self.__sortAscendingMedicament = True
        header.setSortIndicatorShown(True)
        header.setSortIndicator(column, Qt.AscendingOrder if self.__sortAscendingMedicament else Qt.DescendingOrder)
        stmt = self.MedicamentQuery()
        self.modelFeaturesMedicament.loadData(column, self.__sortAscendingMedicament, stmt)


    def sortByColumnBlood(self, column):
        header = self.tableBlood.horizontalHeader()
        if column == self.__sortColumnBlood:
            if self.__sortAscendingBlood:
                self.__sortAscendingBlood = False
            else:
                self.__sortAscendingBlood = True
        else:
            self.__sortColumnBlood = column
            self.__sortAscendingBlood = True
        header.setSortIndicatorShown(True)
        header.setSortIndicator(column, Qt.AscendingOrder if self.__sortAscendingBlood else Qt.DescendingOrder)
        stmt = self.BloodQuery()
        self.modelFeaturesBlood.loadData(column, self.__sortAscendingBlood, stmt)


    def sortByColumnNutrient(self, column):
        header = self.tableNutrient.horizontalHeader()
        if column == self.__sortColumnNutrient:
            if self.__sortAscendingNutrient:
                self.__sortAscendingNutrient = False
            else:
                self.__sortAscendingNutrient = True
        else:
            self.__sortColumnNutrient = column
            self.__sortAscendingNutrient = True
        header.setSortIndicatorShown(True)
        header.setSortIndicator(column, Qt.AscendingOrder if self.__sortAscendingNutrient else Qt.DescendingOrder)
        stmt = self.NutrientQuery()
        self.modelFeaturesNutrient.loadData(column, self.__sortAscendingNutrient, stmt)


    def sortByColumnLimitedBySexAge(self, column):
        header = self.tableLimitedBySexAge.horizontalHeader()
        if column == self.__sortColumnLimitedBySexAge:
            if self.__sortAscendingLimitedBySexAge:
                self.__sortAscendingLimitedBySexAge = False
            else:
                self.__sortAscendingLimitedBySexAge = True
        else:
            self.__sortColumnLimitedBySexAge = column
            self.__sortAscendingLimitedBySexAge = True
        header.setSortIndicatorShown(True)
        header.setSortIndicator(column, Qt.AscendingOrder if self.__sortAscendingLimitedBySexAge else Qt.DescendingOrder)
        stmt = self.LimitedBySexAgeQuery()
        self.modelFeaturesLimitedBySexAge.loadData(column, self.__sortAscendingLimitedBySexAge, stmt)


    def initFilter(self):
        self.filter = '1'


    def clearFilter(self):
        self.checkGroup.setChecked(False)
        self.checkCode.setChecked(False)
        self.checkName.setChecked(False)
        self.checkMKB.setChecked(False)
        self.checkMKBEx.setChecked(False)
        self.rbActive.setChecked(True)
        self.rbInternalAll.setChecked(True)
        self.updateFilter()


    def updateFilter(self):
        if self.tabMESCSGWidget.currentIndex():
            self.updateCSGList()
        else:
            self.filter = '1'
            if self.checkGroup.isChecked():
                group_id = self.cmbGroup.value()
                if group_id:
                    self.filter += """ AND MES.group_id = %d"""%group_id
            if self.checkCode.isChecked():
                self.filter += """ AND MES.code like '%s%%'"""%self.edtCode.text()
            if self.checkName.isChecked():
                self.filter += """ AND MES.name like '%%%s%%'"""%self.edtName.text()
            if self.checkMKB.isChecked():
                self.filter += """ AND exists
                                                (select * from MES_mkb
                                                where MES_mkb.master_id = MES.id
                                                and MES_mkb.mkb like '%s%%')"""%self.edtMKB.text()
            if self.checkMKBEx.isChecked():
                self.filter += """ AND exists
                                                (select * from MES_mkb
                                                where MES_mkb.master_id = MES.id
                                                and MES_mkb.mkbEx like '%s%%')"""%self.edtMKBEx.text()
            if self.rbActive.isChecked():
                self.filter += """ AND MES.active = 1"""
            elif self.rbNotActive.isChecked():
                self.filter += """ AND MES.active = 0"""
            if self.rbInternal.isChecked():
                self.filter += """ AND MES.internal = 1"""
            elif self.rbExternal.isChecked():
                self.filter += """ AND MES.internal = 0"""

            self.updateMain()


    def getCellStr(self, row, column):
        return self.mesModel.data(self.mesModel.index(row, column)).toString()


    def getCellInteger(self, row, column):
        return self.mesModel.data(self.mesModel.index(row, column)).toInt()[0]


    def getCellFloat(self, row, column):
        return self.mesModel.data(self.mesModel.index(row, column)).toDouble()[0]


    def getCellDate(self, row, column):
        return self.mesModel.data(self.mesModel.index(row, column)).toDate()


    def getCellBool(self, row, column):
        return self.mesModel.data(self.mesModel.index(row, column)).toBool()


    def getBrowserCode(self):
        result = ''
        result += '<b>' + self.mes.getName() + '</b>' + '<br>'
        result += u'Минимальная длительность: ' + '<i>' + str(self.mes.getMinDuration()) + '</i>' + '<br>'
        result += u'Максимальная длительность: ' + '<i>' + str(self.mes.getMaxDuration()) + '</i>' + '<br>'
        result += u'Средняя длительность: ' + '<i>' + str(self.mes.getAvgDuration()) + '</i>' + '<br>'
        result += u'Норматив визитов: ' + '<i>' + str(self.mes.getKSGNorm()) + '</i>' + '<br>'
        result += u'Дата окончания: ' + '<i>' + forceString(self.mes.getEndDate()) + '</i>' + '<br>'
        result += u'Политравма: ' + '<i>' + [u'нет', u'да'][forceInt(self.mes.getPolyTrauma())] + '</i>' + '<br>'
        patient_model = self.mes.getPatientModelDict()
        formatted_model = ["%s: <i>%s</i>"%(key, patient_model[key]) for key in patient_model]
        result += '<br>'.join(formatted_model)
        return result


    def getCSGBrowserInfo(self):
        CSGId = self.tblCSGList.currentItemId()
        result = ''
        if CSGId:
            db = QtGui.qApp.db
            table = db.table('CSG')
            record = db.getRecordEx(table, '*', [table['id'].eq(CSGId)])
            if record:
                result += '<b>' + forceString(record.value('name')) + '</b>' + '<br>'
                result += u'Код: ' + '<i>' + forceString(record.value('code')) + '</i>' + '<br>'
                result += u'Пол: ' + '<i>' + [u'не определено', u'мужской', u'женский'][forceInt(record.value('sex'))] + '</i>' + '<br>'
                result += u'Возраст: ' + '<i>' + forceString(record.value('age')) + '</i>' + '<br>'
                result += u'Некое доп. условие: ' + '<i>' + forceString(record.value('note')) + '</i>' + '<br>'
                result += u'Активно: ' + '<i>' + [u'нет', u'да'][forceInt(record.value('active'))] + '</i>' + '<br>'
                result += u'Является внутренним: ' + '<i>' + [u'нет', u'да'][forceInt(record.value('internal'))] + '</i>' + '<br>'
                result += u'Политравма: ' + [u'нет', u'да'][forceInt(record.value('isPolyTrauma'))] + '\n'
        return result


    def getCSGInfo(self):
        CSGId = self.tblCSGList.currentItemId()
        result = ''
        if CSGId:
            db = QtGui.qApp.db
            table = db.table('CSG')
            record = db.getRecordEx(table, '*', [table['id'].eq(CSGId)])
            if record:
                result += u'Название: ' + forceString(record.value('name')) + '\n'
                result += u'Код: ' + forceString(record.value('code')) + '\n'
                result += u'Пол: ' + [u'не определено', u'мужской', u'женский'][forceInt(record.value('sex'))] + '\n'
                result += u'Возраст: ' + forceString(record.value('age')) + '\n'
                result += u'Некое доп. условие: ' + forceString(record.value('note')) + '\n'
                result += u'Активно: ' + [u'нет', u'да'][forceInt(record.value('active'))] + '\n'
                result += u'Является внутренним: ' + [u'нет', u'да'][forceInt(record.value('internal'))] + '\n'
                result += u'Политравма: ' + [u'нет', u'да'][forceInt(record.value('isPolyTrauma'))] + '\n'
        return result


    def openDb(self):
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'samson-vista', 'mesEditor')
        server = settings.value('server', QtCore.QVariant('localhost')).toString()
        port = settings.value('port', QtCore.QVariant(0)).toInt()[0]
        database = settings.value('database', QtCore.QVariant('mes')).toString()
        user = settings.value('user', QtCore.QVariant('dbuser')).toString()
        password = settings.value('password', QtCore.QVariant('dbpassword')).toString()
        connectionName = settings.value('database', QtCore.QVariant('mes')).toString()
        try:
            self.application.db = CMySqlDatabase(server, port, database, user, password, connectionName)
            self.emit(SIGNAL('dbConnectionChanged(bool)'), True)
            #QtGui.qApp.calendarInfo.load()
            #QtGui.qApp.calendarInfo.load()
            self.updateMain()
            self.tableModelCSGList = CCSGTableModel(self)
            self.tableSelectionModelCSGList = QtGui.QItemSelectionModel(self.tableModelCSGList, self)
            self.tableSelectionModelCSGList.setObjectName('tableSelectionModelCSGList')
            self.modelCSGDiagnosis = CCSGMKBModel(self)
            self.selectionModelCSGDiagnosis = QtGui.QItemSelectionModel(self.modelCSGDiagnosis, self)
            self.selectionModelCSGDiagnosis.setObjectName('selectionModelCSGDiagnosis')
            self.modelCSGService = CCSGServicesModel(self)
            self.selectionModelCSGService = QtGui.QItemSelectionModel(self.modelCSGService, self)
            self.selectionModelCSGService.setObjectName('selectionModelCSGService')
            self.tblCSGList.setModel(self.tableModelCSGList)
            self.tblCSGList.setSelectionModel(self.tableSelectionModelCSGList)
            self.tblCSGList.installEventFilter(self)
            self.tblCSGDiagnosis.setModel(self.modelCSGDiagnosis)
            self.tblCSGDiagnosis.setSelectionModel(self.selectionModelCSGDiagnosis)
            self.tblCSGService.setModel(self.modelCSGService)
            self.tblCSGService.setSelectionModel(self.selectionModelCSGService)
            self.connect(self.tableSelectionModelCSGList, SIGNAL('currentChanged(QModelIndex,QModelIndex)'),
                         self.on_tableSelectionModelCSGList_currentChanged)
            self.tblCSGList.addPopupDublicateRow()
            self.tblCSGList.addPopupDelRow()
            self.updateCSGList()
        except Exception, e:
            self.application.db = None
            QtGui.QMessageBox.critical(self,
                                            u'Произошла ошибка',
                                            unicode(e),

                       QtGui.QMessageBox.Close)
            self.on_actConnection_triggered()
            return


    def openDbSetup(self):
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'samson-vista', 'mesEditor')
        server = settings.value('server', QtCore.QVariant('localhost')).toString()
        port = settings.value('port', QtCore.QVariant(0)).toInt()[0]
        database = settings.value('database', QtCore.QVariant('mes')).toString()
        user = settings.value('user', QtCore.QVariant('dbuser')).toString()
        password = settings.value('password', QtCore.QVariant('dbpassword')).toString()
        connectionName = settings.value('database', QtCore.QVariant('mes')).toString()
        try:
            self.application.db = CMySqlDatabase(server, port, database, user, password, connectionName)
            self.emit(SIGNAL('dbConnectionChanged(bool)'), True)
            #QtGui.qApp.calendarInfo.load()
        except Exception, e:
            self.application.db = None
            QtGui.QMessageBox.critical(self,
                                            u'Произошла ошибка',
                                            unicode(e),

                       QtGui.QMessageBox.Close)
            self.on_actConnection_triggered()
            self.openDbSetup()
            return


    def openDbPostSetup(self):
        try:
            self.updateMain()
        except Exception, e:
            self.application.db = None
            QtGui.QMessageBox.critical(self,
                                            u'Произошла ошибка',
                                            unicode(e),
                       QtGui.QMessageBox.Close)
            return


    def closeDb(self):
        if self.application.db:
            connectionName = self.application.db.db.databaseName()
            self.tblCSGList.setModel(None)
            self.tblCSGDiagnosis.setModel(None)
            self.tblCSGService.setModel(None)
            del self.tableModelCSGList
            del self.modelCSGDiagnosis
            del self.modelCSGService
            self.txtCSGBrowser.setHtml('')
            self.lblCountCSG.setText(u'')
            self.application.db.db.close()
            self.application.db.close()
            self.mesModel.clear()
            self.mesModel.reset()
            self.textInfo.setHtml('')
            self.lblCount.setText(u'')
            QtSql.QSqlDatabase.removeDatabase(connectionName)
            self.application.db.db = None
            self.application.db = None
            self.emit(SIGNAL('dbConnectionChanged(bool)'), False)
            #QtGui.qApp.calendarInfo.clear()


    def updateMain(self):
        row = self.mesView.currentIndex().row()
        self.mesModel.setParam(self.application.db, self.filter)
        self.lblCount.setText(u'В списке %d записей'%self.mesModel.rowCount())
        if (not self.mesView.currentRow()) and self.mesModel.rowCount(): # такая фигня всегда при обновлении запроса к модели
            self.mesView.setCurrentRow(row if row > 0 else 0)


    def updateCSGList(self):
        row = self.tblCSGList.currentRow()
        self.tblCSGList.model().setIdList(self.setCSGList())
        self.lblCountCSG.setText(u'В списке %d записей'%self.tableModelCSGList.rowCount())
        if (not self.tblCSGList.currentRow()) and self.tableModelCSGList.rowCount():
            self.tblCSGList.setCurrentRow(row if row and row > 0 else 0)
        self.txtCSGBrowser.setHtml(self.getCSGBrowserInfo())


    def update(self, a=None, b=None):
        row = self.mesView.currentIndex().row()
        self.mes = CMesInfo(self.getCellInteger(row, self.colId))  # id
        self.mes.init(self.getCellInteger(row, self.colActive), # active
                      self.getCellInteger(row, self.colInternal), # internal
                 self.getCellInteger(row, self.colGroupId),  # group_id
                 self.getCellStr(row, self.colCode), # code
                 self.getCellStr(row, self.colName),   # name
                 self.getCellInteger(row, self.colMinDuration), # minDuration
                 self.getCellInteger(row, self.colMaxDuration), # maxDuration
                 self.getCellFloat(row, self.colAvgDuration), # avgDuration
                 self.getCellStr(row, self.colPatientModel),     # patientModel
                 self.getCellFloat(row, self.colTariff),     # tariff
                 self.getCellStr(row, self.colDescr),   # descr
                 self.getCellInteger(row, self.colKSGNorm),
                 self.getCellInteger(row, self.colPeriodicity), # periodicity
                 self.getCellInteger(row, self.colKSGId),
                 self.getCellDate(row, self.colEndDate),
                 self.getCellInteger(row, self.colPolyTrauma)
                 )
        self.textInfo.setHtml(self.getBrowserCode())

        self.modelFeaturesMKB.loadData(stmt=self.MKBQuery())
        self.tableMKB.setModel(self.modelFeaturesMKB)

        self.modelFeaturesServices.loadData(stmt=self.ServicesQuery())
        self.tableServices.setModel(self.modelFeaturesServices)

        self.modelFeaturesVisits.loadData(stmt=self.VisitsQuery())
        self.tableVisits.setModel(self.modelFeaturesVisits)

        self.modelFeaturesEquipment.loadData(stmt=self.EquipmentQuery())
        self.tableEquipment.setModel(self.modelFeaturesEquipment)

        self.modelFeaturesMedicament.loadData(stmt=self.MedicamentQuery())
        self.tableMedicament.setModel(self.modelFeaturesMedicament)

        self.modelFeaturesBlood.loadData(stmt=self.BloodQuery())
        self.tableBlood.setModel(self.modelFeaturesBlood)

        self.modelFeaturesNutrient.loadData(stmt=self.NutrientQuery())
        self.tableNutrient.setModel(self.modelFeaturesNutrient)

        self.modelFeaturesLimitedBySexAge.loadData(stmt=self.LimitedBySexAgeQuery())
        self.tableLimitedBySexAge.setModel(self.modelFeaturesLimitedBySexAge)


    def cloneCurrentRow(self):
        row = self.mesView.currentIndex().row()
        self.mesModel.cloneRow(row)


    def on_actConnection_triggered(self):
        #print 'connection!'
        dlg   = CConnectionDialog(self)
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'samson-vista', 'mesEditor')
        #dlg.setDriverName(preferences.dbDriverName)
        dlg.setServerName(settings.value('server', QtCore.QVariant('localhost')).toString())
        dlg.setServerPort(settings.value('port', QtCore.QVariant(0)).toInt()[0])
        dlg.setDatabaseName(settings.value('database', QtCore.QVariant('mes')).toString())
        dlg.setUserName(settings.value('user', QtCore.QVariant('dbuser')).toString())
        dlg.setPassword(settings.value('password', QtCore.QVariant('dbpassword')).toString())
        if dlg.exec_():
            #preferences.dbDriverName = dlg.driverName()
            settings.setValue('server', QtCore.QVariant(dlg.serverName()))
            settings.setValue('port', QtCore.QVariant(dlg.serverPort()))
            settings.setValue('database', QtCore.QVariant(dlg.databaseName()))
            settings.setValue('user', QtCore.QVariant(dlg.userName()))
            settings.setValue('password', QtCore.QVariant(dlg.password()))


    def add(self):
        if self.tabMESCSGWidget.currentIndex():
            editor = CCSGEditor(self)
            if editor.exec_() == QtGui.QDialog.Accepted:
                self.updateCSGList()
        else:
            mes = CMesInfo(0)
            editor = MesEditor(self, mes)
            if editor.exec_() == QtGui.QDialog.Accepted:
                self.updateMain()


    def edit(self):
        if self.tabMESCSGWidget.currentIndex():
            CSGId = self.tblCSGList.currentItemId()
            if CSGId:
                editor = CCSGEditor(self)
                editor.load(CSGId)
                if editor.exec_() == QtGui.QDialog.Accepted:
                    self.updateCSGList()
        else:
            editor = MesEditor(self, self.mes)
            if editor.exec_() == QtGui.QDialog.Accepted:
                self.updateMain()


    def print_(self):
        if self.tabMESCSGWidget.currentIndex():
            CSGId = self.tblCSGList.currentItemId()
            if CSGId:
                self.getCSGFullDescription(CSGId)
        else:
            view = CReportViewDialog(self)
            view.setWindowTitle(u'МЭС')
            view.setText(self.mes.getFullDescription())
            view.exec_()


    def getCSGFullDescription(self, CSGId):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'КСГ')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(u'%s'%(self.getCSGInfo()))
        cursor.insertBlock()

        model = self.tblCSGDiagnosis.model()
        colWidths  = [ self.tblCSGDiagnosis.columnWidth(i) for i in xrange(model.columnCount()-1) ]
        colWidths.insert(0,10)
        totalWidth = sum(colWidths)
        tableColumns = []
        iColNumber = False
        for iCol, colWidth in enumerate(colWidths):
            if iColNumber == False:
                tableColumns.append(('10%', [u'№'], CReportBase.AlignRight))
                iColNumber = True
            tableColumns.append(('90%', [forceString(model._cols[iCol].title())], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        for iModelRow in xrange(model.rowCount()):
            iTableRow = table.addRow()
            table.setText(iTableRow, 0, iModelRow+1)
            for iModelCol in xrange(model.columnCount()):
                index = model.createIndex(iModelRow, iModelCol)
                text = forceString(model.data(index))
                table.setText(iTableRow, iModelCol+1, text)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

        model = self.tblCSGService.model()
        colWidths  = [ self.tblCSGService.columnWidth(i) for i in xrange(model.columnCount()-1) ]
        colWidths.insert(0,10)
        totalWidth = sum(colWidths)
        tableColumns = []
        iColNumber = False
        for iCol, colWidth in enumerate(colWidths):
            widthInPercents = str(max(1, colWidth*90/totalWidth))+'%'
            if iColNumber == False:
                tableColumns.append((widthInPercents, [u'№'], CReportBase.AlignRight))
                iColNumber = True
            tableColumns.append((widthInPercents, [forceString(model._cols[iCol].title())], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        for iModelRow in xrange(model.rowCount()):
            iTableRow = table.addRow()
            table.setText(iTableRow, 0, iModelRow+1)
            for iModelCol in xrange(model.columnCount()):
                index = model.createIndex(iModelRow, iModelCol)
                text = forceString(model.data(index))
                table.setText(iTableRow, iModelCol+1, text)

        html = doc.toHtml(QByteArray('utf-8'))
        view = CReportViewDialog(self)
        view.setText(html)
        view.exec_()


    def find(self):
        if self.checkGroup.isChecked():
            self.cmbGroup.setFocus()
        elif self.checkCode.isChecked():
            self.edtCode.setFocus()
        elif self.checkName.isChecked():
            self.edtName.setFocus()
        elif self.checkMKB.isChecked():
            self.edtMKB.setFocus()
        elif self.checkMKBEx.isChecked():
            self.edtMKBEx.setFocus()
        else:
            self.checkGroup.setFocus()


    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.btnUpdate.click()
        QtGui.QMainWindow.keyPressEvent(self, e)


    def on_actAbout_triggered(self):
        global lastChangedRev
        global lastChangedDate
        try:
            from buildInfo import lastChangedRev, lastChangedDate
        except:
            lastChangedRev  = 'unknown'
            lastChangedDate = 'unknown'
        QtGui.QMessageBox.about(
            self, u'О программе "%s"'%subtitle, about % (title, lastChangedRev, lastChangedDate)
            )


    def on_actAboutQt_triggered(self):
        QtGui.QMessageBox.aboutQt(self, u'О Qt')


    def on_actrbVisitType_triggered(self):
        CRBVisitTypeList(self).exec_()


    def on_actrbBloodPreparation_triggered(self):
        CRBBloodPreparationList(self).exec_()


    def on_actrbBloodPreparationType_triggered(self):
        CRBBloodPreparationTypeList(self).exec_()


    def on_actrbEquipment_triggered(self):
        CRBEquipmentList(self).exec_()


    def on_actrbEquipmentGroup_triggered(self):
        CRBEquipmentGroupList(self).exec_()


    def on_actrbMedicament_triggered(self):
        CRBMedicamentList(self).exec_()


    def on_actrbMedicamentDosageForm_triggered(self):
        CRBMedicamentDosageFormList(self).exec_()


    def on_actrbMedicamentGroup_triggered(self):
        CRBMedicamentGroupList(self).exec_()


    def on_actrbMesGroup_triggered(self):
        CRBMesGroupList(self).exec_()


    def on_actrbNutrient_triggered(self):
        CRBNutrientList(self).exec_()


    def on_actrbNutrientGroup_triggered(self):
        CRBNutrientGroupList(self).exec_()


    def on_actrbService_triggered(self):
        CRBServiceList(self).exec_()


    def on_actrbServiceGroup_triggered(self):
        CRBServiceGroupList(self).exec_()


    def on_actrbSpeciality_triggered(self):
        CRBSpecialityList(self).exec_()


    @QtCore.pyqtSignature('')
    def on_actMesKSG_triggered(self):
        CMesKSGList(self).exec_()


    @QtCore.pyqtSignature('')
    def on_actImportXML_triggered(self):
        ImportXML(self)


    @QtCore.pyqtSignature('')
    def on_actExportXML_triggered(self):
        ExportXML(self)


    def setTableParam(self):
        map(self.mesView.hideColumn, self.hiddenColumns)

        self.mesView.setColumnWidth(self.colActive, 20)
        self.mesView.setColumnWidth(self.colGroupName, 150)
        self.mesView.setColumnWidth(self.colCode, 50)
        self.mesView.setColumnWidth(self.colName , 300)
        self.mesView.setColumnWidth(self.colAvgDuration, 90)
        self.mesView.setColumnWidth(self.colPatientModel, 140)
        self.mesView.setColumnWidth(self.colTariff, 50)
        self.mesView.setColumnWidth(self.colDescr, 300)
        self.mesView.setCurrentIndex(self.mesModel.index(0, 0))
        self.mesView.setFocus(Qt.OtherFocusReason)

        # Указываем размеры вкладок в ширину
        self.tableMKB.setColumnWidth(0, 100)
        self.tableMKB.setColumnWidth(1, 100)

        self.tableServices.setColumnWidth(0, 250)
        self.tableServices.setColumnWidth(1, 100)
        self.tableServices.setColumnWidth(2, 250)
        self.tableServices.setColumnWidth(3, 50)
        self.tableServices.setColumnWidth(4, 50)
        self.tableServices.setColumnWidth(5, 50)
        self.tableServices.setColumnWidth(6, 50)
        self.tableServices.setColumnWidth(7, 50)

        self.tableVisits.setColumnWidth(0, 200)
        self.tableVisits.setColumnWidth(1, 200)
        self.tableVisits.setColumnWidth(2, 100)
        self.tableVisits.setColumnWidth(3, 70)
        self.tableVisits.setColumnWidth(4, 50)
        self.tableVisits.setColumnWidth(5, 100)

        self.tableEquipment.setColumnWidth(0, 100)
        self.tableEquipment.setColumnWidth(1, 500)
        self.tableEquipment.setColumnWidth(2, 50)
        self.tableEquipment.setColumnWidth(3, 50)

        self.tableMedicament.setColumnWidth(0, 80)
        self.tableMedicament.setColumnWidth(1, 100)
        self.tableMedicament.setColumnWidth(2, 150)
        self.tableMedicament.setColumnWidth(3, 100)
        self.tableMedicament.setColumnWidth(4, 100)
        self.tableMedicament.setColumnWidth(5, 100)
        self.tableMedicament.setColumnWidth(6, 100)
        self.tableMedicament.setColumnWidth(7, 100)
        self.tableMedicament.setColumnWidth(8, 150)
        self.tableMedicament.setColumnWidth(9, 50)
        self.tableMedicament.setColumnWidth(10, 50)

        self.tableBlood.setColumnWidth(0, 100)
        self.tableBlood.setColumnWidth(2, 100)
        self.tableBlood.setColumnWidth(3, 100)
        self.tableBlood.setColumnWidth(4, 100)
        self.tableBlood.setColumnWidth(5, 100)

        self.tableNutrient.setColumnWidth(0, 100)
        self.tableNutrient.setColumnWidth(1, 250)
        self.tableNutrient.setColumnWidth(2, 100)
        self.tableNutrient.setColumnWidth(3, 100)
        self.tableNutrient.setColumnWidth(4, 100)
        self.tableNutrient.setColumnWidth(5, 100)

        self.tableLimitedBySexAge.resizeColumnToContents(0)
        self.tableLimitedBySexAge.resizeColumnToContents(1)
        self.tableLimitedBySexAge.resizeColumnToContents(2)


    def closeEvent(self, event):
        if QtGui.qApp.db:
            QtGui.qApp.db.close()
        QtGui.QMainWindow.closeEvent(self, event)


class MesEditorApp(QtGui.QApplication):
    __pyqtSignals__ = ('dbConnectionChanged(bool)'
                      )
    def __init__(self, args):
        QtGui.QApplication.__init__(self, args)
        self.preferences = CPreferences('MesEditor.ini')
        self.preferences.load()
        self.appPreferences = CPreferences('S11App.ini')
        self.disableLock = True
        self._highlightRedDate = None
        self._highlightInvalidDate = None
        self.calendarInfo = CCalendarInfo(self)
        self.mainWindow = mainWin(self)
        self.logDir = os.path.join(unicode(QDir.toNativeSeparators(QDir.homePath())), '.samson-vista')

    def getGlobalPreference(self, code):
        return None

    def userHasRight(self, action):
        u'Мы ничего страшного не делаем, поэтому пользователь может ВСЁ!'
        return True

    def documentEditor(self):
        return ''

    def startProgressBar(self, steps, format=u'%v из %m'):
        pass

    def stepProgressBar(self, step=1):
        pass

    def stopProgressBar(self):
        pass

    def enableFastPrint(self):
#        return True
        return forceBool(self.appPreferences.appPrefs.get('enableFastPrint', False))

    def setWaitCursor(self):
        self.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))


    def highlightRedDate(self):
        if self._highlightRedDate is None:
            self._highlightRedDate = forceBool(QtGui.qApp.preferences.appPrefs.get('highlightRedDate', False))
        return self._highlightRedDate


    def highlightInvalidDate(self):
        if self._highlightInvalidDate is None:
            self._highlightInvalidDate = forceBool(QtGui.qApp.preferences.appPrefs.get('highlightInvalidDate', False))
        return self._highlightInvalidDate


    def call(self, widget, func, params = ()):
        try:
            return True, func(*params)
        except IOError, e:
            msg=''
            if hasattr(e, 'filename'):
                msg = u'%s:\n[Errno %s] %s' % (e.filename, e.errno, anyToUnicode(e.strerror))
            else:
                msg = u'[Errno %s] %s' % (e.errno, anyToUnicode(e.strerror))
            QtGui.QMessageBox.critical(widget,
                u'Произошла ошибка ввода-вывода', msg, QtGui.QMessageBox.Close)
        except Exception, e:
            #self.logCurrentException()
            widget = widget or self.activeModalWidget() or self.mainWindow
            QtGui.QMessageBox.critical( widget,
                                        u'Произошла ошибка',
                                        unicode(e),
                                        QtGui.QMessageBox.Close)
        return False, None


    def log(self, title, message, stack=None):
        try:
            if not os.path.exists(self.logDir):
                os.makedirs(self.logDir)
            logFile = os.path.join(self.logDir, 'error.log')
            timeString = unicode(QDateTime.currentDateTime().toString(Qt.SystemLocaleDate))
            logString = u'%s\n%s: %s(%s)\n' % ('='*72, timeString, title, message)
            if stack:
                try:
                    logString += ''.join(traceback.format_list(stack)).decode('utf-8') + '\n'
                except:
                    logString += 'stack lost\n'
            file = codecs.open(logFile, mode='a', encoding=locale.getpreferredencoding())
            file.write(logString)
            file.close()
        except:
            pass


    def logException(self, exceptionType, exceptionValue, exceptionTraceback):
        title = repr(exceptionType)
        message = anyToUnicode(exceptionValue)
        self.log(title, message, traceback.extract_tb(exceptionTraceback))
        sys.__excepthook__(exceptionType, exceptionValue, exceptionTraceback)


    def logCurrentException(self):
        self.logException(*sys.exc_info())


if __name__ == "__main__":
    QtGui.qApp = MesEditorApp(sys.argv)
    try:
        #mw=mainWin()
        #mw.show()
        #QtGui.qApp.mainWindow.show()
        QtGui.qApp.exec_()
        QtGui.qApp.preferences.save()
    except Exception, e:
        QtGui.QMessageBox.critical( None,
                                    'error',
                                    unicode(e),
                                    QtGui.QMessageBox.Close)
    mw = None
    QtGui.qApp = None
