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
from PyQt4.QtCore import Qt, SIGNAL, QDate

from library.Utils      import forceDate, forceRef, forceString, smartDict
from library.DateEdit   import CDateEdit
from Orgs.OrgStructComboBoxes import COrgStructureComboBox
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable


def selectData(params):
    begDate                  = params.get('begDate', None)
    endDate                  = params.get('endDate', None)
    policyType               = params.get('policyType', 0)
    attacheTypeTemporary     = params.get('attacheTypeTemporary', 0)
    sex                      = params.get('sex', 0)
    begAge, endAge           = params.get('age', (0, 150))
    orgStructureIdList       = params.get('orgStructureIdList', None)

    db = QtGui.qApp.db

    tableClientAttach  = db.table('ClientAttach')
    tableClient        = db.table('Client')
    tableAttachType    = db.table('rbAttachType')
    tableClientPolicy  = db.table('ClientPolicy')
    tableCP            = db.table('ClientPolicy').alias('CP')
    tableInsurer       = db.table('Organisation').alias('Insurer')

    queryTable = tableClientAttach

    queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(tableClientAttach['client_id']))
    queryTable = queryTable.leftJoin(tableClientPolicy, tableClientPolicy['client_id'].eq(tableClientAttach['client_id']))
    queryTable = queryTable.leftJoin(tableInsurer, tableClientPolicy['insurer_id'].eq(tableInsurer['id']))
    if attacheTypeTemporary:
        queryTable = queryTable.leftJoin(tableAttachType, tableAttachType['id'].eq(tableClientAttach['attachType_id']))

    cond = [tableClientAttach['deleted'].eq(0),
            tableClientPolicy['deleted'].eq(0)]

    if begDate:
        cond.append(db.joinOr([tableClientAttach['endDate'].ge(begDate),
                               tableClientAttach['endDate'].isNull()])
                   )
    if endDate:
        cond.append(tableClientAttach['begDate'].lt(endDate.addDays(1)))
    if attacheTypeTemporary:
        cond.append(tableAttachType['temporary'].eq(attacheTypeTemporary-1))

    pedc = [tableCP['endDate'].isNull()]
    if begDate:
        pedc.append(tableCP['endDate'].ge(begDate))

    pbdc = [tableCP['begDate'].isNull()]
    if endDate:
        pbdc.append(tableCP['begDate'].lt(endDate.addDays(1)))

    datePolicyCond = db.joinAnd( [ db.joinOr(pedc), db.joinOr(pbdc) ] )

    templatePolicyTypeCond = '''
                          ClientPolicy.`id` = (SELECT MAX(CP.`id`) FROM ClientPolicy AS CP
                          WHERE ClientPolicy.`client_id` = CP.`client_id`
                          AND %s
                          AND %s )
                             ''' % (datePolicyCond, '%s')



    if policyType:
        codeList = ['1', '2'] if policyType == 1 else ['3']
        idList = [forceRef(QtGui.qApp.db.translate('rbPolicyType', 'code', code, 'id')) for code in codeList]
        policyTypeCond = tableCP['policyType_id'].inlist(idList)
        cond.append(templatePolicyTypeCond % policyTypeCond)
    else:
        idList = [forceRef(QtGui.qApp.db.translate('rbPolicyType', 'code', code, 'id')) for code in ('1', '2')]
        id = forceRef(QtGui.qApp.db.translate('rbPolicyType', 'code', '3', 'id'))
        cond1 = templatePolicyTypeCond % tableCP['policyType_id'].inlist(idList)
        cond2 = templatePolicyTypeCond % tableCP['policyType_id'].eq(id)
        policyTypeCond = db.joinOr([cond1, cond2])
        cond.append(policyTypeCond)

    if sex:
        cond.append(tableClient['sex'].eq(sex))

    if (begAge, endAge) != (0, 150):
        cond.append(tableClient['birthDate'].lt(locCalcBirthDate(begAge).addDays(1)))
        cond.append(tableClient['birthDate'].ge(locCalcBirthDate(endAge)))

    if orgStructureIdList:
        cond.append(tableClientAttach['orgStructure_id'].inlist(orgStructureIdList))

    fields = [tableClientAttach['client_id'].alias('clientId'),
              tableClientAttach['begDate'].name(),
              tableClientAttach['endDate'].name(),
              tableClientAttach['modifyDatetime'].name(),
              tableInsurer['shortName'].alias('organisationName'),
              tableInsurer['infisCode'].name(),
              tableInsurer['id'].alias('insurerId')]

    stmt = db.selectDistinctStmt(queryTable, fields, cond)
#    print stmt
    return db.query(stmt)


def locCalcBirthDate(value):
    result = QDate.currentDate()
    return result.addYears(-value)



