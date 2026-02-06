#!/usr/bin/env python
# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import re
from PyQt4 import QtGui
from PyQt4.QtCore import QDir, QObject, QVariant, QXmlStreamReader, pyqtSignature, SIGNAL

from library.database import CDatabase, CDatabaseException
from library.dbfpy.dbf import Dbf
from library.DbfViewDialog import CDbfViewDialog
from library.DbEntityCache import CDbEntityCache
from library.Utils import anyToUnicode, exceptionToUnicode, forceDate, forceInt, forceRef, forceString, forceStringEx, nameCase, toVariant

from Exchange.ImportTariffsXML import getTariffDifference, copyTariff
from Exchange.Export import LoggerMixin
from Exchange.Utils  import check_rus_lat, getId, insertTableDataFromDbf, isNotNull, isNull, logQueryResult, runScript, setSqlVariable, tbl


class Cimport():
    def __init__(self, log=None, edtFile=None, db = None, progressBar = None, btnImport=None, btnClose=None, additionalInit = True):
      # log - желательно, типа QTextEdit или производного от него
        if not hasattr(self, 'edtFileName'):
            self.edtFileName = edtFile
        if not hasattr(self, 'db'):
            self.db = db
        if not self.db:
            self.db = QtGui.qApp.db
        if not hasattr(self, 'log'):
            self.log = log
        if not hasattr(self, 'progressBar'):
            self.progressBar = progressBar
        if self.progressBar:
            self.progressBar.setValue(0)
        if not hasattr(self, 'btnImport'):
            self.btnImport = btnImport
        if not hasattr(self, 'btnClose'):
            self.btnClose = btnClose
        self.n=0
        self.row=None
        self.abort=False
        self.importRun=False
        if self.edtFileName:
            QObject.connect(
                self.edtFileName, SIGNAL('textChanged(QString)'), self.checkName)

        if additionalInit:
            self.additionalInit()

    def additionalInit(self):
        self.my_org_id=forceInt(QtGui.qApp.preferences.appPrefs.get('orgId', None))
        self.lpuOrg={}
        self.infisOrg={}
        self.OGRN_Org={}
        self.mapOKVEDtoUnified = {}
        self.mapINNToId = {}
        self.mapOrganisationNameToId = {}
        self.mapPersonKeyToId = {}
        self.refuseTypeIdCache = {}
        self.np_KLADR={}
        self.ul_KLADR={}
        self.smo_ins={}
        self.tableClient=tbl('Client')
        self.tableClientPolicy=tbl('ClientPolicy')
        self.tableClientIdentification=tbl('ClientIdentification')
        self.tableClientAddress=tbl('ClientAddress')
        self.tableClientAttach=tbl('ClientAttach')
        self.tableOrganisation=tbl('Organisation')
        self.tableOrgStructure=tbl('OrgStructure')
        self.tablePerson=tbl('Person')
        self.tableClientWork=tbl('ClientWork')
        self.tableClientDocument=tbl('ClientDocument')
        self.tableAddress=tbl('Address')
        self.tableAddressHouse=tbl('AddressHouse')
        self.tableKLADR=tbl('kladr.KLADR')
        self.tableSTREET=tbl('kladr.STREET')
        self.tableDOMA=tbl('kladr.DOMA')
        self.tablePayRefuseType = tbl('rbPayRefuseType')


    def checkName(self):
        self.btnImport.setEnabled(self.edtFileName.text()!='')


    # @pyqtSignature('')
    def on_btnClose_clicked(self):
        if self.importRun:
            self.abort=True
        else:
            self.close()


    def err2log(self, e):
        if self.log:
            self.log.append(u'запись %s (id="%s") %s' % (self.n, self.row['ID'], e))


    # @pyqtSignature('')
    def on_btnImport_clicked(self):
        self.btnImport.setEnabled(False)
        self.btnClose.setText(u'Прервать')
        if self.progressBar:
            self.progressBar.setValue(0)
        self.abort=False
        self.importRun=True
        try:
            self.startImport()
        except IOError, e:
            QtGui.qApp.logCurrentException()
            msg=''
            if hasattr(e, 'filename'):
                msg = u'%s:\n[Errno %s] %s' % (e.filename, e.errno, anyToUnicode(e.strerror))
            else:
                msg = u'[Errno %s] %s' % (e.errno, anyToUnicode(e.strerror))
            QtGui.QMessageBox.critical (self,
                u'Произошла ошибка ввода-вывода', msg, QtGui.QMessageBox.Close)
        except Exception, e:
            QtGui.qApp.logCurrentException()
            QtGui.qApp.db.rollback()
            QtGui.QMessageBox.critical (self,
                u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)
            self.abort = True
        if self.progressBar:
            if not self.abort:
                self.progressBar.setValue(self.progressBar.maximum()-1)
            self.progressBar.setFormat(u'прервано' if self.abort else u'готово')
        self.btnImport.setEnabled(True)
        self.btnClose.setText(u'Закрыть')
        self.abort=False
        self.importRun=False


    def getClientId(self, lastNameField, firstNameField, patrNameField, sexField, birthDateField):
        bad=False
        lastName=nameCase(self.row[lastNameField])
        firstName=nameCase(self.row[firstNameField])
        patrName=nameCase(self.row[patrNameField])
        if not (lastName and firstName and patrName):
            bad=True
            self.err2log(u'нет полного Ф?О')
        fio=lastName+firstName+patrName
        if not check_rus_lat(fio):
            bad=True
            self.err2log(u'недопустимое Ф?О')
        sex=self.row[sexField]
        if not sex:
            bad=True
            self.err2log(u'не указан пол')
        else:
            if sex in (u'м', u'М'): sex=1
            if sex in (u'ж', u'Ж'): sex=2
        birthDate=self.row[birthDateField]
        if not birthDate:
            bad=True
            self.err2log(u'не указан день рождения')
        if bad:
            return None
        else:
            clientFields=[
                ('lastName', lastName), ('firstName', firstName), ('patrName', patrName),
                ('sex', sex), ('birthDate', birthDate)]
            return getId(self.tableClient, clientFields)


    def getCodeFromId(self, orgStructureSailId, fieldCode):
        db = QtGui.qApp.db
        if orgStructureSailId:
            dbfFileName = unicode(self.edtFileNameOrgStructure.text())
            if not dbfFileName:
                QtGui.QMessageBox.warning( self,
                                     u'Внимание!',
                                     u'Выберите соответствующий ORGSTRUCTURE файл DBF %s'%(self.edtFileNameOrgStructure.text()),
                                     QtGui.QMessageBox.Cancel,
                                     QtGui.QMessageBox.Cancel)
            else:
                dbfSailOrgStructure = Dbf(dbfFileName, readOnly=True, encoding='cp1251')
                for i, row in enumerate(dbfSailOrgStructure):
                    if orgStructureSailId == forceString(row['ID']):
                        orgStructureSailCode = forceString(row['CODE'])
                        record = db.getRecordEx('OrgStructure', 'id', 'deleted = 0 AND %s = \'%s\''%(fieldCode, orgStructureSailCode))
                        if record:
                            return forceRef(record.value('id'))
        return None


    def getOrgStructureId(self, code, field, orgStructureFields, updateOrgStructure = False, attachOrgStructure = False):
        if updateOrgStructure or attachOrgStructure:
            codeOrgStructure = nameCase(forceString(self.row[code]))
            if updateOrgStructure and attachOrgStructure:
                return getId(self.tableOrgStructure, [(field, codeOrgStructure), ('deleted', 0)], orgStructureFields)
            elif updateOrgStructure:
                return self.getUpdateId(self.tableOrgStructure, [(field, codeOrgStructure), ('deleted', 0)], True, orgStructureFields)
            elif attachOrgStructure:
                return self.getUpdateId(self.tableOrgStructure, [(field, codeOrgStructure), ('deleted', 0)], False, orgStructureFields)
        return None


    def getUpdateId(self, table, fields, updateOrgStructure, fields2=[]):
        db = QtGui.qApp.db
        cond=[]
        for (name, val) in fields:
            if val==None:
                cond.append(table[name].isNull())
            else:
                cond.append(table[name].eq(toVariant(val)))
        record=db.getRecordEx(table, '*', where=cond)
        if record and updateOrgStructure:
            updateRecord = False
            for (name, val) in fields2:
                recVal=record.value(name)
                if (recVal.isNull() or forceString(recVal)=='') and isNotNull(val):
                    record.setValue(name, toVariant(val))
                    updateRecord = True
            if updateRecord:
                db.updateRecord(table, record)
            return forceInt(record.value('id'))
        elif not updateOrgStructure:
            record = table.newRecord()
            for (name, val) in fields+fields2:
                record.setValue(name, toVariant(val))
            return db.insertRecord(table, record)
        return None


    def get_clientPolicy_id(self, client_id, serial, number, insurer_id, policyType_id=None):
        if isNull(serial) or isNull(number):
            self.err2log(u'не указан полис')
            return None
        clientPolicyFields=[('client_id', client_id), ('serial', serial), ('number', number)]
        clientPolicyFields2=[('insurer_id', insurer_id), ('policyType_id', policyType_id)]
        return getId(
            self.tableClientPolicy, clientPolicyFields, clientPolicyFields2)


    def lpuFind(self, lpu):
        if not lpu: return None
        id=self.lpuOrg.get(lpu, None)
        if id: return id
        cond='fullName like \'%'+lpu+'%\' or shortName like \'%'+lpu+'%\''
        OrganisationList=self.db.getIdList(self.tableOrganisation, where=cond)
        if OrganisationList:
            id=OrganisationList[0]
        else:
            lpu1=lpu.replace(' ', '')
            LP=lpu1.replace(u'№', 'N')
            def name_cond(LP):
                return 'REPLACE(fullName, \' \', \'\') like \'%'+LP+'%\' or REPLACE(shortName, \' \', \'\') like \'%'+LP+'%\''
            OrganisationList=self.db.getIdList(self.tableOrganisation, where=name_cond(LP))
            if OrganisationList:
                id=OrganisationList[0]
            else:
                LP=lpu1.replace('N', u'№')
                OrganisationList=self.db.getIdList(self.tableOrganisation, where=name_cond(LP))
                if OrganisationList:
                    id=OrganisationList[0]
        if id: self.lpuOrg[lpu]=id
        return id


    def infis2orgId(self, infis):
        if isNull(infis): return None
        id=self.infisOrg.get(infis, None)
        if id: return id
        obs='CONCAT(\',\', obsoleteInfisCode, \',\')'
        cond='infisCode=\''+infis+'\' or '+obs+' like \'%,'+infis+',%\''
        OrganisationList=self.db.getIdList(self.tableOrganisation, where=cond)
        if OrganisationList:
            id=OrganisationList[0]
        if id: self.infisOrg[infis]=id
        return id

    def infis2org(self, infis):
        id=self.infis2orgId(infis)
        if not id: return None
        cond=[]
        cond.append(self.tableOrganisation['id'].eq(toVariant(id)))
        OrganisationList=self.db.getRecordList(self.tableOrganisation, where=cond)
        if OrganisationList:
            id=OrganisationList[0]
        return id


    def OGRN2orgId(self, OGRN):
        if not OGRN:
            return None
        id=self.OGRN_Org.get(OGRN, 0)
        if id != 0:
            return id
        id = forceRef(self.db.translate('Organisation', 'OGRN', OGRN, 'id'))
        if id:
            self.OGRN_Org[OGRN]=id
        return id


    def unifyOKVED(self, okved):
        result = self.mapOKVEDtoUnified.get(okved, None)
        if not result and okved:
            result = okved.split('-', 1)[0] # до тире
            result = result.replace(' ',  '') # без пробелов
            if result and result[0:1].isdigit():
                result = forceString(QtGui.qApp.db.translate('rbOKVED', 'OKVED', result, 'code'))
            self.mapOKVEDtoUnified[okved] = result
        return result


    def getOrganisationId(self, INN, nameFieldName, name):
        result = None
        if INN:
            result = self.mapINNToId.get(INN, 0)
        if result==0 and name:
            result = self.mapOrganisationNameToId.get(name, 0)
        if result==0:
            if INN:
                result = forceInt(self.db.translate(self.tableOrganisation, 'INN', INN, 'id'))
            if not result and name:
                result = forceInt(self.db.translate(
                    self.tableOrganisation, nameFieldName, name, 'id'))
                if result and INN:
                    self.mapINNToId[INN] = result
                    record = self.tableOrganisation.newRecord(['id', 'INN'])
                    record.setValue('id', toVariant(result))
                    record.setValue('INN', toVariant(INN))
                    self.db.updateRecord(self.tableOrganisation, record)
            if not result:
                record = self.tableOrganisation.newRecord(['INN', nameFieldName])
                record.setValue('INN', toVariant(INN))
                record.setValue(nameFieldName, toVariant(name))
                result = self.db.insertRecord(self.tableOrganisation, record)
            if result:
                if INN:
                    self.mapINNToId[INN] = result
                if name:
                    self.mapOrganisationNameToId[name] = result
        return result


    def get_KLADRCode(self, NAS_P, noCache=False):
        if not NAS_P: return None
        KLADRCode=self.np_KLADR.get(NAS_P, None)
        if KLADRCode is not None:
            return KLADRCode
        (NAME, SOCR)=(None, None)
        cond=[]
        m=re_spb.match(NAS_P)
        if m:
            ns=(None, None)
            pos=m.end()
            if pos>=0:
                ns=obl(NAS_P[pos:])
            if ns==(None, None):
                if len(NAS_P)>pos+2:
                    name=NAS_P[pos+1:].split(',')[0].strip()
                    if name:
                        inf=self.db.translate('kladr.OKATO', 'NAME', name, 'infis')
                        if inf:
                            n=self.db.translate('kladr.KLADR', 'infis', inf, 'NAME')
                            s=self.db.translate('kladr.KLADR', 'infis', inf, 'SOCR')
                            if n and s:
                                ns=(n, s)
            if ns==(None, None):
                (NAME, SOCR)=(u'Санкт-Петербург', u'г')
            else:
                (NAME, SOCR)=ns
                cond.append(self.tableKLADR['parent'].like('78%'))
        else:
            m=re_obl.match(NAS_P)
            if m:
                (NAME, SOCR)=obl(NAS_P[m.end():])
                cond.append(self.tableKLADR['parent'].like('47%'))
            elif re.match(u'^респ[\. ]', NAS_P):
                (NAME, SOCR)=(NAS_P[5:len(NAS_P)].strip(), u'Респ')
            else:
                m=re.match(u'респ\.?$', NAS_P)
                if m:
                    (NAME, SOCR)=(NAS_P[:m.start()].strip(), u'Респ')
        if NAME and SOCR:
            cond.append(self.tableKLADR['NAME'].eq(toVariant(NAME)))
            cond.append(self.tableKLADR['SOCR'].eq(toVariant(SOCR)))
            KLADRRecord=QtGui.qApp.db.getRecordEx(self.tableKLADR, 'CODE', where=cond)
            if KLADRRecord:
                KLADRCode=forceString(KLADRRecord.value('CODE'))
        if not KLADRCode:
            KLADRCode=''
        if not noCache:
            self.np_KLADR[NAS_P]=KLADRCode
        return KLADRCode


    def get_KLADRStreetCode(self, UL, KLADRCode, NAS_P, noCache=False):
        db = QtGui.qApp.db
        if not UL or not KLADRCode:
            return None
        key=(UL, KLADRCode, NAS_P)
        KLADRStreetCode=self.ul_KLADR.get(key, None)
        if KLADRStreetCode is not None:
            return KLADRStreetCode
        (NAME, SOCR)=get_street_ns(UL)
        if NAME and SOCR:
            cond=[]
            cond.append(self.tableSTREET['NAME'].eq(toVariant(NAME)))
            cond.append(self.tableSTREET['SOCR'].eq(toVariant(SOCR)))
            cond.append(self.tableSTREET['CODE'].like(KLADRCode[:11]+'%'))
            STREETList=db.getRecordList(self.tableSTREET, where=cond)
            if STREETList:
                KLADRStreetCode = forceString(STREETList[0].value('CODE'))
            else:
                kladr=forceString(db.translate('kladr.infisSTREET', 'name', NAME, 'KLADR'))
                STREET_SOCR=forceString(db.translate(self.tableSTREET, 'CODE', kladr, 'SOCR'))
                if kladr and STREET_SOCR==SOCR:
                    KLADRStreetCode = kladr
                else:
                    infis=forceString(db.translate('kladr.infisSTREET', 'name', NAME, 'code'))
                    if not infis:
                        cond=[]
                        cond.append(self.tableSTREET['NAME'].like(NAME+'%'))
                        cond.append(self.tableSTREET['SOCR'].eq(toVariant(SOCR)))
                        cond.append(self.tableSTREET['CODE'].like('78%'))
                        STREETList=db.getRecordList(self.tableSTREET, where=cond)
                        if STREETList:
                            infis=forceString(STREETList[0].value('infis'))
                    if not infis:
                        pass
                    if infis:
                        cond=[]
                        cond.append(self.tableSTREET['SOCR'].eq(toVariant(SOCR)))
                        cond.append(self.tableSTREET['CODE'].like(KLADRCode[:11]+'%'))
                        cond.append(self.tableSTREET['infis'].eq(toVariant(infis)))
                        STREETList=QtGui.qApp.db.getRecordList(self.tableSTREET, where=cond)
                        CODE_list=[forceString(x.value('CODE')) for x in STREETList]
                        l=len(STREETList)
                        if not l:
                            pass
                        if l==1:
                            KLADRStreetCode = CODE_list[0]
                        elif l>1 and NAS_P:
                            pos=NAS_P.rfind(',')
                            if pos>=0:
                                if NAS_P[-4:]==u' р-н':
                                    raion=NAS_P[pos+1:-4]
                                else:
                                    raion=NAS_P[pos+1:]
                                OKATO=forceString(QtGui.qApp.db.translate(
                                    'kladr.OKATO', 'NAME', raion.strip(), 'CODE'))
                                if OKATO:
                                    cond=[]
                                    cond.append(self.tableSTREET['OCATD'].like(OKATO+'%'))
                                    STREETList=QtGui.qApp.db.getRecordList(
                                        self.tableSTREET, where=cond)
                                    if len(STREETList)==1:
                                        KLADRStreetCode = forceString(STREETList[0].value('CODE'))
                                    else:
                                        cond=[]
                                        cond.append(self.tableSTREET['SOCR'].eq(toVariant(SOCR)))
                                        cond.append(self.tableSTREET['infis'].eq(toVariant(infis)))
                                        cond.append(
                                            'kladr.STREET.OCATD is null or kladr.STREET.OCATD=\'\'')
                                        STREETList=QtGui.qApp.db.getRecordList(
                                            self.tableSTREET, where=cond)
                                        if STREETList:
                                            CODE_list=[forceString(x.value('CODE')) for x in STREETList]
                                            CODE_like_list=[
                                                'kladr.DOMA.CODE like \''+c[:15]+'%\'' for c in CODE_list]
                                            CODE_cond='('+' or '.join(CODE_like_list)+')'
                                            cond=[]
                                            cond.append(self.tableDOMA['OCATD'].like(OKATO+'%'))
                                            cond.append(CODE_cond)
                                            DOMA_list=QtGui.qApp.db.getRecordList(
                                                self.tableDOMA, where=cond)
                                            if DOMA_list:
                                                KLADRStreetCode = forceString(
                                                    DOMA_list[0].value('CODE'))[:17]
        if not KLADRStreetCode:
            KLADRStreetCode=''
        elif KLADRStreetCode[-2:]!='00':
            fixedCode = KLADRStreetCode[:-2]+'00'
            if db.translate(self.tableSTREET, 'CODE', fixedCode, 'CODE'):
                KLADRStreetCode=fixedCode
        if not noCache:
            self.ul_KLADR[key]=KLADRStreetCode
        return KLADRStreetCode

    def get_insurerId(self, SMO_SHORT_):
        if isNull(SMO_SHORT_):
            return None
        id=self.smo_ins.get(SMO_SHORT_, -1)
        if id != -1:
            return id
        id=None
        cond=[]
        cond.append(self.tableOrganisation['title'].eq(toVariant(SMO_SHORT_)))
        cond.append(self.tableOrganisation['isInsurer'].eq(toVariant(1)))
        insurerList=self.db.getIdList(self.tableOrganisation, where=cond)
        if insurerList!=[]:
            id=insurerList[0]
        if not id:
            cond=[]
            cond.append(self.tableOrganisation['infisCode'].eq(toVariant(SMO_SHORT_)))
            cond.append(self.tableOrganisation['isInsurer'].eq(toVariant(1)))
            insurerList=self.db.getIdList(self.tableOrganisation, where=cond)
            if insurerList!=[]:
                id=insurerList[0]
        self.smo_ins[SMO_SHORT_]=id
        return id


    def clearLog(self):
        if self.log:
            self.log.clear()
            #self.log.model().removeRows(0, self.log.model().rowCount())

    def logQueryResult(self, query):
        u'''Записывает результат выполнения запроса query в лог по строкам'''
        if self.log:
            logQueryResult(self.log, query)

    def setSqlVariable(self, name, value):
        u'''Устанавливает значение переменной в запросе на SQL'''
        setSqlVariable(self.db, name, value)

    def runScript(self, instream,  dict = {}):
        u'''Выполняет последовательность запросов к базе данных self.db, считанную из входного потока instream.
        instream - это произвольный контейнер со строками
        dict - набор пар (имя, значение) для установки переменных в SQL
        '''
        db = self.db if self.db else QtGui.qApp.db
        return runScript(db, self.log, instream, dict)


    def addRefuseTypeId(self, code, name=None, financeId=None):
        u'''Добавляет тип причины отказа в соответствующую таблицу.
        Для использования необходимо вызвать additionalInit()'''

        s = name if name else u'неизвестная причина с кодом "%s"' % code
        record = self.tablePayRefuseType.newRecord()
        record.setValue('code', toVariant(code))
        record.setValue('name ', toVariant(s))
        record.setValue('rerun', toVariant(1))

        if financeId:
            record.setValue('finance_id', toVariant(financeId))

        id = self.db.insertRecord(self.tablePayRefuseType, record)
        self.refuseTypeIdCache[code] = id
        return id


    def getRefuseTypeId(self, code):
        u'''Поиск id типа причины отказа по его коду. Результаты кэшируются.
        Для использования необходимо вызвать additionalInit()'''

        result = self.refuseTypeIdCache.get(code, -1)

        if result == -1:
            result =forceRef(self.db.translate(
                'rbPayRefuseType', 'code', code, 'id'))
            self.refuseTypeIdCache[code] = result

        return result

