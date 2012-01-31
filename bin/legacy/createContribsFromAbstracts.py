# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import sys
sys.path.append("c:/development/indico/code/code")

from MaKaC.common import DBMgr
from MaKaC import review
DBMgr.getInstance().startRequest()
from MaKaC.conference import ConferenceHolder
from MaKaC.conference import AcceptedContribution
for conf in ConferenceHolder().getList():
    print "checking conference #%s"%conf.getId()
    for abs in conf.getAbstractMgr().getAbstractList():
        status=abs.getCurrentStatus()
        if isinstance(status,review.AbstractStatusAccepted):
            if status.getContribution() is None:
                contrib=AcceptedContribution(abs)
                status.setContribution(contrib)
                print "abstract #%s...done"%abs.getId()
    print "-"*30
DBMgr.getInstance().endRequest()

