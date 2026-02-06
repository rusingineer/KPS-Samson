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

import urllib

from PyQt4                      import QtGui, QtSql
from PyQt4.QtCore               import Qt, QVariant

from library.DialogBase         import CDialogBase
from library.HttpsConnection    import getConnectionClass
from library.InDocTable         import (
                                        CBoolInDocTableCol,
                                        CDateInDocTableCol,
#                                        CEnumInDocTableCol,
                                        CInDocTableCol,
#                                        CIntInDocTableCol,
#                                        CRBInDocTableCol,
                                        CRecordListModel,
                                       )
from library.MSCAPI             import MSCApi
from library.Utils              import (
                                        forceBool,
#                                        forceDate,
#                                        forceInt,
                                        forceString,
                                        formatBool,
                                        formatSex,
                                        formatSNILS,
                                        withWaitCursor,
                                       )

from Exchange.FSSv2.chainHandler            import CChainHandler
from Exchange.FSSv2.encryptionHandler       import CEncryptionHandler
from Exchange.FSSv2.fixSoapEnvPrefixHandler import CFixSoapEnvPrefixHandler
from Exchange.FSSv2.signatureHandler        import CSignatureHandler
from Exchange.FSSv2.FssSignInfo             import CFssSignInfo

from Exchange.FSSv2.generated.FileOperationsLnService_client import ( FileOperationsLnServiceLocator,
                                                                      GetLNDataRequest,
                                                                      GetLNListBySnilsRequest,
                                                                      DisableLnRequest,
                                                                    )
from Exchange.FSSv2.zsiUtils                import (
                                                     convertTupleToQDate,
                                                     fixu,
                                                     getCryptoNsDict,
                                                   )
from Reports.ReportBase         import CReportBase, createTable
from Reports.ReportView         import CReportViewDialog
from Orgs.Utils                 import getOrganisationInfo

from Ui_TempInvalidPredecessorsSelector import Ui_TempInvalidPredecessorsSelector
from Ui_TempInvalidAnnulmentDialog import Ui_TempInvalidAnnulmentDialog


def searchCase(widget, snils, externalPeriodExists, activeNumbers, prevNumbers, isPeriodsSignature):
    docDescrs = downloadCaseFromFss(snils)
    if docDescrs:
        dlg = CTempInvalidPredecessorsSelector(widget)
        dlg.setIsPeriodsSignature(isPeriodsSignature)
        dlg.setExternalPeriodExists(externalPeriodExists)
        dlg.setActiveNumbers(activeNumbers)
        dlg.setPrevNumbers(prevNumbers)
        for docDescr in docDescrs:
            dlg.appendDoc(docDescr)
        if dlg.exec_():
            return dlg.getCheckedDocs(), dlg.getExternalPeriod()
        else:
            return [], None
    else:
        QtGui.QMessageBox.information(widget,
                                      u'Запрос СФР',
                                      u'В СФР не найдено электронных листков нетрудоспособности для лица со СНИЛС «%s».' % formatSNILS(snils),
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok
                                     )
        return [], None


