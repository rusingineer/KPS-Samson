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
from PyQt4.QtCore import Qt, QEvent, pyqtSignature, SIGNAL, QVariant

from library.database   import CTableRecordCache
from library.TableModel import CTableModel, CTextCol
from library.Utils      import getPref, setPref, forceRef, forceString, forceDate, forceInt
from Events.ActionProperty import CActionPropertyValueTypeRegistry
from Events.ActionStatus  import CActionStatus

from Events.Ui_PropertyValueToTemplateComboBoxPopup import Ui_PropertyValueToTemplateComboBoxPopup

__all__ = [ 'CPropertyValueToTemplateComboBoxPopup',
          ]


class CPropertyValueToTemplateComboBoxPopup(QtGui.QFrame, Ui_PropertyValueToTemplateComboBoxPopup):
    __pyqtSignals__ = ('propertyValueToTemplateSelected(int)'
                      )

    def __init__(self, parent):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.tableModel = CPropertyValueToTemplateTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblPropertyTemplate.setModel(self.tableModel)
        self.tblPropertyTemplate.setSelectionModel(self.tableSelectionModel)
        self.clientId = None
        self.templateId = None
        self.headers = []
        self.items = {}
        self._eventEditor = None
        self.tblPropertyTemplate.installEventFilter(self)
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CPropertyValueToTemplateComboBoxPopup', {})
        self.tblPropertyTemplate.loadPreferences(preferences)


    def setClientId(self, clientId):
        self.clientId = clientId


    def setEventEditor(self, eventEditor):
        self._eventEditor = eventEditor


    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent!=None:
            opt=QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(
                QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if (arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos())):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)


    def closeEvent(self, event):
        preferences = self.tblPropertyTemplate.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CPropertyValueToTemplateComboBoxPopup', preferences)
        QtGui.QFrame.closeEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.tblPropertyTemplate:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblPropertyTemplate.currentIndex()
                self.tblPropertyTemplate.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)


    def updateIdList(self):
        QtGui.qApp.setWaitCursor()
        try:
            crIdList = self.getPropertyTemplateIdList()
            crIdList = self.items.keys()
            self.setPropertyTemplateIdList(crIdList, self.templateId)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def updateIdListEx(self):
        QtGui.qApp.setWaitCursor()
        try:
            if not self.items:
                crIdList = self.getPropertyTemplateIdList()
            else:
                crIdList = self.items.keys()
            self.setPropertyTemplateIdList(crIdList, self.templateId)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def setValue(self, value):
        self.templateId = value


    def setPropertyTemplateIdList(self, idList, posToId):
        self.tblPropertyTemplate.setIdList(idList, posToId)
        self.tblPropertyTemplate.setFocus(Qt.OtherFocusReason)


    def loadHeader(self):
        self.headers = []
        if self.clientId:
            db = QtGui.qApp.db
            tableMonitoring = db.table('Client_Monitoring')
            tableAPTemplate = db.table('ActionPropertyTemplate')
            queryTable = tableMonitoring.innerJoin(tableAPTemplate, tableAPTemplate['id'].eq(tableMonitoring['propertyTemplate_id']))
            cond = [tableAPTemplate['isCalcParamDoseNomenclatureExpense'].eq(1),
                    tableMonitoring['deleted'].eq(0),
                    tableAPTemplate['deleted'].eq(0),
                    tableMonitoring['client_id'].eq(self.clientId)
                    ]
            cols = [tableAPTemplate['id'],
                    tableAPTemplate['name']
                    ]
            records = db.getRecordList(queryTable, cols, cond, order='ActionPropertyTemplate.code, ActionPropertyTemplate.name')
            for record in records:
                templateId = forceRef(record.value('id'))
                if templateId and templateId not in self.headers:
                    self.headers.append(templateId)


    def getValueProperties(self):
        self.headers = []
        self.items = {}
        propertyIdHeader = []
        if not self.clientId:
            return
        self.loadHeader()
        if len(self.headers) > 1:
            for i, header in enumerate(self.headers):
                propertyIdHeader.append(header)
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            tableActionProperty = db.table('ActionProperty')
            tableActionPropertyType = db.table('ActionPropertyType')
            tableMonitoring = db.table('Client_Monitoring')
            tableAPTemplate = db.table('ActionPropertyTemplate')
            queryTable = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
            queryTable = queryTable.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAPTemplate, tableAPTemplate['id'].eq(tableActionPropertyType['template_id']))
            queryTable = queryTable.innerJoin(tableMonitoring, tableMonitoring['propertyTemplate_id'].eq(tableAPTemplate['id']))
            cond = [tableEvent['client_id'].eq(self.clientId),
                    tableAPTemplate['isCalcParamDoseNomenclatureExpense'].eq(1),
                    tableEvent['deleted'].eq(0),
                    tableAction['deleted'].eq(0),
                    tableAction['endDate'].isNotNull(),
                    tableActionPropertyType['template_id'].isNotNull(),
                    tableActionType['deleted'].eq(0),
                    tableActionPropertyType['deleted'].eq(0),
                    tableAPTemplate['deleted'].eq(0),
                    tableMonitoring['deleted'].eq(0),
                    tableActionProperty['deleted'].eq(0),
                    tableActionPropertyType['template_id'].inlist(propertyIdHeader),
                    tableActionProperty['type_id'].eq(tableActionPropertyType['id'])
                    ]
            cols = [u'DISTINCT ActionPropertyType.typeName, ActionPropertyType.valueDomain',]
            records = db.getRecordList(queryTable, cols, cond)
            cols = [tableAction['endDate'],
                    tableActionPropertyType['template_id'],
                    tableActionPropertyType['typeName'],
                    tableActionPropertyType['valueDomain']
                    ]
            for record in records:
                queryTableProperty = queryTable
                typeName = forceString(record.value('typeName'))
                valueDomain = forceString(record.value('valueDomain'))
                propertyType = CActionPropertyValueTypeRegistry.get(typeName, valueDomain)
                if propertyType:
                    tablePropertyType = db.table(propertyType.getTableName())
                    queryTableProperty = queryTableProperty.leftJoin(tablePropertyType, db.joinAnd([tablePropertyType['id'].eq(tableActionProperty['id']), tablePropertyType['value'].trim()+' IS NOT NULL']))
                    cols.append(tablePropertyType['value'].alias('value'+typeName))
                    queryTable = queryTableProperty
            if len(cols) > 4:
                order = [u'Action.endDate DESC']
                records = db.getDistinctRecordList(queryTable, cols, cond, order)
                for record in records:
                    templateId = forceRef(record.value('template_id'))
                    endDate = forceDate(record.value('endDate'))
                    if templateId and endDate:
                        typeName = forceString(record.value('typeName'))
                        valueDomain = forceString(record.value('valueDomain'))
                        value = record.value('value'+typeName)
                        propertyType = CActionPropertyValueTypeRegistry.get(typeName, valueDomain)
                        if propertyType:
                            valueProperty = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                            if valueProperty:
                                if type(valueProperty) is int:
                                    reportLine = self.items.setdefault(templateId, (0, None))
                                    if not reportLine[1] or reportLine[1] < endDate:
                                        reportLine = (valueProperty, endDate)
                                        self.items[templateId] = reportLine
                                elif type(valueProperty) is float:
                                    reportLine = self.items.setdefault(templateId, (0.0, None))
                                    if not reportLine[1] or reportLine[1] < endDate:
                                        reportLine = (valueProperty, endDate)
                                        self.items[templateId] = reportLine
        self.getCalculationParamValuePropertiesCurrentEvent()


    def getCalculationParamValuePropertiesCurrentEvent(self):
        if self._eventEditor:
            db = QtGui.qApp.db
            tableAPTemplate = db.table('ActionPropertyTemplate')
            templateIdList = db.getDistinctIdList(tableAPTemplate, [tableAPTemplate['id']], [tableAPTemplate['isCalcParamDoseNomenclatureExpense'].eq(1)])
            if templateIdList:
                tabs = self._eventEditor.getActionsTabsList()
                for tab in tabs:
                    groups = tab.modelAPActions._items._groups
                    for group in groups:
                        mapItem2Row = group._mapItem2Row
                        for item, row in mapItem2Row.items():
                            if item.action:
                                actionType = item.action.getType()
                                for propertyType in actionType.getPropertiesById().values():
                                    templateId = propertyType.templateId
                                    if templateId and templateId in templateIdList:
                                        record = item.action.getRecord()
                                        endDate = forceDate(record.value('endDate'))
                                        if endDate and forceInt(record.value('status')) == CActionStatus.finished:
                                            value = item.action.getPropertyById(propertyType.id).getValue()
                                            valueProperty = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                                            if valueProperty:
                                                if type(valueProperty) is int:
                                                    reportLine = self.items.setdefault(templateId, (0, None))
                                                    if not reportLine[1] or reportLine[1] < endDate:
                                                        reportLine = (valueProperty, endDate)
                                                        self.items[templateId] = reportLine
                                                elif type(valueProperty) is float:
                                                    reportLine = self.items.setdefault(templateId, (0.0, None))
                                                    if not reportLine[1] or reportLine[1] < endDate:
                                                        reportLine = (valueProperty, endDate)
                                                        self.items[templateId] = reportLine


    def getPropertyTemplateIdList(self):
        self.getValueProperties()
        idList = self.items.keys()
        return idList


    def getPropertyValue(self, templateId):
        valueProperty = None
        if templateId:
            valueProperty = self.items.get(templateId, None)
        return valueProperty


    def setValuePropertyToTemplateItems(self, items):
        self.headers = []
        self.items = items


    def getValuePropertyToTemplateItems(self):
        return self.items


    def selectTemplateId(self, value):
        self.templateId = value
        self.emit(SIGNAL('propertyValueToTemplateSelected(int)'), self.templateId)
        self.close()


    @pyqtSignature('QModelIndex')
    def on_tblPropertyTemplate_doubleClicked(self, index):
        if index.isValid():
            if (Qt.ItemIsEnabled & self.tableModel.flags(index)):
                templateId = self.tblPropertyTemplate.currentItemId()
                self.selectTemplateId(templateId)


class CPropertyValueToTemplateTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Код', ['code'], 30))
        self.addColumn(CTextCol(u'Наименование', ['name'], 30))
        self.setTable('ActionPropertyTemplate')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        tableActionPropertyTemplate = db.table('ActionPropertyTemplate')
        loadFields = [u'''DISTINCT ActionPropertyTemplate.code, ActionPropertyTemplate.name''']
        self._table = tableActionPropertyTemplate
        self._recordsCache = CTableRecordCache(db, self._table, loadFields)

