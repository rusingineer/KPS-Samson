# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import re

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, SIGNAL, pyqtSignature, QVariant, QString, QDate

#from library.adjustPopup         import adjustPopupToWidget
from library.crbcombobox import CRBComboBox
from library.DialogBase      import CConstructHelperMixin
from library.InDocTable      import (
                                         CLocItemDelegate,
                                         CRecordListModel,
                                         CRBInDocTableCol,
                                         CSelectStrInDocTableCol,
                                        )
from library.SortedDict      import CSortedDict
from library.TableModel     import CTableModel, CTextCol, CRefBookCol
from library.Utils               import (
                                         forceRef,
                                         forceString,
                                         forceStringEx,
                                         toVariant,
                                         forceBool,
                                         forceInt,
                                         getPref,
                                         setPref,
                                         withWaitCursor,
                                         trim,
                                        )
from library.SortFilterProxyTableModel import CSortFilterProxyTableModel
from Users.Rights import urEditChkOnlyExistsNomenclature, urAddNewNomenclatureAction
from Stock.Utils                 import (
                                         getExistsNomenclatureIdList,
                                         getExistsNomenclatureAmountSum,
                                        )

from Ui_NomenclatureComboBoxPopup import Ui_NomenclatureComboBoxPopup


class CNomenclatureComboBox(CRBComboBox):
    def __init__(self, parent, nomenclatureId = None, needInternationalNonproprietaryName = False):
        CRBComboBox.__init__(self, parent)
        self.setTable('rbNomenclature')
        self.defaultClassId = None
        self.defaultKindId = None
        self.defaultTypeId = None
        self.defaultFeatures = []
        self._popup = None
        self._stockOrgStructureId = None
        self._onlyExists = False
        self._onlyNomenclature = False
        self._useClientUnitId = False
        self._financeId = None
        self.findNomenclatureName = u''
        self._medicalAidKindId = None
        self._activeSubstanceId = None
        self._smnnUUID = None
        self._smnnName = ''
        self._onlySmnn = False
        self._lfFormId = None
        self._mainStockId = self.getMainStockId() if forceBool(QtGui.qApp.preferences.appPrefs.get('showMainStockRemainings', QVariant())) else None
        self._filter = u''
        self._additionalCond = u''
        self.isFinanceVisible = 0 # 0-как обычно, 1-не показывать, 2-показывать #0013272
        self.isOnlyMnnEsklpFormVisible = False
        self.needInternationalNonproprietaryName = needInternationalNonproprietaryName


    def setIsFinanceVisible(self, value):
        self.isFinanceVisible = value


    def setIsOnlyMnnEsklpFormVisible(self, value):
        self.isOnlyMnnEsklpFormVisible = value


    def setAdditionalCond(self, cond):
        self._additionalCond = forceString(cond)


    def setOnlySmnn(self, value):
        self._onlySmnn = value


    def setFindNomenclatureName(self, value):
        self.findNomenclatureName = value


    def setNomenclatureActiveSubstanceId(self, activeSubstanceId):
        self._activeSubstanceId = activeSubstanceId


    def setNomenclatureSmnnUUID(self, smnnUUID):
        self._smnnUUID = smnnUUID


    def setNomenclatureSmnnName(self, smnnName):
        self._smnnName = smnnName


    def setLfFormId(self, lfFormId):
        self._lfFormId = lfFormId


    def setUseClientUnitId(self, value=True):
        self._useClientUnitId = value


    def setOrgStructureId(self, orgStructureId):
        self._stockOrgStructureId = orgStructureId


    def setOnlyExists(self, value=True):
        self._onlyExists = value


    def setOnlyNomenclature(self, value=False):
        self._onlyNomenclature = value


    def setFinanceId(self, value=None):
        self._financeId = value


    def getMainStockId(self):
        mainStockId = None
        db = QtGui.qApp.db
        table = db.table('OrgStructure')
        record = db.getRecordEx(table, 'id', [table['mainStocks'].eq(1)])
        if record:
            mainStockId = forceInt(record.value('id'))
        return mainStockId


    def setMedicalAidKindId(self, value=None):
        self._medicalAidKindId = value


    def setDefaultIds(self, classId, kindId, typeId):
        self.defaultClassId = classId
        self.defaultKindId = kindId
        self.defaultTypeId = typeId


    def setDefaultClassId(self, classId):
        self.defaultClassId = classId


    def setDefaultKindId(self, kindId):
        self.defaultKindId = kindId


    def setDefaultTypeId(self, typeId):
        self.defaultTypeId = typeId


    def setDefaultFeatures(self, features):
        self.defaultFeatures = features


    def updateItems(self):
        self.reloadData()


    def setQValue(self, var):
        self.setValue(forceRef(var))


    def setFinanceMedicalAidKind(self, var):
        if self._financeId != self._popup._financeId:
            self.setFinanceId(self._popup._financeId)
        if self._medicalAidKindId != self._popup._medicalAidKindId:
            self.setMedicalAidKindId(self._popup._medicalAidKindId)
        self.getFilterData()
        self._filier = self._filter
        self.reloadData()


    def getFilterData(self):
        db = QtGui.qApp.db
        cond = []
        activeSubstanceIdList = []
        smnnIdList = []
        self._filter = u'0'
        tableNomenclature = db.table('rbNomenclature')
        if self._activeSubstanceId:
            tableNomenclatureComposition = db.table('rbNomenclature_Composition')
            queryTableComposition = tableNomenclature.innerJoin(tableNomenclatureComposition, tableNomenclatureComposition['master_id'].eq(tableNomenclature['id']))
            activeSubstanceCond = [tableNomenclatureComposition['activeSubstance_id'].eq(self._activeSubstanceId)]
            activeSubstanceIdList = db.getDistinctIdList(queryTableComposition, tableNomenclature['id'].name(), activeSubstanceCond)
        if self.isOnlyMnnEsklpFormVisible and forceBool(QtGui.qApp.preferences.appPrefs.get('NomenclatureComboBoxPopup_isOnlyMnnEsklpForm', False)):
            cond = []
            if self._smnnName:
                tableEsklp_Smnn = db.table('esklp.Smnn')
                tableNC = db.table('rbNomenclature')
                tableESKLP_Klp = db.table('esklp.Klp')
                queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
                queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
                cond.append(tableEsklp_Smnn['mnn'].eq(self._smnnName))
                if self._lfFormId:
                    tableLfForm= db.table('rbLfForm')
                    tableEsklp_SmnnGrlsLf = db.table('esklp.Smnn_GrlsLf')
                    lfFormRecord = db.getRecordEx(tableLfForm, [tableLfForm['name']], [tableLfForm['id'].eq(self._lfFormId)])
                    lfFormName = forceStringEx(lfFormRecord.value('name')) if lfFormRecord else ''
                    queryTable = queryTable.innerJoin(tableEsklp_SmnnGrlsLf, tableEsklp_SmnnGrlsLf['master_id'].eq(tableEsklp_Smnn['id']))
                    queryTable = queryTable.innerJoin(tableLfForm, db.joinAnd([tableLfForm['name'].eq(tableEsklp_SmnnGrlsLf['lf_name']), tableLfForm['dosage'].eq(tableEsklp_SmnnGrlsLf['dosage_name'])]))
                    cond.append(tableLfForm['isESKLP'].eq(1))
                    cond.append(tableLfForm['name'].eq(lfFormName))
                    cond.append(tableLfForm['name'].eq(tableESKLP_Klp['lf_norm_name']))
                    cond.append(tableNC['lfForm_id'].eq(tableLfForm['id']))
                smnnIdList = db.getDistinctIdList(queryTable, [tableNC['id']], cond)
        elif self._smnnUUID:
            tableEsklp_Smnn = db.table('esklp.Smnn')
            tableNC = db.table('rbNomenclature')
            tableESKLP_Klp = db.table('esklp.Klp')
            queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
            queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
            cond = [tableEsklp_Smnn['UUID'].eq(self._smnnUUID)]
            if self._lfFormId:
                tableLfForm= db.table('rbLfForm')
                tableEsklp_SmnnGrlsLf = db.table('esklp.Smnn_GrlsLf')
                queryTable = queryTable.innerJoin(tableEsklp_SmnnGrlsLf, tableEsklp_SmnnGrlsLf['master_id'].eq(tableEsklp_Smnn['id']))
                queryTable = queryTable.innerJoin(tableLfForm, db.joinAnd([tableLfForm['name'].eq(tableEsklp_SmnnGrlsLf['lf_name']), tableLfForm['dosage'].eq(tableEsklp_SmnnGrlsLf['dosage_name'])]))
                cond.append(tableLfForm['id'].eq(self._lfFormId))
                cond.append(tableLfForm['isESKLP'].eq(1))
                cond.append(tableLfForm['name'].eq(tableESKLP_Klp['lf_norm_name']))
                cond.append(tableLfForm['dosage'].eq(tableESKLP_Klp['dosage_norm_name']))
            smnnIdList = db.getDistinctIdList(queryTable, [tableNC['id']], cond)
        activeSubstanceIdList = list(set(activeSubstanceIdList)|set(smnnIdList))
        if self._onlyExists:
            existsIdList = getExistsNomenclatureIdList(self._stockOrgStructureId, self._financeId, self._medicalAidKindId, nomenclatureIdList = activeSubstanceIdList, isFinanceComboBoxFilter = bool(self.isFinanceVisible))
            if existsIdList:
                cond.append(tableNomenclature['id'].inlist(existsIdList))
                self._filter = 'id in (%s)'%str(existsIdList).strip('[]')
        elif not self._onlyNomenclature:
            existsIdList = getExistsNomenclatureIdList(self._stockOrgStructureId, self._financeId, self._medicalAidKindId, otherHaving = [u'qnt>0'], nomenclatureIdList = activeSubstanceIdList, isFinanceComboBoxFilter = bool(self.isFinanceVisible))
            if existsIdList:
                self._filter = 'id in (%s)'%str(existsIdList).strip('[]')
        else:
            self._filter = u''


    def showPopup(self):
        nomenclatureId = self.getValue()
        if not self._popup:
            self._popup = CNomenclatureComboBoxPopup(self, self._useClientUnitId, self._financeId, self._medicalAidKindId, self.needInternationalNonproprietaryName)
            self.connect(self._popup, SIGNAL('itemsUpdated()'), self.updateItems)
            self.connect(self._popup, SIGNAL('itemSelected(QVariant)'), self.setQValue)
            self.connect(self._popup, SIGNAL('applySearch(QVariant)'), self.setFinanceMedicalAidKind)
        self._popup.setDefaultIds(self.defaultClassId, self.defaultKindId, self.defaultTypeId)
        self._popup.setStockOrgStructureId(self._stockOrgStructureId)
        self._popup.setOnlySmnn(self._onlySmnn)
        self._popup.setNomenclatureActiveSubstanceId(self._activeSubstanceId)
        self._popup.setLfFormId(self._lfFormId)
        self._popup.setNomenclatureSmnnUUID(self._smnnUUID)
        self._popup.setNomenclatureSmnnName(self._smnnName)
        self._popup.setOnlyExists(self._onlyExists)
        self._popup.setOnlyNomenclature(self._onlyNomenclature)
        self._popup.setIsFinanceVisible(self.isFinanceVisible)
        self._popup.setIsOnlyMnnEsklpFormVisible(self.isOnlyMnnEsklpFormVisible)
        self._popup.setFindNomenclatureName(self.findNomenclatureName)
        if not QtGui.qApp.userHasRight(urEditChkOnlyExistsNomenclature):
            self._popup.setOnlyExistsEnabled(False)
        if QtGui.qApp.controlSMFinance() == 1:
            self._popup.setFinanceId(self._financeId)
            self._popup.setEventMedicalAidKindId(self._medicalAidKindId)
            if self.isFinanceVisible == 0:
                self._popup.setFinanceEnabled(True)
            else:
                self._popup.setFinanceEnabled(self.isFinanceVisible == 2)
            self._popup.setMedicalAidKindEnabled(True)
        elif QtGui.qApp.controlSMFinance() == 2:
            self._popup.setFinanceId(self._financeId)
            self._popup.setEventMedicalAidKindId(self._medicalAidKindId)
            if self.isFinanceVisible == 0:
                self._popup.setFinanceEnabled(False)
            else:
                self._popup.setFinanceEnabled(self.isFinanceVisible == 2)
            self._popup.setMedicalAidKindEnabled(False)
        elif QtGui.qApp.controlSMFinance() == 0:
            self._popup.setFinanceId(None)
            if self.isFinanceVisible == 0:
                self._popup.setFinanceVisible(False)
                self._popup.setFinanceEnabled(False)
            else:
                self._popup.setFinanceVisible(self.isFinanceVisible == 2)
                self._popup.setFinanceEnabled(self.isFinanceVisible == 2)
            self._popup.setMedicalAidKindVisible(False)
            self._popup.setMedicalAidKindEnabled(False)
            self._popup.setEventMedicalAidKindId(self._medicalAidKindId)
        if nomenclatureId:
            self._popup.setNomenclatureId(nomenclatureId)
        self._popup.setMainStockId(self._mainStockId)
        self._popup.setDefaultFeatures(self.defaultFeatures)
        self._popup.setAdditionalCond(self._additionalCond)
        pos = self.rect().bottomLeft()
        pos = self.mapToGlobal(pos)
        size = self._popup.sizeHint()
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        size.setWidth(screen.width())
        pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
        pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
        self._popup.move(pos)
        self._popup.resize(size)
        self._popup.show()
        self.setValue(nomenclatureId)


    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            event.ignore()
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            event.ignore()
        if key == Qt.Key_Delete or key == Qt.Key_Backspace:
            self.setValue(None)
            event.accept()
        else:
            CRBComboBox.keyPressEvent(self, event)


