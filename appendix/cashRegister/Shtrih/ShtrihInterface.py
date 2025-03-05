# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2017-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from library.Utils import forceBool, forceInt, forceString
from fr_drv_ng     import ClassicInterface
from ShtrihErrors  import EShtrihError


class CShtrihInterface:
    tagPayerContact  = 1008 # Электронный адрес / телефон получателя
    tagPayerName     = 1227 # Наименование получателя

    #tagAddress       = 1009
    tagOperatorName  = 1021
    tagOperatorVatin = 1203

    tagPaymentObject = 1212 # Признак предмета расчета (тег 1212)
    tagPaymentMethod = 1214 # Признак способа рaсчета (тег 1214)


    # состояние смены
    ssClosed     = 0 # смена не открыта
    ssOpen       = 1 # смена открыта - и готова к работе
    ssExpired    = 2 # смена открыта - и не готова к работе (просрочена)

    # Типы чеков
    rtSell           = 0
    rtSellReturn     = 2

    # Отображение типа чека из OpenCheck в значение для ФН методов
    mapOcToFn        = { 0: 1,  # продажа/приход
                         1: 3,  # покупка/расход
                         2: 2,  # возврат продажи/возврат прихода
                         3: 4,  # возврат покупки/возврат расхода
                       }

    # Типы оплаты
    ptCash           = 1
    ptCard           = 2

    # Признак предмета расчета (тег 1212)
    poCommodity      = 1 # «ТОВАР»
#    poExcise         = 2 # «ПОДАКЦИЗНЫЙ ТОВАР»
#    poJob            = 3 # «РАБОТА»
    poService        = 4 # «УСЛУГА»
    # Этих признаков много - 26 разных кодов, но нам достаточно услуги.

    # Признак способа рaсчета (тег 1214)
    pmFullPrepayment = 1 # Полная предварительная оплата до момента передачи предмета расчета. «ПРЕДОПЛАТА 100%»
    pmPrepayment     = 2 # Частичная предварительная оплата до момента передачи предмета расчета. «ПРЕДОПЛАТА»
    pmAdvance        = 3 # Аванс. «АВАНС»
    pmFullPayment    = 4 # Полная оплата, в том числе с учетом аванса (предварительной оплаты) в момент передачи предмета расчета. «ПОЛНЫЙ РАСЧЕТ»
    pmPartialPayment = 5 # Частичная оплата предмета расчета в момент его передачи с последующей оплатой в кредит. «ЧАСТИЧНЫЙ РАСЧЕТ»
    pmCredit         = 6 # Передача предмета расчета без его оплаты в момент его передачи с последующей оплатой в кредит. «ПЕРЕДАЧА В КРЕДИТ»
    pmCreditPayment  = 7 # Оплата предмета расчета после его передачи с оплатой в кредит (оплата кредита). «ОПЛАТА КРЕДИТА»

    MMU = 0.01 # Минимальная денежная единица

    vatNone   = 4 # без НДС
    vat0      = 3 # НДС 0%
    vat110    = 6 # НДС 10/110
    vat120    = 5 # НДС 20/120
    vatInvaid = 0 # ?


    def __init__(self):
        try:
            self.ci = ClassicInterface()
        except:
            self.ci = None

        self.operatorName  = '' # ФИО оператора
        self.operatorVatin = '' # ИНН оператора
        self.vatTaxPayer   = False
        self.operatorPassword = 1  # называется - пароль. на самом деле номер в таблице :(
        self.sysAdminPassword = 30

        self._checkType   = None # FNOperation не довольствуется CheckType из OpenCheck
        self._paymentType = None # Тип и сумма передаются в pay, а используются в closeReceipt: это пряталка
        self._paymentSum  = None


    def setOperatorName(self, name):
        self.operatorName = name


    def setOperatorVatin(self, vatin):
        self.operatorVatin = vatin


    @classmethod
    def __toMonetaryUnit(cls, sum_):
        return int(round(sum_/cls.MMU))


    @classmethod
    def __fromMonetaryUnit(cls, sum_):
        return sum_*cls.MMU


    def __encodeVat(self, valPercent):
        if self.vatTaxPayer:
            v = int(round(valPercent))
            if v == 20:
                return self.vat120 # НДС 20/120
            elif v == 10:
                return self.vat110 # НДС 10/110
            elif v == 0:
                return self.vat100 #  НДС 0/100
            else:
                return self.vatInvaid
        else:
            return self.vatNone

    def __checkError(self, rc):
        if rc:
            message = self.ci.ResultCodeDescription
            # print rc, message
            raise EShtrihError(rc, message)


    def __checkDocumentClosed(self):
        self.__checkError(self.ci.GetECRStatus())
        mode = self.ci.ECRMode
        if mode == self.ci.PM_OpenedDocument:
            self.ci.Password = self.sysAdminPassword
            self.__checkError(self.ci.SysAdminCancelCheck())
        self.__checkError(self.ci.WaitForPrinting())


    def __setOperatorTags(self):