nt_list=[
    (u'г.', u'г'), (u'гор.', u'г'), (u'город', u'г'),
    (u'п.', u'п'), (u'пос.', u'п'), (u'посёлок', u'п'), (u'поселок', u'п'), (u'ПОС.', u'п'),
    (u'д.', u'д'), (u'дер.', u'д'), (u'деревня', u'д')]

def obl(np):
    for (n, t) in nt_list:
        l=len(n)
        pos=np.find(n)
        if pos>=0:
            pos+=l
            pos2=pos
            for p in range(pos, len(np)):
                if np[p]==',': break
                else: pos2=p
            return (np[pos:pos2+1].strip(), t)
    return (None, None)

re_spb=re.compile(
    u'^((г|Г)(\. | |\.))?(СП(б|Б)|(С|Санкт|САНКТ)-(Петербург|ПЕТЕРБУРГ))')
re_obl=re.compile(u'^(ЛО|Лен(инградская)?( |\.|\. )[Оо]бл(асть)?)[\., ]')

ns_list=[
    (u'улица', u'ул'), (u'ул.', u'ул'), (u'ул', u'ул'), (u'УЛ.', u'ул'), (u'Ул.', u'ул'), (u'.УЛ', u'ул'), (u'УЛ?ЦА', u'ул'), (u'УЛ', u'ул'),
    (u'проспект', u'пр-кт'), (u'пр-кт', u'пр-кт'), (u'пр.', u'пр-кт'),
    (u'ПР.', u'пр-кт'), (u'П.', u'пр-кт'), (u'.ПР', u'пр-кт'),
    (u'переулок', u'пер'), (u'пер.', u'пер'), (u'ПУ.', u'пер'), (u'.ПУ', u'пер'),
    (u'набережная', u'наб'), (u'наб.', u'наб'), (u'Н.', u'наб'), (u'.Н', u'наб'), (u'НАБЕРЕЖНАЯ', u'наб'), (u'НАБ.', u'наб'), (u'НАБ', u'наб'),
    (u'шоссе', u'ш'), (u'ш.', u'ш'), (u'Ш.', u'ш'),  (u'.Ш', u'ш'),
    (u'бульвар', u'б-р'), (u'б-р', u'б-р'), (u'б.', u'б-р'), (u'Б.', u'б-р'), (u'.Б', u'б-р'),
    (u'площадь', u'пл'), (u'пл.', u'пл'),
    (u'аллея', u'аллея'), (u'ал.', u'аллея'), (u'.АЛ', u'аллея'),
    (u'проезд', u'проезд'), (u'пр-д', u'проезд'),
    (u'линия', u'линия'), (u'лин.', u'линия'), (u'.Л', u'линия'), (u'Л?Н?Я', u'линия'),
    (u'ДГ.', u'дор'), (u'дорога', u'дор'),
    (u'остров', u'о'), (u'.О', u'о')]

