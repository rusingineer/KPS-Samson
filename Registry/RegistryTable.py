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
from PyQt4.QtCore import Qt, SIGNAL, QEventLoop, QModelIndex, QVariant, QDateTime

from library.InDocTable import CRecordListModel, CRBInDocTableCol, CDateTimeInDocTableCol, CInDocTableCol, \
    CEnumInDocTableCol
from library.crbcombobox  import CRBComboBox
from library.database     import CRecordCache
from library.Attach.AttachedFile import CAttachedFilesLoader, CAttachedFilesModel
from library.ClientRecordProperties import CRecordProperties
from library.TableModel import (
    CTableModel,
    CBoolCol,
    CCol,
    CDateCol,
    CDesignationCol,
    CDoubleCol,
    CEnumCol,
    CIntCol,
    CNameCol,
    CNumCol,
    CRefBookCol,
    CTextCol,
                                        )
from library.TableView           import CTableView, CExtendedSelectionTableView
from library.Utils import (forceDate, forceDateTime, forceDouble, forceInt, forceRef, forceString, forceStringEx,
                           formatName, formatSex, formatShortNameInt, formatSNILS, toVariant, formatNameInt,
                           getPrefInt, setPref, getListChunks)
from library.TNMS.TNMSComboBox   import convertTNMSDictToDigest, convertTNMSStringToDict
from Accounting.Utils     import unpackExposeDiscipline
from Events.Action        import CActionTypeCache, CAction
from Events.ActionStatus  import CActionStatus
from Events.ActionTypeCol import CActionTypeCol
from Events.Utils         import orderTexts, payStatusText
from RefBooks.TempInvalidState   import CTempInvalidState
from Registry.Utils       import canRemoveEventWithTissue, canRemoveEventWithJobTicket
from Reports.ReportBase   import CReportBase, createTable
from Users.Rights import urDeleteAnyEvents, urDeleteOwnEvents

codeIsPrimary = [u'-', u'первичный', u'повторный', u'активное посещение', u'перевозка', u'амбулаторно']


class CSNILSCol(CTextCol):
    def format(self, values):
        val = unicode(values[0].toString())
        return QVariant(formatSNILS(val))


class CDiagnosisCol(CTextCol):
    def __init__(self, title, fields, defaultWidth, alignment='l'):
        CTextCol.__init__(self, title, fields, defaultWidth, alignment)


    def format(self, values):
        MKB   = forceString(values[0])
        MKBEx = forceString(values[1])
        outText = MKB+'+'+MKBEx if MKBEx else MKB
        return toVariant(outText)


class CMorphologyMKBCol(CTextCol):
    def __init__(self, title, fields, defaultWidth, alignment='l'):
        CTextCol.__init__(self, title, fields, defaultWidth, alignment)


class CTNMSTextCol(CTextCol):
    def __init__(self, title, fields, defaultWidth, alignment='l'):
        CTextCol.__init__(self, title, fields, defaultWidth, alignment)


    def format(self, values):
        return toVariant(convertTNMSDictToDigest(convertTNMSStringToDict(forceString(values[0]))))


class CClientEvalCol(CTextCol):
    def __init__(self, title, fields, expr, defaultWidth, alignment='l'):
        CTextCol.__init__(self, title, fields, defaultWidth, alignment)
        self.expr = expr
        self.cache = CRecordCache(capacity=500)


    def format(self, values):
        clientId = forceInt(values[0])
        output = self.cache.get(clientId)
        if output is None:
            output = QtGui.qApp.db.translate('Client', 'id', clientId, self.expr)
            self.cache.put(clientId, output)
        return output

    def weakFetch(self, listId):
        listId = [i for i in listId if not self.cache.has_key(i)]
        if listId:
            db = QtGui.qApp.db
            table = db.table('Client')
            query = db.query(db.selectStmt(table, ['id', self.expr], table['id'].inlist(listId)))
            while query.next():
                record = query.record()
                self.cache.put(forceInt(record.value('id')), record.value(self.expr))


    def invalidateRecordsCache(self):
        self.cache.invalidate()


#class CClientEvalExCol(CTextCol):
#    def __init__(self, title, fields, rbFields, tableName, rbTableName, defaultWidth, alignment='l'):
#        CTextCol.__init__(self, title, fields, defaultWidth, alignment)
#        self.color = None
#        self.tableName = tableName
#        self.rbTableName = rbTableName
#        self.rbFields = rbFields
#
#
#    def format(self, values):
#        code = ''
#        self.color = None
#        id = values[0]
#        db = QtGui.qApp.db
#        table = db.table(self.tableName)
#        rbTable = db.table(self.rbTableName)
#        record = db.getRecordEx(table.innerJoin(rbTable, table[self.rbFields].eq(rbTable['id'])), [rbTable['code'], rbTable['name'], rbTable['color']], [table['deleted'].eq(0), table['master_id'].eq(id)], '%s.id DESC'%(self.tableName))
#        if record:
#            self.codeName = forceString(record.value('code')) + '-' + forceString(record.value('name'))
#            code = forceString(record.value('code'))
#            self.color = record.value('color')
#        return code
#
#
#    def getCodeNameToolTip(self, values):
#        id = values[0]
#        db = QtGui.qApp.db
#        table = db.table(self.tableName)
#        rbTable = db.table(self.rbTableName)
#        record = db.getRecordEx(table.innerJoin(rbTable, table[self.rbFields].eq(rbTable['id'])), [rbTable['code'], rbTable['name'], rbTable['color']], [table['deleted'].eq(0), table['master_id'].eq(id)], '%s.id DESC'%(self.tableName))
#        if record:
#            codeName = forceString(record.value('code')) + '-' + forceString(record.value('name'))
#            if codeName:
#                return QVariant(codeName)
#        return CCol.invalid
#
#
#    def getBackgroundColor(self, values):
#        val = self.color
#        if val:
#            colorName = forceString(val)
#            if colorName:
#                return QVariant(QtGui.QColor(colorName))
#        return CCol.invalid


class CClientsTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CNameCol(u'Фамилия',    ['lastName'], 15))
        self.addColumn(CNameCol(u'Имя',        ['firstName'], 15))
        self.addColumn(CNameCol(u'Отчество',   ['patrName'], 15))
        self.addColumn(CDateCol(u'Дата рожд.', ['birthDate'], 12, highlightRedDate=False))
        self.addColumn(CEnumCol(u'Пол',        ['sex'], [u'-', u'М', u'Ж'], 4, 'c'))
        self.addColumn(CSNILSCol(u'СНИЛС',     ['SNILS'], 4))

#        self.addColumn(CTextCol(u'Документ',   ['getClientDocument(id)'], 30))
#        self.addColumn(CTextCol(u'Полис',      ['getClientPolicy(id,1)'], 30))
#        self.addColumn(CTextCol(u'Адрес регистрации', ['getClientRegAddress(id)'], 30))
#        self.addColumn(CTextCol(u'Адрес проживания',  ['getClientLocAddress(id)'], 30))
#        self.addColumn(CTextCol(u'Занятость',         ['getClientWork(id)'], 30))
#        self.addColumn(CTextCol(u'Контакты',          ['getClientContacts(id)'], 30))

        self.addColumn(CClientEvalCol(u'Документ',          ['id'], 'getClientDocument(id)',   30))
        self.addColumn(CClientEvalCol(u'Полис',             ['id'], 'getClientPolicy(id,1)',   30))
        self.addColumn(CClientEvalCol(u'Адрес регистрации', ['id'], 'getClientRegAddress(id)', 30))
        self.addColumn(CClientEvalCol(u'Адрес проживания',  ['id'], 'getClientLocAddress(id)', 30))
        self.addColumn(CClientEvalCol(u'Занятость',         ['id'], 'getClientWork(id)',       30))
        self.addColumn(CClientEvalCol(u'Контакты',          ['id'], 'getClientContacts(id)',   30))
        self.addColumn(CClientEvalCol(u'Прикрепление',      ['id'], 'getFormatedClientAttach(id)',   30))
#        self.addColumn(CClientEvalExCol(u'С',               ['id'], 'statusObservationType_id', 'Client_StatusObservation', 'rbStatusObservationClientType', 30)).setToolTip(u'Статус наблюдения пациента')
        self.setTable('Client')


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row    = index.row()
        if role == Qt.DisplayRole: ### or role == Qt.EditRole:
            (col, values) = self.getRecordValues(column, row)
            if column in (6, 7, 8, 9, 10, 11, 12):
                recordId = self.idList()[row]
                if not col.cache.has_key(recordId):
                    listId = self.idList()[max(0, row-self.fetchSize):(row+50)]
                    if listId:
                        col.weakFetch(listId)
            return col.format(values)
        elif role == Qt.TextAlignmentRole:
           col = self._cols[column]
           return col.alignment()
        elif role == Qt.CheckStateRole:
            (col, values) = self.getRecordValues(column, row)
            return col.checked(values)
        elif role == Qt.ForegroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getForegroundColor(values)
        elif role == Qt.BackgroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getBackgroundColor(values)
#        elif role == Qt.ToolTipRole:
#            if column == 12 or column == 13:
#                (col, values) = self.getRecordValues(column, row)
#                return col.getCodeNameToolTip(values)
        return QVariant()



class CClientsTableView(CTableView):
    def __init__(self, parent):
        CTableView.__init__(self, parent)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            event.setAccepted(True)
            self.emit(SIGNAL('requestNewEvent'))
            return
        elif event.matches(QtGui.QKeySequence.Find):
            event.ignore()
            return
        CTableView.keyPressEvent(self, event)

