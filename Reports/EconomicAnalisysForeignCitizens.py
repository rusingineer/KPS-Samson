# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, QDateTime

from Reports.EconomicAnalisys import colClient, colClientName, colClientSex, colClientBirthDate, colCitizenship, \
    colEvent, colKPK, colEventOrder, colEventSetDate, colEventExecDate, colSUM, getStmt, colFinance, \
    colSpecialityOKSOName, colMKBCode
from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase
from Reports.Utils import dateRangeAsStr

from library.Utils import forceString, forceInt, forceDouble, forceDate, forceBool
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog


class CEconomicAnalisysForeignCitizens(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Выполненные объемы услуг иностранным гражданам')

    def selectData(self, params, tablePart):

        cols = [colClient, colClientName, colClientSex, colClientBirthDate, colCitizenship, colEvent, colKPK if tablePart != 3 else colSpecialityOKSOName, colMKBCode, colEventOrder, colEventSetDate, colEventExecDate, colFinance, colSUM]
        colsStmt = u"""select colClient as clientId,
                colClientName as fio,
                colClientSex as clientSex,
                colClientBirthDate as clientBirthDate,
                colCitizenship as countryFullName,
                colEvent as eventId,
                {0},
                colMKBCode as colMKBCode,
                colEventOrder as eventOrder,
                colEventSetDate as eventSetDate,
                colEventExecDate as eventExecDate,
                colFinance as financeName,
                round(sum(colSUM), 2) as sum
                """.format('colKPK' if tablePart != 3 else 'colSpecialityOKSOName as colKPK')
        groupCols = u'colClient, colClientName, colClientSex, colClientBirthDate, colCitizenship, colEvent, {0}, colMKBCode, colEventOrder, colEventSetDate, colEventExecDate, colFinance'.format('colKPK' if tablePart != 3 else 'colSpecialityOKSOName')
        orderCols = u'colClientName, colClientSex, colClientBirthDate, colCitizenship'
        additionCond = u" AND rbSocStatusType.code <> 'м643'"
        if tablePart == 1:
            additionCond += u" AND mt.code in ('1', '2', '3') and mt.regionalCode not in ('111', '112')"
        elif tablePart == 2:
            additionCond += u" AND mt.code = 7"
        elif tablePart == 3:
            additionCond += u" AND (mt.code not in ('1', '2', '3', '7') or (mt.code = '1' and  mt.regionalCode in ('111', '112')))"
        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params, additionCond=additionCond)

        db = QtGui.qApp.db
        return db.query(stmt)


    def build(self, description, params):
        reportRowSize = 12
        reportData = {}

        def processQuery(query):
            while query.next():
                record = query.record()
                clientCode = forceInt(record.value('clientId'))
                finance = forceString(record.value('financeName'))
                fio = forceString(record.value('fio'))
                sum = forceDouble(record.value('sum'))
                sex = forceInt(record.value('clientSex'))
                if sex == 1:
                    sex = u'М'
                elif sex == 2:
                    sex = u'Ж'
                birthDate = forceString(record.value('clientBirthDate'))
                countryName = forceString(record.value('countryFullName'))
                cardCode = forceString(record.value('eventId'))
                profMP = u''
                if forceBool(record.value('specialityName')):
                    profMP = forceString(record.value('specialityName'))
                elif forceBool(record.value('colKPK')):
                    profMP = forceString(record.value('colKPK'))
                mkb = forceString(record.value('colMKBCode'))
                eventOrder = forceInt(record.value('eventOrder'))
                if eventOrder == 1:
                    eventOrder = u'плановый'
                elif eventOrder == 2:
                    eventOrder = u'экстренный'
                elif eventOrder == 3:
                    eventOrder = u'самотёком'
                elif eventOrder == 4:
                    eventOrder = u'принудительный'
                elif eventOrder == 5:
                    eventOrder = u'внутренний перевод'
                elif eventOrder == 6:
                    eventOrder = u'неотложный'

                eventSetDate = forceString(forceDate(record.value('eventSetDate')))
                eventExecDate = forceString(forceDate(record.value('eventExecDate')))

                key = (finance if finance else u'Не задано')
                reportLine = reportData.setdefault(key, [0] * 0)
                tableRow = [clientCode,
                            fio,
                            sex,
                            birthDate,
                            countryName,
                            cardCode,
                            profMP,
                            mkb,
                            eventOrder,
                            eventSetDate,
                            eventExecDate,
                            sum]
                reportLine.append(tableRow)

        tableColumns = [
            ('5%', [u'Код пациента'], CReportBase.AlignLeft),
            ('20%', [u'ФИО'], CReportBase.AlignLeft),
            ('5%', [u'Пол'], CReportBase.AlignCenter),
            ('10%', [u'Дата рождения'], CReportBase.AlignCenter),
            ('10%', [u'Гражданство'], CReportBase.AlignLeft),
            ('10%', [u'Код карточки'], CReportBase.AlignCenter),
            ('10%', [u'Профиль МП'], CReportBase.AlignLeft),
            ('5%', [u'МКБ'], CReportBase.AlignLeft),
            ('5%', [u'Порядок оказания МП'], CReportBase.AlignLeft),
            ('5%', [u'Дата начала'], CReportBase.AlignCenter),
            ('5%', [u'Дата окончания'], CReportBase.AlignCenter),
            ('5%', [u'Сумма, руб.'], CReportBase.AlignRight),
        ]

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        def fillTable(cursor, title):
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u' ')
            cursor.insertBlock()
            cursor.setCharFormat(CReportBase.ReportSubTitle)
            cursor.insertText(title)
            cursor.insertBlock()
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertText(description)
            cursor.insertBlock()
            table = createTable(cursor, tableColumns)
            table.mergeCells(1, 2, 1, 12)
            colsShift = 0
            prevFinance = None
            keys = reportData.keys()
            keys.sort()

            countByFinance = 0
            countAll = 0
            sumByFinance = 0
            sumAll = 0
            for key in keys:
                finance = key
                if prevFinance != finance:
                    if prevFinance is not None:
                        row = table.addRow()
                        table.setText(row, 0, u'Итого по %s' % prevFinance)
                        table.setText(row, 2, u'человек: {0}'.format(countByFinance))
                        table.setText(row, 11, u'{0}'.format(sumByFinance))
                        table.mergeCells(row, 1, 1, 10)
                        countAll += countByFinance
                        sumAll += sumByFinance

                    row = table.addRow()
                    table.setText(row, 0, u'Вид финансирования: %s' % finance, CReportBase.TableHeader)
                    table.mergeCells(row, 0, 1, 12)
                    prevFinance = finance
                    countByFinance = 0
                    sumByFinance = 0

                reportLine = reportData[key]
                for report in reportLine:
                    if report:
                        countByFinance += 1
                        sumByFinance += report[11]
                        rowReport = table.addRow()
                        for col in xrange(reportRowSize):
                            table.setText(rowReport, col + colsShift, report[col])

            if prevFinance is not None:
                row = table.addRow()
                table.setText(row, 0, u'Итого по %s' % prevFinance)
                table.setText(row, 2, u'человек: {0}'.format(countByFinance))
                table.setText(row, 11, u'{0}'.format(sumByFinance))
                table.mergeCells(row, 1, 1, 10)
                countAll += countByFinance
                sumAll += sumByFinance

            row = table.addRow()
            table.setText(row, 0, u'Всего')
            table.setText(row, 2, u'человек: {0}'.format(countAll))
            table.setText(row, 11, u'{0}'.format(sumAll))
            table.mergeCells(row, 1, 1, 10)
            cursor.movePosition(QtGui.QTextCursor.End)

        query = self.selectData(params, 1)
        processQuery(query)
        fillTable(cursor, u'Стационарная медицинская помощь')
        reportData = {}
        query = self.selectData(params, 2)
        processQuery(query)
        fillTable(cursor, u'Стационарозамещающая медицинская помощь')
        reportData = {}
        query = self.selectData(params, 3)
        processQuery(query)
        fillTable(cursor, u'Амбулаторная медицинская помощь')
        return doc


