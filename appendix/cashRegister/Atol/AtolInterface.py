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

import time

from libfptr10 import IFptr

from library.Utils import ( forceBool, forceInt, forceString )

from AtolErrors import EAtolError


class CAtolInterface:
    tagPayerContact  = 1008 # Электронный адрес / телефон получателя
    tagPayerName     = 1227 # Наименование покупателя (плательщика) для ФФД < 1.2: реквизит чека, для ФФД ≥ 1.2: входит в 1256
    tagPayerInfo     = 1256 # Сведения о покупателе (плательщике), ФФД ≥ 1.2

    #tagAddress       = 1009
    tagOperatorName  = 1021
    tagOperatorVatin = 1203

    tagFfdVersion    = 1209 # Номер версии ФФД (int) IFptr.LIBFPTR_FFD_UNKNOWN = 0, IFptr.LIBFPTR_FFD_1_0 = 100, IFptr.LIBFPTR_FFD_1_0_5 = 105, IFptr.LIBFPTR_FFD_1_1 = 110, IFptr.LIBFPTR_FFD_1_2 = 120
    tagPaymentObject = 1212 # Признак предмета расчета (тег 1212)
    tagPaymentMethod = 1214 # Признак способа рaсчета (тег 1214)


    # состояние смены
    ssClosed     = IFptr.LIBFPTR_SS_CLOSED  # смена не открыта
    ssOpen       = IFptr.LIBFPTR_SS_OPENED  # смена открыта - и готова к работе
    ssExpired    = IFptr.LIBFPTR_SS_EXPIRED # смена открыта - и не готова к работе (просрочена)

    # Типы чеков
    rtSell           = IFptr.LIBFPTR_RT_SELL
    rtSellReturn     = IFptr.LIBFPTR_RT_SELL_RETURN

    # Типы оплаты
    ptCash           = IFptr.LIBFPTR_PT_CASH
    ptCard           = IFptr.LIBFPTR_PT_ELECTRONICALLY


    # версии ффд (определяем по тегу 1209)
    ffdUnknown = IFptr.LIBFPTR_FFD_UNKNOWN # = 0
    ffd100     = IFptr.LIBFPTR_FFD_1_0   # = 100
    ffd105     = IFptr.LIBFPTR_FFD_1_0_5 # = 105
    ffd110     = IFptr.LIBFPTR_FFD_1_1   # = 110
    ffd120     = IFptr.LIBFPTR_FFD_1_2   # = 120

    # Признак предмета расчета (передаём в теге 1212)
    poCommodity      = 1 # «ТОВАР»
