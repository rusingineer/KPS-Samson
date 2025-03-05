# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2015 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


import re
import os.path
import sys
from sys import *
import codecs
#import datetime

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *

from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CReportViewDialog
from library.Utils import *
from library.roman import itor
from library import dbfpy
from library.dbfpy.dbf import Dbf

from Exchange.Utils import *
import create_sql
import import_sql


from Ui_Progress import Ui_ProgressDialog


class CProgressDialog(QtGui.QDialog, Ui_ProgressDialog):
    __pyqtSignals__ = ('startWork()', )

    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent #wtf? скрывать Qt-шный parent - это плохая затея
        self.setupUi(self)
        self.setPlacesCount(0)
        self.setOrgsCount(0)
        self.setClientsCount(0)
        self.setServicesCount(0)
#        self._setCount(self.prbServiceStandarts, 0)
#        self._setCount(self.prbMKBStandarts, 0)
#        self._setCount(self.prbMedicaments, 0)
#        self._setCount(self.prbMedicamentStandarts, 0)

        self.start()
        self.connect(self, SIGNAL('startWork(bool)'), self.startWork, Qt.QueuedConnection)

        self.policyTypeId       = None
        self.copyToActionType = False
        self.actionTypeParentGroupId = None
        self.mustImportMes = False

        self.sexMap = {u'Ж':2, u'ж':2, u'М':1, u'м':1}
        self.mapSpecialityCodeNameToId = {}
        self.mapActionTypeCodeNameToId = {}
        self.mapActionTypeCodeToId = {}

        self.mapAreaToKLADR = {}
        self.mapAreaAndPlaceToKLADR = {}
        self.streetMap = {}
        self.cityMap = {}
        self.orgMap = {}
        self.orgCache = {}

        self.insurerCache = {}
        self.showLog = True
        self.importClients = False
        self.matureNetId = None

        self.nProcessed = 0
        self.nUpdated = 0
        self.nSkipped = 0
        self.nAdded = 0
        self.logBrowser.document().setMaximumBlockCount(1024)

        self.db = QtGui.qApp.db
        self.tableClient = self.db.table('Client')
        self.tableClientWork = self.db.table('ClientWork')
        self.tableOrganisation = self.db.table('Organisation')


    def log(self, str,  forceLog = False):
        if self.showLog or forceLog:
            self.logBrowser.append(str)
            self.logBrowser.update()


    def _setCount(self, progressBar, cnt):
        if cnt:
            progressBar.setValue(0)
            progressBar.setMaximum(cnt)
            progressBar.setEnabled(True)
            progressBar.setTextVisible(True)
        else:
            progressBar.setValue(0)
            progressBar.setMaximum(1)
            progressBar.setEnabled(False)
            progressBar.setTextVisible(False)


    def setPlacesCount(self, cnt):
        self._setCount(self.prbPlaces, cnt)


    def setClientsCount(self, cnt):
        self._setCount(self.prbClients, cnt)


    def setOrgsCount(self,  cnt):
        self._setCount(self.prbOrgs,  cnt)


    def setServicesCount(self,  cnt):
        self._setCount(self.prbServices,  cnt)


    def setOptions(self, actionTypeParentGroupId, mustImportMes, mustRecognizeNomenclature, fillEIS):
        self.actionTypeParentGroupId = actionTypeParentGroupId
        self.mustImportMes = mustImportMes
        self.mustRecognizeNomenclature = mustRecognizeNomenclature
        self.fillEIS = fillEIS
#        for label in self.lblServiceStandarts, self.lblMKBStandarts, self.lblMedicaments, self.lblMedicamentStandarts:
#            label.setEnabled(self.mustImportMes)
#        for progressBar in self.prbServiceStandarts, self.prbMKBStandarts, self.prbMedicaments, self.prbMedicamentStandarts:
#            progressBar.setEnabled(self.mustImportMes)


    def start(self):
        self.processDone = False
        self.aborted = False
        self.btnCancel.setText(u'Отмена')


    def stop(self):
        self.processDone = True
        self.btnCancel.setText(u'Закрыть')


    def done(self, r):
        self.stop()
        QtGui.QDialog.done(self, r)


    def exec_(self, importServices=False):
        self.emit(SIGNAL('startWork(bool)'), importServices)
        return QtGui.QDialog.exec_(self)


    @classmethod
    def isNomenclatureService(cls, code):
        return code and len(code) and code[0] in ('A', 'B', 'D', 'E', 'F', u'А', u'В', u'Д', u'Е', u'Ф') and code[3] == '.'


    @pyqtSignature('')
    def on_btnCancel_clicked(self):
        if self.processDone:
            self.accept()
        else:
            self.aborted = True


    def startWork(self,  importServices):
        self.start()
        QtGui.qApp.call(self, self.importServices if importServices else self.work)
        self.stop()
        self.printReport()


    def work(self):
        self.orgCache = {}
        rbDir = forceString(self.parent.edtRBDirName.text())
        spr01path = os.path.join(rbDir,'spr01.dbf')
        spr02path = os.path.join(rbDir, 'spr02.dbf')
        # spr17path = os.path.join(rbDir, 'spr17.dbf')
        spr81path = os.path.join(rbDir, 'spr81.dbf')
        dbfMO = None
        dbfPayers = None
        dbfMOFR = None
        # dbfMedicalAidUnit = None
        cnt = 0
        if os.path.isfile(spr01path):
            dbfMO = Dbf(spr01path, readOnly=True, encoding='cp866')
            cnt+= len(dbfMO)
        if os.path.isfile(spr02path):
            dbfPayers = Dbf(spr02path, readOnly=True, encoding='cp866')
            cnt += len(dbfPayers)
        if os.path.isfile(spr81path):
            dbfMOFR = Dbf(spr81path, readOnly=True, encoding='cp866')
            cnt += len(dbfMOFR)
        # if os.path.isfile(spr17path):
        #     dbfMedicalAidUnit = Dbf(spr17path, readOnly=True, encoding='cp866')
        #     cnt += len(dbfMedicalAidUnit)
        if self.importClients:
            dbfRegistry = Dbf(forceString(self.parent.edtMainDataFileName.text()), readOnly=True, encoding='cp866')

        self.nProcessed = 0
        self.nUpdated = 0
        self.nSkipped = 0
        self.nAdded = 0
        self.setOrgsCount(cnt)
        if dbfMO:
            self.process(dbfMO, self.processLPU, self.prbOrgs)
        if dbfPayers:
            self.process(dbfPayers, self.processOrg, self.prbOrgs)
        if dbfMOFR:
            self.process(dbfMOFR, self.processMORF, self.prbOrgs)

        # if dbfMedicalAidUnit:
        #     self.process(dbfMedicalAidUnit, self.processMedicalAidUnit, self.prbOrgs)

        self.log(u'Загрузка организаций завершена: обработано %d,'\
                    u' обновлено %d, добавлено %d, пропущено %d' % (self.nProcessed,
                    self.nUpdated, self.nAdded, self.nSkipped))

        if self.importClients:
            self.nProcessed = 0
            self.setClientsCount(len(dbfRegistry))
            self.process(dbfRegistry, self.processClient, self.prbClients)
            dbfRegistry.close()

        for d in (dbfMO, dbfPayers, dbfMOFR):
            if d is not None:
                d.close()


    def runProgramScript(self, module, title):
        #file = codecs.open(name, encoding='utf-8', mode='rt')
        #if file is None:
        #    QtGui.QMessageBox.warning(self, title,
        #                u'Не могу открыть файл %s:\n%s.'%(name, file.errorString( )))
        #    return False
        QtGui.qApp.processEvents()
        error = runScript(QtGui.qApp.db, self.logBrowser, module.COMMAND.split('\n'))
        if error is not None:
            QtGui.QMessageBox.warning(self, title,
                        u'Ошибка при выполнении %s:\n%s.'%(str(module), error.text()))
            self.logBrowser.append(unicode(error.text()))
            return False
        #file.close()
        return True


    def importServices(self):
        finished = False
        if self.runProgramScript(create_sql, u'Создание временных таблиц'):
            self.copyToActionType = self.parent.chkCopyToActionType.isChecked()
            dbfServices = Dbf(forceString(self.parent.edtServiceFileName.text()), readOnly=True, encoding='cp866')

            self.setServicesCount(len(dbfServices))
            self.process(dbfServices, self.processService, self.prbServices)

            dbfServices.close()
            finished = True
