# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2016-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QRegExp


__all__ = [ 'CLineEditWithRegExpValidator',
            'prepareRegExp',
            'checkRegExp',
            'romanRegExp'
          ]

romanRegExp = u'(?:M{1,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})|M{0,4}(?:CM|C?D|D?C{1,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})|M{0,4}(?:CM|CD|D?C{0,3})(?:XC|X?L|L?X{1,3})(?:IX|IV|V?I{0,3})|M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|I?V|V?I{1,3}))'


def prepareRegExp(regExp):
    return QRegExp(regExp, Qt.CaseSensitive, QRegExp.RegExp2)


def checkRegExp(regExp):
    return prepareRegExp(regExp).isValid()


class CLineEditWithRegExpValidator(QtGui.QLineEdit):
    anyToRoman = { '1': 'I',  'i': 'I',  'I': 'I', u'ш': 'I', u'Ш': 'I',
                   '2': 'II',
                   '3': 'III',
                   '4': 'IV',
                   '5': 'V',  'v': 'V',  'V': 'V', u'м': 'V', u'М': 'V',
                   '6': 'VI',
                   '7': 'VII',
                   '8': 'VIII',
                   '9': 'IX',
                   '0': 'X',  'x': 'X',  'X': 'X', u'ч': 'X', u'Ч': 'X',
                              'l': 'L',  'L': 'L', u'д': 'L', u'Д': 'L',
                              'c': 'C',  'C': 'C', u'с': 'C', u'С': 'C',
                              'd': 'D',  'D': 'D', u'в': 'D', u'В': 'D',
                              'm': 'M',  'M': 'M', u'ь': 'M', u'Ь': 'M'
                 }
    rus = u'йцукенгшщзхъфывапролджэячсмитьбюё'
    eng = u'qwertyuiop[]asdfghjkl;\'zxcvbnm,.`'
    r2e = {}
    e2r = {}
    for i in range(len(rus)):
        r2e[ rus[i] ] = eng[i]
        e2r[ eng[i] ] = rus[i]

    def __init__(self, parent = None):
        QtGui.QLineEdit.__init__(self, parent)
        self.validator = None
        self.regExp = None


    def setRegExp(self, regExp):
        self.regExp = regExp
        if not regExp:
            self.validator = None
        else:
            rx = prepareRegExp(regExp)
            if not rx.isValid():
                rx = prepareRegExp('')
            self.validator = QtGui.QRegExpValidator(rx, self)
        self.setValidator(self.validator)
        self.update()


    def paintEvent(self, event):
        palette = QtGui.QPalette()
        if self.isEnabled() and not self.hasAcceptableInput():
            palette.setColor(palette.Base,      QtGui.QColor(255, 192, 192))
            palette.setColor(palette.Highlight, Qt.darkRed)
        self.setPalette(palette)
        QtGui.QLineEdit.paintEvent(self, event)
        
        
    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
                QtGui.QLineEdit.keyPressEvent(self, event)
        elif self.regExp                                          \
           and Qt.Key_Space <= event.key() < Qt.Key_Escape      \
           and len(unicode(event.text())) == 1:
            chars = self.filterChar(unicode(event.text()))
            if chars:
                for char in chars:
                    myEvent = QtGui.QKeyEvent(event.type(), ord(char), event.modifiers(), char, False, 1)
                    QtGui.QLineEdit.keyPressEvent(self, myEvent)
            event.accept()
        else:
            QtGui.QLineEdit.keyPressEvent(self, event)
            
            
    def filterChar(self, char):
        if self.regExp == romanRegExp:
            if char.isalpha() or 0x20 <= ord(char) <= 0xFF:
               return self.anyToRoman.get(char, '')
            else:
                return char
        if self.regExp[:5] == u'[А-Я]':
            if self.e2r.has_key(char.lower()):
                char = self.e2r[char.lower()]
            if char.isalpha():
                return char.upper()
            else:
                return ''
        elif self.regExp[:5] == u'[а-я]':
            if self.e2r.has_key(char.lower()):
                char = self.e2r[char.lower()]
            if char.isalpha():
                return char.lower()
            else:
                return ''
        elif self.regExp[:5] == u'[A-Z]':
            if self.r2e.has_key(char.lower()):
                char = self.r2e[char.lower()]
            if char.isalpha():
                return char.upper()
            else:
                return ''
        elif self.regExp[:5] == u'[a-z]':
            if self.r2e.has_key(char.lower()):
                char = self.r2e[char.lower()]
            if char.isalpha():
                return char.lower()
            else:
                return ''
        return char


class CLineEditWithRegExpValidatorMasked(CLineEditWithRegExpValidator): # При использовании imputMask и CLineEditWithRegExpValidator одновременно, 
    def __init__(self, *args, **kwargs):                                # есть проблема с удалением символов из-за того как работает qt
        CLineEditWithRegExpValidator.__init__(self, *args, **kwargs)

    def keyPressEvent(self, ev):
        key = ev.key()
        if key in (Qt.Key_Backspace, Qt.Key_Delete):
            pos = self.cursorPosition()
            txt = self.text()
            raw = txt.replace(":", "").replace("_", "")

            if key == Qt.Key_Backspace:
                if pos == 0:
                    return
                rawIndex = pos - 1 if pos > 2 else pos - 1
                raw = raw[:rawIndex] + raw[rawIndex+1:]
                newPos = max(pos-1, 0)
            else:
                if pos >= len(txt):
                    return
                rawIndex = pos - 1 if pos > 2 else pos
                if rawIndex < len(raw):
                    raw = raw[:rawIndex] + raw[rawIndex+1:]
                newPos = pos

            oldMask = self.inputMask()
            self.blockSignals(True)
            self.setInputMask("")
            self.setText(raw)
            self.setInputMask(oldMask)
            self.blockSignals(False)

            if newPos == 1:
                newPos = 2
            self.setCursorPosition(newPos)
            return
        
        return CLineEditWithRegExpValidator.keyPressEvent(self, ev)