#    poExcise         = 2 # «ПОДАКЦИЗНЫЙ ТОВАР»
#    poJob            = 3 # «РАБОТА»
    poService        = 4 # «УСЛУГА»
    # Этих признаков много - 26 разных кодов, но нам достаточно услуги.

    # Признак способа рaсчета (передаём в теге 1214)
    pmFullPrepayment = 1 # Полная предварительная оплата до момента передачи предмета расчета. «ПРЕДОПЛАТА 100%»
    pmPrepayment     = 2 # Частичная предварительная оплата до момента передачи предмета расчета. «ПРЕДОПЛАТА»
    pmAdvance        = 3 # Аванс. «АВАНС»
    pmFullPayment    = 4 # Полная оплата, в том числе с учетом аванса (предварительной оплаты) в момент передачи предмета расчета. «ПОЛНЫЙ РАСЧЕТ» 
    pmPartialPayment = 5 # Частичная оплата предмета расчета в момент его передачи с последующей оплатой в кредит. «ЧАСТИЧНЫЙ РАСЧЕТ» 
    pmCredit         = 6 # Передача предмета расчета без его оплаты в момент его передачи с последующей оплатой в кредит. «ПЕРЕДАЧА В КРЕДИТ» 
    pmCreditPayment  = 7 # Оплата предмета расчета после его передачи с оплатой в кредит (оплата кредита). «ОПЛАТА КРЕДИТА» 


    def __init__(self):
        try:
            self.fptr = IFptr()
        except:
            self.fptr = None

        self._operatorName  = '' # ФИО оператора
        self._operatorVatin = '' # ИНН оператора
        self._vatTaxPayer   = False
        self._ffdVersion    = None


    def setOperatorName(self, name):
        self._operatorName = name


    def setOperatorVatin(self, vatin):
        self._operatorVatin = vatin


    def __checkError(self, rc):
        if rc != 0:
            code = self.fptr.errorCode()
            message = self.fptr.errorDescription()
            # print rc, code, message
            raise EAtolError(code, message)


    def __checkDocumentClosed(self):
        t = 20
        rc = 0
        while t>0:
            rc = self.fptr.checkDocumentClosed()
            if rc==0:
                break
            time.sleep(0.1)
            t -= 1
        self.__checkError(rc)

        if not self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_CLOSED):
            raise EAtolError(0x10000, u'Документ не закрылся. Попробуйте ещё раз')

        if not self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_PRINTED):
            t = 30
            while True:
                rc = self.fptr.continuePrint()
                if rc==0:
                    break
                time.sleep(0.1)
                t -= 1
            self.__checkError(rc)


    def __encodeVat(self, valPercent):
        if self._vatTaxPayer:
            v = int(round(valPercent))
            if v == 20:
                return IFptr.LIBFPTR_TAX_VAT120
            elif v == 10:
                return IFptr.LIBFPTR_TAX_VAT110
            elif v == 0:
                return IFptr.LIBFPTR_TAX_VAT0
            else:
                return IFptr.LIBFPTR_TAX_INVALID
        else:
            return IFptr.LIBFPTR_TAX_NO



    def __operatorLogin(self):
        if self._operatorName or self._operatorVatin:
            if self._operatorName:
                self.fptr.setParam(self.tagOperatorName, self._operatorName)
            if self._operatorVatin:
                self.fptr.setParam(self.tagOperatorVatin, self._operatorVatin)
            self.__checkError(self.fptr.operatorLogin())


    def __queryRegistrationInfo(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_REG_INFO)
        self.fptr.fnQueryData()

#        self._taxationTypes  = self.fptr.getParamInt(1062)
        self._ffdVersion  = self.fptr.getParamInt(self.tagFfdVersion)


    def setup(self, options):
        self._vatTaxPayer = forceBool(options.get('vatTaxPayer', False))
        link = forceString(options.get('link'))
        settings = {}
        settings[IFptr.LIBFPTR_SETTING_MODEL] = IFptr.LIBFPTR_MODEL_ATOL_AUTO
        settings[IFptr.LIBFPTR_SETTING_ACCESS_PASSWORD] = forceString(options.get('password', ''))
        settings[IFptr.LIBFPTR_SETTING_USER_PASSWORD] = forceString(options.get('operatorPassword', ''))
        settings[IFptr.LIBFPTR_SETTING_OFD_CHANNEL] = IFptr.LIBFPTR_OFD_CHANNEL_AUTO
        if link == 'serial port':
            settings[IFptr.LIBFPTR_SETTING_PORT]       = IFptr.LIBFPTR_PORT_COM
            settings[IFptr.LIBFPTR_SETTING_COM_FILE]   = forceString( options.get('serialPort', '') )
            settings[IFptr.LIBFPTR_SETTING_BAUDRATE]   = forceInt( options.get('serialBaudrate', 19200) )
            settings[IFptr.LIBFPTR_SETTING_BITS]       = IFptr.LIBFPTR_PORT_BITS_8
            settings[IFptr.LIBFPTR_SETTING_STOPBITS]   = IFptr.LIBFPTR_PORT_SB_1
            settings[IFptr.LIBFPTR_SETTING_PARITY]     = IFptr.LIBFPTR_PORT_PARITY_NO
        elif options['link'] == 'tcp/ip':
            settings[IFptr.LIBFPTR_SETTING_PORT]       = IFptr.LIBFPTR_PORT_TCPIP
            settings[IFptr.LIBFPTR_SETTING_IPADDRESS]  = forceString(options.get('tcpIpHost', ''))
            settings[IFptr.LIBFPTR_SETTING_IPPORT]     = forceInt(options.get('tcpIpPort', 5555))
        elif options['link'] == 'bluetooth':
            settings[IFptr.LIBFPTR_SETTING_PORT]       = IFptr.LIBFPTR_PORT_BLUETOOTH
            settings[IFptr.LIBFPTR_SETTING_MACADDRESS] = forceString(options.get('bluetoothMacAddress', ''))
        else: # usb
            settings[IFptr.LIBFPTR_SETTING_PORT]       = IFptr.LIBFPTR_PORT_USB
        if self.fptr:
            self.fptr.setSettings(settings)


    def driverLoaded(self):
        return bool(self.fptr)


    def open(self):
        if self.fptr:
            self.__checkError(self.fptr.open())


    def close(self):
        if self.fptr:
            self.__checkError(self.fptr.close())


    def isOpen(self):
        if self.fptr:
            return self.fptr.isOpened()
        else:
            return False


    def getModelInfo(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_MODEL_INFO)
        self.__checkError(self.fptr.queryData())

