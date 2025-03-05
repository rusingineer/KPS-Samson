# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import json
#from base64      import b64encode

from uuid import uuid4

from PyQt4 import QtGui
from PyQt4 import QtSql
#from PyQt4.QtGui import QMessageBox
#from PyQt4.QtCore import Qt, QDate, , QVariant, pyqtSignature, SIGNAL
from PyQt4.QtCore import Qt, SIGNAL, pyqtSignature, QDateTime

from library.DialogBase          import CDialogBase
from library.InDocTable          import CInDocTableModel, CEnumInDocTableCol,  CInDocTableCol


#from library.crbcombobox         import CRBComboBox
#from library.InDocTable          import CDateInDocTableCol, CFloatInDocTableCol, CInDocTableCol, CRBInDocTableCol
from library.Identification      import findByIdentification
#from library.interchange         import setDatetimeEditValue, setLabelText, setLineEditValue
#from library.PrintInfo           import CInfoContext
#from library.PrintTemplates      import applyTemplate, CPrintAction, CPrintButton, getPrintTemplates
from library.Utils               import  agreeNumberAndWord, forceInt, forceString, forceDateTime, toVariant

#from Reports.ReportBase          import CReportBase, createTable
#from Reports.ReportView          import CReportViewDialog

#from Stock.Mdlp.Logger           import CLogger
#from Stock.Mdlp.Stage            import CMdlpStage
#from Stock.Mdlp.connection       import CMdlpConnection
#from Stock.Mdlp.iimProcess       import iimProcess
#from Stock.Mdlp.iiwdProcess      import iiwdProcess
#from Stock.Mdlp.iiwrProcess      import iiwrProcess
from Stock.NomenclatureComboBox     import CNomenclatureInDocTableCol

from Exchange.MDLP.RetReg import CRetReg, CRegisterMarksByRequisites

from Ui_DisposalOrder import Ui_DisposalOrderDialog

class CDisposalOrderEditDialog(Ui_DisposalOrderDialog, CDialogBase):
    doInitial = 0 # doSendedзапрос создаётся, orderId может быть пустым или заполнен
    doStored  = 1 # запрос создан, сохранён в БД, в случае асинхр. передачи - готов к передаче;
    doSended  = 2 # запрос передан в регистратор выбытия без ошибок; там wait или inProgress - не важно
    doOk      = 3 # регистратор выбытия ответил ready
    doError   = 4 # регистратор выбытия не принял запрос или ответил error

    def __init__(self,  parent):
        CDialogBase.__init__(self, parent)
#        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self.addModels('Items', CItemsModel(self))
        self.addObject('btnSave',     QtGui.QPushButton(u'Сохранить и продолжить набор', self))
        self.addObject('btnExchange', QtGui.QPushButton(u'Выполнить обмен', self))
        self.addObject('btnReset',    QtGui.QPushButton(u'Перезапуск', self))
        self.addObject('btnCloseAndStore',     QtGui.QPushButton(u'Закрыть и передать в накладную', self))
        self.addObject('btnCloseWithoutStore', QtGui.QPushButton(u'Закрыть просто так', self))

        self.setupUi(self)

        self.setModels(self.tblItems,  self.modelItems, self.selectionModelItems)
        self.tblItems.addPopupDelRow()

#        self.prepareItemsPopupMenu(self.tblItems)
#        self.tblItems.popupMenu().addSeparator()
#        self.tblItems.popupMenu().addAction(self.actOpenStockBatchEditor)
#        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        self.buttonBox.addButton(self.btnSave,              QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnExchange,          QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnReset,             QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnCloseAndStore,     QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnCloseWithoutStore, QtGui.QDialogButtonBox.ActionRole)

