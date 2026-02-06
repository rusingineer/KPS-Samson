#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from sys import *
import codecs
from os.path import *
from optparse import OptionParser

import os
import platform

if platform.system() != 'Windows':
    pathtail = '/appendix/kladr_update/main.py'
    sys.path.insert(0, os.path.realpath(__file__).replace(pathtail, ''))

from Exchange.Utils import insertTableDataFromDbf
#from library.DialogBase  import CDialogBase
from library.database    import CDatabase
from library.Utils       import *
from Exchange.Cimport    import Cimport, CDBFimport

from PyQt4 import QtCore, QtGui, QtSql
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSql import *
from Ui_main import Ui_MainWindow

import clear_sql
import create_kladr_sql
import create_okato_sql
import create_copy_sql
import rollback_updating_sql
import test_sql
import update_kladr_sql
import restore_parent_prefix_sql
import update_okato_sql
import update_s11_sql

from address_parser import parseAddress

def getParent(aCode):
    'Get parent code from KLADR code'
    length = 11
    if aCode[:2] == '00': # это военная часть
        return '001'
    # обрезаем код пункта:
    if aCode[9:12] != '000':
        length = 8
    elif aCode[6:9] != '000':
        length = 5
    elif aCode[3:6] != '000':
        length = 2
    else:
        return ''
    parent_code = aCode[:length] + '0'*(11-length)
    # обрезаем лишние нули:
    if parent_code[6:9] != '000':
        length = 8
    elif parent_code[3:6] != '000':
        length = 5
    elif parent_code[1:3] != '00':
        length = 3
    else:
        length = 0
    return parent_code[:length]