class CEventsTableModel(CTableModel):
    class CLocClientColumn(CCol):
        def __init__(self, title, fields, defaultWidth, clientCache):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.clientCache = clientCache

        def format(self, values):
            val = values[0]
            clientId  = forceRef(val)
            clientRecord = self.clientCache.get(clientId)
            if clientRecord:
                name = formatNameInt(forceString(clientRecord.value('lastName')),
                   forceString(clientRecord.value('firstName')),
                   forceString(clientRecord.value('patrName')))
                return toVariant(name)
            return CCol.invalid


    class CLocClientBirthDateColumn(CCol):
        def __init__(self, title, fields, defaultWidth, clientCache, extraFields=[]):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.extraFields = extraFields
            self.clientCache = clientCache

        def format(self, values):
            val = values[0]
            clientId  = forceRef(val)
            clientRecord = self.clientCache.get(clientId)
            if clientRecord:
                return toVariant(forceString(clientRecord.value('birthDate')))
            return CCol.invalid


    class CLocClientSexColumn(CCol):
        def __init__(self, title, fields, defaultWidth, clientCache, extraFields=[]):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.extraFields = extraFields
            self.clientCache = clientCache

        def format(self, values):
            val = values[0]
            clientId  = forceRef(val)
            clientRecord = self.clientCache.get(clientId)
            if clientRecord:
                return toVariant(formatSex(clientRecord.value('sex')))
            return CCol.invalid


    class CLocEventMKBColumn(CCol):
        def __init__(self, title, fields, defaultWidth, extraFields=[], alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self.extraFields = extraFields
            self._cache = {}

        def format(self, values):
            eventId = forceRef(values[0])
            result = self._cache.get(eventId, None)
            if result is None:
                db = QtGui.qApp.db
                query = db.query('SELECT getEventDiagnosis(%d)'%eventId)
                if query.next():
                    diagnosisId = forceRef(query.value(0))
                    if diagnosisId:
                        table = db.table('Diagnosis')
                        record = db.getRecordEx(table, 'MKB', table['id'].eq(diagnosisId))
                        if record:
                            MKB   = forceString(record.value('MKB'))
                            outText = MKB
                            result = toVariant(outText)
                            self._cache[eventId] = result
                    else:
                        result = CCol.invalid
                        self._cache[eventId] = result
                else:
                    result = CCol.invalid
                    self._cache[eventId] = result
            return result

        def invalidateRecordsCache(self):
            self._cache = {}


    class CLocEventMKBExColumn(CCol):
        def __init__(self, title, fields, defaultWidth, extraFields=[], alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self.extraFields = extraFields
            self._cache = {}

        def format(self, values):
            eventId = forceRef(values[0])
            result = self._cache.get(eventId, None)
            if result is None:
                db = QtGui.qApp.db
                query = db.query('SELECT getEventDiagnosis(%d)'%eventId)
                if query.next():
                    diagnosisId = forceRef(query.value(0))
                    if diagnosisId:
                        table = db.table('Diagnosis')
                        record = db.getRecordEx(table, 'MKBEx', table['id'].eq(diagnosisId))
                        if record:
                            MKBEx = forceString(record.value('MKBEx'))
                            outText = MKBEx
                            result = toVariant(outText)
                            self._cache[eventId] = result
                    else:
                        result = CCol.invalid
                        self._cache[eventId] = result
                else:
                    result = CCol.invalid
                    self._cache[eventId] = result
            return result

        def invalidateRecordsCache(self):
            self._cache = {}


    class CLocEventHealthGroupColumn(CCol):
        def __init__(self, title, fields, defaultWidth, extraFields=[], alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self.extraFields = extraFields
            self._cache = {}

        def format(self, values):
            eventId = forceRef(values[0])
            result = self._cache.get(eventId, None)
            if result is None:
                db = QtGui.qApp.db
                query = db.query('SELECT getEventHealthGroupDiagnostic(%d)'%eventId)
                if query.next():
                    healthGroupId = forceRef(query.value(0))
                    if healthGroupId:
                        result = db.translate('rbHealthGroup', 'id', healthGroupId, 'code')
                        self._cache[eventId] = result
                    else:
                        result = CCol.invalid
                        self._cache[eventId] = result
                else:
                    result = CCol.invalid
                    self._cache[eventId] = result
            return result

        def invalidateRecordsCache(self):
            self._cache = {}


    class CLocEventResultColumn(CCol):
        def __init__(self, title, fields, defaultWidth, extraFields=[], alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self.extraFields = extraFields
            self._cache = {}

        def format(self, values):
            eventId = forceRef(values[0])
            result = self._cache.get(eventId, None)
            if result is None:
                db = QtGui.qApp.db
                query = db.query('SELECT getEventResultDiagnostic(%d)'%eventId)
                if query.next():
                    resultId = forceRef(query.value(0))
                    if resultId:
                        result = db.translate('rbDiagnosticResult', 'id', resultId, "concat(regionalCode, ' | ', name)")
                        self._cache[eventId] = result
                    else:
                        result = CCol.invalid
                        self._cache[eventId] = result
                else:
                    result = CCol.invalid
                    self._cache[eventId] = result
            return result

        def invalidateRecordsCache(self):
            self._cache = {}


    def __init__(self, parent, clientCache):
        CTableModel.__init__(self, parent)
        clientCol   = CEventsTableModel.CLocClientColumn( u'Ф.И.О.', ['client_id'], 60, clientCache)
        clientBirthDateCol = CEventsTableModel.CLocClientBirthDateColumn(u'Дата рожд.', ['client_id'], 20, clientCache, ['birthDate'])
        clientSexCol = CEventsTableModel.CLocClientSexColumn(u'Пол', ['client_id'], 5, clientCache, ['sex'])
        self.addColumn(clientCol)
        self.addColumn(CTextCol(u'Код пациента', ['client_id'], 30))
        self.addColumn(clientBirthDateCol)
        self.addColumn(clientSexCol)
        self.addColumn(CDateCol(u'Назначен', ['setDate'],  10))
        self.addColumn(CDateCol(u'Выполнен', ['execDate'], 10))
        self.addColumn(CDateCol(u'След. явка', ['nextEventDate'], 10))
        self.addColumn(CDesignationCol(u'Договор',         ['contract_id'],('vrbContract', 'code'), 20))
        self.addColumn(CRefBookCol(u'Тип',  ['eventType_id'], 'EventType', 15))
        self.addColumn(CRefBookCol(u'МЭС',  ['MES_id'], 'mes.MES', 15, CRBComboBox.showCode))
        self.addColumn(CEventsTableModel.CLocEventMKBColumn(u'MKB', ['id'], 7, ['MKB']))
        self.addColumn(CEventsTableModel.CLocEventMKBExColumn(u'MKBEx', ['id'], 7, ['MKBEx']))
        self.addColumn(CRefBookCol(u'Врач', ['execPerson_id'], 'vrbPersonWithSpecialityAndOrgStr', 15))
        self.addColumn(CEnumCol(u'Первичный', ['isPrimary'], codeIsPrimary, 8))
        self.addColumn(CEnumCol(u'Порядок', ['order'], orderTexts, 8))
        self.addColumn(CRefBookCol(u'Результат события', ['result_id'], 'rbResult', 40, showFields=CRBComboBox.showCodeAndName))
        self.addColumn(CEventsTableModel.CLocEventResultColumn(u'Результат осмотра', ['id'], 7, ['diagnosticResult_id']))
        self.addColumn(CTextCol(u'Номер документа', ['externalId'], 30))
        self.addColumn(CEventsTableModel.CLocEventHealthGroupColumn(u'Группа здоровья', ['id'], 7, ['healthGroup_id']))
        self.addColumn(CRefBookCol(u'Автор', ['createPerson_id'], 'vrbPerson', 15))

        self.addColumn(CDesignationCol(u'Направитель', ['relegateOrg_id'], ('Organisation', 'shortName'), 10))
        self.addColumn(CTextCol(u'Номер направления', ['srcNumber'], 10))
        self.addColumn(CDateCol(u'Дата направления', ['srcDate'], 10))

        self.loadField('createPerson_id')
        self.loadField('prevEvent_id')
        self.loadField('relegateOrg_id')
        self.setTable('Event')
        self.diagnosisIdList = []
        self.diagnosticIdList = []
        self.actionsIdList = []
        self.visitsIdList = []
        self.takenTissueIdList = []
        self._mapColumnToOrder ={'client_id'          :'CONCAT(Client.lastName, Client.firstName, Client.patrName)',
                                 'clientId'           :'Client.id',
                                 'birthDate'          :'Client.birthDate',
                                 'sex'                :'Client.sex',
                                 'setDate'            :'Event.setDate',
                                 'execDate'           :'Event.execDate',
                                 'nextEventDate'      :'Event.nextEventDate',
                                 'contract_id'        :'Event.contract_id',
                                 'eventType_id'       :'EventType.name',
                                 'MES_id'             :'mes.MES.code',
                                 'MKB'                :'Diagnosis.MKB',
                                 'MKBEx'              :'Diagnosis.MKBEx',
                                 'execPerson_id'      :'Event.execPerson_id',
                                 'isPrimary'          :'Event.isPrimary',
                                 'order'              :'Event.order',
                                 'result_id'          :'rbResult.name',
                                 'externalId'         :'Event.externalId',
                                 'healthGroup_id'     :'rbHealthGroup.code',
                                 'diagnosticResult_id':'rbDiagnosticResult.name',
                                 'createPerson_id'    :'Event.createPerson_id',

                                 'relegateOrg_id'     :'Organisation.shortName',
                                 'srcNumber'          :'Event.srcNumber',
                                 'srcDate'            :'Event.srcDate'
                                 }
        self.personalAccountAvailabilityCache = {}
        self.connect(self, SIGNAL('itemsCountChanged(int)'), self.personalAccountRestrictions)

    def getClientCount(self):
        if self.idList():
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            clientCount = db.getDistinctCount(tableEvent,
                                                'client_id',
                                                tableEvent['id'].inlist(self._idList)
                                               )
            return clientCount
        return 0


    def personalAccountRestrictions(self, count):
        self.personalAccountAvailabilityCache = {}


    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        if column == 1:
            fieldName = u'clientId'
        return self._mapColumnToOrder[fieldName]

    def removeRow(self, row, parent = QModelIndex()):
        if self._idList and 0<=row<len(self._idList):
            itemId = self._idList[row]
            if self.canRemoveEvent(itemId):
                return CTableModel.removeRow(self, row, parent)
        return False


    def canRemoveEvent(self, itemId):
        result = True
        if self.hasActionsWithTissue(itemId):
            result = result and canRemoveEventWithTissue()
        if self.hasActionWithJobTicket(itemId):
            result = result and canRemoveEventWithJobTicket()
        result = result and self.isLockedEvent(itemId)
        return result


    def canRemoveItem(self, eventId):
        if QtGui.qApp.userHasRight(urDeleteAnyEvents):
            return True
        record = self.getRecordById(eventId)
        userId = QtGui.qApp.userId
        return QtGui.qApp.userHasRight(urDeleteOwnEvents) and (userId == forceRef(record.value('createPerson_id'))
                                                               or userId == forceRef(record.value('execPerson_id')))


    def isLockedEvent(self, eventId):
        db = QtGui.qApp.db
        tableAppLock_Detail = db.table('AppLock_Detail')
        tableAppLock = db.table('AppLock')
        table = tableAppLock_Detail.leftJoin(tableAppLock, tableAppLock['id'].eq(tableAppLock_Detail['master_id']))
        cond = [tableAppLock_Detail['tableName'].eq('Event'),
                tableAppLock_Detail['recordId'].eq(eventId),
                'TIMESTAMPDIFF(SECOND, AppLock.retTime, NOW()) < 300']
        record = db.getRecordEx(table, ['lockTime', 'person_id', 'addr'], cond)
        if record:
            lockTime = forceDateTime(record.value('lockTime'))
            personId = forceRef(record.value('person_id'))
            personName = forceString(db.translate('vrbPersonWithSpeciality', 'id', personId, 'name')) if personId else u'аноним'
            addr = forceString(record.value('addr'))
            lockInfo = lockTime, personName, addr
            message = u'Данные заблокированы %s\nпользователем %s\nс компьютера %s' % (
                forceString(lockInfo[0]),
                lockInfo[1],
                lockInfo[2])

            QtGui.QMessageBox.critical(QtGui.qApp.mainWindow,
                                      u'Ограничение совместного доступа к данным',
                                      message,
                                      QtGui.QMessageBox.Cancel,
                                      QtGui.QMessageBox.Cancel
                                      )
            return False
        return True


    def hasActionWithJobTicket(self, eventId):
        db                           = QtGui.qApp.db
        tableEvent                   = db.table('Event')
        tableAction                  = db.table('Action')
        tableActionProperty          = db.table('ActionProperty')
        tableActionPropertyJobTicket = db.table('ActionProperty_Job_Ticket')
        tableJobTicket               = db.table('Job_Ticket')
        tableJob                     = db.table('Job')
        queryTable = tableEvent.innerJoin(tableAction,
                                          tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableActionProperty,
                                          tableActionProperty['action_id'].eq(tableAction['id']))
        queryTable = queryTable.innerJoin(tableActionPropertyJobTicket,
                                          tableActionPropertyJobTicket['id'].eq(tableActionProperty['id']))
        queryTable = queryTable.innerJoin(tableJobTicket,
                                          tableJobTicket['id'].eq(tableActionPropertyJobTicket['value']))
        queryTable = queryTable.innerJoin(tableJob,
                                          tableJob['id'].eq(tableJobTicket['master_id']))
        cond = [tableAction['event_id'].eq(eventId),
                tableAction['deleted'].eq(0),
                tableActionProperty['deleted'].eq(0),
                tableJob['deleted'].eq(0)]
        return bool(db.getCount(queryTable, countCol='Job.id', where=cond))


    def hasActionsWithTissue(self, itemId):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        cond = [tableAction['event_id'].eq(itemId),
                tableAction['takenTissueJournal_id'].isNotNull(),
                tableAction['deleted'].eq(0)]
        return bool(db.getCount(tableAction, where=cond))


    def canMakePersonalAccount(self, eventId):
        record = self.recordCache().get(eventId)
        contractId = forceRef(record.value('contract_id'))
        if contractId not in self.personalAccountAvailabilityCache:
            if contractId:
                db = QtGui.qApp.db
                exposeDiscipline = forceInt(db.translate('Contract', 'id',  contractId, 'exposeDiscipline'))
                (
                  exposeBySourceOrg,
                  exposeByOncology,
                  exposeByBatch,
                  exposeByEvent,
                  exposeByMonth,
                  exposeByClient,
                  exposeByInsurer,
                )                 = unpackExposeDiscipline(exposeDiscipline)
                result = exposeByClient or exposeByEvent
            else:
                result = False
            self.personalAccountAvailabilityCache[contractId] = result
            return result
        return self.personalAccountAvailabilityCache[contractId]


    def beforeRemoveItem(self, itemId):
        db = QtGui.qApp.db
        self.diagnosisIdList = db.getDistinctIdList('Diagnostic', idCol='diagnosis_id', where='event_id=%d'%itemId)
        self.diagnosticIdList = db.getDistinctIdList('Diagnostic', idCol='id', where='event_id=%d'%itemId)
        self.actionsIdList = db.getDistinctIdList('Action', idCol='id', where='event_id=%d'%itemId)
        self.visitsIdList = db.getDistinctIdList('Visit', idCol='id', where='event_id=%d'%itemId)
        self.takenTissueIdList =  db.getDistinctIdList('Action', idCol='takenTissueJournal_id', where='event_id=%d'%itemId)


    def afterRemoveItem(self, itemId):
        self.deleteActions()
        self.deleteDiagnosis()
        self.deleteVisits()
        self.deleteTakenTissue()
        self.logDeletion(itemId)


    def deleteActions(self):
        db = QtGui.qApp.db
        if self.actionsIdList:
            tableActionProperty = db.table('ActionProperty')
            filter = [tableActionProperty['action_id'].inlist(self.actionsIdList), tableActionProperty['deleted'].eq(0)]
            db.deleteRecord(tableActionProperty, filter)

            tableActionExecutionPlan = db.table('Action_ExecutionPlan')
            filter = [tableActionExecutionPlan['master_id'].inlist(self.actionsIdList), tableActionExecutionPlan['deleted'].eq(0)]
            db.deleteRecord(tableActionExecutionPlan, filter)

            tableStockMotion = db.table('StockMotion')
            tableActionNR = db.table('Action_NomenclatureReservation')
            filter = [tableActionNR['action_id'].inlist(self.actionsIdList)]
            reservationIdList = db.getDistinctIdList(tableActionNR, [tableActionNR['reservation_id']], filter)
            if reservationIdList:
                filter = [tableStockMotion['id'].inlist(reservationIdList), tableStockMotion['deleted'].eq(0)]
                db.deleteRecord(tableStockMotion, filter)

            tableAction = db.table('Action')
            filter = [tableAction['id'].inlist(self.actionsIdList), tableAction['deleted'].eq(0)]
            stockMotionIdList = db.getDistinctIdList(tableAction, [tableAction['stockMotion_id']], filter)
            if stockMotionIdList:
                tableStockMotionItem = db.table('StockMotion_Item')
                filter = [tableStockMotionItem['master_id'].inlist(stockMotionIdList), tableStockMotionItem['deleted'].eq(0)]
                db.deleteRecord(tableStockMotionItem, filter)
                filter = [tableStockMotion['id'].inlist(stockMotionIdList), tableStockMotion['deleted'].eq(0)]
                db.deleteRecord(tableStockMotion, filter)

            filter = [tableAction['id'].inlist(self.actionsIdList), tableAction['deleted'].eq(0)]
            db.deleteRecord(tableAction, filter)
        self.actionsIdList = []


    def deleteVisits(self):
        db = QtGui.qApp.db
        if self.visitsIdList:
            tableVisit = db.table('Visit')
            filter = [tableVisit['id'].inlist(self.visitsIdList), tableVisit['deleted'].eq(0)]
            db.deleteRecord(tableVisit, filter)
        self.visitsIdList = []


    def deleteDiagnosis(self):
        db = QtGui.qApp.db
        if self.diagnosticIdList:
            tableDiagnostic = db.table('Diagnostic')
            filter = [tableDiagnostic['id'].inlist(self.diagnosticIdList), tableDiagnostic['deleted'].eq(0)]
            db.deleteRecord(tableDiagnostic, filter)
        tableDiagnosis = db.table('Diagnosis')
        tableDC = db.table('Diagnostic').alias('DC')
        # Записи из Diagnostic не удаляются, а отмечаются deleted=1. Diagnostic.id IS NULL оставляю для истории, но
        # он по-сути не нужен больше
        # Одним запросом удалять записи из Diagnosis нельзя, поскольку, если среди удаляемых (проверяемых) записей
        # есть хоть одна, которая не должна быть удалена - условие
        # NOT EXISTS(SELECT DC.id FROM Diagnostic AS DC WHERE (%s) AND DC.deleted = 0 AND (%s))
        # вернёт False для всего списка и ни одна запись не будет удалена (Mantis 0015991)
        # Проходим по списку удаляемых и удаляем записи по одной
        for id in self.diagnosisIdList:
            stmt = 'UPDATE Diagnosis '                                                  \
                   'LEFT JOIN Diagnostic ON Diagnostic.diagnosis_id = Diagnosis.id '    \
                   'LEFT JOIN TempInvalid ON TempInvalid.diagnosis_id = Diagnosis.id '  \
                   'LEFT JOIN Diagnosis AS D ON D.mod_id = Diagnosis.id '               \
                   'SET Diagnosis.deleted = 1 '                                         \
                   'WHERE (%s) '                                                        \
                   'AND Diagnosis.deleted = 0 '                                         \
                   'AND NOT EXISTS(SELECT DC.id FROM Diagnostic AS DC '                 \
                   'WHERE (%s) AND DC.deleted = 0 AND (%s)) '         \
                   'AND Diagnostic.id IS NULL '                                         \
                   'AND TempInvalid.id IS NULL '                                        \
                   'AND D.id IS NULL;' % (tableDiagnosis['id'].eq(id), tableDC['diagnosis_id'].eq(id), tableDC['id'].notInlist(self.diagnosticIdList))
            db.query(stmt)
        self.updateDiagnosisData()
        self.diagnosisIdList = []
        self.diagnosticIdList = []
        QtGui.qApp.emitCurrentClientInfoChanged()

    def deleteTakenTissue(self):
        db = QtGui.qApp.db
        if self.takenTissueIdList:
            tableTTJ = db.table('TakenTissueJournal')
            filter = [tableTTJ['id'].inlist(self.takenTissueIdList), tableTTJ['deleted'].eq(0)]
            db.deleteRecord(tableTTJ, filter)
        self.takenTissueIdList = []


    def updateDiagnosisData(self):
        if self.diagnosisIdList:
            db = QtGui.qApp.db
            tableDiagnostic = db.table('Diagnostic')
            tableDiagnosis = db.table('Diagnosis')
            record = db.getRecordEx(tableDiagnostic, u'MAX(endDate) as endDate', [tableDiagnostic['diagnosis_id'].inlist(self.diagnosisIdList), tableDiagnostic['deleted'].eq(0)])
            endDate = forceDate(record.value('endDate'))
            diagnosisRecord = db.getRecordEx(tableDiagnosis, u'*', [tableDiagnosis['id'].inlist(self.diagnosisIdList), tableDiagnosis['deleted'].eq(0)])
            if endDate and diagnosisRecord:
                diagnosisRecord.setValue('endDate', toVariant(endDate))
                db.updateRecord(tableDiagnosis, diagnosisRecord)

    def logDeletion(self, itemId):
        db = QtGui.qApp.db
        table = db.table('soc_EventLog')
        record = db.getRecordEx(table, '*', table['event_id'].eq(itemId))
        if record:
            record.setValue('deletePerson_id', toVariant(QtGui.qApp.userId))
            record.setValue('addr', toVariant(QtGui.qApp.hostName))
            db.updateRecord(table, record)


class CEventsTableView(CTableView):
    def __init__(self, parent):
        CTableView.__init__(self, parent)
        self._order = None
        self._orderColumn = None
        self._isDesc = True


    def removeEventAfterDirection(self):
        def removeCurrentRowEvent():
            index = self.currentIndex()
            if index.isValid() and self.confirmRemoveRow(self.currentIndex().row()):
                row = self.currentIndex().row()
                self.model().removeRow(row)
                self.setCurrentRow(row)
        row = self.currentIndex().row()
        record = self.model().getRecordByRow(row)
        if record:
            prevEventId = forceRef(record.value('prevEvent_id'))
            if prevEventId:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                record = db.getRecordEx(tableEvent, [tableEvent['relegateOrg_id']], [tableEvent['id'].eq(prevEventId), tableEvent['deleted'].eq(0)])
                relegateOrgId = forceRef(record.value('relegateOrg_id')) if record else None
                if relegateOrgId and relegateOrgId != QtGui.qApp.currentOrgId():
                    tableAction = db.table('Action')
                    tableActionType = db.table('ActionType')
                    tableEventType = db.table('EventType')
                    table = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
                    table = table.innerJoin(tableEvent, db.joinAnd([tableEvent['id'].eq(tableAction['event_id']), tableEvent['deleted'].eq(0)]))
                    table = table.innerJoin(tableEventType, db.joinAnd([tableEventType['id'].eq(tableEvent['eventType_id']), tableEventType['deleted'].eq(0)]))
                    cond = [tableAction['event_id'].eq(prevEventId),
                            tableAction['deleted'].eq(0),
                            tableActionType['deleted'].eq(0),
                            db.joinOr([tableActionType['flatCode'].like(u'recoveryDirection%'),
                                       tableActionType['flatCode'].like(u'inspectionDirection%'),
                                       tableActionType['flatCode'].like(u'researchDirection%'),
                                       tableActionType['flatCode'].like(u'consultationDirection%'),
                                       db.joinAnd([tableActionType['flatCode'].like(u'planning%'), tableEventType['code'].like(u'УО')])])
                            ]
                    record = db.getRecordEx(table, u'*', cond, tableAction['id'].name())
                    actionId = forceRef(record.value('id')) if record else None
                    if actionId:
                        res = QtGui.QMessageBox.warning( self,
                                     u'Внимание!',
                                     u'При удалении События, связанного с внешним направлением, направление будет аннулированно. Продолжить удаление?',
                                     QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                                     QtGui.QMessageBox.Cancel)
                        if res == QtGui.QMessageBox.Ok:
                            QtGui.qApp.call(self, removeCurrentRowEvent)
                            recordAction = db.getRecordEx(tableAction, u'*', [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0)])
                            personId = QtGui.qApp.userId if (QtGui.qApp.userId and QtGui.qApp.userSpecialityId) else forceRef(recordAction.value('person_id'))
                            tablePWS = db.table('vrbPersonWithSpeciality')
                            recordPWS = db.getRecordEx(tablePWS, [tablePWS['name']], [tablePWS['id'].eq(personId)]) if personId else None
                            personName = forceString(recordPWS.value('name')) if recordPWS else ''
                            recordAction.setValue('status', toVariant(CActionStatus.canceled))
                            recordAction.setValue('note', toVariant(u'Отменить: %s %s'%(QDateTime.currentDateTime().toString('dd-MM-yyyy hh:mm'), personName)))
                            db.transaction()
                            try:
                                db.updateRecord(tableAction, recordAction)
                                db.commit()
                            except:
                                db.rollback()
                        return True
        return False


    def order(self):
        return self._order


    def setOrder(self, column):
        if column is not None:
            self._isDesc = not self._isDesc if self._orderColumn == column else False
            self._order = self.getOrder(column) + (' DESC' if self._isDesc else ' ASC')
            self._orderColumn = column
            self.horizontalHeader().setSortIndicator(column, Qt.DescendingOrder if self._isDesc else Qt.AscendingOrder)
        else:
            self._order = None
            self._orderColumn = None
            self._isDesc = True


    def getOrder(self, column):
        return self.model().getOrder(self.model().cols()[column].fields()[0], column)


    def eventHasContinuation(self, eventId):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        table = tableEvent.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        record = db.getRecordEx(table, [tableEvent['id']], [tableEvent['prevEvent_id'].eq(eventId), tableEvent['deleted'].eq(0),
                                                            db.joinOr([tableEventType['context'].ne('relatedAction'), tableEventType['context'].isNull()])])
        return bool(record)


    def cleanPrevEventId(self, eventId):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        table = tableEvent.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        record = db.getRecordEx(table, [tableEvent['id']], [tableEvent['prevEvent_id'].eq(eventId), tableEvent['deleted'].eq(0), tableEventType['context'].eq('relatedAction')])
        if record:
            db.query('update Event set prevEvent_id = NULL where id = {0}'.format(forceRef(record.value('id'))))



    def eventHasAccountItem(self, eventId):
        db = QtGui.qApp.db
        table = db.table('Account_Item')
        cond = [table['event_id'].eq(eventId), table['deleted'].eq(0)]
        record = db.getRecordEx(table, [table['id']], cond)
        accountItemId = forceRef(record.value('id')) if record else None
        return bool(accountItemId)


    def eventHasMSIActionId(self, eventId):
        message = u''
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        queryTable = tableActionType.innerJoin(tableAction, tableAction['actionType_id'].eq(tableActionType['id']))
        cols = [tableActionType['code'].alias('msiCode'),
                tableActionType['name'].alias('msiName')
                ]
        cond = [tableAction['event_id'].eq(eventId),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableActionType['flatCode'].like(u'inspection_mse%'),
                ]
        record = db.getRecordEx(queryTable, cols, cond)
        if record:
            message = forceStringEx(record.value('msiCode')) + u'-' + forceStringEx(record.value('msiName'))
        return message


    def eventHasPrevActionId(self, eventId):
        message = u''
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        queryTable = tableAction.leftJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
        cols = [tableAction['id'],
                tableActionType['code'].alias('lastCode'),
                tableActionType['name'].alias('lastName')
                ]
        cond = [tableAction['event_id'].eq(eventId),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0)]
        recordList = db.getRecordList(queryTable, cols, cond)
        actionIdList = []
        for record in recordList:
            actionIdList.append(forceRef(record.value('id')))
        if actionIdList:
            cols = [tableAction['prevAction_id'],
                    tableActionType['code'].alias('prevCode'),
                    tableActionType['name'].alias('prevName')]
            cond = [tableAction['prevAction_id'].inlist(actionIdList),
                    tableAction['deleted'].eq(0),
                    tableActionType['deleted'].eq(0)]
            prevRecordList = db.getRecordList(queryTable, cols, cond, limit=1)
            lastCode = lastName = ''
            for prevRecord in prevRecordList:
                prevId = forceRef(prevRecord.value('prevAction_id'))
                prevCode = forceStringEx(prevRecord.value('prevCode'))
                prevName = forceStringEx(prevRecord.value('prevName'))
                for record in recordList:
                    if forceRef(record.value('id')) == prevId:
                        lastCode = forceStringEx(record.value('lastCode'))
                        lastName = forceStringEx(record.value('lastName'))
                message = prevCode + u'-' + prevName + u' связанное с действием ' + lastCode + u'-' + lastName
        return message


    def removeCurrentRow(self, needConfirm=True):
        def removeCurrentRowInternal(needConfirm=True):
            eventId = self.currentItemId()
            if eventId:
                messagePrevAction = self.eventHasPrevActionId(eventId)
                # messageMSIAction = self.eventHasMSIActionId(eventId)
                if messagePrevAction:
                    QtGui.QMessageBox().warning(self, u'Внимание!', u'Событие имеет действие %s, поэтому не может быть удалено.' % messagePrevAction, QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                # elif messageMSIAction:
                #     QtGui.QMessageBox().warning(self, u'Внимание!', u'Событие имеет действие %s, поэтому не может быть удалено.' % messageMSIAction, QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                elif self.eventHasContinuation(eventId):
                    QtGui.QMessageBox().warning(self, u'Внимание!', u'Событие имеет продолжение, поэтому не может быть удалено.', QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                elif self.eventHasAccountItem(eventId):
                    QtGui.QMessageBox().warning(self, u'Внимание!', u'По событию выставлен счёт, поэтому оно не может быть удалено.', QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                elif self.removeEventAfterDirection():
                    pass
                else:
                    row = self.currentRow()
                    if not needConfirm or self.confirmRemoveRow(row):
                        self.cleanPrevEventId(eventId)
                        self.model().removeRow(row)
                        self.setCurrentRow(row)
        QtGui.qApp.call(self, removeCurrentRowInternal, (needConfirm, ))


class CEventDiagnosticsTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
#        self.addColumn(CDateCol(u'дата назначения',['setDate'], 10))
        col = self.addColumn(CDateCol(u'Установлен', ['endDate'], 10))
        self.addColumn(CRefBookCol(u'Тип', ['diagnosisType_id'], 'rbDiagnosisType', 6))
        col = self.addColumn(CRefBookCol(u'ГpЗд', ['healthGroup_id'], 'rbHealthGroup', 2, CRBComboBox.showCode))
        col.setToolTip(u'Группа здоровья')
        self.addColumn(CDiagnosisCol(u'Диагноз', ['MKB', 'MKBEx'], 6))
        if QtGui.qApp.isExSubclassMKBVisible():
            col = self.addColumn(CTextCol(u'РСК', ['exSubclassMKB'], 6))
            col.setToolTip(u'Расширенная субклассификация МКБ')
        if QtGui.qApp.defaultMorphologyMKBIsVisible():
            col = self.addColumn(CMorphologyMKBCol(u'Морф.', ['morphologyMKB'], 8))
            col.setToolTip(u'Морфология диагноза МКБ')
        if QtGui.qApp.isTNMSVisible():
            self.addColumn(CTNMSTextCol(u'TNM-Ст', ['TNMS'],  10))
        if QtGui.qApp.isClinicalGroupDiagnosticVisible():
            self.addColumn(CEnumCol(u'КГ', ['clinicalGroup'], (u'', u'1а - подозрение', u'1б - предрак', u'2 - подлежат радикальному лечению', u'3 - ремиссия', u'4 - подлежат паллиативному лечению'), 30)).setToolTip(u'Клиническая группа')
        col = self.addColumn(CRefBookCol(u'Хар', ['character_id'], 'rbDiseaseCharacter', 6))
        col.setToolTip(u'Характер')
        col = self.addColumn(CRefBookCol(u'Фаза', ['phase_id'], 'rbDiseasePhases', 6))
        col.setToolTip(u'Фаза')
        col = self.addColumn(CRefBookCol(u'Ст', ['stage_id'], 'rbDiseaseStage', 6))
        col.setToolTip(u'Стадия')
        col = self.addColumn(CRefBookCol(
            u'ДН', ['dispanser_id'], 'rbDispanser', 6, CRBComboBox.showCode))
        col.setToolTip(u'Диспансерное наблюдение')
#        col = self.addColumn(CEnumCol(u'Г',['hospital'], CHospitalInfo.names, 4))
        col = self.addColumn(CTextCol(u'Госп', ['hospital'], 4))
        col.setToolTip(u'Госпитализация')
        col = self.addColumn(CRefBookCol(
            u'Тр', ['traumaType_id'], 'rbTraumaType', 6, CRBComboBox.showCode))
        col.setToolTip(u'Тип травмы')
        self.addColumn(CRefBookCol(u'ТоксВещ', ['toxicSubstances_id'], 'rbToxicSubstances', 10).setToolTip(u'Токсичное вещество'))
        self.addColumn(CRefBookCol(u'Врач', ['person_id'], 'vrbPerson', 6))
        self.addColumn(CRefBookCol(u'Специальность', ['speciality_id'], 'rbSpeciality', 6))
        self.addColumn(CRefBookCol(u'Результат', ['result_id'], 'rbDiagnosticResult', 6))
        self.addColumn(CTextCol(u'Примечания', ['notes'], 6))
        self.addColumn(CTextCol(u'Описание', ['freeInput'], 6))

#        self.addColumn(CDateCol(u'дата', ['endDate'], 6))
#        self.addColumn(CEnumCol(u'СК', ['sanatorium'], [u'не нуждается', u'нуждается', u'направлен', u'пролечен'], 4))
        db = QtGui.qApp.db
        tableDiagnostic = db.table('Diagnostic')
        tableDiagnosis  = db.table('Diagnosis')
        queryTable = tableDiagnostic.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
#        self.setTable('Diagnostic')
        self.setTable(queryTable)
        self.headerSortingCol = {}


class CPayStatusColumn(CCol):
    def format(self, values):
        payStatus = forceInt(values[0])
        return toVariant(payStatusText(payStatus))


class CEventActionsTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CDateCol(u'Назначено',      ['directionDate'], 15))
        self.addColumn(CBoolCol(u'Срочно',         ['isUrgent'],      15))
        self.addColumn(CDateCol(u'План',           ['plannedEndDate'],15))
        self.addColumn(CDateCol(u'Начато',         ['begDate'],       15))
        self.addColumn(CDateCol(u'Окончено',       ['endDate'],       15))
        self.addColumn(CActionTypeCol(u'Тип',                         15))
        self.addColumn(CEnumCol(u'Состояние',      ['status'], CActionStatus.names, 4))
        self.addColumn(CRefBookCol(u'Назначил',    ['setPerson_id'], 'vrbPersonWithSpeciality', 20))
        self.addColumn(CRefBookCol(u'Выполнил',    ['person_id'],    'vrbPersonWithSpeciality', 20))
        self.addColumn(CTextCol(u'Каб',            ['office'],                                6))
        self.addColumn(CTextCol(u'Примечания',     ['note'],                                  6))
        self.addColumn(CPayStatusColumn(u'Оплата', ['payStatus'], 20, 'l'))
        self.addColumn(CDoubleCol(u'Количество',      ['amount'], 20))
        self.addColumn(CDoubleCol(u'УЕТ',          ['uet'], 20))
        self.addColumn(CTextCol(u'МКБ',            ['MKB'], 20))
        self.setTable('Action')
        self.headerSortingCol = {}


class CEventVisitsTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CRefBookCol(u'Место',       ['scene_id'],         'rbScene',    15))
        self.addColumn(CDateCol(u'Дата',           ['date'],                           15))
        self.addColumn(CRefBookCol(u'Тип',         ['visitType_id'],    'rbVisitType', 15))
        self.addColumn(CRefBookCol(u'Услуга',      ['service_id'],      'rbService',   15))
        self.addColumn(CRefBookCol(u'Выполнил',    ['person_id'],     'vrbPersonWithSpecialityAndOrgStr', 20))
        self.addColumn(CEnumCol(u'Первичный',      ['isPrimary'], codeIsPrimary, 4, 'l'))
        self.addColumn(CPayStatusColumn(u'Оплата', ['payStatus'], 20, 'l'))
        self.setTable('Visit')
        self.headerSortingCol = {}


class CEventExportFileTableModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Наименование действия',      'title', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Наименование документа',         'path',      6)).setReadOnly()
        self.addCol(CRBInDocTableCol(u'Подписавший',    'respSigner_id', 6, 'vrbPersonWithSpeciality')).setReadOnly()
        self.addCol(CDateTimeInDocTableCol(u'Дата подписания врачом', 'respSigningDatetime', 6)).setReadOnly()
        self.addCol(CDateTimeInDocTableCol(u'Дата подписания организацией', 'orgSigningDatetime', 6)).setReadOnly()
        self.addCol(CDateTimeInDocTableCol(u'Дата и время экспорта', 'dateTime', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Состояние',   'success', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Примечания',   'note', 6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Информация о приеме документа федеральным РЭМД', 'StatusREMD', 6)).setReadOnly()
        self.order = u'a.id DESC'
        self.headerSortingCol = {}

    def data(self, index, role):
        if role == Qt.BackgroundColorRole:
            record = self.getRecordByRow(index.row())
            if record:
                successValue = self.getSuccessValueById(forceRef(record.value('afaId')))
                if successValue == u'успех':
                    return QVariant(QtGui.QColor(Qt.green))  # зеленый
                elif successValue == u'ошибка':
                    return QVariant(QtGui.QColor(Qt.red))  # красный
        else:
            return CRecordListModel.data(self, index, role)

    def getSuccessValueById(self, AFAId):
        if AFAId:
            stmt = u"""SELECT case when IM.`status` = 'Success' then 'успех'
        when IM.`status` = 'Failed' then 'ошибка' end AS success
        FROM Action a
  LEFT JOIN Action_FileAttach afa ON a.id = afa.master_id  AND afa.deleted=0
  Left JOIN Action_FileAttach_Export afe  ON afe.id = (SELECT MAX(id) FROM Action_FileAttach_Export afae WHERE afa.id=afae.master_id)
   LEFT JOIN Information_Messages IM on IM.id = (SELECT MAX(Information_Messages.id) FROM Information_Messages
	   WHERE typeMessages = 'REMDStatus' AND IdMedDocumentMis_id=afe.master_id
  AND (((`status` = 'Success' AND IdFedRequest IS NOT NULL ) OR (`status` = 'Failed')) 
  		OR (`status` = 'Success' AND IdFedRequest IS NOT NULL  AND RemdRegNumber !='')))
  WHERE afa.id = %s limit 1""" % (AFAId)
            query = QtGui.qApp.db.query(stmt)
            while query.next():
                record = query.record()
                return forceString(record.value('success'))
        return ''

    def loadData(self, eventId):
        if eventId:
            db = QtGui.qApp.db
            cols = []
            tableQuery = []
            stmt = u'''
            (SELECT DISTINCT 
                     a.id ,
                     afa.id as afaId,  
                     concat_ws(' ', AT.name, 'от', DATE_FORMAT(a.endDate,'%d.%m.%Y')) as title,
                     SUBSTRING_INDEX(afa.path, '/', -1 ) as path,
                     afa.respSigner_id,
                     afa.respSigningDatetime,
                     afa.orgSigningDatetime,
                     afe.dateTime,
                     case when IM.status = 'Success' then 'успех' 
                        when IM.status = 'Failed' then 'ошибка' end as success,
                     afe.note 
              ,                     case when IM.status = 'Success' and IM.Message <> '' AND IM.RemdRegNumber
  then CONCAT('Успех - ', IM.Message)
when IM.status = 'Success' and IM.Message <> '' AND IM.RemdRegNumber =''
  then 'Ожидается валидация документа на федеральном уровне'
when IM.status = 'Failed' and IM.Message <> ''
  then CONCAT('Ошибка - ', IM.Message)
ELSE 'Информация еще не получена' END AS StatusREMD

   FROM Action a
  inner JOIN ActionType AT ON AT.id=a.actionType_id
  INNER JOIN ActionType_Identification ai ON ai.master_id=AT.id
  inner JOIN rbAccountingSystem rbAS ON rbAS.id=ai.system_id
  inner JOIN Action_FileAttach afa ON afa.id=(SELECT MAX(id) FROM Action_FileAttach afa WHERE afa.master_id=a.id AND afa.deleted=0
    AND (( right(SUBSTRING_INDEX(afa.path, '/', -1 ),3) = "xml" AND   RIGHT(rbAS.urn,3)="cda")
  OR ( right(SUBSTRING_INDEX(afa.path, '/', -1 ),3) = "pdf" AND   RIGHT(rbAS.urn,3)="pdf")
  OR ( right(SUBSTRING_INDEX(afa.path, '/', -1 ),3) = "sms" AND   RIGHT(rbAS.urn,5)="Vimis"))
  )  
  left JOIN Action_FileAttach_Export afe  ON afe.id = (SELECT MAX(id) FROM Action_FileAttach_Export afae WHERE afa.id=afae.master_id)
  LEFT JOIN Information_Messages IM on IM.id = (SELECT MAX(Information_Messages.id) FROM Information_Messages
     WHERE typeMessages = 'REMDStatus' AND IdMedDocumentMis_id=afe.master_id
  AND (((status = 'Success' AND IdFedRequest IS NOT NULL ) OR (status = 'Failed')) 
      OR (status = 'Success' AND IdFedRequest IS NOT NULL  AND RemdRegNumber !='')))
      
  WHERE a.event_id = {eventId} and a.deleted=0  AND ai.deleted = 0 -- and  AT.flatCode <> ''  AND ((afa.id IS NOT NULL AND afa.path IS NOT null) OR afa.id IS NULL)
  and AT.flatCode not LIKE '%temperatureSheet%' and rbAS.code LIKE '%n3.medDocumentType.%'
                    ORDER BY {order})
UNION ALL
            (SELECT DISTINCT 
                     a.id ,
                     0 as afaId,  
                     concat_ws(' ', AT.name, 'от', DATE_FORMAT(a.endDate,'%d.%m.%Y')) as title,
                  	 '' as path,
                     NULL AS respSigner_id, 
                     NULL AS respSigningDatetime, 
                     NULL as orgSigningDatetime, 
                     NULL AS `dateTime`,  
                     '' as success,
                     NULL AS note, 
                    'Информация еще не получена' AS StatusREMD 

   FROM Action a
  inner JOIN ActionType AT ON AT.id=a.actionType_id
  INNER JOIN ActionType_Identification ai ON ai.master_id=AT.id
  inner  JOIN rbAccountingSystem rbAS ON rbAS.id=ai.system_id
  		
  WHERE a.event_id = {eventId} and a.deleted=0  AND ai.deleted = 0 -- and AT.flatCode <> '' 
        and AT.flatCode not LIKE '%temperatureSheet%' and rbAS.code LIKE '%n3.medDocumentType.%' 
        AND (  SELECT MAX(afa.id) FROM Action_FileAttach afa 
		    left JOIN Action_FileAttach_Export afe  ON afe.id = (SELECT MAX(id) FROM Action_FileAttach_Export afae WHERE afa.id=afae.master_id)
		  WHERE afa.master_id=a.id AND afa.deleted=0
  ) IS null
        ORDER BY {order})                                        '''
            query = db.query(stmt.format(cols=(', %s' % (','.join(col for col in cols if col))) if cols else '',
                                         queryTable=(''.join(tq for tq in tableQuery if tq)) if tableQuery else '',
                                         eventId=eventId,
                                         order=self.order
                                         )
                             )
            items = []
            while query.next():
                items.append(query.record())
            self.setItems(items)
        else:
            self.clearItems()

    def sort(self, col, order=Qt.AscendingOrder):
        self.headerSortingCol = {col: order}
        reverse = order == Qt.DescendingOrder
        if col in [3, 4, 5]:
            self.items().sort(key=lambda x: forceDateTime(x.value(self.cols()[col].fieldName())) if x else None,
                              reverse=reverse)
        else:
            self.items().sort(key=lambda x: forceString(
                self.cols()[col].toString(x.value(self.cols()[col].fieldName()), x)) if x else None, reverse=reverse)
        self.reset()

class CAmbCardDiagnosticsTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
#        self.addColumn(CDateCol(u'дата назначения',['setDate'], 10))
        self.addColumn(CRefBookCol(u'Врач', ['person_id'], 'vrbPerson', 6))
        self.addColumn(CRefBookCol(u'Специальность', ['speciality_id'], 'rbSpeciality', 6))
        col = self.addColumn(CDateCol(u'Установлен', ['endDate'], 10))
        self.addColumn(CRefBookCol(u'Тип', ['diagnosisType_id'], 'rbDiagnosisType', 6))
        col = self.addColumn(CRefBookCol(
            u'ГpЗд', ['healthGroup_id'], 'rbHealthGroup', 2, CRBComboBox.showCode))
        col.setToolTip(u'Группа здоровья')
        self.addColumn(CDiagnosisCol(u'Диагноз', ['MKB', 'MKBEx'], 6))
        self.addColumn(CTNMSTextCol(u'TNM-Ст', ['TNMS'],  10))
        if QtGui.qApp.isClinicalGroupDiagnosticVisible():
            self.addColumn(CEnumCol(u'КГ', ['clinicalGroup'], (u'', u'1а - подозрение', u'1б - предрак', u'2 - подлежат радикальному лечению', u'3 - ремиссия', u'4 - подлежат паллиативному лечению'), 30)).setToolTip(u'Клиническая группа')
        if QtGui.qApp.isExSubclassMKBVisible():
            col = self.addColumn(CTextCol(u'РСК', ['exSubclassMKB'], 6))
            col.setToolTip(u'Расширенная субклассификация МКБ')
        col = self.addColumn(CRefBookCol(u'Хар', ['character_id'], 'rbDiseaseCharacter', 6))
        col.setToolTip(u'Характер')
        col = self.addColumn(CRefBookCol(u'Фаза', ['phase_id'], 'rbDiseasePhases', 6))
        col.setToolTip(u'Фаза')
        col = self.addColumn(CRefBookCol(u'Ст', ['stage_id'], 'rbDiseaseStage', 6))
        col.setToolTip(u'Стадия')
        col = self.addColumn(CRefBookCol(
            u'ДН', ['dispanser_id'], 'rbDispanser', 6, CRBComboBox.showCode))
        col.setToolTip(u'Диспансерное наблюдение')
#        col = self.addColumn(CEnumCol(u'Г',['hospital'], CHospitalInfo.names, 4))
        col = self.addColumn(CTextCol(u'Госп', ['hospital'], 4))
        col.setToolTip(u'Госпитализация')
        col = self.addColumn(CRefBookCol(
            u'Тр', ['traumaType_id'], 'rbTraumaType', 6, CRBComboBox.showCode))
        col.setToolTip(u'Тип травмы')
        self.addColumn(CRefBookCol(u'ТоксВещ', ['toxicSubstances_id'], 'rbToxicSubstances', 10).setToolTip(u'Токсичное вещество'))
        self.addColumn(CRefBookCol(u'Результат', ['result_id'], 'rbDiagnosticResult', 6))
        self.addColumn(CTextCol(u'Примечания', ['notes'], 6))
        self.addColumn(CTextCol(u'Описание', ['freeInput'], 6))

#        self.addColumn(CDateCol(u'дата', ['endDate'], 6))
#        self.addColumn(CEnumCol(u'СК', ['sanatorium'], [u'не нуждается', u'нуждается', u'направлен', u'пролечен'], 4))
        db = QtGui.qApp.db
        tableDiagnostic = db.table('Diagnostic')
        tableDiagnosis  = db.table('Diagnosis')
        queryTable = tableDiagnostic.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
        self.setTable(queryTable)
        self.headerSortingCol = {}
        self._mapColumnToOrder = {u'diagnosisType_id': u'rbDiagnosisType.name', 
                                 u'healthGroup_id': u'rbHealthGroup.code', 
                                 u'MKB': u'Diagnosis.MKB',
                                 u'MKBEx': u'Diagnosis.MKBEx',
                                 u'TNMS': u'Diagnosis.TNMS',
                                 u'exSubclassMKB': u'Diagnosis.exSubclassMKB',
                                 u'character_id': u'rbDiseaseCharacter.name',
                                 u'endDate': u'Diagnostic.endDate', 
                                 u'phase_id': u'rbDiseasePhases.name',
                                 u'person_id': u'vrbPerson.name', 
                                 u'stage_id': u'rbDiseaseStage.name',
                                 u'dispanser_id': u'rbDispanser.code',
                                 u'hospital': u'Diagnostic.hospital',
                                 u'speciality_id': u'rbSpeciality.name',
                                 u'traumaType_id': u'rbTraumaType.code',
                                 u'toxicSubstances_id': u'rbToxicSubstances.name',
                                 u'result_id': u'rbDiagnosticResult.name',
                                 u'notes': u'Diagnostic.notes',
                                 u'freeInput': u'Diagnostic.freeInput',
                                 u'clinicalGroup': u'Diagnostic.clinicalGroup'
                                 }



class CAmbCardDiagnosticsVisitsTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CRefBookCol(u'Место',       ['scene_id'],         'rbScene',    15))
        self.addColumn(CDateCol(u'Дата',           ['date'],                           15))
        self.addColumn(CRefBookCol(u'Тип',         ['visitType_id'],    'rbVisitType', 15))
        self.addColumn(CRefBookCol(u'Услуга',      ['service_id'],      'rbService',   15))
        self.addColumn(CRefBookCol(u'Выполнил',    ['person_id'],     'vrbPersonWithSpeciality', 20))
        self.addColumn(CEnumCol(u'Первичный', ['isPrimary'], codeIsPrimary, 4, 'l'))
        self.addColumn(CDateCol(u'Дата ввода',     ['createDatetime'],                 15))
        self.addColumn(CDateCol(u'Дата изменения', ['modifyDatetime'],                 15))
        self.setTable('Visit')
        self.headerSortingCol = {}


class CAmbCardDiagnosticsAccompDiagnosticsTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
#        self.addColumn(CDateCol(u'дата назначения',['setDate'], 10))
        self.addColumn(CRefBookCol(u'Врач', ['person_id'], 'vrbPerson', 6))
        self.addColumn(CRefBookCol(u'Специальность', ['speciality_id'], 'rbSpeciality', 6))
        col = self.addColumn(CDateCol(u'Установлен', ['endDate'], 10))
        self.addColumn(CRefBookCol(u'Тип', ['diagnosisType_id'], 'rbDiagnosisType', 6))
        col = self.addColumn(CRefBookCol(
            u'ГpЗд', ['healthGroup_id'], 'rbHealthGroup', 2, CRBComboBox.showCode))
        col.setToolTip(u'Группа здоровья')
        self.addColumn(CDiagnosisCol(u'Диагноз', ['MKB', 'MKBEx'], 6))
        if QtGui.qApp.isExSubclassMKBVisible():
            col = self.addColumn(CTextCol(u'РСК', ['exSubclassMKB'], 6))
            col.setToolTip(u'Расширенная субклассификация МКБ')
        col = self.addColumn(CRefBookCol(u'Хар', ['character_id'], 'rbDiseaseCharacter', 6))
        col.setToolTip(u'Характер')
        col = self.addColumn(CRefBookCol(u'Фаза', ['phase_id'], 'rbDiseasePhases', 6))
        col.setToolTip(u'Фаза')
        col = self.addColumn(CRefBookCol(u'Ст', ['stage_id'], 'rbDiseaseStage', 6))
        col.setToolTip(u'Стадия')
        col = self.addColumn(CRefBookCol(
            u'ДН', ['dispanser_id'], 'rbDispanser', 6, CRBComboBox.showCode))
        col.setToolTip(u'Диспансерное наблюдение')
#        col = self.addColumn(CEnumCol(u'Г',['hospital'], CHospitalInfo.names, 4))
        col = self.addColumn(CTextCol(u'Госп', ['hospital'], 4))
        col.setToolTip(u'Госпитализация')
        col = self.addColumn(CRefBookCol(
            u'Тр', ['traumaType_id'], 'rbTraumaType', 6, CRBComboBox.showCode))
        col.setToolTip(u'Тип травмы')
        self.addColumn(CRefBookCol(u'ТоксВещ', ['toxicSubstances_id'], 'rbToxicSubstances', 10).setToolTip(u'Токсичное вещество'))
        self.addColumn(CRefBookCol(u'Результат', ['result_id'], 'rbDiagnosticResult', 6))
        self.addColumn(CTextCol(u'Примечания', ['notes'], 6))

#        self.addColumn(CDateCol(u'дата', ['endDate'], 6))
#        self.addColumn(CEnumCol(u'СК', ['sanatorium'], CHospitalInfo.names, 4))
        db = QtGui.qApp.db
        tableDiagnostic = db.table('Diagnostic')
        tableDiagnosis  = db.table('Diagnosis')
        queryTable = tableDiagnostic.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
        self.setTable(queryTable)
        self.headerSortingCol = {}


class CAmbCardDiagnosticsActionsTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CDateCol(u'Назначено',      ['directionDate'], 15))
        self.addColumn(CActionTypeCol(u'Тип',                         15))
        self.addColumn(CBoolCol(u'Срочно',         ['isUrgent'],      15))
        self.addColumn(CEnumCol(u'Состояние',      ['status'], CActionStatus.names, 4))
        self.addColumn(CDateCol(u'План',           ['plannedEndDate'],15))
        self.addColumn(CDateCol(u'Начато',         ['begDate'],       15))
        self.addColumn(CDateCol(u'Окончено',       ['endDate'],       15))
        self.addColumn(CTextCol(u'МКБ',                        ['MKB'],                       15))
        self.addColumn(CRefBookCol(u'Назначил',    ['setPerson_id'], 'vrbPersonWithSpeciality', 20))
        self.addColumn(CRefBookCol(u'Выполнил',    ['person_id'],    'vrbPersonWithSpeciality', 20))
        self.addColumn(CTextCol(u'Каб',            ['office'],                                6))
        self.addColumn(CTextCol(u'Примечания',     ['note'],                                  6))
        self.setTable('Action')
        self.headerSortingCol = {}
        self._mapColumnToOrder = {u'directionDate'      :u'Action.directionDate',
                                 u'actionType_id'      :u'ActionType.name',
                                 u'isUrgent'           :u'Action.isUrgent',
                                 u'status'             :u'Action.status',
                                 u'plannedEndDate'     :u'Action.plannedEndDate',
                                 u'begDate'            :u'Action.begDate',
                                 u'endDate'            :u'Action.endDate',
                                 u'MKB'                :u'Action.MKB',
                                 u'setPerson_id'       :u'vrbPersonWithSpeciality.name',
                                 u'person_id'          :u'vrbPersonWithSpeciality.name',
                                 u'office'             :u'Action.office',
                                 u'note'               :u'Action.note'
                                 }


    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]


