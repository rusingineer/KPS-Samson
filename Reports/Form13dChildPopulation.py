# -*- coding: utf-8 -*-
################################################################

from PyQt4 import QtGui, Qt
from PyQt4.QtCore import QDate

from library.Utils      import forceBool, forceInt, forceString

from Orgs.Utils         import getOrgStructureDescendants, getOrgStructures,  getOrgStructureFullName
from Reports.Report     import CReport
# from Reports.ReportBase import CReportBase, createTable
from PyQt4 import QtGui, QtCore
from library.DateEdit import CDateEdit
from Orgs.OrgStructComboBoxes import CAreaComboBox
from Orgs.Utils import getOrgStructureName, getOrgStructureDescendants, getOrganisationShortName
from library.DialogBase import CDialogBase



class CForm13dChildPopulation(CReport):
    name = u'Характеристика детского населения (приписанное население и обслуживаемые организации)'
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(self.name)


    def sortChildrenBySocStatus(self, listOfChildren):

        children_boy = 0
        children_girl = 0
        teenagers = 0
        teenagers_work = 0
        children_LUD = 0
        children_benefits = 0
        children_benefits_federation = 0
        children_benefits_territorial = 0
        children_work = 0
        children_not_work = 0
        children_student = 0
        children_PTU = 0
        children_school = 0
        children_sadik = 0
        children_baby = 0
        for rec in listOfChildren:
            sex = forceString(rec.value('sex'))
            age = forceInt(rec.value('age'))
            SocStatusType_row = forceString(rec.value('socStatusType_code'))
            SocStatusClass_row = forceString(rec.value('socStatusClass_code'))
            LUD = forceString(rec.value('LUD'))

            if sex == u'1':
                children_boy += 1
            else:
                children_girl += 1

            if age >= 15 and age <= 17:
                teenagers += 1
                if u'с05' in SocStatusType_row:
                    teenagers_work += 1

            if LUD and LUD != u"":
                children_LUD += 1

            is_federal = 0
            is_local = 0

            for item in SocStatusClass_row.split(u';'):
                if u'федеральный' in item.lower() and is_federal != 1:
                    is_federal = 1
                    children_benefits_federation += 1
                if (u'муниципальный' in item.lower() or u'субъект' in item.lower()) and is_local != 1:
                    is_local = 1
                    children_benefits_territorial += 1

            children_benefits = children_benefits_federation + children_benefits_territorial

            if SocStatusType_row and SocStatusType_row != u'':
                if u'с01' in SocStatusType_row:
                    children_baby += 1
                if u'с02' in SocStatusType_row:
                    children_sadik += 1
                if u'с03' in SocStatusType_row:
                    children_PTU += 1
                if u'с04' in SocStatusType_row:
                    children_student += 1
                if u'с05' in SocStatusType_row:
                    children_work += 1
                if u'с06' in SocStatusType_row:
                    children_not_work += 1
                if u'с25' in SocStatusType_row:
                    children_school += 1






        return children_boy, children_girl, teenagers, teenagers_work, children_LUD, children_benefits,\
         children_benefits_federation, children_benefits_territorial, children_work, children_not_work,\
         children_student, children_PTU, children_school, children_sadik, children_baby


    def build(self, params=None):
        db = QtGui.qApp.db
        children_all = 0
        children_boy = 0
        children_girl = 0
        teenagers = 0
        teenagers_work = 0
        children_LUD = 0
        children_benefits = 0
        children_benefits_federation = 0
        children_benefits_territorial = 0
        children_work = 0
        children_not_work = 0
        children_student = 0
        children_PTU = 0
        children_school = 0
        children_sadik = 0
        children_baby = 0
        uchastok = forceString(params.get('cmbOrgStructure', None))
        temp_query = db.query(u'SELECT organisation_id from OrgStructure where id = ' + uchastok)
        organisationId = None
        if temp_query.first():
            organisationId = forceString(temp_query.record().value(0).toString())
        organisationShortName = None
        if organisationId:
            temp_query = db.query(u'Select shortName from Organisation where id = ' + forceString(organisationId))
            if temp_query.first():
                organisationShortName = forceString(temp_query.record().value(0).toString())
        uchastok_name = forceString(params.get('cmbOrgStructureText') )
        needDate = forceString(params.get('dateReport', None))
        convertDate = u'-'.join(needDate.split(u'.')[::-1])
        list_orgStructures_id = getOrgStructureDescendants(forceInt(uchastok))
        stroka_orgStructuresID = u','.join(forceString(elem) for elem in list_orgStructures_id)
        mainSqlRequest = u" SELECT age(c.birthDate, ' " + forceString(convertDate) + u"""') AS age, c.id, c.birthDate, c.sex , 
        COALESCE(GROUP_CONCAT(concat_ws('|',sst.regionalCode, sst.name) SEPARATOR ';'),'' ) as socStatusType_code,
        COALESCE(GROUP_CONCAT(concat_ws('|', ssc.code, ssc.name) SEPARATOR ';'),'') as socStatusClass_code,
        COALESCE(GROUP_CONCAT(  d.MKB SEPARATOR ';'),'') as LUD
        FROM  Client c
        LEFT JOIN ClientAttach ca ON ca.client_id = c.id AND ca.deleted = 0
        LEFT JOIN ClientSocStatus css ON css.client_id = c.id AND css.deleted = 0
        LEFT JOIN rbSocStatusType sst ON sst.id = css.socStatusType_id
        LEFT JOIN rbSocStatusClass ssc ON ssc.id = css.socStatusClass_id
        LEFT JOIN Diagnosis d ON d.client_id = c.id AND d.deleted = 0 AND (  (d.endDate is null OR d.endDate <= ' """
        mainSqlRequest += forceString(convertDate) + u"' ) AND d.dispanser_id is not null) "
        mainSqlRequest += u" WHERE c.deleted = 0  AND  (ca.begDate <= '" + forceString(convertDate) + u"' AND (ca.endDate >= '" + \
                          forceString(convertDate) + u"' OR ca.endDate is NULL) AND ca.orgStructure_id in ( " + forceString(stroka_orgStructuresID) + u"))"


        mainSqlRequest += u"AND age(c.birthDate, '" + forceString(convertDate) + u"') < 18  GROUP by c.id "
        rst_query = db.query(mainSqlRequest)
        results_request = []
        while rst_query.next():
            result_rec = rst_query.record()
            results_request.append(result_rec)
        children_all = len(results_request)
        children_boy, children_girl, teenagers, teenagers_work, children_LUD, children_benefits,\
        children_benefits_federation, children_benefits_territorial, children_work, children_not_work,\
        children_student, children_PTU, children_school, children_sadik,\
        children_baby = self.sortChildrenBySocStatus(results_request)



        return u"""
<!DOCTYPE html>
<head>{setPageSize('A4')} {setOrientation('P')} {setLeftMargin(5)} {setTopMargin(5)} {setBottomMargin(5)} {setRightMargin(5)}</head>
<body>  

<p style=" width: 100%; font-weight: bold; font-size: 11pt;" align="right">Форма Ф-13Д</p>
<br>
<p style="font-size: 10pt;" align="center"> {organisationShortName} </p>
<p style="margin: 0 0 10px; font-size: 12pt; font-style: italic; text-transform: uppercase; font-weight: bold;" align="center">ХАРАКТЕРИСТИКА ДЕТСКОГО НАСЕЛЕНИЯ</p>
<p style="margin: 0 0 7px; text-transform: lowercase; font-size: 12pt; font-style: italic; font-weight: bold;" align="center">(приписанное население и обслуживаемые организации)</p>
<p style="margin: 0 0 7px; font-size: 9pt; font-weight: bold; " align="center">Участок: {uchastok_name} </p>
<p style="margin: 0; font-size: 9pt;  font-weight: bold; " align="center">на {needDate} </p>

<br>
<br>
<br>

<table width="100%" border="1"  cellspacing="0" cellspacing="0">
    <tr>
        <th><p style="font-size: 11pt; text-align: center; font-weight: bold;">Показатель</p></th>
        <th><p style="font-size: 11pt; text-align: center; font-weight: bold;">Количество</p></th>
    </tr>
    <tr>
        <td width="50%" style= " padding-right: 3px;  font-size: 10pt; font-weight: bold;" align="right">Численность населения</td>
        <td width="50%" style= " font-size: 10pt;" align="center">&nbsp;</td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; padding-right: 10px;" align="right">Всего</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {children_all} </td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; padding-right: 10px; " align="right">Мальчиков</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {children_boy} </td>
    </tr>
    <tr><td width="50%" style= " font-size: 10pt; padding-right: 10px; " align="right">Девочек</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {children_girl} </td></tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; font-weight: bold; padding-right: 3px;" align="right">Число подростков</td>
        <td width="50%" style= " font-size: 10pt;" align="center">&nbsp;</td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; padding-right: 10px; " align="right">всего</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {teenagers} </td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; padding-right: 10px; " align="right">работающих</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {teenagers_work} </td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; font-weight: bold; padding-right: 3px;" align="right">Число диспансерных</td>
        <td width="50%" style= " font-size: 10pt;" align="center">&nbsp;</td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; padding-right: 10px; " align="right">всего</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {children_LUD} </td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; font-weight: bold; padding-right: 3px;" align="right">Число льготников</td>
        <td width="50%" style= " font-size: 10pt;" align="center">&nbsp;</td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; padding-right: 10px; " align="right">всего</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {children_benefits} </td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; padding-right: 10px; " align="right">федеральных</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {children_benefits_federation} </td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; padding-right: 10px; " align="right">территориальных</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {children_benefits_territorial} </td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; font-weight: bold; padding-right: 3px;" align="right">Социальное положение</td>
        <td width="50%" style= " font-size: 10pt;" align="center">&nbsp;</td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; padding-right: 10px; " align="right">работает</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {children_work} </td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; padding-right: 10px; " align="right">не работает/учиться</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {children_not_work} </td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; padding-right: 10px; " align="right">студент (ВУЗА/Техникума)</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {children_student} </td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; padding-right: 10px; " align="right">Учащийся ПТУ</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {children_PTU} </td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; padding-right: 10px; " align="right">учащийся школы</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {children_school} </td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; padding-right: 10px;" align="right">дошкольник организованный</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {children_sadik} </td>
    </tr>
    <tr>
        <td width="50%" style= " font-size: 10pt; padding-right: 10px;" align="right">дошкольник неорганизованный</td>
        <td width="50%" style= " font-size: 10pt;" align="center"> {children_baby} </td>
    </tr>
</table>


</body>
</html>

        """.replace(u'{organisationShortName}',
     forceString(organisationShortName)).replace(u'{uchastok_name}',
     forceString(uchastok_name)).replace(u'{needDate}',
     forceString(needDate)).replace(u"{children_all}",
     forceString(children_all)).replace(u"{children_boy}",
     forceString(children_boy)).replace(u"{children_girl}",
     forceString(children_girl)).replace(u"{teenagers}",
     forceString(teenagers)).replace(u"{teenagers_work}",
     forceString(teenagers_work)).replace(u"{children_LUD}",
     forceString(children_LUD)).replace(u"{children_benefits}",
     forceString(children_benefits)).replace(u"{children_benefits_federation}",
     forceString(children_benefits_federation)).replace(u"{children_benefits_territorial}",
     forceString(children_benefits_territorial)).replace(u"{children_work}",
     forceString(children_work)).replace(u"{children_not_work}",
     forceString(children_not_work)).replace(u"{children_student}",
     forceString(children_student)).replace(u"{children_PTU}",
     forceString(children_PTU)).replace(u"{children_school}",
     forceString(children_school)).replace(u"{children_sadik}",
     forceString(children_sadik)).replace(u"{children_baby}",
     forceString(children_baby))



    def getSetupDialog(self, parent):
        result = CForm13dChildPopulationDialog(parent)
        result.setTitle(self.title())


        return result



class CForm13dChildPopulationDialog(CDialogBase):

    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        # self.diag = QtGui.QDialog()
        # self.layout_2 = QtGui.QGridLayout()
        self.layout = QtGui.QGridLayout(self) # self.layout_2
        self.cmbOrgStructure = CAreaComboBox(self)
        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.dateReport = CDateEdit()
        self.setWindowTitle(u'Выберите участок')
        self.layout.addWidget(QtGui.QLabel(u'Прикрепление к участку'), 0, 0, 1, 1)
        self.layout.addWidget(self.cmbOrgStructure, 0, 1, 1, 4)
        self.layout.addWidget(QtGui.QLabel(u'На дату'), 1, 0, 1, 1)
        self.layout.addWidget(self.dateReport, 1, 1, 1, 4)
        self.layout.addWidget(self.buttonBox, 2, 3, 1, 2)
        # self.diag.setWindowFlags(self.diag.windowFlags() & ~ QtCore.Qt.WindowContextHelpButtonHint)



    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        #     TODO
        pass

    def params(self):
        result = {}
        result['cmbOrgStructure'] = self.cmbOrgStructure.value()
        result['dateReport'] = self.dateReport.date()
        result['cmbOrgStructureText'] = self.cmbOrgStructure.currentText()
        return result



