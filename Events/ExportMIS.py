# -*- coding: utf-8 -*-
from PyQt4 import QtGui

from library.TableModel import CActionNameCol, CFileNameCol, CDesignationCol, CDateTimeCol, CEnumCol, CTextCol, \
    CStatusREMD_FileAttachCol


def iniExportEvent(self):
    db = QtGui.qApp.db
    try:
        eventId = self.eventId
    except:
        eventId = self.itemId()
    self.modelExport.setTable('Event_Export')
    eventExportIdList = []
    actionExportIdList = []
    vimisExportIdList = []

    self.modelExport_FileAttach.addColumn(CActionNameCol(u'Наименование действия', ('master_id',), 20, ))
    self.modelExport_FileAttach.addColumn(CFileNameCol(u'Наименование документа', ('master_id',), 20, ))
    self.modelExport_FileAttach.addColumn(CDesignationCol(u'Дата подписания документа врачем', ['master_id'],
                                                          ('Action_FileAttach', 'respSigningDatetime'), 20, ))
    self.modelExport_FileAttach.addColumn(
        CDesignationCol(u'Дата подписания документа подписью организации', ['master_id'],
                        ('Action_FileAttach', 'orgSigningDatetime'), 20, ))
    self.modelExport_FileAttach.addColumn(CDateTimeCol(u'Дата и время экспорта', ['dateTime'], 15))

    stmt = u"""IF(success, 'успех', IF((SELECT status FROM Information_Messages WHERE id = (SELECT MAX(id) FROM 
    Information_Messages WHERE typeMessages = 'REMDStatus' AND IdMedDocumentMis_id = Action_FileAttach_Export.master_id 
    AND ((status = 'Success' AND IdFedRequest IS NOT NULL ) OR (status = 'Failed'))) OR id = (SELECT MAX(id) FROM 
    Information_Messages WHERE typeMessages = 'REMDStatus' AND IdMedDocumentMis_id = Action_FileAttach_Export.master_id 
    AND (status = 'Success' AND IdFedRequest IS NOT NULL AND RemdRegNumber !='')) 
    ORDER BY status DESC LIMIT 1)="Success", 'успех', 'ошибка'))"""
    self.modelExport_FileAttach.addColumn(CDesignationCol(u'отправка в Региональный РЭМД', ['id'],
                                                          ('Action_FileAttach_Export', stmt), 15))

    # self.modelExport_FileAttach.addColumn(CEnumCol(u'Состояние', ['success'], [u'ошибка', u'успех'], 15))
    self.modelExport_FileAttach.addColumn(CTextCol(u'Примечания', ['note'], 6))
    self.modelExport_FileAttach.addColumn(
        CStatusREMD_FileAttachCol(u'Информация о приеме документа федеральным РЭМД', ['master_id'], 6))
    self.modelExport_FileAttach.setTable('Action_FileAttach_Export')

    self.modelExport_VIMIS.addColumn(CTextCol(u'Тип СМС', ('DocTypeVimis',), 20, ))
    self.modelExport_VIMIS.addColumn(CTextCol(u'Профиль', ('SystemName',), 20, ))
    self.modelExport_VIMIS.addColumn(CDateTimeCol(u'Дата и время получения уведомления', ['date'], 15))
    self.modelExport_VIMIS.addColumn(
        CDesignationCol(u'отправка в Региональный РЭМД', ['id'],
                        ('Information_Messages', u'if(status="Success","успех","ошибка")'), 15))
    self.modelExport_VIMIS.addColumn(CTextCol(u'Текстовый статус', ['Message'], 6))
    self.modelExport_VIMIS.setTable('Information_Messages')

    if eventId:
        tableEvent_Export = db.table('Event_Export')
        eventExportIdList = db.getDistinctIdList(tableEvent_Export, [tableEvent_Export['id']],
                                                 [tableEvent_Export['master_id'].eq(eventId)])

        tableVIMIS_Export = db.table('Information_Messages')
        vimisExportIdList = db.getDistinctIdList(tableVIMIS_Export, [tableVIMIS_Export['id']],
                                                 [tableVIMIS_Export['IdCaseMis'].eq(eventId),
                                                  tableVIMIS_Export['typeMessages'].eq('VimisResult')])

        tableAction = db.table('Action')
        tableActionFileAttach = db.table('Action_FileAttach')
        tableActionExport = db.table('Action_FileAttach_Export')
        actionsId = db.getDistinctIdList(tableAction, [tableAction['id']],
                                         [tableAction['event_id'].eq(eventId), tableAction['deleted'].eq(0)])
        actionExportId = db.getDistinctIdList(tableActionFileAttach, [tableActionFileAttach['id']],
                                              [tableActionFileAttach['master_id'].inlist(actionsId),
                                               tableActionFileAttach['deleted'].eq(0)])
        order = [tableActionExport['dateTime'].name()]
        actionExportIdList = db.getDistinctIdList(tableActionExport, [tableActionExport['id']],
                                                  [tableActionExport['master_id'].inlist(actionExportId)], order)

    self.modelExport.setIdList(eventExportIdList)
    self.modelExport_FileAttach.setIdList(actionExportIdList)
    self.modelExport_VIMIS.setIdList(vimisExportIdList)