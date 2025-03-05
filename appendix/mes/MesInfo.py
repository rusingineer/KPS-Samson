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


from PyQt4 import QtSql, QtGui

from Reports.MesDescription import insertMainSection, insertPersonServicesSection, insertServiceSection, \
    insertMedicamentsSection
from Reports.ReportBase import CReportBase, createTable
from appendix.mes.MKBTree import checkMKBTable, getMKBName, MKB_TABLE_NAME, MKB_SUBCLASS_ITEM_TABLE_NAME
from library.Utils import forceRef, forceString, toVariant


class CQueryModel(QtSql.QSqlQueryModel):
    u"""Надо бы вместо него использовать CTableModel,
    но там всё сложно, а у меня нет времени разбираться.

    Всегда предполагаем, что в запросе id - первая колонка.
    """
    def __init__(self, parent):
        QtSql.QSqlQueryModel.__init__(self, parent)

    def idList(self):
        result = []
        for i in xrange(self.rowCount()):
            result += [forceRef(self.record(i).value("id")), ]
        return result

    def findItemIdIndex(self, id):
        idList = self.idList()
        if id in idList:
            return idList.index(id)
        else:
            return -1

    def cloneRow(self, num):
        id = forceRef(self.record(num).value("id"))
        self.cloneRowById(id)

    def cloneRowById(self, id):
        self.reset()

    def removeRow(self, num):
        id = forceRef(self.record(num).value("id"))
        self.removeRowById(id)

    def removeRowById(self, id):
        self.reset()

    def canRemoveRow(self, row):
        return True

    def confirmRemoveRow(self, view, row, multiple=False):
        # multiple: запрос относительно одного элемента из множества, нужно предусмотреть досрочный выход из серии вопросов
        # результат: True: можно удалять
        #            False: нельзя удалять
        #            None: удаление прервано
        buttons = QtGui.QMessageBox.Yes|QtGui.QMessageBox.No
        if multiple:
            buttons |= QtGui.QMessageBox.Cancel
        mbResult = QtGui.QMessageBox.question(view, u'Внимание!', u'Действительно удалить?', buttons, QtGui.QMessageBox.No)
        return {QtGui.QMessageBox.Yes: True,
                QtGui.QMessageBox.No: False}.get(mbResult, None)


class CMesModel(CQueryModel):
    def __init(self):
        CQueryModel.__init__(self)
        self.db = None

    def getMESQuery(self, filter):
        return u"""
        SELECT MES.id,
            MES.active as 'Акт.',
            mrbMESGroup.name as 'Группа',
            MES_ksg.name AS 'КСГ',
            MES.code as 'Код',
            MES.name as 'Имя',
            MES.avgDuration as 'Ср. длит.',
            MES.patientModel as 'Модель пациента',
            MES.tariff as 'Тариф',
            MES.descr as 'Описание',
            MES.minDuration,
            MES.maxDuration,
            MES.KSGNorm,
            MES.group_id,
            MES.internal as 'Внутр.',
            MES.periodicity as 'Периодичность',
            MES.ksg_id,
            MES.endDate AS 'Дата окончания',
            MES.isPolyTrauma AS 'Политравма'
        FROM MES
        LEFT JOIN mrbMESGroup ON mrbMESGroup.id = MES.group_id
        LEFT JOIN MES_ksg ON MES_ksg.id = MES.ksg_id
        WHERE %s
        and MES.deleted = 0
        ORDER by MES.code
        """%filter

    def setParam(self, db, filter):
        self.db = db
        self.setQuery(self.getMESQuery(filter), self.db.db)

    def cloneRowById(self, id):
        pass
        #TODO: сделать копирование

    def removeRowById(self, id):
        self.db.query("""
                    UPDATE MES
                    SET deleted = 1
                    WHERE id = %d
                    """%id)
        self.setQuery(self.query().lastQuery(), self.db.db) # вместо self.reset()
#        self.reset() почему-то не работает?????????????


