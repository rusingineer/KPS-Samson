# -*- coding: utf-8 -*-
################################################################

from PyQt4 import QtGui, Qt, QtCore
from PyQt4.QtCore import QDate

from library.Utils      import forceBool, forceInt, forceString

from Orgs.Utils         import getOrgStructureDescendants, getOrgStructures,  getOrgStructureFullName
from Reports.Report     import CReport

from library.DateEdit import CDateEdit
from Orgs.OrgStructComboBoxes import CAreaComboBox
from Orgs.Utils import getOrgStructureName, getOrgStructureDescendants, getOrganisationShortName
from library.DialogBase import CDialogBase





class CForm25dNumberChildrenByAgeAndSocStatus(CReport):
    name = u'Численность детского населения по возрастному составу в разрезе социального пооложения Ф-25д'
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(self.name)


    def getTableLine(self, name, all, category1, category2, category3, category4, category5, category25):

        allChildrenUncategory = len(all)
        tableLine = u"""
        <tr>
            <td>
                <p style="text-align: left; font-size: 9pt; margin-left:5px;" width="23%">{tableLineName}</p>
            </td>
            <td>
                <p style="  font-size: 9pt;" align="center" width="8%">{allChildrenUncategory}</p>
            </td>
            <td>
                <p style="  font-size: 9pt;" align="center" width="12%">{category1}</p>
            </td>
            <td>
                <p style="  font-size: 9pt;" align="center" width="12%">{category2}</p>
            </td>
            <td>
                <p style="  font-size: 9pt;" align="center" width="12%">{category25}</p>
            </td>
            <td>
                <p style="  font-size: 9pt;" align="center" width="12%">{category3}</p>
            </td>
            <td>
                <p style="  font-size: 9pt;" align="center" width="9%">{category4}</p>
            </td>
            <td>
                <p style="  font-size: 9pt;" align="center" width="12%">{category5}</p>
            </td>
        </tr>
        """.replace(u"{tableLineName}",
            forceString(name)).replace(u"{allChildrenUncategory}",
            forceString(allChildrenUncategory)).replace(u"{category1}",
            forceString(category1)).replace(u"{category2}",
            forceString(category2)).replace(u"{category25}",
            forceString(category25)).replace(u"{category3}",
            forceString(category3)).replace(u"{category4}",
            forceString(category4)).replace(u"{category5}",
            forceString(category5))

        return tableLine

    def getTableLineResult(self, name, all, category1, category2, category3, category4, category5, category25):

        allChildrenUncategory = all
        tableLine = u"""
        <tr>
            <td>
                <p style="  font-size: 9pt; font-weight: bold; margin-right:3px;" align="right">{tableLineName}</p>
            </td>
            <td>
                <p style="  font-size: 9pt; font-weight: bold;" align="center">{allChildrenUncategory}</p>
            </td>
            <td>
                <p style="  font-size: 9pt; font-weight: bold;" align="center">{category1}</p>
            </td>
            <td>
                <p style="  font-size: 9pt; font-weight: bold;" align="center">{category2}</p>
            </td>
            <td>
                <p style="  font-size: 9pt; font-weight: bold;" align="center">{category25}</p>
            </td>
            <td>
                <p style="  font-size: 9pt; font-weight: bold;" align="center">{category3}</p>
            </td>
            <td>
                <p style="  font-size: 9pt; font-weight: bold;" align="center">{category4}</p>
            </td>
            <td>
                <p style="  font-size: 9pt; font-weight: bold;" align="center">{category5}</p>
            </td>
        </tr>
        """.replace(u"{tableLineName}",
            forceString(name)).replace(u"{allChildrenUncategory}",
            forceString(allChildrenUncategory)).replace(u"{category1}",
            forceString(category1)).replace(u"{category2}",
            forceString(category2)).replace(u"{category25}",
            forceString(category25)).replace(u"{category3}",
            forceString(category3)).replace(u"{category4}",
            forceString(category4)).replace(u"{category5}",
            forceString(category5))

        return tableLine


    def build(self, params):
        db = QtGui.qApp.db
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
        uchastok_name = forceString(params.get('cmbOrgStructureText'))
        needDate = forceString(params.get('dateReport', None))
        convertDate = u'-'.join(needDate.split(u'.')[::-1])
        attachCond = params.get('radio_chosen', None)
        title_living_place_and_statement = params.get('radio_title', None)
        list_orgStructures_id = getOrgStructureDescendants(forceInt(uchastok))
        stroka_orgStructuresID = u','.join(forceString(elem) for elem in list_orgStructures_id)


        mainSqlRequest = u" SELECT age(c.birthDate, '" + forceString(convertDate) + u"') AS age, "
        mainSqlRequest += u" c.id, c.birthDate, c.sex , "
        mainSqlRequest += u""" COALESCE(GROUP_CONCAT(concat_ws('|',sst.regionalCode, sst.name) SEPARATOR ';'),'' ) as socStatusType_code 
        FROM  Client c
        LEFT JOIN ClientAttach ca ON ca.client_id = c.id AND ca.deleted = 0 
        LEFT JOIN ClientSocStatus css ON css.client_id = c.id AND css.deleted = 0
        LEFT JOIN rbSocStatusType sst ON sst.id = css.socStatusType_id
        WHERE c.deleted = 0 """
        mainSqlRequest += u" AND  (ca.begDate <= '" + forceString(convertDate) + u"' AND (ca.endDate >= '" + forceString(convertDate) + u"' OR ca.endDate is NULL) AND ca.orgStructure_id in (" + forceString(stroka_orgStructuresID) + u") AND ca.attachType_id in " + attachCond + u" ) "
        mainSqlRequest += u" AND age(c.birthDate, '" + forceString(convertDate) + u"') < 18 GROUP by c.id "
        rst_query = db.query(mainSqlRequest)
        results_request = []
        while rst_query.next():
            result_rec = rst_query.record()
            results_request.append(result_rec)
        less_1, less_2_more_1, less_3_more_2, less_4_more_3, less_5_more_4, less_6_more_5, less_7_more_6,\
        less_8_more_7, less_9_more_8, less_10_more_9, less_11_more_10, less_12_more_11,\
        less_13_more_12, less_14_more_13, less_15_more_14,\
        less_16_more_15, less_17_more_16, less_18_more_17 = [[] for _ in range(18)]

        for rec in results_request:
            age = forceInt(rec.value('age'))
            if age < 1:
                less_1.append(rec)
            if age >= 1 and age < 2:
                less_2_more_1.append(rec)
            if age >= 2 and age < 3:
                less_3_more_2.append(rec)
            if age >= 3 and age < 4:
                less_4_more_3.append(rec)
            if age >= 4 and age < 5:
                less_5_more_4.append(rec)
            if age >= 5 and age < 6:
                less_6_more_5.append(rec)
            if age >= 6 and age < 7:
                less_7_more_6.append(rec)
            if age >= 7 and age < 8:
                less_8_more_7.append(rec)
            if age >= 8 and age < 9:
                less_9_more_8.append(rec)
            if age >= 9 and age < 10:
                less_10_more_9.append(rec)
            if age >= 10 and age < 11:
                less_11_more_10.append(rec)
            if age >= 11 and age < 12:
                less_12_more_11.append(rec)
            if age >= 12 and age < 13:
                less_13_more_12.append(rec)
            if age >= 13 and age < 14:
                less_14_more_13.append(rec)
            if age >= 14 and age < 15:
                less_15_more_14.append(rec)
            if age >= 15 and age < 16:
                less_16_more_15.append(rec)
            if age >= 16 and age < 17:
                less_17_more_16.append(rec)
            if age >= 17 and age < 18:
                less_18_more_17.append(rec)

        less_1_c01, less_1_c02, less_1_c03, less_1_c04, less_1_c05,\
        less_1_c25 = self.countChildrenSortByAgeAndSocStatus(less_1)
        tableLine_less_1 = self.getTableLine(u"До 1 года", less_1, less_1_c01, less_1_c02, less_1_c03,
                                             less_1_c04, less_1_c05, less_1_c25)

        less_2_more_1_c01, less_2_more_1_c02, less_2_more_1_c03, less_2_more_1_c04,\
        less_2_more_1_c05, less_2_more_1_c25 = self.countChildrenSortByAgeAndSocStatus(less_2_more_1)
        tableLine_less_2_more_1 = self.getTableLine(u"От 1 до 1л 11м 29д", less_2_more_1,
                            less_2_more_1_c01, less_2_more_1_c02, less_2_more_1_c03, less_2_more_1_c04,
                            less_2_more_1_c05, less_2_more_1_c25)

        less_3_more_2_c01, less_3_more_2_c02, less_3_more_2_c03, less_3_more_2_c04, \
        less_3_more_2_c05, less_3_more_2_c25 = self.countChildrenSortByAgeAndSocStatus(less_3_more_2)
        tableLine_less_3_more_2 = self.getTableLine(u"От 2 до 2л 11м 29д", less_3_more_2, less_3_more_2_c01,
                    less_3_more_2_c02, less_3_more_2_c03, less_3_more_2_c04, less_3_more_2_c05, less_3_more_2_c25)

        less_4_more_3_c01, less_4_more_3_c02, less_4_more_3_c03, less_4_more_3_c04,\
        less_4_more_3_c05, less_4_more_3_c25 = self.countChildrenSortByAgeAndSocStatus(less_4_more_3)
        tableLine_less_4_more_3 = self.getTableLine(u"От 3 до 3л 11м 29д", less_4_more_3, less_4_more_3_c01,
                less_4_more_3_c02, less_4_more_3_c03, less_4_more_3_c04, less_4_more_3_c05, less_4_more_3_c25)

        less_5_more_4_c01, less_5_more_4_c02, less_5_more_4_c03, less_5_more_4_c04,\
        less_5_more_4_c05, less_5_more_4_c25 = self.countChildrenSortByAgeAndSocStatus(less_5_more_4)
        tableLine_less_5_more_4 = self.getTableLine(u"От 4 до 4л 11м 29д", less_5_more_4, less_5_more_4_c01,
                less_5_more_4_c02, less_5_more_4_c03, less_5_more_4_c04, less_5_more_4_c05, less_5_more_4_c25)

        less_6_more_5_c01, less_6_more_5_c02, less_6_more_5_c03, less_6_more_5_c04,\
        less_6_more_5_c05, less_6_more_5_c25 = self.countChildrenSortByAgeAndSocStatus(less_6_more_5)
        tableLine_less_6_more_5 = self.getTableLine(u"От 5 до 5л 11м 29д", less_6_more_5, less_6_more_5_c01,
                less_6_more_5_c02, less_6_more_5_c03, less_6_more_5_c04, less_6_more_5_c05, less_6_more_5_c25)

        less_7_more_6_c01, less_7_more_6_c02, less_7_more_6_c03, less_7_more_6_c04,\
        less_7_more_6_c05, less_7_more_6_c25 = self.countChildrenSortByAgeAndSocStatus(less_7_more_6)
        tableLine_less_7_more_6 = self.getTableLine(u"От 6 до 6л 11м 29д", less_7_more_6,  less_7_more_6_c01,
                less_7_more_6_c02, less_7_more_6_c03, less_7_more_6_c04, less_7_more_6_c05, less_7_more_6_c25)

        less_8_more_7_c01, less_8_more_7_c02, less_8_more_7_c03, less_8_more_7_c04,\
        less_8_more_7_c05, less_8_more_7_c25 = self.countChildrenSortByAgeAndSocStatus(less_8_more_7)
        tableLine_less_8_more_7 = self.getTableLine(u"От 7 до 7л 11м 29д", less_8_more_7, less_8_more_7_c01,
                less_8_more_7_c02, less_8_more_7_c03, less_8_more_7_c04, less_8_more_7_c05, less_8_more_7_c25)

        less_9_more_8_c01, less_9_more_8_c02, less_9_more_8_c03, less_9_more_8_c04,\
        less_9_more_8_c05, less_9_more_8_c25 = self.countChildrenSortByAgeAndSocStatus(less_9_more_8)
        tableLine_less_9_more_8 = self.getTableLine(u"От 8 до 8л 11м 29д", less_9_more_8, less_9_more_8_c01,
                less_9_more_8_c02, less_9_more_8_c03, less_9_more_8_c04, less_9_more_8_c05, less_9_more_8_c25)

        less_10_more_9_c01, less_10_more_9_c02, less_10_more_9_c03, less_10_more_9_c04,\
        less_10_more_9_c05, less_10_more_9_c25 = self.countChildrenSortByAgeAndSocStatus(less_10_more_9)
        tableLine_less_10_more_9 = self.getTableLine(u"От 9 до 9л 11м 29д", less_10_more_9, less_10_more_9_c01,
                 less_10_more_9_c02, less_10_more_9_c03, less_10_more_9_c04, less_10_more_9_c05, less_10_more_9_c25)

        less_11_more_10_c01, less_11_more_10_c02, less_11_more_10_c03, less_11_more_10_c04,\
        less_11_more_10_c05, less_11_more_10_c25 = self.countChildrenSortByAgeAndSocStatus(less_11_more_10)
        tableLine_less_11_more_10 = self.getTableLine(u"От 10 до 10л 11м 29д", less_11_more_10, less_11_more_10_c01,
                  less_11_more_10_c02, less_11_more_10_c03, less_11_more_10_c04, less_11_more_10_c05, less_11_more_10_c25)

        less_12_more_11_c01, less_12_more_11_c02, less_12_more_11_c03, less_12_more_11_c04,\
        less_12_more_11_c05, less_12_more_11_c25 = self.countChildrenSortByAgeAndSocStatus(less_12_more_11)
        tableLine_less_12_more_11 = self.getTableLine(u"От 11 до 11л 11м 29д", less_12_more_11, less_12_more_11_c01,
                  less_12_more_11_c02, less_12_more_11_c03, less_12_more_11_c04, less_12_more_11_c05, less_12_more_11_c25)

        less_13_more_12_c01, less_13_more_12_c02, less_13_more_12_c03, less_13_more_12_c04,\
        less_13_more_12_c05, less_13_more_12_c25 = self.countChildrenSortByAgeAndSocStatus(less_13_more_12)
        tableLine_less_13_more_12 = self.getTableLine(u"От 12 до 12л 11м 29д", less_13_more_12, less_13_more_12_c01,
                  less_13_more_12_c02, less_13_more_12_c03, less_13_more_12_c04, less_13_more_12_c05, less_13_more_12_c25)

        less_14_more_13_c01, less_14_more_13_c02, less_14_more_13_c03, less_14_more_13_c04,\
        less_14_more_13_c05, less_14_more_13_c25 = self.countChildrenSortByAgeAndSocStatus(less_14_more_13)
        tableLine_less_14_more_13 = self.getTableLine(u"От 13 до 13л 11м 29д", less_14_more_13, less_14_more_13_c01,
                  less_14_more_13_c02, less_14_more_13_c03, less_14_more_13_c04, less_14_more_13_c05, less_14_more_13_c25)

        less_15_more_14_c01, less_15_more_14_c02, less_15_more_14_c03, less_15_more_14_c04,\
        less_15_more_14_c05, less_15_more_14_c25 = self.countChildrenSortByAgeAndSocStatus(less_15_more_14)
        tableLine_less_15_more_14 = self.getTableLine(u"От 14 до 14л 11м 29д", less_15_more_14, less_15_more_14_c01,
                  less_15_more_14_c02, less_15_more_14_c03, less_15_more_14_c04, less_15_more_14_c05, less_15_more_14_c25)

        less_16_more_15_c01, less_16_more_15_c02, less_16_more_15_c03, less_16_more_15_c04,\
        less_16_more_15_c05, less_16_more_15_c25 = self.countChildrenSortByAgeAndSocStatus(less_16_more_15)
        tableLine_less_16_more_15 = self.getTableLine(u"От 15 до 15л 11м 29д", less_16_more_15, less_16_more_15_c01,
                  less_16_more_15_c02, less_16_more_15_c03, less_16_more_15_c04, less_16_more_15_c05, less_16_more_15_c25)

        less_17_more_16_c01, less_17_more_16_c02, less_17_more_16_c03, less_17_more_16_c04,\
        less_17_more_16_c05, less_17_more_16_c25 = self.countChildrenSortByAgeAndSocStatus(less_17_more_16)
        tableLine_less_17_more_16 = self.getTableLine(u"От 16 до 16л 11м 29д", less_17_more_16, less_17_more_16_c01,
                  less_17_more_16_c02, less_17_more_16_c03, less_17_more_16_c04, less_17_more_16_c05, less_17_more_16_c25)

        less_18_more_17_c01, less_18_more_17_c02, less_18_more_17_c03, less_18_more_17_c04,\
        less_18_more_17_c05, less_18_more_17_c25 = self.countChildrenSortByAgeAndSocStatus(less_18_more_17)
        tableLine_less_18_more_17 = self.getTableLine(u"От 17 до 17л 11м 29д", less_18_more_17, less_18_more_17_c01,
                  less_18_more_17_c02, less_18_more_17_c03, less_18_more_17_c04, less_18_more_17_c05, less_18_more_17_c25)

        doc = u"""
        <!DOCTYPE html>
<head>{setPageSize('A4')} {setOrientation('P')} {setLeftMargin(5)} {setTopMargin(5)} {setBottomMargin(5)} {setRightMargin(5)}</head>
<body>  
<p style=" width: 100%; font-weight: bold; font-size: 11pt;" align="right">Форма Ф-25Д</p>
<br>
<p style="font-size: 10pt;" align="center">{organisationShortName}</p>
<p style="margin: 0;  font-size: 12pt; font-style: italic; font-weight: bold;" align="center">Численность детского населения</p>
<p style="margin: 0; text-transform: lowercase; font-size: 12pt; font-style: italic; font-weight: bold;" align="center">по возрастному составу</p>
<p style="margin: 0 0 7px; text-transform: lowercase; font-size: 12pt; font-style: italic; font-weight: bold;" align="center">в разрезе социального положения</p>
<p style="margin: 0 0 10px; font-size: 12pt; font-style: italic; text-transform: uppercase; font-weight: bold;" align="center">{title_living_place_and_statement}</p>
<p style="margin: 0; font-size: 9pt;  font-weight: bold; " align="center">на {needDate}</p>
<p style="margin: 0 0 7px; font-size: 9pt; font-weight: bold; " align="center">По участку: {uchastok_name}</p>
<br>
<br>
<br>
<table width="100%" border="1"  cellspacing="0" cellspacing="0">
    <tr>
        <td rowspan="2"> <p style="font-size: 9pt;   font-weight: bold; vertical-align: middle;" align="center">Возраст</p> </td>
        <td rowspan="2" style="padding: 5px;"> <p style="font-size: 9pt;   font-weight: bold; vertical-align: middle;" align="center">Всего</p> </td>
        <td colspan="6" width="75%"> <p style="font-size: 9pt;   font-weight: bold; vertical-align: middle;" align="center">В разрезе социального положения</p> </td>
        
    </tr>
    <tr>
        <td ><p style="font-size: 9pt;   font-weight: bold; vertical-align: middle;" align="center">Дошкольники неорганизо-ванные</p></td>
        <td ><p style="font-size: 9pt;   font-weight: bold; vertical-align: middle;" align="center">Дошкольники организован-ные (ясли/сад)</p></td>
        <td ><p style="font-size: 9pt;   font-weight: bold; vertical-align: middle;" align="center">Учащиеся школ, лицеев, гимназий</p></td>
        <td ><p style="font-size: 9pt;   font-weight: bold; vertical-align: middle;" align="center">Учащиеся техникумов, колледжей, ПТУ</p></td>
        <td ><p style="font-size: 9pt;   font-weight: bold; vertical-align: middle;" align="center">Студенты ВУЗов</p></td>
        <td style="padding: 5px;"><p style="font-size: 9pt;   font-weight: bold; vertical-align: middle;" align="center">Работающие</p></td>        
    </tr>
    
    
        """.replace(u"{organisationShortName}",
forceString(organisationShortName)).replace(u"{title_living_place_and_statement}",
forceString(title_living_place_and_statement)).replace(u"{needDate}",
forceString(needDate)).replace(u"{uchastok_name}",
forceString(uchastok_name))
        allChildren = len(less_1) + len(less_2_more_1) + len(less_3_more_2) + len(less_4_more_3) + \
            len(less_5_more_4) + len(less_6_more_5) + len(less_7_more_6) + len(less_8_more_7) + \
            len(less_9_more_8) + len(less_10_more_9) + len(less_11_more_10) + len(less_12_more_11) + \
            len(less_13_more_12) + len(less_14_more_13) + len(less_15_more_14) + len(less_16_more_15) + \
            len(less_17_more_16) + len(less_18_more_17)

        allChildren_c01 = less_1_c01 + less_2_more_1_c01 + less_3_more_2_c01 + less_4_more_3_c01 + \
                        less_5_more_4_c01 + less_6_more_5_c01 + less_7_more_6_c01 + less_8_more_7_c01 + \
                        less_9_more_8_c01 + less_10_more_9_c01 + less_11_more_10_c01 + less_12_more_11_c01 +\
                        less_13_more_12_c01 + less_14_more_13_c01 + less_15_more_14_c01 + less_16_more_15_c01 +\
                        less_17_more_16_c01 + less_18_more_17_c01

        allChildren_c02 = less_1_c02 + less_2_more_1_c02 + less_3_more_2_c02 + less_4_more_3_c02 + \
                          less_5_more_4_c02 + less_6_more_5_c02 + less_7_more_6_c02 + less_8_more_7_c02 + \
                          less_9_more_8_c02 + less_10_more_9_c02 + less_11_more_10_c02 + less_12_more_11_c02 + \
                          less_13_more_12_c02 + less_14_more_13_c02 + less_15_more_14_c02 + less_16_more_15_c02 + \
                          less_17_more_16_c02 + less_18_more_17_c02

        allChildren_c03 = less_1_c03 + less_2_more_1_c03 + less_3_more_2_c03 + less_4_more_3_c03 + \
                          less_5_more_4_c03 + less_6_more_5_c03 + less_7_more_6_c03 + less_8_more_7_c03 + \
                          less_9_more_8_c03 + less_10_more_9_c03 + less_11_more_10_c03 + less_12_more_11_c03 + \
                          less_13_more_12_c03 + less_14_more_13_c03 + less_15_more_14_c03 + less_16_more_15_c03 + \
                          less_17_more_16_c03 + less_18_more_17_c03

        allChildren_c04 = less_1_c04 + less_2_more_1_c04 + less_3_more_2_c04 + less_4_more_3_c04 + \
                          less_5_more_4_c04 + less_6_more_5_c04 + less_7_more_6_c04 + less_8_more_7_c04 + \
                          less_9_more_8_c04 + less_10_more_9_c04 + less_11_more_10_c04 + less_12_more_11_c04 + \
                          less_13_more_12_c04 + less_14_more_13_c04 + less_15_more_14_c04 + less_16_more_15_c04 + \
                          less_17_more_16_c04 + less_18_more_17_c04

        allChildren_c05 = less_1_c05 + less_2_more_1_c05 + less_3_more_2_c05 + less_4_more_3_c05 + \
                          less_5_more_4_c05 + less_6_more_5_c05 + less_7_more_6_c05 + less_8_more_7_c05 + \
                          less_9_more_8_c05 + less_10_more_9_c05 + less_11_more_10_c05 + less_12_more_11_c05 + \
                          less_13_more_12_c05 + less_14_more_13_c05 + less_15_more_14_c05 + less_16_more_15_c05 + \
                          less_17_more_16_c05 + less_18_more_17_c05

        allChildren_c25 = less_1_c25 + less_2_more_1_c25 + less_3_more_2_c25 + less_4_more_3_c25 + \
                          less_5_more_4_c25 + less_6_more_5_c25 + less_7_more_6_c25 + less_8_more_7_c25 + \
                          less_9_more_8_c25 + less_10_more_9_c25 + less_11_more_10_c25 + less_12_more_11_c25 + \
                          less_13_more_12_c25 + less_14_more_13_c25 + less_15_more_14_c25 + less_16_more_15_c25 + \
                          less_17_more_16_c25 + less_18_more_17_c25




        tableLineAmmount = self.getTableLineResult(u"ИТОГО", allChildren, allChildren_c01,allChildren_c02,
                                                   allChildren_c03, allChildren_c04, allChildren_c05, allChildren_c25 )

        doc += tableLine_less_1 + tableLine_less_2_more_1 + tableLine_less_3_more_2 + tableLine_less_4_more_3 + \
               tableLine_less_5_more_4 + tableLine_less_6_more_5 + tableLine_less_7_more_6 + \
               tableLine_less_8_more_7 + tableLine_less_9_more_8 + tableLine_less_10_more_9 + \
               tableLine_less_11_more_10 + tableLine_less_12_more_11 + tableLine_less_13_more_12 + \
               tableLine_less_14_more_13 + tableLine_less_15_more_14 + tableLine_less_16_more_15 + \
               tableLine_less_17_more_16 + tableLine_less_18_more_17 + tableLineAmmount

        doc += u"""
                </table>
            </body>
        </html>
        """

        return doc


    def countChildrenSortByAgeAndSocStatus(self, listOfChildren):
        category_c01, category_c02, category_c03, category_c04, category_c05, category_c25 = 0,0,0,0,0,0
        for children in listOfChildren:
            if u'с01' in forceString(children.value('socStatusType_code')):
                category_c01 += 1
            if u'с02' in forceString(children.value('socStatusType_code')):
                category_c02 += 1
            if u'с03' in forceString(children.value('socStatusType_code')):
                category_c03 += 1
            if u'с04' in forceString(children.value('socStatusType_code')):
                category_c04 += 1
            if u'с05' in forceString(children.value('socStatusType_code')):
                category_c05 += 1
            if u'с25' in forceString(children.value('socStatusType_code')):
                category_c25 += 1

        return category_c01, category_c02, category_c03, category_c04, category_c05, category_c25

    def getSetupDialog(self, parent):
        result = CForm25dNumberChildrenByAgeAndSocStatusDialog(parent)
        result.setTitle(self.title())
        return result

