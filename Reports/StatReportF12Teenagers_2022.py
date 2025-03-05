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
from PyQt4 import QtGui
from PyQt4.QtCore import QDate

from library.database   import addDateInRange
from library.MapCode    import createMapCodeToRowIdx
from library.Utils      import forceBool, forceInt, forceRef, forceString
from Reports.Report     import CReport, normalizeMKB
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportPersonSickList import addAddressCond, addAttachCond
from Reports.ReportAcuteInfections import getFilterAddress, CReportAcuteInfectionsSetupDialog
from Orgs.Utils         import getOrgStructureListDescendants, getOrgStructureAddressIdList


def getClientCountFor2004(begDate, endDate, eventPurposeId, eventTypeIdList, orgStructureIdList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params):
    clientsCount = 0
    clientsRemovingCount = 0
    clientsDeadCount = 0
    clientsCardioDeadCount = 0

    params['MKBFrom'] = 'I00'
    params['MKBTo'] = 'I99'
    query = selectData(begDate, endDate, eventPurposeId, eventTypeIdList, orgStructureIdList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params)
    while query.next():
        record = query.record()
        sickCount           = forceInt(record.value('sickCount'))
        diseaseCharacter    = forceString(record.value('diseaseCharacter'))
        firstInPeriod       = forceBool(record.value('firstInPeriod'))
        getObserved         = forceInt(record.value('getObserved'))
        getProfilactic      = forceBool(record.value('getProfilactic'))
        getAdultsDispans    = forceBool(record.value('getAdultsDispans'))
        if (firstInPeriod or diseaseCharacter == '1') and getProfilactic and not getAdultsDispans:
            if not getObserved:
                clientsCount += sickCount
    
    query = selectRemoveDispData(begDate, endDate, eventPurposeId, eventTypeIdList, orgStructureIdList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params)
    while query.next():
        record = query.record()
        sickCount = forceInt(record.value('sickCount'))
        clientsRemovingCount += sickCount


    isDead = params.get('dead', False)
    params['dead'] = True
    query = selectData(begDate, endDate, eventPurposeId, eventTypeIdList, orgStructureIdList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params)
    while query.next():
        record = query.record()
        sickCount           = forceInt(record.value('sickCount'))
        diseaseCharacter    = forceString(record.value('diseaseCharacter'))
        firstInPeriod       = forceBool(record.value('firstInPeriod'))
        getObserved         = forceInt(record.value('getObserved'))
        getProfilactic      = forceBool(record.value('getProfilactic'))
        getAdultsDispans    = forceBool(record.value('getAdultsDispans'))
        MKB                 = forceString(record.value('MKB'))
        if (firstInPeriod or diseaseCharacter == '1') and getProfilactic and not getAdultsDispans:
            if not getObserved:
                clientsDeadCount += sickCount
            if MKB.startswith('I'):
                clientsCardioDeadCount += sickCount
    params['dead'] = isDead

    return (clientsCount, clientsRemovingCount, clientsDeadCount, clientsCardioDeadCount)

