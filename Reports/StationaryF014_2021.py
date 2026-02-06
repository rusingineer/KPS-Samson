# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4                    import QtGui
from PyQt4.QtCore             import QDate, QString, Qt

from library.MapCode          import createMapCodeToRowIdx
from library.Utils            import forceString, forceDate, forceInt, forceRef

from Reports.Report           import normalizeMKB
from Reports.ReportBase       import CReportBase, createTable
from Reports.Utils            import (getDataOrgStructure_HBDS,
                                      getDataOrgStructure,
                                      getStringPropertyForTableName,
                                      getStringPropertyValue,
                                      getStringProperty)

from Events.ActionServiceType import CActionServiceType
from Events.Utils             import getActionTypeIdListByFlatCode
from Reports.StationaryF014   import (MainRows4000,
                                      CStationaryF014,
                                      CStationaryF144000,
                                      CStationaryF144001,
                                      CStationaryF144002,
                                      CStationaryF144100,
                                      Rows4201, Rows4400)


RowsUsers4000 = [
    (u'Всего операций', u'1'),
    (u'в том числе операции на нервной системе из них:', u'2'),
    (u'удаление травматической внутричерепной гематомы, очага ушиба, вдавленного перелома черепа, устранение дефекта черепа и лицевого скелета', u'2.1'),
    (u'операции при сосудистых пороках мозга', u'2.2'),
    (u'из них: на аневризмах', u'2.2.1'),
    (u'из них эндоваскулярное выключение', u'2.2.1.1'),
    (u'на мальформациях', u'2.2.2'),
    (u'из них эндоваскулярное выключение', u'2.2.2.1'),
    (u'операции при церебральном инсульте', u'2.3'),
    (u'из них при геморрагическом инсульте', u'2.3.1'),
    (u'из них открытое удаление гематомы', u'2.3.1.1'),
    (u'при инфаркте мозга', u'2.3.2'),
    (u'из них: краниотомия', u'2.3.2.1'),
    (u'эндоваскулярная тромбоэкстрация', u'2.3.2.2'),
    (u'операции при окклюзионно-стенотических поражениях сосудов мозга', u'2.4'),
    (u'из них: на экстрацеребральных отделах сонных и позвоночных артерий', u'2.4.1'),
    (u'из них: эндартерэктомия, редрессация, реимплантация', u'2.4.1.1'),
    (u'стентирование', u'2.4.1.2'),
    (u'на внутричерепных артериях', u'2.4.2'),
    (u'из них экстраинтракраниальные анастомозы', u'2.4.2.1'),
    (u'стентирование', u'2.4.2.2'),
    (u'удаление опухолей головного, спинного мозга', u'2.5'),
    (u'операции при функциональных расстройствах', u'2.6'),
    (u'из них: при болевых синдромах', u'2.6.1'),
    (u'из них: васкулярная декомпрессия', u'2.6.1.1'),
    (u'при эпилепсии, паркинсонизме, мышечно-тонических расстройствах', u'2.6.2'),
    (u'из них: резекционные и деструктивные операции', u'2.6.2.1'),
    (u'установка стимуляторов', u'2.6.2.2'),
    (u'декомпрессивные, стабилизируюшие операции при позвоночно-спинальной травме', u'2.7'),
    (u'декомпрессивные, стабилизируюшие операции при дегенеративных заболеваниях позвоночника', u'2.8'),
    (u'операции на периферических нервах', u'2.9'),
    (u'ликворошунтируюшие операции', u'2.10'),
    (u'операции при врожденных аномалиях развития центральной нервной системы', u'2.11'),
    (u'операции на эндокринной системе', u'3'),
    (u'из них тиреотомии', u'3.1'),
    (u'операции на органе зрения', u'4'),
    (u'из них: кератопластика', u'4.1'),
    (u'задняя витреоэктомия', u'4.2'),
    (u'транпупиллярная термотерапия', u'4.3'),
    (u'Брахитерапия', u'4.4'),
    (u'операции по поводу: глаукомы', u'4.5'),
    (u'из них с применением шунтов и дренажей', u'4.5.1'),
    (u'Энуклеации', u'4.6'),
    (u'Катаракты', u'4.7'),
    (u'из них методом факоэмульсификации', u'4.7.1'),
    (u'интравитреальное введение ингибитора ангиогенеза', u'4.8'),
    (u'операции на органах уха, горла, носа', u'5'),
    (u'из них на ухе', u'5.1'),
    (u'на миндалинах и аденоидах', u'5.2'),
    (u'операции на органах дыхания', u'6'),
    (u'из них на трахее', u'6.1'),
    (u'Пневмонэктомия', u'6.2'),
    (u'эксплоративная торакотомия', u'6.3'),
    (u'операции на сердце', u'7'),
    (u'из них: на открытом сердце', u'7.1'),
    (u'из них с искусственным кровообращением', u'7.1.2'),
    (u'коррекция врожденных пороков сердца', u'7.2'),
    (u'коррекция приобретенных поражений клапанов сердца', u'7.3'),
    (u'при нарушениях ритма - всего', u'7.4'),
    (u'из них: имплантация кардиостимулятора', u'7.4.1'),
    (u'коррекция тахиаритмий', u'7.4.2'),
    (u'из них катетерных аблаций', u'7.4.2.1'),
    (u'по поводу ишемических болезней сердца', u'7.5'),
    (u'из них: аортокоронарное шунтирование', u'7.5.1'),
    (u'ангиопластика коронарных артерий', u'7.5.2'),
    (u'из них со стентированием', u'7.5.2.1'),
    (u'операции на сосудах', u'8'),
    (u'из них: операции на артериях', u'8.1'),
    (u'из них: на питающих головной мозг', u'8.1.1'),
    (u'из них: каротидные эндартерэктомии', u'8.1.1.1'),
    (u'экстраинтракраниальные анастомозы', u'8.1.1.2'),
    (u'рентгенэндоваскулярные дилятации', u'8.1.1.3'),
    (u'из них со стентированием', u'8.1.1.3.1'),
    (u'на почечных артериях', u'8.1.2'),
    (u'на аорте', u'8.1.3'),
    (u'операции на венах', u'8.2'),
    (u'операции на органах брюшной полости', u'9'),
    (u'из них: на желудке по поводу язвенной болезни', u'9.1'),
    (u'аппендэктомии при хроническом аппендиците', u'9.2'),
    (u'грыжесечение при неущемленной грыже', u'9.3'),
    (u'холецистэктомия при хроническом холецистите', u'9.4'),
    (u'лапаротомия диагностическая', u'9.5'),
    (u'на кишечнике', u'9.6'),
    (u'из них на прямой кишке', u'9.6.1'),
    (u'по поводу геморроя', u'9.7'),
    (u'операции на почках и мочеточниках', u'10'),
    (u'операции на мужских половых органах', u'11'),
    (u'из них операции на предстательной железе', u'11.1'),
    (u'операции по поводу стерилизации мужчин', u'12'),
    (u'операции на женских половых органах', u'13'),
    (u'из них: экстирпация и надвлагалищная ампутация матки', u'13.1'),
    (u'на придатках матки по поводу бесплодия', u'13.2'),
    (u'на яичниках по поводу новообразований', u'13.3'),
    (u'по поводу стерилизации женщин', u'13.4'),
    (u'выскабливание матки (кроме аборта)', u'13.5'),
    (u'акушерские операции', u'14'),
    (u'из них: по поводу внематочной беременности', u'14.1'),
    (u'наложение щипцов', u'14.2'),
    (u'вакуум-экстракция', u'14.3'),
    (u'кесарево сечение в сроке 22 недель беременности и более', u'14.4'),
    (u'кесарево сечение в сроке менее 22 недель беременности', u'14.5'),
    (u'Аборт', u'14.6'),
    (u'Плодоразрушающие', u'14.7'),
    (u'экстирпация и надвлагалищная ампутация матки в сроке 22 недель беременности и более, в родах и после родов', u'14.8'),
    (u'экстирпация и надвлагалищная ампутация матки при прерывании беременности в сроке менее 22 недель беременности или после прерывания', u'14.9'),
    (u'операции на костно-мышечной системе', u'15'),
    (u'из них: корригирующие остеотомии', u'15.1'),
    (u'на челюстно-лицевой области', u'15.2'),
    (u'при травмах костей таза', u'15.3'),
    (u'при около- и внутрисуставных переломах', u'15.4'),
    (u'на позвоночнике', u'15.5'),
    (u'при врожденном вывихе бедра', u'15.6'),
    (u'ампутации и экзартикуляции', u'15.7'),
    (u'эндопротезирование, всего', u'15.8'),
    (u'из него тазобедренного сустава', u'15.8.1'),
    (u'коленного сустава', u'15.8.2'),
    (u'на грудной стенке', u'15.9'),
    (u'из них: торакомиопластика', u'15.9.1'),
    (u'Торакостомия', u'15.9.2'),
    (u'операции на молочной железе', u'16'),
    (u'операции на коже и подкожной клетчатке', u'17'),
    (u'из них операции на челюстно-лицевой области', u'17.1'),
    (u'операции на средостении', u'18'),
    (u'из них операции на вилочковой железе', u'18.1'),
    (u'операции на пищеводе', u'19'),
    (u'операции на лимфатической системе', u'20'),
    (u'прочие операции', u'21'),
]


Rows4100 = [
    (u'Оперировано больных – всего (чел.)', u'1'),
    (u'из них дети до 17 лет включительно', u'2'),
    (u'лица старше трудоспособного возраста', u'3'),
    (u'Из общего числа операций операций (стр. 1, гр. 3 табл. 4000) проведено операций с использованием:\nлазерной аппаратуры', u'4'),
    (u'криогенной аппаратуры', u'5'),
    (u'эндоскопической аппаратуры', u'6'),
    (u'из них: стерилизации женщин', u'7'),
    (u'рентгеновской аппаратуры', u'8'),
]


Rows4200 = [
    (u'на органе зрения (из стр. 4 табл. 4000):', u''),
    (u'из них:\nс помощью микрохирургического оборудования\nв том числе:', u'1'),
    (u'по поводу травмы глаза', u'1.1'),
    (u'по поводу диабетической ретинопатии', u'1.2'),
    (u'по поводу ретинопатии недоношенных', u'1.3'),
    (u'по поводу отслойки сетчатки', u'1.4'),
    (u'с использованием лазерной аппаратуры\nв том числе:', u'2'),
    (u'по поводу диабетической ретинопатии', u'2.1'),
    (u'по поводу ретинопатии недоношенных', u'2.2'),
    (u'на ухе (стр. 5.1 табл. 4000) – слухоулучшающие', u'3'),
    (u'из них кохлеарная имплантация', u'3.1'),
    (u'на желудке по поводу язвенной болезни (стр. 9.1 табл. 4000) – органосохраняющие', u'4'),
]


def getSeniorAges(begDate, today):
    age = 'IF(Client.sex = 1, 60, 55)'
    if begDate:
        if begDate.year() == 2021:
            age = 'IF(Client.sex = 1, 61, 56)'
        elif begDate.year() == 2022:
            age = 'IF(Client.sex = 1, 62, 57)'
        elif begDate.year() == 2023:
            age = 'IF(Client.sex = 1, 62, 57)'
        elif begDate.year() >= 2024:
            age = 'IF(Client.sex = 1, 63, 58)'
    return 'age(Client.birthDate, %s) >= %s' % (today, age)


def getAbleAges(begDate, today):
    age = 'IF(Client.sex = 1, 59, 54)'
    if begDate:
        if begDate.year() == 2021:
            age = 'IF(Client.sex = 1, 60, 55)'
        elif begDate.year() == 2022 or begDate.year() == 2023:
            age = 'IF(Client.sex = 1, 61, 56)'
        elif begDate.year() >= 2024:
            age = 'IF(Client.sex = 1, 62, 57)'
    return 'age(Client.birthDate, %s) BETWEEN 16 AND %s' % (today, age)


def getQuotaTypeWTMP(byFinance=False):
    if byFinance:
        return('(SELECT MAX(QuotaType.class)'
              ' FROM QuotaType'
              ' JOIN ActionType_QuotaType ATQT ON QuotaType.id = ATQT.quotaType_id'
              ' WHERE Action.finance_id = ATQT.finance_id'
                 ' AND QuotaType.deleted = 0'
                 ' AND ATQT.master_id = ActionType.id) AS quotaTypeWTMP')
    return('(IF((SELECT QuotaType.class'
          ' FROM QuotaType'
          ' WHERE QuotaType.id = ActionType.quotaType_id AND QuotaType.deleted = 0'
          ' LIMIT 1) = 0, 1,'
        ' IF((SELECT QuotaType.class'
          ' FROM QuotaType'
          ' INNER JOIN ActionType_QuotaType ON ActionType_QuotaType.quotaType_id = QuotaType.id'
          ' WHERE ActionType_QuotaType.master_id = ActionType.id'
          ' AND QuotaType.deleted = 0'
          ' LIMIT 1) = 0, 1, 0))'
        ' AND (EXISTS(SELECT APCQ.value'
           ' FROM ActionPropertyType AS APT'
           ' INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id'
           ' INNER JOIN ActionProperty_Client_Quoting AS APCQ ON APCQ.id=AP.id'
           ' INNER JOIN Client_Quoting AS CQ ON CQ.id=APCQ.value'
           ' WHERE APT.actionType_id=Action.actionType_id'
           ' AND AP.action_id=Action.id'
           ' AND AP.deleted = 0'
          u" AND APT.typeName = 'Квота пациента' AND APT.deleted=0"
           ' AND CQ.deleted=0 AND CQ.master_id = Client.id))'
        ') AS quotaTypeWTMP')