def showDocumentInfo(widget, snils, number):
    def addRow(table, col, val):
        i = table.addRow()
        table.setText(i, 0, col)
        table.setText(i, 1, val or '')

    docDescr = downloadDocumentFromFss(snils, number)
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
    docState = u'%s %s' % ( docDescr['state'], docStateName.get(docDescr['state'], u'(не известно)') )

    title = u'Сведения о листке нетрудоспособности № %s' % number
    textDoc = QtGui.QTextDocument()
    cursor = QtGui.QTextCursor(textDoc)
    cursor.setCharFormat(CReportBase.ReportTitle)
    cursor.insertText(title)
    cursor.insertBlock()
    cursor.setCharFormat(CReportBase.ReportBody)
    columns = [
            ('40%',[], CReportBase.AlignLeft),
            ('50%',[], CReportBase.AlignLeft),
        ]

    table = createTable(cursor, columns, headerRowCount=0, border=0, cellPadding=2, cellSpacing=0)
    # сведения о ЛН
    addRow(table, u'Листок нетрудоспособности №',   docDescr['number'])
    addRow(table, u'Выдан',   forceString(docDescr['issueDate']))
    addRow(table, u'Выдан в', docDescr['issueOrg'])
    addRow(table, u'Адрес',   docDescr['issueOrgAddress'])
    addRow(table, u'ОГРН',    docDescr['issueOrgOgrn'])
    addRow(table, u'Является продолжением №', docDescr['prevNumber'])
    addRow(table, u'Является первичным',  formatBool(docDescr['isPrimary']))
    addRow(table, u'Является дубликатом', formatBool(docDescr['isDuplicate']))
    addRow(table, u'', u'')
    # сведения о пациенте
    addRow(table, u'Фамилия', docDescr['lastName'])
    addRow(table, u'Имя',     docDescr['firstName'])
    addRow(table, u'Отчество',docDescr['patrName'])
    addRow(table, u'Пол',     formatSex(docDescr['sex']))
    addRow(table, u'Дата рождения', forceString(docDescr['birthDay']))
    addRow(table, u'СНИЛС',         formatSNILS(docDescr['snils']))
#    addRow(table, u'Место работы',  docDescr['workPlace'])
#    addRow(table, u'Основное',      formatBool(docDescr['isMainEmployment']))
#    addRow(table, u'Состоит на учёте в службе занятости',  formatBool(docDescr['isUnemployed']))

#    addRow(table, u'По основному месту работы выдан №',  docDescr['parentNumber'])
    # обстоятельства выдачи
    addRow(table, u'Причина нетрудоспособности', docDescr['reason'])
    addRow(table, u'Доп.код',  docDescr['extraReason'])
#    addRow(table, u'Код изм.', docDescr['changeReason'])
    addRow(table, u'Диагноз',  docDescr['diagnosis'])
    addRow(table, u'Дата 1', forceString(docDescr['date1']))
    addRow(table, u'Дата 2', forceString(docDescr['date2']))
    addRow(table, u'Номер путёвки', forceString(docDescr['voucherNo']))
    addRow(table, u'ОГРН санатория или клиники НИИ', forceString(docDescr['voucherOgrn']))
    if docDescr['serv']:
        for iServ, serv in enumerate(docDescr['serv']):
            addRow(table, u'Уход %d:'%(iServ+1),  '')
            addRow(table, u'- фамилия',           serv['lastName'])
            addRow(table, u'- имя',               serv['firstName'])
            addRow(table, u'- отчество',          serv['patrName'])
            addRow(table, u'- дата рождения',     forceString(serv['birthDay']))
            addRow(table, u'- СНИЛС',             formatSNILS(serv['snils']))
            addRow(table, u'- родственная связь', serv['relationCode'])
            addRow(table, u'- причина нетрудоспособности', serv['reason'])
            addRow(table, u'- диагноз', serv['diagnosis'])
            addRow(table, u'- тип лечения',       serv['treatmentType'])
            addRow(table, u'- дата начала ухода',    forceString(serv['begDate']))
            addRow(table, u'- дата окончания ухода', forceString(serv['endDate']))
    addRow(table, u'Постановка на учет в ранние сроки беременности', formatBool(docDescr['preg12week']) if docDescr['preg12week'] is not None else None)
    addRow(table, u'Находился в стационаре с', forceString(docDescr['begHospDate']))
    addRow(table, u'Находился в стационаре по', forceString(docDescr['endHospDate']))
    addRow(table, u'Код нарушения режима',      docDescr['hospBreachCode'])
    addRow(table, u'Дата нарушения режима',     forceString(docDescr['hospBreachDate']))
    addRow(table, u'Дата направления в бюро МСЭ',  forceString(docDescr['mseDate1']))
    addRow(table, u'Дата регистрации документов в бюро МСЭ',  forceString(docDescr['mseDate2']))
    addRow(table, u'Дата освидетельствования в бюро МСЭ',  forceString(docDescr['mseDate3']))
    addRow(table, u'Установлена/изменена группа инвалидности',  forceString(docDescr['mseInvalidGroup']))
    for period, periodTitle in zip(docDescr['period'], (u'Первый', u'Второй', u'Третий')):
        addRow(table, periodTitle+u' период:', '')
        addRow(table, u'- дата начала освобождения',    forceString(period['begDate']))
        addRow(table, u'- дата окончания освобождения', forceString(period['endDate']))
        addRow(table, u'- должность врача',             forceString(period['doctorPost']))
        addRow(table, u'- ФИО врача',                   forceString(period['doctorName']))
        addRow(table, u'- должность председателя ВК',   forceString(period['chairmanPost']))
        addRow(table, u'- ФИО председателя ВК',         forceString(period['chairmanName']))
    addRow(table, u'Приступить к работе с',             forceString(docDescr['returnDate']))
    addRow(table, u'Иное',                              docDescr['otherCode'])
    addRow(table, u'Дата изменения состояния нетрудоспособного', forceString(docDescr['otherDate']))
    addRow(table, u'Выдан листок нетрудоспособности (продолжение) №', docDescr['nextNumber'])
    addRow(table, u'Состояние листка нетрудоспособности', docState)

    view = CReportViewDialog(widget)
    view.setWindowTitle(title)
    view.setText(textDoc)
    view.exec_()



