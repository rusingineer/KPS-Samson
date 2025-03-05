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


# необходимо выработать формулировки названия прав
# 100 идентификаторов urAccess... это перебор

urAdmin = 'adm'

# Сессия
urSessionInformerExternal = 'sInformerExternal' # имеет доступ к внешним уведомлениям Информатор

# Работа
urAccessRegistry       = 'wRegistry'          # имеет доступ к обслуживанию пациентов
urAccessSuspenedAppointment = 'wSuspendedAppointment'# имеет доступ к отложенной записи
urAccessReadTimeLine        = 'wReadTimeLine'        # право на чтение Учёта рабочего времени
urAccessEditTimeLine        = 'wEditTimeLine'        # право на редактирование Учёта рабочего времени  # Было: urAccessTimeLine = 'timeLine' #имеет доступ к графику
urAccessBlanks         = 'wBlanks'            # имеет доступ к учету бланков
urAccessHospitalBeds   = 'wHospitalBeds'      # имеет доступ к Стационарному монитору
urAccessHealthResort   = 'wHealthResort'      # имеет доступ к Санаторному монитору
urAccessSurveillance   = 'wSurveillance'      # имеет доступ к Диспансерному наблюдению
urAccessJobsPlanning   = 'wJobsPlanning'      # имеет доступ к планированию работ
urAccessJobsOperating  = 'wJobsOperating'     # имеет доступ к выполнению работ
urAccessStockControl   = 'wStockControl'      # имеет доступ к складскому учёту
urAccessStockEditSupplier = 'wStockEditSupplier'# имеет право изменять поле "Поставщик" в накладной на списание
urAccessStockEditSupplierPerson = 'wStockEditSupplierPerson'# имеет право изменять поле "Ответственный" в накладной на списание
urAccessGraph          = 'wGraph'
urAccessLUD            = 'wLUD'
urAccessQuoting        = 'wQuoting'           # имеет доступ к редактированию квотирования
urAccessQuotingWatch   = 'wQuotingWatch'      # имеет доступ к просмотру квотирования
urAccessTissueJournal  = 'wTissueJournal'     # имеет доступ к лаболаторному журналу
urAccessSurgeryJournal = 'wSurgeryJournal'    # имеет доступ к Журналу операций
urAccessTreatmentScheme = 'wAccessTreatmentScheme'     # имеет доступ к Плану циклов
urAccessTreatmentSchedule = 'wAccessTreatmentSchedule' # имеет доступ к Графику циклов
urAccessTreatmentControl = 'wAccessTreatmentControl'   # имеет доступ к Управлению циклами
urAccessTreatmentAppointment = 'wAccessTreatmentAppointment' # право назначать мероприятия по циклам
urAccessCentralizedAccounting = 'wCentralizedAccounting'# имеет доступ доступ к "Централизованному учету"
urAccessEditCentralizedAccounting = 'wEditCentralizedAccounting'# право редактировать назначения "Централизованный учет"
urAccessDispService    = 'wDispService'      # имеет доступ к сервису диспансеризации
urAccessClientAttachFederalService= 'clientAttachFederalService'  # доступ к меню Прикрепление on-line
urDemography = 'wDemography'  # Работа: доступ к сервису демографии
urHomeCallJournal = 'wHomeCallJournal'  # Работа: доступ к журналу вызовов на дом
urMedStatic = 'wMedStatic'  # Работа: доступ к сервису мед. статистики

# Работа -> Диспансерное наблюдение
# Только чтение
urSurReadEvent          = 'wSurReadEvent'      # право на чтение события в Диспансерном наблюдении
urSurReadClientInfo     = 'wSurReadClientInfo'  # право на чтение карты пациента в Диспансерном наблюдении
# Запись/изменение
urSurEditEvent          = 'wSurEditEvent'       # право на редактирование события в Диспансерном наблюдении
urSurEditClientInfo     = 'wSurEditClientInfo'  # право редактировать карту пациента в Диспансерном наблюдении

# Работа -> Журнал операций
# Только чтение
urSurgeryJournalReadEvent      = 'wSurgeryJournalReadEvent'      # право на чтение события в Журнале операций
urSurgeryJournalReadAction     = 'wSurgeryJournalReadAction'     # право на чтение действия в Журнале операций
urSurgeryJournalReadClientInfo = 'wSurgeryJournalReadClientInfo' # право на чтение карты пациента в Журнале операций
# Запись/изменение
urSurgeryJournalEditEvent      = 'wSurgeryJournalEditEvent'      # право на редактирование события в Журнале операций
urSurgeryJournalEditAction     = 'wSurgeryJournalEditAction'     # право на редактирование действия в Журнале операций
urSurgeryJournalEditClientInfo = 'wSurgeryJournalEditClientInfo' # право на редактирование карты пациента в Журнале операций

# Работа -> Стационарный монитор
# Только чтение
urHBReadEvent          = 'wHBReadEvent'       # право на чтение события в стационарном мониторе
urHBReadClientInfo     = 'wHBReadClientInfo'  # право на чтение карты пациента в стационарном мониторе
# Запись/изменение
urHBHospitalization    = 'wHBHospitalization' # право на госпитализацию в стационарном мониторе
urHBTransfer           = 'wHBTransfer'        # право на перевод в стационарном мониторе
urHBLeaved             = 'wHBLeaved'          # право на выписку в стационарном мониторе
urHBFeed               = 'wHBFeed'            # право на питание в стационарном мониторе
urHBActionEdit         = 'wHBActionEdit'      # право выполнять назначения в стационарном мониторе
urHBDeath              = 'wHBDeath'           # имеет право доступа к кнопке "Констатация смерти" с вкладки "Умерло"
urHBEditCurrentDateFeed= 'wHBEditCurrentDateFeed' # право редактировать питание на текущую и прошлые даты
urHBEditEvent          = 'wHBEditEvent'       # право на редактирование события в стационарном мониторе
urHBEditClientInfo     = 'wHBEditClientInfo'  # право редактировать карту пациента в стационарном мониторе
urHBEditThermalSheet   = 'wHBEditThermalSheet'# право на редактирование температурного листа в стационарном мониторе
urHBEditHospitalBed    = 'wHBEditHospitalBed' # право на изменение данных о койке пребывания в стационарном мониторе
urHBEditPatron            = 'wHBEditPatron' # право на изменение данных о патроне
urHBEditObservationStatus = 'wHBEditObservationStatus' # право на редактирование статуса наблюдения пациента
urHBCanChangeOrgStructure = 'wHBCanChangeOrgStructure' # право на изменение подразделения (tblOrgStrucutre)
urHBPlanning = 'wHBPlanning' #право на постановку в очередь со вкладки "В очереди"
urHBEditReceivedMKB    = 'wHBEditReceivedMKB' # право на изменение шифра МКБ, свойств "Диагноз направившего учреждения" (или "Диагноз направителя") и "Диагноз при поступлении" на вкладке Поступили
urHBEditAction         = 'wHBEditAction'      # право добавлять действия в стационарном мониторе

