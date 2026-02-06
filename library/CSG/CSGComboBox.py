# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL

from library.Utils import forceRef, forceString
from library.DbComboBox import CDbComboBox, CDbData, CDbModel
from library.CSG.CSGComboBoxPopup import CCSGComboBoxPopup, TABLE_CSG, TABLE_CSG_MKB


__all__ = ('CCSGComboBox',
          )

defaultFilters = {'age': True,
                  'sex': True,
                  'csgServices': True,
                  'mkbCond': 2,
                  'isEventProfile': 1,
                  'MKBEx': None,
                  'duration': 0,
                 }




class CCSGDbData(CDbData):
    def __init__(self, eventEditor, mesServiceTemplate, MKB, eventProfileId, csgRecord, codeMask):
        CDbData.__init__(self)
        self.eventEditor = eventEditor
        self.clientBirthDate = eventEditor.clientBirthDate
        self.clientSex = eventEditor.clientSex
        self.eventBegDate = eventEditor.eventSetDateTime
        self.mesServiceTemplate = mesServiceTemplate
        self.codeMask = codeMask
        self.MKB = MKB
        self.eventProfileId = eventProfileId
        self.csgRecord = csgRecord


    def buildMKBCond(self, mkbCond, MKBvalue):
        tableCSGMkb  = QtGui.qApp.db.table(TABLE_CSG_MKB)
        if mkbCond == 2: # строгое соответствие
            return tableCSGMkb['mkb'].eq(MKBvalue)
        if mkbCond == 3: # по классу
            return tableCSGMkb['mkb'].like(MKBvalue[:1]+'%')
        # по рубрике
        return tableCSGMkb['mkb'].like(MKBvalue[:3]+'%')


    def select(self, filter):
        useSex = filter.get('sex', True)
        useAge = filter.get('age', True)
        useCsgServices = filter.get('csgServices', True)
        mkbCond = filter.get('mkbCond', 2)
        isEventProfile = filter.get('isEventProfile', 1)
        MKBEx = filter.get('MKBEx', None)
        duration = filter.get('duration', 0)
        self.idList = []
        self.strList = []
        db = QtGui.qApp.db
        opATList = []
        tabs = []
        if self.eventEditor and hasattr(self.eventEditor, 'tabStatus'):
            tabs.append(self.eventEditor.tabStatus)
        if self.eventEditor and hasattr(self.eventEditor, 'tabCure'):
            tabs.append(self.eventEditor.tabCure)
        if self.eventEditor and hasattr(self.eventEditor, 'tabDiagnostic'):
            tabs.append(self.eventEditor.tabDiagnostic)
        if self.eventEditor and hasattr(self.eventEditor, 'tabMisc'):
            tabs.append(self.eventEditor.tabMisc)
        for tab in tabs:
            for item in tab.modelAPActions._items:
                opATList.append(item[1]._actionType.id)
        tableCSG = db.table(TABLE_CSG)
        tableCSGMkb  = db.table(TABLE_CSG_MKB)
        tableCSGService = db.table('mes.CSG_Service')
        queryTable = tableCSG
        queryTable = queryTable.leftJoin(tableCSGService, tableCSGService['master_id'].eq(tableCSG['id']))
        queryTable = queryTable.leftJoin(tableCSGMkb,         tableCSGMkb['master_id'].eq(tableCSG['id']))
        cond  = [
            db.joinOr( [
                tableCSG['begDate'].isNull(),
                tableCSG['begDate'].signEx('<=', 'current_timestamp')
                ]),
            db.joinOr( [
                tableCSG['endDate'].isNull(),
                tableCSG['endDate'].signEx('>=', 'current_timestamp')
                ])
            ]

        servicePart = None
        mkbPart = None
        if opATList and useCsgServices:
            tableActionType = db.table('ActionType')
            tableService = db.table('rbService')
            table = tableActionType.leftJoin(tableService, tableService['id'].eq(tableActionType['nomenclativeService_id']))
            recordList = db.getRecordList(table, tableService['infis'], tableActionType['id'].inlist(opATList))
            codeList = [forceString(r.value('infis')) for r in recordList]
            servicePart = [tableCSGService['serviceCode'].inlist(codeList)]
            if mkbCond:
                servicePart.append(tableCSGService['mkb'].eq(self.MKB))
            else:
                servicePart.append(tableCSGService['mkb'].isNull())
            if servicePart:
                cond.append(db.joinAnd(servicePart))
        # elif self.mesServiceTemplate:
        #     joinOr = []
        #     for mesService in self.mesServiceTemplate:
        #         joinOr.append(tableCSGService['serviceCode'].like(forceString(mesService)))
        #     cond.append(db.joinOr(joinOr))

        if self.codeMask:
            cond.append(tableCSG['code'].regexp(self.codeMask))

        if duration:
            cond.append('%d BETWEEN %s AND %s' % (duration, tableCSG['minDuration'], tableCSG['maxDuration']))

        if isEventProfile and self.eventProfileId:
            tableMESGroup = db.table('mes.mrbMESGroup')
            eventProfileCode = forceString(db.translate('rbEventProfile', 'id', self.eventProfileId, 'code'))
            cond.append(tableMESGroup['deleted'].eq(0))
            cond.append(tableMESGroup['code'].like(eventProfileCode))
            queryTable = queryTable.innerJoin(tableMESGroup, tableMESGroup['id'].eq(tableCSG['group_id']))

        if self.MKB and mkbCond:
            subCond = self.buildMKBCond(mkbCond, self.MKB)
            if MKBEx:  # доп. мкб указан
                subCondEx = self.buildMKBCond(mkbCond, MKBEx)
                primary = [tableCSGMkb['blendingMKB'].eq(1), subCond]
                secondary = [tableCSGMkb['blendingMKB'].eq(2), subCondEx]
                mkbPart = [db.joinOr([db.joinAnd(primary), db.joinAnd(secondary)])]
            elif MKBEx == '':  #  не указан
                mkbPart = [subCond, tableCSGMkb['blendingMKB'].eq(0)]
            else:  # не учитывать
                mkbPart = [subCond]

            if not useCsgServices:
                mkbPart.append(tableCSGService['id'].isNull())
            mkbPart = db.joinAnd(mkbPart)
            if mkbPart:
                cond.append(mkbPart)

        if (self.clientSex and useSex) or (self.clientBirthDate and useAge):
            cond.append('SELECT(isSexAndAgeSuitable(IF(%s.sex = 0, 0, %s), %s, %s.sex, %s.age, %s))'%(
                tableCSG.name(),  self.clientSex, db.formatDate(self.clientBirthDate),
                tableCSG.name(), tableCSG.name(), db.formatDate(self.eventBegDate)))

        # csgCond = [x for x in (servicePart, mkbPart) if x is not None]
        # if not csgCond:
        #     csgCond = [None]
        # for dynCond in csgCond:
        #     recordList = db.getRecordList(queryTable, ["DISTINCT "+tableCSG['id'].name(), tableCSG['code'].name()],
        #                           where=cond+[dynCond] if dynCond else cond,
        #                           order='%s.code, %s.id' % (TABLE_CSG, TABLE_CSG))
        #     for record in recordList:
        #         self.idList.append(forceRef(record.value(0)))
        #         self.strList.append(forceString(record.value(1)))

        recordList = db.getRecordList(queryTable, ["DISTINCT " + tableCSG['id'].name(), tableCSG['code'].name()],
                                  where=cond,
                                  order='%s.code, %s.id' % (TABLE_CSG, TABLE_CSG))
        for record in recordList:
            self.idList.append(forceRef(record.value(0)))
            self.strList.append(forceString(record.value(1)))



