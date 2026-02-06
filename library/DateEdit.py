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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, SIGNAL, QDate, QEvent, QObject, QSize

from library.CalendarWidget import CCalendarWidget
from library.ROComboBox     import CStandardItemModel
from library.adjustPopup    import adjustPopupToWidget
from library.Utils          import forceDate

__all__ = ['CDateEdit',
           ]


class CDateValidator(QtGui.QValidator):
    def __init__(self, parent, format, canBeEmpty):
        QtGui.QValidator.__init__(self, parent)
        self.min = QDate(1900, 1, 1)
        self.max = QDate(2099, 12, 31)
        self.defaultMin = QDate(1900, 1, 1)
        self.defaultMax = QDate(2099, 12, 31)
        self.format = format
        self.canBeEmpty = canBeEmpty


    def inputIsEmpty(self, input):
        return not unicode(input).strip(' 0.-')


    def validate(self, input, pos):
        if self.inputIsEmpty(input):
            if self.canBeEmpty:
                return (self.Acceptable, pos)
            else:
                return (self.Intermediate, pos)
        else:
            d = QDate.fromString(input, self.format)
            if d.isValid():
                if self.min!=None and d<self.min:
                    return (self.Intermediate, pos)
                elif self.max!=None and d>self.max:
                    return (self.Intermediate, pos)
                else:
                    return (self.Acceptable, pos)
            else:
                return (self.Intermediate, pos)


    def fixup(self, input):
        if self.inputIsEmpty(input) and self.canBeEmpty:
            newInput = ''
        else:
            d = QDate.fromString(input, self.format)
            newInput = d.toString(self.format)
        if not newInput:
            input.clear()


class CCalendarPopup(QtGui.QFrame):
    def __init__(self, parent = None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
#        self.setFrameShape(QtGui.QFrame.Panel)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.initialDate = QDate()
        self.dateChanged = False
        self.calendar = CCalendarWidget(self)
        self.calendar.setVerticalHeaderFormat(QtGui.QCalendarWidget.NoVerticalHeader)
        self.widgetLayout = QtGui.QVBoxLayout(self)
        self.widgetLayout.setMargin(0)
        self.widgetLayout.setSpacing(0)
        self.widgetLayout.addWidget(self.calendar)
        self.connect(self.calendar, SIGNAL('activated(QDate)'), self.dateSelected)
        self.connect(self.calendar, SIGNAL('clicked(QDate)'), self.dateSelected)
        self.connect(self.calendar, SIGNAL('selectionChanged()'), self.dateSelectionChanged)
        self.calendar.setFocus()


    def setInitialDate(self, date):
        self.initialDate = date
        self.dateChanged = False
        self.calendar.setSelectedDate(date)


    def dateSelected(self, date):
        self.dateChanged=True
        self.emit(SIGNAL('activated(QDate)'), date)
        self.close()


    def mousePressEvent(self, event):
        dateTime = self.parentWidget()
        if dateTime!=None:
            opt=QtGui.QStyleOptionComboBox()
            opt.init(dateTime)
            arrowRect = dateTime.style().subControlRect(
                QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, dateTime)
            arrowRect.moveTo(dateTime.mapToGlobal(arrowRect.topLeft()))
            if (arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos())):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)


    def mouseReleaseEvent(self, event):
#        self.emit(QtCore.SIGNAL('resetButton()'))
        self.parent().mouseReleaseEvent(event)
        pass


    def event(self, event):
        if event.type()==QEvent.KeyPress:
            if event.key()==Qt.Key_Escape:
                self.dateChanged = False
        return QtGui.QFrame.event(self, event)


    def dateSelectionChanged(self):
        self.dateChanged=True
        self.emit(SIGNAL('newDateSelected(QDate)'), self.calendar.selectedDate())


    def hideEvent(self, event):
        if not self.dateChanged:
            self.dateSelected(self.initialDate)


