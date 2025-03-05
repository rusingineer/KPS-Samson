# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, Qt, QObject, SIGNAL, pyqtSignature
from PyQt4.QtGui import QAbstractItemView, QWidget, QAction

from Registry.RegistryTable import CClientEvalCol
from library.DialogBase import CConstructHelperMixin
from library.Calendar import monthName
from library.TableModel import CTableModel, CCol, CDateTimeCol, CDesignationCol, CEnumCol, CIntCol, CNameCol, CTextCol, CDateFixedCol
from library.Utils import forceStringEx, forceRef, formatRecordsCount, exceptionToUnicode, forceInt, forceString, toVariant

from Exchange.ExportDispPlanDialog import CExportDispPlanDialog
from Exchange.ImportDispFactInfosDialog import CImportDispFactInfosDialog
from Exchange.ImportDispFactInvcsDialog import CImportDispFactInvcsDialog
from Exchange.ImportDispPlanQtysDialog import CImportDispPlanQtysDialog
from Exchange.ExportDispContactsDialog import CExportDispContactsDialog
from Exchange.ExportDispPlanDatesDialog import CExportDispPlanDatesDialog
from Exchange.ImportDispExportedPlanDialog import CImportDispExportedPlanDialog

from Orgs.Utils import getOrgStructureDescendants

from Registry.ClientEditDialog import CClientEditDialog
from Registry.PlanningProfilactic import CPlanningProfilactic

from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CReportViewDialog, CPageFormat

from Users.Rights import urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry

from Ui_DispExchangeProfilacticPage import Ui_DispExchangeProfilacticPage