class CAmbCardStatusActionsTableModel(CAmbCardDiagnosticsActionsTableModel):
    pass


class CAmbCardVisitTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)

        self.addColumn(CRefBookCol(u'Врач',               ['person_id'],    'vrbPersonWithSpeciality', 20))
        self.addColumn(CRefBookCol(u'Ассистент',          ['assistant_id'], 'vrbPersonWithSpeciality', 20))
        self.addColumn(CRefBookCol(u'Место',              ['scene_id'],     'rbScene',                 10))
        self.addColumn(CDateCol(u'Дата',                  ['date'],                                    15))
        self.addColumn(CRefBookCol(u'Тип визита',         ['visitType_id'], 'rbVisitType',             10))
        self.addColumn(CRefBookCol(u'Услуга',             ['service_id'],   'rbService',               20))
        self.addColumn(CRefBookCol(u'Тип финансирования', ['finance_id'],   'rbFinance',               10))
        self.loadField('event_id')
        self.setTable('Visit')
        self.headerSortingCol = {}
        self._mapColumnToOrder = {u'person_id'    :u'vrbPersonWithSpeciality.name',
                                  u'assistant_id' :u'vrbPersonWithSpeciality.name',
                                  u'scene_id'     :u'rbScene.name',
                                  u'date'         :u'Visit.date',
                                  u'visitType_id' :u'rbVisitType.name',
                                  u'service_id'   :u'rbService.name',
                                  u'finance_id'   :u'rbFinance.name'
                                 }


    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]


