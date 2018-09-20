/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

import * as actions from '../../actions';
import {getAspectBounds} from '../../util';


const initialMapState = {
    bounds: null,
    search: false,
};


export function mapReducerFactory(namespace) {
    return (state = initialMapState, action) => {
        // aspect updates are global and need to run regardless of the namespace
        if (action.type === actions.UPDATE_ASPECTS) {
            const defaultAspect = action.aspects.find(aspect => aspect.default_on_startup) || action.aspects[0];
            return {...state, bounds: defaultAspect ? getAspectBounds(defaultAspect) : null};
        }

        if (action.namespace !== namespace) {
            return state;
        }

        switch (action.type) {
            case actions.UPDATE_LOCATION:
                return {...state, bounds: action.location};
            case actions.TOGGLE_MAP_SEARCH:
                return {...state, search: action.search};
            default:
                return state;
        }
    };
}