#             if finished and self.copyToActionType:
#                 QtGui.qApp.db.query(u"""SET SQL_SAFE_UPDATES = 0;
# Update ActionType at
#   LEFT JOIN rbService s ON s.id = at.nomenclativeService_id
#   left JOIN ActionType at2 on at2.code = s.infis AND at2.name = s.name AND at2.deleted = 0
# set at.showInForm = 0
# WHERE at.code = s.infis AND at.name <> s.name AND at.deleted = 0 AND LEFT(at.code, 1) IN ('A', 'B', 'K', 'S', 'G', 'V')
# AND at2.id is NOT null;
# SET SQL_SAFE_UPDATES = 0;
#                 """)

        if finished and self.mustImportMes:
#            dbfServiceStandarts = dbf.Dbf(self.parent.getServiceStandartFileName(), readOnly=True, encoding='cp866')
#            dbfMKBStandarts = dbf.Dbf(self.parent.getMKBStandartFileName(), readOnly=True, encoding='cp866')
#            dbfMedicaments = dbf.Dbf(self.parent.getMedicamentFileName(), readOnly=True, encoding='cp866')
#            dbfMedicamentStandarts = dbf.Dbf(self.parent.getMedicamentStandartFileName(), readOnly=True, encoding='cp866')
#            self._setCount(self.prbServiceStandarts, len(dbfServiceStandarts))
#            self._setCount(self.prbMKBStandarts, len(dbfMKBStandarts))
#            self._setCount(self.prbMedicaments, len(dbfMedicaments))
#            self._setCount(self.prbMedicamentStandarts, len(dbfMedicamentStandarts))
#            self.process(dbfServiceStandarts, self.processServiceStandart, self.prbServiceStandarts)
#            self.process(dbfMKBStandarts, self.processMKBStandart, self.prbMKBStandarts)
#            self.process(dbfMedicaments, self.processMedicament, self.prbMedicaments)
#            self.process(dbfMedicamentStandarts, self.processMedicamentStandart, self.prbMedicamentStandarts)
#            dbfServiceStandarts.close()
#            dbfMKBStandarts.close()
#            dbfMedicaments.close()
#            dbfMedicamentStandarts.close()
            finished = self.runProgramScript(import_sql, u'Импорт данных')
        return finished


    def process(self, dbf, step, progressBar):
        self.lblElapsed.setText(u'Текущая операция: ??? зап/с, окончание в ??:??:??')
        time = QTime()
        time.start()
        startPos = 0
        oldSpeed = 0

        for record in dbf:
            QtGui.qApp.processEvents()
            if self.aborted:
                self.reject()
                return
            progressBar.setValue(progressBar.value()+1)
            QtGui.qApp.db.transaction()
            try:
                step(record)
                QtGui.qApp.db.commit()
                self.nProcessed += 1
            except:
                QtGui.qApp.db.rollback()
                raise

            elapsed =time.elapsed()

            if elapsed != 0 and (progressBar.value()-startPos>100):
                startPos = progressBar.value()
                oldSpeed = 100*1000/elapsed
                newSpeed = (oldSpeed+100*1000/elapsed)/2
                if newSpeed != 0:
                    finishTime = QTime.currentTime().addSecs(progressBar.maximum()/newSpeed)
                    self.lblElapsed.setText(u'Текущая операция: %03.f зап/с, окончание в %s' % (newSpeed, finishTime.toString('hh:mm:ss')))
                    time.restart()

# *****************************************************************************************

    def processLPU(self, row):
        OGRN = forceString(row['OGRN'])
        name = forceString(row['NAME'])

        if not OGRN:
            self.nSkipped += 1
            self.log(u'<b><font color=red>Пропуск</font></b> `%s` отсутствует ОГРН.' % name)
            return

        regionalCode = forceString(row['CODE'])
        federalCode = forceString(row['CODE_RF'])
        name = forceString(row['NAME'])
        endDate = forceDate(row['DATO'])
        codeNew = forceString(row['CODE_NEW'])
        isActive = True
        notes = u''

        if endDate:
            isActive = False
        if codeNew:
            notes += u'Новый код: {0}; '.format(codeNew)
        if forceInt(row['IS_GUZ']) != 0:
           notes += u'Террит., федеральная МО. '

        orgId = self.findOrgByOGRNandRegionalCode(OGRN, regionalCode)

        if orgId:
            self.updateOrg(orgId, name, name, '', '', OGRN, '03000',
                '', '', '', '', None, None, None, regionalCode, federalCode, isActive, notes.strip(), netId=self.matureNetId, setIsMedical=True)
            self.log(u'<b><font color=green>Обновляем</font></b> `%s`, ОГРН `%s`, код `%s`.' % (name, OGRN, regionalCode))
            self.nUpdated += 1
        else:
            orgId = self.addOrg(name, name, '', '', '', '', OGRN, '03000',
                '', '', '', '', None, None, None, regionalCode, federalCode, isActive, notes.strip(), netId=self.matureNetId, setIsMedical=True)
            self.log(u'<b><font color=blue>Добавляем</font></b> `%s`, ОГРН `%s`, код `%s`.' % (name, OGRN, regionalCode))
            self.nAdded += 1

        self.orgMap[regionalCode] = orgId

