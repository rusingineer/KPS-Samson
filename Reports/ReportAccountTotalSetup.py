# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import os.path
import shutil
import datetime
import hashlib
from zipfile import ZIP_DEFLATED, ZipFile
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, pyqtSignature, QVariant, QAbstractTableModel, QDateTime, SIGNAL

from Accounting.Utils import roundMath
from Reports.ReportView import CReportViewDialog
from library.AmountToWords import amountToWords
from library.DialogBase import CDialogBase
from library.Identification import getIdentification
from library.TableModel import CCol
from library.dbfpy.dbf import Dbf
from library.Utils import calcAgeInDays, forceBool, forceDate, forceDouble, forceInt, forceRef, forceString, \
    forceStringEx, formatSex, nameCase, pyDate, toVariant, formatSNILS, trim, formatName, formatDate

from Events.Action import CAction
from Exchange.Export import CExportHelperMixin, CAbstractExportPage1, CAbstractExportPage2, CAbstractExportWizard
from Reports.ReportBase import CReportBase, createTable

from Exchange.Ui_ExportR23NativePage1 import Ui_ExportR23NativePage1
from Exchange.Ui_ExportR23NativePage2 import Ui_ExportR23NativePage2
from Exchange.Ui_ExportR23NoKeysDialog import Ui_ExportR23NoKeysDialog

N008dict = {u'Эпителиальный': 1, u'Неэпителиальный': 2, u'Светлоклеточный': 3,
            u'Несветлоклеточный': 4, u'Низкодифференцированная': 5,
            u'Умереннодифференцированная': 6, u'Высокодифференцированная': 7,
            u'Не определена': 8, u'Мелкоклеточный': 9, u'Немелкоклеточный': 10,
            u'Почечноклеточный': 11, u'Не почечноклеточный': 12,
            u'Папиллярный': 13, u'Фолликулярный': 14, u'Гюртклеточный': 15,
            u'Медуллярный': 16, u'Анапластический': 17, u'Базальноклеточный': 18,
            u'Не базальноклеточный': 19, u'Плоскоклеточный': 20, u'Не плоскоклеточный': 21,
            u'Эндометриоидные': 22, u'Не эндометриоидные': 23, u'Аденокарцинома': 24, u'Не аденокарцинома': 25}

N011dict = {u'Наличие мутаций в гене BRAF': 4, u'Отсутствие мутаций в гене BRAF': 5,
            u'Наличие мутаций в гене c-Kit': 6, u'Отсутствие мутаций в гене c-Kit': 7,
            u'Исследование не проводилось': 8, u'Наличие мутаций в гене RAS': 9,
            u'Отсутствие мутаций в гене RAS': 10, u'Наличие мутаций в гене EGFR': 11,
            u'Отсутствие мутаций в гене EGFR': 12, u'Наличие транслокации в генах ALK или ROS1': 13,
            u'Отсутствие транслокации в генах ALK и ROS1': 14, u'Повышенная экспрессия белка PD-L1': 15,
            u'Отсутствие повышенной экспрессии белка PD-L1': 16, u'Наличие рецепторов к эстрогенам': 17,
            u'Отсутствие рецепторов к эстрогенам': 18, u'Наличие рецепторов к прогестерону': 19,
            u'Отсутствие рецепторов к прогестерону': 20, u'Высокий индекс пролиферативной активности экспрессии Ki-67': 21,
            u'Низкий индекс пролиферативной активности экспрессии Ki-67': 22, u'Гиперэкспрессия белка HER2': 23,
            u'Отсутствие гиперэкспрессии белка HER2': 24, u'Наличие мутаций в генах BRCA': 25, u'Отсутствие мутаций в генах BRCA': 26}


def makeReportAccountTotal(widget, accountId, accountItemIdList, accountIdList=[]):
    invoiceClass = CInvoice()
    for accountId in accountIdList:
        wizard = CExportWizard(accountId=accountId, parent=widget, invoiceClass=invoiceClass)
        wizard.setAccountId(accountId)
        wizard.setAccountItemsIdList(accountItemIdList)
        wizard.setSelectedAccounts(accountIdList)
        wizard.exec_()

    return invoiceClass


def updateInternalHash(fileType, keyField, recordList, dats, fieldList, altKeyField=None):
     if len(recordList):
        strValuesList = []
        for rec in recordList:
            stringKey = dats + ''.join([forceString(rec[fld]) for fld in fieldList])
            hashKey = hashlib.sha1(stringKey.encode('utf-8')).hexdigest()
            snils = 'NULL'
            if fileType == 'D':
                sn = 'NULL'
                altKeyFieldValue = "'" + hashKey + "'"
                keyFieldValue = 'NULL'
                snils = "'" + forceString(rec['SNILS']) + "'"
            else:
                sn = forceString(rec['SN'])
                keyFieldValue = (forceString(rec[keyField]) if not altKeyField else 'NULL')
                if fileType in ['P', 'U']:
                    snils = "'" + forceString(rec['DOC_SS']) + "'"
                altKeyFieldValue = ("'" + (forceString(rec[altKeyField]) + "'") if altKeyField else 'NULL')
            rkey = ("'" + forceString(rec['RKEY']) + "'") if forceString(rec['RKEY']) else 'NULL'
            strValuesList.append(u"({0}, '{1}', {2}, {3}, '{4}', {5}, {6})".format(sn,
                                                                   fileType,
                                                                   keyFieldValue,
                                                                   altKeyFieldValue,
                                                                   hashKey,
                                                                   rkey,
                                                                   snils))
        QtGui.qApp.db.query(u"insert into tmp_internalKeys(event_id, typeFile, row_id, alt_row_id, internalKey, RKEY, SNILS) values {0}".format(','.join(strValuesList)))
# ******************************************************************************
def updateInternalHashFLK(recordList, fieldList):
    if len(recordList):
        strValuesList = []
        for rec in recordList:
            valueList = []
            for (fld1, fld2) in fieldList:
                value = forceString(rec[fld1]) if forceString(rec[fld1]) else forceString(rec[fld2])
                if fld1 in ['POL', 'DATR'] and '2' in forceString(rec['Q_G']):
                    value = forceString(rec['POLP']) if fld1 == 'POL' else forceString(rec['DATRP'])
                valueList.append(value)
            stringKey = ''.join(valueList)
            hashKey = hashlib.sha1(stringKey.encode('utf-8')).hexdigest()
            sn = forceString(rec['SN'])
            fkey = ("'" + forceString(rec['FKEY']) + "'") if forceString(rec['FKEY']) else 'NULL'
            strValuesList.append(u"({0}, 'F', '{1}', {2})".format(sn, hashKey, fkey))
        QtGui.qApp.db.query(u"insert into tmp_internalKeysFLK(event_id, typeFile, internalKey, FKEY) values {0}".format(','.join(strValuesList)))


class CExportWizard(CAbstractExportWizard):
    def __init__(self, accountId, invoiceClass, parent=None):
        title = u'Мастер экспорта в ОМС Краснодарского края'
        CAbstractExportWizard.__init__(self, parent, title)
        self.invoice = None
        self.page1 = CExportPage1(self, accountId, invoiceClass)

        if parent.tabWorkType.currentIndex() == 0:  # закладка Расчет
            self.orgStructId = parent.cmbCalcOrgStructure.value()
        else:
            self.orgStructId = parent.cmbAnalysisOrgStructure.value()

        self.addPage(self.page1)

    def exec_(self):
        self.page1.export()
        self.cleanup()

    def getTmpDir(self):
        return CAbstractExportWizard.getTmpDir(self)

    def getInvoice(self):
        return self.invoice

    def getAccountInfo(self, accountId):
        u"""Возвращает словарь с данными о счете по его идентификатору"""
        result = {}
        record = self.db.getRecord('Account', 'id, date, number, exposeDate, '
                                   'contract_id, payer_id, settleDate, personalDate, note, sum, '
                                   'orgStructure_id, type_id', accountId)

        if record:
            result['accDate'] = forceDate(record.value('date'))
            result['exposeDate'] = forceDate(record.value('exposeDate'))
            result['accNumber'] = forceString(record.value('number'))
            result['contractId'] = forceRef(record.value('contract_id'))
            result['payerId'] = forceRef(record.value('payer_id'))
            result['settleDate'] = forceDate(record.value('settleDate'))
            result['personalDate'] = forceDate(record.value('personalDate'))
            result['note'] = forceString(record.value('note'))
            result['accSum'] = forceDouble(record.value('sum'))
            result['accId'] = forceRef(record.value('id'))
            result['accTypeId'] = forceRef(record.value('type_id'))
            accOrgStructureId = forceRef(record.value('orgStructure_id'))
            result['accOrgStructureId'] = accOrgStructureId
            result['oms_code'] = forceString(self.db.translate('OrgStructure', 'id', accOrgStructureId, 'bookkeeperCode'))
            result['isFAP'] = forceBool(self.db.translate('OrgStructure', 'id', accOrgStructureId, 'isFAP'))
            result['payerCode'] = forceString(self.db.translate('Organisation', 'id', result['payerId'], 'infisCode'))
        return result

    def setSelectedAccounts(self, selectedAccountIds):
        self.page1.selectedAccountIds = selectedAccountIds
        for accountId in selectedAccountIds:
            self.page1.mapAccountInfo[accountId] = self.getAccountInfo(accountId)
        if len(selectedAccountIds) > 1:
            self.page1.setTitle(u'Экспорт данных реестра по выбранным {0} счетам'.format(len(selectedAccountIds)))
            self.page1.edtRegistryNumber.setValue(0)
            self.page1.edtRegistryNumber.setEnabled(False)
        else:
            self.page1.mapAccountInfo[self.accountId] = self.getAccountInfo(self.accountId)
            date = self.page1.mapAccountInfo[self.accountId].get('accDate', QDate())
            number = self.page1.mapAccountInfo[self.accountId].get('accNumber', '')
            strNumber = number if trim(number) else u'б/н'
            strDate = forceString(date) if date else u'б/д'
            self.page1.setTitle(u'Экспорт данных реестра по счёту №%s от %s' % (strNumber, strDate))
            try:
                self.page1.edtRegistryNumber.setValue(forceInt(self.info.get('accNumber')))
            except:
                self.page1.edtRegistryNumber.setValue(forceInt(self.info.get('iaccNumber')))

    def setAccountExposeDate(self):
        if self.page1.exportType in [self.page1.exportTypeP25]:
            for accountId in self.page1.selectedAccountIds:
                self.page1.accInfo = self.page1.mapAccountInfo[accountId]
                accountRecord = self.db.getRecord('Account', '*', accountId)
                accountRecord.setValue('id', toVariant(accountId))
                accountRecord.setValue('exposeDate', toVariant(QDate().currentDate()))
                if self.page1.edtRegistryNumber.isEnabled():
                    accountRecord.setValue('number', toVariant(self.page1.edtRegistryNumber.value()))
                    accountRecord.setValue('note', toVariant(self.page1.accInfo.get('note', self.page1.accInfo.get('oldNumber'))))
                accountRecord.setValue('exportedName', toVariant(self.page1.getZipFileName()[:15]))
                self.db.updateRecord('Account', accountRecord)


class CExportPage1(CAbstractExportPage1, Ui_ExportR23NativePage1, CExportHelperMixin):
    exportTypeP25 = 0  # Положение 23
    exportTypePreControlP25 = 1  # предварительный контроль счетов
    exportTypeFLK = 2  # ФЛК реестров
    exportTypeAttachments = 3  # Прикрепленное население
    exportTypeInvoice = 4  # Файлы "Счёт" из реестров
    exportTypeList = [u'Положение 23', u'Предварительный контроль счетов',
                      u'ФЛК реестров', u'Прикрепленное население', u'Файлы "Счёт" из реестров']
    fieldListKeyP = ['SN', 'CODE_MO', 'PL_OGRN', 'FIO', 'IMA', 'OTCH', 'POL', 'DATR', 'KAT', 'SNILS', 'OKATO_OMS',
                     'SPV', 'SPS', 'SPN', 'INV', 'MSE', 'Q_G', 'NOVOR', 'VNOV_D', 'FAMP', 'IMP', 'OTP', 'POLP', 'DATRP',
                     'C_DOC', 'S_DOC', 'N_DOC', 'NAPR_MO', 'NAPR_N', 'NAPR_D', 'NAPR_DP', 'TAL_N', 'TAL_D', 'PR_D_N',
                     'PR_DS_N', 'DATN', 'DATO', 'ISHOB', 'ISHL', 'MP', 'DOC_SS', 'SPEC', 'PROFIL', 'MKBX', 'MKBXS',
                     'DS_ONK', 'MKBX_PR', 'VMP', 'KSO', 'P_CEL', 'VB_P']

    fieldListKeyU = ['UID', 'CODE_MO', 'SN', 'ISTI', 'P_PER', 'KOTD', 'KPK', 'MKBX', 'MKBXS', 'MKBXS_PR', 'PR_MS_N',
                     'MKBXO', 'C_ZAB', 'VP', 'KRIT', 'KRIT2', 'KSLP', 'KSLP_IT', 'KUSL', 'KOLU', 'KD', 'DATN', 'DATO',
                     'TARU', 'SUMM', 'IS_OUT', 'OUT_MO',
                     'DOC_SS', 'SPEC', 'PROFIL', 'VMP', 'DS_ONK',
                     'USL_TIP', 'HIR_TIP', 'LEK_TIPL', 'LEK_TIPV', 'LUCH_TIP']

    fieldListKeyD = ['CODE_MO', 'SNILS', 'FIO', 'IMA', 'OTCH', 'POL', 'DATR', 'DATN', 'DATO']
    fieldListKeyD202005 = ['CODE_MO', 'SNILS', 'FIO', 'IMA', 'OTCH', 'POL', 'DATR']

    fieldListKeyN = ['CODE_MO', 'SN', 'NAPR_N', 'NAPR_MO', 'NAPR_D', 'DOC_SS']

    fieldListKeyR = ['RID', 'CODE_MO', 'SN', 'UID', 'NAZR_D', 'NAPR_MO', 'NAZR', 'SPEC', 'VID_OBS', 'PROFIL', 'KPK', 'NAPR_USL']

    fieldListKeyO = ['OID', 'CODE_MO', 'SN', 'UID', 'DS1_T', 'PR_CONS', 'D_CONS', 'STAD', 'ONK_T', 'ONK_N', 'ONK_M', 'MTSTZ',
                     'SOD', 'REGNUM', 'CODE_SH', 'DATE_INJ', 'PPTR', 'k_FR', 'WEI', 'HEI', 'BSA']

    fieldListKeyI = ['IID', 'CODE_MO', 'SN', 'UID', 'DIAG_D', 'DIAG_TIP', 'DIAG_CODE', 'DIAG_RSLT']

    fieldListKeyC = ['CID', 'CODE_MO', 'SN', 'OID', 'PROT', 'D_PROT']

    fieldListKeyFLK = [('CODE_MO', 'CODE_MO'), ('PL_OGRN', 'PL_OGRN'), ('FIO', 'FIO'), ('IMA', 'IMA'), ('OTCH', 'OTCH'),
                       ('DATR', 'DATR'), ('POL', 'POL'), ('SNILS', 'SNILS'), ('C_DOC', 'C_DOC'), ('S_DOC', 'S_DOC'), ('N_DOC', 'N_DOC'),
                       ('DATN', 'DATN'), ('DATO', 'DATO'), ('SPV', 'SPV'), ('SPS', 'SPS'), ('SPN', 'SPN'), ('OKATO_OMS', 'OKATO_OMS')]
    fieldListKeyFLKImport = [('CODE_MO', 'CODE_MO'), ('PL_OGRNF', 'PL_OGRN'), ('FIOF', 'FIO'), ('IMAF', 'IMA'), ('OTCHF', 'OTCH'),
                       ('DATRF', 'DATR'), ('POLF', 'POL'), ('SNILSF', 'SNILS'), ('C_DOC', 'C_DOC'), ('S_DOC', 'S_DOC'), ('N_DOC', 'N_DOC'),
                       ('DATN', 'DATN'), ('DATO', 'DATO'), ('SPVF', 'SPV'), ('SPSF', 'SPSF'), ('SPNF', 'SPN'), ('OKATO_OMSF', 'OKATO_OMS')]

    def __init__(self, parent, accountId, invoiceClass):
        CAbstractExportPage1.__init__(self, parent)
        CExportHelperMixin.__init__(self)
        self.parent = parent
        self.accountId = accountId
        self.invoice = None
        self.invoiceClass = invoiceClass
        self.lblExportType.setVisible(False)
        self.lblRegistryNumber.setVisible(False)
        self.cmbExportType.setVisible(False)
        self.edtRegistryNumber.setVisible(False)
        self.chkIgnoreErrors.setVisible(False)
        self.chkMakeInvoice.setVisible(False)
        self.chkVerboseLog.setVisible(False)
        self.selectedAccountIds = []
        self.currentAccountId = None
        self.mapAccountInfo = {}
        self.tariffCache = {}
        self.prefix = 'ExportR23Native'
        self.cmbExportType.clear()
        self.noKeysDict = {}
        self.noKeysFLKDict = {}
        self.noKeysSNILS = set()
        self.cmbExportType.setMaxCount(len(self.exportTypeList))
        for exportType in self.exportTypeList:
            self.cmbExportType.addItem(exportType)

        prefs = QtGui.qApp.preferences.appPrefs
        self.ignoreErrors = forceBool(prefs.get('%sIgnoreErrors' % self.prefix, False))
        self.chkVerboseLog.setChecked(forceBool(prefs.get('%sVerboseLog' % self.prefix, False)))
        self.cmbExportType.setCurrentIndex(forceInt(prefs.get('%sExportType' % self.prefix, 0)))
        self.chkIgnoreErrors.setChecked(self.ignoreErrors)

        self.exportedTempInvalidList = []
        self.tempInvalidCache = {}
        self.exportedEvents = set()
        self.DS_ONKSet = set()
        self.exportedOnkoInfo = set()
        self.exportedOnkoInfoI = set()
        self.exportedOnkoInfoC = set()
        self.exportedAppointments = set()
        self.exportedHospitalDirection = set()
        self.uetDict = {}
        self.modernClients = set()
        self.exportType = self.exportTypeInvoice
        self.serviceNum = 0
        self.dbfFileName = {}

        self.chkMakeInvoice.setEnabled(False)
        self.chkMakeInvoice.setChecked(True)
        self.edtRegistryNumber.setEnabled(False)

        if hasattr(self, 'progressBarAccount'):
            self.progressBarAccount.setMinimum(0)
            self.progressBarAccount.setMaximum(1)
            self.progressBarAccount.setText('')

        # Для определения посещений
        self.posServices = set()
        stmt = u"SELECT infis FROM vVisitServices"
        query = self.db.query(stmt)
        while query.next():
            record = query.record()
            self.posServices.add(forceString(record.value('infis')))
        # ТТ 2003 "Добавить вывод в счет-фактуру услуг по гриппу"
        for item in ['A26.30.157.001', 'A26.08.013.003', 'A26.08.013.004']:
            self.posServices.add(item)
        # ТТ 2037 "добавить в счет-фактуру и форму счет итоговый услугу пренатального скрининга"
        self.posServices.add('B03.032.002')

        # Для определения обращений
        self.pobr = set()
        stmt = u"""SELECT rbService.infis
                FROM rbService
                WHERE rbService.name like 'Обращен%'"""
        query = self.db.query(stmt)
        while query.next():
            record = query.record()
            self.pobr.add(forceString(record.value('infis')))
        for item in ['B05.015.002.010', 'B05.015.002.011', 'B05.015.002.012', 'B05.023.002.012',
                      'B05.023.002.013', 'B05.023.002.14', 'B05.050.004.019', 'B05.050.004.020', 'B05.050.004.021',
                      'B05.070.010', 'B05.070.011', 'B05.070.012', 'B03.014.018']:
            self.pobr.add(item)

        # Для определения услуг беременной
        self.pregnancyServices = set()
        stmt = u"""SELECT rbService.infis
                  FROM rbService
                  WHERE rbService.name like '%беременной%'"""
        query = self.db.query(stmt)
        while query.next():
            record = query.record()
            self.pregnancyServices.add(forceString(record.value('infis')))
        # self.chkMakeInvoice.setChecked(False)


    def getInvoice(self):
        return self.invoice

    def setExportMode(self, flag):
        self.btnCancel.setEnabled(flag)
        self.btnExport.setEnabled(not flag)
        self.chkIgnoreErrors.setEnabled(not flag)
        self.chkVerboseLog.setEnabled(not flag)
        self.cmbExportType.setEnabled(not flag)
        self.edtRegistryNumber.setEnabled(not flag
            and self.cmbExportType.currentIndex() not in (self.exportTypeFLK, self.exportTypeAttachments)
            and not hasattr(self, 'selectedAccountIds') or len(self.selectedAccountIds) == 1)
        self.chkMakeInvoice.setEnabled(not flag)


    def validatePage(self):
        # QtGui.qApp.preferences.appPrefs['%sIgnoreErrors' % self.prefix] = toVariant(self.chkIgnoreErrors.isChecked())
        # QtGui.qApp.preferences.appPrefs['%sVerboseLog' % self.prefix] = toVariant(self.chkVerboseLog.isChecked())
        # QtGui.qApp.preferences.appPrefs['%sExportType' % self.prefix] = toVariant(self.cmbExportType.currentIndex())

        return CAbstractExportPage1.validatePage(self)


    def getDbfBaseName(self):
        result = self.dbfFileName
        if not result:
            lpuCode = self.processParams().get('codeLpu')
            if lpuCode:
                result = u'%s.DBF' % (lpuCode)
                self.dbfFileName = result

        return result


    def getZipFileName(self):
        lpuCode = self.accInfo.get('codeLpu') if hasattr(self, 'accInfo') else self.processParams().get('codeLpu')

        if self.exportType in [self.exportTypeFLK, self.exportTypeAttachments]:
            #  Файл ФЛК должен иметь вид ГГММККККК.zip , где ГГММ – отчетный год и месяц ,
            # ККККК – код структурного подразделения (код омс), маска файла PKKKKK – где
            # ККККК – код структурного подразделения, P – буква латинского алфавита.
            # должен быть код омс подразделения в котором была оказана услуга.

            exdate = pyDate(QDate.currentDate())
            if exdate.day < 8:
                exdate = exdate - datetime.timedelta(days=8)
            result = u'%s%s.ZIP' % (exdate.strftime('%y%m'), lpuCode)
        else:
            prefix = u'a' if self.exportType in [self.exportTypePreControlP25] else ''
            result = u'%s%s%s%05d.ZIP' % (prefix, self.accInfo['payerCode'][:4], lpuCode[:5], self.accInfo['iAccNumber'])
        return result


    def exportInt(self):
        self.aborted = False
        self.noExportedAccount = []
        self.ignoreErrors = True
        self.exportType = self.exportTypeInvoice
        self.mkInvoice = True
        self.noKeysDict = {}
        self.NoKeysDictD = {}
        self._export(self.accountId)


    def _export(self, accountId=None):
        self.dbfFileName = None
        params = {}
        if accountId:
            self.currentAccountId = accountId
            self.accInfo = self.mapAccountInfo[self.currentAccountId]
            self.log(u'Экспорт счета № {0} от {1}'.format(self.accInfo.get('accNumber'), unicode(self.accInfo.get('accDate').toString(Qt.SystemLocaleDate))))
        self.serviceNum = 0
        self.exportedTempInvalidList = []
        self.exportedEvents = set()
        self.eventsDict = dict()
        self.RecordListP = []
        self.RecordListU = []
        self.RecordListD = []
        self.RecordListN = []
        self.RecordListR = []
        self.RecordListO = []
        self.RecordListI = []
        self.RecordListC = []

        self.setExportMode(True)
        self.progressBar.reset()
        self.progressBar.setMaximum(1)
        self.progressBar.setValue(0)
        self.progressBar.setText(u'Запрос в БД...')

        self.log(u'Запрос в БД...')
        QtGui.qApp.processEvents()
        if accountId and len(self.accInfo.get('oms_code')) == 5:
            self.log(u'Счет выставлен на подразделение, испольуем его код', True)
            params['codeLpu'] = self.accInfo.get('oms_code')
            self.log(u'Подразделение код: "%s".' % params['codeLpu'], True)
        elif self._parent.orgStructId:
            self.log(u'В фильтре выбрано подразделение, испольуем его код', True)
            params['codeLpu'] = forceString(self.db.translate(
                'OrgStructure', 'id', self._parent.orgStructId, 'bookkeeperCode'))
            self.log(u'Подразделение код: "%s".' % params['codeLpu'], True)
        else:
            lpuId = QtGui.qApp.currentOrgId()
            params['codeLpu'] = forceString(self.db.translate(
                'Organisation', 'id', lpuId , 'infisCode'))
            self.log(u'ЛПУ: код инфис: "%s".' % params['codeLpu'], True)

        if not params['codeLpu']:
            self.log(u'<b><font color=red>ОШИБКА<\font><\b>:'
                     u'Для текущего ЛПУ/подразделения не задан код инфис/для бухгалтерии', True)
            if not self.ignoreErrors:
                self.aborted = True
                return False

        if accountId:
            self.accInfo['codeLpu'] = params['codeLpu']
            params.update(self.accInfo)
            params['iAccNumber'] = 0
            self.accInfo['iAccNumber'] = 0
            if self.edtRegistryNumber.isEnabled():
                params['accNumber'] = forceInt(self.edtRegistryNumber.value())
                self.accInfo['accNumber'] = forceInt(self.edtRegistryNumber.value())
            try:
                params['iAccNumber'] = forceInt(params['accNumber'])
                self.accInfo['iAccNumber'] = forceInt(params['accNumber'])
            except:
                self.log(u'Невозможно привести номер счёта' \
                           u' "%s" к числовому виду' % params['accNumber'])

