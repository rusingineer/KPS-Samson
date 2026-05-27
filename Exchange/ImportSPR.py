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

import xml.etree.ElementTree as ET
import os
from zipfile import ZipFile

from PyQt4          import QtGui
from PyQt4.QtCore   import Qt, QVariant, pyqtSignature, SIGNAL, QDateTime, QDate
from library.Utils  import forceInt, forceString, toVariant, getPref, setPref, forceStringEx, forceDate, forceRef

from Exchange.Ui_ImportRbResult_Wizard_1 import Ui_ImportRbResult_Wizard_1
from Exchange.Ui_ImportRbResult_Wizard_3 import Ui_ImportRbResult_Wizard_3


def ImportSPR(parent=None):
    prefs = QtGui.qApp.preferences.windowPrefs
    zipName = forceString(getPref(prefs, 'ImportSPRZipName', ''))
    fileName = forceString(getPref(prefs, 'ImportSPRFileName', ''))
    geomerty = getPref(prefs, 'ImportSPRGeometry', QVariant()).toByteArray()

    dlg = CImportSPR(parent, fileName, zipName)
    dlg.restoreGeometry(geomerty)
    dlg.exec_()

    setPref(prefs, 'ImportSPRFileName', toVariant(dlg.fileName))
    setPref(prefs, 'ImportSPRZipName', toVariant(dlg.zipFile))
    setPref(prefs, 'ImportSPRGeometry', toVariant(dlg.saveGeometry()))


class CImportSPR(QtGui.QWizard):
    def __init__(self, parent, fileName, zipName):
        QtGui.QWizard.__init__(self, parent, Qt.Dialog)
        self.setWizardStyle(QtGui.QWizard.ModernStyle)
        self.setWindowTitle(u'Импорт справочников ТФОМС КК')
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.selectedItems = []
        self.fileName = fileName
        self.zipFile = zipName
        self.duplicatesResolveMethod = 0  # 0-спросить, 1-обновить, 2-пропустить

        self.addPage(CImportSPR_Page1(self))
        self.addPage(CImportSPR_Page2(self))


class CImportSPR_Page1(QtGui.QWizardPage, Ui_ImportRbResult_Wizard_1):
    def __init__(self, parent):
        QtGui.QWizardPage.__init__(self, parent)
        self._wizard = parent
        self.setupUi(self)
        self.chkFullLog.setVisible(False)
        self.progressBar.setVisible(False)
        self.statusLabel.setVisible(False)
        self.logBrowser.setVisible(False)
        self.edtFileName.setText(self._wizard.zipFile)
        self.rbAskUser.setVisible(False)
        self.rbSkip.setVisible(False)
        self.rbUpdate.setVisible(False)
        self.groupBox.setTitle(u'Доступны к загрузке:')
        self.lblAvailable = QtGui.QLabel(self.groupBox)
        self.vboxlayout1.addWidget(self.lblAvailable)
        self.lblAvailable.setWordWrap(True)
        self.lblAvailable.setText(u"""SPR01, SPR02, SPR11, SPR12, SPR15, SPR20, SPR69, SPR70, SPR71, SPR72, SPR73, SPR82, SPR89, SPR97, SPR98, SPRPFREF, V036, N021, F032""")
        self.tmpDir = ''


    def isComplete(self):
        return len(self.edtFileName.text()) > 0


    @pyqtSignature('bool')
    def on_btnSelectFile_clicked(self, checked=False):
        fileName = forceStringEx(QtGui.QFileDialog.getOpenFileName(
            self, u'Укажите файл с данными', self.edtFileName.text(), u'Архивы (*.zip)'))
        filePath, pureFileName = os.path.split(fileName)
        fileBaseName, fileExt = os.path.splitext(pureFileName) 
        if fileName:
            self.edtFileName.setText(fileName)
            self._wizard.zipFile = fileName.lower()
        if fileExt.lower() == '.zip':
            zf = ZipFile(fileName, 'r', allowZip64=True)
            zf.extract(zf.namelist()[0], self.getTmpDir())
            fileName = os.path.join(self.getTmpDir(), zf.namelist()[0])
            (name,  fileExt) = os.path.splitext(fileName)
        if not (fileExt.lower() in ('.xml')):
            self.edtFileName.setText('')
            return
        if fileName:
            self._wizard.fileName = fileName

    
    def getTmpDir(self):
        if not self.tmpDir:
            self.tmpDir = QtGui.qApp.getTmpDir('ImportSPR')
        return self.tmpDir
    

    @pyqtSignature('QString')
    def on_edtFileName_textChanged(self, text):
        self.emit(SIGNAL('completeChanged()'))


    @pyqtSignature('bool')
    def on_rbAskUser_clicked(self, checked=False):
        self._wizard.duplicatesResolveMethod = 0  # спросить


    @pyqtSignature('bool')
    def on_rbUpdate_clicked(self, checked=False):
        self._wizard.duplicatesResolveMethod = 1  # обновить


    @pyqtSignature('bool')
    def on_rbSkip_clicked(self, checked=False):
        self._wizard.duplicatesResolveMethod = 2  # пропустить


