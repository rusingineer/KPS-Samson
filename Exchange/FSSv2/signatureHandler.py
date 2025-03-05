# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2017-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Handler подписывающий сообщение и проверяющий подпись
##
#############################################################################


from base64                 import b64encode

from ZSI                    import ParsedSoap, SoapWriter
from ZSI.wstools.Utility    import ElementProxy
from ZSI.wstools.Namespaces import DSIG, OASIS, SOAP

from library.MSCAPI.oids   import (
                                    getHashOidByKeyOid,
                                    getSignOidByKeyOid,
                                  )
from library.MSCAPI.xmlsig import (
                                    getHashUriByOid,
                                    getHashOidByUri,
                                    getSignUriByOid,
                                    getSignOidByUri,
                                  )

from c14n                  import exclusiveC14N
from domUtils              import (
                                    verifyAttributeValue,
                                    verifyAttributeValueSet,
                                    getAttributeValue,
                                    getElement,
                                    getElements,
                                    getDecodedText,
                                    getElementPath,
                                    findElementsWithAttributeValue,
                                  )


class CSignatureHandler(object):
    OASIS_X509v3TOKEN           = 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3'
    C14N_EXCLUSIVE_WITHCOMMENTS = 'http://www.w3.org/2001/10/xml-exc-c14n#WithComments'
    C14N_EXCLUSIVE              = 'http://www.w3.org/2001/10/xml-exc-c14n#'
    # SIGN_GOSTR34102001          = 'http://www.w3.org/2001/04/xmldsig-more#gostr34102001-gostr3411'
    # HASH_GOSTR341194            = 'http://www.w3.org/2001/04/xmldsig-more#gostr3411'
    FSSSIG                      = 'urn:ru:fss:integration:types:signature:v01'
    FSSMCHD                     = 'urn:ru:fss:integration:types:mchd:v01'

    def __init__(self, api, userCert, actorUri, signBody, signElementId, mchd=None):
        assert userCert is not None, u'Должно быть задано userCert'
        assert isinstance(actorUri, basestring) and actorUri, u'Должно быть задано actorUri'
        assert isinstance(signBody, bool),  u'Должно быть задано signBody'
        assert isinstance(signElementId, basestring) and signElementId, u'Должно быть задано signElementId'

        self.api = api
        self.userCert = userCert
        self.actorUri = actorUri
        self.signBody = signBody
        self.signElementId = signElementId
        self.mchd = mchd
        self.saveParts = False # for debug


    def sign(self, sw):
        assert isinstance(sw, SoapWriter)

        header   = sw._header
        body     = sw.body

        if self.signBody:
            self._setWsuId(body, self.signElementId)

        self._signItem(header, body, self.signElementId, self.actorUri)

#        print '='*80
#        print sw
#        exit(1)


    def verify(self, ps):
        assert isinstance(ps, ParsedSoap)

        for headerElement in ps.header_elements:
            if (headerElement.namespaceURI, headerElement.localName) == (OASIS.WSSE, 'Security'):
                self._verifySignature(headerElement, ps.body)


#        exit(1)


    #########################################################################
    # for sign ##############################################################
    #########################################################################

#    def _addNSs(self, ep):
#        ep.setNamespaceAttribute('ds',   DSIG.BASE)
#        ep.setNamespaceAttribute('wsse', OASIS.WSSE)
#        ep.setNamespaceAttribute('wsu',  OASIS.UTILITY)


    def _setWsuId(self, ep, wsuId):
        ep.setAttributeNS(OASIS.UTILITY, 'Id', wsuId)


    def _signItem(self, header, body, wsuId, actorUri, powerOfAttorneyId=None):
        signable = self._findElementWithWsuId(body, wsuId)
        canonicalized = exclusiveC14N(signable.node)

        binarySecurityToken, digestValue, signedInfo, signatureValue = self._addSecurityElement(header, wsuId, actorUri, powerOfAttorneyId)

        with self.userCert.provider() as provider:
            certBytes = self._getCertBytes(provider)
            binarySecurityToken.createAppendTextNode(b64encode(certBytes))

#            if self.saveParts:
#                file('for.hash.' + wsuId, 'w').write(canonicalized)
            digest = self._hash(provider, canonicalized)
            digestValue.createAppendTextNode(b64encode(digest))

            canonicalizedSignedInfo = exclusiveC14N(signedInfo.node)
