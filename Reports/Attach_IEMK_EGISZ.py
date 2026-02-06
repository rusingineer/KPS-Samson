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
from PyQt4 import QtGui
from PyQt4.QtCore import *

from Orgs.Utils import getOrgStructureDescendants, getOrgStructureName
from Reports.Report import *
from Reports.ReportBase import *

from library.Utils import *
from Reports.ReportSetupDialog import CReportSetupDialog


class CAttach_IEMK_EGISZ(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет о выгрузке РЭМД в ЕГИСЗ')
        self.stattmp1 = ''

    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setEventTypeVisible(False)
        result.setOnlyPermanentAttachVisible(False)
        result.setOrgStructureVisible(True)
        result.chkActionClass.setText(u'Группировать по подразделениям')
        result.setActionTypeVisible(True)
        result.setPersonVisible(True)
        result.setClientIdVisible(True)
        result.setSetPersonVisible(True)
        result.lblClientId.setText(u'Код карточки')
        result.lblOrgStructure.setText(u'Подразделение (по исполнителю)')
        result.lblPerson.setText(u'Врач (исполнитель)')
        result.lblEventStatus.setText(u'Детализировать по')
        result.setEventStatusVisible(True)

        querytmp = self.selectDatatmp()
        result.cmbEventStatus.removeItem(2)
        result.cmbEventStatus.removeItem(1)
        result.cmbEventStatus.removeItem(0)
        idxDoc = 0
        self.listDoc = []
        while querytmp.next():
            record = querytmp.record()
            note = forceString(record.value('note'))
            value = forceString(record.value('value'))
            system = forceString(record.value('system'))
            code = forceString(record.value('code'))
            self.listDoc.append([note, value, system, code])
            if note:
                result.cmbEventStatus.addItem(u'')
                result.cmbEventStatus.setItemText(idxDoc, note)
            idxDoc += 1
        if idxDoc == 0:
            result.cmbEventStatus.setItemText(0, u'Все')
        else:
            result.cmbEventStatus.addItem(u'')
            result.cmbEventStatus.setItemText(idxDoc, u'Все')

        result.lblActionTypeClass.setVisible(False)
        result.chkDetailPerson.setVisible(False)
        result.lblActionType.setVisible(False)
        result.cmbActionTypeClass.setVisible(False)
        result.cmbActionType.setVisible(False)
        result.setTitle(self.title())
        for i in xrange(result.gridLayout.count()):
            spacer = result.gridLayout.itemAt(i)
            if isinstance(spacer, QtGui.QSpacerItem):
                itemposition = result.gridLayout.getItemPosition(i)
                if itemposition != (43, 0, 1, 10):
                    result.gridLayout.removeItem(spacer)
        result.resize(400, 10)
        return result

    def selectDatatmp(self):
        db = QtGui.qApp.db
        stmt = u'''SELECT note, value, system_id as system, code FROM ActionType_Identification 
  LEFT JOIN rbAccountingSystem `as` ON ActionType_Identification.system_id = `as`.id
  WHERE `as`.code IN ('n3.medDocumentType.Pdf','n3.medDocumentType.Cda')
  AND note != '' AND note IS not NULL and deleted = 0 group by note ORDER BY note'''
        return db.query(stmt)

    def selectData(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        orgStructureId = params.get('orgStructureId', None)
        event_id = params.get('clientId', None)
        details = params.get('eventStatus', None)
        personId = params.get('personId', None)
        setPersonId = params.get('setPersonId', None)
        db = QtGui.qApp.db
        if event_id:
            condpersonId = ''
            orgStructureList = u''
            detail = u''
            details_event = u' and e.id in (%s)' % event_id
            dates = ''
            condSetPersonId = ''
        else:
            details_event = ''
            dates = 'e.execDate BETWEEN DATE(%s) AND DATE(%s) AND' % (db.formatDate(begDate), db.formatDate(endDate))
            if orgStructureId:
                orgStructureIdList = getOrgStructureDescendants(orgStructureId)
                orgStructureList = u' and p.orgStructure_id in (%s)' % (','.join(map(str, orgStructureIdList)))
            else:
                orgStructureList = u''
            if details != len(self.listDoc):
                detail = u' AND EXISTS (SELECT * FROM ActionType_Identification ati WHERE ati.system_id IN (%s) AND ati.master_id = at.id and ati.value = (%s)) ' % (self.listDoc[details][2], self.listDoc[details][1])
                if u'.cda' in self.listDoc[details][3].lower():
                    detail += u' AND  Action_FileAttach.path LIKE "%%.xml" '
                else:
                    detail += u' AND  Action_FileAttach.path LIKE "%%.pdf" '
            else:
                detail = u' AND EXISTS (SELECT * FROM ActionType_Identification ati WHERE ati.system_id IN (SELECT id FROM rbAccountingSystem `as` WHERE code IN ("n3.medDocumentType.Observation","n3.medDocumentType.Cda")) AND ati.master_id = at.id ) '
            if personId:
                condpersonId = ' and p.id = %d' % personId
            else:
                condpersonId = ''
            if setPersonId:
                condSetPersonId = ' and a.setPerson_id = %d' % setPersonId
            else:
                condSetPersonId = ''
        if not endDate or endDate.isNull():
            return None

        stmt = u'''  
SELECT e.client_id,formatClientName(e.client_id) AS fio,e.id AS event_id,at.name,a.endDate AS endDate,
    MAX(ee.dateTime) AS dateTime,
  IFNULL(im1.Message,im.Message) AS Message,IFNULL(im1.status,im.status) AS status,
  at.class,serviceType, IFNULL(im1.id,im1.id) AS messages_id, 
    Action_FileAttach.createDatetime, IFNULL(im1.RemdRegNumber,im1.RemdRegNumber) AS RemdRegNumber, a.id as  fileId, formatPersonName(p.id) as persName, os.name AS osName
FROM Action a
INNER JOIN Event   e          ON e.id = a.event_id
INNER JOIN ActionType   at     ON at.id = a.actionType_id
LEFT JOIN Action_FileAttach ON Action_FileAttach.master_id = a.id 
                             AND Action_FileAttach.deleted = 0
                             AND (Action_FileAttach.path LIKE '%%.pdf' OR Action_FileAttach.path LIKE '%%.xml')
  LEFT JOIN Event_Export ee ON ee.master_id=e.id AND ee.success=1
  Left join Person p on p.id = a.person_id
  
  left JOIN Information_Messages im ON Action_FileAttach.id = im.IdMedDocumentMis AND im.id = (SELECT MAX(id) FROM Information_Messages 
  WHERE Information_Messages.IdMedDocumentMis_id=Action_FileAttach.id anD ((status = 'Success' AND IdFedRequest IS NOT NULL ) OR (status = 'Failed')) )

  left JOIN Information_Messages im1 ON Action_FileAttach.id = im1.IdMedDocumentMis AND im1.id = (SELECT MAX(id) FROM Information_Messages 
  WHERE Information_Messages.IdMedDocumentMis_id=Action_FileAttach.id AND (status = 'Success' AND IdFedRequest IS NOT NULL  AND RemdRegNumber !='') )
  LEFT JOIN ActionType_Identification ati ON at.id = ati.master_id AND ati.deleted=0 AND ati.system_id IN (SELECT id FROM rbAccountingSystem WHERE rbAccountingSystem.code IN ('n3.medDocumentType.Pdf','n3.medDocumentType.Cda'))
LEFT JOIN rbAccountingSystem `as` ON ati.system_id = `as`.id

LEFT JOIN Action_FileAttach_Export afae ON Action_FileAttach.id = afae.master_id 
LEFT JOIN OrgStructure os ON p.orgStructure_id = os.id
  WHERE %(dates)s Action_FileAttach.respSignatureBytes IS NOT NULL -- AND Action_FileAttach.orgSignatureBytes IS NOT NULL 
AND Action_FileAttach.deleted=0
AND ((ati.id IS NOT NULL AND IF(SUBSTRING(Action_FileAttach.path,-3)='pdf', `as`.code = 'n3.medDocumentType.Pdf', `as`.code = 'n3.medDocumentType.Cda')) )
  %(detail)s
AND afae.id IS NOT NULL
%(condpersonId)s  %(orgStructureList)s  %(details_event)s %(condSetPersonId)s
-- AND afae.success=1
 GROUP BY os.name,Action_FileAttach.id, messages_id
ORDER BY os.name,ee.dateTime;
           ''' % {'dates': dates,
                  'condpersonId': condpersonId,
                  'orgStructureList': orgStructureList,
                  'detail': detail,
                  'details_event': details_event,
                  'condSetPersonId': condSetPersonId,
                  }
        db = QtGui.qApp.db
        return db.query(stmt)

    def getDescription(self, params):
        db = QtGui.qApp.db
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        chkActionTypeClass = params.get('chkActionTypeClass', False)
        personId = params.get('personId', None)
        setPersonId = params.get('setPersonId', None)
        orgStructureId = params.get('orgStructureId', None)
        details = params.get('eventStatus', None)
        event_id = params.get('clientId', None)
        chkActionClass = params.get('chkActionTypeClass', False)
        rows = []
        if event_id:
            rows.append(u'по событию: %s ' % event_id)
        else:
            rows.append(dateRangeAsStr(u'за период', begDate, endDate))
            if orgStructureId:
                rows.append(u'по отделению: %s ' % (getOrgStructureName(orgStructureId)))
            if personId:
                rows.append(u'по врачу: %s ' % forceString(db.translate('vrbPerson', 'id', personId, 'name')))
            if setPersonId:
                rows.append(u'по назаначившему врачу: %s ' % forceString(db.translate('vrbPerson', 'id', setPersonId, 'name')))

            if details != len(self.listDoc):
                rows.append(self.listDoc[details][0])

            if chkActionTypeClass:
                rows.append(u'детализировать по отделениям %s ' % forceString(
                    db.translate('vrbPerson', 'id', personId, 'name')))

        rows.append(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        return rows

    def build(self, params):
        chkGroup = params.get('chkActionTypeClass', False)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(u'Успешно принятые документы на федеральном уровне')
        cursor.insertBlock()
        cursor.insertBlock()

        tableColumns = [
            ('5%', [u'№'], CReportBase.AlignRight),
            ('5%', [u'Код пациента'], CReportBase.AlignRight),
            ('10%', [u'ФИО пациента'], CReportBase.AlignRight),
            ('5%', [u'Код карточки'], CReportBase.AlignRight),
            ('10%', [u'ФИО врача'], CReportBase.AlignRight),
            ('35%', [u'Наименование услуги'], CReportBase.AlignRight),
            ('10%', [u'Дата окончания услуги'], CReportBase.AlignRight),
            ('10%', [u'Дата экспорта'], CReportBase.AlignRight),
            ('10%', [u'Идентификатор документа в РЭМД'], CReportBase.AlignRight),
        ]

        table = createTable(cursor, tableColumns)

        query = self.selectData(params)

        table_Success = []
        id_Success = []
        table_Failed = []
        table_not_Message = []
        tempIndex = 0
        temp_osName = ''
        while query.next():
            record = query.record()
            client = forceInt(record.value('client_id'))
            fio = forceString(record.value('fio'))
            event_id = forceInt(record.value('event_id'))
            name = forceString(record.value('name'))
            fileId = forceInt(record.value('fileId'))
            endDate = forceDate(record.value('endDate')).toString("dd.MM.yyyy")
            dateTime = forceDate(record.value('dateTime')).toString("dd.MM.yyyy")
            message = forceString(record.value('Message'))
            status = forceString(record.value('status'))
            persName = forceString(record.value('persName'))
            remdRegNumber = forceString(record.value('RemdRegNumber'))
            osName = forceString(record.value('osName'))
            createDatetime = forceString(record.value('createDatetime'))
            serviceType = forceString(record.value('serviceType'))

            if (status == u'' or message.lower() == u'документ добавлен успешно') and remdRegNumber == '':
                table_not_Message.append(record)
            elif status == 'Failed' and remdRegNumber == '':
                table_Failed.append(record)
            else:
                if u'валидация' in message.lower() or remdRegNumber != '':
                    table_Success.append(record)
                    id_Success.append(fileId)
                    tempIndex += 1

                    if chkGroup:
                        if tempIndex == 0 or osName != temp_osName:
                            tempIndex = 1
                            temp_osName = osName
                            row = table.addRow()
                            table.setText(row, 0, osName, charFormat=CReportBase.ReportSubTitle, blockFormat=CReportBase.AlignLeft)
                            table.mergeCells(row, 0, 1, 9)


                    row = table.addRow()

                    table.setText(row, 0, tempIndex)
                    table.setText(row, 1, client)
                    table.setText(row, 2, fio)
                    table.setHtml(row, 3,
                                  u"<a href='event_" + str(
                                      event_id) + u"'><span style='color: rgb(FF, FF, FF);'>" + str(
                                      event_id) + "</span></a>")
                    table.setText(row, 4, persName)
                    table.setText(row, 5, name)
                    table.setText(row, 6, endDate)
                    table.setText(row, 7, dateTime)
                    table.setText(row, 8, remdRegNumber)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(u'Документы по которым вернулись ошибки')
        cursor.insertBlock()
        cursor.insertBlock()

        tableColumns = [
            ('3%', [u'№'], CReportBase.AlignRight),
            ('5%', [u'Код пациента'], CReportBase.AlignRight),
            ('10%', [u'ФИО пациента'], CReportBase.AlignRight),
            ('5%', [u'Код карточки'], CReportBase.AlignRight),
            ('10%', [u'ФИО врача'], CReportBase.AlignRight),
            ('15%', [u'Наименование услуги'], CReportBase.AlignRight),
            ('10%', [u'Дата окончания услуги'], CReportBase.AlignRight),
            ('10%', [u'Дата экспорта'], CReportBase.AlignRight),
            ('32%', [u'Ошибка экспорта'], CReportBase.AlignRight),
        ]

        table = createTable(cursor, tableColumns)
        tempIndex = 0
        temp_osName = ''
        for record in table_Failed:

            client = forceInt(record.value('client_id'))
            fio = forceString(record.value('fio'))
            event_id = forceInt(record.value('event_id'))
            name = forceString(record.value('name'))
            fileId = forceInt(record.value('fileId'))
            endDate = forceDate(record.value('endDate')).toString("dd.MM.yyyy")
            dateTime = forceDate(record.value('dateTime')).toString("dd.MM.yyyy")
            message = forceString(record.value('Message'))
            persName = forceString(record.value('persName'))
            status = forceString(record.value('status'))
            osName = forceString(record.value('osName'))
            serviceType = forceString(record.value('serviceType'))

            if fileId not in id_Success:
                tempIndex += 1

                if chkGroup:
                    if tempIndex == 0 or osName != temp_osName:
                        tempIndex = 1
                        temp_osName = osName
                        row = table.addRow()
                        table.setText(row, 0, osName, charFormat=CReportBase.ReportSubTitle,
                                      blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(row, 0, 1, 9)

                row = table.addRow()

                table.setText(row, 0, tempIndex)
                table.setText(row, 1, client)
                table.setText(row, 2, fio)
                table.setHtml(row, 3,
                              u"<a href='event_" + str(event_id) + u"'><span style='color: rgb(FF, FF, FF);'>" + str(
                                  event_id) + "</span></a>")
                table.setText(row, 4, persName)
                table.setText(row, 5, name)
                table.setText(row, 6, endDate)
                table.setText(row, 7, dateTime)
                table.setText(row, 8, message)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(
            u'Документы отправленные в ИЭМК, но не получившие уведомление о статусе приема (отображаются выгруженные документы имеющие подписи врача и МО)')
        cursor.insertBlock()
        cursor.insertBlock()

        tableColumns = [
            ('5%', [u'№'], CReportBase.AlignRight),
            ('5%', [u'Код пациента'], CReportBase.AlignRight),
            ('10%', [u'ФИО пациента'], CReportBase.AlignRight),
            ('10%', [u'Код карточки'], CReportBase.AlignRight),
            ('10%', [u'ФИО врача'], CReportBase.AlignRight),
            ('30%', [u'Наименование услуги'], CReportBase.AlignRight),
            ('10%', [u'Дата окончания услуги'], CReportBase.AlignRight),
            ('10%', [u'Дата создания документа'], CReportBase.AlignRight),
            # ('10%', [u'Дата экспорта'], CReportBase.AlignRight),
        ]

        table = createTable(cursor, tableColumns)
        tempIndex = 0
        temp_osName = ''
        for record in table_not_Message:

            client = forceInt(record.value('client_id'))
            fio = forceString(record.value('fio'))
            event_id = forceInt(record.value('event_id'))
            name = forceString(record.value('name'))
            endDate = forceDate(record.value('endDate')).toString("dd.MM.yyyy")
            dateTime = forceDate(record.value('dateTime')).toString("dd.MM.yyyy")
            message = forceString(record.value('Message'))
            persName = forceString(record.value('persName'))
            fileId = forceInt(record.value('fileId'))
            createDatetime = forceString(record.value('createDatetime'))
            status = forceString(record.value('status'))
            osName = forceString(record.value('osName'))
            serviceType = forceString(record.value('serviceType'))

            if fileId not in id_Success:
                tempIndex += 1

                if chkGroup:
                    if tempIndex == 0 or osName != temp_osName:
                        tempIndex = 1
                        temp_osName = osName
                        row = table.addRow()
                        table.setText(row, 0, osName, charFormat=CReportBase.ReportSubTitle,
                                      blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(row, 0, 1, 9)

                row = table.addRow()

                table.setText(row, 0, tempIndex)
                table.setText(row, 1, client)
                table.setText(row, 2, fio)
                table.setHtml(row, 3,
                              u"<a href='event_" + str(event_id) + u"'><span style='color: rgb(FF, FF, FF);'>" + str(
                                  event_id) + "</span></a>")
                table.setText(row, 4, persName)
                table.setText(row, 5, name)
                table.setText(row, 6, endDate)
                table.setText(row, 7, createDatetime)

        return doc