class CAmbCardAttachedFilesTableModel(CAttachedFilesModel):
    def __init__(self, parent):
        CAttachedFilesModel.__init__(self, parent)
        self.setInterface(QtGui.qApp.webDAVInterface)

    def loadItems(self, clientId, filterFiles={u'docTableName': u'All'}):
        db = QtGui.qApp.db
        # items = CAttachedFilesLoader.loadtems(self.interface, 'Client_FileAttach', clientId)
        # tableEvent = db.table('Event')
        # tableAction = db.table('Action')
        # for eventId in db.getIdList(tableEvent,
        #                             'id',
        #                             where=['deleted=0',
        #                                    tableEvent['client_id'].eq(clientId),
        #                                   ]
        #                            ):
        #     items.extend(CAttachedFilesLoader.loadItems(self.interface, 'Event_FileAttach', eventId))
        #     for actionId in db.getIdList(tableAction,
        #                                  'id',
        #                                  where=['deleted=0',
        #                                         tableAction['event_id'].eq(eventId),
        #                                        ]
        #                                 ):
        #         items.extend(CAttachedFilesLoader.loadItems(self.interface, 'Action_FileAttach', actionId))

        # была жалоба на скорость. Я подумал так быстрее
        items = CAttachedFilesLoader.loadAllItems(self.interface, clientId, filterFiles)
        eventsToActionsMap = {}
        actionIdList = []
        eventIdList = []
        for item in items:
            record = item.getRecord(None)
            objTable = forceString(record.value('objectTableName'))
            if objTable == 'Action':
                actionIdList.append(forceRef(record.value('master_id')))
            elif objTable == 'Event':
                eventIdList.append(forceRef(record.value('master_id')))
        if actionIdList:
            tableAction = db.table('Action')
            records = db.getRecordList(tableAction, [tableAction['id'], tableAction['event_id']], [tableAction['deleted'].eq(0), tableAction['id'].inlist(actionIdList)])
            for rec in records:
                eventsToActionsMap[forceRef(rec.value('id'))] = forceRef(rec.value('event_id'))
        # Получаем список event.id в которых есть запрещённые к показу диагнозы (Mantis 0015028)
        eventIdList.extend(list(eventsToActionsMap.values()))
        # restrictedEventIdList = getRestrictedEventIdList(eventIdList, True)
        restrictedEventIdList = []
        viewItems = []
        # Фильтруем первоначальный список файлов, убираем те, которые относятся к запрещённым к показу событиям и действиям
        for item in items:
            record = item.getRecord(None)
            objTable = forceString(record.value('objectTableName'))
            if objTable == 'Action':
                if eventsToActionsMap[forceRef(record.value('master_id'))] not in restrictedEventIdList:
                    viewItems.append(item)
            elif objTable == 'Event':
                if forceRef(record.value('master_id')) not in restrictedEventIdList:
                    viewItems.append(item)
            else:
                if forceRef(record.value('master_id')) not in restrictedEventIdList:
                    viewItems.append(item)

        self.items = viewItems
        column, order = self._getOrderFromPrefs()
        self.sort(column, order)
        self.reset()

    def saveItems(self, masterId):
        pass

    def setItems(self, items):
        self.items = items
        column, order = self._getOrderFromPrefs()
        self.sort(column, order)

    def _getOrderFromPrefs(self):
        column = getPrefInt(QtGui.qApp.preferences.appPrefs, 'CAmbCardAttachedFilesTableModel_orderColumn', 3)
        order = getPrefInt(QtGui.qApp.preferences.appPrefs, 'CAmbCardAttachedFilesTableModel_order', 1)
        return column, Qt.AscendingOrder if order == 0 else Qt.DescendingOrder

    def _setOrderToPrefs(self, column, order):
        setPref(QtGui.qApp.preferences.appPrefs, u'CAmbCardAttachedFilesTableModel_orderColumn', column)
        setPref(QtGui.qApp.preferences.appPrefs, u'CAmbCardAttachedFilesTableModel_order', forceInt(order))

    def sort(self, column, order=Qt.AscendingOrder):
        CAttachedFilesModel.sort(self, column, order)
        self._setOrderToPrefs(column, order)


