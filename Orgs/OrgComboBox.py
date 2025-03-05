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

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, QModelIndex, QVariant, SIGNAL

from library.DbComboBox import CAbstractDbComboBox, CAbstractDbModel, CDbComboBox, CDbData
from library.InDocTable import CInDocTableCol
from library.Utils import forceRef, forceString, quote, toVariant

from Accounting.Tariff import CTariff

from Utils import getOrganisationInfo, getOrganisationInfisAndShortName
from COrgComboBoxPopupEx import COrgComboBoxPopupEx
from OrgComboBoxPopup import COrgComboBoxPopup
from InsurerComboBoxPopup import CInsurerComboBoxPopup


class COrgComboBox(CDbComboBox):
    def __init__(self, parent):
        CDbComboBox.__init__(self, parent)
        self.setNameField('shortName')
        self.setAddNone(True)
        self.setFilter('deleted = 0')
        self.setTable('Organisation')


class COrgComboBoxEx(CDbComboBox):
    def __init__(self, parent):
        CDbComboBox.__init__(self, parent)
        self.setNameField('CONCAT(infisCode, \'| \', shortName)')
        self.setAddNone(True)
        self.setFilter('Organisation.deleted = 0')
        self.setTable('Organisation')
        self.globalFilter = 'Organisation.deleted = 0'
        self._popup = None
        self.isMedical = 0
        self.isMedicalOrg = False


    def setGlobalFilter(self, filter):
        self.globalFilter = filter


    def _createPopup(self):
        if not self._popup:
            self._popup = COrgComboBoxPopup(self)
            self.connect(self._popup, SIGNAL('itemSelected(int)'), self.setValue)


    def showPopup(self):
        if not self.isReadOnly():
            self.__searchString = ''
            self._createPopup()
            pos = self.rect().bottomLeft()
            pos = self.mapToGlobal(pos)
            size = self._popup.sizeHint()
            screen = QtGui.QApplication.desktop().availableGeometry(pos)
            size.setWidth(screen.width())
            pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
            pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
            self._popup.move(pos)
            self._popup.resize(size)
            self._popup.setGlobalFilter(self.globalFilter)
            self._popup.setIsMedical(self.isMedical)
            self._popup.setIsMedicalOrg(self.isMedicalOrg)
            self._popup.show()


    def setIsMedical(self, isMedical):
        self.isMedical = isMedical


    def setIsMedicalOrg(self, isMedicalOrg):
        self.isMedicalOrg = isMedicalOrg


class COrgInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width):
        CInDocTableCol.__init__(self, title, fieldName, width)
        self.orgCaches = {}


    def toString(self, val, record):
        orgId = forceRef(val)
        if orgId:
            info = self.orgCaches.get(orgId, {})
            if not info:
                info = getOrganisationInfo(orgId)
                if info:
                    self.orgCaches[orgId] = info
            if info:
                return toVariant(info.get('shortName', u'не задано'))
        return QVariant(u'не задано')


    def createEditor(self, parent):
        editor = COrgComboBoxEx(parent)
        editor.setAddNone(True, u'не задано')
        return editor


    def setEditorData(self, editor, value, record):
        editor.setValue(forceRef(value))


    def getEditorData(self, editor):
        return toVariant(editor.value())


class COrgInDocTableColEx(COrgInDocTableCol):
    def __init__(self, title, fieldName, width):
        COrgInDocTableCol.__init__(self, title, fieldName, width)


    def toString(self, val, record):
        orgId = forceRef(val)
        info = getOrganisationInfisAndShortName(orgId)
        if info:
            return toVariant(info)
        return QVariant(u'не задано')


class COrgIsMedicalComboBox(COrgComboBox):
    def __init__(self, parent):
        COrgComboBox.__init__(self, parent)
        self.setFilter(u'deleted = 0 and isMedical != 0')

