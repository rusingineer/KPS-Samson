# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2016-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Список прикреплённых файлов
##
#############################################################################

import os.path
from base64 import b64encode

import sip
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, QMetaObject, QSize, QUrl, QDateTime, QTimer, QByteArray

from Reports.ReportView import CReportViewDialog
from library.MSCAPI import MSCApi


from Users.Rights   import ( urCanAttachFile,
                             urCanOpenAnyAttachedFile,
                             urCanOpenOwnAttachedFile,
                             urCanRenameAnyAttachedFile,
                             urCanRenameOwnAttachedFile,
                             urCanDeleteAnyAttachedFile,
                             urCanDeleteOwnAttachedFile,
                             urCanDeleteSuccessExpFile,
                             urCanSignForOrganisation,
                             urAdmin,
                           )


from .AttachFilesTableFlag import CAttachFilesTableFlag
from .AttachedFile import CAttachedFile
from ..CertComboBox import extractCertInfo
from ..MSCAPI import MSCApi
from ..PrintInfo import CInfoContext
from ..Utils import toVariant, forceString, forceRef, anyToUnicode, forceBool
from ..userCertPlate import CCertInfoPlate


class CAttachFilesTable(QtGui.QTableView):
    u'Представление списка прикреплённых файлов'
    __pyqtSignals__ = ('iteractionDone()',
                      )


    def __init__(self, parent):
        QtGui.QTableView.__init__(self)
        self._flags = CAttachFilesTableFlag.canAnything
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.ExtendedSelection)
        self.setSortingEnabled(True)
        self.resetSortIndicator()

        h = self.fontMetrics().height()*3//2
        self.verticalHeader().setDefaultSectionSize(h)
        self.verticalHeader().hide()
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)

        self.actOpen = QtGui.QAction(u'&Открыть', self)
        self.actOpen.setObjectName('actOpen')

        self.actOpenWithSignatures = QtGui.QAction(u'&Печать с оттиском ЭЦП', self)
        self.actOpenWithSignatures.setObjectName('actOpenWithSignatures')

        self.actSave = QtGui.QAction(u'&Сохранить', self)
        self.actSave.setObjectName('actSave')

        if QtGui.qApp.userHasRight(urAdmin):
            self.actSaveKey = QtGui.QAction(u'&Сохранить подпись', self)
            self.actSaveKey.setObjectName('actSaveKey')

        self.actAddKey = QtGui.QAction(u'&Добавить подпись', self)
        self.actAddKey.setObjectName('actAddKey')

        self.actAdd = QtGui.QAction(u'&Добавить',  self)
        self.actAdd.setObjectName('actAdd')
        self.actRename = QtGui.QAction(u'&Переименовать', self)
        self.actRename.setObjectName('actRename')
        self.actComment = QtGui.QAction(u'&Изменить коментарий', self)
        self.actComment.setObjectName('actComment')
        self.actDelete = QtGui.QAction(u'&Удалить',  self)
        self.actDelete.setObjectName('actDelete')

        self.actSignAsResp = QtGui.QAction(u'Подписать за ответственное лицо',  self)
        self.actSignAsResp.setObjectName('actSignAsResp')
        self.actSignAsOrg = QtGui.QAction(u'Подписать за организацию',  self)
        self.actSignAsOrg.setObjectName('actSignAsOrg')

#        self.setContextMenuPolicy(Qt.DefaultContextMenu)

        self.mnuPopup = QtGui.QMenu(self)
        self.mnuPopup.setObjectName('mnuPopup')

        self.mnuPopup.addAction(self.actOpen)
        self.mnuPopup.addAction(self.actOpenWithSignatures)
        self.mnuPopup.addAction(self.actSave)
        if QtGui.qApp.userHasRight(urAdmin):
            self.mnuPopup.addAction(self.actSaveKey)
        self.mnuPopup.addAction(self.actAddKey)
        self.mnuPopup.addSeparator()
        self.mnuPopup.addAction(self.actAdd)
        self.mnuPopup.addAction(self.actRename)
        self.mnuPopup.addAction(self.actComment)
        self.mnuPopup.addAction(self.actDelete)
        self.mnuPopup.addSeparator()
        self.mnuPopup.addAction(self.actSignAsResp)
        self.mnuPopup.addAction(self.actSignAsOrg)

        self.mnuPopup.setDefaultAction(self.actOpen)

        QMetaObject.connectSlotsByName(self)
        # self.actAddKey.triggered.connect(self.actAddKey_triggered)


    def setFlags(self, flags):
        self._flags = flags


    def resetSortIndicator(self):
        self.sortByColumn(-1, Qt.AscendingOrder)


    def sizeHint(self):
        model = self.model()
        if not model:
            return QtGui.QTableView().sizeHint()
        else:
            self.resizeColumnsToContents()
            self.resizeRowsToContents()
            w = self.verticalHeader().width() + self.frameWidth()*2 + self.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent)
            for i in xrange(model.columnCount()):
                self.resizeColumnToContents(0)
                w += self.columnWidth(i)
            h = self.horizontalHeader().height() + self.frameWidth()*2
            for i in xrange(model.rowCount()):
                h += self.rowHeight(i)
            return QSize(w, h)

