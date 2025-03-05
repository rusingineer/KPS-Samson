# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2017-2018 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Вспомогательные функции для облегчения работы с ZSI
##
#############################################################################

import time

from PyQt4.QtCore import QDate

from ZSI                     import SoapWriter, ParsedSoap
from ZSI.wstools.Namespaces  import DSIG, OASIS
from ZSI.schema              import ElementDeclaration, LocalElementDeclaration, TypeDefinition
from ZSI.TCtimes             import gDate, gDateTime, gTime

from fixSoapEnvPrefixHandler import CFixSoapEnvPrefixHandler
from signatureHandler        import CSignatureHandler
from chainHandler            import CChainHandler
from c14n                    import exclusiveC14N


__all__ = ( 'convertISODateToTuple',
            'convertQDateToTuple',
            'convertTupleToQDate',
            'fixu',
            'getCryptoNsDict',
            'patchDateEtcFormat',
            'createPyObject',
            'serializeToXmlAndSignIt',
            'serializeAndRestore',
          )


def convertISODateToTuple(isoDate):
# '1984-03-28' -> (1984, 3, 28, 0, 0, 0, 0, 0, 0)
    t = time.strptime(isoDate, '%Y-%m-%d')
    return ( t.tm_year, t.tm_mon, t.tm_mday, 0, 0, 0, 0, 0, 0)


def convertQDateToTuple(date):
    return ( date.year(), date.month(), date.day(), 0, 0, 0, 0, 0, 0)


def convertTupleToQDate(date):
    # Note: convertTupleToQDate(None) -> None
    return QDate(date[0], date[1], date[2]) if date else None


def fixu(sou):
    # Note: fixu(None) -> None
    if isinstance(sou, str):
        return sou.decode('utf8')
    return sou

#
def createPyObject(typecodeClass):
#    print typecodeClass, issubclass(typecodeClass, TypeDefinition), issubclass(typecodeClass, (ElementDeclaration, LocalElementDeclaration))
#    print typecodeClass, typecodeClass.__module__, typecodeClass.__doc__, dir(typecodeClass)
#    for t in (TypeDefinition, ElementDeclaration, LocalElementDeclaration):
#        print t, issubclass(typecodeClass, t), t.__module__, t.__doc__
#    print 'A', issubclass(TypeDefinition, ElementDeclaration)
#    print 'B', issubclass(ElementDeclaration, TypeDefinition)
#    print 'C', TypeDefinition == ElementDeclaration
#    print issubclass

#    if issubclass(typecodeClass, TypeDefinition):
#       typecode = typecodeClass(typecodeClass.type)
#    elif issubclass(typecodeClass, (ElementDeclaration, LocalElementDeclaration)):
    typecode = typecodeClass()
#    else:
#       assert False
    patchDateEtcFormat(typecode)
    return typecode.pyclass()

#def createPyObject(typecodeClass):
#    print typecodeClass, issubclass(typecodeClass, TypeDefinition), issubclass(typecodeClass, (ElementDeclaration, LocalElementDeclaration))
#    if issubclass(typecodeClass, TypeDefinition):
#       typecode = typecodeClass(typecodeClass.type)
#    elif issubclass(typecodeClass, (ElementDeclaration, LocalElementDeclaration)):
#       typecode = typecodeClass()
#    else:
#       assert False
#    patchDateEtcFormat(typecode)
#    return typecode.pyclass()


#


def getCryptoNsDict():
    nsdict = { 'ds'  : DSIG.BASE,
               'wsse': OASIS.WSSE,
               'wsu' : OASIS.UTILITY,
             }
    return nsdict



# ZSI имеет некоторые особенности.
# Например:
#     - типы данных date, dateTime и time передаются в формате GMT (типа 2018-01-01Z или 10:00:00Z)
#       для передачи таких типов данных используется tuple, который не предусматривает передачу часового пояса.
#       мне обычно не нужно передавать часовой пояс.

def patchDateEtcFormat(typecode):
    if isinstance(typecode, gDate):
        typecode.format = '%(Y)04d-%(M)02d-%(D)02d'
    elif isinstance(typecode, gDateTime):
        typecode.format = '%(Y)04d-%(M)02d-%(D)02dT%(h)02d:%(m)02d:%(s)02d'
        typecode.format_ms = typecode.format + '.%(ms)03d'
    elif isinstance(typecode, gTime):
        typecode.format = '%(h)02d:%(m)02d:%(s)02d'
        typecode.format_ms = typecode.format + '.%(ms)03d'
    elif hasattr(typecode, 'ofwhat'):
        for element in typecode.ofwhat:
            patchDateEtcFormat(element)

# можно ещё заменить
#    def text_to_data(self, text, elt, ps):
#    def get_formatted_content(self, pyobj):


def serializeToXmlAndSignIt(api, userCert, pyobject, elementId, actorUri, customNsDict=None):
    nsdict = getCryptoNsDict()
    if customNsDict:
        nsdict = nsdict.copy()
        nsdict.update(customNsDict)
    sw = SoapWriter(nsdict=nsdict)
    pyobject.set_attribute_Id(elementId)
    sw.serialize(pyobject, pyobject.typecode, typed=False)
    handler = CChainHandler()

    handler.append( CFixSoapEnvPrefixHandler() )

    handler.append( CSignatureHandler(api,
                                      userCert = userCert,
                                      actorUri = actorUri,
                                      signBody = False,
                                      signElementId = elementId,
                                     )
                  )

    handler.sign(sw)

    data     = sw.dom.node.getElementsByTagNameNS(pyobject.typecode.schema, pyobject.typecode.pname)
    security = sw.dom.node.getElementsByTagNameNS(OASIS.WSSE, 'Security')

    assert len(data) == 1
    assert len(security) == 1

    return fixu(exclusiveC14N(data[0])), fixu(exclusiveC14N(security[0]))


def restoreFromXml(prototype, xml):
    if isinstance(xml, unicode):
        xml = xml.encode('utf8')
    ps = ParsedSoap(xml, envelope=False)
    return prototype.typecode.parse(ps.body_root, ps)


def serializeAndRestore(prototype, pyobject):
    nsdict = getCryptoNsDict()
    sw = SoapWriter(envelope=False, nsdict=nsdict)
    sw.serialize(pyobject, pyobject.typecode, typed=False)
    xml = str(sw)
    return restoreFromXml(prototype, xml)
