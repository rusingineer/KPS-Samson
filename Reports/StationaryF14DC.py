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
from PyQt4.QtCore import QDate, QDateTime, QTime

from library.MapCode    import createMapCodeToRowIdx
from library.Utils      import forceDate, forceDateTime, forceInt, forceRef, forceString

from Events.Utils       import getActionTypeIdListByFlatCode
from Events.ActionServiceType import CActionServiceType
from Orgs.Utils         import getOrgStructureFullName
from Reports.Report     import CReport, normalizeMKB
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import getPropertyAPHBP, getOrgStructureProperty, getMovingDays, countMovingDays, getKladrClientRural, dateRangeAsStr, getPropertyAPHBPName

from Reports.Ui_StationaryF14DCSetup import Ui_StationaryF14DCSetupDialog

TwoRows = [
          ( u'Всего', u'1', u'A00-T98'),
          ( u'Инфекционные и паразитарные болезни', u'2', u'A00-B99'),
          ( u'Новообразования', u'3', u'C00-D48'),
          ( u'Болезни крови и кроветворных органов', u'4', u'D50-D89'),
          ( u'Болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'5', u'E00-E90'),
          ( u'Психические расстройства и расстройства поведения', u'6', u'F00-F99'),
          ( u'Болезни нервной системы', u'7', u'G00-G99'),
          ( u'Болезни глаза и его придаточного аппарата', u'8', u'H00-H59'),
          ( u'Болезни уха и сосцевидного отростка', u'9', u'H60-H95'),
          ( u'Болезни системы кровообращения', u'10', u'I00-I99'),
          ( u'Болезни органов дыхания', u'11', u'J00-J99'),
          ( u'Болезни органов пищеварения', u'12', u'K00-K93'),
          ( u'Болезни кожи и подкожной клетчатки', u'13', u'L00-L99'),
          ( u'Болезни костно-мышечной системы и соединительной ткани', u'14', u'M00-M99'),
          ( u'Болезни мочеполовой системы', u'15', u'N00-N99'),
          ( u'Беременность, роды и послеродовой период', u'16', u'O00-O99'),
          ( u'Отдельные состояния , возникающие в перинатальном периоде…', u'17', u'P00-P96'),
          ( u'Врождённые аномалии пороки развития', u'18', u'Q00-Q99'),
          ( u'Симптомы, признаки и отклонения от нормы', u'19', u'R00-R99'),
          ( u'Травмы, отравления', u'20', u'S00-T98'),
          ( u'Кроме того факторы, влияющие на состояние здоровья населения и обращения в учреждения здравоохранения', u'21', u'Z00-Z99'),
          ( u'Оперировано больных (числа выписанных и переведённых)', u'22', u''),
          ( u'Число проведённых операций', u'23', u'')
           ]


ThreeRows = [
          ( u'Всего', u'1', u'A00-T98'),
          ( u'Инфекционные и паразитарные болезни', u'2', u'A00-B99'),
          ( u'Новообразования', u'3', u'C00-D48'),
          ( u'Болезни крови и кроветворных органов', u'4', u'D50-D89'),
          ( u'Болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'5', u'E00-E90'),
          ( u'Психические расстройства и расстройства поведения', u'6', u'F00-F99'),
          ( u'Болезни нервной системы', u'7', u'G00-G99'),
          ( u'Болезни глаза и его придаточного аппарата', u'8', u'H00-H59'),
          ( u'Болезни уха и сосцевидного отростка', u'9', u'H60-H95'),
          ( u'Болезни системы кровообращения', u'10', u'I00-I99'),
          ( u'Болезни органов дыхания', u'11', u'J00-J99'),
          ( u'Болезни органов пищеварения', u'12', u'K00-K93'),
          ( u'Болезни кожи и подкожной клетчатки', u'13', u'L00-L99'),
          ( u'Болезни костно-мышечной системы и соединительной ткани', u'14', u'M00-M99'),
          ( u'Болезни мочеполовой системы', u'15', u'N00-N99'),
          ( u'Беременность, роды и послеродовой период', u'16', u'O00-O99'),
          ( u'Отдельные состояния , возникающие в перинатальном периоде…', u'17', u'P00-P96'),
          ( u'Врождённые аномалии пороки развития', u'18', u'Q00-Q99'),
          ( u'Симптомы, признаки и отклонения от нормы', u'19', u'R00-R99'),
          ( u'Травмы, отравления', u'20', u'S00-T98'),
          ( u'Кроме того факторы, влияющие на состояние здоровья населения и обращения в учреждения здравоохранения', u'21', u'Z00-Z99'),
          ( u'Оперировано больных (числа выписанных и переведённых)', u'22', u''),
          ( u'Число проведённых операций', u'23', u'')
           ]


TwoRows2015 = [
          ( u'Всего', u'1', u'A00-T98'),
          ( u'Инфекционные и паразитарные болезни', u'2', u'A00-B99'),
          ( u'Новообразования', u'3', u'C00-D48'),
          ( u'Болезни крови и кроветворных органов', u'4', u'D50-D89'),
          ( u'Болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'5', u'E00-E90'),
          ( u'Психические расстройства и расстройства поведения', u'6', u'F00-F99'),
          ( u'Болезни нервной системы', u'7', u'G00-G99'),
          ( u'Болезни глаза и его придаточного аппарата', u'8', u'H00-H59'),
          ( u'Болезни уха и сосцевидного отростка', u'9', u'H60-H95'),
          ( u'Болезни системы кровообращения', u'10', u'I00-I99'),
          ( u'Болезни органов дыхания', u'11', u'J00-J99'),
          ( u'Болезни органов пищеварения', u'12', u'K00-K93'),
          ( u'Болезни кожи и подкожной клетчатки', u'13', u'L00-L98'),
          ( u'Болезни костно-мышечной системы и соединительной ткани', u'14', u'M00-M99'),
          ( u'Болезни мочеполовой системы', u'15', u'N00-N99'),
          ( u'Беременность, роды и послеродовой период', u'16', u'O00-O99'),
          ( u'Врождённые аномалии пороки развития', u'17', u'Q00-Q99'),
          ( u'Симптомы, признаки и отклонения от нормы', u'18', u'R00-R99'),
          ( u'Травмы, отравления', u'19', u'S00-T98'),
          ( u'Кроме того факторы, влияющие на состояние здоровья населения и обращения в учреждения здравоохранения', u'20', u'Z00-Z99'),
          ( u'Оперировано больных (числа выписанных и переведённых)', u'21', u''),
          ( u'Число проведённых операций', u'22', u'')
           ]


ThreeRows2015 = [
          ( u'Всего', u'1', u'A00-T98'),
          ( u'Инфекционные и паразитарные болезни', u'2', u'A00-B99'),
          ( u'Новообразования', u'3', u'C00-D48'),
          ( u'Болезни крови и кроветворных органов', u'4', u'D50-D89'),
          ( u'Болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'5', u'E00-E90'),
          ( u'Психические расстройства и расстройства поведения', u'6', u'F00-F99'),
          ( u'Болезни нервной системы', u'7', u'G00-G99'),
          ( u'Болезни глаза и его придаточного аппарата', u'8', u'H00-H59'),
          ( u'Болезни уха и сосцевидного отростка', u'9', u'H60-H95'),
          ( u'Болезни системы кровообращения', u'10', u'I00-I99'),
          ( u'Болезни органов дыхания', u'11', u'J00-J99'),
          ( u'Болезни органов пищеварения', u'12', u'K00-K93'),
          ( u'Болезни кожи и подкожной клетчатки', u'13', u'L00-L98'),
          ( u'Болезни костно-мышечной системы и соединительной ткани', u'14', u'M00-M99'),
          ( u'Болезни мочеполовой системы', u'15', u'N00-N99'),
          ( u'Беременность, роды и послеродовой период', u'16', u'O00-O99'),
          ( u'Врождённые аномалии пороки развития', u'17', u'Q00-Q99'),
          ( u'Симптомы, признаки и отклонения от нормы', u'18', u'R00-R99'),
          ( u'Травмы, отравления', u'19', u'S00-T98'),
          ( u'Кроме того факторы, влияющие на состояние здоровья населения и обращения в учреждения здравоохранения', u'20', u'Z00-Z99'),
          ( u'Оперировано больных (числа выписанных и переведённых)', u'21', u''),
          ( u'Число проведённых операций', u'22', u'')
           ]


class CStationaryF14DCSetupDialog(QtGui.QDialog, Ui_StationaryF14DCSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbGroupMES.setTable('mes.mrbMESGroup', addNone=True)
        self.lblSpecialDeliverClient.setVisible(False)
        self.cmbSpecialDeliverClient.setVisible(False)
        self.cmbSocStatusClass.setTable('rbSocStatusClass', True)
        self.cmbSocStatusType.setTable('rbSocStatusType', True)
        self.cmbFinance.setTable('rbFinance', addNone=True)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.chkGroupingForMES.setChecked(params.get('groupingForMES', False))
        self.cmbGroupMES.setValue(params.get('groupMES', None))
        self.cmbMes.setValue(params.get('MES', None))
        self.cmbDurationType.setCurrentIndex(params.get('durationType', 0))
        self.cmbSocStatusClass.setValue(params.get('socStatusClassId', None))
        self.cmbSocStatusType.setValue(params.get('socStatusTypeId', None))
        self.cmbFinance.setValue(params.get('financeId', None))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['groupingForMES'] = self.chkGroupingForMES.isChecked()
        result['groupMES'] = self.cmbGroupMES.value()
        result['MES'] = self.cmbMes.value()
        result['durationType'] = self.cmbDurationType.currentIndex()
        result['socStatusClassId'] = self.cmbSocStatusClass.value()
        result['socStatusTypeId'] = self.cmbSocStatusType.value()
        result['financeId'] = self.cmbFinance.value()
        return result


class CReportStationary(CReport):
    def __init__(self, parent = None):
        CReport.__init__(self, parent)
        self.clientDeath = 8
        self.deathLeavedStationary = 0
        self.deathLeavedStationaryChild = 0
        self.deathLeavedAmbulance = 0
        self.deathLeavedAmbulanceChild = 0
        self.deathLeavedHouse = 0
        self.deathLeavedHouseChild = 0
        self.deathRuralLeavedStationary= 0
        self.deathRuralLeavedAmbulance = 0
        self.deathRuralLeavedHouse = 0
        self.byActions = True
        self.params = {}


    def getSetupDialog(self, parent):
        result = CStationaryF14DCSetupDialog(parent)
        self.stationaryF14DCSetupDialog = result
        return result


    def getOrgStructureIdList(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    def getOrgStructureTypeIdList(self, orgStructureIdList, isHospital):
        db = QtGui.qApp.db
        tableOS = db.table('OrgStructure')
        if not orgStructureIdList:
           orgStructureIdList = db.getDistinctIdList(tableOS, 'id', [tableOS['deleted'].eq(0), tableOS['type'].eq(0)])
        if orgStructureIdList and isHospital != 2:
            cond = [tableOS['deleted'].eq(0),
                    tableOS['id'].inlist(orgStructureIdList)
                    ]
            typeStr = u''
            isHospitalStr = u''
            if isHospital == 0:
                typeStr = u' AND OS.type != 0'
                isHospitalStr =  u' AND Organisation.isHospital = 1'
            elif isHospital == 1:
                typeStr = u' AND OS.type = 0'
                isHospitalStr =  u' AND Organisation.isHospital = 0'
            cond.append('''((OrgStructure.parent_id IS NOT NULL AND
            EXISTS(SELECT OS.id
            FROM OrgStructure AS OS
            WHERE OS.id = OrgStructure.parent_id %s AND OS.deleted = 0)
            )
            OR (OrgStructure.parent_id IS NULL AND
            EXISTS(SELECT Organisation.id
            FROM Organisation
            WHERE Organisation.deleted = 0 AND Organisation.id = OrgStructure.organisation_id %s)))''' % (typeStr, isHospitalStr)
            )
            return db.getDistinctIdList(tableOS, tableOS['id'].name(), cond)
        elif isHospital == 2:
           return orgStructureIdList #WTF?
        return []


    def dumpParams(self, cursor, params):
        description = []
        self.params = params
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if begDate and endDate:
            description.append(dateRangeAsStr(u'за период', begDate, endDate))
        orgStructureId = params.get('orgStructureId', None)
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        durationType = params.get('durationType', 0)
        description.append(u'расчет длительности пребывания %s'%([u'по визитам', u'по случаю', u'по действиям'][durationType]))
        if params.get('groupingForMES', False):
            description.append(u'учитывать МЭС')
            groupMES = params.get('groupMES', None)
            if groupMES:
                description.append(u'Группа МЭС: %s'%(forceString(QtGui.qApp.db.translate('mes.mrbMESGroup', 'id', groupMES, 'name'))))
            MES = params.get('MES', None)
            if MES:
                description.append(u'МЭС: %s'%(forceString(QtGui.qApp.db.translate('mes.MES', 'id', MES, 'name'))))
        socStatusClassId = params.get('socStatusClassId', None)
        if socStatusClassId:
            description.append(u'класс соц.статуса: %s'%(forceString(QtGui.qApp.db.translate('rbSocStatusClass', 'id', socStatusClassId, 'name'))))
        socStatusTypeId  = params.get('socStatusTypeId', None)
        if socStatusTypeId:
            description.append(u'тип соц.статуса: %s'%(forceString(QtGui.qApp.db.translate('rbSocStatusType', 'id', socStatusTypeId, 'name'))))
        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getProfilEventHospital(self, eventIdList):
        if eventIdList:
            db = QtGui.qApp.db
            tableVisit = db.table('Visit')
            tableEvent = db.table('Event')
            tableRBHBP = db.table('rbHospitalBedProfile')
            tableRBScene = db.table('rbScene')
            cond = [ tableVisit['event_id'].inlist(eventIdList),
                     tableEvent['deleted'].eq(0),
                     tableVisit['deleted'].eq(0),
                     'DATE(Event.setDate) <= DATE(Visit.date)',
                     tableRBScene['code'].eq(2)
                   ]
            queryTable = tableEvent.innerJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableRBHBP, tableVisit['service_id'].eq(tableRBHBP['id']))
            queryTable = queryTable.innerJoin(tableRBScene, tableRBScene['id'].eq(tableVisit['scene_id']))
            cond.append('''Visit.event_id = Event.id AND Visit.deleted = 0
                AND Visit.id = (SELECT MIN(VMI.id) FROM Visit AS VMI WHERE VMI.event_id = Event.id AND VMI.deleted = 0
                AND DATE(VMI.date) = DATE((SELECT MIN(VMD.date) FROM Visit AS VMD WHERE VMD.event_id = Event.id
                AND VMD.deleted = 0))))''')
            return db.getRecordList(queryTable, 'DISTINCT rbHospitalBedProfile.id, rbHospitalBedProfile.name, rbHospitalBedProfile.code', cond, 'Event.id, Visit.date ASC')
        return []

    def getDataEventHospital(self, orgStructureIdList, begDate, endDate, profileIdList, isHospital, groupingForMES, groupMES, MES, financeId):
        if self.byActions and isHospital != 2:
            return self.getDataEventHospitalByActions(orgStructureIdList, begDate, endDate, profileIdList, isHospital, groupingForMES, groupMES, MES, financeId=financeId)
        else:
            return self.getDataEventHospitalByVisits(orgStructureIdList, begDate, endDate, profileIdList, isHospital, groupingForMES, groupMES, MES, financeId)

    def getDataEventHospitalByActions(self, orgStructureIdList, begDate, endDate, profileIdList, isHospital, groupingForMES, groupMES, MES, addFinance = False, financeId = None):
        if orgStructureIdList:
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableA = db.table('Action').alias('A')
            tableActionType = db.table('ActionType')
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tableClient = db.table('Client')
            tableVisit = db.table('Visit')
            tableMES = db.table('mes.MES')
            tableGroupMES = db.table('mes.mrbMESGroup')
            tableRBMedicalAidType = db.table('rbMedicalAidType')
            tableContract = db.table('Contract')
            tableFinance = db.table('rbFinance')
            cond = [ tableEvent['deleted'].eq(0),
                     tableEventType['deleted'].eq(0),
                     tableA['deleted'].eq(0),
                     db.joinOr([tableActionType['flatCode'].eq('leaved'), tableActionType['flatCode'].eq('received')])
                   ]
            queryTable = tableEvent.innerJoin(tableA, tableA['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableA['actionType_id']))
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            queryTable = queryTable.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
            queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            if groupingForMES:
                cond.append(tableEvent['MES_id'].isNotNull())
                if groupMES or MES:
                    queryTable = queryTable.innerJoin(tableMES, tableEvent['MES_id'].eq(tableMES['id']))
                    cond.append(tableMES['deleted'].eq(0))
                    if MES:
                        cond.append(tableEvent['MES_id'].eq(MES))
                    if groupMES:
                        queryTable = queryTable.innerJoin(tableGroupMES, tableMES['group_id'].eq(tableGroupMES['id']))
                        cond.append(tableGroupMES['deleted'].eq(0))
                        cond.append(tableMES['group_id'].eq(groupMES))
            if financeId:
                cond.append(tableContract['finance_id'].eq(financeId))
            cond.append(tableEvent['execDate'].isNotNull())
            cond.append(tableEvent['execDate'].ge(begDate))
            cond.append(tableEvent['setDate'].lt(endDate.addDays(1)))
            cond.append(tableRBMedicalAidType['code'].eq(7))
            socStatusClassId = self.params.get('socStatusClassId', None)
            socStatusTypeId  = self.params.get('socStatusTypeId', None)
            if socStatusClassId or socStatusTypeId:
                tableClientSocStatus = db.table('ClientSocStatus')
                if begDate:
                    cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                       tableClientSocStatus['endDate'].ge(begDate)
                                                      ]),
                                           tableClientSocStatus['endDate'].isNull()
                                          ]))
                if endDate:
                    cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                       tableClientSocStatus['begDate'].lt(endDate.addDays(1))
                                                      ]),
                                           tableClientSocStatus['begDate'].isNull()
                                          ]))
                queryTable = queryTable.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
                if socStatusClassId:
                    cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
                if socStatusTypeId:
                    cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
                cond.append(tableClientSocStatus['deleted'].eq(0))
#            if isHospital == 2:
#                queryTable = queryTable.innerJoin(tableRBScene, tableRBScene['id'].eq(tableVisit['scene_id']))
#                cond.append(tableRBScene['code'].eq(2))
            cond.append(u'''EXISTS( SELECT
                    APOS2.value
                FROM
                    ActionPropertyType AS APT2
                        INNER JOIN
                    ActionProperty AS AP2 ON AP2.type_id = APT2.id
                        INNER JOIN
                    ActionProperty_OrgStructure AS APOS2 ON APOS2.id = AP2.id
                        INNER JOIN
                    OrgStructure AS OS2 ON OS2.id = APOS2.value
                WHERE
                    APT2.actionType_id = A.actionType_id
                        AND AP2.action_id = A.id
                        AND APT2.deleted = 0
                        AND (APT2.name = 'Отделение'
                            OR APT2.name = 'Направлен в отделение')
                        AND OS2.deleted = 0
                        AND APOS2.value IN (%s))'''%','.join(map(str,  orgStructureIdList)))
            eventIdList = db.getDistinctIdList(queryTable, 'Event.id', cond, 'Event.id, A.begDate ASC')
            if eventIdList:
                table = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
                table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))

                cond = [tableEvent['deleted'].eq(0),
                            tableActionType['flatCode'].eq('leaved'),
                        tableEvent['id'].inlist(eventIdList)]

                cols = [getPropertyAPHBPName(False, False, 'id', 'bedProfile'),

                    ]

                movingIdList = getActionTypeIdListByFlatCode(u'moving')
                receivedIdList = getActionTypeIdListByFlatCode(u'received')
                leavedIdList = getActionTypeIdListByFlatCode(u'leaved')
                if movingIdList and receivedIdList and leavedIdList:
                    cols.append(u'''(SELECT COUNT(A.id)
                            FROM Action AS A
                                WHERE A.actionType_id IN (%s)
                                AND A.event_id = Event.id
                                AND A.deleted=0) AS countActions''' % (','.join(str(movingId) for movingId in movingIdList)))

                    cols.append(u'''(select A.id
                            FROM Action AS A
                                WHERE A.actionType_id IN (%s)
                                AND A.event_id = Event.id  ) AS visitReceivedId'''%(','.join(str(receivedId) for receivedId in receivedIdList)))

                    cols.append(u'''(select DATE(A.begDate)
                            FROM Action AS A
                                WHERE A.actionType_id IN (%s)
                                AND A.event_id = Event.id  ) AS visitReceivedDate'''%(','.join(str(receivedId) for receivedId in receivedIdList)))

                    cols.append(u'''(select A.id
                            FROM Action AS A
                                WHERE A.actionType_id IN (%s)
                                AND A.event_id = Event.id  ) AS visitLeavedId'''%(','.join(str(leavedId) for leavedId in leavedIdList)))

                    cols.append(u'''(select DATE(A.begDate)
                            FROM Action AS A
                                WHERE A.actionType_id IN (%s)
                                AND A.event_id = Event.id  AND A.deleted = 0) AS visitLeavedDate'''%(','.join(str(leavedId) for leavedId in leavedIdList)))

                    cols.append(u'''(SELECT rbResult.name
                            FROM
                                rbResult
                            WHERE
                                rbResult.id = Event.result_id
                            LIMIT 1) AS deathLeaved''')

                    cols.append(u'''(select IF(Action.id,1,0)
                            FROM Action AS A
                                WHERE A.actionType_id IN (%s)
                                AND A.event_id = Event.id  AND (%s)) AS deathRuralLeaved'''%(','.join(str(leavedId) for leavedId in leavedIdList), getKladrClientRural()))

                    cols.append(u'''age(Client.birthDate, Event.setDate) AS ageClient''')

                    cols.append(u'''EXISTS( SELECT rbResult.name
                            FROM rbResult
                            WHERE
                                rbResult.id = Event.result_id
                                    AND rbResult.name LIKE '%круглосуточный стационар%') AS countTransfer''')

                    cols.append(u'''(SELECT COUNT(VC.id)
                        FROM Visit AS VC
                        WHERE VC.event_id = Event.id AND VC.deleted = 0 AND (DATE(VC.date) >= %s AND DATE(VC.date) <= %s)) AS countVisit'''%(db.formatDate(begDate), db.formatDate(endDate)))


                    cols.append(u'''Event.setDate, Event.execDate''')

                    table = tableEvent.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
                    table = table.leftJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))
                    table = table.leftJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
                    table = table.leftJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))

                    if addFinance:
                        cols.append(u"Action.finance_id as visitFinanceId")
                        table = table.leftJoin(tableFinance, tableFinance['id'].eq(tableContract['finance_id']))
                        cols.append(u"Contract.finance_id as contractFinanceId")
                        cols.append(u"rbFinance.name as contractFinanceName")
                        socStatusClassId = self.params.get('socStatusClassId', None)
                        socStatusTypeId  = self.params.get('socStatusTypeId', None)
                        if socStatusClassId or socStatusTypeId:
                            tableClientSocStatus = db.table('ClientSocStatus')
                            if begDate:
                                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                                   tableClientSocStatus['endDate'].ge(begDate)
                                                                  ]),
                                                       tableClientSocStatus['endDate'].isNull()
                                                      ]))
                            if endDate:
                                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                                   tableClientSocStatus['begDate'].lt(endDate.addDays(1))
                                                                  ]),
                                                       tableClientSocStatus['begDate'].isNull()
                                                      ]))
                            table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
                            if socStatusClassId:
                                cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
                            if socStatusTypeId:
                                cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
                            cond.append(tableClientSocStatus['deleted'].eq(0))
                stmtVisit = db.selectStmtGroupBy(table, cols, cond, tableEvent['id'].name())
                return db.query(stmtVisit), eventIdList
        return None, None

    def getDataEventHospitalByVisits(self, orgStructureIdList, begDate, endDate, profileIdList, isHospital, groupingForMES, groupMES, MES, financeId):
        if orgStructureIdList:
            db = QtGui.qApp.db
            tableVisit = db.table('Visit')
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tableRBScene = db.table('rbScene')
            tablePerson = db.table('Person')
            tableOS = db.table('OrgStructure')
            tableMES = db.table('mes.MES')
            tableGroupMES = db.table('mes.mrbMESGroup')
            tableRBMedicalAidType = db.table('rbMedicalAidType')
            tableContract = db.table('Contract')

            cond = [ tableEvent['deleted'].eq(0),
                     tablePerson['deleted'].eq(0),
                     tableEventType['deleted'].eq(0),
                     tableVisit['deleted'].eq(0),
                     'DATE(Event.setDate) <= DATE(Visit.date)',
                   ]
            queryTable = tableEvent.innerJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
            queryTable = queryTable.leftJoin(tableOS, tablePerson['orgStructure_id'].eq(tableOS['id']))
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            queryTable = queryTable.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
            queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            if groupingForMES:
                cond.append(tableEvent['MES_id'].isNotNull())
                if groupMES or MES:
                    queryTable = queryTable.innerJoin(tableMES, tableEvent['MES_id'].eq(tableMES['id']))
                    cond.append(tableMES['deleted'].eq(0))
                    if MES:
                        cond.append(tableEvent['MES_id'].eq(MES))
                    if groupMES:
                        queryTable = queryTable.innerJoin(tableGroupMES, tableMES['group_id'].eq(tableGroupMES['id']))
                        cond.append(tableGroupMES['deleted'].eq(0))
                        cond.append(tableMES['group_id'].eq(groupMES))
            if financeId:
                cond.append(tableContract['finance_id'].eq(financeId))
            cond.append(tableEvent['execDate'].isNotNull())
            cond.append(tableEvent['execDate'].ge(begDate))
            cond.append(tableEvent['execDate'].le(endDate))
            cond.append(tableRBMedicalAidType['code'].eq(7))
            cond.append(tableOS['deleted'].eq(0))
            cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
            if isHospital == 2:
                queryTable = queryTable.innerJoin(tableRBScene, tableRBScene['id'].eq(tableVisit['scene_id']))
                cond.append(tableRBScene['code'].eq(2))
