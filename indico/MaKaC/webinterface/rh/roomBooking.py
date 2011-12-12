# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
from MaKaC.plugins.base import pluginId

# Most of the following imports are probably not necessary - to clean

import os,time,re
from collections import defaultdict

import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.locators as locators
from MaKaC.common.general import *
from MaKaC.common.Configuration import Config
from MaKaC.webinterface.rh.base import RoomBookingDBMixin, RHRoomBookingProtected
from datetime import datetime, timedelta, date
from MaKaC.common.utils import validMail, setValidEmailSeparators, parseDate
from MaKaC.common.datetimeParser import parse_date

# The following are room booking related

import MaKaC.webinterface.pages.roomBooking as roomBooking_wp
import MaKaC.webinterface.pages.admins as admins
from MaKaC.rb_room import RoomBase
from MaKaC.rb_reservation import ReservationBase, RepeatabilityEnum
from MaKaC.rb_factory import Factory
from MaKaC.rb_location import CrossLocationQueries, RoomGUID, Location
from MaKaC.rb_tools import intd, FormMode, doesPeriodsOverlap
from MaKaC.errors import MaKaCError, FormValuesError, NoReportError
from MaKaC.plugins import PluginLoader
from MaKaC import plugins
from MaKaC.plugins.RoomBooking.default.reservation import ResvHistoryEntry
from MaKaC.plugins.RoomBooking.default.room import Room
from MaKaC.plugins.RoomBooking.rb_roomblocking import RoomBlockingBase
from MaKaC.plugins.RoomBooking.default.roomblocking import RoomBlockingPrincipal,\
    BlockedRoom
from MaKaC.plugins.RoomBooking.common import getRoomBookingOption
from MaKaC.common.mail import GenericMailer
from MaKaC.common.cache import GenericCache

class CandidateDataFrom( object ):
    DEFAULTS, PARAMS, SESSION = xrange( 3 )

# 0. Base classes

class RoomBookingAvailabilityParamsMixin:
    def _checkParamsRepeatingPeriod( self, params ):
        """
        Extracts startDT, endDT and repeatability
        from the form, if present.

        Assigns these values to self, or Nones if values
        are not present.
        """

        sDay = params.get( "sDay" )
        eDay = params.get( "eDay" )
        sMonth = params.get( "sMonth" )
        eMonth = params.get( "eMonth" )
        sYear = params.get( "sYear" )
        eYear = params.get( "eYear" )

        if sDay and len( sDay.strip() ) > 0:
            sDay = int( sDay.strip() )

        if eDay and len( eDay.strip() ) > 0:
            eDay = int( eDay.strip() )

        if sMonth and len( sMonth.strip() ) > 0:
            sMonth = int( sMonth.strip() )

#        if sYear and sMonth and sDay:
#            # For format checking
#            try:
#                time.strptime(sDay.strip() + "/" + sMonth.strip() + "/" + sYear.strip() , "%d/%m/%Y")
#            except ValueError:
#                raise NoReportError(_("The Start Date must be of the form DD/MM/YYYY and must be a valid date."))

        if eMonth and len( eMonth.strip() ) > 0:
            eMonth = int( eMonth.strip() )

        if sYear and len( sYear.strip() ) > 0:
            sYear = int( sYear.strip() )

        if eYear and len( eYear.strip() ) > 0:
            eYear = int( eYear.strip() )

#        if eYear and eMonth and eDay:
#            # For format checking
#            try:
#                time.strptime(eDay.strip() + "/" + eMonth.strip() + "/" + eYear.strip() , "%d/%m/%Y")
#            except ValueError:
#                raise NoReportError(_("The End Date must be of the form DD/MM/YYYY and must be a valid date."))


        sTime = params.get( "sTime" )
        if sTime and len( sTime.strip() ) > 0:
            sTime = sTime.strip()
        eTime = params.get( "eTime" )
        if eTime and len( eTime.strip() ) > 0:
            eTime = eTime.strip()

        # process sTime and eTime
        if sTime and eTime:

            try:
                time.strptime(sTime, "%H:%M")
            except ValueError:
                raise NoReportError(_("The Start Time must be of the form HH:MM and must be a valid time."))

            t = sTime.split( ':' )
            sHour = int( t[0] )
            sMinute = int( t[1] )

            try:
                time.strptime(eTime, "%H:%M")
            except ValueError:
                raise NoReportError(_("The End Time must be of the form HH:MM and must be a valid time."))

            t = eTime.split( ':' )
            eHour = int( t[0] )
            eMinute = int( t[1] )

        repeatability = params.get( "repeatability" )
        if repeatability and len( repeatability.strip() ) > 0:
            if repeatability == "None":
                repeatability = None
            else:
                repeatability = int( repeatability.strip() )

        self._startDT = None
        self._endDT = None
        self._repeatability = repeatability
        if sYear and sMonth and sDay and sTime and eYear and eMonth and eDay and eTime:
            # Full period specified
            self._startDT = datetime( sYear, sMonth, sDay, sHour, sMinute )
            self._endDT = datetime( eYear, eMonth, eDay, eHour, eMinute )
        elif sYear and sMonth and sDay and eYear and eMonth and eDay:
            # There are no times
            self._startDT = datetime( sYear, sMonth, sDay, 0, 0, 0 )
            self._endDT = datetime( eYear, eMonth, eDay, 23, 59, 59 )
        elif sTime and eTime:
            # There are no dates
            self._startDT = datetime( 1990, 1, 1, sHour, sMinute )
            self._endDT = datetime( 2030, 12, 31, eHour, eMinute )
        self._today=False
        if params.get( "day", "" ) == "today":
            self._today=True
            self._startDT = datetime.today().replace(hour=0,minute=0,second=0)
            self._endDT = self._startDT.replace(hour=23,minute=59,second=59)