# ##################################3

class CRegistryActionsTableView(CTableView):
    def __init__(self, parent):
        CTableView.__init__(self, parent)
        self._order = 'Action.begDate DESC'
        self._orderColumn = None
        self._isDesc = True


    def order(self):
        return self._order


    def setOrder(self, column):
        if column is not None:
            self._isDesc = not self._isDesc if self._orderColumn == column else False
            self._order = self.getOrder(column) + (' DESC' if self._isDesc else ' ASC')
            self._orderColumn = column
            self.horizontalHeader().setSortIndicator(column, Qt.DescendingOrder if self._isDesc else Qt.AscendingOrder)
        else:
            self._order = None
            self._orderColumn = None
            self._isDesc = True


    def getOrder(self, column):
        return self.model().getOrder(self.model().cols()[column].fields()[0], column)


    def setClientInfoHidden(self, hideClientInfo):
        verticalHeaderView = self.verticalHeader()
        h = self.fontMetrics().height()
        if hideClientInfo:
            verticalHeaderView.setDefaultSectionSize(3*h/2)
            verticalHeaderView.hide()
        else:
            verticalHeaderView.setDefaultSectionSize(3*h)
            verticalHeaderView.show()
#        self.model().reset()


    def contentToHTML(self, showMask=None):
        model = self.model()
        cols = model.cols()
        if showMask is None:
            showMask = [None]*(len(cols)+1)
        _showMask = [ not self.isColumnHidden(iCol) if v is None else v
                      for iCol, v in enumerate(showMask)
                    ]
        for idx, elem in enumerate(cols):
            if u''.join(forceString(elem.title().toString()).upper().split('.')) == u'ФИО':
                _showMask[idx] = True

        QtGui.qApp.startProgressBar(model.rowCount())
        try:
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)

            cursor.setCharFormat(CReportBase.ReportTitle)
            header = self.reportHeader()
            if Qt.mightBeRichText(header):
                cursor.insertHtml(header)
            else:
                cursor.insertText(header)
            cursor.insertBlock()
            cursor.setCharFormat(CReportBase.ReportBody)
            description = self.reportDescription()
            if Qt.mightBeRichText(description):
                cursor.insertHtml(description)
            else:
                cursor.insertText(description)
            cursor.insertBlock()

            colWidths  = [ self.columnWidth(i) for i in xrange(len(cols)+1) ]
            colWidths[0]= 10
            totalWidth = sum(colWidths)
            tableColumns = []
            for iCol, colWidth in enumerate(colWidths):
                widthInPercents = str(max(1, colWidth*90/totalWidth))+'%'
                if iCol == 0:
                    tableColumns.append((widthInPercents, [u'№'], CReportBase.AlignRight))
                else:
                    if not _showMask[iCol-1]:
                        continue
                    col = cols[iCol-1]
                    colAlingment = Qt.AlignHorizontal_Mask & forceInt(col.alignment())
                    format = QtGui.QTextBlockFormat()
                    format.setAlignment(Qt.AlignmentFlag(colAlingment))
                    tableColumns.append((widthInPercents, [forceString(col.title())], format))

            table = createTable(cursor, tableColumns)
            for iModelRow in xrange(model.rowCount()):
                QtGui.qApp.stepProgressBar()
                QtGui.qApp.processEvents(QEventLoop.ExcludeUserInputEvents)
                iTableRow = table.addRow()
                table.setText(iTableRow, 0, iModelRow+1)
                headerData = model.headerData(iTableRow-1, Qt.Vertical)
                table.setText(iTableRow, 1, forceString(headerData))
                iTableCol = 1
                for iModelCol in xrange(len(cols)):
                    if not _showMask[iModelCol]:
                        continue
                    index = model.createIndex(iModelRow, iModelCol)
                    text = forceString(model.data(index))
                    table.setText(iTableRow, iTableCol, text)
                    iTableCol += 1
            return doc
        finally:
            QtGui.qApp.stopProgressBar()


    def showRecordProperties(self):
        table = self.model().table()
        itemId = self.currentItemId()
        CRecordProperties(self, table, itemId, showRecordId=True).exec_()


class CRegistryActionsMCTableView(CExtendedSelectionTableView):
    def __init__(self, parent):
        CExtendedSelectionTableView.__init__(self, parent)
        self._order = None
        self._orderColumn = None
        self._isDesc = True


class CActionsTableModel(CTableModel):
    class CLocClientColumn(CEventsTableModel.CLocClientColumn):
        def __init__(self, title, fields, defaultWidth, clientCache, eventCache):
            CEventsTableModel.CLocClientColumn.__init__(self, title, fields, defaultWidth, clientCache)
            self.eventCache = eventCache


        def format(self, values):
            val = values[0]
            eventId  = forceRef(val)
            eventRecord = self.eventCache.get(eventId)
            if eventRecord:
                clientValues = [eventRecord.value('client_id')]
                clientVal = clientValues[0]
                clientId  = forceRef(clientVal)
                clientRecord = self.clientCache.get(clientId)
                if clientRecord:
                    name  = formatNameInt(forceString(clientRecord.value('lastName')),
                                       forceString(clientRecord.value('firstName')),
                                       forceString(clientRecord.value('patrName')))
                    return toVariant(name)
                return CCol.invalid
            return CCol.invalid


    class CLocClientIdentifierColumn(CCol):
        def __init__(self, title, fields, defaultWidth, eventCache):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.eventCache = eventCache
            self.identifiersCache = CRecordCache()


        def getClientIdentifier(self, clientId):
            identifier = self.identifiersCache.get(clientId)
            if identifier is None:
                accountingSystemId = QtGui.qApp.defaultAccountingSystemId()
                if accountingSystemId is None:
                    identifier = clientId
                else:
                    db = QtGui.qApp.db
                    tableClientIdentification = db.table('ClientIdentification')
                    cond = [tableClientIdentification['client_id'].eq(clientId),
                            tableClientIdentification['accountingSystem_id'].eq(accountingSystemId)]
                    record = db.getRecordEx(tableClientIdentification, tableClientIdentification['identifier'], cond)
                    identifier = forceString(record.value(0)) if record else ''
                self.identifiersCache.put(clientId, identifier)
            return identifier


        def format(self, values):
            val = values[0]
            eventId = forceRef(val)
            eventRecord = self.eventCache.get(eventId)
            if eventRecord:
                clientId = forceRef(eventRecord.value('client_id'))
                return toVariant(self.getClientIdentifier(clientId))
            return CCol.invalid


    class CLocClientBirthDateColumn(CEventsTableModel.CLocClientBirthDateColumn):
        def __init__(self, title, fields, defaultWidth, clientCache, eventCache):
            CEventsTableModel.CLocClientBirthDateColumn.__init__(self, title, fields, defaultWidth, clientCache)
            self.eventCache = eventCache

        def format(self, values):
            val = values[0]
            eventId  = forceRef(val)
            eventRecord = self.eventCache.get(eventId)
            if eventRecord:
                return CEventsTableModel.CLocClientBirthDateColumn.format(self, [eventRecord.value('client_id')])
            return CCol.invalid


    class CLocClientSexColumn(CEventsTableModel.CLocClientSexColumn):
        def __init__(self, title, fields, defaultWidth, clientCache, eventCache):
            CEventsTableModel.CLocClientSexColumn.__init__(self, title, fields, defaultWidth, clientCache)
            self.eventCache = eventCache

        def format(self, values):
            val = values[0]
            eventId  = forceRef(val)
            eventRecord = self.eventCache.get(eventId)
            if eventRecord:
                return CEventsTableModel.CLocClientSexColumn.format(self, [eventRecord.value('client_id')])
            return CCol.invalid

    class  CExternalIdColumn(CTextCol):
        def __init__(self, title, fields, defaultWidth):
            CTextCol.__init__(self, title, fields, defaultWidth)
            self._cache = {}

        def format(self, values):
            eventId = forceRef(values[0])
            result = self._cache.get(eventId, u'')
            if not result:
                db = QtGui.qApp.db
                externalId = db.translate('Event', 'id', eventId, 'externalId')
                result = forceString(externalId)
                self._cache[eventId] = result
            return result

    class  CFinanceIdColumn(CTextCol):
        def __init__(self, title, fields, defaultWidth):
            CTextCol.__init__(self, title, fields, defaultWidth)
            self._cache = {}

        def format(self, values):
            financeId = forceRef(values[0])
            result = self._cache.get(financeId, u'')
            if not result:
                db = QtGui.qApp.db
                financeName = db.translate('rbFinance', 'id', financeId, 'name')
                result = forceString(financeName)
                self._cache[financeId] = result
            return result

    class  CContractIdColumn(CTextCol):
        def __init__(self, title, fields, defaultWidth):
            CTextCol.__init__(self, title, fields, defaultWidth)
            self._cache = {}

        def format(self, values):
            contractId = forceRef(values[0])
            result = self._cache.get(contractId, u'')
            contractName = None
            if not result and contractId:
                db = QtGui.qApp.db
                query = db.query('SELECT concat_ws(" ", number, date, resolution) FROM Contract where id=%d'%contractId)
                if query.next():
                    contractName = query.value(0)
                result = forceString(contractName)
                self._cache[contractId] = result
            return result

    class CLocEventExternalIdColumn(CDesignationCol):
        def __init__(self, title, fields, designationChain, defaultWidth, extraFields=[], alignment='l'):
            CDesignationCol.__init__(self, title, fields, designationChain, defaultWidth, alignment)
            self.extraFields = extraFields


    class CLocDateShowTimeColumn(CDateCol):
        def format(self, values):
            val = values[0]
            actionTypeId  = forceRef(values[1])
            if actionTypeId:
                actionType   = CActionTypeCache.getById(actionTypeId)
                showTime = actionType.showTime
                if showTime:
                    val = val.toDateTime()
                    return QVariant(val.toString('dd.MM.yyyy hh:mm'))
                else:
                    val = val.toDate()
                    return QVariant(val.toString('dd.MM.yyyy'))
            return CCol.invalid


    def __init__(self, parent, clientCache, eventCache):
        CTableModel.__init__(self, parent)
        clientCol   = CActionsTableModel.CLocClientColumn( u'Ф.И.О.', ['event_id'], 60, clientCache, eventCache)