class CStationaryF0144000_2021(CStationaryF144000):
    def __init__(self, parent):
        CStationaryF144000.__init__(self, parent)


    def getSetupDialog(self, parent):
        result = CStationaryF144000.getSetupDialog(self, parent)
        # result.setQuotaWMPVisible(True)
        return result


    def build(self, params):
        db = QtGui.qApp.db
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        orgStructureId = params.get('orgStructureId', None)
        orgStructureIdList = []
        if orgStructureId:
            orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
        begDate          = params.get('begDate', QDate())
        endDate          = params.get('endDate', QDate())
        financeId        = params.get('financeId', None)
        typeSurgery      = params.get('typeSurgery', 0)
        isNomeclature    = typeSurgery == 0
        isTypeOS         = params.get('isTypeOS', 0)
        isMedicalAidType = params.get('isMedicalAidType', 0)
        selectActionType = params.get('selectActionType', 0)
        existFlatCode    = params.get('existFlatCode', False)
        quotaFinanceWMP  = bool(params.get('quotaFinanceWMP', 0))

        mapMainRows = createMapCodeToRowIdx( [row[2] for row in MainRows4000] )

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'3.Хирургическая работа учреждения\n(4000)')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

        cols = [('18%',[u'Наименование операции', u'', u'', u'1'], CReportBase.AlignLeft),
                ('4%', [u'№ строки', u'', u'', u'2'], CReportBase.AlignLeft),
                ('3%', [u'Число операций, проведенных в стационаре, ед.', u'всего', u'', u'3'], CReportBase.AlignLeft),
                ('3%', [u'', u'из них: детям 0-17 лет включительно', u'0-14 лет включительно', u'4'], CReportBase.AlignLeft),
                ('3%', [u'', u'', u'из гр.4 в возрасте до 1 года', u'5'], CReportBase.AlignLeft),
                ('3%', [u'', u'', u'15-17 лет включительно', u'6'], CReportBase.AlignLeft),
                ('3%', [u'из них: операций с применением высоких медицинских технологий (ВМП), ед.',u'всего', u'', u'7'], CReportBase.AlignLeft),
                ('3%', [u'', u'из них: детям 0-17 лет включительно', u'0-14 лет включительно', u'8'], CReportBase.AlignLeft),
                ('3%', [u'', u'', u'из гр.8 в возрасте до 1 года', u'9'], CReportBase.AlignLeft),
                ('3%', [u'', u'', u'15-17 лет включи-тельно', u'10'], CReportBase.AlignLeft),
                ('3%', [u'Число операций, при которых наблюдались осложнения в стационаре, ед.',u'всего', u'', u'11'], CReportBase.AlignLeft),
                ('3%', [u'', u'из них: детям 0-17 лет включительно', u'0-14 лет включительно', u'12'], CReportBase.AlignLeft),
                ('3%', [u'',u'', u'из гр.12 в возрасте до 1 года', u'13'], CReportBase.AlignLeft),
                ('3%', [u'', u'', u'15-17 лет включительно', u'14'], CReportBase.AlignLeft),
                ('3%', [u'из них после операций, с применением ВМП, ед.',u'всего', u'', u'15'], CReportBase.AlignLeft),
                ('3%', [u'', u'из них: детям 0-17 лет включительно', u'0-14 лет включительно', u'16'], CReportBase.AlignLeft),
                ('3%', [u'',u'', u'из них (из гр.16) в возрасте до 1 года', u'17'], CReportBase.AlignLeft),
                ('3%', [u'', u'', u'15-17 лет включительно', u'18'], CReportBase.AlignLeft),
                ('3%', [u'Умерло оперированных в стационаре, чел.',u'всего', u'', u'19'], CReportBase.AlignLeft),
                ('3%', [u'', u'из них: детям 0-17 лет включительно', u'0-14 лет включительно', u'20'], CReportBase.AlignLeft),
                ('3%', [u'',u'', u'из них (из гр.20) в возрасте до 1 года', u'21'], CReportBase.AlignLeft),
                ('3%', [u'', u'', u'15-17 лет включительно', u'22'], CReportBase.AlignLeft),
                ('3%', [u'из них умерло после операций, проведенных с применением ВМП',u'всего', u'', u'23'], CReportBase.AlignLeft),
                ('3%', [u'', u'из них: детям 0-17 лет включительно', u'0-14 лет включительно', u'24'], CReportBase.AlignLeft),
                ('3%', [u'',u'', u'из них (из гр.24) в возрасте до 1 года', u'25'], CReportBase.AlignLeft),
                ('3%', [u'', u'', u'15-17 лет включительно', u'26'], CReportBase.AlignLeft),
                ('3%', [u'Из гр.3: проведено операций по поводу злокачественных новообразований, ед.', u'', u'', u'27'], CReportBase.AlignLeft),
                ('3%', [u'Из гр.3: направлено материалов на морфологическое исследование, ед.', u'', u'', u'28'], CReportBase.AlignLeft),
            ]

        table = createTable(cursor, cols)
        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 3, 1)
        table.mergeCells(0, 2, 1, 4)
        table.mergeCells(1, 2, 2, 1)
        table.mergeCells(1, 3, 1, 3)
        table.mergeCells(0, 6, 1, 4)
        table.mergeCells(1, 6, 2, 1)
        table.mergeCells(1, 7, 1, 3)
        table.mergeCells(0, 10, 1, 4)
        table.mergeCells(1, 10, 2, 1)
        table.mergeCells(1, 11, 1, 3)
        table.mergeCells(0, 14, 1, 4)
        table.mergeCells(1, 14, 2, 1)
        table.mergeCells(1, 15, 1, 3)
        table.mergeCells(0, 18, 1, 4)
        table.mergeCells(1, 18, 2, 1)
        table.mergeCells(1, 19, 1, 3)
        table.mergeCells(0, 22, 1, 4)
        table.mergeCells(1, 22, 2, 1)
        table.mergeCells(1, 23, 1, 3)
        table.mergeCells(0, 26, 3, 1)
        table.mergeCells(0, 27, 3, 1)

        mapCodeToRowIdx = self.getRowsSurgery(not isNomeclature)
        mapCodesToRowIdx, mapCodeToRowIdxAddition = self.getSurgery(mapMainRows,
                                                                    mapCodeToRowIdx,
                                                                    orgStructureIdList,
                                                                    begDate,
                                                                    endDate,
                                                                    financeId,
                                                                    selectActionType,
                                                                    typeSurgery,
                                                                    isTypeOS=isTypeOS,
                                                                    isMedicalAidType=isMedicalAidType,
                                                                    existFlatCode=existFlatCode,
                                                                    filterQuotaFinance=quotaFinanceWMP)
        keys = mapCodesToRowIdx.keys()
        keys.sort()
        rowSize = 28
        reportMainData = [0] * rowSize
        reportMainData.append(0.0)

        if typeSurgery == 0:  # номенклатурный
            items = mapCodesToRowIdx.get(QString(u''), reportMainData)
            for row, rowDescr in enumerate(RowsUsers4000):
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                for col, item in enumerate(items[:-1]):  # в новом отчете нет последнего столбца
                    if col > 1:
                        if row == 0 or row == len(RowsUsers4000) - 1:
                            table.setText(i, col, forceString(item))
                        else:
                            table.setText(i, col, u'0')
            return doc

        otherOperations = [0] * rowSize
        for values in mapCodeToRowIdxAddition.values():
            for col, val in enumerate(values[:-1]):  # в новом отчете нет последнего столбца
                if col > 1:
                    otherOperations[col] += val

        if typeSurgery == 1:  # пользовательский
            for row, rowDescr in enumerate(RowsUsers4000):
                rowUsers = rowDescr[1]
                if rowUsers == u'1':
                    rowUsers = u''
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                items = mapCodesToRowIdx.get(QString(rowUsers), reportMainData)
                for col, item in enumerate(items[:-1]):  # в новом отчете нет последнего столбца
                    if col > 1:
                        if row == len(RowsUsers4000) - 1:
                            table.setText(i, col, otherOperations[col])
                        else:
                            table.setText(i, col, forceString(item))

        elif typeSurgery == 2:  # пользовательский с детализацией
            i = table.addRow()
            table.setText(i, 0, u'Всего операций')
            table.setText(i, 1, u'1')
            for col, item in enumerate(otherOperations):
                if col > 1:
                    table.setText(i, col, otherOperations[col])
            for values in mapCodeToRowIdxAddition.values():
                i = table.addRow()
                for col, val in enumerate(values[:-1]):  # в новом отчете нет последнего столбца
                    table.setText(i, col, forceString(val))

        return doc


    def getSurgery(self, mapMainRows, mapCodeToRowIdx, orgStructureIdList, begDateTime, endDateTime, financeId, selectActionType, typeSurgery, isTypeOS=0, isMedicalAidType=0, existFlatCode=None, filterQuotaFinance=False):
        mapCodeToRowIdxAddition = {}
        if mapCodeToRowIdx:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            tableClient = db.table('Client')
            tableRBService = db.table('rbService')
            tableEventType = db.table('EventType')
            tableRBMedicalAidType = db.table('rbMedicalAidType')
            tableContract = db.table('Contract')
            tablePerson = db.table('Person')
            tableOrgStructure = db.table('OrgStructure')
            table = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
            table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            eventIdDataList = {}
            records = []
            if selectActionType > 0:
                flatCode = ['received%', 'moving%', 'leaved%', 'leaved%'][selectActionType-1]
                nameProperty = [u'Направлен в отделение', u'Отделение пребывания', u'Отделение', u'Отделение'][selectActionType-1]
                cond = [tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(flatCode)),
                        tableEvent['deleted'].eq(0),
                        tableAction['deleted'].eq(0),
                        tableActionType['deleted'].eq(0),
                        tableClient['deleted'].eq(0),
                        tableEventType['deleted'].eq(0),
                       ]
                socStatusClassId = self.params.get('socStatusClassId', None)
                socStatusTypeId  = self.params.get('socStatusTypeId', None)
                if socStatusClassId or socStatusTypeId:
                    tableClientSocStatus = db.table('ClientSocStatus')
                    if begDateTime:
                        cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                           tableClientSocStatus['endDate'].ge(begDateTime)
                                                          ]),
                                               tableClientSocStatus['endDate'].isNull()
                                              ]))
                    if endDateTime:
                        cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                           tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                          ]),
                                               tableClientSocStatus['begDate'].isNull()
                                              ]))
                    table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
                    if socStatusClassId:
                        cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
                    if socStatusTypeId:
                        cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
                    cond.append(tableClientSocStatus['deleted'].eq(0))
                if isMedicalAidType:
                    table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
                    cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
                if existFlatCode:
                    cond.append(tableActionType['flatCode'].ne(u''))
                if bool(begDateTime):
                    cond.append(tableAction['endDate'].ge(begDateTime))
                if bool(endDateTime):
                    cond.append(tableAction['begDate'].lt(endDateTime.addDays(1)))
                if orgStructureIdList:
                    cond.append(getDataOrgStructure_HBDS(nameProperty, orgStructureIdList, isTypeOS))
                if financeId:
                    cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(financeId), str(financeId)))
                    table = table.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                if selectActionType == 2:
                    eventRecords = db.getRecordList(table, 'Event.id AS eventId, Action.begDate, Action.endDate', cond)
                    for eventRecord in eventRecords:
                        eventId = forceRef(eventRecord.value('eventId'))
                        dateList = eventIdDataList.get(eventId, [])
                        begDate = forceDate(eventRecord.value('begDate'))
                        endDate = forceDate(eventRecord.value('endDate'))
                        if (begDate, endDate) not in dateList:
                            dateList.append((begDate, endDate))
                        eventIdDataList[eventId] = dateList
                    eventIdList = eventIdDataList.keys()
                else:
                    eventIdList = db.getDistinctIdList(table, 'Event.id', cond)
                    idList = set([])
                    if selectActionType == 1:
                        for eventId in eventIdList:
                            idListDescendant = set(db.getDescendants(tableEvent, 'prevEvent_id', eventId))
                            idList |= idListDescendant
                    elif selectActionType == 3:
                        idListParents = set(db.getTheseAndParents(tableEvent, 'prevEvent_id', eventIdList))
                        idList |= idListParents
                    setEventIdList = set(eventIdList)
                    setEventIdList |= idList
                    eventIdList = list(setEventIdList)
                if eventIdList:
                    order = u'ActionType.group_id, %s'%(u'rbService.code' if typeSurgery == 0 else u'ActionType.flatCode')
                    cols = [tableAction['id'].alias('actionId'),
                            tableAction['event_id'],
                            tableAction['amount'].alias('countSurgery'),
                            tableAction['MKB'],
                            tableAction['begDate'],
                            tableAction['endDate'],
                            tableActionType['id'].alias('actionTypeId'),
                            tableActionType['group_id'].alias('groupId'),
                            tableRBService['code'] if typeSurgery == 0 else tableActionType['flatCode'].alias('code'),
                            tableActionType['name'],
                            tableActionType['flatCode'],
                            tableActionType['serviceType']
                        ]

                    cols.append(getQuotaTypeWTMP(filterQuotaFinance))
                    cols.append('age(Client.birthDate, Event.setDate) AS ageClient')
                    cols.append('%s AS countMorphologicalStudy'%(getStringProperty(u'Направление на морфологию', u'(APS.value = \'да\' OR APS.value = \'ДА\' OR APS.value = \'Да\')')))
                    cols.append('%s AS countDeathSurgery'%(getStringProperty(u'Исход операции', u'(APS.value LIKE \'умер%\' OR APS.value LIKE \'смерть%\')')))
                    cols.append('%s AS countComplication'%(getStringProperty(u'Осложнение', u'(APS.value != \'\' OR APS.value != \' \')')))
                    table = tableAction.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
                    table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
                    table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
                    cond = [tableAction['event_id'].inlist(eventIdList),
                            tableEvent['deleted'].eq(0),
                            tableAction['deleted'].eq(0),
                            tableActionType['deleted'].eq(0),
                            tableClient['deleted'].eq(0),
                            tableAction['endDate'].isNotNull()
                            ]
                    if selectActionType == 4:
                        tableEvent_P = db.table('Event').alias('Event_P')
                        tableAction_P = db.table('Action').alias('Action_P')
                        tableActionType_P = db.table('ActionType').alias('ActionType_P')
                        tableRBService_P = db.table('rbService').alias('rbService_P')
                        cols_P = [  tableAction_P['id'].alias('actionId_P'),
                                    tableAction_P['amount'].alias('countSurgery_P'),
                                    tableAction_P['event_id'].alias('event_id_P'),
                                    tableAction_P['begDate'].alias('begDate_P'),
                                    tableAction_P['endDate'].alias('endDate_P'),
                                    tableAction_P['MKB'].alias('MKB_P'),
                                    tableActionType_P['id'].alias('actionTypeId_P'),
                                    tableActionType_P['group_id'].alias('groupId_P'),
                                    tableRBService_P['code'].alias('code_P') if typeSurgery == 0 else tableActionType_P['flatCode'].alias('code_P'),
                                    tableActionType_P['name'].alias('name_P'),
                                    tableActionType['flatCode'].alias('flatCode_P'),
                                    tableActionType_P['serviceType'].alias('serviceType_P')
                                ]
                        if filterQuotaFinance:
                            cols.append(getQuotaTypeWTMP(byFinance=True) + '_P')
                        else:
                            cols_P.append('''(IF((SELECT QuotaType.class
                                               FROM QuotaType
                                               WHERE QuotaType.id = ActionType_P.quotaType_id AND QuotaType.deleted = 0
                                               LIMIT 1) = 0, 1,
                                           IF((SELECT QuotaType.class
                                               FROM QuotaType
                                               INNER JOIN ActionType_QuotaType ON ActionType_QuotaType.quotaType_id = QuotaType.id
                                               WHERE ActionType_QuotaType.master_id = ActionType_P.id
                                               AND QuotaType.deleted = 0
                                               LIMIT 1) = 0, 1, 0))
                                            AND (EXISTS(SELECT APCQ.value
                                                FROM ActionPropertyType AS APT
                                                INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
                                                INNER JOIN ActionProperty_Client_Quoting AS APCQ ON APCQ.id=AP.id
                                                INNER JOIN Client_Quoting AS CQ ON CQ.id=APCQ.value
                                                WHERE APT.actionType_id=Action_P.actionType_id
                                                AND AP.action_id=Action_P.id
                                                AND AP.deleted = 0
                                                AND APT.typeName = 'Квота пациента' AND APT.deleted=0
                                                AND CQ.deleted=0 AND CQ.master_id = Client.id))
                                            ) AS quotaTypeWTMP_P''')

                        cols_P.append('%s AS countMorphologicalStudy_P'%(getStringPropertyForTableName(u'Action_P', u'Направление на морфологию', u'(APS.value = \'да\' OR APS.value = \'ДА\' OR APS.value = \'Да\')')))
                        cols_P.append(u'%s AS countDeathHospital_P'%(getStringPropertyForTableName(u'Action_P', u'Исход операции', u'(APS.value LIKE \'умер%\' OR APS.value LIKE \'смерть%\')')))
                        cols_P.append(u'%s AS countComplication_P'%(getStringPropertyForTableName(u'Action_P', u'Осложнени%', u'(APS.value != \'\' OR APS.value != \' \')')))
                        tableA_F = db.table('Action').alias('A_F')
                        tableE_F = db.table('Event').alias('E_F')
                        condA_F = [u'E_F.id = getFirstEventId(Event.id)',
                                   tableA_F['deleted'].eq(0),
                                   tableE_F['deleted'].eq(0),
                                   tableA_F['actionType_id'].inlist(getActionTypeIdListByFlatCode('received%'))
                                   ]
                        stmtJOINA = db.selectStmt(u'''Event AS E_F INNER JOIN Action AS A_F ON A_F.event_id = E_F.id''', u'A_F.begDate', condA_F)
                        tableA_E = db.table('Action').alias('A_E')
                        tableAT_E = db.table('ActionType').alias('AT_E')
                        condA_E = [tableA_E['deleted'].eq(0),
                                   tableA_E['event_id'].eq(tableEvent_P['id']),
                                   tableA_E['endDate'].isNotNull(),
                                   tableAT_E['deleted'].eq(0),
                                   tableA_E['endDate'].lt(tableAction['endDate'].addDays(1)),
                                   u'DATE(A_E.begDate) >= DATE(('+unicode(stmtJOINA)+u'))'
                                   ]
                        tableAE = tableA_E.innerJoin(tableAT_E, tableAT_E['id'].eq(tableA_E['actionType_id']))
                        condA_E.append(tableAT_E['serviceType'].eq(CActionServiceType.operation))
                        if typeSurgery == 0:
                            tableRB_A = db.table('rbService').alias('RB_A')
                            condRBSA = [tableRB_A['id'].eq(tableAT_E['nomenclativeService_id'])]
                            tableAE = tableAE.innerJoin(tableRB_A, db.joinAnd(condRBSA))
                        table = table.leftJoin(tableEvent_P, db.joinAnd([tableEvent_P['id'].notInlist(eventIdList),
                                                                         tableEvent_P['client_id'].eq(tableClient['id']),
                                                                         tableEvent_P['deleted'].eq(0),
                                                                         tableEvent_P['id'].ne(tableEvent['id']),
                                                                         db.existsStmt(tableAE, condA_E)
                                                                         ]))
                        condJOINAction = [tableAction_P['event_id'].notInlist(eventIdList),
                                          tableAction_P['event_id'].eq(tableEvent_P['id']),
                                          tableAction_P['event_id'].ne(tableEvent['id']),
                                          tableAction_P['endDate'].isNotNull(),
                                          tableAction_P['deleted'].eq(0),
                                          tableEvent_P['deleted'].eq(0),
                                          tableAction_P['endDate'].lt(tableAction['endDate'].addDays(1)),
                                          u'DATE(Action_P.begDate) >= DATE(('+unicode(stmtJOINA)+u'))'
                                          ]
                        table = table.leftJoin(tableAction_P, db.joinAnd(condJOINAction))
                        condJOINAT = [tableAction_P['actionType_id'].eq(tableActionType_P['id']),
                                      tableActionType_P['deleted'].eq(0)
                                      ]
                        condJOINAT.append(tableActionType_P['serviceType'].eq(CActionServiceType.operation))
                        table = table.leftJoin(tableActionType_P, db.joinAnd(condJOINAT))
                        if typeSurgery == 0:
                            condRBS = [tableRBService_P['id'].eq(tableActionType_P['nomenclativeService_id'])]
                            table = table.leftJoin(tableRBService_P, db.joinAnd(condRBS))
                        cols.extend(cols_P)
                        order += u', ActionType_P.group_id, %s'%(u'rbService_P.code' if typeSurgery == 0 else u'ActionType_P.flatCode')
                    socStatusClassId = self.params.get('socStatusClassId', None)
                    socStatusTypeId  = self.params.get('socStatusTypeId', None)
                    if socStatusClassId or socStatusTypeId:
                        tableClientSocStatus = db.table('ClientSocStatus')
                        if begDateTime:
                            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                               tableClientSocStatus['endDate'].ge(begDateTime)
                                                              ]),
                                                   tableClientSocStatus['endDate'].isNull()
                                                  ]))
                        if endDateTime:
                            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                               tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                              ]),
                                                   tableClientSocStatus['begDate'].isNull()
                                                  ]))
                        table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
                        if socStatusClassId:
                            cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
                        if socStatusTypeId:
                            cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
                        cond.append(tableClientSocStatus['deleted'].eq(0))
                    if typeSurgery == 0:
                        table = table.innerJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
                    if selectActionType == 4:
                        cond.append(db.joinOr([tableActionType['serviceType'].eq(CActionServiceType.operation), tableActionType['id'].inlist(getActionTypeIdListByFlatCode('leaved%'))]))
                    else:
                        cond.append(tableActionType['serviceType'].eq(CActionServiceType.operation))
                    records = db.getRecordList(table, cols, cond, order)
            else:
                cols = [tableAction['id'].alias('actionId'),
                        tableAction['event_id'],
                        tableAction['amount'].alias('countSurgery'),
                        tableAction['MKB'],
                        tableAction['begDate'],
                        tableAction['endDate'],
                        tableActionType['id'].alias('actionTypeId'),
                        tableActionType['group_id'].alias('groupId'),
                        tableRBService['code'] if typeSurgery == 0 else tableActionType['flatCode'].alias('code'),
                        tableActionType['name'],
                        tableActionType['flatCode'],
                        tableActionType['serviceType'],
                    ]

                cols.append(getQuotaTypeWTMP(filterQuotaFinance))
                cols.append('age(Client.birthDate, Event.setDate) AS ageClient')
                cols.append('%s AS countMorphologicalStudy'%(getStringProperty(u'Направление на морфологию', u'(APS.value = \'да\' OR APS.value = \'ДА\' OR APS.value = \'Да\')')))
                cols.append('%s AS countDeathSurgery'%(getStringProperty(u'Исход операции', u'(APS.value LIKE \'умер%\' OR APS.value LIKE \'смерть%\')')))
                cols.append('%s AS countComplication'%(getStringProperty(u'Осложнение', u'(APS.value != \'\' OR APS.value != \' \')')))
                table = tableAction.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
                table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
                table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
                table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
                table = table.leftJoin(tablePerson, tableAction['person_id'].eq(tablePerson['id']))
                cond = [tableEvent['deleted'].eq(0),
                        tableEventType['deleted'].eq(0),
                        tableAction['deleted'].eq(0),
                        tableActionType['deleted'].eq(0),
                        tableClient['deleted'].eq(0),
                        tableAction['endDate'].isNotNull()
                        ]
                socStatusClassId = self.params.get('socStatusClassId', None)
                socStatusTypeId  = self.params.get('socStatusTypeId', None)
                if socStatusClassId or socStatusTypeId:
                    tableClientSocStatus = db.table('ClientSocStatus')
                    if begDateTime:
                        cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                           tableClientSocStatus['endDate'].ge(begDateTime)
                                                          ]),
                                               tableClientSocStatus['endDate'].isNull()
                                              ]))
                    if endDateTime:
                        cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                           tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                          ]),
                                               tableClientSocStatus['begDate'].isNull()
                                              ]))
                    table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
                    if socStatusClassId:
                        cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
                    if socStatusTypeId:
                        cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
                    cond.append(tableClientSocStatus['deleted'].eq(0))
                if isMedicalAidType:
                    table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
                    cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
                if existFlatCode:
                    cond.append(tableActionType['flatCode'].ne(u''))
                if bool(begDateTime):
                    cond.append(tableAction['endDate'].ge(begDateTime))
                if bool(endDateTime):
                    cond.append(tableAction['endDate'].lt(endDateTime.addDays(1)))
                if orgStructureIdList:
                    table = table.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))
                    cond.append(tablePerson['deleted'].eq(0))
                    cond.append(tableOrgStructure['deleted'].eq(0))
                    cond.append(tableOrgStructure['id'].inlist(orgStructureIdList))
                    if isTypeOS == 1:
                        cond.append(u' AND OrgStructure.type != 0')
                    elif isTypeOS == 2:
                        cond.append(u' AND (OrgStructure.type = 0 AND (SELECT getOrgStructureIsType(OrgStructure.id)) = 1)')
                if financeId:
                    cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(financeId), str(financeId)))
                    table = table.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                cond.append(tableActionType['serviceType'].eq(CActionServiceType.operation))
                if typeSurgery == 0:
                    table = table.innerJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
                records = db.getRecordList(table, cols, cond, u'ActionType.group_id, %s'%(u'rbService.code' if typeSurgery == 0 else u'ActionType.flatCode'))
            actionIdList = []
            for record in records:
                actionId = forceRef(record.value('actionId'))
                serviceType = forceInt(record.value('serviceType'))
                if actionId and actionId not in actionIdList and serviceType == CActionServiceType.operation:
                    actionIdList.append(actionId)
                    eventId = forceRef(record.value('event_id'))
                    iterationNext = True
                    if selectActionType == 2:
                        begDate = forceDate(record.value('begDate'))
                        endDate = forceDate(record.value('endDate'))
                        actionDateList = eventIdDataList.get(eventId, [])
                        for actionDate in actionDateList:
                            actionBegDate = actionDate[0]
                            actionEndDate = actionDate[1]
                            if endDate > actionBegDate and begDate < actionEndDate:
                                iterationNext = True
                            elif endDate == begDate and (endDate >= actionBegDate and begDate <= actionEndDate):
                                iterationNext = True
                            else:
                                iterationNext = False
                    if iterationNext:
                        countSurgery = forceInt(record.value('countSurgery'))
                        quotaTypeWTMP = forceInt(record.value('quotaTypeWTMP'))
                        ageClient = forceInt(record.value('ageClient'))
                        countDeathSurgery = forceInt(record.value('countDeathSurgery'))
                        countComplication = forceInt(record.value('countComplication'))
                        countMorphologicalStudy = forceInt(record.value('countMorphologicalStudy'))
                        name = forceString(record.value('name'))
                        flatCode = forceString(record.value('flatCode'))
                        code = QString(forceString(record.value('code')))
                        MKBRec = normalizeMKB(forceString(record.value('MKB')))
                        surgeryOncology = True if MKBRec in mapMainRows.keys() else False
                        mapCodeToRowIdx = self.setValueMapCodeToRowIdx(mapCodeToRowIdx, u'', u'', quotaTypeWTMP, ageClient, countDeathSurgery, countComplication, surgeryOncology, countMorphologicalStudy, countSurgery, typeSurgery != 0)
                        codeList = [QString(code)]
                        indexPoint = code.lastIndexOf(u'.', -1, Qt.CaseInsensitive)
                        while indexPoint > -1:
                            code.truncate(indexPoint)
                            codeList.append(QString(code))
                            indexPoint = code.lastIndexOf(u'.', -1, Qt.CaseInsensitive)
                        for code in codeList:
                            if code:
                                codeInDescr = False
                                for row, rowDescr in enumerate(RowsUsers4000):
                                    if code == rowDescr[1]:
                                        codeInDescr = True
                                        break
                                if codeInDescr:
                                    mapCodeToRowIdx = self.setValueMapCodeToRowIdx(mapCodeToRowIdx, name, code, quotaTypeWTMP, ageClient, countDeathSurgery, countComplication, surgeryOncology, countMorphologicalStudy, countSurgery, typeSurgery != 0)
                                else:
                                    if not mapCodeToRowIdxAddition.get(code, None):
                                        mapCodeToRowIdxAddition[code] = (name, code, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0)
                                    mapCodeToRowIdxAddition = self.setValueMapCodeToRowIdx(mapCodeToRowIdxAddition, name, code, quotaTypeWTMP, ageClient, countDeathSurgery, countComplication, surgeryOncology, countMorphologicalStudy, countSurgery, typeSurgery != 0)
                if selectActionType == 4:
                    actionId = forceRef(record.value('actionId_P'))
                    serviceType = forceInt(record.value('serviceType_P'))
                    if actionId and actionId not in actionIdList and serviceType == CActionServiceType.operation:
                        actionIdList.append(actionId)
                        eventId = forceRef(record.value('event_id_P'))
                        iterationNext = True
                        if iterationNext:
                            countSurgery = forceInt(record.value('countSurgery_P'))
                            quotaTypeWTMP = forceInt(record.value('quotaTypeWTMP_P'))
                            ageClient = forceInt(record.value('ageClient'))
                            countDeathSurgery = forceInt(record.value('countDeathSurgery_P'))
                            countComplication = forceInt(record.value('countComplication_P'))
                            countMorphologicalStudy = forceInt(record.value('countMorphologicalStudy_P'))
                            name = forceString(record.value('name_P'))
                            code = QString(forceString(record.value('code_P')))
                            flatCode = forceString(record.value('flatCode_P'))
                            MKBRec = normalizeMKB(forceString(record.value('MKB_P')))
                            surgeryOncology = True if MKBRec in mapMainRows.keys() else False
                            self.setValueMapCodeToRowIdx(mapCodeToRowIdx, u'', u'', quotaTypeWTMP, ageClient, countDeathSurgery, countComplication, surgeryOncology, countMorphologicalStudy, countSurgery, typeSurgery != 0)
                            codeList = [QString(code)]
                            indexPoint = code.lastIndexOf(u'.', -1, Qt.CaseInsensitive)
                            while indexPoint > -1:
                                code.truncate(indexPoint)
                                codeList.append(QString(code))
                                indexPoint = code.lastIndexOf(u'.', -1, Qt.CaseInsensitive)
                            for code in codeList:
                                codeInDescr = False
                                for row, rowDescr in enumerate(RowsUsers4000):
                                    if code == rowDescr[1]:
                                        codeInDescr = True
                                        break
                                if codeInDescr:
                                    mapCodeToRowIdx = self.setValueMapCodeToRowIdx(mapCodeToRowIdx, name, code, quotaTypeWTMP, ageClient, countDeathSurgery, countComplication, surgeryOncology, countMorphologicalStudy, countSurgery, typeSurgery != 0)
                                else:
                                    if not mapCodeToRowIdxAddition.get(code, None):
                                        mapCodeToRowIdxAddition[code] = (name, code, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0)
                                    mapCodeToRowIdxAddition = self.setValueMapCodeToRowIdx(mapCodeToRowIdxAddition, name, code, quotaTypeWTMP, ageClient, countDeathSurgery, countComplication, surgeryOncology, countMorphologicalStudy, countSurgery, typeSurgery != 0)
        return mapCodeToRowIdx, mapCodeToRowIdxAddition



