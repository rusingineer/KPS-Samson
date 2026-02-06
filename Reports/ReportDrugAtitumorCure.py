# -*- coding: utf-8 -*-
################################################################

from PyQt4 import QtGui, Qt, QtCore
from PyQt4.QtCore import QDate

from library.Utils import forceBool, forceInt, forceString
from Orgs.Utils import getOrgStructureDescendants, getOrgStructures, getOrgStructureFullName
from Reports.Report import CReport
from library.DateEdit import CDateEdit
from Orgs.OrgStructComboBoxes import COrgStructureComboBox, CAreaComboBox
from Orgs.PersonComboBoxEx import CPersonComboBoxEx
from library.crbcombobox import CRBComboBox

from library.DialogBase import CDialogBase
from datetime import date


class CReportDrugAtitumorCure(CReport):
    def columnNumber(self, MKB):
        MKB = MKB.split(u'.')[0]
        if MKB in (u'C01', u'C02', u'C03', u'C04', u'C05', u'C06', u'C07', u'C08', u'C09'):
            column = 1
        elif MKB in (u'C10', u'C11', u'C12', u'C13'):
            column = 2
        elif MKB in (u'C15'):
            column = 3
        elif MKB in (u'C16'):
            column = 4
        elif MKB in (u'C18', u'C19', u'C20', u'C21'):
            column = 5
        elif MKB in (u'C22'):
            column = 6
        elif MKB in (u'C25'):
            column = 7
        elif MKB in (u'C32'):
            column = 8
        elif MKB in (u'C33', u'C34'):
            column = 9
        elif MKB in (u'C43'):
            column = 10
        elif MKB in (u'C47', u'C49'):
            column = 11
        elif MKB in (u'C50'):
            column = 12
        elif MKB in (u'C53'):
            column = 13
        elif MKB in (u'C54'):
            column = 14
        elif MKB in (u'C56'):
            column = 15
        elif MKB in (u'C61'):
            column = 16
        elif MKB in (u'C64'):
            column = 17
        elif MKB in (u'C67'):
            column = 18
        elif MKB in (u'C81', u'C82', u'C83', u'C84', u'C85', u'C86', u'C88', u'C90', u'C96'):
            column = 19
        elif MKB in (u'C91', u'C92', u'C93', u'C94', u'C95'):
            column = 20
        else:
            column = 21
        return column



    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сведения о проведенном лекарственном противоопухолевом лечении')
        self.orientation = QtGui.QPrinter.Landscape

    def selectStmt(self, params):
        begDate = params.get('begDate', None)  # Период начало
        endDate = params.get('endDate', None)  # Период конец
        orgStructure_id = params.get('orgStructure_id', None)  # Поздразделение
        person_id = params.get('person_id', None)  # Врач
        sex = params.get('sex', None)  # Пол
        ageBeg = params.get('ageBeg', None)  # Возраст начало
        ageEnd = params.get('ageEnd', None)  # Возраст конец
        paidStatus = params.get('paidStatus', None)  # Выставлено в счета
        area_id = params.get('area_id', None)  # Участок
        ignoreShineCure = params.get('ignoreShineCure', False)  # Не вкл. схемы лекарств учавств. в лучевой
        socStatusType_id = params.get('socStatusType_id', None)  # Соц статус
        finance_id = params.get('finance_id', None)  # Тип финансирования
        medicalAidKind_id = params.get('medicalAidKind_id', None)  # Вид помощи

        sql_request = u"""
            SELECT e.id as 'e_id', e.execDate, c.sex, a.id as 'act_id',
            ss.code as 'ss_code', ss.name as 'ss_name', ss.drugName as 'ss_drugName', ds.MKB
             from Event e

        """

        sql_join = u""" 
                left join EventType et on et.id = e.eventType_id and et.deleted = 0
                left join rbMedicalAidType mat on mat.id = et.medicalAidType_id 
                left join Action a on a.event_id = e.id and a.deleted = 0
                left join ActionType at on at.id = a.actionType_id and at.deleted = 0
                left join ActionProperty ap on ap.action_id = a.id and ap.deleted = 0
                left join ActionPropertyType apt on apt.id = ap.type_id and apt.deleted = 0
                left join ActionProperty_Integer api on api.id = ap.id
                left join soc_spr80 ss on api.value = ss.id
                left join Diagnostic dc on dc.event_id = e.id and dc.deleted = 0
                left join Diagnosis ds on ds.id = dc.diagnosis_id and ds.deleted = 0
                left join rbDiagnosisType dst on dst.id = dc.diagnosisType_id 
                left join Client c on c.id = e.client_id and c.deleted = 0 
                """

        cond = u""" 
        WHERE e.deleted = 0 
                    AND at.flatCode = 'KRIT'
                    AND apt.name = 'Схема лечения ЗНО'  AND ss.id is not null and ss.type in (1, 13)
                    AND mat.regionalCode in (11, 12, 41, 42)
                    AND dst.name like 'закл%'  
                    AND (ds.MKB like 'C%' or ds.MKB like 'D0%' )
                """

        if begDate:
            cond += u""" AND date(e.setDate) >= '""" + u"-".join(forceString(begDate).split(u'.')[::-1]) + u"' "
        if endDate:
            cond += u""" AND date(e.setDate) <= '""" + u"-".join(forceString(endDate).split(u'.')[::-1]) + u"' "
        if ageBeg or ageEnd:
            if ageBeg and forceInt(ageBeg) != 0:
                cond += u""" AND age(c.birthDate, e.setDate) >= """ + forceString(ageBeg) + u"  "
            if ageEnd and forceInt(ageEnd) != 150:
                cond += u""" AND age(c.birthDate, e.setDate) <= """ + forceString(ageEnd) + u"  "
        if person_id:
            cond += u""" AND e.setPerson_id  = """ + forceString(person_id) + u" "
        if orgStructure_id:
            list_orgStructure_id = QtGui.qApp.db.getDescendants('OrgStructure', 'parent_id', forceInt(orgStructure_id))
            sql_join += u""" left join Person p on p.id = e.setPerson_id  and p.deleted = 0  """
            cond += u""" AND p.orgStructure_id in  (""" + u','.join(forceString(org_id) for org_id in list_orgStructure_id) + u")  "
        if area_id:
            sql_join += u""" left join ClientAttach ca on ca.client_id = c.id and ca.deleted = 0 and ca.endDate is NULL """
            cond += u""" AND ca.orgStructure_id in  (""" + forceString(area_id) + u") "
        if sex and forceInt(sex) > 0:
            cond += u"""  AND c.sex = """ + forceString(sex) + u" "
        if paidStatus and forceInt(paidStatus) > 0:
            if forceInt(paidStatus) == 1:
                cond += u""" AND EXISTS (select 1 from Account_Item ai where  ai.deleted = 0 and ai.event_id = e.id ) """
            elif forceInt(paidStatus) == 2:
                cond += u""" AND NOT EXISTS (select 1 from Account_Item ai where  ai.deleted = 0 and ai.event_id = e.id ) """
        if ignoreShineCure:
            cond += u""" AND ss.code not LIKE 'mt%' """
        if socStatusType_id:
            cond += u""" AND EXISTS (select 1 from ClientSocStatus css where css.deleted = 0 and css.client_id = c.id and   css.socStatusType_id = """ + forceString(
                socStatusType_id) + u" )  "
        if finance_id:
            cond += u""" AND  et.finance_id = """ + forceString(finance_id) + u" "
        if medicalAidKind_id:
            cond += u""" AND et.medicalAidKind_id = """ + forceString(medicalAidKind_id) + u" "

        sql_order = u"""
        order by
              case
                when ss.code like 'sh%' then 1
                when ss.code like 'gemop%' then 2
                when ss.code like 'mt%' then 3
              else 4
              end, ss.code
        """

        sql_request += sql_join  # Добавляем джоины
        sql_request += cond  # Добавляем условия
        sql_request += sql_order  # Добавляем сортировку

        return sql_request

    def build(self, params):


        filter_string = u""
        begDate = params.get('begDate', None)  # Период начало
        endDate = params.get('endDate', None)  # Период конец
        orgStructure_id = params.get('orgStructure_id', None)  # Поздразделение
        person_id = params.get('person_id', None)  # Врач
        sex = params.get('sex', None)  # Пол
        ageBeg = params.get('ageBeg', None)  # Возраст начало
        ageEnd = params.get('ageEnd', None)  # Возраст конец
        paidStatus = params.get('paidStatus', None)  # Выставлено в счета
        area_id = params.get('area_id', None)  # Участок
        ignoreShineCure = params.get('ignoreShineCure', False)  # Не вкл. схемы лекарств учавств. в лучевой
        socStatusType_id = params.get('socStatusType_id', None)  # Соц статус
        finance_id = params.get('finance_id', None)  # Тип финансирования
        medicalAidKind_id = params.get('medicalAidKind_id', None)  # Вид помощи
        if begDate or endDate:
            filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Период: """ + (
                u" с " + forceString(begDate) if begDate else u"") + (
                                 u" по " + forceString(endDate) if endDate else u"")
        if orgStructure_id:
            orgStructureSql = QtGui.qApp.db.getRecordList('OrgStructure', 'OrgStructure.name',
                                                          u'id in (' + forceString(orgStructure_id) + u")")
            if orgStructureSql[0]:
                filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Подразеделение: """ + forceString(
                    orgStructureSql[0].value('name')) + u"</p>"
        if person_id:
            personSql = QtGui.qApp.db.getRecordList('Person', "Person.lastName, Person.firstName, Person.patrName",
                                                    u'id in (' + forceString(person_id) + u")")
            if personSql[0]:
                filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Врач: """ + forceString(
                    personSql[0].value('lastName')) + u' ' +  forceString(
                    personSql[0].value('firstName'))[0] + u'. ' + forceString(
                    personSql[0].value('patrName'))[0] + u'.' + u"</p>"
        if sex:
            filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Пол: """ + (
                u"Мужской" if forceInt(sex) == 1 else u"Женский") + u"</p>"

        if (ageBeg or ageEnd) and not (forceInt(ageBeg) == 0 and forceInt(ageEnd) == 150):
            filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Возраст: """ + (
                u'с ' + forceString(ageBeg) + u' ' if ageBeg else u"") + (
                                 u'по ' + forceString(ageEnd) + u' ' if ageEnd else u"")
        if area_id:
            areaSql = QtGui.qApp.db.getRecordList('OrgStructure', 'OrgStructure.name',
                                                  u'id in (' + forceString(area_id) + u")")
            if areaSql[0]:
                filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Участок: """ + forceString(
                    areaSql[0].value('name')) + u"</p>"
        if paidStatus and paidStatus > 0:
            filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Выставлено в счёт: """ + (u"Да" if forceInt(paidStatus) == 1 else u"Нет") +u"""</p>"""
        if ignoreShineCure:
            filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Не включать схемы лекарственной терапии, применяемые совместно с лучевой</p>"""
        if socStatusType_id:
            socStatusType = QtGui.qApp.db.getRecordList('rbSocStatusType', 'rbSocStatusType.name',
                                                  u'id in (' + forceString(socStatusType_id) + u")")
            if socStatusType[0]:
                filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Социальный статус: """ + forceString(
                    socStatusType[0].value('name')) + u"</p>"

        if finance_id:
            finance = QtGui.qApp.db.getRecordList('rbFinance', 'rbFinance.name', u'id in (' + forceString(finance_id) + u") ")
            if finance[0]:
                filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Тип финансирования: """ + forceString(finance[0].value('name')) + u"</p>"
        if medicalAidKind_id:
            medicalAidKind = QtGui.qApp.db.getRecordList('rbMedicalAidKind', 'rbMedicalAidKind.name', u'id in (' + forceString(medicalAidKind_id) + u") ")
            if medicalAidKind[0]:
                filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Вид помощи: """ + forceString(medicalAidKind[0].value('name')) + u"</p>"

        doc = u"""
        <!DOCTYPE html>
