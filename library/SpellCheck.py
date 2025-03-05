# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import re
from PyQt4 import QtGui,  QtCore

try:
    import library.hunspell as hunspell
    gSpellCheckAvailable = True
except:
    gSpellCheckAvailable = False



class CSpellCheckTextEdit(QtGui.QTextEdit):
    # слово начинается с букв, потом может продолжиться тире (на самом деле - минусом), за которым должны быть буквы
    # таким образом «привет-привет» - это слово,
    # но «-привет» и «привет-» - слова только «привет»
    # и в «привет--привет» два слова «привет»
    # буквы мы можем перечислить, но это тошно.
    # будем использовать \w - это любые буквы, цифры и подчерк.
    # слова типа «101-й» будем считать словами целиком,
    # аббревиатуры игнорируем: «м.н.с.» - три слова, «ФСТЭК» - одно.
    # «во=первых» - это два слова, обшибочно введённый «=» разделяет слова.
    # wordRegex = re.compile(ur'(?iu)\w+([-\u2012\u2013\u2014]\w+)*') # минус и богатые тире
    wordRegex = re.compile(ur'(?iu)\w+([-]\w+)*')  # только минус

    def __init__(self, parent=None):
        QtGui.QTextEdit.__init__(self, parent)

        self._contextMenuActions = []
        self.format = self.getFormatForSpellCheck()
        self.baseDictIsAvailable = False
        pathToDictionary = QtGui.qApp.getPathToDictionary()
        if gSpellCheckAvailable and QtGui.qApp.showingSpellCheckHighlight():
            try:
                self.dict_ = hunspell.DictWithPWL(u'ru_RU', pathToDictionary)
                self.baseDictIsAvailable = True
                self.highlighter = CSpellCheckHighlighter(self.document(), self.wordRegex, self.format)
                self.highlighter.setDict(self.dict_)
            except hunspell.ENoDictionaryFound:
                #QtGui.qApp.logCurrentException()
                self.baseDictIsAvailable = False
                pass


    def addContextMenuAction(self, action):
        self._contextMenuActions.append(action)


    def clearContextMenuActions(self):
        self._contextMenuActions = []


    def getFormatForSpellCheck(self):
        format = QtGui.QTextCharFormat()
        format.setUnderlineColor(QtGui.QColor('red'))
        format.setUnderlineStyle(QtGui.QTextCharFormat.SpellCheckUnderline)
        return format


    def contextMenuEvent(self,  event):
        popupMenu = self.createStandardContextMenu()
        clearSelection = False
        if len(self._contextMenuActions):
            popupMenu.addSeparator()
            for act in self._contextMenuActions:
                popupMenu.addAction(act)

        if gSpellCheckAvailable and self.baseDictIsAvailable and QtGui.qApp.showingSpellCheckHighlight():
            cursor = self.textCursor()
            if not cursor.hasSelection():
                # Выделить слово под курсором для последующего поиска его в словаре
                cursor = self.cursorForPosition(event.pos())
                self.selectWordAtCursor(cursor)
                self.setTextCursor(cursor)
                clearSelection = True

            word = unicode(cursor.selectedText())
            wordStartPos = cursor.selectionStart()
            wordEndPos = cursor.selectionEnd()

            # Проверяем, правильно ли написано слово, и, если нет, предлагаем варианты исправления
            if (word  # слово есть
                    and not any(c.isspace() for c in word)  # в выделении нет пробельных символов
                    and not self.dict_.check(word)  # слова нет в словаре
            ):
                spellMenu = QtGui.QMenu(u'Варианты исправления слова')
                for variant in self.dict_.suggest(word):
                    action = CSpellAction(variant, wordStartPos, wordEndPos, spellMenu)
                    action.correct.connect(self.correctWord)
                    spellMenu.addAction(action)
                recordWord = CRecordCorrectWord(word, u'Внести «%s» в словарь' % word, spellMenu)
                if QtGui.qApp.getPathToDictionary() is None:
                    recordWord.setDisabled(True)
                else:
                    recordWord.setCorrect.connect(self.wrapperForAddWord)
                spellMenu.addAction(recordWord)
                spellMenu.insertSeparator(spellMenu.actions()[-1])
                #  Предлагаем варианты исправления слова в том случае, если они есть
                if len(spellMenu.actions()) != 0:
                    popupMenu.insertSeparator(popupMenu.actions()[0])
                    popupMenu.insertMenu(popupMenu.actions()[0], spellMenu)

        popupMenu.exec_(event.globalPos())
        if clearSelection:
            cursor = self.textCursor()
            cursor.clearSelection()  # этого недостаточно
            self.setTextCursor(cursor)  # для очистки нужно setTextCursor
        event.accept()


    def wrapperForAddWord(self, word):
        if gSpellCheckAvailable:
            self.dict_.add(unicode(word))
            self.highlighter.rehighlight()


    def selectWordAtCursor(self, cursor):
        # в обычном тексте блок - это строка (параграф)
        block = cursor.block()
        text  = unicode(block.text())
        # позиция в блоке
        posInBlock = cursor.position()-block.position()

        # поищем в строке слово содержащее курсор
        nearestDist = len(text)
        nearestWord = None
        for word in re.finditer(self.wordRegex, text):
            # -1 и +1 - как мне кажется немного облегчит прицеливание
            dist = max(word.start() - posInBlock, posInBlock-word.end(), 0)
            if dist<nearestDist:
               nearestDist, nearestWord = dist, word
            if dist == 0:
               break
        if nearestWord and nearestDist<2: # разрешаем немного промахиваться
            # Выделяем слово от начала и до конца слова
            cursor.setPosition(block.position()+nearestWord.start(), QtGui.QTextCursor.MoveAnchor)
            cursor.setPosition(block.position()+nearestWord.end(), QtGui.QTextCursor.KeepAnchor)
        return


    def correctWord(self, word, wordStartPos, wordEndPos):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor = QtGui.QTextCursor(cursor)
            cursor.setPosition(wordStartPos, QtGui.QTextCursor.MoveAnchor)
            cursor.setPosition(wordEndPos, QtGui.QTextCursor.KeepAnchor)

        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(word)
        cursor.endEditBlock()


class CSpellCheckHighlighter(QtGui.QSyntaxHighlighter):

    def __init__(self, parent, wordRegex, format):
        super(CSpellCheckHighlighter, self).__init__(parent)
        self.wordRegex = wordRegex
        self.format = format


    def setDict(self, dict_):
        self.dict_ = dict_


    def highlightBlock(self, text):
        if gSpellCheckAvailable:
            text = unicode(text)

            for word in re.finditer(self.wordRegex, text):
                if not self.dict_.check(word.group()):
                    self.setFormat(word.start(), word.end() - word.start(), self.format)


class CSpellAction(QtGui.QAction):
    correct = QtCore.pyqtSignal(unicode, int, int)

    def __init__(self, word, wordStartPos, wordEndPos, parent):
        QtGui.QAction.__init__(self, word, parent)
        self.wordStartPos = wordStartPos
        self.wordEndPos   = wordEndPos
        self.triggered.connect(self.on_triggered)


    def on_triggered(self):
        self.correct.emit(unicode(self.text()), self.wordStartPos, self.wordEndPos)


class CRecordCorrectWord(QtGui.QAction):
    setCorrect = QtCore.pyqtSignal(unicode)

    def __init__(self, word, title, parent):
        QtGui.QAction.__init__(self, title, parent)
        self.word = word
        self.triggered.connect(self.on_triggered)


    def on_triggered(self):
        self.setCorrect.emit(self.word)
