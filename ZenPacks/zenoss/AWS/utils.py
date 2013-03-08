##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging
log = logging.getLogger('zen.AWS')

import hashlib
import hmac
import base64
import urllib
import datetime

from twisted.internet.error import ConnectionRefusedError, TimeoutError

from zope.event import notify

from Products.AdvancedQuery import Eq, Or
from Products.ZenUtils.Utils import prepId
from Products.Zuul.catalog.events import IndexingEvent
from Products.Zuul.interfaces import ICatalogTool


def addLocalLibPath():
    """
    Helper to add the ZenPack's lib directory to PYTHONPATH.
    """
    import os
    import site

    site.addsitedir(os.path.join(os.path.dirname(__file__), 'lib'))


def awsUrlSign(
        httpVerb='GET',
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


def updateToMany(relationship, root, type_, ids):
    '''
    Update ToMany relationship given search root, type and ids.

    This is a general-purpose function for efficiently building
    non-containing ToMany relationships.
    '''
    root = root.primaryAq()

    new_ids = set(map(prepId, ids))
    current_ids = set(o.id for o in relationship.objectValuesGen())
    changed_ids = new_ids.symmetric_difference(current_ids)

    query = Or(*(Eq('id', x) for x in changed_ids))

    obj_map = {}
    for result in ICatalogTool(root).search(types=[type_], query=query):
        obj_map[result.id] = result.getObject()

    for id_ in new_ids.symmetric_difference(current_ids):
        obj = obj_map.get(id_)
        if not obj:
            continue

        if id_ in new_ids:
            relationship.addRelation(obj)
        else:
            relationship.removeRelation(obj)

        # Index remote object. It might have a custom path reporter.
        notify(IndexingEvent(obj, 'path', False))

        # For componentSearch. Would be nice if we could target
        # idxs=['getAllPaths'], but there's a chance that it won't exist
        # yet.
        obj.index_object()


def updateToOne(relationship, root, type_, id_):
    '''
    Update ToOne relationship given search root, type and ids.

    This is a general-purpose function for efficiently building
    non-containing ToOne relationships.
    '''
    old_obj = relationship()

    # Return with no action if the relationship is already correct.
    if (old_obj and old_obj.id == id_) or (not old_obj and not id_):
        return

    # Remove current object from relationship.
    if old_obj:
        relationship.removeRelation()

        # Index old object. It might have a custom path reporter.
        notify(IndexingEvent(old_obj.primaryAq(), 'path', False))

    # Find and add new object to relationship.
    root = root.primaryAq()
    query = Eq('id', id_)

    for result in ICatalogTool(root).search(types=[type_], query=query):
        new_obj = result.getObject()
        relationship.addRelation(new_obj)

        # Index remote object. It might have a custom path reporter.
        notify(IndexingEvent(new_obj.primaryAq(), 'path', False))

        # For componentSearch. Would be nice if we could target
        # idxs=['getAllPaths'], but there's a chance that it won't exist
        # yet.
        new_obj.index_object()

        return