@withWaitCursor
def downloadCaseFromFss(snils):
    orgId = QtGui.qApp.currentOrgId()
    orgInfo = getOrganisationInfo(orgId)
    ogrn = orgInfo['OGRN']

    api = MSCApi(QtGui.qApp.getCsp())
    cert = QtGui.qApp.getOrgCertOptionalOgrn(api)
    docDescrs = []
    with cert.provider() as master:
        assert master # silence pyflakes
        bodyId, actorUri = CFssSignInfo.getMoElementIdAndActorUri(ogrn)
        port = _getPort(api, actorUri, bodyId)
        if port:
            numbers = _getNumbers(port, ogrn, snils)
            for number in numbers:
                docDescr = _getLNData(port, ogrn, snils, number)
                docDescr['startDate'] = docDescr['begDate']
                prevNumber = docDescr['prevNumber']
                while prevNumber:
                    try:
                        prevDocDescr = _getLNData(port, ogrn, snils, prevNumber)
                    except Exception as ex:
                        if ex.message == u'ЭЛН с номером: %s, СНИЛС: %s - отсутствует в БД' % (prevNumber, snils):
                            break
                        raise ex
                    docDescr['startDate'] = min(docDescr['startDate'], prevDocDescr['begDate'])
                    prevNumber = prevDocDescr['prevNumber']
                docDescrs.append(docDescr)
    return docDescrs


@withWaitCursor
def downloadDocumentFromFss(snils, number):
    orgId = QtGui.qApp.currentOrgId()
    orgInfo = getOrganisationInfo(orgId)
    ogrn = orgInfo['OGRN']
    api = MSCApi(QtGui.qApp.getCsp())
    cert = QtGui.qApp.getOrgCertOptionalOgrn(api)
    with cert.provider() as master:
        assert master # silence pyflakes
        bodyId, actorUri = CFssSignInfo.getMoElementIdAndActorUri(ogrn)
        port = _getPort(api, actorUri, bodyId)
        if port:
            docDescr = _getLNData(port, ogrn, snils, number)
            return docDescr
    return None


