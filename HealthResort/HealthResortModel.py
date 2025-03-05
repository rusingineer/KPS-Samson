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

from PyQt4 import QtGui
from PyQt4.QtCore import (Qt,
                          pyqtSignature,
                          QAbstractTableModel,
                          QDate,
                          QDateTime,
                          QString,
                          QTime,
                          QVariant,
                         )

from library.database             import CTableRecordCache, CRecordCache
from library.InDocTable           import CDateInDocTableCol, CEnumInDocTableCol, CInDocTableModel
from library.PrintInfo            import CDateInfo, CDateTimeInfo
from library.TableModel           import (CBoolCol,
                                          CCol,
                                          CDateCol,
                                          CDateTimeFixedCol,
                                          CDesignationCol,
                                          CEnumCol,
                                          CIntCol,
                                          CNumCol,
                                          CRefBookCol,
                                          CTableModel,
                                          CTextCol,
                                         )

from library.Utils                import (calcAge,
                                          forceBool,
                                          forceDate,
                                          forceDateTime,
                                          forceInt,
                                          forceRef,
                                          forceString,
                                          formatShortNameInt,
                                          getAgeRangeCond,
                                          getDataOSHB,
                                          getHospDocumentLocationInfo,
                                          getMKB,
                                          isMKB,
                                          toVariant,
                                          forceStringEx,
                                         )

from Events.ActionServiceType     import CActionServiceType
from Events.ActionStatus          import CActionStatus
from Events.ActionTypeCol         import CActionTypeCol
from Events.Utils                 import getActionTypeIdListByFlatCode, getRealPayed, getEventDurationRule

from Reports.Utils                import (getActionClientPolicyForDate,
                                          getActionQueueClientPolicyForDate,
                                          getActionTypeStringPropertyValue,
                                          getClientPolicyForDate,
                                          getContractClientPolicyForDate,
                                          getDataOrgStructure,
                                          getDataOrgStructureName,
                                          getDataOrgStructureNameMoving,
                                          getPropertyAPHBP,
                                          getStringProperty,
                                          getStringPropertyValue,
                                          isActionToServiceTypeForEvent,
                                          getStringPropertyEventYes,
                                          updateLIKE,
                                          getPropertyHospitalBedProfile,
                                         )

from Resources.JobTicketChooser   import getJobTicketAsText
from Orgs.Orgs                    import selectOrganisation
from Orgs.Utils                   import getOrganisationShortName
from KLADR.KLADRModel             import getCityName

from HospitalBeds.Ui_ReportF001Setup           import Ui_ReportF001SetupDialog
from HospitalBeds.Ui_HospitalizationExecDialog import Ui_HospitalizationExecDialog
from HospitalBeds.Ui_HBPatronEditorDialog      import Ui_HBPatronEditorDialog


class CHealthResortModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent,  [
            CTextCol(u'Код',            ['code'], 10),
            CBoolCol(u'Штат',           ['isPermanent'], 10),
            CRefBookCol(u'Тип',         ['type_id'], 'rbHospitalBedType', 10),
            CRefBookCol(u'Профиль',     ['profile_id'], 'rbHospitalBedProfile', 10),
            CNumCol(u'Смены',           ['relief'], 6),
            CRefBookCol(u'Режим',       ['schedule_id'], 'rbHospitalBedShedule', 15),
            CDateCol(u'Начало',         ['begDate'], 20),
            CDateCol(u'Окончание',      ['endDate'], 20),
            CDesignationCol(u'Подразделение', ['master_id', 'isBusy'], ('OrgStructure', 'name'), 8),
            CTextCol(u'Наименование',   ['name'], 20),
            CTextCol(u'Возраст',        ['age'], 10),
            CEnumCol(u'Пол',            ['sex'], ['', u'М', u'Ж'], 10),
            ], 'vHospitalBed' )

        self._cols[3].setToolTip(u'Профиль пребывания')


    def isBusy(self, index):
        record = self.getRecordByRow(index.row())
        return forceBool(record.value('isBusy')) if record else None


    def data(self, index, role):
        if role == Qt.BackgroundColorRole:
            record = self.getRecordByRow(index.row())
            if record and forceBool(record.value('isBusy')):
                return toVariant(QtGui.QColor(200, 230, 240))
            else:
                return QVariant()
        else:
            return CTableModel.data(self, index, role)


class CInvoluteBedsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'OrgStructure_HospitalBed_Involution', 'id', 'master_id', parent)
        self.addCol(CEnumInDocTableCol(u'Причина сворачивания', 'involutionType', 16, [u'нет сворачивания', u'ремонт', u'карантин',  u'иные причины',  u'проветривание'])).setReadOnly()
        self.addCol(CDateInDocTableCol(u'Начало сворачивания', 'begDate', 20, canBeEmpty=True)).setReadOnly()
        self.addCol(CDateInDocTableCol(u'Окончание сворачивания', 'endDate', 20, canBeEmpty=True)).setReadOnly()