class mainWin(CDBFimport, QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.db = CDatabase()
        self.db.driverName = 'QMYSQL'
        self.connection = self.db.createConnection('kladr')
        Cimport.__init__(self, additionalInit = False)
#        self.log = QtGui.QStringListModel()
#        self.loglist = QtCore.QStringList()
#        self.listView.setModel(self.log)
        self.checkName()
            
     
    def openKLADR(self):
        self.log.append(u'Открытие БД kladr...')
        self.db.close()
        try:
            self.db.connect(self.connection, self.editServer.text(), None, 'kladr', self.editUser.text(), self.editPassword.text())
        except Exception, e:
            QtGui.QMessageBox.critical( None, 
                                    u'Ошибка!',
                                    u'Не могу открыть базу данных kladr!\nВы уверены, что правильно ввели сервер, имя пользователя и пароль?')
            return False
        return True      
     
     
    def openDB(self):  
        self.log.append(u'Открытие БД %s...'%self.editDatabase.text())
        self.db.close()
        try:
            self.db.connect(self.connection, self.editServer.text(), None, self.editDatabase.text(), self.editUser.text(), self.editPassword.text())
        except Exception, e:
            QtGui.QMessageBox.critical( None, 
                                    u'Ошибка!',
                                    u'Не могу открыть базу данных %s!\nВы уверены, что правильно ввели имя базы данных?'%self.editDatabase.text())
            return False
        return True
      
             
    def runProgramScript(self,  name,  dic,  title):
        error = self.runScript(name.COMMAND.split('\n'), dic) 
        if error is not None:
            QtGui.QMessageBox.warning(self, u'Ошибка при выполнении запроса к БД',
                        u'Ошибка при выполнении операции "%s".\n%s.'%(title, error.text()))
            self.log.append(unicode(error.text()))
            return False
        QtGui.qApp.processEvents()
        return True
        
    def loadTable(self, filename, tablename, fields_ = None):
        try:
            self.fullTable(filename, tablename, [], fields=fields_, mode=1, errors=1)
            return True
        except Exception, e:
            self.log.append(u'Файл %s не обнаружен и не будет загружаться.'%filename)
            return False

    def insertTableDataFromDbf(self, tablename, filename, encoding, binaries=[], fields=None, mode=0, errors=0):
        u"""
        Выкачивает данные из DBF и добавляет в таблицу БД
        tablename - имя таблицы БД
        filename - имя файла DBF
        encoding - кодировка, в которой хранится DBF
        binaries - список номеров полей, которые нужно перекодировать из бинарных в целые
        fields - номера полей, которые надо конвертировать (None - все поля).
                Если номер равен -1, нужно вставить значение по умолчанию.
        mode: 0 - IGNORE,
              1 - REPLACE
        errors: 0 - игнорировать
                1 - завершать работу и возвращать ошибку
        """
        return insertTableDataFromDbf(self.db, tablename, filename, encoding, binaries, fields, mode, errors, batch=10000)
        
    def loadKLADRFromDBF(self, dir):
        query = self.db.query( 'show columns from kladr.STREET' )
        street = [0, 1, 2, 3, 4, 5, 6, -1]
        while query.next():
            record = query.record()
            fieldName = forceString(record.value(0))
            if fieldName == 'eisPrefix':
                street.append(-1)
        result = self.loadTable(dir + '/ALTNAMES.DBF', 'ALTNAMES')
        result = self.loadTable(dir + '/KLADR.DBF', 'KLADR', [0, 1, 2, 3, 4, 5, 6, 7, -1, -1, -1, -1]) or result
        # Загружается всё долго, а чтобы в это время с КЛАДР можно было работать, восстанавливаем поля parent и prefix
        self.log.append(u'Установка вспомогательных полей parent и prefix...')
        self.runProgramScript(restore_parent_prefix_sql, {}, u'Восстановление полей parent и prefix')
        result = self.loadTable(dir + '/STREET.DBF', 'STREET', street) or result
        result = self.loadTable(dir + '/DOMA.DBF', 'DOMA', [0, 1, 2, 3, 4, 5, 6, 7, -1]) or result
        result = self.loadTable(dir + '/FLAT.DBF', 'FLAT') or result
        result = self.loadTable(dir + '/SOCRBASE.DBF', 'SOCRBASE', [0, 1, 2, 3, -1]) or result
        if result:
            self.log.append(u'Загрузка таблиц завершена.')
            return True
        else:
            self.log.append(u'Ошибка: не найден ни один из файлов ALTNAMES.DBF, KLADR.DBF, STREET.DBF, DOMA.DBF, FLAT.DBF, SOCRBASE.DBF')
            return False
      
    def loadOKATOFromDBF(self, dir):
        if self.loadTable(dir + '/OKATO.DBF', 'OKATO', [0, 1, 2, 3, 4, 5, -1]):
            self.log.append(u'Загрузка таблицы завершена.')
            return True
        else:
            self.log.append(u'Ошибка: не найден файл OKATO.DBF')
            return False
      
    def userHasCopyRight(self):
        return False
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        
    def hasCopy(self):
        return False
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
      
    def createCopy(self):
        if self.userHasCopyRight():
            return self.runProgramScript(create_copy_sql, {}, u'Резервное копирование данных')
        return True
      
    def rollback(self):
        if self.hasCopy():
            return self.runProgramScript(rollback_updating_sql, {}, u'Откат сделанных изменений')
        return True
        
    def fixResult(self, result):
        if result:
            self.log.append(u'Обновление выполнено!')
            QtGui.qApp.processEvents()
            QtGui.QMessageBox.information( None, 
                                    u'Всё хорошо!',
                                    u'Обновление выполнено.')
        else:
            QtGui.QMessageBox.information( None, 
                                    u'Всё плохо!',
                                    u'Обновление не выполнено.')
                                    
    def setParentCodes(self):
        table = self.db.forceTable('KLADR')
        records = self.db.getRecordList(table, 'id, CODE, parent, prefix')
        for record in records:
            code = forceString(record.value('CODE'))
            record.setValue('parent', getParent(code))
            record.setValue('prefix', code[:2])
            self.db.updateRecord(table, record)
        
    
    def updateKLADR(self):
        self.checkName()
        if not self.openKLADR():
            return
        kladrDir = self.lineKLADRDir.text()
        result = self.createCopy()
        result = result and self.runProgramScript(create_kladr_sql, {}, u'Cкрипт создания временных таблиц')
        result = result and self.loadKLADRFromDBF(kladrDir)
        # result = result and self.runProgramScript(update_kladr_sql,  {}, u'Обновляющий КЛАДР скрипт')
        if result:
            self.log.append(u'Обновление КЛАДР завершено!')
            if not self.openDB():
                return
            result = self.runProgramScript(update_s11_sql, {}, u'Обновляющий %s скрипт' % self.editDatabase.text())
        self.fixResult(result)
        return result


    def updateOKATO(self):
        self.checkName()
        if not self.openKLADR():
            return
        okatoDir = self.lineOKATODir.text()
        result = self.createCopy()
        result = result and self.runProgramScript(create_okato_sql, {}, u'Cкрипт создания временных таблиц')
        result = result and self.loadOKATOFromDBF(okatoDir)
        result = result and self.runProgramScript(update_okato_sql,  {}, u'Обновляющий ОКАТО скрипт')
        if result:
            self.log.append(u'Обновление ОКАТО завершено!')
            if not self.openDB():
                return
            result = self.runProgramScript(update_s11_sql, {}, u'Обновляющий %s скрипт'%self.editDatabase.text())
        self.fixResult(result)
        return result
      
    def parseAddresses(self):
        self.openDB()
        self.log.append(u'Выбор адресов...')
        result = self.db.query("""
        SELECT id, freeInput 
        FROM ClientAddress
        WHERE address_id IS NULL
        """)
        self.log.append(u'Разбор адресов...')
        defaultRegion = '7800000000000' #TODO: вытаскивать откуда-нибудь
        while result.next():
            record = result.record()
            id = forceRef(record.value('id'))
            freeInput = forceString(record.value('freeInput'))
            if len(freeInput):
                [status, region, street, house, corpus, flat, ostatok] = parseAddress(self.db, freeInput, defaultRegion)            
                corpusStr = u"кор. %s, "%corpus if len(corpus) else ""
                addressStr = u"%s, ул. %s, д. %s, %sкв. %s"%(region, street, house, corpusStr, flat)
                if status == 0:
                    message = addressStr
                    self.log.append(message)                               
                    #    self.log.append(u'%s, ул. %s, д. %s, кв. %s, не разобрано %s'%(region, street, house, flat, ostatok))
                elif status in (3, 4, 5):
                    if not (region == defaultRegion and len(street) == 0):
                        message = u'Разобрано не полностью: %s%s'%(addressStr, u', не разобрано %s'%ostatok if len(ostatok) else '')
                        self.log.append(message)
                    else:
                        pass # ни фига не разобрано!!!!!!!!!!!!!!!!!!!
                else:
                    self.log.append(u'Адрес не определен: %s'%freeInput)
            else:
                pass # адрес пустой!!!!!!!!!!!!!!!!!!!!!!!!!!!

    def test(self):
        if not self.openDB():
            return
        else:
            self.clearLog()
            self.runProgramScript(test_sql, {}, u'Проверяющий целостность БД скрипт')
            errorstxt = QtCore.QFile('errors.txt')
            errorstxt.open(QtCore.QFile.Text | QtCore.QFile.WriteOnly)
            data = self.log.toPlainText()
            errorstxt.writeData(data)
            errorstxt.close()
            self.log.append(u'Результаты сохранены в файле errors.txt')
            self.db.close()


    def checkName(self):
        self.pushUpdateKLADR.setEnabled(self.lineKLADRDir.text()!='')
        self.pushUpdateOKATO.setEnabled(self.lineOKATODir.text()!='')
        self.pushReverse.setEnabled(self.hasCopy())
            
            
    @pyqtSignature('')
    def on_pushKLADRDir_clicked(self):
        dirName = forceString(QtGui.QFileDialog.getExistingDirectory(
            self, u'Укажите каталог', self.lineKLADRDir.text()))
        if dirName != '':
            self.lineKLADRDir.setText(QDir.toNativeSeparators(dirName))
            self.checkName()
            
            
    @pyqtSignature('')
    def on_pushOKATODir_clicked(self):
        dirName = forceString(QtGui.QFileDialog.getExistingDirectory(
            self, u'Укажите каталог', self.lineOKATODir.text()))
        if dirName != '':
            self.lineOKATODir.setText(QDir.toNativeSeparators(dirName))
            self.checkName()

 

if __name__ == "__main__":
    parser = OptionParser(usage = "usage: %prog [options]",add_help_option=True)
    parser.add_option("-s", "--server",   dest="server",   help="server, default '%default'",              default="localhost", metavar="SERVER")
    parser.add_option("-d", "--database", dest="database", help="database, default '%default'",            default="s11",     metavar="DATABASE")
    parser.add_option("-u", "--user",     dest="user",     help="mysql user, default '%default'",          default="root",      metavar="USER")
    parser.add_option("-p", "--password", dest="password", help="mysql user password, default '%default'", default="",          metavar="PASSWORD")
    (options, args) = parser.parse_args()
    app = QtGui.QApplication(sys.argv)
    try:
        mw=mainWin()
        mw.show()
        app.exec_()
    except Exception, e:
        QtGui.QMessageBox.critical( None, 
                                    'error',
                                    unicode(e),
                                    QtGui.QMessageBox.Close)
    mw = None
    app = None
