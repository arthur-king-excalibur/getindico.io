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

import sys
import xmlrpclib
import httplib

class RequestConnection:

    def request(self, host, handler, request_body, verbose=0):
        # issue XML-RPC request

        h = self.make_connection(host)
        if verbose:
            h.set_debuglevel(1)
        try:
            self.send_request(h, handler, request_body)
            self.send_host(h, host)
            self.send_user_agent(h)
            self.send_content(h, request_body)

            response = h.getresponse(buffering=True)

            if response.status == 200:
                self.verbose = verbose
                return self.parse_response(response)
        except xmlrpclib.Fault:
            raise
        except Exception:
            # All unexpected errors leave connection in
            # a strange state, so we clear it.
            self.close()
            raise

        #discard any response data and raise exception
        if (response.getheader("content-length", 0)):
            response.read()
        raise xmlrpclib.ProtocolError(
            host + handler,
            response.status, response.reason,
            response.msg,
            )

class TransportWithTimeout(xmlrpclib.Transport, RequestConnection):

    def setTimeout(self, timeout):
        self._timeout = timeout

    def make_connection(self, host):
        return httplib.HTTPConnection(host, timeout=self._timeout)


class SafeTransportWithTimeout(xmlrpclib.SafeTransport, RequestConnection):

    def setTimeout(self, timeout):
        self._timeout = timeout

    def make_connection(self, host):
        return httplib.HTTPSConnection(host, timeout=self._timeout)


def getServerWithTimeout(uri, transport=None, encoding=None, verbose=0,
                         allow_none=0, use_datetime=0, timeout=None):

    if uri.startswith("https://"):
        transport = SafeTransportWithTimeout()
    else:
        transport = TransportWithTimeout()
    transport.setTimeout(timeout)

    return xmlrpclib.ServerProxy(uri, transport, encoding, verbose, allow_none, use_datetime)
