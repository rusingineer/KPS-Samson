# -*- coding: utf-8 -*-

#############################################################################
##
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

"""
Модуль для создания модальных окон типа Popup с прогресс-баром, выполняющих
обработку данных в фоновом потоке с возможностью прервать выполнение.

Если запустить «тяжелую» функцию в основном потоке, то gui зависнет на время
её выполнения. Так что реализованное здесь – не способ что-то оптимизировать,
а всего лишь возможность показать ход выполнения этой «тяжелой» функции,
чтобы пользователь не нервничал понапрасну.

Например, имеется список строк:
```python
strings = ["qwe", "rty", "uiop"]
```
и к каждому элементу нужно применить какую-то функцию, т.е. что-то вроде
```python
result = map(my_func, strings)
```
но известно, что функция `my_func` работает медленно, и очень желательно
показывать, насколько в процентном соотношении список обработан функцией.
Для этого нужно код выше переписать таким образом:
```python
pbar = CBackgroundProgressBar(showCancel=False)
result = pbar.run(my_func, strings) # map(my_func, strings)
```

Если выполнение было отменено, то будет возвращено None.

"""

from PyQt4.QtGui import QProgressBar, QDialog, QApplication, QPushButton, QHBoxLayout
from PyQt4.QtCore import Qt, pyqtSignal, QEvent

class CBackgroundProgressBar(QDialog):
    """
        Модальное окно с прогресс-баром, которое выполняет обработку данных в
        фоновом потоке с визуальным отображением прогресса.

        Параметры:
        * `parent`: родительный виджет (если есть);
        * `showCancel`: есть ли возможность отменить выполнение
          кнопкой "Отмена";
    """

    def __init__(self, parent=None, showCancel=True):
        # type: (Optional[QWidget], bool) -> None
        super(CBackgroundProgressBar, self).__init__(parent)
        self._setupUi()
        self._terminated = False
        self._finished = False
        if not showCancel:
            self.cancel.setVisible(False)

    def _setupUi(self):
        # окно должно закрыться только при завершении или по кнопке "Отмена"
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_DeleteOnClose) # вместо sip.delete
        self.setWindowModality(Qt.ApplicationModal)
        self.progressbar = QProgressBar(self)
        self.cancel = QPushButton(u"Отмена", self)
        self.cancel.clicked.connect(self._on_cancel)
        layout = QHBoxLayout(self)
        layout.addWidget(self.progressbar)
        layout.addWidget(self.cancel)

    def _on_cancel(self):
        self._terminated = True

    def _moveToCenter(self):
        """Перемещает окно в центр родителя или центр экрана"""
        self.adjustSize()
        parent = self.parentWidget()
        if parent is None:
            screenGeometry = QApplication.desktop().screenGeometry()
            x = (screenGeometry.width() - self.width()) / 2 # PyQt5: // 2
            y = (screenGeometry.height() - self.height()) / 2 # PyQt5: // 2
            self.move(x, y)
        else:
            parentRect = parent.geometry()
            self.move(parentRect.center() - self.rect().center())

    def run(self, func, collection):
        """
            Применяет функцию `func` к каждому элементу итерируемого объекта
            `collection` и возвращает список с результатами применения,
            сопровождая весь процесс визуализацией с ходом выполнения.

            Другими словами, это встроенный `map` с прогресс-баром.
        """
        # type: (Callable[[T], R], Collection[T]) -> Optional[list[R]]
        self.progressbar.setMaximum(len(collection))
        self.progressbar.setValue(0)
        self._moveToCenter()

        self.open()
        # не настоящая многопоточность, но пока и такой достаточно
        result = []
        for i in collection:
            if self._terminated:
                break
            result.append(func(i))
            self.progressbar.setValue(self.progressbar.value() + 1)
            # оживляем анимацию
            QApplication.processEvents()

        self._finished = True
        self.done(QDialog.Accepted)
        return (None if self._terminated else result)
