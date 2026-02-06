# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2015 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature
from datetime import datetime

from library.Utils import forceInt, forceString

from Ui_PlanningProfilactic import Ui_PlanningProfilactic


class CPlanningProfilactic(QtGui.QDialog, Ui_PlanningProfilactic):
    def __init__(self,  parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        currentDate = datetime.now()
        self.sbYear.setValue(currentDate.year)
        self.cmbMonthFrom.setCurrentIndex(currentDate.month)
        self.chkQuantityWorkAge.setVisible(False)
        self.cmbOrgStructure.setTable('OrgStructure')
        self.cmbOrgStructure.setFilter(u"""
            length(OrgStructure.bookkeeperCode) = 5
            and exists (
                select *
                from OrgStructure as Child1
                    left join OrgStructure as Child2 on Child2.parent_id = Child1.id
                    left join OrgStructure as Child3 on Child3.parent_id = Child2.id
                    left join OrgStructure as Child4 on Child4.parent_id = Child3.id
                    left join OrgStructure as Child5 on Child5.parent_id = Child4.id
                where Child1.parent_id = OrgStructure.id
                    and (Child1.areaType in (1, 2)
                        or Child2.areaType in (1, 2)
                        or Child3.areaType in (1, 2)
                        or Child4.areaType in (1, 2)
                        or Child5.areaType in (1, 2)
                    )
            )
            """
            )
        self.cmbOrgStructure.setNameField(u"concat(bookkeeperCode, ' - ', name)")
        self.cmbOrgStructure.setOrder(u"bookkeeperCode, name")
        self.cmbOrgStructure.setAddNone(True, u'все')
        self.cmbOrgStructure.setCurrentIndex(0)
    
    def start(self):
        try:
            QtGui.qApp.setWaitCursor()
            db = QtGui.qApp.db
            year = self.sbYear.value()
            monthFrom = self.cmbMonthFrom.currentIndex() + 1
            monthTo = self.cmbMonthTo.currentIndex() + 1
            addDisp3 = self.chkAddDisp3.isChecked()
            addDisp1 = self.chkAddDisp1.isChecked()
            addProf = self.chkAddProf.isChecked()
            covidPriority = self.chkCovidPriority.isChecked()
            kindList = []
            if addDisp3:
                kindList.append('1')
            if addProf:
                kindList.append('2')
            if addDisp1:
                kindList.append('4')
            if kindList:
                kindWhere = u"dpq.kind in (%s)" % ", ".join(kindList)
            else:
                QtGui.QMessageBox.information(self,
                                            u'Внимание!',
                                            u'Выберите тип профмероприятий!',
                                            QtGui.QMessageBox.Ok)
                return
            orgStructureId = self.cmbOrgStructure.value()
            if orgStructureId is None:
                codeMo = None
                codeMoWhere = u""
            else:
                codeMo = forceString(db.translate('OrgStructure', 'id', orgStructureId, 'bookkeeperCode'))
                codeMoWhere = u"and dpq.code_mo = '%s'" % codeMo
            if self.chkQuantityWorkAge.isChecked():
                stmt = u"""
                    select dpq.year,
                        dpq.mnth,
                        dpq.kind,
                        1 as Ability,
                        dpq.quantityAbility - (
                            SELECT COUNT(distinct Client.id)
                            FROM ClientSocStatus css
                                LEFT JOIN rbSocStatusClass ssc ON ssc.id = css.socStatusClass_id
                                LEFT JOIN rbSocStatusType sst ON sst.id = css.socStatusType_id
                                LEFT JOIN Client on Client.id = css.client_id
                                LEFT JOIN ClientAttach ON ClientAttach.id = (
                                    SELECT MAX(ca.id)
                                    FROM ClientAttach AS ca
                                        INNER JOIN rbAttachType on rbAttachType.id = ca.attachType_id and rbAttachType.code in ('1', '2')
                                        INNER JOIN OrgStructure o on o.id = ca.orgStructure_id
                                    WHERE ca.client_id = Client.id
                                        AND ca.deleted = 0
                                        AND ca.endDate IS NULL
                                        AND o.areaType > 0
                                )
                                LEFT JOIN OrgStructure ON OrgStructure.id = ClientAttach.orgStructure_id
                                LEFT JOIN OrgStructure AS Parent1 ON Parent1.id = OrgStructure.parent_id
                                LEFT JOIN OrgStructure AS Parent2 ON Parent2.id = Parent1.parent_id
                                LEFT JOIN OrgStructure AS Parent3 ON Parent3.id = Parent2.parent_id
                                LEFT JOIN OrgStructure AS Parent4 ON Parent4.id = Parent3.parent_id
                                LEFT JOIN OrgStructure AS Parent5 ON Parent5.id = Parent4.parent_id
                            WHERE (
                                    Client.sex = 1 and age(Client.birthDate, concat(cast(dpq.year as char(4)), '-', cast(dpq.mnth as char(2)), '-01')) < 60
                                    or Client.sex = 2 and age(Client.birthDate, concat(cast(dpq.year as char(4)), '-', cast(dpq.mnth as char(2)), '-01')) < 55
                                )
                                AND Client.deleted = 0
                                AND dpq.year - year(Client.birthDate) >= 18
                                AND ssc.code = 'profilac'
                                AND sst.code = (case dpq.kind
                                    when 1 then 'disp'
                                    when 2 then 'prof'
                                    when 4 then 'disp_1'
                                    when 5 then 'disp_cov1'
                                    when 6 then 'disp_cov2'
                                end)
                                AND css.deleted = 0
                                AND YEAR(css.begDate) = dpq.year
                                AND MONTH(css.begDate) = dpq.mnth
                                AND (
                                    OrgStructure.bookkeeperCode = dpq.code_mo
                                    OR Parent1.bookkeeperCode = dpq.code_mo
                                    OR Parent2.bookkeeperCode = dpq.code_mo
                                    OR Parent3.bookkeeperCode = dpq.code_mo
                                    OR Parent4.bookkeeperCode = dpq.code_mo
                                    OR Parent5.bookkeeperCode = dpq.code_mo
                                )
                        ) AS requeredCount
                    FROM disp_PlanQtys dpq
                    WHERE dpq.year = {year}
                        and dpq.mnth between {monthFrom} and {monthTo}
                        and {kindWhere}
                        {codeMoWhere}
                    HAVING requeredCount > 0
                    union all
                    select dpq.year,
                        dpq.mnth,
                        dpq.kind,
                        2 as Ability,
                        dpq.quantityNotAbility - (
                            SELECT COUNT(distinct Client.id)
                            FROM ClientSocStatus css
                                LEFT JOIN rbSocStatusClass ssc ON ssc.id = css.socStatusClass_id
                                LEFT JOIN rbSocStatusType sst ON sst.id = css.socStatusType_id
                                LEFT JOIN Client on Client.id = css.client_id
                                LEFT JOIN ClientAttach ON ClientAttach.id = (
                                    SELECT MAX(ca.id)
                                    FROM ClientAttach AS ca
                                        INNER JOIN rbAttachType on rbAttachType.id = ca.attachType_id and rbAttachType.code in ('1', '2')
                                        INNER JOIN OrgStructure o on o.id = ca.orgStructure_id
                                    WHERE ca.client_id = Client.id
                                        AND ca.deleted = 0
                                        AND ca.endDate IS NULL
                                        AND o.areaType > 0
                                )
                                LEFT JOIN OrgStructure ON OrgStructure.id = ClientAttach.orgStructure_id
                                LEFT JOIN OrgStructure AS Parent1 ON Parent1.id = OrgStructure.parent_id
                                LEFT JOIN OrgStructure AS Parent2 ON Parent2.id = Parent1.parent_id
                                LEFT JOIN OrgStructure AS Parent3 ON Parent3.id = Parent2.parent_id
                                LEFT JOIN OrgStructure AS Parent4 ON Parent4.id = Parent3.parent_id
                                LEFT JOIN OrgStructure AS Parent5 ON Parent5.id = Parent4.parent_id
                            WHERE (
                                    Client.sex = 1 and age(Client.birthDate, concat(cast(dpq.year as char(4)), '-', cast(dpq.mnth as char(2)), '-01')) >= 60
                                    or Client.sex = 2 and age(Client.birthDate, concat(cast(dpq.year as char(4)), '-', cast(dpq.mnth as char(2)), '-01')) >= 55
                                )
                                AND Client.deleted = 0
                                AND dpq.year - year(Client.birthDate) >= 18
                                AND ssc.code = 'profilac'
                                AND sst.code = (case dpq.kind
                                    when 1 then 'disp'
                                    when 2 then 'prof'
                                    when 4 then 'disp_1'
                                    when 5 then 'disp_cov1'
                                    when 6 then 'disp_cov2'
                                end)
                                AND css.deleted = 0
                                AND YEAR(css.begDate) = dpq.year
                                AND MONTH(css.begDate) = dpq.mnth
                                AND (
                                    OrgStructure.bookkeeperCode = dpq.code_mo
                                    OR Parent1.bookkeeperCode = dpq.code_mo
                                    OR Parent2.bookkeeperCode = dpq.code_mo
                                    OR Parent3.bookkeeperCode = dpq.code_mo
                                    OR Parent4.bookkeeperCode = dpq.code_mo
                                    OR Parent5.bookkeeperCode = dpq.code_mo
                                )
                        ) AS requeredCount
                    FROM disp_PlanQtys dpq
                    WHERE dpq.year = {year}
                        and dpq.mnth between {monthFrom} and {monthTo}
                        and {kindWhere}
                        {codeMoWhere}
                    HAVING requeredCount > 0;
                    """.format(year=year, monthFrom=monthFrom, monthTo=monthTo, kindWhere=kindWhere, codeMoWhere=codeMoWhere)
            else:
                stmt = u"""
                    select dpq.year,
                        dpq.mnth,
                        dpq.kind,
                        dpq.quantity - (
                            SELECT COUNT(distinct Client.id)
                            FROM ClientSocStatus css
                                LEFT JOIN rbSocStatusClass ssc ON ssc.id = css.socStatusClass_id
                                LEFT JOIN rbSocStatusType sst ON sst.id = css.socStatusType_id
                                LEFT JOIN Client ON Client.id = css.client_id
                                LEFT JOIN ClientAttach ON ClientAttach.id = (
                                    SELECT MAX(ca.id)
                                    FROM ClientAttach AS ca
                                        INNER JOIN rbAttachType on rbAttachType.id = ca.attachType_id and rbAttachType.code in ('1', '2')
                                        INNER JOIN OrgStructure o on o.id = ca.orgStructure_id
                                    WHERE ca.client_id = Client.id
                                        AND ca.deleted = 0
                                        AND ca.endDate IS NULL
                                        AND o.areaType > 0
                                )
                                LEFT JOIN OrgStructure ON OrgStructure.id = ClientAttach.orgStructure_id
                                LEFT JOIN OrgStructure AS Parent1 ON Parent1.id = OrgStructure.parent_id
                                LEFT JOIN OrgStructure AS Parent2 ON Parent2.id = Parent1.parent_id
                                LEFT JOIN OrgStructure AS Parent3 ON Parent3.id = Parent2.parent_id
                                LEFT JOIN OrgStructure AS Parent4 ON Parent4.id = Parent3.parent_id
                                LEFT JOIN OrgStructure AS Parent5 ON Parent5.id = Parent4.parent_id
                            WHERE Client.deleted = 0
                                AND dpq.year - year(Client.birthDate) >= 18
                                AND ssc.code = 'profilac'
                                AND sst.code = (case dpq.kind
                                    when 1 then 'disp'
                                    when 2 then 'prof'
                                    when 4 then 'disp_1'
                                    when 5 then 'disp_cov1'
                                    when 6 then 'disp_cov2'
                                end)
                                AND css.deleted = 0
                                AND YEAR(css.begDate) = dpq.year
                                AND MONTH(css.begDate) = dpq.mnth
                                AND (
                                    OrgStructure.bookkeeperCode = dpq.code_mo
                                    OR Parent1.bookkeeperCode = dpq.code_mo
                                    OR Parent2.bookkeeperCode = dpq.code_mo
                                    OR Parent3.bookkeeperCode = dpq.code_mo
                                    OR Parent4.bookkeeperCode = dpq.code_mo
                                    OR Parent5.bookkeeperCode = dpq.code_mo
                                )
                        ) AS requeredCount
                    FROM disp_PlanQtys dpq
                    WHERE dpq.year = {year}
                        and dpq.mnth between {monthFrom} and {monthTo}
                        and {kindWhere}
                        {codeMoWhere}
                    HAVING requeredCount > 0;
                    """.format(year=year, monthFrom=monthFrom, monthTo=monthTo, kindWhere=kindWhere, codeMoWhere=codeMoWhere)
            query = db.query(stmt)
            QtGui.qApp.restoreOverrideCursor()
            cnt = 0
            cntByKind = {1: 0, 2: 0, 4: 0}
            while query.next():
                record = query.record()
                kind = forceInt(record.value('kind'))
                requeredCount = forceInt(record.value('requeredCount'))
                cnt += requeredCount
                if kind in cntByKind:
                    cntByKind[kind] += requeredCount
            if cnt > 0:
                btns = QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Yes
            else:
                btns = QtGui.QMessageBox.Ok
            cntByKindMessages = []
            if addDisp3:
                cntByKindMessages.append(u'Диспансеризация раз в 3 года: %d' % cntByKind[1])
            if addDisp1:
                cntByKindMessages.append(u'Диспансеризация ежегодная: %d' % cntByKind[4])
            if addProf:
                cntByKindMessages.append(u'Профилактические осмотры: %d' % cntByKind[2])
            cntByKindJoinedMessage = "\n".join(cntByKindMessages)
            res = QtGui.QMessageBox.information(self,
                                                u'Внимание!',
                                                u'Подлежит планированию человек: {cnt}. Из них:\n{cntByKind}\nПродолжить?'.format(cnt=cnt, cntByKind=cntByKindJoinedMessage),
                                                btns)
            if res == QtGui.QMessageBox.Yes:
                QtGui.qApp.setWaitCursor()
                currentPersonId = QtGui.qApp.userId
                codeMoSql = u'null' if codeMo is None else u"'%s'" % codeMo
                if self.chkQuantityWorkAge.isChecked():
                    stmt = u"call updateProfilacticPlanAbility(%s, %d, %d, %d, %d, %d, %d, %d);" % (
                        codeMoSql, year, monthFrom, monthTo, addDisp3, addDisp1, addProf, currentPersonId
                    )
                else:
                    stmt = u"call updateProfilacticPlan(%s, %d, %d, %d, %d, %d, %d, %d, %d);" % (
                        codeMoSql, year, monthFrom, monthTo, addDisp3, addDisp1, addProf, currentPersonId, covidPriority
                    )
                message = u'Добавлено записей: %d'
                query = db.query(stmt)
                stmt = 'select @countInsertedRows as cnt;'
                query = db.query(stmt)
                cnt = 0
                QtGui.qApp.restoreOverrideCursor()
                if query.first():
                    record = query.record()
                    cnt = forceInt(record.value('cnt'))
                    QtGui.QMessageBox.information(self,
                                                    u'Планирование завершено',
                                                    message % cnt,
                                                    QtGui.QMessageBox.Ok)
        finally:
            QtGui.qApp.restoreOverrideCursor()
        

    @pyqtSignature('')
    def on_btnStart_clicked(self):
        self.start()
        
    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()