# Работа -> Обслуживание
# Только чтение
urRegTabReadRegistry   = 'regReadRegistry'    #имеет доступ к вкладке Картотека, право на чтение регистрационной карты
urRegTabReadLocationCard= 'regReadLocationCard'#имеет право чтения Место нахождения амбулаторной карты
urRegTabReadEvents     = 'regReadEvents'      #имеет доступ к вкладке Обращение, чтение
urRegTabReadAmbCard    = 'regReadAmbCard'     #имеет доступ к вкладке Мед. карта
urRegTabReadActions    = 'regReadActions'     #имеет доступ к вкладке Обслуживание
urRegTabReadExpert     = 'regReadExpert'      #имеет доступ к вкладке КЭР
urRegTabReadAmbulance  = 'regReadAmbulance'   #имеет доступ к вкладке СМП
urRegTabReadVisits     = 'regReadVisits'      #имеет доступ к вкладке Визиты, чтение
# Запись/изменение
urRegTabNewWriteRegistry = 'regNewWriteRegistry' #имеет доступ к вкладке Картотека, право регистрировать новых пациентов в системе
urRegTabWriteRegistry  = 'regWriteRegistry'   #имеет доступ к вкладке Картотека, право редактировать уже существующие карты пациентов
urEditLocationCard     = 'regEditLocationCard'#имеет право редактировать Место нахождения амбулаторной карты
urEditStatusObservationClient = 'regEditStatusObservationClient'#имеет право редактировать Статус наблюдение пациента
urRegTabWriteEvents    = 'regWriteEvents'     #имеет доступ к вкладке Обращение, изменение
urRegTabWriteAmbCard   = 'regWriteAmbCard'    #имеет доступ к вкладке Мед. карта
urRegTabWriteActions   = 'regWriteActions'    #имеет доступ к вкладке Обслуживание
urRegTabWriteExpert    = 'regWriteExpert'     #имеет доступ к вкладке КЭР
urRegTabEditExpertMC   = 'regTabEditExpertMC' #имеет доступ к ВК
urRegTabWriteVisits    = 'regWriteVisits'     #имеет доступ к вкладке Визиты, изменение
urRegWriteInsurOfficeMark = 'regWriteInsurOfficeMark' #право на изменение данных в документах ВУТ с отметкой страхового стола
urRegTabWriteAmbulance = 'regWriteAmbulance'  #имеет доступ к вкладке СМП
urRegControlDoubles    = 'regControlDoubles'  #имеет доступ к оперативному логическому контролю двойников
urRegDeleteTempInvalid = 'regDeleteTempInvalid' #имеет право удалять листки нетрудоспособности
urRegEditTempInvalidWithInsurance = 'regEditTempInvalidWithInsurance' #имеет право Редактировать/Удалять ВУТ с отметкой Страхового стола, созданные пользователями с такой же сетью обслуживания
urRegEditTempInvalidNoInsurance = 'regEditTempInvalidNoInsurance' # имеет право Редактировать/Удалять ВУТ из любой сети обслуживания, но без отметки страхового стола
urRegTabWriteEventCash = 'editEventCash'  # имеет право Редактировать вкладку Обслуживание пациентов/Обращение/Оплата
urRegTabExpertChangeSignVUT = 'changeSignVUT'  # Имеет право выбирать ЭЦП в реадакторе ВУТ


# Работа -> Обслуживание -> вкладка Обслуживание
# Только чтение, на запись - см. права выше
urReadActionsStatus    = 'regReadActionsStatus'
urReadActionsDiagnostic= 'regReadActionsDiagnostic'
urReadActionsCure      = 'regReadActionsCure'
urReadActionsMisc      = 'regReadActionsMisc'

#Работа -> Выполнение работ
urUseGroupJobTicketsChanging = 'useGroupJobTicketsChanging' #имеет право использовать групповое изменение номерков в режиме "Выполение работ"

#Работа -> Складской учет
urEditOwnMotions = 'editOwnMotions' #имеет право редактировать свои накладные
urEditOtherMotions = 'editOtherPeopleMotions'#имеет право редактировать чужие накладные
urDeleteMotions = 'deleteMotions'#имеет право удалять накладные
urEditChkOnlyExistsNomenclature = 'editChkOnlyExistsNomenclature' #Право изменять фильтр "Только в наличии" в диалоге по выбору ЛСиИМН
urStockPurchaseContract = 'stockPurchaseContract' #имеет доступ к вкладке Складской учет -> Контракты на закупку
urNomenclatureExpenseLaterDate = 'nomenclatureExpenseLaterDate' #имеет право списывать ЛСиИМН пациенту на будущие даты
urNoRestrictRetrospectiveNEClient = 'noRestrictRetrospectiveNEClient' #Право без ограничений ретроспективно списывать ЛСиИМН на пациента
urStockRequirementsToMe = 'stockRequirementsToMe' # Право на доступ к "Складской учет: Требования ко мне"
urEditStockRequirementsToMe = 'editStockRequirementsToMe' # Право редактировать требования "Складской учёт: Требования ко мне"

# Сервис
urAccessAttachClientsForArea = 'attachClientsForArea'  #имеет  доступ к "Выполнить прикрепление пациентов к участкам"
urAccessLogicalControl = 'logiccntl'                   #имеет  доступ к логическому контролю
urAccessLogicalControlDiagnosis = 'logicCntlDiagnosis' #имеет  доступ к логическому контролю ЛУДа
urAccessLogicalControlDoubles   = 'logicCntlDoubles'   #имеет  доступ к контролю двойников
urAccessLogicalControlMES       = 'logicCntlMES'       #имеет  доступ к контролю событий с МЭС
urAccessSchemaClean = 'schemaclean'                    #имеет доступ к очистке бд
urAccessSchemaSync = 'schemaSync'   # может проводить синхронизацию БД
urAccessNotifications = 'notifications' # имеет доступ к системе оповещений
urAccessNotificationLog = 'notificationLog' # имеет доступ к журналу оповещений
urAccessNotificationKind = 'notificationKind' # имеет доступ к видам оповещений
urAccessNotificationRule = 'notificationRule' # имеет доступ к правилам оповещений
urAccessClientAttachExport = 'clientAttachExport' # имеет доступ к  экспорту данных в веб-сервис "Прикрепленное население"
urDoctorSectionExport = 'doctorSectionExport'  # Сервис: доступ к сервису экспорта врачей и участков
urUnlockData = 'unlockData'  # Сервис: доступ к "Разблокировать данные"
urPlanningHospitalBedProfile = 'planningHospitalBedProfile'  # Сервис: "Планирование загруженности коечного фонда"
urPlanningHospitalBedProfileGen = 'planningHospitalBedProfileGen' #Сервис: "Планирование загруженности коечного фонда" : Генерировать список подразделений
urAccesslogicCntlOMSAccounts = 'logicCntlOMSAccounts' #Сервис: доступ к проверке счетов из меню логического контроля
urAdminServiceTMK = 'adminServiceTMK' #Сервис: доступ к меню ТМК-Администрирование
urServiceTMKdirectionList = 'serviceTMKdirectionList' #Сервис: доступ к меню ТМК-список направлений
urPersonSubstitution = 'wPersonSubstitution' # Доступ к сервису замещения сотрудников
urCanChangePersonSubstitution = 'canChangePersonSubstitution' # Право редактировать данные о замещающих сотрудниках

