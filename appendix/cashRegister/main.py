#!/usr/bin/env python
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

import codecs
import locale
import sys
from  optparse import OptionParser

from PyQt4 import QtGui
from PyQt4.QtCore import QTranslator

import library.patches # noqa

from app.App        import CApp
from app.MainWindow import CMainWindow


def main():
    parser = OptionParser(usage = "usage: %prog [options]")
    parser.add_option('--version',
                      dest='version',
                      help='print version and exit',
                      action='store_true',
                      default=False)

    parser.add_option('--SQL',
                      dest='logSql',
                      help='log sql queries',
                      action='store_true',
                      default=False
                     )

#    parser.add_option("-q", "--quiet",   action="store_false", dest="verbose", default=True,  help="don't print status messages to stdout")
    (options, args) = parser.parse_args()

    if options.version:
        print '%s - %s' % (sys.argv[0] if sys.argv else '', CApp.getLatVersion())
    else:
        locale.setlocale(locale.LC_ALL, '')
        app = CApp(sys.argv, options.logSql)
        stdTtranslator = QTranslator()
        stdTtranslator.load('i18n/std_ru.qm')
        app.installTranslator(stdTtranslator)

        QtGui.qApp = app
        app.applyDecorPreferences()
        mainWindow = CMainWindow()
        app.mainWindow = mainWindow
        app.applyDecorPreferences() # применение максимизации/полноэкранного режима к главному окну

        mainWindow.show()
        if app.preferences.dbAutoLogin:
            mainWindow.actLogin.activate(QtGui.QAction.Trigger)
        res = app.exec_()
        mainWindow.savePreferences()
        del mainWindow
        app.preferences.save()
        app.closeDatabase()
        app.doneTrace()
        del app
        QtGui.qApp = None
        return res

#    sys.exit(res)


if __name__ == '__main__':
    sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)
    sys.stderr = codecs.getwriter(locale.getpreferredencoding())(sys.stderr)
    main()
