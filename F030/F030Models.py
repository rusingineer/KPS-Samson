# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
from Registry.Utils import getClientPhone
from library.database import CSqlRecord, CTableRecordCache
from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QModelIndex, QObject, QVariant, SIGNAL, QDate


from library.crbcombobox import CRBComboBox
from library.ICDInDocTableCol import CICDExInDocTableCol
from library.ICDMorphologyInDocTableCol import CMKBMorphologyCol
from library.InDocTable import CBoolInDocTableCol, CDateInDocTableCol, CInDocTableCol, CInDocTableModel, CMKBListInDocTableModel, CRBInDocTableCol, CRBLikeEnumInDocTableCol, CEnumInDocTableCol
from library.TNMS.TNMSComboBox import CTNMSCol
from library.MKBExSubclassComboBox import CMKBExSubclassCol
from library.Utils import firstMonthDay, forceBool, forceDate, forceInt, forceRef, forceString, toVariant, variantEq, forceStringEx

from Events.DiagnosisType import CDiagnosisTypeCol
from Events.EventEditDialog import CEventEditDialog, CDiseaseCharacter, CDiseaseStage, CDiseasePhases, CToxicSubstances, getToxicSubstancesIdListByMKB
from Events.EventInfo import CHospitalInfo
from Events.Utils import getAvailableCharacterIdByMKB, getDiagnosticResultIdList, mkbIsVIMIS, checkAttachOnDate
from Orgs.PersonComboBoxEx import CPersonFindInDocTableCol

