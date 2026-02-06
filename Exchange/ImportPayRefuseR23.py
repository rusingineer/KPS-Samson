# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
import os
import hashlib

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, QDir, pyqtSignature, QRegExp, Qt, QVariant, QDateTime, QFile
from Exchange.XmlStreamReader import CXmlStreamReader

from library.dbfpy.dbf import Dbf
from library.Utils import forceBool, forceDate, forceRef, forceString, nameCase, toVariant, forceInt, formatName, \
    forceStringEx

from Accounting.Utils import updateAccounts, updateDocsPayStatus
from Events.Utils import CPayStatus, getPayStatusMask
from Exchange.Cimport import CDBFimport
from Exchange.Utils import dbfCheckNames, tbl, xmlCheckNames
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CReportViewDialog
from Registry.Utils import getClientPolicyEx, getClientSocStatuses, getSocStatusClassList, getCleintSocStatusType, \
    getSocStatusTypeClasses, getClientSvoSocStatus
from zipfile import is_zipfile, ZipFile
from Exchange.ExportR23Native import CExportPage1, updateInternalHash, CExportR23NoKeysDialog, updateInternalHashFLK
from Exchange.Ui_ImportPayRefuseR23 import Ui_Dialog
import re

def ImportPayRefuseR23Native(widget, accountId, accountItemIdList):
    dlg = CImportPayRefuseR23Native(widget, accountId, accountItemIdList)
    dlg.edtFileName.setText(forceString(QtGui.qApp.preferences.appPrefs.get('ImportPayRefuseR23FileName', '')))
    dlg.chkAddPolicyInfo.setChecked(forceBool(QtGui.qApp.preferences.appPrefs.get('ImportPayRefuseR23AddPolicyInfo', False)))
    dlg.chkDeleteAccount.setChecked(forceBool(QtGui.qApp.preferences.appPrefs.get('ImportPayRefuseR23DeleteAccount', False)))
    dlg.exec_()
    QtGui.qApp.preferences.appPrefs['ImportPayRefuseR23FileName'] = toVariant(dlg.edtFileName.text())
    QtGui.qApp.preferences.appPrefs['ImportPayRefuseR23AddPolicyInfo'] = toVariant(dlg.chkAddPolicyInfo.isChecked())
    QtGui.qApp.preferences.appPrefs['ImportPayRefuseR23DeleteAccount'] = toVariant(dlg.chkDeleteAccount.isChecked())


