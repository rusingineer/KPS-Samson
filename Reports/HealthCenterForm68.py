# -*- coding: utf-8 -*-
# from datetime import date
from datetime import date

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QDate, QString

from Orgs.Utils import getOrgStructureDescendants
from Reports.Ui_HealthCenterForm68SetupDialog import Ui_HealthCenterForm68SetupDialog
from library.DialogBase import CDialogBase

from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable, forceString
from library.Utils import forceDate, forceInt


def selectData2001(begDate, endDate,regionCode ):
    stmt=u"""
SELECT 0 as ind,
       count(e.id) as Total,
       count(usl.pervichno ) as FirstTime,
      sum( act.Zdorov) as Zdorov, 
      count(e.id) - sum( act.Zdorov) as Risk, 
      sum(act.IndPlan) as IndPlan
from Event e 
left join EventType et on et.id = e.eventType_id
left join rbMedicalAidType mt on et.medicalAidType_id = mt.id
inner JOIN
(select a.event_id,
 max(case when at.flatCode = 'end_san' and at.code = '1-04-06' and apt.name ='Факторы риска заболеваний' and( aps.value = '' or aps.value = 'не выявлено' )then 1 else 0 end) as Zdorov,
 max(case when at.flatCode = 'sur_san' and at.code = '1-04-05' and apt.name = 'Индивидуальный план' and aps.value = '' then 0 else 1 end) as IndPlan
from  Action a 
left join ActionType at on a.actionType_id = at.id 
left join ActionProperty ap on ap.action_id = a.id and ap.deleted=0
left join ActionPropertyType apt on ap.type_id = apt.id and ap.deleted=0
left join ActionProperty_String aps on aps.id = ap.id
group by a.event_id)act on act.event_id = e.id
left JOIN
(select v.event_id as pervichno from Visit v 
left join rbService rbs on v.service_id = rbs.id
where rbs.code ='B01.069.014' and v.deleted=0
group by v.event_id) usl on usl.pervichno = e.id
where  e.deleted = 0 and mt.regionalCode = '%s' AND %s
group by ind

UNION ALL

SELECT isObr as ind,
       count(e.id) as Total,
       count(usl.pervichno ) as FirstTime,
      sum( act.Zdorov) as Zdorov, 
      count(e.id) - sum( act.Zdorov) as Risk, 
      sum(act.IndPlan) as IndPlan
from Event e 
left join EventType et on et.id = e.eventType_id
left join rbMedicalAidType mt on et.medicalAidType_id = mt.id
inner JOIN
(select a.event_id,
 max(case when at.flatCode = 'app_san' and at.code = '1-04-03' and apt.name ='Вид обращения' then case aps.value when 'Обратился самостоятельно'  then 1 
                                                       when 'Направлен амбулаторно-поликлиническим учреждением' then 2
                                                       when 'Направлен после лечения в стационаре'then 3
                                                       when 'Направлен после дополнительной диспансеризации' then 4
                                                       when 'Направлен работодателем после прохождения ПМО и УМО' then 5 
                                                       else 0 end else 0 end )as isObr,
 max(case when at.flatCode = 'end_san' and at.code = '1-04-06' and apt.name ='Факторы риска заболеваний' and( aps.value = '' or aps.value = 'не выявлено' )then 1 else 0 end) as Zdorov,
 max(case when at.flatCode = 'sur_san' and at.code = '1-04-05' and apt.name = 'Индивидуальный план' and aps.value = '' then 0 else 1 end) as IndPlan
from  Action a 
left join ActionType at on a.actionType_id = at.id 
left join ActionProperty ap on ap.action_id = a.id and ap.deleted=0
left join ActionPropertyType apt on ap.type_id = apt.id and ap.deleted=0
left join ActionProperty_String aps on aps.id = ap.id
group by a.event_id)act on act.event_id = e.id
left JOIN
(select v.event_id as pervichno from Visit v 
left join rbService rbs on v.service_id = rbs.id
where rbs.code ='B01.069.014' and v.deleted=0
group by v.event_id) usl on usl.pervichno = e.id
where  e.deleted = 0 and  mt.regionalCode ='%s' and isObr>0 AND %s
group by  ind 
"""
    db = QtGui.qApp.db
    tableEvent  = db.table('Event').alias('e')
    cond = []
    cond.append(tableEvent['execDate'].ge(begDate))
    cond.append(db.joinOr([tableEvent['execDate'].lt(endDate.addDays(1)), tableEvent['execDate'].isNull()]))
    return db.query(stmt % (regionCode,db.joinAnd(cond),regionCode,db.joinAnd(cond)))

def selectData2003(begDate, endDate ):
    stmt=u"""
SELECT 
      count(case when age(c.birthDate,e.execDate)<15 then  e.id end) as Total14,
      count(case when age(c.birthDate,e.execDate)>14 then  e.id end) as Total17,
      sum(case when age(c.birthDate,e.execDate)<15 then   act.Zdorov end) as Zdorov14, 
      sum(case when age(c.birthDate,e.execDate)>14 then act.Zdorov end) as Zdorov17, 
      count(case when age(c.birthDate,e.execDate)<15 then e.id end) - sum(case when age(c.birthDate,e.execDate)<15 then act.Zdorov end) as Risk14, 
      count(case when age(c.birthDate,e.execDate)>14 then e.id end) - sum(case when age(c.birthDate,e.execDate)>14 then act.Zdorov end) as Risk17, 
      sum(case when age(c.birthDate,e.execDate)<15 then  act.IndPlan end) as IndPlan14,
      sum(case when age(c.birthDate,e.execDate)>14 then act.IndPlan end) as IndPlan17
from Event e 
left join Client c on c.id = e.client_id
left join EventType et on et.id = e.eventType_id
left join rbMedicalAidType mt on et.medicalAidType_id = mt.id
inner JOIN
(select a.event_id,
 max(case when at.flatCode = 'end_san' and at.code = '1-04-06' and apt.name ='Факторы риска заболеваний' and( aps.value = '' or aps.value = 'не выявлено' )then 1 else 0 end) as Zdorov,
 max(case when at.flatCode = 'sur_san' and at.code = '1-04-05' and apt.name = 'Индивидуальный план' and aps.value = '' then 0 else 1 end) as IndPlan
from  Action a 
left join ActionType at on a.actionType_id = at.id 
left join ActionProperty ap on ap.action_id = a.id and ap.deleted=0
left join ActionPropertyType apt on ap.type_id = apt.id and ap.deleted=0
left join ActionProperty_String aps on aps.id = ap.id
group by a.event_id)act on act.event_id = e.id
left JOIN
(select v.event_id as pervichno from Visit v 
left join rbService rbs on v.service_id = rbs.id
where rbs.code ='B01.069.014' and v.deleted=0
group by v.event_id) usl on usl.pervichno = e.id
where  e.deleted = 0 and mt.regionalCode = '02' AND %s
"""
    db = QtGui.qApp.db
    tableEvent  = db.table('Event').alias('e')
    cond = []
    cond.append(tableEvent['execDate'].ge(begDate))
    cond.append(db.joinOr([tableEvent['execDate'].lt(endDate.addDays(1)), tableEvent['execDate'].isNull()]))
    return db.query(stmt % (db.joinAnd(cond)))

