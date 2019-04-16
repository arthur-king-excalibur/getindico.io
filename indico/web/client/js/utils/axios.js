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

/* global showErrorDialog:false */

import axios from 'axios';
import useAxios from '@use-hooks/axios';
import isURLSameOrigin from 'axios/lib/helpers/isURLSameOrigin';
import qs from 'qs';

import {$T} from 'indico/utils/i18n';
import {camelizeKeys} from './case';


export const indicoAxios = axios.create({
    paramsSerializer: (params) => qs.stringify(params, {arrayFormat: 'repeat'}),
    xsrfCookieName: null,
    xsrfHeaderName: null,
});

indicoAxios.isCancel = axios.isCancel;
indicoAxios.CancelToken = axios.CancelToken;

indicoAxios.interceptors.request.use((config) => {
    if (isURLSameOrigin(config.url)) {
        config.headers.common['X-Requested-With'] = 'XMLHttpRequest';  // needed for `request.is_xhr`
        config.headers.common['X-CSRF-Token'] = document.getElementById('csrf-token').getAttribute('content');
    }
    return config;
});


export function handleAxiosError(error, strict = false) {
    if (axios.isCancel(error)) {
        return;
    }
    if (error.response && error.response.data && error.response.data.error) {
        error = error.response.data.error;
    } else {
        if (strict) {
            throw error;
        }
        error = {
            title: $T.gettext('Something went wrong'),
            message: error.message,
            report_url: null
        };
    }
    if (window.showErrorDialog) {
        showErrorDialog(error);
    } else {
        import(/* webpackMode: "weak" */ 'indico/react/errors').then(({default: showReactErrorDialog}) => {
            showReactErrorDialog(error);
        });
    }
    return error.message;
}

export function useIndicoAxios({camelize, ...args}) {
    const {response, error, loading, reFetch} = useAxios({
        customHandler: err => err && handleAxiosError(err),
        ...args,
        axios: indicoAxios,
    });

    let data = null;
    if (response) {
        data = response.data;
        if (camelize) {
            data = camelizeKeys(data);
        }
    }
    return {response, error, loading, reFetch, data};
}

export default indicoAxios;