def _getCurrentUserMchd():
    db = QtGui.qApp.db
    tablePersonIdentification = db.table('Person_Identification')
    tableAccountingSystem = db.table('rbAccountingSystem')
    query = db.innerJoin(tablePersonIdentification, tableAccountingSystem, tableAccountingSystem['id'].eq(tablePersonIdentification['system_id']))
    cond = [
        tablePersonIdentification['master_id'].eq(QtGui.qApp.userId),
        tablePersonIdentification['deleted'].eq(0),
        tablePersonIdentification['value'].ne(''),
        tableAccountingSystem['code'].eq('MCHD_SFR')
    ]
    record = db.getRecordEx(query, cols=tablePersonIdentification['value'], where=cond, order='Person_Identification.id desc')
    return forceString(record.value('value')) if record else None


def _getOrgCertAndMchd(api):
    mchd = None
    orgCert = QtGui.qApp.getOrgCertOptionalOgrn(api)
    if not orgCert.ogrn():
        mchd = _getCurrentUserMchd()
        if not mchd:
            raise Exception(u'Для отправки данных необходимо наличие подписи организации или машиночитаемой доверенности')
    return (orgCert, mchd)


def _getPort(api, actorUri, bodyId):
    qApp = QtGui.qApp
    useEncryption = qApp.getFssUseEncryption()
    serviceUrl = qApp.getFssServiceUrl()
    if type(serviceUrl) is list:
        serviceUrl = serviceUrl[0]
    orgCert, mchd = _getOrgCertAndMchd(api)

    #        log = sys.stdout

    locator = FileOperationsLnServiceLocator()
    port    = locator.getFileOperationsLnPort(serviceUrl,
                                              nsdict    = getCryptoNsDict(),
                                              transport=getConnectionClass(serviceUrl),
                                              transdict = { 'proxy': qApp.getFssProxyPreferences()
                                                          }
                                             )
    handler = CChainHandler()
    handler.append( CFixSoapEnvPrefixHandler() )

    handler.append( CSignatureHandler(api,
                                      userCert=orgCert,
                                      actorUri=actorUri,
                                      signBody=True,
                                      signElementId=bodyId,
                                      mchd=mchd
                                     )
                  )
    
    if useEncryption:
        fssCert = qApp.getFssCert(api)
        handler.append( CEncryptionHandler(api,
                                           userCert=orgCert,
                                           receiverCert=fssCert,
                                          )
                      )

    port.binding.sig_handler = handler
    return port



def _decodeError(response):
    message = fixu(response.Mess)
    if (     response.Info
         and response.Info.InfoRowset
         and response.Info.InfoRowset.InfoRow
       ):
        for infoRow in response.Info.InfoRowset.InfoRow:
            if (     infoRow
                 and infoRow.Errors
                 and infoRow.Errors.Error
               ):
                for error in infoRow.Errors.Error:
                    if error:
                        errCode = fixu(error.ErrCode)
                        errMess = fixu(error.ErrMess)
                        message += '\n%s: %s' % (errCode, errMess)
    return message


def _getNumbers(port, ogrn, snils):
    request = GetLNListBySnilsRequest()
    request.Ogrn   = ogrn
    request.Snils  = snils

    response = port.GetLNListBySnils(request)
#    out = response.FileOperationsLnUserGetLNListBySnilsOut
    if not response.Status:
        raise Exception(_decodeError(response))
        # raise Exception(fixu(response.Mess))

    if (    response.Data
        and response.Data.OutRowsetLNListbySnils
        and response.Data.OutRowsetLNListbySnils.RowLNbySnils
       ) :

        return [ fixu(row.LnCode,)
                 for row in response.Data.OutRowsetLNListbySnils.RowLNbySnils
                 if row.LnState in ('010', '020')
               ]
    else:
        return []


def _getLNData(port, ogrn, snils, number):
    request = GetLNDataRequest()
    request.Ogrn   = ogrn
    request.LnCode = number
    request.Snils  = snils
    response = port.GetLNData(request)