class CF030BaseDiagnosticsModel(CMKBListInDocTableModel):
    __pyqtSignals__ = ('diagnosisChanged(QString)',
                      )
    MKB_allowed_morphology = ['C', 'D']

    def __init__(self, parent, finishDiagnosisTypeCode, baseDiagnosisTypeCode, accompDiagnosisTypeCode, complicDiagnosisTypeCode):
        CMKBListInDocTableModel.__init__(self, 'Diagnostic', 'id', 'event_id', parent)
        self._parent = parent
        self.isManualSwitchDiagnosis = QtGui.qApp.defaultIsManualSwitchDiagnosis()
        self.isMKBMorphology = QtGui.qApp.defaultMorphologyMKBIsVisible()
        self.characterIdForHandleDiagnosis = None
        self.diagnosisTypeCol = CF030DiagnosisTypeCol( u'Тип', 'diagnosisType_id', 2, [finishDiagnosisTypeCode, baseDiagnosisTypeCode, accompDiagnosisTypeCode, complicDiagnosisTypeCode], smartMode=False)
        self.addCol(self.diagnosisTypeCol)
        self.addCol(CPersonFindInDocTableCol(u'Врач', 'person_id',  20, 'vrbPersonWithSpecialityAndOrgStr', parent=parent))
        self.addExtCol(CICDExInDocTableCol(u'МКБ', 'MKB', 7), QVariant.String)
        if QtGui.qApp.isExSubclassMKBVisible():
            self.addExtCol(CMKBExSubclassCol(u'РСК', 'exSubclassMKB', 10), QVariant.String).setToolTip(u'Расширенная субклассификация МКБ')
        self.addExtCol(CICDExInDocTableCol(u'Доп.МКБ', 'MKBEx', 7), QVariant.String)
        if QtGui.qApp.isTNMSVisible():
            self.addCol(CTNMSCol(u'TNM-Ст', 'TNMS', 10))
        if QtGui.qApp.isClinicalGroupDiagnosticVisible():
            self.addCol(CEnumInDocTableCol(u'КГ', 'clinicalGroup', 30, [u'', u'1а - подозрение', u'1б - предрак', u'2 - подлежат радикальному лечению', u'3 - ремиссия', u'4 - подлежат паллиативному лечению'])).setToolTip(u'Клиническая группа')
        if self.isMKBMorphology:
            self.addExtCol(CMKBMorphologyCol(u'Морф.', 'morphologyMKB', 10, 'MKB_Morphology', filter='`group` IS NOT NULL'), QVariant.String)
        self.addCol(CDiseaseCharacter(u'Хар', 'character_id',   7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Характер')
        if self.isManualSwitchDiagnosis:
            self.addExtCol(CBoolInDocTableCol( u'П', 'handleDiagnosis', 10), QVariant.Int)
            self.characterIdForHandleDiagnosis = forceRef(QtGui.qApp.db.translate('rbDiseaseCharacter', 'code', '1', 'id'))

        self.addCol(CDiseasePhases(u'Фаза', 'phase_id', 7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Фаза')
        self.addCol(CDiseaseStage(u'Ст', 'stage_id', 7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Стадия')
        self.addCol(CRBInDocTableCol(u'ДН', 'dispanser_id', 7, 'rbDispanser', showFields=CRBComboBox.showCode, preferredWidth=150, filter='code not in (2,6)')).setToolTip(u'Диспансерное наблюдение')
        self.addCol(CRBLikeEnumInDocTableCol(u'Госп', 'hospital', 7, CHospitalInfo.names, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Потребность в госпитализации')
        self.addCol(CInDocTableCol(u'Описание', 'freeInput', 15))
        self.columnHandleDiagnosis = self.getColIndex('handleDiagnosis', None)
        self.setFilter(self.table['diagnosisType_id'].inlist([id for id in self.diagnosisTypeCol.ids if id]))
        self.readOnly = False
        self.eventEditor = parent
        self.getDispanserIdLists()
        self.MKBs = []


    def getDispanserIdLists(self):
        db = QtGui.qApp.db
        self.observedDispanserIdList = db.getDistinctIdList('rbDispanser', 'id', ['observed = 1'])
        recordIdList = db.getDistinctIdList('rbDispanser', 'id', ['code = 2'])
        self.takenDispanserId = recordIdList[0] if len(recordIdList) > 0 else None
        self.takenDispanserIdList = db.getDistinctIdList('rbDispanser', 'id', ['code = 2 OR code = 6'])
        consistDispanserIdList = db.getDistinctIdList('rbDispanser', 'id', ['code = 1'])
        self.consistDispanserId = consistDispanserIdList[0] if len(consistDispanserIdList) > 0 else None


    def setReadOnly(self, value):
        self.readOnly = value


    def manualSwitchDiagnosis(self):
        return self.isManualSwitchDiagnosis


    def flags(self, index=QModelIndex()):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        result = CMKBListInDocTableModel.flags(self, index)
        row = index.row()
        if row < len(self._items):
            column = index.column()
            if self.isManualSwitchDiagnosis and index.isValid():
                if column == self.columnHandleDiagnosis:
                    characterId = forceRef(self.items()[row].value('character_id'))
                    if characterId != self.characterIdForHandleDiagnosis:
                        result = (result & ~Qt.ItemIsUserCheckable)
            if self.isMKBMorphology and index.isValid():
                if column == self.getColIndex('morphologyMKB'):
                    mkb = forceString(self.items()[row].value('MKB'))
                    if not (bool(mkb) and mkb[0] in CF030BaseDiagnosticsModel.MKB_allowed_morphology):
                        result = (result & ~Qt.ItemIsEditable)
            if QtGui.qApp.isExSubclassMKBVisible() and index.isValid():
                if column == self.getColIndex('exSubclassMKB'):
                    mkb = forceString(self.items()[row].value('MKB'))
                    if len(mkb) != 6:
                        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            if index.isValid():
                if column == self.getColIndex('MKBEx'):
                    mkb = forceString(self.items()[row].value('MKB'))
                    if not (bool(mkb) and mkb[0] in (u'S', u'T')):
                        return result & ~Qt.ItemIsEnabled
        return result


    def getEmptyRecord(self):
        eventEditor = QObject.parent(self)
        result = CMKBListInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('diagnosis_id', QVariant.Int))
        result.append(QtSql.QSqlField('speciality_id', QVariant.Int))
        result.append(QtSql.QSqlField('setDate', QVariant.DateTime))
        result.append(QtSql.QSqlField('endDate', QVariant.DateTime))
        result.append(QtSql.QSqlField('cTumor_id', QVariant.Int))
        result.append(QtSql.QSqlField('cNodus_id', QVariant.Int))
        result.append(QtSql.QSqlField('cMetastasis_id', QVariant.Int))
        result.append(QtSql.QSqlField('cTNMphase_id', QVariant.Int))
        result.append(QtSql.QSqlField('pTumor_id', QVariant.Int))
        result.append(QtSql.QSqlField('pNodus_id', QVariant.Int))
        result.append(QtSql.QSqlField('pMetastasis_id', QVariant.Int))
        result.append(QtSql.QSqlField('pTNMphase_id', QVariant.Int))
        result.setValue('person_id', toVariant(eventEditor.getSuggestedPersonId()))
        result.setValue('dispanser_id', toVariant(self.consistDispanserId))
        if self.items():
            result.setValue('diagnosisType_id',  toVariant(self.diagnosisTypeCol.ids[2]))
        else:
            result.setValue('diagnosisType_id',  toVariant(self.diagnosisTypeCol.ids[0] if self.diagnosisTypeCol.ids[0] else self.diagnosisTypeCol.ids[1]))
            result.setValue('result_id',  toVariant(eventEditor.defaultDiagnosticResultId if eventEditor.defaultDiagnosticResultId in getDiagnosticResultIdList(eventEditor.eventPurposeId, eventEditor.cmbResult.value()) else None))
        return result


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                if QtGui.qApp.isTNMSVisible() and 0 <= row < len(self.items()) and column == self.items()[row].indexOf('TNMS'):
                    col = self._cols[column]
                    record = self._items[row]
                    tnmsMap = {}
                    for keyName, fieldName in CEventEditDialog.TNMSFieldsDict.items():
                        tnmsMap[keyName] = forceRef(record.value(fieldName))
                    return QVariant([forceString(record.value(col.fieldName())), tnmsMap])
            if index.isValid() and role == Qt.BackgroundRole and QtGui.qApp.preferences.propertyColor and index.column() == 2:
                if mkbIsVIMIS(forceString(self.items()[row].value('MKB'))):
                    return QVariant(QtGui.QBrush(QtGui.QColor(QtGui.qApp.preferences.propertyColor)))
            if index.isValid() and role == Qt.BackgroundRole and column == self.getColIndex('MKBEx'):
                if not Qt.ItemIsEnabled & index.flags():
                    return QVariant(QtGui.QBrush(QtGui.QColor(226, 228, 230)))
        return CMKBListInDocTableModel.data(self, index, role)


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        if not variantEq(self.data(index, role), value):
            eventEditor = QObject.parent(self)
            if column == 0: # тип диагноза
                result = CMKBListInDocTableModel.setData(self, index, value, role)
                if result:
                    self.updateDiagnosisType(set([row]))
                    self.emitDiagnosisChanged()
                return result
            elif column == 1: # врач
                personId = forceRef(value)
                if not eventEditor.checkClientAttendanceEE(personId):
                    return False
                result = CMKBListInDocTableModel.setData(self, index, value, role)
                if result:
                    self.updateDiagnosisType(set())
                    self.emitDiagnosisChanged()
                return result
            elif column == 2: # код МКБ
                newMKB = forceString(value)
                if not newMKB:
                    specifiedMKB = ''
                    specifiedMKBEx = ''
                    specifiedCharacterId = None
                    specifiedTraumaTypeId = None
                    specifiedDispanserId = None
                    specifiedRequiresFillingDispanser = 0
                    specifiedProlongMKB = False
                else:
                    acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = eventEditor.specifyDiagnosis(newMKB)
                    if not acceptable:
                        return False
                value = toVariant(specifiedMKB)
                oldMKB = forceString(self.items()[row].value('MKB')) if 0 <= row < len(self.items()) else None
                result = CMKBListInDocTableModel.setData(self, index, value, role)
                if result:
                    if specifiedRequiresFillingDispanser == 2:
                        if forceString(QtGui.qApp.getGlobalPreference('controlPresenceDispInEventForAttachClient')) == u'да':
                            if checkAttachOnDate(eventEditor.clientId, eventEditor.edtBegDate.date()):
                                self.updateDispanserByMKB(row, specifiedDispanserId, specifiedProlongMKB)
                        else:
                            self.updateDispanserByMKB(row, specifiedDispanserId, specifiedProlongMKB)
                    self.updateCharacterByMKB(row, specifiedMKB, specifiedCharacterId)
                    self.updateTraumaType(row, specifiedMKB, specifiedTraumaTypeId)
                    self.updateClinicalGroup(row, oldMKB, specifiedMKB, eventEditor.itemId(), eventEditor.clientId, eventEditor.eventSetDateTime.date())
                    self.updateToxicSubstancesByMKB(row, specifiedMKB)
                    self.updateTNMS(index, self.items()[row], specifiedMKB)
                    self.updateMKBTNMS(self.items()[row], specifiedMKB)
                    self.inheritMKBTNMS(self.items()[row], oldMKB, specifiedMKB, eventEditor.clientId, eventEditor.eventSetDateTime)
                    self.updateExSubclass(index, self.items()[row], specifiedMKB)
                    self.updateMKBToExSubclass(self.items()[row], specifiedMKB)
                    self.emitDiagnosisChanged(specifiedMKB)
                return result
            if 0 <= row < len(self.items()) and column == self.items()[row].indexOf('MKBEx'): # доп. код МКБ
                newMKB = forceString(value)
                if not newMKB:
                    pass
                else:
                    acceptable = eventEditor.checkDiagnosis(newMKB)
                    if not acceptable:
                        return False
                value = toVariant(newMKB)
                result = CMKBListInDocTableModel.setData(self, index, value, role)

                self.emitDiagnosisChanged(newMKB)
                return result
            elif row == len(self.items()) and column == self.getColIndex('MKBEx'):
                return False
            if QtGui.qApp.isTNMSVisible() and 0 <= row < len(self.items()) and column == self.items()[row].indexOf('TNMS'):
                record = self.items()[row]
                self.updateMKBTNMS(record, forceString(record.value('MKB')))
                if value:
                    valueList = value.toList()
                    valueTNMS = valueList[0]
                    tnmsMap = valueList[1].toMap()
                    for name, TNMSId in tnmsMap.items():
                        if name in CEventEditDialog.TNMSFieldsDict.keys():
                            record.setValue(CEventEditDialog.TNMSFieldsDict[forceString(name)], TNMSId)
                    self.emitRowChanged(row)
                    return CMKBListInDocTableModel.setData(self, index, valueTNMS, role)
            if QtGui.qApp.isExSubclassMKBVisible() and 0 <= row < len(self.items()) and column == self.items()[row].indexOf('exSubclassMKB'):
                record = self.items()[row]
                self.updateMKBToExSubclass(record, forceStringEx(record.value('MKB')))
                return CMKBListInDocTableModel.setData(self, index, value, role)
            return CMKBListInDocTableModel.setData(self, index, value, role)
        else:
            return True


    def updateMKBToExSubclass(self, record, MKB):
        if QtGui.qApp.isExSubclassMKBVisible():
            self.cols()[record.indexOf('exSubclassMKB')].setMKB(forceString(MKB))


    def updateExSubclass(self, index, record, MKB):
        if QtGui.qApp.isExSubclassMKBVisible():
            newMKB = forceString(MKB)
            if self.cols()[record.indexOf('exSubclassMKB')].MKB != newMKB:
                record.setValue('exSubclassMKB', toVariant(u''))
                self.emitRowChanged(index.row())


    def updateMKBTNMS(self, record, MKB):
        if QtGui.qApp.isTNMSVisible():
            self.cols()[record.indexOf('TNMS')].setMKB(forceString(MKB))


    def updateTNMS(self, index, record, MKB):
        if QtGui.qApp.isTNMSVisible():
            newMKB = forceString(MKB)
            if self.cols()[record.indexOf('TNMS')].MKB != newMKB:
                row = index.row()
                tnmsMap = {}
                for keyName, fieldName in CEventEditDialog.TNMSFieldsDict.items():
                    tnmsMap[keyName] = None
                    record.setValue(fieldName, toVariant(None))
                record.setValue('TNMS', toVariant(u''))
                self.emitRowChanged(row)


    def removeRowEx(self, row):
        self.removeRows(row, 1)


    def updateDiagnosisType(self, fixedRowSet):
        mapPersonIdToRow = {}
        diagnosisTypeIds = []
        endDiagnosisTypeIds = None
        endPersonId = None
        endRow = -1
        for row, item in enumerate(self.items()):
            personId = forceRef(item.value('person_id'))
            rows = mapPersonIdToRow.setdefault(personId, [])
            rows.append(row)
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            diagnosisTypeIds.append(diagnosisTypeId)
            if self.diagnosisTypeCol.ids[0] == diagnosisTypeId and personId == self._parent.personId:
                endDiagnosisTypeIds = diagnosisTypeId
                endPersonId = personId
                endRow = row

        for personId, rows in mapPersonIdToRow.iteritems():
            usedDiagnosisTypeIds = [diagnosisTypeIds[row] for row in fixedRowSet.intersection(set(rows))]
            listFixedRowSet = [row for row in fixedRowSet.intersection(set(rows))]
            if ((self.diagnosisTypeCol.ids[0] in usedDiagnosisTypeIds) or (self.diagnosisTypeCol.ids[0] == diagnosisTypeIds[rows[0]])) and personId == self._parent.personId:
                firstDiagnosisId = self.diagnosisTypeCol.ids[0]
            elif (self.diagnosisTypeCol.ids[0] in usedDiagnosisTypeIds) and personId != self._parent.personId:
                 res = QtGui.QMessageBox.warning(self._parent,
                                           u'Внимание!',
                                           u'Смена заключительного диагноза.\nОтветственный будет заменен на \'%s\'.\nВы подтверждаете изменения?' % (forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))),
                                           QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                                           QtGui.QMessageBox.Cancel)
                 if res == QtGui.QMessageBox.Ok:
                     self._parent.personId = personId
                     self._parent.cmbPerson.setValue(self._parent.personId)
                     firstDiagnosisId = self.diagnosisTypeCol.ids[0]
                     rowEndPersonId = mapPersonIdToRow[endPersonId] if endPersonId else None
                     diagnosisTypeColIdsEnd = -1
                     if rowEndPersonId and len(rowEndPersonId) > 1:
                         for rowPerson in rowEndPersonId:
                             if diagnosisTypeIds[rowPerson] == self.diagnosisTypeCol.ids[1] or diagnosisTypeIds[rowPerson] == self.diagnosisTypeCol.ids[0]:
                                if endRow > -1 and endDiagnosisTypeIds == self.diagnosisTypeCol.ids[0] and endRow != rowPerson:
                                     diagnosisTypeColIdsEnd = self.diagnosisTypeCol.ids[2]
                                     break
                         if diagnosisTypeColIdsEnd == -1:
                             diagnosisTypeColIdsEnd = self.diagnosisTypeCol.ids[1]
                     else:
                         if endRow > -1 and endDiagnosisTypeIds == self.diagnosisTypeCol.ids[0]:
                             diagnosisTypeColIdsEnd = self.diagnosisTypeCol.ids[1]
                     if diagnosisTypeColIdsEnd > -1:
                         self.items()[endRow].setValue('diagnosisType_id', toVariant(diagnosisTypeColIdsEnd))
                         self.emitCellChanged(endRow, self.items()[endRow].indexOf('diagnosisType_id'))
                         diagnosisTypeIds[endRow] = forceRef(self.items()[endRow].value('diagnosisType_id'))
                 else:
                     if endRow > -1 and endDiagnosisTypeIds == self.diagnosisTypeCol.ids[0]:
                         self.items()[endRow].setValue('diagnosisType_id', toVariant(endDiagnosisTypeIds))
                         self.emitCellChanged(endRow, self.items()[endRow].indexOf('diagnosisType_id'))
                         diagnosisTypeIds[endRow] = forceRef(self.items()[endRow].value('diagnosisType_id'))
                     firstDiagnosisId = self.diagnosisTypeCol.ids[1]
                     diagnosisTypeColIdsRows = -1
                     if len(rows) > 1:
                         for rowPerson in rows:
                             if diagnosisTypeIds[rowPerson] == self.diagnosisTypeCol.ids[1] or diagnosisTypeIds[rowPerson] == self.diagnosisTypeCol.ids[0] and (rowPerson not in listFixedRowSet):
                                 diagnosisTypeColIdsRows = self.diagnosisTypeCol.ids[2]
                                 break
                         if diagnosisTypeColIdsRows == -1:
                            diagnosisTypeColIdsRows = self.diagnosisTypeCol.ids[1]
                     else:
                         diagnosisTypeColIdsRows = self.diagnosisTypeCol.ids[1]
                     if diagnosisTypeColIdsRows > -1:
                         for rowFixed in listFixedRowSet:
                             self.items()[rowFixed].setValue('diagnosisType_id', toVariant(diagnosisTypeColIdsRows))
                             self.emitCellChanged(rowFixed, self.items()[rowFixed].indexOf('diagnosisType_id'))
                             diagnosisTypeIds[rowFixed] = forceRef(self.items()[rowFixed].value('diagnosisType_id'))
                     usedDiagnosisTypeIds = [diagnosisTypeIds[row] for row in fixedRowSet.intersection(set(rows))]
            else:
                firstDiagnosisId = self.diagnosisTypeCol.ids[1]
            otherDiagnosisId = self.diagnosisTypeCol.ids[2]

            diagnosisTypeId = firstDiagnosisId if firstDiagnosisId not in usedDiagnosisTypeIds else otherDiagnosisId
            freeRows = set(rows).difference(fixedRowSet)
            for row in rows:
                if (row in freeRows) or diagnosisTypeIds[row] not in (firstDiagnosisId, otherDiagnosisId):
                    if diagnosisTypeId != diagnosisTypeIds[row] and diagnosisTypeIds[row] != self.diagnosisTypeCol.ids[3]:
                        self.items()[row].setValue('diagnosisType_id', toVariant(diagnosisTypeId))
                        self.emitCellChanged(row, self.items()[row].indexOf('diagnosisType_id'))
                        diagnosisTypeId = forceRef(self.items()[row].value('diagnosisType_id'))
                        diagnosisTypeIds[row] = diagnosisTypeId
                    diagnosisTypeId = otherDiagnosisId


    def updateDispanserByMKB(self, row, specifiedDispanserId, specifiedProlongMKB):
        item = self.items()[row]
        if specifiedProlongMKB and specifiedDispanserId and specifiedDispanserId in self.observedDispanserIdList:
            dispanserId = specifiedDispanserId if specifiedDispanserId not in self.takenDispanserIdList else self.consistDispanserId
            item.setValue('dispanser_id', toVariant(dispanserId))
            self.emitCellChanged(row, item.indexOf('dispanser_id'))
        elif not specifiedProlongMKB:
            item.setValue('dispanser_id', toVariant(self.takenDispanserId))
            self.emitCellChanged(row, item.indexOf('dispanser_id'))


    def updateCharacterByMKB(self, row, MKB, specifiedCharacterId):
        characterIdList = getAvailableCharacterIdByMKB(MKB)
        item = self.items()[row]
        if specifiedCharacterId in characterIdList:
            characterId = specifiedCharacterId
        else:
            characterId = forceRef(item.value('character_id'))
            if (characterId in characterIdList) or (characterId is None and not characterIdList):
                return
            if characterIdList:
                characterId = characterIdList[0]
            else:
                characterId = None
        item.setValue('character_id', toVariant(characterId))
        self.emitCellChanged(row, item.indexOf('character_id'))


    def updateToxicSubstancesByMKB(self, row, MKB):
        toxicSubstanceIdList = getToxicSubstancesIdListByMKB(MKB)
        item = self.items()[row]
        toxicSubstanceId = forceRef(item.value('toxicSubstances_id'))
        if toxicSubstanceId and toxicSubstanceId in toxicSubstanceIdList:
            return
        item.setValue('toxicSubstances_id', toVariant(None))
        self.emitCellChanged(row, item.indexOf('toxicSubstances_id'))


    def updateTraumaType(self, row, MKB, specifiedTraumaTypeId):
        item = self.items()[row]
        prevTraumaTypeId = forceRef(item.value('traumaType_id'))
        if specifiedTraumaTypeId:
            traumaTypeId = specifiedTraumaTypeId
        else:
            traumaTypeId = prevTraumaTypeId
        if traumaTypeId != prevTraumaTypeId:
            item.setValue('traumaType_id', toVariant(traumaTypeId))
            self.emitCellChanged(row, item.indexOf('traumaType_id'))


    def getPersonsWithSignificantDiagnosisType(self):
        result = []
        significantDiagnosisTypeIdList = [self.diagnosisTypeCol.ids[0], self.diagnosisTypeCol.ids[1]]
        for item in self.items():
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId and diagnosisTypeId in significantDiagnosisTypeIdList:
                personId = forceRef(item.value('person_id'))
                if personId and personId not in result:
                    result.append(personId)
        return result


    def getFinalDiagnosisMKB(self):
        finalDiagnosisTypeId = self.diagnosisTypeCol.ids[0] or self.diagnosisTypeCol.ids[1]
        items = self.items()
        for item in items:
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId == finalDiagnosisTypeId:
                return forceString(item.value('MKB')), forceString(item.value('MKBEx'))
        return '', ''


    def getAssociatedDiagnosisMKB(self):
        associatedDiagnosisTypeId = self.diagnosisTypeCol.ids[2]
        items = self.items()
        for item in items:
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId == associatedDiagnosisTypeId:
                return forceString(item.value('MKB'))
        return ''


    def getComplicationDiagnosisMKB(self):
        complicationDiagnosisTypeId = self.diagnosisTypeCol.ids[3]
        items = self.items()
        for item in items:
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId == complicationDiagnosisTypeId:
                return forceString(item.value('MKB'))
        return ''


    def getFinalDiagnosisId(self):
        finalDiagnosisTypeId = self.diagnosisTypeCol.ids[0]
        items = self.items()
        for item in items:
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId == finalDiagnosisTypeId:
                return forceRef(item.value('diagnosis_id'))
        return None


    def getBaseServiceIdMKB(self):
        serviceId = None
        MKB, MKBEx = self.getFinalDiagnosisMKB()
        if MKB:
            db = QtGui.qApp.db
            table = db.table('MKB')
            cond = [table['DiagID'].like(MKB)]
            record = db.getRecordEx(table, ['service_id'], cond)
            serviceId = forceRef(record.value('service_id')) if record else None
        return serviceId


    def emitDiagnosisChanged(self, MKB=''):
        self.emit(SIGNAL('diagnosisChanged(QString)'), MKB)

    
    def saveItems(self, masterId = None):
        CMKBListInDocTableModel.saveItems(self, masterId)
        self.prophylaxisPlanningSync()
        
    
    def surveillanceRecords(self, clientId):
        MKBs = []
        items = list(self.items())
        if items:
            items.sort(key=lambda x: forceDate(x.value('endDate')))
            for idx, record in enumerate(items):
                dispanserId = forceRef(record.value('dispanser_id'))
                if dispanserId:
                    MKBs.append(forceString(record.value('MKB')))
        if self.MKBs == MKBs or not MKBs:
            if not MKBs:
                self.MKBs = []
            return []
        
        self.MKBs = MKBs
        condMKB = []
        tempMKBs = []
        db = QtGui.qApp.db
        tableDiagnostic = db.table('Diagnostic')
        tableDiagnosis = db.table('Diagnosis')
        queryTable = tableDiagnosis.leftJoin(tableDiagnostic, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            
        for MKB in self.MKBs:
            diag = MKB
            if len(MKB) >= 3:
                diag = MKB[:3]
            if diag and diag not in tempMKBs:
                tempMKBs.append(diag)
        for tempMKB in tempMKBs:
            condMKB.append(tableDiagnosis['MKB'].like(tempMKB + '%'))
            
        cond = [tableDiagnosis['deleted'].eq(0),
                tableDiagnostic['deleted'].eq(0),
                tableDiagnosis['dispanser_id'].isNotNull(),
                tableDiagnostic['dispanser_id'].isNotNull(),
                tableDiagnosis['client_id'].eq(clientId),
                db.joinOr(condMKB)
                ]
            
        cols = [u'Diagnostic.*',
                tableDiagnosis['MKB'],
                tableDiagnosis['MKBEx'],
                tableDiagnosis['dispanserBegDate'],
                tableDiagnosis['dispanserPerson_id'],
                tableDiagnosis['dispanser_id'].alias('diagnosisDispanser_id'),
                tableDiagnostic['endDate'],
                'max(Diagnosis.endDate) as maxDiagnosisEndDate',
                'max(Diagnostic.endDate) as maxDiagnosticEndDate'
                ]
        dispanserItems = db.getRecordListGroupBy(queryTable, cols, cond, group = 'MKB', order='maxDiagnosisEndDate DESC, maxDiagnosticEndDate DESC')
        return dispanserItems


class CF030FinalDiagnosticsModel(CF030BaseDiagnosticsModel):
    __pyqtSignals__ = ('resultChanged()'
                      )

    def __init__(self, parent):
        CF030BaseDiagnosticsModel.__init__(self, parent, '1', '2', '9', '3')
        self.addCol(CRBInDocTableCol(    u'Результат',     'result_id',     10, 'rbDiagnosticResult', showFields=CRBComboBox.showNameAndCode, preferredWidth=350))
        self.mapMKBToServiceId = {}


    def getCloseOrMainDiagnosisTypeIdList(self):
        return self.diagnosisTypeCol.ids[:2]


    def setData(self, index, value, role=Qt.EditRole):
        resultId = self.resultId()
        result = CF030BaseDiagnosticsModel.setData(self, index, value, role)
        eventEditor = QObject.parent(self)
        if resultId != self.resultId() or eventEditor.cmbResult.value() != self.resultId():
            self.emitResultChanged()
        return result


    def removeRowEx(self, row):
        resultId = self.resultId()
        self.removeRows(row, 1)
        eventEditor = QObject.parent(self)
        eventEditor.updateActionsDiagnosisByDiagnostics()
        if resultId != self.resultId() or eventEditor.cmbResult.value() != self.resultId():
            self.emitResultChanged()


    def resultId(self):
        finalDiagnosisTypeId = self.diagnosisTypeCol.ids[0]
        items = self.items()
        for item in items:
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId == finalDiagnosisTypeId:
                return forceRef(item.value('result_id'))
        return None


    def diagnosisServiceId(self):
        items = self.items()
        if items:
            code = forceString(items[0].value('MKB'))
            if code in self.mapMKBToServiceId:
                return self.mapMKBToServiceId[code]
            else:
                serviceId = forceRef(QtGui.qApp.db.translate('MKB', 'DiagID', code, 'service_id'))
                self.mapMKBToServiceId[code] = serviceId
                return serviceId
        else:
            return None


    def emitResultChanged(self):
        self.emit(SIGNAL('resultChanged()'))

class CF030SurveillanceModel(CInDocTableModel):
    Col_MKB = 0
    Col_EndDate = 1
    Col_PersonId = 2
    Col_BegDate = 3

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ProphylaxisPlanning', 'id', 'parent_id', parent)
        self._parent = parent
        db = QtGui.qApp.db
        self.personCache = CTableRecordCache(db, db.forceTable('vrbPersonWithSpeciality'), u'*', capacity=None)
        self.addCol(CICDExInDocTableCol(u'МКБ', 'MKB', 7), QVariant.String).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Дата следующей явки', 'endDate', 10, canBeEmpty=True))
        self.addCol(CPersonFindInDocTableCol(u'Врач по ДН', 'person_id', 20, 'vrbPersonWithSpeciality')).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Дата взятия на ДН', 'takenDate', 10, canBeEmpty=True)).setReadOnly(True)
        self.addHiddenCol('removeDate')
        self.addHiddenCol('removeReason_id')
        self.addHiddenCol('speciality_id')
        self.addHiddenCol('scene_id')
        self.addHiddenCol('prophylaxisPlanningType_id')
        self.addHiddenCol('client_id')
        self.addHiddenCol('contact')
        self.addHiddenCol('dispanser_id')
        self.addHiddenCol('orgStructure_id')
        self.eventEditor = None
        self.readOnly = False
        self.diagnosticRecords = {}
        self.diagnosticGroupRecords = {}
        self.diagnosticItems = []
        self.prophylaxisPlanningTypeId = self.getProphylaxisPlanningType()
        self.MKBs = []
        self.clientId = None
        self.eventId = None
        prefs = QtGui.qApp.preferences.appPrefs
        self.autoPlanning = forceBool(prefs.get('paramPlanningCheck', False))
        if self.autoPlanning:
            self.planningBegDate = forceInt(prefs.get('paramPlanningBegDate', 0))
            self.planningFreq = forceInt(prefs.get('paramPlanningFreq', 6))
            self.planningDuration = 1


    def getProphylaxisPlanningType(self):
        db = QtGui.qApp.db
        table = db.table('rbProphylaxisPlanningType')
        record = db.getRecordEx(table, [table['id']], [table['code'].eq(u'ДН')])
        return forceRef(record.value('id')) if record else None


    def loadItems(self, masterId):
        self._items = []
        MKBs = {}
        if self.MKBs and self.clientId:
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableRBDispanser = db.table('rbDispanser')
            cols = []
            for col in self._cols:
                if not col.external():
                    cols.append(col.fieldName())
            cols.append(self._idFieldName)
            cols.append(self._masterIdFieldName)
            if self._idxFieldName:
                cols.append(self._idxFieldName)
            for col in self._hiddenCols:
                cols.append(col)
            table = self._table
            filter = [table['parent_id'].isNull(),
                      table['client_id'].eq(self.clientId)]
            condMKB = []
            tempMKBs = []
            for MKB in self.MKBs:
                diag = MKB
                if len(MKB) >= 3:
                    diag = MKB[:3]
                if diag and diag not in tempMKBs:
                    tempMKBs.append(diag)
            for tempMKB in tempMKBs:
                condMKB.append(table['MKB'].like(tempMKB + '%'))
            filter.append(db.joinOr(condMKB))
            if self._filter:
                filter.append(self._filter)
            if table.hasField('deleted'):
                filter.append(table['deleted'].eq(0))
            if self._idxFieldName:
                order = [self._idxFieldName, table['takenDate'].name() + u'ASC', table['removeDate'].name() + u'DESC']
            else:
                order = [table['takenDate'].name() + u'ASC', table['removeDate'].name() + u'DESC']
            self._items = db.getRecordList(table, cols, filter, order)
            if self._extColsPresent:
                extSqlFields = []
                for col in self._cols:
                    if col.external():
                        fieldName = col.fieldName()
                        if fieldName not in cols:
                            extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))
                if extSqlFields:
                    for item in self._items:
                        for field in extSqlFields:
                            item.append(field)
            filteredItems = []
            for item in self._items:
                dispanserId = forceRef(item.value('dispanser_id'))
                observed = 0
                if dispanserId:
                    recObserved = db.getRecordEx(tableRBDispanser, [tableRBDispanser['observed']],
                                                 [tableRBDispanser['id'].eq(dispanserId)])
                    observed = forceInt(recObserved.value('observed')) if recObserved else 0
                if observed:
                    filteredItems.append(item)
                else:
                    continue
                

                MKB = forceStringEx(item.value('MKB'))

                diagnosticRecord = self.diagnosticRecords.get(MKB, None)
                dispanserBegDate = forceDate(diagnosticRecord.value('dispanserBegDate')) if diagnosticRecord else QDate()
                dispanserPerson = forceRef(diagnosticRecord.value('dispanserPerson_id')) if diagnosticRecord else None
                d = self.eventEditor.edtBegDate.date()
                lastDay = QDate(d.year(), d.month(), d.daysInMonth())
                recSurv = db.getRecordEx(table, [table['endDate'],
                                                 table['id']], 
                                                [table['endDate'].gt(lastDay),
                                                 table['parent_id'].eq(forceInt(item.value('id'))),
                                                 table['deleted'].eq(0)],
                                                'endDate ASC')
                if recSurv:
                    endDate = forceDate(recSurv.value('endDate'))
                    planId = forceRef(recSurv.value('id'))
                else:
                    endDate = QDate()
                    planId = None
                self._items[self._items.index(item)].setValue('takenDate', dispanserBegDate)
                self._items[self._items.index(item)].setValue('person_id', dispanserPerson)
                if endDate and planId:
                    self._items[self._items.index(item)].setValue('endDate', endDate)
                    self._items[self._items.index(item)].setValue('begDate', endDate)
                    self._items[self._items.index(item)].planning = True
                    self._items[self._items.index(item)].planId = planId
                else:
                    if self.autoPlanning:
                        self.setNewPeriodRecord(self._items[self._items.index(item)])
                    else:
                        self._items[self._items.index(item)].setValue('endDate', QDate()) 
                        self._items[self._items.index(item)].setValue('begDate', QDate())
                    self._items[self._items.index(item)].planning = True
                
                if MKB and MKB[:3] not in MKBs:
                    MKB3 = MKB
                    if len(MKB) >= 3:
                        MKB3 = MKB[:3]
                    MKBs[MKB3] = observed
            self._items = filteredItems
            for item in self._items:
                item.setIsDirty(False)
                
            for MKB in self.MKBs:
                MKBFind = MKB
                if len(MKB) >= 3:
                    MKBFind = MKB[:3]
                needGroup = 0
                if (MKBFind not in MKBs.keys() or not MKBs[MKBFind]):
                    tableDiagnosisType = db.table('rbDiagnosisType')
                    tableDispanserDS = db.table('rbDispanser').alias('DDS')
                    tableDispanserDC = db.table('rbDispanser').alias('DDC')
                    queryTable = tableDiagnosis.leftJoin(tableDiagnostic, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
                    queryTable = queryTable.leftJoin(tableDispanserDC, tableDispanserDC['id'].eq(tableDiagnostic['dispanser_id']))
                    queryTable = queryTable.leftJoin(tableDispanserDS, tableDispanserDS['id'].eq(tableDiagnosis['dispanser_id']))
                    queryTable = queryTable.leftJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(tableDiagnosis['diagnosisType_id']))
                    cond = [tableDiagnosis['MKB'].eq(MKB),
                            tableDiagnosis['deleted'].eq(0),
                            tableDiagnostic['deleted'].eq(0),
                            tableDiagnosis['client_id'].eq(self.clientId),
                            tableDispanserDC['observed'].eq(1),
                            tableDispanserDS['observed'].eq(1),
                            tableDiagnostic['event_id'].isNotNull(),
                            tableDiagnosisType['code'].inlist(['1','2','9','98'])
                            ]
                    cols = [u'Diagnostic.*',
                            tableDiagnosis['MKB'],
                            tableDiagnosis['MKBEx'],
                            tableDiagnosis['dispanserBegDate'],
                            tableDiagnosis['dispanserPerson_id'],
                            tableDiagnosis['dispanser_id'].alias('diagnosisDispanser_id'),
                            tableDiagnostic['endDate'],
                            'max(Diagnosis.endDate) as maxDiagnosisEndDate',
                            'max(Diagnostic.endDate) as maxDiagnosticEndDate'
                            ]
                    diagRecords = db.getRecordListGroupBy(queryTable, cols, cond, group='Diagnostic.id', order='maxDiagnosisEndDate DESC, maxDiagnosticEndDate DESC')
                    diagRecord = diagRecords[0] if diagRecords else None
                    if diagRecord:
                        needGroup = 1
                        self.diagnosticRecords[MKB] = diagRecord
                if needGroup:
                    record = CInDocTableModel.getEmptyRecord(self)
                    specialityId = None
                    orgStructureId = None
                    takenDate = None
                    diagnosticRecord = self.diagnosticRecords.get(MKB, None)
                    if diagnosticRecord:
                        takenDate = forceDate(diagnosticRecord.value('dispanserBegDate')) if forceDate(diagnosticRecord.value('dispanserBegDate')) else QDate()
                        personId = forceRef(diagnosticRecord.value('dispanserPerson_id')) if diagnosticRecord else None
                        record.setValue('person_id', toVariant(personId))
                        personRecord = self.personCache.get(personId) if personId else None
                        if personRecord:
                            orgStructureId = forceRef(personRecord.value('orgStructure_id'))
                            specialityId = forceRef(personRecord.value('speciality_id'))
                            if orgStructureId:
                                record.setValue('orgStructure_id', toVariant(orgStructureId))
                            if specialityId:
                                record.setValue('speciality_id', toVariant(specialityId))
                        record.setValue('MKB', diagnosticRecord.value('MKB'))
                    dispanserId = diagnosticRecord.value('diagnosisDispanser_id')
                    record.setValue('dispanser_id', dispanserId)
                    record.setValue('scene_id', toVariant(None))
                    record.setValue('prophylaxisPlanningType_id', toVariant(self.prophylaxisPlanningTypeId))
                    record.setValue('client_id', toVariant(self.clientId))
                    record.setValue('takenDate', toVariant(takenDate))
                    self.setNewPeriodRecord(record)
                    MKBs[MKBFind] = 1
                    self._items.append(record)
                    self._items[self._items.index(record)].planning = True
        self.reset()


    def loadItem(self, MKB):
        MKBs = {}
        loaded = False
        loadedMKBs = []
        filteredItems = []
        for item in self._items:
            eMKB = forceStringEx(item.value('MKB'))
            if eMKB in self.MKBs:
                if len(eMKB) >= 3:
                    eMKB = eMKB[:3]
                    if eMKB not in loadedMKBs:
                        loadedMKBs.append(eMKB)
                filteredItems.append(item)
        self._items = filteredItems
        if len(MKB) >= 3:
            MKB = MKB[:3]
        if MKB in loadedMKBs:
            return
        if self.MKBs and self.clientId:
            db = QtGui.qApp.db
            tableRBDispanser = db.table('rbDispanser')
            cols = []
            for col in self._cols:
                if not col.external():
                    cols.append(col.fieldName())
            cols.append(self._idFieldName)
            cols.append(self._masterIdFieldName)
            if self._idxFieldName:
                cols.append(self._idxFieldName)
            for col in self._hiddenCols:
                cols.append(col)
            table = self._table
            filter = [table['parent_id'].isNull(),
                      table['client_id'].eq(self.clientId)]
            condMKB = []
            diag = MKB
            if len(MKB) >= 3:
                diag = MKB[:3]
            condMKB.append(table['MKB'].like(diag + '%'))
            filter.append(db.joinOr(condMKB))
            if self._filter:
                filter.append(self._filter)
            if table.hasField('deleted'):
                filter.append(table['deleted'].eq(0))
            if self._idxFieldName:
                order = [self._idxFieldName, table['takenDate'].name() + u'ASC', table['removeDate'].name() + u'DESC']
            else:
                order = [table['takenDate'].name() + u'ASC', table['removeDate'].name() + u'DESC']
            items = db.getRecordList(table, cols, filter, order)
            if self._extColsPresent:
                extSqlFields = []
                for col in self._cols:
                    if col.external():
                        fieldName = col.fieldName()
                        if fieldName not in cols:
                            extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))
                if extSqlFields:
                    for item in items:
                        for field in extSqlFields:
                            item.append(field)
            filteredItems = []
            for item in items:
                dispanserId = forceRef(item.value('dispanser_id'))
                observed = 0
                if dispanserId:
                    recObserved = db.getRecordEx(tableRBDispanser, [tableRBDispanser['observed']],
                                                 [tableRBDispanser['id'].eq(dispanserId)])
                    observed = forceInt(recObserved.value('observed')) if recObserved else 0
                if observed:
                    filteredItems.append(item)
                else:
                    continue
                

                eMKB = forceStringEx(item.value('MKB'))

                diagnosticRecord = self.diagnosticRecords.get(eMKB, None)
                dispanserBegDate = forceDate(diagnosticRecord.value('dispanserBegDate')) if diagnosticRecord else QDate()
                dispanserPerson = forceRef(diagnosticRecord.value('dispanserPerson_id')) if diagnosticRecord else None
                d = self.eventEditor.edtBegDate.date()
                lastDay = QDate(d.year(), d.month(), d.daysInMonth())
                recSurv = db.getRecordEx(table, [table['endDate'],
                                                 table['id']], 
                                                [table['endDate'].gt(lastDay),
                                                 table['parent_id'].eq(forceInt(item.value('id'))),
                                                 table['deleted'].eq(0)],
                                                'endDate ASC')
                if recSurv:
                    endDate = forceDate(recSurv.value('endDate'))
                    planId = forceRef(recSurv.value('id'))
                else:
                    endDate = QDate()
                    planId = None
                item.setValue('takenDate', dispanserBegDate)
                item.setValue('person_id', dispanserPerson)
                if endDate and planId:
                    item.setValue('endDate', endDate)
                    item.setValue('begDate', endDate)
                    item.planning = True
                    item.planId = planId
                else:
                    if self.autoPlanning:
                        self.setNewPeriodRecord(item)
                    else:
                        item.setValue('endDate', QDate()) 
                        item.setValue('begDate', QDate())
                    item.planning = True
                
                if MKB and MKB[:3] not in MKBs:
                    MKB3 = MKB
                    if len(MKB) >= 3:
                        MKB3 = MKB[:3]
                    MKBs[MKB3] = observed
                if MKB not in loadedMKBs:
                    loadedMKBs.append(MKB)
            self._items.extend(filteredItems)
            for item in self._items:
                item.setIsDirty(False)
                
            for MKB in self.MKBs:
                MKBFind = MKB
                if len(MKB) >= 3:
                    MKBFind = MKB[:3]
                if MKBFind in loadedMKBs:
                    continue
                diagnosticRecord = self.diagnosticRecords.get(MKB, None)
                if diagnosticRecord:
                    dispanserId = None
                    for sItem in self._parent.modelFinalDiagnostics.items():
                        sMKB = forceString(sItem.value('MKB'))
                        if sMKB:
                            sDiag = sMKB
                            if len(sMKB) >= 3:
                                sDiag = sMKB[:3]
                        if sDiag == MKBFind:
                            dispanserId = forceRef(sItem.value('dispanser_id'))
                            break
                    observed = 0
                    if dispanserId:
                        recObserved = db.getRecordEx(tableRBDispanser, [tableRBDispanser['observed']],
                                                    [tableRBDispanser['id'].eq(dispanserId)])
                        observed = forceInt(recObserved.value('observed')) if recObserved else 0
                    if not observed:
                        continue
                    record = CInDocTableModel.getEmptyRecord(self)
                    specialityId = None
                    orgStructureId = None
                    takenDate = None
                    if diagnosticRecord:
                        takenDate = forceDate(diagnosticRecord.value('dispanserBegDate')) if forceDate(diagnosticRecord.value('dispanserBegDate')) else QDate()
                        personId = forceRef(diagnosticRecord.value('dispanserPerson_id')) if diagnosticRecord else None
                        record.setValue('person_id', toVariant(personId))
                        personRecord = self.personCache.get(personId) if personId else None
                        if personRecord:
                            orgStructureId = forceRef(personRecord.value('orgStructure_id'))
                            specialityId = forceRef(personRecord.value('speciality_id'))
                            if orgStructureId:
                                record.setValue('orgStructure_id', toVariant(orgStructureId))
                            if specialityId:
                                record.setValue('speciality_id', toVariant(specialityId))
                        record.setValue('MKB', diagnosticRecord.value('MKB'))
                    dispanserId = diagnosticRecord.value('diagnosisDispanser_id')
                    record.setValue('dispanser_id', dispanserId)
                    record.setValue('scene_id', toVariant(None))
                    record.setValue('prophylaxisPlanningType_id', toVariant(self.prophylaxisPlanningTypeId))
                    record.setValue('client_id', toVariant(self.clientId))
                    record.setValue('takenDate', toVariant(takenDate))
                    self.setNewPeriodRecord(record)
                    MKBs[MKBFind] = 1
                    self._items.append(record)
                    self._items[self._items.index(record)].planning = True
                    if MKBFind not in loadedMKBs:
                        loadedMKBs.append(MKBFind)
        self.reset()


    def setNewPeriodRecord(self, record):
        if forceDate(record.value('endDate')) and forceDate(record.value('endDate')) > QDate.currentDate():
            endDate = forceDate(record.value('endDate'))
        else:
            endDate = QDate()
        if self.autoPlanning:
            if not endDate:
                endDate = QDate.currentDate()
            if not self.planningBegDate:
                if not endDate == firstMonthDay(endDate):
                    endDate = firstMonthDay(endDate.addMonths(1))
            endDate = endDate.addMonths(self.planningFreq)
        record.setValue('begDate', toVariant(endDate))
        record.setValue('endDate', toVariant(endDate))
        return record
        

    def setDiagnosticRecords(self, records):
        self.diagnosticRecords = {}
        diagnosticGroupRecords = {}
        self.MKBs = []
        for diagnosticRecord in records:
            MKB = forceStringEx(diagnosticRecord.value('MKB'))
            if MKB:
                if MKB not in self.MKBs:
                    self.MKBs.append(MKB)
                self.diagnosticRecords[MKB] = diagnosticRecord
                MKBGroup = MKB[:3] if len(MKB) > 3 else MKB
                if MKBGroup not in self.diagnosticGroupRecords.keys():
                    diagnosticGroupRecords[MKBGroup] = diagnosticRecord
        for diagnosticGroupMKB, diagnosticGroupRecord in diagnosticGroupRecords.items():
            self.diagnosticGroupRecords[diagnosticGroupMKB] = diagnosticGroupRecord


    def setClientId(self, clientId):
        self.clientId = clientId


    def setEventId(self, eventId):
        self.eventId = eventId


    def setMKB(self, MKB):
        self.MKB = MKB


    def setMKBs(self, MKBs):
        self.MKBs = MKBs


    def setItems(self, items, diagnosticItems):
        CInDocTableModel.setItems(self, items)
        self.diagnosticItems = diagnosticItems


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        rowCount = len(self._items)
        if rowCount > 0:
            item = self._items[rowCount - 1]
            MKB = forceStringEx(item.value('MKB'))
            if MKB:
                result.setValue('MKB', toVariant(MKB))
                result.setValue('takenDate', item.value('takenDate'))
                result.setValue('dispanser_id', item.value('dispanser_id'))
        result.setValue('prophylaxisPlanningType_id', toVariant(self.prophylaxisPlanningTypeId))
        result.setValue('client_id', toVariant(self.clientId))
        result.setValue('plannedDate', toVariant(QDate.currentDate()))
        return result


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def getMaxEndDate(self):
        items = self._items
        maxEndDate = None
        for item in items:
            endDate = forceDate(item.value('endDate'))
            if endDate and endDate > maxEndDate:
                maxEndDate = endDate
        return maxEndDate


    def getMaxRemoveDate(self):
        items = self._items
        maxRemoveDate = None
        for item in items:
            removeDate = forceDate(item.value('removeDate'))
            if removeDate and removeDate > maxRemoveDate:
                maxRemoveDate = removeDate
        return maxRemoveDate


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            row = index.row()
            column = index.column()
            orgStructureId = None
            specialityId = None
            isNew = row == len(self._items)
            if isNew:
                if value.isNull():
                    return False
                maxRemoveDate = self.getMaxRemoveDate()
                maxEndDate = self.getMaxEndDate()
                if maxRemoveDate >= maxEndDate:
                    return False
            result = CInDocTableModel.setData(self, index, value, role)
            if result and 0 <= row < len(self._items):
                item = self._items[row]
                userId = forceRef(item.value('person_id'))
                if column == self.Col_EndDate:
                    self.setValue(row, 'begDate', value)

                if isNew:
                    personRecord = self.personCache.get(userId) if userId else None
                    if personRecord:
                        orgStructureId = forceInt(personRecord.value('orgStructure_id'))
                        specialityId = forceInt(personRecord.value('speciality_id'))
                        if orgStructureId:
                            self.setValue(row, 'orgStructure_id', orgStructureId)
                        if specialityId:
                            self.setValue(row, 'speciality_id', specialityId)

                    self.setValue(row, 'person_id', userId)
                self.emitRowChanged(row)
            return result
        return False


    def getEmptyRecordEx(self, MKB, prophylaxisPlanningTypeId, clientId, personId, dispanserId):
        db = QtGui.qApp.db
        dispanserPerson = None
        diagnosticRecord = self.diagnosticRecords.get(MKB, None)
        if diagnosticRecord:
            dispanserPerson = forceRef(diagnosticRecord.value('dispanserPerson_id')) if diagnosticRecord else None
        personId = personId if personId else dispanserPerson
        table = db.table('ProphylaxisPlanning')
        record = CSqlRecord()
        fields = [table['id'],
                  table['parent_id'],
                  table['MKB'],
                  table['plannedDate'],
                  table['begDate'],
                  table['endDate'],
                  table['visit_id'],
                  table['removeDate'],
                  table['removeReason_id'],
                  table['person_id'],
                  table['orgStructure_id'],
                  table['speciality_id'],
                  table['scene_id'],
                  table['prophylaxisPlanningType_id'],
                  table['client_id'],
                  table['takenDate'],
                  table['dispanser_id'],
                  table['contact'],
                  ]
        for field in fields:
            record.append(QtSql.QSqlField(field.field))
        self.personCache = CTableRecordCache(db, db.forceTable('vrbPerson'), u'*', capacity=None)
        personRecord = self.personCache.get(personId) if personId else None
        orgStructureId = forceRef(personRecord.value('orgStructure_id'))
        specialityId = forceRef(personRecord.value('speciality_id'))

        record.setValue('MKB', toVariant(MKB))
        record.setValue('takenDate', toVariant(QDate()))
        record.setValue('plannedDate', toVariant(QDate.currentDate()))
        record.setValue('person_id', toVariant(personId))
        record.setValue('orgStructure_id', toVariant(orgStructureId))
        record.setValue('speciality_id', toVariant(specialityId))
        record.setValue('scene_id', toVariant(None))
        record.setValue('prophylaxisPlanningType_id', toVariant(prophylaxisPlanningTypeId))
        record.setValue('client_id', toVariant(clientId))
        record.setValue('contact', getClientPhone(clientId))
        record.setValue('dispanser_id', toVariant(dispanserId))
        return record

    
    def saveItems(self, masterId = None):
        db = QtGui.qApp.db
        table = self._table
        masterId = toVariant(masterId)
        masterIdFieldName = self._masterIdFieldName
        idFieldName = self._idFieldName
        idList = {}
        for idx, record in enumerate(self._items):
            isSaved = forceBool(record.value('id'))
            MKB = forceStringEx(record.value('MKB'))
            diag = MKB
            dispanserId = None
            if len(MKB) >= 3:
                diag = MKB[:3]
            for sItem in self._parent.modelFinalDiagnostics.items():
                sMKB = forceString(sItem.value('MKB'))
                if sMKB:
                    sDiag = sMKB
                    if len(sMKB) >= 3:
                        sDiag = sMKB[:3]
                if sDiag == diag:
                    dispanserId = forceRef(sItem.value('dispanser_id'))
                    break
            endDate = record.value('endDate')
            if dispanserId not in db.getDistinctIdList('rbDispanser', 'id', ['observed = 1']):
                continue
            if not isSaved:
                record.setValue(masterIdFieldName, masterId)
                record.setValue('client_id', toVariant(self.clientId))
                isDirty = record.isDirty()
                if self._idxFieldName:
                    record.setValue(self._idxFieldName, toVariant(idx))
                if self._extColsPresent:
                    outRecord = self.removeExtCols(record)
                else:
                    outRecord = record
                outRecord.setValue('begDate', QDate())
                outRecord.setValue('endDate', QDate())
                outRecord.setIsDirty(isDirty)
                id = db.insertOrUpdate(table, outRecord)
                outRecord.setValue('begDate', endDate)
                outRecord.setValue('endDate', endDate)
                record.setValue(idFieldName, toVariant(id))
                idList[idx] = id
                self.saveDependence(idx, id)
            if hasattr(record, 'planning') and record.planning:
                planRecord = None
                if hasattr(record, 'planId') and record.planId:
                    planRecord = db.getRecordEx(table, '*', [table['id'].eq(record.planId)])
                if not planRecord:
                    planRecord = self.getEmptyRecordEx(forceString(record.value('MKB')),
                                                forceInt(record.value('prophylaxisPlanningType_id')),
                                                forceInt(record.value('client_id')),
                                                forceInt(self._parent.cmbPerson.value()),
                                                forceInt(record.value('dispanser_id')))
                        
                planRecord.setValue('endDate', toVariant(endDate))
                planRecord.setValue('begDate', toVariant(endDate))
                planRecord.setValue('parent_id', toVariant(record.value('id')))
                try:
                    id = db.insertOrUpdate(table, planRecord)
                finally:
                    record.setValue('planId', id)
                    record.planId = id
                    res = self.diagnosisDispansPlanedSave(planRecord)
        
        return idList
    
    def diagnosisDispansPlanedSave(self, record):
        db = QtGui.qApp.db
        endDate = forceDate(record.value(u'endDate'))
        prophylaxisPlanningTypeIds = db.getIdList(u'rbProphylaxisPlanningType', u'rbProphylaxisPlanningType.id', u'code like "%ДН%"')
        if not forceInt(record.value(u'prophylaxisPlanningType_id')) in prophylaxisPlanningTypeIds:
            return True
        currentDate = QDate.currentDate()
        if currentDate.year() > endDate.year() or (currentDate.year() == endDate.year() and currentDate.month() > endDate.month()):
            return True
        removeDate = forceDate(record.value(u'removeDate'))
        if removeDate:
            return True
        clientRecord = db.getRecordEx(u'Client', u'age(Client.birthDate, {}) as age'.format(db.formatDate(forceDate(record.value('endDate')))), u'Client.id = {}'.format(forceInt(record.value('client_id'))))
        if forceInt(clientRecord.value('age')) < 18:
            return True
        dispNabMKBRecord = db.getRecordEx(u'soc_DispNabMKB', u'id', u'soc_DispNabMKB.code = "{}" and (soc_DispNabMKB.endDate is NULL or soc_DispNabMKB.endDate > {})'.format(forceString(record.value('MKB')), db.formatDate(forceDate(record.value('begDate')))))
        if not dispNabMKBRecord:
            return True
        tableDiagnosisDispansPlaned = db.table('DiagnosisDispansPlaned')
        tableDiagnosis = db.table('Diagnosis')
        queryTable = tableDiagnosisDispansPlaned.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnosisDispansPlaned['diagnosis_id']))
        cond = [
            tableDiagnosisDispansPlaned['deleted'].eq(0),
            'year = year({})'.format(db.formatDate(forceDate(record.value('endDate')))),
            'month = month({})'.format(db.formatDate(forceDate(record.value('endDate')))),
            tableDiagnosisDispansPlaned['client_id'].eq(forceInt(record.value('client_id'))),
            tableDiagnosis['MKB'].eq(forceString(record.value('MKB')))
        ]
        diagnosisDispansPlanedRecord = db.getRecordEx(queryTable, u'DiagnosisDispansPlaned.id', cond)
        if diagnosisDispansPlanedRecord:
            return True
        tableRBDispanser = db.table('rbDispanser')
        tableRBDiagnosisType = db.table('rbDiagnosisType')
        queryTable = tableDiagnosis.leftJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnosis['dispanser_id']))
        queryTable = queryTable.leftJoin(tableRBDiagnosisType, tableRBDiagnosisType['id'].eq(tableDiagnosis['diagnosisType_id']))
        cond = [
            tableDiagnosis['deleted'].eq(0),
            tableDiagnosis['MKB'].eq(forceString(record.value('MKB'))),
            tableDiagnosis['client_id'].eq(forceInt(record.value('client_id'))),
            tableRBDispanser['observed'].eq(1),
            tableRBDiagnosisType['code'].inlist(['2','9'])
        ]
        diagnosisRecord = db.getRecordEx(queryTable, u'max(Diagnosis.id) as diagId', cond)
        if forceInt(diagnosisRecord.value('diagId')):
            table = db.table('DiagnosisDispansPlaned')
            newRecord = table.newRecord()
            newRecord.setValue('createDatetime', toVariant(currentDate))
            newRecord.setValue('createPerson_id', QtGui.qApp.userId)
            newRecord.setValue('modifyDatetime', toVariant(currentDate))
            newRecord.setValue('modifyPerson_id', QtGui.qApp.userId)
            newRecord.setValue('deleted', toVariant(0))
            newRecord.setValue('client_id', record.value('client_id'))
            newRecord.setValue('diagnosis_id', diagnosisRecord.value('diagId'))
            newRecord.setValue('person_id', record.value('person_id'))
            newRecord.setValue('year', endDate.year())
            newRecord.setValue('month', endDate.month())
            newRecord.setValue('planVisits', toVariant(1))
            newRecord.setValue('isExport', toVariant(1))
            db.insertRecord(table, newRecord)
        return True