def selectData2005(begDate, endDate ):
    stmt=u"""
SELECT p.name,
      sum(act.Zdorov) as zdorovTotal,
      sum(case when mt.regionalCode = '02' then  act.Zdorov end) as zdorovDeti,
      sum(case when mt.regionalCode = '02' and age(c.birthDate,e.execDate)<15 then   act.Zdorov end) as zdorov14, 
      sum(case when mt.regionalCode = '02' and age(c.birthDate,e.execDate)>14 then act.Zdorov end) as zdorov17, 
      count(e.id)-sum(act.Zdorov) as riskTotal,
      count(case when mt.regionalCode = '02' then e.id end) - sum(case when mt.regionalCode = '02' then  act.Zdorov end) as riskDeti,
      count(case when  mt.regionalCode = '02' and age(c.birthDate,e.execDate)<15 then e.id end) - sum(case when  mt.regionalCode = '02' and age(c.birthDate,e.execDate)<15 then act.Zdorov end) as risk14, 
      count(case when  mt.regionalCode = '02' and age(c.birthDate,e.execDate)>14 then e.id end) - sum(case when  mt.regionalCode = '02' and age(c.birthDate,e.execDate)>14 then act.Zdorov end) as risk17 
from Event e 
left join Client c on c.id = e.client_id
left join EventType et on et.id = e.eventType_id
left join rbMedicalAidType mt on et.medicalAidType_id = mt.id
inner join vrbPerson p on p.id = e.execPerson_id
left JOIN
(select a.event_id,
 max(case when at.flatCode = 'end_san' and at.code = '1-04-06' and apt.name ='Факторы риска заболеваний' and( aps.value = '' or aps.value = 'не выявлено' )then 1 else 0 end) as Zdorov
from  Action a 
left join ActionType at on a.actionType_id = at.id 
left join ActionProperty ap on ap.action_id = a.id and ap.deleted=0
left join ActionPropertyType apt on ap.type_id = apt.id and ap.deleted=0
left join ActionProperty_String aps on aps.id = ap.id
group by a.event_id)act on act.event_id = e.id
where   mt.regionalCode in ('01','02') AND e.deleted = 0 AND %s
group by p.name
order by p.name
"""
    db = QtGui.qApp.db
    tableEvent  = db.table('Event').alias('e')
    cond = []
    cond.append(tableEvent['execDate'].ge(begDate))
    cond.append(db.joinOr([tableEvent['execDate'].lt(endDate.addDays(1)), tableEvent['execDate'].isNull()]))
    return db.query(stmt % (db.joinAnd(cond)))

def selectData2006(begDate, endDate ):
    stmt=u"""
select case apt.name   when 'Скрининг-оценка уровня психофизиологического и соматического здоровья, функциональных и адаптивных резервов организма, параметры физического развития' then 1
                       when 'Экспресс-оценка состояния сердца по ЭКГ-сигналам от конечностей' then 2
                       when 'Ангиологический скрининг с автоматическим измерением систолического артериального давления и расчета плече-лодыжечного индекса'then 3
                       when 'Комплексная детальная оценка функций дыхательной системы - компьютеризированная спирометрия' then 4
                       when 'Биоимпедансметрия (процентное соотношение воды, мышечной массы и жировой ткани)' then 5
                       when 'Определение общего холестерина и глюкозы в крови (с принадлежностями) (заключение)' then 6
                       when 'Исследование на наличие наркотических средств, психотропных веществ и их метаболитов в биологических средах организма' then 7
                       when 'Анализ CO выдыхаемого воздуха с определением карбоксигемоглобина' then 8
                       when 'Анализ котинина и других биологических маркеров в крови и моче' then 9
                       when 'Определение содержания CO в выдыхаемом воздухе' then 10
                       when 'Пульсоксиметрия (заключение)' then 12
                       when 'Стоматологическое обследование (диагностика кариеса зубов, болезней пародонта, некариозных поражений, болезней слизистой оболочки и регистрация стоматологического статуса пациента)' then 13
                       when 'Офтальмологическое обследование (проверка остроты зрения, рефрактометрия, тонометрия, исследование бинокулярного зрения, определение вида и степени аметропии, наличия астигматизма)' then 14
                       end as typeId,
                       apt.name,
count(distinct c.id) as clientTotal,
count(distinct(case when  mt.regionalCode ='02' then c.id end )) as clientDeti,
count(distinct (case when aps.id then  e.id end)) eventTotal,
count(distinct(case when aps.id and   mt.regionalCode ='02' then e.id end )) eventDeti,
count(distinct(select e1.client_id from Event e1 
left join Action a1  on a1.event_id = e1.id 
left join ActionType at1 on a1.actionType_id = at1.id 
left join ActionProperty ap1 on ap1.action_id = a1.id and ap1.deleted=0
left join ActionPropertyType apt1 on ap1.type_id = apt1.id and ap1.deleted=0
left join ActionProperty_String aps1 on aps1.id = ap1.id 
where e1.id = e.id  and ap1.deleted=0 and at1.flatCode = 'end_san' and at1.code = '1-04-06' and apt1.name ='Факторы риска заболеваний' and not( aps.value = '' or aps.value = 'не выявлено' ))) riskTotal,
count(distinct(select e1.client_id from Event e1 
left join Action a1  on a1.event_id = e1.id 
left join ActionType at1 on a1.actionType_id = at1.id 
left join ActionProperty ap1 on ap1.action_id = a1.id and ap1.deleted=0
left join ActionPropertyType apt1 on ap1.type_id = apt1.id and ap1.deleted=0
left join ActionProperty_String aps1 on aps1.id = ap1.id 
where e1.id = e.id and mt.regionalCode='02'  and ap1.deleted=0 and at1.flatCode = 'end_san' and at1.code = '1-04-06' and apt1.name ='Факторы риска заболеваний' and not( aps.value = '' or aps.value = 'не выявлено' ))) riskDeti

from Event e 
left join Client c on c.id = e.client_id
left join EventType et on et.id = e.eventType_id
left join rbMedicalAidType mt on et.medicalAidType_id = mt.id
left join Action a  on a.event_id = e.id 
left join ActionType at on a.actionType_id = at.id and at.flatCode = 'sur_san' and at.code = '1-04-05'
left join ActionProperty ap on ap.action_id = a.id and ap.deleted=0
left join ActionPropertyType apt on ap.type_id = apt.id and ap.deleted=0 and  apt.name in 
('Скрининг-оценка уровня психофизиологического и соматического здоровья, функциональных и адаптивных резервов организма, параметры физического развития',
'Экспресс-оценка состояния сердца по ЭКГ-сигналам от конечностей',
'Ангиологический скрининг с автоматическим измерением систолического артериального давления и расчета плече-лодыжечного индекса',
'Комплексная детальная оценка функций дыхательной системы - компьютеризированная спирометрия',
'Биоимпедансметрия (процентное соотношение воды, мышечной массы и жировой ткани)',
'Анализ CO выдыхаемого воздуха с определением карбоксигемоглобина',
'Анализ котинина и других биологических маркеров в крови и моче',
'Пульсоксиметрия (заключение)',
'Определение общего холестерина и глюкозы в крови (с принадлежностями) (заключение)',
'Определение содержания CO в выдыхаемом воздухе',
'Офтальмологическое обследование (проверка остроты зрения, рефрактометрия, тонометрия, исследование бинокулярного зрения, определение вида и степени аметропии, наличия астигматизма)',
'Стоматологическое обследование (диагностика кариеса зубов, болезней пародонта, некариозных поражений, болезней слизистой оболочки и регистрация стоматологического статуса пациента)',
'Исследование на наличие наркотических средств, психотропных веществ и их метаболитов в биологических средах организма')
left join ActionProperty_String aps on aps.id = ap.id 
where  e.deleted = 0 and  mt.regionalCode in ('01','02') and ap.type_id is not null and apt.name is not null AND %s
group by typeId,apt.name
order by typeId"""
    db = QtGui.qApp.db
    tableEvent = db.table('Event').alias('e')
    cond = []
    cond.append(tableEvent['execDate'].ge(begDate))
    cond.append(db.joinOr([tableEvent['execDate'].lt(endDate.addDays(1)), tableEvent['execDate'].isNull()]))
    return db.query(stmt % (db.joinAnd(cond)))

