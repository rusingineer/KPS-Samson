# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import QEvent, QVariant, SIGNAL

from library.Utils           import trim
from library.Utils           import forceRef, forceDate

from Orgs.OrgComboBox        import COrgComboBox
from Orgs.Orgs               import selectOrganisation
from Orgs.Utils              import getOrganisationInfisAndShortName,  COrgInfo


from ActionPropertyValueType import CActionPropertyValueType


class COrganisationActionPropertyValueType(CActionPropertyValueType):
    name        = 'Organisation'
    variantType = QVariant.Int
    badDomain   = u'Неверное описание области определения значения свойства действия типа Organisation:\n%(domain)s'
    badKey      = u'Недопустимый ключ "%(key)s" в описание области определения значения свойства действия типа Organisation:\n%(domain)s'
    badValue    = u'Недопустимое значение "%(val)s" ключа "%(key)s" в описание области определения значения свойства действия типа Organisation:\n%(domain)s'

    class CPropEditor(QtGui.QWidget):
        __pyqtSignals__ = ('editingFinished()',
                           'commit()',
                          )


        def __init__(self, action, domain, parent, clientId, eventTypeId):
            QtGui.QWidget.__init__(self, parent)
            self.boxlayout = QtGui.QHBoxLayout(self)
            self.boxlayout.setMargin(0)
            self.boxlayout.setSpacing(0)
            self.boxlayout.setObjectName('boxlayout')
            self.cmbOrganisation = COrgComboBox(self)
            self.cmbOrganisation.setNameField("concat_ws(' | ', infisCode, shortName)")
            self.cmbOrganisation.setObjectName('cmbOrganisation')

            db = QtGui.qApp.db
            isDirection = False
            if u'isDirection' in domain:
                domainAND = domain.split('AND')
                domainTrim = []
                for domainI in domainAND:
                    domainTrim.append(trim(domainI))
                domain = db.joinAnd(domainTrim.remove(u'(isDirection)'))
                isDirection = True
            filterList = [domain] if domain else []
            self.boxlayout.addWidget(self.cmbOrganisation)
            self.btnSelect = QtGui.QPushButton(self)
            self.btnSelect.setObjectName('btnSelect')
