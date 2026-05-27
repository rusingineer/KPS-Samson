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

from PyQt4 import QtGui
from PyQt4.QtCore import *

from library.dbfpy.dbf import *
from library.Utils     import *
from Registry.Utils import *

from Ui_importPrik import Ui_PrikImportDialog


def dbfFieldExists(dbf, fieldName):
    return (fieldName.upper() in dbf.header.mapNameToIndex)

    
def dbfRecordValue(record, fieldName):
    return record[fieldName] if dbfFieldExists(record.dbf, fieldName) else None


class CDBCache:
    def __init__(self, tableName, keyField):
        self.tableName = tableName
        self.keyField = keyField
        self.dict = {}
    
    def get(self, key):
        if not key:
            return None
        
        if key in self.dict:
            return self.dict[key]
        
        table = QtGui.qApp.db.table(self.tableName)

        record = QtGui.qApp.db.getRecordEx(table, '*', [table[self.keyField].eq(key)], 'id')
        
        self.dict[key] = record
        return record
        
    def getId(self, key):
        record = self.get(key)
        if record:
            return forceRef(record.value('id'))
        else:
            return None
            
    def getField(self, key, fieldName):
        record = self.get(key)
        if record:
            return record.value(fieldName)
        else:
            return QVariant()
            
organisation = CDBCache(tableName = 'Organisation', keyField = 'infisCode')
documentType = CDBCache(tableName = 'rbDocumentType', keyField = 'regionalCode')        