MainRows = [
    ( u'Зарегистрировано заболеваний - всего', u'1.0', u'A00-T98'),
    ( u'в том числе: некоторые инфекционные и паразитарные болезни', u'2.0', u'A00-B99'),
    ( u'из них: кишечные инфекции', u'2.1', u'A00-A09'),
    ( u'менингококковая инфекция', u'2.2', u'A39'),
    ( u'вирусный гепатит', u'2.3', u'B15-B19'),
    ( u'из них хронический вирусный гепатит С', u'2.3.1', u'B18.2'),
    ( u'новообразования', u'3.0', u'C00-D48'),
    ( u'из них: злокачественные новообразования', u'3.1', u'C00-C96'),
    ( u'из них: злокачественные новообразования лимфоидной, кроветворной и родственных им тканей', u'3.1.1', u'C81-C96'),
    ( u'доброкачественные новобразования', u'3.2', u'D10-D36'),
    ( u'болезни крови, кроветворных органов и отдельные нарушения, вовлекающие иммунный механизм', u'4.0', u'D50-D89'),
    ( u'из них: анемии', u'4.1', u'D50-D64'),
    ( u'из них апластические анемии', u'4.1.1', u'D60-D61'),
    ( u'нарушения свертываемости крови, пурпура и другие геморрагические состояния', u'4.2', u'D65-D69'),
    ( u'гемофилия', u'4.2.1', u'D66-D68'),
    ( u'отдельные нарушения, вовлекающие иммунный механизм', u'4.3', u'D80-D89'),
    ( u'болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'5.0', u'E00-E89'),
    ( u'из них: болезни щитовидной железы', u'5.1', u'E00-E07'),
    ( u'из них: синдром врожденной йодной недостаточности', u'5.1.1', u'E00'),
    ( u'эндемический зоб, связанный с йодной недостаточностью', u'5.1.2', u'E01.0-2'),
    ( u'субклинический гипотиреоз вследствие йодной недостаточности и другие формы гипотиреоза', u'5.1.3', u'E02, E03'),
    ( u'другие формы нетоксического зоба', u'5.1.4', u'E04'),
    ( u'тиреотоксикоз (гипертиреоз)', u'5.1.5', u'E05'),
    ( u'тиреоидит', u'5.1.6', u'E06'),
    ( u'сахарный диабет', u'5.2', u'E10-E14'),
    ( u'из него с поражением глаз', u'5.2.1', u'E10.3, E11.3, E12.3, E13.3, E14.3'),
    ( u'с поражением почек', u'5.2.2', u'E10.2, E11.2, E12.2, E13.2, E14.2'),
    ( u'из него (из стр. 5.2):сахарный диабет I типа', u'5.2.3', u'E10'),
    ( u'сахарный диабет II типа', u'5.2.4', u'E11'),
    ( u'гиперфункция гипофиза', u'5.3', u'E22'),
    ( u'гипопитуитаризм', u'5.4', u'E23.0'),
    ( u'несахарный диабет', u'5.5', u'E23.2'),
    ( u'адреногенитальные расстройства', u'5.6', u'E25'),
    ( u'дисфункция яичников', u'5.7', u'E28'),
    ( u'дисфункция яичек', u'5.8', u'E29'),
    ( u'ожирение', u'5.10', u'E66'),
    ( u'из них, крайняя степень ожирения', u'5.10.1', u'E66.2'),
    ( u'фенилкетонурия', u'5.11', u'E70.0'),
    ( u'нарушения обмена галактозы (галактоземия)', u'5.12', u'E74.2'),
    ( u'болезнь Гоше', u'5.13', u'E75.2'),
    ( u'нарушения обмена гликозамигликанов (мукополисахаридоз)', u'5.14', u'E76'),
    ( u'муковисцидоз', u'5.15', u'E84'),
    ( u'психические расстройства и расстройства поведения', u'6.0', u'F01, F03-F99'),
    ( u'из них: психические расстройства и расстройства поведения, связанные с употреблением психоактивных веществ', u'6.1', u'F10-F19'),
    ( u'детский аутизм, атипичный аутизм, синдром Ретта, дезинтегративное расстройство детского возраста', u'6.2', u'F84.0-3'),
    ( u'болезни нервной системы', u'7.0', u'G00-G98'),
    ( u'из них: воспалительные болезни центральной нервной системы', u'7.1', u'G00-G09'),
    ( u'из них: бактериальный менингит', u'7.1.1', u'G00'),
    ( u'из них: энцефалит, миелит и энцефаломиелит', u'7.1.2', u'G04'),
    ( u'системные атрофии, поражающие преимущественно нервную систему', u'7.2', u'G10-G12'),
    ( u'экстрапирамидные и другие двигательные нарушения', u'7.3', u'G20,G21, G23-G25'),
    ( u'другие экстрапирамидные и двигательные нарушения', u'7.3.2', u'G25'),
    ( u'другие дегенеративные болезни нервной системы', u'7.4', u'G30-G31'),
    ( u'демиелинизирующие болезни центральной нервной системы', u'7.5', u'G35-G37'),
    ( u'из них: рассеянный склероз', u'7.5.1', u'G35'),
    ( u'эпизодические и пароксизмальные расстройства', u'7.6', u'G40-G47'),
    ( u'из них: эпилепсия, эпилептический статус', u'7.6.1', u'G40-G41'),
    ( u'преходящие транзиторные церебральные ишемические приступы (атаки) и родственные синдромы', u'7.6.2', u'G45'),
    ( u'поражения отдельных нервов, нервных корешков и сплетений, полиневропатии и другие поражения периферической нервной  системы', u'7.7', u'G50-G64'),
    ( u'из них: синдром Гийена-Барре', u'7.7.1', u'G61.0'),
    ( u'болезни нервно-мышечного синапса и мышц', u'7.8', u'G70-G73'),
    ( u'из них: миастения ', u'7.8.1', u'G70.0, 2'),
    ( u'мышечная дистрофия Дюшенна', u'7.8.2', u'G71.0'),
    ( u'церебральный паралич и другие паралитические синдромы', u'7.9', u'G80-G83'),
    ( u'из них: церебральный паралич', u'7.9.1', u'G80'),
    ( u'расстройства вегетативной(автономной) нервной системы', u'7.10', u'G90'),
    ( u'сосудистые миелопатии', u'7.11', u'G95.1'),
    ( u'болезни глаза и его придаточного аппарата', u'8.0', u'H00-H59'),
    ( u'из них: конъюнктивит', u'8.1', u'H10'),
    ( u'кератит', u'8.2', u'H16'),
    ( u'из них язва роговицы', u'8.2.1', u'H16.0'),
    ( u'катаракта', u'8.3', u'H25-H26'),
    ( u'хориоретинальное воспаление', u'8.4', u'H30'),
    ( u'отслойка сетчатки с разрывом сетчатки', u'8.5', u'H33.0'),
    ( u'преретинопатия', u'8.6', u'H35.1'),
    ( u'дегенерация макулы и заднего полюса', u'8.7', u'H35.3'),
    ( u'глаукома', u'8.8', u'H40'),
    ( u'дегенеративная миопия', u'8.9', u'H44.2'),
    ( u'болезни зрительного нерва и зрительных путей', u'8.10', u'H46-H48'),
    ( u'атрофия зрительного нерва', u'8.10.1', u'H47.2'),
    ( u'болезни мышц глаза, нарушения содружественного движения глаз, аккомодации и рефракции', u'8.11', u'H49-H52'),
    ( u'из них миопия', u'8.11.1', u'H52.1'),
    ( u'астигматизм', u'8.11.2', u'H52.2'),
    ( u'слепота и пониженное зрение', u'8.12', u'H54'),
    ( u'из них: слепота обоих глаз', u'8.12.1', u'H54.0'),
    ( u'болезни уха и сосцевидного отростка', u'9.0', u'H60-H95'),
    ( u'из них: болезни наружного уха', u'9.1', u'H60-H61'),
    ( u'болезни среднего уха и сосцевидного отростка', u'9.2', u'H65-H66, H68-H74'),
    ( u'из них: острый средний отит', u'9.2.1', u'H65.0, H65.1, H66.0'),
    ( u'хронический средний отит', u'9.2.2', u'H65.2-4, H66.1-3'),
    ( u'болезни слуховой (евстахиевой) трубы', u'9.2.3', u'H68-H69'),
    ( u'перфорация барабанной перепонки', u'9.2.4', u'H72'),
    ( u'другие болезни среднего уха и сосцевидного отростка', u'9.2.5', u'H74'),
    ( u'болезни внутреннего уха', u'9.3', u'H80-H81, H83'),
    ( u'из них: отосклероз', u'9.3.1', u'H80'),
    ( u'болезнь Меньера', u'9.3.2', u'H81.0'),
    ( u'кондуктивная и нейросенсорная потеря слуха', u'9.4', u'H90'),
    ( u'из них: кондуктивная потеря слуха двусторонняя', u'9.4.1', u'H90.0'),
    ( u'нейросенсорная потеря слуха двусторонняя', u'9.4.2', u'H90.3'),
    ( u'болезни системы кровообращения', u'10.0', u'I00-I99'),
    ( u'из них: острая ревматическая лихорадка', u'10.1', u'I00-I02'),
    ( u'хронические ревматические болезни сердца', u'10.2', u'I05-I09'),
    ( u'из них: ревматические поражения клапанов', u'10.2.1', u'I05-I08'),
    ( u'болезни, характеризующиеся повышенным кровяным давлением', u'10.3', u'I10-I13'),
    ( u'из них: эссенциальная гипертензия', u'10.3.1', u'I10'),
    ( u'гипертензивная болезнь сердца(гипертоническая болезнь с преимущественным поражением сердца)', u'10.3.2', u'I11'),
    ( u'гипертензивная (гипертоническая) болезнь с преимущественным  поражением  почек', u'10.3.3', u'I12'),
    ( u'гипертензивная (гипертоническая) болезнь с преимущественным  поражением сердца и  почек', u'10.3.4', u'I13'),
    ( u'ишемические болезни сердца', u'10.4', u'I20- I25'),
    ( u'из них: стенокардия', u'10.4.1', u'I20'),
    ( u'из нее: нестабильная стенокардия', u'10.4.1.1', u'I20.0'),
    ( u'острый инфаркт миокарда', u'10.4.2', u'I21'),
    ( u'повторный инфаркт миокарда', u'10.4.3', u'I22'),
    ( u'другие формы острых ишемических  болезней сердца', u'10.4.4', u'I24'),
    ( u'хроническая ишемическая болезнь   сердца', u'10.4.5', u'I25'),
    ( u'из нее постинфарктный кардиосклероз', u'10.4.5.1', u'I25.8'),
    ( u'другие болезни сердца', u'10.5', u'I30-I51'),
    ( u'из них: острый перикардит', u'10.5.1', u'I30'),
    ( u'из них: острый и подострый эндокардит', u'10.5.2', u'I33'),
    ( u'острый миокардит', u'10.5.3', u'I40'),
    ( u'кардиомиопатия', u'10.5.4', u'I42'),
    ( u'цереброваскулярные болезни', u'10.6', u'I60-I69'),
    ( u'из них: субарахноидальное кровоизлияние', u'10.6.1', u'I60'),
    ( u'внутримозговое и другое внутричерепное кровоизлияние', u'10.6.2', u'I61, I62'),
    ( u'инфаркт мозга', u'10.6.3', u'I63'),
    ( u'инсульт, не уточненный, как кровоизлияние или инфаркт', u'10.6.4', u'I64'),
    ( u'закупорка и стеноз прецеребральных, церебральных артерий, не приводящие к инфаркту мозга ', u'10.6.5', u'I65- I66'),
    ( u'другие цереброваскулярные болезни', u'10.6.6', u'I67'),
    ( u'из них:церебральный атеросклероз', u'10.6.6.1', u'I67.2'),
    ( u'последствия цереброваскулярные болезни', u'10.6.7', u'I69'),
    ( u'эндартериит, тромбангиит облитерирующий', u'10.7', u'I70.2, I73.1'),
    ( u'болезни вен, лимфатических сосудов и лимфатических узлов', u'10.8', u'I80-I83, I85-I89'),
    ( u'из них: флебит и тромбофлебит', u'10.8.1', u'I80'),
    ( u'тромбоз портальной вены', u'10.8.2', u'I81'),
    ( u'варикозное расширение вен нижних конечностей', u'10.8.3', u'I83'),
    ( u'болезни органов дыхания', u'11.0', u'J00-J98'),
    ( u'из них: острые респираторные инфекции верхних дыхательных путей', u'11.1', u'J00-J06'),
    ( u'из них: острый ларингит и трахеит', u'11.1.1', u'J04'),
    ( u'острый обструктивный ларингит (круп) и эпиглоттит', u'11.1.2', u'J05'),
    ( u'грипп', u'11.2', u'J09-J11'),
    ( u'пневмонии', u'11.3', u'J12-J16, J18'),
    ( u'из них бронхопневмония, вызванная S Pneumoniae', u'11.3.1', u'J13'),
    ( u'острые респираторные инфекции нижних дыхательных путей', u'11.4', u'J20-J22'),
    ( u'аллергический ринит (поллиноз)', u'11.5', u'J30.1'),
    ( u'хронические болезни миндалин и аденоидов, перитонзиллярный абсцесс', u'11.6', u'J35-J36'),
    ( u'бронхит хронический и неуточненный, эмфизема', u'11.7', u'J40-J43'),
    ( u'другая хроническая обструктивная легочная болезнь ', u'11.8', u'J44'),
    ( u'бронхоэктатическая болезнь', u'11.9', u'J47'),
    ( u'астма, астматический статус', u'11.10', u'J45-J46'),
    ( u'другие интерстициальные легочные болезни, гнойные  и некротические болезни, состояния нижних дыхательных путей, другие болезни плевры', u'11.11', u'J84-J90, J92-J94 '),
    ( u'болезни органов пищеварения', u'12.0', u'K00-K92'),
    ( u'из них: язвенная болезнь желудка и 12-ти перстной кишки', u'12.1', u'K25-K26'),
    ( u'гастрит и дуоденит', u'12.2', u'K29'),
    ( u'грыжи', u'12.3', u'K40-K46'),
    ( u'неинфекционный энтерит и колит', u'12.4', u'K50-K52'),
    ( u'другие болезни кишечника', u'12.5', u'K55-K63'),
    ( u'из них: паралитический илеус и непроходимость кишечника без грыжи', u'12.5.1', u'K56'),
    ( u'геморрой', u'12.6', u'K64'),
    ( u'болезни печени', u'12.7', u'K70-K76'),
    ( u'из них: фиброз и цирроз печени', u'12.7.1', u'K74'),
    ( u'болезни желчного пузыря, желчевыводящих путей', u'12.8', u'K80-K83'),
    ( u'болезни поджелудочной железы', u'12.9', u'K85-K86'),
    ( u'из них острый панкреатит', u'12.9.1', u'K85'),
    ( u'болезни кожи и подкожной клетчатки', u'13.0', u'L00-L98'),
    ( u'из них: атопический дерматит', u'13.1', u'L20'),
    ( u'контактный дерматит', u'13.2', u'L23-L25'),
    ( u'другие дерматиты (экзема)', u'13.3', u'L30'),
    ( u'псориаз', u'13.4', u'L40'),
    ( u'из него: псориаз артропатический', u'13.4.1', u'L40.5'),
    ( u'дискоидная красная волчанка', u'13.5', u'L93.0'),
    ( u'локализованная склеродермия', u'13.6', u'L94.0'),
    ( u'болезни костно-мышечной системы и соединительной ткани', u'14.0', u'M00-M99'),
    ( u'из них: артропатии', u'14.1', u'M00-M25'),
    ( u'из них: пневмококковый артрит и полиартрит', u'14.1.1', u'M00.1'),
    ( u'из них: реактивные артропатии', u'14.1.2', u'M02'),
    ( u'серопозитивный и другие ревматоидные артриты', u'14.1.3', u'M05-M06'),
    ( u'юношеский (ювенальный) артрит', u'14.1.4', u'M08'),
    ( u'артрозы', u'14.1.5', u'M15-M19'),
    ( u'системные поражения соединительной ткани', u'14.2', u'M30-M35'),
    ( u'из них: системная красная волчанка', u'14.2.1', u'M32'),
    ( u'деформирующие дорсопатии', u'14.3', u'M40-M43'),
    ( u'cпондилопатии', u'14.4', u'M45-M48'),
    ( u'из них: анкилозирующий спондилит', u'14.4.1', u'M45'),
    ( u'поражение синовинальных оболочек и сухожилий', u'14.5', u'M65-M67'),
    ( u'остеопатии и хондропатии', u'14.6', u'M80-M94'),
    ( u'из них остеопороз с патологическим переломом', u'14.6.1', u'M80'),
    ( u'остеопороз без патологического перелома', u'14.6.2', u'M81'),
    ( u'болезни мочеполовой системы', u'15.0', u'N00-N99'),
    ( u'из них: гломерулярные, тубулоинтерстициальные болезни почек, другие болезни почки и мочеточника', u'15.1', u'N00-N07, N09-N15, N25-N28'),
    ( u'почечная недостаточность', u'15.2', u'N17-N19'),
    ( u'мочекаменная болезнь', u'15.3', u'N20-N21,N23'),
    ( u'другие болезни мочевой системы', u'15.4', u'N30- N32, N34-N36, N39'),
    ( u'болезни предстательной железы', u'15.5', u'N40-N42'),
    ( u'доброкачественная дисплазия молочной   железы', u'15.7', u'N60'),
    ( u'воспалительные болезни женских тазовых органов', u'15.8', u'N70-N73, N75-N76'),
    ( u'из них сальпингит и оофорит', u'15.8.1', u'N70'),
    ( u'эндометриоз', u'15.9', u'N80'),
    ( u'эрозия и эктропион шейки матки', u'15.10', u'N86'),
    ( u'расстройства менструаций', u'15.11', u'N91-N94'),
    ( u'беременность, роды и послеродовой период', u'16.0', u'O00-O99'),
    ( u'отдельные состояния, возникающие в перинатальном периоде', u'17.0', u'P00-P04'),
    ( u'врожденные аномалии (пороки развития), деформации и хромосомные нарушения', u'18.0', u'Q00-Q99'),
    ( u'из них: врожденные аномалии нервной системы', u'18.1', u'Q00-Q07'),
    ( u'врожденные аномалии глаза', u'18.2', u'Q10-Q15'),
    ( u'врожденные аномалии системы кровообращения', u'18.3', u'Q20-Q28'),
    ( u'врожденные аномалии женских половых органов', u'18.4', u'Q50-Q52'),
    ( u'неопределенность пола и псевдогермафродитизм', u'18.5', u'Q56'),
    ( u'врожденные деформации бедра', u'18.6', u'Q65'),
    ( u'врожденный ихтиоз', u'18.7', u'Q80'),
    ( u'нейрофиброматоз', u'18.8', u'Q85.0'),
    ( u'синдром Дауна', u'18.9', u'Q90'),
    ( u'симптомы, признаки и отклонения от нормы, выявленные при клинических и лабораторных исследованиях, не классифицированные в других рубриках', u'19.0', u'R00-R99'),
    ( u'травмы, отравления и некоторые другие последствия воздействия внешних причин', u'20.0', u'S00-T98'),
    ( u'из них: открытые укушенные раны (только с кодом внешней причины W54)', u'20.1', u'S01, S11, S21, S31, S41, S51, S61, S71, S81, S91'),
    ( u'COVID-19', u'21.0', u'U07.1, U07.2')
]

CompRows = [
    ( u'Всего', u'1.0', u'Z00-Z99'),
    ( u'из них: обращения в медицинские организации для медицинского осмотра и обследования', u'1.1', u'Z00-Z13'),
    ( u'из них: обращения в связи с получением медицинских документов', u'1.1.1', u'Z02.7'),
    ( u'наблюдение при подозрении на COVID-19', u'1.1.2', u'Z03.8'),
    ( u'скрининговое обследование с целью выявления COVID-19', u'1.1.3', u'Z11.5'),
    ( u'потенциальная опасность для здоровья, связанная с инфекционными болезнями', u'1.2', u'Z20-Z29'),
    ( u'из них: контакт с больным COVID-19', u'1.2.1', u'Z20.8'),
    ( u'из них: носительство возбудителя инфекционной болезни', u'1.2.2', u'Z22'),
    ( u'из них: носительство возбудителя COVID-19', u'1.2.3', u'Z22.8'),
    ( u'обращения в медицинские организации в связи с обстоятельствами, относящимися к репродуктивной функции', u'1.3', u'Z30-Z39'),
    ( u'обращения в медицинские организации в связи с необходимостью проведения специфических процедур и получения медицинской помощи', u'1.4', u'Z40-Z54'),
    ( u'из них: помощь, включающая использование реабилитационных процедур', u'1.4.1', u'Z50'),
    ( u'из них: реабилитация лиц, страдающих алкоголизмом', u'1.4.1.1', u'Z50.2'),
    ( u'реабилитация лиц, страдающих наркоманиями', u'1.4.1.2', u'Z50.3'),
    ( u'лечение, включающее другие виды реабилитационных процедур, реабилитация при курении', u'1.4.1.3', u'Z50.8'),
    ( u'паллиативная помощь', u'1.4.2', u'Z51.5'),
    ( u'потенциальная опасность для здоровья, связанная с социально-экономическими и психосоциальными обстоятельствами', u'1.5', u'Z55-Z65'),
    ( u'обращения в медицинские организации в связи с другими обстоятельствами', u'1.6', u'Z70-Z76'),
    ( u'из них: обращения в учреждения здравоохранения для получения других консультаций и медицинских советов, не классифицированные в других рубриках', u'1.6.1', u'Z71'),
    ( u'консультирование и наблюдение по поводу алкоголизма', u'1.6.1.1', u'Z71.4'),
    ( u'консультирование и наблюдение по поводу наркомании', u'1.6.1.2', u'Z71.5'),
    ( u'консультирование и наблюдение по поводу курения', u'1.6.1.3', u'Z71.6'),
    ( u'из них: проблемы, связанные с образом жизни:', u'1.6.2', u'Z72'),
    ( u'из них: употребление табака', u'1.6.2.1', u'Z72.0'),
    ( u'употребление алкоголя', u'1.6.2.2', u'Z72.1'),
    ( u'использование наркотиков', u'1.6.2.3', u'Z72.2'),
    ( u'склонность к азартным играм и пари', u'1.6.2.4', u'Z72.6'),
    ( u'потенциальная опасность для здоровья, связанная с личным или семейным анамнезом и определенными обстоятельствами, влияющими на здоровье', u'1.7', u'Z80-Z99'),
    ( u'из них: заболевания в семейном анамнезе', u'1.7.1', u'Z80-Z84'),
    ( u' из них: наличие илеостомы, колостомы', u'1.7.2', u'Z93.2, Z93.3')
]


def selectData(begDate, endDate, eventPurposeId, eventTypeIdList, orgStructureIdList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params):
    stmt = u"""
SELECT
   Diagnosis.MKB AS MKB,
   COUNT(*) AS sickCount,
   rbDiseaseCharacter.code AS diseaseCharacter,
   rbDiagnosisType.code AS diagnosisType,
   EXISTS(SELECT rbResult.id
   FROM
   Diagnostic AS D1
   INNER JOIN Event ON Event.id = D1.event_id
   INNER JOIN rbResult ON rbResult.id = Event.result_id
   WHERE D1.diagnosis_id = Diagnosis.id AND rbResult.continued = 0
   ORDER BY Event.id) AS closedEvent,
   (SELECT IF(rbDispanser.code IN (2,6), 1, 0)
    FROM
    Diagnostic AS D1
    LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
    WHERE
      D1.diagnosis_id = Diagnosis.id
      AND (rbDispanser.code IN (2,6) AND D1.setDate >= \'%s\' AND D1.setDate <= \'%s\')
    ORDER BY rbDispanser.code
    LIMIT 1) AS getObserved,
   Client.sex AS sex,
   (%s) AS firstInPeriod,
   EXISTS((SELECT rbm1.regionalCode
        FROM
        Diagnostic AS D1
        INNER JOIN Event AS E ON E.id = D1.event_id
        LEFT JOIN EventType ET1 ON ET1.id = E.eventType_id
        LEFT JOIN rbMedicalAidType rbm1 ON ET1.medicalAidType_id = rbm1.id
        WHERE
            D1.diagnosis_id = Diagnosis.id AND E.deleted = 0
            AND D1.deleted = 0 and rbm1.regionalCode in (262))) AS getProfilactic,
   EXISTS(SELECT E.id
    FROM Diagnostic AS D1 INNER JOIN Event AS E ON E.id = D1.event_id
    WHERE D1.diagnosis_id = Diagnosis.id AND E.deleted = 0
    AND D1.deleted = 0 AND E.isPrimary = 2) AS isNotPrimary,
   EXISTS((SELECT rbm2.regionalCode
        FROM
        Diagnostic AS D1
        INNER JOIN Event AS E ON E.id = D1.event_id
        LEFT JOIN EventType ET2 ON ET2.id = E.eventType_id
        LEFT JOIN rbMedicalAidType rbm2 ON ET2.medicalAidType_id = rbm2.id
        WHERE
            D1.diagnosis_id = Diagnosis.id AND E.deleted = 0
            AND D1.deleted = 0 and rbm2.regionalCode in (232,252))) AS getAdultsDispans,
    Client.deathDate AS isDead,
    (SELECT D3.MKB
     FROM Diagnosis AS D3 
     LEFT JOIN Diagnostic AS D4 ON D4.diagnosis_id = D3.id
     LEFT JOIN Event AS E2 ON E2.id = D4.event_id
     LEFT JOIN EventType AS ET2 ON ET2.id = E2.eventType_id
     WHERE E2.client_id = Client.id AND ET2.code in (15) LIMIT 1) AS deathMKB
     
FROM Diagnosis
LEFT JOIN Client ON Client.id = Diagnosis.client_id
%s
LEFT JOIN rbDiagnosisType    ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnosis.character_id
WHERE Diagnosis.diagnosisType_id NOT IN (SELECT RBDT.id FROM rbDiagnosisType AS RBDT WHERE RBDT.code = '7' OR RBDT.code = '11')
AND %s
GROUP BY MKB, diseaseCharacter, sex, firstInPeriod, getObserved, getProfilactic, isNotPrimary, closedEvent, getAdultsDispans, rbDiagnosisType.id
    """
    db = QtGui.qApp.db
    tableDiagnosis  = db.table('Diagnosis')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tablePerson = db.table('Person')
    specialityId = params.get('specialityId', None)

    cond = []
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableDiagnosis['mod_id'].isNull())
    cond.append(tableClient['deleted'].eq(0))
    diagnosticQuery = tableDiagnostic
    diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                       tableDiagnostic['deleted'].eq(0)
                     ]
    addDateInRange(diagnosticCond, tableDiagnostic['setDate'], begDate, endDate)
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
    diagnosticQuery = diagnosticQuery.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    diagnosticCond.append(tableEventType['code'].ne('rmDisp'))
    if specialityId:
        diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['speciality_id'].eq(specialityId))
        diagnosticCond.append(tablePerson['deleted'].eq(0))
    isPersonPost = params.get('isPersonPost', 0)
    if isPersonPost:
        tableRBPost = db.table('rbPost')
        if not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticQuery = diagnosticQuery.leftJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
        if isPersonPost == 1:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('1','2','3') ''')
        elif isPersonPost == 2:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('4','5','6','7','8','9')''')
    if personId:
        diagnosticCond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureIdList:
        if not isPersonPost and not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureListDescendants(orgStructureIdList)))
    else:
        if not isPersonPost and not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if eventTypeIdList:
        diagnosticCond.append(tableEvent['eventType_id'].inlist(eventTypeIdList))
    elif eventPurposeId:
        diagnosticCond.append(tableEventType['purpose_id'].eq(eventPurposeId))

    cond.append(db.existsStmt(diagnosticQuery, diagnosticCond))

    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        cond.append('Client.birthDate <= ADDDATE(%s, INTERVAL -%d YEAR)' % (tableDiagnosis['setDate'].formatValue(QDate(endDate.year(), 12, 31)), ageFrom))
        cond.append('Client.birthDate >= ADDDATE(ADDDATE(%s, INTERVAL -%d YEAR),1)' % (tableDiagnosis['setDate'].formatValue(QDate(endDate.year(), 12, 31)), ageTo+1))
    if socStatusTypeId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusType_id=%d' % socStatusTypeId)
        cond.append('EXISTS('+subStmt+')')
    elif socStatusClassId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusClass_id=%d' % socStatusClassId)
        cond.append('EXISTS('+subStmt+')')
    stmtAddress = ''
    if isFilterAddressOrgStructure:
        addrIdList = None
        cond2 = []
        if (addrType+1) & 1:
            addrIdList = getOrgStructureAddressIdList(addressOrgStructureId)
            cond2 = addAddressCond(db, cond2, 0, addrIdList)
        if (addrType+1) & 2:
            if addrIdList is None:
                addrIdList = getOrgStructureAddressIdList(addressOrgStructureId)
            cond2 = addAddressCond(db, cond2, 1, addrIdList)
        if ((addrType+1) & 4):
            if addressOrgStructureId:
                cond2 = addAttachCond(db, cond2, 'orgStructure_id = %d'%addressOrgStructureId, 1, None)
            else:
                cond2 = addAttachCond(db, cond2, 'LPU_id=%d'%QtGui.qApp.currentOrgId(), 1, None)
        if cond2:
            cond.append(db.joinOr(cond2))
    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
    filterAddress = params.get('isFilterAddress', False)
    if filterAddress:
        stmtAddress += u'''INNER JOIN ClientAddress ON ClientAddress.client_id = Client.id
                              INNER JOIN Address ON Address.id = ClientAddress.address_id
                              INNER JOIN AddressHouse ON AddressHouse.id = Address.house_id'''
        cond.append('ClientAddress.id IN (%s)'%(getFilterAddress(params)))
    if 'attachTo' in params:
        attachOrgId = params['attachTo']
        if attachOrgId:
            cond = addAttachCond(db, cond, 'LPU_id=%d'%attachOrgId, *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachToNonBase' in params:
        cond = addAttachCond(db, cond, 'LPU_id!=%d'%QtGui.qApp.currentOrgId(), *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachType' in params:
        cond = addAttachCond(db, cond, '', *params['attachType'])
    excludeLeaved = params.get('excludeLeaved', False)
    if excludeLeaved:
        outerCond = ['ClientAttach.client_id = Client.id']
        innerCond = ['CA2.client_id = Client.id']
        cond.append('''EXISTS (SELECT ClientAttach.id
           FROM ClientAttach
           LEFT JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
           WHERE ClientAttach.deleted=0
           AND %s
           AND ClientAttach.id = (SELECT MAX(CA2.id)
                       FROM ClientAttach AS CA2
                       LEFT JOIN rbAttachType AS rbAttachType2 ON rbAttachType2.id = CA2.attachType_id
                       WHERE CA2.deleted=0 AND %s))'''% (QtGui.qApp.db.joinAnd(outerCond), QtGui.qApp.db.joinAnd(innerCond)))
        cond.append(tableClient['deathDate'].isNull())
    if 'dead' in params:
        cond.append(tableClient['deathDate'].isNotNull())
        if 'begDeathDate' in params:
            begDeathDate = params['begDeathDate']
            if begDeathDate:
                cond.append(tableClient['deathDate'].dateGe(begDeathDate))
        if 'endDeathDate' in params:
            endDeathDate = params['endDeathDate']
            if endDeathDate:
                cond.append(tableClient['deathDate'].dateLe(endDeathDate))
    isDispanser = params.get('isDispanser', False)
    if params.get('MKBFrom'):
        cond.append(tableDiagnosis['MKB'].ge(params.get('MKBFrom')))
    if params.get('MKBTo'):
        cond.append(tableDiagnosis['MKB'].le(params.get('MKBTo')))
    if isDispanser:
        cond.append(u'''IF((SELECT MAX(rbDispanser.observed)
        FROM
        Diagnostic AS D1
        LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
        WHERE
          D1.diagnosis_id = Diagnosis.id
          AND rbDispanser.observed = 1
          AND D1.endDate = (
            SELECT MAX(D2.endDate)
            FROM Diagnostic AS D2
            WHERE D2.diagnosis_id = Diagnosis.id
              AND D2.dispanser_id IS NOT NULL
              AND D2.endDate < %s)) = 1, 1, 0)''' % (tableDiagnosis['setDate'].formatValue(endDate.addDays(1))))
    return db.query(stmt % (begDate.toString("yyyy-MM-dd"), 
                            endDate.toString("yyyy-MM-dd"),
                            db.joinAnd([tableDiagnosis['setDate'].le(endDate),
                                        tableDiagnosis['setDate'].ge(begDate)]),
                            stmtAddress,
                            db.joinAnd(cond)))


def selectRemoveDispData(begDate, endDate, eventPurposeId, eventTypeIdList, orgStructureIdList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params):
    stmt = u"""
SELECT
   Diagnosis.MKB AS MKB,
   COUNT(*) AS sickCount,
   rbDiagnosisType.code AS diagnosisType,
   Diagnosis.client_id,
   IF(Client.deathDate is NULL, 0, 1) AS isDead,
    (SELECT D3.MKB
     FROM Diagnosis AS D3 
     LEFT JOIN Diagnostic AS D4 ON D4.diagnosis_id = D3.id
     LEFT JOIN Event AS E2 ON E2.id = D4.event_id
     LEFT JOIN EventType AS ET2 ON ET2.id = E2.eventType_id
     WHERE E2.client_id = Client.id AND ET2.code in (15) LIMIT 1) AS deathMKB
   
FROM Diagnosis
LEFT JOIN Client ON Client.id = Diagnosis.client_id
%s
LEFT JOIN rbDiagnosisType    ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnosis.character_id
WHERE Diagnosis.diagnosisType_id NOT IN (SELECT RBDT.id FROM rbDiagnosisType AS RBDT WHERE RBDT.code = '7' OR RBDT.code = '11')
AND %s
GROUP BY MKB, rbDiagnosisType.id
    """
    db = QtGui.qApp.db
    tableDiagnosis  = db.table('Diagnosis')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tablePerson = db.table('Person')
    specialityId = params.get('specialityId', None)

    cond = []
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableDiagnosis['mod_id'].isNull())
    cond.append(tableClient['deleted'].eq(0))
    diagnosticQuery = tableDiagnostic
    diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                       tableDiagnostic['deleted'].eq(0)
                     ]
    addDateInRange(diagnosticCond, tableDiagnostic['setDate'], begDate, endDate)
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    tableRBDispanser = db.table('rbDispanser')
    diagnosticQuery = diagnosticQuery.leftJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
    diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
    diagnosticQuery = diagnosticQuery.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    diagnosticCond.append(tableRBDispanser['code'].inlist(['3','4','5']))
    if specialityId:
        diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['speciality_id'].eq(specialityId))
        diagnosticCond.append(tablePerson['deleted'].eq(0))
    isPersonPost = params.get('isPersonPost', 0)
    if isPersonPost:
        tableRBPost = db.table('rbPost')
        if not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticQuery = diagnosticQuery.leftJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
        if isPersonPost == 1:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('1','2','3') ''')
        elif isPersonPost == 2:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('4','5','6','7','8','9')''')
    if personId:
        diagnosticCond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureIdList:
        if not isPersonPost and not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureListDescendants(orgStructureIdList)))
    else:
        if not isPersonPost and not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if eventTypeIdList:
        diagnosticCond.append(tableEvent['eventType_id'].inlist(eventTypeIdList))
    elif eventPurposeId:
        diagnosticCond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    cond.append(db.existsStmt(diagnosticQuery, diagnosticCond))

    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        cond.append('Client.birthDate <= ADDDATE(%s, INTERVAL -%d YEAR)' % (tableDiagnosis['setDate'].formatValue(QDate(endDate.year(), 12, 31)), ageFrom))
        cond.append('Client.birthDate >= ADDDATE(ADDDATE(%s, INTERVAL -%d YEAR),1)' % (tableDiagnosis['setDate'].formatValue(QDate(endDate.year(), 12, 31)), ageTo+1))
    if socStatusTypeId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusType_id=%d' % socStatusTypeId)
        cond.append('EXISTS('+subStmt+')')
    elif socStatusClassId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusClass_id=%d' % socStatusClassId)
        cond.append('EXISTS('+subStmt+')')
    stmtAddress = ''
    if isFilterAddressOrgStructure:
        addrIdList = None
        cond2 = []
        if (addrType+1) & 1:
            addrIdList = getOrgStructureAddressIdList(addressOrgStructureId)
            cond2 = addAddressCond(db, cond2, 0, addrIdList)
        if (addrType+1) & 2:
            if addrIdList is None:
                addrIdList = getOrgStructureAddressIdList(addressOrgStructureId)
            cond2 = addAddressCond(db, cond2, 1, addrIdList)
        if ((addrType+1) & 4):
            if addressOrgStructureId:
                cond2 = addAttachCond(db, cond2, 'orgStructure_id = %d'%addressOrgStructureId, 1, None)
            else:
                cond2 = addAttachCond(db, cond2, 'LPU_id=%d'%QtGui.qApp.currentOrgId(), 1, None)
        if cond2:
            cond.append(db.joinOr(cond2))
    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
    filterAddress = params.get('isFilterAddress', False)
    if filterAddress:
        stmtAddress += u'''INNER JOIN ClientAddress ON ClientAddress.client_id = Client.id
                              INNER JOIN Address ON Address.id = ClientAddress.address_id
                              INNER JOIN AddressHouse ON AddressHouse.id = Address.house_id'''
        cond.append('ClientAddress.id IN (%s)'%(getFilterAddress(params)))
    if 'attachTo' in params:
        attachOrgId = params['attachTo']
        if attachOrgId:
            cond = addAttachCond(db, cond, 'LPU_id=%d'%attachOrgId, *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachToNonBase' in params:
        cond = addAttachCond(db, cond, 'LPU_id!=%d'%QtGui.qApp.currentOrgId(), *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachType' in params:
        cond = addAttachCond(db, cond, '', *params['attachType'])
    excludeLeaved = params.get('excludeLeaved', False)
    if excludeLeaved:
        outerCond = ['ClientAttach.client_id = Client.id']
        innerCond = ['CA2.client_id = Client.id']
        cond.append('''EXISTS (SELECT ClientAttach.id
           FROM ClientAttach
           LEFT JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
           WHERE ClientAttach.deleted=0
           AND %s
           AND ClientAttach.id = (SELECT MAX(CA2.id)
                       FROM ClientAttach AS CA2
                       LEFT JOIN rbAttachType AS rbAttachType2 ON rbAttachType2.id = CA2.attachType_id
                       WHERE CA2.deleted=0 AND %s))'''% (QtGui.qApp.db.joinAnd(outerCond), QtGui.qApp.db.joinAnd(innerCond)))
        cond.append(tableClient['deathDate'].isNull())
    if 'dead' in params:
        cond.append(tableClient['deathDate'].isNotNull())
        if 'begDeathDate' in params:
            begDeathDate = params['begDeathDate']
            if begDeathDate:
                cond.append(tableClient['deathDate'].dateGe(begDeathDate))
        if 'endDeathDate' in params:
            endDeathDate = params['endDeathDate']
            if endDeathDate:
                cond.append(tableClient['deathDate'].dateLe(endDeathDate))
    isDispanser = params.get('isDispanser', False)
    if params.get('MKBFrom'):
        cond.append(tableDiagnosis['MKB'].ge(params.get('MKBFrom')))
    if params.get('MKBTo'):
        cond.append(tableDiagnosis['MKB'].le(params.get('MKBTo')))
    if isDispanser:
        cond.append(u'''IF((SELECT MAX(rbDispanser.observed)
        FROM
        Diagnostic AS D1
        LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
        WHERE
          D1.diagnosis_id = Diagnosis.id
          AND rbDispanser.observed = 1
          AND D1.endDate = (
            SELECT MAX(D2.endDate)
            FROM Diagnostic AS D2
            WHERE D2.diagnosis_id = Diagnosis.id
              AND D2.dispanser_id IS NOT NULL
              AND D2.endDate < %s)) = 1, 1, 0)'''%(tableDiagnosis['setDate'].formatValue(endDate.addDays(1))))
    return db.query(stmt % (stmtAddress,
                            db.joinAnd(cond)))


def selectObservedData(begDate, endDate, eventPurposeId, eventTypeIdList, orgStructureIdList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params):
    stmt = u"""
SELECT
   Diagnosis.MKB AS MKB,
   COUNT(*) AS sickCount,
   Client.sex AS sex,
   Client.deathDate AS isDead,
    (SELECT D3.MKB
     FROM Diagnosis AS D3 
     LEFT JOIN Diagnostic AS D4 ON D4.diagnosis_id = D3.id
     LEFT JOIN Event AS E2 ON E2.id = D4.event_id
     LEFT JOIN EventType AS ET2 ON ET2.id = E2.eventType_id
     WHERE E2.client_id = Client.id AND ET2.code in (15) LIMIT 1) AS deathMKB
     
FROM Diagnosis
LEFT JOIN Client ON Client.id = Diagnosis.client_id
%s
LEFT JOIN rbDiagnosisType    ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnosis.character_id
WHERE Diagnosis.diagnosisType_id NOT IN (SELECT RBDT.id FROM rbDiagnosisType AS RBDT WHERE RBDT.code = '7' OR RBDT.code = '11')
AND %s
GROUP BY MKB, sex
    """
    db = QtGui.qApp.db
    tableDiagnosis  = db.table('Diagnosis')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tablePerson = db.table('Person')
    specialityId = params.get('specialityId', None)

    cond = []
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableDiagnosis['mod_id'].isNull())
    cond.append(tableClient['deleted'].eq(0))
    diagnosticQuery = tableDiagnostic
    diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                       tableDiagnostic['deleted'].eq(0)
                     ]
    if specialityId:
        diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['speciality_id'].eq(specialityId))
        diagnosticCond.append(tablePerson['deleted'].eq(0))
    isPersonPost = params.get('isPersonPost', 0)
    if isPersonPost:
        tableRBPost = db.table('rbPost')
        if not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticQuery = diagnosticQuery.leftJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
        if isPersonPost == 1:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('1','2','3') ''')
        elif isPersonPost == 2:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('4','5','6','7','8','9')''')
    if personId:
        diagnosticCond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureIdList:
        if not isPersonPost and not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureListDescendants(orgStructureIdList)))
    else:
        if not isPersonPost and not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if eventTypeIdList:
        tableEvent = db.table('Event')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticCond.append(tableEvent['eventType_id'].inlist(eventTypeIdList))
    elif eventPurposeId:
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticQuery = diagnosticQuery.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        diagnosticCond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    cond.append(db.existsStmt(diagnosticQuery, diagnosticCond))

    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        cond.append('Client.birthDate <= ADDDATE(%s, INTERVAL -%d YEAR)' % (tableDiagnosis['setDate'].formatValue(QDate(endDate.year(), 12, 31)), ageFrom))
        cond.append('Client.birthDate >= ADDDATE(ADDDATE(%s, INTERVAL -%d YEAR),1)' % (tableDiagnosis['setDate'].formatValue(QDate(endDate.year(), 12, 31)), ageTo+1))
    if socStatusTypeId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusType_id=%d' % socStatusTypeId)
        cond.append('EXISTS('+subStmt+')')
    elif socStatusClassId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusClass_id=%d' % socStatusClassId)
        cond.append('EXISTS('+subStmt+')')
    stmtAddress = ''
    if isFilterAddressOrgStructure:
        addrIdList = None
        cond2 = []
        if (addrType+1) & 1:
            addrIdList = getOrgStructureAddressIdList(addressOrgStructureId)
            cond2 = addAddressCond(db, cond2, 0, addrIdList)
        if (addrType+1) & 2:
            if addrIdList is None:
                addrIdList = getOrgStructureAddressIdList(addressOrgStructureId)
            cond2 = addAddressCond(db, cond2, 1, addrIdList)
        if ((addrType+1) & 4):
            if addressOrgStructureId:
                cond2 = addAttachCond(db, cond2, 'orgStructure_id = %d'%addressOrgStructureId, 1, None)
            else:
                cond2 = addAttachCond(db, cond2, 'LPU_id=%d'%QtGui.qApp.currentOrgId(), 1, None)
        if cond2:
            cond.append(db.joinOr(cond2))
    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
    filterAddress = params.get('isFilterAddress', False)
    if filterAddress:
        if not stmtAddress:
            stmtAddress = u'''INNER JOIN ClientAddress ON ClientAddress.client_id = Client.id
                              INNER JOIN Address ON Address.id = ClientAddress.address_id
                              INNER JOIN AddressHouse ON AddressHouse.id = Address.house_id'''
        else:
            stmtAddress += u''' INNER JOIN AddressHouse ON AddressHouse.id = Address.house_id'''
        cond.append('ClientAddress.id IN (%s)'%(getFilterAddress(params)))
    if 'attachTo' in params:
        attachOrgId = params['attachTo']
        if attachOrgId:
            cond = addAttachCond(db, cond, 'LPU_id=%d'%attachOrgId, *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachToNonBase' in params:
        cond = addAttachCond(db, cond, 'LPU_id!=%d'%QtGui.qApp.currentOrgId(), *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachType' in params:
        cond = addAttachCond(db, cond, '', *params['attachType'])
    excludeLeaved = params.get('excludeLeaved', False)
    if excludeLeaved:
        outerCond = ['ClientAttach.client_id = Client.id']
        innerCond = ['CA2.client_id = Client.id']
        cond.append('''EXISTS (SELECT ClientAttach.id
           FROM ClientAttach
           LEFT JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
           WHERE ClientAttach.deleted=0
           AND %s
           AND ClientAttach.id = (SELECT MAX(CA2.id)
                       FROM ClientAttach AS CA2
                       LEFT JOIN rbAttachType AS rbAttachType2 ON rbAttachType2.id = CA2.attachType_id
                       WHERE CA2.deleted=0 AND %s))'''% (QtGui.qApp.db.joinAnd(outerCond), QtGui.qApp.db.joinAnd(innerCond)))
        cond.append(tableClient['deathDate'].isNull())
    if 'dead' in params:
        cond.append(tableClient['deathDate'].isNotNull())
        if 'begDeathDate' in params:
            begDeathDate = params['begDeathDate']
            if begDeathDate:
                cond.append(tableClient['deathDate'].dateGe(begDeathDate))
        if 'endDeathDate' in params:
            endDeathDate = params['endDeathDate']
            if endDeathDate:
                cond.append(tableClient['deathDate'].dateLe(endDeathDate))
    if params.get('MKBFrom'):
        cond.append(tableDiagnosis['MKB'].ge(params.get('MKBFrom')))
    if params.get('MKBTo'):
        cond.append(tableDiagnosis['MKB'].le(params.get('MKBTo')))
    cond.append(u'''IF((SELECT MAX(rbDispanser.observed)
        FROM
        Diagnostic AS D1
        LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
        WHERE
          D1.diagnosis_id = Diagnosis.id
          AND rbDispanser.observed = 1
          AND D1.endDate = (
            SELECT MAX(D2.endDate)
            FROM Diagnostic AS D2
            WHERE D2.diagnosis_id = Diagnosis.id
              AND D2.dispanser_id IS NOT NULL
              AND D2.endDate < %s)) = 1, 1, 0)'''%(tableDiagnosis['setDate'].formatValue(begDate.addDays(1))))
    return db.query(stmt % (stmtAddress,
                            db.joinAnd(cond)))


def selectDataClient(begDate, endDate, eventPurposeId, eventTypeIdList, orgStructureIdList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params):
    stmt="""
SELECT
   Diagnosis.client_id,
   (%s) AS firstInPeriod,
   AGE(Client.birthDate, %s) as isAdult

FROM Diagnosis
LEFT JOIN Client ON Client.id = Diagnosis.client_id
%s
LEFT JOIN rbDiagnosisType    ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnosis.character_id
WHERE %s
GROUP BY Diagnosis.client_id, Diagnosis.MKB
ORDER BY firstInPeriod DESC
    """
    db = QtGui.qApp.db
    tableDiagnosis  = db.table('Diagnosis')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tablePerson = db.table('Person')
    specialityId = params.get('specialityId', None)

    cond = []
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableDiagnosis['mod_id'].isNull())
    cond.append(tableDiagnosis['MKB'].notlike(u'%Z%'))
    cond.append(tableClient['deleted'].eq(0))
    diagnosticQuery = tableDiagnostic
    diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                       tableDiagnostic['deleted'].eq(0)
                     ]
    addDateInRange(diagnosticCond, tableDiagnostic['setDate'], begDate, endDate)
    if specialityId:
        diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['speciality_id'].eq(specialityId))
        diagnosticCond.append(tablePerson['deleted'].eq(0))
    if personId:
        diagnosticCond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureIdList:
        if not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureListDescendants(orgStructureIdList)))
    else:
        if not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if eventTypeIdList:
        tableEvent = db.table('Event')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticCond.append(tableEvent['eventType_id'].inlist(eventTypeIdList))
    elif eventPurposeId:
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticQuery = diagnosticQuery.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        diagnosticCond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    cond.append(db.existsStmt(diagnosticQuery, diagnosticCond))

    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        cond.append('Client.birthDate <= ADDDATE(%s, INTERVAL -%d YEAR)' % (tableDiagnosis['setDate'].formatValue(QDate(endDate.year(), 12, 31)), ageFrom))
        cond.append('Client.birthDate >= ADDDATE(ADDDATE(%s, INTERVAL -%d YEAR),1)' % (tableDiagnosis['setDate'].formatValue(QDate(endDate.year(), 12, 31)), ageTo+1))
    if socStatusTypeId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusType_id=%d' % socStatusTypeId)
        cond.append('EXISTS('+subStmt+')')
    elif socStatusClassId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusClass_id=%d' % socStatusClassId)
        cond.append('EXISTS('+subStmt+')')
    stmtAddress = u''''''
    if isFilterAddressOrgStructure:
        addrIdList = None
        cond2 = []
        if (addrType+1) & 1:
            addrIdList = getOrgStructureAddressIdList(addressOrgStructureId)
            cond2 = addAddressCond(db, cond2, 0, addrIdList)
        if (addrType+1) & 2:
            if addrIdList is None:
                addrIdList = getOrgStructureAddressIdList(addressOrgStructureId)
            cond2 = addAddressCond(db, cond2, 1, addrIdList)
        if ((addrType+1) & 4):
            if addressOrgStructureId:
                cond2 = addAttachCond(db, cond2, 'orgStructure_id = %d'%addressOrgStructureId, 1, None)
            else:
                cond2 = addAttachCond(db, cond2, 'LPU_id=%d'%QtGui.qApp.currentOrgId(), 1, None)
        if cond2:
            cond.append(db.joinOr(cond2))
    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
    filterAddress = params.get('isFilterAddress', False)
    if filterAddress:
        stmtAddress += u'''INNER JOIN ClientAddress ON ClientAddress.client_id = Client.id
                              INNER JOIN Address ON Address.id = ClientAddress.address_id
                              INNER JOIN AddressHouse ON AddressHouse.id = Address.house_id'''
        cond.append('ClientAddress.id IN (%s)'%(getFilterAddress(params)))
    if 'attachTo' in params:
        attachOrgId = params['attachTo']
        if attachOrgId:
            cond = addAttachCond(db, cond, 'LPU_id=%d'%attachOrgId, *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachToNonBase' in params:
        cond = addAttachCond(db, cond, 'LPU_id!=%d'%QtGui.qApp.currentOrgId(), *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachType' in params:
        cond = addAttachCond(db, cond, '', *params['attachType'])
    excludeLeaved = params.get('excludeLeaved', False)
    if excludeLeaved:
        outerCond = ['ClientAttach.client_id = Client.id']
        innerCond = ['CA2.client_id = Client.id']
        cond.append('''EXISTS (SELECT ClientAttach.id
           FROM ClientAttach
           LEFT JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
           WHERE ClientAttach.deleted=0
           AND %s
           AND ClientAttach.id = (SELECT MAX(CA2.id)
                       FROM ClientAttach AS CA2
                       LEFT JOIN rbAttachType AS rbAttachType2 ON rbAttachType2.id = CA2.attachType_id
                       WHERE CA2.deleted=0 AND %s))'''% (QtGui.qApp.db.joinAnd(outerCond), QtGui.qApp.db.joinAnd(innerCond)))
        cond.append(tableClient['deathDate'].isNull())
    if 'dead' in params:
        cond.append(tableClient['deathDate'].isNotNull())
        if 'begDeathDate' in params:
            begDeathDate = params['begDeathDate']
            if begDeathDate:
                cond.append(tableClient['deathDate'].dateGe(begDeathDate))
        if 'endDeathDate' in params:
            endDeathDate = params['endDeathDate']
            if endDeathDate:
                cond.append(tableClient['deathDate'].dateLe(endDeathDate))
    isDispanser = params.get('isDispanser', False)
    if isDispanser:
        cond.append(u'''IF((SELECT MAX(rbDispanser.observed)
        FROM
        Diagnostic AS D1
        LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
        WHERE
          D1.diagnosis_id = Diagnosis.id
          AND rbDispanser.observed = 1
          AND D1.endDate = (
            SELECT MAX(D2.endDate)
            FROM Diagnostic AS D2
            WHERE D2.diagnosis_id = Diagnosis.id
              AND D2.dispanser_id IS NOT NULL
              AND D2.endDate < %s)) = 1, 1, 0)'''%(tableDiagnosis['setDate'].formatValue(endDate.addDays(1))))
    return db.query(stmt % (db.joinAnd([tableDiagnosis['setDate'].le(endDate),
                                            tableDiagnosis['setDate'].ge(begDate)]),
                                tableDiagnosis['setDate'].formatValue(QDate(endDate.year(), 12, 31)),
                                stmtAddress,
                                db.joinAnd(cond)))


def selectObservedDataClient(begDate, endDate, eventPurposeId, eventTypeIdList, orgStructureIdList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params):
    stmt="""
SELECT
   Diagnosis.client_id,
   rbDiseaseCharacter.code AS diseaseCharacter,
   Diagnosis.MKB
FROM Diagnosis
LEFT JOIN Client ON Client.id = Diagnosis.client_id
%s
LEFT JOIN rbDiagnosisType    ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnosis.character_id
WHERE Diagnosis.diagnosisType_id NOT IN (SELECT RBDT.id FROM rbDiagnosisType AS RBDT WHERE RBDT.code = '7' OR RBDT.code = '11') AND %s
GROUP BY Diagnosis.client_id, diseaseCharacter, Diagnosis.MKB
    """
    db = QtGui.qApp.db
    tableDiagnosis  = db.table('Diagnosis')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tablePerson = db.table('Person')
    specialityId = params.get('specialityId', None)

    cond = []
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableDiagnosis['mod_id'].isNull())
    cond.append(tableDiagnosis['MKB'].notlike(u'%Z%'))
    cond.append(tableClient['deleted'].eq(0))
    diagnosticQuery = tableDiagnostic
    diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                       tableDiagnostic['deleted'].eq(0)
                     ]
    if specialityId:
        diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['speciality_id'].eq(specialityId))
        diagnosticCond.append(tablePerson['deleted'].eq(0))
    if personId:
        diagnosticCond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureIdList:
        if not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureListDescendants(orgStructureIdList)))
    else:
        if not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if eventTypeIdList:
        tableEvent = db.table('Event')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticCond.append(tableEvent['eventType_id'].inlist(eventTypeIdList))
    elif eventPurposeId:
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticQuery = diagnosticQuery.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        diagnosticCond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    cond.append(db.existsStmt(diagnosticQuery, diagnosticCond))

    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        cond.append('Client.birthDate <= ADDDATE(%s, INTERVAL -%d YEAR)' % (tableDiagnosis['setDate'].formatValue(QDate(endDate.year(), 12, 31)), ageFrom))
        cond.append('Client.birthDate >= ADDDATE(ADDDATE(%s, INTERVAL -%d YEAR),1)' % (tableDiagnosis['setDate'].formatValue(QDate(endDate.year(), 12, 31)), ageTo+1))
    if socStatusTypeId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusType_id=%d' % socStatusTypeId)
        cond.append('EXISTS('+subStmt+')')
    elif socStatusClassId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusClass_id=%d' % socStatusClassId)
        cond.append('EXISTS('+subStmt+')')
    stmtAddress = u''''''
    if isFilterAddressOrgStructure:
        addrIdList = None
        cond2 = []
        if (addrType+1) & 1:
            addrIdList = getOrgStructureAddressIdList(addressOrgStructureId)
            cond2 = addAddressCond(db, cond2, 0, addrIdList)
        if (addrType+1) & 2:
            if addrIdList is None:
                addrIdList = getOrgStructureAddressIdList(addressOrgStructureId)
            cond2 = addAddressCond(db, cond2, 1, addrIdList)
        if ((addrType+1) & 4):
            if addressOrgStructureId:
                cond2 = addAttachCond(db, cond2, 'orgStructure_id = %d'%addressOrgStructureId, 1, None)
            else:
                cond2 = addAttachCond(db, cond2, 'LPU_id=%d'%QtGui.qApp.currentOrgId(), 1, None)
        if cond2:
            cond.append(db.joinOr(cond2))
    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
    filterAddress = params.get('isFilterAddress', False)
    if filterAddress:
        if not stmtAddress:
            stmtAddress = u'''INNER JOIN ClientAddress ON ClientAddress.client_id = Client.id
                              INNER JOIN Address ON Address.id = ClientAddress.address_id
                              INNER JOIN AddressHouse ON AddressHouse.id = Address.house_id'''
        else:
            stmtAddress += u''' INNER JOIN AddressHouse ON AddressHouse.id = Address.house_id'''
        cond.append('ClientAddress.id IN (%s)'%(getFilterAddress(params)))
    if 'attachTo' in params:
        attachOrgId = params['attachTo']
        if attachOrgId:
            cond = addAttachCond(db, cond, 'LPU_id=%d'%attachOrgId, *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachToNonBase' in params:
        cond = addAttachCond(db, cond, 'LPU_id!=%d'%QtGui.qApp.currentOrgId(), *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachType' in params:
        cond = addAttachCond(db, cond, '', *params['attachType'])
    excludeLeaved = params.get('excludeLeaved', False)
    if excludeLeaved:
        outerCond = ['ClientAttach.client_id = Client.id']
        innerCond = ['CA2.client_id = Client.id']
        cond.append('''EXISTS (SELECT ClientAttach.id
           FROM ClientAttach
           LEFT JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
           WHERE ClientAttach.deleted=0
           AND %s
           AND ClientAttach.id = (SELECT MAX(CA2.id)
                       FROM ClientAttach AS CA2
                       LEFT JOIN rbAttachType AS rbAttachType2 ON rbAttachType2.id = CA2.attachType_id
                       WHERE CA2.deleted=0 AND %s))'''% (QtGui.qApp.db.joinAnd(outerCond), QtGui.qApp.db.joinAnd(innerCond)))
        cond.append(tableClient['deathDate'].isNull())
    if 'dead' in params:
        cond.append(tableClient['deathDate'].isNotNull())
        if 'begDeathDate' in params:
            begDeathDate = params['begDeathDate']
            if begDeathDate:
                cond.append(tableClient['deathDate'].dateGe(begDeathDate))
        if 'endDeathDate' in params:
            endDeathDate = params['endDeathDate']
            if endDeathDate:
                cond.append(tableClient['deathDate'].dateLe(endDeathDate))
    cond.append(u'''IF((SELECT MAX(rbDispanser.observed)
        FROM
        Diagnostic AS D1
        LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
        WHERE
          D1.diagnosis_id = Diagnosis.id
          AND rbDispanser.observed = 1
          AND D1.endDate = (
            SELECT MAX(D2.endDate)
            FROM Diagnostic AS D2
            WHERE D2.diagnosis_id = Diagnosis.id
              AND D2.dispanser_id IS NOT NULL
              AND D2.endDate < %s)) = 1, 1, 0)'''%(tableDiagnosis['setDate'].formatValue(QDate(endDate.year(), 12, 31))))
    return db.query(stmt % (stmtAddress,
                            db.joinAnd(cond)))


class CStatReportF12Teenagers_2022(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Дети (15-17 лет включительно)')


    def getDefaultParams(self):
        result = CReport.getDefaultParams(self)
        result['ageFrom'] = 15
        result['ageTo']   = 17
        return result
    
    
    def dumpParamsMultiSelect(self, cursor, params):
        description = []
        eventTypeList = params.get('eventTypeList', None)
        if eventTypeList:
            db = QtGui.qApp.db
            tableET = db.table('EventType')
            records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(eventTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            description.append(u'тип события:  %s'%(u','.join(name for name in nameList if name)))
        else:
            description.append(u'тип события:  не задано')
        orgStructureList = params.get('orgStructureList', None)
        if orgStructureList:
            if len(orgStructureList) == 1 and not orgStructureList[0]:
                description.append(u'подразделение: ЛПУ')
            else:
                db = QtGui.qApp.db
                table = db.table('OrgStructure')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(orgStructureList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                description.append(u'подразделение:  %s'%(u','.join(name for name in nameList if name)))
        else:
            description.append(u'подразделение: ЛПУ')
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
    

    def dumpParamsIsDispanser(self, cursor, params):
        description = []
        isDispanser = params.get('isDispanser', False)
        if isDispanser:
            description.append(u'Учитывать только состоящих на диспансерном наблюдении')
            columns = [ ('100%', [], CReportBase.AlignLeft) ]
            table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
            for i, row in enumerate(description):
                table.setText(i, 0, row)
            cursor.movePosition(QtGui.QTextCursor.End)


    def getSetupDialog(self, parent):
        result = CReportAcuteInfectionsSetupDialog(parent)
        result.setAreaEnabled(False)
        result.setFilterAddressOrgStructureVisible(True)
        result.setAllAddressSelectable(True)
        result.setAllAttachSelectable(True)
        result.setEventTypeListListVisible(True)
        result.setOrgStructureListVisible(True)
        result.setSpecialityVisible(True)
        result.setCMBEventTypeVisible(False)
        result.setCMBOrgStructureVisible(False)
        result.setChkFilterDispanser(True)
        result.setTitle(self.title())
        result.chkDetailMKB.setVisible(True)
        result.chkFilterExcludeLeaved.setVisible(False)
        result.chkFilterExcludeLeaved.setChecked(False)
        result.chkRegisteredInPeriod.setChecked(True)
        result.chkRegisteredInPeriod.setVisible(False)
        result.setUseInputDate(False)
        return result
    
    
    def build(self, params):
        mapMainRows = createMapCodeToRowIdx( [row[2] for row in MainRows] )
        mapCompRows = createMapCodeToRowIdx( [row[2] for row in CompRows] )
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        eventPurposeId = params.get('eventPurposeId', None)
        eventTypeList = params.get('eventTypeList', None)
        orgStructureList = params.get('orgStructureList', None)
        personId = params.get('personId', None)
        sex = params.get('sex', 0)
        ageFrom = params.get('ageFrom', 15)
        ageTo = params.get('ageTo', 17)
        socStatusClassId = params.get('socStatusClassId', None)
        socStatusTypeId = params.get('socStatusTypeId', None)
        isFilterAddressOrgStructure = params.get('isFilterAddressOrgStructure', False)
        addrType = params.get('addressOrgStructureType', 0)
        addressOrgStructureId = params.get('addressOrgStructure', None)
        locality = params.get('locality', 0)
        detailMKB = params.get('detailMKB', False)
        reportLine = None

        rowSize = 11
        rowCompSize = 4
        if detailMKB:
            reportMainData = {}  # { MKB: [reportLine] }
            reportCompData = {}  # { MKB: [reportLine] }
        else:
            reportMainData = [ [0]*rowSize for row in xrange(len(MainRows)) ]
            reportCompData = [ [0]*rowCompSize for row in xrange(len(CompRows)) ]
        
        registered2004 = [0, 0, 0, 0]
        registered2005 = [0, 0]
        query = selectData(begDate, endDate, eventPurposeId, eventTypeList, orgStructureList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params)
        while query.next():
            record = query.record()
            clientId = forceRef(record.value('client_id'))
            MKB = normalizeMKB(forceString(record.value('MKB')))
            sickCount = forceInt(record.value('sickCount'))
            diseaseCharacter = forceString(record.value('diseaseCharacter'))
            diagnosisType = forceString(record.value('diagnosisType'))
            sex = forceInt(record.value('sex'))
            firstInPeriod = forceBool(record.value('firstInPeriod'))
            closedEvent = forceBool(record.value('closedEvent'))
            getObserved = forceInt(record.value('getObserved'))
            getProfilactic = forceBool(record.value('getProfilactic'))
            isNotPrimary = forceBool(record.value('isNotPrimary'))
            getAdultsDispans = forceBool(record.value('getAdultsDispans'))
            #isDead = forceBool(record.value('isDead'))
            #deathMKB = normalizeMKB(forceString(record.value('deathMKB')))
            
            cols = [0]
            if sex == 1:
                cols.append(1)
            if getObserved:
                cols.append(2)
                cols.append(9)
                if sex == 1:
                    cols.append(10)
                if MKB.startswith('I'):
                    registered2004[0] = registered2004[0] + sickCount
            if getAdultsDispans:
                cols.append(6)
            if diseaseCharacter == '1': # острое
                cols.append(3)
                if sex == 1 and MKB.startswith('E66'):
                    registered2005[0] += sickCount
                    if MKB.startswith('E66.2'):
                        registered2005[1] += sickCount
                if getObserved:
                    cols.append(4)
                if getProfilactic:
                    cols.append(5)
                if sex == 1:
                    cols.append(7)
            elif firstInPeriod:
                cols.append(3)
                if sex == 1 and MKB.startswith('E66'):
                    registered2005[0] += sickCount
                    if MKB.startswith('E66.2'):
                        registered2005[1] += sickCount
                if getObserved:
                    cols.append(4)
                if getProfilactic:
                    cols.append(5)
                if sex == 1:
                    cols.append(7)

            if detailMKB:
                reportLine = reportMainData.setdefault(MKB, [0]*rowSize)
                for col in cols:
                    reportLine[col] += sickCount
            else:
                for row in mapMainRows.get(MKB, []):
                    reportLine = reportMainData[row]
                    for col in cols:
                        reportLine[col] += sickCount

            if diagnosisType == '98':
                if detailMKB:
                    reportLine = reportCompData.setdefault(MKB, [0]*rowCompSize)
                    reportLine[0] += sickCount
                    if getProfilactic and isNotPrimary:
                        reportLine[1] += sickCount
                    if closedEvent:
                        reportLine[2] += sickCount
                else:
                    for row in mapCompRows.get(MKB, []):
                        reportLine = reportCompData[row]
                        reportLine[0] += sickCount
                        if getProfilactic and isNotPrimary:
                            reportLine[1] += sickCount
                        if closedEvent:
                            reportLine[2] += sickCount
        
        sex = params.get('sex', 0)
        queryRemove = selectRemoveDispData(begDate, endDate, eventPurposeId, eventTypeList, orgStructureList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params)
        while queryRemove.next():
            record = queryRemove.record()
            MKB = normalizeMKB(forceString(record.value('MKB')))
            sickCount = forceInt(record.value('sickCount'))
            isDead = forceBool(record.value('isDead'))
            deathMKB = normalizeMKB(forceString(record.value('deathMKB')))
            
            cols = [8]

            if MKB.startswith('I'):
                registered2004[1] = registered2004[1] + sickCount
                if isDead:
                    registered2004[2] = registered2004[2] + sickCount
                    if deathMKB.startswith('I'):
                        registered2004[3] = registered2004[3] + sickCount
                        
            if detailMKB:
                reportLine = reportMainData.setdefault(MKB, [0]*rowSize)
                for col in cols:
                    reportLine[col] += sickCount
                    reportLine[9] -= sickCount
                    if sex == 1:
                        reportLine[10] -= sickCount
                    if MKB.startswith('I'):
                        registered2004[0] = registered2004[0] - sickCount
            else:
                for row in mapMainRows.get(MKB, []):
                    reportLine = reportMainData[row]
                    for col in cols:
                        reportLine[col] += sickCount
                        reportLine[9] -= sickCount
                        if sex == 1:
                            reportLine[10] -= sickCount
                        if MKB.startswith('I'):
                            registered2004[0] = registered2004[0] + sickCount
        
        sex = params.get('sex', 0)
        queryObserved = selectObservedData(begDate, endDate, eventPurposeId, eventTypeList, orgStructureList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params)
        while queryObserved.next():
            record = queryObserved.record()
            MKB = normalizeMKB(forceString(record.value('MKB')))
            sex = forceInt(record.value('sex'))
            sickCount = forceInt(record.value('sickCount'))
            #isDead = forceBool(record.value('isDead'))
            #deathMKB = normalizeMKB(forceString(record.value('deathMKB')))
            
            cols = [2, 9, 10]
            if MKB.startswith('I'):
                registered2004[0] = registered2004[0] + sickCount
                
            if detailMKB:
                reportLine = reportMainData.setdefault(MKB, [0]*rowSize)
                for col in cols:
                    reportLine[col] += sickCount
            else:
                for row in mapMainRows.get(MKB, []):
                    reportLine = reportMainData[row]
                    for col in cols:
                        reportLine[col] += sickCount
        
        registeredAll = 0
        registeredFirst = 0
        gotAdult = 0
        clientIdList = []
        queryClient = selectDataClient(begDate, endDate, eventPurposeId, eventTypeList, orgStructureList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params)
        while queryClient.next():
            record = queryClient.record()
            clientId = forceRef(record.value('client_id'))
            firstInPeriod = forceBool(record.value('firstInPeriod'))
            isAdult = forceInt(record.value('isAdult'))
            
            if clientId and clientId not in clientIdList:
                clientIdList.append(clientId)
                registeredAll += 1
                if firstInPeriod:
                   registeredFirst += 1
                if isAdult >= 18:
                    gotAdult += 1

        consistsByEnd = [0, 0, 0]
        clientIdList = []
        clientIdFor2003List1 = {}
        clientIdFor2003List2 = {}
        queryObservedClient = selectObservedDataClient(begDate, endDate, eventPurposeId, eventTypeList, orgStructureList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params)
        while queryObservedClient.next():
            record = queryObservedClient.record()
            clientId = forceRef(record.value('client_id'))
            diseaseCharacter = forceString(record.value('diseaseCharacter'))
            MKB = normalizeMKB(forceString(record.value('MKB')))
            if clientId and MKB in [u'B18.2', u'B18.1', u'B18', u'B18.8', u'B18.9', u'K74.6']:
                clientIdFor20031 = clientIdFor2003List1.setdefault(clientId, [])
                if MKB not in clientIdFor20031:
                    clientIdFor20031.append(MKB)
            if clientId and MKB in [u'B18.2', u'B18.1', u'B18', u'B18.8', u'B18.9', u'C22.0']:
                clientIdFor20032 = clientIdFor2003List2.setdefault(clientId, [])
                if MKB not in clientIdFor20032:
                    clientIdFor20032.append(MKB)

            if clientId and clientId not in clientIdList:
                clientIdList.append(clientId)
                consistsByEnd[0] += 1
        for clientIdFor20031 in clientIdFor2003List1.values():
            consistsByEnd[1] += (1 if len(clientIdFor20031) == 2 else 0)
        for clientIdFor20032 in clientIdFor2003List2.values():
            consistsByEnd[2] += (1 if len(clientIdFor20032) == 2 else 0)
        
        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        chkFilterAttachType = params.get('chkFilterAttachType', False)
        dead = params.get('dead', False)
        chkFilterAttach = params.get('chkFilterAttach', False)
        attachToNonBase = params.get('attachToNonBase', False)
        excludeLeaved = params.get('excludeLeaved', False)
        if chkFilterAttachType or dead or chkFilterAttach or attachToNonBase or excludeLeaved:
           self.dumpParamsAttach(cursor, params)
        if params.get('isFilterAddress', False):
            self.dumpParamsAdress(cursor, params)
        self.dumpParamsMultiSelect(cursor, params)
        self.dumpParamsIsDispanser(cursor, params)
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.insertText(u'(2000)')
        cursor.insertBlock()

        tableColumns = [
            ('17%', [u'Наименование классов и отдельных болезней', u'', u'', u'1'], CReportBase.AlignLeft),
            ('5%', [u'№ строки', u'', u'', u'2'], CReportBase.AlignLeft),
            ('6.5%', [u'Код по МКБ-10 пересмотра', u'', u'', u'3'], CReportBase.AlignLeft),
            ('6.5%', [u'Зарегистрировано заболеваний ', u'Всего, ед', u'', u'4'], CReportBase.AlignRight),
            ('6.5%', [u'', u'из них: юноши', u'', u'5'], CReportBase.AlignRight),
            ('6.5%', [u'', u'из них(из гр. 4):', u'взято под диспансерное наблюдение, чел', u'6'], CReportBase.AlignRight),
            ('6.5%', [u'', u'', u'с впервые в жизни установленным диагнозом', u'7'], CReportBase.AlignRight),
            ('6.5%', [u'', u'из заболеваний с впервые в жизни установленным диагнозом (из гр. 7):', u'взято под диспансерное наблюдение, чел', u'8'], CReportBase.AlignRight),
            ('6.5%', [u'', u'', u'выявлено при профосмотре', u'9'], CReportBase.AlignRight),
            ('6.5%', [u'', u'', u'выявлено при диспансеризации', u'10'], CReportBase.AlignRight),
            ('6.5%', [u'', u'из заболеваний с впервые в жизни установленном диагнозом (из гр. 7) юноши', u'', u'11'], CReportBase.AlignRight),
            ('6.5%', [u'Снято с диспансерного наблюдения, чел', u'', u'', u'12'], CReportBase.AlignRight),
            ('6.5%', [u'Состоит на д.н. на конец периода, чел', u'', u'', u'13'], CReportBase.AlignRight),
            ('6.5%', [u'', u'из них (из гр. 15): юноши', u'', u'14'],CReportBase.AlignRight)
            ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1) # Наименование
        table.mergeCells(0, 1, 3, 1) # № стр.
        table.mergeCells(0, 2, 3, 1) # Код МКБ
        table.mergeCells(0, 3, 1, 8) # Всего
        table.mergeCells(1, 3, 2, 1)
        table.mergeCells(1, 4, 2, 1)
        table.mergeCells(1, 5, 1, 2)
        table.mergeCells(1, 7, 1, 3)
        table.mergeCells(1, 10, 2, 1)
        table.mergeCells(0, 11, 3, 1)
        table.mergeCells(0, 12, 3, 1)
        table.mergeCells(0, 13, 3, 1)

        if detailMKB:
            for row, MKB in enumerate(sorted(reportMainData.keys())):
                reportLine = reportMainData[MKB]
                if not MKB:
                    MKBDescr, MKB = u'', u'Не указано'
                else:
                    MKBDescr = forceString(QtGui.qApp.db.translate('MKB', 'DiagID', MKB, 'DiagName'))
                if MKB.endswith('.0') and not MKBDescr:
                    MKBDescr = forceString(QtGui.qApp.db.translate('MKB', 'DiagID', MKB[:-2], 'DiagName'))
                i = table.addRow()
                table.setText(i, 0, MKBDescr)
                table.setText(i, 1, row+1)
                table.setText(i, 2, MKB)
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])
        else:
            for row, rowDescr in enumerate(MainRows):
                reportLine = reportMainData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(self.format2001(registeredAll, registeredFirst, consistsByEnd[0], gotAdult))
        cursor.insertBlock()
        cursor.insertText(u'(2003) Из числа пациентов, состоящих на конец отчетного года под диспансерным наблюдением (гр. 13): состоит под диспансерным наблюдением лиц с хроническим вирусным гепатитом (B18) и циррозом печени (K74.6) одновременно %d чел.; с хроническим вирусным гепатитом (B18) и гепатоцеллюлярным раком (C22.0) одновременно %d чел.'%(consistsByEnd[1], consistsByEnd[2]))
        cursor.insertBlock()
        cursor.insertText(self.get2004(registered2004))
        cursor.insertBlock()
        cursor.insertText(
            u'(2005) Из числа с впервые в жизни  установленным диагнозом ожирение (из гр. 8 стр. 5.10) у юношей 1 - {}, ' \
            u'крайняя степень ожирения (из гр. 8 стр. 5.10.1) у юношей 2 - {}'.format(registered2005[0], registered2005[1]))
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock()
        cursor.insertText(u'Дети (15-17 лет включительно).')
        cursor.insertBlock()
        cursor.insertText(u'ФАКТОРЫ, ВЛИЯЮЩИЕ НА СОСТОЯНИЕ ЗДОРОВЬЯ НАСЕЛЕНИЯ')
        cursor.insertBlock()
        cursor.insertText(u'И ОБРАЩЕНИЯ В МЕДИЦИНСКИЕ ОРГАНИЗАЦИИ (С ПРОФИЛАКТИЧЕСКОЙ И ИНЫМИ ЦЕЛЯМИ)')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        cursor.insertText(u'(2100)')
        cursor.insertBlock()

        tableColumns = [
            ('30%', [u'Наименование', u'',                   u'1'], CReportBase.AlignLeft),
            ('10%', [u'№ строки',     u'',                   u'2'], CReportBase.AlignLeft),
            ('15%', [u'Код МКБ-10',   u'',                   u'3'], CReportBase.AlignLeft),
            ('15%', [u'Обращения',    u'всего',              u'4'], CReportBase.AlignRight),
            ('15%', [u'',             u'из них: повторные',  u'5'], CReportBase.AlignRight),
            ('15%', [u'',             u'законченные случаи', u'6'], CReportBase.AlignRight),
            ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 3)

        if detailMKB:
            for row, MKB in enumerate(sorted(reportCompData.keys())):
                reportLine = reportCompData[MKB]
                if not MKB:
                    MKBDescr, MKB = u'', u'Не указано'
                else:
                    MKBDescr = forceString(QtGui.qApp.db.translate('MKB', 'DiagID', MKB, 'DiagName'))
                if MKB.endswith('.0') and not MKBDescr:
                    MKBDescr = forceString(QtGui.qApp.db.translate('MKB', 'DiagID', MKB[:-2], 'DiagName'))
                i = table.addRow()
                table.setText(i, 0, MKBDescr)
                table.setText(i, 1, row+1)
                table.setText(i, 2, MKB)
                table.setText(i, 3, reportLine[0])
                table.setText(i, 4, reportLine[1])
                table.setText(i, 5, reportLine[2])
        else:
            for row, rowDescr in enumerate(CompRows):
                reportLine = reportCompData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                table.setText(i, 3, reportLine[0])
                table.setText(i, 4, reportLine[1])
                table.setText(i, 5, reportLine[2])

        cursor = doc.find(u'из них (из гр. 15): юноши')
        if cursor:
            cursor.removeSelectedText()
            cursor.setCharFormat(CReportBase.TableHeader)
            cursor.insertText(u'из них (из гр.13): юноши')

        return doc


    def format2001(self, registeredAll, registeredFirst, consistsByEnd, gotAdult):
        return u'(2001) Число физических лиц зарегистрированных пациентов - Всего (из стр.1.0, гр.4 ) 1 - {}, ' \
                u'из них с диагнозом, установленным впервые в жизни (из стр.1.0, гр.7 ) 2 - {}, ' \
                u'состоит под диспансерным наблюдением на конец отчетного года (из стр.1.0, гр.13 ) 3 - {}, ' \
                u'передано под наблюдение во взрослую поликлинику 4 - {}'.format(registeredAll, registeredFirst, consistsByEnd, gotAdult)
                

    def get2004(self, registered):
        return u'(2004) Число лиц с болезнями системы кровообращения,состоявших под диспансерным наблюдением (стр.10.0 гр.6) - {}, из них снято - {}, из них умерло (из графы 2) - {}, из них умерло от болезней системы кровообращения (из графы 3) - {}.'.format(registered[0], registered[1], registered[2], registered[3])

