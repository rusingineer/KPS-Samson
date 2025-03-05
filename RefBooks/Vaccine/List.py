# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QModelIndex, QRegExp, SIGNAL, pyqtSignature

from library.AgeSelector         import parseAgeSelectorInt
from library.crbcombobox         import CRBModelDataCache
from library.DbComboBox          import CDbModel, CDbComboBox
from library.IdentificationModel import CIdentificationModel, checkIdentification
from library.InDocTable          import CInDocTableCol, CRBInDocTableCol, CInDocTableModel, CLocItemDelegate, CRBSearchInDocTableCol
from library.interchange         import getDoubleBoxValue, getLineEditValue, setDoubleBoxValue, setLineEditValue
from library.ItemsListDialog     import CItemEditorBaseDialog, CItemsListDialog
from library.TableModel          import CTableModel, CDesignationCol, CRefBookCol, CSumDecimalPlaceCol, CTextCol
from library.Utils               import forceRef, forceStringEx, toVariant, forceString, formatRecordsCount


from RefBooks.Tables             import rbCode, rbName

from .Ui_RBVaccineItemList       import Ui_RBVaccineItemList
from .Ui_RBVaccineEditor         import Ui_RBVaccineEditor


class CRBVaccineList(Ui_RBVaccineItemList, CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',              [rbCode], 20),
            CTextCol(u'Наименование',     [rbName], 40),
            CTextCol(u'Региональный код', ['regionalCode'], 20),
            CSumDecimalPlaceCol(u'Доза', ['dose'], 20, decimals=3)
            ], 'rbVaccine', [rbCode, rbName])
        self.tblItems.addPopupDelRow()
        self.setWindowTitleEx(u'Вакцины')


    def getItemEditor(self):
        return CRBVaccineEditor(self)


    def setup(self, *args, **kw):
        CItemsListDialog.setup(self, *args, **kw)

        self.addModels('VaccineInfections',
                       CTableModel(self,
                                   [
                                    CRefBookCol(u'Инфекция', ['infection_id'],'rbInfection', 20, 2)
                                   ],
                                   u'rbInfection_rbVaccine')
                      )

        self.addModels('VaccineSchemes',
                       CTableModel(self,
                                   [
                                    CTextCol(u'Тип прививки',     ['vaccinationType'], 10),
                                    CTextCol(u'Возраст',          ['age'],             10),
                                    CTextCol(u'Минимальный срок', ['minimumTerm'],     10),
                                    CTextCol(u'Срок действия',    ['duration'],        10),
                                    CTextCol(u'Сезонность',       ['seasonality'],     10),
                                   ],
                                   u'rbVaccine_Schema')
                      )

        self.addModels('VaccineSchemaTransitions',
                       CTableModel(self,
                                   [
                                    CRefBookCol(u'Тип перехода', ['transitionType_id'],
                                                u'rbVaccine_SchemaTransitionType', 20, 2),
                                    CDesignationCol(u'Схема перехода', ['schema_id'],
                                                    ('rbVaccine_Schema', 'vaccinationType'), 8)
                                   ],
                                   u'rbVaccine_SchemaTransition')
                      )

        self.setModels(self.tblVaccineInfections,
                       self.modelVaccineInfections,
                       self.selectionModelVaccineInfections)

        self.setModels(self.tblVaccineSchemes,
                       self.modelVaccineSchemes,
                       self.selectionModelVaccineSchemes)

        self.setModels(self.tblVaccineSchemaTransitions,
                       self.modelVaccineSchemaTransitions,
                       self.selectionModelVaccineSchemaTransitions)

        self.connect(self.selectionModel,
                     SIGNAL('currentChanged(QModelIndex, QModelIndex)'),
                     self.on_selectionModel_currentChanged)

        self.connect(self.selectionModelVaccineSchemes,
                     SIGNAL('currentChanged(QModelIndex, QModelIndex)'),
                     self.on_selectionModelVaccineSchemes_currentChanged)


    def getIdByRow(self, model, row):
        if 0 <= row < model.rowCount():
            return model.idList()[row]
        return None


    def on_selectionModel_currentChanged(self, current, previous):
        vaccineId = self.getIdByRow(self.model, current.row())
        if vaccineId:
            db = QtGui.qApp.db

            tableInfectionVaccine = db.table('rbInfection_rbVaccine')
            idList = db.getIdList(tableInfectionVaccine, 'id',
                                  tableInfectionVaccine['vaccine_id'].eq(vaccineId), 'id')
            self.modelVaccineInfections.setIdList(idList)
            self.tblVaccineInfections.setCurrentIndex(self.modelVaccineInfections.index(0, 0))


            tableVaccineSchema = db.table('rbVaccine_Schema')
            idList = db.getIdList(tableVaccineSchema, 'id',
                                  tableVaccineSchema['master_id'].eq(vaccineId), 'id')
            self.modelVaccineSchemes.setIdList(idList)
            self.tblVaccineSchemes.setCurrentIndex(self.modelVaccineSchemes.index(0, 0))



    def on_selectionModelVaccineSchemes_currentChanged(self, current, previous):
        schemaId = self.getIdByRow(self.modelVaccineSchemes, current.row())
        if schemaId:
            db = QtGui.qApp.db

            tableVaccineSchemaTransition = db.table('rbVaccine_SchemaTransition')
            idList = db.getIdList(tableVaccineSchemaTransition, 'id',
                                  tableVaccineSchemaTransition['master_id'].eq(schemaId), 'id')
            self.modelVaccineSchemaTransitions.setIdList(idList)


    def select(self, props):
        table = self.model.table()
        cond  = []
        codeStart=forceString(self.edtCode.text())
        if codeStart:
            cond.append(table['code'].contain(codeStart))
        namePart=forceString(self.edtName.text())
        if namePart:
            cond.append(table['name'].contain(namePart))
        return QtGui.qApp.db.getIdList(table.name(), 'id', where=cond, order=self.order)


    def renewListAndSetTo(self, itemId=None):
        if itemId is None:
            itemId = self.currentItemId()
        idList = self.select(self.props)
        try:
            i = idList.index(itemId)
        except:
            i = 0

        self.model.setIdList(idList)
        self.tblItems.setCurrentRow(max(0, i))
        self.label.setText(formatRecordsCount(len(idList)))


    @pyqtSignature('QString')
    def on_edtCode_textChanged(self, text):
        self.renewListAndSetTo()



    @pyqtSignature('QString')
    def on_edtName_textChanged(self, text):
        self.renewListAndSetTo()


