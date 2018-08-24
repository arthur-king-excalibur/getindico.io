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

import _ from 'lodash';
import createHistory from 'history/createBrowserHistory';
import {queryStringMiddleware, createQueryStringReducer} from 'redux-router-querystring';
import {connectRouter, routerMiddleware} from 'connected-react-router';
import createReduxStore from 'indico/utils/redux';

import reducers from './reducers';
import {initialRoomFilterStateFactory} from './reducers/roomBooking/filters';
import {initialTimelineState} from './reducers/bookRoom';
import {routeConfig as calendarRouteConfig, queryStringReducer as qsCalendarReducer} from './modules/calendar';
import * as actions from './actions';
import {queryString as queryFilterRules} from './serializers/filters';
import {queryString as queryTimelineRules} from './serializers/timeline';


function getRouteConfig() {
    return {
        reduxPathname: ({router: {location: {pathname}}}) => pathname,
        routes: {
            '/book': [
                {
                    listen: actions.SET_FILTER_PARAMETER,
                    select: ({bookRoom: {filters}}) => ({filters}),
                    serialize: queryFilterRules
                },
                {
                    listen: actions.TOGGLE_TIMELINE_VIEW,
                    select: ({bookRoom: {timeline}}) => ({timeline}),
                    serialize: queryTimelineRules
                }
            ],
            '/rooms': {
                listen: actions.SET_FILTER_PARAMETER,
                select: ({roomList: {filters}}) => ({filters}),
                serialize: queryFilterRules
            },
            ...calendarRouteConfig
        }
    };
}

function pathMatch(map, path) {
    for (const pth in map) {
        if (new RegExp(pth).test(path)) {
            return map[pth];
        }
    }
}

export const history = createHistory({
    basename: '/rooms-new'
});

const qsFilterReducer = createQueryStringReducer(
    queryFilterRules,
    (state, action) => {
        if (action.type === actions.INIT) {
            const namespace = pathMatch({
                '^/book': 'bookRoom',
                '^/rooms': 'roomList'
            }, history.location.pathname);
            if (!namespace) {
                return null;
            }
            return {
                namespace,
                queryString: history.location.search.slice(1)
            };
        }
        return null;
    },
    (state, namespace) => (namespace
        ? _.merge({}, state, {[namespace]: {filters: initialRoomFilterStateFactory(namespace)}})
        : state)
);

const qsTimelineReducer = createQueryStringReducer(
    queryTimelineRules,
    (state, action) => {
        if (action.type === actions.INIT) {
            return {
                namespace: 'bookRoom',
                queryString: history.location.search.slice(1)
            };
        }
        return null;
    },
    (state, namespace) => (namespace
        ? _.merge({}, state, {[namespace]: {timeline: initialTimelineState}})
        : state)
);


export default function createRBStore() {
    return createReduxStore(
        'rb-new',
        reducers,
        {},
        [
            routerMiddleware(history),
            queryStringMiddleware(history, getRouteConfig(), {usePush: false})
        ],
        [
            qsFilterReducer,
            qsTimelineReducer,
            qsCalendarReducer
        ],
        rootReducer => connectRouter(history)(rootReducer));
}