class CDateEdit(QtGui.QComboBox):
    __pyqtSignals__ = ('dateChanged(const QDate &)',
                      )

    def __init__(self, parent = None):
        QtGui.QComboBox.__init__(self, parent)
        self._model = CStandardItemModel(self)
        self.setModel(self._model)
        self.setMinimumContentsLength(10)
        self.readOnly = False
        self.highlightRedDate = QtGui.qApp.highlightRedDate()
        self.lineEdit=QtGui.QLineEdit()
        self.lineEdit.setInputMask('99.99.9999')
        self.validator=CDateValidator(self, 'dd.MM.yyyy', False)
        self.lineEdit.setValidator(self.validator)
        self.setLineEdit(self.lineEdit)
        self.lineEdit.setText(QDate.currentDate().toString(self.validator.format))
        self.lineEdit.setCursorPosition(0)
        width = self.lineEdit.minimumSizeHint().width() * 4
        height = self.lineEdit.minimumSizeHint().height() * 1.2
        self.setMinimumSize(width, height)
        self.calendarPopup=None
        self.oldText = self.lineEdit.text()
        self.connect(self.lineEdit, SIGNAL('textEdited(QString)'), self.onTextChange)


    def setReadOnly(self, value=False):
        self.readOnly = value
        self.model().setReadOnly(self.readOnly)


    def isReadOnly(self):
        return self.readOnly


    def minimumDate(self):
        return self.validator.min


    def setMinimumDate(self, min):
        if isinstance(min, QDate) and min.isValid():
            max =self.validator.max
            if max.isValid() and max<min:
                max = min
            self.setDateRange(min, max)


    def clearMinimumDate(self):
        self.setMinimumDate(QDate())


    def maximumDate(self):
        return self.validator.max


    def setMaximumDate(self, max):
        if isinstance(max, QDate) and max.isValid():
            min=self.validator.min
            if min.isValid() and min>max:
                min=max
            self.setDateRange(min, max)


    def clearMaximumDate(self):
        self.setMaximumDate(QDate())


    def setDateRange(self, min, max):
        if  isinstance(min, QDate) and isinstance(max, QDate) and min.isValid() and max.isValid():
            self.validator.min=min
            self.validator.max=max


    def displayFormat(self):
        return self.format()


    def setDisplayFormat(self, format):
        self.setFormat(format)


    def format(self):
        return self.validator.format


    def setFormat(self, format):
        self.validator.format=format


    def canBeEmpty(self, value=True):
        self.validator.canBeEmpty = value


    def setHighlightRedDate(self, value=True):
        self.highlightRedDate = value and QtGui.qApp.highlightRedDate()


    def setCalendarPopup(self, value=True):
        pass


    def showPopup(self):
        if not self.isReadOnly():
            if not self.calendarPopup:
                self.calendarPopup = CCalendarPopup(self)

                self.connect(self.calendarPopup, SIGNAL('newDateSelected(QDate)'), self.setDate)
    #            self.connect(self.calendarPopup, SIGNAL('hidingCalendar(QDate)'), self.setDate)
                self.connect(self.calendarPopup, SIGNAL('activated(QDate)'), self.setDate)
                self.connect(self.calendarPopup, SIGNAL('activated(QDate)'), self.calendarPopup.close)
    #            self.connect(self.calendarPopup, SIGNAL('resetButton()'), self._q_resetButton)

            self.calendarPopup.calendar.setMinimumDate(self.minimumDate())
            self.calendarPopup.calendar.setMaximumDate(self.maximumDate())
            date = self.date()
            if not date:
                date = QDate.currentDate()
            self.calendarPopup.setInitialDate(date)
            self.calendarPopup.show()
            adjustPopupToWidget(self, self.calendarPopup, False)


    def setDate(self, date):
        if date is None:
            date = QDate()

        dateAsText = date.toString(self.validator.format)
        if self.oldText != dateAsText:
            self.setColor(date)
            self.lineEdit.setText(dateAsText)
            self.lineEdit.setCursorPosition(0)
            self.emit(SIGNAL('dateChanged(const QDate &)'), date)
            self.oldText = dateAsText


    def setColor(self, date):
        palette = QtGui.QPalette()
        if self.highlightRedDate and date and QtGui.qApp.calendarInfo.getDayOfWeek(date) in (6,7):
            palette.setColor(QtGui.QPalette.Text, QtGui.QColor(255, 0, 0))
        self.lineEdit.setPalette(palette)


    def setInvalidColor(self):
        palette = QtGui.QPalette()
        if QtGui.qApp.highlightInvalidDate():
            palette.setColor(QtGui.QPalette.Text, QtGui.QColor(255, 0, 255))
        self.lineEdit.setPalette(palette)


    def selectAll(self):
        self.lineEdit.selectAll()
        self.lineEdit.setCursorPosition(0)


    def setCursorPosition(self,  pos=0):
        self.lineEdit.setCursorPosition(pos)


    def text(self):
        return self.lineEdit.text()


    def date(self):
        state, pos = self.validator.validate(self.text(), 0)
        if state == CDateValidator.Acceptable:
            return QDate.fromString(self.text(), self.validator.format)
        else:
            return QDate()


    def onTextChange(self, dateAsText):
        if self.oldText != dateAsText:
            state, pos = self.validator.validate(dateAsText, 0)
            if state == CDateValidator.Acceptable:
                date = self.date()
                self.setColor(date)
                self.emit(SIGNAL('dateChanged(const QDate &)'), date)
            else:
                if not unicode(dateAsText).replace('.', ''):
                    self.emit(SIGNAL('dateChanged(const QDate &)'), QDate())
                self.setInvalidColor()
            self.oldText = dateAsText


    def currentSection(self):
        pos = self.lineEdit.cursorPosition()
        if pos>=6:
            return QtGui.QDateTimeEdit.YearSection
        elif pos>=3:
            return QtGui.QDateTimeEdit.MonthSection
        else:
            return QtGui.QDateTimeEdit.DaySection


    def event(self, event):
        if event.type() == QEvent.KeyPress:
            if self.model().isReadOnly():
                event.accept()
                return False
            key = event.key()
            if key == Qt.Key_Equal or (key == Qt.Key_Space and not self.date().isValid()):
                    self.setDate(QDate.currentDate())
                    event.accept()
                    return True
            if key in (Qt.Key_Plus, Qt.Key_Minus):
                d = self.date()
                if not d.isValid():
                    d = QDate.currentDate()
                step = 1 if key  == Qt.Key_Plus else -1
                if self.currentSection() == QtGui.QDateTimeEdit.YearSection:
                    d = d.addYears(step)
                elif self.currentSection() == QtGui.QDateTimeEdit.MonthSection:
                    d = d.addMonths(step)
