# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2018-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

#import sys

#from ssl import PROTOCOL_SSLv23, SSLContext
from PyQt4.QtCore import QDateTime

from Exchange.FSSv2.generated.FileOperationsLnService_client import ( FileOperationsLnServiceLocator,
                                                                      GetNewLNNumRangeRequest,
                                                                      GetLNDataRequest,
                                                                      PrParseFilelnlpuRequest,
                                                                    )
from Exchange.FSSv2.generated.FileOperationsLnService_types  import ns2 as fssMo
from Exchange.FSSv2.generated.fssns  import fssNsDict

from Exchange.FSSv2.fixSoapEnvPrefixHandler import CFixSoapEnvPrefixHandler
from Exchange.FSSv2.appendXmlToHeader       import CAppendXmlToHeader
from Exchange.FSSv2.signatureHandler        import CSignatureHandler
from Exchange.FSSv2.chainHandler            import CChainHandler
from Exchange.FSSv2.encryptionHandler       import CEncryptionHandler
from Exchange.FSSv2.FssSignInfo             import CFssSignInfo
from Exchange.FSSv2.zsiUtils                import (
                                                     createPyObject,
                                                     convertQDateToTuple,
                                                     convertTupleToQDate,
                                                     fixu,
                                                     getCryptoNsDict,
                                                     patchDateEtcFormat,
                                                     restoreFromXml,
#                                                     serializeAndRestore,
                                                   )
from library.BaseApp                        import CBaseApp
from library.HttpsConnection                import CHttpsConnection
from library.MSCAPI                         import MSCApi
from library.Utils                          import (
#                                                     calcAgeInMonths,
#                                                     calcAgeInYears,
                                                     exceptionToUnicode,
                                                     forceBool,
                                                     forceDate,
                                                     forceDateTime,
                                                     forceInt,
                                                     forceRef,
                                                     forceString,
                                                     forceStringEx,
                                                     formatList,
#                                                     formatName,
                                                     formatSNILS,
                                                     withWaitCursor,
                                                   )

from selectReadyTempInvalidDocumentIds    import getDateOfDirectionToMse


