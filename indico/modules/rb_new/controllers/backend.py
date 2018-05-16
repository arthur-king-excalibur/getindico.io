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
from marshmallow_enum import EnumField
from webargs import fields
from webargs.flaskparser import use_args

from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import with_total_rows
from indico.modules.rb import Location
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.favorites import favorite_room_table
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.modules.rb.models.rooms import Room
from indico.modules.rb_new.schemas import aspects_schema, map_rooms_schema, reservation_occurrences_schema, rooms_schema
from indico.modules.rb_new.util import get_buildings, get_rooms_availability, search_for_rooms


search_room_args = {
    'capacity': fields.Int(),
    'text': fields.Str(),
    'start_dt': fields.DateTime(),
    'end_dt': fields.DateTime(),
    'repeat_frequency': EnumField(RepeatFrequency),
    'repeat_interval': fields.Int(missing=0),
    'building': fields.Str(),
    'floor': fields.Str(),
    'sw_lat': fields.Float(validate=lambda x: -90 <= x <= 90),
    'sw_lng': fields.Float(validate=lambda x: -180 <= x <= 180),
    'ne_lat': fields.Float(validate=lambda x: -90 <= x <= 90),
    'ne_lng': fields.Float(validate=lambda x: -180 <= x <= 180)
}


class RHSearchRooms(RHRoomBookingBase):
    @use_args(dict(search_room_args, **{
        'offset': fields.Int(missing=0, validate=lambda x: x >= 0),
        'limit': fields.Int(missing=10, validate=lambda x: x >= 0)
    }))
    def _process(self, args):
        filter_availability = args.get('start_dt') and args.get('end_dt')
        query = search_for_rooms(args, only_available=filter_availability)
        query = query.limit(args['limit']).offset(args['offset'])
        rooms, total = with_total_rows(query)
        return jsonify(total=total, rooms=rooms_schema.dump(rooms).data)


class RHSearchMapRooms(RHRoomBookingBase):
    @use_args(search_room_args)
    def _process(self, args):
        filter_availability = args.get('start_dt') and args.get('end_dt')
        query = search_for_rooms(args, only_available=filter_availability)
        return jsonify(map_rooms_schema.dump(query.all()).data)


class RHAspects(RHRoomBookingBase):
    def _process(self):
        to_cast = ['top_left_latitude', 'top_left_longitude', 'bottom_right_latitude', 'bottom_right_longitude']
        aspects = [
            {k: float(v) if k in to_cast else v for k, v in aspect.viewitems()}
            for aspect in aspects_schema.dump(Location.default_location.aspects).data
        ]
        return jsonify(aspects)


class RHBuildings(RHRoomBookingBase):
    def _process(self):
        return jsonify(get_buildings())


class RHTimeline(RHRoomBookingBase):
    @use_args({
        'room_ids': fields.List(fields.Int()),
        'start_dt': fields.DateTime(),
        'end_dt': fields.DateTime(),
        'repeat_frequency': EnumField(RepeatFrequency),
        'repeat_interval': fields.Int(missing=0),
        'flexibility': fields.Int(missing=0)
    })
    def _process(self, args):
        rooms = Room.query.filter(Room.is_active, Room.id.in_(args.pop('room_ids')))
        availabilities = get_rooms_availability(rooms, **args)
        for availability in availabilities:
            availability['room'] = rooms_schema.dump(availability['room'], many=False).data
            availability['occurrences'] = reservation_occurrences_schema.dump(availability['occurrences']).data
            availability['conflicts'] = reservation_occurrences_schema.dump(availability['conflicts']).data
            availability['pre_conflicts'] = reservation_occurrences_schema.dump(availability['pre_conflicts']).data
        return jsonify(availabilities)


class RHRoomFavorites(RHRoomBookingBase):
    def _process_args(self):
        self.room = None
        if 'room_id' in request.view_args:
            self.room = Room.get_one(request.view_args['room_id'])

    def _process_GET(self):
        query = (db.session.query(favorite_room_table.c.room_id)
                 .filter(favorite_room_table.c.user_id == session.user.id))
        favorites = [id_ for id_, in query]
        return jsonify(favorites)

    def _process_PUT(self):
        session.user.favorite_rooms.add(self.room)
        return '', 204

    def _process_DELETE(self):
        session.user.favorite_rooms.discard(self.room)
        return '', 204
