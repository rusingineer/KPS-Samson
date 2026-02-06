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
from datetime import date, datetime








class CReportOnkoByStages(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Выявленные онкологические заболевания')
        self.orientation = QtGui.QPrinter.Landscape


    def columnNumber(self, MKB):
        MKB = MKB.split(u'.')[0] if MKB else u''
        if MKB and MKB != u'':
            if u'C' in MKB and forceInt(u''.join(MKB[1:]))<= 95:
                if MKB in (u'C00'):
                    column = 1
                elif MKB in (u'C01', u'C02', u'C03', u'C04', u'C05', u'C06', u'C07', u'C08', u'C09'):
                    column = 2
                elif MKB in (u'C10', u'C11', u'C12', u'C13'):
                    column = 3
                elif MKB in (u'C15'):
                    column = 4
                elif MKB in (u'C16'):
                    column = 5
                elif MKB in (u'C18', u'C19', u'C20', u'C21'):
                    column = 6
                elif MKB in (u'C22'):
                    column = 7
                elif MKB in (u'C25'):
                    column = 8
                elif MKB in (u'C32'):
                    column = 9
                elif MKB in (u'C33', u'C34'):
                    column = 10
                elif MKB in (u'C40', u'C41'):
                    column = 11
                elif MKB in (u'C43'):
                    column = 12
                elif MKB in (u'C44'):
                    column = 13
                elif MKB in (u'C47', u'C49'):
                    column = 14
                elif MKB in (u'C50'):
                    column = 15
                elif MKB in (u'C53'):
                    column = 16
                elif MKB in (u'C54'):
                    column = 17
                elif MKB in (u'C56'):
                    column = 18
                elif MKB in (u'C61'):
                    column = 19
                elif MKB in (u'C64'):
                    column = 20
                elif MKB in (u'C67'):
                    column = 21
                elif MKB in (u'C73'):
                    column = 22
                elif MKB in (u'C81', u'C82', u'C83', u'C84', u'C85', u'C86', u'C88', u'C90', u'C96'):
                    column = 23
                elif MKB in (u'C91', u'C92', u'C93', u'C94', u'C95'):
                    column = 24
                else:
                    column = 25
            elif MKB in (u'D00', u'D01', u'D02', u'D03', u'D04', u'D05', u'D06', u'D07', u'D08', u'D09'):
                if MKB in (u'D05'):
                    column = 27
                elif MKB in (u'D06'):
                    column = 28
                else:
                    column = 26
            else:
                column = 25
        else:
            column = 25
        return column

    def selectStmt(self, params):
        now = datetime.now()
        sql_req = u""" SELECT Event.id, Diagnostic.TNMS as 'stage', Diagnosis.MKB as 'MKB'  from Event """
        sql_join = u"""
            left join Diagnostic on Diagnostic.event_id = Event.id and Diagnostic.deleted = 0
            left join Diagnosis on Diagnosis.id = Diagnostic.diagnosis_id and Diagnosis.deleted = 0
            left join rbDiagnosisType on rbDiagnosisType.id = Diagnostic.diagnosisType_id 
            left join Client on Client.id = Event.client_id and Client.deleted = 0
        """
        isDispanserCheckUp = params.get('isDispanserCheckUp', None)
        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)
        orgStructure_id = params.get('orgStructure_id', None)  # Поздразделение
        person_id = params.get('person_id', None)  # Врач
        sex = params.get('sex', None)  # Пол
        ageBeg = params.get('ageBeg', None)  # Возраст начало
        ageEnd = params.get('ageEnd', None)  # Возраст конец
        area_id = params.get('area_id', None)  # Участок
        socStatusType_id = params.get('socStatusType_id', None)


        cond = u" WHERE Event.deleted = 0 AND rbDiagnosisType.name like 'заключ%' AND (Diagnosis.MKB like 'C%' or Diagnosis.MKB like 'D0%') AND (Diagnosis.MKB NOT like 'C97%') AND (Diagnosis.MKB NOT like 'C98%') AND (Diagnosis.MKB NOT like 'C99%') "
        cond += u""" AND EXISTS(select 1 from rbDiseaseCharacter dc where dc.code = '2' AND Diagnostic.character_id = dc.id) """
        if begDate:
            cond += u""" AND date(Event.execDate) >= '""" + u"-".join(forceString(begDate).split(u'.')[::-1]) + u"' "
        if endDate:
            cond += u""" AND date(Event.execDate) <= '""" + u"-".join(forceString(endDate).split(u'.')[::-1]) + u"' "
        if ageBeg or ageEnd:
            if ageBeg and forceInt(ageBeg) != 0:
                cond += u""" AND age(Client.birthDate, Event.execDate) >= """ + forceString(ageBeg) + u"  "
            if ageEnd and forceInt(ageEnd) != 150:
                cond += u""" AND age(Client.birthDate, Event.execDate) <= """ + forceString(ageEnd) + u"  "
        if person_id:
            cond += u""" AND Event.setPerson_id  = """ + forceString(person_id) + u" "
        if orgStructure_id:
            list_orgStructure_id = QtGui.qApp.db.getDescendants('OrgStructure', 'parent_id', forceInt(orgStructure_id))
            sql_join += u""" left join Person on Person.id = Event.setPerson_id  and Person.deleted = 0  """
            cond += u""" AND Person.orgStructure_id in  (""" + u','.join(forceString(org_id) for org_id in list_orgStructure_id) + u")  "
        if area_id:
            sql_join += u""" left join ClientAttach on ClientAttach.client_id = Client.id and ClientAttach.deleted = 0 and ClientAttach.endDate is NULL """
            cond += u""" AND ClientAttach.orgStructure_id in  (""" + forceString(area_id) + u") "

        if sex and forceInt(sex) > 0:
            cond += u"""  AND Client.sex = """ + forceString(sex) + u" "

        if socStatusType_id:
            cond += u""" AND EXISTS (select 1 from ClientSocStatus css where css.deleted = 0 and css.client_id = Client.id and   css.socStatusType_id = """ + forceString(
                socStatusType_id) + u" )  "

        if isDispanserCheckUp:
            cond += u'''AND ( NOT EXISTS(SELECT DC.id
                                   FROM Diagnostic AS DC
                                   INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                   INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                   WHERE DS.client_id = Client.id
                                   AND date(DC.endDate) <= '%s' AND rbDP.name LIKE '%s' AND DC.deleted = 0 AND DS.deleted = 0
                                   AND (DC.diagnosis_id = Diagnosis.id OR DS.MKB = Diagnosis.MKB))
                        OR EXISTS(SELECT DC.id
                                   FROM Diagnostic AS DC
                                   INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                   INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                   WHERE DS.client_id = Client.id
                                   AND date(DC.endDate) <= '%s' AND rbDP.name LIKE '%s' AND DC.deleted = 0 AND DS.deleted = 0
                                   AND (DC.diagnosis_id = Diagnosis.id OR DS.MKB = Diagnosis.MKB)) ) ''' % (forceString(now.strftime('%Y-%m-%d')) , u'%снят%', forceString(now.strftime('%Y-%m-%d')) , u'%взят повторно%')

        sql_req += sql_join
        sql_req += cond

        return sql_req


    def getCellsInRow(self, matrica_row, title):
        row = u"""<td style="font-size:7pt;" align="center"><b>""" + forceString(title) + "</b></td>"
        for i in range(29):
            row += u"""<td style="font-size:7pt;" align="center">""" + ( forceString(matrica_row[forceString(i)]) if matrica_row[forceString(i)] else u" ") + u"</td>"
        return row


    def build(self, params):

        filter_string = u''

        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)
        if begDate or endDate:
            filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Период: """ + (u" с " + forceString(begDate) if begDate else u"") + (u" по " + forceString(endDate) if endDate else u"")
        orgStructure_id = params.get('orgStructure_id', None)  # Поздразделение
        if orgStructure_id:
            orgStructureSql =  QtGui.qApp.db.getRecordList('OrgStructure', 'OrgStructure.name', u'id in (' + forceString(orgStructure_id) + u")")
            if orgStructureSql[0]:
                filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Подразеделение: """ + forceString(orgStructureSql[0].value('name')) + u"</p>"
        person_id = params.get('person_id', None)  # Врач
        if person_id:
            personSql = QtGui.qApp.db.getRecordList('Person', "Person.lastName, Person.firstName, Person.patrName",
                                                          u'id in (' + forceString(person_id) + u")")
            if personSql[0]:
                filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Врач: """ + forceString(
                    personSql[0].value('lastName')) + forceString(
                    personSql[0].value('firstName'))[0] + u'. ' + forceString(
                    personSql[0].value('patrName'))[0] + u'.' + u"</p>"
        sex = params.get('sex', None)  # Пол
        if sex:
            filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Пол: """ + (u"Мужской" if forceInt(sex) == 1 else u"Женский") + u"</p>"
        ageBeg = params.get('ageBeg', None)  # Возраст начало
        ageEnd = params.get('ageEnd', None)  # Возраст конец
        if (ageBeg or ageEnd) and not (forceInt(ageBeg) == 0 and forceInt(ageEnd) == 150):
            filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Возраст: """ + (u'с ' + forceString(ageBeg) + u'г. ' if ageBeg else u"") + (u'по ' + forceString(ageEnd) + u'г. ' if ageEnd else u"")
        area_id = params.get('area_id', None)  # Участок
        if area_id:
            areaSql = QtGui.qApp.db.getRecordList('OrgStructure', 'OrgStructure.name',
                                                          u'id in (' + forceString(area_id) + u")")
            if areaSql[0]:
                filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Участок: """ + forceString(
                    areaSql[0].value('name')) + u"</p>"
        socStatusType_id = params.get('socStatusType_id', None)
        if socStatusType_id:
            socStatusType = QtGui.qApp.db.getRecordList('rbSocStatusType', 'rbSocStatusType.name',
                                                  u'id in (' + forceString(socStatusType_id) + u")")
            if socStatusType[0]:
                filter_string += u"""<p  style="font-size: 9pt;  margin:7px;  " align="center">Социальный статус: """ + forceString(
                    socStatusType[0].value('name')) + u"</p>"
        isDispanserCheckUp = params.get('isDispanserCheckUp', None)
        if isDispanserCheckUp:
            filter_string += u"""<p style="font-size: 9pt;  margin:7px;  " align="center" >Состоит на ДН на текущую дату по диагнозу<p>"""

        doc = u"""
<!DOCTYPE html>
<html lang="en">
<head>
</head>
<body>

<p style="font-size: 13pt; margin: 0; padding: 0; font-weight:900;" align="center"><b>Выявленные в ЦАОПе онкологические заболевания</b></p>
""" + filter_string + u""" <p style="font-size: 13pt;">&nbsp;</p>
<table border=1 cellSpacing=0 cellPadding=0 width=100%>
  <tr>
    <td rowspan="2" align="center" style="vertical-align: middle; font-size: 7pt;" width=11%><b>Наименование медицинской организации, структурным подразделением которой является ЦАОП</b></td>
    <td rowspan="2" align="center" style="vertical-align: middle; font-size: 7pt;" width=11%><b>Выявлено в отчетный период  в ЦАОПе</b> <i>(без выявленных посмертно)</i></td>
    <td  align="center" style="vertical-align: middle; font-size: 7pt;" width=5.25% ><b>Выявлено ЗНО - всего, из них:</b></td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >губы</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >полости рта</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >глотки</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >пищевода</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >желудка</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >Колоректальный рак</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >печени и внутрипеченочных желчных протоков</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >поджелудочной железы</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >гортани</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >трахеи, бронхов, легкого</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >костей и суставных хрящей</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >меланома кожи</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >других новообразований кожи</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >соединительной и других мягких тканей</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >молочной железы</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >шейки матки</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >тела матки</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >яичника</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >предстательной железы</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >почки</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >мочевого пузыря</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >щитовидной железы</td> 
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >злокачественные лимфомы</td>
    <td align="center" style=" vertical-align: middle;  font-size: 7pt;" width=2.5% >лейкозы</td>
    <td align="center" rowspan="2" style="vertical-align: middle; font-size: 7pt;" width=2.5%>Прочие</td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;" width=5.25%><b>Новообразования in situ всего,</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;" width=2.5%>Карцинома in situ молочной железы</td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;" width=2.5%>Карцинома in situ шейки матки</td>
  </tr>
  <tr>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C00 - C96</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C00</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C01-C09</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C10-С13</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C15</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C16</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C18-С21</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>С22</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>С25</b></td>    
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>С32</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C33, C34</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>С40, С41</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C43</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C44</b></td>    
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C47, C49</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C50</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C53</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C54</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C56</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C61</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C64</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C67</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C73</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C81 - C86; C88; C90; C96</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>C91 - C95</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>D00-09</b></td>
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>D05</b></td>    
    <td align="center" style="vertical-align: middle; font-size: 7pt;"><b>D06</b></td>
  </tr>
        """

        doc += u" <tr> "
        for i in range(31):
            doc += u"""<td align="center" style="font-size: 7pt;"><i>""" + forceString(i+1) + u"</i></td>"
        doc += u" </tr> "

        dict_stage = {u'0': u"I стадия", u'1': u"II стадия", u'2': u"III стадия", u'3': u"IV стадия", u'4': u"Без стадии", u'5': u"Всего"}
        matrica = dict()
        for item in dict_stage.keys():
            row_template = {u'0': 0, u'1': 0, u'2': 0, u'3': 0, u'4': 0, u'5': 0, u'6': 0, u'7': 0, u'8': 0, u'9': 0,
                            u'10': 0,
                            u'11': 0, u'12': 0, u'13': 0, u'14': 0, u'15': 0, u'16': 0, u'17': 0, u'18': 0, u'19': 0,
                            u'20': 0,
                            u'21': 0, u'22': 0, u'23': 0, u'24': 0, u'25': 0, u'26': 0, u'27': 0, u'28': 0}
            matrica[item] = row_template

        sql_stmt = self.selectStmt(params)
        sql_query = QtGui.qApp.db.query(sql_stmt)
        result_list = list()
        while sql_query.next():
            sql_record = sql_query.record()
            result_list.append(sql_record)

        for item in result_list:
            mkb = forceString(item.value('MKB'))
            colNumberByMKB = self.columnNumber(mkb)
            stage = forceString(item.value('stage'))
            rowNumber = 4
            if stage:
                stage = forceString(stage.split(u' ')[-1])
                if u'S' in stage:
                    for i in range(len(stage)):
                        if stage[i].upper() not in (u"I", u"V", u"0"):
                            stage = stage.replace(stage[i], u" ")
                    stage = stage.replace(u" ", u'')
                    if stage == u"IV":
                        rowNumber = 3
                    elif stage == u"III":
                        rowNumber = 2
                    elif stage == u"II":
                        rowNumber = 1
                    elif stage == u"I":
                        rowNumber = 0
                    else:
                        rowNumber = 4
                else:
                    rowNumber = 4
            matrica[forceString(rowNumber)][forceString(colNumberByMKB)] += 1
            matrica[u'5'][forceString(colNumberByMKB)] += 1

        for stringNumber in dict_stage.keys():
            matrica[stringNumber][u'0'] = sum([ matrica[stringNumber][x] if x not in (u'26', u'27', u'28') else 0 for x in matrica[stringNumber].keys()])
            matrica[stringNumber][u'26'] = sum([ matrica[stringNumber][x] if x in (u'26', u'27', u'28') else 0 for x in matrica[stringNumber].keys()])

        doc += u"<tr> "
        doc += u""" <td rowspan="6"></td> """
        doc += forceString(self.getCellsInRow(matrica[u'0'], dict_stage[u'0']))
        doc += u"</tr>"

        for stringNumber in range(1,6):
            doc += u"<tr>" + forceString(self.getCellsInRow(matrica[forceString(stringNumber)], dict_stage[forceString(stringNumber)])) + u"</tr>"

        doc += u"""</table>
        </body>
        </html>
        """

        return doc



    def getSetupDialog(self, parent):
        result = CReportOnkoByStagesDialog(parent)
        result.setTitle(self.title())
        return result



