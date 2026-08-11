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

from PyQt4.QtCore import QVariant
from PyQt4 import QtGui

from library.CSG.CSGComboBox import CCSGComboBox, CCSGDbData, defaultFilters
from library.InDocTable      import CInDocTableCol
from library.Utils import forceString, forceDouble, forceInt

u"""Столбики для редактирования КСГ"""

__all__ = ( 'CCSGInDocTableCol',
          )

class CCSGInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, filter, width, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self._clientBirthDate = None
        self._clientSex = None
        self._MESServiceTemplate=None
        self._eventBegDate = None
        self._MKB = None
        self._associatedMKB = None
        self._complicationMKB = None
        self._codeMask = None
        self._eventProfileId = None
        self._eventEditor = None
        self._filters = filter if filter else defaultFilters
        self._krit = None
        self._fractions = None
        self._csgBegDate = None
        self._csgEndDate = None


    def setEventEditor(self, eventEditor):
        self._eventEditor = eventEditor


    def getMostExpensiveCSG(self, record, filter=None):
        mkb = forceString(record.value('MKB'))
        dbdata = CCSGDbData(self._eventEditor, self._MESServiceTemplate, mkb, self._eventProfileId, record, None)
        filters = self._filters.copy()
        filters.update(filter)
        dbdata.select(filter)
        db = QtGui.qApp.db
        tblContract = db.table('Contract')
        tblContractTariff = db.table('Contract_Tariff')
        tblService = db.table('rbService')
        tblExpense = db.table('rbExpenseServiceItem')
        tblCCE = db.table('Contract_CompositionExpense')

        cols = [tblService['code'].name(), tblService['name'].name(), tblCCE['sum'].name(), tblExpense['name'].name(), tblExpense['code'].name()]
        cond = [tblContract['id'].eq(self._eventEditor.contractId), tblExpense['code'].eq('7'), tblContractTariff['deleted'].eq(0)]
        cond.append(tblService['code'].inlist(dbdata.strList))

        table = tblContract.innerJoin(tblContractTariff, tblContractTariff['master_id'].eq(tblContract['id']))
        table = table.innerJoin(tblService, tblService['id'].eq(tblContractTariff['service_id']))
        table = table.innerJoin(tblCCE, tblCCE['master_id'].eq(tblContractTariff['id']))
        table = table.innerJoin(tblExpense, tblExpense['id'].eq(tblCCE['rbTable_id']))
        recordList = db.getRecordList(table, cols, cond, order=tblCCE['sum'].name()+' DESC', limit=1)
#        """
#SELECT s.code, s.name, cce.sum, esi.name, esi.code
#FROM Contract c
#INNER JOIN Contract_Tariff ct ON (ct.master_id=c.id AND ct.deleted=0)
#INNER JOIN rbService s ON (ct.service_id=s.id)
#INNER JOIN Contract_CompositionExpense cce ON (cce.master_id=ct.id)
#INNER JOIN rbExpenseServiceItem esi ON (cce.rbTable_id=esi.id)
#WHERE c.id = %i
#AND esi.code = 7
#ORDER BY cce.sum DESC;
#        """%self._eventEditor.contractId
        if recordList:
            record = recordList[0]
            serviceCode = forceString(record.value(0))
            return (serviceCode, forceDouble(record.value(2)))
        elif len(dbdata.idList) == 1:
            return (dbdata.strList[0], 0)
        return (None, None)


    def createEditor(self, parent):
        editor = CCSGComboBox(self._eventEditor, self._MESServiceTemplate, self._MKB, self._eventProfileId, self._filters, parent)
        editor.setClientSex(self._clientSex)
        editor.setClientBirthDate(self._clientBirthDate)
        editor.setEventBegDate(self._eventBegDate)
        editor.setCodeMask(self._codeMask)
        editor.setKrit(forceString(QtGui.qApp.db.translate('soc_spr80', 'id', forceInt(self._krit), 'code')))
        editor.setAssociatedMKB(self._associatedMKB)
        editor.setComplicationMKB(self._complicationMKB)
        editor.setFractions(self._fractions)
        editor.setCsgBegDate(self._csgBegDate)
        editor.setCsgEndDate(self._csgEndDate)
        return editor


    def getEditorData(self, editor):
        return QVariant(editor.text())


    def setEventBegDate(self, date):
        self._eventBegDate = date


    def setClientSex(self, clientSex):
        self._clientSex = clientSex


    def setClientBirthDate(self, clientBirthDate):
        self._clientBirthDate = clientBirthDate


    def setMKB(self, MKB):
        self._MKB = MKB


    def setAssociatedMKB(self, associatedMKB):
        self._associatedMKB = associatedMKB


    def setComplicationMKB(self, complicationMKB):
        self._complicationMKB = complicationMKB


    def setEventProfileId(self, eventProfileId):
        self._eventProfileId = eventProfileId


    def setCsgCodeMask(self, mask):
        self._codeMask = mask


    def setCsgServiceTemplate(self, MESServiceTemplate):
        self._MESServiceTemplate = MESServiceTemplate


    def setKrit(self, krit):
        self._krit = krit


    def setFractions(self, fractions):
        self._fractions = fractions


    def setCsgBegDate(self, csgBegDate):
        self._csgBegDate = csgBegDate


    def setCsgEndDate(self, csgEndDate):
        self._csgEndDate = csgEndDate
