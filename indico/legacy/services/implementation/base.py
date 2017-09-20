# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

import os
import sys
import traceback

from flask import g, session

from indico.core.config import config
from indico.core.logger import sentry_set_tags
from indico.legacy.common import security
from indico.legacy.errors import HtmlForbiddenTag, MaKaCError
from indico.legacy.services.interface.rpc.common import HTMLSecurityError, ServiceAccessError
from indico.legacy.webinterface.rh.base import RequestHandlerBase
from indico.util.string import unicode_struct_to_utf8


class ServiceBase(RequestHandlerBase):
    """
    The ServiceBase class is the basic class for services.
    """

    UNICODE_PARAMS = False
    CHECK_HTML = True

    def __init__(self, params):
        if not self.UNICODE_PARAMS:
            params = unicode_struct_to_utf8(params)
        self._reqParams = self._params = params
        self._target = None
        self._startTime = None
        self._endTime = None
        self._doProcess = True

    # Methods =============================================================

    def _checkParams(self):
        """
        Checks the request parameters (normally overloaded)
        """
        pass

    def _check_access(self):
        """
        Checks protection when accessing resources (normally overloaded)
        """
        pass

    def _processError(self):
        """
        Treats errors occured during the process of a RH, returning an error string.
        @param e: the exception
        @type e: An Exception-derived type
        """

        trace = traceback.format_exception(*sys.exc_info())

        return ''.join(trace)

    def process(self):
        """
        Processes the request, analyzing the parameters, and feeding them to the
        _getAnswer() method (implemented by derived classes)
        """

        g.rh = self
        sentry_set_tags({'rh': self.__class__.__name__})

        self._checkParams()
        self._check_access()

        if self.CHECK_HTML:
            try:
                security.Sanitization.sanitizationCheck(self._target, self._params, session.user, ['requestInfo'])
            except HtmlForbiddenTag as e:
                raise HTMLSecurityError('ERR-X0', 'HTML Security problem. {}'.format(e))

        if self._doProcess:
            if config.PROFILE:
                import profile, pstats, random
                proffilename = os.path.join(config.TEMP_DIR, "service%s.prof" % random.random())
                result = [None]
                profile.runctx("result[0] = self._getAnswer()", globals(), locals(), proffilename)
                answer = result[0]
                stats = pstats.Stats(proffilename)
                stats.sort_stats('cumulative', 'time', 'calls')
                stats.dump_stats(os.path.join(config.TEMP_DIR, "IndicoServiceRequestProfile.log"))
                os.remove(proffilename)
            else:
                answer = self._getAnswer()

            return answer

    def _getAnswer(self):
        """
        To be overloaded. It should contain the code that does the actual
        business logic and returns a result (python JSON-serializable object).
        If this method is not overloaded, an exception will occur.
        If you don't want to return an answer, you should still implement this method with 'pass'.
        """
        # This exception will happen if the _getAnswer method is not implemented in a derived class
        raise MaKaCError("No answer was returned")


class ProtectedService(ServiceBase):
    def _checkSessionUser(self):
        """
        Checks that the current user exists (is authenticated)
        """

        if session.user is None:
            self._doProcess = False
            raise ServiceAccessError("You are currently not authenticated. Please log in again.")


class LoggedOnlyService(ProtectedService):
    """
    Only accessible to users who are logged in (access keys not allowed)
    """

    def _check_access(self):
        self._checkSessionUser()