class CNomenclatureInDocTableCol(CRBInDocTableCol):
    def __init__(self, title, fieldName, width, **params):
        CRBInDocTableCol.__init__(self, title, fieldName, width, 'rbNomenclature', **params)
        self.defaultClassId = None
        self.defaultKindId = None
        self.defaultTypeId = None
        self._stockOrgStructureId = None
        self._activeSubstanceId = None
        self._smnnUUID = None
        self._smnnName = ''
        self._onlySmnn = False
        self._lfFormId = None
        self._findNomenclatureName = u''
        self._showLfForm = params.get('showLfForm', False)
        self._stringCache = {}
        self._tableNomenclature = QtGui.qApp.db.table(self.tableName)
        self._tableLfForm = QtGui.qApp.db.table('rbLfForm')
        self.isOnlyMnnEsklpFormVisible = False


    def setIsOnlyMnnEsklpFormVisible(self, value):
        self.isOnlyMnnEsklpFormVisible = value


    def setOnlySmnn(self, value):
        self._onlySmnn = value


    def setStockOrgStructureId(self, orgStructureId):
        self._stockOrgStructureId = orgStructureId


    def setNomenclatureActiveSubstanceId(self, activeSubstanceId):
        self._activeSubstanceId = activeSubstanceId


    def setNomenclatureSmnnUUID(self, smnnUUID):
        self._smnnUUID = smnnUUID


    def setNomenclatureSmnnName(self, smnnName):
        self._smnnName = smnnName


    def setLfFormId(self, lfFormId):
        self._lfFormId = lfFormId


    def setFindNomenclatureName(self, value):
        self._findNomenclatureName = value


    def toString(self, val, record):
        if not self._showLfForm:
            return CRBInDocTableCol.toString(self, val, record)

        nomenclatureId = forceRef(val)
        if nomenclatureId not in self._stringCache:
            text = forceString(CRBInDocTableCol.toString(self, val, record))
            lfForm = self._getLfForm(nomenclatureId)
            lfForm = u'/{0}'.format(lfForm) if lfForm else u''
            self._stringCache[nomenclatureId] = u'{0}{1}'.format(text, lfForm).strip()
        return toVariant(self._stringCache[nomenclatureId])


    def _getLfForm(self, nomenclatureId):
        queryTable = self._tableNomenclature.innerJoin(
            self._tableLfForm, self._tableLfForm['id'].eq(self._tableNomenclature['lfForm_id'])
        )

        fields = [self._tableLfForm['code'].name(), self._tableLfForm['name'].name()]

        cond = self._tableNomenclature['id'].eq(nomenclatureId)

        record = QtGui.qApp.db.getRecordEx(queryTable, fields, cond)
        if not record:
            return ''

        return u'{0}-{1}'.format(
            forceString(record.value('code')),
            forceString(record.value('name'))
        )


    def setDefaultClassId(self, classId):
        self.defaultClassId = classId


    def setDefaultKindId(self, kindId):
        self.defaultKindId = kindId


    def setDefaultTypeId(self, typeId):
        self.defaultTypeId = typeId


    def createEditor(self, parent):
        editor = CNomenclatureComboBox(parent)
        editor.setIsOnlyMnnEsklpFormVisible(self.isOnlyMnnEsklpFormVisible)
        editor.setOnlyNomenclature(True)
        editor.setOnlySmnn(self._onlySmnn)
        editor.setShowFields(self.showFields)
        editor.setPreferredWidth(self.preferredWidth)
        editor.setDefaultIds(self.defaultClassId, self.defaultKindId, self.defaultTypeId)
        editor.setOrgStructureId(self._stockOrgStructureId)
        editor.setNomenclatureActiveSubstanceId(self._activeSubstanceId)
        editor.setLfFormId(self._lfFormId)
        editor.setNomenclatureSmnnUUID(self._smnnUUID)
        editor.setNomenclatureSmnnName(self._smnnName)
        editor.setFindNomenclatureName(self._findNomenclatureName)
        return editor