# *****************************************************************************************

    def processMORF(self, row):
        OGRN = forceString(row['OGRN'])
        fullName = forceString(row['FNAME'])
        shortName = forceString(row['SNAME'])
        OKATO = forceString(row['OKATO'])
        code = forceString(row['CODE'])
        INN = forceString(row['INN'])
        KPP = forceString(row['KPP'])
        address = forceString(row['ADRES'])
        isActive = not bool(forceDate(row['D_END']))
        if OKATO == '03000':
            self.nSkipped += 1
            self.log(u'<b><font color=yellow>Пропуск</font></b> `%s`. МО КК.' % shortName)
            return
        if not OGRN:
            self.nSkipped += 1
            self.log(u'<b><font color=red>Пропуск</font></b> `%s` отсутствует ОГРН.' % shortName)
            return

        orgId = self.findOrgByOGRNandFederalCode(OGRN, code)

        if orgId:
            self.updateOrg(orgId, shortName, fullName, '', '', OGRN, OKATO,
                           address, '', '', '', None, None, None, '', code, isActive=isActive, notes='',
                           netId=self.matureNetId, setIsMedical=True)
            self.log(
                u'<b><font color=green>Обновляем</font></b> `%s`, ОГРН `%s`, код `%s`.' % (shortName, OGRN, code))
            self.nUpdated += 1
        else:
            self.addOrg(shortName, fullName, INN, KPP, '', '', OGRN, OKATO,
                                address, '', '', '', None, None, None, '', code, isActive=isActive, notes='',
                                netId=self.matureNetId, setIsMedical=True)
            self.log(
                u'<b><font color=blue>Добавляем</font></b> `%s`, ОГРН `%s`, код `%s`.' % (shortName, OGRN, code))
            self.nAdded += 1

# *****************************************************************************************

    def processService(self, row):
        code = forceString(row['CODE'].strip())
        if code and not (code[:1] in ['A', 'B', 'G', 'V'] or code[:2] in ['st', 'ds']):
            return
        endDate = QDate(row['DATO']) if row['DATO'] else QDate(2200, 1, 1)
        if endDate < QDate(QDate.currentDate().year()-3, 1, 1):
            return
        name = forceString(row['NAME_LONG'].strip())
        begDate = QDate(row['DATN']) if row['DATN'] else None

        uet = forceDouble(row['UET'])

        serviceId = self.findServiceByCodeAndNameEx(code, name)

        if serviceId:
            self.updateService(serviceId, code, name, begDate, endDate, uet)
        else:
            serviceId = self.addService(code, name, code, begDate, endDate, uet)
        insertRecordFromDbf(QtGui.qApp.db, 'tmpService', row, range(12) + [-1, -1]*2)


        if self.copyToActionType and code[0] in ['A', 'B', 'V']:
            class_id = 3
            groupCode = ''
            
            actionTypeId, class_id = self.findActionTypeByCodeAndName(code, name)
            
            if not actionTypeId:
                groupId = self.actionTypeParentGroupId
                if code[0] in ['A', 'B']:
                    groupCode = code.split(u'.')
                    groupCode = u'.'.join(groupCode[0:2])
    
                if groupCode != '' and groupCode != code:
                    groupId, class_id = self.findActionTypeByCode(groupCode)
    
                    if not groupId:
                        self.log(u'Не найдена группа с кодом "%s" для услуги (%s) "%s".' % \
                                (groupCode, code, name))

            if actionTypeId:
                self.updateActionType(actionTypeId, serviceId, endDate)
            else:
                # если услуга действующая, то добавляем
                if endDate > QDate.currentDate():
                    newId = self.addActionType(code, name, groupId, class_id, serviceId, endDate)
                    # добавляем запись в ActionType_Service
                    if newId:
                        tableActionType_Service = QtGui.qApp.db.table('ActionType_Service')
                        newRecord = tableActionType_Service.newRecord()
                        newRecord.setValue('master_id',  toVariant(newId))
                        newRecord.setValue('service_id',  toVariant(serviceId))
                        QtGui.qApp.db.insertRecord(tableActionType_Service, newRecord)

    def processServiceStandart(self, row):
        insertRecordFromDbf(QtGui.qApp.db, 'tmpServiceStandart', row, range(5) + [-1, -1])

    def processMKBStandart(self, row):
        insertRecordFromDbf(QtGui.qApp.db, 'tmpMKBStandart', row, range(2) + [-1, -1])

    def processMedicament(self, row):
        insertRecordFromDbf(QtGui.qApp.db, 'tmpMedicament', row, range(12) + [-1, -1])

    def processMedicamentStandart(self, row):
        insertRecordFromDbf(QtGui.qApp.db, 'tmpMedicamentStandart', row, range(9) + [-1, -1])

# *****************************************************************************************

    def processArea(self, record):
        code = forceInt(record['KGOR'])
        name = forceString(record['GOROD'])
        table = QtGui.qApp.db.table('kladr.KLADR')
        record = QtGui.qApp.db.getRecordEx(table, 'CODE',
            [table['NAME'].eq(name), table['CODE'].like('510%'),
            ], 'CODE')

        KLADRCode = forceString(record.value(0)) if record else None
        if KLADRCode:
            self.mapAreaToKLADR[code] = KLADRCode
            self.updateKLADRInfisCode(KLADRCode,  code)
        else:
            self.cityMap[code] = name
            self.log(u'! Населённый пункт "%s" (код "%s")'
                        u' не найден в КЛАДРе.' % (name,  code),  True)

# *****************************************************************************************

    def processStreet(self, record):
        codeEx = record['CODUL']
        code = forceInt(codeEx) if codeEx else None
        name = forceString(record['ULIC'])
        self.streetMap[code] = name

# *****************************************************************************************

    def processOrg(self, row):
        regionalCode = forceString(row['CODE'])
        federalCode = forceString(row['CODE_RF'])
        name = forceString(row['NAME'])
        OGRN = forceString(row['OGRN'])

        endDate = forceDate(row['DATO'])
        isActive = True

        if endDate:
            isActive = False

        if not OGRN:
            self.nSkipped += 1
            self.log(u'<b><font color=red>Пропуск</font></b> `%s` отсутствует ОГРН.' % name)
            return

        orgId = self.findOrgByOGRNandRegionalCode(OGRN, regionalCode)

        if orgId:
            self.updateOrg(orgId, name, name, '', '', OGRN, '03000',
                    '', '', '', '', None, None, None, regionalCode, federalCode, isActive, area='23'.ljust(13,'0'), isInsurer=True)
            self.log(u'<b><font color=green>Обновляем</font></b> `%s`, ОГРН `%s`, код `%s`.' % (name, OGRN, regionalCode))
            self.nUpdated += 1
        else:
            orgId = self.addOrg(name, name, '', '',  '', '', OGRN, '03000',
                '', '', '', '', None, None, None, regionalCode, federalCode, isActive, area='23'.ljust(13,'0'), isInsurer=True)
            self.log(u'<b><font color=blue>Добавляем</font></b> `%s`, ОГРН `%s`, код `%s`.' % (name, OGRN, regionalCode))
            self.nAdded += 1

        self.orgMap[regionalCode] = orgId