def selectData2008(begDate, endDate ):
    stmt=u"""
select count(distinct e.id) as total,
count(distinct(case when  mt.regionalCode ='02' then e.id end )) totalDeti,
count(distinct (case when aps.id then  e.id end)) procedura
from Event e 
left join EventType et on et.id = e.eventType_id
left join rbMedicalAidType mt on et.medicalAidType_id = mt.id
left join Action a  on a.event_id = e.id 
left join ActionType at on a.actionType_id = at.id and at.flatCode = 'end_san' and at.code = '1-04-06'
left join ActionProperty ap on ap.action_id = a.id and ap.deleted=0
left join ActionPropertyType apt on ap.type_id = apt.id and ap.deleted=0 and  apt.name ='Посещение кабинета (зала) ЛФК' 
left join ActionProperty_String aps on aps.id = ap.id 
where  mt.regionalCode in ('01','02') AND e.deleted = 0 AND %s """
    db = QtGui.qApp.db
    tableEvent  = db.table('Event').alias('e')
    cond = []
    cond.append(tableEvent['execDate'].ge(begDate))
    cond.append(db.joinOr([tableEvent['execDate'].lt(endDate.addDays(1)), tableEvent['execDate'].isNull()]))
    return db.query(stmt % (db.joinAnd(cond)))

def selectData2009(begDate, endDate ):
    stmt=u"""
select count(distinct e.id) as total,
count(distinct(case when  mt.regionalCode ='02' then e.id end )) totalDeti,
count(distinct (case when aps.id then  e.id end)) school,
count(distinct(case when aps.id and   mt.regionalCode ='02' then e.id end )) schoolDeti,
count(distinct(case when INSTR(aps.value,'Школа профилактики артериальной гипертензии')>0 then e.id  end))  school3,
count(distinct(case when  mt.regionalCode ='02' and INSTR(aps.value,'Школа профилактики артериальной гипертензии')>0 then e.id  end)) schoolDeti3,
count(distinct(case when INSTR(aps.value,'Школа профилактики заболеваний суставов и позвоночника')>0 then e.id  end)) school4,
count(distinct(case when  mt.regionalCode ='02' and  INSTR(aps.value,'Школа профилактики заболеваний суставов и позвоночника')>0 then e.id  end)) schoolDeti4,
count(distinct(case when INSTR(aps.value,'Школа профилактики бронхиальной астмы')>0 then e.id  end)) school5,
count(distinct(case when  mt.regionalCode ='02' and  INSTR(aps.value,'Школа профилактики бронхиальной астмы')>0 then e.id  end)) schoolDeti5,
count(distinct(case when INSTR(aps.value,'Школа профилактики сахарного диабета')>0 then e.id  end)) school6,
count(distinct(case when  mt.regionalCode ='02' and   INSTR(aps.value,'Школа профилактики сахарного диабета')>0 then e.id  end)) schoolDeti6,
count(distinct(case when INSTR(aps.value,'Прочие школы')>0 then e.id  end)) school7, 
count(distinct(case when  mt.regionalCode ='02' and  INSTR(aps.value,'Прочие школы')>0 then e.id  end)) schoolDeti7
from Event e 
left join EventType et on et.id = e.eventType_id
left join rbMedicalAidType mt on et.medicalAidType_id = mt.id
left join Action a  on a.event_id = e.id 
left join ActionType at on a.actionType_id = at.id and at.flatCode = 'end_san' and at.code = '1-04-06'
left join ActionProperty ap on ap.action_id = a.id and ap.deleted=0
left join ActionPropertyType apt on ap.type_id = apt.id and ap.deleted=0 and  apt.name ='Школы здоровья' 
left join ActionProperty_String aps on aps.id = ap.id 
where  mt.regionalCode in ('01','02') AND e.deleted = 0  AND %s """
    db = QtGui.qApp.db
    tableEvent  = db.table('Event').alias('e')
    cond = []
    cond.append(tableEvent['execDate'].ge(begDate))
    cond.append(db.joinOr([tableEvent['execDate'].lt(endDate.addDays(1)), tableEvent['execDate'].isNull()]))
    return db.query(stmt % (db.joinAnd(cond)))