# Расчет
urAccessAccountInfo    = 'acc'                # имеет доступ к учётной информации (договора и счета)
urAccessAccounting     = 'accAccount'         # Расчеты: доступ к счетам независимо от типа финансирования
urAccessAccountingBudget= 'accAccountBudget'  # Расчеты: доступ к счетам с типом финансирования "бюджет"
urAccessAccountingCMI  = 'accAccountCMI'      # Расчеты: доступ к счетам с типом финансирования "ОМС"
urAccessAccountingVMI  = 'accAccountVMI'      # Расчеты: доступ к счетам с типом финансирования "ДМС"
urAccessAccountingCash = 'accAccountCash'     # Расчеты: доступ к счетам с типом финансирования "платно"
urAccessAccountingTargeted = 'accAccountTargeted' # Расчеты: доступ к счетам с типом финансирования "целевой"

urDeleteAccount        = 'accDeleteAccount'    # Расчёты: имеет право удалять счета
urDeleteAccountBudget = 'accDeleteAccountBudget' # Расчеты: имеет право удалять счета с типом финансирования "бюджет"
urDeleteAccountCMI = 'accDeleteAccountCMI' # Расчеты: имеет право удалять счета с типом финансирования "ОМС"
urDeleteAccountVMI = 'accDeleteAccountVMI' # Расчеты: имеет право удалять счета с типом финансирования "ДМС"
urDeleteAccountCash = 'accDeleteAccountCash' # Расчеты: имеет право удалять счета с типом финансирования "Платно"
urDeleteAccountTargeted = 'accDeleteAccountTargeted' # Расчеты: имеет право удалять счета с типом финансирования "Целевой"
urDeleteAccountsAtOnce = 'accDeleteAccountsAtOnce'  #  Расчеты: имеет право удалять все выделенные реестры без предупреждений
urDeleteAccountItem    = 'accDeleteAccountItem'  # Расчёты: имеет право удалять позиции счёта
urDeleteRKEY    = 'accDeleteRKEY'  # Расчёты: имеет право удалять загруженные RKEY

urAccessContract       = 'accContract'        # имеет доступ к  договорам
urAccessPriceCalculate = 'accPriceCalculate'  # имеет доступ к кнопке пересчета тарифов
urAccessCashBook       = 'accCashBook'        # имеет доступ к журналу кассовых операций
# Справочники
urAccessRefBooks          =       'ref'                # имеет доступ к справочнику

# Справочники: Адреса
urAccessRefAddress        =       'refAddress'         # имеет доступ к справочнику Адреса
urAccessRefAddressKLADR   =       'refAddressKLADR'    # имеет доступ к справочнику КЛАДР
urAccessRefAddressAreas   =       'refAddressAreas'    # имеет доступ к справочнику Участки

# Cправочники: Классификаторы
urAccessRefClassificators =       'refCl'                      # имеет доступ к справочнику Класификаторы
urAccessRefClOKPF =               'refClOKPF'                  # имеет доступ к справочнику ОКПФ
urAccessRefClOKFS =               'refClOKFS'                  # имеет доступ к справочнику ОКФС
urAccessRefClHurtType =           'refClHurtType'              # имеет доступ к справочнику Типы вредности
urAccessRefClHurtFactorType =     'refClHurtFactorType'        # имеет доступ к справочнику Факторы вредности
urAccessRefClUnit =               'refClUnit'                  # имеет доступ к справочнику Единицы Измерения

# Cправочники: Скорая помощь
urAccessRefEmergency           =  'refEmergency'               # имеет доступ к справочнику Скорая помощь

# Cправочники: Питание
urAccessRefFeed                =  'refFeed'                    # имеет доступ к справочнику Питание

# Cправочники: Медицинские
urAccessRefMedical             =   'refMed'                    # имеет доступ к справочнику Медицинские
urAccessRefMedMKB              =   'refMedMKB'                 # имеет доступ к справочнику МКБ
urAccessRefMedMKBSubClass      =   'refMedMKBSubClass'         # имеет доступ к справочнику Субклассификация МКБ
urAccessRefMedDiseaseCharacter =   'refMedDiseaseCharacter'    # имеет доступ к справочнику Характеры заболеваний
urAccessRefMedDiseaseStage     =   'refMedDiseaseStage'        # имеет доступ к справочнику Стадии заболеваний
urAccessRefMedDiseasePhase     =   'refMedDiseasePhases'       # имеет доступ к справочнику Фазы заболевания
urAccessRefMedDiagnosisType    =   'refMedDiagnosisType'       # имеет доступ к справочнику Типы диагноза
urAccessRefMedTraumaType       =   'refMedTraumaType'          # имеет доступ к справочнику Типы травм
urAccessRefMedHealthGroup      =   'refMedHealthGroup'         # имеет доступ к справочнику Группы здоровья
urAccessRefMedDispanser        =   'refMedDispanser'           # имеет доступ к справочнику Отметки диспансерного наблюдения
urAccessRefMedResult           =   'refMedResult'              # имеет доступ к справочнику Резльтаты осмотра
urAccessRefMedTempInvalidAnnulmentReason='refMedTempInvalidAnnulmentReason'   # имеет доступ к справочнику Причины отмены документов ВУТ
urAccessRefMedTempInvalidBreak =   'refMedTempInvalidBreak'    # имеет доступ к справочнику Нарушения режима ВУТ
urAccessRefMedTempInvalidDocument= 'refMedTempInvalidDocument' # имеет доступ к справочнику Документы ВУТ
urAccessRefMedTempInvalidReason=   'refMedTempInvalidReason'   # имеет доступ к справочнику Причины временной нетрудоспособности
urAccessRefMedTempInvalidRegime=   'refMedTempInvalidRegime'   # имеет доступ к справочнику Режимы пеорида ВУТ
urAccessRefMedTempInvalidResult=   'refMedTempInvalidResult'   # имеет доступ к справочнику Результаты ВУТ
urRefEditMedTempInvalidExpertKAK=  'refEditMedTempInvalidExpertKAK'# имеет право вносить отметки КЭК
urAccessRefMedComplain         =   'refMedComplain'            # имеет доступ к справочнику Жалобы
urAccessRefMedComplainDelete   =   'refMedComplainDelete'      # имеет право удалять записи из справочника Жалобы
urAccessRefMedThesaurus        =   'refMedThesaurus'           # имеет доступ к справочнику Тезаурус
urAccessRefMedBloodType        =   'refMedBloodType'           # имеет доступ к справочнику Группы крови

# Cправочники: Организации
urAccessRefOrganization        =   'refOrg'                    # имеет доступ к подменю Организации
urAccessRefOrgRBNet            =   'refOrgRBNet'               # имеет доступ к справочнику Сеть
urAccessRefOrgBank             =   'refOrgBank'                # имеет доступ к справочнику Банки
urAccessRefOrgOrganisation     =   'refOrgOrganisation'        # имеет доступ к справочнику Организации

