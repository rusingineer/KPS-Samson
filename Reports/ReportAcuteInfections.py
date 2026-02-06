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
from PyQt4.QtCore import pyqtSignature, QDate

from library.Utils      import forceInt, forceString
from library.database   import addDateInRange
from library.DialogBase import CDialogBase
from Events.EventTypeListEditorDialog import CEventTypeListEditorDialog
from Events.Utils       import getWorkEventTypeFilter
from Orgs.Utils         import getOrgStructureDescendants
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat
from Reports.SelectOrgStructureListDialog import CSelectOrgStructureListDialog


def getFilterAddress(params):
    condAddress = []
    db = QtGui.qApp.db
    tableClient = db.table('Client')
    tableClientAddress = db.table('ClientAddress').alias('CA')
    tableAddress = db.table('Address').alias('A')
    tableAddressHouse = db.table('AddressHouse').alias('AH')

    filterAddressType = params.get('filterAddressType', 0)
    filterAddressCity = params.get('filterAddressCity', None)
    filterAddressStreet = params.get('filterAddressStreet', None)
    filterAddressHouse = params.get('filterAddressHouse', u'')
    filterAddressCorpus = params.get('filterAddressCorpus', u'')
    filterAddressFlat = params.get('filterAddressFlat', u'')
    filterAddressOkato = params.get('filterAddressOkato')
    filterAddressStreetList = params.get('filterAddressStreetList')

    tableQuery = tableClientAddress.innerJoin(tableAddress, tableAddress['id'].eq(tableClientAddress['address_id']))
    tableQuery = tableQuery.innerJoin(tableAddressHouse, tableAddressHouse['id'].eq(tableAddress['house_id']))

    condAddress.append(tableClientAddress['client_id'].eq(tableClient['id']))
    condAddress.append(tableClientAddress['type'].eq(filterAddressType))
    condAddress.append(db.joinOr([tableClientAddress['id'].isNull(), tableClientAddress['deleted'].eq(0)]))
    if filterAddressCity or filterAddressStreet or filterAddressHouse or filterAddressCorpus or filterAddressFlat:
        condAddress.append(db.joinOr([tableAddress['id'].isNull(), tableAddress['deleted'].eq(0)]))
        condAddress.append(db.joinOr([tableAddressHouse['id'].isNull(), tableAddressHouse['deleted'].eq(0)]))
    if filterAddressCity:
        condAddress.append(tableAddressHouse['KLADRCode'].like('%s%%00'%filterAddressCity.rstrip('0')))
    if filterAddressStreet:
        condAddress.append(tableAddressHouse['KLADRStreetCode'].like(filterAddressStreet))
    if filterAddressHouse:
        condAddress.append(tableAddressHouse['number'].eq(filterAddressHouse))
    if filterAddressCorpus:
        condAddress.append(tableAddressHouse['corpus'].eq(filterAddressCorpus))
    if filterAddressFlat:
        condAddress.append(tableAddress['flat'].eq(filterAddressFlat))
    if filterAddressOkato:
        condAddress.append(tableAddressHouse['KLADRStreetCode'].inlist(filterAddressStreetList))
    return db.selectStmt(tableQuery, 'MAX(CA.id)', condAddress)


def addAttachCond(cond, orgCond, attachCategory, attachTypeId, attachBegDate=QDate(), attachEndDate=QDate()):
    db = QtGui.qApp.db
    outerCond = ['ClientAttach.client_id = Client.id']
    innerCond = ['CA2.client_id = Client.id']
    if attachBegDate and attachEndDate:
        outerCond.append(db.joinOr([db.joinAnd(['DATE(ClientAttach.begDate) IS NULL',
                                                'DATE(ClientAttach.endDate) IS NULL'
                                                ]),
                                    db.joinAnd(['DATE(ClientAttach.begDate) IS NOT NULL',
                                                'DATE(ClientAttach.begDate) < DATE(%s)'%(db.formatDate(attachEndDate))
                                                ]),
                                    db.joinAnd(['DATE(ClientAttach.endDate) IS NOT NULL',
                                                'DATE(ClientAttach.endDate) >= DATE(%s)'%(db.formatDate(attachBegDate))
                                                ])
                                    ])
                        )
    elif attachBegDate:
        outerCond.append(db.joinOr([db.joinAnd(['DATE(ClientAttach.begDate) IS NULL',
                                                'DATE(ClientAttach.endDate) IS NULL'
                                                ]),
                                    db.joinAnd(['DATE(ClientAttach.endDate) IS NOT NULL',
                                                'DATE(ClientAttach.endDate) >= DATE(%s)'%(db.formatDate(attachBegDate))
                                                ])
                                    ])
                        )
    elif attachEndDate:
        outerCond.append(db.joinOr([db.joinAnd(['DATE(ClientAttach.begDate) IS NULL',
                                                'DATE(ClientAttach.endDate) IS NULL'
                                                ]),
                                    db.joinAnd(['DATE(ClientAttach.begDate) IS NOT NULL',
                                                'DATE(ClientAttach.begDate) < DATE(%s)'%(db.formatDate(attachEndDate))
                                                ])
                                    ])
                        )
        outerCond.append('DATE(ClientAttach.begDate) >= DATE(%s)'%(db.formatDate(attachBegDate)))
        outerCond.append('DATE(ClientAttach.begDate) < DATE(%s)'%(db.formatDate(attachEndDate)))
    if attachEndDate:
        outerCond.append('DATE(ClientAttach.begDate) <= DATE(%s)'%(db.formatDate(attachEndDate)))
        outerCond.append('DATE(ClientAttach.endDate) > DATE(%s)'%(db.formatDate(attachBegDate)))
    if orgCond:
        outerCond.append(orgCond)
    if attachTypeId:
        outerCond.append('attachType_id=%d' % attachTypeId)
        innerCond.append('CA2.attachType_id=%d' % attachTypeId)
    else:
        if attachCategory == 1:
            innerCond.append('rbAttachType2.temporary=0')
        elif attachCategory == 2:
            innerCond.append('rbAttachType2.temporary')
        elif attachCategory == 3:
            innerCond.append('rbAttachType2.outcome')
        elif attachCategory == 0:
            outerCond.append('rbAttachType.outcome=0')
            innerCond.append('rbAttachType2.temporary=0')
    stmt = '''EXISTS (SELECT ClientAttach.id
       FROM ClientAttach
       LEFT JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
       WHERE ClientAttach.deleted=0
       AND %s
       AND ClientAttach.id in (SELECT MAX(CA2.id)
                   FROM ClientAttach AS CA2
                   LEFT JOIN rbAttachType AS rbAttachType2 ON rbAttachType2.id = CA2.attachType_id
                   WHERE CA2.deleted=0 AND %s))'''
    cond.append(stmt % (QtGui.qApp.db.joinAnd(outerCond), QtGui.qApp.db.joinAnd(innerCond)))
    return cond


