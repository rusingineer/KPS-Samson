# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2016-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from base64 import b64encode

from PyQt4 import QtGui

from library.MSCAPI import MSCApi
from library.Utils import forceString
from library.userCertPlate import CCertInfoPlate

from Orgs.Utils import getOrgNameBySnils


def getAttachCerts(signatureBytes):
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
                orgName = getOrgNameBySnils(snils)

            resolutionScale = 4.0 # настоящий размер/четкость картинки
            plate = CCertInfoPlate.fromCert(cert, orgName=orgName, scale=resolutionScale)
            imgScale = 0.7 # уменьшаем в документе, чтобы помещалось 2 штуки в страницу A4
            imgWidth = int(plate.originalSize.width() * imgScale)
            imgHeight = int(plate.originalSize.height() * imgScale)
            imageString = u'<img src="data:image/png;base64,{0}" width="{1}" height="{2}">'.format(b64encode(plate.bytes), imgWidth, imgHeight)
            imageList.append(imageString)
    return imageList


def prepareSignedReport(html, resp_signatures, org_signature):
    listCert = []
    if u'<!--sign_' in html:
        org_signatureBytes = None
        api = MSCApi(QtGui.qApp.getCsp())

        if org_signature:
            org_signatureBytes = getAttachCerts(org_signature)

        for signBytes in resp_signatures:
            imageList = getAttachCerts(signBytes)
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
        listCert = ['</body><br>']
        for signBytes in resp_signatures:
            imageList = getAttachCerts(signBytes)
            for image in imageList:
                if image != '</body><br>':
                    listCert.append(image)
        if org_signature:
            org_signatureBytes = getAttachCerts(org_signature)
            if org_signatureBytes:
                listCert.append(org_signatureBytes[0])

        imageString = u' '.join([u'<br>'] + listCert) 
        html = html.replace('<!---->', '')
        html = u'{0} {1}'.format(html, imageString)
    return html


def convertSignatureToCMS(signatureBytes):
    max_count = 64  # 64 символа на одну строку
    data = b64encode(signatureBytes)
    lines = [data[i - max_count:i] for i in xrange(max_count, len(data) + max_count, max_count)]
    return '-----BEGIN CMS-----\r\n' + '\r\n'.join(lines) + '\r\n-----END CMS-----\r\n'
