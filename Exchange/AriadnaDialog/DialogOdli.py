# -*- coding: utf-8 -*-
import logging
from logging.handlers import RotatingFileHandler

from Ui_Odli import Ui_DialogOdli
from library.DialogBase import CDialogBase
from library.TableModel import *
from OdliUtils import *
from Events.CreateEvent import *

# Таблица полей Типа действия
from library.database import addDateInRange, CTableRecordCache
from PyQt4.QtCore import (
    Qt,
    pyqtSignature, QDir, )

TASK_SEND_ORDER = 1
TASK_GET_RESULT = 2

class CTabName(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Номер направления', ['number'], 30))
        self.addColumn(CTextCol(u'Пациент', ['clientName'], 25))
        self.addColumn(CTextCol(u'Подразделение', ['orgStructure'], 25))
        self.addColumn(CTextCol(u'Лечащий врач', ['EventPerson'], 30))
        self.addColumn(CTextCol(u'Дата отправки', ['CreateDate'], 25))
        self.addColumn(CTextCol(u'Дата получения результата', ['responseDataTime'], 25))
        self.addColumn(CTextCol(u'Идентификатор пациента', ['clientId'], 25))
        self.addColumn(CTextCol(u'Наименование анализа', ['analisis'], 25))
        self.addColumn(CTextCol(u'Статус', ['status'], 25))
        self.setTable()

    def setTable(self):
        db = QtGui.qApp.db
        tableAction_ExportA = db.table('''Action_Export''').alias('aeA')
        tableAction_ExportL = db.table('''Action_Export''').alias('aeL')
        tableEvent = db.table('''Event''')
        tablePerson = db.table('''Person''')
        tableClient = db.table('''Client''')
        tableAction = db.table('''Action''')
        tableOrgStructure = db.table('''OrgStructure''')
        tableActionType = db.table('''ActionType''')
        tableActionPropertyType = db.table('''ActionPropertyType''').alias('apt')
        tableActionProperty = db.table('''ActionProperty''').alias('ap')
        tableActionProperty_String = db.table('''ActionProperty_String''').alias('aps')
        tableEvPerson = db.table('Person').alias('doc')

        loadFields = []
        loadFields.append(u''' concat_ws(' ',Person.lastName, Person.firstName,  Person.patrName) as EventPerson, 
                                concat_ws(' ',doc.lastName, doc.firstName,  doc.patrName) as ExpPerson,
                                case 
                                  when Action.note <> '' 
                                  then DATE_FORMAT(Action.begDate, '%Y-%m-%d %H:%i:%S') end as CreateDate,  
                                case 
                                  when Action.`note` like 'Результат загружен из ЛИС%' or Action.`note` like 'Исследование отменено%' 
                                  then DATE_FORMAT(
                                        case
                                          when ActionType.flatCode LIKE '%alisa%' then aeL.dateTime
                                          else aeA.dateTime
                                        end,
                                        '%Y-%m-%d %H:%i:%S'
                                  ) 
                                end as responseDataTime, 
                                concat_ws(' ',Client.lastName, Client.firstName,  Client.patrName) as clientName, 
                                case 
                                  when Action.note <> '' 
                                  then Action.note else 'Не выгружен' end as status,
			                    Event.client_id as clientId, 
			                    aps.value as number, 
			                    ActionType.name as analisis, 
			                    OrgStructure.name as orgStructure''')

        ariadnaId = getExternalSystemIdByCode('AriadnaLIS', -1)
        alisaId = getExternalSystemIdByCode('AlisaLIS', -1)

        queryTable = tableAction.leftJoin(tableAction_ExportA, ''' Action.id = aeA.master_id and aeA.system_id = {0}'''.format(ariadnaId))
        queryTable = queryTable.leftJoin(tableAction_ExportL,
                                          ''' Action.id = aeL.master_id and aeL.system_id = {0}'''.format(alisaId))
        queryTable = queryTable.leftJoin(tableEvent, ''' Action.event_id = Event.id''')
        queryTable = queryTable.leftJoin(tablePerson, ''' Person.id = Event.execPerson_id''')
        queryTable = queryTable.leftJoin(tableClient, ''' Client.id = Event.client_id''')
        queryTable = queryTable.leftJoin(tableOrgStructure, ''' Person.orgStructure_id = OrgStructure.id''')
        queryTable = queryTable.leftJoin(tableActionType, ''' ActionType.id = Action.actionType_id and ActionType.serviceType = 10 and (ActionType.flatCode LIKE '%ariadna%' or ActionType.flatCode LIKE '%alisa%') ''')
        queryTable = queryTable.leftJoin(tableActionPropertyType, u''' ActionType.id = apt.actionType_id and apt.deleted=0 and apt.name = 'Номер направления' ''')
        queryTable = queryTable.leftJoin(tableActionProperty, ''' Action.id = ap.action_id and ap.deleted=0 and ap.type_id = apt.id''')
        queryTable = queryTable.leftJoin(tableActionProperty_String, '''aps.id = ap.id''')
        queryTable = queryTable.leftJoin(tableEvPerson, ''' doc.id = Action.createPerson_id''')

        self._table = queryTable
        self._recordsCache = CTableRecordCache(db, self._table, loadFields)


class DialogOdli(CDialogBase, Ui_DialogOdli):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.addObject('mnuAPLoadPrevAction', QtGui.QMenu(self))
        self.addObject('actEvent', QtGui.QAction(u'Открыть обращение', self))
        self.addObject('actOrder', QtGui.QAction(u'Отправить результат', self))
        self.addObject('actResult', QtGui.QAction(u'Получить результат', self))
        self.mnuAPLoadPrevAction.addAction(self.actResult)
        self.mnuAPLoadPrevAction.addAction(self.actOrder)
        self.mnuAPLoadPrevAction.addAction(self.actEvent)
        self.setupUi(self)

        self.addModels('tabName', CTabName(self))
        self.setModels(self.tblActionODLI, self.modeltabName)
        self.tblActionODLI.setPopupMenu(self.mnuAPLoadPrevAction)
        self.updateTblName()

    def updateTblName(self):
        status = u''
        db = QtGui.qApp.db

        table = db.table('Action').alias('a')
        if self.cmbStatus.currentIndex():
            val = self.cmbStatus.currentText()
            if val == u'Не выгружен в ЛИС':
                status += u''' and a.note = '' '''
            else:
                status += u' and a.note like "{0}%" '.format(val)
        orgStructure = u''
        if self.cmbOrgStructure.value():
            orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', self.cmbOrgStructure.value())
            orgStructure = u'and OrgStructure.id in (%s)' % (','.join(map(str, orgStructureIdList)))

        number = u''
        if forceString(self.Number.text()) != '':
            number = u' and aps.value = "{0}" '.format(forceString(self.Number.text()))
        clientfio = u''
        patr = u''
        firstName = u''
        if forceString(self.Client.text()) != '':
            filterClientName = forceString(self.Client.text())
            if filterClientName[0].isnumeric():
                clientfio = u' and Client.id = {0}'.format(forceInt(self.Client.text()))
            else:
                clientNames = filterClientName.split(u' ', 2)
                if len(clientNames) == 3:
                    clientfio = u'and Client.lastName like "{0}%"'.format(forceString(clientNames[0]))
                    firstName = u'and Client.firstName like "{0}%"'.format(forceString(clientNames[1]))
                    patr = u'and Client.patrName like "{0}%"'.format(forceString(clientNames[2]))
                elif len(clientNames) == 2:
                    clientfio = u'and Client.lastName like "{0}%"'.format(forceString(clientNames[0]))
                    firstName = u'and Client.firstName like "{0}%"'.format(forceString(clientNames[1]))
                else:
                    clientfio = u'and Client.lastName like "{0}%"'.format(forceString(clientNames[0]))
        datefilter = []

        addDateInRange(datefilter, table['begDate'], self.cmbDate.date(), self.cmbEndDate.date())

        cond = u'and ' + db.joinAnd(datefilter) if datefilter else ''
        smt = u'''select distinct  a.id as id
                    from Action a
                     left JOIN Event e on e.id = a.event_id
                     left join Client on Client.id=e.client_id
                     inner JOIN ActionType at ON at.id= a.actionType_id and at.serviceType = 10 and (at.flatCode LIKE '%ariadna%' or at.flatCode LIKE '%alisa%')
                     left join ActionPropertyType apt on apt.actionType_id = at.id and apt.deleted = 0 and apt.name = 'Номер направления'
                     left join ActionProperty ap on ap.action_id = a.id and ap.type_id = apt.id and ap.deleted = 0
                    left join ActionProperty_String aps on aps.id = ap.id
                    left join Person on Person.id = a.setPerson_id
                    left join OrgStructure on OrgStructure.id = Person.orgStructure_id
                    where e.deleted = 0 and a.deleted = 0 AND aps.value
                    {status} {clientfio} {patr} 
                    {firstName} {number} {cond} {orgStructure} order by a.id'''.format(
            status=status, clientfio=clientfio, patr=patr, firstName=firstName, number=number, cond=cond, orgStructure=orgStructure)
        query = db.query(smt)
        self.resultTblName = []
        while query.next():
            record = query.record()
            self.resultTblName.append(forceRef(record.value("id")))
        self.tblActionODLI.setIdList(self.resultTblName)
        self.lblRecordsCount.setText(formatRecordsCount(self.tblActionODLI.model().rowCount()))

    def enqueueLisTask(self, actionId, taskType):
        db = QtGui.qApp.db
        orderInfo = OrderMis(actionId)
        number = orderInfo.get('number')
        eventId = orderInfo.get('eventId')

        if not number:
            warninWindow(u'У направления отсутствует номер. Невозможно поставить в очередь.')
            return
        flatCode = getActionFlatCode(actionId).lower()
        if 'alisa' in flatCode:
            extCode = 'AlisaLIS'
        elif 'ariadna' in flatCode:
            extCode = 'AriadnaLIS'
        else:
            warninWindow(u'Не удалось определить ЛИС для направления.')
            return
        externalSystemId = getExternalSystemIdByCode(extCode)
        if not externalSystemId:
            warninWindow(u'Не найдена внешняя система {0}'.format(extCode))
            return
        personId = QtGui.qApp.userId

        try:
            sql = u'''
                INSERT INTO LisExchangeQueue
                    (action_id, event_id, externalSystem_id, taskType, number, createDatetime, createPerson_id)
                VALUES
                    ({actionId}, {eventId}, {externalSystemId}, {taskType}, {number}, NOW(), {personId})'''.format(
                actionId=actionId,
                eventId=eventId,
                externalSystemId=externalSystemId,
                taskType=taskType,
                number=number,
                personId=('NULL' if not personId else int(personId))
            )
            db.query(sql)
            if taskType == 1:
                warninWindow(u'Выгрузка направления в ЛИС поставлена в очередь.')
            if taskType == 2:
                warninWindow(u'Загрузка результата из ЛИС поставлена в очередь.')
        except Exception as e:
            msg = forceString(e)
            if 'Duplicate' in msg or 'duplicate' in msg:
                warninWindow(u'Задача уже есть в очереди.')
            else:
                warninWindow((u'Ошибка постановки в очередь: {0}'.format(anyToUnicode(e))))

    @pyqtSignature('')
    def on_btnAply_clicked(self):
        self.updateTblName()

    @pyqtSignature('')
    def on_btnCancel_2_clicked(self):
        self.cmbStatus.setCurrentIndex(0)
        self.Number.setText('')
        self.Client.setText('')
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(None)
        self.updateTblName()

    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()


    @pyqtSignature('')
    def on_actResult_triggered(self):
        actionId = self.tblActionODLI.currentItemId()
        self.enqueueLisTask(actionId, TASK_GET_RESULT)
        self.updateTblName()

    @pyqtSignature('')
    def on_actOrder_triggered(self):
        actionId = self.tblActionODLI.currentItemId()
        self.enqueueLisTask(actionId, TASK_SEND_ORDER)
        self.updateTblName()

    @pyqtSignature('')
    def on_actEvent_triggered(self):
        result = OrderMis(self.tblActionODLI.currentItemId())
        editEvent(self, result['eventId'])

    def getLogFilePath(self):
        self.logDir = os.path.join(unicode(QDir.toNativeSeparators(QDir.homePath())), '.samson-vista')
        if not os.path.exists(self.logDir):
            os.makedirs(self.logDir)
        return os.path.join(self.logDir, 'error.log')

    def initLogger(self):
        formatter = logging.Formatter(fmt='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        handler = RotatingFileHandler(self.getLogFilePath(), maxBytes=1024*1024*50, backupCount=10, encoding='UTF-8')
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        oldHandlers = list(logger.handlers)
        logger.addHandler(handler)
        for oldHandler in oldHandlers:
            logger.removeHandler(oldHandler)
        self.logger = logger