#            hh           = self.horizontalHeader()
#            headerHeight = hh.height()
#            rowHeight    = self.verticalHeader().defaultSectionSize()
#            frameWidth   = self.frameWidth()
#            lineWidth    = self.lineWidth()
#            iconMetric   = self.style().pixelMetric(QtGui.QStyle.PM_SmallIconSize)
#            dataWidth    = sum( max(self.sizeHintForColumn(column) + iconMetric,
#                                    hh.sectionSizeHint(column)
#                                   )
#                                for column in xrange(model.columnCount())
#                              )
#            return QSize(  dataWidth
#                         + lineWidth*model.columnCount() + 2*frameWidth + 16
#                         + self.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent),
#                           headerHeight
#                         + (max(iconMetric, rowHeight) + lineWidth)*model.rowCount()
#                         + 2*frameWidth
#                         + self.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent),
#                        )

    def widgetForFileDialog(self):
        window = self.window()
        if window and window.windowType() & Qt.Popup != 0:
            return window.parentWidget()
        else:
            return self


    def getCurrentFileItem(self):
        modelIndex = self.currentIndex()
        if modelIndex.isValid():
            return self.model().items[modelIndex.row()]
        else:
            return None

    def selectedItems(self):
        items = []
        for modelIndex in self.selectedIndexes():
            if modelIndex.isValid():
                item = self.model().items[modelIndex.row()]
                if item not in items:
                    items.append(item)
        return items

    def userHasRights(self, fileItem, anyRight, ownRight):
        app = QtGui.qApp
        if app.userHasRight(anyRight):
            return True
        ownFile = bool(fileItem) and not fileItem.isLost and fileItem.authorId == app.userId
        return ownFile and app.userHasRight(ownRight)


    def canAdd(self):
        return bool(self._flags & CAttachFilesTableFlag.canAdd) and QtGui.qApp.userHasRight(urCanAttachFile)


    def canOpen(self, fileItem):
        return (     bool(self._flags & CAttachFilesTableFlag.canOpen)
                 and self.userHasRights(fileItem, urCanOpenAnyAttachedFile, urCanOpenOwnAttachedFile)
               )


    def canSave(self):
        return (     bool(self._flags & CAttachFilesTableFlag.canSave)
               )


    def canRename(self, fileItem):
        return (     bool(self._flags & CAttachFilesTableFlag.canRename)
                and self.userHasRights(fileItem, urCanRenameAnyAttachedFile, urCanRenameOwnAttachedFile)
               )


    def canDelete(self, fileItem):

        if fileItem.id:
            stmt = u'''SELECT id FROM Information_Messages WHERE IdMedDocumentMis_id = %(Id)s AND CHAR_LENGTH(IFNULL(RemdRegNumber, '')) > 0''' % {
                'Id': fileItem.id
            }

            query = QtGui.qApp.db.query(stmt)
            delete_ok = query.size() == 0
        else:
            delete_ok = True

        return (     bool(self._flags & CAttachFilesTableFlag.canDelete)
                     and ((delete_ok or QtGui.qApp.userHasRight(urCanDeleteSuccessExpFile)) and
                          self.userHasRights(fileItem, urCanDeleteAnyAttachedFile, urCanDeleteOwnAttachedFile)
                          )
               )


    def canSignAsResp(self, fileItem):
        return (     bool(self._flags & CAttachFilesTableFlag.canSignAsResp)
                     and QtGui.qApp.isCspDefined()
                     and fileItem.respSignature is None
               )


    def canSignAsOrg(self, fileItem):
        return (     bool(self._flags & CAttachFilesTableFlag.canSignAsOrg)
                     and QtGui.qApp.isCspDefined()
                     and QtGui.qApp.userHasRight(urCanSignForOrganisation)
                     and fileItem.respSignature is not None
                     and fileItem.orgSignature is None
               )


    def openAttachedFile(self, attachedFileItem):
        interface = self.model().interface
        url = interface.getUrl(attachedFileItem)
        QtGui.QDesktopServices.openUrl(QUrl(url))


    def saveAttachedFile(self, attachedFileItem):
        # в Windows при использовании Qt4.6 при открытии QFileDialog popup закрывается :(
        model = self.model()
        documentsDir = unicode(QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.DocumentsLocation))
        localFile = QtGui.QFileDialog.getSaveFileName(self.widgetForFileDialog(),
                                                      u'Сохранить файл',
                                                      os.path.join(documentsDir, attachedFileItem.newName),
                                                      u'Любые файлы(*)')
        if localFile:
            interface = model.interface
            interface.downloadFile(attachedFileItem, unicode(localFile))
            if forceBool(QtGui.qApp.preferences.appPrefs.get('saveWithSignatures', False)):
                if attachedFileItem.hasRespSignature():
                    sigFile = os.path.splitext(forceString(localFile))[0] + '_respSignature.sig'
                    data = convertSignatureToCMS(attachedFileItem.respSignature.signatureBytes)
                    f = open(sigFile, 'wb')
                    try:
                        f.write(data)
                    finally:
                        f.close()
                if attachedFileItem.hasOrgSignature():
                    sigFile = os.path.splitext(forceString(localFile))[0] + '_orgSignature.sig'
                    data = convertSignatureToCMS(attachedFileItem.orgSignature.signatureBytes)
                    f = open(sigFile, 'wb')
                    try:
                        f.write(data)
                    finally:
                        f.close()

    def saveAttachedKeyFile(self, attachedFileItem):
        # в Windows при использовании Qt4.6 при открытии QFileDialog popup закрывается :( 1370973
        db = QtGui.qApp.db

        stmt = u'''select respSignatureBytes from Action_FileAttach where id = %(Id)s''' % {
            'Id': attachedFileItem.id
        }
        myquer = db.query(stmt)
        qz = myquer.size()

        for i in range(0, qz):
            myquer.next()
            qz1 = myquer.value(0).toByteArray()

        if (qz1 and qz):
            documentsDir = unicode(QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.DocumentsLocation))
            localFile = QtGui.QFileDialog.getSaveFileName(self.widgetForFileDialog(),
                                                          u'Сохранить файл',
                                                          os.path.join(documentsDir, u'подпись'),
                                                          u'Любые файлы(*)')
            if localFile:
                f = open(unicode(localFile), 'wb')
                f.write(qz1)
                f.close()
        else:
            QtGui.QMessageBox.information(self, u'Ошибка', u'Отсутствует подпись врача',
                                          QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)

    @staticmethod
    def selectFiles(widget):
        attachFileFromDir = forceString(QtGui.qApp.preferences.appPrefs.get('AttachFileFromDir', ''))
        documentsDir = QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.DocumentsLocation)
        ofr = QtGui.QFileDialog.getOpenFileNames(widget,
                                 u'Выберите файлы',
                                 attachFileFromDir or documentsDir or QtGui.qApp.getHomeDir(),
                                 ';;'.join((u'Документы(*.pdf *.odt *.ods *.doc *.xls *.docx *.xlsx)',
                                            u'Изображения(*.png *.tiff *.jpg *.jpeg *.gif *.bmp *.xpm)',
                                            u'Текстовые файлы(*.txt)',
                                            u'Архивы(*.zip *.7z *.Z *.gz *.bz *.xz *.arj *.rar)',
                                            u'Любые файлы(*)')))
        if ofr:
            QtGui.qApp.preferences.appPrefs['AttachFileFromDir'] = os.path.dirname(forceString(ofr[0]))
        return ofr


    def selectAndUploadFiles(self):
        # в Windows при использовании Qt4.6 при открытии QFileDialog popup закрывается :(
        model = self.model()
        ofr = self.selectFiles(self.widgetForFileDialog())
        if ofr:
            model.uploadFiles( [ unicode(fn) for fn in ofr] )
            if not sip.isdeleted(self):
                self.resetSortIndicator()


    def renameFile(self, fileItem):
        newName, ok = QtGui.QInputDialog.getText(self, # QWidget * parent,
                                                 u'Переименовать ' + fileItem.newName, # const QString & title,
                                                 '',                                   # const QString & label,
                                                 QtGui.QLineEdit.Normal,               # QLineEdit::EchoMode mode = QLineEdit::Normal,
                                                 fileItem.newName                      #  const QString & text = QString()
                                                )
        if ok:
            newName = unicode(newName)
            if all(c not in newName for c in '*?:/\\'):
                row = self.model().indexOfItem(fileItem)
                self.model().renameFile(row, unicode(newName))
                self.resetSortIndicator()
            else:
                pass #!!!


    def editComment(self, fileItem):
        comment = fileItem.comment
        if fileItem.comment == None:
            comment = u''
        comment, ok = QtGui.QInputDialog.getText(self, # QWidget * parent,
                                                 u'Изменить коментарий y ' + fileItem.newName, # const QString & title,
                                                 '',                                   # const QString & label,
                                                 QtGui.QLineEdit.Normal,               # QLineEdit::EchoMode mode = QLineEdit::Normal,
                                                 comment                      #  const QString & text = QString()
                                                )
        if ok:
            comment = unicode(comment)
            if all(c not in comment for c in '*?:/\\'):
                row = self.model().indexOfItem(fileItem)
                self.model().edtComment(row, unicode(comment))
                self.resetSortIndicator()
            else:
                pass #!!!


    def deleteFile(self, fileItem):
        row = self.model().indexOfItem(fileItem)
        self.model().removeRow(row)


    def emitIteractionDone(self):
        QtGui.qApp.emit(SIGNAL('iteractionDone()'))


    def mouseDoubleClickEvent(self, event): # event: QMouseEvent
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.NoModifier:
            fileItem = self.getCurrentFileItem()
            fileOk = bool(fileItem) and not fileItem.isLost
            if fileOk:
                if self.canOpen(fileItem):
                    self.openAttachedFile(fileItem)
                    self.emitIteractionDone()
                elif self.canSave():
                    self.saveAttachedFile(fileItem)
            event.accept()
        else:
            QtGui.QTableView.mouseDoubleClickEvent(self, event)


    def contextMenuEvent(self, event):
        fileItem = self.getCurrentFileItem()
        fileOk = bool(fileItem) and not fileItem.isLost
        self.actAdd.setEnabled(self.canAdd())
        self.actOpen.setEnabled(fileOk and self.canOpen(fileItem))
        self.actSave.setEnabled(fileOk and self.canSave())
        if QtGui.qApp.userHasRight(urAdmin):
            self.actSaveKey.setEnabled(fileOk and self.canSave())

        fileItem = self.getCurrentFileItem()
        respSigner = None
        hasId = False
        if fileItem._record:
            respSigner = forceRef(fileItem._record.value('respSigner_id'))
            hasId = forceBool(fileItem._record.value('id'))
        self.actOpenWithSignatures.setEnabled(fileOk and self.canOpen(fileItem) and forceBool(fileItem.htmlTemplate) and hasId)
        self.actAddKey.setEnabled(fileOk and self.canSave() and bool(respSigner) and hasId)
        self.actRename.setEnabled(fileOk and self.canRename(fileItem))
        self.actComment.setEnabled(fileOk and self.canRename(fileItem))
        self.actDelete.setEnabled(bool(fileItem) and self.canDelete(fileItem))
        self.actSignAsResp.setEnabled(fileOk and self.canSignAsResp(fileItem))
        self.actSignAsOrg.setEnabled(fileOk and self.canSignAsOrg(fileItem))
        self.mnuPopup.exec_(event.globalPos())
        event.accept()


    @pyqtSignature('')
    def on_actOpen_triggered(self):
        fileItem = self.getCurrentFileItem()
        fileOk = bool(fileItem) and not fileItem.isLost
        if fileOk and self.canOpen(fileItem):
            self.openAttachedFile(fileItem)
            self.emitIteractionDone()


    @pyqtSignature('')
    def on_actOpenWithSignatures_triggered(self):
        db = QtGui.qApp.db
        imageMainList = ['</body><br>']
        fileItem = self.getCurrentFileItem()
        fileOk = bool(fileItem) and not fileItem.isLost
        if fileOk and self.canOpen(fileItem):
            attachRecord = fileItem._record
            html = fileItem.htmlTemplate
            filePath = forceString(attachRecord.value('path'))
            if forceBool(filePath):
                fileName = filePath.split('/')[4]
            else:
                fileName = u'Просмотр файла с подписями'

            fileId = forceString(attachRecord.value('id'))
            if u'<!--sign_' in html:
                listCert = []
                org_signatureBytes = None
                signatureBytesList = self.getFileRespSignaturesBytes(fileId)

                signatureBytes = attachRecord.value('respSignatureBytes').toByteArray().data()
                api = MSCApi(QtGui.qApp.getCsp())
                if signatureBytes:
                    listCert.append([self.getAttachCerts(signatureBytes)[0], api.signatureAsStore(signatureBytes).listCerts()[0].snils()])
                if attachRecord.value('orgSignatureBytes').toByteArray():
                    org_signatureBytes = self.getAttachCerts(attachRecord.value('orgSignatureBytes').toByteArray().data())

                for signBytes in signatureBytesList:
                    imageList = self.getAttachCerts(signBytes)
                    for image in imageList:
                        if image != '</body><br>':
                            listCert.append([image, api.signatureAsStore(signBytes).listCerts()[0].snils()])

                for cert in listCert:
                    html = html.replace('<!--sign_' + str(cert[1]) + '-->', cert[0])
                    certSnils = str(cert[1])[:3] + '-' + str(cert[1])[3:6] + '-' + str(cert[1])[6:9] + ' ' + str(cert[1])[9:]
                    html = html.replace('<!--sign_' + certSnils + '-->', cert[0])

                if org_signatureBytes:
                    if u'<!--sign_mo-->' in html:
                        html = html.replace('<!--sign_mo-->', org_signatureBytes[0])
                    else:
                        html = u'{0} {1}'.format(html, org_signatureBytes[0])



            else:
                signatureBytesList = self.getFileRespSignaturesBytes(fileId)

                signatureBytes = attachRecord.value('respSignatureBytes').toByteArray().data()
                signatureBytesList.append(signatureBytes)

                for signBytes in signatureBytesList:
                    imageList = self.getAttachCerts(signBytes)
                    for image in imageList:
                        if image != '</body><br>':
                            imageMainList.append(image)
                if attachRecord.value('orgSignatureBytes').toByteArray():
                    org_signatureBytes = self.getAttachCerts(attachRecord.value('orgSignatureBytes').toByteArray().data())
                    if org_signatureBytes:
                        imageMainList.append(org_signatureBytes[0])

                imageString = u'<br>'
                index = 1
                for image in imageMainList:
                    imageString += image
                    if index % 2 == 0:
                        imageString += u'<br>'
                    index += 1
                html = html.replace('<!---->', '')
                html = u'{0} {1}'.format(html, imageString)

            view = CReportViewDialog(self)
            view.setWindowTitle(u'{0}'.format(fileName))
            view.setText(html)
            view.exec_()


    def getFileRespSignaturesBytes(self, id):
        db = QtGui.qApp.db
        respSignatureBytesList = []
        tableAFAS = db.table('Action_FileAttach_Signature')
        records = db.getRecordList(tableAFAS,
                                   [tableAFAS['signatureBytes']],
                                   [tableAFAS['master_id'].eq(id), tableAFAS['deleted'].eq(0)])
        for record in records:
            respSignatureBytes = record.value('signatureBytes').toByteArray().data()
            respSignatureBytesList.append(respSignatureBytes)
        return respSignatureBytesList


    def getAttachCerts(self, signatureBytes):
        certList = []
        imageList = []

        if signatureBytes:
            try:
                api = MSCApi(QtGui.qApp.getCsp())
            except:
                QtGui.qApp.logCurrentException()
                return
            try:
                with api.signatureAsStore(signatureBytes) as store:
                    for crt in store.listCerts():
                        certList.append(crt)
            except Exception:
                QtGui.qApp.logCurrentException()
        if certList:
            for cert in certList:
                snils = forceString(cert.snils())

                if forceString(cert.org()):
                    orgName = forceString(cert.org())
                else:
                    orgNameBySnils = self.getOrgNameBySnils(snils)
                    if orgNameBySnils:
                        orgName = orgNameBySnils
                    else:
                        orgName = u''

                resolutionScale = 4.0 # настоящий размер/четкость картинки
                plate = CCertInfoPlate.fromCert(cert, orgName=orgName, scale=resolutionScale)
                imgScale = 0.7 # уменьшаем в документе, чтобы помещалось 2 штуки в страницу A4
                imgWidth = int(plate.originalSize.width() * imgScale)
                imgHeight = int(plate.originalSize.height() * imgScale)
                imageString = u'<img src="data:image/png;base64,{0}" width="{1}" height="{2}">'.format(b64encode(plate.bytes), imgWidth, imgHeight)
                imageList.append(imageString)
        return imageList


    def getOrgNameBySnils(self, snils):
        db = QtGui.qApp.db

        tablePerson = db.table('Person')
        tableOrganisation = db.table('Organisation')
        tableQuery = tablePerson.leftJoin(tableOrganisation, tableOrganisation['id'].eq(tablePerson['org_id']))
        records = db.getRecordListGroupBy(tableQuery,
                                          [tableOrganisation['shortName']],
                                          [tablePerson['SNILS'].eq(snils), tablePerson['deleted'].eq(0)],
                                          'Person.org_id')
        orgName = u''
        for record in records:
            orgName = forceString(record.value('shortName'))

        return orgName


    @pyqtSignature('')
    def on_actSave_triggered(self):
        fileItem = self.getCurrentFileItem()
        fileOk = bool(fileItem) and not fileItem.isLost
        if fileOk and self.canSave():
            self.saveAttachedFile(fileItem)

    @pyqtSignature('')
    def on_actSaveKey_triggered(self):
        fileItem = self.getCurrentFileItem()
        fileOk = bool(fileItem) and not fileItem.isLost
        if fileOk and self.canSave():
            self.saveAttachedKeyFile(fileItem)


    @pyqtSignature('')
    def  on_actAddKey_triggered(self):
        interface = QtGui.qApp.webDAVInterface
        for fileItem in self.selectedItems():
            localPath = os.path.join(QtGui.qApp.getTmpDir(), fileItem.oldName)
            interface.downloadFile(fileItem, localPath)
            tmpFile = QtCore.QFile(localPath)
            tmpFile.open(QtCore.QIODevice.ReadOnly)
            pdfBytes = tmpFile.readAll().data()
            tmpFile.close()
            tmpFile.remove()
            try:
                try:
                    api = MSCApi(QtGui.qApp.getCsp())
                    cert = QtGui.qApp.getUserCert(api)

                    db = QtGui.qApp.db
                    pSnils = ''
                    attachRecord = fileItem.getRecord(db.table('Action_FileAttach'))
                    master_id = forceString(attachRecord.value('master_id'))
                    stmt = """
                            SELECT 
                                p1.SNILS as pSnils
                              from ActionPropertyType apt 

                              LEFT JOIN ActionType at ON at.id = apt.actionType_id
                              LEFT JOIN Action a ON at.id = a.actionType_id

                              LEFT JOIN ActionProperty ap ON a.id = ap.action_id AND apt.id = ap.type_id
                              LEFT JOIN ActionProperty_Person app ON app.id=ap.id
                              LEFT JOIN Person p1 ON app.value = p1.id

                              WHERE apt.valueDomain LIKE '%signer%'
                              AND p1.SNILS IS NOT NULL
                              AND p1.SNILS LIKE '%{0}%'
                              AND a.id = {1}

                             and apt.deleted = 0 and at.deleted=0

                             LIMIT 1;
                            """

                    if QtGui.qApp.getUseOwnPk():  # Если ключь пользователя по снилс
                        # Если в умолчаниях настроен ключ по снилс, сверяем снилс члена комиссии = снилс авторизовавшегося пользователя
                        snils = QtGui.qApp.getUserSnils()
                        stmt = stmt.format(snils, master_id)

                    else:  # Произвольный ключ пользователя
                        # Если в умолчаниях настроен произвольный ключ пользователя, снилс члена комиссии = снилс в ЭЦП в умолчаниях.
                        snils = cert.snils()
                        stmt = stmt.format(snils, master_id)

                    query = db.query(stmt)
                    while query.next():
                        rec = query.record()
                        pSnils = forceString(rec.value('pSnils'))

                    if pSnils:
                        detachedSignatureBytes = cert.createDetachedSignature(pdfBytes)
                        signerSnils = cert.snils()
                        records = self.getAvailableSigner(fileItem=fileItem, snils=signerSnils) # Тут recoeds выдает пустым
                        if detachedSignatureBytes and records:
                            # records = self.getAvailableSigner(fileItem=fileItem, snils=signerSnils)
                            # if records:
                            for temp_record in records:
                                signId = None
                                # signBytes = QByteArray(detachedSignatureBytes)
                                signerId = temp_record.value('sig')
                                signingDatetime = toVariant(QDateTime().currentDateTime())
                                signerTitle = toVariant(u'{0} {1}, {2}'.format(cert.surName(),
                                                                               cert.givenName(),
                                                                               cert.snils()))
                                masterId = fileItem.id

                                fileItem.addSignature(signId=signId,
                                                      signBytes=detachedSignatureBytes,
                                                      signerId=signerId,
                                                      signDatetime=signingDatetime,
                                                      signerTitle=signerTitle,
                                                      masterId=masterId)
                            if fileItem._record:
                                fileItem._record._dirty = True
                                fileItem._record.changed = True
                            messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                                                           u'Подписание',
                                                           u'Документ подписан успешно',
                                                           QtGui.QMessageBox.Ok)
                            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
                            messageBox.exec_()
                        else:
                            messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                                                           u'Ошибка подписания документа',
                                                           u'Документ уже подписан или владелец '
                                                           u'ЭЦП отсутствует среди участников',
                                                           QtGui.QMessageBox.Close)
                            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
                            messageBox.exec_()
                    else:
                        QtGui.QMessageBox.warning(self,
                                                  u'Внимание!',
                                                  u'Подписать документ могут только его участники.',

                                                  QtGui.QMessageBox.Ok,
                                                  QtGui.QMessageBox.Ok)


                except Exception, e:
                    QtGui.QMessageBox.information(self, u'Ошибка получения сертификата', anyToUnicode(e.message),
                                                  QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)

            except Exception, e:
                messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                                               u'Ошибка подписания документа',
                                               anyToUnicode(e.message),
                                               QtGui.QMessageBox.Close)
                messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
                messageBox.exec_()

    def getAvailableSigner(self, fileItem, snils):
        db = QtGui.qApp.db
        attachRecord = fileItem.getRecord(db.table('Action_FileAttach'))

        tableName = 'Action_FileAttach'
        table = db.table(tableName)
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableQuery = table
        tableQuery = tableQuery.leftJoin(tableAction, tableAction['id'].eq(table['master_id']))
        cond = db.joinAnd(
            [table['id'].eq(attachRecord.value('id')), table['deleted'].eq(0),
             table['respSigner_id'].isNotNull()])

        tableQuery = tableQuery.leftJoin(tableActionType,
                                         tableActionType['id'].eq(tableAction['actionType_id']))
        tableQuery = tableQuery.leftJoin(db.table('ActionPropertyType').alias('apt'),
                                         'ActionType.id = apt.actionType_id AND apt.typeName="Person" ')
        tableQuery = tableQuery.leftJoin(db.table('ActionProperty').alias('ap'),
                                         'Action.id = ap.action_id AND apt.id = ap.type_id ')
        tableQuery = tableQuery.leftJoin(db.table('ActionProperty_Person').alias('app'), 'ap.id = app.id ')
        tableQuery = tableQuery.leftJoin(db.table('Person'), 'app.value=Person.id ')

        cond += " and Person.SNILS = '%s' and app.id is not null" % snils
        cond += " AND ap.deleted=0 AND apt.deleted=0 AND Action.deleted=0 AND ActionType.deleted=0 " \
                "AND Person.deleted=0 and NOT EXISTS(SELECT 1 FROM Action_FileAttach_Signature afas " \
                "WHERE afas.master_id = Action_FileAttach.id AND afas.signer_id=app.value)"

        cols = [table['id'],
                table['createDatetime'],
                table['createPerson_id'],
                table['modifyPerson_id'],
                table['deleted'],
                table['master_id'],
                table['path'],
                table['respSignatureBytes'],
                table['respSigner_id'],
                table['respSigningDatetime'],
                table['orgSignatureBytes'],
                table['orgSigner_id'],
                table['orgSigningDatetime'],
                db.table('Person')['id'].alias('sig')
                ]
        records = db.getRecordList(tableQuery, cols, cond)
        return records


    @pyqtSignature('')
    def on_actAdd_triggered(self):
        if self.canAdd():
            self.selectAndUploadFiles()


    @pyqtSignature('')
    def on_actRename_triggered(self):
        fileItem = self.getCurrentFileItem()
        fileOk = bool(fileItem) and not fileItem.isLost
        if fileOk and self.canRename(fileItem):
            self.renameFile(fileItem)


    @pyqtSignature('')
    def on_actComment_triggered(self):
        fileItem = self.getCurrentFileItem()
        fileOk = bool(fileItem) and not fileItem.isLost
        if fileOk and self.canRename(fileItem):
            self.editComment(fileItem)


    @pyqtSignature('')
    def on_actDelete_triggered(self):
        for fileItem in self.selectedItems():
            if fileItem and self.canDelete(fileItem):
               self.deleteFile(fileItem)


    @staticmethod
    def __signAsResp(model, row, fileItem):
        api = MSCApi(QtGui.qApp.getCsp())
        userCert = QtGui.qApp.getUserCert(api)

        interface = model.interface
        fileBytes = interface.downloadBytes(fileItem)
        signatureBytes = userCert.createDetachedSignature(fileBytes)
        fileItem.setRespSignature(signatureBytes, QtGui.qApp.userId, QDateTime.currentDateTime())
        if fileItem._record:
            fileItem._record._dirty = True
            fileItem._record.changed = True
        model.touchRow(row)


    @staticmethod
    def __signAsOrg(model, row, fileItem):
        api = MSCApi(QtGui.qApp.getCsp())
        orgCert = QtGui.qApp.getOrgCert(api)

        interface = model.interface
        fileBytes = interface.downloadBytes(fileItem)
        signatureBytes = orgCert.createDetachedSignature(fileBytes)
        fileItem.setOrgSignature(signatureBytes, QtGui.qApp.userId, QDateTime.currentDateTime())
        if fileItem._record:
            fileItem._record._dirty = True
            fileItem._record.changed = True
        model.touchRow(row)



    @pyqtSignature('')
    def on_actSignAsResp_triggered(self):
        model = self.model()
        modelIndex = self.currentIndex()
        if not modelIndex.isValid():
            return

        row = modelIndex.row()
        fileItem = model.items[row]
        fileOk = bool(fileItem) and not fileItem.isLost
        if fileOk and self.canSignAsResp(fileItem):
            # список документов может быть показан непосредственно или как часть popup окна.
            # при вызове crypoapi библиотеки Крипто-Про показывают диалог аутентификации.
            # показ диалога аутентификации Крипто-Про из popup у меня (kde5) приводит к зависанию оконного менеджера.
            # для решения делаем "коленце" - выделяем код подписания в функцию, которая будет вызвана
            # после закрытия popup
            ofr = self.widgetForFileDialog()
            if ofr == self:
                QtGui.qApp.call(self, self.__signAsResp, (model, row, fileItem))
            else:
                QTimer.singleShot(0, lambda: QtGui.qApp.call(ofr, self.__signAsResp, (model, row, fileItem)))
                self.window().close()


    @pyqtSignature('')
    def on_actSignAsOrg_triggered(self):
        model = self.model()
        modelIndex = self.currentIndex()
        if not modelIndex.isValid():
            return

        row = modelIndex.row()
        fileItem = model.items[row]
        fileOk = bool(fileItem) and not fileItem.isLost
        if fileOk and self.canSignAsOrg(fileItem):
            # список документов может быть показан непосредственно или как часть popup окна.
            # при вызове crypoapi библиотеки Крипто-Про показывают диалог аутентификации.
            # показ диалога аутентификации Крипто-Про из popup у меня (kde5) приводит к зависанию оконного менеджера.
            # для решения делаем "коленце" - выделяем код подписания в функцию, которая будет вызвана
            # после закрытия popup
            ofr = self.widgetForFileDialog()
            if ofr == self:
                QtGui.qApp.call(self, self.__signAsOrg, (model, row, fileItem))
            else:
                QTimer.singleShot(0, lambda: QtGui.qApp.call(ofr, self.__signAsOrg, (model, row, fileItem)))
                self.window().close()



def convertSignatureToCMS(signatureBytes):
    max_count = 64  # 64 символа на одну строку
    data = b64encode(signatureBytes)
    lines = [data[i - max_count:i] for i in xrange(max_count, len(data) + max_count, max_count)]
    return '-----BEGIN CMS-----\r\n' + '\r\n'.join(lines) + '\r\n-----END CMS-----\r\n'