#        model           = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_MODEL)
        modelName       = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME)
        firmwareVersion = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)

        return { #'model'   : model,
                 'name'    : modelName,
                 'version' : firmwareVersion,
               }


    def getFactoryNumber(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SERIAL_NUMBER)
        self.__checkError(self.fptr.queryData())
        return self.fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)


    def getOfdExchangeStatus(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_OFD_EXCHANGE_STATUS)
        self.__checkError(self.fptr.fnQueryData())

        exchangeStatus      = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_OFD_EXCHANGE_STATUS)
        unsentCount         = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENTS_COUNT)
        firstUnsentNumber   = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)
#        ofdMessageRead      = self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_OFD_MESSAGE_READ)
        dateTime            = self.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)

        return { 'unsentCount'         : unsentCount,
                 'firstUnsentNumber'   : firstUnsentNumber,
                 'firstUnsentdateTime' : dateTime,

                 'connected'           : bool(exchangeStatus & (1<<0)), # бит 0 - транспортное соединение установлено
                 'queueIsNotEmpty'     : bool(exchangeStatus & (1<<1)), # бит 1 – есть сообщение для передачи в ОФД
#    бит 2 – ожидание ответного сообщения (квитанции) от ОФД
#    бит 3 – есть команда от ОФД
#    бит 4 – изменились настройки соединения с ОФД
#    бит 5 – ожидание ответа на команду от ОФД
               }


    def openSession(self):
        self.__operatorLogin()
#        self.fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT, text)
        self.__checkError(self.fptr.openShift())
        self.__checkDocumentClosed()
        self.__queryRegistrationInfo()

#        self.fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT, text)
#        self.fptr.printText()


    def getSessionState(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHIFT_STATE)
        self.__checkError(self.fptr.queryData())

        state    = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE)
