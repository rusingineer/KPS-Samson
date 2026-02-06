# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4                  import QtGui
from PyQt4.QtCore import QVariant, QDate

from library.CustomComboBoxLike import CCustomComboBoxLike
from library.TNMS.TNMSPopup import CTNMSPopup
from library.InDocTable     import CInDocTableCol
from library.Utils          import forceString, forceRef
from library.adjustPopup    import adjustPopupToWidget

__all__ = ( 'CTNMSComboBox',
            'CTNMSCol',
          )


class CTNMSComboBox(CCustomComboBoxLike):
    def __init__(self, parent = None):
        CCustomComboBoxLike.__init__(self, parent)
        self.MKB = None
        self.isTest = False
        self.endDate = None


    def showPopup(self):
        if self._popup is None:
            self._popup = self.createPopup()
        self._popup.installEventFilter(self)
        adjustPopupToWidget(self, self._popup)
        self.updatePopupBeforeShow()
        self.updateValueFromPopup()
        self._popup.show()
        self._popup.setFocus()

    def updatePopupBeforeShow(self):
        # вынесено в отдельную функцию для использования в проверке заполнения TNMS в обращении
        self._popup.setEndDate(self.endDate)
        self._popup.setTempValue(CCustomComboBoxLike.getValue(self))
        mkbO = None
        if self.endDate and self.endDate >= QDate(2025, 7, 1):
            mkbO = forceString(QtGui.qApp.db.translate('soc_M002', 'mkb10', self.MKB, 'mkbO'))
        self._popup.updateItemsComboBoxes(mkbO if mkbO else self.MKB, self.isTest)

    def setIsTest(self, value):
        self.isTest = value


    def setMKB(self, value):
        self.MKB = value


    def setEndDate(self, date):
        self.endDate = date


    def setValue(self, tnmsString, tnmsIdList={}):
        value = [convertTNMSStringToDict(unicode(forceString(tnmsString))),
                 tnmsIdList]
        CCustomComboBoxLike.setValue(self, value)


    def valueAsString(self, value):
        return convertTNMSDictToDigest(value)


    def getValue(self):
        valueTNMS, tnmsIdList = CCustomComboBoxLike.getValue(self)
        return convertTNMSDictToString(valueTNMS), tnmsIdList


    def createPopup(self):
        return CTNMSPopup(self)


    def setValueToPopup(self):
        valueTNMS, tnmsIdList = CCustomComboBoxLike.getValue(self)
        self._popup.setValue(tnmsIdList)


    def updateValueFromPopup(self):
        CCustomComboBoxLike.setValue(self, self._popup.getValue())


def convertTNMSStringToDict(s):
    result = {}
    mode = 0  # 0: initial, 1: prefix entered, 2: arg code entered
    prefix = ''
    param = ''
    value = ''

    for c in s:
        if mode == 0:
            if c in 'cp':
                prefix = c
                mode = 1
                continue
            elif c.isspace():
                mode = 0
            prefix = ''
            mode = 1
        if mode == 1:
            if c in 'TNMS':
                mode = 2
                param = c
                value = ''
                continue
            else:
                mode = 3
        if mode == 2:
            if c.isspace():
                mode = 4
            else:
                value += c
            continue

        if mode == 3:
            if c.isspace():
                mode = 0
                continue

        if mode == 4:
            if c in 'cp':
                result[prefix + param] = value
                prefix = c
                mode = 1
                continue
            else:
                mode = 2
                value += ' ' + c
                continue

    if mode == 2:
        result[prefix+param] = value
    return result


def convertTNMSDictToString(d):
    l = []
#    digest = {}
    if d:
        for prefix in 'cp':
            for param in 'TNMS':
                key = prefix + param
                value = d.get(key,'')
                if value:
                    l.append(key+value)
#            if value != '':
#                digest[param] = value
#       l.append('|')
#       for param in 'NNMS':
#           value = digest.get(param,'')
#           l.append(param+value)

    return ' '.join(l)


def convertTNMSDictToDigest(d):
    parts = {}
    prefixDict = {}
    values = d.values()
    countX = values.count(u'')
    countValues = len(values)
    if countX >= 0 and countX < countValues:
        for param in 'TNMS':
            for prefix in 'cp':
                key = prefix + param
                value = d.get(key,'')
                if value != u'':
                    prefixDict[prefix] = True
        for param in 'TNMS':
            for prefix in 'cp':
                key = prefix + param
                value = d.get(key,'')
                if prefixDict.get(prefix, False):
                    parts.setdefault(prefix, []).append(param+value)
    return ' '.join('%s(%s)' % (param, ' '.join(parts[param]))
                    for param in sorted(parts.keys())
                   )


def convertTNMSDictToId(s, mkb):
    db = QtGui.qApp.db
    def getTNMSId(val, mkb, table, isTNMphase = False):
        if val:
            tableTNMS = db.table(table)
            cond = [tableTNMS['MKB'].like(mkb)]
            if isTNMphase:
                cond.append('''code LIKE '%s' '''%(val))
            else:
                cond.append('''RIGHT(code, LENGTH(code)-1) LIKE '%s' '''%(val))
            record = db.getRecordEx(tableTNMS, ['id'], cond, 'id')
            id = forceRef(record.value('id')) if record else None
            if not id and len(mkb) > 3:
                id = getTNMSId(val, mkb[:3], table, isTNMphase)
            if not id:
                id = getTNMSId(val, '', table, isTNMphase)
            return id
        return None

    d = convertTNMSStringToDict(s)
    if d and mkb:
        cT = d.get('cT','')
        cTId = getTNMSId(cT, mkb, 'rbTumor')
        cN = d.get('cN','')
        cNId = getTNMSId(cN, mkb, 'rbNodus')
        cM = d.get('cM','')
        cMId = getTNMSId(cM, mkb, 'rbMetastasis')
        cS = d.get('cS','')
        cSId = getTNMSId(cS, mkb, 'rbTNMphase', True)

        pT = d.get('pT','')
        pTId = getTNMSId(pT, mkb, 'rbTumor')
        pN = d.get('pN','')
        pNId = getTNMSId(pN, mkb, 'rbNodus')
        pM = d.get('pM','')
        pMId = getTNMSId(pM, mkb, 'rbMetastasis')
        pS = d.get('pS','')
        pSId = getTNMSId(pS, mkb, 'rbTNMphase', True)

        return [cTId, cNId, cMId, cSId, pTId, pNId, pMId, pSId]
    else:
        return [None]*8


class CTNMSCol(CInDocTableCol):
    def __init__(self, title, fieldName, width, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.MKB = None


    def setMKB(self, MKB):
        self.MKB = MKB


    def toString(self, val, record):
        return QVariant(convertTNMSDictToDigest(convertTNMSStringToDict(forceString(val))))


    def createEditor(self, parent):
        editor = CTNMSComboBox(parent)
        editor.setMKB(self.MKB)
        return editor


    def setEditorData(self, editor, value, record):
        from Events.EventEditDialog import CEventEditDialog
        valueList = value.toList()
        valueTNMS = valueList[0]
        tnmsMap = valueList[1].toMap()
        tnmsIdList = {}
        for name, TNMSId in tnmsMap.items():
            if name in CEventEditDialog.TNMSFieldsDict.keys():
                tnmsIdList[forceString(name)] = forceRef(TNMSId)
        editor.setValue(valueTNMS, tnmsIdList)


    def getEditorData(self, editor):
        return QVariant(list(editor.getValue()))
