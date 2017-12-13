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

from collections import OrderedDict, defaultdict

from flask import flash, redirect, request
from werkzeug.exceptions import NotFound

from indico.core.db.sqlalchemy.protection import ProtectionMode, render_acl
from indico.core.permissions import get_available_permissions
from indico.modules.events import Event
from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.modules.events.management.forms import EventProtectionForm
from indico.modules.events.management.views import WPEventProtection
from indico.modules.events.operations import update_event_protection
from indico.modules.events.sessions import COORDINATOR_PRIV_SETTINGS, session_settings
from indico.modules.events.sessions.operations import update_session_coordinator_privs
from indico.modules.events.util import get_object_from_args, update_object_principals
from indico.util import json
from indico.util.i18n import _
from indico.util.user import principal_from_fossil
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.forms.fields.principals import serialize_principal
from indico.web.util import jsonify_template


FULL_ACCESS_PERMISSION = '_full_access'
READ_ACCESS_PERMISSION = '_read_access'


def get_permissions_info():
    selectable_permissions = {k: v for k, v in get_available_permissions(Event).viewitems() if v.user_selectable}
    special_permissions = {FULL_ACCESS_PERMISSION: _('Manage'), READ_ACCESS_PERMISSION: _('Access')}
    permissions_tree = {
        FULL_ACCESS_PERMISSION: {
            'title': special_permissions[FULL_ACCESS_PERMISSION],
            'children': {
                v.name: {'title': v.friendly_name} for k, v in selectable_permissions.viewitems()
            }
        }
    }
    full_access_children = permissions_tree[FULL_ACCESS_PERMISSION]['children']
    full_access_children[READ_ACCESS_PERMISSION] = {'title': special_permissions[READ_ACCESS_PERMISSION]}
    full_access_children = OrderedDict(sorted(full_access_children.items()))
    available_permissions = dict({k: v.friendly_name for k, v in selectable_permissions.viewitems()},
                                 **special_permissions)
    return available_permissions, permissions_tree


class RHShowNonInheriting(RHManageEventBase):
    """Show a list of non-inheriting child objects"""

    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.obj = get_object_from_args()[2]
        if self.obj is None:
            raise NotFound

    def _process(self):
        objects = self.obj.get_non_inheriting_objects()
        return jsonify_template('events/management/non_inheriting_objects.html', objects=objects)


class RHEventACL(RHManageEventBase):
    """Display the inherited ACL of the event"""

    def _process(self):
        return render_acl(self.event)


class RHEventACLMessage(RHManageEventBase):
    """Render the inheriting ACL message"""

    def _process(self):
        mode = ProtectionMode[request.args['mode']]
        return jsonify_template('forms/protection_field_acl_message.html', object=self.event, mode=mode,
                                endpoint='event_management.acl')


class RHEventProtection(RHManageEventBase):
    """Show event protection"""

    NOT_SANITIZED_FIELDS = {'access_key'}

    def _process(self):
        form = EventProtectionForm(obj=FormDefaults(**self._get_defaults()), event=self.event)
        if form.validate_on_submit():
            permission_principals = defaultdict(set)
            for principal, permissions in form.permissions.data:
                for permission in permissions:
                    permission_principals[permission].add(principal_from_fossil(principal, allow_emails=True,
                                                                                allow_networks=True))
            available_permissions = get_permissions_info()[0]
            for permission in set(available_permissions):
                if permission == FULL_ACCESS_PERMISSION:
                    update_object_principals(self.event, permission_principals.get(permission, set()), full_access=True)
                elif permission == READ_ACCESS_PERMISSION:
                    update_object_principals(self.event, permission_principals.get(permission, set()), read_access=True)
                else:
                    update_object_principals(self.event, permission_principals.get(permission, set()),
                                             permission=permission)
            update_event_protection(self.event, {'protection_mode': form.protection_mode.data,
                                                 'own_no_access_contact': form.own_no_access_contact.data,
                                                 'access_key': form.access_key.data,
                                                 'visibility': form.visibility.data})
            self._update_session_coordinator_privs(form)
            flash(_('Protection settings have been updated'), 'success')
            return redirect(url_for('.protection', self.event))
        return WPEventProtection.render_template('event_protection.html', self.event, 'protection', form=form)

    def _get_defaults(self):
        registration_managers = {p.principal for p in self.event.acl_entries
                                 if p.has_management_permission('registration', explicit=True)}
        event_session_settings = session_settings.get_all(self.event)
        coordinator_privs = {name: event_session_settings[val] for name, val in COORDINATOR_PRIV_SETTINGS.iteritems()
                             if event_session_settings.get(val)}
        permissions = [[serialize_principal(p.principal), list(self._get_principal_permissions(p))]
                       for p in self.event.acl_entries if self._get_principal_permissions(p)]

        return dict({'protection_mode': self.event.protection_mode, 'registration_managers': registration_managers,
                     'access_key': self.event.access_key, 'visibility': self.event.visibility,
                     'own_no_access_contact': self.event.own_no_access_contact, 'permissions': permissions},
                    **coordinator_privs)

    def _update_session_coordinator_privs(self, form):
        data = {field: getattr(form, field).data for field in form.priv_fields}
        update_session_coordinator_privs(self.event, data)

    def _get_principal_permissions(self, principal):
        """Retrieve a set containing the valid permissions of a principal."""
        permissions = set()
        if principal.full_access:
            permissions.add(FULL_ACCESS_PERMISSION)
        if principal.read_access:
            permissions.add(READ_ACCESS_PERMISSION)
        available_permissions = get_permissions_info()[0]
        return permissions | (set(principal.permissions) & set(available_permissions))


class RHEventPermissionsDialog(RHManageEventBase):
    def _process(self):
        principal = json.loads(request.args['principal'])
        permissions_tree = get_permissions_info()[1]
        return jsonify_template('events/management/event_permissions_dialog.html', permissions_tree=permissions_tree,
                                permissions=request.args.getlist('permissions'), principal=principal)