#            self.btnSelect.setText(u'…')
            self.btnSelect.setText(u'...')
            self.btnSelect.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Ignored)
            self.btnSelect.setFixedWidth(20)
            self.boxlayout.addWidget(self.btnSelect)
            self.setFocusProxy(self.cmbOrganisation)
            self.connect(self.btnSelect, SIGNAL('clicked()'), self.on_btnSelect_clicked)
            self.cmbOrganisation.installEventFilter(self)
            self.btnSelect.installEventFilter(self)
            self.action = action
            if not isDirection and self.action and self.action.actionType() and self.action.actionType().flatCode in (u'consultationDirection', u'researchDirection'):
                if u'Профиль' in self.action._actionType._propertiesByName:
                    propertyValue = self.action[u'Профиль']
                    propertiesByName = self.action.getPropertiesByName()
                    property = propertiesByName[u'Профиль']
                    propertyType = property.type()
                    typeName = propertyType.typeName
                    tableOrganisation = db.table('Organisation')
                    record = self.action.getRecord()
                    directionDate = forceDate(record.value('directionDate')) if record else None
                    if typeName == u'Профиль МП':
                        tableOMAP = db.table('Organisation_MedicalAidProfile')
                        cond = [tableOrganisation['deleted'].eq(0)]
                        if propertyValue:
                            cond.append(tableOMAP['medicalAidProfile_id'].eq(propertyValue))
                        if directionDate:
                            cond.append(
                                db.joinOr([tableOMAP['begDate'].isNull(), tableOMAP['begDate'].dateLe(directionDate)]))
                            cond.append(
                                db.joinOr([tableOMAP['endDate'].isNull(), tableOMAP['endDate'].dateGe(directionDate)]))
                        queryTable = tableOrganisation.innerJoin(tableOMAP,
                                                                 tableOMAP['master_id'].eq(tableOrganisation['id']))
                        idList = db.getDistinctIdList(queryTable, [tableOrganisation['id']], cond)
                        filterList.append(tableOrganisation['id'].inlist(idList))
                    if typeName == u'rbHospitalBedProfile':
                        tableOHBP = db.table('Organisation_HospitalBedProfile')
                        cond = [tableOrganisation['deleted'].eq(0)]
                        if propertyValue:
                            cond.append(tableOHBP['hospitalBedProfile_id'].eq(propertyValue))
                        else:
                            cond.append(tableOHBP['hospitalBedProfile_id'].isNotNull())
                        if directionDate:
                            cond.append(db.joinOr([tableOHBP['begDate'].isNull(), tableOHBP['begDate'].dateLe(directionDate)]))
                            cond.append(db.joinOr([tableOHBP['endDate'].isNull(), tableOHBP['endDate'].dateGe(directionDate)]))
                        queryTable = tableOrganisation.innerJoin(tableOHBP, tableOHBP['master_id'].eq(tableOrganisation['id']))
                        idList = db.getDistinctIdList(queryTable, [tableOrganisation['id']], cond)
                        filterList.append(tableOrganisation['id'].inlist(idList))
                    elif  typeName == u'rbSpeciality':
                        tableOSP = db.table('Organisation_Speciality')
                        cond = [tableOrganisation['deleted'].eq(0)]
                        if propertyValue:
                            cond.append(tableOSP['speciality_id'].eq(propertyValue))
                        else:
                            cond.append(tableOSP['speciality_id'].isNotNull())
                        if directionDate:
                            cond.append(db.joinOr([tableOSP['begDate'].isNull(), tableOSP['begDate'].dateLe(directionDate)]))
                            cond.append(db.joinOr([tableOSP['endDate'].isNull(), tableOSP['endDate'].dateGe(directionDate)]))
                        queryTable = tableOrganisation.innerJoin(tableOSP, tableOSP['master_id'].eq(tableOrganisation['id']))
                        idList = db.getDistinctIdList(queryTable, [tableOrganisation['id']], cond)
                        filterList.append(tableOrganisation['id'].inlist(idList))
                if u'Услуга' in self.action._actionType._propertiesByName:
                    propertyValue = self.action[u'Услуга']
                    propertiesByName = self.action.getPropertiesByName()
                    property = propertiesByName[u'Услуга']
                    propertyType = property.type()
                    typeName = propertyType.typeName
                    tableOrganisation = db.table('Organisation')
                    record = self.action.getRecord()
                    directionDate = forceDate(record.value('directionDate')) if record else None
                    if  typeName == u'rbService':
                        tableOSRV = db.table('Organisation_Service')
                        cond = [tableOrganisation['deleted'].eq(0)]
                        if propertyValue:
                            cond.append(tableOSRV['service_id'].eq(propertyValue))
                        else:
                            cond.append(tableOSRV['service_id'].isNotNull())
                        if directionDate:
                            cond.append(db.joinOr([tableOSRV['begDate'].isNull(), tableOSRV['begDate'].dateLe(directionDate)]))
                            cond.append(db.joinOr([tableOSRV['endDate'].isNull(), tableOSRV['endDate'].dateGe(directionDate)]))
                        queryTable = tableOrganisation.innerJoin(tableOSRV, tableOSRV['master_id'].eq(tableOrganisation['id']))
                        idList = db.getDistinctIdList(queryTable, [tableOrganisation['id']], cond)
                        filterList.append(tableOrganisation['id'].inlist(idList))
            self.cmbOrganisation.setFilter(db.joinAnd(filterList))


        def eventFilter(self, widget, event):
            et = event.type()
            if et == QEvent.FocusOut:
                fw = QtGui.qApp.focusWidget()
                while fw and fw != self:
                    fw = fw.parentWidget()
                if not fw:
                    self.emit(SIGNAL('editingFinished()'))
            elif et == QEvent.Hide and widget == self.cmbOrganisation:
                self.emit(SIGNAL('commit()'))
            return QtGui.QWidget.eventFilter(self, widget, event)


        def on_btnSelect_clicked(self):
            sqlFilter = self.cmbOrganisation.filter()
            hospitalBedProfileId = None
            if 'isMedical' in sqlFilter:
                try:
                    hospitalBedProfileId = self.action[u'Профиль']
                except:
                    pass
            orgId = selectOrganisation(self, self.cmbOrganisation.value(), False, self.cmbOrganisation.filter(), hospitalBedProfileId)
            self.cmbOrganisation.updateModel()
            if orgId:
                self.cmbOrganisation.setValue(orgId)


        def setValue(self, value):
            self.cmbOrganisation.setValue(forceRef(value))


        def value(self):
            return self.cmbOrganisation.value()


    def __init__(self, domain = None):
        CActionPropertyValueType.__init__(self, domain)
        self.rawDomain = domain
        self.domain = self.parseDomain(domain)


    def parseDomain(self, domain):
        isInsurer = None
        isHospital = None
        isMed = None
        isDirection = None
        isFilterName = None
        isSMP = None
        isSanatorium = None
        netCodes = []
        infisCodes = []
        for word in domain.split(','):
            if word:
                parts = word.split(':')
                if len(parts) == 1:
                    key, val = u'тип', parts[0].strip()
                elif len(parts) == 2:
                    key, val = parts[0].strip(), parts[1].strip()
                else:
                    raise ValueError, self.badDomain % locals()
                keylower = key.lower()
                vallower = val.lower()
                if keylower == u'тип':
                    if vallower == u'смо':
                        isInsurer = True
                    elif vallower in (u'стац', u'стационар'):
                        isHospital = True
                    elif vallower == u'лпу':
                        isMed = True
                    elif vallower in (u'напр', u'направитель'):
                        isDirection = True
                    elif vallower == u'смп':
                        isSMP = True
                    elif vallower == u'санаторий':
                        isSanatorium = True
                    else:
                        raise ValueError, self.badValue % locals()
                elif keylower == u'сеть':
                    netCodes.append(val)
                elif keylower == u'инфис':
                    infisCodes.extend(vallower.split(';'))

