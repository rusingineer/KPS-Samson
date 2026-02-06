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
from PyQt4.QtCore import QDate

from library.DialogBase import CDialogBase
from library.Utils import forceRef, forceString
from Surveillance.Ui_GroupChangeDispanserPerson import Ui_ChangeDispanserPerson


class CGroupChangeDispanserPerson(CDialogBase, Ui_ChangeDispanserPerson):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.MKB = []


    def checkDataEntered(self):
        result = True
        personId = forceRef(self.cmbPerson.value())
        result = result and (personId or self.checkInputMessage(u'врача по диспансерному учету', True, self.cmbPerson))
        return result
    
    
    def getPersonId(self):
        return self.cmbPerson.value()
    
    
    def setClientCount(self, count):
        self.lblClientCount.setText(u'Кол-во пациентов, у которых будет изменен врач по ДН: {}'.format(forceString(count)))
    
    
    def setMKBList(self, MKBFrom, MKBTo, active):
        self.lblMKBList.setText(u'Диапазон диагнозов: {}'.format(MKBFrom + ' - ' + MKBTo if active else u'не задано'))
    
    
    def setCharacterList(self, character):
        self.lblCharacterList.setText(u'Характеры заболеваний: {}'.format(character))
    
    
    def setMKB(self, active, diagnosisIdList=[]):
        self.lblMKB.setVisible(active)
        self.cmbMKB.setVisible(active)
        if active and diagnosisIdList:
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            records = db.getRecordList(tableDiagnosis, [tableDiagnosis['id'], tableDiagnosis['MKB']], tableDiagnosis['id'].inlist(diagnosisIdList))
            for record in records:
                MKB = forceString(record.value('MKB'))
                if MKB not in self.MKB:
                    self.cmbMKB.addList([[MKB, forceString(record.value('id')), MKB, 2]])
                    self.MKB.append(MKB)
    
    
    def getMKB(self):
        return self.cmbMKB.checkedValueList()
    
    
    def getDiagnosisIdList(self, masterIdList, filter):
        diagnosisIdList = []
        if masterIdList:
            date = filter.get('begDate', QDate.currentDate())
            if not date:
                date = QDate.currentDate()
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableRBDispanser = db.table('rbDispanser')
            cond = [tableDiagnosis['client_id'].inlist(masterIdList),
                    tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    db.joinOr([db.joinAnd([tableDiagnostic['endDate'].isNotNull(), tableDiagnostic['endDate'].le(date)]),
                               db.joinAnd([tableDiagnostic['endDate'].isNull(), tableDiagnostic['setDate'].le(date)])]),
                    tableRBDispanser['observed'].eq(1)
                    ]
            queryTable = tableDiagnosis.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            queryTable = queryTable.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            cond, queryTable = diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic)
            cond.append(u'''NOT EXISTS(SELECT DC.id
                                   FROM Diagnostic AS DC
                                   INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                   INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                   WHERE DC.diagnosis_id = Diagnosis.id AND DC.endDate <= {} AND DC.deleted = 0 AND rbDP.name LIKE '{}')
                            OR EXISTS(SELECT DC.id
                                   FROM Diagnostic AS DC
                                   INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                   INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                   WHERE DC.diagnosis_id = Diagnosis.id AND DC.endDate <= {} AND DC.deleted = 0 AND rbDP.name LIKE '{}')'''.format(db.formatDate(date), u'%снят%', db.formatDate(date), u'%взят повторно%'))
            diagnosisIdList = db.getDistinctIdList(queryTable, [u'Diagnosis.id'], where=cond, order='Diagnostic.endDate DESC')
        return diagnosisIdList
    

def diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic):
    MKBFilter = filter.get('MKBFilter', 0)
    if MKBFilter:
        MKBFrom = filter.get('MKBFrom', None)
        MKBTo   = filter.get('MKBTo', None)
        cond.append(isSurveillanceMKB(MKBFrom, MKBTo))
    diseaseCharacterId = filter.get('diseaseCharacterId', None)
    if diseaseCharacterId:
        cond.append(tableDiagnosis['character_id'].eq(diseaseCharacterId))
    personDN = filter.get('personDN')
    if personDN:
        cond.append(tableDiagnosis['dispanserPerson_id'].eq(personDN))
    orgStructureId = filter.get('orgStructureId', None)
    specialityIdListAsString = filter.get('specialityId', None)
    if orgStructureId or specialityIdListAsString:
        tablePerson = db.table('Person')
        queryTable = queryTable.innerJoin(tablePerson, tablePerson['id'].eq(tableDiagnosis['dispanserPerson_id']))
        cond.append(tablePerson['deleted'].eq(0))
    if orgStructureId:
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
        if orgStructureIdList:
            cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
    if specialityIdListAsString:
        cond.append('Person.speciality_id IN ({})'.format(specialityIdListAsString))
    return cond, queryTable


def isSurveillanceMKB(MKBFrom, MKBTo):
    return '''Diagnosis.MKB >= '{}' AND Diagnosis.MKB <= '{}' '''.format(MKBFrom, MKBTo)