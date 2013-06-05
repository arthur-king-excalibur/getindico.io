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
from cStringIO import StringIO

import MaKaC.webinterface.pages.sessions as sessions
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common.general import *
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected,\
    RoomBookingDBMixin
from MaKaC.webinterface.rh.conferenceBase import RHSessionBase
from MaKaC.webinterface.common.contribFilters import SortingCriteria
from MaKaC.common import Config
from indico.web.flask.util import send_file
from indico.web.http_api.api import SessionHook
from indico.web.http_api.metadata.serializer import Serializer
from MaKaC.webinterface.common.tools import cleanHTMLHeaderFilename


class RHSessionDisplayBase( RHSessionBase, RHDisplayBaseProtected ):

    def _checkParams( self, params ):
        RHSessionBase._checkParams( self, params )

    def _checkProtection( self ):
        RHDisplayBaseProtected._checkProtection( self )


class RHSessionDisplay( RoomBookingDBMixin, RHSessionDisplayBase ):
    _uh = urlHandlers.UHSessionDisplay

    def _checkParams( self, params ):
        RHSessionDisplayBase._checkParams( self, params )

    def _process( self ):
        p = sessions.WPSessionDisplay(self,self._session)
        wf = self.getWebFactory()
        if wf != None:
            p=wf.getSessionDisplay(self,self._session)
        return p.display()

class RHSessionToiCal(RoomBookingDBMixin, RHSessionDisplay):

    def _process( self ):
        filename = "%s-Session.ics"%self._session.getTitle()

        hook = SessionHook({}, 'session', {'event': self._conf.getId(), 'idlist':self._session.getId(), 'dformat': 'ics'})
        res = hook(self.getAW())
        resultFossil = {'results': res[0]}

        serializer = Serializer.create('ics')
        return send_file(filename, StringIO(serializer(resultFossil)), 'ICAL', inline=True)


class RHSessionDisplayRemoveMaterial( RHSessionDisplay ):
    _uh = urlHandlers.UHSessionDisplayRemoveMaterial

    def _checkProtection(self):
        RHSessionDisplay._checkProtection(self)
        if not self._target.canModify( self.getAW() ):
            raise MaKaCError("you are not authorised to manage material for this session")

    def _checkParams( self, params ):
        RHSessionDisplay._checkParams( self, params )
        self._materialIds = self._normaliseListParam( params.get("deleteMaterial", []) )
        self._confirmed=params.has_key("confirm") or params.has_key("cancel")
        self._remove=params.has_key("confirm")

    def _process( self ):
        if self._materialIds != []:
            if self._confirmed:
                if self._remove:
                    for id in self._materialIds:
                        #Performing the deletion of special material types
                        f = materialFactories.SessionMFRegistry.getById( id )
                        if f:
                            f.remove( self._target )
                        else:
                            #Performs the deletion of additional material types
                            mat = self._target.getMaterialById( id )
                            self._target.removeMaterial( mat )
            else:
                for id in self._materialIds:
                    #Performing the deletion of special material types
                    f = materialFactories.SessionMFRegistry.getById( id )
                    if f:
                        mat=f.get(self._contrib)
                    else:
                        #Performs the deletion of additional material types
                        mat = self._target.getMaterialById( id )
                    break
                wp = sessions.WPSessionDisplayRemoveMaterialsConfirm(self, self._conf, mat)
                return wp.display()
        self._redirect( urlHandlers.UHSessionDisplay.getURL( self._target ) )