class CNomenclatureComboBoxPopup(Ui_NomenclatureComboBoxPopup,
                                 QtGui.QFrame,
                                 CConstructHelperMixin
                                ):
    __pyqtSignals__ = ('itemsUpdated()',
                       'itemSelected(QVariant)',
                       'applySearch(QVariant)'  # WTF?
                      )

    def __init__(self, parent=None, useClientUnitId=False, defaultFinanceId=None, defaultMedicalAidKindId=None, needInternationalNonproprietaryName=False):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self._parent = parent
        self.addModels('', CNomenclatureModel(self, useClientUnitId, defaultFinanceId, defaultMedicalAidKindId, needInternationalNonproprietaryName=needInternationalNonproprietaryName))
        self.addModels('NomenclatureSortModel', CSortFilterProxyTableModel(self, self.model))
        self.model = self.modelNomenclatureSortModel.sourceModel()
        self.modelFeatures = CFeaturesModel(self)
        self.addObject('actSelect', QtGui.QAction(self))
        self.addObject('actEdit',   QtGui.QAction(u'Редактировать', self))
        self.addObject('actSearch', QtGui.QAction(self))
        self.setupUi(self)
        self.setModels(self.tblNomenclature, self.modelNomenclatureSortModel, self.selectionModelNomenclatureSortModel)
        self.tabNomenclature.addAction(self.actSelect)
        self.actSelect.setShortcuts([Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select])
        self.tblNomenclature.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.tblNomenclature.addAction(self.actEdit)
        self.tblNomenclature.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.actSearch.setShortcuts([Qt.Key_Return, Qt.Key_Enter])
        self.tabSearch.addAction(self.actSearch)
        self.cmbClass.setTable('rbNomenclatureClass', True)
        self.cmbKind.setTable('rbNomenclatureKind', True)
        self.cmbType.setTable('rbNomenclatureType', True)
        self.cmbLfForm.setTable('rbLfForm', True)
        self.cmbFinance.setTable('rbFinance', True)
        self.cmbMedicalAidKind.setTable('rbMedicalAidKind', True)
        self.tblFeatures.setItemDelegate(CFeatureItemDelegate(self))
        self.tblFeatures.setModel(self.modelFeatures)
        self.tblFeatures.addPopupSelectAllRow()
        self.tblFeatures.addPopupClearSelectionRow()
        self.tblFeatures.addPopupSeparator()
        self.tblFeatures.addPopupDelRow()
        self.findNomenclatureName = u''
        self._additionalCond = u''
        self._defaultClassId = None
        self._defaultKindId = None
        self._defaultTypeId = None
        self._defaultOnlyExists = False
        self._defaultFinanceId = defaultFinanceId
        self._defaultMedicalAidKindId = defaultMedicalAidKindId
        self._onlyExists = False
        self._OnlyLs = False
        self._onlyNomenclature = False
        self._onlySmnn = False
        self._stockOrgStructureId = None
        self._nomenclatureId = None
        self._activeSubstanceId = None
        self._defaultActiveSubstanceId = None
        self._smnnUUID = None
        self._lfFormId = None
        self._defaultSmnnUUID = None
        self._defaultSmnnName = ''
        self._defaultFeatures = []
        self._defaultIsOnlyMnnEsklpForm = False
        # я не хочу загружать features на каждое изменение class/kind/type, поэтому
        # ввёл флаг: features в modelFeatures достоверен или нет
        self._featuresIsValid = True
        self.initSearch()
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CNomenclatureComboBoxPopup', {})
        self.tblNomenclature.loadPreferences(preferences)
        self.tblNomenclature.enableColsHide()
        self.tblNomenclature.enableColsMove()
        self.isFinanceVisible = 0 # 0-как обычно, 1-не показывать, 2-показывать #0013272
        self.tblNomenclature.horizontalHeader().setSortIndicatorShown(True)
        self.tblNomenclature.horizontalHeader().sectionClicked.connect(self.setOrder)
        self.chkOnlyLs.setChecked(forceBool(QtGui.qApp.preferences.appPrefs.get('isShowOnlyLsInFilterNomenklature', QVariant())))
        self.setIsOnlyMnnEsklpFormVisible(False)


    def setOrder(self, column):
        self.tblNomenclature.setOrder(column)
        self.model.headerSortingCol = {column: self.tblNomenclature._isDesc}
        self.model.sortDataModel()


    def setAdditionalCond(self, cond):
        self._additionalCond = forceString(cond)


    def setFindNomenclatureName(self, value):
        self.findNomenclatureName = value


    def setOnlySmnn(self, value):
        self._onlySmnn = value


    @pyqtSignature('')
    def on_btnName_clicked(self):
        if self.findNomenclatureName:
           self.edtName.setText(trim(self.findNomenclatureName))


    def setIsFinanceVisible(self, value):
        self.isFinanceVisible = value


    def setIsOnlyMnnEsklpFormVisible(self, value):
        self.isOnlyMnnEsklpFormVisible = value
        self.chkOnlyMnnEsklpForm.setVisible(self.isOnlyMnnEsklpFormVisible)


    def setNomenclatureActiveSubstanceId(self, activeSubstanceId):
        self._defaultActiveSubstanceId = activeSubstanceId
        self._activeSubstanceId = activeSubstanceId


    def setNomenclatureSmnnUUID(self, smnnUUID):
        self._defaultSmnnUUID = smnnUUID
        self._smnnUUID = smnnUUID


    def setNomenclatureSmnnName(self, smnnName):
        self._defaultSmnnName = smnnName
        self.edtMnnFilter.setText(self._defaultSmnnName)


    def setLfFormId(self, lfFormId):
        self._lfFormId = lfFormId
        self.cmbLfForm.setValue(self._lfFormId)


    def setStockOrgStructureId(self, orgStructureId):
        self._stockOrgStructureId = orgStructureId
        self.model.setStockOrgStructureId(self._stockOrgStructureId)


    def setDefaultIds(self, classId, kindId, typeId):
        self._defaultClassId = classId
        self._defaultKindId = kindId
        self._defaultTypeId = typeId


    def setDefaultFeatures(self, features):
        self._defaultFeatures = features


    def setOnlyExists(self, value=True):
        self.chkOnlyExists.setChecked(value)
        self._defaultOnlyExists = value
        self.model.setOnlyExists(self.chkOnlyExists.isChecked())


    def setOnlyNomenclature(self, value=False):
        self._onlyNomenclature = value


    def setOnlyExistsEnabled(self, value=True):
        self.chkOnlyExists.setEnabled(value)


    def setFinanceId(self, value=None):
        self.cmbFinance.setValue(value)
        self._defaultFinanceId = value
        self.model.setFinanceId(value)


    def setEventMedicalAidKindId(self, value=None):
        self._medicalAidKindId = value
        self.model.setEventMedicalAidKindId(value)


    def setNomenclatureId(self, value=None):
        self._nomenclatureId = value


    def setMainStockId(self, value=None):
        self._mainStockId = value
        self.model.setMainStockId(value)


    def setFinanceEnabled(self, value=True):
        self.lblFinance.setEnabled(value)
        self.cmbFinance.setEnabled(value)


    def setFinanceVisible(self, value=True):
        self.lblFinance.setVisible(value)
        self.cmbFinance.setVisible(value)


    def setMedicalAidKindId(self, value=None):
        self.cmbMedicalAidKind.setValue(value)
        self._defaultMedicalAidKindId = value
        self.model.setMedicalAidKindId(value)


    def setMedicalAidKindEnabled(self, value=True):
        self.cmbMedicalAidKind.setEnabled(value)
        self.lblMedicalAidKind.setEnabled(value)


    def setMedicalAidKindVisible(self, value=True):
        self.lblMedicalAidKind.setVisible(value)
        self.cmbMedicalAidKind.setVisible(value)


    def show(self):
        self.resetSearch()
        self.applySearch()
        self.tabSearchAttributes.setCurrentIndex(0)
        self.tblNomenclature.setFocus()
        QtGui.QFrame.show(self)


    def selectCurrentItem(self):
        row = self.tblNomenclature.currentRow()
        record = self.modelNomenclatureSortModel.getRecordByRow(row)
        id = forceRef(record.value('id'))
        self.hide()
        QtGui.qApp.preferences.appPrefs['NomenclatureComboBoxPopup_isOnlyMnnEsklpForm'] = toVariant(self.chkOnlyMnnEsklpForm.isChecked())
        self.emit(SIGNAL('itemSelected(QVariant)'), toVariant(id))


    def initSearch(self):
        self._classId = self._defaultClassId
        self._kindId = self._defaultKindId
        self._typeId = self._defaultTypeId
        self._financeId = self._defaultFinanceId
        self._activeSubstanceId = self._defaultActiveSubstanceId
        self._smnnUUID = self._defaultSmnnUUID
        self._medicalAidKindId = self._defaultMedicalAidKindId
        self._code = ''
        self._name = ''
        self._producer = ''
        self._ATC = ''
        self._includeAnalogies = False
        self._features = self._defaultFeatures
        self._onlyExists = self._defaultOnlyExists
        self._mnnFilter = self._defaultSmnnName
        self._defaultIsOnlyMnnEsklpForm = forceBool(QtGui.qApp.preferences.appPrefs.get('NomenclatureComboBoxPopup_isOnlyMnnEsklpForm', False))


    def resetSearch(self):
        self.initSearch()
        self.cmbClass.setValue(self._classId)
        self.cmbKind.setValue(self._kindId)
        self.cmbType.setValue(self._typeId)
        self.cmbVEN.setCurrentIndex(0)
        self.cmbLfForm.setValue(self._lfFormId)
        self.cmbFinance.setValue(self._financeId)
        self.chkActiveSubstance.setChecked(bool(self._activeSubstanceId))
        self.cmbActiveSubstance.setValue(self._activeSubstanceId)
        self.cmbMedicalAidKind.setValue(self._medicalAidKindId)
        self.edtCode.setText(self._code)
        self.edtName.setText(self._name)
        self.edtProducer.setText(self._producer)
        self.edtATC.setText(self._ATC)
        self.chkIncludeAnalogies.setChecked(self._includeAnalogies)
        self.chkOnlyExists.setChecked(self._onlyExists)
        self.edtMnnFilter.setText(self._mnnFilter)
        self.chkOnlyMnnEsklpForm.setChecked(self._defaultIsOnlyMnnEsklpForm)
        self._featuresIsValid = False


    @withWaitCursor
    def applySearch(self):
        itemId = self._parent.value()
        if not itemId and self._nomenclatureId:
            itemId = self._nomenclatureId
        self._classId = self.cmbClass.value()
        self._kindId = self.cmbKind.value()
        self._typeId = self.cmbType.value()
        self._VEN = self.cmbVEN.currentIndex()
        self._lfFormId = self.cmbLfForm.value()
        self._financeId = self.cmbFinance.value()
        self._activeSubstanceId = self.cmbActiveSubstance.value() if self.chkActiveSubstance.isChecked() else None
        self._medicalAidKindId = self.cmbMedicalAidKind.value()
        self._code = forceStringEx(self.edtCode.text())
        self._name = forceStringEx(self.edtName.text())
        self._producer = forceStringEx(self.edtProducer.text())
        self._ATC = forceStringEx(self.edtATC.text())
        self._includeAnalogies = self.chkIncludeAnalogies.isChecked()
        self._mnnFilter = forceStringEx(self.edtMnnFilter.text())
        isOnlyMnnEsklpForm = self.chkOnlyMnnEsklpForm.isChecked() if self.isOnlyMnnEsklpFormVisible else False

        if self._features or self._defaultFeatures:
            if not self._featuresIsValid:
                self.modelFeatures.prepareList(self._classId, self._kindId, self._typeId)
                self.modelFeatures.setValuableFeatures(self._features)
                self._featuresIsValid = True
            self._features = self.modelFeatures.getValuableFeatures()
        else:
            self._features = []
        self._onlyExists = self.chkOnlyExists.isChecked()
        self._OnlyLs = self.chkOnlyLs.isChecked()
        self.model.setOnlyExists(self._onlyExists)

        db = QtGui.qApp.db
        activeSubstanceIdList = []
        smnnIdList = []
        tableNomenclature = db.table('rbNomenclature')
        tableType = db.table('rbNomenclatureType')
        table = tableNomenclature
        hasJoinNomenclaturetype = False
        if self._activeSubstanceId:
            tableNomenclatureComposition = db.table('rbNomenclature_Composition')
            queryTableComposition = tableNomenclature.innerJoin(tableNomenclatureComposition, tableNomenclatureComposition['master_id'].eq(tableNomenclature['id']))
            activeSubstanceCond = [tableNomenclatureComposition['activeSubstance_id'].eq(self._activeSubstanceId)]
            activeSubstanceIdList = db.getDistinctIdList(queryTableComposition, tableNomenclature['id'].name(), activeSubstanceCond)
        if isOnlyMnnEsklpForm:
            cond = []
            if self._mnnFilter:
                tableEsklp_Smnn = db.table('esklp.Smnn')
                tableNC = db.table('rbNomenclature')
                tableESKLP_Klp = db.table('esklp.Klp')
                queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
                queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
                cond.append(tableEsklp_Smnn['mnn'].eq(self._mnnFilter))
                if self._lfFormId:
                    tableLfForm= db.table('rbLfForm')
                    tableEsklp_SmnnGrlsLf = db.table('esklp.Smnn_GrlsLf')
                    lfFormRecord = db.getRecordEx(tableLfForm, [tableLfForm['name']], [tableLfForm['id'].eq(self._lfFormId)])
                    lfFormName = forceStringEx(lfFormRecord.value('name')) if lfFormRecord else ''
                    queryTable = queryTable.innerJoin(tableEsklp_SmnnGrlsLf, tableEsklp_SmnnGrlsLf['master_id'].eq(tableEsklp_Smnn['id']))
                    queryTable = queryTable.innerJoin(tableLfForm, db.joinAnd([tableLfForm['name'].eq(tableEsklp_SmnnGrlsLf['lf_name']), tableLfForm['dosage'].eq(tableEsklp_SmnnGrlsLf['dosage_name'])]))
                    cond.append(tableLfForm['isESKLP'].eq(1))
                    cond.append(tableLfForm['name'].eq(lfFormName))
                    cond.append(tableLfForm['name'].eq(tableESKLP_Klp['lf_norm_name']))
                    cond.append(tableNC['lfForm_id'].eq(tableLfForm['id']))
                smnnIdList = db.getDistinctIdList(queryTable, [tableNC['id']], cond)
        elif self._smnnUUID:
            tableEsklp_Smnn = db.table('esklp.Smnn')
            tableNC = db.table('rbNomenclature')
            tableESKLP_Klp = db.table('esklp.Klp')
            queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
            queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
            cond = [tableEsklp_Smnn['UUID'].eq(self._smnnUUID)]
            tableLfForm= db.table('rbLfForm')
            tableEsklp_SmnnGrlsLf = db.table('esklp.Smnn_GrlsLf')
            if self._lfFormId:
                queryTable = queryTable.innerJoin(tableEsklp_SmnnGrlsLf, tableEsklp_SmnnGrlsLf['master_id'].eq(tableEsklp_Smnn['id']))
                queryTable = queryTable.innerJoin(tableLfForm, db.joinAnd([tableLfForm['name'].eq(tableEsklp_SmnnGrlsLf['lf_name']), tableLfForm['dosage'].eq(tableEsklp_SmnnGrlsLf['dosage_name'])]))
                cond.append(tableLfForm['isESKLP'].eq(1))
                cond.append(tableLfForm['name'].eq(tableESKLP_Klp['lf_norm_name']))
                cond.append(tableLfForm['id'].eq(self._lfFormId))
                cond.append(tableNC['lfForm_id'].eq(tableLfForm['id']))
                cond.append(tableLfForm['dosage'].eq(tableESKLP_Klp['dosage_norm_name']))
            else:
                queryTable = queryTable.innerJoin(tableEsklp_SmnnGrlsLf, tableEsklp_SmnnGrlsLf['master_id'].eq(tableEsklp_Smnn['id']))
                queryTable = queryTable.innerJoin(tableLfForm, db.joinAnd([tableLfForm['name'].eq(tableEsklp_SmnnGrlsLf['lf_name']), tableLfForm['dosage'].eq(tableEsklp_SmnnGrlsLf['dosage_name'])]))
                cond.append(tableLfForm['isESKLP'].eq(1))
                cond.append(tableLfForm['name'].eq(tableESKLP_Klp['lf_norm_name']))
                cond.append(tableNC['lfForm_id'].eq(tableLfForm['id']))
                cond.append(tableLfForm['dosage'].eq(tableESKLP_Klp['dosage_norm_name']))
            smnnIdList = db.getDistinctIdList(queryTable, [tableNC['id']], cond)
        elif self._lfFormId:
            tableEsklp_Smnn = db.table('esklp.Smnn')
            tableNC = db.table('rbNomenclature')
            tableESKLP_Klp = db.table('esklp.Klp')
            tableLfForm= db.table('rbLfForm')
            tableEsklp_SmnnGrlsLf = db.table('esklp.Smnn_GrlsLf')
            queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
            queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
            queryTable = queryTable.innerJoin(tableEsklp_SmnnGrlsLf, tableEsklp_SmnnGrlsLf['master_id'].eq(tableEsklp_Smnn['id']))
            queryTable = queryTable.innerJoin(tableLfForm, db.joinAnd([tableLfForm['name'].eq(tableEsklp_SmnnGrlsLf['lf_name']), tableLfForm['dosage'].eq(tableEsklp_SmnnGrlsLf['dosage_name'])]))
            cond = [tableLfForm['isESKLP'].eq(1),
                    tableLfForm['name'].eq(tableESKLP_Klp['lf_norm_name'])
                   ]
            cond.append(tableLfForm['id'].eq(self._lfFormId))
            cond.append(tableNC['lfForm_id'].eq(tableLfForm['id']))
            cond.append(tableLfForm['dosage'].eq(tableESKLP_Klp['dosage_norm_name']))
            smnnIdList = db.getDistinctIdList(queryTable, [tableNC['id']], cond)
        if isOnlyMnnEsklpForm and not smnnIdList:
            idList = []
        elif self._onlySmnn and (self._smnnUUID or self._lfFormId) and not smnnIdList:
            idList = []
        else:
            cond = []
            cond.append(db.joinOr([tableNomenclature['exDate'].ge(QDate().currentDate()), tableNomenclature['exDate'].isNull()]))
            activeSubstanceIdList = list(set(activeSubstanceIdList)|set(smnnIdList))
            if activeSubstanceIdList:
                cond.append(tableNomenclature['id'].inlist(activeSubstanceIdList))
            if self._typeId:
                cond.append(tableNomenclature['type_id'].eq(self._typeId))
            elif self._kindId or self._classId:
                table = table.innerJoin(tableType, tableType['id'].eq(tableNomenclature['type_id']))
                hasJoinNomenclaturetype = True
                if self._kindId:
                    cond.append(tableType['kind_id'].eq(self._kindId))
                else:
                    tableKind = db.table('rbNomenclatureKind')
                    table = table.innerJoin(tableKind, tableKind['id'].eq(tableType['kind_id']))
                    cond.append(tableKind['class_id'].eq(self._classId))
    #        if self._lfFormId:
    #            cond.append(tableNomenclature['lfForm_id'].eq(self._lfFormId))
            if self._VEN:
                cond.append(tableNomenclature['VEN'].eq(self._VEN))
            if self._code:
                cond.append(tableNomenclature['code'].like(self._code))
            if self._name:
                cond.append(
                            db.joinOr([
                                        tableNomenclature['name'].contain(self._name),
                                        tableNomenclature['originName'].contain(self._name),
                                      ])
                           )
            if self._producer:
                cond.append(tableNomenclature['producer'].like(self._producer))
            if self._ATC:
                cond.append(tableNomenclature['ATC'].like(self._ATC))
            if self._mnnFilter:
                cond.append(
                            db.joinOr([
                                        tableNomenclature['mnnLatin'].contain(self._mnnFilter),
                                        tableNomenclature['internationalNonproprietaryName'].contain(self._mnnFilter),
                                      ])
                           )

            if self._includeAnalogies and cond:
                tableTarget = db.table('rbNomenclature').alias('A')
                table = table.innerJoin(tableTarget,
                                       db.joinOr([
                                           db.joinAnd( [tableTarget['analog_id'].isNotNull(),
                                                        tableTarget['analog_id'].eq(tableNomenclature['analog_id'])] ),
                                           db.joinAnd( [tableTarget['analog_id'].isNull(),
                                                        tableTarget['id'].eq(tableNomenclature['id'])] )
                                                  ]))
    #        else:
    #            tableTarget = tableNomenclature
            if self._features:
                cnt = 0
                for name, value in self._features:
                    tableFeature = db.table('rbNomenclature_Feature').alias('F%d' % cnt)
                    table = table.innerJoin(tableFeature, tableFeature['master_id'].eq(tableNomenclature['id']))
                    cond.append(tableFeature['name'].eq(name))
                    cond.append(tableFeature['value'].eq(value))
                    cnt += 1
            if self._onlyExists:
                existsIdList = getExistsNomenclatureIdList(self._stockOrgStructureId, self._financeId, self._medicalAidKindId, nomenclatureIdList = activeSubstanceIdList, isFinanceComboBoxFilter = bool(self.isFinanceVisible))
                cond.append(tableNomenclature['id'].inlist(existsIdList))
            if self._OnlyLs:
                if not hasJoinNomenclaturetype:
                    table = table.innerJoin(tableType, tableType['id'].eq(tableNomenclature['type_id']))
                cond.append(tableType['code'].eq('ls'))
            elif not self._onlyNomenclature:
                existsIdList = getExistsNomenclatureIdList(self._stockOrgStructureId, self._financeId, self._medicalAidKindId, otherHaving = [u'qnt>0'], nomenclatureIdList = activeSubstanceIdList, isFinanceComboBoxFilter = bool(self.isFinanceVisible))
                cond.append(tableNomenclature['id'].inlist(existsIdList))
            if self._additionalCond:
                cond.append(self._additionalCond)
            # сортировка по сохранённому столбцу
            self.tblNomenclature._isDesc = not forceBool(QtGui.qApp.preferences.appPrefs.get('NomenclatureComboBoxPopup_isDescOrder', True))
            self.tblNomenclature._orderColumn = forceInt(QtGui.qApp.preferences.appPrefs.get('NomenclatureComboBoxPopup_ColumnOrder', 1))
            self.tblNomenclature.setOrder(self.tblNomenclature._orderColumn)
            if self.tblNomenclature._order:
                self.model.headerSortingCol = {self.tblNomenclature._orderColumn: self.tblNomenclature._isDesc}
                order = self.tblNomenclature._order
            else:
                order = [tableNomenclature['name'].name(), tableNomenclature['code'].name()]
            idList = db.getDistinctIdList(table, tableNomenclature['id'].name(), cond, order)
        if self._financeId:
            self.model.setFinanceId(self._financeId)
        else:
            self.model.setFinanceId(None)
        if self._medicalAidKindId:
            self.model.setMedicalAidKindId(self._medicalAidKindId)
            self.model.setMedicalAidKindId(None)
        self.tblNomenclature.setIdList(idList, itemId)
        if idList:
            self.tabWidget.setCurrentIndex(0)
            self.tabWidget.setTabEnabled(0, True)
            self.tblNomenclature.setFocus(Qt.OtherFocusReason)
        else:
            self.tabWidget.setCurrentIndex(1)
            self.tabWidget.setTabEnabled(0, False)
            self.tabSearchAttributes.setCurrentIndex(0)
            self.cmbClass.setFocus(Qt.OtherFocusReason)
        if itemId:
            index = self.tblNomenclature.model().findItemIdIndex(itemId)
            if index >= 0:
                self.tblNomenclature.selectRow(index)
        self.emit(SIGNAL('applySearch(QVariant)'), toVariant(itemId))


    def editOrCreateNomenclature(self, nomenclatureId):
        from RefBooks.Nomenclature.List import CRBNomenclatureEditor
        dialog = CRBNomenclatureEditor(self)
        try:
            dialog.load(nomenclatureId)
            if dialog.exec_():
                nomenclatureId = dialog.itemId()
                self.hide()
                self.emit(SIGNAL('itemsUpdated()'))
                self.emit(SIGNAL('itemSelected(QVariant)'), toVariant(nomenclatureId))
        finally:
            dialog.deleteLater()


    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        if index == 2:
            self.editOrCreateNomenclature(None)


    @pyqtSignature('')
    def on_actEdit_triggered(self):
        nomenclatureId = self.tblNomenclature.currentItemId()
        if nomenclatureId:
            self.editOrCreateNomenclature( nomenclatureId)


    @pyqtSignature('')
    def on_actSelect_triggered(self):
        self.selectCurrentItem()


    @pyqtSignature('QModelIndex')
    def on_tblNomenclature_clicked(self, index):
        self.selectCurrentItem()


    @pyqtSignature('')
    def on_actSearch_triggered(self):
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).animateClick()


    @pyqtSignature('int')
    def on_tabSearchAttributes_currentChanged(self, index):
        if index == 1:
            self.modelFeatures.prepareList(self.cmbClass.value(), self.cmbKind.value(), self.cmbType.value())
            self.modelFeatures.setValuableFeatures(self._features)
            self._featuresIsValid = True # пользователь видел, значит всё ок


    @pyqtSignature('int')
    def on_cmbClass_currentIndexChanged(self, index):
        classId = self.cmbClass.value()
        if classId:
            table = QtGui.qApp.db.table('rbNomenclatureKind')
            self.cmbKind.setFilter(table['class_id'].eq(classId))
        else:
            self.cmbKind.setFilter('')
        self._featuresIsValid = False # пользователь не видел, значит нужно будет перезагрузить


    @pyqtSignature('int')
    def on_cmbKind_currentIndexChanged(self, index):
        kindId = self.cmbKind.value()
        if kindId:
            table = QtGui.qApp.db.table('rbNomenclatureType')
            self.cmbType.setFilter(table['kind_id'].eq(kindId))
        else:
            self.cmbType.setFilter('')
        self._featuresIsValid = False


    @pyqtSignature('int')
    def on_cmbActiveSubstance_currentIndexChanged(self, index):
        self.chkActiveSubstance.setChecked(bool(self.cmbActiveSubstance.value()))


    @pyqtSignature('bool')
    def on_chkOnlyExists_toggled(self, value):
        self._parent.setOnlyExists(value)
        self.setOnlyExists(value)
        self._parent.getFilterData()
        self._parent.setFilter(self._parent._filter)


    @pyqtSignature('bool')
    def on_chkOnlyMnnEsklpForm_toggled(self, value):
        QtGui.qApp.preferences.appPrefs['NomenclatureComboBoxPopup_isOnlyMnnEsklpForm'] = toVariant(self.chkOnlyMnnEsklpForm.isChecked())
        self._parent.getFilterData()
        self._parent.setFilter(self._parent._filter)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.applySearch()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetSearch()
        self._featuresIsValid = False


    def closeEvent(self, event):
        preferences = self.tblNomenclature.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CNomenclatureComboBoxPopup', preferences)
        colKeys = self.model.headerSortingCol.keys()
        colKeys.sort()
        QtGui.qApp.preferences.appPrefs['NomenclatureComboBoxPopup_ColumnOrder'] = toVariant(colKeys[0] if len(colKeys) >= 1 else 1)
        QtGui.qApp.preferences.appPrefs['NomenclatureComboBoxPopup_isDescOrder'] = toVariant(self.tblNomenclature._isDesc)
        QtGui.qApp.preferences.appPrefs['NomenclatureComboBoxPopup_isOnlyMnnEsklpForm'] = toVariant(self.chkOnlyMnnEsklpForm.isChecked())
        QtGui.QFrame.closeEvent(self, event)


