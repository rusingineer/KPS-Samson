# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2019 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Страница настройки выбора ЛПУ, подразделения, региона и др.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, SIGNAL, QDir

from library.Utils            import (
                                         forceBool,
                                         forceRef,
                                         forceString,
                                         toVariant,
                                     )
from Orgs.Orgs                import selectOrganisation
from KLADR.Utils              import getProvinceKLADRCode

from Ui_MainPage import Ui_mainPage


class CMainPage(Ui_mainPage, QtGui.QWidget):
    __pyqtSignals__ = ('defaultCityChanged(QString)',
#                       'provinceChanged(QString)'
                      )


    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.cmbProvince.setAreaSelectable(True)
        self.__region = ''


    def setProps(self, props):
        self.cmbOrganisation.setValue(forceRef(props.get('orgId', None)))
        self.cmbOrgStructure.setValue(forceRef(props.get('orgStructureId', None)))
        kladrCode = forceString(props.get('defaultKLADR', '7800000000000'))
        self.cmbDefaultCity.setCode(kladrCode)
        provinceKLADR = forceString(props.get('provinceKLADR', ''))
        self.cmbProvince.setCode(provinceKLADR or getProvinceKLADRCode(kladrCode))

        self.chkHighlightRedDate.setChecked(forceBool(props.get('highlightRedDate', True)))
        self.chkHighlightInvalidDate.setChecked(forceBool(props.get('highlightInvalidDate', True)))

        self.chkPersonFilterInCmb.setChecked(forceBool(props.get('personFilterInCmb', False)))
        self.chkOnlyDoctors.setChecked(forceBool(props.get('onlyDoctorsInPopup', False)))

        self.edtTemplateDir.setText(forceString(props.get('templateDir', QtGui.qApp.getTemplateDir())))
        self.edtBrowserDir.setText(forceString(props.get('browserDir', QtGui.qApp.getBrowserDir())))

        self.edtFTPUrl.setText(forceString(props.get('FTPUrl', '')))


    def getProps(self, props):
        props['orgId']          = toVariant(self.cmbOrganisation.value())
        props['orgStructureId'] = toVariant(self.cmbOrgStructure.value())
        props['defaultKLADR']   = toVariant(self.cmbDefaultCity.code())
        props['provinceKLADR']  = toVariant(self.cmbProvince.code())

        props['highlightRedDate']        = toVariant(bool(self.chkHighlightRedDate.isChecked()))
        props['highlightInvalidDate']    = toVariant(bool(self.chkHighlightInvalidDate.isChecked()))

        props['personFilterInCmb']       = toVariant(self.chkPersonFilterInCmb.isChecked())
        props['onlyDoctorsInPopup']      = toVariant(self.chkOnlyDoctors.isChecked())

        props['templateDir']             = toVariant(self.edtTemplateDir.text())
        props['browserDir']             = toVariant(self.edtBrowserDir.text())

        props['FTPUrl'] = toVariant(self.edtFTPUrl.text())


    @pyqtSignature('int')
    def on_cmbOrganisation_currentIndexChanged(self, index):
        orgId = self.cmbOrganisation.value()
        self.cmbOrgStructure.setOrgId(orgId)


    @pyqtSignature('')
    def on_btnSelectOrganisation_clicked(self):
        orgId = selectOrganisation(self, self.cmbOrganisation.value(), False)
        self.cmbOrganisation.updateModel()
        if orgId:
            self.cmbOrganisation.setValue(orgId)


    @pyqtSignature('int')
    def on_cmbDefaultCity_currentIndexChanged(self):
        cityKLADRCode = self.cmbDefaultCity.code()
        provinceKLADRCode = getProvinceKLADRCode(cityKLADRCode)
        self.cmbProvince.setCode(provinceKLADRCode)
        self.emit(SIGNAL('defaultCityChanged(QString)'), cityKLADRCode)


#    @pyqtSignature('int')
#    def on_cmbProvince_currentIndexChanged(self):
#        province = self.cmbProvince.code()
#        if  self.__province != province:
#            self.emit(SIGNAL('provinceChanged(QString)'), region)
#            self.__province = province

    @pyqtSignature('')
    def on_btnSelectTemplateDir_clicked(self):
        dir = QtGui.QFileDialog.getExistingDirectory(
            self, u'Укажите каталог с шаблонами документов', self.edtTemplateDir.text())
        if dir:
            self.edtTemplateDir.setText(QDir.toNativeSeparators(dir))

    @pyqtSignature('')
    def on_btnSelectBrowserDir_clicked(self):
        dir = QtGui.QFileDialog.getOpenFileName(
            self, u'Укажите каталог и файл браузера', self.edtBrowserDir.text())
        if dir:
            self.edtBrowserDir.setText(QDir.toNativeSeparators(dir))
