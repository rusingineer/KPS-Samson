# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from library.JsonRpc.client   import CJsonRpcClent
from library.Utils import forceString


def callService(method, request, url=None, timeout=600, returnRawResult=False):
    if url:
        url = url.replace('${dbServerName}', QtGui.qApp.preferences.dbServerName)
    else:
        url = forceString(QtGui.qApp.preferences.appPrefs.get('TFCPUrl', ''))
        url = url.replace('${dbServerName}', QtGui.qApp.preferences.dbServerName)
        if not url:
            url = forceString(QtGui.qApp.db.translate('GlobalPreferences', 'code', 'PHP_ServicesUrl', 'value'))
            url = "http://%s/ident/handler.php" % (url if url else QtGui.qApp.preferences.dbServerName)
    client = CJsonRpcClent(url)
    result = client.call(method, request, timeout=timeout)
    if returnRawResult:
        return result
    if result['ok']:
        return result
    elif 'message' in result:
        raise Exception(result['message'])
    else:
        raise Exception(u'Неопознанная ошибка')

def searchClientAttach(personInfo, timeout=10):
    return callService('searchClientAttach', personInfo, timeout=timeout)

def sendQueryForDeAttachForMO(deattachMO):
    return callService('sendQueryForDeAttachForMO', {'deattachlist': [deattachMO]})

def clientAttach(client_id, personInfo, attachInfo):
    return callService('clientAttach', {'attachlist': [{'client_id': client_id, 'person': personInfo, 'info': attachInfo}]})

def clientDeAttach(personInfo, deAttachInfo):
    return callService('clientDeAttach', {'deattachlist': [{'person': personInfo, 'info': deAttachInfo}]})

def sendAttachDoctorSectionInformation(moCode, doctorsInfo, url=None):
    return callService('sendAttachDoctorSectionInformation', {'moCode': moCode, 'doctorsInfo': doctorsInfo}, url=url)
    
def callServiceReAttach(method, request, url=None, timeout=60, returnRawResult=False):
    return callService(method, request, url=url, timeout=timeout, returnRawResult=returnRawResult)
    
def getCKDInformationByKpk(profileCode):
    return callService('getCKDInformationByKpk', {'profileCode': profileCode})

def updatePersonParus():
    return callService('updatePersonParus', {})

def putEvPlanList(exportKind, rowIdList, useSocAttachments=0, url=None):
    return callService('putEvPlanList',
                   {'exportKind': exportKind, 'rowIdList': rowIdList, 'useSocAttachments': useSocAttachments},
                   url)

def getEvFactInfos(date, page, url=None):
    return callService('getEvFactInfos', {'date': date, 'page': page}, url)

def getEvFactInvcs(year, mnth, page, url=None):
    return callService('getEvFactInvcs', {'year': year, 'mnth': mnth, 'page': page}, url)

def getEvPlanQtys(year, url=None):
    return callService('getEvPlanQtys', {'year': year}, url)

def putEvContacts(codeMo, url=None):
    return callService('putEvContacts', {'code_mo': codeMo}, url)

def putEvPlanDates(codeMo, url=None):
    return callService('putEvPlanDates', {'code_mo': codeMo}, url)

def updateExportedPlan(year, month, url=None):
    return callService('updateExportedPlan', {'year': year, 'month': month}, url)

def deleteExportedPlan(expPlanIdList, url=None):
    return callService('deleteExportedPlan', {'expPlanIdList': expPlanIdList, 'userId': QtGui.qApp.userId}, url)

def svodCreateReport(formCode, date, orgStructureId, url=None):
    return callService('svodCreateReport', {'formCode': formCode, 'date': date, 'orgStructureId': orgStructureId}, url)

def svodSendReport(reportId, url=None):
    return callService('svodSendReport', {'reportId': reportId}, url)

def svodUpdateFormList(url=None):
    return callService('svodUpdateFormList', {}, url)