class CPrikImportDialog(QtGui.QDialog, Ui_PrikImportDialog):
    startPrepare = pyqtSignal()
    startWork = pyqtSignal()
    

    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.dbf = Dbf(forceString(parent.edtPrikFileName.text()), readOnly=True, encoding='cp866', enableFieldNameDups=True)
        self.tblDbfView.verticalHeader().setVisible(True)
        h = self.tblDbfView.fontMetrics().height()
        self.tblDbfView.verticalHeader().setDefaultSectionSize(3*h/2)
        self.startPrepare.connect(self.prepare, Qt.QueuedConnection)
        self.btnStart.setEnabled(False)
        self.working = False
        self.canceled = False
        self.preparing = False
        self.updatePolicy = parent.cbUpdate.isChecked()
        self.sexMap = {u'Ж':2, u'ж':2, u'М':1, u'м':1}
        self.policyKindCache = {u'П':3, u'Э':4, u'В':1, u'С':2}
        self.hideLog()
        self.mo_codes = []
        #Оперделяем старый формат по отсутствию поля F_ENP
        (dirName, fileName) = os.path.split(forceString(parent.edtPrikFileName.text()))        
        if not dbfFieldExists(self.dbf, 'F_ENP'):    
            self.old_format = True;
        else:
            self.old_format = False;
        query = QtGui.qApp.db.query('select infisCode from OrgStructure where length(infisCode) = 5 order by infisCode')
        while query.next():
            record = query.record()
            self.mo_codes.append(forceString(record.value('infisCode'))) 
        
        
    def showLog(self):
        self.txtLog.setVisible(True)
        self.btnShowLog.setArrowType(Qt.UpArrow)


    def hideLog(self):
        self.txtLog.setVisible(False)
        self.btnShowLog.setArrowType(Qt.DownArrow)
        
        
    def checkDbfFields(self):
        requiredFields = ['FAM', 'IM', 'OT', 'DATR', 'CODE_MO', 'MIACRES', 'PRIK_D', 
                          'SMO', 'DPFS', 'DPFS_S', 'DPFS_N', 
                          'DOC', 'DOC_S', 'DOC_N']
        if not self.old_format:
            requiredFields+= ['F_ENP', 'F_SMO', 'F_DPFS', 'F_DPFS_S', 'F_DPFS_N', 'F_FAM', 'F_IM', 'F_OT', 'F_SEX',
           'F_DATR', 'F_SNILS',  'F_DOC',  'F_DOC_S',  'F_DOC_N']
        errorFieldList = [field for field in requiredFields if not dbfFieldExists(self.dbf, field)]
        if len(errorFieldList) > 0:
            raise Exception(u'Не удалось запустить импорт; в выбранном файле не обнаружены необходимые поля: %s' % ', '.join(errorFieldList))


    def exec_(self):
        self.checkDbfFields()
        self.startPrepare.emit()
        
        return QtGui.QDialog.exec_(self)
        
        
    def prepare(self):
        self.preparing = True
        self.canceled = False
        recordList = self.updateMIACResAndFilterClients(self.dbf)
        self.model = CPrikImportModel(recordList, self.old_format, self)
        self.tblDbfView.setModel(self.model)
        self.chbSelectAll.setEnabled(True)
        self.chbSelectAll.stateChanged.connect(self.selectAllChecked)
        self.model.recordSelected.connect(self.recordSelected)
        self.startWork.connect(self.work, Qt.QueuedConnection)
        self.btnStart.setEnabled(True)
        self.preparing = False
        
    def selectAllChecked(self, state):
        if state == Qt.PartiallyChecked:
            self.chbSelectAll.setCheckState(Qt.Checked)
            return
        self.model.recordSelected.disconnect(self.recordSelected)
        self.model.selectAll(state == Qt.Checked)
        self.model.recordSelected.connect(self.recordSelected)

        
    def recordSelected(self, countAll, countSelected):
        self.chbSelectAll.stateChanged.disconnect(self.selectAllChecked)
        if countSelected == 0:
            self.chbSelectAll.setCheckState(Qt.Unchecked)
        elif countSelected == countAll:
            self.chbSelectAll.setCheckState(Qt.Checked)
        else:
            self.chbSelectAll.setCheckState(Qt.PartiallyChecked)
        self.chbSelectAll.stateChanged.connect(self.selectAllChecked)
        
    def progressShow(self, caption, maxCount):
        self.lblProgress.setVisible(True)
        self.lblProgress.setText(caption)
        self.prbProgress.setVisible(True)
        self.prbProgress.setMaximum(maxCount)
        self.prbProgress.setValue(0)
        self.lblElapsed.setVisible(True)
        self.lblElapsed.setText(u'Текущая операция: ??? зап/с, окончание в ??:??:??')
        self.time = QTime()
        self.time.start()
        self.startPos = 0
        self.oldSpeed = 0
        
        
    def progressStep(self):
        self.prbProgress.setValue(self.prbProgress.value() + 1)
                
        elapsed = self.time.elapsed()
        if elapsed != 0 and (self.prbProgress.value() - self.startPos > 100):
            self.startPos = self.prbProgress.value()
            self.oldSpeed = 100 * 1000 / elapsed
            newSpeed = (self.oldSpeed + 100 * 1000 / elapsed) / 2
            if newSpeed != 0:
                finishTime = QTime.currentTime().addSecs(self.prbProgress.maximum() / newSpeed)
                self.lblElapsed.setText(u'Текущая операция: %03.f зап/с, окончание в %s' % (newSpeed, finishTime.toString('hh:mm:ss')))
                self.time.restart()
                
        
    def progressHide(self):
        self.lblProgress.setVisible(False)
        self.prbProgress.setVisible(False)
        self.lblElapsed.setVisible(False)
        
    def getPolicyKindByRegionalCode(self, regionalCode):
        result = self.policyKindCache.get(regionalCode,  -1)

        if result == -1:
            result  = forceRef(QtGui.qApp.db.translate('rbPolicyKind', 'regionalCode', regionalCode,  'id'))
            self.policyKindCache[regionalCode] = result

        return result
        
    def updateMIACResAndFilterClients(self, dbf):
        self.progressShow(u'Поиск пациентов и обновление результатов сверки', dbf.recordCount)
        notFoundList = []
        countFound = 0
        countUpdated = 0
        
        QtGui.qApp.db.transaction()
        
        try:
            
            for dbfRecord in dbf:
                
                if self.canceled:
                    QtGui.qApp.db.rollback()
                    self.reject()
                    return
                    
                if dbfRecord['CODE_MO'] not in self.mo_codes:
                    self.progressStep()
                    QtGui.qApp.processEvents()
                    continue
                    
                if not self.old_format and (not dbfRecord['F_ENP']) :
                    self.progressStep()
                    QtGui.qApp.processEvents()
                    continue
                    
                clientRecord = self.findClient(dbfRecord)
                if clientRecord:
                    # обновление полисных и паспортных данных
                    updPolicy = False
                    updClient = False
                    if self.updatePolicy:
                        record = getClientPolicyEx(forceInt(clientRecord.value('id')), True,  None)
                        if self.old_format:
                            smo = dbfRecord['SMO']
                            insurerId = organisation.getId(smo)
                            dpfs = dbfRecord['DPFS']
                            policyKindId = self.getPolicyKindByRegionalCode(dpfs)
                            dpfsS = dbfRecord['DPFS_S']
                            dpfsN = dbfRecord['DPFS_N']
                            doc = dbfRecord['DOC']
                            documentTypeId = documentType.getId(doc)
                            docS = dbfRecord['DOC_S']
                            docN = dbfRecord['DOC_N']
                        else:                            
                            smo = dbfRecord['F_SMO']
                            insurerId = organisation.getId(smo)
                            dpfs = dbfRecord['F_DPFS']
                            policyKindId = self.getPolicyKindByRegionalCode(dpfs)
                            dpfsS = dbfRecord['F_DPFS_S']
                            dpfsN = dbfRecord['F_DPFS_N']
                            doc = dbfRecord['F_DOC']
                            documentTypeId = documentType.getId(doc)
                            docS = dbfRecord['F_DOC_S']
                            docN = dbfRecord['F_DOC_N']
                        dstop = dbfRecord['F_DSTOP']
                        if smo != '9007' and (insurerId  or dpfsS or dpfsN or dstop):
                            table = QtGui.qApp.db.table('ClientPolicy')
                            if record:
                                record.setValue('insurer_id',   toVariant(insurerId))
                                record.setValue('policyType_id', toVariant(1))
                                record.setValue('policyKind_id', toVariant(policyKindId))
                                record.setValue('serial',       toVariant(dpfsS))
                                record.setValue('number',       toVariant(dpfsN))
                                if dstop:
                                    record.setValue('endDate',       toVariant(dstop))
                                record.remove(record.indexOf('compulsoryServiceStop'))
                                record.remove(record.indexOf('voluntaryServiceStop'))
                                record.remove(record.indexOf('area'))
                                record.remove(record.indexOf('enp'))
                                QtGui.qApp.db.updateRecord(table, record)
                            else:
                                record = table.newRecord()
                                record.setValue('client_id',    clientRecord.value('id'))
                                record.setValue('insurer_id',   toVariant(insurerId))
                                record.setValue('policyType_id', toVariant(1))
                                record.setValue('policyKind_id', toVariant(policyKindId))
                                record.setValue('serial',       toVariant(dpfsS))
                                record.setValue('number',       toVariant(dpfsN))
                                if dstop:
                                    record.setValue('endDate',       toVariant(dstop))
                                QtGui.qApp.db.insertRecord(table, record)
                            updPolicy = True
                        record_doc = getClientDocument(forceInt(clientRecord.value('id')))        
                        if documentTypeId and (docS or docN):
                            table = QtGui.qApp.db.table('ClientDocument')
                            if record_doc:
                                record_doc.setValue('documentType_id', toVariant(documentTypeId))
                                record_doc.setValue('serial',         toVariant(docS))
                                record_doc.setValue('number',         toVariant(docN))
                                QtGui.qApp.db.updateRecord(table, record_doc)
                            else:                           
                                record = table.newRecord()
                                record.setValue('client_id',      clientRecord.value('id'))
                                record.setValue('documentType_id', toVariant(documentTypeId))
                                record.setValue('serial',         toVariant(docS))
                                record.setValue('number',         toVariant(docN))
                                QtGui.qApp.db.insertRecord(table, record)
                            updPolicy = True
                        if dbfRecord['F_DATS']:
                            clientRecord.setValue('deathDate',   toVariant(dbfRecord['F_DATS']))
                            updClient=True;
                            
                        if not self.old_format and dbfRecord['F_FAM']:
                            clientRecord.setValue('lastName',   toVariant(nameCase(dbfRecord['F_FAM'])))
                            clientRecord.setValue('firstName',   toVariant(nameCase(dbfRecord['F_IM'])))
                            clientRecord.setValue('patrName',   toVariant(nameCase(dbfRecord['F_OT'])))
                            clientRecord.setValue('birthDate',   toVariant(dbfRecord['F_DATR']))                             
                            clientRecord.setValue('deathDate',   toVariant(dbfRecord['F_DATS']))                             
                            snils = forceString(dbfRecord['F_SNILS'])
                            snils = snils.replace('-', '')
                            snils = snils.replace(' ', '')
                            if snils and snils != clientRecord.value('snils'):
                                clientRecord.setValue('SNILS',   toVariant(snils))                                 
                                updClient=True;
                            if self.sexMap.get(forceString(dbfRecord['F_SEX']))!=clientRecord.value('sex'):  
                                clientRecord.setValue('sex', toVariant(self.sexMap.get(forceString(dbfRecord['F_SEX']))))
                                updClient=True;
                        if updClient:
                            QtGui.qApp.db.updateRecord('Client', clientRecord)
                        
                    countFound += 1
                    if self.old_format:
                        miacRes = dbfRecord['MIACRES']
                        if clientRecord.value('miacRes') != miacRes:
                            clientRecord.setValue('miacRes', toVariant(miacRes))
                            QtGui.qApp.db.updateRecord('Client', clientRecord)
                            countUpdated += 1
                        elif updPolicy:
                            countUpdated += 1
                    else:
                        miacRes = dbfRecord['MIACRES']
                        tfomsRes = dbfRecord['TFOMSRES']
                        f_comm = dbfRecord['F_COMM']
                        f_enp = dbfRecord['F_ENP']
                        m_comm = dbfRecord['M_COMM']
                        
                        if clientRecord.value('miacRes') != miacRes \
                            or clientRecord.value('tfomsRes') != tfomsRes \
                            or clientRecord.value('f_comm') != f_comm \
                            or clientRecord.value('m_comm') != m_comm \
                            or clientRecord.value('f_enp') != f_enp:
                                
                            clientRecord.setValue('tfomsRes', toVariant(tfomsRes))
                            clientRecord.setValue('f_comm', toVariant(f_comm))
                            clientRecord.setValue('miacRes', toVariant(miacRes))
                            clientRecord.setValue('m_comm', toVariant(m_comm))
                            clientRecord.setValue('f_enp',   toVariant(f_enp)) 
                            QtGui.qApp.db.updateRecord('Client', clientRecord)
                            countUpdated += 1
                        elif updClient:
                            countUpdated += 1
                else:
                    notFoundList.append(dbfRecord)
                self.progressStep()
                QtGui.qApp.processEvents()
            QtGui.qApp.db.commit()
        except Exception as e:
            QtGui.qApp.db.rollback()            
            self.logError(unicode(e) or repr(e))
            self.showLog()
            
        countAll = dbf.recordCount
        countAllText = agreeNumberAndWord(countAll, (u"Обработана %d запись", u"Обработано %d записи", u"Обработано %d записей")) % countAll
        countFoundText = agreeNumberAndWord(countFound, (u'%d пациент найден', u'%d пациента найдено', u'%d пациентов найдено')) % countFound
        countUpdatedText = agreeNumberAndWord(countUpdated, (u'%d результат сверки обновлен', u'%d результата сверки обновлено', u'%d результатов сверки обновлено')) % countUpdated
        self.logInfo(u'%s: %s, %s' % (countAllText, countFoundText, countUpdatedText))
            
        self.progressHide()
        
        if countAll == countFound:
            self.btnStart.setEnabled(False)
            self.btnCancel.setText(u'Закрыть')
            self.showLog()
        
        return notFoundList
        
        
    def logInfo(self, text):
        if isinstance(text, basestring):
            self.txtLog.append(text)
        else:
            for str in text:
                self.txtLog.append(str)
        self.txtLog.append('')
        
        
    def logError(self, text):
        if isinstance(text, basestring):
            self.txtLog.append(u'<b><font color=red>Ошибка:</font></b> %s' % text)
        else:
            self.txtLog.append(u'<b><font color=red>Ошибка:</font></b> %s' % text[0])
            for str in text[1:]:
                self.txtLog.append(str)
        self.txtLog.append('')


    def work(self):
        QtGui.qApp.db.transaction()
        self.workStart()
        
        try:
            countAll = 0
            countAdded = 0
            countErrors = 0
            for checked, dbfRecord in self.model.recordList:
                if checked:
                    countAll += 1
                    success, errors = self.addClient(dbfRecord)
                    if success:
                        countAdded += 1
                    else:
                        countErrors += 1
                        clientName = ' '.join([part for part in [dbfRecord['FAM'], dbfRecord['IM'], dbfRecord['OT']] if part])
                        errors = [u'не удалось добавить пациента %s:\n' % clientName] + ['- ' + error for error in errors]
                        self.logError(errors)
                self.progressStep()
                QtGui.qApp.processEvents()
                if self.canceled:
                    QtGui.qApp.db.rollback()
                    self.workCancel()
                    return
            QtGui.qApp.db.commit()
            self.workDone()
            
            countAllText = agreeNumberAndWord(countAll, (u"обработана %d запись", u"обработано %d записи", u"обработано %d записей")) % countAll
            countAddedText = agreeNumberAndWord(countAdded, (u'добавлен %d пациент', u'добавлено %d пациента', u'добавлено %d пациентов')) % countAdded
            countErrorsText = agreeNumberAndWord(countErrors, (u'%d ошибка', u'%d ошибки', u'%d ошибок')) % countErrors
            self.logInfo(u'Импорт завершен: %s, %s, %s' % (countAllText, countAddedText, countErrorsText))
        except Exception as e:
            self.logError(unicode(e) or repr(e))
            QtGui.qApp.db.rollback()
            self.workCancel()
            self.showLog()
        
    def workStart(self):
        self.working = True
        self.progressShow(u'Добавление пациентов из списка', self.model.selectedCount)
        self.btnStart.setEnabled(False)
        self.btnCancel.setText(u'Остановить')
            
            
    def workDone(self):
        self.working = False
        self.progressHide()
        self.btnCancel.setText(u'Закрыть')
        self.showLog()
        
        
    def workCancel(self):
        self.working = False
        self.progressHide()
        self.btnStart.setEnabled(True)
        self.btnCancel.setText(u'Отмена')
        
        
    def addClient(self, dbfRecord):
        errors = []
        if self.old_format:
            fam = dbfRecord['FAM']
            im = dbfRecord['IM']
            ot = dbfRecord['OT']
            datr = dbfRecord['DATR']
            sex = dbfRecord['SEX']
        else:
            fam = dbfRecord['F_FAM']
            im = dbfRecord['F_IM']
            ot = dbfRecord['F_OT']
            datr = dbfRecord['F_DATR']
            sex = dbfRecord['F_SEX']
            
        if not fam:
            errors.append(u'пустое поле "фамилия"')
        if not im:
            errors.append(u'пустое поле "имя"')
        if not datr:
            errors.append(u'пустое поле "дата рождения"')
            
        codeMO = dbfRecord['CODE_MO']
        if not codeMO:
            errors.append(u'пустое поле "ЛПУ"')
        else:
            lpuId = organisation.getId(codeMO)
            if not lpuId:
                errors.append(u'ЛПУ с кодом %s не найдено в справочнике организаций' % codeMO)
                
        prikD = dbfRecord['PRIK_D']
        if not prikD:
            prikD = QDate()
                            
        if len(errors) > 0:
            return (False, errors)
        
        miacres = dbfRecord['MIACRES']
        
        table = QtGui.qApp.db.table('Client')
        record = table.newRecord()
        record.setValue('lastName',  toVariant(nameCase(fam)))
        record.setValue('firstName', toVariant(nameCase(im)))
        record.setValue('patrName',  toVariant(nameCase(ot)))
        record.setValue('birthDate', toVariant(datr))
        record.setValue('sex', toVariant(self.sexMap.get(forceString(sex))))
        record.setValue('miacRes',   toVariant(miacres))
        snils = forceString(dbfRecord['SNILS'])
        snils = snils.replace('-', '')
        snils = snils.replace(' ', '')
        record.setValue('SNILS',   toVariant(snils))
        
        if not self.old_format:
            record.setValue('deathDate',   toVariant(dbfRecord['F_DATS']))
            record.setValue('m_comm',   toVariant(dbfRecord['M_COMM']))
            record.setValue('tfomsRes',   toVariant(dbfRecord['TFOMSRES']))
            record.setValue('f_comm',   toVariant(dbfRecord['F_COMM']))
            record.setValue('f_enp',   toVariant(dbfRecord['F_ENP']))
            snils = forceString(dbfRecord['F_SNILS'])
            snils = snils.replace('-', '')
            snils = snils.replace(' ', '')
            record.setValue('SNILS',   toVariant(snils))
        clientId = QtGui.qApp.db.insertRecord(table, record)
        
        address = self.model.getAddress(dbfRecord)
        if address:
            table = QtGui.qApp.db.table('ClientAddress')
            record = table.newRecord()
            record.setValue('client_id', toVariant(clientId))
            record.setValue('type',      toVariant(0))
            record.setValue('freeInput', toVariant(address))
            QtGui.qApp.db.insertRecord(table, record)
        
        table = QtGui.qApp.db.table('ClientAttach')
        record = table.newRecord()
        record.setValue('client_id',     toVariant(clientId))
        record.setValue('attachType_id', toVariant(2))
        record.setValue('LPU_id',        toVariant(lpuId))
        record.setValue('begDate',       toVariant(prikD))
        QtGui.qApp.db.insertRecord(table, record)
        
        if self.old_format:
            smo = dbfRecord['SMO']
            insurerId = organisation.getId(smo)
            dpfs = dbfRecord['DPFS']
            policyKindId = self.getPolicyKindByRegionalCode(dpfs)
            dpfsS = dbfRecord['DPFS_S']
            dpfsN = dbfRecord['DPFS_N']
            doc = dbfRecord['DOC']
            documentTypeId = documentType.getId(doc)
            docS = dbfRecord['DOC_S']
            docN = dbfRecord['DOC_N']
        else:   
            smo = dbfRecord['F_SMO']
            insurerId = organisation.getId(smo)
            dpfs = dbfRecord['F_DPFS']
            policyKindId = self.getPolicyKindByRegionalCode(dpfs)
            dpfsS = dbfRecord['F_DPFS_S']
            dpfsN = dbfRecord['F_DPFS_N']
            doc = dbfRecord['F_DOC']
            documentTypeId = documentType.getId(doc)
            docS = dbfRecord['F_DOC_S']
            docN = dbfRecord['F_DOC_N']
            
        if insurerId or dpfsS or dpfsN:
            table = QtGui.qApp.db.table('ClientPolicy')
            record = table.newRecord()
            record.setValue('client_id',    toVariant(clientId))
            record.setValue('insurer_id',   toVariant(insurerId))
            record.setValue('policyType_id', toVariant(1))
            record.setValue('policyKind_id', toVariant(policyKindId))
            record.setValue('serial',       toVariant(dpfsS))
            record.setValue('number',       toVariant(dpfsN))
            record.setValue('begDate',       toVariant(QDate()))
            QtGui.qApp.db.insertRecord(table, record)
        
        if documentTypeId and (docS or docN):
            table = QtGui.qApp.db.table('ClientDocument')
            record = table.newRecord()
            record.setValue('client_id',      toVariant(clientId))
            record.setValue('documentType_id', toVariant(documentTypeId))
            record.setValue('serial',         toVariant(docS))
            record.setValue('number',         toVariant(docN))
            QtGui.qApp.db.insertRecord(table, record)
                
        return (True, [])


    def findClient(self, searchRecord):
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        fam = toVariant(nameCase(searchRecord['FAM']))
        im = toVariant(nameCase(searchRecord['IM']))
        datr = toVariant(searchRecord['DATR'])
        ot = nameCase(dbfRecordValue(searchRecord, 'OT'))
        
        condition = [tableClient['deleted'].eq(0),
                     tableClient['lastName'].eq(fam),
                     tableClient['firstName'].eq(im),
                     tableClient['birthDate'].eq(datr) 
                    ]
                    
        if ot:
            ot = toVariant(ot)
            condition.append(tableClient['patrName'].eq(ot))

        record = db.getRecordEx(tableClient, 'id, lastName, firstName, patrName, sex, birthDate, deathDate, SNILS, miacRes, m_comm, tfomsRes, f_comm, f_enp', condition, 'id')
        
        if not record and not self.old_format:
            fam = toVariant(nameCase(searchRecord['F_FAM']))
            im = toVariant(nameCase(searchRecord['F_IM']))
            datr = toVariant(searchRecord['F_DATR'])
            ot = nameCase(dbfRecordValue(searchRecord, 'F_OT'))
            
            condition = [tableClient['deleted'].eq(0),
                         tableClient['lastName'].eq(fam),
                         tableClient['firstName'].eq(im),
                         tableClient['birthDate'].eq(datr) 
                        ]
                        
            if ot:
                ot = toVariant(ot)
                condition.append(tableClient['patrName'].eq(ot))
            if fam:
                record = db.getRecordEx(tableClient, 'id, lastName, firstName, patrName, sex, birthDate, deathDate, SNILS, miacRes, m_comm, tfomsRes, f_comm, f_enp', condition, 'id')

        return record
        
        
    @pyqtSignature("")
    def on_btnStart_clicked(self):
        if not self.working:
            self.canceled = False
            self.startWork.emit()


    @pyqtSignature("")
    def on_btnCancel_clicked(self):
        if self.working or self.preparing:
            self.canceled = True
        else:
            self.reject()
            
            
    @pyqtSignature("")
    def on_btnShowLog_clicked(self):
        if self.txtLog.isVisible():
            self.hideLog()
        else:
            self.showLog()
            

