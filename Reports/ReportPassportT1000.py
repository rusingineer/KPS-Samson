# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4              import QtGui
from PyQt4.QtCore       import Qt, QDate
from library.Utils      import forceInt, forceString
from library.database   import decorateString
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable


def selectData(params):
    db = QtGui.qApp.db
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId')
    accountingSystemId = forceInt(db.translate('rbAccountingSystem', 'code', 'reportT1000', 'id'))

    stmt = u'''
    SELECT
        Client.id,
        Client.sex,
        age(Client.birthDate, {endDate}) AS age,
        rbSocStatusClass.name AS className,
        rbSocStatusType.code AS typeCode,
        ClientWork.okved AS clientOkved,
        Diagnosis.MKB,
        ClientSocStatus.endDate AS socStatusEndDate,
        IF(rbRiskFactor_Identification.id IS NULL, '', rbRiskFactor_Identification.value) AS riskFactorName,
        (
            ClientWork.id IS NOT NULL
            AND
            (
                (ClientWork.OKVED != '' AND ClientWork.freeInput != '')
                OR ClientWork.org_id IS NOT NULL
            )
        ) AS isWorking,
        (
            SELECT
                OKVED
            FROM
                Organisation
            WHERE
                deleted = 0
                AND id = ClientWork.org_id
        ) AS orgOkved,
        (
            ClientWork_Hurt.hurtType_id IS NOT NULL
        ) AS hasWorkHurt,
        BenefitClass.name AS benefitName
    FROM
        Client
        LEFT JOIN ClientSocStatus ON ClientSocStatus.client_id = Client.id
            AND ClientSocStatus.deleted = 0
            AND (ClientSocStatus.endDate IS NULL OR DATE(ClientSocStatus.endDate) > {begDate})
        LEFT JOIN rbSocStatusClass ON ClientSocStatus.socStatusClass_id = rbSocStatusClass.id
        LEFT JOIN rbSocStatusType ON ClientSocStatus.socStatusType_id = rbSocStatusType.id
        LEFT JOIN rbSocStatusClassTypeAssoc ON rbSocStatusClassTypeAssoc.type_id = rbSocStatusType.id
        LEFT JOIN rbSocStatusClass AS BenefitClass ON rbSocStatusClassTypeAssoc.class_id = BenefitClass.id
            AND BenefitClass.group_id = rbSocStatusClass.id
        LEFT JOIN ClientWork ON ClientWork.client_id = Client.id AND ClientWork.deleted = 0
        LEFT JOIN ClientWork_Hurt ON ClientWork_Hurt.master_id = ClientWork.id
        LEFT JOIN ClientRiskFactor ON ClientRiskFactor.client_id = Client.id
            AND ClientRiskFactor.deleted = 0
            AND DATE(ClientRiskFactor.begDate) <= DATE({endDate})
            AND (
                ClientRiskFactor.endDate IS NULL
                OR DATE(ClientRiskFactor.endDate) >= DATE({begDate})
            )
        LEFT JOIN Diagnosis ON Diagnosis.client_id = Client.id AND Diagnosis.deleted = 0
        LEFT JOIN rbRiskFactor ON ClientRiskFactor.riskFactor_id = rbRiskFactor.id
        LEFT JOIN rbRiskFactor_Identification ON rbRiskFactor_Identification.master_id = rbRiskFactor.id
            AND rbRiskFactor_Identification.deleted = 0
            AND rbRiskFactor_Identification.system_id = {accountingSystemId}
    WHERE
        Client.deleted = 0
        AND Client.sex != 0
        AND EXISTS(
            SELECT
                NULL
            FROM
                ClientAttach CA
                LEFT JOIN rbAttachType AT ON AT.id = CA.attachType_id
                LEFT JOIN rbFinance F ON F.id = AT.finance_id
            WHERE
                CA.client_id = Client.id
                AND CA.id = getClientAttachId(Client.id,0)
                AND CA.deleted = 0
                AND CA.orgStructure_id = {orgStructureId}
                AND (DATE(CA.endDate) > {endDate}
                OR CA.endDate is NULL)
                AND F.name like '%ОМС%'
        )
    '''
    return db.query(stmt.format(
            begDate=decorateString(begDate.toString(Qt.ISODate)),
            endDate=decorateString(endDate.toString(Qt.ISODate)),
            orgStructureId=orgStructureId if orgStructureId else 'NULL',
            accountingSystemId=accountingSystemId,
        ))



