# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature
from Reports.EconomicAnalisys import (colServiceInfis, colServiceName,  colAmount, colSUM, getStmt, \
    colMedicalTypeCode, colObr, colEvent, colMKBCode, colPos, colEventTypeId, colCSG, colOrgStructureId, \
    colEventProfileCode, colServiceEndDate,  colFinanceCode, colClient, colSMP, colVUSirius)
from Reports.EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase
from library.Utils import forceString, forceInt, forceDouble, forceBool, forceRef, forceDate



class CReportAFT_Forecast12month(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет для АФТ 12 месяцев')
        self.otherRecords = []
        self.setOrientation(QtGui.QPrinter.Landscape)


    @staticmethod
    def selectData(params):
        """
        colPos - колонка с кол-вом посещений
        colClient - колонка с client_id -- Client.id
        colSum - колонка со стоимостью
        colObr - колонка кол-во обращений
        colAmount - колонка с кол-вом услуг
        colServiceInfis - колонка с кодом услуги
        colEventProfileCode - колонка с rbEventProfile.regionalCode (профили событий) -- для определения диспансеризации
        colServiceEndDate - колонка с датой окончания услуги -- для определения месяца, а может и года
        colMedicalTypeCode - колонка с типом мед.помощи -- для определения Взрослая / детская поликлиника
        colFinanceCode - колонка с кодом финансирования   -- для определения ОМС / платные
        colEventTypeId - колонка с типом события -- для определения


        """
        cols = [colServiceInfis, colServiceName,   colAmount, colSUM, colObr, colEvent,
                colMedicalTypeCode, colMKBCode, colPos, colEventTypeId, colCSG, colVUSirius,
                colEventProfileCode, colServiceEndDate, colFinanceCode, colClient, colSMP]
        colsStmt = u"""select
                        colFinanceCode,
                        colEventProfileCode,
                        colServiceEndDate,
                        colMedicalTypeCode,
                        colEventTypeId,
                        sum(IF(colPos = 0 and colCSG = 0 and colSMP = 0 and colObr = 0, colAmount, 0)) as usl,
                        round(sum(colSUM), 2) as sum,
                        sum(colObr) as colObr,
                        count(distinct colEvent) as visits,
                        sum(colPos) as colPos,
                        group_concat(colClient) as colClient,
                        colVUSirius
                        """
        groupCols = 'colFinanceCode, colServiceEndDate, colEventProfileCode, colMedicalTypeCode, colEventTypeId, colVUSirius'
        orderCols = ''

        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params)

        db = QtGui.qApp.db
        return db.query(stmt)



    def getSetupDialog(self, parent):
        result = CReportAFT_Forecast12monthSetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result



    def build(self, params):

        MONTHS_RU = {
            1: u'Январь', 2: u'Февраль', 3: u'Март', 4: u'Апрель',
            5: u'Май', 6: u'Июнь', 7: u'Июль', 8: u'Август',
            9: u'Сентябрь', 10: u'Октябрь', 11: u'Ноябрь', 12: u'Декабрь'
        }
        FIN_LABELS = {0: u'доп услуги в тарифе ОМС', 1: u'платные услуги'}
        MED_LABELS = {
            u'all': u'всего',
            u'21': u'взрослая поликлиника',
            u'22': u'детская поликлиника'
        }
        MED_ORDER = [u'all', u'21', u'22']

        # Коды профилей событий для строки «Диспансеризация» (платные)
        DISP_PROFILE_CODES = (u'8008', u'8009', u'8011', u'8014', u'8015')
        DOGOVOR_EVENTTYPE_ID = None
        eventTypeId_record  = QtGui.qApp.db.getRecordEx('EventType', 'id', u" EventType.name like '%амб%лече%диаг%униве%сириус%' ")
        if eventTypeId_record:
            DOGOVOR_EVENTTYPE_ID = forceInt(eventTypeId_record.value(u'id')) if eventTypeId_record.value(u'id') else None

        # Внутренние ключи для спецстрок платных услуг
        DISP_KEY = u'__disp__'
        DOGOVOR_KEY = u'__dogovor__'

        SVC_DISPLAY = {
            u'all': u'всего',
            DISP_KEY: u'Диспансеризация'.upper(),
            DOGOVOR_KEY: u'Договор с АНОО ВО "Университет"',
        }

        # ── Фиксированный порядок строк профилей ───────────────────────────
        # Ключи должны совпадать с фактическими значениями colVUSirius в базе.
        # Если значения отличаются — замени строки ниже на нужные коды.
        OMS_PROFILE_ORDER = [
            u'all',
            u'УЗИ'.upper(),
            u'рентген и маммография'.upper(),
            u'функц. диагностика'.upper(),
            u'массаж'.upper(),
            u'физиотерапия'.upper(),
            u'манипуляции'.upper(),
            u'лабораторные иссл.'.upper(),
        ]
        PAID_PROFILE_ORDER = [
            u'all',
            u'Поликлиника'.upper(),
            u'УЗИ'.upper(),
            u'рентген и маммография'.upper(),
            u'функц. диагностика'.upper(),
            u'массаж'.upper(),
            u'физиотерапия'.upper(),
            u'манипуляции'.upper(),
            u'лабораторные иссл.'.upper(),
            DISP_KEY,
            DOGOVOR_KEY,
        ]
        # Детская поликлиника в платных — без Диспансеризации и Договора
        PAID_PROFILE_ORDER_CHILD = [
            u'all',
            u'Поликлиника'.upper(),
            u'УЗИ'.upper(),
            u'рентген и маммография'.upper(),
            u'функц. диагностика'.upper(),
            u'массаж'.upper(),
            u'физиотерапия'.upper(),
            u'манипуляции'.upper(),
            u'лабораторные иссл.'.upper(),
        ]

        # ── Структура словаря ───────────────────────────────────────────────
        # reportDict[fin_code][med_key][svc_key] = {
        #     'pos': {(год,мес): float},  -- посещения
        #     'usl': {(год,мес): int},    -- услуги (не посещения/обращения)
        #     'sum': {(год,мес): float},  -- сумма, руб.
        #     'cli': {(год,мес): int},    -- пациенты (диспансеризация / договор)
        # }
        # fin_code : 0 = ОМС (financeCode='2')  | 1 = платные (financeCode='4')
        # med_key  : 'all' = оба типа  | '21' = взрослая  | '22' = детская
        # svc_key  : 'all' = все суммарно | значение typeUsl | DISP_KEY | DOGOVOR_KEY
        reportDict = {0: {}, 1: {}}
        active_months = set()

        def processQuery(queryObj):
            while queryObj.next():
                record = queryObj.record()

                financeCode = forceString(record.value('colFinanceCode'))
                medicalTypeCode = forceString(record.value('colMedicalTypeCode'))
                serviceEndDate = forceDate(record.value('colServiceEndDate'))
                eventProfileCode = forceString(record.value('colEventProfileCode'))
                eventTypeId = forceRef(record.value('colEventTypeId'))
                usl = forceInt(record.value('usl'))
                summa = forceDouble(record.value('sum'))
                visits = forceInt(record.value('visits'))
                amountClientId = forceString(record.value('colClient'))
                typeUsl = forceString(record.value('colVUSirius'))

                # if (financeCode not in (u'2', u'4') or (medicalTypeCode not in (u'21', u'22'))
                #         or (financeCode == u'4' and medicalTypeCode not in (u'21', u'22', u'211', u'261', u'233', u'244', u'232', u'252', u'262'))):
                #     continue
                if financeCode not in (u'2', u'4'):
                    continue    # скипаем не ОМС и не платные
                if (financeCode == u'4' and medicalTypeCode not in (u'21', u'22', u'211', u'261', u'233', u'244', u'232', u'252', u'262')):
                    continue    # скипаем платные, если у них вид помощи не взр/дет поликлиника или связанные с диспансеризацией
                if financeCode == u'2' and medicalTypeCode not in (u'21', u'22'):
                    continue
                if (not typeUsl or typeUsl == u'') and eventProfileCode not in DISP_PROFILE_CODES:
                    continue

                fin_code = 0 if financeCode == u'2' else 1
                date_year = forceInt(serviceEndDate.toString(u'yyyy'))
                date_month = forceInt(serviceEndDate.toString(u'MM'))
                ym_key = (date_year, date_month)
                active_months.add(ym_key)
                if typeUsl.upper() == u'ЛАБОРАТОРИЯ':
                    typeUsl = u'лабораторные иссл.'
                # Определяем ключ типа услуги
                if fin_code == 1:
                    if medicalTypeCode in (u'211', u'261', u'233', u'244', u'232', u'252', u'262'):
                        if medicalTypeCode in (u'211', u'261', u'233', u'244'):
                            medicalTypeCode = u'21'
                        else:
                            medicalTypeCode = u'22'
                    if eventProfileCode in DISP_PROFILE_CODES:
                        svc_key = DISP_KEY
                    elif DOGOVOR_EVENTTYPE_ID and eventTypeId == DOGOVOR_EVENTTYPE_ID:
                        svc_key = DOGOVOR_KEY
                    else:
                        svc_key = typeUsl.upper() if typeUsl else u'прочее'
                else:
                    svc_key = typeUsl.upper() if typeUsl else u'прочее'

                # Пишем в агрегат 'all' и в конкретный тип мед. помощи
                for med_key in [u'all', medicalTypeCode]:
                    if med_key not in reportDict[fin_code]:
                        reportDict[fin_code][med_key] = {}

                    # Пишем в агрегат 'all' и в конкретный тип услуги
                    for sk in [u'all', svc_key]:
                        entry = reportDict[fin_code][med_key].setdefault(
                            sk, {u'pos': {}, u'usl': {}, u'sum': {}, u'cli': {}}
                        )
                        if svc_key not in (u'__disp__', u'__dogovor__'):
                            entry[u'pos'][ym_key] = entry[u'pos'].get(ym_key, 0.0) + visits

                        entry[u'usl'][ym_key] = entry[u'usl'].get(ym_key, 0) + usl
                        entry[u'sum'][ym_key] = entry[u'sum'].get(ym_key, 0.0) + summa
                        client_id_set = {forceInt(cl_id) for cl_id in amountClientId.split(u',') }
                        entry[u'cli'][ym_key] = set(list(entry[u'cli'].get(ym_key, set())) + list(client_id_set))

        query = self.selectData(params)
        processQuery(query)


        beg_date = params.get('begDate')
        end_date = params.get('endDate')
        sorted_months = []
        if beg_date and end_date:
            cur = beg_date.addDays(0)  # копия, чтобы не менять оригинал
            while cur <= end_date:
                sorted_months.append(
                    (forceInt(cur.toString(u'yyyy')), forceInt(cur.toString(u'MM')))
                )
                cur = cur.addMonths(1)

        multi_year = len({ym[0] for ym in sorted_months}) > 1


        def col_label(ym):
            year, month = ym
            name = MONTHS_RU.get(month, forceString(month))
            return u'{} {}'.format(name, year) if multi_year else name


        def fmt(v):
            """Форматирует кол-во: целое без дробной части, иначе 2 знака."""
            if isinstance(v, float):
                return forceString(int(v)) if v == int(v) else forceString(round(v, 2))
            if isinstance(v, set):
                return forceString(len(v))
            return forceString(v)


        def fmt_sum(v):
            """Форматирует сумму всегда с 2 знаками после запятой (0.00 если пусто)."""
            return u'{:.2f}'.format(float(v) if v else 0.0)


        def get_units(svc_key):
            """Диспансеризация и Договор: пациенты+услуги. Остальные: посещения+услуги."""
            if svc_key in (DISP_KEY, DOGOVOR_KEY):
                return [(u'cli', u'пациенты'), (u'usl', u'услуги')]
            return [(u'pos', u'посещения'), (u'usl', u'услуги')]



        def get_profile_order(fin_code, med_key):
            if fin_code == 0:
                return OMS_PROFILE_ORDER
            if med_key == u'22':  # детская поликлиника в платных
                return PAID_PROFILE_ORDER_CHILD
            return PAID_PROFILE_ORDER  # всего и взрослая в платных


        def aggregate_displayed(med_data, svc_keys):
            """Сумма только по тем профилям услуг, которые реально выводятся строками отчёта."""
            result = {u'pos': {}, u'usl': {}, u'sum': {}, u'cli': {}}
            for svc_key in svc_keys:
                entry = med_data.get(svc_key, {})
                for unit_key in (u'pos', u'usl', u'sum', u'cli'):
                    for ym, val in entry.get(unit_key, {}).items():
                        if unit_key != u'cli':
                            result[unit_key][ym] = result[unit_key].get(ym, 0) + val
                        else:
                            result[unit_key][ym] = result[unit_key].get(ym, 0) + len(val)

            return result

        all_rows = []

        for fin_code in [0, 1]:
            fin_block = []

            for med_key in MED_ORDER:
                med_data = reportDict[fin_code].get(med_key, {})
                med_block = []
                profile_order = get_profile_order(fin_code, med_key)
                displayed_svc_keys = [k for k in profile_order if k != u'all']

                for svc_key in profile_order:
                    if svc_key == u'all':
                        svc_entry = aggregate_displayed(med_data, displayed_svc_keys)
                    else:
                        svc_entry = med_data.get(svc_key, {})
                    units = get_units(svc_key)

                    for idx, (unit_key, unit_label) in enumerate(units):
                        qty_data =  svc_entry.get(unit_key, {})
                        # sum_data = dict  → платные, строка посещения/пациенты (всегда показываем число)
                        # sum_data = None  → ОМС или строка услуги (ячейка пустая)
                        if unit_key in (u'pos', u'cli') and fin_code == 1:
                            sum_data = svc_entry.get(u'sum', {})
                        else:
                            sum_data = None

                        row = {
                            u'unit_label': unit_label,
                            u'qty_data': qty_data,
                            u'sum_data': sum_data,
                        }
                        if idx == 0:
                            row[u'svc_label'] = SVC_DISPLAY.get(svc_key, svc_key).capitalize() if SVC_DISPLAY.get(svc_key, svc_key) not in (u'УЗИ', u'Договор с АНОО ВО "Университет"') else SVC_DISPLAY.get(svc_key, svc_key)
                            row[u'svc_rowspan'] = len(units)
                        med_block.append(row)

                med_block[0][u'med_label'] = MED_LABELS.get(med_key, med_key)
                med_block[0][u'med_rowspan'] = len(med_block)
                fin_block.extend(med_block)

            fin_block[0][u'fin_label'] = FIN_LABELS[fin_code]
            fin_block[0][u'fin_rowspan'] = len(fin_block)
            all_rows.extend(fin_block)


        doc = u''
        doc += u'<table border="1" cellSpacing="0" cellPadding="0">'


        doc += u'<tr>'
        doc += u'<td rowspan="2" align="center"><b>Группа услуг</b></td>'
        doc += u'<td rowspan="2" align="center"><b>Взрослая / Детская</b></td>'
        doc += u'<td rowspan="2" align="center"><b>Профили</b></td>'
        doc += u'<td rowspan="2" align="center"><b>Един. изм.</b></td>'
        doc += u'<td colspan="2" align="center"><b>Прогноз 12 мес.</b></td>'
        for ym in sorted_months:
            doc += u'<td align="center" colspan="2"><b>{}</b></td>'.format(col_label(ym))
        doc += u'</tr>'


        doc += u'<tr>'
        for _ in range(len(sorted_months) + 1):
            doc += u'<td align="center"><b>кол-во</b></td><td align="center"><b>сумма</b></td>'
        doc += u'</tr>'

        # Строки данных
        for row in all_rows:
            doc += u'<tr>'

            if u'fin_label' in row:
                doc += u'<td style="padding-left:2px;" rowspan="{}">{}</td>'.format(
                    row[u'fin_rowspan'], row[u'fin_label'])

            if u'med_label' in row:
                doc += u'<td style="padding-left:2px;" rowspan="{}">{}</td>'.format(
                    row[u'med_rowspan'], row[u'med_label'])

            if u'svc_label' in row:
                doc += u'<td style="padding-left:2px;" rowspan="{}">{}</td>'.format(
                    row[u'svc_rowspan'], row[u'svc_label'])

            doc += u'<td align="center">{}</td>'.format(row[u'unit_label'])

            qty_data = row[u'qty_data']
            sum_data = row[u'sum_data']  # None = пустая ячейка; dict = показываем число
            total_qty = sum(len(qty_data.get(ym, 0)) if type(qty_data.get(ym, 0)) == set else qty_data.get(ym, 0) for ym in sorted_months)
            total_sum = sum(sum_data.get(ym, 0.0) for ym in sorted_months) if sum_data is not None else 0.0

            # Итого: кол-во | сумма
            doc += u'<td align="center">{}</td>'.format(fmt(total_qty))
            doc += u'<td align="center">{}</td>'.format(fmt_sum(total_sum) if sum_data is not None else u'')

            # По каждому (год, месяц)
            for ym in sorted_months:
                doc += u'<td align="center">{}</td>'.format(fmt(qty_data.get(ym, 0)))
                doc += u'<td align="center">{}</td>'.format(fmt_sum(sum_data.get(ym, 0.0)) if sum_data is not None else u'')

            doc += u'</tr>'

        doc += u'</table>'
        return doc