#            params['accTypeCode'] = forceString(QtGui.qApp.db.translate('rbAccountType', 'id', params['accTypeId'], 'regionalCode'))
            params['accTypeName'] = forceString(QtGui.qApp.db.translate('rbAccountType', 'id', params['accTypeId'], 'name'))
        self.noKeysSNILS = set()
        self.setProcessFuncList([self.process, self.processPerson])
        self.setProcessParams(params)
        CAbstractExportPage1.exportInt(self)
        res = True
        if self.exportType in [self.exportTypeP25, self.exportTypePreControlP25, self.exportTypeInvoice]:
            # Пересчет стоимости лечения стоматологии в 2018 году
            if self.accInfo['settleDate'] >= QDate(2018, 1, 1):
                self.calcStom()
            # определение целей посещения
            self.calcFieldsDbfP()
            # работа с RKEY
            if self.exportType != self.exportTypeInvoice:
                # пересчитываем контрольные суммы по FKEY
                fkeysDict = self.calcInternalHashFLK()
                # пересчитываем контрольные суммы по RKEY
                res = self.calcInternalHashAndExportRKEY(fkeysDict)
            # self.fillRKEYS()
        elif self.exportType == self.exportTypeAttachments:
            #  выгружаем dbf
            dbfName = os.path.join(self.getTmpDir(), 'P' + self.getDbfBaseName())
            dbf = Dbf(dbfName, False, encoding='cp866')
            for rec in self.RecordListP:
                _rec = dbf.newRecord()
                _rec.fieldData = rec.fieldData[:]
                _rec.store()
            dbf.close()
        else:
            fkeysDict = self.calcInternalHashFLK()
            #  выгружаем dbf
            dbfName = os.path.join(self.getTmpDir(), 'P' + self.getDbfBaseName())
            dbf = Dbf(dbfName, False, encoding='cp866')
            for rec in self.RecordListP:
                fkey = fkeysDict.get(forceString(rec['SN']), '')
                if fkey == '' or self.exportType in [self.exportTypeP25]:
                    _rec = dbf.newRecord()
                    _rec.fieldData = rec.fieldData[:]
                    _rec['FKEY'] = fkey
                    _rec.store()
            cnt = dbf.recordCount
            dbf.close()
            if not cnt:
                QtGui.QMessageBox.information(self, u'Внимание!',
                                              u'Файл не создан. Не найдено данных с отсутствующими или некорректными FKEY',
                                              QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                self.abort()
            self.db.query(u"""drop temporary table if EXISTS tmp_internalKeysFLK""")

        # Формируем фактуру в zip архив если стоит галочка
        if res and self.mkInvoice:
            self.log(u'Выгрузка счет-фактуры...')
            QtGui.qApp.processEvents()
            contractPayerId = forceInt(self.db.translate(
                'Contract', 'id', params['contractId'], 'payer_id'))
            isOutArea = 1 if contractPayerId == params['payerId'] else 0
            self.makeInvoice(params['accNumber'], params['accDate'], params['settleDate'],
                             params['payerId'], isOutArea, params['accTypeName'])
        return res


    def calcInternalHashAndExportRKEY(self, fkeysDict):
        def fillDBF(fileType, keyField, recordList, dats=None, fieldlistD=None):
            dbfName = os.path.join(self.getTmpDir(), fileType + self.getDbfBaseName())
            dbf = Dbf(dbfName, False, encoding='cp866')
            for rec in recordList:
                if fileType == 'D':
                    stringKey = dats + ''.join([forceString(rec[fld]) for fld in fieldlistD])
                    hashKey = hashlib.sha1(stringKey.encode('utf-8')).hexdigest()
                    rkey = rkeysDict.get((fileType, hashKey), '')
                    if not rkey:
                        self.noKeysSNILS.add(forceString(rec[keyField]))
                    if self.exportType == self.exportTypePreControlP25:
                        rkey = ''
                else:
                    rkey = rkeysDict.get((fileType, forceString(rec[keyField])), '')

                # if fileType != 'D':
                #     fkey = fkeysDict.get(forceString(rec['SN']), '')
                # else:
                #     fkey = True

                if rkey == '' or self.exportType == self.exportTypeP25:
                    _rec = dbf.newRecord()
                    _rec.fieldData = rec.fieldData[:]
                    _rec['RKEY'] = rkey
                    if fileType == 'P':
                        _rec['FKEY'] = fkeysDict.get(forceString(rec['SN']), '')
                    _rec.store()
            dbf.close()
            return dbf.recordCount

        self.log(u'вычисление контрольных сумм RKEY...')
        QtGui.qApp.processEvents()
        self.db.query(u"""drop temporary table if EXISTS tmp_internalKeys""")
        self.db.query(u"""create temporary table if not EXISTS tmp_internalKeys(event_id int, typeFile char(1), row_id int, alt_row_id varchar(40), internalKey varchar(40), RKEY varchar(50), SNILS varchar(14),
                          index event_id(event_id), index row_id(row_id), index alt_row_id(alt_row_id), index typeFile(typeFile))""")
        dats = ''
        fieldlistD = CExportPage1.fieldListKeyD202005
        if self.RecordListP:
            dats = forceDate(self.RecordListP[0]['DATS'])
            fieldlistD = CExportPage1.fieldListKeyD202005 if dats >= QDate(2020, 5, 1) else CExportPage1.fieldListKeyD
            dats = forceString(dats.month()) + forceString(dats.year())
        updateInternalHash('P', 'SN', self.RecordListP, dats, CExportPage1.fieldListKeyP)
        updateInternalHash('U', 'UID', self.RecordListU, dats, CExportPage1.fieldListKeyU)
        updateInternalHash('N', None, self.RecordListN, dats, CExportPage1.fieldListKeyN, 'NAPR_N')
        updateInternalHash('D', None, self.RecordListD, dats, fieldlistD)
        updateInternalHash('R', 'RID', self.RecordListR, dats, CExportPage1.fieldListKeyR)
        updateInternalHash('O', 'OID', self.RecordListO, dats, CExportPage1.fieldListKeyO)
        updateInternalHash('I', 'IID', self.RecordListI, dats, CExportPage1.fieldListKeyI)
        updateInternalHash('C', 'CID', self.RecordListC, dats, CExportPage1.fieldListKeyC)
        self.log(u'обновление/вставка контрольных сумм в таблицу с ключами...')
        QtGui.qApp.processEvents()

        #  Очищаем таблицу ключей от мусорных записей
        self.db.query(u"""drop temporary table if EXISTS tmp_keyList""")
        self.db.query(u"""create temporary table if not EXISTS tmp_keyList(event_id int, sark_id int, index event_id(event_id), index sark_id(sark_id))""")
        # self.log(u'запрос 1')
        QtGui.qApp.processEvents()
        self.db.query(u"""INSERT INTO tmp_keyList(event_id, sark_id)
        SELECT sark.event_id, sark.id
        FROM soc_Account_RowKeys sark
        INNER JOIN tmp_internalKeys t ON t.event_id = sark.event_id AND t.row_id = sark.row_id AND t.typeFile = sark.typeFile
        WHERE t.typeFile in ('P', 'U', 'R', 'O', 'I', 'C') and sark.account_id is null""")
        # self.log(u'запрос 2')
        QtGui.qApp.processEvents()
        self.db.query(u"""INSERT INTO tmp_keyList(event_id, sark_id)
               SELECT sark.event_id, sark.id
               FROM soc_Account_RowKeys sark
               INNER JOIN tmp_internalKeys t ON t.event_id = sark.event_id AND t.alt_row_id = sark.alt_row_id AND t.typeFile = sark.typeFile
               WHERE t.typeFile = 'N' and sark.account_id is null""")
        # self.log(u'запрос 3')
        QtGui.qApp.processEvents()
        self.db.query(u"""DELETE sark
                       FROM soc_Account_RowKeys sark
                       LEFT JOIN tmp_keyList t ON t.event_id = sark.event_id AND t.sark_id = sark.id
                       WHERE sark.event_id in ({0}) and t.sark_id is null and sark.typeFile != 'F'""".format(u','.join([forceString(item) for item in self.exportedEvents]) if self.exportedEvents else '0'))
        # self.log(u'запрос 4')
        QtGui.qApp.processEvents()
        self.db.query(u"""drop temporary table if EXISTS tmp_keyList""")

        #  очищаем ключи для измененных записей файлов 'P', 'U', 'R', 'O', 'I', 'C'
        self.db.query(u"""UPDATE soc_Account_RowKeys sark
INNER JOIN tmp_internalKeys t ON t.event_id = sark.event_id AND t.row_id = sark.row_id AND t.typeFile = sark.typeFile
set sark.account_id = NULL, sark.internalKey = t.internalKey, `key` = IF(sark.internalKey != t.internalKey, NULL, sark.`key`)
WHERE t.typeFile in ('P', 'U', 'R', 'O', 'I', 'C')""")
        # self.log(u'запрос 5')
        QtGui.qApp.processEvents()
        #  очищаем ключи для измененных записей файла 'N'
        self.db.query(u"""UPDATE soc_Account_RowKeys sark
INNER JOIN tmp_internalKeys t ON t.event_id = sark.event_id AND t.alt_row_id = sark.alt_row_id AND t.typeFile = sark.typeFile
set sark.account_id = NULL, sark.internalKey = t.internalKey, `key` = IF(sark.internalKey != t.internalKey, NULL, sark.`key`)
WHERE t.typeFile = 'N'""")
        # self.log(u'запрос 6')
        QtGui.qApp.processEvents()
        #  очищаем ключи для измененных записей файла 'D'
        self.db.query(u"""UPDATE soc_Account_RowKeys sark
INNER JOIN tmp_internalKeys t ON t.alt_row_id = sark.alt_row_id AND t.typeFile = sark.typeFile
set sark.internalKey = t.internalKey, `key` = IF(sark.internalKey != t.internalKey, NULL, sark.`key`)
WHERE t.typeFile = 'D'""")

        # self.log(u'запрос 7')
        QtGui.qApp.processEvents()
        #  вставляем отсутствующие записи для ключей файлов 'P', 'U', 'R', 'O', 'I', 'C'
        self.db.query(u"""INSERT INTO soc_Account_RowKeys(event_id, typeFile, row_id, alt_row_id, internalKey)
select t.event_id, t.typeFile, t.row_id, t.alt_row_id, t.internalKey
from tmp_internalKeys t
left JOIN soc_Account_RowKeys sark ON t.event_id = sark.event_id AND t.row_id = sark.row_id AND t.typeFile = sark.typeFile
where t.typeFile in ('P', 'U', 'R', 'O', 'I', 'C') AND sark.id is null""")
        # self.log(u'запрос 8')
        QtGui.qApp.processEvents()
        #  вставляем отсутствующие записи для ключей файла 'N'
        self.db.query(u"""INSERT INTO soc_Account_RowKeys(event_id, typeFile, row_id, alt_row_id, internalKey)
select t.event_id, t.typeFile, t.row_id, t.alt_row_id, t.internalKey
from tmp_internalKeys t
left JOIN soc_Account_RowKeys sark ON t.event_id = sark.event_id AND t.alt_row_id = sark.alt_row_id AND t.typeFile = sark.typeFile
where t.typeFile = 'N' AND sark.id is null""")
        # self.log(u'запрос 9')
        QtGui.qApp.processEvents()
        #  вставляем отсутствующие записи для ключей файла 'D'
        self.db.query(u"""INSERT INTO soc_Account_RowKeys(event_id, typeFile, row_id, alt_row_id, internalKey)
select t.event_id, t.typeFile, t.row_id, t.alt_row_id, t.internalKey
from tmp_internalKeys t
left JOIN soc_Account_RowKeys sark ON t.alt_row_id = sark.alt_row_id AND t.typeFile = sark.typeFile
where t.typeFile = 'D' AND sark.id is null""")
        # self.log(u'запрос 10')
        QtGui.qApp.processEvents()
        #  таблица событий с отсутствующими ключами
        self.db.query(u"""drop temporary table if EXISTS tmp_eventsWithoutkeys""")
        self.db.query(u"""create temporary table if not EXISTS tmp_eventsWithoutkeys(event_id int)""")
        self.db.query(u"""INSERT INTO tmp_eventsWithoutkeys(event_id)
select t.event_id
from tmp_internalKeys t
left JOIN soc_Account_RowKeys sark ON t.event_id = sark.event_id AND t.row_id = sark.row_id AND t.typeFile = sark.typeFile
where t.typeFile in ('P', 'U', 'R', 'O', 'I', 'C') and ifnull(sark.`key`, '') = ''""")
        self.db.query(u"""INSERT INTO tmp_eventsWithoutkeys(event_id)
select t.event_id
from tmp_internalKeys t
left JOIN soc_Account_RowKeys sark ON t.event_id = sark.event_id AND t.alt_row_id = sark.alt_row_id AND t.typeFile = sark.typeFile
where t.typeFile in ('N') and ifnull(sark.`key`, '') = ''""")
        self.db.query(u"""drop temporary table if EXISTS tmp_DWithoutkeys""")
        self.db.query(u"""create temporary table if not EXISTS tmp_DWithoutkeys(snils varchar(14))""")
        self.db.query(u"""INSERT INTO tmp_DWithoutkeys(snils)
select distinct t.SNILS
from tmp_internalKeys t
left JOIN soc_Account_RowKeys sark ON t.alt_row_id = sark.alt_row_id AND t.typeFile = sark.typeFile
where t.typeFile = 'D' and ifnull(sark.`key`, '') = ''""")
        # Врачи без ключей
        if self.exportType == self.exportTypeP25:
            queryD = self.db.query(u"""select snils from tmp_DWithoutkeys""")
            while queryD.next():
                recordD = queryD.record()
                snils = forceString(recordD.value('snils'))
                for rec in self.RecordListD:
                    if forceString(rec['SNILS']) == snils:
                        self.NoKeysDictD[snils] = u'{0} {1} {2} {3}'.format(snils, forceString(rec['FIO']), forceString(rec['IMA']), forceString(rec['OTCH']))
        # если данные в файле D изменились
        self.db.query(u"""INSERT INTO tmp_eventsWithoutkeys(event_id)
        select t.event_id
        from tmp_internalKeys t
        left JOIN soc_Account_RowKeys sark ON t.event_id = sark.event_id AND t.row_id = sark.row_id AND t.typeFile = sark.typeFile
        left join tmp_DWithoutkeys td on td.snils = t.snils
        where t.typeFile = 'U' and td.snils is not null""")
        self.db.query(u"""drop temporary table if EXISTS tmp_DWithoutkeys""")
        # self.log(u'запрос 11')
        QtGui.qApp.processEvents()
        #  очищаем ключи у событий у которых есть незаполненные ключи
        self.db.query(u"""UPDATE soc_Account_RowKeys sark
inner join tmp_eventsWithoutkeys t on t.event_id = sark.event_id
set sark.`key` = NULL
where sark.typeFile != 'F'""")
        # self.log(u'запрос 12')
        QtGui.qApp.processEvents()
        rkeysDict = {}
        #  заполняем словарь rkey для файлов 'P', 'U', 'R', 'O', 'I', 'C'
        query = self.db.query(u"""SELECT sark.`key`, t.*
FROM soc_Account_RowKeys sark
INNER JOIN tmp_internalKeys t ON t.event_id = sark.event_id AND t.row_id = sark.row_id AND t.typeFile = sark.typeFile
where t.typeFile in ('P', 'U', 'R', 'O', 'I', 'C')""")
        while query.next():
            record = query.record()
            typeFile = forceString(record.value('typeFile'))
            keyfieldName = 'alt_row_id' if typeFile in ['D', 'N'] else 'row_id'
            rkeysDict[(typeFile, forceString(record.value(keyfieldName)))] = forceString(record.value('key'))
        # self.log(u'запрос 13')
        QtGui.qApp.processEvents()
        #  заполняем словарь rkey для файла 'N'
        query = self.db.query(u"""SELECT sark.`key`, t.*
FROM soc_Account_RowKeys sark
INNER JOIN tmp_internalKeys t ON t.event_id = sark.event_id AND t.alt_row_id = sark.alt_row_id AND t.typeFile = sark.typeFile
where t.typeFile = 'N'""")
        while query.next():
            record = query.record()
            typeFile = forceString(record.value('typeFile'))
            keyfieldName = 'alt_row_id' if typeFile in ['D', 'N'] else 'row_id'
            rkeysDict[(typeFile, forceString(record.value(keyfieldName)))] = forceString(record.value('key'))
        # self.log(u'запрос 14')
        QtGui.qApp.processEvents()
        #  заполняем словарь rkey для файла 'D'
        query = self.db.query(u"""SELECT sark.`key`, t.*
FROM soc_Account_RowKeys sark
INNER JOIN tmp_internalKeys t ON t.alt_row_id = sark.alt_row_id AND t.typeFile = sark.typeFile
where t.typeFile = 'D'""")
        while query.next():
            record = query.record()
            typeFile = forceString(record.value('typeFile'))
            keyfieldName = 'alt_row_id' if typeFile in ['D', 'N'] else 'row_id'
            rkeysDict[(typeFile, forceString(record.value(keyfieldName)))] = forceString(record.value('key'))
        # self.log(u'запрос 15')
        QtGui.qApp.processEvents()
        #  выгружаем dbf
        cnt = fillDBF('P', 'SN', self.RecordListP)

        #  выбираем события с отсутсвтвующими rkey
        query = self.db.query(u"""select distinct event_id from tmp_eventsWithoutkeys""")
        noKeySet = set()
        while query.next():
            record = query.record()
            noKeySet.add(forceInt(record.value('event_id')))

        self.db.query(u"""drop temporary table if EXISTS tmp_internalKeys""")
        self.db.query(u"""drop temporary table if EXISTS tmp_eventsWithoutkeys""")

        QtGui.qApp.processEvents()
        for rec_p in self.RecordListP:
            if forceRef(rec_p['SN']) in noKeySet:
                self.noKeysDict[forceRef(rec_p['SN'])] = [forceDate(rec_p['DATS']), forceRef(rec_p['NS']),
                                                          forceRef(rec_p['SN']), formatName(forceString(rec_p['FIO']),
                                                                                            forceString(rec_p['IMA']),
                                                                                            forceString(rec_p['OTCH']))]
        QtGui.qApp.processEvents()
        #  выбираем события с отсутсвтвующими fkey
        for rec_p in self.RecordListP:
            if not fkeysDict.get(forceString(rec_p['SN']), ''):
                self.noKeysFLKDict[forceRef(rec_p['SN'])] = [forceDate(rec_p['DATS']), forceRef(rec_p['NS']),
                                                             forceRef(rec_p['SN']),
                                                             formatName(forceString(rec_p['FIO']),
                                                                        forceString(rec_p['IMA']),
                                                                        forceString(rec_p['OTCH']))]
        if not cnt:
            self.noExportedAccount.append(u'№ {0} от {1}'.format(self.accInfo.get('accNumber'), unicode(self.accInfo.get('accDate').toString(Qt.SystemLocaleDate))))
            return False
        QtGui.qApp.processEvents()

        fillDBF('U', 'UID', self.RecordListU)
        fillDBF('D', 'SNILS', self.RecordListD, dats, fieldlistD)
        fillDBF('R', 'RID', self.RecordListR)
        fillDBF('N', 'NAPR_N', self.RecordListN)
        fillDBF('O', 'OID', self.RecordListO)
        fillDBF('I', 'IID', self.RecordListI)
        fillDBF('C', 'CID', self.RecordListC)

        return True

    def calcInternalHashFLK(self):
        fkeysDict = {}
        self.log(u'вычисление контрольных сумм FKEY...')
        QtGui.qApp.processEvents()
        self.db.query(u"""drop temporary table if EXISTS tmp_internalKeysFLK""")
        self.db.query(u"""create temporary table if not EXISTS tmp_internalKeysFLK(event_id int, typeFile char(1), internalKey varchar(40), FKEY varchar(50), index event_id(event_id))""")
        updateInternalHashFLK(self.RecordListP, CExportPage1.fieldListKeyFLK)
        QtGui.qApp.processEvents()
        #  очищаем ключи для измененных записей файла ФЛК
        self.db.query(u"""UPDATE soc_Account_RowKeys sark
        INNER JOIN tmp_internalKeysFLK t ON t.event_id = sark.event_id AND t.typeFile = sark.typeFile
        set sark.internalKey = t.internalKey, `key` = IF(sark.internalKey != t.internalKey, NULL, sark.`key`)
        WHERE t.typeFile = 'F' and sark.`key` is not null""")
        QtGui.qApp.processEvents()
        #  вставляем отсутствующие записи для ключей файла ФЛК
        self.db.query(u"""INSERT INTO soc_Account_RowKeys(event_id, typeFile, internalKey)
        select t.event_id, t.typeFile, t.internalKey
        from tmp_internalKeysFLK t
        left JOIN soc_Account_RowKeys sark ON t.event_id = sark.event_id and t.typeFile = sark.typeFile
        where t.typeFile = 'F' AND sark.id is null""")
        QtGui.qApp.processEvents()
        #  заполняем словарь fkey для файла ФЛК
        query = self.db.query(u"""SELECT sark.`key`, t.*
    FROM soc_Account_RowKeys sark
    INNER JOIN tmp_internalKeysFLK t ON t.event_id = sark.event_id AND t.typeFile = sark.typeFile
    where t.typeFile = 'F'""")
        while query.next():
            record = query.record()
            fkeysDict[forceString(record.value('event_id'))] = forceString(record.value('key'))
        return fkeysDict


    def calcFieldsDbfP(self):
        for rec_p in self.RecordListP:
            event = self.eventsDict.get(rec_p['SN'], None)
            if event:
                VP = event['VP']
                if event['VS'] in ['ak', 'bk', 'ck', 'dk', 'am', 'bm', 'cm', 'dm', 'au', 'bu', 'cu', 'du', 'ae', 'be', 'ce', 'de', 'ag', 'bg', 'cg', 'dg', 'ah', 'bh', 'ch', 'dh', 'av', 'bv', 'cv', 'dv']:
                    kso = '28' # за медицинскую услугу в поликлинике
                elif VP in ['11', '12', '301', '302', '41', '42', '43', '51', '52', '511', '522']:
                    kso = '33'  # за закон. случай леч. забол., вкл. в соответ. группу забол. (в том числе КСГ забол.) в стацион. усл.
                elif VP in ['401', '402']:
                    kso = '32'  # за закон. случай леч. забол. при оплате МП, оказанной в стационарных условиях (ВМП)
                elif VP in ['801', '802']:
                    if rec_p['OKATO_OMS'] == '03000':  # для краевых
                        kso = '36'  # по подуш. нормат. финан. в сочетании с оплатой за вызов скорой МП (краевые застрахованные)
                    else:
                        kso = '24'  # вызов скорой медицинской помощи (инокраевые застрахованные)
                elif VP in ['271', '272']:
                    kso = '25'  # по подуш. нормат. финан. на прикреп. лиц в сочетании с оплатой за единицу объема медицинской помощи
                elif  VP in ['01', '02', '111', '112', '211', '232', '233', '244', '252', '261', '262', '241', '242', '281', '282']:
                    kso = '29'  # за посещение в поликлинике
                elif VP in ['21', '22', '31', '32']:
                    if event['hasObrService']:
                        kso = '30'  # за обращение (законченный случай) в поликлинике
                    else:
                        kso = '29'  # за посещение в поликлинике
                else:
                    kso = ''
                rec_p['KSO'] = kso

                if VP in ['01', '02', '111', '112', '21', '22', '211', '232', '233', '244', '252', '261', '262', '271', '272', '241',
                          '242', '31', '32', '201', '202', '60', '281', '282']:
                    # старые коды
                    if rec_p['DATO'] <= datetime.date(2018, 3, 31):
                        if VP in ['241', '242']:  # неотложка
                            cel = '2'
                        elif VP in ['111', '112']:  # приемные отделения
                            cel = '9'
                        elif VP in ['01', '02', '211', '232', '233', '244', '252', '261', '262']:  # ЦЗ и дисп
                            cel = '1'
                        elif event['hasObrService']:  # обращение
                            cel = '3'
                        else:
                            cel = '9'  # без обращения
                    # новые коды
                    else:
                        if rec_p['MP'] == '8' and not event['hasObrService']:
                            cel = '1.1' # посещениe в неотложной форме
                        elif VP in ['261', '262']:
                            cel = '2.1' # медицинский осмотр
                        elif VP in ['211', '232', '233', '244', '252']:
                            cel = '2.2' # диспансеризация
                        elif VP in ['01', '02']:
                            cel = '2.3' # комплексное обследование
                        elif event['hasObrService']:
                            cel = '3.0' # обращение по заболеванию
                        elif event['hasHomeServiсe']:
                            cel = '1.2' # активное посещение
                        elif event['hasDNService']:
                            cel = '1.3' # диспансерное наблюдение
                        elif event['hasPatronService']:
                            cel = '2.5' # патронаж
                        elif rec_p['MKBX'] and rec_p['MKBX'][0] != 'Z':
                            cel = '1.0' # посещение по заболеванию
                        else:
                            cel = '2.6' # посещение по другим обстоятельствам
                else:
                    cel = ''
                rec_p['P_CEL'] = cel
            if rec_p['SN'] in self.DS_ONKSet:
                rec_p['DS_ONK'] = '1'
            else:
                rec_p['DS_ONK'] = '0'


    def calcStom(self):
        u"""Пересчет стоимости лечения стоматологии в 2018 году"""
        stomPosDict = {}
        stomPosDictUID = {}
        for rec_u in self.RecordListU:
            if rec_u['VP'] in ['31', '32'] and rec_u['DATO'] >= datetime.date(2018, 1, 1):
                vp = rec_u['VP']
                kusl = rec_u['KUSL']
                summ = rec_u['SUMM']
                stomPos = stomPosDict.setdefault((rec_u['SN'], rec_u['DATO']), [None, 0.0])
                stomPos[1] += summ
                if kusl in self.posServices:
                    stomPos[0] = rec_u['UID']
                else:
                    rec_u['TARU'] = 0.0
                    rec_u['SUMM'] = 0.0
        for stomPos in stomPosDict:
            stomPosDictUID[stomPosDict[stomPos][0]] = stomPosDict[stomPos][1]
        for rec_u in self.RecordListU:
            if rec_u['UID'] in stomPosDictUID:
                summ = stomPosDictUID[rec_u['UID']]
                rec_u['TARU'] = summ
                rec_u['SUMM'] = summ


    def getInvoiceData(self):
        report = dict()

        # Для оптимизации скорости, загружаем данные о пациентах в словарь
        #  Грузим признаки работающих и неработающих в словарь, чтоб быстрее работало
        pdict = dict()
        for rec_p in self.RecordListP:
            pdict[rec_p['SN']] = [rec_p['KAT'], rec_p['IMA'], rec_p['OTCH'], rec_p['DATR'], rec_p['POL'], rec_p['VS']]

        if self.exportType == self.exportTypeInvoice:
            stmt = """select coef_item.value
            from soc_prikCoefType coef
            left join soc_prikCoefItem coef_item on coef_item.master_id = coef.id
            where coef.organisation_id = {0} 
            and coef.coefficientType = 2 
            and {1} between coef.begDate and coef.endDate
            and coef_item.bookkeeperCode = '{2}'""".format(forceInt(self.accInfo.get('payerId')), self.db.formatDate(self.accInfo.get('accDate')), forceString(self.RecordListP[0]['CODE_MO']))
            query = self.db.query(stmt)
            if query.first():
                k2 = forceDouble(query.record().value('value'))
            else:
                k2 = 1.0

        for rec_u in self.RecordListU:
            # Вычисление сумм с учетом коэф. К2 И К3 и ещё К0...
            if self.exportType == self.exportTypeInvoice:
                if forceBool(rec_u['hasK0']):
                    rec_u['TARU'] = forceDouble(rec_u['K0'])
                    rec_u['SUMM'] = forceDouble(rec_u['K0'])
                else:
                    rec_u['TARU'] = roundMath(forceDouble(rec_u['TARU']) * k2, 2) + rec_u['K3']
                    rec_u['SUMM'] = roundMath(forceDouble(rec_u['SUMM']) * k2, 2) + rec_u['K3']

            if self.accInfo['isFAP']:
                keyvalue = 'FAP'
            elif pdict[rec_u['SN']][5] in ['ak', 'bk', 'ck', 'dk', 'am', 'bm', 'cm', 'dm', 'au', 'bu', 'cu', 'du', 'ae', 'be', 'ce', 'de', 'ag', 'bg', 'cg', 'dg', 'ah', 'bh', 'ch', 'dh', 'av', 'bv', 'cv', 'dv']:
                keyvalue = pdict[rec_u['SN']][5]
            else:
                keyvalue = rec_u['VP']
            rep_item = report.setdefault(keyvalue, {
                                                   'name': forceString(self.db.translate('rbMedicalAidType', 'regionalCode', rec_u['VP'], 'name')),
                                                   'fl': [set(), set()],  # кол-во физлиц (неработающие/работающие)
                                                   'sn': [set(), set()],  # кол-во перссчетов
                                                   'obr': [0, 0],  # обращения
                                                   'cpo': [0, 0],  # посещения с обращением
                                                   'cp': [0, 0],  # посещения без обращений
                                                   'cpotw': [0, 0],  # посещения по заболеванию
                                                   'kolu': [0, 0],  # кол-во простых услуг
                                                   'somp': [0, 0],  # кол-во стандартов(КСГ/ВМП)
                                                   'sum_obr': 0,  # сумма обращений
                                                   'sum_pos': 0,  # сумма посещений
                                                   'sum_posotw': [0, 0],  # сумма посещений по заболеванию
                                                   'kd': [0, 0],  # кол-во койко-дней
                                                   'pd': [0, 0],  # кол-во пациенто-дней (для ДС)
                                                   'uet': [0, 0],  # кол-во УЕТ
                                                   'summ': [0, 0]  # общая сумма
                                                   }
                                     )
            rep_all = report.setdefault('-1', {
                                                  'name': u'ИТОГО',
                                                  'fl': [set(), set()],  # кол-во физлиц (неработающие/работающие)
                                                  'sn': [set(), set()],  # кол-во перссчетов
                                                  'obr': [0, 0],  # обращения
                                                  'cpo': [0, 0],  # посещения с обращением
                                                  'cp': [0, 0],  # посещения без обращений
                                                  'cpotw': [0, 0],  # посещения по заболеванию
                                                  'kolu': [0, 0],  # кол-во простых услуг
                                                  'somp': [0, 0],  # кол-во стандартов(КСГ/ВМП)
                                                  'sum_obr': 0,  # сумма обращений
                                                  'sum_pos': 0,  # сумма посещений
                                                  'sum_posotw': [0, 0],  # сумма посещений по заболеванию
                                                  'kd': [0, 0],  # кол-во койко-дней
                                                  'pd': [0, 0],  # кол-во пациенто-дней (для ДС)
                                                  'uet': [0, 0],  # кол-во УЕТ
                                                  'summ': [0, 0]  # общая сумма
                                                  }
                                    )
            if pdict.has_key(rec_u['SN']):
                for rep in [rep_item, rep_all]:
                    kat = forceInt(pdict[rec_u['SN']][0] == '1')
                    rep['fl'][kat].add(tuple(pdict[rec_u['SN']]))
                    rep['sn'][kat].add(rec_u['SN'])
                    if rec_u['KUSL'][:1] in (u'A', u'B'):
                        if rec_u['KUSL'] in self.pobr:
                            rep['obr'][kat] += 1
                            rep['sum_obr'] += rec_u['SUMM']
                        elif rec_u['KUSL'] in self.posServices:
                            event = self.eventsDict.get(rec_u['SN'], None)
                            if event and event['hasObrService']:
                                rep['cpo'][kat] += 1
                            else:
                                rep['cp'][kat] += 1
                                rep['sum_pos'] += rec_u['SUMM']
                                if rec_u['KUSL'][:3] in ['B01', 'B02'] and rec_u['MKBX'][:1] != 'Z' and rec_u['KUSL'] not in self.pregnancyServices:
                                    rep['cpotw'][kat] += 1
                                    rep['sum_posotw'][kat] += rec_u['SUMM']
                        else:
                            rep['kolu'][kat] += rec_u['KOLU']
                    if rec_u['KUSL'][:1] in ['G', 'V']:
                        rep['somp'][kat] += 1
                        if rec_u['VP'] in ['11', '12', '301', '302', '401', '402']:
                            rep['kd'][kat] += rec_u['KD']
                        elif rec_u['VP'] in ['41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522']:
                            rep['pd'][kat] += rec_u['KD']
                    rep['uet'][kat] += self.uetDict.get(rec_u['UID'], 0)
                    rep['summ'][kat] += rec_u['SUMM']
        return report


    def makeInvoice(self, accNumber, accDate, periodDate, payerId, isOutArea, accTypeName):
        reps = self.getInvoiceData()
        casecount = len(reps['-1']['sn'][0]) + len(reps['-1']['sn'][1])
        summ = reps['-1']['summ'][0] + reps['-1']['summ'][1]
        invoice = QtGui.QTextDocument()
        # Рисуем фактуру
        fnt = invoice.defaultFont()
        fnt.setPointSize(8)
        invoice.setDefaultFont(fnt)
        invoice_cursor = QtGui.QTextCursor(invoice)
        fmtdiv = QtGui.QTextBlockFormat()
        invoice_cursor.insertBlock(fmtdiv)
        invoice_cursor.setCharFormat(CReportBase.ReportTitle)
        invoice_cursor.insertText(u'Счет итоговый')
        invoice_cursor.insertBlock()
        fmt = QtGui.QTextBlockFormat()
        # fmt.setAlignment(Qt.AlignRight)
        # invoice_cursor.insertBlock(fmt)
        # invoice_cursor.insertHtml(u"Приложение № 1<br>")
        # invoice_cursor.insertHtml(u"к постановлению Правительства Российской Федерации<br>")
        # invoice_cursor.insertHtml(u"от 26 декабря 2011 г. № 1137<br>")
        # invoice_cursor.insertHtml(u"(в ред. Постановления Правительства РФ от 19.08.2017 № 981)")

        # fmt.setAlignment(Qt.AlignCenter)
        # invoice_cursor.insertBlock(fmt)
        invoice_num  = forceString(accNumber)
        invoice_date = forceString(accDate)

        # invoice_cursor.insertHtml(u"<b>СЧЕТ-ФАКТУРА № %s от %s</b><br>" % ('_'*3, invoice_date.rjust(10,'_')))
        # invoice_cursor.insertHtml(u"<b>ИСПРАВЛЕНИЕ № %s от %s</b><br>" % ('_'*3, '_'*10))
        # invoice_cursor.insertHtml(u"к реестру счетов № %s от %s за %s %s %s<br>" % (invoice_num, invoice_date, str(periodDate.year()), monthName[periodDate.month()], accTypeName))
        fmt.setAlignment(Qt.AlignLeft)
        # invoice_cursor.insertBlock(fmt)
        # table = createTable(invoice_cursor, [ ('30%', [], CReportBase.AlignLeft), ('70%', [], CReportBase.AlignLeft) ],
        #                      headerRowCount=11, border=0, cellPadding=2, cellSpacing=0)
        fmt = QtGui.QTextCharFormat()
        fmt.setFontUnderline(True)
        db = QtGui.qApp.db
        # Формируем запросы
        tableOrganisation = db.table('Organisation')
        tableAccount = db.table('Organisation_Account')
        tableAccounts = db.table('Account')
        tableBank = db.table('Bank')
        tableOrgStructure = db.table('OrgStructure')
        tablef = tableOrganisation.leftJoin(tableAccount, [tableAccount['organisation_id'].eq(tableOrganisation['id'])])
        tablef = tablef.leftJoin(tableBank, [tableAccount['bank_id'].eq(tableBank['id'])])
        tablef = tablef.leftJoin(tableAccounts, [tableAccounts['id'].eq(self.currentAccountId)])
        tablef = tablef.leftJoin(tableOrgStructure, [tableOrgStructure['id'].eq(tableAccounts['orgStructure_id'])])

        # Выгружаем данные поставщика и плательщика
        record = db.getRecordEx(tablef,
                                [tableOrganisation['fullName'].name(),
                                 tableOrganisation['INN'].name(),
                                 tableOrganisation['KPP'].name(),
                                 tableOrganisation['Address'].name(),
                                 tableOrgStructure['name'].alias('OrgStructureName'),
                                 tableOrganisation['accountant'].name(),
                                 tableBank['name'].alias('BankName'),
                                 tableBank['BIK'].name(),
                                 tableAccount['name'].alias('schet'),
                                 tableAccount['personalAccount']
                                ],
                                tableOrganisation['id'].eq(QtGui.qApp.currentOrgId()),
                                order='Organisation_Account.id desc'
        )
        record_pay = db.getRecordEx(tablef,
                                    [tableOrganisation['fullName'].name(),
                                     tableOrganisation['INN'].name(),
                                     tableOrganisation['KPP'].name(),
                                     tableOrganisation['Address'].name(),
                                     tableBank['name'].alias('BankName'),
                                     tableBank['BIK'].name(),
                                     tableAccount['name'].alias('schet'),
                                     tableAccount['personalAccount']
                                    ],
                                    tableOrganisation['id'].eq(payerId),
                                    order='Organisation_Account.id desc'
        )

        fmtc = QtGui.QTextBlockFormat()
        fmtc.setAlignment(Qt.AlignCenter)
        fmtl = QtGui.QTextBlockFormat()
        fmtl.setAlignment(Qt.AlignLeft)

        lpuCode = forceString(self.db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'infisCode'))
        ll = lpuCode[0] + lpuCode[1]
        if forceString(QtGui.qApp.preferences.appPrefs.get('provinceKLADR', '00'))[:2] == '23' and '01' == ll:
            lpu = invoice_num
        else:
            lpu = '___'
        fmt = QtGui.QTextBlockFormat()
        fmt.setAlignment(Qt.AlignCenter)
        invoice_cursor.insertBlock(fmt)
        # invoice_cursor.insertHtml(u"<br><b>СЧЕТ № %s от %s</b><br>" % (lpu, invoice_date.rjust(40,'_')))
        # invoice_cursor.insertHtml(u"к реестру счетов № %s от %s за %s %s %s<br>" % (invoice_num,invoice_date,str(periodDate.year()), monthName[periodDate.month()], accTypeName))
        tableColumns = [
            ('15%', [u'Предмет счета'],CReportBase.AlignCenter),
            ('45%', [u'Наименование'], CReportBase.AlignCenter),
            ('15%', [u'Един. изм.'], CReportBase.AlignCenter),
            ('10%', [u'Количество'], CReportBase.AlignCenter),
            ('15%', [u'Сумма, руб.'], CReportBase.AlignCenter)
            ]
        invoice_cursor.movePosition(QtGui.QTextCursor.End)
        invoice_cursor.insertBlock()

        table = createTable(invoice_cursor, tableColumns, 40, border=1, cellPadding=0, cellSpacing=0)

        for i in range(0, 5):
            table.setText(1, i, str(i + 1), blockFormat=fmtc)
        table.mergeCells(2, 0, 38, 1)
        row_number = 2

        table.setText(row_number, 0, u'Медицинская помощь, оказанная застрахованным гражданам', blockFormat=fmtc)
        table.setText(row_number, 1, u'Стационар', blockFormat=fmtl)
        table.setText(row_number, 2, u'Случаи', blockFormat=fmtc)
        table.mergeCells(row_number, 4, 2, 1)
        table.mergeCells(row_number, 1, 2, 1)
        row_number += 1
        table.setText(row_number, 2, u'койко-день', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'в том числе высокотехнологичная медицинская помощь', blockFormat=fmtl)
        table.setText(row_number, 2, u'Случаи', blockFormat=fmtc)
        table.mergeCells(row_number, 4, 2, 1)
        table.mergeCells(row_number, 1, 2, 1)
        row_number += 1
        table.setText(row_number, 2, u'койко-день', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Дневной стационар', blockFormat=fmtl)
        table.setText(row_number, 2, u'Случаи', blockFormat=fmtc)
        table.mergeCells(row_number, 4, 2, 1)
        table.mergeCells(row_number, 1, 2, 1)
        row_number += 1
        table.setText(row_number, 2, u'пациенто-день', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'в т.ч. экстракорпоральное оплодотворение', blockFormat=fmtl)
        table.setText(row_number, 2, u'Случаи', blockFormat=fmtc)
        table.mergeCells(row_number, 4, 2, 1)
        table.mergeCells(row_number, 1, 2, 1)
        row_number += 1
        table.setText(row_number, 2, u'пациенто-день', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Стационар дневного пребывания', blockFormat=fmtl)
        table.setText(row_number, 2, u'Случаи', blockFormat=fmtc)
        table.mergeCells(row_number, 4, 2, 1)
        table.mergeCells(row_number, 1, 2, 1)
        row_number += 1
        table.setText(row_number, 2, u'пациенто-день', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Диспансеризация пребывающих в стационарных учреждениях детей-сирот и детей, находящихся в трудной жизненной ситуации', blockFormat=fmtl)
        table.setText(row_number, 2, u'посещение', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Диспансеризация детей-сирот и детей, оставшихся без попечения родителей, в том числе усыновленных (удочеренных), принятых под опеку (попечительство), в приемную или патронажную семью', blockFormat=fmtl)
        table.setText(row_number, 2, u'посещение', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Профилактические медицинские осмотры несовершеннолетних', blockFormat=fmtl)
        table.setText(row_number, 2, u'посещение', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Диспансеризация определенных групп взрослого населения', blockFormat=fmtl)
        table.setText(row_number, 2, u'посещение', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Профилактические медицинские осмотры взрослых', blockFormat=fmtl)
        table.setText(row_number, 2, u'посещение', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Посещение с профилактическими и иными целями', blockFormat=fmtl)
        table.setText(row_number, 2, u'посещение', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'в том числе разовые посещения по заболеванию', blockFormat=fmtl)
        table.setText(row_number, 2, u'посещение', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Обращения в связи с заболеваниями', blockFormat=fmtl)
        table.setText(row_number, 2, u'обращение', blockFormat=fmtc)
        table.mergeCells(row_number, 4, 2, 1)
        table.mergeCells(row_number, 1, 2, 1)
        row_number += 1
        table.setText(row_number, 2, u'посещение', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Поликлиника (прикрепленное население)', blockFormat=fmtl)
        table.setText(row_number, 2, u'человек', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Фельдшерско-акушерские пункты', blockFormat=fmtl)
        table.setText(row_number, 2, u'обращение', blockFormat=fmtc)
        table.mergeCells(row_number, 1, 3, 1)
        row_number += 1
        table.setText(row_number, 2, u'посещение', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 2, u'человек', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Неотложная помощь', blockFormat=fmtl)
        table.setText(row_number, 2, u'посещение', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Диагностические исследования, оплачиваемые по тарифам (лабораторные и инструментальные), в том числе:', blockFormat=fmtl)
        table.setText(row_number, 2, u'услуга', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'компьютерная томография', blockFormat=fmtl)
        table.setText(row_number, 2, u'услуга', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'магнитно-резонансная томография', blockFormat=fmtl)
        table.setText(row_number, 2, u'услуга', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'ультразвуковое исследование сердечно-сосудистой системы', blockFormat=fmtl)
        table.setText(row_number, 2, u'услуга', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'эндоскопические диагностические исследования', blockFormat=fmtl)
        table.setText(row_number, 2, u'услуга', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'молекулярно-генетические исследования с целью выявления онкологических заболеваний', blockFormat=fmtl)
        table.setText(row_number, 2, u'услуга', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'гистологические исследования с целью выявления онкологических заболеваний', blockFormat=fmtl)
        table.setText(row_number, 2, u'услуга', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Стоматология (посещение с профилактическими и иными целями)', blockFormat=fmtl)
        table.setText(row_number, 2, u'посещение', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'в том числе разовые посещения по заболеванию', blockFormat=fmtl)
        table.setText(row_number, 2, u'посещение', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Стоматология (обращения в связи с заболеваниями)', blockFormat=fmtl)
        table.setText(row_number, 2, u'обращение', blockFormat=fmtc)
        table.mergeCells(row_number, 4, 2, 1)
        table.mergeCells(row_number, 1, 2, 1)
        row_number += 1
        table.setText(row_number, 2, u'посещение', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Стоматология', blockFormat=fmtl)
        table.setText(row_number, 2, u'УЕТ', blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 1, u'Скорая медицинская помощь', blockFormat=fmtl)
        table.setText(row_number, 2, u'вызов', blockFormat=fmtc)
        table.mergeCells(row_number, 4, 2, 1)
        table.mergeCells(row_number, 1, 2, 1)
        row_number += 1
        table.setText(row_number, 2, u'человек', blockFormat=fmtc)

        invoiceDict = self.invoiceClass.getInvoiceDict()

        summ = 0.0
        # Стационар
        kolsn = 0
        kolkd = 0
        vpsumm = 0.0
        for key in reps:
            if key in ['11', '12', '301', '302', '401', '402']:
                kolsn += len(reps[key]['sn'][0]) + len(reps[key]['sn'][1])
                kolkd += reps[key]['kd'][0] + reps[key]['kd'][1]
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
        row_number = 2
        invoiceDict[u'Стационар'][u'kolsn'] += kolsn
        invoiceDict[u'Стационар'][u'kolkd'] += kolkd
        invoiceDict[u'Стационар'][u'vpsumm'] += vpsumm
        table.setText(row_number, 3, invoiceDict[u'Стационар'][u'kolsn'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Стационар'][u'vpsumm'], blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Стационар'][u'kolkd'], blockFormat=fmtc)
        summ += vpsumm

        # в т.ч. ВМП
        kolsn = 0
        kolkd = 0
        vpsumm = 0.0
        for key in reps:
            if key in ['401', '402']:
                kolsn += len(reps[key]['sn'][0]) + len(reps[key]['sn'][1])
                kolkd += reps[key]['kd'][0] + reps[key]['kd'][1]
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
        invoiceDict[u'ВМП'][u'kolsn'] += kolsn
        invoiceDict[u'ВМП'][u'kolkd'] += kolkd
        invoiceDict[u'ВМП'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'ВМП'][u'kolsn'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'ВМП'][u'vpsumm'], blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'ВМП'][u'kolkd'], blockFormat=fmtc)

        # Дневной стационар
        kolsn = 0
        kolkd = 0
        vpsumm = 0.0
        for key in reps:
            if key in ['41', '42', '43']:
                kolsn += len(reps[key]['sn'][0]) + len(reps[key]['sn'][1])
                kolkd += reps[key]['pd'][0] + reps[key]['pd'][1]
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
        invoiceDict[u'Дневной стационар'][u'kolsn'] += kolsn
        invoiceDict[u'Дневной стационар'][u'kolkd'] += kolkd
        invoiceDict[u'Дневной стационар'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Дневной стационар'][u'kolsn'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Дневной стационар'][u'vpsumm'], blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Дневной стационар'][u'kolkd'], blockFormat=fmtc)
        summ += vpsumm

        # ЭКО
        kolsn = 0
        kolkd = 0
        vpsumm = 0.0
        for key in reps:
            if key == '43':
                kolsn += len(reps[key]['sn'][0]) + len(reps[key]['sn'][1])
                kolkd += reps[key]['pd'][0] + reps[key]['pd'][1]
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
        invoiceDict[u'ЭКО'][u'kolsn'] += kolsn
        invoiceDict[u'ЭКО'][u'kolkd'] += kolkd
        invoiceDict[u'ЭКО'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'ЭКО'][u'kolsn'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'ЭКО'][u'vpsumm'], blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'ЭКО'][u'kolkd'], blockFormat=fmtc)

        # Стационар дневного пребывания
        kolsn = 0
        kolkd = 0
        vpsumm = 0.0
        for key in reps:
            if key in ['51', '52', '511', '522']:
                kolsn += len(reps[key]['sn'][0]) + len(reps[key]['sn'][1])
                kolkd += reps[key]['pd'][0] + reps[key]['pd'][1]
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
        invoiceDict[u'Стационар дневного пребывания'][u'kolsn'] += kolsn
        invoiceDict[u'Стационар дневного пребывания'][u'kolkd'] += kolkd
        invoiceDict[u'Стационар дневного пребывания'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Стационар дневного пребывания'][u'kolsn'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Стационар дневного пребывания'][u'vpsumm'], blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Стационар дневного пребывания'][u'kolkd'], blockFormat=fmtc)

        summ += vpsumm

        # Дисп. детей-сирот
        vpsumm = 0.0
        kolpos = 0
        for key in reps:
            if key == '232':
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['cp'][0] + reps[key]['cp'][1]
        invoiceDict[u'Дисп. детей-сирот'][u'kolpos'] += kolpos
        invoiceDict[u'Дисп. детей-сирот'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Дисп. детей-сирот'][u'kolpos'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Дисп. детей-сирот'][u'vpsumm'], blockFormat=fmtc)
        summ += vpsumm

        # Дисп. детей без попечения
        vpsumm = 0.0
        kolpos = 0
        for key in reps:
            if key == '252':
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['cp'][0] + reps[key]['cp'][1]
        invoiceDict[u'Дисп. детей без попечения'][u'kolpos'] += kolpos
        invoiceDict[u'Дисп. детей без попечения'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Дисп. детей без попечения'][u'kolpos'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Дисп. детей без попечения'][u'vpsumm'], blockFormat=fmtc)
        summ += vpsumm

        # Медосм. несовершеннолетних
        vpsumm = 0.0
        kolpos = 0
        for key in reps:
            if key == '262':
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['cp'][0] + reps[key]['cp'][1]
        invoiceDict[u'Медосм. несовершеннолетних'][u'kolpos'] += kolpos
        invoiceDict[u'Медосм. несовершеннолетних'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Медосм. несовершеннолетних'][u'kolpos'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Медосм. несовершеннолетних'][u'vpsumm'], blockFormat=fmtc)
        summ += vpsumm

        # Дисп. взрослых
        vpsumm = 0.0
        kolpos = 0
        for key in reps:
            if key in ['211', '233', '244']:
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['cp'][0] + reps[key]['cp'][1]
        invoiceDict[u'Дисп. взрослых'][u'kolpos'] += kolpos
        invoiceDict[u'Дисп. взрослых'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Дисп. взрослых'][u'kolpos'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Дисп. взрослых'][u'vpsumm'], blockFormat=fmtc)
        summ += vpsumm

        # Медосм. взрослых
        vpsumm = 0.0
        kolpos = 0
        for key in reps:
            if key == '261':
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['cp'][0] + reps[key]['cp'][1]
        invoiceDict[u'Медосм. взрослых'][u'kolpos'] += kolpos
        invoiceDict[u'Медосм. взрослых'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Медосм. взрослых'][u'kolpos'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % forceInt(invoiceDict[u'Медосм. взрослых'][u'vpsumm']), blockFormat=fmtc)
        summ += vpsumm

        # Посещения с профилактическими и иными целями
        vpsumm = 0.0
        kolpos = 0
        obr = 0
        cpo = 0
        cpotw = 0
        sum_pos = sum_obr = 0
        sum_posotw = 0

        for key in reps:
            if key in ['01', '02', '21', '22', '271', '272', '281', '282']:
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['cp'][0] + reps[key]['cp'][1]
                cpo += reps[key]['cpo'][0] + reps[key]['cpo'][1]
                obr += reps[key]['obr'][0] + reps[key]['obr'][1]
                sum_pos += reps[key]['sum_pos']
                cpotw += reps[key]['cpotw'][0] + reps[key]['cpotw'][1]
                sum_posotw += reps[key]['sum_posotw'][0] + reps[key]['sum_posotw'][1]
                sum_obr += reps[key]['sum_obr']
        invoiceDict[u'Посещения с профилактическими и иными целями'][u'vpsumm'] += vpsumm
        invoiceDict[u'Посещения с профилактическими и иными целями'][u'kolpos'] += kolpos
        invoiceDict[u'Посещения с профилактическими и иными целями'][u'obr'] += obr
        invoiceDict[u'Посещения с профилактическими и иными целями'][u'cpo'] += cpo
        invoiceDict[u'Посещения с профилактическими и иными целями'][u'cpotw'] += cpotw
        invoiceDict[u'Посещения с профилактическими и иными целями'][u'sum_pos'] += sum_pos
        invoiceDict[u'Посещения с профилактическими и иными целями'][u'sum_posotw'] += sum_posotw
        invoiceDict[u'Посещения с профилактическими и иными целями'][u'sum_obr'] += sum_obr
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Посещения с профилактическими и иными целями'][u'kolpos'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Посещения с профилактическими и иными целями'][u'sum_pos'], blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Посещения с профилактическими и иными целями'][u'cpotw'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Посещения с профилактическими и иными целями'][u'sum_posotw'], blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Посещения с профилактическими и иными целями'][u'obr'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Посещения с профилактическими и иными целями'][u'sum_obr'], blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Посещения с профилактическими и иными целями'][u'cpo'], blockFormat=fmtc)
        summ += vpsumm

        # Поликлиника (прикрепленное население)
        vpsumm = 0.0
        fl = 0
        for key in reps:
            if key in ['271', '272']:
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                fl += len(reps[key]['fl'][0]) + len(reps[key]['fl'][1])
        row_number += 1
        table.setText(row_number, 3, fl, blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % 0, blockFormat=fmtc)
        summ += vpsumm
        invoiceDict[u'Поликлиника (прикрепленное население)'][u'fl'] += fl
        invoiceDict[u'Поликлиника (прикрепленное население)'][u'vpsumm'] += vpsumm

        # ФАП
        vpsumm = 0.0
        kolpos = 0
        obr = 0
        cpo = 0
        cpotw = 0
        sum_pos = sum_obr = 0
        sum_posotw = 0
        fl = 0

        for key in reps:
            if key == 'FAP':
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['cp'][0] + reps[key]['cp'][1]
                cpo += reps[key]['cpo'][0] + reps[key]['cpo'][1]
                obr += reps[key]['obr'][0] + reps[key]['obr'][1]
                sum_pos += reps[key]['sum_pos']
                cpotw += reps[key]['cpotw'][0] + reps[key]['cpotw'][1]
                sum_posotw += reps[key]['sum_posotw'][0] + reps[key]['sum_posotw'][1]
                sum_obr += reps[key]['sum_obr']
                fl += len(reps[key]['fl'][0]) + len(reps[key]['fl'][1])
        invoiceDict[u'ФАП'][u'vpsumm'] += vpsumm
        invoiceDict[u'ФАП'][u'kolpos'] += kolpos
        invoiceDict[u'ФАП'][u'obr'] += obr
        invoiceDict[u'ФАП'][u'cpo'] += cpo
        invoiceDict[u'ФАП'][u'cpotw'] += cpotw
        invoiceDict[u'ФАП'][u'sum_pos'] += sum_pos
        invoiceDict[u'ФАП'][u'sum_posotw'] += sum_posotw
        invoiceDict[u'ФАП'][u'fl'] += fl
        invoiceDict[u'ФАП'][u'sum_obr'] += sum_obr
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'ФАП'][u'obr'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'ФАП'][u'sum_obr'], blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'ФАП'][u'kolpos'] + invoiceDict[u'ФАП'][u'cpo'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'ФАП'][u'sum_pos'], blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'ФАП'][u'fl'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % 0, blockFormat=fmtc)
        summ += vpsumm


        # Неотложная помощь
        vpsumm = 0.0
        kolpos = 0
        for key in reps:
            if key in ['111', '112', '241', '242']:
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['cp'][0] + reps[key]['cp'][1]
        invoiceDict[u'Неотложная помощь'][u'kolpos'] += kolpos
        invoiceDict[u'Неотложная помощь'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Неотложная помощь'][u'kolpos'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Неотложная помощь'][u'vpsumm'], blockFormat=fmtc)
        summ += vpsumm

        # Диагностические исследования (лабораторные исследования)
        vpsumm = 0.0
        kolpos = 0
        for key in reps:
            if key in ['80', 'au', 'bu', 'cu', 'du', 'ae', 'be', 'ce', 'de', 'ag', 'bg', 'cg', 'dg', 'ah', 'bh', 'ch', 'dh', 'av', 'bv', 'cv', 'dv']:
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['kolu'][0] + reps[key]['kolu'][1]
            if key in ['ak', 'bk', 'ck', 'dk', 'am', 'bm', 'cm', 'dm']:
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['cpo'][0] + reps[key]['cpo'][1] + reps[key]['cp'][0] + reps[key]['cp'][1]
        invoiceDict[u'Диагностические исследования (лабораторные исследования)'][u'kolpos'] += kolpos
        invoiceDict[u'Диагностические исследования (лабораторные исследования)'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Диагностические исследования (лабораторные исследования)'][u'kolpos'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Диагностические исследования (лабораторные исследования)'][u'vpsumm'], blockFormat=fmtc)
        summ += vpsumm

        # КТ
        vpsumm = 0.0
        kolpos = 0
        for key in reps:
            if key in ['ak', 'bk', 'ck', 'dk']:
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['cpo'][0] + reps[key]['cpo'][1] + reps[key]['cp'][0] + reps[key]['cp'][1]
        invoiceDict[u'КТ'][u'kolpos'] += kolpos
        invoiceDict[u'КТ'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'КТ'][u'kolpos'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'КТ'][u'vpsumm'], blockFormat=fmtc)
        # summ += vpsumm

        # МРТ
        vpsumm = 0.0
        kolpos = 0
        for key in reps:
            if key in ['am', 'bm', 'cm', 'dm']:
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['cpo'][0] + reps[key]['cpo'][1] + reps[key]['cp'][0] + reps[key]['cp'][1]
        invoiceDict[u'МРТ'][u'kolpos'] += kolpos
        invoiceDict[u'МРТ'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'МРТ'][u'kolpos'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'МРТ'][u'vpsumm'], blockFormat=fmtc)
        # summ += vpsumm

        # УЗИ ССС
        vpsumm = 0.0
        kolpos = 0
        for key in reps:
            if key in ['au', 'bu', 'cu', 'du']:
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['kolu'][0] + reps[key]['kolu'][1]
        invoiceDict[u'УЗИ ССС'][u'kolpos'] += kolpos
        invoiceDict[u'УЗИ ССС'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'УЗИ ССС'][u'kolpos'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'УЗИ ССС'][u'vpsumm'], blockFormat=fmtc)
        # summ += vpsumm

        # Эндоскопия
        vpsumm = 0.0
        kolpos = 0
        for key in reps:
            if key in ['ae', 'be', 'ce', 'de']:
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['kolu'][0] + reps[key]['kolu'][1]
        invoiceDict[u'Эндоскопия'][u'kolpos'] += kolpos
        invoiceDict[u'Эндоскопия'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Эндоскопия'][u'kolpos'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Эндоскопия'][u'vpsumm'], blockFormat=fmtc)
        # summ += vpsumm

        # МГИ
        vpsumm = 0.0
        kolpos = 0
        for key in reps:
            if key in ['ag', 'bg', 'cg', 'dg']:
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['kolu'][0] + reps[key]['kolu'][1]
        invoiceDict[u'МГИ'][u'kolpos'] += kolpos
        invoiceDict[u'МГИ'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'МГИ'][u'kolpos'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'МГИ'][u'vpsumm'], blockFormat=fmtc)
        # summ += vpsumm

        # Гистология
        vpsumm = 0.0
        kolpos = 0
        for key in reps:
            if key in ['ah', 'bh', 'ch', 'dh']:
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                kolpos += reps[key]['kolu'][0] + reps[key]['kolu'][1]
        invoiceDict[u'Гистология'][u'kolpos'] += kolpos
        invoiceDict[u'Гистология'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Гистология'][u'kolpos'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Гистология'][u'vpsumm'], blockFormat=fmtc)
        # summ += vpsumm

        # Стоматология
        kolpos = 0
        vpsumm = 0.0
        uet = 0.0
        obr = 0
        cpo = 0
        cpotw = 0
        for key in reps:
            if key in ['31', '32']:
                kolpos += reps[key]['cp'][0] + reps[key]['cp'][1]
                vpsumm += reps[key]['summ'][0] + reps[key]['summ'][1]
                uet += reps[key]['uet'][0] + reps[key]['uet'][1]
                obr += reps[key]['obr'][0] + reps[key]['obr'][1]
                cpo += reps[key]['cpo'][0] + reps[key]['cpo'][1]
                cpotw += reps[key]['cpotw'][0] + reps[key]['cpotw'][1]
        invoiceDict[u'Стоматология'][u'vpsumm'] += vpsumm
        invoiceDict[u'Стоматология'][u'kolpos'] += kolpos
        invoiceDict[u'Стоматология'][u'uet'] += uet
        invoiceDict[u'Стоматология'][u'obr'] += obr
        invoiceDict[u'Стоматология'][u'cpo'] += cpo
        invoiceDict[u'Стоматология'][u'cpotw'] += cpotw
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Стоматология'][u'kolpos'], blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Стоматология'][u'cpotw'], blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Стоматология'][u'obr'], blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Стоматология'][u'cpo'], blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 3, '%.2f' % invoiceDict[u'Стоматология'][u'uet'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Стоматология'][u'vpsumm'], blockFormat=fmtc)
        summ += vpsumm


        # Скорая
        vpsumm = 0.0
        kolpos = 0
        # for rep in reps:
        #     if rep['vp'] in ('801', '802'):
        #         vpsumm += rep['tsumm']
        #         kolpos += rep['tcp']
        invoiceDict[u'Скорая'][u'kolpos'] += kolpos
        invoiceDict[u'Скорая'][u'vpsumm'] += vpsumm
        row_number += 1
        table.setText(row_number, 3, invoiceDict[u'Скорая'][u'kolpos'], blockFormat=fmtc)
        table.setText(row_number, 4, '%.2f' % invoiceDict[u'Скорая'][u'vpsumm'], blockFormat=fmtc)
        row_number += 1
        table.setText(row_number, 3, 0, blockFormat=fmtc)
        summ += vpsumm
        invoiceDict[u'summ'] += summ

        invoice_cursor.movePosition(QtGui.QTextCursor.End)
        fmt = QtGui.QTextBlockFormat()
        fmt.setAlignment(Qt.AlignLeft)
        invoice_cursor.insertBlock(fmt)
        invoice_cursor.insertHtml(u"<br><b>Итого:</b> <u><i>%s (%s)</i></u>" % (invoiceDict[u'summ'], amountToWords(invoiceDict[u'summ'])))
        invoice_cursor.movePosition(QtGui.QTextCursor.End)
        self.invoiceClass.setInvoice(invoice)
        self.invoiceClass.setInvoiceDict(invoiceDict)
        self.parent.close()

# *****************************************************************************************

    def createDbf(self):
        if self.exportType in [self.exportTypeP25, self.exportTypePreControlP25, self.exportTypeInvoice]:
            return (self.createDbfP(), self.createDbfU(),
                    self.createDbfD(), self.createDbfN(), self.createDbfR(),
                    self.createDbfO(), self.createDbfI(), self.createDbfC())
        else:
            return self.createDbfFLK()


    def createDbfP(self):
        u"""Паспортная часть"""
        dbfName = os.path.join(self.getTmpDir(), 'P' + self.getDbfBaseName())
        dbf = Dbf(dbfName, new=True, encoding='cp866')
        dbf.addField(
            ('NS', 'N', 5, 0),  # номер реестра счетов
            ('VS', 'C', 2),  # тип реестра счетов
            ('DATS', 'D'),  # дата формирования реестра счетов
            ('SN', 'N', 12, 0),  # номер персонального счета
            ('DATPS', 'D'),  # дата формирования персонального счета
            ('CODE_MO', 'C', 5),  # код МО, оказавшей медицинскую помощь
            ('PL_OGRN', 'C', 15),  # ОГРН плательщика
            ('FIO', 'C', 30),  # фамилия
            ('IMA', 'C', 25),  # имя
            ('OTCH', 'C', 30),  # отчество
            ('POL', 'C', 1),  # пол (М/Ж)
            ('DATR', 'D'),  # дата рождения
            ('KAT', 'C', 1),  # категория граждан
            ('SNILS', 'C', 14), # СНИЛС (ХХХ-ХХХ-ХХХ ХХ)
            ('OKATO_OMS', 'C', 5),  # код ОКАТО территории страхования по ОМС
            ('SPV', 'N', 1),  # тип ДПФС
            ('SPS', 'C', 10),  # серия ДПФС
            ('SPN', 'C', 20),  # номер ДПФС
            ('INV', 'C', 1),  # группа инвалидности
            ('MSE', 'C', 1),  # направление на МСЭ
            ('Q_G', 'C', 10),  # признак "Особый случай" при регистрации обращения за медицинской помощью
            ('NOVOR', 'C', 9),  # признак новорожденного
            ('VNOV_D', 'N', 10, 0),  # вес при рождении
            ('FAMP', 'C', 30),  # фамилия представителя пациента
            ('IMP', 'C', 20),  # имя представителя пациента
            ('OTP', 'C', 30),  # отчество представителя пациента
            ('POLP', 'C', 1),  # пол представителя пациента (М/Ж)
            ('DATRP', 'D'),  # дата рождения представителя пациента
            ('C_DOC', 'N', 2),  # код типа УДЛ
            ('S_DOC', 'C', 10),  # серия УДЛ
            ('N_DOC', 'C', 15),  # номер УДЛ
            ('NAPR_MO', 'C', 6),  # код направившей МО
            ('NAPR_N', 'C', 15),  # номер направления
            ('NAPR_D', 'D'),  # дата выдачи направления
            ('NAPR_DP', 'D'),  # дата планируемой госпитализации
            ('TAL_N', 'C', 18),  # номер талона на ВМП
            ('TAL_D', 'D'),  # дата выдачи талона на ВМП
            ('PR_D_N', 'C', 1),  # признак диспансерного наблюдения по поводу основного заболевания
            ('PR_DS_N', 'C', 1),  # признак диспансерного наблюдения по поводу сопутствующего заболевания
            ('DATN', 'D'),  # дата начала лечения
            ('DATO', 'D'),  # дата окончания лечения
            ('ISHL', 'C', 3),  # код исхода заболевания
            ('ISHOB', 'C', 3),  # код исхода обращения
            ('MP', 'C', 1),  # код формы обращения
            ('DOC_SS', 'C', 14),  # СНИЛС врача закрывшего талон/историю/карту
            ('SPEC', 'C', 9),  # код специальности врача закрывшего талон/историю
            ('PROFIL', 'C', 3),  # профиль оказанной медицинской помощи
            ('MKBX', 'C', 6),  # код диагноза основного заболевания по МКБ–Х
            ('MKBXS', 'C', 6),  # код диагноза сопутствующего заболевания по МКБ–Х
            ('DS_ONK', 'C', 1),  # признак подозрения на злокачественное новообразование
            ('MKBX_PR', 'C', 1),  # Признак впервые установленного диагноза основного заболевания
            ('VMP', 'C', 2),  # вид медицинской помощи
            ('KSO', 'C', 2),  # способ оплаты медицинской помощи
            ('P_CEL', 'C', 4),  # цель посещения
            ('VB_P', 'C', 1),  # признак внутрибольничного перевода
            ('PV', 'C', 40),  # коды причин возврата
            ('DVOZVRAT', 'D'),  # дата возврата
            ('RKEY', 'C', 50),  # ключ записи
            ('FKEY', 'C', 50)  # ключ записи ФЛК
            )
        return dbf


    def createDbfFLK(self):
        u"""Паспортная часть(ФЛК)"""
        dbfName = os.path.join(self.getTmpDir(), 'P' + self.getDbfBaseName())
        dbf = Dbf(dbfName, new=True, encoding='cp866')
        if self.exportType == self.exportTypeFLK:
            dbf.addField(
                ('NS', 'N', 5, 0),  # номер реестра счетов
                ('VS', 'C', 2),  # тип реестра счетов
                ('DATS', 'D'),  # дата формирования реестра счетов
                ('SN', 'N', 12, 0),  # номер персонального счета
                ('DATPS', 'D'))  # дата формирования персонального счета

        if self.exportType == self.exportTypeAttachments:
            dbf.addField(
                ('CODE_MO', 'C', 5),  # код МО, оказавшей медицинскую помощь
                ('PL_OGRN', 'C', 15),  # ОГРН плательщика
                ('FIO', 'C', 30),  # фамилия
                ('IMA', 'C', 25),  # имя
                ('OTCH', 'C', 30),  # отчество
                ('POL', 'C', 1),  # пол (М/Ж)
                ('DATR', 'D'),  # дата рождения
                ('SNILS', 'C', 14),  # СНИЛС (ХХХ-ХХХ-ХХХ ХХ)
                ('locAddress', 'C', 250),  #
                ('regAddress', 'C', 250),  #
                ('OKATO_OMS', 'C', 5),  # код ОКАТО территории страхования по ОМС
                ('SPV', 'N', 1),  # тип ДПФС
                ('SPS', 'C', 10),  # серия ДПФС
                ('SPN', 'C', 20),  # номер ДПФС
                ('Q_G', 'C', 10),  # признак "Особый случай"
                ('FAMP', 'C', 30),  # фамилия представителя пациента
                ('IMP', 'C', 20),  # имя представителя пациента
                ('OTP', 'C', 30),  # отчество представителя пациента
                ('POLP', 'C', 1),  # пол представителя пациента (М/Ж)
                ('DATRP', 'D'),  # дата рождения представителя пациента
                ('C_DOC', 'N', 2),  # код типа УДЛ
                ('S_DOC', 'C', 10),  # серия УДЛ
                ('N_DOC', 'C', 15),  # номер УДЛ
                ('DATN', 'D'),  # дата начала лечения
                ('DATO', 'D'),  # дата окончания лечения
            )
            return dbf

        dbf.addField(
            ('CODE_MO', 'C', 5),  # код МО, оказавшей медицинскую помощь
            ('PL_OGRN', 'C', 15),  # ОГРН плательщика
            ('FIO', 'C', 30),  # фамилия
            ('IMA', 'C', 25),  # имя
            ('OTCH', 'C', 30),  # отчество
            ('POL', 'C', 1),  # пол (М/Ж)
            ('DATR', 'D'),  # дата рождения
            ('SNILS', 'C', 14),  # СНИЛС (ХХХ-ХХХ-ХХХ ХХ)
            ('OKATO_OMS', 'C', 5),  # код ОКАТО территории страхования по ОМС
            ('SPV', 'N', 1),  # тип ДПФС
            ('SPS', 'C', 10),  # серия ДПФС
            ('SPN', 'C', 20),  # номер ДПФС
            ('Q_G', 'C', 10),  # признак "Особый случай"
            ('FAMP', 'C', 30),  # фамилия представителя пациента
            ('IMP', 'C', 20),  # имя представителя пациента
            ('OTP', 'C', 30),  # отчество представителя пациента
            ('POLP', 'C', 1),  # пол представителя пациента (М/Ж)
            ('DATRP', 'D'),  # дата рождения представителя пациента
            ('C_DOC', 'N', 2),  # код типа УДЛ
            ('S_DOC', 'C', 10),  # серия УДЛ
            ('N_DOC', 'C', 15),  # номер УДЛ
            ('DATN', 'D'),  # дата начала лечения
            ('DATO', 'D'),  # дата окончания лечения
            ('FKEY', 'C', 50)  # значение ключа записи
        )
        return dbf


    def createDbfU(self):
        u"""Создает структуру dbf для медицинских услуг."""
        dbfName = os.path.join(self.getTmpDir(), 'U' + self.getDbfBaseName())
        dbf = Dbf(dbfName, new=True, encoding='cp866')
        dbf.addField(
            ('UID', 'N', 14),  # уникальный номер записи об оказанной медицинской услуге в пределах реестра
            ('CODE_MO', 'C', 5),  # код МО, оказавшей медицинскую помощь
            ('NS', 'N', 5, 0),  # номер реестра счетов
            ('SN', 'N', 12, 0),  # номер персонального счета
            ('ISTI', 'C', 20),  # номер талона амбулаторного пациента / истории болезни / карты вызова СМП
            ('P_PER', 'C', 1),  # признак поступления / перевода в отделение
            ('KOTD', 'C', 4),  # код отделения
            ('KPK', 'C', 2),  # код профиля койки
            ('MKBX', 'C', 6),  # код диагноза основного заболевания по МКБ–Х
            ('MKBXS', 'C', 6),  # код диагноза сопутствующего заболевания по МКБ–Х
            ('MKBXS_PR', 'C', 1),  # признак впервые установленного диагноза сопутствующего заболевания
            ('PR_MS_N', 'C', 1),   # признак диспансерного наблюдения по поводу сопутствующего заболевания
            ('MKBXO', 'C', 6),  # код диагноза осложнения заболевания по МКБ–Х
            ('C_ZAB', 'C', 1),  # характер основного заболевания
            ('VP', 'C', 3),  # код условия оказания медицинской помощи
            ('KRIT', 'C', 9),  # оценка состояния пациента по шкалам или схема лечения или длительность непрерывного проведения ИВЛ
            ('KRIT2', 'C', 9),  # схема лекарственной терапии(только для комбинированных схем лечения)
            ('KSLP', 'C', 40),  # список примененных КСЛП
            ('KSLP_IT', 'N', 4, 2),  # итоговое значение КСЛП для услуги КСГ рассчитанное в соответствии с Тарифным соглашением
            ('KUSL', 'C', 15),  # код медицинской услуги
            ('KOLU', 'N', 3, 0),  # количество услуг
            ('KD', 'N', 3, 0),  # количество койко-дней (дней лечения)
            ('DATN', 'D'),  # дата начала выполнения услуги
            ('DATO', 'D'),  # дата окончания выполнения услуги
            ('TARU', 'N', 10, 2),  # тариф на оплату по ОМС
            ('SUMM', 'N', 14, 2),  # сумма к оплате по ОМС
            ('IS_OUT', 'N', 1, 0),  # причины невыполнения медицинской услуги
            ('OUT_MO', 'C', 5),  # код МО, оказавшей услугу
            ('DOC_SS', 'C', 14),  # СНИЛС врача оказавшего услугу
            ('SPEC', 'C', 9),  # код специальности специалиста, оказавшего услугу
            ('PROFIL', 'C', 3),  # профиль оказанной медицинской помощи
            ('VMP', 'C', 2),  # вид медицинской помощи
            ('COMMENT', 'C', 10),
            ('DS_ONK', 'C', 1),  # признак подозрения на злокачественное новообразование
            ('USL_TIP', 'C', 1),  # тип лечения
            ('HIR_TIP', 'C', 2),  # тип хирургического лечения
            ('LEK_TIPL', 'C', 2),  # линия лекарственнои терапии
            ('LEK_TIPV', 'C', 2),  # цикл лекарственной терапии
            ('LUCH_TIP', 'C', 2),  # тип лучевой терапии
            ('RKEY', 'C', 50),  # значение ключа записи
            )
        if self.exportType == self.exportTypeInvoice:
            dbf.addField(('K3', 'N', 14, 2), ('K0', 'N', 14, 2), ('hasK0', 'N', 1))
        return dbf


    def createDbfD(self):
        u"""Медицинские работники"""
        dbfName = os.path.join(self.getTmpDir(), 'D' + self.getDbfBaseName())
        dbf = Dbf(dbfName, new=True, encoding='cp866')
        dbf.addField(
            ('CODE_MO', 'C', 5),  # код МО, оказавшей медицинскую помощь
            ('SNILS', 'C', 14),  # СНИЛС (ХХХ-ХХХ-ХХХ ХХ)
            ('FIO', 'C', 30),  # фамилия медицинского работника
            ('IMA', 'C', 20),  # имя медицинского работника
            ('OTCH', 'C', 30),  # отчество медицинского работника
            ('POL', 'C', 1),  # пол (М/Ж)
            ('DATR', 'D'),  # дата рождения
            ('DATN', 'D'),  # дата устройства на работу
            ('DATO', 'D'),  # дата увольнения
            ('RKEY', 'C', 50)  # значение ключа записи
            )
        return dbf


    def createDbfN(self):
        u"""Направления на плановую госпитализацию и исследования"""
        dbfName = os.path.join(self.getTmpDir(), 'N' + self.getDbfBaseName())
        dbf = Dbf(dbfName, new=True, encoding='cp866')
        dbf.addField(
            ('CODE_MO', 'C', 5),  # код МО, оказавшей медицинскую помощь и выдавшей направление
            ('NS', 'N', 5, 0),  # номер реестра счетов
            ('SN', 'N', 12, 0),  # номер персонального счета
            ('NAPR_N', 'C', 15),  # номер направления, (ККККК_ХХХХХХХ)
            ('NAPR_MO', 'C', 5),  # код МО, в которое направлен пациент
            ('NAPR_D', 'D'),  # дата направления
            ('DOC_SS', 'C', 14),  # СНИЛС врача сотрудника, выдавшего направление
            ('RKEY', 'C', 50)  # значение ключа записи
            )
        return dbf


    def createDbfR(self):
        u"""Назначения лечащего врача, по результатам проведенных профилактических мероприятий или направления,
        оформленные при подозрении на злокачественное новообразование"""
        dbfName = os.path.join(self.getTmpDir(), 'R' + self.getDbfBaseName())
        dbf = Dbf(dbfName, new=True, encoding='cp866')
        dbf.addField(
            ('RID', 'N', 14),  # уникальный номер записи в пределах реестра
            ('CODE_MO', 'C', 5),  # код МО, оказавшей медицинскую помощь
            ('NS', 'N', 5, 0),  # номер реестра счетов
            ('SN', 'N', 12, 0),  # номер персонального счета
            ('UID', 'N', 14, 0),  # уникальный номер записи об оказанной медицинской услуге в пределах реестра, по результатам оказания которой оформлено назначение (направление)
            ('NAZR_D', 'D'),  # дата назначения (направления)
            ('NAPR_MO', 'C', 6),  # код МО, куда оформлено направление
            ('NAZR', 'C', 2),  # вид назначения (направления)
            ('SPEC', 'C', 9),  # специальность врача, к которому направлен за консультацией
            ('VID_OBS', 'C', 2),  # вид назначенного обследования
            ('PROFIL', 'C', 3),  # профиль назначенной медицинской помощи
            ('KPK', 'C', 3),  # код профиля койки
            ('NAPR_USL', 'C', 15),  # код медицинской услуги (обследования)
            ('RKEY', 'C', 50)  # значение ключа записи
            )
        return dbf


    def createDbfO(self):
        u"""Сведения о случае лечения онкологического заболевания"""
        dbfName = os.path.join(self.getTmpDir(), 'O' + self.getDbfBaseName())
        dbf = Dbf(dbfName, new=True, encoding='cp866')
        dbf.addField(
            ('OID', 'N', 14),  # уникальный номер записи в пределах реестра
            ('CODE_MO', 'C', 5),  # код МО, оказавшей медицинскую помощь
            ('NS', 'N', 5, 0),  # номер реестра счетов
            ('SN', 'N', 12, 0),  # номер персонального счета
            ('UID', 'N', 14, 0),  # уникальный номер записи об оказанной медицинской услуге (КСГ, ВМП) в пределах реестра
            ('DS1_T', 'C', 2),  # повод обращения
            ('PR_CONS', 'C', 1),  # сведения о проведении консилиума
            ('D_CONS', 'D'),  # дата проведения консилиума
            ('STAD', 'C', 3),  # код стадии заболевания
            ('ONK_T', 'C', 4),  # идентификатор Tumor
            ('ONK_N', 'C', 4),  # идентификатор Nodus
            ('ONK_M', 'C', 4),  # идентификатор Metastasis
            ('MTSTZ', 'C', 1),  # признак выявления отдаленных метастазов
            ('SOD', 'N', 6, 2),  # суммарная очаговая доза
            ('REGNUM', 'C', 6),  # Идентификатор лекарственного препарата, применяемого при проведении лекарственной противоопухолевой терапии
            ('CODE_SH', 'C', 10), # Код схемы лекарственной терапии
            ('DATE_INJ', 'D'),  # Дата введения лекарственного препарата
            ('PPTR', 'N', 1, 0),  # Признак проведения профилактики тошноты и рвотного рефлекса
            ('K_FR', 'N', 2, 0),  # Количество фракций проведения лучевой терапии
            ('WEI', 'N', 5, 1),  # Масса тела(кг)
            ('HEI', 'N', 3, 0),  # Рост (см)
            ('BSA', 'N', 4, 2),  # Количество фракций проведения лучевой терапии
            ('RKEY', 'C', 50)  # значение ключа записи
            )
        return dbf


    def createDbfI(self):
        u"""Сведения о проведенных исследованиях и их результатах"""
        dbfName = os.path.join(self.getTmpDir(), 'I' + self.getDbfBaseName())
        dbf = Dbf(dbfName, new=True, encoding='cp866')
        dbf.addField(
            ('IID', 'N', 14),  # уникальный номер записи в пределах реестра
            ('CODE_MO', 'C', 5),  # код МО, оказавшей медицинскую помощь
            ('NS', 'N', 5, 0),  # номер реестра счетов
            ('SN', 'N', 12, 0),  # номер персонального счета
            ('UID', 'N', 14, 0),  # уникальный номер записи сведений о случае лечения онкологического заболевания)
            ('DIAG_D', 'D'),  # дата взятия материала при проведении диагностики
            ('DIAG_TIP', 'C', 1),  # тип диагностического показателя
            ('DIAG_CODE', 'C', 3),  # идентификатор признака/маркёра
            ('DIAG_RSLT', 'C', 3),  # идентифкатор результата диагностики
            ('RKEY', 'C', 50)  # значение ключа записи
            )
        return dbf


    def createDbfC(self):
        u"""Сведения об имеющихся противопоказаниях а проведению определенных типов лечения или отказах пациента от проведения определенных типов лечения"""
        dbfName = os.path.join(self.getTmpDir(), 'C' + self.getDbfBaseName())
        dbf = Dbf(dbfName, new=True, encoding='cp866')
        dbf.addField(
            ('CID', 'N', 14),  # уникальный номер записи в пределах реестра
            ('CODE_MO', 'C', 5),  # код МО, оказавшей медицинскую помощь
            ('NS', 'N', 5, 0),  # номер реестра счетов
            ('SN', 'N', 12, 0),  # номер персонального счета
            ('OID', 'N', 14, 0),  # уникальный номер записи сведений о случае лечения онкологического заболевания
            ('PROT', 'C', 2),  # код противопоказания или отказа
            ('D_PROT', 'D'),  # дата регистрации противопоказания или отказа
            ('RKEY', 'C', 50)  # значение ключа записи
            )
        return dbf


    def createQuery(self):
        if self.exportType in [self.exportTypeP25, self.exportTypePreControlP25, self.exportTypeFLK, self.exportTypeInvoice]:
            return (self.createQueryAccount(), self.createQueryPerson())
        elif self.exportType == self.exportTypeAttachments:
            return (self.createQueryFLKp())


    def createQueryAccount(self):
        tableAccountItem = self.db.table('Account_Item')
        cond = [tableAccountItem['deleted'].eq(0)]
        if self.exportType == self.exportTypeFLK:
            cond.append(tableAccountItem['master_id'].inlist(self.selectedAccountIds))
        else:
            cond.append(tableAccountItem['master_id'].eq(self.currentAccountId))

        stmt = u"""SELECT
  Account_Item.id AS accountItemId,
  Account_Item.master_id AS accountId,
  Account_Item.event_id AS event_id,
  COALESCE(Account_Item.action_id, Account_Item.visit_id, Account_Item.eventCSG_id, Account_Item.event_id) AS UID,
  Account_Item.UET AS UET,
  rbAccountType.regionalCode as accTypeCode,
  Event.client_id AS client_id,
  CASE Event.`order` 
    WHEN 1 then '1'
    WHEN 6 then '8'
    ELSE '2' END AS MP,
  Event.setDate AS begDate,
  Event.execDate AS endDate,
  Client.lastName AS lastName,
  Client.firstName AS firstName,
  Client.patrName AS patrName,
  Client.birthDate AS birthDate,
  Client.birthWeight AS birthWeight,
  Client.birthNumber,
  Client.sex AS sex,
  Client.SNILS AS SNILS,
  ClientPolicy.Serial AS policySerial,
  ClientPolicy.number AS policyNumber,
  Insurer.OKATO AS insurerOKATO,
  Insurer.id AS insurerId,
  Payer.OGRN AS payerOGRN,
  rbPolicyKind.regionalCode AS policyKindCode,
  ClientDocument.Serial AS documentSerial,
  ClientDocument.number AS documentNumber,
  rbDocumentType.regionalCode AS documentRegionalCode,
  IF((ClientWork.org_id is not null or IFNULL(ClientWork.freeInput, '') <> '') and IFNULL(ClientWork.post, '') <> '', 1, 0) AS KAT,
  IF(Account_Item.service_id IS NOT NULL,
  rbItemService.infis,
  IF(Account_Item.visit_id IS NOT NULL, rbVisitService.infis, rbEventService.infis)
  ) AS service,
  ExecPerson.SNILS AS execPersonSNILS,
  Visit.date AS visitDate,
  Action.begDate AS actionDate,
  Action.endDate AS actionEndDate,
  Diagnosis.MKB AS MKBXP,
  IF(rbEventProfile.regionalCode IN ('102', '103', '8008', '8009', '8010', '8011', '8012', '8013', '8014', '8015', '8016', '8017', '8018', '8019', '8020', '8021', '8022')
  OR mt.regionalCode IN ('31', '32'), IF(IFNULL(Action.MKB, '') <> '', Action.MKB, Diagnosis.MKB), Diagnosis.MKB) AS MKB,
  rbDiseasePhases.code as phasesCode,
  AssociatedDiagnosis.MKB as MKBXSP,
  /*для стоматологии выгружаем сопутствующий по особым правилам*/
  IF(mt.regionalCode IN ('31', '32'), IF(COALESCE(rbItemService.infis, rbVisitService.infis, rbEventService.infis) LIKE 'B%%', (SELECT
      MIN(a.MKB)
    FROM Account_Item ai
      LEFT JOIN Action a
        ON a.id = ai.action_id
      LEFT JOIN rbService s
        ON s.id = ai.service_id
    WHERE ai.master_id = Account_Item.master_id
    AND ai.event_id = Account_Item.event_id
    AND ai.deleted = 0
    AND a.endDate = Action.endDate
    AND s.infis LIKE 'A%%'
    AND IFNULL(a.MKB, '') <> ''
    AND a.MKB <> IF(IFNULL(Action.MKB, '') <> '', Action.MKB, Diagnosis.MKB)), NULL),
     /*для всех остальных сопутствующий выгружаем только для услуг приема ответственного*/
     IF(ExecPerson.id = Person.id and (LEFT(rbItemService.infis,1) = 'B' AND rbItemService.name like '%%прием%%' or LEFT(rbItemService.infis, 1) in ('G','V')), AssociatedDiagnosis.MKB, NULL)) AS AssociatedMKB,
  SeqDiagnosis.MKB AS SeqMKB,
  Account_Item.price AS price,
  Account_Item.amount AS amount,
  Account_Item.sum AS sum,
  Account_Item.note,
  Person.SNILS AS personSNILS,
  case when Account_Item.serviceDate >= '2018-04-01' then rbSpeciality.regionalCode else rbSpeciality.federalCode end AS specialityCode,
  rbSpeciality.isHigh as specialityIsHigh,
  case when Event.execDate >= '2018-04-01' then PersonSpeciality.regionalCode else PersonSpeciality.federalCode end as personSpecialityCode,
  PersonSpeciality.isHigh as personSpecialityIsHigh,
  DiagnosticResult.regionalCode AS diagnosticResultCode,
  EventResult.regionalCode AS eventResultCode,
  OrgStructure.infisCode AS orgStructCode,
  HospitalAction.id AS hospitalActionId,
  HospitalDirectionAction.id AS hospitalDirectionActionId,
  HospitalReceivedAction.id AS hospitalReceivedActionId,
  TalonVMP.id as talonVMPid, 
  mt.regionalCode AS medicalAidTypeRegionalCode,
  IFNULL(ItemMedicalAidKind.code, rbMedicalAidKind.code) AS medicalAidKindCode,
  ItemMedicalAidProfile.regionalCode AS medicalAidProfileRegionalCode,
  Account.number AS accountNumber,
  WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode) AS dayCount,
  /*Признак особый случай для ДД*/
  CONCAT(
  CASE WHEN Client.id <> ClientPolicy.client_id THEN '2' ELSE '' END,
  CASE WHEN Client.patrName = '' or Client.id <> ClientPolicy.client_id and repr.patrName = '' THEN '4' ELSE '' END,
  CASE WHEN rbEventProfile.regionalCode IN ('8008', '8010', '8014', '102', '8012', '8013', '8017', '8018', '8020', '8022') THEN '5' WHEN rbEventProfile.regionalCode IN ('8009', '8015', '8016', '103', '8019', '8021') THEN '6' ELSE '' END,
  IF(mt.regionalCode = '12' AND Event.relative_id IS NOT NULL AND age(Client.birthDate, Event.setDate) BETWEEN 4 AND 17, '7', ''),
  IFNULL((select case aps.value
            when 'a-проведение 1 этапа ЭКО(стимуляция суперовуляции)' then 'a'
            when 'b-полный цикл ЭКО с криоконсервацией эмбрионов' then 'b'
            when 'c-размораживание криоконсервированных эмбрионов с последующим переноссом' then 'c'
            when 'd-проведение I-III этапа ЭКО (стимуляция, получение, оплодотворение и культивирование) с последующей криоконсервацией эмбриона' then 'd'
            when 'e-полный цикл ЭКО без применения криоконсервации эмбрионов' then 'e'
            else '' end as step
        from Action ECO_Step
        left join ActionPropertyType apt on apt.actionType_id = ECO_Step.actionType_id and apt.deleted = 0
        left join ActionProperty ap on ap.type_id = apt.id and ap.action_id = ECO_Step.id and ap.deleted = 0
        left join ActionProperty_String aps on aps.id = ap.id
        where ECO_Step.id = (
                        SELECT MAX(A.id)
                        FROM Action A
                        WHERE A.event_id = Event.id AND
                                  A.deleted = 0 AND
                                  A.actionType_id IN (
                                        SELECT AT.id
                                        FROM ActionType AT
                                        WHERE AT.flatCode ='ECO_Step'
                                            AND AT.deleted = 0
                                  )
                    )
            and apt.name = 'Этап ЭКО'), '')
  ) AS Q_G,
  IFNULL(ActionOrg.infisCode, '') AS outOrgCode,
  IF(ActionOrg.infisCode is null or
      (mt.regionalCode in ('211', '233', '244')
      and EXISTS(select 1 from OrgStructure o where o.bookkeeperCode = ActionOrg.infisCode and o.deleted = 0)), 0, 1) as IS_OUT,
  repr.lastName AS FAMP,
  repr.firstName AS IMP,
  repr.patrName AS OTP,
  repr.birthDate AS DATRP,
  repr.sex AS POLP,
  repr.SNILS as SNILSP,
  Event.externalId,
  rbDiseaseCharacter.id as diseaseCharacterId,
  IF(rbDiseaseCharacter.code in ('1', '2'), '1', '0') as MKBX_PR,
  IF(mt.regionalCode in ('261', '262', '211', '233', '244', '232', '252') and rbDiseaseCharacter.code in ('1', '2'), '1', '0') as MKBX_PR_P20,
  IF(AssociatedCharacter.code in ('1', '2'), '1', '0') as MKBXS_PR,
  CASE WHEN rbDispanser.code = '1' then '1'
    WHEN rbDispanser.code in ('2', '6') then '2'
    WHEN rbDispanser.code = '4' then '4'
    WHEN rbDispanser.code in ('3', '5') then '6'
    WHEN IFNULL(rbDispanser.code, '0') not in ('1', '2', '3', '4', '5', '6') and mt.regionalCode in ('261', '262', '211', '233', '244', '232', '252') then '3'
    ELSE '0' END  as PR_D_N,
   CASE WHEN AssocDiagDispanser.code = '1' then '1'
    WHEN AssocDiagDispanser.code in ('2', '6') then '2'
    WHEN AssocDiagDispanser.code = '4' then '4'
    WHEN AssocDiagDispanser.code in ('3', '5') then '6'
    WHEN IFNULL(AssocDiagDispanser.code, '0') not in ('1', '2', '3', '4', '5', '6') and mt.regionalCode in ('261', '262', '211', '233', '244', '232', '252') then '3'
    ELSE '0' END  as PR_DS_N,
   CASE WHEN AssocDiagDispanser.code = '1' then '1'
    WHEN AssocDiagDispanser.code in ('2', '6') then '2'
    WHEN IFNULL(AssocDiagDispanser.code, '0') not in ('1', '2', '6') and mt.regionalCode in ('261', '262', '211', '233', '244', '232', '252') then '3'
    ELSE '0' END as PR_MS_N,
  PersonProfile.regionalCode as personProfileRegionalCode,
  RelegateOrg.smoCode as NAPR_MO,
  RelegateOrg.infisCode as NAPR_MO_OMSCODE,
  Event.srcNumber as NAPR_N,
  Event.srcDate as NAPR_D,
  KRITAction.id as kritActionid,
  IF(rbItemService.infis in ('B04.001.001', 'B04.008.001', 'B04.014.002', 'B04.015.003', 'B04.023.001', 'B04.026.001',
                             'B04.027.001', 'B04.028.001', 'B04.029.001', 'B04.029.005', 'B04.040.002', 'B04.046.001',
                             'B04.047.001', 'B04.047.003', 'B04.047.005', 'B04.050.001', 'B04.053.001', 'B04.057.001',
                             'B04.058.005', 'B04.064.003', 'B04.065.001', 'B04.065.003', 'B04.065.005', 'B04.001.006',
                             'B04.008.005', 'B04.009.001', 'B04.010.001', 'B04.014.007', 'B04.015.005', 'B04.023.016',
                             'B04.026.004', 'B04.028.004', 'B04.029.006', 'B04.031.001', 'B04.031.003', 'B04.050.008',
                             'B04.053.003', 'B04.058.002') and mt.regionalCode in ('21', '22', '31', '32'), 1, 0) as DNService,
  IF(rbItemService.name like '%%беременной%%' or rbItemService.name like '%%патронаж%%', 1, 0) as patronService,
  IF(rbItemService.infis in ('B01.047.015', 'B01.031.008'), 1, 0) as homeService,
  Account_Item.usedCoefficients as KSLP,
  Account_Item.usedCoefficientsValue as KSLP_IT,
  Diagnostic.cTumor_id,
  Diagnostic.cNodus_id,
  Diagnostic.cMetastasis_id,
  Diagnostic.cTNMPhase_id,
  Diagnostic.pTumor_id,
  Diagnostic.pNodus_id,
  Diagnostic.pMetastasis_id,
  Diagnostic.pTNMPhase_id,
IF(substr(COALESCE(rbItemService.infis, rbVisitService.infis, rbEventService.infis), 1, 1) in ('B', 'G', 'V') AND COALESCE(rbItemService.name, rbVisitService.name, rbEventService.name) not like 'Обращен%%',
(SELECT
        MAX(A1.id)
      FROM Action A1
      WHERE A1.event_id = Event.id
      AND A1.deleted = 0
      /*AND A1.person_id = ExecPerson.id*/
      AND (substr(COALESCE(rbItemService.infis, rbVisitService.infis, rbEventService.infis), 1, 1) in ('B') and DATE(A1.endDate) = Account_Item.serviceDate 
            or substr(COALESCE(rbItemService.infis, rbVisitService.infis, rbEventService.infis), 1, 1) in ('G', 'V'))
      AND A1.actionType_id IN (SELECT
          AT1.id
        FROM ActionType AT1
        WHERE AT1.flatCode = 'directionCancer'
        AND AT1.deleted = 0)), NULL) as directionCancerId,
IF(substr(COALESCE(rbItemService.infis, rbVisitService.infis, rbEventService.infis), 1, 1) in ('B') AND COALESCE(rbItemService.name, rbVisitService.name, rbEventService.name) not like 'Обращен%%',
(SELECT
        MAX(A1.id)
      FROM Action A1
      WHERE A1.event_id = Event.id
      AND A1.deleted = 0
      /*AND A1.person_id = ExecPerson.id*/
      AND DATE(A1.endDate) = Account_Item.serviceDate
      AND A1.actionType_id IN (SELECT
          AT1.id
        FROM ActionType AT1
        WHERE AT1.flatCode = 'appointments'
        AND AT1.deleted = 0)), NULL) as appointmentsActionId,
  IF(substr(COALESCE(rbItemService.infis, rbVisitService.infis, rbEventService.infis), 1, 1) in ('G', 'V', 'B', 'A') AND (Account_Item.price > 0 or mt.regionalCode in ('271', '272') AND Contract_Tariff.price > 0),
  (SELECT
        MAX(A1.id)
      FROM Action A1
      WHERE A1.event_id = Event.id
      AND A1.deleted = 0
      /*AND A1.person_id = ExecPerson.id*/
     AND DATE(A1.endDate) = Account_Item.serviceDate
      AND A1.actionType_id IN (SELECT
          AT1.id
        FROM ActionType AT1
        WHERE AT1.flatCode = 'ControlListOnko'
        AND AT1.deleted = 0)), NULL) as ControlListOnkoId, 
IF(substr(COALESCE(rbItemService.infis, rbVisitService.infis, rbEventService.infis), 1, 1) in ('G', 'V', 'B', 'A') AND (Account_Item.price > 0 or mt.regionalCode in ('271', '272') AND Contract_Tariff.price > 0),
 (SELECT
        MAX(A1.id)
      FROM Action A1
      WHERE A1.event_id = Event.id
      AND A1.deleted = 0
      AND A1.person_id = ExecPerson.id
      AND DATE(A1.endDate) = Account_Item.serviceDate
      AND A1.actionType_id IN (SELECT
          AT1.id
        FROM ActionType AT1
        WHERE AT1.flatCode = 'Gistologia'
        AND AT1.deleted = 0)), NULL) as GistologiaId,
IF(substr(COALESCE(rbItemService.infis, rbVisitService.infis, rbEventService.infis), 1, 1) in ('G', 'V', 'B', 'A') AND (Account_Item.price > 0 or mt.regionalCode in ('271', '272') AND Contract_Tariff.price > 0),
  (SELECT
        MAX(A1.id)
      FROM Action A1
      WHERE A1.event_id = Event.id
      AND A1.deleted = 0
      AND A1.person_id = ExecPerson.id
      AND DATE(A1.endDate) = Account_Item.serviceDate
      AND A1.actionType_id IN (SELECT
          AT1.id
        FROM ActionType AT1
        WHERE AT1.flatCode = 'Immunohistochemistry'
        AND AT1.deleted = 0)), NULL) AS ImmunohistochemistryId,
        IF(rbAccountType.regionalCode in ('5', '9' 'd', 'h', 'l', 'p'), (select min(prev.date) from Account_Item prev where prev.event_id = Account_Item.event_id and prev.reexposeItem_id is not null), NULL) as DVOZVRAT
FROM Account_Item
  LEFT JOIN Account ON Account_Item.master_id = Account.id
  Left join Contract_Tariff on Contract_Tariff.id = Account_Item.tariff_id
  LEFT JOIN Action ON Action.id = Account_Item.action_id
  LEFT JOIN Visit ON Visit.id = Account_Item.visit_id
  LEFT JOIN Event ON Event.id = Account_Item.event_id
  LEFT JOIN Organisation RelegateOrg on RelegateOrg.id = Event.relegateOrg_id
  LEFT JOIN Organisation currentOrg on currentOrg.id = Event.org_id
  LEFT JOIN Client ON Client.id = Event.client_id
  LEFT JOIN Client repr ON repr.id = Event.relative_id
  LEFT JOIN ClientPolicy ON ClientPolicy.id = getClientPolicyIdForDate(Client.id, 1, Event.execDate, Event.id)
  LEFT JOIN Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
  LEFT JOIN rbPolicyKind ON rbPolicyKind.id = ClientPolicy.policyKind_id
  /*документ берем на кого оформлен полис*/
  LEFT JOIN ClientDocument ON ClientDocument.client_id = Client.id
    AND ClientDocument.id = (SELECT MAX(CD.id)
      FROM ClientDocument AS CD
        LEFT JOIN rbDocumentType AS rbDT ON rbDT.id = CD.documentType_id
        LEFT JOIN rbDocumentTypeGroup AS rbDTG ON rbDTG.id = rbDT.group_id
      WHERE rbDTG.code = '1'
      AND CD.client_id = IFNULL(ClientPolicy.client_id, Client.id)
      AND CD.deleted = 0)
  LEFT JOIN rbDocumentType ON rbDocumentType.id = ClientDocument.documentType_id
  LEFT JOIN Person ON Person.id = Event.execPerson_id
  LEFT JOIN Person AS ExecPerson ON ExecPerson.id = COALESCE(Visit.person_id, Action.person_id, Event.execPerson_id)
  LEFT JOIN Person AS setActionPerson ON setActionPerson.id = Action.setPerson_id
  LEFT JOIN Diagnostic ON Diagnostic.event_id = Account_Item.event_id
    AND Diagnostic.id = (SELECT d.id
      FROM Diagnostic d
      INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = d.diagnosisType_id
      WHERE d.event_id = Account_Item.event_id
      AND rbDiagnosisType.CODE IN ('1', '2')
      AND d.deleted = 0
      ORDER BY rbDiagnosisType.code
      LIMIT 1)
  left join rbDiseaseCharacter on rbDiseaseCharacter.id = Diagnostic.character_id
  left join rbDiseasePhases on rbDiseasePhases.id = Diagnostic.phase_id
  left join rbDispanser on rbDispanser.id = Diagnostic.dispanser_id
  LEFT JOIN Diagnostic AS AssociatedDiagnostic ON (
    AssociatedDiagnostic.event_id = Account_Item.event_id
    AND AssociatedDiagnostic.diagnosisType_id IN (SELECT
        id
      FROM rbDiagnosisType
      WHERE code = '9')
    AND AssociatedDiagnostic.deleted = 0)
    AND AssociatedDiagnostic.id = (SELECT
        id
      FROM Diagnostic
      WHERE Diagnostic.event_id = Account_Item.event_id
      AND Diagnostic.diagnosisType_id IN (SELECT
          id
        FROM rbDiagnosisType
        WHERE code = '9')
      AND Diagnostic.deleted = 0 LIMIT 1)
  left join rbDiseaseCharacter AssociatedCharacter on AssociatedCharacter.id = AssociatedDiagnostic.character_id
  left join rbDispanser as AssocDiagDispanser on AssocDiagDispanser.id = AssociatedDiagnostic.dispanser_id
  LEFT JOIN Diagnostic AS SeqDiagnostic
    ON (
    SeqDiagnostic.event_id = Account_Item.event_id
    AND SeqDiagnostic.diagnosisType_id IN (SELECT
        id
      FROM rbDiagnosisType
      WHERE code = '3')
    AND SeqDiagnostic.deleted = 0)
    AND SeqDiagnostic.id = (SELECT
        id
      FROM Diagnostic
      WHERE Diagnostic.event_id = Account_Item.event_id
      AND Diagnostic.diagnosisType_id IN (SELECT
          id
        FROM rbDiagnosisType
        WHERE code = '3')
      AND Diagnostic.deleted = 0 LIMIT 1)
  LEFT JOIN ClientWork
    ON ClientWork.client_id = Event.client_id
    AND ClientWork.id = (SELECT
        MAX(CW.id)
      FROM ClientWork AS CW
      WHERE CW.client_id = Client.id
      AND CW.deleted = 0)
   LEFT JOIN Diagnosis ON Diagnosis.id = Diagnostic.diagnosis_id AND Diagnosis.deleted = 0
  LEFT JOIN Diagnosis AS AssociatedDiagnosis ON AssociatedDiagnosis.id = AssociatedDiagnostic.diagnosis_id AND AssociatedDiagnosis.deleted = 0
  LEFT JOIN Diagnosis AS SeqDiagnosis ON SeqDiagnosis.id = SeqDiagnostic.diagnosis_id AND SeqDiagnosis.deleted = 0
  LEFT JOIN rbDiagnosticResult AS DiagnosticResult ON DiagnosticResult.id = Diagnostic.result_id
  LEFT JOIN rbResult AS EventResult ON EventResult.id = Event.result_id
  LEFT JOIN EventType ON EventType.id = Event.eventType_id
  LEFT JOIN rbEventProfile ON rbEventProfile.id = EventType.eventProfile_id
  LEFT JOIN rbService AS rbEventService ON rbEventService.id = EventType.service_id
  LEFT JOIN rbService AS rbVisitService ON rbVisitService.id = Visit.service_id
  LEFT JOIN ActionType ON ActionType.id = Action.actionType_id
  LEFT JOIN OrgStructure ON OrgStructure.id = ExecPerson.orgStructure_id
  LEFT JOIN rbService AS rbItemService ON rbItemService.id = Account_Item.service_id
  LEFT JOIN rbSpeciality ON ExecPerson.speciality_id = rbSpeciality.id
  LEFT JOIN rbSpeciality PersonSpeciality ON PersonSpeciality.id = Person.speciality_id
  LEFT JOIN Organisation AS ActionOrg ON Action.org_id = ActionOrg.id
  LEFT JOIN rbMedicalAidType ON EventType.medicalAidType_id = rbMedicalAidType.id
  LEFT JOIN rbMedicalAidType mt ON mt.id = case when rbMedicalAidType.regionalCode in ('271', '272') and Event.execDate >= '2020-05-01' then (select mat.id from rbMedicalAidType mat where mat.regionalCode = IF(rbMedicalAidType.regionalCode = '271', '21', '22') limit 1) else rbMedicalAidType.id end
  LEFT JOIN rbMedicalAidKind ON EventType.medicalAidKind_id = rbMedicalAidKind.id
  LEFT JOIN rbMedicalAidProfile AS EventMedicalAidProfile ON EventMedicalAidProfile.id = rbEventService.medicalAidProfile_id
  LEFT JOIN rbMedicalAidProfile AS VisitMedicalAidProfile ON VisitMedicalAidProfile.id = rbVisitService.medicalAidProfile_id
  LEFT JOIN rbService_Profile ON rbService_Profile.id = (SELECT MAX(id)
      FROM rbService_Profile rs
      WHERE rs.master_id = rbItemService.id
      AND rs.speciality_id = ExecPerson.speciality_id)
  LEFT JOIN rbMedicalAidKind AS ItemMedicalAidKind ON ItemMedicalAidKind.id = IFNULL(rbService_Profile.medicalAidKind_id, rbItemService.medicalAidKind_id)
  LEFT JOIN rbMedicalAidProfile AS PersonProfile ON PersonProfile.id = PersonSpeciality.medicalAidProfile_id
  LEFT JOIN rbMedicalAidProfile AS ItemMedicalAidProfile ON ItemMedicalAidProfile.id = rbSpeciality.medicalAidProfile_id
  LEFT JOIN Action AS HospitalAction
    ON HospitalAction.id = (SELECT
        MAX(A.id)
      FROM Action A
      WHERE A.event_id = Event.id
      AND A.deleted = 0
      AND A.actionType_id IN (SELECT
          AT.id
        FROM ActionType AT
        WHERE AT.flatCode = 'moving'
        AND AT.deleted = 0))
  LEFT JOIN Action AS HospitalReceivedAction
    ON HospitalReceivedAction.id = getPrevActionId(HospitalAction.event_id, HospitalAction.id, (select max(id) from ActionType where flatCode = 'received' and deleted = 0), HospitalAction.endDate)
  LEFT JOIN Action AS HospitalDirectionAction
    ON HospitalDirectionAction.id = (SELECT
        MAX(A1.id)
      FROM Action A1
      WHERE A1.event_id = Event.id
      AND A1.deleted = 0
      AND A1.status not in (3,6)
      AND A1.actionType_id IN (SELECT
          AT1.id
        FROM ActionType AT1
        WHERE AT1.flatCode in ('hospitalDirection', 'planning')
        AND AT1.deleted = 0))
LEFT JOIN Action AS TalonVMP
    ON TalonVMP.id = (SELECT
        MAX(A1.id)
      FROM Action A1
      WHERE A1.event_id = Event.id
      AND A1.deleted = 0
      AND A1.actionType_id IN (SELECT
          AT1.id
        FROM ActionType AT1
        WHERE AT1.flatCode = 'VMPtalon'
        AND AT1.deleted = 0))
LEFT JOIN Action AS KRITAction
    ON KRITAction.id = (SELECT
        MAX(A1.id)
      FROM Action A1
      WHERE A1.event_id = Event.id
      AND A1.deleted = 0
      AND A1.actionType_id IN (SELECT
          AT1.id
        FROM ActionType AT1
        WHERE AT1.flatCode = 'KRIT'
        AND AT1.deleted = 0))
  
  LEFT JOIN rbAccountType on rbAccountType.id = Account.type_id
  LEFT JOIN Organisation AS Payer ON Payer.id = Account.payer_id
WHERE %s""" % self.db.joinAnd(cond)
        return self.db.query(stmt)


# Запрос для ФЛК по всему приписанному населению
    def createQueryFLKp(self):

        stmt = """
            SELECT
          Client.id        AS client_id,
          Client.id        AS event_id,
          Client.id        AS accountId,
          Client.lastName        AS lastName,
          Client.firstName       AS firstName,
          Client.patrName        AS patrName,
          Client.birthDate       AS birthDate,
          Client.birthNumber,
          Client.sex             AS sex,
          Client.SNILS           AS SNILS,
          getClientLocAddress(Client.id) AS locAddress,
          getClientRegAddress(Client.id) AS regAddress,
          ClientPolicy.serial    AS policySerial,
          ClientPolicy.number    AS policyNumber,
          ClientPolicy.note AS policyNote,
          ClientPolicy.begDate AS policyBegDate,
          ClientPolicy.endDate AS policyEndDate,
          Insurer.infisCode      AS policyInsurer,
          Insurer.INN               AS insurerINN,
          Insurer.shortName          AS insurerName,
          Insurer.OKATO AS insurerOKATO,
          Insurer.OGRN AS insurerOGRN,
          Insurer.area AS insurerArea,
          Insurer.id AS insurerId,
          rbPolicyType.code      AS policyType,
          rbPolicyKind.regionalCode AS policyKindCode,
          ClientDocument.serial  AS documentSerial,
          ClientDocument.number  AS documentNumber,
          rbDocumentType.code    AS documentType,
          rbDocumentType.regionalCode AS documentRegionalCode,
          Citizenship.regionalCode AS citizenshipCode,
          SocStatus.regionalCode AS socStatusCode
      , CURRENT_DATE() clientBegDate
      , CURRENT_DATE() clientEndDate
      , 0 clientSum
      , 0 clientFederalSum
        FROM Client
        left JOIN ClientAttach ca ON ca.id = (
              SELECT MAX(ClientAttach.id)
                    FROM ClientAttach
                    INNER JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
                    WHERE client_id = Client.id
                      AND ClientAttach.deleted = 0
                      AND NOT rbAttachType.TEMPORARY)
        LEFT JOIN rbAttachType rat ON rat.ID = ca.attachType_id
        LEFT JOIN ClientPolicy
    ON ClientPolicy.client_id = Client.id AND ClientPolicy.deleted = 0
      AND ClientPolicy.policyType_id IN (1,2)
      AND  ClientPolicy.begDate = (SELECT
      MAX(CP.begDate)
      FROM ClientPolicy AS CP
      WHERE CP.client_id = Client.id
      AND CP.deleted = 0
      AND CP.policyType_id IN (1,2))
        LEFT JOIN Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
        LEFT JOIN rbPolicyType ON rbPolicyType.id = ClientPolicy.policyType_id
        LEFT JOIN rbPolicyKind ON rbPolicyKind.id = ClientPolicy.policyKind_id
        LEFT JOIN ClientDocument ON ClientDocument.id = (SELECT MAX(CD.id)
                                     FROM   ClientDocument AS CD
                                     LEFT JOIN rbDocumentType AS rbDT ON rbDT.id = CD.documentType_id
                                     LEFT JOIN rbDocumentTypeGroup AS rbDTG ON rbDTG.id = rbDT.group_id
                                     WHERE  rbDTG.code = '1' AND CD.client_id = ifnull(ClientPolicy.client_id, Client.id) AND CD.deleted=0)
        LEFT JOIN rbDocumentType ON rbDocumentType.id = ClientDocument.documentType_id

        LEFT JOIN ClientContact  ON ClientContact.client_id = Client.id AND
                  ClientContact.id = (SELECT MAX(CC.id)
                                     FROM   ClientContact AS CC
                                     LEFT JOIN rbContactType ON CC.contactType_id= rbContactType.id
                                     WHERE  rbContactType.code IN (1,2,3) AND CC.client_id = Client.id AND CC.deleted=0)
        LEFT JOIN ClientWork ON ClientWork.client_id=Client.id AND
                    ClientWork.id = (SELECT max(CW.id)
                                     FROM ClientWork AS CW
                                     WHERE CW.client_id=Client.id AND CW.deleted=0)
        LEFT JOIN ClientSocStatus AS ClientCitizenshipStatus ON ClientCitizenshipStatus.id= (
            SELECT MAX(CSS.id)
            FROM ClientSocStatus AS CSS
            WHERE CSS.client_id = `Client`.id AND
            CSS.deleted = 0 AND CSS.socStatusClass_id = (
                SELECT rbSSC.id
                FROM rbSocStatusClass AS rbSSC
                WHERE rbSSC.code = '8' AND rbSSC.group_id IS NULL
                LIMIT 0,1
            )
        )
        LEFT JOIN rbSocStatusType AS Citizenship ON
            ClientCitizenshipStatus.socStatusType_id = Citizenship.id
        LEFT JOIN ClientSocStatus ON ClientSocStatus.id= (
            SELECT MAX(CSS2.id)
            FROM ClientSocStatus AS CSS2
            WHERE CSS2.client_id = `Client`.id AND
            CSS2.deleted = 0 AND CSS2.socStatusClass_id = (
                SELECT rbSSC2.id
                FROM rbSocStatusClass AS rbSSC2
                WHERE rbSSC2.code = '9' AND rbSSC2.group_id IS NULL
                LIMIT 0,1
            )
        )
        LEFT JOIN rbSocStatusType AS SocStatus ON
            ClientSocStatus.socStatusType_id = SocStatus.id
        where
            (rat.outcome is null or rat.outcome = 0)
        """

        return self.db.query(stmt)


    def createQueryPerson(self):
        tableAccountItem = self.db.table('Account_Item')
        cond = [
            tableAccountItem['master_id'].inlist(self.selectedAccountIds) if self.exportType == self.exportTypeFLK else
            tableAccountItem['master_id'].eq(self.currentAccountId), tableAccountItem['deleted'].eq(0)]

        stmt = """SELECT ExecPerson.snils, min(ExecPerson.lastName) lastName, min(ExecPerson.firstName) firstName, min(ExecPerson.patrName) patrName,
        min(ExecPerson.sex) sex, min(ExecPerson.birthDate) birthDate, 
        (select min(po.validFromDate) 
          FROM Person p
           left join Person_Order po on po.master_id = p.id and po.type = 0 and po.deleted = 0
          WHERE p.deleted = 0 AND p.snils = ExecPerson.snils) AS DATN
        FROM Account_Item
        left join Account a on a.id = Account_Item.master_id
        LEFT JOIN rbPayRefuseType ON rbPayRefuseType.id = Account_Item.refuseType_id
        LEFT JOIN Action ON Action.id = Account_Item.action_id
        LEFT JOIN Visit  ON Visit.id  = Account_Item.visit_id
        LEFT JOIN Event  ON Event.id  = Account_Item.event_id
        LEFT JOIN Person AS ExecPerson ON ExecPerson.id = COALESCE(Visit.person_id, Action.person_id, Event.execPerson_id)
        WHERE {0} 
        GROUP BY ExecPerson.snils
        ORDER BY snils""".format(self.db.joinAnd(cond))
        return self.db.query(stmt)


    def process(self, dbf, record, params):
        db = QtGui.qApp.db
        birthDate = forceDate(record.value('birthDate'))
        begDate = forceDate(record.value('begDate'))
        endDate = forceDate(record.value('endDate'))
        clientId = forceRef(record.value('client_id'))
        accountId = forceRef(record.value('accountId'))
        eventId = forceRef(record.value('event_id'))
        accountItemId = forceRef(record.value('accountItemId'))
        hospitalActionId =  forceRef(record.value('hospitalActionId'))
        hospitalDirectionActionId = forceRef(record.value('hospitalDirectionActionId'))
        hospitalReceivedActionId = forceRef(record.value('hospitalReceivedActionId'))
        appointmentsActionId = forceRef(record.value('appointmentsActionId'))
        talonVMPid = forceRef(record.value('talonVMPid'))
        kritActionid = forceRef(record.value('kritActionid'))
        directionCancerId  = forceRef(record.value('directionCancerId'))
        ControlListOnkoId = forceRef(record.value('ControlListOnkoId'))
        GistologiaId = forceRef(record.value('GistologiaId'))
        ImmunohistochemistryId = forceRef(record.value('ImmunohistochemistryId'))
        VP = forceString(record.value('medicalAidTypeRegionalCode'))
        UID = forceRef(record.value('UID')) #forceRef(record.value('accountItemId'))

        # список кодов специальностей для терапевта, педиатра, ВОП
        if endDate >= QDate(2018, 4, 1):
            specialityList = ['39', '49', '76']
        else:
            specialityList = ['16', '22', '27']

        # Подменяем недействующие коды УОМП
        if VP in ['51', '511'] and QDate(2018, 1, 1) <= endDate < QDate(2018, 9, 1):
            VP = '41'
        elif VP in ['52', '522'] and QDate(2018, 1, 1) <= endDate < QDate(2018, 9, 1):
            VP = '42'
        elif VP == '90' and QDate(2018, 1, 1) <= endDate:
            VP = '41'

        if self.exportType in [self.exportTypeP25, self.exportTypePreControlP25, self.exportTypeInvoice]:
            (dbfP, dbfU, dbfD, dbfN, dbfR, dbfO, dbfI, dbfC) = dbf
        else:
            dbfP = dbf

        if eventId not in self.exportedEvents:
            self.eventsDict[eventId] = {'VP': VP, 'VS': forceString(record.value('accTypeCode')), 'hasObrService': 0, 'hasHomeServiсe': 0, 'hasPatronService': 0, 'hasDNService': 0}
            dbfRecord = dbfP.newRecord()
            if self.exportType != self.exportTypeAttachments:
                if self.exportType in [self.exportTypeP25, self.exportTypePreControlP25, self.exportTypeInvoice]:
                    # номер реестра счетов (п. 1 примечаний) обязательное
                    dbfRecord['NS'] = self.processParams().get('iAccNumber') #if self.edtRegistryNumber.isEnabled() self.edtRegistryNumber.value()
                else:# Для ФЛК берем номера из счетов, если их возможно преобразовать в число, если невозможно то берем от основного
                    try:
                        dbfRecord['NS'] = forceInt(record.value('accountNumber'))
                    except:
                         dbfRecord['NS'] = self.edtRegistryNumber.value()
                         self.log(u'Невозможно привести номер счёта  "%s" к числовому виду' % forceString(record.value('accountNumber')))
                # тип реестра счетов (п. 2;4 примечаний) обязательное SPR21
                dbfRecord['VS'] = forceString(record.value('accTypeCode'))
                # дата формирования реестра счетов (п. 3 примечаний) обязательное
                dbfRecord['DATS'] = pyDate(params.get('accDate', QDate.currentDate()))
                # номер персонального счета обязательное
                dbfRecord['SN'] = eventId
                dbfRecord['DATPS'] = pyDate(endDate)

            # код медицинской организации в системе ОМС, предоставившей медицинскую помощь
            if self.exportType == self.exportTypeFLK:
                if accountId and len(self.mapAccountInfo[accountId].get('oms_code', '')) == 5:
                    dbfRecord['CODE_MO'] = self.mapAccountInfo[accountId].get('oms_code')
                else:
                    dbfRecord['CODE_MO'] = params['codeLpu']
            else:
                dbfRecord['CODE_MO'] = params['codeLpu']

            # ОГРН плательщика (п. 4 примечаний) обязательное SPR02
            dbfRecord['PL_OGRN'] = forceString(record.value('PayerOGRN'))
            dbfRecord['FIO'] = forceString(record.value('lastName')).strip().upper()
            dbfRecord['IMA'] = forceString(record.value('firstName')).strip().upper()
            dbfRecord['OTCH'] = forceString(record.value('patrName')).strip().upper()
            dbfRecord['POL'] = formatSex(record.value('sex')).upper() # пол (М/Ж)
            dbfRecord['DATR'] = pyDate(birthDate) # дата рождения
            if self.exportType in [self.exportTypeP25, self.exportTypePreControlP25, self.exportTypeInvoice]:
                dbfRecord['KAT'] = forceInt(record.value('KAT'))
            dbfRecord['SNILS'] = formatSNILS(forceString(record.value('SNILS')))

            if self.exportType == self.exportTypeAttachments:
                dbfRecord['locAddress'] = nameCase(forceString(record.value('locAddress')))
                dbfRecord['regAddress'] = nameCase(forceString(record.value('regAddress')))

            # код ОКАТО территории страхования по ОМС обязательное для инокраевых SPR39
            dbfRecord['OKATO_OMS'] = forceString(record.value('insurerOKATO'))
            if dbfRecord['OKATO_OMS'] == '':
                insurerId = forceRef(record.value('insurerId'))
                insurerName = forceString(db.translate('Organisation', 'id', insurerId, 'shortName'))
                self.log(u'<b><font color=orange>Внимание<\font><\b>:'\
                    u' ОКАТО для ОМС "%s" не задан, пытаюсь определить по области страхования!' % insurerName)
                insurerArea = forceString(db.translate('Organisation', 'id', insurerId, 'area'))
                dbfRecord['OKATO_OMS'] = forceString(db.translate('kladr.KLADR', 'CODE', insurerArea, 'OCATD'))[:5]
                if dbfRecord['OKATO_OMS'] == '':
                    self.log(u'<b><font color=red>Внимание<\font><\b>:'\
                        u' ОКАТО для СМО "%s" не задан!' % forceString(record.value('insurerName')))
            dbfRecord['SPV'] = forceInt(record.value('policyKindCode'))
            dbfRecord['SPS'] = forceString(record.value('policySerial'))
            dbfRecord['SPN'] = forceString(record.value('policyNumber'))
            Q_G = forceString(record.value('Q_G'))
            dbfRecord['Q_G'] = Q_G
            C_DOC = forceInt(record.value('documentRegionalCode'))
            if self.exportType in [self.exportTypeP25, self.exportTypePreControlP25, self.exportTypeInvoice]:
                age = calcAgeInDays(birthDate, begDate)
                if age < 31 and C_DOC != 3 and '2' in Q_G:
                    dbfRecord['NOVOR'] = '%s%s%s' % (forceInt(record.value('sex')), birthDate.toString('ddMMyy'), forceString(record.value('birthNumber')))
                # Вес при рождении. Указывается при оказании МП недоношенным и маловесным детям
                if forceString(record.value('MKBXP'))[:3] in ['P05', 'P07'] or forceString(record.value('MKBXSP'))[:3] in ['P05', 'P07']:
                    dbfRecord['VNOV_D'] = forceInt(record.value('birthWeight'))

            if '2' in Q_G:
                dbfRecord['FAMP'] = forceString(record.value('FAMP')).strip().upper() # фамилия представителя пациента
                dbfRecord['IMP'] = forceString(record.value('IMP')).strip().upper() # имя представителя пациента
                dbfRecord['OTP'] = forceString(record.value('OTP')).strip().upper() # отчество представителя пациента
                dbfRecord['POLP'] = formatSex(forceString(record.value('POLP')).strip()) # пол представителя пациента (М/Ж)
                dbfRecord['DATRP'] = pyDate(forceDate(record.value('DATRP'))) # дата рождения представителя пациента
                dbfRecord['FIO'] = forceString(record.value('FAMP')).strip().upper()
                dbfRecord['IMA'] = forceString(record.value('IMP')).strip().upper()
                dbfRecord['OTCH'] = forceString(record.value('OTP')).strip().upper()
                dbfRecord['SNILS'] = formatSNILS(forceString(record.value('SNILSP')))

            if C_DOC:
                dbfRecord['C_DOC'] = C_DOC
            dbfRecord['S_DOC'] = forceString(record.value('documentSerial')).strip()
            dbfRecord['N_DOC'] = forceString(record.value('documentNumber')).strip()

            if self.exportType in [self.exportTypeP25, self.exportTypePreControlP25, self.exportTypeInvoice]:
                MP = forceString(record.value('MP'))
                # сведения о направлении на плановую госпитализацию
                NAPR_MO = forceString(record.value('NAPR_MO'))
                NAPR_MO_OMSCODE = forceString(record.value('NAPR_MO_OMSCODE'))
                NAPR_N = forceString(record.value('NAPR_N'))
                if not NAPR_MO_OMSCODE:
                    NAPR_MO_OMSCODE = '88888'
                dbfRecord['NAPR_MO'] = NAPR_MO
                if NAPR_N:
                    if NAPR_MO_OMSCODE + '_' not in NAPR_N:
                        NAPR_N = '%s_%s' % (NAPR_MO_OMSCODE, NAPR_N)
                    dbfRecord['NAPR_N'] = NAPR_N[:15]
                dbfRecord['NAPR_D'] = pyDate(forceDate(record.value('NAPR_D')))

                # Талон ВМП
                if talonVMPid:
                    talonVMP = CAction(record=QtGui.qApp.db.getRecord('Action', '*', talonVMPid))
                    dbfRecord['TAL_N'] = forceString(talonVMP[u'Номер талона'])
                    dbfRecord['TAL_D'] = pyDate(talonVMP[u'Дата талона'])
                    dbfRecord['NAPR_DP'] = pyDate(talonVMP[u'Дата планируемой госпитализации'])

                dbfRecord['PR_D_N'] = forceString(record.value('PR_D_N'))
                dbfRecord['PR_DS_N'] = forceString(record.value('PR_DS_N'))

            dbfRecord['DATN'] = pyDate(begDate)
            dbfRecord['DATO'] = pyDate(endDate)

            # код исхода заболевания обязательное SPR11
            if self.exportType in [self.exportTypeP25, self.exportTypePreControlP25, self.exportTypeInvoice]:
                dbfRecord['ISHL'] = forceString(record.value('diagnosticResultCode'))
                # код исхода обращения обязательное SPR12
                dbfRecord['ISHOB'] = forceString(record.value('eventResultCode'))
                # код вида обращения обязательное SPR14
                dbfRecord['MP'] = MP
                dbfRecord['DOC_SS'] = formatSNILS(forceString(record.value('personSNILS')))
                personSpecialityCode = forceString(record.value('personSpecialityCode'))
                dbfRecord['SPEC'] = personSpecialityCode
                dbfRecord['PROFIL'] = forceString(record.value('personProfileRegionalCode'))
                dbfRecord['MKBX'] = forceString(record.value('MKBXP'))
                dbfRecord['MKBXS'] = forceString(record.value('MKBXSP'))
                dbfRecord['MKBX_PR'] = forceString(record.value('MKBX_PR_P20'))

                if endDate >= QDate(2018, 9, 1) and VP in ['11', '12', '301', '302', '43', '51', '52', '511', '522']:
                    vmp = '31'
                elif endDate < QDate(2018, 9, 1) and VP in ['11', '12', '301', '302', '41', '42', '411', '422', '43', '51', '52', '511', '522']:
                    vmp = '31'
                elif VP in ['401', '402']:
                    vmp = '32'
                elif VP in ['801', '802']:
                    vmp = '21'
                elif personSpecialityCode in specialityList:
                    vmp = '12'
                elif forceBool(record.value('personSpecialityIsHigh')):
                    vmp = '13'
                else:
                    vmp = '11'
                dbfRecord['VMP'] = vmp
                dbfRecord['DVOZVRAT'] = pyDate(forceDate(record.value('DVOZVRAT')))
            self.RecordListP.append(dbfRecord)
            self.exportedEvents.add(eventId)

        if self.exportType not in [self.exportTypeFLK, self.exportTypeAttachments]:
            serviceCode = forceString(record.value('service'))
            patronService = forceInt(record.value('patronService'))
            homeService = forceInt(record.value('homeService'))
            DNService = forceInt(record.value('DNService'))
            isObr = forceInt(record.value('isObr'))
            if patronService:
                self.eventsDict[eventId]['hasPatronService'] = 1
            if homeService:
                self.eventsDict[eventId]['hasHomeServiсe'] = 1
            if DNService:
                self.eventsDict[eventId]['hasDNService'] = 1
            if isObr:
                self.eventsDict[eventId]['hasObrService'] = 1
            dbfRecord = dbfU.newRecord()

            dbfRecord['UID'] = UID
            dbfRecord['CODE_MO'] = params['codeLpu']
            dbfRecord['NS'] = self.processParams().get('iAccNumber')
            dbfRecord['SN'] = eventId
            dbfRecord['ISTI'] = forceString(record.value('externalId'))[:20] if forceString(record.value('externalId')) else forceString(clientId)
            if hospitalReceivedActionId:
                receivedAction = CAction(record=QtGui.qApp.db.getRecord('Action', '*', hospitalReceivedActionId))
                if receivedAction[u'Кем доставлен'] == u'Самостоятельно':
                    dbfRecord['P_PER'] = '1'
                elif receivedAction[u'Кем доставлен'] == u'СМП':
                    dbfRecord['P_PER'] = '2'
                elif receivedAction[u'Кем доставлен'] == u'перевод из другой МО':
                    dbfRecord['P_PER'] = '3'
                elif receivedAction[u'Кем доставлен'] == u'перевод внутри МО с другого профиля':
                    dbfRecord['P_PER'] = '4'

            # если нет поступления но есть движение, то считаем что перевод с другого профиля внутри МО
            if not hospitalReceivedActionId and hospitalActionId:
                dbfRecord['P_PER'] = '4'

            dbfRecord['KOTD'] = forceString(record.value('orgStructCode'))
            # поле KPK = региональному коду справочника "профили коек",
            # койки указанной в действии "движение". если в движении
            # койка не указана = пусто. если нет действия движение = пусто.
            if hospitalActionId:
                action = CAction(record=db.getRecord('Action', '*', hospitalActionId))
                bedCode = self.getHospitalBedProfileRegionalCode(self.getHospitalBedProfileId(forceRef(action[u'койка'])))
                if bedCode:
                    dbfRecord['KPK'] = bedCode

            # код диагноза основного заболевания по МКБ–Х (п. 2 примечаний)
            # обязательное для всех услуг, кроме диагностических SPR20
            dbfRecord['MKBX'] = forceString(record.value('MKB'))
            # код диагноза сопутствующего заболевания по МКБ–Х (п. 2 примечаний) SPR20
            dbfRecord['MKBXS'] = forceString(record.value('AssociatedMKB'))
            if dbfRecord['MKBXS']:
                if VP in ['211', '232', '252', '261', '262']:
                    dbfRecord['MKBXS_PR'] = forceString(record.value('MKBXS_PR'))
                dbfRecord['PR_MS_N'] = forceString(record.value('PR_MS_N'))
            # код диагноза осложнения основного заболевания по МКБ–Х (п. 2 примечаний) SPR20
            dbfRecord['MKBXO'] = forceString(record.value('SeqMKB'))
            # Характер основного заболевания
            # Обязательно к заполнению, если IS_OUT = 0 или код основного диагноза не входит в рубрику Z
            diseaseCharacterId = forceRef(record.value('diseaseCharacterId'))
            if diseaseCharacterId:
                value = None
                if VP in ['11', '12', '301', '302', '41', '42', '411', '422', '43', '51', '52', '511', '522']:
                    if dbfRecord['MKBX'][:1] == 'C' or dbfRecord['MKBX'][:2] == 'D0' or dbfRecord['MKBX'][:3] in ['D45', 'D46', 'D47'] \
                            or (dbfRecord['MKBX'] == 'D70' and (dbfRecord['MKBXS'] >= 'C00' and dbfRecord['MKBXS'] <= 'C80.9' or dbfRecord['MKBXS'] == 'C97')):
                        value = getIdentification('rbDiseaseCharacter', diseaseCharacterId, '', raiseIfNonFound=False)
                elif 'Z' not in forceString(record.value('MKB')):
                    value = getIdentification('rbDiseaseCharacter', diseaseCharacterId, '', raiseIfNonFound=False)
                if value:
                    dbfRecord['C_ZAB'] = value

            # код условия оказания медицинской помощи
            dbfRecord['VP'] = VP

            # оценка состояния по шкалам или схема лечения ЗНО или длительность ИВЛ
            if serviceCode[:1] == 'G' and kritActionid:
                action = CAction(record=db.getRecord('Action', '*', kritActionid))
                for propName in [u'Состояние пациента по ШРМ', u'Схема лечения ЗНО', u'Длительность ИВЛ',
                                 u'МРТ с высоким разрешением', u'Назначение ГИП и СИ', u'Назначение при хр гепатите С',
                                 u'Биопсия/трепанобиопсия при ЗНО', u'Этапы ЭКО', u'Грыжи', u'Ковид', u'Инфаркт', u'Реаб. после Ковид',
                                 u'Лимфа', u'Препараты', u'Фокальные дистонии', u'Состояние после перенесенной лучевой терапии',
                                 u'Множественная травма', u'Антимикробная терапия', u'Дерматозы', u'Иммунизация детей до 2-х лет',
                                 u'Генноинженерные препараты и селективные иммунодепресанты', u'Уровень курации',
                                 u'Терапия с заменой генноинженерных препаратов или селективных иммунодепрессантов',
                                 u'Количество фракций', u'Сопроводительная лекарственная терапия пр ЗНО']:
                    code = self.getKRITCode(forceRef(action[propName]))
                    stmt = u"select NULL from soc_spr69 where ksgkusl = '{kusl}' and KRIT = '{krit}' and (dato is null or dato >= {date})"
                    if code and db.query(stmt.format(kusl=serviceCode, krit=code, date=db.formatDate(endDate))).size() > 0:
                        dbfRecord['KRIT'] = code
                        break
                # схема лекарственной терапии (только для комбинированных схем лечения)
                if dbfRecord['KRIT'][:2] == u'sh' and action[u'Доп. схема лечения ЗНО']:
                    dbfRecord['KRIT2'] = self.getKRITCode(forceRef(action[u'Доп. схема лечения ЗНО']))

            # список примененных КСЛП и итоговое значение КСЛП для услуги КСГ
            dbfRecord['KSLP'] = forceString(record.value('KSLP'))
            if dbfRecord['KSLP']:
                dbfRecord['KSLP_IT'] = forceDouble(record.value('KSLP_IT'))

            # код медицинской услуги обязательное SPR18
            dbfRecord['KUSL'] = serviceCode
            # количество услуг обязательное
            dbfRecord['KOLU'] = forceInt(record.value('amount'))

            if serviceCode[:1] in ('G', 'V'):
                dayCount = forceInt(record.value('dayCount'))
                if (serviceCode in ['st36.013', 'st36.014', 'st36.015'] and endDate < QDate(2026, 1, 1)
                        or serviceCode in ['st36.050', 'st36.051', 'st36.052', 'st36.053', 'st36.054'] and endDate >= QDate(2026, 1, 1)):
                    dbfRecord['KD'] = 0
                else:
                    dbfRecord['KD'] = dayCount if dayCount > 1 else 1

            # дата начала выполнения услуги обязательное
            servDate = forceDate(record.value('actionDate'))
            if serviceCode[:1] in ('A', 'B'):
                endDate = forceDate(record.value('actionEndDate'))
                if not endDate.isValid():
                    endDate = forceDate(record.value('visitDate'))

            if not servDate.isValid():
                servDate = forceDate(record.value('visitDate'))

                if not servDate.isValid():
                    servDate = begDate

            if not servDate.isValid():
                self.log(u'Не задана дата услуги: accountItemId=%d,'\
                    u' eventId=%d.' % (accountItemId, eventId))

            dbfRecord['DATO'] = pyDate(endDate)
            price = forceDouble(record.value('price'))
            dbfRecord['IS_OUT'] = forceInt(record.value('IS_OUT'))
            dbfRecord['OUT_MO'] = forceString(record.value('outOrgCode'))

            if dbfRecord['IS_OUT']:
                dbfRecord['TARU'] = 0.0
                dbfRecord['SUMM'] = 0.0
            else:
                dbfRecord['TARU'] = price
                dbfRecord['SUMM'] = forceDouble(record.value('sum'))

            if self.exportType == self.exportTypeInvoice:
                note = forceString(record.value('note'))
                if 'K3=' in note:
                    dbfRecord['K3'] = forceDouble(note.replace('K3=', ''))
                else:
                    dbfRecord['K3'] = 0.0
                if 'K0=' in note:
                    dbfRecord['K0'] = forceDouble(note.replace('K0=', ''))
                    dbfRecord['hasK0'] = True
                else:
                    dbfRecord['K0'] = 0.0
                    dbfRecord['hasK0'] = False

            if dbfRecord['VP'] in ['111', '112'] and dbfRecord['KUSL'] in self.posServices or serviceCode[:1] in ('G', 'V'):
                dbfRecord['DATN'] = pyDate(servDate)
            else:
                dbfRecord['DATN'] = pyDate(endDate)

            self.uetDict[UID] = forceDouble(record.value('UET'))

            dbfRecord['DOC_SS'] = formatSNILS(forceString(record.value('execPersonSNILS')))
            dbfRecord['SPEC'] = forceString(record.value('specialityCode'))
            dbfRecord['PROFIL'] = forceString(record.value('medicalAidProfileRegionalCode'))

            if endDate >= QDate(2018, 9, 1) and VP in ['11', '12', '301', '302', '43', '51', '52', '511', '522']:
                vmp = '31'
            elif endDate < QDate(2018, 9, 1) and VP in ['11', '12', '301', '302', '41', '42', '411', '422', '43', '51', '52', '511', '522']:
                vmp = '31'
            elif VP in ['401', '402']:
                vmp = '32'
            elif VP in ['801', '802']:
                vmp = '21'
            elif forceString(record.value('specialityCode')) in specialityList:
                vmp = '12'
            elif forceBool(record.value('specialityIsHigh')):
                vmp = '13'
            else:
                vmp = '11'
            dbfRecord['VMP'] = vmp

            DS_ONK = '1' if (directionCancerId or forceString(record.value('phasesCode')) == '10') else '0'
            dbfRecord['DS_ONK'] = DS_ONK
            if DS_ONK == '1':
                self.DS_ONKSet.add(eventId)

            if (dbfRecord['MKBX'][:1] == 'C' or dbfRecord['MKBX'][:2] == 'D0' or dbfRecord['MKBX'][:3] in ['D45', 'D46', 'D47']
                    or (dbfRecord['MKBX'] == 'D70' and dbfRecord['MKBXS'] >= 'C00' and dbfRecord['MKBXS'] <= 'C80.9' or dbfRecord['MKBXS'] == 'C97')):

                if ControlListOnkoId and ControlListOnkoId not in self.exportedOnkoInfo and DS_ONK == '0':
                    action = CAction(record=db.getRecord('Action', '*', ControlListOnkoId))

                    if action[u'Тип лечения'] == u'Хирургическое лечение':
                        dbfRecord['USL_TIP'] = '1'
                    elif action[u'Тип лечения'] == u'Лекарственная противоопухолевая терапия':
                        dbfRecord['USL_TIP'] = '2'
                    elif action[u'Тип лечения'] == u'Лучевая терапия':
                        dbfRecord['USL_TIP'] = '3'
                    elif action[u'Тип лечения'] == u'Химиолучевая терапия':
                        dbfRecord['USL_TIP'] = '4'
                    elif action[u'Тип лечения'] == u'Неспецифическое лечение (осложнения противоопухолевой терапии, установка/замена порт системы (катетера), прочее)':
                        dbfRecord['USL_TIP'] = '5'
                    elif action[u'Тип лечения'] == u'Диагностика':
                        dbfRecord['USL_TIP'] = '6'

                    if dbfRecord['USL_TIP'] == '1':
                        if action[u'Тип хирургического лечения'] == u'Первичной опухоли, в том числе с удалением регионарных лимфатических узлов':
                            dbfRecord['HIR_TIP'] = '1'
                        elif action[u'Тип хирургического лечения'] == u'Метастазов':
                            dbfRecord['HIR_TIP'] = '2'
                        elif action[u'Тип хирургического лечения'] == u'Симптоматическое, реконструктивно-пластическое, хирургическая овариальная суперссия, прочее':
                            dbfRecord['HIR_TIP'] = '3'
                        elif action[u'Тип хирургического лечения'] == u'Выполнено хирургическое стадирование (может указываться при раке яичника вместо "1")':
                            dbfRecord['HIR_TIP'] = '4'
                        elif action[u'Тип хирургического лечения'] == u'Регионарных лимфатических узлов без первичной опухоли':
                            dbfRecord['HIR_TIP'] = '5'
                        elif action[u'Тип хирургического лечения'] == u'Криохирургия/криотерапия, лазерная деструкция, фотодинамическая терапия':
                            dbfRecord['HIR_TIP'] = '6'

                    if dbfRecord['USL_TIP'] == '2':
                        if action[u'Линия лекарственной терапии'] == u'Первая линия':
                            dbfRecord['LEK_TIPL'] = '1'
                        elif action[u'Линия лекарственной терапии'] == u'Вторая линия':
                            dbfRecord['LEK_TIPL'] = '2'
                        elif action[u'Линия лекарственной терапии'] == u'Третья линия':
                            dbfRecord['LEK_TIPL'] = '3'
                        elif action[u'Линия лекарственной терапии'] == u'Линия после третьей':
                            dbfRecord['LEK_TIPL'] = '4'
                        elif action[u'Линия лекарственной терапии'] == u'Неоадъювантная':
                            dbfRecord['LEK_TIPL'] = '5'
                        elif action[u'Линия лекарственной терапии'] == u'Адъювантная':
                            dbfRecord['LEK_TIPL'] = '6'
                        elif action[u'Линия лекарственной терапии'] == u'Периоперационная (до хирургического лечения)':
                            dbfRecord['LEK_TIPL'] = '7'
                        elif action[u'Линия лекарственной терапии'] == u'Периоперационная (после хирургического лечения)':
                            dbfRecord['LEK_TIPL'] = '8'

                        if action[u'Цикл лекарственной терапии'] == u'Первый цикл линии':
                            dbfRecord['LEK_TIPV'] = '1'
                        elif action[u'Цикл лекарственной терапии'] == u'Последующие циклы линии (кроме последнего)':
                            dbfRecord['LEK_TIPV'] = '2'
                        elif action[u'Цикл лекарственной терапии'] == u'Последний цикл линии (лечение прервано)':
                            dbfRecord['LEK_TIPV'] = '3'
                        elif action[u'Цикл лекарственной терапии'] == u'Последний цикл линии (лечение завершено)':
                            dbfRecord['LEK_TIPV'] = '4'

                    if dbfRecord['USL_TIP'] in ['3', '4']:
                        if action[u'Тип лучевой терапии'] == u'Первичной опухоли/ложа опухоли':
                            dbfRecord['LUCH_TIP'] = '1'
                        elif action[u'Тип лучевой терапии'] == u'Метастазов':
                            dbfRecord['LUCH_TIP'] = '2'
                        elif action[u'Тип лучевой терапии'] == u'Симптоматическая':
                            dbfRecord['LUCH_TIP'] = '3'

                    if self.exportType != self.exportTypeInvoice:
                        # файл O
                        dbfRecordO = dbfO.newRecord()
                        dbfRecordO['OID'] = ControlListOnkoId
                        dbfRecordO['CODE_MO'] = params['codeLpu']
                        dbfRecordO['NS'] = self.processParams().get('iAccNumber')
                        dbfRecordO['SN'] = eventId
                        dbfRecordO['UID'] = UID
                        if action[u'Повод обращения'] == u'Первичное лечение (лечение пациента за исключением прогрессирования и рецидива)':
                            dbfRecordO['DS1_T'] = '0'
                        elif action[u'Повод обращения'] == u'Лечение при рецидиве':
                            dbfRecordO['DS1_T'] = '1'
                        elif action[u'Повод обращения'] == u'Лечение при прогрессировании':
                            dbfRecordO['DS1_T'] = '2'
                        elif action[u'Повод обращения'] == u'Динамическое наблюдение':
                            dbfRecordO['DS1_T'] = '3'
                        elif action[u'Повод обращения'] == u'Диспансерное наблюдение (здоров/ремиссия)':
                            dbfRecordO['DS1_T'] = '4'
                        elif action[u'Повод обращения'] == u'Диагностика (при отсутствии специфического лечения)':
                            dbfRecordO['DS1_T'] = '5'
                        elif action[u'Повод обращения'] == u'Симптоматическое лечение':
                            dbfRecordO['DS1_T'] = '6'

                        if action[u'Проведение консилиума'] == u'Отсутствует необходимость проведения консилиума':
                            dbfRecordO['PR_CONS'] = '0'
                        elif action[u'Проведение консилиума'] == u'Определена тактика обследования':
                            dbfRecordO['PR_CONS'] = '1'
                        elif action[u'Проведение консилиума'] == u'Определена тактика лечения':
                            dbfRecordO['PR_CONS'] = '2'
                        elif action[u'Проведение консилиума'] == u'Изменена тактика лечения':
                            dbfRecordO['PR_CONS'] = '3'
                        elif action[u'Проведение консилиума'] == u'Консилиум не проведен при наличии необходимости его проведения':
                            dbfRecordO['PR_CONS'] = '4'

                        if action[u'Дата проведения консилиума']:
                            dbfRecordO['D_CONS'] = pyDate(action[u'Дата проведения консилиума'])

                        if forceRef(record.value('cTNMPhase_id')):
                            value = getIdentification('rbTNMphase', forceRef(record.value('cTNMPhase_id')), '', raiseIfNonFound=False)
                            if value:
                                dbfRecordO['STAD'] = value
                            value = getIdentification('rbTumor', forceRef(record.value('cTumor_id')), '', raiseIfNonFound=False)
                            if value:
                                dbfRecordO['ONK_T'] = value
                            value = getIdentification('rbNodus', forceRef(record.value('cNodus_id')), '', raiseIfNonFound=False)
                            if value:
                                dbfRecordO['ONK_N'] = value
                            value = getIdentification('rbMetastasis', forceRef(record.value('cMetastasis_id')), '', raiseIfNonFound=False)
                            if value:
                                dbfRecordO['ONK_M'] = value
                        elif forceRef(record.value('pTNMPhase_id')):
                            value = getIdentification('rbTNMphase', forceRef(record.value('pTNMPhase_id')), '', raiseIfNonFound=False)
                            if value:
                                dbfRecordO['STAD'] = value
                            value = getIdentification('rbTumor', forceRef(record.value('pTumor_id')), '', raiseIfNonFound=False)
                            if value:
                                dbfRecordO['ONK_T'] = value
                            value = getIdentification('rbNodus', forceRef(record.value('pNodus_id')), '', raiseIfNonFound=False)
                            if value:
                                dbfRecordO['ONK_N'] = value
                            value = getIdentification('rbMetastasis', forceRef(record.value('pMetastasis_id')), '', raiseIfNonFound=False)
                            if value:
                                dbfRecordO['ONK_M'] = value

                        if  dbfRecordO['DS1_T'] in ['1', '2']:
                            if action[u'Выявление отдаленных метастазов'] == u'да':
                                dbfRecordO['MTSTZ'] = '1'

                        if dbfRecord['USL_TIP'] in ['3', '4'] and action[u'Суммарная очаговая доза']:
                            dbfRecordO['SOD'] = forceDouble(action[u'Суммарная очаговая доза'])
                            dbfRecordO['K_FR'] = forceInt(action[u'Количество фракций проведения лучевой терапии'])
                        # сведения о противоопухолевом лекарственном препарате
                        if dbfRecord['USL_TIP'] in ['2', '4']:
                            stmt = u"""select ni.value as REGNUM, a.begDate as DATE_INJ
        FROM Action a
        LEFT JOIN ActionType at ON at.id = a.actionType_id AND at.deleted = 0
        LEFT JOIN ActionPropertyType apt ON at.id = apt.actionType_id AND apt.deleted = 0 AND apt.typeName = 'Номенклатура ЛСиИМН'
        left JOIN ActionProperty ap ON ap.type_id = apt.id AND ap.action_id = a.id AND ap.deleted = 0
        LEFT JOIN ActionProperty_rbNomenclature apn ON apn.id = ap.id
        LEFT JOIN rbNomenclature n ON n.id = apn.value
        LEFT JOIN rbAccountingSystem `as` ON `as`.code = 'AccTFOMS'
        LEFT JOIN rbNomenclature_Identification ni on ni.master_id = n.id AND ni.system_id = `as`.id AND ni.deleted = 0 and ni.checkDate <= a.begDate
        WHERE a.event_id = {0} AND a.deleted = 0 AND at.class = 2 AND ni.value is NOT NULL
        ORDER BY a.begDate, ni.checkDate desc;""".format(eventId)
                            query = db.query(stmt)
                            if query.first():
                                medicamentRecord = query.record()
                                if medicamentRecord:
                                    dbfRecordO['CODE_SH'] = dbfRecord['KRIT']
                                    dbfRecordO['REGNUM'] = forceString(medicamentRecord.value('REGNUM'))
                                    dbfRecordO['DATE_INJ'] = pyDate(forceDate(medicamentRecord.value('DATE_INJ')))
                            if action[u'Проведение профилактики тошноты и рвотного рефлекса'] == u'да':
                                dbfRecordO['PPTR'] = 1
                            else:
                                dbfRecordO['PPTR'] = 0
                            wei = action[u'Масса тела (кг)']
                            if wei is not None:
                                dbfRecordO['WEI'] = round(forceDouble(wei), 1)
                            hei = action[u'Рост (см)']
                            if hei is not None:
                                dbfRecordO['HEI'] = forceInt(hei)
                            bsa = action[u'Площадь поверхности тела']
                            if bsa is not None:
                                dbfRecordO['BSA'] = round(forceDouble(bsa), 2)
                        self.RecordListO.append(dbfRecordO)
                        self.exportedOnkoInfo.add(ControlListOnkoId)
                        # файл С
                        for prop in [u'Противопоказания к проведению хирургического лечения', u'Противопоказания к проведению химиотерапевтического лечения',
                                     u'Противопоказания к проведению лучевой терапии', u'Отказ от проведения хирургического лечения',
                                     u'Отказ от проведения химиотерапевтического лечения', u'Отказ от проведения лучевой терапии',
                                     u'Гистологическое подтверждение диагноза не показано', u'Противопоказания к проведению гистологического исследования']:
                            if forceDate(action[prop]):
                                dbfRecordC = dbfC.newRecord()
                                CID = action.getProperty(prop)._id
                                dbfRecordC['CID'] = CID
                                dbfRecordC['CODE_MO'] = params['codeLpu']
                                dbfRecordC['NS'] = self.processParams().get('iAccNumber')
                                dbfRecordC['SN'] = eventId
                                dbfRecordC['OID'] = ControlListOnkoId
                                dbfRecordC['PROT'] = action.getProperty(prop).type().descr
                                dbfRecordC['D_PROT'] = pyDate(action[prop])
                                self.RecordListC.append(dbfRecordC)
                        # файл I
                        if GistologiaId or ImmunohistochemistryId:
                            if GistologiaId and GistologiaId not in self.exportedOnkoInfoI:
                                action = CAction(record=db.getRecord('Action', '*', GistologiaId))
                                for prop in action.getProperties():
                                    if prop.getValue():
                                        dbfRecordI = dbfI.newRecord()
                                        dbfRecordI['IID'] = prop._id
                                        dbfRecordI['CODE_MO'] = params['codeLpu']
                                        dbfRecordI['NS'] = self.processParams().get('iAccNumber')
                                        dbfRecordI['SN'] = eventId
                                        dbfRecordI['UID'] = UID
                                        dbfRecordI['DIAG_D'] = pyDate(action.getBegDate())
                                        dbfRecordI['DIAG_TIP'] = '1'
                                        dbfRecordI['DIAG_CODE'] = prop.type().descr
                                        dbfRecordI['DIAG_RSLT'] = N008dict.get(prop.getValue(), '')
                                        self.RecordListI.append(dbfRecordI)
                                self.exportedOnkoInfoI.add(GistologiaId)
                        if ImmunohistochemistryId and ImmunohistochemistryId not in self.exportedOnkoInfoI:
                                action = CAction(record=db.getRecord('Action', '*', ImmunohistochemistryId))
                                for prop in action.getProperties():
                                    if prop.getValue():
                                        dbfRecordI = dbfI.newRecord()
                                        dbfRecordI['IID'] = prop._id
                                        dbfRecordI['CODE_MO'] = params['codeLpu']
                                        dbfRecordI['NS'] = self.processParams().get('iAccNumber')
                                        dbfRecordI['SN'] = eventId
                                        dbfRecordI['UID'] = UID
                                        dbfRecordI['DIAG_D'] = pyDate(action.getBegDate())
                                        dbfRecordI['DIAG_TIP'] = '2'
                                        dbfRecordI['DIAG_CODE'] = prop.type().descr
                                        dbfRecordI['DIAG_RSLT'] = N011dict.get(prop.getValue(), '')
                                        self.RecordListI.append(dbfRecordI)
                                self.exportedOnkoInfoI.add(ImmunohistochemistryId)
            self.RecordListU.append(dbfRecord)

            if self.exportType != self.exportTypeInvoice:
                # Файл N
                if hospitalDirectionActionId and hospitalDirectionActionId not in self.exportedHospitalDirection:
                    directionAction = CAction(record=db.getRecord('Action', '*', hospitalDirectionActionId))
                    if directionAction.getType().flatCode == 'planning':
                        orgstructId = forceRef(directionAction[u'Подразделение'])
                        directionOrgCode = self.getOrgStructureBookkeeperCode(orgstructId) if orgstructId else None
                    else:
                        orgId = forceRef(directionAction[u'Куда направляется'])
                        directionOrgCode = self.getOrgInfisCode(orgId) if orgId else None
                    dbfRecord = dbfN.newRecord()
                    dbfRecord['CODE_MO'] = params['codeLpu']
                    dbfRecord['NS'] = self.processParams().get('iAccNumber')
                    dbfRecord['SN'] = eventId
                    dbfRecord['NAPR_N'] = '%s_%s' % (params['codeLpu'], forceString(directionAction[u'Номер направления']))
                    if directionOrgCode:
                        dbfRecord['NAPR_MO'] = directionOrgCode
                    dbfRecord['NAPR_D'] = pyDate(endDate)
                    dbfRecord['DOC_SS'] = formatSNILS(forceString(record.value('execPersonSNILS')))
                    self.RecordListN.append(dbfRecord)
                    self.exportedHospitalDirection.add(hospitalDirectionActionId)

                # Файл R
                for RID in [appointmentsActionId, directionCancerId]:
                    if RID and RID not in self.exportedAppointments:
                        dbfRecord = dbfR.newRecord()
                        appointmentsAction = CAction(record=db.getRecord('Action', '*', RID))
                        dbfRecord['RID'] = RID
                        dbfRecord['CODE_MO'] = params['codeLpu']
                        dbfRecord['NS'] = self.processParams().get('iAccNumber')
                        dbfRecord['SN'] = eventId
                        dbfRecord['UID'] = UID
                        dbfRecord['NAZR_D'] = pyDate(appointmentsAction.getEndDate())
                        directionOrgCode = self._getAttachOrgCodes(forceRef(appointmentsAction[u'Куда направляется'])).get('attachOrgSmoCode', None)
                        if directionOrgCode:
                            dbfRecord['NAPR_MO'] = directionOrgCode
                        if appointmentsAction.getType().flatCode == 'directionCancer':
                            NAZR = u'Вид направления'
                            VID_OBS = u'Метод диагностического исследования'
                        else:
                            NAZR = u'Назначения: направлен на'
                            VID_OBS = u'Назначенные обследования'

                        if appointmentsAction[NAZR] == u'консультацию в мед организацию по месту прикрепления':
                            dbfRecord['NAZR'] = '1'
                        elif appointmentsAction[NAZR] == u'консультацию в иную мед организацию':
                            dbfRecord['NAZR'] = '2'
                        elif appointmentsAction[NAZR] == u'обследование':
                            dbfRecord['NAZR'] = '3'
                        elif appointmentsAction[NAZR] == u'в дневной стационар':
                            dbfRecord['NAZR'] = '4'
                        elif appointmentsAction[NAZR] == u'госпитализацию':
                            dbfRecord['NAZR'] = '5'
                        elif appointmentsAction[NAZR] == u'в реабилитационное отделение':
                            dbfRecord['NAZR'] = '6'
                        elif appointmentsAction[NAZR] == u'Направление к онкологу':
                            dbfRecord['NAZR'] = '7'
                        elif appointmentsAction[NAZR] == u'Направление на биопсию':
                            dbfRecord['NAZR'] = '8'
                        elif appointmentsAction[NAZR] == u'Направление на дообследование':
                            dbfRecord['NAZR'] = '9'
                        elif appointmentsAction[NAZR] == u'Направление для первичного определения тактики обследования или тактики лечения':
                            dbfRecord['NAZR'] = 'a'

                        if appointmentsAction[VID_OBS] == u'лабораторная диагностика':
                            dbfRecord['VID_OBS'] = '1'
                        elif appointmentsAction[VID_OBS] == u'инструментальная диагностика':
                            dbfRecord['VID_OBS'] = '2'
                        elif appointmentsAction[VID_OBS] == u'методы лучевой диагностики, за исключением дорогостоящих':
                            dbfRecord['VID_OBS'] = '3'
                        elif appointmentsAction[VID_OBS] == u'дорогостоящие методы лучевой диагностики (КТ, МРТ, ангиография)':
                            dbfRecord['VID_OBS'] = '4'

                        if appointmentsAction.getType().flatCode == 'appointments':
                            if forceDate(record.value('endDate')) >= QDate(2018, 4, 1):
                                spec = self.getSpecialityRegionalCode(appointmentsAction[u'Специальность'])
                            else:
                                spec = self.getSpecialityFederalCode(appointmentsAction[u'Специальность'])
                            dbfRecord['SPEC'] = spec
                            dbfRecord['PROFIL'] = self.getMedicalAidProfileRegionalCode(appointmentsAction[u'Профиль МП'])
                            dbfRecord['KPK'] = self.getHospitalBedProfileCode(appointmentsAction[u'Профиль койки'])

                        dbfRecord['NAPR_USL'] = self.getServiceInfis(appointmentsAction[u'Медицинская услуга'])
                        self.RecordListR.append(dbfRecord)
                        self.exportedAppointments.add(RID)


    def processPerson(self, dbf, record, params):
        if self.exportType in [self.exportTypeP25, self.exportTypePreControlP25, self.exportTypeInvoice]:
            (dbfP, dbfU, dbfD, dbfN, dbfR, dbfO, dbfI, dbfC) = dbf
            row = dbfD.newRecord()
            snils = forceString(record.value('snils'))
            row['CODE_MO'] = params['codeLpu']
            row['SNILS'] = formatSNILS(snils)
            row['FIO'] = forceString(record.value('lastName'))
            row['IMA'] = forceString(record.value('firstName'))
            row['OTCH'] = forceString(record.value('patrName'))
            row['POL'] = self.sexMap.get(forceInt(record.value('sex')), '')
            row['DATR'] = pyDate(forceDate(record.value('birthDate')))
            row['DATN'] = pyDate(forceDate(record.value('DATN')))
            # dato = forceDate(record.value('DATO'))
            # if dato != QDate(2099, 12, 31):
            #     row['DATO'] = pyDate(dato)
            self.RecordListD.append(row)


    @pyqtSignature('int')
    def on_cmbExportType_currentIndexChanged(self, index):
        if index == self.exportTypeInvoice:
            self.chkMakeInvoice.setChecked(True)
        self.chkMakeInvoice.setEnabled(index in [self.exportTypeP25, self.exportTypePreControlP25])
        self.edtRegistryNumber.setEnabled(index in [self.exportTypeP25, self.exportTypePreControlP25, self.exportTypeInvoice])

    @pyqtSignature('bool')
    def on_rbTFOMS_toggled(self, checked):
        self.cmbPayer.setEnabled(not checked)


    @pyqtSignature('bool')
    def on_rbSMO_toggled(self, checked):
        self.cmbPayer.setEnabled(checked)


class CExportPage2(CAbstractExportPage2, Ui_ExportR23NativePage2):
    def __init__(self, parent):
        CAbstractExportPage2.__init__(self, parent,  'R23NATIVE')
        self.setSubTitle(u'для выполнения шага нажмите кнопку "Завершить"')

    def validatePage(self):
        # success = self.moveFiles(self.fileList)
        #
        # if success:
        #     QtGui.qApp.preferences.appPrefs[
        #         '%sExportDir' % self.prefix] = toVariant(self.edtDir.text())
        #     self.wizard().setAccountExposeDate()
        return True

    def setFileList(self, fileList):
        self.fileList = fileList


    def saveExportResults(self):

        baseName = self._parent.page1.getDbfBaseName()
        zipFileName = self._parent.page1.getZipFileName()
        zipFilePath = os.path.join(forceStringEx(self._parent.getTmpDir()), zipFileName)
        zf = ZipFile(zipFilePath, 'w', allowZip64=True)
        exportType = self._parent.page1.exportType

        if exportType in [CExportPage1.exportTypeP25, CExportPage1.exportTypePreControlP25]:
            prefixes = ('P', 'U', 'D', 'N', 'R', 'O', 'I', 'C')
        elif exportType == CExportPage1.exportTypeInvoice:
            prefixes = []
        else:
            prefixes = ('P')

        # Добавляем фактуру
        if self._parent.page1.mkInvoice:
            filePath = os.path.join(forceStringEx(self.getTmpDir()), os.path.basename("schfakt.html"))
            zf.write(filePath, "schfakt.html", ZIP_DEFLATED)

        for src in prefixes:
            filePath = os.path.join(forceStringEx(self.getTmpDir()), os.path.basename(src + baseName))
            zf.write(filePath, src+os.path.basename(self._parent.page1.getDbfBaseName()), ZIP_DEFLATED)

        zf.close()
        dst = os.path.join(forceStringEx(self.edtDir.text()), zipFileName)
        success, result = QtGui.qApp.call(self, shutil.move, (zipFilePath, dst))
        return success


class CExportR23NoKeysDialog(CDialogBase, Ui_ExportR23NoKeysDialog):
    def __init__(self, parent, items, title=None, message=None):
        CDialogBase.__init__(self,  parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.title = title
        self.message = message
        self.setWindowTitleEx(self.title)
        self.label.setText(self.message)
        self.addModels('NoKeys', CNoKeysModel(self))
        self.tblAccountItems.setModel(self.modelNoKeys)
        self.tblAccountItems.setSortingEnabled(True)
        self.connect(self.tblAccountItems.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)
        self.items = []
        for item in items:
            self.items.append(items[item])
        self.modelNoKeys.loadItems(self.items)
        self.addObject('btnPrint', QtGui.QPushButton(u'Печать', self))
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.connect(self.btnPrint, SIGNAL('clicked()'), self.on_btnPrint_clicked)
        self.headerSortIndicator = None
        self.labelCount.setText(u'Всего персональных счетов: {0}'.format(len(self.items)))


    def setSort(self, col):
        model = self.tblAccountItems.model()
        header = self.tblAccountItems.horizontalHeader()
        header.setSortIndicatorShown(True)
        if self.headerSortIndicator == Qt.DescendingOrder:
            self.headerSortIndicator = Qt.AscendingOrder
        else:
            self.headerSortIndicator = Qt.DescendingOrder
        header.setSortIndicator(col, self.headerSortIndicator)
        items = model.items()
        items.sort(key=lambda x: x[col], reverse=self.headerSortIndicator == Qt.DescendingOrder)
        model.reset()


    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        rowSize = 4
        report = CReportBase()
        params = report.getDefaultParams()
        report.saveDefaultParams(params)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.message)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        cursor.insertHtml('<br/><br/>')
        table = createTable(cursor, [
            ('10%', [u'Дата реестра'], CReportBase.AlignCenter),
            ('10%', [u'Номер реестра'], CReportBase.AlignRight),
            ('10%', [u'Номер перс. счета'], CReportBase.AlignRight),
            ('70%', [u'ФИО'], CReportBase.AlignLeft),
        ]
                            )
        for item in self.modelNoKeys.items():
            row = table.addRow()
            for col in xrange(rowSize):
                if col == 0:
                    table.setText(row, col, formatDate(item[col]))
                else:
                    table.setText(row, col, item[col])
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertHtml('<br/><br/>')

        reportView = CReportViewDialog(self)
        reportView.setWindowTitle(self.title)
        reportView.setOrientation(QtGui.QPrinter.Portrait)
        reportView.setText(doc)
        reportView.exec_()


class CNoKeysModel(QAbstractTableModel):
    u'Список счетов без ключей'
    def __init__(self, parent):
        QAbstractTableModel.__init__(self)
        self._items = []
        self.tableName = None
        self.aligments = [CCol.alg['c'], CCol.alg['r'], CCol.alg['r'], CCol.alg['l']]


    def setTable(self, tableName):
        self.tableName = tableName


    def loadItems(self, items):
        self._items = items
        self.reset()

    def items(self):
        return self._items


    def columnCount(self, index=None):
        return 4


    def rowCount(self, index=None):
        return len(self._items)


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant((u'Дата реестра', u'Номер реестра', u'Номер перс. счет', u'ФИО')[section])
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            row = index.row()
            column = index.column()
            item = self._items[row]
            return QVariant(item[column])
        elif role == Qt.TextAlignmentRole:
            column = index.column()
            return self.aligments[column]
        return QVariant()


class CInvoice:
    def __init__(self):
        self.invoice = None
        self.invoiceDict = {
            u'Стационар': {u'kolsn': 0, u'kolkd': 0, u'vpsumm': 0.0},
            u'ВМП': {u'kolsn': 0, u'kolkd': 0, u'vpsumm': 0.0},
            u'Дневной стационар': {u'kolsn': 0, u'kolkd': 0, u'vpsumm': 0.0},
            u'ЭКО': {u'kolsn': 0, u'kolkd': 0, u'vpsumm': 0.0},
            u'Стационар дневного пребывания': {u'kolsn': 0, u'kolkd': 0, u'vpsumm': 0.0},
            u'Дисп. детей-сирот': {u'vpsumm': 0.0, u'kolpos': 0},
            u'Дисп. детей без попечения': {u'vpsumm': 0.0, u'kolpos': 0},
            u'Медосм. несовершеннолетних': {u'vpsumm': 0.0, u'kolpos': 0},
            u'Дисп. взрослых': {u'vpsumm': 0.0, u'kolpos': 0},
            u'Медосм. взрослых': {u'vpsumm': 0.0, u'kolpos': 0},
            u'Посещения с профилактическими и иными целями': {u'vpsumm': 0.0, u'kolpos': 0, u'obr': 0, u'cpo': 0,
                                                              u'cpotw': 0, u'sum_pos': 0,
                                                              u'sum_obr': 0, u'sum_posotw': 0},
            u'Поликлиника (прикрепленное население)': {u'vpsumm': 0.0, u'fl': 0},
            u'ФАП': {u'vpsumm': 0.0, u'kolpos': 0, u'obr': 0, u'cpo': 0, u'cpotw': 0, u'sum_pos': 0, u'sum_obr': 0, u'sum_posotw': 0, u'fl': 0},
            u'Неотложная помощь': {u'vpsumm': 0.0, u'kolpos': 0},
            u'Диагностические исследования (лабораторные исследования)': {u'vpsumm': 0.0, u'kolpos': 0},
            u'КТ': {u'vpsumm': 0.0, u'kolpos': 0},
            u'МРТ': {u'vpsumm': 0.0, u'kolpos': 0},
            u'УЗИ ССС': {u'vpsumm': 0.0, u'kolpos': 0},
            u'Эндоскопия': {u'vpsumm': 0.0, u'kolpos': 0},
            u'МГИ': {u'vpsumm': 0.0, u'kolpos': 0},
            u'Гистология': {u'vpsumm': 0.0, u'kolpos': 0},
            u'Стоматология': {u'kolpos': 0, u'vpsumm': 0.0, u'uet': 0.0, u'obr': 0, u'cpo': 0, u'cpotw': 0},
            u'Скорая': {u'vpsumm': 0.0, u'kolpos': 0},
            u'summ': 0.0
        }

    def getInvoice(self):
        return self.invoice

    def setInvoice(self, invoice):
        self.invoice = invoice

    def getInvoiceDict(self):
        return self.invoiceDict

    def setInvoiceDict(self, invoiceDict):
        self.invoiceDict = invoiceDict