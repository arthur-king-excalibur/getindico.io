# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import jsonify, request, session
from sqlalchemy.orm import subqueryload, undefer
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.core.db.sqlalchemy.protection import ProtectionMode, render_acl
from indico.modules.events import EventLogKind, EventLogRealm
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.management.controllers.base import RHContributionPersonListMixin
from indico.modules.events.sessions.controllers.management import (RHManageSessionBase, RHManageSessionsActionsBase,
                                                                   RHManageSessionsBase)
from indico.modules.events.sessions.forms import (MeetingSessionBlockForm, SessionForm, SessionProtectionForm,
                                                  SessionTypeForm)
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.sessions.models.types import SessionType
from indico.modules.events.sessions.operations import (create_session, delete_session, update_session,
                                                       update_session_block)
from indico.modules.events.sessions.util import (generate_pdf_from_sessions, generate_spreadsheet_from_sessions,
                                                 session_type_row)
from indico.modules.events.sessions.views import WPManageSessions
from indico.modules.events.util import get_random_color, update_object_principals
from indico.util.spreadsheets import send_csv, send_xlsx
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import send_file
from indico.web.forms.base import FormDefaults
from indico.web.forms.colors import get_colors
from indico.web.forms.util import get_form_field_names
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


def _get_session_list_args(event):
    sessions = (Session.query.with_parent(event)
                .options(undefer('attachment_count'),
                         subqueryload('blocks').undefer('contribution_count'))
                .order_by(db.func.lower(Session.title))
                .all())
    types = [{'id': int(t.id), 'title': t.name} for t in event.session_types]
    return {'sessions': sessions, 'default_colors': get_colors(), 'types': types}


def _render_session_list(event):
    tpl = get_template_module('events/sessions/management/_session_list.html')
    return tpl.render_session_list(event, **_get_session_list_args(event))


class RHSessionsList(RHManageSessionsBase):
    """Display list of all sessions within the event"""

    def _process(self):
        selected_entry = request.args.get('selected')
        selected_entry = int(selected_entry) if selected_entry else None
        return WPManageSessions.render_template('management/session_list.html', self.event,
                                                selected_entry=selected_entry,
                                                **_get_session_list_args(self.event))


class RHCreateSession(RHManageSessionsBase):
    """Create a session in the event"""

    def _get_response(self, new_session):
        sessions = [{'id': s.id, 'title': s.title, 'colors': s.colors} for s in self.event.sessions]
        return jsonify_data(sessions=sessions, new_session_id=new_session.id,
                            html=_render_session_list(self.event))

    def _process(self):
        inherited_location = self.event.location_data
        inherited_location['inheriting'] = True
        form = SessionForm(obj=FormDefaults(colors=get_random_color(self.event), location_data=inherited_location),
                           event=self.event)
        if form.validate_on_submit():
            new_session = create_session(self.event, form.data)
            return self._get_response(new_session)
        return jsonify_form(form)


class RHModifySession(RHManageSessionBase):
    """Modify a session"""

    def _process(self):
        form = SessionForm(obj=self.session, event=self.event)
        if form.validate_on_submit():
            update_session(self.session, form.data)
            return jsonify_data(html=_render_session_list(self.event))
        return jsonify_form(form)


class RHDeleteSessions(RHManageSessionsActionsBase):
    """Remove multiple sessions"""

    def _process(self):
        for sess in self.sessions:
            delete_session(sess)
        return jsonify_data(html=_render_session_list(self.event))


class RHManageSessionsExportBase(RHManageSessionsActionsBase):
    ALLOW_LOCKED = True


class RHExportSessionsCSV(RHManageSessionsExportBase):
    """Export list of sessions to a CSV"""

    def _process(self):
        headers, rows = generate_spreadsheet_from_sessions(self.sessions)
        return send_csv('sessions.csv', headers, rows)


class RHExportSessionsExcel(RHManageSessionsExportBase):
    """Export list of sessions to a XLSX"""

    def _process(self):
        headers, rows = generate_spreadsheet_from_sessions(self.sessions)
        return send_xlsx('sessions.xlsx', headers, rows)


class RHExportSessionsPDF(RHManageSessionsExportBase):
    """Export list of sessions to a PDF"""

    def _process(self):
        pdf_file = generate_pdf_from_sessions(self.sessions)
        return send_file('sessions.pdf', pdf_file, 'application/pdf')


class RHSessionREST(RHManageSessionBase):
    """Perform update or removal of a session"""

    def _process_DELETE(self):
        delete_session(self.session)
        return jsonify_data(html=_render_session_list(self.event))

    def _process_PATCH(self):
        data = request.json
        updates = {}
        if set(data.viewkeys()) > {'colors', 'type_id'}:
            raise BadRequest
        if 'colors' in data:
            colors = ColorTuple(**data['colors'])
            if colors not in get_colors():
                raise BadRequest
            updates['colors'] = colors
        if 'type_id' in data:
            updates.update(self._get_session_type_updates(data['type_id']))
        update_session(self.session, updates)
        return jsonify()

    def _get_session_type_updates(self, type_id):
        updates = {}
        if type_id is None:
            updates['type_id'] = None
        else:
            type = SessionType.get(type_id)
            if not type:
                raise BadRequest('Invalid type id')
            if not self.session.type or type_id != self.session.type.id:
                updates['type_id'] = type_id
        return updates


