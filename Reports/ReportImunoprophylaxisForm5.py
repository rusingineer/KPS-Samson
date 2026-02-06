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
from PyQt4.QtCore import QDate

from library.Utils             import forceInt, forceString
from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable
from library.DialogBase        import CDialogBase
from Ui_ReportImunoprophylaxisForm5SetupDialog import Ui_CReportImunoprophylaxisForm5SetupDialog


def selectData(params):
    begDate = params.get('begDate')
    endDate = params.get('endDate')
    personId = params.get('personId')

    db = QtGui.qApp.db

    tableClientVaccination = db.table('ClientVaccination')
    tableVaccine = db.table('rbVaccine')
    tableInfectionVaccine = db.table('rbInfection_rbVaccine')
    tableInfection = db.table('rbInfection')
    tableClient = db.table('Client')

    queryTable = tableClientVaccination
    queryTable = queryTable.leftJoin(tableVaccine, tableVaccine['id'].eq(tableClientVaccination['vaccine_id']))
    queryTable = queryTable.leftJoin(tableInfectionVaccine, tableInfectionVaccine['vaccine_id'].eq(tableVaccine['id']))
    queryTable = queryTable.leftJoin(tableInfection, tableInfection['id'].eq(tableInfectionVaccine['infection_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableClientVaccination['client_id']))

    cond = []
    if begDate:
        cond.append(tableClientVaccination['datetime'].ge(begDate))
    if endDate:
        cond.append(tableClientVaccination['datetime'].lt(endDate.addDays(1)))
    if personId:
        cond.append(tableClientVaccination['person_id'].eq(personId))

    fields = [tableClient['id'].alias('clientId'),
              'age(Client.`birthDate`, DATE(ClientVaccination.`datetime`)) AS clientAge',
              tableClientVaccination['vaccinationType'],
              tableInfection['code'].alias('infectionCode'),
              tableInfection['name']]

    stmt = db.selectStmtGroupBy(queryTable, fields, cond, u'clientId, name')
    return db.query(stmt)


class CReportImunoprophylaxisForm5(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сведения о профилактических прививках')
        # key -> (rbInfection.code, isRevaccination), value -> reportRow
        self._mapInfectionCode2row = {(u'дифтерия', False) : 2,
                                      (u'дифтерия', True)  : 4,
                                      (u'вирусный гепатит в', False) : 25,
                                      (u'пневмококковая инфекция', False)  : 52,
                                      (u'пневмококковая инфекция', True) : 54,
                                      (u'коклюш', False) : 0,
                                      (u'коклюш', True) : 1,
                                      (u'туберкулез', False) : 23,
                                      (u'туберкулёз', False) : 23,
                                      (u'столбняк', False) : 6,
                                      (u'столбняк', True) : 8,
                                      (u'гемофильная инфекция', False) : 48,
                                      (u'гемофильная инфекция', True) : 49,
                                      (u'полиомиелит', False) : 10,
                                      (u'полиомиелит', True)  : 11,
                                      (u'корь', False) : 12,
                                      (u'корь', True) : 14,
                                      (u'эпидемический паротит', False)  : 16,
                                      (u'эпидемический паротит', True) : 17,
                                      (u'паротит эпидемический', False)  : 16,
                                      (u'паротит эпидемический', True) : 17,
                                      (u'краснуха', False) : 18,
                                      (u'краснуха', True)  : 20,
                                      (u'бешенство', False) : 57,
                                      (u'бешенство', True)  : 58,
                                      (u'ветряная оспа', False) : 50,
                                      (u'вирусный гепатит а', False) : 27,
                                      (u'менингококковая инфекция', False) : 46,
                                      (u'ротавирус', False) : 61,
                                      (u'зонне', False) : 60,
                                      (u'грипп', False)  : 39,
                                      (u'бруцеллез', False) : 33,
                                      (u'бруцеллез', True)  : 34,
                                      (u'клещевой энцефалит', False) : 41,
                                      (u'клещевой энцефалит', True)  : 43,
                                      (u'брюшной тиф', False) : 22,
                                      (u'сибирская язва', False) : 35,
                                      (u'сибирская язва', True)  : 36,
                                      (u'туляремия', False) : 29,
                                      (u'туляремия', True)  : 31,
                                      (u'желтая лихорадка', False) : 38,
                                      (u'лептоспироз', False) : 45,
                                      (u'covid', False) : 62,
                                      (u'лихорадка ку', False) : 59,
                                      (u'ку-лихорадка', False) : 59,
                                      (u'чума', False) : 37,
                                      (u'вирус папиломы человека', False) : 56}
        self._rowsWithChildren = [2, 4, 6, 8, 12, 14, 18, 20, 23, 25, 27, 29, 31, 39, 41, 43, 46, 50, 52, 54]


    def getSetupDialog(self, parent):
        result = CReportImunoprophylaxisForm5SetupDialog(parent)
        result.setTitle(self.title())
        return result


    def _applyDefaults(self):
        rows  = [[u'Вакцинация против коклюша'], # 0
                 [u'Ревакцинация против коклюша'], # 1
                 [u'Вакцинация против дифтерии - всего'], # 2
                 [u'в том числе детей'], # 3
                 [u'Ревакцинация против дифтерии - всего'], # 4
                 [u'в том числе детей'], # 5
                 [u'Вакцинация против столбняка - всего'], # 6
                 [u'в том числе детей'], # 7
                 [u'Ревакцинация против столбняка - всего'], # 8
                 [u'в том числе детей'], # 9
                 [u'Вакцинация против полиомиелита'], # 10
                 [u'Ревакцинация против полиомиелита'], # 11
                 [u'Вакцинация против кори - всего'], # 12
                 [u'в том числе детей'], # 13
                 [u'Ревакцинация против кори - всего'], # 14
                 [u'в том числе детей'], # 15
                 [u'Вакцинация против эпидемического паротита'], # 16
                 [u'Ревакцинация против эпидемического паротита'], # 17
                 [u'Вакцинация против краснухи - всего'], # 18
                 [u'в том числе детей'], # 19 
                 [u'Ревакцинация против краснухи - всего'], # 20
                 [u'в том числе детей'], # 21
                 [u'Прививки против брюшного тифа'], # 22
                 [u'Прививки против туберкулеза - всего'], # 23
                 [u'в том числе новорожденным'], # 24
                 [u'Вакцинация против вирусного гепатита В - всего'], # 25
                 [u'в том числе детей'], # 26
                 [u'Прививки против вирусного гепатита А - всего'], # 27
                 [u'в том числе детей'], # 28
                 [u'Вакцинация против туляремии - всего'], # 29
                 [u'в том числе детей'], # 30
                 [u'Ревакцинация против туляремии - всего'], # 31
                 [u'в том числе детей'], # 32
                 [u'Вакцинация против бруцеллеза'], # 33
                 [u'Ревакцинация против бруцеллеза'], # 34
                 [u'Вакцинация против сибирской язвы'], # 35
                 [u'Ревакцинация против сибирской язвы'], # 36
                 [u'Прививки против чумы'], # 37
                 [u'Прививки против желтой лихорадки'], # 38
                 [u'Прививки против гриппа - всего'], # 39
                 [u'в том числе детям'], # 40
                 [u'Вакцинация против клещевого энцефалита - всего'], # 41
                 [u'в том числе детей'], # 42
                 [u'Ревакцинация против клещевого энцефалита - всего'], # 43
                 [u'в том числе детей'], # 44
                 [u'Прививки против лептоспироза'], # 45
                 [u'Прививки против менингококковой инфекции - всего'], # 46
                 [u'в том числе детей'], # 47
                 [u'Вакцинация против гемофильной инфекции'], # 48
                 [u'Ревакцинация против гемофильной инфекции'], # 49
                 [u'Прививки против ветряной оспы - всего'], # 50
                 [u'в том числе детей'], # 51
                 [u'Вакцинация против пневмококковой инфекции - всего'], # 52
                 [u'в том числе детей'], # 53
                 [u'Ревакцинация против пневмококковой инфекции - всего'], # 54
                 [u'в том числе детей'], # 55
                 [u'Прививки против вируса папилломы человека'], # 56
                 [u'Вакцинация против бешенства'], # 57
                 [u'Ревакцинация против бешенства'], # 58
                 [u'Прививки против лихорадки Ку'], # 59
                 [u'Прививки против дизентерии Зонне'], # 60
                 [u'Вакцинация против ротавирусной инфекции'],  #61
                 [u'Прививки против Covid 19']] # 62
        for idx, row in enumerate(rows):
            row.append(str(idx+1).zfill(2))
            row.append(0)

        return rows


    def getReportData(self, query):

        reportData = self._applyDefaults()
        
        while query.next():

            record = query.record()

            vaccinationType = forceString(record.value('vaccinationType'))
            names = forceString(record.value('name')).split(',')
            for name in names:
                row = None
                for key, value in self._mapInfectionCode2row.items():
                    if key[0] in name.lower() and ((vaccinationType[:1]=='R' and key[1] == True) or (vaccinationType[:1] !='R' and key[1] == False)):
                        row = value
                if row is not None:
                    reportData[row][2] += 1
                    if row in self._rowsWithChildren:
                        if forceInt(record.value('clientAge')) < 18:
                            reportData[row+1][2] += 1

        return reportData


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [( '60%', [u'Наименование'], CReportBase.AlignLeft),
                        ( '10%', [u'№ строки'], CReportBase.AlignRight),
                        ( '30%', [u'Число привитых лиц'], CReportBase.AlignRight)]

        table = createTable(cursor, tableColumns)

        query = selectData(params)

        reportData = self.getReportData(query)

        for reportLine in reportData:
            i = table.addRow()

            for idx, value in enumerate(reportLine):
                table.setText(i, idx, value)

        return doc



class CReportImunoprophylaxisForm5SetupDialog(CDialogBase, Ui_CReportImunoprophylaxisForm5SetupDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)


    def setTitle(self, title):
        self.setWindowTitleEx(title)


    def setParams(self, params):
        currentDate = QDate.currentDate()
        self.edtBegDate.setDate(params.get('begDate', QDate(currentDate.year(), 1, 1)))
        self.edtEndDate.setDate(params.get('endDate', currentDate))
        self.cmbPerson.setValue(params.get('personId', None))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['personId'] = self.cmbPerson.value()
        return result