class COrgIsPayer23ComboBox(COrgComboBox):
    def __init__(self, parent):
        COrgComboBox.__init__(self, parent)
        self.setNameField('CONCAT(infisCode, \'| \', shortName)')
        self.setFilter(u'deleted = 0 and isInsurer = 1 and isActive = 1 and head_id is null and substr(area, 1, 2) = \'23\'')
        self.setAddNone(True, u'не задано')
        
    def setWithoutKTFOMS(self, value):
        cond = u" and infisCode not in ('8008', '9007')" if value else u''
        self.setFilter(u'deleted = 0 and isInsurer = 1 and isActive = 1  and head_id is null and substr(area, 1, 2) = \'23\'%s' % cond)
    

# class COrgInDocTableColEx(COrgInDocTableCol):
#
#     def createEditor(self, parent):
#         editor = COrgIsMedicalComboBox(parent)
#         editor.setAddNone(True, u'не задано')
#         return editor


class CInsurerComboBox(CDbComboBox):
    insurerFilter = 'isInsurer = 1 and deleted = 0 AND isActive = 1'

    def __init__(self, parent):
        CDbComboBox.__init__(self, parent)
        self.setNameField('CONCAT(infisCode,\'| \', shortName)')
        self.setAddNone(True)
        self.setFilter(self.insurerFilter)
        self.setTable('Organisation')
        self._popup = CInsurerComboBoxPopup(self)


    def showPopup(self):
        self.__searchString = ''
        self.connect(self._popup, SIGNAL('insurerSelected(int)'), self.setValue)
        pos = self.rect().bottomLeft()
        pos = self.mapToGlobal(pos)
        size = self._popup.sizeHint()
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        size.setWidth(QtGui.QApplication.desktop().screenGeometry().height())
        pos.setX(max(min(pos.x(), screen.right() - size.width()), screen.left()))
        pos.setY(max(min(pos.y(), screen.bottom() - size.height()), screen.top()))
        self._popup.move(pos)
        self._popup.resize(size)
        self._popup.show()


    def setSerialFilter(self, serial):
        self._popup.setSerialFilter(serial)


    def setAreaFilter(self, areaList):
        self._popup.setAreaFilter(areaList)


class CInsurerComboBoxEx(CInsurerComboBox):
    def __init__(self, parent):
        CInsurerComboBox.__init__(self, parent)
        self.invalidValue = None


    def setValue(self, itemId, isFirst=False):
        rowIndex = self.model().searchId(itemId)
        if rowIndex == -1 and isFirst:
            self.setFilter(' '.join([self.model().filter, ' OR id = {0}'.format(itemId)]))
            self.invalidValue = itemId
            rowIndex = self.model().searchId(itemId)

        self.setCurrentIndex(rowIndex)
        if itemId == self.invalidValue and self.invalidValue:
            self.setStyleSheet('QComboBox {color: red}')
            self._popup.setStyleSheet('QComboBox {color: black}')
        else:
            self.setStyleSheet('')
            self._popup.setStyleSheet('')


class CInsurerAreaInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width):
        CInDocTableCol.__init__(self, title, fieldName, width)
        self._readOnly = True
        self._external = True
        self._valueType = QVariant.Int

    def toString(self, val, record):
        area = QtGui.qApp.db.translate('Organisation', 'id', val, 'area')
        if not area:
           return QVariant(u'не задано')
        return QtGui.qApp.db.translate('kladr.KLADR', 'CODE', area, 'CONCAT(NAME,\' \', SOCR)')


class CInsurerInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width):
        CInDocTableCol.__init__(self, title, fieldName, width)


    def toString(self, val, record):
        result = QtGui.qApp.db.translate('Organisation', 'id', val, 'CONCAT(infisCode,\'| \', shortName)')
        return result if result else QVariant(u'не задано')


    def createEditor(self, parent):
        editor = CInsurerComboBox(parent)
        editor.setAddNone(True, u'не задано')
        return editor


    def setEditorData(self, editor, value, record):
        editor.setValue(forceRef(value))


    def getEditorData(self, editor):
        return toVariant(editor.value())


class CPolyclinicComboBox(CDbComboBox):
    nameField = 'CONCAT(infisCode,\'| \', shortName)'
    filter = 'isMedical != 0 and deleted = 0'
    def __init__(self, parent):
        CDbComboBox.__init__(self, parent)
        self.setNameField(CPolyclinicComboBox.nameField)
        self.setAddNone(True)
        self.setFilter(CPolyclinicComboBox.filter)
        self.setTable('Organisation')