class CMonitoringModel(QAbstractTableModel):
    column = [u'И', u'Номер', u'ФИО', u'Пол', u'Дата рождения', u'Поступил', u'Выбыл', u'Койка', u'Подразделение', u'Лечащий врач']
    sex = [u'', u'М', u'Ж']

    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.items = []
        self.clientDeath = 8
        self.headerSortingCol = {}


    def columnCount(self, index = None):
        return 12


    def rowCount(self, index = None):
        return len(self.items)


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
            elif role == Qt.ToolTipRole:
                if section == 0:
                    return QVariant(u'Статус наблюдения пациента')
                elif section == 1:
                    return QVariant(u'Источник финансирования (код)')
                elif section == 2:
                    return QVariant(u'Договор')
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            item = self.items[row]
            return toVariant(item[column])
        elif role == Qt.ToolTipRole:
            if column == 0:
                item = self.items[row]
                return QVariant(item[0] + u' ' + item[19])
            elif column == 1:
                item = self.items[row]
                return QVariant(item[17] + u' ' + item[1])
            elif column == 13:
                item = self.items[row]
                return QVariant(item[13] + u' ' + item[18])
        elif role == Qt.BackgroundColorRole:
            if column == 0 and self.items[row][0]:
               return toVariant(QtGui.QColor(self.items[row][20]))
        return QVariant()


    def getOrgStructureIdList(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    def getDescendantGroups(self, table, groupCol, groupCond, groupId):
        db = QtGui.qApp.db
        db.checkdb()
        table = db.forceTable(table)
        group = table[groupCol]

        result = set([groupId])
        parents = set([groupCond])

        while parents:
            childrenId = set(db.getIdList(table, where=group.inlist(parents)))
            newChildrenId = childrenId-result
            result |= newChildrenId
            records = db.getRecordList(table, [table['code']], [table['id'].inlist(newChildrenId), table['deleted'].eq(0)])
            childrenCode = set([forceString(record.value('code')) for record in records])
            newChildrenCode = childrenCode-parents
            parents = newChildrenCode
        return list(result)


class CPresenceModel(CMonitoringModel):
    column = [u'C', u'И', u'Д', u'П', u'ПпУ', u'Лицо по уходу', u'К', u'Номер', u'Карта', u'ФИО', u'Пол', u'Дата рождения',
    u'Госпитализирован', u'Поступил', u'Плановая дата выбытия', u'MKB', u'Профиль', u'Койка', u'Помещение', u'Подразделение',
    u'Лечащий врач', u'Исполнитель', u'Гражданство',  u'А|МН П',  u'А|МН пУ',  u'ГрКр', u'Патронаж', u'М',
    u'Койко-дни', u'Путевка', u'Субъект', u'Район', u'Направитель']
    feedColumn          = 3
    extraFeedColumn     = 4
    patronColumn        = 5
    clientIdColumn      = 7
    bedColumn           = 17
    placementColumn     = 18
    namePersonColumn    = 21
    eventColumn         = 33
    actionIdColumn      = 38
    actionTypeIdColumn  = 39
    setDateColumn       = 42
    actionEndDateColumn = 43
    patronIdColumn      = 44
    receivedDateColumn = 13

    def __init__(self, parent):
        CMonitoringModel.__init__(self, parent)
        self.items = []
        self.eventIdList = []
        self._cols = []
        self.begDays = 0

    def cols(self):
        self._cols = [CCol(u'Статус наблюдения',     ['statusObservation'], 20, 'l'),
                      CCol(u'Код ИФ',                ['nameFinance'], 20, 'l'),
                      CCol(u'Договор',               ['contract'], 20, 'l'),
                      CCol(u'Питание',               ['feed'], 20, 'l'),
                      CCol(u'Питание по уходу',      ['extraFeed'], 20, 'l'),
                      CCol(u'Лицо по уходу',         ['patronName'], 20, 'l'),
                      CCol(u'Комфортность',          ['comfortableDate'], 20, 'l'),
                      CCol(u'Номер',                 ['client_id'], 20, 'l'),
                      CCol(u'Карта',                 ['externalId'], 20, 'l'),
                      CCol(u'ФИО',                   ['lastName', 'firstName', 'patrName'], 30, 'l'),
                      CCol(u'Пол',                   ['sex'], 15, 'l'),
                      CCol(u'Дата рождения',         ['birthDate'], 20, 'l'),
                      CCol(u'Госпитализирован',      ['begDate'], 20, 'l'),
                      CCol(u'Поступил',              ['endDate'], 20, 'l'),
                      CCol(u'Плановая дата выбытия', ['plannedEndDate'], 20, 'l'),
                      CCol(u'MKB',                   ['MKB'], 20, 'l'),
                      CCol(u'Профиль',               ['profileName'], 20, 'l'),
                      CCol(u'Койка',                 ['codeBed', 'nameBed'], 30, 'l'),
                      CCol(u'Помещение',             ['placement'], 30, 'l'),
                      CCol(u'Подразделение',         ['nameOrgStructure'], 30, 'l'),
                      CCol(u'Лечащий врач',          ['namePerson'], 30, 'l'),
                      CCol(u'Исполнитель',           ['execPerson'], 30, 'l'),
                      CCol(u'Гражданство',           ['citizenship'], 30, 'l'),
                      CCol(u'Аллергия|Медикаментозная непереносимость пациента', ['clientFeatures'], 20, 'l'),
                      CCol(u'Аллергия|Медикаментозная непереносимость лица по уходу', ['patronFeatures'], 20, 'l'),
                      CCol(u'Группа крови',          ['bloodType'], 20, 'l'),
                      CCol(u'Патронаж',              ['relative'], 20, 'l'),
                      CCol(u'Место нахождение учетного документа',['hospDocumentLocation'], 20, 'l'),
                      CCol(u'Койко-дни',             ['bedDays'], 20, 'l'),
                      CCol(u'Путевка',               ['voucher'], 20, 'l'),
                      CCol(u'Субъект',               ['srcCity'], 20, 'l'),
                      CCol(u'Район',                 ['srcRegion'], 20, 'l'),
                      CCol(u'Направитель',           ['srcOrg'], 20, 'l'),
                      ]
        return self._cols


    def columnCount(self, index = None):
        return 33


    def rowCount(self, index = None):
        return len(self.items)


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
            elif role == Qt.ToolTipRole:
                if section == 0:
                    return QVariant(u'Статус наблюдения пациента')
                elif section == 1:
                    return QVariant(u'Источник финансирования (код)')
                elif section == 2:
                    return QVariant(u'Договор')
                elif section == 3:
                    return QVariant(u'Питание пациента')
                elif section == 4:
                    return QVariant(u'Питание по уходу')
                elif section == 6:
                    return QVariant(u'Комфортность')
                elif section == 16:
                    return QVariant(u'Профиль лечения')
                elif section == 23:
                    return QVariant(u'Аллергия|Медикаментозная непереносимость пациента')
                elif section == 24:
                    return QVariant(u'Аллергия|Медикаментозная непереносимость лица по уходу')
                elif section == 25:
                    return QVariant(u'Группа крови')
                elif section == 27:
                    return QVariant(u'Место нахождение учетного документа')
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            if column != 3 and column != 4:
                item = self.items[row]
                return toVariant(item[column])
            elif column == 3:
                return toVariant(self.feedTextValueItems[row])
            elif column == 4:
                return toVariant(self.extraFeedTextValueItems[row])
        elif role == Qt.CheckStateRole:
            if column == 3 or column == 4:
                item = self.items[row]
                if column == 4 and not item[len(item)-4]:
                    return QVariant()
                return toVariant(Qt.Checked if item[column] else Qt.Unchecked)
        elif role == Qt.ToolTipRole:
            if column == 0:
                item = self.items[row]
                return QVariant(item[0] + u' ' + item[37])
            elif column == 1:
                item = self.items[row]
                return QVariant(item[34] + u' ' + item[1])
            elif column == 17:
                item = self.items[row]
                return QVariant(item[17] + u' ' + item[35])
        elif role == Qt.FontRole:
            if column == 6 and self.items[row][6]:
                comfortDate = self.items[row][6]
                if comfortDate.date() == QDate.currentDate():
                    result = QtGui.QFont()
                    result.setBold(True)
                    return QVariant(result)
            elif column == 3 or column == 4:
                if row >= 0 and row < len(self.items):
                    item = self.items[row]
                    if item:
                        if (column == 3 and item[45]) or (column == 4 and item[46]):
                            result = QtGui.QFont()
                            result.setBold(True)
                            result.setStrikeOut(True)
                            return QVariant(result)
            elif column == 23 or column == 24:
                clientFeatures  = self.items[row][23].split('|')
                patronFeatures  = self.items[row][24].split('|')
                if len(clientFeatures)>0 and (int(clientFeatures[0])>=3 or int(clientFeatures[1])>=3) and column==23:
                    result = QtGui.QFont()
                    result.setBold(True)
                    return QVariant(result)
                if len(patronFeatures)>0 and (int(patronFeatures[0])>=3 or int(patronFeatures[1])>=3) and column==24:
                    result = QtGui.QFont()
                    result.setBold(True)
                    return QVariant(result)
            if self.items[row][len(self.items[row])-3]:
                result = QtGui.QFont()
                result.setBold(True)
                result.setItalic(True)
                return QVariant(result)
        elif role == Qt.BackgroundColorRole:
            if column == 0 and self.items[row][0] and self.items[row][40]:
               return toVariant(QtGui.QColor(self.items[row][40]))
            elif column == 6 and self.items[row][6] and not self.items[row][41]:
               return toVariant(QtGui.QColor(Qt.red))
            elif column == 1:
                colorFinance = self.items[row][len(self.items[row])-1]
                if colorFinance:
                    return toVariant(colorFinance)
            elif column == len(self.column)-2:
                docLocalColor = self.items[row][len(self.items[row])-2]
                if docLocalColor:
                    return toVariant(QtGui.QColor(docLocalColor))
        elif role == Qt.TextColorRole:
            if column == 23 or column == 24:
                clientFeatures  = self.items[row][23].split('|')
                patronFeatures  = self.items[row][24].split('|')
                if len(clientFeatures)>0 and (int(clientFeatures[0])>3 or int(clientFeatures[1])>3) and column==23:
                    return toVariant(QtGui.QColor(Qt.red))
                if len(patronFeatures)>0 and (int(patronFeatures[0])>3 or int(patronFeatures[1])>3) and column==24:
                    return toVariant(QtGui.QColor(Qt.red))
        return QVariant()


    def loadData(self, dialogParams):
        self.begDays = 0
        self.items = []
        self.itemByName = {}
        self.feedTextValueItems = []
        self.extraFeedTextValueItems = []
        self.eventIdList = []
        filterBegDate = dialogParams.get('filterBegDate', None)
        filterEndDate = dialogParams.get('filterEndDate', None)
        filterBegTime = dialogParams.get('filterBegTime', QTime())
        filterEndTime = dialogParams.get('filterEndTime', QTime())
        begDateTime = None
        endDateTime = None
        if filterBegDate and filterBegTime:
            begDateTime = QDateTime(filterBegDate, filterBegTime)
        if filterEndDate and filterEndTime:
            endDateTime = QDateTime(filterEndDate, filterEndTime)
        indexSex = dialogParams.get('indexSex', 0)
        ageFor = dialogParams.get('ageFor', 0)
        ageTo = dialogParams.get('ageTo', 150)
        order = dialogParams.get('order', 0)
        eventTypeId = dialogParams.get('eventTypeId', None)
        orgStructureId = dialogParams.get('orgStructureId', None)
        permanent = dialogParams.get('permanent', None)
        type = dialogParams.get('type', None)
        bedProfile = dialogParams.get('bedProfile', None)
        treatmentProfile = dialogParams.get('treatmentProfile', None)
        presenceDay = dialogParams.get('presenceDay', None)
        codeAttachType = dialogParams.get('codeAttachType', None)
        indexLocalClient = dialogParams.get('indexLocalClient', None)
        finance = dialogParams.get('finance', None)
        contractId = dialogParams.get('contractId', None)
        feed = dialogParams.get('feed', None)
        dateFeed = dialogParams.get('dateFeed', None)
        personId = dialogParams.get('personId', None)
        accountingSystemId = dialogParams.get('accountingSystemId', None)
        filterClientId = dialogParams.get('filterClientId', None)
        filterEventId = dialogParams.get('filterEventId', None)
        statusObservation = dialogParams.get('statusObservation', None)
        codeBeds = dialogParams.get('codeBeds', None)
        placementId = dialogParams.get('placementId', None)
        isPlacementChecked = dialogParams.get('isPlacementChecked', None)
        dietId = dialogParams.get('dietId', None)
        documentTypeForTracking = dialogParams.get('documentTypeForTracking', None)
        documentLocation = dialogParams.get('documentLocation', None)
        srcCity =  dialogParams.get('srcCity', None)
        srcRegion =  dialogParams.get('srcRegion', None)
        relegateOrg = dialogParams.get('srcOrg', None)
        MKBSrcFilter = dialogParams['MKBSrcFilter']
        MKBSrcFrom   = dialogParams['MKBSrcFrom']
        MKBSrcTo     = dialogParams['MKBSrcTo']
        MKBFilter = dialogParams['MKBFilter']
        MKBFrom   = dialogParams['MKBFrom']
        MKBTo     = dialogParams['MKBTo']
        voucherSerial = dialogParams['voucherSerial']
        voucherNumber = dialogParams['voucherNumber']
        isPresenceActionActiviti = dialogParams.get('isPresenceActionActiviti', True)
        scheduleId = dialogParams.get('scheduleId', None)

        self.statusObservation = statusObservation
        defaultOrgStructureEventTypeIdList = dialogParams.get('defaultOrgStructureEventTypeIdList', [])
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableEventFeed = db.table('Event_Feed')
        tableEV = db.table('Event_Voucher')
        tableClient = db.table('Client')
        tableOS = db.table('OrgStructure')
        tableAPOS = db.table('ActionProperty_OrgStructure')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableClientAttach = db.table('ClientAttach')
        tableRBAttachType = db.table('rbAttachType')
        tableContract = db.table('Contract')
        tableRBFinance = db.table('rbFinance')
        tableRBFinanceBC = db.table('rbFinance').alias('rbFinanceByContract')
        tableOrg = db.table('Organisation')
        tableStatusObservation = db.table('Client_StatusObservation')
        tablekladrOKATO = db.table('kladr.OKATO')
        leavedActionTypeIdList = getActionTypeIdListByFlatCode(u'leaved%')

        def getOrderBy(getBed = False):
            orderBY = u'Client.lastName ASC, Action.endDate ASC'
            for key, value in self.headerSortingCol.items():
                if not value:
                    ASC = u'ASC'
                else:
                    ASC = u'DESC'
                if key == 7:
                   orderBY = u'Event.client_id %s'%(ASC)
                elif key == 8:
                    orderBY = u'CAST(Event.externalId AS SIGNED) %s'%(ASC)
                elif key == 9:
                    orderBY = u'Client.lastName %s'%(ASC)
                elif key == 12:
                    orderBY = u'Event.setDate %s'%(ASC)
                elif key == 13:
                    orderBY = u'Action.begDate %s'%(ASC)
                elif key == 16:
                    orderBY = u'profileName %s'%(ASC)
                elif key == 17:
                    if getBed:
                        orderBY = u'bedCodeName %s'%(ASC)
                    else:
                        orderBY = u''
                elif key == 19:
                    orderBY = u'nameOrgStructure %s'%(ASC)
                elif key == 18:
                    orderBY = u'placement %s'%(ASC)
                elif key == 3:
                    orderBY = u'clientDiet %s'%(ASC)
                elif key == 4:
                    orderBY = u'patronDiet %s'%(ASC)
                elif key == 20:
                    orderBY = u'execPerson %s'%(ASC)
                elif key == 29:
                    orderBY = u'Event_Voucher.serial, Event_Voucher.number %s'%(ASC)
            return orderBY

        def getDataMoving(orgStructureId, indexSex = 0, ageFor = 0, ageTo = 150, permanent = None, type = None,
                          bedProfile = None, presenceDay = None, codeAttachType = None, finance = None,
                          feed = None, dateFeed = None, localClient = 0,
                          accountingSystemId = None, filterClientId = None, filterEventId = None,
                          codeBeds = None, defaultOrgStructureEventTypeIdList=[], begDate = None, endDate = None):
            currentDate = QDate.currentDate()
            groupBY = ''
            cols = [tableAction['id'].alias('actionId'),
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableEvent['relative_id'],
                    tableEvent['eventType_id'],
                    tableEvent['setDate'],
                    tableEvent['execDate'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableAction['plannedEndDate'],
                    tableAction['actionType_id'],
                    tableAction['finance_id'],
                    tableEvent['contract_id'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    tableEV['serial'].alias('serialVoucher'),
                    tableEV['number'].alias('numberVoucher'),
                    tableEvent['relegateOrg_id'],
                    tableEvent['directionCity'],
                    tablekladrOKATO['NAME'].alias('directionRegion'),
                    tableOrg['shortName'].alias('relegateOrg'),
                    tablePWS['name'].alias('namePerson')
                    ]
            cols.append(getMKB())
            cols.append(isActionToServiceTypeForEvent(CActionServiceType.reanimation))
            cols.append('''(SELECT EP.name FROM vrbPersonWithSpeciality AS EP WHERE EP.id = Event.execPerson_id) AS execPerson''')
            cols.append(getReceivedBegDate(getActionTypeIdListByFlatCode(u'received%')))
            cols.append(getLeavedEndDate(leavedActionTypeIdList))
            cols.append('''(IF(Event.relative_id IS NOT NULL, (SELECT CONCAT_WS(_utf8' ', ClientE.lastName, ClientE.firstName,
ClientE.patrName) FROM Client AS ClientE WHERE ClientE.deleted = 0 AND ClientE.id = Event.relative_id), _utf8'')) AS patronName''')
            cols.append(u'IF(OrgStructure.id IS NOT NULL AND OrgStructure.deleted=0, OrgStructure.name, NULL) AS nameOrgStructure')
            if not dateFeed:
                dateFeed = currentDate.addDays(1)
            cols.append(getEventFeedId(u'0', db.formatDate(dateFeed), u''' AS countEventClientFeedId'''))
            cols.append(getEventFeedId(u'1', db.formatDate(dateFeed), u''' AS countEventPatronFeedId'''))
            cols.append(getDietCode(u'0', db.formatDate(dateFeed), u''' AS clientDiet'''))
            cols.append(getDietCode(u'1', db.formatDate(dateFeed), u''' AS patronDiet'''))
            cols.append(getEventRefusalToEat(u'0', db.formatDate(dateFeed), u''' AS refusalToEatClient'''))
            cols.append(getEventRefusalToEat(u'1', db.formatDate(dateFeed), u''' AS refusalToEatPatron'''))
            cols.append(getDataOSHB())
            cols.append(getOSHBP())
            cols.append(getHospDocumentLocationInfo())
            comfortableIdList = getActionTypeIdListByFlatCode(u'comfortable%')
            if comfortableIdList:
                cols.append(getActionByFlatCode(comfortableIdList))
            cols.append(getStatusObservation())
            cols.append(getPlacement())
            cols.append('%s AS patronag'%(getStringPropertyValue(u'Патронаж')))
            cols.append('(SELECT name from rbSocStatusType where code = getClientCitizenship(Client.id, CURDATE())) as citizenship')
            cols.append('(SELECT name from rbBloodType where id = Client.bloodType_id) as bloodType')
            cols.append(getClientFeatures())
            cols.append(getPatronFeatures())
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.leftJoin(tableEV, db.joinAnd([tableEV['event_id'].eq(tableEvent['id']), tableEV['deleted'].eq(0)]))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.leftJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
            queryTable = queryTable.leftJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            queryTable = queryTable.leftJoin(tablekladrOKATO, tablekladrOKATO['CODE'].eq(tableEvent['directionRegion']))
            cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'moving%')),
                     tableAction['deleted'].eq(0),
                     tableEvent['deleted'].eq(0),
                     tableAP['deleted'].eq(0),
                     tableClient['deleted'].eq(0),
                     tableAP['action_id'].eq(tableAction['id'])
                   ]
            if scheduleId:
                cond.append(isScheduleBeds(scheduleId))
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'8\')))''')
            if defaultOrgStructureEventTypeIdList:
                cond.append(tableEvent['eventType_id'].inlist(defaultOrgStructureEventTypeIdList))
            if personId:
               cond.append(tableEvent['execPerson_id'].eq(personId))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if srcCity:
                cond.append(tableEvent['directionCity'].eq(srcCity))
            if srcRegion:
                cond.append(tableEvent['directionRegion'].eq(srcRegion))
            if MKBSrcFilter:
                cond.append('Event.directionMKB >= \'%s\' AND Event.directionMKB <= \'%s\''%(MKBSrcFrom, MKBSrcTo))
            if voucherSerial:
                cond.append(tableEV['serial'].eq(voucherSerial))
            if voucherNumber:
                cond.append(tableEV['number'].eq(voucherNumber))
            if self.statusObservation:
                queryTable = queryTable.innerJoin(tableStatusObservation, tableStatusObservation['master_id'].eq(tableClient['id']))
                cond.append(tableStatusObservation['deleted'].eq(0))
                cond.append(tableStatusObservation['statusObservationType_id'].eq(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if feed == 1:
                cond.append('NOT %s'%(getEventFeedId(u'', db.formatDate(dateFeed))))
            elif feed == 2:
                cond.append('%s'%(getEventFeedId(u'', db.formatDate(dateFeed), alias=u'', refusalToEat = 0)))
            elif feed == 3:
                cond.append('%s'%(getEventFeedId(u'', db.formatDate(dateFeed), alias=u'', refusalToEat = 1)))
            if orgStructureIdList:
                cond.append(tableOS['deleted'].eq(0))
                cond.append(getDataOrgStructure(u'Отделение пребывания', orgStructureIdList, False))
            cond.append(tableAPT['name'].like(u'Отделение пребывания'))
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if begDate and endDate:
                cond.append(tableAction['begDate'].le(endDate))
                cond.append(db.joinOr([tableAction['endDate'].ge(begDate), tableAction['endDate'].isNull()]))
            elif begDate:
                cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(begDate)]))
            elif endDate:
                cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].le(endDate)]))
            else:
                cond.append(db.joinAnd([tableAction['begDate'].dateLe(currentDate),
                                        db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].dateGe(currentDate)])]))
            if presenceDay:
               datePresence = endDate.addDays(-presenceDay) if endDate else currentDate.addDays(-presenceDay)
               cond.append(tableAction['begDate'].dateLe(datePresence))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() == 2:
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.code, NULL)) AS codeFinance')
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.name, NULL)) AS nameFinance')
                cols.append(getClientPolicyForDate())
                if finance:
                    cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(finance), str(finance)))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
            elif QtGui.qApp.defaultHospitalBedFinanceByMoving() == 1:
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, NULL) AS nameFinance')
                cols.append(getActionClientPolicyForDate())
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                if finance:
                    cond.append('''(Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s)'''%(str(finance)))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
            else:
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                cols.append(getContractClientPolicyForDate())
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            if localClient == 2:
                cond.append('''NOT %s'''%(getDataAPHB()))
            elif localClient == 1:
                cond.append('''%s'''%(getDataAPHB(permanent, type, bedProfile, codeBeds)))
            else:
                if (permanent and permanent > 0) or (type) or (bedProfile) or codeBeds:
                   cond.append('''%s'''%(getDataAPHB(permanent, type, bedProfile, codeBeds)))
            if isPlacementChecked:
                cond.append(getPlacementCond(placementId))
            if treatmentProfile:
                cond.append(getHospitalBedProfile(treatmentProfile))
            if dietId:
                dateParam = dateFeed if dateFeed else QDate.currentDate()
                feedCond = [
                    tableEventFeed['event_id'].eq(tableEvent['id']),
                    tableEventFeed['diet_id'].eq(dietId),
                    tableEventFeed['date'].eq(dateParam)
                ]
                cond.append(db.existsStmt(tableEventFeed, feedCond))
            if documentTypeForTracking:
                if documentTypeForTracking!=u'specialValueID':
                    tableDocumentTypeForTracking = db.table('Client_DocumentTracking')
                    cond.append(tableDocumentTypeForTracking['deleted'].eq(0))
                    queryTable = queryTable.leftJoin(tableDocumentTypeForTracking, tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                    cond.append(tableDocumentTypeForTracking['documentTypeForTracking_id'].eq(documentTypeForTracking))
                    cond.append(tableDocumentTypeForTracking['documentNumber'].eq(tableEvent['externalId']))
                    groupBY = 'Event.id'
            if documentLocation:
                tableDocumentLocation = db.table('Client_DocumentTrackingItem')
                if not documentTypeForTracking:
                    tableDocumentTypeForTracking = db.table('Client_DocumentTracking')
                    queryTable = queryTable.leftJoin(tableDocumentTypeForTracking, tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                    cond.append(tableDocumentTypeForTracking['documentNumber'].eq(tableEvent['externalId']))
                queryTable = queryTable.leftJoin(tableDocumentLocation, tableDocumentTypeForTracking['id'].eq(tableDocumentLocation['master_id']))
                tableDocumentLocationLimit = db.table('Client_DocumentTrackingItem').alias('tableDocumentLocationLimit')
                cond.append(tableDocumentLocation['documentLocation_id'].inlist(documentLocation))
                cond.append(u'Client_DocumentTracking.documentNumber = Event.externalId')
                cond.append(tableDocumentLocation['id'].eqEx('(%s)'%db.selectStmt(tableDocumentLocationLimit, tableDocumentLocationLimit['id'], tableDocumentLocationLimit['master_id'].eq(tableDocumentLocation['master_id']), 'documentLocationDate desc, documentLocationTime desc limit 1')))
                if groupBY=='':
                    groupBY = 'Event.id'
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            orderBY = getOrderBy(True)
            if isPresenceActionActiviti:
                cond.append(tableAction['endDate'].isNull())
            else:
                if groupBY!='':
                    groupBY += u', ' + u'Event.externalId'
                else:
                    groupBY = u'Event.externalId'
            if groupBY!='':
                records = db.getRecordListGroupBy(queryTable, cols, cond, groupBY, orderBY)
            else:
                records = db.getRecordList(queryTable, cols, cond, orderBY)
            for record in records:
                documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                if documentTypeForTracking==u'specialValueID':
                    if hospDocumentLocation!='':
                        continue
                countEventClientFeedId = forceBool(record.value('countEventClientFeedId'))
                countEventPatronFeedId = forceBool(record.value('countEventPatronFeedId'))
                refusalToEatClient = forceBool(record.value('refusalToEatClient'))
                refusalToEatPatron = forceBool(record.value('refusalToEatPatron'))
                if (feed == 1 and not (countEventClientFeedId + countEventPatronFeedId)) or (feed == 2 and (countEventClientFeedId + countEventPatronFeedId)) or not feed or feed == 3 or feed == 4:
                    bedCodeName = forceString(record.value('bedCodeName')).split("  ")
                    bedCode = forceString(bedCodeName[0]) if len(bedCodeName)>=1 else ''
                    bedName = forceString(bedCodeName[1]) if len(bedCodeName)>=2 else ''
                    bedSex = forceString(bedCodeName[2]) if len(bedCodeName)>=3 else ''
                    eventId = forceRef(record.value('eventId'))
                    clientId = forceRef(record.value('client_id'))
                    statusObservation = forceString(record.value('statusObservation')).split('|')
                    statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                    statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                    statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                    statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                    statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                    comfortable = forceString(record.value('comfortable'))
                    comfortableList = []
                    if comfortable:
                        comfortableList = comfortable.split("  ")
                    comfortableDate = forceDateTime(QVariant(comfortableList[0])) if len(comfortableList)>=1 else ''
                    comfortableStatus = forceInt(QVariant(comfortableList[1])) if len(comfortableList)>=2 else 0
                    if comfortableStatus:
                        comfortablePayStatus = getRealPayed(comfortableStatus)
                    else:
                        comfortablePayStatus = False
                    receivBegDate = forceDate(record.value('receivedBegDate'))
                    leavedEndDate = forceDate(record.value('leavedEndDate'))
                    bedDays = updateDurationEvent(receivBegDate, leavedEndDate, begDate, endDate, forceRef(record.value('eventType_id')), isPresence = True)
                    self.begDays += forceInt(bedDays) if bedDays != u'-' else 0
                    begDate = forceDateTime(record.value('begDate'))
                    endDate = forceDateTime(record.value('endDate'))
                    policyEndDate = forceDate(record.value('policyEndDate'))
                    colorFinance = None
                    if policyEndDate:
                        if forceDate(begDate) < policyEndDate and forceDate(begDate).addDays(3) >= policyEndDate:
                           colorFinance = QtGui.QColor(Qt.yellow)
                        elif forceDate(begDate) >= policyEndDate:
                            colorFinance = QtGui.QColor(Qt.red)
                    receivedBegDate = forceDateTime(record.value('receivedBegDate'))
                    relativeId = forceRef(record.value('relative_id'))
                    patron = forceString(record.value('patronName'))
                    clientAllergy = forceString(record.value('clientAllergy'))
                    clientIntoleranceMedicament = forceString(record.value('clientIntoleranceMedicament'))
                    clientFeatures = '%s|%s'%(clientAllergy,  clientIntoleranceMedicament)
                    patronAllergy = forceString(record.value('patronAllergy'))
                    patronIntoleranceMedicament = forceString(record.value('patronIntoleranceMedicament'))
                    patronFeatures = '%s|%s'%(patronAllergy,  patronIntoleranceMedicament)
                    patronag = forceString(record.value('patronag'))
                    nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                    isActionToServiceType = forceBool(record.value('isActionToServiceType'))
                    serialVoucher = forceStringEx(record.value('serialVoucher'))
                    numberVoucher = forceStringEx(record.value('numberVoucher'))
                    relegateOrgName = forceStringEx(record.value('relegateOrg'))
                    directionCity = getCityName(forceStringEx(record.value('directionCity')))
                    directionRegion = forceStringEx(record.value('directionRegion'))
                    item = [ statusObservationName,
                            #statusObservationCode,
                            forceString(record.value('nameFinance')),
                            nameContract,
                            countEventClientFeedId,
                            countEventPatronFeedId,
                            patron,
                            comfortableDate,
                            clientId,
                            forceString(record.value('externalId')),
                            forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                            self.sex[forceInt(record.value('sex'))],
                            forceString(forceDate(record.value('birthDate'))) + u'(' + forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate')))) + u')',
                            receivedBegDate.toString('dd.MM.yyyy hh:mm'),
                            begDate.toString('dd.MM.yyyy hh:mm'),
                            forceDate(record.value('plannedEndDate')),
                            forceString(record.value('MKB')),
                            forceString(record.value('profileName')),
                            bedCode + bedSex,
                            forceString(record.value('placement')),
                            forceString(record.value('nameOrgStructure')),
                            forceString(record.value('execPerson')),
                            forceString(record.value('namePerson')),
                            forceString(record.value('citizenship')),
                            clientFeatures,
                            patronFeatures,
                            forceString(record.value('bloodType')),
                            patronag,
                            hospDocumentLocation,
                            bedDays,
                            ((serialVoucher + u' ') if serialVoucher else u'') + numberVoucher,
                            directionCity,
                            directionRegion,
                            relegateOrgName,
                            eventId,
                            forceString(record.value('codeFinance')),
                            bedName,
                            endDate.toString('dd.MM.yyyy hh:mm'),
                            statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                            forceRef(record.value('actionId')),
                            forceRef(record.value('actionType_id')),
                            statusObservationColor,
                            comfortablePayStatus,
                            begDate,
                            endDate,
                            relativeId,
                            refusalToEatClient,
                            refusalToEatPatron,
                            isActionToServiceType,
                            documentLocationColor,
                            colorFinance
                            ]
                    if eventId and eventId not in self.eventIdList:
                        self.eventIdList.append(eventId)
                    self.feedTextValueItems.append(forceString(record.value('clientDiet')))
                    self.extraFeedTextValueItems.append(forceString(record.value('patronDiet')))
                    self.items.append(item)
                    dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'contract': nameContract,
                        'clientFeed': forceString(record.value('clientDiet')) if countEventClientFeedId else '',
                        'patronFeed': forceString(record.value('patronDiet')) if countEventPatronFeedId else '',
                        'comfortableDate': comfortableDate,
                        'bedCode': bedCode + bedSex,
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': bedName,
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor,
                        'setDate': CDateTimeInfo(receivedBegDate),
                        'begDate': CDateTimeInfo(begDate),
                        'plannedEndDate': CDateTimeInfo(forceDateTime(record.value('plannedEndDate'))),
                        'refusalToEatClient': forceBool(record.value('refusalToEatClient')),
                        'refusalToEatPatron': forceBool(record.value('refusalToEatPatron')),
                        'profile' : forceString(record.value('profileName')),
                        'placement' : forceString(record.value('placement'))
                    }
                    self.itemByName[eventId] = dict
            self.reset()


        def findReceivedNoEnd(orgStructureIdList = [], dateFeed = None, accountingSystemId = None, filterClientId = None, filterEventId = None, defaultOrgStructureEventTypeIdList=defaultOrgStructureEventTypeIdList, hospitalWard = False, endDateTime = None, begDateTimeFilter = None, endDateTimeFilter = None):
            currentDate = QDate.currentDate()
            groupBY=''
            cols = [tableAction['id'].alias('actionId'),
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableEvent['relative_id'],
                    tableEvent['eventType_id'],
                    tableEvent['setDate'],
                    tableEvent['execDate'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableEvent['setDate'],
                    tableAction['plannedEndDate'],
                    tableAction['actionType_id'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    tableEV['serial'].alias('serialVoucher'),
                    tableEV['number'].alias('numberVoucher'),
                    tableEvent['relegateOrg_id'],
                    tableEvent['directionCity'],
                    tablekladrOKATO['NAME'].alias('directionRegion'),
                    tableOrg['shortName'].alias('relegateOrg'),
                    tablePWS['name'].alias('namePerson')
                    ]
            cols.append(getMKB())
            cols.append(isActionToServiceTypeForEvent(CActionServiceType.reanimation))
            cols.append('''(SELECT EP.name FROM vrbPersonWithSpeciality AS EP WHERE EP.id = Event.execPerson_id) AS execPerson''')
            cols.append(getReceivedBegDate(getActionTypeIdListByFlatCode(u'received%')))
            cols.append(getLeavedEndDate(leavedActionTypeIdList))
            cols.append('''(IF(Event.relative_id IS NOT NULL, (SELECT CONCAT_WS(_utf8' ', ClientE.lastName, ClientE.firstName,
ClientE.patrName, CAST( ClientE.id AS CHAR)) FROM Client AS ClientE WHERE ClientE.deleted = 0 AND ClientE.id = Event.relative_id LIMIT 1), _utf8'')) AS patronName''')
#            cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
#            cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
            nameProperty = u'Направлен в отделение'
            cols.append(getDataOrgStructureName(nameProperty))
            cols.append('%s AS patronag'%(getStringPropertyEventYes(getActionTypeIdListByFlatCode(u'moving%'), u'Патронаж')))
            cols.append(getHospDocumentLocationInfo())
            if not dateFeed:
                dateFeed = currentDate.addDays(1)
            comfortableIdList = getActionTypeIdListByFlatCode(u'comfortable%')
            if comfortableIdList:
                cols.append(getActionByFlatCode(comfortableIdList))
            cols.append(getEventFeedId(u'0', db.formatDate(dateFeed), u''' AS countEventClientFeedId'''))
            cols.append(getEventFeedId(u'1', db.formatDate(dateFeed), u''' AS countEventPatronFeedId'''))
            cols.append(getDietCode(u'0', db.formatDate(dateFeed), u''' AS clientDiet'''))
            cols.append(getDietCode(u'1', db.formatDate(dateFeed), u''' AS patronDiet'''))
            cols.append(getEventRefusalToEat(u'0', db.formatDate(dateFeed), u''' AS refusalToEatClient'''))
            cols.append(getEventRefusalToEat(u'1', db.formatDate(dateFeed), u''' AS refusalToEatPatron'''))
            cols.append(getStatusObservation())
            cols.append(getPlacement())
            cols.append(getOSHBP())
            cols.append('(SELECT name from rbSocStatusType where code = getClientCitizenship(Client.id, CURDATE()) LIMIT 1) as citizenship')
            cols.append('(SELECT name from rbBloodType where id = Client.bloodType_id) as bloodType')
            cols.append(getClientFeatures())
            cols.append(getPatronFeatures())
            queryTable = tableAction.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tableEV, db.joinAnd([tableEV['event_id'].eq(tableEvent['id']), tableEV['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            queryTable = queryTable.leftJoin(tablekladrOKATO, tablekladrOKATO['CODE'].eq(tableEvent['directionRegion']))
            cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'received%')),
                     tableAction['deleted'].eq(0),
                     tableEvent['deleted'].eq(0),
                     tableClient['deleted'].eq(0),
                     tableAction['endDate'].isNull()
                   ]
            if scheduleId:
                cond.append(isScheduleBeds(scheduleId))
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if treatmentProfile:
                cond.append(getHospitalBedProfile(treatmentProfile))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if srcCity:
                cond.append(tableEvent['directionCity'].eq(srcCity))
            if srcRegion:
                cond.append(tableEvent['directionRegion'].eq(srcRegion))
            if MKBSrcFilter:
                cond.append('Event.directionMKB >= \'%s\' AND Event.directionMKB <= \'%s\''%(MKBSrcFrom, MKBSrcTo))
            if voucherSerial:
                cond.append(tableEV['serial'].eq(voucherSerial))
            if voucherNumber:
                cond.append(tableEV['number'].eq(voucherNumber))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'8\')))''')
            if defaultOrgStructureEventTypeIdList:
                cond.append(tableEvent['eventType_id'].inlist(defaultOrgStructureEventTypeIdList))
            if personId:
               cond.append(tableEvent['execPerson_id'].eq(personId))
            if self.statusObservation:
                queryTable = queryTable.innerJoin(tableStatusObservation, tableStatusObservation['master_id'].eq(tableClient['id']))
                cond.append(tableStatusObservation['deleted'].eq(0))
                cond.append(tableStatusObservation['statusObservationType_id'].eq(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if orgStructureIdList and not hospitalWard:
                pigeonHole = db.joinAnd([getActionPropertyTypeName(u'Приемное отделение'),
                getDataOrgStructure(u'Приемное отделение', orgStructureIdList, False)])
                notPigeonHole = db.joinAnd(['NOT %s'%(getActionPropertyTypeName(u'Приемное отделение'))])
                cond.append(db.joinOr([getDataOrgStructure(nameProperty, orgStructureIdList, False), pigeonHole,
                                       notPigeonHole]))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() in (0, 2):
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            cols.append(getContractClientPolicyForDate())
            if feed == 1:
                cond.append('NOT %s'%(getEventFeedId(u'',db.formatDate(dateFeed))))
            elif feed == 2:
                cond.append('%s'%(getEventFeedId(u'',db.formatDate(dateFeed), alias=u'', refusalToEat = 0)))
            elif feed == 3:
                cond.append('%s'%(getEventFeedId(u'',db.formatDate(dateFeed), alias=u'', refusalToEat = 1)))
            if presenceDay:
               datePresence = currentDate.addDays(-presenceDay)
               cond.append(tableAction['begDate'].dateLe(datePresence))
            else:
                if endDateTimeFilter:
                    cond.append(tableAction['begDate'].le(endDateTimeFilter))
                else:
                    cond.append(tableAction['begDate'].dateLe(currentDate))
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if isPlacementChecked:
                cond.append(getPlacementCond(placementId))
            if documentTypeForTracking:
                if documentTypeForTracking!=u'specialValueID':
                    tableDocumentTypeForTracking = db.table('Client_DocumentTracking')
                    cond.append(tableDocumentTypeForTracking['deleted'].eq(0))
                    queryTable = queryTable.leftJoin(tableDocumentTypeForTracking, tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                    cond.append(tableDocumentTypeForTracking['documentTypeForTracking_id'].eq(documentTypeForTracking))
                    cond.append(tableDocumentTypeForTracking['documentNumber'].eq(tableEvent['externalId']))
                    groupBY = 'Event.id'
            if documentLocation:
                tableDocumentLocation = db.table('Client_DocumentTrackingItem')
                if not documentTypeForTracking:
                    tableDocumentTypeForTracking = db.table('Client_DocumentTracking')
                    queryTable = queryTable.leftJoin(tableDocumentTypeForTracking, tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                    cond.append(tableDocumentTypeForTracking['documentNumber'].eq(tableEvent['externalId']))
                queryTable = queryTable.leftJoin(tableDocumentLocation, tableDocumentTypeForTracking['id'].eq(tableDocumentLocation['master_id']))
                tableDocumentLocationLimit = db.table('Client_DocumentTrackingItem').alias('tableDocumentLocationLimit')
                cond.append(tableDocumentLocation['documentLocation_id'].inlist(documentLocation))
                cond.append(tableDocumentLocation['id'].eqEx('(%s)'%db.selectStmt(tableDocumentLocationLimit, tableDocumentLocationLimit['id'], tableDocumentLocationLimit['master_id'].eq(tableDocumentLocation['master_id']), 'documentLocationDate desc, documentLocationTime desc limit 1')))
                if groupBY=='':
                    groupBY = 'Event.id'
            orderBY = getOrderBy()
            if groupBY!='':
                recordsReceived = db.getRecordListGroupBy(queryTable, cols, cond, groupBY, orderBY)
            else:
                recordsReceived = db.getRecordList(queryTable, cols, cond, orderBY)
            for record in recordsReceived:
                documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                if documentTypeForTracking==u'specialValueID':
                    if hospDocumentLocation!='':
                        continue
                countEventClientFeedId = forceBool(record.value('countEventClientFeedId'))
                countEventPatronFeedId = forceBool(record.value('countEventPatronFeedId'))
                refusalToEatClient = forceBool(record.value('refusalToEatClient'))
                refusalToEatPatron = forceBool(record.value('refusalToEatPatron'))
                if (feed == 1 and not (countEventClientFeedId + countEventPatronFeedId)) or (feed == 2 and (countEventClientFeedId + countEventPatronFeedId)) or not feed or feed == 3 or feed == 4:
                    eventId = forceRef(record.value('eventId'))
                    statusObservation = forceString(record.value('statusObservation')).split('|')
                    statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                    statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                    statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                    statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                    statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                    comfortable = forceString(record.value('comfortable'))
                    nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                    comfortableList = []
                    if comfortable:
                        comfortableList = comfortable.split("  ")
                    comfortableDate = forceDateTime(QVariant(comfortableList[0])) if len(comfortableList)>=1 else ''
                    comfortableStatus = forceInt(QVariant(comfortableList[1])) if len(comfortableList)>=2 else 0
                    setDate = forceDateTime(record.value('setDate'))
                    begDate = forceDateTime(record.value('begDate'))
                    endDate = forceDateTime(record.value('endDate'))
                    policyEndDate = forceDate(record.value('policyEndDate'))
                    colorFinance = None
                    if policyEndDate:
                        if forceDate(begDate) < policyEndDate and forceDate(begDate).addDays(3) >= policyEndDate:
                           colorFinance = QtGui.QColor(Qt.yellow)
                        elif forceDate(begDate) >= policyEndDate:
                            colorFinance = QtGui.QColor(Qt.red)
                    receivedBegDate = forceDateTime(record.value('receivedBegDate'))
                    relativeId = forceRef(record.value('relative_id'))
                    patron = forceString(record.value('patronName'))
                    clientAllergy = forceString(record.value('clientAllergy'))
                    clientIntoleranceMedicament = forceString(record.value('clientIntoleranceMedicament'))
                    clientFeatures = '%s|%s'%(clientAllergy,  clientIntoleranceMedicament)
                    patronAllergy = forceString(record.value('patronAllergy'))
                    patronIntoleranceMedicament = forceString(record.value('patronIntoleranceMedicament'))
                    patronag = forceBool(record.value('patronag'))
                    patronFeatures = '%s|%s'%(patronAllergy,  patronIntoleranceMedicament)
                    isActionToServiceType = forceBool(record.value('isActionToServiceType'))
                    receivBegDate = forceDate(record.value('receivedBegDate'))
                    leavedEndDate = forceDate(record.value('leavedEndDate'))
                    bedDays = updateDurationEvent(receivBegDate, leavedEndDate, begDateTimeFilter, endDateTimeFilter, forceRef(record.value('eventType_id')), isPresence = True)
                    self.begDays += forceInt(bedDays) if bedDays != u'-' else 0
                    serialVoucher = forceStringEx(record.value('serialVoucher'))
                    numberVoucher = forceStringEx(record.value('numberVoucher'))
                    relegateOrgName = forceStringEx(record.value('relegateOrg'))
                    directionCity = getCityName(forceStringEx(record.value('directionCity')))
                    directionRegion = forceStringEx(record.value('directionRegion'))
                    item = [statusObservationName,
                            #statusObservationCode,
                            forceString(record.value('nameFinance')),
                            nameContract,
                            countEventClientFeedId,
                            countEventPatronFeedId,
                            patron,
                            comfortableDate,
                            forceRef(record.value('client_id')),
                            forceString(record.value('externalId')),
                            forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                            self.sex[forceInt(record.value('sex'))],
                            forceString(forceDate(record.value('birthDate'))) + u'(' + forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate')))) + u')',
                            receivedBegDate.toString('dd.MM.yyyy hh:mm'),
                            begDate.toString('dd.MM.yyyy hh:mm'),
                            forceDate(record.value('plannedEndDate')),
                            forceString(record.value('MKB')),
                            forceString(record.value('profileName')),
                            forceString(record.value('codeBed')),
                            forceString(record.value('placement')),
                            forceString(record.value('nameOrgStructure')),
                            forceString(record.value('execPerson')),
                            forceString(record.value('namePerson')),
                            forceString(record.value('citizenship')),
                            clientFeatures,
                            patronFeatures,
                            forceString(record.value('bloodType')),
                            u'Да' if patronag else u'Нет',
                            hospDocumentLocation,
                            bedDays,
                            ((serialVoucher + u' ') if serialVoucher else u'') + numberVoucher,
                            directionCity,
                            directionRegion,
                            relegateOrgName,
                            eventId,
                            forceString(record.value('codeFinance')),
                            forceString(record.value('nameBed')),
                            endDate.toString('dd.MM.yyyy hh:mm'),
                            statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                            forceRef(record.value('actionId')),
                            forceRef(record.value('actionType_id')),
                            statusObservationColor,
                            comfortableStatus,
                            setDate,
                            endDate,
                            relativeId,
                            refusalToEatClient,
                            refusalToEatPatron,
                            isActionToServiceType,
                            documentLocationColor,
                            colorFinance
                            ]
                    if eventId and eventId not in self.eventIdList:
                        self.eventIdList.append(eventId)
                    self.feedTextValueItems.append(forceString(record.value('clientDiet')))
                    self.extraFeedTextValueItems.append(forceString(record.value('patronDiet')))
                    self.items.append(item)
                    dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'contract': nameContract,
                        'clientFeed': forceString(record.value('clientDiet')) if countEventClientFeedId else '',
                        'patronFeed': forceString(record.value('patronDiet'))if countEventPatronFeedId else '',
                        'comfortableDate': comfortableDate,
                        'bedCode': forceString(record.value('codeBed')),
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': forceString(record.value('nameBed')),
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor,
                        'setDate': CDateTimeInfo(receivedBegDate),
                        'begDate': CDateTimeInfo(begDate),
                        'plannedEndDate': CDateTimeInfo(forceDateTime(record.value('plannedEndDate'))),
                        'refusalToEatClient': forceBool(record.value('refusalToEatClient')),
                        'refusalToEatPatron': forceBool(record.value('refusalToEatPatron'))
                    }
                    self.itemByName[eventId] = dict
            self.reset()
        movingOSIdList = []
        receivedOSIdList = []
        orgStructureIdList = []
        if orgStructureId:
            treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
            orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem._id else []
            if orgStructureIdList:
                movingOSIdList = db.getIdList(tableOS, tableOS['id'], [tableOS['id'].inlist(orgStructureIdList), tableOS['type'].ne(4), tableOS['deleted'].eq(0)])
                receivedOSIdList = db.getIdList(tableOS, tableOS['id'], [tableOS['id'].inlist(orgStructureIdList), tableOS['type'].eq(4), tableOS['deleted'].eq(0)])
        if indexLocalClient == 2:
            if orgStructureIdList:
                if receivedOSIdList:
                    findReceivedNoEnd(orgStructureIdList, dateFeed, accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList, endDateTime = filterEndDate, begDateTimeFilter = begDateTime, endDateTimeFilter = endDateTime)
                if movingOSIdList:
                    getDataMoving(movingOSIdList, indexSex, ageFor, ageTo, permanent, type, bedProfile, presenceDay, codeAttachType, finance, feed, dateFeed, indexLocalClient, accountingSystemId, filterClientId, filterEventId, codeBeds, defaultOrgStructureEventTypeIdList, begDateTime, endDateTime)
            else:
                getDataMoving([], indexSex, ageFor, ageTo, permanent, type, bedProfile, presenceDay, codeAttachType, finance, feed, dateFeed, indexLocalClient, accountingSystemId, filterClientId, filterEventId, codeBeds, defaultOrgStructureEventTypeIdList, begDateTime, endDateTime)
        elif indexLocalClient == 1:
            if orgStructureIdList:
                if movingOSIdList:
                   getDataMoving(movingOSIdList, indexSex, ageFor, ageTo, permanent, type, bedProfile, presenceDay, codeAttachType, finance, feed, dateFeed, indexLocalClient, accountingSystemId, filterClientId, filterEventId, codeBeds, defaultOrgStructureEventTypeIdList, begDateTime, endDateTime)
            else:
                getDataMoving([], indexSex, ageFor, ageTo, permanent, type, bedProfile, presenceDay, codeAttachType, finance, feed, dateFeed, indexLocalClient, accountingSystemId, filterClientId, filterEventId, codeBeds, defaultOrgStructureEventTypeIdList, begDateTime, endDateTime)
        else:
            if orgStructureIdList:
                if receivedOSIdList:
                    findReceivedNoEnd(receivedOSIdList, dateFeed, accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList, endDateTime = filterEndDate, begDateTimeFilter = begDateTime, endDateTimeFilter = endDateTime)#, True)
                if movingOSIdList:
                    getDataMoving(movingOSIdList, indexSex, ageFor, ageTo, permanent, type, bedProfile, presenceDay, codeAttachType, finance, feed, dateFeed, indexLocalClient, accountingSystemId, filterClientId, filterEventId, codeBeds, defaultOrgStructureEventTypeIdList, begDateTime, endDateTime)
            else:
                findReceivedNoEnd([], dateFeed, accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList, endDateTime = filterEndDate, begDateTimeFilter = begDateTime, endDateTimeFilter = endDateTime)
                getDataMoving([], indexSex, ageFor, ageTo, permanent, type, bedProfile, presenceDay, codeAttachType, finance, feed, dateFeed, indexLocalClient, accountingSystemId, filterClientId, filterEventId, codeBeds, defaultOrgStructureEventTypeIdList, begDateTime, endDateTime)

    def getClientId(self, row):
        return self.items[row][self.clientIdColumn]

    def getEventId(self, row):
        return self.items[row][self.eventColumn]

    def getPatronId(self, row):
        return self.items[row][self.patronIdColumn]

    def getReceivedDate(self, row):
        return self.items[row][self.receivedDateColumn]

    def getActionId(self, row):
        return self.items[row][self.actionIdColumn]

    def getActionTypeId(self, row):
        return self.items[row][self.actionTypeIdColumn]

    def getSetDate(self, row):
        return self.items[row][self.setDateColumn]

    def getEndDate(self, row):
        return self.items[row][self.actionEndDateColumn]

    def getPersonName(self, row):
        return self.items[row][self.namePersonColumn]

    def getBegDays(self):
        return self.begDays


    def getfeedTextValueItem(self, eventId, dateFeed, typeFeed):
        db = QtGui.qApp.db
        tableEventFeed = db.table('Event_Feed')
        cond = [tableEventFeed['event_id'].eq(eventId),
                tableEventFeed['deleted'].eq(0),
                tableEventFeed['typeFeed'].eq(typeFeed),
                tableEventFeed['date'].dateEq(dateFeed)]
        records = db.getRecordList(tableEventFeed, 'diet_id', cond)
        dietIdList = set([forceRef(record.value('diet_id')) for record in records])
        if len(dietIdList) == 1:
            dietId = dietIdList.pop()
            return db.translate('rbDiet', 'id', dietId, 'code')
        return QVariant()


class CReceivedModel(CMonitoringModel):
    column = [u'С', u'И', u'Д', u'П', u'Номер', u'Карта', u'ФИО', u'Пол', u'Дата рождения', u'Госпитализирован',
    u'Поступил', u'Выбыл', u'MKB', u'Профиль', u'Подразделение', u'Лечащий врач', u'Гражданство',
    u'Место вызова', u'М', u'Путевка', u'Субъект', u'Район', u'Направитель']
    eventColumn = 23
    MKBColumn = 12
    actionIdColumn = 30

    def __init__(self, parent):
        CMonitoringModel.__init__(self, parent)
        self.items = []
        self._cols = []

    def columnCount(self, index = None):
        return 23

    def getEventId(self, row):
        return self.items[row][self.eventColumn]

    def getActionId(self, row):
        return self.items[row][self.actionIdColumn]

    def cols(self):
        self._cols = [CCol(u'Статус наблюдения',     ['statusObservation'], 20, 'l'),
                      CCol(u'Код ИФ',                ['nameFinance'], 20, 'l'),
                      CCol(u'Договор',               ['contract'], 20, 'l'),
                      CCol(u'Питание',               ['feed'], 20, 'l'),
                      CCol(u'Номер',                 ['client_id'], 20, 'l'),
                      CCol(u'Карта',                 ['externalId'], 20, 'l'),
                      CCol(u'ФИО',                   ['lastName', 'firstName', 'patrName'], 30, 'l'),
                      CCol(u'Пол',                   ['sex'], 15, 'l'),
                      CCol(u'Дата рождения',         ['birthDate'], 20, 'l'),
                      CCol(u'Госпитализирован',      ['begDateReceived'], 20, 'l'),
                      CCol(u'Поступил',              ['begDate'], 20, 'l'),
                      CCol(u'Выбыл',                 ['endDate'], 20, 'l'),
                      CCol(u'MKB',                   ['MKB'], 20, 'l'),
                      CCol(u'Профиль',               ['profileName'], 30, 'l'),
                      CCol(u'Подразделение',         ['nameOS'], 30, 'l'),
                      CCol(u'Лечащий врач',         ['namePerson'], 30, 'l'),
                      CCol(u'Гражданство',           ['citizenship'], 30, 'l'),
                      CCol(u'Место вызова',          ['placeCallValue'], 30, 'l'),
                      CCol(u'Место нахождения учетного документа',['hospDocumentLocation'], 30, 'l'),
                      CCol(u'Путевка',               ['voucher'], 20, 'l'),
                      CCol(u'Субъект',               ['srcCity'], 20, 'l'),
                      CCol(u'Район',                 ['srcRegion'], 20, 'l'),
                      CCol(u'Направитель',           ['srcOrg'], 20, 'l'),
                      ]
        return self._cols

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
            elif role == Qt.ToolTipRole:
                if section == 0:
                    return QVariant(u'Статус наблюдения пациента')
                elif section == 1:
                    return QVariant(u'Источник финансирования (код)')
                elif section == 2:
                    return QVariant(u'Договор')
                elif section == 3:
                    return QVariant(u'Питание')
                elif section == self.MKBColumn:
                    return QVariant(u'Диагноз направителя;Текущий диагноз')
                elif section == 18:
                    return QVariant(u'Место нахождения учетного документа')
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.BackgroundColorRole:
            if column == 0 and self.items[row][0]:
               return toVariant(QtGui.QColor(self.items[row][27]))
            elif len(forceString(self.items[row][12])) <= 0:
               return toVariant(QtGui.QColor(200, 230, 240))
            elif column == 1:
                colorFinance = self.items[row][len(self.items[row])-2]
                if colorFinance:
                    return toVariant(colorFinance)
            elif column == len(self.column)-2:
                docLocalColor = self.items[row][len(self.items[row])-3]
                if docLocalColor:
                    return toVariant(QtGui.QColor(docLocalColor))
        if role == Qt.DisplayRole:
            if column != 3:
                item = self.items[row]
                return toVariant(item[column])
            elif column == 3:
                return toVariant(self.feedTextValueItems[row])
        elif role == Qt.CheckStateRole:
            if column == 3:
                item = self.items[row]
                return toVariant(Qt.Checked if item[column] else Qt.Unchecked)
        elif role == Qt.ToolTipRole:
            if column == 0:
                item = self.items[row]
                return QVariant(item[0] + u' ' + item[26])
            elif column == 1:
                item = self.items[row]
                return QVariant(item[23] + u' ' + item[1])
            elif column == self.MKBColumn:
                return QVariant(u'Диагноз направителя;Текущий диагноз')
            elif column == 13:
                item = self.items[row]
                return QVariant(item[13] + u' ' + item[24])
        return QVariant()


    def loadData(self, dialogParams):
        self.items = []
        self.itemByName = {}
        self.feedTextValueItems = []
        filterBegDate = dialogParams.get('filterBegDate', None)
        filterEndDate = dialogParams.get('filterEndDate', None)
        filterBegTime = dialogParams.get('filterBegTime', None)
        filterEndTime = dialogParams.get('filterEndTime', None)
        if not filterBegTime.isNull():
            begDateTime = QDateTime(filterBegDate, filterBegTime)
            filterBegDate = begDateTime
        if not filterEndTime.isNull():
            endDateTime = QDateTime(filterEndDate, filterEndTime)
            filterEndDate = endDateTime
        indexSex = dialogParams.get('indexSex', 0)
        ageFor = dialogParams.get('ageFor', 0)
        ageTo = dialogParams.get('ageTo', 150)
        order = dialogParams.get('order', -1)
        eventTypeId = dialogParams.get('eventTypeId', None)
        placeCall = dialogParams.get('placeCall', '')
        orgStructureId = dialogParams.get('orgStructureId', None)
        profile = dialogParams.get('treatmentProfile', None)
        codeAttachType = dialogParams.get('codeAttachType', None)
        indexLocalClient = dialogParams.get('indexLocalClient', None)
        finance = dialogParams.get('finance', None)
        contractId = dialogParams.get('contractId', None)
        feed = dialogParams.get('feed', None)
        dateFeed = dialogParams.get('dateFeed', None)
        personId = dialogParams.get('personId', None)
        accountingSystemId = dialogParams.get('accountingSystemId', None)
        filterClientId = dialogParams.get('filterClientId', None)
        filterEventId = dialogParams.get('filterEventId', None)
        statusObservation = dialogParams.get('statusObservation', None)
        index = dialogParams.get('receivedIndex', 0)
        defaultOrgStructureEventTypeIdList = dialogParams.get('defaultOrgStructureEventTypeIdList', [])
        deliverBy = dialogParams.get('deliverBy', None)
        srcCity =  dialogParams.get('srcCity', None)
        srcRegion =  dialogParams.get('srcRegion', None)
        relegateOrg = dialogParams.get('srcOrg', None)
        MKBSrcFilter = dialogParams['MKBSrcFilter']
        MKBSrcFrom   = dialogParams['MKBSrcFrom']
        MKBSrcTo     = dialogParams['MKBSrcTo']
        MKBFilter = dialogParams['MKBFilter']
        MKBFrom   = dialogParams['MKBFrom']
        MKBTo     = dialogParams['MKBTo']
        voucherSerial = dialogParams['voucherSerial']
        voucherNumber = dialogParams['voucherNumber']

        self.statusObservation = statusObservation
        if orgStructureId:
            treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
            orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem._id else []
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableEV = db.table('Event_Voucher')
        tableClient = db.table('Client')
        tableOS = db.table('OrgStructure')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableAPOS = db.table('ActionProperty_OrgStructure')
        tableClientAttach = db.table('ClientAttach')
        tableRBAttachType = db.table('rbAttachType')
        tableContract = db.table('Contract')
        tableRBFinance = db.table('rbFinance')
        tableRBFinanceBC = db.table('rbFinance').alias('rbFinanceByContract')
        tableEvent_Feed = db.table('Event_Feed')
        tableStatusObservation= db.table('Client_StatusObservation')
        tableOrg = db.table('Organisation')
        tablekladrOKATO = db.table('kladr.OKATO')

        def getOrderBy():
            orderBY = u'Client.lastName ASC'
            for key, value in self.headerSortingCol.items():
                if not value:
                    ASC = u'ASC'
                else:
                    ASC = u'DESC'
                if key == 4:
                   orderBY = u'Event.client_id %s'%(ASC)
                elif key == 5:
                    orderBY = u'CAST(Event.externalId AS SIGNED) %s'%(ASC)
                elif key == 6:
                    orderBY = u'Client.lastName %s'%(ASC)
                elif key == 9:
                    orderBY = u'Event.setDate %s'%(ASC)
                elif key == 10:
                    orderBY = u'Action.begDate %s'%(ASC)
                elif key == 11:
                    orderBY = u'Event.execDate %s, Event.setDate %s'%(ASC,  ASC)
                elif key == 14:
                    orderBY = u'nameOrgStructure %s'%(ASC)
                elif key == 15:
                    orderBY = u'namePerson %s'%(ASC)
                elif key == 19:
                    orderBY = u'Event_Voucher.serial, Event_Voucher.number %s'%(ASC)
            return orderBY

        def findMovingAfterReceived(filterBegDate = None, filterEndDate = None, indexLocalClient = 0, dateFeed = None, orgStructureIdList = [], accountingSystemId = None, filterClientId = None, filterEventId = None, defaultOrgStructureEventTypeIdList=[]):
            nameProperty = u'Отделение пребывания'
            cols = [tableAction['id'],
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableAction['MKB'].alias(u'actionMKB'),
                    tableEvent['setDate'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    tableEV['serial'].alias('serialVoucher'),
                    tableEV['number'].alias('numberVoucher'),
                    tableEvent['relegateOrg_id'],
                    tableEvent['directionCity'],
                    tablekladrOKATO['NAME'].alias('directionRegion'),
                    tableOrg['shortName'].alias('relegateOrg'),
                    tablePWS['name'].alias('namePerson')
                    ]
            cols.append(getReceivedMKB())
            cols.append(getHospDocumentLocationInfo())
            cols.append(getReceivedBegDate(getActionTypeIdListByFlatCode(u'received%')))
            cols.append(u'IF(OrgStructure.id IS NOT NULL AND OrgStructure.deleted=0, OrgStructure.name, NULL) AS nameOS')
            if not dateFeed:
                dateFeed = QDate.currentDate().addDays(1)
            cols.append(getEventFeedId(u'', tableEvent_Feed['date'].formatValue(dateFeed), u''' AS countEventFeedId'''))
            cols.append(getDietCode(u'0', db.formatDate(dateFeed), u''' AS clientDiet'''))
            cols.append(getOSHBP())
            cols.append(getStatusObservation())
            cols.append('(SELECT name from rbSocStatusType where code = getClientCitizenship(Client.id, Action.begDate)) as citizenship')
            cols.append('%s as placeCallValue'%getStringPropertyValue(u'Место вызова'))
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tableEV, db.joinAnd([tableEV['event_id'].eq(tableEvent['id']), tableEV['deleted'].eq(0)]))
            queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            queryTable = queryTable.leftJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
            queryTable = queryTable.leftJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            queryTable = queryTable.leftJoin(tablekladrOKATO, tablekladrOKATO['CODE'].eq(tableEvent['directionRegion']))
            cond = [tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'moving%')),
                    tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableAP['deleted'].eq(0),
                    tableAPT['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tableAP['action_id'].eq(tableAction['id'])
                   ]
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if srcCity:
                cond.append(tableEvent['directionCity'].eq(srcCity))
            if srcRegion:
                cond.append(tableEvent['directionRegion'].eq(srcRegion))
            if MKBSrcFilter:
                cond.append('Event.directionMKB >= \'%s\' AND Event.directionMKB <= \'%s\''%(MKBSrcFrom, MKBSrcTo))
            if voucherSerial:
                cond.append(tableEV['serial'].eq(voucherSerial))
            if voucherNumber:
                cond.append(tableEV['number'].eq(voucherNumber))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            if placeCall and placeCall != u'не определено':
                cond.append(getActionTypeStringPropertyValue(u'Место вызова', u'received%', placeCall))
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'8\')))''')
            cond.append(tableAPT['name'].like(nameProperty))
            if defaultOrgStructureEventTypeIdList:
                cond.append(tableEvent['eventType_id'].inlist(defaultOrgStructureEventTypeIdList))
            if personId:
               cond.append(tableEvent['execPerson_id'].eq(personId))
            if self.statusObservation:
                queryTable = queryTable.innerJoin(tableStatusObservation, tableStatusObservation['master_id'].eq(tableClient['id']))
                cond.append(tableStatusObservation['deleted'].eq(0))
                cond.append(tableStatusObservation['statusObservationType_id'].eq(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate.currentDate()
                cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].eq(filterBegDate)]))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            if orgStructureIdList:
                cond.append(tableOS['deleted'].eq(0))
                cond.append(tableAPOS['value'].inlist(orgStructureIdList))
            if feed == 1:
                cond.append('NOT %s'%(getEventFeedId(u'',tableEvent_Feed['date'].formatValue(dateFeed))))
            elif feed == 2:
                cond.append('%s'%(getEventFeedId(u'',tableEvent_Feed['date'].formatValue(dateFeed), alias=u'', refusalToEat = 0)))
            elif feed == 3:
                cond.append('%s'%(getEventFeedId(u'',tableEvent_Feed['date'].formatValue(dateFeed), alias=u'', refusalToEat = 1)))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() == 2:
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.code, NULL)) AS codeFinance')
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.name, NULL)) AS nameFinance')
                cols.append(getClientPolicyForDate())
                if finance:
                    cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(finance), str(finance)))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
            elif QtGui.qApp.defaultHospitalBedFinanceByMoving() == 1:
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, NULL) AS nameFinance')
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                if finance:
                    cond.append('''(Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s)'''%(str(finance)))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                cols.append(getActionClientPolicyForDate())
            else:
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                cols.append(getContractClientPolicyForDate())
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if profile:
                cond.append(getHospitalBedProfile(profile))
            if deliverBy:
                cond.append(getDeliverByCond(deliverBy))
            orderBy = getOrderBy()
            recordsMoving = db.getRecordList(queryTable, cols, cond, orderBy)
            for record in recordsMoving:
                countEventFeedId = forceBool(record.value('countEventFeedId'))
                if (feed == 1 and not countEventFeedId) or (feed == 2 and countEventFeedId) or not feed or feed == 3:
                    statusObservation = forceString(record.value('statusObservation')).split('|')
                    statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                    statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                    statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                    statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                    statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                    begDate = forceDate(record.value('begDate'))
                    policyEndDate = forceDate(record.value('policyEndDate'))
                    colorFinance = None
                    if policyEndDate:
                        if begDate < policyEndDate and begDate.addDays(3) >= policyEndDate:
                           colorFinance = QtGui.QColor(Qt.yellow)
                        elif begDate >= policyEndDate:
                            colorFinance = QtGui.QColor(Qt.red)
                    nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                    documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                    hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                    documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                    actionMKB = forceString(record.value('actionMKB'))
                    MKB = forceString(record.value('MKB'))
                    if actionMKB or MKB:
                        strMKB = (actionMKB if actionMKB else u'?') + u';' + (MKB if MKB else u'?')
                    else:
                        strMKB = u''
                    serialVoucher = forceStringEx(record.value('serialVoucher'))
                    numberVoucher = forceStringEx(record.value('numberVoucher'))
                    relegateOrgName = forceStringEx(record.value('relegateOrg'))
                    directionCity = getCityName(forceStringEx(record.value('directionCity')))
                    directionRegion = forceStringEx(record.value('directionRegion'))
                    item = [statusObservationName,
                            # statusObservationCode
                            forceString(record.value('nameFinance')),
                            nameContract,
                            countEventFeedId,
                            forceRef(record.value('client_id')),
                            forceString(record.value('externalId')),
                            forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                            self.sex[forceInt(record.value('sex'))],
                            forceString(forceDate(record.value('birthDate'))) + u'(' + forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate')))) + u')',
                            forceDateTime(record.value('receivedBegDate')).toString('dd.MM.yyyy hh:mm'),
                            forceDateTime(record.value('begDate')).toString('dd.MM.yyyy hh:mm'),
                            forceDateTime(record.value('endDate')).toString('dd.MM.yyyy hh:mm'),
                            strMKB,
                            forceString(record.value('profileName')),
                            forceString(record.value('nameOrgStructure')),
                            forceString(record.value('namePerson')),
                            forceString(record.value('citizenship')),
                            forceString(record.value('placeCallValue')),
                            hospDocumentLocation,
                            ((serialVoucher + u' ') if serialVoucher else u'') + numberVoucher,
                            directionCity,
                            directionRegion,
                            relegateOrgName,
                            forceRef(record.value('eventId')),
                            forceString(record.value('codeFinance')),
                            '', #bedName
                            statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                            statusObservationColor,
                            documentLocationColor,
                            colorFinance,
                            forceRef(record.value('id')) # actionId
                            ]
                    self.feedTextValueItems.append(forceString(record.value('clientDiet')))
                    self.items.append(item)
                    eventId = forceRef(record.value('eventId'))
                    dict = {
                            'observationCode': statusObservationCode,
                            'finance': forceString(record.value('nameFinance')),
                            'clientFeed': countEventFeedId,
                            'contract': nameContract,
                            'bedCode': '',
                            'orgStructure': forceString(record.value('nameOrgStructure')),
                            'person': forceString(record.value('namePerson')),
                            'financeCode': forceString(record.value('codeFinance')),
                            'bedName': '',
                            'observationName': statusObservationName,
                            'observationColor': statusObservationColor,
                            'setDate': CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))), #.toString('dd.MM.yyyy hh:mm'),
                            'begDate': CDateTimeInfo(forceDateTime(record.value('begDate'))), #.toString('dd.MM.yyyy hh:mm'),
                            'endDate': CDateTimeInfo(forceDateTime(record.value('endDate'))),
                            'profile' : forceString(record.value('profileName'))
                        }
                    self.itemByName[eventId] = dict
            return None

        def findReceived(filterBegDate = None, filterEndDate = None, orgStructureIdList = [], dateFeed = None, accountingSystemId = None, filterClientId = None, filterEventId = None, defaultOrgStructureEventTypeIdList=[], noMovingAndLeaved = False, isAmbulanceReceived = False):
            cols = [tableAction['id'],
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableAction['MKB'].alias(u'actionMKB'),
                    tableEvent['setDate'],
                    tableEvent['execDate'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    getDataOrgStructureName(u'Направлен в отделение'),
                    tableEV['serial'].alias('serialVoucher'),
                    tableEV['number'].alias('numberVoucher'),
                    tableEvent['relegateOrg_id'],
                    tableEvent['directionCity'],
                    tablekladrOKATO['NAME'].alias('directionRegion'),
                    tableOrg['shortName'].alias('relegateOrg'),
                    tablePWS['name'].alias('namePerson')
                    ]
            cols.append(getReceivedMKB())
            cols.append(getReceivedBegDate(getActionTypeIdListByFlatCode(u'received%')))
            cols.append(getOSHBP())
            cols.append('(SELECT name from rbSocStatusType where code = getClientCitizenship(Client.id, Action.begDate)) as citizenship')
            cols.append('%s as placeCallValue'%getStringPropertyValue(u'Место вызова'))
            if not dateFeed:
                dateFeed = QDate.currentDate().addDays(1)
            cols.append(getEventFeedId(u'', db.formatDate(dateFeed), u''' AS countEventFeedId'''))
            cols.append(getDietCode(u'0', db.formatDate(dateFeed), u''' AS clientDiet'''))
            cols.append(getStatusObservation())
            cols.append(getHospDocumentLocationInfo())
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tableEV, db.joinAnd([tableEV['event_id'].eq(tableEvent['id']), tableEV['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            queryTable = queryTable.leftJoin(tablekladrOKATO, tablekladrOKATO['CODE'].eq(tableEvent['directionRegion']))
            cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'received%')),
                     tableAction['deleted'].eq(0),
                     tableEvent['deleted'].eq(0),
                     tableClient['deleted'].eq(0),
                     tableAction['endDate'].isNotNull()
                   ]
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if srcCity:
                cond.append(tableEvent['directionCity'].eq(srcCity))
            if srcRegion:
                cond.append(tableEvent['directionRegion'].eq(srcRegion))
            if MKBSrcFilter:
                cond.append('Event.directionMKB >= \'%s\' AND Event.directionMKB <= \'%s\''%(MKBSrcFrom, MKBSrcTo))
            if voucherSerial:
                cond.append(tableEV['serial'].eq(voucherSerial))
            if voucherNumber:
                cond.append(tableEV['number'].eq(voucherNumber))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            if placeCall and placeCall != u'не определено':
                cond.append(getActionTypeStringPropertyValue(u'Место вызова', u'received%', placeCall))
            if profile:
                cond.append(getPropertyAPHBP(profile, False))
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'8\')))''')
            if defaultOrgStructureEventTypeIdList:
                cond.append(tableEvent['eventType_id'].inlist(defaultOrgStructureEventTypeIdList))
            if personId:
               cond.append(tableEvent['execPerson_id'].eq(personId))
            if self.statusObservation:
                queryTable = queryTable.innerJoin(tableStatusObservation, tableStatusObservation['master_id'].eq(tableClient['id']))
                cond.append(tableStatusObservation['deleted'].eq(0))
                cond.append(tableStatusObservation['statusObservationType_id'].eq(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate.currentDate()
                cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].eq(filterBegDate)]))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            if not isAmbulanceReceived:
                queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
                queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
                queryTable = queryTable.innerJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
                queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
                cond.append(tableAPT['name'].like(u'Направлен в отделение'))
                cond.append(tableAP['deleted'].eq(0))
                cond.append(tableAPT['deleted'].eq(0))
                cond.append(tableAP['action_id'].eq(tableAction['id']))
                cond.append(tableOS['deleted'].eq(0))
                if orgStructureIdList:
                    cond.append(tableAPOS['value'].inlist(orgStructureIdList))
            else:
                cond.append('''NOT %s'''% (getActionPropertyTypeName(u'Направлен в отделение')))
            if noMovingAndLeaved:
                movingIdList = getActionTypeIdListByFlatCode(u'moving%')
                leavedIdList = getActionTypeIdListByFlatCode(u'leaved%')
                cond.append('''NOT EXISTS(SELECT AM.id FROM Action AS AM WHERE AM.actionType_id IN (%s) AND AM.deleted=0 AND
AM.event_id = Event.id)'''%(','.join(forceString(movingId) for movingId in movingIdList if movingId)))
                if not isAmbulanceReceived:
                    cond.append('''NOT EXISTS(SELECT AM.id FROM Action AS AM WHERE AM.actionType_id IN (%s) AND AM.deleted=0 AND
AM.event_id = Event.id)'''%(','.join(forceString(leavedId) for leavedId in leavedIdList if leavedId)))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() in (0, 2):
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            cols.append(getContractClientPolicyForDate())
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            if feed == 1:
                cond.append('NOT %s'%(getEventFeedId(u'',db.formatDate(dateFeed))))
            elif feed == 2:
                cond.append('%s'%(getEventFeedId(u'',db.formatDate(dateFeed), alias=u'', refusalToEat = 0)))
            elif feed == 3:
                cond.append('%s'%(getEventFeedId(u'',db.formatDate(dateFeed), alias=u'', refusalToEat = 1)))
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if deliverBy:
                cond.append(getDeliverByCond(deliverBy))
            if profile:
                cond.append(getHospitalBedProfile(profile))
            orderBy = getOrderBy()
            recordsReceived = db.getRecordList(queryTable, cols, cond, orderBy)
            for record in recordsReceived:
                countEventFeedId = forceBool(record.value('countEventFeedId'))
                if (feed == 1 and not countEventFeedId) or (feed == 2 and countEventFeedId) or not feed or feed == 3:
                    statusObservation = forceString(record.value('statusObservation')).split('|')
                    statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                    statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                    statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                    statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                    statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                    nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                    begDate = forceDateTime(record.value('begDate'))
                    policyEndDate = forceDate(record.value('policyEndDate'))
                    colorFinance = None
                    if policyEndDate:
                        if forceDate(begDate) < policyEndDate and forceDate(begDate).addDays(3) >= policyEndDate:
                           colorFinance = QtGui.QColor(Qt.yellow)
                        elif forceDate(begDate) >= policyEndDate:
                            colorFinance = QtGui.QColor(Qt.red)
                    documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                    hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                    documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                    actionMKB = forceString(record.value('actionMKB'))
                    MKB = forceString(record.value('MKB'))
                    if actionMKB or MKB:
                        strMKB = (actionMKB if actionMKB else u'?') + u';' + (MKB if MKB else u'?')
                    else:
                        strMKB = u''
                    serialVoucher = forceStringEx(record.value('serialVoucher'))
                    numberVoucher = forceStringEx(record.value('numberVoucher'))
                    relegateOrgName = forceStringEx(record.value('relegateOrg'))
                    directionCity = getCityName(forceStringEx(record.value('directionCity')))
                    directionRegion = forceStringEx(record.value('directionRegion'))
                    item = [statusObservationName,
                            #statusObservationCode,
                            forceString(record.value('nameFinance')),
                            nameContract,
                            countEventFeedId,
                            forceRef(record.value('client_id')),
                            forceString(record.value('externalId')),
                            forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                            self.sex[forceInt(record.value('sex'))],
                            forceString(forceDate(record.value('birthDate'))) + u'(' + forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate')))) + u')',
                            forceDateTime(record.value('receivedBegDate')).toString('dd.MM.yyyy hh:mm'),
                            begDate,
                            forceDateTime(record.value('execDate')).toString('dd.MM.yyyy hh:mm'),
                            strMKB,
                            forceString(record.value('profileName')),
                            forceString(record.value('nameOrgStructure')),
                            forceString(record.value('namePerson')),
                            forceString(record.value('citizenship')),
                            forceString(record.value('placeCallValue')),
                            hospDocumentLocation,
                            ((serialVoucher + u' ') if serialVoucher else u'') + numberVoucher,
                            directionCity,
                            directionRegion,
                            relegateOrgName,
                            forceRef(record.value('eventId')),
                            forceString(record.value('codeFinance')),
                            '',
                            statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                            statusObservationColor,
                            documentLocationColor,
                            colorFinance,
                            forceRef(record.value('id')) # actionId
                            ]
                    self.feedTextValueItems.append(forceString(record.value('clientDiet')))
                    self.items.append(item)
                    eventId = forceRef(record.value('eventId'))
                    dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'clientFeed': countEventFeedId,
                        'contract': nameContract,
                        'bedCode': '',
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': '',
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor,
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'person': forceString(record.value('namePerson')),
                        'setDate': CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))),
                        'begDate': CDateTimeInfo(forceDateTime(record.value('begDate'))),
                        'endDate': CDateTimeInfo(forceDateTime(record.value('execDate'))),
                        'profile' : forceString(record.value('profileName'))
                    }
                    self.itemByName[eventId] = dict


        def findReceivedWithoutSpecification(filterBegDate = None, filterEndDate = None, orgStructureIdList = [], dateFeed = None, accountingSystemId = None, filterClientId = None, filterEventId = None, defaultOrgStructureEventTypeIdList=[]):
            cols = [tableAction['id'],
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableAction['MKB'].alias(u'actionMKB'),
                    tableEvent['setDate'],
                    tableEvent['execDate'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    getDataOrgStructureName(u'Направлен в отделение'),
                    tableEV['serial'].alias('serialVoucher'),
                    tableEV['number'].alias('numberVoucher'),
                    tableEvent['relegateOrg_id'],
                    tableEvent['directionCity'],
                    tablekladrOKATO['NAME'].alias('directionRegion'),
                    tableOrg['shortName'].alias('relegateOrg'),
                    tablePWS['name'].alias('namePerson')
                    ]
            cols.append(getReceivedMKB())
            cols.append(getReceivedBegDate(getActionTypeIdListByFlatCode(u'received%')))
            cols.append(getOSHBP())
            cols.append(getHospDocumentLocationInfo())
            cols.append('(SELECT name from rbSocStatusType where code = getClientCitizenship(Client.id, Action.begDate)) as citizenship')
            cols.append('%s as placeCallValue'%getStringPropertyValue(u'Место вызова'))
            if not dateFeed:
                dateFeed = QDate.currentDate().addDays(1)
            cols.append(getEventFeedId(u'', db.formatDate(dateFeed), u''' AS countEventFeedId'''))
            cols.append(getDietCode(u'0', db.formatDate(dateFeed), u''' AS clientDiet'''))
            cols.append(getStatusObservation())
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.leftJoin(tableEV, db.joinAnd([tableEV['event_id'].eq(tableEvent['id']), tableEV['deleted'].eq(0)]))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            queryTable = queryTable.leftJoin(tablekladrOKATO, tablekladrOKATO['CODE'].eq(tableEvent['directionRegion']))
            cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'received%')),
                     tableAction['deleted'].eq(0),
                     tableEvent['deleted'].eq(0),
                     tableClient['deleted'].eq(0),
                     #tableAction['endDate'].isNotNull()
                   ]
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            if placeCall and placeCall != u'не определено':
               cond.append(getStringProperty(u'Место вызова', u'''APS.value %s'''%(updateLIKE(placeCall))))
            if profile:
                cond.append(getPropertyAPHBP(profile, False))
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'8\')))''')
            if defaultOrgStructureEventTypeIdList:
                cond.append(tableEvent['eventType_id'].inlist(defaultOrgStructureEventTypeIdList))
            if personId:
               cond.append(tableEvent['execPerson_id'].eq(personId))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if srcCity:
                cond.append(tableEvent['directionCity'].eq(srcCity))
            if srcRegion:
                cond.append(tableEvent['directionRegion'].eq(srcRegion))
            if MKBSrcFilter:
                cond.append('Event.directionMKB >= \'%s\' AND Event.directionMKB <= \'%s\''%(MKBSrcFrom, MKBSrcTo))
            if voucherSerial:
                cond.append(tableEV['serial'].eq(voucherSerial))
            if voucherNumber:
                cond.append(tableEV['number'].eq(voucherNumber))
            if self.statusObservation:
                queryTable = queryTable.innerJoin(tableStatusObservation, tableStatusObservation['master_id'].eq(tableClient['id']))
                cond.append(tableStatusObservation['deleted'].eq(0))
                cond.append(tableStatusObservation['statusObservationType_id'].eq(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate.currentDate()
                cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].eq(filterBegDate)]))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            if orgStructureIdList:
                cond.append(tableAPOS['value'].inlist(orgStructureIdList))
                queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
                queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
                queryTable = queryTable.innerJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
                queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
                cond.append(tableAPT['name'].like(u'Направлен в отделение'))
                cond.append(tableAP['deleted'].eq(0))
                cond.append(tableAPT['deleted'].eq(0))
                cond.append(tableAP['action_id'].eq(tableAction['id']))
                cond.append(tableOS['deleted'].eq(0))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() in (0, 2):
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            cols.append(getContractClientPolicyForDate())
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            if feed == 1:
                cond.append('NOT %s'%(getEventFeedId(u'',db.formatDate(dateFeed))))
            elif feed == 2:
                cond.append('%s'%(getEventFeedId(u'',db.formatDate(dateFeed), alias=u'', refusalToEat = 0)))
            elif feed == 3:
                cond.append('%s'%(getEventFeedId(u'',db.formatDate(dateFeed), alias=u'', refusalToEat = 1)))
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if deliverBy:
                cond.append(getDeliverByCond(deliverBy))
            if profile:
                cond.append(getHospitalBedProfile(profile))
            orderBy = getOrderBy()
            recordsReceived = db.getRecordList(queryTable, cols, cond, orderBy)
            for record in recordsReceived:
                countEventFeedId = forceBool(record.value('countEventFeedId'))
                if (feed == 1 and not countEventFeedId) or (feed == 2 and countEventFeedId) or not feed or feed == 3:
                    statusObservation = forceString(record.value('statusObservation')).split('|')
                    statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                    statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                    statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                    statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                    statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                    nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                    begDate = forceDateTime(record.value('begDate'))
                    policyEndDate = forceDate(record.value('policyEndDate'))
                    colorFinance = None
                    if policyEndDate:
                        if forceDate(begDate) < policyEndDate and forceDate(begDate).addDays(3) >= policyEndDate:
                           colorFinance = QtGui.QColor(Qt.yellow)
                        elif forceDate(begDate) >= policyEndDate:
                            colorFinance = QtGui.QColor(Qt.red)
                    documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                    hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                    documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                    actionMKB = forceString(record.value('actionMKB'))
                    MKB = forceString(record.value('MKB'))
                    if actionMKB or MKB:
                        strMKB = (actionMKB if actionMKB else u'?') + u';' + (MKB if MKB else u'?')
                    else:
                        strMKB = u''
                    serialVoucher = forceStringEx(record.value('serialVoucher'))
                    numberVoucher = forceStringEx(record.value('numberVoucher'))
                    relegateOrgName = forceStringEx(record.value('relegateOrg'))
                    directionCity = getCityName(forceStringEx(record.value('directionCity')))
                    directionRegion = forceStringEx(record.value('directionRegion'))
                    item = [statusObservationName,
                            # statusObservationCode,
                            forceString(record.value('nameFinance')),
                            nameContract,
                            countEventFeedId,
                            forceRef(record.value('client_id')),
                            forceString(record.value('externalId')),
                            forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                            self.sex[forceInt(record.value('sex'))],
                            forceString(forceDate(record.value('birthDate'))) + u'(' + forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate')))) + u')',
                            forceDateTime(record.value('receivedBegDate')).toString('dd.MM.yyyy hh:mm'),
                            begDate,
                            forceDateTime(record.value('execDate')).toString('dd.MM.yyyy hh:mm'),
                            strMKB,
                            forceString(record.value('profileName')),
                            forceString(record.value('nameOrgStructure')),
                            forceString(record.value('namePerson')),
                            forceString(record.value('citizenship')),
                            forceString(record.value('placeCallValue')),
                            hospDocumentLocation,
                            ((serialVoucher + u' ') if serialVoucher else u'') + numberVoucher,
                            directionCity,
                            directionRegion,
                            relegateOrgName,
                            forceRef(record.value('eventId')),
                            forceString(record.value('codeFinance')),
                            '',
                            statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                            statusObservationColor,
                            documentLocationColor,
                            colorFinance,
                            forceRef(record.value('id')) # actionId
                            ]
                    self.feedTextValueItems.append(forceString(record.value('clientDiet')))
                    self.items.append(item)
                    eventId = forceRef(record.value('eventId'))
                    dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'clientFeed': countEventFeedId,
                        'contract': nameContract,
                        'bedCode': '',
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': '',
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor,
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'person': forceString(record.value('namePerson')),
                        'setDate': CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))),
                        'begDate': CDateTimeInfo(forceDateTime(record.value('begDate'))),
                        'endDate': CDateTimeInfo(forceDateTime(record.value('execDate'))),
                        'profile' : forceString(record.value('profileName'))
                    }
                    self.itemByName[eventId] = dict

        def findReceivedNoEnd(filterBegDate = None, filterEndDate = None, orgStructureIdList = [], dateFeed = None, orgStructureId = 0, accountingSystemId = None, filterClientId = None, filterEventId = None, defaultOrgStructureEventTypeIdList=[]):
            cols = [tableAction['id'],
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableAction['MKB'].alias(u'actionMKB'),
                    tableEvent['setDate'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    tableEV['serial'].alias('serialVoucher'),
                    tableEV['number'].alias('numberVoucher'),
                    tableEvent['relegateOrg_id'],
                    tableEvent['directionCity'],
                    tablekladrOKATO['NAME'].alias('directionRegion'),
                    tableOrg['shortName'].alias('relegateOrg'),
                    tablePWS['name'].alias('namePerson')
                    ]
            cols.append(getReceivedMKB())
            cols.append(getReceivedBegDate(getActionTypeIdListByFlatCode(u'received%')))
            cols.append(getOSHBP())
            cols.append(getHospDocumentLocationInfo())
            nameProperty = u'Направлен в отделение'
            cols.append(getDataOrgStructureName(nameProperty))
            if not dateFeed:
                dateFeed = QDate.currentDate().addDays(1)
            cols.append(getEventFeedId(u'', db.formatDate(dateFeed), u''' AS countEventFeedId'''))
            cols.append(getDietCode(u'0', db.formatDate(dateFeed), u''' AS clientDiet'''))
            cols.append(getStatusObservation())
            cols.append('(SELECT name from rbSocStatusType where code = getClientCitizenship(Client.id, Action.begDate)) as citizenship')
            cols.append('%s as placeCallValue'%getStringPropertyValue(u'Место вызова'))
            queryTable = tableAction.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tableEV, db.joinAnd([tableEV['event_id'].eq(tableEvent['id']), tableEV['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            queryTable = queryTable.leftJoin(tablekladrOKATO, tablekladrOKATO['CODE'].eq(tableEvent['directionRegion']))
            cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'received%')),
                     tableAction['deleted'].eq(0),
                     tableEvent['deleted'].eq(0),
                     tableClient['deleted'].eq(0),
                     #tableAction['endDate'].isNull()
                   ]
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            if placeCall and placeCall != u'не определено':
               cond.append(getStringProperty(u'Место вызова', u'''APS.value %s'''%(updateLIKE(placeCall))))
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'8\')))''')
            if defaultOrgStructureEventTypeIdList:
                cond.append(tableEvent['eventType_id'].inlist(defaultOrgStructureEventTypeIdList))
            if personId:
               cond.append(tableEvent['execPerson_id'].eq(personId))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if srcCity:
                cond.append(tableEvent['directionCity'].eq(srcCity))
            if srcRegion:
                cond.append(tableEvent['directionRegion'].eq(srcRegion))
            if MKBSrcFilter:
                cond.append('Event.directionMKB >= \'%s\' AND Event.directionMKB <= \'%s\''%(MKBSrcFrom, MKBSrcTo))
            if voucherSerial:
                cond.append(tableEV['serial'].eq(voucherSerial))
            if voucherNumber:
                cond.append(tableEV['number'].eq(voucherNumber))
            if profile:
                cond.append(getPropertyAPHBP(profile, False))
            if self.statusObservation:
                queryTable = queryTable.innerJoin(tableStatusObservation, tableStatusObservation['master_id'].eq(tableClient['id']))
                cond.append(tableStatusObservation['deleted'].eq(0))
                cond.append(tableStatusObservation['statusObservationType_id'].eq(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate.currentDate()
                cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].eq(filterBegDate)]))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            if orgStructureIdList:
                cond.append(db.joinOr([getDataOrgStructure(nameProperty, orgStructureIdList, False), getDataOrgStructure(u'Приемное отделение', orgStructureIdList, False)]))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() in (0, 2):
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            cols.append(getContractClientPolicyForDate())
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            if feed == 1:
                cond.append('NOT %s'%(getEventFeedId(u'',db.formatDate(dateFeed))))
            elif feed == 2:
                cond.append('%s'%(getEventFeedId(u'',db.formatDate(dateFeed), alias=u'', refusalToEat = 0)))
            elif feed == 3:
                cond.append('%s'%(getEventFeedId(u'',db.formatDate(dateFeed), alias=u'', refusalToEat = 1)))
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if deliverBy:
                cond.append(getDeliverByCond(deliverBy))
            if profile:
                cond.append(getHospitalBedProfile(profile))
            orderBy = getOrderBy()
            recordsReceived = db.getRecordList(queryTable, cols, cond, orderBy)
            for record in recordsReceived:
                countEventFeedId = forceBool(record.value('countEventFeedId'))
                if (feed == 1 and not countEventFeedId) or (feed == 2 and countEventFeedId) or not feed or feed == 3:
                    statusObservation = forceString(record.value('statusObservation')).split('|')
                    statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                    statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                    statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                    statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                    statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                    nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                    begDate = forceDateTime(record.value('begDate'))
                    policyEndDate = forceDate(record.value('policyEndDate'))
                    colorFinance = None
                    if policyEndDate:
                        if forceDate(begDate) < policyEndDate and forceDate(begDate).addDays(3) >= policyEndDate:
                           colorFinance = QtGui.QColor(Qt.yellow)
                        elif forceDate(begDate) >= policyEndDate:
                            colorFinance = QtGui.QColor(Qt.red)
                    documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                    hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                    documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                    actionMKB = forceString(record.value('actionMKB'))
                    MKB = forceString(record.value('MKB'))
                    if actionMKB or MKB:
                        strMKB = (actionMKB if actionMKB else u'?') + u';' + (MKB if MKB else u'?')
                    else:
                        strMKB = u''
                    serialVoucher = forceStringEx(record.value('serialVoucher'))
                    numberVoucher = forceStringEx(record.value('numberVoucher'))
                    relegateOrgName = forceStringEx(record.value('relegateOrg'))
                    directionCity = getCityName(forceStringEx(record.value('directionCity')))
                    directionRegion = forceStringEx(record.value('directionRegion'))
                    item = [statusObservationName,
                            # statusObservationCode,
                            forceString(record.value('nameFinance')),
                            nameContract,
                            countEventFeedId,
                            forceRef(record.value('client_id')),
                            forceString(record.value('externalId')),
                            forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                            self.sex[forceInt(record.value('sex'))],
                            forceString(forceDate(record.value('birthDate'))) + u'(' + forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate')))) + u')',
                            forceDateTime(record.value('receivedBegDate')).toString('dd.MM.yyyy hh:mm'),
                            begDate,
                            forceDateTime(record.value('endDate')).toString('dd.MM.yyyy hh:mm'),
                            strMKB,
                            forceString(record.value('profileName')),
                            forceString(record.value('nameOrgStructure')),
                            forceString(record.value('namePerson')),
                            forceString(record.value('citizenship')),
                            forceString(record.value('placeCallValue')),
                            hospDocumentLocation,
                            ((serialVoucher + u' ') if serialVoucher else u'') + numberVoucher,
                            directionCity,
                            directionRegion,
                            relegateOrgName,
                            forceRef(record.value('eventId')),
                            forceString(record.value('codeFinance')),
                            '',
                            statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                            statusObservationColor,
                            documentLocationColor,
                            colorFinance,
                            forceRef(record.value('id')) # actionId
                            ]
                    self.feedTextValueItems.append(forceString(record.value('clientDiet')))
                    self.items.append(item)
                    eventId = forceRef(record.value('eventId'))
                    dict = {
                            'observationCode': statusObservationCode,
                            'finance': forceString(record.value('nameFinance')),
                            'clientFeed': countEventFeedId,
                            'contract': nameContract,
                            'bedCode': '',
                            'orgStructure': forceString(record.value('nameOrgStructure')),
                            'financeCode': forceString(record.value('codeFinance')),
                            'bedName': '',
                            'observationName': statusObservationName,
                            'observationColor': statusObservationColor,
                            'setDate': CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))),
                            'begDate': CDateTimeInfo(forceDateTime(record.value('begDate'))),
                            'endDate': CDateTimeInfo(forceDateTime(record.value('endDate'))),
                            'profile' : forceString(record.value('profileName'))
                        }
                    self.itemByName[eventId] = dict

        if index == 0:
            self.items = []
            findReceived(filterBegDate, filterEndDate, orgStructureIdList, dateFeed, accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList)
        elif index == 1:
            self.items = []
            findMovingAfterReceived(filterBegDate, filterEndDate, indexLocalClient, dateFeed, orgStructureIdList, accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList)
        elif index == 2:
            self.items = []
            findReceivedNoEnd(filterBegDate, filterEndDate, orgStructureIdList, dateFeed, orgStructureId, accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList)
        elif index == 3:
            self.items = []
            findReceived(filterBegDate, filterEndDate, orgStructureIdList, dateFeed, accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList, True)
        elif index == 4:
            self.items = []
            findReceived(filterBegDate, filterEndDate, orgStructureIdList, dateFeed, accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList, True, True)
        elif index == 5:
            self.items = []
            findReceivedWithoutSpecification(filterBegDate, filterEndDate, orgStructureIdList, dateFeed, accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList)
        self.reset()


    def getClientId(self, row):
        return self.items[row][4]