#                elif event.modifiers() & Qt.ControlModifier:
#                    d = d.addDays(step*7)
                else:
                    d = d.addDays(step)
                pos = self.lineEdit.cursorPosition()
                self.setDate(d)
                self.lineEdit.setCursorPosition(pos)
                event.accept()
                return True
        return QtGui.QComboBox.event(self, event)


#    def _q_resetButton(self):
#        if (self.arrowState == QtGui.QStyle.State_None):
#            return
#        self.arrowState=QtGui.QStyle.State_None
#        self.buttonState = 0
#        self.hoverControl = QtGui.QStyle.SC_ComboBoxFrame
#        self.q.update()


if __name__ == "__main__":

    import sys

    class CFakeCalendatInfo(QObject):
        def getDayOfWeek(self, date):
            return date.dayOfWeek()


    def onDateChanged(date):
        print 'date changed', date.toString('yyyy-MM-dd')


    def onEditingFinished():
        print 'editing finished'


    app = QtGui.QApplication(sys.argv)
    QtGui.qApp = app
    app.highlightRedDate = lambda: True
    app.highlightInvalidDate = lambda: True
    app.calendarInfo = CFakeCalendatInfo()

    dialog = QtGui.QDialog()
    gridlayout = QtGui.QGridLayout(dialog)
    gridlayout.setMargin(9)
    gridlayout.setSpacing(6)
    btn = QtGui.QPushButton(u'new date', dialog)
    gridlayout.addWidget(btn,0,0,1,1)
    cv = CDateEdit(dialog)
    gridlayout.addWidget(cv,1,0,1,1)
    out = QtGui.QLabel()
    gridlayout.addWidget(out,2,0,1,1)
    dialog.resize(QSize(300, 300))
    out.setText('00.00.0000')

    QObject.connect(btn, SIGNAL('clicked()'), lambda: cv.setDate((cv.date() or QDate.currentDate()).addDays(1)))
    QObject.connect(cv, SIGNAL('dateChanged(QDate)'), onDateChanged)
    QObject.connect(cv, SIGNAL('editingFinished()'),  onEditingFinished)
    QObject.connect(cv.lineEdit, SIGNAL('returnPressed()'), lambda :(out.setText(cv.lineEdit.text())))
    dialog.show()
    sys.exit(app.exec_())


class CCurrentDateEdit(CDateEdit):
    def __init__(self, parent = None):
        CDateEdit.__init__(self, parent)
        self.isCurrentDate = False


    def setCurrentDate(self, isCurrentDate = False):
        self.isCurrentDate = isCurrentDate


    def onTextChange(self, dateAsText):
        if self.oldText != dateAsText:
            state, pos = self.validator.validate(dateAsText, 0)
            if state == CDateValidator.Acceptable:
                date = self.date()
                self.setColor(date)
                self.emit(SIGNAL('dateChanged(const QDate &)'), date)
            else:
                if self.isCurrentDate:
                    if not unicode(dateAsText).replace('.', ''):
                        self.emit(SIGNAL('dateChanged(const QDate &)'), QDate())
                    else:
                        currentDate = QDate.currentDate()
                        date = currentDate.toString(self.validator.format)
                        state, pos = self.validator.validate(date, 0)
                        if state == CDateValidator.Acceptable:
                            dateAsText = date
                            self.setColor(currentDate)
                            self.lineEdit.setText(dateAsText)
                            self.lineEdit.setCursorPosition(0)
                            self.emit(SIGNAL('dateChanged(const QDate &)'), currentDate)
                        else:
                            self.lineEdit.setText(self.oldText)
                            self.lineEdit.setCursorPosition(0)
                            self.emit(SIGNAL('dateChanged(const QDate &)'), forceDate(self.oldText))
                            dateAsText = self.oldText
                else:
                    if not unicode(dateAsText).replace('.', ''):
                        self.emit(SIGNAL('dateChanged(const QDate &)'), QDate())
                    self.setInvalidColor()
            self.oldText = dateAsText