class CReportAFT_Forecast12monthSetupDialog(CEconomicAnalisysSetupDialog):
    def __init__(self, parent=None):
        CEconomicAnalisysSetupDialog.__init__(self, parent)
        self.setOrgStructureVisible(False)
        self.setSpecialityVisible(False)
        self.setPersonVisible(False)
        self.setFinanceVisible(False)
        self.setVisibleWidget('lblContract', False)
        self.setVisibleWidget('cmbContract', False)
        self.setVidPomVisible(False)
        self.setRazrNasVisible(False)
        self.settypePayVisible(False)
        self.setPayerVisible(False)
        self.setEventRelegateOrgVisible(False)
        self.setVisibleWidget('lblPurpose', False)
        self.setVisibleWidget('cmbPurpose', False)
        self.setEventTypeVisible(False)
        self.setVisibleWidget('cmbStepECO', False)
        self.setVisibleWidget('lblStepECO', False)
        self.setAgeVisible(False)
        self.setSexVisible(False)
        self.setProfileBedVisible(False)
        self.setDetailToVisible(False)
        self.setGroupByPersonSnilsVisible(False)
        self.setVisibleWidget('lblClient', False)
        self.setVisibleWidget('edtFilterClientId', False)
        self.setVisibleWidget('btnFindClientInfo', False)
        self.setVisibleWidget('chkMKBFilter', False)
        self.setVisibleWidget('edtMKBFrom', False)
        self.setVisibleWidget('edtMKBTo', False)
        self.setCashPaymentsVisible(False)
        self.cbOnlyNotExposed.setVisible(False)
        self.setDateTypeVisible(False)
        self.setNoschetaVisible(False)
        self.setVisibleWidget('lblAccountType', False)
        self.setVisibleWidget('cmbAccountType', False)
        self.setSchetaVisible(False)
        self.setPriceVisible(True)


    def setParams(self, params):
        CEconomicAnalisysSetupDialog.setParams(self, params)


    def params(self):
        result = CEconomicAnalisysSetupDialog.params(self)
        return result



