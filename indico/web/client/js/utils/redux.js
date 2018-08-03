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
import {createStore, combineReducers, applyMiddleware} from 'redux';
import thunkMiddleware from 'redux-thunk';
import {composeWithDevTools} from 'redux-devtools-extension';
import {FORM_ERROR} from 'final-form';
import {handleSubmissionError} from 'indico/react/forms';
import {handleAxiosError} from 'indico/utils/axios';


// similar to the standard combineReducers, but accepts
// root reducers as well
export function combineRootReducers(...reducers) {
    const reducerFunctions = reducers.map(reducer => (
        (typeof reducer === 'function') ? reducer : combineReducers(reducer))
    );

    return (state, action) => reducerFunctions.reduce((st, fn) => fn(st, action), state);
}


export default function createReduxStore(
    name, reducers, initialData = {}, additionalMiddleware = [], postReducers = [], enhancer = r => r
) {
    const middleware = [thunkMiddleware, ...additionalMiddleware];
    const composeEnhancers = composeWithDevTools({name: `Indico:${name}`});

    return createStore(
        enhancer(combineRootReducers({
            staticData: (state = {}) => state,
            ...reducers
        }, ...postReducers)),
        initialData,
        composeEnhancers(applyMiddleware(...middleware)));
}


export const RequestState = {
    NOT_STARTED: 'not_started',
    STARTED: 'started',
    SUCCESS: 'success',
    ERROR: 'error',
};


export function requestReducer(requestAction, successAction, errorAction) {
    const initialState = {state: RequestState.NOT_STARTED, error: null};
    return (state = initialState, action) => {
        switch (action.type) {
            case requestAction:
                return {...state, state: RequestState.STARTED, error: null};
            case successAction:
                return {...state, state: RequestState.SUCCESS, error: null};
            case errorAction:
                return {...state, state: RequestState.ERROR, error: action.error};
            default:
                return state;
        }
    };
}


export function submitFormAction(submitFunc, requestAction, successAction, errorAction) {
    return async (dispatch) => {
        dispatcher(dispatch, requestAction);
        let response;
        try {
            response = await submitFunc();
        } catch (error) {
            if (_.get(error, 'response.status') === 422) {
                // if it's 422 we assume it's from webargs validation
                dispatcher(dispatch, errorAction, {error: handleSubmissionError(error)});
                return {data: null, error: handleSubmissionError(error)};
            } else if (_.get(error, 'response.status') === 418) {
                // this is an error that was expected, and will be handled by the app
                dispatcher(dispatch, errorAction, {error: {[FORM_ERROR]: error.response.data.message}});
                return {data: null, error: {[FORM_ERROR]: error.response.data.message}};
            } else {
                // anything else here is unexpected and triggers the usual error dialog
                const message = handleAxiosError(error, true);
                dispatcher(dispatch, errorAction, {error: {[FORM_ERROR]: message}});
                return {data: null, error: {[FORM_ERROR]: message}};
            }
        }

        const {data} = response;
        dispatcher(dispatch, successAction, {data});
        return {data, error: null};
    };
}


export function ajaxAction(requestFunc, requestAction, successAction, errorAction, transformData = d => d) {
    return async (dispatch) => {
        if (requestAction) {
            dispatcher(dispatch, requestAction);
        }
        let response;
        try {
            response = await requestFunc();
        } catch (error) {
            if (_.get(error, 'response.status') === 418) {
                // this is an error that was expected, and will be handled by the app
                if (errorAction) {
                    dispatcher(dispatch, errorAction, {error: error.response.data});
                }
                return {data: null, error: error.response.data};
            } else {
                const message = handleAxiosError(error, true);
                if (errorAction) {
                    dispatcher(dispatch, errorAction, {error: message});
                }
                return {data: null, error: message};
            }
        }

        const data = transformData(response.data);
        dispatcher(dispatch, successAction, {data});
        return {data, error: null};
    };
}


function dispatcher(dispatch, actions, data = {}) {
    if (Array.isArray(actions)) {
        actions.forEach(action => {
            dispatch({type: action, ...data});
        });
    } else {
        dispatch({type: actions, ...data});
    }
}
