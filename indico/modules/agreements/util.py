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

from indico.core import signals
from indico.core.db import db
from indico.util.signals import named_objects_from_signal

from indico.modules.agreements.models.agreements import Agreement
from indico.modules.agreements.notifications import notify_agreement_new


def get_agreement_definitions():
    return named_objects_from_signal(signals.agreements.get_definitions.send(), plugin_attr='plugin')


def send_new_agreements(event, name, people, email_body):
    """Creates and send agreements for a list of people on a given event.

    :param event: The `Conference` associated with the agreement
    :param name: The agreement type matcing a :class:`AgreementDefinition` name
    :param people: The list of people for whom agreements will be created
    :param email_body: The body of the email
    """
    agreements = []
    for person in people:
        agreement = Agreement.create_from_data(event_id=event.getId(), type=name, person=person)
        db.session.add(agreement)
        agreements.append(agreement)
    db.session.flush()
    for agreement in agreements:
        notify_agreement_new(agreement, email_body)
    return agreements
