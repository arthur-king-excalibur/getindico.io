# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

from MaKaC.conference import ConferenceHolder

from indico.web.http_api.hooks.base import HTTPAPIHook
from indico.web.http_api.hooks.event import EventBaseHook
from indico.web.http_api.util import get_query_parameter

from indico.util.date_time import format_datetime


@HTTPAPIHook.register
class CheckInHook(EventBaseHook):
    RE = r'(?P<event>[\w\s]+)/registrant/(?P<registrant_id>[\w\s]+)/checkin'
    NO_CACHE = True
    COMMIT = True

    def _getParams(self):
        super(CheckInHook, self)._getParams()
        self._check_in = get_query_parameter(self._queryParams, ["checked_in"]) == "yes"
        self._secret = get_query_parameter(self._queryParams, ["secret"])
        registrant_id = self._pathParams["registrant_id"]
        self._conf = ConferenceHolder().getById(self._pathParams['event'])
        self._registrant = self._conf.getRegistrantById(registrant_id)
        self._type = "checkin"

    def _hasAccess(self, aw):
        return self._conf.canManageRegistration(aw.getUser()) and self._secret == self._registrant.getCheckInUUID()

    def export_checkin(self, aw):
        self._registrant.setCheckedIn(self._check_in)
        checkin_date = format_datetime(self._registrant.getAdjustedCheckInDate()) if self._check_in else None
        return {
            "success": True,
            "checkin_date": checkin_date
        }


@HTTPAPIHook.register
class RegistrantsHook(EventBaseHook):
    RE = r'(?P<event>[\w\s]+)/registrants'
    NO_CACHE = True

    def _getParams(self):
        super(RegistrantsHook, self)._getParams()
        self._conf_id = self._pathParams['event']
        self._type = "registrants"
        self._conf = ConferenceHolder().getById(self._conf_id)

    def _hasAccess(self, aw):
        return self._conf.canManageRegistration(aw.getUser())

    def export_registrants(self, aw):
        registrants = self._conf.getRegistrantsList()
        registrant_list = []
        for registrant in registrants:
            registration_date = format_datetime(registrant.getAdjustedRegistrationDate())
            checkin_date = format_datetime(registrant.getAdjustedCheckInDate())
            reg = {
                "id": registrant.getId(),
                "full_name": registrant.getFullName(title=True, firstNameFirst=True),
                "checked_in": registrant.isCheckedIn(),
                "checkin_date": checkin_date,
                "registration_date": registration_date,
                "secret": registrant.getCheckInUUID(),
                "payed": registrant.getPayed() if self._conf.getModPay().isActivated() else None,
                "pay_amount": registrant.getTotal() if self._conf.getModPay().isActivated() else None
            }
            regForm = self._conf.getRegistrationForm()
            reg.update(regForm.getPersonalData().getRegistrantValues(registrant))
            registrant_list.append(reg)
        return {"registrants": registrant_list}