class CApp(CBaseApp):
#    __pyqtSignals__ = ('dbConnectionChanged(bool)',
#                       'currentUserIdChanged()',
#                      )

    title       = u'САМСОН-СФР-ЭЛН-v2'
    titleLat    =  'SAMSON-FSS-ELN-V2'
    version     =  '2.5'

    iniFileName = 'fsseln.ini'
    logFileName = 'fsseln.log'

    systemFssCode = u'СФР'
    systemFssName = u'Фонд социального страхования Российской Федерации'

    defaultRequestedNumbersQuantity = 5
    minRequestedNumbersQuantity     = 1
    maxRequestedNumbersQuantity     = 1000

    docStateName = {
                    '010' : u'ЭЛН открыт',
                    '020' : u'ЭЛН продлен',
                    '030' : u'ЭЛН закрыт',
                    '040' : u'ЭЛН направление на МСЭ',
                    '050' : u'ЭЛН дополнен данными МСЭ',
                    '060' : u'ЭЛН заполнен Страхователем',
                    '070' : u'ЭЛН заполнен Страхователем (реестр ПВСО)',
                    '080' : u'Пособие выплачено',
                    '090' : u'Действия прекращены',
                   }


    @classmethod
    def getLatVersion(cls):
        return u'%s, v.%s (rev. %s from %s)' % (cls.titleLat, cls.version, cls.lastChangedRev, cls.lastChangedDate)


    def __init__(self, args, iniFileName, disableLock, logSql):
        CBaseApp.__init__(self, args, iniFileName or self.initFileName)
        self.disableLock = disableLock
        self.logSql = logSql


    def getTempInvalidDocTypeId(self):
        db = self.db
        table = db.table('rbTempInvalidDocument')
        record = db.getRecordEx(table,
                                'id',
                                [ table['type'].eq(0),  # 0-ВУТ
                                  table['code'].eq('1') # Листок нетрудоспособности
                                ]
                               )
        if record:
            result = forceRef(record.value('id'))
            return result
        raise Exception(u'В базе данных нет записи для листка нетрудоспособности rbTempInvalidDocument.type=0 and rbTempInvalidDocument.code=\'1\'')


    def getTempInvalidBlankTypeId(self):
        db = self.db
        table = db.table('rbBlankTempInvalids')
        record = db.getRecordEx(table,
                                'id',
                                 table['code'].eq(u'01Э') # "Электронный листок нетрудоспособности
                               )
        if record:
            return forceRef(record.value('id'))
        else:
            record = table.newRecord()
            record.setValue('code', u'01Э')
            record.setValue('name', u'Электронный листок нетрудоспособности')
            record.setValue('doctype_id',  self.getTempInvalidDocTypeId())
            return db.insertRecord(table, record)


    def getCurrentOrgOgrn(self):
        orgId = self.getCurrentOrgId()
        result = forceString(self.db.translate('Organisation', 'id', orgId, 'OGRN'))
        if not result:
            raise Exception(u'Для текущей огранизации (Organisation.id=%r) не определён ОГРН' % orgId)
        return result


    def getUserSnils(self):
        result = forceString(self.db.translate('Person', 'id', self.userId, 'SNILS'))
        if not result:
            raise Exception(u'Для текущего пользователя (Person.id=%r) не определён СНИЛС' % self.userId)
        return result


    def getUserName(self):
        result = forceString(self.db.translate('vrbPerson', 'id', self.userId, 'name'))
        return result


    def getUserConact(self, mask):
        db = self.db
        tablePersonContact = db.table('Person_Contact')
        tableContactType   = db.table('rbContactType')
        table = tablePersonContact.innerJoin(tableContactType,
                                             tableContactType['id'].eq(tablePersonContact['contactType_id']))
        record = db.getRecordEx(table,
                                tablePersonContact['contact'],
                                [ tablePersonContact['deleted'].eq(0),
                                  tableContactType['name'].like(mask)
                                ]
                               )
        if record:
            return forceStringEx(record.value('contact'))
        return ''


    def getUserPhone(self):
        return self.getUserConact('%раб%тел%') or self.getUserConact('%тел%раб%')


    def getUserEmail(self):
        return self.getUserConact('%mail%') or self.getUserConact('%эл%поч%')


    def getRequestedNumbersQuantity(self):
        result = forceInt(self.preferences.appPrefs.get('requestedNumbersQuantity', self.defaultRequestedNumbersQuantity))
        return max(min(self.maxRequestedNumbersQuantity, result), self.minRequestedNumbersQuantity)


    def getCsp(self):
        result = forceString(self.preferences.appPrefs.get('csp', ''))
        if not result:
            raise Exception(u'В настройках не определён криптопровайдер')
        return result


    def getUseOwnPk(self):
        return forceBool(self.preferences.appPrefs.get('useOwnPk', True))


    def getUserCertSha1(self):
        result = forceString(self.preferences.appPrefs.get('userCertSha1', ''))
        if not result:
            raise Exception(u'В настройках не определён сертификат пользователя')
        return result


    def getServiceUrl(self):
        result = forceString(self.preferences.appPrefs.get('serviceUrl', ''))
        if not result:
            db = self.db
            tableGP = db.table('GlobalPreferences')
            recordUrlELN = db.getRecordList(tableGP, 'value', [tableGP['note'].eq('ELN')], 'code')
            result = [forceString(item.value('value')) for item in recordUrlELN if recordUrlELN]
        if not result:
            raise Exception(u'В настройках не определён URL сервиса')
        return result


    def getUseEncryption(self):
        return forceBool(self.preferences.appPrefs.get('useEncryption', ''))


    def getFssCertSha1(self):
        result = forceString(self.preferences.appPrefs.get('fssCertSha1', ''))
        if not result:
            raise Exception(u'В настройках не определён сертификат СФР')
        return result


    def getUserCert(self, api):
        now = QDateTime.currentDateTime().toPyDateTime()
        if self.getUseOwnPk():
            snils = self.getUserSnils()
            result = api.findCertInStores(api.SNS_OWN_CERTIFICATES, snils=snils, datetime=now)
            if not result:
                raise Exception(u'Не удалось найти действующий сертификат пользователя по СНИЛС «%s»' % formatSNILS(snils))
        else:
            userCertSha1 = self.getUserCertSha1()
            result = api.findCertInStores(api.SNS_OWN_CERTIFICATES, sha1hex=userCertSha1)
            if not result:
                raise Exception(u'Не удалось найти сертификат пользователя с отпечатком sha1 %s' % userCertSha1)
            if not result.notBefore() <= now <= result.notAfter():
                raise Exception(u'Сертификат пользователя с отпечатком sha1 %s найден, но сейчас не действителен' %  userCertSha1)
        return result
    
    
    def getCurrentUserMchd(self):
        db = self.db
        tablePersonIdentification = db.table('Person_Identification')
        tableAccountingSystem = db.table('rbAccountingSystem')
        query = db.innerJoin(tablePersonIdentification, tableAccountingSystem, tableAccountingSystem['id'].eq(tablePersonIdentification['system_id']))
        cond = [
            tablePersonIdentification['master_id'].eq(self.userId),
            tablePersonIdentification['deleted'].eq(0),
            tablePersonIdentification['value'].ne(''),
            tableAccountingSystem['code'].eq('MCHD_SFR')
        ]
        record = db.getRecordEx(query, cols=tablePersonIdentification['value'], where=cond, order='Person_Identification.id desc')
        return forceString(record.value('value')) if record else None


    def getUserCertAndMchd(self, api):
        mchd = None
        userCert = self.getUserCert(api)
        if not userCert.ogrn():
            mchd = self.getCurrentUserMchd()
            if not mchd:
                raise Exception(u'Для отправки данных необходимо наличие подписи организации или машиночитаемой доверенности')
        return (userCert, mchd)
        

    def getFssCert(self, api):
        fssCertSha1 = self.getFssCertSha1()
        result = api.findCertInStores([api.SNS_OTHER_CERTIFICATES, api.SNS_OWN_CERTIFICATES], sha1hex=fssCertSha1)
        if not result:
            raise Exception(u'Не удалось найти сертификат СФР с отпечатком sha1 %s' % fssCertSha1)
        today = QDateTime.currentDateTime().toPyDateTime()
        if not result.notBefore() <= today <= result.notAfter():
            raise Exception(u'Сертификат СФР с отпечатком sha1 %s найден, но сейчас не действителен' %  fssCertSha1)
        return result


    def getFssSystemId(self):
        db = self.db
        tableExternalSystem = db.table('rbExternalSystem')
        systemId = forceRef(db.translate(tableExternalSystem, 'code', self.systemFssCode, 'id'))
        if systemId is None:
            record = tableExternalSystem.newRecord()
            record.setValue('code', self.systemFssCode)
            record.setValue('name', self.systemFssName)
            systemId = db.insertRecord(tableExternalSystem, record)
        return systemId


    def getProxyPreferences(self):
        props = self.preferences.appPrefs
        useProxy = forceBool(props.get('useProxy', False))

        proxyAddress  = None
        proxyPort     = None
        proxyLogin    = None
        proxyPassword = None

        if useProxy:
            proxyAddress = forceString(props.get('proxyAddress', ''))
            proxyPort    = forceInt(props.get('proxyPort', 0))
            proxyUseAuth = forceBool(props.get('proxyUseAuth', False))
            if proxyUseAuth:
                proxyLogin    = forceString(props.get('proxyLogin', ''))
                proxyPassword = forceString(props.get('proxyPassword', ''))

        return { 'address' : proxyAddress,
                 'port'    : proxyPort,
                 'login'   : proxyLogin,
                 'password': proxyPassword,
               }


    @withWaitCursor
    def requestNumbers(self):
        csp    = self.getCsp()
        myOgrn = self.getCurrentOrgOgrn()
        api = MSCApi(csp)

        request = GetNewLNNumRangeRequest()
        request.Ogrn = myOgrn
        request.CntLnNumbers = self.getRequestedNumbersQuantity()
        bodyId, actorUri = CFssSignInfo.getMoElementIdAndActorUri(myOgrn)
        port, mchd = self.__getPort(api, actorUri, bodyId, signBody=True)
        response = port.GetNewLNNumRange(request)
        if not response.Status:
            raise Exception(fixu(response.Mess))
        result = [unicode(lnCode) for lnCode in response.Data.LnCode] if response.Data and response.Data.LnCode else []
        return result

    @withWaitCursor
    def sendDocument(self, tempInvalidDocumentId):
        csp           = self.getCsp()
        myOgrn        = self.getCurrentOrgOgrn()
        api = MSCApi(csp)

        documentInfo = self.__getDocumentInfo(tempInvalidDocumentId)
        # запросить состояние документа
        # если такой документ уже есть, то берём его за основу.
        document = self.__getDocumentFromFss(api, myOgrn, documentInfo)
        if not document:
            document = self.__fillNewDocument(myOgrn, documentInfo)
        documentElementId, documentActorUri = CFssSignInfo.getMoElementIdAndActorUri(myOgrn, documentInfo['number'])
        document.set_attribute_Id(documentElementId)
        self.__fillHospitalisationDates(document, documentInfo)
        # if documentInfo['begDateStationary'] and documentInfo['endDateStationary']:
        #     document.HospitalDt1 = convertQDateToTuple(documentInfo['begDateStationary'])
        #     document.HospitalDt2 = convertQDateToTuple(documentInfo['endDateStationary'])
        fssStatus = documentInfo['fssStatus']
        securities = []
        steps      = []
        signerId = None
        mseDate = None
        skipDocumentPost = False
        if fssStatus == '':
            if self.__checkPeriodPresence(document, securities, documentInfo, 0):
                nextFssStatus = 'P0'
                steps.append(u'проверка первого периода')
                skipDocumentPost = True
            else:
                if self.__fillPeriod(document, securities, documentInfo, 0):
                    careInfoList = self.__getCareInfoList(tempInvalidDocumentId, documentInfo['clientId'])
                    self.__fillServsPeriod(document, careInfoList, 0)
                    nextFssStatus = 'P0'
                    steps.append(u'передача первого периода')
                    signerId = self.__getPeriodSignerId(documentInfo, 0)
                mseDate = getDateOfDirectionToMse(tempInvalidDocumentId)
        elif fssStatus == 'P0':
            if self.__checkPeriodPresence(document, securities, documentInfo, 1):
                nextFssStatus = 'P1'
                steps.append(u'проверка второго периода')
                skipDocumentPost = True
            else:
                if self.__fillPeriod(document, securities, documentInfo, 1):
                    careInfoList = self.__getCareInfoList(tempInvalidDocumentId, documentInfo['clientId'])
                    self.__fillServsPeriod(document, careInfoList, 1)
                    nextFssStatus = 'P1'
                    steps.append(u'передача второго периода')
                    signerId = self.__getPeriodSignerId(documentInfo, 1) or signerId
                mseDate = getDateOfDirectionToMse(tempInvalidDocumentId)
        elif fssStatus == 'P1':
            if self.__checkPeriodPresence(document, securities, documentInfo, 2):
                nextFssStatus = 'P2'
                steps.append(u'проверка третьего периода')
                skipDocumentPost = True
            else:
                if self.__fillPeriod(document, securities, documentInfo, 2):
                    careInfoList = self.__getCareInfoList(tempInvalidDocumentId, documentInfo['clientId'])
                    self.__fillServsPeriod(document, careInfoList, 2)
                    nextFssStatus = 'P2'
                    steps.append(u'передача третьего периода')
                    signerId = self.__getPeriodSignerId(documentInfo, 2) or signerId
                mseDate = getDateOfDirectionToMse(tempInvalidDocumentId)
        elif fssStatus == 'P2':
            mseDate = getDateOfDirectionToMse(tempInvalidDocumentId)
            pass
        elif fssStatus == 'M':
            pass

        if skipDocumentPost:
            ok, message = True, u'Исправление рассинхронизации с сервисом СФР'
        else:
            if not (document.ServData and document.ServData.ServFullData):
                    document.Diagnos  = self.__hideDiagnosis(documentInfo['diagnosis'])

            if document.HospitalBreach is None:
                if self.__fillBreach(document, securities, documentInfo):
                    steps.append(u'передача нарушения режима')
                    signerId = self.__getBreachSignerId(documentInfo) or signerId

            if mseDate:
                document.MseDt1 = convertQDateToTuple(mseDate)
                nextFssStatus = 'M'
                steps.append(u'передача направления на МСЭ')

            if self.__fillResult(document, securities, documentInfo):
                nextFssStatus = 'R'
                steps.append(u'закрытие ЭЛН')
                signerId = self.__getResultSignerId(documentInfo) or signerId

            # фиксируем требования ФЛК
            document.WrittenAgreementFlag = True
            if document.Reason1 in ('09', '12', '13', '14', '15'):
                if document.ServData and document.ServData.ServFullData:
                    document.Reason1 = None
                    document.Diagnos = None
                    document.HospitalDt1 = None
                    document.HospitalDt2 = None

            ok, message, mchd = self.__postDocumentToFss(api, myOgrn, document, securities)
        if ok:
            self.__updateFssStatus(tempInvalidDocumentId, nextFssStatus)
        if steps:
            message = u'%s (%s)' %(message, ', '.join(steps))
        self.__logDocumentPost(documentInfo, ok, message, signerId, mchd)
        return ok, documentInfo['number'], message



    @withWaitCursor
    def checkExpiredDocument(self, tempInvalidDocumentId):
        csp           = self.getCsp()
        myOgrn        = self.getCurrentOrgOgrn()
        api = MSCApi(csp)

        documentInfo = self.__getDocumentInfo(tempInvalidDocumentId)
        document = self.__getDocumentFromFss(api, myOgrn, documentInfo)
        if document is None:
            return False, documentInfo['number'], u'Сервис СФР не предоставил информации об ЭЛН'

        parts = [ u'%s %s' % (document.LnState,
                              self.docStateName.get(document.LnState, u'(не известно)')
                             )
                ]

        try:
            ok = True
            if document.LnState in ('030', '060', '070', '080'):
                # 030,060,070,080 - переводим эпизод в состояние "передан" присваевая результат с кодом "31" и пустым "решением"
                # При этом не устанавливаем никаких дат
                    self.__closeTempInvalid(tempInvalidDocumentId, 3, '31', 0, None, None)
                    parts.append(u'Случай ВУТ помечен как переданный')
            elif document.LnState in ('040', '050'):
                # 040,050 - переводим эпизод в состояние "передан" присваевая результат с кодом "31" и "решение"="направление на МСЭ". 
                # При этом устанавливаем дату регистрации / освидетельствования в направлении на МСЭ (при наличии)
                otherwiseDate = document.MseDt1
                if otherwiseDate:
                    self.__closeTempInvalid(tempInvalidDocumentId, 3, '31', 3, None, convertTupleToQDate(otherwiseDate))
                    parts.append(u'Случай ВУТ помечен как переданный с направлением на МСЭ')
                else:
                    ok = False
                    parts.append(u'Сервис СФР не сообщил дату направления на МСЭ')
            elif document.LnState == '090':
                # 090 - переводим эпизод в состояние "Аннулирован" присваивая результат с кодом "99" 
                self.__closeTempInvalid(tempInvalidDocumentId, 4, '99', None, None, None)
                parts.append(u'Случай ВУТ помечен как аннулированный')
        except Exception as e:
            self.logCurrentException()
            parts.append( exceptionToUnicode(e) )
            ok = False

        return ok, documentInfo['number'], u'; '.join(parts)


    def __hideDiagnosis(self, diagnosis):
        if (not diagnosis
            or ('C00' <= diagnosis < 'D49/')  # «онкология», «детская онкология»
            or ('A50' <= diagnosis < 'A74/')  # «дерматовенерология»,
            or ('B35' <= diagnosis < 'B99/')  # «дерматовенерология»,
            or ('F00' <= diagnosis < 'F99/')  # «психиатрия-наркология», психические расстройства и расстройствах поведения
            or ('B20' <= diagnosis < 'B24/')  # медицинская помощь при заболевании, вызываемом вирусом иммунодефицита человека (ВИЧ-инфекции)
            or ('A15' <= diagnosis < 'A19/')  # медицинская помощь больным туберкулезом
            or (diagnosis in ['Z11.3', 'Z20.2', 'Z22.4', 'Z04.0', 'Z50.3', 'Z71.5', 'Z72.2',
                               'Z50.2', 'Z71.4', 'Z72.1', 'Z81.1', 'Z03.0', 'Z11.1', 'Z20.1'])
            ):
            return '0000000000'
        else:
            return diagnosis


    def __getCareInfoList(self, tempInvalidDocumentId, mainClientId):
        db = self.db
        tableTempInvalidDocumentCare = db.table('TempInvalidDocument_Care')
        tableClient                  = db.table('Client')
        tableTempInvalidReason       = db.table('rbTempInvalidReason')
        tableTempInvalidRegime       = db.table('rbTempInvalidRegime')

        table = tableTempInvalidDocumentCare
        table = table.innerJoin(tableClient,           tableClient['id'].eq(tableTempInvalidDocumentCare['client_id']))
        table = table.leftJoin(tableTempInvalidReason, tableTempInvalidReason['id'].eq(tableTempInvalidDocumentCare['tempInvalidReason_id']))
        table = table.leftJoin(tableTempInvalidRegime, tableTempInvalidRegime['id'].eq(tableTempInvalidDocumentCare['tempInvalidRegime_id']))

        records = db.getRecordList(table,
                                   [ tableTempInvalidDocumentCare['begDate'],
                                     tableTempInvalidDocumentCare['endDate'],
                                     tableTempInvalidDocumentCare['MKB'],
                                     tableTempInvalidDocumentCare['client_id'],
                                     tableClient['lastName'],
                                     tableClient['firstName'],
                                     tableClient['patrName'],
                                     tableClient['sex'],
                                     tableClient['birthDate'],
                                     tableClient['SNILS'],
                                     tableTempInvalidReason['code'].alias('reasonCode'),
                                     tableTempInvalidRegime['code'].alias('regimeCode'),
                                   ],
                                   tableTempInvalidDocumentCare['master_id'].eq(tempInvalidDocumentId),
                                   tableTempInvalidDocumentCare['idx'].name()
                                  )
        result = []
        for record in records:
            clientId  = forceRef(record.value('client_id'))
            item = {
                     'clientId'          : clientId, # for debug purposes
                     'begDate'           : forceDate(record.value('begDate')),
                     'endDate'           : forceDate(record.value('endDate')),
                     'diagnosis'         : forceString(record.value('MKB')) or None,
                     'lastName'          : forceStringEx(record.value('lastName')).upper(),
                     'firstName'         : forceStringEx(record.value('firstName')).upper(),
                     'patrName'          : forceStringEx(record.value('patrName')).upper() or None,
                     'sex'               : forceInt(record.value('sex')),
                     'birthDate'         : forceDate(record.value('birthDate')),
                     'SNILS'             : forceString(record.value('SNILS')) or None,
                     'relation'          : self.__getRelation(mainClientId, clientId),
                     'reasonCode'        : forceString(record.value('reasonCode')) or None,
                     'regimeCode'        : forceString(record.value('regimeCode')) or None,
                   }
            result.append(item)
        return result


    def __getOrgStructureAddress(self, orgStructureId):
        db = self.db
        table = db.table('OrgStructure')
        while orgStructureId:
            record = db.getRecord(table, 'address, parent_id', orgStructureId)
            address = forceStringEx(record.value('address'))
            if address:
                return address
            orgStructureId = forceRef(record.value('parent_id'))
        return None


    def __getDocumentInfo(self, tempInvalidDocumentId):
        db = self.db
        tableTempInvalidDocument      = db.table('TempInvalidDocument')
        tableOrigTempInvalidDocument  = db.table('TempInvalidDocument').alias('OrigTempInvalidDocument')
        tableTempInvalid              = db.table('TempInvalid')
        tableClient                   = db.table('Client')
        tableDiagnosis                = db.table('Diagnosis')
        tableTempInvalidReason        = db.table('rbTempInvalidReason')
        tableTempInvalidExtraReason   = db.table('rbTempInvalidExtraReason')
        tableTempInvalidChangedReason = db.table('rbTempInvalidReason').alias('rbTempInvalidChangedReason')
        tablePerson                   = db.table('Person')

        table = tableTempInvalidDocument
        table = table.innerJoin(tableTempInvalid,             tableTempInvalid['id'].eq(tableTempInvalidDocument['master_id']))
        table = table.innerJoin(tableClient,                  tableClient['id'].eq(tableTempInvalid['client_id']))
        table = table.leftJoin(tableOrigTempInvalidDocument,  tableOrigTempInvalidDocument['id'].eq(tableTempInvalidDocument['prevDuplicate_id']))
        table = table.leftJoin(tableDiagnosis,                tableDiagnosis['id'].eq(tableTempInvalid['diagnosis_id']))
        table = table.leftJoin(tableTempInvalidReason,        tableTempInvalidReason['id'].eq(tableTempInvalid['tempInvalidReason_id']))
        table = table.leftJoin(tableTempInvalidExtraReason,   tableTempInvalidExtraReason['id'].eq(tableTempInvalid['tempInvalidExtraReason_id']))
        table = table.leftJoin(tableTempInvalidChangedReason, tableTempInvalidChangedReason['id'].eq(tableTempInvalid['tempInvalidChangedReason_id']))
        table = table.leftJoin(tablePerson,                   tablePerson['id'].eq(tableTempInvalidDocument['person_id']))

        record = db.getRecordEx(table,
                                [   tableTempInvalidDocument['number'],     # Номер документа
                                    tableTempInvalidDocument['prevNumber'], # Продолжение документа с номером
                                    tableTempInvalidDocument['duplicate'],  # Флаг "дубликат" (Нет/Да)
                                    tableOrigTempInvalidDocument['number'].alias('origNumber'), # исходный номер для дубликата
                                    tableTempInvalidDocument['issueDate'],  # Дата выдачи листа нетрудоспособности

                                    tableClient['lastName'],
                                    tableClient['firstName'],
                                    tableClient['patrName'],
                                    tableClient['sex'],
                                    tableClient['birthDate'],
                                    tableClient['SNILS'],
                                    # сведения о МО берутся из настройки
                                    tableTempInvalidReason['code'].alias('reasonCode'),
                                    tableTempInvalidExtraReason['code'].alias('extraReasonCode'),
                                    tableTempInvalidChangedReason['code'].alias('changedReasonCode'),
                                    tableDiagnosis['MKB'].alias('diagnosis'),
                                    tableTempInvalid['id'].alias('tempInvalid_id'),
                                    tableTempInvalid['begDatePermit'],
                                    tableTempInvalid['endDatePermit'],
                                    tableTempInvalid['numberPermit'],
                                    tableTempInvalid['OGRN'].alias('OGRNPermit'),

                                    tableTempInvalid['accountPregnancyTo12Weeks'],
                                    tableTempInvalid['begDateStationary'],
                                    tableTempInvalid['endDateStationary'],

                                    tablePerson['orgStructure_id'],
#################################################################################
                                    tableTempInvalid['client_id'],
                                    tableTempInvalidDocument['modifyDatetime'],
                                    tableTempInvalidDocument['fssStatus'],  # Состояние ЛН с точки зрения обмена с СФР ''-не определено, P0-P2-переданы периоды, M-передано напр.на МСЭ, R-закрыто

#                                    tableTempInvalid['resultDate'],
#                                    tableTempInvalid['resultOtherwiseDate'],

                                ],
                                tableTempInvalidDocument['id'].eq(tempInvalidDocumentId)
                             )

        orgStructureId = forceRef(record.value('orgStructure_id'))

        orgRecord = db.getRecord('Organisation',
                                 ['fullName', 'shortName', 'title', 'address'],
                                 self.getCurrentOrgId()
                                )

        tableTempInvalidDocumentSignature = db.table('TempInvalidDocument_Signature')
        signatureRecords = db.getRecordList(tableTempInvalidDocumentSignature,
                                            '*',
                                            tableTempInvalidDocumentSignature['master_id'].eq(tempInvalidDocumentId))
        signatures  = {}
        for signatureRecord in signatureRecords:
            subject = forceString(signatureRecord.value('subject'))
            signature = { 'id':      forceInt(signatureRecord.value('id')),
                          'subject': subject,
                          'dataXml': forceString(signatureRecord.value('dataXml')),
                          'securityXml': forceString(signatureRecord.value('securityXml')),
                          'begDate': forceDate(signatureRecord.value('begDate')),
                          'endDate': forceDate(signatureRecord.value('endDate')),
                          'signPersonId': forceRef(signatureRecord.value('signPerson_id')),
                        }
            signatures[subject] = signature

        clientId  = forceRef(record.value('client_id'))
        parentNumber = None
        isDuplicate = forceBool(record.value('duplicate'))
        origNumber  = forceString(record.value('origNumber'))
        if not isDuplicate or not origNumber:
            isDuplicate = False
            origNumber  = None

        return {
                 'clientId'          : clientId, # for internal purposes
                 'SNILS'             : forceString(record.value('SNILS')),
                 'lastName'          : forceStringEx(record.value('lastName')).upper(),
                 'firstName'         : forceStringEx(record.value('firstName')).upper(),
                 'patrName'          : forceStringEx(record.value('patrName')).upper() or None,
                 'sex'               : forceInt(record.value('sex')),
                 'birthDate'         : forceDate(record.value('birthDate')),

                 'number'            : forceString(record.value('number')),
                 'parentNumber'      : parentNumber,
                 'prevNumber'        : forceString(record.value('prevNumber')) or None,
#                 'isPrimary'         : not forceRef(record.value('prev_id')),
                 'isDuplicate'       : isDuplicate,
                 'origNumber'        : origNumber,
                 'issueDate'         : forceDate(record.value('issueDate')),
                 'orgName'           : ( #  forceString(orgRecord.value('title'))
                                         # or
                                           forceStringEx(orgRecord.value('shortName'))
                                        or forceStringEx(orgRecord.value('fullName'))
                                       ).upper(),
                 'orgAddress'        : (self.__getOrgStructureAddress(orgStructureId) or forceStringEx(orgRecord.value('address'))).upper(),
                 'reasonCode'        : forceString(record.value('reasonCode')) or None,
                 'extraReasonCode'   : forceString(record.value('extraReasonCode')) or None,
                 'changedReasonCode' : forceString(record.value('changedReasonCode')) or None,
                 'diagnosis'         : forceString(record.value('diagnosis')) or None,
                 'begDatePermit'     : forceDate(record.value('begDatePermit')) or None,
                 'endDatePermit'     : forceDate(record.value('endDatePermit')) or None,
                 'numberPermit'      : forceString(record.value('numberPermit')) or None,
                 'OGRNPermit'        : forceString(record.value('OGRNPermit')) or None,
                 'accountPregnancyTo12Weeks': forceInt(record.value('accountPregnancyTo12Weeks')),
                 'begDateStationary' : forceDate(record.value('begDateStationary')),
                 'endDateStationary' : forceDate(record.value('endDateStationary')),
                 #################################################################################
                 'id'                : tempInvalidDocumentId,
                 'modifyDatetime'    : forceDateTime(record.value('modifyDatetime')),
                 'fssStatus'         : forceString(record.value('fssStatus')),
                 'signatures'        : signatures,
               }


    def __getRelation(self, clientId, relatedId):
        if not relatedId:
            return None
        db = self.db
        tableClientRelation = db.table('ClientRelation')
        tableRelationType   = db.table('rbRelationType')
        table = tableClientRelation.innerJoin(tableRelationType,
                                              tableRelationType['id'].eq(tableClientRelation['relativeType_id'])
                                             )
        record = db.getRecordEx(table,
                                [ tableRelationType['code'],
                                ],
                                [ tableClientRelation['deleted'].eq(0),
                                  tableClientRelation['client_id'].eq(clientId),
                                  tableClientRelation['relative_id'].eq(relatedId),
                                ]
                               )
        if not record:
            record = db.getRecordEx(table,
                                    [ tableRelationType['code'],
                                    ],
                                    [ tableClientRelation['deleted'].eq(0),
                                      tableClientRelation['client_id'].eq(relatedId),
                                      tableClientRelation['relative_id'].eq(clientId),
                                    ]
                                   )
        if record:
            code = forceString(record.value('code'))
        else:
            code = '00'

        map = { '01' : '38', '02': '38', '05': '38', '06': '38', # мать
                '03' : '39', '04': '39', '07': '39', '08': '39', # отец
                '09' : '40', '10': '40', '11': '40',             # опекун
                None : '42',
              }
        return map.get(code) or map.get(None)


    def __updateFssStatus(self, tempInvalidDocumentId, nextFssStatus):
        db = self.db
        tableTempInvalidDocument = db.table('TempInvalidDocument')
        record = tableTempInvalidDocument.newRecord(['id', 'fssStatus'])
        record.setValue('id', tempInvalidDocumentId)
        record.setValue('fssStatus', nextFssStatus)
        db.updateRecord(tableTempInvalidDocument, record)


    def __logDocumentPost(self, documentInfo, ok, message, signerId, mchd):
        db = self.db
        tableTempInvalidDocumentExport = db.table('TempInvalidDocument_Export')
        record = tableTempInvalidDocumentExport.newRecord()
        record.setValue('master_id',      documentInfo['id'])
        record.setValue('masterDatetime', documentInfo['modifyDatetime'])
        record.setValue('system_id',      self.getFssSystemId())
        record.setValue('person_id',      self.userId)
        record.setValue('dateTime',       QDateTime.currentDateTime())
        record.setValue('success',        ok)
        record.setValue('externalId',     documentInfo['number'])
        record.setValue('note',           message)
        record.setValue('respPerson_id',  signerId)
        record.setValue('proxy',          mchd)
        db.insertRecord(tableTempInvalidDocumentExport, record)


    def __getPort(self, api, actorUri, signElementId, signBody=False, securities=None):
        useEncryption  = self.getUseEncryption()
        serviceUrl     = self.getServiceUrl()
        if type(serviceUrl) is list:
            serviceUrl = serviceUrl[0]
        userCert, mchd = self.getUserCertAndMchd(api)
        nsdict = getCryptoNsDict().copy()
        nsdict.update(fssNsDict)
