# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QDateTime

from library.JsonRpc.client import CJsonRpcClent
from library.Utils import forceString, toVariant

class CUOServiceClient(object):
    def __init__(self):
        self.url = QtGui.qApp.getMqHelperUrl()
        self.client = CJsonRpcClent(self.url)
    
    def getAvailableAppointments(self, orgId, profileId):
        return self.client.call(
            'getAvailableAppointments',
            params={
                'targetOrgId': orgId,
                'medicalAidProfileId': profileId,
            }
        )

    def getInspectDoctorsReferral2(self, doctorsReferal):
        return self.client.call(
            'getInspectDoctorsReferral2',
            params={
                'doctorsReferal': doctorsReferal,
            }
        )

    def registerReferral(self, action):
        result = self.client.call(
            'registerReferral',
            params={
                'actionId': action.getId(),
            }
        )
        if not result.get('idMq', ''):
            raise Exception(u"Неизвестная ошибка (пустой номер направления)")
        return result['idMq']
    
    def cancelReferral(self, action, sourceCode, reasonCode, reasonComment):
        self.client.call(
            'cancelReferral',
            params={
                'actionId': action.getId(),
                'sourceCode': sourceCode,
                'reasonCode': reasonCode,
                'reasonComment': reasonComment
            }
        )
    
    def setAppointment(self, action, specialityId, doctorId, appointmentId):
        self.client.call(
            'setAppointment',
            params={
                'actionId': action.getId(),
                'specialityId': specialityId,
                'doctorId': doctorId,
                'appointmentId': appointmentId,
            }
        )

    def createClaimForRefusal(self, action):
        self.client.call(
            'createClaimForRefusal',
            params={
                'actionId': action.getId(),
            }
        )

    def updatemedserviceprofile(self, id):
        result = self.client.call(
            'updatemedserviceprofile',
            params={
                'medProfId': id,
            }
        )
        if not result.get('result', ''):
            return Exception(u"Неизвестная ошибка")
        return result['result']