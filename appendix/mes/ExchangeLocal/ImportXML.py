# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2015 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

u"""Импорт тарифа из XML"""
from itertools import izip_longest

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QXmlStreamReader, Qt, QString

from ExportXML import mesSimpleFields, mesRefFields, mesRefTableNames, \
    mesKeyFields, exportVersion, mesVisitSimpleFields, mesVisitRefFields, \
    mesVisitRefTableNames, mesServiceSimpleFields, mesServiceRefFields, \
    mesServiceRefTableNames, mesLimitationSimpleFields, mesMKBSimpleFields
from Ui_ImportXML import Ui_ImportXML
from library.Utils import forceString, forceBool, toVariant, forceStringEx, forceRef, variantEq, forceDouble, forceInt, \
    anyToUnicode, trim
from library.crbcombobox import CRBModelDataCache


def ImportXML(widget):
    appPrefs = QtGui.qApp.preferences.appPrefs

    fileName = forceString(appPrefs.get('ImportMesXMLFileName', ''))
    fullLog = forceBool(appPrefs.get('ImportMesXMLFullLog', ''))
    updateMes = forceBool(appPrefs.get('ImportMesXMLUpdateMes'))
    dlg = CImportMesXML(fileName, widget)
    dlg.chkFullLog.setChecked(fullLog)
    dlg.exec_()
    appPrefs['ImportMesXMLFileName'] = toVariant(dlg.fileName)
    appPrefs['ImportMesXMLFullLog'] = toVariant(dlg.chkFullLog.isChecked())
    appPrefs['ImportMesXMLUpdateMes'] = toVariant(dlg.chkUpdateMes.isChecked())


class CMyXmlStreamReader(QXmlStreamReader):
    def __init__(self, parent, showLog, updateMes):
        QXmlStreamReader.__init__(self)
        self._parent = parent
        self.db = QtGui.qApp.db
        self.table = self.db.table('MES')
        self.tableMesVisit = self.db.table('MES_visit')
        self.tableMesService = self.db.table('MES_service')
        self.tableService = self.db.table('mrbService')
        self.tableMesGroup = self.db.table('mrbMESGroup')
        self.tableVisitType = self.db.table('mrbVisitType')
        self.tableSpeciality = self.db.table('mrbSpeciality')
        self.tableLimitation = self.db.table('MES_limitedBySexAge')
        self.tableMKB = self.db.table('MES_mkb')
        self.showLog = showLog
        self.updateMes = updateMes
        self.refValueCache = {}
        self.mapKeyToRecord = {}

        for record in self.db.getRecordList(self.table, where=self.table['deleted'].eq(0)):
            self.addMesToMap(record)
        for field, tableName in zip(mesRefFields + mesVisitRefFields + mesServiceRefFields,
                                    mesRefTableNames + mesVisitRefTableNames + mesServiceRefTableNames):
            self.refValueCache[field] = CRBModelDataCache.reset(tableName)
        for field, tableName in zip(mesRefFields + mesVisitRefFields + mesServiceRefFields,
                                    mesRefTableNames + mesVisitRefTableNames + mesServiceRefTableNames):
            self.refValueCache[field] = CRBModelDataCache.getData(tableName, True)

        self.skip = False
        self.nadded = 0
        self.ncoincident = 0
        self.nprocessed = 0
        self.nupdated = 0
        self.nskipped = 0


    def getMesKey(self, record):
        return tuple([ forceStringEx(record.value(fieldName)) if not record.value(fieldName).isNull() else None for fieldName in mesKeyFields ])


    def getMesDescr(self, record):
        parts = []
        for fieldName in mesKeyFields:
            if fieldName in self.refValueCache:
                value = forceRef(record.value(fieldName))
                if value:
                    value = forceString(self.refValueCache[fieldName].getNameById(value))
            else:
                value = forceString(record.value(fieldName))
            if value:
                parts.append(fieldName+' = '+value)
        return ', '.join([part for part in parts if part])


    def getMesDifference(self, oldRecord, newRecord, oldVisits, newVisits,
                         oldServices, newServices, limitations,
                            oldLimitations, mkb, oldMKB):
        parts = []

        for fieldName in mesSimpleFields + mesRefFields:
            if fieldName not in mesKeyFields:
                oldValue = oldRecord.value(fieldName)
                newValue = newRecord.value(fieldName)
                if not variantEq(oldValue, newValue):
                    parts.append(u'%s было %s стало %s' % (fieldName,
                                                           forceString(oldValue),
                                                           forceString(newValue)))

        # проверяем изменения в визитах
        visits1 = [(d.value('groupCode'), \
                              d.value('serviceCode'), \
                              d.value('additionalServiceCode'), \
                              d.value('averageQnt'), \
                              d.value('sex'),  \
                              d.value('begAgeUnit'), \
                              d.value('minimumAge'), \
                              d.value('endAgeUnit'), \
                              d.value('maximumAge'), \
                              d.value('controlPeriod')) for d in newVisits]

        visits2 = [(d.value('groupCode'), \
                              d.value('serviceCode'), \
                              d.value('additionalServiceCode'), \
                              d.value('averageQnt'), \
                              d.value('sex'),  \
                              d.value('begAgeUnit'), \
                              d.value('minimumAge'), \
                              d.value('endAgeUnit'), \
                              d.value('maximumAge'), \
                              d.value('controlPeriod')) for d in oldVisits]

        visitsDiffList = izip_longest(visits1, visits2)
        for visitDiff in visitsDiffList:
            if not visitDiff[1]:
                parts.append(u'новый визит %s. '%visitDiff[0][3])
            elif not visitDiff[0]:
                parts.append(u'удален визит %s. '%visitDiff[1][3])
            elif visitDiff[0] != visitDiff[1]:
                parts.append(u'визит: было "%s %s %s %.2f" стало "%s %s %s %.2f"' % (
                    forceString(visitDiff[1][0]),
                    forceString(visitDiff[1][1]),
                    forceString(visitDiff[1][2]),
                    forceDouble(visitDiff[1][3]),
                    forceString(visitDiff[0][0]),
                    forceString(visitDiff[0][1]),
                    forceString(visitDiff[0][2]),
                    forceDouble(visitDiff[0][3])
                    ))