#        log = sys.stdout
        locator = FileOperationsLnServiceLocator()
        port    = locator.getFileOperationsLnPort(serviceUrl,
                                                  nsdict    = nsdict,
                                                  transport = CHttpsConnection,
                                                  transdict = { 'proxy': self.getProxyPreferences()
                                                              }
#                                                  tracefile = log,
                                                 )
        handler = CChainHandler()
        handler.append( CFixSoapEnvPrefixHandler() )
        if securities:
            handler.append( CAppendXmlToHeader(securities) )
        handler.append( CSignatureHandler(api,
                                          userCert=userCert,
                                          actorUri=actorUri,
                                          signBody=signBody,
                                          signElementId=signElementId,
                                          mchd=mchd
                                         )
                      )

        if useEncryption:
            fssCert = self.getFssCert(api)
            handler.append( CEncryptionHandler(api,
                                               userCert = userCert,
                                               receiverCert = fssCert,
                                              )
                          )

        port.binding.sig_handler = handler
        return (port, mchd)


    def __getDocumentFromFss(self, api, myOgrn, documentInfo):
#        return None
        # Получить документ из СФР для последующего обновления
        request = GetLNDataRequest()
        request.Ogrn   = myOgrn
        request.LnCode = documentInfo['number']
        request.Snils  = documentInfo['SNILS']
        bodyId, actorUri = CFssSignInfo.getMoElementIdAndActorUri(myOgrn)
        port, mchd = self.__getPort(api, actorUri, bodyId, signBody=True)
        response = port.GetLNData(request)


        if response.Status:
#            print 'response', type(response), dir(response)
#            print 'response.Data', type(response.Data), dir(response.Data)
#            print 'response.Info', type(response.Info), dir(response.Info)

            fssDocument = response.Data.OutRowset.ResponseRow
            return self.__copyFssDocument(fssDocument)
        else:
            return None


    def __postDocumentToFss(self, api, myOgrn, document, securities):
        request = PrParseFilelnlpuRequest()
        patchDateEtcFormat(request.typecode)

#        request.Request = rel = request.new_request()
        request.Ogrn = myOgrn
        pXmlFile = request.PXmlFile = request.new_pXmlFile()
        rowset = pXmlFile.Rowset = pXmlFile.new_rowset()
        rowset.typecode.typed=False
        rowset.set_attribute_author(self.getUserName())
        rowset.set_attribute_email(self.getUserEmail())
        rowset.set_attribute_phone(self.getUserPhone())
        rowset.set_attribute_software(u'САМСОН')
        rowset.set_attribute_version('2.0')
        rowset.set_attribute_version_software('0.2u')
        rowset.Row = [ document ]
        signElementId, actorUri = CFssSignInfo.getMoElementIdAndActorUri(myOgrn, document.LnCode)
        port, mchd = self.__getPort(api, actorUri, signElementId, securities=securities)
        response = port.PrParseFilelnlpu(request)