#
# ##########################################################################
#

class CRBVaccineEditor(Ui_RBVaccineEditor, CItemEditorBaseDialog):
    def __init__(self, parent):
        CItemEditorBaseDialog.__init__(self, parent, 'rbVaccine')
        self.setupUi(self)
        self.addModels('VaccineInfections', CVaccineInfectionsModel(self))
        self.addModels('VaccineSchemaTransitions', CVaccineSchemaTransitions(self))
        self.addModels('VaccineSchemes', CVaccineSchemesModel(self, self.modelVaccineSchemaTransitions))
        self.addModels('VaccineIdentification', CVaccineIdentificationModel(self))
        self.setModels(self.tblVaccineInfections, self.modelVaccineInfections, self.selectionModelVaccineInfections)
        self.setModels(self.tblVaccineSchemes, self.modelVaccineSchemes, self.selectionModelVaccineSchemes)
        self.setModels(self.tblVaccineSchemaTransitions,
                       self.modelVaccineSchemaTransitions,
                       self.selectionModelVaccineSchemaTransitions)
        self.setModels(self.tblVaccineIdentification,
                       self.modelVaccineIdentification,
                       self.selectionModelVaccineIdentification)

        self.setWindowTitleEx(u'Вакцина')

        self.tblVaccineSchemes.setItemDelegateForColumn(0, CVaccinationTypeDelegate(self.tblVaccineSchemes))

        self.tblVaccineInfections.setCurrentIndex(self.modelVaccineInfections.index(0, 0))
        self.tblVaccineSchemes.setCurrentIndex(self.modelVaccineSchemes.index(0, 0))

        self.connect(self.selectionModelVaccineSchemes,
                     SIGNAL('currentChanged(QModelIndex, QModelIndex)'),
                     self.on_selectionModelVaccineSchemes_currentChanged)

        self.connect(self.modelVaccineSchemes,
                     SIGNAL('setTransitionsEnabled(bool)'),
                     self.on_setTransitionsEnabled)
        self.connect(QtGui.qApp, SIGNAL('sgtinReceived(QString)'), self.onSgtinReceived)
        self.connect(QtGui.qApp, SIGNAL('gtinReceived(QString)'),  self.onGtinReceived)

        self.tblVaccineInfections.addPopupDelRow()
        self.tblVaccineSchemaTransitions.addPopupDelRow()
        self.tblVaccineSchemes.addPopupDelRow()
        self.tblVaccineIdentification.addPopupDelRow()
        self.tblVaccineIdentification.setDelRowsChecker(self.modelVaccineIdentification.delRowsChecker)


    def setEditable(self, value):
        self.setReadOnly(not value)


    def setReadOnly(self, value):
        CItemEditorBaseDialog.setReadOnly(self, value)
        edtWigets = [self.edtCode, self.edtName, self.edtRegionalCode, self.edtDose]
        for wgt in edtWigets:
            wgt.setReadOnly(value)

        models = [self.modelVaccineInfections, self.modelVaccineSchemaTransitions, self.modelVaccineSchemes]
        for model in models:
            model.setEnableAppendLine(not value)
            for col in model.cols():
                col.setReadOnly(value)

        buttons = QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel if not value else QtGui.QDialogButtonBox.Close
        self.buttonBox.setStandardButtons(buttons)


    def on_setTransitionsEnabled(self, value):
        self.tblVaccineSchemaTransitions.setEnabled(value)


    def on_selectionModelVaccineSchemes_currentChanged(self, current, previous):
        self.modelVaccineSchemes.loadTransitions(current.row())


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(self.edtCode,                record, 'code' )
        setLineEditValue(self.edtName,                record, 'name' )
        setLineEditValue(self.edtRegionalCode,        record, 'regionalCode')
        setDoubleBoxValue(self.edtDose,               record, 'dose')
        self.modelVaccineInfections.loadItems(self.itemId())
        self.tblVaccineInfections.setCurrentIndex(self.modelVaccineInfections.index(0, 0))
        self.modelVaccineSchemes.loadItems(self.itemId())
        self.tblVaccineSchemes.setCurrentIndex(self.modelVaccineSchemes.index(0, 0))
        self.modelVaccineIdentification.loadItems(self.itemId())


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(self.edtCode,                record, 'code' )
        getLineEditValue(self.edtName,                record, 'name' )
        getLineEditValue(self.edtRegionalCode,        record, 'regionalCode')
        getDoubleBoxValue(self.edtDose,               record, 'dose')
        return record


    def saveInternals(self, id):
        self.modelVaccineInfections.saveItems(id)
        self.modelVaccineSchemes.saveItems(id)
        self.modelVaccineIdentification.saveItems(id)


    def checkDataEntered(self):
        result = CItemEditorBaseDialog.checkDataEntered(self)
        result = result and self.checkSchemesModelDataEntered()
        return result


    def checkSchemesModelDataEntered(self):
        for row, item in enumerate(self.modelVaccineSchemes.items()):
            age         = forceStringEx(item.value('age'))
            minimumTerm = forceStringEx(item.value('minimumTerm'))
            duration    = forceStringEx(item.value('duration'))
            if age:
                try:
                    (begUnit, begCount, endUnit, endCount) = parseAgeSelectorInt(age)
                    if endUnit and endCount:
                        if not self.checkExistsSchemaTransition(row, code=u'!в'):
                            self.tblVaccineSchemes.setCurrentIndex(self.modelVaccineSchemes.index(row, 0))
                            return self.checkInputMessage(u'тип перехода с кодом \'!в\'',
                                                          False, self.tblVaccineSchemaTransitions)
                except ValueError:
                    return self.checkInputMessage(u'корректный возраст', False, self.tblVaccineSchemes, row, 1)
            if minimumTerm:
                try:
                    (begUnit, begCount, endUnit, endCount) = parseAgeSelectorInt(minimumTerm)
                    if endUnit or endCount:
                        raise ValueError, u'Недопустимый синтаксис селектора возраста "%s"' % minimumTerm
                except ValueError:
                    return self.checkInputMessage(u'корректный минимальный срок', False, self.tblVaccineSchemes, row, 2)
            if duration:
                try:
                    (begUnit, begCount, endUnit, endCount) = parseAgeSelectorInt(duration)
                    if begUnit or begCount:
                        raise ValueError, u'Недопустимый синтаксис селектора возраста "%s"' % duration
                    elif endUnit or endCount:
                        if not self.checkExistsSchemaTransition(row, code=u'!с'):
                            self.tblVaccineSchemes.setCurrentIndex(self.modelVaccineSchemes.index(row, 0))
                            return self.checkInputMessage(u'тип перехода с кодом \'!с\'',
                                                          True, self.tblVaccineSchemaTransitions)
                except ValueError:
                    return self.checkInputMessage(u'корректный срок действия', False, self.tblVaccineSchemes, row, 3)
        return True


    def checkExistsSchemaTransition(self, vaccineSchemaRow, code=None):
        if code is None:
            return None, True

        data = CRBModelDataCache.getData('rbVaccine_SchemaTransitionType', addNone=False)

        transitionItems = self.modelVaccineSchemes.getTransitionItems(vaccineSchemaRow)
        for transitionRow, transitionItem in enumerate(transitionItems):
            transitionTypeId = forceRef(transitionItem.value('transitionType_id'))
            if transitionTypeId:
                transitionTypeCode = forceStringEx(data.getCodeById(transitionTypeId))
                if transitionTypeCode == code:
                    return True

        return False


    def onSgtinReceived(self, sgtin):
        self.onGtinReceived(sgtin[:14])


    def onGtinReceived(self, gtin):
        urn = 'urn:gtin'
        systemId = forceRef(QtGui.qApp.db.translate('rbAccountingSystem', 'urn', urn, 'id'))
        if systemId:
            self.modelVaccineIdentification.addIdentification(systemId, gtin)
            self.tabWidget.setCurrentWidget(self.tabIdentification)
        else:
            QtGui.QMessageBox.critical(self,
                u'Внимание!',
                u'Добавление идентификации невозможно, так как не найдена учётная система с urn «%s»' % urn,
                QtGui.QMessageBox.Ok,
                QtGui.QMessageBox.Ok)