class CReportOnkoByStagesDialog(CDialogBase):
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

        self.cmbArea = CAreaComboBox(self)
        self.chkExistsOnDispanserCheckUp = QtGui.QCheckBox(
            u'Состоит на ДН на текущую дату по диагнозу')
        self.cmbSocStatusType = CRBComboBox(self)
        self.cmbSocStatusType.setTable('rbSocStatusType')

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
        self.layout.addWidget(QtGui.QLabel(u'Участок'), 6, 0, 1, 1)
        self.layout.addWidget(self.cmbArea, 6, 1, 1, 4)
        self.layout.addWidget(self.chkExistsOnDispanserCheckUp, 7, 0, 1, 4)
        self.layout.addWidget(QtGui.QLabel(u'Соц. статус'), 8, 0, 1, 1)
        self.layout.addWidget(self.cmbSocStatusType, 8, 1, 1, 4)

        self.layout.addWidget(self.buttonBox, 9, 3, 1, 2)


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
        result['area_id'] = self.cmbArea.value()
        result['socStatusType_id'] = self.cmbSocStatusType.value()
        result['isDispanserCheckUp'] = self.chkExistsOnDispanserCheckUp.isChecked()
        result['ageBeg'] = self.ageBeg.value()
        result['ageEnd'] = self.ageEnd.value()
        return result