#        clientIdentifierCol = CActionsTableModel.CLocClientIdentifierColumn(u'Идентификатор', ['event_id'], 30, eventCache)
        clientBirthDateCol = CActionsTableModel.CLocClientBirthDateColumn(u'Дата рожд.', ['event_id'], 20, clientCache, eventCache)
        clientSexCol = CActionsTableModel.CLocClientSexColumn(u'Пол', ['event_id'], 5, clientCache, eventCache)
        self.addColumn(clientCol)
        self.addColumn(clientBirthDateCol)
        self.addColumn(clientSexCol)
        self.addColumn(CActionsTableModel.CLocDateShowTimeColumn(u'Назначено',      ['directionDate', 'actionType_id'], 15))
        self.addColumn(CActionTypeCol(u'Тип',                         15))
        self.addColumn(CIntCol(u'Количество',      ['amount'],        6))
        self.addColumn(CTextCol(u'УЕТ',            ['uet'],             6))
        self.addColumn(CBoolCol(u'Срочно',         ['isUrgent'],      15))
        self.addColumn(CEnumCol(u'Состояние',      ['status'], CActionStatus.names, 4))
        self.addColumn(CActionsTableModel.CLocDateShowTimeColumn(u'План',           ['plannedEndDate', 'actionType_id'],15))
        self.addColumn(CActionsTableModel.CLocDateShowTimeColumn(u'Начато',         ['begDate', 'actionType_id'],       15))
        self.addColumn(CActionsTableModel.CLocDateShowTimeColumn(u'Окончено',       ['endDate', 'actionType_id'],       15))
        self.addColumn(CTextCol(u'МКБ',            ['MKB'],       15))
        self.addColumn(CRefBookCol(u'Назначил',    ['setPerson_id'], 'vrbPersonWithSpeciality', 20))
        self.addColumn(CRefBookCol(u'Выполнил',    ['person_id'],    'vrbPersonWithSpeciality', 20))
        self.addColumn(CTextCol(u'Каб',            ['office'],                                6))
        self.addColumn(CTextCol(u'Примечания',     ['note'],                                  6))
        self.addColumn(CActionsTableModel.CLocEventExternalIdColumn(u'Номер документа', ['event_id'],   ('Event', 'externalId'), 20, ['externalId']))
        self.addColumn(CRefBookCol(u'Тип финансирования',  ['finance_id'], 'rbFinance',    10))
#        self.addColumn(CRefBookCol(u'Договор',            ['contract_id'], 'vrbContract', 20))
        self.addColumn(CDesignationCol(u'Договор',         ['contract_id'],('vrbContract', 'code'), 20))
        self.loadField('id')
        self.loadField('event_id')
        self.loadField('amount')
        self.setTable('Action')
        self._mapColumnToOrder = {u'event_id'           :u'CONCAT(Client.lastName, Client.firstName, Client.patrName)',
                                 u'birthDate'          :u'Client.birthDate',
                                 u'sex'                :u'Client.sex',
                                 u'directionDate'      :u'Action.directionDate',
                                 u'actionType_id'      :u'Action.actionType_id',
                                 u'amount'             :u'Action.amount',
                                 u'uet'                :u'Action.uet',
                                 u'isUrgent'           :u'Action.isUrgent',
                                 u'status'             :u'Action.status',
                                 u'plannedEndDate'     :u'Action.plannedEndDate',
                                 u'begDate'            :u'Action.begDate',
                                 u'endDate'            :u'Action.endDate',
                                 u'MKB'                :u'Action.MKB',
                                 u'setPerson_id'       :u'vrbSetPersonWithSpeciality.name',
                                 u'person_id'          :u'vrbPersonWithSpeciality.name',
                                 u'office'             :u'Action.office',
                                 u'note'               :u'Action.note',
                                 u'externalId'         :u'Event.externalId',
                                 u'finance_id'         :u'rbFinance.code',
                                 u'contract_id'        :u'vrbContract.code'
                                 }

    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]


#    def headerData(self, section, orientation, role=Qt.DisplayRole):
##        if orientation == Qt.Vertical:
##            if role == Qt.DisplayRole:
##                id = self._idList[section]
##                self._recordsCache.weakFetch(id, self._idList[max(0, section-self.fetchSize):(section+self.fetchSize)])
##                record = self._recordsCache.get(id)
##                clientValues   = self.clientCol.extractValuesFromRecord(record)
##                clientValue = forceString(self.clientCol.format(clientValues))
##                clientIdentifier = ''
##                clientIdentifierValues = self.clientIdentifierCol.extractValuesFromRecord(record)
##                clientIdentifier = forceString(self.clientIdentifierCol.format(clientIdentifierValues))
##                clientBirthDateValues = self.clientBirthDateCol.extractValuesFromRecord(record)
##                clientBirthDate = forceString(self.clientBirthDateCol.format(clientBirthDateValues))
##                clientSexValues = self.clientSexCol.extractValuesFromRecord(record)
##                clientSex = forceString(self.clientSexCol.format(clientSexValues))
##                clientFIOSex = u', '.join([clientValue, clientSex])
##                birthDateSex = u', '.join([clientIdentifier, clientBirthDate])
##                result =  u'\n'.join([clientFIOSex, birthDateSex])
##                return QVariant(result)
#        return CTableModel.headerData(self, section, orientation, role)


    def getActionsTotal(self):
        """Возвращает статистику по действиям модели"""
        # type: () -> dict[str, Union[int, float]]
        amount = 0.0
        uet = 0.0
        clients = set() # type: set[int]
        if self.idList():
            # Got a packet bigger than 'max_allowed_packet' bytes.
            # чтобы не получать такую ошибку из-за длинного idList,
            # разбиваем на куски по 300 штук
            db = QtGui.qApp.db
            tableA = db.table("Action")
            tableE = db.table('Event')
            table = tableA.innerJoin(tableE, tableA['event_id'].eq(tableE['id']))
            cols = [
                tableE["client_id"],
                tableA["uet"],
                tableA["amount"],
            ]

            def _getActionsTotal(idListChunk):
                amount = 0.0
                uet = 0.0
                clients = set() # type: set[int]
                records = db.getRecordList(table, cols, tableA["id"].inlist(idListChunk))
                for record in records:
                    amount += forceDouble(record.value("amount"))
                    uet += forceDouble(record.value("uet"))
                    clients.add(forceInt(record.value("client_id")))
                return {
                    "amount": amount,
                    "uet": uet,
                    "clients": clients,
                }

            result = QtGui.qApp.callWithProgressBar(
                None,
                _getActionsTotal,
                list(getListChunks(self.idList(), 300)),
            ) or []
            if result:
                # совмещаем результаты
                for x in result:
                    amount += x["amount"]
                    uet += x["uet"]
                    clients.update(x["clients"])

        # TODO: возвращать dataclass вместо словаря?
        return {
            "amount": amount,
            "uet": uet,
            "clientsCount": len(clients),
        }
    
    
    def getClientCount(self):
        if self.idList():
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableEvent  = db.table('Event')
            tableAction = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))

            # Got a packet bigger than 'max_allowed_packet' bytes.
            # чтобы не получать такую ошибку из-за длинного actionIdList,
            # разбиваем на куски по 100 штук
            clients = set() # type: set[int]
            for idList in getListChunks(self._idList, 100):
                clients.update(db.getIdList(tableAction, tableEvent['client_id'], tableAction['id'].inlist(idList)))

            clientCount = len(clients)
            return clientCount
        return 0
    
    
    def getEventCount(self):
        if self.idList():
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            EventCount = db.getDistinctCount(tableAction,
                                                'event_id',
                                                tableAction['id'].inlist(self._idList)
                                               )
            return EventCount
        return 0


class CMedicalCommissionActionsTableModel(CActionsTableModel):
    class CLocActionPropertiColumn(CCol):
        def __init__(self, title, fields, propertiName, defaultWidth, alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self.actionCaches = {}
            self.propertiName = propertiName

        def clearActionCaches(self):
            self.actionCaches.clear()

        def updateActionCaches(self, id):
            if id in self.actionCaches.keys():
                self.actionCaches.pop(id, None)

        def format(self, values):
            actionId = forceRef(values[0])
            if actionId:
                action = self.actionCaches.get(actionId, None)
                if not action:
                    db = QtGui.qApp.db
                    tableAction = db.table('Action')
                    record = db.getRecordEx(tableAction, '*', [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0)])
                    if record:
                        action = CAction(record=record)
                        if action:
                            self.actionCaches[actionId] = action
                if action and self.propertiName in action._actionType._propertiesByName:
                    return QVariant(action[self.propertiName])
            return CCol.invalid

    class CLocActionDateColumn(CCol):
        def __init__(self, title, fields, fieldName, defaultWidth, alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self.actionCaches = {}
            self.fieldName = fieldName

        def clearActionCaches(self):
            self.actionCaches.clear()

        def updateActionCaches(self, id):
            if id in self.actionCaches.keys():
                self.actionCaches.pop(id, None)

        def format(self, values):
            actionId = forceRef(values[0])
            actionTypeId = forceRef(values[1])
            if actionId:
                record = self.actionCaches.get(actionId, None)
                if not record:
                    db = QtGui.qApp.db
                    tableAction = db.table('Action')
                    record = db.getRecordEx(tableAction, '*', [tableAction['prevAction_id'].eq(actionId), tableAction['deleted'].eq(0)])
                    if record:
                        self.actionCaches[actionId] = record
                if record and self.fieldName:
                    actionTypeId = forceRef(record.value('actionType_id'))
                    if actionTypeId:
                        actionType   = CActionTypeCache.getById(actionTypeId)
                        showTime = actionType.showTime
                        if showTime:
                            val = forceDateTime(record.value(self.fieldName))
                            return QVariant(val.toString('dd.MM.yyyy hh:mm'))
                        else:
                            val = forceDate(record.value(self.fieldName))
                            return QVariant(val.toString('dd.MM.yyyy'))
                    return CCol.invalid
            return CCol.invalid

    Col_Number = 4
    Col_NumberMC = 5
    Col_Decision = 14

    def __init__(self, parent, clientCache, eventCache):
        CActionsTableModel.__init__(self, parent, clientCache, eventCache)
        self._cols = []
        clientCol   = CActionsTableModel.CLocClientColumn( u'Ф.И.О.', ['event_id'], 60, clientCache, eventCache)
        clientBirthDateCol = CActionsTableModel.CLocClientBirthDateColumn(u'Дата рожд.', ['event_id'], 20, clientCache, eventCache)
        clientSexCol = CActionsTableModel.CLocClientSexColumn(u'Пол', ['event_id'], 5, clientCache, eventCache)
        self.addColumn(clientCol)
        self.addColumn(clientBirthDateCol)
        self.addColumn(clientSexCol)
        self.addColumn(CActionTypeCol(u'Тип', 15, showFields=CRBComboBox.showName))
        self.addColumn(CMedicalCommissionActionsTableModel.CLocActionPropertiColumn(u'Номер',    ['id'], u'Номер',    15))
        self.addColumn(CMedicalCommissionActionsTableModel.CLocActionPropertiColumn(u'Номер ЛН', ['id'], u'Номер ЛН', 15))
        self.addColumn(CEnumCol(                                 u'Состояние', ['status'], CActionStatus.names,    4))
        self.addColumn(CActionsTableModel.CLocDateShowTimeColumn(u'Назначено', ['directionDate', 'actionType_id'], 15))
        self.addColumn(CActionsTableModel.CLocDateShowTimeColumn(u'План',      ['plannedEndDate', 'actionType_id'],15))
        self.addColumn(CActionsTableModel.CLocDateShowTimeColumn(u'Начато',    ['begDate', 'actionType_id'],       15))
        self.addColumn(CActionsTableModel.CLocDateShowTimeColumn(u'Окончено',  ['endDate', 'actionType_id'],       15))
        self.addColumn(CTextCol(   u'МКБ',        ['MKB'],                                     15))
        self.addColumn(CRefBookCol(u'Назначил',   ['setPerson_id'], 'vrbPersonWithSpeciality', 20))
        self.addColumn(CRefBookCol(u'Выполнил',   ['person_id'],    'vrbPersonWithSpeciality', 20))
        self.addColumn(CMedicalCommissionActionsTableModel.CLocActionPropertiColumn(u'Решение', ['id'], u'Решение', 50))
        self.addColumn(CTextCol(   u'Примечания', ['note'],                                    6))
        self.loadField('id')
        self.loadField('event_id')
        self.setTable('Action')
        self._mapColumnToOrder ={u'event_id'           :u'CONCAT(Client.lastName, Client.firstName, Client.patrName)',
                                 u'birthDate'          :u'Client.birthDate',
                                 u'sex'                :u'Client.sex',
                                 u'directionDate'      :u'Action.directionDate',
                                 u'actionType_id'      :u'Action.actionType_id',
                                 u'status'             :u'Action.status',
                                 u'plannedEndDate'     :u'Action.plannedEndDate',
                                 u'begDate'            :u'Action.begDate',
                                 u'endDate'            :u'Action.endDate',
                                 u'MKB'                :u'Action.MKB',
                                 u'setPerson_id'       :u'vrbSetPersonWithSpeciality.name',
                                 u'person_id'          :u'vrbPersonWithSpeciality.name',
                                 u'note'               :u'Action.note',
                                 u'id'                 :u'expertDecision',
                                 }


    def getOrder(self, fieldName, column):
        if column == CMedicalCommissionActionsTableModel.Col_Number:
            return u'expertNumberExpertise'
        elif column == CMedicalCommissionActionsTableModel.Col_NumberMC:
            return u'expertNumberMC'
        elif column == CMedicalCommissionActionsTableModel.Col_Decision:
            return u'expertDecision'
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]


    def updateColumnsCaches(self, id):
        self._cols[CMedicalCommissionActionsTableModel.Col_Number].updateActionCaches(id)
        self._cols[CMedicalCommissionActionsTableModel.Col_NumberMC].updateActionCaches(id)
        self._cols[CMedicalCommissionActionsTableModel.Col_Decision].updateActionCaches(id)


    def clearColumnsCaches(self):
        self._cols[CMedicalCommissionActionsTableModel.Col_Number].clearActionCaches()
        self._cols[CMedicalCommissionActionsTableModel.Col_NumberMC].clearActionCaches()
        self._cols[CMedicalCommissionActionsTableModel.Col_Decision].clearActionCaches()


    def data(self, index, role=Qt.DisplayRole):
        result = CActionsTableModel.data(self, index, role)
        if role == Qt.ToolTipRole:
            column = index.column()
            if column == CMedicalCommissionActionsTableModel.Col_Decision:
                row = index.row()
                (col, values) = self.getRecordValues(column, row)
                return col.format(values)
        return result


