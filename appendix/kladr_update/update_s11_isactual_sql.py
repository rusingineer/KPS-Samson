#!/usr/bin/env python
# -*- coding: utf-8 -*-
COMMAND = u"""

select 'Удаление неактуальных улиц... ' as ' ';

CREATE TEMPORARY TABLE temp_street (CODE varchar(17));

INSERT INTO temp_street
SELECT kst.CODE
FROM kladr.STREET kst
LEFT JOIN AddressHouse ah ON ah.KLADRStreetCode = kst.CODE
WHERE
kst.IS_ACTUAL IS NULL
AND
ah.KLADRStreetCode IS NULL;

DELETE FROM kladr.STREET WHERE CODE IN (SELECT CODE FROM temp_street);

select 'Удаление неактуальных населенных пунктов... ' as ' ';

CREATE TEMPORARY TABLE temp_kladr (CODE varchar(13));

INSERT INTO temp_kladr
SELECT kk.CODE
FROM kladr.KLADR kk
LEFT JOIN AddressHouse ah ON ah.KLADRCode = kk.CODE
WHERE
kk.IS_ACTUAL IS NULL
AND
ah.KLADRCode IS NULL;

DELETE FROM kladr.KLADR WHERE CODE IN (SELECT CODE FROM temp_kladr);
"""