def get_street_ns(UL):
    UL_len=len(UL)
    for (n, s) in ns_list:
        l=len(n)
        if l>=UL_len:
            continue
        if UL[0:l]==n and (UL[l]==u' ' or n[-1]==u'.'):
            return((UL[l:UL_len].strip(), s))
        if UL[UL_len-l-1:UL_len]==(u' '+n):
            return((UL[0:UL_len-l].strip(), s))
    return (None, None)


# QtGui.qApp.db - база, куда импортировать
# QtGui.qApp.EIS_db - база, откуда импортировать
class CEISimport(Cimport):
    def exec_(self):
        props=QtGui.qApp.preferences.appPrefs
        EIS_dbDatabaseName=forceStringEx(props.get('EIS_databaseName', QVariant()))
        self.edtFileName.setText(EIS_dbDatabaseName)
        EIS_dbServerName=forceStringEx(props.get('EIS_serverName', QVariant()))
        self.edtIP.setText(EIS_dbServerName)
        self.checkName()
        QtGui.QDialog.exec_(self)
        QtGui.qApp.EIS_db.close()
        QtGui.qApp.EIS_db=None

    def checkName(self):
        self.btnImport.setEnabled(self.edtFileName.text()!='' and self.edtIP.text()!='')

    def loadFromEIS(self, msg, table):
        u'''копирует результат запроса msg из ЕИС в таблицу db.table'''
        result = QtGui.qApp.EIS_db.query(msg)
        while result.next():
            QtGui.qApp.db.insertRecord(table, result.record())
        if result.lastError().isValid():
            raise CDatabaseException(CDatabase.errQueryError%result.lastError().text())
            return False
        return result



