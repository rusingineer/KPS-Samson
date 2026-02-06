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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QObject, QRegExp, pyqtSignature, SIGNAL
from PyQt4.QtGui import QFont

from library.AgeSelector import checkAgeSelectorSyntax
from library.crbcombobox import CRBComboBox
from library.DialogBase  import CDialogBase
from library.IdentificationModel import checkIdentification
from library.InDocTable  import CInDocTableModel, CBoolInDocTableCol, CCodeNameInDocTableCol, CEnumInDocTableCol, CInDocTableCol, CRBInDocTableCol
from library.interchange import getCheckBoxValue, getComboBoxValue, getDateEditValue, getDoubleBoxValue, getLineEditValue, getRBComboBoxValue, getTextEditValue, setCheckBoxValue, setComboBoxValue, setDateEditValue, setDoubleBoxValue, setLineEditValue, setRBComboBoxValue, setTextEditValue
from library.ItemEditorDialogWithIdentification import CItemEditorDialogWithIdentification
from library.ItemsListDialog import CItemsSplitListDialogEx, CItemEditorBaseDialog
from library.TableModel  import CBoolCol, CEnumCol, CRefBookCol, CTextCol, CTableModel, CDateCol
from library.Utils import addDots, addDotsEx, forceDate, forceRef, forceString, forceStringEx, toVariant

from Exchange.Cimport    import Cimport

from RefBooks.Tables     import rbCode, rbName, rbService, rbServiceGroup

from Ui_RBServiceEditor        import Ui_ItemEditorDialog
from Ui_ServiceFilterDialog    import Ui_ServiceFilterDialog
from Ui_SynchronizeActionTypes import Ui_SyncDialog

import synchronizeActionTypes_sql
import synchronizeActionTypes_create_sql


SexList = ('', u'М', u'Ж')


def isComplexService(code):
    u"""Услуга сложная, если её код начинается с В или она имеет подчинённые"""
    if unicode(code).startswith(u'В') or unicode(code).startswith('B'):
        return True
    result = QtGui.qApp.db.query("""SELECT * from rbService, rbService_Contents
                                                        where rbService_Contents.master_id = rbService.id
                                                        and rbService.code = '%s'"""%code)
    return result.size() > 0