#        print response, dir(response)
#        out = response.WSResult

        if response.Status:
            return True, (fixu(response.Mess) or 'ok'), mchd
        else:
            messageParts = [fixu(response.Mess)]
            if response.Info and response.Info.InfoRowset and response.Info.InfoRowset.InfoRow:
                for row in response.Info.InfoRowset.InfoRow[0].Errors.Error:
                    messageParts.append('%s\t%s' % ( fixu(row.ErrCode), fixu(row.ErrMess)))

            return False, '\n'.join(messageParts), mchd


    def __copyFssDocument(self, fssDocument):
#        print fssMo.rowset_Dec
        rowset = createPyObject(fssMo.rowset_Dec)
        document = rowset.new_row()

        # шапка
        document.LnCode = fssDocument.LnCode
        document.LnDate = fssDocument.LnDate
        document.LpuAddress = fssDocument.LpuAddress
        document.LpuName = fssDocument.LpuName
        document.LpuOgrn = fssDocument.LpuOgrn
        document.PrevLnCode = fssDocument.PrevLnCode
        document.PreviouslyIssuedCode = fssDocument.PreviouslyIssuedCode

        document.DuplicateFlag = fssDocument.DuplicateFlag
        document.IdMo = fssDocument.IdMo

        # пациент
        document.Surname = fssDocument.Surname
        document.Name = fssDocument.Name
        document.Patronymic = fssDocument.Patronymic
        document.Gender = fssDocument.Gender
        document.Birthday = fssDocument.Birthday
        document.Snils = fssDocument.Snils

        # и т.п.
        document.Date1 = fssDocument.Date1
        document.Date2 = fssDocument.Date2
        document.Diagnos = fssDocument.Diagnos

        if fssDocument.HospitalBreach:
            fssHb = fssDocument.HospitalBreach
            hb = document.HospitalBreach = document.new_hospitalBreach()
            hb.HospitalBreachCode = fssHb.HospitalBreachCode
            hb.HospitalBreachDt = fssHb.HospitalBreachDt

        document.HospitalDt1 = fssDocument.HospitalDt1
        document.HospitalDt2 = fssDocument.HospitalDt2
        document.IntermittentMethodFlag = fssDocument.IntermittentMethodFlag
        document.LnHash = fssDocument.LnHash
        document.LnState = fssDocument.LnState
        document.MseDt1 = fssDocument.MseDt1
        document.MseDt2 = fssDocument.MseDt2
        document.MseDt3 = fssDocument.MseDt3
        document.MseInvalidGroup = fssDocument.MseInvalidGroup
        document.PrimaryFlag = fssDocument.PrimaryFlag
        document.Reason1 = fssDocument.Reason1
        document.Reason2 = fssDocument.Reason2

        if fssDocument.ServData and fssDocument.ServData.ServFullData:
            document.ServData = document.new_servData()
            document.ServData.ServFullData = sfdList = []
            for fssServFullData in fssDocument.ServData.ServFullData:
                servFullData = document.ServData.new_servFullData()
                servFullData.Snils            = fssServFullData.Snils
                servFullData.Surname          = fssServFullData.Surname
                servFullData.Name             = fssServFullData.Name
                servFullData.Patronymic       = fssServFullData.Patronymic
                #servFullData.Gender           = fssServFullData.Gender   # Пола нет
                servFullData.Birthday         = fssServFullData.Birthday
                servFullData.ServRelationCode = fssServFullData.ServRelationCode
                servFullData.Diagnosis        = getattr(fssServFullData, 'Diagnosis', None) # если диагноза нет, то в fssServFullData нет _diagnosis :(
                servFullData.Reason1          = fssServFullData.Reason1
                servFullData.ServDt1          = fssServFullData.ServDt1
                servFullData.ServDt2          = fssServFullData.ServDt2
                servFullData.TreatmentType    = fssServFullData.TreatmentType
                sfdList.append(servFullData)

        document.TreatPeriods = document.new_treatPeriods()
        for fssTfp in fssDocument.TreatPeriods.TreatFullPeriod:
            tfp = document.TreatPeriods.new_treatFullPeriod()
            document.TreatPeriods.TreatFullPeriod.append(tfp)
            tfp.TreatChairman = fssTfp.TreatChairman
            tfp.TreatChairmanRole = fssTfp.TreatChairmanRole
            if fssTfp.TreatPeriod:
                fssTp = fssTfp.TreatPeriod
                tp = tfp.TreatPeriod = tfp.new_treatPeriod()
                tp.IdDoctor        = fssTp.IdDoctor
                tp.TreatDoctor     = fssTp.TreatDoctor
                tp.TreatDoctorRole = fssTp.TreatDoctorRole
                tp.TreatDt1        = fssTp.TreatDt1
                tp.TreatDt2        = fssTp.TreatDt2

        document.VoucherNo            = fssDocument.VoucherNo
        document.VoucherOgrn          = fssDocument.VoucherOgrn
        document.WrittenAgreementFlag = fssDocument.WrittenAgreementFlag

        if fssDocument.LnResult:
            fssLr = fssDocument.LnResult
            lr =  document.LnResult = document.new_lnResult()
            lr.MseResult     = fssLr.MseResult
            lr.NextLnCode    = fssLr.NextLnCode
            lr.OtherStateDt  = fssLr.OtherStateDt
            lr.ReturnDateLpu = fssLr.ReturnDateLpu

        document.Unconditional = True
        return document


    def __fillNewDocument(self, myOgrn, documentInfo):
        # Подготовить новый "пустой" документ (без периодов, нарушения и результата)
        number = documentInfo['number']
#        documentElementId, documentActorUri = CFssSignInfo.getMoElementIdAndActorUri(myOgrn, number)

        rowset = createPyObject(fssMo.rowset_Dec)
        document = rowset.new_row()
#        document.typecode.typed = False # WFT?

        document.Unconditional = True
        document.Surname       = documentInfo['lastName']
        document.Name          = documentInfo['firstName']
        document.Patronymic    = documentInfo['patrName']
        document.Gender        = 0 if documentInfo['sex'] == 1 else 1
        document.Birthday      = convertQDateToTuple(documentInfo['birthDate'])
        document.Snils         = documentInfo['SNILS']

        document.LnCode        = number
        document.PrevLnCode    = documentInfo['prevNumber']
        document.PrimaryFlag   = not bool(documentInfo['prevNumber'])
        document.DuplicateFlag = documentInfo['isDuplicate']
        document.PreviouslyIssuedCode = documentInfo['origNumber']
        document.LnDate        = convertQDateToTuple(documentInfo['issueDate'])

#        document.IdMo          = …
        document.LpuName       = documentInfo['orgName']
        document.LpuAddress    = documentInfo['orgAddress']
        document.LpuOgrn       = myOgrn

        document.Reason1       = documentInfo['reasonCode']
        document.Reason2       = documentInfo['extraReasonCode']
        document.Diagnos       = self.__hideDiagnosis(documentInfo['diagnosis'])
        document.Date1         = convertQDateToTuple(documentInfo['begDatePermit']) if documentInfo['begDatePermit'] else None
        document.Date2         = convertQDateToTuple(documentInfo['endDatePermit']) if documentInfo['endDatePermit'] else None

        document.VoucherNo     = documentInfo['numberPermit']
        document.VoucherOgrn   = documentInfo['OGRNPermit']

