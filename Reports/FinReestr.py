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
from PyQt4 import QtGui
from PyQt4.QtCore import QDate, QDateTime, pyqtSignature

from Orgs.Utils import getOrgStructureFullName
from Reports.EconomicAnalisysSetupDialog import getCond, CEconomicAnalisysSetupDialog
from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat
from Reports.Utils import dateRangeAsStr
from library.Utils import forceString, forceDate, forceInt, forceDouble


class CFinReestr(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Финансовая сводка по реестрам')
        self.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape, leftMargin=10,
                                      topMargin=10, rightMargin=10, bottomMargin=10)
        self.isDetailed = False

    def getSetupDialog(self, parent):
        result = CFinReestrSetupDialog(parent)
        result.setTitle(u'Параметры отчёта')
        result.resize(400, 10)
        return result
    
    
    def selectData(self, params):
        stmt = u"""
    SELECT Account.number AS num, OrgStructure.bookkeeperCode AS lpu, OrgStructure.name AS lpu_name,
     Account.settleDate AS schet_date, Account.date AS schet_fact_date, rbAccountType.name AS type_reestr,
     CASE when Account.group_id in (1, 2, 9) then 'Койко-день' 
          when Account.group_id in (3, 4, 5, 6, 11, 12, 13, 14, 15, 16, 17, 24, 25, 26, 27, 28, 29, 31, 32, 33) then 'Посещение'
          when Account.group_id in (7, 10, 22) then 'День лечения' 
          when Account.group_id in (18, 19, 20, 21, 23, 30) then 'Услуга' 
          when Account.group_id = 8 then 'Вызов бригады СМП'
  END AS ed,
  COUNT(DISTINCT ai.event_id) AS kol_usl
  , Account.uet AS kol_uet
  , Account.sum AS summ
  , CONCAT(o.infisCode, ' | ', o.title) AS cont
  FROM Account
LEFT JOIN OrgStructure ON Account.orgStructure_id = OrgStructure.id
LEFT JOIN rbAccountType ON Account.type_id = rbAccountType.id
LEFT JOIN Contract ON Account.contract_id = Contract.id
LEFT JOIN rbFinance on rbFinance.id = Contract.finance_id
LEFT JOIN Organisation o ON Account.payer_id = o.id
LEFT JOIN Account_Item ai ON Account.id = ai.master_id
  WHERE %(cond)s and Account.deleted = 0 
  GROUP BY o.id, Account.id
  ORDER BY %(orderby)s
    """
        db = QtGui.qApp.db
        self.isDetailed = params.get("paydetail", False)
        params['dataType'] = 2
        cond = getCond(params)
        orderby = "Account.settleDate, Account.date"
        if self.isDetailed:
            orderby = "OrgStructure.bookkeeperCode, o.infisCode, Account.settleDate, Account.date"

        st = stmt % {"cond": cond, "orderby": orderby}
        return db.query(st)
    
    
    def getDescription(self, params):
        db = QtGui.qApp.db
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        orgStructureId = params.get('orgStructureId', None)
        typeFinanceId = params.get('financeId', None)
        contractId = params.get('contractId', None)
        accountType = params.get('accountType', 0)
        rows = []
        rows.append(u'по дате счет-фактуры')
        rows.append(dateRangeAsStr(u'за период', begDate, endDate))
        if orgStructureId:
            rows.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        if typeFinanceId is not None:
            rows.append(u'тип финансирования: ' + forceString(db.translate('rbFinance', 'id', typeFinanceId, 'name')))
        if contractId:
            rows.append(u'договор: ' + forceString(db.translate('Contract', 'id', contractId, "concat_ws(' | ', (select rbFinance.name from rbFinance where rbFinance.id = Contract.finance_id), Contract.resolution, Contract.number)")))
        if accountType:
            rows.insert(10, u'типы реестров: %s' %
                          [u"не задано", u"Только Основные", u"Основные + Дополнительные", u"Только Повторные"][
                              params.get("accountType", 0)])
        if params.get("paydetail", False):
            rows.insert(10, u'в разрезе плательщиков')
        rows.append(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        return rows
    
    
    def build(self, params):
        reportRowSize = 11
        reportData = {}
# osname = forceString(record.value('osname'))
  #              fin = forceString(record.value('fin'))
#                infis = forceString(record.value('infis'))
               # name = forceString(record.value('name'))
             #   amount = forceInt(record.value('amount'))
           #     kd = forceInt(record.value('kd'))
         #       pd = forceInt(record.value('pd'))
       #         uet = forceDouble(record.value('uet'))
     #           sum = forceDouble(record.value('sum'))
   #             cnt = forceInt(record.value('cnt'))
 #               pos = forceInt(record.value('pos'))

                #key = (osname, fin,   infis,  name)
              #  reportLine = reportData.setdefault(key, [0]*reportRowSize)
            #    reportLine[0] += amount
          #      reportLine[1] += kd
        #        reportLine[2] += pd
      #          reportLine[3] += uet
    #            reportLine[4] += sum
  #              reportLine[5] += cnt
#                 reportLine[6] += pos


        def processQuery(query):
            while query.next():
                record = query.record()
                num= forceString(record.value('num'))#name
                lpu= forceString(record.value('lpu'))#name
                lpu_name= forceString(record.value('lpu_name'))#name
                schet_date= forceDate(record.value('schet_date'))#name
                schet_fact_date= forceDate(record.value('schet_fact_date'))#name
                type_reestr= forceString(record.value('type_reestr'))#name
                ed= forceString(record.value('ed'))#name
                cont= forceString(record.value('cont'))#name
                kol_usl = forceInt(record.value('kol_usl'))#+
                kol_uet = forceDouble(record.value('kol_uet'))#+
                summ = forceDouble(record.value('summ'))#+
                if self.isDetailed:
                    key = (cont, lpu, schet_date, schet_fact_date, lpu_name, num, type_reestr,  ed)
                else:
                    key = (lpu, schet_date, schet_fact_date, lpu_name, num, type_reestr,  ed, cont)
                reportLine = reportData.setdefault(key, [0]*reportRowSize)
                
                reportLine[0] += kol_usl
                reportLine[1] += kol_uet
                reportLine[2] += summ
             #   reportLine[0] += kd
             #   reportLine[1] += sum
              #  reportLine[2] += cnt
        query = self.selectData(params)
        processQuery(query)
        
        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Финансовая сводка по реестрам')
        cursor.setCharFormat(CReportBase.ReportBody)
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        
        
        if self.isDetailed is False:
            tableColumns = [
                ('3.7%',  [ u'№ п/п'], CReportBase.AlignLeft),
                ('7.1%',  [ u'Код ЛПУ'], CReportBase.AlignLeft),
                ('16.2%',  [ u'Наименование ЛПУ'], CReportBase.AlignLeft),
                ('9.1%',  [ u'Расчётная дата'], CReportBase.AlignLeft),
                ('9.1%',  [ u'Дата счёт-фактуры'], CReportBase.AlignLeft),
                ('4%',  [ u'Номер реестра'], CReportBase.AlignLeft),
                ('14.4%',  [ u'Тип реестра'], CReportBase.AlignLeft),
                ('10.9%',  [ u'Единица учёта'], CReportBase.AlignLeft),
                ('7.3%',  [ u'Кол-во перс. счетов'], CReportBase.AlignLeft),
                ('7.3%',  [ u'Кол-во УЕТ'], CReportBase.AlignLeft),
                ('10.9%',  [ u'Сумма'], CReportBase.AlignLeft),
                ]
            table = createTable(cursor, tableColumns)
            table.mergeCells(0, 0, 1, 1)

        
        
        if self.isDetailed:
            totalBynum = [0]*reportRowSize
            totalByReport = [0]*reportRowSize
            colsShift = 8
            prevnum = None
            number = 1
            otstup = 1
            
            keys = reportData.keys()
            keys.sort()
            def drawTotal(table,  total,  text): 
        
                row = table.addRow()

                table.setText(row, 1, text, CReportBase.TableHeader)
                table.mergeCells(row, 0, 1, 8)
                for col in xrange(reportRowSize):
                    if (col<3):
                        table.setText(row, col + colsShift, total[col])
            if not keys:
                tableColumns = [
                    ('3.7%',  [ u'№ п/п'], CReportBase.AlignLeft),
                    ('7.1%',  [ u'Код ЛПУ'], CReportBase.AlignLeft),
                    ('16.2%',  [ u'Наименование ЛПУ'], CReportBase.AlignLeft),
                    ('9.1%',  [ u'Расчётная дата'], CReportBase.AlignLeft),
                    ('9.1%',  [ u'Дата счёт-фактуры'], CReportBase.AlignLeft),
                    ('4%',  [ u'Номер реестра'], CReportBase.AlignLeft),
                    ('14.4%',  [ u'Тип реестра'], CReportBase.AlignLeft),
                    ('10.9%',  [ u'Единица учёта'], CReportBase.AlignLeft),
                    ('7.3%',  [ u'Кол-во перс. счетов'], CReportBase.AlignLeft),
                    ('7.3%',  [ u'Кол-во УЕТ'], CReportBase.AlignLeft),
                    ('10.9%',  [ u'Сумма'], CReportBase.AlignLeft),
                    ]
                table = createTable(cursor, tableColumns)
            else:
                for key in keys:
                    #key = (cont, lpu, schet_date, schet_fact_date, lpu_name, num, type_reestr,  ed)
                    num = key[5]
                    cont = key[0]
                    ed = key[7]
                    type_reestr = key[6]
                    schet_fact_date = key[3]
                    schet_date = key[2]
                    lpu_name = key[4]
                    lpu = key[1]
                    #mergeCells(int row, int column, int numRows, int numCols)
                    
                
                    reportLine = reportData[key]
                    if prevnum!=None and prevnum!=cont:
                        drawTotal(table,  totalBynum, u'ИТОГО');
                        totalBynum = [0]*reportRowSize
                        
                    
                        
                    if prevnum!=cont or prevnum is None:
                        cursor.movePosition(QtGui.QTextCursor.End)                                        
                        #рисуем вторую табличку
                        if otstup>1:
                            cursor.insertBlock()
                            cursor.insertBlock()
                        otstup+=1
                        cursor.setCharFormat(CReportBase.TableHeader)
                        cursor.setBlockFormat(CReportBase.AlignLeft)
                        cursor.insertBlock()
                        cursor.insertText(cont)
                        cursor.setCharFormat(CReportBase.ReportTitle)
                        tableColumns = [
                            ('3.7%',  [ u'№ п/п'], CReportBase.AlignLeft),
                            ('7.1%',  [ u'Код ЛПУ'], CReportBase.AlignLeft),
                            ('16.2%',  [ u'Наименование ЛПУ'], CReportBase.AlignLeft),
                            ('9.1%',  [ u'Расчётная дата'], CReportBase.AlignLeft),
                            ('9.1%',  [ u'Дата счёт-фактуры'], CReportBase.AlignLeft),
                            ('4%',  [ u'Номер реестра'], CReportBase.AlignLeft),
                            ('14.4%',  [ u'Тип реестра'], CReportBase.AlignLeft),
                            ('10.9%',  [ u'Единица учёта'], CReportBase.AlignLeft),
                            ('7.3%',  [ u'Кол-во перс. счетов'], CReportBase.AlignLeft),
                            ('7.3%',  [ u'Кол-во УЕТ'], CReportBase.AlignLeft),
                            ('10.9%',  [ u'Сумма'], CReportBase.AlignLeft),
                            ]

                        table = createTable(cursor, tableColumns)
                        number=1
                        
                    row = table.addRow()            
                    table.setText(row, 0, number)
                    table.setText(row, 1, lpu)
                    table.setText(row, 2, lpu_name)
                    table.setText(row, 3, schet_date.toString("dd.MM.yyyy"))
                    table.setText(row, 4, schet_fact_date.toString("dd.MM.yyyy"))
                    table.setText(row, 5, num)
                    table.setText(row, 6, type_reestr)
                    table.setText(row, 7, ed)
                    for col in xrange(reportRowSize):
                        if (col<3):
                            table.setText(row, col + colsShift, reportLine[col])
                        totalByReport[col] = totalByReport[col] + reportLine[col]
                        totalBynum[col] = totalBynum[col] + reportLine[col]
                    prevnum = cont
                    number+=1
            #total
            
                    
            cursor.setCharFormat(CReportBase.TableHeader)
            drawTotal(table,  totalBynum, u'ИТОГО');
        else:
            for col in xrange(reportRowSize):
                table.mergeCells(0, col, 2, 1)

            totalBynum = [0]*reportRowSize
            totalByReport = [0]*reportRowSize
            colsShift = 8
            prevnum = None
            number = 1
            
            keys = reportData.keys()
            keys.sort()
            def drawTotal(table,  total,  text): 
        
                row = table.addRow()

                table.setText(row, 1, text, CReportBase.TableHeader)
                table.mergeCells(row, 0, 1, 8)
                for col in xrange(reportRowSize):
                    if (col<3):
                        table.setText(row, col + colsShift, total[col])
            for key in keys:
                #key = (lpu, schet_date,  schet_fact_date, lpu_name, num, type_reestr,  ed, cont)
                num = key[4]
                cont = key[7]
                ed = key[6]
                type_reestr = key[5]
                schet_fact_date = key[2]
                schet_date = key[1]
                lpu_name = key[3]
                lpu = key[0]
                #mergeCells(int row, int column, int numRows, int numCols)
                
            
                reportLine = reportData[key]
                
                row = table.addRow()            
                table.setText(row, 0, number)
                table.setText(row, 1, lpu)
                table.setText(row, 2, lpu_name)
                table.setText(row, 3, schet_date.toString("dd.MM.yyyy"))
                table.setText(row, 4, schet_fact_date.toString("dd.MM.yyyy"))
                table.setText(row, 5, num)
                table.setText(row, 6, type_reestr)
                table.setText(row, 7, ed)
                for col in xrange(reportRowSize):
                    if (col<3):
                        table.setText(row, col + colsShift, reportLine[col])
                    totalByReport[col] = totalByReport[col] + reportLine[col]
                    totalBynum[col] = totalBynum[col] + reportLine[col]
                prevnum = num
                number+=1
            #total
            cursor.setCharFormat(CReportBase.TableHeader)
            drawTotal(table,  totalByReport, u'ИТОГО');
        return doc


class CFinReestrSetupDialog(CEconomicAnalisysSetupDialog):
    def __init__(self, parent=None):
        CEconomicAnalisysSetupDialog.__init__(self, parent)
        self.setVisibilityProfileBed(False)
        self.setFinanceVisible(True)
        self.setSpecialityVisible(False)
        self.setPersonVisible(False)
        self.setVidPomVisible(False)
        self.setSchetaVisible(False)
        self.setPayerVisible(False)
        self.setEventTypeVisible(False)
        self.setSexVisible(False)
        self.setDetailToVisible(False)
        self.setRazrNasVisible(False)
        self.setAgeVisible(False)
        self.setNoschetaVisible(False)
        self.setNoschetaEnabled(False)
        self.setDateTypeVisible(False)
        self.edtBegTime.setVisible(False)
        self.edtEndTime.setVisible(False)
        self.setPriceVisible(False)
        self.setDetailVisible(True)


    def setTitle(self, title):
        self.setWindowTitle(title)
        
    def setVisibilityForDateType(self, datetype):
        pass


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.cmbPerson.setBegDate(date)
        self.updateContractFilter()

    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.cmbPerson.setEndDate(date)
        self.updateContractFilter()

    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)

    @pyqtSignature('int')
    def on_cmbFinance_currentIndexChanged(self, index):
        self.updateContractFilter()