class CStationaryF144001_2021(CStationaryF144001):
    def __init__(self, parent):
        CStationaryF144001.__init__(self, parent)
        self.setTitle(u'3.1.Хирургическая работа организации\n(лица старше трудоспособного возраста)\n(4001)')


    def getSetupDialog(self, parent):
        result = CStationaryF144001.getSetupDialog(self, parent)
        # result.setQuotaWMPVisible(True)
        return result


    def build(self, params):
        db = QtGui.qApp.db
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        orgStructureId = params.get('orgStructureId', None)
        orgStructureIdList = []
        if orgStructureId:
            orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
        begDate         = params.get('begDate', QDate())
        endDate         = params.get('endDate', QDate())
        financeId       = params.get('financeId', None)
        typeSurgery     = params.get('typeSurgery', 0)
        isNomeclature   = typeSurgery == 0
        selectActionType = params.get('selectActionType', 0)
        isMedicalAidType = params.get('isMedicalAidType', 0)
        isTypeOS        = params.get('isTypeOS', 0)
        quotaFinanceWMP = bool(params.get('quotaFinanceWMP', 0))

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

        cols = [('23%', [u'Наименование операции', u'', u'', u'1'], CReportBase.AlignLeft),
                ('5%',  [u'№ строки', u'', u'', u'2'], CReportBase.AlignLeft),
                ('12%', [u'Число операций, проведенных в стационаре, ед', u'всего', u'(из гр.3 т.4000)', u'3'], CReportBase.AlignLeft),
                ('12%', [u'', u'из них: с применением высоких медицинских технологий (ВМТ)', u'(из гр.7 т.4000)', u'4'], CReportBase.AlignLeft),
                ('12%', [u'Число операций, при которых наблюдались осложнения в стационаре, ед',u'всего', u'(из гр.11 т.4000)', u'5'], CReportBase.AlignLeft),
                ('12%', [u'', u'из них: после операций с применением ВМТ', u'(из гр.15 т.4000)', u'6'], CReportBase.AlignLeft),
                ('12%', [u'Умерло оперированных в стационаре, ед', u'всего', u'(из гр.19 т.4000)', u'7'], CReportBase.AlignLeft),
                ('12%', [u'', u'из них умерло: после операций проведённых с ВМТ', u'(из гр.23 т.4000)', u'8'], CReportBase.AlignLeft),
        ]
        table = createTable(cursor, cols)
        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 3, 1)
        table.mergeCells(0, 2, 1, 2)
        table.mergeCells(0, 4, 1, 2)
        table.mergeCells(0, 6, 1, 2)

        mapCodeToRowIdx = self.getRowsSurgery(not isNomeclature)
        mapCodesToRowIdx, mapCodeToRowIdxAddition = self.getSurgery(mapCodeToRowIdx,
                                                                    orgStructureIdList,
                                                                    begDate,
                                                                    endDate,
                                                                    financeId,
                                                                    typeSurgery,
                                                                    selectActionType,
                                                                    isTypeOS=isTypeOS,
                                                                    isMedicalAidType=isMedicalAidType,
                                                                    filterQuotaFinance=quotaFinanceWMP)
        keys = mapCodesToRowIdx.keys()
        keys.sort()
        rowSize = 8
        reportMainData = [0] * rowSize

        if typeSurgery == 0:  # номенклатурный
            items = mapCodesToRowIdx.get(QString(u''), reportMainData)
            for row, rowDescr in enumerate(RowsUsers4000):
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                for col, item in enumerate(items):
                    if col > 1:
                        if row == 0 or row == len(RowsUsers4000) - 1:
                            table.setText(i, col, forceString(item))
                        else:
                            table.setText(i, col, u'0')
            return doc

        otherOperations = [0] * rowSize
        for values in mapCodeToRowIdxAddition.values():
            for col, val in enumerate(values):
                if col > 1:
                    otherOperations[col] += val

        if typeSurgery == 1:  # пользовательский
            for row, rowDescr in enumerate(RowsUsers4000):
                rowUsers = rowDescr[1]
                if rowUsers == u'1':
                    rowUsers = u''
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                items = mapCodesToRowIdx.get(QString(rowUsers), reportMainData)
                for col, item in enumerate(items):
                    if col > 1:
                        if row == len(RowsUsers4000) - 1:
                            table.setText(i, col, otherOperations[col])
                        else:
                            table.setText(i, col, forceString(item))

        elif typeSurgery == 2:  # пользовательский с детализацией
            i = table.addRow()
            table.setText(i, 0, u'Всего операций')
            table.setText(i, 1, u'1')
            for col, item in enumerate(otherOperations):
                if col > 1:
                    table.setText(i, col, otherOperations[col])
            for values in mapCodeToRowIdxAddition.values():
                i = table.addRow()
                for col, val in enumerate(values):
                    table.setText(i, col, forceString(val))

        return doc


    def ageSelector(self, begDate, today='Event.setDate'):
        return getSeniorAges(begDate, today)


    def getSurgery(self, mapCodeToRowIdx, orgStructureIdList, begDateTime, endDateTime, financeId, typeSurgery, selectActionType, isTypeOS=0, isMedicalAidType=0, filterQuotaFinance=False):
        def setValueMapCodeToRowIdx(mapCodeToRowIdx, code, quotaTypeWTMP, ageClient, countDeathSurgery, countComplication, countSurgery):
            if mapCodeToRowIdx.get(code, None):
                items = mapCodeToRowIdx[code]
                valueName = items[0]
                valueRow = items[1]
                valueSurgery = items[2]
                valueSurgeryWTMP = items[3]
                valueComplication = items[4]
                valueComplicationWTMP = items[5]
                valueDeath = items[6]
                valueDeathWTMP = items[7]
                valueSurgery += countSurgery
                if quotaTypeWTMP:
                    valueSurgeryWTMP += countSurgery
                if countComplication:
                    valueComplication += countSurgery
                if countComplication and quotaTypeWTMP:
                    valueComplicationWTMP += countSurgery
                if countDeathSurgery:
                    valueDeath += 1
                if countDeathSurgery and quotaTypeWTMP:
                    valueDeathWTMP += 1

                mapCodeToRowIdx[code] = (valueName, valueRow, valueSurgery, valueSurgeryWTMP, valueComplication, valueComplicationWTMP,
                                         valueDeath, valueDeathWTMP)
            return mapCodeToRowIdx

        if mapCodeToRowIdx:
            mapCodeToRowIdxAddition = {}
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            tableClient = db.table('Client')
            tableRBService = db.table('rbService')
            tableEventType = db.table('EventType')
            tableRBMedicalAidType = db.table('rbMedicalAidType')
            tableContract = db.table('Contract')
            tablePerson = db.table('Person')
            table = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
            table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            eventIdDataList = {}
            records = []
            if selectActionType > 0:
                flatCode = ['received%', 'moving%', 'leaved%'][selectActionType-1]
                nameProperty = [u'Направлен в отделение', u'Отделение пребывания', u'Отделение'][selectActionType-1]
                cond = [tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(flatCode)),
                        tableEvent['deleted'].eq(0),
                        tableAction['deleted'].eq(0),
                        tableActionType['deleted'].eq(0),
                        tableClient['deleted'].eq(0),
                        tableEventType['deleted'].eq(0)
                        ]
                socStatusClassId = self.params.get('socStatusClassId', None)
                socStatusTypeId  = self.params.get('socStatusTypeId', None)
                if socStatusClassId or socStatusTypeId:
                    tableClientSocStatus = db.table('ClientSocStatus')
                    if begDateTime:
                        cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                           tableClientSocStatus['endDate'].ge(begDateTime)
                                                          ]),
                                               tableClientSocStatus['endDate'].isNull()
                                              ]))
                    if endDateTime:
                        cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                           tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                          ]),
                                               tableClientSocStatus['begDate'].isNull()
                                              ]))
                    table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
                    if socStatusClassId:
                        cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
                    if socStatusTypeId:
                        cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
                    cond.append(tableClientSocStatus['deleted'].eq(0))
                if isMedicalAidType:
                    table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
                    cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
                if bool(begDateTime):
                    cond.append(tableAction['endDate'].ge(begDateTime))
                if bool(endDateTime):
                    cond.append(tableAction['begDate'].lt(endDateTime.addDays(1)))
                if orgStructureIdList:
                    cond.append(getDataOrgStructure_HBDS(nameProperty, orgStructureIdList, isTypeOS))
                cond.append(tableClient['sex'].ne(0))
                cond.append(self.ageSelector(begDateTime))
                if financeId:
                    cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(financeId), str(financeId)))
                    table = table.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                if selectActionType == 2:
                    eventRecords = db.getRecordList(table, 'Event.id AS eventId, Action.begDate, Action.endDate', cond)
                    for eventRecord in eventRecords:
                        eventId = forceRef(eventRecord.value('eventId'))
                        dateList = eventIdDataList.get(eventId, [])
                        begDate = forceDate(eventRecord.value('begDate'))
                        endDate = forceDate(eventRecord.value('endDate'))
                        if (begDate, endDate) not in dateList:
                            dateList.append((begDate, endDate))
                        eventIdDataList[eventId] = dateList
                    eventIdList = eventIdDataList.keys()
                else:
                    eventIdList = db.getDistinctIdList(table, 'Event.id', cond)
                    idList = set([])
                    if selectActionType == 1:
                        for eventId in eventIdList:
                            idListDescendant = set(db.getDescendants(tableEvent, 'prevEvent_id', eventId))
                            idList |= idListDescendant
                    elif selectActionType == 3:
                        idListParents = set(db.getTheseAndParents(tableEvent, 'prevEvent_id', eventIdList))
                        idList |= idListParents
                    setEventIdList = set(eventIdList)
                    setEventIdList |= idList
                    eventIdList = list(setEventIdList)
                if eventIdList:
                    cols = [tableAction['id'].alias('actionId'),
                            tableAction['event_id'],
                            tableAction['amount'].alias('countSurgery'),
                            tableAction['MKB'],
                            tableAction['begDate'],
                            tableAction['endDate'],
                            tableActionType['id'].alias('actionTypeId'),
                            tableActionType['group_id'].alias('groupId'),
                            tableRBService['code'] if typeSurgery == 0 else tableActionType['flatCode'].alias('code'),
                            tableActionType['name']
                            ]
                    cols.append(getQuotaTypeWTMP(filterQuotaFinance))
                    cols.append('age(Client.birthDate, Event.setDate) AS ageClient')
                    cols.append('%s AS countMorphologicalStudy'%(getStringProperty(u'Направление на морфологию', u'(APS.value = \'да\' OR APS.value = \'ДА\' OR APS.value = \'Да\')')))
                    cols.append('%s AS countDeathSurgery'%(getStringProperty(u'Исход операции', u'(APS.value LIKE \'умер%\' OR APS.value LIKE \'смерть%\')')))
                    cols.append('%s AS countComplication'%(getStringProperty(u'Осложнение', u'(APS.value != \'\' OR APS.value != \' \')')))
                    table = tableAction.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
                    table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
                    table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
                    cond = [tableAction['event_id'].inlist(eventIdList),
                                  tableEvent['deleted'].eq(0),
                                  tableAction['deleted'].eq(0),
                                  tableActionType['deleted'].eq(0),
                                  tableClient['deleted'].eq(0),
                                  tableAction['endDate'].isNotNull()
                                ]
                    socStatusClassId = self.params.get('socStatusClassId', None)
                    socStatusTypeId  = self.params.get('socStatusTypeId', None)
                    if socStatusClassId or socStatusTypeId:
                        tableClientSocStatus = db.table('ClientSocStatus')
                        if begDateTime:
                            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                               tableClientSocStatus['endDate'].g(begDateTime)
                                                              ]),
                                                   tableClientSocStatus['endDate'].isNull()
                                                  ]))
                        if endDateTime:
                            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                               tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                              ]),
                                                   tableClientSocStatus['begDate'].isNull()
                                                  ]))
                        table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
                        if socStatusClassId:
                            cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
                        if socStatusTypeId:
                            cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
                        cond.append(tableClientSocStatus['deleted'].eq(0))
                    cond.append(tableActionType['serviceType'].eq(CActionServiceType.operation))
                    if typeSurgery == 0:
                        table = table.innerJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
                    records = db.getRecordList(table, cols, cond, u'ActionType.group_id, %s'%(u'rbService.code' if typeSurgery == 0 else u'ActionType.flatCode'))
            else:
                cols = [tableAction['id'].alias('actionId'),
                        tableAction['event_id'],
                        tableAction['amount'].alias('countSurgery'),
                        tableAction['MKB'],
                        tableAction['begDate'],
                        tableAction['endDate'],
                        tableActionType['id'].alias('actionTypeId'),
                        tableActionType['group_id'].alias('groupId'),
                        tableRBService['code'] if typeSurgery == 0 else tableActionType['flatCode'].alias('code'),
                        tableActionType['name']
                        ]

                cols.append(getQuotaTypeWTMP(filterQuotaFinance))
                cols.append('age(Client.birthDate, Event.setDate) AS ageClient')
                cols.append('%s AS countMorphologicalStudy'%(getStringProperty(u'Направление на морфологию', u'(APS.value = \'да\' OR APS.value = \'ДА\' OR APS.value = \'Да\')')))
                cols.append('%s AS countDeathSurgery'%(getStringProperty(u'Исход операции', u'(APS.value LIKE \'умер%\' OR APS.value LIKE \'смерть%\')')))
                cols.append('%s AS countComplication'%(getStringProperty(u'Осложнение', u'(APS.value != \'\' OR APS.value != \' \')')))
                table = tableAction.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
                table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
                table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
                table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
                table = table.leftJoin(tablePerson, tableAction['person_id'].eq(tablePerson['id']))
                cond = [tableEvent['deleted'].eq(0),
                              tableEventType['deleted'].eq(0),
                              tableAction['deleted'].eq(0),
                              tableActionType['deleted'].eq(0),
                              tableClient['deleted'].eq(0),
                              tableAction['endDate'].isNotNull()
                            ]
                cond.append(tableClient['sex'].ne(0))
                cond.append(self.ageSelector(begDateTime))
                socStatusClassId = self.params.get('socStatusClassId', None)
                socStatusTypeId  = self.params.get('socStatusTypeId', None)
                if socStatusClassId or socStatusTypeId:
                    tableClientSocStatus = db.table('ClientSocStatus')
                    if begDateTime:
                        cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                           tableClientSocStatus['endDate'].ge(begDateTime)
                                                          ]),
                                               tableClientSocStatus['endDate'].isNull()
                                              ]))
                    if endDateTime:
                        cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                           tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                          ]),
                                               tableClientSocStatus['begDate'].isNull()
                                              ]))
                    table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
                    if socStatusClassId:
                        cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
                    if socStatusTypeId:
                        cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
                    cond.append(tableClientSocStatus['deleted'].eq(0))
                if isMedicalAidType:
                    table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
                    cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
                if bool(begDateTime):
                    cond.append(tableAction['endDate'].ge(begDateTime))
                if bool(endDateTime):
                    cond.append(tableAction['endDate'].lt(endDateTime.addDays(1)))
                if orgStructureIdList:
                    tableOrgStructure = db.table('OrgStructure')
                    table = table.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))
                    cond.append(tablePerson['deleted'].eq(0))
                    cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
                    cond.append(tableOrgStructure['deleted'].eq(0))
                    cond.append(tableOrgStructure['id'].inlist(orgStructureIdList))
                    if isTypeOS == 1:
                        cond.append(u' AND OrgStructure.type != 0')
                    elif isTypeOS == 2:
                        cond.append(u' AND (OrgStructure.type = 0 AND (SELECT getOrgStructureIsType(OrgStructure.id)) = 1)')
                if financeId:
                    cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(financeId), str(financeId)))
                    table = table.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                cond.append(tableActionType['serviceType'].eq(CActionServiceType.operation))
                if typeSurgery == 0:
                    table = table.innerJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
                records = db.getRecordList(table, cols, cond, u'ActionType.group_id, %s'%(u'rbService.code' if typeSurgery == 0 else u'ActionType.flatCode'))
            for record in records:
                eventId = forceRef(record.value('event_id'))
                iterationNext = True
                if selectActionType == 2:
                    begDate = forceDate(record.value('begDate'))
                    endDate = forceDate(record.value('endDate'))
                    actionDateList = eventIdDataList.get(eventId, [])
                    for actionDate in actionDateList:
                        actionBegDate = actionDate[0]
                        actionEndDate = actionDate[1]
                        if endDate > actionBegDate and begDate < actionEndDate:
                            iterationNext = True
                        elif endDate == begDate and (endDate >= actionBegDate and begDate <= actionEndDate):
                            iterationNext = True
                        else:
                            iterationNext = False
                if iterationNext:
                    countSurgery = forceInt(record.value('countSurgery'))
                    quotaTypeWTMP = forceInt(record.value('quotaTypeWTMP'))
                    ageClient = forceInt(record.value('ageClient'))
                    countDeathSurgery = forceInt(record.value('countDeathSurgery'))
                    countComplication = forceInt(record.value('countComplication'))
                    name = forceString(record.value('name'))
                    code = QString(forceString(record.value('code')))
                    setValueMapCodeToRowIdx(mapCodeToRowIdx, u'', quotaTypeWTMP, ageClient, countDeathSurgery, countComplication, countSurgery)
                    codeList = [QString(code)]
                    indexPoint = code.lastIndexOf(u'.', -1, Qt.CaseInsensitive)
                    while indexPoint > -1:
                        code.truncate(indexPoint)
                        codeList.append(QString(code))
                        indexPoint = code.lastIndexOf(u'.', -1, Qt.CaseInsensitive)
                    for code in codeList:
                        if code:
                            codeInDescr = False
                            if typeSurgery != 2:
                                for row, rowDescr in enumerate(RowsUsers4000):
                                    if code == rowDescr[1]:
                                        codeInDescr = True
                                        break
                            if typeSurgery != 2 and codeInDescr:
                                mapCodeToRowIdx = setValueMapCodeToRowIdx(mapCodeToRowIdx, code, quotaTypeWTMP, ageClient, countDeathSurgery, countComplication, countSurgery)
                            else:
                                if not mapCodeToRowIdxAddition.get(code, None):
                                    mapCodeToRowIdxAddition[code] = (name, code, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0)
                                mapCodeToRowIdxAddition = setValueMapCodeToRowIdx(mapCodeToRowIdxAddition, code, quotaTypeWTMP, ageClient, countDeathSurgery, countComplication, countSurgery)
        return mapCodeToRowIdx, mapCodeToRowIdxAddition



