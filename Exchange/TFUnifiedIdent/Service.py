# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2015 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

# поддержка получения полиса пациента по унифицированному протоколу

from PyQt4                  import QtCore, QtGui
from library.JsonRpc.client import CJsonRpcClent
from library.Utils          import formatSex, formatSNILS, smartDict

__all__ = ['CTFUnifiedIdentService',
          ]


class CTFUnifiedIdentService:

    def __init__(self, url, login=None, password=None):
        self.url = url
        self.login = login
        self.password = password


    def getPolicyAndAttach(self,
                           firstName,
                           lastName,
                           patrName,
                           sex,
                           birthDate,
                           snils,
                           policyType,
                           policySerial,
                           policyNumber,
                           docTypeId,
                           docSerial,
                           docNumber
                          ):

        def strToQDate(s):
            try:
                result = QtCore.QDate.fromString(s, QtCore.Qt.ISODate)
                if not result.isValid():
                    result = None
                return result
            except:
                return None


        dbServerName = QtGui.qApp.preferences.dbServerName
        url = self.url.replace('${dbServerName}', dbServerName)
        client = CJsonRpcClent(url, self.login, self.password)
        resp = client.call('searchClientPolicy',
                           dict(lastName     = lastName,
                                firstName    = firstName,
                                patrName     = patrName,
                                sex          = formatSex(sex),
                                birthDate    = unicode(birthDate.toString(QtCore.Qt.ISODate)) if birthDate else None,
                                snils        = formatSNILS(snils),
                                policyType = policyType, 
                                policySerial = policySerial,
                                policyNumber = policyNumber,
                                docTypeId = docTypeId,
                                docSerial    = docSerial,
                                docNumber    = docNumber,
                                personId     = QtGui.qApp.userId,
                                workstation  = QtGui.qApp.hostName,
                               ), 10
                          )
        if resp and 'policy' in resp:
            policy = resp.get('policy')
            result = smartDict()
            result.hicId = policy.get('hicId', None)
            result.hicName = policy.get('hicName', '?')
            result.typeCode = policy.get('type', None)
            result.kindCode = policy.get('kind', None)
            result.policySerial = policy.get('serial', '')
            result.policyNumber = policy.get('number', '')
            result.begDate      = QtCore.QDate.fromString(policy.get('begDate', ''), QtCore.Qt.ISODate)
            result.endDate      = QtCore.QDate.fromString(policy.get('endDate', ''), QtCore.Qt.ISODate) if policy.get('endDate', None) else None
            result.person = policy.get('person', u'<Неизвестен>')
            result.birthDate = QtCore.QDate.fromString(policy.get('birthDate', ''), QtCore.Qt.ISODate)
            result.lastName = policy.get('lastName', '')
            result.firstName = policy.get('firstName', '')
            result.patrName = policy.get('patrName', '')
            result.snils = resp.get('snils', '')
            result.cv19Severity = resp.get('cv19Severity', '')
            result.SOC = resp.get('SOC', None)
            if any(resp.get('dd', None)):
                result.dd = resp['dd']
            
            try:
                result.sex = [u'', u'м', u'ж'].index(policy.get('sex', '').lower())
            except:
                result.sex = 0

            return result
        else:
            return None