class CCSGDbModel(CDbModel):
    def __init__(self, parent):
        CDbModel.__init__(self, parent)
        self.editor = parent
        self.dbdata = None

    def prepareData(self):
        self.dbdata = CCSGDbData(self.editor.eventEditor, self.editor.mesServiceTemplate, self.editor.MKB, self.editor.eventProfileId, self.editor.csgRecord, self.editor.codeMask)
        self.dbdata.select(self.editor.filterValues)


class CCSGComboBox(CDbComboBox):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                      )

    def __init__(self, eventEditor, mesServiceTemplate, MKB, eventProfileId, filter = None, parent = None):
        CDbComboBox.__init__(self, parent)
        self.filterValues = filter if filter else defaultFilters
        self.setModel(CCSGDbModel(self))
        self._popup = None
        self.csgId = None
        self.clientSex = 0
        self.clientBirthDate = None
        self.eventBegDate = None
        self.MKB = MKB
        self.eventProfileId = eventProfileId
        self.codeMask = None
        self._tableName = TABLE_CSG
        self.mesServiceTemplate = mesServiceTemplate
        self._addNone = True
        self._customFilter = None
        self.eventEditor = eventEditor
        self._popup = CCSGComboBoxPopup(self, eventEditor = self.eventEditor)
        self.connect(self._popup, SIGNAL('CSGSelected(int)'), self.setValue)


    def setCSGRecord(self, record):
        self.csgRecord = record
        self.model().prepareData()


    def setEventBegDate(self, date):
        self.eventBegDate = date


    def setClientSex(self, clientSex):
        self.clientSex = clientSex


    def setClientBirthDate(self, clientBirthDate):
        self.clientBirthDate = clientBirthDate


    def setCodeMask(self, mask):
        self.codeMask = mask


    def showPopup(self):
        pos = self.mapToGlobal(self.rect().bottomLeft())
        size = self._popup.sizeHint()
        width= max(size.width(), self.width())
        size.setWidth(width)
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
        pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
        self._popup.move(pos)
        self._popup.resize(size)
        self._popup.show()
        self._popup.setup(self.clientSex, self.clientBirthDate, self.MKB, self.value(), self.eventBegDate, self.mesServiceTemplate, self.codeMask, self.eventProfileId)