#    out = response.FileOperationsLnUserGetLNDataOut
    if not response.Status:
        # raise Exception(fixu(response.Mess))
        raise Exception(_decodeError(response))
    document = response.Data.OutRowset.ResponseRow
    result = {
               'number'           : fixu(document.LnCode),
               'issueDate'        : convertTupleToQDate(document.LnDate),
               'issueOrg'         : fixu(document.LpuName),
               'issueOrgAddress'  : fixu(document.LpuAddress),
               'issueOrgOgrn'     : fixu(document.LpuOgrn),
               'prevNumber'       : fixu(document.PrevLnCode),
               'isPrimary'        : document.PrimaryFlag,
               'isDuplicate'      : document.DuplicateFlag,

               'lastName'         : fixu(document.Surname),
               'firstName'        : fixu(document.Name),
               'patrName'         : fixu(document.Patronymic),
               'sex'              : document.Gender+1,
               'birthDay'         : convertTupleToQDate(document.Birthday),
               'snils'            : fixu(document.Snils),

               'reason'           : fixu(document.Reason1),
               'extraReason'      : fixu(document.Reason2),
#               'changeReason'     : fixu(document.REASON3),
               'diagnosis'        : fixu(document.Diagnos),
               'date1'            : convertTupleToQDate(document.Date1),
               'date2'            : convertTupleToQDate(document.Date2),
               'voucherNo'        : fixu(document.VoucherNo),
               'voucherOgrn'      : fixu(document.VoucherOgrn),
               'serv'             : [ {
                                        'lastName'     : fixu(serv.Surname),
                                        'firstName'    : fixu(serv.Name),
                                        'patrName'     : fixu(serv.Patronymic),
                                        'birthDay'     : convertTupleToQDate(serv.Birthday),
                                        'snils'        : fixu(serv.Snils),
                                        'relationCode' : fixu(serv.ServRelationCode),
                                        'reason'       : fixu(serv.Reason1),
                                        'diagnosis'    : fixu(serv.Diagnosis),
                                        'treatmentType': fixu(serv.TreatmentType),
                                        'begDate'      : convertTupleToQDate(serv.ServDt1),
                                        'endDate'      : convertTupleToQDate(serv.ServDt2),
                                      }
                                      for serv in document.ServData.ServFullData
                                    ] if document.ServData and document.ServData.ServFullData
                                      else [],
               'preg12week'       : document.Pregn12wFlag,
               #
               'begHospDate'      : convertTupleToQDate(document.HospitalDt1),
               'endHospDate'      : convertTupleToQDate(document.HospitalDt2),

               'hospBreachCode'   : fixu(document.HospitalBreach.HospitalBreachCode) if document.HospitalBreach else None,
               'hospBreachDate'   : convertTupleToQDate(document.HospitalBreach.HospitalBreachDt) if document.HospitalBreach else None,
               'mseDate1'         : convertTupleToQDate(document.MseDt1),
               'mseDate2'         : convertTupleToQDate(document.MseDt2),
               'mseDate3'         : convertTupleToQDate(document.MseDt3),
               'mseInvalidGroup'  : document.MseInvalidGroup,

               'period'           : [ { 'begDate'   : convertTupleToQDate(fullPeriod.TreatPeriod.TreatDt1),
                                        'endDate'   : convertTupleToQDate(fullPeriod.TreatPeriod.TreatDt2),
                                        'doctorPost': fixu(fullPeriod.TreatPeriod.TreatDoctorRole),
                                        'doctorName': fixu(fullPeriod.TreatPeriod.TreatDoctor),
                                        'chairmanPost': fixu(fullPeriod.TreatChairmanRole),
                                        'chairmanName': fixu(fullPeriod.TreatChairman),
                                      }
                                      for fullPeriod in document.TreatPeriods.TreatFullPeriod
                                    ],
               'returnDate'       : convertTupleToQDate(document.LnResult.ReturnDateLpu) if document.LnResult else None,
               'otherCode'        : fixu(document.LnResult.MseResult) if document.LnResult else None,
               'otherDate'        : convertTupleToQDate(document.LnResult.OtherStateDt) if document.LnResult else None,
               'nextNumber'       : fixu(document.LnResult.NextLnCode) if document.LnResult else None,

               'state'            : fixu(document.LnState),
               'begDate'          : convertTupleToQDate(document.TreatPeriods.TreatFullPeriod[0].TreatPeriod.TreatDt1),
               'endDate'          : convertTupleToQDate(document.TreatPeriods.TreatFullPeriod[-1].TreatPeriod.TreatDt2),
             }
    if result['serv'] and not result['reason']:
        result['reason'] = '09'