class CPolyclinicComboBoxEx(COrgComboBoxEx):
    nameField = 'CONCAT(infisCode,\'| \', shortName)'
    def __init__(self, parent):
        COrgComboBoxEx.__init__(self, parent)
        self.setNameField(CPolyclinicComboBoxEx.nameField)
        self.setAddNone(True)
        self.setIsMedicalOrg(True)
        self.setTable('Organisation')


class CShortNameOrgComboBoxEx(COrgComboBoxEx):
    nameField = 'CONCAT(infisCode,\'| \', shortName)'
    def __init__(self, parent):
        COrgComboBoxEx.__init__(self, parent)
        self.setNameField(CShortNameOrgComboBoxEx.nameField)
        self.setAddNone(True)
        self.setTable('Organisation')


class COrgAccComboBox(CDbComboBox):
    def __init__(self, parent):
        CDbComboBox.__init__(self, parent)
        self.setNameField('name')
        self.setAddNone(True)
        self.setFilter('1=0')
        self.setTable('Organisation_Account')
        self.__orgId = None


    def setOrgId(self, orgId):
        if self.__orgId != orgId:
            if orgId:
                self.setAddNone(False)
                self.setFilter('organisation_id=\'%d\'' % orgId)
            else:
                self.setAddNone(True)
                self.setFilter('1=0')
            self.__orgId = orgId
            self.model().reset()
            if self.model().rowCount(QModelIndex())>0:
                self.setCurrentIndex(0)


class CContractDbData(CDbData):
    def __init__(self):
        CDbData.__init__(self)
        self.financeList = []
        self._addNone = False
        
    def addNone(self, value=True):
        self._addNone = value

    def select(self, cond):
        self.selectInt(True, True, cond)
        if self.idList:
            return
        self.selectInt(True, False, cond)
        if self.idList:
            return
        self.selectInt(False, True, cond)
        if self.idList:
            return
        self.selectInt(False, False, cond)


    def selectInt(self, strictEventType, strictContingent, cond):
        from Events.Utils import getEventFinanceId
