# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
from Events.Service import CTariffInfo
from RefBooks.MedicalAidKind.Info    import CMedicalAidKindInfo
from RefBooks.MedicalAidProfile.Info import CMedicalAidProfileInfo
from RefBooks.MedicalAidType.Info    import CMedicalAidTypeInfo
from RefBooks.ServiceGroup.Info      import CServiceGroupInfo

from library.PrintInfo               import (
                                             CDateInfo,
                                             CRBInfoWithIdentification,
                                            )
from library.Utils                   import (
                                             forceString,
                                             forceBool,
                                             forceRef,
                                             forceDouble,
                                             forceInt,
                                            )


class CServiceInfo(CRBInfoWithIdentification):
    tableName = 'rbService'

    def _initByRecord(self, record):
        self._groupId = forceRef(record.value('group_id'))
        self._eisLegacy = forceBool(record.value('eisLegacy'))
        self._license = forceBool(record.value('license'))
        self._infis = forceString(record.value('infis'))
        self._begDate = CDateInfo(record.value('begDate'))
        self._endDate = CDateInfo(record.value('endDate'))
        self._medicalAidProfile = self.getInstance(CMedicalAidProfileInfo, forceInt(record.value('medicalAidProfile_id')))
        self._medicalAidKind = self.getInstance(CMedicalAidKindInfo, forceInt(record.value('medicalAidKind_id')))
        self._medicalAidType = self.getInstance(CMedicalAidTypeInfo, forceInt(record.value('medicalAidType_id')))
        self._adultUetDoctor = forceDouble(record.value('adultUetDoctor'))
        self._adultUetAverageMedWorker = forceDouble(record.value('adultUetAverageMedWorker'))
        self._childUetDoctor = forceDouble(record.value('childUetDoctor'))
        self._childUetAverageMedWorker = forceDouble(record.value('childUetAverageMedWorker'))


    def _initByNull(self):
        self._groupId = None
        self._eisLegacy = False
        self._eisLegacy = False
        self._license = False
        self._infis = ''
        self._begDate = CDateInfo()
        self._endDate = CDateInfo()
        self._medicalAidProfile = self.getInstance(CMedicalAidProfileInfo, None)
        self._medicalAidKind = self.getInstance(CMedicalAidKindInfo, None)
        self._medicalAidType = self.getInstance(CMedicalAidTypeInfo, None)
        self._adultUetDoctor = 0
        self._adultUetAverageMedWorker = 0
        self._childUetDoctor = 0
        self._childUetAverageMedWorker = 0

    def prepareTariff(self, contractId, clientId = None):
       self.tariff = CTariffInfo(self.context,  self.id)
       self.tariff.setContractId(contractId)
       if clientId:
           self.tariff.setClientId(clientId)

    group       = property(lambda self: self.getInstance(CServiceGroupInfo, self.load()._groupId))
    eisLegacy   = property(lambda self: self.load()._eisLegacy)
    license     = property(lambda self: self.load()._license)
    infis       = property(lambda self: self.load()._infis)
    begDate     = property(lambda self: self.load()._begDate)
    endDate     = property(lambda self: self.load()._endDate)
    medicalAidProfile = property(lambda self: self.load()._medicalAidProfile)
    medicalAidKind = property(lambda self: self.load()._medicalAidKind)
    medicalAidType = property(lambda self: self.load()._medicalAidType)
    adultUetDoctor = property(lambda self: self.load()._adultUetDoctor)
    adultUetAverageMedWorker = property(lambda self: self.load()._adultUetAverageMedWorker)
    childUetDoctor = property(lambda self: self.load()._childUetDoctor)
    childUetAverageMedWorker = property(lambda self: self.load()._childUetAverageMedWorker)