# *****************************************************************************************

    def processInsurer(self, row):
        regionalCode = forceString(row['CODE'])
        name = forceString(row['NAME'])
        OGRN = forceString(row['OGRN'])

        if not OGRN:
            self.nSkipped += 1
            self.log(u'<b><font color=red>Пропуск</font></b> `%s` отсутствует ОГРН.' % name)
            return

        orgId = self.findOrgByOGRNandRegionalCode(OGRN, regionalCode)
        headId = self.findHeadOrgByOGRN(OGRN)

        if headId == orgId:
            headId = None

        if orgId:
            self.updateInsurer(orgId, name, OGRN, regionalCode)
            self.log(u'<b><font color=green>Обновляем</font></b> `%s`, ОГРН `%s`, код `%s`.' % (name, OGRN, regionalCode))
            self.nUpdated += 1
        else:
            orgId = self.addInsurer(name, OGRN, regionalCode, headId)
            self.log(u'<b><font color=blue>Добавляем</font></b> `%s`, ОГРН `%s`, код `%s`.' % (name, OGRN, regionalCode))
            self.nAdded += 1
            if not headId:
                self.log(u'<b><font color=orange>Внимание</font></b> '\
                    u'Не найдена головная организация.')

        self.insurerCache[regionalCode] = orgId


    def addInsurer(self, name, OGRN, regionalCode, masterId=None):
        table = QtGui.qApp.db.table('Organisation')
        record = table.newRecord()
        record.setValue('fullName', toVariant(name))
        record.setValue('shortName', toVariant(name))
        record.setValue('title', toVariant(name))
        record.setValue('infisCode', toVariant(regionalCode))
        record.setValue('isInsurer', toVariant(1))
        record.setValue('OGRN', toVariant(OGRN))
        record.setValue('area', '23'.ljust(13,'0'))

        if masterId:
            record.setValue('head_id', toVariant(masterId))

        orgId = QtGui.qApp.db.insertRecord(table, record)
        return orgId


    def updateInsurer(self, orgId, name, OGRN, regionalCode):
        table = QtGui.qApp.db.table('Organisation')
        record = QtGui.qApp.db.getRecord(table, '*', orgId)
        record.setValue('fullName', toVariant(name))
        record.setValue('shortName', toVariant(name))
        record.setValue('title', toVariant(name))
        record.setValue('infisCode', toVariant(regionalCode))
        record.setValue('isInsurer', toVariant(1))
        record.setValue('OGRN', toVariant(OGRN))
        record.setValue('area', '23'.ljust(13,'0'))
        QtGui.qApp.db.updateRecord(table, record)

# *****************************************************************************************

    def processAlienInsurer(self, row):
        name = forceString(row['NAM_SMOP'])
        shortName = forceString(row['NAM_SMOK'])

        if not shortName:
            shortName = name

        if name != '':
            #orgId = self.findOrgByName(name)

            OGRN = forceString(row['OGRN'])
            OKPO = '' # forceString(row['Q_OKPO'])
            OKATO = forceString(row['TF_OKATO'])
            smoCode = forceString(row['SMOCOD'])
            if smoCode:
                orgId = self.findBySmoCode(smoCode)
            if not orgId:
                self.log(u'Не найдено по SMOCOD, ищем по имени.')
                orgId = self.findOrgByName(name)

            #region = nameCase(forceString(row['NAME_TQ']))
            address = (forceString(row['INDEX_J'])+' '+forceString(row['ADDR_J'])).strip()
    #        isHead = forceInt(row['Q_ORG']) == 1
            postAddress = (forceString(row['INDEX_F'])+' '+forceString(row['ADDR_F'])).strip()
            chief = formatName(forceString(row['FAM_RUK']), forceString(row['IM_RUK']),
                                            forceString(row['OT_RUK']))
            #accountant = formatName(forceString(row['FAM_BUX']), forceString(row['IM_BUX']),
            #                                forceString(row['OT_BUX']))
            phone = forceString(row['PHONE'])
            fax = forceString(row['FAX'])
            email = forceString(row['E_MAIL'])
            INN = forceString(row['INN'])
            KPP = forceString(row['KPP'])
            #OKPO = forceString(row['Q_OKPO'])
            #OKVED = forceString(row['Q_OKVED'])
            isHead = forceInt(row['ORG']) in (1, 0)
            headId = None if isHead else self.findHeadOrgByOGRN(OGRN)

            if headId == orgId:
                headId = None

            area = self. getAreaCodeByOKATO(OKATO)

            if area[:2] == '23':
                self.log(u'<b><font color=green>Пропуск</font></b> Не иногородняя организация `%s`, ОГРН `%s`.' % (name, OGRN))
                self.nSkipped += 1
                return

            if address == '':
                address = postAddress

#            if not orgId and INN != '' and KPP != '':
#                orgId = self.findOrgId(INN, KPP)

            if orgId:
                self.updateAlienInsurer(orgId, name, shortName,  INN,  KPP,  OGRN, chief,
                                 address,    phone,  fax,  email,smoCode, headId, area, OKATO)
                self.log(u'<b><font color=green>Обновляем</font></b> `%s`, ОГРН `%s`.' % (name, OGRN))
                self.nUpdated += 1
            else:
                orgId = self.addAlienInsurer(name, shortName,  INN,  KPP,   OGRN, chief,
                                     address,  phone,  fax,  email,smoCode, headId,  area, OKATO)
                self.log(u'<b><font color=blue>Добавляем</font></b> `%s`, ОГРН `%s`.' % (name, OGRN))
                self.nAdded += 1

# *****************************************************************************************

    def processMedicalAidUnit(self, row):
        regionalCode = forceString(row['CODE'].strip())
        name = forceString(row['NAME'].strip())

        id = self.findMedicalAidUnit(name)

        if id:
            self.updateMedicalAidUnit(id, name, regionalCode)
            self.log(u'<b><font color=green>Обновляем</font></b> `%s`, код `%s`.' % (name, regionalCode))
            self.nUpdated += 1
        else:
            self.addMedicalAidUnit(name, regionalCode)
            self.log(u'<b><font color=blue>Добавляем</font></b> `%s`, код `%s`.' % (name, regionalCode))
            self.nAdded += 1

# *****************************************************************************************

    def findMedicalAidUnit(self, name):
        return forceRef(QtGui.qApp.db.translate('rbMedicalAidUnit', 'name', name, 'id'))


    def updateMedicalAidUnit(self, id, name, regionalCode):
        table = QtGui.qApp.db.table('rbMedicalAidUnit')
        record = QtGui.qApp.db.getRecord(table, '*', id)
        record.setValue('name', toVariant(name))
        record.setValue('descr', toVariant(name))
        record.setValue('regionalCode', toVariant(regionalCode))
        QtGui.qApp.db.updateRecord(table, record)


    def addMedicalAidUnit(self, name, regionalCode):
        table = QtGui.qApp.db.table('rbMedicalAidUnit')
        record = table.newRecord()
        record.setValue('code', toVariant(regionalCode))
        record.setValue('name', toVariant(name))
        record.setValue('descr', toVariant(name))
        record.setValue('regionalCode', toVariant(regionalCode))
        return QtGui.qApp.db.insertRecord(table, record)