class CStationaryF144001A_2021(CStationaryF144001_2021):
    def __init__(self, parent):
        CStationaryF144001_2021.__init__(self, parent)
        self.setTitle(u'Хирургическая работа организации\n(лица трудоспособного возраста)\n(4001а)')

    def ageSelector(self, begDate, today='Event.setDate'):
        return getAbleAges(begDate, today)



class CStationaryF144002_2021(CStationaryF144002):
    def __init__(self, parent):
        CStationaryF144002.__init__(self, parent)


    def getSetupDialog(self, parent):
        result = CStationaryF144002.getSetupDialog(self, parent)
        # result.setQuotaWMPVisible(True)
        return result


    def getRowsChildren4002(self, orgStructureIdList, begDateTime, endDateTime, isHospital=None):
        db = QtGui.qApp.db
        tableEvent      = db.table('Event')
        tableAction     = db.table('Action')
        tableActionType = db.table('ActionType')
        tableClient     = db.table('Client')
        tableRBService  = db.table('rbService')
        tableEventType  = db.table('EventType')
        tableRBMedicalAidType = db.table('rbMedicalAidType')

        socStatusClassId = self.params.get('socStatusClassId', None)
        socStatusTypeId  = self.params.get('socStatusTypeId', None)
        # filterQuotaFinance = bool(self.stationaryF14SetupDialog.cmbQuotaFinanceWMP.currentIndex())
        filterQuotaFinance = False
        selectActionType = self.params.get('selectActionType', 0)

        flatCode = ['received%', 'received%', 'moving%', 'leaved%'][selectActionType]
        nameProperty = [u'Направлен в отделение', u'Направлен в отделение', u'Отделение пребывания', u'Отделение'][selectActionType]

        table = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
        table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))

        cond = [tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(flatCode)),
                tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableEventType['deleted'].eq(0),
                ]

        if socStatusClassId or socStatusTypeId:
            tableClientSocStatus = db.table('ClientSocStatus')
            if begDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                   tableClientSocStatus['endDate'].ge(begDateTime)
                                                  ]),
                                       tableClientSocStatus['endDate'].isNull()
                                      ]))
            if endDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                   tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                  ]),
                                       tableClientSocStatus['begDate'].isNull()
                                      ]))
            table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
            if socStatusClassId:
                cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
            if socStatusTypeId:
                cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
            cond.append(tableClientSocStatus['deleted'].eq(0))

        cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
        cond.append('age(Client.birthDate, Event.setDate) <= 1')

        joinOr1 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNull()])
        joinOr2 = db.joinAnd([tableAction['begDate'].isNotNull(),
                              tableAction['begDate'].ge(begDateTime),
                              tableAction['begDate'].lt(endDateTime.addDays(1))])

        joinOr3 = db.joinAnd([tableAction['begDate'].isNull(),
                              tableAction['endDate'].isNotNull(),
                              tableAction['endDate'].ge(begDateTime)])

        joinOr4 = db.joinAnd([tableAction['begDate'].isNotNull(),
                              tableAction['begDate'].lt(begDateTime.addDays(1)),
                              db.joinOr([tableAction['endDate'].isNull(),
                                         tableAction['endDate'].ge(begDateTime)])
                              ])
        cond.append(db.joinOr([joinOr1, joinOr2, joinOr3, joinOr4]))

        if orgStructureIdList:
            cond.append(getDataOrgStructure(nameProperty, orgStructureIdList))
        eventIdList = db.getDistinctIdList(table, 'Event.id', cond)
        if eventIdList:
            cols = [tableAction['id'].alias('actionId'),
                    tableAction['event_id'],
                    tableClient['birthGestationalAge'],
                    tableAction['MKB'],
                   ]
            # cols.append(getQuotaTypeWTMP(filterQuotaFinance))
            cols.append('%s AS countDeathSurgery'%(getStringProperty(u'Исход операции', u"(APS.value LIKE 'умер%' OR APS.value LIKE 'смерть%')")))
            cols.append('%s AS countComplication'%(getStringProperty(u'Осложнение', u"(APS.value != '' OR APS.value != ' ')")))

            table = tableAction.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
            table = table.innerJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
            table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            cond = [tableAction['event_id'].inlist(eventIdList),
                    tableEvent['deleted'].eq(0),
                    tableAction['deleted'].eq(0),
                    tableActionType['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tableActionType['class'].eq(2),
                    tableAction['endDate'].isNotNull(),
                    ]

            if socStatusClassId or socStatusTypeId:
                tableClientSocStatus = db.table('ClientSocStatus')
                if begDateTime:
                    cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                       tableClientSocStatus['endDate'].ge(begDateTime)
                                                      ]),
                                           tableClientSocStatus['endDate'].isNull()
                                          ]))
                if endDateTime:
                    cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                       tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                      ]),
                                           tableClientSocStatus['begDate'].isNull()
                                          ]))
                table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
                if socStatusClassId:
                    cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
                if socStatusTypeId:
                    cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
                cond.append(tableClientSocStatus['deleted'].eq(0))

            cond.append(tableActionType['serviceType'].eq(CActionServiceType.operation))
            return db.getRecordList(table, cols, cond)

        return []



