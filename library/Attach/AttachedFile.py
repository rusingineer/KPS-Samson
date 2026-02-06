# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2016-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Описание присоединённого файла, который хранится где-то
## и модель списка таких файлов.
##
#############################################################################

import posixpath
import locale
import zlib

from PyQt4 import QtGui
from PyQt4.QtCore import (
    Qt,
    SIGNAL,
    QAbstractTableModel,
    QByteArray,
    QDateTime,
    QModelIndex,
    QVariant,
    pyqtSignal,
)

from library.Utils import forceDateTime, forceRef, forceString, forceInt, toVariant
from library.CertComboBox import extractCertInfo
from library.MSCAPI       import MSCApi
from library.naturalSort import convertKeyForNaturalSort
from library.database    import CTableRecordCache, CSqlRecord


class CAttachedFileSignature:
    u"""Описание подписи присоединённого файла"""
    def __init__(self, signatureBytes=None, signerId=None, signingDatetime=None):
        self.signatureBytes  = signatureBytes   # отсоединённая подпись присоединённого файла
        self.signerId        = signerId         # id врача
        self.signingDatetime = signingDatetime  # дата и время подписи

        self.certName = None
        self.certHtml = None
        self.certCustom = None

        if self.signatureBytes:
            try:
                api = MSCApi(QtGui.qApp.getCsp())
            except:
#                QtGui.qApp.logCurrentException()
                self.certName = self.certHtml = u'ОШИБКА: Криптопровайдер не настроен'
                return

            try:
                with api.signatureAsStore(signatureBytes) as store:
                    for cert in store.listCerts():
                        with cert:
                            _, self.certName, self.certHtml = extractCertInfo(cert)
                            self.certCustom = cert
                            break
            except Exception:
                QtGui.qApp.logCurrentException()
                self.certName = self.certHtml = u'ОШИБКА: смотри журнал'


class CAttachedFileSignatureFull:
    u"""Полное описание подписи присоединённого файла (включая несохраненные подписи)"""
    def __init__(self, signId=None, signatureBytes=None, signerId=None, signingDatetime=None,
                                                            signerTitle=None, masterId=None):
        self.signId = signId
        self.signatureBytes  = signatureBytes   # отсоединённая подпись присоединённого файла
        self.signerId        = signerId         # id врача
        self.signingDatetime = signingDatetime  # дата и время подписи
        self.signerTitle = signerTitle
        self.masterId = masterId


class CAttachedFile:
    u"""Описание присоединённого файла, который хранится где-то (в WebDAV)"""
    def __init__(self):
        self._record       = None
        self.id            = None
        self.persistentDir = None
        self.tmpDir        = None
        self.oldName       = None
        self.newName       = None
        self.comment       = None

        self.size          = None
        self.lastModified  = None
        self.authorId      = None
        self.respSigner_name = None
        self.templateId = None