class CNomenclatureModel(CTableModel):
    class CQntCol(CTextCol):
        def __init__(self, useClientUnitId, financeId, medicalAidKindId=None):
            CTextCol.__init__(self, u'Остаток', ['id'], 10)
            self.useClientUnitId = useClientUnitId
            self.financeId = financeId
            self.medicalAidKindId = medicalAidKindId
            self._cacheClientUnitId = {}
            self._cache = {}
            self.stockOrgStructureId = None
            self.isOnlyExists = False

        def setOnlyExists(self, value):
            if value != self.isOnlyExists:
                self._cache = {}
            self.isOnlyExists = value

        def getValue(self, values):
            nomenclatureId = forceRef(values[0])
            if (nomenclatureId, self.financeId, self.medicalAidKindId, self.stockOrgStructureId) in self._cache:
                return forceStringEx(self._cache[nomenclatureId, self.financeId, self.medicalAidKindId, self.stockOrgStructureId] )
            return  forceStringEx(None)

        def setFinanceId(self, value):
            self.financeId = value

        def setMedicalAidKindId(self, value):
            self.medicalAidKindId = value

        def setStockOrgStructureId(self, stockOrgStructureId):
            self.stockOrgStructureId = stockOrgStructureId

        def format(self, values):
            nomenclatureId = forceRef(values[0])
            if (nomenclatureId, self.financeId, self.medicalAidKindId, self.stockOrgStructureId) not in self._cache:
                unitId = self._getUnitId(nomenclatureId)
                if self.medicalAidKindId and QtGui.qApp.controlSMFinance() != 0:
                    self._cache[nomenclatureId, self.financeId, self.medicalAidKindId, self.stockOrgStructureId] = getExistsNomenclatureAmountSum(nomenclatureId, unitId=unitId, financeId = self.financeId, orgStructureId=self.stockOrgStructureId, medicalAidKindId = self.medicalAidKindId, otherHaving = ['`qnt` > 0.0001 and ((shelfTime>=curDate()) OR shelfTime is NULL)'] if self.isOnlyExists else [u'1'])
                else:
                    self._cache[nomenclatureId, self.financeId, self.medicalAidKindId, self.stockOrgStructureId] = getExistsNomenclatureAmountSum(nomenclatureId, unitId=unitId, financeId = self.financeId, orgStructureId=self.stockOrgStructureId, otherHaving = ['`qnt` > 0.0001 and ((shelfTime>=curDate()) OR shelfTime is NULL)'] if self.isOnlyExists else [u'1'])
            return QVariant(self._cache[nomenclatureId, self.financeId, self.medicalAidKindId, self.stockOrgStructureId])

        def _getUnitId(self, nomenclatureId):
            if not self.useClientUnitId:
                return None

            if nomenclatureId not in self._cacheClientUnitId:

                unitId = forceRef(
                    QtGui.qApp.db.translate('rbNomenclature', 'id', nomenclatureId, 'defaultClientUnit_id')
                )
                self._cacheClientUnitId[nomenclatureId] = unitId

            return self._cacheClientUnitId[nomenclatureId]

    class CMainStockQntCol(CQntCol):
        def __init__(self, useClientUnitId, financeId, medicalAidKindId=None):
            CTextCol.__init__(self, u'Остаток основного склада', ['id'], 10)
            self.useClientUnitId = useClientUnitId
            self.financeId = financeId
            self.medicalAidKindId = medicalAidKindId
            self._cacheClientUnitId = {}
            self._cache = {}
            self.mainStockId = None
            self.isOnlyExists = False

        def setOnlyExists(self, value):
            if value != self.isOnlyExists:
                self._cache = {}
            self.isOnlyExists = value

        def format(self, values):
            nomenclatureId = forceRef(values[0])
            if (nomenclatureId, self.financeId, self.medicalAidKindId) not in self._cache:
                unitId = self._getUnitId(nomenclatureId)
                if self.medicalAidKindId and QtGui.qApp.controlSMFinance() != 0:
                    self._cache[nomenclatureId, self.financeId, self.medicalAidKindId] = getExistsNomenclatureAmountSum(nomenclatureId, unitId=unitId, financeId = self.financeId, orgStructureId=self.mainStockId, medicalAidKindId = self.medicalAidKindId, otherHaving = ['`qnt` > 0.0001 and ((shelfTime>=curDate()) OR shelfTime is NULL)'] if self.isOnlyExists else [u'1'])
                else:
                    self._cache[nomenclatureId, self.financeId, self.medicalAidKindId] = getExistsNomenclatureAmountSum(nomenclatureId, unitId=unitId, financeId = self.financeId, orgStructureId=self.mainStockId, otherHaving = ['`qnt` > 0.0001 and ((shelfTime>=curDate()) OR shelfTime is NULL)'] if self.isOnlyExists else [u'1'])
            return QVariant(self._cache[nomenclatureId, self.financeId, self.medicalAidKindId])

        def setMainStockId(self, mainStockId):
            self.mainStockId = mainStockId

    def __init__(self, parent, useClientUnitId=False, financeId=None, medicalAidKindId=None, mainStockId=None, needInternationalNonproprietaryName=False):
        self.isOnlyExists = False
        self.qntCol = CNomenclatureModel.CQntCol(useClientUnitId, financeId, medicalAidKindId)
        self.mainStockQntCol = CNomenclatureModel.CMainStockQntCol(useClientUnitId, financeId, medicalAidKindId)
        showMainStockRemainings = forceBool(QtGui.qApp.preferences.appPrefs.get('showMainStockRemainings', QVariant()))
        cols = [
            CTextCol(     u'Код',             ['code'],      10),
            CTextCol(     u'Наименование',    ['name'],      60),
            CTextCol(     u'МНН на латыни',   ['mnnLatin'],  20),
            CTextCol(     u'Дозировка',       ['dosageValue'], 20),
            CRefBookCol(  u'Форма выпуска',   ['lfForm_id'], 'rbLfForm', 15, CRBComboBox.showName),
            CTextCol(     u'Дата включения',  ['inDate'],   20),
            CTextCol(     u'Дата исключения', ['exDate'],   20),
            CTextCol(     u'Производитель',   ['producer'],  20),
            self.qntCol,
            ]
        if showMainStockRemainings:
            cols.append(self.mainStockQntCol)
        if needInternationalNonproprietaryName:
            cols.insert(2, CTextCol(u'МНН на русском', ['internationalNonproprietaryName'], 20))
        CTableModel.__init__(self, parent, cols, 'rbNomenclature' )
        self._mapColumnToOrder = {
            'code': 'rbNomenclature.code',
            'name': 'rbNomenclature.name',
            'internationalNonproprietaryName': 'rbNomenclature.internationalNonproprietaryName',
            'mnnLatin': 'rbNomenclature.mnnLatin',
            'dosageValue': 'rbNomenclature.dosageValue',
            'lfForm_id': 'rbNomenclature.lfForm_id',
            'inDate': 'rbNomenclature.inDate',
            'exDate': 'rbNomenclature.exDate',
            'producer': 'rbNomenclature.producer',
            'id': 'rbNomenclature.id',
        }


    def sortDataModel(self):
        for col, value in self.headerSortingCol.items():
            if self.cols()[col].fields()[0] == u'id':
                self.alfNumKey_sort(key=lambda recordId: self.getRecordValueByIdCol(col, recordId), reverse=value)
            else:
                self.idList().sort(key=lambda recordId: self.getRecordValueByIdCol(col, recordId), reverse=value)
        self.reset()


    def alfNumKey_sort(self, key=lambda s:s, reverse=True):
        def getNumKeyFunc(key):
            convert = lambda text: int(text) if text.isdigit() else text
            return lambda s: [convert(c) for c in re.split('([0-9]+)', unicode(key(s)) if isinstance(key(s), (QString, str)) else key(s))] if isinstance(key(s), (QString, str, unicode)) else key(s)
        sort_key = getNumKeyFunc(key)
        self.idList().sort(key=sort_key, reverse=reverse)


    def setFinanceId(self, value):
        self.qntCol.setFinanceId(value)
        self.emitDataChanged()


    def setMedicalAidKindId(self, value):
        self.qntCol.setMedicalAidKindId(value)
        self.emitDataChanged()


    def setEventMedicalAidKindId(self, value):
        self.medicalAidKindId = value
        self.qntCol.setMedicalAidKindId(value)
        self.emitDataChanged()


    def setMainStockId(self, value):
        self.mainStockId = value
        self.mainStockQntCol.setMainStockId(value)
        self.emitDataChanged()


    def setStockOrgStructureId(self, value):
        self.stockOrgStructureId = value
        self.qntCol.setStockOrgStructureId(value)
        self.emitDataChanged()


    def setOnlyExists(self, value):
        self.isOnlyExists = value
        self.qntCol.setOnlyExists(value)
        self.mainStockQntCol.setOnlyExists(value)


