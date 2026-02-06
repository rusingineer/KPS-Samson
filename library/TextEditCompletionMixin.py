from PyQt4 import QtGui
from PyQt4.QtCore import Qt

class CTextEditCompletionMixin:
    def __init__(self):
        self._completer = None


    def setCompleter(self, completer):
        if self._completer:
            self._completer.setWidget(None)
            self._completer.activated.disconnect(self.insertCompletion)
        self._completer = completer
        if completer is not None:
            completer.setWidget(self)
            completer.setCompletionMode(QtGui.QCompleter.PopupCompletion)
            completer.activated.connect(self.insertCompletion)
        
    
    def keyPressEvent(self, event):
        handled = self.handleCompletionBeforeKeyPress(event)
        if not handled:
            QtGui.QTextEdit.keyPressEvent(self, event)
        self.handleCompletionAfterKeyPress(event)
    

    def handleCompletionBeforeKeyPress(self, event):
        if not self._completer:
            return
        popupVisible = self._completer.popup().isVisible()
        if popupVisible and event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
            event.ignore()
            return True
        else:
            return False
    

    def handleCompletionAfterKeyPress(self, event):
        if not self._completer:
            return
        popupVisible = self._completer.popup().isVisible()
        text = unicode(event.text())
        if not text or (text == ' ' and not popupVisible):
            return
        completionPrefix = self.completionPrefix()
        if not completionPrefix:
            self._completer.popup().hide()
            return
        if self._completer.completionPrefix() != completionPrefix:
            self._completer.setCompletionPrefix(completionPrefix)
            self._completer.popup().setCurrentIndex(self._completer.completionModel().index(0, 0))
        cursorRect = self.cursorRect()
        cursorRect.setWidth(self._completer.popup().sizeHintForColumn(0) + self._completer.popup().verticalScrollBar().sizeHint().width())
        self._completer.complete(cursorRect)
        return


    def completionPrefix(self):
        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        return unicode(cursor.selectedText()).strip()
    

    def insertCompletion(self, completion):
        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        cursor.insertText(completion)
        self.setTextCursor(cursor)