# -*- coding: utf-8 -*-

# from UOServiceClient import CUOServiceClient
# client = CUOServiceClient()
# idMq = client.getlpulist('qw')

from PyQt4 import QtGui
from PyQt4.QtCore import *

from library.Utils import *

def warninWindow(massege):
    buttons = QtGui.QMessageBox.Ok
    QtGui.QMessageBox.warning(QtGui.qApp.mainWindow,
                              u'Информация',
                              massege,
                              buttons)

def checkDirectionOrg(self, orgId, action):
    db = QtGui.qApp.db
    try:
        stmt = u'''
                SELECT o.title,o.id, oi.value FROM Organisation_Identification oi
          left JOIN rbAccountingSystem `as` ON oi.system_id = `as`.id
          left JOIN Organisation o ON oi.master_id = o.id
          WHERE o.id=%s AND `as`.code='org.n3' and oi.deleted=0''' % (orgId)
        query = db.query(stmt)
        while query.next():
            title = forceString(query.value(0))
            value = forceString(query.value(2))

        stmt = u'''SELECT ae.note FROM Action_Export ae
  left JOIN rbExternalSystem es ON ae.system_id = es.id
  WHERE ae.externalId=%s AND ae.master_id=%s AND es.code="РЕГИЗ.УО"''' % (action[u'Идентификатор направления'], forceRef(action._record.value('id')))
        query = db.query(stmt)
        while query.next():
            note = forceString(query.value(0))
        if note != value: #2921904
            if QtGui.QMessageBox.critical(self,
                                          u'Внимание! Запись невозможна!',
                                          u'Направление зарегистрировано в сервисе УО в "'+title+u'"<br>В поле "Куда направляется" сейчас указана другая организация. <br><br>Исправить целевую организацию в поле "Куда направляется"?',
                                          QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                          QtGui.QMessageBox.No) == QtGui.QMessageBox.No:
                return False
            else:
                stmt = u'''  SELECT o.title,o.id FROM Organisation_Identification oi
  left JOIN rbAccountingSystem `as` ON oi.system_id = `as`.id
  left JOIN Organisation o ON oi.master_id = o.id
  WHERE oi.value='%s' AND `as`.code='org.n3' and oi.deleted=0''' % (note)
                query = db.query(stmt)
                while query.next():
                    id = forceString(query.value(1))
                if id:
                    propertiesByName = action.getPropertiesByName()
                    propertiesByName[u'Куда направляется'].setValue(id)
                    return True
                else:
                    return False
        return True
    except:
        pass

def ConnectionInfo(orgStructureId):
    db = QtGui.qApp.db
    tableOrg = db.table('OrgStructure')
    tableOrgIdent  = db.table('OrgStructure_Identification')
    tableRbAccountingSystem  = db.table('rbAccountingSystem')
    queryTable = tableOrg.leftJoin(tableOrgIdent, '''OrgStructure.id = OrgStructure_Identification.master_id''')
    queryTable = queryTable.leftJoin(tableRbAccountingSystem, '''rbAccountingSystem.id = OrgStructure_Identification.system_id''')
    # cond = [tableOrg['id'].eq(orgStructureId), tableRbAccountingSystem.eq('urn:oid:1.2.643.2.69.1.1.1.64')]
    cond = [u" OrgStructure.id = {0} ".format(orgStructureId), u"rbAccountingSystem.urn = 'urn:oid:1.2.643.2.69.1.1.1.64'", u"rbAccountingSystem.code = 'GUID_TVSP'"]
    cols = [tableOrgIdent['value'].alias('idLpu')]
    idLpu = ''
    record = db.getRecordEx(queryTable, cols, cond)
    if record is None:
        return idLpu
    else:
        idLpu = forceString(record.value('idLpu'))
    return idLpu