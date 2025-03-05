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

__all__ = ('EShtrihError', )



class EShtrihError(Exception):
    def __init__(self, errorCode, message):
        self.message = message
        self.code    = errorCode
        self.args    = self.message, self.code


    def __str__(self):
        return self.message.encode('utf-8')


    def __unicode__(self):
        return self.message
