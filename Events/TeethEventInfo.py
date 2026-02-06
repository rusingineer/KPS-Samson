# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from Events.EventInfo import CEventInfo, CEmergencyEventInfo
from Events.ActionInfo     import CCookedActionInfo


STOMAT_TABLE = '''<table cellpadding=0 cellspacing=0 width=100%% border="1">
<tr><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td><b>8</b></td><td><b>7</b></td><td><b>6</b></td><td><b>5</b></td><td><b>4</b></td><td><b>3</b></td><td><b>2</b></td><td><b>1</b></td><td><b>1</b></td><td><b>2</b></td><td><b>3</b></td><td><b>4</b></td><td><b>5</b></td><td><b>6</b></td><td><b>7</b></td><td><b>8</b></td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td></tr>
</table>'''

NEW_STOMAT_TABLE = '''<table cellpadding=0 cellspacing=0 width=100%% border="1">
<tr><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td></tr> 
<tr><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td></tr> 
<tr><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td></tr> 
<tr><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td></tr> 
<tr><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td><td align="center"><b>%s</b></td></tr> 
<tr><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td></tr> 
<tr><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td><td align="center">%s</td></tr> 
<tr><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td><td align="center" bgcolor="%s">%s</td></tr> 
</table>'''


STOMAT_CHILD_TABLE = '''<table cellpadding=0 cellspacing=0 width=100%% border="1">
<tr><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td><b>5</b></td><td><b>4</b></td><td><b>3</b></td><td><b>2</b></td><td><b>1</b></td><td><b>1</b></td><td><b>2</b></td><td><b>3</b></td><td><b>4</b></td><td><b>5</b></td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td></tr>
</table>'''


NEW_STOMAT_CHILD_TABLE = '''<table cellpadding=0 cellspacing=0 width=100%% border="1">
<tr><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td></tr>
<tr><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td></tr>
</table>'''


PARODENT_TABLE = '''<table cellpadding=0 cellspacing=0 width=100%% border="1">
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td><b>8</b></td><td><b>7</b></td><td><b>6</b></td><td><b>5</b></td><td><b>4</b></td><td><b>3</b></td><td><b>2</b></td><td><b>1</b></td><td><b>1</b></td><td><b>2</b></td><td><b>3</b></td><td><b>4</b></td><td><b>5</b></td><td><b>6</b></td><td><b>7</b></td><td><b>8</b></td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
</table>'''

NEW_PARODENT_TABLE = '''<table cellpadding=0 cellspacing=0 width=100%% border="1">
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td></tr>
<tr><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
</table>'''


PARODENT_CHILD_TABLE = '''<table cellpadding=0 cellspacing=0 width=100%% border="1">
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td><b>5</b></td><td><b>4</b></td><td><b>3</b></td><td><b>2</b></td><td><b>1</b></td><td><b>1</b></td><td><b>2</b></td><td><b>3</b></td><td><b>4</b></td><td><b>5</b></td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
</table>'''

NEW_PARODENT_CHILD_TABLE = '''<table cellpadding=0 cellspacing=0 width=100%% border="1">
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td></tr>
<tr><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
</table>'''


class CStomatActionInfo(CCookedActionInfo):
    UP = 0
    DONW = 1

    def getProp(self, name, where, number):
        propname = u'%s.%s.%d'%(unicode(name), (u'Верхний', u'Нижний')[where], number)
        return self[propname]

    def getStatus(self, where, number):
        strstatus = self.getProp(u'Статус', where, number).value
        return int(strstatus) if len(strstatus) else -1

    def getMobility(self, where, number):
        return self.getProp(u'Подвижность', where, number).value

    def getConditions(self, where, number):
        return self.getProp(u'Состояние', where, number).value.split(', ')

    def hasCondition(self, where, number, name):
        return name in self.getConditions(where, number)

    def hasAnyCondition(self, where, number, names):
        return any(self.hasCondition(where, number, name) for name in names)

    def getNumber(self, where, number):
        return int(self.getProp((u'Верх', u'Низ')[where], where, number).value)

    def getSanitation(self):
        return self[u'Санация'].value

    def isSanitationNeed(self):
        return u'нуждается' in self.getSanitation()

    def isSanitationPlanned(self):
        return u'запланирована' in self.getSanitation()

    def isSanitationDone(self):
        return u'проведена' in self.getSanitation()


class CParodentActionInfo(CStomatActionInfo):
    pass