class CDispExchangeProfilacticPage(QWidget, Ui_DispExchangeProfilacticPage, CConstructHelperMixin):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.addModels('Clients', CClientsModel(self))
        self.addModels('PlanExportErrors', CPlanExportErrorsModel(self))
        self.addModels('FactInfos', CFactInfosModel(self))
        self.addModels('FactInvcs', CFactInvcsModel(self))
        self.addObject('actEditClient', QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actDispAdd', QAction(u'Запланировать мероприятие', self))
        self.addObject('actDispDel', QAction(u'Удалить планирование', self))
        self.setupUi(self)
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.actDispAdd.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.actDispDel.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        # self.tblClients.createPopupMenu([self.actEditClient])
        self.setModels(self.tblClients, self.modelClients, self.selectionModelClients)
        self.setModels(self.tblPlanExportErrors, self.modelPlanExportErrors, self.selectionModelPlanExportErrors)
        self.setModels(self.tblFactInfos, self.modelFactInfos, self.selectionModelFactInfos)
        self.setModels(self.tblFactInvcs, self.modelFactInvcs, self.selectionModelFactInvcs)
        currentDate = QDate.currentDate()
        self.orderFieldByColumn = [
            'Client.lastName',
            'Client.firstName',
            'Client.patrName',
            'Client.birthDate',
            'Client.sex',
            'CSS.socStatusType_id',
            'CSS.begDate',
            'CSS.endDate',
            'CSSU.begDate',
            'CSSU.endDate',
            'EventStage1.execDate',
            'EventStage2.execDate',
            'EventProf.execDate',
            'EventUStage1.execDate',
            'EventUStage2.execDate',
            'AttachOrgStructure.name',
        ]
        self.order = (0, True)
        self.sbYear.setValue(currentDate.year())
        self.updateClientsList()
        self.updateClientModels()
        header = self.tblClients.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(0, Qt.AscendingOrder)
        QObject.connect(header, SIGNAL('sectionClicked(int)'), self.setClientSort)
        self.tblClients.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.currentFilters = {'year': None, 'month': None, 'kind': None}
        self.cmbSocStatusesType.setTable('rbSocStatusType', True)
        self.on_chkSocStatuses_toggled(self.chkSocStatuses.isChecked())


    def contextMenuEvent(self, event):
        self.menu = QtGui.QMenu(self)
        year = self.sbYear.value()
        month = self.cmbMonth.currentIndex()
        kind = self.cmbKind.currentIndex()
        selectedRows = self.getSelectedRows(self.tblClients)
        if len(selectedRows) == 1:
            self.menu.addAction(self.actEditClient)
        if self.currentFilters['year'] == year and self.currentFilters['month'] == month and self.currentFilters['kind'] == kind and (self.chkForPlanning.isChecked() or self.chkNotPlanned.isChecked()) and kind != 0 and month != 0:
            self.menu.addAction(self.actDispAdd)
        if self.chkExportedSuccessfully.isChecked() or self.chkExportedWithErrors.isChecked() or self.chkNotExported.isChecked():
            self.menu.addAction(self.actDispDel)
        self.menu.popup(QtGui.QCursor.pos())

    def getSelectedRows(self, tbl):
        result = [index.row() for index in tbl.selectedIndexes()]
        result = list(set(result) & set(result))
        result.sort()
        return result

    def updateClientsList(self):
        try:
            db = QtGui.qApp.db
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            tableClient = db.table('Client')
            year = self.sbYear.value()
            month = self.cmbMonth.currentIndex()
            dispPassedIndex = self.cmbDispPassed.currentIndex()
            startOfThisYear = QDate(year, 1, 1)
            startOfNextYear = QDate(year + 1, 1, 1)
            startOfPrevYear = QDate(year - 1, 1, 1)
            if month == 0:
                dateFrom = QDate(year, 1, 1)
                dateTo = QDate(year, 12, 31)
            else:
                dateFrom = QDate(year, month, 1)
                if month == 12:
                    dateTo = startOfNextYear
                else:
                    dateTo = QDate(year, month + 1, 1)

            policy = ''
            kind = self.cmbKind.currentIndex()
            if self.chkForPlanning.isChecked():
                policy = u"""LEFT JOIN ClientPolicy ON ClientPolicy.client_id = Client.id AND ClientPolicy.deleted = 0
                      AND ClientPolicy.policyType_id IN (1,2)
                      AND  ClientPolicy.begDate = (SELECT
                      MAX(CP.begDate)
                      FROM ClientPolicy AS CP
                      WHERE CP.client_id = Client.id
                      AND CP.deleted = 0
                      AND CP.policyType_id IN (1,2))
                  LEFT JOIN Organisation ON Organisation.id = ClientPolicy.insurer_id"""

            attachTypeIds = db.getIdList('rbAttachType', where="code in ('1', '2')")

            sql = u"""
            select Client.id,
                SST.code as sstCode,
                CSS.begDate,
                CSS.endDate,
                SSTU.code as sstCodeU,
                CSSU.begDate as begDateU,
                CSSU.endDate as endDateU,
                AttachOrgStructure.name as attachName,
                cast(EventStage1.execDate as date) as lastStage1,
                cast(EventStage2.execDate as date) as lastStage2,
                cast(EventProf.execDate as date) as lastProf,
                cast(EventUStage1.execDate as date) as lastUStage1,
                cast(EventUStage2.execDate as date) as lastUStage2,
                PlanExport.id as planExport_id,
                PlanExportU.id as planExportU_id
            from Client
                left join ClientSocStatus as CSS on CSS.id = (
                    select max(CSS.id)
                    from ClientSocStatus as CSS
                        left join rbSocStatusClass as SSC on SSC.id = CSS.socStatusClass_id
                        left join rbSocStatusType as SST on SST.id = CSS.socStatusType_id
                    where CSS.client_id = Client.id
                        and CSS.deleted = 0
                        and CSS.begDate >= '%(startOfThisYear)s'
                        and CSS.begDate < '%(startOfNextYear)s'
                        and SSC.code = 'profilac'
                        and SST.code in ('disp', 'disp_2', 'disp_1', 'prof')
                )
                left join rbSocStatusType as SST on SST.id = CSS.socStatusType_id
                left join ClientSocStatus as CSSU on CSSU.id = (
                    select max(CSS.id)
                    from ClientSocStatus as CSS
                        left join rbSocStatusClass as SSC on SSC.id = CSS.socStatusClass_id
                        left join rbSocStatusType as SST on SST.id = CSS.socStatusType_id
                    where CSS.client_id = Client.id
                        and CSS.deleted = 0
                        and CSS.begDate >= '%(startOfThisYear)s'
                        and CSS.begDate < '%(startOfNextYear)s'
                        and SSC.code = 'profilac'
                        and SST.code in ('disp_cov1', 'disp_cov2')
                )
                left join rbSocStatusType as SSTU on SSTU.id = CSSU.socStatusType_id
                left join ClientAttach as Attach on Attach.id = (
                    select max(Attach.id)
                    from ClientAttach as Attach
                    left join OrgStructure o on o.id = Attach.orgStructure_id
                    where Attach.client_id = Client.id
                        and Attach.deleted = 0
                        and Attach.endDate is null
                        and o.areaType > 0
                        and Attach.attachType_id in (%(attachTypeIds)s)
                )
                LEFT JOIN ClientWork ON ClientWork.client_id = Client.id AND ClientWork.id = (
                    SELECT
                    MAX(CW.id)
                    FROM ClientWork AS CW
                    WHERE CW.client_id = Client.id
                    AND CW.deleted = 0)
                left join rbSocStatusType as lgotaType on lgotaType.id = (
                    select t.id
                    from ClientSocStatus as ss
                        left join rbSocStatusClass as cl on cl.id = ss.socStatusClass_id
                        left join rbSocStatusClass as cg on cg.id = cl.group_id
                        left join rbSocStatusType as t on t.id = ss.socStatusType_id
                    where ss.client_id = Client.id
                        and ss.deleted = 0
                        and t.code in ('010', '011', '012', '020', '050', '140')
                        and cl.code = '1'
                        and cg.code = '1'
                    order by t.code
                    limit 1
                )
                left join rbSocStatusType as lgota08X on lgota08X.id = (
                    select t.id
                    from ClientSocStatus as ss
                        left join rbSocStatusClass as cl on cl.id = ss.socStatusClass_id
                        left join rbSocStatusClass as cg on cg.id = cl.group_id
                        left join rbSocStatusType as t on t.id = ss.socStatusType_id
                    where ss.client_id = Client.id
                        and ss.deleted = 0
                        and ss.endDate is null
                        and t.code in ('081', '082', '083')
                        and cl.code = '1'
                        and cg.code = '1'
                    order by t.code
                    limit 1
                )
                left join rbSocStatusType as socStatus114 on socStatus114.id = (
                  select t.id
                  from ClientSocStatus as ss
                    left join rbSocStatusClass as cl on cl.id = ss.socStatusClass_id
                    left join rbSocStatusType as t on t.id = ss.socStatusType_id
                  where ss.client_id = Client.id
                    and ss.deleted = 0
                    and ss.endDate is null
                    and t.code = 'd_114'
                    and cl.code = '9'
                  limit 1
                )
                left join disp_PlanExport as PlanExport on PlanExport.exportKind = 'ClientSocStatus' and PlanExport.row_id = CSS.id
                left join disp_PlanExport as PlanExportU on PlanExportU.exportKind = 'ClientSocStatus' and PlanExportU.row_id = CSSU.id
                left join OrgStructure as AttachOrgStructure on AttachOrgStructure.id = Attach.orgStructure_id
                left join Event as EventStage1 on EventStage1.id = (
                    select e.id
                    from Event as e
                        inner join EventType as et on et.id = e.eventType_id
                        inner join rbEventProfile as ep on ep.id = et.eventProfile_id
                    where e.client_id = Client.id
                        and e.deleted = 0
                        and e.execDate >= '%(startOfThisYear)s'
                        and e.execDate < '%(startOfNextYear)s'
                        and ep.regionalCode in ('8008', '8014', '8017')
                    order by e.execDate desc
                    limit 1
                )
                left join Event as EventStage2 on EventStage2.id = (
                    select e.id
                    from Event as e
                        inner join EventType as et on et.id = e.eventType_id
                        inner join rbEventProfile as ep on ep.id = et.eventProfile_id
                    where e.client_id = Client.id
                        and e.deleted = 0
                        and e.execDate >= '%(startOfThisYear)s'
                        and e.execDate < '%(startOfNextYear)s'
                        and ep.regionalCode in ('8009', '8015')
                    order by e.execDate desc
                    limit 1
                )
                left join Event as EventProf on EventProf.id = (
                    select e.id
                    from Event as e
                        inner join EventType as et on et.id = e.eventType_id
                        inner join rbEventProfile as ep on ep.id = et.eventProfile_id
                    where e.client_id = Client.id
                        and e.deleted = 0
                        and e.execDate >= '%(startOfThisYear)s'
                        and e.execDate < '%(startOfNextYear)s'
                        and ep.regionalCode = '8011'
                    order by e.execDate desc
                    limit 1
                )
                left join Event as EventUStage1 on EventUStage1.id = (
                    select e.id
                    from Event as e
                        inner join EventType as et on et.id = e.eventType_id
                        inner join rbEventProfile as ep on ep.id = et.eventProfile_id
                    where e.client_id = Client.id
                        and e.deleted = 0
                        and e.execDate >= '%(startOfThisYear)s'
                        and e.execDate < '%(startOfNextYear)s'
                        and ep.regionalCode = '8018'
                    order by e.execDate desc
                    limit 1
                )
                left join Event as EventUStage2 on EventUStage2.id = (
                    select e.id
                    from Event as e
                        inner join EventType as et on et.id = e.eventType_id
                        inner join rbEventProfile as ep on ep.id = et.eventProfile_id
                    where e.client_id = Client.id
                        and e.deleted = 0
                        and e.execDate >= '%(startOfThisYear)s'
                        and e.execDate < '%(startOfNextYear)s'
                        and ep.regionalCode = '8019'
                    order by e.execDate desc
                    limit 1
                )
                left join ClientIdentification as ReestrCOVID on ReestrCOVID.id = (
                    select ci.id
                    from ClientIdentification as ci
                        left join rbAccountingSystem as acs on acs.id = ci.accountingSystem_id
                    where ci.client_id = Client.id
                        and ci.deleted = 0
                        and ci.checkDate < '%(startOfNextYear)s'
                        and acs.code = 'ReestrCOVID'
                    order by ci.checkDate desc
                    limit 1
                )
                %(policy)s
            """ % {
                "startOfThisYear": startOfThisYear.toString('yyyy-MM-dd'),
                "startOfNextYear": startOfNextYear.toString('yyyy-MM-dd'),
                "attachTypeIds": ', '.join([str(id) for id in attachTypeIds]),
                "policy": policy
            }
            where = [
                'Client.deleted = 0'
            ]
            if self.chkFilterLastName.isChecked():
                lastName = forceStringEx(self.edtFilterLastName.text())
                if lastName:
                    where.append("Client.lastName like '%s%%'" % lastName)
            if self.chkFilterFirstName.isChecked():
                firstName = forceStringEx(self.edtFilterFirstName.text())
                if firstName:
                    where.append("Client.firstName like '%s%%'" % firstName)
            if self.chkFilterPatrName.isChecked():
                patrName = forceStringEx(self.edtFilterPatrName.text())
                if patrName:
                    where.append("Client.patrName like '%s%%'" % patrName)
            if self.chkFilterBirthDay.isChecked():
                birthDate = self.edtFilterBirthDay.date()
                if not birthDate:
                    birthDate = None
                if self.chkFilterEndBirthDay.isChecked():
                    endBirthDate = self.edtFilterEndBirthDay.date()
                    if not endBirthDate:
                        endBirthDate = None
                    where.append(tableClient['birthDate'].dateGe(birthDate))
                    where.append(tableClient['birthDate'].dateLe(endBirthDate))
                else:
                    where.append(tableClient['birthDate'].eq(birthDate))
            if self.chkFilterAddressOrgStructure.isChecked():
                orgStructureId = self.cmbFilterAddressOrgStructure.value()
                if orgStructureId:
                    orgStructureIdList = getOrgStructureDescendants(orgStructureId)
                    tableClientAttach = db.table('ClientAttach').alias('Attach')
                    # where.append(u"Attach.attachType_id = 2")
                    where.append(tableClientAttach['orgStructure_id'].inlist(orgStructureIdList))

            if self.chkFilterSex.isChecked():
                sex = self.cmbFilterSex.currentIndex()
                if sex:
                    where.append(tableClient['sex'].eq(sex))
            if self.cmbBusyness.currentIndex() == 1:
                where.append(u"IF((ClientWork.org_id is not null or IFNULL(ClientWork.freeInput, '') <> '') and IFNULL(ClientWork.post, '') <> '', 1, 0) = 1")
            elif self.cmbBusyness.currentIndex() == 2:
                where.append(u"IF((ClientWork.org_id is not null or IFNULL(ClientWork.freeInput, '') <> '') and IFNULL(ClientWork.post, '') <> '', 1, 0) = 0")

            if self.chkSocStatuses.isChecked():
                socStatusesCondition = self.chkSocStatusesCondition.isChecked()  # socStatusesCondition

                socStatusesBegDate = self.edtFilterSocStatusesBegDate.date()  # socStatusesBegDate
                socStatusesEndDate = self.edtFilterSocStatusesEndDate.date()  # socStatusesEndDate  # filter.get('socStatusesEndDate', QDate())

                socStatusesClass = self.cmbSocStatusesClass.value()  # socStatusesClass
                socStatusesType = self.cmbSocStatusesType.value()  # socStatusesType

                tableClientSocStatus = db.table('ClientSocStatus')
                clientFilterTable = db.table('Client')
                socStatusFilterTable = db.table('ClientSocStatus')

                if socStatusesCondition and not socStatusesEndDate and not socStatusesBegDate and not socStatusesType and not socStatusesClass:
                    where.append(tableClientSocStatus['id'].isNull())
                if socStatusesClass:
                    socStatusClassIdList = db.getDescendants('rbSocStatusClass', 'group_id', socStatusesClass)
                    if socStatusClassIdList:
                        stmtStatusTypeId = u'''SELECT DISTINCT rbSocStatusClassTypeAssoc.type_id
                FROM  rbSocStatusClassTypeAssoc
                WHERE rbSocStatusClassTypeAssoc.class_id IN (%s)''' % (
                            u','.join(str(socStatusClassId) for socStatusClassId in socStatusClassIdList))
                        queryStatusTypeId = db.query(stmtStatusTypeId)
                        resultStatusTypeIdList = []
                        while queryStatusTypeId.next():
                            resultStatusTypeIdList.append(queryStatusTypeId.value(0).toInt()[0])
                            parentSocStatusClassIdList = db.getTheseAndParents('rbSocStatusClass', 'group_id',
                                                                               [socStatusesClass])
                        if socStatusesCondition:
                            clientFilterTable = clientFilterTable.leftJoin(socStatusFilterTable, db.joinAnd(
                                [clientFilterTable['id'].eq(socStatusFilterTable['client_id']),
                                 tableClientSocStatus['deleted'].eq(0)]))
                            if resultStatusTypeIdList:
                                clientFilterCond = [db.joinOr(
                                    [socStatusFilterTable['socStatusType_id'].inlist(resultStatusTypeIdList),
                                     tableClientSocStatus['id'].isNull()])]
                                if socStatusesBegDate:
                                    clientFilterCond.append(
                                        db.joinOr([socStatusFilterTable['endDate'].dateGe(socStatusesBegDate),
                                                   socStatusFilterTable['endDate'].isNull()]))
                                if socStatusesEndDate:
                                    clientFilterCond.append(
                                        db.joinOr([socStatusFilterTable['begDate'].dateLe(socStatusesEndDate),
                                                   socStatusFilterTable['begDate'].isNull()]))
                                clientSocStatusesFilterIdList = db.getIdList(clientFilterTable, clientFilterTable['id'],
                                                                             clientFilterCond, ['id'])
                                where.append(tableClient['id'].notInlist(clientSocStatusesFilterIdList))
                            else:
                                clientFilterCond = [db.joinOr([db.joinAnd[(socStatusFilterTable['socStatusType_id'].inlist(parentSocStatusClassIdList),
                                tableClientSocStatus['id'].isNull())],tableClientSocStatus['socStatusType_id'].isNull()])]
                        else:
                            if resultStatusTypeIdList:
                                where.append(tableClientSocStatus['socStatusType_id'].inlist(resultStatusTypeIdList))
                            else:
                                where.append(tableClientSocStatus['socStatusClass_id'].inlist(parentSocStatusClassIdList))
                                where.append(tableClientSocStatus['socStatusType_id'].isNull())
                                where.append(tableClientSocStatus['deleted'].eq(0))
                    else:
                        if socStatusesCondition:
                            clientFilterTable = clientFilterTable.leftJoin(
                                socStatusFilterTable,
                                db.joinAnd([clientFilterTable['id'].eq(
                                    socStatusFilterTable['client_id']),
                                    tableClientSocStatus['deleted'].eq(0)]))
                            clientFilterCond = [db.joinOr([socStatusFilterTable['socStatusClass_id'].eq(socStatusesClass),tableClientSocStatus['id'].isNull()])]
                            if socStatusesBegDate:
                                clientFilterCond.append(db.joinOr([socStatusFilterTable['endDate'].dateGe(socStatusesBegDate),socStatusFilterTable['endDate'].isNull()]))
                            if socStatusesEndDate:
                                clientFilterCond.append(db.joinOr([socStatusFilterTable['begDate'].dateLe(socStatusesEndDate),socStatusFilterTable['begDate'].isNull()]))
                            clientSocStatusesFilterIdList = db.getIdList(clientFilterTable, clientFilterTable['id'],clientFilterCond, ['id'])
                            where.append(tableClient['id'].notInlist(clientSocStatusesFilterIdList))
                        else:
                            where.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusesClass))
                            where.append(tableClientSocStatus['deleted'].eq(0))
                if socStatusesType:
                    if socStatusesCondition:
                        if not socStatusesClass:
                            clientFilterTable = clientFilterTable.leftJoin(
                                socStatusFilterTable,
                                db.joinAnd([clientFilterTable['id'].eq(
                                    socStatusFilterTable['client_id']),
                                    tableClientSocStatus['deleted'].eq(0)]))
                        clientFilterCond = [
                            db.joinOr([clientFilterTable['socStatusType_id'].eq(socStatusesType),
                                       clientFilterTable['id'].isNull()])]
                        if socStatusesBegDate:
                            clientFilterCond.append(
                                db.joinOr([socStatusFilterTable['endDate'].dateGe(socStatusesBegDate),
                                           socStatusFilterTable['endDate'].isNull()]))
                        if socStatusesEndDate:
                            clientFilterCond.append(
                                db.joinOr([socStatusFilterTable['begDate'].dateLe(socStatusesEndDate),
                                           socStatusFilterTable['begDate'].isNull()]))
                        clientSocStatusesFilterIdList = db.getIdList(clientFilterTable, clientFilterTable['id'], clientFilterCond, ['id'])
                        where.append(tableClient['id'].notInlist(clientSocStatusesFilterIdList))
                    else:
                        where.append(tableClientSocStatus['socStatusType_id'].eq(socStatusesType))
                        where.append(tableClientSocStatus['deleted'].eq(0))
                if not socStatusesCondition:
                    if socStatusesBegDate:
                        where.append(db.joinOr([tableClientSocStatus['endDate'].dateGe(socStatusesBegDate),
                                                tableClientSocStatus['endDate'].isNull()]))
                    if socStatusesEndDate:
                        where.append(db.joinOr([tableClientSocStatus['begDate'].dateLe(socStatusesEndDate),
                                                tableClientSocStatus['begDate'].isNull()]))

            if self.chkForPlanning.isChecked():
                date = QDate(year, 12, 31)
                where.append("Attach.id is not null")
                if kind == 0:
                    where.append("(CSS.id is null or CSSU.id is null)")
                elif kind in (1, 2, 3, 4):
                    where.append("CSS.id is null")
                elif kind in (5, 6):
                    where.append("CSSU.id is null")
                where.append(tableClient['birthDate'].le(QDate.currentDate().addYears(-18)))
                if kind == 0:
                    where.append(tableClient['birthDate'].le(date.addYears(-18)))
                elif kind == 1:
                    where.append("AGE(Client.birthDate, '{age}') IN (18, 21, 24, 27, 30, 33, 36, 39)".format(age=date.toString('yyyy-MM-dd')))
                elif kind == 2:
                    where.append("0")
                elif kind == 3:
                    where.append("""AGE(Client.birthDate, '{age}') between 18 and 39 
                                    AND AGE(Client.birthDate, '{age}') NOT IN (18, 21, 24, 27, 30, 33, 36, 39)""".format(age=date.toString('yyyy-MM-dd')))
                    where.append('lgotaType.code is null')
                    where.append('socStatus114.code is null')
                elif kind == 4:
                    where.append("""(AGE(Client.birthDate, '{age}') >= 40 
                    OR lgotaType.code in ('010', '011', '012', '140') 
                    OR lgotaType.code in ('020', '050') and lgota08X.code is not null
                    OR socStatus114.code is not null)""".format(age=date.toString('yyyy-MM-dd')))
                elif kind in (5, 6):
                    where.append(u"ReestrCOVID.id is not null")

                if kind in (1, 2, 3, 4):
                    matCodes = "'211', '261'"
                elif kind in (5, 6):
                    matCodes = "'233'"
                else:
                    matCodes = None
                if matCodes:
                    where.append(
                        u"""NOT EXISTS(select e.id 
                            FROM Event e
                            LEFT JOIN Contract c ON c.id = e.contract_id
                            LEFT JOIN rbFinance f ON f.id = c.finance_id
                            LEFT JOIN EventType et on et.id = e.eventType_id
                            LEFT JOIN rbMedicalAidType mat ON et.medicalAidType_id = mat.id
                            WHERE e.client_id = Client.id and e.execDate >= '{startOfThisYear}' and e.execDate < '{startOfNextYear}' 
                                AND e.deleted = 0 
                                AND mat.regionalCode in ({matCodes})
                                AND f.code = '2')
                        """.format(
                            startOfThisYear=startOfThisYear.toString('yyyy-MM-dd'),
                            startOfNextYear=startOfNextYear.toString('yyyy-MM-dd'),
                            matCodes=matCodes
                        )
                    )
                where.append(u"NOT EXISTS (SELECT NULL FROM disp_ExcludedFromPlanning WHERE client_id = Client.id AND `year` = {0})".format(year))
                where.append(u"NOT EXISTS (SELECT NULL FROM disp_FactInvcs WHERE client_id = Client.id AND `year` = {0})".format(year))
                where.append(u"NOT EXISTS (SELECT NULL FROM disp_FactInfos WHERE client_id = Client.id AND `year` = {0})".format(year))
                where.append(u"ClientPolicy.id is not null")
                where.append(u"Client.deathDate IS NULL")
                where.append(u"Organisation.OKATO = '03000'")
            elif self.chkNotPlanned.isChecked():
                where.append('CSS.id is null and CSSU.id is null')
            else:
                kindGroups = []
                if kind in (0, 1, 2, 3, 4):
                    kindGroups.append(('CSS', 'PlanExport'))
                if kind in (0, 5, 6):
                    kindGroups.append(('CSSU', 'PlanExportU'))
                kindGroupsFilter = []
                for cssTable, planExportTable in kindGroups:
                    groupFilter = []
                    groupFilter.append("{cssTable}.begDate >= '{dateFrom}' and {cssTable}.begDate < '{dateTo}'".format(
                        cssTable=cssTable,
                        dateFrom=dateFrom.toString('yyyy-MM-dd'),
                        dateTo=dateTo.toString('yyyy-MM-dd')
                    ))
                    statusFilter = []
                    if self.chkNotExported.isChecked():
                        statusFilter.append("{planExportTable}.id is null".format(planExportTable=planExportTable))
                    if self.chkExportedSuccessfully.isChecked():
                        statusFilter.append("{planExportTable}.exportSuccess = 1".format(planExportTable=planExportTable))
                    if self.chkExportedWithErrors.isChecked():
                        statusFilter.append("{planExportTable}.exportSuccess = 0".format(planExportTable=planExportTable))
                    if len(statusFilter) > 0:
                        groupFilter.append('(' + ' or '.join(statusFilter) + ')')
                    kindGroupsFilter.append('(' + ' and '.join(groupFilter) + ')')
                where.append('(' + ' or '.join(kindGroupsFilter) + ')')
                if kind == 1:
                    where.append("SST.code = 'disp'")
                elif kind == 2:
                    where.append("SST.code = 'disp_2'")
                elif kind == 3:
                    where.append("SST.code = 'prof'")
                elif kind == 4:
                    where.append("SST.code = 'disp_1'")
                elif kind == 5:
                    where.append("SSTU.code = 'disp_cov1'")
                elif kind == 6:
                    where.append("SSTU.code = 'disp_cov2'")
            if self.cmbDispPassed.isEnabled() and dispPassedIndex in [1, 2]:
                if kind == 0:
                    profileList = ['8008', '8011', '8014', '8017', '8018', '8019']
                    matList = ['211', '261', '233']
                elif kind == 1:
                    profileList = ['8008']
                    matList = ['211', '261']
                elif kind == 2:
                    profileList = ['8017']
                    matList = ['211', '261']
                elif kind == 4:
                    profileList = ['8014']
                    matList = ['211', '261']
                elif kind == 3:
                    profileList = ['8011']
                    matList = ['211', '261']
                elif kind in (5, 6):
                    profileList = ['8018']
                    matList = ['233']
                where.append(u"""{dispPassed} EXISTS(select e.id 
                                                FROM Event e
                                                LEFT JOIN EventType et on et.id = e.eventType_id
                                                LEFT JOIN rbEventProfile ep ON ep.id = et.eventProfile_id
                                                LEFT JOIN rbMedicalAidType mat ON et.medicalAidType_id = mat.id
                                                WHERE e.client_id = Client.id 
                                                        AND e.execDate >= '{startOfThisYear}' AND e.execDate < '{startOfNextYear}' 
                                                        AND e.deleted = 0 
                                                        AND ep.regionalCode in ({profileCondition})
                                                        AND mat.regionalCode in ({matCondition})
                                                        )""".format(dispPassed='NOT' if dispPassedIndex == 2 else '',
                                                                    profileCondition=','.join(profileList),
                                                                    matCondition=','.join(matList),
                                                                    startOfThisYear=startOfThisYear.toString('yyyy-MM-dd'),
                                                                    startOfNextYear=startOfNextYear.toString('yyyy-MM-dd')))
            if self.chkHideUDEvents.isEnabled() and self.chkHideUDEvents.isChecked():
                where.append(u"""NOT EXISTS(select e.id 
                                                FROM Event e
                                                LEFT JOIN EventType et on et.id = e.eventType_id
                                                LEFT JOIN rbEventProfile ep ON ep.id = et.eventProfile_id
                                                LEFT JOIN rbMedicalAidType mat ON et.medicalAidType_id = mat.id
                                                WHERE e.client_id = Client.id 
                                                        AND e.deleted = 0 
                                                        AND ep.regionalCode = '8018'
                                                        AND mat.regionalCode = '233'
                                                        )""")
            sql += (('\nLEFT JOIN ClientSocStatus ON Client.id = ClientSocStatus.client_id' if self.chkSocStatuses.isChecked() else '') + '\nwhere ' + ' and '.join(where))

            order = self.getOrderField()
            sql += (' order by ' + order)

            idList = []
            infoDict = self.modelClients.clientInfoDict
            infoDict.clear()
            query = db.query(sql)
            while query.next():
                record = query.record()
                clientId = forceRef(record.value('id'))
                idList.append(clientId)
                infoDict[clientId] = record
            self.modelClients.setIdList(idList)
            count = len(idList)
            people = u", {0} человек".format(len(list(set(idList)))) if idList else u""
            self.lblClientsCount.setText(formatRecordsCount(count) + people)
        except Exception as e:
            QtGui.QMessageBox.critical(self, u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)
        finally:
            QtGui.QApplication.restoreOverrideCursor()


    def updateClientModels(self):
        client_id = self.tblClients.currentItemId()
        year = self.sbYear.value()
        clientInfo = self.modelClients.clientInfoDict.get(client_id)
        planExport_id = forceRef(clientInfo.value('planExport_id')) if clientInfo else None
        self.modelPlanExportErrors.update(planExport_id)
        self.tabWidget.setTabText(0, u'Ошибки (%d)' % self.modelPlanExportErrors.rowCount())
        self.modelFactInfos.update(client_id, year)
        self.tabWidget.setTabText(1, u'Информирование (%d)' % self.modelFactInfos.rowCount())
        self.modelFactInvcs.update(client_id, year)
        self.tabWidget.setTabText(2, u'Счета (%d)' % self.modelFactInvcs.rowCount())
    
    def getOrderField(self):
        column, asc = self.order
        direction = ' asc' if asc else ' desc'
        field = self.orderFieldByColumn[column] + direction
        return field
    
    def setClientSort(self, newColumn):
        newOrderField = self.orderFieldByColumn[newColumn]
        if newOrderField is None:
            return
        column, asc = self.order
        if column == newColumn:
            newAsc = not asc
        else:
            newAsc = True
        self.order = (newColumn, newAsc)
        self.updateClientsList()

    def showReport(self):
        def showReportInt(isShort=False):
            report = CDispExchangeReport(self, self.modelClients, isShort)
            description = self.reportDescription()
            reportTxt = report.build(description)
            view = CReportViewDialog(self)
            view.setWindowTitle(report.title())
            view.setText(reportTxt)
            if report.pageFormat:
                view.setPageFormat(report.pageFormat)
            return view

        dialog = QtGui.QDialog(self)
        dialog.setWindowTitle(u"Настройки отчета")
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        vbox = QtGui.QVBoxLayout()
        chk = QtGui.QCheckBox(dialog)
        chk.setText(u"Печатать данные всех колонок")
        chk.setChecked(False)
        chk.setObjectName('chk')
        vbox.addWidget(chk)
        btnBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok, Qt.Horizontal, dialog)
        vbox.addWidget(btnBox)
        dialog.setLayout(vbox)
        btnBox.accepted.connect(dialog.accept)
        btnBox.rejected.connect(dialog.reject)
        dialog.show()
        if dialog.exec_():
            view = QtGui.qApp.callWithWaitCursor(self, showReportInt, isShort=not chk.isChecked())
            view.exec_()
        dialog.setParent(None)

    
    def reportDescription(self):
        year = self.sbYear.value()
        month = self.cmbMonth.currentIndex()
        kind = self.cmbKind.currentIndex()
        lines = []
        lines.append(u'Год: %d' % year)
        if month > 0:
            monthText = self.cmbMonth.currentText()
            lines.append(u'Месяц: %s' % monthText)
        if kind > 0:
            kindText = self.cmbKind.currentText()
            lines.append(u'Вид осмотра: %s' % kindText)
        if self.chkFilterLastName.isChecked():
            lastName = forceStringEx(self.edtFilterLastName.text())
            lines.append(u'Фамилия: %s' % lastName)
        if self.chkFilterFirstName.isChecked():
            firstName = forceStringEx(self.edtFilterFirstName.text())
            lines.append(u'Имя: %s' % firstName)
        if self.chkFilterPatrName.isChecked():
            patrName = forceStringEx(self.edtFilterPatrName.text())
            lines.append(u'Отчество: %s' % patrName)
        statusLines = []
        if self.chkNotPlanned.isChecked():
            statusLines.append(u'- не запланированные')
        if self.chkNotExported.isChecked():
            statusLines.append(u'- запланированные, не отправленные')
        if self.chkExportedSuccessfully.isChecked():
            statusLines.append(u'- отправленные успешно')
        if self.chkExportedWithErrors.isChecked():
            statusLines.append(u'- отправленные с ошибками')
        if len(statusLines) > 0 and len(statusLines) < 4:
            lines.append(u'Статус:')
            lines += statusLines
        return '\n'.join(lines)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelClients_currentRowChanged(self, current, previous):
        self.updateClientModels()

    @pyqtSignature('')
    def on_btnApplyFilter_clicked(self):
        year = self.sbYear.value()
        month = self.cmbMonth.currentIndex()
        kind = self.cmbKind.currentIndex()
        self.currentFilters['year'] = year
        self.currentFilters['month'] = month
        self.currentFilters['kind'] = kind
        self.updateClientsList()

    @pyqtSignature('')
    def on_btnResetFilter_clicked(self):
        self.chkFilterLastName.setChecked(False)
        self.chkFilterFirstName.setChecked(False)
        self.chkFilterPatrName.setChecked(False)
        self.chkNotPlanned.setChecked(False)
        self.chkNotExported.setChecked(True)
        self.chkExportedSuccessfully.setChecked(False)
        self.chkExportedWithErrors.setChecked(False)
        year = self.sbYear.value()
        month = self.cmbMonth.currentIndex()
        kind = self.cmbKind.currentIndex()
        self.currentFilters['year'] = year
        self.currentFilters['month'] = month
        self.currentFilters['kind'] = kind
        self.updateClientsList()

    @pyqtSignature('int')
    def on_chkFilterLastName_stateChanged(self, state):
        self.edtFilterLastName.setEnabled(state == Qt.Checked)
        if self.chkFilterLastName.isChecked():
            self.edtFilterLastName.setFocus()

    @pyqtSignature('int')
    def on_chkFilterFirstName_stateChanged(self, state):
        self.edtFilterFirstName.setEnabled(state == Qt.Checked)
        if self.chkFilterFirstName.isChecked():
            self.edtFilterFirstName.setFocus()

    @pyqtSignature('int')
    def on_chkFilterPatrName_stateChanged(self, state):
        self.edtFilterPatrName.setEnabled(state == Qt.Checked)
        if self.chkFilterPatrName.isChecked():
            self.edtFilterPatrName.setFocus()

    @pyqtSignature('int')
    def on_cmbSocStatusesClass_currentIndexChanged(self, index):
        socStatusClassId = self.cmbSocStatusesClass.value()
        if socStatusClassId:
            filter = (u'''rbSocStatusType.id IN (SELECT DISTINCT rbSocStatusClassTypeAssoc.type_id
            FROM  rbSocStatusClassTypeAssoc
            WHERE rbSocStatusClassTypeAssoc.class_id = %s)'''%(socStatusClassId))
        else:
            filter = u''
        self.cmbSocStatusesType.setFilter(filter)

    @pyqtSignature('bool')
    def on_chkFilterBirthDay_toggled(self, checked):
        if checked:
            self.edtFilterBirthDay.setEnabled(checked)
            self.chkFilterEndBirthDay.setEnabled(checked)
            self.edtFilterEndBirthDay.setEnabled(self.chkFilterEndBirthDay.isChecked())
            self.edtFilterBirthDay.setFocus()
        else:
            self.edtFilterBirthDay.setEnabled(False)
            self.chkFilterEndBirthDay.setEnabled(False)
            self.edtFilterEndBirthDay.setEnabled(False)

    @pyqtSignature('bool')
    def on_chkFilterAddressOrgStructure_toggled(self, checked):
        self.cmbFilterAddressOrgStructure.setEnabled(checked)

    @pyqtSignature('bool')
    def on_chkFilterEndBirthDay_toggled(self, checked):
        self.edtFilterEndBirthDay.setEnabled(checked)
        if self.chkFilterEndBirthDay.isChecked():
            self.edtFilterEndBirthDay.setFocus()

    @pyqtSignature('bool')
    def on_chkFilterSex_toggled(self, checked):
        self.cmbFilterSex.setEnabled(checked)

    @pyqtSignature('bool')
    def on_chkSocStatuses_toggled(self, checked):
        self.chkSocStatusesCondition.setEnabled(checked)

        self.lblFilterSocStatusesBegDate.setEnabled(checked)
        self.edtFilterSocStatusesBegDate.setEnabled(checked)
        self.lblFilterSocStatusesEndDate.setEnabled(checked)
        self.edtFilterSocStatusesEndDate.setEnabled(checked)

        self.cmbSocStatusesClass.setEnabled(checked)
        self.cmbSocStatusesType.setEnabled(checked)

    @pyqtSignature('')
    def on_btnPlanningProfilactic_clicked(self):
        CPlanningProfilactic(self).exec_()

    @pyqtSignature('')
    def on_btnPutEvPlanList_clicked(self):
        CExportDispPlanDialog(self).exec_()

    @pyqtSignature('')
    def on_btnGetEvFactInfos_clicked(self):
        CImportDispFactInfosDialog(self).exec_()

    @pyqtSignature('')
    def on_btnGetEvFactInvcs_clicked(self):
        CImportDispFactInvcsDialog(self).exec_()

    @pyqtSignature('')
    def on_btnGetEvPlanQtys_clicked(self):
        CImportDispPlanQtysDialog(self).exec_()

    @pyqtSignature('')
    def on_btnPutEvContacts_clicked(self):
        CExportDispContactsDialog(self).exec_()

    @pyqtSignature('')
    def on_btnPutEvPlanDates_clicked(self):
        CExportDispPlanDatesDialog(self).exec_()

    @pyqtSignature('')
    def on_btnExportedPlan_clicked(self):
        CImportDispExportedPlanDialog(self).exec_()

    @pyqtSignature('')
    def on_chkForPlanning_clicked(self):
        self.cmbDispPassed.setDisabled(self.chkForPlanning.isChecked())
        self.chkHideUDEvents.setEnabled(self.chkForPlanning.isChecked() and self.cmbKind.currentIndex() in (5, 6))
        if self.chkForPlanning.isChecked():
            self.chkNotExported.setChecked(False)
            self.chkNotPlanned.setChecked(False)
            self.chkExportedSuccessfully.setChecked(False)
            self.chkExportedWithErrors.setChecked(False)

    @pyqtSignature('')
    def on_chkNotPlanned_clicked(self):
        if self.chkNotPlanned.isChecked():
            self.chkForPlanning.setChecked(False)
            self.chkNotExported.setChecked(False)
            self.chkExportedSuccessfully.setChecked(False)
            self.chkExportedWithErrors.setChecked(False)
            self.cmbDispPassed.setDisabled(self.chkForPlanning.isChecked())
            self.chkHideUDEvents.setEnabled(self.chkForPlanning.isChecked() and self.cmbKind.currentIndex() in (5, 6))

    @pyqtSignature('')
    def on_chkNotExported_clicked(self):
        if self.chkNotExported.isChecked():
            self.chkForPlanning.setChecked(False)
            self.chkNotPlanned.setChecked(False)
            self.cmbDispPassed.setDisabled(self.chkForPlanning.isChecked())
            self.chkHideUDEvents.setEnabled(self.chkForPlanning.isChecked() and self.cmbKind.currentIndex() in (5, 6))

    @pyqtSignature('')
    def on_chkExportedSuccessfully_clicked(self):
        if self.chkExportedSuccessfully.isChecked():
            self.chkForPlanning.setChecked(False)
            self.chkNotPlanned.setChecked(False)
            self.cmbDispPassed.setDisabled(self.chkForPlanning.isChecked())
            self.chkHideUDEvents.setEnabled(self.chkForPlanning.isChecked() and self.cmbKind.currentIndex() in (5, 6))

    @pyqtSignature('')
    def on_chkExportedWithErrors_clicked(self):
        if self.chkExportedWithErrors.isChecked():
            self.chkForPlanning.setChecked(False)
            self.chkNotPlanned.setChecked(False)
            self.cmbDispPassed.setDisabled(self.chkForPlanning.isChecked())
            self.chkHideUDEvents.setEnabled(self.chkForPlanning.isChecked() and self.cmbKind.currentIndex() in (5, 6))
    
    @pyqtSignature('int')
    def on_cmbKind_currentIndexChanged(self, index):
        self.chkHideUDEvents.setEnabled(self.chkForPlanning.isChecked() and self.cmbKind.currentIndex() in (5, 6))

    @pyqtSignature('')
    def on_actDispAdd_triggered(self):
        rows = self.getSelectedRows(self.tblClients)
        year = forceInt(self.currentFilters['year'])
        month = forceInt(self.currentFilters['month'])
        kind = forceInt(self.currentFilters['kind'])
        self.modelClients.addDisp(rows=rows, kind=kind, month=month, year=year)
        # self.updateClientsList()

    @pyqtSignature('')
    def on_actDispDel_triggered(self):
        rows = self.getSelectedRows(self.tblClients)
        year = forceInt(self.sbYear.value())
        self.modelClients.delDisp(rows=rows, year=year)
        # self.updateClientsList()

    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        clientId = self.tblClients.currentItemId()
        if clientId is not None and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = None
            QtGui.qApp.setWaitCursor()
            try:
                try:
                    dialog = CClientEditDialog(self)
                    dialog.load(clientId)
                finally:
                    QtGui.qApp.restoreOverrideCursor()
                if dialog.exec_():
                    self.update()
            finally:
                if dialog:
                    dialog.deleteLater()

    @pyqtSignature('')
    def on_btnShowReport_clicked(self):
        self.showReport()