class RHRoomBookingBase( RoomBookingAvailabilityParamsMixin, RoomBookingDBMixin, RHRoomBookingProtected ):
    """
    All room booking related hanlders are derived from this class.
    This gives them:
    - several general use methods
    - login-protection
    - auto connecting/disconnecting from room booking db
    """

    def _checkProtection( self ):
        RHRoomBookingProtected._checkProtection(self)

    def _clearSessionState( self ):
        session = self._websession

        session.setVar( "actionSucceeded", None )
        session.setVar( "deletionFailed", None )
        session.setVar( "formMode", None )

        session.setVar( "candDataInSession", None )
        session.setVar( "candDataInParams", None )
        session.setVar( "afterCalPreview", None )

        session.setVar( "showErrors", False )
        session.setVar( "errors", None )
        session.setVar( "thereAreConflicts", None )

        session.setVar( "roomID", None )
        session.setVar( "roomLocation", None )
        session.setVar( "resvID", None )

    # Room

    def _saveRoomCandidateToSession( self, c ):
        # TODO: is this method needed anymore??
        session = self._websession     # Just an alias
        if self._formMode == FormMode.MODIF:
            session.setVar( "roomID", c.id )
            session.setVar( "roomLocation", c.locationName )

        session.setVar( "name", c.name )
        session.setVar( "site", c.site )
        session.setVar( "building", c.building )
        session.setVar( "floor", c.floor )
        session.setVar( "roomNr", c.roomNr )
        session.setVar( "latitude", c.latitude )
        session.setVar( "longitude", c.longitude )

        session.setVar( "isActive", c.isActive )
        session.setVar( "isReservable", c.isReservable )
        session.setVar( "resvsNeedConfirmation", c.resvsNeedConfirmation )
        session.setVar( "resvStartNotification", c.resvStartNotification )
        session.setVar( "resvStartNotificationBefore", c.resvStartNotificationBefore )
        session.setVar( "resvEndNotification", c.resvEndNotification )
        session.setVar( "resvNotificationToResponsible", c.resvNotificationToResponsible )

        session.setVar( "responsibleId", c.responsibleId )
        session.setVar( "whereIsKey", c.whereIsKey )
        session.setVar( "telephone", c.telephone )

        session.setVar( "capacity", c.capacity )
        session.setVar( "division", c.division )
        session.setVar( "surfaceArea", c.surfaceArea )
        session.setVar( "comments", c.comments )

        session.setVar( "equipment", c.getEquipment() )
        for name, value in c.customAtts.iteritems():
            session.setVar( "cattr_" + name, value )

    def _getErrorsOfRoomCandidate( self, c ):
        errors = []
        #if not c.site:
        #    errors.append( "Site can not be blank" )
        if not c.floor:
            errors.append( "Floor can not be blank" )
        if not c.roomNr:
            errors.append( "Room number can not be blank" )
        if not c.responsibleId:
            errors.append( "Room must have a responsible person" )
        if not c.building or c.building < 1:
            errors.append( "Building must be a positive integer" )
        if not c.capacity or c.capacity < 1:
            errors.append( "Capacity must be a positive integer" )

        try:
            if c.longitude and float(c.longitude) < 0:
                errors.append("Longitude must be a positive number")
        except ValueError:
            errors.append("Longitude must be a number")

        try:
            if c.latitude and float(c.latitude) < 0:
                errors.append("Latitude must be a positive number")
        except ValueError:
            errors.append("Latitude must be a number")

        params = self._params
        if ( params['largePhotoPath'] != '' ) ^ ( params['smallPhotoPath'] != '' ):
            errors.append( "Either upload both photos or none")

        # Custom attributes
        manager = CrossLocationQueries.getCustomAttributesManager( c.locationName )
        for ca in manager.getAttributes( location = c.locationName ):
            if ca['name'] == 'notification email' :
                if c.customAtts[ 'notification email' ] and not validMail(c.customAtts['notification email']) :
                    errors.append( "Invalid format for the notification email" )
            if ca['required']:
                if not c.customAtts.has_key( ca['name'] ): # not exists
                    errors.append( ca['name'] + " can not be blank" )
                elif not c.customAtts[ ca['name'] ]:       # is empty
                    errors.append( ca['name'] + " can not be blank" )

        return errors

    def _loadRoomCandidateFromDefaults( self, candRoom ):
        candRoom.isActive = True

        candRoom.building = None
        candRoom.floor = ''
        candRoom.roomNr = ''
        candRoom.longitude = ''
        candRoom.latitude = ''

        candRoom.capacity = 20
        candRoom.site = ''
        candRoom.division = None
        candRoom.isReservable = True
        candRoom.resvsNeedConfirmation = False
        candRoom.resvStartNotification = False
        candRoom.resvStartNotificationBefore = None
        candRoom.resvEndNotification = False
        candRoom.resvNotificationToResponsible = False
        candRoom.photoId = None
        candRoom.externalId = None

        candRoom.telephone = ''      # str
        candRoom.surfaceArea = None
        candRoom.whereIsKey = ''
        candRoom.comments = ''
        candRoom.responsibleId = None

    def _loadRoomCandidateFromSession( self, candRoom ):
        session = self._websession # Just an alias

        candRoom.name = session.getVar( "name" )
        candRoom.site = session.getVar( "site" )
        candRoom.building = intd( session.getVar( "building" ) )
        candRoom.floor = session.getVar( "floor" )
        candRoom.roomNr = session.getVar( "roomNr" )
        candRoom.latitude = session.getVar( "latitude" )
        candRoom.longitude = session.getVar( "longitude" )

        candRoom.isActive = bool( session.getVar( "isActive" ) )
        candRoom.isReservable = bool( session.getVar( "isReservable" ) )
        candRoom.resvsNeedConfirmation = bool( session.getVar( "resvsNeedConfirmation" ) )
        candRoom.resvStartNotification = session.getVar("resvStartNotification")
        candRoom.resvStartNotificationBefore = session.getVar("resvStartNotificationBefore")
        candRoom.resvEndNotification = bool( session.getVar( "resvEndNotification" ) )
        candRoom.resvNotificationToResponsible = bool( session.getVar( "resvNotificationToResponsible" ) )

        candRoom.responsibleId = session.getVar( "responsibleId" )
        candRoom.whereIsKey = session.getVar( "whereIsKey" )
        candRoom.telephone = session.getVar( "telephone" )

        candRoom.capacity = intd( session.getVar( "capacity" ) )
        candRoom.division = session.getVar( "division" )
        candRoom.surfaceArea = intd( session.getVar( "surfaceArea" ) )
        candRoom.comments = session.getVar( "comments" )

        candRoom.setEquipment( session.getVar( "equipment" ) )

        manager = CrossLocationQueries.getCustomAttributesManager( candRoom.locationName )
        for ca in manager.getAttributes( location = candRoom.locationName ):
            value = session.getVar( "cattr_" + ca['name'] )
            if value != None:
                if ca['name'] == 'notification email' :
                    candRoom.customAtts[ 'notification email' ] = setValidEmailSeparators(value)
                else :
                    candRoom.customAtts[ ca['name'] ] = value


    def _loadRoomCandidateFromParams( self, candRoom, params ):
        candRoom.name = params.get( "name" )
        candRoom.site = params.get( "site" )
        candRoom.building = intd( params.get( "building" ) )
        candRoom.floor = params.get( "floor" )
        candRoom.roomNr = params.get( "roomNr" )
        candRoom.latitude = params.get( "latitude" )
        candRoom.longitude = params.get( "longitude" )

        candRoom.isActive = bool( params.get( "isActive" ) ) # Safe
        candRoom.isReservable = bool( params.get( "isReservable" ) ) # Safe
        candRoom.resvsNeedConfirmation = bool( params.get( "resvsNeedConfirmation" ) ) # Safe
        candRoom.resvStartNotification = bool( params.get( "resvStartNotification" ) )
        tmp = params.get("resvStartNotificationBefore")
        candRoom.resvStartNotificationBefore = intd(tmp) if tmp else None
        candRoom.resvEndNotification = bool( params.get( "resvEndNotification" ) )
        candRoom.resvNotificationToResponsible = bool(params.get('resvNotificationToResponsible'))


        candRoom.responsibleId = params.get( "responsibleId" )
        if candRoom.responsibleId == "None":
            candRoom.responsibleId = None
        candRoom.whereIsKey = params.get( "whereIsKey" )
        candRoom.telephone = params.get( "telephone" )

        candRoom.capacity = intd( params.get( "capacity" ) )
        candRoom.division = params.get( "division" )
        candRoom.surfaceArea = intd( params.get( "surfaceArea" ) )
        candRoom.comments = params.get( "comments" )
        #TODO: change this in order to support many periods
        candRoom.clearNonBookableDates()
        if params.get("startDateNonBookablePeriod0", "") and params.get("endDateNonBookablePeriod0",""):
            candRoom.addNonBookableDateFromParams({"startDate": datetime(*(time.strptime(params.get("startDateNonBookablePeriod0"), '%d/%m/%Y')[0:6])),
                                                   "endDate": datetime(*(time.strptime(params.get("endDateNonBookablePeriod0"), '%d/%m/%Y')[0:6]))})

        eqList = []
        vcList = []
        for k, v in params.iteritems():
            if k.startswith( "equ_" ) and v:
                eqList.append(k[4:len(k)])
            if k.startswith( "vc_" ) and v:
                vcList.append(k[3:])
        candRoom.setEquipment( eqList )
        candRoom.setAvailableVC(vcList)

        for k, v in params.iteritems():
            if k.startswith( "cattr_" ):
                attrName = k[6:len(k)]
                if attrName == 'notification email' :
                    candRoom.customAtts['notification email'] = setValidEmailSeparators(v)
                else :
                    candRoom.customAtts[attrName] = v

    # Resv

    def _saveResvCandidateToSession( self, c ):
        session = self._websession
        if self._formMode == FormMode.MODIF:
            session.setVar( "resvID", c.id )
            session.setVar( "roomLocation", c.locationName )
        session.setVar( "roomID", c.room.id )
        session.setVar( "startDT", c.startDT )
        session.setVar( "endDT", c.endDT )
        session.setVar( "repeatability", c.repeatability )
        session.setVar( "bookedForId", c.bookedForId )
        if c.bookedForId:
            session.setVar( "bookedForName", c.bookedForUser.getFullName() )
        else:
            session.setVar( "bookedForName", c.bookedForName )
        session.setVar( "contactPhone", c.contactPhone )
        session.setVar( "contactEmail", c.contactEmail )
        session.setVar( "reason", c.reason )
        session.setVar( "usesAVC", c.usesAVC )
        session.setVar( "needsAVCSupport", c.needsAVCSupport )

        if hasattr(self, '_skipConflicting'):
            if self._skipConflicting:
                skip = 'on'
            else:
                skip = 'off'
            session.setVar( "skipConflicting", skip )

        if hasattr(c, "useVC"):
            session.setVar( "useVC",  c.useVC)


    def _getErrorsOfResvCandidate( self, c ):
        errors = []
        self._thereAreConflicts = False
        if getRoomBookingOption('bookingsForRealUsers') and not c.bookedForUser:
            errors.append( "Booked for can not be blank" )
        elif not getRoomBookingOption('bookingsForRealUsers') and not c.bookedForName:
            errors.append( "Booked for can not be blank" )
        if not c.reason:
            errors.append( "Purpose can not be blank" )
        if not c.isRejected and not c.isCancelled:
            collisions = c.getCollisions( sansID = self._candResv.id )
            if len( collisions ) > 0:
                if self._skipConflicting and c.startDT.date() != c.endDT.date():
                    for collision in collisions:
                        c.excludeDay( collision.startDT.date() )
                else:
                    self._thereAreConflicts = True
                    errors.append( "There are conflicts with other bookings" )
            blockedDates = c.getBlockedDates(c.createdByUser())
            if len( blockedDates ):
                if self._skipConflicting and c.startDT.date() != c.endDT.date():
                    for blockedDate in blockedDates:
                        c.excludeDay( blockedDate )
                else:
                    self._thereAreConflicts = True
                    errors.append( "There are conflicts with blockings" )

        return errors

    def _loadResvCandidateFromSession( self, candResv, params ):
        # After successful searching or failed save
        session = self._websession

        roomID = params['roomID']
        if isinstance( roomID, list ):
            roomID = int( roomID[0] )
        else:
            roomID = int( roomID )
        roomLocation = params.get( "roomLocation" )
        if isinstance( roomLocation, list ):
            roomLocation = roomLocation[0]
        if not roomLocation:
            roomLocation = session.getVar( "roomLocation" )

        if not candResv:
            candResv = Location.parse( roomLocation ).factory.newReservation() # The same location as for room

        if not candResv.room:
            candResv.room = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )
        candResv.startDT = session.getVar( "startDT" )
        candResv.endDT = session.getVar( "endDT" )
        candResv.repeatability = session.getVar( "repeatability" )
        candResv.bookedForId = session.getVar( "bookedForId" )
        candResv.bookedForName = session.getVar( "bookedForName" )
        candResv.contactPhone = session.getVar( "contactPhone" )
        candResv.contactEmail = setValidEmailSeparators(session.getVar( "contactEmail" ))
        candResv.reason = session.getVar( "reason" )
        candResv.usesAVC = session.getVar( "usesAVC" )
        candResv.needsAVCSupport = session.getVar( "needsAVCSupport" )
        self._skipConflicting = session.getVar( "skipConflicting" ) == "on"

        useVC = session.getVar('useVC')
        if useVC is not None:
            candResv.useVC = useVC

        return candResv

    def _loadResvCandidateFromParams( self, candResv, params ):
        # After calendar preview
        roomID = params['roomID']
        if isinstance( roomID, list ):
            roomID = int( roomID[0] )
        else:
            roomID = int( roomID )
        roomLocation = params.get( "roomLocation" )
        if isinstance( roomLocation, list ):
            roomLocation = roomLocation[0]
        if not candResv:
            candResv = Location.parse( roomLocation ).factory.newReservation() # The same location as room
        if not candResv.room:
            candResv.room = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )
        self._checkParamsRepeatingPeriod( params )
        candResv.startDT = self._startDT
        candResv.endDT = self._endDT
        candResv.repeatability = self._repeatability
        candResv.bookedForId = params.get("bookedForId")
        candResv.bookedForName = params.get("bookedForName")
        candResv.contactEmail = setValidEmailSeparators(params["contactEmail"])
        candResv.contactPhone = params["contactPhone"]
        candResv.reason = params["reason"]
        candResv.usesAVC = params.get( "usesAVC" ) == "on"
        candResv.needsAVCSupport = params.get( "needsAVCSupport" ) == "on"
        self._skipConflicting = params.get( "skipConflicting" ) == "on"
        d = {}
        for vc in candResv.room.getAvailableVC():
            d[vc[:3]] = vc
        candResv.useVC = []
        for param in params:
            if len(param) > 3 and param[:3] == "vc_":
                vc = d.get(param[3:], None)
                if vc:
                    candResv.useVC.append(vc)
        return candResv

    def _loadResvCandidateFromDefaults( self, params ):
        ws = self._websession
        # After room details
        if not params.has_key('roomID'):
            raise MaKaCError( _("""The parameter roomID is missing."""))
        if not params.has_key('roomLocation'):
            raise MaKaCError( _("""The parameter roomLocation is missing"""))
        roomID = int( params['roomID'] )
        roomLocation = params['roomLocation']
        candResv = Location.parse( roomLocation ).factory.newReservation() # Create in the same location as room
        if not candResv.room:
            candResv.room = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )
        # Generic defaults
        now = datetime.now()
        if now.weekday() in [4,5]:
            now = now + timedelta( 7 - now.weekday() )
        else:
            now = now + timedelta( 1 )

        # Sets the dates if needed
        dayD = params.get("day")
        monthM = params.get("month")
        yearY = params.get("year")
        dayEnd = params.get("dayEnd")
        monthEnd = params.get("monthEnd")
        yearEnd = params.get("yearEnd")

        hourStart = params.get("hour")
        minuteStart = params.get("minute")
        hourEnd = params.get("hourEnd")
        minuteEnd = params.get("minuteEnd")
        repeatability = params.get("repeatability")

        if hourStart and minuteStart and hourStart.isdigit() and minuteStart.isdigit():
            hourStart = int(hourStart)
            minuteStart = int(minuteStart)
        else:
            hourStart = 8
            minuteStart = 30

        if hourEnd and minuteEnd and hourEnd.isdigit() and minuteEnd.isdigit():
            hourEnd = int(hourEnd)
            minuteEnd = int(minuteEnd)
        else:
            hourEnd = 17
            minuteEnd = 30

        if dayD != None and dayD.isdigit() and \
           monthM != None and monthM.isdigit() and \
           yearY != None and yearY.isdigit():
            candResv.startDT = datetime(int(yearY), int(monthM), int(dayD), hourStart, minuteStart)
            if dayEnd != None and dayEnd.isdigit() and \
               monthEnd != None and monthEnd.isdigit() and \
               yearEnd!= None and yearEnd.isdigit():
                candResv.endDT = datetime(int(yearEnd), int(monthEnd), int(dayEnd), hourEnd, minuteEnd)
                if candResv.endDT.date() != candResv.startDT.date() and candResv.repeatability is None:
                    candResv.repeatability = RepeatabilityEnum.daily
            else:
                candResv.endDT = datetime(int(yearY), int(monthM), int(dayD), hourEnd, minuteEnd)
        else:
            if candResv.startDT == None:
                candResv.startDT = datetime( now.year, now.month, now.day, hourStart, minuteStart )
            if candResv.endDT == None:
                candResv.endDT = datetime( now.year, now.month, now.day, hourEnd, minuteEnd )
        if repeatability is not None:
            if repeatability == 'None':
                candResv.repeatability = None
            else:
                candResv.repeatability = int(repeatability)
        if self._getUser():
            if candResv.bookedForUser is None:
                candResv.bookedForUser = self._getUser()
            if candResv.bookedForName == None:
                candResv.bookedForName = self._getUser().getFullName()
            if candResv.contactEmail == None:
                candResv.contactEmail = self._getUser().getEmail()
            if candResv.contactPhone == None:
                candResv.contactPhone = self._getUser().getTelephone()
        else:
            candResv.bookedForUser = None
            candResv.bookedForName = candResv.contactEmail = candResv.contactPhone = ""
        if candResv.reason == None:
            candResv.reason = ""
        if candResv.usesAVC == None:
            candResv.usesAVC = False
        if candResv.needsAVCSupport == None:
            candResv.needsAVCSupport = False

        if not ws.getVar( "dontAssign" ) and not params.get("ignoreSession"):
            if ws.getVar( "defaultStartDT" ):
                candResv.startDT = ws.getVar( "defaultStartDT" )
            if ws.getVar( "defaultEndDT" ):
                candResv.endDT = ws.getVar( "defaultEndDT" )
            if ws.getVar( "defaultRepeatability" ) != None:
                candResv.repeatability = ws.getVar( "defaultRepeatability" )
            if ws.getVar( "defaultBookedForId" ):
                candResv.bookedForId = ws.getVar( "defaultBookedForId" )
            if ws.getVar( "defaultBookedForName" ):
                candResv.bookedForName = ws.getVar( "defaultBookedForName" )
            if ws.getVar( "defaultReason" ):
                candResv.reason = ws.getVar( "defaultReason" )

            if ws.getVar( "assign2Session" ):
                self._assign2Session = ws.getVar( "assign2Session" )
            if ws.getVar( "assign2Contribution" ):
                self._assign2Contributioon = ws.getVar( "assign2Contribution" )

        return candResv


