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
from urlparse import urlunparse

from twisted.internet.error import ConnectionRefusedError, TimeoutError
from twisted.web import http

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


def iso8601(seconds_ago=0):
    '''
    Return a ISO8601 date and time representation of now adjusted by
    seconds_ago in UTC.
    '''
    utcnow = datetime.datetime.utcnow()
    if seconds_ago == 0:
        utc = utcnow
    else:
        utc = utcnow - datetime.timedelta(seconds=seconds_ago)

    return utc.strftime('%Y-%m-%dT%H:%M:%S.000Z')


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
    httpRequest['Timestamp'] = iso8601()

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


def getSESRegions():
    addLocalLibPath()
    import boto.ses
    region_infos = boto.ses.regions()
    regions = []
    for region in region_infos:
        regions.append(region.name)
    return regions


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
        if result.type == ConnectionRefusedError:
            return 'connection refused'
        elif result.type == TimeoutError:
            return 'connection timeout'
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

    # No need to find new object if id_ is empty.
    if not id_:
        return

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


def unreserved_instance_count(ec2_conn, instance):
    if instance.state != 'running':
        return 0  # stoppend instances not need discount
    if instance.spot_instance_request_id:
        return 0  # spot instances cannot use discount

    # getting running instances of the same type
    # in the same availability zone
    instances = ec2_conn.get_only_instances(filters={
        'instance-state-name': 'running',
        'instance-type': instance.instance_type,
        'availability-zone': instance.placement,
    })
    # and not spot instances
    instances = filter(lambda i: not i.spot_instance_request_id, instances)

    # getting active reserved instances of the same type
    # in the same availability zone
    reserved = ec2_conn.get_all_reserved_instances(filters={
        'state': 'active',
        'instance-type': instance.instance_type,
        'availability-zone': instance.placement,
    })
    return len(instances) - len(reserved)


def unused_reserved_instances_count(ec2_conn, reserved_instance):
    # getting running instances of the same type
    # in the same availability zone
    instances = ec2_conn.get_only_instances(filters={
        'instance-state-name': 'running',
        'instance-type': reserved_instance.instance_type,
        'availability-zone': reserved_instance.availability_zone,
    })
    # and not spot instances
    instances = filter(lambda i: not i.spot_instance_request_id, instances)

    # getting active reserved instances of the same type
    # in the same availability zone
    reserved = ec2_conn.get_all_reserved_instances(filters={
        'state': 'active',
        'instance-type': reserved_instance.instance_type,
        'availability-zone': reserved_instance.availability_zone,
    })
    return len(reserved) - len(instances)

def prodState(state):
    # if the state is stopped return decommissioned, otherwise production.
    if state == 'stopped':
        return -1
    else:
        return 1000


def twisted_web_client_parse(url, defaultPort=None):
    """
    Split the given URL into the scheme, host, port, and path.

    @type url: C{str}
    @param url: An URL to parse.

    @type defaultPort: C{int} or C{None}
    @param defaultPort: An alternate value to use as the port if the URL does
    not include one.

    @return: A four-tuple of the scheme, host, port, and path of the URL.  All
    of these are C{str} instances except for port, which is an C{int}.
    """
    url = url.strip()
    parsed = http.urlparse(url)
    scheme = parsed[0]
    path = urlunparse(('', '') + parsed[2:])

    if defaultPort is None:
        if scheme == 'https':
            defaultPort = 443
        else:
            defaultPort = 80

    host, port = parsed[1], defaultPort
    if ':' in host:
        host, port = host.split(':')
        try:
            port = int(port)
        except ValueError:
            port = defaultPort

    if path == '':
        path = '/'

    return scheme, host, port, path


def format_time(time):
    '''
    Return formatted time string.
    '''
    return time[:time.rfind('.')].replace('T', ' ')