# *****************************************************************************************
    kladrCache= {}

    def getAreaCodeByOKATO(self, OKATO):
        result = self.kladrCache.get(OKATO, -1)

        if result == -1:
            result = ''
            table = QtGui.qApp.db.table('kladr.KLADR')
            record = QtGui.qApp.db.getRecordEx(table, 'CODE', table['OCATD'].like(OKATO+'...'))

            if record:
                result  = forceString(record.value(0))

            if result:
                result = result[:11].ljust(13,'0')

            self.kladrCache[OKATO] = result

        return result

# *****************************************************************************************

    def addAlienInsurer(self, name, shortName,  INN,  KPP, OGRN, chief,
                                    address,  phone,  fax,  email,smoCode, masterId=None, area=None, OKATO=None):
        table = QtGui.qApp.db.table('Organisation')
        record = table.newRecord()
        record.setValue('fullName', toVariant(name))
        record.setValue('shortName', toVariant(shortName))
        record.setValue('INN',  toVariant(INN))
        record.setValue('KPP',  toVariant(KPP))
        record.setValue('OGRN', toVariant(OGRN))
        record.setValue('chiefFreeInput', toVariant(chief))
        #record.setValue('address',  toVariant(address))
        record.setValue('phone', toVariant(phone))

        record.setValue('title', toVariant(name))
        record.setValue('isInsurer', toVariant(1))
        record.setValue('smoCode', toVariant(smoCode))
        notes = u''

        if fax != '':
            notes += u'факс: %s' % fax

        if email != '':
            notes += u' email: %s' % email

        if notes != '':
            record.setValue('notes', toVariant(notes))

        if masterId:
            record.setValue('head_id', toVariant(masterId))

        if area:
            record.setValue('area', toVariant(area))

        if OKATO:
            record.setValue('OKATO', toVariant(OKATO))

        orgId = QtGui.qApp.db.insertRecord(table, record)
        return orgId


    def updateAlienInsurer(self, orgId,  name, shortName,  INN,  KPP, OGRN, chief,
                                      address,  phone,  fax,  email,smoCode, masterId=None,  area=None, OKATO=None):
        table = QtGui.qApp.db.table('Organisation')
        record = QtGui.qApp.db.getRecord(table, '*', orgId)
        record.setValue('fullName', toVariant(name))
        record.setValue('shortName', toVariant(shortName))
        record.setValue('INN',  toVariant(INN))
        record.setValue('KPP',  toVariant(KPP))
        record.setValue('OGRN', toVariant(OGRN))
        record.setValue('chiefFreeInput', toVariant(chief))
        #record.setValue('address',  toVariant(address))
        record.setValue('phone', toVariant(phone))

        record.setValue('title', toVariant(name))
        record.setValue('isInsurer', toVariant(1))
        record.setValue('smoCode', toVariant(smoCode))
        notes = u''

        if fax != '':
            notes += u'факс: %s' % fax

        if email != '':
            notes += u' email: %s' % email

        if notes != '':
            record.setValue('notes', toVariant(notes))

        if area:
            record.setValue('area', toVariant(area))

        if masterId:
            record.setValue('head_id', toVariant(masterId))

        if OKATO:
            record.setValue('OKATO', toVariant(OKATO))

        QtGui.qApp.db.updateRecord(table, record)

# *****************************************************************************************

    def updateKLADRInfisCode(self,  KLADRCode,  infisCode):
        table = QtGui.qApp.db.table('kladr.KLADR')
        table.setIdFieldName('CODE')
        record = QtGui.qApp.db.getRecordEx(table, 'CODE, infis',
            [table['CODE'].eq(KLADRCode),], 'CODE')
        record.setValue('infis', toVariant(infisCode))
        QtGui.qApp.db.updateRecord(table, record)

# *****************************************************************************************

    def findClientByNPP(self, npp):
        table = QtGui.qApp.db.table('ClientIdentification')
        record = QtGui.qApp.db.getRecordEx(table, 'client_id', [table['deleted'].eq(0),
                                                          table['accountingSystem_id'].eq(self.accountingSystemId),
                                                          table['identifier'].eq(npp)
                                                         ], 'id')
        if record:
            return forceRef(record.value(0))
        else:
            return None

# *****************************************************************************************

    def findClientByNameSexAndBirthDate(self, lastName, firstName, patrName, sex, birthDate):
        table = QtGui.qApp.db.table('Client')
        record = QtGui.qApp.db.getRecordEx(table, 'id',  [table['deleted'].eq(0),
                                                          table['lastName'].eq(nameCase(lastName)),
                                                          table['firstName'].eq(nameCase(firstName)),
                                                          table['patrName'].eq(nameCase(patrName)),
                                                          table['sex'].eq(sex),
                                                          table['birthDate'].eq(birthDate)
                                                         ], 'id')
        if record:
            return forceRef(record.value(0))
        else:
            return None

# *****************************************************************************************

    def findServiceByCodeAndName(self, code, name):
        table = QtGui.qApp.db.table('rbService')
        record = QtGui.qApp.db.getRecordEx(table, 'id', [table['code'].eq(code),
                                                         table['name'].eq(name),
                                                         ], 'id')
        if record:
            return forceRef(record.value(0))
        else:
            return None


    def findServiceByCodeAndNameEx(self, code, name):
        db = QtGui.qApp.db
        table = db.table('rbService')
        record = db.getRecordEx(table, ['id', 'name'], [table['code'].eq(code)], 'id desc')
        if record:
            oldName = forceString(record.value('name'))
            tmpName = oldName.lower()
            newName = name.lower()
            id = forceRef(record.value('id'))
            for ch in '/.,+-*)( ':
                newName = newName.replace(ch, '')
                tmpName = tmpName.replace(ch, '')
            if newName == tmpName:
                return id
            else:
                self.log(u'Найдена услуга с совпадающим кодом "%s", но с отличающимся наименованием \n старое "%s" \n новое "%s" \n будет добавлена новая услуга' % \
                         (code, oldName, name))
                return None
        else:
            return None
# *****************************************************************************************

    def findSpecialityByName(self, name):
        key = (name)
        result = self.mapSpecialityCodeNameToId.get(key)

        if not result:
            table = QtGui.qApp.db.table('rbSpeciality')
            record = QtGui.qApp.db.getRecordEx(table, 'id',  [
                                                        table['name'].eq(name),
                                                         ], 'id')
            if record:
                result = forceRef(record.value(0))
                self.mapSpecialityCodeNameToId[key] = result

        return result

# *****************************************************************************************

    def findActionTypeByCodeAndName(self, code,  name):
        key = (code,  name)
        result = self.mapActionTypeCodeNameToId.get(key)

        if not result:
            table = QtGui.qApp.db.table('ActionType')
            record = QtGui.qApp.db.getRecordEx(table, 'id, class',  [table['deleted'].eq(0),
                                                        table['code'].eq(code),
                                                        table['name'].eq(name),
                                                        #table['class'].eq('3'),
                                                         ], 'id')
            if record:
                result = (forceRef(record.value(0)), forceInt(record.value(1)))
                self.mapActionTypeCodeNameToId[key] = result
                self.mapActionTypeCodeToId[code] = result
        if not result:
            result = (None, None)
        return result

