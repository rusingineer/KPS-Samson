# -*- coding: utf-8 -*-
# from datetime import date

from datetime import date
from PyQt4 import QtGui
from PyQt4.QtCore import QDate
from PyQt4.QtGui import QTextCharFormat

from Reports.HealthCenterForm68 import CHealthCenterForm68SetupDialog
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable, forceString
from library.Utils import forceDate, forceInt
def selectData(begDate, endDate ):

    db = QtGui.qApp.db
    stmt = u""" DROP TEMPORARY TABLE IF EXISTS CHealthCenterAnaliz_FirstResultData"""
    db.query(stmt)
    stmt = u""" DROP TEMPORARY TABLE IF EXISTS CHealthCenterAnaliz_SecondResultData"""
    db.query(stmt)

    tableEvent  = db.table('Event').alias('e')
    cond = []
    cond.append(tableEvent['execDate'].ge(begDate))
    cond.append(db.joinOr([tableEvent['execDate'].lt(endDate.addDays(1)), tableEvent['execDate'].isNull()]))

    stmt = u""" CREATE TEMPORARY TABLE if not exists CHealthCenterAnaliz_FirstResultData AS
select  e.id, c.sex, age(c.birthDate, e.execDate) as clientAge,
act.*
from Event e 
left join Client c on c.id = e.client_id
left join EventType et on et.id = e.eventType_id
left join rbMedicalAidType mt on et.medicalAidType_id = mt.id
inner JOIN
(select a.event_id,
 max(case when at.flatCode = 'app_san' and at.code = '1-04-03' and
  apt.name = 'Вид обращения'  then case aps.value when 'Обратился самостоятельно'  then 1 
                                                       when 'Направлен амбулаторно-поликлиническим учреждением' then 2
                                                       when 'Направлен после лечения в стационаре' then 3
                                                       when 'Направлен после дополнительной диспансеризации' then 4
                                                       when 'Направлен работодателем после прохождения ПМО и УМО' then 5 
                                                       else 0 end else 0 end )as vidObr,

 max(case when at.flatCode = 'app_san' and at.code = '1-04-03' and
  apt.name ='Социальный статус' then case aps.value when 'служащий'then 7 
                                                      when 'рабочий'then 8
                                                      when 'учащийся' then 9
                                                      when 'не работающий' then 10
                                                      else 0 end else 0 end )as socStatus,
 max(case when at.flatCode = 'app_san' and at.code = '1-04-03' and
  apt.name ='Образование' then case aps.value when 'высшее'then 12 
                                                      when 'среднее'then 13
                                                      when 'начальное' then 14
                                                      when 'не имеет' then 15
                                                      else 0 end else 0 end )as vidObraz,
 max(case when at.flatCode = 'app_san' and at.code = '1-04-03' and
  apt.name = 'Житель' then case aps.value when 'городской' then 17 
                                                      when 'сельский' then 18
                                                      else 0 end else 0 end )as jitel,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Употребление алкоголя'   then case aps.value when 'случайное' then 20
                                                       when 'мало' then 21
                                                       when 'много' then 22
                                                       when 'часто' then 23 
                                                       when 'не употребляет'  then 24 
                                                       else 0 end else 0 end )as useAlc,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Тип алкоголя' then case aps.value when 'крепкие алкогольные напитки'then 26 
                                                      when 'слабоалкогольные напитки'then 27
                                                      else 0 end else 0 end )as typeAlc,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Табакокурение' then case aps.value when 'не курит'then 29 
                                                      when 'курит' then 30
                                                      else 0 end else 0 end )as typeSmoke,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'С какого возраста'  then case aps.value when '0-9 лет' then 32
                                                       when '10-14 лет' then 33
                                                       when '15-19 лет' then 34
                                                       when '20-39 лет' then 35 
                                                       when '40 лет и старше'  then 36 
                                                       else 0 end else 0 end )as ageSmoke,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Количество штук в день' then case aps.value when '1-4 шт.' then 38
                                                       when '5-9 шт.' then 39
                                                       when '10-20 шт.' then 40
                                                       when '21 и более' then 41 
                                                       else 0 end else 0 end )as countSmoke,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Режим питания' then case aps.value when 'регулярный'then 43 
                                                      when 'нерегулярный ' then 44
                                                      else 0 end else 0 end )as rejim,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Преобладание компонентов продуктов питания'  then case aps.value when 'белки' then 46
                                                       when 'жиры' then 47
                                                       when 'углеводы' then 48
                                                       else 0 end else 0 end )as komponent,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Калорийность рациона'  then case aps.value when 'высокая' then 50
                                                       when 'низкая' then 51
                                                       else 0 end else 0 end )as kaloria,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Сон' then case aps.value when '7-9 часов'then 53 
                                                      when 'менее 7 часов' then 54
                                                      when 'более 9 часов' then 55
                                                      else 0 end else 0 end )as dream,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Занятия физкультурой и спортом' then case aps.value when 'систематические' then 57
                                                       when 'случайные' then 58
                                                       when 'не занимается' then 59
                                                       else 0 end else 0 end )as fizra,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Физкультура'  then case aps.value when 'утренняя гимнастика' then 61
                                                       when 'бег' then 62
                                                       when 'ходьба на лыжах' then 63
                                                       when 'езда на велосипеде' then 64
                                                       when 'оздоровительное плавание' then 65
                                                       when 'игра в теннис' then 66
                                                       else 0 end else 0 end )as fizraType,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Другие физ нагрузки' and  aps.value is not null and aps.value<>'' then 67  else 0 end )as fizraTypeOther,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Характер отдыха' then case aps.value when 'активный'then 70 
                                                      when 'пассивный' then 71
                                                      when 'смешанный' then 72
                                                      else 0 end else 0 end )as restType,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Характер труда' then case aps.value when 'нормированный рабочий день' then 74
                                                       when 'ненормированный рабочий день' then 75
                                                       else 0 end else 0 end )as workType,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Работа'  then case aps.value when 'сидячая' then 77
                                                       when 'на ногах' then 78
                                                       when 'разъезды' then 79
                                                       else 0 end else 0 end )as work,
max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Другая работа'  and  aps.value is not null and aps.value<>'' then 80  else 0 end )as workOther,
 max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Производственные вредности'  then case aps.value when 'химические факторы' then 82
                                                       when 'биологические факторы' then 83
                                                       when 'производный шум' then 84
                                                       when 'вибрация' then 85
                                                       when 'статическое напряжение' then 86
                                                       when 'перенапряжение голосового и (или) зрительного аппарата ' then 87
                                                       else 0 end else 0 end )as vrednost,
max(case when at.flatCode = 'anam_san' and at.code = '1-04-02' and
  apt.name = 'Другие факторы вредности'  and  aps.value is not null and aps.value<>'' then 88  else 0 end )as vrednostOther,
 max(case when at.flatCode = 'app_san' and at.code = '1-04-03' and
  apt.name = 'Цель настоящего обращения'  then case aps.value when 'получение информации о здоровом образе жизни' then 91
                                                       when 'правильное питание' then 92
                                                       when 'отказ от табакокурения' then 93
                                                       when 'отказ от приема алкоголя' then 94
                                                       when 'получение информации о наличии заболеваний' then 95
                                                       else 0 end else 0 end )as goal,
max(case when at.flatCode = 'app_san' and at.code = '1-04-03' and
  apt.name = 'Другая цель' and  aps.value is not null and aps.value<>'' then 96  else 0 end )as goalOther,
 max(case when at.flatCode = 'app_san' and at.code = '1-04-03' and
  apt.name = 'Источник получения информации'  then case aps.value when 'радио' then 99
                                                       when 'телевидение' then 100
                                                       when 'печатные издания' then 101
                                                       when 'интернет' then 102
                                                       when 'от врача' then 103
                                                       when 'от знакомых' then 104
                                                       else 0 end else 0 end )as info,
max(case when at.flatCode = 'app_san' and at.code = '1-04-03' and
  apt.name = 'Другие источники информации'   and  aps.value is not null and aps.value<>'' then 105  else 0 end )as infoOther,
 max(case when at.flatCode = 'san_san' and at.code = '1-04-04' and apt.name = 'АД (систолическое)'  then api.value else 0 end )as ad_s,
 max(case when at.flatCode = 'san_san' and at.code = '1-04-04' and apt.name = 'АД (диастолическое)'  then api.value else 0 end )as ad_d,
 max(case when at.flatCode = 'san_san' and at.code = '1-04-04' and apt.name = 'ИМТ'  then apd.value  else 0 end )as imt,
 max(case when at.flatCode = 'san_san' and at.code = '1-04-04' and apt.name = 'Глюкоза натощак (ммоль/л)'  then apd.value else 0 end )as glukoza,
 max(case when at.flatCode = 'san_san' and at.code = '1-04-04' and apt.name = 'Холестерин (ммоль/л)'  then apd.value else 0 end )as holesterin
from Action a 
left join ActionType at on a.actionType_id = at.id 
left join ActionProperty ap on ap.action_id = a.id and ap.deleted=0
left join ActionPropertyType apt on ap.type_id = apt.id and ap.deleted=0
left join ActionProperty_String aps on aps.id = ap.id 
left join ActionProperty_Integer api on api.id = ap.id 
left join ActionProperty_Double apd on apd.id = ap.id 
group by a.event_id)act on act.event_id = e.id
inner JOIN
(select v.event_id as pervichno from Visit v 
left join rbService rbs on v.service_id = rbs.id
where rbs.code ='B01.069.014' and v.deleted=0
group by v.event_id) usl on usl.pervichno = e.id
where   mt.regionalCode in ('01','02') AND e.deleted = 0 AND %s
group by e.id;
"""
    db.query(stmt  % (db.joinAnd(cond)))

    stmt=u"""
CREATE TEMPORARY TABLE if not exists CHealthCenterAnaliz_SecondResultData AS
select vidObr as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where vidObr>0
group by vidObr
"""
    db.query(stmt )


    stmt = u"""
insert INTO CHealthCenterAnaliz_SecondResultData
select socStatus as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where socStatus>0
group by socStatus
"""
    db.query(stmt )

    stmt ="""
    insert INTO CHealthCenterAnaliz_SecondResultData
select vidObraz as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where vidObraz>0
group by vidObraz
"""
    db.query(stmt )

    stmt = """
insert INTO CHealthCenterAnaliz_SecondResultData
select jitel as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where jitel>0
group by jitel
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select useAlc as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where useAlc>0
group by useAlc
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select typeAlc as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where typeAlc>0
group by typeAlc
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select typeSmoke as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where typeSmoke>0
group by typeSmoke
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select ageSmoke as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where ageSmoke>0
group by ageSmoke
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select countSmoke as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where countSmoke>0
group by countSmoke
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select rejim as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where rejim>0
group by rejim
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select komponent as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where komponent>0
group by komponent
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select kaloria as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where kaloria>0
group by kaloria
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select dream as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where dream>0
group by dream
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select fizra as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where fizra>0
group by fizra
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select fizraType as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where fizraType>0
group by fizraType
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select fizraTypeOther as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where fizraTypeOther>0
group by fizraTypeOther
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select restType as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where restType>0
group by restType
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select workType as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where workType>0
group by workType
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select work as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where work>0
group by work
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select workOther as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where workOther>0
group by workOther
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select vrednost as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where vrednost>0
group by vrednost
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select vrednostOther as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where vrednostOther>0
group by vrednostOther
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select goal as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where goal>0
group by goal
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select goalOther as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where goalOther>0
group by goalOther
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select info as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where info>0
group by info
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select infoOther as numberStr,
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where infoOther>0
group by infoOther
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select case when (ad_s between 60 and 90 and  ad_d between 100 and 140) then 108
       else case when (ad_s > 90 or ad_d > 140) then 109 
       else case when (ad_s < 60 or ad_d < 90) then 110
       end end end as numberStr, 
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where ad_s>0  and ad_d>0
group by numberStr
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select case when (imt between 18.5 and 24.9) then 112
       else case when (imt between 25.0 and 29.9) then 113 
       else case when (imt >= 30) then 114 
       else case when (imt <= 18.4) then 115
       end end end end as numberStr, 
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where imt>0 
group by numberStr
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select case when (glukoza between 2.2 and 6.5) then 117
       else case when (glukoza > 6.5) then 118 
       else case when (glukoza < 2.2) then 119 
       end end end as numberStr, 
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where glukoza>0 
group by numberStr
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select case when holesterin <= 5.0 then 121 else 122 end as numberStr, 
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where holesterin>0 
group by numberStr
"""
    db.query(stmt )

    stmt = """insert INTO CHealthCenterAnaliz_SecondResultData
select case ((case typeSmoke when 30 then 1 else 0 end)+
       (case when holesterin > 5 then 1 else 0 end)+
       (case when imt > 24.9 then 1 else 0 end)+
       (case when ad_s > 90 or ad_d > 140 then 1 else 0 end)) when 2 then 124 
       when 3 then 125 when 4 then 126 end as numberStr, 
 count(case when sex='1' and clientAge<18 then id end ) male17,
 count(case when sex='1' and clientAge between 18 and 29 then id end ) male29,
 count(case when sex='1' and clientAge between 30 and 39 then id end ) male39,
 count(case when sex='1' and clientAge between 40 and 49 then id end ) male49,
 count(case when sex='1' and clientAge between 50 and 59 then id end ) male59,
 count(case when sex='1' and clientAge>59 then id end ) male60,
 count(case when sex='2' and clientAge<18 then id end ) female17,
 count(case when sex='2' and clientAge between 18 and 29 then id end ) female29,
 count(case when sex='2' and clientAge between 30 and 39 then id end ) female39,
 count(case when sex='2' and clientAge between 40 and 49 then id end ) female49,
 count(case when sex='2' and clientAge between 50 and 59 then id end ) female59,
 count(case when sex='2' and clientAge>59 then id end ) female60
from CHealthCenterAnaliz_FirstResultData
where ((case typeSmoke when 30 then 1 else 0 end)+
       (case when holesterin > 5 then 1 else 0 end)+
       (case when imt > 24.9 then 1 else 0 end)+
       (case when ad_s > 90 or ad_d > 140 then 1 else 0 end))>1
group by numberStr
"""
    db.query(stmt)
    stmt = u""" select * from CHealthCenterAnaliz_SecondResultData """
    return db.query(stmt)