# ###############################################################

class CVaccineInfectionsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbInfection_rbVaccine', 'id', 'vaccine_id', parent)
        self.addCol(CRBSearchInDocTableCol(u'Инфекция', 'infection_id', 20, 'rbInfection', showFields=2))
        self._idxFieldName = ''


rus = u'км.'
eng = u'rv/'
r2e = {}
e2r = {}
for i in range(len(rus)):
    r2e[ rus[i] ] = eng[i]
    e2r[ eng[i] ] = rus[i]


class CVaccinationTypeDelegate(CLocItemDelegate):
    def editorEvent(self, event, model, option, index):
        event.isNew = False
        flags = model.flags(index)
        if not (flags & Qt.ItemIsEnabled and flags & Qt.ItemIsEditable):
            return False

        if index.row() == len(model.items()) and isinstance(event, QtGui.QKeyEvent):
            chr = unicode(event.text()).lower()
            if r2e.has_key(chr):
                model.setVaccineTypeFirstChar(r2e[chr].upper())
            elif e2r.has_key(chr):
                model.setVaccineTypeFirstChar(chr.upper())
            else:
                model.setVaccineTypeFirstChar('')

            event.isNew = True

        return CLocItemDelegate.editorEvent(self, event, model, option, index)



class CVaccineSchemesModel(CInDocTableModel):

    class CVaccinationTypeCol(CInDocTableCol):
        class CLineEdit(QtGui.QLineEdit):

            def keyPressEvent(self, event):
                chr = unicode(event.text()).lower()
                if r2e.has_key(chr):
                    if hasattr(event, 'isNew'):
                        engChr = r2e[chr].upper() if not event.isNew else ' '
                    else:
                        engChr = r2e[chr].upper()
                    myEvent = QtGui.QKeyEvent(event.type(), ord(engChr), event.modifiers(), engChr, event.isAutoRepeat(), event.count())
                    QtGui.QLineEdit.keyPressEvent(self, myEvent)
                elif e2r.has_key(chr):
                    if hasattr(event, 'isNew'):
                        engChr = chr.upper() if not event.isNew else ' '
                    else:
                        engChr = chr.upper()
                    myEvent = QtGui.QKeyEvent(event.type(), ord(engChr), event.modifiers(), engChr, event.isAutoRepeat(), event.count())
                    QtGui.QLineEdit.keyPressEvent(self, myEvent)
                else:
                    QtGui.QLineEdit.keyPressEvent(self, event)


        def createEditor(self, parent):
            editor = CVaccineSchemesModel.CVaccinationTypeCol.CLineEdit(parent)
            editor.setValidator(QtGui.QRegExpValidator(QRegExp(u'V\d{1,}/\d*|R\d{1,}/\d*|RV\d{1,}/\d*'), None))
            return editor

        def setEditorData(self, editor, value, record):
            editor.setText(forceStringEx(record.value('vaccinationType')))


    def __init__(self, parent, modelTransitions):
        CInDocTableModel.__init__(self, 'rbVaccine_Schema', 'id', 'master_id', parent)
        self.addCol(CVaccineSchemesModel.CVaccinationTypeCol(u'Тип прививки',
                                                             'vaccinationType',
                                                             10, maxLength=7))
        self.addCol(CInDocTableCol(u'Возраст',             'age',             10,                    maxLength=9))
        self.addCol(CInDocTableCol(u'Минимальный срок',    'minimumTerm',     10,                    maxLength=9))
        self.addCol(CInDocTableCol(u'Срок действия',       'duration',        10,                    maxLength=9))
        self.addCol(CInDocTableCol(u'Сезонность',          'seasonality',     10, inputMask='99-99', maxLength=5))
        self._modelTransitions = modelTransitions
        self._mapRow2TransitionItems = {}
        self._vaccineTypeFirstChar = ''


    def setVaccineTypeFirstChar(self, char):
        char = char if char in ('V', 'R', '/') else ''
        self._vaccineTypeFirstChar = char


    def getEmptyRecord(self):
        record = CInDocTableModel.getEmptyRecord(self)
        record.setValue('vaccinationType', toVariant(self.getNewVaccinationType()))
        return record


    def getNewVaccinationType(self):
        def _getPrefix():
            if self._vaccineTypeFirstChar == 'V':
                return 'V'
            elif self._vaccineTypeFirstChar == 'R':
                return 'RV'
            else:
                return 'V'
        if self._items:
            lastRecord = self._items[-1]
            lastVaccinationType = forceStringEx(lastRecord.value('vaccinationType'))
            if lastVaccinationType:
                if self._vaccineTypeFirstChar and self._vaccineTypeFirstChar != lastVaccinationType[0] and self._vaccineTypeFirstChar != '/':
                    lastVaccinationType = self._vaccineTypeFirstChar
                if lastVaccinationType[-1].isdigit():
                    if lastVaccinationType[0].isalpha():
                        strEnd = 2 if lastVaccinationType[1].isalpha() else 1
                        lastDigitPart = lastVaccinationType[strEnd:]
                        if '/' in lastDigitPart:
                            digitSubParts = lastDigitPart.split('/')
                            newDigitPart = digitSubParts[0]+'/'+unicode(int(digitSubParts[1])+1)
                        else:
                            newDigitPart = unicode(int(lastDigitPart)+1)
                        newVaccinationType = lastVaccinationType[:strEnd]+newDigitPart
                    else:
                        newVaccinationType = _getPrefix() + u'1'
                elif len(lastVaccinationType) > 1 and lastVaccinationType[-1] == '/':
                    newVaccinationType = lastVaccinationType + '1'
                else:
                    newVaccinationType = _getPrefix() + '1'
            else:
                newVaccinationType = _getPrefix() + u'1'
        else:
            newVaccinationType = _getPrefix() + u'1'

        return newVaccinationType



    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0<=row and row+count<=len(self._items):
            for locRow in range(row, row+count):
                self._mapRow2TransitionItems[locRow] = []
            return CInDocTableModel.removeRows(self, row, count, parentIndex)
        return False


    def getTransitionItems(self, row):
        result = self._mapRow2TransitionItems.get(row, None)
        if result is None:
            item = self.items()[row]
            itemId = forceRef(item.value('id'))
            if itemId:
                self._modelTransitions.loadItems(itemId)
                result = self._modelTransitions.items()
            else:
                result = []
            self._mapRow2TransitionItems[row] = result

        return result

    def loadTransitions(self, row):
        if 0 <= row < len(self.items()):
            transitionItems = self.getTransitionItems(row)
            self._modelTransitions.setItems(transitionItems)
            self.emit(SIGNAL('setTransitionsEnabled(bool)'), True)
        else:
            self.emit(SIGNAL('setTransitionsEnabled(bool)'), False)

    def saveDependence(self, idx, id):
        items = self._mapRow2TransitionItems.get(idx, [])
        for item in items:
            self._modelTransitions.setItems(items)
            self._modelTransitions.saveItems(id)