#        # проверяем изменения в визитах
#        for oldX in  oldVisits:
#            for newX in newVisits:
#                if (forceRef(newX.value('visitType_id')) == forceRef(oldX.value('visitType_id'))) and\
#                    (forceRef(newX.value('speciality_id')) == forceRef(oldX.value('speciality_id'))) and \
#                        (not variantEq(newX.value('groupCode'), oldX.value('groupCode')) or \
#                         not variantEq(newX.value('serviceCode'), oldX.value('serviceCode')) or \
#                         not variantEq(newX.value('additionalServiceCode'), oldX.value('additionalServiceCode')) or \
#                         not variantEq(newX.value('averageQnt'), oldX.value('averageQnt')) or \
#                         not variantEq(newX.value('sex'), oldX.value('sex')) or \
#                         not variantEq(newX.value('begAgeUnit'), oldX.value('begAgeUnit')) or \
#                         not variantEq(newX.value('minimumAge'), oldX.value('minimumAge')) or \
#                         not variantEq(newX.value('endAgeUnit'), oldX.value('endAgeUnit')) or \
#                         not variantEq(newX.value('maximumAge'), oldX.value('maximumAge')) or \
#                         not variantEq(newX.value('controlPeriod'), oldX.value('controlPeriod'))
#                                                                         ):
#                    parts.append(u'визит тип=%d услуга=%d было "%s %s %s %.2f" стало "%s %s %s %.2f"' % (
#                        forceRef(newX.value('visitType_id')), forceRef(newX.value('speciality_id')),
#                        forceString(oldX.value('groupCode')),
#                        forceString(oldX.value('serviceCode')),
#                        forceString(oldX.value('additionalServiceCode')),
#                        forceInt(oldX.value('averageQnt')),
#                        forceString(newX.value('groupCode')),
#                        forceString(newX.value('serviceCode')),
#                        forceString(newX.value('additionalServiceCode')),
#                        forceInt(newX.value('averageQnt'))
#                        ))
#
#        # проверяем появление удалённых визитов
#        for oldX in  oldVisits:
#            flag = False
#
#            for newX in newVisits:
#                if (forceRef(newX.value('visitType_id')) == forceRef(oldX.value('visitType_id'))) and\
#                    (forceRef(newX.value('speciality_id')) == forceRef(oldX.value('speciality_id'))):
#                    flag = True
#                    break
#
#            if not flag:
#                    parts.append(u'удален визит тип=%d услуга=%d' % (
#                        forceInt(oldX.value('visitType_id')),
#                        forceInt(oldX.value('speciality_id'))
#                    ))
#
#        # проверяем появление новых визитов
#        for newX in newVisits:
#            flag = False
#
#            for oldX in oldVisits:
#                if (forceRef(newX.value('visitType_id')) == forceRef(oldX.value('visitType_id'))) and\
#                    (forceRef(newX.value('speciality_id')) == forceRef(oldX.value('speciality_id'))):
#                    flag = True
#                    break
#
#            if not flag:
#                    parts.append(u'новый визит id=%d %d' % (
#                        forceInt(newX.value('visitType_id')),
#                        forceInt(newX.value('speciality_id'))
#                        ))

        # проверяем изменения в услугах
        services1 = [(d.value('service_id'), \
                              d.value('groupCode'), \
                              d.value('necessity'), \
                              d.value('averageQnt'), \
                              d.value('binding'), \
                              d.value('sex'),  \
                              d.value('begAgeUnit'), \
                              d.value('minimumAge'), \
                              d.value('endAgeUnit'), \
                              d.value('maximumAge'), \
                              d.value('controlPeriod')) for d in newServices]

        services2 = [(d.value('service_id'), \
                              d.value('groupCode'), \
                              d.value('necessity'), \
                              d.value('averageQnt'), \
                              d.value('binding'), \
                              d.value('sex'),  \
                              d.value('begAgeUnit'), \
                              d.value('minimumAge'), \
                              d.value('endAgeUnit'), \
                              d.value('maximumAge'), \
                              d.value('controlPeriod')) for d in oldServices]

        servicesDiffList = izip_longest(services1, services2)
        for serviceDiff in servicesDiffList:
            if not serviceDiff[1]:
                parts.append(u'новая услуга %s. '%serviceDiff[0][0])
            elif not serviceDiff[0]:
                parts.append(u'удалена услуга %s. '%serviceDiff[1][0])
            elif serviceDiff[0] != serviceDiff[1]:
                parts.append(u'услуга: было "%d %d %.2f %d" стало "%d %d %.2f %d"' % (
                    #forceRef(newX.value('service_id')),
                    forceInt(serviceDiff[1][0]),
                    forceInt(serviceDiff[1][2]),
                    forceDouble(serviceDiff[1][1]),
                    forceInt(serviceDiff[1][3]),
                    forceInt(serviceDiff[0][0]),
                    forceInt(serviceDiff[0][2]),
                    forceDouble(serviceDiff[0][1]),
                    forceInt(serviceDiff[0][3])
                    ))

