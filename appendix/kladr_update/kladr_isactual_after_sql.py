#!/usr/bin/env python
# -*- coding: utf-8 -*-
COMMAND = u"""
use kladr;

select 'Простановка признака актуальности улиц...' as ' ';

-- Простановка признака актуальности улиц
UPDATE STREET SET IS_ACTUAL = NULL WHERE IS_INSERTED IS NULL;

select 'Простановка признака актуальности населенных пунктов...' as ' ';

-- Простановка признака актуальности населенных пунктов
UPDATE KLADR SET IS_ACTUAL = NULL WHERE IS_INSERTED IS NULL;
"""