class CImportSPR_Page2(QtGui.QWizardPage, Ui_ImportRbResult_Wizard_3):
    def __init__(self, parent):
        QtGui.QWizardPage.__init__(self, parent)
        self._wizard = parent
        self.setupUi(self)
        self.aborted = False
        self.done = False
        self.nProcessed = 0
        self.nUpdated = 0
        self.nSkipped = 0
        self.nAdded = 0
        self.progressBar.reset()
        self.btnAbort.setEnabled(False)
        self.statusLabel.setVisible(False)
        self.connect(self, SIGNAL('import()'), self.import_, Qt.QueuedConnection)
        self.connect(parent, SIGNAL('rejected()'), self.on_btnAbort_clicked)


    def initializePage(self):
        self.emit(SIGNAL('import()'))


    def isComplete(self):
        return self.done


    def import_(self):
        self.progressBar.reset()
        self.progressBar.setMaximum(1)
        self.progressBar.setValue(0)
        self.btnAbort.setEnabled(True)

        self._wizard.setButtonLayout([QtGui.QWizard.FinishButton])
        db = QtGui.qApp.db
        db.transaction()
        try:
            result = self.readItems(self._wizard.fileName)
            if result == 1:
                msg = u'Загрузка справочника {name} завершена: обработано {proc},'\
                        u' добавлено {add}'.format(name=os.path.basename(self._wizard.fileName), proc=self.nProcessed, add=self.nAdded)
                if self.nUpdated:
                    msg = msg + u', обновлено {upd}'.format(upd=self.nUpdated)
                if self.nSkipped:
                    msg = msg + u', пропущено {skip}'.format(skip=self.nSkipped)
                self.logBrowser.append(msg)
        except Exception as e:
            db.rollback()
            QtGui.QMessageBox.critical(self, u'Ошибка импорта', unicode(e))
            self.btnAbort.setEnabled(False)
            raise
        else:
            if result == 1:
                db.commit()
                self.btnAbort.setEnabled(False)
                self.done = True
                self.emit(SIGNAL('completeChanged()'))


    @pyqtSignature('bool')
    def on_btnAbort_clicked(self, checked=False):
        self.aborted = True
        if not self.done:
            msg = u'Загрузка организаций завершена: обработано {proc},'\
                        u' добавлено {add}'.format(proc=self.nProcessed, add=self.nAdded)
            if self.nUpdated:
                msg = msg + u', обновлено {upd}'.format(upd=self.nUpdated)
            if self.nSkipped:
                msg = msg + u', пропущено {skip}'.format(skip=self.nSkipped)
            self.logBrowser.append(msg)
            QtGui.qApp.db.commit()
            self.btnAbort.setEnabled(False)
            self.done = True
            self.emit(SIGNAL('completeChanged()'))
            
                
    
    def readItems(self, fileName):
        if self._wizard.zipFile.endswith(('spr69.zip')):
            table = QtGui.qApp.db.table('soc_spr69')
            return self.processSPR69(fileName, table)
        tree = ET.parse(fileName)
        root = tree.getroot()
        self.progressBar.setMaximum(len(root))
        items = []  

        if root.tag != 'packet':
            raise Exception(u'Неверный корневой элемент "%s"' % root.tag)
        
        if self._wizard.zipFile.endswith('spr01.zip'):
            return self.processLPU(root)
        if self._wizard.zipFile.endswith('spr02.zip'):
            return self.processOrg(root)
        if self._wizard.zipFile.endswith('f032.zip'):
            return self.processMORF(root)
        if self._wizard.zipFile.endswith('spr15.zip'):
            return self.processPayRefuseTypes(root)
        if self._wizard.zipFile.endswith(('spr11.zip', 'spr12.zip', 'spr20.zip', 'spr82.zip', 'spr98.zip')):
            import re
            pattern = r'spr\d{2}\.'
            tableName = re.search(pattern, self._wizard.zipFile)
            table = QtGui.qApp.db.table('soc_'+tableName.group(0)[:-1])
            return self.processSOCSPR(root, table)
        if self._wizard.zipFile.endswith(('spr70.zip', 'spr71.zip', 'spr72.zip', 'spr73.zip')):
            import re
            pattern = r'spr\d{2}\.'
            tableName = re.search(pattern, self._wizard.zipFile)
            table = QtGui.qApp.db.table('soc_'+tableName.group(0)[:-1])
            return self.processKSGKUSL(root, table)    
        #if self._wizard.zipFile.endswith(('spr80.zip')):
            #table = QtGui.qApp.db.table('soc_spr80')
            #return self.processSPR80(root, table)
        if self._wizard.zipFile.endswith(('spr89.zip')):
            table = QtGui.qApp.db.table('soc_spr89')
            return self.processSPR89(root, table)
        if self._wizard.zipFile.endswith(('spr97.zip')):
            table = QtGui.qApp.db.table('soc_spr97')
            return self.processSPR97(root, table)
        if self._wizard.zipFile.endswith(('sprpfref.zip')):
            table = QtGui.qApp.db.table('soc_SPRPFREF')
            return self.processSPRPFREF(root, table)
        if self._wizard.zipFile.endswith(('v036.zip')):
            table = QtGui.qApp.db.table('soc_V036')
            return self.processv036(root, table)
        if self._wizard.zipFile.endswith(('n021.zip')):
            table = QtGui.qApp.db.table('soc_sprN021')
            return self.processSPRN021(root, table)
        return items
    
    
    def processLPU(self, root): #SPR01
        db = QtGui.qApp.db
        for item in root:
            self.progressBar.setValue(self.progressBar.value() + 1)
            if self.aborted:
                return 1
            if item.tag == 'zglv':
                continue
            if item.tag != 'zap':
                raise Exception(u'Неожиданный элемент "%s"' % item.tag)
            self.nProcessed += 1
            OGRN = forceString(item.find('OGRN').text) if item.find('OGRN') is not None else None
            name = forceString(item.find('NAME').text) if item.find('NAME') is not None else None

            if not OGRN:
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=red>Пропуск</font></b> `{}` отсутствует ОГРН.'.format(name))
                continue

            regionalCode = forceString(item.find('CODE').text) if item.find('CODE') is not None else None
            federalCode = forceString(item.find('CODE_RF').text) if item.find('CODE_RF') is not None else None
            endDate = forceDate(QDate.fromString(item.find('DATO').text, Qt.ISODate)) if item.find('DATO') is not None and item.find('DATO').text is not None else None
            codeNew = forceString(item.find('CODE_NEW').text) if item.find('CODE_NEW') is not None else None
            isActive = True
            notes = u''

            if endDate:
                isActive = False
            if codeNew:
                notes += u'Новый код: {0}; '.format(codeNew)
            if item.find('IS_GUZ') is not None and forceInt(item.find('IS_GUZ').text) != 0:
                notes += u'Террит., федеральная МО. '

            orgId = findOrgByOGRNandRegionalCode(OGRN, regionalCode)
            msg = u'Код: {}, Наименование: {}, ОГРН: {}'.format(orgId, name, OGRN)
            if orgId:
                updateOrg(orgId, name, name, '', '', OGRN, '03000',
                    '', '', '', '', None, None, None, regionalCode, federalCode, isActive, notes.strip(), netId=forceRef(db.translate('rbNet', 'code', '1', 'id')), setIsMedical=True)
                self.logBrowser.append(u'<b><font color=green>Обновляем</font></b> `{}`, ОГРН `{}`, код `{}`.'.format(name, OGRN, regionalCode))
                self.nUpdated += 1
            else:
                orgId = addOrg(name, name, '', '', '', '', OGRN, '03000',
                    '', '', '', '', None, None, None, regionalCode, federalCode, isActive, notes.strip(), netId=forceRef(db.translate('rbNet', 'code', '1', 'id')), setIsMedical=True)
                self.logBrowser.append(u'<b><font color=blue>Добавляем</font></b> `{}`, ОГРН `{}`, код `{}`.'.format(name, OGRN, regionalCode))
                self.nAdded += 1
            
            QtGui.qApp.processEvents()
        return 1


    def processOrg(self, root): #SPR02
        for item in root:
            self.progressBar.setValue(self.progressBar.value() + 1)
            if self.aborted:
                return 1
            if item.tag == 'zglv':
                continue
            if item.tag != 'zap':
                raise Exception(u'Неожиданный элемент "%s"' % item.tag)
            self.nProcessed += 1
            
            regionalCode = forceString(item.find('CODE').text) if item.find('CODE') is not None else None
            federalCode = forceString(item.find('CODE_RF').text) if item.find('CODE_RF') is not None else None
            OGRN = forceString(item.find('OGRN').text) if item.find('OGRN') is not None else None
            name = forceString(item.find('NAME').text) if item.find('NAME') is not None else None

            endDate = forceDate(QDate.fromString(item.find('DATO').text, Qt.ISODate)) if item.find('DATO') is not None and item.find('DATO').text is not None else None
            isActive = True

            if endDate:
                isActive = False

            if not OGRN:
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=red>Пропуск</font></b> `{}` отсутствует ОГРН.'.format(name))
                continue

            orgId = findOrgByOGRNandRegionalCode(OGRN, regionalCode)

            if orgId:
                updateOrg(orgId, name, name, '', '', OGRN, '03000',
                        '', '', '', '', None, None, None, regionalCode, federalCode, isActive, area='23'.ljust(13,'0'), isInsurer=True)
                self.logBrowser.append(u'<b><font color=green>Обновляем</font></b> `{}`, ОГРН `{}`, код `{}`.'.format(name, OGRN, regionalCode))
                self.nUpdated += 1
            else:
                orgId = addOrg(name, name, '', '',  '', '', OGRN, '03000',
                    '', '', '', '', None, None, None, regionalCode, federalCode, isActive, area='23'.ljust(13,'0'), isInsurer=True)
                self.logBrowser.append(u'<b><font color=blue>Добавляем</font></b> `{}`, ОГРН `{}`, код `{}`.'.format(name, OGRN, regionalCode))
                self.nAdded += 1

            QtGui.qApp.processEvents()
        return 1


    def processMORF(self, root): #F032
        db = QtGui.qApp.db
        for item in root:
            self.progressBar.setValue(self.progressBar.value() + 1)
            if self.aborted:
                return 1
            if item.tag == 'zglv':
                continue
            if item.tag != 'zap':
                raise Exception(u'Неожиданный элемент "%s"' % item.tag)
            self.nProcessed += 1
            
            OGRN = forceString(item.find('OGRN').text) if item.find('OGRN') is not None else None
            shortName = forceString(item.find('NAM_MOK').text) if item.find('NAM_MOK') is not None else None

            if not OGRN:
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=red>Пропуск</font></b> `{}` отсутствует ОГРН.'.format(shortName))
                continue
            
            OKATO = forceString(item.find('OKTMO_P').text) if item.find('OKTMO_P') is not None else None
            if len(OKATO) > 5:
                OKATO = OKATO[:5]
            if len(OKATO) < 5:
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=yellow>Пропуск</font></b> `%s`. Неправильный ОКАТО.' % shortName)
                continue
            if OKATO == '03000':
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=yellow>Пропуск</font></b> `%s`. МО КК.' % shortName)
                continue
            
            fullName = forceString(item.find('NAM_MOP').text) if item.find('NAM_MOP') is not None else None
            code = forceString(item.find('MCOD').text) if item.find('MCOD') is not None else None
            INN = forceString(item.find('INN').text) if item.find('INN') is not None else None
            KPP = forceString(item.find('KPP').text) if item.find('KPP') is not None else None
            isActive = not bool(forceDate(QDate.fromString(item.find('D_END').text, Qt.ISODate)) if item.find('D_END') is not None and item.find('D_END').text is not None else None)

            orgId = findOrgByOGRNandFederalCode(OGRN, code)

            if orgId:
                updateOrg(orgId, shortName, fullName, '', '', OGRN, OKATO,
                        '', '', '', '', None, None, None, '', code, isActive=isActive, notes='',
                        netId=forceRef(db.translate('rbNet', 'code', '1', 'id')), setIsMedical=True)
                self.logBrowser.append(u'<b><font color=green>Обновляем</font></b> `{}`, ОГРН `{}`, код `{}`.'.format(shortName, OGRN, code))
                self.nUpdated += 1
            else:
                orgId = addOrg(shortName, fullName, INN, KPP, '', '', OGRN, OKATO,
                    '', '', '', '', None, None, None, '', code, isActive=isActive, notes='',
                    netId=forceRef(db.translate('rbNet', 'code', '1', 'id')), setIsMedical=True)
                self.logBrowser.append(u'<b><font color=blue>Добавляем</font></b> `{}`, ОГРН `{}`, код `{}`.'.format(shortName, OGRN, code))
                self.nAdded += 1

            QtGui.qApp.processEvents()
        return 1
    
    
    def processPayRefuseTypes(self, root):
        for item in root:
            self.progressBar.setValue(self.progressBar.value() + 1)
            if self.aborted:
                return 1
            if item.tag == 'zglv':
                continue
            if item.tag != 'zap':
                raise Exception(u'Неожиданный элемент "%s"' % item.tag)
            self.nProcessed += 1
            code = forceString(item.find('CODE').text) if item.find('CODE') is not None else None
            if not code:
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=red>Пропуск</font></b> отсутствует код.')
                continue
            
            name = forceString(item.find('NAME').text) if item.find('NAME') is not None else None
            if not code:
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=red>Пропуск</font></b> `{}` отсутствует наименование.'.format(code))
                continue

            payRefuseTypeId = findPayRefuseType(code)
            reason = forceString(item.find('KOMMENT').text) if item.find('KOMMENT') is not None else None
            
            if payRefuseTypeId:
                updatePayRefuseType(code, name, reason)
                self.logBrowser.append(u'<b><font color=green>Обновляем</font></b> Наименование `{}`, код `{}`.'.format(name, code))
                self.nUpdated += 1
            else:
                payRefuseTypeId = addPayRefuseType(code, name, reason)
                self.logBrowser.append(u'<b><font color=blue>Добавляем</font></b> Наименование `{}`, код `{}`.'.format(name, code))
                self.nAdded += 1
            
            QtGui.qApp.processEvents()
        return 1
    
    
    def processSOCSPR(self, root, table): #SPR11, SPR12, SPR20, SPR82, SPR98
        clearTable(table)
        records = []
        if table.name() == 'soc_spr20':
            spr20 = True
        else:
            spr20 = False
            
        for item in root:
            self.progressBar.setValue(self.progressBar.value() + 1)
            if self.aborted:
                if records:
                    QtGui.qApp.db.insertRecordList(table, records)
                return 1
            if item.tag == 'zglv':
                continue
            if item.tag != 'zap':
                raise Exception(u'Неожиданный элемент "%s"' % item.tag)
            self.nProcessed += 1
            code = forceString(item.find('CODE').text) if item.find('CODE') is not None else None
            if not code:
                code = forceString(item.find('KUSL').text) if item.find('KUSL') is not None else None
            name = forceString(item.find('NAME').text) if item.find('NAME') is not None else None

            if not code:
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=red>Пропуск</font></b> `{}` отсутствует код.'.format(name))
                continue

            groupCode = forceString(item.find('CODE_GR').text) if item.find('CODE_GR') is not None else None
            moCode = forceString(item.find('CODE_MO').text) if item.find('CODE_MO') is not None else None
            begDate = forceDate(QDate.fromString(item.find('DATN').text, Qt.ISODate)) if item.find('DATN') is not None and item.find('DATN').text is not None else None
            endDate = forceDate(QDate.fromString(item.find('DATO').text, Qt.ISODate)) if item.find('DATO') is not None and item.find('DATO').text is not None else None
            if spr20:
                isOms = forceInt(item.find('IS_OMS').text) if item.find('IS_OMS') is not None else None
                if not isOms:
                    self.nSkipped += 1
                    self.logBrowser.append(u'<b><font color=red>Пропуск</font></b> `{}` отсутствует в ОМС.'.format(name))
                    continue
                    
            records.append(addSPR(table, code, name, groupCode, begDate, endDate, moCode))
            self.logBrowser.append(u'<b><font color=blue>Добавляем</font></b> код `{}` {}.'.format(code, ', "'+name+'"' if name else ''))
            self.nAdded += 1
            
            QtGui.qApp.processEvents()
        if records:
            QtGui.qApp.db.insertRecordList(table, records)
        return 1
    
    
    def processKSGKUSL(self, root, table): #SPR70, SPR71, SPR72, SPR73
        clearTable(table)
        records = []
        for item in root:
            self.progressBar.setValue(self.progressBar.value() + 1)
            if self.aborted:
                if records:
                    QtGui.qApp.db.insertRecordList(table, records)
                return 1
            if item.tag == 'zglv':
                continue
            if item.tag != 'zap':
                raise Exception(u'Неожиданный элемент "%s"' % item.tag)
            self.nProcessed += 1
            code = forceString(item.find('KSGKUSL').text) if item.find('KSGKUSL') is not None else None
            if not code:
                code = forceString(item.find('CODE').text) if item.find('CODE') is not None else None
                
            if not code:
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=red>Пропуск</font></b> отсутствует KSGKUSL.')
                continue

            itog = forceString(item.find('KSGITOG').text) if item.find('KSGITOG') is not None else None
            mkb = forceString(item.find('KSGMKBX').text) if item.find('KSGMKBX') is not None else None
            begDate = forceDate(QDate.fromString(item.find('DATN').text, Qt.ISODate)) if item.find('DATN') is not None and item.find('DATN').text is not None else None
            endDate = forceDate(QDate.fromString(item.find('DATO').text, Qt.ISODate)) if item.find('DATO') is not None and item.find('DATO').text is not None else None
            code_2 = forceString(item.find('CODE2').text) if item.find('CODE2') is not None else None
            level = forceString(item.find('LEV').text) if item.find('LEV') is not None else None

            records.append(addKSGKUSL(table, code, begDate, endDate, itog, mkb, code_2, level))
            self.logBrowser.append(u'<b><font color=blue>Добавляем</font></b> KSGKUSL `{}` {}.'.format(code, ', MKB: "'+mkb+'"' if mkb else ''))
            self.nAdded += 1

            QtGui.qApp.processEvents()
        if records:
            QtGui.qApp.db.insertRecordList(table, records)
        return 1
    
    
    def processSPR80(self, root, table): #SPR80
        clearTable(table)
        records = []
        for item in root:
            self.progressBar.setValue(self.progressBar.value() + 1)
            if self.aborted:
                if records:
                    QtGui.qApp.db.insertRecordList(table, records)
                return 1
            if item.tag == 'zglv':
                continue
            if item.tag != 'zap':
                raise Exception(u'Неожиданный элемент "%s"' % item.tag)
            self.nProcessed += 1
            code = forceString(item.find('CODE').text) if item.find('CODE') is not None else None
            name = forceString(item.find('NAME').text) if item.find('NAME') is not None else None
                
            if not code:
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=red>Пропуск</font></b> `{}` отсутствует код.'.format(name))
                continue

            days = forceString(item.find('KD').text) if item.find('KD') is not None else None
            hospital = forceString(item.find('KOL').text) if item.find('KOL') is not None else None
            begDate = forceDate(QDate.fromString(item.find('DATN').text, Qt.ISODate)) if item.find('DATN') is not None and item.find('DATN').text is not None else None
            endDate = forceDate(QDate.fromString(item.find('DATO').text, Qt.ISODate)) if item.find('DATO') is not None and item.find('DATO').text is not None else None
            drugName = forceString(item.find('MNN').text) if item.find('MNN') is not None else None
            note = forceString(item.find('COMMENT').text) if item.find('COMMENT') is not None else None

            
            records.append(addSPR80(table, code, begDate, endDate, name, days, hospital, drugName, note))
            self.logBrowser.append(u'<b><font color=blue>Добавляем</font></b> `{}`, код `{}`.'.format(name, code))
            self.nAdded += 1

            QtGui.qApp.processEvents()
        if records:
            QtGui.qApp.db.insertRecordList(table, records)
        return 1      
    
    
    def processSPR89(self, root, table): #SPR89
        clearTable(table)
        records = []
        for item in root:
            self.progressBar.setValue(self.progressBar.value() + 1)
            if self.aborted:
                if records:
                    QtGui.qApp.db.insertRecordList(table, records)
                return 1
            if item.tag == 'zglv':
                continue
            if item.tag != 'zap':
                raise Exception(u'Неожиданный элемент "%s"' % item.tag)
            self.nProcessed += 1
            code = forceString(item.find('CODE_GR').text) if item.find('CODE_GR') is not None else None
            tariff = forceString(item.find('B_TARIFF').text) if item.find('B_TARIFF') is not None else None
            begDate = forceDate(QDate.fromString(item.find('DATN').text, Qt.ISODate)) if item.find('DATN') is not None and item.find('DATN').text is not None else None
            endDate = forceDate(QDate.fromString(item.find('DATO').text, Qt.ISODate)) if item.find('DATO') is not None and item.find('DATO').text is not None else None

            records.append(addSPR89(table, code, begDate, endDate, tariff))
            self.logBrowser.append(u'<b><font color=blue>Добавляем</font></b> Тариф: {}, Группы: {}.'.format(tariff, code))
            self.nAdded += 1
            QtGui.qApp.processEvents()
        if records:
            QtGui.qApp.db.insertRecordList(table, records)
        return 1   
    
    
    def processSPR97(self, root, table): #SPR97
        clearTable(table)
        records = []
        for item in root:
            self.progressBar.setValue(self.progressBar.value() + 1)
            if self.aborted:
                if records:
                    QtGui.qApp.db.insertRecordList(table, records)
                return 1
            if item.tag == 'zglv':
                continue
            if item.tag != 'zap':
                raise Exception(u'Неожиданный элемент "%s"' % item.tag)
            self.nProcessed += 1
            code = forceString(item.find('KUSL').text) if item.find('KUSL') is not None else None
                
            if not code:
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=red>Пропуск</font></b> отсутствует код.')
                continue

            begDate = forceDate(QDate.fromString(item.find('DATN').text, Qt.ISODate)) if item.find('DATN') is not None and item.find('DATN').text is not None else None
            endDate = forceDate(QDate.fromString(item.find('DATO').text, Qt.ISODate)) if item.find('DATO') is not None and item.find('DATO').text is not None else None

            records.append(addSPR97(table, code, begDate, endDate))
            self.logBrowser.append(u'<b><font color=blue>Добавляем</font></b> Код: {}, Дата начала: {}.'.format(code, forceString(begDate)))
            self.nAdded += 1
            
            QtGui.qApp.processEvents()
        if records:
            QtGui.qApp.db.insertRecordList(table, records)
        return 1    
    
    
    def processSPRPFREF(self, root, table): #SPRPFREF
        clearTable(table)
        records = []
        for item in root:
            self.progressBar.setValue(self.progressBar.value() + 1)
            if self.aborted:
                if records:
                    QtGui.qApp.db.insertRecordList(table, records)
                return 1
            if item.tag == 'zglv':
                continue
            if item.tag != 'zap':
                raise Exception(u'Неожиданный элемент "%s"' % item.tag)
            self.nProcessed += 1
            type = forceString(item.find('TYPE').text) if item.find('TYPE') is not None else None
            code = forceString(item.find('CODE_UR').text) if item.find('CODE_UR') is not None else None
            code_mo = forceString(item.find('CODE_MO').text) if item.find('CODE_MO') is not None else None
            begDate = forceDate(QDate.fromString(item.find('DATN').text, Qt.ISODate)) if item.find('DATN') is not None and item.find('DATN').text is not None else None
            endDate = forceDate(QDate.fromString(item.find('DATO').text, Qt.ISODate)) if item.find('DATO')is not None and item.find('DATO').text is not None else None
            vs = forceString(item.find('VS').text) if item.find('VS') is not None else None
            vp = forceString(item.find('VP').text) if item.find('VP') is not None else None

            records.append(addSPRPFREF(table, code, begDate, endDate, type, code_mo, vs, vp))
            self.logBrowser.append(u'<b><font color=blue>Добавляем</font></b> Тип: {}, Код: {}, VS: {}, VP: {}, Дата начала: {}.'.format(type, code, vs, vp, forceString(begDate)))
            self.nAdded += 1
            
            QtGui.qApp.processEvents()
        if records:
            QtGui.qApp.db.insertRecordList(table, records)
        return 1 
    
    
    def processv036(self, root, table): #v036
        clearTable(table)
        records = []
        for item in root:
            self.progressBar.setValue(self.progressBar.value() + 1)
            if self.aborted:
                if records:
                    QtGui.qApp.db.insertRecordList(table, records)
                return 1
            if item.tag == 'zglv':
                continue
            if item.tag != 'zap':
                raise Exception(u'Неожиданный элемент "%s"' % item.tag)
            self.nProcessed += 1
            code = forceString(item.find('S_CODE').text) if item.find('S_CODE') is not None else None
            name = forceString(item.find('NAME').text) if item.find('NAME') is not None else None

            if not code:
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=red>Пропуск</font></b> `{}` отсутствует код.'.format(name))
                continue
            
            parameter = forceString(item.find('Parameter').text) if item.find('Parameter') is not None else None
            begDate = forceDate(QDate.fromString(item.find('DATEBEG').text, Qt.ISODate)) if item.find('DATEBEG') is not None and item.find('DATEBEG').text is not None else None
            endDate = forceDate(QDate.fromString(item.find('DATEEND').text, Qt.ISODate)) if item.find('DATEEND')is not None and item.find('DATEEND').text is not None else None
            note = forceString(item.find('COMMENT').text) if item.find('COMMENT') is not None else None

            records.append(addV036(table, code, begDate, endDate, name, parameter, note))
            self.logBrowser.append(u'<b><font color=blue>Добавляем</font></b> Код: {}, Наименование: {}, Дата начала: {}.'.format(code, name, forceString(begDate)))
            self.nAdded += 1
            
            QtGui.qApp.processEvents()
        if records:
            QtGui.qApp.db.insertRecordList(table, records)
        return 1
    
    
    def processSPR69(self, fileName, table): #SPR69
        tableMes = QtGui.qApp.db.table('mes.SPR69')
        clearTable(table)
        clearTable(tableMes)
        records = []
        mesRecords = []
        self.progressBar.setMaximum(0)
        for event, item in ET.iterparse(fileName):
            if self.aborted:
                if records:
                    QtGui.qApp.db.insertRecordList(table, records)
                if mesRecords:
                    QtGui.qApp.db.insertRecordList(tableMes, mesRecords)
                return 1
            if item.tag != 'zap':
                continue
            self.nProcessed += 1
            begDate = forceDate(QDate.fromString(item.find('DATN').text, Qt.ISODate)) if item.find('DATN') is not None and item.find('DATN').text is not None else None
            if begDate.year() in (QDate.currentDate().year(), QDate.currentDate().year() - 1):
                name = forceString(item.find('VPNAME').text) if item.find('VPNAME') is not None else None
                mkb1 = forceString(item.find('MKBX').text) if item.find('MKBX') is not None else None
                mkb2 = forceString(item.find('MKBX2').text) if item.find('MKBX2') is not None else None
                mkb3 = forceString(item.find('MKBX3').text) if item.find('MKBX3') is not None else None
                code = forceString(item.find('KUSL').text) if item.find('KUSL') is not None else None
                age = forceString(item.find('AGE').text) if item.find('AGE') is not None else None
                sex = forceString(item.find('POL').text) if item.find('POL') is not None else None
                dlit = forceString(item.find('DLIT').text) if item.find('DLIT') is not None else None
                krit = forceString(item.find('KRIT').text) if item.find('KRIT') is not None else None
                fr = forceString(item.find('FR').text) if item.find('FR') is not None else None
                ksgcode = forceString(item.find('KSGCODE').text) if item.find('KSGCODE') is not None else None
                ksgkoef = forceString(item.find('KSGKOEF').text) if item.find('KSGKOEF') is not None else None
                endDate = forceDate(QDate.fromString(item.find('DATO').text, Qt.ISODate)) if item.find('DATO') is not None and item.find('DATO').text is not None else None

                records.append(addSPR69(table, name, mkb1, mkb2, mkb3, code, age, sex, dlit, krit, fr, ksgcode, ksgkoef, begDate, endDate))
                mesRecords.append(addMesSPR69(tableMes, name, mkb1, mkb2, mkb3, code, age, sex, dlit, krit, fr, ksgcode, ksgkoef, begDate, endDate))
                # self.logBrowser.append(u'<b><font color=blue>Добавляем</font></b> Код: {}, Наименование: {}, Дата начала: {}.'.format(code, name, forceString(begDate)))
                self.nAdded += 1
            else:
                self.nSkipped += 1
            
            QtGui.qApp.processEvents()
            if len(records) == 10000:
                QtGui.qApp.db.insertRecordList(table, records)
                records = []
            if len(mesRecords) == 10000:
                QtGui.qApp.db.insertRecordList(tableMes, mesRecords)
                mesRecords = []
            item.clear()
        if records:
            QtGui.qApp.db.insertRecordList(table, records)
        if mesRecords:
            QtGui.qApp.db.insertRecordList(tableMes, mesRecords)
        QtGui.qApp.db.query('CALL mes.UpdateMesfSpr69;')   
        self.progressBar.setMaximum(self.nProcessed)
        self.progressBar.setValue(self.nProcessed)
        QtGui.qApp.processEvents()
        return 1    
    
    
    def processSPRN021(self, root, table): #SPRN021
        clearTable(table)
        records = []
        for item in root:
            self.progressBar.setValue(self.progressBar.value() + 1)
            if self.aborted:
                if records:
                    QtGui.qApp.db.insertRecordList(table, records)
                return 1
            if item.tag == 'zglv':
                continue
            if item.tag != 'zap':
                raise Exception(u'Неожиданный элемент "%s"' % item.tag)
            self.nProcessed += 1
            code = forceString(item.find('ID_ZAP').text) if item.find('ID_ZAP') is not None else None
                
            if not code:
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=red>Пропуск</font></b> отсутствует код.')
                continue
            
            codeSh = forceString(item.find('CODE_SH').text) if item.find('CODE_SH') is not None else None
                
            if not codeSh:
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=red>Пропуск</font></b> отсутствует код схемы.')
                continue
            
            idLekp = forceString(item.find('ID_LEKP').text) if item.find('ID_LEKP') is not None else None
                
            if not idLekp:
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=red>Пропуск</font></b> отсутствует ИД лекарственного препарата.')
                continue
            
            idLekpExt = forceString(item.find('ID_LEKP_EXT').text) if item.find('ID_LEKP_EXT') is not None else None
                
            if not idLekpExt:
                self.nSkipped += 1
                self.logBrowser.append(u'<b><font color=red>Пропуск</font></b> отсутствует внешний ИД лекарственного препарата.')
                continue

            begDate = forceDate(QDate.fromString(item.find('DATEBEG').text, Qt.ISODate)) if item.find('DATEBEG') is not None and item.find('DATEBEG').text is not None else None
            endDate = forceDate(QDate.fromString(item.find('DATEEND').text, Qt.ISODate)) if item.find('DATEEND') is not None and item.find('DATEEND').text is not None else None
            lekpExt = forceString(item.find('LEKP_EXT').text) if item.find('LEKP_EXT') is not None else None

            records.append(addSPRN021(table, code, codeSh, idLekp, lekpExt, idLekpExt, begDate, endDate))
            self.logBrowser.append(u'<b><font color=blue>Добавляем</font></b> Код: {}, Дата начала: {}.'.format(code, forceString(begDate)))
            self.nAdded += 1
            
            QtGui.qApp.processEvents()
        if records:
            QtGui.qApp.db.insertRecordList(table, records)
        return 1    
    
    
