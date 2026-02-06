# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
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
from library.Utils      import forceBool, forceDate, forceInt, forceRef, forceString

from Orgs.Utils         import getOrgStructureDescendants, getOrgStructures
from Reports.Report     import CReport, normalizeMKB
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportAcuteInfections import CReportAcuteInfectionsSetupDialog, addAttachCond, getFilterAddress


MainRows = [
    ( u'Зарегистрировано заболеваний - всего', u'1.0', u'A00-T98'),
    ( u'в том числе: некоторые инфекционные и паразитарные болезни', u'2.0', u'A00-B99'),
    ( u'из них: кишечные инфекции', u'2.1', u'A00-A09'),
    ( u'менингококковая инфекция', u'2.2', u'A39'),
    ( u'сепсис', u'2.3', u'A40-A41'),
    ( u'острый полиомиелит', u'2.4', u'A80'),
    ( u'вирусный гепатит', u'2.5', u'B15-B19'),
    ( u'новообразования', u'3.0', u'C00-D48'),
    ( u'из них: злокачественные новообразования', u'3.1', u'C00-C97'),
    ( u'из них: злокачественные новообразования лимфоидной, кроветворной и родственных им тканей', u'3.1.1', u'C81-C96'),
    ( u'доброкачественные новобразования', u'3.2', u'D10-D36'),
    ( u'болезни крови, кроветворных органов и отдельные нарушения, вовлекающие иммунный механизм', u'4.0', u'D50-D89'),
    ( u'из них: анемии', u'4.1', u'D50-D64'),
    ( u'из них апластические анемии', u'4.1.1', u'D60-D61'),
    ( u'нарушения свертываемости крови, пурпуа и другие гемморагические состояния', u'4.2', u'D65-D69'),
    ( u'из них: диссеминированное внутрисосудистое свертывание крови (синдром дефибринации)', u'4.2.1', u'D65'),
    ( u'гемофилия', u'4.2.2', u'D66-D68'),
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
    ( u'из него (из стр. 5.2):сахарный диабет I типа', u'5.2.2', u'E10'),
    ( u'сахарный диабет II типа', u'5.2.3', u'E11'),
    ( u'гиперфункция гипофиза', u'5.3', u'E22'),
    ( u'гипопитуитаризм', u'5.4', u'E23.0'),
    ( u'несахарный диабет', u'5.5', u'E23.2'),
    ( u'адреногенитальные расстройства', u'5.6', u'E25'),
    ( u'дисфункция яичников', u'5.7', u'E28'),
    ( u'дисфункция яичек', u'5.8', u'E29'),
    ( u'ожирение', u'5.9', u'E66'),
    ( u'фенилкетонурия', u'5.10', u'E70.0'),
    ( u'нарушения обмена галактозы (галактоземия)', u'5.11', u'E74.2'),
    ( u'болезнь Гоше', u'5.12', u'E75.2'),
    ( u'нарушения обмена гликозамигликанов (мукополисахаридоз)', u'5.13', u'E76'),
    ( u'муковисцидоз', u'5.14', u'E84'),
    ( u'психические расстройства и расстройства поведения', u'6.0', u'F01, F03-F99'),
    ( u'из них: психические расстройства и расстройства поведения, связанные с употреблением психоактивных веществ', u'6.1', u'F10-F19'),
    ( u'болезни нервной системы', u'7.0', u'G00-G98'),
    ( u'из них: воспалительные болезни центральной нервной системы', u'7.1', u'G00-G09'),
    ( u'из них: бактериальный менингит', u'7.1.1', u'G00'),
    ( u'из них: энцефалит, миелит и энцефаломиелит', u'7.1.2', u'G04'),
    ( u'системные атрофии, поражающие преимущественно нервную систему', u'7.2', u'G10-G12'),
    ( u'экстрапирамидные и другие двигательные нарушения', u'7.3', u'G20, G21, G23-G25'),
    ( u'из них: болезнь Паркинсона', u'7.3.1', u'G20'),
    ( u'другие экстрапирамидные и двигательные нарушения', u'7.3.2', u'G25'),
    ( u'другие дегенеративные болезни нервной системы', u'7.4', u'G30-G31'),
    ( u'из них: болезнь Альцгеймера', u'7.4.1', u'G30'),
    ( u'демиелинизирующие болезни центральной нервной системы', u'7.5', u'G35-G37'),
    ( u'из них: рассеянный склероз', u'7.5.1', u'G35'),
    ( u'эпизодические и пароксизмальные расстройства', u'7.6', u'G40-G47'),
    ( u'из них: эпилепсия, эпилептический статус', u'7.6.1', u'G40-G41'),
    ( u'преходящие транзиторные церебральные ишемические приступы (атаки) и родственные синдромы', u'7.6.2', u'G45'),
    ( u'поражения отдельных нервов, нервных корешков и сплетений, полиневропатии и другие поражения периферической нервной  системы', u'7.7', u'G50-G64'),
    ( u'из них: синдром Гийена-Барре', u'7.7.1', u'G61.0'),
    ( u'болезни нервно-мышечного синапса и мышц', u'7.8', u'G70-G73'),
    ( u'из них: миастения ', u'7.8.1', u'G70.0, 2, 9'),
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
    ( u'из них: болезни наружного уха', u'9.1', u'H60-H62'),
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
    ( u'гипертензивная болезнь сердца (гипертоническая болезнь с преимущественным поражением сердца)', u'10.3.2', u'I11'),
    ( u'гипертензивная (гипертоническая) болезнь с преимущественным поражением почек с почечной недостаточностью', u'10.3.3', u'I12'),
    ( u'гипертензивная (гипертоническая) болезнь с преимущественным поражением сердца и почек', u'10.3.4', u'I13'),
    ( u'ишемические болезни сердца', u'10.4', u'I20-I25'),
    ( u'из них: стенокардия', u'10.4.1', u'I20'),
    ( u'из нее: нестабильная стенокардия', u'10.4.1.1', u'I20.0'),
    ( u'острый инфаркт миокарда', u'10.4.2', u'I21'),
    ( u'повторный инфаркт миокарда', u'10.4.3', u'I22'),
    ( u'другие формы острой ишемической болезни сердца', u'10.4.4', u'I24'),
    ( u'хроническая ишемическая болезнь сердца', u'10.4.5', u'I25'),
    ( u'из нее постинфарктный кардиосклероз', u'10.4.5.1', u'I25.8'),
    ( u'легочная эмболия', u'10.5', u'I26'),
    ( u'другие болезни сердца', u'10.6', u'I30-I51'),
    ( u'из них: острый перикардит', u'10.6.1', u'I30'),
    ( u'из них: острый и подострый эндокардит', u'10.6.2', u'I33'),
    ( u'острый миокардит', u'10.6.3', u'I40'),
    ( u'кардиомиопатия', u'10.6.4', u'I42'),
    ( u'цереброваскулярные болезни', u'10.7', u'I60-I69'),
    ( u'из них: субарахноидальное кровоизлияние', u'10.7.1', u'I60'),
    ( u'внутримозговое и другое внутречерепное кровоизлияние', u'10.7.2', u'I61, I62'),
    ( u'инфаркт мозга', u'10.7.3', u'I63'),
    ( u'инсульт, не уточненный как кровоизлияние или инфаркт (инсульт церебральный)', u'10.7.4', u'I64'),
    ( u'закупорка и стеноз прецеребральных, церебральных артерий, не приводящие к инфаркту мозга ', u'10.7.5', u'I65- I66'),
    ( u'другие цереброваскулярные болезни', u'10.7.6', u'I67'),
    ( u'из них: церебральный атеросклероз', u'10.7.6.1', u'I67.2'),
    ( u'последствия церереброваскулярных болезней', u'10.7.7', u'I69'),
    ( u'эндартериит, тромбангиит облитерирующий', u'10.8', u'I70.2, I73.1'),
    ( u'болезни вен, лимфатических сосудов и лимфатических узлов', u'10.9', u'I80-I83, I85-I89'),
    ( u'из них: флебит и тромбофлебит', u'10.9.1', u'I80'),
    ( u'тромбоз портальной вены', u'10.9.2', u'I81'),
    ( u'варикозное расширение вен нижних конечностей', u'10.9.3', u'I83'),
    ( u'геморрой', u'10.9.4', u'I84'),
    ( u'болезни органов дыхания', u'11.0', u'J00-J98'),
    ( u'из них: острые респираторные инфекции верхних дыхательных путей', u'11.1', u'J00-J06'),
    ( u'из них: острый ларингит и трахеит', u'11.1.1', u'J04'),
    ( u'острый обструктивный ларингит (круп) и эпиглоттит', u'11.1.2', u'J05'),
    ( u'грипп', u'11.2', u'J09-J11'),
    ( u'острые респираторные инфекции нижних дыхательных путей', u'11.3', u'J12-J16, J18'),
    ( u'пневмония', u'11.4', u'J12-J18'),
    ( u'аллергический ринит (поллиноз)', u'11.5', u'J30.1'),
    ( u'хронические болезни миндалин и аденоидов, перитонзиллярный абсцесс', u'11.6', u'J35-J36'),
    ( u'бронхит хронический и неуточненный, эмфизема', u'11.7', u'J40-J43'),
    ( u'другая хроническая обструктивная легочная болезнь ', u'11.8', u'J44'),
    ( u'бронхоэктатическая болезнь', u'11.9', u'J47'),
    ( u'астма, астматический статус', u'11.10', u'J45, J46'),
    ( u'другие интерстициальные легочные болезни, гнойные и некротические состояния нижних дыхательных путей, другие болезни плевры', u'11.11', u'J84-J90, J92-J94'),
    ( u'болезни органов пищеварения', u'12.0', u'K00-K92'),
    ( u'из них: язвенная болезнь желудка и 12-ти перстной кишки', u'12.1', u'K25-K26'),
    ( u'гастрит и дуоденит', u'12.2', u'K29'),
    ( u'грыжи', u'12.3', u'K40-K46'),
    ( u'неинфекционный энтерит и колит', u'12.4', u'K50-K52'),
    ( u'другие болезни кишечника', u'12.5', u'K55-K63'),
    ( u'из них: паралитический илеус и непроходимость кишечника без грыжи', u'12.5.1', u'K56'),
    ( u'геморрой', u'12.6', u'K64'),
    ( u'перитонит', u'12.7', u'K65'),
    ( u'болезни печени', u'12.8', u'K70-K76'),
    ( u'из них: фиброз и цирроз печени', u'12.8.1', u'K74'),
    ( u'болезни желчного пузыря, желчевыводящих путей', u'12.9', u'K80-K83'),
    ( u'болезни поджелудочной железы', u'12.10', u'K85-K86'),
    ( u'из них: острый панкреатит', u'12.10.1', u'K85'),
    ( u'болезни кожи и подкожной клетчатки', u'13.0', u'L00-L99'),
    ( u'из них: пузырчатка', u'13.1', u'L10'),
    ( u'буллезный пемфигоид', u'13.2', u'L12'),
    ( u'дерматит герпетиформный Дюринга', u'13.3', u'L13.0'),
    ( u'атопический дерматит', u'13.4', u'L20'),
    ( u'контактный дерматит', u'13.5', u'L23-L25'),
    ( u'другие дерматиты (экзема)', u'13.6', u'L30'),
    ( u'псориаз', u'13.7', u'L40'),
    ( u'из него: псориаз артропатический', u'13.7.1', u'L40.5'),
    ( u'лишай красный плоский', u'13.8', u'L43'),
    ( u'дискоидная красная волчанка', u'13.9', u'L93.0'),
    ( u'локализованная склеродермия', u'13.10', u'L94.0'),
    ( u'болезни костно-мышечной системы и соединительной ткани', u'14.0', u'M00-M99'),
    ( u'из них: артропатии', u'14.1', u'M00-M25'),
    ( u'из них: реактивные артропатии', u'14.1.1', u'M02'),
    ( u'серопозитивный и серонегативный артриты', u'14.1.2', u'M05, M06'),
    ( u'юнешеский (ювенильный) артрит', u'14.1.3', u'M08'),
    ( u'артрозы', u'14.1.4', u'M15-M19'),
    ( u'системные поражения соединительной ткани', u'14.2', u'M30-M35'),
    ( u'из них: системная красная волчанка', u'14.2.1', u'M32'),
    ( u'деформирующие дорсопатии', u'14.3', u'M40-M43'),
    ( u'спондилопатии', u'14.4', u'M45-M49'),
    ( u'из них: анкилозирующий спондилит', u'14.4.1', u'M45'),
    ( u'поражения синовиальных оболочек и сухожилий', u'14.5', u'M65-M67'),
    ( u'остеопатии и хондропатии', u'14.6', u'M80-M94'),
    ( u'из них остеопорозы', u'14.6.1', u'M80 - M81'),
    ( u'болезни мочеполовой системы', u'15.0', u'N00-N99'),
    ( u'из них: гломерулярные, тубулоинтерстициальные болезни почек, другие болезни почки и мочеточника', u'15.1', u'N00-N15, N25-N28'),
    ( u'почечная недостаточность', u'15.2', u'N17-N19'),
    ( u'мочекаменная болезнь', u'15.3', u'N20-N21, N23'),
    ( u'другие болезни мочевой системы', u'15.4', u'N30-N32, N34-N36, N39'),
    ( u'болезни предстательной железы', u'15.5', u'N40-N42'),
    ( u'мужское бесплодие', u'15.6', u'N46'),
    ( u'доброкачественная дисплазия молочной железы', u'15.7', u'N60'),
    ( u'воспалительные болезни женских тазовых органов', u'15.8', u'N70-N73, N75-N76'),
    ( u'из них сальпингит и оофорит', u'15.8.1', u'N70'),
    ( u'эндометриоз', u'15.9', u'N80'),
    ( u'эрозия и эктропион шейки матки', u'15.10', u'N86'),
    ( u'расстройства менструаций', u'15.11', u'N91 - N94'),
    ( u'женское бесплодие', u'15.12', u'N97'),
    ( u'беременность, роды и послеродовой период', u'16.0', u'O00-O99'),
    ( u'отдельные состояния, возникающие в перинатальном периоде', u'17.0', u'P00-P04'),
    ( u'врожденные аномалии (пороки развития), деформации и хромосомные нарушения', u'18.0', u'Q00-Q99'),
    ( u'из них: врожденные аномалии нервной системы', u'18.1', u'Q00-Q07'),
    ( u'врожденные аномалии глаза', u'18.2', u'Q10-Q15'),
    ( u'врожденные аномалии системы кровообращения', u'18.3', u'Q20-Q28'),
    ( u'врожденные аномалии тела и шейки матки, другие врожденные аномалии женских половых органов', u'18.4', u'Q51-Q52'),
    ( u'неопределенность пола и псевдогермафродитизм', u'18.5', u'Q56'),
    ( u'врожденные деформации бедра ', u'18.6', u'Q65'),
    ( u'врожденный ихтиоз', u'18.7', u'Q80'),
    ( u'нейрофиброматоз', u'18.8', u'Q85.0'),
    ( u'синдром Дауна', u'18.9', u'Q90'),
    ( u'симптомы, признаки и отклонения от нормы, выявленные при клинических и лабораторных исследованиях, не классифицированные в других рубриках', u'19.0', u'R00-R99'),
    ( u'травмы, отравления и некоторые другие последствия воздействия внешних причин', u'20.0', u'S00-T98'),
]

