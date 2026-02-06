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


from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QEvent, pyqtSignature, SIGNAL, QVariant

from Registry.RegistryTable import CSNILSCol
from library.database       import CTableRecordCache
from library.TableModel     import CTableModel, CDateCol, CEnumCol, CTextCol, CDesignationCol
from library.Utils          import forceInt, forceString, forceRef, getPref, setPref, toVariant
# from Users.Rights         import urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry

from Ui_ClientRelationSimpleComboBoxPopup import Ui_ClientRelationSimpleComboBoxPopup

__all__ = [ 'CClientRelationSimpleComboBoxPopup',
          ]


class CClientRelationSimpleComboBoxPopup(QtGui.QFrame, Ui_ClientRelationSimpleComboBoxPopup):
    __pyqtSignals__ = ('relatedClientIdSelected(int)'
                      )

    def __init__(self, parent = None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.needSNILS = parent.getNeedSNILS()
        self.tableModel = CClientRelationSimpleTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblClientRelation.setModel(self.tableModel)
        self.tblClientRelation.setSelectionModel(self.tableSelectionModel)
        self.date = None
        self.code = None
        self.clientId = None
        self.clientLowerId = None
        self.regAddressInfo = {}
        self.logAddressInfo = {}
        self.dialogInfo = {}
        self.tblClientRelation.installEventFilter(self)
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CClientRelationComboBoxPopup', {})
        self.tblClientRelation.loadPreferences(preferences)


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
        preferences = self.tblClientRelation.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CClientRelationSimpleComboBoxPopup', preferences)
        QtGui.QFrame.closeEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.tblClientRelation:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblClientRelation.currentIndex()
                self.tblClientRelation.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)


    def setClientLowerId(self, clientLowerId):
        self.clientLowerId = clientLowerId


    def setClientRelationTable(self):
        self.setClientRelationIdList(self.getClientRelationIdList(), self.clientId)


    def setClientRelationIdList(self, idList, posToId):
        self.tblClientRelation.setIdList(idList, posToId)
        self.tblClientRelation.setFocus(Qt.OtherFocusReason)


    def getClientRelationIdList(self):
        if self.clientId:
            clientId = self.clientId
            idList = []
        else:
            clientId = QtGui.qApp.currentClientId()
            if self.clientLowerId:
                idList = []
            else:
                idList = [clientId]
        if not clientId:
            return []
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableDocument = db.table('ClientDocument')
        tableAddress = db.table('ClientAddress')
        tableDocumentType = db.table('rbDocumentType')
        tableCRR = db.table('ClientRelation').alias('CRR')
        tableCRC = db.table('ClientRelation').alias('CRC')
        queryTable = tableClient.leftJoin(tableCRR, db.joinAnd([tableCRR['relative_id'].eq(tableClient['id']), tableCRR['deleted'].eq(0)]))
        queryTable = queryTable.leftJoin(tableCRC, db.joinAnd([tableCRC['client_id'].eq(tableClient['id']), tableCRC['deleted'].eq(0)]))
        queryTable = queryTable.leftJoin(tableAddress, db.joinAnd([tableClient['id'].eq(tableAddress['client_id']), tableAddress['deleted'].eq(0)]))
        queryTable = queryTable.leftJoin(tableDocument, db.joinAnd([tableClient['id'].eq(tableDocument['client_id']), tableDocument['deleted'].eq(0)]))
        queryTable = queryTable.leftJoin(tableDocumentType, tableDocument['documentType_id'].eq(tableDocumentType['id']))
        cond = [tableClient['deleted'].eq(0),
                tableClient['id'].eq(clientId)
                ]
        if self.clientLowerId and not isinstance(self.clientLowerId, list):
            cond.append(tableCRC['relative_id'].ne(self.clientLowerId))
        orderList = ['Client.lastName', 'Client.firstName', 'Client.patrName']
        orderStr = ', '.join([fieldName for fieldName in orderList])
        cols = [u'DISTINCT Client.id AS clientId',
                tableCRR['client_id'].alias('cRRClientId'),
                tableCRC['relative_id'].alias('relativeId')
                ]
        records = db.getRecordList(queryTable, cols, where=cond, order=orderStr, limit=1000)
        for record in records:
            clientIdRec = forceRef(record.value('id'))
            if clientIdRec and clientIdRec not in idList:
                idList.append(clientIdRec)
            cRRClientId = forceRef(record.value('cRRClientId'))
            if cRRClientId and cRRClientId not in idList:
                idList.append(cRRClientId)
            relativeId = forceRef(record.value('relativeId'))
            if relativeId and relativeId not in idList:
                idList.append(relativeId)
        if idList:
            queryTable = tableClient.leftJoin(tableAddress, db.joinAnd([tableClient['id'].eq(tableAddress['client_id']), tableAddress['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableDocument, db.joinAnd([tableClient['id'].eq(tableDocument['client_id']), tableDocument['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableDocumentType, tableDocument['documentType_id'].eq(tableDocumentType['id']))
            cond = [tableClient['id'].inlist(idList),
                    tableClient['deleted'].eq(0)
                    ]
            idList = db.getDistinctIdList(queryTable, tableClient['id'].name(), where=cond, order=orderStr, limit=1000)
        if idList and self.clientLowerId and isinstance(self.clientLowerId, list):
            idList = list(set(idList) - set(self.clientLowerId))
        return idList


    def setDate(self, date):
        self.tableModel.date = date


    def setClientRelationCode(self, code, clientId, regAddressInfo, logAddressInfo):
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        self.code = code
        self.clientId = clientId
        self.tableModel.setClientId(self.clientId if self.clientId else QtGui.qApp.currentClientId())
        self.regAddressInfo = regAddressInfo
        self.logAddressInfo = logAddressInfo
        idList = []
        id = None
        if code:
            record = db.getRecordEx(tableClient, [tableClient['id']], [tableClient['deleted'].eq(0), tableClient['id'].eq(code)])
            if record:
                id = forceInt(record.value(0))
            if id:
                idList = [id]
        self.setClientRelationIdList(idList, id)


    def selectClientRelationCode(self, code):
        self.code = code
        self.emit(SIGNAL('relatedClientIdSelected(int)'), code)
        self.close()


    def getCurrentClientRelationCode(self):
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        id = self.tblClientRelation.currentItemId()
        code = None
        if id:
            record = db.getRecordEx(tableClient, [tableClient['id']], [tableClient['deleted'].eq(0), tableClient['id'].eq(id)])
            if record:
                code = forceInt(record.value(0))
            return code
        return None


    @pyqtSignature('QModelIndex')
    def on_tblClientRelation_doubleClicked(self, index):
        if index.isValid():
            if (Qt.ItemIsEnabled & self.tableModel.flags(index)):
                code = self.getCurrentClientRelationCode()
                self.selectClientRelationCode(code)


class CClientRelationSimpleTableModel(CTableModel):

    class CRelationTypeCol(CDesignationCol):
        def __init__(self, title, fields, designationChain, defaultWidth, alignment='l'):
            CDesignationCol.__init__(self, title, fields, designationChain, defaultWidth, alignment)
            db = QtGui.qApp.db
            self.clientId = None
            if not isinstance(designationChain, list):
                designationChain = [designationChain]
            self._caches = []
            for tableName, fieldName in designationChain:
                self._caches.append(CTableRecordCache(db, tableName))

        def setClientId(self, clientId):
            self.clientId = clientId

        def format(self, values):
            val = values[0]
            clientId = values[1].toInt()[0]
            relativeId = values[2].toInt()[0]
            for cache in self._caches:
                recordId  = val.toInt()[0]
                if recordId:
                    record = cache.get(recordId)
                    if record:
                        code = forceString(record.value('code'))
                        leftName = forceString(record.value('leftName'))
                        rightName = forceString(record.value('rightName'))
                        if self.clientId:
                            if self.clientId == clientId:
                                val = toVariant(code + u' | ' + leftName + u'->' + rightName)
                            elif self.clientId == relativeId:
                                val = toVariant(code + u' | ' + rightName + u'->' + leftName)
                        else:
                            val = toVariant(code + u' | ' + leftName + u'->' + rightName)
                    else:
                        return QVariant()
                else:
                    return QVariant()
            return val

    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CClientRelationSimpleTableModel.CRelationTypeCol(u'Связь', ['relativeTypeId', 'clientId', 'relativeId'], ('rbRelationType', 'code'),   20))
        self.addColumn(CTextCol(u'Фамилия', ['lastName'], 30))
        self.addColumn(CTextCol(u'Имя', ['firstName'], 30))
        self.addColumn(CTextCol(u'Отчество', ['patrName'], 30))
        if parent.needSNILS:
            self.addColumn(CSNILSCol(u'СНИЛС', ['SNILS'], 35))
        self.addColumn(CTextCol(u'Номер клиента', ['id'], 20))
        self.addColumn(CEnumCol(u'Пол', ['sex'], ['', u'М', u'Ж'], 10))
        self.addColumn(CDateCol(u'Дата рождения', ['birthDate'], 20, highlightRedDate=False))
        self.addColumn(CTextCol(u'Адрес регистрации', ['regAddress'], 20))
        self.addColumn(CTextCol(u'Адрес проживания', ['logAddress'], 20))
        self.addColumn(CTextCol(u'Тип документа', ['name'], 20))
        self.addColumn(CTextCol(u'Серия документа', ['serial'], 20))
        self.addColumn(CTextCol(u'Номер документа', ['number'], 20))
        self.addColumn(CTextCol(u'Документ выдан', ['origin'], 20))
        self.addColumn(CDateCol(u'Дата выдачи документа', ['date'], 20))
        self.clientId = None
        self.date = QDate.currentDate()


    def setClientId(self, clientId):
        self.clientId = clientId
        self.cols()[0].setClientId(self.clientId)
        self.setTable('Client')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableDocument = db.table('ClientDocument')
        tableAddress = db.table('ClientAddress')
        tableDocumentType = db.table('rbDocumentType')
        loadFields = []
        loadFields.append(u'''DISTINCT Client.id, Client.lastName, Client.firstName, Client.patrName, Client.SNILS,Client.birthDate, Client.sex,
        ClientDocument.serial, ClientDocument.number, ClientDocument.date, ClientDocument.origin, rbDocumentType.name,
        IF(ClientAddress.type = 0, concat(_utf8'Адрес регистрации: ', ClientAddress.freeInput), _utf8'') AS regAddress,
        IF(ClientAddress.type = 1, concat(_utf8'Адрес проживания: ', ClientAddress.freeInput), _utf8'') AS logAddress,
        IF(CRR.relativeType_id, CRR.relativeType_id, CRC.relativeType_id) AS relativeTypeId,
        IF(CRR.relativeType_id, CRR.client_id, CRC.client_id) AS clientId,
        IF(CRR.relativeType_id, CRR.relative_id, CRC.relative_id) AS relativeId''')
        queryTable = tableClient.leftJoin(tableAddress, tableClient['id'].eq(tableAddress['client_id']))
        queryTable = queryTable.leftJoin(tableDocument, tableClient['id'].eq(tableDocument['client_id']))
        queryTable = queryTable.leftJoin(tableDocumentType, tableDocument['documentType_id'].eq(tableDocumentType['id']))
        tableCRR = db.table('ClientRelation').alias('CRR')
        tableCRC = db.table('ClientRelation').alias('CRC')
        queryTable = queryTable.leftJoin(tableCRR, db.joinAnd([tableCRR['relative_id'].eq(tableClient['id']), tableCRR['client_id'].eq(self.clientId), tableCRR['deleted'].eq(0)]))
        queryTable = queryTable.leftJoin(tableCRC, db.joinAnd([tableCRC['client_id'].eq(tableClient['id']), tableCRC['relative_id'].eq(self.clientId), tableCRC['deleted'].eq(0)]))
        self._table = queryTable
        self._recordsCache = CTableRecordCache(db, self._table, loadFields)