class CRBServiceList(CItemsSplitListDialogEx):
    def __init__(self, parent, forSelect=False, uniqueCode=True):
        CItemsSplitListDialogEx.__init__(self, parent,
            rbService,
            [
            CRefBookCol(u'Группа', ['group_id'], rbServiceGroup, 20, showFields=CRBComboBox.showName),
            CTextCol(u'Код',                 [rbCode], 20),
            CTextCol(u'Наименование',        [rbName], 50),
            CBoolCol(u'Унаследовано из ЕИС', ['eisLegacy'], 10),
            CTextCol(u'ИНФИС код',           ['infis'], 20),
            CEnumCol(u'Лицензирование',      ['license'], [u'не требуется', u'требуется лицензия', u'требуется персональный сертификат'], 30),
            CDateCol(u'Дата начала', ['begDate'], 20),
            CDateCol(u'Дата окончания', ['endDate'], 20)
            ],
            [rbCode, rbName],
            'rbService_Contents',
            [
            CRefBookCol(u'Код', ['service_id'], rbService, 20, showFields=CRBComboBox.showCode),
            CRefBookCol(u'Наименование', ['service_id'], rbService, 50, showFields=CRBComboBox.showName),
            CBoolCol(u'Обязательно', ['required'], 10),
            ],
            'master_id', 'service_id', forSelect=forSelect, filterClass=CServiceFilterDialog)
        self.setWindowTitleEx(u'Услуги')
        self.addPopupAction('actImport2ActionType', u'Преобразовать выделенные услуги в типы действий', self.importSelected2ActionType)


    def getItemEditor(self):
        return CRBServiceEditor(self)


    def select(self, props):
        table = self.model.table()
        cond = []

        group = props.get('group', None)
        if group:
            cond.append(table['group_id'].eq(group))

        section = props.get('section', 0)
        type = props.get('type', 0)
        class_ = props.get('class', 0)
        if section:
            sectionRecord = QtGui.qApp.db.getRecord('rbServiceSection', ['code'], section)
            sectionCode = forceString(sectionRecord.value('code'))
            cond.append("""left(rbService.code, %d) = '%s'"""%(len(sectionCode), sectionCode))

            if type:
                cond.append("""(select code
                            from rbServiceType
                            where id = %s)
                            = substr(rbService.code from %d for 2)"""%(type, len(sectionCode)+1))

            if class_:
                cond.append("""rbService.code like concat('___.',
            (select code
                            from rbServiceClass
                            where id = %s), '%%')
                            """%class_)

        code= props.get('code', '')
        if code:
            cond.append(table['code'].likeBinary(addDots(code)))

        name = props.get('name', '')
        if name:
            cond.append(table['name'].like(addDotsEx(name)))

        note = props.get('note', '')
        if note:
            cond.append(table['note'].like(addDotsEx(note)))

        flagEIS = props.get('EIS', Qt.PartiallyChecked)
        if flagEIS != Qt.PartiallyChecked:
            cond.append(table['eisLegacy'].eq(flagEIS != Qt.Unchecked))

        flagNomenclature = props.get('nomenclature', Qt.PartiallyChecked)
        if flagNomenclature != Qt.PartiallyChecked:
            cond.append(table['nomenclatureLegacy'].eq(flagNomenclature!= Qt.Unchecked))

        createBegDate = props.get('createBegDate',  QDate())
        if createBegDate:
            cond.append(table['createDatetime'].dateGe(createBegDate))

        createEndDate = props.get('createEndDate',  QDate())
        if createEndDate:
            cond.append(table['createDatetime'].dateLe(createEndDate))

        begDate = props.get('begDate',  QDate())
        if begDate:
            cond.append(table['begDate'].ge(forceString(begDate.toString(Qt.ISODate))))

        endDate = props.get('endDate',  QDate())
        if endDate:
            cond.append(table['endDate'].le(forceString(endDate.toString(Qt.ISODate))))

        flagCloseServices = props.get('closeServices', 2)
        if flagCloseServices:
            cond.append(table['endDate'].ge(forceString(QDate.currentDate().toString(Qt.ISODate))))

        return QtGui.qApp.db.getIdList(table.name(),
                           'id',
                           cond,
                           self.order)

    def setup(self, cols, tableName, order, forSelect=False, filterClass=None):
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.forSelect = forSelect
        self.filterClass = filterClass
        self.props = {}
        self.order = order
        self.addModels('', CServiceModel(self, cols))
        self.model.idFieldName = self.idFieldName
        self.model.setTable(tableName, recordCacheCapacity=QtGui.qApp.db.getCount(tableName, 'id'))
        self.setModels(self.tblItems, self.model, self.selectionModel)
        #        self.createPopupMenu(self.tblItems)
        self.btnSelect.setEnabled(self.forSelect)
        self.btnSelect.setVisible(self.forSelect)
        self.btnSelect.setDefault(self.forSelect)
        self.btnFilter.setEnabled(self.forSelect and bool(self.filterClass))
        self.btnFilter.setEnabled(bool(self.filterClass))
        self.btnFilter.setVisible(bool(self.filterClass))
        self.btnEdit.setDefault(not self.forSelect)
        self.tblItems.setFocus(Qt.OtherFocusReason)

        self.btnNew.setShortcut('F9')
        self.btnEdit.setShortcut('F4')
        self.btnPrint.setShortcut('F6')
        QObject.connect(
            self.tblItems.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)


    def copyInternals(self, newItemId, oldItemId):
        db = QtGui.qApp.db
        tableServiceContents = db.table('rbService_Contents')
        records = db.getRecordList(
            tableServiceContents, '*',
            tableServiceContents['master_id'].eq(oldItemId))
        for record in records:
            record.setNull('id')
            record.setValue('master_id', toVariant(newItemId))
            db.insertRecord(tableServiceContents, record)

        tableServiceProfile = db.table('rbService_Profile')
        records = db.getRecordList(
            tableServiceProfile, '*',
            tableServiceProfile['master_id'].eq(oldItemId))
        for record in records:
            record.setNull('id')
            record.setValue('master_id', toVariant(newItemId))
            db.insertRecord(tableServiceProfile, record)


    def importSelected2ActionType(self):
        selectedIdList = self.tblItems.selectedItemIdList()
        CSynchronizeActionTypesDialog(self, selectedIdList).exec_()


