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
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, QDate, QEvent, QObject, QVariant

from library.TableModel import CRefBookCol, CTableModel, CTextCol
from library.Utils import calcAgeTuple, getPref, setPref, getPrefBool, getPrefInt

from Ui_MESComboBoxPopup import Ui_MESComboBoxPopup


class CMESComboBoxPopup(QtGui.QFrame, Ui_MESComboBoxPopup):
    __pyqtSignals__ = ('MESSelected(int)',
                      )

    def __init__(self, parent = None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.tableModel = CMESTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblMES.setModel(self.tableModel)
        self.tblMES.setSelectionModel(self.tableSelectionModel)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
#       к сожалению в данном случае setDefault обеспечивает рамочку вокруг кнопочки
#       но enter не работает...
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setShortcut(Qt.Key_Return)
        self.eventBegDate = None
        self.clientSex = 0
        self.baseDate = None
        self.clientBirthDate = None
        self.clientAge = None
        self.clientAgePrevYearEnd = None
        self.clientAgeCurrYearEnd = None
        self.eventProfileId = None
        self.specialityId = None
        self.MKB = ''
        self.MKBEx = ''
        self.AssociatedMKB = ''
        self.ComplicationMKB = ''
        self.mesId = None
        self.tblMES.installEventFilter(self)
        self.execDate = None
        self.mesCodeTemplate = None
        self.mesNameTemplate = None
        self.contractId = None
        self.eventTypeId = None
        self.criteriaList = []
        self.fractions = None
        self.headerMESCol = self.tblMES.horizontalHeader()
        self.headerMESCol.setClickable(True)
        QObject.connect(self.headerMESCol,
                               SIGNAL('sectionClicked(int)'),
                               self.onHeaderMESColClicked)

        QObject.connect(self.tblMES.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)
        self.sort = {'column' : 'code',  'desc' : False}

        if QtGui.qApp.provinceKLADR()[:2] == u'23':
            self.chkSpeciality.setVisible(False)
            self.chkActive.setVisible(False)

        widgets = [self.chkSex, self.chkAge, self.chkMesCodeTemplate, self.chkContract, self.chkMesServices,
                   self.chkEventProfile, self.chkMesNameTemplate, self.chkActive, self.chkSpeciality,
                   self.chkAdditionCriteria]
        for widget in widgets:
            QObject.connect(widget, SIGNAL('toggled(bool)'), self.on_widget_toggled)
        QObject.connect(self.cmbMKB, SIGNAL('currentIndexChanged(int)'), self.on_widget_toggled)
        QObject.connect(self.cmbMKBEx, SIGNAL('currentIndexChanged(int)'), self.on_widget_toggled)


    def onHeaderMESColClicked(self, col):
        headerSortingCol = self.tableModel.headerSortingCol.get(col, False)
        self.tableModel.headerSortingCol = {}
        self.tableModel.headerSortingCol[col] = not headerSortingCol
        self.tableModel.sortDataModel()


    def saveChkBoxPreferences(self):
        chkBoxPreferences = QtGui.qApp.preferences.appPrefs
        setPref(chkBoxPreferences, 'chkSex', QVariant(self.chkSex.isChecked()))
        setPref(chkBoxPreferences, 'chkAge', QVariant(self.chkAge.isChecked()))
        setPref(chkBoxPreferences, 'chkEventProfile', QVariant(self.chkEventProfile.isChecked()))
        setPref(chkBoxPreferences, 'chkMesCodeTemplate', QVariant(self.chkMesCodeTemplate.isChecked()))
        setPref(chkBoxPreferences, 'chkMesNameTemplate', QVariant(self.chkMesNameTemplate.isChecked()))
        setPref(chkBoxPreferences, 'chkSpeciality', QVariant(self.chkSpeciality.isChecked()))
        setPref(chkBoxPreferences, 'chkActive', QVariant(self.chkActive.isChecked()))
        setPref(chkBoxPreferences, 'chkMesServices', QVariant(self.chkMesServices.isChecked()))
        setPref(chkBoxPreferences, 'chkContract', QVariant(self.chkContract.isChecked()))
        setPref(chkBoxPreferences, 'cmbMKB', QVariant(self.cmbMKB.currentIndex()))
        setPref(chkBoxPreferences, 'chkAdditionCriteria', QVariant(self.chkAdditionCriteria.isChecked()))


    def loadChkBoxPreferences(self):
        chkBoxPreferences = QtGui.qApp.preferences.appPrefs
        self.chkSex.setChecked(getPrefBool(chkBoxPreferences, 'chkSex', False))
        self.chkAge.setChecked(getPrefBool(chkBoxPreferences, 'chkAge', False))
        self.chkEventProfile.setChecked(getPrefBool(chkBoxPreferences, 'chkEventProfile', False))
        self.chkMesCodeTemplate.setChecked(getPrefBool(chkBoxPreferences, 'chkMesCodeTemplate', False))
        self.chkMesNameTemplate.setChecked(getPrefBool(chkBoxPreferences, 'chkMesNameTemplate', False))
        self.chkSpeciality.setChecked(getPrefBool(chkBoxPreferences, 'chkSpeciality', False))
        self.chkActive.setChecked(getPrefBool(chkBoxPreferences, 'chkActive', False))
        self.chkMesServices.setChecked(getPrefBool(chkBoxPreferences, 'chkMesServices', False))
        self.chkContract.setChecked(getPrefBool(chkBoxPreferences, 'chkContract', False))
        self.chkAdditionCriteria.setChecked(getPrefBool(chkBoxPreferences, 'chkAdditionCriteria', False))
        self.cmbMKB.setCurrentIndex(getPrefInt(chkBoxPreferences, 'cmbMKB', 2))
        self.rbManual.setChecked(True)
               
        
    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent!=None:
            opt=QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(
                QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if (arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos())):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)


    def closeEvent(self, event):
        preferences = self.tblMES.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CMESComboBoxPopup', preferences)
        self.saveChkBoxPreferences()
        QtGui.QFrame.closeEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.tblMES:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblMES.currentIndex()
                self.tblMES.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBox_reset()

    @pyqtSignature('bool')
    def on_rbMKB_toggled(self, checked):
        widgets = [self.chkSex, self.chkAge, self.chkMesCodeTemplate, self.chkContract, self.chkMesServices,
                   self.cmbMKB, self.cmbMKBEx, self.chkEventProfile, self.chkMesNameTemplate, self.chkActive,
                   self.chkSpeciality, self.chkAdditionCriteria]
        if checked:
            for widget in widgets:
                widget.blockSignals(True)
            self.chkSex.setChecked(checked)
            self.chkAge.setChecked(checked)
            self.chkMesCodeTemplate.setChecked(checked)
            self.chkContract.setChecked(checked)
            self.cmbMKB.setCurrentIndex(2)

            self.chkEventProfile.setChecked(not checked)
            self.chkMesNameTemplate.setChecked(not checked)
            self.chkActive.setChecked(not checked)
            self.chkSpeciality.setChecked(not checked)
            self.chkMesServices.setChecked(not checked)
            self.chkAdditionCriteria.setChecked(not checked)
            self.cmbMKBEx.setCurrentIndex(0)
            for widget in widgets:
                widget.blockSignals(False)
            self.on_buttonBox_apply()

    @pyqtSignature('bool')
    def on_widget_toggled(self, checked):
        self.rbManual.setChecked(True)

    @pyqtSignature('bool')
    def on_rbOperation_toggled(self, checked):
        widgets = [self.chkSex, self.chkAge, self.chkMesCodeTemplate, self.chkContract, self.chkMesServices, self.cmbMKB,
                   self.cmbMKBEx, self.chkEventProfile, self.chkMesNameTemplate, self.chkActive, self.chkSpeciality,
                   self.chkAdditionCriteria]
        if checked:
            for widget in widgets:
                widget.blockSignals(True)
            self.chkSex.setChecked(checked)
            self.chkAge.setChecked(checked)
            self.chkMesCodeTemplate.setChecked(checked)
            self.chkContract.setChecked(checked)
            self.chkMesServices.setChecked(checked)

            self.cmbMKB.setCurrentIndex(0)
            self.cmbMKBEx.setCurrentIndex(0)
            self.chkEventProfile.setChecked(not checked)
            self.chkMesNameTemplate.setChecked(not checked)
            self.chkActive.setChecked(not checked)
            self.chkSpeciality.setChecked(not checked)
            self.chkAdditionCriteria.setChecked(not checked)
            for widget in widgets:
                widget.blockSignals(False)
            self.on_buttonBox_apply()


    @pyqtSignature('bool')
    def on_rbManual_toggled(self, checked):
        pass

    def on_buttonBox_reset(self):
        self.chkSex.setChecked(False)
        self.chkAge.setChecked(False)
        self.chkEventProfile.setChecked(False)
        self.chkMesCodeTemplate.setChecked(True)
        self.chkMesNameTemplate.setChecked(False)
        self.chkSpeciality.setChecked(False)
        self.chkActive.setChecked(False)
        self.chkMesServices.setChecked(False)
        self.cmbMKB.setCurrentIndex(2)
        self.cmbMKBEx.setCurrentIndex(0)


    def on_buttonBox_apply(self):
        useSex        = self.chkSex.isChecked()
        useAge        = self.chkAge.isChecked()
        useProfile    = self.chkEventProfile.isChecked()
        useMesCode  = self.chkMesCodeTemplate.isChecked()
        useMesName = self.chkMesNameTemplate.isChecked()
        useSpeciality   = self.chkSpeciality.isChecked()
        useMesServices = self.chkMesServices.isChecked()
        useActivity   = self.chkActive.isChecked()
        useContract = self.chkContract.isChecked()
        mkbCond    = self.cmbMKB.currentIndex()
        mkbCondEx  = self.cmbMKBEx.currentIndex()
        useAdditionCriteria = self.chkAdditionCriteria.isChecked()
        idList = self.getMesIdList(useSex, useAge, useProfile, useMesCode, useMesName, useMesServices, useSpeciality, useActivity, useContract, mkbCond, mkbCondEx, useAdditionCriteria)
        self.setMESIdList(idList)


    def setMESIdList(self, idList):
        # if idList:
        self.tblMES.setIdList(idList, self.mesId)
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.setTabEnabled(0, True)
        self.tblMES.setFocus(Qt.OtherFocusReason)
        # else:
        #     self.tabWidget.setCurrentIndex(1)
        #     self.tabWidget.setTabEnabled(0, False)
        #     self.chkSex.setFocus(Qt.OtherFocusReason)


    def getMesIdList(self, useSex, useAge, useProfile, useMesCode, useMesName, useMesServices, useSpeciality, useActivity, useContract, mkbCond, mkbCondEx, useAdditionCriteria=False):
        db = QtGui.qApp.db
        tableMES = db.table('mes.MES')
        tableMESService = db.table('mes.MES_service')
        tableMESRBService = db.table('mes.mrbService')
        queryTable = tableMES
        cond  = []
        date = self.execDate if self.execDate else self.eventBegDate
        if not date:
            date = self.baseDate
        if self.eventProfileId and useProfile:
            tableMESGroup = db.table('mes.mrbMESGroup')
            tableEventProfile = db.table('rbEventProfile')
            queryTable = queryTable.leftJoin(tableMESGroup, tableMESGroup['id'].eq(tableMES['group_id']))
            queryTable = queryTable.leftJoin(tableEventProfile, tableEventProfile['regionalCode'].eq(tableMESGroup['code']))
            cond.append(db.joinOr([tableEventProfile['id'].eq(self.eventProfileId), tableMESGroup['id'].isNull(), '''TRIM(mes.mrbMESGroup.code) = '' ''']))
        if self.mesCodeTemplate and useMesCode:
            cond.append(tableMES['code'].regexp(self.mesCodeTemplate))
        if self.mesNameTemplate and useMesName:
            cond.append(tableMES['name'].regexp(self.mesNameTemplate))
        if date:
            cond.append(db.joinOr([tableMES['endDate'].isNull(), tableMES['endDate'].ge(date)]))
        if (self.clientSex and useSex) or (self.clientAge and useAge):
            tableMESLimitedBySexAge = db.table('mes.MES_limitedBySexAge')
            queryTable = queryTable.leftJoin(tableMESLimitedBySexAge, tableMESLimitedBySexAge['master_id'].eq(tableMES['id']))
            sexStr = ''
            ageStr = ''
            if self.clientSex and useSex:
                sexStr = u''' AND mes.MES_limitedBySexAge.sex in (%d, 0) ''' % (self.clientSex)
            if self.clientAge and useAge:
                clientAge = self.clientAge[3]
                clientAgeMonths = self.clientAge[2]
                if clientAge == 0:
                    clientAge = round(clientAgeMonths / 12.0, 2)
                if self.clientAgePrevYearEnd is None:
                    self.clientAgePrevYearEnd = self.clientAgeCurrYearEnd
                    if self.baseDate and self.clientBirthDate:
                        self.clientAgeCurrYearEnd = calcAgeTuple(self.clientBirthDate, QDate(self.baseDate.year(), 12, 31))
                clientAgeCurrYearEnd = self.clientAgeCurrYearEnd[3]
                clientAgeMonthsCurrYear = self.clientAgeCurrYearEnd[2]
                if clientAgeCurrYearEnd == 0:
                    clientAgeCurrYearEnd = round(clientAgeMonthsCurrYear / 12.0, 2)
                clientAgePrevYearEnd = self.clientAgePrevYearEnd[3]
                clientAgeMonthsPrevYear = self.clientAgePrevYearEnd[2]
                if clientAgePrevYearEnd == 0:
                    clientAgePrevYearEnd = round(clientAgeMonthsPrevYear / 12.0, 2)
                ageStr = u''' AND (mes.MES_limitedBySexAge.minimumAge = 0 or mes.MES_limitedBySexAge.minimumAge <= (
                IF(mes.MES_limitedBySexAge.begAgeUnit = 1,
                IF(mes.MES_limitedBySexAge.controlPeriod = 1, %s, IF(mes.MES_limitedBySexAge.controlPeriod = 2, %s, %s)),
                IF(mes.MES_limitedBySexAge.begAgeUnit = 2,
                IF(mes.MES_limitedBySexAge.controlPeriod = 1, %s, IF(mes.MES_limitedBySexAge.controlPeriod = 2, %s, %s)),
                IF(mes.MES_limitedBySexAge.begAgeUnit = 3,
                IF(mes.MES_limitedBySexAge.controlPeriod = 1, %s, IF(mes.MES_limitedBySexAge.controlPeriod = 2, %s, %s)),
                IF(mes.MES_limitedBySexAge.begAgeUnit = 4,
                IF(mes.MES_limitedBySexAge.controlPeriod = 1, %s, IF(mes.MES_limitedBySexAge.controlPeriod = 2, %s, %s)),
                IF(mes.MES_limitedBySexAge.controlPeriod = 1, %s, IF(mes.MES_limitedBySexAge.controlPeriod = 2, %s, %s))))))))
                
                AND (mes.MES_limitedBySexAge.maximumAge = 0 or mes.MES_limitedBySexAge.maximumAge >= (
                IF(mes.MES_limitedBySexAge.endAgeUnit = 1,
                IF(mes.MES_limitedBySexAge.controlPeriod = 1, %s, IF(mes.MES_limitedBySexAge.controlPeriod = 2, %s, %s)),
                IF(mes.MES_limitedBySexAge.endAgeUnit = 2,
                IF(mes.MES_limitedBySexAge.controlPeriod = 1, %s, IF(mes.MES_limitedBySexAge.controlPeriod = 2, %s, %s)),
                IF(mes.MES_limitedBySexAge.endAgeUnit = 3,
                IF(mes.MES_limitedBySexAge.controlPeriod = 1, %s, IF(mes.MES_limitedBySexAge.controlPeriod = 2, %s, %s)),
                IF(mes.MES_limitedBySexAge.endAgeUnit = 4,
                IF(mes.MES_limitedBySexAge.controlPeriod = 1, %s, IF(mes.MES_limitedBySexAge.controlPeriod = 2, %s, %s)),
                IF(mes.MES_limitedBySexAge.controlPeriod = 1, %s, IF(mes.MES_limitedBySexAge.controlPeriod = 2, %s, %s))
                ))))))
                '''%(u'%.2f'%(self.clientAgeCurrYearEnd[0]), u'%.2f'%(self.clientAgePrevYearEnd[0]), u'%.2f'%(self.clientAge[0]),
                u'%.2f'%(self.clientAgeCurrYearEnd[1]), u'%.2f'%(self.clientAgePrevYearEnd[1]), u'%.2f'%(self.clientAge[1]),
                u'%.2f'%(self.clientAgeCurrYearEnd[2]),u'%.2f'%(self.clientAgePrevYearEnd[2]),u'%.2f'%(self.clientAge[2]),
                u'%.2f'%(self.clientAgeCurrYearEnd[3]), u'%.2f'%(self.clientAgePrevYearEnd[3]), u'%.2f'%(self.clientAge[3]),
                u'%.2f'%(clientAgeCurrYearEnd), u'%.2f'%(clientAgePrevYearEnd), u'%.2f'%(clientAge),
                u'%.2f'%(self.clientAgeCurrYearEnd[0]), u'%.2f'%(self.clientAgePrevYearEnd[0]), u'%.2f'%(self.clientAge[0]),
                u'%.2f'%(self.clientAgeCurrYearEnd[1]), u'%.2f'%(self.clientAgePrevYearEnd[1]), u'%.2f'%(self.clientAge[1]),
                u'%.2f'%(self.clientAgeCurrYearEnd[2]),u'%.2f'%(self.clientAgePrevYearEnd[2]),u'%.2f'%(self.clientAge[2]),
                u'%.2f'%(self.clientAgeCurrYearEnd[3]), u'%.2f'%(self.clientAgePrevYearEnd[3]), u'%.2f'%(self.clientAge[3]),
                u'%.2f'%(clientAgeCurrYearEnd), u'%.2f'%(clientAgePrevYearEnd), u'%.2f'%(clientAge)
                )
            sexAgeStr = u'''NOT EXISTS(SELECT MES_limitedBySexAge.id FROM mes.MES_limitedBySexAge AS MES_limitedBySexAge
                  WHERE mes.MES.`id` = MES_limitedBySexAge.`master_id` AND MES_limitedBySexAge.`master_id` IS NOT NULL AND MES_limitedBySexAge.deleted = 0
                  LIMIT 1) OR (mes.MES_limitedBySexAge.deleted = 0%s%s)'''%(sexStr, ageStr)
            cond.append(sexAgeStr)
        if self.specialityId and useSpeciality:
            regionalCode = db.translate('rbSpeciality', 'id', self.specialityId, 'regionalCode')
            tableMESVisit      = db.table('mes.MES_visit')
            tableMESSpeciality = db.table('mes.mrbSpeciality')
            tableMESVisitType  = db.table('mes.mrbVisitType')
            subTable = tableMESVisit.leftJoin(tableMESVisitType,  tableMESVisitType['id'].eq(tableMESVisit['visitType_id']))
            subTable = subTable.leftJoin(tableMESSpeciality, tableMESSpeciality['id'].eq(tableMESVisit['speciality_id']))

            subCond  = [tableMESVisit['master_id'].eq(tableMES['id']),
                        tableMESVisit['deleted'].eq(0),
#                        tableMESVisitType['code'].eq(u'Л'),
                        tableMESSpeciality['regionalCode'].eq(regionalCode)
                       ]
            cond.append(db.joinOr([db.existsStmt(subTable, subCond),
                                   'NOT '+db.existsStmt(tableMESVisit, tableMESVisit['master_id'].eq(tableMES['id']))
                                  ]))
        if useActivity:
            cond.append(tableMES['active'].eq(1))

        if useContract and self.contractId:

            condET = 'and (ct.eventType_id = %d or ct.eventType_id is null)' % self.eventTypeId if self.eventTypeId else ''
            contractCond = u'''MES.code in (
            select s.infis from rbService s
            left join Contract c on c.id = %d
            left join Contract_Tariff ct on ct.service_id = s.id
            where ct.master_id in (c.id, c.priceListExternal_id) and
            ct.deleted = 0 and
            (ct.endDate is not null and %s between ct.begDate and ct.endDate
             or %s >= ct.begDate and ct.endDate is null) and
            ct.tariffType = 13 %s
            )
            ''' % (self.contractId, db.formatDate(date) , db.formatDate(date), condET)
            cond.append(contractCond)
        cond.append(tableMES['deleted'].eq(0))
        
        if self.mesServiceTemplate and useMesServices:
            queryTable = queryTable.innerJoin(tableMESService, tableMESService['master_id'].eq(tableMES['id']))
            queryTable = queryTable.innerJoin(tableMESRBService, tableMESRBService['id'].eq(tableMESService['service_id']))
            joinOr = []
            for mesService in self.mesServiceTemplate:
                joinOr.append(u"mes.mrbService.code LIKE '%s' "% (mesService))
                
            cond.append(db.joinOr(joinOr))
            cond.append(tableMESService['deleted'].eq(0))
            cond.append(tableMESRBService['deleted'].eq(0))
            cond.append(db.joinOr([tableMESService['begDate'].isNull(), tableMESService['begDate'].le(date)]))
            cond.append(db.joinOr([tableMESService['endDate'].isNull(), tableMESService['endDate'].ge(date)]))
            if useAdditionCriteria:
                if self.criteriaList and self.fractions is not None:
                    cond.append(db.joinAnd([tableMESService['minFr'].le(self.fractions),
                                            tableMESService['maxFr'].ge(self.fractions),
                                            tableMESService['krit'].inlist(self.criteriaList)]))

                elif self.criteriaList:
                    cond.append(db.joinOr([tableMESService['krit'].inlist(self.criteriaList),
                                           tableMESService['krit'].isNull()]))
            
            # условие по кодам мкб
            if (self.MKB or self.AssociatedMKB or self.ComplicationMKB) and mkbCond:
                str_mkb = "and (mes.SPR69.MKBX is null or mes.SPR69.MKBX = '%s' or (substr(mes.SPR69.MKBX, 1, 2) like '_.' and substr(mes.SPR69.MKBX, 1, 1) = '%s'))" % (self.MKB, self.MKB[:1])
                str_mkb += "and (mes.SPR69.MKBX2 is null or mes.SPR69.MKBX2 = '%s')" % self.AssociatedMKB
                str_mkb += "and (mes.SPR69.MKBX3 is null or mes.SPR69.MKBX3 = '%s')" % self.ComplicationMKB
            else:
                str_mkb = "and mes.SPR69.MKBX is null"
            cond.append(u"(mes.MES.code like 'G%%' and exists(select id from mes.SPR69 where mes.SPR69.KSGCODE = mes.MES.code %s and mes.mrbService.code = mes.SPR69.KUSL) or mes.MES.code not like 'G%%')" % str_mkb)     


        if (self.MKB or self.AssociatedMKB or self.ComplicationMKB) and mkbCond:
            tableMESMkb  = db.table('mes.MES_mkb')
            if mkbCond == 2: # строгое соответствие
                subCond = db.joinAnd([db.joinOr([db.joinAnd([tableMESMkb['mkb'].like('_.'), tableMESMkb['mkb'].like(self.MKB[:1] + '.')]),
                    tableMESMkb['mkb'].eq(self.MKB), tableMESMkb['mkb'].eq('')]),
                    db.joinOr([tableMESMkb['mkb2'].eq(self.AssociatedMKB), tableMESMkb['mkb2'].isNull()]),
                    db.joinOr([tableMESMkb['mkb3'].eq(self.ComplicationMKB), tableMESMkb['mkb3'].isNull()])
                    ])
            else: # по рубрике
                subCond = db.joinOr([db.joinAnd([tableMESMkb['mkb'].like('_.'), tableMESMkb['mkb'].like(self.MKB[:1] + '.')]),
                    tableMESMkb['mkb'].like(self.MKB[:3]+'%')])
            subCond  = [ tableMESMkb['master_id'].eq(tableMES['id']),
                         tableMESMkb['deleted'].eq(0),
                         subCond
                       ]

            subCond.append(db.joinOr([tableMESMkb['begDate'].isNull(), tableMESMkb['begDate'].le(date)]))
            subCond.append(db.joinOr([tableMESMkb['endDate'].isNull(), tableMESMkb['endDate'].ge(date)]))

            if useAdditionCriteria:
                if self.criteriaList:
                    subCond.append(db.joinOr([tableMESMkb['krit'].inlist(self.criteriaList),
                                tableMESMkb['krit'].isNull()]))
                if self.fractions is not None:
                    cond.append(db.joinAnd([tableMESService['minFr'].le(self.fractions),
                                            tableMESService['maxFr'].ge(self.fractions)]))

            # условие по кодам услуг
            str_usl = "and ifnull(KUSL, '') in (''"
            if self.mesServiceTemplate and useMesServices:
                
                for mesService in self.mesServiceTemplate:
                    str_usl += ", '" + mesService + "'"
                    
            str_usl += ')'
                    
            subCond.append(u"""(mes.MES.code like 'G%%' and exists(select id from mes.SPR69 where mes.SPR69.KSGCODE = mes.MES.code 
            AND IFNULL(mes.MES_mkb.MKB, '') between IFNULL(mes.SPR69.mkb1beg, '') AND IFNULL(mes.SPR69.mkb1end, '')
            AND IFNULL(mes.MES_mkb.mkb2, '') between IFNULL(mes.SPR69.mkb2beg, '') AND IFNULL(mes.SPR69.mkb2end, '')
            %s) or mes.MES.code not like 'G%%')""" % str_usl)
            cond.append(db.existsStmt(tableMESMkb, subCond))

        if self.MKBEx and mkbCondEx:
            tableMESMkbEx  = db.table('mes.MES_mkb').alias('MES_mkbEx')
            if mkbCondEx == 2: # строгое соответствие
                subCond = tableMESMkbEx['mkbEx'].inlist([self.MKBEx])
            else: # по рубрике
                subCond  = tableMESMkbEx['mkbEx'].like(self.MKBEx[:3]+'%')
            subCond  = [ tableMESMkbEx['master_id'].eq(tableMES['id']),
                         tableMESMkbEx['deleted'].eq(0),
                         subCond
                       ]
            cond.append(db.existsStmt(tableMESMkbEx, subCond))

        if useAdditionCriteria:
            tableSpr69 = db.table('soc_spr69')
            queryTable = queryTable.innerJoin(tableSpr69, tableSpr69['ksgkusl'].eq(tableMES['code']))
            if date:
                cond.append(db.joinOr([tableSpr69['dato'].isNull(), tableSpr69['dato'].ge(date)]))
                cond.append(db.joinOr([tableSpr69['datn'].isNull(), tableSpr69['datn'].le(date)]))

            if self.criteriaList:
                cond.append(tableSpr69['KRIT'].inlist(self.criteriaList))
            if self.fractions:
                cond.append(tableSpr69['fr'].eq(self.fractions))

        orderCond='mes.MES.code asc, mes.MES.id'

        idList = db.getDistinctIdList(queryTable, tableMES['id'].name(),
                              where=cond,
                              order=orderCond,
                              )
                              
        return idList


    def setup(self, baseDate, clientSex, clientBirthDate, clientAge, clientAgePrevYearEnd, clientAgeCurrYearEnd, eventProfileId, mesCodeTemplate, mesNameTemplate, mesServiceTemplate, specialityId, MKB, AssociatedMKB, ComplicationMKB, MKBEx, mesId, eventBegDate, contractId, execDate, eventTypeId, criteriaList, fractions):
        self.eventBegDate = eventBegDate
        self.clientSex = clientSex
        self.baseDate = baseDate
        self.clientBirthDate = clientBirthDate
        self.clientAge = clientAge
        self.clientAgePrevYearEnd = clientAgePrevYearEnd
        self.clientAgeCurrYearEnd = clientAgeCurrYearEnd
        self.eventProfileId = eventProfileId
        self.mesCodeTemplate = mesCodeTemplate
        self.mesNameTemplate = mesNameTemplate
        self.mesServiceTemplate = mesServiceTemplate
        self.specialityId = specialityId
        self.MKB = MKB
        self.AssociatedMKB = AssociatedMKB
        self.ComplicationMKB = ComplicationMKB
        self.MKBEx = MKBEx
        self.mesId = mesId
        self.chkMesCodeTemplate.setChecked(bool(mesCodeTemplate))
        self.chkMesNameTemplate.setChecked(bool(mesNameTemplate))
        self.contractId = contractId
        self.execDate = execDate
        self.eventTypeId = eventTypeId
        self.criteriaList = criteriaList
        self.fractions = fractions
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CMESComboBoxPopup', {})
        self.tblMES.loadPreferences(preferences)
        self.loadChkBoxPreferences()
        self.on_buttonBox_apply()


    @pyqtSignature('QModelIndex')
    def on_tblMES_doubleClicked(self, index):
        if index.isValid():
            if (Qt.ItemIsEnabled & self.tableModel.flags(index)):
                mesId = self.tblMES.currentItemId()
                self.mesId = mesId
                self.emit(SIGNAL('MESSelected(int)'), mesId)
                self.close()
    def setSort(self, col):
        #0 - Группа
        #1 - Код
        #2 - наименование
        #3 - Описание
        #4 - К. затратности
        if col in [0, 1, 2, 3, 4]:
            colN = ('group_id',  'code',  'name',  'descr',  'ksgkoef')[col]
            if self.sort['column'] == colN:
                self.sort['desc'] = not self.sort['desc']
            else:
                self.sort['column']  = colN
                self.sort['desc'] = False
            self.tblMES.model().sort(self.sort['column'], self.sort['desc'])
        


class CMESTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CRefBookCol(u'Группа',       ['group_id'],  'mes.mrbMESGroup', 10))
        self.addColumn(CTextCol(u'Код',             ['code'],  20))
        self.addColumn(CTextCol(u'Наименование',    ['name'],  40))
        self.addColumn(CTextCol(u'Описание',        ['descr'], 40))
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            self.addColumn(CTextCol(u'Коэф. затратоемкости', ['ksgkoef'], 4))
        else:
            self.addColumn(CTextCol(u'Модель пациента', ['patientModel'], 20))
        self.setTable('mes.MES')
        self.date = QDate.currentDate()

    def sort(self, colN, reverse):
        if self._idList:
            db = QtGui.qApp.db
            tableMES = db.table('mes.MES')
            cond = [tableMES['id'].inlist(self._idList)]
            order = '%s %s'%(colN, u'DESC' if reverse else u'ASC')
            self._idList = db.getIdList(tableMES, tableMES['id'].name(), cond, order)
            self.reset()
        pass
        
    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable
