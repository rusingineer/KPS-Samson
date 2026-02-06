# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, QTimer, QVariant

from library.DialogBase import CConstructHelperMixin
from library.TableModel import CQueryModel, CTextCol, CDateTimeCol, CTextListCol
from library.Utils import forceRef, forceInt, forceBool, forceString, formatRecordsCount, exceptionToUnicode

from Exchange.PyServices import getPyServices, CDistantMonitoringService

from Ui_RegistryNotificationPage import Ui_RegistryNotificationPage

class UserNotificationsMode:
    Standard = 1
    Extended = 2
    Default = Standard

class CRegistryNotificationPage(QtGui.QWidget, Ui_RegistryNotificationPage, CConstructHelperMixin):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.timer = None
        self.addModels('NotificationList', CNotificationListModel(self))
        self.addObject('actOpenSYSDMTasksPage', QtGui.QAction(u'Переход в СИС ДН планировщик', self))
        self.setupUi(self)
        self.tblNotificationList.addPopupAction(self.actOpenSYSDMTasksPage)
        self.tblNotificationList.popupMenuAboutToShow.connect(self.popupMenuAboutToShow)
        self.setModels(self.tblNotificationList, self.modelNotificationList, self.selectionModelNotificationList)
        db = QtGui.qApp.db
        self.userSnils = forceString(db.translate('Person', 'id', QtGui.qApp.userId, 'SNILS'))
        self.sysdmEventTypeId = forceRef(db.translate('EventType', 'code', 'SYSDM', 'id', nonDeleted=True))
        self.pyServices = getPyServices(CDistantMonitoringService)
    
    def setTabWidget(self, tabWidget):
        self.tabWidget = tabWidget
        self.tabWidget.tabShown.connect(self.on_tabWidget_tabShown)
        self.tabWidget.tabHidden.connect(self.on_tabWidget_tabHidden)
        self.tabWidget.currentChanged.connect(self.on_tabWidget_currentChanged)
        self.isCurrentTab = (self.tabWidget.currentWidget() == self)
        if not self.isCurrentTab and self.tabWidget.isTabVisible(self):
            self.startTimer()
        #self.updateNotificationList()

    def updateNotificationList(self):
        self.modelNotificationList.update()
        rowCount = self.modelNotificationList.rowCount()
        maxPriority = self.modelNotificationList.maxPriority()
        self.lblRecordCount.setText(formatRecordsCount(rowCount))
        tabIndex = self.tabWidget.indexOf(self)
        mode = QtGui.qApp.preferences.appPrefs.get('userNotificationsMode', UserNotificationsMode.Default)
        clientNameColumn = self.modelNotificationList.columnIndexByFieldName('client_lastName')
        if mode == UserNotificationsMode.Standard:
            self.tabWidget.setTabText(tabIndex, u'Уведомления')
            self.tblNotificationList.setColumnHidden(clientNameColumn, True)
        else:
            self.tabWidget.setTabText(tabIndex, u'Уведомления (' + unicode(rowCount) + u')')
            self.tblNotificationList.setColumnHidden(clientNameColumn, False)
        self.tabWidget.setTabIcon(tabIndex, priorityIcon(maxPriority))
        self.tabWidget.setTabTextColor(tabIndex, priorityTextColor(maxPriority))
    
    @pyqtSignature('QWidget*')
    def on_tabWidget_tabShown(self, widget):
        if widget == self:
            self.startTimer()
    
    @pyqtSignature('QWidget*')
    def on_tabWidget_tabHidden(self, widget):
        if widget == self:
            self.stopTimer()
    
    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        widget = self.tabWidget.widget(index)
        wasCurrentTab = self.isCurrentTab
        self.isCurrentTab = (widget == self)
        if not wasCurrentTab and self.isCurrentTab:
            # переключили на эту вкладку
            self.updateNotificationList()
            self.stopTimer()
        elif wasCurrentTab and not self.isCurrentTab and self.tabWidget.isTabVisible(self):
            # переключили с этой вкладки на другую
            self.startTimer()
    
    def popupMenuAboutToShow(self):
        record = self.tblNotificationList.currentItem()
        eventTypeId = forceRef(record.value('eventType_id')) if record else None
        self.actOpenSYSDMTasksPage.setEnabled(bool(self.pyServices and self.sysdmEventTypeId and eventTypeId == self.sysdmEventTypeId))
    
    @pyqtSignature('')
    def on_actOpenSYSDMTasksPage_triggered(self):
        self.pyServices.openWebApp(self.userSnils)

    def startTimer(self):
        self.stopTimer()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateNotificationList)
        self.timer.start(60000)

    def stopTimer(self):
        if self.timer:
            self.timer.stop()
            self.timer = None