#
# ##########################################################################
#


class CSynchronizeActionTypesDialog(CDialogBase, Cimport, Ui_SyncDialog):
    @pyqtSignature('')
    def on_btnImport_clicked(self): Cimport.on_btnImport_clicked(self)
    @pyqtSignature('')
    def on_btnClose_clicked(self): Cimport.on_btnClose_clicked(self)

    def __init__(self, parent, services):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        Cimport.__init__(self)
        self.services = services
        query = """
                SELECT concat(code, ' - ', name)
                FROM rbService
                WHERE id IN (%s)
                """%', '.join([str(id) for id in self.services])
        result = QtGui.qApp.db.query(query)
        while result.next():
            self.serviceList.addItem(result.record().value(0).toString())


    def startImport(self):
        db = QtGui.qApp.db
        error = self.runScript(synchronizeActionTypes_create_sql.COMMAND.split('\n'))
        if not error:
            self.log.append(u'Определение номенклатурных услуг...')
            db.query("""    INSERT IGNORE INTO tmpService2ActionType(code, name, parentCode, `level`, `class`)
                            SELECT  rbService.code AS code,
                                    rbService.name AS name,
                                    NULL AS `parentCode`,
                                    0 AS `level`,
                                    rbServiceType.`class` AS `class`
                            FROM rbService
                            LEFT JOIN rbServiceType ON rbServiceType.section = LEFT(rbService.code, 1) AND rbServiceType.code = SUBSTR(rbService.code FROM 2 FOR 2)
                            WHERE rbService.nomenclatureLegacy = 1
                            AND rbService.id IN (%s)
                          """%', '.join([str(id) for id in self.services]))
            self.log.append(u'Определение прочих услуг...')
            db.query("""    INSERT IGNORE INTO tmpService2ActionType(code, name, parentCode, `level`, `class`)
                            SELECT  rbService.code AS code,
                                    rbService.name AS name,
                                    '-' AS `parentCode`,
                                    2 AS `level`,
                                    3 AS `class`
                            FROM rbService
                            WHERE rbService.nomenclatureLegacy = 0
                            AND rbService.id IN (%s)
                          """%', '.join([str(id) for id in self.services]))
            error = self.runScript(synchronizeActionTypes_sql.COMMAND.split('\n'), {'person_id':QtGui.qApp.userId,
         'updateNames': int(self.checkUpdateNames.isChecked()),
         'compareDeleted': int(self.checkCompareDeleted.isChecked())})
        if error is not None:
            QtGui.QMessageBox.warning(self, u'Импорт услуг',
                        u'Ошибка при импорте услуг:\n%s.'%error.text())
            self.log.append(unicode(error.text()))


#
# ##########################################################################
#

class CServiceContentsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbService_Contents', 'id', 'master_id', parent)
        self.addCol(CCodeNameInDocTableCol(u'Услуга', 'service_id', 40, rbService, preferredWidth = 100))
        self.addCol(CBoolInDocTableCol(u'Обязательно', 'required', 10))


class CMedicalAidProfilesModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbService_Profile', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(   u'Специальность',  'speciality_id', 20, 'rbSpeciality', showFields = CRBComboBox.showName))
        self.addCol(CEnumInDocTableCol( u'Пол',            'sex',  5, SexList))
        self.addCol(CInDocTableCol(     u'Возраст',        'age',  12))
        self.addCol(CInDocTableCol(     u'Код МКБ',        'mkbRegExp', 12))
        self.addCol(CRBInDocTableCol(   u'Профиль',        'medicalAidProfile_id', 20, 'rbMedicalAidProfile', showFields = CRBComboBox.showName))
        self.addCol(CRBInDocTableCol(   u'Вид',            'medicalAidKind_id',    20, 'rbMedicalAidKind', showFields = CRBComboBox.showName))
        self.addCol(CRBInDocTableCol(   u'Тип',            'medicalAidType_id',    20, 'rbMedicalAidType', showFields = CRBComboBox.showName))