#        self.btnPrepareDispRequestToRegistrar.setEnabled(False)
#        self.buttonBox.addButton(self.btnSelectWithdrawalByRegisrar, QtGui.QDialogButtonBox.ActionRole)
#        self.btnSelectWithdrawalByRegisrar.setEnabled(False)
#        self.buttonBox.addButton(self.btnProductionEditDialog, QtGui.QDialogButtonBox.ActionRole)

        self.connect(QtGui.qApp, SIGNAL('Gs1BarcodeReceived(QByteArray, PyQt_PyObject)'), self.onGs1BarcodeReceived)

        self.record            = None
        self.orderId           = None
        self.baseInvoiceNumber = None
        self.baseInvoiceDate   = None
        self.rvRequestId       = ''
        self.mdlpRequestId     = ''
        self.status            = self.doInitial
        self.errorCode         = None
        self.errorDescr        = None


    def setAttrs(self, baseInvoiceNumber, baseInvoiceDate):
        orderId = self._findOrderId(baseInvoiceNumber, baseInvoiceDate)
        if orderId:
            self._load(orderId)
        else:
            self.setBaseInvoiceNumber(baseInvoiceNumber)
            self.setBaseInvoiceDate(baseInvoiceDate)
            self.setRvRequestId('')
            self.setMdlpRequestId('')
            self.setStatus(self.doInitial)


    def getSgtins(self):
        return self.modelItems.getSgtins()


    def _findOrderId(self, baseInvoiceNumber, baseInvoiceDate):
        db = QtGui.qApp.db
        table = db.table('DisposalOrder')
        cond = [ table['baseInvoiceNumber'].eq(baseInvoiceNumber),
                 table['baseInvoiceDate'].dateEq(baseInvoiceDate.date())
               ]
        ids = db.getIdList(table, where=cond, order='id', limit=1)
        return ids[0] if ids else None


    def _load(self, orderId):
        db = QtGui.qApp.db
        table = db.table('DisposalOrder')
        record = db.getRecord(table, '*', orderId)
        self.setBaseInvoiceNumber(forceString(record.value('baseInvoiceNumber')))
        self.setBaseInvoiceDate(forceDateTime(record.value('baseInvoiceDate')))
        self.setRvRequestId(forceString(record.value('rvRequestId')))
        self.setMdlpRequestId(forceString(record.value('mdlpRequestId')))
        self.setStatus(forceInt(record.value('status')),
                       forceInt(record.value('errorCode')) ,
                       forceString(record.value('errorDescr')) ,
                      )
        self.modelItems.loadItems(orderId)
        self.orderId = orderId
        self.record = record


    def _save(self, includeItems = True):
        db = QtGui.qApp.db
        now = QDateTime.currentDateTime()
        table = db.table('DisposalOrder')
        if self.record is None:
            record = table.newRecord()
            record.setValue('baseInvoiceNumber', self.baseInvoiceNumber)
            record.setValue('baseInvoiceDate',   self.baseInvoiceDate)
            record.setValue('createDatetime',    now)
            record.setValue('createPerson_id',   QtGui.qApp.userId)

        else:
            record = QtSql.QSqlRecord(self.record)
        record.setValue('rvRequestId',     self.rvRequestId)
        record.setValue('mdlpRequestId',   self.mdlpRequestId)
        record.setValue('status',          self.status)
        record.setValue('errorCode',       self.errorCode)
        record.setValue('errorDescr',      self.errorDescr)
        record.setValue('modifyDatetime',  now)
        record.setValue('modifyPerson_id', QtGui.qApp.userId)
        try:
            db.transaction()
            orderId = db.insertOrUpdate(table, record)
            if includeItems:
                self.modelItems.saveItems(orderId)
            db.commit()
            self.record = record
            self.orderId = orderId
        except:
            db.rollback()
            QtGui.qApp.logCurrentException()
            raise


    def _send(self):
        url, user, password = QtGui.qApp.getMdlpRetRegPres()
        retReg = CRetReg(url, user, password)
        doc = CRegisterMarksByRequisites(type_    = 0,
                                         code     = '0504204',
                                         codeName = u'Требование накладная',
                                         date     = self.baseInvoiceDate.toPyDateTime(),
                                         number   = self.baseInvoiceNumber,
                                         marks    = self.modelItems.getMarks()
                                        )
        resp = retReg.queueUp(self.rvRequestId, doc)
        return resp.status_code


    def _requestOrderStatus(self):
        url, user, password = QtGui.qApp.getMdlpRetRegPres()
        retReg = CRetReg(url, user, password)
        resp = retReg.requestStatus(self.rvRequestId)
        if resp.status_code == 200:
            return 200, resp.json()
        return resp.status_code, resp.text()


    def _setRvResult(self, orderResult):
        self.setMdlpRequestId(orderResult['mdlpRequestId'])
        self.modelItems.setMarkResults(orderResult['marks'])



    def setBaseInvoiceNumber(self, baseInvoiceNumber):
        self.baseInvoiceNumber = baseInvoiceNumber
        self.edtBaseInvoiceNumber.setText(baseInvoiceNumber)


    def setBaseInvoiceDate(self, baseInvoiceDate):
        self.baseInvoiceDate = baseInvoiceDate
        self.edtBaseInvoiceDate.setDate(baseInvoiceDate.date())
        self.edtBaseInvoiceTime.setTime(baseInvoiceDate.time())


    def setRvRequestId(self, rvRequestId):
        self.rvRequestId = rvRequestId
        self.lblRvRequestIdValue.setText(rvRequestId)


    def setMdlpRequestId(self, mdlpRequestId):
        self.mdlpRequestId = mdlpRequestId
        self.lblMdlpRequestIdValue.setText(mdlpRequestId)


    def setStatus(self, status, errorCode=0, errorDescr=''):
        self.status = status
        self.errorCode = errorCode
        self.errorDescr = errorDescr

 #       itemsEditable = False
        canSave = False
        canExchange = False
        canReset = False
        if status == self.doInitial:
            statusText = u'В процессе создания'
