# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import QVariant, QDate

from library.DialogBase import CDialogBase
from library.ICDInDocTableCol import CICDExInDocTableCol
from library.InDocTable import CInDocTableModel, CRBInDocTableCol, CDateInDocTableCol, CBoolInDocTableCol, CEnumInDocTableCol
from library.Utils import forceBool, forceRef, forceString, toVariant, forceDate
from Registry.Utils import createDiagnosticRecords

from Surveillance.Ui_SurveillanceRemoveAcute import Ui_SurveillanceRemoveAcute


class CSurveillanceRemoveAcute(CDialogBase, Ui_SurveillanceRemoveAcute):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.addModels('Diagnosis', CDiagnosisModel(self))
        self.setModels(self.tblDiagnosis, self.modelDiagnosis, self.selectionModelDiagnosis)
        self.modelDiagnosis.setEnableAppendLine(False)
        self.cmbDispanser.setTable('rbDispanser', False, filter=u'rbDispanser.observed = 0')
        self.clientId = None
    
    
    def saveData(self):
        if self.cmbDispanser.value():
            return self.modelDiagnosis.saveItems(self.clientId, self.cmbDispanser.value(), self)
        else:
            self.checkValueMessage(u'Необходимо выбрать текущий статус ДН',
                                   False, 
                                   self.cmbDispanser)
            return False
    
    
    def setClient(self, clientId):
        self.clientId = clientId
        return self.modelDiagnosis.loadItems(self.clientId)


class CDiagnosisModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Diagnosis', 'id', 'client_id', parent)
        self.addExtCol(CBoolInDocTableCol(u'', 'checking', 20), QVariant.Bool)
        self.addCol(CICDExInDocTableCol(u'МКБ', 'MKB', 6)).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Дата взятия на ДН', 'dispanserBegDate', 12)).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Статус ДН', 'dispanser_id', 15, 'rbDispanser')).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Врач ДН', 'dispanserPerson_id', 6, 'vrbPersonWithSpecialityAndOrgStr')).setReadOnly(True)
        self.addCol(CEnumInDocTableCol(u'Характер', 'character_id', 15, [u'Фактор', u'Острое'])).setReadOnly(True)
        self.addHiddenCol('client_id')
        self.addHiddenCol('id')


    def loadItems(self, masterId):
        diagnosisRecordList = anyAcute(masterId)
        if not diagnosisRecordList:
            return False
        self._items = diagnosisRecordList
        self.reset()
        return True
    
    
    def saveItems(self, clientId, newDispanser, dialog):
        db = QtGui.qApp.db
        diagnosisRecordList = []
        MKBlist = []
        tableDiagnosis = db.table('Diagnosis')
        for item in self._items:
            if forceBool(item.value('checking')):
                diagnosisRecordList.append(item)
                MKB = forceString(item.value('MKB'))
                if MKB not in MKBlist:
                    MKBlist.append(MKB)
        if diagnosisRecordList:
            message = u'Будет произведено снятие пациента с диагнозов [{}]\nВнесенные изменения отменить невозможно. Продолжить?'''.format(', '.join(MKBlist))
            if QtGui.QMessageBox.question(dialog,
                                    u'Внимание!',
                                    message,
                                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                    QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                idList = []
                for item in diagnosisRecordList:
                    idList.append(forceRef(item.value('id')))
                if idList:
                    updateCols = [
                        tableDiagnosis['endDate'].eq(forceDate(QDate.currentDate())),
                        tableDiagnosis['dispanser_id'].eq(newDispanser),
                        tableDiagnosis['person_id'].eq(QtGui.qApp.userId),
                    ]
                    updateCond = [
                        tableDiagnosis['id'].inlist(idList),
                        tableDiagnosis['deleted'].eq(0),
                        ]
                    db.updateRecords(tableDiagnosis, updateCols, updateCond)
                    createDiagnosticRecords(diagnosisRecordList, clientId=clientId, removeDispanserId=newDispanser, removeDate=QDate.currentDate())
                return True
            else:
                return False
        else:
            dialog.checkValueMessage(u'Не выбран ни один диагноз',
                                   False, 
                                   dialog.tblDiagnosis)
            return False
    

def anyAcute(masterId):
    if masterId:
        db = QtGui.qApp.db
        tableDiagnosis = db.table('Diagnosis')
        tableRBDispanser = db.table('rbDispanser')
        tableDiagnosisType = db.table('rbDiagnosisType')
        cols = [
            'FALSE as checking',
            tableDiagnosis['MKB'],
            tableDiagnosis['dispanserBegDate'],
            tableDiagnosis['dispanser_id'],
            tableDiagnosis['dispanserPerson_id'],
            tableDiagnosis['character_id'],
            tableDiagnosis['client_id'],
            tableDiagnosis['id'],
        ]
        cond = [tableDiagnosis['client_id'].eq(masterId),
                tableDiagnosis['deleted'].eq(0),
                tableRBDispanser['observed'].eq(1),
                db.joinOr([db.joinAnd([tableDiagnosis['character_id'].isNull(), tableDiagnosisType['name'].like(u'%фактор%')]), tableDiagnosis['character_id'].eq(1)])
                ]
        queryTable = tableDiagnosis.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnosis['dispanser_id']))
        queryTable = queryTable.innerJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(tableDiagnosis['diagnosisType_id']))
        return db.getDistinctRecordList(queryTable, cols, where=cond, order='Diagnosis.endDate DESC')
    return []