#        self.ci.Password = self.operatorPassword
        if self.operatorName:
            self.ci.TagNumber = self.tagOperatorName
            self.ci.TagType   = self.ci.TT_String
            self.ci.TagValueStr = self.operatorName
            self.__checkError(self.ci.FNSendTag())
        if self.operatorVatin:
            self.ci.TagNumber = self.tagOperatorVatin
            self.ci.TagType   = self.ci.TT_String
            self.ci.TagValueStr = self.operatorVatin
            self.__checkError(self.ci.FNSendTag())


    def __operatorLogin(self):
#        self.__checkError(self.ci.WaitForPrinting())
        self.__checkError(self.ci.GetECRStatus())
        mode = self.ci.ECRMode
        if mode == self.ci.PM_SessionOpenOver24h:
            self.ci.Password = self.sysAdminPassword
            self.__checkError(self.ci.FNBeginCloseSession())
            self.__setOperatorTags()
            self.__checkError(self.ci.PrintReportWithCleaning())
            self.__checkError(self.ci.WaitForPrinting())
            self.ci.Password = self.sysAdminPassword
            self.__checkError(self.ci.FNBeginOpenSession())
            self.ci.Password = self.operatorPassword
            self.__setOperatorTags()
            self.__checkError(self.ci.FNOpenSession())
        elif mode == self.ci.PM_SessionClosed:
            self.ci.Password = self.sysAdminPassword
            self.__checkError(self.ci.FNBeginOpenSession())
            self.ci.Password = self.operatorPassword
            self.__setOperatorTags()
            self.__checkError(self.ci.FNOpenSession())
        elif mode == self.ci.PM_OpenedDocument:
            self.ci.Password = self.sysAdminPassword
            self.__checkError(self.ci.SysAdminCancelCheck())
            self.__checkError(self.ci.WaitForPrinting())
            self.ci.Password = self.operatorPassword


    def setup(self, options):
        self.vatTaxPayer = forceBool(options.get('vatTaxPayer', False))
        self.operatorPassword = forceInt(options.get('operatorPassword', 0)) or 1
        self.sysAdminPassword = forceInt(options.get('sysAdminPassword', 0)) or 30

        link = forceString(options.get('link'))
        if link == 'serial port':
            params = { 'port'     : forceString(options.get('serialPort', 'COM1')),
                       'baudrate' : forceInt(options.get('serialBaudrate', 38400)),
                       'timeout'  : 20000
                     }
            uri = 'serial://%(port)s?baudrate=%(baudrate)d&timeout=%(timeout)d' % params
        elif options['link'] == 'tcp/ip':
            params = { 'host'     : forceString(options.get('tcpIpHost', '127.0.0.1')),
                       'port'     : forceInt(options.get('tcpIpPort', 7778)),
                       'timeout'  : 30000
                     }
            uri = 'tcp://%(host)s:%(port)d?timeout=%(timeout)d' % params
        elif options['link'] == 'bluetooth':
            params = { 'mac'      : forceString(options.get('bluetoothMacAddress', '000000000000')),
                       'timeout'  : 30000
                     }
            uri = 'btserial://%(mac)s?timeout=%(timeout)d' % params
        else: # usb
            params = { 'timeout'  : 10000
                     }
            uri = 'cdcacm://shtrihfr?timeout=%(timeout)d' % params
        if self.ci:
            self.ci.ConnectionURI = uri


    def driverLoaded(self):
        return bool(self.ci)


    def open(self):
        if self.ci:
            self.__checkError(self.ci.Connect())
            self.ci.Password = self.operatorPassword
            self.ci.SysAdminPassword = self.sysAdminPassword


    def close(self):
        if self.ci:
            self.__checkError(self.ci.Disconnect())


    def isOpen(self):
        if self.ci:
            return self.ci.Connected
        else:
            return False


    def getModelInfo(self):
        # GetECRStatus()
        modelName       = self.ci.UDescription
        firmwareVersion = self.ci.ECRSoftVersion
        build           = self.ci.ECRBuild
        return { #'model'   : model,
                 'name'    : modelName,
                 'version' : '%s %d' %(firmwareVersion, build)
               }


    def getFactoryNumber(self):
        self.ci.Password = self.operatorPassword