#    print number, result
    return result


def _disableLn(port, ogrn, snils, number, reasonCode, reasonText):
    request = DisableLnRequest()
    request.Ogrn   = ogrn
    request.Snils  = snils
    request.LnCode = number
    request.ReasonCode = reasonCode
    request.Reason = reasonText

    response = port.DisableLn(request)
#    out = response.FileOperationsLnUserDisableLnOut
    if not response.Status:
        raise Exception( _decodeError(response) )
    return True


class CTempInvalidPredecessorsSelector(Ui_TempInvalidPredecessorsSelector, CDialogBase):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.addModels('Predecessors', CTempInvalidPredecessorsModel(self))
        self.setupUi(self)
#        self.setWindowTitle(u'')
        self.tblPredecessors.setModel(self.modelPredecessors)
        self.edtBegExternalPeriod.canBeEmpty(True)
        self.edtBegExternalPeriod.setReadOnly(True)
        self.edtBegExternalPeriod.setDate(None)
        self.edtEndExternalPeriod.canBeEmpty(True)
        self.edtEndExternalPeriod.setReadOnly(True)
        self.edtEndExternalPeriod.setDate(None)

        self.externalPeriodExists = False
        self.activeNumbers = set()
        self.prevNumbers = set()
        self.isPeriodsSignature = False


    def setIsPeriodsSignature(self, isPeriodsSignature):
        self.isPeriodsSignature = isPeriodsSignature
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(not isPeriodsSignature)


    def setExternalPeriodExists(self, externalPeriodExists):
        self.externalPeriodExists = externalPeriodExists


    def setActiveNumbers(self, activeNumbers):
        self.activeNumbers = activeNumbers


    def setPrevNumbers(self, prevNumbers):
        self.prevNumbers = prevNumbers


    def appendDoc(self, docDescr):
        number = docDescr['number']

        record = self.modelPredecessors.getEmptyRecord()
        record.setValue('add', True if number not in self.activeNumbers and number not in self.prevNumbers else None)
        record.setValue('number',      number)
        record.setValue('issueDate',   docDescr['issueDate'])
        record.setValue('issueOrg',    docDescr['issueOrg'])
        record.setValue('begDate',     docDescr['begDate'])
        record.setValue('endDate',     docDescr['endDate'])
        record.setValue('reason',      docDescr['reason'])
        record.setValue('extraReason', docDescr['extraReason'])
        record.setValue('diagnosis',   docDescr['diagnosis'])
        record.docDescr = docDescr

        notes = []
        if number in self.activeNumbers:
            notes.append(u'Листок учтён')
        elif number in self.prevNumbers:
            notes.append(u'Листок учтён как предыдущий')

        record.setValue('note', ', '.join(notes))
        self.modelPredecessors.addRecord(record)
        begExternalPeriod = docDescr['startDate']
        endExternalPeriod = docDescr['endDate']
        self.edtBegExternalPeriod.setDate(min(self.edtBegExternalPeriod.date() or begExternalPeriod, begExternalPeriod))
        self.edtEndExternalPeriod.setDate(max(self.edtEndExternalPeriod.date() or endExternalPeriod, begExternalPeriod))
        self.chkExternalPeriod.setChecked(not self.externalPeriodExists)


    def getCheckedDocs(self):
        result = []
        for record in self.modelPredecessors.items():
            if forceBool(record.value('add')):
                docDescr = record.docDescr
                result.append(docDescr)
        return result


    def getExternalPeriod(self):
        if self.chkExternalPeriod.isChecked():
            return self.edtBegExternalPeriod.date(), self.edtEndExternalPeriod.date()
        else:
            return None