class RHRoomBookingAdminBase( RHRoomBookingBase ):
    """
    Adds admin authorization. All classes that implement admin
    tasks should be derived from this class.
    """
    def _checkProtection( self ):
        if self._getUser() == None:
            self._checkSessionUser()
        elif not self._getUser().isRBAdmin():
            raise MaKaCError( "You are not authorized to take this action." )

class RHRoomBookingWelcome( RHRoomBookingBase ):
    _uh = urlHandlers.UHRoomBookingWelcome

    def _process( self ):
        if Location.getDefaultLocation() and Location.getDefaultLocation().isMapAvailable():
            self._redirect( urlHandlers.UHRoomBookingMapOfRooms.getURL())
        else:
            self._redirect( urlHandlers.UHRoomBookingSearch4Rooms.getURL( forNewBooking = True ))


# 1. Searching

class RHRoomBookingSearch4Rooms( RHRoomBookingBase ):

    def _cleanDefaultsFromSession( self ):
        websession = self._websession
        websession.setVar( "defaultStartDT", None )
        websession.setVar( "defaultEndDT", None )
        websession.setVar( "defaultRepeatability", None )
        websession.setVar( "defaultBookedForId", None )
        websession.setVar( "defaultBookedForName", None )
        websession.setVar( "defaultReason", None )
        websession.setVar( "assign2Session", None )
        websession.setVar( "assign2Contribution", None )

    def _setGeneralDefaultsInSession( self ):
        now = datetime.now()

        # if it's saturday or sunday, postpone for monday as a default
        if now.weekday() in [5,6]:
            now = now + timedelta( 7 - now.weekday() )

        websession = self._websession
        websession.setVar( "defaultStartDT", datetime( now.year, now.month, now.day, 8, 30 ) )
        websession.setVar( "defaultEndDT", datetime( now.year, now.month, now.day, 17, 30 ) )

    def _checkParams( self, params ):
        self._cleanDefaultsFromSession()
        self._setGeneralDefaultsInSession()
        self._forNewBooking = False
        self._eventRoomName = None
        if params.get( 'forNewBooking' ):
            self._forNewBooking = params.get( 'forNewBooking' ) == 'True'

    def _businessLogic( self ):
        self._rooms = CrossLocationQueries.getRooms( allFast = True )
        self._rooms.sort()
        self._equipment = CrossLocationQueries.getPossibleEquipment()

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingSearch4Rooms( self, self._forNewBooking )
        return p.display()

class RHRoomBookingSearch4Bookings( RHRoomBookingBase ):

    def _businessLogic( self ):
        self._rooms = CrossLocationQueries.getRooms( allFast = True )
        self._rooms.sort()

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingSearch4Bookings( self )
        return p.display()

class RHRoomBookingSearch4Users( RHRoomBookingBase ):

    def _checkParams( self, params ):

        roomID = params.get( "roomID" )
        roomLocation = params.get( "roomLocation" )
        candRoom = None
        if roomID:
            self._formMode = FormMode.MODIF
            roomID = int( roomID )
            candRoom = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )
        else:
            self._formMode = FormMode.NEW
            candRoom = Factory.newRoom()  # Is it OK? Potential bug.

        self._loadRoomCandidateFromParams( candRoom, params )
        self._saveRoomCandidateToSession( candRoom )

        # Set session
        self._websession.setVar( "showErrors", False )
        self._websession.setVar( "candDataInSession", True )

        if params.has_key( 'largePhotoPath' ): del params['largePhotoPath']
        if params.has_key( 'smallPhotoPath' ): del params['smallPhotoPath']

        self._forceWithoutExtAuth = True
        if params.has_key( 'searchExt' )  and  params['searchExt'] == 'Nice':
            self._forceWithoutExtAuth = False

    def _process( self ):
        p = roomBooking_wp.WPRoomBookingSearch4Users( self )
        return p.display( **self._getRequestParams() )

class RHRoomBookingMapOfRooms(RHRoomBookingBase):

    def _checkParams(self, params):
        RHRoomBookingBase._checkParams(self, params)
        self._roomID = params.get('roomID')

    def _process(self):
        params = {}
        if self._roomID:
            params['roomID'] = self._roomID
        page = roomBooking_wp.WPRoomBookingMapOfRooms(self, **params)
        return page.display()

class RHRoomBookingMapOfRoomsWidget(RHRoomBookingBase):

    def __init__(self, *args, **kwargs):
        RHRoomBookingBase.__init__(self, *args, **kwargs)
        self._cache = GenericCache('MapOfRooms')

    def _setGeneralDefaultsInSession( self ):
        now = datetime.now()

        # if it's saturday or sunday, postpone for monday as a default
        if now.weekday() in [5,6]:
            now = now + timedelta( 7 - now.weekday() )

        websession = self._websession
        websession.setVar( "defaultStartDT", datetime( now.year, now.month, now.day, 8, 30 ) )
        websession.setVar( "defaultEndDT", datetime( now.year, now.month, now.day, 17, 30 ) )

    def _checkParams(self, params):
        self._setGeneralDefaultsInSession()
        RHRoomBookingBase._checkParams(self, params)
        self._roomID = params.get('roomID')

    def _businessLogic(self):
        # get all rooms
        defaultLocation = Location.getDefaultLocation()
        rooms = RoomBase.getRooms(location=defaultLocation.friendlyName)
        aspects = [aspect.toDictionary() for aspect in defaultLocation.getAspects()]

        # specialization for a video conference, CERN-specific
        possibleEquipment = defaultLocation.factory.getEquipmentManager().getPossibleEquipment()
        possibleVideoConference = 'Video conference' in possibleEquipment
        self._forVideoConference = possibleVideoConference and self._getRequestParams().get("avc") == 'y'

        # break-down the rooms by buildings
        buildings = {}
        for room in rooms:
            if room.building:

                # if it's the first room in that building, initialize the building
                building = buildings.get(room.building, None)
                if building is None:
                    title = _("Building") + " %s" % room.building
                    building = {'has_coordinates':False, 'number':room.building, 'title':title, 'rooms':[]}
                    buildings[room.building] = building

                # if the room has coordinates, set the building coordinates
                if room.latitude and room.longitude:
                    building['has_coordinates'] = True
                    building['latitude'] = room.latitude
                    building['longitude'] = room.longitude

                # add the room to its building
                if not self._forVideoConference or room.needsAVCSetup:
                    building['rooms'].append(room.fossilize())

        # filter the buildings with rooms and coordinates and return them
        buildings_with_coords = [b for b in buildings.values() if b['rooms'] and b['has_coordinates']]
        self._defaultLocation = defaultLocation.friendlyName
        self._aspects = aspects
        self._buildings = buildings_with_coords

    def _process(self):
        params = self._getRequestParams()
        html = self._cache.get(params)
        if not html:
            self._businessLogic()
            page = roomBooking_wp.WPRoomBookingMapOfRoomsWidget(self, self._aspects, self._buildings, self._defaultLocation, self._forVideoConference, self._roomID)
            html = page.display()
            self._cache.set(params, html, 300)
        return html

# 2. List of ...