#        from Registry.Utils import getClientAttaches

    # нужен запрос типа
    #    SELECT *
    #    FROM Contract
    #    WHERE
    #      recipient_id = orgId
    #      AND ((EXISTS (SELECT id
    #                    FROM Contract_Specification
    #                    WHERE
    #                        Contract_Specification.master_id=Contract.id
    #                        AND Contract_Specification.eventType_id = $eventTypeId
    #                   )
    #           ) OR
    #           (NOT EXISTS (
    #                    SELECT id
    #                    FROM Contract_Specification
    #                    WHERE Contract_Specification.master_id=Contract.id
    #                       )
    #           )
    #          )
    #      AND ((EXISTS (SELECT id
    #                    FROM Contract_Contingent
    #                    WHERE
    #                        Contract_Contingent.master_id=Contract.id
    #                        AND (Contract_Contingent.org_id = $clientOrgId OR Contract_Contingent.org_id IS NULL)
    #                   )
    #           ) OR
    #           (NOT EXISTS (
    #                    SELECT id
    #                    FROM Contract_Contingent
    #                    WHERE Contract_Contingent.master_id=Contract.id
    #                       )
    #           )
    #          )
    #      AND Contract.finance_id = $eventType.financeId
    #      AND Contract.begDate <= begDate
    #      AND Contract.endDate >= endDate
    # с учётом того что параметры функции могут быть нулями

        db = QtGui.qApp.db
        tableContract = db.table('Contract')
        tableFinance = db.table('rbFinance')
        filter = [tableContract['deleted'].eq(0)]
        
        if cond.orgId:
            filter.append(tableContract['recipient_id'].eq(cond.orgId))
        if cond.financeId:
            filter.append(tableContract['finance_id'].eq(cond.financeId))
        if cond.eventTypeId:
            tableContractSpecification = db.table('Contract_Specification')
            condInContract = db.joinAnd([tableContractSpecification['master_id'].eq(tableContract['id']),
                                         tableContractSpecification['deleted'].eq(0)])
            if strictEventType:
                filterEventType = [condInContract, tableContractSpecification['eventType_id'].eq(cond.eventTypeId)]
                condEventType = db.existsStmt(tableContractSpecification, filterEventType)
            else:
                filterEventType = [condInContract, tableContractSpecification['eventType_id'].isNotNull()]
                condEventType = 'NOT '+db.existsStmt(tableContractSpecification, filterEventType)
            filter.append(condEventType)
            financeId = getEventFinanceId(cond.eventTypeId)
            if financeId:
                filter.append(tableContract['finance_id'].eq(financeId))
        if cond.actionTypeId and cond.financeId:
            tableActionTypeService = db.table('ActionType_Service')
            tableContractTariff = db.table('Contract_Tariff')
            tableATCT = tableContractTariff.leftJoin(tableActionTypeService, tableActionTypeService['service_id'].eq(tableContractTariff['service_id']))
            actionFilter = [tableContractTariff['deleted'].eq(0),
                            db.joinOr([tableContractTariff['master_id'].eq(tableContract['id']), tableContractTariff['master_id'].eq(tableContract['priceListExternal_id'])]),
                            tableActionTypeService['master_id'].eq(cond.actionTypeId),
                            tableContractTariff['tariffType'].inlist([CTariff.ttActionAmount, CTariff.ttActionUET, CTariff.ttHospitalBedService]),
                            db.joinOr([tableActionTypeService['finance_id'].eq(cond.financeId),
                                       'ActionType_Service.finance_id IS NULL AND NOT EXISTS(SELECT 1 FROM ActionType_Service AS ATS WHERE ATS.master_id=%d AND ATS.finance_id=%d)' % (cond.actionTypeId, cond.financeId)
                                      ]
                                     )
                           ]
            filter.append(db.existsStmt(tableATCT, db.joinAnd(actionFilter)))
        tableContractContingent = db.table('Contract_Contingent')
        condInContract = db.joinAnd([tableContractContingent['master_id'].eq(tableContract['id']),
                                     tableContractContingent['deleted'].eq(0)])
        if strictContingent:
            condContingent = 'isClientInContractContingent(Contract.id, %d, %s, %s, %s)' \
                             % ( cond.clientId,
                                 db.formatDate(cond.begDate or cond.endDate or QDate.currentDate()),
                                 quote(QtGui.qApp.defaultKLADR()),
                                 quote(QtGui.qApp.provinceKLADR())
                               )


