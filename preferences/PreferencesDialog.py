#!/usr/bin/env python
# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2019-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Диалог настроек s11
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature

from Users.Rights          import (
                                    urAdmin,
                                    urAccessSetupGlobalPreferencesEdit,
                                    urAccessSetupGlobalPreferencesWatching,
                                  )

from PreferencesDialogBase import CPreferencesDialogBase

from AccountingPage        import CAccountingPage
from ActionPage            import CActionPage
from AnalysisPage          import CAnalysisPage
from Treatment             import CTreatment
from ClientPlatePage       import CClientPlatePage
from ClientCardPage        import CClientCardPage
from SurgeryPage           import CSurgeryPage
from FormPage              import CFormPage
from CryptoPage            import CCryptoPage
from EisOmsPage            import CEisOmsPage
from EkpPage               import CEkpPage
from EmailPage             import CEmailPage
from EventPage             import CEventPage
from FileStoragePage       import CFileStoragePage
from FreeQueuePage         import CFreeQueuePage
from FssPage               import CFssPage
from GlobalsPage           import CGlobalsPage
from JobsOperatingPage     import CJobsOperatingPage
from MainPage              import CMainPage
from MdlpPage              import CMdlpPage
from PacsPage              import CPacsPage
from PrintPage             import CPrintPage
from RegistryPage          import CRegistryPage
from ReportPage            import CReportPage
from SerialPortScannerPage import CSerialPortScannerPage
from StockPage             import CStockPage
from TempInvalidPage       import CTempInvalidPage
from TerritorialFundPage   import CTerritorialFundPage
from TimetablePage         import CTimetablePage
from TreesPage             import CTreesPage
from VoucherPage           import CVoucherPage
from SpellCheckPage        import CSpellCheckPage
from LLOPage               import CLLOPage
from InformerPage          import CInformerPage
from DiagnosisPage         import CDiagnosisPage
from HospitalBedsPage      import CHospitalBedsPage
from UISComPage            import CUISComPage

from library.Utils         import forceString


class CPreferencesDialog(CPreferencesDialogBase):
    def __init__(self, parent=None):
        CPreferencesDialogBase.__init__(self, parent)

        self.addPage(CMainPage(self))
        self.addPage(CGlobalsPage(self))
        self.addPage(CTreesPage(self))
        self.addPage(CAnalysisPage(self))

        self.addPage(CClientPlatePage(self))
        self.addPage(CClientCardPage(self))
        self.addPage(CFormPage(self))
        self.addPage(CTimetablePage(self))
        self.addPage(CFreeQueuePage(self))
        self.addPage(CDiagnosisPage(self))
        self.addPage(CRegistryPage(self))
        self.addPage(CHospitalBedsPage(self))
        self.addPage(CEventPage(self))
        self.addPage(CActionPage(self))
        self.addPage(CJobsOperatingPage(self))
        self.addPage(CStockPage(self))
        self.addPage(CVoucherPage(self))
        self.addPage(CTreatment(self))
        self.addPage(CSurgeryPage(self))

        self.addPage(CPrintPage(self))
        self.addPage(CReportPage(self))
        self.addPage(CAccountingPage(self))

        self.addPage(CTempInvalidPage(self))
        self.addPage(CSerialPortScannerPage(self))

        self.addPage(CTerritorialFundPage(self))
        self.addPage(CPacsPage(self))
        self.addPage(CFileStoragePage(self))
        self.addPage(CCryptoPage(self))
        self.addPage(CFssPage(self))
        self.addPage(CMdlpPage(self))
        self.addPage(CEmailPage(self))

        # self.addPage(CEisOmsPage(self))
        # self.addPage(CEkpPage(self))

        self.addPage(CSpellCheckPage(self))

        # self.addPage(CLLOPage(self))

        self.addPage(CInformerPage(self))

        if forceString(QtGui.qApp.db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'infisCode')) == "48001":
            self.addPage(CUISComPage(self))

        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        if not QtGui.qApp.userHasAnyRight([urAdmin,
                                           urAccessSetupGlobalPreferencesWatching,
                                           urAccessSetupGlobalPreferencesEdit
                                          ]
                                         ):
            self.enablePage(self.globalsPage, False)


    @pyqtSignature('QString')
    def on_mainPage_defaultCityChanged(self, kladrCode):
        pass
        # isSpb = str(kladrCode).startswith('78')
        # self.enablePage(self.eisOmsPage, isSpb)
        # self.enablePage(self.ekpPage,    isSpb)


    @pyqtSignature('PyQt_PyObject')
    def on_cryptoPage_apiChanged(self, api):
        self.fssPage.setApi(api)
        self.mdlpPage.setApi(api)


    @pyqtSignature('QString')
    def on_cryptoPage_userCertChanged(self, userCertSha1):
        self.mdlpPage.setUserCertSha1(userCertSha1)

