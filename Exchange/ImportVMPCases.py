# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
import os

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QDate

from Events.Action import CAction
from library import xlrd
from library.Utils import forceString, forceRef, forceDate, quote

from Exchange.Ui_ImportVMPCases import Ui_ImportVMPCases


class ImportVMPCases(QtGui.QDialog, Ui_ImportVMPCases):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.abort = False
        self.progressBar.reset()
        self.progressBar.setMaximum(1)
        self.progressBar.setValue(0)
        self.db = QtGui.qApp.db


    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()


    @pyqtSignature('')
    def on_btnSelectFile_clicked(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, u'Укажите файл с данными', self.edtFileName.text(), u'Файл xls (*.xls)')
        if fileName != '':
            self.edtFileName.setText(fileName)
            self.btnImport.setEnabled(True)


    @pyqtSignature('QString')
    def on_edtFileName_textChanged(self):
        filePath = forceString(self.edtFileName.text())
        path, ext = os.path.splitext(filePath)
        filePathValid = os.path.isfile(filePath) and ext.lower() == '.xls'
        self.btnImport.setEnabled(filePathValid)


    @pyqtSignature('')
    def on_btnAbort_clicked(self):
        self.abort = True


    @pyqtSignature('')
    def on_btnImport_clicked(self):
        self.logBrowser.clear()
        self.btnImport.setEnabled(False)
        self.abort=False
        self.progressBar.reset()
        self.progressBar.setMaximum(1)
        self.progressBar.setValue(0)
        self.btnAbort.setEnabled(True)
        QtGui.qApp.call(self, self.startImport)
        self.btnAbort.setEnabled(False)
        self.progressBar.setFormat(u'прервано' if self.abort else u'готово')
        self.btnImport.setEnabled(True)
        self.abort=False


    def startImport(self):
        def excelDateToQDate(cellValue, datemode, returnString=True, dateFormat='yyyy-MM-dd'):
            if isinstance(cellValue, float):
                year, month, day, hour, minute, second = xlrd.xldate_as_tuple(cellValue, datemode)
                if returnString:
                    return unicode(QDate(year, month, day).toString(dateFormat))
                else:
                    return QDate(year, month, day)
            return QDate()

        def getEventAndActionPropertyId(snils, eventExecDate):
            getEventAndActionPropertyIdSTMT = u"""
            SELECT
              Event.id as eventId, 
              Action.id as actionId,
              Event.setDate as talonHospDate
            FROM Event
            LEFT JOIN Client ON Event.client_id = Client.id
            LEFT JOIN EventType ON Event.eventType_id = EventType.id
            LEFT JOIN rbMedicalAidType ON EventType.medicalAidType_id = rbMedicalAidType.id
            LEFT JOIN Action ON Event.id = Action.event_id AND Action.deleted = 0
            LEFT JOIN ActionType ON Action.actionType_id = ActionType.id
            WHERE Event.deleted = 0
              AND Client.deleted = 0
              AND Client.SNILS = '{snils}'
              AND Event.execDate BETWEEN '{eventExecDate}' AND '{eventExecDate}' + interval 1 day
              AND rbMedicalAidType.regionalCode IN ('401', '402')
              AND ActionType.flatCode = 'VMPtalon'
            """.format(snils=snils, eventExecDate=eventExecDate)

            query = self.db.query(getEventAndActionPropertyIdSTMT)
            if query.next():
                record = query.record()
                return forceRef(record.value('eventId')), forceRef(record.value('actionId')), forceDate(record.value('talonHospDate'))
            else:
                return None, None, None


        fileName = forceString(self.edtFileName.text())
        workbook = xlrd.open_workbook(fileName)
        sheet = workbook.sheet_by_index(0)

        self.logBrowser.append(u'Найдено {rows} строк.\nНачат импорт.'.format(rows=str(sheet.nrows)))
        self.progressBar.setMaximum(sheet.nrows - 11) # первые 3 строки заголовка и 8 строк описания цветов

        for row in range(3, sheet.nrows-8):
            QtGui.qApp.processEvents()
            if self.abort:
                self.logBrowser.append(u'Импорт прерван пользователем!')
                return
            talonNumber = sheet.cell_value(row, 0)
            snils = str(sheet.cell_value(row, 8)).replace('-', '').replace(' ', '')
            eventExecDate = excelDateToQDate(sheet.cell_value(row, 4), workbook.datemode)
            talonDate = excelDateToQDate(sheet.cell_value(row, 3), workbook.datemode, returnString=False)

            if not eventExecDate:
                self.logBrowser.append(u'Строка {row}: ошибка при считывании "Дата выписки" или "Дата выписки" отсутствует '.format(row=row))
                self.progressBar.step()
                continue

            eventId, actionId, talonHospDate = getEventAndActionPropertyId(snils, eventExecDate)

            if not eventId:
                self.logBrowser.append(u'Строка {row}: событие не найдено!'.format(row=row))
                self.progressBar.step()
                continue

            self.logBrowser.append(u'Строка {row}: Событие для заполнение талона найдено, начато заполнение талона ВМП.'.format(row=row))

            if not (talonNumber and talonDate and talonHospDate):
                missedValues = []
                if not talonNumber:
                    missedValues.append(u'"Номер талона"')
                if not talonDate:
                    missedValues.append(u'"Дата талона"')
                if not talonHospDate:
                    missedValues.append(u'"Дата планируемой госпитализации"')
                self.logBrowser.append(u'Строка {row}: Значение ({missedValues}) отсутствует или произошла ошибка при получении значения, данный талон будет пропущен!.'.format(row=row, missedValues=u', '.join(missedValues)))
                self.progressBar.step()
                continue

            lockId = None
            try:
                self.db.query('CALL getAppLock_(%s, %d, %d, %s, %s, @res)' % (quote('Event'), eventId, 0, 1, quote('ImportVMPCases')))
                query = self.db.query('SELECT @res')

                if query.next():
                    record = query.record()
                    s = forceString(record.value(0)).split()
                    if len(s) > 1:
                        isSuccess = int(s[0])
                        if isSuccess:
                            lockId = int(s[1])
                        else:
                            self.logBrowser.append(u'Строка {row}: Событие {eventId} заблокировано'.format(row=row, eventId=eventId))
                if lockId:
                    action = CAction(record=self.db.getRecord('Action', '*', actionId))

                    if action:
                        propTalonNumber = action.getProperty(u'Номер талона')
                        if propTalonNumber:
                            propTalonNumber.setValue(talonNumber)

                        propTalonDate = action.getProperty(u'Дата талона')
                        if propTalonDate:
                            propTalonDate.setValue(talonDate)

                        propTalonHospDate = action.getProperty(u'Дата планируемой госпитализации')
                        if propTalonHospDate:
                            propTalonHospDate.setValue(talonHospDate)

                        action.save(idx=-1)
                        self.logBrowser.append(u'Строка {row}: талон ВМП заполнен.'.format(row=row))

            except Exception as e:
                self.logBrowser.append(u'Строка {row}: при заполнении талона ВМП произошла ошибка ({e})'.format(row=row, e=e))
            finally:
                if lockId:
                    self.db.query('CALL ReleaseAppLock(%d)' % lockId)
                self.progressBar.step()

        self.logBrowser.append(u'Импорт закончен!')
