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

from MaKaC.common import Config
from MaKaC.common.utils import encodeUnicode

from MaKaC.errors import MaKaCError, HtmlScriptError, HtmlForbiddenTag
from MaKaC.webinterface.common.tools import escape_html, restrictedHTML

"""
base module for HTML security
"""

class Sanitization(object):

    @staticmethod
    def _sanitize(params, level, doNotSanitize=[]):
        for i in params:
            if i in doNotSanitize:
                continue
            if isinstance(params, dict):
                param = params[i]
            else:
                param = i
            if isinstance(param, str):
                res = restrictedHTML(param, level)
                if res is not None:
                    raise HtmlForbiddenTag(res)
            elif isinstance(param, list) or isinstance(param, dict):
                Sanitization._sanitize(param, level)

    @staticmethod
    def _escapeHTML(params):
        index = 0
        for i in params:
            # params can be a list or a dictonary
            # we need to define k depending if it is a list or a dictonary
            # in order to be able to do such a operation: params[k] = something.
            if isinstance(params, dict):
                param = params[i]
                k = i
            else:
                param = i
                k = index  # since we are  looping a list, we need to increment the index to
                index += 1 # get the correct 'k' in the next iteration.
            if isinstance(param, str):
                params[k] = escape_html(param)
            elif isinstance(param, list) or isinstance(param, dict):
                Sanitization._escapeHTML(param)

    @staticmethod
    def _encodeUnicode(params):
        index = 0
        for i in params:
            # params can be a list or a dictonary
            # we need to define k depending if it is a list or a dictonary
            # in order to be able to do such a operation: params[k] = something.
            if isinstance(params, dict):
                param = params[i]
                k = i
            else:
                param = i
                k = index  # since we are  looping a list, we need to increment the index to
                index += 1 # get the correct 'k' in the next iteration.
            if isinstance(param, str) and param != "":
                params[k] = encodeUnicode(param)
                if params[k] == "":
                    raise MaKaCError(_("Your browser is using an encoding which is not recognized by Indico... Please make sure you set your browser encoding to utf-8"))
            elif isinstance(param, list) or isinstance(param, dict):
                Sanitization._encodeUnicode(param)

    @staticmethod
    def sanitizationCheck(target, params, accessWrapper, doNotSanitize=[]):
        # first make sure all params are utf-8
        Sanitization._encodeUnicode(params)

        # then check the security level of data sent to the server
        # if no user logged in, then no html allowed
        if accessWrapper.getUser():
            level = Config.getInstance().getSanitizationLevel()
        elif target and hasattr(target, "canModify") and target.canModify(accessWrapper):
            # not logged user, but use a modification key
            level = Config.getInstance().getSanitizationLevel()
        else:
            level = 0

        if level not in range(4):
            level = 1

        if level == 0:
            #Escape all HTML tags
            Sanitization._escapeHTML(params)

        elif level in [1,2]:
            #level 1 or default: raise error if script or style detected
            #level 2: raise error if script but style accepted
            Sanitization._sanitize(params, level, doNotSanitize)

        elif level == 3:
            # Absolutely no checks
            return