# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
import re
import urlparse
import requests

from PyQt4 import QtSql
from PyQt4.QtCore import *

from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat, CReportViewDialog
from library.JsonRpc.client   import CJsonRpcClent
from library.Utils            import *
from library.DockWidget       import CDockWidget
from library.DialogBase       import CConstructHelperMixin
from library.PreferencesMixin import *
from Events.Action            import *
from Registry.Utils           import *
from SMPAddEventDialog        import CSMPAddEventDialog
from types import NoneType
from datetime import datetime

from Ui_SMPDockContent   import Ui_Form


class CSMPDockWidget(CDockWidget):
    def __init__(self, parent):
        CDockWidget.__init__(self, parent)
        self.setWindowTitle(u'СМП')
        self.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.content = None
        self.contentPreferences = {}


    def loadPreferences(self, preferences):
        self.contentPreferences = getPref(preferences, 'content', {})
        CDockWidget.loadPreferences(self, preferences)
        if isinstance(self.content, CPreferencesMixin):
            self.content.loadPreferences(self.contentPreferences)


    def savePreferences(self):
        result = CDockWidget.savePreferences(self)
        self.updateContentPreferences()
        setPref(result, 'content', self.contentPreferences)
        return result


    def updateContentPreferences(self):
        if isinstance(self.content, CPreferencesMixin):
            self.contentPreferences = self.content.savePreferences()


    def showEvent(self, event):
        self.connect(QtGui.qApp, QtCore.SIGNAL('dbConnectionChanged(bool)'), self.onConnectionChanged)
        if QtGui.qApp.db and QtGui.qApp.userId and not isinstance(self.content, CSMPDockContent):
            self.onDBConnected()
        self.emit(SIGNAL('visibilityChanged(QDockWidget*, bool)'), self, True)


    def closeEvent(self, event):
        self.disconnect(QtGui.qApp, QtCore.SIGNAL('dbConnectionChanged(bool)'), self.onConnectionChanged)
        self.onDBDisconnected()
        self.emit(SIGNAL('visibilityChanged(QDockWidget*, bool)'), self, False)


    def onConnectionChanged(self, value):
        if value:
            self.onDBConnected()
        else:
            self.onDBDisconnected()


    def onDBConnected(self):
        self.setWidget(None)
        if self.content:
            self.content.setParent(None)
            self.content.deleteLater()
        self.content = CSMPDockContent(self)
        self.content.loadPreferences(self.contentPreferences)
        self.setWidget(self.content)
        self.emit(SIGNAL('contentCreated(QDockWidget*)'), self)


    def onDBDisconnected(self):
        self.setWidget(None)
        if self.content:
            self.updateContentPreferences()
            self.content.setParent(None)
            if hasattr(self.content, 'refreshTimer'):
                self.content.refreshTimer.stop()
            self.content.deleteLater()
        self.content = QtGui.QLabel(u'необходимо\nподключение\nк базе данных', self)
        self.content.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.content.setDisabled(True)
        self.setWidget(self.content)
        self.emit(SIGNAL('contentDestroyed(QDockWidget*)'), self)