class CDBFimport(Cimport):
    # @pyqtSignature('')
    def on_btnView_clicked(self):
        fileName = self.edtFileName.text()
        fileNames = re.findall('"(.+?)"', fileName)
        if len(fileNames):
            fileName = fileNames[0]
        fname=unicode(forceStringEx(fileName))
        if fname:
            CDbfViewDialog(self, fileName=fname).exec_()

    def insertTableDataFromDbf(self, tablename, filename, encoding, binaries=[], fields=None, mode=0, errors=0):
        u'''
    Выкачивает данные из DBF и добавляет в таблицу БД
    tablename - имя таблицы БД
    filename - имя файла DBF
    encoding - кодировка, в которой хранится DBF
    binaries - список номеров полей, которые нужно перекодировать из бинарных в целые
    fields - номера полей, которые надо конвертировать (None - все поля). Если номер равен -1, нужно вставить значение по умолчанию.
    mode: 0 - IGNORE,
          1 - REPLACE
    errors: 0 - игнорировать
        1 - завершать работу и возвращать ошибку
    '''
        return insertTableDataFromDbf(self.db, tablename, filename, encoding, binaries, fields, mode, errors)

    def fullTable(self, filename, tablename, binaries, fields=None, mode=0, errors=0):
        self.log.append(u'Заполняется таблица %s из файла %s...'%(tablename, filename))
        QtGui.qApp.processEvents()
        result = self.insertTableDataFromDbf(tablename, unicode(filename), 'ibm866', binaries, fields, mode, errors)
        if errors == 1 and result:
            self.log(result.text())#self.logQueryResult(result)