#        for oldX in oldServices:
#            for newX in newServices:
#                if (forceRef(newX.value('service_id')) == forceRef(oldX.value('service_id'))) and \
#                        (not variantEq(newX.value('groupCode'), oldX.value('groupCode')) or \
#                         not variantEq(newX.value('necessity'), oldX.value('necessity')) or \
#                         not variantEq(newX.value('averageQnt'), oldX.value('averageQnt')) or \
#                         not variantEq(newX.value('binding'), oldX.value('binding')) or \
#                         not variantEq(newX.value('sex'), oldX.value('sex')) or \
#                         not variantEq(newX.value('begAgeUnit'), oldX.value('begAgeUnit')) or \
#                         not variantEq(newX.value('minimumAge'), oldX.value('minimumAge')) or \
#                         not variantEq(newX.value('endAgeUnit'), oldX.value('endAgeUnit')) or \
#                         not variantEq(newX.value('maximumAge'), oldX.value('maximumAge')) or \
#                         not variantEq(newX.value('controlPeriod'), oldX.value('controlPeriod'))
#                                                                         ):
#                    parts.append(u'услуга тип=%d было "%d %d %.2f %d" стало "%d %d %.2f %d"' % (
#                        forceRef(newX.value('service_id')),
#                        forceInt(oldX.value('groupCode')),
#                        forceInt(oldX.value('averageQnt')),
#                        forceDouble(oldX.value('necessity')),
#                        forceInt(oldX.value('binding')),
#                        forceInt(newX.value('groupCode')),
#                        forceInt(newX.value('averageQnt')),
#                        forceDouble(newX.value('necessity')),
#                        forceInt(newX.value('binding'))
#                        ))
#
#        # проверяем появление удалённых услуг
#        for oldX in oldServices:
#            flag = False
#
#            for newX in newServices:
#                if forceRef(newX.value('service_id')) == forceRef(oldX.value('service_id')):
#                    flag = True
#                    break
#
#            if not flag:
#                    parts.append(u'удалена услуга тип=%d' %
#                        forceInt(oldX.value('service_id'))
#                    )
#
#        # проверяем появление новых услуг
#        for newX in newServices:
#            flag = False
#
#            for oldX in oldServices:
#                if forceRef(newX.value('service_id')) == forceRef(oldX.value('service_id')):
#                    flag = True
#                    break
#
#            if not flag:
#                    parts.append(u'новая услуга тип=%d' %
#                        forceInt(newX.value('service_id'))
#                        )
#
#        # проверяем изменения в органичениях
#        for oldX in oldLimitations:
#            for newX in limitations:
#                if (not variantEq(newX.value('sex'), oldX.value('sex')) or \
#                         not variantEq(newX.value('begAgeUnit'), oldX.value('begAgeUnit')) or \
#                         not variantEq(newX.value('minimumAge'), oldX.value('minimumAge')) or \
#                         not variantEq(newX.value('endAgeUnit'), oldX.value('endAgeUnit')) or \
#                         not variantEq(newX.value('maximumAge'), oldX.value('maximumAge')) or \
#                         not variantEq(newX.value('controlPeriod'), oldX.value('controlPeriod'))
#                                                                         ):
#                    parts.append(u'ограничение было "%s %i %s %i %s %i" стало "%s %i %s %i %s %i"' % (
#                        formatSex(oldX.value('sex')),
#                        forceInt(oldX.value('begAgeUnit')),
#                        forceString(oldX.value('minimumAge')),
#                        forceInt(oldX.value('endAgeUnit')),
#                        forceString(oldX.value('maximumAge')),
#                        forceInt(oldX.value('controlPeriod')),
#                        formatSex(newX.value('sex')),
#                        forceInt(newX.value('begAgeUnit')),
#                        forceString(newX.value('minimumAge')),
#                        forceInt(newX.value('endAgeUnit')),
#                        forceString(newX.value('maximumAge')),
#                        forceInt(newX.value('controlPeriod'))
#                        ))