class CStationaryF144100_2021(CStationaryF144100):
    def __init__(self, parent):
        CStationaryF144100.__init__(self, parent)


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        typeSurgery = params.get('typeSurgery', 0)

        orgStructureIndex = self.stationaryF14SetupDialog.cmbOrgStructure._model.index(self.stationaryF14SetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14SetupDialog.cmbOrgStructure.rootModelIndex())
        orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex) if orgStructureIndex.row() else []

        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'(4100)')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        cols = [('60%', [u'Наименование показателей', u'1'], CReportBase.AlignLeft),
                ('10%', [u'№ строки', u'2'],                 CReportBase.AlignCenter),
                ('30%', [u'Число', u'3'],                    CReportBase.AlignRight),
               ]
        table = createTable(cursor, cols)

        records = self.getOperation(orgStructureIdList, begDate, endDate, financeId, typeSurgery)
        reportLine = [0] * 8
        clientsChild = set()
        clientsSenior = set()
        for record in records:
            clientId = forceRef(record.value('client_id'))
            isChild = forceInt(record.value('isChild'))
            isSenior = forceInt(record.value('isSenior'))
            flatCode = forceString(record.value('flatCode'))
            usedEquipment = forceString(record.value('usedEquipment')).lower()

            if isChild:
                clientsChild.add(clientId)
            if isSenior:
                clientsSenior.add(clientId)

            if usedEquipment == u'лазерная':
                reportLine[3] += 1
            if usedEquipment == u'криогенная':
                reportLine[4] += 1
            if usedEquipment == u'эндоскопическая':
                reportLine[5] += 1
                if flatCode == '13.4':
                    reportLine[6] += 1
            if usedEquipment == u'рентгеновская':
                reportLine[7] += 1

        reportLine[1] = len(clientsChild)
        reportLine[2] = len(clientsSenior)

        clientsChild.update(clientsSenior)
        reportLine[0] = len(clientsChild)

        for row, rowDescr in enumerate(Rows4100):
            name, line = rowDescr
            i = table.addRow()
            table.setText(i, 0, name)
            table.setText(i, 1, line)
            table.setText(i, 2, reportLine[row])

        return doc


    def getOperation(self, orgStructureIdList, begDateTime, endDateTime, financeId, typeSurgery):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableClient = db.table('Client')
        tableRBService = db.table('rbService')
        tableEventType = db.table('EventType')
        tableContract = db.table('Contract')
        tableRBMedicalAidType = db.table('rbMedicalAidType')

        socStatusClassId = self.params.get('socStatusClassId', None)
        socStatusTypeId  = self.params.get('socStatusTypeId', None)
        selectActionType = self.params.get('selectActionType', 0)

        flatCode = ['received%', 'received%', 'moving%', 'leaved%'][selectActionType]
        nameProperty = [u'Направлен в отделение', u'Направлен в отделение', u'Отделение пребывания', u'Отделение'][selectActionType]

        table = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
        table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))

        flatCodeList = getActionTypeIdListByFlatCode(flatCode)
        flatCodeList.extend(getActionTypeIdListByFlatCode('13.4'))  # код 13.4 для 7-ой строки отчета
        cond = [tableAction['actionType_id'].inlist(flatCodeList),
                tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableEventType['deleted'].eq(0),
               ]

        if socStatusClassId or socStatusTypeId:
            tableClientSocStatus = db.table('ClientSocStatus')
            if begDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                   tableClientSocStatus['endDate'].ge(begDateTime)
                                                  ]),
                                       tableClientSocStatus['endDate'].isNull()
                                      ]))
            if endDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                   tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                  ]),
                                       tableClientSocStatus['begDate'].isNull()
                                      ]))
            table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
            if socStatusClassId:
                cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
            if socStatusTypeId:
                cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
            cond.append(tableClientSocStatus['deleted'].eq(0))

        cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
        joinOr1 = db.joinAnd([tableAction['begDate'].isNull(),
                              tableAction['endDate'].isNull()])

        joinOr2 = db.joinAnd([tableAction['begDate'].isNotNull(),
                              tableAction['begDate'].ge(begDateTime),
                              tableAction['begDate'].lt(endDateTime.addDays(1))])

        joinOr3 = db.joinAnd([tableAction['begDate'].isNull(),
                              tableAction['endDate'].isNotNull(),
                              tableAction['endDate'].ge(begDateTime)])

        joinOr4 = db.joinAnd([tableAction['begDate'].isNotNull(),
                              tableAction['begDate'].lt(begDateTime.addDays(1)),
                              db.joinOr([tableAction['endDate'].isNull(),
                                tableAction['endDate'].ge(begDateTime)])])
        cond.append(db.joinOr([joinOr1, joinOr2, joinOr3, joinOr4]))

        if orgStructureIdList:
            cond.append(getDataOrgStructure(nameProperty, orgStructureIdList))
        if financeId:
            cond.append("((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))"%(str(financeId), str(financeId)))
            table = table.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))

        eventIdList = db.getDistinctIdList(table, 'Event.id', cond)
        if not eventIdList:
            return []

        cols = [tableAction['id'].alias('actionId'),
                tableEvent['client_id'],
                tableActionType['id'].alias('actionTypeId'),
                tableActionType['group_id'].alias('groupId'),
                tableActionType['name'],
                tableActionType['flatCode'],
                tableRBService['code'] if typeSurgery == 0 else tableActionType['flatCode'].alias('code')
               ]
        cols.append(getQuotaTypeWTMP(byFinance=False))
        cols.append('(%s) AS isSenior' % getSeniorAges(begDateTime, 'Event.setDate'))
        cols.append('(age(Client.birthDate, Event.setDate) <= 17) AS isChild')
        cols.append('%s AS usedEquipment' % getStringPropertyValue(u'Использована аппаратура'))

        table = tableAction.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
        table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        cond = [tableAction['event_id'].inlist(eventIdList),
                tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableActionType['class'].eq(2),
                tableAction['endDate'].isNotNull(),
               ]
        socStatusClassId = self.params.get('socStatusClassId', None)
        socStatusTypeId  = self.params.get('socStatusTypeId', None)
        if socStatusClassId or socStatusTypeId:
            tableClientSocStatus = db.table('ClientSocStatus')
            if begDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                   tableClientSocStatus['endDate'].ge(begDateTime)
                                                  ]),
                                       tableClientSocStatus['endDate'].isNull()
                                      ]))
            if endDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                   tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                  ]),
                                       tableClientSocStatus['begDate'].isNull()
                                      ]))
            table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
            if socStatusClassId:
                cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
            if socStatusTypeId:
                cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
            cond.append(tableClientSocStatus['deleted'].eq(0))

        if typeSurgery == 0:
            table = table.innerJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
            cols.append(tableRBService['code'].alias('codeService'))
        else:
            cols.append(tableActionType['serviceType'].alias('codeService'))

        cond.append(tableActionType['serviceType'].eq(CActionServiceType.operation))
        return db.getRecordList(table, cols, cond)