class CForm25dNumberChildrenByAgeAndSocStatusDialog(CDialogBase):

    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)

        self.layout = QtGui.QGridLayout(self)
        self.cmbOrgStructure = CAreaComboBox(self)
        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.dateReport = CDateEdit()

        self.groupbox = QtGui.QGroupBox(u"Численность населения")
        self.radio_living_place_and_statement = QtGui.QRadioButton(u"приписанного по месту жительства и заявлению")
        self.radio_living_place = QtGui.QRadioButton(u"приписанного только по месту жительства")
        self.radio_living_statement = QtGui.QRadioButton(u"приписанного только по заявлению")
        self.radio_living_place_and_statement.setChecked(True)

        self.groupLayout = QtGui.QVBoxLayout()
        self.groupLayout.addWidget(self.radio_living_place_and_statement)
        self.groupLayout.addWidget(self.radio_living_place)
        self.groupLayout.addWidget(self.radio_living_statement)
        self.groupbox.setLayout(self.groupLayout)


        self.setWindowTitle(u'Выберите участок')
        self.layout.addWidget(QtGui.QLabel(u'Прикрепление к участку'), 0, 0, 1, 1)
        self.layout.addWidget(self.cmbOrgStructure, 0, 1, 1, 4)
        self.layout.addWidget(QtGui.QLabel(u'На дату'), 1, 0, 1, 1)
        self.layout.addWidget(self.dateReport, 1, 1, 1, 4)
        self.layout.addWidget(self.groupbox, 2, 0, 1, 5)
        self.layout.addWidget(self.buttonBox, 3, 3, 1, 2)
        self.setWindowFlags(self.windowFlags() & ~ QtCore.Qt.WindowContextHelpButtonHint)



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
        radio_chosen = None
        title_living_place_and_statement = None
        if self.radio_living_place_and_statement.isChecked():
            radio_chosen = u" (select rat.id FROM rbAttachType rat WHERE rat.code in ('1', '2')) "
            title_living_place_and_statement = u"ПРИПИСАННОГО ПО МЕСТУ ЖИТЕЛЬСТВА И ЗАЯВЛЕНИЮ"
        if self.radio_living_place.isChecked():
            radio_chosen = u" (select rat.id FROM rbAttachType rat WHERE rat.code in ('1')) "
            title_living_place_and_statement = u"ПРИПИСАННОГО ТОЛЬКО ПО МЕСТУ ЖИТЕЛЬСТВА"
        if self.radio_living_statement.isChecked():
            radio_chosen = u" (select rat.id FROM rbAttachType rat WHERE rat.code in ('2')) "
            title_living_place_and_statement = u"ПРИПИСАННОГО ТОЛЬКО ПО ЗАЯВЛЕНИЮ"
        result['radio_chosen'] = radio_chosen
        result['radio_title'] = title_living_place_and_statement
        return result


