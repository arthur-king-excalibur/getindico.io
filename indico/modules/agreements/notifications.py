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

from flask_pluginengine import current_plugin

from indico.core.notifications import email_sender, make_email
from indico.core.plugins import get_plugin_template_module
from indico.web.flask.templating import get_template_module


@email_sender
def notify_agreement_required_new(agreement):
    func = get_template_module if not current_plugin else get_plugin_template_module
    template = func('agreements/emails/agreement_required_new.html', agreement=agreement)
    return make_email(agreement.person_email, template=template, html=True)


@email_sender
def notify_agreement_required_reminder(agreement):
    func = get_template_module if not current_plugin else get_plugin_template_module
    template = func('agreements/emails/agreement_required_reminder.html', agreement=agreement)
    return make_email(agreement.person_email, template=template, html=True)