<html lang="en">
<head>
    {setPageSize('A4')} {setOrientation('L')} {setLeftMargin(10)} {setTopMargin(10)} {setBottomMargin(10)} {setRightMargin(10)} 
</head>
<body>

<p style="font-size: 11pt; margin: 0; padding: 0;" ><b>Сведения о проведенном лекарственном противоопухолевом лечении в условиях дневного стационара ЦАОПа</b></p>
"""  + filter_string  + u"""
        <table border=1 cellSpacing=0 cellPadding=0 width=100%>
  <tr>
    <td rowspan="3" align="center" style="vertical-align: middle; font-size: 7pt;" width=13%>
      <b>Наименование медицинской организации</b>
    </td>
    <td rowspan="3" align="center" style="vertical-align: middle; font-size: 7pt;" width=4%>
      <b>Код схемы</b> 
    </td>
    <td rowspan="3" align="center" style="vertical-align: middle; font-size: 7pt;" width=14%>
      <b>МНН лекарственных препаратов</b>
    </td>
    <td rowspan="3" align="center" style="vertical-align: middle; font-size: 7pt;" width=7%>
      <b>Количество госпитализаций</b>
    </td>
    <td colspan="21" align="center" style="vertical-align: middle; font-size: 7pt;" width=62%>
      <b>из них</b>
    </td>
  </tr>
  <tr>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >полости рта</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >глотки</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >пищевода</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >желудка</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >Колоректальный рак</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >печени и внутрипеченочных желчных протоков</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >поджелудочной железы</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >гортани</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >трахеи, бронхов, легкого</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >меланома кожи</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >соединительной и других мягких тканей</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >молочной железы</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >шейки матки</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >тела матки</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >яичника</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >предстательной железы</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >почки</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >мочевого пузыря</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >злокачественные лимфомы</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2% >лейкозы</td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;" rowspan="2" width=4%><b>прочие</b></td>
  </tr>
  <tr>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C01 - C09</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C10 - C13</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C15</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C16</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C18-С21</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C22</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C25</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C32</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C33, C34</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C43</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C47, C49</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C50</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C53</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C54</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C56</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C61</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C64</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C67</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C81 - C86; C88; C90; C96</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C91 - C95</b></td>
  </tr>

        """
        string_colNumber = u"<tr>"
        for i in range(25):
            string_colNumber += u""" <td align="center" style="font-size: 7pt;"><i>""" + forceString(
                i + 1) + u"</i></td> "
        string_colNumber += u" </tr> "
        doc += string_colNumber

        sql_req = self.selectStmt(params)
        sql_query = QtGui.qApp.db.query(sql_req)
        matrica = dict()
        list_of_rows = set()
        list_of_drugNamess = dict()
        while sql_query.next():
            sql_record = sql_query.record()
            ss_code = forceString(sql_record.value('ss_code'))
            mkb_code = forceString(sql_record.value('MKB'))
            drugName = forceString(sql_record.value('ss_drugName'))
            col = self.columnNumber(mkb_code)
            temp_dict_columns = {
                u'0': 0, u'1': 0, u'2': 0, u'3': 0, u'4': 0, u'5': 0, u'6': 0, u'7': 0, u'8': 0, u'9': 0, u'10': 0,
                u'11': 0, u'12': 0, u'13': 0, u'14': 0, u'15': 0, u'16': 0, u'17': 0, u'18': 0, u'19': 0, u'20': 0, u'21': 0
            }
            if ss_code not in matrica.keys():
                matrica[ss_code] = temp_dict_columns
            matrica[ss_code][forceString(col)] += 1
            matrica[ss_code][u'0'] += 1
            list_of_drugNamess[ss_code] = drugName
            list_of_rows.add(ss_code)

        list_of_rows = sorted(list_of_rows, key = self.sortedKey)
        for row in list_of_rows:
            row_string = u""" <tr><td></td> """
            row_string += u'<td align="center" style="font-size:7pt;" >' + forceString(row) + u"</td> "
            row_string += u'<td style="font-size:7pt;">' + forceString(list_of_drugNamess[row]) + u"</td> "

            for columnMatrix in range(22):
                row_string  += u'<td align="center" style="font-size:9pt;">' + (forceString(matrica[row][forceString(columnMatrix)]) if matrica[row][forceString(columnMatrix)] > 0 else u' ') + u"</td> "
            row_string += u"</tr>"
            doc += row_string


        doc += u"""
        </table>