#        self.author        = None

        self.respSignature = None
        self.orgSignature  = None
        self.additionalSignatures = None
        self.additionalSignaturesList = None  # Используется, в том числе для хранения не сохраненных в БД подписей
        self.htmlTemplate = None

        self.isLost        = False


    def _setRemoteFile(self, filePath, size, lastModified):
        self.persistentDir, self.oldName = posixpath.split(filePath)
        self.size = size
        self.lastModified = lastModified
        self.newName = self.oldName
        self.tmpDir  = None


    def _setLostFile(self, filePath):
        self.persistentDir, self.oldName = posixpath.split(filePath)
        self.newName = self.oldName
        self.tmpDir = None
        self.isLost = True


    def _setTmpFile(self, filePath, size, lastModified):
        self.tmpDir, self.oldName = posixpath.split(filePath)
        self.size = size
        self.lastModified = lastModified
        self.newName = self.oldName
        self.persistentDir = None
        self.isLost = False


    def setRecord(self, record, tableName='Action_FileAttach'):
        self._record = record
        self.id = forceRef(record.value('id'))
        self.comment = forceString(record.value('comment'))
        self.authorId = forceRef(record.value('createPerson_id'))
        self.setRespSignature(record.value('respSignatureBytes').toByteArray().data(),
                              forceRef(record.value('respSigner_id')),
                              forceDateTime(record.value('respSigningDatetime')))
        self.setOrgSignature(record.value('orgSignatureBytes').toByteArray().data(),
                             forceRef(record.value('orgSigner_id')),
                             forceDateTime(record.value('orgSigningDatetime')))
        self.respSigner_name = forceString(record.value('respSigner_name'))
        self.loadAdditionalSignatures(self.id)
        self.loadHtmlTemplate(self.id, tableName)
        if not self.htmlTemplate:
            html = forceString(record.value('html'))
            self.htmlTemplate = html if html else None


    def getRecord(self, table=None):
        if self._record:
            record = self._record
        else:
            if not table:
                record = CSqlRecord()
                record._dirty = True
                return record
            record = table.newRecord()
            record.setValue('deleted', 0)
        record.setValue('path', self.getPath())
        record.setValue('comment', self.comment)
        if self.respSignature and self.respSignature.signatureBytes:
            record.setValue('respSignatureBytes', QByteArray(self.respSignature.signatureBytes))
            record.setValue('respSigner_id',      self.respSignature.signerId)
            record.setValue('respSigningDatetime', self.respSignature.signingDatetime)
            if self.respSignature.certCustom:
                record.setValue('respSigner_name', u'{0} {1} {2}'.format(forceString(self.respSignature.certCustom.surName()),
                                                                         forceString(self.respSignature.certCustom.givenName()),
                                                                         forceString(self.respSignature.certCustom.snils())))
            else:
                record.setValue('respSigner_name', None)
        if self.orgSignature and self.orgSignature.signatureBytes:
            record.setValue('orgSignatureBytes', QByteArray(self.orgSignature.signatureBytes))
            record.setValue('orgSigner_id',      self.orgSignature.signerId)
            record.setValue('orgSigningDatetime', self.orgSignature.signingDatetime)
        return record


    def loadAdditionalSignatures(self, masterId):
        db = QtGui.qApp.db
        table = db.table('Action_FileAttach_Signature')
        cond = db.joinAnd([table['deleted'].eq(0), table['master_id'].eq(masterId)])
        records = db.getRecordList(table, '*', cond)
        self.additionalSignatures = []
        self.additionalSignaturesList = []

        for record in records:
            signId = forceInt(record.value('id'))
            signBytes = record.value('signatureBytes').toByteArray().data()
            signerId = forceRef(record.value('signer_id'))
            signDatetime = forceDateTime(record.value('signingDatetime'))
            signerTitle = forceString(record.value('signerTitle'))
            self.additionalSignaturesList.append(CAttachedFileSignatureFull(signId=signId,
                                                                            signatureBytes=signBytes,
                                                                            signerId=signerId,
                                                                            signingDatetime=signDatetime,
                                                                            signerTitle=signerTitle,
                                                                            masterId=masterId
                                                                            ))
            self.additionalSignatures.append(CAttachedFileSignature(signatureBytes=signBytes,
                                                                    signerId=signerId,
                                                                    signingDatetime=signDatetime
                                                                    ))


    def loadHtmlTemplate(self, masterId, tableName='Action_FileAttach'):
        db = QtGui.qApp.db
        table = db.table(tableName + '_PrintTemplate')
        record = db.getRecord(table, '*', masterId)
        if record:
            html = record.value('html').toByteArray()
            self.templateId = forceRef(record.value('template_id'))
            try:
                if html:
                    decompressor = zlib.decompressobj(zlib.MAX_WBITS | 32)
                    decompressedData = decompressor.decompress(html)
                    decompressedData += decompressor.flush()
                    self.htmlTemplate = decompressedData.decode('utf8')
            except Exception:
                QtGui.qApp.logCurrentException()


    def addSignature(self, signId=None, signBytes=None, signerId=None, signDatetime=None,
                                                                signerTitle=None, masterId=None):
        self.additionalSignaturesList.append(CAttachedFileSignatureFull(signId=signId,
                                                                        signatureBytes=signBytes,
                                                                        signerId=signerId,
                                                                        signingDatetime=signDatetime,
                                                                        signerTitle=signerTitle,
                                                                        masterId=masterId
                                                                        ))
        self.additionalSignatures.append(CAttachedFileSignature(signatureBytes=signBytes,
                                                                signerId=signerId,
                                                                signingDatetime=signDatetime
                                                                ))


    def setAuthorId(self, authorId):
        self.authorId = authorId


    def setHtmlTemplate(self, html):
        self.htmlTemplate = html


    def setRespSignature(self, signatureBytes, singerId, signingDateTime):
        if signatureBytes:
            self.respSignature = CAttachedFileSignature(signatureBytes, singerId, signingDateTime)
        else:
            self.respSignature = None


    def hasRespSignature(self):
        s = self.respSignature
        return s and s.signatureBytes and s.signerId and s.signingDatetime


    def setOrgSignature(self, signatureBytes, singerId, signingDateTime):
        if signatureBytes:
            self.orgSignature = CAttachedFileSignature(signatureBytes, singerId, signingDateTime)
        else:
            self.orgSignature = None


    def hasOrgSignature(self):
        s = self.orgSignature
        return s and s.signatureBytes and s.signerId and s.signingDatetime


    def getRespSignerId(self):
        if self.respSignature and self.respSignature.signatureBytes:
            return self.respSignature.signerId
        return None


    def getRespSignerToolTip(self):
        if self.respSignature and self.respSignature.certHtml:
            return self.respSignature.certHtml
        return None


    def getOrgSignerId(self):
        if self.orgSignature and self.orgSignature.signatureBytes:
            return self.orgSignature.signerId
        return None


    def getOrgSignerToolTip(self):
        if self.orgSignature and self.orgSignature.certHtml:
            return self.orgSignature.certHtml
        return None


    @classmethod
    def remoteFile(cls, path, size, lastModified):
        result = cls()
        result._setRemoteFile(path, size, lastModified)
        return result


    @classmethod
    def lostFile(cls, path):
        result = cls()
        result._setLostFile(path)
        return result


    @classmethod
    def tmpFile(cls, path, size, lastModified):
        result = cls()
        result._setTmpFile(path, size, lastModified)
        result.setAuthorId(QtGui.qApp.userId)
        return result


    def rename(self, newName):
        self.newName = newName
        if self._record:
            self._record._dirty = True
            self._record.changed = True


    def edtComment(self, comment):
        self.comment = comment
        if self._record:
            self._record._dirty = True
            self._record.changed = True


    def getPath(self):
        return posixpath.join(self.persistentDir if self.persistentDir else self.tmpDir,
                              self.oldName
                             )