class CVaccineSchemaTransitions(CInDocTableModel):
    class CSchemaInDocTableCol(CInDocTableCol):
        def __init__(self):
            CInDocTableCol.__init__(self, u'Схема перехода', 'schema_id', 20)
            self._model = CDbModel(None)
            self._model.setNameField('CONCAT_WS(\' | \', (SELECT code FROM rbVaccine WHERE rbVaccine.id=master_id), vaccinationType)')
            self._model.setAddNone(False)
            self._model.setTable('rbVaccine_Schema')
            self._cache = {}


        def toString(self, val, record):
            return self._model.getNameById(forceRef(val))



        def createEditor(self, parent):
            editor = CDbComboBox(parent)
            editor.setModel(self._model)
            return editor


        def setEditorData(self, editor, value, record):
            editor.setValue(forceRef(value))


        def getEditorData(self, editor):
            return toVariant(editor.value())



    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbVaccine_SchemaTransition', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Тип перехода', 'transitionType_id', 20,
                                     u'rbVaccine_SchemaTransitionType', showFields=2))
        self.addCol(CVaccineSchemaTransitions.CSchemaInDocTableCol())



class CVaccineIdentificationModel(CIdentificationModel):
    def __init__(self, parent):
        CIdentificationModel.__init__(self, parent, 'rbVaccine_Identification', 'rbVaccine')
        self.addCol(CInDocTableCol(u'Тип прививки', 'vaccinationType', 30), idx=-1)