# *****************************************************************************************

    def findActionTypeByCode(self, code):
        result = self.mapActionTypeCodeToId.get(code)

        if not result:
            table = QtGui.qApp.db.table('ActionType')
            record = QtGui.qApp.db.getRecordEx(table, 'id, class',  [table['deleted'].eq(0),
                                                        table['code'].eq(code),
                                                        #table['class'].eq('3'),
                                                         ], 'id')
            if record:
                result = (forceRef(record.value(0)), forceInt(record.value(1)))
                self.mapActionTypeCodeToId[code] = result
        if not result:
            result = (None, None)
        return result

# *****************************************************************************************

    def findClientBySNILS(self, SNILS):
        table = QtGui.qApp.db.table('Client')
        record = QtGui.qApp.db.getRecordEx(table, 'id',  [table['deleted'].eq(0),
                                                          table['SNILS'].eq(SNILS),
                                                         ], 'id')
        if record:
            return forceRef(record.value(0))
        else:
            return None

# *****************************************************************************************

    def addClient(self, lastName, firstName, patrName, birthDate, sex,  SNILS):
        table = QtGui.qApp.db.table('Client')
        record = table.newRecord()
        record.setValue('lastName',  toVariant(nameCase(lastName)))
        record.setValue('firstName', toVariant(nameCase(firstName)))
        record.setValue('patrName',  toVariant(nameCase(patrName)))
        record.setValue('birthDate', toVariant(birthDate))
        record.setValue('sex',       toVariant(sex))
        record.setValue('SNILS',     toVariant(SNILS))
        clientId = QtGui.qApp.db.insertRecord(table, record)
        return clientId

# *****************************************************************************************

    def updateClient(self, clientId, lastName, firstName, patrName, birthDate, sex,  SNILS):
        record = self.db.getRecord(self.tableClient, '*', clientId)
        isDirty = False

        if forceString(record.value('lastName')) != nameCase(lastName):
            record.setValue('lastName', toVariant(nameCase(lastName)))
            isDirty = True

        if forceString(record.value('firstName')) != nameCase(firstName):
            record.setValue('firstName', toVariant(nameCase(firstName)))
            isDirty = True

        if forceString(record.value('patrName')) != nameCase(patrName):
            record.setValue('patrName', toVariant(nameCase(patrName)))
            isDirty = True

        if forceDate(record.value('birthDate')) != birthDate:
            record.setValue('birthDate', toVariant(birthDate))
            isDirty = True

        if forceInt(record.value('sex')) != sex:
            record.setValue('sex', toVariant(sex))
            isDirty = True

        if forceString(record.value('SNILS')) != SNILS:
            record.setValue('SNILS', toVariant(SNILS))
            isDirty = True

        if isDirty:
            self.db.updateRecord(self.tableClient, record)

# *****************************************************************************************

    def addClientPolicy(self, clientId, insurerId, serial, number, begDate, endDate,  note):
        table = QtGui.qApp.db.table('ClientPolicy')
        record = table.newRecord()
        record.setValue('client_id', toVariant(clientId))
        record.setValue('insurer_id', toVariant(insurerId))
        record.setValue('policyType_id', toVariant(self.policyTypeId))
        record.setValue('serial', toVariant(serial))
        record.setValue('number', toVariant(number))
        record.setValue('begDate', toVariant(begDate))
        record.setValue('endDate', toVariant(endDate))
        record.setValue('note',  toVariant(note))
        QtGui.qApp.db.insertRecord(table, record)

# *****************************************************************************************

    def updateClientPolicy(self, clientId, insurerId, serial, number, begDate, endDate, note):
        u"""Возвращаем True, если данные импортируемого полиса актуальны, иначе False"""

        record = selectLatestRecord('ClientPolicy', clientId,
            '(`Tmp`.`policyType_id`=''%d'')' % self.policyTypeId)

        if record:
            if (forceDate(record.value('begDate')) != begDate or \
                forceDate(record.value('endDate')) != endDate)  and \
                (forceDate(record.value('begDate')) < begDate):
                    record.setValue('begDate', toVariant(begDate))
                    record.setValue('endDate', toVariant(endDate))

                    if insurerId and forceRef(record.value('insurer_id')) != insurerId:
                        record.setValue('insurer_id', toVariant(insurerId))

                    if forceString(record.value('serial')) != serial:
                        record.setValue('serial', toVariant(serial))

                    if forceString(record.value('number')) != number:
                        record.setValue('number', toVariant(number))

                    self.db.updateRecord('ClientPolicy', record)
            else:
                return False

            if forceString(record.value('note')) != note:
                record.setValue('note', toVariant(note))
                self.db.updateRecord('ClientPolicy', record)
        else:
            self.addClientPolicy(clientId, insurerId, serial, number, begDate, endDate, note)

        return True

# *****************************************************************************************

    def getOrganisationId(self, INN, KPP):
        if INN and KPP:
            table = QtGui.qApp.db.table('Organisation')
            record = QtGui.qApp.db.getRecordEx(table, 'id',[table['deleted'].eq(0),
                                                      table['INN'].eq(INN),
                                                      table['KPP'].eq(KPP)], 'id')
            if record:
                return forceRef(record.value(0))
            elif self.addDummyOrganisations:
                record = table.newRecord()
                name = u'ИНН: %s; КПП: %s' % (INN, KPP)
                record.setValue('fullName', toVariant(name))
                record.setValue('shortName', toVariant(name))
                record.setValue('INN', toVariant(INN))
                record.setValue('KPP', toVariant(KPP))
                return QtGui.qApp.db.insertRecord(table, record)
        return None

# *****************************************************************************************

    def processClient(self, row):
        SNILS = forceString(forceString(row['SNILS'])).strip().replace('-', '').replace(' ', '')
        lastName  = nameCase(forceString(row['FAM']))
        firstName = nameCase(forceString(row['IM']))
        patrName  = nameCase(forceString(row['OTCH']))
        sex = self.sexMap.get(forceString(row['POL']), 0)
        birthDate = QDate(row['DATR']) if row['DATR'] else QDate()

        policySerial = forceString(row['POLIS_S']).strip()
        policyNumber = forceString(row['POLIS_N']).strip()
        policyInsurer = self.insurerCache.get(forceString(row['SMO']))
        policyBegDate = QDate(row['DATN']) if row['DATN'] else None
        policyEndDate = QDate(row['DATK']) if row['DATK'] else None

        workINN = forceString(row['INNRAB'])
        workKPP = forceString(row['KPPRAB'])
        workName = forceString(row['MRAB'])
        workOKVED = forceString(row['OKVED'])

        if not policyInsurer:
            self.log(u'<b><font color=orange>ВНИМАНИЕ</b>:'
                    u'Определить СМО для клиента "%s %s %s" невозможно. '
                    u'Неизвестная региональный код СМО: "%s".' %\
                    (lastName, firstName, patrName,  forceString(row['SMO'])),  True)

        clientId = self.findClientByNameSexAndBirthDate(lastName, firstName, patrName, sex, birthDate)

        if not clientId and SNILS:
            clientId = self.findClientBySNILS(SNILS)

        if clientId:
            if self.updateClientPolicy(clientId, policyInsurer, policySerial, policyNumber, policyBegDate, policyEndDate, None):
                self.updateClient(clientId, lastName, firstName, patrName, birthDate, sex, SNILS)
                self.updateClientWork(clientId, workINN,  workKPP, workName,  workOKVED)
        else:
            clientId = self.addClient(lastName, firstName, patrName, birthDate, sex, SNILS)
            self.addClientPolicy(clientId, policyInsurer, policySerial, policyNumber, policyBegDate, policyEndDate, None)
            self.addClientWork(clientId, workINN, workKPP, workName, workOKVED)

