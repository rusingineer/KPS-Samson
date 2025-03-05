# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
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

from Orgs.Utils import getOrgStructureListDescendants, getOrgStructureFullName
from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportSetupDialog import CReportSetupDialog
from Reports.ReportView import CPageFormat
from library.Utils import forceInt, forceString, forceDate, calcAge, forceRef, forceBool


def selectData(params):
    endDate = params.get('endDate', QDate())
    endTime = params.get('endTime', QTime())
    orgStructureId = params.get('orgStructureId', None)
    descendantsIdList = []

    if orgStructureId:
        descendantsIdList = getOrgStructureListDescendants([orgStructureId])

    db = QtGui.qApp.db

    tableEvent = db.table('Event')
    tableAction = db.table('Action')
    tableOrgStructureHospitalBed = db.table('OrgStructure_HospitalBed')
    tableRbHospitalBedProfile = db.table('rbHospitalBedProfile')
    tableRbHospitalBedType = db.table('rbHospitalBedType')
    tableOrgStrucutre = db.table('OrgStructure')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    # tableAssociatedDiagnostic = db.table('Diagnostic').alias('AssociatedDiagnostic')
    tableDiagnosis = db.table('Diagnosis')
    # tableAssociatedDiagnosis = db.table('Diagnosis').alias('AssociatedDiagnosis')
    queryTable = tableOrgStructureHospitalBed
    queryTable = queryTable.leftJoin(tableRbHospitalBedProfile, tableRbHospitalBedProfile['id'].eq(tableOrgStructureHospitalBed['profile_id']))
    queryTable = queryTable.leftJoin(tableRbHospitalBedType, tableRbHospitalBedType['id'].eq(tableOrgStructureHospitalBed['type_id']))
    queryTable = queryTable.leftJoin(tableOrgStrucutre, tableOrgStrucutre['id'].eq(tableOrgStructureHospitalBed['master_id']))
    queryTable = queryTable.leftJoin(tableAction, '''Action.id = (SELECT Action.id
  FROM ActionProperty_HospitalBed
  LEFT JOIN ActionProperty ON ActionProperty_HospitalBed.`id` = ActionProperty.`id` AND ActionProperty.deleted = 0
  LEFT JOIN Action ON ActionProperty.`action_id` = Action.`id` AND Action.deleted = 0
  LEFT JOIN ActionType at ON at.id = Action.actionType_id AND at.deleted = 0
  WHERE ActionProperty_HospitalBed.value = OrgStructure_HospitalBed.id
    AND at.flatCode = 'moving'
    AND Action.status in (0, 2)
    AND (Action.`endDate` IS NULL OR Action.`endDate` > '{0}')
    AND (Action.begDate < '{1}')
  ORDER BY Action.`begDate` DESC LIMIT 1
  )'''.format(
        " ".join([db.formatDate(endDate), db.formatTime(endTime)]).replace("'", ""),
              " ".join([db.formatDate(endDate), db.formatTime(endTime)]).replace("'", "")
            ))
    queryTable = queryTable.leftJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableDiagnostic, [tableDiagnostic['event_id'].eq(tableEvent['id']), '''Diagnostic.id = (SELECT d.id
      FROM Diagnostic d
      INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = d.diagnosisType_id
      WHERE d.event_id = Event.id
      AND rbDiagnosisType.CODE = '7'
      AND d.deleted = 0
      ORDER BY rbDiagnosisType.code
      LIMIT 1)'''])
    # queryTable = queryTable.leftJoin(tableAssociatedDiagnostic, [tableAssociatedDiagnostic['event_id'].eq(tableEvent['id']), '''AssociatedDiagnostic.id = (SELECT d.id
    #   FROM Diagnostic d
    #   INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = d.diagnosisType_id
    #   WHERE d.event_id = Event.id
    #   AND rbDiagnosisType.CODE = '11'
    #   AND d.deleted = 0
    #   ORDER BY rbDiagnosisType.code
    #   LIMIT 1)'''])
    queryTable = queryTable.leftJoin(tableDiagnosis, [tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']), tableDiagnosis['deleted'].eq(0)])
    # queryTable = queryTable.leftJoin(tableAssociatedDiagnosis, [tableAssociatedDiagnosis['id'].eq(tableAssociatedDiagnostic['diagnosis_id']), tableAssociatedDiagnosis['deleted'].eq(0)])

    cols = [tableOrgStructureHospitalBed['id'].alias('OSHBId'),
            tableOrgStructureHospitalBed['master_id'].alias('masterOrgStructure'),
            tableOrgStrucutre['name'].alias('orgStructureName'),
            tableOrgStructureHospitalBed['code'].alias('OSHBCode'),
            tableOrgStructureHospitalBed['name'].alias('OSHBName'),
            tableOrgStructureHospitalBed['relief'].alias('OSHBrelief'),
            tableOrgStructureHospitalBed['isPermanent'],
            tableRbHospitalBedType['name'].alias('typeName'),
            tableOrgStructureHospitalBed['sex'].alias('clientSex'),
            tableClient['lastName'].alias('clientLastName'),
            tableClient['firstName'].alias('clientFirstName'),
            tableClient['patrName'].alias('clientPatrName'),
            tableClient['birthDate'].alias('clientBirthDate'),
            tableDiagnosis['MKB'].alias('clientMKB'),
            # tableAssociatedDiagnosis['MKB'].alias('clientMKBEx'),
            tableAction['begDate'].alias('clientBegDate'),
            tableAction['endDate'].alias('clientEndDate'),
            tableEvent['id'].alias('eventId')
            ]
    cond = ["OrgStructure_HospitalBed.deleted = 0 AND (OrgStructure_HospitalBed.`endDate` IS NULL OR OrgStructure_HospitalBed.`endDate` > '{0}')".format(" ".join([db.formatDate(endDate), db.formatTime(endTime)]).replace("'", ""))]
    if descendantsIdList:
        cond.append(tableOrgStructureHospitalBed['master_id'].inlist(descendantsIdList))

    recordsList = db.getRecordList(queryTable, cols, cond, 'OrgStructure_HospitalBed.code, OrgStructure.name')

    return recordsList


class CReportBedFund(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по коечному фонду')
        self.setOrientation(QtGui.QPrinter.Landscape)
        self.pageFormat = CPageFormat(pageSize=QtGui.QPrinter.A4, orientation=QtGui.QPrinter.Landscape, leftMargin=10, topMargin=10, rightMargin=10, bottomMargin=10)

    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setTitle(self.title())
        result.setFixedHeight(150)

        result.setEventTypeVisible(False)
        result.setOnlyPermanentAttachVisible(False)
        result.setDatePeriodVisible(True)
        result.lblEndDate.setText(u'Дата/Время')

        result.lblBegDate.setVisible(False)
        result.edtBegDate.setVisible(False)

        result.setTimePeriodVisible(True)
        result.edtBegTime.setVisible(False)

        result.setOrgStructureVisible(True)
        return result

    def getDescription(self, params):
        rows = []
        endDate = params.get('endDate', QDate())
        endTime = params.get('endTime', QTime())
        if endDate:
            rows.append(u'На дату: {0} {1}'.format(forceString(endDate), forceString(endTime)))

        orgStructureId = params.get('orgStructureId', None)
        if orgStructureId:
            rows.append(u'Подразделение: ' + getOrgStructureFullName(orgStructureId))

        rows.append(u'Отчёт составлен: %s'%forceString(QDateTime.currentDateTime()))

        return rows

    def loadData(self, hospitalBedId, ignoreEventID, endDate):
        sex = [u'', u'М', u'Ж']
        items = []
        db = QtGui.qApp.db
        tableAPHB = db.table('ActionProperty_HospitalBed')
        tableAP = db.table('ActionProperty')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableEventType = db.table('EventType')
        tableDiagnostic = db.table('Diagnostic')
        tableDiagnosis = db.table('Diagnosis')
        tablePersonWithSpeciality = db.table('vrbPersonWithSpeciality')
        queryTable = tableAPHB.leftJoin(tableAP, tableAPHB['id'].eq(tableAP['id']))
        queryTable = queryTable.leftJoin(tableAction, tableAction['id'].eq(tableAP['action_id']))
        queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        queryTable = queryTable.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        queryTable = queryTable.leftJoin(tablePersonWithSpeciality, tableEvent['execPerson_id'].eq(tablePersonWithSpeciality['id']))
        queryTable = queryTable.leftJoin(tableDiagnostic, [tableDiagnostic['event_id'].eq(tableEvent['id']), '''Diagnostic.id = (SELECT d.id
          FROM Diagnostic d
          INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = d.diagnosisType_id
          WHERE d.event_id = Event.id
          AND rbDiagnosisType.CODE = '7'
          AND d.deleted = 0
          ORDER BY rbDiagnosisType.code
          LIMIT 1)'''])
        queryTable = queryTable.leftJoin(tableDiagnosis, [tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']), tableDiagnosis['deleted'].eq(0)])
        cols = [tableEvent['id'].alias('eventId'),
                tableEvent['client_id'],
                tableClient['lastName'],
                tableClient['firstName'],
                tableClient['patrName'],
                tableClient['sex'],
                tableClient['birthDate'],
                tableEvent['setDate'],
                tableEvent['execDate'],
                tablePersonWithSpeciality['name'],
                tableEventType['name'].alias('eventType'),
                tableAction['begDate'].alias('clientBegDate'),
                tableDiagnosis['MKB'].alias('clientMKB')
               ]
        cond = [ tableAPHB['value'].eq(hospitalBedId),
                 tableAction['deleted'].eq(0),
                 tableAction['status'].inlist([0, 1]),
                 tableEvent['deleted'].eq(0),
               ]
        if endDate:
            cond.append(tableAction['begDate'].le(endDate))
            cond.append(db.joinOr([tableAction['endDate'].gt(endDate), tableAction['endDate'].isNull()]))

        records = db.getRecordList(queryTable, cols, cond)
        for record in records:
            if forceRef(record.value('eventId')) != ignoreEventID:
                clientId = forceRef(record.value('client_id'))
                sexClient = sex[forceInt(record.value('sex'))]
                item = [clientId,
                        forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                        sexClient,
                        forceDate(record.value('birthDate')),
                        forceDate(record.value('setDate')),
                        forceDate(record.value('execDate')),
                        forceString(record.value('eventType')),
                        forceString(record.value('name')),
                        forceRef(record.value('eventId')),
                        forceString(record.value('clientBegDate')),
                        forceString(record.value('clientMKB'))
                       ]
                items.append(item)

        return items

    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()

        tableColumns = [
            ('3%', [u'№', u'1'], CReportBase.AlignLeft),
            ('15%', [u'Отделение', u'2'], CReportBase.AlignLeft),
            ('25%', [u'Койка', u'3'], CReportBase.AlignRight),
            ('5%', [u'Штат', u'4'], CReportBase.AlignRight),
            ('3%', [u'Смены', u'5'], CReportBase.AlignRight),
            ('10%', [u'Тип койки', u'6'], CReportBase.AlignRight),
            ('3%', [u'Пол', u'7'], CReportBase.AlignRight),
            ('3%', [u'Свободно/Занято', u'8'], CReportBase.AlignRight),
            ('18%', [u'ФИО', u'9'], CReportBase.AlignRight),
            ('3%', [u'Возраст', u'10'], CReportBase.AlignRight),
            ('10%', [u'Дата поступления', u'11'], CReportBase.AlignRight),
            ('5%', [u'Предварительный диагноз (МКБ)', u'12'], CReportBase.AlignRight),
        ]
        recordsList = selectData(params)

        endDate = params.get('endDate', QDate())
        endTime = params.get('endTime', QTime())
        if not endTime.isNull():
            endDateTime = QDateTime(endDate, endTime)
            endDate = endDateTime

        self.dumpParams(cursor, params)
        cursor.insertBlock()
        table = createTable(cursor, tableColumns)


        if recordsList:
            boldChars = QtGui.QTextCharFormat()
            boldChars.setFontWeight(QtGui.QFont.Bold)
            col_num = 0
            for record in recordsList:
                eventId = forceInt(record.value('eventId'))
                orgStructureName = forceString(record.value('orgStructureName'))
                OSHBId = forceString(record.value('OSHBId'))
                code = forceString(record.value('OSHBCode'))
                name = forceString(record.value('OSHBName'))
                relief = forceString(record.value('OSHBrelief'))
                typeName = forceString(record.value('typeName'))
                clientSex = forceInt(record.value('clientSex'))
                if clientSex == 1:
                    clientSex = u'М'
                elif clientSex == 2:
                    clientSex = u'Ж'
                else:
                    clientSex = u''
                lastName = forceString(record.value('clientLastName'))
                firstName = forceString(record.value('clientFirstName'))
                patrName = forceString(record.value('clientPatrName'))
                fullName = u'{0} {1} {2}'.format(lastName, firstName, patrName)
                birthDate = forceDate(record.value('clientBirthDate'))
                age = ''
                if birthDate:
                    age = calcAge(birthDate, params.get('endDate', QDate()))
                MKB = forceString(record.value('clientMKB'))
                clientBegDate = forceString(record.value('clientBegDate'))
                isPermanent = u'[ш] 'if forceBool(record.value('isPermanent')) else u'[]'

                n = table.addRow()
                col_num += 1
                table.setText(n, 0, col_num)
                table.setText(n, 1, orgStructureName)
                table.setText(n, 2, code + u" " + name)
                table.setText(n, 3, isPermanent)
                table.setText(n, 4, relief)
                table.setText(n, 5, typeName)

                if fullName.replace(" ", "") == "":
                    table.setText(n, 7, u'Свободно')
                else:
                    table.setText(n, 7, u'Занято')

                    table.setText(n, 6, clientSex)
                    table.setText(n, 8, fullName)
                    table.setText(n, 9, age)
                    table.setText(n, 10, clientBegDate)
                    table.setText(n, 11, MKB)

                if int(relief) > 1:
                    items = self.loadData(OSHBId, eventId, endDate)
                    if items:
                        for item in items:
                            n = table.addRow()
                            table.setText(n, 0, u"   ")
                            table.setText(n, 1, u'    ')
                            table.setText(n, 2, u'    ')
                            table.setText(n, 3, u'    ')
                            table.setText(n, 4, u'    ')
                            table.setText(n, 5, u'   ')
                            table.setText(n, 6, clientSex)
                            table.setText(n, 7, u'Занято')
                            table.setText(n, 8, item[1])
                            table.setText(n, 9, calcAge(item[3]))
                            table.setText(n, 10, item[9])
                            table.setText(n, 11, item[10])

                    ost = int(relief) - (len(items) + 1)
                    for _ in xrange(ost):
                        n = table.addRow()
                        table.setText(n, 0, u"   ")
                        table.setText(n, 1, u'    ')
                        table.setText(n, 2, u'    ')
                        table.setText(n, 3, u'    ')
                        table.setText(n, 4, u'    ')
                        table.setText(n, 5, u'    ')
                        table.setText(n, 6, u'   ')
                        table.setText(n, 7, u'Свободно')
                        table.setText(n, 8, u'   ')
                        table.setText(n, 9, u'   ')
                        table.setText(n, 10, u'   ')
                        table.setText(n, 11, u'   ')

        return doc