class CFeatureItemDelegate(CLocItemDelegate):
    def createEditor(self, parent, option, index):
        column = index.column()
        editor = index.model().createEditor(column, index.row(), parent)
        self.connect(editor, SIGNAL('commit()'), self.emitCommitData)
        self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)

        self.editor   = editor
        self.row      = index.row()
        self.rowcount = index.model().rowCount(None)
        self.column   = column
        return editor


class CFeatureEditor(CSelectStrInDocTableCol):
    def toString(self, val, record):
        return val


class CFeaturesModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.colName  = self.addExtCol(CFeatureEditor(u'Наименование',  'name', 20, []), QVariant.String)
        self.colValue = self.addExtCol(CFeatureEditor(u'Значение',  'value', 20, []), QVariant.String)
        self.setEnableAppendLine(True)
        self.actualValues = {}


    def getEmptyRecord(self):
        record = CRecordListModel.getEmptyRecord(self)
        record.append(QtSql.QSqlField('name', QVariant.String))
        record.append(QtSql.QSqlField('value', QVariant.String))
        return record


    def prepareList(self, classId, kindId, typeId):
        self.actualValues = getFeaturesAndValues(classId, kindId, typeId)


    def createEditor(self, column, row, parent):
        if column == 0:
            names = self.actualValues.keys()
            names.sort()
            self.colName.values = names
            return self.colName.createEditor(parent)
        else:
            name = forceString(self.value(row, 'name') or '')
            self.colValue.values = self.actualValues.get(name, [])
            return self.colValue.createEditor(parent)


    def setEmptyFeatures(self):
        items = []
        names = self.actualValues.keys()
        names.sort()
        for name in names:
            if name in self.actualValues:
                item = self.getEmptyRecord()
                item.setValue('name', name)
                item.setValue('value', '')
                items.append(item)
        self.setItems(items)


    def setValuableFeatures(self, features):
        items = []
        for name, value in features:
            if name in self.actualValues:
                item = self.getEmptyRecord()
                item.setValue('name', name)
                item.setValue('value', value)
                items.append(item)
        self.setItems(items)


    def getValuableFeatures(self):
        result = []
        for item in self.items():
            name = forceString(item.value('name'))
            value = forceString(item.value('value'))
            if value:
                result.append((name, value))
        return result


