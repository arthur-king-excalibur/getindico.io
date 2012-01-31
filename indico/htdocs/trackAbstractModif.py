# -*- coding: utf-8 -*-
##
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

from MaKaC.webinterface.rh import trackModif


def index(req, **params):
    return trackModif.RHTrackAbstract( req ).process( params )


def proposeToBeAcc( req, **params ):
    return trackModif.RHTrackAbstractPropToAccept( req ).process( params )


def proposeToBeRej( req, **params ):
    return trackModif.RHTrackAbstractPropToReject( req ).process( params )


def abstractToPDF(req, **params):
    return trackModif.RHAbstractToPDF( req ).process( params )


def directAccess(req, **params):
    return trackModif.RHTrackAbstractDirectAccess( req ).process( params )  


def proposeForOtherTracks( req, **params ):
    return trackModif.RHTrackAbstractPropForOtherTracks( req ).process( params )


def comments(req,**params):
    return trackModif.RHAbstractIntComments( req ).process( params )


def commentNew(req,**params):
    return trackModif.RHAbstractIntCommentNew( req ).process( params )


def commentEdit(req,**params):
    return trackModif.RHAbstractIntCommentEdit( req ).process( params )


def commentRem(req,**params):
    return trackModif.RHAbstractIntCommentRem( req ).process( params )

def abstractAction( req, **params ):
    return trackModif.RHAbstractsActions( req ).process( params )

def markAsDup(req,**params):
    return trackModif.RHModAbstractMarkAsDup( req ).process( params )

def unMarkAsDup(req,**params):
    return trackModif.RHModAbstractUnMarkAsDup( req ).process( params )
