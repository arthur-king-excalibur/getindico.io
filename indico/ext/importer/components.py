# -*- coding: utf-8 -*-
##
## $id$
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

import os
import zope.interface
from webassets import Bundle, Environment

from indico.core.extpoint import Component
from indico.core.extpoint.events import ITimetableContributor
from MaKaC.plugins.base import Observable
from MaKaC.common.Configuration import Config
from indico.ext.importer.handlers import RHImporterHtdocs
from MaKaC.common.info import HelperMaKaCInfo

class ImporterContributor(Component, Observable):
    """
    Adds interface extension to event's timetable modification websites.
    """

    zope.interface.implements(ITimetableContributor)

    @classmethod
    def includeTimetableJSFiles(cls, obj, params = {}):
        """
        Includes additional javascript file.
        """
        info = HelperMaKaCInfo.getMaKaCInfoInstance()
        asset_env = Environment( RHImporterHtdocs._local_path, '/importer')
        asset_env.debug = info.isDebugActive()

        asset_env.register('importer', Bundle('js/importer.js',
                                                           filters='jsmin',
                                                           output="importer__%(version)s.min.js"))
        params['paths'].extend(asset_env['importer'].urls())

    @classmethod
    def includeTimetableCSSFiles(cls, obj, params = {}):
        """
        Includes additional Css files.
        """
        params['paths'].append("importer/importer.css")

    @classmethod
    def customTimetableLinks(cls, obj, params = {}):
        """
        Inserts an "Import" link in a timetable header.
        """
        params.update({"Import" : "createImporterDialog"})