#            itemsEditable = True
            canSave = True
            canExchange = True
        elif status == self.doStored:
            statusText = u'Запрос создан'
            canExchange = True
        elif status == self.doSended:
            statusText = u'Запрос отправлен в регистратор выбытия'
            canExchange = True
        elif status == self.doOk:
            statusText = u'Запрос успешно отработан регистратором выбытия'
        elif status == self.doError:
            statusText = ''
            if errorCode:
                statusText += u' (%s)' % errorCode
            if errorDescr:
                statusText += u' ' + errorDescr
            if statusText:
                statusText = ':' + statusText
            statusText = u'Регистратр выбытия сообщает об ошибке' + statusText
            canReset = True
        else:
            statusText = u'Неизвестный статус {%s}' % status
        self.lblStatusValue.setText(statusText)
        self.tblItems.setPopupDelRowEnabled(status == self.doInitial)
        self.btnSave.setEnabled(canSave)
        self.btnExchange.setEnabled(canExchange and QtGui.qApp.isMdlpRetRegEnabled())
        self.btnReset.setEnabled(canReset)

#        self.btnClose.setEnabled(canClose)



    def onGs1BarcodeReceived(self, rawData, assocList):
        # bytes(rawData) -> '010405483902928821qqqqqqqqqqqqqqq\x1d91eeee\x1d92qqqqqqqqqqqqq='
        # [('01', '04054839029288'), ('21', 'qqqqqqqqqqqqqqq'), ('91', 'eeee'), ('92', 'qqqqqqqqqqqqq=')]
        assoc = dict(assocList)
        if not('01' in assoc and '21' in assoc):
            return
        sgtin = assoc['01'] + assoc['21']
        if self.status == self.doInitial:
            row = self.modelItems.findRowBySgtin(sgtin)
            if row is None:
                row = self.modelItems.addRow(sgtin, rawData)
            self.tblItems.setCurrentRow(row)
        else:
            row = self.modelItems.findRowBySgtin(sgtin)
            if row is not None:
                self.tblItems.setCurrentRow(row)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelItems_currentRowChanged(self, current, previous):
        statisticText = self.modelItems.getStatistic(current.row())
        self.lblSummaryInfo.setText(statisticText)


    @pyqtSignature('')
    def on_btnSave_clicked(self):
        self._save()


    @pyqtSignature('')
    def on_btnExchange_clicked(self):
        if self.status == self.doInitial:
            # мы закончили ввод и хотим передать запрос в регистратор выбытия.
            # во-первых - присваиваем (новый) rvRequestId,
            # во-вторых - сохраняем
            # в третьих - переводим в состояние Stored
            try:
                self.setRvRequestId(str(uuid4()))
                self.setStatus(self.doStored)
                self._save()
            except:
                self.setRvRequestId('')
                self.setStatus(self.doInitial)
        if self.status == self.doStored:
            # Мы закончили ввод и только что зафиксировали запрос в БД.
            # либо открыли форму - и обнаружили что данные ещё не переданы
            # во-первых пытаемcя передать; передача может быть совсем неуспешна или
            # закончиться 201 (ok), 409 (уже есть такой), и др.
            # если 201 или 409: переводим в состояние Sended,
            # иначе - Error
            code = self._send()
            if code in (201,  409):
                try:
                    self.setStatus(self.doSended)
                    self._save(includeItems=False)
                except:
                    self.setStatus(self.doStored)
            else:
                pass # ???

        if self.status == self.doSended:
            # Мы передали документ в регистратор выбытия (только что или в пред.сессию, неважно),
            # теперь нам нужно получить отзыв от регистраторы выбытия
            # если cтатус задания в регистраторе выбытия ready –
            # то заполняем спосок ответа по маркам и переводим запрос в состояние Ok
            # если cтатус задания в регистраторе выбытия error -
            # то переводим запрос в состояние Error
            # иначе - ничего не делаем, так как ответа пока нет
            try:
                httpCode, resp = self._requestOrderStatus()
                if httpCode == 200:
                    assert isinstance(resp, dict)
                    results = resp.get('results')
                    assert isinstance(results, dict) and 'status' in results
                    status = results.get('status')
                    if status == 'ready':
                        result = results.get('result')
                        assert isinstance(result, dict)
                        self._setRvResult(result)
                        self.setStatus(self.doOk)
                        self._save()
                    elif status == 'error':
                        error = results.get('error')
                        assert isinstance(error, dict) and 'code' in error and 'description' in error
                        errorCode = error['code']
                        errorDescription = error['description']
                        if errorCode == 5090:
                            errorDescriptionEx = CRetReg.explainErrorCode(errorDescription)
                            if errorDescriptionEx:
                                errorDescription = u'%s [%s]' % (errorDescription, errorDescriptionEx)

                        self.setStatus(self.doError,
                                       errorCode,
                                       errorDescription
                                      )
                        self._save(includeItems=False)
                    elif status == 'wait' or status == 'inProgress':
                        return
                    else:
                        self.setStatus(self.doError,
                                       httpCode,
                                       json.dumps(resp, ensure_ascii=False)
                                      )
                        self._save(includeItems=False)
                else:
                    self.setStatus(self.doError,
                                   httpCode,
                                   resp
                                  )
                    self._save(includeItems=False)

            except:
                assert False


    @pyqtSignature('')
    def on_btnReset_clicked(self):
        if self.status == self.doError:
            self.setStatus(self.doInitial)
            self.setRvRequestId('')
            self.setMdlpRequestId('')
            self.setMdlpRequestId('')


    @pyqtSignature('')
    def on_btnCloseAndStore_clicked(self):
