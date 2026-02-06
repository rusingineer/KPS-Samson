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


from library.AgeSelector   import parseAgeSelector
from library.Utils         import (
                                   forceBool,
                                   forceDate,
                                   forceDouble,
                                   forceInt,
                                   forceRef,
                                   forceString,
                                   forceStringEx,
                                  )


class CTariff(object):
    ttVisit               =  0 # visit
    ttEvent               =  1 # event
    ttActionAmount        =  2 # action, по количеству
    ttEventAsCoupleVisits =  3 # "визит-день", тарифицируется множество визитов
    ttHospitalBedDay      =  4 # "койко-день"
    ttActionUET           =  5 # action, по УЕТ
    ttHospitalBedService  =  6 # "койка-профиль"
    ttVisitByAction       =  7 # визит по мероприятию
    ttVisitsByMES         =  8 # Визиты по МЭС
    ttEventByMES          =  9 # Событие по МЭС
    ttEventByMESLen       = 10 # Событие по МЭС, с учётом длительности события
    ttCoupleVisits        = 11 # "визиты по профилю" тарифицируется множество визитов
    ttEventByMESLevel     = 12 # Событие по МЭС с учётом уровня выполнения и длительности
    ttKrasnodarA13        = 13 # Событие по МЭС с заморочками для Краснодара
    ttMurmansk2015Hospital= 14 # Событие по МЭС для стационара в Мурманске
    ttCSG                 = 15 # КСГ в событии

    tariffTypeNames = (u'посещение',
                       u'событие',
                       u'мероприятие по количеству',
                       u'визит-день',
                       u'событие по койко-дням',
                       u'мероприятие по УЕТ',
                       u'мероприятие по количеству и тарифу койки',
                       u'визиты по мероприятию',
                       u'визиты по МЭС',
                       u'событие по МЭС',
                       u'событие по МЭС с учётом длительности',
                       u'визиты по профилю',
                       u'событие по МЭС с учётом уровня выполнения и длительности',
                       u'Краснодар,П13: событие по КСГ с учётом длительности и операций',
                       u'Мурманск,2015: стационар',
                       u'КСГ'
                      )

    # в UI мы используем округление при показе в редакторе.
    # при этом используется код типа QString.number(0.125,'f',2)
    # я хочу схитрить и не использовать округления средствами Qt
    def __init__(self, record, precision=None):
        if precision is None:
            locRound = lambda num: num
#        if precision<0:
#            locRound = lambda num: round(num, precision)
        else:
            # на такое ухищрение пришлось пойти на из-за того, что
            # традиционный round(0.125,2) в python2 даёт 0.13, а хочется 0.12 и т.п.
#            locRound = lambda num: QString.number(num, 'f', precision).toDouble()[0]
            locRound = lambda num: float('%.*f' % (precision, num))

        self.id                 = forceInt(record.value('id'))
        self.eventTypeId        = forceRef(record.value('eventType_id'))
        self.cureMethodId       = forceRef(record.value('cureMethod_id'))
        self.resultId           = forceRef(record.value('result_id'))
        self.tariffType         = forceInt(record.value('tariffType'))
        self.serviceId          = forceRef(record.value('service_id'))
        self.tariffCategoryId   = forceRef(record.value('tariffCategory_id'))
        self.MKB                = forceStringEx(record.value('MKB'))
        self.parsedMKB          = self.parseMKB(self.MKB)
        #self.phaseId           = forceRef(record.value('phase_id'))
        self.amount             = forceDouble(record.value('amount'))
        self.uet                = forceDouble(record.value('uet'))
        self.price              = locRound(forceDouble(record.value('price')))
        self.vat                = forceDouble(record.value('VAT'))
        frags = [(0.0, 0.0, self.price)]
        if forceDouble(record.value('frag1Start')):
            frags.append(( forceDouble(record.value('frag1Start')),
                           forceDouble(record.value('frag1Sum')),
                           locRound(forceDouble(record.value('frag1Price'))),
                        ))
        if forceDouble(record.value('frag2Start')):
            frags.append(( forceDouble(record.value('frag2Start')),
                           forceDouble(record.value('frag2Sum')),
                           locRound(forceDouble(record.value('frag2Price'))),
                        ))
        frags.reverse()
        self.frags              = frags
        self.sex                = forceInt(record.value('sex'))
        self.age                = forceStringEx(record.value('age'))
        self.controlPeriod      = forceInt(record.value('controlPeriod'))
        self.begDate            = forceDate(record.value('begDate'))
        self.endDate            = forceDate(record.value('endDate'))
        self.endDate1           = self.endDate.addDays(1) if self.endDate else None
        self.unitId             = forceRef(record.value('unit_id'))
        self.batch              = forceString(record.value('batch'))
        self.mesStatus          = forceInt(record.value('mesStatus'))
        self.enableCoefficients = forceBool(record.value('enableCoefficients'))
        if self.age:
            self.ageSelector = parseAgeSelector(self.age)
        else:
            self.ageSelector = None


    @staticmethod
    def parseMKB(MKB):
        result = []
        MKB = MKB.replace(' ', '').replace('\t', '').upper()
        for range in MKB.split(','):
            if range:
                parts = range.split('-')
                result.append((parts[0], parts[-1]+'\x7F'))
        return result


    def dateInRange(self, date):
        return (not self.begDate or self.begDate<=forceDate(date)) and (not self.endDate1 or forceDate(date)<self.endDate1) #forceDate, потому что date может быть QDateTime и неправильно будет работать сравнение


    def matchMKB(self, MKB):
        if self.parsedMKB:
            for low, high in self.parsedMKB:
                if low<=MKB.upper()<high:
                    return True
            return False
        else:
            return True


#    def phaseIdEq(self, phaseId):
#        if self.phaseId == phaseId:
#            return True
#        else:
#            return False


    def evalAmountPriceSum(self, amount, coefficient=1.0):
        if self.amount:
            amount = min(amount, self.amount)
        sum = 0
        for fragStart, fragSum, fragPrice in self.frags:
            if amount>=fragStart:
                sum = fragSum + (amount-fragStart)*fragPrice
                break
        price = sum/amount if amount else self.price
        return amount, price, round(sum*coefficient, 2)


    def limitationIsExceeded(self, amount):
        for fragStart, fragSum, fragPrice in self.frags:
            if fragStart>0 and amount>=fragStart:
                return True
        return False