class CTransferModel(CMonitoringModel):
    column = [u'С', u'И', u'Д', u'П', u'Номер', u'Карта', u'ФИО', u'Пол', u'Дата рождения', u'Госпитализирован',
    u'Поступил', u'Выбыл', u'MKB', u'Профиль', u'Подразделение', u'Переведен из', u'Лечащий врач',
    u'Гражданство', u'М', u'Путевка', u'Субъект', u'Район', u'Направитель']

    def __init__(self, parent):
        CMonitoringModel.__init__(self, parent)
        self.items = []
        self._cols = []
        self.transfer = 0


    def columnCount(self, index = None):
        return 23


    def cols(self):
        self._cols = [CCol(u'Статус наблюдения',     ['statusObservation'], 20, 'l'),
                      CCol(u'Код ИФ',                ['nameFinance'], 20, 'l'),
                      CCol(u'Договор',               ['contract'], 20, 'l'),
                      CCol(u'Питание',               ['feed'], 20, 'l'),
                      CCol(u'Номер',                 ['client_id'], 20, 'l'),
                      CCol(u'Карта',                 ['externalId'], 20, 'l'),
                      CCol(u'ФИО',                   ['lastName', 'firstName', 'patrName'], 30, 'l'),
                      CCol(u'Пол',                   ['sex'], 15, 'l'),
                      CCol(u'Дата рождения',         ['birthDate'], 20, 'l'),
                      CCol(u'Госпитализирован',      ['begDateReceived'], 20, 'l'),
                      CCol(u'Поступил',              ['begDate'], 20, 'l'),
                      CCol(u'Выбыл',                 ['endDate'], 20, 'l'),
                      CCol(u'MKB',                   ['MKB'], 20, 'l'),
                      CCol(u'Профиль',               ['profileName'], 30, 'l'),
                      CCol(u'Подразделение',         ['nameOS'], 30, 'l'),
                      CCol(u'Переведен в',           ['transferOS'], 30, 'l') if self.transfer else CCol(u'Переведен из', ['nameOS'], 30, 'l'),
                      CCol(u'Лечащий врач',         ['namePerson'], 30, 'l'),
                      CCol(u'Гражданство',           ['citizenship'], 30, 'l'),
                      CCol(u'Место нахождения учетного документа',['hospDocumentLocation'], 30, 'l'),
                      CCol(u'Путевка',               ['voucher'], 20, 'l'),
                      CCol(u'Субъект',               ['srcCity'], 20, 'l'),
                      CCol(u'Район',                 ['srcRegion'], 20, 'l'),
                      CCol(u'Направитель',           ['srcOrg'], 20, 'l'),
                      ]
        return self._cols


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
            elif role == Qt.ToolTipRole:
                if section == 0:
                    return QVariant(u'Статус наблюдения пациента')
                elif section == 1:
                    return QVariant(u'Источник финансирования (код)')
                elif section == 2:
                    return QVariant(u'Договор')
                elif section == 3:
                    return QVariant(u'Питание')
                elif section == 18:
                    return QVariant(u'Место нахождения учетного документа')
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.BackgroundColorRole:
            if column == 0 and self.items[row][0]:
               return toVariant(QtGui.QColor(self.items[row][27]))
            elif len(forceString(self.items[row][12])) <= 0:
               return toVariant(QtGui.QColor(200, 230, 240))
            elif column == 1:
                colorFinance = self.items[row][len(self.items[row])-1]
                if colorFinance:
                    return toVariant(colorFinance)
            elif column == len(self.column)-1:
                docLocalColor = self.items[row][len(self.items[row])-2]
                if docLocalColor:
                    return toVariant(QtGui.QColor(docLocalColor))
        if role == Qt.DisplayRole:
            if column != 3:
                item = self.items[row]
                return toVariant(item[column])
            elif column == 3:
                return toVariant(self.feedTextValueItems[row])
        elif role == Qt.CheckStateRole:
            if column == 3:
                item = self.items[row]
                return toVariant(Qt.Checked if item[column] else Qt.Unchecked)
        elif role == Qt.ToolTipRole:
            if column == 0:
                item = self.items[row]
                return QVariant(item[0] + u' ' + item[26])
            elif column == 1:
                item = self.items[row]
                return QVariant(item[24] + u' ' + item[1])
            elif column == 13:
                item = self.items[row]
                return QVariant(item[13] + u' ' + item[23])
        return QVariant()


    def loadData(self, dialogParams):
        self.items = []
        self.itemByName = {}
        self.feedTextValueItems = []
        filterBegDate = dialogParams.get('filterBegDate', None)
        filterEndDate = dialogParams.get('filterEndDate', None)
        filterBegTime = dialogParams.get('filterBegTime', None)
        filterEndTime = dialogParams.get('filterEndTime', None)
        if not filterBegTime.isNull():
            begDateTime = QDateTime(filterBegDate, filterBegTime)
            filterBegDate = begDateTime
        if not filterEndTime.isNull():
            endDateTime = QDateTime(filterEndDate, filterEndTime)
            filterEndDate = endDateTime
        indexSex = dialogParams.get('indexSex', 0)
        ageFor = dialogParams.get('ageFor', 0)
        ageTo = dialogParams.get('ageTo', 150)
        order = dialogParams.get('order', -1)
        eventTypeId = dialogParams.get('eventTypeId', None)
        orgStructureId = dialogParams.get('orgStructureId', None)
        permanent = dialogParams.get('permanent', None)
        type = dialogParams.get('type', None)
        profile = dialogParams.get('treatmentProfile', None)
        codeAttachType = dialogParams.get('codeAttachType', None)
        indexLocalClient = dialogParams.get('indexLocalClient', None)
        finance = dialogParams.get('finance', None)
        contractId = dialogParams.get('contractId', None)
        feed = dialogParams.get('feed', None)
        dateFeed = dialogParams.get('dateFeed', None)
        personId = dialogParams.get('personId', None)
        accountingSystemId = dialogParams.get('accountingSystemId', None)
        filterClientId = dialogParams.get('filterClientId', None)
        filterEventId = dialogParams.get('filterEventId', None)
        statusObservation = dialogParams.get('statusObservation', None)
        self.transfer = dialogParams.get('transfer', 0)
        stayOrgStructure = dialogParams.get('stayOrgStructure', 1)
        srcCity =  dialogParams.get('srcCity', None)
        srcRegion =  dialogParams.get('srcRegion', None)
        relegateOrg = dialogParams.get('srcOrg', None)
        MKBSrcFilter = dialogParams['MKBSrcFilter']
        MKBSrcFrom   = dialogParams['MKBSrcFrom']
        MKBSrcTo     = dialogParams['MKBSrcTo']
        MKBFilter = dialogParams['MKBFilter']
        MKBFrom   = dialogParams['MKBFrom']
        MKBTo     = dialogParams['MKBTo']
        voucherSerial = dialogParams['voucherSerial']
        voucherNumber = dialogParams['voucherNumber']
        scheduleId = dialogParams.get('scheduleId', None)
        self.statusObservation = statusObservation
        if orgStructureId:
            treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
            orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem._id else []
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableEV = db.table('Event_Voucher')
        tableClient = db.table('Client')
        tableOS = db.table('OrgStructure')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableAPOS = db.table('ActionProperty_OrgStructure')
        tableClientAttach = db.table('ClientAttach')
        tableRBAttachType = db.table('rbAttachType')
        tableContract = db.table('Contract')
        tableRBFinance = db.table('rbFinance')
        tableRBFinanceBC = db.table('rbFinance').alias('rbFinanceByContract')
        tableEvent_Feed = db.table('Event_Feed')
        tableStatusObservation= db.table('Client_StatusObservation')
        tableOrg = db.table('Organisation')
        tablekladrOKATO = db.table('kladr.OKATO')
        nameReceivedOS = u'Отделение пребывания'
        if self.transfer:
            nameTransferOS = u'Переведен в отделение'
            self.column[15] = u'Переведен в'
        else:
            nameTransferOS = u'Переведен из отделения'
            self.column[15] = u'Переведен из'
        def getOrderBy():
            orderBY = u'Client.lastName ASC'
            for key, value in self.headerSortingCol.items():
                if not value:
                    ASC = u'ASC'
                else:
                    ASC = u'DESC'
                if key == 4:
                   orderBY = u'Event.client_id %s'%(ASC)
                elif key == 5:
                    orderBY = u'CAST(Event.externalId AS SIGNED) %s'%(ASC)
                elif key == 6:
                    orderBY = u'Client.lastName %s'%(ASC)
                elif key == 9:
                    orderBY = u'Event.setDate %s'%(ASC)
                elif key == 10:
                    orderBY = u'Action.begDate %s'%(ASC)
                elif key == 11:
                    orderBY = u'Action.endDate %s, Action.begDate %s'%(ASC,  ASC)
                elif key == 16:
                    orderBY = u'namePerson %s'%(ASC)
                elif key == 19:
                    orderBY = u'Event_Voucher.serial, Event_Voucher.number %s'%(ASC)
            return orderBY

        def getTransfer(orgStructureIdList, filterBegDate = None, filterEndDate = None, indexSex = 0, ageFor = 0, ageTo = 150, permanent = None,
        type = None, profile = None, codeAttachType = None, finance = None, localClient = 0, feed = None, dateFeed = None, accountingSystemId = None,
        filterClientId = None, filterEventId = None):
            cols = [tableAction['id'],
                tableEvent['id'].alias('eventId'),
                tableEvent['client_id'],
                tableEvent['externalId'],
                tableClient['lastName'],
                tableClient['firstName'],
                tableClient['patrName'],
                tableClient['sex'],
                tableClient['birthDate'],
                tableAction['begDate'],
                tableAction['endDate'],
                tableEvent['setDate'],
                tableOS['name'].alias('nameFromOS'),
                tableContract['number'].alias('numberContract'),
                tableContract['date'].alias('dateContract'),
                tableContract['resolution'].alias('resolutionContract'),
                tableEV['serial'].alias('serialVoucher'),
                tableEV['number'].alias('numberVoucher'),
                tableEvent['relegateOrg_id'],
                tableEvent['directionCity'],
                tablekladrOKATO['NAME'].alias('directionRegion'),
                tableOrg['shortName'].alias('relegateOrg'),
                tablePWS['name'].alias('namePerson')
                ]
            cols.append(getMKB())
            cols.append(getHospDocumentLocationInfo())
            cols.append(getReceivedBegDate(getActionTypeIdListByFlatCode(u'received%')))
            if not dateFeed:
                dateFeed = QDate.currentDate().addDays(1)
            cols.append(getEventFeedId(u'', tableEvent_Feed['date'].formatValue(dateFeed), u''' AS countEventFeedId'''))
            cols.append(getDietCode(u'0', db.formatDate(dateFeed), u''' AS clientDiet'''))
            cols.append(getDataOrgStructureName(nameReceivedOS))
            cols.append(getOSHBP())
            cols.append(getStatusObservation())
            cols.append('(SELECT name from rbSocStatusType where code = getClientCitizenship(Client.id, Action.begDate)) as citizenship')
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tableEV, db.joinAnd([tableEV['event_id'].eq(tableEvent['id']), tableEV['deleted'].eq(0)]))
            queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            queryTable = queryTable.innerJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
            queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            queryTable = queryTable.leftJoin(tablekladrOKATO, tablekladrOKATO['CODE'].eq(tableEvent['directionRegion']))
            cond = [tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'moving%')),
                    tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableAP['deleted'].eq(0),
                    tableAPT['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tableAP['action_id'].eq(tableAction['id']),
                    tableOS['deleted'].eq(0)
                   ]
            if scheduleId:
                cond.append(isScheduleBeds(scheduleId))
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'8\')))''')
            cond.append(tableAPT['name'].like(nameTransferOS))
            if personId:
               cond.append(tableEvent['execPerson_id'].eq(personId))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if srcCity:
                cond.append(tableEvent['directionCity'].eq(srcCity))
            if srcRegion:
                cond.append(tableEvent['directionRegion'].eq(srcRegion))
            if MKBSrcFilter:
                cond.append('Event.directionMKB >= \'%s\' AND Event.directionMKB <= \'%s\''%(MKBSrcFrom, MKBSrcTo))
            if voucherSerial:
                cond.append(tableEV['serial'].eq(voucherSerial))
            if voucherNumber:
                cond.append(tableEV['number'].eq(voucherNumber))
            if self.statusObservation:
                queryTable = queryTable.innerJoin(tableStatusObservation, tableStatusObservation['master_id'].eq(tableClient['id']))
                cond.append(tableStatusObservation['deleted'].eq(0))
                cond.append(tableStatusObservation['statusObservationType_id'].eq(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate.currentDate()
                cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].eq(filterBegDate)]))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            if feed == 1:
                cond.append('NOT %s'%(getEventFeedId(u'',tableEvent_Feed['date'].formatValue(dateFeed))))
            elif feed == 2:
                cond.append('%s'%(getEventFeedId(u'',tableEvent_Feed['date'].formatValue(dateFeed), alias=u'', refusalToEat = 0)))
            elif feed == 3:
                cond.append('%s'%(getEventFeedId(u'',tableEvent_Feed['date'].formatValue(dateFeed), alias=u'', refusalToEat = 1)))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() == 2:
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.code, NULL)) AS codeFinance')
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.name, NULL)) AS nameFinance')
                cols.append(getContractClientPolicyForDate())
                if finance:
                    cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(finance), str(finance)))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
            elif QtGui.qApp.defaultHospitalBedFinanceByMoving() == 1:
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, NULL) AS nameFinance')
                cols.append(getActionClientPolicyForDate())
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                if finance:
                    cond.append('''(Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s)'''%(str(finance)))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
            else:
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                cols.append(getContractClientPolicyForDate())
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if orgStructureIdList:
                if stayOrgStructure:
                    cond.append(getDataOrgStructure(nameReceivedOS, orgStructureIdList, False))
                else:
                    cond.append(getDataOrgStructure(nameTransferOS, orgStructureIdList, False))
            if profile:
                cond.append(getHospitalBedProfile(profile))
            orderBy = getOrderBy()
            return  db.getRecordList(queryTable, cols, cond, orderBy)
        recordsMoving = getTransfer(orgStructureIdList, filterBegDate, filterEndDate, indexSex, ageFor, ageTo, permanent, type, profile,
        codeAttachType, finance, indexLocalClient, feed, dateFeed, accountingSystemId, filterClientId, filterEventId)
        for record in recordsMoving:
            countEventFeedId = forceBool(record.value('countEventFeedId'))
            if (feed == 1 and not countEventFeedId) or (feed == 2 and countEventFeedId) or not feed or feed == 3:
                statusObservation = forceString(record.value('statusObservation')).split('|')
                statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                begDate = forceDate(record.value('begDate'))
                policyEndDate = forceDate(record.value('policyEndDate'))
                colorFinance = None
                if policyEndDate:
                    if begDate < policyEndDate and begDate.addDays(3) >= policyEndDate:
                       colorFinance = QtGui.QColor(Qt.yellow)
                    elif begDate >= policyEndDate:
                        colorFinance = QtGui.QColor(Qt.red)
                documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                serialVoucher = forceStringEx(record.value('serialVoucher'))
                numberVoucher = forceStringEx(record.value('numberVoucher'))
                relegateOrgName = forceStringEx(record.value('relegateOrg'))
                directionCity = getCityName(forceStringEx(record.value('directionCity')))
                directionRegion = forceStringEx(record.value('directionRegion'))
                item = [statusObservationName,
                            # statusObservationCode,
                        forceString(record.value('nameFinance')),
                        nameContract,
                        countEventFeedId,
                        forceRef(record.value('client_id')),
                        forceString(record.value('externalId')),
                        forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                        self.sex[forceInt(record.value('sex'))],
                        forceString(forceDate(record.value('birthDate'))) + u'(' + forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate')))) + u')',
                        forceDateTime(record.value('receivedBegDate')).toString('dd.MM.yyyy hh:mm'),
                        forceDateTime(record.value('begDate')).toString('dd.MM.yyyy hh:mm'),
                        forceDateTime(record.value('endDate')).toString('dd.MM.yyyy hh:mm'),
                        forceString(record.value('MKB')),
                        forceString(record.value('profileName')),
                        forceString(record.value('nameOrgStructure')),
                        forceString(record.value('nameFromOS')),
                        forceString(record.value('namePerson')),
                        forceString(record.value('citizenship')),
                        hospDocumentLocation,
                        ((serialVoucher + u' ') if serialVoucher else u'') + numberVoucher,
                        directionCity,
                        directionRegion,
                        relegateOrgName,
                        forceRef(record.value('eventId')),
                        forceString(record.value('codeFinance')),
                        '',
                        statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                        statusObservationColor,
                        documentLocationColor,
                        colorFinance
                        ]
                self.feedTextValueItems.append(forceString(record.value('clientDiet')))
                self.items.append(item)
                eventId = forceRef(record.value('eventId'))
                dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'clientFeed': countEventFeedId,
                        'contract': nameContract,
                        'bedCode': '',
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': '',
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'orgStructureFrom': forceString(record.value('nameFromOS')),
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor,
                        'setDate': CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))), #.toString('dd.MM.yyyy hh:mm'),
                        'begDate': CDateTimeInfo(forceDateTime(record.value('begDate'))), #.toString('dd.MM.yyyy hh:mm'),
                        'endDate': CDateTimeInfo(forceDateTime(record.value('endDate')))
                    }
                self.itemByName[eventId] = dict
        self.reset()


    def getEventId(self, row):
        return self.items[row][23]


    def getClientId(self, row):
        return self.items[row][4]