def selectData(useInputDate, begInputDate, endInputDate, registeredInPeriod, begDate, endDate, eventPurposeId, eventTypeId, orgStructureId, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, MKBList, accountAccomp, locality, params):
#    stmt="""
#SELECT
#   MKB,
#   ageGroup,
#   sex,
#   COUNT(*) AS cnt
#   FROM (
#SELECT
#    Diagnosis.MKB AS MKB,
#    IF( ADDDATE(Client.birthDate, INTERVAL 18 YEAR)<=Diagnosis.setDate,
#        2,
#        IF ( ADDDATE(Client.birthDate, INTERVAL 15 YEAR)>Diagnosis.setDate,
#          0,
#          1)
#      ) AS ageGroup,
#    Client.sex AS sex
#FROM Diagnosis
#LEFT JOIN Client ON Client.id = Diagnosis.client_id
#LEFT JOIN rbDiagnosisType ON rbDiagnosisType.id = Diagnosis.diagnosisType_id%s
#WHERE %s
#) AS T
#GROUP BY MKB, ageGroup, sex
#ORDER BY MKB
#    """
    stmt="""
SELECT
   MKB,
   ageGroup,
   sex,
   COUNT(*) AS cnt
   FROM (
SELECT
    Diagnosis.MKB AS MKB,
    IF( ADDDATE(Client.birthDate, INTERVAL 18 YEAR)<=Diagnosis.setDate,
        2,
        IF ( ADDDATE(Client.birthDate, INTERVAL 15 YEAR)>Diagnosis.setDate,
          0,
          1)
      ) AS ageGroup,
    Client.sex AS sex
FROM %s
WHERE %s
) AS T
GROUP BY MKB, ageGroup, sex
ORDER BY MKB
    """
    db = QtGui.qApp.db
    tableDiagnosis  = db.table('Diagnosis')
    tableDiagnosisType = db.table('rbDiagnosisType')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tablePerson = db.table('Person')
    tableClientAddress = db.table('ClientAddress')
    tableAddress = db.table('Address')
    tableAddressHouse = db.table('AddressHouse')
    queryTable = tableDiagnosis.leftJoin(tableClient, tableDiagnosis['client_id'].eq(tableClient['id']))
    queryTable = queryTable.leftJoin(tableDiagnosisType, tableDiagnosis['diagnosisType_id'].eq(tableDiagnosisType['id']))
    cond = []
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableDiagnosis['mod_id'].isNull())
    addDateInRange(cond, tableDiagnosis['setDate'], begDate, endDate)