#
# ##########################################################################
#

class CRBServiceEditor(Ui_ItemEditorDialog, CItemEditorDialogWithIdentification):
    def __init__(self,  parent):
        CItemEditorDialogWithIdentification.__init__(self, parent, rbService)
        self.setWindowTitleEx(u'Услуга')
        self.setupDirtyCather()


    def preSetupUi(self):
        CItemEditorDialogWithIdentification.preSetupUi(self)
        self.addModels('Services', CServiceContentsModel(self))
        self.addModels('MedicalAidProfiles', CMedicalAidProfilesModel(self))


    def postSetupUi(self):
        CItemEditorDialogWithIdentification.postSetupUi(self)
        self.cmbServiceGroup.setTable('rbServiceGroup')
        self.cmbMedicalAidProfile.setTable('rbMedicalAidProfile')
        self.cmbMedicalAidKind.setTable('rbMedicalAidKind')
        self.cmbMedicalAidType.setTable('rbMedicalAidType')
        self.setModels(self.tblServices, self.modelServices, self.selectionModelServices)
        self.setModels(self.tblMedicalAidProfiles, self.modelMedicalAidProfiles, self.selectionModelMedicalAidProfiles)
        self.tblMedicalAidProfiles.addMoveRow()
        self.tblMedicalAidProfiles.addPopupDelRow()
        self.tblServices.addPopupDuplicateCurrentRow()
        self.tblServices.addPopupDuplicateSelectRows()
        self.tblServices.addPopupDelRow()


    def setRecord(self, record):
        # здесь к сожалению нельзя вызвать метод базового класса,
        # так как кто-то решил что длинное название требует другого редактора...
        #CItemEditorDialogWithIdentification.setRecord(self, record)

        CItemEditorBaseDialog.setRecord(self, record)
        setRBComboBoxValue(self.cmbServiceGroup, record, 'group_id')
        setLineEditValue(self.edtCode, record, rbCode)
        setTextEditValue(self.edtName, record, rbName)
        setCheckBoxValue(self.chkEisLegacy, record, 'eisLegacy')
        setCheckBoxValue(self.chkNomenclatureLegacy, record, 'nomenclatureLegacy')
        setComboBoxValue(self.cmbLicense, record, 'license')
        setLineEditValue(self.edtInfis, record, 'infis')
        setDateEditValue(self.edtBegDate, record, 'begDate')
        setDateEditValue(self.edtEndDate, record, 'endDate')
        setDoubleBoxValue(self.edtUetAdultDoctor,           record, 'adultUetDoctor')
        setDoubleBoxValue(self.edtUetChildDoctor,           record, 'childUetDoctor')
        setDoubleBoxValue(self.edtUetAdultAvarageMedWorker, record, 'adultUetAverageMedWorker')
        setDoubleBoxValue(self.edtUetChildAvarageMedWorker, record, 'childUetAverageMedWorker')
        setLineEditValue(self.edtNote, record, 'note')
        setDoubleBoxValue(self.edtQualityLevel,             record, 'qualityLevel')
        setDoubleBoxValue(self.edtSuperviseComplexityFactor,record, 'superviseComplexityFactor')
        self.modelServices.loadItems(self.itemId())
        setRBComboBoxValue(self.cmbMedicalAidProfile, record, 'medicalAidProfile_id')
        setRBComboBoxValue(self.cmbMedicalAidKind,    record, 'medicalAidKind_id')
        setRBComboBoxValue(self.cmbMedicalAidType,    record, 'medicalAidType_id')
        self.modelMedicalAidProfiles.loadItems(self.itemId())
        # см. выше :(
        self.modelIdentification.loadItems(self.itemId())


    def getRecord(self):
        # здесь к сожалению нельзя вызвать метод базового класса,
        # так как кто-то решил что длинное название требует другого редактора...
        #record = CItemEditorDialogWithIdentification.getRecord(self)
        record = CItemEditorBaseDialog.getRecord(self)
        getRBComboBoxValue(self.cmbServiceGroup, record, 'group_id')
        getLineEditValue(self.edtCode, record, rbCode)
        getTextEditValue(self.edtName, record, rbName)
        getCheckBoxValue(self.chkEisLegacy, record, 'eisLegacy')
        getCheckBoxValue(self.chkNomenclatureLegacy, record, 'nomenclatureLegacy')
        getComboBoxValue(self.cmbLicense, record, 'license')
        getLineEditValue(self.edtInfis, record, 'infis')
        getDateEditValue(self.edtBegDate, record, 'begDate')
        getDateEditValue(self.edtEndDate, record, 'endDate')
        getDoubleBoxValue(self.edtUetAdultDoctor,           record, 'adultUetDoctor')
        getDoubleBoxValue(self.edtUetChildDoctor,           record, 'childUetDoctor')
        getDoubleBoxValue(self.edtUetAdultAvarageMedWorker, record, 'adultUetAverageMedWorker')
        getDoubleBoxValue(self.edtUetChildAvarageMedWorker, record, 'childUetAverageMedWorker')
        getLineEditValue(self.edtNote, record, 'note')
        getDoubleBoxValue(self.edtQualityLevel, record, 'qualityLevel')
        getDoubleBoxValue(self.edtSuperviseComplexityFactor,  record, 'superviseComplexityFactor')
        getRBComboBoxValue(self.cmbMedicalAidProfile, record, 'medicalAidProfile_id')
        getRBComboBoxValue(self.cmbMedicalAidKind,    record, 'medicalAidKind_id')
        getRBComboBoxValue(self.cmbMedicalAidType, record, 'medicalAidType_id')
        return record


    def saveInternals(self, id):
        CItemEditorDialogWithIdentification.saveInternals(self, id)
        self.modelServices.saveItems(id)
        self.modelMedicalAidProfiles.saveItems(id)


    def checkDataEntered(self):
        # здесь к сожалению нельзя вызвать метод базового класса,
        # так как кто-то решил что длинное название требует другого редактора...
        #result = CItemEditorDialogWithIdentification.checkDataEntered(self)
        #result = result and self.checkMedicalAidProfiles()

        result = True
        code    = forceStringEx(self.edtCode.text())
        name    = forceStringEx(self.edtName.toPlainText())
        result = result and (code or self.checkInputMessage(u'код', False, self.edtCode))
        result = result and (name or self.checkInputMessage(u'наименование', False, self.edtName))
        result = result and self.checkMedicalAidProfiles()
        result = result and checkIdentification(self, self.tblIdentification)
        return result


    def checkMedicalAidProfiles(self):
        result = True
        for i, item in enumerate(self.modelMedicalAidProfiles.items()):
            age = forceString(item.value('age'))
            mkbRegExp = forceString(item.value('mkbRegExp'))
            mkbRegExpIsValid = not mkbRegExp or QRegExp(mkbRegExp).isValid()
            profileId = forceRef(item.value('medicalAidProfile_id'))
            result = result and (checkAgeSelectorSyntax(age) or self.checkValueMessage(u'Диапазон возрастов указан неверно', False, self.tblMedicalAidProfiles, i, 1))
            result = result and (mkbRegExpIsValid or self.checkValueMessage(u'Регулярное выражение кода МКБ указано неверно', False, self.tblMedicalAidProfiles, i, 2))
            result = result and (profileId or self.checkInputMessage(u'профиль', False, self.tblMedicalAidProfiles, i, 3))
            if not result:
                break
        return  result