class CLeavedModel(CMonitoringModel):
    column = [u'С', u'И', u'Д', u'Номер', u'Карта', u'ФИО', u'Пол', u'Дата рождения', u'Госпитализирован', u'Поступил',
    u'Выбыл', u'МЭС', u'MKB', u'Профиль', u'Подразделение', u'Лечащий врач', u'Гражданство', u'М',
    u'Койко-дни', u'Путевка', u'Субъект', u'Район', u'Направитель']
    eventColumn = 23

    def __init__(self, parent):
        CMonitoringModel.__init__(self, parent)
        self.items = []
        self._cols = []
        self.begDays = 0

    def columnCount(self, index = None):
        return 23

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
            elif role == Qt.ToolTipRole:
                if section == 17:
                    return QVariant(u'Место нахождение учетного документа')
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            item = self.items[row]
            return toVariant(item[column])
        elif role == Qt.ToolTipRole:
            if column == 0:
                item = self.items[row]
                return QVariant(item[0] + u' ' + item[27])
            elif column == 1:
                item = self.items[row]
                return QVariant(item[24] + u' ' + item[1])
            elif column == 12:
                item = self.items[row]
                return QVariant(item[12] + u' ' + item[25])
            elif column == 16:
                item = self.items[row]
                return QVariant(item[16] + u' ' + item[1])
        elif role == Qt.BackgroundColorRole:
            if column == 0 and self.items[row][0]:
               return toVariant(QtGui.QColor(self.items[row][28]))
            elif column == 1:
                colorFinance = self.items[row][len(self.items[row])-1]
                if colorFinance:
                    return toVariant(colorFinance)
            elif column == len(self.column)-2:
                docLocalColor = self.items[row][len(self.items[row])-2]
                if docLocalColor:
                    return toVariant(QtGui.QColor(docLocalColor))
        return QVariant()

    def getEventId(self, row):
        return self.items[row][self.eventColumn]

    def getClientId(self, row):
        return self.items[row][3]

    def cols(self):
        self._cols = [CCol(u'Статус наблюдения',     ['statusObservation'], 20, 'l'),
                      CCol(u'Код ИФ',                ['nameFinance'], 20, 'l'),
                      CCol(u'Договор',               ['contract'], 20, 'l'),
                      CCol(u'Номер',                 ['client_id'], 20, 'l'),
                      CCol(u'Карта',                 ['externalId'], 20, 'l'),
                      CCol(u'ФИО',                   ['lastName', 'firstName', 'patrName'], 30, 'l'),
                      CCol(u'Пол',                   ['sex'], 15, 'l'),
                      CCol(u'Дата рождения',         ['birthDate'], 20, 'l'),
                      CCol(u'Госпитализирован',      ['begDateReceived'], 20, 'l'),
                      CCol(u'Поступил',              ['begDate'], 20, 'l'),
                      CCol(u'Выбыл',                 ['endDate'], 20, 'l'),
                      CCol(u'МЭС',                   ['mes'], 20, 'l'),
                      CCol(u'MKB',                   ['MKB'], 20, 'l'),
                      CCol(u'Профиль',               ['profileName'], 30, 'l'),
                      CCol(u'Подразделение',         ['nameOS'], 30, 'l'),
                      CCol(u'Лечащий врач',         ['namePerson'], 30, 'l'),
                      CCol(u'Гражданство',           ['citizenship'], 30, 'l'),
                      CCol(u'Место нахождение учетного документа',['hospDocumentLocation'], 30, 'l'),
                      CCol(u'Койко-дни',             ['bedDays'], 20, 'l'),
                      CCol(u'Путевка',               ['voucher'], 20, 'l'),
                      CCol(u'Субъект',               ['srcCity'], 20, 'l'),
                      CCol(u'Район',                 ['srcRegion'], 20, 'l'),
                      CCol(u'Направитель',           ['srcOrg'], 20, 'l'),
                      ]
        return self._cols

    def loadData(self, dialogParams):
        self.begDays = 0
        self.items = []
        self.itemByName = {}
        filterBegDate = dialogParams.get('filterBegDate', None)
        filterEndDate = dialogParams.get('filterEndDate', None)
        filterBegTime = dialogParams.get('filterBegTime', None)
        filterEndTime = dialogParams.get('filterEndTime', None)
        if not filterBegTime.isNull():
            begDateTime = QDateTime(filterBegDate, filterBegTime)
            filterBegDate = begDateTime
        if not filterEndTime.isNull():
            endDateTime = QDateTime(filterEndDate, filterEndTime)
            filterEndDate = endDateTime
        indexSex = dialogParams.get('indexSex', 0)
        ageFor = dialogParams.get('ageFor', 0)
        ageTo = dialogParams.get('ageTo', 150)
        order = dialogParams.get('order', -1)
        eventTypeId = dialogParams.get('eventTypeId', None)
        orgStructureId = dialogParams.get('orgStructureId', None)
        profile = dialogParams.get('treatmentProfile', None)
        codeAttachType = dialogParams.get('codeAttachType', None)
        finance = dialogParams.get('finance', None)
        contractId = dialogParams.get('contractId', None)
        personId = dialogParams.get('personId', None)
        accountingSystemId = dialogParams.get('accountingSystemId', None)
        filterClientId = dialogParams.get('filterClientId', None)
        filterEventId = dialogParams.get('filterEventId', None)
        statusObservation = dialogParams.get('statusObservation', None)
        conclusion = dialogParams.get('conclusion', 0)
        leavedIndex = dialogParams.get('leavedIndex', 0)
        eventClosedType = dialogParams.get('eventClosedType', 0)
        filterMES = dialogParams.get('filterMES', u'')
        srcCity =  dialogParams.get('srcCity', None)
        srcRegion =  dialogParams.get('srcRegion', None)
        relegateOrg = dialogParams.get('srcOrg', None)
        MKBSrcFilter = dialogParams['MKBSrcFilter']
        MKBSrcFrom   = dialogParams['MKBSrcFrom']
        MKBSrcTo     = dialogParams['MKBSrcTo']
        MKBFilter = dialogParams['MKBFilter']
        MKBFrom   = dialogParams['MKBFrom']
        MKBTo     = dialogParams['MKBTo']
        voucherSerial = dialogParams['voucherSerial']
        voucherNumber = dialogParams['voucherNumber']
        relegateOrg = dialogParams.get('relegateOrg', None)
        documentTypeForTracking = dialogParams.get('documentTypeForTracking', None)
        documentLocation = dialogParams.get('documentLocation', None)
        scheduleId = dialogParams.get('scheduleId', None)
        self.statusObservation = statusObservation
        groupBY = ''

        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableEV = db.table('Event_Voucher')
        tableMes = db.table('mes.MES')
        tableClient = db.table('Client')
        tableAPOS = db.table('ActionProperty_OrgStructure')
        tableOS = db.table('OrgStructure')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableClientAttach = db.table('ClientAttach')
        tableRBAttachType = db.table('rbAttachType')
        tableContract = db.table('Contract')
        tableRBFinance = db.table('rbFinance')
        tableRBFinanceBC = db.table('rbFinance').alias('rbFinanceByContract')
        tableStatusObservation= db.table('Client_StatusObservation')
        tableOrg = db.table('Organisation')
        tablekladrOKATO = db.table('kladr.OKATO')
        actionTypeIdList = getActionTypeIdListByFlatCode(u'received%')
        leavedActionTypeIdList = getActionTypeIdListByFlatCode(u'leaved%')

        def getOrderBy(setDate, begDate, endDate):
            orderBY = u'Client.lastName ASC'
            for key, value in self.headerSortingCol.items():
                if not value:
                    ASC = u'ASC'
                else:
                    ASC = u'DESC'
                if key == 3:
                   orderBY = u'Event.client_id %s'%(ASC)
                elif key == 4:
                    orderBY = u'CAST(Event.externalId AS SIGNED) %s'%(ASC)
                elif key == 5:
                    orderBY = u'Client.lastName %s'%(ASC)
                elif key == 9:
                    orderBY = u'%s %s, %s %s'%(begDate, ASC, setDate, ASC)
                elif key == 10:
                    orderBY = u'Action.%s %s'%(endDate, ASC)
                elif key == 8:
                    if leavedIndex == 1 or leavedIndex == 2:
                        orderBY = u'Action.%s %s'%(begDate, ASC)
                    elif leavedIndex == 0:
                        orderBY = u'%s %s'%(setDate, ASC)
                elif key == 11:
                    orderBY = u'mes.MES.code %s'%(ASC)
                elif key == 14:
                    orderBY = u'nameOrgStructure %s'%(ASC)
                elif key == 15:
                    orderBY = u'namePerson %s'%(ASC)
                elif key == 19:
                    orderBY = u'Event_Voucher.serial, Event_Voucher.number %s'%(ASC)
            return orderBY

        if orgStructureId:
            treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
            orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem._id else []
        if leavedIndex == 1 or leavedIndex == 2:
            groupBY = u''
            cols = [tableAction['begDate'],
                    tableAction['id'],
                    tableEvent['id'].alias('eventId'),
                    tableEvent['externalId'],
                    tableEvent['client_id'],
                    tableEvent['eventType_id'],
                    tableEvent['setDate'],
                    tableEvent['execDate'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['endDate'],
                    tableAction['plannedEndDate'],
                    tableMes['code'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    tableEV['serial'].alias('serialVoucher'),
                    tableEV['number'].alias('numberVoucher'),
                    tableEvent['relegateOrg_id'],
                    tableEvent['directionCity'],
                    tablekladrOKATO['NAME'].alias('directionRegion'),
                    tableOrg['shortName'].alias('relegateOrg'),
                    tablePWS['name'].alias('namePerson')
                    ]
            cols.append(getMKB())
            cols.append(getReceivedBegDate(actionTypeIdList))
            cols.append(getReceivedEndDate(u'Направлен в отделение', actionTypeIdList))
            cols.append(getLeavedEndDate(leavedActionTypeIdList))
            cols.append(getOSHBP())
            cols.append(getStatusObservation())
            cols.append(getHospDocumentLocationInfo())
            cols.append('(SELECT name from rbSocStatusType where code = getClientCitizenship(Client.id, Action.begDate)) as citizenship')
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.leftJoin(tableEV, db.joinAnd([tableEV['event_id'].eq(tableEvent['id']), tableEV['deleted'].eq(0)]))
            queryTable = queryTable.innerJoin(tableMes, tableMes['id'].eq(tableEvent['MES_id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            queryTable = queryTable.innerJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
            queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            queryTable = queryTable.leftJoin(tablekladrOKATO, tablekladrOKATO['CODE'].eq(tableEvent['directionRegion']))
            cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'moving%')),
                     tableAction['deleted'].eq(0),
                     tableEvent['deleted'].eq(0),
                     tableAP['deleted'].eq(0),
                     tableClient['deleted'].eq(0),
                     tableAP['action_id'].eq(tableAction['id']),
                     tableAction['endDate'].isNotNull(),
                     tableAPT['name'].like(u'Отделение пребывания')
                   ]
            if scheduleId:
                cond.append(isScheduleBeds(scheduleId))
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if leavedIndex == 2:
                cond.append(tableAction['endDate'].isNotNull())
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            if filterMES:
                cond.append(tableMes['code'].eq(filterMES))
            if eventClosedType == 1:
                cond.append(tableEvent['execDate'].isNotNull())
            elif eventClosedType == 2:
                cond.append(tableEvent['execDate'].isNull())
            cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'8\')))''')
            cols.append(u'IF(OrgStructure.id IS NOT NULL AND OrgStructure.deleted=0, OrgStructure.name, NULL) AS orgStructureName')
            if personId:
               cond.append(tableEvent['execPerson_id'].eq(personId))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if srcCity:
                cond.append(tableEvent['directionCity'].eq(srcCity))
            if srcRegion:
                cond.append(tableEvent['directionRegion'].eq(srcRegion))
            if MKBSrcFilter:
                cond.append('Event.directionMKB >= \'%s\' AND Event.directionMKB <= \'%s\''%(MKBSrcFrom, MKBSrcTo))
            if voucherSerial:
                cond.append(tableEV['serial'].eq(voucherSerial))
            if voucherNumber:
                cond.append(tableEV['number'].eq(voucherNumber))
            if self.statusObservation:
                queryTable = queryTable.innerJoin(tableStatusObservation, tableStatusObservation['master_id'].eq(tableClient['id']))
                cond.append(tableStatusObservation['deleted'].eq(0))
                cond.append(tableStatusObservation['statusObservationType_id'].eq(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() == 2:
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.code, NULL)) AS codeFinance')
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.name, NULL)) AS nameFinance')
                cols.append(getClientPolicyForDate())
                if finance:
                    cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(finance), str(finance)))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
            elif QtGui.qApp.defaultHospitalBedFinanceByMoving() == 1:
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, NULL) AS nameFinance')
                cols.append(getActionClientPolicyForDate())
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                if finance:
                    cond.append('''(Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s)'''%(str(finance)))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
            else:
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                cols.append(getContractClientPolicyForDate())
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if profile:
                cond.append(getHospitalBedProfile(profile))
            if documentTypeForTracking:
                if documentTypeForTracking!=u'specialValueID':
                    tableDocumentTypeForTracking = db.table('Client_DocumentTracking')
                    cond.append(tableDocumentTypeForTracking['deleted'].eq(0))
                    queryTable = queryTable.leftJoin(tableDocumentTypeForTracking, tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                    cond.append(tableDocumentTypeForTracking['documentTypeForTracking_id'].eq(documentTypeForTracking))
                    cond.append(tableDocumentTypeForTracking['documentNumber'].eq(tableEvent['externalId']))
                    groupBY = 'Event.id'
            if documentLocation:
                tableDocumentLocation = db.table('Client_DocumentTrackingItem')
                if not documentTypeForTracking:
                    tableDocumentTypeForTracking = db.table('Client_DocumentTracking')
                    queryTable = queryTable.leftJoin(tableDocumentTypeForTracking, tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                    cond.append(tableDocumentTypeForTracking['documentNumber'].eq(tableEvent['externalId']))
                queryTable = queryTable.leftJoin(tableDocumentLocation, tableDocumentTypeForTracking['id'].eq(tableDocumentLocation['master_id']))
                tableDocumentLocationLimit = db.table('Client_DocumentTrackingItem').alias('tableDocumentLocationLimit')
                cond.append(tableDocumentLocation['documentLocation_id'].inlist(documentLocation))
                cond.append(tableDocumentLocation['id'].eqEx('(%s)'%db.selectStmt(tableDocumentLocationLimit, tableDocumentLocationLimit['id'], tableDocumentLocationLimit['master_id'].eq(tableDocumentLocation['master_id']), 'documentLocationDate desc, documentLocationTime desc limit 1')))
                if groupBY=='':
                    groupBY = 'Event.id'
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if orgStructureIdList:
                cond.append(tableOS['deleted'].eq(0))
                cond.append(tableAPOS['value'].inlist(orgStructureIdList))
            if forceBool(filterBegDate.date()):
                cond.append(tableAction['endDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['endDate'].le(filterEndDate))
            if conclusion and conclusion != u'не определено':
                cond.append(getStringProperty(u'Исход госпитализации', u'(APS.value %s)'%(updateLIKE(conclusion))))
            orderBy = getOrderBy('Event.setDate', 'receivedBegDate', 'endDate')
            if groupBY!='':
                records = db.getRecordListGroupBy(queryTable, cols, cond, groupBY,u'%s%s'%(orderBy, u', Action.id' if leavedIndex == 2 else u''))
            else:
                records = db.getRecordList(queryTable, cols, cond, u'%s%s'%(orderBy, u', Action.id' if leavedIndex == 2 else u''))
            for record in records:
                documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                if documentTypeForTracking==u'specialValueID':
                    if hospDocumentLocation!='':
                        continue
                statusObservation = forceString(record.value('statusObservation')).split('|')
                statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                begDate = forceDate(record.value('receivedBegDate'))
                policyEndDate = forceDate(record.value('policyEndDate'))
                colorFinance = None
                if policyEndDate:
                    if begDate < policyEndDate and begDate.addDays(3) >= policyEndDate:
                       colorFinance = QtGui.QColor(Qt.yellow)
                    elif begDate >= policyEndDate:
                        colorFinance = QtGui.QColor(Qt.red)
                nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                receivedBegDate = forceDate(record.value('receivedBegDate'))
                leavedEndDate = forceDate(record.value('leavedEndDate'))
                bedDays = updateDurationEvent(receivedBegDate, leavedEndDate, filterBegDate, filterEndDate, forceRef(record.value('eventType_id')), isPresence = False)
                self.begDays += forceInt(bedDays) if bedDays != u'-' else 0
                serialVoucher = forceStringEx(record.value('serialVoucher'))
                numberVoucher = forceStringEx(record.value('numberVoucher'))
                relegateOrgName = forceStringEx(record.value('relegateOrg'))
                directionCity = getCityName(forceStringEx(record.value('directionCity')))
                directionRegion = forceStringEx(record.value('directionRegion'))
                item = [statusObservationName,
                            # statusObservationCode,
                        forceString(record.value('nameFinance')),
                        nameContract,
                        forceRef(record.value('client_id')),
                        forceString(record.value('externalId')),
                        forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                        self.sex[forceInt(record.value('sex'))],
                        forceString(forceDate(record.value('birthDate'))) + u'(' + forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate')))) + u')',
                        forceDateTime(record.value('receivedBegDate')),
                        forceDateTime(record.value('receivedEndDate')),
                        forceDateTime(record.value('endDate')),
                        forceString(record.value('code')),
                        forceString(record.value('MKB')),
                        forceString(record.value('profileName')),
                        forceString(record.value('orgStructureName')),
                        forceString(record.value('namePerson')),
                        forceString(record.value('citizenship')),
                        hospDocumentLocation,
                        bedDays,
                        ((serialVoucher + u' ') if serialVoucher else u'') + numberVoucher,
                        directionCity,
                        directionRegion,
                        relegateOrgName,
                        forceRef(record.value('eventId')),
                        forceString(record.value('codeFinance')),
                        '',
                        forceString(record.value('externalId')),
                        statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                        statusObservationColor,
                        documentLocationColor,
                        colorFinance
                        ]
                self.items.append(item)
                eventId = forceRef(record.value('eventId'))
                dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'contract': nameContract,
                        'bedCode': '',
                        'orgStructure': forceString(record.value('orgStructureName')),
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': '',
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor,
                        'setDate': CDateTimeInfo(forceDateTime(record.value('setDate'))), #.toString('dd.MM.yyyy hh:mm'),
                        'begDate': CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))), #.toString('dd.MM.yyyy hh:mm'),
                        'endDate': CDateTimeInfo(forceDateTime(record.value('endDate'))),
                        'profile' : forceString(record.value('profileName'))
                    }
                self.itemByName[eventId] = dict
            self.reset()
        elif leavedIndex == 0 or leavedIndex == 3 or leavedIndex == 4:
            groupBY = u''
            cols = [tableAction['begDate'],
                    tableAction['id'],
                    tableEvent['id'].alias('eventId'),
                    tableEvent['externalId'],
                    tableEvent['client_id'],
                    tableEvent['eventType_id'],
                    tableEvent['setDate'],
                    tableEvent['execDate'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['endDate'],
                    tableMes['code'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    tableEV['serial'].alias('serialVoucher'),
                    tableEV['number'].alias('numberVoucher'),
                    tableEvent['relegateOrg_id'],
                    tableEvent['directionCity'],
                    tablekladrOKATO['NAME'].alias('directionRegion'),
                    tableOrg['shortName'].alias('relegateOrg'),
                    tablePWS['name'].alias('namePerson')
                    ]
            cols.append(getMKB())
            actionTypeIdList = getActionTypeIdListByFlatCode(u'received%')
            cols.append(getReceivedBegDate(actionTypeIdList))
            cols.append(getReceivedEndDate(u'Направлен в отделение', actionTypeIdList))
            cols.append(getLeavedEndDate(leavedActionTypeIdList))
            cols.append(getDataOrgStructureName(u'Отделение'))
            cols.append(getStatusObservation())
            cols.append(getOSHBP())
            cols.append(getHospDocumentLocationInfo())
            cols.append('(SELECT name from rbSocStatusType where code = getClientCitizenship(Client.id, Action.begDate) LIMIT 1) as citizenship')
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.leftJoin(tableEV, db.joinAnd([tableEV['event_id'].eq(tableEvent['id']), tableEV['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableMes, tableMes['id'].eq(tableEvent['MES_id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            queryTable = queryTable.leftJoin(tablekladrOKATO, tablekladrOKATO['CODE'].eq(tableEvent['directionRegion']))
            cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'leaved%')),
                     tableAction['deleted'].eq(0),
                     tableEvent['deleted'].eq(0),
                     tableClient['deleted'].eq(0)
                   ]
            if scheduleId:
                cond.append(isScheduleBeds(scheduleId))
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if srcCity:
                cond.append(tableEvent['directionCity'].eq(srcCity))
            if srcRegion:
                cond.append(tableEvent['directionRegion'].eq(srcRegion))
            if MKBSrcFilter:
                cond.append('Event.directionMKB >= \'%s\' AND Event.directionMKB <= \'%s\''%(MKBSrcFrom, MKBSrcTo))
            if voucherSerial:
                cond.append(tableEV['serial'].eq(voucherSerial))
            if voucherNumber:
                cond.append(tableEV['number'].eq(voucherNumber))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            if filterMES:
                cond.append(tableMes['code'].eq(filterMES))
            if eventClosedType == 1:
                cond.append(tableEvent['execDate'].isNotNull())
            elif eventClosedType == 2:
                cond.append(tableEvent['execDate'].isNull())
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'8\')))''')
            if personId:
               cond.append(tableEvent['execPerson_id'].eq(personId))
            if profile:
                cond.append(getHospitalBedProfile(profile))
            if documentTypeForTracking:
                if documentTypeForTracking!=u'specialValueID':
                    tableDocumentTypeForTracking = db.table('Client_DocumentTracking')
                    cond.append(tableDocumentTypeForTracking['deleted'].eq(0))
                    queryTable = queryTable.leftJoin(tableDocumentTypeForTracking, tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                    cond.append(tableDocumentTypeForTracking['documentTypeForTracking_id'].eq(documentTypeForTracking))
                    cond.append(tableDocumentTypeForTracking['documentNumber'].eq(tableEvent['externalId']))
                    groupBY = 'Event.id'
            if documentLocation:
                tableDocumentLocation = db.table('Client_DocumentTrackingItem')
                if not documentTypeForTracking:
                    tableDocumentTypeForTracking = db.table('Client_DocumentTracking')
                    queryTable = queryTable.leftJoin(tableDocumentTypeForTracking, tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                    cond.append(tableDocumentTypeForTracking['documentNumber'].eq(tableEvent['externalId']))
                queryTable = queryTable.leftJoin(tableDocumentLocation, tableDocumentTypeForTracking['id'].eq(tableDocumentLocation['master_id']))
                tableDocumentLocationLimit = db.table('Client_DocumentTrackingItem').alias('tableDocumentLocationLimit')
                cond.append(tableDocumentLocation['documentLocation_id'].inlist(documentLocation))
                cond.append(tableDocumentLocation['id'].eqEx('(%s)'%db.selectStmt(tableDocumentLocationLimit, tableDocumentLocationLimit['id'], tableDocumentLocationLimit['master_id'].eq(tableDocumentLocation['master_id']), 'documentLocationDate desc, documentLocationTime desc limit 1')))
                if groupBY == '':
                    groupBY = 'Event.id'
            if self.statusObservation:
                queryTable = queryTable.innerJoin(tableStatusObservation, tableStatusObservation['master_id'].eq(tableClient['id']))
                cond.append(tableStatusObservation['deleted'].eq(0))
                cond.append(tableStatusObservation['statusObservationType_id'].eq(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() in (0, 2):
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            cols.append(getContractClientPolicyForDate())
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            movingIdList = getActionTypeIdListByFlatCode(u'moving%')
            if leavedIndex == 3:
                cond.append(u'''EXISTS(SELECT A.id
                                FROM Action AS A
                                WHERE A.event_id = Event.id AND A.deleted = 0
                                AND A.actionType_id IN (%s))'''%(','.join(str(movingId) for movingId in movingIdList if movingId)))
            elif leavedIndex == 4:
                cond.append(u'''NOT EXISTS(SELECT A.id
                                FROM Action AS A
                                WHERE A.event_id = Event.id AND A.deleted = 0
                                AND A.actionType_id IN (%s))'''%(','.join(str(movingId) for movingId in movingIdList if movingId)))
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if forceBool(filterBegDate.date()):
                cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(filterBegDate)]))
            if forceBool(filterEndDate.date()):
                cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].le(filterEndDate)]))
            if orgStructureId:
                treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
                orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem._id else []
            if orgStructureIdList:
                cond.append(getDataOrgStructure(u'Отделение', orgStructureIdList, False))
            if conclusion and conclusion != u'не определено':
                cond.append(getStringProperty(u'Исход госпитализации', u'(APS.value %s)'%(updateLIKE(conclusion))))
            orderBy = getOrderBy('receivedBegDate', 'receivedEndDate', 'endDate')
            if groupBY != '':
                records = db.getRecordListGroupBy(queryTable, cols, cond, groupBY, orderBy)
            else:
                records = db.getRecordList(queryTable, cols, cond, orderBy)
            for record in records:
                documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                if documentTypeForTracking==u'specialValueID':
                    if hospDocumentLocation!='':
                        continue
                statusObservation = forceString(record.value('statusObservation')).split('|')
                statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                begDate = forceDate(record.value('receivedBegDate'))
                policyEndDate = forceDate(record.value('policyEndDate'))
                colorFinance = None
                if policyEndDate:
                    if begDate < policyEndDate and begDate.addDays(3) >= policyEndDate:
                       colorFinance = QtGui.QColor(Qt.yellow)
                    elif begDate >= policyEndDate:
                        colorFinance = QtGui.QColor(Qt.red)
                nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                receivedBegDate = forceDate(record.value('receivedBegDate'))
                leavedEndDate = forceDate(record.value('leavedEndDate'))
                bedDays = updateDurationEvent(receivedBegDate, leavedEndDate, filterBegDate, filterEndDate, forceRef(record.value('eventType_id')), isPresence = False)
                self.begDays += forceInt(bedDays) if bedDays != u'-' else 0
                serialVoucher = forceStringEx(record.value('serialVoucher'))
                numberVoucher = forceStringEx(record.value('numberVoucher'))
                relegateOrgName = forceStringEx(record.value('relegateOrg'))
                directionCity = getCityName(forceStringEx(record.value('directionCity')))
                directionRegion = forceStringEx(record.value('directionRegion'))
                item = [statusObservationName,
                            # statusObservationCode,
                        forceString(record.value('nameFinance')),
                        nameContract,
                        forceRef(record.value('client_id')),
                        forceString(record.value('externalId')),
                        forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                        self.sex[forceInt(record.value('sex'))],
                        forceString(forceDate(record.value('birthDate'))) + u'(' + forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate')))) + u')',
                        forceDateTime(record.value('receivedBegDate')),
                        forceDateTime(record.value('receivedEndDate')),
                        forceDateTime(record.value('endDate')),
                        forceString(record.value('code')),
                        forceString(record.value('MKB')),
                        forceString(record.value('profileName')),
                        forceString(record.value('nameOrgStructure')),
                        forceString(record.value('namePerson')),
                        forceString(record.value('citizenship')),
                        hospDocumentLocation,
                        bedDays,
                        ((serialVoucher + u' ') if serialVoucher else u'') + numberVoucher,
                        directionCity,
                        directionRegion,
                        relegateOrgName,
                        forceRef(record.value('eventId')),
                        forceString(record.value('codeFinance')),
                        '',
                        forceString(record.value('externalId')),
                        statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                        statusObservationColor,
                        documentLocationColor,
                        colorFinance
                        ]
                self.items.append(item)
                eventId = forceRef(record.value('eventId'))
                dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'contract': nameContract,
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'financeCode': forceString(record.value('codeFinance')),
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor,
                        'setDate': CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))), #.toString('dd.MM.yyyy hh:mm'),
                        'begDate': CDateTimeInfo(forceDateTime(record.value('receivedEndDate'))), #.toString('dd.MM.yyyy hh:mm'),
                        'endDate': CDateTimeInfo(forceDateTime(record.value('endDate'))),
                        'profile' : forceString(record.value('profileName'))
                    }
                self.itemByName[eventId] = dict
        self.reset()


    def getBegDays(self):
        return self.begDays


