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
##
## Форма 106: свидетельство о смерти
##
#############################################################################

from PyQt4 import QtGui

from library.DialogBase import CDialogBase
from library.InDocTable import CInDocTableModel, CDateInDocTableCol, CInDocTableCol

from F106.Ui_DiagnosisSelectionDialog import Ui_DiagnosisSelectionDialog

class CDiagnosisSelectionModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Diagnosis', None, None, parent)
        self.addCol(CInDocTableCol(u'МКБ', 'MKB', 10).setReadOnly())
        self.addCol(CInDocTableCol(u'Врач', 'name', 10).setReadOnly())
        self.addCol(CDateInDocTableCol(u'Дата', 'date', 10).setReadOnly())
        self.addCol(CInDocTableCol(u'Результат', 'resultName', 10).setReadOnly())
        self.setEnableAppendLine(False)


class CDiagnosisSelectionDialog(CDialogBase, Ui_DiagnosisSelectionDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.addModels('Diagnosises', CDiagnosisSelectionModel(self))
        self.setModels(self.tblDiagnosises, self.modelDiagnosises, self.selectionModelDiagnosises)
        self.MKBrecord = None
        

    def findDiagnosis(self, clientId):
        db = QtGui.qApp.db
        tableDiagnostic = db.table('Diagnostic')
        tableEvent = db.table('Event')
        tableDiagnosis = db.table('Diagnosis')
        tableRbResult = db.table('rbResult')
        tablePerson = db.table('vrbPerson')
        tableRbDiagnosisType = db.table('rbDiagnosisType')
        table = tableDiagnostic.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
        table = table.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        table = table.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        table = table.leftJoin(tableRbResult, tableRbResult['id'].eq(tableEvent['result_id']))
        table = table.leftJoin(tableRbDiagnosisType, tableRbDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id']))
        
        cond = [tableEvent['client_id'].eq(clientId), 
                    tableDiagnostic['deleted'].eq(0), 
                    tableEvent['execDate'].isNotNull(), 
                    tableRbDiagnosisType['code'].inlist([1, 4, 8])]
        
        cols = [tableDiagnosis['MKB'], 
                    tableDiagnosis['MKBEx'], 
                    tableDiagnostic['traumaType_id'], 
                    tableDiagnostic['character_id'], 
                    tableDiagnostic['phase_id'], 
                    tableDiagnostic['stage_id'], 
                    tablePerson['name'], 
                    tableEvent['execDate'].alias('date'), 
                    tableRbResult['name'].alias('resultName'), 
                    db.if_(db.joinOr([tableRbResult['name'].like(u'смерть'), tableRbResult['name'].like(u'умер')]), 
                            '1', '0') + ' as death'
                    ]
        
        order = 'death DESC,date DESC'
        
        recordList = db.getRecordList(table, cols, cond, order)
        if recordList:
            self.modelDiagnosises.setItems(recordList)
            self.tblDiagnosises.setCurrentIndex(self.modelDiagnosises.index(0, 0))
            return True
        return False
        

    def getDiagnosis(self):
        if not self.MKBrecord:
            index = self.selectionModelDiagnosises.currentIndex()
            if index:
                record = self.modelDiagnosises.items()[index.row()]
                self.MKBrecord = record
        return self.MKBrecord
        

    def saveData(self):
        index = self.selectionModelDiagnosises.currentIndex()
        record = self.modelDiagnosises.items()[index.row()]
        self.MKBrecord = record
        return True