class CReportAttachingMotion(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по движению контингентов')
        self._mapInsurer2Info = {}
        self.resetHelpers()

    def resetHelpers(self):
        self._mapInsurer2Info.clear()


    def getSetupDialog(self, parent):
        result = CReportAttachingMotionSetup(parent, self)
        result.setTitle(self.title())
        return result


    def getDescription(self, params):
        begDate                  = params.get('begDate', None)
        endDate                  = params.get('endDate', None)
        policyType               = params.get('policyType', 0)
        policyTypeText           = params.get('policyTypeText', '')
        attacheTypeTemporary     = params.get('attacheTypeTemporary', 0)
        attacheTypeTemporaryText = params.get('attacheTypeTemporaryText', '')
        sex                      = params.get('sex', 0)
        begAge, endAge           = params.get('age', (0, 150))

        rows = []
        if begDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endDate))
        if policyType:
            rows.append(u'Тип полиса: %s'%policyTypeText)
        if attacheTypeTemporary:
            rows.append(u'Тип прикрепления: %s'%attacheTypeTemporaryText)
        if (begAge, endAge) != (0, 150):
            rows.append(u'Возраст: от %d до %d' % (begAge, endAge))
        if sex:
            rows.append(u'Пол: %s' % (u'М' if sex==1 else u'Ж'))

        return rows


    def build(self, params):
#        print QDateTime.currentDateTime().time()
        query = selectData(params)
#        print 'query was done: ', QDateTime.currentDateTime().time()
        self.structInfo(query, params)
#        print 'was struckted: ', QDateTime.currentDateTime().time()

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
                        ('%2',
                        [u'№', u''], CReportBase.AlignRight),
                        ('%7',
                        [u'Код', u''], CReportBase.AlignRight),
                        ('%23',
                        [u'Организация', u''], CReportBase.AlignRight),
                        ('%7',
                        [u'Кол-во на начало периода', u''], CReportBase.AlignRight),
                        ('%7',
                        [u'Прикрепление', u'Всего'], CReportBase.AlignRight),
                        ('%7',
                        [u'', u'В т.ч. продление'], CReportBase.AlignRight),
                        ('%7',
                        [u'', u'В т.ч. первично'], CReportBase.AlignRight),
                        ('%7',
                        [u'Снятие', u'Всего'], CReportBase.AlignRight),
                        ('%7',
                        [u'', u'В т.ч. по срокам'], CReportBase.AlignRight),
                        ('%7',
                        [u'', u'В т.ч. по списку г/п'], CReportBase.AlignRight),
                        ('%7',
                        [u'Дельта', u''], CReportBase.AlignRight),
                        ('%7',
                        [u'Кол-во на конеч периода', u''], CReportBase.AlignRight),
                        ]

        table = createTable(cursor, tableColumns)

        table.mergeCells(0, 0,  2, 1)
        table.mergeCells(0, 1,  2, 1)
        table.mergeCells(0, 2,  2, 1)
        table.mergeCells(0, 3,  2, 1)
        table.mergeCells(0, 4,  1, 3)
        table.mergeCells(0, 7,  1, 3)
        table.mergeCells(0, 10, 2, 1)
        table.mergeCells(0, 10, 2, 1)

        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)

        keysList = self._mapInsurer2Info.keys()
        keysList.sort()

        result = [0]*9
        for insurerId in keysList:
            info = self._mapInsurer2Info[insurerId][0]

            i = table.addRow()
            table.setText(i, 0, i)

            for idx, value in enumerate(info):
                table.setText(i, idx+1, value)
                if idx > 1:
                    result[idx-2] += value

        i = table.addRow()
        table.mergeCells(i, 0,  1, 3)
        table.setText(i, 0, u'Всего', charFormat=boldChars)
        for idx, value in enumerate(result):
            table.setText(i, idx+3, value, charFormat=boldChars)

        return doc


    def structInfo(self, query, params):
        self.resetHelpers()

        condBegDate                  = params.get('begDate', None)
        condEndDate                  = params.get('endDate', None)

        while query.next():
            record = query.record()

            begDate = forceDate(record.value('begDate'))
            endDate = forceDate(record.value('endDate'))
            modifyDatetime = forceDate(record.value('modifyDatetime'))
            clientId = forceRef(record.value('clientId'))
            insurerId = forceRef(record.value('insurerId'))
            organisationName = forceString(record.value('organisationName')) if insurerId else u'Не определено'
            infisCode = forceString(record.value('infisCode'))

            info, infoHelper = self._mapInsurer2Info.setdefault(insurerId, (
                                                                            [infisCode, organisationName]+[0]*9,
                                                                            smartDict(clientListInRange=[])
                                                                           )
                                                               )

            if not begDate or begDate < condBegDate:
                info[2] += 1
                info[9] -= 1

            if condBegDate <= begDate and begDate <= condEndDate:
                info[3] += 1

                if clientId in infoHelper.clientListInRange:
                    info[5] += 1
                else:
                    info[4] += 1
                    infoHelper.clientListInRange.append(clientId)

            if endDate and condBegDate <= endDate and endDate <= condEndDate:
                info[6] += 1

                if modifyDatetime == begDate:
                    info[7] += 1
                else:
                    info[8] += 1

            if not endDate or endDate > condEndDate:
                info[10] += 1
                info[9] += 1