class CQueueModel(CMonitoringModel):
    column = [u'С', u'И', u'Номер', u'Карта', u'ФИО', u'Пол', u'Дата рождения', u'Поставлен', u'Завершение планирования',
    u'Плановая дата госпитализации', u'Статус', u'Ожидание', u'MKB', u'Профиль', u'Подразделение', u'Ответственный',
    u'Гражданство', u'М', u'Направитель', u'Номер направления', u'АПУ', u'Путевка', u'Субъект', u'Район', u'Направитель']

    def __init__(self, parent):
        CMonitoringModel.__init__(self, parent)
        self.items = []
        self._cols = []

    def cols(self):
        self._cols = [CCol(u'Статус наблюдения',     ['statusObservation'], 20, 'l'),
                      CCol(u'Код ИФ',                ['nameFinance'], 20, 'l'),
                      CCol(u'Номер',                 ['client_id'], 20, 'l'),
                      CCol(u'Карта',                 ['externalId'], 20, 'l'),
                      CCol(u'ФИО',                   ['lastName', 'firstName', 'patrName'], 30, 'l'),
                      CCol(u'Пол',                   ['sex'], 15, 'l'),
                      CCol(u'Дата рождения',         ['birthDate'], 20, 'l'),
                      CCol(u'Поставлен',             ['begDate'], 20, 'l'),
                      CCol(u'Завершение планирования',['endDate'], 20, 'l'),
                      CCol(u'Плановая дата госпитализации', ['plannedEndDate'], 20, 'l'),
                      CCol(u'Статус',                ['status'], 20, 'l'),
                      CCol(u'Ожидание',              ['plannedEndDate'], 20, 'l'),
                      CCol(u'MKB',                   ['MKB'], 20, 'l'),
                      CCol(u'Профиль',               ['profileName'], 30, 'l'),
                      CCol(u'Подразделение',         ['nameOS'], 30, 'l'),
                      CCol(u'Ответственный',         ['namePerson'], 30, 'l'),
                      CCol(u'Гражданство',           ['citizenship'], 30, 'l'),
                      CCol(u'Место нахождения учетного документа',['hospDocumentLocation'], 30, 'l'),
                      CCol(u'Направитель',['relegateOrg'], 30, 'l'),
                      CCol(u'Номер направления',     ['srcNumber'], 30, 'l'),
                      CCol(u'АПУ',['policlinicPlannedDate'], 30, 'l'),
                      CCol(u'Путевка',               ['voucher'], 20, 'l'),
                      CCol(u'Субъект',               ['srcCity'], 20, 'l'),
                      CCol(u'Район',                 ['srcRegion'], 20, 'l'),
                      CCol(u'Направитель',           ['srcOrg'], 20, 'l'),
                      ]
        return self._cols


    def columnCount(self, index = None):
        return 24


    def getClientId(self, row):
        return self.items[row][2]


    def getEventId(self, row):
        return self.items[row][25]


    def getExternalId(self, row):
        return self.items[row][3]


    def getRelegateOrgId(self, row):
        return self.items[row][len(self.items[row])-6]


    def getRelegatePersonId(self, row):
        return self.items[row][len(self.items[row])-5]


    def getSrcDate(self, row):
        return self.items[row][len(self.items[row])-4]


    def getSrcNumber(self, row):
        return self.items[row][len(self.items[row])-3]


    def getDirectionDate(self, row):
        return self.items[row][len(self.items[row])-2]


    def getSetPersonId(self, row):
        return self.items[row][len(self.items[row])-1]


    def rowCount(self, index = None):
        return len(self.items)


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
            elif role == Qt.ToolTipRole:
                if section == 0:
                    return QVariant(u'Статус наблюдения пациента')
                elif section == 1:
                    return QVariant(u'Источник финансирования (код)')
                elif section == 17:
                    return QVariant(u'Место нахождения учетного документа')
                elif section == 20:
                    return QVariant(u'Плановая дата госпитализации поликлиники')
        return QVariant()


    def getPlanningActionId(self, eventId):
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        planningActionId = 0
        cols = [tableAction['id'].alias('planningActionId')]
        queryTable = tableAction
        queryTable = queryTable.leftJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'planning%')),
                     tableAction['deleted'].eq(0),
                     tableEvent['deleted'].eq(0),
                     tableEvent['id'].eq(eventId)]
        records = db.getRecordList(queryTable, cols, cond)
        if records:
            for record in records:
                planningActionId = forceInt(record.value('planningActionId'))
        return planningActionId


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.BackgroundColorRole:
            if column == 0 and self.items[row][0]:
               return toVariant(QtGui.QColor(self.items[row][30])) # statusObservationColor