class CXMLimport(Cimport, LoggerMixin):
    def __init__(self, log=None, edtFile=None, db = None, progressBar = None, btnImport=None, btnClose=None):
        Cimport.__init__(self, log, edtFile, db, progressBar, btnImport, btnClose)
        LoggerMixin.__init__(self)
        self._xmlReader = QXmlStreamReader()

    def readElementText(self):
        return self._xmlReader.readElementText()

    def errorString(self):
        return self._xmlReader.errorString()


    def atEnd(self):
        return self._xmlReader.atEnd()


    def name(self):
        return self._xmlReader.name()


    def setDevice(self,  device):
        return self._xmlReader.setDevice(device)

    def hasError(self):
        return self._xmlReader.hasError() or self.abort


    def raiseError(self,  str):
        self._xmlReader.raiseError(u'[%d:%d] %s' %\
            (self._xmlReader.lineNumber(), self._xmlReader.columnNumber(), str))


    def readNext(self):
        QtGui.qApp.processEvents()
        self._xmlReader.readNext()

        if self.progressBar:
            self.progressBar.setValue(self._xmlReader.device().pos())


    def err2log(self, e):
        if self.log:
            self.log.append(u'[%d:%d] %s' % (self._xmlReader.lineNumber(), \
                                             self._xmlReader.columnNumber(), e))

    def isEndElement(self):
        return self._xmlReader.isEndElement()


    def isStartElement(self):
        return self._xmlReader.isStartElement()


    def readUnknownElement(self, silent=False):
        assert self.isStartElement()

        if not silent:
            self.err2log(u'Неизвестный элемент: '+self.name().toString())

        while (not self.atEnd()):
            self.readNext()

            if (self.isEndElement()):
                break

            if (self.isStartElement()):
                self.readUnknownElement(silent)

            if self.hasError():
                break


    def readGroup(self, groupName, fieldsList, silent=False, subGroupDict=None):
        u'''Чтение группы элементов
            groupName - имя группы
            fieldsList - список полей в группе, не содержащие подгрупп
            silent - подавление вывода сообщений о неизвестных элементах
            subGroupDict - словарь подгрупп. Ключ - имя подгруппы,
                содержание: tuple из двух элементов: список полей подгруппы,
                словарь в элементами

            Возвращается словарь с распознанными элементами.'''
        assert self.isStartElement() and self.name() == groupName
        result = {}

        while (not self.atEnd()):
            self.readNext()

            if self.isEndElement():
                break

            if self.isStartElement():
                name = forceString(self.name().toString())
                if name in fieldsList:
                    result[name] = forceString(self.readElementText())
                elif subGroupDict and name in subGroupDict.keys():
                    (subFields, subDict) = subGroupDict[name]
                    val = self.readGroup(name, subFields, silent, subDict)

                    if result.has_key(name):
                        if isinstance(result[name], list):
                            result[name].append(val)
                        else:
                            result[name] = [result[name], val]
                    else:
                        result[name] = val
                else:
                    self.readUnknownElement(silent)

            if self.hasError():
                break

        return result


    def lookupIdByCodeName(self, code, name, table, cache):
        if code and name:
            key = (code, name)
            id = cache.get(key,  None)

            if id:
                return id

            cond = []
            cond.append(table['code'].eq(toVariant(code)))
            cond.append(table['name'].eq(toVariant(name)))
            record = self.db.getRecordEx(table, ['id'], where=cond)

            if record:
                id = forceRef(record.value('id'))
                cache[key] = id
                return id
        return None


    def readGroupEx(self, groupName, fieldsList, silent=False, subGroupDict=None):
        u'''Чтение группы элементов
            groupName - имя группы
            fieldsList - список полей в группе, не содержащие подгрупп
            silent - подавление вывода сообщений о неизвестных элементах
            subGroupDict - словарь подгрупп. Ключ - имя подгруппы,
                содержание - словарь с полями:
                fields - tuple с именами полей подгруппы
                subgroup - словарь подподгруппы
            Возвращается словарь с распознанными элементами.'''
        assert self.isStartElement() and self.name() == groupName
        result = {}

        while (not self.atEnd()):
            self.readNext()

            if self.isEndElement():
                break

            if self.isStartElement():
                name = forceString(self.name().toString())
                if name in fieldsList:
                    result[name] = forceString(self.readElementText())
                elif subGroupDict and name in subGroupDict.keys():
                    subDict = subGroupDict[name]
                    val = self.readGroupEx(name,
                                          subDict.get('fields', tuple()), silent,
                                          subDict.get('subGroup', {}))

                    if result.has_key(name):
                        if isinstance(result[name], list):
                            result[name].append(val)
                        else:
                            result[name] = [result[name], val]
                    else:
                        result[name] = val
                else:
                    self.readUnknownElement(silent)

            if self.hasError():
                break

        return result


    @pyqtSignature('')
    def on_btnSelectFile_clicked(self):
        fileName = QtGui.QFileDialog.getOpenFileName(
            self, u'Укажите файл с данными', self.edtFileName.text(), u'Файлы XML (*.xml)')
        if fileName != '':
            self.edtFileName.setText(QDir.toNativeSeparators(fileName))
            self.checkName()

