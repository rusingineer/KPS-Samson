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
## Разнообразные утилиты для работы с DOM
##
#############################################################################

#from ZSI.wstools.c14n import Canonicalize
#from c14n import Canonicalize
#from c14n import exclusiveC14N


def verifyAttributeValue(node, namespaceURI, localName, expectedValue):
    value = getAttributeValue(node, namespaceURI, localName)
    if value != expectedValue:
        raise Exception(u'В элементе %s атрибут {%s}:%s имеет неожиданное значение «%s», ожидалось %r' % (getElementPath(node), namespaceURI, localName, value, expectedValue))

def verifyAttributeValueSet(node, namespaceURI, localName, expectedValues):
    value = getAttributeValue(node, namespaceURI, localName)
    if value not in expectedValues:
        raise Exception(u'В элементе %s атрибут {%s}:%s имеет неожиданное значение «%s», ожидалось одно из %r' % (getElementPath(node), namespaceURI, localName, value, expectedValues))


def getAttributeValue(node, namespaceURI, localName):
    value = node.getAttributeNS(namespaceURI, localName)
    if not value:
        raise Exception(u'В элементе %s не найден атрибут {%s}:%s' % (getElementPath(node), namespaceURI, localName))
    return value


def getElement(node, namespaceURI, localName):
    for childNode in node.childNodes:
        if (     childNode.nodeType == childNode.ELEMENT_NODE
             and (namespaceURI is None or childNode.namespaceURI == namespaceURI)
             and childNode.localName == localName
           ):
            return childNode
    raise Exception(u'В элементе %s не найден элемент {%s}:%s' % (node.tagName, namespaceURI, localName))


def getElements(node, namespaceURI, localName):
    return [childNode
            for childNode in node.childNodes
            if (     childNode.nodeType == childNode.ELEMENT_NODE
                 and (namespaceURI is None or childNode.namespaceURI == namespaceURI)
                 and childNode.localName == localName
               )
           ]


def getDecodedText(node):
    text = ''.join(childNode.data for childNode in node.childNodes if childNode.TEXT_NODE)
    try:
        result = text.decode('base64')
    except:
        raise Exception(u'не удалось декодировать элемент %s' % getElementPath(node) )
    if not result:
        raise Exception(u'элемент %s пуст' % getElementPath(node) )
    return result


def getElementPath(node):
    parts = []
    while node:
        parts.append(node.localName)
        node = node.parentNode
        if node and node.nodeType == node.DOCUMENT_NODE:
            node = None
    parts.append('')
    return '/'.join( reversed(parts) )



#def exclusiveC14N(node):
#    return Canonicalize(node, unsuppressedPrefixes=[]).encode('utf-8')


def findElementsWithAttributeValue(node, namespaceURI, localName, value):
    result = []

    def iter(node):
        if node.getAttributeNS(namespaceURI, localName) == value:
            result.append(node)
        for childNode in node.childNodes:
            if childNode.nodeType == childNode.ELEMENT_NODE:
                iter(childNode)

    iter(node)
    return result