#    cond.append(db.joinOr([tableDiagnosis['setDate'].isNull(), tableDiagnosis['setDate'].le(endDate)]))
#    cond.append(tableDiagnosis['endDate'].ge(begDate))

    diagnosticQuery = tableDiagnostic
    diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                       tableDiagnostic['deleted'].eq(0)
                     ]
    if registeredInPeriod:
        addDateInRange(diagnosticCond, tableDiagnostic['setDate'], begDate, endDate)
    if useInputDate:
        tableEvent  = db.table('Event')
        queryTable = queryTable.innerJoin(tableEvent, tableEvent['client_id'].eq(tableClient['id']))
        cond.append(tableEvent['deleted'].eq(0))
        addDateInRange(cond, tableEvent['createDatetime'], begInputDate, endInputDate)
    isPersonPost = params.get('isPersonPost', 0)
    if isPersonPost:
        tableRBPost = db.table('rbPost')
        diagnosticQuery = diagnosticQuery.innerJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticQuery = diagnosticQuery.innerJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
        diagnosticCond.append(tablePerson['deleted'].eq(0))
        if isPersonPost == 1:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('1','2','3') ''')
        elif isPersonPost == 2:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('4','5','6','7','8','9')''')
    if personId:
        diagnosticCond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureId:
        if not isPersonPost:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        if not isPersonPost:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if eventTypeId:
        tableEvent = db.table('Event')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticCond.append(tableEvent['eventType_id'].eq(eventTypeId))
    elif eventPurposeId:
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticQuery = diagnosticQuery.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        diagnosticCond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    cond.append(db.existsStmt(diagnosticQuery, diagnosticCond))

    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        cond.append('Diagnosis.endDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
        cond.append('Diagnosis.endDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
    if socStatusTypeId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusType_id=%d' % socStatusTypeId)
        cond.append('EXISTS('+subStmt+')')
    elif socStatusClassId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusClass_id=%d' % socStatusClassId)
        cond.append('EXISTS('+subStmt+')')
    MKBCond = []
    for MKB in MKBList:
        MKBCond.append( tableDiagnosis['MKB'].like(MKB+'%') )
    cond.append(db.joinOr(MKBCond))
    if not accountAccomp:
        cond.append(tableDiagnosisType['code'].inlist(['1', '2', '4']))

    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))

    filterAddress = params.get('isFilterAddress', False)
    if filterAddress:
        filterAddressType = params.get('filterAddressType', 0)
        filterAddressCity = params.get('filterAddressCity', None)
        filterAddressStreet = params.get('filterAddressStreet', None)
        filterAddressHouse = params.get('filterAddressHouse', u'')
        filterAddressCorpus = params.get('filterAddressCorpus', u'')
        filterAddressFlat = params.get('filterAddressFlat', u'')
        queryTable = queryTable.leftJoin(tableClientAddress, tableClient['id'].eq(tableClientAddress['client_id']))
        cond.append(tableClientAddress['type'].eq(filterAddressType))
        cond.append(db.joinOr([tableClientAddress['id'].isNull(), tableClientAddress['deleted'].eq(0)]))
        if filterAddressCity or filterAddressStreet or filterAddressHouse or filterAddressCorpus or filterAddressFlat:
            queryTable = queryTable.leftJoin(tableAddress, tableClientAddress['address_id'].eq(tableAddress['id']))
            queryTable = queryTable.leftJoin(tableAddressHouse, tableAddress['house_id'].eq(tableAddressHouse['id']))
            cond.append(db.joinOr([tableAddress['id'].isNull(), tableAddress['deleted'].eq(0)]))
            cond.append(db.joinOr([tableAddressHouse['id'].isNull(), tableAddressHouse['deleted'].eq(0)]))
        if filterAddressCity:
            cond.append(tableAddressHouse['KLADRCode'].like(filterAddressCity))
        if filterAddressStreet:
            cond.append(tableAddressHouse['KLADRStreetCode'].like(filterAddressStreet))
        if filterAddressHouse:
            cond.append(tableAddressHouse['number'].eq(filterAddressHouse))
        if filterAddressCorpus:
            cond.append(tableAddressHouse['corpus'].eq(filterAddressCorpus))
        if filterAddressFlat:
            cond.append(tableAddress['flat'].eq(filterAddressFlat))

    return db.query(stmt % (db.getTableName(queryTable), db.joinAnd(cond)))