class RHSessionPersonList(RHContributionPersonListMixin, RHManageSessionsActionsBase):
    """List of persons in the session's contributions"""

    template = 'events/sessions/management/session_person_list.html'
    ALLOW_LOCKED = True

    @property
    def _membership_filter(self):
        session_ids = {s.id for s in self.sessions}
        return Contribution.session_id.in_(session_ids)


class RHSessionProtection(RHManageSessionBase):
    """Manage session protection"""

    def _process(self):
        form = SessionProtectionForm(obj=FormDefaults(**self._get_defaults()), session=self.session,
                                     prefix='session-protection-')
        if form.validate_on_submit():
            update_session(self.session, {'protection_mode': form.protection_mode.data})
            if self.session.is_protected:
                update_object_principals(self.session, form.acl.data, read_access=True)
            update_object_principals(self.session, form.managers.data, full_access=True)
            update_object_principals(self.session, form.coordinators.data, permission='coordinate')
            return jsonify_data(flash=False, html=_render_session_list(self.event))
        return jsonify_form(form)

    def _get_defaults(self):
        acl = {x.principal for x in self.session.acl_entries if x.read_access}
        managers = {x.principal for x in self.session.acl_entries if x.full_access}
        coordinators = {x.principal for x in self.session.acl_entries if x.has_management_permission('coordinate',
                                                                                                     explicit=True)}
        return {'managers': managers, 'protection_mode': self.session.protection_mode, 'coordinators': coordinators,
                'acl': acl}


class RHSessionACL(RHManageSessionBase):
    """Display the ACL of the session"""

    def _process(self):
        return render_acl(self.session)


class RHSessionACLMessage(RHManageSessionBase):
    """Render the inheriting ACL message"""

    def _process(self):
        mode = ProtectionMode[request.args['mode']]
        return jsonify_template('forms/protection_field_acl_message.html', object=self.session, mode=mode,
                                endpoint='sessions.acl')


class RHManageSessionBlock(RHManageSessionBase):
    """Manage a block of a session"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.session_block
        }
    }

    def _process_args(self):
        RHManageSessionBase._process_args(self)
        self.session_block = SessionBlock.get_one(request.view_args['block_id'])

    def _process(self):
        form = MeetingSessionBlockForm(obj=FormDefaults(**self._get_form_defaults()), event=self.event,
                                       session_block=self.session_block)
        if form.validate_on_submit():
            session_data = {k[8:]: v for k, v in form.data.iteritems() if k in form.session_fields}
            block_data = {k[6:]: v for k, v in form.data.iteritems() if k in form.block_fields}
            update_session(self.session, session_data)
            update_session_block(self.session_block, block_data)
            return jsonify_data(flash=False)
        self.commit = False
        return jsonify_template('events/forms/session_block_form.html', form=form, block=self.session_block)

    def _get_form_defaults(self):
        fields = get_form_field_names(MeetingSessionBlockForm)
        defaults = {}
        defaults.update((name, getattr(self.session, name[8:])) for name in fields if name.startswith('session_'))
        defaults.update((name, getattr(self.session_block, name[6:])) for name in fields if name.startswith('block_'))
        return defaults


class RHSessionBlocks(RHManageSessionBase):
    def _process(self):
        return jsonify_template('events/sessions/management/session_blocks.html', sess=self.session)


class RHManageSessionTypes(RHManageSessionsBase):
    """Dialog to manage the SessionTypes of an event"""

    def _process(self):
        types = self.event.session_types.all()
        return jsonify_template('events/sessions/management/types_dialog.html', event=self.event,
                                types=types)


class RHManageSessionTypeBase(RHManageSessionsBase):
    """Manage a session type of an event"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.session_type
        }
    }

    def _process_args(self):
        RHManageSessionsBase._process_args(self)
        self.session_type = SessionType.get_one(request.view_args['session_type_id'])


class RHEditSessionType(RHManageSessionTypeBase):
    """Dialog to edit a SessionType"""

    def _process(self):
        form = SessionTypeForm(event=self.event, obj=self.session_type)
        if form.validate_on_submit():
            old_name = self.session_type.name
            form.populate_obj(self.session_type)
            db.session.flush()
            self.event.log(EventLogRealm.management, EventLogKind.change, 'Sessions',
                           'Updated type: {}'.format(old_name), session.user)
            return jsonify_data(html_row=session_type_row(self.session_type), flash=False)
        return jsonify_form(form)


class RHCreateSessionType(RHManageSessionsBase):
    """Dialog to add a SessionType"""

    def _get_response(self, new_type):
        types = [{'id': t.id, 'title': t.name} for t in self.event.session_types]
        return jsonify_data(types=types, new_type_id=new_type.id,
                            html_row=session_type_row(new_type))

    def _process(self):
        form = SessionTypeForm(event=self.event)
        if form.validate_on_submit():
            session_type = SessionType()
            form.populate_obj(session_type)
            self.event.session_types.append(session_type)
            db.session.flush()
            self.event.log(EventLogRealm.management, EventLogKind.positive, 'Sessions',
                           'Added type: {}'.format(session_type.name), session.user)
            return self._get_response(session_type)
        return jsonify_form(form)


class RHDeleteSessionType(RHManageSessionTypeBase):
    """Dialog to delete a SessionType"""

    def _process(self):
        db.session.delete(self.session_type)
        db.session.flush()
        self.event.log(EventLogRealm.management, EventLogKind.negative, 'Sessions',
                       'Deleted type: {}'.format(self.session_type.name), session.user)
        return jsonify_data(flash=False)