#        self.ci.Password = 30
        self.ci.TableNumber = 18
        self.ci.RowNumber = 1
        self.ci.FieldNumber = 1
        self.__checkError(self.ci.ReadTable())
        return self.ci.ValueOfFieldString


    def getOfdExchangeStatus(self):
#    Password - пароль системного администратора.
        self.ci.Password = self.sysAdminPassword
        self.__checkError(self.ci.FNGetInfoExchangeStatus())
        exchangeStatus = self.ci.InfoExchangeStatus
        unsentCount = self.ci.MessageCount
        firstUnsentNumber = self.ci.DocumentNumber
        firstUnsentDateTime = self.ci.Date

        return { 'unsentCount'         : unsentCount,
                 'firstUnsentNumber'   : firstUnsentNumber,
                 'firstUnsentdateTime' : firstUnsentDateTime,

                 'connected'           : bool(exchangeStatus & (1<<0)), # Бит 0 – транспортное соединение установлено
                 'queueIsNotEmpty'     : bool(exchangeStatus & (1<<1)), # Бит 1 – есть сообщение для передачи в ОФД
                 # Бит 2 – ожидание ответного сообщения (квитанции) от ОФД
                 # Бит 3 – есть команда от ОФД
                 # Бит 4 – изменились настройки соединения с ОФД
               }


    def openSession(self):
        self.__operatorLogin()


    def getSessionState(self):
        self.__checkError(self.ci.GetECRStatus())
        mode = self.ci.ECRMode
        if mode == self.ci.PM_SessionClosed:
            state = self.ssClosed
        elif mode == self.ci.PM_SessionOpenOver24h:
            state = self.ssExpired
        else:
            state = self.ssOpen

        return { 'state': state,
#                 'date' : self._decodeDate(resp[1:4][::-1]),
#                 'time' : self._decodeTime(resp[4:7]),
               }


    def getSessionInfo(self):
        self.ci.Password = self.operatorPassword
        self.__checkError(self.ci.GetECRStatus())
        #self.__checkError(self.ci.FNGetCurrentSessionParams())
        sessionNumber = self.ci.SessionNumber
        #receiptNumber = self.ci.ReceiptNumber
        receiptNumber = self.ci.OpenDocumentNumber
        return { 'sessionNumber' : sessionNumber,
                 'receiptNumber' : receiptNumber,
               }


    def closeSession(self):
        self.__checkError(self.ci.FNBeginCloseSession())
        self.__setOperatorTags()
        self.__checkError(self.ci.PrintReportWithCleaning())
        self.__checkError(self.ci.WaitForPrinting())


    def openReceipt(self,
                    receiptType,
                    payerName=None,
                    payerEmail=None,
                    printReceipt=True,
                    customAttrName=None,
                    customAttrValue=None):
        self.__operatorLogin()
        self.ci.Password = self.operatorPassword
        if payerName:
            self.ci.TagNumber   = self.tagPayerName
            self.ci.TagType     = self.ci.TT_String
            self.ci.TagValueStr = payerName
            self.ci.FNSendTag()
        if payerEmail:
