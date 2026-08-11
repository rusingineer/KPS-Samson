# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature
from Reports.EconomicAnalisys import (colServiceInfis, colServiceName, colKDPD, colUET, colAmount, colSUM, getStmt, \
    colMedicalTypeCode, colObr, colEvent, colMKBCode, colPos, colEventTypeId, colIsFAP, colOrgStructureId, \
    colEventProfileCode, colServiceEndDate, colPayerInfis, colFinanceCode, colClient, colPosTypeHomeUrgent, colPosTypeHomeUrgentAND,
  colPosTypeHomeOnly, getEventTypeMap, getPregnancyServices, getCodesSetAndMap, getSPRPFREFMap, getSpr98Map, getVSbyGroupAccountType)
from Reports.EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase
from library.Utils import forceString, forceInt, forceDouble, forceBool, forceRef, forceDate



class CReportAFT_002(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет для АФТ 002')
        self.otherRecords = []


    @staticmethod
    def selectData(params):
        cols = [colServiceInfis, colServiceName, colKDPD, colUET, colAmount, colSUM, colObr, colEvent,
                colMedicalTypeCode, colMKBCode, colPos, colEventTypeId, colIsFAP, colOrgStructureId,
                colEventProfileCode, colServiceEndDate, colFinanceCode, colPayerInfis, colClient, colPosTypeHomeUrgent, colPosTypeHomeUrgentAND,
                colPosTypeHomeOnly]
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
                        colClient,
                        colPosTypeHomeUrgent,
                        colPosTypeHomeUrgentAND,
                        colPosTypeHomeOnly
                        """
        groupCols = ''
        orderCols = ''

        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params)

        db = QtGui.qApp.db
        return db.query(stmt)



    def getSetupDialog(self, parent):
        result = CReportAFT_002SetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result



    def build(self, params):
        reportData = {0: {}, 1:{}}

        ammountAttachedClients = params.get('ammountAttachedClients', 0)
        coefficient = params.get('coefficient', 0)

        tableColumns = [
            ('5', [u'Группа'], CReportBase.AlignCenter),
            ('5%', [u'№ п.п.'], CReportBase.AlignCenter),
            ('45%', [u'Наименование'], CReportBase.AlignLeft),
            ('5%', [u'Един. изм.'], CReportBase.AlignCenter),
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
            (1, u"Дневной стационар",                                                       [u"Случаи", u"пациенто-день"]),
            (3, u"Неотложная помощь, в том числе:",                                         [u"посещение"]),
            (4, u" - помощь на дому (неотложная)",                                          [u"посещение"]),
            (5, u"Диагностические исследования",                                            [u"услуга"]),
            (6, u"Диспансеризация детей-сирот и детей, оставшихся без попечения родителей", [u"комплексное посещение"]),
            (7, u"Диспансеризация определенных групп взрослого населения",                  [u"комплексное посещение"]),
            (8, u"Диспансеризация граждан репродуктивного возраста",                        [u"комплексное посещение"]),
            (9, u"Диспансерное наблюдение несовершеннолетних",                              [u"посещение"]),
            (10, u"Диспансерное наблюдение взрослых",                                       [u"посещение"]),
            (11, u"Профилактические медицинские осмотры несовершеннолетних",                [u"комплексное посещение"]),
            (12, u"Профилактические медицинские осмотры взрослых",                          [u"комплексное посещение"] ),
            (13, u"Посещения с профилактическими и иными целями, в том числе",              [u"посещение"]),
            (14, u" - помощь на дому (плановая)",                                           [u"посещение"]),
            (15, u"Обращения в связи с заболеваниями",                                      [u"обращение", u"посещение"]),
            (17, u"Поликлиника (прикрепленное население)",                                  [u"человек"]),
        ]

        eventTypeMapping = getEventTypeMap()
        pregnancyServicesMapping =  getPregnancyServices()
        omsCodesMapping, omsCodesSet = getCodesSetAndMap()
        SPRPFREFMapping = getSPRPFREFMap(omsCodesSet)
        spr98Mapping = getSpr98Map(omsCodesSet)

        def processQuery(queryObj, multipl=0):
            db = QtGui.qApp.db
            # Делаем маппинг идентификаторов событий
            eventTypeMap = eventTypeMapping
            # Для определения услуг беременной
            pregnancyServices = pregnancyServicesMapping
            # делаем маппинг кодов омс
            omsCodesMap, omsCodeSet = omsCodesMapping, omsCodesSet
            # делаем маппинг справочника soc_SPRPFREF
            SPRPFREFMap = SPRPFREFMapping
            # делаем маппинг справочника soc_spr98
            spr98Map = spr98Mapping

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
                isPosUrgentOrHomeAND = forceBool(record.value('colPosTypeHomeUrgentAND'))  # Теперь не OR, а AND
                isPosUrgentOrHome = forceBool(record.value('colPosTypeHomeUrgent'))
                isPosOnlyHome = forceBool(record.value('colPosTypeHomeOnly'))

                vs = getVSbyGroupAccountType(VP, eventProfileCode, identifier)

                # обнуление по подушевому финансированию
                exposedSumma = summa
                if payerInfis != '9007' and financeCode == '2':
                    prref = SPRPFREFMap.get((codeMO, vs, VP), [])
                    inprref = False
                    if prref:
                        for begDate, endDate in prref:
                            if begDate <= serviceEndDate and (
                                    not endDate.isNull() and serviceEndDate < endDate.addDays(1) or endDate.isNull()):
                                inprref = True
                                break
                    if not inprref:
                        prref = SPRPFREFMap.get(('', vs, VP), [])
                        if prref:
                            for begDate, endDate in prref:
                                if begDate <= serviceEndDate and (
                                        not endDate.isNull() and serviceEndDate < endDate.addDays(1) or endDate.isNull()):
                                    inprref = True
                                    break
                    inspr98 = False
                    if inprref:
                        spr98 = spr98Map.get((codeMO, code_usl), [])
                        if spr98:
                            for begDate, endDate in spr98:
                                if begDate <= serviceEndDate and (
                                        not endDate.isNull() and serviceEndDate < endDate.addDays(1) or endDate.isNull()):
                                    inspr98 = True
                                    break
                        if not inspr98:
                            spr98 = spr98Map.get(('', code_usl), [])
                            if spr98:
                                for begDate, endDate in spr98:
                                    if begDate <= serviceEndDate and (
                                            not endDate.isNull() and serviceEndDate < endDate.addDays(
                                            1) or endDate.isNull()):
                                        inspr98 = True
                                        break
                        if not inspr98:
                            exposedSumma = 0
                        else:
                            exposedSumma = summa
                    else:
                        exposedSumma = summa

                if VP in ['31', '32', '01', '02', '21', '22', '271', '272', '281', '282'] and identifier is None:
                    recordList.append(
                        [VP, eventId, code_usl, amount, kd, uet, summa, exposedSumma, isObr, mkb, isPos, eventTypeId, isFAP,
                         clientId, isPosUrgentOrHome])
                    if isObr:
                        eventsWithObr.add(eventId)

                # Стационар
                # 1 Дневной стационар
                if VP in ['41', '42', '43']:
                    lineData = reportData[multipl].setdefault(1,[0] * 4)
                    lineData[0] += summa
                    lineData[1] += exposedSumma
                    if code_usl.startswith('G'):
                        lineData[2] += amount
                        lineData[3] += kd

                # Стационар дневного пребывания
                # Диспансеризация пребывающих в стационарных учреждениях детей-сирот и детей, находящихся в трудной жизненной ситуации
                # 6 Диспансеризация детей-сирот и детей, оставшихся без попечения родителей, в том числе усыновленных (удочеренных), принятых под опеку (попечительство), в приемную или патронажную семью
                elif VP in ['252']:
                    lineData = reportData[multipl].setdefault(6,[0] * 4)
                    if summa:
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                # 7 Диспансеризация определенных групп взрослого населения
                elif VP in ['211']:
                    lineData = reportData[multipl].setdefault(7,[0] * 4)
                    if summa:
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                # Углубленная диспансеризация
                # 8 Диспансеризация граждан репродуктивного возраста
                elif VP in ['244']:
                    lineData = reportData[multipl].setdefault(8,[0] * 4)
                    if summa:
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                # 11 Профилактические медицинские осмотры несовершеннолетних
                elif VP in ['262']:
                    lineData = reportData[multipl].setdefault(11,[0] * 4)
                    if summa:
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                # 12 Профилактические медицинские осмотры взрослых
                elif VP in ['261']:
                    lineData = reportData[multipl].setdefault(12,[0] * 4)
                    if summa:
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                # 3 Неотложная помощь
                elif VP in ['241', '242']:
                    lineData = reportData[multipl].setdefault(3,[0] * 4)
                    lineData[0] += summa
                    lineData[1] += exposedSumma
                    if isPos:
                        lineData[2] += amount
                    if isPosUrgentOrHomeAND:
                        # 4 Неотложная помощь - Помощь на дому(неотложная)
                        lineData = reportData[multipl].setdefault(4, [0] * 4)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                    if isPosOnlyHome:
                        # 14 Неотложная помощь - Помощь на дому(плановая)
                        lineData = reportData[multipl].setdefault(14, [0] * 4)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount

                # 5 Диагностические исследования, оплачиваемые по тарифам (лабораторные и инструментальные)
                elif (VP == '80' or identifier) and summa > 0:
                    lineData = reportData[multipl].setdefault(5,[0] * 4)
                    lineData[0] += summa
                    lineData[1] += exposedSumma
                    lineData[2] += amount

            # повторный проход и обработка поликлиники и стоматологии
            for VP, eventId, code_usl, amount, kd, uet, summa, exposedSumma, isObr, mkb, isPos, eventTypeId, isFAP, clientId, isPosUrgentOrHome in recordList:
                if VP in ['01', '02', '21', '22', '271', '272', '281', '282']:
                    # Фельдшерско-акушерские пункты
                    if isFAP:
                        continue
                    # Обращения в связи с заболеваниями
                    elif isObr:
                        lineData = reportData[multipl].setdefault(15, [0] * 4)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        lineData[2] += amount
                    elif eventId in eventsWithObr:
                        if isPos:
                            lineData = reportData[multipl].setdefault(15, [0] * 4)
                            lineData[0] += summa
                            lineData[1] += exposedSumma
                            lineData[3] += amount
                    else:
                        # Посещение с профилактическими и иными целями
                        lineData = reportData[multipl].setdefault(13,[0] * 4)
                        lineData[0] += summa
                        lineData[1] += exposedSumma
                        if isPos or code_usl in ['A26.30.157.001', 'A26.08.013.003', 'A26.08.013.004', 'B03.014.018',
                                                 'B03.032.002']:
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
                            # 9 несовершеннолетних
                            if VP in ['22', '272']:
                                lineData = reportData[multipl].setdefault(9,[0] * 4)
                                lineData[0] += summa
                                lineData[1] += exposedSumma
                                lineData[2] += amount
                            # 10 взрослых
                            elif VP in ['21', '271']:
                                lineData = reportData[multipl].setdefault(10,[0] * 4)
                                lineData[0] += summa
                                lineData[1] += exposedSumma
                                lineData[2] += amount

                        # в том числе разовые посещения по заболеванию

                        # Исследования на ОРВИ и грипп
                        # if code_usl in ['A26.30.157.001', 'A26.08.013.003', 'A26.08.013.004']:
                        #     lineData = reportData[multipl].setdefault(25,[0] * 4)
                        #     lineData[0] += summa
                        #     lineData[1] += exposedSumma
                        #     lineData[2] += amount
                        # # Комплексное исследование больных с хроническими гепатитами В и С
                        # elif code_usl in ['B03.014.018']:
                        #     lineData = reportData[multipl].setdefault(26,[0] * 4)
                        #     lineData[0] += summa
                        #     lineData[1] += exposedSumma
                        #     lineData[2] += amount
                        # # комплексное исследование пренатальной диагностики
                        # elif code_usl in ['B03.032.002']:
                        #     lineData = reportData[multipl].setdefault(27,[0] * 4)
                        #     lineData[0] += summa
                        #     lineData[1] += exposedSumma
                        #     lineData[2] += amount
                        # # Школа сахарного диабета
                        # elif code_usl in ['B04.012.001.010', 'B04.012.001.011', 'B04.012.001.012']:
                        #     lineData = reportData[multipl].setdefault(28,[0] * 4)
                        #     lineData[0] += summa
                        #     lineData[1] += exposedSumma
                        #     lineData[2] += amount
                        # # Школа для больных с артериальной гипертензией
                        # elif code_usl in ['B04.015.001']:
                        #     lineData = reportData[multipl].setdefault(29,[0] * 4)
                        #     lineData[0] += summa
                        #     lineData[1] += exposedSumma
                        #     lineData[2] += amount
                        # # Школа для больных с сердечной недостаточностью
                        # elif code_usl in ['B04.015.002']:
                        #     lineData = reportData[multipl].setdefault(30,[0] * 4)
                        #     lineData[0] += summa
                        #     lineData[1] += exposedSumma
                        #     lineData[2] += amount
                        # # Школа для пациентов с хронической болезнью почек
                        # elif code_usl in ['B04.025.004']:
                        #     lineData = reportData[multipl].setdefault(31,[0] * 4)
                        #     lineData[0] += summa
                        #     lineData[1] += exposedSumma
                        #     lineData[2] += amount
                        # # Школа для больных с бронхиальной астмой
                        # elif code_usl in ['B04.037.003']:
                        #     lineData = reportData[multipl].setdefault(32,[0] * 4)
                        #     lineData[0] += summa
                        #     lineData[1] += exposedSumma
                        #     lineData[2] += amount
                        # # Школа для эндокринологических больных с ожирением
                        # elif code_usl in ['B04.058.001.001']:
                        #     lineData = reportData[multipl].setdefault(33,[0] * 4)
                        #     lineData[0] += summa
                        #     lineData[1] += exposedSumma
                        #     lineData[2] += amount
                        # # Школа обучения пациентов по профилактике остеопороза и его осложнений
                        # elif code_usl in ['B04.058.010']:
                        #     lineData = reportData[multipl].setdefault(34,[0] * 4)
                        #     lineData[0] += summa
                        #     lineData[1] += exposedSumma
                        #     lineData[2] += amount
                        # # Школа для пациентов с избыточной массой тела и ожирением
                        # elif code_usl in ['B05.069.008']:
                        #     lineData = reportData[multipl].setdefault(35,[0] * 4)
                        #     lineData[0] += summa
                        #     lineData[1] += exposedSumma
                        #     lineData[2] += amount


        # Краевые
        params['naselenie'] = 1
        query1 = self.selectData(params)
        processQuery(query1, 0)


        #Инокраевые
        params['naselenie'] = 2
        query2 = self.selectData(params)
        processQuery(query2, 1)

        # Вычитаем из Посещения с профилакт... - ДН несовершен и ДН взрослые
        for mult in [0,1]:
            data = reportData[mult]
            if 13 in data:
                line13 = data[13]
                if 9 in data:
                    line9 = data[9]
                    line13[0] -= line9[0]
                    line13[1] -= line9[1]
                    line13[2] -= line9[2]
                if 10 in data:
                    line10 = data[10]
                    line13[0] -= line10[0]
                    line13[1] -= line10[1]
                    line13[2] -= line10[2]


        for mult in [0, 1]:
            reportData[mult].setdefault(17, [0] * 4)

        # reportData[0][17][0] = forceDouble(coefficient) * forceDouble(ammountAttachedClients)
        reportData[0][17][1] = forceDouble(coefficient) * forceDouble(ammountAttachedClients)

        table = createTable(cursor, tableColumns)


        groups = [
            (0, u"КРАЕВЫЕ"),
            (1, u"ИНОКРАЕВЫЕ"),
            ("total", u"ВСЕГО")
        ]



        for groupIndex, groupName in groups:
            rowNum = 1
            startRow = table.rowCount()

            totalSum = 0
            totalExposed = 0
            totalCount = 0

            for num, name, units in reportRows:

                # ВСЕГО считаем на лету
                if groupIndex == "total":
                    line0 = reportData.get(0, {}).get(num, [0, 0, 0, 0])
                    line1 = reportData.get(1, {}).get(num, [0, 0, 0, 0])
                    line = [
                        line0[0] + line1[0],
                        line0[1] + line1[1],
                        line0[2] + line1[2],
                        line0[3] + line1[3],
                    ]
                else:
                    line = reportData.get(groupIndex, {}).get(num, [0, 0, 0, 0])

                summa = line[0]
                exposed = line[1]
                count = line[2]

                firstRow = True
                localStart = table.rowCount()

                for i, unit in enumerate(units):

                    row = table.addRow()

                    # --- ВАЖНО: номер теперь у КАЖДОЙ строки
                    table.setText(row, 1, forceString(rowNum))
                    rowNum += 1

                    if firstRow:
                        table.setText(row, 2, name)
                        firstRow = False

                        totalSum += summa
                        totalExposed += exposed
                        totalCount += count

                    table.setText(row, 3, unit)

                    if unit:
                        # --- распределяем количество по строкам
                        if i == 0:
                            table.setText(row, 4, forceString(count))
                        elif i == 1 and len(units) > 1:
                            table.setText(row, 4, forceString(line[3]))  # ← было kd

                        # сумма только в первой строке
                        if i == 0:
                            table.setText(row, 5, forceString(round(summa, 2)))
                            table.setText(row, 6, forceString(round(exposed, 2)))

                if len(units) > 1:
                    endRow = table.rowCount() - 1
                    table.mergeCells(localStart, 2, endRow - localStart + 1, 1)

            totalRow = table.addRow()
            table.setText(totalRow, 1, u'')
            table.setText(totalRow, 2, u"ИТОГО")
            table.setText(totalRow, 4, forceString(totalCount))
            table.setText(totalRow, 5, forceString(round(totalSum, 2)))
            table.setText(totalRow, 6, forceString(round(totalExposed, 2)))

            # объединение колонки "Группа"
            endRow = table.rowCount() - 1
            table.setText(startRow, 0, groupName)
            table.mergeCells(startRow, 0, endRow - startRow + 1, 1)
        return doc


class CReportAFT_002SetupDialog(CEconomicAnalisysSetupDialog):
    def __init__(self, parent=None):
        self.edtAmountClients = QtGui.QLineEdit()
        self.edtCoefficient = QtGui.QLineEdit()
        self.edtLayout = QtGui.QGridLayout()
        self.edtLayout.addWidget( QtGui.QLabel(u"Коэффициент"), 0,0, 1,1 )
        self.edtLayout.addWidget(self.edtCoefficient,0,1,1,5 )
        self.edtLayout.addWidget( QtGui.QLabel(u"Кол-во прикрепленного населения"), 1, 0, 1,1 )
        self.edtLayout.addWidget(self.edtAmountClients,1,1,1,5 )
        self.edtLayout.addItem(QtGui.QSpacerItem(20,40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), 2,1)
        self.edtAmountClients.setValidator(QtGui.QIntValidator())
        self.edtCoefficient.setValidator(QtGui.QDoubleValidator())
        self.edtCoefficient.textChanged.connect(self.edtCoefficient_format_text)
        self.edtAmountClients.textChanged.connect(self.edtAmount_format_text)
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
        self.setPriceVisible(False)
        self.setCashPaymentsVisible(False)
        self.gridLayout_4.addLayout(self.edtLayout, self.gridLayout_4.rowCount()-1, 0, 1,5)
        self.cmbScheta.view().setRowHidden(1, True)
        self.cmbScheta.view().setRowHidden(2, True)
        self.cbOnlyNotExposed.setVisible(False)


    def setParams(self, params):
        CEconomicAnalisysSetupDialog.setParams(self, params)
        self.cbOnlyNotExposed.setChecked(False)
        self.cbOnlyNotExposed.setVisible(False)



    def params(self):
        result = CEconomicAnalisysSetupDialog.params(self)
        result['ammountAttachedClients'] = forceInt(self.edtAmountClients.text()) if self.edtAmountClients.text() else 0
        result['coefficient'] = forceDouble(self.edtCoefficient.text()) if self.edtCoefficient.text() else 0
        self.cbOnlyNotExposed.setChecked(False)
        self.cbOnlyNotExposed.setVisible(False)

        return result


    def setVisibilityForDateType(self, datetype):
        if datetype == 1:
            self.setDateEnabled(True)
            self.setNoschetaEnabled(False)
            self.setSchetaEnabled(False)
            self.setAccountTypeEnabled(False)
        elif datetype == 2:
            self.setAccountTypeEnabled(True)
            self.setDateEnabled(True)
            self.setNoschetaEnabled(False)
            self.setSchetaEnabled(True)
        elif datetype == 3:
            self.setAccountTypeEnabled(True)
            self.setSchetaEnabled(True)
            if self.printOnlyByAccountIdList:
                self.grpdatetype.setEnabled(False)
                self.setDateEnabled(False)
                self.setNoschetaEnabled(False)
            else:
                self.setDateEnabled(True)
                self.setNoschetaEnabled(True)


    @pyqtSignature('bool')
    def on_rbDatalech_toggled(self, checked):
        if checked:
            self.setVisibilityForDateType(1)
        self.cbOnlyNotExposed.setChecked(False)
        self.cbOnlyNotExposed.setVisible(False)


    def edtCoefficient_format_text(self, text):
        self.edtCoefficient.setText((text.replace(u',', u'.').replace(u' ', u'')))


    def edtAmount_format_text(self, text):
        self.edtAmountClients.setText((text.replace(u',', u'').replace(u'.', u'').replace(u'-', u'').replace(u' ', u'')))