class CClientsModel(CTableModel):
    class CSocStatusTypeNameCol(CTextCol):
        def __init__(self, title, fields, defaultWidth, cssDict):
            CTextCol.__init__(self, title, fields, defaultWidth, 'l')
            self.dict = cssDict
            db = QtGui.qApp.db
            self.typeNameByCode = {
                'disp': u'Дисп. раз в 3 г',
                'disp_2': u'Дисп. раз в 2 г',
                'disp_1': u'Дисп. ежегодная',
                'prof': u'Проф. осмотр',
                'disp_cov1': u'УД (1 гр)',
                'disp_cov2': u'УД (2 гр)'
            }

        def format(self, values):
            clientId = forceRef(values[0])
            record = self.dict.get(clientId)
            if record:
                kindGroupNames = []
                sstCode = forceString(record.value('sstCode'))
                sstCodeU = forceString(record.value('sstCodeU'))
                if sstCode in self.typeNameByCode:
                    kindGroupNames.append(self.typeNameByCode[sstCode])
                if sstCodeU in self.typeNameByCode:
                    kindGroupNames.append(self.typeNameByCode[sstCodeU])
                if kindGroupNames:
                    return ', '.join(kindGroupNames)
                else:
                    return CCol.invalid
            else:
                return CCol.invalid
    
    class CSocStatusDateCol(CDateFixedCol):
        def __init__(self, title, fields, defaultWidth, dateField, cssDict):
            CDateFixedCol.__init__(self, title, fields, defaultWidth, highlightRedDate=False)
            self.dateField = dateField
            self.dict = cssDict

        def format(self, values):
            clientId = forceRef(values[0])
            record = self.dict.get(clientId)
            if record:
                date = record.value(self.dateField)
                return CDateFixedCol.format(self, [date])
            else:
                return CCol.invalid
    
    class CInfoDictCol(CTextCol):
        def __init__(self, title, defaultWidth, infoDict, dictKey):
            CTextCol.__init__(self, title, ['id'], defaultWidth, 'l')
            self.infoDict = infoDict
            self.dictKey = dictKey

        def format(self, values):
            clientId = forceRef(values[0])
            record = self.infoDict.get(clientId)
            if record:
                return toVariant(forceString(record.value(self.dictKey)))
            else:
                return CCol.invalid

    def __init__(self, parent):
        self.clientInfoDict = {}
        CTableModel.__init__(self, parent)
        self.parent = parent
        self.addColumn(CNameCol(u'Фамилия',    ['lastName'], 15))
        self.addColumn(CNameCol(u'Имя',        ['firstName'], 15))
        self.addColumn(CNameCol(u'Отчество',   ['patrName'], 15))
        self.addColumn(CDateFixedCol(u'Дата рожд.', ['birthDate'], 12, highlightRedDate=False))
        self.addColumn(CEnumCol(u'Пол',        ['sex'], [u'-', u'М', u'Ж'], 4, 'c'))
        self.addColumn(CClientsModel.CSocStatusTypeNameCol(u'Мероприятие', ['id'], 15, self.clientInfoDict))
        self.addColumn(CClientsModel.CSocStatusDateCol(u'Дата начала', ['id'], 15, 'begDate', self.clientInfoDict))
        self.addColumn(CClientsModel.CSocStatusDateCol(u'Дата окончания', ['id'], 15, 'endDate', self.clientInfoDict))
        self.addColumn(CClientsModel.CSocStatusDateCol(u'Дата начала УД', ['id'], 15, 'begDateU', self.clientInfoDict))
        self.addColumn(CClientsModel.CSocStatusDateCol(u'Дата окончания УД', ['id'], 15, 'endDateU', self.clientInfoDict))
        self.addColumn(CClientsModel.CInfoDictCol(u'Дата 1 этапа', 15, self.clientInfoDict, 'lastStage1'))
        self.addColumn(CClientsModel.CInfoDictCol(u'Дата 2 этапа', 15, self.clientInfoDict, 'lastStage2'))
        self.addColumn(CClientsModel.CInfoDictCol(u'Дата профосмотра', 15, self.clientInfoDict, 'lastProf'))
        self.addColumn(CClientsModel.CInfoDictCol(u'Дата 1 этапа УД', 15, self.clientInfoDict, 'lastUStage1'))
        self.addColumn(CClientsModel.CInfoDictCol(u'Дата 2 этапа УД', 15, self.clientInfoDict, 'lastUStage2'))
        self.addColumn(CClientsModel.CInfoDictCol(u'Участок', 15, self.clientInfoDict, 'attachName'))
        self.addColumn(CClientEvalCol(u'Контакты', ['id'], 'getClientContacts(id)', 30))
        self.addColumn(CClientEvalCol(u'Адрес проживания', ['id'], 'getClientLocAddress(id)', 30))
        self.setTable('Client')

    def addDisp(self, rows, year=None, month=None, kind=None):
        db = QtGui.qApp.db
        idList = []
        for row in rows:
            record = self.getRecordByRow(row)
            clientId = forceString(record.value('id'))
            idList.append(clientId)
        personId = QtGui.qApp.userId
        kindId = self.getSocKindId(kind)
        classId = self.getSocClassId()
        begDate = QDate(year, month, 1)
        endDate = QDate(year, month, begDate.daysInMonth())

        countCSSId = self.getCSSidCount(kindId, begDate, endDate)
        months = {0: u'Все',
                  1: u'Январь', 2: u'Февраль', 3: u'Март',
                  4: u'Апрель', 5: u'Май', 6: u'Июнь',
                  7: u'Июль', 8: u'Август', 9: u'Сентябрь',
                  10: u'Октябрь', 11: u'Ноябрь', 12: u'Декабрь'}
        kinds = {1: u'Диспансеризация раз в 3 года', 2: u'Диспансеризация раз в 2 года', 3: u'Профосмотр', 4: u'Диспансеризация ежегодная', 5: u'Диспансеризация углубленная (группа 1)', 6: u'Диспансеризация углубленная (группа 2)'}
        forPlanningCount = len(idList)
        countDispPlan = self.getDispPlanCount(kind, month, year)
        needCount = forceInt(countDispPlan) - forceInt(countCSSId)


        buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
        messageText = u'Год: {0}\n' \
                      u'Месяц: {1}\n' \
                      u'Мероприятие: {2}\n' \
                      u'Будет запланировано: {3} чел. \n' \
                      u'Ранее запланировано: {4} чел.\n' \
                      u'Подлежит планированию по плану: {5} чел.\n' \
                      u'Необходимо запланировать: {6} чел.\n' \
                      u'Продолжить планирование?'.format(year, months[month], kinds[kind], forPlanningCount, countCSSId, countDispPlan, needCount)
        messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Question,
                                       u'Внимание!',
                                       messageText,
                                       buttons,
                                       self.parent)
        messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
        messageBox.setDefaultButton(QtGui.QMessageBox.No)
        result = messageBox.exec_()
        if result == QtGui.QMessageBox.Yes:
            for clientId in idList:
                stmt = 'INSERT INTO ClientSocStatus (createDatetime, createPerson_id, client_id, ' \
                       'socStatusClass_id, socStatusType_id, begDate, endDate) ' \
                       'VALUES (NOW(), {0}, {1}, {2}, {3}, {4}, {5})'.format(personId, clientId, classId, kindId,
                                                                             db.formatDate(begDate),
                                                                             db.formatDate(endDate))
                db.query(stmt)
            self.parent.updateClientsList()
            messageBox.close()
        elif result == QtGui.QMessageBox.No:
            messageBox.close()


    def delDisp(self, rows, year):
        db = QtGui.qApp.db
        tableCSS = db.table('ClientSocStatus')
        idList = []
        for row in rows:
            record = self.getRecordByRow(row)
            id = forceString(record.value('id'))
            idList.append(id)
        cond = [tableCSS['client_id'].inlist(idList)]
        begDate = QDate(year, 1, 1)
        endDate = QDate(year, 12, 31)
        cond.append(tableCSS['begDate'].dateBetween(begDate, endDate))
        cond.append(db.joinOr([tableCSS['endDate'].dateBetween(begDate, endDate), tableCSS['endDate'].isNull()]))
        classId = self.getSocClassId()
        cond.append(tableCSS['socStatusClass_id'].eq(classId))
        forPlanningCount = len(idList)

        buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
        messageText = u'Из регистрационных карт {0} чел. будет удалено ' \
                      u'планирование \nпрофилактических мероприятий на {1} год.\n' \
                      u'Продолжить удаление?'.format(forPlanningCount, year)
        messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Question,
                                       u'Внимание!',
                                       messageText,
                                       buttons,
                                       self.parent)
        messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
        messageBox.setDefaultButton(QtGui.QMessageBox.No)
        result = messageBox.exec_()
        if result == QtGui.QMessageBox.Yes:
            db.markRecordsDeleted(tableCSS, cond)
            self.parent.updateClientsList()
            messageBox.close()
        else:
            messageBox.close()

    def getSocKindId(self, kind):
        db = QtGui.qApp.db
        kind = forceInt(kind)
        ssTypeIds = []
        if kind == 1:
            ssTypeIds = db.getIdList('rbSocStatusType', where="code = 'disp'")
        elif kind == 2:
            ssTypeIds = db.getIdList('rbSocStatusType', where="code = 'disp_2'")
        elif kind == 4:
            ssTypeIds = db.getIdList('rbSocStatusType', where="code = 'disp_1'")
        elif kind == 3:
            ssTypeIds = db.getIdList('rbSocStatusType', where="code = 'prof'")
        elif kind == 5:
            ssTypeIds = db.getIdList('rbSocStatusType', where="code = 'disp_cov1'")
        elif kind == 6:
            ssTypeIds = db.getIdList('rbSocStatusType', where="code = 'disp_cov2'")
        return ssTypeIds[0]

    def getSocClassId(self):
        db = QtGui.qApp.db
        ssClassId = forceRef(db.translate('rbSocStatusClass', 'code', 'profilac', 'id'))
        return ssClassId

    def getCSSidCount(self, kindId, begDate, endDate):
        db = QtGui.qApp.db
        tableCSS = db.table('ClientSocStatus')
        cond = []
        cond.append(tableCSS['begDate'].dateBetween(begDate, endDate))
        cond.append(tableCSS['endDate'].dateBetween(begDate, endDate))
        cond.append(tableCSS['socStatusType_id'].eq(kindId))
        cond.append(tableCSS['deleted'].eq(0))
        count = db.getCount(tableCSS, where=cond)
        return count

    def getDispPlanCount(self, kind, month, year):
        db = QtGui.qApp.db
        tableDPQ = db.table('disp_PlanQtys')
        cond = []
        if kind == 2:
            kind = 3
        elif kind == 3:
            kind = 2

        cond.append(tableDPQ['kind'].eq(kind))
        cond.append(tableDPQ['mnth'].eq(month))
        cond.append(tableDPQ['year'].eq(year))
        count = db.getRecordEx(tableDPQ, cols=tableDPQ['quantity'], where=cond)
        if count:
            cnt = forceInt(count.value('quantity'))
        else:
            cnt = 0
        return cnt


class CPlanExportErrorsModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CIntCol(u'Код ошибки', ['errorType_id'], 20),
            CDesignationCol(u'Текст ошибки', ['errorType_id'], ('disp_ErrorTypes', 'name'), 20)
            ], 'disp_PlanExportErrors')

    def update(self, planExport_id):
        if planExport_id is None:
            idList = []
        else:
            db = QtGui.qApp.db
            table = db.table('disp_PlanExportErrors')
            where = [
                table['planExport_id'].eq(planExport_id)
                ]
            idList = db.getIdList(table, idCol=table['id'], where=where)
        self.setIdList(idList)

class CFactInfosModel(CTableModel):
    def __init__(self, parent):
        infomeths = (u'',
            u'sms',
            u'email',
            u'телефон',
            u'почта',
            u'прочее')
        infosteps = (u'',
            u'приглашение на профилактическое мероприятие',
            u'напоминание о прохождении мероприятия',
            u'приглашения на второй этап диспансеризации')
        CTableModel.__init__(self, parent, [
            CTextCol(u'Код СМО', ['smo_code'], 20),
            CDateTimeCol(u'Дата', ['infodate'], 20),
            CEnumCol(u'Метод', ['infometh'], infomeths, 20),
            CEnumCol(u'Этап', ['infostep'], infosteps, 20),
            ], 'disp_FactInfos')

    def update(self, client_id, year):
        if client_id is None:
            idList = []
        else:
            db = QtGui.qApp.db
            tableFactInfos = db.table('disp_FactInfos')
            where = [
                tableFactInfos['client_id'].eq(client_id),
                tableFactInfos['year'].eq(year)
                ]
            idList = db.getIdList(tableFactInfos, where=where)
        self.setIdList(idList)