class CReportPassportT1000(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Т.1000')


    def getSetupDialog(self, parent):
        dialog = CReport.getSetupDialog(self, parent)
        dialog.setEventTypeVisible(False)
        dialog.setOnlyPermanentAttachVisible(False)
        dialog.setOrgStructureVisible(True)
        dialog.adjustSize()
        return dialog


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            (u'15%', [u'Состав прикрепленного к врачебному (терапевтическому) участку населения по возрасту, полу', u'', u''], CReportBase.AlignLeft),
            (u'4%', [u'№ строки', u'', u''], CReportBase.AlignCenter),
            (u'9%', [u'Всего (человек)', u'', u''], CReportBase.AlignRight),
            (u'9%', [u'Из них', u'Имеют льготную категорию', u'Федеральную'], CReportBase.AlignRight),
            (u'9%', [u'', u'', u'Субъекта Российской федерации'], CReportBase.AlignRight),
            (u'9%', [u'', u'', u'Муниципальную'], CReportBase.AlignRight),
            (u'9%', [u'', u'Инвалиды', u'Всего'], CReportBase.AlignRight),
            (u'9%', [u'', u'', u'1 группы'], CReportBase.AlignRight),
            (u'9%', [u'', u'', u'2 группы'], CReportBase.AlignRight),
            (u'9%', [u'', u'', u'3 группы'], CReportBase.AlignRight),
            (u'1.8%', [u'Место работы', u'Образование', u''], CReportBase.AlignRight),
            (u'1.8%', [u'', u'Здравоохранение', u''], CReportBase.AlignRight),
            (u'1.8%', [u'', u'Организации отдыха и культуры', u''], CReportBase.AlignRight),
            (u'1.8%', [u'', u'Научно-исследовательские учреждения', u''], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0,0, 3,1)
        table.mergeCells(0,1, 3,1)
        table.mergeCells(0,2, 3,1)
        table.mergeCells(0,3, 1,7)
        table.mergeCells(1,3, 1,3)
        table.mergeCells(1,6, 1,4)
        table.mergeCells(0,10, 1,4)
        table.mergeCells(1,10, 2,1)
        table.mergeCells(1,11, 2,1)
        table.mergeCells(1,12, 2,1)
        table.mergeCells(1,13, 2,1)

        reportDataKeys = (
            'adults',
            'able',
            'seniors',
            'working',
            'notworking',
            'pensioner',
            'workhurt',
            'alcohol',
            'smoking',
            'drugs',
            'tuberculosis',
            'neoplasm',
            'diabetes',
            'kardio',
            'muscul',
        )
        reportDataRowText = (
            u'Взрослое население (18 лет и старше)',
            u'В том числе трудоспособного возраста',
            u'60 лет и старше',
            u'Работающие',
            u'Неработающие',
            u'Пенсионеры',
            u'Число лиц, имеющих производственную вредность',
            u'Алкоголем - всего',
            u'Курением - всего',
            u'Наркотиками - всего',
            u'Туберкулез - всего',
            u'Злокачественное новообразование - всего',
            u'Сахарный диабет - всего',
            u'Сердечно-сосудистой системы - всего',
            u'Опорно-двигательного аппарата - всего',
        )

        reportData = {}
        for key in reportDataKeys:
            reportData[key] = [set() for i in xrange(12)]
            reportData[key + 'Male'] = [set() for i in xrange(12)]
            reportData[key + 'Female'] = [set() for i in xrange(12)]

        query = selectData(params)
        while query.next():
            record = query.record()
            clientId = forceInt(record.value('id'))
            age = forceInt(record.value('age'))
            sex = forceInt(record.value('sex'))
            MKB = forceString(record.value('MKB'))
            className = forceString(record.value('className')).lower()
            benefitName = forceString(record.value('benefitName')).lower()
            typeCode = forceString(record.value('typeCode'))
            isWorking = forceInt(record.value('isWorking'))
            hasWorkHurt = forceInt(record.value('hasWorkHurt'))
            riskFactorName = forceString(record.value('riskFactorName')).lower()
            clientOkved = forceString(record.value('clientOkved'))
            orgOkved = forceString(record.value('orgOkved'))
            okved = orgOkved or clientOkved

            keys = []
            if age >= 18:
                keys.append('adults')
                if sex == 1:
                    keys.append('adultsMale')
                else:
                    keys.append('adultsFemale')
            if sex == 1 and 16 <= age < 65:
                if 'able' not in keys:
                    keys.append('able')
                keys.append('ableMale')
            if sex == 2 and 16 <= age < 60:
                if 'able' not in keys:
                    keys.append('able')
                keys.append('ableFemale')
            if age >= 60:
                keys.append('seniors')
                if sex == 1:
                    keys.append('seniorsMale')
                else:
                    keys.append('seniorsFemale')

            if isWorking:
                keys.append('working')
                if sex == 1:
                    keys.append('workingMale')
                else:
                    keys.append('workingFemale')
            else:
                keys.append('notworking')
                if sex == 1:
                    keys.append('notworkingMale')
                else:
                    keys.append('notworkingFemale')

            if typeCode == u'с07':  # пенсионер
                keys.append('pensioner')
                if sex == 1:
                    keys.append('pensionerMale')
                else:
                    keys.append('pensionerFemale')

            if hasWorkHurt:
                keys.append('workhurt')
                if sex == 1:
                    keys.append('workhurtMale')
                else:
                    keys.append('workhurtFemale')

            if riskFactorName == u'курение':
                keys.append('smoking')
                if sex == 1:
                    keys.append('smokingMale')
                else:
                    keys.append('smokingFemale')
            if riskFactorName == u'алкоголь':
                keys.append('alcohol')
                if sex == 1:
                    keys.append('alcoholMale')
                else:
                    keys.append('alcoholFemale')
            if riskFactorName == u'наркотики':
                keys.append('drugs')
                if sex == 1:
                    keys.append('drugsMale')
                else:
                    keys.append('drugsFemale')

            if 'A15' <= MKB[:3] <= 'A19':
                keys.append('tuberculosis')
                if sex == 1:
                    keys.append('tuberculosisMale')
                else:
                    keys.append('tuberculosisFemale')
            if MKB.startswith('C'):
                keys.append('neoplasm')
                if sex == 1:
                    keys.append('neoplasmMale')
                else:
                    keys.append('neoplasmFemale')
            if 'E10' <= MKB[:3] <= 'E14':
                keys.append('diabetes')
                if sex == 1:
                    keys.append('diabetesMale')
                else:
                    keys.append('diabetesFemale')
            if MKB.startswith('I'):
                keys.append('kardio')
                if sex == 1:
                    keys.append('kardioMale')
                else:
                    keys.append('kardioFemale')
            if MKB.startswith('M'):
                keys.append('muscul')
                if sex == 1:
                    keys.append('musculMale')
                else:
                    keys.append('musculFemale')


            for key in keys:
                reportLine = reportData[key]
                reportLine[0].add(clientId)


                if className == u'федеральный':
                    reportLine[1].add(clientId)
                if className == u'субъект рф':
                    reportLine[2].add(clientId)
                if className == u'муниципальный':
                    reportLine[3].add(clientId)

                if typeCode == '081':  # инвалид I
                    reportLine[4].add(clientId)
                    reportLine[5].add(clientId)
                if typeCode == '082':  # инвалид II
                    reportLine[4].add(clientId)
                    reportLine[6].add(clientId)
                if typeCode == '083':  # инвалид III
                    reportLine[4].add(clientId)
                    reportLine[7].add(clientId)

                if okved.startswith('M80'):
                    reportLine[8].add(clientId)
                elif 'N85.10' <= okved[:6] <= 'N85.14':
                    reportLine[9].add(clientId)
                elif okved.startswith('O92'):
                    reportLine[10].add(clientId)
                elif okved.startswith('K73'):
                    reportLine[11].add(clientId)

        # убрать из неработающих тех, кто уже есть в работающих
        for keysex in ('', 'Male', 'Female'):
            working = reportData['working' + keysex]
            notworking = reportData['notworking' + keysex]
            for i in xrange(len(working)):
                notworking[i] -= working[i]

        rownum = 1
        for i in xrange(len(reportDataKeys)):
            if reportDataKeys[i] == 'alcohol':
                row = table.addRow()
                table.setText(row, 0, u'Относятся к группам риска и злоупотребляют:')
            elif reportDataKeys[i] == 'tuberculosis':
                row = table.addRow()
                table.setText(row, 0, u'Число лиц, имеющих заболевания:')
            rownum = self.addLine(table, reportData, reportDataKeys[i], reportDataRowText[i], rownum)
        return doc


    def addLine(self, table, reportData, key, text, rownum=0):
        reportLine = reportData[key]
        reportLineMale = reportData[key + 'Male']
        reportLineFemale = reportData[key + 'Female']

        row = table.addRow()
        rowMale = table.addRow()
        rowFemale = table.addRow()

        table.setText(row, 0, text)
        table.setText(row, 1, rownum)
        for i, clientSet in enumerate(reportLine):
            if i == 4:  # Инвалиды - Всего
                table.setText(row, 2+i,
                    len(reportLine[i+1]) + len(reportLine[i+2]) + len(reportLine[i+3]))
            else:
                table.setText(row, 2+i, len(clientSet))

        table.setText(rowMale, 0, u'Мужчины')
        table.setText(rowMale, 1, rownum+1)
        for i, clientSet in enumerate(reportLineMale):
            if i == 4:  # Инвалиды - Всего
                table.setText(rowMale, 2+i,
                    len(reportLineMale[i+1]) + len(reportLineMale[i+2]) + len(reportLineMale[i+3]))
            else:
                table.setText(rowMale, 2+i, len(clientSet))

        table.setText(rowFemale, 0, u'Женщины')
        table.setText(rowFemale, 1, rownum+2)
        for i, clientSet in enumerate(reportLineFemale):
            if i == 4:  # Инвалиды - Всего
                table.setText(rowFemale, 2+i,
                    len(reportLineFemale[i+1]) + len(reportLineFemale[i+2]) + len(reportLineFemale[i+3]))
            else:
                table.setText(rowFemale, 2+i, len(clientSet))

        return rownum + 3