class CTempInvalidPredecessorsModel(CRecordListModel):
    def __init__(self,  parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CBoolInDocTableCol(u'Добавить',    'add', 6))
        self.addCol(CInDocTableCol(    u'Номер',       'number', 12)).setReadOnly()
        self.addCol(CDateInDocTableCol(u'Выдан',       'issueDate', 6)).setReadOnly()
        self.addCol(CInDocTableCol(    u'Выдан в',     'issueOrg', 6)).setReadOnly()
        self.addCol(CDateInDocTableCol(u'C',           'begDate', 6)).setReadOnly()
        self.addCol(CDateInDocTableCol(u'По',          'endDate', 6)).setReadOnly()
        self.addCol(CInDocTableCol(    u'Причина',     'reason',   6)).setReadOnly()
        self.addCol(CInDocTableCol(    u'Диагноз',     'diagnosis',6)).setReadOnly()
        self.addCol(CInDocTableCol(u'Примечание',  'note',    6)).setReadOnly()


    def cellReadOnly(self, index):
        return self.data(index, Qt.EditRole).isNull()


    def getEmptyRecord(self):
        result = QtSql.QSqlRecord()
        result.append(QtSql.QSqlField('add',           QVariant.Bool))
        result.append(QtSql.QSqlField('number',        QVariant.String))
        result.append(QtSql.QSqlField('issueDate',     QVariant.Date))
        result.append(QtSql.QSqlField('issueOrg',      QVariant.String))
        result.append(QtSql.QSqlField('begDate',       QVariant.Date))
        result.append(QtSql.QSqlField('endDate',       QVariant.Date))
        result.append(QtSql.QSqlField('reason',        QVariant.String))
        result.append(QtSql.QSqlField('extraReason',   QVariant.String))
        result.append(QtSql.QSqlField('diagnosis',     QVariant.String))
        result.append(QtSql.QSqlField('note',          QVariant.String))
#        result.append(QtSql.QSqlField('docDescr',      QVariant.String))
        return result


def annulment(widget, snils, number):
    dlg = CTempInvalidAnnulmentDialog(widget)
    if dlg.exec_():
        annulmentReasonId = dlg.getAnnulmentReasonId()
        if annulmentReasonId:
            if doAnnlument(snils, number, annulmentReasonId):
                return annulmentReasonId
    return None


@withWaitCursor
def doAnnlument(snils, number, reasonId):
    db = QtGui.qApp.db

    orgId = QtGui.qApp.currentOrgId()
    orgInfo = getOrganisationInfo(orgId)
    ogrn = orgInfo['OGRN']

    table = db.table('rbTempInvalidAnnulmentReason')
    reasonCode = forceString(db.translate(table, 'id', reasonId, 'code'))
    reasonText = forceString(db.translate(table, 'id', reasonId, 'name'))

    api = MSCApi(QtGui.qApp.getCsp())
    cert = QtGui.qApp.getOrgCertOptionalOgrn(api)
    with cert.provider() as master:
        assert master # silence pyflakes
        bodyId, actorUri = CFssSignInfo.getMoElementIdAndActorUri(ogrn)
        port = _getPort(api, actorUri, bodyId)
        if port:
            return _disableLn(port, ogrn, snils, number, reasonCode, reasonText)
    return None


class CTempInvalidAnnulmentDialog(Ui_TempInvalidAnnulmentDialog, CDialogBase):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.cmbAnnulmentReason.setTable('rbTempInvalidAnnulmentReason')


    def getAnnulmentReasonId(self):
        return self.cmbAnnulmentReason.value()