#            self.ci.TagNumber   = self.tagPayerContact
#            self.ci.TagType     = self.ci.TT_String
#            self.ci.TagValueStr = payerEmail
#            self.ci.FNSendTag()
            self.ci.CustomerEmail = payerEmail
            self.ci.FNSendCustomerEmail()

        if customAttrName and customAttrValue:
            self.ci.TagNumber   = 1084
            self.ci.FNBeginSTLVTag()
            self.ci.TagNumber   = 1085
            self.ci.TagType     = self.ci.TT_String
            self.ci.TagValueStr = customAttrName
            self.ci.FNAddTag()
            self.ci.TagNumber   = 1086
            self.ci.TagType     = self.ci.TT_String
            self.ci.TagValueStr = customAttrValue
            self.ci.FNAddTag()
            self.ci.FNSendSTLVTag()

        self.ci.CheckType = receiptType
        self._checkType = receiptType
        self.ci.SkipPrint = not printReceipt
        self.__checkError(self.ci.OpenCheck())
        self.__setOperatorTags()


    def cancelReceipt(self):
        self.ci.Password = self.operatorPassword
        self.__checkError(self.ci.CancelCheck())


    def closeReceipt(self):
        # Метод производит закрытие чека комбинированным типом оплаты с вычислением налогов и суммы сдачи.
        # Перед вызовом метода в свойстве Password указать пароль оператора и заполнить перечисленные в таблице используемые свойства.
        # В свойстве OperatorNumber возвращается порядковый номер оператора, чей пароль был введен.
        # В свойстве Change возвращается сумма сдачи.
        self.ci.Password = self.operatorPassword
        self.ci.Summ1  = 0
        self.ci.Summ2  = 0
        self.ci.Summ3  = 0
        self.ci.Summ4  = 0
        self.ci.Summ5  = 0
        self.ci.Summ6  = 0
        self.ci.Summ7  = 0
        self.ci.Summ8  = 0
        self.ci.Summ9  = 0
        self.ci.Summ10 = 0
        self.ci.Summ11 = 0
        self.ci.Summ12 = 0
        self.ci.Summ13 = 0
        self.ci.Summ14 = 0
        self.ci.Summ15 = 0
        self.ci.Summ16 = 0
        self.ci.RoundingSumm = 0 # Сумма округления
        self.ci.TaxValue1 = 0 # Налоги мы не считаем
        self.ci.TaxValue2 = 0
        self.ci.TaxValue3 = 0
        self.ci.TaxValue4 = 0
        self.ci.TaxValue5 = 0
        self.ci.TaxValue6 = 0
        self.ci.TaxType = 1 # Основная система налогообложения
        self.ci.StringForPrinting = ''

        if self._paymentType == self.ptCash:
            self.ci.Summ1 = self.__toMonetaryUnit(self._paymentSum) # Наличные
        else:
            self.ci.Summ2 = self.__toMonetaryUnit(self._paymentSum) # Картой (МИР?)

        self.__checkError(self.ci.FNCloseCheckEx())
        self.__checkError(self.ci.WaitForPrinting())
        self.__checkDocumentClosed()


    def isReceiptOpen(self):
        self.__checkError(self.ci.GetECRStatus())
        return self.ci.ECRMode == self.ci.PM_OpenedDocument


#    def getReceiptState(self):
#        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_RECEIPT_STATE)
#        self.__checkError(self.fptr.queryData())
#
#        receiptType     = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE)
#        receiptNumber   = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_NUMBER)
#        documentNumber  = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)
#        return { 'type'          : receiptType,
#                 'receiptNumber' : receiptNumber,
#                 'docNumber'     : documentNumber,
#               }


    def register(self,
                 name,
                 price,
                 quantity,
                 sum_,
                 vatPercent=0,
                 section=0,
                 paymentObject=poService,     # 4, # poService
                 paymentMethod=pmFullPayment, # 4, # pmFullPayment
                 checkCache=True):
        if sum_ == 0 and price != 0:
            sum_ = round(price*quantity, 2)
        elif sum_ != 0 and price == 0 and quantity != 0:
            price = round(sum_/quantity, 2)
        self.ci.CheckType         = self.mapOcToFn[self._checkType]
        self.ci.StringForPrinting = name
        self.ci.Price             = self.__toMonetaryUnit(price)
        self.ci.Quantity          = quantity
        self.ci.MeasureUnit       = self.ci.MU_Item             # Мера количества предмета расчета
        self.ci.Summ1Enabled      = True                        # Указываем, что сами рассчитываем цену
        self.ci.Summ1             = self.__toMonetaryUnit(sum_) # Сумма позиции с учетом скидок
        self.ci.TaxValueEnabled   = False                       # Налог мы не рассчитываем, типа считает само
        self.ci.Tax1              = self.__encodeVat(vatPercent)
        self.ci.Department        = section                     # Номер отдела
        self.ci.PaymentItemSign   = paymentObject               # Признак предмета расчета (тег 1212)
        self.ci.PaymentTypeSign   = paymentMethod               # Признак способа рaсчета (тег 1214)
        self.__checkError(self.ci.FNOperation())
