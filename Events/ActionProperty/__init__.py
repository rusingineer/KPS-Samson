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

u"""
Описание свойств Action
"""
__all__ = (# 'CActionPropertyType',
           # 'CActionPropertyValueType',
           # 'CActionPropertyValueTypeRegistry',
            'CActionProperty',
          )

from ActionPropertyValueType  import CActionPropertyValueTypeRegistry

from AnatomicalLocalizationsActionPropertyValueType import CAnatomicalLocalizationsActionPropertyValueType
from ArterialPressureActionPropertyValueType    import CArterialPressureActionPropertyValueType
from BlankNumberActionPropertyValueType         import CBlankNumberActionPropertyValueType
from BlankSerialActionPropertyValueType         import CBlankSerialActionPropertyValueType
from BlankSerialNumberActionPropertyValueType   import CBlankSerialNumberActionPropertyValueType
from BooleanActionPropertyValueType             import CBooleanActionPropertyValueType
from ClientQuotingActionPropertyValueType       import CClientQuotingActionPropertyValueType
from ClientRelationActionPropertyValueType      import CClientRelationActionPropertyValueType
from ComplaintsActionPropertyValueType          import CComplaintsActionPropertyValueType
from ConstructorActionPropertyValueType         import CConstructorActionPropertyValueType
from ContractActionPropertyValueType            import CContractActionPropertyValueType
from CounterActionPropertyValueType             import CCounterActionPropertyValueType
from CsgActionPropertyValueType                 import CCsgActionPropertyValueType
from DateActionPropertyValueType                import CDateActionPropertyValueType
from DateTimeActionPropetyValueType             import CDateTimeActionPropertyValueType
from DoubleActionPropertyValueType              import CDoubleActionPropertyValueType
from Events.ActionProperty.DiagnosticServiceActionPropertyValueType import CDiagnosticServiceActionPropertyValueType
from Events.ActionProperty.JsonActionPropertyValueType import CJSONActionPropertyValueType
from Events.ActionProperty.ReferenceMultiValueActionPropertyValueType import CReferenceMultiActionPropertyValueType
from FeatureActionPropertyValueType             import CFeatureActionPropertyValueType
from FinanceActionPropertyValueType             import CFinanceActionPropertyValueType
from HospitalBedActionPropertyValueType         import CHospitalBedActionPropertyValueType
from HospitalBedProfileActionPropertyValueType  import CHospitalBedProfileActionPropertyValueType
from HtmlActionPropertyValueType                import CHtmlActionPropertyValueType
from ImageActionPropertyValueType               import CImageActionPropertyValueType
from ImageMapActionPropertyValueType            import CImageMapActionPropertyValueType
from IntegerActionPropertyValueType             import CIntegerActionPropertyValueType
from JobTicketActionPropertyValueType           import CJobTicketActionPropertyValueType
from MedicalAidProfileActionPropertyValueType   import CMedicalAidProfileActionPropertyValueType
from NomenclatureActionPropertyValueType        import CNomenclatureActionPropertyValueType
from NomenclatureActiveSubstanceActionPropertyValueType import CNomenclatureActiveSubstanceActionPropertyValueType
from NomenclatureSmnnActionPropertyValueType    import CNomenclatureSmnnActionPropertyValueType
from NomenclatureSmnnGrlsLfActionPropertyValueType import CNomenclatureSmnnGrlsLfActionPropertyValueType
from NomenclatureCalculationParamActionPropertyValueType import CNomenclatureCalculationParamActionPropertyValueType
from NomenclatureUsingTypeActionPropertyValueType import CNomenclatureUsingTypeActionPropertyValueType
from OrganisationActionPropertyValueType        import COrganisationActionPropertyValueType
from OrgStructureActionPropertyValueType        import COrgStructureActionPropertyValueType
from OrgStructurePlacementActionPropertyValueType import COrgStructurePlacementActionPropertyValueType
from PacsActionPropertyValueType                import CPacsActionPropertyValueType
from PersonActionPropertyValueType              import CPersonActionPropertyValueType
from PhaseMenstrualActionPropertyValueType      import CPhaseMenstrualActionPropertyValueType
from PulseActionPropertyValueType               import CPulseActionPropertyValueType
from RadiationDoseActionPropertyValueType       import CRadiationDoseActionPropertyValueType
from ReferenceActionPropertyValueType           import CReferenceActionPropertyValueType
from ReferenceColumnsActionPropertyValueType    import CReferenceColumnsActionPropertyValueType
from RLSActionPropertyValueType                 import CRLSActionPropertyValueType
from SamplingActionPropertyValueType            import CSamplingActionPropertyValueType
from SocStatusActionPropertyValueType           import CSocStatusActionPropertyValueType
from SpecialityActionPropertyValueType          import CSpecialityActionPropertyValueType
from ServiceActionPropertyValueType             import CServiceActionPropertyValueType
from StringActionPropertyValueType              import CStringActionPropertyValueType
from TemperatureActionPropertyValueType         import CTemperatureActionPropertyValueType
from TextActionPropertyValueType                import CTextActionPropertyValueType
from TimeActionPropertyValueType                import CTimeActionPropertyValueType
from ToothActionPropertyValueType               import CToothActionPropertyValueType
from UrlActionPropertyValueType                 import CUrlActionPropertyValueType
from ExemptionActionPropertyValueType import CExemptionActionPropertyValueType
from MKBActionPropertyValueType import CMKBActionPropertyValueType
from KRITActionPropertyValueType import CKRITActionPropertyValueType
from ActionPropertyType       import CActionPropertyType
from TissueTypeActionPropertyValueType import CTissueTypeActionPropertyValueType
from ActionProperty           import CActionProperty

CActionPropertyValueTypeRegistry.register(CAnatomicalLocalizationsActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CArterialPressureActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CBlankNumberActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CBlankSerialActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CBlankSerialNumberActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CBooleanActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CClientQuotingActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CClientRelationActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CComplaintsActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CConstructorActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CContractActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CCounterActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CCsgActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CDateActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CDoubleActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CFeatureActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CFinanceActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CHospitalBedActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CHospitalBedProfileActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CHtmlActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CImageActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CImageMapActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CIntegerActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CJobTicketActionPropertyValueType)
# CActionPropertyValueTypeRegistry.register(CJSONActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CMedicalAidProfileActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CNomenclatureActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CNomenclatureActiveSubstanceActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CNomenclatureSmnnActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CNomenclatureSmnnGrlsLfActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CNomenclatureCalculationParamActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CNomenclatureUsingTypeActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(COrganisationActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(COrgStructureActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(COrgStructurePlacementActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CPacsActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CPersonActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CPhaseMenstrualActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CPulseActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CRadiationDoseActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CReferenceActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CReferenceColumnsActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CRLSActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CSamplingActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CSocStatusActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CSpecialityActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CServiceActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CStringActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CTemperatureActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CTextActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CTimeActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CToothActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CUrlActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CExemptionActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CMKBActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CKRITActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CTissueTypeActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CDiagnosticServiceActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CReferenceMultiActionPropertyValueType)
CActionPropertyValueTypeRegistry.register(CDateTimeActionPropertyValueType)