class CHealthCenterForm68SetupDialog(CDialogBase, Ui_HealthCenterForm68SetupDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.on_cmbType_currentIndexChanged(0)

    def setParams(self, params):
        begDate = params.get('begDate', QDate.currentDate())
        endDate = params.get('endDate', QDate.currentDate())
        self.edtReportYear.setValue(begDate.year())
        if begDate.month() == 1 and endDate.month() == 12:
            self.cmbType.setCurrentIndex(0)
        else:
            self.cmbType.setCurrentIndex(1)
            self.cmbMonth.setCurrentIndex(endDate.month()-1)
            if begDate.month() < endDate.month():
               self.chkCumulativeTotal.setChecked(True)
        return


    def params(self):
        result = {}

        begMonth = 1
        endMonth = self.cmbMonth.currentIndex() + 1
        
        if self.cmbType.currentIndex() == 1 and not self.chkCumulativeTotal.isChecked():
            begMonth = endMonth

        begDate = QDate(self.edtReportYear.value(), begMonth, 1)

        if self.cmbType.currentIndex() == 0:
            endDate = begDate.addYears(1)
        else:
            endDate = QDate(self.edtReportYear.value(), endMonth, 1).addMonths(1)

        endDate = endDate.addDays(-1)

        result['begDate'] = begDate
        result['endDate'] = endDate
        return result


    @pyqtSignature('int')
    def on_cmbType_currentIndexChanged(self, index):
        if self.cmbType.currentIndex() == 0:
            self.chkCumulativeTotal.setVisible(False)
            self.lblMonth.setVisible(False)
            self.cmbMonth.setVisible(False)
        else:
            self.chkCumulativeTotal.setVisible(True)
            self.lblMonth.setVisible(True)
            self.cmbMonth.setVisible(True)

class CHealthCenterForm68(CReport):
    name = u'Форма 68 Сведения о деятельности центра здоровья'

    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(self.name)

    def getSetupDialog(self, parent):
        result = CHealthCenterForm68SetupDialog(parent)
        return result

    def getTable1001(self, cursor):
        tableColumns = [('50%', [u'Наименование подразделений и кабинетов', u'1'], CReportBase.AlignLeft),
                ('5%', [u'№ строки',   u'2'], CReportBase.AlignRight),
                ('45%', [u'Всего кабинетов', u'3'], CReportBase.AlignRight),
                ]


        table = createTable(cursor, tableColumns)

        i = table.addRow()
        table.setText(i, 0, u'Кабинет тестирования на аппаратно-программном комплексе')
        table.setText(i, 1, u'01')
        i = table.addRow()
        table.setText(i, 0, u'Кабинет инструментально-лабораторного обследования')
        table.setText(i, 1, u'02')
        i = table.addRow()
        table.setText(i, 0, u'Лечебно-физкультурный кабинет (зал)')
        table.setText(i, 1, u'03')
        i = table.addRow()
        table.setText(i, 0, u'Кабинет школы здоровья*')
        table.setText(i, 1, u'04')
        i = table.addRow()
        table.setText(i, 0, u'Кабинет здорового ребенка')
        table.setText(i, 1, u'05')
        i = table.addRow()
        table.setText(i, 0, u'Кабинет врача, прошедшего тематическое усовершенствование по формированию здорового образа жизни')
        table.setText(i, 1, u'06')
        i = table.addRow()
        table.setText(i, 0, u'Прочие**')
        table.setText(i, 1, u'07')

    def getTable1200(self, cursor):
        tableColumns = [('35%', [u'Наименование',u'', u'1'], CReportBase.AlignLeft),
                ('5%', [u'№ строки', u'',  u'2'], CReportBase.AlignRight),
                ('10%', [u'Число должностей', u'штатные', u'3'], CReportBase.AlignRight),
                ('10%', [u'', u'занятые', u'4'], CReportBase.AlignRight),
                ('10%', [u'Число физических лиц на занятых должностях', u'основные работники', u'5'], CReportBase.AlignRight),
                ('10%', [u'', u'совместители', u'6'], CReportBase.AlignRight),
                ('8%', [u'Наличие* квалификационной категории', u'Высшая', u'7'], CReportBase.AlignRight),
                ('6%', [u'', u'I', u'8'], CReportBase.AlignRight),
                ('6%', [u'', u'II', u'9'], CReportBase.AlignRight),
                ]


        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 1, 2)
        table.mergeCells(0, 4, 1, 2)
        table.mergeCells(0, 6, 1, 3)

        i = table.addRow()
        table.setText(i, 0, u'Врачи всего')
        table.setText(i, 1, u'01')
        i = table.addRow()
        table.setText(i, 0, u'в том числе руководители')
        table.setText(i, 1, u'02')
        i = table.addRow()
        table.setText(i, 0, u'из числа врачей (стр.01) прошли тематическое усовершенствование по формированию здорового образа жизни -всего')
        table.setText(i, 1, u'03')
        i = table.addRow()
        table.setText(i, 0, u'в том числе руководители')
        table.setText(i, 1, u'04')
        i = table.addRow()
        table.setText(i, 0, u'Средний медицинский персонал')
        table.setText(i, 1, u'05')
        i = table.addRow()
        table.setText(i, 0, u'Прочий персонал (программист)')
        table.setText(i, 1, u'06')
        i = table.addRow()
        table.setText(i, 0, u'Всего по Центру здоровья')
        table.setText(i, 1, u'07')

    def getTable1300(self, cursor):
        tableColumns = [('70%', [u'Наименование оборудования', u'1'], CReportBase.AlignLeft),
                ('4%', [u'№ строки',   u'2'], CReportBase.AlignRight),
                ('13%', [u'Количество единиц', u'3'], CReportBase.AlignRight),
                ('13%', [u'Количество введённого в эксплуатацию', u'4'], CReportBase.AlignRight),
                ]


        table = createTable(cursor, tableColumns)

        i = table.addRow()
        table.setText(i, 0, u'АПК для скрин-оцен.уровня психфиз.и сомат.здоровья,функц.и адапт.резервов орг-ма с компл.оборуд.для измер.парам.физ.развития')
        table.setText(i, 1, u'01')
        i = table.addRow()
        table.setText(i, 0, u'Система скрининга сердца компьютеризированная (экспресс-оценка состояния сердца по ЭКГ-сигналам  от конечностей)')
        table.setText(i, 1, u'02')
        i = table.addRow()
        table.setText(i, 0, u'Система ангиологич. скрининга с автоматическим измерением сист.артериального давления и расчета плече-лодыжечного индекса	')
        table.setText(i, 1, u'03')
        i = table.addRow()
        table.setText(i, 0, u'Аппарат для комплексной детальной оценки функций дыхательной системы (спирометр компьютеризированный)')
        table.setText(i, 1, u'04')
        i = table.addRow()
        table.setText(i, 0, u'Биоимпедансметр для анализа внутренних сред организма (% соотношение воды,мышечной и жировой ткани)')
        table.setText(i, 1, u'05')
        i = table.addRow()
        table.setText(i, 0, u'Экспресс-анализатор для определения общего холестерина и глюкозы в крови (с принадлежностями)')
        table.setText(i, 1, u'06')
        i = table.addRow()
        table.setText(i, 0, u'Оборудование для определения токсических веществ в биологических средах организма')
        table.setText(i, 1, u'07')

        i = table.addRow()
        table.setText(i, 0, u'Анализатор окиси углерода выдыхаемого воздуха с определением карбоксигемоглобина')
        table.setText(i, 1, u'08')
        i = table.addRow()
        table.setText(i, 0, u'Анализатор котинина и других биологических маркеров в крови и моче')
        table.setText(i, 1, u'09')
        i = table.addRow()
        table.setText(i, 0, u'Смокелайзер')
        table.setText(i, 1, u'10')
        i = table.addRow()
        table.setText(i, 0, u'Кардиотренажер')
        table.setText(i, 1, u'11')
        i = table.addRow()
        table.setText(i, 0, u'Пульсоксиметр (оксиметр пульсовой)')
        table.setText(i, 1, u'12')
        i = table.addRow()
        table.setText(i, 0, u'Рабочее место гигиениста стоматологического, в состав которого входит: установка стоматологическая, компрессор, пылесос, слюноотсос, пескоструйный аппарат, комплект мебели')
        table.setText(i, 1, u'13')
        i = table.addRow()
        table.setText(i, 0, u'Рабочее место среднего медицинского персонала офтальмологического кабинета, в состав которого входит набор пробных очковых линз и призм с пробной оправой, проектор знаков, автоматический рефрактометр, автоматический пневмотонометр')
        table.setText(i, 1, u'14')

    def getTable1302(self, cursor):

        tableColumns = [('70%', [u'Наименование оборудования', u'1'], CReportBase.AlignLeft),
                ('4%', [u'№ строки',   u'2'], CReportBase.AlignRight),
                ('13%', [u'Количество единиц', u'3'], CReportBase.AlignRight),
                ('13%', [u'Количество введённого в эксплуатацию', u'4'], CReportBase.AlignRight),
                ]


        table = createTable(cursor, tableColumns)

        i = table.addRow()
        table.setText(i, 0, u'АПК для скрин-оцен.уровня психфиз.и сомат.здоровья,функц.и адапт.резервов орг-ма с компл.оборуд.для измер.парам.физ.развития')
        table.setText(i, 1, u'01')
        i = table.addRow()
        table.setText(i, 0, u'Аппарат для комплексной детальной оценки функций дыхательной системы (спирометр компьютеризированный)')
        table.setText(i, 1, u'02')
        i = table.addRow()
        table.setText(i, 0, u'Биоимпедансметр для анализа внутренних сред организма (процентное соотношение воды, мышечной и жировой ткани)')
        table.setText(i, 1, u'03')
        i = table.addRow()
        table.setText(i, 0, u'Экспресс-анализатор для определения общего холестерина и глюкозы в крови (с принадлежностями)')
        table.setText(i, 1, u'04')
        i = table.addRow()
        table.setText(i, 0, u'Анализатор для определения токсических веществ в биологических средах организма')
        table.setText(i, 1, u'05')
        i = table.addRow()
        table.setText(i, 0, u'Анализатор котинина и других биологических маркеров в моче')
        table.setText(i, 1, u'06')
        i = table.addRow()
        table.setText(i, 0, u'Анализатор окиси углерода выдыхаемого воздуха с определением корбоксигемоглобина')
        table.setText(i, 1, u'07')

        i = table.addRow()
        table.setText(i, 0, u'Пульсоксиметр (оксиметр пульсовой)')
        table.setText(i, 1, u'08')
        i = table.addRow()
        table.setText(i, 0, u'Рабочее место гигиениста стоматологического, в состав которого входит установка стоматологическая универсальная с ультразвуковым сканером')
        table.setText(i, 1, u'09')
        i = table.addRow()
        table.setText(i, 0, u'Весы медицинские для взвешивания грудных детей')
        table.setText(i, 1, u'10')
        i = table.addRow()
        table.setText(i, 0, u'Комплект оборудования для наглядной пропаганды здорового образа жизни')
        table.setText(i, 1, u'11')
        i = table.addRow()
        table.setText(i, 0, u'Комплект оборудования для зала лечебной физической культуры')
        table.setText(i, 1, u'12')
        i = table.addRow()
        table.setText(i, 0, u'Рабочее место среднего медицинского персонала офтальмологического кабинета, в состав которого входит набор пробных очковых линз и призм с пробной оправой, проектор знаков, автоматический рефрактометр, автоматический пневмотонометр')
        table.setText(i, 1, u'13')


    def getTable2001(self, params, cursor, regionCode):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        query = selectData2001(begDate, endDate, regionCode)
        total = 0
        tableColumns = [('25%', [u'Наименование показателя', u'', u'1'], CReportBase.AlignLeft),
                ('5%', [u'№ строки', u'',  u'2'], CReportBase.AlignRight),
                ('10%', [u'Всего', u'', u'3'], CReportBase.AlignRight),
                ('10%', [u'Из них первично', u'',  u'4'], CReportBase.AlignRight),
                ('10%', [[u'Из них выявлено:', True], u'здоровые', u'5'], CReportBase.AlignRight),
                ('10%', [u'', u'с факторами риска', u'6'],CReportBase.AlignRight),
                ('10%', [u'назначены индивидуальные планы по здоровому образу жизни',u'', '7'], CReportBase.AlignCenter),
                ('10%', [[u'Направлено первично:', True], u'к врачам специалистам АПУ*', u'8'], CReportBase.AlignRight),
                ('10%', [u'', u'в стационар', u'9'],CReportBase.AlignRight),
                ]


        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 2, 1)
        table.mergeCells(0, 4, 1, 2)
        table.mergeCells(0, 6, 2, 1)
        table.mergeCells(0, 7, 1, 2)

        i = table.addRow()
        table.setText(i, 0, u'обратившиеся в Центр здоровья - всего')
        table.setText(i, 1, u'01')
        i = table.addRow()
        table.setText(i, 0, u'в том числе: самостоятельно')
        table.setText(i, 1, u'02')
        i = table.addRow()
        table.setText(i, 0, u'направленные ЛПУ по месту прикрепления')
        table.setText(i, 1, u'03')
        i = table.addRow()
        table.setText(i, 0, u'направленные из стационаров после острого заболевания')
        table.setText(i, 1, u'04')
        i = table.addRow()
        table.setText(i, 0, u'направленные врачом, ответственным за проведение дополнительной диспансеризации работающих граждан с I (практически здоров) и II (риск развития заболеваний)  группами состояния здоровья')
        table.setText(i, 1, u'05')
        i = table.addRow()
        table.setText(i, 0, u'направленные работодателем по заключению врача, ответственного за проведение периодических медицинских осмотров')
        table.setText(i, 1, u'06')
        i=3
        while query.next():
            record = query.record()
            if i == 3:
                total = forceInt(record.value('Total'))
            table.setText(i, 2, forceInt(record.value('Total')))
            table.setText(i, 3, forceInt(record.value('FirstTime')))
            table.setText(i, 4, forceInt(record.value('Zdorov')))
            table.setText(i, 5, forceInt(record.value('Risk')))
            table.setText(i, 6, forceInt(record.value('IndPlan')))
            i=i+1
        return total

    def getTable2003(self, params, cursor):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        query = selectData2003(begDate, endDate)
        tableColumns = [('50%', [u'Наименование показателя', u'', u'1'], CReportBase.AlignLeft),
                ('10%', [u'№ строки', u'',  u'2'], CReportBase.AlignCenter),
                ('20%', [u'Возраст', u'0-14 лет',  u'3'], CReportBase.AlignCenter),
                ('20%', [u'', u'15-17 лет', u'4'], CReportBase.AlignCenter),
                ]


        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 1, 2)

        query.next()
        record = query.record()

        i = table.addRow()
        table.setText(i, 0, u'Всего обследовано детей')
        table.setText(i, 1, u'01')
        table.setText(i, 2, forceInt(record.value('Total14')))
        table.setText(i, 3, forceInt(record.value('Total17')))
        i = table.addRow()
        table.setText(i, 0, u'из них: здоровые')
        table.setText(i, 1, u'02')
        table.setText(i, 2, forceInt(record.value('Zdorov14')))
        table.setText(i, 3, forceInt(record.value('Zdorov17')))
        i = table.addRow()
        table.setText(i, 0, u'с факторами риска')
        table.setText(i, 1, u'03')
        table.setText(i, 2, forceInt(record.value('Risk14')))
        table.setText(i, 3, forceInt(record.value('Risk17')))
        i = table.addRow()
        table.setText(i, 0, u'назначены индивидуальные планы по здоровому образу жизни')
        table.setText(i, 1, u'04')
        table.setText(i, 2, forceInt(record.value('IndPlan14')))
        table.setText(i, 3, forceInt(record.value('IndPlan17')))
        i = table.addRow()
        table.setText(i, 0, u'направлены (из строки 01)')
        table.setText(i, 1, u'05')
        table.setText(i, 2, 0)
        table.setText(i, 3, 0)
        i = table.addRow()
        table.setText(i, 0, u'в амбулаторно-поликлинические учреждения')
        table.setText(i, 1, u'06')
        table.setText(i, 2, 0)
        table.setText(i, 3, 0)
        i = table.addRow()
        table.setText(i, 0, u'в стационар')
        table.setText(i, 1, u'07')
        table.setText(i, 2, 0)
        table.setText(i, 3, 0)

    def getTable2005(self, params, cursor5):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        query = selectData2005(begDate, endDate)
        tableColumns = [('15%', [u'Осмотрено врачами-специалистами', u'', u'', u''], CReportBase.AlignLeft),
                ('5%', [u'№ строки',  u'', u'', u''], CReportBase.AlignCenter),
                ('5%', [u'Из числа граждан, осмотренных врачами-специалистами', u'здоровые',u'всего', u''], CReportBase.AlignCenter),
                ('5%', [u'',u'', u'в т.ч.детей 0-17 лет', u''],CReportBase.AlignCenter),
                ('5%', [u'',u'',u'из них', u'0-14 лет'], CReportBase.AlignCenter),
                ('5%', [u'', u'',u'',u'15-17 лет'],CReportBase.AlignRight),
                ('5%', [u'', u'с факторами риска',u'всего', u''], CReportBase.AlignCenter),
                ('5%', [u'',u'', u'в т.ч.детей 0-17 лет', u''],CReportBase.AlignCenter),
                ('5%', [u'',u'',u'из них', u'0-14 лет'], CReportBase.AlignCenter),
                ('5%', [u'', u'',u'',u'15-17 лет'],CReportBase.AlignRight),
                ('5%', [u'', u'направлены к врачам-специалистам АПУ',u'всего', u''], CReportBase.AlignCenter),
                ('5%', [u'',u'', u'в т.ч.детей 0-17 лет', u''],CReportBase.AlignCenter),
                ('5%', [u'',u'',u'из них', u'0-14 лет'], CReportBase.AlignCenter),
                ('5%', [u'', u'',u'',u'15-17 лет'],CReportBase.AlignRight),
                ('5%', [u'', u'направлены в стационар',u'всего', u''], CReportBase.AlignCenter),
                ('5%', [u'',u'', u'в т.ч.детей 0-17 лет', u''],CReportBase.AlignCenter),
                ('5%', [u'',u'',u'из них', u'0-14 лет'], CReportBase.AlignCenter),
                ('5%', [u'', u'',u'',u'15-17 лет'],CReportBase.AlignCenter),
                ]


        table = createTable(cursor5, tableColumns)
        table.mergeCells(0, 0, 4, 1)
        table.mergeCells(0, 1, 4, 1)
        table.mergeCells(0, 2, 1, 16)

        table.mergeCells(1, 2, 1, 4)
        table.mergeCells(2, 2, 2, 1)
        table.mergeCells(2, 3, 2, 1)
        table.mergeCells(2, 4, 1, 2)

        table.mergeCells(1, 6, 1, 4)
        table.mergeCells(2, 6, 2, 1)
        table.mergeCells(2, 7, 2, 1)
        table.mergeCells(2, 8, 1, 2)

        table.mergeCells(1, 10, 1, 4)
        table.mergeCells(2, 10, 2, 1)
        table.mergeCells(2, 11, 2, 1)
        table.mergeCells(2, 12, 1, 2)

        table.mergeCells(1, 14, 1, 4)
        table.mergeCells(2, 14, 2, 1)
        table.mergeCells(2, 15, 2, 1)
        table.mergeCells(2, 16, 1, 2)

        itogo =[0,0,0,0,0,0,0,0]
        i=0

        while query.next():
            record = query.record()
            i = table.addRow()
            table.setText(i, 0, forceString(record.value('name')))
            table.setText(i, 1, (str(i-3) if (i-3)>9 else '0'+str(i-3)))
            table.setText(i, 2, forceInt(record.value('zdorovTotal')))
            itogo[0] = itogo[0] + forceInt(record.value('zdorovTotal'))
            table.setText(i, 3, forceInt(record.value('zdorovDeti')))
            itogo[1] = itogo[1] + forceInt(record.value('zdorovDeti'))
            table.setText(i, 4, forceInt(record.value('zdorov14')))
            itogo[2] = itogo[2] + forceInt(record.value('zdorov14'))
            table.setText(i, 5, forceInt(record.value('zdorov17')))
            itogo[3] = itogo[3] + forceInt(record.value('zdorov17'))
            table.setText(i, 6, forceInt(record.value('riskTotal')))
            itogo[4] = itogo[4] + forceInt(record.value('riskTotal'))
            table.setText(i, 7, forceInt(record.value('riskDeti')))
            itogo[5] = itogo[5] + forceInt(record.value('riskDeti'))
            table.setText(i, 8, forceInt(record.value('risk14')))
            itogo[6] = itogo[6] + forceInt(record.value('risk14'))
            table.setText(i, 9, forceInt(record.value('risk17')))
            itogo[7] = itogo[7] + forceInt(record.value('risk17'))
            i=i+1

        i = table.addRow()
        table.setText(i, 0, u'Всего:')
        table.setText(i, 1, ((str(i-3) if (i-3)>9 else '0'+str(i-3))))
        for p in range(0, 8):
            table.setText(i, p+2, itogo[p])

    def getTable2006(self, params, cursor5):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        query = selectData2006(begDate, endDate)
        tableColumns = [('43%', [u'Наименование оборудования', u''], CReportBase.AlignLeft),
                ('3%', [u'№ строки',  u''], CReportBase.AlignCenter),
                ('9%', [u'Число обследованных лиц', u'всего'], CReportBase.AlignCenter),
                ('9%', [u'', u'в т.ч.детей 0-17 лет'],CReportBase.AlignCenter),
                ('9%', [u'Количество проведённых обследований (первичных и повторных)', u'всего'], CReportBase.AlignCenter),
                ('9%', [u'', u'в т.ч.детей 0-17 лет'],CReportBase.AlignCenter),
                ('9%', [u'Выявлено лиц с факторами риска',u'всего'], CReportBase.AlignCenter),
                ('9%', [u'', u'в т.ч.детей 0-17 лет'],CReportBase.AlignCenter),
                ]


        table = createTable(cursor5, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 1, 2)
        table.mergeCells(0, 4, 1, 2)
        table.mergeCells(0, 6, 1, 2)

        i = table.addRow()
        table.setText(i, 0, u'Аппаратно-программный комплекс для скрининг-оценки уровня психофизиологического и соматического здоровья, функциональных и адаптивных резервов организма с комплектом оборудования для измерения параметров физического развития, в состав которого входит')
        table.setText(i, 1, '01')
        i = table.addRow()
        table.setText(i, 0, u'Система скрининга сердца компьютеризированная (экспресс-оценка состояния сердца по ЭКГ-сигналам от конечностей)')
        table.setText(i, 1, '02')
        i = table.addRow()
        table.setText(i, 0, u'Система ангиологического скрининга с автоматическим измерением систолического артериального давления и расчёта плечелодыжечного индекса')
        table.setText(i, 1, '03')
        i = table.addRow()
        table.setText(i, 0, u'Аппарат для комплексной детальной оценки функций дыхательной системы (спирометр компьютеризированный)')
        table.setText(i, 1, '04')
        i = table.addRow()
        table.setText(i, 0, u'Биоимпедансметр для анализа внутренних сред организма (процентное соотношение воды, мышечной и жировой ткани)')
        table.setText(i, 1, '05')
        i = table.addRow()
        table.setText(i, 0, u'Экспресс-анализатор для определения общего холестерина и глюкозы в крови (с принадлежностями)')
        table.setText(i, 1, '08')
        i = table.addRow()
        table.setText(i, 0, u'Оборудование для определения токсических веществ в биологических средах организма')
        table.setText(i, 1, '07')
        i = table.addRow()
        table.setText(i, 0, u'Анализатор окиси углерода выдыхаемого воздуха с определением карбоксигемоглобина')
        table.setText(i, 1, '08')
        i = table.addRow()
        table.setText(i, 0, u'Анализатор котинина и других биологических маркеров в крови и моче')
        table.setText(i, 1, '09')
        i = table.addRow()
        table.setText(i, 0, u'Смокелайзер')
        table.setText(i, 1, '10')
        i = table.addRow()
        table.setText(i, 0, u'Кардиотренажёр')
        table.setText(i, 1, '11')
        i = table.addRow()
        table.setText(i, 0, u'Пульсоксиметр (оксиметр пульсовой)')
        table.setText(i, 1, '12')
        i = table.addRow()
        table.setText(i, 0, u'Рабочее место гигиениста стоматологического, в состав которого входит: установка стоматологическая, компрессор, пылесос, слюноотсос, пескоструйный аппарат, комплект мебели')
        table.setText(i, 1, '13')
        i = table.addRow()
        table.setText(i, 0, u'Рабочее место среднего медицинского персонала офтальмологического кабинета, в состав которого входит набор пробных очковых линз и призм с пробной оправой, проектор знаков, автоматический рефрактометр, автоматический пневмотонометр')
        table.setText(i, 1, '14')

        itogo =[0,0,0,0,0,0,0,0]
        i=2
        while query.next():
            if i == 12:
                table.setText(i, 1, '11')
                i=i+1
            record = query.record()
            table.setText(i, 1, forceString(record.value('typeId')))
            table.setText(i, 2, forceInt(record.value('clientTotal')))
            itogo[0] = itogo[0] + forceInt(record.value('clientTotal'))
            table.setText(i, 3, forceInt(record.value('clientDeti')))
            itogo[1] = itogo[1] + forceInt(record.value('clientDeti'))
            table.setText(i, 4, forceInt(record.value('eventTotal')))
            itogo[2] = itogo[2] + forceInt(record.value('eventTotal'))
            table.setText(i, 5, forceInt(record.value('eventDeti')))
            itogo[3] = itogo[3] + forceInt(record.value('eventDeti'))
            table.setText(i, 6, forceInt(record.value('riskTotal')))
            itogo[4] = itogo[4] + forceInt(record.value('riskTotal'))
            table.setText(i, 7, forceInt(record.value('riskDeti')))
            itogo[5] = itogo[5] + forceInt(record.value('riskDeti'))
            i=i+1
        #
        # i = table.addRow()
        # table.setText(i, 0, u'Всего:')
        # table.setText(i, 1, ((str(i) if i>9 else '0'+str(i))))
        # for p in range(0, 8):
        #     table.setText(i, p+2, itogo[p])

    def getTable2008(self, params, cursor5):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        query = selectData2008(begDate, endDate)
        tableColumns = [('70%', u'', CReportBase.AlignLeft),
                ('5%', u'№ строки', CReportBase.AlignCenter),
                ('25%', u'Всего', CReportBase.AlignCenter),
                ]


        table = createTable(cursor5, tableColumns)
        query.next()
        record = query.record()

        i = table.addRow()
        table.setText(i, 0, u'Число лиц, закончивших лечение, - всего:')
        table.setText(i, 1, ((str(i) if i>9 else '0'+str(i))))
        table.setText(i, 2, forceInt(record.value('total')))

        i = table.addRow()
        table.setText(i, 0, u'из них дети 0 - 17 лет включительно')
        table.setText(i, 1, ((str(i) if i>9 else '0'+str(i))))
        table.setText(i, 2, forceInt(record.value('totalDeti')))

        i = table.addRow()
        table.setText(i, 0, u' Число отпущенных процедур - всего')
        table.setText(i, 1, ((str(i) if i>9 else '0'+str(i))))
        table.setText(i, 2, forceInt(record.value('procedura')))

    def getTable2009(self, params, cursor5):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        query = selectData2009(begDate, endDate)
        tableColumns = [('50%', u'', CReportBase.AlignLeft),
                ('5%', u'№ строки', CReportBase.AlignCenter),
                ('25%', u'Всего', CReportBase.AlignCenter),
                ('25%', u'из них детей (0 - 17 лет включительно)', CReportBase.AlignCenter)
                ]


        table = createTable(cursor5, tableColumns)
        query.next()
        record = query.record()

        i = table.addRow()
        table.setText(i, 0, u'Число лиц, обученных основам здорового образа жизни, - всего:')
        table.setText(i, 1, ((str(i) if i>9 else '0'+str(i))))
        table.setText(i, 2, forceInt(record.value('total')))
        table.setText(i, 3, forceInt(record.value('totalDeti')))

        i = table.addRow()
        table.setText(i, 0, u'Число лиц, обученных в школах здоровья - всего,в том числе :')
        table.setText(i, 1, ((str(i) if i>9 else '0'+str(i))))
        table.setText(i, 2, forceInt(record.value('school')))
        table.setText(i, 3, forceInt(record.value('schoolDeti')))

        i = table.addRow()
        table.setText(i, 0, u' школе профилактики артериальной гипертензии')
        table.setText(i, 1, ((str(i) if i>9 else '0'+str(i))))
        table.setText(i, 2, forceInt(record.value('school3')))
        table.setText(i, 3, forceInt(record.value('schoolDeti3')))

        i = table.addRow()
        table.setText(i, 0, u' школе профилактики заболеваний костно-мышечной системы')
        table.setText(i, 1, ((str(i) if i>9 else '0'+str(i))))
        table.setText(i, 2, forceInt(record.value('school4')))
        table.setText(i, 3, forceInt(record.value('schoolDeti4')))

        i = table.addRow()
        table.setText(i, 0, u'   школе профилактики бронхиальной астмы')
        table.setText(i, 1, ((str(i) if i>9 else '0'+str(i))))
        table.setText(i, 2, forceInt(record.value('school5')))
        table.setText(i, 3, forceInt(record.value('schoolDeti5')))

        i = table.addRow()
        table.setText(i, 0, u'   школе профилактики сахарного диабета')
        table.setText(i, 1, ((str(i) if i>9 else '0'+str(i))))
        table.setText(i, 2, forceInt(record.value('school6')))
        table.setText(i, 3, forceInt(record.value('schoolDeti6')))

        i = table.addRow()
        table.setText(i, 0, u'   прочих школах')
        table.setText(i, 1, ((str(i) if i>9 else '0'+str(i))))
        table.setText(i, 2, forceInt(record.value('school7')))
        table.setText(i, 3, forceInt(record.value('schoolDeti7')))

    def build(self, params):
        monthList = [u'Январь', u'Февраль', u'Март', u'Апрель', u'Май', u'Июнь', u'Июль', u'Август', u'Сентябрь',
                     u'Октябрь', u'Ноябрь', u'Декабрь']
        begDate = params.get('begDate', QDate.currentDate())
        endDate = params.get('endDate', QDate.currentDate())

        orgId = QtGui.qApp.currentOrgId()
        orgName = u''
        address = u''
        if orgId:
            record = QtGui.qApp.db.getRecordEx('Organisation', 'fullName, Address', 'id=%s AND deleted = 0'%(str(orgId)))
            if record:
                orgName = forceString(record.value('fullName'))
                address = forceString(record.value('Address'))


        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        # cursor.setCharFormat(CReportBase.ReportTitle)
        # cursor.insertText(self.name)
        # cursor.insertBlock()
        # self.dumpParams(cursor, params)
        cursor.insertBlock()

        columns = [('70%', [], CReportBase.AlignLeft),('30%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=4, border=0, cellPadding=2, cellSpacing=0)

        table.setText(0, 1, u'Приложение № 4')
        table.setText(1, 1, u'к приказу Министерства')
        table.setText(2, 1, u'здравоохранения и социального развития Российской Федерации')
        table.setText(3, 1, u'от 19 августа 2009 г. № 597н')

        cursor.movePosition(QtGui.QTextCursor.End)

        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)

        cursor.insertBlock()
        columns2 = [('100%', [], CReportBase.AlignCenter)]
        table2 = createTable(cursor, columns2, headerRowCount=2, border=1, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'Отраслевое статистическое наблюдение', charFormat=boldChars)
        table2.setText(1, 0, u'Конфиденциальность гарантируется получателем информации', charFormat=boldChars)
        cursor.movePosition(QtGui.QTextCursor.End)

        cursor.insertBlock()
        table2 = createTable(cursor, columns2, headerRowCount=1, border=1, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'Сведения о деятельности центра здоровья за %s'%(str(begDate.year())+u' год' if begDate.month() == 1 and endDate.month() == 12 else monthList[endDate.month() - 1]+' '+str(begDate.year())+u' года'), charFormat=CReport.ReportTitle)
        cursor.movePosition(QtGui.QTextCursor.End)

        cursor.insertBlock()
        columnsB = [('80%', [], CReportBase.AlignLeft),('20%', [], CReportBase.AlignCenter)]
        tableB = createTable(cursor, columnsB, headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)
        cursorB = tableB.cellAt(0, 0).firstCursorPosition()

        columns2 = [('80%', [], CReportBase.AlignLeft),('20%', [], CReportBase.AlignLeft)]
        table2 = createTable(cursorB, columns2, headerRowCount=2, border=1, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'Представляют:')
        table2.setText(0, 1, u'Сроки представления')
        table2.setText(1, 0, u'Государственные учреждения здравоохранения субъектов Российской Федерации и учреждения здравоохранения муниципальных образований (амбулаторно-поликлинические,стационарно-поликлинические, врачебно-физкультурные диспансеры, Центры медицинской профилактики и др.), имеющие в своём составе центр здоровья:- органам исполнительной власти субъектов Российской Федерации Органы исполнительной власти субъекта Российской Федерации;- Министерству здравоохранения и социального развития Российской Федерации')

        columns3 = [('100%', [], CReportBase.AlignLeft)]
        cursor1 = table2.cellAt(1, 1).firstCursorPosition()

        table3 = createTable(cursor1, columns3, headerRowCount=3, border=0, cellPadding=2, cellSpacing=0)
        table3.setText(0, 0, u'10 числа следующего за отчётным периодом месяца')
        table3.setText(2, 0, u' 20 числа следующего за отчётным периодом месяца')

        cursorB = tableB.cellAt(0, 1).firstCursorPosition()
        table4 = createTable(cursorB, columns3, headerRowCount=3, border=0, cellPadding=2, cellSpacing=0)
        cursor1 = table4.cellAt(0, 0).firstCursorPosition()
        table5 =  createTable(cursor1, columns3, headerRowCount=1, border=1, cellPadding=2, cellSpacing=0)
        table5.setText(0,0,u'Отчётная форма', charFormat=boldChars)
        cursor1 = table4.cellAt(1, 0).firstCursorPosition()
        table5 =  createTable(cursor1, columns3, headerRowCount=1, border=1, cellPadding=2, cellSpacing=0)
        table5.setText(0,0,u'Форма № 68', charFormat=boldChars)
        cursor1 = table4.cellAt(2, 0).firstCursorPosition()
        table5 =  createTable(cursor1, columns3, headerRowCount=3, border=0, cellPadding=2, cellSpacing=0)
        table5.setText(0,0,u'Утверждена приказом Минздравсоцразвития России от 19 августа 2009 г.№ 597н')
        table5.setText(1,0,u'(ежемесячная, годовая)')


        cursor.movePosition(QtGui.QTextCursor.End)

        cursor.insertBlock()
        columnsB = [('100%', [], CReportBase.AlignLeft)]
        tableB = createTable(cursor, columnsB, headerRowCount=1, border=2, cellPadding=2, cellSpacing=0)
        cursorB = tableB.cellAt(0, 0).firstCursorPosition()
        table3 = createTable(cursorB, columns3, headerRowCount=3, border=0, cellPadding=2, cellSpacing=0)
        table3.setText(0, 0, u'Наименование отчитывающейся организации %s'%orgName)
        table3.setText(1, 0, u'Почтовый адрес: %s'%address)
        table3.setText(2, 0, u'Выход в интернет')

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        columns2 = [('100%', [], CReportBase.AlignCenter)]
        table2 = createTable(cursor, columns2, headerRowCount=2, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'1.     Общие сведения', charFormat=boldChars)
        table2.setText(1, 0, u'1.1. Структура центра здоровья', charFormat=boldChars)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'(1001)')
        cursor.insertBlock()
        self.getTable1001(cursor)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'* Указать наименования школ здоровья.')
        cursor.insertBlock()
        cursor.insertText(u'** Указать наименования кабинетов.')
        cursor.insertBlock()

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        columns2 = [('100%', [], CReportBase.AlignCenter)]
        table2 = createTable(cursor, columns2, headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'1.2. Штаты центра здоровья на конец отчётного года', charFormat=boldChars)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'(1200)')
        self.getTable1200(cursor)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'_____________________________________________________________________________')
        cursor.insertBlock()
        cursor.insertText(u'* Указываются квалификационные категории основных работников центра здоровья.')

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        columns2 = [('100%', [], CReportBase.AlignCenter)]
        table2 = createTable(cursor, columns2, headerRowCount=2, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'1.3       Оборудование', charFormat=boldChars)
        table2.setText(1, 0, u'1.3.1. Центр здоровья для взрослого населения', charFormat=boldChars)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'(1300)')
        self.getTable1300(cursor)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        columns2 = [('100%', [], CReportBase.AlignCenter)]
        table2 = createTable(cursor, columns2, headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'1.3.2. Центр здоровья для детей', charFormat=boldChars)
        cursor.movePosition(QtGui.QTextCursor.End)
        self.getTable1302(cursor)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        columns2 = [('100%', [], CReportBase.AlignCenter)]
        table2 = createTable(cursor, columns2, headerRowCount=3, border=0, cellPadding=2, cellSpacing=0)
        # table2.mergeCells(0, 0, 1, 1)
        # table2.mergeCells(1, 0, 1, 1)
        table2.setText(0, 0, u'2. Деятельность центра здоровья', charFormat=boldChars)
        table2.setText(1, 0, u'2.1. Контингенты обратившихся граждан', charFormat=boldChars)
        table2.setText(2, 0, u'Взрослые (18 лет и старше)', charFormat=boldChars)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'(2001)')
        cursor.insertBlock()

        totalAdult = self.getTable2001(params, cursor, '01')
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'_____________________________________________________________________________')
        cursor.insertBlock()
        cursor.insertText(u'* Амбулаторно-поликлинические учреждения.')


        cursor.movePosition(QtGui.QTextCursor.End)
        table2 = createTable(cursor, columns2, headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'дети (0 - 17 лет включительно), обратившиеся в центр здоровья', charFormat=boldChars)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'(2002)')
        cursor.insertBlock()

        totalChild = self.getTable2001(params, cursor, '02')
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'_____________________________________________________________________________')
        cursor.insertBlock()
        cursor.insertText(u'* Амбулаторно-поликлинические учреждения.')

        cursor.movePosition(QtGui.QTextCursor.End)
        table2 = createTable(cursor, columns2, headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'дети (0 - 17 лет включительно), обследованные в центре здоровья', charFormat=boldChars)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'(2003)')
        cursor.insertBlock()

        self.getTable2003(params, cursor)

        cursor.movePosition(QtGui.QTextCursor.End)
        table2 = createTable(cursor, columns2, headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'2.2. Посещения центра здоровья', charFormat=boldChars)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'(2004)      Всего посещений  %d, из них дети (0-17 лет включительно) %d.'%(totalAdult+totalChild, totalChild))
        cursor.insertBlock()


        cursor.movePosition(QtGui.QTextCursor.End)
        table2 = createTable(cursor, columns2, headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'2.3. Осмотрено врачами-специалистами', charFormat=boldChars)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'(2005)')
        cursor.insertBlock()

        self.getTable2005(params, cursor)

        cursor.movePosition(QtGui.QTextCursor.End)
        table2 = createTable(cursor, columns2, headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'2.4. Обследовано в кабинете тестирования', charFormat=boldChars)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'(2006)')
        cursor.insertBlock()

        self.getTable2006(params, cursor)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'(2007)     Число комплексных обследований, всего       %d, из них дети (0-17 лет включительно)        %d.'%(totalAdult+totalChild, totalChild))
        cursor.insertBlock()

        cursor.movePosition(QtGui.QTextCursor.End)
        table2 = createTable(cursor, columns2, headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'2.5. Деятельность кабинета лечебной физкультуры', charFormat=boldChars)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        columns = [('10%', [], CReportBase.AlignLeft),('90%', [], CReportBase.AlignRight)]
        table3 = createTable(cursor, columns, headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)
        table3.setText(0, 0, u'(2008)')
        table3.setText(0, 1, u' Коды по ОКЕИ: человек - 792, единица - 642')
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        self.getTable2008(params, cursor)

        cursor.movePosition(QtGui.QTextCursor.End)
        table2 = createTable(cursor, columns2, headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'2.6. Школы здоровья', charFormat=boldChars)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(u'(2009)')
        cursor.insertBlock()
        self.getTable2009(params, cursor)
        cursor.movePosition(QtGui.QTextCursor.End)

        cursor.insertBlock()
        cursor.insertText(u'Дата составления документа %s'% QDate.currentDate().toString('dd.MM.yyyy'))
        columns2 = [('30%', [], CReportBase.AlignLeft),('50%', [], CReportBase.AlignLeft),('20%', [], CReportBase.AlignCenter)]
        table2 = createTable(cursor, columns2, headerRowCount=4, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0,0,u'Должность руководителя организации')
        table2.setText(0,1,u'____________________________________')
        table2.setText(0,2,u'_____________________')
        table2.setText(1,1,u'(Ф.И.О.)')
        table2.setText(1,2,u'(подпись)')
        table2.setText(2,0,u'Должность лица, ответственного за составление формы')
        table2.setText(2,1,u'____________________________________')
        table2.setText(2,2,u'_____________________')
        table2.setText(3,1,u'(Ф.И.О.)')
        table2.setText(3,2,u'(подпись)')

        return doc