class CAttachedFilesLoader:

    @staticmethod
    def itemsPresent(interface, tableName, masterId):
        if interface:
            db = QtGui.qApp.db
            table = db.table(tableName)
            cond = db.joinAnd([table['deleted'].eq(0), table['master_id'].eq(masterId)])
            return db.getCount(table, countCol='1', where=cond)
        else:
            return 0


    @staticmethod
    def loadItems(interface, tableName, masterId):
        if interface:
            db = QtGui.qApp.db
            table = db.table(tableName)
            cond = db.joinAnd([table['deleted'].eq(0), table['master_id'].eq(masterId)])
            records = db.getRecordList(table, '*', cond)
            result = []
            for record in records:
                path = forceString(record.value('path'))
                item = interface.createAttachedFileItem(path)
                item.setRecord(record, tableName)
                result.append(item)
            return result
        else:
            return []

    @staticmethod
    def loadItemsWithOrder(interface, tableName, masterId, order):
        if interface:
            db = QtGui.qApp.db
            table = db.table(tableName)
            cond = db.joinAnd([table['deleted'].eq(0), table['master_id'].eq(masterId)])
            records = db.getRecordList(table, '*', cond, order)
            result = []
            for record in records:
                path = forceString(record.value('path'))
                item = interface.createAttachedFileItem(path)
                item.setRecord(record)
                result.append(item)
            return result
        else:
            return []

    @staticmethod
    def loadItemsFromRecords(interface, records):
        if interface:
            result = []
            for record in records:
                path = forceString(record.value('path'))
                item = interface.createAttachedFileItem(path)
                item.setRecord(record)
                result.append(item)
            return result
        else:
            return []

    @staticmethod
    def loadAllItems(interface, clientId, filterFiles):
        records = []
        result = []
        recordMap = {}
        if interface and clientId:
            db = QtGui.qApp.db
            cols = ['master_id', 'comment', 'path', 'createPerson_id', 'respSignatureBytes', 'respSigner_id',
                    'respSigningDatetime', 'orgSignatureBytes', 'orgSigner_id', 'orgSigningDatetime', 'id']
            tableCFA = db.table('Client_FileAttach')
            cond = [
                tableCFA['deleted'].eq(0),
                tableCFA['master_id'].eq(clientId),
            ]
            colsCfa = list(cols)
            colsCfa.append(u'\'Client\' as objectTableName')
            if filterFiles['docTableName'] in (u'All', u'Client'):
                cond.extend(getFilterCond(filterFiles, tableCFA))
                records.extend(db.getRecordList(tableCFA, colsCfa, cond))
            tableA = db.table('Action')
            tableAFA = db.table('Action_FileAttach')
            tableAFAE = db.table('Action_FileAttach_Export')
            tableAT = db.table('ActionType')
            tableE = db.table('Event')
            table = tableAFA.leftJoin(tableAFAE, tableAFA['id'].eq(tableAFAE['master_id']))
            table = table.leftJoin(tableA, tableA['id'].eq(tableAFA['master_id']))
            table = table.leftJoin(tableAT, tableAT['id'].eq(tableA['actionType_id']))
            table = table.leftJoin(tableE, tableE['id'].eq(tableA['event_id']))
            colsAfa = u', '.join([u', '.join(['Action_FileAttach.%s' % col for col in cols]),
                                  tableAFAE['success'].name(),
                                  u'\'Action\' as objectTableName'])
            cond = [
                tableE['client_id'].eq(clientId),
                tableA['deleted'].eq(0),
                tableAFA['deleted'].eq(0),
            ]
            if filterFiles['docTableName'] in (u'All', u'Action'):
                actionTypeClass = filterFiles.get('actionTypeClass', None)
                if actionTypeClass or actionTypeClass == 0:
                    cond.append(tableAT['class'].eq(filterFiles.get('actionTypeClass')))
                if filterFiles.get('actionTypeGroup', None):
                    cond.append(tableAT['group_id'].eq(filterFiles.get('actionTypeGroup')))
                if filterFiles.get('actionType', None):
                    cond.append(tableA['actionType_id'].eq(filterFiles.get('actionType')))
                serviceType = filterFiles.get('serviceType', None)
                if serviceType or serviceType == 0:
                    cond.append(tableAT['serviceType'].eq(filterFiles.get('serviceType')))
                cond.extend(getFilterCond(filterFiles, table, extTable=tableA))
                records.extend(db.getRecordList(table, colsAfa, cond))
            tableEFA = db.table('Event_FileAttach')
            tableEFAExport = db.table('Event_FileAttach_Export')
            table = tableEFA.leftJoin(tableEFAExport, tableEFA['id'].eq(tableEFAExport['master_id']))
            table = table.leftJoin(tableE, tableE['id'].eq(tableEFA['master_id']))
            colsEfa = u', '.join([u', '.join(['Event_FileAttach.%s' % col for col in cols]),
                                  tableEFAExport['success'].name(),
                                  u'\'Event\' as objectTableName'])
            cond = [
                tableE['client_id'].eq(clientId),
                tableE['deleted'].eq(0),
                tableEFA['deleted'].eq(0),
            ]
            if filterFiles['docTableName'] in (u'All', u'Event'):
                if filterFiles.get('eventId', None):
                    cond.append(tableE['id'].eq(filterFiles.get('eventId')))
                if filterFiles.get('eventType', None):
                    cond.append(tableE['eventType_id'].eq(filterFiles.get('eventType')))
                if filterFiles.get('externalId', None):
                    cond.append(tableE['externalId'].eq(filterFiles.get('externalId')))
                cond.extend(getFilterCond(filterFiles, table, extTable=tableE))
                records.extend(db.getRecordList(table, colsEfa, cond))
            tablePP = db.table('ProphylaxisPlanning')
            tablePPFA = db.table('ProphylaxisPlanning_FileAttach')
            colsPpfa = u', '.join([u', '.join(['ProphylaxisPlanning_FileAttach.%s' % col for col in cols]),
                                   u'\'ProphylaxisPlanning\' as objectTableName'])
            table = tablePPFA.join(tablePP, tablePP['id'].eq(tablePPFA['master_id']))
            cond = [
                tablePP['client_id'].eq(clientId),
                tablePP['deleted'].eq(0),
                tablePPFA['deleted'].eq(0),
            ]
            if filterFiles['docTableName'] in (u'All', u'ProphylaxisPlanning'):
                cond.extend(getFilterCond(filterFiles, table))
                records.extend(db.getRecordList(table, colsPpfa, cond))

        for record in records:
            path = forceString(record.value('path'))
            recordMap[path] = record
        for path in recordMap:
            item = interface.createAttachedFileItem(path)
            item.setRecord(recordMap[path])
            result.append(item)
        return result

    @staticmethod
    def saveItems(interface, tableName, masterId, items, saveOnlyChanged=False):
        if interface:
            interface.saveFiles(items)
            idSet = set([item.id for item in items if item.id])
            db = QtGui.qApp.db
            table = db.table(tableName)
            cond = db.joinAnd([table['deleted'].eq(0),
                               table['master_id'].eq(masterId),
                               table['id'].notInlist(idSet)
                               ])
            db.deleteRecord(table, cond)
            for item in items:
                record = item.getRecord(table)
                record.setValue('master_id', masterId)
                if item.id and saveOnlyChanged:
                    if hasattr(record, 'changed') and record.changed:
                        pass
                    else:
                        continue
                _id = db.insertOrUpdate(table, record)
                item.id = _id
                CAttachedFilesLoader.saveAdditionalSign(item)
                CAttachedFilesLoader.savePrintTemplate(item, tableName)
                item.setRecord(record)

    @staticmethod
    def saveAdditionalSign(item):
        db = QtGui.qApp.db
        tableAFAS = db.table('Action_FileAttach_Signature')
        signList = item.additionalSignaturesList
        if signList:
            for sign in signList:
                if not sign.signId:
                    signatureBytes = sign.signatureBytes
                    signerId = sign.signerId
                    signingDatetime = sign.signingDatetime
                    signerTitle = sign.signerTitle
                    masterId = item.id
                    record = tableAFAS.newRecord()
                    record.setValue('createDatetime', toVariant(QDateTime().currentDateTime()))
                    record.setValue('createPerson_id', QtGui.qApp.userId)
                    record.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
                    record.setValue('modifyPerson_id', QtGui.qApp.userId)
                    record.setValue('master_id', masterId)
                    record.setValue('signatureBytes', QByteArray(signatureBytes))
                    record.setValue('signer_id', signerId)
                    record.setValue('signingDatetime', signingDatetime)
                    record.setValue('signerTitle', toVariant(signerTitle))
                    db.insertOrUpdate(tableAFAS, record)


    @staticmethod
    def savePrintTemplate(item, tableName='Action_FileAttach'):
        if item.htmlTemplate or item.templateId:
            db = QtGui.qApp.db
            table = db.table(tableName + '_PrintTemplate')
            record = db.getRecord(table, '*', item.id)
            if not record:
                record = table.newRecord()
                if item.htmlTemplate:
                    value = item.htmlTemplate.encode('utf8')
                    compData = zlib.compress(value)
                    record.setValue('html', QByteArray(compData))
                record.setValue('id', item.id)
                record.setValue('template_id', item.templateId)
                db.insertRecord(table, record)