CompRows = [
    (u'Всего', u'1.0', u'Z00-Z99'),
    (u'из них: обращения в учреждения здравоохранения для медицинского осмотра и обследования', u'1.1', u'Z00-Z13'),
    (u'из них: обращения в связи с получением медицинских документов', u'1.1.1', u'Z02.7'),
    (u'потенциальная опасность для здоровья, связанная с инфекционными болезнями', u'1.2', u'Z20-Z29'),
    (u'из них: носительство возбудителя инфекционной болезни', u'1.2.1', u'Z22'),
    (u'обращения в учреждения здравоохранения в связи с обстоятельствами, относящимися к репродуктивной функции', u'1.3', u'Z30-Z39'),
    (u'обращения в учреждения здравоохранения в связи с необходимостью проведения специфических процедур и получения медицинской помощи', u'1.4', u'Z40-Z54'),
    (u'из них: помощь, включающая использование реабилитационных процедур', u'1.4.1', u'Z50'),
    (u'паллиативная помощь', u'1.4.2', u'Z51.5'),
    (u'потенциальная опасность для здоровья, связанная с социально-экономическими и психосоциальными обстоятельствами', u'1.5', u'Z55-Z65'),
    (u'обращения в учреждения здравоохранения в связи с другими обстоятельствами', u'1.6', u'Z70-Z76'),
    (u'потенциальная опасность для здоровья, связанная с личным или семейным анамнезом и определенными обстоятельствами, влияющими на здоровье', u'1.7', u'Z80-Z99'),
    (u'из них: наличие илеостомы, колостомы', u'1.7.1', u'Z93.2, Z93.3')
]