# 0-пропустить, 1-добавить, 2-обновить
def getDuplicatesResolveMethod(parent, duplicatesResolveMethod, msg):
    if duplicatesResolveMethod == 0:  # спросить у пользователя
        msgbox = QtGui.QMessageBox()
        msgbox.setText(u'Обнаружено совпадение:\n' + msg)
        msgbox.addButton(u'Обновить', QtGui.QMessageBox.ActionRole)  # 0
        msgbox.addButton(u'Добавить', QtGui.QMessageBox.ActionRole)  # 1
        msgbox.addButton(u'Пропустить', QtGui.QMessageBox.ActionRole)  #2
        msgbox.addButton(u'Закрыть', QtGui.QMessageBox.RejectRole) #3
        msgbox.buttons()[0].setVisible(False)
        btn = msgbox.exec_()
        if btn == 3:
            return 3
        if btn == 0: # обновить
            return 2
        if btn == 1:  # добавить
            return 1
        return 0
    if duplicatesResolveMethod == 1:  # обновить
        return 2
    return 0


def clearTable(table):
    db = QtGui.qApp.db
    name = table.name()
    db.query('SET SQL_SAFE_UPDATES = 0;')
    if not name == 'soc_spr69' and not name =='mes.SPR69':
        db.deleteRecordSimple(table, 'True')
    else:
        db.query(u'''DELETE FROM {} WHERE datn >= STR_TO_DATE(CONCAT(year(CURDATE()), '-01-01'), '%Y-%m-%d');'''.format(name))
    db.query('SET SQL_SAFE_UPDATES = 1;')
    