#        # проверяем изменения в МКБ
#        for oldX in oldMKB:
#            for newX in mkb:
#                if (not variantEq(newX.value('mkb'), oldX.value('mkb')) ):
#                    parts.append(u'мкб было "%s" стало "%s"' % (
#                        forceString(oldX.value('mkb')),
#                        forceString(newX.value('mkb'))
#                        ))
#
#        # проверяем появление удалённых mkb
#        for oldX in  oldMKB:
#            flag = False
#
#            for newX in mkb:
#                if (forceString(newX.value('mkb')) == forceString(oldX.value('mkb'))):
#                    flag = True
#                    break
#
#            if not flag:
#                    parts.append(u'удален диагноз %s' % (
#                        forceString(oldX.value('mkb'))
#                    ))
#
#        # проверяем появление новых мкб
#        for newX in mkb:
#            flag = False
#
#            for oldX in oldMKB:
#                if (forceString(newX.value('mkb')) == forceString(oldX.value('mkb'))):
#                    flag = True
#                    break
#
#            if not flag:
#                    parts.append(u'новый диагноз %s' % (
#                        forceString(newX.value('mkb'))
#                        ))

        mkb1 = [forceString(d.value('mkb')) for d in mkb]
        mkb2 = [forceString(d.value('mkb')) for d in oldMKB]
        mkbDiffList = izip_longest(mkb1, mkb2)
        for mkbDiff in mkbDiffList:
            if not mkbDiff[1]:
                parts.append(u'новый диагноз %s. '%mkbDiff[0])
            elif not mkbDiff[0]:
                parts.append(u'удалён диагноз %s. '%mkbDiff[1])
            elif mkbDiff[0] != mkbDiff[1]:
                parts.append(u'диагноз: был %s, стал %s'%(mkbDiff[1], mkbDiff[0]))

        return ', '.join(parts)


    def copyMes(self, oldRecord, newRecord):
        for fieldName in mesSimpleFields+mesRefFields:
            if fieldName not in mesKeyFields:
                oldRecord.setValue(fieldName, newRecord.value(fieldName))


    def addMesToMap(self, record):
        key = self.getMesKey(record)
        self.mapKeyToRecord.setdefault(key, record)


    def raiseError(self, str):
        QXmlStreamReader.raiseError(self, u'[%d:%d] %s' % (self.lineNumber(), self.columnNumber(), str))


    def readNext(self):
        QXmlStreamReader.readNext(self)
        self._parent.progressBar.setValue(self.device().pos())


    def log(self, str, forceLog = False,  red = None):
        if self.showLog or forceLog:
            if red:
                color = self._parent.logBrowser.textColor()
                self._parent.logBrowser.setTextColor( Qt.red )
                self._parent.logBrowser.append(str)
                self._parent.logBrowser.setTextColor( color )
            else:
                self._parent.logBrowser.append(str)
            self._parent.logBrowser.update()


    def readFile(self, device):
        self.setDevice(device)
        try:
            while (not self.atEnd()):
                self.readNext()

                if self.isStartElement():
                    if self.name() == 'MesExport':
                        if self.attributes().value('version') == exportVersion:
                            self.readData()
                        else:
                            self.raiseError(u'Версия формата "%s" не поддерживается. Должна быть "%s"' \
                                % (self.attributes().value('version').toString(), exportVersion))
                    else:
                        self.raiseError(u'Неверный формат экспорта данных.')

                if self.hasError() or self._parent.aborted:
                    return False

        except IOError, e:
            QtGui.qApp.logCurrentException()
            msg=''
            if hasattr(e, 'filename'):
                msg = u'%s:\n[Errno %s] %s' % (e.filename, e.errno, anyToUnicode(e.strerror))
            else:
                msg = u'[Errno %s] %s' % (e.errno, anyToUnicode(e.strerror))
            QtGui.QMessageBox.critical (self._parent,
                u'Произошла ошибка ввода-вывода', msg, QtGui.QMessageBox.Close)
            self.log(u'! Ошибка ввода-вывода: %s' % msg, True)
            return False
        except Exception, e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical (self._parent,
                u'Произошла ошибка', unicode(e), QtGui.QMessageBox.Close)
            self.log(u'! Ошибка: %s' % unicode(e), True)
            return False
        return not (self.hasError() or self._parent.aborted)


    def readData(self):
        assert self.isStartElement() and self.name() == 'MesExport'
        while (not self.atEnd()):
            self.readNext()
            if self.isEndElement():
                break
            if self.isStartElement():
                if (self.name() == 'MesElement'):
                    self.readMesElement()
                else:
                    self.readUnknownElement()
            if self.hasError() or self._parent.aborted:
                break


    def readMesElement(self):
        assert self.isStartElement() and self.name() == 'MesElement'
        newRecord = self.table.newRecord()
        services = []
        visits = []
        limitations = []
        mkb = []

        for fieldName in mesSimpleFields:
            value = toVariant(self.attributes().value(fieldName).toString())
            value.convert(newRecord.field(fieldName).type())
            newRecord.setValue(fieldName, value)

        while not self.atEnd():
            self.readNext()
            QtGui.qApp.processEvents()
            if self.isEndElement():
                break
            if self.isStartElement():
                name = self.name().toString()
                if name == 'group':
                    newRecord.setValue(name+'_id', toVariant(self.readGroup()))
                elif name == 'MesService':
                    services.append(self.readMesService())
                elif name == 'MesVisit':
                    visits.append(self.readMesVisit())
                elif name == 'MesLimitation':
                    limitations.append(self.readMesLimitations())
                elif name == 'MesMKB':
                    mkb.append(self.readMesMKB())
                else:
                    self.readUnknownElement()

        self.log(u'МЭС %s' % self.getMesDescr(newRecord))

        if self.skip:
            self.log(u'Информация по МЭС не полная. Пропускаем.',  True,  True)
            self.nskipped += 1
            self.skip = False
        else:

            if self.hasError() or self._parent.aborted:
                return None

            key = self.getMesKey(newRecord)
            record = self.mapKeyToRecord.get(key, None)
            if record:
                if self.updateMes:
                    oldId = forceRef(record.value('id'))

                    cond = [self.tableMesVisit['deleted'].eq(0),
                            self.tableMesVisit['master_id'].eq(oldId)]
                    oldVisits = self.db.getRecordList(self.tableMesVisit, where=cond)

                    cond = [self.tableMesService['deleted'].eq(0),
                            self.tableMesService['master_id'].eq(oldId)]
                    oldServices = self.db.getRecordList(self.tableMesService, where=cond)

                    cond = [self.tableLimitation['deleted'].eq(0),
                            self.tableLimitation['master_id'].eq(oldId)]
                    oldLimitations = self.db.getRecordList(self.tableLimitation, where=cond)

                    cond = [self.tableMKB['deleted'].eq(0),
                            self.tableMKB['master_id'].eq(oldId)]
                    oldMKB = self.db.getRecordList(self.tableMKB, where=cond)

                    diff = self.getMesDifference(record, newRecord, visits, oldVisits, services, oldServices, limitations,
                            oldLimitations, mkb, oldMKB)
                    if diff:
                        self.log(u'* Существующий МЭС %s отличается и будет обновлён' % self.getMesDescr(record),  True)
                        self.log(u': Различия: %s' % diff)
                        self.copyMes(record, newRecord)
                        self.db.updateRecord(self.table, record)

                        for x in oldVisits:
                            x.setValue('deleted', toVariant(4))
                            self.db.updateRecord(self.tableMesVisit, x)

                        for x in oldServices:
                            x.setValue('deleted', toVariant(4))
                            self.db.updateRecord(self.tableMesService, x)

                        for x in oldLimitations:
                            x.setValue('deleted', toVariant(4))
                            self.db.updateRecord(self.tableLimitation, x)

                        for x in oldMKB:
                            x.setValue('deleted', toVariant(4))
                            self.db.updateRecord(self.tableMKB, x)

                        for x in visits:
                            x.setValue('master_id', toVariant(oldId))
                            self.db.insertRecord(self.tableMesVisit, x)

                        for x in services:
                            x.setValue('master_id', toVariant(oldId))
                            self.db.insertRecord(self.tableMesService, x)

                        for x in limitations:
                            x.setValue('master_id', toVariant(oldId))
                            self.db.insertRecord(self.tableLimitation, x)

                        for x in mkb:
                            x.setValue('master_id', toVariant(oldId))
                            self.db.insertRecord(self.tableMKB, x)

                        self.nupdated += 1
                    else:
                        self.log(u'* Изменений не обнаружено')
                        self.ncoincident += 1
                else:
                    self.log(u'%% Найдена совпадающая запись, пропускаем')
                    self.ncoincident += 1
            else:
                self.log(u'% Сходные записи не обнаружены, добавляем')
                newId = self.db.insertRecord(self.table, newRecord)
                self.addMesToMap(newRecord)

                for x in visits:
                    x.setValue('master_id', toVariant(newId))
                    self.db.insertRecord(self.tableMesVisit, x)

                for x in services:
                    x.setValue('master_id', toVariant(newId))
                    self.db.insertRecord(self.tableMesService, x)

                for x in limitations:
                    x.setValue('master_id', toVariant(newId))
                    self.db.insertRecord(self.tableLimitation, x)

                for x in mkb:
                    x.setValue('master_id', toVariant(newId))
                    self.db.insertRecord(self.tableMKB, x)

                self.nadded += 1

        self.nprocessed += 1
        self._parent.lblStatus.setText(
                u'импорт МЭС: %d добавлено; %d обновлено; %d совпадений; %d неполных; %d обработано;' % (self.nadded,
                self.nupdated, self.ncoincident, self.nskipped, self.nprocessed))


    def readMesVisit(self):
        assert self.isStartElement() and self.name() == 'MesVisit'
        newRecord = self.tableMesVisit.newRecord()

        for fieldName in mesVisitSimpleFields:
            value = toVariant(self.attributes().value(fieldName).toString())
            value.convert(newRecord.field(fieldName).type())
            newRecord.setValue(fieldName, value)

        while not self.atEnd():
            self.readNext()
            QtGui.qApp.processEvents()
            if self.isEndElement():
                break
            if self.isStartElement():
                name = self.name().toString()
                if name == 'visitType':
                    newRecord.setValue(name+'_id', toVariant(self.readVisitType()))
                elif name == 'speciality':
                    newRecord.setValue(name+'_id', toVariant(self.readSpeciality()))
                else:
                    self.readUnknownElement()

        return newRecord


    def readMesService(self):
        assert self.isStartElement() and self.name() == 'MesService'
        newRecord = self.tableMesService.newRecord()

        for fieldName in mesServiceSimpleFields:
            value = toVariant(self.attributes().value(fieldName).toString())
            value.convert(newRecord.field(fieldName).type())
            newRecord.setValue(fieldName, value)

        while not self.atEnd():
            self.readNext()
            QtGui.qApp.processEvents()
            if self.isEndElement():
                break
            if self.isStartElement():
                name = self.name().toString()
                if name == 'service':
                    newRecord.setValue(name+'_id', toVariant(self.readService()))
                else:
                    self.readUnknownElement()

        return newRecord


    def readMesLimitations(self):
        assert self.isStartElement() and self.name() == 'MesLimitation'
        newRecord = self.tableLimitation.newRecord()

        for fieldName in mesLimitationSimpleFields:
            value = toVariant(self.attributes().value(fieldName).toString())
            value.convert(newRecord.field(fieldName).type())
            newRecord.setValue(fieldName, value)

        while not self.atEnd():
            self.readNext()
            QtGui.qApp.processEvents()
            if self.isEndElement():
                break

        return newRecord


    def readMesMKB(self):
        assert self.isStartElement() and self.name() == 'MesMKB'
        newRecord = self.tableMKB.newRecord()

        for fieldName in mesMKBSimpleFields:
            value = toVariant(self.attributes().value(fieldName).toString())
            value.convert(newRecord.field(fieldName).type())
            newRecord.setValue(fieldName, value)

        while not self.atEnd():
            self.readNext()
            QtGui.qApp.processEvents()
            if self.isEndElement():
                break

        return newRecord


    def readRefElement(self):
        code = forceString(self.attributes().value('code').toString())
        name = forceString(self.attributes().value('name').toString())
        while not self.atEnd():
            self.readNext()
            QtGui.qApp.processEvents()
            if self.isEndElement():
                break
            if self.isStartElement():
                self.readUnknownElement()
        return code, name


    def readSubElement(self, elementName, table, logStr):
        assert self.isStartElement() and self.name() == elementName
        code, name = self.readRefElement()
        if code or name:
            self.log(u'%s (%s) "%s"'%(logStr, code, name))
        return self.lookupOrAddItem(code, name, elementName+'_id', table, logStr)


    def readUnknownElement(self):
        assert self.isStartElement()
        self.log(u'Неизвестный элемент: '+self.name().toString())
        while (not self.atEnd()):
            self.readNext()
            if (self.isEndElement()):
                break
            if (self.isStartElement()):
                self.readUnknownElement()
            if self.hasError() or self._parent.aborted:
                break


    def readGroup(self):
        return self.readSubElement('group', self.tableMesGroup, u'Группа МЭС')


    def readService(self):
        return self.readSubElement('service', self.tableService,  u'Услуга')


    def readSpeciality(self):
        return self.readSubElement('speciality', self.tableSpeciality, u'Специальность')


    def readVisitType(self):
        return self.readSubElement('visitType', self.tableVisitType, u'Тип визита')


    def lookupIdByCodeName(self, code, name, fieldName, searchByName = False):
        cache = self.refValueCache[fieldName]
        index = cache.getIndexByCode(code)
        if index>=0 and ( searchByName or trim(cache.getName(index)) == trim(name) ):
            return cache.getId(index)
        index = cache.getIndexByName(name)
        if index>=0 and cache.getCode(index) == code:
            return cache.getId(index)
        return None


    def addRefItem(self, code, name,  table,  fieldName, tableName):
        record = table.newRecord()
        record.setValue('code', toVariant(code))
        record.setValue('name', toVariant(name))
        id = self.db.insertRecord(table, record)
        cache = self.refValueCache[fieldName]
        cache.addItem(id, code, name)
        self.log(u'%s (%s) "%s" не найден(а), добавлен(а). (id=%d)' % (tableName, code, name, id),  True)
        return id


    def lookupOrAddItem(self, code, name, idName, table, logStr):
        if code and name:
            return self.lookupIdByCodeName(code, name, idName) or \
                self.addRefItem(code, name, table, idName, logStr)
        return None