#            contingentFilter = [condInContract,
#                                tableContractContingent['sex'].inlist([0, cond.clientSex]),
#                               ]
#
#            contingentSocStatusCond = [tableContractContingent['socStatusType_id'].isNull()]
#            tableClientSocStatus = db.table('ClientSocStatus')
#            socStatusCond = [tableClientSocStatus['client_id'].eq(cond.clientId),
#                                        tableClientSocStatus['deleted'].eq(0),
#                                        db.joinOr([tableClientSocStatus['endDate'].isNull(),
#                                                        tableClientSocStatus['endDate'].dateGe(cond.begDate)]),
#                                        tableClientSocStatus['begDate'].dateLe(cond.endDate)]
#            socStatusRecords = db.getRecordList(tableClientSocStatus, 'SocStatusType_id as socStatus, begDate, endDate', socStatusCond)
#            if socStatusRecords:
#                contingentSocStatusCond.append(tableContractContingent['socStatusType_id'].inlist(
#                                                                                            forceInt(record.value('socStatus')) for record in socStatusRecords ))
#            contingentFilter.append(db.joinOr(contingentSocStatusCond))
#            # client_id: пропускаем
#            # attachType_id
#            attachList = getClientAttaches(cond.clientId, cond.begDate)
#            attachTypeIdList = []
#            for attach in attachList:
#                if (    (not cond.orgId or attach['LPU_id'] == cond.orgId)
#                    and not attach['outcome']
#                    and not (cond.begDate and attach['begDate'] and attach['begDate'] > cond.begDate )
#                    and not (cond.begDate and attach['endDate'] and attach['endDate'] < cond.begDate )
#                   ):
#                    attachTypeIdList.append(attach['attachTypeId'])
#
#            contingentFilter.append(db.joinOr([tableContractContingent['attachType_id'].isNull(),
#                                               tableContractContingent['attachType_id'].inlist(attachTypeIdList)
#                                              ]))
#
#            if cond.clientOrgId:
#                contingentFilter.append(db.joinOr([tableContractContingent['org_id'].eq(cond.clientOrgId),
#                                                   tableContractContingent['org_id'].isNull()
#                                                  ]))
#            if cond.clientPolicyInfoList:
#                contingentFilterByPolicy = []
#                for insurerId, policyTypeId in cond.clientPolicyInfoList:
#                    subFilterContingent = []
#                    if insurerId:
#                        subFilterContingent.append(db.joinOr([tableContractContingent['insurer_id'].eq(insurerId),
#                                                              tableContractContingent['insurer_id'].isNull()
#                                                             ]))
#                        subFilterContingent.append('insurerServiceAreaMatch(%d, Contract_Contingent.serviceArea, %s, %s)' %
#                                                   (insurerId,
#                                                    quote(QtGui.qApp.defaultKLADR()),
#                                                    quote(QtGui.qApp.provinceKLADR()),
#                                                   )
#                                                  )
#                    else:
#                        subFilterContingent.append(tableContractContingent['insurer_id'].isNull())
#                        subFilterContingent.append('insurerServiceAreaMatch(NULL, Contract_Contingent.serviceArea, %s, %s)' %
#                                                   (quote(QtGui.qApp.defaultKLADR()),
#                                                    quote(QtGui.qApp.provinceKLADR()),
#                                                   )
#                                                  )
#                    if policyTypeId:
#                        subFilterContingent.append(db.joinOr([tableContractContingent['policyType_id'].eq(policyTypeId),
#                                                              tableContractContingent['policyType_id'].isNull()
#                                                             ]))
#                    else:
#                        subFilterContingent.append(tableContractContingent['policyType_id'].isNull())
#                    if subFilterContingent:
#                        contingentFilterByPolicy.append(db.joinAnd(subFilterContingent))
#                if contingentFilterByPolicy:
#                    contingentFilter.append(db.joinOr(contingentFilterByPolicy))
#            condContingent = db.existsStmt(tableContractContingent, contingentFilter)
        else:
            contingentFilter = [condInContract]
            condContingent = 'NOT '+db.existsStmt(tableContractContingent, contingentFilter)
        filter.append(condContingent)
        if cond.begDate:
            filter.append(tableContract['begDate'].le(cond.begDate))
        if cond.endDate:
            filter.append(tableContract['endDate'].ge(cond.endDate))

        self.idList=[]
        self.strList=[]
        self.financeList=[]
        stmt = db.selectStmt(tableContract.leftJoin(tableFinance, tableFinance['id'].eq(tableContract['finance_id'])),
                             [tableContract['id'], tableContract['number'], tableContract['date'], tableContract['resolution'],
                              tableFinance['code'].alias('finance')
                             ],
                             filter,
                             [tableContract['number'].name(), tableFinance['code'].name() + ' DESC', tableContract['date'].name(), tableContract['resolution'].name()]
                            )
        
        query = db.query(stmt)
        while query.next():
            record = query.record()
            id = record.value('id').toInt()[0]
            str = ' '.join([forceString(record.value(name)) for name in ('number', 'date', 'resolution')])
            finance = forceString(record.value('finance'))
            self.idList.append(id)
            self.strList.append(str)
            self.financeList.append(finance)
        
        if self._addNone and self.idList:
            self.idList.insert(0, None)
            self.strList.insert(0, u'Не задано')
            self.financeList.insert(0,'')


    def onlyOneWithSameFinance(self, index):
        if 0<=index<len(self.financeList):
            return self.financeList.count(self.financeList[index])
        else:
            return False


    def getContractIdByFinance(self, financeCode):
        if financeCode in self.financeList:
            index = self.financeList.index(financeCode)
            return self.idList[index]
        return None