class CStationaryF144110_2021(CStationaryF014):
    def __init__(self, parent):
        CStationaryF014.__init__(self, parent)
        self.setTitle(u'Таблица 4110')


    def getSetupDialog(self, parent):
        result = CStationaryF014.getSetupDialog(self, parent)
        result.setTypeSurgeryVisible(False)
        result.cmbSelectActionType.insertItem(0, u'Анестезия')
        return result


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

        tableColumns = [
            ('20%', [u'Виды анестезий', u'', u'1'], CReportBase.AlignLeft),
            ('20%', [u'№ строки', u'', u'2'], CReportBase.AlignCenter),
            ('20%', [u'Проведено анестезий, ед', u'экстренных', u'3'], CReportBase.AlignRight),
            ('20%', [u'', u'плановых', u'4'], CReportBase.AlignRight),
            ('20%', [u'Умерло пациентов, чел', u'', u'5'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0,0, 2,1)
        table.mergeCells(0,1, 2,1)
        table.mergeCells(0,2, 1,2)
        table.mergeCells(0,4, 2,1)

        reportData = [[0, 0, 0] for i in xrange(9)]
        rowDescr = (
            u'Аналгоседация',
            u'Эпидуральная анестезия',
            u'Спинальная (субарахноидальная) анестезия',
            u'Спинально-эпидуральная анестезия',
            u'Тотальная внутривенная анестезия',
            u'Комбинированный эндотрахеальный наркоз',
            u'Сочетанная анестезия',
            u'Сакральная анестезия',
            u'Внутриполостная анестезия')

        records = self.getAnesthesia(params)
        total = [0, 0, 0]
        actionIds = set()
        for record in records:
            actionId = forceRef(record.value('actionId'))
            if  actionId in actionIds:
                continue
            actionIds.add(actionId)
            value = forceInt(record.value('value'))
            isDeath = forceInt(record.value('isDeath'))
            isUrgent = forceInt(record.value('isUrgent'))
            reportData[value - 1][0 if isUrgent else 1] += 1
            reportData[value - 1][2] += isDeath
            total[0 if isUrgent else 1] += 1
            total[2] += isDeath

        for i, descr in enumerate(rowDescr):
            row = table.addRow()
            table.setText(row, 0, descr)
            table.setText(row, 1, i + 1)
            table.setText(row, 2, reportData[i][0])
            table.setText(row, 3, reportData[i][1])
            table.setText(row, 4, reportData[i][2])

        row = table.addRow()
        table.setText(row, 0, u'Всего')
        table.setText(row, 1, u'10')
        table.setText(row, 2, total[0])
        table.setText(row, 3, total[1])
        table.setText(row, 4, total[2])
        return doc


    def getEventIdList(self, params):
        db = QtGui.qApp.db
        selectActionType = params.get('selectActionType', 0)
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        orgStructureId = params.get('orgStructureId', None)
        orgStructureIdList = []
        if orgStructureId:
            orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)

        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableEventType = db.table('EventType')
        tableRBMedicalAidType = db.table('rbMedicalAidType')

        table = tableAction.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
        table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))

        flatCode = ['received%', 'received%', 'moving%', 'leaved%'][selectActionType-1]
        nameProperty = [u'Направлен в отделение', u'Направлен в отделение', u'Отделение пребывания', u'Отделение'][selectActionType-1]

        cond = [tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(flatCode)),
                tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableEventType['deleted'].eq(0),
                tableRBMedicalAidType['code'].inlist([1, 2, 3]),
               ]
        if begDate:
            cond.append(tableAction['endDate'].ge(begDate))
        if endDate:
            cond.append(tableAction['endDate'].lt(endDate.addDays(1)))
        if orgStructureIdList:
            cond.append(getDataOrgStructure(nameProperty, orgStructureIdList))

        return db.getDistinctIdList(table, tableEvent['id'].name(), cond)


    def getAnesthesia(self, params):
        db = QtGui.qApp.db
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())

        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableClient = db.table('Client')
        tableEventType = db.table('EventType')
        tableRBMedicalAidType = db.table('rbMedicalAidType')
        tableActionTypeIdentification = db.table('ActionType_Identification')

        cols = [
            tableAction['id'].alias('actionId'),
            tableAction['isUrgent'],
            tableActionTypeIdentification['value'],
        ]
        cols.append('%s AS isDeath' % (getStringProperty(u'Исход анестезии',
                                            u"(APS.value LIKE '%смерть%'"
                                            u" OR APS.value LIKE '%умер%'"
                                            u" OR APS.value LIKE 'летальный исход')")))

        table = tableAction.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
        table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
        table = table.leftJoin(tableActionTypeIdentification, tableActionTypeIdentification['master_id'].eq(tableActionType['id']))

        cond = [tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableAction['endDate'].isNotNull(),
                tableActionType['id'].inlist(getActionTypeIdListByFlatCode('anesthesia%')),
                tableEventType['deleted'].eq(0),
                tableRBMedicalAidType['code'].inlist([1, 2, 3]),
                ]

        socStatusClassId = params.get('socStatusClassId', None)
        socStatusTypeId  = params.get('socStatusTypeId', None)
        selectActionType = params.get('selectActionType', 0)

        if selectActionType == 0:
            if begDate:
                cond.append(tableAction['endDate'].ge(begDate))
            if endDate:
                cond.append(tableAction['endDate'].lt(endDate.addDays(1)))
        else:
            systemIdList = db.getIdList('rbAccountingSystem', 'id', "urn = 'urn:oid:4110'")
            cond.append(tableAction['event_id'].inlist(self.getEventIdList(params)))
            cond.append(tableActionTypeIdentification['system_id'].inlist(systemIdList))
            cond.append(tableActionTypeIdentification['value'].inlist(map(str, range(1,10))))

        if socStatusClassId or socStatusTypeId:
            tableClientSocStatus = db.table('ClientSocStatus')
            if begDate:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                   tableClientSocStatus['endDate'].ge(begDate)
                                                  ]),
                                       tableClientSocStatus['endDate'].isNull()
                                      ]))
            if endDate:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                   tableClientSocStatus['begDate'].lt(endDate.addDays(1))
                                                  ]),
                                       tableClientSocStatus['begDate'].isNull()
                                      ]))
            table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
            if socStatusClassId:
                cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
            if socStatusTypeId:
                cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
            cond.append(tableClientSocStatus['deleted'].eq(0))

        return db.getRecordList(table, cols, cond)