class CTeethEventInfo(CEventInfo):
    def __init__(self, context, id):
        CEventInfo.__init__(self, context, id)
        self._action_stomat = None
        self._action_parodent = None


    def _load(self):
        return CEventInfo._load(self) and self.initActions()


    def initActions(self):
        self._action_stomat = None
        self._action_parodent = None
        for act in self._actions:
            if act.flatCode == 'dentitionInspection':
                self._action_stomat = self.context.getInstance(CStomatActionInfo, act._record, act._action)
            if act.flatCode == 'parodentInsp':
                self._action_parodent = self.context.getInstance(CParodentActionInfo, act._record, act._action)
        return bool(self._action_stomat and self._action_parodent)


    def getStomatTable(self, newForm=True, adult=True):
        colors = ('white', 'lightGray', 'darkYellow', 'cyan', 'blue', 'green', 'darkGreen', 'magenta', 'yellow', 'red')
        props = ()
        for i in xrange(16) if adult else xrange(3,13):
            status = self._action_stomat.getProp(u'Статус', 0, i+1).value
            props += (colors[int(status) if len(status) else 0], )
            props += (status, )
        for i in xrange(16) if adult else xrange(3,13):
            props += (self._action_stomat.getProp(u'Подвижность', 0, i+1).value, )
        for i in xrange(16) if adult else xrange(3,13):
            props += (self._action_stomat.getProp(u'Состояние', 0, i+1).value, )
        if newForm:
            for i in xrange(16) if adult else xrange(3,13):
                props += (self._action_stomat.getProp(u'Верх', 0, i+1).value, )
            for i in xrange(16) if adult else xrange(3,13):
                props += (self._action_stomat.getProp(u'Низ', 1, i+1).value, )
        for i in xrange(16) if adult else xrange(3,13):
            props += (self._action_stomat.getProp(u'Состояние', 1, i+1).value, )
        for i in xrange(16) if adult else xrange(3,13):
            props += (self._action_stomat.getProp(u'Подвижность', 1, i+1).value, )
        for i in xrange(16) if adult else xrange(3,13):
            status = self._action_stomat.getProp(u'Статус', 1, i+1).value
            props += (colors[int(status) if len(status) else 0], )
            props += (status, )
        if adult:
            return (NEW_STOMAT_TABLE if newForm else STOMAT_TABLE) % props
        else:
            return (NEW_STOMAT_CHILD_TABLE if newForm else STOMAT_CHILD_TABLE) % props


    def getParodentTable(self, newForm=True, adult=True):
        props = ()
        for i in xrange(16) if adult else xrange(3,13):
            props += (self._action_parodent.getProp(u'Клиновидный', 0, i+1).value, )
        for i in xrange(16) if adult else xrange(3,13):
            props += (self._action_parodent.getProp(u'Рецессия', 0, i+1).value, )
        for i in xrange(16) if adult else xrange(3,13):
            props += (self._action_parodent.getProp(u'Подвижность', 0, i+1).value, )
        for i in xrange(16) if adult else xrange(3,13):
            props += (self._action_parodent.getProp(u'Глубина', 0, i+1).value, )
        if newForm:
            for i in xrange(16) if adult else xrange(3,13):
                props += (self._action_parodent.getProp(u'Верх', 0, i+1).value, )
            for i in xrange(16) if adult else xrange(3,13):
                props += (self._action_parodent.getProp(u'Низ', 1, i+1).value, )
        for i in xrange(16) if adult else xrange(3,13):
            props += (self._action_parodent.getProp(u'Глубина', 1, i+1).value, )
        for i in xrange(16) if adult else xrange(3,13):
            props += (self._action_parodent.getProp(u'Подвижность', 1, i+1).value, )
        for i in xrange(16) if adult else xrange(3,13):
            props += (self._action_parodent.getProp(u'Рецессия', 1, i+1).value, )
        for i in xrange(16) if adult else xrange(3,13):
            props += (self._action_parodent.getProp(u'Клиновидный', 1, i+1).value, )
        if adult:
            return (NEW_PARODENT_TABLE if newForm else PARODENT_TABLE) % props
        else:
            return (NEW_PARODENT_CHILD_TABLE if newForm else PARODENT_CHILD_TABLE) % props


    stomatAction       = property(lambda self: self.load()._action_stomat)
    parodentAction     = property(lambda self: self.load()._action_parodent)
    stomat             = property(lambda self: self.load().getStomatTable(newForm=False, adult=True))
    parodent           = property(lambda self: self.load().getParodentTable(newForm=False, adult=True))
    stomatfull         = property(lambda self: self.load().getStomatTable(newForm=True, adult=True))
    parodentfull       = property(lambda self: self.load().getParodentTable(newForm=True, adult=True))

    stomatchild        = property(lambda self: self.load().getStomatTable(newForm=False, adult=False))
    parodentchild      = property(lambda self: self.load().getParodentTable(newForm=False, adult=False))
    stomatchildfull    = property(lambda self: self.load().getStomatTable(newForm=True, adult=False))
    parodentchildfull  = property(lambda self: self.load().getParodentTable(newForm=True, adult=False))


class CEmergencyTeethEventInfo(CEmergencyEventInfo, CTeethEventInfo):
    def __init__(self, context, id):
        CTeethEventInfo.__init__(self, context, id)