# Справочники: Персонал
urAccessRefPerson                       = 'refPerson'               # имеет доступ к подменю Персонал
urAccessRefPersonOrgStructure           = 'refPersonOrgStructure'   # имеет доступ к справочнику Структура ЛПУ
urAccessRefPersonRBSpeciality           = 'refPersonRBSpeciality'   # имеет доступ к справочнику Специальности
urAccessRefPersonRBPost                 = 'refPersonRBPost'         # имеет доступ к справочнику Должности
urAccessRefPersonRBActivity             = 'refPersonRBActivity'     # имеет доступ к справочнику Виды(типы) деятельности врача
urAccessRefPersonRBAppointmentPurpose   = 'refPersonRBRBAppointmentPurpose' # имеет доступ к справочнику Назначения приёма
urAccessRefPersonPersonal               = 'refPersonPersonal'       # имеет доступ к справочнику Сотрудники

# Справочники: Персонификация
urAccessRefPersonfication = 'refPersnftn'# имеет доступ к подменю Персонификация
urAccessRefPersnftnPolicyKind = 'refPersnftnPolicyKind'# имеет доступ к справочнику Вид полиса
urAccessRefPersnftnPolicyType = 'refPersnftnPolicyType'# имеет доступ к справочнику Тип полиса
urAccessRefPersnftnDocumentTypeGroup = 'refPersnftnDocumentTypeGroup'# имеет доступ к справочнику Группа типа документа
urAccessRefPersnftnDocumentType = 'refPersnftnDocumentType'# имеет доступ к справочнику Тип документа
urAccessRefPersnftnContactType = 'refPersnftnContactType'# имеет доступ к справочнику Способы связи с пациентом
urAccessRefEditLocationCard    = 'refPersnftnEditLocationCard'#имеет доступ к справочнику Место нахождения амбулаторной карты
urAccessRefEditCardType    = 'refPersnftnEditCardType'#имеет доступ к справочнику Виды медицинских карт
urAccessRefPersnftnResearchKind = 'refPersnftnResearchKind'# имеет доступ к справочнику Виды обследования
urAccessRefPersnftnContingentKind = 'refPersnftnContingentKind'# имеет доступ к справочнику Виды контингентов

# Справочники: Соц статус
urAccessRefSocialStatus   = 'refSocState'# имеет доступ к подменю Соц статус
urAccessRefSocialStatusType  = 'refSocStateType' # имеет доступ к справочнику Соц. статус: тип, льготы
urAccessRefSocialStatusClass = 'refSocStateClass'# имеет доступ к справочнику Классификатор социальных статусов

# Справочники: Учёт
urAccessRefAccount                       = 'refAccount' # имеет доступ к подменю Учёт
urAccessRefAccountRBVisitType            = 'refAccountRBVisitType'# имеет доступ к справочнику Тип визита
urAccessRefAccountEventType              = 'refAccountEventType'# имеет доступ к справочнику Типы событий
urAccessRefAccountRBEventTypePurpose     = 'refAccountRBEventTypePurpose'# имеет доступ к справочнику Назначение типа события
urAccessRefAccountRBEventProfile         = 'refAccountRBEventProfile'# имеет доступ к справочнику Профиль события
urAccessRefAccountRBScene                = 'refAccountRBScene'# имеет доступ к справочнику Место выполнения визита
urAccessRefAccountRBAttachType           = 'refAccountRBAttachType'# имеет доступ к справочнику Тип прикрепления
urAccessRefAccountRBMedicalAidUnit       = 'refAccountRBMedicalAidUnit'# имеет доступ к справочнику Единицы учета мед. помощи
urAccessRefAccountActionPropertyTemplate = 'refAccountActionPropertyTemplate'# имеет доступ к справочнику Библиотека свойств действий
urAccessRefAccountRBActionShedule        = 'refAccountRBActionShedule'       # имеет доступ к справочнику График выполнения назначения
urAccessRefAccountActionType             = 'refAccountActionType'            # имеет доступ к справочнику Типы действий
urDeleteActionTypeProperties             = 'refDeleteActionTypeProperties'   # может в справочнике типов действий удалять все свойства выбранных действий
urAccessRefAccountActionTemplate         = 'refAccountActionTemplate'        # имеет доступ к справочнику Шаблоны действий
urAccessRefDeletedAllActionTemplate         = 'refAccountDeletedAllActionTemplate'        # имеет право на удаление из справочника Шаблоны действий
urAccessRefDeletedActionTemplate         = 'refAccountDeletedActionTemplate' # имеет право на удаление из справочника Шаблоны действий только своих созданных шаблонов действий
urAccessRefUpdateOwnerActionTemplate     = 'refAccountUpdateOwnerActionTemplate' # имеет право на удаление и редактирование Шаблонов действий если является владельцем шаблона
urAccessRefAccountRBReasonOfAbsence      = 'refAccountRBReasonOfAbsence'     # имеет доступ к справочнику Причины отсутствия
urAccessRefAccountRBHospitalBedProfile   = 'refAccountRBHospitalBedProfile'  # имеет доступ к справочнику Профили коек
urAccessRefAccountJobPurpose             = 'refAccountJobPurpose'            # имеет доступ к справочнику Назначение работ
urAccessRefAccountBlankType              = 'refAccountBlankType'             # имеет доступ к справочнику Типы бланков
urAccessRefAgreementType                 = 'refAgreementType'                # имеет доступ к справочнику Типы согласования
urAccessRefAccountQuotaType              = 'refAccountQuotaType'             # имеет доступ к справочнику Виды квот

# Справочники: Финансовые
urAccessRefFinancial           = 'refFin'                # имеет доступ к подменю Финансовые
urAccessRefFinRBFinance        = 'refFinRBFinance'       # имеет доступ к справочнику "Источники финансирования"
urAccessRefFinRBService        = 'refFinRBService'       # имеет доступ к справочнику Услуги (профиль ЕИС)
urAccessRefFinRBTariffCategory = 'refFinRBTariffCategory'# имеет доступ к справочнику "Тарифные категории"
urAccessRefFinRBPayRefuseType  = 'refFinRBPayRefuseType' # имеет доступ к справочнику "Причины отказа платежа"
urAccessRefFinRBCashOperation  = 'refFinRBCashOperation' # имеет доступ к справочнику "Кассовые операции"

# Справочники: лекарственные средства и изделия медицинского назначения
urAccessNomenclature           = 'refNomenclature' # имеет доступ к справочнику "Номенклатура лекарственных средств и изделий медицинского назначения"
urAccessStockRecipe            = 'refStockRecipe'  # имеет доступ к справочнику "Рецепты производства ЛСиИМН"

# Спарвочники: Лаборатория
urAccessLaboratory                  = 'refLaboratory' # имеет доступ к подменю Лаболатория
urAccessEquipment                   = 'refEquipment' # имеет доступ к подменю Оборудование
urAccessEquipmentMaintenanceJournal = 'refEquipmentMaintenanceJournal' # Имеет доступ к редактированию журнала технического обслуживания оборудования

# Справочники: Иммунопрофилактика
urAccessImunoprophylaxis            = 'refImunoprophylaxis' # Имеет доступ к справочникам иммунопрофилактики

# Справочники: Летальность
urAccessLethality                   = 'refLethality' # Имеет доступ к справочникам летальности

# ---
urAccessUI                = 'ui'         # имеет доступ к интерфейсу пользователя
urAccessExchange          = 'exchng'     # имеет достук к обмену информацией