def selectData(registeredInPeriod, begDate, endDate, eventPurposeId, eventTypeId, orgStructureId, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, areaIdEnabled, areaId, locality, eventTypeDDId, params):
    stmt="""
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
   ORDER BY Event.id
   LIMIT 1) AS closedEvent,
   (%s) AS firstInPeriod,
   %s
   (SELECT IF(rbDispanser.code = 2 OR rbDispanser.code = 6, 1, 0)
    FROM
    Diagnostic AS D1
    LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
    WHERE
      D1.diagnosis_id = Diagnosis.id
      AND (rbDispanser.code = 2 OR rbDispanser.code = 6)
    ORDER BY rbDispanser.code
    LIMIT 1) AS getObserved,
   IF((SELECT MAX(rbDispanser.observed)
FROM
Diagnostic AS D1
LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
WHERE
  D1.diagnosis_id = Diagnosis.id
  AND D1.endDate = (
    SELECT MAX(D2.endDate)
    FROM Diagnostic AS D2
    WHERE D2.diagnosis_id = Diagnosis.id
      AND D2.dispanser_id IS NOT NULL
      AND  D2.endDate<%s))
      = 1, 1, 0) AS observed

FROM Diagnosis
INNER JOIN Client ON Client.id = Diagnosis.client_id
%s
LEFT JOIN rbDiagnosisType    ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnosis.character_id
WHERE %s
GROUP BY MKB, diseaseCharacter, firstInPeriod, observed, rbDiagnosisType.id
    """
    db = QtGui.qApp.db
    tableDiagnosis  = db.table('Diagnosis')
    tableDiseaseCharacter = db.table('rbDiseaseCharacter')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tablePerson = db.table('Person')
    tableEvent = db.table('Event')
    tableOrgStructureAddress = db.table('OrgStructure_Address')
    tableAddress = db.table('Address')

    cond = []
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableDiagnosis['mod_id'].isNull())
    cond.append(db.joinOr([tableDiagnosis['setDate'].isNull(), tableDiagnosis['setDate'].lt(endDate.addDays(1))]))
    cond.append(db.joinOr([tableDiagnosis['endDate'].ge(begDate), tableDiseaseCharacter['code'].eq('3')]))

    diagnosticQuery = tableDiagnostic
    diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                       tableDiagnostic['deleted'].eq(0)
                     ]

    if registeredInPeriod:
        addDateInRange(diagnosticCond, tableDiagnostic['setDate'], begDate, endDate)
    isPersonPost = params.get('isPersonPost', 0)
    if isPersonPost:
        tableRBPost = db.table('rbPost')
        diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticQuery = diagnosticQuery.leftJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
        diagnosticCond.append(tablePerson['deleted'].eq(0))
        if isPersonPost == 1:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('1','2','3') ''')
        elif isPersonPost == 2:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('4','5','6','7','8','9')''')
    if personId:
        diagnosticCond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureId:
        if not isPersonPost:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        if not isPersonPost:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if eventTypeId:
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticCond.append(tableEvent['eventType_id'].eq(eventTypeId))
    elif eventPurposeId:
        tableEventType = db.table('EventType')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticQuery = diagnosticQuery.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        diagnosticCond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    cond.append(db.existsStmt(diagnosticQuery, diagnosticCond))
    if eventTypeDDId:
        colsEventTypeDDId = u'''(SELECT E.id
        FROM Diagnostic
        INNER JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id=rbDiagnosisType.id
        INNER JOIN Event AS E ON Diagnostic.event_id=E.id
        WHERE Diagnosis.deleted = 0 AND Diagnostic.deleted = 0 AND Diagnostic.diagnosis_id=Diagnosis.id
        AND E.eventType_id  = %d
        AND (rbDiagnosisType.code = '1'
        OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = E.execPerson_id
        AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
        INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
        AND DC.diagnosis_id=Diagnosis.id
        LIMIT 1))))) AS eventId,  '''%(eventTypeDDId)
    else:
        colsEventTypeDDId = u''''''
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        cond.append('Diagnosis.endDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
        cond.append('Diagnosis.endDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
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
    if areaIdEnabled:
        stmtAddress = u'''INNER JOIN ClientAddress ON ClientAddress.client_id = Diagnosis.client_id
                        AND ClientAddress.id = (SELECT MAX(id) FROM ClientAddress AS CA WHERE CA.Type=1 and CA.client_id = Diagnosis.client_id)
INNER JOIN Address ON Address.id = ClientAddress.address_id'''
        if areaId:
            orgStructureIdList = getOrgStructureDescendants(areaId)
        else:
            orgStructureIdList = getOrgStructures(QtGui.qApp.currentOrgId())
        subCond = [ tableOrgStructureAddress['master_id'].inlist(orgStructureIdList),
                    tableOrgStructureAddress['house_id'].eq(tableAddress['house_id']),
                  ]
        cond.append(db.existsStmt(tableOrgStructureAddress, subCond))
    else:
        stmtAddress = u''''''
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
            addAttachCond(cond, 'LPU_id=%d'%attachOrgId, *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachToNonBase' in params:
        addAttachCond(cond, 'LPU_id!=%d'%QtGui.qApp.currentOrgId(), *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachType' in params:
        addAttachCond(cond, '', *params['attachType'])
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
                cond.append(tableClient['deathDate'].ge(begDeathDate))
        if 'endDeathDate' in params:
            endDeathDate = params['endDeathDate']
            if endDeathDate:
                cond.append(tableClient['deathDate'].lt(endDeathDate.addDays(1)))
    return db.query(stmt % (db.joinAnd([tableDiagnosis['setDate'].le(endDate),
                                        tableDiagnosis['setDate'].ge(begDate)]),
                            colsEventTypeDDId,
                            tableDiagnosis['setDate'].formatValue(endDate.addDays(1)),
                            stmtAddress,
                            db.joinAnd(cond)))


def selectDataClient(registeredInPeriod, begDate, endDate, eventPurposeId, eventTypeId, orgStructureId, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, areaIdEnabled, areaId, locality, params, boolThyroidosData = False):
    if boolThyroidosData:
        stmt="""
SELECT
   Diagnosis.MKB AS MKB,
   Diagnosis.client_id,
  Client.deathDate AS begDateDeath

FROM Diagnosis
INNER JOIN Client ON Client.id = Diagnosis.client_id
%s
INNER JOIN rbDiagnosisType    ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
INNER JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnosis.character_id
WHERE %s AND (Diagnosis.MKB >= 'E00' AND Diagnosis.MKB <= 'E07') AND EXISTS(SELECT MAX(rbDispanser.observed)
FROM
Diagnostic AS D1
LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
WHERE
  D1.diagnosis_id = Diagnosis.id
  AND D1.endDate = (
    SELECT MAX(D2.endDate)
    FROM Diagnostic AS D2
    WHERE D2.diagnosis_id = Diagnosis.id
      AND D2.dispanser_id IS NOT NULL
      AND  D2.endDate < %s))
    """
    else:
        stmt="""
SELECT
   Diagnosis.MKB AS MKB,
   Diagnosis.client_id,
   rbDiseaseCharacter.code AS diseaseCharacter,
   (%s) AS firstInPeriod,
   IF((SELECT MAX(rbDispanser.observed)
FROM
Diagnostic AS D1
LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
WHERE
  D1.diagnosis_id = Diagnosis.id
  AND D1.endDate = (
    SELECT MAX(D2.endDate)
    FROM Diagnostic AS D2
    WHERE D2.diagnosis_id = Diagnosis.id
      AND D2.dispanser_id IS NOT NULL
      AND  D2.endDate<%s))
      = 1, 1, 0) AS observed

FROM Diagnosis
INNER JOIN Client ON Client.id = Diagnosis.client_id
%s
INNER JOIN rbDiagnosisType    ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
INNER JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnosis.character_id
WHERE %s
GROUP BY Diagnosis.client_id
ORDER BY firstInPeriod DESC, observed DESC
    """ # GROUP BY Diagnosis.client_id
    db = QtGui.qApp.db
    tableDiagnosis  = db.table('Diagnosis')
    tableDiseaseCharacter = db.table('rbDiseaseCharacter')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tablePerson = db.table('Person')
    tableOrgStructureAddress = db.table('OrgStructure_Address')
    tableAddress = db.table('Address')

    cond = []
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableDiagnosis['mod_id'].isNull())
    cond.append(db.joinOr([tableDiagnosis['setDate'].isNull(), tableDiagnosis['setDate'].lt(endDate.addDays(1))]))
    cond.append(db.joinOr([tableDiagnosis['endDate'].ge(begDate), tableDiseaseCharacter['code'].eq('3')]))

    diagnosticQuery = tableDiagnostic
    diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                       tableDiagnostic['deleted'].eq(0)
                     ]
    if registeredInPeriod:
        addDateInRange(diagnosticCond, tableDiagnostic['setDate'], begDate, endDate)
    if personId:
        diagnosticCond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureId:
        diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if eventTypeId:
        tableEvent = db.table('Event')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticCond.append(tableEvent['eventType_id'].eq(eventTypeId))
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
        cond.append('Diagnosis.endDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
        cond.append('Diagnosis.endDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
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
    if areaIdEnabled:
        stmtAddress = u'''INNER JOIN ClientAddress ON ClientAddress.client_id = Diagnosis.client_id
                        AND ClientAddress.id = (SELECT MAX(id) FROM ClientAddress AS CA WHERE CA.Type=1 and CA.client_id = Diagnosis.client_id)
INNER JOIN Address ON Address.id = ClientAddress.address_id'''
        if areaId:
            orgStructureIdList = getOrgStructureDescendants(areaId)
        else:
            orgStructureIdList = getOrgStructures(QtGui.qApp.currentOrgId())
        subCond = [ tableOrgStructureAddress['master_id'].inlist(orgStructureIdList),
                    tableOrgStructureAddress['house_id'].eq(tableAddress['house_id']),
                  ]
        cond.append(db.existsStmt(tableOrgStructureAddress, subCond))
    else:
        stmtAddress = u''''''
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
            addAttachCond(cond, 'LPU_id=%d'%attachOrgId, *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachToNonBase' in params:
        addAttachCond(cond, 'LPU_id!=%d'%QtGui.qApp.currentOrgId(), *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachType' in params:
        addAttachCond(cond, '', *params['attachType'])
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
                cond.append(tableClient['deathDate'].ge(begDeathDate))
        if 'endDeathDate' in params:
            endDeathDate = params['endDeathDate']
            if endDeathDate:
                cond.append(tableClient['deathDate'].lt(endDeathDate.addDays(1)))
    if boolThyroidosData:
        return db.query(stmt % (stmtAddress, db.joinAnd(cond), tableDiagnosis['setDate'].formatValue(endDate.addDays(1))))
    else:
        return db.query(stmt % (db.joinAnd([tableDiagnosis['setDate'].le(endDate),
                                        tableDiagnosis['setDate'].ge(begDate)]),
                            tableDiagnosis['setDate'].formatValue(endDate.addDays(1)),
                            stmtAddress,
                            db.joinAnd(cond)))


class CStatReportF12Adults(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        title = u'Ф.12 (взрослые)'
        self.setTitle(title, u'Ф.12 (взрослые)')


    def getDefaultParams(self):
        result = CReport.getDefaultParams(self)
        result['ageFrom']     = 18
        result['ageTo']       = 150
        return result


    def getSetupDialog(self, parent):
        result = CReportAcuteInfectionsSetupDialog(parent)
        result.setAreaEnabled(True)
        result.setAllAddressSelectable(True)
        result.setEventTypeDDEnabled(True)
        result.setAllAttachSelectable(True)
        result.setTitle(self.title())
        return result


    def build(self, params):
        mapMainRows = createMapCodeToRowIdx( [row[2] for row in MainRows] )
        mapCompRows = createMapCodeToRowIdx( [row[2] for row in CompRows] )

        registeredInPeriod = params.get('registeredInPeriod', False)
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        eventPurposeId = params.get('eventPurposeId', None)
        eventTypeId = params.get('eventTypeId', None)
        eventTypeDDId = params.get('eventTypeDDId', None)
        orgStructureId = params.get('orgStructureId', None)
        personId = params.get('personId', None)
        sex = params.get('sex', 0)
        ageFrom = params.get('ageFrom', 18)
        ageTo = params.get('ageTo', 150)
        socStatusClassId = params.get('socStatusClassId', None)
        socStatusTypeId = params.get('socStatusTypeId', None)
        areaIdEnabled = params.get('areaIdEnabled', None)
        areaId = params.get('areaId', None)
        locality = params.get('locality', 0)
        reportLine = None
        chkFilterAttachType = params.get('chkFilterAttachType', False)
        dead = params.get('dead', False)
        chkFilterAttach = params.get('chkFilterAttach', False)
        attachToNonBase = params.get('attachToNonBase', False)
        excludeLeaved = params.get('excludeLeaved', False)
        rowSize = 7
        getObservedSum = 0
        eventTypeDDSum = 0
        eventIdList = []
        reportMainData = [ [0]*rowSize for row in xrange(len(MainRows)) ]
        reportCompData = [ [0]*rowSize for row in xrange(len(CompRows)) ]
        query = selectData(registeredInPeriod, begDate, endDate, eventPurposeId, eventTypeId, orgStructureId, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, areaIdEnabled, areaId, locality, eventTypeDDId, params)
        while query.next():
            record    = query.record()
            clientId = forceRef(record.value('client_id'))
            MKB       = normalizeMKB(forceString(record.value('MKB')))
            sickCount = forceInt(record.value('sickCount'))
            diseaseCharacter = forceString(record.value('diseaseCharacter'))
            diagnosisType = forceString(record.value('diagnosisType'))
            firstInPeriod = forceBool(record.value('firstInPeriod'))
            closedEvent = forceBool(record.value('closedEvent'))
            observed = forceBool(record.value('observed'))
            getObserved = forceInt(record.value('getObserved'))
            getObservedSum += getObserved
            eventId = forceRef(record.value('eventId'))
            if (eventId not in eventIdList) and (diseaseCharacter == 1 or diseaseCharacter == 2):
                eventTypeDDSum += 1
                eventIdList.append(eventId)
            cols = [0]
            if diseaseCharacter == '1': # острое
                cols.append(1)
                if getObserved:
                    cols.append(2)
                cols.append(3)
            else:
                if firstInPeriod:
                    cols.append(1)
                    if getObserved:
                        cols.append(2)
                    cols.append(4)
                else:
                    cols.append(5)
            if observed:
                cols.append(6)

            for row in mapMainRows.get(MKB, []):
                reportLine = reportMainData[row]
                for col in cols:
                    reportLine[col] += sickCount

            if diagnosisType == '98':
                for row in mapCompRows.get(MKB, []):
                    reportLine = reportCompData[row]
                    reportLine[0] += sickCount
                    if diseaseCharacter != '1' and not firstInPeriod:
                        reportLine[1] += sickCount
                    if closedEvent:
                        reportLine[2] += sickCount
        registeredAll = 0
        registeredFirst = 0
        consistsByEnd = 0
        thyroidosUnhangAll = 0
        thyroidosUnhangRecovery = 0
        thyroidosUnhangDeath = 0
        clientIdList = []
        clientIdForThyroidosList = []
        queryClient = selectDataClient(registeredInPeriod, begDate, endDate, eventPurposeId, eventTypeId, orgStructureId, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, areaIdEnabled, areaId, locality, params)
        while queryClient.next():
            record    = queryClient.record()
            clientId = forceRef(record.value('client_id'))
            diseaseCharacter = forceString(record.value('diseaseCharacter'))
            firstInPeriod = forceBool(record.value('firstInPeriod'))
            observed = forceBool(record.value('observed'))

            if clientId and clientId not in clientIdList:
                clientIdList.append(clientId)
                registeredAll += 1
                if observed:
                    consistsByEnd += 1
                if firstInPeriod:
                   registeredFirst += 1
        queryThyroidos = selectDataClient(registeredInPeriod, begDate, endDate, eventPurposeId, eventTypeId, orgStructureId, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, areaIdEnabled, areaId, locality, params, True)
        while queryThyroidos.next():
            record    = queryThyroidos.record()
            clientId = forceRef(record.value('client_id'))
            if clientId and clientId not in clientIdForThyroidosList:
                clientIdForThyroidosList.append(clientId)
                thyroidosUnhangAll += 1
                deathDate = forceDate(record.value('begDateDeath'))
                if deathDate and (begDate <= deathDate and deathDate <= endDate):
                    thyroidosUnhangDeath += 1
        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        if chkFilterAttachType or dead or chkFilterAttach or attachToNonBase or excludeLeaved:
           self.dumpParamsAttach(cursor, params)
        if params.get('isFilterAddress', False):
            self.dumpParamsAdress(cursor, params)
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.insertText(u'(3000)')
        cursor.insertBlock()

        tableColumns = [
            ('30%', [u'Наименование классов и отдельных болезней', u'', u'', u'1'], CReportBase.AlignLeft),
            ('6%',  [u'№ строки',                 u'', u'', u'2'], CReportBase.AlignLeft),
            ('8%',  [u'Код по МКБ-10 пересмотра', u'', u'', u'3'], CReportBase.AlignLeft),
            ('8%',  [u'Зарегистрировано пациентов с данным заболеванием', u'Всего', u'', u'4'], CReportBase.AlignRight),
            ('8%',  [u'', u'В т.ч. впервые',      u'всего', u'5'], CReportBase.AlignRight),
            ('8%',  [u'', u'', u'из них (из гр.5): взято под диспансерное наблюдение', u'6'], CReportBase.AlignRight),
            ('8%',  [u'', u'',                    u'острые', u'7'], CReportBase.AlignRight),
            ('8%',  [u'', u'',                    u'хрон.', u'9'], CReportBase.AlignRight),
            ('8%',  [u'', u'В т.ч. хрон.',        u'', u'10'], CReportBase.AlignRight),
            ('8%',  [u'Состоит на д.н. на конец периода', u'', u'', u'11'], CReportBase.AlignRight),
            ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1) # Наименование
        table.mergeCells(0, 1, 3, 1) # № стр.
        table.mergeCells(0, 2, 3, 1) # Код МКБ
        table.mergeCells(0, 3, 1, 6) # Всего
        table.mergeCells(1, 3, 2, 1) # Всего
        table.mergeCells(1, 4, 1, 4) # Впервые
        table.mergeCells(1, 8, 2, 1) # Хрон.
        table.mergeCells(0, 9, 3, 1) # Д.Н.

        for row, rowDescr in enumerate(MainRows):
            reportLine = reportMainData[row]
            i = table.addRow()
            table.setText(i, 0, rowDescr[0])
            table.setText(i, 1, rowDescr[1])
            table.setText(i, 2, rowDescr[2] + (u' (часть)' if row == 59 else ''))
            for col in xrange(rowSize):
                table.setText(i, 3+col, reportLine[col])
        thyroidosUnhangRecovery = thyroidosUnhangAll - thyroidosUnhangDeath
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'''(3001) Заболевания, выявленные впервые в жизни во время дополнительной диспансеризации (работающего населения ), дополнительных медосмотров %d ; из них взято под диспансерное наблюдение %d . '''%(eventTypeDDSum, getObservedSum))
        cursor.insertBlock()
        cursor.insertText(u'''(3002) Число физических лиц зарегистрированных пациентов – всего %d , из них с диагнозом , установленным впервые в жизни %d , состоит под диспансерным наблюдением на конец отчетного года (из гр. 6, стр. 1) %d .'''%(registeredAll, registeredFirst, consistsByEnd))
        cursor.insertBlock()
        cursor.insertText(u'''(3003) Из числа состоящих под диспансерным наблюдением пациентов с заболеваниями щитовидной железы (из стр. 5.1) снято с диспансерного наблюдения: всего %d, из них в связи с выздоровлением %d, со смертью %d. '''%(thyroidosUnhangAll, thyroidosUnhangRecovery, thyroidosUnhangDeath))
        cursor.insertBlock()

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'ФАКТОРЫ, ВЛИЯЮЩИЕ НА СОСТОЯНИЕ ЗДОРОВЬЯ НАСЕЛЕНИЯ')
        cursor.insertBlock()
        cursor.insertText(u'И ОБРАЩЕНИЯ В УЧРЕЖДЕНИЯ ЗДРАВООХРАНЕНИЯ')
        cursor.insertBlock()
        cursor.insertText(u'(3100)')
        cursor.insertBlock()
        cursor.insertBlock()

        tableColumns = [
            ('30%', [u'Наименование', u'', u'1'], CReportBase.AlignLeft),
            ('10%', [u'№ строки', u'', u'2'], CReportBase.AlignLeft),
            ('15%', [u'Шифр по МКБ-Х пересмотра', u'', u'3'], CReportBase.AlignLeft),
            ('15%', [u'Обращений', u'всего', u'4'], CReportBase.AlignRight),
            ('15%', [u'', u'из них: повторные', u'5'], CReportBase.AlignRight),
            ('15%', [u'', u'законченные случаи', u'6'], CReportBase.AlignRight),
            ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 3)

        for row, rowDescr in enumerate(CompRows):
            reportLine = reportCompData[row]
            i = table.addRow()
            table.setText(i, 0, rowDescr[0])
            table.setText(i, 1, rowDescr[1])
            table.setText(i, 2, rowDescr[2])
            table.setText(i, 3, reportLine[0])
            table.setText(i, 4, reportLine[1])
            table.setText(i, 5, reportLine[2])

        return doc
