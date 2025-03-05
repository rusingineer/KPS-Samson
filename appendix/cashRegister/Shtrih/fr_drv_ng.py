# -*- coding: utf-8 -*-
# This file is generated automatically, all changes will be lost!


from __future__ import division, absolute_import, print_function, unicode_literals
import ctypes
import datetime
import os
import os.path
import sys
import time


time_t = ctypes.c_long      # это но это не точно
context_p = ctypes.c_void_p # этого достаточно


def wrapString(s):
    if isinstance(s, bytes):
        return(s)
    else:
        return s.encode('utf-8')


def unwrapString(s):
    return s.decode('utf-8')


def wrapDateTime(dt):
    return int(time.mktime(dt.timetuple()))


def unwrapDateTime(ts):
    return datetime.datetime.fromtimestamp(ts)


class ClassicInterfaceWrap:
    @staticmethod
    def loadLibrary():
        fileDirName = os.path.dirname(__file__)
        if os.name == 'nt' or sys.platform == 'cygwin':
            baseNames = [ 'classic_fr_drv_ng.dll',    # для случая msvc
                          'libclassic_fr_drv_ng.dll', # для случая mingw
                        ]
            libDirs   = [ os.path.join(fileDirName, 'fr_drv_ng'),
                          fileDirName,
                          os.path.join(os.path.curdir, 'fr_drv_ng'),
                          os.path.curdir,
                          ''
                        ]
        elif os.name == 'posix':
            baseNames = [ 'libclassic_fr_drv_ng.so',
                        ]
#            bitness   = ctypes.sizeof(ctypes.c_void_p)*8
            libDirs   = [
#                          os.path.join('/', 'opt', 'fr_drv_ng', 'lib%d' % bitness),
                          os.path.join('/', 'opt', 'fr_drv_ng', 'lib'),
                          os.path.join('/', 'opt', 'fr_drv_ng'),
#                          os.path.join(fileDirName, 'fr_drv_ng', 'lib%d' % bitness),
                          os.path.join(fileDirName, 'fr_drv_ng', 'lib'),
                          os.path.join(fileDirName, 'fr_drv_ng'),
                          fileDirName,
#                          os.path.join(os.path.curdir, 'fr_drv_ng', 'lib%d' % bitness),
                          os.path.join(os.path.curdir, 'fr_drv_ng', 'lib'),
                          os.path.join(os.path.curdir, 'fr_drv_ng'),
                          os.path.curdir,
                        ]
        else:
            raise NotImplementedError('fr_drv_ng support is not implemented for this platform')

        for baseName in baseNames:
            for libDir in libDirs:
                try:
                    return ctypes.CDLL(os.path.join(libDir, baseName))
                except:
                    pass
        raise Exception('fr_drv_ng library not found in list %r'
                        % [
                            os.path.join(libDir, baseName)
                            for libDir in libDirs
                            for baseName in baseNames
                          ]
                       )


    def __init__(self):
        self.lib = lib = self.loadLibrary()
        c_classic_init_proto = ctypes.CFUNCTYPE(context_p, ctypes.c_char_p)
        c_classic_deinit_proto = ctypes.CFUNCTYPE(None, context_p)
        Buy_proto = ctypes.CFUNCTYPE(ctypes.c_int, context_p)
        Get_CPLog_proto = ctypes.CFUNCTYPE(ctypes.c_bool, context_p)
        Get_Price_proto = ctypes.CFUNCTYPE(ctypes.c_int64, context_p)
        Set_Price_proto = ctypes.CFUNCTYPE(None, context_p, ctypes.c_int64)
        Set_Tax1_proto = ctypes.CFUNCTYPE(None, context_p, ctypes.c_int)
        Get_INN_proto = ctypes.CFUNCTYPE(ctypes.c_size_t, context_p, ctypes.c_char_p, ctypes.c_size_t)
        Set_INN_proto = ctypes.CFUNCTYPE(None, context_p, ctypes.c_char_p, ctypes.c_size_t)
        Get_Date_proto = ctypes.CFUNCTYPE(time_t, context_p)
        Set_CPLog_proto = ctypes.CFUNCTYPE(None, context_p, ctypes.c_bool)
        Get_Password_proto = ctypes.CFUNCTYPE(ctypes.c_uint32, context_p)
        Set_Password_proto = ctypes.CFUNCTYPE(None, context_p, ctypes.c_uint32)
        Set_Date_proto = ctypes.CFUNCTYPE(None, context_p, time_t)
        Get_Quantity_proto = ctypes.CFUNCTYPE(ctypes.c_double, context_p)
        Set_Quantity_proto = ctypes.CFUNCTYPE(None, context_p, ctypes.c_double)
        Get_CheckSum_proto = ctypes.CFUNCTYPE(ctypes.c_uint64, context_p)
        Set_CheckSum_proto = ctypes.CFUNCTYPE(None, context_p, ctypes.c_uint64)

        self.c_classic_init   = c_classic_init_proto(('c_classic_init', lib))
        self.c_classic_deinit = c_classic_deinit_proto(('c_classic_deinit', lib))
        self.AddLD = Buy_proto(('AddLD', lib))
        self.Beep = Buy_proto(('Beep', lib))
        self.Buy = Buy_proto(('Buy', lib))
        self.BuyEx = Buy_proto(('BuyEx', lib))
        self.CancelCheck = Buy_proto(('CancelCheck', lib))
        self.CashIncome = Buy_proto(('CashIncome', lib))
        self.CashOutcome = Buy_proto(('CashOutcome', lib))
        self.Charge = Buy_proto(('Charge', lib))
        self.CheckSubTotal = Buy_proto(('CheckSubTotal', lib))
        self.CloseCheck = Buy_proto(('CloseCheck', lib))
        self.ConfirmDate = Buy_proto(('ConfirmDate', lib))
        self.Connect = Buy_proto(('Connect', lib))
        self.ContinuePrint = Buy_proto(('ContinuePrint', lib))
        self.Correction = Buy_proto(('Correction', lib))
        self.CutCheck = Buy_proto(('CutCheck', lib))
        self.DampRequest = Buy_proto(('DampRequest', lib))
        self.DeleteLD = Buy_proto(('DeleteLD', lib))
        self.Disconnect = Buy_proto(('Disconnect', lib))
        self.Discount = Buy_proto(('Discount', lib))
        self.DozeOilCheck = Buy_proto(('DozeOilCheck', lib))
        self.Draw = Buy_proto(('Draw', lib))
        self.EKLZDepartmentReportInDatesRange = Buy_proto(('EKLZDepartmentReportInDatesRange', lib))
        self.EKLZDepartmentReportInSessionsRange = Buy_proto(('EKLZDepartmentReportInSessionsRange', lib))
        self.EKLZJournalOnSessionNumber = Buy_proto(('EKLZJournalOnSessionNumber', lib))
        self.EKLZSessionReportInDatesRange = Buy_proto(('EKLZSessionReportInDatesRange', lib))
        self.EKLZSessionReportInSessionsRange = Buy_proto(('EKLZSessionReportInSessionsRange', lib))
        self.ExchangeBytes = Buy_proto(('ExchangeBytes', lib))
        self.FeedDocument = Buy_proto(('FeedDocument', lib))
        self.Fiscalization = Buy_proto(('Fiscalization', lib))
        self.FiscalReportForDatesRange = Buy_proto(('FiscalReportForDatesRange', lib))
        self.FiscalReportForSessionRange = Buy_proto(('FiscalReportForSessionRange', lib))
        self.GetActiveLD = Buy_proto(('GetActiveLD', lib))
        self.EnumLD = Buy_proto(('EnumLD', lib))
        self.GetCashReg = Buy_proto(('GetCashReg', lib))
        self.GetCountLD = Buy_proto(('GetCountLD', lib))
        self.GetData = Buy_proto(('GetData', lib))
        self.GetDeviceMetrics = Buy_proto(('GetDeviceMetrics', lib))
        self.GetECRStatus = Buy_proto(('GetECRStatus', lib))
        self.GetShortECRStatus = Buy_proto(('GetShortECRStatus', lib))
        self.GetExchangeParam = Buy_proto(('GetExchangeParam', lib))
        self.GetFieldStruct = Buy_proto(('GetFieldStruct', lib))
        self.GetFiscalizationParameters = Buy_proto(('GetFiscalizationParameters', lib))
        self.GetFMRecordsSum = Buy_proto(('GetFMRecordsSum', lib))
        self.GetLastFMRecordDate = Buy_proto(('GetLastFMRecordDate', lib))
        self.GetLiterSumCounter = Buy_proto(('GetLiterSumCounter', lib))
        self.GetOperationReg = Buy_proto(('GetOperationReg', lib))
        self.GetParamLD = Buy_proto(('GetParamLD', lib))
        self.GetRangeDatesAndSessions = Buy_proto(('GetRangeDatesAndSessions', lib))
        self.GetRKStatus = Buy_proto(('GetRKStatus', lib))
        self.GetTableStruct = Buy_proto(('GetTableStruct', lib))
        self.InitFM = Buy_proto(('InitFM', lib))
        self.InitTable = Buy_proto(('InitTable', lib))
        self.InterruptDataStream = Buy_proto(('InterruptDataStream', lib))
        self.InterruptFullReport = Buy_proto(('InterruptFullReport', lib))
        self.InterruptTest = Buy_proto(('InterruptTest', lib))
        self.LaunchRK = Buy_proto(('LaunchRK', lib))
        self.LoadLineData = Buy_proto(('LoadLineData', lib))
        self.OilSale = Buy_proto(('OilSale', lib))
        self.OpenCheck = Buy_proto(('OpenCheck', lib))
        self.OpenDrawer = Buy_proto(('OpenDrawer', lib))
        self.PrintBarCode = Buy_proto(('PrintBarCode', lib))
        self.PrintDepartmentReport = Buy_proto(('PrintDepartmentReport', lib))
        self.PrintDocumentTitle = Buy_proto(('PrintDocumentTitle', lib))
        self.PrintOperationReg = Buy_proto(('PrintOperationReg', lib))
        self.PrintReportWithCleaning = Buy_proto(('PrintReportWithCleaning', lib))
        self.PrintReportWithoutCleaning = Buy_proto(('PrintReportWithoutCleaning', lib))
        self.PrintString = Buy_proto(('PrintString', lib))
        self.PrintWideString = Buy_proto(('PrintWideString', lib))
        self.ReadEKLZDocumentOnKPK = Buy_proto(('ReadEKLZDocumentOnKPK', lib))
        self.ReadEKLZSessionTotal = Buy_proto(('ReadEKLZSessionTotal', lib))
        self.ReadLicense = Buy_proto(('ReadLicense', lib))
        self.ReadTable = Buy_proto(('ReadTable', lib))
        self.RepeatDocument = Buy_proto(('RepeatDocument', lib))
        self.ResetAllTRK = Buy_proto(('ResetAllTRK', lib))
        self.ResetRK = Buy_proto(('ResetRK', lib))
        self.ResetSettings = Buy_proto(('ResetSettings', lib))
        self.ResetSummary = Buy_proto(('ResetSummary', lib))
        self.ReturnBuy = Buy_proto(('ReturnBuy', lib))
        self.ReturnBuyEx = Buy_proto(('ReturnBuyEx', lib))
        self.ReturnSale = Buy_proto(('ReturnSale', lib))
        self.ReturnSaleEx = Buy_proto(('ReturnSaleEx', lib))
        self.Sale = Buy_proto(('Sale', lib))
        self.SaleEx = Buy_proto(('SaleEx', lib))
        self.SetActiveLD = Buy_proto(('SetActiveLD', lib))
        self.SetDate = Buy_proto(('SetDate', lib))
        self.SetDozeInMilliliters = Buy_proto(('SetDozeInMilliliters', lib))
        self.SetDozeInMoney = Buy_proto(('SetDozeInMoney', lib))
        self.SetExchangeParam = Buy_proto(('SetExchangeParam', lib))
        self.SetParamLD = Buy_proto(('SetParamLD', lib))
        self.SetPointPosition = Buy_proto(('SetPointPosition', lib))
        self.SetRKParameters = Buy_proto(('SetRKParameters', lib))
        self.SetSerialNumber = Buy_proto(('SetSerialNumber', lib))
        self.SetTime = Buy_proto(('SetTime', lib))
        self.ShowProperties = Buy_proto(('ShowProperties', lib))
        self.StopEKLZDocumentPrinting = Buy_proto(('StopEKLZDocumentPrinting', lib))
        self.StopRK = Buy_proto(('StopRK', lib))
        self.Storno = Buy_proto(('Storno', lib))
        self.StornoEx = Buy_proto(('StornoEx', lib))
        self.StornoCharge = Buy_proto(('StornoCharge', lib))
        self.StornoDiscount = Buy_proto(('StornoDiscount', lib))
        self.SummOilCheck = Buy_proto(('SummOilCheck', lib))
        self.SysAdminCancelCheck = Buy_proto(('SysAdminCancelCheck', lib))
        self.Test = Buy_proto(('Test', lib))
        self.WriteLicense = Buy_proto(('WriteLicense', lib))
        self.WriteTable = Buy_proto(('WriteTable', lib))
        self.PrintStringWithFont = Buy_proto(('PrintStringWithFont', lib))
        self.Get_BatteryCondition = Get_CPLog_proto(('Get_BatteryCondition', lib))
        self.Get_CheckResult = Get_Price_proto(('Get_CheckResult', lib))
        self.Set_CheckResult = Set_Price_proto(('Set_CheckResult', lib))
        self.Get_CurrentDozeInMilliliters = Buy_proto(('Get_CurrentDozeInMilliliters', lib))
        self.Set_CurrentDozeInMilliliters = Set_Tax1_proto(('Set_CurrentDozeInMilliliters', lib))
        self.Get_CurrentDozeInMoney = Get_Price_proto(('Get_CurrentDozeInMoney', lib))
        self.Set_CurrentDozeInMoney = Set_Price_proto(('Set_CurrentDozeInMoney', lib))
        self.Get_DozeInMilliliters = Buy_proto(('Get_DozeInMilliliters', lib))
        self.Set_DozeInMilliliters = Set_Tax1_proto(('Set_DozeInMilliliters', lib))
        self.Get_DozeInMoney = Get_Price_proto(('Get_DozeInMoney', lib))
        self.Set_DozeInMoney = Set_Price_proto(('Set_DozeInMoney', lib))
        self.Get_ECRAdvancedModeDescription = Get_INN_proto(('Get_ECRAdvancedModeDescription', lib))
        self.Get_ECRInput = Get_INN_proto(('Get_ECRInput', lib))
        self.Get_ECROutput = Get_INN_proto(('Get_ECROutput', lib))
        self.Get_EmergencyStopCode = Buy_proto(('Get_EmergencyStopCode', lib))
        self.Get_EmergencyStopCodeDescription = Get_INN_proto(('Get_EmergencyStopCodeDescription', lib))
        self.Get_IsCheckClosed = Get_CPLog_proto(('Get_IsCheckClosed', lib))
        self.Get_IsCheckMadeOut = Get_CPLog_proto(('Get_IsCheckMadeOut', lib))
        self.Get_KPKNumber = Buy_proto(('Get_KPKNumber', lib))
        self.Set_KPKNumber = Set_Tax1_proto(('Set_KPKNumber', lib))
        self.Get_Motor = Get_CPLog_proto(('Get_Motor', lib))
        self.Get_Pistol = Get_CPLog_proto(('Get_Pistol', lib))
        self.Get_RKNumber = Buy_proto(('Get_RKNumber', lib))
        self.Set_RKNumber = Set_Tax1_proto(('Set_RKNumber', lib))
        self.Get_RoughValve = Get_CPLog_proto(('Get_RoughValve', lib))
        self.Get_SlowingInMilliliters = Buy_proto(('Get_SlowingInMilliliters', lib))
        self.Set_SlowingInMilliliters = Set_Tax1_proto(('Set_SlowingInMilliliters', lib))
        self.Get_SlowingValve = Get_CPLog_proto(('Get_SlowingValve', lib))
        self.Get_StatusRK = Buy_proto(('Get_StatusRK', lib))
        self.Get_StatusRKDescription = Get_INN_proto(('Get_StatusRKDescription', lib))
        self.Get_TRKNumber = Buy_proto(('Get_TRKNumber', lib))
        self.Set_TRKNumber = Set_Tax1_proto(('Set_TRKNumber', lib))
        self.Get_LDBaudrate = Buy_proto(('Get_LDBaudrate', lib))
        self.Set_LDBaudrate = Set_Tax1_proto(('Set_LDBaudrate', lib))
        self.Get_LDComNumber = Buy_proto(('Get_LDComNumber', lib))
        self.Set_LDComNumber = Set_Tax1_proto(('Set_LDComNumber', lib))
        self.Get_LDCount = Buy_proto(('Get_LDCount', lib))
        self.Get_LDIndex = Buy_proto(('Get_LDIndex', lib))
        self.Set_LDIndex = Set_Tax1_proto(('Set_LDIndex', lib))
        self.Get_LDName = Get_INN_proto(('Get_LDName', lib))
        self.Set_LDName = Set_INN_proto(('Set_LDName', lib))
        self.Get_LDNumber = Buy_proto(('Get_LDNumber', lib))
        self.Set_LDNumber = Set_Tax1_proto(('Set_LDNumber', lib))
        self.Get_WaitPrintingTime = Buy_proto(('Get_WaitPrintingTime', lib))
        self.EKLZActivizationResult = Buy_proto(('EKLZActivizationResult', lib))
        self.EKLZActivization = Buy_proto(('EKLZActivization', lib))
        self.CloseEKLZArchive = Buy_proto(('CloseEKLZArchive', lib))
        self.GetEKLZSerialNumber = Buy_proto(('GetEKLZSerialNumber', lib))
        self.Get_EKLZNumber = Get_INN_proto(('Get_EKLZNumber', lib))
        self.EKLZInterrupt = Buy_proto(('EKLZInterrupt', lib))
        self.GetEKLZCode1Report = Buy_proto(('GetEKLZCode1Report', lib))
        self.Get_LastKPKDocumentResult = Get_Price_proto(('Get_LastKPKDocumentResult', lib))
        self.Get_LastKPKDate = Get_Date_proto(('Get_LastKPKDate', lib))
        self.Get_LastKPKTime = Get_Date_proto(('Get_LastKPKTime', lib))
        self.Get_LastKPKNumber = Buy_proto(('Get_LastKPKNumber', lib))
        self.Get_EKLZFlags = Buy_proto(('Get_EKLZFlags', lib))
        self.GetEKLZCode2Report = Buy_proto(('GetEKLZCode2Report', lib))
        self.TestEKLZArchiveIntegrity = Buy_proto(('TestEKLZArchiveIntegrity', lib))
        self.Get_TestNumber = Buy_proto(('Get_TestNumber', lib))
        self.Set_TestNumber = Set_Tax1_proto(('Set_TestNumber', lib))
        self.Get_EKLZVersion = Get_INN_proto(('Get_EKLZVersion', lib))
        self.Get_EKLZData = Get_INN_proto(('Get_EKLZData', lib))
        self.GetEKLZVersion = Buy_proto(('GetEKLZVersion', lib))
        self.InitEKLZArchive = Buy_proto(('InitEKLZArchive', lib))
        self.GetEKLZData = Buy_proto(('GetEKLZData', lib))
        self.GetEKLZJournal = Buy_proto(('GetEKLZJournal', lib))
        self.GetEKLZDocument = Buy_proto(('GetEKLZDocument', lib))
        self.GetEKLZDepartmentReportInDatesRange = Buy_proto(('GetEKLZDepartmentReportInDatesRange', lib))
        self.GetEKLZDepartmentReportInSessionsRange = Buy_proto(('GetEKLZDepartmentReportInSessionsRange', lib))
        self.GetEKLZSessionReportInDatesRange = Buy_proto(('GetEKLZSessionReportInDatesRange', lib))
        self.GetEKLZSessionReportInSessionsRange = Buy_proto(('GetEKLZSessionReportInSessionsRange', lib))
        self.GetEKLZSessionTotal = Buy_proto(('GetEKLZSessionTotal', lib))
        self.GetEKLZActivizationResult = Buy_proto(('GetEKLZActivizationResult', lib))
        self.SetEKLZResultCode = Buy_proto(('SetEKLZResultCode', lib))
        self.OpenFiscalSlipDocument = Buy_proto(('OpenFiscalSlipDocument', lib))
        self.OpenStandardFiscalSlipDocument = Buy_proto(('OpenStandardFiscalSlipDocument', lib))
        self.RegistrationOnSlipDocument = Buy_proto(('RegistrationOnSlipDocument', lib))
        self.StandardRegistrationOnSlipDocument = Buy_proto(('StandardRegistrationOnSlipDocument', lib))
        self.ChargeOnSlipDocument = Buy_proto(('ChargeOnSlipDocument', lib))
        self.StandardChargeOnSlipDocument = Buy_proto(('StandardChargeOnSlipDocument', lib))
        self.CloseCheckOnSlipDocument = Buy_proto(('CloseCheckOnSlipDocument', lib))
        self.StandardCloseCheckOnSlipDocument = Buy_proto(('StandardCloseCheckOnSlipDocument', lib))
        self.ConfigureSlipDocument = Buy_proto(('ConfigureSlipDocument', lib))
        self.ConfigureStandardSlipDocument = Buy_proto(('ConfigureStandardSlipDocument', lib))
        self.FillSlipDocumentWithUnfiscalInfo = Buy_proto(('FillSlipDocumentWithUnfiscalInfo', lib))
        self.ClearSlipDocumentBufferString = Buy_proto(('ClearSlipDocumentBufferString', lib))
        self.ClearSlipDocumentBuffer = Buy_proto(('ClearSlipDocumentBuffer', lib))
        self.PrintSlipDocument = Buy_proto(('PrintSlipDocument', lib))
        self.Get_CopyType = Buy_proto(('Get_CopyType', lib))
        self.Set_CopyType = Set_Tax1_proto(('Set_CopyType', lib))
        self.Get_NumberOfCopies = Buy_proto(('Get_NumberOfCopies', lib))
        self.Set_NumberOfCopies = Set_Tax1_proto(('Set_NumberOfCopies', lib))
        self.Get_CopyOffset1 = Buy_proto(('Get_CopyOffset1', lib))
        self.Set_CopyOffset1 = Set_Tax1_proto(('Set_CopyOffset1', lib))
        self.Get_CopyOffset2 = Buy_proto(('Get_CopyOffset2', lib))
        self.Set_CopyOffset2 = Set_Tax1_proto(('Set_CopyOffset2', lib))
        self.Get_CopyOffset3 = Buy_proto(('Get_CopyOffset3', lib))
        self.Set_CopyOffset3 = Set_Tax1_proto(('Set_CopyOffset3', lib))
        self.Get_CopyOffset4 = Buy_proto(('Get_CopyOffset4', lib))
        self.Set_CopyOffset4 = Set_Tax1_proto(('Set_CopyOffset4', lib))
        self.Get_CopyOffset5 = Buy_proto(('Get_CopyOffset5', lib))
        self.Set_CopyOffset5 = Set_Tax1_proto(('Set_CopyOffset5', lib))
        self.Get_ClicheFont = Buy_proto(('Get_ClicheFont', lib))
        self.Set_ClicheFont = Set_Tax1_proto(('Set_ClicheFont', lib))
        self.Get_HeaderFont = Buy_proto(('Get_HeaderFont', lib))
        self.Set_HeaderFont = Set_Tax1_proto(('Set_HeaderFont', lib))
        self.Get_EKLZFont = Buy_proto(('Get_EKLZFont', lib))
        self.Set_EKLZFont = Set_Tax1_proto(('Set_EKLZFont', lib))
        self.Get_ClicheStringNumber = Buy_proto(('Get_ClicheStringNumber', lib))
        self.Set_ClicheStringNumber = Set_Tax1_proto(('Set_ClicheStringNumber', lib))
        self.Get_HeaderStringNumber = Buy_proto(('Get_HeaderStringNumber', lib))
        self.Set_HeaderStringNumber = Set_Tax1_proto(('Set_HeaderStringNumber', lib))
        self.Get_EKLZStringNumber = Buy_proto(('Get_EKLZStringNumber', lib))
        self.Set_EKLZStringNumber = Set_Tax1_proto(('Set_EKLZStringNumber', lib))
        self.Get_FMStringNumber = Buy_proto(('Get_FMStringNumber', lib))
        self.Set_FMStringNumber = Set_Tax1_proto(('Set_FMStringNumber', lib))
        self.Get_ClicheOffset = Buy_proto(('Get_ClicheOffset', lib))
        self.Set_ClicheOffset = Set_Tax1_proto(('Set_ClicheOffset', lib))
        self.Get_HeaderOffset = Buy_proto(('Get_HeaderOffset', lib))
        self.Set_HeaderOffset = Set_Tax1_proto(('Set_HeaderOffset', lib))
        self.Get_EKLZOffset = Buy_proto(('Get_EKLZOffset', lib))
        self.Set_EKLZOffset = Set_Tax1_proto(('Set_EKLZOffset', lib))
        self.Get_KPKOffset = Buy_proto(('Get_KPKOffset', lib))
        self.Set_KPKOffset = Set_Tax1_proto(('Set_KPKOffset', lib))
        self.Get_FMOffset = Buy_proto(('Get_FMOffset', lib))
        self.Set_FMOffset = Set_Tax1_proto(('Set_FMOffset', lib))
        self.Get_OperationBlockFirstString = Buy_proto(('Get_OperationBlockFirstString', lib))
        self.Set_OperationBlockFirstString = Set_Tax1_proto(('Set_OperationBlockFirstString', lib))
        self.Get_QuantityFormat = Buy_proto(('Get_QuantityFormat', lib))
        self.Set_QuantityFormat = Set_Tax1_proto(('Set_QuantityFormat', lib))
        self.Get_StringQuantityInOperation = Buy_proto(('Get_StringQuantityInOperation', lib))
        self.Set_StringQuantityInOperation = Set_Tax1_proto(('Set_StringQuantityInOperation', lib))
        self.Get_TextStringNumber = Buy_proto(('Get_TextStringNumber', lib))
        self.Set_TextStringNumber = Set_Tax1_proto(('Set_TextStringNumber', lib))
        self.Get_QuantityStringNumber = Buy_proto(('Get_QuantityStringNumber', lib))
        self.Set_QuantityStringNumber = Set_Tax1_proto(('Set_QuantityStringNumber', lib))
        self.Get_SummStringNumber = Buy_proto(('Get_SummStringNumber', lib))
        self.Set_SummStringNumber = Set_Tax1_proto(('Set_SummStringNumber', lib))
        self.Get_DepartmentStringNumber = Buy_proto(('Get_DepartmentStringNumber', lib))
        self.Set_DepartmentStringNumber = Set_Tax1_proto(('Set_DepartmentStringNumber', lib))
        self.Get_TextFont = Buy_proto(('Get_TextFont', lib))
        self.Set_TextFont = Set_Tax1_proto(('Set_TextFont', lib))
        self.Get_QuantityFont = Buy_proto(('Get_QuantityFont', lib))
        self.Set_QuantityFont = Set_Tax1_proto(('Set_QuantityFont', lib))
        self.Get_MultiplicationFont = Buy_proto(('Get_MultiplicationFont', lib))
        self.Set_MultiplicationFont = Set_Tax1_proto(('Set_MultiplicationFont', lib))
        self.Get_PriceFont = Buy_proto(('Get_PriceFont', lib))
        self.Set_PriceFont = Set_Tax1_proto(('Set_PriceFont', lib))
        self.Get_SummFont = Buy_proto(('Get_SummFont', lib))
        self.Set_SummFont = Set_Tax1_proto(('Set_SummFont', lib))
        self.Get_DepartmentFont = Buy_proto(('Get_DepartmentFont', lib))
        self.Set_DepartmentFont = Set_Tax1_proto(('Set_DepartmentFont', lib))
        self.Get_TextSymbolNumber = Buy_proto(('Get_TextSymbolNumber', lib))
        self.Set_TextSymbolNumber = Set_Tax1_proto(('Set_TextSymbolNumber', lib))
        self.Get_QuantitySymbolNumber = Buy_proto(('Get_QuantitySymbolNumber', lib))
        self.Set_QuantitySymbolNumber = Set_Tax1_proto(('Set_QuantitySymbolNumber', lib))
        self.Get_PriceSymbolNumber = Buy_proto(('Get_PriceSymbolNumber', lib))
        self.Set_PriceSymbolNumber = Set_Tax1_proto(('Set_PriceSymbolNumber', lib))
        self.Get_SummSymbolNumber = Buy_proto(('Get_SummSymbolNumber', lib))
        self.Set_SummSymbolNumber = Set_Tax1_proto(('Set_SummSymbolNumber', lib))
        self.Get_DepartmentSymbolNumber = Buy_proto(('Get_DepartmentSymbolNumber', lib))
        self.Set_DepartmentSymbolNumber = Set_Tax1_proto(('Set_DepartmentSymbolNumber', lib))
        self.Get_TextOffset = Buy_proto(('Get_TextOffset', lib))
        self.Set_TextOffset = Set_Tax1_proto(('Set_TextOffset', lib))
        self.Get_QuantityOffset = Buy_proto(('Get_QuantityOffset', lib))
        self.Set_QuantityOffset = Set_Tax1_proto(('Set_QuantityOffset', lib))
        self.Get_SummOffset = Buy_proto(('Get_SummOffset', lib))
        self.Set_SummOffset = Set_Tax1_proto(('Set_SummOffset', lib))
        self.Get_DepartmentOffset = Buy_proto(('Get_DepartmentOffset', lib))
        self.Set_DepartmentOffset = Set_Tax1_proto(('Set_DepartmentOffset', lib))
        self.DiscountOnSlipDocument = Buy_proto(('DiscountOnSlipDocument', lib))
        self.StandardDiscountOnSlipDocument = Buy_proto(('StandardDiscountOnSlipDocument', lib))
        self.Get_IsClearUnfiscalInfo = Get_CPLog_proto(('Get_IsClearUnfiscalInfo', lib))
        self.Set_IsClearUnfiscalInfo = Set_CPLog_proto(('Set_IsClearUnfiscalInfo', lib))
        self.Get_InfoType = Buy_proto(('Get_InfoType', lib))
        self.Set_InfoType = Set_Tax1_proto(('Set_InfoType', lib))
        self.Get_StringNumber = Buy_proto(('Get_StringNumber', lib))
        self.Set_StringNumber = Set_Tax1_proto(('Set_StringNumber', lib))
        self.EjectSlipDocument = Buy_proto(('EjectSlipDocument', lib))
        self.Get_EjectDirection = Buy_proto(('Get_EjectDirection', lib))
        self.Set_EjectDirection = Set_Tax1_proto(('Set_EjectDirection', lib))
        self.LoadLineDataEx = Buy_proto(('LoadLineDataEx', lib))
        self.DrawEx = Buy_proto(('DrawEx', lib))
        self.ConfigureGeneralSlipDocument = Buy_proto(('ConfigureGeneralSlipDocument', lib))
        self.Get_OperationNameStringNumber = Buy_proto(('Get_OperationNameStringNumber', lib))
        self.Set_OperationNameStringNumber = Set_Tax1_proto(('Set_OperationNameStringNumber', lib))
        self.Get_OperationNameFont = Buy_proto(('Get_OperationNameFont', lib))
        self.Set_OperationNameFont = Set_Tax1_proto(('Set_OperationNameFont', lib))
        self.Get_OperationNameOffset = Buy_proto(('Get_OperationNameOffset', lib))
        self.Set_OperationNameOffset = Set_Tax1_proto(('Set_OperationNameOffset', lib))
        self.Get_TotalStringNumber = Buy_proto(('Get_TotalStringNumber', lib))
        self.Set_TotalStringNumber = Set_Tax1_proto(('Set_TotalStringNumber', lib))
        self.Get_Summ1StringNumber = Buy_proto(('Get_Summ1StringNumber', lib))
        self.Set_Summ1StringNumber = Set_Tax1_proto(('Set_Summ1StringNumber', lib))
        self.Get_Summ2StringNumber = Buy_proto(('Get_Summ2StringNumber', lib))
        self.Set_Summ2StringNumber = Set_Tax1_proto(('Set_Summ2StringNumber', lib))
        self.Get_Summ3StringNumber = Buy_proto(('Get_Summ3StringNumber', lib))
        self.Set_Summ3StringNumber = Set_Tax1_proto(('Set_Summ3StringNumber', lib))
        self.Get_Summ4StringNumber = Buy_proto(('Get_Summ4StringNumber', lib))
        self.Set_Summ4StringNumber = Set_Tax1_proto(('Set_Summ4StringNumber', lib))
        self.Get_ChangeStringNumber = Buy_proto(('Get_ChangeStringNumber', lib))
        self.Set_ChangeStringNumber = Set_Tax1_proto(('Set_ChangeStringNumber', lib))
        self.Get_Tax1TurnOverStringNumber = Buy_proto(('Get_Tax1TurnOverStringNumber', lib))
        self.Set_Tax1TurnOverStringNumber = Set_Tax1_proto(('Set_Tax1TurnOverStringNumber', lib))
        self.Get_Tax2TurnOverStringNumber = Buy_proto(('Get_Tax2TurnOverStringNumber', lib))
        self.Set_Tax2TurnOverStringNumber = Set_Tax1_proto(('Set_Tax2TurnOverStringNumber', lib))
        self.Get_Tax3TurnOverStringNumber = Buy_proto(('Get_Tax3TurnOverStringNumber', lib))
        self.Set_Tax3TurnOverStringNumber = Set_Tax1_proto(('Set_Tax3TurnOverStringNumber', lib))
        self.Get_Tax4TurnOverStringNumber = Buy_proto(('Get_Tax4TurnOverStringNumber', lib))
        self.Set_Tax4TurnOverStringNumber = Set_Tax1_proto(('Set_Tax4TurnOverStringNumber', lib))
        self.Get_Tax1SumStringNumber = Buy_proto(('Get_Tax1SumStringNumber', lib))
        self.Set_Tax1SumStringNumber = Set_Tax1_proto(('Set_Tax1SumStringNumber', lib))
        self.Get_Tax2SumStringNumber = Buy_proto(('Get_Tax2SumStringNumber', lib))
        self.Set_Tax2SumStringNumber = Set_Tax1_proto(('Set_Tax2SumStringNumber', lib))
        self.Get_Tax3SumStringNumber = Buy_proto(('Get_Tax3SumStringNumber', lib))
        self.Set_Tax3SumStringNumber = Set_Tax1_proto(('Set_Tax3SumStringNumber', lib))
        self.Get_Tax4SumStringNumber = Buy_proto(('Get_Tax4SumStringNumber', lib))
        self.Set_Tax4SumStringNumber = Set_Tax1_proto(('Set_Tax4SumStringNumber', lib))
        self.Get_SubTotalStringNumber = Buy_proto(('Get_SubTotalStringNumber', lib))
        self.Set_SubTotalStringNumber = Set_Tax1_proto(('Set_SubTotalStringNumber', lib))
        self.Get_DiscountOnCheckStringNumber = Buy_proto(('Get_DiscountOnCheckStringNumber', lib))
        self.Set_DiscountOnCheckStringNumber = Set_Tax1_proto(('Set_DiscountOnCheckStringNumber', lib))
        self.Get_TotalFont = Buy_proto(('Get_TotalFont', lib))
        self.Set_TotalFont = Set_Tax1_proto(('Set_TotalFont', lib))
        self.Get_TotalSumFont = Buy_proto(('Get_TotalSumFont', lib))
        self.Set_TotalSumFont = Set_Tax1_proto(('Set_TotalSumFont', lib))
        self.Get_Summ1Font = Buy_proto(('Get_Summ1Font', lib))
        self.Set_Summ1Font = Set_Tax1_proto(('Set_Summ1Font', lib))
        self.Get_Summ1NameFont = Buy_proto(('Get_Summ1NameFont', lib))
        self.Set_Summ1NameFont = Set_Tax1_proto(('Set_Summ1NameFont', lib))
        self.Get_Summ2NameFont = Buy_proto(('Get_Summ2NameFont', lib))
        self.Set_Summ2NameFont = Set_Tax1_proto(('Set_Summ2NameFont', lib))
        self.Get_Summ3NameFont = Buy_proto(('Get_Summ3NameFont', lib))
        self.Set_Summ3NameFont = Set_Tax1_proto(('Set_Summ3NameFont', lib))
        self.Get_Summ4NameFont = Buy_proto(('Get_Summ4NameFont', lib))
        self.Set_Summ4NameFont = Set_Tax1_proto(('Set_Summ4NameFont', lib))
        self.Get_Summ2Font = Buy_proto(('Get_Summ2Font', lib))
        self.Set_Summ2Font = Set_Tax1_proto(('Set_Summ2Font', lib))
        self.Get_Summ3Font = Buy_proto(('Get_Summ3Font', lib))
        self.Set_Summ3Font = Set_Tax1_proto(('Set_Summ3Font', lib))
        self.Get_Summ4Font = Buy_proto(('Get_Summ4Font', lib))
        self.Set_Summ4Font = Set_Tax1_proto(('Set_Summ4Font', lib))
        self.Get_ChangeFont = Buy_proto(('Get_ChangeFont', lib))
        self.Set_ChangeFont = Set_Tax1_proto(('Set_ChangeFont', lib))
        self.Get_ChangeSumFont = Buy_proto(('Get_ChangeSumFont', lib))
        self.Set_ChangeSumFont = Set_Tax1_proto(('Set_ChangeSumFont', lib))
        self.Get_Tax1NameFont = Buy_proto(('Get_Tax1NameFont', lib))
        self.Set_Tax1NameFont = Set_Tax1_proto(('Set_Tax1NameFont', lib))
        self.Get_Tax2NameFont = Buy_proto(('Get_Tax2NameFont', lib))
        self.Set_Tax2NameFont = Set_Tax1_proto(('Set_Tax2NameFont', lib))
        self.Get_Tax3NameFont = Buy_proto(('Get_Tax3NameFont', lib))
        self.Set_Tax3NameFont = Set_Tax1_proto(('Set_Tax3NameFont', lib))
        self.Get_Tax4NameFont = Buy_proto(('Get_Tax4NameFont', lib))
        self.Set_Tax4NameFont = Set_Tax1_proto(('Set_Tax4NameFont', lib))
        self.Get_Tax1TurnOverFont = Buy_proto(('Get_Tax1TurnOverFont', lib))
        self.Set_Tax1TurnOverFont = Set_Tax1_proto(('Set_Tax1TurnOverFont', lib))
        self.Get_Tax2TurnOverFont = Buy_proto(('Get_Tax2TurnOverFont', lib))
        self.Set_Tax2TurnOverFont = Set_Tax1_proto(('Set_Tax2TurnOverFont', lib))
        self.Get_Tax3TurnOverFont = Buy_proto(('Get_Tax3TurnOverFont', lib))
        self.Set_Tax3TurnOverFont = Set_Tax1_proto(('Set_Tax3TurnOverFont', lib))
        self.Get_Tax4TurnOverFont = Buy_proto(('Get_Tax4TurnOverFont', lib))
        self.Set_Tax4TurnOverFont = Set_Tax1_proto(('Set_Tax4TurnOverFont', lib))
        self.Get_Tax1RateFont = Buy_proto(('Get_Tax1RateFont', lib))
        self.Set_Tax1RateFont = Set_Tax1_proto(('Set_Tax1RateFont', lib))
        self.Get_Tax2RateFont = Buy_proto(('Get_Tax2RateFont', lib))
        self.Set_Tax2RateFont = Set_Tax1_proto(('Set_Tax2RateFont', lib))
        self.Get_Tax3RateFont = Buy_proto(('Get_Tax3RateFont', lib))
        self.Set_Tax3RateFont = Set_Tax1_proto(('Set_Tax3RateFont', lib))
        self.Get_Tax4RateFont = Buy_proto(('Get_Tax4RateFont', lib))
        self.Set_Tax4RateFont = Set_Tax1_proto(('Set_Tax4RateFont', lib))
        self.Get_Tax1SumFont = Buy_proto(('Get_Tax1SumFont', lib))
        self.Set_Tax1SumFont = Set_Tax1_proto(('Set_Tax1SumFont', lib))
        self.Get_Tax2SumFont = Buy_proto(('Get_Tax2SumFont', lib))
        self.Set_Tax2SumFont = Set_Tax1_proto(('Set_Tax2SumFont', lib))
        self.Get_Tax3SumFont = Buy_proto(('Get_Tax3SumFont', lib))
        self.Set_Tax3SumFont = Set_Tax1_proto(('Set_Tax3SumFont', lib))
        self.Get_Tax4SumFont = Buy_proto(('Get_Tax4SumFont', lib))
        self.Set_Tax4SumFont = Set_Tax1_proto(('Set_Tax4SumFont', lib))
        self.Get_SubTotalFont = Buy_proto(('Get_SubTotalFont', lib))
        self.Set_SubTotalFont = Set_Tax1_proto(('Set_SubTotalFont', lib))
        self.Get_SubTotalSumFont = Buy_proto(('Get_SubTotalSumFont', lib))
        self.Set_SubTotalSumFont = Set_Tax1_proto(('Set_SubTotalSumFont', lib))
        self.Get_DiscountOnCheckFont = Buy_proto(('Get_DiscountOnCheckFont', lib))
        self.Set_DiscountOnCheckFont = Set_Tax1_proto(('Set_DiscountOnCheckFont', lib))
        self.Get_DiscountOnCheckSumFont = Buy_proto(('Get_DiscountOnCheckSumFont', lib))
        self.Set_DiscountOnCheckSumFont = Set_Tax1_proto(('Set_DiscountOnCheckSumFont', lib))
        self.Get_TotalSymbolNumber = Buy_proto(('Get_TotalSymbolNumber', lib))
        self.Set_TotalSymbolNumber = Set_Tax1_proto(('Set_TotalSymbolNumber', lib))
        self.Get_Summ1SymbolNumber = Buy_proto(('Get_Summ1SymbolNumber', lib))
        self.Set_Summ1SymbolNumber = Set_Tax1_proto(('Set_Summ1SymbolNumber', lib))
        self.Get_Summ2SymbolNumber = Buy_proto(('Get_Summ2SymbolNumber', lib))
        self.Set_Summ2SymbolNumber = Set_Tax1_proto(('Set_Summ2SymbolNumber', lib))
        self.Get_Summ3SymbolNumber = Buy_proto(('Get_Summ3SymbolNumber', lib))
        self.Set_Summ3SymbolNumber = Set_Tax1_proto(('Set_Summ3SymbolNumber', lib))
        self.Get_Summ4SymbolNumber = Buy_proto(('Get_Summ4SymbolNumber', lib))
        self.Set_Summ4SymbolNumber = Set_Tax1_proto(('Set_Summ4SymbolNumber', lib))
        self.Get_ChangeSymbolNumber = Buy_proto(('Get_ChangeSymbolNumber', lib))
        self.Set_ChangeSymbolNumber = Set_Tax1_proto(('Set_ChangeSymbolNumber', lib))
        self.Get_Tax1NameSymbolNumber = Buy_proto(('Get_Tax1NameSymbolNumber', lib))
        self.Set_Tax1NameSymbolNumber = Set_Tax1_proto(('Set_Tax1NameSymbolNumber', lib))
        self.Get_Tax1TurnOverSymbolNumber = Buy_proto(('Get_Tax1TurnOverSymbolNumber', lib))
        self.Set_Tax1TurnOverSymbolNumber = Set_Tax1_proto(('Set_Tax1TurnOverSymbolNumber', lib))
        self.Get_Tax1RateSymbolNumber = Buy_proto(('Get_Tax1RateSymbolNumber', lib))
        self.Set_Tax1RateSymbolNumber = Set_Tax1_proto(('Set_Tax1RateSymbolNumber', lib))
        self.Get_Tax1SumSymbolNumber = Buy_proto(('Get_Tax1SumSymbolNumber', lib))
        self.Set_Tax1SumSymbolNumber = Set_Tax1_proto(('Set_Tax1SumSymbolNumber', lib))
        self.Get_Tax2NameSymbolNumber = Buy_proto(('Get_Tax2NameSymbolNumber', lib))
        self.Set_Tax2NameSymbolNumber = Set_Tax1_proto(('Set_Tax2NameSymbolNumber', lib))
        self.Get_Tax2TurnOverSymbolNumber = Buy_proto(('Get_Tax2TurnOverSymbolNumber', lib))
        self.Set_Tax2TurnOverSymbolNumber = Set_Tax1_proto(('Set_Tax2TurnOverSymbolNumber', lib))
        self.Get_Tax2RateSymbolNumber = Buy_proto(('Get_Tax2RateSymbolNumber', lib))
        self.Set_Tax2RateSymbolNumber = Set_Tax1_proto(('Set_Tax2RateSymbolNumber', lib))
        self.Get_Tax2SumSymbolNumber = Buy_proto(('Get_Tax2SumSymbolNumber', lib))
        self.Set_Tax2SumSymbolNumber = Set_Tax1_proto(('Set_Tax2SumSymbolNumber', lib))
        self.Get_Tax3NameSymbolNumber = Buy_proto(('Get_Tax3NameSymbolNumber', lib))
        self.Set_Tax3NameSymbolNumber = Set_Tax1_proto(('Set_Tax3NameSymbolNumber', lib))
        self.Get_Tax3TurnOverSymbolNumber = Buy_proto(('Get_Tax3TurnOverSymbolNumber', lib))
        self.Set_Tax3TurnOverSymbolNumber = Set_Tax1_proto(('Set_Tax3TurnOverSymbolNumber', lib))
        self.Get_Tax3RateSymbolNumber = Buy_proto(('Get_Tax3RateSymbolNumber', lib))
        self.Set_Tax3RateSymbolNumber = Set_Tax1_proto(('Set_Tax3RateSymbolNumber', lib))
        self.Get_Tax3SumSymbolNumber = Buy_proto(('Get_Tax3SumSymbolNumber', lib))
        self.Set_Tax3SumSymbolNumber = Set_Tax1_proto(('Set_Tax3SumSymbolNumber', lib))
        self.Get_Tax4NameSymbolNumber = Buy_proto(('Get_Tax4NameSymbolNumber', lib))
        self.Set_Tax4NameSymbolNumber = Set_Tax1_proto(('Set_Tax4NameSymbolNumber', lib))
        self.Get_Tax4TurnOverSymbolNumber = Buy_proto(('Get_Tax4TurnOverSymbolNumber', lib))
        self.Set_Tax4TurnOverSymbolNumber = Set_Tax1_proto(('Set_Tax4TurnOverSymbolNumber', lib))
        self.Get_Tax4RateSymbolNumber = Buy_proto(('Get_Tax4RateSymbolNumber', lib))
        self.Set_Tax4RateSymbolNumber = Set_Tax1_proto(('Set_Tax4RateSymbolNumber', lib))
        self.Get_Tax4SumSymbolNumber = Buy_proto(('Get_Tax4SumSymbolNumber', lib))
        self.Set_Tax4SumSymbolNumber = Set_Tax1_proto(('Set_Tax4SumSymbolNumber', lib))
        self.Get_SubTotalSymbolNumber = Buy_proto(('Get_SubTotalSymbolNumber', lib))
        self.Set_SubTotalSymbolNumber = Set_Tax1_proto(('Set_SubTotalSymbolNumber', lib))
        self.Get_DiscountOnCheckSymbolNumber = Buy_proto(('Get_DiscountOnCheckSymbolNumber', lib))
        self.Set_DiscountOnCheckSymbolNumber = Set_Tax1_proto(('Set_DiscountOnCheckSymbolNumber', lib))
        self.Get_DiscountOnCheckSumSymbolNumber = Buy_proto(('Get_DiscountOnCheckSumSymbolNumber', lib))
        self.Set_DiscountOnCheckSumSymbolNumber = Set_Tax1_proto(('Set_DiscountOnCheckSumSymbolNumber', lib))
        self.Get_TotalOffset = Buy_proto(('Get_TotalOffset', lib))
        self.Set_TotalOffset = Set_Tax1_proto(('Set_TotalOffset', lib))
        self.Get_Summ1Offset = Buy_proto(('Get_Summ1Offset', lib))
        self.Set_Summ1Offset = Set_Tax1_proto(('Set_Summ1Offset', lib))
        self.Get_TotalSumOffset = Buy_proto(('Get_TotalSumOffset', lib))
        self.Set_TotalSumOffset = Set_Tax1_proto(('Set_TotalSumOffset', lib))
        self.Get_Summ1NameOffset = Buy_proto(('Get_Summ1NameOffset', lib))
        self.Set_Summ1NameOffset = Set_Tax1_proto(('Set_Summ1NameOffset', lib))
        self.Get_Summ2Offset = Buy_proto(('Get_Summ2Offset', lib))
        self.Set_Summ2Offset = Set_Tax1_proto(('Set_Summ2Offset', lib))
        self.Get_Summ2NameOffset = Buy_proto(('Get_Summ2NameOffset', lib))
        self.Set_Summ2NameOffset = Set_Tax1_proto(('Set_Summ2NameOffset', lib))
        self.Get_Summ3Offset = Buy_proto(('Get_Summ3Offset', lib))
        self.Set_Summ3Offset = Set_Tax1_proto(('Set_Summ3Offset', lib))
        self.Get_Summ3NameOffset = Buy_proto(('Get_Summ3NameOffset', lib))
        self.Set_Summ3NameOffset = Set_Tax1_proto(('Set_Summ3NameOffset', lib))
        self.Get_Summ4Offset = Buy_proto(('Get_Summ4Offset', lib))
        self.Set_Summ4Offset = Set_Tax1_proto(('Set_Summ4Offset', lib))
        self.Get_Summ4NameOffset = Buy_proto(('Get_Summ4NameOffset', lib))
        self.Set_Summ4NameOffset = Set_Tax1_proto(('Set_Summ4NameOffset', lib))
        self.Get_ChangeOffset = Buy_proto(('Get_ChangeOffset', lib))
        self.Set_ChangeOffset = Set_Tax1_proto(('Set_ChangeOffset', lib))
        self.Get_ChangeSumOffset = Buy_proto(('Get_ChangeSumOffset', lib))
        self.Set_ChangeSumOffset = Set_Tax1_proto(('Set_ChangeSumOffset', lib))
        self.Get_Tax1NameOffset = Buy_proto(('Get_Tax1NameOffset', lib))
        self.Set_Tax1NameOffset = Set_Tax1_proto(('Set_Tax1NameOffset', lib))
        self.Get_Tax1TurnOverOffset = Buy_proto(('Get_Tax1TurnOverOffset', lib))
        self.Set_Tax1TurnOverOffset = Set_Tax1_proto(('Set_Tax1TurnOverOffset', lib))
        self.Get_Tax1RateOffset = Buy_proto(('Get_Tax1RateOffset', lib))
        self.Set_Tax1RateOffset = Set_Tax1_proto(('Set_Tax1RateOffset', lib))
        self.Get_Tax1SumOffset = Buy_proto(('Get_Tax1SumOffset', lib))
        self.Set_Tax1SumOffset = Set_Tax1_proto(('Set_Tax1SumOffset', lib))
        self.Get_Tax2NameOffset = Buy_proto(('Get_Tax2NameOffset', lib))
        self.Set_Tax2NameOffset = Set_Tax1_proto(('Set_Tax2NameOffset', lib))
        self.Get_Tax2TurnOverOffset = Buy_proto(('Get_Tax2TurnOverOffset', lib))
        self.Set_Tax2TurnOverOffset = Set_Tax1_proto(('Set_Tax2TurnOverOffset', lib))
        self.Get_Tax2RateOffset = Buy_proto(('Get_Tax2RateOffset', lib))
        self.Set_Tax2RateOffset = Set_Tax1_proto(('Set_Tax2RateOffset', lib))
        self.Get_Tax2SumOffset = Buy_proto(('Get_Tax2SumOffset', lib))
        self.Set_Tax2SumOffset = Set_Tax1_proto(('Set_Tax2SumOffset', lib))
        self.Get_Tax3NameOffset = Buy_proto(('Get_Tax3NameOffset', lib))
        self.Set_Tax3NameOffset = Set_Tax1_proto(('Set_Tax3NameOffset', lib))
        self.Get_Tax3TurnOverOffset = Buy_proto(('Get_Tax3TurnOverOffset', lib))
        self.Set_Tax3TurnOverOffset = Set_Tax1_proto(('Set_Tax3TurnOverOffset', lib))
        self.Get_Tax3RateOffset = Buy_proto(('Get_Tax3RateOffset', lib))
        self.Set_Tax3RateOffset = Set_Tax1_proto(('Set_Tax3RateOffset', lib))
        self.Get_Tax3SumOffset = Buy_proto(('Get_Tax3SumOffset', lib))
        self.Set_Tax3SumOffset = Set_Tax1_proto(('Set_Tax3SumOffset', lib))
        self.Get_Tax4NameOffset = Buy_proto(('Get_Tax4NameOffset', lib))
        self.Set_Tax4NameOffset = Set_Tax1_proto(('Set_Tax4NameOffset', lib))
        self.Get_Tax4TurnOverOffset = Buy_proto(('Get_Tax4TurnOverOffset', lib))
        self.Set_Tax4TurnOverOffset = Set_Tax1_proto(('Set_Tax4TurnOverOffset', lib))
        self.Get_Tax4RateOffset = Buy_proto(('Get_Tax4RateOffset', lib))
        self.Set_Tax4RateOffset = Set_Tax1_proto(('Set_Tax4RateOffset', lib))
        self.Get_Tax4SumOffset = Buy_proto(('Get_Tax4SumOffset', lib))
        self.Set_Tax4SumOffset = Set_Tax1_proto(('Set_Tax4SumOffset', lib))
        self.Get_SubTotalOffset = Buy_proto(('Get_SubTotalOffset', lib))
        self.Set_SubTotalOffset = Set_Tax1_proto(('Set_SubTotalOffset', lib))
        self.Get_SubTotalSumOffset = Buy_proto(('Get_SubTotalSumOffset', lib))
        self.Set_SubTotalSumOffset = Set_Tax1_proto(('Set_SubTotalSumOffset', lib))
        self.Get_SlipDocumentWidth = Buy_proto(('Get_SlipDocumentWidth', lib))
        self.Set_SlipDocumentWidth = Set_Tax1_proto(('Set_SlipDocumentWidth', lib))
        self.Get_SlipDocumentLength = Buy_proto(('Get_SlipDocumentLength', lib))
        self.Set_SlipDocumentLength = Set_Tax1_proto(('Set_SlipDocumentLength', lib))
        self.Get_PrintingAlignment = Buy_proto(('Get_PrintingAlignment', lib))
        self.Set_PrintingAlignment = Set_Tax1_proto(('Set_PrintingAlignment', lib))
        self.Get_SlipStringIntervals = Get_INN_proto(('Get_SlipStringIntervals', lib))
        self.Set_SlipStringIntervals = Set_INN_proto(('Set_SlipStringIntervals', lib))
        self.Get_SlipEqualStringIntervals = Buy_proto(('Get_SlipEqualStringIntervals', lib))
        self.Set_SlipEqualStringIntervals = Set_Tax1_proto(('Set_SlipEqualStringIntervals', lib))
        self.Get_KPKFont = Buy_proto(('Get_KPKFont', lib))
        self.Set_KPKFont = Set_Tax1_proto(('Set_KPKFont', lib))
        self.Get_DiscountOnCheckOffset = Buy_proto(('Get_DiscountOnCheckOffset', lib))
        self.Set_DiscountOnCheckOffset = Set_Tax1_proto(('Set_DiscountOnCheckOffset', lib))
        self.Get_DiscountOnCheckSumOffset = Buy_proto(('Get_DiscountOnCheckSumOffset', lib))
        self.Set_DiscountOnCheckSumOffset = Set_Tax1_proto(('Set_DiscountOnCheckSumOffset', lib))
        self.WideLoadLineData = Buy_proto(('WideLoadLineData', lib))
        self.PrintTaxReport = Buy_proto(('PrintTaxReport', lib))
        self.Get_FileVersionMS = Get_Password_proto(('Get_FileVersionMS', lib))
        self.Get_FileVersionLS = Get_Password_proto(('Get_FileVersionLS', lib))
        self.GetLongSerialNumberAndLongRNM = Buy_proto(('GetLongSerialNumberAndLongRNM', lib))
        self.SetLongSerialNumber = Buy_proto(('SetLongSerialNumber', lib))
        self.FiscalizationWithLongRNM = Buy_proto(('FiscalizationWithLongRNM', lib))
        self.Connect2 = Buy_proto(('Connect2', lib))
        self.GetECRPrinterStatus = Buy_proto(('GetECRPrinterStatus', lib))
        self.Get_PrinterStatus = Buy_proto(('Get_PrinterStatus', lib))
        self.Get_ServerVersion = Get_INN_proto(('Get_ServerVersion', lib))
        self.Get_LDComputerName = Get_INN_proto(('Get_LDComputerName', lib))
        self.Set_LDComputerName = Set_INN_proto(('Set_LDComputerName', lib))
        self.Get_LDTimeout = Buy_proto(('Get_LDTimeout', lib))
        self.Set_LDTimeout = Set_Tax1_proto(('Set_LDTimeout', lib))
        self.ServerConnect = Buy_proto(('ServerConnect', lib))
        self.ServerDisconnect = Buy_proto(('ServerDisconnect', lib))
        self.Get_ServerConnected = Get_CPLog_proto(('Get_ServerConnected', lib))
        self.LockPort = Buy_proto(('LockPort', lib))
        self.UnlockPort = Buy_proto(('UnlockPort', lib))
        self.Get_PortLocked = Get_CPLog_proto(('Get_PortLocked', lib))
        self.AdminUnlockPort = Buy_proto(('AdminUnlockPort', lib))
        self.AdminUnlockPorts = Buy_proto(('AdminUnlockPorts', lib))
        self.ServerCheckKey = Buy_proto(('ServerCheckKey', lib))
        self.GetFontMetrics = Buy_proto(('GetFontMetrics', lib))
        self.GetFreeLDNumber = Buy_proto(('GetFreeLDNumber', lib))
        self.Get_LogOn = Get_CPLog_proto(('Get_LogOn', lib))
        self.Set_LogOn = Set_CPLog_proto(('Set_LogOn', lib))
        self.ReadTable2 = Buy_proto(('ReadTable2', lib))
        self.WriteTable2 = Buy_proto(('WriteTable2', lib))
        self.SetFieldMinValue = Set_Tax1_proto(('SetFieldMinValue', lib))
        self.SetFieldMaxValue = Set_Tax1_proto(('SetFieldMaxValue', lib))
        self.Get_CPLog = Get_CPLog_proto(('Get_CPLog', lib))
        self.Set_CPLog = Set_CPLog_proto(('Set_CPLog', lib))
        self.Get_CashControlHost = Get_INN_proto(('Get_CashControlHost', lib))
        self.Set_CashControlHost = Set_INN_proto(('Set_CashControlHost', lib))
        self.Get_CashControlPort = Get_INN_proto(('Get_CashControlPort', lib))
        self.Set_CashControlPort = Set_INN_proto(('Set_CashControlPort', lib))
        self.Get_CashControlEnabled = Get_CPLog_proto(('Get_CashControlEnabled', lib))
        self.Set_CashControlEnabled = Set_CPLog_proto(('Set_CashControlEnabled', lib))
        self.Get_CashControlUseTCP = Get_CPLog_proto(('Get_CashControlUseTCP', lib))
        self.Set_CashControlUseTCP = Set_CPLog_proto(('Set_CashControlUseTCP', lib))
        self.Get_CashControlPassword = Get_Password_proto(('Get_CashControlPassword', lib))
        self.Set_CashControlPassword = Set_Password_proto(('Set_CashControlPassword', lib))
        self.CashControlOpen = Buy_proto(('CashControlOpen', lib))
        self.CashControlClose = Buy_proto(('CashControlClose', lib))
        self.Get_LDConnectionType = Buy_proto(('Get_LDConnectionType', lib))
        self.Set_LDConnectionType = Set_Tax1_proto(('Set_LDConnectionType', lib))
        self.Get_LDTCPPort = Buy_proto(('Get_LDTCPPort', lib))
        self.Set_LDTCPPort = Set_Tax1_proto(('Set_LDTCPPort', lib))
        self.Get_LDIPAddress = Get_INN_proto(('Get_LDIPAddress', lib))
        self.Set_LDIPAddress = Set_INN_proto(('Set_LDIPAddress', lib))
        self.Get_LDUseIPAddress = Get_CPLog_proto(('Get_LDUseIPAddress', lib))
        self.Set_LDUseIPAddress = Set_CPLog_proto(('Set_LDUseIPAddress', lib))
        self.SaveParams = Buy_proto(('SaveParams', lib))
        self.Get_CPLogFile = Get_INN_proto(('Get_CPLogFile', lib))
        self.Set_CPLogFile = Set_INN_proto(('Set_CPLogFile', lib))
        self.Get_ComLogFile = Get_INN_proto(('Get_ComLogFile', lib))
        self.Set_ComLogFile = Set_INN_proto(('Set_ComLogFile', lib))
        self.Get_LineData2 = Get_INN_proto(('Get_LineData2', lib))
        self.Set_LineData2 = Set_INN_proto(('Set_LineData2', lib))
        self.Get_RecoverError165 = Get_CPLog_proto(('Get_RecoverError165', lib))
        self.Set_RecoverError165 = Set_CPLog_proto(('Set_RecoverError165', lib))
        self.Get_MaxRecoverCount = Buy_proto(('Get_MaxRecoverCount', lib))
        self.Set_MaxRecoverCount = Set_Tax1_proto(('Set_MaxRecoverCount', lib))
        self.GetEKLZCode1Status = Buy_proto(('GetEKLZCode1Status', lib))
        self.GetEKLZCode2Status = Buy_proto(('GetEKLZCode2Status', lib))
        self.ReadWriteFM = Buy_proto(('ReadWriteFM', lib))
        self.PrintHeader = Buy_proto(('PrintHeader', lib))
        self.CloseCheckWithResult = Buy_proto(('CloseCheckWithResult', lib))
        self.Get_OperationCode = Buy_proto(('Get_OperationCode', lib))
        self.Get_AccType = Buy_proto(('Get_AccType', lib))
        self.Set_AccType = Set_Tax1_proto(('Set_AccType', lib))
        self.Get_Address = Buy_proto(('Get_Address', lib))
        self.Set_Address = Set_Tax1_proto(('Set_Address', lib))
        self.Get_WrittenByte = Buy_proto(('Get_WrittenByte', lib))
        self.Set_WrittenByte = Set_Tax1_proto(('Set_WrittenByte', lib))
        self.Get_ReadByte = Buy_proto(('Get_ReadByte', lib))
        self.Get_TransferByte = Get_INN_proto(('Get_TransferByte', lib))
        self.Set_TransferByte = Set_INN_proto(('Set_TransferByte', lib))
        self.AboutBox = Buy_proto(('AboutBox', lib))
        self.PresenterKeep = Buy_proto(('PresenterKeep', lib))
        self.PresenterPush = Buy_proto(('PresenterPush', lib))
        self.OpenScreen = Buy_proto(('OpenScreen', lib))
        self.CloseScreen = Buy_proto(('CloseScreen', lib))
        self.Get_ComLogOnlyErrors = Get_CPLog_proto(('Get_ComLogOnlyErrors', lib))
        self.Set_ComLogOnlyErrors = Set_CPLog_proto(('Set_ComLogOnlyErrors', lib))
        self.SetSCPassword = Buy_proto(('SetSCPassword', lib))
        self.Get_LastKPKDateStr = Get_INN_proto(('Get_LastKPKDateStr', lib))
        self.Get_LastKPKTimeStr = Get_INN_proto(('Get_LastKPKTimeStr', lib))
        self.MethodSupported = Get_CPLog_proto(('MethodSupported', lib))
        self.Get_MethodName = Get_INN_proto(('Get_MethodName', lib))
        self.Set_MethodName = Set_INN_proto(('Set_MethodName', lib))
        self.Get_PropertyName = Get_INN_proto(('Get_PropertyName', lib))
        self.Set_PropertyName = Set_INN_proto(('Set_PropertyName', lib))
        self.PropertySupported = Get_CPLog_proto(('PropertySupported', lib))
        self.Get_LockTimeout = Buy_proto(('Get_LockTimeout', lib))
        self.Set_LockTimeout = Set_Tax1_proto(('Set_LockTimeout', lib))
        self.LockPortTimeout = Buy_proto(('LockPortTimeout', lib))
        self.Get_SlipStringInterval = Buy_proto(('Get_SlipStringInterval', lib))
        self.Set_SlipStringInterval = Set_Tax1_proto(('Set_SlipStringInterval', lib))
        self.GetIBMStatus = Buy_proto(('GetIBMStatus', lib))
        self.GetShortIBMStatus = Buy_proto(('GetShortIBMStatus', lib))
        self.Get_IBMStatusByte1 = Buy_proto(('Get_IBMStatusByte1', lib))
        self.Get_IBMStatusByte2 = Buy_proto(('Get_IBMStatusByte2', lib))
        self.Get_IBMStatusByte3 = Buy_proto(('Get_IBMStatusByte3', lib))
        self.Get_IBMStatusByte4 = Buy_proto(('Get_IBMStatusByte4', lib))
        self.Get_IBMStatusByte5 = Buy_proto(('Get_IBMStatusByte5', lib))
        self.Get_IBMStatusByte6 = Buy_proto(('Get_IBMStatusByte6', lib))
        self.Get_IBMStatusByte7 = Buy_proto(('Get_IBMStatusByte7', lib))
        self.Get_IBMStatusByte8 = Buy_proto(('Get_IBMStatusByte8', lib))
        self.Get_IBMFlags = Buy_proto(('Get_IBMFlags', lib))
        self.Get_IBMDocumentNumber = Buy_proto(('Get_IBMDocumentNumber', lib))
        self.Get_IBMLastSaleReceiptNumber = Buy_proto(('Get_IBMLastSaleReceiptNumber', lib))
        self.Get_IBMLastBuyReceiptNumber = Buy_proto(('Get_IBMLastBuyReceiptNumber', lib))
        self.Get_IBMLastReturnSaleReceiptNumber = Buy_proto(('Get_IBMLastReturnSaleReceiptNumber', lib))
        self.Get_IBMLastReturnBuyReceiptNumber = Buy_proto(('Get_IBMLastReturnBuyReceiptNumber', lib))
        self.Get_IBMSessionDay = Buy_proto(('Get_IBMSessionDay', lib))
        self.Get_IBMSessionMonth = Buy_proto(('Get_IBMSessionMonth', lib))
        self.Get_IBMSessionYear = Buy_proto(('Get_IBMSessionYear', lib))
        self.Get_IBMSessionHour = Buy_proto(('Get_IBMSessionHour', lib))
        self.Get_IBMSessionMin = Buy_proto(('Get_IBMSessionMin', lib))
        self.Get_IBMSessionSec = Buy_proto(('Get_IBMSessionSec', lib))
        self.Get_IBMSessionDateTime = Get_Date_proto(('Get_IBMSessionDateTime', lib))
        self.Get_EscapeIP = Get_INN_proto(('Get_EscapeIP', lib))
        self.Set_EscapeIP = Set_INN_proto(('Set_EscapeIP', lib))
        self.Get_EscapePort = Buy_proto(('Get_EscapePort', lib))
        self.Set_EscapePort = Set_Tax1_proto(('Set_EscapePort', lib))
        self.Get_LDEscapeIP = Get_INN_proto(('Get_LDEscapeIP', lib))
        self.Set_LDEscapeIP = Set_INN_proto(('Set_LDEscapeIP', lib))
        self.Get_LDEscapePort = Buy_proto(('Get_LDEscapePort', lib))
        self.Set_LDEscapePort = Set_Tax1_proto(('Set_LDEscapePort', lib))
        self.Get_EscapeTimeout = Buy_proto(('Get_EscapeTimeout', lib))
        self.Set_EscapeTimeout = Set_Tax1_proto(('Set_EscapeTimeout', lib))
        self.Get_LDEscapeTimeout = Buy_proto(('Get_LDEscapeTimeout', lib))
        self.Set_LDEscapeTimeout = Set_Tax1_proto(('Set_LDEscapeTimeout', lib))
        self.Get_CommandTimeout = Buy_proto(('Get_CommandTimeout', lib))
        self.Set_CommandTimeout = Set_Tax1_proto(('Set_CommandTimeout', lib))
        self.Get_UseCommandTimeout = Get_CPLog_proto(('Get_UseCommandTimeout', lib))
        self.Set_UseCommandTimeout = Set_CPLog_proto(('Set_UseCommandTimeout', lib))
        self.Get_CommandCount = Buy_proto(('Get_CommandCount', lib))
        self.Get_CommandIndex = Buy_proto(('Get_CommandIndex', lib))
        self.Set_CommandIndex = Set_Tax1_proto(('Set_CommandIndex', lib))
        self.GetCommandParams = Buy_proto(('GetCommandParams', lib))
        self.SetCommandParams = Buy_proto(('SetCommandParams', lib))
        self.SaveCommandParams = Buy_proto(('SaveCommandParams', lib))
        self.Get_CommandName = Get_INN_proto(('Get_CommandName', lib))
        self.Get_CommandDefTimeout = Buy_proto(('Get_CommandDefTimeout', lib))
        self.Get_CommandCode = Buy_proto(('Get_CommandCode', lib))
        self.SetAllCommandsParams = Buy_proto(('SetAllCommandsParams', lib))
        self.Get_TimeoutsUsing = Buy_proto(('Get_TimeoutsUsing', lib))
        self.Set_TimeoutsUsing = Set_Tax1_proto(('Set_TimeoutsUsing', lib))
        self.SetDefCommandsParams = Buy_proto(('SetDefCommandsParams', lib))
        self.OpenSession = Buy_proto(('OpenSession', lib))
        self.WaitForPrinting = Buy_proto(('WaitForPrinting', lib))
        self.Get_IntervalNumber = Buy_proto(('Get_IntervalNumber', lib))
        self.Set_IntervalNumber = Set_Tax1_proto(('Set_IntervalNumber', lib))
        self.Get_IntervalValue = Buy_proto(('Get_IntervalValue', lib))
        self.Set_IntervalValue = Set_Tax1_proto(('Set_IntervalValue', lib))
        self.GetInterval = Buy_proto(('GetInterval', lib))
        self.SetInterval = Buy_proto(('SetInterval', lib))
        self.Get_ParentWnd = Buy_proto(('Get_ParentWnd', lib))
        self.Set_ParentWnd = Set_Tax1_proto(('Set_ParentWnd', lib))
        self.ShowTablesDlg = Buy_proto(('ShowTablesDlg', lib))
        self.Get_MobilePayEnabled = Get_CPLog_proto(('Get_MobilePayEnabled', lib))
        self.Set_MobilePayEnabled = Set_CPLog_proto(('Set_MobilePayEnabled', lib))
        self.Get_PayDepartment = Buy_proto(('Get_PayDepartment', lib))
        self.Set_PayDepartment = Set_Tax1_proto(('Set_PayDepartment', lib))
        self.Get_ParamsPageIndex = Buy_proto(('Get_ParamsPageIndex', lib))
        self.Set_ParamsPageIndex = Set_Tax1_proto(('Set_ParamsPageIndex', lib))
        self.ShowPayParams = Buy_proto(('ShowPayParams', lib))
        self.Get_SaleError = Get_CPLog_proto(('Get_SaleError', lib))
        self.Set_SaleError = Set_CPLog_proto(('Set_SaleError', lib))
        self.ReprintSlipDocument = Buy_proto(('ReprintSlipDocument', lib))
        self.Get_RealPayDepartment = Buy_proto(('Get_RealPayDepartment', lib))
        self.Set_RealPayDepartment = Set_Tax1_proto(('Set_RealPayDepartment', lib))
        self.CardPayProperties = Buy_proto(('CardPayProperties', lib))
        self.Get_CardPayEnabled = Get_CPLog_proto(('Get_CardPayEnabled', lib))
        self.Set_CardPayEnabled = Set_CPLog_proto(('Set_CardPayEnabled', lib))
        self.Get_CardPayType = Buy_proto(('Get_CardPayType', lib))
        self.Set_CardPayType = Set_Tax1_proto(('Set_CardPayType', lib))
        self.Get_ccUseTextAsWareName = Get_CPLog_proto(('Get_ccUseTextAsWareName', lib))
        self.Get_ccWareNameLineNumber = Buy_proto(('Get_ccWareNameLineNumber', lib))
        self.Set_ccUseTextAsWareName = Set_CPLog_proto(('Set_ccUseTextAsWareName', lib))
        self.Set_ccWareNameLineNumber = Set_Tax1_proto(('Set_ccWareNameLineNumber', lib))
        self.Get_ccHeaderLineCount = Buy_proto(('Get_ccHeaderLineCount', lib))
        self.Set_ccHeaderLineCount = Set_Tax1_proto(('Set_ccHeaderLineCount', lib))
        self.Get_LogCommands = Get_CPLog_proto(('Get_LogCommands', lib))
        self.Set_LogCommands = Set_CPLog_proto(('Set_LogCommands', lib))
        self.Get_LogMethods = Get_CPLog_proto(('Get_LogMethods', lib))
        self.Set_LogMethods = Set_CPLog_proto(('Set_LogMethods', lib))
        self.PrintLine = Buy_proto(('PrintLine', lib))
        self.JournalClear = Buy_proto(('JournalClear', lib))
        self.JournalGetRow = Buy_proto(('JournalGetRow', lib))
        self.Get_JournalEnabled = Get_CPLog_proto(('Get_JournalEnabled', lib))
        self.Set_JournalEnabled = Set_CPLog_proto(('Set_JournalEnabled', lib))
        self.Get_JournalRow = Get_INN_proto(('Get_JournalRow', lib))
        self.Get_JournalRowCount = Buy_proto(('Get_JournalRowCount', lib))
        self.Get_JournalRowNumber = Buy_proto(('Get_JournalRowNumber', lib))
        self.Set_JournalRowNumber = Set_Tax1_proto(('Set_JournalRowNumber', lib))
        self.Get_JournalText = Get_INN_proto(('Get_JournalText', lib))
        self.JournalInit = Buy_proto(('JournalInit', lib))
        self.FindDevice = Buy_proto(('FindDevice', lib))
        self.LoadParams = Buy_proto(('LoadParams', lib))
        self.FinishDocument = Buy_proto(('FinishDocument', lib))
        self.PrintTrailer = Buy_proto(('PrintTrailer', lib))
        self.Get_SerialNumberAsInteger = Buy_proto(('Get_SerialNumberAsInteger', lib))
        self.Get_INNAsInteger = Buy_proto(('Get_INNAsInteger', lib))
        self.Get_ECRDate = Get_Date_proto(('Get_ECRDate', lib))
        self.Set_ECRDate = Set_Date_proto(('Set_ECRDate', lib))
        self.Get_ECRTime = Get_Date_proto(('Get_ECRTime', lib))
        self.Set_ECRTime = Set_Date_proto(('Set_ECRTime', lib))
        self.WaitForCheckClose = Buy_proto(('WaitForCheckClose', lib))
        self.GetSummFactor = Buy_proto(('GetSummFactor', lib))
        self.GetQuantityFactor = Buy_proto(('GetQuantityFactor', lib))
        self.ReadDeviceMetrics = Buy_proto(('ReadDeviceMetrics', lib))
        self.ReadEcrStatus = Buy_proto(('ReadEcrStatus', lib))
        self.SaveState = Buy_proto(('SaveState', lib))
        self.RestoreState = Buy_proto(('RestoreState', lib))
        self.Get_HasCashControlLicense = Get_CPLog_proto(('Get_HasCashControlLicense', lib))
        self.Get_BufferingType = Buy_proto(('Get_BufferingType', lib))
        self.Set_BufferingType = Set_Tax1_proto(('Set_BufferingType', lib))
        self.LoadImage = Buy_proto(('LoadImage', lib))
        self.GetCashAcceptorStatus = Buy_proto(('GetCashAcceptorStatus', lib))
        self.GetCashAcceptorRegisters = Buy_proto(('GetCashAcceptorRegisters', lib))
        self.CashAcceptorReport = Buy_proto(('CashAcceptorReport', lib))
        self.Get_FeedAfterCut = Get_CPLog_proto(('Get_FeedAfterCut', lib))
        self.Set_FeedAfterCut = Set_CPLog_proto(('Set_FeedAfterCut', lib))
        self.Get_FeedLineCount = Buy_proto(('Get_FeedLineCount', lib))
        self.Set_FeedLineCount = Set_Tax1_proto(('Set_FeedLineCount', lib))
        self.ClearResult = Buy_proto(('ClearResult', lib))
        self.MasterPayClearBuffer = Buy_proto(('MasterPayClearBuffer', lib))
        self.MasterPayAddTextBlock = Buy_proto(('MasterPayAddTextBlock', lib))
        self.MasterPayCreateMac = Buy_proto(('MasterPayCreateMac', lib))
        self.Get_CashControlProtocols = Get_INN_proto(('Get_CashControlProtocols', lib))
        self.LoadBlockData = Buy_proto(('LoadBlockData', lib))
        self.Get_LogMaxFileSize = Buy_proto(('Get_LogMaxFileSize', lib))
        self.Set_LogMaxFileSize = Set_Tax1_proto(('Set_LogMaxFileSize', lib))
        self.Get_LogMaxFileCount = Buy_proto(('Get_LogMaxFileCount', lib))
        self.Set_LogMaxFileCount = Set_Tax1_proto(('Set_LogMaxFileCount', lib))
        self.Get_BinaryConversion = Buy_proto(('Get_BinaryConversion', lib))
        self.Set_BinaryConversion = Set_Tax1_proto(('Set_BinaryConversion', lib))
        self.Get_CodePage = Buy_proto(('Get_CodePage', lib))
        self.Set_CodePage = Set_Tax1_proto(('Set_CodePage', lib))
        self.Get_PrintJournalBeforeZReport = Get_CPLog_proto(('Get_PrintJournalBeforeZReport', lib))
        self.Set_PrintJournalBeforeZReport = Set_CPLog_proto(('Set_PrintJournalBeforeZReport', lib))
        self.GetEKLZCode3Report = Buy_proto(('GetEKLZCode3Report', lib))
        self.Get_TransmitStatus = Buy_proto(('Get_TransmitStatus', lib))
        self.Get_TransmitQueueSize = Buy_proto(('Get_TransmitQueueSize', lib))
        self.Get_TransmitSessionNumber = Buy_proto(('Get_TransmitSessionNumber', lib))
        self.Get_TransmitDocumentNumber = Buy_proto(('Get_TransmitDocumentNumber', lib))
        self.ReadModemParameter = Buy_proto(('ReadModemParameter', lib))
        self.WriteModemParameter = Buy_proto(('WriteModemParameter', lib))
        self.Get_ParameterNumber = Buy_proto(('Get_ParameterNumber', lib))
        self.Set_ParameterNumber = Set_Tax1_proto(('Set_ParameterNumber', lib))
        self.Get_ParameterValue = Get_INN_proto(('Get_ParameterValue', lib))
        self.Set_ParameterValue = Set_INN_proto(('Set_ParameterValue', lib))
        self.Get_TranslationEnabled = Get_CPLog_proto(('Get_TranslationEnabled', lib))
        self.Set_TranslationEnabled = Set_CPLog_proto(('Set_TranslationEnabled', lib))
        self.Get_ModelIndex = Buy_proto(('Get_ModelIndex', lib))
        self.Set_ModelIndex = Set_Tax1_proto(('Set_ModelIndex', lib))
        self.Get_ModelParamIndex = Buy_proto(('Get_ModelParamIndex', lib))
        self.Set_ModelParamIndex = Set_Tax1_proto(('Set_ModelParamIndex', lib))
        self.Get_ModelParamCount = Buy_proto(('Get_ModelParamCount', lib))
        self.GetPortNames = Buy_proto(('GetPortNames', lib))
        self.Get_ReceiptOutputType = Buy_proto(('Get_ReceiptOutputType', lib))
        self.OutputReceipt = Buy_proto(('OutputReceipt', lib))
        self.Set_ReceiptOutputType = Set_Tax1_proto(('Set_ReceiptOutputType', lib))
        self.Sale2 = Buy_proto(('Sale2', lib))
        self.PrintCliche = Buy_proto(('PrintCliche', lib))
        self.PrintBarcodeLine = Buy_proto(('PrintBarcodeLine', lib))
        self.PrintBarcodeGraph = Buy_proto(('PrintBarcodeGraph', lib))
        self.Get_BarcodeTypes = Get_INN_proto(('Get_BarcodeTypes', lib))
        self.Get_BarcodeAlignments = Get_INN_proto(('Get_BarcodeAlignments', lib))
        self.ResetECR = Buy_proto(('ResetECR', lib))
        self.PrintZReportFromBuffer = Buy_proto(('PrintZReportFromBuffer', lib))
        self.PrintZReportInBuffer = Buy_proto(('PrintZReportInBuffer', lib))
        self.Get_LogFileMaxSize = Buy_proto(('Get_LogFileMaxSize', lib))
        self.Set_LogFileMaxSize = Set_Tax1_proto(('Set_LogFileMaxSize', lib))
        self.ClearPrintBuffer = Buy_proto(('ClearPrintBuffer', lib))
        self.ReadPrintBufferLine = Buy_proto(('ReadPrintBufferLine', lib))
        self.ReadPrintBufferLineNumber = Buy_proto(('ReadPrintBufferLineNumber', lib))
        self.Get_PrintBufferFormat = Buy_proto(('Get_PrintBufferFormat', lib))
        self.Set_PrintBufferFormat = Set_Tax1_proto(('Set_PrintBufferFormat', lib))
        self.Get_PrintBufferLineNumber = Buy_proto(('Get_PrintBufferLineNumber', lib))
        self.Get_NakCount = Buy_proto(('Get_NakCount', lib))
        self.Set_NakCount = Set_Tax1_proto(('Set_NakCount', lib))
        self.Get_MaxAnswerReadCount = Buy_proto(('Get_MaxAnswerReadCount', lib))
        self.Get_MaxCommandSendCount = Buy_proto(('Get_MaxCommandSendCount', lib))
        self.Get_MaxENQSendCount = Buy_proto(('Get_MaxENQSendCount', lib))
        self.Set_MaxAnswerReadCount = Set_Tax1_proto(('Set_MaxAnswerReadCount', lib))
        self.Set_MaxCommandSendCount = Set_Tax1_proto(('Set_MaxCommandSendCount', lib))
        self.Set_MaxENQSendCount = Set_Tax1_proto(('Set_MaxENQSendCount', lib))
        self.Get_CommandRetryCount = Buy_proto(('Get_CommandRetryCount', lib))
        self.Set_CommandRetryCount = Set_Tax1_proto(('Set_CommandRetryCount', lib))
        self.OpenNonfiscalDocument = Buy_proto(('OpenNonfiscalDocument', lib))
        self.CloseNonFiscalDocument = Buy_proto(('CloseNonFiscalDocument', lib))
        self.Get_AttributeNumber = Buy_proto(('Get_AttributeNumber', lib))
        self.Get_AttributeValue = Get_INN_proto(('Get_AttributeValue', lib))
        self.PrintAttribute = Buy_proto(('PrintAttribute', lib))
        self.Set_AttributeNumber = Set_Tax1_proto(('Set_AttributeNumber', lib))
        self.Set_AttributeValue = Set_INN_proto(('Set_AttributeValue', lib))
        self.Get_ModelID = Buy_proto(('Get_ModelID', lib))
        self.ReadModelParamValue = Buy_proto(('ReadModelParamValue', lib))
        self.Set_ModelID = Set_Tax1_proto(('Set_ModelID', lib))
        self.LoadCashControlParams = Buy_proto(('LoadCashControlParams', lib))
        self.Set_Connected = Set_CPLog_proto(('Set_Connected', lib))
        self.Get_EnteredTaxPassword = Get_Password_proto(('Get_EnteredTaxPassword', lib))
        self.Get_BanknoteCount = Buy_proto(('Get_BanknoteCount', lib))
        self.Get_BanknoteType = Buy_proto(('Get_BanknoteType', lib))
        self.Get_CashAcceptorPollingMode = Buy_proto(('Get_CashAcceptorPollingMode', lib))
        self.Get_Poll1 = Buy_proto(('Get_Poll1', lib))
        self.Get_Poll2 = Buy_proto(('Get_Poll2', lib))
        self.Set_BanknoteType = Set_Tax1_proto(('Set_BanknoteType', lib))
        self.ReadBanknoteCount = Buy_proto(('ReadBanknoteCount', lib))
        self.Get_LDSysAdminPassword = Get_Password_proto(('Get_LDSysAdminPassword', lib))
        self.Set_LDSysAdminPassword = Set_Password_proto(('Set_LDSysAdminPassword', lib))
        self.PrintOperationalTaxReport = Buy_proto(('PrintOperationalTaxReport', lib))
        self.Get_CapOpenCheck = Get_CPLog_proto(('Get_CapOpenCheck', lib))
        self.Get_PollDescription = Get_INN_proto(('Get_PollDescription', lib))
        self.WaitConnection = Buy_proto(('WaitConnection', lib))
        self.ReadModelParamDescription = Buy_proto(('ReadModelParamDescription', lib))
        self.Get_HRIPosition = Buy_proto(('Get_HRIPosition', lib))
        self.PrintBarcodeUsingPrinter = Buy_proto(('PrintBarcodeUsingPrinter', lib))
        self.Set_HRIPosition = Set_Tax1_proto(('Set_HRIPosition', lib))
        self.Get_KPKStr = Get_INN_proto(('Get_KPKStr', lib))
        self.CloseCheckWithKPK = Buy_proto(('CloseCheckWithKPK', lib))
        self.ReadEKLZActivizationParams = Buy_proto(('ReadEKLZActivizationParams', lib))
        self.GetShortReportInDatesRange = Buy_proto(('GetShortReportInDatesRange', lib))
        self.GetShortReportInSessionRange = Buy_proto(('GetShortReportInSessionRange', lib))
        self.ReadLastReceipt = Buy_proto(('ReadLastReceipt', lib))
        self.ReadLastReceiptLine = Buy_proto(('ReadLastReceiptLine', lib))
        self.ReadLastReceiptMac = Buy_proto(('ReadLastReceiptMac', lib))
        self.Get_TextBlock = Get_INN_proto(('Get_TextBlock', lib))
        self.Get_TextBlockNumber = Buy_proto(('Get_TextBlockNumber', lib))
        self.Set_TextBlock = Set_INN_proto(('Set_TextBlock', lib))
        self.Set_TextBlockNumber = Set_Tax1_proto(('Set_TextBlockNumber', lib))
        self.BeginDocument = Buy_proto(('BeginDocument', lib))
        self.EndDocument = Buy_proto(('EndDocument', lib))
        self.Get_PosControlReceiptSeparator = Get_INN_proto(('Get_PosControlReceiptSeparator', lib))
        self.Set_PosControlReceiptSeparator = Set_INN_proto(('Set_PosControlReceiptSeparator', lib))
        self.Print2DBarcode = Buy_proto(('Print2DBarcode', lib))
        self.Set_BarcodeDataLength = Set_Tax1_proto(('Set_BarcodeDataLength', lib))
        self.LoadAndPrint2DBarcode = Buy_proto(('LoadAndPrint2DBarcode', lib))
        self.Get_ExciseCode = Buy_proto(('Get_ExciseCode', lib))
        self.Set_ExciseCode = Set_Tax1_proto(('Set_ExciseCode', lib))
        self.ExcisableOperation = Buy_proto(('ExcisableOperation', lib))
        self.ReadReportBufferLine = Buy_proto(('ReadReportBufferLine', lib))
        self.Get_SaveSettingsType = Buy_proto(('Get_SaveSettingsType', lib))
        self.Set_SaveSettingsType = Set_Tax1_proto(('Set_SaveSettingsType', lib))
        self.ReadParams = Buy_proto(('ReadParams', lib))
        self.Get_ModelNames = Get_INN_proto(('Get_ModelNames', lib))
        self.Get_ModelsCount = Buy_proto(('Get_ModelsCount', lib))
        self.Get_FMFlagsEx = Buy_proto(('Get_FMFlagsEx', lib))
        self.Get_FMMode = Buy_proto(('Get_FMMode', lib))
        self.Get_IsASPDMode = Get_CPLog_proto(('Get_IsASPDMode', lib))
        self.Get_IsCorruptedFiscalizationInfo = Get_CPLog_proto(('Get_IsCorruptedFiscalizationInfo', lib))
        self.Get_IsCorruptedFMRecords = Get_CPLog_proto(('Get_IsCorruptedFMRecords', lib))
        self.GetCashRegEx = Buy_proto(('GetCashRegEx', lib))
        self.Get_RegBuyRec = Get_Price_proto(('Get_RegBuyRec', lib))
        self.Get_RegBuyReturnRec = Get_Price_proto(('Get_RegBuyReturnRec', lib))
        self.Get_RegBuyReturnSession = Get_Price_proto(('Get_RegBuyReturnSession', lib))
        self.Get_RegBuySession = Get_Price_proto(('Get_RegBuySession', lib))
        self.Get_RegSaleRec = Get_Price_proto(('Get_RegSaleRec', lib))
        self.Get_RegSaleReturnRec = Get_Price_proto(('Get_RegSaleReturnRec', lib))
        self.Get_RegSaleReturnSession = Get_Price_proto(('Get_RegSaleReturnSession', lib))
        self.Get_RegSaleSession = Get_Price_proto(('Get_RegSaleSession', lib))
        self.GetWareBaseCashRegs = Buy_proto(('GetWareBaseCashRegs', lib))
        self.Get_WareCode = Buy_proto(('Get_WareCode', lib))
        self.Set_WareCode = Set_Tax1_proto(('Set_WareCode', lib))
        self.PrintCashierReport = Buy_proto(('PrintCashierReport', lib))
        self.PrintHourlyReport = Buy_proto(('PrintHourlyReport', lib))
        self.PrintWareReport = Buy_proto(('PrintWareReport', lib))
        self.UpdateWare = Buy_proto(('UpdateWare', lib))
        self.CheckFM = Buy_proto(('CheckFM', lib))
        self.RemoveWare = Buy_proto(('RemoveWare', lib))
        self.Get_RecordCount = Buy_proto(('Get_RecordCount', lib))
        self.Get_CheckingType = Buy_proto(('Get_CheckingType', lib))
        self.Set_CheckingType = Set_Tax1_proto(('Set_CheckingType', lib))
        self.ReadErrorDescription = Buy_proto(('ReadErrorDescription', lib))
        self.ReadLastErrorDescription = Buy_proto(('ReadLastErrorDescription', lib))
        self.ReadWare = Buy_proto(('ReadWare', lib))
        self.Get_UseWareCode = Get_CPLog_proto(('Get_UseWareCode', lib))
        self.Set_UseWareCode = Set_CPLog_proto(('Set_UseWareCode', lib))
        self.Get_RequestErrorDescription = Get_CPLog_proto(('Get_RequestErrorDescription', lib))
        self.Set_RequestErrorDescription = Set_CPLog_proto(('Set_RequestErrorDescription', lib))
        self.Get_AdjustRITimeout = Get_CPLog_proto(('Get_AdjustRITimeout', lib))
        self.Set_AdjustRITimeout = Set_CPLog_proto(('Set_AdjustRITimeout', lib))
        self.Get_UCodePageText = Get_INN_proto(('Get_UCodePageText', lib))
        self.Set_ReconnectPort = Set_CPLog_proto(('Set_ReconnectPort', lib))
        self.Get_DoNotSendENQ = Get_CPLog_proto(('Get_DoNotSendENQ', lib))
        self.Set_DoNotSendENQ = Set_CPLog_proto(('Set_DoNotSendENQ', lib))
        self.ReadModelParam = Buy_proto(('ReadModelParam', lib))
        self.InitEEPROM = Buy_proto(('InitEEPROM', lib))
        self.Get_CheckEJConnection = Get_CPLog_proto(('Get_CheckEJConnection', lib))
        self.Get_CheckFMConnection = Get_CPLog_proto(('Get_CheckFMConnection', lib))
        self.Set_CheckEJConnection = Set_CPLog_proto(('Set_CheckEJConnection', lib))
        self.Set_CheckFMConnection = Set_CPLog_proto(('Set_CheckFMConnection', lib))
        self.CheckConnection = Buy_proto(('CheckConnection', lib))
        self.ChangeProtocol = Buy_proto(('ChangeProtocol', lib))
        self.Get_LDProtocolType = Buy_proto(('Get_LDProtocolType', lib))
        self.Set_LDProtocolType = Set_Tax1_proto(('Set_LDProtocolType', lib))
        self.GetECRParams = Buy_proto(('GetECRParams', lib))
        self.ShowImportDlg = Buy_proto(('ShowImportDlg', lib))
        self.Get_LastPrintResult = Buy_proto(('Get_LastPrintResult', lib))
        self.Get_UseSlipCheck = Get_CPLog_proto(('Get_UseSlipCheck', lib))
        self.Set_UseSlipCheck = Set_CPLog_proto(('Set_UseSlipCheck', lib))
        self.Get_TypeOfLastEntryFMEx = Buy_proto(('Get_TypeOfLastEntryFMEx', lib))
        self.JournalOperation = Buy_proto(('JournalOperation', lib))
        self.Get_AutoSensorValues = Get_CPLog_proto(('Get_AutoSensorValues', lib))
        self.Set_AutoSensorValues = Set_CPLog_proto(('Set_AutoSensorValues', lib))
        self.Get_AutoStartSearch = Get_CPLog_proto(('Get_AutoStartSearch', lib))
        self.Get_SearchTimeout = Buy_proto(('Get_SearchTimeout', lib))
        self.Set_AutoStartSearch = Set_CPLog_proto(('Set_AutoStartSearch', lib))
        self.Set_SearchTimeout = Set_Tax1_proto(('Set_SearchTimeout', lib))
        self.Get_TCPConnectionTimeout = Buy_proto(('Get_TCPConnectionTimeout', lib))
        self.Set_TCPConnectionTimeout = Set_Tax1_proto(('Set_TCPConnectionTimeout', lib))
        self.MFPActivization = Buy_proto(('MFPActivization', lib))
        self.MFPCloseArchive = Buy_proto(('MFPCloseArchive', lib))
        self.MFPGetPermitActivizationCode = Buy_proto(('MFPGetPermitActivizationCode', lib))
        self.MFPGetCustomerCode = Buy_proto(('MFPGetCustomerCode', lib))
        self.MFPPrepareActivization = Buy_proto(('MFPPrepareActivization', lib))
        self.MFPSetCustomerCode = Buy_proto(('MFPSetCustomerCode', lib))
        self.MFPSetPermitActivizationCode = Buy_proto(('MFPSetPermitActivizationCode', lib))
        self.MFPGetPrepareActivizationResult = Buy_proto(('MFPGetPrepareActivizationResult', lib))
        self.CloseCheckEx = Buy_proto(('CloseCheckEx', lib))
        self.Get_CustomerCode = Buy_proto(('Get_CustomerCode', lib))
        self.Set_CustomerCode = Set_Tax1_proto(('Set_CustomerCode', lib))
        self.Get_PermitActivizationCode = Buy_proto(('Get_PermitActivizationCode', lib))
        self.Set_PermitActivizationCode = Set_Tax1_proto(('Set_PermitActivizationCode', lib))
        self.Get_ActivizationStatus = Buy_proto(('Get_ActivizationStatus', lib))
        self.Set_ActivizationStatus = Set_Tax1_proto(('Set_ActivizationStatus', lib))
        self.Get_MFPStatus = Buy_proto(('Get_MFPStatus', lib))
        self.Set_MFPStatus = Set_Tax1_proto(('Set_MFPStatus', lib))
        self.Get_KPKValue = Buy_proto(('Get_KPKValue', lib))
        self.Set_KPKValue = Set_Tax1_proto(('Set_KPKValue', lib))
        self.Get_ActivizationControlByte = Buy_proto(('Get_ActivizationControlByte', lib))
        self.Set_ActivizationControlByte = Set_Tax1_proto(('Set_ActivizationControlByte', lib))
        self.Get_PrepareActivizationRemainCount = Buy_proto(('Get_PrepareActivizationRemainCount', lib))
        self.Set_PrepareActivizationRemainCount = Set_Tax1_proto(('Set_PrepareActivizationRemainCount', lib))
        self.Get_AnswerCode = Buy_proto(('Get_AnswerCode', lib))
        self.Set_AnswerCode = Set_Tax1_proto(('Set_AnswerCode', lib))
        self.GetMFPCode3Status = Buy_proto(('GetMFPCode3Status', lib))
        self.Get_MFPNumber = Get_INN_proto(('Get_MFPNumber', lib))
        self.Set_MFPNumber = Set_INN_proto(('Set_MFPNumber', lib))
        self.Get_ReadTimeout = Buy_proto(('Get_ReadTimeout', lib))
        self.Set_ReadTimeout = Set_Tax1_proto(('Set_ReadTimeout', lib))
        self.ClearReportBuffer = Buy_proto(('ClearReportBuffer', lib))
        self.Get_IsBlockedByWrongTaxPassword = Get_CPLog_proto(('Get_IsBlockedByWrongTaxPassword', lib))
        self.Get_LastFMRecordType = Buy_proto(('Get_LastFMRecordType', lib))
        self.ShowAdditionalParams = Buy_proto(('ShowAdditionalParams', lib))
        self.Get_CloudCashdeskEnabled = Get_CPLog_proto(('Get_CloudCashdeskEnabled', lib))
        self.Get_ECRID = Get_INN_proto(('Get_ECRID', lib))
        self.Set_CloudCashdeskEnabled = Set_CPLog_proto(('Set_CloudCashdeskEnabled', lib))
        self.Set_ECRID = Set_INN_proto(('Set_ECRID', lib))
        self.GetCloudCashdeskParams = Buy_proto(('GetCloudCashdeskParams', lib))
        self.Get_KSAInfo = Get_INN_proto(('Get_KSAInfo', lib))
        self.Set_KSAInfo = Set_INN_proto(('Set_KSAInfo', lib))
        self.DrawScale = Buy_proto(('DrawScale', lib))
        self.Get_BarcodeFirstLine = Buy_proto(('Get_BarcodeFirstLine', lib))
        self.Set_BarcodeFirstLine = Set_Tax1_proto(('Set_BarcodeFirstLine', lib))
        self.Get_SKNOError = Buy_proto(('Get_SKNOError', lib))
        self.Set_SKNOError = Set_Tax1_proto(('Set_SKNOError', lib))
        self.Get_SKNOIdentifier = Get_INN_proto(('Get_SKNOIdentifier', lib))
        self.Set_SKNOIdentifier = Set_INN_proto(('Set_SKNOIdentifier', lib))
        self.LoadGraphics512 = Buy_proto(('LoadGraphics512', lib))
        self.PrintGraphics512 = Buy_proto(('PrintGraphics512', lib))
        self.Get_SyncTimeout = Buy_proto(('Get_SyncTimeout', lib))
        self.Set_SyncTimeout = Set_Tax1_proto(('Set_SyncTimeout', lib))
        self.FNGetExpirationTime = Buy_proto(('FNGetExpirationTime', lib))
        self.FNGetSerial = Buy_proto(('FNGetSerial', lib))
        self.FNGetStatus = Buy_proto(('FNGetStatus', lib))
        self.FNGetVersion = Buy_proto(('FNGetVersion', lib))
        self.FNBeginFiscalization = Buy_proto(('FNBeginFiscalization', lib))
        self.FNFiscalization = Buy_proto(('FNFiscalization', lib))
        self.FNCancelDocument = Buy_proto(('FNCancelDocument', lib))
        self.FNResetState = Buy_proto(('FNResetState', lib))
        self.FNFindDocument = Buy_proto(('FNFindDocument', lib))
        self.Get_DocumentData = Get_INN_proto(('Get_DocumentData', lib))
        self.Set_DocumentData = Set_INN_proto(('Set_DocumentData', lib))
        self.FNOpenSession = Buy_proto(('FNOpenSession', lib))
        self.FNSendTLV = Buy_proto(('FNSendTLV', lib))
        self.FNDiscountOperation = Buy_proto(('FNDiscountOperation', lib))
        self.FNStorno = Buy_proto(('FNStorno', lib))
        self.OFDExchange = Buy_proto(('OFDExchange', lib))
        self.Get_OFDEnabled = Get_CPLog_proto(('Get_OFDEnabled', lib))
        self.Set_OFDEnabled = Set_CPLog_proto(('Set_OFDEnabled', lib))
        self.FNBeginCalculationStateReport = Buy_proto(('FNBeginCalculationStateReport', lib))
        self.FNBeginCloseFiscalMode = Buy_proto(('FNBeginCloseFiscalMode', lib))
        self.FNBeginCloseSession = Buy_proto(('FNBeginCloseSession', lib))
        self.FNBeginCorrectionReceipt = Buy_proto(('FNBeginCorrectionReceipt', lib))
        self.FNBeginOpenSession = Buy_proto(('FNBeginOpenSession', lib))
        self.FNBeginRegistrationReport = Buy_proto(('FNBeginRegistrationReport', lib))
        self.FNBuildCalculationStateReport = Buy_proto(('FNBuildCalculationStateReport', lib))
        self.FNBuildCorrectionReceipt = Buy_proto(('FNBuildCorrectionReceipt', lib))
        self.FNBuildRegistrationReport = Buy_proto(('FNBuildRegistrationReport', lib))
        self.FNCloseFiscalMode = Buy_proto(('FNCloseFiscalMode', lib))
        self.FNCloseSession = Buy_proto(('FNCloseSession', lib))
        self.FNGetCurrentSessionParams = Buy_proto(('FNGetCurrentSessionParams', lib))
        self.FNGetInfoExchangeStatus = Buy_proto(('FNGetInfoExchangeStatus', lib))
        self.FNGetOFDTicketByDocNumber = Buy_proto(('FNGetOFDTicketByDocNumber', lib))
        self.FNGetUnconfirmedDocCount = Buy_proto(('FNGetUnconfirmedDocCount', lib))
        self.FNReadFiscalDocumentTLV = Buy_proto(('FNReadFiscalDocumentTLV', lib))
        self.FNRequestFiscalDocumentTLV = Buy_proto(('FNRequestFiscalDocumentTLV', lib))
        self.FNBuildReregistrationReport = Buy_proto(('FNBuildReregistrationReport', lib))
        self.FNGetFiscalizationResult = Buy_proto(('FNGetFiscalizationResult', lib))
        self.FNDiscountTaxOperation = Buy_proto(('FNDiscountTaxOperation', lib))
        self.FNCloseCheckEx = Buy_proto(('FNCloseCheckEx', lib))
        self.Get_ChargeValue = Get_Price_proto(('Get_ChargeValue', lib))
        self.Get_DiscountValue = Get_Price_proto(('Get_DiscountValue', lib))
        self.Set_ChargeValue = Set_Price_proto(('Set_ChargeValue', lib))
        self.Set_DiscountValue = Set_Price_proto(('Set_DiscountValue', lib))
        self.Get_DiscountName = Get_INN_proto(('Get_DiscountName', lib))
        self.Set_DiscountName = Set_INN_proto(('Set_DiscountName', lib))
        self.FNSendCustomerEmail = Buy_proto(('FNSendCustomerEmail', lib))
        self.Annulment = Buy_proto(('Annulment', lib))
        self.FNDiscountChargeRN = Buy_proto(('FNDiscountChargeRN', lib))
        self.ExportTables = Buy_proto(('ExportTables', lib))
        self.ImportTables = Buy_proto(('ImportTables', lib))
        self.FNSendTag = Buy_proto(('FNSendTag', lib))
        self.ReadSerialNumber = Buy_proto(('ReadSerialNumber', lib))
        self.FNPrintOperatorConfirm = Buy_proto(('FNPrintOperatorConfirm', lib))
        self.FNGetFiscalizationResultByNumber = Buy_proto(('FNGetFiscalizationResultByNumber', lib))
        self.AnnulmentRB = Buy_proto(('AnnulmentRB', lib))
        self.FNGetTagDescription = Buy_proto(('FNGetTagDescription', lib))
        self.Get_TagDescription = Get_INN_proto(('Get_TagDescription', lib))
        self.Set_TagDescription = Set_INN_proto(('Set_TagDescription', lib))
        self.FNPrintDocument = Buy_proto(('FNPrintDocument', lib))
        self.FNGetDocumentAsString = Buy_proto(('FNGetDocumentAsString', lib))
        self.Ping = Buy_proto(('Ping', lib))
        self.Get_URL = Get_INN_proto(('Get_URL', lib))
        self.Set_URL = Set_INN_proto(('Set_URL', lib))
        self.Get_PingTime = Buy_proto(('Get_PingTime', lib))
        self.Set_PingTime = Set_Tax1_proto(('Set_PingTime', lib))
        self.Get_PingResult = Buy_proto(('Get_PingResult', lib))
        self.Set_PingResult = Set_Tax1_proto(('Set_PingResult', lib))
        self.Get_ICSEnabled = Get_CPLog_proto(('Get_ICSEnabled', lib))
        self.Get_ICSPollPeriod = Buy_proto(('Get_ICSPollPeriod', lib))
        self.Set_ICSEnabled = Set_CPLog_proto(('Set_ICSEnabled', lib))
        self.Set_ICSPollPeriod = Set_Tax1_proto(('Set_ICSPollPeriod', lib))
        self.FNOperation = Buy_proto(('FNOperation', lib))
        self.FNSendTLVOperation = Buy_proto(('FNSendTLVOperation', lib))
        self.Get_TaxValue1Enabled = Get_CPLog_proto(('Get_TaxValue1Enabled', lib))
        self.Get_TaxValue2Enabled = Get_CPLog_proto(('Get_TaxValue2Enabled', lib))
        self.Get_TaxValue3Enabled = Get_CPLog_proto(('Get_TaxValue3Enabled', lib))
        self.Get_TaxValue4Enabled = Get_CPLog_proto(('Get_TaxValue4Enabled', lib))
        self.Get_TaxValue5Enabled = Get_CPLog_proto(('Get_TaxValue5Enabled', lib))
        self.Get_TaxValue6Enabled = Get_CPLog_proto(('Get_TaxValue6Enabled', lib))
        self.Set_TaxValue1Enabled = Set_CPLog_proto(('Set_TaxValue1Enabled', lib))
        self.Set_TaxValue2Enabled = Set_CPLog_proto(('Set_TaxValue2Enabled', lib))
        self.Set_TaxValue3Enabled = Set_CPLog_proto(('Set_TaxValue3Enabled', lib))
        self.Set_TaxValue4Enabled = Set_CPLog_proto(('Set_TaxValue4Enabled', lib))
        self.Set_TaxValue5Enabled = Set_CPLog_proto(('Set_TaxValue5Enabled', lib))
        self.Set_TaxValue6Enabled = Set_CPLog_proto(('Set_TaxValue6Enabled', lib))
        self.FNBuildCorrectionReceipt2 = Buy_proto(('FNBuildCorrectionReceipt2', lib))
        self.Get_OFDReadTimeout = Buy_proto(('Get_OFDReadTimeout', lib))
        self.Set_OFDReadTimeout = Set_Tax1_proto(('Set_OFDReadTimeout', lib))
        self.FNGetNonClearableSumm = Buy_proto(('FNGetNonClearableSumm', lib))
        self.ResetSerialNumber = Buy_proto(('ResetSerialNumber', lib))
        self.DBFindDocument = Buy_proto(('DBFindDocument', lib))
        self.Get_DBFilePath = Get_INN_proto(('Get_DBFilePath', lib))
        self.Set_DBFilePath = Set_INN_proto(('Set_DBFilePath', lib))
        self.DBPrintDocument = Buy_proto(('DBPrintDocument', lib))
        self.Get_KKTLicense = Buy_proto(('Get_KKTLicense', lib))
        self.Get_LicenseNumber = Buy_proto(('Get_LicenseNumber', lib))
        self.Get_PUKCode = Buy_proto(('Get_PUKCode', lib))
        self.ReadKKTLicenses = Buy_proto(('ReadKKTLicenses', lib))
        self.Set_KKTLicense = Set_Tax1_proto(('Set_KKTLicense', lib))
        self.Set_LicenseNumber = Set_Tax1_proto(('Set_LicenseNumber', lib))
        self.Set_PUKCode = Set_Tax1_proto(('Set_PUKCode', lib))
        self.Get_OFDExchangeSuspended = Get_CPLog_proto(('Get_OFDExchangeSuspended', lib))
        self.Set_OFDExchangeSuspended = Set_CPLog_proto(('Set_OFDExchangeSuspended', lib))
        self.CloseCheckBel = Buy_proto(('CloseCheckBel', lib))
        self.GetKKTLicenseByNumber = Buy_proto(('GetKKTLicenseByNumber', lib))
        self.WriteKKTLicense = Buy_proto(('WriteKKTLicense', lib))
        self.FNSendSenderEmail = Buy_proto(('FNSendSenderEmail', lib))
        self.Get_Discount1 = Get_Price_proto(('Get_Discount1', lib))
        self.Get_Discount2 = Get_Price_proto(('Get_Discount2', lib))
        self.Get_Discount3 = Get_Price_proto(('Get_Discount3', lib))
        self.Get_Discount4 = Get_Price_proto(('Get_Discount4', lib))
        self.Get_UseTaxDiscountBel = Get_CPLog_proto(('Get_UseTaxDiscountBel', lib))
        self.Set_Discount1 = Set_Price_proto(('Set_Discount1', lib))
        self.Set_Discount2 = Set_Price_proto(('Set_Discount2', lib))
        self.Set_Discount3 = Set_Price_proto(('Set_Discount3', lib))
        self.Set_Discount4 = Set_Price_proto(('Set_Discount4', lib))
        self.Set_UseTaxDiscountBel = Set_CPLog_proto(('Set_UseTaxDiscountBel', lib))
        self.Get_Summ1AsString = Get_INN_proto(('Get_Summ1AsString', lib))
        self.Get_Summ2AsString = Get_INN_proto(('Get_Summ2AsString', lib))
        self.Get_Summ3AsString = Get_INN_proto(('Get_Summ3AsString', lib))
        self.Get_Summ4AsString = Get_INN_proto(('Get_Summ4AsString', lib))
        self.DBGetNextDocument = Buy_proto(('DBGetNextDocument', lib))
        self.DBPrintNextDocument = Buy_proto(('DBPrintNextDocument', lib))
        self.DBQueryDocumentsInSession = Buy_proto(('DBQueryDocumentsInSession', lib))
        self.Get_DBDocType = Buy_proto(('Get_DBDocType', lib))
        self.Set_DBDocType = Set_Tax1_proto(('Set_DBDocType', lib))
        self.Get_OPBarcodeInputType = Buy_proto(('Get_OPBarcodeInputType', lib))
        self.Get_OPIdPayment = Get_INN_proto(('Get_OPIdPayment', lib))
        self.Get_OPRequisiteNumber = Buy_proto(('Get_OPRequisiteNumber', lib))
        self.Get_OPRequisiteValue = Get_INN_proto(('Get_OPRequisiteValue', lib))
        self.Get_OPSystem = Buy_proto(('Get_OPSystem', lib))
        self.Get_OPTransactionStatus = Buy_proto(('Get_OPTransactionStatus', lib))
        self.Get_OPTransactionType = Buy_proto(('Get_OPTransactionType', lib))
        self.OnlinePay = Buy_proto(('OnlinePay', lib))
        self.OPGetLastRequisite = Buy_proto(('OPGetLastRequisite', lib))
        self.OPGetLastStatus = Buy_proto(('OPGetLastStatus', lib))
        self.Set_OPBarcodeInputType = Set_Tax1_proto(('Set_OPBarcodeInputType', lib))
        self.Set_OPIdPayment = Set_INN_proto(('Set_OPIdPayment', lib))
        self.Set_OPRequisiteNumber = Set_Tax1_proto(('Set_OPRequisiteNumber', lib))
        self.Set_OPRequisiteValue = Set_INN_proto(('Set_OPRequisiteValue', lib))
        self.Set_OPSystem = Set_Tax1_proto(('Set_OPSystem', lib))
        self.Set_OPTransactionStatus = Set_Tax1_proto(('Set_OPTransactionStatus', lib))
        self.Set_OPTransactionType = Set_Tax1_proto(('Set_OPTransactionType', lib))
        self.Get_Token = Get_INN_proto(('Get_Token', lib))
        self.GenerateMonoToken = Buy_proto(('GenerateMonoToken', lib))
        self.Set_Token = Set_INN_proto(('Set_Token', lib))
        self.RebootKKT = Buy_proto(('RebootKKT', lib))
        self.FNAddTag = Buy_proto(('FNAddTag', lib))
        self.FNBeginSTLVTag = Buy_proto(('FNBeginSTLVTag', lib))
        self.FNSendSTLVTag = Buy_proto(('FNSendSTLVTag', lib))
        self.FNSendSTLVTagOperation = Buy_proto(('FNSendSTLVTagOperation', lib))
        self.FNSendTagOperation = Buy_proto(('FNSendTagOperation', lib))
        self.Get_SymbolCode = Buy_proto(('Get_SymbolCode', lib))
        self.Set_SymbolCode = Set_Tax1_proto(('Set_SymbolCode', lib))
        self.Get_SymbolWidth = Buy_proto(('Get_SymbolWidth', lib))
        self.Set_SymbolWidth = Set_Tax1_proto(('Set_SymbolWidth', lib))
        self.Get_SymbolHeight = Buy_proto(('Get_SymbolHeight', lib))
        self.Set_SymbolHeight = Set_Tax1_proto(('Set_SymbolHeight', lib))
        self.Get_FileType = Buy_proto(('Get_FileType', lib))
        self.Set_FileType = Set_Tax1_proto(('Set_FileType', lib))
        self.Get_DelayOnDisconnect = Buy_proto(('Get_DelayOnDisconnect', lib))
        self.Set_DelayOnDisconnect = Set_Tax1_proto(('Set_DelayOnDisconnect', lib))
        self.Set_GTIN = Set_INN_proto(('Set_GTIN', lib))
        self.Get_GTIN = Get_INN_proto(('Get_GTIN', lib))
        self.FNSendItemCodeData = Buy_proto(('FNSendItemCodeData', lib))
        self.FNCheckItemBarcode = Buy_proto(('FNCheckItemBarcode', lib))
        self.FNRequestRegistrationTLV = Buy_proto(('FNRequestRegistrationTLV', lib))
        self.ReadLoaderVersion = Buy_proto(('ReadLoaderVersion', lib))
        self.Get_RequestDocumentType = Buy_proto(('Get_RequestDocumentType', lib))
        self.Set_RequestDocumentType = Set_Tax1_proto(('Set_RequestDocumentType', lib))
        self.FNOpenCheckCorrection = Buy_proto(('FNOpenCheckCorrection', lib))
        self.FNCountersSync = Buy_proto(('FNCountersSync', lib))
        self.FNGetFreeMemoryResource = Buy_proto(('FNGetFreeMemoryResource', lib))
        self.ReadCashDrawerSum = Buy_proto(('ReadCashDrawerSum', lib))
        self.ReadFeatureLicenses = Buy_proto(('ReadFeatureLicenses', lib))
        self.WriteFeatureLicenses = Buy_proto(('WriteFeatureLicenses', lib))
        self.SetDeviceFunction = Buy_proto(('SetDeviceFunction', lib))
        self.GetDeviceFunction = Buy_proto(('GetDeviceFunction', lib))
        self.FNSendItemBarcode = Buy_proto(('FNSendItemBarcode', lib))
        self.FNGetKMServerExchangeStatus = Buy_proto(('FNGetKMServerExchangeStatus', lib))
        self.FNGetMarkingCodeWorkStatus = Buy_proto(('FNGetMarkingCodeWorkStatus', lib))
        self.FNBeginReadNotifications = Buy_proto(('FNBeginReadNotifications', lib))
        self.FNReadNotificationBlock = Buy_proto(('FNReadNotificationBlock', lib))
        self.FNConfirmNotificationRead = Buy_proto(('FNConfirmNotificationRead', lib))
        self.GetTagAsTLV = Buy_proto(('GetTagAsTLV', lib))
        self.ReadRandomSequence = Buy_proto(('ReadRandomSequence', lib))
        self.Authorization = Buy_proto(('Authorization', lib))
        self.FNAcceptMarkingCode = Buy_proto(('FNAcceptMarkingCode', lib))
        self.FNDeclineMarkingCode = Buy_proto(('FNDeclineMarkingCode', lib))
        self.FNMarkingClearBuffer = Buy_proto(('FNMarkingClearBuffer', lib))
        self.FNBindMarkingItem = Buy_proto(('FNBindMarkingItem', lib))
        self.FNBeginReadArchive = Buy_proto(('FNBeginReadArchive', lib))
        self.FNReadArchiveItem = Buy_proto(('FNReadArchiveItem', lib))
        self.FNSaveArchive = Buy_proto(('FNSaveArchive', lib))
        self.Set_LastDocumentNumber = Set_Tax1_proto(('Set_LastDocumentNumber', lib))
        self.Get_LastDocumentNumber = Buy_proto(('Get_LastDocumentNumber', lib))
        self.Set_FirstDocumentNumber = Set_Tax1_proto(('Set_FirstDocumentNumber', lib))
        self.Get_FirstDocumentNumber = Buy_proto(('Get_FirstDocumentNumber', lib))
        self.FNSendUserAttribute = Buy_proto(('FNSendUserAttribute', lib))
        self.RenderDeclarativeDocument = Buy_proto(('RenderDeclarativeDocument', lib))
        self.LoadFont = Buy_proto(('LoadFont', lib))
        self.ReadFontHash = Buy_proto(('ReadFontHash', lib))
        self.ResetFont = Buy_proto(('ResetFont', lib))
        self.LoadFontSymbol = Buy_proto(('LoadFontSymbol', lib))
        self.DecodeTLVData = Buy_proto(('DecodeTLVData', lib))
        self.FNGetImplementation = Buy_proto(('FNGetImplementation', lib))
        self.FNGetOSUSupportStatus = Buy_proto(('FNGetOSUSupportStatus', lib))
        self.FNGetDocumentSize = Buy_proto(('FNGetDocumentSize', lib))
        self.FNReadFiscalBarcode = Buy_proto(('FNReadFiscalBarcode', lib))
        self.PrintStringWithWrap = Buy_proto(('PrintStringWithWrap', lib))
        self.Get_BarCode = Get_INN_proto(('Get_BarCode', lib))
        self.Set_BarCode = Set_INN_proto(('Set_BarCode', lib))
        self.Get_BatteryVoltage = Get_Quantity_proto(('Get_BatteryVoltage', lib))
        self.Get_BaudRate = Buy_proto(('Get_BaudRate', lib))
        self.Set_BaudRate = Set_Tax1_proto(('Set_BaudRate', lib))
        self.Get_Change = Get_Price_proto(('Get_Change', lib))
        self.Get_CheckType = Buy_proto(('Get_CheckType', lib))
        self.Set_CheckType = Set_Tax1_proto(('Set_CheckType', lib))
        self.Get_ComNumber = Buy_proto(('Get_ComNumber', lib))
        self.Set_ComNumber = Set_Tax1_proto(('Set_ComNumber', lib))
        self.Get_ContentsOfCashRegister = Get_Price_proto(('Get_ContentsOfCashRegister', lib))
        self.Get_ContentsOfOperationRegister = Buy_proto(('Get_ContentsOfOperationRegister', lib))
        self.Get_CutType = Get_CPLog_proto(('Get_CutType', lib))
        self.Set_CutType = Set_CPLog_proto(('Set_CutType', lib))
        self.Get_DataBlock = Get_INN_proto(('Get_DataBlock', lib))
        self.Get_DataBlockHex = Get_INN_proto(('Get_DataBlockHex', lib))
        self.Get_DataBlockNumber = Buy_proto(('Get_DataBlockNumber', lib))
        self.Get_Date = Get_Date_proto(('Get_Date', lib))
        self.Set_Date = Set_Date_proto(('Set_Date', lib))
        self.Get_Department = Buy_proto(('Get_Department', lib))
        self.Set_Department = Set_Tax1_proto(('Set_Department', lib))
        self.Get_DeviceCode = Buy_proto(('Get_DeviceCode', lib))
        self.Set_DeviceCode = Set_Tax1_proto(('Set_DeviceCode', lib))
        self.Get_DeviceCodeDescription = Get_INN_proto(('Get_DeviceCodeDescription', lib))
        self.Get_DiscountOnCheck = Get_Quantity_proto(('Get_DiscountOnCheck', lib))
        self.Set_DiscountOnCheck = Set_Quantity_proto(('Set_DiscountOnCheck', lib))
        self.Get_DocumentName = Get_INN_proto(('Get_DocumentName', lib))
        self.Set_DocumentName = Set_INN_proto(('Set_DocumentName', lib))
        self.Get_DocumentNumber = Get_Password_proto(('Get_DocumentNumber', lib))
        self.Set_DocumentNumber = Set_Password_proto(('Set_DocumentNumber', lib))
        self.Get_DrawerNumber = Buy_proto(('Get_DrawerNumber', lib))
        self.Set_DrawerNumber = Set_Tax1_proto(('Set_DrawerNumber', lib))
        self.Get_ECRAdvancedMode = Buy_proto(('Get_ECRAdvancedMode', lib))
        self.Get_ECRBuild = Buy_proto(('Get_ECRBuild', lib))
        self.Get_ECRFlags = Buy_proto(('Get_ECRFlags', lib))
        self.Get_ReceiptRibbonIsPresent = Get_CPLog_proto(('Get_ReceiptRibbonIsPresent', lib))
        self.Get_JournalRibbonIsPresent = Get_CPLog_proto(('Get_JournalRibbonIsPresent', lib))
        self.Get_SlipDocumentIsPresent = Get_CPLog_proto(('Get_SlipDocumentIsPresent', lib))
        self.Get_SlipDocumentIsMoving = Get_CPLog_proto(('Get_SlipDocumentIsMoving', lib))
        self.Get_PointPosition = Get_CPLog_proto(('Get_PointPosition', lib))
        self.Set_PointPosition = Set_CPLog_proto(('Set_PointPosition', lib))
        self.Get_EKLZIsPresent = Get_CPLog_proto(('Get_EKLZIsPresent', lib))
        self.Get_JournalRibbonOpticalSensor = Get_CPLog_proto(('Get_JournalRibbonOpticalSensor', lib))
        self.Get_ReceiptRibbonOpticalSensor = Get_CPLog_proto(('Get_ReceiptRibbonOpticalSensor', lib))
        self.Get_JournalRibbonLever = Get_CPLog_proto(('Get_JournalRibbonLever', lib))
        self.Get_ReceiptRibbonLever = Get_CPLog_proto(('Get_ReceiptRibbonLever', lib))
        self.Get_LidPositionSensor = Get_CPLog_proto(('Get_LidPositionSensor', lib))
        self.Get_IsDrawerOpen = Get_CPLog_proto(('Get_IsDrawerOpen', lib))
        self.Get_IsPrinterRightSensorFailure = Get_CPLog_proto(('Get_IsPrinterRightSensorFailure', lib))
        self.Get_IsPrinterLeftSensorFailure = Get_CPLog_proto(('Get_IsPrinterLeftSensorFailure', lib))
        self.Get_IsEKLZOverflow = Get_CPLog_proto(('Get_IsEKLZOverflow', lib))
        self.Get_QuantityPointPosition = Get_CPLog_proto(('Get_QuantityPointPosition', lib))
        self.Get_SKNOStatus = Buy_proto(('Get_SKNOStatus', lib))
        self.Set_SKNOStatus = Set_Tax1_proto(('Set_SKNOStatus', lib))
        self.Get_ECRMode = Buy_proto(('Get_ECRMode', lib))
        self.Get_ECRMode8Status = Buy_proto(('Get_ECRMode8Status', lib))
        self.Get_ECRModeDescription = Get_INN_proto(('Get_ECRModeDescription', lib))
        self.Get_ECRSoftDate = Get_Date_proto(('Get_ECRSoftDate', lib))
        self.Get_ECRSoftVersion = Get_INN_proto(('Get_ECRSoftVersion', lib))
        self.Get_FieldName = Get_INN_proto(('Get_FieldName', lib))
        self.Get_FieldNumber = Buy_proto(('Get_FieldNumber', lib))
        self.Set_FieldNumber = Set_Tax1_proto(('Set_FieldNumber', lib))
        self.Get_FieldSize = Buy_proto(('Get_FieldSize', lib))
        self.Get_FieldType = Get_CPLog_proto(('Get_FieldType', lib))
        self.Get_FirstLineNumber = Buy_proto(('Get_FirstLineNumber', lib))
        self.Set_FirstLineNumber = Set_Tax1_proto(('Set_FirstLineNumber', lib))
        self.Get_FirstSessionDate = Get_Date_proto(('Get_FirstSessionDate', lib))
        self.Set_FirstSessionDate = Set_Date_proto(('Set_FirstSessionDate', lib))
        self.Get_FirstSessionNumber = Buy_proto(('Get_FirstSessionNumber', lib))
        self.Set_FirstSessionNumber = Set_Tax1_proto(('Set_FirstSessionNumber', lib))
        self.Get_FMBuild = Buy_proto(('Get_FMBuild', lib))
        self.Get_FMFlags = Buy_proto(('Get_FMFlags', lib))
        self.Get_FM1IsPresent = Get_CPLog_proto(('Get_FM1IsPresent', lib))
        self.Get_FM2IsPresent = Get_CPLog_proto(('Get_FM2IsPresent', lib))
        self.Get_LicenseIsPresent = Get_CPLog_proto(('Get_LicenseIsPresent', lib))
        self.Get_FMOverflow = Get_CPLog_proto(('Get_FMOverflow', lib))
        self.Get_IsBatteryLow = Get_CPLog_proto(('Get_IsBatteryLow', lib))
        self.Get_IsLastFMRecordCorrupted = Get_CPLog_proto(('Get_IsLastFMRecordCorrupted', lib))
        self.Get_IsFMSessionOpen = Get_CPLog_proto(('Get_IsFMSessionOpen', lib))
        self.Get_IsFM24HoursOver = Get_CPLog_proto(('Get_IsFM24HoursOver', lib))
        self.Get_FMSoftDate = Get_Date_proto(('Get_FMSoftDate', lib))
        self.Get_FMSoftVersion = Get_INN_proto(('Get_FMSoftVersion', lib))
        self.Get_FreeRecordInFM = Buy_proto(('Get_FreeRecordInFM', lib))
        self.Get_FreeRegistration = Buy_proto(('Get_FreeRegistration', lib))
        self.Get_INN = Get_INN_proto(('Get_INN', lib))
        self.Set_INN = Set_INN_proto(('Set_INN', lib))
        self.Get_LastLineNumber = Buy_proto(('Get_LastLineNumber', lib))
        self.Set_LastLineNumber = Set_Tax1_proto(('Set_LastLineNumber', lib))
        self.Get_LastSessionDate = Get_Date_proto(('Get_LastSessionDate', lib))
        self.Set_LastSessionDate = Set_Date_proto(('Set_LastSessionDate', lib))
        self.Get_LastSessionNumber = Buy_proto(('Get_LastSessionNumber', lib))
        self.Set_LastSessionNumber = Set_Tax1_proto(('Set_LastSessionNumber', lib))
        self.Get_License = Get_INN_proto(('Get_License', lib))
        self.Set_License = Set_INN_proto(('Set_License', lib))
        self.Get_LineData = Get_INN_proto(('Get_LineData', lib))
        self.Set_LineData = Set_INN_proto(('Set_LineData', lib))
        self.Get_LineNumber = Buy_proto(('Get_LineNumber', lib))
        self.Set_LineNumber = Set_Tax1_proto(('Set_LineNumber', lib))
        self.Get_LogicalNumber = Buy_proto(('Get_LogicalNumber', lib))
        self.Get_MAXValueOfField = Buy_proto(('Get_MAXValueOfField', lib))
        self.Get_MINValueOfField = Buy_proto(('Get_MINValueOfField', lib))
        self.Get_NameCashReg = Get_INN_proto(('Get_NameCashReg', lib))
        self.Get_NameOperationReg = Get_INN_proto(('Get_NameOperationReg', lib))
        self.Get_NewPasswordTI = Get_Password_proto(('Get_NewPasswordTI', lib))
        self.Set_NewPasswordTI = Set_Password_proto(('Set_NewPasswordTI', lib))
        self.Get_OpenDocumentNumber = Buy_proto(('Get_OpenDocumentNumber', lib))
        self.Get_OperatorNumber = Buy_proto(('Get_OperatorNumber', lib))
        self.Get_Password = Get_Password_proto(('Get_Password', lib))
        self.Set_Password = Set_Password_proto(('Set_Password', lib))
        self.Get_PortNumber = Buy_proto(('Get_PortNumber', lib))
        self.Set_PortNumber = Set_Tax1_proto(('Set_PortNumber', lib))
        self.Get_Price = Get_Price_proto(('Get_Price', lib))
        self.Set_Price = Set_Price_proto(('Set_Price', lib))
        self.Get_Quantity = Get_Quantity_proto(('Get_Quantity', lib))
        self.Set_Quantity = Set_Quantity_proto(('Set_Quantity', lib))
        self.Get_QuantityOfOperations = Buy_proto(('Get_QuantityOfOperations', lib))
        self.Get_RegisterNumber = Buy_proto(('Get_RegisterNumber', lib))
        self.Set_RegisterNumber = Set_Tax1_proto(('Set_RegisterNumber', lib))
        self.Get_RegistrationNumber = Buy_proto(('Get_RegistrationNumber', lib))
        self.Set_RegistrationNumber = Set_Tax1_proto(('Set_RegistrationNumber', lib))
        self.Get_ReportType = Get_CPLog_proto(('Get_ReportType', lib))
        self.Set_ReportType = Set_CPLog_proto(('Set_ReportType', lib))
        self.Get_ResultCode = Buy_proto(('Get_ResultCode', lib))
        self.Get_ResultCodeDescription = Get_INN_proto(('Get_ResultCodeDescription', lib))
        self.Get_RNM = Get_INN_proto(('Get_RNM', lib))
        self.Set_RNM = Set_INN_proto(('Set_RNM', lib))
        self.Get_RowNumber = Buy_proto(('Get_RowNumber', lib))
        self.Set_RowNumber = Set_Tax1_proto(('Set_RowNumber', lib))
        self.Get_RunningPeriod = Buy_proto(('Get_RunningPeriod', lib))
        self.Set_RunningPeriod = Set_Tax1_proto(('Set_RunningPeriod', lib))
        self.Get_SerialNumber = Get_INN_proto(('Get_SerialNumber', lib))
        self.Set_SerialNumber = Set_INN_proto(('Set_SerialNumber', lib))
        self.Get_SessionNumber = Buy_proto(('Get_SessionNumber', lib))
        self.Set_SessionNumber = Set_Tax1_proto(('Set_SessionNumber', lib))
        self.Get_StringForPrinting = Get_INN_proto(('Get_StringForPrinting', lib))
        self.Set_StringForPrinting = Set_INN_proto(('Set_StringForPrinting', lib))
        self.Get_StringQuantity = Buy_proto(('Get_StringQuantity', lib))
        self.Set_StringQuantity = Set_Tax1_proto(('Set_StringQuantity', lib))
        self.Get_Summ1 = Get_Price_proto(('Get_Summ1', lib))
        self.Set_Summ1 = Set_Price_proto(('Set_Summ1', lib))
        self.Get_Summ2 = Get_Price_proto(('Get_Summ2', lib))
        self.Set_Summ2 = Set_Price_proto(('Set_Summ2', lib))
        self.Get_Summ3 = Get_Price_proto(('Get_Summ3', lib))
        self.Set_Summ3 = Set_Price_proto(('Set_Summ3', lib))
        self.Get_Summ4 = Get_Price_proto(('Get_Summ4', lib))
        self.Set_Summ4 = Set_Price_proto(('Set_Summ4', lib))
        self.Get_TableName = Get_INN_proto(('Get_TableName', lib))
        self.Get_TableNumber = Buy_proto(('Get_TableNumber', lib))
        self.Set_TableNumber = Set_Tax1_proto(('Set_TableNumber', lib))
        self.Get_Tax1 = Buy_proto(('Get_Tax1', lib))
        self.Set_Tax1 = Set_Tax1_proto(('Set_Tax1', lib))
        self.Get_Tax2 = Buy_proto(('Get_Tax2', lib))
        self.Set_Tax2 = Set_Tax1_proto(('Set_Tax2', lib))
        self.Get_Tax3 = Buy_proto(('Get_Tax3', lib))
        self.Set_Tax3 = Set_Tax1_proto(('Set_Tax3', lib))
        self.Get_Tax4 = Buy_proto(('Get_Tax4', lib))
        self.Set_Tax4 = Set_Tax1_proto(('Set_Tax4', lib))
        self.Get_Time = Get_Date_proto(('Get_Time', lib))
        self.Set_Time = Set_Date_proto(('Set_Time', lib))
        self.Get_Timeout = Buy_proto(('Get_Timeout', lib))
        self.Set_Timeout = Set_Tax1_proto(('Set_Timeout', lib))
        self.Get_TimeStr = Get_INN_proto(('Get_TimeStr', lib))
        self.Set_TimeStr = Set_INN_proto(('Set_TimeStr', lib))
        self.Get_TransferBytes = Get_INN_proto(('Get_TransferBytes', lib))
        self.Set_TransferBytes = Set_INN_proto(('Set_TransferBytes', lib))
        self.Get_TypeOfLastEntryFM = Get_CPLog_proto(('Get_TypeOfLastEntryFM', lib))
        self.Get_TypeOfSumOfEntriesFM = Get_CPLog_proto(('Get_TypeOfSumOfEntriesFM', lib))
        self.Set_TypeOfSumOfEntriesFM = Set_CPLog_proto(('Set_TypeOfSumOfEntriesFM', lib))
        self.Get_UCodePage = Buy_proto(('Get_UCodePage', lib))
        self.Get_UDescription = Get_INN_proto(('Get_UDescription', lib))
        self.Get_UMajorProtocolVersion = Buy_proto(('Get_UMajorProtocolVersion', lib))
        self.Get_UMajorType = Buy_proto(('Get_UMajorType', lib))
        self.Get_UMinorProtocolVersion = Buy_proto(('Get_UMinorProtocolVersion', lib))
        self.Get_UMinorType = Buy_proto(('Get_UMinorType', lib))
        self.Get_UModel = Buy_proto(('Get_UModel', lib))
        self.Get_UseJournalRibbon = Get_CPLog_proto(('Get_UseJournalRibbon', lib))
        self.Set_UseJournalRibbon = Set_CPLog_proto(('Set_UseJournalRibbon', lib))
        self.Get_UseReceiptRibbon = Get_CPLog_proto(('Get_UseReceiptRibbon', lib))
        self.Set_UseReceiptRibbon = Set_CPLog_proto(('Set_UseReceiptRibbon', lib))
        self.Get_UseSlipDocument = Get_CPLog_proto(('Get_UseSlipDocument', lib))
        self.Set_UseSlipDocument = Set_CPLog_proto(('Set_UseSlipDocument', lib))
        self.Get_ValueOfFieldInteger = Buy_proto(('Get_ValueOfFieldInteger', lib))
        self.Set_ValueOfFieldInteger = Set_Tax1_proto(('Set_ValueOfFieldInteger', lib))
        self.Get_ValueOfFieldString = Get_INN_proto(('Get_ValueOfFieldString', lib))
        self.Set_ValueOfFieldString = Set_INN_proto(('Set_ValueOfFieldString', lib))
        self.Get_FontType = Buy_proto(('Get_FontType', lib))
        self.Set_FontType = Set_Tax1_proto(('Set_FontType', lib))
        self.Get_EKLZResultCode = Buy_proto(('Get_EKLZResultCode', lib))
        self.Set_EKLZResultCode = Set_Tax1_proto(('Set_EKLZResultCode', lib))
        self.Get_FMResultCode = Buy_proto(('Get_FMResultCode', lib))
        self.Get_PowerSourceVoltage = Get_Quantity_proto(('Get_PowerSourceVoltage', lib))
        self.Get_ECRModeStatus = Buy_proto(('Get_ECRModeStatus', lib))
        self.Get_ComputerName = Get_INN_proto(('Get_ComputerName', lib))
        self.Set_ComputerName = Set_INN_proto(('Set_ComputerName', lib))
        self.Get_PrintWidth = Buy_proto(('Get_PrintWidth', lib))
        self.Get_CharWidth = Buy_proto(('Get_CharWidth', lib))
        self.Get_CharHeight = Buy_proto(('Get_CharHeight', lib))
        self.Get_FontCount = Buy_proto(('Get_FontCount', lib))
        self.Get_ConnectionType = Buy_proto(('Get_ConnectionType', lib))
        self.Set_ConnectionType = Set_Tax1_proto(('Set_ConnectionType', lib))
        self.Get_TCPPort = Buy_proto(('Get_TCPPort', lib))
        self.Set_TCPPort = Set_Tax1_proto(('Set_TCPPort', lib))
        self.Get_IPAddress = Get_INN_proto(('Get_IPAddress', lib))
        self.Set_IPAddress = Set_INN_proto(('Set_IPAddress', lib))
        self.Get_UseIPAddress = Get_CPLog_proto(('Get_UseIPAddress', lib))
        self.Set_UseIPAddress = Set_CPLog_proto(('Set_UseIPAddress', lib))
        self.Get_SysAdminPassword = Get_Password_proto(('Get_SysAdminPassword', lib))
        self.Set_SysAdminPassword = Set_Password_proto(('Set_SysAdminPassword', lib))
        self.Get_OperationType = Buy_proto(('Get_OperationType', lib))
        self.Set_OperationType = Set_Tax1_proto(('Set_OperationType', lib))
        self.Get_PresenterIn = Get_CPLog_proto(('Get_PresenterIn', lib))
        self.Get_PresenterOut = Get_CPLog_proto(('Get_PresenterOut', lib))
        self.Get_SCPassword = Get_Password_proto(('Get_SCPassword', lib))
        self.Set_SCPassword = Set_Password_proto(('Set_SCPassword', lib))
        self.Get_NewSCPassword = Get_Password_proto(('Get_NewSCPassword', lib))
        self.Set_NewSCPassword = Set_Password_proto(('Set_NewSCPassword', lib))
        self.Get_BarcodeAlignment = Buy_proto(('Get_BarcodeAlignment', lib))
        self.Set_BarcodeAlignment = Set_Tax1_proto(('Set_BarcodeAlignment', lib))
        self.Get_FinishDocumentMode = Buy_proto(('Get_FinishDocumentMode', lib))
        self.Set_FinishDocumentMode = Set_Tax1_proto(('Set_FinishDocumentMode', lib))
        self.Get_PrintBarcodeText = Buy_proto(('Get_PrintBarcodeText', lib))
        self.Set_PrintBarcodeText = Set_Tax1_proto(('Set_PrintBarcodeText', lib))
        self.Get_FileName = Get_INN_proto(('Get_FileName', lib))
        self.Set_FileName = Set_INN_proto(('Set_FileName', lib))
        self.Get_DriverMajorVersion = Get_Password_proto(('Get_DriverMajorVersion', lib))
        self.Get_DriverMinorVersion = Get_Password_proto(('Get_DriverMinorVersion', lib))
        self.Get_DriverRelease = Get_Password_proto(('Get_DriverRelease', lib))
        self.Get_DriverBuild = Get_Password_proto(('Get_DriverBuild', lib))
        self.Get_BlockType = Buy_proto(('Get_BlockType', lib))
        self.Set_BlockType = Set_Tax1_proto(('Set_BlockType', lib))
        self.Get_BlockNumber = Buy_proto(('Get_BlockNumber', lib))
        self.Set_BlockNumber = Set_Tax1_proto(('Set_BlockNumber', lib))
        self.Get_BlockDataHex = Get_INN_proto(('Get_BlockDataHex', lib))
        self.Set_BlockDataHex = Set_INN_proto(('Set_BlockDataHex', lib))
        self.Get_BarcodeType = Buy_proto(('Get_BarcodeType', lib))
        self.Set_BarcodeType = Set_Tax1_proto(('Set_BarcodeType', lib))
        self.Get_BarWidth = Buy_proto(('Get_BarWidth', lib))
        self.Set_BarWidth = Set_Tax1_proto(('Set_BarWidth', lib))
        self.Get_CapGetShortECRStatus = Get_CPLog_proto(('Get_CapGetShortECRStatus', lib))
        self.Get_WaitForPrintingDelay = Buy_proto(('Get_WaitForPrintingDelay', lib))
        self.Set_WaitForPrintingDelay = Set_Tax1_proto(('Set_WaitForPrintingDelay', lib))
        self.Get_LineSwapBytes = Get_CPLog_proto(('Get_LineSwapBytes', lib))
        self.Set_LineSwapBytes = Set_CPLog_proto(('Set_LineSwapBytes', lib))
        self.Get_LineDataHex = Get_INN_proto(('Get_LineDataHex', lib))
        self.Set_LineDataHex = Set_INN_proto(('Set_LineDataHex', lib))
        self.Get_CenterImage = Get_CPLog_proto(('Get_CenterImage', lib))
        self.Set_CenterImage = Set_CPLog_proto(('Set_CenterImage', lib))
        self.Get_ShowProgress = Get_CPLog_proto(('Get_ShowProgress', lib))
        self.Set_ShowProgress = Set_CPLog_proto(('Set_ShowProgress', lib))
        self.Get_ModelParamValue = Buy_proto(('Get_ModelParamValue', lib))
        self.Get_ModelParamNumber = Buy_proto(('Get_ModelParamNumber', lib))
        self.Set_ModelParamNumber = Set_Tax1_proto(('Set_ModelParamNumber', lib))
        self.Get_Connected = Get_CPLog_proto(('Get_Connected', lib))
        self.Get_ConnectionTimeout = Buy_proto(('Get_ConnectionTimeout', lib))
        self.Set_ConnectionTimeout = Set_Tax1_proto(('Set_ConnectionTimeout', lib))
        self.Get_ModelParamDescription = Get_INN_proto(('Get_ModelParamDescription', lib))
        self.Get_DriverVersion = Get_INN_proto(('Get_DriverVersion', lib))
        self.Get_BarcodeDataLength = Buy_proto(('Get_BarcodeDataLength', lib))
        self.Get_BarcodeParameter1 = Buy_proto(('Get_BarcodeParameter1', lib))
        self.Get_BarcodeParameter2 = Buy_proto(('Get_BarcodeParameter2', lib))
        self.Get_BarcodeParameter3 = Buy_proto(('Get_BarcodeParameter3', lib))
        self.Get_BarcodeParameter4 = Buy_proto(('Get_BarcodeParameter4', lib))
        self.Get_BarcodeParameter5 = Buy_proto(('Get_BarcodeParameter5', lib))
        self.Set_BarcodeParameter1 = Set_Tax1_proto(('Set_BarcodeParameter1', lib))
        self.Set_BarcodeParameter2 = Set_Tax1_proto(('Set_BarcodeParameter2', lib))
        self.Set_BarcodeParameter3 = Set_Tax1_proto(('Set_BarcodeParameter3', lib))
        self.Set_BarcodeParameter4 = Set_Tax1_proto(('Set_BarcodeParameter4', lib))
        self.Set_BarcodeParameter5 = Set_Tax1_proto(('Set_BarcodeParameter5', lib))
        self.Get_BarcodeStartBlockNumber = Buy_proto(('Get_BarcodeStartBlockNumber', lib))
        self.Set_BarcodeStartBlockNumber = Set_Tax1_proto(('Set_BarcodeStartBlockNumber', lib))
        self.Get_CarryStrings = Get_CPLog_proto(('Get_CarryStrings', lib))
        self.Get_DelayedPrint = Get_CPLog_proto(('Get_DelayedPrint', lib))
        self.Set_CarryStrings = Set_CPLog_proto(('Set_CarryStrings', lib))
        self.Set_DelayedPrint = Set_CPLog_proto(('Set_DelayedPrint', lib))
        self.Get_ErrorCode = Buy_proto(('Get_ErrorCode', lib))
        self.Set_ErrorCode = Set_Tax1_proto(('Set_ErrorCode', lib))
        self.Get_ErrorDescription = Get_INN_proto(('Get_ErrorDescription', lib))
        self.Get_ReconnectPort = Get_CPLog_proto(('Get_ReconnectPort', lib))
        self.Get_SwapBytesMode = Buy_proto(('Get_SwapBytesMode', lib))
        self.Set_SwapBytesMode = Set_Tax1_proto(('Set_SwapBytesMode', lib))
        self.Get_BarcodeHex = Get_INN_proto(('Get_BarcodeHex', lib))
        self.Set_BarcodeHex = Set_INN_proto(('Set_BarcodeHex', lib))
        self.Get_ProtocolType = Buy_proto(('Get_ProtocolType', lib))
        self.Set_ProtocolType = Set_Tax1_proto(('Set_ProtocolType', lib))
        self.Get_Summ5 = Get_Price_proto(('Get_Summ5', lib))
        self.Set_Summ5 = Set_Price_proto(('Set_Summ5', lib))
        self.Get_Summ6 = Get_Price_proto(('Get_Summ6', lib))
        self.Set_Summ6 = Set_Price_proto(('Set_Summ6', lib))
        self.Get_Summ7 = Get_Price_proto(('Get_Summ7', lib))
        self.Set_Summ7 = Set_Price_proto(('Set_Summ7', lib))
        self.Get_Summ8 = Get_Price_proto(('Get_Summ8', lib))
        self.Set_Summ8 = Set_Price_proto(('Set_Summ8', lib))
        self.Get_Summ9 = Get_Price_proto(('Get_Summ9', lib))
        self.Set_Summ9 = Set_Price_proto(('Set_Summ9', lib))
        self.Get_Summ10 = Get_Price_proto(('Get_Summ10', lib))
        self.Set_Summ10 = Set_Price_proto(('Set_Summ10', lib))
        self.Get_Summ11 = Get_Price_proto(('Get_Summ11', lib))
        self.Set_Summ11 = Set_Price_proto(('Set_Summ11', lib))
        self.Get_Summ12 = Get_Price_proto(('Get_Summ12', lib))
        self.Set_Summ12 = Set_Price_proto(('Set_Summ12', lib))
        self.Get_Summ13 = Get_Price_proto(('Get_Summ13', lib))
        self.Set_Summ13 = Set_Price_proto(('Set_Summ13', lib))
        self.Get_Summ14 = Get_Price_proto(('Get_Summ14', lib))
        self.Set_Summ14 = Set_Price_proto(('Set_Summ14', lib))
        self.Get_Summ15 = Get_Price_proto(('Get_Summ15', lib))
        self.Set_Summ15 = Set_Price_proto(('Set_Summ15', lib))
        self.Get_Summ16 = Get_Price_proto(('Get_Summ16', lib))
        self.Set_Summ16 = Set_Price_proto(('Set_Summ16', lib))
        self.Get_NameCashRegEx = Get_INN_proto(('Get_NameCashRegEx', lib))
        self.Get_RequestType = Buy_proto(('Get_RequestType', lib))
        self.Set_RequestType = Set_Tax1_proto(('Set_RequestType', lib))
        self.Get_HorizScale = Buy_proto(('Get_HorizScale', lib))
        self.Set_HorizScale = Set_Tax1_proto(('Set_HorizScale', lib))
        self.Get_VertScale = Buy_proto(('Get_VertScale', lib))
        self.Set_VertScale = Set_Tax1_proto(('Set_VertScale', lib))
        self.Get_GraphBufferType = Buy_proto(('Get_GraphBufferType', lib))
        self.Set_GraphBufferType = Set_Tax1_proto(('Set_GraphBufferType', lib))
        self.Get_LineLength = Buy_proto(('Get_LineLength', lib))
        self.Set_LineLength = Set_Tax1_proto(('Set_LineLength', lib))
        self.Get_FNCurrentDocument = Buy_proto(('Get_FNCurrentDocument', lib))
        self.Set_FNCurrentDocument = Set_Tax1_proto(('Set_FNCurrentDocument', lib))
        self.Get_FNDocumentData = Buy_proto(('Get_FNDocumentData', lib))
        self.Set_FNDocumentData = Set_Tax1_proto(('Set_FNDocumentData', lib))
        self.Get_FNLifeState = Buy_proto(('Get_FNLifeState', lib))
        self.Set_FNLifeState = Set_Tax1_proto(('Set_FNLifeState', lib))
        self.Get_FNSessionState = Buy_proto(('Get_FNSessionState', lib))
        self.Set_FNSessionState = Set_Tax1_proto(('Set_FNSessionState', lib))
        self.Get_FNSoftVersion = Get_INN_proto(('Get_FNSoftVersion', lib))
        self.Set_FNSoftVersion = Set_INN_proto(('Set_FNSoftVersion', lib))
        self.Get_FNSoftType = Buy_proto(('Get_FNSoftType', lib))
        self.Get_FNWarningFlags = Buy_proto(('Get_FNWarningFlags', lib))
        self.Set_FNWarningFlags = Set_Tax1_proto(('Set_FNWarningFlags', lib))
        self.Get_FiscalSign = Get_Password_proto(('Get_FiscalSign', lib))
        self.Set_FiscalSign = Set_Password_proto(('Set_FiscalSign', lib))
        self.Get_FiscalSignAsString = Get_INN_proto(('Get_FiscalSignAsString', lib))
        self.Get_KKTRegistrationNumber = Get_INN_proto(('Get_KKTRegistrationNumber', lib))
        self.Set_KKTRegistrationNumber = Set_INN_proto(('Set_KKTRegistrationNumber', lib))
        self.Get_TaxType = Buy_proto(('Get_TaxType', lib))
        self.Set_TaxType = Set_Tax1_proto(('Set_TaxType', lib))
        self.Get_WorkMode = Buy_proto(('Get_WorkMode', lib))
        self.Set_WorkMode = Set_Tax1_proto(('Set_WorkMode', lib))
        self.Get_DocumentType = Buy_proto(('Get_DocumentType', lib))
        self.Set_DocumentType = Set_Tax1_proto(('Set_DocumentType', lib))
        self.Get_OFDTicketReceived = Get_CPLog_proto(('Get_OFDTicketReceived', lib))
        self.Set_OFDTicketReceived = Set_CPLog_proto(('Set_OFDTicketReceived', lib))
        self.Get_TLVData = Get_INN_proto(('Get_TLVData', lib))
        self.Set_TLVData = Set_INN_proto(('Set_TLVData', lib))
        self.Get_DataBlockSize = Buy_proto(('Get_DataBlockSize', lib))
        self.Set_DataBlockSize = Set_Tax1_proto(('Set_DataBlockSize', lib))
        self.Get_DataLength = Buy_proto(('Get_DataLength', lib))
        self.Set_DataLength = Set_Tax1_proto(('Set_DataLength', lib))
        self.Get_OFDPort = Buy_proto(('Get_OFDPort', lib))
        self.Set_OFDPort = Set_Tax1_proto(('Set_OFDPort', lib))
        self.Get_OFDServer = Get_INN_proto(('Get_OFDServer', lib))
        self.Set_OFDServer = Set_INN_proto(('Set_OFDServer', lib))
        self.Get_OFDPollPeriod = Buy_proto(('Get_OFDPollPeriod', lib))
        self.Set_OFDPollPeriod = Set_Tax1_proto(('Set_OFDPollPeriod', lib))
        self.Get_DocumentCount = Buy_proto(('Get_DocumentCount', lib))
        self.Set_DocumentCount = Set_Tax1_proto(('Set_DocumentCount', lib))
        self.Get_ReceiptNumber = Buy_proto(('Get_ReceiptNumber', lib))
        self.Set_ReceiptNumber = Set_Tax1_proto(('Set_ReceiptNumber', lib))
        self.Get_InfoExchangeStatus = Buy_proto(('Get_InfoExchangeStatus', lib))
        self.Set_InfoExchangeStatus = Set_Tax1_proto(('Set_InfoExchangeStatus', lib))
        self.Get_MessageState = Buy_proto(('Get_MessageState', lib))
        self.Set_MessageState = Set_Tax1_proto(('Set_MessageState', lib))
        self.Get_MessageCount = Buy_proto(('Get_MessageCount', lib))
        self.Set_MessageCount = Set_Tax1_proto(('Set_MessageCount', lib))
        self.Get_MessageNumber = Get_Price_proto(('Get_MessageNumber', lib))
        self.Set_MessageNumber = Set_Price_proto(('Set_MessageNumber', lib))
        self.Get_ReportTypeInt = Buy_proto(('Get_ReportTypeInt', lib))
        self.Set_ReportTypeInt = Set_Tax1_proto(('Set_ReportTypeInt', lib))
        self.Get_TaxValue = Get_Price_proto(('Get_TaxValue', lib))
        self.Set_TaxValue = Set_Price_proto(('Set_TaxValue', lib))
        self.Get_RegistrationReasonCode = Buy_proto(('Get_RegistrationReasonCode', lib))
        self.Set_RegistrationReasonCode = Set_Tax1_proto(('Set_RegistrationReasonCode', lib))
        self.Get_CustomerEmail = Get_INN_proto(('Get_CustomerEmail', lib))
        self.Set_CustomerEmail = Set_INN_proto(('Set_CustomerEmail', lib))
        self.Get_Date2 = Get_Date_proto(('Get_Date2', lib))
        self.Set_Date2 = Set_Date_proto(('Set_Date2', lib))
        self.Get_Time2 = Get_Date_proto(('Get_Time2', lib))
        self.Set_Time2 = Set_Date_proto(('Set_Time2', lib))
        self.Get_FiscalSignOFD = Get_INN_proto(('Get_FiscalSignOFD', lib))
        self.Set_FiscalSignOFD = Set_INN_proto(('Set_FiscalSignOFD', lib))
        self.Get_AutoOpenSession = Get_CPLog_proto(('Get_AutoOpenSession', lib))
        self.Set_AutoOpenSession = Set_CPLog_proto(('Set_AutoOpenSession', lib))
        self.Get_TagNumber = Buy_proto(('Get_TagNumber', lib))
        self.Set_TagNumber = Set_Tax1_proto(('Set_TagNumber', lib))
        self.Get_TagType = Buy_proto(('Get_TagType', lib))
        self.Set_TagType = Set_Tax1_proto(('Set_TagType', lib))
        self.Get_TagValueInt = Get_CheckSum_proto(('Get_TagValueInt', lib))
        self.Set_TagValueInt = Set_CheckSum_proto(('Set_TagValueInt', lib))
        self.Get_TagValueStr = Get_INN_proto(('Get_TagValueStr', lib))
        self.Set_TagValueStr = Set_INN_proto(('Set_TagValueStr', lib))
        self.Get_TagValueFVLN = Get_Quantity_proto(('Get_TagValueFVLN', lib))
        self.Set_TagValueFVLN = Set_Quantity_proto(('Set_TagValueFVLN', lib))
        self.Get_TagValueDateTime = Get_Date_proto(('Get_TagValueDateTime', lib))
        self.Set_TagValueDateTime = Set_Date_proto(('Set_TagValueDateTime', lib))
        self.Get_TagValueBin = Get_INN_proto(('Get_TagValueBin', lib))
        self.Set_TagValueBin = Set_INN_proto(('Set_TagValueBin', lib))
        self.Get_TagValueLength = Buy_proto(('Get_TagValueLength', lib))
        self.Set_TagValueLength = Set_Tax1_proto(('Set_TagValueLength', lib))
        self.Get_ShowTagNumber = Get_CPLog_proto(('Get_ShowTagNumber', lib))
        self.Set_ShowTagNumber = Set_CPLog_proto(('Set_ShowTagNumber', lib))
        self.Get_RoundingSumm = Buy_proto(('Get_RoundingSumm', lib))
        self.Set_RoundingSumm = Set_Tax1_proto(('Set_RoundingSumm', lib))
        self.Get_TaxValue1 = Get_Price_proto(('Get_TaxValue1', lib))
        self.Set_TaxValue1 = Set_Price_proto(('Set_TaxValue1', lib))
        self.Get_TaxValue2 = Get_Price_proto(('Get_TaxValue2', lib))
        self.Set_TaxValue2 = Set_Price_proto(('Set_TaxValue2', lib))
        self.Get_TaxValue3 = Get_Price_proto(('Get_TaxValue3', lib))
        self.Set_TaxValue3 = Set_Price_proto(('Set_TaxValue3', lib))
        self.Get_TaxValue4 = Get_Price_proto(('Get_TaxValue4', lib))
        self.Set_TaxValue4 = Set_Price_proto(('Set_TaxValue4', lib))
        self.Get_TaxValue5 = Get_Price_proto(('Get_TaxValue5', lib))
        self.Set_TaxValue5 = Set_Price_proto(('Set_TaxValue5', lib))
        self.Get_TaxValue6 = Get_Price_proto(('Get_TaxValue6', lib))
        self.Set_TaxValue6 = Set_Price_proto(('Set_TaxValue6', lib))
        self.Get_Summ1Enabled = Get_CPLog_proto(('Get_Summ1Enabled', lib))
        self.Set_Summ1Enabled = Set_CPLog_proto(('Set_Summ1Enabled', lib))
        self.Get_TaxValueEnabled = Get_CPLog_proto(('Get_TaxValueEnabled', lib))
        self.Set_TaxValueEnabled = Set_CPLog_proto(('Set_TaxValueEnabled', lib))
        self.Get_PaymentTypeSign = Buy_proto(('Get_PaymentTypeSign', lib))
        self.Set_PaymentTypeSign = Set_Tax1_proto(('Set_PaymentTypeSign', lib))
        self.Get_PaymentItemSign = Buy_proto(('Get_PaymentItemSign', lib))
        self.Set_PaymentItemSign = Set_Tax1_proto(('Set_PaymentItemSign', lib))
        self.Get_CalculationSign = Buy_proto(('Get_CalculationSign', lib))
        self.Set_CalculationSign = Set_Tax1_proto(('Set_CalculationSign', lib))
        self.Get_CorrectionType = Buy_proto(('Get_CorrectionType', lib))
        self.Set_CorrectionType = Set_Tax1_proto(('Set_CorrectionType', lib))
        self.Get_AutoEoD = Get_CPLog_proto(('Get_AutoEoD', lib))
        self.Set_AutoEoD = Set_CPLog_proto(('Set_AutoEoD', lib))
        self.Get_AutoOFDExchange = Get_CPLog_proto(('Get_AutoOFDExchange', lib))
        self.Set_AutoOFDExchange = Set_CPLog_proto(('Set_AutoOFDExchange', lib))
        self.Get_EmailAddress = Get_INN_proto(('Get_EmailAddress', lib))
        self.Set_EmailAddress = Set_INN_proto(('Set_EmailAddress', lib))
        self.Get_TagID = Buy_proto(('Get_TagID', lib))
        self.Set_TagID = Set_Tax1_proto(('Set_TagID', lib))
        self.Set_ConnectionURI = Set_INN_proto(('Set_ConnectionURI', lib))
        self.Get_ConnectionURI = Get_INN_proto(('Get_ConnectionURI', lib))
        self.Get_BlockData = Get_INN_proto(('Get_BlockData', lib))
        self.Set_BlockData = Set_INN_proto(('Set_BlockData', lib))
        self.Get_WrapStrings = Get_CPLog_proto(('Get_WrapStrings', lib))
        self.Set_WrapStrings = Set_CPLog_proto(('Set_WrapStrings', lib))
        self.Set_MarkingType = Set_Tax1_proto(('Set_MarkingType', lib))
        self.Get_MarkingType = Buy_proto(('Get_MarkingType', lib))
        self.Get_LoaderVersion = Get_INN_proto(('Get_LoaderVersion', lib))
        self.Get_WorkModeEx = Buy_proto(('Get_WorkModeEx', lib))
        self.Set_WorkModeEx = Set_Tax1_proto(('Set_WorkModeEx', lib))
        self.Get_INNOFD = Get_INN_proto(('Get_INNOFD', lib))
        self.Set_INNOFD = Set_INN_proto(('Set_INNOFD', lib))
        self.Get_RegistrationReasonCodeEx = Buy_proto(('Get_RegistrationReasonCodeEx', lib))
        self.Set_RegistrationReasonCodeEx = Set_Tax1_proto(('Set_RegistrationReasonCodeEx', lib))
        self.Get_SkipPrint = Get_CPLog_proto(('Get_SkipPrint', lib))
        self.Set_SkipPrint = Set_CPLog_proto(('Set_SkipPrint', lib))
        self.Get_DigitalSign = Get_INN_proto(('Get_DigitalSign', lib))
        self.Set_DigitalSign = Set_INN_proto(('Set_DigitalSign', lib))
        self.Get_DeviceFunctionNumber = Buy_proto(('Get_DeviceFunctionNumber', lib))
        self.Set_DeviceFunctionNumber = Set_Tax1_proto(('Set_DeviceFunctionNumber', lib))
        self.Get_ValueOfFunctionInteger = Buy_proto(('Get_ValueOfFunctionInteger', lib))
        self.Set_ValueOfFunctionInteger = Set_Tax1_proto(('Set_ValueOfFunctionInteger', lib))
        self.Get_ValueOfFunctionString = Get_INN_proto(('Get_ValueOfFunctionString', lib))
        self.Set_ValueOfFunctionString = Set_INN_proto(('Set_ValueOfFunctionString', lib))
        self.Get_EnableCashcoreMarkCompatibility = Get_CPLog_proto(('Get_EnableCashcoreMarkCompatibility', lib))
        self.Set_EnableCashcoreMarkCompatibility = Set_CPLog_proto(('Set_EnableCashcoreMarkCompatibility', lib))
        self.Set_CheckItemLocalError = Set_Tax1_proto(('Set_CheckItemLocalError', lib))
        self.Get_CheckItemLocalError = Buy_proto(('Get_CheckItemLocalError', lib))
        self.Set_MarkingTypeEx = Set_Tax1_proto(('Set_MarkingTypeEx', lib))
        self.Get_MarkingTypeEx = Buy_proto(('Get_MarkingTypeEx', lib))
        self.Set_MeasureUnit = Set_Tax1_proto(('Set_MeasureUnit', lib))
        self.Get_MeasureUnit = Buy_proto(('Get_MeasureUnit', lib))
        self.Set_DivisionalQuantity = Set_CPLog_proto(('Set_DivisionalQuantity', lib))
        self.Get_DivisionalQuantity = Get_CPLog_proto(('Get_DivisionalQuantity', lib))
        self.Set_Numerator = Set_CheckSum_proto(('Set_Numerator', lib))
        self.Get_Numerator = Get_CheckSum_proto(('Get_Numerator', lib))
        self.Set_Denominator = Set_CheckSum_proto(('Set_Denominator', lib))
        self.Get_Denominator = Get_CheckSum_proto(('Get_Denominator', lib))
        self.Get_FreeMemorySize = Buy_proto(('Get_FreeMemorySize', lib))
        self.Set_FreeMemorySize = Set_Tax1_proto(('Set_FreeMemorySize', lib))
        self.Get_MCCheckStatus = Buy_proto(('Get_MCCheckStatus', lib))
        self.Set_MCCheckStatus = Set_Tax1_proto(('Set_MCCheckStatus', lib))
        self.Get_MCNotificationStatus = Buy_proto(('Get_MCNotificationStatus', lib))
        self.Set_MCNotificationStatus = Set_Tax1_proto(('Set_MCNotificationStatus', lib))
        self.Get_MCCommandFlags = Buy_proto(('Get_MCCommandFlags', lib))
        self.Set_MCCommandFlags = Set_Tax1_proto(('Set_MCCommandFlags', lib))
        self.Get_MCCheckResultSavedCount = Buy_proto(('Get_MCCheckResultSavedCount', lib))
        self.Set_MCCheckResultSavedCount = Set_Tax1_proto(('Set_MCCheckResultSavedCount', lib))
        self.Get_MCRealizationCount = Buy_proto(('Get_MCRealizationCount', lib))
        self.Set_MCRealizationCount = Set_Tax1_proto(('Set_MCRealizationCount', lib))
        self.Get_MCStorageSize = Buy_proto(('Get_MCStorageSize', lib))
        self.Set_MCStorageSize = Set_Tax1_proto(('Set_MCStorageSize', lib))
        self.Get_CheckSum = Get_CheckSum_proto(('Get_CheckSum', lib))
        self.Set_CheckSum = Set_CheckSum_proto(('Set_CheckSum', lib))
        self.Get_NotificationCount = Buy_proto(('Get_NotificationCount', lib))
        self.Set_NotificationCount = Set_Tax1_proto(('Set_NotificationCount', lib))
        self.Get_NotificationNumber = Get_Price_proto(('Get_NotificationNumber', lib))
        self.Set_NotificationNumber = Set_Price_proto(('Set_NotificationNumber', lib))
        self.Get_NotificationSize = Buy_proto(('Get_NotificationSize', lib))
        self.Set_NotificationSize = Set_Tax1_proto(('Set_NotificationSize', lib))
        self.Get_DataOffset = Buy_proto(('Get_DataOffset', lib))
        self.Set_DataOffset = Set_Tax1_proto(('Set_DataOffset', lib))
        self.Set_MarkingType2 = Set_Tax1_proto(('Set_MarkingType2', lib))
        self.Get_MarkingType2 = Buy_proto(('Get_MarkingType2', lib))
        self.Get_RandomSequence = Get_INN_proto(('Get_RandomSequence', lib))
        self.Set_RandomSequence = Set_INN_proto(('Set_RandomSequence', lib))
        self.Get_RandomSequenceHex = Get_INN_proto(('Get_RandomSequenceHex', lib))
        self.Set_RandomSequenceHex = Set_INN_proto(('Set_RandomSequenceHex', lib))
        self.Get_AuthData = Get_INN_proto(('Get_AuthData', lib))
        self.Set_AuthData = Set_INN_proto(('Set_AuthData', lib))
        self.Set_FNArchiveType = Set_Tax1_proto(('Set_FNArchiveType', lib))
        self.Get_FNArchiveType = Buy_proto(('Get_FNArchiveType', lib))
        self.Set_MarkingOnly = Set_CPLog_proto(('Set_MarkingOnly', lib))
        self.Get_MarkingOnly = Get_CPLog_proto(('Get_MarkingOnly', lib))
        self.Set_ItemStatus = Set_Tax1_proto(('Set_ItemStatus', lib))
        self.Get_ItemStatus = Buy_proto(('Get_ItemStatus', lib))
        self.Set_CheckItemMode = Set_Tax1_proto(('Set_CheckItemMode', lib))
        self.Get_CheckItemMode = Buy_proto(('Get_CheckItemMode', lib))
        self.Set_CheckItemLocalResult = Set_Tax1_proto(('Set_CheckItemLocalResult', lib))
        self.Get_CheckItemLocalResult = Buy_proto(('Get_CheckItemLocalResult', lib))
        self.Set_KMServerErrorCode = Set_Tax1_proto(('Set_KMServerErrorCode', lib))
        self.Get_KMServerErrorCode = Buy_proto(('Get_KMServerErrorCode', lib))
        self.Set_KMServerCheckingStatus = Set_Tax1_proto(('Set_KMServerCheckingStatus', lib))
        self.Get_KMServerCheckingStatus = Buy_proto(('Get_KMServerCheckingStatus', lib))
        self.Set_UserAttributeName = Set_INN_proto(('Set_UserAttributeName', lib))
        self.Get_UserAttributeName = Get_INN_proto(('Get_UserAttributeName', lib))
        self.Set_UserAttributeValue = Set_INN_proto(('Set_UserAttributeValue', lib))
        self.Get_UserAttributeValue = Get_INN_proto(('Get_UserAttributeValue', lib))
        self.Set_WaitForPrintingTimeout = Set_Price_proto(('Set_WaitForPrintingTimeout', lib))
        self.Get_WaitForPrintingTimeout = Get_Price_proto(('Get_WaitForPrintingTimeout', lib))
        self.Set_DeclarativeInput = Set_INN_proto(('Set_DeclarativeInput', lib))
        self.Get_DeclarativeInput = Get_INN_proto(('Get_DeclarativeInput', lib))
        self.Set_DeclarativeOutput = Set_INN_proto(('Set_DeclarativeOutput', lib))
        self.Get_DeclarativeOutput = Get_INN_proto(('Get_DeclarativeOutput', lib))
        self.Set_DeclarativeEndpointPath = Set_INN_proto(('Set_DeclarativeEndpointPath', lib))
        self.Get_DeclarativeEndpointPath = Get_INN_proto(('Get_DeclarativeEndpointPath', lib))
        self.Get_FontHashHex = Get_INN_proto(('Get_FontHashHex', lib))
        self.Set_MCOSUSign = Set_CPLog_proto(('Set_MCOSUSign', lib))
        self.Get_MCOSUSign = Get_CPLog_proto(('Get_MCOSUSign', lib))
        self.Set_DocumentSize = Set_Tax1_proto(('Set_DocumentSize', lib))
        self.Get_DocumentSize = Buy_proto(('Get_DocumentSize', lib))
        self.Set_FNImplementation = Set_INN_proto(('Set_FNImplementation', lib))
        self.Get_FNImplementation = Get_INN_proto(('Get_FNImplementation', lib))
        self.Set_FNOSUSupportStatus = Set_Tax1_proto(('Set_FNOSUSupportStatus', lib))
        self.Get_FNOSUSupportStatus = Buy_proto(('Get_FNOSUSupportStatus', lib))


classicInterfaceWrap = None


class ClassicInterface(object):

    ###################################################################################################################################
    # TBarcodeAlignment: The TBarcodeAlignment enum Выравнивание штрих-кода
    baCenter                                              =    0 # по центру
    baLeft                                                =    1 # влево
    baRight                                               =    2 # вправо
    ###################################################################################################################################
    # TFinishDocumentMode: Режим завершения документа
    fdmTrailerDisabled                                    =    0 # Не печатать рекламный текст
    fdmTrailerEnabled                                     =    1 # Печатать рекламный текст
    ###################################################################################################################################
    # TBinaryConversion: Режим конвертации двоичных данных
    BINARY_CONVERSION_NONE                                =    0 # Без ковертации
    BINARY_CONVERSION_HEX                                 =    1 # В виде HEX строки
    ###################################################################################################################################
    # TCodePage: 
    CODE_PAGE_DEFAULT                                     =    0 # 
    CODE_PAGE_RUSSIAN                                     =    1 # 
    CODE_PAGE_ARMENIAN_UNICODE                            =    2 # 
    CODE_PAGE_ARMENIAN_ANSI                               =    3 # 
    CODE_PAGE_KAZAKH_UNICODE                              =    4 # 
    CODE_PAGE_TURKMEN_UNICODE                             =    5 # 
    ###################################################################################################################################
    # TConnectionType: Тип подключения
    Local                                                 =    0 # Локально
    ServerTcp                                             =    1 # Сервер ККМ (TCP)
    ServerDCOM                                            =    2 # Сервер ККМ (DCOM)
    ESCAPE                                                =    3 # ESCAPE.
    NotUsed                                               =    4 # Не используется
    Emulator                                              =    5 # Эмулятор
    Tcp                                                   =    6 # Подключение через ТСР-сокет
    ###################################################################################################################################
    # BarcodeTextPosition: The BarcodeTextPosition enum Положение текста при печати штрих-кода. Используется методами PrintBarcodeLine.
    BCT_None                                              =    0 # Не печатать
    BCT_Below                                             =    1 # Печатать снизу
    BCT_Above                                             =    2 # Печатать сверху
    BCT_Both                                              =    3 # Печатать сверху и снизу
    ###################################################################################################################################
    # BarcodeLineType: The BarcodeLineType enum Тип штрих-кода для метода PrintBacodeLine.
    BC1D_Code128A                                         =    0 # 
    BC1D_Code128B                                         =    1 # 
    BC1D_Code128C                                         =    2 # 
    BC1D_ReservedForQR                                    =    3 # PrintBacodeLine.
    BC1D_Code39                                           =    4 # Code39.
    BC1D_EAN13                                            =    5 # EAN13.
    ###################################################################################################################################
    # Barcode2DType: The Barcode2DType enum.
    BC2D_PDF417                                           =    0 # PDF417.
    BC2D_DATAMATRIX                                       =    1 # Datamatrix.
    BC2D_AZTEC                                            =    2 # AZTEC.
    BC2D_QRCODE                                           =    3 # QR code.
    ###################################################################################################################################
    # DevicePropertiesEnumeration: The DevicePropertiesEnumeration enum целые можно передавать в Set_ModelParamNumber.
    DPE_f00_journal_weight_sensor                         =    0 # Весовой датчик контрольной ленты
    DPE_f01_receipt_weight_sensor                         =    1 # Весовой датчик чековой ленты
    DPE_f02_journal_opt_sensor                            =    2 # Оптический датчик контрольной ленты
    DPE_f03_receipt_opt_sensor                            =    3 # Оптический датчик чековой ленты
    DPE_f04_cover_sensor                                  =    4 # Датчик крышки
    DPE_f05_journal_lever                                 =    5 # Рычаг термоголовки контрольной ленты
    DPE_f06_receipt_lever                                 =    6 # Рычаг термоголовки чековой ленты
    DPE_f07_hi_slip_sensor                                =    7 # Верхний датчик подкладного документа
    DPE_f08_low_slip_sensor                               =    8 # Нижний датчик подкладного документа
    DPE_f09_presenter                                     =    9 # Презентер поддерживается
    DPE_f10_presenter_commands                            =   10 # Поддержка команд работы с презентером
    DPE_f11_ej_overflow_flag                              =   11 # Флаг заполнения ЭКЛЗ
    DPE_f12_ej                                            =   12 # ЭКЛЗ поддерживается
    DPE_f13_cutter                                        =   13 # Отрезчик поддерживается
    DPE_f14_drawer_status_as_presenter_paper_sensor       =   14 # Состояние ДЯ как датчик бумаги в презентере
    DPE_f15_drawer_sensor                                 =   15 # Датчик денежного ящика
    DPE_f16_presenter_in_paper_sensor                     =   16 # Датчик бумаги на входе в презентер
    DPE_f17_presenter_out_paper_sensor                    =   17 # Датчик бумаги на выходе из презентера
    DPE_f18_bill_acceptor                                 =   18 # Купюроприемник поддерживается
    DPE_f19_tax_keyboard                                  =   19 # Клавиатура НИ поддерживается
    DPE_f20_journal                                       =   20 # Контрольная лента поддерживается
    DPE_f21_slip                                          =   21 # Подкладной документ поддерживается
    DPE_f22_non_fiscal_doc_commands                       =   22 # Поддержка команд нефискального документа
    DPE_f23_cashcore                                      =   23 # Поддержка протокола Кассового Ядра (cashcore)
    DPE_f24_inn_leading_zeros                             =   24 # Ведущие нули в ИНН
    DPE_f25_rnm_leading_zeros                             =   25 # Ведущие нули в РНМ
    DPE_f26_line_printing_bytes_swapping                  =   26 # Переворачивать байты при печати линии
    DPE_f27_wrong_tax_password_blocking                   =   27 # Блокировка ФР по неверному паролю налогового инспектора
    DPE_f28_alt_protocol                                  =   28 # Поддержка альтернативного нижнего уровня протокола ККТ
    DPE_f29_string_printing_commands_wrap_strings_by_n    =   29 # Поддержка переноса строк символом ' ' (код 10) в командах печати строк 12H,17H,2FH.
    DPE_f30_string_printing_commands_wrap_strings_by_font =   30 # Поддержка переноса строк номером шрифта (коды 1…9) в команде печати строк 2FH.
    DPE_f31_fisc_commands_wrap_strings_by_n               =   31 # Поддержка переноса строк символом ' ' (код 10) в фискальных командах 80H…87H,8AH,8BH.
    DPE_f32_fisc_commands_wrap_strings_by_font            =   32 # Поддержка переноса строк номером шрифта (коды 1…9) в фискальных командах 80H…87H,8AH,8BH.
    DPE_f33_senior_cashier                                =   33 # Права "СТАРШИЙ КАССИР" (28) на снятие отчетов: X, операционных регистров, по отделам, по налогам, по кассирам, почасового, по товарам
    DPE_f34_slip_receipt_bit3                             =   34 # Поддержка "Бит 3 - слип чек" в командах печати строк 12H,17H,2FH, графики C1H,C3H; Поддержка поля "результат последней печати" в кратком запросе ФР 10H.
    DPE_f35_block_graphic_loading                         =   35 # Поддержка блочной загрузки графики в команде C4H.
    DPE_f36_error_description_command                     =   36 # Поддержка команды 6BH возврата описания ошибок ФР
    DPE_f37_print_flags_for_print_ext_graphics_print_line =   37 # Поддержка флагов печати для команд печати расширенной графики C3H и печати линии C5H.
    DPE_f38_skno                                          =   38 # Поддержка СКНО
    DPE_f39_mfp                                           =   39 # Поддержка МФП
    DPE_f40_ej5                                           =   40 # Поддержка ЭКЛЗ5.
    DPE_f41_print_scaled_graphics                         =   41 # Печать графики с масштабированием
    DPE_f42_print_ext_graphics_512                        =   42 # Загрузка и печать графики 512 с масштабированием
    DPE_f43_fs                                            =   43 # Поддержка ФН
    DPE_f44_eod                                           =   44 # Поддержка EoD.
    DPE_f45_tag_autoprint_support                         =   45 # Поддержка авопечати тегов
    DPE_f46_qr_in_footer_support                          =   46 # Поддержка двумерных штрихкодов в футере
    DPE_f47_fs_1_1_support                                =   47 # Поддержка ФН 1.1.
    DPE_f48_correction_new_support                        =   48 # Поддержка чеков коррекции как обычных чеков
    DPE_f49_error_description_command_extended            =   49 # Поддержка в команде 6BH отсутствие параметров или передача четырех байтного подкода ошибки
    DPE_f50_fd_answers_extended                           =   50 # Поддержка расширенных ответов на команды формирования ФД.
    DPE_f51_fd_authorization_req                          =   51 # Требуется авторизация на команды формирования ФД
    DPE_f52_plain_protocolv1_transfer                     =   52 # Поддержка "чистой" передачи поверх надежного протокола
    DPE_f53_blocking_mode_available                       =   53 # Поддержка режима блокирования в рамках сесси поверх надежного протокола(автоматическая отмена незавершенного документа)
    DPE_reserved                                          =   54 # Зарезервировано
    DPE_Font1Width                                        =   64 # Ширина печати шрифтом 1.
    DPE_Font2Width                                        =   65 # Ширина печати шрифтом 2.
    DPE_FirstDrawLine                                     =   66 # Номер первой печатаемой линии в графике
    DPE_InnDigitCount                                     =   67 # Количество цифр в ИНН
    DPE_RnmDigitCount                                     =   68 # Количество цифр в РНМ
    DPE_LongRnmDigitCount                                 =   69 # Количество цифр в длинном РНМ
    DPE_LongSerialDigitCount                              =   70 # Количество цифр в длинном заводском номере
    DPE_DefaultTaxPassword                                =   71 # Пароль налогового инспектора по умолчанию
    DPE_DefaultAdminPassword                              =   72 # Пароль сист.админа по умолчанию
    DPE_BluetoothTableNumber                              =   73 # Номер таблицы "BLUETOOTH БЕСПРОВОДНОЙ МОДУЛЬ".
    DPE_TaxFieldNumber                                    =   74 # Номер поля "НАЧИСЛЕНИЕ НАЛОГОВ".
    DPE_MaxCmdLength                                      =   75 # Максимальная длина команды
    DPE_MaxDrawLineWidth                                  =   76 # Ширина произвольной графической линии в байтах (печать одномерного штрих-кода)
    DPE_MaxDrawLineWidth512                               =   77 # Ширина графической линии в буфере графики-512.
    DPE_MaxDrawLineCount512                               =   78 # Количество линий в буфере графики-512.
    DPE_FsTableNumber                                     =   79 # Номер таблицы Фискального Накопителя
    DPE_OfdTableNmb                                       =   80 # Номер таблицы параметров ОФД
    DPE_EmbeddedTableNumber                               =   81 # Номер таблицы встраиваемой техники
    DPE_FFDVersionTableNumber                             =   82 # Номер таблицы версии ФФД
    DPE_FFDVersionFieldNumber                             =   83 # Номер поля версии ФФД
    ###################################################################################################################################
    # ESwapBytesMode: 
    SBM_Swap                                              =    0 # Переворачивать
    SBM_NoSwap                                            =    1 # Не переворачивать
    SBM_Prop                                              =    2 # Использовать свойство драйвера LineSwapBytes.
    SBM_Model                                             =    3 # Использовать настройки модели(бит 26 из флагов команды F7)
    ###################################################################################################################################
    # PrinterMode: The PrinterMode enum Режим ФР
    PM_UnknownMode                                        =  0x0 # 0 - Например, на время печати отчетов из буфера. Технический режим.
    PM_DumpMode                                           =  0x1 # 1 - Выдача данных
    PM_SessionOpen                                        =  0x2 # 2 - Открытая смена, 24 часа не кончились
    PM_SessionOpenOver24h                                 =  0x3 # 3 - Открытая смена, 24 часа кончились
    PM_SessionClosed                                      =  0x4 # 4 - Закрытая смена
    PM_TaxmanPasswordError                                =  0x5 # 5 - Блокировка по неправильному паролю налогового инспектора
    PM_DateConfirmWaiting                                 =  0x6 # 6 - Ожидание подтверждения ввода даты
    PM_PointModificationAllowed                           =  0x7 # 7 - Разрешение изменения положения десятичной точки
    PM_OpenedDocument                                     =  0x8 # 8 - Открытый документ
    PM_TechnologicalResetAllowed                          =  0x9 # 9 - Режим разрешения технологического обнуления
    PM_TestRun                                            =  0xa # 10 - Тестовый прогон.
    PM_FullFiscalReportInProgress                         =  0xb # 11 - Печать полного фис. отчета
    PM_CryptoJournalReportInProgress                      =  0xc # 12 - Печать отчёта ЭКЛЗ
    PM_FiscalSlipMode                                     =  0xd # 13 - Работа с фискальным подкладным документом
    PM_SlipPrintingInProgress                             =  0xe # 14 - Печать подкладного документа
    PM_FiscalSlipIsReady                                  =  0xf # 15 - Фискальный подкладной документ сформирован
    PM_OpenedDocumentBuy                                  = 0x18 # Открытый документ: покупка
    PM_OpenedSlipDocumentBuy                              = 0x1d # Открыт ПД покупки
    PM_LoadingAndPositioningSlip                          = 0x1e # Загрузка и позиционирование ПД
    PM_OpenedDocumentSaleReturn                           = 0x28 # Открытый документ: возврат продажи
    PM_OpenedSlipDocumentSaleReturn                       = 0x2d # Открыт ПД возврата продажи
    PM_PositioningSlip                                    = 0x2e # Позиционирование ПД
    PM_OpenedDocumentBuyReturn                            = 0x38 # Открытый документ: возврат покупки
    PM_OpenedSlipDocumentBuyReturn                        = 0x3d # Открыт ПД возврата покупки
    PM_PrintingSlip                                       = 0x3e # Печать ПД
    PM_OpenedDocumentNonFiscal                            = 0x48 # Открытый документ: нефискальный
    PM_SlipPrinted                                        = 0x4c # Печать ПД закончена
    PM_DocumentPrinted                                    = 0x4e # Печать закончена
    PM_EjectingSlip                                       = 0x5e # Выброс ПД
    PM_WaitingSlipRemoval                                 = 0x6e # Ожидание извлечения ПД
    ###################################################################################################################################
    # PrinterSubmode: 
    PSM_PaperPresent                                      =    0 # 0 - Бумага есть – ФР не в фазе печати операции
    PSM_PassivePaperAbsense                               =    1 # 1 - Пассивное отсутствие бумаги – ФР не в фазе печати операции
    PSM_ActivePaperAbsense                                =    2 # 2 - Активное отсутствие бумаги – ФР в фазе печати операции
    PSM_AfterAvtivePaperAbsense                           =    3 # 3 - После активного отсутствия бумаги – ФР ждет команду продолжения печати
    PSM_ReportPrintingInProgress                          =    4 # 4 - Фаза печати операции полных фискальных отчетов
    PSM_OperationPrintingInProgress                       =    5 # 5 - Фаза печати операции
    ###################################################################################################################################
    # DeviceFunctionEnumeration: 
    DFE_SkipAllPrinting                                   =    0 # Пропуск печати всех документов. Если установлено в 1, то документы на бумажной ленте не печатаются и формируются только в электронном виде.
    DFE_AutoReadDetailedErrorDescription                  =    1 # Автоматически получать подробное описание ошибки из ККТ(на основе КЯ). Подробное описание находится в свойстве #ErrorDescription.
    DFE_DataPresentation                                  =    2 # Вид представления данных(0 - в виде строк, разделенных  , 1 - в виде json)
    DFE_PlainTransfer                                     =    3 # Прямая передача команд поверх надежных протоколов нижнего уровня (TCP)
    DFE_BlockingMode                                      =    4 # Эксклюзивная обработка команд на ККТ (блокировка команд на остальных интерфейсах, доступно только если передача надежная (TCP) )
    DFE_SkipRequisitePrint                                =    5 # Пропуск печати реквизитов документов средствами драйвера. Если установлено в 1, то печать управляется в зависимости от поля "печать реквизитов пользователя" Т17П12 или "АВТОПЕЧАТЬ ТЕГОВ в КЯ" Т1П50 в КЯ
    DFE_UseDefaultPropertyIfNotSetByUser                  =    6 # 
    ###################################################################################################################################
    # DataPresentationFormat: 
    DPF_ClassicText                                       =    0 # Данные в виде строк с разделителем   и уровнем вложенности за счет пробелов в начале строки
    DPF_ClassicJson                                       =    1 # Данные в виде json {"tag": 1234, "value": "значение", "desc": "описание тега"}.
    ###################################################################################################################################
    # TagTypeEnumeration: 
    TT_Byte                                               =    0 # Тип Byte.
    TT_Uint16                                             =    1 # Тип Uint16.
    TT_Uint32                                             =    2 # Тип UInt32.
    TT_VLN                                                =    3 # Тип VLN.
    TT_FVLN                                               =    4 # Тип FVLN.
    TT_BitMask                                            =    5 # Тип "битовое поле".
    TT_UnixTime                                           =    6 # Тип "время".
    TT_String                                             =    7 # Тип "строка".
    TT_STLV                                               =    8 # Тип составной тег
    TT_ByteArray                                          =    9 # Тип массив байт
    ###################################################################################################################################
    # MeasurementUnitEnumeration: Мера количества предмета расчета, свойство MeasureUnit (тег 2108)
    MU_Item                                               =    0 # Применяется для предметов расчета, которые могут быть реализованы поштучно или единицами
    MU_Gram                                               =   10 # Грамм
    MU_Kilogram                                           =   11 # Килограмм
    MU_Ton                                                =   12 # Тонна
    MU_Centimeter                                         =   20 # Сантиметр
    MU_Decimeter                                          =   21 # Дециметр
    MU_Meter                                              =   22 # Метр
    MU_SquareCentimeter                                   =   30 # Квадратный сантиметр
    MU_SquareDecimeter                                    =   31 # Квадратный дециметр
    MU_SquareMeter                                        =   32 # Квадратный метр
    MU_Milliliter                                         =   40 # Миллилитр
    MU_Liter                                              =   41 # Литр
    MU_CubicMeter                                         =   42 # Кубический метр
    MU_KilowattHour                                       =   50 # Киловатт час
    MU_Gigacalorie                                        =   51 # Гигакалория
    MU_Day                                                =   70 # Сутки (день)
    MU_Hour                                               =   71 # Час
    MU_Minute                                             =   72 # Минута
    MU_Second                                             =   73 # Секунда
    MU_Kilobyte                                           =   80 # Килобайт
    MU_Megabyte                                           =   81 # Мегабайт
    MU_Gigabyte                                           =   82 # Гигабайт
    MU_Terabyte                                           =   83 # Терабайт
    MU_Other                                              =  255 # Применяется при использовании иных единиц измерения

    def __init__(self, instance_prefix='fr_drv_ng'):
        global classicInterfaceWrap
        self.context = None
        if classicInterfaceWrap is None:
            classicInterfaceWrap = ClassicInterfaceWrap()
        self.context = classicInterfaceWrap.c_classic_init(wrapString(instance_prefix))

    def __del__(self):
        global classicInterfaceWrap
        if classicInterfaceWrap and self.context:
            classicInterfaceWrap.c_classic_deinit(self.context)
        self.context = None


    def AddLD(self):
        return classicInterfaceWrap.AddLD(self.context)

    def Beep(self): # Гудок
        return classicInterfaceWrap.Beep(self.context)

    def Buy(self): # Покупка
        return classicInterfaceWrap.Buy(self.context)

    def BuyEx(self):
        return classicInterfaceWrap.BuyEx(self.context)

    def CancelCheck(self): # Аннулировать чек
        return classicInterfaceWrap.CancelCheck(self.context)

    def CashIncome(self): # Внесение
        return classicInterfaceWrap.CashIncome(self.context)

    def CashOutcome(self): # Выплата
        return classicInterfaceWrap.CashOutcome(self.context)

    def Charge(self): # Надбавка
        return classicInterfaceWrap.Charge(self.context)

    def CheckSubTotal(self): # Подытог чека
        return classicInterfaceWrap.CheckSubTotal(self.context)

    def CloseCheck(self): # Закрыть чек
        return classicInterfaceWrap.CloseCheck(self.context)

    def ConfirmDate(self): # Подтвердить дату
        return classicInterfaceWrap.ConfirmDate(self.context)

    def Connect(self): # Установить связь
        return classicInterfaceWrap.Connect(self.context)

    def ContinuePrint(self): # Продолжить печать
        return classicInterfaceWrap.ContinuePrint(self.context)

    def Correction(self):
        return classicInterfaceWrap.Correction(self.context)

    def CutCheck(self): # Отрезать чек
        return classicInterfaceWrap.CutCheck(self.context)

    def DampRequest(self): # Запрос дампа
        return classicInterfaceWrap.DampRequest(self.context)

    def DeleteLD(self):
        return classicInterfaceWrap.DeleteLD(self.context)

    def Disconnect(self): # Разорвать связь
        return classicInterfaceWrap.Disconnect(self.context)

    def Discount(self): # Скидка
        return classicInterfaceWrap.Discount(self.context)

    def DozeOilCheck(self):
        return classicInterfaceWrap.DozeOilCheck(self.context)

    def Draw(self): # ПечатьКартинки
        return classicInterfaceWrap.Draw(self.context)

    def EKLZDepartmentReportInDatesRange(self):
        return classicInterfaceWrap.EKLZDepartmentReportInDatesRange(self.context)

    def EKLZDepartmentReportInSessionsRange(self):
        return classicInterfaceWrap.EKLZDepartmentReportInSessionsRange(self.context)

    def EKLZJournalOnSessionNumber(self):
        return classicInterfaceWrap.EKLZJournalOnSessionNumber(self.context)

    def EKLZSessionReportInDatesRange(self):
        return classicInterfaceWrap.EKLZSessionReportInDatesRange(self.context)

    def EKLZSessionReportInSessionsRange(self):
        return classicInterfaceWrap.EKLZSessionReportInSessionsRange(self.context)

    def ExchangeBytes(self): # Метод посылает последовательность байтов от хоста в ККТ и получает ответ
        return classicInterfaceWrap.ExchangeBytes(self.context)

    def FeedDocument(self): # Продвинуть документ
        return classicInterfaceWrap.FeedDocument(self.context)

    def Fiscalization(self): # Фискализация
        return classicInterfaceWrap.Fiscalization(self.context)

    def FiscalReportForDatesRange(self): # Фискальный отчёт по диапазону дат
        return classicInterfaceWrap.FiscalReportForDatesRange(self.context)

    def FiscalReportForSessionRange(self): # Фискальный отчёт по диапазону смен
        return classicInterfaceWrap.FiscalReportForSessionRange(self.context)

    def GetActiveLD(self):
        return classicInterfaceWrap.GetActiveLD(self.context)

    def EnumLD(self):
        return classicInterfaceWrap.EnumLD(self.context)

    def GetCashReg(self): # Получить денежный регистр
        return classicInterfaceWrap.GetCashReg(self.context)

    def GetCountLD(self):
        return classicInterfaceWrap.GetCountLD(self.context)

    def GetData(self): # Получить данные
        return classicInterfaceWrap.GetData(self.context)

    def GetDeviceMetrics(self): # Получить параметры устройства
        return classicInterfaceWrap.GetDeviceMetrics(self.context)

    def GetECRStatus(self): # Получить состояние ККМ
        return classicInterfaceWrap.GetECRStatus(self.context)

    def GetShortECRStatus(self): # Получить короткий запрос состояния ККМ
        return classicInterfaceWrap.GetShortECRStatus(self.context)

    def GetExchangeParam(self): # Получить параметры обмена
        return classicInterfaceWrap.GetExchangeParam(self.context)

    def GetFieldStruct(self): # Получить структуру поля
        return classicInterfaceWrap.GetFieldStruct(self.context)

    def GetFiscalizationParameters(self): # Получить параметры фискализации
        return classicInterfaceWrap.GetFiscalizationParameters(self.context)

    def GetFMRecordsSum(self): # Получить сумму записей ФП
        return classicInterfaceWrap.GetFMRecordsSum(self.context)

    def GetLastFMRecordDate(self): # Получить дату последней записи в ФП
        return classicInterfaceWrap.GetLastFMRecordDate(self.context)

    def GetLiterSumCounter(self):
        return classicInterfaceWrap.GetLiterSumCounter(self.context)

    def GetOperationReg(self): # Получить операционный регистр
        return classicInterfaceWrap.GetOperationReg(self.context)

    def GetParamLD(self):
        return classicInterfaceWrap.GetParamLD(self.context)

    def GetRangeDatesAndSessions(self): # Получить диапазон дат и смен
        return classicInterfaceWrap.GetRangeDatesAndSessions(self.context)

    def GetRKStatus(self):
        return classicInterfaceWrap.GetRKStatus(self.context)

    def GetTableStruct(self): # Получить структуру таблицы
        return classicInterfaceWrap.GetTableStruct(self.context)

    def InitFM(self): # Инициализировать ФП
        return classicInterfaceWrap.InitFM(self.context)

    def InitTable(self): # Инициализировать таблицы
        return classicInterfaceWrap.InitTable(self.context)

    def InterruptDataStream(self): # Прервать выдачу данных
        return classicInterfaceWrap.InterruptDataStream(self.context)

    def InterruptFullReport(self): # Прервать полный отчёт
        return classicInterfaceWrap.InterruptFullReport(self.context)

    def InterruptTest(self): # Прервать тестовый прогон
        return classicInterfaceWrap.InterruptTest(self.context)

    def LaunchRK(self):
        return classicInterfaceWrap.LaunchRK(self.context)

    def LoadLineData(self):
        return classicInterfaceWrap.LoadLineData(self.context)

    def OilSale(self):
        return classicInterfaceWrap.OilSale(self.context)

    def OpenCheck(self): # Открыть чек
        return classicInterfaceWrap.OpenCheck(self.context)

    def OpenDrawer(self): # Открыть денежный ящик
        return classicInterfaceWrap.OpenDrawer(self.context)

    def PrintBarCode(self): # Напечатать штрихкод
        return classicInterfaceWrap.PrintBarCode(self.context)

    def PrintDepartmentReport(self): # Напечатать отчет по отделам
        return classicInterfaceWrap.PrintDepartmentReport(self.context)

    def PrintDocumentTitle(self): # Печать заголовка документа
        return classicInterfaceWrap.PrintDocumentTitle(self.context)

    def PrintOperationReg(self): # Печать операционных регистров
        return classicInterfaceWrap.PrintOperationReg(self.context)

    def PrintReportWithCleaning(self): # Снять отчёт с гашением
        return classicInterfaceWrap.PrintReportWithCleaning(self.context)

    def PrintReportWithoutCleaning(self): # Снять отчёт без гашения
        return classicInterfaceWrap.PrintReportWithoutCleaning(self.context)

    def PrintString(self): # Печать cтроки
        return classicInterfaceWrap.PrintString(self.context)

    def PrintWideString(self): # Печать жирной cтроки
        return classicInterfaceWrap.PrintWideString(self.context)

    def ReadEKLZDocumentOnKPK(self):
        return classicInterfaceWrap.ReadEKLZDocumentOnKPK(self.context)

    def ReadEKLZSessionTotal(self):
        return classicInterfaceWrap.ReadEKLZSessionTotal(self.context)

    def ReadLicense(self): # Прочитать лицензию
        return classicInterfaceWrap.ReadLicense(self.context)

    def ReadTable(self): # Прочитать таблицу
        return classicInterfaceWrap.ReadTable(self.context)

    def RepeatDocument(self): # Повторить документ
        return classicInterfaceWrap.RepeatDocument(self.context)

    def ResetAllTRK(self):
        return classicInterfaceWrap.ResetAllTRK(self.context)

    def ResetRK(self):
        return classicInterfaceWrap.ResetRK(self.context)

    def ResetSettings(self): # Технологическое обнуление
        return classicInterfaceWrap.ResetSettings(self.context)

    def ResetSummary(self): # Общее гашение
        return classicInterfaceWrap.ResetSummary(self.context)

    def ReturnBuy(self): # Возврат покупки
        return classicInterfaceWrap.ReturnBuy(self.context)

    def ReturnBuyEx(self):
        return classicInterfaceWrap.ReturnBuyEx(self.context)

    def ReturnSale(self): # Возврат продажи
        return classicInterfaceWrap.ReturnSale(self.context)

    def ReturnSaleEx(self):
        return classicInterfaceWrap.ReturnSaleEx(self.context)

    def Sale(self): # Продажа
        return classicInterfaceWrap.Sale(self.context)

    def SaleEx(self):
        return classicInterfaceWrap.SaleEx(self.context)

    def SetActiveLD(self):
        return classicInterfaceWrap.SetActiveLD(self.context)

    def SetDate(self): # Установить дату
        return classicInterfaceWrap.SetDate(self.context)

    def SetDozeInMilliliters(self):
        return classicInterfaceWrap.SetDozeInMilliliters(self.context)

    def SetDozeInMoney(self):
        return classicInterfaceWrap.SetDozeInMoney(self.context)

    def SetExchangeParam(self): # Установить Параметры Обмена
        return classicInterfaceWrap.SetExchangeParam(self.context)

    def SetParamLD(self):
        return classicInterfaceWrap.SetParamLD(self.context)

    def SetPointPosition(self): # Установить положение точки
        return classicInterfaceWrap.SetPointPosition(self.context)

    def SetRKParameters(self):
        return classicInterfaceWrap.SetRKParameters(self.context)

    def SetSerialNumber(self): # Установить заводской номер
        return classicInterfaceWrap.SetSerialNumber(self.context)

    def SetTime(self): # Установить время
        return classicInterfaceWrap.SetTime(self.context)

    def ShowProperties(self):
        return classicInterfaceWrap.ShowProperties(self.context)

    def StopEKLZDocumentPrinting(self):
        return classicInterfaceWrap.StopEKLZDocumentPrinting(self.context)

    def StopRK(self):
        return classicInterfaceWrap.StopRK(self.context)

    def Storno(self): # Сторно
        return classicInterfaceWrap.Storno(self.context)

    def StornoEx(self):
        return classicInterfaceWrap.StornoEx(self.context)

    def StornoCharge(self): # Сторно надбавки
        return classicInterfaceWrap.StornoCharge(self.context)

    def StornoDiscount(self): # Сторно скидки
        return classicInterfaceWrap.StornoDiscount(self.context)

    def SummOilCheck(self):
        return classicInterfaceWrap.SummOilCheck(self.context)

    def SysAdminCancelCheck(self): # Отмена чека администратором
        return classicInterfaceWrap.SysAdminCancelCheck(self.context)

    def Test(self): # Тестовый прогон
        return classicInterfaceWrap.Test(self.context)

    def WriteLicense(self): # Записать лицензию
        return classicInterfaceWrap.WriteLicense(self.context)

    def WriteTable(self): # Записать таблицу
        return classicInterfaceWrap.WriteTable(self.context)

    def PrintStringWithFont(self): # Печать cтроки данным шрифтом
        return classicInterfaceWrap.PrintStringWithFont(self.context)

    def Get_BatteryCondition(self):
        return classicInterfaceWrap.Get_BatteryCondition(self.context)

    def Get_CheckResult(self):
        return classicInterfaceWrap.Get_CheckResult(self.context)

    def Set_CheckResult(self, value):
        classicInterfaceWrap.Set_CheckResult(self.context, value)

    def Get_CurrentDozeInMilliliters(self):
        return classicInterfaceWrap.Get_CurrentDozeInMilliliters(self.context)

    def Set_CurrentDozeInMilliliters(self, value):
        classicInterfaceWrap.Set_CurrentDozeInMilliliters(self.context, value)

    def Get_CurrentDozeInMoney(self):
        return classicInterfaceWrap.Get_CurrentDozeInMoney(self.context)

    def Set_CurrentDozeInMoney(self, value):
        classicInterfaceWrap.Set_CurrentDozeInMoney(self.context, value)

    def Get_DozeInMilliliters(self):
        return classicInterfaceWrap.Get_DozeInMilliliters(self.context)

    def Set_DozeInMilliliters(self, value):
        classicInterfaceWrap.Set_DozeInMilliliters(self.context, value)

    def Get_DozeInMoney(self):
        return classicInterfaceWrap.Get_DozeInMoney(self.context)

    def Set_DozeInMoney(self, value):
        classicInterfaceWrap.Set_DozeInMoney(self.context, value)

    def Get_ECRAdvancedModeDescription(self): # Описание подрежима ККМ
        resultLen = classicInterfaceWrap.Get_ECRAdvancedModeDescription(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ECRAdvancedModeDescription(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_ECRInput(self):
        resultLen = classicInterfaceWrap.Get_ECRInput(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ECRInput(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_ECROutput(self):
        resultLen = classicInterfaceWrap.Get_ECROutput(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ECROutput(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_EmergencyStopCode(self):
        return classicInterfaceWrap.Get_EmergencyStopCode(self.context)

    def Get_EmergencyStopCodeDescription(self):
        resultLen = classicInterfaceWrap.Get_EmergencyStopCodeDescription(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_EmergencyStopCodeDescription(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_IsCheckClosed(self):
        return classicInterfaceWrap.Get_IsCheckClosed(self.context)

    def Get_IsCheckMadeOut(self):
        return classicInterfaceWrap.Get_IsCheckMadeOut(self.context)

    def Get_KPKNumber(self):
        return classicInterfaceWrap.Get_KPKNumber(self.context)

    def Set_KPKNumber(self, value):
        classicInterfaceWrap.Set_KPKNumber(self.context, value)

    def Get_Motor(self):
        return classicInterfaceWrap.Get_Motor(self.context)

    def Get_Pistol(self):
        return classicInterfaceWrap.Get_Pistol(self.context)

    def Get_RKNumber(self):
        return classicInterfaceWrap.Get_RKNumber(self.context)

    def Set_RKNumber(self, value):
        classicInterfaceWrap.Set_RKNumber(self.context, value)

    def Get_RoughValve(self):
        return classicInterfaceWrap.Get_RoughValve(self.context)

    def Get_SlowingInMilliliters(self):
        return classicInterfaceWrap.Get_SlowingInMilliliters(self.context)

    def Set_SlowingInMilliliters(self, value):
        classicInterfaceWrap.Set_SlowingInMilliliters(self.context, value)

    def Get_SlowingValve(self):
        return classicInterfaceWrap.Get_SlowingValve(self.context)

    def Get_StatusRK(self):
        return classicInterfaceWrap.Get_StatusRK(self.context)

    def Get_StatusRKDescription(self):
        resultLen = classicInterfaceWrap.Get_StatusRKDescription(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_StatusRKDescription(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_TRKNumber(self):
        return classicInterfaceWrap.Get_TRKNumber(self.context)

    def Set_TRKNumber(self, value):
        classicInterfaceWrap.Set_TRKNumber(self.context, value)

    def Get_LDBaudrate(self):
        return classicInterfaceWrap.Get_LDBaudrate(self.context)

    def Set_LDBaudrate(self, value):
        classicInterfaceWrap.Set_LDBaudrate(self.context, value)

    def Get_LDComNumber(self):
        return classicInterfaceWrap.Get_LDComNumber(self.context)

    def Set_LDComNumber(self, value):
        classicInterfaceWrap.Set_LDComNumber(self.context, value)

    def Get_LDCount(self):
        return classicInterfaceWrap.Get_LDCount(self.context)

    def Get_LDIndex(self):
        return classicInterfaceWrap.Get_LDIndex(self.context)

    def Set_LDIndex(self, value):
        classicInterfaceWrap.Set_LDIndex(self.context, value)

    def Get_LDName(self):
        resultLen = classicInterfaceWrap.Get_LDName(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_LDName(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_LDName(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_LDName(self.context, valueBuff, len(valueBuff))

    def Get_LDNumber(self):
        return classicInterfaceWrap.Get_LDNumber(self.context)

    def Set_LDNumber(self, value):
        classicInterfaceWrap.Set_LDNumber(self.context, value)

    def Get_WaitPrintingTime(self):
        return classicInterfaceWrap.Get_WaitPrintingTime(self.context)

    def EKLZActivizationResult(self):
        return classicInterfaceWrap.EKLZActivizationResult(self.context)

    def EKLZActivization(self):
        return classicInterfaceWrap.EKLZActivization(self.context)

    def CloseEKLZArchive(self):
        return classicInterfaceWrap.CloseEKLZArchive(self.context)

    def GetEKLZSerialNumber(self):
        return classicInterfaceWrap.GetEKLZSerialNumber(self.context)

    def Get_EKLZNumber(self):
        resultLen = classicInterfaceWrap.Get_EKLZNumber(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_EKLZNumber(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def EKLZInterrupt(self):
        return classicInterfaceWrap.EKLZInterrupt(self.context)

    def GetEKLZCode1Report(self):
        return classicInterfaceWrap.GetEKLZCode1Report(self.context)

    def Get_LastKPKDocumentResult(self):
        return classicInterfaceWrap.Get_LastKPKDocumentResult(self.context)

    def Get_LastKPKDate(self):
        return unwrapDateTime(classicInterfaceWrap.Get_LastKPKDate(self.context))

    def Get_LastKPKTime(self):
        return unwrapDateTime(classicInterfaceWrap.Get_LastKPKTime(self.context))

    def Get_LastKPKNumber(self):
        return classicInterfaceWrap.Get_LastKPKNumber(self.context)

    def Get_EKLZFlags(self):
        return classicInterfaceWrap.Get_EKLZFlags(self.context)

    def GetEKLZCode2Report(self):
        return classicInterfaceWrap.GetEKLZCode2Report(self.context)

    def TestEKLZArchiveIntegrity(self):
        return classicInterfaceWrap.TestEKLZArchiveIntegrity(self.context)

    def Get_TestNumber(self):
        return classicInterfaceWrap.Get_TestNumber(self.context)

    def Set_TestNumber(self, value):
        classicInterfaceWrap.Set_TestNumber(self.context, value)

    def Get_EKLZVersion(self):
        resultLen = classicInterfaceWrap.Get_EKLZVersion(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_EKLZVersion(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_EKLZData(self):
        resultLen = classicInterfaceWrap.Get_EKLZData(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_EKLZData(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def GetEKLZVersion(self):
        return classicInterfaceWrap.GetEKLZVersion(self.context)

    def InitEKLZArchive(self):
        return classicInterfaceWrap.InitEKLZArchive(self.context)

    def GetEKLZData(self):
        return classicInterfaceWrap.GetEKLZData(self.context)

    def GetEKLZJournal(self):
        return classicInterfaceWrap.GetEKLZJournal(self.context)

    def GetEKLZDocument(self):
        return classicInterfaceWrap.GetEKLZDocument(self.context)

    def GetEKLZDepartmentReportInDatesRange(self):
        return classicInterfaceWrap.GetEKLZDepartmentReportInDatesRange(self.context)

    def GetEKLZDepartmentReportInSessionsRange(self):
        return classicInterfaceWrap.GetEKLZDepartmentReportInSessionsRange(self.context)

    def GetEKLZSessionReportInDatesRange(self):
        return classicInterfaceWrap.GetEKLZSessionReportInDatesRange(self.context)

    def GetEKLZSessionReportInSessionsRange(self):
        return classicInterfaceWrap.GetEKLZSessionReportInSessionsRange(self.context)

    def GetEKLZSessionTotal(self):
        return classicInterfaceWrap.GetEKLZSessionTotal(self.context)

    def GetEKLZActivizationResult(self):
        return classicInterfaceWrap.GetEKLZActivizationResult(self.context)

    def SetEKLZResultCode(self):
        return classicInterfaceWrap.SetEKLZResultCode(self.context)

    def OpenFiscalSlipDocument(self):
        return classicInterfaceWrap.OpenFiscalSlipDocument(self.context)

    def OpenStandardFiscalSlipDocument(self):
        return classicInterfaceWrap.OpenStandardFiscalSlipDocument(self.context)

    def RegistrationOnSlipDocument(self):
        return classicInterfaceWrap.RegistrationOnSlipDocument(self.context)

    def StandardRegistrationOnSlipDocument(self):
        return classicInterfaceWrap.StandardRegistrationOnSlipDocument(self.context)

    def ChargeOnSlipDocument(self):
        return classicInterfaceWrap.ChargeOnSlipDocument(self.context)

    def StandardChargeOnSlipDocument(self):
        return classicInterfaceWrap.StandardChargeOnSlipDocument(self.context)

    def CloseCheckOnSlipDocument(self):
        return classicInterfaceWrap.CloseCheckOnSlipDocument(self.context)

    def StandardCloseCheckOnSlipDocument(self):
        return classicInterfaceWrap.StandardCloseCheckOnSlipDocument(self.context)

    def ConfigureSlipDocument(self):
        return classicInterfaceWrap.ConfigureSlipDocument(self.context)

    def ConfigureStandardSlipDocument(self):
        return classicInterfaceWrap.ConfigureStandardSlipDocument(self.context)

    def FillSlipDocumentWithUnfiscalInfo(self):
        return classicInterfaceWrap.FillSlipDocumentWithUnfiscalInfo(self.context)

    def ClearSlipDocumentBufferString(self):
        return classicInterfaceWrap.ClearSlipDocumentBufferString(self.context)

    def ClearSlipDocumentBuffer(self):
        return classicInterfaceWrap.ClearSlipDocumentBuffer(self.context)

    def PrintSlipDocument(self):
        return classicInterfaceWrap.PrintSlipDocument(self.context)

    def Get_CopyType(self):
        return classicInterfaceWrap.Get_CopyType(self.context)

    def Set_CopyType(self, value):
        classicInterfaceWrap.Set_CopyType(self.context, value)

    def Get_NumberOfCopies(self):
        return classicInterfaceWrap.Get_NumberOfCopies(self.context)

    def Set_NumberOfCopies(self, value):
        classicInterfaceWrap.Set_NumberOfCopies(self.context, value)

    def Get_CopyOffset1(self):
        return classicInterfaceWrap.Get_CopyOffset1(self.context)

    def Set_CopyOffset1(self, value):
        classicInterfaceWrap.Set_CopyOffset1(self.context, value)

    def Get_CopyOffset2(self):
        return classicInterfaceWrap.Get_CopyOffset2(self.context)

    def Set_CopyOffset2(self, value):
        classicInterfaceWrap.Set_CopyOffset2(self.context, value)

    def Get_CopyOffset3(self):
        return classicInterfaceWrap.Get_CopyOffset3(self.context)

    def Set_CopyOffset3(self, value):
        classicInterfaceWrap.Set_CopyOffset3(self.context, value)

    def Get_CopyOffset4(self):
        return classicInterfaceWrap.Get_CopyOffset4(self.context)

    def Set_CopyOffset4(self, value):
        classicInterfaceWrap.Set_CopyOffset4(self.context, value)

    def Get_CopyOffset5(self):
        return classicInterfaceWrap.Get_CopyOffset5(self.context)

    def Set_CopyOffset5(self, value):
        classicInterfaceWrap.Set_CopyOffset5(self.context, value)

    def Get_ClicheFont(self):
        return classicInterfaceWrap.Get_ClicheFont(self.context)

    def Set_ClicheFont(self, value):
        classicInterfaceWrap.Set_ClicheFont(self.context, value)

    def Get_HeaderFont(self):
        return classicInterfaceWrap.Get_HeaderFont(self.context)

    def Set_HeaderFont(self, value):
        classicInterfaceWrap.Set_HeaderFont(self.context, value)

    def Get_EKLZFont(self):
        return classicInterfaceWrap.Get_EKLZFont(self.context)

    def Set_EKLZFont(self, value):
        classicInterfaceWrap.Set_EKLZFont(self.context, value)

    def Get_ClicheStringNumber(self):
        return classicInterfaceWrap.Get_ClicheStringNumber(self.context)

    def Set_ClicheStringNumber(self, value):
        classicInterfaceWrap.Set_ClicheStringNumber(self.context, value)

    def Get_HeaderStringNumber(self):
        return classicInterfaceWrap.Get_HeaderStringNumber(self.context)

    def Set_HeaderStringNumber(self, value):
        classicInterfaceWrap.Set_HeaderStringNumber(self.context, value)

    def Get_EKLZStringNumber(self):
        return classicInterfaceWrap.Get_EKLZStringNumber(self.context)

    def Set_EKLZStringNumber(self, value):
        classicInterfaceWrap.Set_EKLZStringNumber(self.context, value)

    def Get_FMStringNumber(self):
        return classicInterfaceWrap.Get_FMStringNumber(self.context)

    def Set_FMStringNumber(self, value):
        classicInterfaceWrap.Set_FMStringNumber(self.context, value)

    def Get_ClicheOffset(self):
        return classicInterfaceWrap.Get_ClicheOffset(self.context)

    def Set_ClicheOffset(self, value):
        classicInterfaceWrap.Set_ClicheOffset(self.context, value)

    def Get_HeaderOffset(self):
        return classicInterfaceWrap.Get_HeaderOffset(self.context)

    def Set_HeaderOffset(self, value):
        classicInterfaceWrap.Set_HeaderOffset(self.context, value)

    def Get_EKLZOffset(self):
        return classicInterfaceWrap.Get_EKLZOffset(self.context)

    def Set_EKLZOffset(self, value):
        classicInterfaceWrap.Set_EKLZOffset(self.context, value)

    def Get_KPKOffset(self):
        return classicInterfaceWrap.Get_KPKOffset(self.context)

    def Set_KPKOffset(self, value):
        classicInterfaceWrap.Set_KPKOffset(self.context, value)

    def Get_FMOffset(self):
        return classicInterfaceWrap.Get_FMOffset(self.context)

    def Set_FMOffset(self, value):
        classicInterfaceWrap.Set_FMOffset(self.context, value)

    def Get_OperationBlockFirstString(self):
        return classicInterfaceWrap.Get_OperationBlockFirstString(self.context)

    def Set_OperationBlockFirstString(self, value):
        classicInterfaceWrap.Set_OperationBlockFirstString(self.context, value)

    def Get_QuantityFormat(self):
        return classicInterfaceWrap.Get_QuantityFormat(self.context)

    def Set_QuantityFormat(self, value):
        classicInterfaceWrap.Set_QuantityFormat(self.context, value)

    def Get_StringQuantityInOperation(self):
        return classicInterfaceWrap.Get_StringQuantityInOperation(self.context)

    def Set_StringQuantityInOperation(self, value):
        classicInterfaceWrap.Set_StringQuantityInOperation(self.context, value)

    def Get_TextStringNumber(self):
        return classicInterfaceWrap.Get_TextStringNumber(self.context)

    def Set_TextStringNumber(self, value):
        classicInterfaceWrap.Set_TextStringNumber(self.context, value)

    def Get_QuantityStringNumber(self):
        return classicInterfaceWrap.Get_QuantityStringNumber(self.context)

    def Set_QuantityStringNumber(self, value):
        classicInterfaceWrap.Set_QuantityStringNumber(self.context, value)

    def Get_SummStringNumber(self):
        return classicInterfaceWrap.Get_SummStringNumber(self.context)

    def Set_SummStringNumber(self, value):
        classicInterfaceWrap.Set_SummStringNumber(self.context, value)

    def Get_DepartmentStringNumber(self):
        return classicInterfaceWrap.Get_DepartmentStringNumber(self.context)

    def Set_DepartmentStringNumber(self, value):
        classicInterfaceWrap.Set_DepartmentStringNumber(self.context, value)

    def Get_TextFont(self):
        return classicInterfaceWrap.Get_TextFont(self.context)

    def Set_TextFont(self, value):
        classicInterfaceWrap.Set_TextFont(self.context, value)

    def Get_QuantityFont(self):
        return classicInterfaceWrap.Get_QuantityFont(self.context)

    def Set_QuantityFont(self, value):
        classicInterfaceWrap.Set_QuantityFont(self.context, value)

    def Get_MultiplicationFont(self):
        return classicInterfaceWrap.Get_MultiplicationFont(self.context)

    def Set_MultiplicationFont(self, value):
        classicInterfaceWrap.Set_MultiplicationFont(self.context, value)

    def Get_PriceFont(self):
        return classicInterfaceWrap.Get_PriceFont(self.context)

    def Set_PriceFont(self, value):
        classicInterfaceWrap.Set_PriceFont(self.context, value)

    def Get_SummFont(self):
        return classicInterfaceWrap.Get_SummFont(self.context)

    def Set_SummFont(self, value):
        classicInterfaceWrap.Set_SummFont(self.context, value)

    def Get_DepartmentFont(self):
        return classicInterfaceWrap.Get_DepartmentFont(self.context)

    def Set_DepartmentFont(self, value):
        classicInterfaceWrap.Set_DepartmentFont(self.context, value)

    def Get_TextSymbolNumber(self):
        return classicInterfaceWrap.Get_TextSymbolNumber(self.context)

    def Set_TextSymbolNumber(self, value):
        classicInterfaceWrap.Set_TextSymbolNumber(self.context, value)

    def Get_QuantitySymbolNumber(self):
        return classicInterfaceWrap.Get_QuantitySymbolNumber(self.context)

    def Set_QuantitySymbolNumber(self, value):
        classicInterfaceWrap.Set_QuantitySymbolNumber(self.context, value)

    def Get_PriceSymbolNumber(self):
        return classicInterfaceWrap.Get_PriceSymbolNumber(self.context)

    def Set_PriceSymbolNumber(self, value):
        classicInterfaceWrap.Set_PriceSymbolNumber(self.context, value)

    def Get_SummSymbolNumber(self):
        return classicInterfaceWrap.Get_SummSymbolNumber(self.context)

    def Set_SummSymbolNumber(self, value):
        classicInterfaceWrap.Set_SummSymbolNumber(self.context, value)

    def Get_DepartmentSymbolNumber(self):
        return classicInterfaceWrap.Get_DepartmentSymbolNumber(self.context)

    def Set_DepartmentSymbolNumber(self, value):
        classicInterfaceWrap.Set_DepartmentSymbolNumber(self.context, value)

    def Get_TextOffset(self):
        return classicInterfaceWrap.Get_TextOffset(self.context)

    def Set_TextOffset(self, value):
        classicInterfaceWrap.Set_TextOffset(self.context, value)

    def Get_QuantityOffset(self):
        return classicInterfaceWrap.Get_QuantityOffset(self.context)

    def Set_QuantityOffset(self, value):
        classicInterfaceWrap.Set_QuantityOffset(self.context, value)

    def Get_SummOffset(self):
        return classicInterfaceWrap.Get_SummOffset(self.context)

    def Set_SummOffset(self, value):
        classicInterfaceWrap.Set_SummOffset(self.context, value)

    def Get_DepartmentOffset(self):
        return classicInterfaceWrap.Get_DepartmentOffset(self.context)

    def Set_DepartmentOffset(self, value):
        classicInterfaceWrap.Set_DepartmentOffset(self.context, value)

    def DiscountOnSlipDocument(self):
        return classicInterfaceWrap.DiscountOnSlipDocument(self.context)

    def StandardDiscountOnSlipDocument(self):
        return classicInterfaceWrap.StandardDiscountOnSlipDocument(self.context)

    def Get_IsClearUnfiscalInfo(self):
        return classicInterfaceWrap.Get_IsClearUnfiscalInfo(self.context)

    def Set_IsClearUnfiscalInfo(self, value):
        classicInterfaceWrap.Set_IsClearUnfiscalInfo(self.context, value)

    def Get_InfoType(self):
        return classicInterfaceWrap.Get_InfoType(self.context)

    def Set_InfoType(self, value):
        classicInterfaceWrap.Set_InfoType(self.context, value)

    def Get_StringNumber(self):
        return classicInterfaceWrap.Get_StringNumber(self.context)

    def Set_StringNumber(self, value):
        classicInterfaceWrap.Set_StringNumber(self.context, value)

    def EjectSlipDocument(self):
        return classicInterfaceWrap.EjectSlipDocument(self.context)

    def Get_EjectDirection(self):
        return classicInterfaceWrap.Get_EjectDirection(self.context)

    def Set_EjectDirection(self, value):
        classicInterfaceWrap.Set_EjectDirection(self.context, value)

    def LoadLineDataEx(self):
        return classicInterfaceWrap.LoadLineDataEx(self.context)

    def DrawEx(self):
        return classicInterfaceWrap.DrawEx(self.context)

    def ConfigureGeneralSlipDocument(self):
        return classicInterfaceWrap.ConfigureGeneralSlipDocument(self.context)

    def Get_OperationNameStringNumber(self):
        return classicInterfaceWrap.Get_OperationNameStringNumber(self.context)

    def Set_OperationNameStringNumber(self, value):
        classicInterfaceWrap.Set_OperationNameStringNumber(self.context, value)

    def Get_OperationNameFont(self):
        return classicInterfaceWrap.Get_OperationNameFont(self.context)

    def Set_OperationNameFont(self, value):
        classicInterfaceWrap.Set_OperationNameFont(self.context, value)

    def Get_OperationNameOffset(self):
        return classicInterfaceWrap.Get_OperationNameOffset(self.context)

    def Set_OperationNameOffset(self, value):
        classicInterfaceWrap.Set_OperationNameOffset(self.context, value)

    def Get_TotalStringNumber(self):
        return classicInterfaceWrap.Get_TotalStringNumber(self.context)

    def Set_TotalStringNumber(self, value):
        classicInterfaceWrap.Set_TotalStringNumber(self.context, value)

    def Get_Summ1StringNumber(self):
        return classicInterfaceWrap.Get_Summ1StringNumber(self.context)

    def Set_Summ1StringNumber(self, value):
        classicInterfaceWrap.Set_Summ1StringNumber(self.context, value)

    def Get_Summ2StringNumber(self):
        return classicInterfaceWrap.Get_Summ2StringNumber(self.context)

    def Set_Summ2StringNumber(self, value):
        classicInterfaceWrap.Set_Summ2StringNumber(self.context, value)

    def Get_Summ3StringNumber(self):
        return classicInterfaceWrap.Get_Summ3StringNumber(self.context)

    def Set_Summ3StringNumber(self, value):
        classicInterfaceWrap.Set_Summ3StringNumber(self.context, value)

    def Get_Summ4StringNumber(self):
        return classicInterfaceWrap.Get_Summ4StringNumber(self.context)

    def Set_Summ4StringNumber(self, value):
        classicInterfaceWrap.Set_Summ4StringNumber(self.context, value)

    def Get_ChangeStringNumber(self):
        return classicInterfaceWrap.Get_ChangeStringNumber(self.context)

    def Set_ChangeStringNumber(self, value):
        classicInterfaceWrap.Set_ChangeStringNumber(self.context, value)

    def Get_Tax1TurnOverStringNumber(self):
        return classicInterfaceWrap.Get_Tax1TurnOverStringNumber(self.context)

    def Set_Tax1TurnOverStringNumber(self, value):
        classicInterfaceWrap.Set_Tax1TurnOverStringNumber(self.context, value)

    def Get_Tax2TurnOverStringNumber(self):
        return classicInterfaceWrap.Get_Tax2TurnOverStringNumber(self.context)

    def Set_Tax2TurnOverStringNumber(self, value):
        classicInterfaceWrap.Set_Tax2TurnOverStringNumber(self.context, value)

    def Get_Tax3TurnOverStringNumber(self):
        return classicInterfaceWrap.Get_Tax3TurnOverStringNumber(self.context)

    def Set_Tax3TurnOverStringNumber(self, value):
        classicInterfaceWrap.Set_Tax3TurnOverStringNumber(self.context, value)

    def Get_Tax4TurnOverStringNumber(self):
        return classicInterfaceWrap.Get_Tax4TurnOverStringNumber(self.context)

    def Set_Tax4TurnOverStringNumber(self, value):
        classicInterfaceWrap.Set_Tax4TurnOverStringNumber(self.context, value)

    def Get_Tax1SumStringNumber(self):
        return classicInterfaceWrap.Get_Tax1SumStringNumber(self.context)

    def Set_Tax1SumStringNumber(self, value):
        classicInterfaceWrap.Set_Tax1SumStringNumber(self.context, value)

    def Get_Tax2SumStringNumber(self):
        return classicInterfaceWrap.Get_Tax2SumStringNumber(self.context)

    def Set_Tax2SumStringNumber(self, value):
        classicInterfaceWrap.Set_Tax2SumStringNumber(self.context, value)

    def Get_Tax3SumStringNumber(self):
        return classicInterfaceWrap.Get_Tax3SumStringNumber(self.context)

    def Set_Tax3SumStringNumber(self, value):
        classicInterfaceWrap.Set_Tax3SumStringNumber(self.context, value)

    def Get_Tax4SumStringNumber(self):
        return classicInterfaceWrap.Get_Tax4SumStringNumber(self.context)

    def Set_Tax4SumStringNumber(self, value):
        classicInterfaceWrap.Set_Tax4SumStringNumber(self.context, value)

    def Get_SubTotalStringNumber(self):
        return classicInterfaceWrap.Get_SubTotalStringNumber(self.context)

    def Set_SubTotalStringNumber(self, value):
        classicInterfaceWrap.Set_SubTotalStringNumber(self.context, value)

    def Get_DiscountOnCheckStringNumber(self):
        return classicInterfaceWrap.Get_DiscountOnCheckStringNumber(self.context)

    def Set_DiscountOnCheckStringNumber(self, value):
        classicInterfaceWrap.Set_DiscountOnCheckStringNumber(self.context, value)

    def Get_TotalFont(self):
        return classicInterfaceWrap.Get_TotalFont(self.context)

    def Set_TotalFont(self, value):
        classicInterfaceWrap.Set_TotalFont(self.context, value)

    def Get_TotalSumFont(self):
        return classicInterfaceWrap.Get_TotalSumFont(self.context)

    def Set_TotalSumFont(self, value):
        classicInterfaceWrap.Set_TotalSumFont(self.context, value)

    def Get_Summ1Font(self):
        return classicInterfaceWrap.Get_Summ1Font(self.context)

    def Set_Summ1Font(self, value):
        classicInterfaceWrap.Set_Summ1Font(self.context, value)

    def Get_Summ1NameFont(self):
        return classicInterfaceWrap.Get_Summ1NameFont(self.context)

    def Set_Summ1NameFont(self, value):
        classicInterfaceWrap.Set_Summ1NameFont(self.context, value)

    def Get_Summ2NameFont(self):
        return classicInterfaceWrap.Get_Summ2NameFont(self.context)

    def Set_Summ2NameFont(self, value):
        classicInterfaceWrap.Set_Summ2NameFont(self.context, value)

    def Get_Summ3NameFont(self):
        return classicInterfaceWrap.Get_Summ3NameFont(self.context)

    def Set_Summ3NameFont(self, value):
        classicInterfaceWrap.Set_Summ3NameFont(self.context, value)

    def Get_Summ4NameFont(self):
        return classicInterfaceWrap.Get_Summ4NameFont(self.context)

    def Set_Summ4NameFont(self, value):
        classicInterfaceWrap.Set_Summ4NameFont(self.context, value)

    def Get_Summ2Font(self):
        return classicInterfaceWrap.Get_Summ2Font(self.context)

    def Set_Summ2Font(self, value):
        classicInterfaceWrap.Set_Summ2Font(self.context, value)

    def Get_Summ3Font(self):
        return classicInterfaceWrap.Get_Summ3Font(self.context)

    def Set_Summ3Font(self, value):
        classicInterfaceWrap.Set_Summ3Font(self.context, value)

    def Get_Summ4Font(self):
        return classicInterfaceWrap.Get_Summ4Font(self.context)

    def Set_Summ4Font(self, value):
        classicInterfaceWrap.Set_Summ4Font(self.context, value)

    def Get_ChangeFont(self):
        return classicInterfaceWrap.Get_ChangeFont(self.context)

    def Set_ChangeFont(self, value):
        classicInterfaceWrap.Set_ChangeFont(self.context, value)

    def Get_ChangeSumFont(self):
        return classicInterfaceWrap.Get_ChangeSumFont(self.context)

    def Set_ChangeSumFont(self, value):
        classicInterfaceWrap.Set_ChangeSumFont(self.context, value)

    def Get_Tax1NameFont(self):
        return classicInterfaceWrap.Get_Tax1NameFont(self.context)

    def Set_Tax1NameFont(self, value):
        classicInterfaceWrap.Set_Tax1NameFont(self.context, value)

    def Get_Tax2NameFont(self):
        return classicInterfaceWrap.Get_Tax2NameFont(self.context)

    def Set_Tax2NameFont(self, value):
        classicInterfaceWrap.Set_Tax2NameFont(self.context, value)

    def Get_Tax3NameFont(self):
        return classicInterfaceWrap.Get_Tax3NameFont(self.context)

    def Set_Tax3NameFont(self, value):
        classicInterfaceWrap.Set_Tax3NameFont(self.context, value)

    def Get_Tax4NameFont(self):
        return classicInterfaceWrap.Get_Tax4NameFont(self.context)

    def Set_Tax4NameFont(self, value):
        classicInterfaceWrap.Set_Tax4NameFont(self.context, value)

    def Get_Tax1TurnOverFont(self):
        return classicInterfaceWrap.Get_Tax1TurnOverFont(self.context)

    def Set_Tax1TurnOverFont(self, value):
        classicInterfaceWrap.Set_Tax1TurnOverFont(self.context, value)

    def Get_Tax2TurnOverFont(self):
        return classicInterfaceWrap.Get_Tax2TurnOverFont(self.context)

    def Set_Tax2TurnOverFont(self, value):
        classicInterfaceWrap.Set_Tax2TurnOverFont(self.context, value)

    def Get_Tax3TurnOverFont(self):
        return classicInterfaceWrap.Get_Tax3TurnOverFont(self.context)

    def Set_Tax3TurnOverFont(self, value):
        classicInterfaceWrap.Set_Tax3TurnOverFont(self.context, value)

    def Get_Tax4TurnOverFont(self):
        return classicInterfaceWrap.Get_Tax4TurnOverFont(self.context)

    def Set_Tax4TurnOverFont(self, value):
        classicInterfaceWrap.Set_Tax4TurnOverFont(self.context, value)

    def Get_Tax1RateFont(self):
        return classicInterfaceWrap.Get_Tax1RateFont(self.context)

    def Set_Tax1RateFont(self, value):
        classicInterfaceWrap.Set_Tax1RateFont(self.context, value)

    def Get_Tax2RateFont(self):
        return classicInterfaceWrap.Get_Tax2RateFont(self.context)

    def Set_Tax2RateFont(self, value):
        classicInterfaceWrap.Set_Tax2RateFont(self.context, value)

    def Get_Tax3RateFont(self):
        return classicInterfaceWrap.Get_Tax3RateFont(self.context)

    def Set_Tax3RateFont(self, value):
        classicInterfaceWrap.Set_Tax3RateFont(self.context, value)

    def Get_Tax4RateFont(self):
        return classicInterfaceWrap.Get_Tax4RateFont(self.context)

    def Set_Tax4RateFont(self, value):
        classicInterfaceWrap.Set_Tax4RateFont(self.context, value)

    def Get_Tax1SumFont(self):
        return classicInterfaceWrap.Get_Tax1SumFont(self.context)

    def Set_Tax1SumFont(self, value):
        classicInterfaceWrap.Set_Tax1SumFont(self.context, value)

    def Get_Tax2SumFont(self):
        return classicInterfaceWrap.Get_Tax2SumFont(self.context)

    def Set_Tax2SumFont(self, value):
        classicInterfaceWrap.Set_Tax2SumFont(self.context, value)

    def Get_Tax3SumFont(self):
        return classicInterfaceWrap.Get_Tax3SumFont(self.context)

    def Set_Tax3SumFont(self, value):
        classicInterfaceWrap.Set_Tax3SumFont(self.context, value)

    def Get_Tax4SumFont(self):
        return classicInterfaceWrap.Get_Tax4SumFont(self.context)

    def Set_Tax4SumFont(self, value):
        classicInterfaceWrap.Set_Tax4SumFont(self.context, value)

    def Get_SubTotalFont(self):
        return classicInterfaceWrap.Get_SubTotalFont(self.context)

    def Set_SubTotalFont(self, value):
        classicInterfaceWrap.Set_SubTotalFont(self.context, value)

    def Get_SubTotalSumFont(self):
        return classicInterfaceWrap.Get_SubTotalSumFont(self.context)

    def Set_SubTotalSumFont(self, value):
        classicInterfaceWrap.Set_SubTotalSumFont(self.context, value)

    def Get_DiscountOnCheckFont(self):
        return classicInterfaceWrap.Get_DiscountOnCheckFont(self.context)

    def Set_DiscountOnCheckFont(self, value):
        classicInterfaceWrap.Set_DiscountOnCheckFont(self.context, value)

    def Get_DiscountOnCheckSumFont(self):
        return classicInterfaceWrap.Get_DiscountOnCheckSumFont(self.context)

    def Set_DiscountOnCheckSumFont(self, value):
        classicInterfaceWrap.Set_DiscountOnCheckSumFont(self.context, value)

    def Get_TotalSymbolNumber(self):
        return classicInterfaceWrap.Get_TotalSymbolNumber(self.context)

    def Set_TotalSymbolNumber(self, value):
        classicInterfaceWrap.Set_TotalSymbolNumber(self.context, value)

    def Get_Summ1SymbolNumber(self):
        return classicInterfaceWrap.Get_Summ1SymbolNumber(self.context)

    def Set_Summ1SymbolNumber(self, value):
        classicInterfaceWrap.Set_Summ1SymbolNumber(self.context, value)

    def Get_Summ2SymbolNumber(self):
        return classicInterfaceWrap.Get_Summ2SymbolNumber(self.context)

    def Set_Summ2SymbolNumber(self, value):
        classicInterfaceWrap.Set_Summ2SymbolNumber(self.context, value)

    def Get_Summ3SymbolNumber(self):
        return classicInterfaceWrap.Get_Summ3SymbolNumber(self.context)

    def Set_Summ3SymbolNumber(self, value):
        classicInterfaceWrap.Set_Summ3SymbolNumber(self.context, value)

    def Get_Summ4SymbolNumber(self):
        return classicInterfaceWrap.Get_Summ4SymbolNumber(self.context)

    def Set_Summ4SymbolNumber(self, value):
        classicInterfaceWrap.Set_Summ4SymbolNumber(self.context, value)

    def Get_ChangeSymbolNumber(self):
        return classicInterfaceWrap.Get_ChangeSymbolNumber(self.context)

    def Set_ChangeSymbolNumber(self, value):
        classicInterfaceWrap.Set_ChangeSymbolNumber(self.context, value)

    def Get_Tax1NameSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax1NameSymbolNumber(self.context)

    def Set_Tax1NameSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax1NameSymbolNumber(self.context, value)

    def Get_Tax1TurnOverSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax1TurnOverSymbolNumber(self.context)

    def Set_Tax1TurnOverSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax1TurnOverSymbolNumber(self.context, value)

    def Get_Tax1RateSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax1RateSymbolNumber(self.context)

    def Set_Tax1RateSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax1RateSymbolNumber(self.context, value)

    def Get_Tax1SumSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax1SumSymbolNumber(self.context)

    def Set_Tax1SumSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax1SumSymbolNumber(self.context, value)

    def Get_Tax2NameSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax2NameSymbolNumber(self.context)

    def Set_Tax2NameSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax2NameSymbolNumber(self.context, value)

    def Get_Tax2TurnOverSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax2TurnOverSymbolNumber(self.context)

    def Set_Tax2TurnOverSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax2TurnOverSymbolNumber(self.context, value)

    def Get_Tax2RateSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax2RateSymbolNumber(self.context)

    def Set_Tax2RateSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax2RateSymbolNumber(self.context, value)

    def Get_Tax2SumSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax2SumSymbolNumber(self.context)

    def Set_Tax2SumSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax2SumSymbolNumber(self.context, value)

    def Get_Tax3NameSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax3NameSymbolNumber(self.context)

    def Set_Tax3NameSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax3NameSymbolNumber(self.context, value)

    def Get_Tax3TurnOverSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax3TurnOverSymbolNumber(self.context)

    def Set_Tax3TurnOverSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax3TurnOverSymbolNumber(self.context, value)

    def Get_Tax3RateSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax3RateSymbolNumber(self.context)

    def Set_Tax3RateSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax3RateSymbolNumber(self.context, value)

    def Get_Tax3SumSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax3SumSymbolNumber(self.context)

    def Set_Tax3SumSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax3SumSymbolNumber(self.context, value)

    def Get_Tax4NameSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax4NameSymbolNumber(self.context)

    def Set_Tax4NameSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax4NameSymbolNumber(self.context, value)

    def Get_Tax4TurnOverSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax4TurnOverSymbolNumber(self.context)

    def Set_Tax4TurnOverSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax4TurnOverSymbolNumber(self.context, value)

    def Get_Tax4RateSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax4RateSymbolNumber(self.context)

    def Set_Tax4RateSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax4RateSymbolNumber(self.context, value)

    def Get_Tax4SumSymbolNumber(self):
        return classicInterfaceWrap.Get_Tax4SumSymbolNumber(self.context)

    def Set_Tax4SumSymbolNumber(self, value):
        classicInterfaceWrap.Set_Tax4SumSymbolNumber(self.context, value)

    def Get_SubTotalSymbolNumber(self):
        return classicInterfaceWrap.Get_SubTotalSymbolNumber(self.context)

    def Set_SubTotalSymbolNumber(self, value):
        classicInterfaceWrap.Set_SubTotalSymbolNumber(self.context, value)

    def Get_DiscountOnCheckSymbolNumber(self):
        return classicInterfaceWrap.Get_DiscountOnCheckSymbolNumber(self.context)

    def Set_DiscountOnCheckSymbolNumber(self, value):
        classicInterfaceWrap.Set_DiscountOnCheckSymbolNumber(self.context, value)

    def Get_DiscountOnCheckSumSymbolNumber(self):
        return classicInterfaceWrap.Get_DiscountOnCheckSumSymbolNumber(self.context)

    def Set_DiscountOnCheckSumSymbolNumber(self, value):
        classicInterfaceWrap.Set_DiscountOnCheckSumSymbolNumber(self.context, value)

    def Get_TotalOffset(self):
        return classicInterfaceWrap.Get_TotalOffset(self.context)

    def Set_TotalOffset(self, value):
        classicInterfaceWrap.Set_TotalOffset(self.context, value)

    def Get_Summ1Offset(self):
        return classicInterfaceWrap.Get_Summ1Offset(self.context)

    def Set_Summ1Offset(self, value):
        classicInterfaceWrap.Set_Summ1Offset(self.context, value)

    def Get_TotalSumOffset(self):
        return classicInterfaceWrap.Get_TotalSumOffset(self.context)

    def Set_TotalSumOffset(self, value):
        classicInterfaceWrap.Set_TotalSumOffset(self.context, value)

    def Get_Summ1NameOffset(self):
        return classicInterfaceWrap.Get_Summ1NameOffset(self.context)

    def Set_Summ1NameOffset(self, value):
        classicInterfaceWrap.Set_Summ1NameOffset(self.context, value)

    def Get_Summ2Offset(self):
        return classicInterfaceWrap.Get_Summ2Offset(self.context)

    def Set_Summ2Offset(self, value):
        classicInterfaceWrap.Set_Summ2Offset(self.context, value)

    def Get_Summ2NameOffset(self):
        return classicInterfaceWrap.Get_Summ2NameOffset(self.context)

    def Set_Summ2NameOffset(self, value):
        classicInterfaceWrap.Set_Summ2NameOffset(self.context, value)

    def Get_Summ3Offset(self):
        return classicInterfaceWrap.Get_Summ3Offset(self.context)

    def Set_Summ3Offset(self, value):
        classicInterfaceWrap.Set_Summ3Offset(self.context, value)

    def Get_Summ3NameOffset(self):
        return classicInterfaceWrap.Get_Summ3NameOffset(self.context)

    def Set_Summ3NameOffset(self, value):
        classicInterfaceWrap.Set_Summ3NameOffset(self.context, value)

    def Get_Summ4Offset(self):
        return classicInterfaceWrap.Get_Summ4Offset(self.context)

    def Set_Summ4Offset(self, value):
        classicInterfaceWrap.Set_Summ4Offset(self.context, value)

    def Get_Summ4NameOffset(self):
        return classicInterfaceWrap.Get_Summ4NameOffset(self.context)

    def Set_Summ4NameOffset(self, value):
        classicInterfaceWrap.Set_Summ4NameOffset(self.context, value)

    def Get_ChangeOffset(self):
        return classicInterfaceWrap.Get_ChangeOffset(self.context)

    def Set_ChangeOffset(self, value):
        classicInterfaceWrap.Set_ChangeOffset(self.context, value)

    def Get_ChangeSumOffset(self):
        return classicInterfaceWrap.Get_ChangeSumOffset(self.context)

    def Set_ChangeSumOffset(self, value):
        classicInterfaceWrap.Set_ChangeSumOffset(self.context, value)

    def Get_Tax1NameOffset(self):
        return classicInterfaceWrap.Get_Tax1NameOffset(self.context)

    def Set_Tax1NameOffset(self, value):
        classicInterfaceWrap.Set_Tax1NameOffset(self.context, value)

    def Get_Tax1TurnOverOffset(self):
        return classicInterfaceWrap.Get_Tax1TurnOverOffset(self.context)

    def Set_Tax1TurnOverOffset(self, value):
        classicInterfaceWrap.Set_Tax1TurnOverOffset(self.context, value)

    def Get_Tax1RateOffset(self):
        return classicInterfaceWrap.Get_Tax1RateOffset(self.context)

    def Set_Tax1RateOffset(self, value):
        classicInterfaceWrap.Set_Tax1RateOffset(self.context, value)

    def Get_Tax1SumOffset(self):
        return classicInterfaceWrap.Get_Tax1SumOffset(self.context)

    def Set_Tax1SumOffset(self, value):
        classicInterfaceWrap.Set_Tax1SumOffset(self.context, value)

    def Get_Tax2NameOffset(self):
        return classicInterfaceWrap.Get_Tax2NameOffset(self.context)

    def Set_Tax2NameOffset(self, value):
        classicInterfaceWrap.Set_Tax2NameOffset(self.context, value)

    def Get_Tax2TurnOverOffset(self):
        return classicInterfaceWrap.Get_Tax2TurnOverOffset(self.context)

    def Set_Tax2TurnOverOffset(self, value):
        classicInterfaceWrap.Set_Tax2TurnOverOffset(self.context, value)

    def Get_Tax2RateOffset(self):
        return classicInterfaceWrap.Get_Tax2RateOffset(self.context)

    def Set_Tax2RateOffset(self, value):
        classicInterfaceWrap.Set_Tax2RateOffset(self.context, value)

    def Get_Tax2SumOffset(self):
        return classicInterfaceWrap.Get_Tax2SumOffset(self.context)

    def Set_Tax2SumOffset(self, value):
        classicInterfaceWrap.Set_Tax2SumOffset(self.context, value)

    def Get_Tax3NameOffset(self):
        return classicInterfaceWrap.Get_Tax3NameOffset(self.context)

    def Set_Tax3NameOffset(self, value):
        classicInterfaceWrap.Set_Tax3NameOffset(self.context, value)

    def Get_Tax3TurnOverOffset(self):
        return classicInterfaceWrap.Get_Tax3TurnOverOffset(self.context)

    def Set_Tax3TurnOverOffset(self, value):
        classicInterfaceWrap.Set_Tax3TurnOverOffset(self.context, value)

    def Get_Tax3RateOffset(self):
        return classicInterfaceWrap.Get_Tax3RateOffset(self.context)

    def Set_Tax3RateOffset(self, value):
        classicInterfaceWrap.Set_Tax3RateOffset(self.context, value)

    def Get_Tax3SumOffset(self):
        return classicInterfaceWrap.Get_Tax3SumOffset(self.context)

    def Set_Tax3SumOffset(self, value):
        classicInterfaceWrap.Set_Tax3SumOffset(self.context, value)

    def Get_Tax4NameOffset(self):
        return classicInterfaceWrap.Get_Tax4NameOffset(self.context)

    def Set_Tax4NameOffset(self, value):
        classicInterfaceWrap.Set_Tax4NameOffset(self.context, value)

    def Get_Tax4TurnOverOffset(self):
        return classicInterfaceWrap.Get_Tax4TurnOverOffset(self.context)

    def Set_Tax4TurnOverOffset(self, value):
        classicInterfaceWrap.Set_Tax4TurnOverOffset(self.context, value)

    def Get_Tax4RateOffset(self):
        return classicInterfaceWrap.Get_Tax4RateOffset(self.context)

    def Set_Tax4RateOffset(self, value):
        classicInterfaceWrap.Set_Tax4RateOffset(self.context, value)

    def Get_Tax4SumOffset(self):
        return classicInterfaceWrap.Get_Tax4SumOffset(self.context)

    def Set_Tax4SumOffset(self, value):
        classicInterfaceWrap.Set_Tax4SumOffset(self.context, value)

    def Get_SubTotalOffset(self):
        return classicInterfaceWrap.Get_SubTotalOffset(self.context)

    def Set_SubTotalOffset(self, value):
        classicInterfaceWrap.Set_SubTotalOffset(self.context, value)

    def Get_SubTotalSumOffset(self):
        return classicInterfaceWrap.Get_SubTotalSumOffset(self.context)

    def Set_SubTotalSumOffset(self, value):
        classicInterfaceWrap.Set_SubTotalSumOffset(self.context, value)

    def Get_SlipDocumentWidth(self):
        return classicInterfaceWrap.Get_SlipDocumentWidth(self.context)

    def Set_SlipDocumentWidth(self, value):
        classicInterfaceWrap.Set_SlipDocumentWidth(self.context, value)

    def Get_SlipDocumentLength(self):
        return classicInterfaceWrap.Get_SlipDocumentLength(self.context)

    def Set_SlipDocumentLength(self, value):
        classicInterfaceWrap.Set_SlipDocumentLength(self.context, value)

    def Get_PrintingAlignment(self):
        return classicInterfaceWrap.Get_PrintingAlignment(self.context)

    def Set_PrintingAlignment(self, value):
        classicInterfaceWrap.Set_PrintingAlignment(self.context, value)

    def Get_SlipStringIntervals(self):
        resultLen = classicInterfaceWrap.Get_SlipStringIntervals(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_SlipStringIntervals(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_SlipStringIntervals(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_SlipStringIntervals(self.context, valueBuff, len(valueBuff))

    def Get_SlipEqualStringIntervals(self):
        return classicInterfaceWrap.Get_SlipEqualStringIntervals(self.context)

    def Set_SlipEqualStringIntervals(self, value):
        classicInterfaceWrap.Set_SlipEqualStringIntervals(self.context, value)

    def Get_KPKFont(self):
        return classicInterfaceWrap.Get_KPKFont(self.context)

    def Set_KPKFont(self, value):
        classicInterfaceWrap.Set_KPKFont(self.context, value)

    def Get_DiscountOnCheckOffset(self):
        return classicInterfaceWrap.Get_DiscountOnCheckOffset(self.context)

    def Set_DiscountOnCheckOffset(self, value):
        classicInterfaceWrap.Set_DiscountOnCheckOffset(self.context, value)

    def Get_DiscountOnCheckSumOffset(self):
        return classicInterfaceWrap.Get_DiscountOnCheckSumOffset(self.context)

    def Set_DiscountOnCheckSumOffset(self, value):
        classicInterfaceWrap.Set_DiscountOnCheckSumOffset(self.context, value)

    def WideLoadLineData(self):
        return classicInterfaceWrap.WideLoadLineData(self.context)

    def PrintTaxReport(self): # Напечатать отчет по налогам
        return classicInterfaceWrap.PrintTaxReport(self.context)

    def Get_FileVersionMS(self):
        return classicInterfaceWrap.Get_FileVersionMS(self.context)

    def Get_FileVersionLS(self):
        return classicInterfaceWrap.Get_FileVersionLS(self.context)

    def GetLongSerialNumberAndLongRNM(self):
        return classicInterfaceWrap.GetLongSerialNumberAndLongRNM(self.context)

    def SetLongSerialNumber(self):
        return classicInterfaceWrap.SetLongSerialNumber(self.context)

    def FiscalizationWithLongRNM(self):
        return classicInterfaceWrap.FiscalizationWithLongRNM(self.context)

    def Connect2(self):
        return classicInterfaceWrap.Connect2(self.context)

    def GetECRPrinterStatus(self):
        return classicInterfaceWrap.GetECRPrinterStatus(self.context)

    def Get_PrinterStatus(self):
        return classicInterfaceWrap.Get_PrinterStatus(self.context)

    def Get_ServerVersion(self):
        resultLen = classicInterfaceWrap.Get_ServerVersion(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ServerVersion(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_LDComputerName(self):
        resultLen = classicInterfaceWrap.Get_LDComputerName(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_LDComputerName(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_LDComputerName(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_LDComputerName(self.context, valueBuff, len(valueBuff))

    def Get_LDTimeout(self):
        return classicInterfaceWrap.Get_LDTimeout(self.context)

    def Set_LDTimeout(self, value):
        classicInterfaceWrap.Set_LDTimeout(self.context, value)

    def ServerConnect(self):
        return classicInterfaceWrap.ServerConnect(self.context)

    def ServerDisconnect(self):
        return classicInterfaceWrap.ServerDisconnect(self.context)

    def Get_ServerConnected(self):
        return classicInterfaceWrap.Get_ServerConnected(self.context)

    def LockPort(self):
        return classicInterfaceWrap.LockPort(self.context)

    def UnlockPort(self):
        return classicInterfaceWrap.UnlockPort(self.context)

    def Get_PortLocked(self):
        return classicInterfaceWrap.Get_PortLocked(self.context)

    def AdminUnlockPort(self):
        return classicInterfaceWrap.AdminUnlockPort(self.context)

    def AdminUnlockPorts(self):
        return classicInterfaceWrap.AdminUnlockPorts(self.context)

    def ServerCheckKey(self):
        return classicInterfaceWrap.ServerCheckKey(self.context)

    def GetFontMetrics(self): # Получить параметры шрифта
        return classicInterfaceWrap.GetFontMetrics(self.context)

    def GetFreeLDNumber(self):
        return classicInterfaceWrap.GetFreeLDNumber(self.context)

    def Get_LogOn(self):
        return classicInterfaceWrap.Get_LogOn(self.context)

    def Set_LogOn(self, value): # Логгирование в драйвере глобальное и включено всегда
        classicInterfaceWrap.Set_LogOn(self.context, value)

    def ReadTable2(self):
        return classicInterfaceWrap.ReadTable2(self.context)

    def WriteTable2(self):
        return classicInterfaceWrap.WriteTable2(self.context)

    def SetFieldMinValue(self, value):
        classicInterfaceWrap.SetFieldMinValue(self.context, value)

    def SetFieldMaxValue(self, value):
        classicInterfaceWrap.SetFieldMaxValue(self.context, value)

    def Get_CPLog(self):
        return classicInterfaceWrap.Get_CPLog(self.context)

    def Set_CPLog(self, value):
        classicInterfaceWrap.Set_CPLog(self.context, value)

    def Get_CashControlHost(self):
        resultLen = classicInterfaceWrap.Get_CashControlHost(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_CashControlHost(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_CashControlHost(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_CashControlHost(self.context, valueBuff, len(valueBuff))

    def Get_CashControlPort(self):
        resultLen = classicInterfaceWrap.Get_CashControlPort(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_CashControlPort(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_CashControlPort(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_CashControlPort(self.context, valueBuff, len(valueBuff))

    def Get_CashControlEnabled(self):
        return classicInterfaceWrap.Get_CashControlEnabled(self.context)

    def Set_CashControlEnabled(self, value):
        classicInterfaceWrap.Set_CashControlEnabled(self.context, value)

    def Get_CashControlUseTCP(self):
        return classicInterfaceWrap.Get_CashControlUseTCP(self.context)

    def Set_CashControlUseTCP(self, value):
        classicInterfaceWrap.Set_CashControlUseTCP(self.context, value)

    def Get_CashControlPassword(self):
        return classicInterfaceWrap.Get_CashControlPassword(self.context)

    def Set_CashControlPassword(self, value):
        classicInterfaceWrap.Set_CashControlPassword(self.context, value)

    def CashControlOpen(self):
        return classicInterfaceWrap.CashControlOpen(self.context)

    def CashControlClose(self):
        return classicInterfaceWrap.CashControlClose(self.context)

    def Get_LDConnectionType(self):
        return classicInterfaceWrap.Get_LDConnectionType(self.context)

    def Set_LDConnectionType(self, value):
        classicInterfaceWrap.Set_LDConnectionType(self.context, value)

    def Get_LDTCPPort(self):
        return classicInterfaceWrap.Get_LDTCPPort(self.context)

    def Set_LDTCPPort(self, value):
        classicInterfaceWrap.Set_LDTCPPort(self.context, value)

    def Get_LDIPAddress(self):
        resultLen = classicInterfaceWrap.Get_LDIPAddress(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_LDIPAddress(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_LDIPAddress(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_LDIPAddress(self.context, valueBuff, len(valueBuff))

    def Get_LDUseIPAddress(self):
        return classicInterfaceWrap.Get_LDUseIPAddress(self.context)

    def Set_LDUseIPAddress(self, value):
        classicInterfaceWrap.Set_LDUseIPAddress(self.context, value)

    def SaveParams(self):
        return classicInterfaceWrap.SaveParams(self.context)

    def Get_CPLogFile(self):
        resultLen = classicInterfaceWrap.Get_CPLogFile(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_CPLogFile(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_CPLogFile(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_CPLogFile(self.context, valueBuff, len(valueBuff))

    def Get_ComLogFile(self):
        resultLen = classicInterfaceWrap.Get_ComLogFile(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ComLogFile(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_ComLogFile(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_ComLogFile(self.context, valueBuff, len(valueBuff))

    def Get_LineData2(self):
        resultLen = classicInterfaceWrap.Get_LineData2(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_LineData2(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_LineData2(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_LineData2(self.context, valueBuff, len(valueBuff))

    def Get_RecoverError165(self):
        return classicInterfaceWrap.Get_RecoverError165(self.context)

    def Set_RecoverError165(self, value):
        classicInterfaceWrap.Set_RecoverError165(self.context, value)

    def Get_MaxRecoverCount(self):
        return classicInterfaceWrap.Get_MaxRecoverCount(self.context)

    def Set_MaxRecoverCount(self, value):
        classicInterfaceWrap.Set_MaxRecoverCount(self.context, value)

    def GetEKLZCode1Status(self):
        return classicInterfaceWrap.GetEKLZCode1Status(self.context)

    def GetEKLZCode2Status(self):
        return classicInterfaceWrap.GetEKLZCode2Status(self.context)

    def ReadWriteFM(self):
        return classicInterfaceWrap.ReadWriteFM(self.context)

    def PrintHeader(self):
        return classicInterfaceWrap.PrintHeader(self.context)

    def CloseCheckWithResult(self):
        return classicInterfaceWrap.CloseCheckWithResult(self.context)

    def Get_OperationCode(self):
        return classicInterfaceWrap.Get_OperationCode(self.context)

    def Get_AccType(self):
        return classicInterfaceWrap.Get_AccType(self.context)

    def Set_AccType(self, value):
        classicInterfaceWrap.Set_AccType(self.context, value)

    def Get_Address(self):
        return classicInterfaceWrap.Get_Address(self.context)

    def Set_Address(self, value):
        classicInterfaceWrap.Set_Address(self.context, value)

    def Get_WrittenByte(self):
        return classicInterfaceWrap.Get_WrittenByte(self.context)

    def Set_WrittenByte(self, value):
        classicInterfaceWrap.Set_WrittenByte(self.context, value)

    def Get_ReadByte(self):
        return classicInterfaceWrap.Get_ReadByte(self.context)

    def Get_TransferByte(self):
        resultLen = classicInterfaceWrap.Get_TransferByte(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_TransferByte(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_TransferByte(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_TransferByte(self.context, valueBuff, len(valueBuff))

    def AboutBox(self):
        return classicInterfaceWrap.AboutBox(self.context)

    def PresenterKeep(self):
        return classicInterfaceWrap.PresenterKeep(self.context)

    def PresenterPush(self):
        return classicInterfaceWrap.PresenterPush(self.context)

    def OpenScreen(self):
        return classicInterfaceWrap.OpenScreen(self.context)

    def CloseScreen(self):
        return classicInterfaceWrap.CloseScreen(self.context)

    def Get_ComLogOnlyErrors(self):
        return classicInterfaceWrap.Get_ComLogOnlyErrors(self.context)

    def Set_ComLogOnlyErrors(self, value):
        classicInterfaceWrap.Set_ComLogOnlyErrors(self.context, value)

    def SetSCPassword(self): # Установить пароль ЦТО
        return classicInterfaceWrap.SetSCPassword(self.context)

    def Get_LastKPKDateStr(self):
        resultLen = classicInterfaceWrap.Get_LastKPKDateStr(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_LastKPKDateStr(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_LastKPKTimeStr(self):
        resultLen = classicInterfaceWrap.Get_LastKPKTimeStr(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_LastKPKTimeStr(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def MethodSupported(self):
        return classicInterfaceWrap.MethodSupported(self.context)

    def Get_MethodName(self):
        resultLen = classicInterfaceWrap.Get_MethodName(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_MethodName(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_MethodName(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_MethodName(self.context, valueBuff, len(valueBuff))

    def Get_PropertyName(self):
        resultLen = classicInterfaceWrap.Get_PropertyName(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_PropertyName(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_PropertyName(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_PropertyName(self.context, valueBuff, len(valueBuff))

    def PropertySupported(self):
        return classicInterfaceWrap.PropertySupported(self.context)

    def Get_LockTimeout(self):
        return classicInterfaceWrap.Get_LockTimeout(self.context)

    def Set_LockTimeout(self, value):
        classicInterfaceWrap.Set_LockTimeout(self.context, value)

    def LockPortTimeout(self):
        return classicInterfaceWrap.LockPortTimeout(self.context)

    def Get_SlipStringInterval(self):
        return classicInterfaceWrap.Get_SlipStringInterval(self.context)

    def Set_SlipStringInterval(self, value):
        classicInterfaceWrap.Set_SlipStringInterval(self.context, value)

    def GetIBMStatus(self):
        return classicInterfaceWrap.GetIBMStatus(self.context)

    def GetShortIBMStatus(self):
        return classicInterfaceWrap.GetShortIBMStatus(self.context)

    def Get_IBMStatusByte1(self):
        return classicInterfaceWrap.Get_IBMStatusByte1(self.context)

    def Get_IBMStatusByte2(self):
        return classicInterfaceWrap.Get_IBMStatusByte2(self.context)

    def Get_IBMStatusByte3(self):
        return classicInterfaceWrap.Get_IBMStatusByte3(self.context)

    def Get_IBMStatusByte4(self):
        return classicInterfaceWrap.Get_IBMStatusByte4(self.context)

    def Get_IBMStatusByte5(self):
        return classicInterfaceWrap.Get_IBMStatusByte5(self.context)

    def Get_IBMStatusByte6(self):
        return classicInterfaceWrap.Get_IBMStatusByte6(self.context)

    def Get_IBMStatusByte7(self):
        return classicInterfaceWrap.Get_IBMStatusByte7(self.context)

    def Get_IBMStatusByte8(self):
        return classicInterfaceWrap.Get_IBMStatusByte8(self.context)

    def Get_IBMFlags(self):
        return classicInterfaceWrap.Get_IBMFlags(self.context)

    def Get_IBMDocumentNumber(self):
        return classicInterfaceWrap.Get_IBMDocumentNumber(self.context)

    def Get_IBMLastSaleReceiptNumber(self):
        return classicInterfaceWrap.Get_IBMLastSaleReceiptNumber(self.context)

    def Get_IBMLastBuyReceiptNumber(self):
        return classicInterfaceWrap.Get_IBMLastBuyReceiptNumber(self.context)

    def Get_IBMLastReturnSaleReceiptNumber(self):
        return classicInterfaceWrap.Get_IBMLastReturnSaleReceiptNumber(self.context)

    def Get_IBMLastReturnBuyReceiptNumber(self):
        return classicInterfaceWrap.Get_IBMLastReturnBuyReceiptNumber(self.context)

    def Get_IBMSessionDay(self):
        return classicInterfaceWrap.Get_IBMSessionDay(self.context)

    def Get_IBMSessionMonth(self):
        return classicInterfaceWrap.Get_IBMSessionMonth(self.context)

    def Get_IBMSessionYear(self):
        return classicInterfaceWrap.Get_IBMSessionYear(self.context)

    def Get_IBMSessionHour(self):
        return classicInterfaceWrap.Get_IBMSessionHour(self.context)

    def Get_IBMSessionMin(self):
        return classicInterfaceWrap.Get_IBMSessionMin(self.context)

    def Get_IBMSessionSec(self):
        return classicInterfaceWrap.Get_IBMSessionSec(self.context)

    def Get_IBMSessionDateTime(self):
        return unwrapDateTime(classicInterfaceWrap.Get_IBMSessionDateTime(self.context))

    def Get_EscapeIP(self):
        resultLen = classicInterfaceWrap.Get_EscapeIP(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_EscapeIP(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_EscapeIP(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_EscapeIP(self.context, valueBuff, len(valueBuff))

    def Get_EscapePort(self):
        return classicInterfaceWrap.Get_EscapePort(self.context)

    def Set_EscapePort(self, value):
        classicInterfaceWrap.Set_EscapePort(self.context, value)

    def Get_LDEscapeIP(self):
        resultLen = classicInterfaceWrap.Get_LDEscapeIP(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_LDEscapeIP(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_LDEscapeIP(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_LDEscapeIP(self.context, valueBuff, len(valueBuff))

    def Get_LDEscapePort(self):
        return classicInterfaceWrap.Get_LDEscapePort(self.context)

    def Set_LDEscapePort(self, value):
        classicInterfaceWrap.Set_LDEscapePort(self.context, value)

    def Get_EscapeTimeout(self):
        return classicInterfaceWrap.Get_EscapeTimeout(self.context)

    def Set_EscapeTimeout(self, value):
        classicInterfaceWrap.Set_EscapeTimeout(self.context, value)

    def Get_LDEscapeTimeout(self):
        return classicInterfaceWrap.Get_LDEscapeTimeout(self.context)

    def Set_LDEscapeTimeout(self, value):
        classicInterfaceWrap.Set_LDEscapeTimeout(self.context, value)

    def Get_CommandTimeout(self):
        return classicInterfaceWrap.Get_CommandTimeout(self.context)

    def Set_CommandTimeout(self, value):
        classicInterfaceWrap.Set_CommandTimeout(self.context, value)

    def Get_UseCommandTimeout(self):
        return classicInterfaceWrap.Get_UseCommandTimeout(self.context)

    def Set_UseCommandTimeout(self, value):
        classicInterfaceWrap.Set_UseCommandTimeout(self.context, value)

    def Get_CommandCount(self):
        return classicInterfaceWrap.Get_CommandCount(self.context)

    def Get_CommandIndex(self):
        return classicInterfaceWrap.Get_CommandIndex(self.context)

    def Set_CommandIndex(self, value):
        classicInterfaceWrap.Set_CommandIndex(self.context, value)

    def GetCommandParams(self):
        return classicInterfaceWrap.GetCommandParams(self.context)

    def SetCommandParams(self):
        return classicInterfaceWrap.SetCommandParams(self.context)

    def SaveCommandParams(self):
        return classicInterfaceWrap.SaveCommandParams(self.context)

    def Get_CommandName(self):
        resultLen = classicInterfaceWrap.Get_CommandName(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_CommandName(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_CommandDefTimeout(self):
        return classicInterfaceWrap.Get_CommandDefTimeout(self.context)

    def Get_CommandCode(self):
        return classicInterfaceWrap.Get_CommandCode(self.context)

    def SetAllCommandsParams(self):
        return classicInterfaceWrap.SetAllCommandsParams(self.context)

    def Get_TimeoutsUsing(self):
        return classicInterfaceWrap.Get_TimeoutsUsing(self.context)

    def Set_TimeoutsUsing(self, value):
        classicInterfaceWrap.Set_TimeoutsUsing(self.context, value)

    def SetDefCommandsParams(self):
        return classicInterfaceWrap.SetDefCommandsParams(self.context)

    def OpenSession(self): # Открыть смену
        return classicInterfaceWrap.OpenSession(self.context)

    def WaitForPrinting(self): # Ожидать завершения печати
        return classicInterfaceWrap.WaitForPrinting(self.context)

    def Get_IntervalNumber(self):
        return classicInterfaceWrap.Get_IntervalNumber(self.context)

    def Set_IntervalNumber(self, value):
        classicInterfaceWrap.Set_IntervalNumber(self.context, value)

    def Get_IntervalValue(self):
        return classicInterfaceWrap.Get_IntervalValue(self.context)

    def Set_IntervalValue(self, value):
        classicInterfaceWrap.Set_IntervalValue(self.context, value)

    def GetInterval(self):
        return classicInterfaceWrap.GetInterval(self.context)

    def SetInterval(self):
        return classicInterfaceWrap.SetInterval(self.context)

    def Get_ParentWnd(self):
        return classicInterfaceWrap.Get_ParentWnd(self.context)

    def Set_ParentWnd(self, value):
        classicInterfaceWrap.Set_ParentWnd(self.context, value)

    def ShowTablesDlg(self):
        return classicInterfaceWrap.ShowTablesDlg(self.context)

    def Get_MobilePayEnabled(self):
        return classicInterfaceWrap.Get_MobilePayEnabled(self.context)

    def Set_MobilePayEnabled(self, value):
        classicInterfaceWrap.Set_MobilePayEnabled(self.context, value)

    def Get_PayDepartment(self):
        return classicInterfaceWrap.Get_PayDepartment(self.context)

    def Set_PayDepartment(self, value):
        classicInterfaceWrap.Set_PayDepartment(self.context, value)

    def Get_ParamsPageIndex(self):
        return classicInterfaceWrap.Get_ParamsPageIndex(self.context)

    def Set_ParamsPageIndex(self, value):
        classicInterfaceWrap.Set_ParamsPageIndex(self.context, value)

    def ShowPayParams(self):
        return classicInterfaceWrap.ShowPayParams(self.context)

    def Get_SaleError(self):
        return classicInterfaceWrap.Get_SaleError(self.context)

    def Set_SaleError(self, value):
        classicInterfaceWrap.Set_SaleError(self.context, value)

    def ReprintSlipDocument(self):
        return classicInterfaceWrap.ReprintSlipDocument(self.context)

    def Get_RealPayDepartment(self):
        return classicInterfaceWrap.Get_RealPayDepartment(self.context)

    def Set_RealPayDepartment(self, value):
        classicInterfaceWrap.Set_RealPayDepartment(self.context, value)

    def CardPayProperties(self):
        return classicInterfaceWrap.CardPayProperties(self.context)

    def Get_CardPayEnabled(self):
        return classicInterfaceWrap.Get_CardPayEnabled(self.context)

    def Set_CardPayEnabled(self, value):
        classicInterfaceWrap.Set_CardPayEnabled(self.context, value)

    def Get_CardPayType(self):
        return classicInterfaceWrap.Get_CardPayType(self.context)

    def Set_CardPayType(self, value):
        classicInterfaceWrap.Set_CardPayType(self.context, value)

    def Get_ccUseTextAsWareName(self):
        return classicInterfaceWrap.Get_ccUseTextAsWareName(self.context)

    def Get_ccWareNameLineNumber(self):
        return classicInterfaceWrap.Get_ccWareNameLineNumber(self.context)

    def Set_ccUseTextAsWareName(self, value):
        classicInterfaceWrap.Set_ccUseTextAsWareName(self.context, value)

    def Set_ccWareNameLineNumber(self, value):
        classicInterfaceWrap.Set_ccWareNameLineNumber(self.context, value)

    def Get_ccHeaderLineCount(self):
        return classicInterfaceWrap.Get_ccHeaderLineCount(self.context)

    def Set_ccHeaderLineCount(self, value):
        classicInterfaceWrap.Set_ccHeaderLineCount(self.context, value)

    def Get_LogCommands(self):
        return classicInterfaceWrap.Get_LogCommands(self.context)

    def Set_LogCommands(self, value):
        classicInterfaceWrap.Set_LogCommands(self.context, value)

    def Get_LogMethods(self):
        return classicInterfaceWrap.Get_LogMethods(self.context)

    def Set_LogMethods(self, value):
        classicInterfaceWrap.Set_LogMethods(self.context, value)

    def PrintLine(self): # Печать линии методом печати графической линии
        return classicInterfaceWrap.PrintLine(self.context)

    def JournalClear(self):
        return classicInterfaceWrap.JournalClear(self.context)

    def JournalGetRow(self):
        return classicInterfaceWrap.JournalGetRow(self.context)

    def Get_JournalEnabled(self):
        return classicInterfaceWrap.Get_JournalEnabled(self.context)

    def Set_JournalEnabled(self, value):
        classicInterfaceWrap.Set_JournalEnabled(self.context, value)

    def Get_JournalRow(self):
        resultLen = classicInterfaceWrap.Get_JournalRow(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_JournalRow(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_JournalRowCount(self):
        return classicInterfaceWrap.Get_JournalRowCount(self.context)

    def Get_JournalRowNumber(self):
        return classicInterfaceWrap.Get_JournalRowNumber(self.context)

    def Set_JournalRowNumber(self, value):
        classicInterfaceWrap.Set_JournalRowNumber(self.context, value)

    def Get_JournalText(self):
        resultLen = classicInterfaceWrap.Get_JournalText(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_JournalText(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def JournalInit(self):
        return classicInterfaceWrap.JournalInit(self.context)

    def FindDevice(self): # Поиск устройства
        return classicInterfaceWrap.FindDevice(self.context)

    def LoadParams(self):
        return classicInterfaceWrap.LoadParams(self.context)

    def FinishDocument(self): # Конец документа
        return classicInterfaceWrap.FinishDocument(self.context)

    def PrintTrailer(self): # Печать рекламного текста
        return classicInterfaceWrap.PrintTrailer(self.context)

    def Get_SerialNumberAsInteger(self):
        return classicInterfaceWrap.Get_SerialNumberAsInteger(self.context)

    def Get_INNAsInteger(self):
        return classicInterfaceWrap.Get_INNAsInteger(self.context)

    def Get_ECRDate(self):
        return unwrapDateTime(classicInterfaceWrap.Get_ECRDate(self.context))

    def Set_ECRDate(self, value):
        classicInterfaceWrap.Set_ECRDate(self.context, wrapDateTime(value))

    def Get_ECRTime(self):
        return unwrapDateTime(classicInterfaceWrap.Get_ECRTime(self.context))

    def Set_ECRTime(self, value):
        classicInterfaceWrap.Set_ECRTime(self.context, wrapDateTime(value))

    def WaitForCheckClose(self):
        return classicInterfaceWrap.WaitForCheckClose(self.context)

    def GetSummFactor(self):
        return classicInterfaceWrap.GetSummFactor(self.context)

    def GetQuantityFactor(self):
        return classicInterfaceWrap.GetQuantityFactor(self.context)

    def ReadDeviceMetrics(self):
        return classicInterfaceWrap.ReadDeviceMetrics(self.context)

    def ReadEcrStatus(self):
        return classicInterfaceWrap.ReadEcrStatus(self.context)

    def SaveState(self):
        return classicInterfaceWrap.SaveState(self.context)

    def RestoreState(self):
        return classicInterfaceWrap.RestoreState(self.context)

    def Get_HasCashControlLicense(self):
        return classicInterfaceWrap.Get_HasCashControlLicense(self.context)

    def Get_BufferingType(self):
        return classicInterfaceWrap.Get_BufferingType(self.context)

    def Set_BufferingType(self, value):
        classicInterfaceWrap.Set_BufferingType(self.context, value)

    def LoadImage(self): # Загрузить картинку
        return classicInterfaceWrap.LoadImage(self.context)

    def GetCashAcceptorStatus(self):
        return classicInterfaceWrap.GetCashAcceptorStatus(self.context)

    def GetCashAcceptorRegisters(self):
        return classicInterfaceWrap.GetCashAcceptorRegisters(self.context)

    def CashAcceptorReport(self):
        return classicInterfaceWrap.CashAcceptorReport(self.context)

    def Get_FeedAfterCut(self):
        return classicInterfaceWrap.Get_FeedAfterCut(self.context)

    def Set_FeedAfterCut(self, value):
        classicInterfaceWrap.Set_FeedAfterCut(self.context, value)

    def Get_FeedLineCount(self):
        return classicInterfaceWrap.Get_FeedLineCount(self.context)

    def Set_FeedLineCount(self, value):
        classicInterfaceWrap.Set_FeedLineCount(self.context, value)

    def ClearResult(self): # Очистить код ошибки
        return classicInterfaceWrap.ClearResult(self.context)

    def MasterPayClearBuffer(self):
        return classicInterfaceWrap.MasterPayClearBuffer(self.context)

    def MasterPayAddTextBlock(self):
        return classicInterfaceWrap.MasterPayAddTextBlock(self.context)

    def MasterPayCreateMac(self):
        return classicInterfaceWrap.MasterPayCreateMac(self.context)

    def Get_CashControlProtocols(self):
        resultLen = classicInterfaceWrap.Get_CashControlProtocols(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_CashControlProtocols(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def LoadBlockData(self): # Загрузить блок данных
        return classicInterfaceWrap.LoadBlockData(self.context)

    def Get_LogMaxFileSize(self):
        return classicInterfaceWrap.Get_LogMaxFileSize(self.context)

    def Set_LogMaxFileSize(self, value):
        classicInterfaceWrap.Set_LogMaxFileSize(self.context, value)

    def Get_LogMaxFileCount(self):
        return classicInterfaceWrap.Get_LogMaxFileCount(self.context)

    def Set_LogMaxFileCount(self, value):
        classicInterfaceWrap.Set_LogMaxFileCount(self.context, value)

    def Get_BinaryConversion(self):
        return classicInterfaceWrap.Get_BinaryConversion(self.context)

    def Set_BinaryConversion(self, value):
        classicInterfaceWrap.Set_BinaryConversion(self.context, value)

    def Get_CodePage(self):
        return classicInterfaceWrap.Get_CodePage(self.context)

    def Set_CodePage(self, value):
        classicInterfaceWrap.Set_CodePage(self.context, value)

    def Get_PrintJournalBeforeZReport(self):
        return classicInterfaceWrap.Get_PrintJournalBeforeZReport(self.context)

    def Set_PrintJournalBeforeZReport(self, value):
        classicInterfaceWrap.Set_PrintJournalBeforeZReport(self.context, value)

    def GetEKLZCode3Report(self):
        return classicInterfaceWrap.GetEKLZCode3Report(self.context)

    def Get_TransmitStatus(self):
        return classicInterfaceWrap.Get_TransmitStatus(self.context)

    def Get_TransmitQueueSize(self):
        return classicInterfaceWrap.Get_TransmitQueueSize(self.context)

    def Get_TransmitSessionNumber(self):
        return classicInterfaceWrap.Get_TransmitSessionNumber(self.context)

    def Get_TransmitDocumentNumber(self):
        return classicInterfaceWrap.Get_TransmitDocumentNumber(self.context)

    def ReadModemParameter(self):
        return classicInterfaceWrap.ReadModemParameter(self.context)

    def WriteModemParameter(self):
        return classicInterfaceWrap.WriteModemParameter(self.context)

    def Get_ParameterNumber(self):
        return classicInterfaceWrap.Get_ParameterNumber(self.context)

    def Set_ParameterNumber(self, value):
        classicInterfaceWrap.Set_ParameterNumber(self.context, value)

    def Get_ParameterValue(self):
        resultLen = classicInterfaceWrap.Get_ParameterValue(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ParameterValue(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_ParameterValue(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_ParameterValue(self.context, valueBuff, len(valueBuff))

    def Get_TranslationEnabled(self):
        return classicInterfaceWrap.Get_TranslationEnabled(self.context)

    def Set_TranslationEnabled(self, value):
        classicInterfaceWrap.Set_TranslationEnabled(self.context, value)

    def Get_ModelIndex(self):
        return classicInterfaceWrap.Get_ModelIndex(self.context)

    def Set_ModelIndex(self, value):
        classicInterfaceWrap.Set_ModelIndex(self.context, value)

    def Get_ModelParamIndex(self):
        return classicInterfaceWrap.Get_ModelParamIndex(self.context)

    def Set_ModelParamIndex(self, value):
        classicInterfaceWrap.Set_ModelParamIndex(self.context, value)

    def Get_ModelParamCount(self): # Количество параметров модели
        return classicInterfaceWrap.Get_ModelParamCount(self.context)

    def GetPortNames(self):
        return classicInterfaceWrap.GetPortNames(self.context)

    def Get_ReceiptOutputType(self):
        return classicInterfaceWrap.Get_ReceiptOutputType(self.context)

    def OutputReceipt(self):
        return classicInterfaceWrap.OutputReceipt(self.context)

    def Set_ReceiptOutputType(self, value):
        classicInterfaceWrap.Set_ReceiptOutputType(self.context, value)

    def Sale2(self):
        return classicInterfaceWrap.Sale2(self.context)

    def PrintCliche(self): # Печать клише
        return classicInterfaceWrap.PrintCliche(self.context)

    def PrintBarcodeLine(self): # Печать штрих-кода линией
        return classicInterfaceWrap.PrintBarcodeLine(self.context)

    def PrintBarcodeGraph(self):
        return classicInterfaceWrap.PrintBarcodeGraph(self.context)

    def Get_BarcodeTypes(self):
        resultLen = classicInterfaceWrap.Get_BarcodeTypes(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_BarcodeTypes(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_BarcodeAlignments(self):
        resultLen = classicInterfaceWrap.Get_BarcodeAlignments(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_BarcodeAlignments(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def ResetECR(self): # Сброс ККМ
        return classicInterfaceWrap.ResetECR(self.context)

    def PrintZReportFromBuffer(self): # Распечатать отчёт с гашением из буфера
        return classicInterfaceWrap.PrintZReportFromBuffer(self.context)

    def PrintZReportInBuffer(self): # Снять отчёт с гашением в буфер
        return classicInterfaceWrap.PrintZReportInBuffer(self.context)

    def Get_LogFileMaxSize(self):
        return classicInterfaceWrap.Get_LogFileMaxSize(self.context)

    def Set_LogFileMaxSize(self, value):
        classicInterfaceWrap.Set_LogFileMaxSize(self.context, value)

    def ClearPrintBuffer(self):
        return classicInterfaceWrap.ClearPrintBuffer(self.context)

    def ReadPrintBufferLine(self):
        return classicInterfaceWrap.ReadPrintBufferLine(self.context)

    def ReadPrintBufferLineNumber(self):
        return classicInterfaceWrap.ReadPrintBufferLineNumber(self.context)

    def Get_PrintBufferFormat(self):
        return classicInterfaceWrap.Get_PrintBufferFormat(self.context)

    def Set_PrintBufferFormat(self, value):
        classicInterfaceWrap.Set_PrintBufferFormat(self.context, value)

    def Get_PrintBufferLineNumber(self):
        return classicInterfaceWrap.Get_PrintBufferLineNumber(self.context)

    def Get_NakCount(self):
        return classicInterfaceWrap.Get_NakCount(self.context)

    def Set_NakCount(self, value):
        classicInterfaceWrap.Set_NakCount(self.context, value)

    def Get_MaxAnswerReadCount(self):
        return classicInterfaceWrap.Get_MaxAnswerReadCount(self.context)

    def Get_MaxCommandSendCount(self):
        return classicInterfaceWrap.Get_MaxCommandSendCount(self.context)

    def Get_MaxENQSendCount(self):
        return classicInterfaceWrap.Get_MaxENQSendCount(self.context)

    def Set_MaxAnswerReadCount(self, value):
        classicInterfaceWrap.Set_MaxAnswerReadCount(self.context, value)

    def Set_MaxCommandSendCount(self, value):
        classicInterfaceWrap.Set_MaxCommandSendCount(self.context, value)

    def Set_MaxENQSendCount(self, value):
        classicInterfaceWrap.Set_MaxENQSendCount(self.context, value)

    def Get_CommandRetryCount(self):
        return classicInterfaceWrap.Get_CommandRetryCount(self.context)

    def Set_CommandRetryCount(self, value):
        classicInterfaceWrap.Set_CommandRetryCount(self.context, value)

    def OpenNonfiscalDocument(self):
        return classicInterfaceWrap.OpenNonfiscalDocument(self.context)

    def CloseNonFiscalDocument(self):
        return classicInterfaceWrap.CloseNonFiscalDocument(self.context)

    def Get_AttributeNumber(self):
        return classicInterfaceWrap.Get_AttributeNumber(self.context)

    def Get_AttributeValue(self):
        resultLen = classicInterfaceWrap.Get_AttributeValue(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_AttributeValue(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def PrintAttribute(self):
        return classicInterfaceWrap.PrintAttribute(self.context)

    def Set_AttributeNumber(self, value):
        classicInterfaceWrap.Set_AttributeNumber(self.context, value)

    def Set_AttributeValue(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_AttributeValue(self.context, valueBuff, len(valueBuff))

    def Get_ModelID(self):
        return classicInterfaceWrap.Get_ModelID(self.context)

    def ReadModelParamValue(self): # Прочитать параметр модели
        return classicInterfaceWrap.ReadModelParamValue(self.context)

    def Set_ModelID(self, value):
        classicInterfaceWrap.Set_ModelID(self.context, value)

    def LoadCashControlParams(self):
        return classicInterfaceWrap.LoadCashControlParams(self.context)

    def Set_Connected(self, value): # Устанавливает значение свойства #Connected При установке этого свойства в true Вызывается метод
        classicInterfaceWrap.Set_Connected(self.context, value)

    def Get_EnteredTaxPassword(self):
        return classicInterfaceWrap.Get_EnteredTaxPassword(self.context)

    def Get_BanknoteCount(self):
        return classicInterfaceWrap.Get_BanknoteCount(self.context)

    def Get_BanknoteType(self):
        return classicInterfaceWrap.Get_BanknoteType(self.context)

    def Get_CashAcceptorPollingMode(self):
        return classicInterfaceWrap.Get_CashAcceptorPollingMode(self.context)

    def Get_Poll1(self):
        return classicInterfaceWrap.Get_Poll1(self.context)

    def Get_Poll2(self):
        return classicInterfaceWrap.Get_Poll2(self.context)

    def Set_BanknoteType(self, value):
        classicInterfaceWrap.Set_BanknoteType(self.context, value)

    def ReadBanknoteCount(self):
        return classicInterfaceWrap.ReadBanknoteCount(self.context)

    def Get_LDSysAdminPassword(self):
        return classicInterfaceWrap.Get_LDSysAdminPassword(self.context)

    def Set_LDSysAdminPassword(self, value):
        classicInterfaceWrap.Set_LDSysAdminPassword(self.context, value)

    def PrintOperationalTaxReport(self):
        return classicInterfaceWrap.PrintOperationalTaxReport(self.context)

    def Get_CapOpenCheck(self):
        return classicInterfaceWrap.Get_CapOpenCheck(self.context)

    def Get_PollDescription(self):
        resultLen = classicInterfaceWrap.Get_PollDescription(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_PollDescription(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def WaitConnection(self):
        return classicInterfaceWrap.WaitConnection(self.context)

    def ReadModelParamDescription(self): # Прочитать описание параметра модели
        return classicInterfaceWrap.ReadModelParamDescription(self.context)

    def Get_HRIPosition(self):
        return classicInterfaceWrap.Get_HRIPosition(self.context)

    def PrintBarcodeUsingPrinter(self):
        return classicInterfaceWrap.PrintBarcodeUsingPrinter(self.context)

    def Set_HRIPosition(self, value):
        classicInterfaceWrap.Set_HRIPosition(self.context, value)

    def Get_KPKStr(self):
        resultLen = classicInterfaceWrap.Get_KPKStr(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_KPKStr(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def CloseCheckWithKPK(self):
        return classicInterfaceWrap.CloseCheckWithKPK(self.context)

    def ReadEKLZActivizationParams(self):
        return classicInterfaceWrap.ReadEKLZActivizationParams(self.context)

    def GetShortReportInDatesRange(self):
        return classicInterfaceWrap.GetShortReportInDatesRange(self.context)

    def GetShortReportInSessionRange(self):
        return classicInterfaceWrap.GetShortReportInSessionRange(self.context)

    def ReadLastReceipt(self):
        return classicInterfaceWrap.ReadLastReceipt(self.context)

    def ReadLastReceiptLine(self):
        return classicInterfaceWrap.ReadLastReceiptLine(self.context)

    def ReadLastReceiptMac(self):
        return classicInterfaceWrap.ReadLastReceiptMac(self.context)

    def Get_TextBlock(self):
        resultLen = classicInterfaceWrap.Get_TextBlock(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_TextBlock(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_TextBlockNumber(self):
        return classicInterfaceWrap.Get_TextBlockNumber(self.context)

    def Set_TextBlock(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_TextBlock(self.context, valueBuff, len(valueBuff))

    def Set_TextBlockNumber(self, value):
        classicInterfaceWrap.Set_TextBlockNumber(self.context, value)

    def BeginDocument(self):
        return classicInterfaceWrap.BeginDocument(self.context)

    def EndDocument(self):
        return classicInterfaceWrap.EndDocument(self.context)

    def Get_PosControlReceiptSeparator(self):
        resultLen = classicInterfaceWrap.Get_PosControlReceiptSeparator(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_PosControlReceiptSeparator(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_PosControlReceiptSeparator(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_PosControlReceiptSeparator(self.context, valueBuff, len(valueBuff))

    def Print2DBarcode(self): # Печать двухмерного штрих-кода
        return classicInterfaceWrap.Print2DBarcode(self.context)

    def Set_BarcodeDataLength(self, value):
        classicInterfaceWrap.Set_BarcodeDataLength(self.context, value)

    def LoadAndPrint2DBarcode(self): # Загрузка и печать двухмерного штрих-кода
        return classicInterfaceWrap.LoadAndPrint2DBarcode(self.context)

    def Get_ExciseCode(self):
        return classicInterfaceWrap.Get_ExciseCode(self.context)

    def Set_ExciseCode(self, value):
        classicInterfaceWrap.Set_ExciseCode(self.context, value)

    def ExcisableOperation(self):
        return classicInterfaceWrap.ExcisableOperation(self.context)

    def ReadReportBufferLine(self):
        return classicInterfaceWrap.ReadReportBufferLine(self.context)

    def Get_SaveSettingsType(self):
        return classicInterfaceWrap.Get_SaveSettingsType(self.context)

    def Set_SaveSettingsType(self, value):
        classicInterfaceWrap.Set_SaveSettingsType(self.context, value)

    def ReadParams(self):
        return classicInterfaceWrap.ReadParams(self.context)

    def Get_ModelNames(self):
        resultLen = classicInterfaceWrap.Get_ModelNames(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ModelNames(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_ModelsCount(self):
        return classicInterfaceWrap.Get_ModelsCount(self.context)

    def Get_FMFlagsEx(self):
        return classicInterfaceWrap.Get_FMFlagsEx(self.context)

    def Get_FMMode(self):
        return classicInterfaceWrap.Get_FMMode(self.context)

    def Get_IsASPDMode(self):
        return classicInterfaceWrap.Get_IsASPDMode(self.context)

    def Get_IsCorruptedFiscalizationInfo(self):
        return classicInterfaceWrap.Get_IsCorruptedFiscalizationInfo(self.context)

    def Get_IsCorruptedFMRecords(self):
        return classicInterfaceWrap.Get_IsCorruptedFMRecords(self.context)

    def GetCashRegEx(self): # Получить денежный регистр доп
        return classicInterfaceWrap.GetCashRegEx(self.context)

    def Get_RegBuyRec(self):
        return classicInterfaceWrap.Get_RegBuyRec(self.context)

    def Get_RegBuyReturnRec(self):
        return classicInterfaceWrap.Get_RegBuyReturnRec(self.context)

    def Get_RegBuyReturnSession(self):
        return classicInterfaceWrap.Get_RegBuyReturnSession(self.context)

    def Get_RegBuySession(self):
        return classicInterfaceWrap.Get_RegBuySession(self.context)

    def Get_RegSaleRec(self):
        return classicInterfaceWrap.Get_RegSaleRec(self.context)

    def Get_RegSaleReturnRec(self):
        return classicInterfaceWrap.Get_RegSaleReturnRec(self.context)

    def Get_RegSaleReturnSession(self):
        return classicInterfaceWrap.Get_RegSaleReturnSession(self.context)

    def Get_RegSaleSession(self):
        return classicInterfaceWrap.Get_RegSaleSession(self.context)

    def GetWareBaseCashRegs(self):
        return classicInterfaceWrap.GetWareBaseCashRegs(self.context)

    def Get_WareCode(self):
        return classicInterfaceWrap.Get_WareCode(self.context)

    def Set_WareCode(self, value):
        classicInterfaceWrap.Set_WareCode(self.context, value)

    def PrintCashierReport(self): # Снять отчет по кассирам
        return classicInterfaceWrap.PrintCashierReport(self.context)

    def PrintHourlyReport(self):
        return classicInterfaceWrap.PrintHourlyReport(self.context)

    def PrintWareReport(self):
        return classicInterfaceWrap.PrintWareReport(self.context)

    def UpdateWare(self):
        return classicInterfaceWrap.UpdateWare(self.context)

    def CheckFM(self):
        return classicInterfaceWrap.CheckFM(self.context)

    def RemoveWare(self):
        return classicInterfaceWrap.RemoveWare(self.context)

    def Get_RecordCount(self):
        return classicInterfaceWrap.Get_RecordCount(self.context)

    def Get_CheckingType(self):
        return classicInterfaceWrap.Get_CheckingType(self.context)

    def Set_CheckingType(self, value):
        classicInterfaceWrap.Set_CheckingType(self.context, value)

    def ReadErrorDescription(self): # Получить описание ошибки
        return classicInterfaceWrap.ReadErrorDescription(self.context)

    def ReadLastErrorDescription(self): # Получить описание последней ошибки
        return classicInterfaceWrap.ReadLastErrorDescription(self.context)

    def ReadWare(self):
        return classicInterfaceWrap.ReadWare(self.context)

    def Get_UseWareCode(self):
        return classicInterfaceWrap.Get_UseWareCode(self.context)

    def Set_UseWareCode(self, value):
        classicInterfaceWrap.Set_UseWareCode(self.context, value)

    def Get_RequestErrorDescription(self):
        return classicInterfaceWrap.Get_RequestErrorDescription(self.context)

    def Set_RequestErrorDescription(self, value):
        classicInterfaceWrap.Set_RequestErrorDescription(self.context, value)

    def Get_AdjustRITimeout(self):
        return classicInterfaceWrap.Get_AdjustRITimeout(self.context)

    def Set_AdjustRITimeout(self, value):
        classicInterfaceWrap.Set_AdjustRITimeout(self.context, value)

    def Get_UCodePageText(self):
        resultLen = classicInterfaceWrap.Get_UCodePageText(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_UCodePageText(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_ReconnectPort(self, value): # Устанавливает значение свойства #ReconnectPort
        classicInterfaceWrap.Set_ReconnectPort(self.context, value)

    def Get_DoNotSendENQ(self):
        return classicInterfaceWrap.Get_DoNotSendENQ(self.context)

    def Set_DoNotSendENQ(self, value):
        classicInterfaceWrap.Set_DoNotSendENQ(self.context, value)

    def ReadModelParam(self):
        return classicInterfaceWrap.ReadModelParam(self.context)

    def InitEEPROM(self):
        return classicInterfaceWrap.InitEEPROM(self.context)

    def Get_CheckEJConnection(self):
        return classicInterfaceWrap.Get_CheckEJConnection(self.context)

    def Get_CheckFMConnection(self):
        return classicInterfaceWrap.Get_CheckFMConnection(self.context)

    def Set_CheckEJConnection(self, value):
        classicInterfaceWrap.Set_CheckEJConnection(self.context, value)

    def Set_CheckFMConnection(self, value):
        classicInterfaceWrap.Set_CheckFMConnection(self.context, value)

    def CheckConnection(self):
        return classicInterfaceWrap.CheckConnection(self.context)

    def ChangeProtocol(self):
        return classicInterfaceWrap.ChangeProtocol(self.context)

    def Get_LDProtocolType(self):
        return classicInterfaceWrap.Get_LDProtocolType(self.context)

    def Set_LDProtocolType(self, value):
        classicInterfaceWrap.Set_LDProtocolType(self.context, value)

    def GetECRParams(self):
        return classicInterfaceWrap.GetECRParams(self.context)

    def ShowImportDlg(self):
        return classicInterfaceWrap.ShowImportDlg(self.context)

    def Get_LastPrintResult(self):
        return classicInterfaceWrap.Get_LastPrintResult(self.context)

    def Get_UseSlipCheck(self):
        return classicInterfaceWrap.Get_UseSlipCheck(self.context)

    def Set_UseSlipCheck(self, value):
        classicInterfaceWrap.Set_UseSlipCheck(self.context, value)

    def Get_TypeOfLastEntryFMEx(self):
        return classicInterfaceWrap.Get_TypeOfLastEntryFMEx(self.context)

    def JournalOperation(self):
        return classicInterfaceWrap.JournalOperation(self.context)

    def Get_AutoSensorValues(self):
        return classicInterfaceWrap.Get_AutoSensorValues(self.context)

    def Set_AutoSensorValues(self, value):
        classicInterfaceWrap.Set_AutoSensorValues(self.context, value)

    def Get_AutoStartSearch(self):
        return classicInterfaceWrap.Get_AutoStartSearch(self.context)

    def Get_SearchTimeout(self):
        return classicInterfaceWrap.Get_SearchTimeout(self.context)

    def Set_AutoStartSearch(self, value):
        classicInterfaceWrap.Set_AutoStartSearch(self.context, value)

    def Set_SearchTimeout(self, value):
        classicInterfaceWrap.Set_SearchTimeout(self.context, value)

    def Get_TCPConnectionTimeout(self):
        return classicInterfaceWrap.Get_TCPConnectionTimeout(self.context)

    def Set_TCPConnectionTimeout(self, value):
        classicInterfaceWrap.Set_TCPConnectionTimeout(self.context, value)

    def MFPActivization(self):
        return classicInterfaceWrap.MFPActivization(self.context)

    def MFPCloseArchive(self):
        return classicInterfaceWrap.MFPCloseArchive(self.context)

    def MFPGetPermitActivizationCode(self):
        return classicInterfaceWrap.MFPGetPermitActivizationCode(self.context)

    def MFPGetCustomerCode(self):
        return classicInterfaceWrap.MFPGetCustomerCode(self.context)

    def MFPPrepareActivization(self):
        return classicInterfaceWrap.MFPPrepareActivization(self.context)

    def MFPSetCustomerCode(self):
        return classicInterfaceWrap.MFPSetCustomerCode(self.context)

    def MFPSetPermitActivizationCode(self):
        return classicInterfaceWrap.MFPSetPermitActivizationCode(self.context)

    def MFPGetPrepareActivizationResult(self):
        return classicInterfaceWrap.MFPGetPrepareActivizationResult(self.context)

    def CloseCheckEx(self): # Расширенное закрытие чека
        return classicInterfaceWrap.CloseCheckEx(self.context)

    def Get_CustomerCode(self):
        return classicInterfaceWrap.Get_CustomerCode(self.context)

    def Set_CustomerCode(self, value):
        classicInterfaceWrap.Set_CustomerCode(self.context, value)

    def Get_PermitActivizationCode(self):
        return classicInterfaceWrap.Get_PermitActivizationCode(self.context)

    def Set_PermitActivizationCode(self, value):
        classicInterfaceWrap.Set_PermitActivizationCode(self.context, value)

    def Get_ActivizationStatus(self):
        return classicInterfaceWrap.Get_ActivizationStatus(self.context)

    def Set_ActivizationStatus(self, value):
        classicInterfaceWrap.Set_ActivizationStatus(self.context, value)

    def Get_MFPStatus(self):
        return classicInterfaceWrap.Get_MFPStatus(self.context)

    def Set_MFPStatus(self, value):
        classicInterfaceWrap.Set_MFPStatus(self.context, value)

    def Get_KPKValue(self):
        return classicInterfaceWrap.Get_KPKValue(self.context)

    def Set_KPKValue(self, value):
        classicInterfaceWrap.Set_KPKValue(self.context, value)

    def Get_ActivizationControlByte(self):
        return classicInterfaceWrap.Get_ActivizationControlByte(self.context)

    def Set_ActivizationControlByte(self, value):
        classicInterfaceWrap.Set_ActivizationControlByte(self.context, value)

    def Get_PrepareActivizationRemainCount(self):
        return classicInterfaceWrap.Get_PrepareActivizationRemainCount(self.context)

    def Set_PrepareActivizationRemainCount(self, value):
        classicInterfaceWrap.Set_PrepareActivizationRemainCount(self.context, value)

    def Get_AnswerCode(self):
        return classicInterfaceWrap.Get_AnswerCode(self.context)

    def Set_AnswerCode(self, value):
        classicInterfaceWrap.Set_AnswerCode(self.context, value)

    def GetMFPCode3Status(self):
        return classicInterfaceWrap.GetMFPCode3Status(self.context)

    def Get_MFPNumber(self):
        resultLen = classicInterfaceWrap.Get_MFPNumber(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_MFPNumber(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_MFPNumber(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_MFPNumber(self.context, valueBuff, len(valueBuff))

    def Get_ReadTimeout(self):
        return classicInterfaceWrap.Get_ReadTimeout(self.context)

    def Set_ReadTimeout(self, value):
        classicInterfaceWrap.Set_ReadTimeout(self.context, value)

    def ClearReportBuffer(self):
        return classicInterfaceWrap.ClearReportBuffer(self.context)

    def Get_IsBlockedByWrongTaxPassword(self):
        return classicInterfaceWrap.Get_IsBlockedByWrongTaxPassword(self.context)

    def Get_LastFMRecordType(self):
        return classicInterfaceWrap.Get_LastFMRecordType(self.context)

    def ShowAdditionalParams(self):
        return classicInterfaceWrap.ShowAdditionalParams(self.context)

    def Get_CloudCashdeskEnabled(self):
        return classicInterfaceWrap.Get_CloudCashdeskEnabled(self.context)

    def Get_ECRID(self):
        resultLen = classicInterfaceWrap.Get_ECRID(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ECRID(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_CloudCashdeskEnabled(self, value):
        classicInterfaceWrap.Set_CloudCashdeskEnabled(self.context, value)

    def Set_ECRID(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_ECRID(self.context, valueBuff, len(valueBuff))

    def GetCloudCashdeskParams(self):
        return classicInterfaceWrap.GetCloudCashdeskParams(self.context)

    def Get_KSAInfo(self):
        resultLen = classicInterfaceWrap.Get_KSAInfo(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_KSAInfo(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_KSAInfo(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_KSAInfo(self.context, valueBuff, len(valueBuff))

    def DrawScale(self):
        return classicInterfaceWrap.DrawScale(self.context)

    def Get_BarcodeFirstLine(self):
        return classicInterfaceWrap.Get_BarcodeFirstLine(self.context)

    def Set_BarcodeFirstLine(self, value):
        classicInterfaceWrap.Set_BarcodeFirstLine(self.context, value)

    def Get_SKNOError(self):
        return classicInterfaceWrap.Get_SKNOError(self.context)

    def Set_SKNOError(self, value):
        classicInterfaceWrap.Set_SKNOError(self.context, value)

    def Get_SKNOIdentifier(self):
        resultLen = classicInterfaceWrap.Get_SKNOIdentifier(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_SKNOIdentifier(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_SKNOIdentifier(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_SKNOIdentifier(self.context, valueBuff, len(valueBuff))

    def LoadGraphics512(self): # Загрузка графики 512
        return classicInterfaceWrap.LoadGraphics512(self.context)

    def PrintGraphics512(self): # Печать графики 512 с масштабированием
        return classicInterfaceWrap.PrintGraphics512(self.context)

    def Get_SyncTimeout(self):
        return classicInterfaceWrap.Get_SyncTimeout(self.context)

    def Set_SyncTimeout(self, value):
        classicInterfaceWrap.Set_SyncTimeout(self.context, value)

    def FNGetExpirationTime(self): # Запросить срок действия ФН
        return classicInterfaceWrap.FNGetExpirationTime(self.context)

    def FNGetSerial(self): # Запросить заводской номер ФН
        return classicInterfaceWrap.FNGetSerial(self.context)

    def FNGetStatus(self): # Запросить состояние ФН
        return classicInterfaceWrap.FNGetStatus(self.context)

    def FNGetVersion(self): # Запросить версию ФН
        return classicInterfaceWrap.FNGetVersion(self.context)

    def FNBeginFiscalization(self):
        return classicInterfaceWrap.FNBeginFiscalization(self.context)

    def FNFiscalization(self):
        return classicInterfaceWrap.FNFiscalization(self.context)

    def FNCancelDocument(self): # Отменить документ ФН
        return classicInterfaceWrap.FNCancelDocument(self.context)

    def FNResetState(self): # Сбросить состояние ФН
        return classicInterfaceWrap.FNResetState(self.context)

    def FNFindDocument(self): # Найти документ ФН
        return classicInterfaceWrap.FNFindDocument(self.context)

    def Get_DocumentData(self):
        resultLen = classicInterfaceWrap.Get_DocumentData(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_DocumentData(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_DocumentData(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_DocumentData(self.context, valueBuff, len(valueBuff))

    def FNOpenSession(self): # Открыть смену ФН
        return classicInterfaceWrap.FNOpenSession(self.context)

    def FNSendTLV(self): # Передать структуру TLV в ФН
        return classicInterfaceWrap.FNSendTLV(self.context)

    def FNDiscountOperation(self):
        return classicInterfaceWrap.FNDiscountOperation(self.context)

    def FNStorno(self): # Сторно ФН
        return classicInterfaceWrap.FNStorno(self.context)

    def OFDExchange(self): # Выполнить единичный обмен с ОФД средствами драйвера(EoD)
        return classicInterfaceWrap.OFDExchange(self.context)

    def Get_OFDEnabled(self):
        return classicInterfaceWrap.Get_OFDEnabled(self.context)

    def Set_OFDEnabled(self, value):
        classicInterfaceWrap.Set_OFDEnabled(self.context, value)

    def FNBeginCalculationStateReport(self): # Начать формирование отчета о состоянии расчетов
        return classicInterfaceWrap.FNBeginCalculationStateReport(self.context)

    def FNBeginCloseFiscalMode(self): # Начать закрытие фискального режима
        return classicInterfaceWrap.FNBeginCloseFiscalMode(self.context)

    def FNBeginCloseSession(self): # Начать закрытие смены
        return classicInterfaceWrap.FNBeginCloseSession(self.context)

    def FNBeginCorrectionReceipt(self): # Начать формирование чека коррекции
        return classicInterfaceWrap.FNBeginCorrectionReceipt(self.context)

    def FNBeginOpenSession(self): # Начать открытие смены
        return classicInterfaceWrap.FNBeginOpenSession(self.context)

    def FNBeginRegistrationReport(self): # Начать формирование отчета о регистрации ККТ
        return classicInterfaceWrap.FNBeginRegistrationReport(self.context)

    def FNBuildCalculationStateReport(self): # Сформировать отчет о состоянии расчетов
        return classicInterfaceWrap.FNBuildCalculationStateReport(self.context)

    def FNBuildCorrectionReceipt(self): # Сформировать чек коррекции ФН
        return classicInterfaceWrap.FNBuildCorrectionReceipt(self.context)

    def FNBuildRegistrationReport(self): # Сформировать отчет о регистрации ФН
        return classicInterfaceWrap.FNBuildRegistrationReport(self.context)

    def FNCloseFiscalMode(self): # Закрыть фискальный режим ФН
        return classicInterfaceWrap.FNCloseFiscalMode(self.context)

    def FNCloseSession(self): # Закрыть смену
        return classicInterfaceWrap.FNCloseSession(self.context)

    def FNGetCurrentSessionParams(self): # Получить параметры текущей смены ФН
        return classicInterfaceWrap.FNGetCurrentSessionParams(self.context)

    def FNGetInfoExchangeStatus(self): # Получить статус информационного обмена
        return classicInterfaceWrap.FNGetInfoExchangeStatus(self.context)

    def FNGetOFDTicketByDocNumber(self): # Запрос квитанции о получении данных в ОФД по номеру документа
        return classicInterfaceWrap.FNGetOFDTicketByDocNumber(self.context)

    def FNGetUnconfirmedDocCount(self): # Запрос количества ФД, на которые нет квитанции
        return classicInterfaceWrap.FNGetUnconfirmedDocCount(self.context)

    def FNReadFiscalDocumentTLV(self): # Прочитать запрошенный командой FNRequestFiscalDocumentTLV фискальный документ в формате TLV
        return classicInterfaceWrap.FNReadFiscalDocumentTLV(self.context)

    def FNRequestFiscalDocumentTLV(self): # Запросить фискальный документ в формате TLV для дальнейшего чтения при помощи метода FNReadFiscalDocumentTLV
        return classicInterfaceWrap.FNRequestFiscalDocumentTLV(self.context)

    def FNBuildReregistrationReport(self): # Сформировать отчет о перерегистрации ФН
        return classicInterfaceWrap.FNBuildReregistrationReport(self.context)

    def FNGetFiscalizationResult(self): # Запросить итоги фискализации ФН
        return classicInterfaceWrap.FNGetFiscalizationResult(self.context)

    def FNDiscountTaxOperation(self):
        return classicInterfaceWrap.FNDiscountTaxOperation(self.context)

    def FNCloseCheckEx(self): # Закрытие чека расширенное в ФН
        return classicInterfaceWrap.FNCloseCheckEx(self.context)

    def Get_ChargeValue(self):
        return classicInterfaceWrap.Get_ChargeValue(self.context)

    def Get_DiscountValue(self):
        return classicInterfaceWrap.Get_DiscountValue(self.context)

    def Set_ChargeValue(self, value):
        classicInterfaceWrap.Set_ChargeValue(self.context, value)

    def Set_DiscountValue(self, value):
        classicInterfaceWrap.Set_DiscountValue(self.context, value)

    def Get_DiscountName(self):
        resultLen = classicInterfaceWrap.Get_DiscountName(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_DiscountName(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_DiscountName(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_DiscountName(self.context, valueBuff, len(valueBuff))

    def FNSendCustomerEmail(self): # Передает в ФН тег 1008 (“телефон или e-mail покупателя”)
        return classicInterfaceWrap.FNSendCustomerEmail(self.context)

    def Annulment(self):
        return classicInterfaceWrap.Annulment(self.context)

    def FNDiscountChargeRN(self):
        return classicInterfaceWrap.FNDiscountChargeRN(self.context)

    def ExportTables(self): # Экспорт всех таблиц в файл
        return classicInterfaceWrap.ExportTables(self.context)

    def ImportTables(self): # Импорт таблиц из файла csv файла
        return classicInterfaceWrap.ImportTables(self.context)

    def FNSendTag(self): # Отправить произвольный тег в ФН
        return classicInterfaceWrap.FNSendTag(self.context)

    def ReadSerialNumber(self): # Получить заводской номер устройства
        return classicInterfaceWrap.ReadSerialNumber(self.context)

    def FNPrintOperatorConfirm(self):
        return classicInterfaceWrap.FNPrintOperatorConfirm(self.context)

    def FNGetFiscalizationResultByNumber(self): # Запрос итогов фискализации ФН по номеру
        return classicInterfaceWrap.FNGetFiscalizationResultByNumber(self.context)

    def AnnulmentRB(self):
        return classicInterfaceWrap.AnnulmentRB(self.context)

    def FNGetTagDescription(self):
        return classicInterfaceWrap.FNGetTagDescription(self.context)

    def Get_TagDescription(self):
        resultLen = classicInterfaceWrap.Get_TagDescription(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_TagDescription(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_TagDescription(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_TagDescription(self.context, valueBuff, len(valueBuff))

    def FNPrintDocument(self):
        return classicInterfaceWrap.FNPrintDocument(self.context)

    def FNGetDocumentAsString(self): # Получить документ из ФН в виде текста
        return classicInterfaceWrap.FNGetDocumentAsString(self.context)

    def Ping(self):
        return classicInterfaceWrap.Ping(self.context)

    def Get_URL(self):
        resultLen = classicInterfaceWrap.Get_URL(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_URL(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_URL(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_URL(self.context, valueBuff, len(valueBuff))

    def Get_PingTime(self):
        return classicInterfaceWrap.Get_PingTime(self.context)

    def Set_PingTime(self, value):
        classicInterfaceWrap.Set_PingTime(self.context, value)

    def Get_PingResult(self):
        return classicInterfaceWrap.Get_PingResult(self.context)

    def Set_PingResult(self, value):
        classicInterfaceWrap.Set_PingResult(self.context, value)

    def Get_ICSEnabled(self):
        return classicInterfaceWrap.Get_ICSEnabled(self.context)

    def Get_ICSPollPeriod(self):
        return classicInterfaceWrap.Get_ICSPollPeriod(self.context)

    def Set_ICSEnabled(self, value):
        classicInterfaceWrap.Set_ICSEnabled(self.context, value)

    def Set_ICSPollPeriod(self, value):
        classicInterfaceWrap.Set_ICSPollPeriod(self.context, value)

    def FNOperation(self): # Операция в ФН
        return classicInterfaceWrap.FNOperation(self.context)

    def FNSendTLVOperation(self): # Отправить TLV, привязанный к операции
        return classicInterfaceWrap.FNSendTLVOperation(self.context)

    def Get_TaxValue1Enabled(self):
        return classicInterfaceWrap.Get_TaxValue1Enabled(self.context)

    def Get_TaxValue2Enabled(self):
        return classicInterfaceWrap.Get_TaxValue2Enabled(self.context)

    def Get_TaxValue3Enabled(self):
        return classicInterfaceWrap.Get_TaxValue3Enabled(self.context)

    def Get_TaxValue4Enabled(self):
        return classicInterfaceWrap.Get_TaxValue4Enabled(self.context)

    def Get_TaxValue5Enabled(self):
        return classicInterfaceWrap.Get_TaxValue5Enabled(self.context)

    def Get_TaxValue6Enabled(self):
        return classicInterfaceWrap.Get_TaxValue6Enabled(self.context)

    def Set_TaxValue1Enabled(self, value):
        classicInterfaceWrap.Set_TaxValue1Enabled(self.context, value)

    def Set_TaxValue2Enabled(self, value):
        classicInterfaceWrap.Set_TaxValue2Enabled(self.context, value)

    def Set_TaxValue3Enabled(self, value):
        classicInterfaceWrap.Set_TaxValue3Enabled(self.context, value)

    def Set_TaxValue4Enabled(self, value):
        classicInterfaceWrap.Set_TaxValue4Enabled(self.context, value)

    def Set_TaxValue5Enabled(self, value):
        classicInterfaceWrap.Set_TaxValue5Enabled(self.context, value)

    def Set_TaxValue6Enabled(self, value):
        classicInterfaceWrap.Set_TaxValue6Enabled(self.context, value)

    def FNBuildCorrectionReceipt2(self): # Сформировать чек коррекции V2
        return classicInterfaceWrap.FNBuildCorrectionReceipt2(self.context)

    def Get_OFDReadTimeout(self):
        return classicInterfaceWrap.Get_OFDReadTimeout(self.context)

    def Set_OFDReadTimeout(self, value):
        classicInterfaceWrap.Set_OFDReadTimeout(self.context, value)

    def FNGetNonClearableSumm(self): # Получить необнуляемые суммы в ФН
        return classicInterfaceWrap.FNGetNonClearableSumm(self.context)

    def ResetSerialNumber(self):
        return classicInterfaceWrap.ResetSerialNumber(self.context)

    def DBFindDocument(self):
        return classicInterfaceWrap.DBFindDocument(self.context)

    def Get_DBFilePath(self):
        resultLen = classicInterfaceWrap.Get_DBFilePath(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_DBFilePath(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_DBFilePath(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_DBFilePath(self.context, valueBuff, len(valueBuff))

    def DBPrintDocument(self):
        return classicInterfaceWrap.DBPrintDocument(self.context)

    def Get_KKTLicense(self):
        return classicInterfaceWrap.Get_KKTLicense(self.context)

    def Get_LicenseNumber(self):
        return classicInterfaceWrap.Get_LicenseNumber(self.context)

    def Get_PUKCode(self):
        return classicInterfaceWrap.Get_PUKCode(self.context)

    def ReadKKTLicenses(self):
        return classicInterfaceWrap.ReadKKTLicenses(self.context)

    def Set_KKTLicense(self, value):
        classicInterfaceWrap.Set_KKTLicense(self.context, value)

    def Set_LicenseNumber(self, value):
        classicInterfaceWrap.Set_LicenseNumber(self.context, value)

    def Set_PUKCode(self, value):
        classicInterfaceWrap.Set_PUKCode(self.context, value)

    def Get_OFDExchangeSuspended(self):
        return classicInterfaceWrap.Get_OFDExchangeSuspended(self.context)

    def Set_OFDExchangeSuspended(self, value):
        classicInterfaceWrap.Set_OFDExchangeSuspended(self.context, value)

    def CloseCheckBel(self):
        return classicInterfaceWrap.CloseCheckBel(self.context)

    def GetKKTLicenseByNumber(self):
        return classicInterfaceWrap.GetKKTLicenseByNumber(self.context)

    def WriteKKTLicense(self):
        return classicInterfaceWrap.WriteKKTLicense(self.context)

    def FNSendSenderEmail(self): # Передает в ФН тег 1117 (“адрес электронной почты отправителя чека”)
        return classicInterfaceWrap.FNSendSenderEmail(self.context)

    def Get_Discount1(self):
        return classicInterfaceWrap.Get_Discount1(self.context)

    def Get_Discount2(self):
        return classicInterfaceWrap.Get_Discount2(self.context)

    def Get_Discount3(self):
        return classicInterfaceWrap.Get_Discount3(self.context)

    def Get_Discount4(self):
        return classicInterfaceWrap.Get_Discount4(self.context)

    def Get_UseTaxDiscountBel(self):
        return classicInterfaceWrap.Get_UseTaxDiscountBel(self.context)

    def Set_Discount1(self, value):
        classicInterfaceWrap.Set_Discount1(self.context, value)

    def Set_Discount2(self, value):
        classicInterfaceWrap.Set_Discount2(self.context, value)

    def Set_Discount3(self, value):
        classicInterfaceWrap.Set_Discount3(self.context, value)

    def Set_Discount4(self, value):
        classicInterfaceWrap.Set_Discount4(self.context, value)

    def Set_UseTaxDiscountBel(self, value):
        classicInterfaceWrap.Set_UseTaxDiscountBel(self.context, value)

    def Get_Summ1AsString(self):
        resultLen = classicInterfaceWrap.Get_Summ1AsString(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_Summ1AsString(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_Summ2AsString(self):
        resultLen = classicInterfaceWrap.Get_Summ2AsString(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_Summ2AsString(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_Summ3AsString(self):
        resultLen = classicInterfaceWrap.Get_Summ3AsString(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_Summ3AsString(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_Summ4AsString(self):
        resultLen = classicInterfaceWrap.Get_Summ4AsString(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_Summ4AsString(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def DBGetNextDocument(self):
        return classicInterfaceWrap.DBGetNextDocument(self.context)

    def DBPrintNextDocument(self):
        return classicInterfaceWrap.DBPrintNextDocument(self.context)

    def DBQueryDocumentsInSession(self):
        return classicInterfaceWrap.DBQueryDocumentsInSession(self.context)

    def Get_DBDocType(self):
        return classicInterfaceWrap.Get_DBDocType(self.context)

    def Set_DBDocType(self, value):
        classicInterfaceWrap.Set_DBDocType(self.context, value)

    def Get_OPBarcodeInputType(self):
        return classicInterfaceWrap.Get_OPBarcodeInputType(self.context)

    def Get_OPIdPayment(self):
        resultLen = classicInterfaceWrap.Get_OPIdPayment(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_OPIdPayment(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_OPRequisiteNumber(self):
        return classicInterfaceWrap.Get_OPRequisiteNumber(self.context)

    def Get_OPRequisiteValue(self):
        resultLen = classicInterfaceWrap.Get_OPRequisiteValue(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_OPRequisiteValue(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_OPSystem(self):
        return classicInterfaceWrap.Get_OPSystem(self.context)

    def Get_OPTransactionStatus(self):
        return classicInterfaceWrap.Get_OPTransactionStatus(self.context)

    def Get_OPTransactionType(self):
        return classicInterfaceWrap.Get_OPTransactionType(self.context)

    def OnlinePay(self):
        return classicInterfaceWrap.OnlinePay(self.context)

    def OPGetLastRequisite(self):
        return classicInterfaceWrap.OPGetLastRequisite(self.context)

    def OPGetLastStatus(self):
        return classicInterfaceWrap.OPGetLastStatus(self.context)

    def Set_OPBarcodeInputType(self, value):
        classicInterfaceWrap.Set_OPBarcodeInputType(self.context, value)

    def Set_OPIdPayment(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_OPIdPayment(self.context, valueBuff, len(valueBuff))

    def Set_OPRequisiteNumber(self, value):
        classicInterfaceWrap.Set_OPRequisiteNumber(self.context, value)

    def Set_OPRequisiteValue(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_OPRequisiteValue(self.context, valueBuff, len(valueBuff))

    def Set_OPSystem(self, value):
        classicInterfaceWrap.Set_OPSystem(self.context, value)

    def Set_OPTransactionStatus(self, value):
        classicInterfaceWrap.Set_OPTransactionStatus(self.context, value)

    def Set_OPTransactionType(self, value):
        classicInterfaceWrap.Set_OPTransactionType(self.context, value)

    def Get_Token(self):
        resultLen = classicInterfaceWrap.Get_Token(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_Token(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def GenerateMonoToken(self):
        return classicInterfaceWrap.GenerateMonoToken(self.context)

    def Set_Token(self, value):
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_Token(self.context, valueBuff, len(valueBuff))

    def RebootKKT(self): # Перезагрузить ККТ
        return classicInterfaceWrap.RebootKKT(self.context)

    def FNAddTag(self): # Добавить тег
        return classicInterfaceWrap.FNAddTag(self.context)

    def FNBeginSTLVTag(self): # Начать СТЛВ тег
        return classicInterfaceWrap.FNBeginSTLVTag(self.context)

    def FNSendSTLVTag(self): # Отправить СТЛВ тег
        return classicInterfaceWrap.FNSendSTLVTag(self.context)

    def FNSendSTLVTagOperation(self): # Отправить СТЛВ тег, привязанный к операции
        return classicInterfaceWrap.FNSendSTLVTagOperation(self.context)

    def FNSendTagOperation(self): # Отправить тег, привязанный к операции
        return classicInterfaceWrap.FNSendTagOperation(self.context)

    def Get_SymbolCode(self): # Код символа
        return classicInterfaceWrap.Get_SymbolCode(self.context)

    def Set_SymbolCode(self, value):
        classicInterfaceWrap.Set_SymbolCode(self.context, value)

    def Get_SymbolWidth(self): # Ширина символа
        return classicInterfaceWrap.Get_SymbolWidth(self.context)

    def Set_SymbolWidth(self, value):
        classicInterfaceWrap.Set_SymbolWidth(self.context, value)

    def Get_SymbolHeight(self): # Высота символа
        return classicInterfaceWrap.Get_SymbolHeight(self.context)

    def Set_SymbolHeight(self, value):
        classicInterfaceWrap.Set_SymbolHeight(self.context, value)

    def Get_FileType(self):
        return classicInterfaceWrap.Get_FileType(self.context)

    def Set_FileType(self, value):
        classicInterfaceWrap.Set_FileType(self.context, value)

    def Get_DelayOnDisconnect(self):
        return classicInterfaceWrap.Get_DelayOnDisconnect(self.context)

    def Set_DelayOnDisconnect(self, value):
        classicInterfaceWrap.Set_DelayOnDisconnect(self.context, value)

    def Set_GTIN(self, value): # Код маркировки товара
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_GTIN(self.context, valueBuff, len(valueBuff))

    def Get_GTIN(self): # Get_GTIN Возвращает значения свойства #GTIN
        resultLen = classicInterfaceWrap.Get_GTIN(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_GTIN(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def FNSendItemCodeData(self): # Отправить КТН тег
        return classicInterfaceWrap.FNSendItemCodeData(self.context)

    def FNCheckItemBarcode(self): # Проверка маркированного товара
        return classicInterfaceWrap.FNCheckItemBarcode(self.context)

    def FNRequestRegistrationTLV(self): # Запрос параметра открытия ФН
        return classicInterfaceWrap.FNRequestRegistrationTLV(self.context)

    def ReadLoaderVersion(self): # Прочитать версию загрузчика
        return classicInterfaceWrap.ReadLoaderVersion(self.context)

    def Get_RequestDocumentType(self):
        return classicInterfaceWrap.Get_RequestDocumentType(self.context)

    def Set_RequestDocumentType(self, value):
        classicInterfaceWrap.Set_RequestDocumentType(self.context, value)

    def FNOpenCheckCorrection(self): # Открыть чек коррекции
        return classicInterfaceWrap.FNOpenCheckCorrection(self.context)

    def FNCountersSync(self):
        return classicInterfaceWrap.FNCountersSync(self.context)

    def FNGetFreeMemoryResource(self):
        return classicInterfaceWrap.FNGetFreeMemoryResource(self.context)

    def ReadCashDrawerSum(self): # Получить сумму денег в денежном ящике
        return classicInterfaceWrap.ReadCashDrawerSum(self.context)

    def ReadFeatureLicenses(self): # Прочитать лицензию из ККМ
        return classicInterfaceWrap.ReadFeatureLicenses(self.context)

    def WriteFeatureLicenses(self): # Записать лицензию в ККМ
        return classicInterfaceWrap.WriteFeatureLicenses(self.context)

    def SetDeviceFunction(self): # Установить значение функции устройства
        return classicInterfaceWrap.SetDeviceFunction(self.context)

    def GetDeviceFunction(self): # Получает значение функции устройства
        return classicInterfaceWrap.GetDeviceFunction(self.context)

    def FNSendItemBarcode(self): # Привязать марку к позиции
        return classicInterfaceWrap.FNSendItemBarcode(self.context)

    def FNGetKMServerExchangeStatus(self): # Получить состояние по передаче уведомлений о реализации маркированного товара
        return classicInterfaceWrap.FNGetKMServerExchangeStatus(self.context)

    def FNGetMarkingCodeWorkStatus(self): # Запрос статуса по работе с кодами маркировки
        return classicInterfaceWrap.FNGetMarkingCodeWorkStatus(self.context)

    def FNBeginReadNotifications(self): # Начать чтение уведомлений о реализации маркированного товара из ФН (ФФД 1.2) (автономный режим) Уведомления читаются затем последовательно вызовом метода FNReadNotificationBlock
        return classicInterfaceWrap.FNBeginReadNotifications(self.context)

    def FNReadNotificationBlock(self): # Прочитать блок уведомления о реализации маркированного товара из ФН. Производится последовательное чтение. Ошибка 8 означает, что все уведомления прочитаны. (ФФД 1.2) (автономный режим)
        return classicInterfaceWrap.FNReadNotificationBlock(self.context)

    def FNConfirmNotificationRead(self): # Подтверждение выгрузки уведомления (ФФД 1.2)
        return classicInterfaceWrap.FNConfirmNotificationRead(self.context)

    def GetTagAsTLV(self): # Получить представление тега в виде TLV массива байт. Для работы с STLV-тегами необходимо сначала использовать методы FNBeginSTLVTag, FNAddTag
        return classicInterfaceWrap.GetTagAsTLV(self.context)

    def ReadRandomSequence(self): # Получить случайную последовательность
        return classicInterfaceWrap.ReadRandomSequence(self.context)

    def Authorization(self): # Авторизоваться
        return classicInterfaceWrap.Authorization(self.context)

    def FNAcceptMarkingCode(self): # Принять код маркировки
        return classicInterfaceWrap.FNAcceptMarkingCode(self.context)

    def FNDeclineMarkingCode(self): # Отвергнуть код маркировки
        return classicInterfaceWrap.FNDeclineMarkingCode(self.context)

    def FNMarkingClearBuffer(self): # Очистить буфер проверки КМ
        return classicInterfaceWrap.FNMarkingClearBuffer(self.context)

    def FNBindMarkingItem(self): # Привязать код маркировки
        return classicInterfaceWrap.FNBindMarkingItem(self.context)

    def FNBeginReadArchive(self): # Начать чтение архива ФН
        return classicInterfaceWrap.FNBeginReadArchive(self.context)

    def FNReadArchiveItem(self): # Прочитать документ и добавить его в архив ФН.(Необходимо предварительно вызвать метод FNBeginReadArchive)
        return classicInterfaceWrap.FNReadArchiveItem(self.context)

    def FNSaveArchive(self): # Сохранить архив ФН в файл
        return classicInterfaceWrap.FNSaveArchive(self.context)

    def Set_LastDocumentNumber(self, value):
        classicInterfaceWrap.Set_LastDocumentNumber(self.context, value)

    def Get_LastDocumentNumber(self):
        return classicInterfaceWrap.Get_LastDocumentNumber(self.context)

    def Set_FirstDocumentNumber(self, value):
        classicInterfaceWrap.Set_FirstDocumentNumber(self.context, value)

    def Get_FirstDocumentNumber(self):
        return classicInterfaceWrap.Get_FirstDocumentNumber(self.context)

    def FNSendUserAttribute(self): # Послать дополнительный реквизит пользователя, тег 1084
        return classicInterfaceWrap.FNSendUserAttribute(self.context)

    def RenderDeclarativeDocument(self): # Рендер декларативного документа
        return classicInterfaceWrap.RenderDeclarativeDocument(self.context)

    def LoadFont(self): # Загружает пользовательский шрифт из файла в формате "spf"
        return classicInterfaceWrap.LoadFont(self.context)

    def ReadFontHash(self): # Прочитать хеш пользовательского шрифта
        return classicInterfaceWrap.ReadFontHash(self.context)

    def ResetFont(self): # Сбросить пользовательский шрифт в ККТ на шрифт по умолчанию (№1)
        return classicInterfaceWrap.ResetFont(self.context)

    def LoadFontSymbol(self): # Загружает данные символа пользовательского шрифта (№9)
        return classicInterfaceWrap.LoadFontSymbol(self.context)

    def DecodeTLVData(self): # Декодировать TLV в строку
        return classicInterfaceWrap.DecodeTLVData(self.context)

    def FNGetImplementation(self): # Получить исполнение ФНа (подверсия)
        return classicInterfaceWrap.FNGetImplementation(self.context)

    def FNGetOSUSupportStatus(self): # Запрос статуса поддержки ФН ОСУ
        return classicInterfaceWrap.FNGetOSUSupportStatus(self.context)

    def FNGetDocumentSize(self): # Размер в байтах текущего документа в ФН
        return classicInterfaceWrap.FNGetDocumentSize(self.context)

    def FNReadFiscalBarcode(self): # Возвращает штрихкод фискального чека
        return classicInterfaceWrap.FNReadFiscalBarcode(self.context)

    def PrintStringWithWrap(self): # Печать cтроки с переносом
        return classicInterfaceWrap.PrintStringWithWrap(self.context)

    def Get_BarCode(self): # Штрих-код, печатаемый на чеке
        resultLen = classicInterfaceWrap.Get_BarCode(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_BarCode(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_BarCode(self, value): # Устанавливает значение свойства #BarCode
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_BarCode(self.context, valueBuff, len(valueBuff))

    def Get_BatteryVoltage(self): # Напряжение на батарейке
        return classicInterfaceWrap.Get_BatteryVoltage(self.context)

    def Get_BaudRate(self): # Скорость обмена
        return classicInterfaceWrap.Get_BaudRate(self.context)

    def Set_BaudRate(self, value): # Устанавливает значение свойства #BaudRate
        classicInterfaceWrap.Set_BaudRate(self.context, value)

    def Get_Change(self): # Сдача
        return classicInterfaceWrap.Get_Change(self.context)

    def Get_CheckType(self): # Тип чека
        return classicInterfaceWrap.Get_CheckType(self.context)

    def Set_CheckType(self, value): # Устанавливает значение свойства #CheckType
        classicInterfaceWrap.Set_CheckType(self.context, value)

    def Get_ComNumber(self): # Номер Com-порта
        return classicInterfaceWrap.Get_ComNumber(self.context)

    def Set_ComNumber(self, value): # Устанавливает значение свойства #ComNumber
        classicInterfaceWrap.Set_ComNumber(self.context, value)

    def Get_ContentsOfCashRegister(self): # Содержимое денежного регистра
        return classicInterfaceWrap.Get_ContentsOfCashRegister(self.context)

    def Get_ContentsOfOperationRegister(self): # Содержимое операционного регистра
        return classicInterfaceWrap.Get_ContentsOfOperationRegister(self.context)

    def Get_CutType(self): # Тип отрезки
        return classicInterfaceWrap.Get_CutType(self.context)

    def Set_CutType(self, value): # Устанавливает значение свойства #CutType
        classicInterfaceWrap.Set_CutType(self.context, value)

    def Get_DataBlock(self): # Блок данных
        resultLen = classicInterfaceWrap.Get_DataBlock(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_DataBlock(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_DataBlockHex(self): # Возвращает значение свойства #DataBlockHex
        resultLen = classicInterfaceWrap.Get_DataBlockHex(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_DataBlockHex(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_DataBlockNumber(self): # Номер блока данных
        return classicInterfaceWrap.Get_DataBlockNumber(self.context)

    def Get_Date(self): # Внутренняя дата ККМ
        return unwrapDateTime(classicInterfaceWrap.Get_Date(self.context))

    def Set_Date(self, value): # Устанавливает значение свойства #Date
        classicInterfaceWrap.Set_Date(self.context, wrapDateTime(value))

    def Get_Department(self): # Номер отдела (секции)
        return classicInterfaceWrap.Get_Department(self.context)

    def Set_Department(self, value): # Устанавливает значение свойства #Department
        classicInterfaceWrap.Set_Department(self.context, value)

    def Get_DeviceCode(self): # Код устройства
        return classicInterfaceWrap.Get_DeviceCode(self.context)

    def Set_DeviceCode(self, value): # Устанавливает значение свойства #DeviceCode
        classicInterfaceWrap.Set_DeviceCode(self.context, value)

    def Get_DeviceCodeDescription(self): # Описание устройства
        resultLen = classicInterfaceWrap.Get_DeviceCodeDescription(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_DeviceCodeDescription(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_DiscountOnCheck(self): # Скидка на чек
        return classicInterfaceWrap.Get_DiscountOnCheck(self.context)

    def Set_DiscountOnCheck(self, value): # Устанавливает значение свойства #DiscountOnCheck
        classicInterfaceWrap.Set_DiscountOnCheck(self.context, value)

    def Get_DocumentName(self): # Наименование документа
        resultLen = classicInterfaceWrap.Get_DocumentName(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_DocumentName(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_DocumentName(self, value): # Устанавливает значение свойства #DocumentName
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_DocumentName(self.context, valueBuff, len(valueBuff))

    def Get_DocumentNumber(self): # Номер документа
        return classicInterfaceWrap.Get_DocumentNumber(self.context)

    def Set_DocumentNumber(self, value): # Устанавливает значение свойства #DocumentNumber
        classicInterfaceWrap.Set_DocumentNumber(self.context, value)

    def Get_DrawerNumber(self): # Номер денежного ящика
        return classicInterfaceWrap.Get_DrawerNumber(self.context)

    def Set_DrawerNumber(self, value): # Устанавливает значение свойства #DrawerNumber
        classicInterfaceWrap.Set_DrawerNumber(self.context, value)

    def Get_ECRAdvancedMode(self): # Подрежим ККМ
        return classicInterfaceWrap.Get_ECRAdvancedMode(self.context)

    def Get_ECRBuild(self): # Номер сборки ПО ККМ
        return classicInterfaceWrap.Get_ECRBuild(self.context)

    def Get_ECRFlags(self): # Флаги ККМ
        return classicInterfaceWrap.Get_ECRFlags(self.context)

    def Get_ReceiptRibbonIsPresent(self): # Рулон чековой ленты есть
        return classicInterfaceWrap.Get_ReceiptRibbonIsPresent(self.context)

    def Get_JournalRibbonIsPresent(self): # Рулон операционного журнала есть
        return classicInterfaceWrap.Get_JournalRibbonIsPresent(self.context)

    def Get_SlipDocumentIsPresent(self): # Подкладной документ есть
        return classicInterfaceWrap.Get_SlipDocumentIsPresent(self.context)

    def Get_SlipDocumentIsMoving(self): # Подкладной документ проходит
        return classicInterfaceWrap.Get_SlipDocumentIsMoving(self.context)

    def Get_PointPosition(self): # Положение точки
        return classicInterfaceWrap.Get_PointPosition(self.context)

    def Set_PointPosition(self, value): # Устанавливает значение свойства #PointPosition
        classicInterfaceWrap.Set_PointPosition(self.context, value)

    def Get_EKLZIsPresent(self): # ЭКЛЗ есть
        return classicInterfaceWrap.Get_EKLZIsPresent(self.context)

    def Get_JournalRibbonOpticalSensor(self): # Оптический датчик операционного журнала
        return classicInterfaceWrap.Get_JournalRibbonOpticalSensor(self.context)

    def Get_ReceiptRibbonOpticalSensor(self): # Оптический датчик чековой ленты
        return classicInterfaceWrap.Get_ReceiptRibbonOpticalSensor(self.context)

    def Get_JournalRibbonLever(self): # Рычаг термоголовки операционного журнала
        return classicInterfaceWrap.Get_JournalRibbonLever(self.context)

    def Get_ReceiptRibbonLever(self): # Рычаг термоголовки чековой ленты
        return classicInterfaceWrap.Get_ReceiptRibbonLever(self.context)

    def Get_LidPositionSensor(self): # Датчик крышки корпуса
        return classicInterfaceWrap.Get_LidPositionSensor(self.context)

    def Get_IsDrawerOpen(self): # Денежный ящик открыт
        return classicInterfaceWrap.Get_IsDrawerOpen(self.context)

    def Get_IsPrinterRightSensorFailure(self): # Отказ правого датчика печатающего механизма
        return classicInterfaceWrap.Get_IsPrinterRightSensorFailure(self.context)

    def Get_IsPrinterLeftSensorFailure(self): # Отказ левого датчика печатающего механизма
        return classicInterfaceWrap.Get_IsPrinterLeftSensorFailure(self.context)

    def Get_IsEKLZOverflow(self): # Переполнение ЭКЛЗ
        return classicInterfaceWrap.Get_IsEKLZOverflow(self.context)

    def Get_QuantityPointPosition(self): # Положение точки в количестве
        return classicInterfaceWrap.Get_QuantityPointPosition(self.context)

    def Get_SKNOStatus(self): # Статус СКНО
        return classicInterfaceWrap.Get_SKNOStatus(self.context)

    def Set_SKNOStatus(self, value): # Устанавливает значение свойства #SKNOStatus
        classicInterfaceWrap.Set_SKNOStatus(self.context, value)

    def Get_ECRMode(self): # Режим ККМ
        return classicInterfaceWrap.Get_ECRMode(self.context)

    def Get_ECRMode8Status(self): # Статус 8 режима
        return classicInterfaceWrap.Get_ECRMode8Status(self.context)

    def Get_ECRModeDescription(self): # Описание режима ККМ
        resultLen = classicInterfaceWrap.Get_ECRModeDescription(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ECRModeDescription(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_ECRSoftDate(self): # Дата ПО ККМ
        return unwrapDateTime(classicInterfaceWrap.Get_ECRSoftDate(self.context))

    def Get_ECRSoftVersion(self): # Версия ПО ККТ
        resultLen = classicInterfaceWrap.Get_ECRSoftVersion(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ECRSoftVersion(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_FieldName(self): # Название поля
        resultLen = classicInterfaceWrap.Get_FieldName(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_FieldName(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_FieldNumber(self): # Номер поля
        return classicInterfaceWrap.Get_FieldNumber(self.context)

    def Set_FieldNumber(self, value): # Устанавливает значение свойства #FieldNumber
        classicInterfaceWrap.Set_FieldNumber(self.context, value)

    def Get_FieldSize(self): # Размер поля
        return classicInterfaceWrap.Get_FieldSize(self.context)

    def Get_FieldType(self): # Тип поля
        return classicInterfaceWrap.Get_FieldType(self.context)

    def Get_FirstLineNumber(self): # Номер первой линии
        return classicInterfaceWrap.Get_FirstLineNumber(self.context)

    def Set_FirstLineNumber(self, value): # Устанавливает значение свойства #FirstLineNumber
        classicInterfaceWrap.Set_FirstLineNumber(self.context, value)

    def Get_FirstSessionDate(self): # Дата первой смены
        return unwrapDateTime(classicInterfaceWrap.Get_FirstSessionDate(self.context))

    def Set_FirstSessionDate(self, value): # Устанавливает значение свойства #FirstSessionDate
        classicInterfaceWrap.Set_FirstSessionDate(self.context, wrapDateTime(value))

    def Get_FirstSessionNumber(self): # Номер первой смены
        return classicInterfaceWrap.Get_FirstSessionNumber(self.context)

    def Set_FirstSessionNumber(self, value): # Устанавливает значение свойства #FirstSessionNumber
        classicInterfaceWrap.Set_FirstSessionNumber(self.context, value)

    def Get_FMBuild(self): # Сборка ФП
        return classicInterfaceWrap.Get_FMBuild(self.context)

    def Get_FMFlags(self): # Флаги ФП
        return classicInterfaceWrap.Get_FMFlags(self.context)

    def Get_FM1IsPresent(self): # ФП1 есть
        return classicInterfaceWrap.Get_FM1IsPresent(self.context)

    def Get_FM2IsPresent(self): # ФП2 есть
        return classicInterfaceWrap.Get_FM2IsPresent(self.context)

    def Get_LicenseIsPresent(self): # Лицензия есть
        return classicInterfaceWrap.Get_LicenseIsPresent(self.context)

    def Get_FMOverflow(self): # Переполнение ФП
        return classicInterfaceWrap.Get_FMOverflow(self.context)

    def Get_IsBatteryLow(self): # Низкое напряжение на батарее
        return classicInterfaceWrap.Get_IsBatteryLow(self.context)

    def Get_IsLastFMRecordCorrupted(self): # Последняя запись в ФП испорчена
        return classicInterfaceWrap.Get_IsLastFMRecordCorrupted(self.context)

    def Get_IsFMSessionOpen(self): # Смена в ФП открыта
        return classicInterfaceWrap.Get_IsFMSessionOpen(self.context)

    def Get_IsFM24HoursOver(self): # 24 часа в ФП кончились
        return classicInterfaceWrap.Get_IsFM24HoursOver(self.context)

    def Get_FMSoftDate(self): # Дата ПО ФП
        return unwrapDateTime(classicInterfaceWrap.Get_FMSoftDate(self.context))

    def Get_FMSoftVersion(self): # Версия ПО ФП
        resultLen = classicInterfaceWrap.Get_FMSoftVersion(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_FMSoftVersion(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_FreeRecordInFM(self): # Количество свободных записей в ФП
        return classicInterfaceWrap.Get_FreeRecordInFM(self.context)

    def Get_FreeRegistration(self): # Количество оставшихся перерегистраций
        return classicInterfaceWrap.Get_FreeRegistration(self.context)

    def Get_INN(self): # ИНН
        resultLen = classicInterfaceWrap.Get_INN(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_INN(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_INN(self, value): # Устанавливает значение свойства #INN
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_INN(self.context, valueBuff, len(valueBuff))

    def Get_LastLineNumber(self): # Номер последней линии
        return classicInterfaceWrap.Get_LastLineNumber(self.context)

    def Set_LastLineNumber(self, value): # Устанавливает значение свойства #LastLineNumber
        classicInterfaceWrap.Set_LastLineNumber(self.context, value)

    def Get_LastSessionDate(self): # Дата последней смены
        return unwrapDateTime(classicInterfaceWrap.Get_LastSessionDate(self.context))

    def Set_LastSessionDate(self, value): # Устанавливает значение свойства #LastSessionDate
        classicInterfaceWrap.Set_LastSessionDate(self.context, wrapDateTime(value))

    def Get_LastSessionNumber(self): # Номер последней смены
        return classicInterfaceWrap.Get_LastSessionNumber(self.context)

    def Set_LastSessionNumber(self, value): # Устанавливает значение свойства #LastSessionNumber
        classicInterfaceWrap.Set_LastSessionNumber(self.context, value)

    def Get_License(self): # Лицензия
        resultLen = classicInterfaceWrap.Get_License(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_License(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_License(self, value): # Устанавливает значение свойства #License
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_License(self.context, valueBuff, len(valueBuff))

    def Get_LineData(self): # Графическая информация
        resultLen = classicInterfaceWrap.Get_LineData(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_LineData(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_LineData(self, value): # Устанавливает значение свойства #LineData
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_LineData(self.context, valueBuff, len(valueBuff))

    def Get_LineNumber(self): # Номер линии
        return classicInterfaceWrap.Get_LineNumber(self.context)

    def Set_LineNumber(self, value): # Устанавливает значение свойства #LineNumber
        classicInterfaceWrap.Set_LineNumber(self.context, value)

    def Get_LogicalNumber(self): # Номер в зале
        return classicInterfaceWrap.Get_LogicalNumber(self.context)

    def Get_MAXValueOfField(self): # Максимальное значение поля
        return classicInterfaceWrap.Get_MAXValueOfField(self.context)

    def Get_MINValueOfField(self): # Минимальное значение поля
        return classicInterfaceWrap.Get_MINValueOfField(self.context)

    def Get_NameCashReg(self): # Название денежного регистра
        resultLen = classicInterfaceWrap.Get_NameCashReg(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_NameCashReg(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_NameOperationReg(self): # Название операционного регистра
        resultLen = classicInterfaceWrap.Get_NameOperationReg(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_NameOperationReg(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_NewPasswordTI(self): # Новый пароль НИ
        return classicInterfaceWrap.Get_NewPasswordTI(self.context)

    def Set_NewPasswordTI(self, value): # Устанавливает значение свойства #NewPasswordTI
        classicInterfaceWrap.Set_NewPasswordTI(self.context, value)

    def Get_OpenDocumentNumber(self): # Сквозной номер документа
        return classicInterfaceWrap.Get_OpenDocumentNumber(self.context)

    def Get_OperatorNumber(self): # Порядковый номер оператора, чей пароль был введен
        return classicInterfaceWrap.Get_OperatorNumber(self.context)

    def Get_Password(self): # Пароль для исполнения метода драйвера
        return classicInterfaceWrap.Get_Password(self.context)

    def Set_Password(self, value): # Устанавливает значение свойства #Password
        classicInterfaceWrap.Set_Password(self.context, value)

    def Get_PortNumber(self): # Номер порта
        return classicInterfaceWrap.Get_PortNumber(self.context)

    def Set_PortNumber(self, value): # Устанавливает значение свойства #PortNumber
        classicInterfaceWrap.Set_PortNumber(self.context, value)

    def Get_Price(self): # Цена
        return classicInterfaceWrap.Get_Price(self.context)

    def Set_Price(self, value): # Устанавливает значение свойства #Price
        classicInterfaceWrap.Set_Price(self.context, value)

    def Get_Quantity(self): # Количество
        return classicInterfaceWrap.Get_Quantity(self.context)

    def Set_Quantity(self, value): # Устанавливает значение свойства #Quantity
        classicInterfaceWrap.Set_Quantity(self.context, value)

    def Get_QuantityOfOperations(self): # Количество операций
        return classicInterfaceWrap.Get_QuantityOfOperations(self.context)

    def Get_RegisterNumber(self): # Номер регистра
        return classicInterfaceWrap.Get_RegisterNumber(self.context)

    def Set_RegisterNumber(self, value): # Устанавливает значение свойства #RegisterNumber
        classicInterfaceWrap.Set_RegisterNumber(self.context, value)

    def Get_RegistrationNumber(self): # Количество перерегистраций
        return classicInterfaceWrap.Get_RegistrationNumber(self.context)

    def Set_RegistrationNumber(self, value): # Устанавливает значение свойства #RegistrationNumber
        classicInterfaceWrap.Set_RegistrationNumber(self.context, value)

    def Get_ReportType(self): # Тип отчёта
        return classicInterfaceWrap.Get_ReportType(self.context)

    def Set_ReportType(self, value): # Устанавливает значение свойства #ReportType
        classicInterfaceWrap.Set_ReportType(self.context, value)

    def Get_ResultCode(self): # Код ошибки
        return classicInterfaceWrap.Get_ResultCode(self.context)

    def Get_ResultCodeDescription(self): # Описание кода ошибки
        resultLen = classicInterfaceWrap.Get_ResultCodeDescription(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ResultCodeDescription(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_RNM(self): # РНМ
        resultLen = classicInterfaceWrap.Get_RNM(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_RNM(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_RNM(self, value): # Устанавливает значение свойства #RNM
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_RNM(self.context, valueBuff, len(valueBuff))

    def Get_RowNumber(self): # Номер ряда
        return classicInterfaceWrap.Get_RowNumber(self.context)

    def Set_RowNumber(self, value): # Устанавливает значение свойства #RowNumber
        classicInterfaceWrap.Set_RowNumber(self.context, value)

    def Get_RunningPeriod(self): # Период прогона
        return classicInterfaceWrap.Get_RunningPeriod(self.context)

    def Set_RunningPeriod(self, value): # Устанавливает значение свойства #RunningPeriod
        classicInterfaceWrap.Set_RunningPeriod(self.context, value)

    def Get_SerialNumber(self): # Заводской номер
        resultLen = classicInterfaceWrap.Get_SerialNumber(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_SerialNumber(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_SerialNumber(self, value): # Устанавливает значение свойства #SerialNumber
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_SerialNumber(self.context, valueBuff, len(valueBuff))

    def Get_SessionNumber(self): # Номер смены
        return classicInterfaceWrap.Get_SessionNumber(self.context)

    def Set_SessionNumber(self, value): # Устанавливает значение свойства #SessionNumber
        classicInterfaceWrap.Set_SessionNumber(self.context, value)

    def Get_StringForPrinting(self): # Строка для печати
        resultLen = classicInterfaceWrap.Get_StringForPrinting(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_StringForPrinting(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_StringForPrinting(self, value): # Устанавливает значение свойства #StringForPrinting
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_StringForPrinting(self.context, valueBuff, len(valueBuff))

    def Get_StringQuantity(self): # Количество строк
        return classicInterfaceWrap.Get_StringQuantity(self.context)

    def Set_StringQuantity(self, value): # Устанавливает значение свойства #StringQuantity
        classicInterfaceWrap.Set_StringQuantity(self.context, value)

    def Get_Summ1(self): # Сумма1
        return classicInterfaceWrap.Get_Summ1(self.context)

    def Set_Summ1(self, value): # Устанавливает значение свойства #Summ1
        classicInterfaceWrap.Set_Summ1(self.context, value)

    def Get_Summ2(self): # Сумма2
        return classicInterfaceWrap.Get_Summ2(self.context)

    def Set_Summ2(self, value): # Устанавливает значение свойства #Summ2
        classicInterfaceWrap.Set_Summ2(self.context, value)

    def Get_Summ3(self): # Сумма3
        return classicInterfaceWrap.Get_Summ3(self.context)

    def Set_Summ3(self, value): # Устанавливает значение свойства #Summ3
        classicInterfaceWrap.Set_Summ3(self.context, value)

    def Get_Summ4(self): # Сумма4
        return classicInterfaceWrap.Get_Summ4(self.context)

    def Set_Summ4(self, value): # Устанавливает значение свойства #Summ4
        classicInterfaceWrap.Set_Summ4(self.context, value)

    def Get_TableName(self): # Название таблицы
        resultLen = classicInterfaceWrap.Get_TableName(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_TableName(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_TableNumber(self): # Номер таблицы
        return classicInterfaceWrap.Get_TableNumber(self.context)

    def Set_TableNumber(self, value): # Устанавливает значение свойства #TableNumber
        classicInterfaceWrap.Set_TableNumber(self.context, value)

    def Get_Tax1(self): # Налог1
        return classicInterfaceWrap.Get_Tax1(self.context)

    def Set_Tax1(self, value): # Устанавливает значение свойства #Tax1
        classicInterfaceWrap.Set_Tax1(self.context, value)

    def Get_Tax2(self): # Налог2
        return classicInterfaceWrap.Get_Tax2(self.context)

    def Set_Tax2(self, value): # Устанавливает значение свойства #Tax2
        classicInterfaceWrap.Set_Tax2(self.context, value)

    def Get_Tax3(self): # Налог3
        return classicInterfaceWrap.Get_Tax3(self.context)

    def Set_Tax3(self, value): # Устанавливает значение свойства #Tax3
        classicInterfaceWrap.Set_Tax3(self.context, value)

    def Get_Tax4(self): # Налог4
        return classicInterfaceWrap.Get_Tax4(self.context)

    def Set_Tax4(self, value): # Устанавливает значение свойства #Tax4
        classicInterfaceWrap.Set_Tax4(self.context, value)

    def Get_Time(self): # Время
        return unwrapDateTime(classicInterfaceWrap.Get_Time(self.context))

    def Set_Time(self, value): # Устанавливает значение свойства #Time
        classicInterfaceWrap.Set_Time(self.context, wrapDateTime(value))

    def Get_Timeout(self): # Тайм-аут приема байта
        return classicInterfaceWrap.Get_Timeout(self.context)

    def Set_Timeout(self, value): # Устанавливает значение свойства #Timeout
        classicInterfaceWrap.Set_Timeout(self.context, value)

    def Get_TimeStr(self): # Время cтрока
        resultLen = classicInterfaceWrap.Get_TimeStr(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_TimeStr(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_TimeStr(self, value): # Устанавливает значение свойства #TimeStr
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_TimeStr(self.context, valueBuff, len(valueBuff))

    def Get_TransferBytes(self): # Посылаемые байты
        resultLen = classicInterfaceWrap.Get_TransferBytes(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_TransferBytes(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_TransferBytes(self, value): # Устанавливает значение свойства #TransferBytes
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_TransferBytes(self.context, valueBuff, len(valueBuff))

    def Get_TypeOfLastEntryFM(self): # Тип последней записи ФП
        return classicInterfaceWrap.Get_TypeOfLastEntryFM(self.context)

    def Get_TypeOfSumOfEntriesFM(self): # Тип суммы записей ФП
        return classicInterfaceWrap.Get_TypeOfSumOfEntriesFM(self.context)

    def Set_TypeOfSumOfEntriesFM(self, value): # Устанавливает значение свойства #TypeOfSumOfEntriesFM
        classicInterfaceWrap.Set_TypeOfSumOfEntriesFM(self.context, value)

    def Get_UCodePage(self): # Кодовая страница
        return classicInterfaceWrap.Get_UCodePage(self.context)

    def Get_UDescription(self): # Название устройства
        resultLen = classicInterfaceWrap.Get_UDescription(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_UDescription(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_UMajorProtocolVersion(self): # Версия протокола
        return classicInterfaceWrap.Get_UMajorProtocolVersion(self.context)

    def Get_UMajorType(self): # Тип устрйоства
        return classicInterfaceWrap.Get_UMajorType(self.context)

    def Get_UMinorProtocolVersion(self): # Подверсия протокола
        return classicInterfaceWrap.Get_UMinorProtocolVersion(self.context)

    def Get_UMinorType(self): # Подтип устройства
        return classicInterfaceWrap.Get_UMinorType(self.context)

    def Get_UModel(self): # Модель устройства
        return classicInterfaceWrap.Get_UModel(self.context)

    def Get_UseJournalRibbon(self): # Использовать ленту операционного журнала
        return classicInterfaceWrap.Get_UseJournalRibbon(self.context)

    def Set_UseJournalRibbon(self, value): # Устанавливает значение свойства #UseJournalRibbon
        classicInterfaceWrap.Set_UseJournalRibbon(self.context, value)

    def Get_UseReceiptRibbon(self): # Использовать чековую ленту
        return classicInterfaceWrap.Get_UseReceiptRibbon(self.context)

    def Set_UseReceiptRibbon(self, value): # Устанавливает значение свойства #UseReceiptRibbon
        classicInterfaceWrap.Set_UseReceiptRibbon(self.context, value)

    def Get_UseSlipDocument(self): # Использовать подкладной документ
        return classicInterfaceWrap.Get_UseSlipDocument(self.context)

    def Set_UseSlipDocument(self, value): # Устанавливает значение свойства #UseSlipDocument
        classicInterfaceWrap.Set_UseSlipDocument(self.context, value)

    def Get_ValueOfFieldInteger(self): # Значение поля целое
        return classicInterfaceWrap.Get_ValueOfFieldInteger(self.context)

    def Set_ValueOfFieldInteger(self, value): # Устанавливает значение свойства #ValueOfFieldInteger
        classicInterfaceWrap.Set_ValueOfFieldInteger(self.context, value)

    def Get_ValueOfFieldString(self): # Значение поля строка
        resultLen = classicInterfaceWrap.Get_ValueOfFieldString(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ValueOfFieldString(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_ValueOfFieldString(self, value): # Устанавливает значение свойства #ValueOfFieldString
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_ValueOfFieldString(self.context, valueBuff, len(valueBuff))

    def Get_FontType(self): # Тип шрифта
        return classicInterfaceWrap.Get_FontType(self.context)

    def Set_FontType(self, value): # Устанавливает значение свойства #FontType
        classicInterfaceWrap.Set_FontType(self.context, value)

    def Get_EKLZResultCode(self): # Код ошибки ЭКЛЗ
        return classicInterfaceWrap.Get_EKLZResultCode(self.context)

    def Set_EKLZResultCode(self, value): # Устанавливает значение свойства #EKLZResultCode
        classicInterfaceWrap.Set_EKLZResultCode(self.context, value)

    def Get_FMResultCode(self): # Код ошибки ФП
        return classicInterfaceWrap.Get_FMResultCode(self.context)

    def Get_PowerSourceVoltage(self): # Напряжение источника питания
        return classicInterfaceWrap.Get_PowerSourceVoltage(self.context)

    def Get_ECRModeStatus(self): # Статус режима
        return classicInterfaceWrap.Get_ECRModeStatus(self.context)

    def Get_ComputerName(self): # Имя компьютера
        resultLen = classicInterfaceWrap.Get_ComputerName(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ComputerName(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_ComputerName(self, value): # Устанавливает значение свойства #ComputerName
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_ComputerName(self.context, valueBuff, len(valueBuff))

    def Get_PrintWidth(self): # Ширина печати
        return classicInterfaceWrap.Get_PrintWidth(self.context)

    def Get_CharWidth(self): # Ширина символа
        return classicInterfaceWrap.Get_CharWidth(self.context)

    def Get_CharHeight(self): # Высота символа
        return classicInterfaceWrap.Get_CharHeight(self.context)

    def Get_FontCount(self): # Количество шрифтов
        return classicInterfaceWrap.Get_FontCount(self.context)

    def Get_ConnectionType(self): # Тип подключения к устройству
        return classicInterfaceWrap.Get_ConnectionType(self.context)

    def Set_ConnectionType(self, value): # Устанавливает значение свойства #ConnectionType
        classicInterfaceWrap.Set_ConnectionType(self.context, value)

    def Get_TCPPort(self): # Порт TCP
        return classicInterfaceWrap.Get_TCPPort(self.context)

    def Set_TCPPort(self, value): # Устанавливает значение свойства #TCPPort
        classicInterfaceWrap.Set_TCPPort(self.context, value)

    def Get_IPAddress(self): # IP адрес
        resultLen = classicInterfaceWrap.Get_IPAddress(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_IPAddress(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_IPAddress(self, value): # Устанавливает значение свойства #IPAddress
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_IPAddress(self.context, valueBuff, len(valueBuff))

    def Get_UseIPAddress(self): # Использовать IP адрес
        return classicInterfaceWrap.Get_UseIPAddress(self.context)

    def Set_UseIPAddress(self, value): # Устанавливает значение свойства #UseIPAddress
        classicInterfaceWrap.Set_UseIPAddress(self.context, value)

    def Get_SysAdminPassword(self): # Пароль системного администратора
        return classicInterfaceWrap.Get_SysAdminPassword(self.context)

    def Set_SysAdminPassword(self, value): # Устанавливает значение свойства #SysAdminPassword
        classicInterfaceWrap.Set_SysAdminPassword(self.context, value)

    def Get_OperationType(self): # Тип операции
        return classicInterfaceWrap.Get_OperationType(self.context)

    def Set_OperationType(self, value): # Устанавливает значение свойства #OperationType
        classicInterfaceWrap.Set_OperationType(self.context, value)

    def Get_PresenterIn(self): # Вход накопителя
        return classicInterfaceWrap.Get_PresenterIn(self.context)

    def Get_PresenterOut(self): # Выход накопителя
        return classicInterfaceWrap.Get_PresenterOut(self.context)

    def Get_SCPassword(self): # Пароль ЦТО
        return classicInterfaceWrap.Get_SCPassword(self.context)

    def Set_SCPassword(self, value): # Устанавливает значение свойства #SCPassword
        classicInterfaceWrap.Set_SCPassword(self.context, value)

    def Get_NewSCPassword(self): # Новый пароль ЦТО
        return classicInterfaceWrap.Get_NewSCPassword(self.context)

    def Set_NewSCPassword(self, value): # Устанавливает значение свойства #NewSCPassword
        classicInterfaceWrap.Set_NewSCPassword(self.context, value)

    def Get_BarcodeAlignment(self): # Выравнивание штрих-кода
        return classicInterfaceWrap.Get_BarcodeAlignment(self.context)

    def Set_BarcodeAlignment(self, value): # Устанавливает значение свойства #BarcodeAlignment
        classicInterfaceWrap.Set_BarcodeAlignment(self.context, value)

    def Get_FinishDocumentMode(self): # Режим завершения документа
        return classicInterfaceWrap.Get_FinishDocumentMode(self.context)

    def Set_FinishDocumentMode(self, value): # Устанавливает значение свойства #FinishDocumentMode
        classicInterfaceWrap.Set_FinishDocumentMode(self.context, value)

    def Get_PrintBarcodeText(self): # Печать текста штрих-кода
        return classicInterfaceWrap.Get_PrintBarcodeText(self.context)

    def Set_PrintBarcodeText(self, value): # Устанавливает значение свойства #PrintBarcodeText
        classicInterfaceWrap.Set_PrintBarcodeText(self.context, value)

    def Get_FileName(self): # Имя файла
        resultLen = classicInterfaceWrap.Get_FileName(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_FileName(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_FileName(self, value): # Устанавливает значение свойства #FileName
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_FileName(self.context, valueBuff, len(valueBuff))

    def Get_DriverMajorVersion(self): # Номер версии драйвера
        return classicInterfaceWrap.Get_DriverMajorVersion(self.context)

    def Get_DriverMinorVersion(self): # Номер подверсии драйвера
        return classicInterfaceWrap.Get_DriverMinorVersion(self.context)

    def Get_DriverRelease(self): # Номер релиза драйвера
        return classicInterfaceWrap.Get_DriverRelease(self.context)

    def Get_DriverBuild(self): # Номер сборки драйвера
        return classicInterfaceWrap.Get_DriverBuild(self.context)

    def Get_BlockType(self): # Тип блока
        return classicInterfaceWrap.Get_BlockType(self.context)

    def Set_BlockType(self, value): # Устанавливает значение свойства #BlockType
        classicInterfaceWrap.Set_BlockType(self.context, value)

    def Get_BlockNumber(self): # Номер блока
        return classicInterfaceWrap.Get_BlockNumber(self.context)

    def Set_BlockNumber(self, value): # Устанавливает значение свойства #BlockNumber
        classicInterfaceWrap.Set_BlockNumber(self.context, value)

    def Get_BlockDataHex(self): # Блок данных для загрузки, в виде HEX строки
        resultLen = classicInterfaceWrap.Get_BlockDataHex(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_BlockDataHex(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_BlockDataHex(self, value): # Устанавливает значение свойства #BlockDataHex
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_BlockDataHex(self.context, valueBuff, len(valueBuff))

    def Get_BarcodeType(self): # Тип штрих-кода
        return classicInterfaceWrap.Get_BarcodeType(self.context)

    def Set_BarcodeType(self, value): # Устанавливает значение свойства #BarcodeType
        classicInterfaceWrap.Set_BarcodeType(self.context, value)

    def Get_BarWidth(self): # Ширина вертикальной линии в штрих-коде
        return classicInterfaceWrap.Get_BarWidth(self.context)

    def Set_BarWidth(self, value): # Устанавливает значение свойства #BarWidth
        classicInterfaceWrap.Set_BarWidth(self.context, value)

    def Get_CapGetShortECRStatus(self): # Поддерживается короткий запрос состояния
        return classicInterfaceWrap.Get_CapGetShortECRStatus(self.context)

    def Get_WaitForPrintingDelay(self): # Задержка ожидания печати
        return classicInterfaceWrap.Get_WaitForPrintingDelay(self.context)

    def Set_WaitForPrintingDelay(self, value): # Устанавливает значение свойства #WaitForPrintingDelay
        classicInterfaceWrap.Set_WaitForPrintingDelay(self.context, value)

    def Get_LineSwapBytes(self): # Переворачивать байты при печати линии
        return classicInterfaceWrap.Get_LineSwapBytes(self.context)

    def Set_LineSwapBytes(self, value): # Устанавливает значение свойства #LineSwapBytes
        classicInterfaceWrap.Set_LineSwapBytes(self.context, value)

    def Get_LineDataHex(self): # Графическая информация HEX
        resultLen = classicInterfaceWrap.Get_LineDataHex(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_LineDataHex(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_LineDataHex(self, value): # Устанавливает значение свойства #LineDataHex
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_LineDataHex(self.context, valueBuff, len(valueBuff))

    def Get_CenterImage(self): # Центрировать картинку
        return classicInterfaceWrap.Get_CenterImage(self.context)

    def Set_CenterImage(self, value): # Устанавливает значение свойства #CenterImage
        classicInterfaceWrap.Set_CenterImage(self.context, value)

    def Get_ShowProgress(self): # Показывать прогресс
        return classicInterfaceWrap.Get_ShowProgress(self.context)

    def Set_ShowProgress(self, value): # Устанавливает значение свойства #ShowProgress
        classicInterfaceWrap.Set_ShowProgress(self.context, value)

    def Get_ModelParamValue(self): # Значение параметра модели
        return classicInterfaceWrap.Get_ModelParamValue(self.context)

    def Get_ModelParamNumber(self): # Номер параметра модели
        return classicInterfaceWrap.Get_ModelParamNumber(self.context)

    def Set_ModelParamNumber(self, value): # Устанавливает значение свойства #ModelParamNumber
        classicInterfaceWrap.Set_ModelParamNumber(self.context, value)

    def Get_Connected(self): # Прочитать/Установить состояние соединения
        return classicInterfaceWrap.Get_Connected(self.context)

    def Get_ConnectionTimeout(self): # Таймаут подключения
        return classicInterfaceWrap.Get_ConnectionTimeout(self.context)

    def Set_ConnectionTimeout(self, value): # Устанавливает значение свойства #ConnectionTimeout
        classicInterfaceWrap.Set_ConnectionTimeout(self.context, value)

    def Get_ModelParamDescription(self): # Описание параметра модели
        resultLen = classicInterfaceWrap.Get_ModelParamDescription(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ModelParamDescription(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_DriverVersion(self): # Версия драйвера
        resultLen = classicInterfaceWrap.Get_DriverVersion(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_DriverVersion(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_BarcodeDataLength(self): # Длина данных штрих-кода
        return classicInterfaceWrap.Get_BarcodeDataLength(self.context)

    def Get_BarcodeParameter1(self): # Параметр штрих-кода 1
        return classicInterfaceWrap.Get_BarcodeParameter1(self.context)

    def Get_BarcodeParameter2(self): # Параметр штрих-кода 2
        return classicInterfaceWrap.Get_BarcodeParameter2(self.context)

    def Get_BarcodeParameter3(self): # Параметр штрих-кода 3
        return classicInterfaceWrap.Get_BarcodeParameter3(self.context)

    def Get_BarcodeParameter4(self): # Параметр штрих-кода 4
        return classicInterfaceWrap.Get_BarcodeParameter4(self.context)

    def Get_BarcodeParameter5(self): # Параметр штрих-кода 5
        return classicInterfaceWrap.Get_BarcodeParameter5(self.context)

    def Set_BarcodeParameter1(self, value): # Устанавливает значение свойства #BarcodeParameter1
        classicInterfaceWrap.Set_BarcodeParameter1(self.context, value)

    def Set_BarcodeParameter2(self, value): # Устанавливает значение свойства #BarcodeParameter2
        classicInterfaceWrap.Set_BarcodeParameter2(self.context, value)

    def Set_BarcodeParameter3(self, value): # Устанавливает значение свойства #BarcodeParameter3
        classicInterfaceWrap.Set_BarcodeParameter3(self.context, value)

    def Set_BarcodeParameter4(self, value): # Устанавливает значение свойства #BarcodeParameter4
        classicInterfaceWrap.Set_BarcodeParameter4(self.context, value)

    def Set_BarcodeParameter5(self, value): # Устанавливает значение свойства #BarcodeParameter5
        classicInterfaceWrap.Set_BarcodeParameter5(self.context, value)

    def Get_BarcodeStartBlockNumber(self): # Номер начального блока данных
        return classicInterfaceWrap.Get_BarcodeStartBlockNumber(self.context)

    def Set_BarcodeStartBlockNumber(self, value): # Устанавливает значение свойства #BarcodeStartBlockNumber
        classicInterfaceWrap.Set_BarcodeStartBlockNumber(self.context, value)

    def Get_CarryStrings(self): # Переносить строки при печати
        return classicInterfaceWrap.Get_CarryStrings(self.context)

    def Get_DelayedPrint(self): # Отложенная печать
        return classicInterfaceWrap.Get_DelayedPrint(self.context)

    def Set_CarryStrings(self, value): # Устанавливает значение свойства #CarryStrings
        classicInterfaceWrap.Set_CarryStrings(self.context, value)

    def Set_DelayedPrint(self, value): # Устанавливает значение свойства #DelayedPrint
        classicInterfaceWrap.Set_DelayedPrint(self.context, value)

    def Get_ErrorCode(self): # Код ошибки
        return classicInterfaceWrap.Get_ErrorCode(self.context)

    def Set_ErrorCode(self, value): # Устанавливает значение свойства #ErrorCode
        classicInterfaceWrap.Set_ErrorCode(self.context, value)

    def Get_ErrorDescription(self): # Описание ошибки
        resultLen = classicInterfaceWrap.Get_ErrorDescription(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ErrorDescription(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_ReconnectPort(self): # Переподключать соединение в случае отсутствия связи
        return classicInterfaceWrap.Get_ReconnectPort(self.context)

    def Get_SwapBytesMode(self): # Режим переворачивания байта
        return classicInterfaceWrap.Get_SwapBytesMode(self.context)

    def Set_SwapBytesMode(self, value): # Устанавливает значение свойства #SwapBytesMode
        classicInterfaceWrap.Set_SwapBytesMode(self.context, value)

    def Get_BarcodeHex(self): # Строка с двоичными данными штрих-кода
        resultLen = classicInterfaceWrap.Get_BarcodeHex(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_BarcodeHex(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_BarcodeHex(self, value): # Устанавливает значение свойства #BarcodeHex
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_BarcodeHex(self.context, valueBuff, len(valueBuff))

    def Get_ProtocolType(self): # Тип протокола
        return classicInterfaceWrap.Get_ProtocolType(self.context)

    def Set_ProtocolType(self, value): # Устанавливает значение свойства #ProtocolType
        classicInterfaceWrap.Set_ProtocolType(self.context, value)

    def Get_Summ5(self): # Сумма5
        return classicInterfaceWrap.Get_Summ5(self.context)

    def Set_Summ5(self, value): # Устанавливает значение свойства #Summ5
        classicInterfaceWrap.Set_Summ5(self.context, value)

    def Get_Summ6(self): # Сумма6
        return classicInterfaceWrap.Get_Summ6(self.context)

    def Set_Summ6(self, value): # Устанавливает значение свойства #Summ6
        classicInterfaceWrap.Set_Summ6(self.context, value)

    def Get_Summ7(self): # Сумма7
        return classicInterfaceWrap.Get_Summ7(self.context)

    def Set_Summ7(self, value): # Устанавливает значение свойства #Summ7
        classicInterfaceWrap.Set_Summ7(self.context, value)

    def Get_Summ8(self): # Сумма8
        return classicInterfaceWrap.Get_Summ8(self.context)

    def Set_Summ8(self, value): # Устанавливает значение свойства #Summ8
        classicInterfaceWrap.Set_Summ8(self.context, value)

    def Get_Summ9(self): # Сумма9
        return classicInterfaceWrap.Get_Summ9(self.context)

    def Set_Summ9(self, value): # Устанавливает значение свойства #Summ9
        classicInterfaceWrap.Set_Summ9(self.context, value)

    def Get_Summ10(self): # Сумма10
        return classicInterfaceWrap.Get_Summ10(self.context)

    def Set_Summ10(self, value): # Устанавливает значение свойства #Summ10
        classicInterfaceWrap.Set_Summ10(self.context, value)

    def Get_Summ11(self): # Сумма11
        return classicInterfaceWrap.Get_Summ11(self.context)

    def Set_Summ11(self, value): # Устанавливает значение свойства #Summ11
        classicInterfaceWrap.Set_Summ11(self.context, value)

    def Get_Summ12(self): # Сумма12
        return classicInterfaceWrap.Get_Summ12(self.context)

    def Set_Summ12(self, value): # Устанавливает значение свойства #Summ12
        classicInterfaceWrap.Set_Summ12(self.context, value)

    def Get_Summ13(self): # Сумма13
        return classicInterfaceWrap.Get_Summ13(self.context)

    def Set_Summ13(self, value): # Устанавливает значение свойства #Summ13
        classicInterfaceWrap.Set_Summ13(self.context, value)

    def Get_Summ14(self): # Сумма14
        return classicInterfaceWrap.Get_Summ14(self.context)

    def Set_Summ14(self, value): # Устанавливает значение свойства #Summ14
        classicInterfaceWrap.Set_Summ14(self.context, value)

    def Get_Summ15(self): # Сумма15
        return classicInterfaceWrap.Get_Summ15(self.context)

    def Set_Summ15(self, value): # Устанавливает значение свойства #Summ15
        classicInterfaceWrap.Set_Summ15(self.context, value)

    def Get_Summ16(self): # Сумма16
        return classicInterfaceWrap.Get_Summ16(self.context)

    def Set_Summ16(self, value): # Устанавливает значение свойства #Summ16
        classicInterfaceWrap.Set_Summ16(self.context, value)

    def Get_NameCashRegEx(self): # Имя расширенного денежного регистра
        resultLen = classicInterfaceWrap.Get_NameCashRegEx(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_NameCashRegEx(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_RequestType(self): # Тип запроса
        return classicInterfaceWrap.Get_RequestType(self.context)

    def Set_RequestType(self, value): # Устанавливает значение свойства #RequestType
        classicInterfaceWrap.Set_RequestType(self.context, value)

    def Get_HorizScale(self): # Горизонтальное масштабирование
        return classicInterfaceWrap.Get_HorizScale(self.context)

    def Set_HorizScale(self, value): # Устанавливает значение свойства #HorizScale
        classicInterfaceWrap.Set_HorizScale(self.context, value)

    def Get_VertScale(self): # Вертикальное масштабирование
        return classicInterfaceWrap.Get_VertScale(self.context)

    def Set_VertScale(self, value): # Устанавливает значение свойства #VertScale
        classicInterfaceWrap.Set_VertScale(self.context, value)

    def Get_GraphBufferType(self): # Тип графического буфера
        return classicInterfaceWrap.Get_GraphBufferType(self.context)

    def Set_GraphBufferType(self, value): # Устанавливает значение свойства #GraphBufferType
        classicInterfaceWrap.Set_GraphBufferType(self.context, value)

    def Get_LineLength(self): # Длина линии
        return classicInterfaceWrap.Get_LineLength(self.context)

    def Set_LineLength(self, value): # Устанавливает значение свойства #LineLength
        classicInterfaceWrap.Set_LineLength(self.context, value)

    def Get_FNCurrentDocument(self): # Текущий документ ФН
        return classicInterfaceWrap.Get_FNCurrentDocument(self.context)

    def Set_FNCurrentDocument(self, value): # Устанавливает значение свойства #FNCurrentDocument
        classicInterfaceWrap.Set_FNCurrentDocument(self.context, value)

    def Get_FNDocumentData(self): # Данные документа ФН
        return classicInterfaceWrap.Get_FNDocumentData(self.context)

    def Set_FNDocumentData(self, value): # Устанавливает значение свойства #FNDocumentData
        classicInterfaceWrap.Set_FNDocumentData(self.context, value)

    def Get_FNLifeState(self): # Состояние жизни ФН
        return classicInterfaceWrap.Get_FNLifeState(self.context)

    def Set_FNLifeState(self, value): # Устанавливает значение свойства #FNLifeState
        classicInterfaceWrap.Set_FNLifeState(self.context, value)

    def Get_FNSessionState(self): # Состояние смены ФН
        return classicInterfaceWrap.Get_FNSessionState(self.context)

    def Set_FNSessionState(self, value): # Устанавливает значение свойства #FNSessionState
        classicInterfaceWrap.Set_FNSessionState(self.context, value)

    def Get_FNSoftVersion(self): # ФН версия
        resultLen = classicInterfaceWrap.Get_FNSoftVersion(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_FNSoftVersion(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_FNSoftVersion(self, value): # Устанавливает значение свойства #FNSoftVersion
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_FNSoftVersion(self.context, valueBuff, len(valueBuff))

    def Get_FNSoftType(self): # Тип программного обеспечения ФН
        return classicInterfaceWrap.Get_FNSoftType(self.context)

    def Get_FNWarningFlags(self): # Флаги предупреждения ФН
        return classicInterfaceWrap.Get_FNWarningFlags(self.context)

    def Set_FNWarningFlags(self, value): # Устанавливает значение свойства #FNWarningFlags
        classicInterfaceWrap.Set_FNWarningFlags(self.context, value)

    def Get_FiscalSign(self): # Фискальный признак
        return classicInterfaceWrap.Get_FiscalSign(self.context)

    def Set_FiscalSign(self, value): # Устанавливает значение свойства #FiscalSign
        classicInterfaceWrap.Set_FiscalSign(self.context, value)

    def Get_FiscalSignAsString(self): # Фискальный признак документа в виде строки
        resultLen = classicInterfaceWrap.Get_FiscalSignAsString(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_FiscalSignAsString(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_KKTRegistrationNumber(self): # Регистрационный номер ККТ
        resultLen = classicInterfaceWrap.Get_KKTRegistrationNumber(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_KKTRegistrationNumber(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_KKTRegistrationNumber(self, value): # Устанавливает значение свойства #KKTRegistrationNumber
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_KKTRegistrationNumber(self.context, valueBuff, len(valueBuff))

    def Get_TaxType(self): # Код налогообложения
        return classicInterfaceWrap.Get_TaxType(self.context)

    def Set_TaxType(self, value): # Устанавливает значение свойства #TaxType
        classicInterfaceWrap.Set_TaxType(self.context, value)

    def Get_WorkMode(self): # Режим работы
        return classicInterfaceWrap.Get_WorkMode(self.context)

    def Set_WorkMode(self, value): # Устанавливает значение свойства #WorkMode
        classicInterfaceWrap.Set_WorkMode(self.context, value)

    def Get_DocumentType(self): # Тип документа ФН
        return classicInterfaceWrap.Get_DocumentType(self.context)

    def Set_DocumentType(self, value): # Устанавливает значение свойства #DocumentType
        classicInterfaceWrap.Set_DocumentType(self.context, value)

    def Get_OFDTicketReceived(self): # Получена ли квитанция из ОФД
        return classicInterfaceWrap.Get_OFDTicketReceived(self.context)

    def Set_OFDTicketReceived(self, value): # Устанавливает значение свойства #OFDTicketReceived
        classicInterfaceWrap.Set_OFDTicketReceived(self.context, value)

    def Get_TLVData(self): # Данные TLV
        resultLen = classicInterfaceWrap.Get_TLVData(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_TLVData(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen)

    def Set_TLVData(self, value): # Устанавливает значение свойства #TLVData
        classicInterfaceWrap.Set_TLVData(self.context, value, len(value))

    def Get_DataBlockSize(self): # Размер блока данных
        return classicInterfaceWrap.Get_DataBlockSize(self.context)

    def Set_DataBlockSize(self, value): # Устанавливает значение свойства #DataBlockSize
        classicInterfaceWrap.Set_DataBlockSize(self.context, value)

    def Get_DataLength(self): # Длина данных
        return classicInterfaceWrap.Get_DataLength(self.context)

    def Set_DataLength(self, value): # Устанавливает значение свойства #DataLength
        classicInterfaceWrap.Set_DataLength(self.context, value)

    def Get_OFDPort(self): # Порт ОФД
        return classicInterfaceWrap.Get_OFDPort(self.context)

    def Set_OFDPort(self, value): # Устанавливает значение свойства #OFDPort
        classicInterfaceWrap.Set_OFDPort(self.context, value)

    def Get_OFDServer(self): # Адрес сервера ОФД
        resultLen = classicInterfaceWrap.Get_OFDServer(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_OFDServer(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_OFDServer(self, value): # Устанавливает значение свойства #OFDServer
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_OFDServer(self.context, valueBuff, len(valueBuff))

    def Get_OFDPollPeriod(self): # Пауза между сессиями обмена с ОФД
        return classicInterfaceWrap.Get_OFDPollPeriod(self.context)

    def Set_OFDPollPeriod(self, value): # Устанавливает значение свойства #OFDPollPeriod
        classicInterfaceWrap.Set_OFDPollPeriod(self.context, value)

    def Get_DocumentCount(self): # Количество документов
        return classicInterfaceWrap.Get_DocumentCount(self.context)

    def Set_DocumentCount(self, value): # Устанавливает значение свойства #DocumentCount
        classicInterfaceWrap.Set_DocumentCount(self.context, value)

    def Get_ReceiptNumber(self): # Номер чека
        return classicInterfaceWrap.Get_ReceiptNumber(self.context)

    def Set_ReceiptNumber(self, value): # Устанавливает значение свойства #ReceiptNumber
        classicInterfaceWrap.Set_ReceiptNumber(self.context, value)

    def Get_InfoExchangeStatus(self): # Статус информационного обмена
        return classicInterfaceWrap.Get_InfoExchangeStatus(self.context)

    def Set_InfoExchangeStatus(self, value): # Устанавливает значение свойства #InfoExchangeStatus
        classicInterfaceWrap.Set_InfoExchangeStatus(self.context, value)

    def Get_MessageState(self): # Состояние сообщения
        return classicInterfaceWrap.Get_MessageState(self.context)

    def Set_MessageState(self, value): # Устанавливает значение свойства #MessageState
        classicInterfaceWrap.Set_MessageState(self.context, value)

    def Get_MessageCount(self): # Количество сообщений
        return classicInterfaceWrap.Get_MessageCount(self.context)

    def Set_MessageCount(self, value): # Устанавливает значение свойства #MessageCount
        classicInterfaceWrap.Set_MessageCount(self.context, value)

    def Get_MessageNumber(self): # Номер сообщения
        return classicInterfaceWrap.Get_MessageNumber(self.context)

    def Set_MessageNumber(self, value): # Устанавливает значение свойства #MessageNumber
        classicInterfaceWrap.Set_MessageNumber(self.context, value)

    def Get_ReportTypeInt(self): # Тип отчета
        return classicInterfaceWrap.Get_ReportTypeInt(self.context)

    def Set_ReportTypeInt(self, value): # Устанавливает значение свойства #ReportTypeInt
        classicInterfaceWrap.Set_ReportTypeInt(self.context, value)

    def Get_TaxValue(self): # Сумма налога
        return classicInterfaceWrap.Get_TaxValue(self.context)

    def Set_TaxValue(self, value): # Устанавливает значение свойства #TaxValue
        classicInterfaceWrap.Set_TaxValue(self.context, value)

    def Get_RegistrationReasonCode(self): # Код причины перерегистрации
        return classicInterfaceWrap.Get_RegistrationReasonCode(self.context)

    def Set_RegistrationReasonCode(self, value): # Устанавливает значение свойства #RegistrationReasonCode
        classicInterfaceWrap.Set_RegistrationReasonCode(self.context, value)

    def Get_CustomerEmail(self): # EmailПользователя
        resultLen = classicInterfaceWrap.Get_CustomerEmail(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_CustomerEmail(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_CustomerEmail(self, value): # Устанавливает значение свойства #CustomerEmail
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_CustomerEmail(self.context, valueBuff, len(valueBuff))

    def Get_Date2(self): # Дата2
        return unwrapDateTime(classicInterfaceWrap.Get_Date2(self.context))

    def Set_Date2(self, value): # Устанавливает значение свойства #Date2
        classicInterfaceWrap.Set_Date2(self.context, wrapDateTime(value))

    def Get_Time2(self): # Время2
        return unwrapDateTime(classicInterfaceWrap.Get_Time2(self.context))

    def Set_Time2(self, value): # Устанавливает значение свойства #Time2
        classicInterfaceWrap.Set_Time2(self.context, wrapDateTime(value))

    def Get_FiscalSignOFD(self): # Фискальный признак ОФД
        resultLen = classicInterfaceWrap.Get_FiscalSignOFD(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_FiscalSignOFD(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_FiscalSignOFD(self, value): # Устанавливает значение свойства #FiscalSignOFD
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_FiscalSignOFD(self.context, valueBuff, len(valueBuff))

    def Get_AutoOpenSession(self): # Автоматическое открытие смены, если закрыта
        return classicInterfaceWrap.Get_AutoOpenSession(self.context)

    def Set_AutoOpenSession(self, value): # Устанавливает значение свойства #AutoOpenSession
        classicInterfaceWrap.Set_AutoOpenSession(self.context, value)

    def Get_TagNumber(self): # Номер тега
        return classicInterfaceWrap.Get_TagNumber(self.context)

    def Set_TagNumber(self, value): # Устанавливает значение свойства #TagNumber
        classicInterfaceWrap.Set_TagNumber(self.context, value)

    def Get_TagType(self): # Тип тега
        return classicInterfaceWrap.Get_TagType(self.context)

    def Set_TagType(self, value): # Устанавливает значение свойства #TagType
        classicInterfaceWrap.Set_TagType(self.context, value)

    def Get_TagValueInt(self): # Значение целочисленного тега
        return classicInterfaceWrap.Get_TagValueInt(self.context)

    def Set_TagValueInt(self, value): # Устанавливает значение свойства #TagValueInt
        classicInterfaceWrap.Set_TagValueInt(self.context, value)

    def Get_TagValueStr(self): # Строковое значение тега
        resultLen = classicInterfaceWrap.Get_TagValueStr(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_TagValueStr(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_TagValueStr(self, value): # Устанавливает значение свойства #TagValueStr
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_TagValueStr(self.context, valueBuff, len(valueBuff))

    def Get_TagValueFVLN(self): # Значение тега с плавающей запятой
        return classicInterfaceWrap.Get_TagValueFVLN(self.context)

    def Set_TagValueFVLN(self, value): # Устанавливает значение свойства #TagValueFVLN
        classicInterfaceWrap.Set_TagValueFVLN(self.context, value)

    def Get_TagValueDateTime(self): # Значение тега с датой и временем
        return unwrapDateTime(classicInterfaceWrap.Get_TagValueDateTime(self.context))

    def Set_TagValueDateTime(self, value): # Устанавливает значение свойства #TagValueDateTime
        classicInterfaceWrap.Set_TagValueDateTime(self.context, wrapDateTime(value))

    def Get_TagValueBin(self): # Значение тега с бинарными данными
        resultLen = classicInterfaceWrap.Get_TagValueBin(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_TagValueBin(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_TagValueBin(self, value): # Устанавливает значение свойства #TagValueBin
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_TagValueBin(self.context, valueBuff, len(valueBuff))

    def Get_TagValueLength(self): # Количество байт длины значения тега
        return classicInterfaceWrap.Get_TagValueLength(self.context)

    def Set_TagValueLength(self, value): # Устанавливает значение свойства #TagValueLength
        classicInterfaceWrap.Set_TagValueLength(self.context, value)

    def Get_ShowTagNumber(self): # Выводить номер тэга
        return classicInterfaceWrap.Get_ShowTagNumber(self.context)

    def Set_ShowTagNumber(self, value): # Устанавливает значение свойства #ShowTagNumber
        classicInterfaceWrap.Set_ShowTagNumber(self.context, value)

    def Get_RoundingSumm(self): # Сумма округления
        return classicInterfaceWrap.Get_RoundingSumm(self.context)

    def Set_RoundingSumm(self, value): # Устанавливает значение свойства #RoundingSumm
        classicInterfaceWrap.Set_RoundingSumm(self.context, value)

    def Get_TaxValue1(self): # Значение налога 1
        return classicInterfaceWrap.Get_TaxValue1(self.context)

    def Set_TaxValue1(self, value): # Устанавливает значение свойства #TaxValue1
        classicInterfaceWrap.Set_TaxValue1(self.context, value)

    def Get_TaxValue2(self): # Значение налога 2
        return classicInterfaceWrap.Get_TaxValue2(self.context)

    def Set_TaxValue2(self, value): # Устанавливает значение свойства #TaxValue2
        classicInterfaceWrap.Set_TaxValue2(self.context, value)

    def Get_TaxValue3(self): # Значение налога 3
        return classicInterfaceWrap.Get_TaxValue3(self.context)

    def Set_TaxValue3(self, value): # Устанавливает значение свойства #TaxValue3
        classicInterfaceWrap.Set_TaxValue3(self.context, value)

    def Get_TaxValue4(self): # Значение налога 4
        return classicInterfaceWrap.Get_TaxValue4(self.context)

    def Set_TaxValue4(self, value): # Устанавливает значение свойства #TaxValue4
        classicInterfaceWrap.Set_TaxValue4(self.context, value)

    def Get_TaxValue5(self): # Значение налога 5
        return classicInterfaceWrap.Get_TaxValue5(self.context)

    def Set_TaxValue5(self, value): # Устанавливает значение свойства #TaxValue5
        classicInterfaceWrap.Set_TaxValue5(self.context, value)

    def Get_TaxValue6(self): # Значение налога 6
        return classicInterfaceWrap.Get_TaxValue6(self.context)

    def Set_TaxValue6(self, value): # Устанавливает значение свойства #TaxValue6
        classicInterfaceWrap.Set_TaxValue6(self.context, value)

    def Get_Summ1Enabled(self): # Сумма1 вкл
        return classicInterfaceWrap.Get_Summ1Enabled(self.context)

    def Set_Summ1Enabled(self, value): # Устанавливает значение свойства #Summ1Enabled
        classicInterfaceWrap.Set_Summ1Enabled(self.context, value)

    def Get_TaxValueEnabled(self): # Значение налога1 вкл
        return classicInterfaceWrap.Get_TaxValueEnabled(self.context)

    def Set_TaxValueEnabled(self, value): # Устанавливает значение свойства #TaxValueEnabled
        classicInterfaceWrap.Set_TaxValueEnabled(self.context, value)

    def Get_PaymentTypeSign(self): # Признак способа расчета
        return classicInterfaceWrap.Get_PaymentTypeSign(self.context)

    def Set_PaymentTypeSign(self, value): # Устанавливает значение свойства #PaymentTypeSign
        classicInterfaceWrap.Set_PaymentTypeSign(self.context, value)

    def Get_PaymentItemSign(self): # Признак предмета расчета
        return classicInterfaceWrap.Get_PaymentItemSign(self.context)

    def Set_PaymentItemSign(self, value): # Устанавливает значение свойства #PaymentItemSign
        classicInterfaceWrap.Set_PaymentItemSign(self.context, value)

    def Get_CalculationSign(self): # Признак расчета
        return classicInterfaceWrap.Get_CalculationSign(self.context)

    def Set_CalculationSign(self, value): # Устанавливает значение свойства #CalculationSign
        classicInterfaceWrap.Set_CalculationSign(self.context, value)

    def Get_CorrectionType(self): # Тип коррекции
        return classicInterfaceWrap.Get_CorrectionType(self.context)

    def Set_CorrectionType(self, value): # Устанавливает значение свойства #CorrectionType
        classicInterfaceWrap.Set_CorrectionType(self.context, value)

    def Get_AutoEoD(self): # Автоматичесий обмен с ОФД средствами драйвера
        return classicInterfaceWrap.Get_AutoEoD(self.context)

    def Set_AutoEoD(self, value): # Устанавливает значение свойства #AutoEoD
        classicInterfaceWrap.Set_AutoEoD(self.context, value)

    def Get_AutoOFDExchange(self): # дублирует свойство
        return classicInterfaceWrap.Get_AutoOFDExchange(self.context)

    def Set_AutoOFDExchange(self, value): # Устанавливает значение свойства #AutoOFDExchange
        classicInterfaceWrap.Set_AutoOFDExchange(self.context, value)

    def Get_EmailAddress(self): # Еmail отправителя
        resultLen = classicInterfaceWrap.Get_EmailAddress(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_EmailAddress(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_EmailAddress(self, value): # Устанавливает значение свойства #EmailAddress
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_EmailAddress(self.context, valueBuff, len(valueBuff))

    def Get_TagID(self): # Идентификатор STLV-тега
        return classicInterfaceWrap.Get_TagID(self.context)

    def Set_TagID(self, value): # Устанавливает значение свойства #TagID
        classicInterfaceWrap.Set_TagID(self.context, value)

    def Set_ConnectionURI(self, value): # URI для соединения с ККТ
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_ConnectionURI(self.context, valueBuff, len(valueBuff))

    def Get_ConnectionURI(self): # Возвращает значение свойства #ConnectionURI
        resultLen = classicInterfaceWrap.Get_ConnectionURI(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ConnectionURI(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_BlockData(self): # Блок данных для загрузки
        resultLen = classicInterfaceWrap.Get_BlockData(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_BlockData(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen)

    def Set_BlockData(self, value): # Устанавливает значение свойства #BlockData
        classicInterfaceWrap.Set_BlockData(self.context, value, len(value))

    def Get_WrapStrings(self): # Переносить строки
        return classicInterfaceWrap.Get_WrapStrings(self.context)

    def Set_WrapStrings(self, value): # Устанавливает значение свойства #WrapStrings
        classicInterfaceWrap.Set_WrapStrings(self.context, value)

    def Set_MarkingType(self, value): # Тип маркировки товара
        classicInterfaceWrap.Set_MarkingType(self.context, value)

    def Get_MarkingType(self): # Возвращает значение свойства #MarkingType
        return classicInterfaceWrap.Get_MarkingType(self.context)

    def Get_LoaderVersion(self): # Не печатать чек
        resultLen = classicInterfaceWrap.Get_LoaderVersion(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_LoaderVersion(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_WorkModeEx(self): # Расширенные признаки работы ККТ
        return classicInterfaceWrap.Get_WorkModeEx(self.context)

    def Set_WorkModeEx(self, value): # Устанавливает значение свойства #WorkModeEx
        classicInterfaceWrap.Set_WorkModeEx(self.context, value)

    def Get_INNOFD(self): # ИНН ОФД
        resultLen = classicInterfaceWrap.Get_INNOFD(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_INNOFD(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_INNOFD(self, value): # Устанавливает значение свойства #INNOFD
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_INNOFD(self.context, valueBuff, len(valueBuff))

    def Get_RegistrationReasonCodeEx(self): # Код причины изменения сведений о ККТ
        return classicInterfaceWrap.Get_RegistrationReasonCodeEx(self.context)

    def Set_RegistrationReasonCodeEx(self, value): # Устанавливает значение свойства #RegistrationReasonCodeEx
        classicInterfaceWrap.Set_RegistrationReasonCodeEx(self.context, value)

    def Get_SkipPrint(self): # Не печатать чек
        return classicInterfaceWrap.Get_SkipPrint(self.context)

    def Set_SkipPrint(self, value): # Устанавливает значение свойства #SkipPrint
        classicInterfaceWrap.Set_SkipPrint(self.context, value)

    def Get_DigitalSign(self): # Цифровая подпись лицензии
        resultLen = classicInterfaceWrap.Get_DigitalSign(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_DigitalSign(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_DigitalSign(self, sign): # Устанавливает значение свойства #DigitalSign
        signBuff = wrapString(sign)
        classicInterfaceWrap.Set_DigitalSign(self.context, signBuff, len(signBuff))

    def Get_DeviceFunctionNumber(self): # Номер функции устройства
        return classicInterfaceWrap.Get_DeviceFunctionNumber(self.context)

    def Set_DeviceFunctionNumber(self, value): # Устанавливает значение свойства #DeviceFunctionNumber
        classicInterfaceWrap.Set_DeviceFunctionNumber(self.context, value)

    def Get_ValueOfFunctionInteger(self): # Значение фунции устройства, в зависимости от свойства
        return classicInterfaceWrap.Get_ValueOfFunctionInteger(self.context)

    def Set_ValueOfFunctionInteger(self, value): # Устанавливает значение свойства #ValueOfFunctionInteger
        classicInterfaceWrap.Set_ValueOfFunctionInteger(self.context, value)

    def Get_ValueOfFunctionString(self): # Значение функции устройства строковое
        resultLen = classicInterfaceWrap.Get_ValueOfFunctionString(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_ValueOfFunctionString(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_ValueOfFunctionString(self, value): # Устанавливает значение свойства #ValueOfFunctionString
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_ValueOfFunctionString(self.context, valueBuff, len(valueBuff))

    def Get_EnableCashcoreMarkCompatibility(self): # Режим совместимости КЯ при печати признака маркировки
        return classicInterfaceWrap.Get_EnableCashcoreMarkCompatibility(self.context)

    def Set_EnableCashcoreMarkCompatibility(self, value): # Устанавливает значение свойства #EnableCashcoreMarkCompatibility
        classicInterfaceWrap.Set_EnableCashcoreMarkCompatibility(self.context, value)

    def Set_CheckItemLocalError(self, value): # Результат локальной проверки КМ
        classicInterfaceWrap.Set_CheckItemLocalError(self.context, value)

    def Get_CheckItemLocalError(self): # Возвращает значение свойства #CheckItemLocalError
        return classicInterfaceWrap.Get_CheckItemLocalError(self.context)

    def Set_MarkingTypeEx(self, value): # Расширенный тип маркировки товара
        classicInterfaceWrap.Set_MarkingTypeEx(self.context, value)

    def Get_MarkingTypeEx(self): # Возвращает значение свойства #MarkingTypeEx
        return classicInterfaceWrap.Get_MarkingTypeEx(self.context)

    def Set_MeasureUnit(self, value): # Мера количества
        classicInterfaceWrap.Set_MeasureUnit(self.context, value)

    def Get_MeasureUnit(self): # Возвращает значение свойства #MeasureUnit
        return classicInterfaceWrap.Get_MeasureUnit(self.context)

    def Set_DivisionalQuantity(self, value): # Дробное количество
        classicInterfaceWrap.Set_DivisionalQuantity(self.context, value)

    def Get_DivisionalQuantity(self): # Возвращает значение свойства #DivisionalQuantity
        return classicInterfaceWrap.Get_DivisionalQuantity(self.context)

    def Set_Numerator(self, value): # Числитель
        classicInterfaceWrap.Set_Numerator(self.context, value)

    def Get_Numerator(self): # Возвращает значение свойства #Numerator
        return classicInterfaceWrap.Get_Numerator(self.context)

    def Set_Denominator(self, value): # Знаменатель
        classicInterfaceWrap.Set_Denominator(self.context, value)

    def Get_Denominator(self): # Возвращает значение свойства #Denominator
        return classicInterfaceWrap.Get_Denominator(self.context)

    def Get_FreeMemorySize(self): # Размер свободной памяти
        return classicInterfaceWrap.Get_FreeMemorySize(self.context)

    def Set_FreeMemorySize(self, value): # Устанавливает значение свойства #FreeMemorySize
        classicInterfaceWrap.Set_FreeMemorySize(self.context, value)

    def Get_MCCheckStatus(self): # Состояние проверки КМ
        return classicInterfaceWrap.Get_MCCheckStatus(self.context)

    def Set_MCCheckStatus(self, value): # Устанавливает значение свойства #MCCheckStatus
        classicInterfaceWrap.Set_MCCheckStatus(self.context, value)

    def Get_MCNotificationStatus(self): # Состояние уведомления КМ
        return classicInterfaceWrap.Get_MCNotificationStatus(self.context)

    def Set_MCNotificationStatus(self, value): # Устанавливает значение свойства #MCNotificationStatus
        classicInterfaceWrap.Set_MCNotificationStatus(self.context, value)

    def Get_MCCommandFlags(self): # Флаги команд КМ
        return classicInterfaceWrap.Get_MCCommandFlags(self.context)

    def Set_MCCommandFlags(self, value): # Устанавливает значение свойства #MCCommandFlags
        classicInterfaceWrap.Set_MCCommandFlags(self.context, value)

    def Get_MCCheckResultSavedCount(self): # Количество КМ, результаты проверки которых, сохранены в ФН
        return classicInterfaceWrap.Get_MCCheckResultSavedCount(self.context)

    def Set_MCCheckResultSavedCount(self, value): # Устанавливает значение свойства #MCCheckResultSavedCount
        classicInterfaceWrap.Set_MCCheckResultSavedCount(self.context, value)

    def Get_MCRealizationCount(self): # Количество КМ, включенных в уведомление о реализации
        return classicInterfaceWrap.Get_MCRealizationCount(self.context)

    def Set_MCRealizationCount(self, value): # Устанавливает значение свойства #MCRealizationCount
        classicInterfaceWrap.Set_MCRealizationCount(self.context, value)

    def Get_MCStorageSize(self): # Заполнение области хранения маркированного товара
        return classicInterfaceWrap.Get_MCStorageSize(self.context)

    def Set_MCStorageSize(self, value): # Устанавливает значение свойства #MCStorageSize
        classicInterfaceWrap.Set_MCStorageSize(self.context, value)

    def Get_CheckSum(self): # Контрольная сумма
        return classicInterfaceWrap.Get_CheckSum(self.context)

    def Set_CheckSum(self, value): # Устанавливает значение свойства #CheckSum
        classicInterfaceWrap.Set_CheckSum(self.context, value)

    def Get_NotificationCount(self): # Количество уведомлений
        return classicInterfaceWrap.Get_NotificationCount(self.context)

    def Set_NotificationCount(self, value): # Устанавливает значение свойства #NotificationCount
        classicInterfaceWrap.Set_NotificationCount(self.context, value)

    def Get_NotificationNumber(self): # Номер уведомления
        return classicInterfaceWrap.Get_NotificationNumber(self.context)

    def Set_NotificationNumber(self, value): # Устанавливает значение свойства #NotificationNumber
        classicInterfaceWrap.Set_NotificationNumber(self.context, value)

    def Get_NotificationSize(self): # Размер уведомления
        return classicInterfaceWrap.Get_NotificationSize(self.context)

    def Set_NotificationSize(self, value): # Устанавливает значение свойства #NotificationSize
        classicInterfaceWrap.Set_NotificationSize(self.context, value)

    def Get_DataOffset(self): # Смещение данных
        return classicInterfaceWrap.Get_DataOffset(self.context)

    def Set_DataOffset(self, value): # Устанавливает значение свойства #DataOffset
        classicInterfaceWrap.Set_DataOffset(self.context, value)

    def Set_MarkingType2(self, value): # Тип маркировки товара 2(Распознанный тип КМ Тег 2100)
        classicInterfaceWrap.Set_MarkingType2(self.context, value)

    def Get_MarkingType2(self): # Возвращает значение свойства #MarkingType2
        return classicInterfaceWrap.Get_MarkingType2(self.context)

    def Get_RandomSequence(self): # Прочитать случайную последовательность из ФН
        resultLen = classicInterfaceWrap.Get_RandomSequence(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_RandomSequence(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen)

    def Set_RandomSequence(self, value): # Устанавливает значение свойства #RandomSequence
        classicInterfaceWrap.Set_RandomSequence(self.context, value, len(value))

    def Get_RandomSequenceHex(self): # Прочитать случайную последовательность из ФН
        resultLen = classicInterfaceWrap.Get_RandomSequenceHex(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_RandomSequenceHex(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_RandomSequenceHex(self, value): # Устанавливает значение свойства #RandomSequenceHex
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_RandomSequenceHex(self.context, valueBuff, len(valueBuff))

    def Get_AuthData(self): # Данные для авторизации
        resultLen = classicInterfaceWrap.Get_AuthData(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_AuthData(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen)

    def Set_AuthData(self, value): # Устанавливает значение свойства #AuthData
        classicInterfaceWrap.Set_AuthData(self.context, value, len(value))

    def Set_FNArchiveType(self, value): # Тип файла архива ФН
        classicInterfaceWrap.Set_FNArchiveType(self.context, value)

    def Get_FNArchiveType(self): # Возвращает значение свойства #FNArchiveType
        return classicInterfaceWrap.Get_FNArchiveType(self.context)

    def Set_MarkingOnly(self, value): # Только с кодами маркировки
        classicInterfaceWrap.Set_MarkingOnly(self.context, value)

    def Get_MarkingOnly(self): # Возвращает значение свойства #MarkingOnly
        return classicInterfaceWrap.Get_MarkingOnly(self.context)

    def Set_ItemStatus(self, value): # Статус позиции
        classicInterfaceWrap.Set_ItemStatus(self.context, value)

    def Get_ItemStatus(self): # Возвращает значение свойства #ItemStatus
        return classicInterfaceWrap.Get_ItemStatus(self.context)

    def Set_CheckItemMode(self, value): # Режим обработки
        classicInterfaceWrap.Set_CheckItemMode(self.context, value)

    def Get_CheckItemMode(self): # Возвращает значение свойства #CheckItemMode
        return classicInterfaceWrap.Get_CheckItemMode(self.context)

    def Set_CheckItemLocalResult(self, value): # Статус локальной проверки
        classicInterfaceWrap.Set_CheckItemLocalResult(self.context, value)

    def Get_CheckItemLocalResult(self): # Возвращает значение свойства #CheckItemLocalResult
        return classicInterfaceWrap.Get_CheckItemLocalResult(self.context)

    def Set_KMServerErrorCode(self, value): # Код ответа ФН на команду онлайн-проверки КМ
        classicInterfaceWrap.Set_KMServerErrorCode(self.context, value)

    def Get_KMServerErrorCode(self): # Возвращает значение свойства #KMServerErrorCode
        return classicInterfaceWrap.Get_KMServerErrorCode(self.context)

    def Set_KMServerCheckingStatus(self, value): # Результат онлайн проверки КМ
        classicInterfaceWrap.Set_KMServerCheckingStatus(self.context, value)

    def Get_KMServerCheckingStatus(self): # Возвращает значение свойства #KMServerCheckingStatus
        return classicInterfaceWrap.Get_KMServerCheckingStatus(self.context)

    def Set_UserAttributeName(self, value): # Наименование дополнительного реквизита пользователя
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_UserAttributeName(self.context, valueBuff, len(valueBuff))

    def Get_UserAttributeName(self): # Возвращает значение свойства #UserAttributeName
        resultLen = classicInterfaceWrap.Get_UserAttributeName(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_UserAttributeName(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_UserAttributeValue(self, value): # Значение дополнительного реквизита пользователя
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_UserAttributeValue(self.context, valueBuff, len(valueBuff))

    def Get_UserAttributeValue(self): # Возвращает значение свойства #UserAttributeValue
        resultLen = classicInterfaceWrap.Get_UserAttributeValue(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_UserAttributeValue(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_WaitForPrintingTimeout(self, value): # Общий таймаут ожидания окончания печати
        classicInterfaceWrap.Set_WaitForPrintingTimeout(self.context, value)

    def Get_WaitForPrintingTimeout(self): # Возвращает значение свойства #WaitForPrintingTimeout
        return classicInterfaceWrap.Get_WaitForPrintingTimeout(self.context)

    def Set_DeclarativeInput(self, value): # Входные данные декларативного документа
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_DeclarativeInput(self.context, valueBuff, len(valueBuff))

    def Get_DeclarativeInput(self): # Возвращает значение свойства #DeclarativeInput
        resultLen = classicInterfaceWrap.Get_DeclarativeInput(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_DeclarativeInput(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_DeclarativeOutput(self, value): # Выходные данные декларативного документа
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_DeclarativeOutput(self.context, valueBuff, len(valueBuff))

    def Get_DeclarativeOutput(self): # Возвращает значение свойства #DeclarativeOutput
        resultLen = classicInterfaceWrap.Get_DeclarativeOutput(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_DeclarativeOutput(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_DeclarativeEndpointPath(self, value): # Путь/тип интерпретации декларативного документа
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_DeclarativeEndpointPath(self.context, valueBuff, len(valueBuff))

    def Get_DeclarativeEndpointPath(self): # Возвращает значение свойства #DeclarativeEndpointPath
        resultLen = classicInterfaceWrap.Get_DeclarativeEndpointPath(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_DeclarativeEndpointPath(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Get_FontHashHex(self): # Хеш пользовательского шрифта из ККТ
        resultLen = classicInterfaceWrap.Get_FontHashHex(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_FontHashHex(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_MCOSUSign(self, value): # Признак ОСУ(Объемно Сортового Учета)
        classicInterfaceWrap.Set_MCOSUSign(self.context, value)

    def Get_MCOSUSign(self): # Возвращает значение свойства #MCOSUSign
        return classicInterfaceWrap.Get_MCOSUSign(self.context)

    def Set_DocumentSize(self, value): # Размер текущего документа в ФН в байтах
        classicInterfaceWrap.Set_DocumentSize(self.context, value)

    def Get_DocumentSize(self): # Возвращает значение свойства #DocumentSize
        return classicInterfaceWrap.Get_DocumentSize(self.context)

    def Set_FNImplementation(self, value): # Исполнение ФН
        valueBuff = wrapString(value)
        classicInterfaceWrap.Set_FNImplementation(self.context, valueBuff, len(valueBuff))

    def Get_FNImplementation(self): # Возвращает значение свойства #FNImplementation
        resultLen = classicInterfaceWrap.Get_FNImplementation(self.context, None, 0)
        resultBuffer = ctypes.create_string_buffer(resultLen+1)
        classicInterfaceWrap.Get_FNImplementation(self.context, resultBuffer, resultLen+1)
        return ctypes.string_at(resultBuffer, resultLen).decode('utf-8')

    def Set_FNOSUSupportStatus(self, value): # Cтатус поддержки ФН ОСУ Возможные значения: FF - не поддерживает 00 - поддерживает и ОСУ не активна 01 - поддерживает и ОСУ активна
        classicInterfaceWrap.Set_FNOSUSupportStatus(self.context, value)

    def Get_FNOSUSupportStatus(self): # Возвращает значение свойства #FNOSUSupportStatus
        return classicInterfaceWrap.Get_FNOSUSupportStatus(self.context)


    BatteryCondition                = property(fget=Get_BatteryCondition               , fset=None                               )
    CheckResult                     = property(fget=Get_CheckResult                    , fset=Set_CheckResult                    )
    CurrentDozeInMilliliters        = property(fget=Get_CurrentDozeInMilliliters       , fset=Set_CurrentDozeInMilliliters       )
    CurrentDozeInMoney              = property(fget=Get_CurrentDozeInMoney             , fset=Set_CurrentDozeInMoney             )
    DozeInMilliliters               = property(fget=Get_DozeInMilliliters              , fset=Set_DozeInMilliliters              )
    DozeInMoney                     = property(fget=Get_DozeInMoney                    , fset=Set_DozeInMoney                    )
    ECRAdvancedModeDescription      = property(fget=Get_ECRAdvancedModeDescription     , fset=None                               ) # Описание подрежима ККМ
    ECRInput                        = property(fget=Get_ECRInput                       , fset=None                               )
    ECROutput                       = property(fget=Get_ECROutput                      , fset=None                               )
    EmergencyStopCode               = property(fget=Get_EmergencyStopCode              , fset=None                               )
    EmergencyStopCodeDescription    = property(fget=Get_EmergencyStopCodeDescription   , fset=None                               )
    IsCheckClosed                   = property(fget=Get_IsCheckClosed                  , fset=None                               )
    IsCheckMadeOut                  = property(fget=Get_IsCheckMadeOut                 , fset=None                               )
    KPKNumber                       = property(fget=Get_KPKNumber                      , fset=Set_KPKNumber                      )
    Motor                           = property(fget=Get_Motor                          , fset=None                               )
    Pistol                          = property(fget=Get_Pistol                         , fset=None                               )
    RKNumber                        = property(fget=Get_RKNumber                       , fset=Set_RKNumber                       )
    RoughValve                      = property(fget=Get_RoughValve                     , fset=None                               )
    SlowingInMilliliters            = property(fget=Get_SlowingInMilliliters           , fset=Set_SlowingInMilliliters           )
    SlowingValve                    = property(fget=Get_SlowingValve                   , fset=None                               )
    StatusRK                        = property(fget=Get_StatusRK                       , fset=None                               )
    StatusRKDescription             = property(fget=Get_StatusRKDescription            , fset=None                               )
    TRKNumber                       = property(fget=Get_TRKNumber                      , fset=Set_TRKNumber                      )
    LDBaudrate                      = property(fget=Get_LDBaudrate                     , fset=Set_LDBaudrate                     )
    LDComNumber                     = property(fget=Get_LDComNumber                    , fset=Set_LDComNumber                    )
    LDCount                         = property(fget=Get_LDCount                        , fset=None                               )
    LDIndex                         = property(fget=Get_LDIndex                        , fset=Set_LDIndex                        )
    LDName                          = property(fget=Get_LDName                         , fset=Set_LDName                         )
    LDNumber                        = property(fget=Get_LDNumber                       , fset=Set_LDNumber                       )
    WaitPrintingTime                = property(fget=Get_WaitPrintingTime               , fset=None                               )
    EKLZNumber                      = property(fget=Get_EKLZNumber                     , fset=None                               )
    LastKPKDocumentResult           = property(fget=Get_LastKPKDocumentResult          , fset=None                               )
    LastKPKDate                     = property(fget=Get_LastKPKDate                    , fset=None                               )
    LastKPKTime                     = property(fget=Get_LastKPKTime                    , fset=None                               )
    LastKPKNumber                   = property(fget=Get_LastKPKNumber                  , fset=None                               )
    EKLZFlags                       = property(fget=Get_EKLZFlags                      , fset=None                               )
    TestNumber                      = property(fget=Get_TestNumber                     , fset=Set_TestNumber                     )
    EKLZVersion                     = property(fget=Get_EKLZVersion                    , fset=None                               )
    EKLZData                        = property(fget=Get_EKLZData                       , fset=None                               )
    CopyType                        = property(fget=Get_CopyType                       , fset=Set_CopyType                       )
    NumberOfCopies                  = property(fget=Get_NumberOfCopies                 , fset=Set_NumberOfCopies                 )
    CopyOffset1                     = property(fget=Get_CopyOffset1                    , fset=Set_CopyOffset1                    )
    CopyOffset2                     = property(fget=Get_CopyOffset2                    , fset=Set_CopyOffset2                    )
    CopyOffset3                     = property(fget=Get_CopyOffset3                    , fset=Set_CopyOffset3                    )
    CopyOffset4                     = property(fget=Get_CopyOffset4                    , fset=Set_CopyOffset4                    )
    CopyOffset5                     = property(fget=Get_CopyOffset5                    , fset=Set_CopyOffset5                    )
    ClicheFont                      = property(fget=Get_ClicheFont                     , fset=Set_ClicheFont                     )
    HeaderFont                      = property(fget=Get_HeaderFont                     , fset=Set_HeaderFont                     )
    EKLZFont                        = property(fget=Get_EKLZFont                       , fset=Set_EKLZFont                       )
    ClicheStringNumber              = property(fget=Get_ClicheStringNumber             , fset=Set_ClicheStringNumber             )
    HeaderStringNumber              = property(fget=Get_HeaderStringNumber             , fset=Set_HeaderStringNumber             )
    EKLZStringNumber                = property(fget=Get_EKLZStringNumber               , fset=Set_EKLZStringNumber               )
    FMStringNumber                  = property(fget=Get_FMStringNumber                 , fset=Set_FMStringNumber                 )
    ClicheOffset                    = property(fget=Get_ClicheOffset                   , fset=Set_ClicheOffset                   )
    HeaderOffset                    = property(fget=Get_HeaderOffset                   , fset=Set_HeaderOffset                   )
    EKLZOffset                      = property(fget=Get_EKLZOffset                     , fset=Set_EKLZOffset                     )
    KPKOffset                       = property(fget=Get_KPKOffset                      , fset=Set_KPKOffset                      )
    FMOffset                        = property(fget=Get_FMOffset                       , fset=Set_FMOffset                       )
    OperationBlockFirstString       = property(fget=Get_OperationBlockFirstString      , fset=Set_OperationBlockFirstString      )
    QuantityFormat                  = property(fget=Get_QuantityFormat                 , fset=Set_QuantityFormat                 )
    StringQuantityInOperation       = property(fget=Get_StringQuantityInOperation      , fset=Set_StringQuantityInOperation      )
    TextStringNumber                = property(fget=Get_TextStringNumber               , fset=Set_TextStringNumber               )
    QuantityStringNumber            = property(fget=Get_QuantityStringNumber           , fset=Set_QuantityStringNumber           )
    SummStringNumber                = property(fget=Get_SummStringNumber               , fset=Set_SummStringNumber               )
    DepartmentStringNumber          = property(fget=Get_DepartmentStringNumber         , fset=Set_DepartmentStringNumber         )
    TextFont                        = property(fget=Get_TextFont                       , fset=Set_TextFont                       )
    QuantityFont                    = property(fget=Get_QuantityFont                   , fset=Set_QuantityFont                   )
    MultiplicationFont              = property(fget=Get_MultiplicationFont             , fset=Set_MultiplicationFont             )
    PriceFont                       = property(fget=Get_PriceFont                      , fset=Set_PriceFont                      )
    SummFont                        = property(fget=Get_SummFont                       , fset=Set_SummFont                       )
    DepartmentFont                  = property(fget=Get_DepartmentFont                 , fset=Set_DepartmentFont                 )
    TextSymbolNumber                = property(fget=Get_TextSymbolNumber               , fset=Set_TextSymbolNumber               )
    QuantitySymbolNumber            = property(fget=Get_QuantitySymbolNumber           , fset=Set_QuantitySymbolNumber           )
    PriceSymbolNumber               = property(fget=Get_PriceSymbolNumber              , fset=Set_PriceSymbolNumber              )
    SummSymbolNumber                = property(fget=Get_SummSymbolNumber               , fset=Set_SummSymbolNumber               )
    DepartmentSymbolNumber          = property(fget=Get_DepartmentSymbolNumber         , fset=Set_DepartmentSymbolNumber         )
    TextOffset                      = property(fget=Get_TextOffset                     , fset=Set_TextOffset                     )
    QuantityOffset                  = property(fget=Get_QuantityOffset                 , fset=Set_QuantityOffset                 )
    SummOffset                      = property(fget=Get_SummOffset                     , fset=Set_SummOffset                     )
    DepartmentOffset                = property(fget=Get_DepartmentOffset               , fset=Set_DepartmentOffset               )
    IsClearUnfiscalInfo             = property(fget=Get_IsClearUnfiscalInfo            , fset=Set_IsClearUnfiscalInfo            )
    InfoType                        = property(fget=Get_InfoType                       , fset=Set_InfoType                       )
    StringNumber                    = property(fget=Get_StringNumber                   , fset=Set_StringNumber                   )
    EjectDirection                  = property(fget=Get_EjectDirection                 , fset=Set_EjectDirection                 )
    OperationNameStringNumber       = property(fget=Get_OperationNameStringNumber      , fset=Set_OperationNameStringNumber      )
    OperationNameFont               = property(fget=Get_OperationNameFont              , fset=Set_OperationNameFont              )
    OperationNameOffset             = property(fget=Get_OperationNameOffset            , fset=Set_OperationNameOffset            )
    TotalStringNumber               = property(fget=Get_TotalStringNumber              , fset=Set_TotalStringNumber              )
    Summ1StringNumber               = property(fget=Get_Summ1StringNumber              , fset=Set_Summ1StringNumber              )
    Summ2StringNumber               = property(fget=Get_Summ2StringNumber              , fset=Set_Summ2StringNumber              )
    Summ3StringNumber               = property(fget=Get_Summ3StringNumber              , fset=Set_Summ3StringNumber              )
    Summ4StringNumber               = property(fget=Get_Summ4StringNumber              , fset=Set_Summ4StringNumber              )
    ChangeStringNumber              = property(fget=Get_ChangeStringNumber             , fset=Set_ChangeStringNumber             )
    Tax1TurnOverStringNumber        = property(fget=Get_Tax1TurnOverStringNumber       , fset=Set_Tax1TurnOverStringNumber       )
    Tax2TurnOverStringNumber        = property(fget=Get_Tax2TurnOverStringNumber       , fset=Set_Tax2TurnOverStringNumber       )
    Tax3TurnOverStringNumber        = property(fget=Get_Tax3TurnOverStringNumber       , fset=Set_Tax3TurnOverStringNumber       )
    Tax4TurnOverStringNumber        = property(fget=Get_Tax4TurnOverStringNumber       , fset=Set_Tax4TurnOverStringNumber       )
    Tax1SumStringNumber             = property(fget=Get_Tax1SumStringNumber            , fset=Set_Tax1SumStringNumber            )
    Tax2SumStringNumber             = property(fget=Get_Tax2SumStringNumber            , fset=Set_Tax2SumStringNumber            )
    Tax3SumStringNumber             = property(fget=Get_Tax3SumStringNumber            , fset=Set_Tax3SumStringNumber            )
    Tax4SumStringNumber             = property(fget=Get_Tax4SumStringNumber            , fset=Set_Tax4SumStringNumber            )
    SubTotalStringNumber            = property(fget=Get_SubTotalStringNumber           , fset=Set_SubTotalStringNumber           )
    DiscountOnCheckStringNumber     = property(fget=Get_DiscountOnCheckStringNumber    , fset=Set_DiscountOnCheckStringNumber    )
    TotalFont                       = property(fget=Get_TotalFont                      , fset=Set_TotalFont                      )
    TotalSumFont                    = property(fget=Get_TotalSumFont                   , fset=Set_TotalSumFont                   )
    Summ1Font                       = property(fget=Get_Summ1Font                      , fset=Set_Summ1Font                      )
    Summ1NameFont                   = property(fget=Get_Summ1NameFont                  , fset=Set_Summ1NameFont                  )
    Summ2NameFont                   = property(fget=Get_Summ2NameFont                  , fset=Set_Summ2NameFont                  )
    Summ3NameFont                   = property(fget=Get_Summ3NameFont                  , fset=Set_Summ3NameFont                  )
    Summ4NameFont                   = property(fget=Get_Summ4NameFont                  , fset=Set_Summ4NameFont                  )
    Summ2Font                       = property(fget=Get_Summ2Font                      , fset=Set_Summ2Font                      )
    Summ3Font                       = property(fget=Get_Summ3Font                      , fset=Set_Summ3Font                      )
    Summ4Font                       = property(fget=Get_Summ4Font                      , fset=Set_Summ4Font                      )
    ChangeFont                      = property(fget=Get_ChangeFont                     , fset=Set_ChangeFont                     )
    ChangeSumFont                   = property(fget=Get_ChangeSumFont                  , fset=Set_ChangeSumFont                  )
    Tax1NameFont                    = property(fget=Get_Tax1NameFont                   , fset=Set_Tax1NameFont                   )
    Tax2NameFont                    = property(fget=Get_Tax2NameFont                   , fset=Set_Tax2NameFont                   )
    Tax3NameFont                    = property(fget=Get_Tax3NameFont                   , fset=Set_Tax3NameFont                   )
    Tax4NameFont                    = property(fget=Get_Tax4NameFont                   , fset=Set_Tax4NameFont                   )
    Tax1TurnOverFont                = property(fget=Get_Tax1TurnOverFont               , fset=Set_Tax1TurnOverFont               )
    Tax2TurnOverFont                = property(fget=Get_Tax2TurnOverFont               , fset=Set_Tax2TurnOverFont               )
    Tax3TurnOverFont                = property(fget=Get_Tax3TurnOverFont               , fset=Set_Tax3TurnOverFont               )
    Tax4TurnOverFont                = property(fget=Get_Tax4TurnOverFont               , fset=Set_Tax4TurnOverFont               )
    Tax1RateFont                    = property(fget=Get_Tax1RateFont                   , fset=Set_Tax1RateFont                   )
    Tax2RateFont                    = property(fget=Get_Tax2RateFont                   , fset=Set_Tax2RateFont                   )
    Tax3RateFont                    = property(fget=Get_Tax3RateFont                   , fset=Set_Tax3RateFont                   )
    Tax4RateFont                    = property(fget=Get_Tax4RateFont                   , fset=Set_Tax4RateFont                   )
    Tax1SumFont                     = property(fget=Get_Tax1SumFont                    , fset=Set_Tax1SumFont                    )
    Tax2SumFont                     = property(fget=Get_Tax2SumFont                    , fset=Set_Tax2SumFont                    )
    Tax3SumFont                     = property(fget=Get_Tax3SumFont                    , fset=Set_Tax3SumFont                    )
    Tax4SumFont                     = property(fget=Get_Tax4SumFont                    , fset=Set_Tax4SumFont                    )
    SubTotalFont                    = property(fget=Get_SubTotalFont                   , fset=Set_SubTotalFont                   )
    SubTotalSumFont                 = property(fget=Get_SubTotalSumFont                , fset=Set_SubTotalSumFont                )
    DiscountOnCheckFont             = property(fget=Get_DiscountOnCheckFont            , fset=Set_DiscountOnCheckFont            )
    DiscountOnCheckSumFont          = property(fget=Get_DiscountOnCheckSumFont         , fset=Set_DiscountOnCheckSumFont         )
    TotalSymbolNumber               = property(fget=Get_TotalSymbolNumber              , fset=Set_TotalSymbolNumber              )
    Summ1SymbolNumber               = property(fget=Get_Summ1SymbolNumber              , fset=Set_Summ1SymbolNumber              )
    Summ2SymbolNumber               = property(fget=Get_Summ2SymbolNumber              , fset=Set_Summ2SymbolNumber              )
    Summ3SymbolNumber               = property(fget=Get_Summ3SymbolNumber              , fset=Set_Summ3SymbolNumber              )
    Summ4SymbolNumber               = property(fget=Get_Summ4SymbolNumber              , fset=Set_Summ4SymbolNumber              )
    ChangeSymbolNumber              = property(fget=Get_ChangeSymbolNumber             , fset=Set_ChangeSymbolNumber             )
    Tax1NameSymbolNumber            = property(fget=Get_Tax1NameSymbolNumber           , fset=Set_Tax1NameSymbolNumber           )
    Tax1TurnOverSymbolNumber        = property(fget=Get_Tax1TurnOverSymbolNumber       , fset=Set_Tax1TurnOverSymbolNumber       )
    Tax1RateSymbolNumber            = property(fget=Get_Tax1RateSymbolNumber           , fset=Set_Tax1RateSymbolNumber           )
    Tax1SumSymbolNumber             = property(fget=Get_Tax1SumSymbolNumber            , fset=Set_Tax1SumSymbolNumber            )
    Tax2NameSymbolNumber            = property(fget=Get_Tax2NameSymbolNumber           , fset=Set_Tax2NameSymbolNumber           )
    Tax2TurnOverSymbolNumber        = property(fget=Get_Tax2TurnOverSymbolNumber       , fset=Set_Tax2TurnOverSymbolNumber       )
    Tax2RateSymbolNumber            = property(fget=Get_Tax2RateSymbolNumber           , fset=Set_Tax2RateSymbolNumber           )
    Tax2SumSymbolNumber             = property(fget=Get_Tax2SumSymbolNumber            , fset=Set_Tax2SumSymbolNumber            )
    Tax3NameSymbolNumber            = property(fget=Get_Tax3NameSymbolNumber           , fset=Set_Tax3NameSymbolNumber           )
    Tax3TurnOverSymbolNumber        = property(fget=Get_Tax3TurnOverSymbolNumber       , fset=Set_Tax3TurnOverSymbolNumber       )
    Tax3RateSymbolNumber            = property(fget=Get_Tax3RateSymbolNumber           , fset=Set_Tax3RateSymbolNumber           )
    Tax3SumSymbolNumber             = property(fget=Get_Tax3SumSymbolNumber            , fset=Set_Tax3SumSymbolNumber            )
    Tax4NameSymbolNumber            = property(fget=Get_Tax4NameSymbolNumber           , fset=Set_Tax4NameSymbolNumber           )
    Tax4TurnOverSymbolNumber        = property(fget=Get_Tax4TurnOverSymbolNumber       , fset=Set_Tax4TurnOverSymbolNumber       )
    Tax4RateSymbolNumber            = property(fget=Get_Tax4RateSymbolNumber           , fset=Set_Tax4RateSymbolNumber           )
    Tax4SumSymbolNumber             = property(fget=Get_Tax4SumSymbolNumber            , fset=Set_Tax4SumSymbolNumber            )
    SubTotalSymbolNumber            = property(fget=Get_SubTotalSymbolNumber           , fset=Set_SubTotalSymbolNumber           )
    DiscountOnCheckSymbolNumber     = property(fget=Get_DiscountOnCheckSymbolNumber    , fset=Set_DiscountOnCheckSymbolNumber    )
    DiscountOnCheckSumSymbolNumber  = property(fget=Get_DiscountOnCheckSumSymbolNumber , fset=Set_DiscountOnCheckSumSymbolNumber )
    TotalOffset                     = property(fget=Get_TotalOffset                    , fset=Set_TotalOffset                    )
    Summ1Offset                     = property(fget=Get_Summ1Offset                    , fset=Set_Summ1Offset                    )
    TotalSumOffset                  = property(fget=Get_TotalSumOffset                 , fset=Set_TotalSumOffset                 )
    Summ1NameOffset                 = property(fget=Get_Summ1NameOffset                , fset=Set_Summ1NameOffset                )
    Summ2Offset                     = property(fget=Get_Summ2Offset                    , fset=Set_Summ2Offset                    )
    Summ2NameOffset                 = property(fget=Get_Summ2NameOffset                , fset=Set_Summ2NameOffset                )
    Summ3Offset                     = property(fget=Get_Summ3Offset                    , fset=Set_Summ3Offset                    )
    Summ3NameOffset                 = property(fget=Get_Summ3NameOffset                , fset=Set_Summ3NameOffset                )
    Summ4Offset                     = property(fget=Get_Summ4Offset                    , fset=Set_Summ4Offset                    )
    Summ4NameOffset                 = property(fget=Get_Summ4NameOffset                , fset=Set_Summ4NameOffset                )
    ChangeOffset                    = property(fget=Get_ChangeOffset                   , fset=Set_ChangeOffset                   )
    ChangeSumOffset                 = property(fget=Get_ChangeSumOffset                , fset=Set_ChangeSumOffset                )
    Tax1NameOffset                  = property(fget=Get_Tax1NameOffset                 , fset=Set_Tax1NameOffset                 )
    Tax1TurnOverOffset              = property(fget=Get_Tax1TurnOverOffset             , fset=Set_Tax1TurnOverOffset             )
    Tax1RateOffset                  = property(fget=Get_Tax1RateOffset                 , fset=Set_Tax1RateOffset                 )
    Tax1SumOffset                   = property(fget=Get_Tax1SumOffset                  , fset=Set_Tax1SumOffset                  )
    Tax2NameOffset                  = property(fget=Get_Tax2NameOffset                 , fset=Set_Tax2NameOffset                 )
    Tax2TurnOverOffset              = property(fget=Get_Tax2TurnOverOffset             , fset=Set_Tax2TurnOverOffset             )
    Tax2RateOffset                  = property(fget=Get_Tax2RateOffset                 , fset=Set_Tax2RateOffset                 )
    Tax2SumOffset                   = property(fget=Get_Tax2SumOffset                  , fset=Set_Tax2SumOffset                  )
    Tax3NameOffset                  = property(fget=Get_Tax3NameOffset                 , fset=Set_Tax3NameOffset                 )
    Tax3TurnOverOffset              = property(fget=Get_Tax3TurnOverOffset             , fset=Set_Tax3TurnOverOffset             )
    Tax3RateOffset                  = property(fget=Get_Tax3RateOffset                 , fset=Set_Tax3RateOffset                 )
    Tax3SumOffset                   = property(fget=Get_Tax3SumOffset                  , fset=Set_Tax3SumOffset                  )
    Tax4NameOffset                  = property(fget=Get_Tax4NameOffset                 , fset=Set_Tax4NameOffset                 )
    Tax4TurnOverOffset              = property(fget=Get_Tax4TurnOverOffset             , fset=Set_Tax4TurnOverOffset             )
    Tax4RateOffset                  = property(fget=Get_Tax4RateOffset                 , fset=Set_Tax4RateOffset                 )
    Tax4SumOffset                   = property(fget=Get_Tax4SumOffset                  , fset=Set_Tax4SumOffset                  )
    SubTotalOffset                  = property(fget=Get_SubTotalOffset                 , fset=Set_SubTotalOffset                 )
    SubTotalSumOffset               = property(fget=Get_SubTotalSumOffset              , fset=Set_SubTotalSumOffset              )
    SlipDocumentWidth               = property(fget=Get_SlipDocumentWidth              , fset=Set_SlipDocumentWidth              )
    SlipDocumentLength              = property(fget=Get_SlipDocumentLength             , fset=Set_SlipDocumentLength             )
    PrintingAlignment               = property(fget=Get_PrintingAlignment              , fset=Set_PrintingAlignment              )
    SlipStringIntervals             = property(fget=Get_SlipStringIntervals            , fset=Set_SlipStringIntervals            )
    SlipEqualStringIntervals        = property(fget=Get_SlipEqualStringIntervals       , fset=Set_SlipEqualStringIntervals       )
    KPKFont                         = property(fget=Get_KPKFont                        , fset=Set_KPKFont                        )
    DiscountOnCheckOffset           = property(fget=Get_DiscountOnCheckOffset          , fset=Set_DiscountOnCheckOffset          )
    DiscountOnCheckSumOffset        = property(fget=Get_DiscountOnCheckSumOffset       , fset=Set_DiscountOnCheckSumOffset       )
    FileVersionMS                   = property(fget=Get_FileVersionMS                  , fset=None                               )
    FileVersionLS                   = property(fget=Get_FileVersionLS                  , fset=None                               )
    PrinterStatus                   = property(fget=Get_PrinterStatus                  , fset=None                               )
    ServerVersion                   = property(fget=Get_ServerVersion                  , fset=None                               )
    LDComputerName                  = property(fget=Get_LDComputerName                 , fset=Set_LDComputerName                 )
    LDTimeout                       = property(fget=Get_LDTimeout                      , fset=Set_LDTimeout                      )
    ServerConnected                 = property(fget=Get_ServerConnected                , fset=None                               )
    PortLocked                      = property(fget=Get_PortLocked                     , fset=None                               )
    LogOn                           = property(fget=Get_LogOn                          , fset=Set_LogOn                          )
    CPLog                           = property(fget=Get_CPLog                          , fset=Set_CPLog                          )
    CashControlHost                 = property(fget=Get_CashControlHost                , fset=Set_CashControlHost                )
    CashControlPort                 = property(fget=Get_CashControlPort                , fset=Set_CashControlPort                )
    CashControlEnabled              = property(fget=Get_CashControlEnabled             , fset=Set_CashControlEnabled             )
    CashControlUseTCP               = property(fget=Get_CashControlUseTCP              , fset=Set_CashControlUseTCP              )
    CashControlPassword             = property(fget=Get_CashControlPassword            , fset=Set_CashControlPassword            )
    LDConnectionType                = property(fget=Get_LDConnectionType               , fset=Set_LDConnectionType               )
    LDTCPPort                       = property(fget=Get_LDTCPPort                      , fset=Set_LDTCPPort                      )
    LDIPAddress                     = property(fget=Get_LDIPAddress                    , fset=Set_LDIPAddress                    )
    LDUseIPAddress                  = property(fget=Get_LDUseIPAddress                 , fset=Set_LDUseIPAddress                 )
    CPLogFile                       = property(fget=Get_CPLogFile                      , fset=Set_CPLogFile                      )
    ComLogFile                      = property(fget=Get_ComLogFile                     , fset=Set_ComLogFile                     )
    LineData2                       = property(fget=Get_LineData2                      , fset=Set_LineData2                      )
    RecoverError165                 = property(fget=Get_RecoverError165                , fset=Set_RecoverError165                )
    MaxRecoverCount                 = property(fget=Get_MaxRecoverCount                , fset=Set_MaxRecoverCount                )
    OperationCode                   = property(fget=Get_OperationCode                  , fset=None                               )
    AccType                         = property(fget=Get_AccType                        , fset=Set_AccType                        )
    Address                         = property(fget=Get_Address                        , fset=Set_Address                        )
    WrittenByte                     = property(fget=Get_WrittenByte                    , fset=Set_WrittenByte                    )
    ReadByte                        = property(fget=Get_ReadByte                       , fset=None                               )
    TransferByte                    = property(fget=Get_TransferByte                   , fset=Set_TransferByte                   )
    ComLogOnlyErrors                = property(fget=Get_ComLogOnlyErrors               , fset=Set_ComLogOnlyErrors               )
    LastKPKDateStr                  = property(fget=Get_LastKPKDateStr                 , fset=None                               )
    LastKPKTimeStr                  = property(fget=Get_LastKPKTimeStr                 , fset=None                               )
    MethodName                      = property(fget=Get_MethodName                     , fset=Set_MethodName                     )
    PropertyName                    = property(fget=Get_PropertyName                   , fset=Set_PropertyName                   )
    LockTimeout                     = property(fget=Get_LockTimeout                    , fset=Set_LockTimeout                    )
    SlipStringInterval              = property(fget=Get_SlipStringInterval             , fset=Set_SlipStringInterval             )
    IBMStatusByte1                  = property(fget=Get_IBMStatusByte1                 , fset=None                               )
    IBMStatusByte2                  = property(fget=Get_IBMStatusByte2                 , fset=None                               )
    IBMStatusByte3                  = property(fget=Get_IBMStatusByte3                 , fset=None                               )
    IBMStatusByte4                  = property(fget=Get_IBMStatusByte4                 , fset=None                               )
    IBMStatusByte5                  = property(fget=Get_IBMStatusByte5                 , fset=None                               )
    IBMStatusByte6                  = property(fget=Get_IBMStatusByte6                 , fset=None                               )
    IBMStatusByte7                  = property(fget=Get_IBMStatusByte7                 , fset=None                               )
    IBMStatusByte8                  = property(fget=Get_IBMStatusByte8                 , fset=None                               )
    IBMFlags                        = property(fget=Get_IBMFlags                       , fset=None                               )
    IBMDocumentNumber               = property(fget=Get_IBMDocumentNumber              , fset=None                               )
    IBMLastSaleReceiptNumber        = property(fget=Get_IBMLastSaleReceiptNumber       , fset=None                               )
    IBMLastBuyReceiptNumber         = property(fget=Get_IBMLastBuyReceiptNumber        , fset=None                               )
    IBMLastReturnSaleReceiptNumber  = property(fget=Get_IBMLastReturnSaleReceiptNumber , fset=None                               )
    IBMLastReturnBuyReceiptNumber   = property(fget=Get_IBMLastReturnBuyReceiptNumber  , fset=None                               )
    IBMSessionDay                   = property(fget=Get_IBMSessionDay                  , fset=None                               )
    IBMSessionMonth                 = property(fget=Get_IBMSessionMonth                , fset=None                               )
    IBMSessionYear                  = property(fget=Get_IBMSessionYear                 , fset=None                               )
    IBMSessionHour                  = property(fget=Get_IBMSessionHour                 , fset=None                               )
    IBMSessionMin                   = property(fget=Get_IBMSessionMin                  , fset=None                               )
    IBMSessionSec                   = property(fget=Get_IBMSessionSec                  , fset=None                               )
    IBMSessionDateTime              = property(fget=Get_IBMSessionDateTime             , fset=None                               )
    EscapeIP                        = property(fget=Get_EscapeIP                       , fset=Set_EscapeIP                       )
    EscapePort                      = property(fget=Get_EscapePort                     , fset=Set_EscapePort                     )
    LDEscapeIP                      = property(fget=Get_LDEscapeIP                     , fset=Set_LDEscapeIP                     )
    LDEscapePort                    = property(fget=Get_LDEscapePort                   , fset=Set_LDEscapePort                   )
    EscapeTimeout                   = property(fget=Get_EscapeTimeout                  , fset=Set_EscapeTimeout                  )
    LDEscapeTimeout                 = property(fget=Get_LDEscapeTimeout                , fset=Set_LDEscapeTimeout                )
    CommandTimeout                  = property(fget=Get_CommandTimeout                 , fset=Set_CommandTimeout                 )
    UseCommandTimeout               = property(fget=Get_UseCommandTimeout              , fset=Set_UseCommandTimeout              )
    CommandCount                    = property(fget=Get_CommandCount                   , fset=None                               )
    CommandIndex                    = property(fget=Get_CommandIndex                   , fset=Set_CommandIndex                   )
    CommandName                     = property(fget=Get_CommandName                    , fset=None                               )
    CommandDefTimeout               = property(fget=Get_CommandDefTimeout              , fset=None                               )
    CommandCode                     = property(fget=Get_CommandCode                    , fset=None                               )
    TimeoutsUsing                   = property(fget=Get_TimeoutsUsing                  , fset=Set_TimeoutsUsing                  )
    IntervalNumber                  = property(fget=Get_IntervalNumber                 , fset=Set_IntervalNumber                 )
    IntervalValue                   = property(fget=Get_IntervalValue                  , fset=Set_IntervalValue                  )
    ParentWnd                       = property(fget=Get_ParentWnd                      , fset=Set_ParentWnd                      )
    MobilePayEnabled                = property(fget=Get_MobilePayEnabled               , fset=Set_MobilePayEnabled               )
    PayDepartment                   = property(fget=Get_PayDepartment                  , fset=Set_PayDepartment                  )
    ParamsPageIndex                 = property(fget=Get_ParamsPageIndex                , fset=Set_ParamsPageIndex                )
    SaleError                       = property(fget=Get_SaleError                      , fset=Set_SaleError                      )
    RealPayDepartment               = property(fget=Get_RealPayDepartment              , fset=Set_RealPayDepartment              )
    CardPayEnabled                  = property(fget=Get_CardPayEnabled                 , fset=Set_CardPayEnabled                 )
    CardPayType                     = property(fget=Get_CardPayType                    , fset=Set_CardPayType                    )
    ccUseTextAsWareName             = property(fget=Get_ccUseTextAsWareName            , fset=Set_ccUseTextAsWareName            )
    ccWareNameLineNumber            = property(fget=Get_ccWareNameLineNumber           , fset=Set_ccWareNameLineNumber           )
    ccHeaderLineCount               = property(fget=Get_ccHeaderLineCount              , fset=Set_ccHeaderLineCount              )
    LogCommands                     = property(fget=Get_LogCommands                    , fset=Set_LogCommands                    )
    LogMethods                      = property(fget=Get_LogMethods                     , fset=Set_LogMethods                     )
    JournalEnabled                  = property(fget=Get_JournalEnabled                 , fset=Set_JournalEnabled                 )
    JournalRow                      = property(fget=Get_JournalRow                     , fset=None                               )
    JournalRowCount                 = property(fget=Get_JournalRowCount                , fset=None                               )
    JournalRowNumber                = property(fget=Get_JournalRowNumber               , fset=Set_JournalRowNumber               )
    JournalText                     = property(fget=Get_JournalText                    , fset=None                               )
    SerialNumberAsInteger           = property(fget=Get_SerialNumberAsInteger          , fset=None                               )
    INNAsInteger                    = property(fget=Get_INNAsInteger                   , fset=None                               )
    ECRDate                         = property(fget=Get_ECRDate                        , fset=Set_ECRDate                        )
    ECRTime                         = property(fget=Get_ECRTime                        , fset=Set_ECRTime                        )
    HasCashControlLicense           = property(fget=Get_HasCashControlLicense          , fset=None                               )
    BufferingType                   = property(fget=Get_BufferingType                  , fset=Set_BufferingType                  )
    FeedAfterCut                    = property(fget=Get_FeedAfterCut                   , fset=Set_FeedAfterCut                   )
    FeedLineCount                   = property(fget=Get_FeedLineCount                  , fset=Set_FeedLineCount                  )
    CashControlProtocols            = property(fget=Get_CashControlProtocols           , fset=None                               )
    LogMaxFileSize                  = property(fget=Get_LogMaxFileSize                 , fset=Set_LogMaxFileSize                 )
    LogMaxFileCount                 = property(fget=Get_LogMaxFileCount                , fset=Set_LogMaxFileCount                )
    BinaryConversion                = property(fget=Get_BinaryConversion               , fset=Set_BinaryConversion               )
    CodePage                        = property(fget=Get_CodePage                       , fset=Set_CodePage                       )
    PrintJournalBeforeZReport       = property(fget=Get_PrintJournalBeforeZReport      , fset=Set_PrintJournalBeforeZReport      )
    TransmitStatus                  = property(fget=Get_TransmitStatus                 , fset=None                               )
    TransmitQueueSize               = property(fget=Get_TransmitQueueSize              , fset=None                               )
    TransmitSessionNumber           = property(fget=Get_TransmitSessionNumber          , fset=None                               )
    TransmitDocumentNumber          = property(fget=Get_TransmitDocumentNumber         , fset=None                               )
    ParameterNumber                 = property(fget=Get_ParameterNumber                , fset=Set_ParameterNumber                )
    ParameterValue                  = property(fget=Get_ParameterValue                 , fset=Set_ParameterValue                 )
    TranslationEnabled              = property(fget=Get_TranslationEnabled             , fset=Set_TranslationEnabled             )
    ModelIndex                      = property(fget=Get_ModelIndex                     , fset=Set_ModelIndex                     )
    ModelParamIndex                 = property(fget=Get_ModelParamIndex                , fset=Set_ModelParamIndex                )
    ModelParamCount                 = property(fget=Get_ModelParamCount                , fset=None                               ) # Количество параметров модели
    ReceiptOutputType               = property(fget=Get_ReceiptOutputType              , fset=Set_ReceiptOutputType              )
    BarcodeTypes                    = property(fget=Get_BarcodeTypes                   , fset=None                               )
    BarcodeAlignments               = property(fget=Get_BarcodeAlignments              , fset=None                               )
    LogFileMaxSize                  = property(fget=Get_LogFileMaxSize                 , fset=Set_LogFileMaxSize                 )
    PrintBufferFormat               = property(fget=Get_PrintBufferFormat              , fset=Set_PrintBufferFormat              )
    PrintBufferLineNumber           = property(fget=Get_PrintBufferLineNumber          , fset=None                               )
    NakCount                        = property(fget=Get_NakCount                       , fset=Set_NakCount                       )
    MaxAnswerReadCount              = property(fget=Get_MaxAnswerReadCount             , fset=Set_MaxAnswerReadCount             )
    MaxCommandSendCount             = property(fget=Get_MaxCommandSendCount            , fset=Set_MaxCommandSendCount            )
    MaxENQSendCount                 = property(fget=Get_MaxENQSendCount                , fset=Set_MaxENQSendCount                )
    CommandRetryCount               = property(fget=Get_CommandRetryCount              , fset=Set_CommandRetryCount              )
    AttributeNumber                 = property(fget=Get_AttributeNumber                , fset=Set_AttributeNumber                )
    AttributeValue                  = property(fget=Get_AttributeValue                 , fset=Set_AttributeValue                 )
    ModelID                         = property(fget=Get_ModelID                        , fset=Set_ModelID                        )
    Connected                       = property(fget=Get_Connected                      , fset=Set_Connected                      ) # Прочитать/Установить состояние соединения
    EnteredTaxPassword              = property(fget=Get_EnteredTaxPassword             , fset=None                               )
    BanknoteCount                   = property(fget=Get_BanknoteCount                  , fset=None                               )
    BanknoteType                    = property(fget=Get_BanknoteType                   , fset=Set_BanknoteType                   )
    CashAcceptorPollingMode         = property(fget=Get_CashAcceptorPollingMode        , fset=None                               )
    Poll1                           = property(fget=Get_Poll1                          , fset=None                               )
    Poll2                           = property(fget=Get_Poll2                          , fset=None                               )
    LDSysAdminPassword              = property(fget=Get_LDSysAdminPassword             , fset=Set_LDSysAdminPassword             )
    CapOpenCheck                    = property(fget=Get_CapOpenCheck                   , fset=None                               )
    PollDescription                 = property(fget=Get_PollDescription                , fset=None                               )
    HRIPosition                     = property(fget=Get_HRIPosition                    , fset=Set_HRIPosition                    )
    KPKStr                          = property(fget=Get_KPKStr                         , fset=None                               )
    TextBlock                       = property(fget=Get_TextBlock                      , fset=Set_TextBlock                      )
    TextBlockNumber                 = property(fget=Get_TextBlockNumber                , fset=Set_TextBlockNumber                )
    PosControlReceiptSeparator      = property(fget=Get_PosControlReceiptSeparator     , fset=Set_PosControlReceiptSeparator     )
    BarcodeDataLength               = property(fget=Get_BarcodeDataLength              , fset=Set_BarcodeDataLength              ) # Длина данных штрих-кода
    ExciseCode                      = property(fget=Get_ExciseCode                     , fset=Set_ExciseCode                     )
    SaveSettingsType                = property(fget=Get_SaveSettingsType               , fset=Set_SaveSettingsType               )
    ModelNames                      = property(fget=Get_ModelNames                     , fset=None                               )
    ModelsCount                     = property(fget=Get_ModelsCount                    , fset=None                               )
    FMFlagsEx                       = property(fget=Get_FMFlagsEx                      , fset=None                               )
    FMMode                          = property(fget=Get_FMMode                         , fset=None                               )
    IsASPDMode                      = property(fget=Get_IsASPDMode                     , fset=None                               )
    IsCorruptedFiscalizationInfo    = property(fget=Get_IsCorruptedFiscalizationInfo   , fset=None                               )
    IsCorruptedFMRecords            = property(fget=Get_IsCorruptedFMRecords           , fset=None                               )
    RegBuyRec                       = property(fget=Get_RegBuyRec                      , fset=None                               )
    RegBuyReturnRec                 = property(fget=Get_RegBuyReturnRec                , fset=None                               )
    RegBuyReturnSession             = property(fget=Get_RegBuyReturnSession            , fset=None                               )
    RegBuySession                   = property(fget=Get_RegBuySession                  , fset=None                               )
    RegSaleRec                      = property(fget=Get_RegSaleRec                     , fset=None                               )
    RegSaleReturnRec                = property(fget=Get_RegSaleReturnRec               , fset=None                               )
    RegSaleReturnSession            = property(fget=Get_RegSaleReturnSession           , fset=None                               )
    RegSaleSession                  = property(fget=Get_RegSaleSession                 , fset=None                               )
    WareCode                        = property(fget=Get_WareCode                       , fset=Set_WareCode                       )
    RecordCount                     = property(fget=Get_RecordCount                    , fset=None                               )
    CheckingType                    = property(fget=Get_CheckingType                   , fset=Set_CheckingType                   )
    UseWareCode                     = property(fget=Get_UseWareCode                    , fset=Set_UseWareCode                    )
    RequestErrorDescription         = property(fget=Get_RequestErrorDescription        , fset=Set_RequestErrorDescription        )
    AdjustRITimeout                 = property(fget=Get_AdjustRITimeout                , fset=Set_AdjustRITimeout                )
    UCodePageText                   = property(fget=Get_UCodePageText                  , fset=None                               )
    ReconnectPort                   = property(fget=Get_ReconnectPort                  , fset=Set_ReconnectPort                  ) # Переподключать соединение в случае отсутствия связи
    DoNotSendENQ                    = property(fget=Get_DoNotSendENQ                   , fset=Set_DoNotSendENQ                   )
    CheckEJConnection               = property(fget=Get_CheckEJConnection              , fset=Set_CheckEJConnection              )
    CheckFMConnection               = property(fget=Get_CheckFMConnection              , fset=Set_CheckFMConnection              )
    LDProtocolType                  = property(fget=Get_LDProtocolType                 , fset=Set_LDProtocolType                 )
    LastPrintResult                 = property(fget=Get_LastPrintResult                , fset=None                               )
    UseSlipCheck                    = property(fget=Get_UseSlipCheck                   , fset=Set_UseSlipCheck                   )
    TypeOfLastEntryFMEx             = property(fget=Get_TypeOfLastEntryFMEx            , fset=None                               )
    AutoSensorValues                = property(fget=Get_AutoSensorValues               , fset=Set_AutoSensorValues               )
    AutoStartSearch                 = property(fget=Get_AutoStartSearch                , fset=Set_AutoStartSearch                )
    SearchTimeout                   = property(fget=Get_SearchTimeout                  , fset=Set_SearchTimeout                  )
    TCPConnectionTimeout            = property(fget=Get_TCPConnectionTimeout           , fset=Set_TCPConnectionTimeout           )
    CustomerCode                    = property(fget=Get_CustomerCode                   , fset=Set_CustomerCode                   )
    PermitActivizationCode          = property(fget=Get_PermitActivizationCode         , fset=Set_PermitActivizationCode         )
    ActivizationStatus              = property(fget=Get_ActivizationStatus             , fset=Set_ActivizationStatus             )
    MFPStatus                       = property(fget=Get_MFPStatus                      , fset=Set_MFPStatus                      )
    KPKValue                        = property(fget=Get_KPKValue                       , fset=Set_KPKValue                       )
    ActivizationControlByte         = property(fget=Get_ActivizationControlByte        , fset=Set_ActivizationControlByte        )
    PrepareActivizationRemainCount  = property(fget=Get_PrepareActivizationRemainCount , fset=Set_PrepareActivizationRemainCount )
    AnswerCode                      = property(fget=Get_AnswerCode                     , fset=Set_AnswerCode                     )
    MFPNumber                       = property(fget=Get_MFPNumber                      , fset=Set_MFPNumber                      )
    ReadTimeout                     = property(fget=Get_ReadTimeout                    , fset=Set_ReadTimeout                    )
    IsBlockedByWrongTaxPassword     = property(fget=Get_IsBlockedByWrongTaxPassword    , fset=None                               )
    LastFMRecordType                = property(fget=Get_LastFMRecordType               , fset=None                               )
    CloudCashdeskEnabled            = property(fget=Get_CloudCashdeskEnabled           , fset=Set_CloudCashdeskEnabled           )
    ECRID                           = property(fget=Get_ECRID                          , fset=Set_ECRID                          )
    KSAInfo                         = property(fget=Get_KSAInfo                        , fset=Set_KSAInfo                        )
    BarcodeFirstLine                = property(fget=Get_BarcodeFirstLine               , fset=Set_BarcodeFirstLine               )
    SKNOError                       = property(fget=Get_SKNOError                      , fset=Set_SKNOError                      )
    SKNOIdentifier                  = property(fget=Get_SKNOIdentifier                 , fset=Set_SKNOIdentifier                 )
    SyncTimeout                     = property(fget=Get_SyncTimeout                    , fset=Set_SyncTimeout                    )
    DocumentData                    = property(fget=Get_DocumentData                   , fset=Set_DocumentData                   )
    OFDEnabled                      = property(fget=Get_OFDEnabled                     , fset=Set_OFDEnabled                     )
    ChargeValue                     = property(fget=Get_ChargeValue                    , fset=Set_ChargeValue                    )
    DiscountValue                   = property(fget=Get_DiscountValue                  , fset=Set_DiscountValue                  )
    DiscountName                    = property(fget=Get_DiscountName                   , fset=Set_DiscountName                   )
    TagDescription                  = property(fget=Get_TagDescription                 , fset=Set_TagDescription                 )
    URL                             = property(fget=Get_URL                            , fset=Set_URL                            )
    PingTime                        = property(fget=Get_PingTime                       , fset=Set_PingTime                       )
    PingResult                      = property(fget=Get_PingResult                     , fset=Set_PingResult                     )
    ICSEnabled                      = property(fget=Get_ICSEnabled                     , fset=Set_ICSEnabled                     )
    ICSPollPeriod                   = property(fget=Get_ICSPollPeriod                  , fset=Set_ICSPollPeriod                  )
    TaxValue1Enabled                = property(fget=Get_TaxValue1Enabled               , fset=Set_TaxValue1Enabled               )
    TaxValue2Enabled                = property(fget=Get_TaxValue2Enabled               , fset=Set_TaxValue2Enabled               )
    TaxValue3Enabled                = property(fget=Get_TaxValue3Enabled               , fset=Set_TaxValue3Enabled               )
    TaxValue4Enabled                = property(fget=Get_TaxValue4Enabled               , fset=Set_TaxValue4Enabled               )
    TaxValue5Enabled                = property(fget=Get_TaxValue5Enabled               , fset=Set_TaxValue5Enabled               )
    TaxValue6Enabled                = property(fget=Get_TaxValue6Enabled               , fset=Set_TaxValue6Enabled               )
    OFDReadTimeout                  = property(fget=Get_OFDReadTimeout                 , fset=Set_OFDReadTimeout                 )
    DBFilePath                      = property(fget=Get_DBFilePath                     , fset=Set_DBFilePath                     )
    KKTLicense                      = property(fget=Get_KKTLicense                     , fset=Set_KKTLicense                     )
    LicenseNumber                   = property(fget=Get_LicenseNumber                  , fset=Set_LicenseNumber                  )
    PUKCode                         = property(fget=Get_PUKCode                        , fset=Set_PUKCode                        )
    OFDExchangeSuspended            = property(fget=Get_OFDExchangeSuspended           , fset=Set_OFDExchangeSuspended           )
    Discount1                       = property(fget=Get_Discount1                      , fset=Set_Discount1                      )
    Discount2                       = property(fget=Get_Discount2                      , fset=Set_Discount2                      )
    Discount3                       = property(fget=Get_Discount3                      , fset=Set_Discount3                      )
    Discount4                       = property(fget=Get_Discount4                      , fset=Set_Discount4                      )
    UseTaxDiscountBel               = property(fget=Get_UseTaxDiscountBel              , fset=Set_UseTaxDiscountBel              )
    Summ1AsString                   = property(fget=Get_Summ1AsString                  , fset=None                               )
    Summ2AsString                   = property(fget=Get_Summ2AsString                  , fset=None                               )
    Summ3AsString                   = property(fget=Get_Summ3AsString                  , fset=None                               )
    Summ4AsString                   = property(fget=Get_Summ4AsString                  , fset=None                               )
    DBDocType                       = property(fget=Get_DBDocType                      , fset=Set_DBDocType                      )
    OPBarcodeInputType              = property(fget=Get_OPBarcodeInputType             , fset=Set_OPBarcodeInputType             )
    OPIdPayment                     = property(fget=Get_OPIdPayment                    , fset=Set_OPIdPayment                    )
    OPRequisiteNumber               = property(fget=Get_OPRequisiteNumber              , fset=Set_OPRequisiteNumber              )
    OPRequisiteValue                = property(fget=Get_OPRequisiteValue               , fset=Set_OPRequisiteValue               )
    OPSystem                        = property(fget=Get_OPSystem                       , fset=Set_OPSystem                       )
    OPTransactionStatus             = property(fget=Get_OPTransactionStatus            , fset=Set_OPTransactionStatus            )
    OPTransactionType               = property(fget=Get_OPTransactionType              , fset=Set_OPTransactionType              )
    Token                           = property(fget=Get_Token                          , fset=Set_Token                          )
    SymbolCode                      = property(fget=Get_SymbolCode                     , fset=Set_SymbolCode                     ) # Код символа
    SymbolWidth                     = property(fget=Get_SymbolWidth                    , fset=Set_SymbolWidth                    ) # Ширина символа
    SymbolHeight                    = property(fget=Get_SymbolHeight                   , fset=Set_SymbolHeight                   ) # Высота символа
    FileType                        = property(fget=Get_FileType                       , fset=Set_FileType                       )
    DelayOnDisconnect               = property(fget=Get_DelayOnDisconnect              , fset=Set_DelayOnDisconnect              )
    GTIN                            = property(fget=Get_GTIN                           , fset=Set_GTIN                           ) # Get_GTIN Возвращает значения свойства #GTIN
    RequestDocumentType             = property(fget=Get_RequestDocumentType            , fset=Set_RequestDocumentType            )
    LastDocumentNumber              = property(fget=Get_LastDocumentNumber             , fset=Set_LastDocumentNumber             )
    FirstDocumentNumber             = property(fget=Get_FirstDocumentNumber            , fset=Set_FirstDocumentNumber            )
    BarCode                         = property(fget=Get_BarCode                        , fset=Set_BarCode                        ) # Штрих-код, печатаемый на чеке
    BatteryVoltage                  = property(fget=Get_BatteryVoltage                 , fset=None                               ) # Напряжение на батарейке
    BaudRate                        = property(fget=Get_BaudRate                       , fset=Set_BaudRate                       ) # Скорость обмена
    Change                          = property(fget=Get_Change                         , fset=None                               ) # Сдача
    CheckType                       = property(fget=Get_CheckType                      , fset=Set_CheckType                      ) # Тип чека
    ComNumber                       = property(fget=Get_ComNumber                      , fset=Set_ComNumber                      ) # Номер Com-порта
    ContentsOfCashRegister          = property(fget=Get_ContentsOfCashRegister         , fset=None                               ) # Содержимое денежного регистра
    ContentsOfOperationRegister     = property(fget=Get_ContentsOfOperationRegister    , fset=None                               ) # Содержимое операционного регистра
    CutType                         = property(fget=Get_CutType                        , fset=Set_CutType                        ) # Тип отрезки
    DataBlock                       = property(fget=Get_DataBlock                      , fset=None                               ) # Блок данных
    DataBlockHex                    = property(fget=Get_DataBlockHex                   , fset=None                               ) # Возвращает значение свойства #DataBlockHex
    DataBlockNumber                 = property(fget=Get_DataBlockNumber                , fset=None                               ) # Номер блока данных
    Date                            = property(fget=Get_Date                           , fset=Set_Date                           ) # Внутренняя дата ККМ
    Department                      = property(fget=Get_Department                     , fset=Set_Department                     ) # Номер отдела (секции)
    DeviceCode                      = property(fget=Get_DeviceCode                     , fset=Set_DeviceCode                     ) # Код устройства
    DeviceCodeDescription           = property(fget=Get_DeviceCodeDescription          , fset=None                               ) # Описание устройства
    DiscountOnCheck                 = property(fget=Get_DiscountOnCheck                , fset=Set_DiscountOnCheck                ) # Скидка на чек
    DocumentName                    = property(fget=Get_DocumentName                   , fset=Set_DocumentName                   ) # Наименование документа
    DocumentNumber                  = property(fget=Get_DocumentNumber                 , fset=Set_DocumentNumber                 ) # Номер документа
    DrawerNumber                    = property(fget=Get_DrawerNumber                   , fset=Set_DrawerNumber                   ) # Номер денежного ящика
    ECRAdvancedMode                 = property(fget=Get_ECRAdvancedMode                , fset=None                               ) # Подрежим ККМ
    ECRBuild                        = property(fget=Get_ECRBuild                       , fset=None                               ) # Номер сборки ПО ККМ
    ECRFlags                        = property(fget=Get_ECRFlags                       , fset=None                               ) # Флаги ККМ
    ReceiptRibbonIsPresent          = property(fget=Get_ReceiptRibbonIsPresent         , fset=None                               ) # Рулон чековой ленты есть
    JournalRibbonIsPresent          = property(fget=Get_JournalRibbonIsPresent         , fset=None                               ) # Рулон операционного журнала есть
    SlipDocumentIsPresent           = property(fget=Get_SlipDocumentIsPresent          , fset=None                               ) # Подкладной документ есть
    SlipDocumentIsMoving            = property(fget=Get_SlipDocumentIsMoving           , fset=None                               ) # Подкладной документ проходит
    PointPosition                   = property(fget=Get_PointPosition                  , fset=Set_PointPosition                  ) # Положение точки
    EKLZIsPresent                   = property(fget=Get_EKLZIsPresent                  , fset=None                               ) # ЭКЛЗ есть
    JournalRibbonOpticalSensor      = property(fget=Get_JournalRibbonOpticalSensor     , fset=None                               ) # Оптический датчик операционного журнала
    ReceiptRibbonOpticalSensor      = property(fget=Get_ReceiptRibbonOpticalSensor     , fset=None                               ) # Оптический датчик чековой ленты
    JournalRibbonLever              = property(fget=Get_JournalRibbonLever             , fset=None                               ) # Рычаг термоголовки операционного журнала
    ReceiptRibbonLever              = property(fget=Get_ReceiptRibbonLever             , fset=None                               ) # Рычаг термоголовки чековой ленты
    LidPositionSensor               = property(fget=Get_LidPositionSensor              , fset=None                               ) # Датчик крышки корпуса
    IsDrawerOpen                    = property(fget=Get_IsDrawerOpen                   , fset=None                               ) # Денежный ящик открыт
    IsPrinterRightSensorFailure     = property(fget=Get_IsPrinterRightSensorFailure    , fset=None                               ) # Отказ правого датчика печатающего механизма
    IsPrinterLeftSensorFailure      = property(fget=Get_IsPrinterLeftSensorFailure     , fset=None                               ) # Отказ левого датчика печатающего механизма
    IsEKLZOverflow                  = property(fget=Get_IsEKLZOverflow                 , fset=None                               ) # Переполнение ЭКЛЗ
    QuantityPointPosition           = property(fget=Get_QuantityPointPosition          , fset=None                               ) # Положение точки в количестве
    SKNOStatus                      = property(fget=Get_SKNOStatus                     , fset=Set_SKNOStatus                     ) # Статус СКНО
    ECRMode                         = property(fget=Get_ECRMode                        , fset=None                               ) # Режим ККМ
    ECRMode8Status                  = property(fget=Get_ECRMode8Status                 , fset=None                               ) # Статус 8 режима
    ECRModeDescription              = property(fget=Get_ECRModeDescription             , fset=None                               ) # Описание режима ККМ
    ECRSoftDate                     = property(fget=Get_ECRSoftDate                    , fset=None                               ) # Дата ПО ККМ
    ECRSoftVersion                  = property(fget=Get_ECRSoftVersion                 , fset=None                               ) # Версия ПО ККТ
    FieldName                       = property(fget=Get_FieldName                      , fset=None                               ) # Название поля
    FieldNumber                     = property(fget=Get_FieldNumber                    , fset=Set_FieldNumber                    ) # Номер поля
    FieldSize                       = property(fget=Get_FieldSize                      , fset=None                               ) # Размер поля
    FieldType                       = property(fget=Get_FieldType                      , fset=None                               ) # Тип поля
    FirstLineNumber                 = property(fget=Get_FirstLineNumber                , fset=Set_FirstLineNumber                ) # Номер первой линии
    FirstSessionDate                = property(fget=Get_FirstSessionDate               , fset=Set_FirstSessionDate               ) # Дата первой смены
    FirstSessionNumber              = property(fget=Get_FirstSessionNumber             , fset=Set_FirstSessionNumber             ) # Номер первой смены
    FMBuild                         = property(fget=Get_FMBuild                        , fset=None                               ) # Сборка ФП
    FMFlags                         = property(fget=Get_FMFlags                        , fset=None                               ) # Флаги ФП
    FM1IsPresent                    = property(fget=Get_FM1IsPresent                   , fset=None                               ) # ФП1 есть
    FM2IsPresent                    = property(fget=Get_FM2IsPresent                   , fset=None                               ) # ФП2 есть
    LicenseIsPresent                = property(fget=Get_LicenseIsPresent               , fset=None                               ) # Лицензия есть
    FMOverflow                      = property(fget=Get_FMOverflow                     , fset=None                               ) # Переполнение ФП
    IsBatteryLow                    = property(fget=Get_IsBatteryLow                   , fset=None                               ) # Низкое напряжение на батарее
    IsLastFMRecordCorrupted         = property(fget=Get_IsLastFMRecordCorrupted        , fset=None                               ) # Последняя запись в ФП испорчена
    IsFMSessionOpen                 = property(fget=Get_IsFMSessionOpen                , fset=None                               ) # Смена в ФП открыта
    IsFM24HoursOver                 = property(fget=Get_IsFM24HoursOver                , fset=None                               ) # 24 часа в ФП кончились
    FMSoftDate                      = property(fget=Get_FMSoftDate                     , fset=None                               ) # Дата ПО ФП
    FMSoftVersion                   = property(fget=Get_FMSoftVersion                  , fset=None                               ) # Версия ПО ФП
    FreeRecordInFM                  = property(fget=Get_FreeRecordInFM                 , fset=None                               ) # Количество свободных записей в ФП
    FreeRegistration                = property(fget=Get_FreeRegistration               , fset=None                               ) # Количество оставшихся перерегистраций
    INN                             = property(fget=Get_INN                            , fset=Set_INN                            ) # ИНН
    LastLineNumber                  = property(fget=Get_LastLineNumber                 , fset=Set_LastLineNumber                 ) # Номер последней линии
    LastSessionDate                 = property(fget=Get_LastSessionDate                , fset=Set_LastSessionDate                ) # Дата последней смены
    LastSessionNumber               = property(fget=Get_LastSessionNumber              , fset=Set_LastSessionNumber              ) # Номер последней смены
    License                         = property(fget=Get_License                        , fset=Set_License                        ) # Лицензия
    LineData                        = property(fget=Get_LineData                       , fset=Set_LineData                       ) # Графическая информация
    LineNumber                      = property(fget=Get_LineNumber                     , fset=Set_LineNumber                     ) # Номер линии
    LogicalNumber                   = property(fget=Get_LogicalNumber                  , fset=None                               ) # Номер в зале
    MAXValueOfField                 = property(fget=Get_MAXValueOfField                , fset=None                               ) # Максимальное значение поля
    MINValueOfField                 = property(fget=Get_MINValueOfField                , fset=None                               ) # Минимальное значение поля
    NameCashReg                     = property(fget=Get_NameCashReg                    , fset=None                               ) # Название денежного регистра
    NameOperationReg                = property(fget=Get_NameOperationReg               , fset=None                               ) # Название операционного регистра
    NewPasswordTI                   = property(fget=Get_NewPasswordTI                  , fset=Set_NewPasswordTI                  ) # Новый пароль НИ
    OpenDocumentNumber              = property(fget=Get_OpenDocumentNumber             , fset=None                               ) # Сквозной номер документа
    OperatorNumber                  = property(fget=Get_OperatorNumber                 , fset=None                               ) # Порядковый номер оператора, чей пароль был введен
    Password                        = property(fget=Get_Password                       , fset=Set_Password                       ) # Пароль для исполнения метода драйвера
    PortNumber                      = property(fget=Get_PortNumber                     , fset=Set_PortNumber                     ) # Номер порта
    Price                           = property(fget=Get_Price                          , fset=Set_Price                          ) # Цена
    Quantity                        = property(fget=Get_Quantity                       , fset=Set_Quantity                       ) # Количество
    QuantityOfOperations            = property(fget=Get_QuantityOfOperations           , fset=None                               ) # Количество операций
    RegisterNumber                  = property(fget=Get_RegisterNumber                 , fset=Set_RegisterNumber                 ) # Номер регистра
    RegistrationNumber              = property(fget=Get_RegistrationNumber             , fset=Set_RegistrationNumber             ) # Количество перерегистраций
    ReportType                      = property(fget=Get_ReportType                     , fset=Set_ReportType                     ) # Тип отчёта
    ResultCode                      = property(fget=Get_ResultCode                     , fset=None                               ) # Код ошибки
    ResultCodeDescription           = property(fget=Get_ResultCodeDescription          , fset=None                               ) # Описание кода ошибки
    RNM                             = property(fget=Get_RNM                            , fset=Set_RNM                            ) # РНМ
    RowNumber                       = property(fget=Get_RowNumber                      , fset=Set_RowNumber                      ) # Номер ряда
    RunningPeriod                   = property(fget=Get_RunningPeriod                  , fset=Set_RunningPeriod                  ) # Период прогона
    SerialNumber                    = property(fget=Get_SerialNumber                   , fset=Set_SerialNumber                   ) # Заводской номер
    SessionNumber                   = property(fget=Get_SessionNumber                  , fset=Set_SessionNumber                  ) # Номер смены
    StringForPrinting               = property(fget=Get_StringForPrinting              , fset=Set_StringForPrinting              ) # Строка для печати
    StringQuantity                  = property(fget=Get_StringQuantity                 , fset=Set_StringQuantity                 ) # Количество строк
    Summ1                           = property(fget=Get_Summ1                          , fset=Set_Summ1                          ) # Сумма1
    Summ2                           = property(fget=Get_Summ2                          , fset=Set_Summ2                          ) # Сумма2
    Summ3                           = property(fget=Get_Summ3                          , fset=Set_Summ3                          ) # Сумма3
    Summ4                           = property(fget=Get_Summ4                          , fset=Set_Summ4                          ) # Сумма4
    TableName                       = property(fget=Get_TableName                      , fset=None                               ) # Название таблицы
    TableNumber                     = property(fget=Get_TableNumber                    , fset=Set_TableNumber                    ) # Номер таблицы
    Tax1                            = property(fget=Get_Tax1                           , fset=Set_Tax1                           ) # Налог1
    Tax2                            = property(fget=Get_Tax2                           , fset=Set_Tax2                           ) # Налог2
    Tax3                            = property(fget=Get_Tax3                           , fset=Set_Tax3                           ) # Налог3
    Tax4                            = property(fget=Get_Tax4                           , fset=Set_Tax4                           ) # Налог4
    Time                            = property(fget=Get_Time                           , fset=Set_Time                           ) # Время
    Timeout                         = property(fget=Get_Timeout                        , fset=Set_Timeout                        ) # Тайм-аут приема байта
    TimeStr                         = property(fget=Get_TimeStr                        , fset=Set_TimeStr                        ) # Время cтрока
    TransferBytes                   = property(fget=Get_TransferBytes                  , fset=Set_TransferBytes                  ) # Посылаемые байты
    TypeOfLastEntryFM               = property(fget=Get_TypeOfLastEntryFM              , fset=None                               ) # Тип последней записи ФП
    TypeOfSumOfEntriesFM            = property(fget=Get_TypeOfSumOfEntriesFM           , fset=Set_TypeOfSumOfEntriesFM           ) # Тип суммы записей ФП
    UCodePage                       = property(fget=Get_UCodePage                      , fset=None                               ) # Кодовая страница
    UDescription                    = property(fget=Get_UDescription                   , fset=None                               ) # Название устройства
    UMajorProtocolVersion           = property(fget=Get_UMajorProtocolVersion          , fset=None                               ) # Версия протокола
    UMajorType                      = property(fget=Get_UMajorType                     , fset=None                               ) # Тип устрйоства
    UMinorProtocolVersion           = property(fget=Get_UMinorProtocolVersion          , fset=None                               ) # Подверсия протокола
    UMinorType                      = property(fget=Get_UMinorType                     , fset=None                               ) # Подтип устройства
    UModel                          = property(fget=Get_UModel                         , fset=None                               ) # Модель устройства
    UseJournalRibbon                = property(fget=Get_UseJournalRibbon               , fset=Set_UseJournalRibbon               ) # Использовать ленту операционного журнала
    UseReceiptRibbon                = property(fget=Get_UseReceiptRibbon               , fset=Set_UseReceiptRibbon               ) # Использовать чековую ленту
    UseSlipDocument                 = property(fget=Get_UseSlipDocument                , fset=Set_UseSlipDocument                ) # Использовать подкладной документ
    ValueOfFieldInteger             = property(fget=Get_ValueOfFieldInteger            , fset=Set_ValueOfFieldInteger            ) # Значение поля целое
    ValueOfFieldString              = property(fget=Get_ValueOfFieldString             , fset=Set_ValueOfFieldString             ) # Значение поля строка
    FontType                        = property(fget=Get_FontType                       , fset=Set_FontType                       ) # Тип шрифта
    EKLZResultCode                  = property(fget=Get_EKLZResultCode                 , fset=Set_EKLZResultCode                 ) # Код ошибки ЭКЛЗ
    FMResultCode                    = property(fget=Get_FMResultCode                   , fset=None                               ) # Код ошибки ФП
    PowerSourceVoltage              = property(fget=Get_PowerSourceVoltage             , fset=None                               ) # Напряжение источника питания
    ECRModeStatus                   = property(fget=Get_ECRModeStatus                  , fset=None                               ) # Статус режима
    ComputerName                    = property(fget=Get_ComputerName                   , fset=Set_ComputerName                   ) # Имя компьютера
    PrintWidth                      = property(fget=Get_PrintWidth                     , fset=None                               ) # Ширина печати
    CharWidth                       = property(fget=Get_CharWidth                      , fset=None                               ) # Ширина символа
    CharHeight                      = property(fget=Get_CharHeight                     , fset=None                               ) # Высота символа
    FontCount                       = property(fget=Get_FontCount                      , fset=None                               ) # Количество шрифтов
    ConnectionType                  = property(fget=Get_ConnectionType                 , fset=Set_ConnectionType                 ) # Тип подключения к устройству
    TCPPort                         = property(fget=Get_TCPPort                        , fset=Set_TCPPort                        ) # Порт TCP
    IPAddress                       = property(fget=Get_IPAddress                      , fset=Set_IPAddress                      ) # IP адрес
    UseIPAddress                    = property(fget=Get_UseIPAddress                   , fset=Set_UseIPAddress                   ) # Использовать IP адрес
    SysAdminPassword                = property(fget=Get_SysAdminPassword               , fset=Set_SysAdminPassword               ) # Пароль системного администратора
    OperationType                   = property(fget=Get_OperationType                  , fset=Set_OperationType                  ) # Тип операции
    PresenterIn                     = property(fget=Get_PresenterIn                    , fset=None                               ) # Вход накопителя
    PresenterOut                    = property(fget=Get_PresenterOut                   , fset=None                               ) # Выход накопителя
    SCPassword                      = property(fget=Get_SCPassword                     , fset=Set_SCPassword                     ) # Пароль ЦТО
    NewSCPassword                   = property(fget=Get_NewSCPassword                  , fset=Set_NewSCPassword                  ) # Новый пароль ЦТО
    BarcodeAlignment                = property(fget=Get_BarcodeAlignment               , fset=Set_BarcodeAlignment               ) # Выравнивание штрих-кода
    FinishDocumentMode              = property(fget=Get_FinishDocumentMode             , fset=Set_FinishDocumentMode             ) # Режим завершения документа
    PrintBarcodeText                = property(fget=Get_PrintBarcodeText               , fset=Set_PrintBarcodeText               ) # Печать текста штрих-кода
    FileName                        = property(fget=Get_FileName                       , fset=Set_FileName                       ) # Имя файла
    DriverMajorVersion              = property(fget=Get_DriverMajorVersion             , fset=None                               ) # Номер версии драйвера
    DriverMinorVersion              = property(fget=Get_DriverMinorVersion             , fset=None                               ) # Номер подверсии драйвера
    DriverRelease                   = property(fget=Get_DriverRelease                  , fset=None                               ) # Номер релиза драйвера
    DriverBuild                     = property(fget=Get_DriverBuild                    , fset=None                               ) # Номер сборки драйвера
    BlockType                       = property(fget=Get_BlockType                      , fset=Set_BlockType                      ) # Тип блока
    BlockNumber                     = property(fget=Get_BlockNumber                    , fset=Set_BlockNumber                    ) # Номер блока
    BlockDataHex                    = property(fget=Get_BlockDataHex                   , fset=Set_BlockDataHex                   ) # Блок данных для загрузки, в виде HEX строки
    BarcodeType                     = property(fget=Get_BarcodeType                    , fset=Set_BarcodeType                    ) # Тип штрих-кода
    BarWidth                        = property(fget=Get_BarWidth                       , fset=Set_BarWidth                       ) # Ширина вертикальной линии в штрих-коде
    CapGetShortECRStatus            = property(fget=Get_CapGetShortECRStatus           , fset=None                               ) # Поддерживается короткий запрос состояния
    WaitForPrintingDelay            = property(fget=Get_WaitForPrintingDelay           , fset=Set_WaitForPrintingDelay           ) # Задержка ожидания печати
    LineSwapBytes                   = property(fget=Get_LineSwapBytes                  , fset=Set_LineSwapBytes                  ) # Переворачивать байты при печати линии
    LineDataHex                     = property(fget=Get_LineDataHex                    , fset=Set_LineDataHex                    ) # Графическая информация HEX
    CenterImage                     = property(fget=Get_CenterImage                    , fset=Set_CenterImage                    ) # Центрировать картинку
    ShowProgress                    = property(fget=Get_ShowProgress                   , fset=Set_ShowProgress                   ) # Показывать прогресс
    ModelParamValue                 = property(fget=Get_ModelParamValue                , fset=None                               ) # Значение параметра модели
    ModelParamNumber                = property(fget=Get_ModelParamNumber               , fset=Set_ModelParamNumber               ) # Номер параметра модели
    ConnectionTimeout               = property(fget=Get_ConnectionTimeout              , fset=Set_ConnectionTimeout              ) # Таймаут подключения
    ModelParamDescription           = property(fget=Get_ModelParamDescription          , fset=None                               ) # Описание параметра модели
    DriverVersion                   = property(fget=Get_DriverVersion                  , fset=None                               ) # Версия драйвера
    BarcodeParameter1               = property(fget=Get_BarcodeParameter1              , fset=Set_BarcodeParameter1              ) # Параметр штрих-кода 1
    BarcodeParameter2               = property(fget=Get_BarcodeParameter2              , fset=Set_BarcodeParameter2              ) # Параметр штрих-кода 2
    BarcodeParameter3               = property(fget=Get_BarcodeParameter3              , fset=Set_BarcodeParameter3              ) # Параметр штрих-кода 3
    BarcodeParameter4               = property(fget=Get_BarcodeParameter4              , fset=Set_BarcodeParameter4              ) # Параметр штрих-кода 4
    BarcodeParameter5               = property(fget=Get_BarcodeParameter5              , fset=Set_BarcodeParameter5              ) # Параметр штрих-кода 5
    BarcodeStartBlockNumber         = property(fget=Get_BarcodeStartBlockNumber        , fset=Set_BarcodeStartBlockNumber        ) # Номер начального блока данных
    CarryStrings                    = property(fget=Get_CarryStrings                   , fset=Set_CarryStrings                   ) # Переносить строки при печати
    DelayedPrint                    = property(fget=Get_DelayedPrint                   , fset=Set_DelayedPrint                   ) # Отложенная печать
    ErrorCode                       = property(fget=Get_ErrorCode                      , fset=Set_ErrorCode                      ) # Код ошибки
    ErrorDescription                = property(fget=Get_ErrorDescription               , fset=None                               ) # Описание ошибки
    SwapBytesMode                   = property(fget=Get_SwapBytesMode                  , fset=Set_SwapBytesMode                  ) # Режим переворачивания байта
    BarcodeHex                      = property(fget=Get_BarcodeHex                     , fset=Set_BarcodeHex                     ) # Строка с двоичными данными штрих-кода
    ProtocolType                    = property(fget=Get_ProtocolType                   , fset=Set_ProtocolType                   ) # Тип протокола
    Summ5                           = property(fget=Get_Summ5                          , fset=Set_Summ5                          ) # Сумма5
    Summ6                           = property(fget=Get_Summ6                          , fset=Set_Summ6                          ) # Сумма6
    Summ7                           = property(fget=Get_Summ7                          , fset=Set_Summ7                          ) # Сумма7
    Summ8                           = property(fget=Get_Summ8                          , fset=Set_Summ8                          ) # Сумма8
    Summ9                           = property(fget=Get_Summ9                          , fset=Set_Summ9                          ) # Сумма9
    Summ10                          = property(fget=Get_Summ10                         , fset=Set_Summ10                         ) # Сумма10
    Summ11                          = property(fget=Get_Summ11                         , fset=Set_Summ11                         ) # Сумма11
    Summ12                          = property(fget=Get_Summ12                         , fset=Set_Summ12                         ) # Сумма12
    Summ13                          = property(fget=Get_Summ13                         , fset=Set_Summ13                         ) # Сумма13
    Summ14                          = property(fget=Get_Summ14                         , fset=Set_Summ14                         ) # Сумма14
    Summ15                          = property(fget=Get_Summ15                         , fset=Set_Summ15                         ) # Сумма15
    Summ16                          = property(fget=Get_Summ16                         , fset=Set_Summ16                         ) # Сумма16
    NameCashRegEx                   = property(fget=Get_NameCashRegEx                  , fset=None                               ) # Имя расширенного денежного регистра
    RequestType                     = property(fget=Get_RequestType                    , fset=Set_RequestType                    ) # Тип запроса
    HorizScale                      = property(fget=Get_HorizScale                     , fset=Set_HorizScale                     ) # Горизонтальное масштабирование
    VertScale                       = property(fget=Get_VertScale                      , fset=Set_VertScale                      ) # Вертикальное масштабирование
    GraphBufferType                 = property(fget=Get_GraphBufferType                , fset=Set_GraphBufferType                ) # Тип графического буфера
    LineLength                      = property(fget=Get_LineLength                     , fset=Set_LineLength                     ) # Длина линии
    FNCurrentDocument               = property(fget=Get_FNCurrentDocument              , fset=Set_FNCurrentDocument              ) # Текущий документ ФН
    FNDocumentData                  = property(fget=Get_FNDocumentData                 , fset=Set_FNDocumentData                 ) # Данные документа ФН
    FNLifeState                     = property(fget=Get_FNLifeState                    , fset=Set_FNLifeState                    ) # Состояние жизни ФН
    FNSessionState                  = property(fget=Get_FNSessionState                 , fset=Set_FNSessionState                 ) # Состояние смены ФН
    FNSoftVersion                   = property(fget=Get_FNSoftVersion                  , fset=Set_FNSoftVersion                  ) # ФН версия
    FNSoftType                      = property(fget=Get_FNSoftType                     , fset=None                               ) # Тип программного обеспечения ФН
    FNWarningFlags                  = property(fget=Get_FNWarningFlags                 , fset=Set_FNWarningFlags                 ) # Флаги предупреждения ФН
    FiscalSign                      = property(fget=Get_FiscalSign                     , fset=Set_FiscalSign                     ) # Фискальный признак
    FiscalSignAsString              = property(fget=Get_FiscalSignAsString             , fset=None                               ) # Фискальный признак документа в виде строки
    KKTRegistrationNumber           = property(fget=Get_KKTRegistrationNumber          , fset=Set_KKTRegistrationNumber          ) # Регистрационный номер ККТ
    TaxType                         = property(fget=Get_TaxType                        , fset=Set_TaxType                        ) # Код налогообложения
    WorkMode                        = property(fget=Get_WorkMode                       , fset=Set_WorkMode                       ) # Режим работы
    DocumentType                    = property(fget=Get_DocumentType                   , fset=Set_DocumentType                   ) # Тип документа ФН
    OFDTicketReceived               = property(fget=Get_OFDTicketReceived              , fset=Set_OFDTicketReceived              ) # Получена ли квитанция из ОФД
    TLVData                         = property(fget=Get_TLVData                        , fset=Set_TLVData                        ) # Данные TLV
    DataBlockSize                   = property(fget=Get_DataBlockSize                  , fset=Set_DataBlockSize                  ) # Размер блока данных
    DataLength                      = property(fget=Get_DataLength                     , fset=Set_DataLength                     ) # Длина данных
    OFDPort                         = property(fget=Get_OFDPort                        , fset=Set_OFDPort                        ) # Порт ОФД
    OFDServer                       = property(fget=Get_OFDServer                      , fset=Set_OFDServer                      ) # Адрес сервера ОФД
    OFDPollPeriod                   = property(fget=Get_OFDPollPeriod                  , fset=Set_OFDPollPeriod                  ) # Пауза между сессиями обмена с ОФД
    DocumentCount                   = property(fget=Get_DocumentCount                  , fset=Set_DocumentCount                  ) # Количество документов
    ReceiptNumber                   = property(fget=Get_ReceiptNumber                  , fset=Set_ReceiptNumber                  ) # Номер чека
    InfoExchangeStatus              = property(fget=Get_InfoExchangeStatus             , fset=Set_InfoExchangeStatus             ) # Статус информационного обмена
    MessageState                    = property(fget=Get_MessageState                   , fset=Set_MessageState                   ) # Состояние сообщения
    MessageCount                    = property(fget=Get_MessageCount                   , fset=Set_MessageCount                   ) # Количество сообщений
    MessageNumber                   = property(fget=Get_MessageNumber                  , fset=Set_MessageNumber                  ) # Номер сообщения
    ReportTypeInt                   = property(fget=Get_ReportTypeInt                  , fset=Set_ReportTypeInt                  ) # Тип отчета
    TaxValue                        = property(fget=Get_TaxValue                       , fset=Set_TaxValue                       ) # Сумма налога
    RegistrationReasonCode          = property(fget=Get_RegistrationReasonCode         , fset=Set_RegistrationReasonCode         ) # Код причины перерегистрации
    CustomerEmail                   = property(fget=Get_CustomerEmail                  , fset=Set_CustomerEmail                  ) # EmailПользователя
    Date2                           = property(fget=Get_Date2                          , fset=Set_Date2                          ) # Дата2
    Time2                           = property(fget=Get_Time2                          , fset=Set_Time2                          ) # Время2
    FiscalSignOFD                   = property(fget=Get_FiscalSignOFD                  , fset=Set_FiscalSignOFD                  ) # Фискальный признак ОФД
    AutoOpenSession                 = property(fget=Get_AutoOpenSession                , fset=Set_AutoOpenSession                ) # Автоматическое открытие смены, если закрыта
    TagNumber                       = property(fget=Get_TagNumber                      , fset=Set_TagNumber                      ) # Номер тега
    TagType                         = property(fget=Get_TagType                        , fset=Set_TagType                        ) # Тип тега
    TagValueInt                     = property(fget=Get_TagValueInt                    , fset=Set_TagValueInt                    ) # Значение целочисленного тега
    TagValueStr                     = property(fget=Get_TagValueStr                    , fset=Set_TagValueStr                    ) # Строковое значение тега
    TagValueFVLN                    = property(fget=Get_TagValueFVLN                   , fset=Set_TagValueFVLN                   ) # Значение тега с плавающей запятой
    TagValueDateTime                = property(fget=Get_TagValueDateTime               , fset=Set_TagValueDateTime               ) # Значение тега с датой и временем
    TagValueBin                     = property(fget=Get_TagValueBin                    , fset=Set_TagValueBin                    ) # Значение тега с бинарными данными
    TagValueLength                  = property(fget=Get_TagValueLength                 , fset=Set_TagValueLength                 ) # Количество байт длины значения тега
    ShowTagNumber                   = property(fget=Get_ShowTagNumber                  , fset=Set_ShowTagNumber                  ) # Выводить номер тэга
    RoundingSumm                    = property(fget=Get_RoundingSumm                   , fset=Set_RoundingSumm                   ) # Сумма округления
    TaxValue1                       = property(fget=Get_TaxValue1                      , fset=Set_TaxValue1                      ) # Значение налога 1
    TaxValue2                       = property(fget=Get_TaxValue2                      , fset=Set_TaxValue2                      ) # Значение налога 2
    TaxValue3                       = property(fget=Get_TaxValue3                      , fset=Set_TaxValue3                      ) # Значение налога 3
    TaxValue4                       = property(fget=Get_TaxValue4                      , fset=Set_TaxValue4                      ) # Значение налога 4
    TaxValue5                       = property(fget=Get_TaxValue5                      , fset=Set_TaxValue5                      ) # Значение налога 5
    TaxValue6                       = property(fget=Get_TaxValue6                      , fset=Set_TaxValue6                      ) # Значение налога 6
    Summ1Enabled                    = property(fget=Get_Summ1Enabled                   , fset=Set_Summ1Enabled                   ) # Сумма1 вкл
    TaxValueEnabled                 = property(fget=Get_TaxValueEnabled                , fset=Set_TaxValueEnabled                ) # Значение налога1 вкл
    PaymentTypeSign                 = property(fget=Get_PaymentTypeSign                , fset=Set_PaymentTypeSign                ) # Признак способа расчета
    PaymentItemSign                 = property(fget=Get_PaymentItemSign                , fset=Set_PaymentItemSign                ) # Признак предмета расчета
    CalculationSign                 = property(fget=Get_CalculationSign                , fset=Set_CalculationSign                ) # Признак расчета
    CorrectionType                  = property(fget=Get_CorrectionType                 , fset=Set_CorrectionType                 ) # Тип коррекции
    AutoEoD                         = property(fget=Get_AutoEoD                        , fset=Set_AutoEoD                        ) # Автоматичесий обмен с ОФД средствами драйвера
    AutoOFDExchange                 = property(fget=Get_AutoOFDExchange                , fset=Set_AutoOFDExchange                ) # дублирует свойство
    EmailAddress                    = property(fget=Get_EmailAddress                   , fset=Set_EmailAddress                   ) # Еmail отправителя
    TagID                           = property(fget=Get_TagID                          , fset=Set_TagID                          ) # Идентификатор STLV-тега
    ConnectionURI                   = property(fget=Get_ConnectionURI                  , fset=Set_ConnectionURI                  ) # Возвращает значение свойства #ConnectionURI
    BlockData                       = property(fget=Get_BlockData                      , fset=Set_BlockData                      ) # Блок данных для загрузки
    WrapStrings                     = property(fget=Get_WrapStrings                    , fset=Set_WrapStrings                    ) # Переносить строки
    MarkingType                     = property(fget=Get_MarkingType                    , fset=Set_MarkingType                    ) # Возвращает значение свойства #MarkingType
    LoaderVersion                   = property(fget=Get_LoaderVersion                  , fset=None                               ) # Не печатать чек
    WorkModeEx                      = property(fget=Get_WorkModeEx                     , fset=Set_WorkModeEx                     ) # Расширенные признаки работы ККТ
    INNOFD                          = property(fget=Get_INNOFD                         , fset=Set_INNOFD                         ) # ИНН ОФД
    RegistrationReasonCodeEx        = property(fget=Get_RegistrationReasonCodeEx       , fset=Set_RegistrationReasonCodeEx       ) # Код причины изменения сведений о ККТ
    SkipPrint                       = property(fget=Get_SkipPrint                      , fset=Set_SkipPrint                      ) # Не печатать чек
    DigitalSign                     = property(fget=Get_DigitalSign                    , fset=Set_DigitalSign                    ) # Цифровая подпись лицензии
    DeviceFunctionNumber            = property(fget=Get_DeviceFunctionNumber           , fset=Set_DeviceFunctionNumber           ) # Номер функции устройства
    ValueOfFunctionInteger          = property(fget=Get_ValueOfFunctionInteger         , fset=Set_ValueOfFunctionInteger         ) # Значение фунции устройства, в зависимости от свойства
    ValueOfFunctionString           = property(fget=Get_ValueOfFunctionString          , fset=Set_ValueOfFunctionString          ) # Значение функции устройства строковое
    EnableCashcoreMarkCompatibility = property(fget=Get_EnableCashcoreMarkCompatibility, fset=Set_EnableCashcoreMarkCompatibility) # Режим совместимости КЯ при печати признака маркировки
    CheckItemLocalError             = property(fget=Get_CheckItemLocalError            , fset=Set_CheckItemLocalError            ) # Возвращает значение свойства #CheckItemLocalError
    MarkingTypeEx                   = property(fget=Get_MarkingTypeEx                  , fset=Set_MarkingTypeEx                  ) # Возвращает значение свойства #MarkingTypeEx
    MeasureUnit                     = property(fget=Get_MeasureUnit                    , fset=Set_MeasureUnit                    ) # Возвращает значение свойства #MeasureUnit
    DivisionalQuantity              = property(fget=Get_DivisionalQuantity             , fset=Set_DivisionalQuantity             ) # Возвращает значение свойства #DivisionalQuantity
    Numerator                       = property(fget=Get_Numerator                      , fset=Set_Numerator                      ) # Возвращает значение свойства #Numerator
    Denominator                     = property(fget=Get_Denominator                    , fset=Set_Denominator                    ) # Возвращает значение свойства #Denominator
    FreeMemorySize                  = property(fget=Get_FreeMemorySize                 , fset=Set_FreeMemorySize                 ) # Размер свободной памяти
    MCCheckStatus                   = property(fget=Get_MCCheckStatus                  , fset=Set_MCCheckStatus                  ) # Состояние проверки КМ
    MCNotificationStatus            = property(fget=Get_MCNotificationStatus           , fset=Set_MCNotificationStatus           ) # Состояние уведомления КМ
    MCCommandFlags                  = property(fget=Get_MCCommandFlags                 , fset=Set_MCCommandFlags                 ) # Флаги команд КМ
    MCCheckResultSavedCount         = property(fget=Get_MCCheckResultSavedCount        , fset=Set_MCCheckResultSavedCount        ) # Количество КМ, результаты проверки которых, сохранены в ФН
    MCRealizationCount              = property(fget=Get_MCRealizationCount             , fset=Set_MCRealizationCount             ) # Количество КМ, включенных в уведомление о реализации
    MCStorageSize                   = property(fget=Get_MCStorageSize                  , fset=Set_MCStorageSize                  ) # Заполнение области хранения маркированного товара
    CheckSum                        = property(fget=Get_CheckSum                       , fset=Set_CheckSum                       ) # Контрольная сумма
    NotificationCount               = property(fget=Get_NotificationCount              , fset=Set_NotificationCount              ) # Количество уведомлений
    NotificationNumber              = property(fget=Get_NotificationNumber             , fset=Set_NotificationNumber             ) # Номер уведомления
    NotificationSize                = property(fget=Get_NotificationSize               , fset=Set_NotificationSize               ) # Размер уведомления
    DataOffset                      = property(fget=Get_DataOffset                     , fset=Set_DataOffset                     ) # Смещение данных
    MarkingType2                    = property(fget=Get_MarkingType2                   , fset=Set_MarkingType2                   ) # Возвращает значение свойства #MarkingType2
    RandomSequence                  = property(fget=Get_RandomSequence                 , fset=Set_RandomSequence                 ) # Прочитать случайную последовательность из ФН
    RandomSequenceHex               = property(fget=Get_RandomSequenceHex              , fset=Set_RandomSequenceHex              ) # Прочитать случайную последовательность из ФН
    AuthData                        = property(fget=Get_AuthData                       , fset=Set_AuthData                       ) # Данные для авторизации
    FNArchiveType                   = property(fget=Get_FNArchiveType                  , fset=Set_FNArchiveType                  ) # Возвращает значение свойства #FNArchiveType
    MarkingOnly                     = property(fget=Get_MarkingOnly                    , fset=Set_MarkingOnly                    ) # Возвращает значение свойства #MarkingOnly
    ItemStatus                      = property(fget=Get_ItemStatus                     , fset=Set_ItemStatus                     ) # Возвращает значение свойства #ItemStatus
    CheckItemMode                   = property(fget=Get_CheckItemMode                  , fset=Set_CheckItemMode                  ) # Возвращает значение свойства #CheckItemMode
    CheckItemLocalResult            = property(fget=Get_CheckItemLocalResult           , fset=Set_CheckItemLocalResult           ) # Возвращает значение свойства #CheckItemLocalResult
    KMServerErrorCode               = property(fget=Get_KMServerErrorCode              , fset=Set_KMServerErrorCode              ) # Возвращает значение свойства #KMServerErrorCode
    KMServerCheckingStatus          = property(fget=Get_KMServerCheckingStatus         , fset=Set_KMServerCheckingStatus         ) # Возвращает значение свойства #KMServerCheckingStatus
    UserAttributeName               = property(fget=Get_UserAttributeName              , fset=Set_UserAttributeName              ) # Возвращает значение свойства #UserAttributeName
    UserAttributeValue              = property(fget=Get_UserAttributeValue             , fset=Set_UserAttributeValue             ) # Возвращает значение свойства #UserAttributeValue
    WaitForPrintingTimeout          = property(fget=Get_WaitForPrintingTimeout         , fset=Set_WaitForPrintingTimeout         ) # Возвращает значение свойства #WaitForPrintingTimeout
    DeclarativeInput                = property(fget=Get_DeclarativeInput               , fset=Set_DeclarativeInput               ) # Возвращает значение свойства #DeclarativeInput
    DeclarativeOutput               = property(fget=Get_DeclarativeOutput              , fset=Set_DeclarativeOutput              ) # Возвращает значение свойства #DeclarativeOutput
    DeclarativeEndpointPath         = property(fget=Get_DeclarativeEndpointPath        , fset=Set_DeclarativeEndpointPath        ) # Возвращает значение свойства #DeclarativeEndpointPath
    FontHashHex                     = property(fget=Get_FontHashHex                    , fset=None                               ) # Хеш пользовательского шрифта из ККТ
    MCOSUSign                       = property(fget=Get_MCOSUSign                      , fset=Set_MCOSUSign                      ) # Возвращает значение свойства #MCOSUSign
    DocumentSize                    = property(fget=Get_DocumentSize                   , fset=Set_DocumentSize                   ) # Возвращает значение свойства #DocumentSize
    FNImplementation                = property(fget=Get_FNImplementation               , fset=Set_FNImplementation               ) # Возвращает значение свойства #FNImplementation
    FNOSUSupportStatus              = property(fget=Get_FNOSUSupportStatus             , fset=Set_FNOSUSupportStatus             ) # Возвращает значение свойства #FNOSUSupportStatus