# *****************************************************************************************


    def findOrgId(self, INN, KPP):
        key = (INN,  KPP)
        orgId = self.orgCache.get(key)

        if not orgId:
            record = self.db.getRecordEx(self.tableOrganisation, 'id',
                                                        [self.tableOrganisation['deleted'].eq(0),
                                                          self.tableOrganisation['INN'].eq(INN),
                                                          self.tableOrganisation['KPP'].eq(KPP)
                                                         ], 'id')
            if record:
                orgId = forceRef(record.value(0))
                self.orgCache[key] = orgId

        return orgId

# *****************************************************************************************

    def findOrgByName(self, fullName):
        table = QtGui.qApp.db.table('Organisation')
        record = QtGui.qApp.db.getRecordEx(table, 'id',  [table['deleted'].eq(0),
                                                          table['fullName'].eq(fullName)], 'id')
        if record:
            return forceRef(record.value(0))
        else:
            return None

# *****************************************************************************************

    def findOrgByOGRN(self, OGRN):
        table = QtGui.qApp.db.table('Organisation')
        record = QtGui.qApp.db.getRecordEx(table, 'id',  [table['deleted'].eq(0),
                                                          table['OGRN'].eq(OGRN)], 'id')
        if record:
            return forceRef(record.value(0))
        else:
            return None

# *****************************************************************************************

    def findBySmoCode(self, smoCode):
        table = QtGui.qApp.db.table('Organisation')
        record = QtGui.qApp.db.getRecordEx(table, 'id',  [table['deleted'].eq(0),
                                                          table['smoCode'].eq(smoCode),
                                                          'Organisation.area NOT LIKE "23%"'], 'id')
        if record:
            return forceRef(record.value(0))
        else:
            return None

# *****************************************************************************************

    def findOrgByOGRNandRegionalCode(self, OGRN, regionalCode):
        table = QtGui.qApp.db.table('Organisation')
        record = QtGui.qApp.db.getRecordEx(table, 'id',  [table['deleted'].eq(0),
                                                          table['OGRN'].eq(OGRN),
                                                          table['infisCode'].eq(regionalCode)], 'id')
        if record:
            return forceRef(record.value(0))
        else:
            return None
# *****************************************************************************************
    def findOrgByOGRNandFederalCode(self, OGRN, federalCode):
        table = QtGui.qApp.db.table('Organisation')
        record = QtGui.qApp.db.getRecordEx(table, 'id', [table['deleted'].eq(0),
                                                         table['OGRN'].eq(OGRN),
                                                         table['smoCode'].eq(federalCode)], 'id')
        if record:
            return forceRef(record.value(0))
        else:
            return None

# *****************************************************************************************

    def findHeadOrgByOGRN(self, OGRN):
        table = QtGui.qApp.db.table('Organisation')
        record = QtGui.qApp.db.getRecordEx(table, 'id',  [table['deleted'].eq(0),
                                                          table['OGRN'].eq(OGRN),
                                                          table['head_id'].isNull()], 'id')
        if record:
            return forceRef(record.value(0))
        else:
            return None

# *****************************************************************************************

    def findChildOrgByOGRN(self, orgId, OGRN, name):
        table = QtGui.qApp.db.table('Organisation')
        record = QtGui.qApp.db.getRecordEx(table, 'id',  [table['deleted'].eq(0),
                                                          table['OGRN'].eq(OGRN),
                                                          table['head_id'].eq(orgId),
                                                          table['fullName'].eq(name)], 'id')
        if record:
            return forceRef(record.value(0))
        else:
            return None

# *****************************************************************************************

    def addOrg(self, shortName, fullName, INN, KPP, OKPO, OKVED, OGRN, OKATO,
                        address, chief, accountant, phone, fax, email, masterId,
                        infisCode, federalCode=None, isActive=True, notes=None, area=None, netId=None, isInsurer=False,
                        setIsMedical=True):
        table = QtGui.qApp.db.table('Organisation')
        record = table.newRecord()
        record.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
        record.setValue('createDatetime', toVariant(QDateTime().currentDateTime()))
        record.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
        record.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
        record.setValue('fullName', toVariant(fullName))
        record.setValue('shortName', toVariant(shortName))
        record.setValue('title', toVariant(shortName))
        record.setValue('OKPO', toVariant(OKPO))
        record.setValue('OKVED', toVariant(OKVED))
        record.setValue('INN', toVariant(INN))
        record.setValue('KPP', toVariant(KPP))
        record.setValue('OGRN', toVariant(OGRN))
        record.setValue('OKATO', toVariant(OKATO))
        record.setValue('address', toVariant(address))
        record.setValue('chiefFreeInput', toVariant(chief))
        record.setValue('accountant', toVariant(accountant))
        record.setValue('phone', toVariant(phone))
        record.setValue('smoCode', toVariant(federalCode))
        record.setValue('isActive', toVariant(isActive))

        if not notes:
            notes = u''

        if fax:
            notes += u'факс: %s' % fax

        if email:
            notes += u' email: %s' % email

        if notes != '':
            record.setValue('notes', toVariant(notes))

        if masterId:
            record.setValue('head_id',  toVariant(masterId))

        if area:
            record.setValue('area',  area)

        record.setValue('infisCode',  toVariant(infisCode))

        if netId:
            record.setValue('net_id', netId)

        if isInsurer:
            record.setValue('isInsurer', toVariant(1))

        if setIsMedical:
            record.setValue('isMedical', toVariant(3))

        return QtGui.qApp.db.insertRecord(table, record)

# *****************************************************************************************

    def updateOrg(self, orgId, shortName, fullName, OKPO, OKVED, OGRN, OKATO,
                            address, chief, accountant, phone, fax, email, masterId,
                            infisCode, federalCode=None, isActive=True, notes=None, area=None, netId=None, isInsurer=False,
                            setIsMedical=True):
        table = QtGui.qApp.db.table('Organisation')
        record = QtGui.qApp.db.getRecord(table, '*', orgId)
        record.setValue('fullName', toVariant(fullName))
        record.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
        record.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
        record.setValue('shortName', toVariant(shortName))
        record.setValue('title', toVariant(shortName))
        record.setValue('OKPO', toVariant(OKPO))
        record.setValue('OKVED', toVariant(OKVED))
        record.setValue('OGRN', toVariant(OGRN))
        record.setValue('OKATO', toVariant(OKATO))
        record.setValue('chiefFreeInput', toVariant(chief))
        record.setValue('accountant', toVariant(accountant))
        record.setValue('phone', toVariant(phone))
        record.setValue('smoCode', toVariant(federalCode))
        record.setValue('isActive', toVariant(isActive))

        if not notes:
            notes = u''

        if fax:
            notes += u'факс: %s' % fax

        if email:
            notes += u' email: %s' % email

        if notes != '':
            record.setValue('notes', toVariant(notes))

        if masterId:
            record.setValue('head_id', toVariant(masterId))

        if area:
            record.setValue('area', area)

        if netId:
            record.setValue('net_id', netId)

        if isInsurer:
            record.setValue('isInsurer', toVariant(1))

        if setIsMedical:
            record.setValue('isMedical', toVariant(3))

        record.setValue('infisCode',  toVariant(infisCode))
        return QtGui.qApp.db.updateRecord(table, record)

