# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4              import QtGui
from PyQt4.QtCore       import Qt, pyqtSignature, QDate, QDateTime, QString

from library.MapCode          import createMapCodeToRowIdx
from library.Utils            import forceInt, forceString

from Orgs.Utils               import getOrgStructureFullName
from Events.ActionServiceType import CActionServiceType
from Events.EventTypeListEditorDialog import CEventTypeListEditorDialog
from Reports.Report           import CReport, normalizeMKB
from Reports.ReportBase       import CReportBase, createTable
from Reports.ReportView       import CPageFormat
from Reports.Utils            import dateRangeAsStr, getStringProperty

from Ui_AnaliticReportsSurgery import Ui_AnaliticReportsSurgeryDialog


MainRows4000 = [( u'Новообразования', u'3.0', u'C00-D48')]


RowsUsers4000 = [( u'Всего операций', u'1'),
                 ( u'в том числе: операции на нервной системе', u'2'),
                 ( u'из них: на головном мозге', u'2.1'),
                 ( u'на переферической нервной системе', u'2.2'),
                 ( u'Операции на эндокринной системе', u'3'),
                 ( u'из них: тиреотомии', u'3.1'),
                 ( u'Операции на органе зрения', u'4'),
                 ( u'из них: кератопластика', u'4.1'),
                 ( u'задняя витреоэктомия', u'4.2'),
                 ( u'операции по поводу: глаукомы', u'4.3'),
                 ( u'из них: с применением шунтов и дренажей', u'4.3.1'),
                 ( u'энуклеации', u'4.4'),
                 ( u'катаракты', u'4.5'),
                 ( u'из них: методом факоэмульсификации', u'4.5.1'),
                 ( u'Операции на органах уха, горла, носа', u'5'),
                 ( u'из них: на ухе', u'5.1'),
                 ( u'на миндалинах и аденоидах', u'5.2'),
                 ( u'Операции на органах дыхания', u'6'),
                 ( u'из них: на трахее', u'6.1'),
                 ( u'пневмонэктомия', u'6.2'),
                 ( u'эксплоративная торакотомия', u'6.3'),
                 ( u'Операции на сердце', u'7'),
                 ( u'из них: на открытом сердце', u'7.1'),
                 ( u'в т.ч. с искусственным кровообращением', u'7.1.1'),
                 ( u'коррекция врожденных пороков сердца', u'7.2'),
                 ( u'коррекция приобретенных поражений клапанов сердца', u'7.3'),
                 ( u'при нарушении ритма – всего', u'7.4'),
                 ( u'в том числе:имплантация кардиостимулятора', u'7.4.1'),
                 ( u'коррекция тахиаритмий', u'7.5'),
                 ( u'из них: катетерных амблаций', u'7.5.1'),
                 ( u'по поводу ишемических болезней сердца', u'7.6'),
                 ( u'из них: аортокоронарное шунтирование', u'7.6.1'),
                 ( u'ангиопластика коронарных артерий', u'7.6.2'),
                 ( u'из них: со стентированием', u'7.6.2.1'),
                 ( u'Операции на сосудах', u'8'),
                 ( u'из них: операции на артериях', u'8.1'),
                 ( u'в том числе на: питающих головной мозг', u'8.1.1'),
                 ( u'из них: каротидные эндартерэктомии', u'8.1.1.1'),
                 ( u'экстраинтракраниальные анастомозы', u'8.1.1.2'),
                 ( u'рентгенэндоваскулярные дилятации', u'8.1.1.3'),
                 ( u'из них: со стентированием ', u'8.1.1.3.1'),
                 ( u'на почечных артериях ', u'8.1.2'),
                 ( u'на аорте', u'8.1.3'),
                 ( u'операции на венах', u'8.2'),
                 ( u'Операции на органах брюшной полости', u'9'),
                 ( u'из них: на желудке по поводу язвенной болезни', u'9.1'),
                 ( u'аппендэктомии при хроническом аппендиците', u'9.2'),
                 ( u'грыжесечение при неущемленной грыже', u'9.3'),
                 ( u'холецистэктомия при хроническом холецистите', u'9.4'),
                 ( u'лапаротомия диагностическая', u'9.5'),
                 ( u'на кишечнике', u'9.6'),
                 ( u'из них: на прямой кишке', u'9.6.1'),
                 ( u'по поводу геморроя ', u'9.7'),
                 ( u'Операции на почках и мочеточниках', u'10'),
                 ( u'Операции на мужских половых органах', u'11'),
                 ( u'из них: операции на предстательной железе', u'11.1'),
                 ( u'Операции по поводу стерилизации мужчин', u'12'),
                 ( u'Операции на женских половых органах', u'13'),
                 ( u'из них: экстирпация и надвлагалищная ампутация матки', u'13.1'),
                 ( u'на придатках матки по поводу бесплодия', u'13.2'),
                 ( u'на яичниках по поводу новообразований ', u'13.3'),
                 ( u'по поводу стерилизации женщин', u'13.4'),
                 ( u'выскабливание матки (кроме аборта)', u'13.5'),
                 ( u'Акушерские операции', u'14'),
                 ( u'из них: по поводу внематочной беременности', u'14.1'),
                 ( u'наложение щипцов', u'14.2'),
                 ( u'вакуум-экстракция', u'14.3'),
                 ( u'кесарево сечение в сроке 28 недель беременности и более', u'14.4'),
                 ( u'кесарево сечение в сроке менее 28 недель беременности', u'14.5'),
                 ( u'аборт', u'14.6'),
                 ( u'плодоразрушающие', u'14.7'),
                 ( u'экстирпация и надвлагалищная ампутация матки в сроке 28 недель беременности и более, в родах и после родов', u'14.8'),
                 ( u'экстирпация и надвлагалищная ампутация матки при прерывании беременности в сроке менее 28 недель беременности или после прерывания', u'14.9'),
                 ( u'Операции на костно-мышечной системе', u'15'),
                 ( u'из них: коррегирующие остеотомии', u'15.1'),
                 ( u'на челюстно-лицевой области', u'15.2'),
                 ( u'при травмах костей таза', u'15.3'),
                 ( u'при около- и внутрисуставных переломах', u'15.4'),
                 ( u'на позвоночнике', u'15.5'),
                 ( u'при врожденном вывихе бедра', u'15.6'),
                 ( u'ампутации и экзартикуляции', u'15.7'),
                 ( u'эндопротезирование-всего', u'15.8'),
                 ( u'из них: тазобедренного сустава', u'15.8.1'),
                 ( u'коленного сустава', u'15.8.2'),
                 ( u'на грудной стенке', u'15.9'),
                 ( u'из них: торакомиопластика', u'15.9.1'),
                 ( u'торакостомия', u'15.9.2'),
                 ( u'Операции на молочной железе', u'16'),
                 ( u'Операции на коже и подкожной клетчатке', u'17'),
                 ( u'из них: на челюстно-лицевой области', u'17.1'),
                 ( u'операции на средостении', u'18'),
                 ( u'из них операции на вилочковой железе', u'18.1'),
                 ( u'операции на пищеводе', u'19'),
                 ( u'Прочие операции', u'20')
                 ]


