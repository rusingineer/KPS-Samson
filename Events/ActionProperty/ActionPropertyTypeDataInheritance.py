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

import re

from PyQt4 import QtGui


class CActionPropertyTypeDataInheritance(object):
    in_prefix = u'in_'
    out_prefix = u'out_'
    property_prefix = u'property.'
    reProperty = u'%s\w+' % property_prefix
    action_prefix = u'action.'
    reAction = u'%s\w+' % action_prefix
    reTitle = u'%s|%s' % (reProperty, reAction)
    reBrackets = u'(?<=\[)(.*?)(?=\])'

    def __init__(self, parent):
        self._dataInheritance = parent.dataInheritance
        self._incomingSequence = []
        self._outgoingSequence = []
        self.incoming = set()
        self.outgoing = set()
        if QtGui.qApp.checkGlobalPreference(u'23:DataInheritanceByModel', u'да') and self._dataInheritance:
            if self._dataInheritance:
                self.__parceDataInheritance(self.in_prefix)
                self.__parceDataInheritance(self.out_prefix)

    def isSimple(self):
        return len(self._incomingSequence) == 1 and not self._incomingSequence[0].title()

    def __parceDataInheritance(self, prefix):
        '''
            ввод. строка вида
            [0..1][список заголовков 1][1..1][список полей 1], ... [0..1][список заголовков n][1..1][список полей n]
            Ex:
            [property.name][in_zhivot,in_matka,in_polpl,in_predlezh,in_chast,in_serdce]
            in_zhivot,in_matka
            [in_zhivot,in_matka,in_polpl,in_predlezh,in_chast,in_serdce]
        '''
        reDest = u'%s\w+' % prefix
        if re.search(reDest, self._dataInheritance):
            title = []
            dataList = re.findall(self.reBrackets, self._dataInheritance)
            for idx, tmpData in enumerate(dataList or [self._dataInheritance]):
                if re.search(self.reTitle, tmpData):
                    title = re.findall(self.reTitle, tmpData)
                else:
                    for name in map(lambda x: re.sub('^' + prefix, '', x), re.findall(reDest, tmpData)):
                        if prefix == self.in_prefix:
                            self._incomingSequence.append(CActionPropertyTypeDataInheritanceItem(title, name))
                            self.incoming.add(name)
                        elif prefix == self.out_prefix:
                            self._outgoingSequence.append(CActionPropertyTypeDataInheritanceItem([], name))
                            self.outgoing.add(name)
                    title = []

    def getIncomingSequence(self):
        return self._incomingSequence

    def getOutgoingSequence(self):
        return self._outgoingSequence


class CActionPropertyTypeDataInheritanceItem(object):
    is_property = 1
    is_action = 2

    def __init__(self, title, name):
        self._title = []
        self._name = name
        self._hasAction = False
        self.initTitle(title)

    def initTitle(self, title):
        for val in title:
            if re.search(CActionPropertyTypeDataInheritance.reProperty, val):
                self._title.append(
                    (self.is_property, re.sub('^' + CActionPropertyTypeDataInheritance.property_prefix, '', val)))
            elif re.search(CActionPropertyTypeDataInheritance.reAction, val):
                self._title.append(
                    (self.is_action, re.sub('^' + CActionPropertyTypeDataInheritance.action_prefix, '', val)))
                self._hasAction = True

    def title(self):
        return self._title

    def name(self):
        return self._name

    def hasAction(self):
        return self._hasAction

    def formatTitle(self, sourceActionInfo, sourcePropertyType):
        val = ''
        try:
            for item in self._title:
                # Есть ощущение, что для property используется только name
                # if item[0] == self.is_property:
                #     prop = sourceActionInfo[sourcePropertyType.name]
                #     if hasattr(prop, item[1]):
                #         val += (' ' if val else '') + getattr(prop, item[1])
                # elif item[0] == self.is_action:
                #     if hasattr(sourceActionInfo, item[1]):
                #         val += (' ' if val else '') + getattr(sourceActionInfo, item[1])
                if item[0] == self.is_property:
                    source = sourcePropertyType
                elif item[0] == self.is_action:
                    source = sourceActionInfo
                if hasattr(source, item[1]):
                    val += (' ' if val else '') + getattr(source, item[1])
        except:
            QtGui.qApp.logCurrentException()
        return val