class CImportMesXML(QtGui.QDialog, Ui_ImportXML):
    def __init__(self, fileName, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.progressBar.reset()
        self.progressBar.setValue(0)
        self.fileName = fileName
        self.aborted = False
        self.connect(self, QtCore.SIGNAL('import()'), self.import_, Qt.QueuedConnection)
        self.connect(self, QtCore.SIGNAL('rejected()'), self.abort)
        if fileName:
            self.edtFileName.setText(fileName)
            self.btnImport.setEnabled(True)


    def abort(self):
        self.aborted = True


    def import_(self):
        self.aborted = False
        self.btnAbort.setEnabled(True)
        success, result = QtGui.qApp.call(self, self.doImport)
        if self.aborted or not success:
            self.progressBar.setText(u'Прервано')
        self.btnAbort.setEnabled(False)


    @QtCore.pyqtSignature('')
    def on_btnSelectFile_clicked(self):
        self.fileName = QtGui.QFileDialog.getOpenFileName(
            self, u'Укажите файл с данными', self.edtFileName.text(), u'Файлы XML (*.xml)')
        if self.fileName:
            self.edtFileName.setText(self.fileName)
            self.btnImport.setEnabled(True)


    @QtCore.pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()


    @QtCore.pyqtSignature('')
    def on_btnAbort_clicked(self):
        self.abort()


    @QtCore.pyqtSignature('')
    def on_btnImport_clicked(self):
        self.emit(QtCore.SIGNAL('import()'))


    @QtCore.pyqtSignature('QString')
    def on_edtFileName_textChanged(self):
        self.fileName = self.edtFileName.text()
        self.btnImport.setEnabled(self.fileName != '')


    def doImport(self):
        fileName = self.edtFileName.text()
        if not fileName:
            return
        inFile = QtCore.QFile(fileName)
        if not inFile.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
            QtGui.QMessageBox.warning(self, u'Импорт МЭС',
                                      QString(u'Не могу открыть файл для чтения %1:\n%2.')
                                      .arg(fileName)
                                      .arg(inFile.errorString()))
            return

        self.progressBar.reset()
        self.progressBar.setValue(0)
        self.progressBar.setFormat(u'%v байт')
        self.lblStatus.setText('')
        self.progressBar.setMaximum(max(inFile.size(), 1))
        xmlStreamReader = CMyXmlStreamReader(self,
                                             self.chkFullLog.isChecked(),
                                             self.chkUpdateMes.isChecked())

        self.btnImport.setEnabled(False)
        if (xmlStreamReader.readFile(inFile)):
            self.progressBar.setText(u'Готово')
        else:
            self.progressBar.setText(u'Прервано')
            if self.aborted:
                self.logBrowser.append(u'! Прервано пользователем.')
            else:
                self.logBrowser.append(u'! Ошибка: файл %s, %s' % (fileName, xmlStreamReader.errorString()))
        self.edtFileName.setEnabled(False)
        self.btnSelectFile.setEnabled(False)