class CStationaryF144200_2021(CStationaryF014):
    def __init__(self, parent = None):
        CStationaryF014.__init__(self, parent)


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        typeSurgery = params.get('typeSurgery', 0)
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'(4200)Из общего числа операций(единиц)')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        cols = [('45%',[u'Наименование показателей', u'1'], CReportBase.AlignLeft),
                ('5%', [u'№ строки',                 u'2'], CReportBase.AlignCenter),
                ('25%',[u'Всего',                    u'3'], CReportBase.AlignRight),
                ('25%',[u'из них: у детей',          u'4'], CReportBase.AlignRight),
               ]

        table = createTable(cursor, cols)
        reportData = [[0,0] for _ in xrange(12)]
        recordList = self.getOperations(begDate, endDate, params)

        def addOne(reportData, row, clientAge):
            reportData[row][0] += 1
            if clientAge <= 17:
                reportData[row][1] += 1

        for record in recordList:
            flatCode = forceString(record.value('flatCode'))
            serviceCode = forceString(record.value('code'))
            MKB = normalizeMKB(forceString(record.value('MKB')))
            clientAge = forceInt(record.value('clientAge'))
            usedEquipment = forceString(record.value('usedEquipment')).lower()

            if flatCode == u'4':
                addOne(reportData, 0, clientAge)
                if usedEquipment == u'микрохирургическая':
                    addOne(reportData, 1, clientAge)
                    if MKB.startswith('S05'):
                        addOne(reportData, 2, clientAge)
                    elif MKB in ('E10.3', 'E11.3', 'E12.3', 'E13.3', 'E14.3'):
                        addOne(reportData, 3, clientAge)
                    elif MKB == 'E35.1':
                        addOne(reportData, 4, clientAge)
                    if MKB.startswith('H33'):
                        addOne(reportData, 5, clientAge)
                elif usedEquipment == u'лазерная':
                    addOne(reportData, 6, clientAge)
                    if MKB in ('E10.3', 'E11.3', 'E12.3', 'E13.3', 'E14.3'):
                        addOne(reportData, 7, clientAge)
                    elif MKB == 'E35.1':
                        addOne(reportData, 8, clientAge)
            elif flatCode in ('5.1', '5.1.'):
                addOne(reportData, 9, clientAge)
                if typeSurgery == 0:
                    if serviceCode.startswith('16.25.'):
                        addOne(reportData, 10, clientAge)
                else:
                    if MKB in ('H90.3', 'H90.4', 'H90.5', 'H90.6', 'H90.7',
                        'H90.8', 'Q16.0', 'Q17.0') or MKB.startswith('H91'):
                            addOne(reportData, 10, clientAge)
            elif flatCode in ('9.1', '9.1.'):
                if typeSurgery == 0:
                    # английская или русская буква А
                    if serviceCode in (u'A16.16.013', u'А16.16.013'):
                        addOne(reportData, 11, clientAge)
                else:
                    if MKB.startswith('K25') or MKB.startswith('K27') or MKB.startswith('K28'):
                        addOne(reportData, 11, clientAge)

        for row, rowDescr in enumerate(Rows4200):
            i = table.addRow()
            name, line = rowDescr
            table.setText(i, 0, name)
            table.setText(i, 1, line)
            table.setText(i, 2, reportData[row][0])
            table.setText(i, 3, reportData[row][1])

        return doc


    def getOperations(self, begDateTime, endDateTime, params):
        db = QtGui.qApp.db

        financeId = params.get('financeId')
        typeSurgery = params.get('typeSurgery', 0)
        orgStructureId = params.get('orgStructureId', None)
        orgStructureIdList = []
        if orgStructureId:
            orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)

        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableClient = db.table('Client')
        tableContract = db.table('Contract')
        tableEventType = db.table('EventType')
        tableRBMedicalAidType = db.table('rbMedicalAidType')
        tableRBService = db.table('rbService')

        socStatusClassId = params.get('socStatusClassId', None)
        socStatusTypeId  = params.get('socStatusTypeId', None)
        selectActionType = params.get('selectActionType', 0)

        nameProperty = [u'Направлен в отделение', u'Направлен в отделение', u'Отделение пребывания', u'Отделение'][selectActionType]

        table = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
        table = table.leftJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))

        cond = [tableActionType['flatCode'].inlist(['4', '5.1', '5.1.', '9.1', '9.1.']),
                tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableEventType['deleted'].eq(0),
                ]

        if typeSurgery == 0:
            cond.append(tableRBService['id'].isNotNull())

        if socStatusClassId or socStatusTypeId:
            tableClientSocStatus = db.table('ClientSocStatus')
            if begDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                   tableClientSocStatus['endDate'].ge(begDateTime)
                                                  ]),
                                       tableClientSocStatus['endDate'].isNull()
                                      ]))
            if endDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                   tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                  ]),
                                       tableClientSocStatus['begDate'].isNull()
                                      ]))
            table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
            if socStatusClassId:
                cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
            if socStatusTypeId:
                cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
            cond.append(tableClientSocStatus['deleted'].eq(0))

        cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
        joinOr1 = db.joinAnd([tableAction['begDate'].isNull(),
                              tableAction['endDate'].isNull()])

        joinOr2 = db.joinAnd([tableAction['begDate'].isNotNull(),
                              tableAction['begDate'].ge(begDateTime),
                              tableAction['begDate'].lt(endDateTime.addDays(1))])

        joinOr3 = db.joinAnd([tableAction['begDate'].isNull(),
                              tableAction['endDate'].isNotNull(),
                              tableAction['endDate'].ge(begDateTime)])

        joinOr4 = db.joinAnd([tableAction['begDate'].isNotNull(),
                              tableAction['begDate'].lt(begDateTime.addDays(1)),
                              db.joinOr([tableAction['endDate'].isNull(),
                                         tableAction['endDate'].ge(begDateTime)])])

        cond.append(db.joinOr([joinOr1, joinOr2, joinOr3, joinOr4]))
        if orgStructureIdList:
            cond.append(getDataOrgStructure(nameProperty, orgStructureIdList))
        if financeId:
            cond.append('((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %d) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %d))' % (financeId, financeId))
            table = table.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))

        cols = [
            tableActionType['flatCode'],
            tableAction['MKB'],
            tableRBService['code'],
            'age(Client.birthDate, Event.setDate) AS clientAge',
            '%s AS usedEquipment' % getStringPropertyValue(u'Использована аппаратура'),
        ]

        return db.getRecordList(table, cols, cond)