class CAttachedFilesModel(QAbstractTableModel):
    u"""Список прикреплённых файлов"""
    changed = pyqtSignal()

    def __init__(self, parent):
        QAbstractTableModel.__init__(self)
        self.interface = None
        self.tableName = None
        self.items = []
        self.personsCache = CTableRecordCache(QtGui.qApp.db, 'vrbPersonWithSpeciality', '*')


    def setInterface(self, interface):
        self.interface = interface


    def setTable(self, tableName):
        self.tableName = tableName


    def loadItems(self, masterId):
        self.items = CAttachedFilesLoader.loadItems(self.interface, self.tableName, masterId)
        self.reset()


    def saveItems(self, masterId, saveOnlyChanged=False):
        CAttachedFilesLoader.saveItems(self.interface, self.tableName, masterId, self.items, saveOnlyChanged=saveOnlyChanged)


    def columnCount(self, index=None):
        return 9


    def rowCount(self, index=None):
        return len(self.items)


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant((u'ID', u'Имя файла', u'Комментарий', u'Размер', u'Дата', u'Автор', u'Владелец подписи', u'Подпись отв.лица', u'Подпись организации')[section])
        return QVariant()


#    def flags(self, index):
#        row = index.row()
#        item = self.items[row]
#        if item.isLost:
#            return Qt.ItemIsSelectable
#        else:
#            return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def _getPersonName(self, personId):
        return self.personsCache.get(personId).value('name') if personId else None

    def _getPersonNameWithSnils(self, item):
        return u'{0} {1}, СНИЛС {2}'.format(forceString(item.respSignature.certCustom.surName()),
                                            forceString(item.respSignature.certCustom.givenName()),
                                            forceString(item.respSignature.certCustom.snils())) if item.respSignature else None

    def _getAddSignatures(self, currentItem):
        result = u''
        if currentItem:
            res = []
            result = ''
            additionalSignatures = currentItem.additionalSignaturesList
            if additionalSignatures:
                for sign in additionalSignatures:
                    if forceString(sign.signerTitle):
                        titleList = forceString(sign.signerTitle).split(',')[0].split(' ')
                        fullLastName = titleList[0] if titleList else ''
                        cutFirstName = u' %s.' % titleList[1][:1] if len(titleList) >= 2 else ''
                        cutPatrName = u' %s.' % titleList[2][:1] if len(titleList) == 3 else ''
                        temp = u'{0}{1}{2}'.format(fullLastName, cutFirstName, cutPatrName)
                    else:
                        temp = u'----'
                    if sign.signId:
                        res.append(u'{1} {0} <b>ЭЦП</b> {2} <br>'.format(
                            forceString(self._getPersonName(sign.signerId)),
                            forceString(sign.signingDatetime), temp))
                    else:
                        res.append(u'{1} {0} <b>ЭЦП</b> {2} - ПОДПИСЬ НЕ СОХРАНЕНА<br>'.format(
                            forceString(self._getPersonName(sign.signerId)),
                            forceString(sign.signingDatetime), temp))
                result = '\n'.join(res)
        return result


    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            row = index.row()
            column = index.column()
            item = self.items[row]
            if column == 0:
                return QVariant(item.id)
            if column == 1:
                return QVariant(item.newName)
            if column == 2:
                return QVariant(item.comment)
            elif column == 3:
                return QVariant(item.size)
            elif column == 4:
                return QVariant(item.lastModified)
            elif column == 5:
                return QVariant(self._getPersonName(item.authorId))
            elif column == 6:
                if item.respSignature and item.respSignature.certCustom:
                    respSigner_name = u'{0} {1}, СНИЛС {2}'.format(forceString(item.respSignature.certCustom.surName()),
                                                                   forceString(item.respSignature.certCustom.givenName()),
                                                                   forceString(item.respSignature.certCustom.snils())) if item.respSignature else None
                else:
                    respSigner_name = None
                return QVariant(item.respSigner_name if item.respSigner_name else respSigner_name)
            elif column == 7:
                return self._getPersonName(item.getRespSignerId())
            elif column == 8:
                return self._getPersonName(item.getOrgSignerId())
            # elif column == 7:
            #     return QVariant(self._getAddSignatures(item.additionalSignatures))
            return QVariant()

        elif role == Qt.TextAlignmentRole:
            column = index.column()
            if column == 1:
                return QVariant(Qt.AlignLeft | Qt.AlignVCenter)
            elif column == 3:
                return QVariant(Qt.AlignRight | Qt.AlignVCenter)
            elif column == 4:
                return QVariant(Qt.AlignCenter | Qt.AlignVCenter)
            elif column == 5:
                return QVariant(Qt.AlignCenter | Qt.AlignVCenter)
            elif column == 6:
                return QVariant(Qt.AlignCenter | Qt.AlignVCenter)
            elif column == 7:
                return QVariant(Qt.AlignCenter | Qt.AlignVCenter)
            return QVariant(Qt.AlignLeft | Qt.AlignVCenter)

        elif role == Qt.DecorationRole:
            row = index.row()
            column = index.column()
            item = self.items[row]
            if column == 1:
                if item.isLost:
                    return QVariant(QtGui.qApp.style().standardIcon(QtGui.QStyle.SP_MessageBoxWarning))
                else:
                    #                    return QVariant(QtGui.QIcon(QtGui.QPixmap(row*10,row*10)))
                    return QVariant(QtGui.QColor(0, 0, 0, 0))
        #        elif role == Qt.DecorationRole:
            if column == 5:
                if item.additionalSignatures:
                    return QVariant(QtGui.qApp.style().standardIcon(QtGui.QStyle.SP_MessageBoxInformation))
                return QVariant()

        elif role == Qt.ToolTipRole:
            column = index.column()
            if column == 5:
                row = index.row()
                item = self.items[row]
                if self._getAddSignatures(item):
                    tooltip = ('<html><body><table width = 400>' +
                               ''.join('<tr><td>%s</td></tr>' % self._getAddSignatures(item) + '</table></body></html>'))
                    return tooltip
            if column == 7:
                row = index.row()
                item = self.items[row]
                return QVariant(item.getRespSignerToolTip())
            if column == 8:
                row = index.row()
                item = self.items[row]
                return QVariant(item.getOrgSignerToolTip())

        return QVariant()


    def sort(self, column, order=Qt.AscendingOrder):