#        number   = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
#        dateTime = self.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)

        return { 'state': state,
#                 'date' : self._decodeDate(resp[1:4][::-1]),
#                 'time' : self._decodeTime(resp[4:7]),
               }


    def getSessionInfo(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_SHIFT)
        self.__checkError(self.fptr.fnQueryData())

        sessionNumber = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
        receiptNumber = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_NUMBER)
        return { 'sessionNumber' : sessionNumber,
                 'receiptNumber' : receiptNumber,
               }



    def closeSession(self):
        self.__operatorLogin()
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_CLOSE_SHIFT)
        self.__checkError(self.fptr.report())
        self.__checkDocumentClosed()


    def openReceipt(self,
                    receiptType,
                    payerName=None,
                    payerEmail=None,
                    printReceipt=True,
                    customAttrName=None,
                    customAttrValue=None):
        self.__operatorLogin()
        if customAttrName and customAttrValue:
            self.fptr.setParam(1085, customAttrName)
            self.fptr.setParam(1086, customAttrValue)
            self.fptr.utilFormTlv()
            customAttr = self.fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE)
        else:
            customAttr = None
        if payerName:
            if self._ffdVersion == self.ffd120:
                self.fptr.setParam(self.tagPayerName, payerName)
                # self.fptr.setParam(self.tagPayerInn, int(payerInn))
                self.fptr.utilFormTlv()
                payerInfo = self.fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE)
                self.fptr.setParam(self.tagPayerInfo, payerInfo)
            else:
                self.fptr.setParam(self.tagPayerName, payerName)
        if payerEmail:
            self.fptr.setParam(self.tagPayerContact, payerEmail)
        if not printReceipt:
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY, True)
        if customAttr:
            self.fptr.setParam(1084, customAttr)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, receiptType)
        self.__checkError(self.fptr.openReceipt())


    def cancelReceipt(self):
        self.__checkError(self.fptr.cancelReceipt())


    def closeReceipt(self):
        self.__checkError(self.fptr.closeReceipt())
        self.__checkDocumentClosed()


    def isReceiptOpen(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_RECEIPT_STATE)
        self.__checkError( self.fptr.queryData())
        receiptType = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE)
        return receiptType != IFptr.LIBFPTR_RT_CLOSED


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

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME,   name)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_PRICE,            price)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY,         quantity)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_MEASUREMENT_UNIT, IFptr.LIBFPTR_IU_PIECE)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_SUM,              sum_) # ???
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_POSITION_SUM,     sum_)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE,         self.__encodeVat(vatPercent))
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_SUM,          0) # При передаче значения 0 рассчитывается автоматически
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DEPARTMENT,       section)
        self.fptr.setParam(self.tagPaymentObject,                paymentObject) # Признак предмета расчета (тег 1212)
        self.fptr.setParam(self.tagPaymentMethod,                paymentMethod) # Признак способа рaсчета (тег 1214)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_CHECK_SUM,        checkCache)
        self.__checkError(self.fptr.registration())



    def pay(self, paymentType, sum_):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, paymentType)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, sum_)
        self.__checkError(self.fptr.payment())


    def getCash(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_CASH_SUM)
        self.__checkError(self.fptr.queryData())
        return self.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_SUM)


    def putToCash(self, sum_):
        self.__operatorLogin()
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_SUM, sum_)
        self.__checkError(self.fptr.cashIncome())


    def takeFromCash(self, sum_):
        self.__operatorLogin()
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_SUM, sum_)
        self.__checkError(self.fptr.cashOutcome())


    # Команды печати
    def printText(self, text):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT, text)
#        self.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, IFptr.LIBFPTR_ALIGNMENT_CENTER)
        self.fptr.printText()


    def printLastDocument(self):
        self.__operatorLogin()
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_LAST_DOCUMENT)
        self.__checkError(self.fptr.report())
        self.__checkDocumentClosed()


    # Команды управления
    def cutReceipt(self, partialy=False):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_CUT_TYPE, 
                           IFptr.LIBFPTR_CT_PART if partialy else IFptr.LIBFPTR_CT_FULL)
        self.fptr.cut()


    def beep(self):
        self.fptr.beep()


    def sound(self, freq, duration):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FREQUENCY, freq)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DURATION, duration*1000)
        self.fptr.beep()


    def reportX(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_X)
        self.fptr.report()


    def reportLastDocument(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_LAST_DOCUMENT)
        self.fptr.report()


    def reportOfdExchangeStatus(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_OFD_EXCHANGE_STATUS)
        self.fptr.report()
        #checkDocumentClosed?


    def reportQuantity(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_QUANTITY)
        self.fptr.report()


    def reportOperators(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_OPERATORS)
        self.fptr.report()


    def reportHours(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_HOURS)
        self.fptr.report()


    def reportShiftTotalCounters(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_FN_SHIFT_TOTAL_COUNTERS)
        self.fptr.report()


    def reportFnTotalCounters(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_FN_TOTAL_COUNTERS)
        self.fptr.report()


    def reportOfdTest(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_OFD_TEST)
        self.fptr.report()


    def reportCashRegisterInfo(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_KKT_INFO)
        self.fptr.report()


    def reportRegistration(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_FN_REGISTRATIONS)
        self.fptr.report()



#    def printDocumentByNumber(self, number) - может быть полезно, не реализовано.
