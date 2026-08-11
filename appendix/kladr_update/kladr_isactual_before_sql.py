#!/usr/bin/env python
# -*- coding: utf-8 -*-
COMMAND = u"""
use kladr;

select 'Очистка признака актуальности улиц...' as ' ';

-- Очистка поля, которое указывает на то что данные обновлены
UPDATE STREET SET IS_INSERTED = NULL;

select 'Очистка признака актуальности населенных пунктов...' as ' ';

-- Очистка поля, которое указывает на то что данные обновлены
UPDATE KLADR SET IS_INSERTED = NULL;
"""

