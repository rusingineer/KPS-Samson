import requests
import urlparse
import urllib
from PyQt4 import QtGui
from PyQt4.QtCore import QXmlStreamReader, QUrl

from library.Utils import forceString


class CPyServices:
    def __init__(self, url):
        url = url.replace('\\\\', '//')
        self.url = url
    
    def get(self, methodName, params={}):
        try:
            response = requests.get(urlparse.urljoin(self.api, methodName), params=params)
            return self.jsonResponse(response)
        except requests.exceptions.RequestException as e:
            QtGui.qApp.logCurrentException()
            raise e

    def post(self, methodName, params={}):
        try:
            response = requests.post(urlparse.urljoin(self.api, methodName), params=params)
            return self.jsonResponse(response)
        except requests.exceptions.RequestException as e:
            QtGui.qApp.logCurrentException()
            raise e

    def postFiles(self, methodName, files):
        try:
            response = requests.post(urlparse.urljoin(self.api, methodName), files=files)
            return self.jsonResponse(response)
        except requests.exceptions.RequestException as e:
            QtGui.qApp.logCurrentException()
            raise e

    def postJson(self, methodName, json):
        try:
            response = requests.post(urlparse.urljoin(self.api, methodName), json=json)
            return self.jsonResponse(response)
        except requests.exceptions.RequestException as e:
            QtGui.qApp.logCurrentException()
            raise e
    
    def jsonResponse(self, response):
        try:
            json = response.json()
        except ValueError:
            json = None
        if response.status_code != 200:
            if not json:
                raise Exception(response.text)
            if 'detail' in json:
                raise Exception(json['detail'])
            else:
                raise Exception(json)
        return json


class CSchematronService(CPyServices):
    def __init__(self, url):
        CPyServices.__init__(self, url)
        self.api = urlparse.urljoin(url, '/api/schematron/')

    def listCdaCodes(self):
        return self.get('list_cda_codes')

    def validateCda(self, xmlText):
        files = {'file': xmlText}
        return self.postFiles('validate_cda', files=files)

    def getCdaCode(self, xmlText):
        reader = QXmlStreamReader(xmlText)
        reader.setNamespaceProcessing(False)
        while not reader.atEnd():
            reader.readNext()
            if reader.isStartElement() and reader.name() == "code":
                attributes = reader.attributes()
                if attributes.value("codeSystem") == "1.2.643.5.1.13.13.11.1522":
                    return str(attributes.value("code"))
        return None


class CDistantMonitoringService(CPyServices):
    def __init__(self, url):
        CPyServices.__init__(self, url)
        self.api = urlparse.urljoin(url, '/api/distant_monitoring/')

    def createPractitioner(self, personId):
        return self.post('create_practitioner', { 'person_id': personId })

    def editPractitioner(self, personId):
        return self.post('edit_practitioner', { 'person_id': personId })

    def createDevice(self, equipmentId):
        return self.post('create_device', { 'equipment_id': equipmentId })

    def deactivateDevice(self, equipmentId):
        return self.post('deactivate_device', { 'equipment_id': equipmentId })

    def createServiceRequest(self, params):
        response = self.post('create_service_request', params)
        return response['event_id']

    def editServiceRequest(self, params):
        return self.post('edit_service_request', params)

    def createProcedure(self, params):
        return self.post('create_procedure', params)

    def createDeviceUseStatement(self, params):
        return self.post('create_device_use_statement', params)

    def createSubscription(self, event_id):
        return self.post('create_subscription', { 'event_id': event_id })

    def disableSubscription(self, event_id):
        return self.post('disable_subscription', { 'event_id': event_id })

    def openWebApp(self, personSnils, clientSnils=None):
        url = 'authenticate_doctor_by_snils?person_snils=' + urllib.quote(personSnils)
        if clientSnils:
            url += '&client_snils=' + urllib.quote(clientSnils)
        url = urlparse.urljoin(self.api, url)
        QtGui.QDesktopServices.openUrl(QUrl(url))


def getPyServices(serviceClass):
    url = forceString(QtGui.qApp.getGlobalPreference('23:servicesURL'))
    return serviceClass(url) if url else None
