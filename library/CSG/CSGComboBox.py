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

from library.Utils import forceRef, forceString, forceDate
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
                  'showOnlyByContract': True
                 }




class CCSGDbData(CDbData):
    def __init__(self, eventEditor, mesServiceTemplate, MKB, eventProfileId, csgRecord, codeMask, krit=None,
                 associatedMKB=None, complicationMKB=None, fractions=None, csgBegDate=None, csgEndDate=None):
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
        self.krit = krit
        self.associatedMKB = associatedMKB
        self.complicationMKB = complicationMKB
        self.fractions = fractions
        self.csgBegDate = csgBegDate
        self.csgEndDate = csgEndDate


    def buildMKBCond(self, mkbCond, MKBvalue):
        tableCSGMkb  = QtGui.qApp.db.table(TABLE_CSG_MKB)
        if mkbCond == 2: # строгое соответствие
            return tableCSGMkb['mkb'].eq(MKBvalue)
        if mkbCond == 3: # по классу
            return tableCSGMkb['mkb'].like(MKBvalue[:1]+'%')
        # по рубрике
        return tableCSGMkb['mkb'].like(MKBvalue[:3]+'%')


    def buildMKBCondNew(self, mkbCond, MKBvalue, table, field):
        # tableCSGMkb  = QtGui.qApp.db.table(TABLE_CSG_MKB)
        if mkbCond == 2: # строгое соответствие
            return table[field].eq(MKBvalue)
        if mkbCond == 3: # по классу
            return table[field].like(MKBvalue[:1]+'%')
        # по рубрике
        return table[field].like(MKBvalue[:3]+'%')


    def select(self, filter):
        useSex = filter.get('sex', True)
        useAge = filter.get('age', True)
        useCsgServices = filter.get('csgServices', True)
        mkbCond = filter.get('mkbCond', 2)
        isEventProfile = filter.get('isEventProfile', 1)
        MKBEx = filter.get('MKBEx', None)
        duration = filter.get('duration', 0)
        showOnlyByContract = filter.get('showOnlyByContract', True)
        clientAge = self.eventEditor.clientAge
        self.idList = [None]
        self.strList = ['']
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

        tableActionType = db.table('ActionType')
        tableService = db.table('rbService')
        table = tableActionType.leftJoin(tableService,
                                         tableService['id'].eq(tableActionType['nomenclativeService_id']))
        recordList = db.getRecordList(table, tableService['infis'], tableActionType['id'].inlist(opATList))
        codeList = [forceString(r.value('infis')) for r in recordList]

        begDate = self.csgBegDate
        endDate = self.csgEndDate
        if not endDate and not begDate:
            begDate = forceDate(self.eventEditor.edtBegDate.date())
            endDate = forceDate(self.eventEditor.edtEndDate.date())
        if not endDate:
            endDate = begDate

        if not duration:
            duration = begDate.daysTo(endDate)

        vpId = forceRef(db.translate('EventType', 'id', self.eventEditor.eventTypeId, 'medicalAidType_id'))
        vpCode = forceString(db.translate('rbMedicalAidType', 'id', vpId, 'regionalCode'))
        vpname = ''
        if vpCode in ('11','12','301','302','401','402'):
            vpname = u'стационар'
        elif vpCode in ('41', '411', '42', '422', '43', '51', '511', '52', '522', '71', '72', '90'):
            vpname = u'дневной стационар'

        contractId = forceString(self.eventEditor.contractId) if self.eventEditor.contractId else '0'  # если в событии не указан договор
        if not showOnlyByContract:
            # если надо вывести ещё и те, на которые нет тарифа
            contractId += ',-1'

        # if self.codeMask:
        #     cond.append(tableService['infis'].regexp(self.codeMask))

        stmt = u"CALL getCSG_Group('{0}', '{1}', '{2}', '{3}', {4}, {5}, '{6}', '{7}', {8}, '{9}', '{10}', '{11}', '{12}', '{13}');".format(
            self.MKB, self.associatedMKB, self.complicationMKB, ",".join(codeList), forceString(clientAge[0]),
            forceString(clientAge[3]), u'М' if self.clientSex == 1 else u'Ж', begDate.toString('yyyy-MM-dd'),
            forceString(duration), vpname, endDate.toString('yyyy-MM-dd'), self.krit if self.krit else u'',
            forceString(self.fractions) if self.fractions else u'', contractId
        )
        query = db.query(stmt)

        # recordList = db.getRecordList(queryTable,
        #                                ["DISTINCT " + tableService['id'].name(), tableService['infis'].name()],
        #                                where=cond,
        #                                order='%s.infis, %s.id' % (tableService.name(), tableService.name()))

        csgRecords = []
        hasCsgWithDlit = False
        while query.next():
            record = query.record()
            dlit = forceString(record.value(2))
            if dlit:
                hasCsgWithDlit = True
            csgRecords.append((forceRef(record.value(0)), forceString(record.value(1)), dlit))

        for record in csgRecords:
            if record[2] and hasCsgWithDlit or not hasCsgWithDlit:
                self.idList.append(record[0])
                self.strList.append(record[1])


    def select_old(self, filter):
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
        tableSpr69 = db.table('soc_spr69')
        queryTable = tableCSG
        queryTable = queryTable.leftJoin(tableCSGService, tableCSGService['master_id'].eq(tableCSG['id']))
        queryTable = queryTable.leftJoin(tableCSGMkb,         tableCSGMkb['master_id'].eq(tableCSG['id']))
        queryTable = queryTable.leftJoin(tableSpr69, tableSpr69['ksgkusl'].eq(tableCSG['code']))
        cond  = [
            db.joinOr( [
                tableCSG['begDate'].isNull(),
                tableCSG['begDate'].signEx('<=', 'current_timestamp')
                ]),
            db.joinOr( [
                tableCSG['endDate'].isNull(),
                tableCSG['endDate'].signEx('>=', 'current_timestamp')
                ]),
            db.joinOr( [
                tableSpr69['datn'].isNull(),
                tableSpr69['datn'].signEx('<=', 'current_timestamp')
                ]),
            db.joinOr( [
                tableSpr69['dato'].isNull(),
                tableSpr69['dato'].signEx('>=', 'current_timestamp')
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

        if self.krit:
            cond.append(tableSpr69['KRIT'].eq(self.krit))
            
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
        self.dbdata = CCSGDbData(
            self.editor.eventEditor, self.editor.mesServiceTemplate, self.editor.MKB, self.editor.eventProfileId,
            self.editor.csgRecord, self.editor.codeMask, self.editor.krit, self.editor.associatedMKB,
            self.editor.complicationMKB, self.editor.fractions, self.editor.csgBegDate, self.editor.csgEndDate
        )
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
        # до CCSGTableModel значения, устанавливаемые после init не доходят
        # используем modelCsgCol, чтобы вытянуть установленные фильтры
        modelCsgCol = parent.parent().model().csgCol
        self.associatedMKB = modelCsgCol._associatedMKB
        self.complicationMKB = modelCsgCol._complicationMKB
        self.eventProfileId = eventProfileId
        self.codeMask = None
        self.krit = forceString(QtGui.qApp.db.translate('soc_spr80', 'id', forceRef(modelCsgCol._krit), 'code'))
        self.fractions = modelCsgCol._fractions
        self.csgBegDate = forceDate(modelCsgCol._csgBegDate)
        self.csgEndDate = forceDate(modelCsgCol._csgEndDate)
        self._tableName = TABLE_CSG
        self.mesServiceTemplate = mesServiceTemplate
        self._addNone = True
        self._customFilter = None
        self._contractId = eventEditor.contractId
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


    def setKrit(self, krit):
        self.krit = krit


    def setAssociatedMKB(self, associatedMKB):
        self.associatedMKB = associatedMKB


    def setComplicationMKB(self, complicationMKB):
        self.complicationMKB = complicationMKB


    def setFractions(self, fractions):
        self.fractions = fractions


    def setCsgBegDate(self, csgBegDate):
        self.csgBegDate = csgBegDate


    def setCsgEndDate(self, csgEndDate):
        self.csgEndDate = csgEndDate


    def setValue(self, itemId):
        rowIndex = max(self.model().searchId(itemId), 0)
        self.setCurrentIndex(rowIndex)


    def value(self):
        rowIndex = self.currentIndex()
        return self.model().getId(rowIndex)


    def setText(self, name):
        itemId = self.model().getIdByName(name)
        rowIndex = max(self.model().searchId(itemId), 0)
        self.setCurrentIndex(rowIndex)


    def text(self):
        rowIndex = self.currentIndex()
        return forceString(self.model().getName(rowIndex))


    def updateModel(self):
        itemText = self.text()
        self.model().update()
        self.setText(itemText)


    def showPopup(self):
        pos = self.mapToGlobal(self.rect().bottomLeft())
        size = self._popup.sizeHint()
        width= max(size.width(), self.width())
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        size.setWidth(screen.width())
        pos.setX(max(min(pos.x(), screen.right() - size.width()), screen.left()))
        pos.setY(max(min(pos.y(), screen.bottom() - size.height()), screen.top()))
        self._popup.move(pos)
        self._popup.resize(size)
        self._popup.show()
        self._popup.setup(
            self.clientSex, self.clientBirthDate, self.MKB, self.value(), self.eventBegDate, self.mesServiceTemplate,
            self.codeMask, self.eventProfileId, self.krit, self.associatedMKB, self.complicationMKB, self.fractions,
            self.csgBegDate, self.csgEndDate
        )