class CReportAcuteInfections(CReport):
    rowTypes = [ (u'J10', u'Грипп, вызванный идентифицированным вирусом гриппа' ),
                 (u'J11', u'Грипп, вирус не идентифицирован' ),
                 (u'J03', u'Ангина'),
                 (u'J06', u'ОРВИ'  ),
                 (u'J18', u'Пневмония'),
                 (u'J20', u'Бронхит'),
                 (u'O99.5', u'Болезни органов дыхания, осложняющие беременность, деторождение и послеродовой период'),
               ]

    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Сводка по выявленным острым инфекционным заболеваниям')
        self.setOrientation(QtGui.QPrinter.Landscape)
        self.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape, leftMargin=1,
                                      topMargin=1, rightMargin=1, bottomMargin=1)


    def getSetupDialog(self, parent):
        result = CReportAcuteInfectionsSetupDialog(parent)
        result.setAccountAccompEnabled(True)
        result.setTitle(self.title())
        return result


    def build(self, params):
        registeredInPeriod = params.get('registeredInPeriod', False)
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        useInputDate = bool(params.get('useInputDate', False))
        begInputDate = params.get('begInputDate', QDate())
        endInputDate = params.get('endInputDate', QDate())
        eventPurposeId = params.get('eventPurposeId', None)
        eventTypeId = params.get('eventTypeId', None)
        orgStructureId = params.get('orgStructureId', None)
        personId = params.get('personId', None)
        sex = params.get('sex', 0)
        ageFrom = params.get('ageFrom', 0)
        ageTo = params.get('ageTo', 150)
        socStatusClassId = params.get('socStatusClassId', None)
        socStatusTypeId = params.get('socStatusTypeId', None)
        accountAccomp = params.get('accountAccomp', False)
        locality = params.get('locality', False)

        reportRowSize = 9

        mapMKBToTypeIndex = {}
        for index, rowType in enumerate(self.rowTypes):
            mapMKBToTypeIndex[rowType[0]] = index

        reportData = {}
        MKBList = []
        query = selectData(useInputDate, begInputDate, endInputDate, registeredInPeriod, begDate, endDate, eventPurposeId, eventTypeId, orgStructureId, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, [t[0] for t in self.rowTypes], accountAccomp, locality, params)

        while query.next():
            record    = query.record()
            cnt       = forceInt(record.value('cnt'))
            MKB       = forceString(record.value('MKB'))
            sex       = forceInt(record.value('sex'))
            ageGroup  = forceInt(record.value('ageGroup'))

            reportRow = reportData.get(MKB, None)
            if not reportRow:
                reportRow = [0]*reportRowSize
                reportData[MKB] = reportRow
                MKBList.append(MKB)

            if sex in (1, 2):
                reportRow[ageGroup*2+sex-1] += cnt
                reportRow[5+sex] += cnt
                reportRow[8] += cnt

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        if params.get('isFilterAddress', False):
            self.dumpParamsAdress(cursor, params)
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('15%', [u'Диагноз',             u''], CReportBase.AlignLeft),
            ('9%', [u'Дети (0-14 лет)',                u'М'], CReportBase.AlignRight),
            ('9%', [u'',                    u'Ж'], CReportBase.AlignRight),
            ('9%', [u'Подростки (15-17 лет)',           u'М'], CReportBase.AlignRight),
            ('9%', [u'',                    u'Ж'], CReportBase.AlignRight),
            ('9%', [u'Взрослые (18 лет и старше)',            u'М'], CReportBase.AlignRight),
            ('9%', [u'',                    u'Ж'], CReportBase.AlignRight),
            ('10%', [u'Всего',               u'М'], CReportBase.AlignRight),
            ('10%', [u'',                    u'Ж'], CReportBase.AlignRight),
            ('11%', [u'Всего',               u''],  CReportBase.AlignRight),
            ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 1, 2)
        table.mergeCells(0, 3, 1, 2)
        table.mergeCells(0, 5, 1, 2)
        table.mergeCells(0, 7, 1, 2)
        table.mergeCells(0, 9, 2, 1)

        prevTypeIndex = None
        total = [0]*reportRowSize
        for MKB in MKBList:
            typeIndex = mapMKBToTypeIndex[MKB[:3] if MKB != u'O99.5' else MKB]
            if typeIndex != prevTypeIndex:
                if prevTypeIndex is not None:
                    self.produceTotalLine(table, u'Всего', total)
                i = table.addRow()
                table.mergeCells(i, 0, 1, reportRowSize+1)
                table.setText(i, 0, self.rowTypes[typeIndex][1])
                prevTypeIndex = typeIndex
                total = [0]*reportRowSize
            row = reportData[MKB]
            i = table.addRow()
            table.setText(i, 0, MKB)
            for j in xrange(reportRowSize):
                table.setText(i, j+1, row[j])
                total[j] += row[j]
        if prevTypeIndex is not None:
            self.produceTotalLine(table, u'Всего', total)
        return doc


    def produceTotalLine(self, table, title, total):
        i = table.addRow()
        table.setText(i, 0, title, CReportBase.TableTotal)
        for j in xrange(len(total)):
            table.setText(i, j+1, total[j], CReportBase.TableTotal)


from Ui_ReportAcuteInfectionsSetup import Ui_ReportAcuteInfectionsSetupDialog