# Анализ
urAccessAnalysis                  = 'aFullAccess'                # имеет полный доступ к анализу
urAccessAnalysisPersonal          = 'aPersonal'                  # имеет полный доступ к персональному анализу
urAccessAnalysisOrgStruct         = 'aSubStruct'                 # имеет полный доступ к анализу подразделения
urAccessAnalysisTimeline          = 'aAnalysisTimeline'          # имеет доступ к "Анализ: Расписание"
urAccessAnalysisTimelinePreRecord = 'aAnalysisTimelinePreRecord' # имеет доступ к "Анализ: Расписание: Предварительная запись"
urAccessAnalysisAnaliticReports   = 'aAnalysisAnaliticReports'   # имеет доступ к "Анализ: Аналитические отчеты"
urAccessAdministrator   = 'aAnalysisAccessAdministrator'   # имеет доступ к "Анализ: Администратор"
urAccessStatReports            = 'aStatReports'            # имеет право на доступ к "Анализ: Статистические отчёты"
urAccessReportsChief           = 'aReportsChief'           # имеет право на доступ к "Анализ: Отчеты для руководителя"
urAccessGenRep                 = 'aGenRep'                 # имеет право на доступ к "Анализ: Генератор отчётов"
urAccessReportsByVisits        = 'aReportsByVisits'        # имеет право на доступ к "Анализ: Посещаемость"
urAccessReportsBuMorbidity     = 'aReportsBuMorbidity'     # имеет право на доступ к "Анализ: Заболеваемость"
urAccessDispObservation        = 'aDispObservation'        # имеет право на доступ к "Анализ: Диспансерное наблюдение"
urAccessAnalysisService        = 'aAnalysisService'        # имеет право на доступ к "Анализ: Обслуживание"
urAccessTempInvalid            = 'aTempInvalid'            # имеет право на доступ к "Анализ: ВУТ"
urAccessDeath                  = 'aDeath'                  # имеет право на доступ к "Анализ: Летальность"
urAccessContingent             = 'aContingent'             # имеет право на доступ к "Анализ: Контингент"
urAccessWorkload               = 'aWorkload'               # имеет право на доступ к "Анализ: Выработка"
urAccessStationary             = 'aStationary'             # имеет право на доступ к "Анализ: Стационар"
urAccessAccountingAnalysis     = 'aAccountingAnalysis'     # имеет право на доступ к "Анализ: Счета"
urAccessEconomicAnalysis      = 'aAnalysisEconomicReports' # имеет право на доступ к "Анализ: Экономический анализ"
urAccessEmergencyCall          = 'aEmergencyCall'          # имеет право на доступ к "Анализ: Скорая помощь"
urAccessReportImunoprophylaxis = 'aReportImunoprophylaxis' # имеет право на доступ к "Анализ: Иммунопрофилактика"
urAccessReportLaboratory       = 'aReportLaboratory'       # имеет право на доступ к "Анализ: Лаборатория"
urAccessReportTrauma           = 'aReportTrauma'           # имеет право на доступ к "Анализ: Травматология"
urAccessReportSanstorium       = 'aReportSanstorium'       # имеет право на доступ к "Анализ: Санаторий"
urAccessReportsForRK           = 'aReportsForRK'           # имеет право на доступ к "Анализ: Отчеты для Республики Калмыкия"

# Настройки
urAccessSetupDB                = 'setupDB'                # имеет доступ к настройкам БД
urAccessSetupAccountSystems    = 'setupAccSys'            # имеет доступ к внешним учётным системам
urAccessSetupDefault           = 'setupDefault'           # имеет доступ к установкам значений по умолчанию
urAccessSetupExport            = 'setupAccExpFmt'         # имеет доступ к форматам экспорта
urAccessSetupTemplate          = 'setupTemplate'          # имеет доступ к настройкам шаблонов
urDeletePrintTemplate          = 'deletePrintTemplate'    # имеет право удалять шаблоны печати
urAccessSetupUserRights        = 'setupUsrRights'         # имеет доступ к настройкам прав пользователя
urAccessSetupProfilesUserRights= 'setupProfilesUserRights'# имеет доступ к настройкам профилей прав пользователей
urAccessSetupGlobalPreferencesWatching = 'setupGlobalPreferencesWatching' # имеет доступ к чтению таблицы глобальных настроек
urAccessSetupGlobalPreferencesEdit = 'setupGlobalPreferencesEdit' # имеет доступ к редактированию таблицы глобальных настроек
urAccessCalendar               = 'setupCalendar'          # имеет доступ к настройке календаря
urAccessSetupCounter           = 'setupCounter'           # имеет доступ к настройке счетчиков
urSetupInformer = 'setupInformer'  # Настройки: доступ к сообщениям информатора
urAccessPreferencesPermitOnlyParentStock = 'preferencesPermitOnlyParentStock' # имеет доступ к редактированию "Предпочтения: Складской учёт: Оформлять требования только на вышестоящий склад"
urAccessPreferencesAgreeRequirementsStock = 'preferencesAgreeRequirementsStock' # имеет право согласовывать требования "Предпочтения: Складской учёт: Согласовывать требования"
urAccessStockAgreeRequirements = 'stockAgreeRequirements' # имеет право согласовывать требования "Складской учёт"
urAccessViewRequirementsForAllStock = 'viewRequirementsForAllStock' # имеет право просматривать требования ко всем складам "Складской учёт"

#urCanChangeOwnPassword = 2

# -- в процессе работы:

urAccessF000planner       = 'f000planner'        # показывается планировщик Ф.000
urAccessF001planner       = 'f001planner'        # показывается планировщик Ф.001
urAccessF003planner       = 'f003planner'        # показывается планировщик Ф.003
urAccessF025planner       = 'f25planner'         # показывается планировщик Ф.025
urAccessF030planner       = 'f030planner'        # показывается планировщик Ф.030
urAccessF043planner       = 'f043planner'        # показывается планировщик Ф.043
urAccessF110planner       = 'f110planner'        # показывается планировщик Ф.110
urAccessF072planner       = 'f072planner'        # показывается планировщик Ф.072
urAccessF090planner       = 'f090planner'        # показывается планировщик Ф.090
urLoadActionTemplate      = 'loadActionTemplate' # возможно загружать шаблоны действий в F25 etc.
urSaveActionTemplate      = 'saveActionTemplate' # возможно создавать/изменять шаблоны действий в F25 etc.
urCopyPrevAction          = 'copyPrevAction'     # Копировать действия из предыдущих событий в F25 etc.
urDeleteNotOwnActions     = 'deleteNotOwnActions'  # Имеет право удалять чужие действия
urDeleteActionsWithJobTicket = 'deleteActionsWithJobTicket'  # Имеет право удалять действия, связанные с номерком на работу
urChangeMKB               = 'changeMKB'          # исправить шифр МКБ в ЛУД
urChangeDiagnosis         = 'changeDiagnosis'    # изменить диагноз в ЛУД
urChangePeriodDiagnosis   = 'changePeriodDiagnosis'# изменить период диагноза в ЛУД
urLocalControlLUD         = 'localControlLUD'    # доступ к оперативному логическому контролю ЛУДа
urEditReportForm          = 'editReportForm'     # редактировать печатные формы отчетов во внешнем редакторе
urEditOtherpeopleAction   = 'editOtherpeopleAction' # редактировать "чужие" действия всех пользователей
urEditSubservientPeopleAction = 'editSubservientPeopleAction' # редактировать "чужие" действия своих подчиненных
urEditOtherPeopleActionSpecialityOnly = 'editOtherPeopleActionSpecialityOnly' # редактировать чужие действия только своей специальности
urHospitalTabReceived     = 'hospitalTabReceived'# имеет доступ к кнопке "Госпитализация" с вкладки "Поступили"
urHospitalTabPlanning     = 'hospitalTabPlanning'# имеет доступ к кнопке "Госпитализация" с вкладки "В очереди"
#urHospitalTabDeath        = 'hospitalTabDeath'   # имеет доступ к кнопке "Госпитализация" с вкладки "Умерли"
urLeavedTabPresence       = 'leavedTabPresence'  # имеет доступ к кнопке "Выписка" с вкладки "Присутствуют"
urQueueOverTime           = 'queueOverTime'      # Окно "График": имеет право записывать пациентов на "пустое" время
urQueueToSelfOverTime     = 'queueToSelfOverTime'# Окно "График": имеет право записывать пациентов к себе на "пустое" время
urDeleteOtherQueue        = 'queueDeletedTime'   # имеет право удалять созданные другими записи в листе предварительной записи
urDeleteOwnQueue          = 'queueToSelfDeletedTime'  # Окно "График": имеет право удалять созданные им записи в листе предварительной записи
urQueueCancelMinDateLimit = 'queueCancelMinDateLimit' # Окно "График": не ограничивать календарь снизу
urQueueCancelMaxDateLimit = 'queueCancelMaxDateLimit' # Окно "График": не ограничивать календарь сверху
urQueueModifyCheck        = 'queueModifyCheck'        # Окно "График": возможность менять отметку
urDeleteEventWithTissue   = 'deleteEventWithTissue'   # Право на удаление событий с действиями связанными с забором биоматериала
urDeleteEventWithJobTicket = 'deleteEventWithJobTicket' # Право на удаление событий с действиями связанными с номерком на Работу
urDeleteAnyEvents          = 'deleteAnyEvents'         # Имеет право удалять События любого пользователя
urDeleteOwnEvents          = 'deleteOwnEvents'         # Имеет право удалять свои События
urDeleteProbe              = 'deleteProbe'             # Абсолютное право на удаление проб
urEditProbePerson          = 'editProbePerson'         # Имеет право редактировать исполнителя в пробах
urEditJobTicket            = 'editJobTicket'           # Имеет право редактировать талончик на работу в действиях
urUsePreviouslyAppointedJobTicket = 'usePreviouslyAppointedJobTicket'  # Имеет право использовать ранее назначенные номерки
urUsePropertyCorrector     = 'usePropertyCorrector'    # Имеет право использовать утилиту 'корректор свойств'
urQueueingOutreaching      = 'queueingOutreaching'     # Имеет право превышать квоту на запись к врачу
urEditExecutionPlanAction  = 'editExecutionPlanAction' # Имеет право редактировать календарь выполнения назначения
urEditAfterInvoicingEvent  = 'editAfterInvoicingEvent' # Имеет право изменять события после выставления счёта.
urEditClosedEvent          = 'editClosedEvent'         # Имеет право изменять закрытые события.
urEditClosedEventCash      = 'EditClosedEventCash'     # Имеет право редактировать записи на вкладке Оплата в закрытом событии
urEditEndDateEvent         = 'editEndDateEvent'        # Имеет право закрывать события.
urCanAddExceedJobTicket    = 'canAddExceedJobTicket'   # Имеет право добавлять превышающий количество "Талон на выполнение работ"'
urAddNewNomenclatureAction = 'AddNewNomenclatureAction' # Имеет право добавлять препараты ЛСИМН из свойства действия
urCanEditClientVaccination = 'canEditClientVaccination' # Имеет право редактировать прививочную карту
urCanReadClientVaccination = 'canReadClientVaccination' # Имеет право читать прививочную карту
urBatchRegLocatCardProcess = 'wBatchRegLocatCardProcess' # Имеет право на пакетную регистрацию статуса места нахождения карты пациента
urGroupEditorLocatAccountDocument = 'wGroupEditorLocatAccountDocument' #Имеет право использовать Групповой редактор места нахождения учетного документа
urReadCheckPeriodActions   = 'wReadCheckPeriodActions' # Имеет право на чтение диалога "Контроль движения пациента"
urEditCheckPeriodActions   = 'wEditCheckPeriodActions' # Имеет право редактировать "Контроль движения пациента"
urCanUseNomenclatureButton = 'canUseNomenclatureButton'#Имеет право использовать кнопку "Списание ЛСИиМН"
urUpdateEventTypeByEvent   = 'updateEventTypeByEvent'  #Имеет право изменять тип события
urEditCoordinationAction   = 'editCoordinationAction'  # Имеет право редактировать данные о согласовании услуги в отдельном редакторе Действия и на вкладке "Оплата.Услуги" события.
# urRegEditClientAttach      = 'regEditClientAttach'     # Имеет право редактировать данные на вкладке Прикрепление Регистрационной карточки пациента.
urEditEventExpertise       = 'editEventExpertise'      #Имеет право редактировать сведений об Экспертизе случая
urSendInternalNotifications = 'sendInternalNotifications' #Имеет право рассылать оповещения через Регистратуру
urSendExternalNotifications = 'sendExternalNotifications' #Имеет право рассылать оповещения через внешнюю утилиту
urSendInternalAmbNotifications = 'sendInternalAmbNotifications' #Имеет право рассылать оповещения через График
urEditEventJournalOfPerson = 'editEventJournalOfPerson'# Имеет право редактировать Журнал назначения лечащего врача
urEditLoginPasswordProfileUser= 'editLoginPasswordProfileUser'# Имеет право редактировать логин, пароль и профиль прав в карточке персоны.
urCanDetachActionFromJobTicket = 'canDetachActionFromJobTicket' # Право на отмену действия в режиме выполнения работы
urReadMedicalDiagnosis     = 'readMedicalDiagnosis'    # Имеет право читать врачебную формулировку диагноза
urEditMedicalDiagnosis     = 'editMedicalDiagnosis'    # Имеет право редактировать врачебную формулировку диагноза
urEditThermalSheetPastDate = 'editThermalSheetPastDate'# Имеет право на редактирование температурного листа на прошлые даты
urRegEditClientDeathDate   = 'regEditClientDeathDate'  # Имеет право редактировать дату смерти пациента
urEditProphylaxisPlanning  = 'editProphylaxisPlanning' # Имеет право редактировать "Журнал планирования профилактического наблюдения"
urEditIssueDateTempInvalid = 'editIssueDateTempInvalid'# Имеет право редактировать дату выдачи документа ВУТ (issueDate)