class CCurrentDateEditEx(CCurrentDateEdit):
    def __init__(self, parent=None):
        CCurrentDateEdit.__init__(self, parent)
        self.connect(self.lineEdit, SIGNAL('textEdited(QString)'), self.onTextChange)


    def onTextChange(self, dateAsText):
        if self.oldText != dateAsText:
            state, pos = self.validator.validate(dateAsText, 0)
            if state == CDateValidator.Acceptable:
                date = self.date()
                self.setColor(date)
                self.emit(SIGNAL('dateChanged(const QDate &)'), date)
            else:
                if self.isCurrentDate:
                    if not unicode(dateAsText).replace('.', ''):
                        self.emit(SIGNAL('dateChanged(const QDate &)'), QDate())
                    else:
                        currentDate = QDate.currentDate()
                        date = currentDate.toString(self.validator.format)
                        state, pos = self.validator.validate(date, 0)
                        if state == CDateValidator.Acceptable:
                            dateAsText = date
                            self.setColor(currentDate)
                            self.lineEdit.setText(dateAsText)
                            self.lineEdit.setCursorPosition(0)
                            self.emit(SIGNAL('dateChanged(const QDate &)'), currentDate)
                        else:
                            self.lineEdit.setText(self.oldText)
                            self.lineEdit.setCursorPosition(0)
                            self.emit(SIGNAL('dateChanged(const QDate &)'), forceDate(self.oldText))
                            dateAsText = self.oldText
                else:
                    self.setInvalidColor()
                    d = QDate.fromString(dateAsText, self.validator.format)
                    currentDate = QDate.currentDate()
                    date = currentDate.toString(self.validator.format)
                    if d.isValid() and state != CDateValidator.Acceptable:
                        self.setColor(currentDate)
                        self.lineEdit.setText(self.oldText)
                        #self.lineEdit.setCursorPosition(0)
                        state, pos = self.validator.validate(self.oldText, 0)
                        oldDate = QDate.fromString(self.oldText, self.validator.format)
                        if oldDate.isValid() and state == CDateValidator.Acceptable:
                            self.emit(SIGNAL('dateChanged(const QDate &)'), oldDate)
                        else:
                            self.emit(SIGNAL('dateChanged(const QDate &)'), currentDate)
                            self.oldText = date
                        dateAsText = self.oldText
                    else:
                        if not unicode(dateAsText).replace('.', ''):
                            self.emit(SIGNAL('dateChanged(const QDate &)'), QDate())
                        elif len(unicode(dateAsText).replace('.', '')) == len(unicode(self.validator.format).replace('.', '')):
                            self.setColor(currentDate)
                            self.lineEdit.setText(date)
                            self.emit(SIGNAL('dateChanged(const QDate &)'), currentDate)
                            dateAsText = date
            self.oldText = dateAsText
class CCurrentDateEditEF(CCurrentDateEditEx):
    __pyqtSignals__ = ('editingFinished()',
                      )

    def __init__(self, parent=None):
        CCurrentDateEdit.__init__(self, parent)
        self.connect(self.lineEdit, SIGNAL('textEdited(QString)'), self.onTextChange)


    def showPopup(self):
        if not self.isReadOnly():
            if not self.calendarPopup:
                self.calendarPopup = CCalendarPopup(self)

                self.connect(self.calendarPopup, SIGNAL('newDateSelected(QDate)'), self.setDate)
                #            self.connect(self.calendarPopup, SIGNAL('hidingCalendar(QDate)'), self.setDate)
                self.connect(self.calendarPopup, SIGNAL('activated(QDate)'), self.setDate)
                self.connect(self.calendarPopup, SIGNAL('activated(QDate)'), self.calendarPopup.close)
            #            self.connect(self.calendarPopup, SIGNAL('resetButton()'), self._q_resetButton)
            self.calendarPopup.installEventFilter(self)
            self.calendarPopup.calendar.setMinimumDate(self.minimumDate())
            self.calendarPopup.calendar.setMaximumDate(self.maximumDate())
            date = self.date()
            if not date:
                date = QDate.currentDate()
            self.calendarPopup.setInitialDate(date)
            self.calendarPopup.show()
            adjustPopupToWidget(self, self.calendarPopup, False)


    def eventFilter(self, obj, event):
        if event.type() == QEvent.Close:
            self.hidePopup()
            return True
        return QtGui.QComboBox.eventFilter(self, obj, event)


    def hidePopup(self):
        if self.calendarPopup:
            self.calendarPopup.hide()
        QtGui.QComboBox.hidePopup(self)
        self.setFocus()
        self.emit(SIGNAL('editingFinished()'))

