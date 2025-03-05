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



def ConnectionInfo(orgStructureId):
    db = QtGui.qApp.db
    tableOrg = db.table('OrgStructure')
    tableOrgIdent  = db.table('OrgStructure_Identification')
    tableRbAccountingSystem  = db.table('rbAccountingSystem')
    queryTable = tableOrg.leftJoin(tableOrgIdent, '''OrgStructure.id = OrgStructure_Identification.master_id''')
    queryTable = queryTable.leftJoin(tableRbAccountingSystem, '''rbAccountingSystem.id = OrgStructure_Identification.system_id''')
    # cond = [tableOrg['id'].eq(orgStructureId), tableRbAccountingSystem.eq('urn:oid:1.2.643.2.69.1.1.1.64')]
    cond = [u" OrgStructure.id = {0} ".format(orgStructureId), u"rbAccountingSystem.urn = 'urn:oid:1.2.643.2.69.1.1.1.64'", u"rbAccountingSystem.code = 'org.n3'"]
    cols = [tableOrgIdent['value'].alias('idLpu')]
    idLpu = ''
    record = db.getRecordEx(queryTable, cols, cond)
    if record is None:
        return idLpu
    else:
        idLpu = forceString(record.value('idLpu'))
    return idLpu