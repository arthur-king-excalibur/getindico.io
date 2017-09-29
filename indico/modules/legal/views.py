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

from __future__ import unicode_literals

from indico.legacy.webinterface.pages.base import WPDecorated, WPJinjaMixin
from indico.legacy.webinterface.wcomponents import WSimpleNavigationDrawer
from indico.modules.admin.views import WPAdmin
from indico.util.i18n import _


class WPLegalMixin:
    template_prefix = 'legal/'


class WPManageLegalMessages(WPLegalMixin, WPAdmin):
    pass


class WPDisplayLegalMessages(WPLegalMixin, WPJinjaMixin, WPDecorated):
    def _getNavigationDrawer(self):
        return WSimpleNavigationDrawer(_('Terms and Conditions'))

    def _getBody(self, params):
        return self._getPageContent(params)