class RHRoomBookingRoomList( RHRoomBookingBase ):

    def _checkParams( self, params ):

        self._roomLocation = None
        if params.get("roomLocation") and len( params["roomLocation"].strip() ) > 0:
            self._roomLocation = params["roomLocation"].strip()

        self._freeSearch = None
        if params.get("freeSearch") and len( params["freeSearch"].strip() ) > 0:
            s = params["freeSearch"].strip()
            # Remove commas
            self._freeSearch = ""
            for c in s:
                if c != ',': self._freeSearch += c

        self._capacity = None
        if params.get("capacity") and len( params["capacity"].strip() ) > 0:
            self._capacity = int( params["capacity"].strip() )

        self._availability = "Don't care"
        if params.get("availability") and len( params["availability"].strip() ) > 0:
            self._availability = params["availability"].strip()

        if self._availability != "Don't care":
            self._checkParamsRepeatingPeriod( params )

        self._includePrebookings = False
        if params.get( 'includePrebookings' ) == "on": self._includePrebookings = True

        self._includePendingBlockings = False
        if params.get( 'includePendingBlockings' ) == "on": self._includePendingBlockings = True

        # The end of "avail/don't care"

        # Equipment
        self._equipment = []
        for k, v in params.iteritems():
            if k[0:4] == "equ_" and v == "on":
                self._equipment.append( k[4:100] )

        # Special
        self._isReservable = self._ownedBy = self._isAutoConfirmed = None
        self._isActive = True

        if params.get( 'isReservable' ) == "on": self._isReservable = True
        if params.get( 'isAutoConfirmed' ) == "on": self._isAutoConfirmed = True

        # only admins can choose to consult non-active rooms
        if self._getUser() and self._getUser().isRBAdmin() and params.get( 'isActive', None ) != "on":
            self._isActive = None

        self._onlyMy = params.get( 'onlyMy' ) == "on"

    def _businessLogic( self ):
        if self._onlyMy: # Can't be done in checkParams since it must be after checkProtection
            self._title = "My rooms"
            self._ownedBy = self._getUser()

        r = RoomBase()
        r.capacity = self._capacity
        r.isActive = self._isActive
        #r.responsibleId = self._responsibleId
        r.isReservable = self._isReservable
        if self._isAutoConfirmed:
            r.resvsNeedConfirmation = False
        for eq in self._equipment:
            r.insertEquipment( eq )

        if self._availability == "Don't care":
            rooms = CrossLocationQueries.getRooms( location = self._roomLocation, freeText = self._freeSearch, ownedBy = self._ownedBy, roomExample = r, pendingBlockings = self._includePendingBlockings )
            # Special care for capacity (20% => greater than)
            if len ( rooms ) == 0:
                rooms = CrossLocationQueries.getRooms( location = self._roomLocation, freeText = self._freeSearch, ownedBy = self._ownedBy, roomExample = r, minCapacity = True, pendingBlockings = self._includePendingBlockings )
        else:
            # Period specification
            p = ReservationBase()
            p.startDT = self._startDT
            p.endDT = self._endDT
            p.repeatability = self._repeatability
            if self._includePrebookings:
                p.isConfirmed = None   # because it defaults to True

            # Set default values for later booking form
            self._websession.setVar( "defaultStartDT", p.startDT )
            self._websession.setVar( "defaultEndDT", p.endDT )
            self._websession.setVar( "defaultRepeatability", p.repeatability )

            available = ( self._availability == "Available" )

            rooms = CrossLocationQueries.getRooms( \
                location = self._roomLocation,
                freeText = self._freeSearch,
                ownedBy = self._ownedBy,
                roomExample = r,
                resvExample = p,
                available = available,
                pendingBlockings = self._includePendingBlockings )
            # Special care for capacity (20% => greater than)
            if len ( rooms ) == 0:
                rooms = CrossLocationQueries.getRooms( \
                    location = self._roomLocation,
                    freeText = self._freeSearch,
                    ownedBy = self._ownedBy,
                    roomExample = r,
                    resvExample = p,
                    available = available,
                    minCapacity = True,
                    pendingBlockings = self._includePendingBlockings )

        rooms.sort()

        self._rooms = rooms

        self._mapAvailable = Location.getDefaultLocation() and Location.getDefaultLocation().isMapAvailable()

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingRoomList( self, self._onlyMy )
        return p.display()

class RHRoomBookingBookingList( RHRoomBookingBase ):

    def _checkParams( self, params ):
        self._roomGUIDs = []
        self._allRooms = False
        roomGUIDs = params.get( "roomGUID" )
        if isinstance( roomGUIDs, list ) and 'allRooms' in roomGUIDs:
            roomGUIDs = 'allRooms'
        if isinstance( roomGUIDs, str ):
            if roomGUIDs == "allRooms":
                self._allRooms = True
                roomGUIDs = [ str(room.guid) for room in CrossLocationQueries.getRooms( allFast = True )]
            else:
                roomGUIDs = [roomGUIDs.strip()]
        if isinstance( roomGUIDs, list )  and  roomGUIDs != ['']:
            self._roomGUIDs = roomGUIDs

        resvEx = ReservationBase()
        self._checkParamsRepeatingPeriod( params )
        resvEx.startDT = self._startDT
        resvEx.endDT = self._endDT
        bookedForName = params.get( "bookedForName" )
        if bookedForName and len( bookedForName.strip() ) > 0:
            resvEx.bookedForName = bookedForName.strip()
        reason = params.get( "reason" )
        if reason and len( reason.strip() ) > 0:
            resvEx.reason = reason.strip()
        self._title = "Bookings"

        onlyPrebookings = params.get( "onlyPrebookings" )
        self._onlyPrebookings = False

        onlyBookings = params.get( "onlyBookings" )
        self._onlyBookings = False

        if onlyPrebookings and len( onlyPrebookings.strip() ) > 0:
            if onlyPrebookings == 'on':
                resvEx.isConfirmed = False
                self._title = "PRE-" + self._title
                self._onlyPrebookings = True
        elif onlyBookings and len( onlyBookings.strip() ) > 0:
            if onlyBookings == 'on':
                resvEx.isConfirmed = True
                self._onlyBookings = True
        else:
            # find pre-bookings as well
            resvEx.isConfirmed = None

        self._onlyMy = False
        onlyMy = params.get( "onlyMy" )
        if onlyMy and len( onlyMy.strip() ) > 0:
            if onlyMy == 'on':
                self._onlyMy = True
                self._title = "My " + self._title
        else:
            resvEx.createdBy = None
        self._ofMyRooms = False
        ofMyRooms = params.get( "ofMyRooms" )
        if ofMyRooms and len( ofMyRooms.strip() ) > 0:
            if ofMyRooms == 'on':
                self._ofMyRooms = True
                self._title = self._title + " for your rooms"
        else:
            self._rooms = None

        self._search = False
        search = params.get( "search" )
        if search and len( search.strip() ) > 0:
            if search == 'on':
                self._search = True
                self._title = "Search " + self._title

        self._order = params.get( "order", "" )

        isArchival = params.get( "isArchival" )
        if isArchival and len( isArchival.strip() ) > 0:
            self._isArchival = True
        else:
            self._isArchival = None

        self._autoCriteria = False
        if params.get( "autoCriteria" ) == "True" or not resvEx.startDT:
            now = datetime.now()
            after = now + timedelta( 7 ) # 1 week later

            resvEx.startDT = datetime( now.year, now.month, now.day, 0, 0, 0 )
            resvEx.endDT = datetime( after.year, after.month, after.day, 23, 59, 00 )
            self._autoCriteria = True
            self._isArchival = None

        isRejected = params.get( "isRejected" )
        if isRejected and len( isRejected.strip() ) > 0:
            resvEx.isRejected = isRejected == 'on'
        else:
            resvEx.isRejected = False
        isCancelled = params.get( "isCancelled" )
        if isCancelled and len( isCancelled.strip() ) > 0:
            resvEx.isCancelled = isCancelled == 'on'
        else:
            resvEx.isCancelled = False


        needsAVCSupport = params.get( "needsAVCSupport" )
        if needsAVCSupport and len( needsAVCSupport.strip() ) > 0:
            resvEx.needsAVCSupport = needsAVCSupport == 'on'
        else:
            resvEx.needsAVCSupport = None

        usesAVC = params.get( "usesAVC" )
        if usesAVC and len( usesAVC.strip() ) > 0:
            resvEx.usesAVC = usesAVC == 'on'
        else:
            resvEx.usesAVC = None

        isHeavy = params.get( "isHeavy" )
        if isHeavy and len( isHeavy.strip() ) > 0:
            self._isHeavy = True
        else:
            self._isHeavy = None

        self._resvEx = resvEx

        session = self._websession
        self._prebookingsRejected = session.getVar( 'prebookingsRejected' )
        self._subtitle = session.getVar( 'title' )
        self._description = session.getVar( 'description' )
        session.setVar( 'title', None )
        session.setVar( 'description', None )
        session.setVar( 'prebookingsRejected', None )


    def _process( self ):
        # The following can't be done in checkParams since it must be after checkProtection
        if self._onlyMy:
            self._resvEx.createdBy = str( self._getUser().id )
        if self._ofMyRooms:
            self._rooms = self._getUser().getRooms()
            self._roomGUIDs = None

        # Whether to show [Reject ALL conflicting PRE-bookings] button
        self._showRejectAllButton = False
        if self._rooms and not self._resvEx.isConfirmed:
            self._showRejectAllButton = True

        if self._roomGUIDs:
            rooms = [ RoomGUID.parse( rg ).getRoom() for rg in self._roomGUIDs ]
            if self._rooms is list:
                self._rooms.extend( rooms )
            else:
                self._rooms = rooms

        # Init
        resvEx = self._resvEx

        days = None
        #self._overload stores type of overload 0 - no overload 1 - too long period selected 2 - too many bookings fetched
        self._overload = 0
        if resvEx.startDT and resvEx.endDT:
            if ( resvEx.endDT - resvEx.startDT ).days > 400:
                self._overload = 1
                self._resvs = []
            else:
                # Prepare 'days' so .getReservations will use days index
                if resvEx.repeatability == None:
                    resvEx.repeatability = RepeatabilityEnum.daily
                periods = resvEx.splitToPeriods(endDT = resvEx.endDT)
                days = [ period.startDT.date() for period in periods ]

        # We only use the cache if no options except a start/end date are sent and all rooms are included
        self._useCache = (self._allRooms and
            not self._onlyPrebookings and
            not self._onlyBookings and
            not self._onlyMy and
            not self._ofMyRooms and
            not self._search and
            not self._isArchival and
            not self._isHeavy and
            not self._resvEx.bookedForName and
            not self._resvEx.reason and
            not self._resvEx.createdBy and
            not self._resvEx.isRejected and
            not self._resvEx.isCancelled and
            not self._resvEx.needsAVCSupport and
            not self._resvEx.usesAVC and
            self._resvEx.isConfirmed is None)
        self._cache = None
        self._updateCache = False

        self._dayBars = {}
        if not self._overload:
            if self._useCache:
                self._cache = GenericCache('RoomBookingCalendar')
                self._dayBars = dict((day, bar) for day, bar in self._cache.get_multi(map(str, days)).iteritems() if bar)
                dayMap = dict(((str(day), day) for day in days))
                for day in self._dayBars.iterkeys():
                    days.remove(dayMap[day])
                self._updateCache = bool(len(days))

            self._resvs = []
            day = None # Ugly but...othery way to avoid it?
            for day in days:
                for loc in Location.allLocations:
                    self._resvs += CrossLocationQueries.getReservations( location = loc.friendlyName, resvExample = resvEx, rooms = self._rooms, archival = self._isArchival, heavy = self._isHeavy, days = [day] )
                if len(self._resvs) > 400:
                    self._overload = 2
                    break
            if day:
                self._resvEx.endDT = datetime( day.year, day.month, day.day, 23, 59, 00 )

        p = roomBooking_wp.WPRoomBookingBookingList( self )
        return p.display()


# 3. Details of ...

class RHRoomBookingRoomDetails( RHRoomBookingBase ):

    def _checkParams( self, params ):
        locator = locators.WebLocator()
        locator.setRoom( params )
        self._room = self._target = locator.getObject()

        session = self._websession
        self._afterActionSucceeded = session.getVar( "actionSucceeded" )
        self._afterDeletionFailed = session.getVar( "deletionFailed" )
        self._formMode = session.getVar( "formMode" )

        self._searchingStartDT = self._searchingEndDT = None
        if not params.get( 'calendarMonths' ):
            self._searchingStartDT = session.getVar( "defaultStartDT" )
            self._searchingEndDT = session.getVar( "defaultEndDT" )

        self._clearSessionState()

    def _businessLogic( self ):
        pass

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingRoomDetails( self )
        return p.display()

