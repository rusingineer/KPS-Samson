# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import re
from string import letters

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from library.Utils import forceString
from library.MultivalueComboBox import CBaseMultivalue
from library.ROComboBox import CROComboBox


class CStrComboBox(CBaseMultivalue, CROComboBox):
    def __init__(self, parent=None):
        CROComboBox.__init__(self, parent)
        CBaseMultivalue.__init__(self, multivalue=False)
        self.setDuplicatesEnabled(True)
        self._variants = []
        self._regexps  = []
        self._methodsNames = {'mc' : (self.setMultivalueChecking, (True, ))}
        self.installEventFilter(self)


    def setDomain(self, domain, isUpdateCurrIndex=True):
        self.clear()
        self._variants, self._regexps, err, methodsItems = self._parse(domain)
        for variant in self._variants:
            self.addItem(variant)
        self.setEditable(bool(self._regexps))
        for method, args in methodsItems:
            method(*args)
        if isUpdateCurrIndex:
            self.setCurrentIndex(0)


    def _parse(self, domain):
        return CStrComboBox.parse(domain, self._methodsNames)


    def setValue(self, value):
        if self.isCheckedColumnIsHiden():
            text = forceString(value)
            if self.isEditable():
                index = self.findText(text, Qt.MatchStartsWith)
                self.setCurrentIndex(index)
                self.setEditText(text)
            else:
                index = self.findText(text, Qt.MatchFixedString)
                self.setCurrentIndex(index)
        else:
            CBaseMultivalue.setValue(self, value)


    def text(self):
        return unicode(self.currentText())


    value = text


    def canMatch(self, text):
        for regexp in self._regexps:
            if re.match(regexp, text, re.I):
                return True
        return False


    def setEditText(self, text):
        t = forceString(text)
        if self.isCheckedColumnIsHiden():
            if t in self._variants or self.canMatch(t):
                CROComboBox.setEditText(self, t)
        else:
            CROComboBox.setEditText(self, t)


    @staticmethod
    def parse(definition, methodNames={}):
        def appendUnique(target, str):
            if str not in target:
                target.append(str)

        variants      = []
        regexps       = []
        methodsItems  = []
        err           = False
        state         = 0
        method        = ''

        if u'_urn_' in definition:
            for word in definition.split(','):
                parts = word.split('_urn_')
                if len(parts) == 2:
                    key, val = parts[0].strip(), parts[1].strip()
                    data = None
                elif len(parts) == 3:
                        key, val, data = parts[0].strip(), parts[1].strip(), parts[2].strip()
                else:
                    raise ValueError, self.badDomain % locals()
                keylower = key
                vallower = val

                db = QtGui.qApp.db
                table = db.table(keylower+'_Identification')
                cond = []
                cond.append('deleted = 0')
                cond.append(table['master_id'].eq(QtGui.qApp.currentOrgId()))
                tableNet = db.table('rbAccountingSystem')
                netIdList = db.getIdList(tableNet, 'id', tableNet['urn'].eq(vallower))
                cond.append(table['system_id'].inlist(netIdList))
                values = db.getRecordEx(table, 'value', cond)
                if values:
                    value = forceString(values.value('value'))
                    if data:
                        if 'R' in data or 'r' in data:
                            value = value + QtCore.QDate.currentDate().toString(QtCore.QDate.currentDate().toString(data.replace('R', '').replace('r', '')))
                        elif 'L' in data or 'l' in data:
                            value = QtCore.QDate.currentDate().toString(QtCore.QDate.currentDate().toString(data.replace('L', '').replace('L', ''))) + value
                        else:
                            return [value], [], False, []
                        return [value], [], False, []
                    else:
                        return [value], [], False, []
                else:
                    return [u'Указанная в настройке идентификация не найдена "' + vallower + '"'], [], False, []
        else:
            for c in definition:
                if state == 0: # base state
                    if c == '"' or c == "'":
                        q = c
                        state = 2
                        a = ''
                        target = variants # variant string
                    elif c == '*':
                        appendUnique(regexps, '.*')
                        state = 3
                    elif c == 'r':
                        state = 1
                    elif c == ' ':
                        pass
                    elif c == '[':
                        state = 5
                        err = True
                    elif c == ']':
                        err = False
                    else:
                        err = True
                        break
                elif state == 1: # awaiting quote in regexp
                    if c == '"' or c == "'":
                        q = c
                        state = 2
                        a = ''
                        target = regexps # regexp mode
                    else:
                        err = True
                        break
                elif state == 2: # string input mode
                    if c == '\\':
                        state = 3
                    elif c == q:
                        appendUnique(target, a)
                        state = 4
                    else:
                        a += c
                elif state == 3: # back slashed char
                    a += c
                    state = 2
                elif state == 4: # string finished, awaiting comma or EOS
                    if c == ',':
                        state = 0
                    elif c == ' ':
                        pass
                    else:
                        err = True
                        break
                elif state == 5:
                    if c in letters:
                        method += c
                        if method in methodNames:
                            methodsItems.append(methodNames[method])
                            method = ''
                            state  = 0
                else:
                    err = True
                    break

            if state != 0 and state != 4:
                err = True
            return variants, regexps, err, methodsItems


    def keyPressEvent(self, event):
        if self.model().isReadOnly():
            event.accept()
        elif event.key() in (Qt.Key_Enter, Qt.Key_Return):
            event.accept()
        else:
            QtGui.QComboBox.keyPressEvent(self, event)