class CReportAttachingMotionSetup(QtGui.QDialog):
    def __init__(self, parent, report):
        QtGui.QDialog.__init__(self, parent)

        self.gridLayout = QtGui.QGridLayout(self)

        self.lblBegDate = QtGui.QLabel(u'От', self)
        self.edtBegDate = CDateEdit(self)

        self.gridLayout.addWidget(self.lblBegDate, 0, 0)
        self.gridLayout.addWidget(self.edtBegDate, 0, 1)

        self.lblEndDate   = QtGui.QLabel(u'по', self)
        self.edtEndDate   = CDateEdit(self)

        self.gridLayout.addWidget(self.lblEndDate, 1, 0)
        self.gridLayout.addWidget(self.edtEndDate, 1, 1)

        self.lblAttacheTypeTemporary = QtGui.QLabel(u'Тип прикрепления', self)
        self.cmbAttacheTypeTemporary = QtGui.QComboBox(self)
        self.cmbAttacheTypeTemporary.addItem(u'Не учитывать')
        self.cmbAttacheTypeTemporary.addItem(u'Постоянное')
        self.cmbAttacheTypeTemporary.addItem(u'Временное')

        self.gridLayout.addWidget(self.lblAttacheTypeTemporary, 2, 0)
        self.gridLayout.addWidget(self.cmbAttacheTypeTemporary, 2, 1)

        self.lblPolicyType = QtGui.QLabel(u'Тип полиса', self)
        self.cmbPolicyType = QtGui.QComboBox(self)
        self.cmbPolicyType.addItem(u'Не учитывать')
        self.cmbPolicyType.addItem(u'ОМС')
        self.cmbPolicyType.addItem(u'ДМС')

        self.gridLayout.addWidget(self.lblPolicyType, 3, 0)
        self.gridLayout.addWidget(self.cmbPolicyType, 3, 1)

        self.lblSex = QtGui.QLabel(u'Пол', self)
        self.cmbSex = QtGui.QComboBox(self)
        self.cmbSex.addItem(u'')
        self.cmbSex.addItem(u'М')
        self.cmbSex.addItem(u'Ж')

        self.gridLayout.addWidget(self.lblSex, 4, 0)
        self.gridLayout.addWidget(self.cmbSex, 4, 1)

        self.lblAge = QtGui.QLabel(u'Возраст', self)
        self.edtBegAge = QtGui.QSpinBox(self)
        self.edtEndAge = QtGui.QSpinBox(self)
        self.edtBegAge.setRange(0, 150)
        self.edtEndAge.setRange(0, 150)
        self.edtEndAge.setValue(150)
        self.ageLayout = QtGui.QHBoxLayout(self)
        self.ageLayout.addWidget(self.edtBegAge)
        self.ageLayout.addWidget(self.edtEndAge)

        self.gridLayout.addWidget(self.lblAge, 5, 0)
        self.gridLayout.addLayout(self.ageLayout, 5, 1)

        self.lblOrgStructure = QtGui.QLabel(u'Подразделение', self)
        self.cmbOrgStructure = COrgStructureComboBox(self)

        self.gridLayout.addWidget(self.lblOrgStructure, 6, 0)
        self.gridLayout.addWidget(self.cmbOrgStructure, 6, 1)

        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)

        self.gridLayout.addWidget(self.buttonBox, 7, 1)

        self.connect(self.buttonBox, SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, SIGNAL('rejected()'), self.reject)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbAttacheTypeTemporary.setCurrentIndex(params.get('attacheTypeTemporary', 0))
        self.cmbPolicyType.setCurrentIndex(params.get('policyType', 0))
        self.cmbSex.setCurrentIndex(params.get('sex', 0))
        begAge, endAge = params.get('age', (0, 150))
        self.edtBegAge.setValue(begAge)
        self.edtEndAge.setValue(endAge)
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))


    def params(self):
        params = {}

        params['begDate'] = self.edtBegDate.date()
        params['endDate'] = self.edtEndDate.date()

        params['attacheTypeTemporary']  = self.cmbAttacheTypeTemporary.currentIndex()
        params['attacheTypeTemporaryText']  = self.cmbAttacheTypeTemporary.currentText()
        params['policyType'] = self.cmbPolicyType.currentIndex()
        params['policyTypeText']  = self.cmbPolicyType.currentText()

        params['sex'] = self.cmbSex.currentIndex()
        params['age'] = (self.edtBegAge.value(), self.edtEndAge.value())

        params['orgStructureId'] = self.cmbOrgStructure.value()
        if params['orgStructureId']:
            params['orgStructureIdList'] = self.cmbOrgStructure.getItemIdList()

        return params