class RHRoomBookingRoomStats( RHRoomBookingBase ):

    def _checkParams( self, params ):
        locator = locators.WebLocator()
        locator.setRoom( params )
        self._period = params.get("period","pastmonth")
        self._room = self._target = locator.getObject()

    def _businessLogic( self ):
        self._kpiAverageOccupation = self._room.getMyAverageOccupation(self._period)
        self._kpiActiveRooms = RoomBase.getNumberOfActiveRooms()
        self._kpiReservableRooms = RoomBase.getNumberOfReservableRooms()
        self._kpiReservableCapacity, self._kpiReservableSurface = RoomBase.getTotalSurfaceAndCapacity()
        # Bookings
        st = ReservationBase.getRoomReservationStats(self._room)
        self._booking_stats = st
        self._totalBookings = st['liveValid'] + st['liveCancelled'] + st['liveRejected'] + st['archivalValid'] + st['archivalCancelled'] + st['archivalRejected']

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingRoomStats( self )
        return p.display()

class RHRoomBookingBookingDetails( RHRoomBookingBase ):

    def _checkParams( self, params ):

        locator = locators.WebLocator()
        locator.setRoomBooking( params )
        self._resv = self._target = locator.getObject()

        self._afterActionSucceeded = self._websession.getVar( "actionSucceeded" )
        self._title = self._websession.getVar( "title" )
        self._description = self._websession.getVar( "description" )
        self._afterDeletionFailed = self._websession.getVar( "deletionFailed" )

        self._clearSessionState()

    def _businessLogic( self ):
        pass

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingBookingDetails( self )
        return p.display()

# 4. New

class RHRoomBookingBookingForm( RHRoomBookingBase ):

    def _checkParams( self, params ):
        session = self._websession  # Just an alias
        self._thereAreConflicts = session.getVar( 'thereAreConflicts' )
        self._skipConflicting = False

        # DATA FROM?
        self._dataFrom = CandidateDataFrom.DEFAULTS
        if params.get( "candDataInParams" ) or params.get( "afterCalPreview" ):
            self._dataFrom = CandidateDataFrom.PARAMS
        if session.getVar( "candDataInSession" ):
            self._dataFrom = CandidateDataFrom.SESSION

        # Reservation ID?
        resvID = None
        if self._dataFrom == CandidateDataFrom.SESSION:
            resvID = session.getVar( "resvID" )
            roomLocation = session.getVar( "roomLocation" )
        else:
            resvID = params.get( "resvID" )
            if isinstance( resvID, list ): resvID = resvID[0]
            roomLocation = params.get( "roomLocation" )
            if isinstance( roomLocation, list ): roomLocation = roomLocation[0]
        if resvID == "None": resvID = None
        if resvID: resvID = int( resvID )

        # FORM MODE?
        if resvID:
            self._formMode = FormMode.MODIF
        else:
            self._formMode = FormMode.NEW

        # SHOW ERRORS?
        self._showErrors = self._websession.getVar( "showErrors" )
        if self._showErrors:
            self._errors = self._websession.getVar( "errors" )

        # CREATE CANDIDATE OBJECT
        candResv = None

        if self._formMode == FormMode.NEW:
            if self._dataFrom == CandidateDataFrom.SESSION:
                candResv = self._loadResvCandidateFromSession( None, params )
            elif self._dataFrom == CandidateDataFrom.PARAMS:
                candResv = self._loadResvCandidateFromParams( None, params )
            else:
                candResv = self._loadResvCandidateFromDefaults( params )

        if self._formMode == FormMode.MODIF:
            import copy
            candResv = copy.copy(CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation ))
            if self._dataFrom == CandidateDataFrom.PARAMS:
                self._loadResvCandidateFromParams( candResv, params )
            if self._dataFrom == CandidateDataFrom.SESSION:
                self._loadResvCandidateFromSession( candResv, params )

        self._errors = session.getVar( "errors" )

        self._candResv = candResv

        self._clearSessionState()
        self._requireRealUsers = getRoomBookingOption('bookingsForRealUsers')


    def _checkProtection( self ):

        RHRoomBookingBase._checkProtection(self)

        # only do the remaining checks the rest if the basic ones were successful
        # (i.e. user is logged in)
        if self._doProcess:
            if not self._candResv.room.isActive and not self._getUser().isRBAdmin():
                raise FormValuesError( "You are not authorized to book this room." )

            if not self._candResv.room.canBook( self._getUser() ) and not self._candResv.room.canPrebook( self._getUser() ):
                raise FormValuesError( "You are not authorized to book this room." )

            if self._formMode == FormMode.MODIF:
                if not self._candResv.canModify( self.getAW() ):
                    raise MaKaCError( "You are not authorized to take this action." )

    def _businessLogic( self ):
        pass

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingBookingForm( self )
        return p.display()

class RHRoomBookingCloneBooking( RHRoomBookingBase ):
    """
    Performs open a new booking form with the data of an already existing booking.
    """

    def _checkParams( self, params ):
        session = self._websession  # Just an alias

        # DATA FROM
        session.setVar( "candDataInSession", True )

        self._formMode = FormMode.NEW

        # Reservation ID
        resvID = int(params.get( "resvID" ))

        # CREATE CANDIDATE OBJECT
        candResv = CrossLocationQueries.getReservations( resvID = resvID)
        if type(candResv) == list:
            candResv=candResv[0]
        self._saveResvCandidateToSession(candResv)
        self._room = candResv.room


    def _process( self ):
        self._redirect(urlHandlers.UHRoomBookingBookingForm.getURL(self._room))


class RHRoomBookingSaveBooking( RHRoomBookingBase ):
    """
    Performs physical INSERT or UPDATE.
    When succeeded redirects to booking details, otherwise returns to booking
    form.
    """

    def _checkParams( self, params ):

        self._roomLocation = params.get("roomLocation")
        self._roomID       = params.get("roomID")
        self._resvID             = params.get( "resvID" )
        if self._resvID == 'None':
            self._resvID = None

        # if the user is not logged in it will be redirected
        # to the login page by the _checkProtection, so we don't
        # need to store info in the session or process the other params
        if not self._getUser():
            return

        self._answer = params.get( "answer", None )

        self._skipConflicting = False

        # forceAddition is set by the confirmation dialog, so that
        # prebookings that conflict with other prebookings are
        # silently added

        self._forceAddition = params.get("forceAddition","False")
        if self._forceAddition == 'True':
            self._forceAddition = True
        else:
            self._forceAddition = False

        candResv = None
        if self._resvID:
            self._formMode = FormMode.MODIF
            self._resvID = int( self._resvID )
            _candResv = CrossLocationQueries.getReservations( resvID = self._resvID, location = self._roomLocation )
            self._orig_candResv = _candResv

            # Creates a "snapshot" of the reservation's attributes before modification
            self._resvAttrsBefore = self._orig_candResv.createSnapshot()

            import copy
            candResv = copy.copy(_candResv)

            if self._forceAddition:
                # booking data comes from session if confirmation was required
                self._loadResvCandidateFromSession( candResv, params )
            else:
                self._loadResvCandidateFromParams( candResv, params )

            # Creates a "snapshot" of the reservation's attributes after modification
            self._resvAttrsAfter = candResv.createSnapshot()

        else:
            self._formMode = FormMode.NEW
            candResv = Location.parse( self._roomLocation ).factory.newReservation()
            candResv.createdDT = datetime.now()
            candResv.createdBy = str( self._getUser().id )
            candResv.isRejected = False
            candResv.isCancelled = False

            if self._forceAddition:
                # booking data comes from session if confirmation was required
                self._loadResvCandidateFromSession( candResv, params )
            else:
                self._loadResvCandidateFromParams( candResv, params )

            self._resvID = None


        self._candResv = candResv

        for nbd in self._candResv.room.getNonBookableDates():
            if (doesPeriodsOverlap(nbd.getStartDate(),nbd.getEndDate(),self._candResv.startDT,self._candResv.endDT)):
                raise FormValuesError("You cannot book this room during the following periods due to maintenance reasons: %s"%("; ".join(map(lambda x: "from %s to %s"%(x.getStartDate().strftime("%d/%m/%Y"),x.getEndDate().strftime("%d/%m/%Y")), self._candResv.room.getNonBookableDates()))))

        self._params = params
        self._clearSessionState()


    def _checkProtection( self ):
        # If the user is not logged in, we redirect the same reservation page
        if not self._getUser():
            self._redirect(urlHandlers.UHSignIn.getURL(
                                    returnURL = urlHandlers.UHRoomBookingBookingForm.getURL(
                                            roomID = self._roomID,
                                            resvID = self._resvID,
                                            roomLocation = self._roomLocation )))
            self._doProcess = False
        else:
            RHRoomBookingBase._checkProtection(self)
            if not self._candResv.room.isActive and not self._getUser().isRBAdmin():
                raise MaKaCError( "You are not authorized to book this room." )

            if self._formMode == FormMode.MODIF:
                if not self._candResv.canModify( self.getAW() ):
                    raise MaKaCError( "You are not authorized to take this action." )

    def _businessLogic( self ):

        candResv = self._candResv
        emailsToBeSent = []
        self._confirmAdditionFirst = False;

        # Set confirmation status
        candResv.isConfirmed = True
        user = self._getUser()
        if not candResv.room.canBook( user ):
            candResv.isConfirmed = False


        errors = self._getErrorsOfResvCandidate( candResv )
        session = self._websession

        if not errors and self._answer != 'No':

            isConfirmed = candResv.isConfirmed
            candResv.isConfirmed = None
            # find pre-booking collisions
            self._collisions = candResv.getCollisions(sansID=candResv.id)
            candResv.isConfirmed = isConfirmed

            if not self._forceAddition and self._collisions:
                # save the reservation to the session
                self._saveResvCandidateToSession( candResv )
                # ask for confirmation about the pre-booking
                self._confirmAdditionFirst = True


            # approved pre-booking or booking
            if not self._confirmAdditionFirst:

                # Form is OK and (no conflicts or skip conflicts)
                if self._formMode == FormMode.NEW:
                    candResv.insert()
                    emailsToBeSent += candResv.notifyAboutNewReservation()
                    if candResv.isConfirmed:
                        session.setVar( "title", 'You have successfully made a booking.' )
                        session.setVar( "description", 'NOTE: Your booking is complete. However, be <b>aware</b> that in special cases the person responsible for a room may reject your booking. In that case you would be instantly notified by e-mail.' )
                    else:
                        session.setVar( "title", 'You have successfully made a <span style="color: Red;">PRE</span>-booking.' )
                        session.setVar( "description", 'NOTE: PRE-bookings are subject to acceptance or rejection. Expect an e-mail with acceptance/rejection information.' )
                elif self._formMode == FormMode.MODIF:
                    self._orig_candResv.unindexDayReservations()
                    self._orig_candResv.clearCalendarCache()
                    if self._forceAddition:
                        self._loadResvCandidateFromSession( self._orig_candResv, self._params )
                    else:
                        self._loadResvCandidateFromParams( self._orig_candResv, self._params )
                    self._orig_candResv.update()
                    self._orig_candResv.indexDayReservations()
                    emailsToBeSent += self._orig_candResv.notifyAboutUpdate()

                    # Add entry to the log
                    info = []
                    self._orig_candResv.getResvHistory().getResvModifInfo(info, self._resvAttrsBefore , self._resvAttrsAfter)

                    # If no modification was observed ("Save" was pressed but no field
                    # was changed) no entry is added to the log
                    if len(info) > 1 :
                        histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
                        self._orig_candResv.getResvHistory().addHistoryEntry(histEntry)

                    session.setVar( "title", 'Booking updated.' )
                    session.setVar( "description", 'Please review details below.' )

                session.setVar( "actionSucceeded", True )

                # Booking - reject all colliding PRE-Bookings
                if candResv.isConfirmed and self._collisions:
                    rejectionReason = "Conflict with booking: %s" % urlHandlers.UHRoomBookingBookingDetails.getURL(candResv)
                    for coll in self._collisions:
                        collResv = coll.withReservation
                        if collResv.repeatability is None: # not repeatable -> reject whole booking. easy :)
                            collResv.rejectionReason = rejectionReason
                            collResv.reject()    # Just sets isRejected = True
                            collResv.update()
                            emails = collResv.notifyAboutRejection()
                            emailsToBeSent += emails

                            # Add entry to the booking history
                            info = []
                            info.append("Booking rejected")
                            info.append("Reason: '%s'" % collResv.rejectionReason)
                            histEntry = ResvHistoryEntry(self._getUser(), info, emails)
                            collResv.getResvHistory().addHistoryEntry(histEntry)
                        else: # repeatable -> only reject the specific days
                            rejectDate = coll.startDT.date()
                            collResv.excludeDay(rejectDate, unindex=True)
                            collResv.update()
                            emails = collResv.notifyAboutRejection(date=rejectDate, reason=rejectionReason)
                            emailsToBeSent += emails

                            # Add entry to the booking history
                            info = []
                            info.append("Booking occurence of the %s rejected" % rejectDate.strftime("%d %b %Y"))
                            info.append("Reason: '%s'" % rejectionReason)
                            histEntry = ResvHistoryEntry(self._getUser(), info, emails)
                            collResv.getResvHistory().addHistoryEntry(histEntry)

        else:
            session.setVar( "candDataInSession", True )
            session.setVar( "errors", errors )

            if self._answer == 'No':
                session.setVar( "actionSucceeded", True )
            else:
                session.setVar( "actionSucceeded", False )
                session.setVar( "showErrors", True )
                session.setVar( "thereAreConflicts", self._thereAreConflicts )

            self._saveResvCandidateToSession( candResv )

        # Form is not properly filled OR there are conflicts
        self._errors = errors

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

    def _process( self ):

        self._businessLogic()

        if self._errors or self._answer == 'No':
            url = urlHandlers.UHRoomBookingBookingForm.getURL( self._candResv.room, resvID=self._resvID )
        elif self._confirmAdditionFirst:
            p = roomBooking_wp.WPRoomBookingConfirmBooking( self )
            return p.display()
        else:
            url = urlHandlers.UHRoomBookingBookingDetails.getURL( self._candResv )

        self._redirect( url )


