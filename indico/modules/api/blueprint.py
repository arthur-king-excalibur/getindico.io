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

from indico.web.flask.wrappers import IndicoBlueprint
from indico.web.http_api.handlers import handler as api_handler
from MaKaC.services.interface.rpc.json import process as jsonrpc_handler

api_blueprint = _bp = IndicoBlueprint('api', __name__, template_folder='templates')

# Legacy JSON-RPC API
_bp.add_url_rule('/services/json-rpc', view_func=jsonrpc_handler, endpoint='jsonrpc', methods=('POST',))

# HTTP API
_bp.add_url_rule('/export/<path:path>', view_func=api_handler, endpoint='httpapi', defaults={'prefix': 'export'})
_bp.add_url_rule('/api/<path:path>', view_func=api_handler, endpoint='httpapi', defaults={'prefix': 'api'},
                 methods=('POST',))
_bp.add_url_rule('/<any(api, export):prefix>', endpoint='httpapi', build_only=True)