#            if profileIdList:
#                cond.append('''EXISTS(SELECT V.id FROM Visit AS V INNER JOIN rbHospitalBedProfile ON rbHospitalBedProfile.service_id = V.service_id
#                WHERE rbHospitalBedProfile.id IN (%s) AND V.event_id = Event.id AND V.deleted = 0
#                AND V.id = (SELECT MIN(VMI.id) FROM Visit AS VMI WHERE VMI.event_id = Event.id AND VMI.deleted = 0
#                AND DATE(VMI.date) = DATE((SELECT MIN(VMD.date) FROM Visit AS VMD WHERE VMD.event_id = Event.id
#                AND VMD.deleted = 0))))'''%(','.join(str(profileId) for profileId in profileIdList if profileId)))
            eventIdList = db.getDistinctIdList(queryTable, 'Event.id', cond, 'Event.id, Visit.date ASC')
            if eventIdList:
                movingIdList = getActionTypeIdListByFlatCode(u'moving%')
                stmtVisit = u'''SELECT
   (select rbHospitalBedProfile.id
    from Action AS HospitalAction
    left join ActionPropertyType on ActionPropertyType.name = 'койка' and ActionPropertyType.actionType_id = HospitalAction.actionType_id and ActionPropertyType.deleted = 0
    left join ActionProperty on ActionProperty.type_id = ActionPropertyType.id and ActionProperty.action_id = HospitalAction.id and ActionProperty.deleted = 0
    left join ActionProperty_HospitalBed on ActionProperty_HospitalBed.id = ActionProperty.id
    left join OrgStructure_HospitalBed on OrgStructure_HospitalBed.id = ActionProperty_HospitalBed.value
    left join rbHospitalBedProfile on rbHospitalBedProfile.id = OrgStructure_HospitalBed.profile_id
    where HospitalAction.id = (
        SELECT MAX(A.id)
        FROM Action A
        WHERE A.event_id = Event.id AND
            A.deleted = 0 AND
            A.actionType_id IN (
                SELECT AT.id
                FROM ActionType AT
                WHERE AT.flatCode ='moving'
                AND AT.deleted = 0
                )
            ) and HospitalAction.id is not NULL) AS bedProfile,

    %s

    (SELECT MIN(VIDMin.id)
    FROM Visit AS VIDMin
    WHERE VIDMin.event_id = Event.id AND VIDMin.deleted = 0
    AND DATE(VIDMin.date) = DATE((SELECT MIN(V.date) FROM Visit AS V WHERE V.event_id = Event.id))) AS visitReceivedId,

    (SELECT MIN(V.date) FROM Visit AS V WHERE V.event_id = Event.id AND V.deleted = 0) AS visitReceivedDate,

    (SELECT MAX(VIDMax.id)
    FROM Visit AS VIDMax
    WHERE VIDMax.event_id = Event.id AND  VIDMax.deleted = 0
    AND DATE(VIDMax.date) = DATE((SELECT MAX(V.date) FROM Visit AS V WHERE V.event_id = Event.id
    AND V.deleted = 0 AND Event.execDate IS NOT NULL))) AS visitLeavedId,

    (SELECT MAX(V.date)
    FROM Visit AS V
    WHERE V.event_id = Event.id AND V.deleted = 0 AND Event.execDate IS NOT NULL) AS visitLeavedDate,

    (SELECT rbResult.name FROM rbResult WHERE rbResult.id = Event.result_id
    LIMIT 1) AS deathLeaved,

    (SELECT MAX(VIDMax.id)
    FROM Visit AS VIDMax
    WHERE VIDMax.event_id = Event.id AND  VIDMax.deleted = 0 AND %s
    AND DATE(VIDMax.date) = DATE((SELECT MAX(V.date) FROM Visit AS V WHERE V.event_id = Event.id
    AND V.deleted = 0 AND Event.execDate IS NOT NULL))) AS deathRuralLeaved,

    age(Client.birthDate, Event.setDate) AS ageClient,

    EXISTS(SELECT rbResult.name
    FROM rbResult WHERE rbResult.id = Event.result_id
    AND rbResult.name LIKE '%%круглосуточный стационар%%') AS countTransfer,

    (SELECT COUNT(VC.id)
    FROM Visit AS VC
    WHERE VC.event_id = Event.id AND VC.deleted = 0 AND (DATE(VC.date) >= %s AND DATE(VC.date) <= %s)) AS countVisit,

    Event.setDate, Event.execDate,
    WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode) as PD

    FROM Event
    LEFT JOIN EventType ON EventType.id = Event.eventType_id
    INNER JOIN Visit ON Visit.event_id=Event.id
    LEFT JOIN rbService on rbService.id = Visit.service_id
    LEFT JOIN rbMedicalAidType mt ON mt.id = ifnull(rbService.medicalAidType_id, EventType.medicalAidType_id)
    INNER JOIN Client ON Event.client_id=Client.id

    WHERE (Event.deleted=0) AND (Client.deleted = 0) AND (Visit.deleted=0) AND Event.id IN (%s)

    GROUP BY Event.id
    ORDER BY Event.id, Visit.date ASC'''%((u'''(SELECT COUNT(A.id)
    FROM Action AS A WHERE A.actionType_id IN (%s) AND A.event_id = Event.id AND A.deleted=0) AS countActions,''' % (','.join(str(movingId) for movingId in movingIdList))) if movingIdList else u'',
    getKladrClientRural(), db.formatDate(begDate), db.formatDate(endDate), u','.join(str(eventId) for eventId in eventIdList if eventId))
                return db.query(stmtVisit), eventIdList
        return None, None


    def unrolledHospitalBedEvent(self, orgStructureIdList, begDate, endDate, reportLineList, profile = None):
        if orgStructureIdList:
            db = QtGui.qApp.db
            tableOSHB = db.table('OrgStructure_HospitalBed')
            tableOS = db.table('OrgStructure')
            tableHBSchedule = db.table('rbHospitalBedShedule')
            queryTable = tableOSHB.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
            cond = [tableOSHB['master_id'].inlist(orgStructureIdList),
                    tableOS['deleted'].eq(0)
                    ]
            queryTable = queryTable.innerJoin(tableHBSchedule, tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
            cond.append(tableHBSchedule['code'].ne(1))
            joinOr1 = db.joinOr([tableOSHB['begDate'].isNull(), tableOSHB['begDate'].ge(begDate)])
            joinOr2 = db.joinOr([tableOSHB['begDate'].isNull(), tableOSHB['begDate'].lt(endDate)])
            cond.append(db.joinAnd([joinOr1, joinOr2]))
            cond.append(tableOSHB['profile_id'].eq(profile))
            countBeds = db.getCount(queryTable, countCol='OrgStructure_HospitalBed.id', where=cond)
            reportLineAll = reportLineList.get('', None)
            if reportLineAll:
                reportLineAll['countBed'] += countBeds
                reportLineList[''] = reportLineAll
            reportLine = reportLineList.get(profile, None)
            if reportLine:
                reportLine['countBed'] += countBeds
                reportLineList[profile] = reportLine
        return reportLineList


    def averageYarHospitalBedEvent(self, orgStructureIdList, begDate, endDate, reportLineList, profile = None):
        if orgStructureIdList:
            begDatePeriod = QDate(begDate.year(), 1, 1)
            endDatePeriod = begDatePeriod.addMonths(12)
            countReceived = self.getReceived(begDatePeriod, endDatePeriod, orgStructureIdList, u'Направлен в отделение', profile)
            reportLineAll = reportLineList.get('', None)
            if reportLineAll:
                reportLineAll['countAverageBed'] += countReceived/12
                reportLineList[''] = reportLineAll
            reportLine = reportLineList.get(profile, None)
            if reportLine:
                reportLine['countAverageBed'] += countReceived/12
                reportLineList[profile] = reportLine
        return reportLineList


    def getDataEventAdult(self, orgStructureIdList, begDate, endDate, ageChildren, isHospital, groupingForMES, groupMES, MES, financeId):
        if self.byActions and isHospital == 0:
            return self.getDataEventAdultByActions(orgStructureIdList, begDate, endDate, ageChildren, isHospital, groupingForMES, groupMES, MES, financeId)
        else:
            return self.getDataEventAdultByVisits(orgStructureIdList, begDate, endDate, ageChildren, isHospital, groupingForMES, groupMES, MES, financeId)

    def getDataEventAdultByActions(self, orgStructureIdList, begDate, endDate, ageChildren, isHospital, groupingForMES, groupMES, MES, financeId):
        if orgStructureIdList:
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableA = db.table('Action').alias('A')
            tableActionType = db.table('ActionType')
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tableClient = db.table('Client')
            tableVisit = db.table('Visit')
            tableMES = db.table('mes.MES')
            tableGroupMES = db.table('mes.mrbMESGroup')
            tableRBMedicalAidType = db.table('rbMedicalAidType')
            tableDiagnostic = db.table('Diagnostic')
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnosisType = db.table('rbDiagnosisType')
            tableContract = db.table('Contract')

            cond = [ tableEvent['deleted'].eq(0),
                     tableEventType['deleted'].eq(0),
                     tableA['deleted'].eq(0),
                     db.joinOr([tableActionType['flatCode'].eq('leaved'), tableActionType['flatCode'].eq('received')]),
                     ageChildren
                   ]
            queryTable = tableEvent.innerJoin(tableA, tableA['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableA['actionType_id']))
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            queryTable = queryTable.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
            queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            if groupingForMES:
                cond.append(tableEvent['MES_id'].isNotNull())
                if groupMES or MES:
                    queryTable = queryTable.innerJoin(tableMES, tableEvent['MES_id'].eq(tableMES['id']))
                    cond.append(tableMES['deleted'].eq(0))
                    if MES:
                        cond.append(tableEvent['MES_id'].eq(MES))
                    if groupMES:
                        queryTable = queryTable.innerJoin(tableGroupMES, tableMES['group_id'].eq(tableGroupMES['id']))
                        cond.append(tableGroupMES['deleted'].eq(0))
                        cond.append(tableMES['group_id'].eq(groupMES))
            if financeId:
                cond.append(tableContract['finance_id'].eq(financeId))
            cond.append(tableEvent['execDate'].isNotNull())
            cond.append(tableEvent['execDate'].ge(begDate))
            cond.append(tableEvent['setDate'].lt(endDate.addDays(1)))
            cond.append(tableRBMedicalAidType['code'].eq(7))
            socStatusClassId = self.params.get('socStatusClassId', None)
            socStatusTypeId  = self.params.get('socStatusTypeId', None)
            if socStatusClassId or socStatusTypeId:
                tableClientSocStatus = db.table('ClientSocStatus')
                if begDate:
                    cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                       tableClientSocStatus['endDate'].ge(begDate)
                                                      ]),
                                           tableClientSocStatus['endDate'].isNull()
                                          ]))
                if endDate:
                    cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                       tableClientSocStatus['begDate'].lt(endDate.addDays(1))
                                                      ]),
                                           tableClientSocStatus['begDate'].isNull()
                                          ]))
                queryTable = queryTable.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
                if socStatusClassId:
                    cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
                if socStatusTypeId:
                    cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
                cond.append(tableClientSocStatus['deleted'].eq(0))
#            if isHospital == 2:
#                queryTable = queryTable.innerJoin(tableRBScene, tableRBScene['id'].eq(tableVisit['scene_id']))
#                cond.append(tableRBScene['code'].eq(2))
            cond.append(u'''EXISTS( SELECT
                    APOS2.value
                FROM
                    ActionPropertyType AS APT2
                        INNER JOIN
                    ActionProperty AS AP2 ON AP2.type_id = APT2.id
                        INNER JOIN
                    ActionProperty_OrgStructure AS APOS2 ON APOS2.id = AP2.id
                        INNER JOIN
                    OrgStructure AS OS2 ON OS2.id = APOS2.value
                WHERE
                    APT2.actionType_id = A.actionType_id
                        AND AP2.action_id = A.id
                        AND APT2.deleted = 0
                        AND (APT2.name = 'Отделение'
                            OR APT2.name = 'Направлен в отделение')
                        AND OS2.deleted = 0
                        AND APOS2.value IN (%s))'''%','.join(map(str,  orgStructureIdList)))
            eventIdList = db.getDistinctIdList(queryTable, 'Event.id', cond, 'Event.id, A.begDate ASC')
            if eventIdList:
                table = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
                table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))

                cond = [tableEvent['deleted'].eq(0),
                            tableActionType['flatCode'].eq('leaved'),
                        tableEvent['id'].inlist(eventIdList)]

                cols = ['Diagnosis.MKB'
                    ]

                movingIdList = getActionTypeIdListByFlatCode(u'moving')
                receivedIdList = getActionTypeIdListByFlatCode(u'received')
                leavedIdList = getActionTypeIdListByFlatCode(u'leaved')
                if movingIdList and receivedIdList and leavedIdList:
                    cols.append(u'''(SELECT COUNT(A.id)
                            FROM Action AS A
                                WHERE A.actionType_id IN (%s)
                                AND A.event_id = Event.id
                                AND A.deleted=0) AS countActions''' % (','.join(str(movingId) for movingId in movingIdList)))

                    cols.append(u'''EXISTS( SELECT Organisation.isMedical
                                FROM Organisation
                                    INNER JOIN
                                Event AS E ON E.relegateOrg_id = Organisation.id
                            WHERE
                                E.id = Event.id
                                    AND Organisation.isMedical = 3
                                    AND Organisation.deleted = 0) AS relegateOrg''')

                    cols.append(u'''EXISTS(SELECT Diagnostic.healthGroup_id FROM Diagnostic INNER JOIN rbHealthGroup ON rbHealthGroup.id = Diagnostic.diagnosis_id
WHERE Diagnostic.deleted = 0 AND rbHealthGroup.code = 1 LIMIT 1) AS healthGroup''')

                    cols.append(u'''(select A.endDate
                            FROM Action AS A
                                WHERE A.actionType_id IN (%s)
                                AND A.event_id = Event.id AND A.deleted = 0) AS visitLeavedDate'''%(','.join(str(leavedId) for leavedId in leavedIdList)))

                    cols.append(u'''EXISTS( SELECT rbResult.name
                            FROM rbResult
                            WHERE
                                rbResult.id = Event.result_id
                                    AND rbResult.name LIKE '%круглосуточный стационар%') AS countTransfer''')

                    cols.append(u'''EXISTS( SELECT
                                rbResult.name
                            FROM
                                rbResult
                            WHERE
                                rbResult.id = Event.result_id
                                    AND (rbResult.code = 99
                                    OR rbResult.name LIKE '%умер%'
                                    OR rbResult.name LIKE '%смерть%')) AS countDeath''')

                    cols.append(u'''age(Client.birthDate, Event.setDate) AS ageClient''')

                    cols.append(u'''(SELECT SUM(A.amount)
                        FROM
                            Action AS A
                                INNER JOIN
                            ActionType AS AT ON A.actionType_id = AT.id
                        WHERE
                            A.event_id = Event.id AND A.deleted = 0
                                AND AT.deleted = 0
                                AND A.endDate IS NOT NULL
                                AND AT.class = 2
                                AND AT.serviceType = %d) AS countSurgery'''%(CActionServiceType.operation))

                    cols.append(u'''(SELECT COUNT(VC.id)
                        FROM Visit AS VC
                        WHERE VC.event_id = Event.id AND VC.deleted = 0 AND (DATE(VC.date) >= %s AND DATE(VC.date) <= %s)) AS countVisit'''%(db.formatDate(begDate), db.formatDate(endDate)))


                    cols.append(u'''Event.setDate, Event.execDate''')

                    table = tableEvent.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
                    table = table.leftJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))
                    table = table.leftJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
                    table = table.leftJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
                    table = table.innerJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
                    table = table.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
                    table = table.innerJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id']))
                    socStatusClassId = self.params.get('socStatusClassId', None)
                    socStatusTypeId  = self.params.get('socStatusTypeId', None)
                    if socStatusClassId or socStatusTypeId:
                        tableClientSocStatus = db.table('ClientSocStatus')
                        if begDate:
                            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                               tableClientSocStatus['endDate'].ge(begDate)
                                                              ]),
                                                   tableClientSocStatus['endDate'].isNull()
                                                  ]))
                        if endDate:
                            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                               tableClientSocStatus['begDate'].lt(endDate.addDays(1))
                                                              ]),
                                                   tableClientSocStatus['begDate'].isNull()
                                                  ]))
                        table = table.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
                        if socStatusClassId:
                            cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
                        if socStatusTypeId:
                            cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
                        cond.append(tableClientSocStatus['deleted'].eq(0))
                stmtVisit = db.selectStmtGroupBy(table, cols, cond, tableEvent['id'].name())
                return db.query(stmtVisit)
        return None

    def getDataEventAdultByVisits(self, orgStructureIdList, begDate, endDate, ageChildren, isHospital, groupingForMES, groupMES, MES, financeId):
        orgStructureTypeIdList = self.getOrgStructureTypeIdList(orgStructureIdList, isHospital)
        db = QtGui.qApp.db
        tableVisit = db.table('Visit')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableEventType = db.table('EventType')
        tableRBScene = db.table('rbScene')
        tablePerson = db.table('Person')
        tableOS = db.table('OrgStructure')
        tableMES = db.table('mes.MES')
        tableGroupMES = db.table('mes.mrbMESGroup')
        tableRBMedicalAidType = db.table('rbMedicalAidType')
        tableContract = db.table('Contract')

        cond = [ tableEvent['deleted'].eq(0),
                 tablePerson['deleted'].eq(0),
                 tableEventType['deleted'].eq(0),
                 tableVisit['deleted'].eq(0),
                 tableClient['deleted'].eq(0),
                 tableEvent['execDate'].isNotNull()
               ]
        queryTable = tableEvent.innerJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
        queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        queryTable = queryTable.leftJoin(tableOS, tablePerson['orgStructure_id'].eq(tableOS['id']))
        queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        queryTable = queryTable.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
        queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
        if groupingForMES:
            cond.append(tableEvent['MES_id'].isNotNull())
            if groupMES or MES:
                queryTable = queryTable.innerJoin(tableMES, tableEvent['MES_id'].eq(tableMES['id']))
                cond.append(tableMES['deleted'].eq(0))
                if MES:
                    cond.append(tableEvent['MES_id'].eq(MES))
                if groupMES:
                    queryTable = queryTable.innerJoin(tableGroupMES, tableMES['group_id'].eq(tableGroupMES['id']))
                    cond.append(tableGroupMES['deleted'].eq(0))
                    cond.append(tableMES['group_id'].eq(groupMES))
        if financeId:
            cond.append(tableContract['finance_id'].eq(financeId))
        socStatusClassId = self.params.get('socStatusClassId', None)
        socStatusTypeId  = self.params.get('socStatusTypeId', None)
        if socStatusClassId or socStatusTypeId:
            tableClientSocStatus = db.table('ClientSocStatus')
            if begDate:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                   tableClientSocStatus['endDate'].ge(begDate)
                                                  ]),
                                       tableClientSocStatus['endDate'].isNull()
                                      ]))
            if endDate:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                   tableClientSocStatus['begDate'].lt(endDate.addDays(1))
                                                  ]),
                                       tableClientSocStatus['begDate'].isNull()
                                      ]))
            queryTable = queryTable.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
            if socStatusClassId:
                cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
            if socStatusTypeId:
                cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
            cond.append(tableClientSocStatus['deleted'].eq(0))
        cond.append(tableEvent['execDate'].ge(begDate))
        cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))
        cond.append(tableRBMedicalAidType['code'].eq(7))
        cond.append(tableOS['deleted'].eq(0))
        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureTypeIdList))
        if isHospital == 2:
            queryTable = queryTable.innerJoin(tableRBScene, tableRBScene['id'].eq(tableVisit['scene_id']))
            cond.append(tableRBScene['code'].eq(2))
        else:
            queryTable = queryTable.leftJoin(tableRBScene, tableRBScene['id'].eq(tableVisit['scene_id']))
            cond.append(db.joinOr([tableVisit['scene_id'].isNull(), tableRBScene['code'].ne(2)]))
        if ageChildren:
            cond.append(ageChildren)
        eventIdList = db.getDistinctIdList(queryTable, 'Event.id', cond, 'Event.id, Visit.date ASC')
        if eventIdList:
            movingIdList = getActionTypeIdListByFlatCode(u'moving%')
            stmtVisit = u'''SELECT Diagnosis.MKB, %s
EXISTS(SELECT Organisation.isMedical FROM Organisation INNER JOIN Event AS E ON E.relegateOrg_id = Organisation.id WHERE E.id = Event.id AND Organisation.isMedical = 3 AND Organisation.deleted = 0) AS relegateOrg,
EXISTS(SELECT Diagnostic.healthGroup_id FROM Diagnostic INNER JOIN rbHealthGroup ON rbHealthGroup.id = Diagnostic.diagnosis_id
WHERE Diagnostic.deleted = 0 AND rbHealthGroup.code = 1 LIMIT 1) AS healthGroup,
(SELECT MAX(V.date) FROM Visit AS V WHERE V.event_id = Event.id AND V.deleted = 0 AND Event.execDate IS NOT NULL) AS visitLeavedDate,
EXISTS(SELECT rbResult.name FROM rbResult WHERE rbResult.id = Event.result_id AND rbResult.name LIKE '%%круглосуточный стационар%%') AS countTransfer,
EXISTS(SELECT rbResult.name FROM rbResult WHERE rbResult.id = Event.result_id
AND (rbResult.code = 99 OR rbResult.name LIKE '%%умер%%' OR rbResult.name LIKE '%%смерть%%')) AS countDeath,
(SELECT COUNT(VC.id) FROM Visit AS VC WHERE VC.event_id = Event.id AND Event.execDate IS NOT NULL AND VC.deleted = 0) AS countVisit,
(SELECT SUM(A.amount)
FROM Action AS A INNER JOIN ActionType AS AT ON A.actionType_id = AT.id
WHERE A.event_id = Event.id AND A.deleted = 0 AND AT.deleted = 0 AND A.endDate IS NOT NULL AND AT.class = 2
AND AT.serviceType = %d) AS countSurgery,
Event.setDate, Event.execDate,
age(Client.birthDate, Event.setDate) AS clientAge

FROM Event
INNER JOIN Visit ON Visit.event_id=Event.id
INNER JOIN Client ON Event.client_id=Client.id
INNER JOIN Diagnostic ON Diagnostic.event_id = Event.id
INNER JOIN Diagnosis ON Diagnosis.id = Diagnostic.diagnosis_id
INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = Diagnostic.diagnosisType_id

WHERE (Event.deleted=0) AND (Client.deleted = 0) AND (Visit.deleted=0) AND Event.id IN (%s) AND (rbDiagnosisType.code = '1' OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id
WHERE DT.code = '1' AND DC.event_id = Event.id LIMIT 1))))

GROUP BY Event.id
ORDER BY Event.id, Visit.date ASC'''%((u'''(SELECT COUNT(A.id) FROM Action AS A WHERE A.actionType_id IN (%s) AND A.event_id = Event.id AND A.deleted=0) AS countActions,''' % (u','.join(str(movingId) for movingId in movingIdList))) if movingIdList else u'',
                                      CActionServiceType.operation, u','.join(str(eventId) for eventId in eventIdList if eventId))
            return db.query(stmtVisit)
        return None


    def getReceived(self, begDateTime, endDateTime, orgStructureIdList, nameProperty = u'Направлен в отделение', profile = None):
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('received%')),
                 tableAction['deleted'].eq(0),
                 tableEvent['deleted'].eq(0),
                 tableActionType['deleted'].eq(0),
                 tableClient['deleted'].eq(0)
               ]
        queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        if profile:
            cond.append(u'''%s'''%(getPropertyAPHBP([profile], True)))
        socStatusClassId = self.params.get('socStatusClassId', None)
        socStatusTypeId  = self.params.get('socStatusTypeId', None)
        if socStatusClassId or socStatusTypeId:
            tableClientSocStatus = db.table('ClientSocStatus')
            if begDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                   tableClientSocStatus['endDate'].ge(begDateTime)
                                                  ]),
                                       tableClientSocStatus['endDate'].isNull()
                                      ]))
            if endDateTime:
                cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                   tableClientSocStatus['begDate'].lt(endDateTime.addDays(1))
                                                  ]),
                                       tableClientSocStatus['begDate'].isNull()
                                      ]))
            queryTable = queryTable.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
            if socStatusClassId:
                cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
            if socStatusTypeId:
                cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
            cond.append(tableClientSocStatus['deleted'].eq(0))
        cond.append(u'''%s'''%(getOrgStructureProperty(u'Направлен в отделение', orgStructureIdList)))
        cond.append(db.joinAnd([tableAction['begDate'].ge(begDateTime), tableAction['begDate'].lt(endDateTime)]))
        stmt = db.selectStmt(queryTable, u'COUNT(Client.id) AS countAll', where=cond)
        query = db.query(stmt)
        if query.first():
            record = query.record()
            return forceInt(record.value('countAll'))
        else:
            return 0