class RHRoomBookingRoomForm( RHRoomBookingAdminBase ):
    """
    Form for creating NEW and MODIFICATION of an existing room.
    """

    def _checkParams( self, params ):
        session = self._websession  # Just an alias

        # DATA FROM?
        self._dataFrom = CandidateDataFrom.DEFAULTS
        if params.get( "candDataInParams" ):
            self._dataFrom = CandidateDataFrom.PARAMS
        if session.getVar( "candDataInSession" ):
            self._dataFrom = CandidateDataFrom.SESSION

        # Room ID?
        roomID = None
        roomLocation = None
        if self._dataFrom == CandidateDataFrom.SESSION:
            roomID = session.getVar( "roomID" )
            roomLocation = session.getVar( "roomLocation" )
        else:
            roomID = params.get( "roomID" )
            roomLocation = params.get( "roomLocation" )
        if roomID: roomID = int( roomID )

        # FORM MODE?
        if roomID:
            self._formMode = FormMode.MODIF
        else:
            self._formMode = FormMode.NEW

        # SHOW ERRORS?
        self._showErrors = self._websession.getVar( "showErrors" )
        if self._showErrors:
            self._errors = self._websession.getVar( "errors" )

        # CREATE CANDIDATE OBJECT
        candRoom = None

        if self._formMode == FormMode.NEW:
            locationName = params.get("roomLocation", "")
            location = Location.parse(locationName)
            if str(location) == "None":
                # Room should be inserted into default backend => using Factory
                candRoom = Factory.newRoom()
            else:
                candRoom = location.newRoom()
            if self._dataFrom == CandidateDataFrom.SESSION:
                self._loadRoomCandidateFromSession( candRoom )
            else:
                self._loadRoomCandidateFromDefaults( candRoom )

        if self._formMode == FormMode.MODIF:
            candRoom = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )

            if self._dataFrom == CandidateDataFrom.PARAMS:
                self._loadRoomCandidateFromParams( candRoom, params )
            if self._dataFrom == CandidateDataFrom.SESSION:
                self._loadRoomCandidateFromSession( candRoom )

        self._errors = session.getVar( "errors" )

        # After searching for responsible
        if params.get( 'selectedPrincipals' ):
            candRoom.responsibleId = params['selectedPrincipals']

        self._candRoom = self._target = candRoom
        self._clearSessionState()

    def _process( self ):
        p = admins.WPRoomBookingRoomForm( self )
        return p.display()

class RHRoomBookingSaveRoom( RHRoomBookingAdminBase ):
    """
    Performs physical INSERT or UPDATE.
    When succeeded redirects to room details, otherwise returns to room form.
    """

    def _uploadPhotos( self, candRoom, params ):
        if (params.get( "largePhotoPath" ) and params.get( "smallPhotoPath" )
            and params["largePhotoPath"].filename and params["smallPhotoPath"].filename):
            candRoom.savePhoto( params["largePhotoPath"] )
            candRoom.saveSmallPhoto( params["smallPhotoPath"] )

    def _checkParams( self, params ):
        roomID = params.get( "roomID" )
        roomLocation = params.get( "roomLocation" )

        candRoom = None
        if roomID:
            self._formMode = FormMode.MODIF
            if roomID: roomID = int( roomID )
            candRoom = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )
        else:
            self._formMode = FormMode.NEW
            if roomLocation:
                name = Location.parse(roomLocation).friendlyName
            else:
                name = Location.getDefaultLocation().friendlyName
            location = Location.parse(name)
            candRoom = location.newRoom()
            candRoom.locationName = name

        self._loadRoomCandidateFromParams( candRoom, params )
        self._candRoom = self._target = candRoom
        self._params = params

    def _process( self ):
        candRoom = self._candRoom
        params = self._params

        errors = self._getErrorsOfRoomCandidate( candRoom )
        if not errors:
            # Succeeded
            if self._formMode == FormMode.MODIF:
                candRoom.update()
                # if responsibleId changed
                candRoom.notifyAboutResponsibility()
                url = urlHandlers.UHRoomBookingRoomDetails.getURL(candRoom)

            elif self._formMode == FormMode.NEW:
                candRoom.insert()
                candRoom.notifyAboutResponsibility()
                url = urlHandlers.UHRoomBookingAdminLocation.getURL(Location.parse(candRoom.locationName), actionSucceeded = True)

            self._uploadPhotos( candRoom, params )
            self._websession.setVar( "actionSucceeded", True )
            self._websession.setVar( "formMode", self._formMode )
            self._redirect( url ) # Redirect to room DETAILS
        else:
            # Failed
            self._websession.setVar( "actionSucceeded", False )
            self._websession.setVar( "candDataInSession", True )
            self._websession.setVar( "errors", errors )
            self._websession.setVar( "showErrors", True )

            self._saveRoomCandidateToSession( candRoom )
            url = urlHandlers.UHRoomBookingRoomForm.getURL( None )
            self._redirect( url ) # Redirect again to FORM


class RHRoomBookingDeleteRoom( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        roomID = params.get( "roomID" )
        roomID = int( roomID )
        roomLocation = params.get( "roomLocation" )
        self._room = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )
        self._target = self._room

    def _process( self ):
        room = self._room
        # Check whether deletion is possible
        liveResv = room.getLiveReservations()
        if len( liveResv ) == 0:
            # Possible - delete
            for resv in room.getReservations():
                resv.remove()
            room.remove()
            self._websession.setVar( 'title', "Room has been deleted." )
            self._websession.setVar( 'description', "You have successfully deleted the room. All its archival, cancelled and rejected bookings have also been deleted." )
            url = urlHandlers.UHRoomBookingStatement.getURL()
            self._redirect( url ) # Redirect to deletion confirmation
        else:
            # Impossible
            self._websession.setVar( 'deletionFailed', True )
            url = urlHandlers.UHRoomBookingRoomDetails.getURL( room )
            self._redirect( url ) # Redirect to room DETAILS

class RHRoomBookingDeleteBooking( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        resvID = int( params.get( "resvID" ) )
        roomLocation = params.get( "roomLocation" )
        self._resv = CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation )
        self._target = self._resv

    def _process( self ):
        # Booking deletion is always possible - just delete
        self._resv.remove()
        self._websession.setVar( 'title', "Booking has been deleted." )
        self._websession.setVar( 'description', "You have successfully deleted the booking." )
        url = urlHandlers.UHRoomBookingStatement.getURL()
        self._redirect( url ) # Redirect to deletion confirmation

class RHRoomBookingCancelBooking( RHRoomBookingBase ):

    def _checkParams( self , params ):
        resvID = int( params.get( "resvID" ) )
        roomLocation = params.get( "roomLocation" )
        self._resv = CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation )
        self._target = self._resv

    def _checkProtection( self ):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only owner (the one who created) and admin can CANCEL
        # (Responsible can not cancel a booking!)
        if ( not self._resv.isOwnedBy( user ) ) and \
            ( not self._getUser().isRBAdmin() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        # Booking deletion is always possible - just delete
        self._resv.cancel()    # Just sets isCancel = True
        self._resv.update()
        emailsToBeSent = self._resv.notifyAboutCancellation()

        # Add entry to the booking history
        info = []
        info.append("Booking cancelled")
        histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
        self._resv.getResvHistory().addHistoryEntry(histEntry)

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

        self._websession.setVar( 'actionSucceeded', True )
        self._websession.setVar( 'title', "Booking has been cancelled." )
        self._websession.setVar( 'description', "You have successfully cancelled the booking." )
        url = urlHandlers.UHRoomBookingBookingDetails.getURL( self._resv )
        self._redirect( url ) # Redirect to booking details


class RHRoomBookingCancelBookingOccurrence( RHRoomBookingBase ):

    def _checkParams( self , params ):
        resvID = int( params.get( "resvID" ) )
        roomLocation = params.get( "roomLocation" )
        date = params.get( "date" )

        self._resv = CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation )
        self._date = parse_date( date )
        self._target = self._resv

    def _checkProtection( self ):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only user/admin can cancell a booking occurrence
        # (Owner can not reject his own booking, he should cancel instead)
        if self._resv.createdBy != user.getId() and (not user.isRBAdmin()):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        self._resv.excludeDay( self._date, unindex=True )
        self._resv.update()
        emailsToBeSent = self._resv.notifyAboutCancellation( date = self._date )

        # Add entry to the booking history
        info = []
        info.append("Booking occurence of the %s cancelled" %self._date.strftime("%d %b %Y"))
        histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
        self._resv.getResvHistory().addHistoryEntry(histEntry)

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

        self._websession.setVar( 'actionSucceeded', True )
        self._websession.setVar( 'title', "Selected occurrence has been cancelled." )
        self._websession.setVar( 'description', "You have successfully cancelled an occurrence of this booking." )
        url = urlHandlers.UHRoomBookingBookingDetails.getURL( self._resv )
        self._redirect( url ) # Redirect to booking details