class CImportPayRefuseR23Native(QtGui.QDialog, Ui_Dialog, CDBFimport):
    sexMap = {u'Ж': 2, u'ж': 2, u'М': 1, u'м': 1}

    @pyqtSignature('')
    def on_btnImport_clicked(self): CDBFimport.on_btnImport_clicked(self)
    @pyqtSignature('')
    def on_btnClose_clicked(self): CDBFimport.on_btnClose_clicked(self)
    @pyqtSignature('')
    def on_btnView_clicked(self): CDBFimport.on_btnView_clicked(self)


    def __init__(self, parent, accountId, accountItemIdList):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.parent = parent
        CDBFimport.__init__(self, self.log)
        self.accountId = accountId
        self.accountItemIdList = accountItemIdList
        self.checkName()
        self.errorPrefix = ''

        self.nProcessed = 0
        self.nPayed = 0
        self.nRefused = 0
        self.nNotFound = 0

        self.tableAccountItem = tbl('Account_Item')
        self.tableEvent = tbl('Event')
        self.tableAccount = tbl('Account')
        self.tableAcc = self.db.join(self.tableAccountItem, self.tableAccount,
            'Account_Item.master_id = Account.id').join(self.tableEvent,
            'Account_Item.event_id = Event.id')

        self.prevContractId = None
        self.financeTypeOMS = forceRef(self.db.translate('rbFinance',
            'code', '2', 'id'))

        self.orgCache = {}
        self.orgInoCache = {}
        self.orgInoOkatoCache = {}
        self.policyKindCache = {}
        self.omsCodesOrg = []
        stmt = u"""SELECT DISTINCT os.bookkeeperCode
            FROM OrgStructure os
            WHERE length(os.bookkeeperCode) = 5 and os.deleted = 0;"""
        query = self.db.query(stmt)
        while query.next():
            record=query.record()
            self.omsCodesOrg.append(forceString(record.value('bookkeeperCode')))

        self.deleteAccount = False
        self.hasFieldPV = True
        self.hasFieldDvozvrat = True
        self.importType2013 = False
        self.defaultPolicyKindId = None
        self.dbfFileNames = {}
        self.db = QtGui.qApp.db
        self.isDispFLK = False
        self.delSocStatus = False
        self.isPreControl = False
        self.importFLK = False
        self.tfomsOGRN = forceString(self.db.translate('Organisation', 'infisCode', '9007', 'OGRN'))


    @pyqtSignature('')
    def on_btnSelectFile_clicked(self):
        result = False
        fstr = ""
        if self.tabImportType.currentIndex() == 2:
            result = QtGui.QMessageBox().question(self,
                                        u'Внимание!',
                                        u'Хотите выбрать всю папку с файлами?',
                                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                        QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes
        if not result:
            if self.isPreControl:
                filter = u'zip Archive (va*.zip)'
            else:
                filter = u'zip Archive (v*.zip)'
            fileNames = QtGui.QFileDialog.getOpenFileNames(
                self, u'Укажите файл с данными', self.edtFileName.text(), filter)
            if len(fileNames):
                fstr = " ".join(['"%s"' % QDir.toNativeSeparators(f) for f in fileNames])
        else:
            fstr = QtGui.QFileDialog.getExistingDirectory(
                self, u'Укажите файл с данными', self.edtFileName.text())
        self.edtFileName.setText(fstr)


    def load_zip(self, fileName):
        try:
            if is_zipfile(forceString(fileName)):
                archive = ZipFile(forceString(fileName), 'r')
                if not self.isPreControl:
                    # если не предконтроль - ищем архив в архиве
                    for file in archive.filelist:
                        if file.filename[-4:] == '.zip':
                            try:
                                import cStringIO as StringIO
                            except ImportError:
                                import StringIO
                            in_memory_archive = StringIO.StringIO(archive.read(file))
                            archive = ZipFile(in_memory_archive, 'r')
                            # archive = ZipFile(forceString(fileName), 'r')
                            break

                names = archive.namelist()
                rxDbf = QRegExp('^[PUDNROICEML]\\d{1,5}.dbf', Qt.CaseInsensitive) #transit
                rxXml = QRegExp('^[PUDNROICEML]\\d{1,5}.xml', Qt.CaseInsensitive)
                found = False
                dbfnames = [] #transit
                xmlnames = []
                for name in names:
                    if rxDbf.exactMatch(name): #transit
                        if not found:
                            found = name[0] == 'P'
                        dbfnames.append(name)
                    elif rxXml.exactMatch(name):
                        if not found:
                            found = name[0] == 'P'
                        xmlnames.append(name)
                if not found and self.tabImportType.currentIndex() != 0:
                    self.err2log(u'В архиве отсутствует паспортная часть')
                    return
                self.dbfFileNames = {} #transit
                self.xmlFileNames = {}
                for dbfname in dbfnames: #transit
                    self.dbfFileNames[dbfname[0]] = (archive.extract(dbfname, QtGui.qApp.getHomeDir()))
                for xmlname in xmlnames:
                    self.xmlFileNames[xmlname[0]] = (archive.extract(xmlname, QtGui.qApp.getHomeDir()))
                self.btnImport.setEnabled(True)
            else:
                self.err2log(u'Выбранный файл отсутствует или не является архивом')
                self.dbfFileNames = {} #transit
                self.xmlFileNames = {}
        except Exception as e:
            self.err2log(u'Ошибка распаковки архива: Невозможно распаковать архив\n' + unicode(e))
            self.dbfFileNames = {} #transit
            self.xmlFileNames = {}



    def err2log(self, e):
        self.log.append('<span style="color:red">' + self.errorPrefix + e + '</span>')


    def importDbf(self):
        dbfP = Dbf(self.dbfFileNames['P'], readOnly=True, encoding='cp866')
        self.labelNum.setText(u'всего записей в источнике:' + str(len(dbfP)))

        requiredFields = ['FIO', 'IMA', 'OTCH', 'POL', 'DATR', 'VS', 'SN']
        self.hasFieldPV = 'PV' in dbfP.header.fields
        self.hasFieldRKEY = 'RKEY' in dbfP.header.fields
        self.hasFieldFKEY = 'FKEY' in dbfP.header.fields
        self.hasFieldDvozvrat = 'DVOZVRAT' in dbfP.header.fields
    
        if self.importFLK:
            requiredFields += ['PL_OGRNF', 'SPSF', 'SPNF', 'CS']
            self.policyTypeId = forceRef(self.db.translate('rbPolicyType', 'code', '1', 'id'))
            self.defaultPolicyKindId = forceRef(self.db.translate('rbPolicyKind', 'code', '1', 'id'))
            self.log.append(u'Режим предварительной проверки счетов.')
            self.accountNumber = forceString(self.db.translate('Account', 'id', self.accountId, 'number'))
            self.importType2013 = dbfCheckNames(dbfP, ['SPVF', 'FIOF', 'IMAF',
                'OTCHF', 'DATRF', 'POLF', 'OKATO_OMSF',  'SNILSF'])
    
        if not dbfCheckNames(dbfP, requiredFields):
            self.log.append(u'в файле импорта отсутствуют необходимые поля.')
            return

        self.progressBar.setMaximum(len(dbfP)-1)

        self.printdata = []
        if self.isPreControl:
            if not self.hasFieldRKEY:
                self.log.append(u'в файле импорта отсутствует поле RKEY')
                return
            self.db.query(u"""drop temporary table if EXISTS tmp_internalKeys""")
            self.db.query(u"""create temporary table if not EXISTS tmp_internalKeys(event_id int, typeFile char(1), row_id int, alt_row_id varchar(40), internalKey varchar(40), RKEY varchar(50), SNILS varchar(14),
            index event_id(event_id), index row_id(row_id), index alt_row_id(alt_row_id), index typeFile(typeFile))""")
            self.RecordList = dict()
            self.importedEvents = set()

            for dbfName in self.dbfFileNames:
                dbf = Dbf(self.dbfFileNames[dbfName], readOnly=True, encoding='cp866')
                self.nProcessed = 0
                self.nPayed = 0
                self.nRefused = 0
                self.nNotFound = 0
                self.progressBar.reset()
                self.progressBar.setValue(0)
                self.progressBar.setMaximum(len(dbf) - 1)
                self.RecordList[dbfName] = []

                for row in dbf:
                    QtGui.qApp.processEvents()
                    if self.abort:
                        break
                    self.progressBar.step()
                    self.nProcessed += 1
                    self.stat.setText(self.statistic % (self.nProcessed, self.nPayed, self.nRefused, self.nNotFound))
                    self.RecordList[dbfName].append(row)
                    if dbfName == 'P' and forceString(row['RKEY']):
                        self.importedEvents.add(forceInt(row['SN']))

            dats = ''
            if self.RecordList['P']:
                dats = forceDate(self.RecordList['P'][0]['DATS'])
                fieldlistD = CExportPage1.fieldListKeyD202005 if dats >= QDate(2020, 5, 1) else CExportPage1.fieldListKeyD
                dats = forceString(dats.month()) + forceString(dats.year())
            updateInternalHash('P', 'SN', self.RecordList['P'], dats, CExportPage1.fieldListKeyP)
            updateInternalHash('U', 'UID', self.RecordList['U'], dats, CExportPage1.fieldListKeyU)
            updateInternalHash('N', None, self.RecordList['N'], dats, CExportPage1.fieldListKeyN, 'NAPR_N')
            updateInternalHash('D', None, self.RecordList['D'], dats, fieldlistD)
            updateInternalHash('R', 'RID', self.RecordList['R'], dats, CExportPage1.fieldListKeyR)
            updateInternalHash('O', 'OID', self.RecordList['O'], dats, CExportPage1.fieldListKeyO)
            updateInternalHash('I', 'IID', self.RecordList['I'], dats, CExportPage1.fieldListKeyI)
            updateInternalHash('C', 'CID', self.RecordList['C'], dats, CExportPage1.fieldListKeyC)
            updateInternalHash('E', 'EID', self.RecordList['E'], dats, CExportPage1.fieldListKeyE)
            updateInternalHash('M', 'MID', self.RecordList['M'], dats, CExportPage1.fieldListKeyM)
            updateInternalHash('L', 'LID', self.RecordList['L'], dats, CExportPage1.fieldListKeyL)

            self.db.query(u"""UPDATE soc_Account_RowKeys sark
                    INNER JOIN tmp_internalKeys t ON t.event_id = sark.event_id AND t.row_id = sark.row_id AND t.typeFile = sark.typeFile
                    set sark.`key` = t.RKEY
                    WHERE t.typeFile in ('P', 'U', 'R', 'O', 'I', 'C', 'E', 'M', 'L') and sark.internalKey = t.internalKey and t.RKEY is not null""")

            self.db.query(u"""UPDATE soc_Account_RowKeys sark
                    INNER JOIN tmp_internalKeys t ON t.event_id = sark.event_id AND t.alt_row_id = sark.alt_row_id AND t.typeFile = sark.typeFile
                    set sark.`key` = t.RKEY
                    WHERE t.typeFile = 'N' and sark.internalKey = t.internalKey and t.RKEY is not null""")

            self.db.query(u"""UPDATE soc_Account_RowKeys sark
                    INNER JOIN tmp_internalKeys t ON t.alt_row_id = sark.alt_row_id AND t.typeFile = sark.typeFile
                    set sark.`key` = t.RKEY
                    WHERE t.typeFile = 'D' and sark.internalKey = t.internalKey and t.RKEY is not null""")
            noKeySet = set()
            if self.importedEvents:
                query = self.db.query(u"""SELECT distinct sark.event_id
                        FROM soc_Account_RowKeys sark
                        WHERE sark.`key` is null and sark.typeFile != 'F' and sark.event_id in ({0})""".format(
                    u','.join([forceString(item) for item in self.importedEvents])))
                while query.next():
                    record = query.record()
                    noKeySet.add(forceInt(record.value('event_id')))

            if noKeySet:
                #  очищаем неполностью загруженные ключи
                self.db.query(u"""UPDATE soc_Account_RowKeys
                                            SET `key` = NULL
                                            WHERE event_id in ({0}) and typeFile != 'F'""".format(
                    u','.join([forceString(item) for item in noKeySet])))

                for rec_p in self.RecordList['P']:
                    if forceRef(rec_p['SN']) in noKeySet:
                        self.noKeysDict[forceRef(rec_p['SN'])] = [forceDate(rec_p['DATS']),
                                                            forceRef(rec_p['NS']), forceRef(rec_p['SN']),
                                                            formatName(forceString(rec_p['FIO']),
                                                                        forceString(rec_p['IMA']),
                                                                        forceString(rec_p['OTCH']))]

            qr = self.db.query(u"""SELECT count(distinct sark.event_id) 
                                                        FROM soc_Account_RowKeys sark
                                                        INNER JOIN tmp_internalKeys t ON t.event_id = sark.event_id AND t.row_id = sark.row_id AND t.typeFile = sark.typeFile
                                                        WHERE t.typeFile = 'P' and sark.internalKey = t.internalKey and sark.`key` is not null""")
            qr.first()
            self.nPayed = qr.record().value(0).toInt()[0]
            self.nProcessed = len(self.RecordList['P'])
            self.db.query(u"""drop temporary table if EXISTS tmp_internalKeys""")
            self.stat.setText(self.statistic % (self.nProcessed, self.nPayed, self.nRefused, self.nNotFound))
        else:
            #пробуем запихнуть дбф в список и упорядочить
            recList = []
            rowList = []
            for row in dbfP:
                recList.append(row.fieldData)
            recList.sort(key=lambda item: item[4])
            row = dbfP.newRecord()
            eventList = []
            for rec in recList:
                row = dbfP.newRecord()
                row.fieldData = rec
                rowList.append(row)

            if self.importFLK:
                if not self.hasFieldFKEY:
                    self.log.append(u'в файле импорта отсутствует поле FKEY')
                    return
                self.db.query(u"""drop temporary table if EXISTS tmp_internalKeysFLK""")
                self.db.query(u"""create temporary table if not EXISTS tmp_internalKeysFLK(event_id int, typeFile char(1), internalKey varchar(40), FKEY varchar(50), index event_id(event_id))""")
                updateInternalHashFLK(rowList, CExportPage1.fieldListKeyFLKImport)
                QtGui.qApp.processEvents()
                #  записываем ключи
                self.db.query(u"""UPDATE soc_Account_RowKeys sark
                        INNER JOIN tmp_internalKeysFLK t ON t.event_id = sark.event_id AND t.typeFile = sark.typeFile
                        set sark.internalKey = t.internalKey, `key` = t.FKEY
                        WHERE t.typeFile = 'F' and t.FKEY is not null""")
                QtGui.qApp.processEvents()
                #  вставляем отсутствующие записи для ключей файла ФЛК
                self.db.query(u"""INSERT INTO soc_Account_RowKeys(event_id, typeFile, internalKey, `key`)
                        select t.event_id, t.typeFile, t.internalKey, t.FKEY
                        from tmp_internalKeysFLK t
                        left JOIN soc_Account_RowKeys sark ON t.event_id = sark.event_id and t.typeFile = sark.typeFile
                        where t.typeFile = 'F' AND sark.id is null""")

            # бежим по упорядоченному списку, каждый элемент вставляем в шаблон записи исходной дбф
            for rec in recList:
                row.fieldData = rec
                QtGui.qApp.processEvents()
                if self.abort:
                    break
                self.progressBar.step()
                self.stat.setText(self.statistic % (self.nProcessed, self.nPayed, self.nRefused, self.nNotFound))
                self.process(row)
                eventList.append(forceRef(row['SN']))
                self.nProcessed += 1
            if self.currentAccountId and QtGui.qApp.checkGlobalPreference(u'23:ImportAccountPayed', u'да'):
                tableAccountItem = self.db.table('Account_Item')
                cond = [tableAccountItem['master_id'].eq(self.currentAccountId),
                        tableAccountItem['deleted'].eq(0),
                        tableAccountItem['event_id'].notInlist(eventList)
                        ]
                epxr = [tableAccountItem['number'].eq(u'б/н'),
                        'Account_Item.`date` = CURDATE()',
                        'Account_Item.payedSum = Account_Item.sum',
                        'Account_Item.refuseType_id = NULL'
                ]
                self.db.updateRecords(tableAccountItem, epxr, self.db.joinAnd(cond))
            self.stat.setText(self.statistic % (self.nProcessed, self.nPayed, self.nRefused, self.nNotFound))

            if self.importFLK:
                if self.deleteAccount and self.chkDeleteAccount.isChecked():
                    self.log.append(u'Территория страхования одного из пациентов изменилась, текущий счет будет удалён.')
                    self.parent.tblAccounts.removeSelectedRows()
                    self.parent.updateAccountsPanel(self.parent.modelAccounts.idList())
            else:
                updateAccounts(list(self.accountIdSet))
        dbfP.close()


    def importXml(self):
        self.GROUP_NAMES = {
        'ZL_LIST' : ('ZGLV', 'SCHET', 'ZAP'),
        'ZAP': ('PACIENT', 'Z_SL'),
        'Z_SL': ('SL','DSVED'),
        'SL': ('USL', 'SANK','CONS', 'ONK_SL','DS2_N','NAPR','NAZ', 'LEK_PR'),
        'ONK_SL':('ONK_USL','B_DIAG','B_PROT'),
        'ONK_USL':('LEK_PR'),
        'USL': ('KSLP','DENTES', 'MR_USL_N', 'MED_DEV'),
        'KSLP': ('SL_KOEF'),
        'DENTES': ('DENT'),
        'DENT': ('SURFACES'),
        'KSLP': ('SL_KOEF'),
        'LEK_PR':('LEK_DOSE')
    }
        txtFile = QFile(self.xmlFileNames['P'])
        if not txtFile.open(QFile.ReadOnly | QFile.Text):
            self.err2log(u'Ошибка открытия файла {0} для чтения: {1}'
                            .format(self.xmlFileNames['P'],
                                    forceString(txtFile.errorString())))
            pass
        self.reader = CXmlStreamReader(self, self.GROUP_NAMES, 'ZL_LIST', self.log, 'ZAP')
        self.reader.setDevice(txtFile)
        result = False
        self.progressBar.setFormat('%p%')
        self.progressBar.reset()
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(txtFile.size() - 1)
        self.nProcessed = 0
        self.nPayed = 0
        self.nRefused = 0
        self.nNotFound = 0
        self.RecordList = {'P': []}
        self.importedEvents = set()
        self.printdata = []
        recList = []
        if self.reader.readHeader():
            self.log.append(u'Режим предварительной проверки счетов.')
            count = 0
            if self.importFLK:
                self.policyTypeId = forceRef(self.db.translate('rbPolicyType', 'code', '1', 'id'))
                self.defaultPolicyKindId = forceRef(self.db.translate('rbPolicyKind', 'code', '1', 'id'))
                self.accountNumber = forceString(self.db.translate('Account', 'id', self.accountId, 'number'))

            for name, row in self.reader.readData():
                if name == 'ZAP':
                    count += 1
                    self.labelNum.setText(u'всего записей в источнике:' + str(count))
                    self.hasFieldPV = bool(row.get('PV', False))
                    self.hasFieldRKEY = bool(row.get('RKEY', False))
                    self.hasFieldFKEY = bool(row.get('FKEY', False))
                    self.hasFieldDvozvrat = bool(row.get('DVOZVRAT', False))

                    if self.isPreControl:
                        if not self.hasFieldRKEY:
                            self.log.append(u'в файле импорта отсутствует поле RKEY')
                            return
                        self.db.query(u"""drop temporary table if EXISTS tmp_internalKeys""")
                        self.db.query(u"""create temporary table if not EXISTS tmp_internalKeys(event_id int, typeFile char(1), row_id int, alt_row_id varchar(40), internalKey varchar(40), RKEY varchar(50), SNILS varchar(14),
                        index event_id(event_id), index row_id(row_id), index alt_row_id(alt_row_id), index typeFile(typeFile))""")
                    else:
                        recList.append(row)
                    QtGui.qApp.processEvents()
                    if self.abort:
                        break
                    self.RecordList['P'].append(row)
                    if forceString(row.get('RKEY', '')):
                        self.importedEvents.add(forceInt(row.get('SN', None))) 
                QtGui.qApp.processEvents()

            if self.reader.hasError() or self.abort:
                self.err2log(self.reader.errorString())
            if self.isPreControl:
                dats = ''
                if self.RecordList['P']:
                    dats = forceDate(self.RecordList['P'][0].get('DATS', None))
                    fieldlistD = CExportPage1.fieldListKeyD202005 if dats >= QDate(2020, 5, 1) else CExportPage1.fieldListKeyD
                    dats = forceString(dats.month()) + forceString(dats.year())
                updateInternalHash('P', 'SN', self.RecordList['P'], dats, CExportPage1.fieldListKeyP)
                updateInternalHash('U', 'UID', self.RecordList['U'], dats, CExportPage1.fieldListKeyU)
                updateInternalHash('N', None, self.RecordList['N'], dats, CExportPage1.fieldListKeyN, 'NAPR_N')
                updateInternalHash('D', None, self.RecordList['D'], dats, fieldlistD)
                updateInternalHash('R', 'RID', self.RecordList['R'], dats, CExportPage1.fieldListKeyR)
                updateInternalHash('O', 'OID', self.RecordList['O'], dats, CExportPage1.fieldListKeyO)
                updateInternalHash('I', 'IID', self.RecordList['I'], dats, CExportPage1.fieldListKeyI)
                updateInternalHash('C', 'CID', self.RecordList['C'], dats, CExportPage1.fieldListKeyC)
                updateInternalHash('E', 'EID', self.RecordList['E'], dats, CExportPage1.fieldListKeyE)
                updateInternalHash('M', 'MID', self.RecordList['M'], dats, CExportPage1.fieldListKeyM)
                updateInternalHash('L', 'LID', self.RecordList['L'], dats, CExportPage1.fieldListKeyL)

                self.db.query(u"""UPDATE soc_Account_RowKeys sark
                        INNER JOIN tmp_internalKeys t ON t.event_id = sark.event_id AND t.row_id = sark.row_id AND t.typeFile = sark.typeFile
                        set sark.`key` = t.RKEY
                        WHERE t.typeFile in ('P', 'U', 'R', 'O', 'I', 'C', 'E', 'M', 'L') and sark.internalKey = t.internalKey and t.RKEY is not null""")

                self.db.query(u"""UPDATE soc_Account_RowKeys sark
                        INNER JOIN tmp_internalKeys t ON t.event_id = sark.event_id AND t.alt_row_id = sark.alt_row_id AND t.typeFile = sark.typeFile
                        set sark.`key` = t.RKEY
                        WHERE t.typeFile = 'N' and sark.internalKey = t.internalKey and t.RKEY is not null""")

                self.db.query(u"""UPDATE soc_Account_RowKeys sark
                        INNER JOIN tmp_internalKeys t ON t.alt_row_id = sark.alt_row_id AND t.typeFile = sark.typeFile
                        set sark.`key` = t.RKEY
                        WHERE t.typeFile = 'D' and sark.internalKey = t.internalKey and t.RKEY is not null""")
                noKeySet = set()
                if self.importedEvents:
                    query = self.db.query(u"""SELECT distinct sark.event_id
                            FROM soc_Account_RowKeys sark
                            WHERE sark.`key` is null and sark.typeFile != 'F' and sark.event_id in ({0})""".format(
                        u','.join([forceString(item) for item in self.importedEvents])))
                    while query.next():
                        record = query.record()
                        noKeySet.add(forceInt(record.value('event_id')))

                if noKeySet:
                    #  очищаем неполностью загруженные ключи
                    self.db.query(u"""UPDATE soc_Account_RowKeys
                                                SET `key` = NULL
                                                WHERE event_id in ({0}) and typeFile != 'F'""".format(
                        u','.join([forceString(item) for item in noKeySet])))

                    for rec_p in self.RecordList['P']:
                        self.progressBar.step()
                        self.nProcessed += 1
                        self.stat.setText(self.statistic % (self.nProcessed, self.nPayed, self.nRefused, self.nNotFound))
                        if forceRef(rec_p.get('SN', None)) in noKeySet:
                            self.noKeysDict[forceRef(rec_p['SN'])] = [forceDate(rec_p.get('DATS', None)),
                                                                forceRef(rec_p.get('NS', None)), forceRef(rec_p.get('SN',None)),
                                                                formatName(forceString(rec_p.get('FIO', '')),
                                                                            forceString(rec_p.get('IMA', '')),
                                                                            forceString(rec_p.get('OTCH', '')))]

                qr = self.db.query(u"""SELECT count(distinct sark.event_id) 
                                                            FROM soc_Account_RowKeys sark
                                                            INNER JOIN tmp_internalKeys t ON t.event_id = sark.event_id AND t.row_id = sark.row_id AND t.typeFile = sark.typeFile
                                                            WHERE t.typeFile = 'P' and sark.internalKey = t.internalKey and sark.`key` is not null""")
                qr.first()
                self.nPayed = qr.record().value(0).toInt()[0]
                self.nProcessed = len(self.RecordList['P'])
                self.db.query(u"""drop temporary table if EXISTS tmp_internalKeys""")
                self.stat.setText(self.statistic % (self.nProcessed, self.nPayed, self.nRefused, self.nNotFound))
            else:
                rowList = []
                eventList = []
                eventIdList = set()
                clientIdList = set()
                self.eventRecordDict = {}
                self.clientRecordDict = {}
                for rec in recList:
                    rowList.append(rec)
                    if forceString(rec.get('FKEY')):
                        eventIdList.add(forceInt(rec.get('SN', None)))

                # Для ускорения подгрузки данных события/пациента
                eventRecordList = self.db.getRecordList(self.tableEvent, '*', self.tableEvent['id'].inlist(eventIdList))
                for record in eventRecordList:
                    self.eventRecordDict[forceRef(record.value('id'))] = record
                    clientIdList.add(forceRef(record.value('client_id')))
                    relativeId = forceRef(record.value('relative_id'))
                    if relativeId:
                        clientIdList.add(relativeId)

                clientRecordList = self.db.getRecordList(self.tableClient, '*', self.tableClient['id'].inlist(clientIdList))
                for record in clientRecordList:
                    self.clientRecordDict[forceRef(record.value('id'))] = record

                #
                if self.importFLK:
                    self.db.query(u"""drop temporary table if EXISTS tmp_internalKeysFLK""")
                    self.db.query(u"""create temporary table if not EXISTS tmp_internalKeysFLK(event_id int, typeFile char(1), internalKey varchar(40), FKEY varchar(50), index event_id(event_id))""")
                    self.updateInternalHashFLK(rowList, CExportPage1.fieldListKeyFLKImport)
                    QtGui.qApp.processEvents()
                    #  записываем ключи
                    self.db.query(u"""UPDATE soc_Account_RowKeys sark
                            INNER JOIN tmp_internalKeysFLK t ON t.event_id = sark.event_id AND t.typeFile = sark.typeFile
                            set sark.internalKey = t.internalKey, `key` = t.FKEY
                            WHERE t.typeFile = 'F' and t.FKEY is not null""")
                    QtGui.qApp.processEvents()
                    #  вставляем отсутствующие записи для ключей файла ФЛК
                    self.db.query(u"""INSERT INTO soc_Account_RowKeys(event_id, typeFile, internalKey, `key`)
                            select t.event_id, t.typeFile, t.internalKey, t.FKEY
                            from tmp_internalKeysFLK t
                            left JOIN soc_Account_RowKeys sark ON t.event_id = sark.event_id and t.typeFile = sark.typeFile
                            where t.typeFile = 'F' AND sark.id is null""")

                # бежим по упорядоченному списку, каждый элемент вставляем в шаблон записи исходной дбф
                statistic = u'обработано: %d; идентифицировано: %d; не идентифицировано: %d; не найдено: %d'
                self.progressBar.setValue(0)
                self.progressBar.setMaximum(len(recList) - 1)

                for row in recList:
                    QtGui.qApp.processEvents()
                    if self.abort:
                        break
                    self.progressBar.step()
                    self.stat.setText(statistic % (self.nProcessed, self.nPayed, self.nRefused, self.nNotFound))
                    self.process(row)
                    eventList.append(forceRef(row.get('SN', None)))
                if self.currentAccountId and QtGui.qApp.checkGlobalPreference(u'23:ImportAccountPayed', u'да'):
                    tableAccountItem = self.db.table('Account_Item')
                    cond = [tableAccountItem['master_id'].eq(self.currentAccountId),
                            tableAccountItem['deleted'].eq(0),
                            tableAccountItem['event_id'].notInlist(eventList)
                            ]
                    epxr = [tableAccountItem['number'].eq(u'б/н'),
                            'Account_Item.`date` = CURDATE()',
                            'Account_Item.payedSum = Account_Item.sum',
                            'Account_Item.refuseType_id = NULL'
                    ]
                    self.db.updateRecords(tableAccountItem, epxr, self.db.joinAnd(cond))
                self.stat.setText(statistic % (self.nProcessed, self.nPayed, self.nRefused, self.nNotFound))

                if self.importFLK:
                    if self.deleteAccount and self.chkDeleteAccount.isChecked():
                        self.log.append(u'Территория страхования одного из пациентов изменилась, текущий счет будет удалён.')
                        self.parent.tblAccounts.removeSelectedRows()
                        self.parent.updateAccountsPanel(self.parent.modelAccounts.idList())
                else:
                    updateAccounts(list(self.accountIdSet))
        txtFile.close()


    def updateInternalHashFLK(self, recordList, fieldList):
        if len(recordList):
            strValuesList = []
            for rec in recordList:
                valueList = []
                for (fld1, fld2) in fieldList:
                    value = forceString(rec.get(fld1)) if forceString(rec.get(fld1)) else forceString(rec.get(fld2))
                    if fld1 in ['POLF', 'POL', 'DATR', 'DATRF'] and '2' in forceString(rec.get('Q_G')):
                        value = forceString(rec.get('POLP')) if fld1 in ['POL', 'POLF'] else forceString(rec.get('DATRP'))
                    if fld1 in ['FIOF', 'IMAF', 'OTCHF']:
                        value = value.upper()
                    valueList.append(value)
                stringKey = ''.join(valueList)
                hashKey = hashlib.sha1(stringKey.encode('utf-8')).hexdigest()
                sn = forceString(rec.get('SN'))
                if QtGui.qApp.rkey and sn == QtGui.qApp.rkey:
                    QtGui.qApp.log(u'FKEY', stringKey)
                    QtGui.qApp.log(u'FKEY', hashKey)
                fkey = ("'" + forceString(rec.get('FKEY')) + "'") if forceString(rec.get('FKEY')) else 'NULL'
                strValuesList.append(u"({0}, 'F', '{1}', {2})".format(sn, hashKey, fkey))
            QtGui.qApp.db.query(u"insert into tmp_internalKeysFLK(event_id, typeFile, internalKey, FKEY) values {0}".format(','.join(strValuesList)))
        

    def startImport(self):
        self.isDispFLK = False  
        self.delSocStatus = False
        if self.isPreControl:
            self.statistic = u'обработано: %d; без ошибок: %d; с ошибками: %d; не найдено: %d'
        else:
            self.statistic = u'обработано: %d; оплаченых: %d; отказаных: %d; не найдено: %d'
        
        # print self.edtFileName.text()
        if self.tabImportType.currentIndex() == 2 and os.path.isdir(self.edtFileName.text()):
            if self.isPreControl:
                filter = u'va*.zip'
            else:
                filter = u'v*.zip'
            dir = QDir(self.edtFileName.text())
            fileNames = dir.entryList([filter], QDir.Files)
            fileNames = [dir.absoluteFilePath(f) for f in fileNames]
        else:
            fileNames = re.findall('"(.+?)"', self.edtFileName.text())

        if not len(fileNames):
            return
        self.noKeysDict = {}
        for i, fileName in enumerate(fileNames):
            if i == 0:
                self.log.append(fileName + '\r\n')
            else:
                self.log.append('\r\n' + fileName + '\r\n')

            self.load_zip(fileName)

            if self.xmlFileNames or self.dbfFileNames:
                self.deleteAccount = False
                self.progressBar.setFormat('%p%')
                self.currentAccountOnly = self.chkOnlyCurrentAccount.isChecked()
                self.addPolicyInfo = self.chkAddPolicyInfo.isChecked()
                self.confirmation = self.edtConfirmation.text()

                if not self.confirmation:
                    self.log.append(u'нет подтверждения')
                    return
        
                self.prevContractId = None
                self.accountIdSet = set()
                self.currentAccountId = None
        
                self.nProcessed = 0
                self.nPayed = 0
                self.nRefused = 0
                self.nNotFound = 0

                if self.importFLK:
                    self.process = self.processPolicyRowXml if self.xmlFileNames else self.processPolicyRow
                else:
                    self.process = self.processRow
                if self.dbfFileNames:
                    self.importDbf()
                elif self.xmlFileNames and self.importFLK:
                    self.importXml()
                
            elif QtGui.qApp.checkGlobalPreference(u'23:ImportAccountPayed', u'да'):
                baseDir, name = os.path.split(forceString(fileName))
                if re.match('v[0-9]{14}.zip', name.lower()):
                    number = name[1:15]
                    qr = self.db.query(u"""SELECT id From Account a WHERE exportedName = '{0}' AND deleted = 0 order BY `date` DESC limit 1""".format(number))
                    if qr.first():
                        record = qr.record()
                        accountId = forceRef(record.value('id'))
                        self.db.query(u"""Update Account_Item ai
                        set ai.date = curdate(), ai.number = 'б/н', ai.payedSum = ai.sum, ai.refuseType_id = NULL
                        WHERE ai.master_id = {0} and ai.deleted = 0""".format(forceString(accountId)))
                        self.db.query(u"call updateAccount({0})".format(forceString(accountId)))

        if self.isPreControl and self.noKeysDict:
            if self.noKeysDict:
                dial = CExportR23NoKeysDialog(self, self.noKeysDict, title=u"Результаты импорта RKEY",
                                              message=u"Импортируемый ключ RKEY не соответствует данным персонального счета. Проведите экспорт указанных персональных счетов на предварительный контроль")
                dial.exec_()

        if self.importFLK and QtGui.QMessageBox.question(self,
                                       u'Внимание!',
                                       u'Печатать результат проверки?',
                                       QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                       QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
            self.printReport()

    def processRow(self, row):
        lastName = forceString(row['FIO'])
        firstName = forceString(row['IMA'])
        patrName = forceString(row['OTCH'])

        if self.hasFieldDvozvrat:
            refuseDate = QDate(row['DVOZVRAT']) if row['DVOZVRAT'] else QDate()
        else:
            refuseDate = QDate.currentDate()


        refuseReasonCodeList = forceString(row['PV']).split(' ') if self.hasFieldPV else ['Отказано']
        eventId = forceRef(row['SN'])

        payStatusMask = 0
        accDate = QDate(row['DATS']) if row['DATS'] else QDate()
        accNumber = forceString(row['NS'])

        self.errorPrefix = u'Строка %d (%s %s %s): ' % (self.progressBar.value(), lastName,  firstName,  patrName)

        accountType = forceString(row['VS'])
        if accountType not in ['3', 'f', 'b', 'j', 'n', 'r', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'bk', 'bm', 'bu', 'be', 'bg', 'bh', 'bo', 'bv', 'bp', 'bd']:
            self.err2log(u'тип счёта не возвратный, код "%s"' % accountType)
            return

        if refuseDate.isValid() and refuseReasonCodeList == []:
            self.err2log(u'нет кода отказа')
            return

        if not refuseDate.isValid() and refuseReasonCodeList != []:
            self.err2log(u'нет даты отказа')
            return

        if not eventId:
            self.err2log(u'отсутствует идентификатор пациента')

        cond = []
        cond.append(self.tableEvent['id'].eq(toVariant(eventId)))

        if accDate.isValid():
            cond.append(self.tableAccount['date'].eq(toVariant(accDate)))

        if accNumber:
            cond.append(self.tableAccount['number'].eq(toVariant(accNumber)))

        if self.currentAccountOnly:
            cond.append(self.tableAccount['id'].eq(toVariant(self.accountId)))

        fields = """Account_Item.id, Account.date as Account_date, Account_Item.date as Account_Item_date,
        Account_Item.master_id as Account_id, Account.contract_id as contract_id"""
        recordList = self.db.getRecordList(self.tableAcc, fields, where=cond)

        if recordList != []:
            for record in recordList:
                self.accountIdSet.add(forceRef(record.value('Account_id')))
                self.currentAccountId = forceRef(record.value('Account_id'))
                contractId = forceRef(record.value('contract_id'))

                if self.prevContractId != contractId:
                    self.prevContractId = contractId
                    financeId = forceRef(self.db.translate('Contract', 'id', contractId, 'finance_id'))
                    payStatusMask = getPayStatusMask(financeId)

                accDate = forceDate(record.value('Account_date'))
                accItemDate = forceDate(record.value('Account_Item_date'))

                if accItemDate:
                    self.err2log(u'счёт уже отказан')
                    return

                if accDate > refuseDate:
                    self.err2log(u'счёт уже отказан')
                    return

                self.nProcessed += 1
                accountItemId = forceRef(record.value('id'))
                accItem = self.db.getRecord(self.tableAccountItem, '*', accountItemId)
                accItem.setValue('date', toVariant(refuseDate))
                refuseTypeId = None

                if refuseDate:
                    self.nRefused += 1
                    refuseTypeId = self.getRefuseTypeId(refuseReasonCodeList[0])

                if not refuseTypeId:
                    refuseTypeId = self.addRefuseTypeId(refuseReasonCodeList[0], financeId=self.financeTypeOMS)

                accItem.setValue('refuseType_id', toVariant(refuseTypeId))
                accItem.setValue('payedSum', toVariant(0))
                updateDocsPayStatus(accItem, payStatusMask, CPayStatus.refusedBits)

                accItem.setValue('number', toVariant(self.confirmation))
                self.db.updateRecord(self.tableAccountItem, accItem)
        else:
            self.nNotFound += 1
            self.err2log(u'счёт не найден')


    # def processPreControl(self, row):
    #     lastName = forceString(row['FIO'])
    #     firstName = forceString(row['IMA'])
    #     patrName = forceString(row['OTCH'])
    #     self.dats = forceString(forceDate(row['DATS']).toString("MMyyyy"))
    #
    #
    #     accDate = QDate(row['DATS'])
    #     eventId = forceRef(row['SN'])
    #
    #     if not eventId:
    #         self.err2log(u'отсутствует идентификатор события')
    #         self.nNotFound += 1
    #
    #     if not self.accountId:
    #         accNumber = forceString(row['NS'])
    #         cond = [self.tableAccount['deleted'].eq(0)]
    #         if accDate.isValid():
    #             cond.append(self.tableAccount['date'].eq(toVariant(accDate)))
    #         if accNumber:
    #             cond.append(self.tableAccount['number'].eq(toVariant(accNumber)))
    #
    #         record = self.db.getRecordEx(self.tableAccount, 'id', where=cond)
    #         if record:
    #             self.accountId = forceRef(record.value('id'))
    #
    #     self.errorPrefix = u'Строка %d (%s %s %s) перс.счет № %s: ' % (self.progressBar.value(), lastName, firstName, patrName, eventId)
    #
    #     if forceString(row['RKEY']):
    #         # cond = "event_id = {1} and typeFile = '{2}' and row_id = {3}".format(eventId, 'P', eventId)
    #         # keyRec = self.db.getRecordEx('soc_Account_RowKeys', '*', where=cond)
    #         # if not keyRec:
    #         #     keyRec = self.db.table('soc_Account_RowKeys').newRecord()
    #         #     keyRec.setValue('account_id', toVariant(self.accountId))
    #         #     keyRec.setValue('event_id', toVariant(eventId))
    #         #     keyRec.setValue('typeFile', toVariant('P'))
    #         #     keyRec.setValue('row_id', toVariant(eventId))
    #         # keyRec.setValue('key', forceString(row['RKEY']))
    #         # self.db.insertOrUpdate('soc_Account_RowKeys', keyRec)
    #         self.nPayed += 1
    #     else:
    #         self.err2log(u'Коды ошибок: {0}'.format(forceString(row['PV'])))
    #         self.nRefused += 1


    # Импорт ФЛК сделался и давать на печать пробежавшие результаты
    def printReport(self):
        report = CReportBase()
        params = report.getDefaultParams()
        report.saveDefaultParams(params)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Результаты предварительной проверки счетов')
        cursor.insertBlock()
        cursor.insertHtml('<br/><br/>')
        table = createTable(cursor, [('30%', [u'Пациент'], CReportBase.AlignLeft),
                                     ('70%', [u'Результат'], CReportBase.AlignLeft)
                                     ]
                            )
        for printRow in self.printdata:
            row = table.addRow()
            table.setHtml(row, 0, printRow[0])

            table.setHtml(row, 1, printRow[1])
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertHtml('<br/><br/>')
        cursor.insertText(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))

        reportView = CReportViewDialog(self)
        reportView.setWindowTitle(u'Результаты предварительной проверки счетов')
        reportView.setOrientation(QtGui.QPrinter.Portrait)
        reportView.setText(doc)
        reportView.exec_()


    def processPolicyRowXml(self, row):
        """Обработка записи ФЛК из xml"""
        lastName = nameCase(forceString(row.get('FIO')))
        firstName = nameCase(forceString(row.get('IMA')))
        patrName = nameCase(forceString(row.get('OTCH')))
        insurerOGRN = forceString(row.get('PL_OGRNF'))
        eventId = forceInt(row.get('SN'))
        msg = []
        self.errorPrefix = u'Строка %d (%s %s %s): ' % (self.progressBar.value(), lastName,  firstName,  patrName)
        requiredFields = ['CODE_MO', 'FIO', 'IMA', 'POL', 'DATR']
        if not xmlCheckNames(row, requiredFields):
            self.err2log(u'отсутствуют необходимые поля.')
            msg.append(u'отсутствуют необходимые поля.')
            self.nProcessed += 1
            self.nRefused += 1
            return
        if not forceString(row.get('FKEY')):
            self.nProcessed += 1
            self.nRefused += 1
            return
        if not insurerOGRN:
            self.err2log(u'отсутствует ОГРН плательщика')
            msg.append(u'отсутствует ОГРН плательщика')
            self.nProcessed += 1
            self.nRefused += 1
            return
        if not eventId:
            self.err2log(u'отсутствует идентификатор пациента')
            msg.append(u'отсутствует идентификатор пациента')
            self.nProcessed += 1
            self.nRefused += 1
            return

        self.nPayed += 1

        serial = forceString(row.get('SPSF'))
        number = forceString(row.get('SPNF'))
        enp = forceString(row.get('ENPF'))

        oldInsurerOGRN = forceString(row.get('PL_OGRN'))
        Q_G = forceString(row.get('Q_G'))

        newInsurerOkato = forceString(row.get('OKATO_OMSF'))
        if newInsurerOkato != '03000' and newInsurerOkato != '':
            (insurerId, insurerArea) = self.findOrgByOKATO(newInsurerOkato)
        else:
            (insurerId, insurerArea) = self.findOrgByOGRN(insurerOGRN)

        # если DATPS пустой, ищем по client_id, если заполненный - по event_id
        datPS = forceString(row.get('DATPS'))
        if datPS:
            eventRecord = self.eventRecordDict.get(eventId)
            if eventRecord:
                if '2' in Q_G:
                    clientId = forceRef(eventRecord.value('relative_id'))
                else:
                    clientId = forceRef(eventRecord.value('client_id'))

                clientRecord = self.clientRecordDict.get(clientId)
            else:
                self.err2log(u'<b><font color=red>Персональный счет не найден!:</font></b> `%s`' % eventId)
                msg.append(u'Персональный счет не найден!: `%s`' % eventId)
                self.nProcessed += 1
                return
        else:
            clientId = eventId
            clientRecord = self.db.getRecord(self.tableClient, '*', clientId)

        if clientRecord:
            newLastName = nameCase(forceString(row.get('FIOF')))
            newFirstName = nameCase(forceString(row.get('IMAF')))
            newPatrName = nameCase(forceString(row.get('OTCHF')))
            newSex = self.sexMap.get(forceString(row.get('POLF')), 0)
            newBirthDate = QDate.fromString(row.get('DATRF'), 'yyyy-MM-dd') if row.get('DATRF') else QDate()
            newBegDate = QDate.fromString(row.get('DATNP'), 'yyyy-MM-dd') if row.get('DATNP') else QDate()
            newEndDate = QDate.fromString(row.get('DATOP'), 'yyyy-MM-dd') if row.get('DATOP') else QDate()
            newSnils = forceString(row.get('SNILSF')).replace('-', '').replace(' ', '')
            svoSocStatus = forceString(row.get('SOC'))

            if self.updateClient(clientId, newLastName, newFirstName, newPatrName, newSex, newBirthDate, newSnils, clientRecord):
                self.err2log(u'<b><font color=blue>Обновлены</font></b> личные данные клиента' u' %s.' % clientId)
                msg.append(u'Обновлены личные данные клиента' u' %s.' % clientId)

            if not insurerId and insurerOGRN:
                self.err2log(u'Страховая компания с ОГРН кодом `%s` не найдена.' % insurerOGRN)
                msg.append(u'Страховая компания с ОГРН кодом `%s` не найдена.' % insurerOGRN)
                self.nProcessed += 1
                return

            if clientId and number:
                record = getClientPolicyEx(clientId, True,  QDate.fromString(row.get('DATO'), 'yyyy-MM-dd'), eventId)

                if record:
                    oldSerial = forceString(record.value('serial'))
                    oldNumber = forceString(record.value('number'))
                    oldInsurerId = forceRef(record.value('insurer_id'))
                    oldBegDate = forceDate(record.value('begDate'))
                    oldEndDate = forceDate(record.value('endDate'))
                    policyKindId = self.defaultPolicyKindId
                    policyKindChanged = False

                    # если ОГРН совпадают, страховую оставляем туже
                    if insurerOGRN == oldInsurerOGRN and newInsurerOkato == '03000':
                        insurerId = oldInsurerId

                    if (newInsurerOkato != '03000' and newInsurerOkato != ''
                            and self.findOKATObyOrg(forceInt(record.value('insurer_id'))) == newInsurerOkato):
                        insurerId = oldInsurerId
                        
                    oldPolicyKindId = forceRef(record.value('policyKind_id'))
                    newPolicyKindId = self.getPolicyKindByRegionalCode(forceString(row.get('SPVF')))

                    if newPolicyKindId:
                        policyKindId = newPolicyKindId
                        policyKindChanged = newPolicyKindId != oldPolicyKindId

                    if oldSerial != serial or oldNumber != number \
                            or oldInsurerId != insurerId or policyKindChanged \
                            or oldBegDate != newBegDate or oldEndDate != newEndDate:

                        if oldBegDate and oldBegDate != newBegDate:
                            # проверка наличия такого же полиса
                            table = self.tableClientPolicy
                            if not self.db.getRecordEx(table, 'id', [table['deleted'].eq(0),
                                                                     table['client_id'].eq(clientId),
                                                                     table['insurer_id'].eq(insurerId),
                                                                     table['number'].eq(number),
                                                                     table['serial'].eq(serial),
                                                                     table['begDate'].eq(newBegDate),
                                                                     table['endDate'].eq(newEndDate) if newEndDate else table['endDate'].isNull(),
                                                                     table['policyType_id'].eq(self.policyTypeId),
                                                                     table['policyKind_id'].eq(policyKindId)]):
                                self.err2log(u'<b><font color=green>Добавляем</font></b>'
                                            u' новый полис %s №%s (%s) -> %s №%s (%s).' %
                                            (oldSerial,  oldNumber, oldInsurerId if oldInsurerId else 0, serial, number, insurerId if insurerId else 0))
                                self.addClientPolicy(clientId, insurerId, serial, number,  newBegDate,  newEndDate, policyKindId)
                                if oldEndDate.isNull():
                                    if newBegDate.addDays(-1) >= forceDate(record.value('begDate')):
                                        record.setValue('endDate', toVariant(newBegDate.addDays(-1)))
                                    else:
                                        record.setValue('endDate', toVariant(record.value('begDate')))
                                record.setValue('note', toVariant(u'Импорт ФЛК от {0}'.format(QDate.currentDate().toString('dd.MM.yyyy'))))
                                record.remove(record.indexOf('compulsoryServiceStop'))
                                record.remove(record.indexOf('voluntaryServiceStop'))
                                record.remove(record.indexOf('area'))
                                record.remove(record.indexOf('enp'))
                                self.db.updateRecord(self.tableClientPolicy, record)

                                msg.append(u'Добавлен'
                                        u' новый полис %s №%s (%s) -> %s №%s (%s).' %
                                        (oldSerial,  oldNumber, oldInsurerId if oldInsurerId else 0, serial, number, insurerId if insurerId else 0))
                        else:
                            if insurerId and insurerId != oldInsurerId:
                                record.setValue('insurer_id', toVariant(insurerId))
                            record.setValue('serial', toVariant(serial))
                            record.setValue('number',  toVariant(number))
                            record.setValue('policyKind_id', toVariant(policyKindId))
                            if oldBegDate.isNull():
                                record.setValue('begDate', toVariant(newBegDate))
                            if newEndDate:
                                record.setValue('endDate', toVariant(newEndDate))
                            else:
                                record.setValue('endDate', QVariant())
                            record.setValue('checkDate', toVariant(QDateTime().currentDateTime()))
                            record.setValue('note', toVariant(u'Импорт ФЛК от {0}'.format(QDate().currentDate().toString('dd.MM.yyyy'))))
                            record.remove(record.indexOf('compulsoryServiceStop'))
                            record.remove(record.indexOf('voluntaryServiceStop'))
                            record.remove(record.indexOf('area'))
                            record.remove(record.indexOf('enp'))
                            self.db.updateRecord(self.tableClientPolicy, record)
                            self.err2log(u'<b><font color=blue>Обновлен</font></b>'
                                        u' полис %s №%s (%s) -> %s №%s (%s).' %
                                        (oldSerial,  oldNumber, oldInsurerId if oldInsurerId else 0, serial, number, insurerId if insurerId else 0))

                        oldInsurerArea = forceString(self.db.translate('Organisation', 'id', oldInsurerId, 'area'))

                        if insurerArea and oldInsurerArea != insurerArea:
                            self.err2log(u'<b><font color=red>Изменилась территория страхования пациента: `%s` -> `%s` для счета `%s`</font>'
                                        % (oldInsurerArea, insurerArea, forceString(row.get('NS'))))
                            msg.append(u'Изменилась территория страхования пациента: `%s` -> `%s` для счета `%s`'
                                    % (oldInsurerArea, insurerArea, forceString(row.get('NS'))))
                            if self.accountNumber == forceString(row.get('NS')):
                                self.err2log(u'Территория изменилась для текущего счета')
                                msg.append(u'Территория изменилась для текущего счета')
                                self.deleteAccount = True
                else:
                    policyKindId = self.getPolicyKindByRegionalCode(forceString(row.get('SPVF')))
                    record = getClientPolicyEx(clientId, True, None)
                    if record:
                        oldInsurerId = forceInt(record.value('insurer_id'))
                        if (newInsurerOkato != '03000' and newInsurerOkato != ''
                                and self.findOKATObyOrg(oldInsurerId) == newInsurerOkato):
                            insurerId = oldInsurerId
                        
                    self.addClientPolicy(clientId, insurerId, serial, number, newBegDate, newEndDate, policyKindId)
                    if insurerId:
                        self.err2log(u'<b><font color=green>Добавляем</font></b>'u' новый полис %s №%s (%s).' % (serial, number, forceInt(insurerId)))
                        msg.append(u'Добавлен новый полис %s №%s (%s).' % (serial, number, insurerId))
                    else:
                        self.err2log(u'<b><font color=green>Добавляем</font></b>'u' новый полис %s №%s.' % (serial, forceInt(number)))
                        msg.append(u'Добавлен новый полис %s №%s.' % (serial, number))
            else:
                self.err2log(u'<b><font color=silver>Без изменений:</font></b> `%s`' % forceInt(clientId))
                msg.append(u'Без изменений `%s`' % clientId)

            if clientId and enp:
                record = getClientPolicyEx(clientId, True, QDate.fromString(row.get('DATO'), 'yyyy-MM-dd'), eventId)
                if not record:
                    record = getClientPolicyEx(clientId, True, None)
                if record:
                    oldENP = forceString(record.value('enp'))
                else:
                    oldENP = ''
                enp_system_id = self.db.translate('rbAccountingSystem', 'code', 'ENP', 'id')
                table = self.tableClientIdentification
                if oldENP != enp and not oldENP:
                    # если раньше ЕНП не было
                    # заносим ЕНП в ClientIdentification
                    enp_record = table.newRecord()
                    enp_record.setValue('createDatetime', QDate.fromString(row.get('DATO'), 'yyyy-MM-dd'))
                    enp_record.setValue('modifyDatetime', QDate.fromString(row.get('DATO'), 'yyyy-MM-dd'))
                    enp_record.setValue('deleted', toVariant(0))
                    enp_record.setValue('client_id', clientId)
                    enp_record.setValue('accountingSystem_id', toVariant(enp_system_id))
                    enp_record.setValue('identifier', toVariant(enp))
                    enp_record.setValue('checkDate', QDate.fromString(row.get('DATO'), 'yyyy-MM-dd'))
                    enp_record.setValue(
                        'note', toVariant(u'Импорт ФЛК от {0}'.format(QDate.currentDate().toString('dd.MM.yyyy')))
                    )
                    self.db.insertRecord(table, enp_record)
                    self.err2log(u'<b><font color=green>Добавляем</font></b>'u' новый ЕНП №%s.' % (forceInt(enp)))
                    msg.append(u'Добавлен новый ЕНП №%s.' % enp)
                elif oldENP != enp and oldENP:
                    # если данные ЕНП отличаются и раньше был другой ЕНП
                    # обновляем ЕНП в ClientIdentification
                    enp_record = self.db.getRecordEx(
                        table, '*',
                        [table['deleted'].eq(0), table['accountingSystem_id'].eq(enp_system_id),
                         table['client_id'].eq(clientId)]
                    )
                    if enp_record is not None:
                        enp_record.setValue('modifyDatetime', QDate.fromString(row.get('DATO'), 'yyyy-MM-dd'))
                        enp_record.setValue('identifier', toVariant(enp))
                        enp_record.setValue('checkDate', QDate.fromString(row.get('DATO'), 'yyyy-MM-dd'))
                        enp_record.setValue(
                            'note', toVariant(u'Импорт ФЛК от {0}'.format(QDate.currentDate().toString('dd.MM.yyyy')))
                        )
                        self.db.updateRecord(table, enp_record)
                        self.err2log(u'<b><font color=green>Обновляем</font></b>'u' информацию об ЕНП №%s.' % (forceInt(enp)))
                        msg.append(u'Обновлена информация об ЕНП №%s.' % enp)

            if clientId:
                # обработка соц статуса сво
                clientSvoSocStatusRow = getClientSvoSocStatus(clientId)
                self.processClientSvoSocStatus(msg, clientId, svoSocStatus, clientSvoSocStatusRow)

        else:
            self.err2log(u'<b><font color=silver>Пациент не найден:</font></b> `%s`' % forceInt(clientId))
            msg.append(u'Пациент не найден: `%s`' % forceInt(clientId))
            self.nNotFound += 1

        self.nProcessed += 1
        msgstr = u'<br/>'.join(msg)
        self.printdata.append([u'%s %s %s' % (lastName,  firstName,  patrName), msgstr])
    
    
    def processPolicyRow(self, row):
        lastName = nameCase(forceString(row['FIO']))
        firstName = nameCase(forceString(row['IMA']))
        patrName = nameCase(forceString(row['OTCH']))
        msg = []
        self.errorPrefix = u'Строка %d (%s %s %s): ' % (self.progressBar.value(), lastName,  firstName,  patrName)

        eventId = forceRef(row['SN'])
        serial = forceString(row['SPSF'])
        number = forceString(row['SPNF'])
        insurerOGRN = forceString(row['PL_OGRNF'])
        oldInsurerOGRN = forceString(row['PL_OGRN'])
        vs = forceString(row['VS'])
        prikMO = forceString(row['PRIK_MO'])
        Q_G = forceString(row['Q_G'])

        newInsurerOkato = forceString(row['OKATO_OMSF'])
        if newInsurerOkato != '03000' and newInsurerOkato != '':
            (insurerId, insurerArea) = self.findOrgByOKATO(newInsurerOkato)
        else:
            (insurerId, insurerArea) = self.findOrgByOGRN(insurerOGRN)

        if not eventId:
            self.err2log(u'отсутствует идентификатор пациента')
            msg.append(u'отсутствует идентификатор пациента')

        # если DATPS пустой, ищем по client_id, если заполненный - по event_id
        datPS = forceString(row['DATPS'])
        clientRecord = None
        if datPS:
            eventRecord = self.db.getRecord(self.tableEvent, '*', eventId)
            if eventRecord:
                if '2' in Q_G:
                    clientId = forceInt(eventRecord.value('relative_id'))
                else:
                    clientId = forceInt(eventRecord.value('client_id'))
                clientRecord = self.db.getRecord(self.tableClient, '*', clientId)
            else:
                self.err2log(u'<b><font color=red>Персональный счет не найден!:</font></b> `%d`' % eventId)
                msg.append(u'Персональный счет не найден!: `%d`' % eventId)
                self.nProcessed += 1
                return
        else:
            clientId = eventId
            clientRecord = self.db.getRecord(self.tableClient, '*', clientId)

        if clientRecord:
            if not insurerOGRN:
                self.err2log(u'отсутствует ОГРН плательщика')
                msg.append(u'отсутствует ОГРН плательщика')
                self.nProcessed += 1
                return

            if clientId and self.importType2013:
                newLastName = nameCase(forceString(row['FIOF']))
                newFirstName = nameCase(forceString(row['IMAF']))
                newPatrName = nameCase(forceString(row['OTCHF']))
                newSex = self.sexMap.get(forceString(row['POLF']), 0)
                newBirthDate = QDate(row['DATRF']) if row['DATRF'] else None
                newBegDate = QDate(row['DATNP']) if row['DATNP'] else None
                newEndDate = QDate(row['DATOP']) if row['DATOP'] else None
                newSnils = forceString(row['SNILSF']).replace('-', '').replace(' ', '')

                if self.updateClient(clientId, newLastName, newFirstName, newPatrName, newSex, newBirthDate, newSnils, clientRecord):
                    self.err2log(u'<b><font color=blue>Обновлены</font></b> личные данные клиента'
                                 u' %d.' % (clientId))
                    msg.append(u'Обновлены личные данные клиента'
                               u' %d.' % (clientId))

            if not insurerId and insurerOGRN:
                self.err2log(u'Страховая компания с ОГРН кодом `%s` не найдена.' % insurerOGRN)
                msg.append(u'Страховая компания с ОГРН кодом `%s` не найдена.' % insurerOGRN)
                self.nProcessed += 1
                return

            if clientId and number:
                record = getClientPolicyEx(clientId, True,  QDate(row['DATO']), eventId)

                if record:
                    oldSerial = forceString(record.value('serial'))
                    oldNumber = forceString(record.value('number'))
                    oldInsurerId = forceRef(record.value('insurer_id'))
                    oldBegDate = forceDate(record.value('begDate'))
                    oldEndDate = forceDate(record.value('endDate'))
                    policyKindId = self.defaultPolicyKindId
                    policyKindChanged = False

                    # если ОГРН совпадают, страховую оставляем туже
                    if oldInsurerOGRN == insurerOGRN and newInsurerOkato == '03000':
                        insurerId = oldInsurerId

                    if (newInsurerOkato != '03000' and newInsurerOkato != ''
                            and self.findOKATObyOrg(forceInt(record.value('insurer_id'))) == newInsurerOkato):
                        insurerId = oldInsurerId

                    if self.importType2013:
                        oldPolicyKindId = forceRef(record.value('policyKind_id'))
                        newPolicyKindId = self.getPolicyKindByRegionalCode(forceString(row['SPVF']))

                        if newPolicyKindId:
                            policyKindId = newPolicyKindId
                            policyKindChanged = newPolicyKindId != oldPolicyKindId

                    if oldSerial != serial or oldNumber != number \
                            or oldInsurerId != insurerId or policyKindChanged \
                            or oldBegDate != newBegDate or oldEndDate != newEndDate:

                        if oldBegDate and oldBegDate != newBegDate:
                            self.err2log(u'<b><font color=green>Добавляем</font></b>'
                                         u' новый полис %s №%s (%d) -> %s №%s (%d).' %
                                         (oldSerial,  oldNumber, oldInsurerId if oldInsurerId else 0, serial, number,  insurerId if insurerId else 0))
                            self.addClientPolicy(clientId, insurerId, serial, number,  newBegDate,  newEndDate, policyKindId)
                            if oldEndDate.isNull():
                                if newBegDate.addDays(-1) >= forceDate(record.value('begDate')):
                                    record.setValue('endDate', toVariant(newBegDate.addDays(-1)))
                                else:
                                    record.setValue('endDate', toVariant(record.value('begDate')))
                            record.setValue('note', toVariant(u'Импорт ФЛК от {0}'.format(QDate.currentDate().toString('dd.MM.yyyy'))))
                            record.remove(record.indexOf('compulsoryServiceStop'))
                            record.remove(record.indexOf('voluntaryServiceStop'))
                            record.remove(record.indexOf('area'))
                            self.db.updateRecord(self.tableClientPolicy, record)

                            msg.append(u'Добавлен'
                                       u' новый полис %s №%s (%d) -> %s №%s (%d).' %
                                       (oldSerial,  oldNumber, oldInsurerId if oldInsurerId else 0, serial, number, insurerId if insurerId else 0))
                        else:
                            if insurerId and insurerId != oldInsurerId:
                                record.setValue('insurer_id', toVariant(insurerId))
                            record.setValue('serial', toVariant(serial))
                            record.setValue('number',  toVariant(number))
                            record.setValue('policyKind_id', toVariant(policyKindId))
                            if oldBegDate.isNull():
                                record.setValue('begDate', toVariant(newBegDate))
                            if newEndDate:
                                record.setValue('endDate', toVariant(newEndDate))
                            else:
                                record.setValue('endDate', QVariant())
                            record.setValue('checkDate', toVariant(QDateTime().currentDateTime()))
                            record.setValue('note', toVariant(u'Импорт ФЛК от {0}'.format(QDate().currentDate().toString('dd.MM.yyyy'))))
                            record.remove(record.indexOf('compulsoryServiceStop'))
                            record.remove(record.indexOf('voluntaryServiceStop'))
                            record.remove(record.indexOf('area'))
                            self.db.updateRecord(self.tableClientPolicy, record)
                            self.err2log(u'<b><font color=blue>Обновлен</font></b>'
                                         u' полис %s №%s (%d) -> %s №%s (%d).' %
                                         (oldSerial,  oldNumber, oldInsurerId if oldInsurerId else 0, serial, number, insurerId if insurerId else 0))
                                             
                        oldInsurerArea = forceString(self.db.translate('Organisation', 'id', oldInsurerId, 'area'))

                        if insurerArea and oldInsurerArea != insurerArea:
                            self.err2log(u'<b><font color=red>Изменилась территория страхования пациента: `%s` -> `%s` для счета `%s`</font>'
                                         % (oldInsurerArea, insurerArea, forceString(row['NS'])))
                            msg.append(u'Изменилась территория страхования пациента: `%s` -> `%s` для счета `%s`'
                                       % (oldInsurerArea, insurerArea, forceString(row['NS'])))
                            if self.accountNumber == forceString(row['NS']):
                                self.err2log(u'Территория изменилась для текущего счета')
                                msg.append(u'Территория изменилась для текущего счета')
                                self.deleteAccount = True
                    else:
                        msg.append(u'Без изменений')
                else:
                    policyKindId = self.getPolicyKindByRegionalCode(forceString(row['SPVF']))
                    record = getClientPolicyEx(clientId, True, None)
                    if record:
                        oldInsurerId = forceInt(record.value('insurer_id'))
                        if (newInsurerOkato != '03000' and newInsurerOkato != ''
                                and self.findOKATObyOrg(oldInsurerId) == newInsurerOkato):
                            insurerId = oldInsurerId
                        
                    self.addClientPolicy(clientId, insurerId, serial, number, newBegDate, newEndDate, policyKindId)
                    if insurerId:
                        self.err2log(u'<b><font color=green>Добавляем</font></b>'u' новый полис %s №%s (%d).' % (serial, number, insurerId))
                        msg.append(u'Добавлен новый полис %s №%s (%d).' % (serial, number, insurerId))
                    else:
                        self.err2log(u'<b><font color=green>Добавляем</font></b>'u' новый полис %s №%s.' % (serial, number))
                        msg.append(u'Добавлен новый полис %s №%s.' % (serial, number))
            else:
                self.err2log(u'<b><font color=silver>Без изменений:</font></b> `%d`' % clientId)
                msg.append(u'Без изменений `%d`' % clientId)
        else:
            self.err2log(u'<b><font color=silver>Пациент не найден:</font></b> `%d`' % clientId)
            msg.append(u'Пациент не найден: `%d`' % clientId)

        self.nProcessed += 1
        msgstr = u'<br/>'.join(msg)
        self.printdata.append([u'%s %s %s' % (lastName,  firstName,  patrName), msgstr])

    # def findOrgByInfis(self, infis):
    #     u"""Возвращает id и область страховой."""
    #     if not infis:
    #         return (None, None)
    #
    #     result = self.orgCache.get(infis, -1)
    #
    #     if result == -1:
    #         result = (None, None)
    #         table = self.db.table('Organisation')
    #         record = self.db.getRecordEx(table, 'id, area', [table['deleted'].eq(0),
    #                                      table['infisCode'].eq(infis)], 'id')
    #
    #         if record:
    #             result = (forceRef(record.value(0)), forceString(record.value(1)))
    #             self.orgCache[infis] = result
    #
    #     return result

    def findOrgByOGRN(self, ogrn):
        u"""Возвращает id и область страховой."""
        if not ogrn:
            return None, None
        result = self.orgCache.get(ogrn, -1)
        if result == -1:
            result = (None, None)
            table = self.db.table('Organisation')
            record = self.db.getRecordEx(table, 'id', [table['deleted'].eq(0),
                                         table['OGRN'].eq(ogrn),
                                         table['isInsurer'].eq(1),
                                         table['head_id'].isNull(),
                                         table['area'].eq('2300000000000'),
                                         table['isActive'].eq(1)], 'id')
            if record:
                result = (forceRef(record.value(0)), '2300000000000')
                self.orgCache[ogrn] = result
        return result

    def findOrgByOKATO(self, okato):
        u"""Возвращает id и область страховой."""
        if not okato:
            return None, None
        result = self.orgInoCache.get(okato, -1)
        if result == -1:
            result = (None, None)
            table = self.db.table('Organisation')
            record = self.db.getRecordEx(table, 'id, area',  [table['deleted'].eq(0),
                                                              table['OKATO'].eq(okato),
                                                              table['isActive'].eq(1),
                                                              table['isInsurer'].eq(1),
                                                              table['head_id'].isNull()], 'id')
            if record:
                result = (forceRef(record.value(0)), forceString(record.value(1)))
                self.orgInoCache[okato] = result
        return result

    def findOKATObyOrg(self, orgId):
        u"""Возвращает окато страховой."""
        if not orgId:
            return None

        result = self.orgInoOkatoCache.get(orgId,  -1)
        if result == -1:
            result = None
            table = self.db.table('Organisation')
            record = self.db.getRecordEx(table,
                                         'okato',
                                         [table['deleted'].eq(0), table['id'].eq(orgId),
                                          table['isActive'].eq(1), table['isInsurer'].eq(1),
                                          table['head_id'].isNull()],
                                         'okato'
                                         )

            if record:
                result = forceString(record.value(0))
                self.orgInoOkatoCache[orgId] = result

        return result

    def getPolicyKindByRegionalCode(self, regionalCode):
        result = self.policyKindCache.get(regionalCode, -1)

        if result == -1:
            result = forceRef(self.db.translate('rbPolicyKind', 'regionalCode', regionalCode, 'id'))
            self.policyKindCache[regionalCode] = result

        return result

    def addClientPolicy(self, clientId, insurerId, serial, number,  begDate,  endDate, policyKindId=None):
        record = self.tableClientPolicy.newRecord()
        record.setValue('client_id', toVariant(clientId))
        record.setValue('insurer_id', toVariant(insurerId))
        record.setValue('policyType_id', toVariant(self.policyTypeId))
        record.setValue('policyKind_id', toVariant(policyKindId))
        if begDate:
            record.setValue('begDate', toVariant(begDate))
            if endDate:
                record.setValue('endDate', toVariant(endDate))
            else:
                record.setValue('endDate', QVariant())
        record.setValue('checkDate', toVariant(QDateTime().currentDateTime()))
        record.setValue('serial', toVariant(serial))
        record.setValue('number', toVariant(number))
        record.setValue('note', toVariant(u'Импорт ФЛК от {0}'.format(QDate().currentDate().toString('dd.MM.yyyy'))))
        self.db.insertRecord(self.tableClientPolicy, record)

    def updateClient(self, clientId, lastName, firstName, patrName, sex, birthDate, snils, clientRecord):
        dirty = False
        if lastName and forceString(clientRecord.value('lastName')) != lastName:
            clientRecord.setValue('lastName', toVariant(lastName))
            dirty = True

        if firstName and forceString(clientRecord.value('firstName')) != firstName:
            clientRecord.setValue('firstName', toVariant(firstName))
            dirty = True

        if lastName and forceString(clientRecord.value('patrName')) != patrName:
            # это не ошибка, если меняются данные пациента, то фонд возвращает корректные ФИО, и отчество может быть пустым
            # поэтому надо его очищать в базе
            clientRecord.setValue('patrName', toVariant(patrName))
            dirty = True

        if birthDate and birthDate.isValid() and forceDate(clientRecord.value('birthDate')) != birthDate:
            clientRecord.setValue('birthDate', toVariant(birthDate))
            dirty = True

        if sex and sex != 0 and forceInt(clientRecord.value('sex')) != sex:
            clientRecord.setValue('sex', toVariant(sex))
            dirty = True

        if snils and forceString(clientRecord.value('SNILS')) != snils:
            clientRecord.setValue('SNILS', toVariant(snils))
            dirty = True

        if dirty:
            tableClientHistory = self.db.table('Client_History')
            historyRecord = tableClientHistory.newRecord()
            historyRecord.setValue('master_id', clientRecord.value('id'))
            historyRecord.setValue('lastName', clientRecord.value('lastName'))
            historyRecord.setValue('firstName', clientRecord.value('firstName'))
            historyRecord.setValue('patrName', clientRecord.value('patrName'))
            historyRecord.setValue('birthDate', clientRecord.value('birthDate'))
            historyRecord.setValue('birthTime', clientRecord.value('birthTime'))
            historyRecord.setValue('sex', clientRecord.value('sex'))
            historyRecord.setValue('SNILS', clientRecord.value('SNILS'))
            historyRecord.setValue('deathDate', clientRecord.value('deathDate'))

            self.db.updateRecord(self.tableClient, clientRecord)
            self.db.insertRecord(tableClientHistory, historyRecord)

        return dirty

    def processClientSvoSocStatus(self, msg, clientId, flkSocStatus, clientSvoSocStatusRow):

        def checkSocStatusTypeClassAssoc(statusCode, svoClassId):
            # проверка, есть ли в rbSocStatusType тип соц статуса с кодом statusCode
            # с проставленной связью c классом svo
            tableAssoc = self.db.table('rbSocStatusClassTypeAssoc')
            tableType = self.db.table('rbSocStatusType')
            table = tableType.leftJoin(tableAssoc, tableType['id'].eq(tableAssoc['type_id']))
            if self.db.getRecordEx(
                table, '*',
                [
                    tableType['code'].eq(statusCode),
                    tableAssoc['class_id'].eq(svoClassId)
                ]
            ):
                return True
            else:
                return False

        socStatusSvoClassId = forceInt(self.db.translate('rbSocStatusClass', 'code', 'svo', 'id'))
        tableSocStatus = self.db.table('ClientSocStatus')

        if flkSocStatus != '000':
            # если код соц статуса не 000, то проверим, есть ли он в rbSocStatusType и связан ли с классом svo
            # checkAssocOk = checkSocStatusTypeClassAssoc(flkSocStatus, socStatusSvoClassId)

            if not checkSocStatusTypeClassAssoc(flkSocStatus, socStatusSvoClassId):
                # если код соц статуса не занесён в rbSocStatusType,
                # то создаём с названием 'отсутствующая запись справочника "Социальная категория"'
                tableSocStatusType = self.db.table('rbSocStatusType')
                socStatusTypeRecord = tableSocStatusType.newRecord()
                socStatusTypeRecord.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                socStatusTypeRecord.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
                socStatusTypeRecord.setValue('code', toVariant(flkSocStatus))
                socStatusTypeRecord.setValue('name', toVariant(u'отсутствующая запись справочника "Социальная категория"'))
                socStatusTypeRecord.setValue('shortName', toVariant(''))
                socStatusTypeRecord.setValue('socCode', toVariant(''))
                socStatusTypeRecord.setValue('regionalCode', toVariant(flkSocStatus))
                self.db.insertRecord(tableSocStatusType, socStatusTypeRecord)

                insertedTypeId = forceInt(socStatusTypeRecord.value('id'))

                # и относим к классу соц статуса с кодом svo
                tableSocStatusClassTypeAssoc = self.db.table('rbSocStatusClassTypeAssoc')
                socStatusClassTypeAssocRecord = tableSocStatusClassTypeAssoc.newRecord()
                socStatusClassTypeAssocRecord.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                socStatusClassTypeAssocRecord.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
                socStatusClassTypeAssocRecord.setValue('class_id', toVariant(socStatusSvoClassId))
                socStatusClassTypeAssocRecord.setValue('type_id', toVariant(insertedTypeId))
                self.db.insertRecord(tableSocStatusClassTypeAssoc, socStatusClassTypeAssocRecord)

                self.err2log(u'<b><font color=green>Добавляем в справочник "Социальный статус: типы"</font></b>'u' соц статус %s - %s.' % (flkSocStatus, u'отсутствующая запись справочника "Социальная категория"'))
                msg.append(u'Добавлен в справочник соц статус %s - %s.' % (flkSocStatus, u'отсутствующая запись справочника "Социальная категория"'))

        if clientSvoSocStatusRow:
            # если у пациента уже был соц статус по классу svo, то определяем его код
            curSvoSocStatusId = forceRef(clientSvoSocStatusRow.value('socStatusType_id'))
            curSvoSocStatusCode = forceStringEx(self.db.translate('rbSocStatusType', 'id', curSvoSocStatusId, 'code'))
        else:
            curSvoSocStatusCode = None

        if clientSvoSocStatusRow and flkSocStatus == '000':
            # если у пациента уже был соц статус по классу svo, а от флк пришёл соц статус 000 - помечаем его удалённым

            clientSvoSocStatusRow.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
            clientSvoSocStatusRow.setValue('deleted', toVariant(1))
            self.db.updateRecord(tableSocStatus, clientSvoSocStatusRow)
            self.err2log(u'<b><font color=green>Удаляем</font></b>'u' соц статус %s.' % curSvoSocStatusCode)
            msg.append(u'Удалён соц статус %s.' % curSvoSocStatusCode)

        elif flkSocStatus != '000' and not clientSvoSocStatusRow:
            # если у пациента не было соц статуса по классу svo, а от флк пришёл код соц статуса - создаём новый с кодом из флк

            socStatusRecord = tableSocStatus.newRecord()
            socStatusRecord.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
            socStatusRecord.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
            socStatusRecord.setValue('deleted', toVariant(0))
            socStatusRecord.setValue('client_id', toVariant(clientId))
            socStatusRecord.setValue('socStatusClass_id', toVariant(socStatusSvoClassId))
            socStatusRecord.setValue('socStatusType_id', toVariant(
                forceInt(self.db.translate('rbSocStatusType', 'code', flkSocStatus, 'id'))))
            socStatusRecord.setValue('begDate', toVariant(QDate(0, 0, 0)))
            socStatusRecord.setValue('note', toVariant(''))

            self.db.insertRecord(tableSocStatus, socStatusRecord)
            self.err2log(u'<b><font color=green>Добавляем</font></b>'u' соц статус %s.' % flkSocStatus)
            msg.append(u'Добавлен соц статус %s.' % flkSocStatus)

        elif flkSocStatus != '000' and flkSocStatus != curSvoSocStatusCode:
            # если у пациента уже был соц статус по классу svo,
            # а от флк пришёл иной код соц статуса - помечаем старый удалённым и создаём новый с кодом из флк
            clientSvoSocStatusRow.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
            clientSvoSocStatusRow.setValue('deleted', toVariant(1))
            self.db.updateRecord(tableSocStatus, clientSvoSocStatusRow)

            socStatusRecord = tableSocStatus.newRecord()
            socStatusRecord.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
            socStatusRecord.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
            socStatusRecord.setValue('deleted', toVariant(0))
            socStatusRecord.setValue('client_id', toVariant(clientId))
            socStatusRecord.setValue('socStatusClass_id', toVariant(socStatusSvoClassId))
            socStatusRecord.setValue('socStatusType_id', toVariant(
                forceInt(self.db.translate('rbSocStatusType', 'code', flkSocStatus, 'id'))))
            socStatusRecord.setValue('begDate', toVariant(QDate(0, 0, 0)))
            socStatusRecord.setValue('note', toVariant(''))

            self.db.insertRecord(tableSocStatus, socStatusRecord)
            self.err2log(u'<b><font color=green>Меняем</font></b>'u' соц статус с %s на %s.' % (
                curSvoSocStatusCode, flkSocStatus
            ))
            msg.append(u'Изменён соц статус с %s на %s.' % (curSvoSocStatusCode, flkSocStatus))


    @pyqtSignature('int')
    def on_tabImportType_currentChanged(self, index):
        self.importFLK = index == 1
        self.isPreControl = index == 2


    # def updateRKEY(self, eventId, typeFile, rowId, RKEY, altRowId=None):
    #     db = QtGui.qApp.db
    #
    #     if altRowId:
    #         cond = "account_id = {0} and typeFile = '{1}' and alt_row_id = '{2}'".format(self.accountId, typeFile, altRowId)
    #     else:
    #         cond = "account_id = {0} and event_id = {1} and typeFile = '{2}' and row_id = {3}".format(self.accountId, eventId, typeFile, rowId)
    #
    #     keyRec = db.getRecordEx('soc_Account_RowKeys', '*', where=cond)
    #
    #     if not keyRec:
    #         keyRec = db.table('soc_Account_RowKeys').newRecord()
    #         keyRec.setValue('account_id', toVariant(self.accountId))
    #         keyRec.setValue('event_id', toVariant(eventId))
    #         keyRec.setValue('typeFile', toVariant(typeFile))
    #         keyRec.setValue('row_id', toVariant(rowId))
    #         keyRec.setValue('alt_row_id', toVariant(altRowId))
    #
    #     keyRec.setValue('key', toVariant(RKEY))
    #
    #     db.insertOrUpdate('soc_Account_RowKeys', keyRec)