class CStationaryF144201_2021(CStationaryF014):
    def __init__(self, parent = None):
        CStationaryF014.__init__(self, parent)
        self.stationaryF14SetupDialog = None


    def build(self, params):
        orgStructureIndex = self.stationaryF14SetupDialog.cmbOrgStructure._model.index(self.stationaryF14SetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14SetupDialog.cmbOrgStructure.rootModelIndex())
        orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex) if orgStructureIndex.row() else []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'(4201)')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [
                ('25%',[u'Наименование трансплантаций', u'1'], CReportBase.AlignLeft),
                ('5%', [u'№ строки', u'2'], CReportBase.AlignCenter),
                ('10%',[u'Проведено операций (трансплантаций) - всего', u'3'], CReportBase.AlignRight),
                ('10%',[u'из них детям', u'4'], CReportBase.AlignRight),
                ('10%',[u'Число операций, при которых наблюдались осложнения (из гр. 3)', u'5'], CReportBase.AlignRight),
                ('10%',[u'из них детям', u'6'], CReportBase.AlignRight),
                ('10%',[u'Умерло оперированных (из гр. 3)', u'7'], CReportBase.AlignRight),
                ('10%',[u'из них детей (из гр. 7)', u'8'], CReportBase.AlignRight),
                ('10%',[u'Направлено материалов на морфологическое исследование (из гр. 3)', u'9'], CReportBase.AlignRight)
            ]
            table = createTable(cursor, cols)
            recordList = self.getTransplantation(orgStructureIdList, begDate, endDate)

            def processReportLine(reportLine, record):
                countDeathSurgery = forceInt(record.value('countDeathSurgery'))
                clientAge = forceInt(record.value('clientAge'))
                countComplication = forceInt(record.value('countComplication'))
                countMorphologicalStudy = forceInt(record.value('countMorphologicalStudy'))
                reportLine[0] += 1
                if countComplication:
                    reportLine[2] += 1
                if countDeathSurgery:
                    reportLine[4] += 1
                if countMorphologicalStudy:
                    reportLine[6] += 1
                if clientAge <= 17:
                    reportLine[1] += 1
                    if countComplication:
                        reportLine[3] += 1
                    if countDeathSurgery:
                        reportLine[5] += 1

            eventIds = set()
            reportData = [[0]*7 for _ in xrange(len(Rows4201))]
            for record in recordList:
                eventId = forceInt(record.value('event_id'))
                value = forceString(record.value('value')).lower()
                processReportLine(reportData[0], record)

                if value == u'легкого':
                    processReportLine(reportData[1], record)
                if value == u'сердца':
                    processReportLine(reportData[2], record)
                if value == u'печени':
                    processReportLine(reportData[3], record)
                if value == u'поджелудочной железы':
                    processReportLine(reportData[4], record)
                if value == u'тонкой кишки':
                    processReportLine(reportData[5], record)
                if value == u'почки':
                    processReportLine(reportData[6], record)
                if value == u'костного мозга':
                    processReportLine(reportData[7], record)
                if value == u'прочих органов':
                    processReportLine(reportData[8], record)
                if eventId in eventIds:
                    processReportLine(reportData[9], record)
                eventIds.add(eventId)

            for row, rowDescr in enumerate(Rows4201):
                i = table.addRow()
                name, line = rowDescr
                table.setText(i, 0, name)
                table.setText(i, 1, line)
                for col, data in enumerate(reportData[row]):
                    table.setText(i, 2+col, data)

        return doc


    def getTransplantation(self, orgStructureIdList, begDateTime, endDateTime):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableClient = db.table('Client')
        tableEventType = db.table('EventType')
        tableRBMedicalAidType = db.table('rbMedicalAidType')
        tableAP = db.table('ActionProperty')
        tableAPT = db.table('ActionPropertyType')
        tableAPS = db.table('ActionProperty_String')

        socStatusClassId = self.params.get('socStatusClassId', None)
        socStatusTypeId  = self.params.get('socStatusTypeId', None)
        selectActionType = self.params.get('selectActionType', 0)

        nameProperty = [u'Направлен в отделение', u'Направлен в отделение', u'Отделение пребывания', u'Отделение'][selectActionType]

        table = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
        table = table.innerJoin(tableAP, tableAP['action_id'].eq(tableAction['id']))
        table = table.innerJoin(tableAPT, tableAP['type_id'].eq(tableAPT['id']))
        table = table.innerJoin(tableAPS, tableAP['id'].eq(tableAPS['id']))

        cond = [tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableEventType['deleted'].eq(0),
                tableAP['deleted'].eq(0),
                tableAPT['deleted'].eq(0),
                tableActionType['serviceType'].eq(CActionServiceType.operation),
                tableAPT['name'].eq(u'Трансплантация'),
            ]

        cols = [
            tableAction['event_id'],
            'age(Client.birthDate, Event.setDate) AS clientAge',
            tableAPS['value'],
        ]

        if socStatusClassId or socStatusTypeId:
            tableClientSocStatus = db.table('ClientSocStatus')
            if begDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                   tableClientSocStatus['endDate'].ge(begDateTime)
                                                  ]),
                                       tableClientSocStatus['endDate'].isNull()
                                      ]))
            if endDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                   tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                  ]),
                                       tableClientSocStatus['begDate'].isNull()
                                      ]))
            table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
            if socStatusClassId:
                cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
            if socStatusTypeId:
                cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
            cond.append(tableClientSocStatus['deleted'].eq(0))

        cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
        joinOr1 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNull()])
        joinOr2 = db.joinAnd([tableAction['begDate'].isNotNull(), tableAction['begDate'].ge(begDateTime), tableAction['begDate'].lt(endDateTime.addDays(1))])
        joinOr3 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNotNull(), tableAction['endDate'].ge(begDateTime)])
        joinOr4 = db.joinAnd([tableAction['begDate'].isNotNull(), tableAction['begDate'].lt(begDateTime.addDays(1)), db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(begDateTime)])])
        cond.append(db.joinOr([joinOr1, joinOr2, joinOr3, joinOr4]))
        if orgStructureIdList:
            cond.append(getDataOrgStructure(nameProperty, orgStructureIdList))

        cols.append('%s AS countDeathSurgery' % (getStringProperty(u'Исход операции', u"(APS.value LIKE 'умер%' OR APS.value LIKE 'смерть%' OR APS.value LIKE 'летальный исход')")))
        cols.append('%s AS countMorphologicalStudy' % (getStringProperty(u'Направление на морфологию', u"(APS.value LIKE 'да')")))
        cols.append('%s AS countComplication' % (getStringProperty(u'Осложнение', u"(APS.value != '' OR APS.value != ' ')")))

        return db.getRecordList(table, cols, cond, order='Action.id')


class CStationaryF14_4300_4301_4302_2021(CStationaryF014):
    def __init__(self, parent=None):
        CStationaryF014.__init__(self, parent)


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Стационар. Форма 14. Подстрочники (4300), (4301), (4302).')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

        counts = self.getOperations(begDate, endDate, params)

        cursor.insertText(u'(4300)\nИз числа стентирований (из табл. 4000) (стр. 7.5.2.1) - проведено пациентам с инфарктом миокарда %s.' % counts[0])
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(4301)\nИз числа операций на сосудах, питающих головной мозг (из табл. 4000) (стр. 8.1.1.) проведено операций при внутримозговом кровоизлиянии %s.' % counts[1])
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'(4302)\nИз числа оперативных вмешательств проведено: по поводу множественной травмы %s, нейротравмы %s.' % (counts[2], counts[3]))
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)

        return doc


    def getOperations(self, begDateTime, endDateTime, params):
        db = QtGui.qApp.db

        financeId = params.get('financeId')
        orgStructureId = params.get('orgStructureId', None)
        orgStructureIdList = []
        if orgStructureId:
            orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)

        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableClient = db.table('Client')
        tableContract = db.table('Contract')
        tableEventType = db.table('EventType')
        tableRBMedicalAidType = db.table('rbMedicalAidType')

        socStatusClassId = params.get('socStatusClassId', None)
        socStatusTypeId  = params.get('socStatusTypeId', None)
        selectActionType = params.get('selectActionType', 0)

        nameProperty = [u'Направлен в отделение', u'Направлен в отделение', u'Отделение пребывания', u'Отделение'][selectActionType]

        table = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))

        cond = [tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableEventType['deleted'].eq(0),
                tableActionType['serviceType'].eq(CActionServiceType.operation),
            ]

        if socStatusClassId or socStatusTypeId:
            tableClientSocStatus = db.table('ClientSocStatus')
            if begDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                   tableClientSocStatus['endDate'].ge(begDateTime)
                                                  ]),
                                       tableClientSocStatus['endDate'].isNull()
                                      ]))
            if endDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                   tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                  ]),
                                       tableClientSocStatus['begDate'].isNull()
                                      ]))
            table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
            if socStatusClassId:
                cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
            if socStatusTypeId:
                cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
            cond.append(tableClientSocStatus['deleted'].eq(0))

        cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
        cond.append(tableAction['begDate'].ge(begDateTime))
        cond.append(tableAction['endDate'].lt(endDateTime.addDays(1)))
        if orgStructureIdList:
            cond.append(getDataOrgStructure(nameProperty, orgStructureIdList))
        if financeId:
            cond.append('((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %d) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %d))' % (financeId, financeId))
            table = table.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))

        cols = [
            "SUM(ActionType.flatCode = '7.5.2.1' AND Action.MKB IN ('I21.0', 'I21.1', 'I21.2', 'I21.3', 'I21.4', 'I21.9', 'I22.0', 'I22.1', 'I22.8', 'I22.9', 'I25.2')) AS count4300",

            "SUM(ActionType.flatCode = '8.1.1' AND Action.MKB != 'I61.7' AND (LEFT(Action.MKB, 3) IN ('I60', 'I61') OR Action.MKB IN ('I62.0', 'I62.1', 'I62.9'))) AS count4301",

            "SUM(LEFT(Action.MKB, 3) = 'T02' OR Action.MKB IN ('T07', 'T07.0')) AS count4302_1",
            "SUM(LEFT(Action.MKB, 3) IN ('S06', 'S04', 'S07', 'S14', 'S24', 'S34', 'S44', 'S54', 'S64', 'S74', 'S84', 'S94') OR Action.MKB IN ('S02.0', 'S02.1', 'S02.9', 'S09.7')) AS count4302_2",
        ]

        query = db.query(db.selectStmt(table, cols, cond))
        if query.next():
            return [forceInt(query.value(i)) for i in xrange(4)]
        return [0, 0, 0, 0]



class CStationaryF144400_2021(CStationaryF014):
    def __init__(self, parent = None):
        CStationaryF014.__init__(self, parent)
        self.stationaryF14SetupDialog = None


    def build(self, params):
        orgStructureIndex = self.stationaryF14SetupDialog.cmbOrgStructure._model.index(self.stationaryF14SetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14SetupDialog.cmbOrgStructure.rootModelIndex())
        orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex) if orgStructureIndex.row() else []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        typeSurgery = params.get('typeSurgery', 0)
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'(4400)')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('75%',[u'Наименование показателей'], CReportBase.AlignLeft),
                    ('3%', [u'№ графы'], CReportBase.AlignCenter),
                    ('22%',[u'Число'], CReportBase.AlignRight),
                   ]
            table = createTable(cursor, cols)
            records = self.getRestoration(orgStructureIdList, begDate, endDate)

            def cmpCode2(code):
                return (code >= u'А16.12.001' and code <= u'А16.12.023') or \
                       (code >= u'А16.12.025' and code <= u'А16.12.028') or \
                       (code >= u'А16.10.001' and code <= u'А16.10.018')

            def cmpCode3(code):
                return code >= u'А16.15.001' and code <= u'А16.15.012'

            def cmpCode4(code):
                return (code >= u'А16.04.001' and code <= u'А16.04.023') or \
                       (code >= u'А16.03.021' and code <= u'А16.03.041') or \
                       (code == u'А16.31.017') or (code == u'А16.31.018')

            count = [0] * 5
            for record in records:
                flatCodeList = forceString(record.value('flatCodeList')).split(',')
                codeList = forceString(record.value('codeList')).split(',')
                MKBList = forceString(record.value('MKBList')).split(',')

                if 'recoveryDirection2018' not in flatCodeList:
                    continue
                if any(i.startswith('K85') for i in MKBList) and any(map(cmpCode3, codeList)):
                    count[3] += 1

                if typeSurgery == 0:  # номенклатурный
                    codeList = forceString(record.value('codeList')).split(',')
                    if u'А16.16.021' in codeList or u'А16.16.013' in codeList:
                        count[0] += 1
                    if u'А16.14.009' in codeList:
                        count[1] += 1
                    if any(map(cmpCode2, codeList)):
                        count[2] += 1
                    if any(map(cmpCode4, codeList)):
                        count[4] += 1
                else:
                    if '9.1' in flatCodeList:
                        count[0] += 1
                    if '9.4' in flatCodeList:
                        count[1] += 1
                    if '7' in flatCodeList or '8' in flatCodeList:
                        count[2] += 1
                    if '15' in flatCodeList:
                        count[4] += 1

            count.insert(0, sum(count))
            for row, rowDescr in enumerate(Rows4400):
                i = table.addRow()
                name, line = rowDescr
                table.setText(i, 0, name)
                table.setText(i, 1, line)
                table.setText(i, 2, count[row])

        return doc


    def getRestoration(self, orgStructureIdList, begDateTime, endDateTime):
        db = QtGui.qApp.db

        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableClient = db.table('Client')
        tableRBService = db.table('rbService')
        tableEventType = db.table('EventType')
        tableRBMedicalAidType = db.table('rbMedicalAidType')

        table = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
        table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        table = table.leftJoin(tableRBService, tableActionType['nomenclativeService_id'].eq(tableRBService['id']))

        cond = [tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableEventType['deleted'].eq(0),
            ]

        socStatusClassId = self.params.get('socStatusClassId', None)
        socStatusTypeId  = self.params.get('socStatusTypeId', None)
        selectActionType = self.params.get('selectActionType', 0)

        nameProperty = [u'Направлен в отделение', u'Направлен в отделение', u'Отделение пребывания', u'Отделение'][selectActionType]

        if socStatusClassId or socStatusTypeId:
            tableClientSocStatus = db.table('ClientSocStatus')
            if begDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                   tableClientSocStatus['endDate'].ge(begDateTime)
                                                  ]),
                                       tableClientSocStatus['endDate'].isNull()
                                      ]))
            if endDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                   tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                  ]),
                                       tableClientSocStatus['begDate'].isNull()
                                      ]))
            table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
            if socStatusClassId:
                cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
            if socStatusTypeId:
                cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
            cond.append(tableClientSocStatus['deleted'].eq(0))

        cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
        joinOr1 = db.joinAnd([tableAction['begDate'].isNull(),
                              tableAction['endDate'].isNull()])

        joinOr2 = db.joinAnd([tableAction['begDate'].isNotNull(),
                              tableAction['begDate'].ge(begDateTime),
                              tableAction['begDate'].lt(endDateTime.addDays(1))])

        joinOr3 = db.joinAnd([tableAction['begDate'].isNull(),
                              tableAction['endDate'].isNotNull(),
                              tableAction['endDate'].ge(begDateTime)])

        joinOr4 = db.joinAnd([tableAction['begDate'].isNotNull(),
                              tableAction['begDate'].lt(begDateTime.addDays(1)),
                              db.joinOr([tableAction['endDate'].isNull(),
                                         tableAction['endDate'].ge(begDateTime)])])

        cond.append(db.joinOr([joinOr1, joinOr2, joinOr3, joinOr4]))
        if orgStructureIdList:
            cond.append(getDataOrgStructure(nameProperty, orgStructureIdList))

        cols = [
            tableAction['event_id'],
            'GROUP_CONCAT(DISTINCT ActionType.flatCode) AS flatCodeList',
            'GROUP_CONCAT(DISTINCT rbService.code) AS codeList',
            'GROUP_CONCAT(DISTINCT Action.MKB) AS MKBList',
        ]

        return db.getRecordListGroupBy(table, cols, cond, 'Action.event_id')