#############################################################################################################################
#SPR01, SPR02, F032
def findOrgByOGRNandRegionalCode(OGRN, regionalCode):
    table = QtGui.qApp.db.table('Organisation')
    record = QtGui.qApp.db.getRecordEx(table, 'id',  [table['deleted'].eq(0),
                                                        table['OGRN'].eq(OGRN),
                                                        table['infisCode'].eq(regionalCode)], 'id')
    if record:
        return forceRef(record.value(0))
    else:
        return None


def findOrgByOGRNandFederalCode(OGRN, federalCode):
    table = QtGui.qApp.db.table('Organisation')
    record = QtGui.qApp.db.getRecordEx(table, 'id', [table['deleted'].eq(0),
                                                        table['OGRN'].eq(OGRN),
                                                        table['smoCode'].eq(federalCode)], 'id')
    if record:
        return forceRef(record.value(0))
    else:
        return None


def updateOrg(orgId, shortName, fullName, OKPO, OKVED, OGRN, OKATO,
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
    
    
def addOrg(shortName, fullName, INN, KPP, OKPO, OKVED, OGRN, OKATO,
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
#############################################################################################################################
#SPR11, SPR12, SPR20, SPR82, SPR98


def addSPR(table, code, name, groupCode, begDate, endDate, moCode):
    codeField = 'code' if not table.name() == 'soc_spr82' else 'CODE' #другой регистр у spr82
    datnField = 'DATN' if table.name() == 'soc_spr82' else 'begDate' if table.name() == 'soc_spr98' else 'datn' #отличные поля у spr98 и spr82
    datoField = 'DATO' if table.name() == 'soc_spr82' else 'endDate' if table.name() == 'soc_spr98' else 'dato' #отличные поля у spr98 и spr82
    record = table.newRecord()
    record.setValue(codeField, toVariant(code))
    record.setValue(datnField, toVariant(begDate))
    record.setValue(datoField, toVariant(endDate))
    if name:  
        record.setValue('name', toVariant(name))
    if groupCode:
        record.setValue('code_gr', toVariant(groupCode))
    if moCode:
        record.setValue('code_mo', toVariant(moCode))
    return record
#############################################################################################################################
#SPR70, SPR71, SPR72, SPR73


def addKSGKUSL(table, code, begDate, endDate, itog, mkb, code_2, level):
    record = table.newRecord()
    record.setValue('ksgkusl', toVariant(code))
    record.setValue('datn', toVariant(begDate))
    record.setValue('dato', toVariant(endDate))
    if itog:
        record.setValue('ksgitog', toVariant(itog))
    if mkb:
        record.setValue('ksgmkb', toVariant(mkb))
    if code_2:
        record.setValue('ksgkusl2', toVariant(code_2))
    if level:
        record.setValue('level', toVariant(level))
    return record
#############################################################################################################################
#SPR80


def addSPR80(table, code, begDate, endDate, name, days, hospital, drugName, note):
    record = table.newRecord()
    record.setValue('begDate', toVariant(begDate))
    record.setValue('code', toVariant(code))
    if name:
        record.setValue('name', toVariant(name))
    if endDate:
        record.setValue('endDate', toVariant(endDate))
    if days:
        record.setValue('days', toVariant(days))
    if hospital:
        record.setValue('hospital', toVariant(hospital))
    if drugName:
        record.setValue('drugName', toVariant(drugName))
    if note:
        record.setValue('note', toVariant(note))
    return record
#############################################################################################################################
#SPR89


def addSPR89(table, code, begDate, endDate, tariff):
    record = table.newRecord()
    record.setValue('DATN', toVariant(begDate))
    record.setValue('CODE_GR', toVariant(code))
    if tariff:
        record.setValue('B_TARIFF', toVariant(tariff))
    if endDate:
        record.setValue('DATO', toVariant(endDate))
    return record

#############################################################################################################################
#SPR97

def addSPR97(table, code, begDate, endDate):
    record = table.newRecord()
    record.setValue('kusl', toVariant(code))
    record.setValue('datn', toVariant(begDate))
    record.setValue('dato', toVariant(endDate))
    return record
#############################################################################################################################
#SPRPFREF


def addSPRPFREF(table, code, begDate, endDate, type, code_mo, vs, vp):
    record = table.newRecord()
    record.setValue('DATN', toVariant(begDate))
    record.setValue('CODE_UR', toVariant(code))
    record.setValue('TYPE', toVariant(type))
    record.setValue('VS', toVariant(vs))
    record.setValue('VP', toVariant(vp))
    if endDate:
        record.setValue('DATO', toVariant(endDate))
    if code_mo:
        record.setValue('CODE_MO', toVariant(code_mo))
    return record
#############################################################################################################################
#V036


def addV036(table, code, begDate, endDate, name, parameter, note):
    record = table.newRecord()
    record.setValue('begDate', toVariant(begDate))
    record.setValue('serviceCode', toVariant(code))
    record.setValue('serviceName', toVariant(name))
    record.setValue('parameter', toVariant(parameter))
    if endDate:
        record.setValue('endDate', toVariant(endDate))
    if note:
        record.setValue('comment', toVariant(note))
    return record
#############################################################################################################################
#SPR69


def addSPR69(table, name, mkb1, mkb2, mkb3, code, age, sex, dlit, krit, fr, ksgcode, ksgkoef, begDate, endDate):
    record = table.newRecord()
    record.setValue('vpname', toVariant(name))
    record.setValue('mkb', toVariant(mkb1))
    record.setValue('mkb2', toVariant(mkb2))
    record.setValue('mkb3', toVariant(mkb3))
    record.setValue('kusl', toVariant(code))
    record.setValue('age', toVariant(age))
    record.setValue('pol', toVariant(sex))
    record.setValue('dlit', toVariant(dlit))
    record.setValue('KRIT', toVariant(krit))
    record.setValue('fr', toVariant(fr))
    record.setValue('ksgkusl', toVariant(ksgcode))
    record.setValue('ksgkoef', toVariant(ksgkoef))
    record.setValue('datn', toVariant(begDate))
    record.setValue('dato', toVariant(endDate))
    return record

def addMesSPR69(table, name, mkb1, mkb2, mkb3, code, age, sex, dlit, krit, fr, ksgcode, ksgkoef, begDate, endDate):
    record = table.newRecord()
    record.setValue('VPNAME', toVariant(name))
    record.setValue('MKBX', toVariant(mkb1))
    record.setValue('MKBX2', toVariant(mkb2))
    record.setValue('MKBX3', toVariant(mkb3))
    record.setValue('KUSL', toVariant(code))
    record.setValue('AGE', toVariant(age))
    record.setValue('POL', toVariant(sex))
    record.setValue('DLIT', toVariant(dlit))
    record.setValue('KRIT', toVariant(krit))
    record.setValue('FR', toVariant(fr))
    record.setValue('KSGCODE', toVariant(ksgcode))
    record.setValue('KSGKOEF', toVariant(ksgkoef))
    record.setValue('DATN', toVariant(begDate))
    record.setValue('DATO', toVariant(endDate))
    return record
#############################################################################################################################
#SPRN021


def addSPRN021(table, code, codeSh, idLekp, lekpExt, idLekpExt, begDate, endDate):
    record = table.newRecord()
    record.setValue('code', toVariant(code))
    record.setValue('CODE_SH', toVariant(codeSh))
    record.setValue('ID_LEKP', toVariant(idLekp))
    record.setValue('DATN', toVariant(begDate))
    record.setValue('DATO', toVariant(endDate))
    record.setValue('LEKP_EXT', toVariant(lekpExt))
    record.setValue('ID_LEKP_EXT', toVariant(idLekpExt))
    return record
#############################################################################################################################
#SPR015


def findPayRefuseType(code):
    table = QtGui.qApp.db.table('rbPayRefuseType')
    record = QtGui.qApp.db.getRecordEx(table, 'id',  [table['code'].eq(code)], 'code')
    if record:
        return forceRef(record.value(0))
    else:
        return None


def updatePayRefuseType(code, name, reason):
    table = QtGui.qApp.db.table('rbPayRefuseType')
    record = QtGui.qApp.db.getRecordEx(table, '*',  [table['code'].eq(code)], 'code')
    
    record.setValue('name', toVariant(name))
    record.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
    record.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
    record.setValue('reason', toVariant(reason))
    
    return QtGui.qApp.db.updateRecord(table, record)


def addPayRefuseType(code, name, reason):
    table = QtGui.qApp.db.table('rbPayRefuseType')
    record = table.newRecord()
    
    record.setValue('code', toVariant(code))
    record.setValue('name', toVariant(name))
    record.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
    record.setValue('createDatetime', toVariant(QDateTime().currentDateTime()))
    record.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
    record.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
    record.setValue('reason', toVariant(reason))
    record.setValue('finance_id', toVariant(2))
    record.setValue('rerun', toVariant(1))
    
    return QtGui.qApp.db.insertRecord(table, record)
    