def getFeaturesAndValues(classId = 0, kindId = 0, typeId = 0, nomenclatureId = 0):
    db = QtGui.qApp.db
    cond = []
    tableNomenclature = db.table('rbNomenclature')
    table = tableNomenclature

    if nomenclatureId:
        cond.append(tableNomenclature['id'].eq(nomenclatureId))
    elif typeId:
        cond.append(tableNomenclature['type_id'].eq(typeId))
    elif kindId or classId:
        tableType = db.table('rbNomenclatureType')
        table = table.innerJoin(tableType, tableType['id'].eq(tableNomenclature['type_id']))
        if kindId:
            cond.append(tableType['kind_id'].eq(kindId))
        else:
            tableKind = db.table('rbNomenclatureKind')
            table = table.innerJoin(tableKind, tableKind['id'].eq(tableType['kind_id']))
            cond.append(tableKind['class_id'].eq(classId))

    tableFeature = db.table('rbNomenclature_Feature')
    table = table.innerJoin(tableFeature, tableFeature['master_id'].eq(tableNomenclature['id']))

    stmt = db.selectDistinctStmt(table, [tableFeature['name'], tableFeature['value']], cond, 'idx')
    query = db.query(stmt)
    result = CSortedDict()
    while query.next():
        name  = forceString(query.value(0))
        value = forceString(query.value(1))
        result.setdefault(name, []).append(value)
    for name, value in result.iteritems():
        value.sort()
    return result
        #print d