#        document.PARENT_CODE   = documentInfo.get('parentNumber', None)

        document.LnState  = '000'

        document.TreatPeriods = document.new_treatPeriods()

        document.WrittenAgreementFlag = True
        document.IntermittentMethodFlag = False
        return document


    def __fillHospitalisationDates(self, document, documentInfo):
        begDate = documentInfo['begDateStationary']
        endDate = documentInfo['endDateStationary']
        if begDate and endDate and begDate <= endDate:
            if document.DuplicateFlag:
                document.HospitalDt1 = convertQDateToTuple(begDate)
                document.HospitalDt2 = convertQDateToTuple(endDate)
            else:
                hasValidSignedPeriod = False
                for sugnatureSubject, signature in documentInfo['signatures'].iteritems():
                    if sugnatureSubject.startswith('D'):
                        if signature['endDate'] == endDate:
                            hasValidSignedPeriod = True
                            break
                if hasValidSignedPeriod:
                    document.HospitalDt1 = convertQDateToTuple(begDate)
                    document.HospitalDt2 = convertQDateToTuple(endDate)


    def __fillPeriod(self, document, securites, documentInfo, periodIdx):
        doctorSignature   = documentInfo['signatures'].get('D%d' % periodIdx)
        chairmanSignature = documentInfo['signatures'].get('C%d' % periodIdx)
        if not doctorSignature:
            return False

        periods = document.TreatPeriods.TreatFullPeriod
        assert len(periods) == periodIdx, u'len(periods) /* %d */ != periodIdx /* %d */' % (len(periods), periodIdx)

        tfp = document.TreatPeriods.new_treatFullPeriod()
        if chairmanSignature:
            tfp = restoreFromXml(tfp, chairmanSignature['dataXml'])
