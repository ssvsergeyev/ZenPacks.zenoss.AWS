###########################################################################
#
# This program is part of Zenoss Core, an open source monitoring platform.
# Copyright (C) 2013 Zenoss Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 or (at your
# option) any later version as published by the Free Software Foundation.
#
# For complete information please visit: http://www.zenoss.com/oss/
#
###########################################################################

import logging
log = logging.getLogger('zen.AWS')

import hashlib
import hmac
import base64
import json
import urllib
import datetime

from twisted.internet.error import ConnectionRefusedError, TimeoutError


def addLocalLibPath():
    """
    Helper to add the ZenPack's lib directory to PYTHONPATH.
    """
    import os
    import site

    site.addsitedir(os.path.join(os.path.dirname(__file__), 'lib'))


def awsUrlSign(httpVerb='GET',
                hostHeader=None,
                uriRequest="/",
                httpRequest=None,
                awsKeys=None):

    """
    Method that will take the URL requst and provide a signed
    API query string.

    httpVerb = GET, PUT, POST
    hostHeader - example: monitoring.us-east-1.amazonaws.com
    uriRequest - example: /client/api (default / )
    httpRequest - example: {'Action': 'ListMetrics', ...}
    awsKeys - example: ('MYACCESSKEY', 'MYSECRETKEY')
    """

    # Set time of request for key signing
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
    httpRequest['Timestamp'] = timestamp

    accesskey = awsKeys[0]
    secretkey = awsKeys[1]

    httpRequest['AWSAccessKeyId'] = accesskey

    # The query string needs to be url encoded prior to signing
    queryString = urllib.urlencode(httpRequest)

    # The query string needs to be in byte order
    splitQuery = queryString.split('&')
    splitQuery.sort()

    # Now rejoin key/values for query string to sign
    new_query_line = '&'.join(splitQuery)

    signme = '\n'.join([httpVerb, hostHeader, uriRequest, new_query_line])

    # Get key signing has setup.
    new_hmac = hmac.new(secretkey, digestmod=hashlib.sha256)
    new_hmac.update(signme)

    sig = {'Signature': base64.b64encode(new_hmac.digest())}

    signature = urllib.urlencode(sig)

    return '%s/?%s&%s' % (hostHeader, new_query_line, signature)


def lookup_cwregion(value):

    # Data used to update regions endpoint for CloudWatch.
    return {
        'us-east-1': 'monitoring.us-east-1.amazonaws.com',
        'us-west-1': 'monitoring.us-west-1.amazonaws.com',
        'us-west-2': 'monitoring.us-west-2.amazonaws.com',
        'sa-east-1': 'monitoring.sa-east-1.amazonaws.com',
        'eu-west-1': 'monitoring.eu-west-1.amazonaws.com',
        'ap-northeast-1': 'monitoring.ap-northeast-1.amazonaws.com',
        'ap-southeast-1': 'monitoring.ap-southeast-1.amazonaws.com',
        'ap-southeast-2': 'monitoring.ap-southeast-2.amazonaws.com',
        }.get(value, 'monitoring.us-east-1.amazonaws.com')


def result_errmsg(result):
    """Return a useful error message string given a twisted errBack result."""
    try:
        from pywbem.cim_operations import CIMError

        if result.type == ConnectionRefusedError:
            return 'connection refused. Check IP and zWBEMPort'
        elif result.type == TimeoutError:
            return 'connection timeout. Check IP and zWBEMPort'
        elif result.type == CIMError:
            if '401' in result.value.args[1]:
                return 'login failed. Check zWBEMUsername and zWBEMPassword'
            else:
                return result.value.args[1]
        else:
            return result.getErrorMessage()
    except AttributeError:
        pass

    return str(result)