class CHealthCenterAnaliz(CReport):
    name = u'Анализ факторов риска развития заболеваний среди первичных пациентов ЦЗ'


    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(self.name)
        self.setOrientation(QtGui.QPrinter.Landscape)

    def getSetupDialog(self, parent):
        result = CHealthCenterForm68SetupDialog(parent)
        result.setWindowTitle(self.name)
        return result

    def initRowWithZeroValue(self, table):
        i = table.addRow()
        for p in range(0, 12):
            table.setText(i, p+1, 0)
        return i


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

        cursor.insertBlock()

        columns = [('80%', [], CReportBase.AlignLeft),('20%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=4, border=0, cellPadding=2, cellSpacing=0)

        table.setText(0, 1, u'Форма ЦЗ №')
        table.setText(1, 1, u'Приложение к приказу')
        table.setText(2, 1, u'департамента здравоохранения')
        table.setText(3, 1, u'от 02.02.2011 №190')

        cursor.movePosition(QtGui.QTextCursor.End)

        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)

        cursor.insertBlock()
        columns2 = [('100%', [], CReportBase.AlignCenter)]

        cursor.insertBlock()
        table2 = createTable(cursor, columns2, headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0, 0, u'Анализ факторов риска развития заболеваний среди первичных пациентов ЦЗ ', charFormat=CReport.ReportTitle)
        cursor.movePosition(QtGui.QTextCursor.End)

        table2 = createTable(cursor, columns2, headerRowCount=3, border=0, cellPadding=2, cellSpacing=0)

        underlinedChars = QtGui.QTextCharFormat()
        underlinedChars.setFontWeight(QtGui.QFont.Bold)
        underlinedChars.setFontUnderline(True)

        table2.setText(0, 0, orgName, charFormat=underlinedChars)
        table2.setText(1,0, u'(наименование центра здоровья)')
        table2.setText(2, 0, u'за %s'%(str(begDate.year())+u' год' if begDate.month() == 1 and endDate.month() == 12 else monthList[endDate.month() - 1]+' '+str(begDate.year())+u' года'), charFormat=underlinedChars)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)

        tableColumns = [('30%', [u'Показатель',u'', u''], CReportBase.AlignLeft),
                ('5%', [u'Мужчины', u'возраст, лет', u'0-17'], CReportBase.AlignRight),
                ('5%', [u'', u'', u'18-29'], CReportBase.AlignRight),
                ('6%', [u'', u'', u'30-39'], CReportBase.AlignRight),
                ('6%', [u'', u'', u'40-49'], CReportBase.AlignRight),
                ('6%', [u'', u'', u'50-59'], CReportBase.AlignRight),
                ('7%', [u'', u'', u'60 и старше'], CReportBase.AlignRight),
                ('5%', [u'Женщины', u'возраст, лет', u'0-17'], CReportBase.AlignRight),
                ('5%', [u'', u'', u'18-29'], CReportBase.AlignRight),
                ('6%', [u'', u'', u'30-39'], CReportBase.AlignRight),
                ('6%', [u'', u'', u'40-49'], CReportBase.AlignRight),
                ('6%', [u'', u'', u'50-59'], CReportBase.AlignRight),
                ('7%', [u'', u'', u'60 и старше'], CReportBase.AlignRight),
                ]


        table = createTable(cursor, tableColumns)

        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 1, 6)
        table.mergeCells(1, 1, 1, 6)
        table.mergeCells(0, 7, 1, 6)
        table.mergeCells(1, 7, 1, 6)

        i = table.addRow()
        table.setText(i, 0, u'Вид обращения',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             обратился самостоятельно')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             направлен амбулаторно-профилактическим учреждением')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             направлен после доп.диспансеризации')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             направлен после лечения в стационаре')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             направлен работодателем')
        i = table.addRow()
        table.setText(i, 0, u'Социальный статус',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             служащий')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             рабочий')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             учащийся')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             неработающий')
        i = table.addRow()
        table.setText(i, 0, u'Вид образования',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             высшее')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             среднее')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             начальное')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             не имеет')
        i = table.addRow()
        table.setText(i, 0, u'Житель',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'          городской')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'          сельский')
        i = table.addRow()
        table.setText(i, 0, u'Употребление алкоголя',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             случайно')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             мало')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             много')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             часто')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             не употребляет')
        i = table.addRow()
        table.setText(i, 0, u'Количество потребляемого алкоголя',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             крепкие алкогольные напитки')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             слабоалкогольные напитки')
        i = table.addRow()
        table.setText(i, 0, u'Табакокурение',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             не курит')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             курит')
        i = table.addRow()
        table.setText(i, 0, u'     с какого возраста',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             0-9 лет')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             10-14 лет')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             15-19 лет')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             20-39 лет')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             40 лет и старше')
        i = table.addRow()
        table.setText(i, 0, u'     по сколько штук в день',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             1-4 шт.')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             5-9 шт.')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             10-20 шт.')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             21 и более')
        i = table.addRow()
        table.setText(i, 0, u'Режим питания',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             регулярный')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             нерегулярный')
        i = table.addRow()
        table.setText(i, 0, u'Преобладание компонентов продуктов питания',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             белки')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             жиры')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             углеводы')
        i = table.addRow()
        table.setText(i, 0, u'Калорийность рациона',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             высокая')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             низкая')
        i = table.addRow()
        table.setText(i, 0, u'Сон',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             7-9 часов')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             менее 7 часов')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             более 9 часов')
        i = table.addRow()
        table.setText(i, 0, u'Занятия физической культурой и спортом',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             систематическое')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             случайное')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             не занимается')
        i = table.addRow()
        table.setText(i, 0, u'Физкультура',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             утренняя гимнастика')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             бег')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             ходьба на лыжах')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             езда на велосипеде')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             оздоровительное плавание')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             игра в теннис')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             другое')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             сочетание нескольких видов')
        i = table.addRow()
        table.setText(i, 0, u'Характер отдыха',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             активный')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             пассивный')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             смешанный')
        i = table.addRow()
        table.setText(i, 0, u'Характер труда',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             нормированный рабочий день')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             ненормированный рабочий день')
        i = table.addRow()
        table.setText(i, 0, u'Работа',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             сидячая')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             на ногах')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             разъезды')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             другая')
        i = table.addRow()
        table.setText(i, 0, u'Производственные вредности',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             химические факторы')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             биологические факторы')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             производственный шум')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             вибрация')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             статическое напряжение')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             перенапряжение голосового или зрительного аппарата')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             другое')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             сочетание нескольких видов')
        i = table.addRow()
        table.setText(i, 0, u'Цель обращения',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             получение информации о ЗОЖ')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             правильное питание')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             отказ от табакокурения')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             отказ от приёма алкоголя')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             получение информации о наличии заболеваний')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             другое')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             сочетание нескольких видов')
        i = table.addRow()
        table.setText(i, 0, u'Источник получения информации',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             радио')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             телевидение')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             печатные издания')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             интернет')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             от врача')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             от знакомых')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             другое')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             сочетание нескольких видов')
        i = table.addRow()
        table.setText(i, 0, u'Артериальное давление',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             норма')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             повышенное')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             пониженное')
        i = table.addRow()
        table.setText(i, 0, u'Индекс массы тела (ИМТ)',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             норма (18,5-24,9)')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             избыточный вес (ИМТ - 25,0-29,9)')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             ожирение (ИМТ - 30,0 и выше)')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             дефицит массы тела (ИМТ - 18,4 и менее)')
        i = table.addRow()
        table.setText(i, 0, u'Глюкоза крови',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             норма')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             гипергликемия')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             гипогликемия')
        i = table.addRow()
        table.setText(i, 0, u'Холестерин крови',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             норма')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             повышен')
        i = table.addRow()
        table.setText(i, 0, u'Сочетание факторов риска развития заболеваний ССС (курение, повышенное АД, избыточный вес или ожирение, повышенный холестерин)',charFormat=boldChars)
        table.mergeCells(i, 0, 1, 13)
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             2 фактора')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             3 фактора')
        i = self.initRowWithZeroValue(table)
        table.setText(i, 0, u'             4 фактора')

        cursor.movePosition(QtGui.QTextCursor.End)
        query = selectData(begDate, endDate)

        while query.next():
            record = query.record()
            numberStr = forceInt(record.value('numberStr'))+3
            table.setText(numberStr, 1, forceInt(record.value('male17')))
            table.setText(numberStr, 2, forceInt(record.value('male29')))
            table.setText(numberStr, 3, forceInt(record.value('male39')))
            table.setText(numberStr, 4, forceInt(record.value('male49')))
            table.setText(numberStr, 5, forceInt(record.value('male59')))
            table.setText(numberStr, 6, forceInt(record.value('male60')))
            table.setText(numberStr, 7, forceInt(record.value('female17')))
            table.setText(numberStr, 8, forceInt(record.value('female29')))
            table.setText(numberStr, 9, forceInt(record.value('female39')))
            table.setText(numberStr, 10, forceInt(record.value('female49')))
            table.setText(numberStr, 11, forceInt(record.value('female59')))
            table.setText(numberStr, 12, forceInt(record.value('female60')))


        cursor.insertBlock()
        columns2 = [('30%', [], CReportBase.AlignLeft),('35%', [], CReportBase.AlignLeft),('35%', [], CReportBase.AlignCenter)]
        table2 = createTable(cursor, columns2, headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)
        table2.setText(0,1,u'Руководитель', charFormat = boldChars)
        table2.setText(0,2,u'_______________________________________________________________________')

        return doc