#            elif self.items[row][27]: # movingActionId = getMovingActionForPlannedDate(moving), есть событие с Движением begDate <= (даты планирования) и begDate >= (endDate планирования)
#               return toVariant(QtGui.QColor(0, 255, 0))
#            elif len(forceString(self.items[row][12])) <= 0: # MKB не указан
#               return toVariant(QtGui.QColor(200, 230, 240))
            elif column == 1:
                colorFinance = self.items[row][len(self.items[row])-7] # colorFinance
                if colorFinance:
                    return toVariant(colorFinance)
            elif column == len(self.column)-4:  # documentLocationColor
                docLocalColor = self.items[row][len(self.items[row])-8]
                if docLocalColor:
                    return toVariant(QtGui.QColor(docLocalColor))
        if role == Qt.DisplayRole:
            item = self.items[row]
            return toVariant(item[column])
        elif role == Qt.ToolTipRole:
            if column == 0:
                item = self.items[row]
                return QVariant(item[0] + u' ' + item[29])
            elif column == 1:
                item = self.items[row]
                return QVariant(item[26] + u' ' + item[1])
            elif column == 13:
                item = self.items[row]
                return QVariant(item[13] + u' ' + item[27])
        return QVariant()

    def loadData(self, dialogParams):
        self.items = []
        self.itemByName = {}
        indexSex = dialogParams.get('indexSexPlaning', 0)
        ageFor = dialogParams.get('ageForPlaning', 0)
        ageTo = dialogParams.get('ageToPlaning', 150)
        order = dialogParams.get('order', -1)
        eventTypeId = dialogParams.get('eventTypeId', None)
        orgStructureId = dialogParams.get('orgStructureId', None)
        permanent = dialogParams.get('permanent', None)
        type = dialogParams.get('type', None)
        profile = dialogParams.get('treatmentProfile', None)
        presenceDay = dialogParams.get('presenceDayPlaning', None)
        codeAttachType = dialogParams.get('codeAttachTypePlaning', None)
        finance = dialogParams.get('financePlaning', None)
        contractId = dialogParams.get('contractIdPlaning', None)
        personId = dialogParams.get('personIdPlaning', None)
        personExecId = dialogParams.get('personExecIdPlaning', None)
        accountingSystemId = dialogParams.get('accountingSystemIdPlaning', None)
        filterClientId = dialogParams.get('filterClientIdPlaning', None)
        filterEventId = dialogParams.get('filterEventIdPlaning', None)
        isHospitalization = dialogParams.get('isHospitalization', 0)
        statusObservation = dialogParams.get('statusObservationPlaning', None)
        insurerId = dialogParams.get('insurerIdPlaning', None)
        regionSMO, regionTypeSMO, regionSMOCode = dialogParams.get('regionSMOPlaning', (False, 0, None))
        relegateOrg = dialogParams.get('relegateOrgPlaning', None)
        actionStatus = dialogParams.get('actionStatus', None)
        profileDirectionsId = dialogParams.get('profileDirectionsId', None)
        eventSrcNumber = dialogParams.get('eventSrcNumber', None)
        actionTypePlaningId = dialogParams.get('actionTypePlaningId', None)
        isNoPlannedEndDate = dialogParams.get('isNoPlannedEndDate', False)
        planActionBegDate      = dialogParams.get('planActionBegDate', None)
        planActionEndDate      = dialogParams.get('planActionEndDate', None)
        plannedBegDate         = dialogParams.get('plannedBegDate', None)
        plannedEndDate         = dialogParams.get('plannedEndDate', None)
        planWaitingBegDate     = dialogParams.get('planWaitingBegDate', None)
        planWaitingEndDate     = dialogParams.get('planWaitingEndDate', None)
        planBeforeOnsetBegDate = dialogParams.get('planBeforeOnsetBegDate', None)
        planBeforeOnsetEndDate = dialogParams.get('planBeforeOnsetEndDate', None)
        planExceedingDays      = dialogParams.get('planExceedingDays', None)

        self.statusObservation = statusObservation

        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableEV = db.table('Event_Voucher')
        tableClient = db.table('Client')
        tableOS = db.table('OrgStructure')
        tableOrg = db.table('Organisation')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableClientAttach = db.table('ClientAttach')
        tableRBAttachType = db.table('rbAttachType')
        tableStatusObservation= db.table('Client_StatusObservation')
        tablekladrOKATO = db.table('kladr.OKATO')
        tableContract = db.table('Contract')
        tableClientPolicy = db.table('ClientPolicy')
        currentDate = QDate.currentDate()

        colsDirection = [tableEvent['relegateOrg_id'],
                        tableEvent['relegatePerson_id'],
                        tableEvent['srcDate'],
                        tableEvent['srcNumber'],
                        tableAction['directionDate'],
                        tableAction['setPerson_id'],
                        ]

        def getOrderBy():
            orderBY = u'Client.lastName ASC'
            for key, value in self.headerSortingCol.items():
                if not value:
                    ASC = u'ASC'
                else:
                    ASC = u'DESC'
                if key == 1:
                   orderBY = u'CAST(financeCodeName AS SIGNED) %s'%(ASC)
                elif key == 2:
                   orderBY = u'Event.client_id %s'%(ASC)
                elif key == 4:
                    orderBY = u'Client.lastName %s'%(ASC)
                elif key == 7:
                    orderBY = u'Action.begDate %s'%(ASC)
                elif key == 9:
                    orderBY = u'Action.plannedEndDate %s'%(ASC)
                elif key == 11:
                    orderBY = u'Action.begDate %s'%(ASC)
                elif key == 14:
                    orderBY = u'nameOrgStructure %s'%(ASC)
                elif key == 15:
                    orderBY = u'namePerson %s'%(ASC)
                elif key == 21:
                    orderBY = u'Event_Voucher.serial, Event_Voucher.number %s'%(ASC)
            return orderBY

        def getPlanning(orgStructureIdList, indexSex = 0, ageFor = 0, ageTo = 150, permanent = None, type = None, profile = None, presenceDay = None, codeAttachType = None,
                        finance = None, noBeds = False, personId = None, accountingSystemId = None, filterClientId = None, filterEventId = None, personExecId = None):
            nameProperty = u'подразделение'
            groupBy = u''
            cols = [tableAction['id'],
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableEvent['srcNumber'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableAction['plannedEndDate'],
                    tableAction['status'],
                    tablePWS['name'].alias('namePerson'),
                    tableEV['serial'].alias('serialVoucher'),
                    tableEV['number'].alias('numberVoucher'),
                    tableEvent['relegateOrg_id'],
                    tableEvent['directionCity'],
                    tablekladrOKATO['NAME'].alias('directionRegion'),
                    tableOrg['shortName'].alias('relegateOrg')
                    ]
            cols.append(getMKB())
            cols.append(getOSHBP())
            cols.append(getDataOrgStructureName(nameProperty))
            cols.append(getStatusObservation())
            cols.append(getPropertyAPOS(u'Направлен в отделение', getActionTypeIdListByFlatCode(u'received%')))
            cols.append(getMovingActionForPlannedDate(getActionTypeIdListByFlatCode(u'moving%')))
            cols.append(getHospDocumentLocationInfo())
            cols.append('(SELECT name from rbSocStatusType where code = getClientCitizenship(Client.id, Action.plannedEndDate)) as citizenship')
            cols.append(u'''(SELECT ActionProperty_Date.value FROM ActionProperty_Date
                                        LEFT JOIN ActionProperty ON ActionProperty.id = ActionProperty_Date.id
                                        LEFT JOIN Action AS ACT ON ACT.id = ActionProperty.action_id
                                        LEFT JOIN ActionPropertyType ON ActionPropertyType.id = ActionProperty.type_id
                                        WHERE ACT.id = Action.id AND ActionPropertyType.name = 'Плановая дата госпитализации поликлиники') as policlinicPlannedDate''')
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tableEV, db.joinAnd([tableEV['event_id'].eq(tableEvent['id']), tableEV['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            queryTable = queryTable.leftJoin(tablekladrOKATO, tablekladrOKATO['CODE'].eq(tableEvent['directionRegion']))
            cond = [ tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'recoveryDirection%')),
                     tableAction['deleted'].eq(0),
                     tableEvent['deleted'].eq(0),
                     tableClient['deleted'].eq(0)
                   ]
            if planActionBegDate:
                cond.append(tableAction['begDate'].dateGe(planActionBegDate))
            if planActionEndDate:
                cond.append(tableAction['begDate'].dateLe(planActionEndDate))
            if plannedBegDate:
                cond.append(tableAction['plannedEndDate'].dateGe(plannedBegDate))
            if plannedEndDate:
                cond.append(tableAction['plannedEndDate'].dateLe(plannedEndDate))
            if planWaitingBegDate:
                cond.append(u'''Action.plannedEndDate IS NOT NULL AND ADDDATE(Action.begDate, %d) <= Action.plannedEndDate'''%(planWaitingBegDate))
            if planWaitingEndDate:
                cond.append(u'''Action.plannedEndDate IS NOT NULL AND ADDDATE(Action.begDate, %d) >= Action.plannedEndDate'''%(planWaitingEndDate))
            if planBeforeOnsetBegDate:
                cond.append(u'''Action.plannedEndDate IS NOT NULL AND ADDDATE(CURDATE(), %d) <= Action.plannedEndDate'''%(planBeforeOnsetBegDate))
            if planBeforeOnsetEndDate:
                cond.append(u'''Action.plannedEndDate IS NOT NULL AND ADDDATE(CURDATE(), %d) >= Action.plannedEndDate'''%(planBeforeOnsetEndDate))
            if planExceedingDays:
                cond.append(u'''(Action.plannedEndDate IS NOT NULL AND (DATE_ADD(Action.plannedEndDate, INTERVAL %d DAY) < CURDATE()))
                OR ((Action.begDate IS NOT NULL AND Action.plannedEndDate IS NULL) AND (DATE_ADD(Action.begDate, INTERVAL %d DAY) < CURDATE()))'''%(planExceedingDays, planExceedingDays))
            if isNoPlannedEndDate:
                cond.append(tableAction['plannedEndDate'].isNull())
            if actionStatus:
                cond.append(tableAction['status'].inlist(actionStatus))
            if profileDirectionsId > 0:
                cond.append(getPropertyHospitalBedProfile(u'Профиль', profileDirectionsId))
            elif profileDirectionsId == 0:
                groupBy = u'Action.id HAVING profileName is NULL'
            if eventSrcNumber:
                cond.append(tableEvent['srcNumber'].eq(eventSrcNumber))
            if actionTypePlaningId:
                cond.append(tableAction['actionType_id'].eq(actionTypePlaningId))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            #cond.append(tableAction['status'].ne(3))
            if personId:
               cond.append(tableAction['person_id'].eq(personId))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if self.statusObservation:
                queryTable = queryTable.innerJoin(tableStatusObservation, tableStatusObservation['master_id'].eq(tableClient['id']))
                cond.append(tableStatusObservation['deleted'].eq(0))
                cond.append(tableStatusObservation['statusObservationType_id'].eq(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if finance:
                condFinance = u' AND ActionProperty_rbFinance.value = %d' % (finance)
            else:
                condFinance = u''
            cols.append(u'''(SELECT CONCAT_WS(' ', CONVERT(rbFinance.id,CHAR(11)), rbFinance.code, rbFinance.name)
                            FROM  ActionType AS AT
                                INNER JOIN Action AS A ON AT.id=A.actionType_id
                                INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=AT.id
                                LEFT JOIN ActionProperty AS AP ON AP.type_id=APT.id AND AP.action_id = A.id
                                LEFT JOIN ActionProperty_rbFinance ON ActionProperty_rbFinance.id=AP.id
                                LEFT JOIN rbFinance ON rbFinance.id=ActionProperty_rbFinance.value
                            WHERE  A.deleted=0 AND AT.deleted=0 AND APT.deleted=0 AND A.id = Action.id AND APT.name = 'источник финансирования'%s) AS financeCodeName''' % (condFinance))
            cols.append(getDataOrgStructureName(nameProperty))
            cols.append(getActionQueueClientPolicyForDate())
#            if presenceDay:
#                currentDateFormat = tableAction['begDate'].formatValue(currentDate)
#                cond.append(u'DATEDIFF(%s, Action.begDate) = %d' % (forceString(currentDateFormat), presenceDay))
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if orgStructureIdList:
                cond.append(db.joinOr([getDataOrgStructure(nameProperty, orgStructureIdList, False), 'NOT %s'%(getActionPropertyTypeName(nameProperty))]))
            if profile:
                cond.append(getHospitalBedProfile(profile))
            if insurerId or regionSMO:
                tableRBFinance = db.table('rbFinance')
                tableRBFinanceBC = db.table('rbFinance').alias('rbFinanceByContract')
                if QtGui.qApp.defaultHospitalBedFinanceByMoving() == 2:
                    cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.code, NULL)) AS codeFinance')
                    cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.name, NULL)) AS nameFinance')
                    cols.append(getClientPolicyForDate())
                    if finance:
                        cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(finance), str(finance)))
                        queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                        queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                        queryTable = queryTable.innerJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
                    else:
                        queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                        queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                        queryTable = queryTable.leftJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
                elif QtGui.qApp.defaultHospitalBedFinanceByMoving() == 1:
                    cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, NULL) AS codeFinance')
                    cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, NULL) AS nameFinance')
                    cols.append(getActionClientPolicyForDate())
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    if finance:
                        cond.append('''(Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s)'''%(str(finance)))
                        queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    else:
                        queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                else:
                    cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                    cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                    cols.append(getContractClientPolicyForDate())
                    if finance:
                        cond.append(tableContract['deleted'].eq(0))
                        cond.append(tableRBFinance['id'].eq(finance))
                        queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                        queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                    else:
                        queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                        queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
                queryTable = queryTable.innerJoin(tableClientPolicy,
                                                  u'''(ClientPolicy.id = getClientPolicyIdForDate(Client.id, IF(Contract.id IS NOT NULL AND Contract.deleted=0, IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, NULL)), NULL), IF(Action.endDate IS NOT NULL, DATE(Action.endDate), CURDATE())))''')
                if not regionSMO:
                    cond.append(tableClientPolicy['insurer_id'].eq(insurerId))
                else:
                    tableOrganisation = db.table('Organisation').alias('Org_Area')
                    queryTable = queryTable.innerJoin(tableOrganisation, [tableOrganisation['id'].eq(tableClientPolicy['insurer_id']), tableOrganisation['deleted'].eq(0)])
                    if regionSMOCode:
                        if regionTypeSMO:
                            cond.append(tableOrganisation['area'].notlike(regionSMOCode))
                        else:
                            cond.append(tableOrganisation['area'].like(regionSMOCode))
            if contractId:
                cond.append(isContractPropertyValue(u'Договор', contractId))
            if isHospitalization == 1:
                cond.append(isPlanningToHospitalization())
            elif isHospitalization == 2:
                cond.append(u'NOT %s'%(isPlanningToHospitalization()))
            orderBy = getOrderBy()
            cols.extend(colsDirection)
            records = db.getRecordListGroupBy(queryTable, cols, cond, groupBy, orderBy)
            return records
        if orgStructureId:
            treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
            orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem._id else []
            recordType = db.getRecordEx(tableOS, [tableOS['id']], [tableOS['deleted'].eq(0), tableOS['type'].eq(4), tableOS['id'].inlist(orgStructureIdList)])
            if recordType and forceRef(recordType.value('id')):
                orgStructureIdList = []
        records = getPlanning(orgStructureIdList, indexSex, ageFor, ageTo, permanent, type, profile, presenceDay, codeAttachType, finance, False, personId, accountingSystemId, filterClientId, filterEventId, personExecId)
        for record in records:
            financeCodeName = forceString(record.value('financeCodeName')).split(" ")
            if len(financeCodeName)>=2:
                idFinance = forceRef(financeCodeName[0]) if len(financeCodeName)>=1 else 0
                nameFinance = forceString(financeCodeName[2]) if len(financeCodeName)>=3 else u''
                codeFinance = forceString(financeCodeName[1]) if len(financeCodeName)>=3 else u''
            else:
                idFinance = 0
                nameFinance = u''
                codeFinance = u''
            if not finance or (finance and finance == forceInt(idFinance)):
                begDateAction = forceDate(record.value('begDate'))
                endDateAction = forceDate(record.value('endDate'))
                waitingDays = begDateAction.daysTo(endDateAction) if endDateAction else begDateAction.daysTo(currentDate)
                statusObservation = forceString(record.value('statusObservation')).split('|')
                statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                policyEndDate = forceDate(record.value('policyEndDate'))
                colorFinance = None
                if policyEndDate:
                    if begDateAction < policyEndDate and begDateAction.addDays(3) >= policyEndDate:
                       colorFinance = QtGui.QColor(Qt.yellow)
                    elif begDateAction >= policyEndDate:
                        colorFinance = QtGui.QColor(Qt.red)
                documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                itemDirection = [
                                    forceRef(record.value('relegateOrg_id')),
                                    forceRef(record.value('relegatePerson_id')),
                                    forceDate(record.value('srcDate')),
                                    forceString(record.value('srcNumber')),
                                    forceDate(record.value('directionDate')),
                                    forceRef(record.value('setPerson_id')),
                                ]
                serialVoucher = forceStringEx(record.value('serialVoucher'))
                numberVoucher = forceStringEx(record.value('numberVoucher'))
                relegateOrgName = forceStringEx(record.value('relegateOrg'))
                directionCity = getCityName(forceStringEx(record.value('directionCity')))
                directionRegion = forceStringEx(record.value('directionRegion'))
                item = [statusObservationCode,
                        nameFinance,
                        forceRef(record.value('client_id')),
                        forceString(record.value('externalId')),
                        forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                        self.sex[forceInt(record.value('sex'))],
                        forceString(forceDate(record.value('birthDate'))) + u'(' + forceString(calcAge(forceDate(record.value('birthDate')), None)) + u')',
                        begDateAction,
                        endDateAction,
                        forceDate(record.value('plannedEndDate')),
                        CActionStatus.names[forceInt(record.value('status'))],
                        waitingDays,
                        forceString(record.value('MKB')),
                        forceString(record.value('profileName')),
                        forceString(record.value('nameOrgStructure')),
                        forceString(record.value('namePerson')),
                        forceString(record.value('citizenship')),
                        hospDocumentLocation,
                        forceString(record.value('relegateOrg')),
                        forceString(record.value('srcNumber')),
                        forceDate(record.value('policlinicPlannedDate')),
                        ((serialVoucher + u' ') if serialVoucher else u'') + numberVoucher,
                        directionCity,
                        directionRegion,
                        relegateOrgName,
                        forceRef(record.value('eventId')),
                        nameFinance,
                        codeFinance,
                        forceBool(record.value('APOS_value')),
                        statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                        statusObservationColor,
                        forceRef(record.value('movingActionId')),
                        documentLocationColor,
                        colorFinance
                        ]
                item.extend(itemDirection)
                self.items.append(item)
                eventId = forceRef(record.value('eventId'))
                orgStr = forceString(record.value('APOS_value'))
                hasOrgStr = forceBool(record.value('APOS_value'))
                dict = {
                        'observationCode': statusObservationCode,
                        'finance': nameFinance,
                        'bedCode': '',
                        'orgStructureName': forceString(record.value('nameOrgStructure')),
                        'bedName': '',
                        'waitingDays': waitingDays,
                        'orgStructure': orgStr if hasOrgStr else '',
                        'begDate': CDateInfo(begDateAction),
                        'plannedBegDate': CDateInfo(forceDate(record.value('plannedEndDate'))),
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor
                    }
                self.itemByName[eventId] = dict
        self.reset()


