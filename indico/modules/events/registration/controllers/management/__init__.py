# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from indico.modules.events.registration.controllers import RegistrationFormMixin
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHManageRegFormsBase(RHConferenceModifBase):
    """Base class for all registration management RHs"""

    CSRF_ENABLED = True

    def _process(self):
        return RH._process(self)

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.event = self._conf


class RHManageRegFormBase(RHManageRegFormsBase, RegistrationFormMixin):
    """Base class for a specific registration form"""

    def _checkParams(self, params):
        RHManageRegFormsBase._checkParams(self, params)
        RegistrationFormMixin._checkParams(self)