#        self.__checkError(self.ci.Sale())


    def pay(self, paymentType, sum_):
        self._paymentType = paymentType
        self._paymentSum  = sum_


    def getCash(self):
        self.ci.Password = self.operatorPassword
        self.__checkError(self.ci.ReadCashDrawerSum())
        return self.__fromMonetaryUnit(self.ci.Summ1)


    def putToCash(self, sum_):
        self.ci.Password = self.operatorPassword
#        self.__operatorLogin()
        self.ci.Summ1 = self.__toMonetaryUnit(sum_)
        self.__checkError(self.ci.CashIncome())


    def takeFromCash(self, sum_):
        self.ci.Password = self.operatorPassword
#        self.__operatorLogin()
        self.ci.Summ1 = self.__toMonetaryUnit(sum_)
        self.__checkError(self.ci.CashOutcome())


    # Команды печати
    def printText(self, text):
        self.ci.StringForPrinting = text
        self.ci.PrintString()


    def printLastDocument(self):
        self.__operatorLogin()
        self.ci.Password = self.operatorPassword
        self.__checkError(self.ci.RepeatDocument())
        self.__checkError(self.ci.WaitForPrinting())
        self.__checkDocumentClosed()


    # Команды управления
    def cutReceipt(self, partialy=False):
        self.ci.CutType = partialy # тип отрезки (TRUE – неполная отрезка, FALSE – полная отрезка)
        self.ci.CutCheck()


    def beep(self):
        self.ci.Beep()


#?    def sound(self, freq, duration):
#        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FREQUENCY, freq)
#        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DURATION, duration*1000)
#        self.fptr.beep()


    def reportX(self):
        self.ci.Password = self.sysAdminPassword # self.operatorPassword
        self.__checkError(self.ci.PrintReportWithoutCleaning())
        self.__checkError(self.ci.WaitForPrinting())
        self.__checkDocumentClosed()


    def reportLastDocument(self):
        self.ci.Password = self.operatorPassword
        self.__checkError(self.ci.RepeatDocument())
        self.__checkError(self.ci.WaitForPrinting())
        self.__checkDocumentClosed()


    def reportOfdExchangeStatus(self):
        self.ci.Password = self.sysAdminPassword
        self.__checkError(self.ci.FNBeginCalculationStateReport())
        self.__setOperatorTags()
        self.__checkError(self.ci.FNBuildCalculationStateReport())
#        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_OFD_EXCHANGE_STATUS)
#        self.fptr.report()
        self.__checkError(self.ci.WaitForPrinting())
        self.__checkDocumentClosed()


    def reportQuantity(self):
        self.ci.Password = self.sysAdminPassword
        self.__checkError(self.ci.PrintWareReport())
        self.__checkError(self.ci.WaitForPrinting())
        self.__checkDocumentClosed()


    def reportOperators(self):
        self.ci.Password = self.sysAdminPassword
        self.__checkError(self.ci.PrintCashierReport())
        self.__checkError(self.ci.WaitForPrinting())
        self.__checkDocumentClosed()


    def reportHours(self):
        self.ci.Password = self.sysAdminPassword
        self.__checkError(self.ci.PrintHourlyReport())
        self.__checkError(self.ci.WaitForPrinting())
        self.__checkDocumentClosed()

# Следующие методы не реализованы, так как
# во-первых я затрудняюсь найти их прямые аналоги
# и во-вторых - я не уверен что они действительно необходимы

#    def reportShiftTotalCounters(self):
##        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_FN_SHIFT_TOTAL_COUNTERS)
##        self.fptr.report()


#    def reportFnTotalCounters(self):
##        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_FN_TOTAL_COUNTERS)
##        self.fptr.report()


#    def reportOfdTest(self):
##       self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_OFD_TEST)
##       self.fptr.report()


#    def reportCashRegisterInfo(self):
#        self.ci.Password = self.sysAdminPassword
#        self.__checkError(self.ci.FNBeginRegistrationReport())
#        self.__checkError(self.ci.FNBuildRegistrationReport())
#        self.__checkError(self.ci.WaitForPrinting())
#        self.__checkDocumentClosed()


#    def reportRegistration(self):
#        self.ci.Password = self.sysAdminPassword
#        self.__checkError(self.ci.FNBeginRegistrationReport())
#        self.__checkError(self.ci.FNBuildRegistrationReport())
#        self.__checkError(self.ci.WaitForPrinting())
#        self.__checkDocumentClosed()
##        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_FN_REGISTRATIONS)
##        self.fptr.report()



#    def printDocumentByNumber(self, number) - может быть полезно, не реализовано.