urCanAttachFile            = 'canAttachFile'            # Право прикреплять файлы
urCanOpenOwnAttachedFile   = 'canOpenOwnAttachedFile'   # Право открывать свои прикреплённые файлы
urCanOpenAnyAttachedFile   = 'canOpenAnyAttachedFile'   # Право открывать любые прикреплённые файлы
urCanRenameOwnAttachedFile = 'canRenameOwnAttachedFile' # Право переименовывать свои прикреплённые файлы
urCanRenameAnyAttachedFile = 'canRenameAnyAttachedFile' # Право переименовывать любые прикреплённые файлы
urCanDeleteOwnAttachedFile = 'canDeleteOwnAttachedFile' # Право удалять свои прикреплённые файлы
urCanDeleteAnyAttachedFile = 'canDeleteAnyAttachedFile' # Право удалять любые прикреплённые файлы
urCanDeleteSuccessExpFile   = 'canDeleteSuccessExpFile'   # Право удалять успешно выгруженные файлы
urCanCreateNewActionTypeGroup = 'canCreateNewActionTypeGroup' # Право создавать шаблоны назначения действий
urCanEditForeignActionTypeGroup = 'canEditForeignActionTypeGroup' # Право редактировать шаблоны назначения действий, созданные другими пользователями
urCanDeleteForeignActionTypeGroup = 'canDeleteForeignActionTypeGroup' # Право удалять в справочнике Шаблоны назначения действий записи созданные другими пользователями
urCanDeleteActionNomenclatureExpense = 'canDeleteActionNomenclatureExpense' #Имеет право удалять действия, связанные со списанием ЛСиИМН
urDeattachMO                = 'deattachMO' #Имеет право запрашивать открепление в другой МО
urNewEventCliSnils                = 'NewEventCliSnils' #Имеет право создавать событие пациенту с отсутствующим снилсом
urNewEventCliUDL                = 'NewEventCliUDL' #Имеет право создавать событие пациенту с отсутствующим документом УДЛ
urNewEventCliPolis                = 'NewEventCliPolis' #Имеет право создавать событие пациенту с отсутствующим полисом
urCreateExpertConcurrentlyOnCloseVUT  = 'createExpertConcurrentlyOnCloseVUT' #Имеет право создавать б/л по совместительству по закрытому б/л на основное место работы'
urCanSaveEventWithMKBNotOMS = 'canSaveEventWithMKBNotOMS' #События: имеет право сохранять события по ОМС с МКБ не оплач в ОМС
urCanChangeEventExpose = 'canChangeEventExpose' # События: имеет право изменять флаг "Выставлять в счёт"
urCanSignOrgCert            = 'canSignOrgCert'            # Право подписывать документы сертификатом организации
urCanSingOrgSertNoAdmin = 'canSingOrgSertNoAdmin'  # Право подписывать чужие документы сертификатом организации без административных прав
urchangeSignDOC = 'canchangeSignDOC'  # Право выбирать подпись для подписания без административных прав
urHospitalOverWaitDirection = 'hospitalOverWaitDirection'  # События: Имеет право госпитализировать по направлению с превышенным сроком ожидания

# Регистрационая карта пациента

urEnableTabPassport = 'regEditClientPassport'  # Имеет доступ к вкладке "Паспортные данные"
urEnableSocStatus = 'regEditClientSocStatus'  # Имеет доступ к вкладке "Соц.статус"
urEnableClientAttach = 'regEditClientAttach'  # Имеет доступ к вкладке "Прикрепление"
urEnableTabWork = 'regEditClientWork'  # Имеет доступ к вкладке "Занятость"
urEnableTabChangeJournalInfo = 'regEditChangeJournalInfo'  # Имеет доступ к вкладке Журнал изменений
urEnableTabDocs = 'regEditClientDocs'  # Регистрационная карта: Имеет доступ к редактированию вкладки "Идентификация"
urEnableTabClientPolicy = 'regEditClientPolicy'  # Регистрационная карта: Имеет доступ к редактированию вкладки "Полисы"
urEnableTabClientAddress = 'regEditClientAddress'  # Регистрационная карта: Имеет доступ к редактированию вкладки "Адреса"
urRegEditClientHistory     = 'regEditClientHistory'    # Имеет право редактировать историю данных пациента.
urEnableTabFeature = 'regEditClientFeature'  # Имеет доступ к вкладке "Особенности"
urEnableTabResearch = 'regEditClientResearch'  # Имеет доступ к вкладке "Обследования"
urEnableTabDangerous = 'regEditClientDangerous'  # Имеет доступ к вкладке "Общ. опасность"
urEnableTabContingentKind = 'regEditClientContingentKind'  # Имеет доступ к вкладке "Контингент"
urEnableTabIdentification = 'regEditClientIdentification'  # Имеет доступ к вкладке "Идентификаторы"
urEnableTabRelations = 'regEditClientRelations'  # Имеет доступ к вкладке "Связи"
urEnableTabContacts = 'regEditClientContacts'  # Имеет доступ к вкладке "Прочее"
urEnableTabQuoting = 'regEditClientQuoting'  # Имеет доступ к вкладке "Квоты"
urEnableTabDeposit = 'regEditClientDeposit'  # Имеет доступ к вкладке "Депозитная карта"
urEnableTabConsent = 'regEditClientConsent'  # Имеет доступ к вкладке "Согласия"
urEnableTabClientMonitoring = 'regEditClientMonitoring'  # Имеет доступ к редактированию вкладки "Мониторинг"
urEnableTabClientEpidemic = 'regEditClientEpidemic'  # Имеет доступ к редактированию вкладки "ЭпидНаблюдение"
urRegEditClientHospitalization = 'regEditClientHospitalization'  # Имеет доступ к вкладке "Сведения о госпитализациях"

urRegEditClientAttachEndDateOwnAreaOnly = 'regEditClientAttachEndDateOwnAreaOnly'  # Регистрационная карта: Имеет право заполнять дату и причину открепления только для своего участка
urRegReadClientVisibleContingentKindOwnAreaOnly = 'regReadClientVisibleContingentKindOwnAreaOnly'  # Регистрационная карта: Имеет доступ к чтению вкладки "Контингент" только пациентов своего участка
urRegCreateClientContingentKindOwnAreaOnly = 'regCreateClientContingentKindOwnAreaOnly'  # Регистрационная карта: Имеет право создавать запись о Контингенте только для пациентов своего участка
urRegEditClientContingentKindOpenOwnAreaOnly = 'regEditClientContingentKindOpenOwnAreaOnly'  # Регистрационная карта: Имеет право редактирования не снятых Контингентов только для пациентов своего участка"
urRegEditClientContingentKindClosedOwnAreaOnly = 'regEditClientContingentKindClosedOwnAreaOnly'  # Регистрационная карта: Имеет право редактирования снятых Контингентов только для пациентов своего участка
urRegCreateClientAttachOwnAreaOnly = 'regCreateClientAttachOwnAreaOnly'  # Регистрационная карта: Имеет право прикрепления пациентов только к своему участку

