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

from library.InDocTable import CInDocTableModel, CIntInDocTableCol, CEnumInDocTableCol, CCodeNameInDocTableCol, \
    CFloatInDocTableCol, CBoolInDocTableCol, CAgeInDocTableCol, CInDocTableCol, CDateInDocTableCol, CRBInDocTableCol, \
    CCodeRefInDocTableCol
from library.ItemsListDialog import CItemEditorBaseDialog
from library.Utils import forceString, forceDate, forceRef

from Ui_Editor import Ui_MESEditor


class CMKBModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'MES_mkb', 'id', 'master_id', parent)
        self.__parent = parent
        self.addCol(CMKBInDocTableCol(u'Диагноз', 'mkb', 10)).setSortable(True)
        self.addCol(CMKBInDocTableCol(u'Доп. диагноз', 'mkbEx', 10)).setSortable(True)
        self.addCol(CMKBInDocTableCol(u'Соп. диагноз', 'mkb2', 10)).setSortable(True)
        self.addCol(CMKBInDocTableCol(u'Диагноз осложнения', 'mkb3', 10)).setSortable(True)
        self.addCol(CIntInDocTableCol(u'Группировка', 'groupingMKB', 10)).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Сочетаемость', 'blendingMKB', 10, [u'основной и дополнительный', u'основной', u'дополнительный'])).setSortable(True)
        QtCore.QObject.connect(self, QtCore.SIGNAL('dataChanged(const QModelIndex&, const QModelIndex&)'), self.updateDiagnosis)


    def cellReadOnly(self, index):
        return index.column() == 2


    def updateDiagnosis(self, lt=None, rb=None):
        if lt and lt.column() > 1:
            return
        if not checkMKBTable():
            return
        for i in xrange(self.rowCount()-1):
            code = forceString(self.data(self.index(i, 0)))
            name = getMKBName(code)


class CServicesModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'MES_service', 'id', 'master_id', parent)
        self.__parent = parent
        self.addCol(CCodeNameInDocTableCol(u'Услуга', 'service_id', 100, 'mrbService', filter='deleted=0')).setSortable(True)
        self.addCol(CIntInDocTableCol(u'СК', 'averageQnt', 10, low=0, high=1000)).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'ЧП', 'necessity', 10, precision=2)).setSortable(True)
        self.addCol(CIntInDocTableCol(u'Группа', 'groupCode', 10, low=0, high=10000)).setSortable(True)
        self.addCol(CBoolInDocTableCol(u'Объединять', 'binding', 10)).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Пол', 'sex', 4, [u'', u'М', u'Ж'])).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Единица С', 'begAgeUnit', 6, [u'', u'Д', u'Н', u'М', u'Г'])).setSortable(True)
        self.addCol(CAgeInDocTableCol(u'Минимальный возраст', 'minimumAge', 10, high=400)).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Единица ПО', 'endAgeUnit', 6, [u'', u'Д', u'Н', u'М', u'Г'])).setSortable(True)
        self.addCol(CAgeInDocTableCol(u'Максимальный возраст', 'maximumAge', 10, high=400)).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Период контроля', 'controlPeriod', 4, [u'Дата случая', u'Конец года случая', u'Конец предыдущего случаю года'])).setSortable(True)
        self.addCol(CInDocTableCol(u'Доп. критерий', 'krit', 10)).setSortable(True)
        self.addCol(CIntInDocTableCol(u'мин. фракций', 'minFr', 10, low=0, high=99)).setSortable(True)
        self.addCol(CIntInDocTableCol(u'макс. фракций', 'maxFr', 10, low=0, high=99)).setSortable(True)
        self.addCol(CDateInDocTableCol(u'Дата начала', 'begDate', 15, canBeEmpty=True))
        self.addCol(CDateInDocTableCol(u'Дата окончания', 'endDate', 15, canBeEmpty=True))



class CVisitsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'MES_visit', 'id', 'master_id', parent)
        self.__parent = parent
        self.addCol(CRBInDocTableCol(u'Тип визита', 'visitType_id', 50, 'mrbVisitType')).setSortable(True)
        self.addCol(CCodeNameInDocTableCol(u'Специальность', 'speciality_id', 50, 'mrbSpeciality', filter='deleted=0')).setSortable(True)
        self.addCol(CCodeRefInDocTableCol(u'Услуга', 'serviceCode', 30, 'mrbService')).setSortable(True)
        self.addCol(CInDocTableCol(u'Доп. код', 'additionalServiceCode', 30)).setSortable(True)
        self.addCol(CInDocTableCol(u'Альтернативный доп. код', 'altAdditionalServiceCode', 30)).setSortable(True)
        self.addCol(CIntInDocTableCol(u'Группировка', 'groupCode', 10, low=1, high=100)).setSortable(True)
        self.addCol(CIntInDocTableCol(u'СК', 'averageQnt', 10, low=0, high=1000)).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Пол', 'sex', 4, [u'', u'М', u'Ж'])).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Единица С', 'begAgeUnit', 6, [u'', u'Д', u'Н', u'М', u'Г'])).setSortable(True)
        self.addCol(CAgeInDocTableCol(u'Минимальный возраст', 'minimumAge', 10, high=400)).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Единица ПО', 'endAgeUnit', 6, [u'', u'Д', u'Н', u'М', u'Г'])).setSortable(True)
        self.addCol(CAgeInDocTableCol(u'Максимальный возраст', 'maximumAge', 10, high=400)).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Период контроля', 'controlPeriod', 4, [u'Дата случая', u'Конец года случая', u'Конец предыдущего случаю года'])).setSortable(True)


class CEquipmentModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'MES_equipment', 'id', 'master_id', parent)
        self.__parent = parent
        self.addCol(CCodeNameInDocTableCol(u'Оборудование', 'equipment_id', 100, 'mrbEquipment', preferredWidth = 100, filter='deleted=0')).setSortable(True)
        self.addCol(CIntInDocTableCol(u'СК', 'averageQnt', 10, low=0, high=1000)).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'ЧП', 'necessity', 10, precision=2)).setSortable(True)


class CMedicamentModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'MES_medicament', 'id', 'master_id', parent)
        self.__parent = parent
        self.addCol(CCodeRefInDocTableCol(u'Медикамент', 'medicamentCode', 30, 'mrbMedicament', filter='deleted=0')).setSortable(True)
        self.addCol(CInDocTableCol(u'Дозировка', 'dosage', 30)).setSortable(True)
        self.addCol(CRBInDocTableCol(u'Лекарственная форма', 'dosageForm_id', 100, 'mrbMedicamentDosageForm', preferredWidth = 100, filter='deleted=0')).setSortable(True)
        self.addCol(CIntInDocTableCol(u'СЧЕ', 'averageQnt', 10, low=0, high=1000)).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'ЧН', 'necessity', 10, precision=2)).setSortable(True)


class CBloodModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'MES_bloodPreparation', 'id', 'master_id', parent)
        self.__parent = parent
        self.addCol(CRBInDocTableCol(u'Препарат крови', 'preparation_id', 100, 'mrbBloodPreparation', preferredWidth = 100, filter='deleted=0')).setSortable(True)
        self.addCol(CIntInDocTableCol(u'СК', 'averageQnt', 10, low=0, high=1000)).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'ЧП', 'necessity', 10, precision=2)).setSortable(True)


class CNutrientModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'MES_nutrient', 'id', 'master_id', parent)
        self.__parent = parent
        self.addCol(CCodeNameInDocTableCol(u'Питательное средство', 'nutrient_id', 100, 'mrbNutrient', preferredWidth = 100, filter='deleted=0')).setSortable(True)
        self.addCol(CIntInDocTableCol(u'СК', 'averageQnt', 10, low=0, high=1000)).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'ЧП', 'necessity', 10, precision=2)).setSortable(True)


class CLimitedBySexAgeModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'MES_limitedBySexAge', 'id', 'master_id', parent)
        self.__parent = parent
        self.addCol(CEnumInDocTableCol(u'Пол', 'sex', 4, [u'', u'М', u'Ж'])).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Единица С', 'begAgeUnit', 6, [u'', u'Д', u'Н', u'М', u'Г'])).setSortable(True)
        self.addCol(CAgeInDocTableCol(u'Минимальный возраст', 'minimumAge', 10, high=400)).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Единица ПО', 'endAgeUnit', 6, [u'', u'Д', u'Н', u'М', u'Г'])).setSortable(True)
        self.addCol(CAgeInDocTableCol(u'Максимальный возраст', 'maximumAge', 10, high=400)).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Период контроля', 'controlPeriod', 4, [u'Дата случая', u'Конец года случая', u'Конец предыдущего случаю года'])).setSortable(True)


class MesEditor(CItemEditorBaseDialog, Ui_MESEditor):
    u"""Окно редактирования МЭС"""
    CHECK_ERRORS = {0:u"""Корректная запись.""",
                    1:u"""Код не введён.""",
                    2:u"""Код не уникален""",
                    3:u"""Тариф должен быть вещественным числом."""}
    def __init__(self, parent, mes):
        CItemEditorBaseDialog.__init__(self, parent, 'MES')
        self.setupUi(self)
        self.mes_info = mes

        self.addModels('MKB', CMKBModel(self))
        self.setModels(self.tblMKB, self.modelMKB, self.selectionModelMKB)
        self.tabMKB.setFocusProxy(self.tblMKB)
        self.tblMKB.addPopupDelRow()

        self.addModels('Services', CServicesModel(self))
        self.setModels(self.tblServices, self.modelServices, self.selectionModelServices)
        self.tabServices.setFocusProxy(self.tblServices)
        self.tblServices.addPopupDelRow()

        self.addModels('Visits', CVisitsModel(self))
        self.setModels(self.tblVisits, self.modelVisits, self.selectionModelVisits)
        self.tabVisits.setFocusProxy(self.tblVisits)
        self.tblVisits.addPopupDelRow()

        self.addModels('Equipment', CEquipmentModel(self))
        self.setModels(self.tblEquipment, self.modelEquipment, self.selectionModelEquipment)
        self.tabEquipment.setFocusProxy(self.tblEquipment)
        self.tblEquipment.addPopupDelRow()

        self.addModels('Medicament', CMedicamentModel(self))
        self.setModels(self.tblMedicament, self.modelMedicament, self.selectionModelMedicament)
        self.tabMedicament.setFocusProxy(self.tblMedicament)
        self.tblMedicament.addPopupDelRow()

        self.addModels('Blood', CBloodModel(self))
        self.setModels(self.tblBlood, self.modelBlood, self.selectionModelBlood)
        self.tabBlood.setFocusProxy(self.tblBlood)
        self.tblBlood.addPopupDelRow()

        self.addModels('Nutrient', CNutrientModel(self))
        self.setModels(self.tblNutrient, self.modelNutrient, self.selectionModelNutrient)
        self.tabNutrient.setFocusProxy(self.tblNutrient)
        self.tblNutrient.addPopupDelRow()

        self.addModels('LimitedBySexAge', CLimitedBySexAgeModel(self))
        self.setModels(self.tblLimitedBySexAge, self.modelLimitedBySexAge, self.selectionModelLimitedBySexAge)
        self.tabLimitedBySexAge.setFocusProxy(self.tblLimitedBySexAge)
        self.tblLimitedBySexAge.addPopupDelRow()

        self.cmbGroup.setTable('mrbMESGroup', filter='deleted=0')
        self.cmbKSG.setTable('MES_ksg')
        if not self.mes_info.isNew():
            self.load()


    def getMES(self):
        return self.mes_info


    def load(self):
        CItemEditorBaseDialog.load(self, self.mes_info.getId())
        self.chkActive.setChecked(self.mes_info.isActive())
        self.chkInternal.setChecked(self.mes_info.isInternal())
        self.cmbGroup.setValue(self.mes_info.getGroupId())
        self.cmbKSG.setValue(self.mes_info.getKSGId())
        self.edtCode.setText(self.mes_info.getCode())
        self.edtName.setText(self.mes_info.getName())
        self.textDescription.setPlainText(self.mes_info.getDescription())
        self.edtModel.setText(self.mes_info.getPatientModel())
        self.edtTariff.setText(str(self.mes_info.getTariff()))
        self.spinMin.setValue(self.mes_info.getMinDuration())
        self.spinMax.setValue(self.mes_info.getMaxDuration())
        self.spinAvg.setValue(self.mes_info.getAvgDuration())
        self.spinKSG.setValue(self.mes_info.getKSGNorm())
        self.edtEndDate.setDate(forceDate(self.mes_info.getEndDate()))
        self.edtPeriodicity.setValue(self.mes_info.getPeriodicity())
        self.chkPolyTrauma.setChecked(self.mes_info.getPolyTrauma())


    def save(self):
        self.mes_info.init(self.chkActive.isChecked(),
                           self.chkInternal.isChecked(),
                           self.cmbGroup.value(),
                           self.edtCode.text(),
                           self.edtName.text(),
                           self.spinMin.value(),
                           self.spinMax.value(),
                           self.spinAvg.value(),
                           self.edtModel.text(),
                           float(self.edtTariff.text()),
                           self.textDescription.toPlainText(),
                           self.spinKSG.value(),
                           self.edtPeriodicity.value(),
                           self.cmbKSG.value(),
                           self.edtEndDate.date(),
                           self.chkPolyTrauma.isChecked()
                           )
        try:
            db = QtGui.qApp.db
            db.transaction()
            try:
                id = self.mes_info.save()
                self.modelMKB.saveItems(id)
                self.modelServices.saveItems(id)
                self.modelVisits.saveItems(id)
                self.modelEquipment.saveItems(id)
                self.modelMedicament.saveItems(id)
                self.modelBlood.saveItems(id)
                self.modelNutrient.saveItems(id)
                self.modelLimitedBySexAge.saveItems(id)
                db.commit()
            except:
                db.rollback()
                #QtGui.qApp.logCurrentException()
                raise
            self.setItemId(id)
            self.setIsDirty(False)
            return id
        except Exception, e:
            #QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        unicode(e),
                                        QtGui.QMessageBox.Close)
            return None


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        id = self.itemId()
        self.modelMKB.loadItems(id)
        self.modelServices.loadItems(id)
        self.modelVisits.loadItems(id)
        self.modelEquipment.loadItems(id)
        self.modelMedicament.loadItems(id)
        self.modelBlood.loadItems(id)
        self.modelNutrient.loadItems(id)
        self.modelLimitedBySexAge.loadItems(id)
        self.setIsDirty(False)


    def check(self):
        u"""Проверка записи на корректность"""
        code = self.edtCode.text()
        if not len(code):
            return 1
        query = QtGui.qApp.db.query("""
            SELECT id
            from MES
            where code = '%s'
            and deleted = 0"""%code)
        if query.size() > 0: # такой код есть, проверяем на уникальность
            if self.mes_info.isNew():
                return 2
            else:
                query.first()
                if forceRef(query.record().value("id")) != self.mes_info.getId():
                    return 2
        try:
            self.mes_info.setTariff(float(self.edtTariff.text()))
        except:
            return 3
        return 0


    def saveData(self):
        status = self.check()
        if status == 0:
            self.save()
            return True
        else:
            QtGui.QMessageBox.warning(self, u'Проверка данных', self.CHECK_ERRORS[status])
            return False