class CAttendanceActionsTableModel(CTableModel):
    class CLocPresenceOSColumn(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')


        def format(self, values):
            val = values[0]
            eventId  = forceRef(val)
            if eventId:
                db = QtGui.qApp.db
                table = db.table('Event')
                clientRecord = db.getRecordEx(table, [table['client_id']], [table['deleted'].eq(0), table['id'].eq(eventId)])
                if clientRecord:
                    clientId = forceRef(clientRecord.value('client_id'))
                if not clientId:
                    return CCol.invalid
                record = values[1]
                actionDate = forceDate(record.value('directionDate'))
                if not actionDate:
                    actionDate = forceDate(record.value('begDate'))
                if not actionDate:
                    return CCol.invalid
                query = QtGui.qApp.db.query(getDataOrgStructureNameMoving(u'Отделение пребывания', actionDate, clientId, u'moving%%'))
                if query.first():
                    record=query.record()
                    return record.value('nameOrgStructure')
                return CCol.invalid
            return CCol.invalid


    class CLocJobTicketColumn(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')


        def format(self, values):
            val = values[0]
            actionId  = forceRef(val)
            if actionId:
                db = QtGui.qApp.db
                tableAction = db.table('Action')
                tableAP = db.table('ActionProperty')
                tableAPT = db.table('ActionPropertyType')
                tableAPJT = db.table('ActionProperty_Job_Ticket')
                tableJT = db.table('Job_Ticket')
                table = tableAction.innerJoin(tableAP, tableAP['action_id'].eq(tableAction['id']))
                table = table.innerJoin(tableAPT, tableAPT['id'].eq(tableAP['type_id']))
                table = table.innerJoin(tableAPJT, tableAP['id'].eq(tableAPJT['id']))
                table = table.innerJoin(tableJT, tableAPJT['value'].eq(tableJT['id']))
                cond = [tableAction['id'].eq(actionId),
                        tableJT['deleted'].eq(0),
                        tableAPT['deleted'].eq(0),
                        tableAPT['actionType_id'].eq(tableAction['actionType_id']),
                        tableAP['action_id'].eq(tableAction['id']),
                        tableAPT['typeName'].like('JobTicket'),
                        tableJT['id'].isNotNull()
                        ]
                record = db.getRecordEx(table, [tableAPJT['value']], cond, order=tableAPJT['id'].name())
                if record:
                    jobTicketId = forceRef(record.value('value'))
                    return toVariant(getJobTicketAsText(jobTicketId)) if jobTicketId else QVariant()
                return CCol.invalid
            return CCol.invalid


    class CLocClientColumn(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')


        def format(self, values):
            val = values[0]
            eventId  = forceRef(val)
            if eventId:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                tableClient = db.table('Client')
                table = tableEvent.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))

                clientRecord = db.getRecordEx(table, [tableClient['lastName'], tableClient['firstName'], tableClient['patrName']], [tableEvent['deleted'].eq(0), tableClient['deleted'].eq(0), tableEvent['id'].eq(eventId)])
                if clientRecord:
                    name  = formatShortNameInt(forceString(clientRecord.value('lastName')),
                                                    forceString(clientRecord.value('firstName')),
                                                    forceString(clientRecord.value('patrName')))
                    return toVariant(name)
                return CCol.invalid
            return CCol.invalid


    class CLocClientIdentifierColumn(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.identifiersCache = CRecordCache()


        def getClientIdentifier(self, clientId):
            identifier = self.identifiersCache.get(clientId)
            if identifier is None:
                accountingSystemId = QtGui.qApp.defaultAccountingSystemId()
                if accountingSystemId is None:
                    identifier = clientId
                else:
                    db = QtGui.qApp.db
                    tableClientIdentification = db.table('ClientIdentification')
                    cond = [tableClientIdentification['client_id'].eq(clientId),
                            tableClientIdentification['accountingSystem_id'].eq(accountingSystemId)]
                    record = db.getRecordEx(tableClientIdentification, tableClientIdentification['identifier'], cond)
                    identifier = forceString(record.value(0)) if record else ''
                self.identifiersCache.put(clientId, identifier)
            return identifier


        def format(self, values):
            val = values[0]
            eventId = forceRef(val)
            if eventId:
                db = QtGui.qApp.db
                table = db.table('Event')
                clientRecord = db.getRecordEx(table, [table['client_id'], table['externalId']], [table['deleted'].eq(0), table['id'].eq(eventId)])
                if clientRecord:
                    clientId = forceRef(clientRecord.value('client_id'))
                    externalId = forceString(clientRecord.value('externalId'))
                    return toVariant(forceString(self.getClientIdentifier(clientId)) + (u', карта %s'%(externalId) if externalId else u''))
            return CCol.invalid


    class CLocClientBirthDateColumn(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')


        def format(self, values):
            val = values[0]
            eventId  = forceRef(val)
            if eventId:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                tableClient = db.table('Client')
                table = tableEvent.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
                clientRecord = db.getRecordEx(table, [tableClient['birthDate']], [tableEvent['deleted'].eq(0), tableClient['deleted'].eq(0), tableEvent['id'].eq(eventId)])
                if clientRecord:
                    return toVariant(forceString(clientRecord.value('birthDate')))
            return CCol.invalid


    class CLocClientSexColumn(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')


        def format(self, values):
            val = values[0]
            eventId  = forceRef(val)
            if eventId:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                tableClient = db.table('Client')
                table = tableEvent.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
                clientRecord = db.getRecordEx(table, [tableClient['sex']], [tableEvent['deleted'].eq(0), tableClient['deleted'].eq(0), tableEvent['id'].eq(eventId)])
                if clientRecord:
                    return toVariant([u'', u'М', u'Ж'][forceInt(clientRecord.value('sex'))])
            return CCol.invalid


    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.clientCol   = CAttendanceActionsTableModel.CLocClientColumn( u'Ф.И.О.', ['event_id'], 60)
        self.clientIdentifierCol = CAttendanceActionsTableModel.CLocClientIdentifierColumn(u'Идентификатор', ['event_id'], 30)
        self.clientBirthDateCol = CAttendanceActionsTableModel.CLocClientBirthDateColumn(u'Дата рожд.', ['event_id'], 20)
        self.clientSexCol = CAttendanceActionsTableModel.CLocClientSexColumn(u'Пол', ['event_id'], 5)
        self.addColumn(self.clientCol)
        self.addColumn(self.clientBirthDateCol)
        self.addColumn(self.clientSexCol)
        self.addColumn(CDateTimeFixedCol(u'Назначено',      ['directionDate'], 15))
        self.addColumn(CAttendanceActionsTableModel.CLocPresenceOSColumn( u'Отделение пребывания', ['event_id'], 60))
        self.addColumn(CAttendanceActionsTableModel.CLocJobTicketColumn( u'Номерок', ['id'], 60))
        self.addColumn(CActionTypeCol(u'Действие', 15))
        self.addColumn(CBoolCol(u'Срочно',         ['isUrgent'],      15))
        self.addColumn(CIntCol(u'Д',               ['duration'],      15))
        self.addColumn(CIntCol(u'И',               ['periodicity'],   15))
        self.addColumn(CIntCol(u'К',               ['aliquoticity'],  15))
        self.addColumn(CEnumCol(u'Состояние',      ['status'], CActionStatus.names, 4))
        self.addColumn(CDateTimeFixedCol(u'Начато',     ['begDate'],       15))
        self.addColumn(CDateTimeFixedCol(u'Окончено',   ['endDate'],       15))
        self.addColumn(CDateCol(u'План',           ['plannedEndDate'],15))
        self.addColumn(CRefBookCol(u'Назначил',    ['setPerson_id'], 'vrbPersonWithSpeciality', 20))
        self.addColumn(CRefBookCol(u'Выполнил',    ['person_id'],    'vrbPersonWithSpeciality', 20))
        self.addColumn(CTextCol(u'Каб',            ['office'],                                6))
        self.addColumn(CTextCol(u'Примечания',     ['note'],                                  6))
        self.setTable('Action')
        self._mapColumnToOrder = {u'event_id'           :u'CONCAT(Client.lastName, Client.firstName, Client.patrName)',
                                 u'birthDate'          :u'Client.birthDate',
                                 u'sex'                :u'Client.sex',
                                 u'directionDate'      :u'Action.directionDate',
                                 u'actionType_id'      :u'AT.name',
                                 u'duration'           :u'Action.duration',
                                 u'periodicity'        :u'Action.periodicity',
                                 u'aliquoticity'       :u'Action.aliquoticity',
                                 u'isUrgent'           :u'Action.isUrgent',
                                 u'status'             :u'Action.status',
                                 u'plannedEndDate'     :u'Action.plannedEndDate',
                                 u'begDate'            :u'Action.begDate',
                                 u'endDate'            :u'Action.endDate',
                                 u'setPerson_id'       :u'vrbSetPersonWithSpeciality.name',
                                 u'person_id'          :u'vrbPersonWithSpeciality.name',
                                 u'office'             :u'Action.office',
                                 u'note'               :u'Action.note',
                                 }


    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        return CTableModel.headerData(self, section, orientation, role)


    def flags(self, index):
        enabled = True
        if enabled:
            return Qt.ItemIsEnabled|Qt.ItemIsSelectable
        else:
            return Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        loadFields = []
        loadFields.append(u'''Client.id AS clientId, CONCAT_WS(' ', Client.lastName, Client.firstName,
        Client.patrName) AS FIO, Client.birthDate, Client.sex, Action.id, Action.event_id,
        Action.directionDate, Action.isUrgent, Action.plannedEndDate,
        Action.begDate, Action.endDate, Action.actionType_id, Action.status, Action.setPerson_id,
        Action.person_id, Action.office, Action.note, Action.specifiedName, Action.duration,
        Action.periodicity, Action.aliquoticity''')
        queryTable = tableAction.leftJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        self._table = queryTable
        self._recordsCache = CTableRecordCache(db, self._table, loadFields)


class CHospitalActionsTableModel(CAttendanceActionsTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CDateTimeFixedCol(u'Назначено',      ['directionDate'], 15))
        self.addColumn(CAttendanceActionsTableModel.CLocJobTicketColumn( u'Номерок', ['id'], 60))
        self.addColumn(CActionTypeCol(u'Действие', 15))
        self.addColumn(CBoolCol(u'Срочно',         ['isUrgent'],      15))
        self.addColumn(CIntCol(u'Д',               ['duration'],      15))
        self.addColumn(CIntCol(u'И',               ['periodicity'],   15))
        self.addColumn(CIntCol(u'К',               ['aliquoticity'],  15))
        self.addColumn(CEnumCol(u'Состояние',      ['status'], CActionStatus.names, 4))
        self.addColumn(CDateTimeFixedCol(u'Начато',     ['begDate'],       15))
        self.addColumn(CDateTimeFixedCol(u'Окончено',   ['endDate'],       15))
        self.addColumn(CDateCol(u'План',           ['plannedEndDate'],15))
        self.addColumn(CRefBookCol(u'Назначил',    ['setPerson_id'], 'vrbPersonWithSpeciality', 20))
        self.addColumn(CRefBookCol(u'Выполнил',    ['person_id'],    'vrbPersonWithSpeciality', 20))
        self.addColumn(CTextCol(u'Каб',            ['office'],                                6))
        self.addColumn(CTextCol(u'Примечания',     ['note'],                                  6))
        self.addColumn(CTextCol(u'Ф.И.О.', ['FIO'], 60))
        self.addColumn(CDateCol(u'Дата рожд.', ['birthDate'], 20, highlightRedDate=False))
        self.addColumn(CEnumCol(u'Пол', ['sex'], ['', u'М', u'Ж'], 5))
        self.setTable('Action')


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.ToolTipRole:
                if section == 3:
                    return QVariant(u'Длительность курса лечения в днях.')
                elif section == 4:
                    return QVariant(u'''Интервал: 0 - каждый день,
                                        1 - через 1 день,
                                        2 - через 2 дня,
                                        3 - через 3 дня,
                                        и т.д.''')
                elif section == 5:
                    return QVariant(u'Сколько раз в сутки.')
        return CAttendanceActionsTableModel.headerData(self, section, orientation, role)


def getDateReceivedCol():
    db = QtGui.qApp.db
    table = db.table('Action').alias('AR')
    return '(SELECT MIN(`AR`.`endDate`) '\
            'FROM `Action` AS `AR` '\
            'WHERE `AR`.`event_id`=`Action`.`event_id` '\
            'AND `AR`.`deleted`=0 '\
            'AND %s '\
            'AND `AR`.`status`=2) AS begDateReceived' % table['actionType_id'].inlist(getActionTypeIdListByFlatCode('received%'))


def getDateLeavedCol():
    db = QtGui.qApp.db
    table = db.table('Action').alias('AL')
    return '(SELECT MAX(`AL`.`endDate`) '\
            'FROM `Action` AS `AL` '\
            'WHERE `AL`.`event_id`=`Action`.`event_id` '\
            'AND `AL`.`deleted`=0 '\
            'AND %s '\
            'AND `AL`.`status`=2) AS endDateLeaved' % table['actionType_id'].inlist(getActionTypeIdListByFlatCode('leaved%'))


def getDeliverByCond(deliverBy):
    if deliverBy:
        if deliverBy == u'без уточнения':
            cond = ' is NULL '
        else:
            cond = '= \'%s\' '%deliverBy
    else:
        'as \'deliveredBy\''
    return u'''
    (select APS.value from
            ActionType as AT
            left join Action as A on A.actionType_id = AT.id
            left join ActionPropertyType as APT on APT.actionType_id = AT.id
            left join ActionProperty AS AP on AP.type_id = APT.id
            left join ActionProperty_String AS APS ON APS.id = AP.id

            where AT.flatCode = 'received'
            and A.event_id = Event.id
            and AP.action_id = A.id
            and AT.deleted = 0
            and APT.name = 'Кем доставлен') %s
    ''' %cond


def getPlacement():
    return u'''(SELECT
            OSP.name
        FROM
            ActionPropertyType AS APT
                INNER JOIN
            ActionProperty AS AP ON AP.type_id = APT.id
                INNER JOIN
            ActionProperty_OrgStructure_Placement AS APOS ON APOS.id = AP.id
                INNER JOIN
            OrgStructure_Placement as OSP on OSP.id = APOS.value
        WHERE
            (AP.action_id = Action.id)
                AND (APT.actionType_id = Action.actionType_id
                AND APT.deleted = 0
                AND APT.name = 'Помещение') LIMIT 1) as \'placement\' '''


def getPlacementCond(placement):
    placementCond = ('EXISTS',  'AND OSP.id = %i'%placement, '') if placement else ('', '', 'is NULL')
    return u'''%s(SELECT
            OSP.name
        FROM
            ActionPropertyType AS APT
                INNER JOIN
            ActionProperty AS AP ON AP.type_id = APT.id
                INNER JOIN
            ActionProperty_OrgStructure_Placement AS APOS ON APOS.id = AP.id
                INNER JOIN
            OrgStructure_Placement as OSP on OSP.id = APOS.value
        WHERE
            (AP.action_id = Action.id)
                %s
                AND (APT.actionType_id = Action.actionType_id
                AND APT.deleted = 0
                AND APT.name = 'Помещение')) %s ''' % (placementCond[0], placementCond[1], placementCond[2])


def getClientFeatures():
    return u'''(SELECT MAX(ClientAllergy.power) FROM ClientAllergy where Client.id=ClientAllergy.client_id) as clientAllergy,
                    (SELECT MAX(ClientIntoleranceMedicament.power) FROM ClientIntoleranceMedicament where Client.id=ClientIntoleranceMedicament.client_id) as clientIntoleranceMedicament'''


def getPatronFeatures():
    return u'''(SELECT MAX(ClientAllergy.power) FROM ClientAllergy where Event.relative_id=ClientAllergy.client_id) as patronAllergy,
                    (SELECT MAX(ClientIntoleranceMedicament.power) FROM ClientIntoleranceMedicament where Event.relative_id=ClientIntoleranceMedicament.client_id) as patronIntoleranceMedicament'''


def getStatusObservation():
    return '''(SELECT CONCAT_WS('|', IF(rbStatusObservationClientType.code IS NOT NULL, rbStatusObservationClientType.code, ''), IF(rbStatusObservationClientType.name IS NOT NULL, rbStatusObservationClientType.name, ''), IF(rbStatusObservationClientType.color IS NOT NULL, rbStatusObservationClientType.color, ''),
    CONCAT_WS(' ', DATE_FORMAT(Client_StatusObservation.createDatetime, '%d.%m.%Y'), TIME_FORMAT(Client_StatusObservation.createDatetime, '%H:%i:%S')), vrbPersonWithSpeciality.name)
FROM Client_StatusObservation
LEFT JOIN rbStatusObservationClientType ON rbStatusObservationClientType.id = Client_StatusObservation.statusObservationType_id
LEFT JOIN vrbPersonWithSpeciality ON vrbPersonWithSpeciality.id = Client_StatusObservation.createPerson_id
WHERE Client_StatusObservation.deleted = 0 AND Client_StatusObservation.master_id = Client.id
ORDER BY Client_StatusObservation.createDatetime DESC
LIMIT 0,1) AS statusObservation'''


def getCurrentOSHB():
    return '''(SELECT CONCAT_WS('  ', OSHB.code, OSHB.name, IF(OSHB.sex=1, \'%s\', IF(OSHB.sex=2, \'%s\', ' ')))
FROM Action AS A
INNER JOIN ActionType AS AT ON AT.id=A.actionType_id
INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=AT.id
INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
INNER JOIN ActionProperty_HospitalBed AS APHB ON APHB.id=AP.id
INNER JOIN OrgStructure_HospitalBed AS OSHB ON OSHB.id=APHB.value
INNER JOIN OrgStructure AS OS ON OS.id=OSHB.master_id
WHERE (A.event_id=Event.id) AND (A.deleted=0) AND (AP.deleted=0) AND (OS.deleted=0)
AND (APT.typeName = 'HospitalBed') AND (AP.action_id=A.id)
AND (A.endDate IS NULL)
) AS bedCodeName'''%(forceString(u''' /М'''), forceString(u''' /Ж'''))


def getDataAPHB(permanent=0, type=0, profile=0, codeBeds=None):
    strFilter = u''''''
    strSelected = u''''''
    if permanent and permanent > 0:
        strFilter += u''' AND OSHB.isPermanent=%s'''%(forceString(permanent - 1))
    if type:
        strFilter += u''' AND OSHB.type_id=%s'''%(forceString(type))
    if codeBeds:
        strFilter += u''' AND OSHB.code %s '''%(updateLIKE(codeBeds))
    if profile:
        if QtGui.qApp.defaultHospitalBedProfileByMoving():
            strSelected = getHospitalBedProfile([profile]) + u''' AND '''
        else:
            strFilter += u''' AND OSHB.profile_id=%s'''%(forceString(profile))
    strSelected += '''EXISTS(SELECT APHB.value
FROM ActionPropertyType AS APT
INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
INNER JOIN ActionProperty_HospitalBed AS APHB ON APHB.id=AP.id
INNER JOIN OrgStructure_HospitalBed AS OSHB ON OSHB.id=APHB.value
WHERE APT.actionType_id=Action.actionType_id AND AP.action_id=Action.id
AND AP.deleted=0 AND APT.deleted=0 AND APT.typeName = 'HospitalBed'%s)'''%(strFilter)
    return strSelected


def isScheduleBeds(scheduleId):
    return '''EXISTS(SELECT APHB.value
FROM ActionPropertyType AS APT
INNER JOIN ActionProperty AS AP ON AP.type_id = APT.id
INNER JOIN ActionProperty_HospitalBed AS APHB ON APHB.id = AP.id
INNER JOIN OrgStructure_HospitalBed AS OSHB ON OSHB.id = APHB.value
WHERE APT.actionType_id = Action.actionType_id AND AP.action_id = Action.id
AND AP.deleted = 0 AND APT.deleted = 0 AND APT.typeName = 'HospitalBed'
AND OSHB.schedule_id = %s)'''%(scheduleId)


def getHospitalBedProfile(profileList):
    return '''EXISTS(SELECT APHBP.value
FROM ActionPropertyType AS APT_Profile
INNER JOIN ActionProperty AS AP_Profile ON AP_Profile.type_id=APT_Profile.id
INNER JOIN ActionProperty_rbHospitalBedProfile AS APHBP ON APHBP.id=AP_Profile.id
INNER JOIN rbHospitalBedProfile AS RBHBP ON RBHBP.id=APHBP.value
WHERE APT_Profile.actionType_id = Action.actionType_id
AND AP_Profile.action_id = Action.id
AND AP_Profile.deleted = 0
AND APT_Profile.deleted = 0
AND APT_Profile.typeName = 'rbHospitalBedProfile'
AND APHBP.value IN (%s))'''%(','.join(str(profileId) for profileId in profileList if profileId))


def getOSHBP():
    return '''(SELECT RBHBP.name
FROM ActionPropertyType AS APT_Profile
INNER JOIN ActionProperty AS AP_Profile ON AP_Profile.type_id=APT_Profile.id
INNER JOIN ActionProperty_rbHospitalBedProfile AS APHBP ON APHBP.id=AP_Profile.id
INNER JOIN rbHospitalBedProfile AS RBHBP ON RBHBP.id=APHBP.value
WHERE APT_Profile.actionType_id = Action.actionType_id
AND AP_Profile.action_id = Action.id
AND AP_Profile.deleted = 0
AND APT_Profile.deleted = 0
AND APT_Profile.typeName = 'rbHospitalBedProfile'
LIMIT 1) as 'profileName'
'''


def getActionPropertyTypeName(nameProperty):
    return '''EXISTS(SELECT APT.id
FROM ActionPropertyType AS APT
INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
WHERE (AP.action_id=Action.id)
AND (APT.actionType_id=Action.actionType_id AND APT.deleted=0 AND APT.name %s))'''%(updateLIKE(nameProperty))


def getEventFeedId(typeFeed, dateFeed, alias=u'', refusalToEat = -1):
    return u'''EXISTS(SELECT EF.id
    FROM Event_Feed AS EF
    WHERE EF.event_id = Action.event_id AND EF.deleted = 0%s%s
    AND DATE(EF.date) = %s%s)%s'''%(u' AND EF.typeFeed = %s' % (typeFeed) if typeFeed else u'',
    u' AND EF.refusalToEat = %s'%(refusalToEat) if refusalToEat > -1 else u'',
    dateFeed,
    u' ORDER BY EF.refusalToEat DESC' if refusalToEat > -1 else u'',
    alias)


def getDietCode(typeFeed, dateFeed, alias=u'', refusalToEat = -1):
    return u'''(SELECT rbDiet.code
    FROM Event_Feed AS EF
    INNER JOIN rbDiet ON rbDiet.id = EF.diet_id
    WHERE EF.id = (SELECT MAX(EF2.id)
               FROM Event_Feed AS EF2
               WHERE EF2.event_id = Action.event_id AND EF2.deleted = 0%s%s
    AND DATE(EF2.date) = %s%s))%s'''%(u' AND EF2.typeFeed = %s' % (typeFeed) if typeFeed else u'',
    u' AND EF2.refusalToEat = %s'%(refusalToEat) if refusalToEat > -1 else u'',
    dateFeed,
    u' ORDER BY EF2.refusalToEat DESC' if refusalToEat > -1 else u'',
    alias)


def getEventRefusalToEat(typeFeed, dateFeed, alias=u''):
    return u'''(SELECT EF.refusalToEat
    FROM Event_Feed AS EF
    WHERE EF.event_id = Action.event_id AND EF.deleted = 0%s
    AND DATE(EF.date) = %s
    ORDER BY EF.refusalToEat DESC
    LIMIT 1)%s'''%(u' AND EF.typeFeed = %s' % (typeFeed) if typeFeed else u'', dateFeed, alias)


def getPropertyAPOS(nameProperty, actionTypeIdList):
    return u'''(EXISTS(SELECT APOS.value
    FROM Event AS E
    INNER JOIN Action AS A ON A.event_id = E.id
    INNER JOIN ActionType AS AT ON AT.id=A.actionType_id
    INNER JOIN ActionPropertyType AS APT ON AT.id = APT.actionType_id
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id AND AP.action_id = A.id
    INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
    WHERE E.client_id = Event.client_id AND E.deleted = 0 AND A.deleted = 0 AND AT.deleted = 0 AND AP.deleted = 0
    AND A.endDate IS NOT NULL AND (Action.plannedEndDate IS NULL OR (DATE(A.begDate) <= DATE(Action.plannedEndDate)
    AND DATE(Action.plannedEndDate) <= DATE(A.endDate))) AND APT.deleted=0 AND APT.name %s
    AND A.actionType_id IN (%s))) AS APOS_value'''%(updateLIKE(nameProperty), ','.join(str(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId))


def getReceivedEndDate(nameProperty, actionTypeIdList):
    return u'''(SELECT A.endDate
    FROM Event AS E
    INNER JOIN Action AS A ON A.event_id = E.id
    INNER JOIN ActionType AS AT ON AT.id=A.actionType_id
    INNER JOIN ActionPropertyType AS APT ON AT.id = APT.actionType_id
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id AND AP.action_id = A.id
    INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
    WHERE E.id = getActionReceivedFirstEventId(Event.id) AND E.deleted = 0 AND A.deleted = 0 AND AT.deleted = 0 AND AP.deleted = 0 AND APOS.value IS NOT NULL
    AND APT.deleted=0 AND APT.name %s AND A.actionType_id IN (%s) LIMIT 1) AS receivedEndDate'''%(updateLIKE(nameProperty),
    ','.join(str(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId))


def getReceivedBegDate(actionTypeIdList):
    return u'''(SELECT A.begDate
    FROM Event AS E
    INNER JOIN Action AS A ON A.event_id = E.id
    WHERE E.id = getActionReceivedFirstEventId(Event.id) AND E.deleted = 0 AND A.deleted = 0
    AND A.actionType_id IN (%s)
    ORDER BY A.begDate LIMIT 1) AS receivedBegDate'''%(','.join(str(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId))


def getLeavedEndDate(actionTypeIdList):
    return u'''(SELECT A.endDate
    FROM Event AS E
    INNER JOIN Action AS A ON A.event_id = E.id
    WHERE E.id = getActionLeavedLastEventId(Event.id) AND E.deleted = 0 AND A.deleted = 0
    AND A.actionType_id IN (%s)
    ORDER BY A.endDate LIMIT 1) AS leavedEndDate'''%(','.join(str(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId))


def getActionByFlatCode(actionTypeIdList):
    db = QtGui.qApp.db
    tableAction = db.table('Action')
    return '''(SELECT CONCAT_WS('  ', A.plannedEndDate, A.payStatus)
FROM Action AS A
WHERE A.event_id = Event.id AND A.actionType_id IN (%s) AND A.deleted=0 AND A.plannedEndDate >= %s
ORDER BY A.plannedEndDate ASC
LIMIT 1) AS comfortable'''%(u', '.join(str(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId) , tableAction['begDate'].formatValue(QDateTime.currentDateTime()))


def getMovingActionForPlannedDate(actionTypeIdList):
    return u'''(SELECT A.id
    FROM Event AS E
    INNER JOIN Action AS A ON A.event_id = E.id
    WHERE E.client_id = Event.client_id AND E.deleted = 0 AND A.deleted = 0
    AND A.begDate IS NOT NULL AND (DATE(A.begDate) <= DATE(Action.plannedEndDate)
    AND DATE(Action.endDate) <= DATE(A.begDate))
    AND A.actionType_id IN (%s)
    ORDER BY A.begDate ASC
    LIMIT 1) AS movingActionId'''%(','.join(str(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId))


def isPlanningToHospitalization():
    return u'''EXISTS(SELECT E.id
    FROM Event AS E
    INNER JOIN EventType AS ET ON ET.id = E.eventType_id
    WHERE E.prevEvent_id = Action.event_id AND E.deleted = 0 AND ET.deleted = 0
    AND Action.deleted = 0 AND (ET.medicalAidType_id IN (SELECT MAT.id from rbMedicalAidType AS MAT where MAT.code IN ('8')))
    )'''


class CReportF001SetupDialog(QtGui.QDialog, Ui_ReportF001SetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)


    def setParams(self, params):
        self.chkClientId.setChecked(params.get('chkClientId', True))
        self.chkEventId.setChecked(params.get('chkEventId', False))
        self.chkExternalEventId.setChecked(params.get('chkExternalEventId', False))
        self.chkPrintTypeEvent.setChecked(params.get('chkPrintTypeEvent', False))
        self.cmbCondSort.setCurrentIndex(params.get('condSort', 0))
        self.cmbCondOrgStructure.setCurrentIndex(params.get('condOrgStructure', 0))
        self.cmbPrintTypeMKB.setCurrentIndex(params.get('printTypeMKB', 0))
        self.chkSelectClients.setChecked(params.get('chkSelectClients', 0))


    def params(self):
        result = {}
        result['chkClientId'] = self.chkClientId.isChecked()
        result['chkEventId']  = self.chkEventId.isChecked()
        result['chkExternalEventId'] = self.chkExternalEventId.isChecked()
        result['chkPrintTypeEvent']  = self.chkPrintTypeEvent.isChecked()
        result['chkSelectClients']   = self.chkSelectClients.isChecked()
        result['condSort']           = self.cmbCondSort.currentIndex()
        result['condOrgStructure']   = self.cmbCondOrgStructure.currentIndex()
        result['printTypeMKB']       = self.cmbPrintTypeMKB.currentIndex()
        return result


class CHospitalizationExecDialog(QtGui.QDialog, Ui_HospitalizationExecDialog):
    def __init__(self, eventId, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.edtExecDate.setFocus(Qt.OtherFocusReason)
        self.edtExecDate.setDate(QDate.currentDate())
        self.edtExecTime.setTime(QTime.currentTime())
        db = QtGui.qApp.db
        tableAT = db.table('ActionType')
        tableAP = db.table('ActionPropertyType')
        table = tableAT.leftJoin(tableAP, tableAT['id'].eq(tableAP['actionType_id']))
        cond = [tableAT['deleted'].eq(0),
                    tableAT['flatCode'].eq('leaved'),
                    tableAP['deleted'].eq(0),
                    tableAP['name'].like(u'Исход госпитализации'),
                    tableAP['typeName'].eq('String')
                ]
        record = db.getRecordEx(table, 'valueDomain', cond)
        self.values = []
        if record:
            values = forceString(record.value(0))
            self.values = values.replace('\'', '').split(',')
            self.values.insert(0, '')
            self.cmbExec.insertItems(0, self.values)

        self.cmbMesSpecification.setTable('rbMesSpecification')
        tableEvent = db.table('Event')
        record = db.getRecordEx(tableEvent, [tableEvent['MES_id'].name(), tableEvent['mesSpecification_id'].name(), tableEvent['execPerson_id'].name()],
                                                [tableEvent['id'].eq(eventId)])
        if record:
            self.cmbMes.setValue(forceRef(record.value(0)))
            self.cmbMesSpecification.setValue(forceRef(record.value(1)))
            self.cmbPerson.setValue(forceRef(record.value('execPerson_id')))

        currentOrgId = QtGui.qApp.currentOrgId()
        currentOrgStructureId = QtGui.qApp.currentOrgStructureId()
        if currentOrgStructureId:
            self.cmbPerson.setOrganisationId(currentOrgId)
            self.cmbPerson.setOrgStructureId(currentOrgStructureId)


    def params(self):
        result = {}
        date = self.edtExecDate.date()
        time = self.edtExecTime.time()
        result['ExecDateTime'] = QDateTime(date, QTime(time.hour(), time.minute()))
        result['ExecPerson'] = self.cmbPerson.value()
        result['ExecResult'] = self.values[self.cmbExec.currentIndex()]
        result['mesId'] = self.cmbMes.value()
        result['mesSpecification'] = self.cmbMesSpecification.value()
        return result


    @pyqtSignature('QString')
    def on_cmbExec_currentIndexChanged(self, string):
        flag = string.contains(QString(u'другой стационар'))
        self.lblTransferTo.setEnabled(flag)
        self.edtTransferTo.setEnabled(flag)
        self.btnSelectTransferToOrganisation.setEnabled(flag)


    @pyqtSignature('')
    def on_btnSelectTransferToOrganisation_clicked(self):
        orgId = selectOrganisation(self, None, False, filter='isMedical != 0')
        if orgId:
            self.edtTransferTo.setText(getOrganisationShortName(orgId))


    def done(self, r):
        if r > 0:
            dateTime = QDateTime(self.edtExecDate.date(), self.edtExecTime.time())
            if dateTime > QDateTime.currentDateTime():
                res = QtGui.QMessageBox.warning( self,
                                         u'Внимание!',
                                         u'Вы указали будущее время для данного Действия!',
                                         QtGui.QMessageBox.Ok|QtGui.QMessageBox.Ignore,
                                         QtGui.QMessageBox.Ok)
                if res == QtGui.QMessageBox.Ok:
                    self.edtExecDate.setFocus(Qt.ShortcutFocusReason)
                    return
            if self.edtTransferTo.isEnabled():
                if self.edtTransferTo.text()==u'':
                        QtGui.QMessageBox.critical(self,
                            u'Внимание!',
                            u'Необходимо заполнить поле "Переведен в стационар".',
                            QtGui.QMessageBox.Ok,
                            QtGui.QMessageBox.Ok)
                        return
        QtGui.QDialog.done(self, r)


class CHBPatronEditorDialog(QtGui.QDialog, Ui_HBPatronEditorDialog):
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)

    def setClientId(self, clientId):
        self.cmbPatron.setClientId(clientId)

    def setCurrentPatronId(self, patronId):
        self.cmbPatron.setValue(patronId)

    def getPatronId(self):
        return self.cmbPatron.value()


def updateDurationEvent(begDate, endDate, begDateFilter, endDateFilter, eventTypeId, isPresence):
    if not endDate:
        if isPresence:
            endDate = endDateFilter.date() if endDateFilter else QDate.currentDate()
        else:
            endDate = QDate.currentDate()
    text = '-'
    if begDate:
        duration = begDate.daysTo(endDate)+getEventDurationRule(eventTypeId)
        if duration > 0:
            text = str(duration)
    return text


def getReceivedMKB():
    return '''(SELECT Diagnosis.MKB
FROM Diagnosis INNER JOIN Diagnostic ON Diagnostic.diagnosis_id=Diagnosis.id
INNER JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id=rbDiagnosisType.id
WHERE Diagnostic.event_id = Event.id AND Diagnosis.deleted = 0 AND Diagnostic.deleted = 0
AND (rbDiagnosisType.code = '1'
OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
AND DC.event_id = Event.id AND DC.deleted = 0
LIMIT 1)))
OR (rbDiagnosisType.code = '7' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
AND DC.event_id = Event.id AND DC.deleted = 0
LIMIT 1)) AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '2'
AND DC.event_id = Event.id AND DC.deleted = 0
LIMIT 1))))
ORDER BY Diagnosis.id
LIMIT 1) AS MKB'''


def isContractPropertyValue(nameProperty, value):
    return u'''EXISTS(SELECT APC.id
    FROM ActionProperty AS AP
    INNER JOIN ActionPropertyType AS APT ON AP.type_id = APT.id
    INNER JOIN ActionProperty_Contract AS APC ON APC.id = AP.id
    INNER JOIN Contract AS C ON C.id = APC.value
    WHERE AP.action_id = Action.id AND APT.actionType_id = Action.actionType_id
    AND  Action.id IS NOT NULL AND C.deleted = 0 AND Action.deleted = 0
    AND APT.deleted=0 AND AP.deleted=0 AND APT.name %s AND APC.value = %s
    )'''%(updateLIKE(nameProperty), value)