class CContractDbModel(CAbstractDbModel):
    def __init__(self, parent, addNone=False):
        CAbstractDbModel.__init__(self, parent)
        self.orgId = QtGui.qApp.currentOrgId()
        self.clientId = None
        self.clientSex   = None
        self.clientAge   = None
        self.clientOrgId = None
        self.clientPolicyInfoList = None
        self.financeId   = None
        self.medicalAidKindId = None
        self.eventTypeId = None
        self.actionTypeId= None
        self.begDate = QDate.currentDate()
        self.endDate = self.begDate
        self._addNone = addNone


    def initDbData(self):
        self.dbdata = CContractDbData()
        self.dbdata.addNone(value=self._addNone)
        if self.orgId and (self.eventTypeId or self.financeId) and self.clientId:
            self.dbdata.select(self)


    def setOrgId(self, orgId):
        if self.orgId != orgId:
            self.orgId = orgId
            self.dbdata = None
            self.reset()


    def setClientInfo(self, clientId, sex, age, orgId, policyInfoList):
        if (  self.clientId != clientId
           or self.clientSex != sex
           or self.clientAge != age
           or self.clientOrgId != orgId
           or self.clientPolicyInfoList != policyInfoList):
            self.clientId    = clientId
            self.clientSex   = sex
            self.clientAge   = age
            self.clientOrgId = orgId
            self.clientPolicyInfoList = policyInfoList
            self.dbdata = None
            self.reset()


    def setFinanceId(self, financeId):
        if self.financeId != financeId:
            self.financeId = financeId
            self.dbdata = None
            self.reset()


    def setMedicalAidKindId(self, medicalAidKindId):
        if self.medicalAidKindId != medicalAidKindId:
            self.medicalAidKindId = medicalAidKindId


    def getFinanceId(self):
        return self.financeId


    def setEventTypeId(self, eventTypeId):
        if self.eventTypeId != eventTypeId:
            self.eventTypeId = eventTypeId
            self.dbdata = None
            self.reset()


    def setActionTypeId(self, actionTypeId):
        if self.actionTypeId != actionTypeId:
            self.actionTypeId = actionTypeId
            self.dbdata = None
            self.reset()


    def setBegDate(self, begDate):
        if self.begDate != begDate:
            self.begDate = begDate
            self.dbdata = None
            self.reset()


    def setEndDate(self, endDate):
        if self.endDate != endDate:
            self.endDate = endDate
            self.dbdata = None
            self.reset()


    def onlyOneWithSameFinance(self, index):
        if self.dbdata:
            return self.dbdata.onlyOneWithSameFinance(index)
        else:
            return False


    def getContractIdByFinance(self, financeCode):
        if self.dbdata:
            return self.dbdata.getContractIdByFinance(financeCode)
        return None


class CContractComboBox(CAbstractDbComboBox):
    __pyqtSignals__ = ('valueChanged()',
                      )

    def __init__(self, parent, addNone=False):
        CAbstractDbComboBox.__init__(self, parent)
        self.__model = CContractDbModel(self, addNone=addNone)
        self.__prevValue = None
        self.setModel(self.__model)
        self.readOnly = False
        self.connect(self, SIGNAL('currentIndexChanged(int)'), self.onCurrentIndexChanged)


    def setReadOnly(self, value=False):
        self.readOnly = value
        self.__model.setReadOnly(self.readOnly)


    def isReadOnly(self):
        return self.readOnly


    def keyPressEvent(self, event):
        if self.isReadOnly():
            event.accept()
        else:
            CAbstractDbComboBox.keyPressEvent(self, event)


    def showPopup(self):
        if not self.isReadOnly():
            CAbstractDbComboBox.showPopup(self)
        view = self.view()
        viewFrame = view.parent()
        size = view.sizeHint()
        size.setWidth(size.width()*2)
        viewFrame.resize(size)


    def getWeakValue(self):
        if self.__model.dbdata:
            return self.value()
        else:
            return None


    def setCurrentIfOnlyOne(self):
        n = self.__model.rowCount()
        if n == 1:
            self.setCurrentIndex(0)
        elif n > 1 and self.__model.onlyOneWithSameFinance(0):
            self.setCurrentIndex(0)
        else:
            self.setCurrentIndex(-1)


    def setOrgId(self, orgId):
        self.__model.setOrgId(orgId)
