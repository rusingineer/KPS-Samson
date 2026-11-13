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


from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import QVariant, pyqtSignature, Qt

from Events.Action import CActionTypeCache, CActionPropertyType
from Events.UserDictionaryList import UserDictionaryPropertyTypes
from library.CTableComboBox import CTableComboBox
from library.DialogBase import CDialogBase
from library.InDocTable import CRecordListModel, CInDocTableCol
from library.Utils import forceInt, forceRef, forceString, toVariant

from RefBooks.Person.List import getSamePersonIdList

from .Ui_UserDictionaryCopy import Ui_UserDictionaryCopyDialog


class CUserDictionaryCopyDialog(CDialogBase, Ui_UserDictionaryCopyDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.addModels('CopyUserDictionary', CCopyUserDictionaryModel(self))
        self.setModels(self.tblCopyUserDictionary, self.modelCopyUserDictionary, self.selectionModelCopyUserDictionary)
        self.cmbActionTypeSource.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
        self.cmbActionTypeSource.setMinimumContentsLength(12)
        self.cmbActionTypeNew.setClassesPopupVisible(True)
        self.cmbActionTypeSource.setClassesPopupVisible(True)
        self.progressBar.setVisible(False)
        self.modelCopyUserDictionary.addProgressBar(self.progressBar)


    def accept(self):
        self.modelCopyUserDictionary.copyUserDictionary()
        CDialogBase.accept(self)


    def loadItems(self):
        newActionTypeId = self.cmbActionTypeNew.value()
        sourceActionTypeId = self.cmbActionTypeSource.value()
        self.modelCopyUserDictionary.loadItems(newActionTypeId, sourceActionTypeId)


    @pyqtSignature('int')
    def on_cmbActionTypeSource_currentIndexChanged(self,  val):
        self.loadItems()


    @pyqtSignature('int')
    def on_cmbActionTypeNew_currentIndexChanged(self,  val):
        self.loadItems()


class CCopyUserDictionaryModel(CRecordListModel):
    class CSourceColumn(CInDocTableCol):
        def __init__(self, title, field, defaultWidth, model):
            CInDocTableCol.__init__(self, title, field, defaultWidth)
            self.model = model
            self.caches = {}


        def toString(self, val, record):
            actionPropertyTypeId = forceRef(val)
            if actionPropertyTypeId:
                actionPropertyType = self.caches.get(actionPropertyTypeId, None)
                if not actionPropertyType:
                    actionPropertyTypeRecord = QtGui.qApp.db.getRecordEx('ActionPropertyType', '*', 'id = {}'.format(actionPropertyTypeId))
                    actionPropertyType = CActionPropertyType(actionPropertyTypeRecord)
                    self.caches[actionPropertyTypeId] = actionPropertyType
                if actionPropertyType:
                    return toVariant(actionPropertyType.name)
            return QVariant()
        

        def createEditor(self, parent):
            editor = CTableComboBox(parent)
            editor.setTable('ActionPropertyType',
                            True,
                            '',
                            ',name',
                            [u'Наименование'],
                            isView=False
                            )
            return editor


        def getEditorData(self, editor):
            return QVariant(editor.value())


        def setEditorData(self, editor, value, record):
            typeName = forceString(record.value('typeName'))
            cond = u"deleted = 0 AND actionType_id = {} AND typeName = '{}'".format(self.model.sourceActionTypeId, typeName)
            editor.setFilter(cond)
            editor.setValue(forceInt(value))
        
        
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CCopyUserDictionaryModel.CSourceColumn(u'Назначение', 'idNew', 2, self)).setReadOnly()
        self.addCol(CCopyUserDictionaryModel.CSourceColumn(u'Источник', 'idSource', 2, self))
        self.addHiddenCol('typeName')
        self.progressBar = None
        self.personId = QtGui.qApp.userId
        self.personIdList = getSamePersonIdList(QtGui.qApp.userId)
        self.newActionTypeId = None
        self.sourceActionTypeId = None
    
    
    def addProgressBar(self, progressBar):
        self.progressBar = progressBar


    def loadItems(self, newActionTypeId, sourceActionTypeId):
        self.newActionTypeId = newActionTypeId
        self.sourceActionTypeId = sourceActionTypeId
        if newActionTypeId and sourceActionTypeId:
            db = QtGui.qApp.db
            tableActionType = db.table('ActionType')
            tableActionPropertyType = db.table('ActionPropertyType')
            sourceActionType = CActionTypeCache.getById(sourceActionTypeId)
            
            table = tableActionType.leftJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
            cols = [
                    tableActionPropertyType['id'].alias('idNew'),
                    tableActionPropertyType['name'],
                    tableActionPropertyType['shortName'],
                    tableActionPropertyType['typeName']
                    ]
            cond = [
                tableActionType['deleted'].eq(0),
                tableActionPropertyType['deleted'].eq(0),
                tableActionType['id'].eq(newActionTypeId),
                tableActionPropertyType['typeName'].inlist(UserDictionaryPropertyTypes)
            ]
            items = QtGui.qApp.db.getRecordList(table, cols=cols, where=cond)
            for item in items:
                item.append(QtSql.QSqlField('idSource', QVariant.Int))
                name = forceString(item.value('name'))
                shortName = forceString(item.value('shortName'))
                sourcePropertyType = None
                if sourceActionType.hasProperty(name):
                    sourcePropertyType = sourceActionType.getPropertyType(name)
                elif shortName in sourceActionType.getPropertiesByShortName():
                    sourcePropertyType = sourceActionType.getPropertyTypeByShortName(shortName)
                if sourcePropertyType:
                    newTypeName = forceString(item.value('typeName'))
                    if newTypeName == sourcePropertyType.typeName:
                        item.setValue('idSource', sourcePropertyType.id)
            self.setItems(items)
        else:
            self.setItems([])
        
    
    def getUserDictionary(self, actionPropertyTypeIdList):
        db = QtGui.qApp.db
        tableUserDictionary = db.table('UserDictionary')
        cond = [
            tableUserDictionary['person_id'].inlist(self.personIdList),
            tableUserDictionary['actionPropertyType_id'].inlist(actionPropertyTypeIdList),
        ]
        cols = [
            tableUserDictionary['actionPropertyType_id'],
            tableUserDictionary['text'],
        ]
        recordList = QtGui.qApp.db.getRecordList(tableUserDictionary, cols, where=cond)
        return recordList
    
    
    def copyUserDictionary(self):
        db = QtGui.qApp.db
        copiedProperties = []
        newPropertyTypeIds = set()
        sourcePropertyTypeIds = set()
        propertyIdMap = {}
        for item in self.items():
            idSource = forceRef(item.value('idSource'))
            idNew = forceRef(item.value('idNew'))
            if idSource:
                copiedProperties.append((idNew, idSource))
                newPropertyTypeIds.add(idNew)
                sourcePropertyTypeIds.add(idSource)
        if copiedProperties:
            sourceRecords = self.getUserDictionary(list(sourcePropertyTypeIds))
            existingRecords = self.getUserDictionary(list(newPropertyTypeIds))
            existingSet = set()
            for record in existingRecords:
                propertyTypeId = forceRef(record.value('actionPropertyType_id'))
                text = forceString(record.value('text'))
                existingSet.add((propertyTypeId, text))
            sourceMap = {}
            for record in sourceRecords:
                propertyTypeId = forceRef(record.value('actionPropertyType_id'))
                text = forceString(record.value('text'))
                if propertyTypeId not in sourceMap:
                    sourceMap[propertyTypeId] = []
                sourceMap[propertyTypeId].append(text)
            newRecords = []
            tableUserDictionary = db.table('UserDictionary')
            for idNew, idSource in copiedProperties:
                sourceTexts = sourceMap.get(idSource, [])
                for text in sourceTexts:
                    if (idNew, text) not in existingSet:
                        newRecord = tableUserDictionary.newRecord()
                        newRecord.setValue('person_id', self.personId)
                        newRecord.setValue('actionPropertyType_id', idNew)
                        newRecord.setValue('text', text)
                        newRecords.append(newRecord)
            self.progressBar.setValue(0)
            self.progressBar.setMaximumWidth(len(newRecords))
            self.progressBar.setVisible(True)
            db.transaction()
            try:
                for newRecord in newRecords:
                    db.insertRecord(tableUserDictionary, newRecord)
                    self.progressBar.setValue(self.progressBar.value() + 1)
                db.commit()
            except:
                db.rollback()
            finally:
                self.progressBar.setVisible(False)