# ###################################################################


class CF030DiagnosisTypeCol(CDiagnosisTypeCol):
    def __init__(self, title=u'Тип', fieldName='diagnosisType_id', width=5, diagnosisTypeCodes=[], smartMode=True, **params):
        CDiagnosisTypeCol.__init__(self, title, fieldName, width, diagnosisTypeCodes, smartMode, **params)
        self.namesF030 = [u'Закл', u'Осн', u'Соп', u'Осл']


    def toString(self, val, record):
        id = forceRef(val)
        if id in self.ids:
            return toVariant(self.namesF030[self.ids.index(id)])
        return QVariant()


    def setEditorData(self, editor, value, record):
        editor.clear()
        if value.isNull():
            value = record.value(self.fieldName())
        id = forceRef(value)
        if self.smartMode:
            if id == self.ids[0]:
                editor.addItem(self.namesF030[0], toVariant(self.ids[0]))
            elif id == self.ids[1]:
                if self.ids[0]:
                    editor.addItem(self.namesF030[0], toVariant(self.ids[0]))
                editor.addItem(self.namesF030[1], toVariant(self.ids[1]))
            else:
                editor.addItem(self.namesF030[2], toVariant(self.ids[2]))
                editor.addItem(self.namesF030[3], toVariant(self.ids[3]))
        else:
            for itemName, itemId in zip(self.namesF030, self.ids):
                if itemId:
                    editor.addItem(itemName, toVariant(itemId))
        currentIndex = editor.findData(toVariant(id))
        editor.setCurrentIndex(currentIndex)