class CNotificationListModel(CQueryModel):
    class CPriorityCol(CTextCol):
        def __init__(self, title, fields, defaultWidth):
            CTextCol.__init__(self, title, fields, defaultWidth)
        
        def decoration(self, values):
            priority = forceInt(values[0])
            return QVariant(priorityIcon(priority))
        
        def format(self, values):
            priority = forceInt(values[0])
            return QVariant(priorityName(priority))


    def __init__(self, parent):
        CQueryModel.__init__(self, parent)
        self.addColumn(CNotificationListModel.CPriorityCol(u'Приоритет', ['priority'], 20))
        self.addColumn(CDateTimeCol(u'Получено', ['createDatetime'], 6))
        self.addColumn(CTextListCol(u'ФИО пациента', ['client_lastName', 'client_firstName', 'client_patrName'], 20))

    def update(self):
        mode = QtGui.qApp.preferences.appPrefs.get('userNotificationsMode', UserNotificationsMode.Default)
        db = QtGui.qApp.db
        tableNotification = db.table('UserNotification')
        tableNotificationEvent = db.table('UserNotification_Event')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        query = tableNotification.leftJoin(tableNotificationEvent, tableNotificationEvent['userNotification_id'].eq(tableNotification['id']))
        query = query.leftJoin(tableEvent, tableEvent['id'].eq(tableNotificationEvent['event_id']))
        query = query.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        cond = [
            tableNotification['person_id'].eq(QtGui.qApp.userId),
            tableNotification['status'].eq(1)
        ]
        if mode == UserNotificationsMode.Extended:
            cond.append(u'''UserNotification.id = (SELECT un.id
                FROM UserNotification as un
                    INNER JOIN UserNotification_Event as une on une.userNotification_id = un.id
                WHERE une.event_id = Event.id
                    AND un.status = 1
                ORDER BY un.priority desc, un.createDatetime desc
                LIMIT 1)'''
            )
        cols = [
            tableNotification['priority'],
            tableNotification['text'],
            tableNotification['createDatetime'],
            tableEvent['eventType_id'],
            tableClient['lastName'].alias('client_lastName'),
            tableClient['firstName'].alias('client_firstName'),
            tableClient['patrName'].alias('client_patrName')
        ]
        limit = 1 if mode == UserNotificationsMode.Standard else None
        records = db.getRecordList(query, cols=cols, where=cond, order='UserNotification.`priority` desc, UserNotification.createDatetime desc', limit=limit)
        self.setRecords(records)
    
    def data(self, index, role):
        column = index.column()
        row = index.row()
        if role == Qt.DecorationRole and column == self.columnIndexByFieldName('priority'):
            (col, values) = self.getRecordValues(column, row)
            return col.decoration(values)
        elif role == Qt.BackgroundRole:
            return self.getBackgroundColor(row)
        return CQueryModel.data(self, index, role)
    
    def getBackgroundColor(self, row):
        record = self._records[row]
        priority = forceInt(record.value('priority'))
        return QVariant(priorityColor(priority))
    
    def maxPriority(self):
        if self._records:
            return forceInt(self._records[0].value('priority'))
        else:
            return 0

def priorityIcon(priority):
    if priority == 1:
        return QtGui.QIcon(':/new/prefix1/icons/bell_1.png')
    elif priority == 2:
        return QtGui.QIcon(':/new/prefix1/icons/bell_2.png')
    elif priority == 3:
        return QtGui.QIcon(':/new/prefix1/icons/bell_3.png')
    else:
        return QtGui.QIcon()

def priorityColor(priority):
    if priority == 1:
        return QtGui.QColor(224, 255, 224)
    elif priority == 2:
        return QtGui.QColor(255, 255, 200)
    elif priority == 3:
        return QtGui.QColor(255, 192, 192)
    else:
        return QtGui.QColor

def priorityTextColor(priority):
    if priority == 1:
        return QtGui.QColor(0, 90, 0)
    elif priority == 2:
        return QtGui.QColor(60, 60, 0)
    elif priority == 3:
        return QtGui.QColor(0, 60, 0)
    else:
        return QtGui.QColor()

def priorityName(priority):
    if priority == 1:
        return u'Низкий'
    elif priority == 2:
        return u'Средний'
    elif priority == 3:
        return u'Высокий'
    else:
        return u'Неизвестный (' + unicode(priority) + u')'