#        self._save()
        self.accept()


    @pyqtSignature('')
    def on_btnCloseWithoutStore_clicked(self):
#        self._save()
        self.reject()


class CEnumInDocTableColEx(CEnumInDocTableCol):
    def toString(self, val, record):
        idx = forceInt(val)
        if idx is None or idx<0:
            return toVariant(None)
        if idx<len(self.values):
            return toVariant(self.values[idx])
        else:
            return toVariant('{%d}'%idx)


class CItemsModel(CInDocTableModel):
    Props             =   ( 'deviceError',
                            'flcError',
                            'localCheckStatus',
                            'onlineCheckError',
                            'onlineCheckStatus',
                            'state',
                          )

    DeviceErrors        = ( u'0–Нет ошибок',
                            u'1–Устройство недоступно',
                            u'2–Устройство не функционирует',
                            u'3–Отсутствует МБ РВ',
                            u'4–Истек срок использования МБ РВ',
                            u'5–МБ РВ блокирован',
                            u'6–МБ РВ не функционален',
                            u'7–РВ не зарегистрирован',
                            u'8–Отсутствует связь с СЭ',
                          )

    FlcErrors           = ( u'0–Нет ошибок',
                            u'1–Не допустимое значение идентификатора применения (GS AI) в КМ',
                            u'2–Не допустимые символы КМ',
                            u'3–Не допустимое количество символов в составе идентификатора применения (GS AI)',
                            u'4–Значение ТН ВЭД не относится к фармацевтической продукции',
                            u'5–Недопустимая последовательность групп в КМ',
                            u'6–Недопустимое значение доли от вторичной упаковки',
                          )

    LocalStatuses =       ( u'0–проверка не проводилась',
                            u'1–код маркировки проверен, достоверный',
                            u'2–код маркировки проверен, недостоверный',
                            u'3–проверка не проводилась',
                            u'4–проверка не проводилась',
                          )

    OnlineCheckStatuses = ( u'0–Прошла успешно',
                            u'1–Не проводилась',
                            u'2–Прошла не успешно',
                          )

    OnlineCheckErrors   = ( u'0–Статус успешно изменён',
                            u'1–КИЗ отсутствует в базе АС «Серверы СКЗКМ» или ИС МП',
                            u'2–Некорректный формат КИЗ',
                            u'3–Не прошла криптографическая проверка КПКИЗ',
                            u'4–КИЗ имеет в базе АС «Серверы СКЗКМ» статус не совместимый с запрашиваемым изменением',
                          )

    States              = ( u'',
                            u'1–Сформирован',
                            u'2–Готов',
                            u'3–Выдан',
                            u'4–Выпущен',
                            u'5–Не использован',
                            u'6–Упакован',
                            u'7–Распакован',
                            u'8–Выбыл',
                            u'9–Выбыл через розничную сеть',
                            u'10–В состоянии выбытия',
                            u'11–Утерян',
                            u'12–Оборот приостановлен',
                            u'13–Оборот запрещён',
                            u'14–Потреблён',
                            u'15–Дублирован',
                            u'16–Выбыл через оптовую сеть'
                          )

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'DisposalOrder_Item', 'id', 'master_id', parent)
        self.addCol(CNomenclatureInDocTableCol(u'ЛСиИМН', 'nomenclature_id', 50)).setReadOnly()
        self.addCol(CInDocTableCol(u'SGTIN', 'sgtin', 16)).setReadOnly()
        self.addCol(CEnumInDocTableColEx(u'Код ошибки РВ',             'deviceError',       20, self.DeviceErrors       )).setReadOnly()
        self.addCol(CEnumInDocTableColEx(u'Код ошибки ФЛК',            'flcError',          20, self.FlcErrors          )).setReadOnly()
        self.addCol(CEnumInDocTableColEx(u'Статус локальной проверки', 'localCheckStatus',  20, self.LocalStatuses      )).setReadOnly()
        self.addCol(CEnumInDocTableColEx(u'Код ошибки от сервера',     'onlineCheckError',  20, self.OnlineCheckErrors  )).setReadOnly()
        self.addCol(CEnumInDocTableColEx(u'Статус проверок сервером',  'onlineCheckStatus', 20, self.OnlineCheckStatuses)).setReadOnly()
        self.addCol(CEnumInDocTableColEx(u'Статус кода маркировки',    'state',             20, self.States             )).setReadOnly()

        self.addHiddenCol('mark')
        self.addHiddenCol('json')
        self.setEnableAppendLine(False)


    def getStatistic(self, currentRow):
        cnt = self.rowCount()
        if cnt == 0:
            result = u'Список пуст'
        else:
            result = u'В списке %d %s' % ( cnt,
                                           agreeNumberAndWord(cnt, (u'позиция',  u'позиции',  u'позиций'))
                                         )
            if currentRow>=0:
                currentGtin = forceString(self.value(currentRow, 'sgtin'))[:14]
                currentName = forceString(self.data(self.index(currentRow, 0),  Qt.DisplayRole))
                gtinCount = 0
                for item in self.items():
                    itemGtin = forceString(item.value('sgtin'))[:14]
                    if currentGtin == itemGtin:
                        gtinCount += 1
                result += u', в т.ч. %d %s «%s»' % ( gtinCount,
                                                     agreeNumberAndWord(gtinCount, (u'упаковка',  u'упаковки',  u'упаковок')),
                                                     currentName or currentGtin
                                                   )
        return result

    def getEmptyRecord(self):
        record = CInDocTableModel.getEmptyRecord(self)
        for prop in self.Props:
            record.setValue(prop, -1)
        return record


    def findRowBySgtin(self, sgtin):
        for row, item in enumerate(self.items()):
            if forceString(item.value('sgtin')) == sgtin:
                return row
        return None


    def addRow(self, sgtin, mark):
        gtin = sgtin[:14]
        nomenclatureId = findByIdentification('rbNomenclature', 'urn:gtin', gtin, raiseIfNonFound=False)

        record = self.getEmptyRecord()
        record.setValue('nomenclature_id', nomenclatureId)
        record.setValue('sgtin', sgtin)
        record.setValue('mark',  mark)
        row = self.rowCount()
        self.addRecord(record)
        return row


    def getMarks(self):
        result = {}
        for item in self.items():
            sgtin = forceString(item.value('sgtin'))
            mark  = forceString(item.value('mark'))
            result[sgtin] = mark
        return result


    def setMarkResults(self, markResults):
        for item in self.items():
            sgtin = forceString(item.value('sgtin'))
            markResult = markResults.get(sgtin)
            if markResult:
                for prop in self.Props:
                    item.setValue(prop, markResult.get(prop, -1))
                item.setValue('json', json.dumps(markResult, ensure_ascii=False))


    def cleanMarkResults(self):
        for item in self.items():
            for prop in self.Props:
                    item.setValue(prop, -1)
            item.setValue('json', '')


    def getSgtins(self):
        result = []
        for item in self.items():
            sgtin = forceString(item.value('sgtin'))
            result.append(sgtin)
        return result