class CMesInfo:
    u"""Запись МЭС"""
    def __init__(self, id=0, active=1, internal=0, group_id=0, code=None, name=None, min=None, max=None, avg=None, model=None, tariff=None,
                 description=None, norm=None, periodicity=0, ksg_id=None, endDate = None, isPolyTrauma=0):
        self.id = id
        self.init(active, internal, group_id, code, name, min, max, avg, model, tariff, description, norm, periodicity, ksg_id, endDate, isPolyTrauma)

    def init(self, active, internal, group_id, code, name, min, max, avg, model, tariff, description, norm, periodicity, ksg_id, endDate, isPolyTrauma):
        self.active = active
        self.internal = internal
        self.group_id = group_id
        self.code = code
        self.name = name
        self.min = min
        self.max = max
        self.avg = avg
        self.model = model
        self.tariff = tariff
        self.description = description
        self.norm = norm
        self.periodicity = periodicity
        self.ksg_id = ksg_id
        self.endDate = endDate
        self.isPolyTrauma = isPolyTrauma

    def getId(self):
        return self.id

    def isNew(self):
        return self.getId() == 0

    def isSaved(self):
        return True # как проверять?????????

    def isActive(self):
        return self.active == 1

    def isInternal(self):
        return self.internal == 1

    def getPolyTrauma(self):
        return self.isPolyTrauma == 1

    def getGroupId(self):
        return self.group_id

    def getKSGId(self):
        return self.ksg_id

    def getCode(self):
        return self.code

    def getName(self):
        return self.name

    def getDescription(self):
        return self.description

    def getMinDuration(self):
        return self.min

    def getMaxDuration(self):
        return self.max

    def getAvgDuration(self):
        return self.avg

    def getKSGNorm(self):
        return self.norm
        
    def getEndDate(self):
        return self.endDate

    def getPeriodicity(self):
        return self.periodicity

    def getPatientModel(self):
        return unicode(self.model)

    def getPatientModelDict(self):
        codes = self.getPatientModel().split('.')
        #print "codes = " + str(codes)
        query = QtGui.qApp.db.query("""
            SELECT fieldIdx, name, tableName
            FROM ModelDescription
            ORDER BY fieldIdx
        """)
        result = {}
        num = 0
        while query.next() and num < len(codes):
            record = query.record()
            subquery = QtGui.qApp.db.query("""
                SELECT name
                FROM %s
                WHERE code = '%s'
            """%(forceString(record.value("tableName")), codes[num]))
            subquery.first()
            subrecord = subquery.record()
            result[ unicode(record.value("name").toString()) ] = forceString(subrecord.value("name"))
            num += 1
        return result

    def getTariff(self):
        return self.tariff

    def setTariff(self, tariff):
        self.tariff = tariff


    def insertMKBSection(self, cursor):
        db = QtGui.qApp.db
        cursor.insertText(u'Заболевания, входящие в МЭС (в формулировках МКБ)')
        cursor.insertBlock()
        charFormat = QtGui.QTextCharFormat()
        cursor.setCharFormat(charFormat)

        tableColumns = [
                ('5%',   [u'№'],                   CReportBase.AlignRight),
                ('10%',  [u'Код диагноза по МКБ'], CReportBase.AlignLeft),
                ('20%',[u'Диагноз'],             CReportBase.AlignLeft),
                ('10%',  [u'Код доп. диагноза по МКБ'], CReportBase.AlignLeft),
                ('20%',[u'Доп. диагноз'],        CReportBase.AlignLeft),
                ('10%', [u'Код осложнения основного диагноза по МКБ'], CReportBase.AlignLeft),
                ('20%', [u'Осложнение'], CReportBase.AlignLeft),
                ]

        table = createTable(cursor, tableColumns)
        tableMKB = db.table('MES_mkb')
        if checkMKBTable():
            for record in db.getRecordList(tableMKB, 'mkb, mkbEx, mkb2, mkb3', tableMKB['master_id'].eq(self.getId()) + ' and ' + tableMKB['deleted'].eq('0'), 'mkb, mkbEx, mkb2, mkb3'):
                i = table.addRow()
                table.setText(i, 0, i)
                mkb = record.value('mkb')
                table.setText(i, 1, forceString(mkb))
                table.setText(i, 2, getMKBName(forceString(mkb)))
                # mkbEx = record.value('mkbEx')
                # table.setText(i, 3, forceString(mkbEx))
                # table.setText(i, 4, getMKBName(forceString(mkbEx)))
                mkb2 = record.value('mkb2')
                table.setText(i, 3, forceString(mkb2))
                table.setText(i, 4, getMKBName(forceString(mkb2)))
                mkb3 = record.value('mkb3')
                table.setText(i, 5, forceString(mkb3))
                table.setText(i, 6, getMKBName(forceString(mkb3)))
        else:
            for record in db.getRecordList(tableMKB, 'mkb, mkbEx', tableMKB['master_id'].eq(self.getId()) + ' and ' + tableMKB['deleted'].eq('0'), 'mkb, mkbEx'):
                i = table.addRow()
                table.setText(i, 0, i)
                mkb = record.value('mkb')
                table.setText(i, 1, forceString(mkb))
                table.setText(i, 2, '')
                # mkbEx = record.value('mkbEx')
                # table.setText(i, 3, forceString(mkbEx))
                # table.setText(i, 4, '')
                mkb2 = record.value('mkb2')
                table.setText(i, 3, forceString(mkb2))
                table.setText(i, 4, '')
                mkb3 = record.value('mkb3')
                table.setText(i, 5, forceString(mkb3))
                table.setText(i, 6, '')


        cursor.movePosition(QtGui.QTextCursor.End)


    def getFullDescription(self):
        u"""Описание МЭС (чуть-чуть отличается от стандартного описания из Reports.MesDescription)"""
        mesId = self.getId()
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        insertMainSection(cursor, mesId)
        cursor.insertBlock()
        cursor.insertBlock()
        self.insertMKBSection(cursor) # вот здесь отличие
        cursor.insertBlock()
        cursor.insertBlock()
        insertPersonServicesSection(cursor, mesId)
        insertServiceSection(cursor, mesId, u'Услуги лечащего врача', u'в')
        insertServiceSection(cursor, mesId, u'Лабораторные диагностические услуги', u'к')
        insertServiceSection(cursor, mesId, u'Инструментальные диагностические услуги', u'д')
        insertServiceSection(cursor, mesId, u'Немедикаментозная терапия', u'л')
        insertServiceSection(cursor, mesId, u'Вспомогательные услуги', u'с')
        insertServiceSection(cursor, mesId, u'Услуги по экспертизе', u'э')
        insertServiceSection(cursor, mesId, u'Прочие услуги', None)
        insertMedicamentsSection(cursor, mesId)
        return doc



    def load(self):
        query = QtGui.qApp.db.query(CMesModel.getMESQuery("id=%d"%self.getId()))
        if query.first():
            record = query.record()
            self.init(record.value(u'Акт.'),
                      record.value(u'Внутр.'),
                      record.value('group_id'),
                      record.value(u'Код'),
                      record.value(u'Имя'),
                      record.value('minDuration'),
                      record.value('maxDuration'),
                      record.value(u'Ср. длит.'),
                      record.value(u'Модель пациента'),
                      record.value(u'Тариф'),
                      record.value(u'Описание'),
                      record.value('KSGNorm'),
                      record.value('Периодичность'),
                      record.value('ksg_id'),
                      record.value('Дата окончания'),
                      record.value('Политравма')
                      )

    def save(self):
        u"""Сохраняет в БД и возвращает id сохранённой записи"""
        record = QtGui.qApp.db.record("MES")
        record.setValue("active", toVariant(self.isActive()))
        record.setValue("internal", toVariant(self.isInternal()))
        record.setValue("group_id", toVariant(self.getGroupId()))
        record.setValue("code", toVariant(self.getCode()))
        record.setValue("name", toVariant(self.getName()))
        record.setValue("descr", toVariant(self.getDescription()))
        record.setValue("patientModel", toVariant(self.getPatientModel()))
        record.setValue("minDuration", toVariant(self.getMinDuration()))
        record.setValue("maxDuration", toVariant(self.getMaxDuration()))
        record.setValue("avgDuration", toVariant(self.getAvgDuration()))
        #tariff_field = record.field("tariff")
        #tariff_field.setType(QtCore.QVariant.String)  # вещ. число сохраняем как строку, чтобы не было проблем с форматом
        #print QtGui.qApp.db.driver().formatValue(tariff_field)
        #record.replace(record.indexOf("tariff"), tariff_field)
        record.setValue("tariff", toVariant(self.getTariff()))
        record.setValue("KSGNorm", toVariant(self.getKSGNorm()))
        record.setValue("periodicity", toVariant(self.getPeriodicity()))
        record.setValue('ksg_id', toVariant(self.getKSGId()))
        record.setValue('endDate', toVariant(self.getEndDate()))
        record.setValue('isPolyTrauma', toVariant(self.getPolyTrauma()))
        if self.isNew():
            return QtGui.qApp.db.insertRecord("MES", record)
        else:
            record.setValue("id", toVariant(self.id))
            return QtGui.qApp.db.updateRecord("MES", record)


    def getMKBQuery(self):
        if checkMKBTable():
            return u"""
        SELECT MES_mkb.mkb as 'Код диагноза',
        CONCAT_WS(' / ', %s.DiagName, %s.name) as 'Диагноз',
        MES_mkb.mkbEx as 'Доп.код диагноза',
        CONCAT_WS(' / ', MKB_mkbEx.DiagName, MKBEx_SUBCLASS.name) as 'Доп.диагноз',
        MES_mkb.mkb2 as 'Код соп. диагноза',
        CONCAT_WS(' / ', MKB_mkb2.DiagName, MKB2_SUBCLASS.name) as 'Соп.диагноз',
        MES_mkb.mkb3 as 'Код осложнения диагноза',
        CONCAT_WS(' / ', MKB_mkb3.DiagName, MKB3_SUBCLASS.name) as 'Диагноз осложнения',
        MES_mkb.groupingMKB AS 'Группировка',
        IF(MES_mkb.blendingMKB = 0, 'основной и дополнительный', IF(MES_mkb.blendingMKB = 1, 'основной', 'дополнительный')) AS 'Сочетаемость',
        MES_mkb.krit as 'Доп.критерий',
        DATE(MES_mkb.begDate) as `Дата начала`,
        DATE(MES_mkb.endDate) as `Дата окончания`
        FROM MES_mkb
        LEFT JOIN %s on %s.DiagID = LEFT(MES_mkb.mkb, 5)
        LEFT JOIN %s AS MKB_mkbEx on MKB_mkbEx.DiagID = LEFT(MES_mkb.mkbEx, 5)
        LEFT JOIN %s AS MKB_mkb2 on MKB_mkb2.DiagID = LEFT(MES_mkb.mkb2, 5)
        LEFT JOIN %s AS MKB_mkb3 on MKB_mkb3.DiagID = LEFT(MES_mkb.mkb3, 5)
        LEFT JOIN %s ON (%s.master_id = %s.MKBSubclass_id
        AND (length(MES_mkb.mkb) = 6 AND %s.code = RIGHT(MES_mkb.mkb, 1)))
        LEFT JOIN %s AS MKBEx_SUBCLASS ON (MKBEx_SUBCLASS.master_id = MKB_mkbEx.MKBSubclass_id
        AND (length(MES_mkb.mkbEx) = 6 AND MKBEx_SUBCLASS.code = RIGHT(MES_mkb.mkbEx, 1)))
        LEFT JOIN %s AS MKB2_SUBCLASS ON (MKB2_SUBCLASS.master_id = MKB_mkb2.MKBSubclass_id
        AND (length(MES_mkb.mkb2) = 6 AND MKB2_SUBCLASS.code = RIGHT(MES_mkb.mkb2, 1)))
        LEFT JOIN %s AS MKB3_SUBCLASS ON (MKB3_SUBCLASS.master_id = MKB_mkb3.MKBSubclass_id
        AND (length(MES_mkb.mkb3) = 6 AND MKB3_SUBCLASS.code = RIGHT(MES_mkb.mkb3, 1)))
        WHERE MES_mkb.master_id = %d
        and MES_mkb.deleted = 0
        """ % (MKB_TABLE_NAME, MKB_SUBCLASS_ITEM_TABLE_NAME, MKB_TABLE_NAME, MKB_TABLE_NAME, MKB_TABLE_NAME, MKB_TABLE_NAME, MKB_TABLE_NAME,
             MKB_SUBCLASS_ITEM_TABLE_NAME, MKB_SUBCLASS_ITEM_TABLE_NAME, MKB_SUBCLASS_ITEM_TABLE_NAME, MKB_SUBCLASS_ITEM_TABLE_NAME, MKB_TABLE_NAME, MKB_SUBCLASS_ITEM_TABLE_NAME,
             MKB_SUBCLASS_ITEM_TABLE_NAME, self.id)
        else:
            return u"""
        SELECT mkb as 'Код диагноза',
        '' as 'Диагноз',
        mkbEx as 'Доп.код диагноза',
        '' as 'Доп.диагноз',
        mkb2 as 'Код соп. диагноза',
        '' as 'Соп.диагноз',
        mkb3 as 'Код осложнения диагноза',
        '' as 'Диагноз осложнения',
        groupingMKB AS 'Группировка',
        IF(blendingMKB = 0, 'основной и дополнительный', IF(blendingMKB = 1, 'основной', 'дополнительный')) AS 'Сочетаемость'
        FROM MES_mkb
        WHERE master_id = %d
        and MES_mkb.deleted = 0
        """ % (self.id)


    def getServicesQuery(self):
        return u"""
        SELECT mrbServiceGroup.name as `Группа`,
        mrbService.code as `Код`,
        mrbService.name as `Название`,
        mrbService.doctorWTU as `УЕТ вр.`,
        mrbService.paramedicalWTU as `УЕТ перс.`,
        MES_service.averageQnt as `СК`,
        MES_service.necessity as `ЧП`,
        MES_service.groupCode as `Группа`,
        MES_service.binding as `Объединять`,
        IF(sex = 1, 'М', IF(sex = 2, 'Ж', 'не определено')) as `Пол`,
        IF(begAgeUnit = 1, 'Д', IF(begAgeUnit = 2, 'Н', IF(begAgeUnit = 3, 'М', IF(begAgeUnit = 4, 'Г','не определено')))) as `Единица С`,
        minimumAge as `Минимальный возраст`,
        IF(endAgeUnit = 1, 'Д', IF(endAgeUnit = 2, 'Н', IF(endAgeUnit = 3, 'М', IF(endAgeUnit = 4, 'Г','не определено')))) as `Единица ПО`,
        maximumAge as `Максимальный возраст`,
        IF(controlPeriod = 1, 'Конец года случая', IF(controlPeriod = 2, 'Конец предыдущего случаю года', 'Дата случая')) as `Период контроля`,
        MES_service.krit as 'Доп.критерий',
        MES_service.minFr as 'мин. фракций',
        MES_service.maxFr as 'макс. фракций',
        DATE(MES_service.begDate) as `Дата начала`,
        DATE(MES_service.endDate) as `Дата окончания`
        FROM MES_service
        LEFT JOIN mrbService ON mrbService.id = MES_service.service_id
        LEFT JOIN mrbServiceGroup ON mrbServiceGroup.id = mrbService.group_id
        WHERE master_id = %d
        and MES_service.deleted = 0
        """%self.id