class RHRoomBookingRejectBooking( RHRoomBookingBase ):

    def _checkParams( self , params ):
        resvID = int( params.get( "resvID" ) )
        roomLocation = params.get( "roomLocation" )
        reason = params.get( "reason" )

        self._resv = CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation )
        self._resv.rejectionReason = reason
        self._target = self._resv

    def _checkProtection( self ):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only responsible and admin can REJECT
        # (Owner can not reject his own booking, he should cancel instead)
        if ( not self._resv.room.isOwnedBy( user ) ) and \
            ( not self._getUser().isRBAdmin() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        self._resv.reject()    # Just sets isRejected = True
        self._resv.update()
        emailsToBeSent = self._resv.notifyAboutRejection()

        # Add entry to the booking history
        info = []
        info.append("Booking rejected")
        info.append("Reason : '%s'" %self._resv.rejectionReason)
        histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
        self._resv.getResvHistory().addHistoryEntry(histEntry)

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

        self._websession.setVar( 'actionSucceeded', True )
        self._websession.setVar( 'title', "Booking has been rejected." )
        self._websession.setVar( 'description', "NOTE: rejection e-mail has been sent to the user. However, it's advisable to <strong>inform</strong> the user directly. Note that users often don't read e-mails." )
        url = urlHandlers.UHRoomBookingBookingDetails.getURL( self._resv )
        self._redirect( url ) # Redirect to booking details


class RHRoomBookingRejectALlConflicting( RHRoomBookingBase ):

#    def _checkParams( self , params ):
#        pass

    def _checkProtection( self ):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only responsible and admin can REJECT
        # (Owner can not reject his own booking, he should cancel instead)
        if ( not user.getRooms() ) and \
            ( not self._getUser().isRBAdmin() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        userRooms = self._getUser().getRooms()
        emailsToBeSent = []

        resvEx = ReservationBase()
        resvEx.isConfirmed = False
        resvEx.isRejected = False
        resvEx.isCancelled = False

        resvs = CrossLocationQueries.getReservations( resvExample = resvEx, rooms = userRooms )

        counter = 0
        for resv in resvs:
            # There's a big difference between 'isConfirmed' being None and False. This value needs to be
            # changed to None and after the search reverted to the previous value. For further information,
            # please take a look at the comment in rb_reservation.py::ReservationBase.getCollisions method
            tmpConfirmed = resv.isConfirmed
            resv.isConfirmed = None
            if resv.getCollisions( sansID = resv.id, boolResult = True ):
                resv.rejectionReason = "Your PRE-booking conflicted with exiting booking. (Please note it IS possible even if you were the first one to PRE-book the room)."
                resv.reject()    # Just sets isRejected = True
                resv.update()
                emailsToBeSent += resv.notifyAboutRejection()
                counter += 1
                # Add entry to the history of the rejected reservation
                info = []
                info.append("Booking rejected due to conflict with existing booking")
                histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
                resv.getResvHistory().addHistoryEntry(histEntry)
            resv.isConfirmed = tmpConfirmed
        self._websession.setVar( 'prebookingsRejected', True )
        if counter > 0:
            self._websession.setVar( 'title', str( counter ) + " conflicting PRE-bookings have been rejected." )
            self._websession.setVar( 'description', "Rejection e-mails have been sent to the users, with explanation that their PRE-bookings conflicted with the present confirmed bookings." )
        else:
            self._websession.setVar( 'title', "There are no conflicting PRE-bookings for your rooms." )
            self._websession.setVar( 'description', "" )
        for notification in emailsToBeSent:
            GenericMailer.send(notification)
        url = urlHandlers.UHRoomBookingBookingList.getURL( ofMyRooms = True, onlyPrebookings = True, autoCriteria = True )
        self._redirect( url ) # Redirect to booking details

class RHRoomBookingAcceptBooking( RHRoomBookingBase ):

    def _checkParams( self , params ):
        resvID = int( params.get( "resvID" ) )
        roomLocation = params.get( "roomLocation" )
        self._resv = CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation )
        self._target = self._resv

    def _checkProtection( self ):
        RHRoomBookingBase._checkProtection(self)

        # only do the remaining checks the rest if the basic ones were successful
        # (i.e. user is logged in)
        if self._doProcess:
            user = self._getUser()
            # Only responsible and admin can ACCEPT
            if ( not self._resv.room.isOwnedBy( user ) ) and \
                ( not self._getUser().isRBAdmin() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        emailsToBeSent = []
        session = self._websession
        if len( self._resv.getCollisions( sansID = self._resv.id ) ) == 0:
            # No conflicts
            self._resv.isConfirmed = True
            self._resv.update()
            emailsToBeSent += self._resv.notifyAboutConfirmation()

            # Add entry to the booking history
            info = []
            info.append("Booking accepted")
            histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
            self._resv.getResvHistory().addHistoryEntry(histEntry)

            session.setVar( 'actionSucceeded', True )
            session.setVar( 'title', "Booking has been accepted." )
            session.setVar( 'description', "NOTE: confirmation e-mail has been sent to the user." )
            url = urlHandlers.UHRoomBookingBookingDetails.getURL( self._resv )
            self._redirect( url ) # Redirect to booking details
        else:
            errors = ["PRE-Booking conflicts with other (confirmed) bookings."]
            session.setVar( "actionSucceeded", False )
            session.setVar( "candDataInSession", True )
            session.setVar( "errors", errors )
            session.setVar( "showErrors", True )
            session.setVar( "thereAreConflicts", True )

            session.setVar( 'title', "PRE-Booking conflicts with other (confirmed) bookings." )
            session.setVar( 'description', "" )

            self._formMode = FormMode.MODIF
            self._saveResvCandidateToSession( self._resv )
            url = urlHandlers.UHRoomBookingBookingForm.getURL( self._resv.room )
            self._redirect( url ) # Redirect to booking details
        for notification in emailsToBeSent:
            GenericMailer.send(notification)

class RHRoomBookingStatement( RHRoomBookingBase ):

    def _checkParams( self , params ):
        session = self._websession
        self._title = session.getVar( 'title' )
        self._description = session.getVar( 'description' )
        session.setVar( 'title', None )
        session.setVar( 'description', None )

    def _process( self ):
        return roomBooking_wp.WPRoomBookingStatement( self ).display()

class RHRoomBookingAdmin( RHRoomBookingAdminBase ):

    def _process( self ):
        return admins.WPRoomBookingAdmin( self ).display()

class RHRoomBookingAdminLocation( RHRoomBookingAdminBase ):

    def _checkParams( self, params ):
        self._withKPI = False
        if params.get( 'withKPI' ) == 'True':
            self._withKPI = True
        name = params.get("locationId","")
        self._location = Location.parse(name)
        if str(self._location) == "None":
            raise MaKaCError( "%s: Unknown Location" % name )

        if params.get("actionSucceeded", None):
            self._actionSucceeded = True
        else:
            self._actionSucceeded = False

    def _process( self ):

        if self._withKPI:
            self._kpiAverageOccupation = RoomBase.getAverageOccupation(location=self._location.friendlyName)
            self._kpiTotalRooms = RoomBase.getNumberOfRooms(location=self._location.friendlyName)
            self._kpiActiveRooms = RoomBase.getNumberOfActiveRooms(location=self._location.friendlyName)
            self._kpiReservableRooms = RoomBase.getNumberOfReservableRooms(location=self._location.friendlyName)
            self._kpiReservableCapacity, self._kpiReservableSurface = RoomBase.getTotalSurfaceAndCapacity(location=self._location.friendlyName)

            # Bookings

            st = ReservationBase.getReservationStats(location=self._location.friendlyName)
            self._booking_stats = st
            self._totalBookings = st['liveValid'] + st['liveCancelled'] + st['liveRejected'] + st['archivalValid'] + st['archivalCancelled'] + st['archivalRejected']

        return admins.WPRoomBookingAdminLocation( self, self._location, actionSucceeded = self._actionSucceeded ).display()


class RHRoomBookingSetDefaultLocation( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        self._defaultLocation = params["defaultLocation"]

    def _process( self ):
        Location.setDefaultLocation( self._defaultLocation )
        url = urlHandlers.UHRoomBookingAdmin.getURL()
        self._redirect( url )

class RHRoomBookingSaveLocation( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        self._locationName = params["newLocationName"].strip()
        self._pluginClass = None
        name = params.get("pluginName","default")
        plugs = PluginLoader.getPluginsByType("RoomBooking")
        for plug in plugs:
            if pluginId(plug) == name:
                self._pluginClass = plug.roombooking.getRBClass()
        if self._pluginClass == None:
            raise MaKaCError( "%s: Cannot find requested plugin" % name )

    def _process( self ):
        if self._locationName:
            location = Location( self._locationName, self._pluginClass )
            Location.insertLocation( location )

        url = urlHandlers.UHRoomBookingAdmin.getURL()
        self._redirect( url )

class RHRoomBookingDeleteLocation( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        self._locationName = params["removeLocationName"]

    def _process( self ):

        if self._locationName:
            Location.removeLocation( self._locationName )
        url = urlHandlers.UHRoomBookingAdmin.getURL()
        self._redirect( url )

class RHRoomBookingSaveEquipment( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        self._eq = params["newEquipmentName"].strip()
        name = params.get("locationId","")
        self._location = Location.parse(name)
        if str(self._location) == "None":
            raise MaKaCError( "%s: Unknown Location" % name )

    def _process( self ):
        if self._eq:
            self._location.factory.getEquipmentManager().insertEquipment( self._eq, location=self._location.friendlyName )
        url = urlHandlers.UHRoomBookingAdminLocation.getURL(self._location)
        self._redirect( url )

class RHRoomBookingDeleteEquipment( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        self._eq = params["removeEquipmentName"]
        name = params.get("locationId","")
        self._location = Location.parse(name)
        if str(self._location) == "None":
            raise MaKaCError( "%s: Unknown Location" % name )

    def _process( self ):
        self._location.factory.getEquipmentManager().removeEquipment( self._eq, location=self._location.friendlyName )
        url = urlHandlers.UHRoomBookingAdminLocation.getURL(self._location)
        self._redirect( url )

class RHRoomBookingSaveCustomAttribute( RHRoomBookingAdminBase ): # + additional

    def _checkParams( self , params ):
        name = params.get("locationId","")
        self._location = Location.parse(name)
        if str(self._location) == "None":
            raise MaKaCError( "%s: Unknown Location" % name )

        self._newAttr = None
        if params.get( "newCustomAttributeName" ):
            attrName = params["newCustomAttributeName"].strip()
            if attrName:
                attrIsReq = False
                if params.get( "newCustomAttributeIsRequired" ) == "on":
                    attrIsReq = True
                attrIsHidden = False
                if params.get( "newCustomAttributeIsHidden" ) == "on":
                    attrIsHidden = True
                self._newAttr = { \
                    'name': attrName,
                    'type': 'str',
                    'required': attrIsReq,
                    'hidden': attrIsHidden }

        # Set "required" for _all_ custom attributes
        manager = self._location.factory.getCustomAttributesManager()
        for ca in manager.getAttributes(location=self._location.friendlyName):
            required = hidden = False
            # Try to find in params (found => required == True)
            for k in params.iterkeys():
                if k[0:10] == "cattr_req_":
                    attrName = k[10:100].strip()
                    if attrName == ca['name']:
                        required = True
                if k[0:10] == "cattr_hid_":
                    attrName = k[10:100].strip()
                    if attrName == ca['name']:
                        hidden = True
            manager.setRequired( ca['name'], required, location=self._location.friendlyName )
            manager.setHidden( ca['name'], hidden, location=self._location.friendlyName )

    def _process( self ):
        if self._newAttr:
            self._location.factory.getCustomAttributesManager().insertAttribute( self._newAttr, location=self._location.friendlyName )
        url = urlHandlers.UHRoomBookingAdminLocation.getURL(self._location)
        self._redirect( url )

class RHRoomBookingDeleteCustomAttribute( RHRoomBookingAdminBase ):  # + additional

    def _checkParams( self , params ):
        self._attr = params["removeCustomAttributeName"]
        name = params.get("locationId","")
        self._location = Location.parse(name)
        if str(self._location) == "None":
            raise MaKaCError( "%s: Unknown Location" % name )

    def _process( self ):
        self._location.factory.getCustomAttributesManager().removeAttribute( self._attr, location=self._location.friendlyName )
        url = urlHandlers.UHRoomBookingAdminLocation.getURL(self._location)
        self._redirect( url )

class RHRoomBookingSendRoomPhoto( RHRoomBookingBase ):

    def _checkParams( self, params ):
        self.fileName = params['photoId'] + ".jpg"
        self.small = params.get( 'small' ) == 'True' # Large by default

    def _process( self ):
        cfg = Config.getInstance()

        filePath = cfg.getRoomPhotosDir()
        if self.small:
            filePath = cfg.getRoomSmallPhotosDir()
        fullPath = os.path.join( filePath, self.fileName )

        self._req.content_type = "image/jpeg"
        #self._req.headers_out["Content-Disposition"] = "inline; filename=\"%s\"" % self.fileName
        self._req.sendfile( fullPath )


class RHRoomBookingGetRoomSelectList( RHRoomBookingBase ):

    def _checkParams( self, params ):
        self.location = params.get( 'locationName' )
        self.forSubEvents = params.get( 'forSubEvents' ) == 'True'

    def _process( self ):

        self._roomList = []
        if self.location:
            self._roomList = CrossLocationQueries.getRooms( location = self.location )
        self._locationRoom = ""

        from MaKaC.webinterface import wcomponents
        if self.forSubEvents:
            p = wcomponents.WRoomBookingRoomSelectList4SubEvents( self )
        else:
            p = wcomponents.WRoomBookingRoomSelectList( self )

        return p.getHTML( self.getRequestParams() )

        #return "<div style='background-color: red;'>&nbsp;&nbsp;&nbsp;&nbsp;</div>"

class RHRoomBookingRejectBookingOccurrence( RHRoomBookingBase ):

    def _checkParams( self , params ):
        resvID = int( params.get( "resvID" ) )
        roomLocation = params.get( "roomLocation" )
        reason = params.get( "reason" )
        date = params.get( "date" )

        self._resv = CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation )
        self._rejectionReason = reason
        self._date = parse_date( date )
        self._target = self._resv

    def _checkProtection( self ):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only responsible and admin can REJECT
        # (Owner can not reject his own booking, he should cancel instead)
        if ( not self._resv.room.isOwnedBy( user ) ) and \
            ( not self._getUser().isRBAdmin() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        self._resv.excludeDay( self._date, unindex=True )
        self._resv.update()
        emailsToBeSent = self._resv.notifyAboutRejection( date = self._date, reason = self._rejectionReason )

        # Add entry to the booking history
        info = []
        info.append("Booking occurence of the %s rejected" %self._date.strftime("%d %b %Y"))
        info.append("Reason : '%s'" %self._rejectionReason)
        histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
        self._resv.getResvHistory().addHistoryEntry(histEntry)

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

        self._websession.setVar( 'actionSucceeded', True )
        self._websession.setVar( 'title', "Selected occurrence of this booking has been rejected." )
        self._websession.setVar( 'description', "NOTE: rejection e-mail has been sent to the user. " )
        url = urlHandlers.UHRoomBookingBookingDetails.getURL( self._resv )
        self._redirect( url ) # Redirect to booking details


class RHRoomBookingBlockingsForMyRooms(RHRoomBookingBase):

    def _checkParams(self, params):
        self.filterState = params.get('filterState')

    def _process(self):
        activeState = -1
        if self.filterState == 'pending':
            activeState = None
        elif self.filterState == 'accepted':
            activeState = True
        elif self.filterState == 'rejected':
            activeState = False
        myRoomBlocks = defaultdict(list)
        for room in self._getUser().getRooms():
            roomBlocks = RoomBlockingBase.getByRoom(room, activeState)
            if roomBlocks:
                myRoomBlocks[str(room.guid)] += roomBlocks
        p = roomBooking_wp.WPRoomBookingBlockingsForMyRooms(self, myRoomBlocks)
        return p.display()

class RHRoomBookingBlockingDetails(RHRoomBookingBase):

    def _checkParams(self, params):
        blockId = int(params.get('blockingId'))
        self._block = RoomBlockingBase.getById(blockId)
        if not self._block:
            raise MaKaCError('A blocking with this ID does not exist.')

    def _process(self):
        p = roomBooking_wp.WPRoomBookingBlockingDetails(self, self._block)
        return p.display()

class RHRoomBookingBlockingList(RHRoomBookingBase):

    def _checkParams(self, params):
        self.onlyMine = 'onlyMine' in params
        self.onlyRecent = 'onlyRecent' in params
        self.onlyThisYear = 'onlyThisYear' in params

    def _process(self):
        if self.onlyMine:
            blocks = RoomBlockingBase.getByOwner(self._getUser())
            if self.onlyThisYear:
                firstDay = date(date.today().year, 1, 1)
                lastDay = date(date.today().year, 12, 31)
                blocks = [block for block in blocks if block.startDate <= lastDay and firstDay <= block.endDate]
        elif self.onlyThisYear:
            blocks = RoomBlockingBase.getByDateSpan(date(date.today().year, 1, 1), date(date.today().year, 12, 31))
            if self.onlyMine:
                blocks = [block for block in blocks if block.createdByUser == self._getUser()]
        else:
            blocks = RoomBlockingBase.getAll()

        if self.onlyRecent:
            blocks = [block for block in blocks if date.today() <= block.endDate]
        p = roomBooking_wp.WPRoomBookingBlockingList(self, blocks)
        return p.display()

class RHRoomBookingBlockingForm(RHRoomBookingBase):

    def _checkParams(self, params):

        self._action = params.get('action')
        blockId = params.get('blockingId')
        if blockId is not None:
            self._block = RoomBlockingBase.getById(int(blockId))
            if not self._block:
                raise MaKaCError('A blocking with this ID does not exist.')
        else:
            self._block = Factory.newRoomBlocking()()
            self._block.startDate = date.today()
            self._block.endDate = date.today()

        self._hasErrors = False
        if self._action == 'save':
            from MaKaC.services.interface.rpc import json
            self._reason = params.get('reason', '').strip()
            allowedUsers = json.decode(params.get('allowedUsers', '[]'))
            blockedRoomGuids = json.decode(params.get('blockedRooms', '[]'))
            startDate = params.get('startDate')
            endDate = params.get('endDate')
            if startDate and endDate:
                self._startDate = parseDate(startDate)
                self._endDate = parseDate(endDate)
            else:
                self._startDate = self._endDate = None

            self._blockedRooms = [RoomGUID.parse(guid).getRoom() for guid in blockedRoomGuids]
            self._allowedUsers = [RoomBlockingPrincipal.getByTypeId(fossil['_type'], fossil['id']) for fossil in allowedUsers]

            if not self._reason or not self._blockedRooms:
                self._hasErrors = True
            elif self._createNew and (not self._startDate or not self._endDate or self._startDate > self._endDate):
                self._hasErrors = True

    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)
        if not self._doProcess: # if we are not logged in
            return
        if not self._createNew:
            if not self._block.canModify(self._getUser()):
                raise MaKaCError("You are not authorized to modify this blocking.")
        else:
            if not (Room.isAvatarResponsibleForRooms(self._getUser()) or self._getUser().isAdmin() or self._getUser().isRBAdmin()):
                raise MaKaCError("Only users who own at least one room are allowed to create blockings.")

    def _process(self):
        if self._action == 'save' and not self._hasErrors:
            self._block.message = self._reason
            if self._createNew:
                self._block.createdByUser = self._getUser()
                self._block.startDate = self._startDate
                self._block.endDate = self._endDate
            currentBlockedRooms = set()
            for room in self._blockedRooms:
                br = self._block.getBlockedRoom(room)
                if not br:
                    br = BlockedRoom(room)
                    self._block.addBlockedRoom(br)
                    if room.getResponsible() == self._getUser():
                        br.approve(sendNotification=False)
                currentBlockedRooms.add(br)
            # Remove blocked rooms which have been removed from the list
            for br in set(self._block.blockedRooms) - currentBlockedRooms:
                self._block.delBlockedRoom(br)
            # Replace allowed-users/groups list
            self._block.allowed = self._allowedUsers
            # Insert/update(re-index) the blocking
            if self._createNew:
                self._block.insert()
            else:
                self._block.update()
            self._redirect(urlHandlers.UHRoomBookingBlockingsBlockingDetails.getURL(self._block))

        elif self._action == 'save' and self._createNew and self._hasErrors:
            # If we are creating a new blocking and there are errors, populate the block object anyway to preserve the entered values
            self._block.message = self._reason
            self._block.startDate = self._startDate
            self._block.endDate = self._endDate
            self._block.allowed = self._allowedUsers
            for room in self._blockedRooms:
                self._block.addBlockedRoom(BlockedRoom(room))

        p = roomBooking_wp.WPRoomBookingBlockingForm(self, self._block, self._hasErrors)
        return p.display()

    @property
    def _createNew(self):
        return self._block.id is None

class RHRoomBookingDelete(RHRoomBookingBase):

    def _checkParams(self, params):
        blockId = int(params.get('blockingId'))
        self._block = RoomBlockingBase.getById(blockId)

    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)
        if not self._block.canDelete(self._getUser()):
            raise MaKaCError("You are not authorized to delete this blocking.")

    def _process(self):
        self._block.remove()
        self._redirect(urlHandlers.UHRoomBookingBlockingList.getURL(onlyMine=True, onlyRecent=True))