class CAnaliticReportsSurgeryDialog(QtGui.QDialog, Ui_AnaliticReportsSurgeryDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbFinance.setTable('rbFinance', addNone=True)
        self.eventTypeList = []


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbSpecialDeliverClient.setCurrentIndex(params.get('eventOrder', 0))
        self.cmbFinance.setValue(params.get('financeId', None))
        self.cmbTypeSurgery.setCurrentIndex(params.get('typeSurgery', 0))
        self.cmbSelectType.setCurrentIndex(params.get('selectType', 0))
        self.cmbPerson.setValue(params.get('personId', None))
        self.chkExistFlatCode.setChecked(params.get('existFlatCode', False))

        self.eventTypeList =  params.get('eventTypeList', [])
        if self.eventTypeList:
            db = QtGui.qApp.db
            tableET = db.table('EventType')
            records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(self.eventTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            self.lblEventTypeList.setText(u','.join(name for name in nameList if name))
        else:
                self.lblEventTypeList.setText(u'не задано')


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['eventOrder'] = self.cmbSpecialDeliverClient.currentIndex()
        result['financeId'] = self.cmbFinance.value()
        result['typeSurgery'] = self.cmbTypeSurgery.currentIndex()
        result['eventTypeList'] = self.eventTypeList
        result['selectType'] = self.cmbSelectType.currentIndex()
        result['personId'] = self.cmbPerson.value()
        result['existFlatCode'] = self.chkExistFlatCode.isChecked()
        return result


    @pyqtSignature('')
    def on_btnEventTypeList_clicked(self):
        self.eventTypeList = []
        self.lblEventTypeList.setText(u'не задано')
        dialog = CEventTypeListEditorDialog(self)
        if dialog.exec_():
            self.eventTypeList = dialog.values()
            if self.eventTypeList:
                db = QtGui.qApp.db
                tableET = db.table('EventType')
                records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(self.eventTypeList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblEventTypeList.setText(u','.join(name for name in nameList if name))


class CAnaliticReportsSurgery(CReport):
    def __init__(self, parent = None):
        CReport.__init__(self, parent)
        self.setTitle(u'Хирургическая работа учреждения.')
        self.stationaryF14SetupDialog = None
        self.clientDeath = 8
        self.orientation = CPageFormat.Landscape


    def getSetupDialog(self, parent):
        result = CAnaliticReportsSurgeryDialog(parent)
        self.stationaryF14SetupDialog = result
        return result


    def dumpParams(self, cursor, params):
        description = []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        eventOrder = params.get('eventOrder', 0)
        if begDate and endDate:
            description.append(dateRangeAsStr(u'за период', begDate, endDate))
        selectType = params.get('selectType', 0)
        description.append(u'выбор: %s'%{0: u'по врачу ответственному за действие',
                                         1: u'по врачу ответственному за событие'}.get(selectType, u'по врачу ответственному за действие'))
        personId = params.get('personId', None)
        if personId:
            description.append(u'врач: %s'%(forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))))
        orgStructureId = params.get('orgStructureId', None)
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        if eventOrder == 2:
            description.append(u'учет экстренных пациентов '+ u'по атрибуту События "экстренно"')
        elif eventOrder == 1:
            description.append(u'учет экстренных пациентов '+ u'по свойству "Доставлен по экстренным показаниям"')
        financeId = params.get('financeId', None)
        description.append(u'тип финансирования: %s'%(forceString(QtGui.qApp.db.translate('rbFinance', 'id', financeId, 'name')) if financeId else u'не задано'))
        if self.stationaryF14SetupDialog.cmbTypeSurgery.isVisible():
            description.append(u'учет операций: %s'%([u'номенклатурный', u'пользовательский'][params.get('typeSurgery', 0)]))
        existFlatCode = params.get('existFlatCode', False)
        if existFlatCode:
            description.append(u'учитывать только заполненный "код для отчетов"')
        eventTypeList = params.get('eventTypeList', None)
        if eventTypeList:
            db = QtGui.qApp.db
            tableET = db.table('EventType')
            records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(eventTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            description.append(u'тип события:  %s'%(u','.join(name for name in nameList if name)))
        else:
            description.append(u'тип события:  не задано')
        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getOrgStructureIdList(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    def build(self, params):
        db = QtGui.qApp.db
        orgStructureId = params.get('orgStructureId', None)
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId) if orgStructureId else []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        isNomeclature = params.get('typeSurgery', 0)
        eventTypeList = params.get('eventTypeList', None)
        selectType = params.get('selectType', 0)
        personId = params.get('personId', None)
        existFlatCode       = params.get('existFlatCode', False)
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            mapMainRows = createMapCodeToRowIdx( [row[2] for row in MainRows4000] )
            if isNomeclature:
                rowSize = 28
                reportMainData = [0]*(rowSize-1)
                reportMainData.append(0.0)
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'3.Хирургическая работа учреждения\n(4000)')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('15%',[u'Наименование операции', u'', u'', u'1'], CReportBase.AlignLeft),
                    ('4%', [u'№ строки', u'', u'', u'2'], CReportBase.AlignLeft),
                    ('3%', [u'Число операций, проведенных в стационаре', u'всего', u'', u'3'], CReportBase.AlignLeft),
                    ('3%', [u'', u'из них: детям 0-17 лет включительно', u'0-14 лет включительно', u'4'], CReportBase.AlignLeft),
                    ('3%', [u'', u'', u'из них (из гр.4) в возрасте до 1 года', u'5'], CReportBase.AlignLeft),
                    ('3%', [u'', u'', u'15-17 лет включительно', u'6'], CReportBase.AlignLeft),
                    ('3%', [u'Из них операций с применением высоких медицинских технологий (ВМП)',u'всего', u'', u'7'], CReportBase.AlignLeft),
                    ('3%', [u'', u'из них: детям 0-17 лет включительно', u'0-14 лет включительно', u'8'], CReportBase.AlignLeft),
                    ('3%', [u'', u'', u'из них (из гр.8) в возрасте до 1 года', u'9'], CReportBase.AlignLeft),
                    ('3%', [u'', u'', u'15-17 лет включи-тельно', u'10'], CReportBase.AlignLeft),
                    ('3%', [u'Число операций, при которых наблюдались осложнения в стационаре',u'всего', u'', u'11'], CReportBase.AlignLeft),
                    ('3%', [u'', u'из них: детям 0-17 лет включительно', u'0-14 лет включительно', u'12'], CReportBase.AlignLeft),
                    ('3%', [u'',u'', u'из них (из гр.12) в возрасте до 1 года', u'13'], CReportBase.AlignLeft),
                    ('3%', [u'', u'', u'15-17 лет включительно', u'14'], CReportBase.AlignLeft),
                    ('3%', [u'из них после операций, с применением ВМП',u'всего', u'', u'15'], CReportBase.AlignLeft),
                    ('3%', [u'', u'из них: детям 0-17 лет включительно', u'0-14 лет включительно', u'16'], CReportBase.AlignLeft),
                    ('3%', [u'',u'', u'из них (из гр.16) в возрасте до 1 года', u'17'], CReportBase.AlignLeft),
                    ('3%', [u'', u'', u'15-17 лет включительно', u'18'], CReportBase.AlignLeft),
                    ('3%', [u'Умерло оперированных в стационаре',u'всего', u'', u'19'], CReportBase.AlignLeft),
                    ('3%', [u'', u'из них: детям 0-17 лет включительно', u'0-14 лет включительно', u'20'], CReportBase.AlignLeft),
                    ('3%', [u'',u'', u'из них (из гр.20) в возрасте до 1 года', u'21'], CReportBase.AlignLeft),
                    ('3%', [u'', u'', u'15-17 лет включительно', u'22'], CReportBase.AlignLeft),
                    ('3%', [u'из них умерло после операций, проведенных с применением ВМП',u'всего', u'', u'23'], CReportBase.AlignLeft),
                    ('3%', [u'', u'из них: детям 0-17 лет включительно', u'0-14 лет включительно', u'24'], CReportBase.AlignLeft),
                    ('3%', [u'',u'', u'из них (из гр.24) в возрасте до 1 года', u'25'], CReportBase.AlignLeft),
                    ('3%', [u'', u'', u'15-17 лет включительно', u'26'], CReportBase.AlignLeft),
                    ('3%', [u'Из гр.3: проведено операций по поводу злокачественных новообразований', u'', u'', u'27'], CReportBase.AlignLeft),
                    ('3%', [u'Из гр.3: направлено материалов на морфологическое исследование', u'', u'', u'28'], CReportBase.AlignLeft)
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
            mapCodeToRowIdx = self.getRowsSurgery(isNomeclature)
            mapCodesToRowIdx = self.getSurgery(mapMainRows, mapCodeToRowIdx, orgStructureIdList, begDate, endDate, financeId, isNomeclature, eventTypeList, selectType, personId, existFlatCode)
            keys = mapCodesToRowIdx.keys()
            keys.sort()
            if isNomeclature:
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
                            table.setText(i, col, forceString(item))
            else:
                for key in keys:
                    items = mapCodesToRowIdx[key]
                    i = table.addRow()
                    for col, item in enumerate(items):
                        table.setText(i, col, forceString(item))
        return doc


    def getRowsSurgery(self, isNomeclature):
        mapCodeToRowIdx = {}
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        cond = [tableActionType['deleted'].eq(0)]
        cond.append(tableActionType['serviceType'].eq(CActionServiceType.operation))
        stmt = db.selectStmt(tableActionType, [tableActionType['flatCode'], tableActionType['code'] if not isNomeclature else tableActionType['flatCode'].alias('code'), tableActionType['name'],
                                               tableActionType['group_id'], tableActionType['id'].alias('actionTypeId')], cond, u'%s , ActionType.group_id'%(u'ActionType.code' if not isNomeclature else u'ActionType.flatCode'))
        records = db.query(stmt)
        if not isNomeclature:
            numbers = [1]
            mapCodeToRowIdx[''] = (u'Всего операций', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            while records.next():
                record = records.record()
                code = QString(forceString(record.value('code')))
                name = forceString(record.value('name'))
                if not mapCodeToRowIdx.get(code, None):
                    codeList = code.split('.')
                    lenCodeList = len(codeList)
                    if len(numbers) < lenCodeList:
                        for i in range(lenCodeList - len(numbers)):
                            numbers.append(0)
                    elif len(numbers) > lenCodeList:
                        for i in range(len(numbers) - lenCodeList):
                            numbers[len(numbers)- (1 + i)] = 0
                    numbers[lenCodeList-1] += 1
                    rowIdx = u'.'.join(str(number) for number in numbers)
                    mapCodeToRowIdx[code] = (name, rowIdx, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
                    rowIdx = []
        else:
            mapCodeToRowIdx[''] = (u'Всего операций', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            while records.next():
                record = records.record()
                code = QString(forceString(record.value('code')))
                name = forceString(record.value('name'))
                if not mapCodeToRowIdx.get(code, None):
                    codeList = [QString(code)]
                    indexPoint = code.lastIndexOf(u'.', -1, Qt.CaseInsensitive)
                    while indexPoint > -1:
                        code.truncate(indexPoint)
                        codeList.append(QString(code))
                        indexPoint = code.lastIndexOf(u'.', -1, Qt.CaseInsensitive)
                    codeList.sort()
                    for code in codeList:
                        if not mapCodeToRowIdx.get(code, None):
                            mapCodeToRowIdx[code] = (name, code, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        return mapCodeToRowIdx


    def getSurgery(self, mapMainRows, mapCodeToRowIdx, orgStructureIdList, begDateTime, endDateTime, financeId, isNomeclature, eventTypeList, selectType, personId, existFlatCode):
        def setValueMapCodeToRowIdx(mapCodeToRowIdx, code, quotaTypeWTMP, ageClient, countDeathSurgery, countComplication, surgeryOncology, countMorphologicalStudy, amount):
            if mapCodeToRowIdx.get(code, None):
                items = mapCodeToRowIdx[code]
                valueName = items[0]
                valueRow = items[1]
                valueSurgery = items[2] + amount
                valueSurgeryChildren14 = items[3]
                valueSurgeryChildren1 = items[4]
                valueSurgeryChildren17 = items[5]
                valueSurgeryWTMP = items[6]
                valueSurgeryWTMP14 = items[7]
                valueSurgeryWTMP1 = items[8]
                valueSurgeryWTMP17 = items[9]
                valueComplication = items[10]
                valueComplication14 = items[11]
                valueComplication1 = items[12]
                valueComplication17 = items[13]
                valueComplicationWTMP = items[14]
                valueComplicationWTMP14 = items[15]
                valueComplicationWTMP1 = items[16]
                valueComplicationWTMP17 = items[17]
                valueDeath = items[18]
                valueDeath14 = items[19]
                valueDeath1 = items[20]
                valueDeath17 = items[21]
                valueDeathWTMP = items[22]
                valueDeathWTMP14 = items[23]
                valueDeathWTMP1 = items[24]
                valueDeathWTMP17 = items[25]
                valueSurgeryOncology = items[26]
                valueMorphologicalStudy = items[27]
                if surgeryOncology:
                    valueSurgeryOncology += amount
                if quotaTypeWTMP:
                    valueSurgeryWTMP += amount
                if countComplication:
                    valueComplication += amount
                if countComplication and quotaTypeWTMP:
                    valueComplicationWTMP += amount
                if countDeathSurgery:
                    valueDeath += 1
                if countDeathSurgery and quotaTypeWTMP:
                    valueDeathWTMP += 1
                if countMorphologicalStudy:
                    valueMorphologicalStudy += amount
                valuePostsurgicalLethality = round((100.0 * float(valueDeath))/float(valueSurgery), 2)
                if ageClient < 18:
                    if ageClient >= 0 and ageClient < 15:
                        valueSurgeryChildren14 += amount
                        if quotaTypeWTMP: valueSurgeryWTMP14 += amount
                        if countComplication: valueComplication14 += amount
                        if countComplication and quotaTypeWTMP: valueComplicationWTMP14 += amount
                        if countDeathSurgery: valueDeath14 += 1
                        if countDeathSurgery and quotaTypeWTMP: valueDeathWTMP14 += 1
                    elif ageClient >= 15 and ageClient < 18:
                        valueSurgeryChildren17 += amount
                        if quotaTypeWTMP: valueSurgeryWTMP17 += amount
                        if countComplication: valueComplication17 += amount
                        if countComplication and quotaTypeWTMP: valueComplicationWTMP17 += amount
                        if countDeathSurgery: valueDeath17 += 1
                        if countDeathSurgery and quotaTypeWTMP: valueDeathWTMP17 += 1
                    if ageClient >= 0 and ageClient < 1:
                        valueSurgeryChildren1 += amount
                        if quotaTypeWTMP: valueSurgeryWTMP1 += amount
                        if countComplication: valueComplication1 += amount
                        if countComplication and quotaTypeWTMP: valueComplicationWTMP1 += amount
                        if countDeathSurgery: valueDeath1 += 1
                        if countDeathSurgery and quotaTypeWTMP: valueDeathWTMP1 += 1

                mapCodeToRowIdx[code] = (valueName, valueRow, valueSurgery, valueSurgeryChildren14, valueSurgeryChildren1,
                                         valueSurgeryChildren17, valueSurgeryWTMP, valueSurgeryWTMP14, valueSurgeryWTMP1,
                                         valueSurgeryWTMP17, valueComplication, valueComplication14, valueComplication1,
                                         valueComplication17, valueComplicationWTMP, valueComplicationWTMP14, valueComplicationWTMP1,
                                         valueComplicationWTMP17, valueDeath,  valueDeath14, valueDeath1, valueDeath17,
                                         valueDeathWTMP, valueDeathWTMP14, valueDeathWTMP1, valueDeathWTMP17,
                                         valueSurgeryOncology, valueMorphologicalStudy)
        if mapCodeToRowIdx:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            tableClient = db.table('Client')
            tableRBService = db.table('rbService')
            tableEventType = db.table('EventType')
            tableContract = db.table('Contract')
            tablePerson = db.table('Person')
            cond = [tableEvent['deleted'].eq(0),
                    tableEventType['deleted'].eq(0),
                    tableAction['deleted'].eq(0),
                    tableActionType['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tableAction['endDate'].isNotNull()
                    ]
            table = tableAction.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
            table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            if eventTypeList:
                cond.append(tableEventType['id'].inlist(eventTypeList))
            if existFlatCode:
                cond.append(tableActionType['flatCode'].ne(u''))
            if bool(begDateTime):
                cond.append(tableAction['endDate'].ge(begDateTime))
            if bool(endDateTime):
                cond.append(tableAction['endDate'].lt(endDateTime.addDays(1)))
            if selectType:
                table = table.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
            else:
                table = table.innerJoin(tablePerson, tableAction['person_id'].eq(tablePerson['id']))
            if personId:
                if selectType:
                    cond.append(tablePerson['deleted'].eq(0))
                    cond.append(tablePerson['id'].eq(personId))
                else:
                    cond.append(tablePerson['deleted'].eq(0))
                    cond.append(tablePerson['id'].eq(personId))
            if orgStructureIdList:
                if selectType:
                    cond.append(tablePerson['deleted'].eq(0))
                    cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
                else:
                    cond.append(tablePerson['deleted'].eq(0))
                    cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
            if financeId:
                cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(financeId), str(financeId)))
                table = table.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            cols = [tableAction['id'].alias('actionId'),
                    tableAction['amount'],
                    tableAction['event_id'],
                    tableAction['MKB'],
                    tableActionType['id'].alias('actionTypeId'),
                    tableActionType['group_id'].alias('groupId'),
                    tableRBService['code'] if not isNomeclature else tableActionType['flatCode'].alias('code'),
                    tableActionType['name']
                    ]
            cols.append('IF((SELECT QuotaType.class FROM QuotaType WHERE QuotaType.id = ActionType.quotaType_id LIMIT 1) = 0, 1, 0) AS quotaTypeWTMP')
            cols.append('age(Client.birthDate, Event.setDate) AS ageClient')
            cols.append('%s AS countMorphologicalStudy'%(getStringProperty(u'Направление на морфологию', u'(APS.value = \'да\' OR APS.value = \'ДА\' OR APS.value = \'Да\')')))
            cols.append('%s AS countDeathSurgery'%(getStringProperty(u'Исход операции', u'(APS.value LIKE \'умер%\' OR APS.value LIKE \'смерть%\')')))
            cols.append('%s AS countComplication'%(getStringProperty(u'Осложнение', u'(APS.value != \'\' OR APS.value != \' \')')))
            if not isNomeclature:
                table = table.innerJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
            cond.append(tableActionType['serviceType'].eq(CActionServiceType.operation))
            records = db.getRecordList(table, cols, cond, u'ActionType.group_id, %s'%(u'rbService.code' if not isNomeclature else u'ActionType.flatCode'))
            for record in records:
                quotaTypeWTMP = forceInt(record.value('quotaTypeWTMP'))
                ageClient = forceInt(record.value('ageClient'))
                countDeathSurgery = forceInt(record.value('countDeathSurgery'))
                countComplication = forceInt(record.value('countComplication'))
                countMorphologicalStudy = forceInt(record.value('countMorphologicalStudy'))
                amount = forceInt(record.value('amount'))
                code = QString(forceString(record.value('code')))
                MKBRec = normalizeMKB(forceString(record.value('MKB')))
                surgeryOncology = True if MKBRec in mapMainRows.keys() else False
                setValueMapCodeToRowIdx(mapCodeToRowIdx, u'', quotaTypeWTMP, ageClient, countDeathSurgery, countComplication, surgeryOncology, countMorphologicalStudy, amount)
                codeList = [QString(code)]
                indexPoint = code.lastIndexOf(u'.', -1, Qt.CaseInsensitive)
                while indexPoint > -1:
                    code.truncate(indexPoint)
                    codeList.append(QString(code))
                    indexPoint = code.lastIndexOf(u'.', -1, Qt.CaseInsensitive)
                for code in codeList:
                    if code:
                        setValueMapCodeToRowIdx(mapCodeToRowIdx, code, quotaTypeWTMP, ageClient, countDeathSurgery, countComplication, surgeryOncology, countMorphologicalStudy, amount)
        return mapCodeToRowIdx