class CSMPDockContent(QtGui.QWidget, Ui_Form, CConstructHelperMixin, CContainerPreferencesMixin):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.addModels('CallInfo', CCallInfoModel(self))
        self.setModels(self.tblCallInfo, self.modelCallInfo, self.selectionModelCallInfo)
        self.selectionModelCallInfo.currentRowChanged.connect(self.selectionChanged)
        self.modelCallInfo.modelReset.connect(self.selectionChanged)
        self.tblCallInfo.contextMenuEvent = self.tblCallInfoContextMenuEvent

        column = namedtuple('column', 'show, caption, sql')
        self.columns = [
            column(True,  u'Дата вызова',      u"callInfo.callDate"), 
            column(True,  u'Время звонка',     u"eventItem.eventTime"), 
            column(True,  u'Статус вызова',    u"eventType.name"), 
            column(True,  u'Фамилия',          u"callInfo.lastName"), 
            column(True,  u'Имя',              u"callInfo.name"), 
            column(True,  u'Отчество',         u"callInfo.patronymic"),
            column(True,  u'Вызов загружен ',  u"DATE_FORMAT(eventItem.createDateTime, '%d.%m.%y %H:%i')"),
            column(True,  u'Подтверждение получения', u"case when eventItem.updEvent = 0 then 'Нет подтверждения' when eventItem.updEvent = 1 and callInfo.Type <> 2 then 'Подтверждение отправлено' when eventItem.isDone = 0 and eventItem.updEvent = 1 and callInfo.Type = 2 then 'Нет подтверждения' when eventItem.isDone = 1 and eventItem.updEvent = 1 and callInfo.Type = 2 then 'Подтверждение отправлено' end"),
            column(True,  u'Сообщение',        u"eventItem.note"), 
            column(True,  u'ФИО передавшего вызов', u"eventItem.transferUser"), 
            column(True,  u'Тип вызова',       u"case callInfo.Type when 0 then 'НМП' when 1 then '03' when 2 then 'Активное посещение врача' end"),
            column(False, u'Пол',              u"callInfo.sex"), 
            column(False, u'Лет',              u"callInfo.ageYears"), 
            column(False, u'Месяцев',          u"callInfo.ageMonths"), 
            column(False, u'Дней',             u"callInfo.ageDays"), 
            column(False, u'Время приёма вызова', u"callInfo.endReceivingCall"), 
            column(False, u'Время окончания приёма вызова', u"callInfo.receptionEndingTime"), 
            column(False, u'Основной диагноз', u"callInfo.diseaseBasic"), 
            column(False, u'Результат выезда', u"callInfo.resultDeparture"), 
            column(False, u'Категория срочности вызова', u"callInfo.urgencyCategory"), 
            column(False, u'Вид вызова',       u"callInfo.callKind"), 
            column(False, u'Повод к вызову',   u"callInfo.callOccasion"), 
            column(False, u'Вызов повторный?', u"case callInfo.isRepeated when 0 then 'нет' when 1 then 'да' end"), 
            column(False, u'ФИО вызывающего',  u"callInfo.callerName"), 
            column(False, u'Место вызова',     u"callInfo.callPlace"), 
            column(False, u'ФИО принявшего вызов', u"callInfo.userReceiver"), 
            column(False, u'Населенный пункт', u"callInfo.settlement"), 
            column(False, u'Улица',            u"callInfo.street"), 
            column(False, u'Номер дома',       u"concat(cast(callInfo.house as char), case when char_length(callInfo.houseFract) > 0 then concat('/', callInfo.houseFract) else '' end)"), 
            column(False, u'Корпус',           u"callInfo.building"), 
            column(False, u'Квартира',         u"callInfo.flat"), 
            column(False, u'Подъезд',          u"callInfo.porch"), 
            column(False, u'Код домофона',     u"callInfo.porchCode"), 
            column(False, u'Этаж',             u"callInfo.floor"), 
            column(False, u'Ориентиры',        u"callInfo.landmarks"), 
            column(False, u'Телефон',          u"callInfo.telephone"), 
            column(False, u'rId',              u"eventItem.rId"), 
            column(False, u'updEvent',         u"eventItem.updEvent"), 
            column(False, u'OMS_CODE',         u"callInfo.OMS_CODE"), 
            column(False, u'idCallNumber',     u"callInfo.idCallNumber"),
            column(False, u'Номер вызова',     u"callInfo.idCallNumber"),
            column(False, u'Type',             u"callInfo.Type"),
            column(False, u'Информация',       u"callInfo.active_visit_item_info"),
            column(False, u'eventitem_id',     u"eventItem.id"),
            column(False, u'idCallEventType',  u"idCallEventType"),
        ]
        
        self.addComboBoxItems(self.cmbEventType, u"select id, Name from smp_sprcalleventtype")
        self.addComboBoxItems(self.cmbOrganisation, u"""select bookkeeperCode,
                                                            concat(bookkeeperCode, ' - ', name) as name
                                                        from OrgStructure
                                                        where length(bookkeeperCode) > 0
                                                        order by bookkeeperCode, name""")

        self.updateCallList()
        
        for index, column in enumerate(self.columns):
            self.tblCallInfo.setColumnHidden(index, not column.show)
        self.refreshTimer = QTimer()
        self.refreshTimer.timeout.connect(self.getNewEvents)
        self.refreshTimer.start(1000 * 60)
        self.getNewEvents()
        
        self.addEventDialog = CSMPAddEventDialog(self)
        self.addComboBoxItems(self.addEventDialog.cmbEventType, u"select id, Name from smp_sprcalleventtype where eventAccess = 1 and isDeleted = 0")

        self.addEventDialogDoctorCome = CSMPAddEventDialog(self)
        self.addComboBoxItems(self.addEventDialogDoctorCome.cmbEventType, u"select id, Name from smp_sprcalleventtype WHERE id = 66 OR id = 77")


    def tblCallInfoContextMenuEvent(self, event):
        self.menu = QtGui.QMenu(self)
        findClient = QtGui.QAction(u'Найти в картотеке', self)
        self.menu.addAction(findClient)
        findClient.triggered.connect(self.findClient)
        printSMPList = QtGui.QAction(u'Печать списка вызовов', self)
        self.menu.addAction(printSMPList)
        printSMPList.triggered.connect(self.printSMPList)
        self.menu.popup(QtGui.QCursor.pos())


    def findClient(self):
        currentRow = self.tblCallInfo.currentRow()
        app = QtGui.qApp
        mainWindow = app.mainWindow
        if mainWindow.registry:
            if not isinstance(currentRow, NoneType):
                data = self.modelCallInfo.record(currentRow)
                lastName = forceString(data.value(u'Фамилия'))
                firstName = forceString(data.value(u'Имя'))
                patrName = forceString(data.value(u'Отчество'))
                mainWindow.registry.chkFilterLastName.setChecked(True)
                mainWindow.registry.chkFilterFirstName.setChecked(True)
                mainWindow.registry.chkFilterPatrName.setChecked(True)
                mainWindow.registry.edtFilterLastName.setText(lastName)
                mainWindow.registry.edtFilterFirstName.setText(firstName)
                mainWindow.registry.edtFilterPatrName.setText(patrName)
                mainWindow.registry.on_buttonBoxClient_apply()
        else:
            QtGui.QMessageBox.warning(self, u'Внимание!',
                                      u'Для поиска необходимо открыть окно картотеки!',
                                      QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)

    def printSMPList(self):
        report = CSMPListReport(self, self.modelCallInfo)
        doc = report.build()
        view = CReportViewDialog(self)
        view.setWindowTitle(report.title())
        view.setText(doc)
        if report.pageFormat:
            view.setPageFormat(report.pageFormat)
        view.exec_()


    def addComboBoxItems(self, comboBox, sql):
        query = QtGui.qApp.db.query(sql)
        while query.next():
            id   = query.value(0)
            name = query.value(1).toString()
            comboBox.addItem(name, id)


    def updateCallList(self):
        
        sql = u"""
            select %s
            from smp_callinfo as callInfo
                left join smp_eventitem as eventItem on eventItem.idCallNumber = callInfo.idCallNumber
                    AND eventItem.id =
                    (
                        SELECT MAX(ss.id)
                        FROM smp_eventitem ss
                        WHERE
                                ss.idCallNumber = eventItem.idCallNumber
                            AND (CASE WHEN ss.rId <> 0 THEN 1 ELSE 0 END) = (CASE WHEN eventItem.rId <> 0 THEN 1 ELSE 0 END)
                    )
                left join smp_sprcalleventtype as eventType on eventType.id = eventItem.idCallEventType
        """ % ', '.join(u"%s as `%s`" % (column.sql, column.caption) for column in self.columns)

        where = []
        
        where.append(u"callInfo.callDate = '%s'" % str(self.calDate.selectedDate().toString('yyyy-MM-dd')))

        where.append(u"callInfo.OMS_CODE = '%s'" % str(self.cmbOrganisation.itemData(self.cmbOrganisation.currentIndex()).toString()))
        
        typeList = []
        if self.chbNMP.isChecked():
            typeList.append(0)
        if self.chb03.isChecked():
            typeList.append(1)
        if self.chbDoctorCome.isChecked():
            typeList.append(2)
        if typeList:
            where.append(u"callInfo.Type in (%s)" % ','.join(str(type) for type in typeList))
            
        if self.chbEventType.isChecked() and self.cmbEventType.currentIndex != 0:
            eventTypeId = self.cmbEventType.itemData(self.cmbEventType.currentIndex()).toInt()[0]
            where.append(u"eventItem.idCallEventType = %d" % eventTypeId)
            
        where = ' and '.join(where)
        if where:
            sql += " where " + where
            
        self.modelCallInfo.setQuery(sql)
        self.tblCallInfo.show()
        self.tblCallInfo.resizeColumnsToContents()


    def updateCalendarDates(self):
        self.calDate.setDateTextFormat(QDate(), QtGui.QTextCharFormat())
        db = QtGui.qApp.db
        
        sql = u"""select distinct callInfo.callDate 
            from smp_callinfo as callInfo
            left join smp_eventitem as eventItem on eventItem.idCallNumber = callInfo.idCallNumber
        """
        
        where = []
        
        where.append(u"callInfo.callDate is not null")
        
        where.append(u"callInfo.OMS_CODE = '%s'" % str(self.cmbOrganisation.itemData(self.cmbOrganisation.currentIndex()).toString()))
        
        typeList = []
        if self.chbNMP.isChecked():
            typeList.append(0)
        if self.chb03.isChecked():
            typeList.append(1)
        if self.chbDoctorCome.isChecked():
            typeList.append(2)
        if typeList:
            where.append(u"callInfo.Type in (%s)" % ','.join(str(type) for type in typeList))
            
        if self.chbEventType.isChecked() and self.cmbEventType.currentIndex != 0:
            eventTypeId = self.cmbEventType.itemData(self.cmbEventType.currentIndex()).toInt()[0]
            where.append(u"eventItem.idCallEventType = %d" % eventTypeId)
            
        where = ' and '.join(where)
        if where:
            sql += " where " + where
        
        query = db.query(sql)
        bold = QtGui.QTextCharFormat()
        bold.setFontWeight(QtGui.QFont.Bold)
        while query.next():
            date = query.value(0).toDate()
            self.calDate.setDateTextFormat(date, bold)


    def canUpdEvent(self, record):
        rId = record.value(u'rId')
        if not rId or rId.isNull():
            return False
        type = record.value(u'Type')
        if not type or type.isNull() or type.toInt()[0] != 0:
            return False
        updEvent = record.value(u'updEvent')
        if not updEvent or updEvent.isNull() or updEvent.toInt()[0] != 0:
            return False
        return True


    def canAddEvent(self, record):
        type = record.value(u'Type')
        #if not type or type.isNull() or type.toInt()[0] != 0:
        if not type or type.isNull() or type.toInt()[0] not in [0, 2]:
            return False
        updEvent = record.value(u'updEvent')
        if not updEvent or updEvent.isNull() or updEvent.toInt()[0] == 0:
            return False
        idCallEventType = record.value(u'idCallEventType')
        if idCallEventType and not idCallEventType.isNull() and type.toInt()[0] in [0, 2] and idCallEventType.toInt()[0] != 1:
            return False
        return True


    def selectionChanged(self, current = QModelIndex(), previous = QModelIndex()):
        self.btnAddEvent.setText(u'Результат вызова')

        if not current.isValid():
            self.txtCallInfo.clear()
            self.btnUpdEvent.setEnabled(False)
            self.btnAddEvent.setEnabled(False)
            self.btnPrintCallInfo.setEnabled(False)
            return

        record = self.modelCallInfo.record(current.row())
        
        self.btnUpdEvent.setEnabled(self.canUpdEvent(record))
        self.btnAddEvent.setEnabled(self.canAddEvent(record))
        self.btnPrintCallInfo.setEnabled(True)

        def formatField(name):
            value = record.value(name)
            if value.isNull() or len(forceString(value).strip()) == 0:
                return u''
            else:
                return u'<div><b>%s:</b> %s</div>' % (name, forceString(value))

        def formatField_for_information(name):
            value = record.value(name)
            if value.isNull() or len(forceString(value).strip()) == 0:
                return u''
            else:
                text = forceString(value)
                text = text.replace("\n", "<br>")
                return u'<div>%s</div>' % (text)

        text = u'''<style> 
            .header {
                font: bold large; 
                margin-bottom: 5px; 
                margin-left: 20px;
            }
            </style>'''
        
        text += u'<div class="header">Пациент</div>'
        text += formatField(u'Фамилия')
        text += formatField(u'Имя')
        text += formatField(u'Отчество')
        text += formatField(u'Пол')
        age = []
        ageParts = [
            (u'Лет', (u'год', u'года', u'лет')), 
            (u'Месяцев', (u'месяц', u'месяца', u'месяцев')), 
            (u'Дней', (u'день', u'дня', u'дней'))
        ]
        for partName, words in ageParts:
            part = record.value(partName)
            if not part.isNull():
                part = forceInt(part)
                age.append(u'%d %s' % (part, agreeNumberAndWord(part, words)))
        if age:
            text += u'<div><b>Возраст:</b> %s</div>' % ', '.join(age)
        text += u'<hr>'

        text += u'<div class="header">Вызов</div>'
        text += formatField(u'Номер вызова')
        text += formatField(u'Дата вызова')
        text += formatField(u'Время приёма вызова')
        text += formatField(u'Время окончания приёма вызова')
        text += formatField(u'Основной диагноз')
        text += formatField(u'Результат выезда')
        text += formatField(u'Категория срочности вызова')
        text += formatField(u'Вид вызова')
        text += formatField(u'Повод к вызову')
        text += formatField(u'Вызов повторный?')
        text += formatField(u'ФИО вызывающего')
        text += formatField(u'Место вызова')
        text += formatField(u'ФИО принявшего вызов')
        text += u'<hr>'
        
        text += u'<div class="header">Адрес и контактные данные</div>'
        text += formatField(u'Населенный пункт')
        text += formatField(u'Улица')
        text += formatField(u'Номер дома')
        text += formatField(u'Корпус')
        text += formatField(u'Квартира')
        text += formatField(u'Подъезд')
        text += formatField(u'Код домофона')
        text += formatField(u'Этаж')
        text += formatField(u'Ориентиры')
        text += formatField(u'Телефон')

        type_rec = record.value(u'Type')
        if type_rec and not type_rec.isNull() and type_rec.toInt()[0] == 2:
            text += u'<hr>'
            text += u'<div class="header">Сводная информация по вызову</div>'
            text += formatField_for_information(u'Информация')
            self.btnAddEvent.setText(u'Статус вызова')

        text += u'<hr>'
        
        self.txtCallInfo.setText(text)


    def getNewEvents(self):
        if (QtGui.qApp.isBusyReconnect == 1):
            return

        isNotification = False

        # Сначала вызовы СМП Активное посещение врача
        sql = u"""  select MAX(callInfo.callDate)
                    from smp_callinfo as callInfo
                    inner join smp_eventitem as eventItem on eventItem.idCallNumber = callInfo.idCallNumber
                    WHERE 
                            callInfo.Type = 2 
                        AND eventItem.rId = 0 
                        AND 
                        (
                            eventItem.idCallEventType IS NULL
                            OR 
                            eventItem.idCallEventType = 1
                        )
                    and callInfo.OMS_CODE = '%s'""" % str(self.cmbOrganisation.itemData(self.cmbOrganisation.currentIndex()).toString())
        if QtGui.qApp.db:
            query = QtGui.qApp.db.query(sql)
            if query.first() and not query.value(0).toDate().isNull():
                date = query.value(0).toDate()
                self.lblNewEventsAct.setText(u'Новые вызовы СМП (Активн.) (дата: <a href="setdate:%s">%s</a>)' % (date.toString(Qt.ISODate), forceString(date)))
                isNotification = True
            else:
                self.lblNewEventsAct.setText(u"")

        # Затем вызовы СМП, которые НМП
        sql = u"""select MAX(callInfo.callDate)
                  from smp_callinfo as callInfo
                  inner join smp_eventitem as eventItem on eventItem.idCallNumber = callInfo.idCallNumber
                  where eventItem.updEvent = 0 and callInfo.Type = 0
                    AND eventItem.id = (SELECT MAX(ei.id) FROM smp_eventitem ei WHERE ei.idCallNumber = callInfo.idCallNumber AND ei.rId > 0)
                    and callInfo.OMS_CODE = '%s'""" % str(self.cmbOrganisation.itemData(self.cmbOrganisation.currentIndex()).toString())
        if QtGui.qApp.db:
            query = QtGui.qApp.db.query(sql)
            if query.first() and not query.value(0).toDate().isNull():
                date = query.value(0).toDate()
                self.lblNewEvents.setText(u'Новые вызовы СМП (дата: <a href="setdate:%s">%s</a>)' % (date.toString(Qt.ISODate), forceString(date)))
                isNotification = True
            else:
                self.lblNewEvents.setText(u"")

        self.setTabNotification(isNotification)


    def setTabNotification(self, hasNewEvents):
        tabBar, tabIndex = QtGui.qApp.mainWindow.findDockTab(self.parent())
        if tabBar:
            if hasNewEvents:
                tabBar.setTabTextColor(tabIndex, Qt.red)
                tabBar.setTabIcon(tabIndex, self.style().standardIcon(QtGui.QStyle.SP_MessageBoxWarning))
            else:
                tabBar.setTabTextColor(tabIndex, Qt.black)
                tabBar.setTabIcon(tabIndex, QtGui.QIcon())


    def getMyFIO(self):
        db = QtGui.qApp.db
        query = db.query("select CONCAT_WS(' ', p.lastName, p.firstName, p.patrName) AS fio from Person p where p.id = {0} LIMIT 1;".format(QtGui.qApp.userInfo._userId))
        if query.next():
            return forceString(query.value(0))
        return str()


    @QtCore.pyqtSignature('bool')
    def on_chbEventType_toggled(self, checked):
        self.cmbEventType.setEnabled(checked)
        self.updateCalendarDates()
        self.updateCallList()


    @QtCore.pyqtSignature('bool')
    def on_chb03_toggled(self, checked):
        self.updateCalendarDates()
        self.updateCallList()


    @QtCore.pyqtSignature('bool')
    def on_chbNMP_toggled(self, checked):
        self.updateCalendarDates()
        self.updateCallList()


    @QtCore.pyqtSignature('bool')
    def on_chbDoctorCome_toggled(self, checked):
        self.updateCalendarDates()
        self.updateCallList()


    @QtCore.pyqtSignature('')
    def on_calDate_selectionChanged(self):
        self.updateCallList()


    @QtCore.pyqtSignature('int')
    def on_cmbEventType_currentIndexChanged(self, index):
        self.updateCalendarDates()
        self.updateCallList()


    @QtCore.pyqtSignature('int')
    def on_cmbOrganisation_currentIndexChanged(self, index):
        self.updateCalendarDates()
        self.updateCallList()


    @QtCore.pyqtSignature('')
    def on_btnUpdEvent_clicked(self):
        record = self.modelCallInfo.record(self.selectionModelCallInfo.currentIndex().row())
        if not self.canUpdEvent(record):
            return

        rId = record.value(u'rId').toInt()[0]

        urlService = forceString(QtGui.qApp.db.translate('GlobalPreferences', 'code', 'PHP_ServicesUrl', 'value'))
        if not urlService:
            urlService = QtGui.qApp.preferences.dbServerName
        clent = CJsonRpcClent("http://%s/smp/handler.php" % urlService)
        try:
            result = clent.call('updEvent', {'id': rId, 'operFIO': self.getMyFIO()[:25]})
            if result:
                QtGui.QMessageBox.information(self, u'Информация', u'Подтверждение отправлено', QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                self.updateCalendarDates()
                self.updateCallList()
                self.getNewEvents()
            else:
                QtGui.QMessageBox.critical(self, u'Ошибка', u'Подтверждение не отправлено', QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
        except Exception as e:
            QtGui.QMessageBox.critical(self, u'Ошибка', unicode(e), QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)


    @QtCore.pyqtSignature('')
    def on_btnRefresh_clicked(self):
        self.updateCalendarDates()
        self.updateCallList()


    @QtCore.pyqtSignature('')
    def on_btnAddEvent_clicked(self):
        record = self.modelCallInfo.record(self.selectionModelCallInfo.currentIndex().row())
        if not self.canAddEvent(record):
            return

        type_rec = record.value(u'Type').toInt()[0]
        if type_rec == 0:
            if self.addEventDialog.exec_() == QtGui.QDialog.Accepted:
                eventTypeId = self.addEventDialog.eventTypeId()
                note = self.addEventDialog.note()
                lpuCode = forceString(record.value(u'OMS_CODE'))
                idCallNumber = record.value(u'idCallNumber').toLongLong()[0]
                operFIO = QtGui.qApp.userInfo.name()
                urlService = forceString(QtGui.qApp.db.translate('GlobalPreferences', 'code', 'PHP_ServicesUrl', 'value'))
                if not urlService:
                    urlService = QtGui.qApp.preferences.dbServerName
                clent = CJsonRpcClent("http://%s/smp/handler.php" % urlService)
                try:
                    result = clent.call('addEvent', {'lpuCode': lpuCode, 'idCallNumber': idCallNumber, 'note': note, 'idCallEventType': eventTypeId, 'operFIO': operFIO})
                    if result == -1:
                        QtGui.QMessageBox.critical(self, u'Ошибка', u'Результат вызова не отправлен (-1)', QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                    else:
                        QtGui.QMessageBox.information(self, u'Информация', u'Данные отправлены успешно', QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                        self.updateCallList()
                        self.updateCalendarDates()
                        self.getNewEvents()
                except Exception as e:
                    QtGui.QMessageBox.critical(self, u'Ошибка', unicode(e), QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
        elif type_rec == 2:
            if self.addEventDialogDoctorCome.exec_() == QtGui.QDialog.Accepted:
                result_id = self.addEventDialogDoctorCome.eventTypeId()
                if result_id == 66:
                    result_id = 0
                elif result_id == 77:
                    result_id = 1
                description = self.addEventDialogDoctorCome.note()
                eventitem_id = record.value(u'eventitem_id').toInt()[0]
                person_id = QtGui.qApp.userId

                servicesURL = forceString(QtGui.qApp._globalPreferences.get('23:servicesURL'))
                if servicesURL:
                    servicesURL = servicesURL.replace('${dbServerName}', QtGui.qApp.preferences.dbServerName)
                    servicesURL = urlparse.urljoin(servicesURL, '/api/local/services/smp')
                    try:
                        params_str = "eventitem_id=%s&person_id=%s&result_id=%s" % (str(eventitem_id), str(person_id), str(result_id))
                        if result_id == 1:
                            params_str = params_str + "&description=%s" % description
                        response = requests.get(servicesURL + '/accept_or_reject_active_visit?%s' % params_str)
                        content = json.loads(response.content.decode('utf-8'))
                        if content[u'status'] == 1:
                            QtGui.QMessageBox.information(self, u'Информация', u'Данные отправлены успешно',
                                                          QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                            self.updateCallList()
                            self.updateCalendarDates()
                            self.getNewEvents()
                        else:
                            QtGui.QMessageBox().critical(self, u'Ошибка',
                                                         u'Произошла ошибка: ' + unicode(content[u'message']),
                                                         QtGui.QMessageBox.Close)
                    except Exception as e:
                        res = QtGui.QMessageBox().warning(self,
                                                          u'Внимание!',
                                                          u"Не удалось установить соединение с сервером сервисов, проверьте доступность сервера сервисов с текущего рабочего места\n показать детали?",
                                                          QtGui.QMessageBox.Ok | QtGui.QMessageBox.Close,
                                                          QtGui.QMessageBox.Close)
                        if res == QtGui.QMessageBox.Ok:
                            QtGui.QMessageBox().critical(self, u'Ошибка', u'Произошла ошибка: ' + unicode(e),
                                                         QtGui.QMessageBox.Close)
                else:
                    QtGui.QMessageBox().critical(self, u'Ошибка', u'Не указан адрес сервера сервисов в глобальных настройках МИС', QtGui.QMessageBox.Close)


    @QtCore.pyqtSignature('QString')
    def on_lblNewEvents_linkActivated(self, link):
        self.common_linkActivated(link)


    @QtCore.pyqtSignature('QString')
    def on_lblNewEventsAct_linkActivated(self, link):
        self.common_linkActivated(link)


    def common_linkActivated(self, link):
        link = str(link)
        if link[:8] == u"setdate:":
            date = QDate.fromString(link[8:], Qt.ISODate)
            self.calDate.setSelectedDate(date)


    @QtCore.pyqtSignature('')
    def on_btnPrintCallInfo_clicked(self):
        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        dialog = QtGui.QPrintDialog(printer, self)
        if dialog.exec_():
            self.txtCallInfo.print_(printer)


class CCallInfoModel(QtSql.QSqlQueryModel):
    def __init__(self, parent):
        QtSql.QSqlQueryModel.__init__(self, parent)

class CSMPListReport(CReportBase):
    def __init__(self, parent, model):
        CReportBase.__init__(self, parent)
        self.model = model
        self.setTitle(u'Список вызовов СМП')
        self.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape, leftMargin=1,
                                      topMargin=1, rightMargin=1, bottomMargin=1)

    def formatAge(self, record):
        age = []
        ageParts = [
            (u'Лет', (u'год', u'года', u'лет')),
            (u'Месяцев', (u'месяц', u'месяца', u'месяцев')),
            (u'Дней', (u'день', u'дня', u'дней'))
        ]
        for partName, words in ageParts:
            part = record.value(partName)
            if not part.isNull():
                part = forceInt(part)
                age.append(u'%d %s' % (part, agreeNumberAndWord(part, words)))
        if age:
            return ', '.join(age)

    def formatAddress(self, record):
        settlement = forceString(record.value(26))
        street = forceString(record.value(27))
        house = forceString(record.value(28))
        building = forceString(record.value(29))
        flat = forceString(record.value(30))
        porch = forceString(record.value(31))
        porchCode = forceString(record.value(32))
        floor = forceString(record.value(33))
        landmarks = forceString(record.value(34))

        addressParts = []

        if settlement:
            addressParts.append(settlement)
        if street:
            addressParts.append(u" {0}".format(street))
        if house and house != 0:
            addressParts.append(u"д. {0}".format(house))
        if building and building != 0:
            addressParts.append(u"корп. {0}".format(building))
        if flat and flat != 0:
            addressParts.append(u"кв. {0}".format(flat))
        if porch and porch != "0":
            addressParts.append(u"подъезд {0}".format(porch))
        if porchCode and porchCode != 0:
            addressParts.append(u"код домофона {0}".format(porchCode))
        if floor and floor != "0":
            addressParts.append(u"этаж {0}".format(floor))
        if landmarks:
            addressParts.append(u"ориентир: {0}".format(landmarks))

        return ", ".join(part for part in addressParts if part)

    def extractDiagnosis(self, text):
        pattern = u"<b>Основной диагноз:</b> ([^<]+)"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        else:
            return ''

    def extractComplaints(self, text):
        pattern = u"<b>Жалобы:</b> ([^<]+)"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        else:
            return ''
    def extractClientBirthDate(self, text):
        pattern = u"<b>Дата рождения:</b> ([^<]+)"
        match = re.search(pattern, text)
        if not match:
            return ''
        dateStr = match.group(1).strip()
        try:
            birthDate = datetime.strptime(dateStr, "%d.%m.%Y")
            return birthDate.strftime("%Y-%m-%d")
        except ValueError:
            return ''

    def findClientId(self, lastName, firstName, patrName, birthDate):
        db = QtGui.qApp.db
        table = db.table('Client')
        cond = [
            table['lastName'].eq(lastName),
            table['firstName'].eq(firstName),
            table['patrName'].eq(patrName),
            table['birthDate'].dateEq(birthDate),
            table['deleted'].eq(0)
        ]

        record = db.getRecordEx(table, 'id', cond)
        if record:
            return forceInt(record.value('id'))
        else:
            return ''

    def findClientAttach(self, clientId):
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableClientAttach = db.table('ClientAttach')
        tableOrgStructure = db.table('OrgStructure')
        cond = [
            tableClient['id'].eq(clientId),
            tableClient['deleted'].eq(0),
            tableClientAttach['deleted'].eq(0),

        ]

        queryTable = tableClient.innerJoin(tableClientAttach, tableClientAttach['client_id'].eq(tableClient['id']))
        queryTable = queryTable.innerJoin(tableOrgStructure, tableOrgStructure['id'].eq(tableClientAttach['orgStructure_id']))

        record = db.getRecordEx(queryTable, tableOrgStructure['name'], cond)
        if record:
            return forceString(record.value('name'))
        else:
            return ''

    def build(self):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        # cursor.insertText(description)
        cursor.insertBlock()

        tableColumns = [
            ('8%', [u'Дата вызова'], CReportBase.AlignLeft),
            ('5%', [u'Время приёма вызова'], CReportBase.AlignLeft),
            ('5%', [u'Тип вызова'], CReportBase.AlignLeft),
            ('5%', [u'Код пациента'], CReportBase.AlignLeft),
            ('15%', [u'ФИО'], CReportBase.AlignLeft),
            ('5%', [u'Пол'], CReportBase.AlignLeft),
            ('5%', [u'Возраст'], CReportBase.AlignLeft),
            ('10%', [u'Основной диагноз'], CReportBase.AlignLeft),
            ('22%', [u'Жалобы'], CReportBase.AlignLeft),
            ('10%', [u'Повод к вызову'], CReportBase.AlignLeft),
            ('15%', [u'Адрес'], CReportBase.AlignLeft),
            ('10%', [u'Участок'], CReportBase.AlignLeft),
            ('10%', [u'Телефон'], CReportBase.AlignLeft),
            ('10%', [u'ФИО передавшего вызов'], CReportBase.AlignLeft),
            ('10%', [u'Подтверждение вызова'], CReportBase.AlignLeft)
        ]
        table = createTable(cursor, tableColumns)
        rowCount = self.model.rowCount()
        for row in xrange(0, rowCount):
            tableRow = table.addRow()
            record = self.model.record(row)
            callDate = forceString(record.value(0))
            endReceivingCall = forceString(record.value(15))
            fio = formatName(forceString(record.value(3)),
                             forceString(record.value(4)),
                             forceString(record.value(5)))
            sex = forceString(record.value(11))
            age = self.formatAge(record)
            type_rec = record.value(41).toInt()[0]
            info = forceString(record.value(42))
            if forceString(record.value(17)) == '' and type_rec == 2:
                diseaseBasic = self.extractDiagnosis(info)
            else:
                diseaseBasic = forceString(record.value(17))
            complaints = self.extractComplaints(info)
            callOccasion = forceString(record.value(21))
            address = self.formatAddress(record)
            telephone = forceString(record.value(35))
            transferUser = forceString(record.value(9))
            isDone = forceString(record.value(7))
            type_name = ''
            if type_rec == 0:
                type_name = u'НМП'
            elif type_rec == 1:
                type_name = u'03'
            elif type_rec == 2:
                type_name = u'СМП (Актив.)'
            birthDate = self.extractClientBirthDate(info)
            clientId = self.findClientId(forceString(record.value(3)), forceString(record.value(4)),
                                                  forceString(record.value(5)), birthDate)
            attach = self.findClientAttach(forceString(clientId))

            table.setText(tableRow, 0, callDate)
            table.setText(tableRow, 1, endReceivingCall)
            table.setText(tableRow, 2, type_name)
            table.setText(tableRow, 3, clientId)
            table.setText(tableRow, 4, fio)
            table.setText(tableRow, 5, sex)
            table.setText(tableRow, 6, age)
            table.setText(tableRow, 7, diseaseBasic)
            table.setText(tableRow, 8, complaints)
            table.setText(tableRow, 9, callOccasion)
            table.setText(tableRow, 10, address)
            table.setText(tableRow, 11, attach)
            table.setText(tableRow, 12, telephone)
            table.setText(tableRow, 13, transferUser)
            table.setText(tableRow, 14, isDone)

        return doc