# ******************************************************************************

class CImportTariffsMixin():
    u'''Примесевый класс для импорта тарифов'''

    def __init__(self, log, tariffList, tariffExpenseItems):
        self._serviceCache = {}
        self._tariffCategoryIdCache = {}

        self.log = log
        self.tblContract_Tariff = tbl('Contract_Tariff')
        self.tblContract_CompositionExpense = tbl('Contract_CompositionExpense')
        self.tblContract_Coefficient = tbl('Contract_Coefficient')
        self.tblTariffCategory = tbl('rbTariffCategory')
        self.tblService = tbl('rbService')

        self.tariffExpenseItems = list(tariffExpenseItems)

        self.tariffList = map(None, tariffList)
        self.tariffDict = {}

        self.nAdded = 0
        self.nSkipped = 0
        self.nUpdated = 0
        self.dupSkip = True
        self.dupUpdate = False

        for i, tariff in enumerate(self.tariffList):
            key = ( forceInt(tariff.value('tariffType')),
                    forceRef(tariff.value('service_id')),
                    forceInt(tariff.value('sex')),
                    forceString(tariff.value('age')),
                    forceRef(tariff.value('tariffCategory_id'))
                  )
            tariffIndexList = self.tariffDict.setdefault(key, [])
            tariffIndexList.append(i)

        self.findServiceByInfisCode = lambda code: self.findIdByCode(code, 'rbService', self._serviceCache, 'infis')
        self.findTariffCategory = lambda code: self.findIdByCode(code, 'rbTariffCategory', self._tariffCategoryIdCache)


    def addOrUpdateTariff(self, serviceCode, newTariff, newExpenses):
        def _addTariff():
            self.log.append(u'Добавляем тариф для услуги %s' % serviceCode)
            self.nAdded += 1
            self.addTariff(newTariff)
            self.tariffExpenseItems.append(newExpenses)

        tariffType = forceInt(newTariff.value('tariffType'))
        serviceId  = forceRef(newTariff.value('service_id'))
        sex = forceInt(newTariff.value('sex'))
        age = forceString(newTariff.value('age'))
        tariffCategoryId = forceRef(newTariff.value('tariffCategory_id'))

        key = (tariffType, serviceId, sex, age, tariffCategoryId)
        tariffIndexList = self.tariffDict.get(key, None)

        if tariffIndexList:
            self.log.append(u'Найден совпадающий тариф.')

            # проверяем интервалы действия тарифов на пересечение
            for i in tariffIndexList:
                tariff = self.tariffList[i]

                if self.tariffPeriodIntersect(tariff, newTariff):
                    break
            # если не пересекаются - добавляем новый
            else:
                self.log.append(u'Интервал действия тарифа не пересекается с имеющимися.')
                _addTariff()
                return

            if self.dupSkip:
                self.log.append(u'Пропускаем.')
                self.nSkipped += len(tariffIndexList)
                return

            for i in tariffIndexList:
                tariff = self.tariffList[i]
                diffStr = getTariffDifference(tariff, self.tariffExpenseItems[self.tariffList.index(tariff)],
                                                                                                    newTariff,  newExpenses)

                if not diffStr or not self.tariffPeriodIntersect(tariff, newTariff):
                    self.nSkipped += 1
                    break

                if self.dupUpdate:
                    self.log.append(u'Обновляем.')
                    self.tariffExpenseItems[self.tariffList.index(tariff)] = newExpenses
                    copyTariff(tariff, newTariff)
                    self.nUpdated += 1
                else:
                    self.log.append(u'Запрос действий у пользователя.')
                    answer = QtGui.QMessageBox.question(self, u'Совпадающий тариф',
                                        u'Услуга "%s"\nРазличия: %s\n'
                                        u'Обновить?' %(serviceCode, diffStr),
                                        QtGui.QMessageBox.No|QtGui.QMessageBox.Yes,
                                        QtGui.QMessageBox.No)
                    self.log.append(u'Выбор пользователя %s' % \
                    (u'обновить' if answer == QtGui.QMessageBox.Yes else u'пропустить'))
                    if answer == QtGui.QMessageBox.Yes:
                        self.tariffExpenseItems[self.tariffList.index(tariff)] = newExpenses
                        copyTariff(tariff, newTariff)
                        self.nUpdated += 1
                    else:
                        self.nSkipped += 1
        else:
            _addTariff()

    def addTariff(self, newTariff):
        tariffType = forceInt(newTariff.value('tariffType'))
        serviceId  = forceRef(newTariff.value('service_id'))
        sex = forceInt(newTariff.value('sex'))
        age = forceString(newTariff.value('age'))
        category = forceRef(newTariff.value('tariffCategory_id'))

        i = len(self.tariffList)
        self.tariffList.append(newTariff)
        key = (tariffType, serviceId, sex, age, category)
        tariffIndexList = self.tariffDict.setdefault(key, [])
        tariffIndexList.append(i)


    def tariffPeriodIntersect(self, tariff, newTariff):
        oldBegDate = forceDate(tariff.value('begDate'))
        oldEndDate = forceDate(tariff.value('endDate'))
        begDate = forceDate(newTariff.value('begDate'))
        endDate = forceDate(newTariff.value('endDate'))
        result = (((begDate >= oldBegDate and begDate <= oldEndDate) or
                        (endDate >= oldBegDate and endDate <= oldEndDate)) or
                        (begDate < oldBegDate and endDate > oldEndDate))
        return result


    def findIdByCode(self, code, table, cache, codeFieldName = 'code', idFieldName = 'id'):
        result = cache.get(code,  -1)

        if result == -1:
            result = forceRef(QtGui.qApp.db.translate(table, codeFieldName, code, idFieldName))
            cache[code] = result

        return result


    def addTariffCategory(self, code):
        record = self.tblTariffCategory.newRecord()
        record.setValue('code', toVariant(code))
        record.setValue('name', toVariant(u'Тарифная категория с кодом %s' % code))
        id = QtGui.qApp.db.insertRecord(self.tblTariffCategory, record)
        self._tariffCategoryIdCache[code] = id
        return id


    def ensureTariffCategory(self, code):
        id = self.findTariffCategory(code)

        if not id:
            id = self.addTariffCategory(code)

        return id