class CNomenclatureActionPropertyComboBox(CNomenclatureComboBox):
    def __init__(self, parent):
        CRBComboBox.__init__(self, parent)
        itemId = self.value() #Хранить в самом комбобоксе все значения не имеет смысла
        if itemId:            #так как во всплывающем окне мы делаем запрос заново
            self._filter = u'id in ({})'.format(itemId)
        else:
            self._filter = u'id is NULL'
        self.setTable('rbNomenclature', filter=self._filter)
        self.defaultClassId = None
        self.defaultKindId = None
        self.defaultTypeId = None
        self.defaultFeatures = []
        self._popup = None
        self._stockOrgStructureId = None
        self._onlyExists = False
        self._onlyNomenclature = False
        self._useClientUnitId = False
        self._financeId = None
        self._medicalAidKindId = None
        self._activeSubstanceId = None
        self._mainStockId = self.getMainStockId() if forceBool(QtGui.qApp.preferences.appPrefs.get('showMainStockRemainings', QVariant())) else None
        self.isFinanceVisible = 0 # 0-как обычно, 1-не показывать, 2-показывать #0013272
        
        
    def getFilterData(self):
        itemId = self.value() #Хранить в самом комбобоксе все значения не имеет смысла
        if itemId:            #так как во всплывающем окне мы делаем запрос заново
            self._filter = 'id in ({})'.format(itemId)
        else:
            self._filter = 'id is NULL'
    
    def showPopup(self):
        nomenclatureId = self.getValue()
        #if not self._popup: создавать попап заново оказалось быстрее
        self._popup = CNomenclatureComboBoxPopup(self, self._useClientUnitId, self._financeId, self._medicalAidKindId)
        self.connect(self._popup, SIGNAL('itemsUpdated()'), self.updateItems)
        self.connect(self._popup, SIGNAL('itemSelected(QVariant)'), self.setQValue)
        self.connect(self._popup, SIGNAL('applySearch(QVariant)'), self.setFinanceMedicalAidKind)
        self._popup.setDefaultIds(self.defaultClassId, self.defaultKindId, self.defaultTypeId)
        self._popup.setStockOrgStructureId(self._stockOrgStructureId)
        self._popup.setNomenclatureActiveSubstanceId(self._activeSubstanceId)
        self._popup.setOnlyExists(self._onlyExists)
        self._popup.setOnlyNomenclature(self._onlyNomenclature)
        self._popup.setIsFinanceVisible(self.isFinanceVisible)
        if not QtGui.qApp.userHasRight(urAddNewNomenclatureAction):
            self._popup.tabWidget.setTabEnabled(2, False)
        if not QtGui.qApp.userHasRight(urEditChkOnlyExistsNomenclature):
            self._popup.setOnlyExistsEnabled(False)
        if QtGui.qApp.controlSMFinance() == 1:
            self._popup.setFinanceId(self._financeId)
            self._popup.setEventMedicalAidKindId(self._medicalAidKindId)
            if self.isFinanceVisible == 0:
                self._popup.setFinanceEnabled(True)
            else:
                self._popup.setFinanceEnabled(self.isFinanceVisible == 2)
            self._popup.setMedicalAidKindEnabled(True)
        elif QtGui.qApp.controlSMFinance() == 2:
            self._popup.setFinanceId(self._financeId)
            self._popup.setEventMedicalAidKindId(self._medicalAidKindId)
            if self.isFinanceVisible == 0:
                self._popup.setFinanceEnabled(False)
            else:
                self._popup.setFinanceEnabled(self.isFinanceVisible == 2)
            self._popup.setMedicalAidKindEnabled(False)
        elif QtGui.qApp.controlSMFinance() == 0:
            self._popup.setFinanceId(None)
            if self.isFinanceVisible == 0:
                self._popup.setFinanceVisible(False)
                self._popup.setFinanceEnabled(False)
            else:
                self._popup.setFinanceVisible(self.isFinanceVisible == 2)
                self._popup.setFinanceEnabled(self.isFinanceVisible == 2)
            self._popup.setMedicalAidKindVisible(False)
            self._popup.setMedicalAidKindEnabled(False)
            self._popup.setEventMedicalAidKindId(self._medicalAidKindId)
        if nomenclatureId:
            self._popup.setNomenclatureId(nomenclatureId)
        self._popup.setMainStockId(self._mainStockId)
        self._popup.setDefaultFeatures(self.defaultFeatures)
        pos = self.rect().bottomLeft()
        pos = self.mapToGlobal(pos)
        size = self._popup.sizeHint()
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        size.setWidth(screen.width())
        pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
        pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
        self._popup.move(pos)
        self._popup.resize(size)
        self._popup.show()
        self.setValue(nomenclatureId)