#TODO: как отображать состав сложных услуг? 


    def getVisitsQuery(self):
        return u"""
        SELECT mrbVisitType.name as 'Тип визита',
        mrbSpeciality.name as 'Специальность',
        MES_visit.serviceCode as 'Код услуги',
        MES_visit.additionalServiceCode as 'Доп. код',
        MES_visit.altAdditionalServiceCode as 'Альтернативный доп. код',
        MES_visit.groupCode as 'Группировка',
        MES_visit.averageQnt as 'СК',
        IF(sex = 1, 'М', IF(sex = 2, 'Ж', 'не определено')) as `Пол`,
        IF(begAgeUnit = 1, 'Д', IF(begAgeUnit = 2, 'Н', IF(begAgeUnit = 3, 'М', IF(begAgeUnit = 4, 'Г','не определено')))) as `Единица С`,
        minimumAge as `Минимальный возраст`,
        IF(endAgeUnit = 1, 'Д', IF(endAgeUnit = 2, 'Н', IF(endAgeUnit = 3, 'М', IF(endAgeUnit = 4, 'Г','не определено')))) as `Единица ПО`,
        maximumAge as `Максимальный возраст`,
        IF(controlPeriod = 1, 'Конец года случая', IF(controlPeriod = 2, 'Конец предыдущего случаю года', 'Дата случая')) as `Период контроля`
        FROM MES_visit
        LEFT JOIN mrbVisitType ON mrbVisitType.id = MES_visit.visitType_id
        LEFT JOIN mrbSpeciality ON mrbSpeciality.id = MES_visit.speciality_id
        WHERE master_id = %d
        and MES_visit.deleted = 0
        """%self.id


    def getEquipmentQuery(self):
        return u"""
        SELECT mrbEquipment.code as `Код`,
        mrbEquipment.name as `Оборудование`,
        MES_equipment.averageQnt as `СЧЕ`,
        MES_equipment.necessity as `ЧН`
        FROM MES_equipment
        LEFT JOIN mrbEquipment ON mrbEquipment.id = MES_equipment.equipment_id
        WHERE master_id = %d
        and MES_equipment.deleted = 0
        """%self.id


    def getMedicamentQuery(self):
        return u"""
        SELECT MES_medicament.medicamentCode as `Код`,
        mrbMedicament.name as `МНН`,
        mrbMedicament.tradeName as `Торговое название`,
        mrbMedicament.form as `Форма выпуска`,
        mrbMedicament.packSize as `Кол-во в упак.`,
        mrbMedicament.packPrice as `Цена упак.`,
        mrbMedicament.unitPrice as `Цена ед.`,
        MES_medicament.dosage as `Дозировка`,
        mrbMedicamentDosageForm.name as 'Лекарственная форма',
        MES_medicament.averageQnt as 'СЧЕ',
        MES_medicament.necessity as 'ЧН'
        FROM MES_medicament
        LEFT JOIN mrbMedicament ON mrbMedicament.code = MES_medicament.medicamentCode
        LEFT JOIN mrbMedicamentDosageForm ON mrbMedicamentDosageForm.id = MES_medicament.dosageForm_id
        WHERE master_id = %d
        and MES_medicament.deleted = 0
        """%self.id


    def getBloodQuery(self):
        return u"""
        SELECT
        mrbBloodPreparation.code as `Код`,
        mrbBloodPreparation.dosage as `Дозировка`,
        mrbBloodPreparation.tariff as `Тариф`,
        MES_bloodPreparation.averageQnt as `СЧЕ`,
        MES_bloodPreparation.necessity as `ЧН`
        FROM MES_bloodPreparation
        LEFT JOIN mrbBloodPreparation ON mrbBloodPreparation.id = MES_bloodPreparation.preparation_id
        WHERE master_id = %d
        and MES_bloodPreparation.deleted = 0
        """%self.id


    def getNutrientQuery(self):
        return u"""
        SELECT mrbNutrient.code as `Код`,
        mrbNutrient.name as `Наименование`,
        mrbNutrient.dosage as `Дозировка`,
        mrbNutrient.tariff as `Тариф`,
        MES_nutrient.averageQnt as `СЧЕ`,
        MES_nutrient.necessity as `ЧН`
        FROM MES_nutrient
        LEFT JOIN mrbNutrient ON mrbNutrient.id = MES_nutrient.nutrient_id
        WHERE master_id = %d
        and MES_nutrient.deleted = 0
        """%self.id


    def getLimitedBySexAgeQuery(self):
        return u"""
        SELECT IF(sex = 1, 'М', IF(sex = 2, 'Ж', 'не определено')) as `Пол`,
        IF(begAgeUnit = 1, 'Д', IF(begAgeUnit = 2, 'Н', IF(begAgeUnit = 3, 'М', IF(begAgeUnit = 4, 'Г','не определено')))) as `Единица С`,
        minimumAge as `Минимальный возраст`,
        IF(endAgeUnit = 1, 'Д', IF(endAgeUnit = 2, 'Н', IF(endAgeUnit = 3, 'М', IF(endAgeUnit = 4, 'Г','не определено')))) as `Единица ПО`,
        maximumAge as `Максимальный возраст`,
        IF(controlPeriod = 1, 'Конец года случая', IF(controlPeriod = 2, 'Конец предыдущего случаю года', 'Дата случая')) as `Период контроля`
        FROM MES_limitedBySexAge
        WHERE master_id = %d AND deleted = 0
        ORDER BY minimumAge, controlPeriod
        """%self.id