#        def prepKey(s):
#            return ( convertKeyForNaturalSort(s.upper().replace(u'Ё', u'Е'))
#                     + unichr(0xFFFF)
#                     + s
#                   )
        def prepKey(s):
            return locale.strxfrm(convertKeyForNaturalSort(s))

        keys = {0: lambda item: prepKey(item.newName),
                1: lambda item: prepKey(item.comment),
                2: lambda item: item.size,
                3: lambda item: item.lastModified,
                4: lambda item: forceString(self._getPersonName(item.authorId)),
                5: lambda item: forceString(self._getPersonNameWithSnils(item)),
                6: lambda item: forceString(self._getPersonName(item.getRespSignerId())),
                7: lambda item: forceString(self._getPersonName(item.getOrgSignerId())),
                }
        self.items.sort(key=keys[column], reverse=order != Qt.AscendingOrder)
        self.reset()


    def removeRows(self, row,  count, parent = QModelIndex()):
        self.beginRemoveRows(parent, row, row+count-1)
        try:
            del self.items[row: row+count]
            self.changed.emit()
            return True
        except:
            return False
        finally:
            self.endRemoveRows()


    def isNotEmpty(self):
        return bool(self.items)


#    def append(self, item):
#        self.items.append(item)


    def setAttachedFileItemList(self, attachedFileItemList):
        self.items = attachedFileItemList
        self.reset()


    def uploadFiles(self, localFileList):
        for localFile in localFileList:
            fileItem = self.interface.uploadFile(localFile)
            if fileItem:
                self.beginInsertRows(QModelIndex(), len(self.items), len(self.items)+1)
                self.items.append( fileItem )
                self.endInsertRows()
        self.changed.emit()


    def uploadBytes(self, fileName, fileBytes, userSignatureBytes, orgSignatureBytes, templateId=None, html=''):
        fileItem = self.interface.uploadBytes(fileName, fileBytes)
        fileItem.templateId = templateId
        fileItem.setRespSignature(userSignatureBytes, QtGui.qApp.userId, QDateTime().currentDateTime())
        fileItem.setOrgSignature(orgSignatureBytes, QtGui.qApp.userId, QDateTime().currentDateTime())
        if html:
            fileItem.setHtmlTemplate(html)
        self.beginInsertRows(QModelIndex(), 1, len(self.items)+1)
        self.items.append(fileItem)
        self.endInsertRows()
        self.changed.emit()