#        else:
#            tfp.treatChairmanRole = ''
#            tfp.treatChairman = ''

        tp = restoreFromXml(tfp.new_treatPeriod(), doctorSignature['dataXml'])
        if tfp.TreatPeriod:
            assert tfp.TreatPeriod.__dict__ == tp.__dict__, u'tfp.TreatPeriod.__dict__ /* %r */ != tp.__dict__ /* %r */' % (tfp.TreatPeriod.__dict__,tp.__dict__)
        else:
            tfp.TreatPeriod = tp
        periods.append(tfp)
        securites.append(doctorSignature['securityXml'])
        if chairmanSignature:
            securites.append(chairmanSignature['securityXml'])
        return True


    def __getPeriodSignerId(self, documentInfo, periodIdx):
        doctorSignature = documentInfo['signatures'].get('D%d' % periodIdx)
        personId = doctorSignature['signPersonId'] if doctorSignature else None
        return personId


    def __fillServsPeriod(self, document, careInfoList, periodIdx):
        treatPeriod = document.TreatPeriods.TreatFullPeriod[periodIdx].TreatPeriod
        periodBegDate = convertTupleToQDate(treatPeriod.TreatDt1)
        periodEndDate = convertTupleToQDate(treatPeriod.TreatDt2)
        servData = document.ServData if document.ServData else document.new_servData()
        sfdList = []
        for careInfo in careInfoList:
            careBegDate = max( periodBegDate, careInfo['begDate']) if careInfo['begDate'] else periodBegDate
            careEndDate = min( periodEndDate, careInfo['endDate']) if careInfo['endDate'] else periodEndDate
            if careBegDate <= careEndDate:
                servFullData = servData.new_servFullData()
                servFullData.Snils            = careInfo['SNILS']
                servFullData.Surname          = careInfo['lastName']
                servFullData.Name             = careInfo['firstName']
                servFullData.Patronymic       = careInfo['patrName']
                #servFullData.Gender           = 0 if careInfo['sex'] == 1 else 1
                servFullData.Birthday         = convertQDateToTuple(careInfo['birthDate'])
                servFullData.ServRelationCode = careInfo['relation']
                servFullData.Diagnosis        = self.__hideDiagnosis(careInfo['diagnosis'])
                servFullData.Reason1          = careInfo['reasonCode']
                servFullData.ServDt1          = convertQDateToTuple(careBegDate)
                servFullData.ServDt2          = convertQDateToTuple(careEndDate)
                servFullData.TreatmentType    = careInfo['regimeCode'] if careInfo['regimeCode'] in ('2', '3') else '1'
                sfdList.append(servFullData)
        if sfdList:
            if not document.ServData:
                document.ServData = servData
                document.ServData.ServFullData = []
            document.ServData.ServFullData.extend(sfdList)


    def __checkPeriodPresence(self, document, securites, documentInfo, periodIdx):
        doctorSignature   = documentInfo['signatures'].get('D%d' % periodIdx)
        chairmanSignature = documentInfo['signatures'].get('C%d' % periodIdx)
        if not doctorSignature:
            return False

        periods = document.TreatPeriods.TreatFullPeriod
        if len(periods) <= periodIdx:
            return False

        tfp = document.TreatPeriods.new_treatFullPeriod()
        if chairmanSignature:
            tfp = restoreFromXml(tfp, chairmanSignature['dataXml'])
#        else:
#            tfp.treatChairmanRole = ''
#            tfp.treatChairman = ''

        tp = restoreFromXml(tfp.new_treatPeriod(), doctorSignature['dataXml'])
        if not tfp.TreatPeriod:
            tfp.TreatPeriod = tp

        presentTfp = periods[periodIdx]

        diffFields = []
        if presentTfp.TreatPeriod.TreatDoctor != tfp.TreatPeriod.TreatDoctor:
            diffFields.append('treatDoctor')
        if presentTfp.TreatPeriod.TreatDoctorRole != tfp.TreatPeriod.TreatDoctorRole:
            diffFields.append('treatDoctorRole')
        if presentTfp.TreatPeriod.TreatDt1 != tfp.TreatPeriod.TreatDt1:
            diffFields.append('treatDt1')
        if presentTfp.TreatPeriod.TreatDt2 != tfp.TreatPeriod.TreatDt2:
            diffFields.append('treatDt2')

        if diffFields:
            raise Exception(u'При попытке передать %s период обнаружено, что сервис СФР уже знает о подобном периоде, но есть различие в %s %s' %
                              ( [u'первый', u'второй', u'третий'][periodIdx],
                                u'свойстве' if len(diffFields) == 1 else u'свойствах',
                                u', '.join(diffFields)
                              )
                           )
        return True


    def __fillBreach(self, document, securites, documentInfo):
        breachSignature   = documentInfo['signatures'].get('B')

        if not breachSignature:
            return False
        breach = document.new_hospitalBreach()
        document.HospitalBreach = restoreFromXml(breach, breachSignature['dataXml'])
        securites.append(breachSignature['securityXml'])
        return True


    def __getBreachSignerId(self, documentInfo):
        breachSignature = documentInfo['signatures'].get('B')
        personId = breachSignature['signPersonId'] if breachSignature else None
        return personId


    def __fillResult(self, document, securites, documentInfo):
        resultSignature   = documentInfo['signatures'].get('R')

        if not resultSignature:
            return False

        result = document.new_lnResult()
        document.LnResult = restoreFromXml(result, resultSignature['dataXml'])
        document.Diagnos   = self.__hideDiagnosis(documentInfo['diagnosis'])
        securites.append(resultSignature['securityXml'])
        return True


    def __getResultSignerId(self, documentInfo):
        resultSignature = documentInfo['signatures'].get('R')
        personId = resultSignature['signPersonId'] if resultSignature else None
        return personId


    def __closeTempInvalid(self, tempInvalidDocumentId, state, resultCode, decision, date, otherwiseDate):
        db = self.db
        tempInvalidId = forceRef(db.translate('TempInvalidDocument', 'id', tempInvalidDocumentId, 'master_id'))
        if not tempInvalidId:
            raise Exception(u'В документе пустая ссылка на случай ВУТ')

        tableTempInvalidResult = db.table('rbTempInvalidResult')
        cond = [ tableTempInvalidResult['type'].eq(0),
                 tableTempInvalidResult['code'].eq(resultCode),
               ]
        if decision is not None:
            cond.append( tableTempInvalidResult['decision'].eq(decision) )
        if state is not None:
            cond.append( tableTempInvalidResult['state'].eq(state) )
        resultRecord = db.getRecordEx(tableTempInvalidResult, 'id', cond, 'id')
        resultId = forceRef(resultRecord.value('id')) if resultRecord else None
        if not resultId:
            parts = [ u'В справочнике «Результаты периода ВУТ» не найдена запись с кодом «%s»' % resultCode ]
            if decision is not None:
                parts.append( u'решением %d' %  decision)
            if state is not None:
                parts.append( u'состоянием %d' % parts)
            raise Exception(formatList(parts))

        tableTempInvalid = db.table('TempInvalid')
        record = tableTempInvalid.newRecord(('id', 'state', 'result_id', 'resultDate', 'resultOtherwiseDate'))
        record.setValue('id',                  tempInvalidId)
        record.setValue('state',               state)
        record.setValue('result_id',           resultId)
        record.setValue('resultDate',          date)
        record.setValue('resultOtherwiseDate', otherwiseDate)
        db.updateRecord(tableTempInvalid, record)


    def checkPersonInSession(self, user_id):
        db = self.db
        tableAppSession = db.table('AppSession')
        cond = [tableAppSession['person_id'].eq(user_id),
                tableAppSession['status'].eq(0),
                ]
        return db.getRecordEx(tableAppSession, cols='*', where=cond)