#            if self.saveParts:
#                file('for.sign.' + wsuId, 'w').write(canonicalizedSignedInfo)
            signature = self._sign(provider, canonicalizedSignedInfo)
            signatureValue.createAppendTextNode(b64encode(signature))


    def _findElementWithWsuId(self, ep, wsuId):
        nodes = findElementsWithAttributeValue(ep.node, OASIS.UTILITY, 'Id', wsuId)
        if len(nodes) == 0:
            raise Exception('Sign failure: element with wsu:Id="%s" not found' % wsuId)
        if len(nodes) > 1:
            raise Exception('Sign failure: too many elements with wsu:Id="%s" not found' % wsuId)
        return ElementProxy(ep.sw, nodes[0])


    def _addSecurityElement(self, container, wsuId, actorUri, powerOfAttorneyId=None):
        keyOid = self.userCert.keyOid()
        hashOid = getHashOidByKeyOid(keyOid)
        hashUri = getHashUriByOid(hashOid)
        signOid = getSignOidByKeyOid(keyOid)
        signUri = getSignUriByOid(signOid)

        security = container.createAppendElement(OASIS.WSSE, 'Security')
        security.setAttributeNS(SOAP.ENV, 'actor', actorUri)

        binarySecurityToken = security.createAppendElement(OASIS.WSSE, 'BinarySecurityToken')
        binarySecurityToken.setAttributeNS(None,          'EncodingType', OASIS.X509TOKEN.Base64Binary)
        binarySecurityToken.setAttributeNS(None,          'ValueType',    self.OASIS_X509v3TOKEN)
        binarySecurityToken.setAttributeNS(OASIS.UTILITY, 'Id',           actorUri)

        signature = security.createAppendElement(DSIG.BASE, 'Signature')

        signedInfo = signature.createAppendElement(DSIG.BASE, 'SignedInfo')
        canonicalizationMethod = signedInfo.createAppendElement(DSIG.BASE, 'CanonicalizationMethod')
        canonicalizationMethod.setAttributeNS(None, 'Algorithm', self.C14N_EXCLUSIVE)
        signatureMethod = signedInfo.createAppendElement(DSIG.BASE, 'SignatureMethod')
        signatureMethod.setAttributeNS(None, 'Algorithm', signUri)

        reference = signedInfo.createAppendElement(DSIG.BASE, 'Reference')
        reference.setAttributeNS(None, 'URI', '#' + wsuId)
        transforms = reference.createAppendElement(DSIG.BASE, 'Transforms')
        transform = transforms.createAppendElement(DSIG.BASE, 'Transform')
        transform.setAttributeNS(None, 'Algorithm', self.C14N_EXCLUSIVE)
        digestMethod = reference.createAppendElement(DSIG.BASE, 'DigestMethod')
        digestMethod.setAttributeNS(None, 'Algorithm', hashUri)
        digestValue = reference.createAppendElement(DSIG.BASE, 'DigestValue')

        signatureValue = signature.createAppendElement(DSIG.BASE, 'SignatureValue')
        keyInfo = signature.createAppendElement(DSIG.BASE, 'KeyInfo')
        securityTokenReference = keyInfo.createAppendElement(OASIS.WSSE, 'SecurityTokenReference')
        reference = securityTokenReference.createAppendElement(OASIS.WSSE, 'Reference')
        reference.setAttributeNS(None, 'ValueType', self.OASIS_X509v3TOKEN)
        reference.setAttributeNS(None, 'URI', '#' + actorUri)

        if self.mchd:
            dsObject = signature.createAppendElement(DSIG.BASE, 'object')
            authority = dsObject.createAppendElement(self.FSSSIG, 'authority')
            powerOfAttorneyLink = authority.createAppendElement(self.FSSMCHD, 'powerOfAttorneyLink')
            uuid = powerOfAttorneyLink.createAppendElement(self.FSSMCHD, 'uuid')
            uuid.createAppendTextNode(self.mchd)

        # if powerOfAttorneyId:
        #     object_ = signature.createAppendElement(DSIG.BASE, 'Object')
        #     authority = object_.createAppendElement(self.urnFssSignature, 'authority')
        #     authority.setNamespaceAttribute('fssSignature', self.urnFssSignature)
        #     authority.setNamespaceAttribute('fssPoa',       self.urnFssPowerOfAttorney)
        #     powerOfAttorneyLink = authority.createAppendElement(self.urnFssPowerOfAttorney, 'powerOfAttorneyLink')
        #     uuid = powerOfAttorneyLink.createAppendElement(self.urnFssPowerOfAttorney, 'uuid')
        #     uuid.createAppendTextNode(powerOfAttorneyId)

        return ( binarySecurityToken,
                 digestValue,
                 signedInfo,
                 signatureValue,
               )


    def _getCertBytes(self, provider):
        return self.userCert.encoded()


    def _hash(self, provider, string):
        keyOid = self.userCert.keyOid()
        hashOid = getHashOidByKeyOid(keyOid)
        with provider.hash(algId=self.api.getHashAlgIdByOid(hashOid)) as h:
            h.update(string)
            return h.digest()


    def _sign(self, provider, string):
        keyOid = self.userCert.keyOid()
        hashOid = getHashOidByKeyOid(keyOid)
        with provider.hash(algId=self.api.getHashAlgIdByOid(hashOid)) as h:
            h.update(string)
            signature = h.sign(self.api.AT_KEYEXCHANGE)
            return signature[::-1]


    #########################################################################
    # for verify ############################################################
    #########################################################################

    def _verifySignature(self, security, body):
        api = self.api

        actorUri = getAttributeValue(security, SOAP.ENV, 'actor')
        binarySecurityToken = getElement( security, OASIS.WSSE, 'BinarySecurityToken')
        verifyAttributeValue(binarySecurityToken, None, 'EncodingType', OASIS.X509TOKEN.Base64Binary)
        verifyAttributeValue(binarySecurityToken, None, 'ValueType',    self.OASIS_X509v3TOKEN)
        certBytes = getDecodedText(binarySecurityToken)
        with api.cert(certBytes) as cert:
            signature = getElement(security, DSIG.BASE, 'Signature')
            signedInfo = getElement(signature, DSIG.BASE, 'SignedInfo')
            canonicalizationMethod = getElement(signedInfo, DSIG.BASE, 'CanonicalizationMethod')
            verifyAttributeValueSet(canonicalizationMethod, None, 'Algorithm', (self.C14N_EXCLUSIVE_WITHCOMMENTS, self.C14N_EXCLUSIVE))

            signatureMethod = getElement(signedInfo, DSIG.BASE, 'SignatureMethod')
            signUri = getAttributeValue(signatureMethod, None, 'Algorithm')
            signOid = getSignOidByUri(signUri)
            if signOid != getSignOidByKeyOid(cert.keyOid()):
                raise Exception(u'%s.Algorithm не соответствует сертификату' % getElementPath(signatureMethod))

            reference = getElement(signedInfo, DSIG.BASE, 'Reference')
            uri = getAttributeValue(reference, None, 'URI')
            if not uri.startswith('#') or len(uri)<=1:
                raise Exception(u'элемент %s имеет неправильное значение атрибута %s' % (getElementPath(reference), 'URI'))
            signableId = uri[1:]

            transforms = getElement(reference, DSIG.BASE, 'Transforms')
            transformList = getElements(transforms, DSIG.BASE, 'Transform')
            if len(transformList) != 1:
                raise Exception(u'контейнер %s имеет имеет неправильное количество элементов %s' % (getElementPath(transforms), 'Transform'))
            verifyAttributeValueSet(transformList[0], None, 'Algorithm', (self.C14N_EXCLUSIVE_WITHCOMMENTS, self.C14N_EXCLUSIVE))

            digestMethod = getElement(reference, DSIG.BASE, 'DigestMethod')
            hashUri = getAttributeValue(digestMethod, None, 'Algorithm')
            hashOid = getHashOidByUri(hashUri)
            if hashOid != getHashOidByKeyOid(cert.keyOid()):
                raise Exception(u'%s.Algorithm не соответствует сертификату' % getElementPath(digestMethod))

            digestValue = getDecodedText(getElement(reference, DSIG.BASE,'DigestValue'))
            signatureValue = getDecodedText(getElement(signature, DSIG.BASE, 'SignatureValue'))[::-1]

            keyInfo = getElement(signature, DSIG.BASE, 'KeyInfo')
            securityTokenReference = getElement(keyInfo, OASIS.WSSE, 'SecurityTokenReference')
            reference =  getElement(securityTokenReference, OASIS.WSSE, 'Reference')

            if getAttributeValue(reference, None, 'URI') != '#' + actorUri:
                raise Exception(u'элемент %s имеет неправильное значение атрибута %s' % (getElementPath(reference), 'URI'))

            # 2024-12-11: сервер не передаёт ValueType, ну да нам не очень-то и нужно...
            # verifyAttributeValue(reference, None, 'ValueType', self.OASIS_X509v3TOKEN)

            signables = findElementsWithAttributeValue(body, OASIS.UTILITY, 'Id', signableId)
            if not signables:
                raise Exception(u'элемент с атрибутом {%s}:Id="%s" не найден' % (OASIS.UTILITY, signableId))
            if len(signables)>1:
                raise Exception(u'найдено несколько элементов с атрибутом {%s}:Id="%s" не найден' % (OASIS.UTILITY, signableId))

            signable = signables[0]
            signableXml = exclusiveC14N(signable)

            with api.provider(flags=api.CRYPT_VERIFYCONTEXT, providerType=api.getProviderTypeByKeyOid(cert.keyOid())) as provider:
                with provider.hash(algId=api.getHashAlgIdByOid(hashOid)) as h:
                    h.update(signableXml)
                    if h.digest() != digestValue:
                        raise Exception(u'значение хэш для элемента %s не совпало с указанным' % getElementPath(signable))

                with provider.importPubKeyfromCert(cert) as pubKey:
                    with provider.hash(algId=api.getHashAlgIdByOid(hashOid)) as h:
                        h.update(exclusiveC14N(signedInfo))
                        if not h.verifySignature(signatureValue, pubKey):
                            raise Exception(u'подпись для элемента %s не совпала с указанной' % getElementPath(signable))

        return signableId, actorUri, signable