#
# ##########################################################################
#


class CServiceFilterDialog(QtGui.QDialog, Ui_ServiceFilterDialog):
    def __init__(self,  parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbServiceGroup.setTable('rbServiceGroup')
        self.cmbSection.setTable('rbServiceSection')
        self.cmbSection.setFilter(order='id') # чтобы русские А и В не шли после D и F
        self.cmbType.setTable('rbServiceType')
        self.cmbClass.setTable('rbServiceClass')
        self.edtBegDate.canBeEmpty(True)
        self.edtEndDate.canBeEmpty(True)
        self.edtCreatePeriodBegDate.canBeEmpty(True)
        self.edtCreatePeriodEndDate.canBeEmpty(True)
        self.edtCode.setFocus(Qt.ShortcutFocusReason)
        QObject.connect(self.cmbSection, SIGNAL('currentIndexChanged(int)'), self.on_cmbSection_currentIndexChanged)
        self.updateTypesClasses()


    def setProps(self,  props):
        self.cmbServiceGroup.setValue(props.get('group', 0))
        self.cmbSection.setValue(props.get('section', 0))
        self.cmbType.setValue(props.get('type', 0))
        self.cmbClass.setValue(props.get('class', 0))
        self.edtCode.setText(props.get('code', ''))
        self.edtName.setText(props.get('name', ''))
        self.edtNote.setText(props.get('note', ''))
        self.chkEIS.setCheckState(props.get('EIS', Qt.PartiallyChecked))
        self.chkNomenclature.setCheckState(props.get('nomenclature', Qt.PartiallyChecked))
        self.chkCloseServices.setCheckState(props.get('сloseServices', 2))
        self.edtBegDate.setDate(props.get('begDate', QDate()))
        self.edtEndDate.setDate(props.get('endDate', QDate()))
        self.edtCreatePeriodBegDate.setDate(props.get('createBegDate', QDate()))
        self.edtCreatePeriodEndDate.setDate(props.get('createEndDate', QDate()))


    def props(self):
        result = {'group'  : forceRef(self.cmbServiceGroup.value()),
                  'section': forceRef(self.cmbSection.value()),
                  'type'   : forceRef(self.cmbType.value()),
                  'class'  : forceRef(self.cmbClass.value()),
                  'code'   : forceStringEx(self.edtCode.text()),
                  'name'   : forceStringEx(self.edtName.text()),
                  'note'   : forceStringEx(self.edtNote.text()),
                  'EIS'    : self.chkEIS.checkState(),
                  'nomenclature': self.chkNomenclature.checkState(),
                  'begDate': forceDate(self.edtBegDate.date()),
                  'endDate': forceDate(self.edtEndDate.date()),
                  'createBegDate': forceDate(self.edtCreatePeriodBegDate.date()),
                  'createEndDate': forceDate(self.edtCreatePeriodEndDate.date()),
                  'closeServices': self.chkCloseServices.checkState()
                 }
        return result


    def updateTypesClasses(self):
        code = self.cmbSection.code()
        if code and code != "0":
            self.edtCode.setText(code)
            self.cmbType.setEnabled(True)
            self.cmbType.setFilter('section="%s"'%code)
            if code in (u'А', u'В'):
                self.cmbClass.setEnabled(True)
                self.cmbClass.setFilter('section="%s"'%code)
            else:
                self.cmbClass.setEnabled(False)
        else:
            self.cmbType.setValue(0)
            self.cmbType.setEnabled(False)
            self.cmbClass.setValue(0)
            self.cmbClass.setEnabled(False)


    @pyqtSignature('')
    def on_cmbSection_currentIndexChanged(self):
        self.updateTypesClasses()

class CServiceModel(CTableModel):
    def __init__(self, parent, cols):
        CTableModel.__init__(self, parent, cols)
        self._expiredServices = set()



    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        record = self.getRecordByRow(row)
        endDate = forceDate(record.value('endDate'))
        if role == Qt.ToolTipRole:
            if endDate:
                if endDate <= QDate.currentDate():
                    return u"Данная услуга не является актуальной"
                else:
                    return u""

        if role == Qt.FontRole:
            if endDate:
                font = QFont()
                if endDate <= QDate.currentDate():
                    font.setItalic(True)
                    font.setBold(True)
                    return font
                else:
                    return font

        return CTableModel.data(self, index, role)