urRegEditClientVisibleTabPassport = 'regReadClientVisiblePassport'  # видит вкладку "Паспортные данные"
urRegEditClientVisibleTabSocStatus = 'regReadClientVisibleSocStatus'  # видит вкладку "Соц.статус"
urRegEditClientVisibleTabAttach = 'regReadClientVisibleAttach'  # видит вкладку "Прикрепление"
urRegEditClientVisibleTabWork = 'regReadClientVisibleWork'  # видит вкладку "Занятость"
urRegEditClientVisibleTabChangeJournalInfo = 'regEditClientVisibleTabChangeJournalInfo'  # видит вкладку Журнал изменений
urRegEditClientVisibleTabDocs = 'regReadClientVisibleDocs'  # видит вкладку "Идентификация"
urRegEditClientVisiblePolicy = 'regReadClientVisiblePolicy'  # видит вкладку "Полисы"
urRegEditClientVisibleAddress = 'regReadClientVisibleAddress'  # видит вкладку "Адреса"
urRegEditClientVisibleHistory = 'regReadClientVisibleHistory'  # видит вкладку "ФИО"
urRegEditClientVisibleTabFeature = 'regReadClientVisibleFeature'  # видит вкладку "Особенности"
urRegEditClientVisibleTabResearch = 'regReadClientVisibleResearch'  # видит вкладку "Обследования"
urRegEditClientVisibleTabDangerous = 'regReadClientVisibleDangerous'  # видит вкладку "Общ. опасность"
urRegEditClientVisibleTabContingentKind = 'regReadClientVisibleContingentKind'  # видит вкладку "Контингент"
urRegEditClientVisibleTabIdentification = 'regReadClientVisibleIdentification'  # видит вкладку "Идентификаторы"
urRegEditClientVisibleTabRelations = 'regReadClientVisibleRelations'  # видит вкладку "Связи"
urRegEditClientVisibleTabContacts = 'regReadClientVisibleContacts'  # видит вкладку "Прочее"
urRegEditClientVisibleTabQuoting = 'regReadClientVisibleQuoting'  # видит вкладку "Квоты"
urRegEditClientVisibleTabDeposit = 'regReadClientVisibleDeposit'  # видит вкладку "Депозитная карта"
urRegEditClientVisibleTabConsent = 'regReadClientVisibleConsent'  # видит вкладку "Согласия"
urRegEditClientVisibleTabMonitoring = 'regReadClientVisibleMonitoring'  # видит вкладку "Мониторинг"
urRegEditClientVisibleTabEpidemic = 'regReadClientVisibleEpidemic'  # видит вкладку "ЭпидНаблюдение"

urRegEditClientInfo = 'regEditClientInfo'  # Регистрационная карта: Имеет доступ к редактированию информации о пациенте (ФИО, пол, д/р)
urRegEditClientSnils = 'regEditClientSnils'  # Регистрационная карта: Имеет доступ к редактированию СНИЛС пациента

urRegDeleteAttachSync = 'regDeleteAttachSync'  # Регистрационная карта: Имеет право удалять синхронизированные записи прикрепления

urEditAfterReturnEvent = 'editAfterReturnEvent'  # Редактирование события, по которым у счета есть причина возврата

# новые права пользователей для психиатрии и наркологии
urRegVisibleOwnAreaEventsOnly = 'regVisibleOwnAreaEventsOnly'  # Имеет право на вкладке Обращение видеть все события только пациентов своего участка
urRegVisibleOwnEventsOnly = 'regVisibleOwnEventsOnly'  # Имеет право на вкладке Обращения видеть только свои события
urRegVisibleOwnEventsOrgStructureOnly = 'regVisibleOwnEventsOrgStructureOnly'  # Имеет право на вкладке Обращения видеть только события своего подразделения
urRegVisibleOwnEventsParentOrgStructureOnly = 'regVisibleOwnEventsParentOrgStructureOnly'  # Имеет право на вкладке Обращения видеть события вышестоящего подразделения и всех его дочерних структур

urRegVisibleOwnAreaActionsOnly = 'regVisibleOwnAreaActionsOnly'  # Имеет право на вкладке Обслуживание видеть все действия только пациентов своего участка
urRegVisibleSetOwnActionsOnly = 'regVisibleSetOwnActionsOnly'  # Имеет право на вкладке Обслуживание видеть только свои назначенные действия
urRegVisibleSetOwnActionsOrgStructureOnly = 'regVisibleSetOwnActionsOrgStructureOnly'  # Имеет право на вкладке Обслуживание видеть только назначенные действия своего подразделения
urRegVisibleSetOwnActionsParentOrgStructureOnly = 'regVisibleSetOwnActionsParentOrgStructureOnly'  # Имеет право на вкладке Обслуживание видеть назначенные действия  вышестоящего подразделения и всех его дочерних структур

urRegVisibleExecOwnActionsOnly = 'regVisibleExecOwnActionsOnly'  # Имеет право на вкладке Обслуживание видеть только свои выполненные действия
urRegVisibleExecOwnActionsOrgStructureOnly = 'regVisibleExecOwnActionsOrgStructureOnly'  # Имеет право на вкладке Обслуживание видеть только выполненные действия своего подразделения
urRegVisibleExecOwnActionsParentOrgStructureOnly = 'regVisibleExecOwnActionsParentOrgStructureOnly'  # Имеет право на вкладке Обслуживание видеть выполненные действия  вышестоящего подразделения и всех его дочерних структур

urReadEventMedKart = 'readEventMedKart'  # Имеет право чтения медицинской карты из события
urReadJobTicketMedKart = 'readJobTicketMedKart'  # Имеет право чтения медицинской карты из режима Выполнение работ
urHBVisibleOwnEventsOrgStructureOnly = 'wHBVisibleOwnEventsOrgStructureOnly'  # Имеет право в стационарном мониторе видеть события только своего подразделения
urHBVisibleOwnEventsParentOrgStructureOnly = 'wHBVisibleOwnEventsParentOrgStructureOnly'  # Имеет право в стационарном мониторе видеть события вышестоящего подразделения и всех его дочерних структур

urCanDeleteClientDocumentTracking = 'canDeleteClientDocumentTracking'  # Право удалять записи в "Журнале хранения учетных документов"

canChangeActionPerson = 'canChangeActionPerson'  # Имеет право изменять Исполнителя в действии

canRightForCreateAccounts = 'canRightForCreateAccounts'  # Имеет право формировать счета
urFsselnEditPerson = 'FsselnEditPerson'  # Право редактировать поле Врач в утилите fsseln
urEditContractConditionF9 = 'editContractConditionF9'  # Имеет право редактировать условие "Договор" в добавлении действий по F9 в событии
urCanSaveF043WithoutStom = 'canSaveF043WithoutStom'  # Имеет право сохранять ф.043 без стоматологических приемов

## Подписание ЛН
#urSignTempInvalidAsDoctor = 'signTempInvalidAsDoctor' # имеет право подписывать листок нетрудоспособности как доктор
#urSignTempInvalidAsChief  = 'signTempInvalidAsChief'  # имеет право подписывать листок нетрудоспособности как председатель ВК

urCanSignForOrganisation   = 'canSignForOrganisation'  # имеет право подписывать за организацию
urCanIgnoreAttachFile      = 'canIgnoreAttachFile'     # Имеет право игнорировать требование прикрепления файла к Действию
urCanUserRemoveDispanser   = 'canUserRemoveDispanser'  # Имеет право снятия пациента с ДН в МО