class CProtocolMCActionsTableModel(CMedicalCommissionActionsTableModel):
    Col_DirectionDateMSI  = 16
    Col_PlannedEndDateMSI = 17
    Col_EndDateMSI        = 18

    def __init__(self, parent, clientCache, eventCache):
        CMedicalCommissionActionsTableModel.__init__(self, parent, clientCache, eventCache)
        self.addColumn(CMedicalCommissionActionsTableModel.CLocActionDateColumn(u'Направление на МСЭ', ['id', 'actionType_id'], 'directionDate',  15))
        self.addColumn(CMedicalCommissionActionsTableModel.CLocActionDateColumn(u'Регистрация МСЭ',    ['id', 'actionType_id'], 'plannedEndDate', 15))
        self.addColumn(CMedicalCommissionActionsTableModel.CLocActionDateColumn(u'Выполнение МСЭ',     ['id', 'actionType_id'], 'endDate',        15))
        self.setTable('Action')
        self._mapColumnToOrder ={'event_id'           :'CONCAT(Client.lastName, Client.firstName, Client.patrName)',
                                 'birthDate'          :'Client.birthDate',
                                 'sex'                :'Client.sex',
                                 'directionDate'      :'Action.directionDate',
                                 'actionType_id'      :'Action.actionType_id',
                                 'status'             :'Action.status',
                                 'plannedEndDate'     :'Action.plannedEndDate',
                                 'begDate'            :'Action.begDate',
                                 'endDate'            :'Action.endDate',
                                 'MKB'                :'Action.MKB',
                                 'setPerson_id'       :'vrbSetPersonWithSpeciality.name',
                                 'person_id'          :'vrbPersonWithSpeciality.name',
                                 'note'               :'Action.note',
                                 'id'                 :'endDateMSI',
                                 }


    def getOrder(self, fieldName, column):
        if column == CProtocolMCActionsTableModel.Col_DirectionDateMSI:
            return u'directionDateMSI'
        elif column == CProtocolMCActionsTableModel.Col_PlannedEndDateMSI:
            return u'plannedEndDateMSI'
        elif column == CProtocolMCActionsTableModel.Col_EndDateMSI:
            return u'endDateMSI'
        else:
            return CMedicalCommissionActionsTableModel.getOrder(self, fieldName, column)
        # return self._mapColumnToOrder[fieldName]


    def updateColumnsCaches(self, id):
        CMedicalCommissionActionsTableModel.updateColumnsCaches(self, id)
        self._cols[CProtocolMCActionsTableModel.Col_DirectionDateMSI].updateActionCaches(id)
        self._cols[CProtocolMCActionsTableModel.Col_PlannedEndDateMSI].updateActionCaches(id)
        self._cols[CProtocolMCActionsTableModel.Col_EndDateMSI].updateActionCaches(id)


    def clearColumnsCaches(self):
        CMedicalCommissionActionsTableModel.clearColumnsCaches(self)
        self._cols[CProtocolMCActionsTableModel.Col_DirectionDateMSI].clearActionCaches()
        self._cols[CProtocolMCActionsTableModel.Col_PlannedEndDateMSI].clearActionCaches()
        self._cols[CProtocolMCActionsTableModel.Col_EndDateMSI].clearActionCaches()


class CMedicalSocialInspectionActionsTableModel(CMedicalCommissionActionsTableModel):
    class CLocDateActionPropertiColumn(CDateCol):
        def __init__(self, title, fields, propertiName, defaultWidth, alignment='l', highlightRedDate=True):
            CDateCol.__init__(self, title, fields, defaultWidth, alignment)
            self.actionCaches = {}
            self.propertiName = propertiName

        def clearActionCaches(self):
            self.actionCaches.clear()

        def updateActionCaches(self, id):
            if id in self.actionCaches.keys():
                self.actionCaches.pop(id, None)

        def format(self, values):
            actionId = forceRef(values[0])
            if actionId:
                action = self.actionCaches.get(actionId, None)
                if not action:
                    db = QtGui.qApp.db
                    tableAction = db.table('Action')
                    record = db.getRecordEx(tableAction, '*', [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0)])
                    if record:
                        action = CAction(record=record)
                        if action:
                            self.actionCaches[actionId] = action
                if action and self.propertiName in action._actionType._propertiesByName:
                    properti = action[self.propertiName]
                    if properti:
                        return QVariant(properti.toString(Qt.LocaleDate))
            return CCol.invalid

    Col_Decision = 16
    Col_DisabilityGroup = 17

    def __init__(self, parent, clientCache, eventCache):
        CMedicalCommissionActionsTableModel.__init__(self, parent, clientCache, eventCache)
        self._cols = []
        clientCol   = CActionsTableModel.CLocClientColumn( u'Ф.И.О.', ['event_id'], 60, clientCache, eventCache)
        clientBirthDateCol = CActionsTableModel.CLocClientBirthDateColumn(u'Дата рожд.', ['event_id'], 20, clientCache, eventCache)
        clientSexCol = CActionsTableModel.CLocClientSexColumn(u'Пол', ['event_id'], 5, clientCache, eventCache)
        self.addColumn(clientCol)
        self.addColumn(clientBirthDateCol)
        self.addColumn(clientSexCol)
        self.addColumn(CActionTypeCol(u'Тип', 15, showFields=CRBComboBox.showName))
        self.addColumn(CMedicalCommissionActionsTableModel.CLocActionPropertiColumn(u'Номер',    ['id'], u'Номер',    15))
        self.addColumn(CMedicalCommissionActionsTableModel.CLocActionPropertiColumn(u'Номер ЛН', ['id'], u'Номер ЛН', 15))
        self.addColumn(CEnumCol(                                 u'Состояние', ['status'], CActionStatus.names,    4))
        self.addColumn(CActionsTableModel.CLocDateShowTimeColumn(u'Назначено', ['directionDate', 'actionType_id'], 15))
        self.addColumn(CActionsTableModel.CLocDateShowTimeColumn(u'План',      ['plannedEndDate', 'actionType_id'],15))
        self.addColumn(CActionsTableModel.CLocDateShowTimeColumn(u'Начато',    ['begDate', 'actionType_id'],       15))
        self.addColumn(CActionsTableModel.CLocDateShowTimeColumn(u'Окончено',  ['endDate', 'actionType_id'],       15))
        self.addColumn(CTextCol(   u'МКБ',        ['MKB'],                                     15))
        self.addColumn(CRefBookCol(u'Назначил',   ['setPerson_id'], 'vrbPersonWithSpeciality', 20))
        self.addColumn(CRefBookCol(u'Выполнил',   ['person_id'],    'vrbPersonWithSpeciality', 20))
        self.addColumn(CMedicalSocialInspectionActionsTableModel.CLocDateActionPropertiColumn(u'Рег-ция', ['id'], u'Дата регистрации МСЭ',         50).setToolTip(u'Дата регистрации документов в бюро МСЭ'))
        self.addColumn(CMedicalSocialInspectionActionsTableModel.CLocDateActionPropertiColumn(u'МСЭ',     ['id'], u'Дата освидетельствования МСЭ', 50).setToolTip(u'Дата освидетельствования в бюро МСЭ'))
        self.addColumn(CMedicalCommissionActionsTableModel.CLocActionPropertiColumn(u'Результат', ['id'], u'Результат', 50))
        self.addColumn(CMedicalCommissionActionsTableModel.CLocActionPropertiColumn(u'Группа',    ['id'], u'Группа инвалидности', 50))
        self.addColumn(CTextCol(   u'Примечания', ['note'],                                    6))
        self.setTable('Action')


    def data(self, index, role=Qt.DisplayRole):
        result = CActionsTableModel.data(self, index, role)
        if role == Qt.ToolTipRole:
            column = index.column()
            if column in [CMedicalSocialInspectionActionsTableModel.Col_Decision, CMedicalSocialInspectionActionsTableModel.Col_DisabilityGroup]:
                row = index.row()
                (col, values) = self.getRecordValues(column, row)
                return col.format(values)
        return result


class CExpertTempInvalidTableModel(CTableModel):
    class CLocClientColumn(CEventsTableModel.CLocClientColumn):
        def __init__(self, title, fields, defaultWidth, clientCache):
            CEventsTableModel.CLocClientColumn.__init__(self, title, fields, defaultWidth, clientCache)

    class CLocClientBirthDateColumn(CEventsTableModel.CLocClientBirthDateColumn):
        def __init__(self, title, fields, defaultWidth, clientCache):
            CEventsTableModel.CLocClientBirthDateColumn.__init__(self, title, fields, defaultWidth, clientCache)

    class CLocClientSexColumn(CEventsTableModel.CLocClientSexColumn):
        def __init__(self, title, fields, defaultWidth, clientCache):
            CEventsTableModel.CLocClientSexColumn.__init__(self, title, fields, defaultWidth, clientCache)

    class CPrevCol(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.recordCache = None

        def format(self, values):
            id = forceRef(values[0])
            record = self.recordCache.get(id) if self.recordCache and id else None
            if record:
                return QVariant(forceString(record.value('serial')) + ' ' + forceString(record.value('number')))
            return CCol.invalid

    class CLocCountVisitsColumn(CCol):
        def __init__(self, title, fields, defaultWidth, alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self._cache = {}

        def format(self, values):
            tempInvalidId = forceRef(values[0])
            result = self._cache.get(tempInvalidId, 0)
            db = QtGui.qApp.db
            stmt = u'''SELECT COUNT(Visit.id)
            FROM TempInvalid
            INNER JOIN Event ON TempInvalid.client_id = Event.client_id
            INNER JOIN Visit ON Visit.event_id = Event.id
            WHERE TempInvalid.id = %s AND Event.deleted = 0 AND Visit.deleted = 0 AND TempInvalid.deleted = 0
            AND DATE(Visit.date) >= TempInvalid.begDate AND DATE(Visit.date) <= TempInvalid.endDate'''%(tempInvalidId)
            query = db.query(stmt)
            if query.next():
                result = forceInt(query.value(0))
                self._cache[tempInvalidId] = result
            else:
                result = CCol.invalid
                self._cache[tempInvalidId] = result
            return result

        def invalidateRecordsCache(self):
            self._cache.clear()

        def updateRecordsCache(self, id):
            if id in self._cache.keys():
                self._cache.pop(id, None)

    Col_CountVisits = 12

    def __init__(self, parent, clientCache):
        CTableModel.__init__(self, parent)
        clientCol   = CExpertTempInvalidTableModel.CLocClientColumn( u'Ф.И.О.', ['client_id'], 60, clientCache)
        clientBirthDateCol = CExpertTempInvalidTableModel.CLocClientBirthDateColumn(u'Дата рожд.', ['client_id'], 20, clientCache)
        clientSexCol = CExpertTempInvalidTableModel.CLocClientSexColumn(u'Пол', ['client_id'], 5, clientCache)
        self.addColumn(clientCol)
        self.addColumn(clientBirthDateCol)
        self.addColumn(clientSexCol)
        self.addColumn(CBoolCol(u'СтСт',                                             ['insuranceOfficeMark'],                                                  6))
        self.addColumn(CRefBookCol(u'Причина нетрудоспособности',                    ['tempInvalidReason_id'], 'rbTempInvalidReason',                          15))
        self.addColumn(CDateCol(u'Дата начала ВУТ',                                  ['caseBegDate'],                                                          10))
        self.addColumn(CDateCol(u'Начало',                                           ['begDate'],                                                              12))
        self.addColumn(CDateCol(u'Окончание',                                        ['endDate'],                                                              12))
        self.addColumn(CRefBookCol(u'Врач',                                          ['person_id'],            'vrbPerson',                                    6))
        self.addColumn(CDesignationCol(u'МКБ',                                       ['diagnosis_id'],         ('Diagnosis', 'MKB'),                           6))
        self.addColumn(CEnumCol(u'Состояние',                                        ['state'],               CTempInvalidState.names,                         4))
        self.addColumn(CNumCol(u'Длительность',                                      ['duration'],                                                             10))
        self.addColumn(CExpertTempInvalidTableModel.CLocCountVisitsColumn(u'Визиты', ['id'],                                                                   10))
        self.addColumn(CRefBookCol(u'Тип',                                           ['doctype_id'],           'rbTempInvalidDocument',                        15))
        self.addColumn(CDateCol(u'В стационаре "с"',                                 ['begDateStationary'],                                                    12))
        self.addColumn(CDateCol(u'В стационаре "по"',                                ['endDateStationary'],                                                    12))
        self.addColumn(CRefBookCol(u'Нарушение режима',                              ['break_id'],             'rbTempInvalidBreak',                           15))
        self.addColumn(CDateCol(u'Дата нарушения режима',                            ['breakDate'],                                                            12))
        self.addColumn(CRefBookCol(u'Результат',                                     ['result_id'],            'rbTempInvalidResult',                          15))
        self.addColumn(CDateCol(u'Дата результата - Приступить к работе',            ['resultDate'],                                                           12))
        self.addColumn(CDateCol(u'Дата результата - Иное',                           ['resultOtherwiseDate'],                                                  12))
        self.addColumn(CTextCol(u'Номер путевки',                                    ['numberPermit'],                                                         12))
        self.addColumn(CDateCol(u'Дата начала путевки',                              ['begDatePermit'],                                                        12))
        self.addColumn(CDateCol(u'Дата окончания путевки',                           ['endDatePermit'],                                                        12))
        self.addColumn(CRefBookCol(u'Инвалидность',                                  ['disability_id'],        'rbTempInvalidRegime',                          15))
        self.setTable('TempInvalid')


    def updateColumnsCaches(self, id):
        self._cols[CExpertTempInvalidTableModel.Col_CountVisits].updateRecordsCache(id)


    def clearColumnsCaches(self):
        self._cols[CExpertTempInvalidTableModel.Col_CountVisits].invalidateRecordsCache()


class CExpertTempInvalidPeriodsTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CDateCol(   u'Дата открытия',    ['begDate'], 10))
        self.addColumn(CDateCol(   u'Дата закрытия',    ['endDate'], 10))
        self.addColumn(CRefBookCol(u'Закрыл',           ['endPerson_id'], 'vrbPerson', 6))
        self.addColumn(CRefBookCol(u'Председатель ВК',  ['chairPerson_id'],'vrbPerson', 6))
        self.addColumn(CBoolCol(   u'Внешний',          ['isExternal'], 10))
        self.addColumn(CRefBookCol(u'Режим',            ['regime_id'], 'rbTempInvalidRegime', 15))
        # self.addColumn(CRefBookCol(u'Результат периода',['result_id'], 'rbTempInvalidResult', 15))
        self.addColumn(CTextCol(   u'Примечания',       ['note'], 6))
        self.setTable('TempInvalid_Period')
        self.headerSortingCol = {}


class CExpertTempInvalidDuplicatesTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CBoolCol(u'СтСт',      ['insuranceOfficeMark'],                6))
        self.addColumn(CTextCol(u'Серия',     ['serial'],                             6))
        self.addColumn(CTextCol(u'Номер',     ['number'],                             6))
        self.addColumn(CDateCol(u'Дата',      ['date'],                              12))
        self.addColumn(CRefBookCol(u'Выдал',  ['person_id'], 'vrbPerson',             6))
        self.setTable('TempInvalidDuplicate')
        self.headerSortingCol = {}


