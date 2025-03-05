# -*- coding: utf-8 -*-

from PyQt4               import QtGui
from library.JsonRpc.client   import CJsonRpcClent
from library.Utils       import *

def callService(method, request, url=None, timeout=600):
    if url:
        url = url.replace('${dbServerName}', QtGui.qApp.preferences.dbServerName)
        clent = CJsonRpcClent(url)
    else:
        clent = CJsonRpcClent("http://%s/ident/handler.php" % QtGui.qApp.preferences.dbServerName)
    result = clent.call(method, request, timeout=timeout)
    if result['ok']:
        return result
    elif 'message' in result:
        raise Exception(result['message'])
    else:
        raise Exception(u'Неопознанная ошибка')

def searchClientAttach(personInfo, timeout=10):
    url = forceString(QtGui.qApp.preferences.appPrefs.get('TFCPUrl', ''))
    return callService('searchClientAttach', personInfo, url=url, timeout=timeout)

def sendQueryForDeAttachForMO(deattachMO):
    url = forceString(QtGui.qApp.preferences.appPrefs.get('TFCPUrl', ''))
    return callService('sendQueryForDeAttachForMO', {'deattachlist': [deattachMO]}, url=url)

def clientAttach(client_id, personInfo, attachInfo):
    url = forceString(QtGui.qApp.preferences.appPrefs.get('TFCPUrl', ''))
    return callService('clientAttach', {'attachlist': [{'client_id': client_id, 'person': personInfo, 'info': attachInfo}]}, url=url)

def clientDeAttach(personInfo, deAttachInfo):
    url = forceString(QtGui.qApp.preferences.appPrefs.get('TFCPUrl', ''))
    return callService('clientDeAttach', {'deattachlist': [{'person': personInfo, 'info': deAttachInfo}]}, url=url)

def sendAttachDoctorSectionInformation(moCode, doctorsInfo, url=None):
    return callService('sendAttachDoctorSectionInformation', {'moCode': moCode, 'doctorsInfo': doctorsInfo}, url=url)
    
def callServiceReAttach(method, request, url=None, timeout=60):
    if url:
        clent = CJsonRpcClent(url)
    else:
        clent = CJsonRpcClent("http://%s/ident/handler.php" % QtGui.qApp.preferences.dbServerName)
    result = clent.call(method, request, timeout=timeout)
    return result
    
def getCKDInformationByKpk(profileCode):
    return callService('getCKDInformationByKpk', {'profileCode': profileCode})

def updatePersonParus():
    return callService('updatePersonParus', {})

def putEvPlanList(exportKind, rowIdList, url = None):
    return callService('putEvPlanList', {'exportKind': exportKind, 'rowIdList': rowIdList}, url)

def getEvFactInfos(date, page, url = None):
    return callService('getEvFactInfos', {'date': date, 'page': page}, url)

def getEvFactInvcs(year, mnth, page, url = None):
    return callService('getEvFactInvcs', {'year': year, 'mnth': mnth, 'page': page}, url)

def getEvPlanQtys(year, url = None):
    return callService('getEvPlanQtys', {'year': year}, url)

def putEvContacts(codeMo, url = None):
    return callService('putEvContacts', {'code_mo': codeMo}, url)

def putEvPlanDates(codeMo, url = None):
    return callService('putEvPlanDates', {'code_mo': codeMo}, url)

def updateExportedPlan(year, month, url = None):
    return callService('updateExportedPlan', {'year': year, 'month': month}, url)

def deleteExportedPlan(expPlanIdList, url = None):
    return callService('deleteExportedPlan', {'expPlanIdList': expPlanIdList, 'userId': QtGui.qApp.userId}, url)

def svodCreateReport(formCode, date, orgStructureId, url = None):
    return callService('svodCreateReport', {'formCode': formCode, 'date': date, 'orgStructureId': orgStructureId}, url)

def svodSendReport(reportId, url = None):
    return callService('svodSendReport', {'reportId': reportId}, url)

def svodUpdateFormList(url = None):
    return callService('svodUpdateFormList', {}, url)