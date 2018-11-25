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
from marshmallow import validate
from sqlalchemy.orm import joinedload
from webargs import fields
from webargs.flaskparser import abort, use_kwargs, use_args
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.rb import Room
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.equipment import EquipmentType, RoomEquipmentAssociation
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.room_attributes import RoomAttribute, RoomAttributeAssociation
from indico.modules.rb.models.room_features import RoomFeature
from indico.modules.rb.util import rb_is_admin
from indico.modules.rb_new.schemas import (admin_equipment_type_schema, room_attribute_schema,
                                           room_feature_schema)

from indico.util.i18n import _
from indico.util.marshmallow import ModelList
from indico.modules.rb_new.controllers.backend.common import room_args
from indico.modules.rb_new.operations.admin import get_room_attributes, update_room, update_room_equipment, \
    update_room_attributes, update_room_availability
from indico.modules.rb_new.schemas import (admin_locations_schema, attributes_schema, room_equipment_schema,
                                           room_update_schema, nonbookable_periods_schema, bookable_hours_schema)


class RHRoomBookingAdminBase(RHRoomBookingBase):
    def _check_access(self):
        RHRoomBookingBase._check_access(self)
        if not rb_is_admin(session.user):
            raise Forbidden


class RHLocations(RHRoomBookingAdminBase):
    def _process(self):
        query = Location.query.options(joinedload('rooms'))
        return jsonify(admin_locations_schema.dump(query.all()).data)


class RHFeatures(RHRoomBookingAdminBase):
    def _process_args(self):
        id_ = request.view_args.get('feature_id')
        self.feature = RoomFeature.get_one(id_) if id_ is not None else None

    def _dump_features(self):
        query = RoomFeature.query.order_by(RoomFeature.title)
        return room_feature_schema.dump(query, many=True).data

    def _jsonify_one(self, equipment_type):
        return jsonify(room_feature_schema.dump(equipment_type).data)

    def _jsonify_many(self):
        return jsonify(self._dump_features())

    def _process_GET(self):
        if self.feature:
            return self._jsonify_one(self.feature)
        else:
            return self._jsonify_many()

    def _process_DELETE(self):
        db.session.delete(self.feature)
        db.session.flush()
        return '', 204

    @use_kwargs({
        'name': fields.String(validate=validate.Length(min=2), required=True),
        'title': fields.String(validate=validate.Length(min=2), required=True),
        'icon': fields.String(missing=''),
    })
    def _process_POST(self, name, title, icon):
        self._check_conflict(name)
        feature = RoomFeature(name=name, title=title, icon=icon)
        db.session.add(feature)
        db.session.flush()
        return self._jsonify_one(feature), 201

    @use_kwargs({
        'name': fields.String(validate=validate.Length(min=2)),
        'title': fields.String(validate=validate.Length(min=2)),
        'icon': fields.String(),
    })
    def _process_PATCH(self, name=None, title=None, icon=None):
        if name is not None:
            self._check_conflict(name)
            self.feature.name = name
        if title is not None:
            self.feature.title = title
        if icon is not None:
            self.feature.icon = icon
        db.session.flush()
        return self._jsonify_one(self.feature)

    def _check_conflict(self, name):
        query = RoomFeature.query.filter(db.func.lower(RoomFeature.name) == name.lower())
        if self.feature:
            query = query.filter(RoomFeature.id != self.feature.id)
        if query.has_rows():
            abort(422, messages={'name': [_('Name must be unique')]})


class RHEquipmentTypes(RHRoomBookingAdminBase):
    def _process_args(self):
        id_ = request.view_args.get('equipment_type_id')
        self.equipment_type = EquipmentType.get_one(id_) if id_ is not None else None

    def _dump_equipment_types(self):
        query = EquipmentType.query.options(joinedload('features')).order_by(EquipmentType.name)
        return admin_equipment_type_schema.dump(query, many=True).data

    def _get_room_counts(self):
        query = (db.session.query(RoomEquipmentAssociation.c.equipment_id, db.func.count())
                 .group_by(RoomEquipmentAssociation.c.equipment_id))
        return dict(query)

    def _jsonify_one(self, equipment_type):
        counts = self._get_room_counts()
        eq = admin_equipment_type_schema.dump(equipment_type).data
        eq['num_rooms'] = counts.get(eq['id'], 0)
        return jsonify(eq)

    def _jsonify_many(self):
        counts = self._get_room_counts()
        equipment_types = self._dump_equipment_types()
        for eq in equipment_types:
            eq['num_rooms'] = counts.get(eq['id'], 0)
        return jsonify(equipment_types)

    def _process_GET(self):
        if self.equipment_type:
            return self._jsonify_one(self.equipment_type)
        else:
            return self._jsonify_many()

    def _process_DELETE(self):
        db.session.delete(self.equipment_type)
        db.session.flush()
        return '', 204

    @use_kwargs({
        'name': fields.String(validate=validate.Length(min=2), required=True),
        'features': ModelList(RoomFeature, missing=[])
    })
    def _process_POST(self, name, features):
        self._check_conflict(name)
        equipment_type = EquipmentType(name=name, features=features)
        db.session.add(equipment_type)
        db.session.flush()
        return self._jsonify_one(equipment_type), 201

    @use_kwargs({
        'name': fields.String(validate=validate.Length(min=2)),
        'features': ModelList(RoomFeature)
    })
    def _process_PATCH(self, name=None, features=None):
        if name is not None:
            self._check_conflict(name)
            self.equipment_type.name = name
        if features is not None:
            self.equipment_type.features = features
        db.session.flush()
        return self._jsonify_one(self.equipment_type)

    def _check_conflict(self, name):
        query = EquipmentType.query.filter(db.func.lower(EquipmentType.name) == name.lower())
        if self.equipment_type:
            query = query.filter(EquipmentType.id != self.equipment_type.id)
        if query.has_rows():
            abort(422, messages={'name': [_('Name must be unique')]})