class CFactInvcsModel(CTableModel):
    def __init__(self, parent):
        invcsttss = (
            u'',
            u'счет за 1 этап',
            u'счет за 2 этап',
            u'счет за осмотр')
        CTableModel.__init__(self, parent, [
            CEnumCol(u'Месяц', ['mnth'], monthName, 20),
            CTextCol(u'Код СМО', ['smo_code'], 20),
            CDateTimeCol(u'Дата начала', ['invcdatn'], 20),
            CDateTimeCol(u'Дата окончания', ['invcdato'], 20),
            CDateTimeCol(u'Дата перс. счета', ['invcdate'], 20),
            CEnumCol(u'Статус', ['invcstts'], invcsttss, 20),
            CTextCol(u'Исход', ['ishob'], 20),
            ], 'disp_FactInvcs')

    def update(self, client_id, year):
        if client_id is None:
            idList = []
        else:
            db = QtGui.qApp.db
            tableFactInvcs = db.table('disp_FactInvcs')
            where = [
                tableFactInvcs['client_id'].eq(client_id),
                tableFactInvcs['year'].eq(year)
                ]
            idList = db.getIdList(tableFactInvcs, where=where)
        self.setIdList(idList)


class CDispExchangeReport(CReportBase):
    def __init__(self, parent, model, isShort):
        CReportBase.__init__(self, parent)
        self.model = model
        self.isShort = isShort
        self.setTitle(u'Проф. мероприятия')
        self.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape, leftMargin=1, topMargin=1, rightMargin=1,  bottomMargin=1)
        
    def build(self, description):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(description)
        cursor.insertBlock()
        if self.isShort:
            tableColumns = [
                ('35%', [u'Ф.И.О.'],       CReportBase.AlignLeft),
                ('8%',  [u'Дата рождения'], CReportBase.AlignLeft),
                ('5%',  [u'Пол'],           CReportBase.AlignLeft),
                ('32%', [u'Контакты'],      CReportBase.AlignLeft),
                ('20%',  [u'Мероприятие'],   CReportBase.AlignLeft)
            ]
        else:
            tableColumns = [
                ('10%', [u'Фамилия'],           CReportBase.AlignLeft),
                ('10%', [u'Имя'],               CReportBase.AlignLeft),
                ('10%', [u'Отчество'],          CReportBase.AlignLeft),
                ('8%',  [u'Дата рождения'],     CReportBase.AlignLeft),
                ('5%',  [u'Пол'],               CReportBase.AlignLeft),
                ('8%',  [u'Мероприятие'],       CReportBase.AlignLeft),
                ('8%',  [u'Дата начала'],       CReportBase.AlignLeft),
                ('8%',  [u'Дата окончания'],    CReportBase.AlignLeft),
                ('8%',  [u'Дата начала УД'],    CReportBase.AlignLeft),
                ('8%',  [u'Дата окончания УД'], CReportBase.AlignLeft),
                ('8%',  [u'Дата 1 этапа'],      CReportBase.AlignLeft),
                ('8%',  [u'Дата 2 этапа'],      CReportBase.AlignLeft),
                ('8%',  [u'Дата профосмотра'],  CReportBase.AlignLeft),
                ('8%',  [u'Дата 1 этапа УД'],   CReportBase.AlignLeft),
                ('8%',  [u'Дата 2 этапа УД'],   CReportBase.AlignLeft),
                ('10%', [u'Участок'],           CReportBase.AlignLeft),
                ('10%', [u'Контакты'],          CReportBase.AlignLeft),
                ('10%', [u'Адрес проживания'],  CReportBase.AlignLeft),
            ]
        table = createTable(cursor, tableColumns)
        rowCount = self.model.rowCount()
        columnCount = len(tableColumns)
        for row in xrange(0, rowCount):
            tableRow = table.addRow()
            mapColNums = {1: 3, 2: 4, 3: 16, 4: 5}
            if self.isShort:

                lastNameCol, lastName = self.model.getRecordValues(0, row)
                firstNameCol, firstName = self.model.getRecordValues(1, row)
                patrNameCol, patrName = self.model.getRecordValues(2, row)
                text = u' '.join([forceString(lastNameCol.format(lastName)),
                                  forceString(firstNameCol.format(firstName)),
                                  forceString(patrNameCol.format(patrName))])
                table.setText(tableRow, 0, text)
            for column in xrange(0 + (1 if self.isShort else 0), columnCount):
                (modelColumn, values) = self.model.getRecordValues(mapColNums[column] if self.isShort else column, row)
                text = forceString(modelColumn.format(values))
                table.setText(tableRow, column, text)
        return doc