class CExpertTempInvalidDocumentsTableModel(CTableModel):
    # class CLocClientCol(CDesignationCol):
    #     def __init__(self, title, fields, designationChain, defaultWidth, alignment='l'):
    #         CDesignationCol.__init__(self, title, fields, designationChain, defaultWidth, alignment)
    #
    #     def format(self, values):
    #         val = values[0]
    #         for cache in self._caches:
    #             recordId  = val.toInt()[0]
    #             if recordId:
    #                 record = cache.get(recordId)
    #                 if record:
    #                     birthDate = forceString(record.value('birthDate'))
    #                     sex = formatSex(record.value('sex'))
    #                     val = toVariant(formatName(forceString(record.value('lastName')),
    #                            forceString(record.value('firstName')),
    #                            forceString(record.value('patrName'))) + u', ' + birthDate + u', ' + sex)
    #                 else:
    #                     return QVariant()
    #             else:
    #                 return QVariant()
    #         return val

    class CLocParentClientCol(CDesignationCol):
        def __init__(self, title, fields, designationChain, defaultWidth, alignment='l'):
            CDesignationCol.__init__(self, title, fields, designationChain, defaultWidth, alignment)

        def format(self, values):
            val = values[0]
            tempInvalidId = val.toInt()[0]
            if tempInvalidId:
                tempInvalidRecord = self._caches[0].get(tempInvalidId)
                clientId = forceRef(tempInvalidRecord.value('client_id')) if tempInvalidRecord else None
                if clientId:
                    record = self._caches[1].get(clientId)
                    if record:
                        birthDate = forceString(record.value('birthDate'))
                        sex = formatSex(record.value('sex'))
                        return toVariant(formatName(forceString(record.value('lastName')),
                               forceString(record.value('firstName')),
                               forceString(record.value('patrName'))) + u', ' + birthDate + u', ' + sex)
            return QVariant()

    class CLocDocumentCol(CDesignationCol):
        def __init__(self, title, fields, designationChain, defaultWidth, alignment='l'):
            CDesignationCol.__init__(self, title, fields, designationChain, defaultWidth, alignment)

        def format(self, values):
            val = values[0]
            for cache in self._caches:
                recordId  = val.toInt()[0]
                if recordId:
                    record = cache.get(recordId)
                    if record:
                        issueDate = forceString(record.value('issueDate'))
                        val = toVariant(forceString(record.value('serial')) + u'-' + forceString(record.value('number')) + u', ' + forceString(record.value('placeWork')) + u', ' + issueDate)
                    else:
                        return QVariant()
                else:
                    return QVariant()
            return val

    class CLocExportFSSCol(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')

        def getExportFSS(self, documentId):
            exportFSS = u''
            if documentId:
                db = QtGui.qApp.db
                tableTempInvalidDocument = db.table('TempInvalidDocument')
                tableDocumentExport = db.table('TempInvalidDocument_Export')
                tableExternalSystem = db.table('rbExternalSystem')
                queryTable = tableTempInvalidDocument.innerJoin(tableDocumentExport, tableDocumentExport['master_id'].eq(tableTempInvalidDocument['id']))
                queryTable = queryTable.innerJoin(tableExternalSystem, tableExternalSystem['id'].eq(tableDocumentExport['system_id']))
                if documentId:
                    cond = [tableDocumentExport['master_id'].eq(documentId),
                            tableExternalSystem['code'].eq(u'СФР'),
                            tableTempInvalidDocument['deleted'].eq(0)
                            ]
                    record = db.getRecordEx(queryTable, [tableDocumentExport['note']], cond, order = u'TempInvalidDocument_Export.id DESC')
                    exportFSS = forceStringEx(record.value('note')) if record else u''
            return exportFSS

        def format(self, values):
            documentId = forceRef(values[0])
            if documentId:
                return toVariant(self.getExportFSS(documentId))
            return CCol.invalid

    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CExpertTempInvalidDocumentsTableModel.CLocParentClientCol(u'ФИО', ['master_id'], [('TempInvalid', 'id, client_id'), ('Client', 'id, birthDate, lastName, firstName, patrName, birthDate, sex')], 30))
        self.addColumn(CDateCol(       u'Дата выдачи',                         ['issueDate'],                                                                          12))
        self.addColumn(CTextCol(       u'Серия',                               ['serial'],                                                                              6))
        self.addColumn(CTextCol(       u'Номер',                               ['number'],                                                                              6))
        self.addColumn(CBoolCol(       u'Д',                                   ['duplicate'],                                                                           3).setToolTip(u'Дубликат'))
        self.addColumn(CRefBookCol(    u'Причина выдачи дубликата',            ['duplicateReason_id'], 'rbTempInvalidDuplicateReason',                                 10))
        self.addColumn(CBoolCol(       u'Э',                                   ['electronic'],                                                                          3).setToolTip(u'Электронный'))
        self.addColumn(CEnumCol(       u'Занятость',                           ['busyness'],        [u'', u'основное', u'совместитель', u'на учете'],                  10))
        self.addColumn(CTextCol(       u'Место работы',                        ['placeWork'],                                                                          20))
        self.addColumn(CTextCol(       u'ПДН',                                 ['prevNumber'],                                                                         12).setToolTip(u'Продолжение документа с номером'))
        self.addColumn(CExpertTempInvalidDocumentsTableModel.CLocDocumentCol(u'ИПД',   ['prev_id'], ('TempInvalidDocument', 'serial, number, placeWork, issueDate'),   20).setToolTip(u'Идентификатор продолжения документа'))
        self.addColumn(CRefBookCol(    u'Выдал',                               ['person_id'],       'vrbPersonWithSpeciality',                                         20))
        self.addColumn(CRefBookCol(    u'Закрыл',                              ['execPerson_id'],   'vrbPersonWithSpeciality',                                         20))
        self.addColumn(CRefBookCol(    u'Председатель ВК',                     ['chairPerson_id'],  'vrbPersonWithSpeciality',                                         20))
        # self.addColumn(CExpertTempInvalidDocumentsTableModel.CLocClientCol(u'Пациент 1', ['clientPrimum_id'], ('Client', 'id, birthDate, lastName, firstName, patrName, birthDate, sex'), 30))
        # self.addColumn(CExpertTempInvalidDocumentsTableModel.CLocClientCol(u'Пациент 2', ['clientSecond_id'], ('Client', 'id, birthDate, lastName, firstName, patrName, birthDate, sex'), 30))
        self.addColumn(CExpertTempInvalidDocumentsTableModel.CLocDocumentCol(u'ИВД',     ['last_id'], ('TempInvalidDocument', 'serial, number, placeWork, issueDate'), 20).setToolTip(u'Идентификатор выданного документа'))
        self.addColumn(CTextCol(       u'Примечание',                          ['note'],                                                                               20))
        self.addColumn(CBoolCol(       u'Внешний',                             ['isExternal'],                                                                         10))
        self.addColumn(CExpertTempInvalidDocumentsTableModel.CLocExportFSSCol(u'Статус передачи в СФР', ['id'], 20))
        self.setTable('TempInvalidDocument')


    def getCurrentTempInvalidId(self, tempInvalidDocumentId):
        if tempInvalidDocumentId:
            db = QtGui.qApp.db
            table = db.table('TempInvalidDocument')
            record = db.getRecordEx(table, [table['master_id']], [table['id'].eq(tempInvalidDocumentId), table['deleted'].eq(0)], table['issueDate'].name())
            return forceRef(record.value('master_id')) if record else None
        return None
    
    
    def sort(self, col, sortOrder=Qt.AscendingOrder):
        if self._idList:
            db = QtGui.qApp.db
            table = db.table('TempInvalidDocument')
            cond = [table['id'].inlist(self._idList)]
            colClass = self.cols()[col]
            colName = colClass.fields()[0]
            order = '{} {}'.format(colName, u'DESC' if sortOrder else u'ASC')
            if col in [5,11,12,13]:
                tableSort = db.table(colClass.tableName).alias('fieldSort')
                table = table.leftJoin(tableSort, tableSort['id'].eq(table[colName]))
                order = 'fieldSort.name {}'.format(u'DESC' if sortOrder else u'ASC')
            elif col in [0]:
                tableSort = db.table('TempInvalid').alias('fieldSort')
                tableClient = db.table('Client').alias('fieldSort2')
                table = table.leftJoin(tableSort, tableSort['id'].eq(table['master_id']))
                table = table.leftJoin(tableClient, tableClient['id'].eq(tableSort['client_id']))
                order = 'lastName {}, firstName, patrName, birthDate, fieldSort2.sex'.format(u'DESC' if sortOrder else u'ASC')
            elif col in [10, 14]:
                tableSort = db.table('TempInvalidDocument').alias('fieldSort')
                table = table.leftJoin(tableSort, tableSort['id'].eq(table['last_id' if col == 14 else 'prev_id']))
                order = 'fieldSort.serial {}, fieldSort.number, fieldSort.placeWork, fieldSort.issueDate'.format(u'DESC' if sortOrder else u'ASC')
            self._idList = db.getIdList(table, table['id'].name() , where = cond, order=order)
            self.reset()


class CVisitsTableModel(CTableModel):
    class CLocClientColumn(CEventsTableModel.CLocClientColumn):
        def __init__(self, title, fields, defaultWidth, clientCache, eventCache):
            CEventsTableModel.CLocClientColumn.__init__(self, title, fields, defaultWidth, clientCache)
            self.eventCache = eventCache


        def format(self, values):
            val = values[0]
            eventId  = forceRef(val)
            eventRecord = self.eventCache.get(eventId)
            if eventRecord:
                clientValues = [eventRecord.value('client_id')]
                clientVal = clientValues[0]
                clientId  = forceRef(clientVal)
                clientRecord = self.clientCache.get(clientId)
                if clientRecord:
                    name  = formatShortNameInt(forceString(clientRecord.value('lastName')),
                                       forceString(clientRecord.value('firstName')),
                                       forceString(clientRecord.value('patrName')))
                    return toVariant(name)
                return CCol.invalid
            return CCol.invalid


    class CLocClientIdentifierColumn(CCol):
        def __init__(self, title, fields, defaultWidth, eventCache):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.eventCache = eventCache
            self.identifiersCache = CRecordCache()


        def getClientIdentifier(self, clientId):
            identifier = self.identifiersCache.get(clientId)
            if identifier is None:
                accountingSystemId = QtGui.qApp.defaultAccountingSystemId()
                if accountingSystemId is None:
                    identifier = clientId
                else:
                    db = QtGui.qApp.db
                    tableClientIdentification = db.table('ClientIdentification')
                    cond = [tableClientIdentification['client_id'].eq(clientId),
                            tableClientIdentification['accountingSystem_id'].eq(accountingSystemId)]
                    record = db.getRecordEx(tableClientIdentification, tableClientIdentification['identifier'], cond)
                    identifier = forceString(record.value(0)) if record else ''
                self.identifiersCache.put(clientId, identifier)
            return identifier


        def format(self, values):
            val = values[0]
            eventId = forceRef(val)
            eventRecord = self.eventCache.get(eventId)
            if eventRecord:
                clientId = forceRef(eventRecord.value('client_id'))
                return toVariant(self.getClientIdentifier(clientId))
            return CCol.invalid


    class CLocClientBirthDateColumn(CEventsTableModel.CLocClientBirthDateColumn):
        def __init__(self, title, fields, defaultWidth, clientCache, eventCache):
            CEventsTableModel.CLocClientBirthDateColumn.__init__(self, title, fields, defaultWidth, clientCache)
            self.eventCache = eventCache

        def format(self, values):
            val = values[0]
            eventId  = forceRef(val)
            eventRecord = self.eventCache.get(eventId)
            if eventRecord:
                return CEventsTableModel.CLocClientBirthDateColumn.format(self, [eventRecord.value('client_id')])
            return CCol.invalid


    class CLocClientSexColumn(CEventsTableModel.CLocClientSexColumn):
        def __init__(self, title, fields, defaultWidth, clientCache, eventCache):
            CEventsTableModel.CLocClientSexColumn.__init__(self, title, fields, defaultWidth, clientCache)
            self.eventCache = eventCache

        def format(self, values):
            val = values[0]
            eventId  = forceRef(val)
            eventRecord = self.eventCache.get(eventId)
            if eventRecord:
                return CEventsTableModel.CLocClientSexColumn.format(self, [eventRecord.value('client_id')])
            return CCol.invalid

    class  CExternalIdColumn(CTextCol):
        def __init__(self, title, fields, defaultWidth):
            CTextCol.__init__(self, title, fields, defaultWidth)
            self._cache = {}

        def format(self, values):
            eventId = forceRef(values[0])
            result = self._cache.get(eventId, u'')
            if not result:
                db = QtGui.qApp.db
                externalId = db.translate('Event', 'id', eventId, 'externalId')
                result = forceString(externalId)
                self._cache[eventId] = result
            return result

    class  CFinanceIdColumn(CTextCol):
        def __init__(self, title, fields, defaultWidth):
            CTextCol.__init__(self, title, fields, defaultWidth)
            self._cache = {}

        def format(self, values):
            financeId = forceRef(values[0])
            result = self._cache.get(financeId, u'')
            if not result:
                db = QtGui.qApp.db
                financeName = db.translate('rbFinance', 'id', financeId, 'name')
                result = forceString(financeName)
                self._cache[financeId] = result
            return result


    def __init__(self, parent, clientCache, eventCache):
        CTableModel.__init__(self, parent)
        clientCol   = CVisitsTableModel.CLocClientColumn( u'Ф.И.О.', ['event_id'], 60, clientCache, eventCache)
#        clientIdentifierCol = CVisitsTableModel.CLocClientIdentifierColumn(u'Идентификатор', ['event_id'], 30, eventCache)
        clientBirthDateCol = CVisitsTableModel.CLocClientBirthDateColumn(u'Дата рожд.', ['event_id'], 20, clientCache, eventCache)
        clientSexCol = CVisitsTableModel.CLocClientSexColumn(u'Пол', ['event_id'], 5, clientCache, eventCache)
        self.addColumn(clientCol)
        self.addColumn(clientBirthDateCol)
        self.addColumn(clientSexCol)
        self.addColumn(CDateCol(u'Дата',                 ['date'],                                    15))
        self.addColumn(CRefBookCol(u'Тип',               ['visitType_id'], 'rbVisitType',             15))
        self.addColumn(CRefBookCol(u'Исполнитель',       ['person_id'],    'vrbPersonWithSpecialityAndOrgStr', 20))
        self.addColumn(CRefBookCol(u'Место',             ['scene_id'],     'rbScene',                 15))
        self.addColumn(CBoolCol(u'Признак первичности',  ['isPrimary'],                               15))
        self.addColumn(CRefBookCol(u'Услуга',            ['service_id'],   'rbService',               15))
        self.addColumn(CBoolCol(u'Флаги финансирования', ['payStatus'],                               15))
        self.addColumn(CRefBookCol(u'Ассистент',         ['assistant_id'], 'vrbPersonWithSpecialityAndOrgStr', 20))
        self.addColumn(CDesignationCol(u'Номер документа', ['event_id'],   ('Event', 'externalId'), 20))
        self.addColumn(CRefBookCol(u'Тип финансирования', ['finance_id'],   'rbFinance',               10))

        self.loadField('id')
        self.loadField('event_id')
        self.setTable('Visit')
        self.headerSortingCol = {}


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        return CTableModel.headerData(self, section, orientation, role)


class CSchedulesTableView(CTableView):
    def __init__(self, parent):
        CTableView.__init__(self, parent)
        self._order = None
        self._orderColumn = None
        self._isDesc = True


    def getOrder(self, column):
        return self.model().getOrder(self.model().cols()[column].fieldName(), column)


    def itemId(self, index):
        if index.isValid():
            row = index.row()
            itemIdList = self.model().itemIdList()
            if 0 <= row < len(itemIdList):
                return itemIdList[row]
        return None


    def itemIdList(self):
        idList = []
        items = self.model().items()
        if items is not None:
            for item in items:
                idList.append(forceRef(item.value('id')))
        return idList