class RHAttributes(RHRoomBookingAdminBase):
    def _process_args(self):
        id_ = request.view_args.get('attribute_id')
        self.attribute = RoomAttribute.get_one(id_) if id_ is not None else None

    def _dump_attributes(self):
        query = RoomAttribute.query.order_by(RoomAttribute.title)
        return room_attribute_schema.dump(query, many=True).data

    def _get_room_counts(self):
        query = (db.session.query(RoomAttributeAssociation.attribute_id, db.func.count())
                 .group_by(RoomAttributeAssociation.attribute_id))
        return dict(query)

    def _jsonify_one(self, attribute):
        counts = self._get_room_counts()
        attr = room_attribute_schema.dump(attribute).data
        attr['num_rooms'] = counts.get(attr['id'], 0)
        return jsonify(attr)

    def _jsonify_many(self):
        counts = self._get_room_counts()
        attributes = self._dump_attributes()
        for attr in attributes:
            attr['num_rooms'] = counts.get(attr['id'], 0)
        return jsonify(attributes)

    def _process_GET(self):
        if self.attribute:
            return self._jsonify_one(self.attribute)
        else:
            return self._jsonify_many()

    def _process_DELETE(self):
        db.session.delete(self.attribute)
        db.session.flush()
        return '', 204

    @use_kwargs({
        'name': fields.String(validate=validate.Length(min=2), required=True),
        'title': fields.String(validate=validate.Length(min=2), required=True),
        'hidden': fields.Bool(missing=False),
    })
    def _process_POST(self, name, title, hidden):
        self._check_conflict(name)
        attribute = RoomAttribute(name=name, title=title, is_hidden=hidden)
        db.session.add(attribute)
        db.session.flush()
        return self._jsonify_one(attribute), 201

    @use_kwargs({
        'name': fields.String(validate=validate.Length(min=2)),
        'title': fields.String(validate=validate.Length(min=2)),
        'hidden': fields.Bool(),
    })
    def _process_PATCH(self, name=None, title=None, hidden=None):
        if name is not None:
            self._check_conflict(name)
            self.attribute.name = name
        if title is not None:
            self.attribute.title = title
        if hidden is not None:
            self.attribute.is_hidden = hidden
        db.session.flush()
        return self._jsonify_one(self.attribute)

    def _check_conflict(self, name):
        query = RoomAttribute.query.filter(db.func.lower(RoomAttribute.name) == name.lower())
        if self.attribute:
            query = query.filter(RoomAttribute.id != self.attribute.id)
        if query.has_rows():
            abort(422, messages={'name': [_('Name must be unique')]})


class RHRoomAdminBase(RHRoomBookingBase):
    def _process_args(self):
        self.room = Room.get_one(request.view_args['room_id'])


# Returns all currently existing room attributes
class RHRoomAttributesAll(RHRoomBookingBase):
    def _process_args(self):
        attributes = RoomAttribute.query.all()
        return jsonify(attributes_schema.dump(attributes).data)


class RHRoomAttributes(RHRoomAdminBase):
    def _process(self):
        return jsonify(get_room_attributes(self.room.id))


class RHRoomAttributesUpdate(RHRoomAdminBase):
    def _process(self):
        update_room_attributes(self.room, request.get_json())
        return jsonify(get_room_attributes(self.room.id))


class RHRoomAvailability(RHRoomAdminBase):
    def _process(self):
        return jsonify({'nonbookable_periods': nonbookable_periods_schema.dump(self.room.nonbookable_periods, many=True).data,
                       'bookable_hours': bookable_hours_schema.dump(self.room.bookable_hours, many=True).data})


class RHRoomAvailabilityUpdate(RHRoomAdminBase):
    @use_args({'bookable_hours': fields.Nested({'start_time': fields.Time(),
                                                'end_time': fields.Time()}, many=True),
               'nonbookable_periods': fields.Nested({'start_dt': fields.DateTime(),
                                                     'end_dt': fields.DateTime()}, many=True)})
    def _process(self, args):
        update_room_availability(self.room, args)
        return jsonify({'nonbookable_periods': nonbookable_periods_schema.dump(self.room.nonbookable_periods, many=True).data,
                       'bookable_hours': bookable_hours_schema.dump(self.room.bookable_hours, many=True).data})


class RHRoomEquipment(RHRoomAdminBase):
    def _process(self):
        return jsonify(room_equipment_schema.dump(self.room).data)


class RHRoomEquipmentUpdate(RHRoomAdminBase):
    def _check_access(self):
        RHRoomAdminBase._check_access(self)
        if not rb_is_admin(session.user):
            raise Forbidden

    @use_args({
        'available_equipment': fields.List(fields.Int(), required=True)
    })
    def _process(self, args):
        update_room_equipment(self.room, args)
        return jsonify(room_update_schema.dump(self.room, many=False).data)


class RHRoomImage(RHRoomAdminBase):
    def _process(self):
        return ""


class RHRoom(RHRoomAdminBase):
    def _process(self):
        return jsonify(room_update_schema.dump(self.room).data)


class RHRoomUpdate(RHRoomAdminBase):
    def _check_access(self):
        RHRoomAdminBase._check_access(self)
        if not rb_is_admin(session.user):
            raise Forbidden

    @use_args(room_args)
    def _process(self, args):
        update_room(self.room, args)
        return jsonify(room_update_schema.dump(self.room, many=False).data)
