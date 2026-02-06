# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QDate

from Reports.MesDispansListDialog import getMesDispansList, getMesDispansNameList

from Reports.Ui_Report131_1000Setup import Ui_Report131_1000SetupDialog


class CReportForm131_1000_SetupDialog(QtGui.QDialog, Ui_Report131_1000SetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbFilterContingentType.setTable('rbSocStatusType', addNone=True, filter='code in ("disp","prof") or code like "%disp%"')
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.setMesDispansListVisible(False)
        self.mesDispansIdList = []


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setMesDispansListVisible(self, value):
        self.mesDispansListVisible = value
        self.btnMesDispansList.setVisible(value)
        self.lblMesDispansList.setVisible(value)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbFilterContingentType.setValue(params.get('contingentTypeId', None))
        self.chkAttache.setChecked(params.get('isAttache', True))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        if self.mesDispansListVisible:
            self.mesDispansIdList = params.get('mesDispansIdList', [])
            nameList = getMesDispansNameList(self.mesDispansIdList)
            if nameList:
                self.lblMesDispansList.setText(u','.join(name for name in nameList if name))
            else:
                self.lblMesDispansList.setText(u'не задано')


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['contingentTypeId'] = self.cmbFilterContingentType.value()
        result['isAttache'] = self.chkAttache.isChecked()
        result['orgId'] = self.cmbOrgStructure.model().orgId
        if self.mesDispansListVisible:
            result['mesDispansIdList'] = self.mesDispansIdList
        return result


    @pyqtSignature('int')
    def on_cmbFilterContingentType_currentIndexChanged(self, index):
        contingentTypeId = self.cmbFilterContingentType.value()
        stringInfo = u'Введите тип контингента' if not contingentTypeId else u''
        self.cmbFilterContingentType.setToolTip(stringInfo)
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(bool(contingentTypeId))


    @pyqtSignature('')
    def on_btnMesDispansList_clicked(self):
        db = QtGui.qApp.db
        tableMES = db.table('mes.MES')
        tableMESGroup = db.table('mes.mrbMESGroup')
        filter = [tableMESGroup['code'].eq(u'ДиспанС'),
                  db.joinOr([tableMES['endDate'].isNull(), tableMES['endDate'].ge(self.edtBegDate.date())])
                  ]
        self.mesDispansIdList, nameList = getMesDispansList(self, filter)
        if self.mesDispansIdList and nameList:
            self.lblMesDispansList.setText(u','.join(name for name in nameList if name))
        else:
            self.lblMesDispansList.setText(u'не задано')