class CStationaryOne_2015F14DC(CReportStationary):#actOne2015Forma14DC
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. 2.Использование мест дневного стационара медицинской организации по профилям(2000).')
        self.stationaryF14DCSetupDialog = None
        self.movingDaysAll = 0
        self.movingDaysChild = 0
        self.movingDaysSenior = 0
        self.leavedAll = 0
        self.leavedChild = 0
        self.leavedSenior = 0
        self.orgHouse = 0


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        self.byActions = True if durationType == 2 else False
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            doc = QtGui.QTextDocument()
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'2.Использование мест дневного стационара медицинской организации по профилям(2000).')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('7.7%', [u'Профили коек.', u'', u'', u'', u'1'], CReportBase.AlignLeft),
                    ('3%',   [u'№стр.', u'', u'', u'', u'2'], CReportBase.AlignRight),

                    ('4.7%', [u'Дневной стационар при больничном учреждении', u'Число коек', u'для взрослых', u'на конец года', u'3'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'', u'', u'число среднегодовых мест', u'4'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'', u'для детей', u'на конец года', u'5'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'', u'', u'число среднегодовых мест', u'6'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'Выписано пациентов', u'взрослых', u'', u'7'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'', u'из них:', u'лиц старше трудоспособного возраста', '8'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'', u'', u'детей 0-17 лет включительно', u'9'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'Проведено пациенто-дней', u'взрослых', u'', u'10'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'', u'из них:', u'лиц старше трудоспособного возраста', u'11'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'', u'', u'детей 0-17 лет включительно', u'12'], CReportBase.AlignRight),

                    ('4.7%', [u'Дневные стационары медицинских организаций, оказывающих медицинскую помощь в амбулаторных условиях', u'Число коек', u'для взрослых', u'на конец года', u'13'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'', u'', u'число среднегодовых мест', u'14'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'', u'для детей', u'на конец года', u'15'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'', u'', u'число среднегодовых мест', u'16'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'Выписано пациентов', u'взрослых', u'', u'17'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'', u'из них:', u'лиц старше трудоспособного возраста', u'18'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'', u'', u'детей 0-17 лет включительно', u'19'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'Проведено пациенто-дней', u'взрослых', u'', u'20'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'', u'из них:', u'лиц старше трудоспособного возраста', u'21'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'', u'', u'детей 0-17 лет включительно', u'22'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 4, 1)  # Профили коек
            table.mergeCells(0, 1, 4, 1)  # №стр

            table.mergeCells(0, 2, 1, 10)  # Дневной стационар при больничном учреждении
            table.mergeCells(1, 2, 1, 4)
            table.mergeCells(2, 2, 1, 2)
            table.mergeCells(2, 4, 1, 2)

            table.mergeCells(1, 6, 1, 3)
            table.mergeCells(2, 6, 2, 1)
            table.mergeCells(2, 8, 2, 1)

            table.mergeCells(1, 9, 1, 3)
            table.mergeCells(2, 9, 2, 1)
            table.mergeCells(2, 11, 2, 1)

            table.mergeCells(0, 12, 1, 10)  # Дневной стационар при амбулаторно-поликлинических учреждениях
            table.mergeCells(1, 12, 1, 4)
            table.mergeCells(2, 12, 1, 2)
            table.mergeCells(2, 14, 1, 2)

            table.mergeCells(1, 16, 1, 3)
            table.mergeCells(2, 16, 2, 1)
            table.mergeCells(2, 18, 2, 1)

            table.mergeCells(1, 19, 1, 3)
            table.mergeCells(2, 19, 2, 1)
            table.mergeCells(2, 21, 2, 1)


            statOrgStructureTypeIdList = self.getOrgStructureTypeIdList(orgStructureIdList, 0)
            ambOrgStructureTypeIdList = self.getOrgStructureTypeIdList(orgStructureIdList, 1)
            housOrgStructureTypeIdList = self.getOrgStructureTypeIdList(orgStructureIdList, 2)
            orgStructureTypeIdList = list(set(statOrgStructureTypeIdList) | set(ambOrgStructureTypeIdList) | set(housOrgStructureTypeIdList))
            reportLineList, bedProfileIdList, rowProfileIdList = self.getProfileIdList(table, orgStructureTypeIdList)
            if statOrgStructureTypeIdList:
                self.fillReportTable(statOrgStructureTypeIdList, begDate, endDate, table, 2, 0, bedProfileIdList, reportLineList, rowProfileIdList, groupingForMES, groupMES, MES, durationType)
            if ambOrgStructureTypeIdList:
                self.fillReportTable(ambOrgStructureTypeIdList, begDate, endDate, table, 12, 1, bedProfileIdList, reportLineList, rowProfileIdList, groupingForMES, groupMES, MES, durationType)
            if housOrgStructureTypeIdList:
                self.fillReportTable(housOrgStructureTypeIdList, begDate, endDate, table, None, 2, bedProfileIdList, reportLineList, rowProfileIdList, groupingForMES, groupMES, MES, durationType)

            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(u'''(3001) Число медицинских организаций, имеющих стационары на дому:''')#%(self.orgHouse))
            cursor.insertBlock()
            cursor.insertText(u'''Пролечено пациентов всего %d из них: детей (0-17 лет вкл.) %d, лиц старше трудоспособного возраста %d.'''%(self.leavedAll, self.leavedChild, self.leavedSenior))
            cursor.insertBlock()
            cursor.insertText(u'''Проведено дней лечения всего %d, из них: детьми (0-17 лет вкл.) %d, лицами старше трудоспособного возраста %d.'''%(self.movingDaysAll, self.movingDaysChild, self.movingDaysSenior))
            cursor.insertBlock()
            cursor.insertText(u'''(3100) Умерло в дневном стационаре при подразделениях медицинских организаций, оказывающих медицинскую помощь: в стационарных условиях - %d, из них: детей - %d, в амбулаторных условиях - %d, из них: детей - %d, на дому - %d, из них: детей - %d.'''%(self.deathLeavedStationary, self.deathLeavedStationaryChild, self.deathLeavedAmbulance, self.deathLeavedAmbulanceChild, self.deathLeavedHouse, self.deathLeavedHouseChild))
            cursor.insertBlock()

        return doc


    def getDataEventHospital(self, orgStructureIdList, begDate, endDate, profileIdList, isHospital, groupingForMES, groupMES, MES, financeId):
        if orgStructureIdList:
            db = QtGui.qApp.db
            tableVisit = db.table('Visit')
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tableRBScene = db.table('rbScene')
            tablePerson = db.table('Person')
            tableOS = db.table('OrgStructure')
            tableMES = db.table('mes.MES')
            tableGroupMES = db.table('mes.mrbMESGroup')
            tableRBMedicalAidType = db.table('rbMedicalAidType')

            cond = [ tableEvent['deleted'].eq(0),
                     tablePerson['deleted'].eq(0),
                     tableEventType['deleted'].eq(0)
                   ]
            queryTable = tableEvent.leftJoin(tableVisit, [ tableVisit['event_id'].eq(tableEvent['id']), 
                tableVisit['deleted'].eq(0), 
                u'DATE(Event.setDate) <= DATE(Visit.date)'])
            queryTable = queryTable.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
            queryTable = queryTable.leftJoin(tableOS, tablePerson['orgStructure_id'].eq(tableOS['id']))
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            queryTable = queryTable.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
            if groupingForMES:
                cond.append(tableEvent['MES_id'].isNotNull())
                if groupMES or MES:
                    queryTable = queryTable.innerJoin(tableMES, tableEvent['MES_id'].eq(tableMES['id']))
                    cond.append(tableMES['deleted'].eq(0))
                    if MES:
                        cond.append(tableEvent['MES_id'].eq(MES))
                    if groupMES:
                        queryTable = queryTable.innerJoin(tableGroupMES, tableMES['group_id'].eq(tableGroupMES['id']))
                        cond.append(tableGroupMES['deleted'].eq(0))
                        cond.append(tableMES['group_id'].eq(groupMES))
            cond.append(tableEvent['execDate'].isNotNull())
            cond.append(tableEvent['execDate'].ge(begDate))
            cond.append(tableEvent['execDate'].le(endDate))
            cond.append(tableRBMedicalAidType['code'].eq(7))
            cond.append(tableOS['deleted'].eq(0))
            cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
            if isHospital == 2:
                queryTable = queryTable.innerJoin(tableRBScene, tableRBScene['id'].eq(tableVisit['scene_id']))
                cond.append(tableRBScene['code'].eq(2))
            if profileIdList:
                cond.append(u"""exists (select HospitalAction.id 
                    from Action AS HospitalAction
                    left join ActionPropertyType on ActionPropertyType.name = 'койка' and ActionPropertyType.actionType_id = HospitalAction.actionType_id and ActionPropertyType.deleted = 0
                    left join ActionProperty on ActionProperty.type_id = ActionPropertyType.id and ActionProperty.action_id = HospitalAction.id and ActionProperty.deleted = 0
                    left join ActionProperty_HospitalBed on ActionProperty_HospitalBed.id = ActionProperty.id
                    left join OrgStructure_HospitalBed on OrgStructure_HospitalBed.id = ActionProperty_HospitalBed.value
                    left join rbHospitalBedProfile on rbHospitalBedProfile.id = OrgStructure_HospitalBed.profile_id
                    where HospitalAction.id = (
                        SELECT MAX(A.id)
                        FROM Action A
                        WHERE A.event_id = Event.id AND
                                  A.deleted = 0 AND
                                  A.actionType_id IN (
                                        SELECT AT.id
                                        FROM ActionType AT
                                        WHERE AT.flatCode ='moving'
                                            AND AT.deleted = 0
                                  )
                    ) and HospitalAction.id is not null and rbHospitalBedProfile.id in (%s))""" % (u','.join(str(profileId) for profileId in profileIdList if profileId)))
                                
            eventIdList = db.getDistinctIdList(queryTable, u'Event.id', cond, u'Event.id, Visit.date ASC')
            if eventIdList:
                movingIdList = getActionTypeIdListByFlatCode(u'moving%')
                stmtVisit = u'''SELECT   
    (select rbHospitalBedProfile.id
    from Action AS HospitalAction
    left join ActionPropertyType on ActionPropertyType.name = 'койка' and ActionPropertyType.actionType_id = HospitalAction.actionType_id and ActionPropertyType.deleted = 0
    left join ActionProperty on ActionProperty.type_id = ActionPropertyType.id and ActionProperty.action_id = HospitalAction.id and ActionProperty.deleted = 0
    left join ActionProperty_HospitalBed on ActionProperty_HospitalBed.id = ActionProperty.id
    left join OrgStructure_HospitalBed on OrgStructure_HospitalBed.id = ActionProperty_HospitalBed.value
    left join rbHospitalBedProfile on rbHospitalBedProfile.id = OrgStructure_HospitalBed.profile_id
    where HospitalAction.id = (
        SELECT MAX(A.id)
        FROM Action A
        WHERE A.event_id = Event.id AND
            A.deleted = 0 AND
            A.actionType_id IN (
                SELECT AT.id
                FROM ActionType AT
                WHERE AT.flatCode ='moving'
                AND AT.deleted = 0
                )
            ) and HospitalAction.id is not NULL) AS bedProfile,
            
    %s

    (SELECT MIN(VIDMin.id)
    FROM Visit AS VIDMin
    WHERE VIDMin.event_id = Event.id AND VIDMin.deleted = 0
    AND DATE(VIDMin.date) = DATE((SELECT MIN(V.date) FROM Visit AS V WHERE V.event_id = Event.id))) AS visitReceivedId,

    (SELECT MIN(V.date) FROM Visit AS V WHERE V.event_id = Event.id AND V.deleted = 0) AS visitReceivedDate,

    (SELECT MAX(VIDMax.id)
    FROM Visit AS VIDMax
    WHERE VIDMax.event_id = Event.id AND  VIDMax.deleted = 0
    AND DATE(VIDMax.date) = DATE((SELECT MAX(V.date) FROM Visit AS V WHERE V.event_id = Event.id
    AND V.deleted = 0 AND Event.execDate IS NOT NULL))) AS visitLeavedId,

    (SELECT MAX(V.date)
    FROM Visit AS V
    WHERE V.event_id = Event.id AND V.deleted = 0 AND Event.execDate IS NOT NULL) AS visitLeavedDate,

    (SELECT rbResult.id FROM rbResult WHERE rbResult.id = Event.result_id LIMIT 1) AS deathLeaved,

    (SELECT COUNT(VC.id)
    FROM Visit AS VC
    WHERE VC.event_id = Event.id AND VC.deleted = 0 AND (DATE(VC.date) >= %s AND DATE(VC.date) <= %s)) AS countVisit,

    Event.setDate, Event.execDate, Event.id AS eventId,

    age(Client.birthDate, Event.setDate) AS clientAge, Client.sex,
    
    WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode) as PD

    FROM Event
    LEFT JOIN EventType ON EventType.id = Event.eventType_id
    LEFT JOIN Visit ON Visit.event_id=Event.id
    left join rbService on rbService.id = Visit.service_id
    LEFT JOIN rbMedicalAidType mt ON mt.id = ifnull(rbService.medicalAidType_id, EventType.medicalAidType_id)
    INNER JOIN Client ON Event.client_id=Client.id

    WHERE (Event.deleted=0) AND (Client.deleted = 0) AND (Visit.deleted=0) AND Event.id IN (%s)

    GROUP BY Event.id
    ORDER BY Event.id, Visit.date ASC'''%(((u'''(SELECT COUNT(A.id)
    FROM Action AS A WHERE A.actionType_id IN (%s) AND A.event_id = Event.id AND A.deleted=0) AS countActions,''' % (u','.join(str(movingId) for movingId in movingIdList))) if movingIdList else u''),
    db.formatDate(begDate), db.formatDate(endDate), u','.join(str(eventId) for eventId in eventIdList if eventId))
                return db.query(stmtVisit), eventIdList
        return None, None


    def unrolledHospitalBedEvent(self, orgStructureIdList, begDate, endDate, reportLineList, profile = None):
        if orgStructureIdList:
            db = QtGui.qApp.db
            tableOSHB = db.table('OrgStructure_HospitalBed')
            tableOS = db.table('OrgStructure')
            tableHBSchedule = db.table('rbHospitalBedShedule')
            queryTable = tableOSHB.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
            cond = [tableOSHB['master_id'].inlist(orgStructureIdList),
                    tableOS['deleted'].eq(0)
                    ]
            queryTable = queryTable.innerJoin(tableHBSchedule, tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
            cond.append(tableHBSchedule['code'].ne(1))
            joinOr1 = db.joinOr([tableOSHB['begDate'].isNull(), tableOSHB['begDate'].ge(begDate)])
            joinOr2 = db.joinOr([tableOSHB['begDate'].isNull(), tableOSHB['begDate'].lt(endDate)])
            cond.append(db.joinAnd([joinOr1, joinOr2]))
            cond.append(tableOSHB['profile_id'].eq(profile))
            countBeds = db.getCount(queryTable, countCol='OrgStructure_HospitalBed.id', where=cond)
            reportLineAll = reportLineList.get('', None)
            if reportLineAll:
                reportLineAll['countBedAdult'] += countBeds
                reportLineAll['countBedChild'] += countBeds
                reportLineList[''] = reportLineAll
            reportLine = reportLineList.get(profile, None)
            if reportLine:
                reportLine['countBedAdult'] += countBeds
                reportLine['countBedChild'] += countBeds
                reportLineList[profile] = reportLine
        return reportLineList


    def averageDaysHospitalBedEvent(self, orgStructureIdList, begDatePeriod, endDatePeriod, profile = None):
        days = 0
        if orgStructureIdList:
            db = QtGui.qApp.db
            tableOSHB = db.table('OrgStructure_HospitalBed')
            tableOS = db.table('OrgStructure')
            tableHBSchedule = db.table('rbHospitalBedShedule')
            queryTable = tableOSHB.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
            cond = [tableOSHB['master_id'].inlist(orgStructureIdList),
                    tableOS['deleted'].eq(0)
                    ]
            queryTable = queryTable.innerJoin(tableHBSchedule, tableOSHB['schedule_id'].eq(tableHBSchedule['id']))
            cond.append(tableHBSchedule['code'].ne(1))
            joinAnd = db.joinAnd([tableOSHB['endDate'].isNull(), db.joinOr([db.joinAnd([tableOSHB['begDate'].isNotNull(), tableOSHB['begDate'].lt(endDatePeriod)]), tableOSHB['begDate'].isNull()])])
            cond.append(db.joinOr([db.joinAnd([tableOSHB['endDate'].isNotNull(), tableOSHB['endDate'].gt(begDatePeriod), tableOSHB['begDate'].isNotNull(), tableOSHB['begDate'].lt(endDatePeriod)]), joinAnd]))
            cond.append(tableOSHB['profile_id'].eq(profile))
            stmt = db.selectStmt(queryTable, [tableOSHB['id'], tableOSHB['begDate'], tableOSHB['endDate'], tableOSHB['relief']], where=cond)
            query = db.query(stmt)
            bedIdList = []
            while query.next():
                record = query.record()
                bedId = forceRef(record.value('id'))
                relief = forceInt(record.value('relief'))
                if bedId not in bedIdList:
                    daysBed = 0
                    bedIdList.append(bedId)
                    begDate = forceDate(record.value('begDate'))
                    endDate = forceDate(record.value('endDate'))
                    if not begDate or begDate < begDatePeriod:
                        begDate = begDatePeriod
                    if not endDate or endDate > endDatePeriod:
                        endDate = endDatePeriod
                    if begDate and endDate:
                        if begDate == endDate:
                            daysBed = relief if relief else 1
                        else:
                            daysBed = begDate.daysTo(endDate) * relief if relief else begDate.daysTo(endDate)
                        days += daysBed
        return days


    def averageYarHospitalBedEvent(self, orgStructureIdList, begDate, endDate, reportLineList, profile = None):
        if orgStructureIdList:
            days = 0
            begMonth = begDate.month()
            begYear = begDate.year()
            begDatePeriod = QDate(begYear, begMonth, 1)
            endMonth = endDate.month()
            endYear = endDate.year()
            endDatePeriod = begDatePeriod.addMonths(1)
            daysMonths = 0
            daysYears = 0
            while endDatePeriod.month() <= endMonth and endDatePeriod.year() <= endYear:
                days = self.averageDaysHospitalBedEvent(orgStructureIdList, begDatePeriod, endDatePeriod, profile)
                daysMonths += days / begDatePeriod.daysInMonth()
                begDatePeriod = begDatePeriod.addMonths(1)
                endDatePeriod = endDatePeriod.addMonths(1)
            daysYears = daysMonths / begDatePeriod.month()
            reportLineAll = reportLineList.get('', None)
            if reportLineAll:
                reportLineAll['countAverageBedAdult'] += daysYears
                reportLineAll['countAverageBedChild'] += daysYears
                reportLineList[''] = reportLineAll
            reportLine = reportLineList.get(profile, None)
            if reportLine:
                reportLine['countAverageBedAdult'] += daysYears
                reportLine['countAverageBedChild'] += daysYears
                reportLineList[profile] = reportLine
        return reportLineList


    def getProfileIdList(self, table, orgStructureIdList):
        db = QtGui.qApp.db
        tableOSHB = db.table('OrgStructure_HospitalBed')
        tableRBHospitalBedProfile = db.table('rbHospitalBedProfile')
        queryTable = tableOSHB.innerJoin(tableRBHospitalBedProfile, tableOSHB['profile_id'].eq(tableRBHospitalBedProfile['id']))
        cols = ['DISTINCT rbHospitalBedProfile.id, rbHospitalBedProfile.code, rbHospitalBedProfile.name']
        bedProfileRecords = db.getRecordList(queryTable, cols, [tableOSHB['master_id'].inlist(orgStructureIdList)])
        reportLineList = {u'': {'code':u'', 'name':u'', 'countBedAdult':0, 'countAverageBedAdult':0, 'countBedChild':0,
                                'countAverageBedChild':0, 'visitLeavedAdult':0, 'visitLeavedSenior':0, 'visitLeavedChild':0,
                                'countVisitAdult':0, 'countVisitSenior':0, 'countVisitChild':0}}
        rowProfileIdList = {}
        bedProfileIdList = []
        rowProfile = table.addRow()
        rowProfileIdList[''] = rowProfile
        cnt = 1
        table.setText(rowProfile, 1, cnt)
        table.setText(rowProfile, 0, u'ВСЕГО\nв том числе:')
        for bedProfileRecord in bedProfileRecords:
            profileId = forceRef(bedProfileRecord.value('id'))
            code = forceString(bedProfileRecord.value('code'))
            name = forceString(bedProfileRecord.value('name'))
            if profileId not in bedProfileIdList:
                bedProfileIdList.append(profileId)
            if not reportLineList.get(profileId, None):
                reportLine = {'code':u'', 'name':u'', 'countBedAdult':0, 'countAverageBedAdult':0, 'countBedChild':0,
                            'countAverageBedChild':0, 'visitLeavedAdult':0, 'visitLeavedSenior':0, 'visitLeavedChild':0,
                            'countVisitAdult':0, 'countVisitSenior':0, 'countVisitChild':0}
                reportLine['code'] = code
                reportLine['name'] = name
                reportLineList[profileId] = reportLine
                cnt += 1
                rowProfile = table.addRow()
                rowProfileIdList[profileId] = rowProfile
                table.setText(rowProfile, 1, cnt)
                table.setText(rowProfile, 0, reportLine['name'])
        return reportLineList, bedProfileIdList, rowProfileIdList


    def fillReportTable(self, orgStructureIdList, begDate, endDate, table, cols, isHospital, bedProfileIdList, reportLineList, rowProfileIdList, groupingForMES, groupMES, MES, durationType = 0, financeId=None):
        db = QtGui.qApp.db
        tableRBHospitalBedProfile = db.table('rbHospitalBedProfile')
        for profileId in bedProfileIdList:
            reportLineList = self.unrolledHospitalBedEvent(orgStructureIdList, begDate, endDate, reportLineList, profileId)
            reportLineList = self.averageYarHospitalBedEvent(orgStructureIdList, begDate, endDate, reportLineList, profileId)
        records, eventIdList = self.getDataEventHospital(orgStructureIdList, begDate, endDate, bedProfileIdList, isHospital, groupingForMES, groupMES, MES, financeId)
        if records:
            eventIdList = []
            while records.next():
                record = records.record()
                countVisit = 0
                execDate = forceDate(record.value('execDate'))
                clientAge = forceInt(record.value('clientAge'))
                sex = forceInt(record.value('sex'))
                eventId = forceRef(record.value('eventId'))
                if isHospital != 2:
                    profileId = forceRef(record.value('bedProfile'))
                    if durationType == 0:
                        countVisit = forceInt(record.value('countVisit'))
                    elif durationType == 1:
                        countVisit = forceInt(record.value('PD'))
                    elif durationType == 2:
                        countVisit = forceInt(record.value('countActions'))
                    self.movingDaysAll += countVisit
                    if clientAge < 18:
                        self.movingDaysChild += countVisit
                    if (clientAge >= 55 and sex == 2) or (clientAge >= 60 and sex == 1):
                        self.movingDaysSenior += countVisit
                    if eventId and eventId not in eventIdList:
                        eventIdList.append(eventId)
                        self.leavedAll += 1
                        if clientAge < 18:
                            self.leavedChild += 1
                        if (clientAge >= 55 and sex == 2) or (clientAge >= 60 and sex == 1):
                            self.leavedSenior += 1    
                    reportLine = reportLineList.get(profileId, None)
                    reportLineAll = reportLineList.get('', None)
                    deathLeaved = forceString(record.value('deathLeaved'))
                    countDeathLeaved = 1 if (u'умер' in deathLeaved or u'смерть' in deathLeaved) else 0
                    if isHospital == 0:
                        self.deathLeavedStationary += countDeathLeaved
                        if clientAge < 18:
                            self.deathLeavedStationaryChild += countDeathLeaved
                    elif isHospital == 1:
                        self.deathLeavedAmbulance += countDeathLeaved
                        if clientAge < 18:
                            self.deathLeavedAmbulanceChild += countDeathLeaved
                    if not reportLine:
                        bedRepRecord = db.getRecordEx(tableRBHospitalBedProfile, [tableRBHospitalBedProfile['code'], tableRBHospitalBedProfile['name']], [tableRBHospitalBedProfile['id'].eq(profileId)])
                        if bedRepRecord:
                            code = forceString(bedRepRecord.value('code'))
                            name = forceString(bedRepRecord.value('name'))
                            reportLine = {'code':u'', 'name':u'', 'countBedAdult':0, 'countAverageBedAdult':0, 'countBedChild':0,
                                        'countAverageBedChild':0, 'visitLeavedAdult':0, 'visitLeavedSenior':0, 'visitLeavedChild':0,
                                        'countVisitAdult':0, 'countVisitSenior':0, 'countVisitChild':0}
                            reportLine['code'] = code
                            reportLine['name'] = name
                    if reportLine:
                        if execDate >= begDate and (not endDate or execDate <= endDate):
                            if clientAge >= 18:
                                reportLine['visitLeavedAdult'] += 1
                                reportLineAll['visitLeavedAdult'] += 1
                                if (sex == 2 and clientAge >= 55) or (sex == 1 and clientAge >= 60):
                                    reportLine['visitLeavedSenior'] += 1
                                    reportLineAll['visitLeavedSenior'] += 1
                            else:
                                reportLine['visitLeavedChild'] += 1
                                reportLineAll['visitLeavedChild'] += 1
                        if durationType == 0:
                            countVisit = forceInt(record.value('countVisit'))
                        elif durationType == 1:
                            countVisit = forceInt(record.value('PD'))
                        elif durationType == 2:
                            countVisit = forceInt(record.value('countActions'))
                        if clientAge >= 18:
                            reportLine['countVisitAdult'] += countVisit
                            reportLineAll['countVisitAdult'] += countVisit
                            if (sex == 2 and clientAge >= 55) or (sex == 1 and clientAge >= 60):
                                reportLine['countVisitSenior'] += countVisit
                                reportLineAll['countVisitSenior'] += countVisit
                        else:
                            reportLine['countVisitChild'] += countVisit
                            reportLineAll['countVisitChild'] += countVisit
                        reportLineList[profileId] = reportLine
                        reportLineList[''] = reportLineAll

                elif isHospital == 2:
                    deathLeaved = forceString(record.value('deathLeaved'))
                    countDeathLeaved = 1 if (u'умер' in deathLeaved or u'смерть' in deathLeaved) else 0
                    self.deathLeavedHouse += countDeathLeaved
                    if clientAge < 18:
                        self.deathLeavedHouseChild += countDeathLeaved

            if isHospital != 2:
                reportLine = reportLineList.get(u'', {'code':u'', 'name':u'', 'countBedAdult':0, 'countAverageBedAdult':0, 'countBedChild':0,
                                                    'countAverageBedChild':0, 'visitLeavedAdult':0, 'visitLeavedSenior':0, 'visitLeavedChild':0,
                                                    'countVisitAdult':0, 'countVisitSenior':0, 'countVisitChild':0})
                rowAll = rowProfileIdList.get(u'', None)
                table.setText(rowAll, cols, reportLine['countBedAdult'])
                table.setText(rowAll, cols+2, reportLine['countBedChild'])
                table.setText(rowAll, cols+1, reportLine['countAverageBedAdult'])
                table.setText(rowAll, cols+3, reportLine['countAverageBedChild'])
                table.setText(rowAll, cols+4, reportLine['visitLeavedAdult'])
                table.setText(rowAll, cols+5, reportLine['visitLeavedSenior'])
                table.setText(rowAll, cols+6, reportLine['visitLeavedChild'])
                table.setText(rowAll, cols+7, reportLine['countVisitAdult'])
                table.setText(rowAll, cols+8, reportLine['countVisitSenior'])
                table.setText(rowAll, cols+9, reportLine['countVisitChild'])
                if reportLineList.get('', None):
                    del reportLineList['']
                for key, reportLine in reportLineList.items():
                    rowProfile = rowProfileIdList.get(key, None)
                    table.setText(rowProfile, cols, reportLine['countBedAdult'])
                    table.setText(rowProfile, cols+2, reportLine['countBedChild'])
                    table.setText(rowProfile, cols+1, reportLine['countAverageBedAdult'])
                    table.setText(rowProfile, cols+3, reportLine['countAverageBedChild'])
                    table.setText(rowProfile, cols+4, reportLine['visitLeavedAdult'])
                    table.setText(rowProfile, cols+5, reportLine['visitLeavedSenior'])
                    table.setText(rowProfile, cols+6, reportLine['visitLeavedChild'])
                    table.setText(rowProfile, cols+7, reportLine['countVisitAdult'])
                    table.setText(rowProfile, cols+8, reportLine['countVisitSenior'])
                    table.setText(rowProfile, cols+9, reportLine['countVisitChild'])
                    reportLine['countBedAdult'] = 0
                    reportLine['countBedChild'] = 0
                    reportLine['countAverageBedAdult'] = 0
                    reportLine['countAverageBedChild'] = 0
                    reportLine['visitLeavedAdult'] = 0
                    reportLine['visitLeavedSenior'] = 0
                    reportLine['visitLeavedChild'] = 0
                    reportLine['countVisitAdult'] = 0
                    reportLine['countVisitSenior'] = 0
                    reportLine['countVisitChild'] = 0
                    reportLineList[key] = reportLine
                if not reportLineList.get('', None):
                    reportLineList[u''] = {'code':u'', 'name':u'', 'countBedAdult':0, 'countAverageBedAdult':0, 'countBedChild':0,
                                        'countAverageBedChild':0, 'visitLeavedAdult':0, 'visitLeavedSenior':0, 'visitLeavedChild':0,
                                        'countVisitAdult':0, 'countVisitSenior':0, 'countVisitChild':0}


class CStationaryTwoAdult_2015F14DC(CReportStationary):
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. 3.Движение пациентов в дневных стационарах, сроки и исходы лечения. 3.1.Дневные стационары для взрослых.(3000).')
        self.stationaryF14DCSetupDialog = None


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            rowSize = 9
            mapMainRows = createMapCodeToRowIdx( [row[2] for row in TwoRows2015] )
            reportMainData = [ [0]*rowSize for row in xrange(len(TwoRows2015)) ]
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            titleText = u'Форма 14ДС. 3.Движение пациентов в дневных стационарах, сроки и исходы лечения. 3.1.Дневные стационары для взрослых.(3000).'
            cursor.insertText(titleText)
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('13%', [u'Наименование классов МКБ-10', u'', u'', u'1'], CReportBase.AlignLeft),
                    ('5%', [u'№ строки', u'', u'', u'2'], CReportBase.AlignRight),
                    ('10%', [u'Код по МКБ-10', u'', u'', u'3'], CReportBase.AlignLeft),

                    ('8%', [u'Дневные стационары медицинских организаций, оказывающих медицинскую помощь', u'в стационарных условиях', u'Выписано пациентов', u'4'], CReportBase.AlignLeft),
                    ('8%', [u'', u'', u'Проведено пациентодней', u'5'], CReportBase.AlignRight),
                    ('8%', [u'', u'', u'Умерло', '6'], CReportBase.AlignRight),

                    ('8%', [u'', u'в амбулаторных условиях', u'Выписано пациентов', u'7'], CReportBase.AlignRight),
                    ('8%', [u'', u'', u'Проведено пациентодней', u'8'], CReportBase.AlignRight),
                    ('8%', [u'', u'', u'Умерло', u'9'], CReportBase.AlignRight),

                    ('8%', [u'', u'на дому', u'Выписано пациентов', u'10'], CReportBase.AlignRight),
                    ('8%', [u'', u'', u'Проведено пациентодней', u'11'], CReportBase.AlignRight),
                    ('8%', [u'', u'', u'Умерло', u'12'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 3, 1)  # название
            table.mergeCells(0, 1, 3, 1)  # №стр
            table.mergeCells(0, 2, 3, 1)  # код по МКБ
            table.mergeCells(0, 3, 1, 9)  # Дневной стационар
            table.mergeCells(1, 3, 1, 3)  # Дневной стационар при больничных учреждениях
            table.mergeCells(1, 6, 1, 3)  # Дневной стационар при амбулаторно-поликлинических учреждениях
            table.mergeCells(1, 9, 1, 3) # Дневной стационар при амбулаторно-поликлинических учреждениях

            isHospitals = [(0, 0), (3, 1), (6, 2)]
            medicalCheckupHealthy = 0
            leavedEnlistmentSum = 0
            conscript = 0
            child = 0
            conscriptChild = 0
            for i, isHospital in isHospitals:
                records = self.getDataEventAdult(orgStructureIdList, begDate, endDate.addDays(1), u'''(age(Client.birthDate, Event.setDate)) >= 18''', isHospital, groupingForMES, groupMES, MES, financeId)
                if records:
                    while records.next():
                        record = records.record()
                        MKBRec = normalizeMKB(forceString(record.value('MKB')))
                        visitLeavedDate = forceDate(record.value('visitLeavedDate'))
                        countDeath = forceInt(record.value('countDeath'))
                        clientAge = forceInt(record.value('clientAge'))
                        countVisit = 0
                        if durationType == 0:
                            countVisit = forceInt(record.value('countVisit'))
                        elif durationType == 1:
                            countVisit = forceInt(record.value('PD'))
                        elif durationType == 2:
                            countVisit = forceInt(record.value('countActions'))
                        countSurgery = forceInt(record.value('countSurgery'))
                        healthGroup = forceInt(record.value('healthGroup'))
                        relegateOrg = forceInt(record.value('relegateOrg'))
                        medicalCheckupHealthy =+ healthGroup
                        if clientAge < 18:
                            conscriptChild += healthGroup
                        leavedEnlistmentSum += relegateOrg
                        if relegateOrg and healthGroup:
                            conscript += 1
                            if clientAge < 18:
                               conscriptChild += 1
                        for row in mapMainRows.get(MKBRec, []):
                            reportLine = reportMainData[row]
                            if visitLeavedDate:
                                reportLine[i] += 1
                            reportLine[i+1] += countVisit
                            reportLine[i+2] += countDeath
                        if countSurgery:
                            reportLine = reportMainData[len(TwoRows2015)-2]
                            if visitLeavedDate:
                                reportLine[i] += 1
                            reportLine[i+1] = u'X'
                            reportLine[i+2] += countDeath
                            reportLine = reportMainData[len(TwoRows2015)-1]
                            if visitLeavedDate:
                                reportLine[i] += countSurgery
                            reportLine[i+1] = u'X'
                            reportLine[i+2] = u'X'
            for row, rowDescr in enumerate(TwoRows2015):
                reportLine = reportMainData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])

            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(u'''(4000) Из общего числа выписанных - (гр. 4, 7) – направленные райвоенкоматом %d. '''%(leavedEnlistmentSum))
            cursor.insertBlock()
            cursor.insertText(u'''(4100) Лица, госпитализированные для обследования и оказавшиеся здоровыми: взрослые %d, из них призывники %d, дети %d, из них: призывники %d.'''%(medicalCheckupHealthy, conscript, child, conscriptChild))
            cursor.insertBlock()

        return doc


class CStationaryTwoChildren_2015F14DC(CReportStationary):#actTwoChildren_2015Forma14DC
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. 3.Движение пациентов в дневных стационарах, сроки и исходы лечения. 3.1.Дневные стационары для детей.(3500).')
        self.stationaryF14DCSetupDialog = None


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        financeId = params.get('financeId', None)
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            rowSize = 9
            mapMainRows = createMapCodeToRowIdx( [row[2] for row in ThreeRows2015] )
            reportMainData = [ [0]*rowSize for row in xrange(len(ThreeRows2015)) ]
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = []
            if orgStructureIndex.isValid():
                treeItem = orgStructureIndex.internalPointer()
                if treeItem._id:
                    orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            titleText = u'Форма 14ДС. 3.Движение пациентов в дневных стационарах, сроки и исходы лечения. 3.1.Дневные стационары для детей.(3500).'
            cursor.insertText(titleText)
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('13%', [u'Наименование классов МКБ-10', u'', u'', u'1'], CReportBase.AlignLeft),
                    ('5%', [u'№ строки', u'', u'', u'2'], CReportBase.AlignRight),
                    ('10%', [u'Код по МКБ-10', u'', u'', u'3'], CReportBase.AlignLeft),

                    ('8%', [u'Дневные стационары медицинских организаций, оказывающих медицинскую помощь', u'в стационарных условиях', u'Выписано пациентов', u'4'], CReportBase.AlignLeft),
                    ('8%', [u'', u'', u'Проведено пациентодней', u'5'], CReportBase.AlignRight),
                    ('8%', [u'', u'', u'Умерло', u'6'], CReportBase.AlignRight),

                    ('8%', [u'', u'в амбулаторных условиях', u'Выписано пациентов', u'7'], CReportBase.AlignRight),
                    ('8%', [u'', u'', u'Проведено пациентодней', u'8'], CReportBase.AlignRight),
                    ('8%', [u'', u'', u'Умерло', u'9'], CReportBase.AlignRight),

                    ('8%', [u'', u'на дому', u'Выписано пациентов', u'10'], CReportBase.AlignRight),
                    ('8%', [u'', u'', u'Проведено пациентодней', u'11'], CReportBase.AlignRight),
                    ('8%', [u'', u'', u'Умерло', u'12'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 3, 1)  # название
            table.mergeCells(0, 1, 3, 1)  # №стр
            table.mergeCells(0, 2, 3, 1)  # код по МКБ
            table.mergeCells(0, 3, 1, 9)  # Дневной стационар
            table.mergeCells(1, 3, 1, 3)  # Дневной стационар при больничных учреждениях
            table.mergeCells(1, 6, 1, 3)  # Дневной стационар при амбулаторно-поликлинических учреждениях
            table.mergeCells(1, 9, 1, 3) # Дневной стационар при амбулаторно-поликлинических учреждениях

            isHospitals = [(0, 0), (3, 1), (6, 2)]
            medicalCheckupHealthy = 0
            leavedEnlistmentSum = 0
            conscript = 0
            child = 0
            conscriptChild = 0
            for i, isHospital in isHospitals:
                records = self.getDataEventAdult(orgStructureIdList, begDate, endDate, u'''(age(Client.birthDate, Event.setDate)) < 18''', isHospital, groupingForMES, groupMES, MES, financeId)
                if records:
                    while records.next():
                        record = records.record()
                        MKBRec = normalizeMKB(forceString(record.value('MKB')))
                        visitLeavedDate = forceDate(record.value('visitLeavedDate'))
                        countDeath = forceInt(record.value('countDeath'))
                        clientAge = forceInt(record.value('clientAge'))
                        countVisit = 0
                        if durationType == 0:
                            countVisit = forceInt(record.value('countVisit'))
                        elif durationType == 1:
                            setDate = forceDate(record.value('setDate'))
                            execDate = forceDate(record.value('execDate'))
                            countVisit = setDate.daysTo(execDate)+1
                        elif durationType == 2:
                            countVisit = forceInt(record.value('countActions'))
                        countSurgery = forceInt(record.value('countSurgery'))
                        healthGroup = forceInt(record.value('healthGroup'))
                        relegateOrg = forceInt(record.value('relegateOrg'))
                        medicalCheckupHealthy =+ healthGroup
                        if clientAge < 18:
                            conscriptChild += healthGroup
                        leavedEnlistmentSum += relegateOrg
                        if relegateOrg and healthGroup:
                            conscript += 1
                            if clientAge < 18:
                               conscriptChild += 1
                        for row in mapMainRows.get(MKBRec, []):
                            reportLine = reportMainData[row]
                            if visitLeavedDate:
                                reportLine[i] += 1
                            reportLine[i+1] += countVisit
                            reportLine[i+2] += countDeath
                        if countSurgery:
                            reportLine = reportMainData[len(ThreeRows2015)-2]
                            if visitLeavedDate:
                                reportLine[i] += 1
                            reportLine[i+1] = u'X'
                            reportLine[i+2] += countDeath
                            reportLine = reportMainData[len(ThreeRows2015)-1]
                            if visitLeavedDate:
                                reportLine[i] += countSurgery
                            reportLine[i+1] = u'X'
                            reportLine[i+2] = u'X'

            for row, rowDescr in enumerate(ThreeRows2015):
                reportLine = reportMainData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(u'''(4000) Из общего числа выписанных - (гр. 4, 7) – направленные райвоенкоматом %d. '''%(leavedEnlistmentSum))
            cursor.insertBlock()
            cursor.insertText(u'''(4100) Лица, госпитализированные для обследования и оказавшиеся здоровыми: взрослые %d, из них призывники %d, дети %d, из них: призывники %d.'''%(medicalCheckupHealthy, conscript, child, conscriptChild))
            cursor.insertBlock()
        return doc



class CStationaryOneF14DC(CReportStationary):#actOneForma14DC
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. Раздел I. Использование коечного фонда. Общий.')
        self.stationaryF14DCSetupDialog = None


    def build(self, params):
        self.deathRuralLeavedStationary = 0
        self.deathLeavedStationary = 0
        self.deathRuralLeavedAmbulance = 0
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        self.byActions = True if durationType == 2 else False
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            doc = QtGui.QTextDocument()
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'Раздел I. Использование коечного фонда\n(1100)')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('3%',[u'№стр.', u'', u'1'], CReportBase.AlignRight),
                    ('7.7%',[u'Профили коек.', u'', u'2'], CReportBase.AlignLeft),
                    ('4.7%', [u'Дневной стационар при больничном учреждении', u'Число мест', u'3'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'число среднегодовых мест', u'4'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'поступило больных', u'5'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'выписано', u'6'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'из них детей (0-17 лет)', '7'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'в т.ч. круглосуточный стационар(из г.6)', u'8'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'проведено больными дней лечения', u'9'], CReportBase.AlignRight),

                    ('4.7%', [u'Дневной стационар при амбулаторно-поликлинических учреждениях', u'Число мест', u'10'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'число среднегодовых мест', u'11'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'поступило больных', u'12'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'выписано', u'13'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'из них детей (0-17 лет)', '14'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'в т.ч. круглосуточный стационар(из г.13)', u'15'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'проведено больными дней лечения', u'16'], CReportBase.AlignRight),

                    ('4.7%', [u'Стационар на дому', u'Число мест', u'17'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'выписано', u'18'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'из них детей (0-17 лет)', '19'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'в т.ч. круглосуточный стационар(из г.18)', u'20'], CReportBase.AlignRight),
                    ('4.7%', [u'', u'проведено больными дней лечения', u'21'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 2, 1)  # №стр
            table.mergeCells(0, 1, 2, 1)  # Профили коек
            table.mergeCells(0, 2, 1, 7)  # Дневной стационар при больничном учреждении
            table.mergeCells(0, 9, 1, 7)  # Дневной стационар при амбулаторно-поликлинических учреждениях
            table.mergeCells(0, 16, 1, 5) # Стационар на дому
            statOrgStructureTypeIdList = self.getOrgStructureTypeIdList(orgStructureIdList, 0)
            ambOrgStructureTypeIdList = self.getOrgStructureTypeIdList(orgStructureIdList, 1)
            housOrgStructureTypeIdList = self.getOrgStructureTypeIdList(orgStructureIdList, 2)
            orgStructureTypeIdList = list(set(statOrgStructureTypeIdList) | set(ambOrgStructureTypeIdList) | set(housOrgStructureTypeIdList))
            reportLineList, bedProfileIdList, rowProfileIdList = self.getProfileIdList(table, orgStructureTypeIdList)
            if statOrgStructureTypeIdList:
                self.fillReportTable(statOrgStructureTypeIdList, begDate, endDate, table, 2, 0, bedProfileIdList, reportLineList, rowProfileIdList, groupingForMES, groupMES, MES, durationType, financeId)
            if ambOrgStructureTypeIdList:
                self.fillReportTable(ambOrgStructureTypeIdList, begDate, endDate, table, 9, 1, bedProfileIdList, reportLineList, rowProfileIdList, groupingForMES, groupMES, MES, durationType, financeId)
            if housOrgStructureTypeIdList:
                self.fillReportTable(housOrgStructureTypeIdList, begDate, endDate, table, 16, 2, bedProfileIdList, reportLineList, rowProfileIdList, groupingForMES, groupMES, MES, durationType, financeId)
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(u'''(1101) Из числа выбывших умерло в дневном стационаре больничного учреждения - %d, амбулаторно-поликлинического учреждения  - %d, в стационаре на дому - %d. '''%(self.deathLeavedStationary, self.deathLeavedAmbulance, self.deathLeavedHouse))
            cursor.insertBlock()
            cursor.insertText(u'''(1102) Из числа выбывших сельские жители: в дневном стационаре больничного учреждения - %d, амбулаторно-поликлинического учреждения - %d, в стационаре на дому - %d.'''%(self.deathRuralLeavedStationary, self.deathRuralLeavedAmbulance, self.deathRuralLeavedHouse))
            cursor.insertBlock()

        return doc


    def getProfileIdList(self, table, orgStructureIdList):
        db = QtGui.qApp.db
        tableOSHB = db.table('OrgStructure_HospitalBed')
        tableRBHospitalBedProfile = db.table('rbHospitalBedProfile')
        queryTable = tableOSHB.innerJoin(tableRBHospitalBedProfile, tableOSHB['profile_id'].eq(tableRBHospitalBedProfile['id']))
        cols = ['DISTINCT rbHospitalBedProfile.id, rbHospitalBedProfile.code, rbHospitalBedProfile.name']
        bedProfileRecords = db.getRecordList(queryTable, cols, [tableOSHB['master_id'].inlist(orgStructureIdList)])
        reportLineList = {'':{'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0}}
        rowProfileIdList = {}
        bedProfileIdList = []
        rowProfile = table.addRow()
        rowProfileIdList[''] = rowProfile
        cnt = 1
        table.setText(rowProfile, 0, cnt)
        table.setText(rowProfile, 1, u'ВСЕГО\nв том числе:')
        for bedProfileRecord in bedProfileRecords:
            profileId = forceRef(bedProfileRecord.value('id'))
            code = forceString(bedProfileRecord.value('code'))
            name = forceString(bedProfileRecord.value('name'))
            if profileId not in bedProfileIdList:
                bedProfileIdList.append(profileId)
            if not reportLineList.get(profileId, None):
                reportLine = {'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0}
                reportLine['code'] = code
                reportLine['name'] = name
                reportLineList[profileId] = reportLine
                cnt += 1
                rowProfile = table.addRow()
                rowProfileIdList[profileId] = rowProfile
                table.setText(rowProfile, 0, cnt)
                table.setText(rowProfile, 1, reportLine['name'])
        return reportLineList, bedProfileIdList, rowProfileIdList


    def fillReportTable(self, orgStructureIdList, begDate, endDate, table, cols, isHospital, bedProfileIdList, reportLineList, rowProfileIdList, groupingForMES, groupMES, MES, durationType = 0, financeId=None):
        db = QtGui.qApp.db
        tableRBHospitalBedProfile = db.table('rbHospitalBedProfile')
        for profileId in bedProfileIdList:
            reportLineList = self.unrolledHospitalBedEvent(orgStructureIdList, begDate, endDate, reportLineList, profileId)
            if isHospital != 2:
                reportLineList = self.averageYarHospitalBedEvent(orgStructureIdList, begDate, endDate, reportLineList, profileId)
        records, eventIdList = self.getDataEventHospital(orgStructureIdList, begDate, endDate, bedProfileIdList, isHospital, groupingForMES, groupMES, MES, financeId)
        if records:
            while records.next():
                record = records.record()
                profileId = forceRef(record.value('bedProfile'))
                reportLine = reportLineList.get(profileId, None)
                reportLineAll = reportLineList.get('', None)
                deathLeaved = forceString(record.value('deathLeaved'))
                countDeathLeaved = 1 if (u'умер' in deathLeaved or u'смерть' in deathLeaved) else 0
                if not reportLine:
                    bedRepRecord = db.getRecordEx(tableRBHospitalBedProfile, [tableRBHospitalBedProfile['code'], tableRBHospitalBedProfile['name']], [tableRBHospitalBedProfile['id'].eq(profileId)])
                    if bedRepRecord:
                        code = forceString(bedRepRecord.value('code'))
                        name = forceString(bedRepRecord.value('name'))
                        reportLine = {'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0}
                        reportLine['code'] = code
                        reportLine['name'] = name
                if reportLine:
                    visitReceivedId = forceRef(record.value('visitReceivedId'))
                    visitReceivedDate = forceDate(record.value('visitReceivedDate'))
                    if visitReceivedDate >= begDate and (not endDate or visitReceivedDate <= endDate):
                        reportLine['visitReceived'] += 1
                        reportLineAll['visitReceived'] += 1
                    visitLeavedId = forceRef(record.value('visitLeavedId'))
                    visitLeavedDate = forceDate(record.value('visitLeavedDate'))
                    if (visitReceivedId != visitLeavedId) and visitLeavedDate >= begDate and (not endDate or visitLeavedDate <= endDate):
                        reportLine['visitLeaved'] += 1
                        reportLineAll['visitLeaved'] += 1
                        if isHospital == 0:
                            self.deathLeavedStationary += countDeathLeaved
                            self.deathRuralLeavedStationary += forceInt(record.value('deathRuralLeaved'))
                        elif isHospital == 1:
                            self.deathLeavedAmbulance += countDeathLeaved
                            if forceInt(record.value('deathRuralLeaved')):
                                self.deathRuralLeavedAmbulance += 1
                        elif isHospital == 2:
                            self.deathLeavedHouse += countDeathLeaved
                            self.deathRuralLeavedHouse += forceInt(record.value('deathRuralLeaved'))
                        ageClient = forceInt(record.value('ageClient'))
                        if ageClient <= 17:
                            reportLine['ageChildren'] += 1
                            reportLineAll['ageChildren'] += 1
                    countTransfer = forceInt(record.value('countTransfer'))
                    countVisit = 0
                    if durationType == 0:
                        countVisit = forceInt(record.value('countVisit'))
                    reportLine['countTransfer'] += countTransfer
                    reportLine['countVisit'] += countVisit
                    reportLineAll['countTransfer'] += countTransfer
                    reportLineAll['countVisit'] += countVisit
                    reportLineList[profileId] = reportLine
                    reportLineList[''] = reportLineAll
            if durationType > 0:
                begDateTime = QDateTime(begDate, QTime(0, 0))
                endDateTime = QDateTime(endDate, QTime(23, 59))
                for profile in reportLineList.keys():
                    if profile == '':
                        reportLineList[profile]['countVisit'] = getMovingDays(orgStructureIdList, begDateTime, endDateTime, bedProfileIdList)
                    else:
                        reportLineList[profile]['countVisit'] = getMovingDays(orgStructureIdList, begDateTime, endDateTime, [profile])
            reportLine = reportLineList.get('', {'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0})
            rowAll = rowProfileIdList.get('', None)
            if isHospital != 2:
                table.setText(rowAll, cols, reportLine['countBed'])
                table.setText(rowAll, cols+1, reportLine['countAverageBed'])
                table.setText(rowAll, cols+2, reportLine['visitReceived'])
                table.setText(rowAll, cols+3, reportLine['visitLeaved'])
                table.setText(rowAll, cols+4, reportLine['ageChildren'])
                table.setText(rowAll, cols+5, reportLine['countTransfer'])
                table.setText(rowAll, cols+6, reportLine['countVisit'])
                if reportLineList.get('', None):
                    del reportLineList['']
                for key, reportLine in reportLineList.items():
                    rowProfile = rowProfileIdList.get(key, None)
                    table.setText(rowProfile, cols, reportLine['countBed'])
                    table.setText(rowProfile, cols+1, reportLine['countAverageBed'])
                    table.setText(rowProfile, cols+2, reportLine['visitReceived'])
                    table.setText(rowProfile, cols+3, reportLine['visitLeaved'])
                    table.setText(rowProfile, cols+4, reportLine['ageChildren'])
                    table.setText(rowProfile, cols+5, reportLine['countTransfer'])
                    table.setText(rowProfile, cols+6, reportLine['countVisit'])
                    reportLine['countBed'] = 0
                    reportLine['countAverageBed'] = 0
                    reportLine['visitReceived'] = 0
                    reportLine['visitLeaved'] = 0
                    reportLine['ageChildren'] = 0
                    reportLine['countTransfer'] = 0
                    reportLine['countVisit'] = 0
                    reportLineList[key] = reportLine
            else:
                table.setText(rowAll, cols, reportLine['countBed'])
                table.setText(rowAll, cols+1, reportLine['visitLeaved'])
                table.setText(rowAll, cols+2, reportLine['ageChildren'])
                table.setText(rowAll, cols+3, reportLine['countTransfer'])
                table.setText(rowAll, cols+4, reportLine['countVisit'])
                if reportLineList.get('', None):
                    del reportLineList['']
                for key, reportLine in reportLineList.items():
                    rowProfile = rowProfileIdList.get(key, None)
                    table.setText(rowProfile, cols, reportLine['countBed'])
                    table.setText(rowProfile, cols+1, reportLine['visitLeaved'])
                    table.setText(rowProfile, cols+2, reportLine['ageChildren'])
                    table.setText(rowProfile, cols+3, reportLine['countTransfer'])
                    table.setText(rowProfile, cols+4, reportLine['countVisit'])
                    reportLine['countBed'] = 0
                    reportLine['visitLeaved'] = 0
                    reportLine['ageChildren'] = 0
                    reportLine['countTransfer'] = 0
                    reportLine['countVisit'] = 0
                    reportLineList[key] = reportLine
            if not reportLineList.get('', None):
                reportLineList[''] = {'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0}


class CStationaryOneHospitalF14DC(CReportStationary):#actOneForma14DC CStationaryOnePolyclinicF14DC
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. Раздел I. Использование коечного фонда. Дневной стационар при больничном учреждении.')
        self.stationaryF14DCSetupDialog = None
        self.byActions = False


    def build(self, params):
        self.deathRuralLeavedStationary = 0
        self.deathLeavedStationary = 0
        db = QtGui.qApp.db
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        self.byActions = True if durationType == 2 else False
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            doc = QtGui.QTextDocument()
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            orgStructureTypeIdList = self.getOrgStructureTypeIdList(orgStructureIdList, 0)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'Раздел I. Использование коечного фонда\n(1100)')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('4%',[u'№стр.', u'', u'1'], CReportBase.AlignRight),
                    ('19%',[u'Профили коек.', u'', u'2'], CReportBase.AlignLeft),
                    ('11%', [u'Дневной стационар при больничном учреждении', u'Число мест', u'3'], CReportBase.AlignRight),
                    ('11%', [u'', u'число среднегодовых мест', u'4'], CReportBase.AlignRight),
                    ('11%', [u'', u'поступило больных', u'5'], CReportBase.AlignRight),
                    ('11%', [u'', u'выписано', u'6'], CReportBase.AlignRight),
                    ('11%', [u'', u'из них детей (0-17 лет)', '7'], CReportBase.AlignRight),
                    ('11%', [u'', u'в т.ч. круглосуточный стационар(из г.6)', u'8'], CReportBase.AlignRight),
                    ('11%', [u'', u'проведено больными дней лечения', u'9'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 2, 1)  # №стр
            table.mergeCells(0, 1, 2, 1)  # Профили коек
            table.mergeCells(0, 2, 1, 7)  # Дневной стационар при больничном учреждении
            if orgStructureTypeIdList:
                tableOSHB = db.table('OrgStructure_HospitalBed')
                tableRBHospitalBedProfile = db.table('rbHospitalBedProfile')
                cols = ['DISTINCT rbHospitalBedProfile.id, rbHospitalBedProfile.code, rbHospitalBedProfile.name']
                queryTable = tableOSHB.innerJoin(tableRBHospitalBedProfile, tableOSHB['profile_id'].eq(tableRBHospitalBedProfile['id']))
                bedProfileRecords = db.getRecordList(queryTable, cols, [tableOSHB['master_id'].inlist(orgStructureTypeIdList)])
                reportLineList = {'':{'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0}}
                bedProfileIdList = []
                for bedProfileRecord in bedProfileRecords:
                    profileId = forceRef(bedProfileRecord.value('id'))
                    if profileId not in bedProfileIdList:
                        bedProfileIdList.append(profileId)
                    if not reportLineList.get(profileId, None):
                        reportLine = {'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0}
                        reportLine['code'] = forceString(bedProfileRecord.value('code'))
                        reportLine['name'] = forceString(bedProfileRecord.value('name'))
                        reportLineList[profileId] = reportLine

                    reportLineList = self.unrolledHospitalBedEvent(orgStructureTypeIdList, begDate, endDate, reportLineList, profileId)
                    reportLineList = self.averageYarHospitalBedEvent(orgStructureTypeIdList, begDate, endDate, reportLineList, profileId)
                records, eventIdList = self.getDataEventHospital(orgStructureTypeIdList, begDate, endDate, bedProfileIdList, 0, groupingForMES, groupMES, MES, financeId)
                if records:
                    while records.next():
                        record = records.record()
                        profileId = forceRef(record.value('bedProfile'))
                        reportLine = reportLineList.get(profileId, None)
                        reportLineAll = reportLineList.get('', None)
                        deathLeaved = forceString(record.value('deathLeaved'))
                        countDeathLeaved = 1 if (u'умер' in deathLeaved or u'смерть' in deathLeaved) else 0
                        self.deathLeavedStationary += countDeathLeaved
                        self.deathRuralLeavedStationary += forceInt(record.value('deathRuralLeaved'))
                        if not reportLine:
                            bedRepRecord = db.getRecordEx(tableRBHospitalBedProfile, [tableRBHospitalBedProfile['code'], tableRBHospitalBedProfile['name']], [tableRBHospitalBedProfile['id'].eq(profileId)])
                            if bedRepRecord:
                                code = forceString(bedRepRecord.value('code'))
                                name = forceString(bedRepRecord.value('name'))
                                reportLine = {'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0}
                                reportLine['code'] = code
                                reportLine['name'] = name
                        if reportLine:
                            visitReceivedId = forceRef(record.value('visitReceivedId'))
                            visitReceivedDate = forceDate(record.value('visitReceivedDate'))
                            if visitReceivedDate >= begDate and (not endDate or visitReceivedDate <= endDate):
                                reportLine['visitReceived'] += 1
                                reportLineAll['visitReceived'] += 1
                            visitLeavedId = forceRef(record.value('visitLeavedId'))
                            visitLeavedDate = forceDate(record.value('visitLeavedDate'))
                            if (visitReceivedId != visitLeavedId) and visitLeavedDate >= begDate and (not endDate or visitLeavedDate <= endDate):
                                reportLine['visitLeaved'] += 1
                                reportLineAll['visitLeaved'] += 1
                                ageClient = forceInt(record.value('ageClient'))
                                if ageClient <= 17:
                                    reportLine['ageChildren'] += 1
                                    reportLineAll['ageChildren'] += 1
                            countTransfer = forceInt(record.value('countTransfer'))
                            if durationType == 0:
                                countVisit = forceInt(record.value('countVisit'))
                                reportLine['countVisit'] += countVisit
                                reportLineAll['countVisit'] += countVisit
                            reportLine['countTransfer'] += countTransfer
                            reportLineAll['countTransfer'] += countTransfer
                            reportLineList[profileId] = reportLine
                            reportLineList[''] = reportLineAll
                    if durationType > 0:
                        begDateTime = QDateTime(begDate, QTime(0, 0))
                        endDateTime = QDateTime(endDate, QTime(23, 59))
                        for profile in reportLineList.keys():
                            if profile == '':
                                reportLineList[profile]['countVisit'] = getMovingDays(orgStructureTypeIdList, begDateTime, endDateTime, bedProfileIdList)
                            else:
                                reportLineList[profile]['countVisit'] = getMovingDays(orgStructureTypeIdList, begDateTime, endDateTime, [profile])
                cnt = 1
                rowProfile = table.addRow()
                reportLine = reportLineList.get('', {'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0})
                table.setText(rowProfile, 0, cnt)
                table.setText(rowProfile, 1, u'ВСЕГО\nв том числе:')
                table.setText(rowProfile, 2, reportLine['countBed'])
                table.setText(rowProfile, 3, reportLine['countAverageBed'])
                table.setText(rowProfile, 4, reportLine['visitReceived'])
                table.setText(rowProfile, 5, reportLine['visitLeaved'])
                table.setText(rowProfile, 6, reportLine['ageChildren'])
                table.setText(rowProfile, 7, reportLine['countTransfer'])
                table.setText(rowProfile, 8, reportLine['countVisit'])
                if reportLineList.get('', None):
                    del reportLineList['']
                for key, reportLine in reportLineList.items():
                    rowProfile = table.addRow()
                    cnt += 1
                    table.setText(rowProfile, 0, cnt)
                    table.setText(rowProfile, 1, reportLine['name'])
                    table.setText(rowProfile, 2, reportLine['countBed'])
                    table.setText(rowProfile, 3, reportLine['countAverageBed'])
                    table.setText(rowProfile, 4, reportLine['visitReceived'])
                    table.setText(rowProfile, 5, reportLine['visitLeaved'])
                    table.setText(rowProfile, 6, reportLine['ageChildren'])
                    table.setText(rowProfile, 7, reportLine['countTransfer'])
                    table.setText(rowProfile, 8, reportLine['countVisit'])


            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(u'''(1101) Из числа выбывших умерло в дневном стационаре больничного учреждения - %d.'''%(self.deathLeavedStationary))
            cursor.insertBlock()
            cursor.insertText(u'''(1102) Из числа выбывших сельские жители: в дневном стационаре больничного учреждения - %d.'''%(self.deathRuralLeavedStationary))
            cursor.insertBlock()
        return doc


class CStationaryOnePolyclinicF14DC(CReportStationary):#actOneForma14DC
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. Раздел I. Использование коечного фонда. Дневной стационар при амбулаторно-поликлинических учреждениях.')
        self.stationaryF14DCSetupDialog = None


    def build(self, params):
        db = QtGui.qApp.db
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        self.byActions = True if durationType == 2 else False
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            doc = QtGui.QTextDocument()
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            orgStructureTypeIdList = self.getOrgStructureTypeIdList(orgStructureIdList, 1)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'Раздел I. Использование коечного фонда\n(1100)')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('4%',[u'№стр.', u'', u'1'], CReportBase.AlignRight),
                    ('19%',[u'Профили коек.', u'', u'2'], CReportBase.AlignLeft),
                    ('11%', [u'Дневной стационар при амбулаторно-поликлинических учреждениях', u'Число мест', u'3'], CReportBase.AlignRight),
                    ('11%', [u'', u'число среднегодовых мест', u'4'], CReportBase.AlignRight),
                    ('11%', [u'', u'поступило больных', u'5'], CReportBase.AlignRight),
                    ('11%', [u'', u'выписано', u'6'], CReportBase.AlignRight),
                    ('11%', [u'', u'из них детей (0-17 лет)', '7'], CReportBase.AlignRight),
                    ('11%', [u'', u'в т.ч. круглосуточный стационар(из г.6)', u'8'], CReportBase.AlignRight),
                    ('11%', [u'', u'проведено больными дней лечения', u'9'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 2, 1)  # №стр
            table.mergeCells(0, 1, 2, 1)  # Профили коек
            table.mergeCells(0, 2, 1, 7)  # Дневной стационар при амбулаторно-поликлинических учреждениях
            if orgStructureTypeIdList:
                tableOSHB = db.table('OrgStructure_HospitalBed')
                tableRBHospitalBedProfile = db.table('rbHospitalBedProfile')
                cols = ['DISTINCT rbHospitalBedProfile.id, rbHospitalBedProfile.code, rbHospitalBedProfile.name']
                queryTable = tableOSHB.innerJoin(tableRBHospitalBedProfile, tableOSHB['profile_id'].eq(tableRBHospitalBedProfile['id']))
                bedProfileRecords = db.getRecordList(queryTable, cols, [tableOSHB['master_id'].inlist(orgStructureTypeIdList)])
                reportLineList = {'':{'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0}}
                bedProfileIdList = []
                for bedProfileRecord in bedProfileRecords:
                    profileId = forceRef(bedProfileRecord.value('id'))
                    if profileId not in bedProfileIdList:
                        bedProfileIdList.append(profileId)
                    if not reportLineList.get(profileId, None):
                        reportLine = {'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0}
                        reportLine['code'] = forceString(bedProfileRecord.value('code'))
                        reportLine['name'] = forceString(bedProfileRecord.value('name'))
                        reportLineList[profileId] = reportLine

                    reportLineList = self.unrolledHospitalBedEvent(orgStructureTypeIdList, begDate, endDate, reportLineList, profileId)
                    reportLineList = self.averageYarHospitalBedEvent(orgStructureTypeIdList, begDate, endDate, reportLineList, profileId)
                records, eventIdList = self.getDataEventHospital(orgStructureTypeIdList, begDate, endDate, bedProfileIdList, 1, groupingForMES, groupMES, MES, financeId)
                if records:
                    while records.next():
                        record = records.record()
                        profileId = forceRef(record.value('bedProfile'))
                        reportLine = reportLineList.get(profileId, None)
                        reportLineAll = reportLineList.get('', None)
                        deathLeaved = forceString(record.value('deathLeaved'))
                        countDeathLeaved = 1 if (u'умер' in deathLeaved or u'смерть' in deathLeaved) else 0
                        if not reportLine:
                            bedRepRecord = db.getRecordEx(tableRBHospitalBedProfile, [tableRBHospitalBedProfile['code'], tableRBHospitalBedProfile['name']], [tableRBHospitalBedProfile['id'].eq(profileId)])
                            if bedRepRecord:
                                code = forceString(bedRepRecord.value('code'))
                                name = forceString(bedRepRecord.value('name'))
                                reportLine = {'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0}
                                reportLine['code'] = code
                                reportLine['name'] = name
                        if reportLine:
                            visitReceivedId = forceRef(record.value('visitReceivedId'))
                            visitReceivedDate = forceDate(record.value('visitReceivedDate'))
                            if visitReceivedDate >= begDate and (not endDate or visitReceivedDate <= endDate):
                                reportLine['visitReceived'] += 1
                                reportLineAll['visitReceived'] += 1
                            visitLeavedId = forceRef(record.value('visitLeavedId'))
                            visitLeavedDate = forceDate(record.value('visitLeavedDate'))
                            if (visitReceivedId != visitLeavedId) and visitLeavedDate >= begDate and (not endDate or visitLeavedDate <= endDate):
                                reportLine['visitLeaved'] += 1
                                reportLineAll['visitLeaved'] += 1
                                self.deathLeavedAmbulance += countDeathLeaved
                                self.deathRuralLeavedAmbulance += forceInt(record.value('deathRuralLeaved'))
                            ageClient = forceInt(record.value('ageClient'))
                            if ageClient <= 17:
                                reportLine['ageChildren'] += 1
                                reportLineAll['ageChildren'] += 1
                            countTransfer = forceInt(record.value('countTransfer'))
                            if durationType == 0:
                                countVisit = forceInt(record.value('countVisit'))
                                reportLine['countVisit'] += countVisit
                                reportLineAll['countVisit'] += countVisit
                            reportLine['countTransfer'] += countTransfer
                            reportLineAll['countTransfer'] += countTransfer
                            reportLineList[profileId] = reportLine
                            reportLineList[''] = reportLineAll
                    if durationType > 0:
                        begDateTime = QDateTime(begDate, QTime(0, 0))
                        endDateTime = QDateTime(endDate, QTime(23, 59))
                        for profile in reportLineList.keys():
                            if profile == '':
                                reportLineList[profile]['countVisit'] = getMovingDays(orgStructureTypeIdList, begDateTime, endDateTime, bedProfileIdList)
                            else:
                                reportLineList[profile]['countVisit'] = getMovingDays(orgStructureTypeIdList, begDateTime, endDateTime, [profile])
                cnt = 1
                rowProfile = table.addRow()
                reportLine = reportLineList.get('', {'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0})
                table.setText(rowProfile, 0, cnt)
                table.setText(rowProfile, 1, u'ВСЕГО\nв том числе:')
                table.setText(rowProfile, 2, reportLine['countBed'])
                table.setText(rowProfile, 3, reportLine['countAverageBed'])
                table.setText(rowProfile, 4, reportLine['visitReceived'])
                table.setText(rowProfile, 5, reportLine['visitLeaved'])
                table.setText(rowProfile, 6, reportLine['ageChildren'])
                table.setText(rowProfile, 7, reportLine['countTransfer'])
                table.setText(rowProfile, 8, reportLine['countVisit'])
                if reportLineList.get('', None):
                    del reportLineList['']
                for key, reportLine in reportLineList.items():
                    rowProfile = table.addRow()
                    cnt += 1
                    table.setText(rowProfile, 0, cnt)
                    table.setText(rowProfile, 1, reportLine['name'])
                    table.setText(rowProfile, 2, reportLine['countBed'])
                    table.setText(rowProfile, 3, reportLine['countAverageBed'])
                    table.setText(rowProfile, 4, reportLine['visitReceived'])
                    table.setText(rowProfile, 5, reportLine['visitLeaved'])
                    table.setText(rowProfile, 6, reportLine['ageChildren'])
                    table.setText(rowProfile, 7, reportLine['countTransfer'])
                    table.setText(rowProfile, 8, reportLine['countVisit'])
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(u'''(1101) Из числа выбывших умерло в дневном стационаре амбулаторно-поликлинического учреждения - %d. '''%(self.deathLeavedAmbulance))
            cursor.insertBlock()
            cursor.insertText(u'''(1102) Из числа выбывших сельские жители: в дневном стационаре амбулаторно-поликлинического учреждения - %d.'''%(self.deathRuralLeavedAmbulance))
            cursor.insertBlock()
        return doc


class CStationaryOneHouseF14DC(CReportStationary):#actOneForma14DC
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. Раздел I. Использование коечного фонда. Стационар на дому.')
        self.stationaryF14DCSetupDialog = None


    def build(self, params):
        db = QtGui.qApp.db
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        self.byActions = True if durationType == 2 else False
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            doc = QtGui.QTextDocument()
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            orgStructureTypeIdList = self.getOrgStructureTypeIdList(orgStructureIdList, 2)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'Раздел I. Использование коечного фонда\n(1100)')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('4%',[u'№стр.', u'', u'1'], CReportBase.AlignRight),
                    ('21%',[u'Профили коек.', u'', u'2'], CReportBase.AlignLeft),
                    ('15%', [u'Стационар на дому', u'Число мест', u'3'], CReportBase.AlignRight),
                    ('15%', [u'', u'выписано', u'4'], CReportBase.AlignRight),
                    ('15%', [u'', u'из них детей (0-17 лет)', '5'], CReportBase.AlignRight),
                    ('15%', [u'', u'в т.ч. круглосуточный стационар(из г.18)', u'6'], CReportBase.AlignRight),
                    ('15%', [u'', u'проведено больными дней лечения', u'7'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 2, 1)  # №стр
            table.mergeCells(0, 1, 2, 1)  # Профили коек
            table.mergeCells(0, 2, 1, 5) # Стационар на дому
            if orgStructureTypeIdList:
                tableOSHB = db.table('OrgStructure_HospitalBed')
                tableRBHospitalBedProfile = db.table('rbHospitalBedProfile')
                cols = ['DISTINCT rbHospitalBedProfile.id, rbHospitalBedProfile.code, rbHospitalBedProfile.name']
                queryTable = tableOSHB.innerJoin(tableRBHospitalBedProfile, tableOSHB['profile_id'].eq(tableRBHospitalBedProfile['id']))
                bedProfileRecords = db.getRecordList(queryTable, cols, [tableOSHB['master_id'].inlist(orgStructureTypeIdList)])
                bedProfileIdList = []
                for bedProfileRecord in bedProfileRecords:
                    profileId = forceRef(bedProfileRecord.value('id'))
                    if profileId not in bedProfileIdList:
                        bedProfileIdList.append(profileId)
                records, eventIdList = self.getDataEventHospital(orgStructureTypeIdList, begDate, endDate, bedProfileIdList, 2, groupingForMES, groupMES, MES, financeId)
                bedProfileRecords = self.getProfilEventHospital(eventIdList)
                reportLineList = {'':{'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0}}
                profileIdList = []
                for bedProfileRecord in bedProfileRecords:
                    profileId = forceRef(bedProfileRecord.value('id'))
                    if profileId not in profileIdList:
                        profileIdList.append(profileId)
                    if not reportLineList.get(profileId, None):
                        reportLine = {'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0}
                        reportLine['code'] = forceString(bedProfileRecord.value('code'))
                        reportLine['name'] = forceString(bedProfileRecord.value('name'))
                        reportLineList[profileId] = reportLine
                    reportLineList = self.unrolledHospitalBedEvent(orgStructureTypeIdList, begDate, endDate, reportLineList, profileId)
                if records:
                    while records.next():
                        record = records.record()
                        profileId = forceRef(record.value('bedProfile'))
                        reportLine = reportLineList.get(profileId, None)
                        reportLineAll = reportLineList.get('', None)
                        deathLeaved = forceString(record.value('deathLeaved'))
                        countDeathLeaved = 1 if (u'умер' in deathLeaved or u'смерть' in deathLeaved) else 0
                        self.deathLeavedHouse += countDeathLeaved
                        self.deathRuralLeavedHouse += forceInt(record.value('deathRuralLeaved'))
                        if not reportLine:
                            bedRepRecord = db.getRecordEx(tableRBHospitalBedProfile, [tableRBHospitalBedProfile['code'], tableRBHospitalBedProfile['name']], [tableRBHospitalBedProfile['id'].eq(profileId)])
                            if bedRepRecord:
                                code = forceString(bedRepRecord.value('code'))
                                name = forceString(bedRepRecord.value('name'))
                                reportLine = {'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0}
                                reportLine['code'] = code
                                reportLine['name'] = name
                        if reportLine:
                            visitReceivedId = forceRef(record.value('visitReceivedId'))
                            visitReceivedDate = forceDate(record.value('visitReceivedDate'))
                            if visitReceivedDate >= begDate and (not endDate or visitReceivedDate <= endDate):
                                reportLine['visitReceived'] += 1
                                reportLineAll['visitReceived'] += 1
                            visitLeavedId = forceRef(record.value('visitLeavedId'))
                            visitLeavedDate = forceDate(record.value('visitLeavedDate'))
                            if (visitReceivedId != visitLeavedId) and visitLeavedDate >= begDate and (not endDate or visitLeavedDate <= endDate):
                                reportLine['visitLeaved'] += 1
                                reportLineAll['visitLeaved'] += 1
                            ageClient = forceInt(record.value('ageClient'))
                            if ageClient <= 17:
                                reportLine['ageChildren'] += 1
                                reportLineAll['ageChildren'] += 1
                            countTransfer = forceInt(record.value('countTransfer'))
                            if durationType == 0:
                                countVisit = forceInt(record.value('countVisit'))
                            elif durationType == 1:
                                setDate = forceDate(record.value('setDate'))
                                execDate = forceDate(record.value('execDate'))
                                countVisit = setDate.daysTo(execDate)+1
                            elif durationType == 2:
                                countVisit = 0
                            reportLine['countTransfer'] += countTransfer
                            reportLine['countVisit'] += countVisit
                            reportLineAll['countTransfer'] += countTransfer
                            reportLineAll['countVisit'] += countVisit
                            reportLineList[profileId] = reportLine
                            reportLineList[''] = reportLineAll
                    cnt = 1
                    rowProfile = table.addRow()
                    reportLine = reportLineList.get('', {'code':'', 'name':'', 'visitReceived':0, 'visitLeaved':0, 'ageChildren':0, 'countTransfer':0, 'countVisit':0, 'countBed':0, 'countAverageBed':0})
                    table.setText(rowProfile, 0, cnt)
                    table.setText(rowProfile, 1, u'ВСЕГО\nв том числе:')
                    table.setText(rowProfile, 2, reportLine['countBed'])
                    table.setText(rowProfile, 3, reportLine['visitLeaved'])
                    table.setText(rowProfile, 4, reportLine['ageChildren'])
                    table.setText(rowProfile, 5, reportLine['countTransfer'])
                    table.setText(rowProfile, 6, reportLine['countVisit'])
                    if reportLineList.get('', None):
                        del reportLineList['']
                    for key, reportLine in reportLineList.items():
                        rowProfile = table.addRow()
                        cnt += 1
                        table.setText(rowProfile, 0, cnt)
                        table.setText(rowProfile, 1, reportLine['name'])
                        table.setText(rowProfile, 2, reportLine['countBed'])
                        table.setText(rowProfile, 3, reportLine['visitLeaved'])
                        table.setText(rowProfile, 4, reportLine['ageChildren'])
                        table.setText(rowProfile, 5, reportLine['countTransfer'])
                        table.setText(rowProfile, 6, reportLine['countVisit'])
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(u'''(1101) Из числа выбывших умерло в дневном стационаре на дому - %d. '''%(self.deathLeavedHouse))
            cursor.insertBlock()
            cursor.insertText(u'''(1102) Из числа выбывших сельские жители: в стационаре на дому - %d.'''%(self.deathRuralLeavedHouse))
            cursor.insertBlock()
        return doc


class CStationaryTwoAdultF14DC(CReportStationary):#actTwoAdultForma14D
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. Раздел II. 18 лет и старше. Общий.')
        self.stationaryF14DCSetupDialog = None


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        self.byActions = True if durationType == 2 else False
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            rowSize = 12
            mapMainRows = createMapCodeToRowIdx( [row[2] for row in TwoRows] )
            reportMainData = [ [0]*rowSize for row in xrange(len(TwoRows)) ]
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = []
            if orgStructureIndex.isValid():
                treeItem = orgStructureIndex.internalPointer()
                if treeItem._id:
                    orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            titleText = u'Раздел II. Состав больных в дневном стационаре, сроки и исходы лечения\n(2000) (18 лет и старше)'
            cursor.insertText(titleText)
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('7%',[u'', u'', u'1'], CReportBase.AlignLeft),
                    ('7%',[u'№ строки', u'', u'2'], CReportBase.AlignRight),
                    ('7%', [u'Код по МКБ-X', u'', u'3'], CReportBase.AlignLeft),
                    ('7%', [u'Дневной стационар при больничных учреждениях', u'выписано больных', u'4'], CReportBase.AlignRight),
                    ('7%', [u'', u'из них направлено в круглосуточн. Стационар', u'5'], CReportBase.AlignRight),
                    ('7%', [u'', u'проведено выписанными больными дней лечения', u'6'], CReportBase.AlignRight),
                    ('7%', [u'', u'умерло', '7'], CReportBase.AlignRight),

                    ('7%', [u'Дневной стационар при амбулаторно-поликлинических учреждениях', u'выписано больных', u'8'], CReportBase.AlignRight),
                    ('7%', [u'', u'из них направлено в круглосуточн. Стационар', u'9'], CReportBase.AlignRight),
                    ('7%', [u'', u'проведено выписанными больными дней лечения', u'10'], CReportBase.AlignRight),
                    ('7%', [u'', u'умерло', u'11'], CReportBase.AlignRight),

                    ('7%', [u'Стационар на дому', u'выписано больных', u'12'], CReportBase.AlignRight),
                    ('7%', [u'', u'из них направлено в круглосуточн. Стационар', u'13'], CReportBase.AlignRight),
                    ('7%', [u'', u'проведено выписанными больными дней лечения', u'14'], CReportBase.AlignRight),
                    ('7%', [u'', u'умерло', u'15'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 2, 1)  # название
            table.mergeCells(0, 1, 2, 1)  # №стр
            table.mergeCells(0, 2, 2, 1)  # код по МКБ
            table.mergeCells(0, 3, 1, 4)  # Дневной стационар при больничных учреждениях
            table.mergeCells(0, 7, 1, 4)  # Дневной стационар при амбулаторно-поликлинических учреждениях
            table.mergeCells(0, 11, 1, 4) # Дневной стационар при амбулаторно-поликлинических учреждениях

            isHospitals = [(0, 0), (4, 1), (8, 2)]
            medicalCheckupHealthy = 0
            leavedEnlistmentSum = 0
            conscript = 0
            for i, isHospital in isHospitals:
                records = self.getDataEventAdult(orgStructureIdList, begDate, endDate, u'''(age(Client.birthDate, Event.setDate)) >= 18''', isHospital, groupingForMES, groupMES, MES, financeId)
                if records:
                    while records.next():
                        record = records.record()
                        MKBRec = normalizeMKB(forceString(record.value('MKB')))
                        visitLeavedDate = forceDate(record.value('visitLeavedDate'))
                        countTransfer = forceInt(record.value('countTransfer'))
                        countDeath = forceInt(record.value('countDeath'))
                        countVisit = 0
                        if durationType == 0:
                            countVisit = forceInt(record.value('countVisit'))
                        elif durationType >= 1:
                            setDate = forceDateTime(record.value('setDate'))
                            execDate = forceDateTime(record.value('execDate'))
                            countVisit = countMovingDays(setDate, execDate, QDateTime(begDate, QTime(0, 0)), QDateTime(endDate, QTime(23, 59)), 2)
                        countSurgery = forceInt(record.value('countSurgery'))
                        healthGroup = forceInt(record.value('healthGroup'))
                        relegateOrg = forceInt(record.value('relegateOrg'))
                        medicalCheckupHealthy =+ healthGroup
                        leavedEnlistmentSum += relegateOrg
                        if relegateOrg and healthGroup:
                            conscript += 1
                        for row in mapMainRows.get(MKBRec, []):
                            reportLine = reportMainData[row]
                            if visitLeavedDate and visitLeavedDate <= endDate:
                                reportLine[i] += 1
                            reportLine[i+1] += countTransfer
                            reportLine[i+2] += countVisit
                            reportLine[i+3] += countDeath
                        if countSurgery:
                            reportLine = reportMainData[len(TwoRows)-2]
                            if visitLeavedDate and visitLeavedDate <= endDate:
                                reportLine[i] += 1
                            reportLine[i+1] += countTransfer
                            reportLine[i+2] = u'X'
                            reportLine[i+3] += countDeath
                            reportLine = reportMainData[len(TwoRows)-1]
                            if visitLeavedDate and visitLeavedDate <= endDate:
                                reportLine[i] += countSurgery
                            reportLine[i+1] = u'X'
                            reportLine[i+2] = u'X'
                            reportLine[i+3] = u'X'
            for row, rowDescr in enumerate(TwoRows):
                reportLine = reportMainData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])

            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(u'''(2001) Из общего числа выписанных - (гр. 4, 8) – направленные райвоенкоматом %d. '''%(leavedEnlistmentSum))
            cursor.insertBlock()
            cursor.insertText(u'''(2002) Кроме того лица, госпитализированные для обследования и оказавшиеся здоровыми  %d, из них призывники %d .'''%(medicalCheckupHealthy, conscript))
            cursor.insertBlock()

        return doc


class CStationaryTwoAdultHospitalF14DC(CReportStationary):#actTwoAdultForma14D
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. Раздел II. 18 лет и старше. Дневной стационар при больничном учреждении.')
        self.stationaryF14DCSetupDialog = None


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        self.byActions = True if durationType == 2 else False
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            rowSize = 4
            mapMainRows = createMapCodeToRowIdx( [row[2] for row in TwoRows] )
            reportMainData = [ [0]*rowSize for row in xrange(len(TwoRows)) ]
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
#            orgStructureIdList = []
#            if orgStructureIndex.isValid():
#                treeItem = orgStructureIndex.internalPointer()
#                if treeItem._id:
#                    orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            orgStructureTypeIdList = self.getOrgStructureTypeIdList(orgStructureIdList, 0)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            titleText = u'Раздел II. Состав больных в дневном стационаре, сроки и исходы лечения\n(2000) (18 лет и старше)'
            cursor.insertText(titleText)
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('21%',[u'', u'', u'1'], CReportBase.AlignLeft),
                    ('4%',[u'№ строки', u'', u'2'], CReportBase.AlignRight),
                    ('15%', [u'Код по МКБ-X', u'', u'3'], CReportBase.AlignLeft),
                    ('15%', [u'Дневной стационар при больничных учреждениях', u'выписано больных', u'4'], CReportBase.AlignRight),
                    ('15%', [u'', u'из них направлено в круглосуточн. Стационар', u'5'], CReportBase.AlignRight),
                    ('15%', [u'', u'проведено выписанными больными дней лечения', u'6'], CReportBase.AlignRight),
                    ('15%', [u'', u'умерло', '7'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 2, 1)  # название
            table.mergeCells(0, 1, 2, 1)  # №стр
            table.mergeCells(0, 2, 2, 1)  # код по МКБ
            table.mergeCells(0, 3, 1, 4)  # Дневной стационар при больничных учреждениях
            medicalCheckupHealthy = 0
            leavedEnlistmentSum = 0
            conscript = 0
            records = self.getDataEventAdult(orgStructureTypeIdList, begDate, endDate, u'''(age(Client.birthDate, Event.setDate)) >= 18''', 0, groupingForMES, groupMES, MES, financeId)
            if records:
                while records.next():
                    record = records.record()
                    MKBRec = normalizeMKB(forceString(record.value('MKB')))
                    visitLeavedDate = forceDate(record.value('visitLeavedDate'))
                    countTransfer = forceInt(record.value('countTransfer'))
                    countDeath = forceInt(record.value('countDeath'))
                    countVisit = 0
                    if durationType == 0:
                        countVisit = forceInt(record.value('countVisit'))
                    elif durationType >= 1:
                        setDate = forceDateTime(record.value('setDate'))
                        execDate = forceDateTime(record.value('execDate'))
                        countVisit = countMovingDays(setDate, execDate, QDateTime(begDate, QTime(0, 0)), QDateTime(endDate, QTime(23, 59)), 2)
                    countSurgery = forceInt(record.value('countSurgery'))
                    healthGroup = forceInt(record.value('healthGroup'))
                    relegateOrg = forceInt(record.value('relegateOrg'))
                    medicalCheckupHealthy =+ healthGroup
                    leavedEnlistmentSum += relegateOrg
                    if relegateOrg and healthGroup:
                        conscript += 1

                    for row in mapMainRows.get(MKBRec, []):
                        reportLine = reportMainData[row]
                        if visitLeavedDate and visitLeavedDate <= endDate:
                            reportLine[0] += 1
                        reportLine[1] += countTransfer
                        reportLine[2] += countVisit
                        reportLine[3] += countDeath
                    if countSurgery:
                        reportLine = reportMainData[len(TwoRows)-2]
                        if visitLeavedDate and visitLeavedDate <= endDate:
                            reportLine[0] += 1
                        reportLine[1] += countTransfer
                        reportLine[2] = u'X'
                        reportLine[3] += countDeath
                        reportLine = reportMainData[len(TwoRows)-1]
                        if visitLeavedDate and visitLeavedDate <= endDate:
                            reportLine[0] += countSurgery
                        reportLine[1] = u'X'
                        reportLine[2] = u'X'
                        reportLine[3] = u'X'
            for row, rowDescr in enumerate(TwoRows):
                reportLine = reportMainData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(u'''(2001) Из общего числа выписанных - (гр. 4, 8) – направленные райвоенкоматом %d. '''%(leavedEnlistmentSum))
            cursor.insertBlock()
            cursor.insertText(u'''(2002) Кроме того лица, госпитализированные для обследования и оказавшиеся здоровыми  %d, из них призывники %d .'''%(medicalCheckupHealthy, conscript))
            cursor.insertBlock()
        return doc


class CStationaryTwoAdultPoliclinicF14DC(CReportStationary):#actTwoAdultForma14D
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. Раздел II. 18 лет и старше. Дневной стационар при амбулаторно-поликлинических учреждениях.')
        self.stationaryF14DCSetupDialog = None


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        self.byActions = True if durationType == 2 else False
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            rowSize = 4
            mapMainRows = createMapCodeToRowIdx( [row[2] for row in TwoRows] )
            reportMainData = [ [0]*rowSize for row in xrange(len(TwoRows)) ]
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = []
            if orgStructureIndex.isValid():
                treeItem = orgStructureIndex.internalPointer()
                if treeItem._id:
                    orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            titleText = u'Раздел II. Состав больных в дневном стационаре, сроки и исходы лечения\n(2000) (18 лет и старше)'
            cursor.insertText(titleText)
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('21%',[u'', u'', u'1'], CReportBase.AlignLeft),
                    ('4%',[u'№ строки', u'', u'2'], CReportBase.AlignRight),
                    ('15%', [u'Код по МКБ-X', u'', u'3'], CReportBase.AlignLeft),
                    ('15%', [u'Дневной стационар при амбулаторно-поликлинических учреждениях', u'выписано больных', u'4'], CReportBase.AlignRight),
                    ('15%', [u'', u'из них направлено в круглосуточн. Стационар', u'5'], CReportBase.AlignRight),
                    ('15%', [u'', u'проведено выписанными больными дней лечения', u'6'], CReportBase.AlignRight),
                    ('15%', [u'', u'умерло', u'7'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 2, 1)  # название
            table.mergeCells(0, 1, 2, 1)  # №стр
            table.mergeCells(0, 2, 2, 1)  # код по МКБ
            table.mergeCells(0, 3, 1, 4)  # Дневной стационар при амбулаторно-поликлинических учреждениях
            medicalCheckupHealthy = 0
            leavedEnlistmentSum = 0
            conscript = 0
            records = self.getDataEventAdult(orgStructureIdList, begDate, endDate, u'''(age(Client.birthDate, Event.setDate)) >= 18''', 1, groupingForMES, groupMES, MES, financeId)
            if records:
                while records.next():
                    record = records.record()
                    MKBRec = normalizeMKB(forceString(record.value('MKB')))
                    visitLeavedDate = forceDate(record.value('visitLeavedDate'))
                    countTransfer = forceInt(record.value('countTransfer'))
                    countDeath = forceInt(record.value('countDeath'))
                    countVisit = 0
                    if durationType == 0:
                        countVisit = forceInt(record.value('countVisit'))
                    elif durationType == 1:
                        setDate = forceDate(record.value('setDate'))
                        execDate = forceDate(record.value('execDate'))
                        countVisit = setDate.daysTo(execDate)+1
                    elif durationType == 2:
                        countVisit = forceInt(record.value('countActions'))
                    countSurgery = forceInt(record.value('countSurgery'))
                    healthGroup = forceInt(record.value('healthGroup'))
                    relegateOrg = forceInt(record.value('relegateOrg'))
                    medicalCheckupHealthy =+ healthGroup
                    leavedEnlistmentSum += relegateOrg
                    if relegateOrg and healthGroup:
                        conscript += 1

                    for row in mapMainRows.get(MKBRec, []):
                        reportLine = reportMainData[row]
                        if visitLeavedDate:
                            reportLine[0] += 1
                        reportLine[1] += countTransfer
                        reportLine[2] += countVisit
                        reportLine[3] += countDeath
                    if countSurgery:
                        reportLine = reportMainData[len(TwoRows)-2]
                        if visitLeavedDate:
                            reportLine[0] += 1
                        reportLine[1] += countTransfer
                        reportLine[2] = u'X'
                        reportLine[3] += countDeath
                        reportLine = reportMainData[len(TwoRows)-1]
                        if visitLeavedDate:
                            reportLine[0] += countSurgery
                        reportLine[1] = u'X'
                        reportLine[2] = u'X'
                        reportLine[3] = u'X'
            for row, rowDescr in enumerate(TwoRows):
                reportLine = reportMainData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(u'''(2001) Из общего числа выписанных - (гр. 4, 8) – направленные райвоенкоматом %d. '''%(leavedEnlistmentSum))
            cursor.insertBlock()
            cursor.insertText(u'''(2002) Кроме того лица, госпитализированные для обследования и оказавшиеся здоровыми  %d, из них призывники %d .'''%(medicalCheckupHealthy, conscript))
            cursor.insertBlock()
        return doc


class CStationaryTwoAdultHouseF14DC(CReportStationary):#actTwoAdultForma14D
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. Раздел II. 18 лет и старше. Стационар на дому.')
        self.stationaryF14DCSetupDialog = None


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        self.byActions = True if durationType == 2 else False
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            rowSize = 4
            mapMainRows = createMapCodeToRowIdx( [row[2] for row in TwoRows] )
            reportMainData = [ [0]*rowSize for row in xrange(len(TwoRows)) ]
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = []
            if orgStructureIndex.isValid():
                treeItem = orgStructureIndex.internalPointer()
                if treeItem._id:
                    orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            titleText = u'Раздел II. Состав больных в дневном стационаре, сроки и исходы лечения\n(2000) (18 лет и старше)'
            cursor.insertText(titleText)
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('21%',[u'', u'', u'1'], CReportBase.AlignLeft),
                    ('4%',[u'№ строки', u'', u'2'], CReportBase.AlignRight),
                    ('15%', [u'Код по МКБ-X', u'', u'3'], CReportBase.AlignLeft),
                    ('15%', [u'Стационар на дому', u'выписано больных', u'4'], CReportBase.AlignRight),
                    ('15%', [u'', u'из них направлено в круглосуточн. Стационар', u'5'], CReportBase.AlignRight),
                    ('15%', [u'', u'проведено выписанными больными дней лечения', u'6'], CReportBase.AlignRight),
                    ('15%', [u'', u'умерло', u'7'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 2, 1)  # название
            table.mergeCells(0, 1, 2, 1)  # №стр
            table.mergeCells(0, 2, 2, 1)  # код по МКБ
            table.mergeCells(0, 3, 1, 4)  # Стационар на дому
            medicalCheckupHealthy = 0
            leavedEnlistmentSum = 0
            conscript = 0
            records = self.getDataEventAdult(orgStructureIdList, begDate, endDate, u'''(age(Client.birthDate, Event.setDate)) >= 18''', 2, groupingForMES, groupMES, MES, financeId)
            if records:
                while records.next():
                    record = records.record()
                    MKBRec = normalizeMKB(forceString(record.value('MKB')))
                    visitLeavedDate = forceDate(record.value('visitLeavedDate'))
                    countTransfer = forceInt(record.value('countTransfer'))
                    countDeath = forceInt(record.value('countDeath'))
                    countVisit = 0
                    if durationType == 0:
                        countVisit = forceInt(record.value('countVisit'))
                    elif durationType == 1:
                        setDate = forceDate(record.value('setDate'))
                        execDate = forceDate(record.value('execDate'))
                        countVisit = setDate.daysTo(execDate)+1
                    elif durationType == 2:
                        countVisit = forceInt(record.value('countActions'))
                    countSurgery = forceInt(record.value('countSurgery'))
                    healthGroup = forceInt(record.value('healthGroup'))
                    relegateOrg = forceInt(record.value('relegateOrg'))
                    medicalCheckupHealthy =+ healthGroup
                    leavedEnlistmentSum += relegateOrg
                    if relegateOrg and healthGroup:
                        conscript += 1

                    for row in mapMainRows.get(MKBRec, []):
                        reportLine = reportMainData[row]
                        if visitLeavedDate:
                            reportLine[0] += 1
                        reportLine[1] += countTransfer
                        reportLine[2] += countVisit
                        reportLine[3] += countDeath
                    if countSurgery:
                        reportLine = reportMainData[len(TwoRows)-2]
                        if visitLeavedDate:
                            reportLine[0] += 1
                        reportLine[1] += countTransfer
                        reportLine[2] = u'X'
                        reportLine[3] += countDeath
                        reportLine = reportMainData[len(TwoRows)-1]
                        if visitLeavedDate:
                            reportLine[0] += countSurgery
                        reportLine[1] = u'X'
                        reportLine[2] = u'X'
                        reportLine[3] = u'X'
            for row, rowDescr in enumerate(TwoRows):
                reportLine = reportMainData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(u'''(2001) Из общего числа выписанных - (гр. 4, 8) – направленные райвоенкоматом %d. '''%(leavedEnlistmentSum))
            cursor.insertBlock()
            cursor.insertText(u'''(2002) Кроме того лица, госпитализированные для обследования и оказавшиеся здоровыми  %d, из них призывники %d .'''%(medicalCheckupHealthy, conscript))
            cursor.insertBlock()
        return doc


class CStationaryTwoChildrenF14DC(CReportStationary):#actTwoChildrenForma14DC
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. Раздел II. Дети 0-17 лет включительно. Общий.')
        self.stationaryF14DCSetupDialog = None


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        self.byActions = True if durationType == 2 else False
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            rowSize = 12
            mapMainRows = createMapCodeToRowIdx( [row[2] for row in ThreeRows] )
            reportMainData = [ [0]*rowSize for row in xrange(len(ThreeRows)) ]
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = []
            if orgStructureIndex.isValid():
                treeItem = orgStructureIndex.internalPointer()
                if treeItem._id:
                    orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            titleText = u'Раздел II. Состав больных в дневном стационаре, сроки и исходы лечения\n(2003) (дети 0-17 лет включительно)'
            cursor.insertText(titleText)
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('7%',[u'', u'', u'1'], CReportBase.AlignLeft),
                    ('7%',[u'№ строки', u'', u'2'], CReportBase.AlignRight),
                    ('7%', [u'Код по МКБ-X', u'', u'3'], CReportBase.AlignLeft),
                    ('7%', [u'Дневной стационар при больничных учреждениях', u'выписано больных', u'4'], CReportBase.AlignRight),
                    ('7%', [u'', u'из них направлено в круглосуточн. Стационар', u'5'], CReportBase.AlignRight),
                    ('7%', [u'', u'проведено выписанными больными дней лечения', u'6'], CReportBase.AlignRight),
                    ('7%', [u'', u'умерло', '7'], CReportBase.AlignRight),

                    ('7%', [u'Дневной стационар при амбулаторно-поликлинических учреждениях', u'выписано больных', u'8'], CReportBase.AlignRight),
                    ('7%', [u'', u'из них направлено в круглосуточн. Стационар', u'9'], CReportBase.AlignRight),
                    ('7%', [u'', u'проведено выписанными больными дней лечения', u'10'], CReportBase.AlignRight),
                    ('7%', [u'', u'умерло', u'11'], CReportBase.AlignRight),

                    ('7%', [u'Стационар на дому', u'выписано больных', u'12'], CReportBase.AlignRight),
                    ('7%', [u'', u'из них направлено в круглосуточн. Стационар', u'13'], CReportBase.AlignRight),
                    ('7%', [u'', u'проведено выписанными больными дней лечения', u'14'], CReportBase.AlignRight),
                    ('7%', [u'', u'умерло', u'15'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 2, 1)  # название
            table.mergeCells(0, 1, 2, 1)  # №стр
            table.mergeCells(0, 2, 2, 1)  # код по МКБ
            table.mergeCells(0, 3, 1, 4)  # Дневной стационар при больничных учреждениях
            table.mergeCells(0, 7, 1, 4)  # Дневной стационар при амбулаторно-поликлинических учреждениях
            table.mergeCells(0, 11, 1, 4) # Дневной стационар при амбулаторно-поликлинических учреждениях

            isHospitals = [(0, 0), (4, 1), (8, 2)]
            medicalCheckupHealthy = 0
            leavedEnlistmentSum = 0
            conscript = 0
            for i, isHospital in isHospitals:
                records = self.getDataEventAdult(orgStructureIdList, begDate, endDate, u'''(age(Client.birthDate, Event.setDate)) < 18''', isHospital, groupingForMES, groupMES, MES, financeId)
                if records:
                    while records.next():
                        record = records.record()
                        MKBRec = normalizeMKB(forceString(record.value('MKB')))
                        visitLeavedDate = forceDate(record.value('visitLeavedDate'))
                        countTransfer = forceInt(record.value('countTransfer'))
                        countDeath = forceInt(record.value('countDeath'))
                        countVisit = 0
                        if durationType == 0:
                            countVisit = forceInt(record.value('countVisit'))
                        elif durationType >= 1:
                            setDate = forceDateTime(record.value('setDate'))
                            execDate = forceDateTime(record.value('execDate'))
                            countVisit = countMovingDays(setDate, execDate, QDateTime(begDate, QTime(0, 0)), QDateTime(endDate, QTime(23, 59)), 2)
                        countSurgery = forceInt(record.value('countSurgery'))
                        healthGroup = forceInt(record.value('healthGroup'))
                        relegateOrg = forceInt(record.value('relegateOrg'))
                        medicalCheckupHealthy =+ healthGroup
                        leavedEnlistmentSum += relegateOrg
                        if relegateOrg and healthGroup:
                            conscript += 1

                        for row in mapMainRows.get(MKBRec, []):
                            reportLine = reportMainData[row]
                            if visitLeavedDate and visitLeavedDate <= endDate:
                                reportLine[i] += 1
                            reportLine[i+1] += countTransfer
                            reportLine[i+2] += countVisit
                            reportLine[i+3] += countDeath
                        if countSurgery:
                            reportLine = reportMainData[len(TwoRows)-2]
                            if visitLeavedDate and visitLeavedDate <= endDate:
                                reportLine[i] += 1
                            reportLine[i+1] += countTransfer
                            reportLine[i+2] = u'X'
                            reportLine[i+3] += countDeath
                            reportLine = reportMainData[len(TwoRows)-1]
                            if visitLeavedDate  and visitLeavedDate <= endDate:
                                reportLine[i] += countSurgery
                            reportLine[i+1] = u'X'
                            reportLine[i+2] = u'X'
                            reportLine[i+3] = u'X'

            for row, rowDescr in enumerate(ThreeRows):
                reportLine = reportMainData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(u'''(2004) Из общего числа выписанных - (гр. 4, 8) – направленные райвоенкоматом %d. '''%(leavedEnlistmentSum))
            cursor.insertBlock()
            cursor.insertText(u'''(2005) Кроме того лица, госпитализированные для обследования и оказавшиеся здоровыми  %d, из них призывники %d .'''%(medicalCheckupHealthy, conscript))
            cursor.insertBlock()
        return doc


class CStationaryTwoChildrenHospitalF14DC(CReportStationary):#actTwoChildrenForma14DC
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. Раздел II. Дети 0-17 лет включительно. Дневной стационар при больничном учреждении.')
        self.stationaryF14DCSetupDialog = None


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        self.byActions = True if durationType == 2 else False
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            rowSize = 4
            mapMainRows = createMapCodeToRowIdx( [row[2] for row in ThreeRows] )
            reportMainData = [ [0]*rowSize for row in xrange(len(ThreeRows)) ]
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
#            orgStructureIdList = []
#            if orgStructureIndex.isValid():
#                treeItem = orgStructureIndex.internalPointer()
#                if treeItem._id:
#                    orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            orgStructureTypeIdList = self.getOrgStructureTypeIdList(orgStructureIdList, 0)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            titleText = u'Раздел II. Состав больных в дневном стационаре, сроки и исходы лечения\n(2003) (дети 0-17 лет включительно)'
            cursor.insertText(titleText)
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('21%',[u'', u'', u'1'], CReportBase.AlignLeft),
                    ('4%',[u'№ строки', u'', u'2'], CReportBase.AlignRight),
                    ('15%', [u'Код по МКБ-X', u'', u'3'], CReportBase.AlignLeft),
                    ('15%', [u'Дневной стационар при больничных учреждениях', u'выписано больных', u'4'], CReportBase.AlignRight),
                    ('15%', [u'', u'из них направлено в круглосуточн. Стационар', u'5'], CReportBase.AlignRight),
                    ('15%', [u'', u'проведено выписанными больными дней лечения', u'6'], CReportBase.AlignRight),
                    ('15%', [u'', u'умерло', '7'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 2, 1)  # название
            table.mergeCells(0, 1, 2, 1)  # №стр
            table.mergeCells(0, 2, 2, 1)  # код по МКБ
            table.mergeCells(0, 3, 1, 4)  # Дневной стационар при больничных учреждениях
            medicalCheckupHealthy = 0
            leavedEnlistmentSum = 0
            conscript = 0
            records = self.getDataEventAdult(orgStructureTypeIdList, begDate, endDate, u'''(age(Client.birthDate, Event.setDate)) < 18''', 0, groupingForMES, groupMES, MES, financeId)
            if records:
                while records.next():
                    record = records.record()
                    MKBRec = normalizeMKB(forceString(record.value('MKB')))
                    visitLeavedDate = forceDate(record.value('visitLeavedDate'))
                    countTransfer = forceInt(record.value('countTransfer'))
                    countDeath = forceInt(record.value('countDeath'))
                    countVisit = 0
                    if durationType == 0:
                        countVisit = forceInt(record.value('countVisit'))
                    elif durationType >= 1:
                        setDate = forceDateTime(record.value('setDate'))
                        execDate = forceDateTime(record.value('execDate'))
                        countVisit = countMovingDays(setDate, execDate, QDateTime(begDate, QTime(0, 0)), QDateTime(endDate, QTime(23, 59)), 2)
                    countSurgery = forceInt(record.value('countSurgery'))
                    healthGroup = forceInt(record.value('healthGroup'))
                    relegateOrg = forceInt(record.value('relegateOrg'))
                    medicalCheckupHealthy =+ healthGroup
                    leavedEnlistmentSum += relegateOrg
                    if relegateOrg and healthGroup:
                        conscript += 1

                    for row in mapMainRows.get(MKBRec, []):
                        reportLine = reportMainData[row]
                        if visitLeavedDate and visitLeavedDate <= endDate:
                            reportLine[0] += 1
                        reportLine[1] += countTransfer
                        reportLine[2] += countVisit
                        reportLine[3] += countDeath
                    if countSurgery:
                        reportLine = reportMainData[len(TwoRows)-2]
                        if visitLeavedDate and visitLeavedDate <= endDate:
                            reportLine[0] += 1
                        reportLine[1] += countTransfer
                        reportLine[2] = u'X'
                        reportLine[3] += countDeath
                        reportLine = reportMainData[len(TwoRows)-1]
                        if visitLeavedDate and visitLeavedDate <= endDate:
                            reportLine[0] += countSurgery
                        reportLine[1] = u'X'
                        reportLine[2] = u'X'
                        reportLine[3] = u'X'
            for row, rowDescr in enumerate(ThreeRows):
                reportLine = reportMainData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(u'''(2004) Из общего числа выписанных - (гр. 4, 8) – направленные райвоенкоматом %d. '''%(leavedEnlistmentSum))
            cursor.insertBlock()
            cursor.insertText(u'''(2005) Кроме того лица, госпитализированные для обследования и оказавшиеся здоровыми  %d, из них призывники %d .'''%(medicalCheckupHealthy, conscript))
            cursor.insertBlock()
        return doc


class CStationaryTwoChildrenPoliclinicF14DC(CReportStationary):#actTwoChildrenForma14DC
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. Раздел II. Дети 0-17 лет включительно. Дневной стационар при амбулаторно-поликлинических учреждениях.')
        self.stationaryF14DCSetupDialog = None


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        self.byActions = True if durationType == 2 else False
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            rowSize = 4
            mapMainRows = createMapCodeToRowIdx( [row[2] for row in ThreeRows] )
            reportMainData = [ [0]*rowSize for row in xrange(len(ThreeRows)) ]
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = []
            if orgStructureIndex.isValid():
                treeItem = orgStructureIndex.internalPointer()
                if treeItem._id:
                    orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            titleText = u'Раздел II. Состав больных в дневном стационаре, сроки и исходы лечения\n(2003) (дети 0-17 лет включительно)'
            cursor.insertText(titleText)
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('21%',[u'', u'', u'1'], CReportBase.AlignLeft),
                    ('4%',[u'№ строки', u'', u'2'], CReportBase.AlignRight),
                    ('15%', [u'Код по МКБ-X', u'', u'3'], CReportBase.AlignLeft),
                    ('15%', [u'Дневной стационар при амбулаторно-поликлинических учреждениях', u'выписано больных', u'4'], CReportBase.AlignRight),
                    ('15%', [u'', u'из них направлено в круглосуточн. Стационар', u'5'], CReportBase.AlignRight),
                    ('15%', [u'', u'проведено выписанными больными дней лечения', u'6'], CReportBase.AlignRight),
                    ('15%', [u'', u'умерло', u'7'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 2, 1)  # название
            table.mergeCells(0, 1, 2, 1)  # №стр
            table.mergeCells(0, 2, 2, 1)  # код по МКБ
            table.mergeCells(0, 3, 1, 4)  # Дневной стационар при амбулаторно-поликлинических учреждениях
            medicalCheckupHealthy = 0
            leavedEnlistmentSum = 0
            conscript = 0
            records = self.getDataEventAdult(orgStructureIdList, begDate, endDate, u'''(age(Client.birthDate, Event.setDate)) < 18''', 1, groupingForMES, groupMES, MES, financeId)
            if records:
                while records.next():
                    record = records.record()
                    MKBRec = normalizeMKB(forceString(record.value('MKB')))
                    visitLeavedDate = forceDate(record.value('visitLeavedDate'))
                    countTransfer = forceInt(record.value('countTransfer'))
                    countDeath = forceInt(record.value('countDeath'))
                    countVisit = 0
                    if durationType == 0:
                        countVisit = forceInt(record.value('countVisit'))
                    elif durationType == 1:
                        setDate = forceDate(record.value('setDate'))
                        execDate = forceDate(record.value('execDate'))
                        countVisit = setDate.daysTo(execDate)+1
                    elif durationType == 2:
                        countVisit = forceInt(record.value('countActions'))
                    countSurgery = forceInt(record.value('countSurgery'))
                    healthGroup = forceInt(record.value('healthGroup'))
                    relegateOrg = forceInt(record.value('relegateOrg'))
                    medicalCheckupHealthy =+ healthGroup
                    leavedEnlistmentSum += relegateOrg
                    if relegateOrg and healthGroup:
                        conscript += 1

                    for row in mapMainRows.get(MKBRec, []):
                        reportLine = reportMainData[row]
                        if visitLeavedDate:
                            reportLine[0] += 1
                        reportLine[1] += countTransfer
                        reportLine[2] += countVisit
                        reportLine[3] += countDeath
                    if countSurgery:
                        reportLine = reportMainData[len(TwoRows)-2]
                        if visitLeavedDate:
                            reportLine[0] += 1
                        reportLine[1] += countTransfer
                        reportLine[2] = u'X'
                        reportLine[3] += countDeath
                        reportLine = reportMainData[len(TwoRows)-1]
                        if visitLeavedDate:
                            reportLine[0] += countSurgery
                        reportLine[1] = u'X'
                        reportLine[2] = u'X'
                        reportLine[3] = u'X'
            for row, rowDescr in enumerate(ThreeRows):
                reportLine = reportMainData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(u'''(2004) Из общего числа выписанных - (гр. 4, 8) – направленные райвоенкоматом %d. '''%(leavedEnlistmentSum))
            cursor.insertBlock()
            cursor.insertText(u'''(2005) Кроме того лица, госпитализированные для обследования и оказавшиеся здоровыми  %d, из них призывники %d .'''%(medicalCheckupHealthy, conscript))
            cursor.insertBlock()
        return doc


class CStationaryTwoChildrenHouseF14DC(CReportStationary):#actTwoChildrenForma14DC
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. Раздел II. Дети 0-17 лет включительно. Стационар на дому.')
        self.stationaryF14DCSetupDialog = None


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId = params.get('financeId', None)
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        self.byActions = True if durationType == 2 else False
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            rowSize = 4
            mapMainRows = createMapCodeToRowIdx( [row[2] for row in ThreeRows] )
            reportMainData = [ [0]*rowSize for row in xrange(len(ThreeRows)) ]
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = []
            if orgStructureIndex.isValid():
                treeItem = orgStructureIndex.internalPointer()
                if treeItem._id:
                    orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            titleText = u'Раздел II. Состав больных в дневном стационаре, сроки и исходы лечения\n(2003) (дети 0-17 лет включительно)'
            cursor.insertText(titleText)
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('21%',[u'', u'', u'1'], CReportBase.AlignLeft),
                    ('4%',[u'№ строки', u'', u'2'], CReportBase.AlignRight),
                    ('15%', [u'Код по МКБ-X', u'', u'3'], CReportBase.AlignLeft),
                    ('15%', [u'Стационар на дому', u'выписано больных', u'4'], CReportBase.AlignRight),
                    ('15%', [u'', u'из них направлено в круглосуточн. Стационар', u'5'], CReportBase.AlignRight),
                    ('15%', [u'', u'проведено выписанными больными дней лечения', u'6'], CReportBase.AlignRight),
                    ('15%', [u'', u'умерло', u'7'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 2, 1)  # название
            table.mergeCells(0, 1, 2, 1)  # №стр
            table.mergeCells(0, 2, 2, 1)  # код по МКБ
            table.mergeCells(0, 3, 1, 4)  # Стационар на дому
            medicalCheckupHealthy = 0
            leavedEnlistmentSum = 0
            conscript = 0
            records = self.getDataEventAdult(orgStructureIdList, begDate, endDate, u'''(age(Client.birthDate, Event.setDate)) < 18''', 2, groupingForMES, groupMES, MES, financeId)
            if records:
                while records.next():
                    record = records.record()
                    MKBRec = normalizeMKB(forceString(record.value('MKB')))
                    visitLeavedDate = forceDate(record.value('visitLeavedDate'))
                    countTransfer = forceInt(record.value('countTransfer'))
                    countDeath = forceInt(record.value('countDeath'))
                    countVisit = 0
                    if durationType == 0:
                        countVisit = forceInt(record.value('countVisit'))
                    elif durationType == 1:
                        setDate = forceDate(record.value('setDate'))
                        execDate = forceDate(record.value('execDate'))
                        countVisit = setDate.daysTo(execDate)+1
                    elif durationType == 2:
                        countVisit = forceInt(record.value('countActions'))
                    countSurgery = forceInt(record.value('countSurgery'))
                    healthGroup = forceInt(record.value('healthGroup'))
                    relegateOrg = forceInt(record.value('relegateOrg'))
                    medicalCheckupHealthy =+ healthGroup
                    leavedEnlistmentSum += relegateOrg
                    if relegateOrg and healthGroup:
                        conscript += 1

                    for row in mapMainRows.get(MKBRec, []):
                        reportLine = reportMainData[row]
                        if visitLeavedDate:
                            reportLine[0] += 1
                        reportLine[1] += countTransfer
                        reportLine[2] += countVisit
                        reportLine[3] += countDeath
                    if countSurgery:
                        reportLine = reportMainData[len(TwoRows)-2]
                        if visitLeavedDate:
                            reportLine[0] += 1
                        reportLine[1] += countTransfer
                        reportLine[2] = u'X'
                        reportLine[3] += countDeath
                        reportLine = reportMainData[len(TwoRows)-1]
                        if visitLeavedDate:
                            reportLine[0] += countSurgery
                        reportLine[1] = u'X'
                        reportLine[2] = u'X'
                        reportLine[3] = u'X'
            for row, rowDescr in enumerate(TwoRows):
                reportLine = reportMainData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(u'''(2004) Из общего числа выписанных - (гр. 4, 8) – направленные райвоенкоматом %d. '''%(leavedEnlistmentSum))
            cursor.insertBlock()
            cursor.insertText(u'''(2005) Кроме того лица, госпитализированные для обследования и оказавшиеся здоровыми  %d, из них призывники %d .'''%(medicalCheckupHealthy, conscript))
            cursor.insertBlock()
        return doc


class CStationaryTypePaymentF14DC(CReportStationary): #actTypePaymentF14DC
    def __init__(self, parent = None):
        CReportStationary.__init__(self, parent)
        self.setTitle(u'Форма 14ДС. ВИДЫ ОПЛАТЫ')
        self.stationaryF14DCSetupDialog = None


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        groupingForMES = params.get('groupingForMES', False)
        durationType = params.get('durationType', 0)
        self.byActions = True if durationType == 2 else False
        if groupingForMES:
            groupMES = params.get('groupMES', None)
            MES = params.get('MES', None)
        else:
            groupMES = None
            MES = None
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            rowSize = 6
            orgStructureIndex = self.stationaryF14DCSetupDialog.cmbOrgStructure._model.index(self.stationaryF14DCSetupDialog.cmbOrgStructure.currentIndex(), 0, self.stationaryF14DCSetupDialog.cmbOrgStructure.rootModelIndex())
            orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex)
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            titleText = u'Раздел II. ВИДЫ ОПЛАТЫ\n(4000)'
            cursor.insertText(titleText)
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('15%', [u'Вид оплаты', u'', u'1'], CReportBase.AlignLeft),
                    ('5%', [u'№ строки', u'', u'2'], CReportBase.AlignLeft),
                    ('10%',[u'Число выбывших больных из дневного стационара(выписано + умерло)', u'больничных учреждений', u'3'], CReportBase.AlignRight),
                    ('10%',[u'', u'амбулаторно-поликлинических учреждений', u'4'], CReportBase.AlignRight),
                    ('15%', [u'', u'на дому', u'5'], CReportBase.AlignRight),
                    ('15%', [u'Число дней лечения, проведенное выбывшими из дневного стационара (выписано + умерло)', u'больничных учреждений', u'6'], CReportBase.AlignRight),
                    ('15%', [u'', u'амбулаторно-поликлинических учреждений', u'7'], CReportBase.AlignRight),
                    ('15%', [u'', u'на дому ', u'8'], CReportBase.AlignRight)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 2, 1)  # название
            table.mergeCells(0, 1, 2, 1)  # №стр
            table.mergeCells(0, 2, 1, 3)  # код по МКБ
            table.mergeCells(0, 5, 1, 3)  # Стационар на дому

            isHospitals = [(0, 0), (1, 1), (2, 2)]
            financeIdList = {}
            cnt = 0
            for i, isHospital in isHospitals:
                records = self.getDataEventTypePayment(orgStructureIdList, begDate, endDate, u'''(age(Client.birthDate, Event.setDate)) < 18''', isHospital, groupingForMES, groupMES, MES, durationType)[0]
                if records:
                    while records.next():
                        record = records.record()
                        visitLeavedDate = forceDate(record.value('visitLeavedDate'))
                        countVisit = forceInt(record.value('countActions'))
                        visitFinanceId = forceRef(record.value('visitFinanceId'))
                        contractFinanceId = forceRef(record.value('contractFinanceId'))
                        visitFinanceName = forceString(record.value('visitFinanceName'))
                        contractFinanceName = forceString(record.value('contractFinanceName'))
                        financeId = visitFinanceId
                        financeName = visitFinanceName
                        if durationType >= 1:
                            financeId = contractFinanceId
                            financeName = contractFinanceName
                        reportLine = financeIdList.get((financeId, financeName), [0]*rowSize)
                        if visitLeavedDate and visitLeavedDate <= endDate:
                            reportLine[i] += 1
                            if durationType >= 1:
                                setDate = forceDateTime(record.value('visitReceivedDate'))
                                execDate = forceDateTime(record.value('visitLeavedDate'))
                                countVisit = countMovingDays(setDate, execDate, QDateTime(begDate, QTime(0, 0)), QDateTime(endDate, QTime(23, 59)), 2)
                            reportLine[i+3] += countVisit
                            financeIdList[(financeId, financeName)] = reportLine
            for financeKey, reportLine in financeIdList.items():
                i = table.addRow()
                cnt += 1
                financeId, financeName = financeKey
                table.setText(i, 0, financeName)
                table.setText(i, 1, cnt)
                for col in xrange(rowSize):
                    table.setText(i, 2+col, reportLine[col])
        return doc

    def getDataEventTypePayment(self, orgStructureIdList, begDate, endDate, ageChildren, isHospital, groupingForMES, groupMES, MES, durationType):
        if self.byActions:
            if isHospital == 0:
                return self.getDataEventHospitalByActions(orgStructureIdList, begDate, endDate, [], isHospital, groupingForMES, groupMES, MES, True)
            else:
                return None, None
        else:
            return self.getDataEventTypePaymentByVisits(orgStructureIdList, begDate, endDate, ageChildren, isHospital, groupingForMES, groupMES, MES, durationType)


    def getDataEventTypePaymentByVisits(self, orgStructureIdList, begDate, endDate, ageChildren, isHospital, groupingForMES, groupMES, MES, durationType):
        orgStructureTypeIdList = self.getOrgStructureTypeIdList(orgStructureIdList, isHospital)
        if orgStructureTypeIdList:
            db = QtGui.qApp.db
            tableVisit = db.table('Visit')
            tableEvent = db.table('Event')
            tableClient = db.table('Client')
            tableEventType = db.table('EventType')
            tableRBScene = db.table('rbScene')
            tablePerson = db.table('Person')
            tableOS = db.table('OrgStructure')
            tableMES = db.table('mes.MES')
            tableGroupMES = db.table('mes.mrbMESGroup')
            tableRBMedicalAidType = db.table('rbMedicalAidType')

            cond = [ tableEvent['deleted'].eq(0),
                     tablePerson['deleted'].eq(0),
                     tableEventType['deleted'].eq(0),
                     tableVisit['deleted'].eq(0),
                     tableClient['deleted'].eq(0),
                     tableEvent['execDate'].isNotNull()
                   ]
            queryTable = tableEvent.innerJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tableOS, tablePerson['orgStructure_id'].eq(tableOS['id']))
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            queryTable = queryTable.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
            if groupingForMES:
                cond.append(tableEvent['MES_id'].isNotNull())
                if groupMES or MES:
                    queryTable = queryTable.innerJoin(tableMES, tableEvent['MES_id'].eq(tableMES['id']))
                    cond.append(tableMES['deleted'].eq(0))
                    if MES:
                        cond.append(tableEvent['MES_id'].eq(MES))
                    if groupMES:
                        queryTable = queryTable.innerJoin(tableGroupMES, tableMES['group_id'].eq(tableGroupMES['id']))
                        cond.append(tableGroupMES['deleted'].eq(0))
                        cond.append(tableMES['group_id'].eq(groupMES))
            socStatusClassId = self.params.get('socStatusClassId', None)
            socStatusTypeId  = self.params.get('socStatusTypeId', None)
            if socStatusClassId or socStatusTypeId:
                tableClientSocStatus = db.table('ClientSocStatus')
                if begDate:
                    cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                                       tableClientSocStatus['endDate'].ge(begDate)
                                                      ]),
                                           tableClientSocStatus['endDate'].isNull()
                                          ]))
                if endDate:
                    cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                                       tableClientSocStatus['begDate'].lt(endDate.addDays(1))
                                                      ]),
                                           tableClientSocStatus['begDate'].isNull()
                                          ]))
                queryTable = queryTable.leftJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
                if socStatusClassId:
                    cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
                if socStatusTypeId:
                    cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
                cond.append(tableClientSocStatus['deleted'].eq(0))
            joinOr2 = db.joinAnd([tableEvent['setDate'].isNotNull(), tableEvent['setDate'].ge(begDate), tableEvent['setDate'].lt(endDate)])
            joinOr3 = db.joinAnd([tableEvent['setDate'].lt(endDate), tableEvent['execDate'].isNotNull(), tableEvent['execDate'].gt(begDate)])
            joinOr4 = db.joinAnd([tableEvent['setDate'].isNotNull(), tableEvent['setDate'].le(begDate), tableEvent['execDate'].gt(begDate)])
            cond.append(db.joinOr([joinOr2, joinOr3, joinOr4]))
            cond.append(tableRBMedicalAidType['code'].eq(7))
            cond.append(tableOS['deleted'].eq(0))
            cond.append(tablePerson['orgStructure_id'].inlist(orgStructureTypeIdList))
            if isHospital == 2:
                queryTable = queryTable.innerJoin(tableRBScene, tableRBScene['id'].eq(tableVisit['scene_id']))
                cond.append(tableRBScene['code'].eq(2))
            #cond.append(ageChildren)
            eventIdList = db.getDistinctIdList(queryTable, 'Event.id', cond, 'Event.id, Visit.date ASC')
            if eventIdList:
                stmtVisit = u'''SELECT %s

    (SELECT MAX(V.date) FROM Visit AS V WHERE V.event_id = Event.id AND V.deleted = 0 AND Event.execDate IS NOT NULL) AS visitLeavedDate,
    EXISTS(SELECT rbResult.name FROM rbResult WHERE rbResult.id = Event.result_id
    AND (rbResult.code = 99 OR rbResult.name LIKE '%%умер%%' OR rbResult.name LIKE '%%смерть%%')) AS countDeath,
    Event.setDate, Event.execDate, Event.id AS eventId

    FROM Event
    INNER JOIN Visit ON Visit.event_id=Event.id
    INNER JOIN Client ON Event.client_id=Client.id
    LEFT JOIN  Contract ON Contract.id = Event.contract_id
    INNER JOIN Diagnostic ON Diagnostic.event_id = Event.id
    INNER JOIN Diagnosis ON Diagnosis.id = Diagnostic.diagnosis_id
    INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = Diagnostic.diagnosisType_id

    WHERE (Event.deleted=0) AND (Client.deleted = 0) AND (Visit.deleted=0) AND Event.id IN (%s) AND (rbDiagnosisType.code = '1'
    OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
    AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id
    WHERE DT.code = '1' AND DC.event_id = Event.id LIMIT 1))))

    GROUP BY %s
    ORDER BY Event.id, Visit.date ASC'''%(u'''COUNT(Visit.id) AS countActions,
    Visit.finance_id AS visitFinanceId, Contract.finance_id AS contractFinanceId,
    IF(Visit.finance_id, (SELECT rbFinance.name FROM rbFinance WHERE rbFinance.id = Visit.finance_id), '') AS visitFinanceName,
    IF(Contract.finance_id, (SELECT rbFinance.name FROM rbFinance WHERE rbFinance.id = Contract.finance_id), '') AS contractFinanceName,'''
    if durationType == 0 else (u''' Contract.finance_id AS contractFinanceId,
    IF(Contract.finance_id, (SELECT rbFinance.name FROM rbFinance WHERE rbFinance.id = Contract.finance_id), '') AS contractFinanceName,'''
    if durationType == 1  else u''),
    u','.join(str(eventId) for eventId in eventIdList if eventId),
    u'''Visit.finance_id, Event.id''' if durationType == 0 else u'''Event.id''' )
                return (db.query(stmtVisit), None)
        return (None, None)

