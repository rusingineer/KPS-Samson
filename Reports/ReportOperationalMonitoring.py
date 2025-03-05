# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.EconomicAnalisys import colServiceInfis, colServiceName, colKDPD, colUET, colAmount, colSUM, getStmt, \
    colMedicalTypeCode, colObr, colEvent, colMKBCode, colPos, colEventTypeId, colIsFAP, colOrgStructureId, \
    colEventProfileCode, colServiceEndDate, colPayerInfis, colFinanceCode, colClient
from Reports.EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase
from library.Utils import forceString, forceInt, forceDouble, forceBool, forceRef, forceDate


class CReportOperationalMonitoring(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Оперативный мониторинг оказания медицинской помощи')

    @staticmethod
    def selectData(params):
        cols = [colServiceInfis, colServiceName, colKDPD, colUET, colAmount, colSUM, colObr, colEvent,
                colMedicalTypeCode, colMKBCode, colPos, colEventTypeId, colIsFAP, colOrgStructureId,
                colEventProfileCode, colServiceEndDate, colFinanceCode, colPayerInfis, colClient]
        colsStmt = u"""select colServiceInfis as code_usl,
                colServiceName as name_usl,
                colAmount as amount,
                round(colUET, 2) as uet,
                colKD as kd,
                round(colSUM, 2) as sum,
                colObr,
                colEvent,
                colMedicalTypeCode,
                colMKBCode,
                colPos,
                colEventTypeId,
                colIsFAP,
                colOrgStructureId,
                colEventProfileCode,
                colServiceEndDate,
                colPayerInfis,
                colFinanceCode,
                colClient
                """
        groupCols = ''
        orderCols = ''

        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params)

        db = QtGui.qApp.db
        return db.query(stmt)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        return result

    def build(self, params):
        reportData = {}
        tableColumns = [
            ('5%',  [u'№ п.п.'], CReportBase.AlignCenter),
            ('50%', [u'Наименование'], CReportBase.AlignLeft),
            ('5%',  [u'Един. изм.'], CReportBase.AlignCenter),
            ('10%', [u'Количество'], CReportBase.AlignRight),
            ('10%', [u'Сумма, руб.'], CReportBase.AlignRight),
            ('10%', [u'Выставлено, руб.'], CReportBase.AlignRight)
        ]

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText('\n'.join(self.getDescription(params)))
        cursor.insertBlock()
        reportRows = [
            (1,  u'Стационар', [u'Случаи', u'койко-день']),
            (2,  u'в т.ч. высокотехнологичная медицинская помощь', [u'Случаи', u'койко-день']),
            (3,  u'Дневной стационар', [u'Случаи', u'пациенто-день']),
            (4,  u'в т.ч. экстракорпоральное оплодотворение', [u'Случаи', u'пациенто-день']),
            (5,  u'Стационар дневного пребывания', [u'Случаи', u'пациенто-день']),
            (6,  u'Диспансеризация пребывающих в стационарных учреждениях детей-сирот и детей, находящихся в трудной жизненной ситуации', [u'комплексное посещение']),
            (7,  u"""Диспансеризация детей-сирот и детей, оставшихся без попечения родителей,
в том числе усыновленных (удочеренных), принятых под опеку (попечительство), в приемную или патронажную семью""", [u'комплексное посещение']),
            (8,  u"Диспансеризация определенных групп взрослого населения", [u'комплексное посещение']),
            (9,  u"Углубленная диспансеризация", [u'комплексное посещение']),
            (10, u"Профилактические медицинские осмотры несовершеннолетних", [u'комплексное посещение']),
            (11, u"Профилактические медицинские осмотры взрослых", [u'комплексное посещение']),
            (12, u"Посещение с профилактическими и иными целями, в том числе:", [u'посещение']),
            (13, u" - разовые посещения по заболеванию", [u'посещение']),
            (14, u" - диспансерное наблюдение несовершеннолетних", [u'посещение']),
            (15, u" - диспансерное наблюдение взрослых", [u'посещение']),
            (16, u" - исследования на ОРВИ и грипп", [u'посещение']),
            (17, u" - комплексное исследование больных с хроническими гепатитами В и С", [u'посещение']),
            (18, u" - комплексное исследование пренатальной диагностики", [u'посещение']),
            (19, u" - школа сахарного диабета", [u'посещение']),
            (20, u"Обращения в связи с заболеваниями", [u'обращение', u'посещение']),
            (21, u"Поликлиника (прикрепленное население)", [u'человек']),
            (22, u"Фельдшерско-акушерские пункты", [u'обращение', u'посещение', u'человек']),
            (23, u"Неотложная помощь", [u'посещение']),
            (24, u"Диагностические исследования, оплачиваемые по тарифам (лабораторные и инструментальные), в том числе:", [u'услуга']),
            (25, u" - магнитно-резонансная томография", [u'услуга']),
            (26, u" - компьютерная томография", [u'услуга']),
            (27, u" - ультразвуковое исследование сердечно-сосудистой системы", [u'услуга']),
            (28, u" - эндоскопические диагностические исследования", [u'услуга']),
            (29, u" - молекулярно-генетические исследования с целью выявления онкологических заболеваний", [u'услуга']),
            (30, u" - гистологические исследования с целью выявления онкологических заболеваний", [u'услуга']),
            (31, u" - исследования на COVID-19", [u'услуга']),
            (32, u"Стоматология (посещение с профилактическими и иными целями)", [u'посещение', u'УЕТ']),
            (33, u"в том числе разовые посещения по заболеванию", [u'посещение', u'УЕТ']),
            (34, u"Стоматология (обращения в связи с заболеваниями)", [u'обращение', u'посещение', u'УЕТ']),
            (35, u"Стоматология", [u'УЕТ'])
        ]

        def processQuery(queryObj):
            db = QtGui.qApp.db
            # Делаем маппинг идентификаторов событий
            eventTypeMap = {}
            stmt = u"""SELECT et.id, eti.value
FROM EventType et
LEFT JOIN EventType_Identification eti ON et.id = eti.master_id AND eti.deleted = 0
LEFT JOIN rbAccountingSystem `as` ON eti.system_id = `as`.id
WHERE `as`.code = 'AccTFOMS' AND et.deleted = 0 AND eti.value IN ('ak', 'am', 'au', 'ae', 'ag', 'ah', 'av')"""
            etQuery = db.query(stmt)
            while etQuery.next():
                record = etQuery.record()
                eventTypeId = forceRef(record.value('id'))
                identifier = forceString(record.value('value'))
                eventTypeMap[eventTypeId] = identifier

            # Для определения услуг беременной
            pregnancyServices = set()
            stmt = u"""SELECT rbService.infis
                         FROM rbService
                         WHERE rbService.name like '%беременной%'"""
            pregnancyQuery = db.query(stmt)
            while pregnancyQuery.next():
                record = pregnancyQuery.record()
                pregnancyServices.add(forceString(record.value('infis')))

            # делаем маппинг кодов омс
            omsCodesMap = {}
            omsCodeSet = set()
            stmt = u"SELECT id, getOMSCode(id) AS omsCode FROM OrgStructure WHERE deleted = 0"
            omsQuery = db.query(stmt)
            while omsQuery.next():
                record = omsQuery.record()
                orgStructureId = forceRef(record.value('id'))
                omsCode = forceString(record.value('omsCode'))
                omsCodeSet.add(omsCode)
                omsCodesMap[orgStructureId] = omsCode

            # делаем маппинг справочника soc_SPRPFREF
            SPRPFREFMap = {}
            CODE_UR = forceString(db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'infisCode'))
            omsCodeSet.add(CODE_UR)
            stmt = u"SELECT * FROM soc_SPRPFREF WHERE CODE_UR = {0}".format(CODE_UR)
            SPRPFREFQuery = db.query(stmt)
            while SPRPFREFQuery.next():
                record = SPRPFREFQuery.record()
                codeMO = forceString(record.value('CODE_MO'))
                vs = forceString(record.value('VS'))
                vp = forceString(record.value('VP'))
                begDate = forceDate(record.value('DATN'))
                endDate = forceDate(record.value('DATO'))
                prref = SPRPFREFMap.setdefault((codeMO, vs, vp), [])
                prref.append((begDate, endDate))

            # делаем маппинг справочника soc_spr98
            spr98Map = {}
            tableSPR98 = db.table('soc_spr98')
            spr98Records = db.getRecordList(tableSPR98, where=[db.joinOr([tableSPR98['code_mo'].inlist(omsCodeSet), tableSPR98['code_mo'].isNull()])])
            for record in spr98Records:
                codeMO = forceString(record.value('code_mo'))
                code = forceString(record.value('code'))
                begDate = forceDate(record.value('begDate'))
                endDate = forceDate(record.value('endDate'))
                spr98 = spr98Map.setdefault((codeMO, code), [])
                spr98.append((begDate, endDate))

            mapSpr13ToGroupAccountType = {'11': 1, '12': 1, '301': 1, '302': 1, '401': 2, '402': 2, '241': 3,
                                          '242': 3, '201': 3, '202': 3, '21': 3, '22': 3, '31': 3, '32': 3,
                                          '60': 3, '111': 3, '112': 3, '01': 3, '02': 3, '281': 3, '282': 3,
                                          '271': 4, '272': 4, '261': 5, '211': 5, '233': 5, '244': 5, '262': 6, '252': 6,
                                          '232': 6, '43': 7, '41': 7, '42': 7, '51': 7, '52': 7, '71': 7, '72': 7,
                                          '90': 7, '411': 7, '422': 7, '511': 7, '522': 7, '801': 8, '802': 8}

            mapGroupAccountTypeToAccountType = {
                1: '2',
                2: 'i',
                3: '2',
                4: 'm',
                5: 'a',  # старые типы реестров по дисп
                6: 'e',  # медосмотры несовершеннолетних
                7: '2',
                8: '2',
                9: 'q',
                10: 'q',
                11: 'a1',  # первый этап дисп
                12: 'a2',  # второй этап дисп
                13: 'a3',  # профосмотры взрослых
                14: 'o',  # ДН
                15: 'o',  # разовые посещения по подушевому
                16: 'ak',  # по компьютерной томографии
                17: 'am',  # по магнитно-резонансной томографии
                18: 'au',  # по ультразвуковому исследованию ССС
                19: 'ae',  # по эндоскопическим диаг. исследованиям
                20: 'ag',  # по мол.-ген. иссл. с целью выявления онк. заб.
                21: 'ah',  # по гист. исследованиям с целью выявления онк. заб.
                22: 'ao',  # по экстракорпоральному оплодотворению
                23: 'av',  # по коронавирусу
                24: '4',  # ДН по полному подушевому
                25: '4',  # разовые посещения по полному подушевому
                26: 'a4',  # по углуб. дисп. взр.нас. I этап
                27: 'a5',  # по углуб. дисп. взр.нас. II этап
                28: 'e',  # Диспансеризация детей-сирот
                29: 'e',  # диспансеризация детей остав-ся без попечения родит,
                30: 'ap',  # по патологоанатомическим вскрытиям
                31: 'a6',  # дисп. для оценки репрод. здоровья I этап
                32: 'a7'  # дисп. для оценки репрод. здоровья II этап
            }

            reportData.setdefault('total', [0] * 3)
            recordList = []
            clientSet = set()
            eventsWithObr = set()
            stacEvents = set()

            while queryObj.next():
                record = queryObj.record()
                VP = forceString(record.value('colMedicalTypeCode'))
                code_usl = forceString(record.value('code_usl'))
                amount = forceInt(record.value('amount'))
                kd = forceInt(record.value('kd'))
                uet = forceDouble(record.value('uet'))
                summa = forceDouble(record.value('sum'))
                isObr = forceBool(record.value('colObr'))
                eventId = forceRef(record.value('colEvent'))
                mkb = forceString(record.value('colMKBCode'))
                isPos = forceBool(record.value('colPos'))
                eventTypeId = forceRef(record.value('colEventTypeId'))
                isFAP = forceBool(record.value('colIsFAP'))
                orgStructureId = forceRef(record.value('colOrgStructureId'))
                eventProfileCode = forceString(record.value('colEventProfileCode'))
                serviceEndDate = forceDate(record.value('colServiceEndDate'))
                codeMO = omsCodesMap.get(orgStructureId, None)
                identifier = eventTypeMap.get(eventTypeId, None)
                payerInfis = forceString(record.value('colPayerInfis'))
                financeCode = forceString(record.value('colFinanceCode'))
                clientId = forceRef(record.value('colClient'))

                groupAccountType = mapSpr13ToGroupAccountType.get(VP)
                if groupAccountType == 5:
                    if eventProfileCode in ['8008', '8014', '8017']:
                        groupAccountType = 11
                    elif eventProfileCode in ['8009', '8015']:
                        groupAccountType = 12
                    elif eventProfileCode == '8011':
                        groupAccountType = 13
                    elif eventProfileCode == '8018':
                        groupAccountType = 26
                    elif eventProfileCode == '8019':
                        groupAccountType = 27
                    elif eventProfileCode == '8020':
                        groupAccountType = 31
                    elif eventProfileCode == '8021':
                        groupAccountType = 32
                elif groupAccountType in [3, 7]:
                    newGroupAccountType = {'ak': 16, 'am': 17, 'au': 18, 'ae': 19, 'ag': 20, 'ah': 21, 'ao': 22, 'av': 23}.get(identifier, None)
                    groupAccountType = newGroupAccountType if newGroupAccountType else groupAccountType
                elif groupAccountType == 6:
                    if VP == '232':  # Диспансеризация детей-сирот
                        groupAccountType = 28
                    elif VP == '252':  # диспансеризация детей остав-ся без попечения родит
                        groupAccountType = 29
                vs = mapGroupAccountTypeToAccountType.get(groupAccountType)

                # обнуление по подушевому финансированию
                exposedSumma = summa
                if payerInfis != '9007' and financeCode == '2':
                    prref = SPRPFREFMap.get((codeMO, vs, VP), [])
                    inprref = False
                    if prref:
                        for begDate, endDate in prref:
                            if begDate <= serviceEndDate and (not endDate.isNull() and serviceEndDate < endDate.addDays(1) or endDate.isNull()):
                                inprref = True
                                break
                    if not inprref:
                        prref = SPRPFREFMap.get(('', vs, VP), [])
                        if prref:
                            for begDate, endDate in prref:
                                if begDate <= serviceEndDate and (not endDate.isNull() and serviceEndDate < endDate.addDays(1) or endDate.isNull()):
                                    inprref = True
                                    break
                    inspr98 = False
                    if inprref:
                        spr98 = spr98Map.get((codeMO, code_usl), [])
                        if spr98:
                            for begDate, endDate in spr98:
                                if begDate <= serviceEndDate and (not endDate.isNull() and serviceEndDate < endDate.addDays(1) or endDate.isNull()):
                                    inspr98 = True
                                    break
                        if not inspr98:
                            spr98 = spr98Map.get(('', code_usl), [])
                            if spr98:
                                for begDate, endDate in spr98:
                                    if begDate <= serviceEndDate and (not endDate.isNull() and serviceEndDate < endDate.addDays(1) or endDate.isNull()):
                                        inspr98 = True
                                        break
                        if not inspr98:
                            exposedSumma = 0
                        else:
                            exposedSumma = summa
                    else:
                        exposedSumma = summa

                if VP in ['31', '32', '01', '02', '21', '22', '271', '272', '281', '282'] and identifier is None:
                    recordList.append([VP, eventId, code_usl, amount, kd, uet, summa, exposedSumma, isObr, mkb, isPos, eventTypeId, isFAP, clientId])
                    if isObr:
                        eventsWithObr.add(eventId)
                lineData = reportData.setdefault('total', [0] * 5)
                lineData[0] += summa
                lineData[1] += exposedSumma

                # Стационар
                if VP in ['11', '12', '301', '302', '401', '402']:
                    lineData = reportData.setdefault(1, [0] * 5)
                    lineData[0] += summa
                    lineData[1] += exposedSumma
                    if code_usl.startswith('G') or code_usl.startswith('V'):
                        if eventId not in stacEvents:
                            lineData[2] += amount
                            stacEvents.add(eventId)
                        lineData[3] += kd

                    # в т.ч. высокотехнологичная медицинская помощь
                    if VP in ['401', '402']:
                        lineData = reportData.setdefault(2, [0] * 5)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        if code_usl.startswith('V'):
                            lineData[2] += amount
                            lineData[3] += kd
                # Дневной стационар
                elif VP in ['41', '42', '43']:
                    lineData = reportData.setdefault(3, [0] * 5)
                    lineData[0] += summa
                    lineData[1] += exposedSumma
                    if code_usl.startswith('G'):
                        lineData[2] += amount
                        lineData[3] += kd
                    # в т.ч. экстракорпоральное оплодотворение
                    if VP in ['43']:
                        lineData = reportData.setdefault(4, [0] * 5)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        if code_usl.startswith('G'):
                            lineData[2] += amount
                            lineData[3] += kd
                # Стационар дневного пребывания
                elif VP in ['51', '52']:
                    lineData = reportData.setdefault(5, [0] * 5)
                    lineData[0] += summa
                    lineData[1] += exposedSumma
                    if code_usl.startswith('G'):
                        lineData[2] += amount
                        lineData[3] += kd
                # Диспансеризация пребывающих в стационарных учреждениях детей-сирот и детей, находящихся в трудной жизненной ситуации
                elif VP in ['232']:
                    lineData = reportData.setdefault(6, [0] * 5)
                    if summa:
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                # Диспансеризация детей-сирот и детей, оставшихся без попечения родителей, в том числе усыновленных (удочеренных), принятых под опеку (попечительство), в приемную или патронажную семью
                elif VP in ['252']:
                    lineData = reportData.setdefault(7, [0] * 5)
                    if summa:
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                # Диспансеризация определенных групп взрослого населения
                elif VP in ['211', '244']:
                    lineData = reportData.setdefault(8, [0] * 5)
                    if summa:
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                # Углубленная диспансеризация
                elif VP in ['233']:
                    lineData = reportData.setdefault(9, [0] * 5)
                    if summa:
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                # Профилактические медицинские осмотры несовершеннолетних
                elif VP in ['262']:
                    lineData = reportData.setdefault(10, [0] * 5)
                    if summa:
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                # Профилактические медицинские осмотры взрослых
                elif VP in ['261']:
                    lineData = reportData.setdefault(11, [0] * 5)
                    if summa:
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                # Неотложная помощь
                elif VP in ['111', '112', '241', '242']:
                    lineData = reportData.setdefault(23, [0] * 5)
                    lineData[0] += summa
                    lineData[1] += exposedSumma
                    if isPos:
                        lineData[2] += amount
                # Диагностические исследования, оплачиваемые по тарифам (лабораторные и инструментальные)
                elif (VP == '80' or identifier) and summa > 0:
                    lineData = reportData.setdefault(24, [0] * 5)
                    lineData[0] += summa
                    lineData[1] += exposedSumma
                    lineData[2] += amount
                    # магнитно-резонансная томография
                    if identifier == 'am':
                        lineData = reportData.setdefault(25, [0] * 5)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                    # компьютерная томография
                    elif identifier == 'ak':
                        lineData = reportData.setdefault(26, [0] * 5)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                    # ультразвуковое исследование сердечно-сосудистой системы
                    elif identifier == 'au':
                        lineData = reportData.setdefault(27, [0] * 5)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                    # эндоскопические диагностические исследования
                    elif identifier == 'ae':
                        lineData = reportData.setdefault(28, [0] * 5)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                    # молекулярно-генетические исследования с целью выявления онкологических заболеваний
                    elif identifier == 'ae':
                        lineData = reportData.setdefault(29, [0] * 5)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                    # гистологические исследования с целью выявления онкологических заболеваний
                    elif identifier == 'ag':
                        lineData = reportData.setdefault(30, [0] * 5)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                    # Исследования на COVID-19
                    elif identifier == 'av':
                        lineData = reportData.setdefault(31, [0] * 5)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount

            # повторный проход и обработка поликлиники и стоматологии
            for VP, eventId, code_usl, amount, kd, uet, summa, exposedSumma, isObr, mkb, isPos, eventTypeId, isFAP, clientId in recordList:
                if VP in ['01', '02', '21', '22', '271', '272', '281', '282']:
                    # Фельдшерско-акушерские пункты
                    if isFAP:
                        clientSet.add(clientId)
                        if isObr:
                            lineData = reportData.setdefault(22, [0] * 5)
                            lineData[2] += amount
                        elif isPos:
                            lineData = reportData.setdefault(22, [0] * 5)
                            lineData[0] += summa
                            lineData[1] += exposedSumma
                            lineData[3] += amount
                    # Обращения в связи с заболеваниями
                    elif isObr:
                        lineData = reportData.setdefault(20, [0] * 5)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                    elif eventId in eventsWithObr:
                        if isPos:
                            lineData = reportData.setdefault(20, [0] * 5)
                            lineData[0] += summa
                            lineData[1] += exposedSumma
                            lineData[3] += amount
                    else:
                        # Посещение с профилактическими и иными целями
                        lineData = reportData.setdefault(12, [0] * 5)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        if isPos or code_usl in ['A26.30.157.001', 'A26.08.013.003', 'A26.08.013.004', 'B03.014.018', 'B03.032.002']:
                            lineData[2] += amount
                        # Диспансерное наблюдение
                        if code_usl in ['B04.001.006', 'B04.008.005', 'B04.009.001', 'B04.010.001', 'B04.014.007',
                                        'B04.015.005',
                                        'B04.023.016', 'B04.026.004', 'B04.028.004', 'B04.029.006', 'B04.031.001',
                                        'B04.031.003',
                                        'B04.050.008', 'B04.053.003', 'B04.058.002', 'B04.001.001', 'B04.008.001',
                                        'B04.014.002',
                                        'B04.015.003', 'B04.023.001', 'B04.026.001', 'B04.027.001', 'B04.028.001',
                                        'B04.029.001',
                                        'B04.029.005', 'B04.040.002', 'B04.046.001', 'B04.047.001', 'B04.047.003',
                                        'B04.047.005',
                                        'B04.050.001', 'B04.053.001', 'B04.057.001', 'B04.058.005']:
                            # несовершеннолетних
                            if VP in ['22', '272']:
                                lineData = reportData.setdefault(14, [0] * 5)
                                lineData[0] += summa
                                lineData[1] += exposedSumma
                                lineData[2] += amount
                            # взрослых
                            elif VP in ['21', '271']:
                                lineData = reportData.setdefault(15, [0] * 5)
                                lineData[0] += summa
                                lineData[1] += exposedSumma
                                lineData[2] += amount
                        # в том числе разовые посещения по заболеванию
                        elif mkb[:1] != 'Z' and isPos and code_usl[:3] in ['B01', 'B02'] and code_usl not in pregnancyServices:
                            lineData = reportData.setdefault(13, [0] * 5)
                            lineData[0] += summa
                            lineData[1] += exposedSumma
                            lineData[2] += amount

                        # Исследования на ОРВИ и грипп
                        if code_usl in ['A26.30.157.001', 'A26.08.013.003', 'A26.08.013.004']:
                            lineData = reportData.setdefault(16, [0] * 5)
                            lineData[0] += summa
                            lineData[1] += exposedSumma
                            lineData[2] += amount
                        # Комплексное исследование больных с хроническими гепатитами В и С
                        elif code_usl in ['B03.014.018']:
                            lineData = reportData.setdefault(17, [0] * 5)
                            lineData[0] += summa
                            lineData[1] += exposedSumma
                            lineData[2] += amount
                        # комплексное исследование пренатальной диагностики
                        elif code_usl in ['B03.032.002']:
                            lineData = reportData.setdefault(18, [0] * 5)
                            lineData[0] += summa
                            lineData[1] += exposedSumma
                            lineData[2] += amount
                        # Школа сахарного диабета
                        elif code_usl in ['B04.012.001.010', 'B04.012.001.011', 'B04.012.001.012']:
                            lineData = reportData.setdefault(19, [0] * 5)
                            lineData[0] += summa
                            lineData[1] += exposedSumma
                            lineData[2] += amount
                elif VP in ['31', '32']:
                    # Стоматология
                    lineData = reportData.setdefault(35, [0] * 5)
                    lineData[0] += summa
                    lineData[1] += exposedSumma
                    lineData[2] += uet
                    # Стоматология (обращения в связи с заболеваниями)
                    if isObr:
                        lineData = reportData.setdefault(34, [0] * 5)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                    elif eventId in eventsWithObr:
                        lineData = reportData.setdefault(34, [0] * 5)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        if isPos:
                            lineData[3] += amount
                        lineData[4] += uet
                    else:
                        # Стоматология (посещение с профилактическими и иными целями)
                        lineData = reportData.setdefault(32, [0] * 5)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        if isPos:
                            lineData[2] += amount
                        lineData[3] += uet
                        # в том числе разовые посещения по заболеванию
                        if mkb[:1] != 'Z':
                            lineData = reportData.setdefault(33, [0] * 5)
                            lineData[0] += summa
                            lineData[1] += exposedSumma
                            if isPos:
                                lineData[2] += amount
                            lineData[3] += uet

            lineData = reportData.setdefault(22, [0] * 5)
            lineData[4] += len(clientSet)

        query = self.selectData(params)
        processQuery(query)

        table = createTable(cursor, tableColumns)
        for reportRow in reportRows:
            num, name, units = reportRow
            row = table.addRow()
            table.setText(row, 0, num)
            table.setText(row, 1, name)
            table.setText(row, 2, units[0])

            if num in reportData:
                reportLine = reportData[num]
            else:
                reportLine = [0.0, 0.0, 0, 0, 0]

            table.setText(row, 3, reportLine[2])
            if name == u"Фельдшерско-акушерские пункты":
                table.setText(row, 4, '0.00')
                table.setText(row, 5, '0.00')
            else:
                table.setText(row, 4, '{:.2f}'.format(reportLine[0]))
                table.setText(row, 5, '{:.2f}'.format(reportLine[1]))
            if len(units) > 1:
                rowNum = row
                i = 2
                for unit in units[1:]:
                    i += 1
                    row = table.addRow()
                    table.setText(row, 2, unit)
                    if unit == u'УЕТ':
                        table.setText(row, 3, '{:.2f}'.format(reportLine[i]))
                    else:
                        table.setText(row, 3, reportLine[i])
                    if name == u"Фельдшерско-акушерские пункты":
                        if i == 3:
                            table.setText(row, 4, reportLine[0])
                            table.setText(row, 5, reportLine[1])
                        else:
                            table.setText(row, 4, '{:.2f}'.format(0.0))
                            table.setText(row, 5, '{:.2f}'.format(0.0))

                table.mergeCells(rowNum, 0, len(units), 1)
                table.mergeCells(rowNum, 1, len(units), 1)
                if name != u"Фельдшерско-акушерские пункты":
                    table.mergeCells(rowNum, 4, len(units), 1)
                    table.mergeCells(rowNum, 5, len(units), 1)
        # итого
        row = table.addRow()
        table.setText(row, 1, u'ИТОГО')
        reportLine = reportData['total']
        table.setText(row, 4, '{:.2f}'.format(reportLine[0]))
        table.setText(row, 5, '{:.2f}'.format(reportLine[1]))

        return doc