class CReportAcuteInfectionsSetupDialog(CDialogBase, Ui_ReportAcuteInfectionsSetupDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.patientRequired = False
        self.setupUi(self)
        self.cmbEventPurpose.setTable('rbEventTypePurpose', True, filter='code != \'0\'')
        self.cmbEventTypeDD.setTable('EventType', True, filter ='form = 131', order='EventType.id DESC')
        self.cmbEventType.setTable('EventType', True, filter=getWorkEventTypeFilter(isApplyActive=True))
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbFinance.setTable('rbFinance', addNone=True)
        self.cmbSocStatusType.setTable('vrbSocStatusType', True)
        self.cmbFilterAttachType.setTable('rbAttachType', True)
        self.cmbSpeciality.setTable('rbSpeciality', True)
        self.cmbPhase.setTable('rbDiseasePhases', True)
        self.cmbPhaseEx.setTable('rbDiseasePhases', True)
        self.setAreaEnabled(False)
        self.setFilterAddressOrgStructureVisible(False)
        self.setMKBFilterEnabled(False)
        self.setAccountAccompEnabled(False)
        self.setOnlyFirstTimeEnabled(False)
        self.setNotNullTraumaTypeEnabled(False)
        self.setEventTypeDDEnabled(False)
        self.setPersonPostEnabled(True)
        self.setFinanceVisible(False)

        self.cmbArea.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbArea.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbFilterAddressCity.setCode(QtGui.qApp.defaultKLADR())
        self.eventTypeList = []
        self.orgStructureList = []

        self._isAllAddressSelectable = False
        self.setAllAttachSelectable()
        self.setEventTypeListListVisible(False)
        self.setOrgStructureListVisible(False)
        self.setCMBEventTypeVisible(True)
        self.setCMBOrgStructureVisible(True)
        self.setSpecialityVisible(False)
        self.setChkFilterDispanser(False)


    def setChkFilterDispanser(self, value):
        self.isDispanserVisible = value
        self.chkFilterDispanser.setVisible(value)


    def setCMBEventTypeVisible(self, value):
        self.isEventTypeVisible = value
        self.cmbEventType.setVisible(value)
        self.lblEventType.setVisible(value)


    def setSpecialityVisible(self, value):
        self.cmbSpeciality.setVisible(value)
        self.lblSpeciality.setVisible(value)


    def setEventTypeListListVisible(self, value):
        self.btnEventTypeList.setVisible(value)
        self.lblEventTypeList.setVisible(value)


    def setCMBOrgStructureVisible(self, value):
        self.isOrgStructureVisible = value
        self.cmbOrgStructure.setVisible(value)
        self.lblOrgStructure.setVisible(value)


    def setOrgStructureListVisible(self, value):
        self.btnOrgStructureList.setVisible(value)
        self.lblOrgStructureList.setVisible(value)


    def setAllAttachSelectable(self, value = False):
        self._isAllAttachSelectable = value
        self.chkFilterAttachType.setVisible(value)
        self.cmbFilterAttachCategory.setVisible(value)
        self.cmbFilterAttachType.setVisible(value)
        self.edtFilterAttachBegDate.setVisible(value)
        self.edtFilterAttachEndDate.setVisible(value)
        self.chkFilterDead.setVisible(value)
        self.chkFilterDeathBegDate.setVisible(value)
        self.chkFilterDeathEndDate.setVisible(value)
        self.edtFilterDeathBegDate.setVisible(value)
        self.edtFilterDeathEndDate.setVisible(value)
        self.chkFilterAttach.setVisible(value)
        self.chkFilterAttachNonBase.setVisible(value)
        self.cmbFilterAttachOrganisation.setVisible(value)
        self.chkFilterAttachNonBase.setVisible(value)
        self.chkFilterExcludeLeaved.setVisible(value)


    def setAGEVisible(self, value):
        self.frmAge.setVisible(value)
        self.lblAge.setVisible(value)
        self.lblAgeTo.setVisible(value)
        self.lblAgeYears.setVisible(value)
        self.edtAgeFrom.setVisible(value)
        self.edtAgeTo.setVisible(value)


    def setAGE(self, ageFrom, ageTo):
        self.edtAgeFrom.setValue(ageFrom)
        self.edtAgeTo.setValue(ageTo)


    def setAreaEnabled(self, mode=True):
        for widget in (self.chkArea, self.lblArea, self.cmbArea):
            widget.setVisible(mode)
        self.areaEnabled = mode

    def setFilterAddressOrgStructureVisible(self, mode=False):
        self.chkFilterAddressOrgStructure.setVisible(mode)
        self.cmbFilterAddressOrgStructureType.setVisible(mode)
        self.cmbFilterAddressOrgStructure.setVisible(mode)

    def setMKBFilterEnabled(self, mode=True):
        for widget in (self.lblMKB, self.frmMKB, self.lblMKBEx, self.frmMKBEx):
            widget.setVisible(mode)
        self.MKBFilterEnabled = mode


    def setPersonPostEnabled(self, mode=False):
        self.lblPersonPost.setVisible(mode)
        self.cmbPersonPost.setVisible(mode)
        self.personPostEnabled = mode


    def setAccountAccompEnabled(self, mode=True):
        self.chkAccountAccomp.setVisible(mode)
        self.accountAccompEnabled = mode


    def setOnlyFirstTimeEnabled(self, mode=True):
        self.chkOnlyFirstTime.setVisible(mode)
        self.onlyFirstTimeEnabled = mode


    def setRegisteredInPeriod(self, mode=True):
        self.chkRegisteredInPeriod.setVisible(mode)
        self.registeredInPeriod = mode


    def setUseInputDate(self, mode=True):
        self.chkUseInputDate.setVisible(mode)
        self.lblBegInputDate.setVisible(mode)
        self.lblEndInputDate.setVisible(mode)
        self.edtBegInputDate.setVisible(mode)
        self.edtEndInputDate.setVisible(mode)
        self.useInputDate = mode


    def setNotNullTraumaTypeEnabled(self, mode=True):
        self.chkNotNullTraumaType.setVisible(mode)
        self.notNullTraumaType = mode


    def setEventTypeDDEnabled(self, mode=True):
        self.lblEventTypeDD.setVisible(mode)
        self.cmbEventTypeDD.setVisible(mode)
        self.notEventTypeDD = mode


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setEventTypeVisible(self, visible=True):
        pass
        
    def setFinanceVisible(self, visible=True):
        self.lblFinance.setVisible(visible)
        self.cmbFinance.setVisible(visible)


    def setParams(self, params):
        self.chkUseInputDate.setChecked(bool(params.get('useInputDate', False)))
        self.edtBegInputDate.setDate(params.get('begInputDate', QDate.currentDate()))
        self.edtEndInputDate.setDate(params.get('endInputDate', QDate.currentDate()))
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbEventPurpose.setValue(params.get('eventPurposeId', None))
        if self.isEventTypeVisible:
            self.cmbEventType.setValue(params.get('eventTypeId', None))
        else:
            self.eventTypeList =  params.get('eventTypeList', [])
            if self.eventTypeList:
                db = QtGui.qApp.db
                tableET = db.table('EventType')
                records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(self.eventTypeList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblEventTypeList.setText(u','.join(name for name in nameList if name))
            else:
                self.lblEventTypeList.setText(u'не задано')
        self.cmbFinance.setValue(params.get('financeId', None))
        eventTypeDDId = None
        if self.notEventTypeDD:
            eventTypeDDId = params.get('eventTypeDDId', None)
            totalItems = self.cmbEventTypeDD._model.rowCount(None)
            if totalItems > 0:
                if not eventTypeDDId:
                    eventTypeDDId = self.cmbEventTypeDD._model.getId(0)
        self.cmbEventTypeDD.setValue(eventTypeDDId)
        if self.isOrgStructureVisible:
            self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        else:
            self.orgStructureList = params.get('orgStructureList', [])
            if self.orgStructureList:
                if len(self.orgStructureList) == 1 and not self.orgStructureList[0]:
                    self.lblOrgStructureList.setText(u'подразделение: ЛПУ')
                else:
                    db = QtGui.qApp.db
                    table = db.table('OrgStructure')
                    records = db.getRecordList(table, [table['name']], [table['deleted'].eq(0), table['id'].inlist(self.orgStructureList)])
                    self.lblOrgStructureList.setText(u', '.join(forceString(record.value('name')) for record in records if forceString(record.value('name'))))
            else:
                self.lblOrgStructureList.setText(u'подразделение: ЛПУ')
        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbSex.setCurrentIndex(params.get('sex', 0))
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 150))
        self.cmbSocStatusClass.setValue(params.get('socStatusClassId', None))
        self.cmbSocStatusType.setValue(params.get('socStatusTypeId', None))
        areaIdEnabled = bool(params.get('areaIdEnabled', False))
        self.chkArea.setChecked(areaIdEnabled)
        self.cmbArea.setEnabled(areaIdEnabled)
        self.cmbArea.setValue(params.get('areaId', None))
        MKBFilter = params.get('MKBFilter', 0)
        self.cmbMKBFilter.setCurrentIndex(MKBFilter if MKBFilter else 0)
        self.edtMKBFrom.setText(params.get('MKBFrom', 'A00'))
        self.edtMKBTo.setText(params.get('MKBTo',   'Z99.9'))
        self.cmbPhase.setValue(params.get('phaseId', None))
        MKBExFilter = params.get('MKBExFilter', 0)
        self.cmbMKBExFilter.setCurrentIndex(MKBExFilter if MKBExFilter else 0)
        self.edtMKBExFrom.setText(params.get('MKBExFrom', 'A00'))
        self.edtMKBExTo.setText(params.get('MKBExTo',   'Z99.9'))
        self.cmbPhaseEx.setValue(params.get('phaseIdEx', None))
        self.chkAccountAccomp.setChecked(bool(params.get('accountAccomp', False)))
        self.chkOnlyFirstTime.setChecked(bool(params.get('onlyFirstTime', False)))
        self.chkNotNullTraumaType.setChecked(bool(params.get('notNullTraumaType', False)))
        self.chkRegisteredInPeriod.setChecked(bool(params.get('registeredInPeriod', False)))
        self.cmbLocality.setCurrentIndex(params.get('locality', 0))
        self.chkFilterAddress.setChecked(bool(params.get('isFilterAddress', False)))
        self.cmbFilterAddressType.setCurrentIndex(params.get('filterAddressType', 0))
        self.cmbFilterAddressCity.setCode(params.get('filterAddressCity', QtGui.qApp.defaultKLADR()))
        addressStreet = params.get('filterAddressStreet', u'')
        if not addressStreet:
            addressStreet = QtGui.qApp.defaultKLADR()
            self.cmbFilterAddressStreet.setCity(addressStreet)
        else:
            self.cmbFilterAddressStreet.setCode(addressStreet)
        self.cmbFilterAddressOkato.setKladrCode(params.get('filterAddressOkato', QtGui.qApp.defaultKLADR()))
        self.edtFilterAddressHouse.setText(params.get('filterAddressHouse', u''))
        self.edtFilterAddressCorpus.setText(params.get('filterAddressCorpus', u''))
        self.edtFilterAddressFlat.setText(params.get('filterAddressFlat', u''))
        self.chkFilterAttachType.setChecked(params.get('chkFilterAttachType', False))
        attachCategory, attachTypeId, attachBegDate, attachEndDate = params.get('attachType', (0, None, QDate(), QDate()))
        self.cmbFilterAttachCategory.setCurrentIndex(attachCategory)
        self.cmbFilterAttachType.setValue(attachTypeId)
        self.edtFilterAttachBegDate.setDate(attachBegDate)
        self.edtFilterAttachEndDate.setDate(attachEndDate)
        self.chkFilterDead.setChecked(params.get('dead', False))
        self.chkFilterDeathBegDate.setChecked(params.get('chkFilterDeathBegDate', False))
        self.chkFilterDeathEndDate.setChecked(params.get('chkFilterDeathEndDate', False))
        self.edtFilterDeathBegDate.setDate(params.get('begDeathDate', QDate()))
        self.edtFilterDeathEndDate.setDate(params.get('endDeathDate', QDate()))
        self.chkFilterAttach.setChecked(params.get('chkFilterAttach', False))
        self.cmbFilterAttachOrganisation.setValue(params.get('attachTo', None))
        self.chkFilterAttachNonBase.setChecked(params.get('attachToNonBase', False))
        self.chkFilterExcludeLeaved.setChecked(params.get('excludeLeaved', False))
        if self.personPostEnabled:
            self.cmbPersonPost.setCurrentIndex(params.get('isPersonPost', 0))
        self.chkFilterAddressOrgStructure.setChecked(params.get('isFilterAddressOrgStructure', False))
        self.cmbFilterAddressOrgStructureType.setCurrentIndex(params.get('addressOrgStructureType', 0))
        self.cmbFilterAddressOrgStructure.setValue(params.get('addressOrgStructure', None))
        if self.isDispanserVisible:
            self.chkFilterDispanser.setChecked(params.get('isDispanser', False))


    def params(self):
        result = {}
        result['useInputDate'] = self.chkUseInputDate.isChecked()
        result['begInputDate'] = self.edtBegInputDate.date()
        result['endInputDate'] = self.edtEndInputDate.date()
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['specialityId'] = self.cmbSpeciality.value()
        result['eventPurposeId'] = self.cmbEventPurpose.value()
        if self.isEventTypeVisible:
            result['eventTypeId'] = self.cmbEventType.value()
        else:
            result['eventTypeList'] = self.eventTypeList
        result['financeId'] = self.cmbFinance.value()
        if self.notEventTypeDD:
            result['eventTypeDDId'] = self.cmbEventTypeDD.value()
        if self.isOrgStructureVisible:
            result['orgStructureId'] = self.cmbOrgStructure.value()
        else:
            if len(self.orgStructureList) == 1 and not self.orgStructureList[0]:
               result['orgStructureList'] = []
            else:
                result['orgStructureList'] = self.orgStructureList
        result['personId'] = self.cmbPerson.value()
        result['sex'] = self.cmbSex.currentIndex()
        result['ageFrom'] = self.edtAgeFrom.value()
        result['ageTo'] = self.edtAgeTo.value()
        result['socStatusClassId'] = self.cmbSocStatusClass.value()
        result['socStatusTypeId'] = self.cmbSocStatusType.value()
        if self.areaEnabled:
            result['areaIdEnabled'] = self.chkArea.isChecked()
            result['areaId'] = self.cmbArea.value()
        if self.MKBFilterEnabled:
            result['MKBFilter'] = self.cmbMKBFilter.currentIndex()
            result['MKBFrom']   = unicode(self.edtMKBFrom.text())
            result['MKBTo']     = unicode(self.edtMKBTo.text())
            result['phaseId']   = self.cmbPhase.value()
            result['MKBExFilter']= self.cmbMKBExFilter.currentIndex()
            result['MKBExFrom']  = unicode(self.edtMKBExFrom.text())
            result['MKBExTo']    = unicode(self.edtMKBExTo.text())
            result['phaseIdEx']  = self.cmbPhaseEx.value()
        if self.accountAccompEnabled:
            result['accountAccomp'] = self.chkAccountAccomp.isChecked()
        if self.onlyFirstTimeEnabled:
            result['onlyFirstTime'] = self.chkOnlyFirstTime.isChecked()
        if self.notNullTraumaType:
            result['notNullTraumaType'] = self.chkNotNullTraumaType.isChecked()
        result['registeredInPeriod'] = self.chkRegisteredInPeriod.isChecked()
        result['locality'] = self.cmbLocality.currentIndex()
        result['isFilterAddress'] = self.chkFilterAddress.isChecked()
        result['filterAddressType'] = self.cmbFilterAddressType.currentIndex()
        result['filterAddressCity'] = self.cmbFilterAddressCity.code()
        result['filterAddressOkato'] = self.cmbFilterAddressOkato.value()
        result['filterAddressStreet'] = self.cmbFilterAddressStreet.code()
        result['filterAddressStreetList'] = self.cmbFilterAddressStreet.codeList()
        result['filterAddressHouse'] = self.edtFilterAddressHouse.text()
        result['filterAddressCorpus'] = self.edtFilterAddressCorpus.text()
        result['filterAddressFlat'] = self.edtFilterAddressFlat.text()
        if self._isAllAttachSelectable:
            result['chkFilterAttachType'] = self.chkFilterAttachType.isChecked()
            if self.chkFilterAttachType.isChecked():
                result['attachType'] = (self.cmbFilterAttachCategory.currentIndex(),
                                        self.cmbFilterAttachType.value(),
                                        self.edtFilterAttachBegDate.date(),
                                        self.edtFilterAttachEndDate.date())
            result['chkFilterDead'] = self.chkFilterDead.isChecked()
            if self.chkFilterDead.isChecked():
                result['dead'] = True
            result['chkFilterDeathBegDate'] = self.chkFilterDeathBegDate.isChecked()
            if self.chkFilterDeathBegDate.isChecked():
                result['begDeathDate'] = self.edtFilterDeathBegDate.date()
            result['chkFilterDeathEndDate'] = self.chkFilterDeathEndDate.isChecked()
            if self.chkFilterDeathEndDate.isChecked():
                result['endDeathDate'] = self.edtFilterDeathEndDate.date()
            result['chkFilterAttach'] = self.chkFilterAttach.isChecked()
            result['chkFilterAttachNonBase'] = self.chkFilterAttachNonBase.isChecked()
            if self.chkFilterAttach.isChecked():
                result['attachTo'] = self.cmbFilterAttachOrganisation.value()
            elif self.chkFilterAttachNonBase.isChecked():
                result['attachToNonBase'] = True
            result['excludeLeaved'] = self.chkFilterExcludeLeaved.isChecked()
        if self.personPostEnabled:
            result['isPersonPost'] = self.cmbPersonPost.currentIndex()
        result['isFilterAddressOrgStructure'] = self.chkFilterAddressOrgStructure.isChecked()
        result['addressOrgStructureType'] = self.cmbFilterAddressOrgStructureType.currentIndex()
        result['addressOrgStructure'] = self.cmbFilterAddressOrgStructure.value()
        if self.isDispanserVisible:
            result['isDispanser'] = self.chkFilterDispanser.isChecked()
        return result


    def exec_(self):
        result = CDialogBase.exec_(self)
        if self._isAllAddressSelectable:
            self.setAllAddressSelectable(False)
        return result


    def setAllAddressSelectable(self, value):
        self._isAllAddressSelectable = value
        self.cmbFilterAddressCity.model().setAllSelectable(value)


    @pyqtSignature('int')
    def on_cmbEventPurpose_currentIndexChanged(self, index):
        if self.isEventTypeVisible:
            eventPurposeId = self.cmbEventPurpose.value()
            if eventPurposeId:
                filter = 'EventType.purpose_id=%d' % eventPurposeId
            else:
                filter = getWorkEventTypeFilter(isApplyActive=True)
            self.cmbEventType.setFilter(filter)


    @pyqtSignature('bool')
    def on_chkUseInputDate_toggled(self, checked):
        self.lblBegInputDate.setEnabled(checked)
        self.edtBegInputDate.setEnabled(checked)
        self.lblEndInputDate.setEnabled(checked)
        self.edtEndInputDate.setEnabled(checked)


    @pyqtSignature('int')
    def on_cmbFilterAddressCity_currentIndexChanged(self, index):
        code = self.cmbFilterAddressCity.code()
        self.cmbFilterAddressStreet.setCity(code)
        self.cmbFilterAddressOkato.setKladrCode(code)

    @pyqtSignature('int')
    def on_cmbFilterAddressOkato_currentIndexChanged(self, index):
        okato = self.cmbFilterAddressOkato.value()
        self.cmbFilterAddressStreet.setOkato(okato)


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.cmbPerson.setBegDate(date)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.cmbPerson.setEndDate(date)


    @pyqtSignature('int')
    def on_cmbSocStatusClass_currentIndexChanged(self, index):
        socStatusClassId = self.cmbSocStatusClass.value()
        filter = ('class_id=%d' % socStatusClassId) if socStatusClassId else ''
        self.cmbSocStatusType.setFilter(filter)


    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        self.edtMKBFrom.setEnabled(index == 1)
        self.edtMKBTo.setEnabled(index == 1)
        self.cmbPhase.setEnabled(index == 1)


    @pyqtSignature('int')
    def on_cmbMKBExFilter_currentIndexChanged(self, index):
        self.edtMKBExFrom.setEnabled(index == 1)
        self.edtMKBExTo.setEnabled(index == 1)
        self.cmbPhaseEx.setEnabled(index == 1)


    @pyqtSignature('')
    def on_btnEventTypeList_clicked(self):
        self.eventTypeList = []
        self.lblEventTypeList.setText(u'не задано')
        eventPurposeId = self.cmbEventPurpose.value()
        if eventPurposeId:
            filter = u'EventType.purpose_id =%d' % eventPurposeId
        else:
            filter = getWorkEventTypeFilter(isApplyActive=True)
        dialog = CEventTypeListEditorDialog(self, filter)
        if dialog.exec_():
            self.eventTypeList = dialog.values()
            if self.eventTypeList:
                db = QtGui.qApp.db
                tableET = db.table('EventType')
                records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(self.eventTypeList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblEventTypeList.setText(u','.join(name for name in nameList if name))


    @pyqtSignature('')
    def on_btnOrgStructureList_clicked(self):
        self.orgStructureList = []
        db = QtGui.qApp.db
        self.lblOrgStructureList.setText(u'подразделение: ЛПУ')
        orgId = QtGui.qApp.currentOrgId()
        filter = []
        if orgId:
            filter.append(u'organisation_id = %s'%(orgId))
        dialog = CSelectOrgStructureListDialog(self, db.joinAnd(filter))
        if dialog.exec_():
            self.orgStructureList = dialog.values()
            if self.orgStructureList:
                if len(self.orgStructureList) == 1 and not self.orgStructureList[0]:
                    self.lblOrgStructureList.setText(u'подразделение: ЛПУ')
                else:
                    table = db.table('OrgStructure')
                    records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.orgStructureList)])
                    nameList = []
                    for record in records:
                        nameList.append(forceString(record.value('name')))
                    self.lblOrgStructureList.setText(u', '.join(name for name in nameList if name))


    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        specialityId = self.cmbSpeciality.value()
        self.cmbPerson.setSpecialityId(specialityId)