</body>
</html>
        """

        return doc


    def getSetupDialog(self, parent):
        result = CReportDrugAtitumorCureDialog(parent)
        result.setTitle(self.title())
        return result


    # ф-ия для сортировки строк
    def sortedKey(self, word):
        if word.startswith('sh'):
            return (0, float(word[2:]))
        elif word.startswith('gemop'):
            return (1, float(word[5:]))
        elif word.startswith('mt'):
            return (2, float(word[2:]))
        else:
            return (3, word)


class CReportDrugAtitumorCureDialog(CDialogBase):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)

        self.layout = QtGui.QGridLayout(self)

        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.dateStart = CDateEdit()
        self.dateStart.setDate(QDate(date.today()))
        self.dateEnd = CDateEdit()
        self.dateEnd.setDate(QDate(date.today()))
        self.cmbOrgStructure = COrgStructureComboBox(self)
        self.cmbPerson = CPersonComboBoxEx(self)

        self.cmbSex = QtGui.QComboBox(self)
        self.cmbSex.addItem(u'Не выбрано')
        self.cmbSex.addItem(u'Мужской')
        self.cmbSex.addItem(u'Женский')
        self.ageBeg = QtGui.QSpinBox(self)
        self.ageBeg.setRange(0, 150)
        self.ageBeg.setValue(0)
        self.ageEnd = QtGui.QSpinBox(self)
        self.ageEnd.setRange(0, 150)
        self.ageEnd.setValue(150)

        self.ageLayout = QtGui.QHBoxLayout(self)

        self.ageLayout.addWidget(QtGui.QLabel(u'с'))
        self.ageLayout.addWidget(self.ageBeg)
        self.ageLayout.addWidget(QtGui.QLabel(u'по'))
        self.ageLayout.addWidget(self.ageEnd)

        self.cmbExposed = QtGui.QComboBox(self)
        self.cmbExposed.addItem(u'Не выбрано')
        self.cmbExposed.addItem(u'Да')
        self.cmbExposed.addItem(u'Нет')
        self.cmbArea = CAreaComboBox(self)
        self.chkIgnoreShineCure = QtGui.QCheckBox(
            u'не включать схемы лекарственной терапии, применяемые совместно с лучевой')
        self.cmbSocStatusType = CRBComboBox(self)
        self.cmbSocStatusType.setTable('rbSocStatusType')
        self.cmbFinance = CRBComboBox(self)
        self.cmbFinance.setTable('rbFinance')
        self.cmbMedicalAidKind = CRBComboBox(self)
        self.cmbMedicalAidKind.setTable('rbMedicalAidKind')

        self.layout.addWidget(QtGui.QLabel(u'с'), 0, 0, 1, 1)
        self.layout.addWidget(self.dateStart, 0, 1, 1, 4)
        self.layout.addWidget(QtGui.QLabel(u'по'), 1, 0, 1, 1)
        self.layout.addWidget(self.dateEnd, 1, 1, 1, 4)
        self.layout.addWidget(QtGui.QLabel(u"Подразделение:"), 2, 0, 1, 1)
        self.layout.addWidget(self.cmbOrgStructure, 2, 1, 1, 4)
        self.layout.addWidget(QtGui.QLabel(u"Врач"), 3, 0, 1, 1)
        self.layout.addWidget(self.cmbPerson, 3, 1, 1, 4)
        self.layout.addWidget(QtGui.QLabel(u'Пол:'), 4, 0, 1, 1)
        self.layout.addWidget(self.cmbSex, 4, 1, 1, 4)
        self.layout.addWidget(QtGui.QLabel(u'Возраст'), 5, 0, 1, 1)
        self.layout.addLayout(self.ageLayout, 5, 1, 1, 4)

        self.layout.addWidget(QtGui.QLabel(u'Выставлено в счет:'), 6, 0, 1, 1)
        self.layout.addWidget(self.cmbExposed, 6, 1, 1, 4)
        self.layout.addWidget(QtGui.QLabel(u'Участок'), 7, 0, 1, 1)
        self.layout.addWidget(self.cmbArea, 7, 1, 1, 4)
        self.layout.addWidget(self.chkIgnoreShineCure, 8, 0, 1, 4)
        self.layout.addWidget(QtGui.QLabel(u'Соц. статус'), 9, 0, 1, 1)
        self.layout.addWidget(self.cmbSocStatusType, 9, 1, 1, 4)
        self.layout.addWidget(QtGui.QLabel(u'Тип финансирования'), 10, 0, 1, 1)
        self.layout.addWidget(self.cmbFinance, 10, 1, 1, 4)
        self.layout.addWidget(QtGui.QLabel(u'Вид помощи'), 11, 0, 1, 1)
        self.layout.addWidget(self.cmbMedicalAidKind, 11, 1, 1, 4)

        self.layout.addWidget(self.buttonBox, 12, 3, 1, 2)

    def setParams(self, params):
        # TODO
        pass

    def setTitle(self, title):
        self.setWindowTitle(title)

    def params(self):
        result = {}
        result['person_id'] = self.cmbPerson.value()
        result['orgStructure_id'] = self.cmbOrgStructure.value()
        result['begDate'] = self.dateStart.date()
        result['endDate'] = self.dateEnd.date()
        result['sex'] = self.cmbSex.currentIndex()
        result['paidStatus'] = self.cmbExposed.currentIndex()
        result['medicalAidKind_id'] = self.cmbMedicalAidKind.value()
        result['finance_id'] = self.cmbFinance.value()
        result['area_id'] = self.cmbArea.value()
        result['socStatusType_id'] = self.cmbSocStatusType.value()
        result['ignoreShineCure'] = self.chkIgnoreShineCure.isChecked()
        result['ageBeg'] = self.ageBeg.value()
        result['ageEnd'] = self.ageEnd.value()
        return result








