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
from PyQt4.QtCore import QDate, pyqtSignature, QDir, QTime

from library import xlwt
from library.Utils import forceString, forceStringEx, forceDate

from Exchange.Ui_ExportVMPCases import Ui_ExportVMPCases


class ExportVMPCases(QtGui.QDialog, Ui_ExportVMPCases):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.abort = False
        self.edtBegDate.setDate(QDate.currentDate())
        self.edtEndDate.setDate(QDate.currentDate())
        self.progressBar.reset()
        self.progressBar.setMaximum(1)
        self.progressBar.setValue(0)
        self.db = QtGui.qApp.db


    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()


    @pyqtSignature('')
    def on_btnSelectDir_clicked(self):
        path = QtGui.QFileDialog.getExistingDirectory(self,
                                                      u'Выберите директорий для сохранения файла выгрузки',
                                                      forceStringEx(self.edtDirPath.text()),
                                                      QtGui.QFileDialog.ShowDirsOnly)
        if forceString(path):
            self.edtDirPath.setText(QDir.toNativeSeparators(path))
            self.btnExport.setEnabled(True)


    @pyqtSignature('QString')
    def on_edtDirPath_textChanged(self):
        dirPath = forceString(self.edtDirPath.text())
        filePathValid = os.path.exists(dirPath)
        self.btnExport.setEnabled(filePathValid)


    @pyqtSignature('')
    def on_btnAbort_clicked(self):
        self.abort = True


    def getQuery(self):
        stmt = u"""
               SELECT 
                    soc_spr74.KUSL,
                    rbService.name,
                    soc_spr74.PROF,
                    soc_spr74.PROFNAME,
                    soc_spr74.NGR,
                    soc_spr74.VID,
                    soc_spr74.METOD,
                    soc_spr74.MET_NAME,
                    soc_spr74.MODEL,
                    Client.lastName,
                    Client.firstName,
                    Client.patrName,
                    Event.externalId,
                    formatSNILS(Client.SNILS) AS SNILS,
                    Client.birthDate,
                    ClientDocument.serial,
                    ClientDocument.number,
                    Diagnosis.MKB,
                    Event.setDate,
                    Event.execDate,
                    Organisation.smoCode
                FROM Event
                      LEFT JOIN Action ON Event.id = Action.event_id AND Action.deleted = 0
                      LEFT JOIN ActionType ON Action.actionType_id = ActionType.id
                      LEFT JOIN EventType ON Event.eventType_id = EventType.id
                      LEFT JOIN rbMedicalAidType ON EventType.medicalAidType_id = rbMedicalAidType.id
                      LEFT JOIN rbService ON ActionType.nomenclativeService_id = rbService.id
                      LEFT JOIN soc_spr74 ON soc_spr74.KUSL = rbService.infis 
                        AND Event.execDate >= soc_spr74.DATN
                        AND (Event.execDate <= soc_spr74.DATO OR soc_spr74.DATO IS NULL)
                      LEFT JOIN Client ON Event.client_id = Client.id
                      LEFT JOIN ClientPolicy ON ClientPolicy.id = getClientPolicyIdForDate(Client.id, 1, Event.execDate, Event.id)
                      LEFT JOIN ClientDocument ON ClientDocument.id = getClientDocumentId(Client.id)
                      LEFT JOIN Diagnosis on Diagnosis.id = getEventDiagnosis(Event.id)
                      LEFT JOIN Organisation ON Organisation.id = ClientPolicy.insurer_id
                WHERE Client.deleted = 0
                AND Event.deleted = 0
                AND rbMedicalAidType.regionalCode IN ('401', '402')
                AND Event.execDate >= '{begDate}' AND Event.execDate < '{endDate}' + interval 1 day
                AND EXISTS (SELECT 1
                              FROM Action aTalon
                              LEFT JOIN ActionType atTalon ON aTalon.actionType_id = atTalon.id
                              LEFT JOIN ActionPropertyType aptTalon ON atTalon.id = aptTalon.actionType_id
                              LEFT JOIN ActionProperty apTalon ON apTalon.action_id = aTalon.id AND apTalon.type_id = aptTalon.id
                              LEFT JOIN ActionProperty_String apsTalon ON apsTalon.id = apTalon.id
                              WHERE aTalon.event_id = Event.id
                              AND aTalon.deleted = 0
                              AND atTalon.flatCode = 'VMPtalon' 
                              AND atTalon.deleted = 0
                              AND aptTalon.name = 'Номер талона'
                              AND (apTalon.id IS NULL 
                                   OR apTalon.deleted = 1 
                                   OR apsTalon.value IS NULL 
                                   OR apsTalon.value = '')
                            )
                AND rbService.infis LIKE 'V%';""".format(begDate=forceString(self.edtBegDate.date().toString('yyyy-MM-dd')), endDate=forceString(self.edtEndDate.date().toString('yyyy-MM-dd')))
        return self.db.query(stmt)


    @pyqtSignature('')
    def on_btnExport_clicked(self):
        self.logBrowser.clear()
        self.btnExport.setEnabled(False)
        self.abort=False
        self.progressBar.reset()
        self.progressBar.setMaximum(1)
        self.progressBar.setValue(0)
        self.btnAbort.setEnabled(True)
        QtGui.qApp.call(self, self.startExport)
        self.btnAbort.setEnabled(False)
        self.progressBar.setFormat(u'прервано' if self.abort else u'готово')
        self.btnExport.setEnabled(True)
        self.abort=False


    def startExport(self):
        query = self.getQuery()
        todayDateStr = unicode(QDate.currentDate().toString('dd.MM.yyyy'))
        workbook = xlwt.Workbook()
        pageNumber = 1
        sheet = workbook.add_sheet(u'ВТ ОМС %s %s' % (todayDateStr, pageNumber))

        def printHeader(sheet, rowNumber):
            sheet.col(0).width = int(256.0 * 3.29)
            sheet.col(1).width = int(256 * 16.29)
            sheet.col(2).width = int(256 * 22.29)
            sheet.col(3).width = int(256 * 59.29)
            sheet.col(4).width = int(256 * 19.29)
            sheet.col(5).width = int(256 * 8.43)
            sheet.col(6).width = int(256 * 9.29)
            sheet.col(7).width = int(256 * 10.29)
            sheet.col(8).width = 256 * 16
            sheet.col(9).width = int(256 * 6.29)
            sheet.col(10).width = int(256 * 13.29)
            sheet.col(11).width = int(256 * 8.71)
            sheet.col(12).width = int(256 * 10.29)

            style = xlwt.Style.easyxf(
                "align: horizontal center, wrap true, vertical center; font: bold true, name Times New Roman, height 220; borders: top thin, bottom thin, left thin, right thin;")
            sheet.write_merge(rowNumber, rowNumber, 0, 12, u'Список по ВТ ОМС для системы на %s' % todayDateStr,
                              style=style)
            rowNumber += 1
            sheet.write(rowNumber, 0, u'№', style=style)
            sheet.write(rowNumber, 1, u'Услуга', style=style)
            sheet.write(rowNumber, 2, u'Наименование услуги', style=style)
            sheet.write(rowNumber, 3, u'Профиль, группа, метод, модель', style=style)
            sheet.write(rowNumber, 4, u'ФИО', style=style)
            sheet.write(rowNumber, 5, u'№ карты', style=style)
            sheet.write(rowNumber, 6, u'СНИЛС', style=style)
            sheet.write(rowNumber, 7, u'Дата рождения', style=style)
            sheet.write(rowNumber, 8, u'Серия и № докум', style=style)
            sheet.write(rowNumber, 9, u'МКБ', style=style)
            sheet.write(rowNumber, 10, u'Дата начала / Дата окончания лечения', style=style)
            sheet.write(rowNumber, 11, u'Код СМО', style=style)
            sheet.write(rowNumber, 12, u'Дата формирования', style=style)

        rowsCount = query.size()
        rowNumber = 0
        if rowsCount and rowsCount > 0:
            self.progressBar.setMaximum(rowsCount)
            self.logBrowser.append(u'Найдено {rowCount} {eventString}.\nНачата запись в xls.'.format(rowCount=unicode(rowsCount), eventString= u'событие' if rowsCount==0 else u'событий(я)'))
            printHeader(sheet, rowNumber)
            rowNumber += 1
            styleMerged = xlwt.Style.easyxf(
                "align: horizontal center, vertical center, wrap true; font: name Times New Roman, height 220; borders: top thin, bottom thin, left thin, right thin;")
            styleUpper = xlwt.Style.easyxf(
                "align: horizontal left, vertical center, wrap true; font: name Times New Roman, height 220; borders: top thin, left thin, right thin;")
            styleCenter = xlwt.Style.easyxf(
                "align: horizontal left, vertical center, wrap true; font: name Times New Roman, height 220; borders: left thin, right thin;")
            styleDown = xlwt.Style.easyxf(
                "align: horizontal left, vertical center, wrap true; font: name Times New Roman, height 220; borders: bottom thin, left thin, right thin;")
            logRowCounter = 0
            while query.next():
                QtGui.qApp.processEvents()
                if self.abort:
                    self.logBrowser.append(u'Экспорт прерван пользователем!')
                    return
                record = query.record()
                rowNumber += 1
                logRowCounter += 1
                if rowNumber == 65536:
                    pageNumber += 1
                    sheet = workbook.add_sheet(u'ВТ ОМС %s %s' % (todayDateStr, pageNumber))
                    rowNumber = 0
                    printHeader(sheet, rowNumber)
                    rowNumber += 1

                prof = forceString(record.value('PROF')) + u' - ' + forceString(record.value('PROFNAME'))
                groupNumberAndVid = u'Группа - ' + forceString(record.value('NGR')) + u' Вид - ' + forceString(
                    record.value('VID'))
                methodAndMetName = u'Метод ' + forceString(record.value('METOD')) + u' Вид - ' + forceString(
                    record.value('MET_NAME'))
                model = u'Модель ' + forceString(record.value('MODEL'))

                # 1
                sheet.write_merge(rowNumber, rowNumber + 3, 0, 0, rowNumber, style=styleMerged)
                # 2
                sheet.write_merge(rowNumber, rowNumber + 3, 1, 1, forceString(record.value('KUSL')), style=styleMerged)
                # 3
                sheet.write_merge(rowNumber, rowNumber + 3, 2, 2, forceString(record.value('name')), style=styleMerged)
                # 4
                sheet.write_merge(rowNumber, rowNumber, 3, 3, prof, style=styleUpper)
                sheet.write_merge(rowNumber + 1, rowNumber + 1, 3, 3, groupNumberAndVid, style=styleCenter)
                sheet.write_merge(rowNumber + 2, rowNumber + 2, 3, 3, methodAndMetName, style=styleCenter)
                sheet.write_merge(rowNumber + 3, rowNumber + 3, 3, 3, model, style=styleDown)
                # 5
                sheet.write_merge(rowNumber, rowNumber, 4, 4, forceString(record.value('lastName')), style=styleUpper)
                sheet.write_merge(rowNumber + 1, rowNumber + 1, 4, 4, forceString(record.value('firstName')),
                                  style=styleCenter)
                sheet.write_merge(rowNumber + 2, rowNumber + 2, 4, 4, forceString(record.value('patrName')),
                                  style=styleCenter)
                sheet.write_merge(rowNumber + 3, rowNumber + 3, 4, 4, u'', style=styleDown)
                # 6
                sheet.write_merge(rowNumber, rowNumber + 3, 5, 5, forceString(record.value('externalId')),
                                  style=styleMerged)
                # 7
                sheet.write_merge(rowNumber, rowNumber + 3, 6, 6, forceString(record.value('SNILS')), style=styleMerged)
                # 8
                sheet.write_merge(rowNumber, rowNumber + 3, 7, 7, forceString(record.value('birthDate')), style=styleMerged)
                # 9
                sheet.write_merge(rowNumber, rowNumber, 8, 8, forceString(record.value('serial')), style=styleUpper)
                sheet.write_merge(rowNumber + 1, rowNumber + 1, 8, 8, forceString(record.value('number')),
                                  style=styleCenter)
                sheet.write_merge(rowNumber + 3, rowNumber + 3, 8, 8, u'', style=styleDown)
                # 10
                sheet.write_merge(rowNumber, rowNumber + 3, 9, 9, forceString(record.value('MKB')), style=styleMerged)
                # 11
                sheet.write_merge(rowNumber, rowNumber, 10, 10,
                                  unicode(forceDate(record.value('setDate')).toString('dd.MM.yyyy')), style=styleUpper)
                sheet.write_merge(rowNumber + 1, rowNumber + 1, 10, 10,
                                  unicode(forceDate(record.value('execDate')).toString('dd.MM.yyyy')), style=styleCenter)
                sheet.write_merge(rowNumber + 2, rowNumber + 2, 10, 10, u'', style=styleCenter)
                sheet.write_merge(rowNumber + 3, rowNumber + 3, 10, 10, u'', style=styleDown)
                # 12
                sheet.write_merge(rowNumber, rowNumber + 3, 11, 11, forceString(record.value('smoCode')), style=styleMerged)
                # 13
                sheet.write_merge(rowNumber, rowNumber, 12, 12, forceString(todayDateStr), style=styleUpper)
                sheet.write_merge(rowNumber + 1, rowNumber + 1, 12, 12,
                                  forceString(QTime().currentTime().toString('HH:mm:ss')), style=styleCenter)
                sheet.write_merge(rowNumber + 2, rowNumber + 2, 12, 12, u'', style=styleCenter)
                sheet.write_merge(rowNumber + 3, rowNumber + 3, 12, 12, u'', style=styleDown)

                rowNumber += 3

                self.logBrowser.append(u'Строка {row}: Информация по событию записана в файл.'.format(row=logRowCounter))
                self.progressBar.step()

            outDir = forceString(self.edtDirPath.text())
            fileName = os.path.join(forceStringEx(outDir),
                                    u"Список по ВТ ОМС на %s.xls" % QDate().fromString(todayDateStr, 'dd.MM.yyyy').toString(
                                        'dd_MM_yyyy'))
            if os.path.isfile(fileName):
                basePath = fileName.replace('.xls', '')
                counter = 1
                while True:
                    newName = u'{basePath} {counter}.xls'.format(basePath=basePath, counter=counter)
                    if not os.path.isfile(newName):
                        fileName = newName
                        break
                    counter += 1

            self.logBrowser.append(u'Сохранение .xls файла.')
            workbook.save(fileName)
        else:
            self.logBrowser.append(u'События не найдены.')
            return