class CEconomicAnalisysForeignCitizensEx(CEconomicAnalisysForeignCitizens):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysForeignCitizens.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.cmbOrgStructure.setVisible(False)
        result.cmbSpeciality.setVisible(False)
        result.cmbPerson.setVisible(False)
        result.cmbContract.setVisible(False)
        result.cmbEventType.setVisible(False)
        result.cmbFinance.setVisible(False)
        result.cmbDetailTo.setVisible(False)
        result.cmbNoscheta.setVisible(False)
        result.cmbPayer.setVisible(False)
        result.cmbProfileBed.setVisible(False)
        result.cmbRazrNas.setVisible(False)
        result.cmbScheta.setVisible(False)
        result.cmbStepECO.setVisible(False)
        result.cmbtypePay.setVisible(False)
        result.cmbVidPom.setVisible(False)
        result.lblContract.setVisible(False)
        result.lblDetailTo.setVisible(False)
        result.lblEventType.setVisible(False)
        result.lblFinance.setVisible(False)
        result.lblNoscheta.setVisible(False)
        result.lblPayer.setVisible(False)
        result.lblPerson.setVisible(False)
        result.lblProfileBed.setVisible(False)
        result.lblRazrNas.setVisible(False)
        result.lblScheta.setVisible(False)
        result.lblSpeciality.setVisible(False)
        result.lblStepECO.setVisible(False)
        result.lbltypePay.setVisible(False)
        result.lblVidPom.setVisible(False)
        result.grpdatetype.setVisible(False)
        result.cbPrice.setVisible(False)
        result.setSexVisible(False)
        result.setAgeVisible(False)
        result.lblOrgStructure.setVisible(False)
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        description = []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        begTime = params.get('begTime', None)
        endTime = params.get('endTime', None)
        begDateTime = None
        endDateTime = None
        if begTime and endTime:
            begDateTime = QDateTime(begDate, begTime)
            endDateTime = QDateTime(endDate, endTime)
        dateType = params.get('dataType', None)
        description.append(u'по закрытым событиям')
        if dateType != 3 and (begDate or endDate):
            if begDateTime and endDateTime:
                description.append(dateRangeAsStr(u'за период', begDateTime, endDateTime))
            else:
                description.append(dateRangeAsStr(u'за период', begDate, endDate))
        description.append(u'отчёт составлен:' + forceString(QDateTime.currentDateTime()))
        return CEconomicAnalisysForeignCitizens.build(self, '\n'.join(description), params)