alignLeft  = QVariant(Qt.AlignLeft|Qt.AlignVCenter)
alignRight = QVariant(Qt.AlignRight|Qt.AlignVCenter)

class CColumn:
    def __init__(self, caption, source, alignment=alignLeft):
        self.caption = caption
        self.source = source
        self.alignment = alignment
        

class CPrikImportModel(QAbstractTableModel):
    recordSelected = pyqtSignal(int, int)
    
    def __init__(self, recordList, old_format, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.recordList = [[True, record] for record in recordList]
        self.recordCount = len(recordList)
        self.selectedCount = len(recordList)
        self.old_format = old_format
        if self.old_format:
            self.columns = [
                CColumn(u'Фамилия',           'FAM'), 
                CColumn(u'Имя',               'IM'), 
                CColumn(u'Отчество',          'OT'), 
                CColumn(u'Дата рождения',     'DATR'), 
                CColumn(u'СНИЛС',     'SNILS'), 
                CColumn(u'Адрес',             self.getAddress), 
                CColumn(u'ЛПУ',               self.getLPU),
                CColumn(u'Дата прикрепления', 'PRIK_D'),
                CColumn(u'СМО',               self.getSMO), 
                CColumn(u'Тип полиса',        self.getPolicyKindName), 
                CColumn(u'Серия полиса',      'DPFS_S'), 
                CColumn(u'Номер полиса',      'DPFS_N'), 
                CColumn(u'Документ',          self.getDocumentType), 
                CColumn(u'Серия документа',   'DOC_S'), 
                CColumn(u'Номер документа',   'DOC_N')                
            ]            
        else:
            self.columns = [
                CColumn(u'Номер',             'F_ENP'), 
                CColumn(u'Фамилия',           'F_FAM'), 
                CColumn(u'Имя',               'F_IM'), 
                CColumn(u'Отчество',          'F_OT'), 
                CColumn(u'Дата рождения',     'F_DATR'), 
                CColumn(u'СНИЛС',     'F_SNILS'), 
                CColumn(u'Адрес',             self.getAddress), 
                CColumn(u'ЛПУ',               self.getLPU),
                CColumn(u'Дата прикрепления', 'PRIK_D'),
                CColumn(u'СМО',               self.getSMO), 
                CColumn(u'Тип полиса',        self.getPolicyKindName), 
                CColumn(u'Серия полиса',      'F_DPFS_S'), 
                CColumn(u'Номер полиса',      'F_DPFS_N'), 
                CColumn(u'Документ',          self.getDocumentType), 
                CColumn(u'Серия документа',   'F_DOC_S'), 
                CColumn(u'Номер документа',   'F_DOC_N')                
            ]
        self.orgDict = {}
        self.policyKind = {u'С': (2, toVariant(u'старый')), 
                           u'В': (1, toVariant(u'временный')), 
                           u'П': (3, toVariant(u'новый')), 
                           u'Э': (4, toVariant(u'электронный')), 
                           u'5': (5, toVariant(u'электронный (УЭК)'))}
                              
        
    def getLPU(self, record):
        return organisation.getField(record['CODE_MO'], 'title')

        
    def getSMO(self, record):
        if self.old_format:
            fieldName = 'SMO'
        else:
             fieldName = 'F_SMO'
        return organisation.getField(record[fieldName], 'title')
            
            
    def getDocumentType(self, record):
        if self.old_format:
            fieldName = 'DOC'
        else:
             fieldName = 'F_DOC'
        return documentType.getField(record[fieldName], 'name')
                    
        
    def getAddress(self, record):
        parts = [
            (u'р-н %s',   dbfRecordValue(record, 'R_NAME')), 
            (u'%s',       dbfRecordValue(record, 'C_NAME')), 
            (u'%s',       dbfRecordValue(record, 'NP_NAME')), 
            (u'%s',       dbfRecordValue(record, 'UL_NAME')), 
            (u'д. %s',    dbfRecordValue(record, 'DOM')), 
            (u'корп. %s', dbfRecordValue(record, 'KOR')), 
            (u'кв. %s',   dbfRecordValue(record, 'KV'))
        ]
        return ', '.join([template % str for template, str in parts if str])
        
        
    def getPolicyKindId(self, dpfs):
        if dpfs in self.policyKind:
            return self.policyKind[dpfs][0]
        else:
            return None
            
            
    def getPolicyKindName(self, record):
        if self.old_format:
            dpfs = record['DPFS']
        else:
             dpfs = record['F_DPFS']
        if dpfs and dpfs in self.policyKind:
            return self.policyKind[dpfs][1]
        else:
            return QVariant()


    def getColumnWidth(self, columnIndex):
        return columnIndex * 20

    def getRecord(self, row):
        return self.recordList[row][1]

    def columnCount(self, parentIndex = None):
        return len(self.columns) + 1

    def rowCount(self, parentIndex = None):
        return len(self.recordList)

    def flags(self, index):
        result = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.column() == 0:
            result |= Qt.ItemIsUserCheckable
        return result

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return toVariant(u'Выбрать')
            else:
                return toVariant(self.columns[section - 1].caption)
        if orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                return toVariant(section+1)
            if role == Qt.TextAlignmentRole:
                return alignRight
        return QVariant()
        
        
    def getCellValue(self, row, columnIndex):
        record = self.getRecord(row)
        if record == None:
            return QVariant()
        else:
            source = self.columns[columnIndex].source
            if hasattr(source, '__call__'):
                return toVariant(source(record))
            else:
                return toVariant(dbfRecordValue(record, source))
            

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row    = index.row()
        if role == Qt.DisplayRole:
            if column == 0:
                return QVariant()
            else:
                return self.getCellValue(row, column - 1)
        elif role == Qt.TextAlignmentRole:
            if column == 0:
                return QVariant()
            else:
                return self.columns[column - 1].alignment
        elif role == Qt.CheckStateRole and column == 0:
            return Qt.Checked if self.recordList[row][0] else Qt.Unchecked
        return QVariant()
        
    def setData(self, index, value, role):
        if role == Qt.CheckStateRole and index.column() == 0:
            row = index.row()
            checked, record = self.recordList[row]
            if checked:
                self.selectedCount -= 1
            else:
                self.selectedCount += 1
            self.recordList[row] = (not checked, record)
            self.recordSelected.emit(self.recordCount, self.selectedCount)
            return True
        else:
            return False

    def selectAll(self, checked):
        self.recordList = [(checked, record) for oldChecked, record in self.recordList]
        if checked:
            self.selectedCount = self.recordCount
        else:
            self.selectedCount = 0
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.recordCount - 1, 0))