# *****************************************************************************************

    def addService(self, code,  name, infisCode, begDate, endDate, uet):
        table = QtGui.qApp.db.table('rbService')
        record = table.newRecord()
        record.setValue('code', toVariant(code))
        record.setValue('name', toVariant(name))

        if infisCode:
            record.setValue('infis', toVariant(infisCode))
            record.setValue('eisLegacy', toVariant(self.fillEIS))

        if self.isNomenclatureService(code):
            record.setValue('nomenclatureLegacy', toVariant(True))

        record.setValue('begDate',  toVariant(begDate))
        record.setValue('endDate',  toVariant(endDate))
        record.setValue('adultUetDoctor',  toVariant(uet))
        return QtGui.qApp.db.insertRecord(table, record)

# *****************************************************************************************

    def updateService(self, serviceId, infisCode, name, begDate, endDate, uet):
        table = QtGui.qApp.db.table('rbService')
        record = QtGui.qApp.db.getRecord(table, '*', serviceId)

        if infisCode:
            record.setValue('infis', toVariant(infisCode))
            if self.fillEIS:
                record.setValue('eisLegacy', toVariant(True))

        code = forceString(record.value('code'))
        if self.mustRecognizeNomenclature and self.isNomenclatureService(code):
            record.setValue('nomenclatureLegacy', toVariant(True))

        record.setValue('name', toVariant(name))
        record.setValue('begDate',  toVariant(begDate))
        record.setValue('endDate',  toVariant(endDate))
        record.setValue('adultUetDoctor',  toVariant(uet))
        return QtGui.qApp.db.updateRecord(table, record)

# *****************************************************************************************

    def ensureSpecialityRegionalCode(self, specialityId, regionalCode):
        table = QtGui.qApp.db.table('rbSpeciality')
        record = QtGui.qApp.db.getRecord(table, '*', specialityId)
        if forceString(record.value('regionalCode')) == '':
            record.setValue('regionalCode',  toVariant(regionalCode))
            return QtGui.qApp.db.updateRecord(table, record)

# *****************************************************************************************

    def addActionType(self, code,  name, groupId, class_id, serviceId, endDate):
        table = QtGui.qApp.db.table('ActionType')
        record = table.newRecord()
        record.setValue('code', toVariant(code))
        record.setValue('name', toVariant(name))
        record.setValue('title', toVariant(name))
        
        if class_id is not None:
            record.setValue('class', toVariant(class_id))
        else:
            record.setValue('class', toVariant(3))
            
        if groupId:
            record.setValue('group_id', toVariant(groupId))

        if serviceId:
            record.setValue('nomenclativeService_id',  toVariant(serviceId))
            
        showInForm = 0 if endDate <= QDate.currentDate() else 1
        record.setValue('showInForm',  toVariant(showInForm))
        
        #умолчания
        record.setValue('defaultStatus',  toVariant(2)) # состояние = закончено 
        record.setValue('defaultDirectionDate',  toVariant(1)) # дата назначения = дата начала события
        record.setValue('defaultPlannedEndDate',  toVariant(0)) # планируемая дата выполнения = не определено
        record.setValue('defaultBegDate',  toVariant(3)) # дата начала = дата окончания события
        record.setValue('defaultEndDate',  toVariant(3)) # дата окончания = дата окончания события
        record.setValue('defaultPersonInEvent',  toVariant(3)) # исполнитель = ответственный за событие
        record.setValue('defaultPersonInEditor',  toVariant(3)) # исполнитель в отд редакторе = ответственный за событие
        record.setValue('defaultMKB',  toVariant(5)) # МКБ и морфология по умолчанию = вводится непосредственно 

        return QtGui.qApp.db.insertRecord(table, record)

# *****************************************************************************************

    def updateActionType(self, id, serviceId, endDate):
        table = QtGui.qApp.db.table('ActionType')
        record = QtGui.qApp.db.getRecord(table, '*', id)

        if serviceId:
            record.setValue('nomenclativeService_id',  toVariant(serviceId))

        if endDate <= QDate.currentDate():
            record.setValue('showInForm',  toVariant(0))
            
        return QtGui.qApp.db.updateRecord(table, record)

# *****************************************************************************************

    def _addClientWork(self, clientId, organisationId):
        record = self.tableClientWork.newRecord()
        record.setValue('client_id', toVariant(clientId))
        record.setValue('org_id', toVariant(organisationId))
        self.db.insertRecord(self.tableClientWork, record)

# *****************************************************************************************

    def addClientWork(self, clientId, INN, KPP, name,  OKVED):
        if not (INN and KPP and name):
            return

        organisationId = self.findOrgId(INN, KPP)

        if not organisationId:
            organisationId = self.findOrgByName(name)

        if not organisationId:
            organisationId = self.addOrg(name, name, INN, KPP, '', OKVED, '', '', '', '', '', '', '', '', None, '', None)

        if organisationId:
            self._addClientWork(clientId, organisationId)

# *****************************************************************************************

    def updateClientWork(self, clientId, INN, KPP, name, OKVED):
        if not (INN and KPP and name):
            return

        organisationId = self.findOrgId(INN, KPP)

        if not organisationId:
            organisationId = self.findOrgByName(name)

        if not organisationId:
            organisationId = self.addOrg(name, name, INN, KPP, '', OKVED, '', '', '', '', '', '', '', '', None, '', None)

        if organisationId:
            record = QtGui.qApp.db.getRecordEx(self.tableClientWork, 'id',
                                                                [self.tableClientWork['deleted'].eq(0),
                                                                self.tableClientWork['client_id'].eq(clientId),
                                                                self.tableClientWork['org_id'].eq(organisationId)], 'id')
            if not record:
                self._addClientWork(clientId, organisationId)

    def printReport(self):
        report = CReportBase()
        params = report.getDefaultParams()
        report.saveDefaultParams(params)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Результаты импорта')
        cursor.insertBlock()
        cursor.insertHtml('<br/><br/>')
        cursor.insertText(self.logBrowser.toPlainText())
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertHtml('<br/><br/>')
        cursor.insertText(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        reportView = CReportViewDialog(self)
        reportView.setWindowTitle(u'Результаты импорта')
        reportView.setOrientation(QtGui.QPrinter.Portrait)
        reportView.setText(doc)
        reportView.exec_()