#?
    def saveFiles(self):
        return self.interface.saveFiles(self.items)

    def indexOfItem(self, item):
        return self.items.index(item)

    def touchRow(self, row):
        self.emit(SIGNAL('dataChanged()'), self.index(row, 0), self.index(row, self.columnCount()-1))
        self.changed.emit()

    def renameFile(self, row, newName):
        self.items[row].rename(newName)
        self.touchRow(row)
        self.changed.emit()

    def edtComment(self, row, comment):
        self.items[row].edtComment(comment)
        self.touchRow(row)
        self.changed.emit()


def getFilterCond(filter, table, extTable=None):
    filterCond = []
    if extTable and filter.get('begSetDate', None):
        if extTable.tableName == u'Action':
            filterCond.append(extTable['begDate'].dateGe(filter.get('begSetDate')))
            filterCond.append(extTable['begDate'].dateLt(filter.get('endSetDate')))
        elif extTable.tableName == u'Event':
            filterCond.append(extTable['setDate'].dateGe(filter.get('begSetDate')))
            filterCond.append(extTable['setDate'].dateLt(filter.get('endSetDate')))
    if filter.get('begDate', None):
        filterCond.append(table['createDatetime'].dateGe(filter.get('begDate')))
        filterCond.append(table['createDatetime'].dateLt(filter.get('endDate')))
    if filter.get('authorId', None):
        filterCond.append(table['createPerson_id'].eq(filter.get('authorId')))
    if filter.get('signerId', None):
        filterCond.append(table['respSigner_id'].eq(filter.get('signerId')))
    if filter.get('fileName', None):
        fileName = filter.get('fileName').replace('_', '\\_').replace('%', '\\%')
        filterCond.append(u'SUBSTRING_INDEX({0}, "/", -1) LIKE "%{1}%"'.format(table['path'], fileName))
    return filterCond