class CDoubleComboBox(CStrComboBox):
    def __init__(self, parent=None):
        CStrComboBox.__init__(self, parent)

    def _parse(self, domain):
        return self.parse(domain)

    def value(self):
        return self.currentText()

    def setDomain(self, domain):
        CStrComboBox.setDomain(self, domain)
        if self.isEditable():
            validator = QtGui.QDoubleValidator(self)
            self.lineEdit().setValidator(validator)


    def parse(self, definition):
        variants     = []
        regexps      = []
        methodsItems = []
        err          = False
        state        = None
        dote         = False
        method       = ''

        for c in definition:
            if state is None and c == '{':
               continue
            if state is None:
                state = 1 # working state
                a = ''
            elif state:
                if c == '{':
                    state = 0 # not working state
                    err = True
                elif c == '}':
                    state = 2 # end state


            if state == 1:
                if c == ' ':
                    pass
                elif c == '[':
                    state = 3
                    err = True
                elif c == ']':
                    err = False
                elif c == ';':
                    if a:
                        variants.append(a)
                    a = ''
                    dote = False
                elif c.isdigit() or c == '-':
                    a += c
                elif c  == '.':
                    if dote:
                        state = 0
                        err = True
                    dote = True
                    a += c
                elif c == '*':
                    regexps.append('.*')
                else:
                    state = 0
                    err = True

            elif state == 2:
                if a and a.replace('-', '').isdigit():
                    variants.append(a)
                    state = 0

            elif state == 3:
                if c in letters:
                    method += c
                    if method in self._methodsNames:
                        methodsItems.append(self._methodsNames[method])
                        method = ''
                        state  = 1

        if not err and state == 1:
            if a and a.replace('-', '').isdigit():
                variants.append(a)

        return variants, regexps, err, methodsItems


class CIntComboBox(CStrComboBox):
    def __init__(self, parent=None):
        CStrComboBox.__init__(self, parent)

    def _parse(self, domain):
        return self.parse(domain)

    def value(self):
        return self.currentText()

    def setDomain(self, domain):
        CStrComboBox.setDomain(self, domain)
        if self.isEditable():
            validator = QtGui.QIntValidator(self)
            self.lineEdit().setValidator(validator)


    def parse(self, definition):
        variants     = []
        regexps      = []
        methodsItems = []
        err          = False
        state        = None
        dote         = False
        method       = ''

        for c in definition:
            if state is None and c == '{':
               continue
            if state is None:
                state = 1 # working state
                a = ''
            elif state:
                if c == '{':
                    state = 0 # not working state
                    err = True
                elif c == '}':
                    state = 2 # end state

            if state == 3:
                if c == ';':
                    state = 1

            if state == 1:
                if c == ' ':
                    pass

                elif c == '[':
                    state = 3
                    err = True
                elif c == ']':
                    err = False

                elif c == ';':
                    if a:
                        variants.append(a)
                    a = ''
                    dote = False

                elif c.isdigit() or c == '-':
                    a += c

                elif c == '*':
                    regexps.append('.*')

                elif c == '.':
                    if dote:
                        state = 0
                        err = True
                    else:
                        state = 3 # wait `;` char
                        variants.append(a)
                        a = ''
                        dote = True

                else:
                    state = 0
                    err = True

            elif state == 2:
                if a and a.replace('-', '').isdigit():
                    variants.append(a)
                    state = 0

            elif state == 3:
                if c in letters:
                    method += c
                    if method in self._methodsNames:
                        methodsItems.append(self._methodsNames[method])
                        method = ''
                        state  = 1

        if not err and state == 1:
            if a and a.replace('-', '').isdigit():
                variants.append(a)

        return variants, regexps, err, methodsItems

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    cmb = CStrComboBox()
    cmb.setDomain(u'[mc]"","0","R","C","P","Pt","П","A","И","К","П/С","G"')
    cmb.setDomain(u'[mc]"","0","R","C","P","Pt","П","A","И","К","П/С","G"')
    cmb.show()
    app.exec_()