# ******************************************************************************

class CImportHelperMixin():
    def __init__(self):
        self.__db = QtGui.qApp.db
        self.__tblClientPolicy = tbl('ClientPolicy')


    def addClientPolicy(self, clientId, insurerId, serial, number, begDate,
                        endDate, note=None, policyTypeId=None,
                        policyKindId=None):
        record = self.__tblClientPolicy.newRecord()
        record.setValue('client_id', toVariant(clientId))
        record.setValue('insurer_id', toVariant(insurerId))
        record.setValue('policyType_id', toVariant(policyTypeId))
        record.setValue('policyKind_id', toVariant(policyKindId))
        record.setValue('serial', toVariant(serial))
        record.setValue('number', toVariant(number))
        record.setValue('begDate', toVariant(begDate))
        record.setValue('endDate', toVariant(endDate))
        record.setValue('note',  toVariant(note))
        self.__db.insertRecord(self.__tblClientPolicy, record)


class CPolicyKindRegionalCodeCache(CDbEntityCache):
    mapIdToCode = {}

    @classmethod
    def purge(cls):
        cls.mapIdToCode.clear()


    @classmethod
    def getCode(cls, _id):
        result = cls.mapIdToCode.get(_id, False)
        if result == False:
            cls.connect()
            result = forceString(QtGui.qApp.db.translate('rbPolicyKind', 'id',
                                                         _id, 'regionalCode'))
            cls.mapIdToCode[_id] = result
        return result


class COrganisationInfisCodeCache(CDbEntityCache):
    mapIdToCode = {}

    @classmethod
    def purge(cls):
        cls.mapIdToCode.clear()


    @classmethod
    def getCode(cls, _id):
        result = cls.mapIdToCode.get(_id, False)
        if result == False:
            cls.connect()
            result = forceString(QtGui.qApp.db.translate('Organisation', 'id',
                                                         _id, 'infisCode'))
            cls.mapIdToCode[_id] = result
        return result