#                elif keylower == u'профиль-койки':
#                    if val.startswith('@'):
#                        pass
#                    else:
#
                elif keylower == u'имя':
                    if vallower:
                        isFilterName = vallower
                    else:
                        raise ValueError, self.badValue % locals()
                else:
                    raise ValueError, self.badKey % locals()
        db = QtGui.qApp.db
        table = db.table('Organisation')
        cond = []
        cond.append('deleted = 0')
        if isDirection:
            cond.append('isDirection')
        if isInsurer:
            cond.append('isInsurer')
        if isHospital:
            cond.append('isMedical= 2 ')
        if isMed:
            cond.append('isMedical != 0')
        if isSMP:
            cond.append('isMedical = 4')
        if isSanatorium:
            cond.append('isMedical = 5')
        if isFilterName:
            cond.append(table['fullName'].contain(isFilterName))
        if netCodes:
            tableNet = db.table('rbNet')
            contNet = [tableNet['code'].inlist(netCodes), tableNet['name'].inlist(netCodes)]
            netIdList = db.getIdList(tableNet, 'id', db.joinOr(contNet))
            cond.append(table['net_id'].inlist(netIdList))
        if infisCodes:
            cond.append(table['infisCode'].inlist(infisCodes))
        return db.joinAnd(cond)


    @staticmethod
    def convertDBValueToPyValue(value):
        return forceRef(value)


    convertQVariantToPyValue = convertDBValueToPyValue


    def toText(self, v):
        return getOrganisationInfisAndShortName(forceRef(v))


    def toInfo(self, context, v):
        return context.getInstance(COrgInfo, forceRef(v))