#        self.setCurrentIfOnlyOne()


    def setClientInfo(self, clientId, sex, age, orgId, policyInfoList):
        self.__model.setClientInfo(clientId, sex, age, orgId, policyInfoList)


    def setFinanceId(self, financeId):
        self.__model.setFinanceId(financeId)


    def setMedicalAidKindId(self, medicalAidKindId):
        self.__model.setMedicalAidKindId(medicalAidKindId)


    def setEventTypeId(self, eventTypeId):
        self.__model.setEventTypeId(eventTypeId)


    def setActionTypeId(self, actionTypeId):
        self.__model.setActionTypeId(actionTypeId)


    def setBegDate(self, begDate):
        signalsBlocked = self.blockSignals(True)
        try:
            self.__model.setBegDate(begDate)
            self.setCurrentIfOnlyOne()
        finally:
            self.blockSignals(signalsBlocked)
        self.conditionalEmitValueChanged()


    def setEndDate(self, endDate):
        signalsBlocked = self.blockSignals(True)
        try:
            self.__model.setEndDate(endDate)
            self.setCurrentIfOnlyOne()
        finally:
            self.blockSignals(signalsBlocked)
        self.conditionalEmitValueChanged()


    def setDate(self, date):
        signalsBlocked = self.blockSignals(True)
        try:
            self.__model.setBegDate(date)
            self.__model.setEndDate(date)
        finally:
            self.blockSignals(signalsBlocked)
        if self.__prevValue is not None:
            self.setValue(self.__prevValue)
        if self.getWeakValue() is None:
            self.setCurrentIfOnlyOne()


    def setCurrentIndex(self, index):
        CAbstractDbComboBox.setCurrentIndex(self, index)
        self.conditionalEmitValueChanged()


    def onCurrentIndexChanged(self, index):
        self.conditionalEmitValueChanged()


    def setValue(self, value):
        CAbstractDbComboBox.setValue(self, value)
        self.conditionalEmitValueChanged()


    def conditionalEmitValueChanged(self):
        value = self.getWeakValue()
        if self.__prevValue != value:
            self.__prevValue = value
            self.emit(SIGNAL('valueChanged()'))


    def getContractIdByFinance(self, financeCode):
        return self.__model.getContractIdByFinance(financeCode)
#
#
# ##############################################################
#
#

class CIndependentContractComboBox(CDbComboBox):
    def __init__(self, parent):
        CDbComboBox.__init__(self, parent)
        self.setTable('Contract', nameField='CONCAT_WS(\' \',grouping, number, DATE_FORMAT(date,\'%d.%m.%Y\'), resolution)')
        self.setAddNone(True, u'не задано')
        self.begDate = QDate.currentDate()
        self.endDate = QDate.currentDate()
        self.financeId = None
        self.updateFilter()

    def setBegDate(self, date):
        if date != self.begDate:
            self.begDate = date
            self.updateFilter()

    def setEndDate(self, date):
        if date != self.endDate:
            self.begDate = date
            self.updateFilter()

    def setFinanceId(self, financeId):
        if financeId != self.financeId:
            self.financeId = financeId
            self.updateFilter()

    def updateFilter(self):
        db = QtGui.qApp.db
        value = self.value()
        tableContract = db.table('Contract')
        cond = [tableContract['endDate'].dateGe(self.begDate),
                tableContract['begDate'].dateLe(self.endDate),
                tableContract['recipient_id'].eq(QtGui.qApp.currentOrgId())]
        if self.financeId:
            cond.append(tableContract['finance_id'].eq(self.financeId))
        self.setFilter(db.joinAnd(cond))
        self.setValue(value)

#
#
# ############################################################################
#
#


class CResultComboBox(CDbComboBox):
    def __init__(self, parent):
        CDbComboBox.__init__(self, parent)
        self.setNameField('name')
        self.setAddNone(True)
        self.setTable('vrbResultWithPurpose')


class CSanatoriumComboBox(COrgComboBoxEx):
    def __init__(self, parent):
        COrgComboBoxEx.__init__(self, parent)
        self.setFilter('isMedical = 5')
        
       
class CSanatoriumInDocTableCol(COrgInDocTableCol):

    def createEditor(self, parent):
        editor = CSanatoriumComboBox(parent)
        editor.setAddNone(True, u'не задано')
        return editor
